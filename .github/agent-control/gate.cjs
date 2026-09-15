// Trusted default-branch code only. A skipped step is not a model execution.
function decide({body, association, login, pr, history, now}) {
  if (!['OWNER','MEMBER','COLLABORATOR'].includes(association) && login !== 'chatgpt-codex-connector[bot]') return {reason:'untrusted-author'};
  const match = body.match(/^@claude review(?: delta)? ([a-f0-9]{40})\s*$/m);
  if (!match) return {reason:'no-explicit-review-command'};
  if (!pr || pr.state !== 'open' || pr.draft) return {reason:'requires-open-ready-pr'};
  if (pr.head.repo.full_name !== pr.base.repo.full_name) return {reason:'fork-not-enabled'};
  if (match[1] !== pr.head.sha) return {reason:'stale-sha'};
  const key = `Agent execution ${pr.head.sha} ${pr.base.sha}`;
  const recent = history.filter(s => s.started_at && s.conclusion !== 'skipped' && now-Date.parse(s.started_at) < 86400000);
  if (recent.some(s=>s.name===key)) return {reason:'already-executed-this-head-base'};
  if (recent.length >= 3) return {reason:'three-executions-in-24h'};
  return {allow:true, key, reason:'admitted'};
}
module.exports={decide};
module.exports.run=async ({github,context,core})=>{
  const {owner,repo}=context.repo;
  const event=context.payload;
  const number=event.issue?.number || event.pull_request?.number;
  const input=event.comment || event.review;
  if (!number || !input || (event.issue && !event.issue.pull_request)) {core.setOutput('allow','false'); return;}
  const {data:pr}=await github.rest.pulls.get({owner,repo,pull_number:number});
  const runs=await github.paginate(github.rest.actions.listWorkflowRuns,{owner,repo,workflow_id:'claude.yml',per_page:100});
  const history=[];
  for (const r of runs) {
    if (r.display_title!==`Agent review PR ${number}`) continue;
    const jobs=await github.paginate(github.rest.actions.listJobsForWorkflowRun,{owner,repo,run_id:r.id,filter:'all',per_page:100});
    for (const j of jobs) history.push(...(j.steps||[]).filter(s=>s.name.startsWith('Agent execution ')));
  }
  const d=decide({body:input.body||'',association:input.author_association,login:input.user?.login,pr,history,now:Date.now()});
  core.setOutput('allow',String(!!d.allow)); core.setOutput('execution',d.key||'Agent execution blocked');
  core.setOutput('head',pr.head.sha); core.setOutput('base',pr.base.sha);
  await core.summary.addHeading('Agent admission').addRaw(JSON.stringify({pr:number,head:pr.head.sha,base:pr.base.sha,...d})).write();
  if (!d.allow && !['no-explicit-review-command','untrusted-author'].includes(d.reason)) core.setFailed(`Review blocked: ${d.reason}. No model started; unresolved findings still block release.`);
};

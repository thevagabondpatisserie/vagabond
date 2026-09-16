// Trusted default-branch code only. A skipped step is not a model execution.
const RUN_NAME_PREFIX = 'Agent review PR ';
const ALLOWED_BOT = 'chatgpt-codex-connector[bot]';
function decide({body, association, login, pr, history, now}) {
  if (!['OWNER','MEMBER','COLLABORATOR'].includes(association) && login !== ALLOWED_BOT) return {reason:'untrusted-author'};
  const match = body.match(/^@claude review(?: delta)? ([a-fA-F0-9]{40})\s*$/m);
  if (!match) return {reason:'no-explicit-review-command'};
  if (!pr || pr.state !== 'open' || pr.draft) return {reason:'requires-open-ready-pr'};
  if (pr.head.repo.full_name !== pr.base.repo.full_name) return {reason:'fork-not-enabled'};
  if (match[1].toLowerCase() !== pr.head.sha.toLowerCase()) return {reason:'stale-sha'};
  const field=name=>body.match(new RegExp('^'+name+':\\s*(.+)$','mi'))?.[1]?.trim();
  if (field('Base')?.toLowerCase()!==pr.base.sha.toLowerCase() || !field('Scope') || !field('Evidence')) return {reason:'missing-or-stale-review-context'};
  if (/^@claude review delta /mi.test(body) && !/^[a-f0-9]{40}$/i.test(field('Previous')||'')) return {reason:'missing-previous-sha'};
  const key = `Agent execution ${pr.head.sha} ${pr.base.sha}`;
  const recent = history.filter(s => s.started_at && s.conclusion !== 'skipped' && now-Date.parse(s.started_at) < 86400000);
  if (recent.some(s=>s.name===key)) return {reason:'already-executed-this-head-base'};
  if (recent.length >= 3) return {reason:'three-executions-in-24h'};
  return {allow:true, key, reason:'admitted'};
}
module.exports={decide,RUN_NAME_PREFIX,ALLOWED_BOT};
module.exports.run=async ({github,context,core})=>{
  const {owner,repo}=context.repo;
  const event=context.payload;
  const number=event.issue?.number || event.pull_request?.number;
  const input=event.comment || event.review;
  if (!number || !input || (event.issue && !event.issue.pull_request)) {core.setOutput('allow','false'); return;}
  const {data:pr}=await github.rest.pulls.get({owner,repo,pull_number:number});
  const args={body:input.body||'',association:input.author_association,login:input.user?.login,pr,history:[],now:Date.now()};
  const preflight=decide(args);
  if (!preflight.allow) {
    core.setOutput('allow','false');
    core.setFailed(`Review not started: ${preflight.reason}`);
    return;
  }
  // Scan run metadata, not every historical job. Old runs can be rerun today.
  // Bound API use and fail closed if the complete history cannot be established.
  let requests=0;
  const bounded=async(method,params,key)=>{
    const result=[];
    for(let page=1;;page++) {
      if (++requests>80) throw new Error('History API budget exceeded; no model admitted');
      const {data}=await method({...params,per_page:100,page});
      const rows=data[key]; if(!Array.isArray(rows)) throw new Error('Invalid history response');
      result.push(...rows); if(rows.length<100) return result;
    }
  };
  const runs=await bounded(github.rest.actions.listWorkflowRuns,{owner,repo,workflow_id:'claude.yml'},'workflow_runs');
  const history=[];
  for (const r of runs) {
    if (r.display_title!==`${RUN_NAME_PREFIX}${number}`) continue;
    if(r.status==='completed' && Date.parse(r.updated_at)<args.now-86400000) continue;
    const jobs=await bounded(github.rest.actions.listJobsForWorkflowRun,{owner,repo,run_id:r.id,filter:'all'},'jobs');
    for (const j of jobs) history.push(...(j.steps||[]).filter(s=>s.name.startsWith('Agent execution ')));
  }
  const d=decide({...args,history});
  core.setOutput('allow',String(!!d.allow)); core.setOutput('execution',d.key||'Agent execution blocked');
  core.setOutput('head',pr.head.sha); core.setOutput('base',pr.base.sha);
  await core.summary.addHeading('Agent admission').addRaw(JSON.stringify({pr:number,head:pr.head.sha,base:pr.base.sha,...d})).write();
  if (!d.allow && !['no-explicit-review-command','untrusted-author'].includes(d.reason)) core.setFailed(`Review blocked: ${d.reason}. No model started; unresolved findings still block release.`);
};

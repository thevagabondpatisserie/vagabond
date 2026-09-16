const {test}=require('node:test'); const assert=require('node:assert/strict'); const {decide}=require('./gate.cjs');
const head='a'.repeat(40),base='b'.repeat(40),now=Date.now();
const contextText=`\nBase: ${base}\nPrevious: ${base}\nScope: gate\nEvidence: local tests`;
const command=(sha=head)=>`@claude review ${sha}${contextText}`;
const input=()=>({body:`@claude review delta ${head}${contextText}`,association:'OWNER',login:'owner',now,history:[],pr:{state:'open',draft:false,head:{sha:head,repo:{full_name:'a/b'}},base:{sha:base,repo:{full_name:'a/b'}}}});
test('valid current head',()=>assert.equal(decide(input()).allow,true));
test('ack and stale cannot launch',()=>{for(const body of ['thanks @claude',`@claude review ${base}`]) assert.ok(!decide({...input(),body}).allow)});
test('untrusted cannot launch',()=>assert.ok(!decide({...input(),association:'NONE'}).allow));
test('draft and fork rejected',()=>{for(const change of [p=>p.draft=true,p=>p.head.repo.full_name='evil/fork']){const x=input();change(x.pr);assert.ok(!decide(x).allow)}});
const entry=(name,conclusion='success',age=1000)=>({name,conclusion,started_at:new Date(now-age).toISOString()});
test('duplicate exact head/base, including failed action, blocked',()=>{for(const c of ['success','failure'])assert.ok(!decide({...input(),history:[entry(`Agent execution ${head} ${base}`,c)]}).allow)});
test('third allowed, fourth blocked; changed base cannot bypass limit',()=>{const x=input();x.history=[1,2].map(n=>entry('Agent execution '+n));assert.equal(decide(x).allow,true);x.history.push(entry('Agent execution 3'));assert.equal(decide(x).reason,'three-executions-in-24h')});
test('skips and expired executions do not consume budget',()=>assert.equal(decide({...input(),history:[entry(`Agent execution ${head} ${base}`,'skipped'),entry(`Agent execution ${head} ${base}`,'success',86400001)]}).allow,true));
test('adapter counts prior attempt in same run and never uses PR checkout',async()=>{
 const outputs={},notes=[]; const current={id:10,display_title:'Agent review PR 7'};
 const github={rest:{pulls:{get:async()=>({data:input().pr})},actions:{
 listWorkflowRuns:async()=>({data:{workflow_runs:[current]}}),
 listJobsForWorkflowRun:async args=>{assert.equal(args.filter,'all');return {data:{jobs:[{steps:[entry(`Agent execution ${head} ${base}`)]}]}}}
 }}};
 await require('./gate.cjs').run({github,context:{repo:{owner:'a',repo:'b'},runId:10,payload:{issue:{number:7,pull_request:{}},comment:{body:command(),author_association:'OWNER',user:{login:'owner'}}}},core:{setOutput:(k,v)=>outputs[k]=v,setFailed:x=>notes.push(x),summary:{addHeading(){return this},addRaw(){return this},async write(){}}}});
 assert.equal(outputs.allow,'false');assert.match(notes[0],/already-executed/);
});
test('API failure does not admit a model',async()=>{
 const outputs={};await assert.rejects(require('./gate.cjs').run({github:{rest:{pulls:{get:async()=>{throw Error('403')}}}},context:{repo:{},payload:{issue:{number:7,pull_request:{}},comment:{}}},core:{setOutput:(k,v)=>outputs[k]=v}}));assert.notEqual(outputs.allow,'true');
});

test('closed PR rejected and uppercase SHA accepted',()=>{
 const x=input();x.pr.state='closed';assert.equal(decide(x).reason,'requires-open-ready-pr');
 assert.equal(decide({...input(),body:command(head.toUpperCase())}).allow,true);
});
test('only configured Codex bot bypasses membership',()=>{
 assert.equal(decide({...input(),association:'NONE',login:'chatgpt-codex-connector[bot]'}).allow,true);
 assert.equal(decide({...input(),association:'NONE',login:'other-bot[bot]'}).reason,'untrusted-author');
});
test('workflow labels and bot identity are a durable contract',()=>{
 const fs=require('node:fs'),path=require('node:path');const s=fs.readFileSync(path.join(__dirname,'../workflows/claude.yml'),'utf8');
 const {RUN_NAME_PREFIX,ALLOWED_BOT}=require('./gate.cjs');
 const valid=t=>t.includes('run-name: '+RUN_NAME_PREFIX+'${{') && t.includes(`allowed_bots: '${ALLOWED_BOT}'`);
 assert.ok(valid(s));assert.ok(!valid(s.replace(RUN_NAME_PREFIX,'different ')));assert.ok(!valid(s.replace(ALLOWED_BOT,'different')));
 assert.ok(s.indexOf('Admit explicit')<s.indexOf('Checkout exact admitted'));
});
async function adapter(runs,jobs,body=command()){
 const outputs={};const core={setOutput:(k,v)=>outputs[k]=v,setFailed:x=>outputs.error=x,summary:{addHeading(){return this},addRaw(){return this},async write(){}}};
 const github={rest:{pulls:{get:async()=>({data:input().pr})},actions:{listWorkflowRuns:async()=>({data:{workflow_runs:runs}}),listJobsForWorkflowRun:jobs}}};
 await require('./gate.cjs').run({github,core,context:{repo:{owner:'a',repo:'b'},runId:10,payload:{issue:{number:7,pull_request:{}},comment:{body,author_association:'OWNER',user:{login:'owner'}}}}});return outputs;
}
test('old completed runs skip jobs; old run rerun today still counted',async()=>{
 const old={id:1,display_title:'Agent review PR 7',status:'completed',created_at:'2020-01-01T00:00:00Z',updated_at:'2020-01-01T00:00:00Z'};
 const recent={...old,id:2,updated_at:new Date().toISOString()};const calls=[];
 const out=await adapter([old,recent],async a=>{calls.push(a.run_id);return {data:{jobs:[{steps:[entry(`Agent execution ${head} ${base}`)]}]}}});
 assert.deepEqual(calls,[2]);assert.equal(out.allow,'false');
});
test('history API budget fails closed',async()=>{
 const rows=Array.from({length:99},(_,id)=>({id,display_title:'Agent review PR 7'}));let calls=0;
 await assert.rejects(adapter(rows,async()=>{calls++;return {data:{jobs:[]}}}),/budget exceeded/);assert.equal(calls,79);
});
test('invalid command never reads history',async()=>{
 const out=await adapter([],async()=>{throw Error('must not call')},'thanks @claude review');assert.equal(out.allow,'false');assert.match(out.error,/no-explicit/);
});

test('missing context cannot spend a review; delta needs previous SHA',()=>{
 for(const field of ['Base','Scope','Evidence','Previous']) {
 const x=input();x.body=x.body.split('\n').filter(line=>!line.startsWith(field+':')).join('\n');assert.ok(!decide(x).allow);
 }
});

const {test}=require('node:test'); const assert=require('node:assert/strict'); const {decide}=require('./gate.cjs');
const head='a'.repeat(40),base='b'.repeat(40),now=Date.now();
const input=()=>({body:`@claude review delta ${head}`,association:'OWNER',login:'owner',now,history:[],pr:{state:'open',draft:false,head:{sha:head,repo:{full_name:'a/b'}},base:{sha:base,repo:{full_name:'a/b'}}}});
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
 const api={pulls:{get:async()=>({data:input().pr})},actions:{listWorkflowRuns:'runs',listJobsForWorkflowRun:'jobs'}};
 const github={rest:api,paginate:async(method,args)=>{if(method==='runs')return[current];assert.equal(args.filter,'all');return[{steps:[entry(`Agent execution ${head} ${base}`)]}]}};
 await require('./gate.cjs').run({github,context:{repo:{owner:'a',repo:'b'},runId:10,payload:{issue:{number:7,pull_request:{}},comment:{body:`@claude review ${head}`,author_association:'OWNER',user:{login:'owner'}}}},core:{setOutput:(k,v)=>outputs[k]=v,setFailed:x=>notes.push(x),summary:{addHeading(){return this},addRaw(){return this},async write(){}}}});
 assert.equal(outputs.allow,'false');assert.match(notes[0],/already-executed/);
});
test('API failure does not admit a model',async()=>{
 const outputs={};await assert.rejects(require('./gate.cjs').run({github:{rest:{pulls:{get:async()=>{throw Error('403')}}}},context:{repo:{},payload:{issue:{number:7,pull_request:{}},comment:{}}},core:{setOutput:(k,v)=>outputs[k]=v}}));assert.notEqual(outputs.allow,'true');
});

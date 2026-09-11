const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('vagabond/public/js/bep/17-cai-dat.js','utf8');
async function run(answers, canApprove=1, fail=false){
 const calls=[],prompts=[],notes=[];
 const ctx={document:{getElementById:()=>({value:'2026-09-09'})},today:()=> '2026-09-11',busy:()=>{},money:String,toast:()=>{},go:()=>{},baoTin:x=>notes.push(x),
 xacNhan:async x=>{prompts.push(x);return answers.shift()},api:async(n,p)=>{calls.push(p);if(p.chay_thu)return {chon:2,so_nhap:1,pham_vi:["SI-09","SI-NHAP"],tien:150000,hom_nay:'2026-09-11',che_do_de_xuat:'keo',cua_phap_ly_con_mo:0,cua_minvoice_con_mo:1,han_ky_gui:'2026-09-10',duoc_xac_nhan_qua_han:canApprove};if(fail)throw Error('API lỗi');return {nhat_ky:'ok'};}};
 vm.createContext(ctx);vm.runInContext(source,ctx);await ctx.cdKeo();return {calls,prompts,notes};
}
(async()=>{
 let x=await run([true,true]);assert.equal(x.calls.length,2);assert.equal(x.calls[1].che_do,'giu_ngay');assert.equal(x.calls[1].ngay,'2026-09-09');assert.equal(x.calls[1].xac_nhan_qua_han,1);assert.deepEqual(JSON.parse(x.calls[1].pham_vi),["SI-09","SI-NHAP"]);assert(x.prompts[0].includes('ký ngày thực tế'));assert(x.calls[1].ly_do.includes('2026-09-11'));
 x=await run([false]);assert.equal(x.calls.length,1);
 x=await run([true,false]);assert.equal(x.calls.length,1);
 x=await run([],0);assert.equal(x.calls.length,1);assert(x.notes[0].includes('quản lý'));
 x=await run([true,true],1,true);assert.equal(x.calls.length,2);assert.equal(x.notes.at(-1),'API lỗi');
 console.log('PASS 5 tình huống UI: xác nhận giữ ngày, hủy hai bước, thiếu quyền, API lỗi');
})().catch(e=>{console.error(e);process.exitCode=1});

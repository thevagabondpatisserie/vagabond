/* v558: nut Mo khoa / Dong khoa mot to tren man Khoa so cua app.
   Anh Viet chot 03/10/2026 nut phai co tren app lan Desk. Truoc v558 may chu
   co mo_khoa_mot_to ma khong nut nao goi toi. Ca nay nap THAT 17-cai-dat.js,
   chay dung chuoi bam cua ke toan: mo man, chon loai, go so, ghi ly do, bam
   Mo khoa; roi bam Dong khoa tren to dang mo. */
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('vagabond/public/js/bep/17-cai-dat.js','utf8');
function dungMoiTruong(suaDuoc){
  const calls=[],toasts=[],notes=[],els={};let html='',khung=null;
  const el=id=>els[id]||(els[id]={id,value:'',onclick:null});
  const ctx={
    h:s=>String(s==null?'':s),ngayNgan:s=>s,busy:()=>{},toast:x=>toasts.push(x),baoTin:x=>notes.push(x),
    posChipNut:(a,t,on)=>'<button '+a+(on?' data-on':'')+'>'+t+'</button>',kmHangChip:x=>'<div>'+x+'</div>',
    confirmSheet:async()=>true,
    frame:(t,b)=>{html=b;for(const k in els)delete els[k];khung={onclick:null};return khung;},
    document:{getElementById:id=>(html.indexOf('id="'+id+'"')>=0?el(id):null)},
    api:async(m,p)=>{calls.push([m,p]);
      if(m.endsWith('cai_dat_khoa_so'))return {so_ngay:3,den:'',ngay_khoa:'2026-09-30',so_to_dang_mo:1,sua_duoc:suaDuoc,loai:['hoá đơn bán','hoá đơn mua'],loai_ma:[['Sales Invoice','hoá đơn bán'],['Purchase Invoice','hoá đơn mua']]};
      if(m.endsWith('ds_to_dang_mo'))return [{doctype:'Sales Invoice',loai:'hoá đơn bán',name:'SI-26-09-00001'}];
      return {ok:1};}
  };
  vm.createContext(ctx);vm.runInContext(source,ctx);
  return {ctx,calls,toasts,notes,els,get html(){return html},get khung(){return khung}};
}
function go(m,id,v){m.ctx.document.getElementById(id).value=v;}
function bam(m,attr,val){m.khung.onclick({target:{closest:s=>s==='['+attr+']'?{getAttribute:()=>val}:null}});}
(async()=>{
  let m=dungMoiTruong(1);
  await m.ctx.scrKhoaSo();
  assert(m.html.includes('Mở khoá một tờ'),'ke toan truong thay o mo khoa');
  assert(m.html.includes('SI-26-09-00001')&&m.html.includes('data-ksdong="0"'),'thay to dang mo va nut dong');
  // Thieu ly do thi khong goi may chu
  go(m,'ksSoTo','HDM-26-08-00012');
  await m.ctx.ksMoTo();
  assert(!m.calls.some(c=>c[0].endsWith('mo_khoa_mot_to')),'thieu ly do khong duoc mo');
  assert(m.toasts.at(-1).includes('lý do'));
  // Doi loai sang hoa don mua, go so va ly do, bam mo
  bam(m,'data-ksl','Purchase Invoice');
  go(m,'ksSoTo','HDM-26-08-00012');go(m,'ksLyDoMo','Sửa mã món sai');
  await m.ctx.ksMoTo();
  const mo=m.calls.find(c=>c[0].endsWith('mo_khoa_mot_to'));
  assert.deepEqual(mo[1],{doctype:'Purchase Invoice',name:'HDM-26-08-00012',ly_do:'Sửa mã món sai'});
  // Bam Dong khoa tren to dang mo
  bam(m,'data-ksdong','0');
  await new Promise(r=>setTimeout(r,0));
  const dong=m.calls.find(c=>c[0].endsWith('dong_khoa_mot_to'));
  assert.deepEqual(dong[1],{doctype:'Sales Invoice',name:'SI-26-09-00001'});
  // Ke toan thuong: thay danh sach nhung khong co nut mo, nut dong
  m=dungMoiTruong(0);
  await m.ctx.scrKhoaSo();
  assert(!m.html.includes('Mở khoá một tờ'),'ke toan thuong khong thay o mo khoa');
  assert(m.html.includes('SI-26-09-00001')&&!m.html.includes('data-ksdong'),'chi xem, khong dong');
  console.log('PASS 4 ca mo khoa mot to: thieu ly do, chon loai roi mo, dong khoa, ke toan thuong chi xem');
})().catch(e=>{console.error(e);process.exitCode=1});

const fs=require('fs'),vm=require('vm'),assert=require('assert');
const dg=require('./dom_gia.js');
const source=fs.readFileSync('vagabond/public/js/bep/19-ho-so-tt.js','utf8');
const code=source.slice(source.indexOf('var hsCocLan = null;'));
const stored=new Map(); let calls=[],messages=[],khung,done=0,fail=true;
let danhRows=[{name:'PE-1',ngay:'2026-09-10',con_coc:3000000}],saoRows=[];
function env(){
 const tai=dg.taiLieuGia();
 const c={console,JSON,Number,
  sinhMaLanNhan:()=> 'LN-request-coc-247-unique',hasRole:()=>true,
  sessionStorage:{getItem:k=>stored.get(k),setItem:(k,v)=>stored.set(k,v),removeItem:k=>stored.delete(k)},
  h:x=>String(x||''),money:x=>String(x),busy:()=>{},toast:x=>messages.push(x),baoTin:x=>messages.push(x),xacNhan:async()=>true,
  frame:(t,html)=>{khung=new dg.ElementGia('div');khung.innerHTML=html;tai.body.children=[khung];return khung;},
  api:async(m,a)=>{calls.push({m,a:JSON.parse(JSON.stringify(a))});
   if(m.endsWith('.danh_sach'))return {rows:danhRows};
   if(m.endsWith('.sao_ke_coc'))return {rows:saoRows};
   if(fail)throw Error('Mất phản hồi');return {ok:1,da_can:2000000,da_lam_roi:1};}
 };vm.createContext(c);vm.runInContext(code,c);return {c,tai};
}
(async()=>{
 let {c,tai}=env();
 assert.equal(JSON.stringify(c.hsChiaCoc([{hoa_don:'A',so_tien:2000000},{hoa_don:'B',so_tien:8000000}],3000000)),JSON.stringify([{hoa_don:'A',so_tien:2000000},{hoa_don:'B',so_tien:1000000}]));
 assert.equal(c.hsDocTienDot('3.000.000'),3000000);assert(Number.isNaN(c.hsDocTienDot('3abc')));assert(Number.isNaN(c.hsDocTienDot('-3')));
 await c.hsMoCanCoc('NCC-1',[{hoa_don:'HD-1',so_tien:2000000}],()=>done++);
 await khung._nghe.click[0]({target:tai.querySelector('[data-hscoc]')});
 assert.equal(done,0);assert(stored.has('vgb_coc_app_pending'));
 const sent=calls.at(-1).a;assert.equal(sent.ma_lan,'CC-request-coc-247-unique');
 ({c,tai}=env());fail=false;await c.hsThuLaiCanCoc(()=>done++);
 assert.deepStrictEqual(calls.at(-1).a,sent);assert.equal(done,1);assert.equal(stored.size,0);
 danhRows=Array.from({length:9},(_,i)=>({name:'PE-'+(i+1),ngay:'2026-09-'+String(i+1).padStart(2,'0'),con_coc:1000}));
 ({c,tai}=env());await c.hsMoCanCoc('NCC-1',[{hoa_don:'HD-1',so_tien:1000}],()=>{});
 let tim=tai.getElementById('hsCocTim');assert(tim);
 tim.value='PE-9';tim.dispatchEvent(dg.suKien('input',{},tim));
 assert.equal(tai.querySelectorAll('[data-hscoc]').filter(x=>x.style.display!=='none').length,1);
 saoRows=Array.from({length:9},(_,i)=>({name:'BT-'+(i+1),date:'2026-09-'+String(i+1).padStart(2,'0'),withdrawal:1000,description:'Giao dich '+(i+1)}));
 await c.hsNoiSaoKeCoc('NCC-1','PE-1',()=>{});
 tim=tai.getElementById('hsCocGdTim');assert(tim);
 tim.value='BT-8';tim.dispatchEvent(dg.suKien('input',{},tim));
 assert.equal(tai.querySelectorAll('[data-cocgd]').filter(x=>x.style.display!=='none').length,1);
 console.log('PASS APP cọc: mất phản hồi, tải lại trang, retry giữ nguyên mã và payload');
})().catch(e=>{console.error(e);process.exitCode=1;});

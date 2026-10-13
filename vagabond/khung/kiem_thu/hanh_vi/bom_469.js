const fs=require('fs'),vm=require('vm'),assert=require('assert');
const {taiLieuGia,ElementGia}=require('./dom_gia.js');
const document=taiLieuGia(),calls=[];
let reply,fail=false,resolve;
const box={document,console,Date,Math,JSON,Promise,setTimeout,clearTimeout,h:x=>String(x==null?'':x),num:String,
 hasRole:()=>false,go:f=>f(),sheet:()=>{},errMsg:e=>e.message,
 api:async(url,args)=>{calls.push({url,args});if(fail)throw Error('Mất kết nối');return reply===undefined?await new Promise(r=>resolve=r):reply;},
 frame:(t,html,o={})=>{document.body.innerHTML='';let b=new ElementGia('div');b.setAttribute('id','vgbBody');b.innerHTML=html+(o.footer||'');document.body.children.push(b);return b;}};
vm.createContext(box);vm.runInContext(fs.readFileSync('vagabond/public/js/bep/26-cong-thuc.js','utf8'),box);
const html=()=>document.getElementById('vgbBody').innerHTML;
const row={bom:'BOM-X',nguoi:'Linh',luc:'2026-10-13',cau:['Đổi lượng 1 thành 2']};
(async()=>{
 // Máy ở UTC vẫn phải lọc ngày theo Sài Gòn, kể cả sát giao ngày và đầu tháng.
 reply={ds:[],tong:0};
 for(const [luc,tu,den] of [['2026-10-13T16:30:00Z','2026-10-07','2026-10-13'],['2026-10-13T17:30:00Z','2026-10-08','2026-10-14'],['2026-09-30T18:00:00Z','2026-09-25','2026-10-01']]){
  box.Date=class extends Date{constructor(...a){super(...(a.length?a:[luc]));}};
  await box.scrCongThucNhatKy();assert.strictEqual(calls.at(-1).args.den_ngay,den);assert.strictEqual(calls.at(-1).args.tu_ngay,tu);
 }
 box.Date=Date;
 assert.strictEqual(box.ctD.tt,'dang_dung');
 for(const n of [0,1,5]){
  reply={ds:Array(n).fill(row),tong:n,nguoi:[],mon:[]};await box.scrCongThucNhatKy();
  assert.strictEqual(document.querySelectorAll('[data-ctnkbom]').length,n);if(!n)assert(html().includes('Không có lần sửa'));
  reply={bom:'BOM-X',ten:'Món',ma:'M',so_luong:1,dvt:'Cái',dong:[],ban_truoc:[],ban_sau:[],trang_thai:'da_huy',lich_su:Array(n).fill(row)};
  await box.scrCongThucXem('BOM-X');assert(html().includes(n?'Linh':'Chưa có lần sửa'));
 }
 for(const f of [()=>box.scrCongThucNhatKy(),()=>box.scrCongThucXem('BOM-X')]){
  reply=undefined;let pending=f();assert(html().includes('⏳'));resolve({ds:[],tong:0,dong:[],ban_truoc:[],ban_sau:[],lich_su:[],trang_thai:'da_huy'});await pending;
  fail=true;await f();assert(html().includes('Mất kết nối'));fail=false;
 }
 reply={ds:[{...row,da_xoa:'DEL-X'}],tong:1};await box.scrCongThucNhatKy();
 let el=document.querySelector('[data-ctnkbom]');reply={bom:'BOM-X',ten:'Món xoá',dong:[{ma:'N',sl:2}]};
 await document.getElementById('vgbBody').onclick({target:el});assert.strictEqual(calls.at(-1).url,'vagabond.cong_thuc.ban_da_xoa');
 assert(html().includes('Chỉ đọc'));assert(!document.getElementById('ctSua'));assert(!document.getElementById('ctGhiSo'));
 console.log('PASS BOM 0/1/many/loading/error/deleted read-only');
})().catch(e=>{console.error(e);process.exit(1);});

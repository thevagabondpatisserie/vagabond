/* #391: chạy màn thật, chip/tìm/xuất/chọn cấn với API giả, không ghi tiền. */
'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const dom=require('./dom_gia');
const bep=path.resolve(__dirname,'../../../public/js/bep');
function doc(n){return fs.readFileSync(path.join(bep,n),'utf8');}
async function nghi(){for(let i=0;i<10;i++)await Promise.resolve();await new Promise(r=>setImmediate(r));}
async function moi(fin=true,loi=false){
 const document=dom.taiLieuGia(),root=document.createElement('div');root.id='vgb';document.body.appendChild(root);
 const calls=[],writes=[],opened=[],downloads=[];
 const row={name:'HD-1',bill_no:'00001',supplier:'NCC',supplier_name:'Nhà cung cấp',ma_ncc:'M001',ngay:'2026-09-01',con_no:100,account_currency:'VND',currency:'VND',company:'CTY',credit_to:'331',trang_thai:'Còn nợ',tre_ngay:3};
 const g={frappe:{session:{user:"test"}},document,console,Promise,JSON,Math,Number,String,Object,Array,Date,Error,RegExp,parseInt,parseFloat,setTimeout,clearTimeout,
  location:{href:'https://erp/bep',pathname:'/bep',hostname:'erp',search:'',hash:''},history:{pushState(){},replaceState(){},back(){}},requestAnimationFrame:f=>f(),
  h:s=>String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'),money:String,ngayNgan:String,
  toast(){},busy(){},baoTin:s=>writes.push(['tin',s]),dSkin(){},errMsg:e=>e.message,
  posChipNut:(a,n)=>'<button '+a+'>'+n+'</button>',kmHangChip:s=>'<div>'+s+'</div>',
  tdkNap:(id,a)=>{g.files=a;},tdkDs:()=>g.files||[],tdkKhoi:()=>'<div></div>',tdkNoi(){},tdkVeLai(){},hsChonCanCoc:(...a)=>writes.push(a),
  hasRole:()=>fin,hsCoQuyenCanCoc:()=>fin,hsCocLan:null,hsMoCanCoc:(...a)=>writes.push(a),hsThuLaiCanCoc:()=>writes.push(['retry']),
  bcTaiVe:(...a)=>downloads.push(a),open:(...a)=>opened.push(a),
  sheet:(t,ds,chon,cb)=>{g.choices=ds;g.pick=cb;},
  api:async(m,a)=>{calls.push({m,a});if(loi)throw new Error('Mất mạng');if(m.endsWith('khoan_da_tra'))return {ncc:'NCC',con_no:100,rows:[{name:'PE-1',con_coc:60,ngay:'2026-09-01',unc:[]}]};if(m.endsWith('luu_unc'))return {so_unc:1};if(m.endsWith('xuat_excel'))return {ten_file:'no.xlsx',b64:'AA=='};
   return {cong_ty:'CTY',cac_cong_ty:['CTY'],cac_nhom:['Hàng'],ngay_doc:'2026-10-01',so_hd:65,so_ncc:1,tong_theo_tien:{VND:100},dem:{tat_ca:65,con_no:65,qua_han:65},con_nua:!a.trang,dong:a.tu_khoa==='rỗng'?[]:[row]};}
 };
 g.window=g;g.root=root;vm.createContext(g);
 vm.runInContext(doc('01-khung-app.js'),g);vm.runInContext(doc('15-khuon-danh-sach.js'),g);
 const src=doc('16-mua-hang.js');vm.runInContext(src.slice(src.indexOf('/* Công nợ NCC:'),src.indexOf('/* ---------------- Hoa don ban ra')),g);
 await g.scrNoPhaiTra();
 return {g,root,document,calls,writes,opened,downloads,row,async click(sel){const el=root.querySelector(sel);assert(el,sel);el.dispatchEvent(dom.suKien('click',{},el));await nghi();}};
}
(async()=>{
 const m=await moi();
 await m.click('[data-dscc="chang|qua_han"]');assert.equal(m.calls.at(-1).a.trang_thai,'qua_han');
 await m.click('#cntSau');assert.equal(m.calls.at(-1).a.trang,1);
 const inp=m.document.getElementById('cntDsTim');inp.value='00001';inp.dispatchEvent(dom.suKien('keydown',{key:'Enter'},inp));await nghi();
 assert.equal(m.calls.at(-1).a.tu_khoa,'00001');assert.equal(m.calls.at(-1).a.trang,0);
 await m.click('[data-dsxuat]');const loc=JSON.parse(m.calls.at(-1).a.loc);assert.equal(loc.tu_khoa,'00001');assert.equal(loc.trang_thai,'qua_han');assert.equal(m.downloads.length,1);
 await m.click('[data-cntcan]');m.g.pick({value:'PE-1'});await nghi();
 m.g.files=[{url:'/private/files/unc.pdf'}];
 const moneyInput=m.document.getElementById('cntSoTien');moneyInput.value='40';
 const confirm=m.document.getElementById('cntXacNhanCan');confirm.dispatchEvent(dom.suKien('click',{},confirm));await nghi();
 assert.equal(m.calls.at(-1).m,'vagabond.cong_no_ncc.luu_unc');
 assert.equal(m.writes[0][0],'NCC');assert.deepEqual(JSON.parse(JSON.stringify(m.writes[0][1])),[{hoa_don:'HD-1',so_tien:40}]);
 assert(m.document.getElementById('cntUncCu').textContent.includes('UNC đã đính: 1'));
 const f=await moi();await f.click('[data-cntcan]');f.g.pick({value:'PE-1'});await nghi();
 f.document.getElementById('cntSoTien').value='61';await f.click('#cntXacNhanCan');
 assert(!f.writes.some(x=>x[0]==='NCC'),'vượt dư không được cấn');
 f.document.getElementById('cntSoTien').value='40';f.g.files=['/private/files/unc.pdf'];
 const apiCu=f.g.api;f.g.api=async(m,a)=>{if(m.endsWith('luu_unc'))throw new Error('Không lưu được UNC');return apiCu(m,a);};
 await f.click('#cntXacNhanCan');assert(!f.writes.some(x=>x[0]==='NCC'),'UNC lỗi phải dừng trước phân bổ');
 f.g.api=apiCu;await f.click('#cntLuuUnc');assert(!f.writes.some(x=>x[0]==='NCC'),'chỉ lưu UNC không phân bổ');
 m.g.hsCocLan={payload:'pending'};await m.g.cntCanTru(m.row);assert.equal(m.writes.at(-1)[0],'retry');
 await m.g.scrNoPhaiTra();
 const u=await moi(false);await u.click('[data-cntdong]');assert(!u.g.choices.some(x=>x.value==='can'||x.value==='loi'));assert.equal(u.writes.length,0);
 const e=await moi(true,true);assert(e.document.getElementById('cntThuLai'));await e.click('#cntThuLai');assert.equal(e.calls.length,2);
 const inp2=m.document.getElementById('cntDsTim');inp2.value='rỗng';inp2.dispatchEvent(dom.suKien('change',{},inp2));await nghi();assert(!m.root.querySelector('[data-cntdong]'));
 console.log('Công nợ NCC: chip, tìm, phân trang, Excel, quyền, cấn, retry, lỗi và rỗng PASS');
})().catch(e=>{console.error(e);process.exit(1);});

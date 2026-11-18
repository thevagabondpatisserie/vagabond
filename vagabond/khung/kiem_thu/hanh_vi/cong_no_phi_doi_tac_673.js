/* v673 (chị Dung 18/11/2026): hoá đơn phí Grab treo Công nợ phải trả. Chạy màn
   thật Công nợ phải trả với API giả: bấm Cấn trừ công nợ ở dòng hoá đơn Grab
   phải có lối "Phí đối tác đã giữ lại" mở màn đề xuất; nhà cung cấp thường giữ
   lối một chạm sang "Đã trả trước khi lên ERP" như v549. Kế toán lập phiếu,
   kế toán trưởng lập và ghi sổ một lần bấm. Không ghi tiền thật. */
'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const dom=require('./dom_gia');
const bep=path.resolve(__dirname,'../../../public/js/bep');
function doc(n){return fs.readFileSync(path.join(bep,n),'utf8');}
async function nghi(){for(let i=0;i<10;i++)await Promise.resolve();await new Promise(r=>setImmediate(r));}
const DX={hoa_don:{name:'HDM-26-10-00089',bill_no:'798888',ten_ncc:'CÔNG TY TNHH GRAB',con_no:44071417,ngay:'2026-10-06',noi_dung:'Phí dịch vụ'},
 doi_tac:'grab',doi_tac_ds:[{k:'grab',ten:'GrabFood'},{k:'onepay',ten:'OnePay'}],loai:'don',loai_ds:[{k:'don',ten:'Phí theo đơn'},{k:'ky',ten:'Phí kỳ, quảng cáo'}],
 ky:{tu:'2026-09-01',den:'2026-09-30',doan:'tháng trước ngày hoá đơn'},ky_ds:[{tu:'2026-09-01',den:'2026-09-30',ten:'Kỳ trên hoá đơn'},{tu:'2026-09-01',den:'2026-09-30',ten:'Tháng 09/2026'},{tu:'2026-08-01',den:'2026-08-31',ten:'Tháng 08/2026'}],
 phieu:[],quyen:{xac_nhan:false},lap_duoc:true,ly_do:'',tong_doi_soat:44071417,da_bu_truoc:0,can_bu:44071417,lech:0,so_nguon:30,nguon_chua_xn:0,so_dong:1184,
 dinh_khoan:[{ve:'Nợ',tk:'3311',doi:'GRAB',so:44071417},{ve:'Có',tk:'1311',doi:'KL',so:44071417}]};
async function moi(vai,{grab=true,pe=[],xacNhan=false,phieu=[]}={}){
 const document=dom.taiLieuGia(),root=document.createElement('div');root.id='vgb';document.body.appendChild(root);
 const calls=[],tin=[],hoi=[];
 const row={name:'HDM-26-10-00089',bill_no:'798888',supplier:'NC000056',supplier_name:grab?'CÔNG TY TNHH GRAB':'PRINTECO',ma_ncc:'NC000056',ngay:'2026-10-06',con_no:44071417,
  account_currency:'VND',currency:'VND',company:'CTY',credit_to:'331',trang_thai:'Còn nợ',tre_ngay:6,cho_duyet:[],phieu_phi:phieu,phi_doi_tac:grab};
 const g={frappe:{session:{user:'test'}},document,console,Promise,JSON,Math,Number,String,Object,Array,Date,Error,RegExp,parseInt,parseFloat,setTimeout,clearTimeout,
  location:{href:'https://erp/bep',pathname:'/bep',hostname:'erp',search:'',hash:''},history:{pushState(){},replaceState(){},back(){}},requestAnimationFrame:f=>f(),
  h:s=>String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'),money:String,
  toast(){},busy(){},baoTin:s=>tin.push(s),dSkin(){},errMsg:e=>e.message,
  posChipNut:(a,n)=>'<button '+a+'>'+n+'</button>',kmHangChip:s=>'<div>'+s+'</div>',
  tdkNap(){},tdkDs:()=>[],tdkKhoi:()=>'<div></div>',tdkNoi(){},tdkVeLai(){},hsChonCanCoc(){},
  hsCoQuyenCanCoc:()=>vai.some(v=>['Accounts User','Accounts Manager','System Manager'].indexOf(v)>=0),hsCocLan:null,hsThuLaiCanCoc(){},open(){},
  confirmSheet:async(t,m)=>{hoi.push(t+'|'+m);return true;},hoiChon:async()=>null,sinhMaLanNhan:()=>'LN-1',
  sheet:(t,ds,chon,cb)=>{g.choices=ds;g.pick=cb;},
  api:async(m,a)=>{calls.push({m,a});
   if(m.endsWith('khoan_da_tra'))return {ncc:'NCC',con_no:44071417,rows:pe};
   if(m.endsWith('xem_truoc_erp'))return {hoa_don:row.name,con_no:44071417,dang_cho:0,cho_duyet:[],ke_toan:true,tk_tam:'',tk_co:'11211'};
   if(m.endsWith('can_tru_phi.de_xuat'))return Object.assign({},DX,{quyen:{xac_nhan:xacNhan},phieu:g.phieuDx||[]});
   if(m.endsWith('can_tru_phi.lap'))return {name:'CTSAN-00012',tong_bu:44071417};
   if(m.endsWith('can_tru_phi.xac_nhan'))return {name:a.ten,trang_thai:'Đã cấn trừ',ly_do:'',but_toan:'ACC-JV-1'};
   return {cong_ty:'CTY',cac_cong_ty:['CTY'],cac_nhom:['Hàng'],ngay_doc:'2026-11-18',so_hd:1,so_ncc:1,tong_theo_tien:{VND:44071417},dem:{tat_ca:1,con_no:1},con_nua:false,dong:[row],ke_toan:true,tk_co_chon:[]};}
 };
 g.window=g;g.root=root;vm.createContext(g);
 vm.runInContext(doc('01-khung-app.js'),g);vm.runInContext(doc('15-khuon-danh-sach.js'),g);
 vm.runInContext('S.roles='+JSON.stringify(vai),g);
 const src=doc('16-mua-hang.js');vm.runInContext(src.slice(src.indexOf('/* Công nợ NCC:'),src.indexOf('/* ---------------- Hoa don ban ra')),g);
 await g.scrNoPhaiTra();
 return {g,root,document,calls,tin,hoi,
  async click(sel){const el=document.querySelector(sel)||root.querySelector(sel);assert(el,'thiếu '+sel);el.dispatchEvent(dom.suKien('click',{},el));await nghi();},
  goi:t=>calls.filter(c=>c.m.endsWith(t))};
}
(async()=>{
 // Ca 1: kế toán, hoá đơn Grab, không có phiếu chi: có lối Phí đối tác, chọn là mở đề xuất.
 const a=await moi(['Accounts User']);
 await a.click('[data-cntcan]');
 assert(a.g.choices&&a.g.choices.some(x=>x.value==='__phi_dt'),'có lối Phí đối tác đã giữ lại');
 assert(a.g.choices.some(x=>x.value==='__truoc_erp'),'vẫn giữ lối trả trước ERP');
 assert.equal(a.goi('xem_truoc_erp').length,0,'không nhảy thẳng sang trả trước ERP');
 a.g.pick(a.g.choices.find(x=>x.value==='__phi_dt'));await nghi();
 const dx=a.goi('can_tru_phi.de_xuat');assert.equal(dx.length,1);assert.equal(dx[0].a.hoa_don,'HDM-26-10-00089');
 assert(a.root.innerHTML.includes('Bút toán khi ghi sổ'),'thấy định khoản trước khi lập');
 assert.equal((a.root.innerHTML.match(/class="chip on"/g)||[]).length,3,'mỗi hàng chip tô đúng một chip (kỳ trùng tháng không tô hai)');
 // Đổi chip đối tác: gọi lại đề xuất với đối tác mới.
 await a.click('[data-cntpddt="onepay"]');
 assert.equal(a.goi('can_tru_phi.de_xuat').at(-1).a.doi_tac,'onepay','đổi đối tác gửi đúng lựa chọn');
 // Kế toán lập: một lần lập, không tự ghi sổ.
 await a.click('#cntPdLap');
 assert.equal(a.goi('can_tru_phi.lap').length,1);assert.equal(a.goi('can_tru_phi.xac_nhan').length,0,'kế toán không tự ghi sổ');
 assert(/Không chuyển tiền/.test(a.hoi.at(-1)),'hộp xác nhận nói không chuyển tiền');

 // Ca 2: kế toán trưởng: lập và ghi sổ trong một lần bấm.
 const b=await moi(['Accounts Manager'],{xacNhan:true});
 await b.click('[data-cntcan]');b.g.pick(b.g.choices.find(x=>x.value==='__phi_dt'));await nghi();
 assert(b.document.getElementById('cntPdLap').textContent.includes('Lập phiếu và ghi sổ'));
 await b.click('#cntPdLap');
 assert.equal(b.goi('can_tru_phi.lap').length,1);
 const xn=b.goi('can_tru_phi.xac_nhan');assert.equal(xn.length,1);assert.equal(xn[0].a.ten,'CTSAN-00012','ghi sổ đúng phiếu vừa lập');

 // Ca 3: nhà cung cấp thường (Printeco) không có lối phí đối tác, giữ một chạm v549.
 const c=await moi(['Accounts User'],{grab:false});
 await c.click('[data-cntcan]');
 assert.equal(c.goi('xem_truoc_erp').length,1,'mở thẳng màn trả trước ERP như cũ');

 // Ca 4: thu mua không thấy lối phí đối tác.
 const d=await moi(['Purchase User']);
 await d.click('[data-cntcan]');
 assert(!(d.g.choices||[]).some(x=>x.value==='__phi_dt'),'thu mua không lập phiếu phí');

 // Ca 5: phiếu nháp hiện trên dòng hoá đơn; kế toán trưởng mở và xác nhận.
 const e=await moi(['Accounts Manager'],{xacNhan:true,phieu:[{name:'CTSAN-00012',tong_bu:44071417}]});
 assert(e.root.innerHTML.includes('Phiếu cấn trừ phí CTSAN-00012'),'dòng nói đang có phiếu chờ');
 e.g.phieuDx=[{name:'CTSAN-00012',docstatus:0,trang_thai:'',ly_do:'',tong_bu:44071417,but_toan:'',tu:'2026-09-01',den:'2026-09-30',doi_soat:1}];
 await e.click('[data-cntphidt="0"]');
 await e.click('[data-cntpdxn="CTSAN-00012"]');
 assert.equal(e.goi('can_tru_phi.xac_nhan').length,1,'xác nhận đúng phiếu nháp');
 console.log('Cấn trừ phí đối tác theo đối soát (v673): 5 ca PASS');
})().catch(e=>{console.error(e);process.exit(1);});

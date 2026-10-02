/* v552 (chị Dung 02/10/2026): màn Bút toán hiện số hiệu tài khoản và cho kế
   toán đổi tài khoản một dòng của bút toán NHÁP. Chạy màn thật scrButToanXem
   với API giả, bấm đúng nút như chị Dung trên PKT-2026-00067: vế Có tạm thành
   11211 MB Bank. Không ghi tiền thật. */
'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const dom=require('./dom_gia');
const bep=path.resolve(__dirname,'../../../public/js/bep');
function doc(n){return fs.readFileSync(path.join(bep,n),'utf8');}
async function nghi(){for(let i=0;i<10;i++)await Promise.resolve();await new Promise(r=>setImmediate(r));}
function butToan(nhap,ghi){
 return {ma:'PKT-2026-00067',ngay:'2026-10-02',dien_giai:'[Trả trước khi lên ERP] Cấn hóa đơn ACC-PINV-2026-01919',
  trang_thai:nhap?'Nháp':'Đã ghi sổ',nhap:nhap?1:0,tong:37584000,ghi_duoc:ghi?1:0,sua_duoc:(nhap&&ghi)?1:0,
  dong:[{ma_dong:'r1',tk:'331 - Phải trả cho người bán - TV',ten_tk:'331 - Phải trả cho người bán',no:37584000,co:0,ben:'CÔNG TY TNHH TÁC KHÍ VIỆT',doi_duoc:0},
   {ma_dong:'r2',tk:'Temporary Opening - TV',ten_tk:'Temporary Opening',no:0,co:37584000,ben:'',doi_duoc:(nhap&&ghi)?1:0}]};
}
async function moi({nhap=true,ghi=true,go_tu='11211',chon='11211 - Tiền gửi MB Bank 31561568 - TV'}={}){
 const document=dom.taiLieuGia(),root=document.createElement('div');root.id='vgb';document.body.appendChild(root);
 const calls=[],tin=[],hoi=[];
 const g={frappe:{session:{user:'dung'}},document,console,Promise,JSON,Math,Number,String,Object,Array,Date,Error,RegExp,parseInt,parseFloat,setTimeout,clearTimeout,
  location:{href:'https://erp/bep',pathname:'/bep',hostname:'erp',search:'',hash:''},history:{pushState(){},replaceState(){},back(){}},requestAnimationFrame:f=>f(),
  h:s=>String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'),money:x=>String(x),hsNgayVn:String,toast(){},busy(){},baoTin:s=>tin.push(s),dSkin(){},
  api:async(m,a)=>{calls.push({m,a});
   if(m.endsWith('.xem'))return butToan(nhap,ghi);
   if(m.endsWith('tim_tai_khoan'))return {rows:[
    {ma:'11211 - Tiền gửi MB Bank 31561568 - TV',ten:'11211 - Tiền gửi MB Bank 31561568',kieu:'Bank',can_ben:0},
    {ma:'331 - Phải trả cho người bán - TV',ten:'331 - Phải trả cho người bán',kieu:'Payable',can_ben:1}]};
   if(m.endsWith('doi_tai_khoan'))return {ok:1,loi_nhan:'Đã đổi'};
   return {};}
 };
 g.window=g;g.root=root;vm.createContext(g);
 vm.runInContext(doc('01-khung-app.js'),g);
 const src=doc('21-ke-toan-khac.js');vm.runInContext(src,g);
 /* Hộp thoại giả: ghi lại câu hỏi, trả lời như chị Dung. */
 g.hoiChu=async(t)=>{hoi.push(t);return go_tu;};
 g.hoiChon=async(t,m,ds)=>{hoi.push(t);g.luaChon=ds;return chon;};
 await g.scrButToanXem('PKT-2026-00067');await nghi();
 return {g,root,document,calls,tin,hoi,
  async click(sel){const el=root.querySelector(sel)||document.querySelector(sel);assert(el,'thiếu '+sel);el.dispatchEvent(dom.suKien('click',{},el));await nghi();},
  goi:t=>calls.filter(c=>c.m.endsWith(t))};
}
(async()=>{
 // Ca 1: chị Dung mở bút toán nháp: thấy số hiệu 331, nút đổi chỉ ở vế Có.
 const d=await moi();
 const html=d.root.innerHTML;
 assert(html.includes('331 - Phải trả cho người bán'),'hiện số hiệu 331');
 assert(d.root.querySelector('[data-btdoi="r2"]'),'vế Có có nút Đổi tài khoản');
 assert(!d.root.querySelector('[data-btdoi="r1"]'),'vế Nợ 331 gắn NCC/hoá đơn không có nút đổi');

 // Ca 2: đổi vế Có sang 11211 MB Bank: gõ số hiệu, chọn, gọi đúng API, mở lại màn.
 await d.click('[data-btdoi="r2"]');
 assert.equal(d.goi('tim_tai_khoan')[0].a.tu_khoa,'11211','tìm theo số hiệu chị gõ');
 assert(!d.g.luaChon.some(x=>/^331/.test(x.k)),'danh sách chọn bỏ tài khoản công nợ');
 const doi=d.goi('doi_tai_khoan');assert.equal(doi.length,1);
 assert.deepEqual(doi[0].a,{ma:'PKT-2026-00067',ma_dong:'r2',tk:'11211 - Tiền gửi MB Bank 31561568 - TV'});
 assert.equal(d.goi('.xem').length,2,'đổi xong tải lại bút toán để soát');

 // Ca 3: bấm Huỷ ở hộp gõ thì không gọi gì.
 const h=await moi({go_tu:null});
 await h.click('[data-btdoi="r2"]');
 assert.equal(h.goi('tim_tai_khoan').length+h.goi('doi_tai_khoan').length,0,'huỷ thì không đổi');

 // Ca 4: bút toán đã ghi sổ, hoặc người không có quyền ghi sổ: không có nút đổi.
 const s=await moi({nhap:false});
 assert(!s.root.querySelector('[data-btdoi]'),'đã ghi sổ thì không đổi');
 const k=await moi({ghi:false});
 assert(!k.root.querySelector('[data-btdoi]'),'không quyền ghi sổ thì không đổi');
 console.log('PASS 552: màn Bút toán hiện số hiệu, kế toán đổi vế Có nháp sang 11211 MB Bank');
})().catch(e=>{console.error(e);process.exit(1);});

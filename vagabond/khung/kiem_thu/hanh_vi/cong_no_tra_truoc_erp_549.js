/* v549: hóa đơn trả TRƯỚC KHI LÊN ERP (ca Printeco 04/04/2026). Chạy màn thật
   Công nợ phải trả với API giả, bấm đúng nút "Cấn trừ công nợ" như anh Việt.
   Bản v548 rơi về hộp hướng dẫn khi không có phiếu chi nào trên ERP; ca 2 chốt
   lại đường đó. Không ghi tiền thật. */
'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const dom=require('./dom_gia');
const bep=path.resolve(__dirname,'../../../public/js/bep');
function doc(n){return fs.readFileSync(path.join(bep,n),'utf8');}
async function nghi(){for(let i=0;i<10;i++)await Promise.resolve();await new Promise(r=>setImmediate(r));}
async function moi(vai,{pe=[],cho=[],keToan=false,loiLap=false}={}){
 const document=dom.taiLieuGia(),root=document.createElement('div');root.id='vgb';document.body.appendChild(root);
 const calls=[],tin=[],xacNhan=[];
 const row={name:'ACC-PINV-2026-01226',bill_no:'74',supplier:'NCC',supplier_name:'PRINTECO',ma_ncc:'NC000277',ngay:'2026-04-04',con_no:212090400,account_currency:'VND',currency:'VND',company:'CTY',credit_to:'331',trang_thai:'Còn nợ',tre_ngay:180,cho_duyet:cho};
 let soLan=0;
 const g={frappe:{session:{user:'test'}},document,console,Promise,JSON,Math,Number,String,Object,Array,Date,Error,RegExp,parseInt,parseFloat,setTimeout,clearTimeout,
  location:{href:'https://erp/bep',pathname:'/bep',hostname:'erp',search:'',hash:''},history:{pushState(){},replaceState(){},back(){}},requestAnimationFrame:f=>f(),
  h:s=>String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'),money:String,ngayNgan:String,
  toast(){},busy(){},baoTin:s=>tin.push(s),dSkin(){},errMsg:e=>e.message,
  posChipNut:(a,n)=>'<button '+a+'>'+n+'</button>',kmHangChip:s=>'<div>'+s+'</div>',
  tdkNap:(id,a)=>{g.files=a;},tdkDs:()=>g.files||[],tdkKhoi:()=>'<div></div>',tdkNoi(){},tdkVeLai(){},hsChonCanCoc(){},
  hasRole:r=>vai.indexOf(r)>=0,hsCoQuyenCanCoc:()=>vai.some(v=>['Accounts User','Accounts Manager','AP Kiểm soát (FIN)','System Manager'].indexOf(v)>=0),
  hsCocLan:null,hsThuLaiCanCoc(){},bcTaiVe(){},open(){},
  confirmSheet:async(t,m)=>{xacNhan.push(m);return true;},sinhMaLanNhan:()=>'LN-ma'+(++soLan),
  sheet:(t,ds,chon,cb)=>{g.choices=ds;g.pick=cb;},
  api:async(m,a)=>{calls.push({m,a});
   if(m.endsWith('khoan_da_tra'))return {ncc:'NCC',con_no:212090400,rows:pe};
   if(m.endsWith('xem_truoc_erp'))return {hoa_don:row.name,con_no:212090400,dang_cho:0,cho_duyet:[],ke_toan:keToan,tk_tam:'Temporary Opening - TV'};
   if(m.endsWith('lap_truoc_erp')){if(loiLap)throw new Error('Mất mạng');return {je:'PKT-1',da_ghi_so:keToan};}
   if(m.endsWith('duyet_truoc_erp')||m.endsWith('bo_truoc_erp'))return {ok:1};
   return {cong_ty:'CTY',cac_cong_ty:['CTY'],cac_nhom:['Hàng'],ngay_doc:'2026-10-01',so_hd:1,so_ncc:1,tong_theo_tien:{VND:212090400},dem:{tat_ca:1,con_no:1,qua_han:1},con_nua:false,dong:[row],ke_toan:keToan};}
 };
 g.window=g;g.root=root;vm.createContext(g);
 vm.runInContext(doc('01-khung-app.js'),g);vm.runInContext(doc('15-khuon-danh-sach.js'),g);
 /* hasRole thật của khung đọc S.roles: đặt vai ở đó, không thay hàm. */
 vm.runInContext('S.roles='+JSON.stringify(vai),g);
 const src=doc('16-mua-hang.js');vm.runInContext(src.slice(src.indexOf('/* Công nợ NCC:'),src.indexOf('/* ---------------- Hoa don ban ra')),g);
 await g.scrNoPhaiTra();
 const m={g,root,document,calls,tin,xacNhan,row,
  async click(sel){const el=document.querySelector(sel)||root.querySelector(sel);assert(el,'thiếu '+sel);el.dispatchEvent(dom.suKien('click',{},el));await nghi();},
  goi:t=>calls.filter(c=>c.m.endsWith(t))};
 return m;
}
(async()=>{
 // Ca 1: Uyên (thu mua) bấm Cấn trừ công nợ: mở màn khai, bắt UNC, gửi nháp.
 const u=await moi(['Purchase User']);
 await u.click('[data-cntcan]');
 assert.equal(u.goi('xem_truoc_erp').length,1,'thu mua mở được màn khai, không rơi về hướng dẫn');
 assert.equal(u.tin.length,0,'không hiện hộp hướng dẫn');
 assert(u.document.getElementById('cntTeGui').textContent.includes('Gửi kế toán duyệt'));
 u.document.getElementById('cntTeNgay').value='2026-04-10';
 await u.click('#cntTeGui');
 assert.equal(u.goi('lap_truoc_erp').length,0,'thiếu UNC thì chưa gửi');
 assert(/UNC/.test(u.tin.at(-1)));
 u.g.files=['/private/files/unc-printeco.pdf'];
 u.document.getElementById('cntTeTien').value='300000000';await u.click('#cntTeGui');
 assert.equal(u.goi('lap_truoc_erp').length,0,'vượt dư thì chưa gửi');
 u.document.getElementById('cntTeTien').value='212090400';await u.click('#cntTeGui');
 const lap=u.goi('lap_truoc_erp');assert.equal(lap.length,1);
 assert.equal(lap[0].a.hoa_don,'ACC-PINV-2026-01226');assert.equal(lap[0].a.so_tien,212090400);
 assert.equal(lap[0].a.ngay_tra,'2026-04-10');assert.deepEqual(JSON.parse(lap[0].a.unc),['/private/files/unc-printeco.pdf']);
 assert(/^TE-/.test(lap[0].a.ma_lan),'có mã lần chống gửi hai lần');
 assert(/Có tài khoản tạm/.test(u.xacNhan.at(-1)),'hộp xác nhận nói rõ bút toán, không chuyển tiền');

 // Ca 2 (đúng ca anh Việt): kế toán, hóa đơn KHÔNG có phiếu chi trên ERP.
 // v548 rơi về hướng dẫn; nay mở thẳng màn khai và ghi sổ luôn, không bắt UNC.
 const k=await moi(['System Manager'],{keToan:true});
 await k.click('[data-cntcan]');
 assert.equal(k.goi('khoan_da_tra').length,1);
 assert.equal(k.tin.length,0,'không còn hộp hướng dẫn khi không có phiếu chi');
 assert(k.document.getElementById('cntTeGui').textContent.includes('Ghi sổ cấn trừ'));
 k.document.getElementById('cntTeNgay').value='2026-04-10';await k.click('#cntTeGui');
 assert.equal(k.goi('lap_truoc_erp').length,1,'kế toán ghi được không cần UNC');

 // Ca 3: mất phản hồi rồi bấm lại: CÙNG mã lần, máy chủ nhận ra lần cũ.
 const r=await moi(['System Manager'],{keToan:true,loiLap:true});
 await r.click('[data-cntcan]');r.document.getElementById('cntTeNgay').value='2026-04-10';
 await r.click('#cntTeGui');await r.click('#cntTeGui');
 const hai=r.goi('lap_truoc_erp');assert.equal(hai.length,2);assert.equal(hai[0].a.ma_lan,hai[1].a.ma_lan,'bấm lại giữ mã lần');

 // Ca 4: kế toán có phiếu chi trên ERP vẫn thấy lối trả trước ERP trong danh sách.
 const p=await moi(['Accounts User'],{pe:[{name:'PE-1',con_coc:60,ngay:'2026-09-01',unc:[]}],keToan:true});
 await p.click('[data-cntcan]');
 assert(p.g.choices.some(x=>x.value==='__truoc_erp'),'có lối trả trước ERP');
 assert(p.g.choices.some(x=>x.value==='PE-1'),'vẫn giữ phiếu chi cũ');

 // Ca 5: dòng có nháp chờ duyệt: kế toán thấy Duyệt, thu mua chỉ thấy Rút lại.
 const c=await moi(['Accounts User'],{cho:[{je:'PKT-9',so_tien:1000}],keToan:true});
 assert(c.root.innerHTML.includes('Chờ kế toán duyệt'));
 await c.click('[data-cntduyet="PKT-9"]');assert.equal(c.goi('duyet_truoc_erp')[0].a.je,'PKT-9');
 const t=await moi(['Purchase User'],{cho:[{je:'PKT-9',so_tien:1000}]});
 assert(!t.root.querySelector('[data-cntduyet]'),'thu mua không duyệt được');
 assert(t.root.querySelector('[data-cntbo="PKT-9"]'));

 // Ca 6: không có vai nào thì chỉ có hướng dẫn, không gọi API ghi.
 const n=await moi([]);await n.click('[data-cntcan]');
 assert.equal(n.tin.length,1);assert.equal(n.goi('xem_truoc_erp').length,0);
 console.log('PASS 549: cấn hóa đơn trả trước ERP, thu mua gửi nháp, kế toán ghi sổ, chống gửi hai lần');
})().catch(e=>{console.error(e);process.exit(1);});

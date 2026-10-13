/* Chạy hàm vẽ thật, DOM thật của bộ giả lập; mọi fetch không khai sẵn đều lỗi. */
'use strict';
const assert=require('assert'),vm=require('vm'),{doc,ham,nap}=require('./qr_474_chung');
const {taiLieuGia}=require('./dom_gia');
const tk={bank:'MB',bin:'970422',stk:'VQRQALEAF2999',ten:'Vagabond'};
const golden='00020101021238570010A000000727012700069704220113VQRQALEAF29990208QRIBFTTA530370454061600005802VN62120808TCVG8FRJ630450D4';
function ctx(){const c={console,URLSearchParams,setTimeout,clearTimeout,setInterval:()=>0,clearInterval(){},CFGBH:{qr_quay:tk,qr_nguon:{}},posQuay:{ma:"TCV"},posSepayNhan:0,posSepayGoiY:0,h:s=>String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'),money:n=>String(n),document:taiLieuGia(),fetch:()=>{throw Error('Mạng ngoài bị chặn');}};c.window=c;return nap(c);}
function qr(html){const m=html.match(/<img[^>]+src="([^"]+)"/);assert(m,'Phải có ảnh');assert(m[1].startsWith('data:image/svg+xml'),'Không gọi ảnh mạng');return m[1];}
(async()=>{
 const c=ctx();assert.equal(c.VgbQr.chuoi({bin:tk.bin,stk:tk.stk,tien:160000,noi_dung:'TCVG8FRJ'}),golden);
 const a=qr(c.posKhoiQr('TCVG8FRJ',160000,'','TCV'));const b=qr(c.posKhoiQr('TCVG8FRJ',200000,'','TCV'));assert.notEqual(a,b);
 c.CFGBH.qr_quay={bank:'MB'};const missing=c.posKhoiQr('TCVG8FRJ',160000,'','TCV');assert(!missing.includes('<img'));assert(missing.includes('tài khoản'));assert(missing.includes('160000'));assert(missing.includes('TCVG8FRJ'));c.CFGBH.qr_quay=tk;
 const vendor=c.qrcode;c.qrcode=undefined;assert(c.posKhoiQr('TCVG8FRJ',160000).includes('thư viện'));c.qrcode=vendor;
 // Hai hàm vẽ Sales thật, cùng DOM nhận HTML như trình duyệt.
 for(const [ten,id] of [['dsvVeQr','dsvQr'],['dstVeQr','dstQr']]){
  const o=c.document.createElement('div');o.setAttribute('id',id);c.document.body.appendChild(o);
  Object.assign(c,{DSV_PT:'Chuyển khoản',d:{grand_total:160000,custom_nguon:'Tại chỗ'},dsvNoiDung:'TCVG8FRJ',dsvDiem:'TCV',dsvTuPancake:()=>false,dsTay:{pt:'Chuyển khoản',mon:[{qty:2,rate:80000}],nguon:'Tại chỗ',quay:'TCV',bill:'G8FRJ'},nguonBH:()=>({}),posNoiDungCk:()=> 'TCVG8FRJ'});
  vm.runInContext(ham(doc('vagabond/public/js/bep/08-doanh-so-sales.js'),ten),c);c[ten]();qr(o.innerHTML);
  c.qrcode=undefined;c[ten]();assert(!o.innerHTML.includes('<img'));assert(o.innerHTML.includes('thư viện'));assert(o.innerHTML.includes(tk.stk));c.qrcode=vendor;
 }
 // Bảng QR dùng đúng hàm mở bảng, thư viện hỏng vẫn có chuyển tay.
 vm.runInContext(ham(doc('vagabond/public/js/bep/09-tinh-tien-quay.js'),'posQrSheet'),c);
 c.posBillVua=null;c.qrcode=undefined;c.posQrSheet('TCVG8FRJ',160000,'','','TCV');
 const bang=c.document.body.children[c.document.body.children.length-1];assert(bang.innerHTML.includes('thư viện'));assert(bang.innerHTML.includes(tk.stk));assert(!bang.innerHTML.includes('<img'));c.qrcode=vendor;
 // Raw Pancake là opaque, kể cả Unicode: bộ dựng không viết lại.
 const raw='000201 Páncake nguyên chuỗi';assert.equal(c.VgbQr.chuoi({qr_text:raw}),raw);assert(c.VgbQr.tao({qr_text:raw}).anh);
 console.log('QR474: golden, đổi tiền, thiếu tài khoản/thư viện, Sales x2, Pancake đạt');
})().catch(e=>{console.error(e);process.exit(1);});

// Chạy hàm màn thật với DOM giả, không gọi site production.
const fs=require('fs'), vm=require('vm'), assert=require('assert');
const dg=require('./dom_gia.js');
const src=fs.readFileSync('vagabond/public/js/bep/21-ke-toan-khac.js','utf8');
const ma=src.slice(src.indexOf("var tgdTim ="),src.indexOf('/* ================= CANH BAO PHUONG THUC'));
const tai=dg.taiLieuGia(); let khung, goi=[], thongBao=[], troLai=[];
let rows=[{name:'BT-1',date:'2026-09-09',mo_ta:'Internet',reference_number:'REF-1',nhan_ngan_hang:'MB',dung_duoc:1,vi_sao_khong:'',ma:'BT-1',ten_ban_ghi:'BT-1',tham_chieu:'REF-1',ngay:'2026-09-09',noi_dung:'Internet',tien:100,chi:100,thu:0,tai_khoan:'MB',ly_do:''}];
const that={document:tai,console,frame:(t,html)=>{khung=new dg.ElementGia('div');khung.innerHTML=html;tai.body.children=[khung];return khung;},h:x=>String(x||''),money:x=>String(x),hsNgayVn:x=>x,kmHangChip:x=>x,posChipNut:(a,t)=>'<button '+a+'>'+t+'</button>',busy:()=>{},toast:x=>thongBao.push(x),baoTin:x=>thongBao.push(x),hoiCo:async()=>true,go:async f=>f(),scrHoSoTTView:x=>troLai.push(x),api:async(m,a)=>{goi.push({m,a});return m.endsWith('.gan')?{loi_nhan:'Đã chọn'}:{rows,tong:rows.length,so_tien:12345};}};
that.confirmSheet=async()=>true;vm.createContext(that);vm.runInContext(fs.readFileSync('vagabond/public/js/bep/23-khop-sepay.js','utf8')+'\n'+ma,that);
// v528: gán tay xong gọi hsSauGan (19-ho-so-tt.js) để hỏi nhớ mẫu sao kê; nạp đúng hàm thật đó.
{const s19=fs.readFileSync('vagabond/public/js/bep/19-ho-so-tt.js','utf8');const i=s19.indexOf('async function hsSauGan(');
 const j=s19.slice(i+1).search(/\n(?:async )?function /);vm.runInContext(j<0?s19.slice(i):s19.slice(i,i+1+j),that);}
(async()=>{
await that.scrTimGiaoDich('APP.26.09.015',100);
assert.equal(goi[0].m,'vagabond.doi_soat_sepay.ung_vien');assert.equal(goi[0].a.ma_phieu,'APP.26.09.015');
assert(khung.innerHTML.includes('12345 đ'));assert(!tai.getElementById('tgdT'));assert.equal(goi[0].a.loai,'app');
assert(khung.innerHTML.includes('MB'));assert(khung.innerHTML.includes('REF-1'));
const dong=tai.querySelector('[data-gd]'); await dong.onclick();
assert.equal(goi[1].m,'vagabond.doi_chieu_app.gan');assert.equal(goi[1].a.ma_giao_dich,'BT-1');assert.equal(troLai[0],'APP.26.09.015');
rows[0].vi_sao_khong='Đã dùng ở APP khác';rows[0].dung_duoc=0;goi=[];
await that.scrTimGiaoDich('APP.26.09.016',100); await tai.querySelector('[data-gd]').onclick();
assert.equal(goi.length,1);assert.equal(thongBao.at(-1),'Đã dùng ở APP khác');
that.tgdTim='loc-cu';await that.scrTimGiaoDich('APP.26.09.017',200);assert.equal(goi.at(-1).a.tu_khoa,'');assert.equal(goi.at(-1).a.ma_phieu,'APP.26.09.017');
const hsSrc=fs.readFileSync('vagabond/public/js/bep/19-ho-so-tt.js','utf8');
vm.runInContext(hsSrc.slice(hsSrc.indexOf('function hsCanhBaoDoiChieu('),hsSrc.indexOf('async function hsHanh(')),that);
assert(that.hsCanhBaoDoiChieu({canh_bao_doi_chieu:'Đã huỷ bút toán - không chuyển tiền thêm'}).includes('không chuyển tiền thêm'));
assert.equal(that.hsCanhBaoDoiChieu({}), '');
const batDau=hsSrc.indexOf('async function hsHanh(');
const tiep=hsSrc.slice(batDau+1).search(/\n(?:async )?function /);
vm.runInContext(hsSrc.slice(batDau,batDau+1+tiep),that);
goi=[];troLai=[];
that.hoiCo=async()=>false;
await that.hsHanh('bodoichieu',{ma:'APP-BO'});assert.equal(goi.length,0);
that.hoiCo=async(t,noidung)=>{assert(noidung.includes('Đã duyệt'));assert(noidung.includes('không chuyển tiền thêm'));return true;};
that.api=async(m,a)=>{goi.push({m,a});return {loi_nhan:'Đã bỏ'};};
await that.hsHanh('bodoichieu',{ma:'APP-BO'});
assert.equal(goi[0].m,'vagabond.doi_chieu_app.bo');assert.equal(goi[0].a.name,'APP-BO');assert.equal(troLai[0],'APP-BO');
let ban=[];that.busy=x=>ban.push(x);that.api=async()=>{throw Error('Còn bút toán');};
troLai=[];await that.hsHanh('bodoichieu',{ma:'APP-BO'});
assert.equal(thongBao.at(-1),'Còn bút toán');assert.equal(troLai.length,0);assert.equal(ban.at(-1),false);
console.log('PASS UI #247: API theo hồ sơ, khóa bản ghi, tài khoản/tham chiếu, chặn dòng đã dùng, reset bộ lọc');
})().catch(e=>{console.error(e);process.exitCode=1});

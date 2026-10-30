// #245: lỗi nguồn đơn phải có câu thử lại, không bị biến thành lịch sử rỗng.
// v621: chạy trên trang thật (HTML + chu.js + thanh-vien.js) bằng khung chung
// tv_khung.js thay cho DOM tự chế; giữ nguyên mọi khẳng định cũ.
const assert = require('node:assert/strict');
const { dungTrang, nghi } = require('./tv_khung.js');
(async()=>{
  let duLieu = {ok:1,ten:'Khách',diem:25000,don:[],don_loi:true,co_ho_so:true};
  const t = await dungTrang({ san_sang: { otp: 1, qua: { mo: 1, uu_dai: 'Giảm 20.000đ' } }, toi: () => duLieu });
  const tim = t.tim;
  assert.match(tim('don').children[0].textContent,/Chưa tải được/);
  assert.ok(!tim('don').children.some(x=>x.textContent.includes('Chưa có đơn')));
  const nut = tim('don').children.find(x=>x.tagName==='BUTTON');
  assert.ok(nut && nut.textContent==='Thử lại');
  duLieu = {...duLieu,don_loi:false};
  await nut.onclick(); await nghi();
  assert.match(tim('don').children[0].textContent,/Chưa có đơn/);
  assert.ok(!tim('don').children.some(x=>x.tagName==='BUTTON'));
  assert.match(tim('diem').textContent,/25/);
  duLieu = {...duLieu,don_chua_mo:true};
  await nut.onclick(); await nghi();
  assert.match(tim('don').children[0].textContent,/chưa khả dụng/);
  assert.ok(!tim('don').children.some(x=>x.tagName==='BUTTON'||x.textContent.includes('Chưa có đơn')));
  duLieu = {...duLieu,don_chua_mo:false,don:[{ma_don:'300',luc_tao:'2026-09-19T17:30:00Z',ngay_dat:'2026-09-20',tong:125000,trang_thai:'Đã giao',mau_trang_thai:'xanh',mon:[{ten:'Bánh <script>',sl:2,hinh:'/files/banh.jpg'},{ten:'Bánh 2',sl:1,hinh:'javascript:alert(1)'}]}]};
  await nut.onclick(); await nghi();
  const dong=tim('don').children[0];
  assert.equal(dong.className,'don');
  assert.match(dong.children[0].children[0].textContent,/20\/09\/2026/);
  assert.equal(dong.children[0].children[1].textContent,'Đã giao');
  assert.match(dong.children[0].children[1].className,/xanh/);
  assert.equal(dong.children[1].textContent,'125.000 đ');
  const mon=dong.children.filter(x=>x.className==='mon-don');
  assert.equal(mon.length,2);
  mon.forEach(m=>assert.equal(m.children[0].className,'ph'));
  const anh=mon[0].children[0].children[0];
  assert.equal(anh.src,'/files/banh.jpg');
  assert.equal(mon[1].children[0].textContent,'🍰');
  assert.equal(mon[1].children[0].children.length,0);
  anh.onerror();assert.equal(mon[0].children[0].children[0].textContent,'🍰');
  assert.equal(mon[0].children[1].children[0].textContent,'Bánh <script>');
  console.log('PASS #245: lỗi nguồn, thử lại, rỗng hợp lệ, giữ điểm');
})().catch(e=>{console.error(e);process.exitCode=1;});

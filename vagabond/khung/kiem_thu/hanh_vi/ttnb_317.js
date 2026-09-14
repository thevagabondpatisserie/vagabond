/* #317: chạy màn chi tiết thật và bấm nút đầu/cuối màn, kể cả API lỗi. */
'use strict';
const fs = require('fs'), vm = require('vm'), path = require('path'), assert = require('assert');
const dg = require('./dom_gia');
const src = fs.readFileSync(path.resolve(__dirname, '../../../public/js/bep/16-mua-hang.js'), 'utf8');
async function kiem(loi, nut, nac = 2) {
  const document = dg.taiLieuGia();
  let dich;
  const c = {document, console, window: {}, S: {stack: Array(nac).fill(null)}, h: x => String(x || ''), money: x => String(x || 0),
    frame: (title, html, opt) => {document.body.innerHTML = '<button id="vgbBack"></button>' + html + ((opt || {}).footer || ''); return document.body;},
    api: async () => {if (loi) throw Error('Lỗi thử'); return {name:'TTNB-THU', tien:10, trang_thai:'Cho ke toan', duoc_duyet_buoc_nay:1};},
    go: (fn, replace) => {dich = {fn, replace};}
  };
  vm.createContext(c); vm.runInContext(src, c);
  c.ttnbLoc = {chip:'cho_duyet', ngay:7, tim:'phiếu thử', nguoi:'nguoi-thu'};
  const loc = JSON.stringify(c.ttnbLoc);
  await c.ttnbCt('TTNB-THU');
  const b = document.getElementById(nut);
  assert(b && typeof b.onclick === 'function', 'Nút quay lại chưa gắn hành vi');
  b.onclick();
  assert(dich && dich.fn === c.scrTTNB && dich.replace === (nac > 1), 'Quay lại phải về danh sách TTNB');
  assert.strictEqual(JSON.stringify(c.ttnbLoc), loc, 'Không được mất bộ lọc');
}
function kiemChonYcps() {
  const document = dg.taiLieuGia();
  const c = {document, window:{}, console, h:x=>String(x||''), money:String, soTien:Number,
    kmHangChip:x=>x, posChipNut:(attrs, text)=>'<button '+attrs+'>'+text+'</button>',
    frame:(title,html,opt)=>{document.body.innerHTML=html+(opt.footer||'');return document.body;}};
  vm.createContext(c); vm.runInContext(src,c);
  const query=document.body.querySelectorAll.bind(document.body);
  document.body.querySelectorAll=sel=>sel==='input[id^="dnk_so_tien_"]'?[]:query(sel); // Phiếu thử không có dòng tiền.
  c.dncDm={loai_nghiep_vu:['Tạm ứng','Hoàn ứng']};
  c.dncForm={loai_nghiep_vu:'Hoàn ứng', thuoc_tam_ung:'UNG', cac_khoan:[]};
  for (const can of [true,false]) {
    c.dncTamUng=[{ma:'UNG',ycps_can_thay:can}];c.dncVe([]);
    assert.strictEqual(!!document.getElementById('dncYcps'),can,'Picker hoàn ứng theo cờ máy chủ');
  }
  c.dncForm.loai_nghiep_vu='Tạm ứng';c.dncForm.yeu_cau_phat_sinh='YCPS-CU';c.dncVe([]);
  const btn=document.body.querySelectorAll('[data-dnc]').find(x=>x.getAttribute('data-dnc')==='loai_nghiep_vu|Hoàn ứng');
  btn.click();
  assert.strictEqual(c.dncForm.yeu_cau_phat_sinh,'','Đổi loại phải xoá YCPS sót');
}
(async () => {
  kiemChonYcps();
  const nhac = {window:{}, console}; vm.createContext(nhac); vm.runInContext(src, nhac);
  for (const tt of ['Cho ke toan', 'Cho duyet']) {
    const html = nhac.ttnbKhopSepay({khop_duoc:0, trang_thai:tt});
    assert.strictEqual(html.includes('Duyệt phiếu trước'), tt === 'Cho ke toan');
  }
  const c = {window: {}, console, soTien: Number}; vm.createContext(c); vm.runInContext(src, c);
  function phieu(nv, tien) {return {loai_nghiep_vu:nv, cac_khoan:[{so_tien:tien}]};}
  assert(!c.dncHuongDuyet(phieu('Hoàn ứng', 3000000), 2000000).includes('giám đốc'));
  assert(c.dncHuongDuyet(phieu('Tạm ứng', 3000000), 2000000).includes('giám đốc'));
  assert(c.dncHuongDuyet(phieu('Chi phí', 500001), 2000000).includes('phiếu chi APP'));
  await kiem(false, 'vgbBack');
  await kiem(false, 'ttnbVeDanhSach');
  await kiem(true, 'vgbBack');
  await kiem(false, 'ttnbVeDanhSach', 1);
  console.log('TTNB #317: 4 ca quay lại đạt');
})().catch(e => {console.error(e); process.exitCode = 1;});

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
(async () => {
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

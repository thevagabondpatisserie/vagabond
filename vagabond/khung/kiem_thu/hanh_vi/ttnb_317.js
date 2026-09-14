/* #317: chạy màn chi tiết thật và bấm nút đầu/cuối màn, kể cả API lỗi. */
'use strict';
const fs = require('fs'), vm = require('vm'), path = require('path'), assert = require('assert');
const dg = require('./dom_gia');
const src = fs.readFileSync(path.resolve(__dirname, '../../../public/js/bep/16-mua-hang.js'), 'utf8');
async function kiem(loi, nut) {
  const document = dg.taiLieuGia();
  let dich;
  const c = {document, console, window: {}, h: x => String(x || ''), money: x => String(x || 0),
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
  assert(dich && dich.fn === c.scrTTNB && dich.replace, 'Quay lại phải về danh sách TTNB');
  assert.strictEqual(JSON.stringify(c.ttnbLoc), loc, 'Không được mất bộ lọc');
}
(async () => {
  await kiem(false, 'vgbBack');
  await kiem(false, 'ttnbVeDanhSach');
  await kiem(true, 'vgbBack');
  console.log('TTNB #317: 3 ca quay lại đạt');
})().catch(e => {console.error(e); process.exitCode = 1;});

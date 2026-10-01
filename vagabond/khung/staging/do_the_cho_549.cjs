'use strict';
/* #403 vòng 5: đo thẻ "Chờ kế toán duyệt" trên Chromium THẬT với CSS thật của
   00-nen.js, màn 390x844. Bộ giả lập node không tính CSS nên không thấy được
   ghi chú bị .card{overflow:hidden} cắt mất (Codex finding trên 1978e2b: ghi
   chú một chuỗi dài không dấu cách, mở "Xem đủ" vẫn bị cắt bên phải).
   Không cần site: dựng thẻ bằng đúng hàm cntDongCho của 16-mua-hang.js. */
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const {chromium} = require('playwright');

const bep = path.resolve(__dirname, '../../public/js/bep');
const doc = (n) => fs.readFileSync(path.join(bep, n), 'utf8');
const nen = doc('00-nen.js');
const dau = nen.indexOf('var CSS = `') + 'var CSS = `'.length;
const css = nen.slice(dau, nen.indexOf('`;', dau));
if (!/\.card\{[^}]*overflow:hidden/.test(css)) throw new Error('CSS .card đã đổi, xem lại phép đo');

const g = {console, money: (n) => Number(n).toLocaleString('vi-VN'),
  h: (s) => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;')};
vm.createContext(g);
const k15 = doc('15-khuon-danh-sach.js');
vm.runInContext(k15.slice(k15.indexOf('function ngayNgan'), k15.indexOf('/* Danh sach dai qua')), g);
const s16 = doc('16-mua-hang.js');
vm.runInContext(s16.slice(s16.indexOf('function cntLucGui'), s16.indexOf('async function cntDuyetTruocErp')), g);

const ghiChu = 'UNC-MB-' + '0123456789'.repeat(29);
const the = g.cntDongCho({cho_duyet: [{je: 'PKT-7', so_tien: 212090400,
  unc: ['/f/a.pdf', '/f/b.pdf', '/f/c.pdf'], nguoi_gui: 'Nguyễn Thị Uyên',
  luc_gui: '2026-10-01 15:00:09', ngay_tra: '2026-04-10', dien_giai: ghiChu}]}, true);

(async () => {
  const trinh = await chromium.launch({headless: true});
  try {
    const trang = await trinh.newPage({viewport: {width: 390, height: 844}});
    await trang.setContent('<style>' + css + '</style><div id="vgb"><div style="padding:12px">' + the + '</div></div>');
    await trang.evaluate(() => { document.querySelector('details').open = true; });
    const kq = await trang.evaluate(() => {
      const the = document.querySelector('.card').getBoundingClientRect();
      const dong = [...document.querySelectorAll('details > div')].map((d) => ({
        chu: d.textContent.slice(0, 24), rong: d.scrollWidth, khung: d.clientWidth,
        phai: Math.round(d.getBoundingClientRect().left + d.scrollWidth)}));
      const bo = document.querySelector('[data-cntbo]').getBoundingClientRect();
      return {the_phai: Math.round(the.right), dong, nut_day: Math.round(bo.bottom),
        chu_mo: document.querySelector('details').innerText};
    });
    console.log(JSON.stringify({the_phai: kq.the_phai, nut_day: kq.nut_day, dong: kq.dong}));
    const hong = [];
    kq.dong.forEach((d) => { if (d.rong > d.khung + 1 || d.phai > kq.the_phai) hong.push('dòng bị cắt: ' + d.chu); });
    if (!kq.chu_mo.includes(ghiChu.slice(-40))) hong.push('ghi chú mở ra không đủ');
    if (!kq.chu_mo.includes('lúc 01/10/2026 15:00')) hong.push('phần mở không nhắc lúc gửi');
    if (kq.nut_day > 844) hong.push('nút Từ chối ra ngoài màn đầu 844px');
    if (hong.length) { console.error('HỎNG 549 thẻ chờ duyệt: ' + hong.join('; ')); process.exitCode = 1; return; }
    console.log('PASS 549 thẻ chờ duyệt trên Chromium 390x844: ghi chú dài tự xuống dòng, nút trong màn đầu');
  } finally { await trinh.close(); }
})().catch((e) => { console.error(e); process.exit(1); });

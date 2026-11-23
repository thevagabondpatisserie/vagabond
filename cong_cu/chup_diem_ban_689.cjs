/* v689: chụp và đo hai màn có chip điểm bán đổi theo danh mục (Biên nhận nộp tiền mặt,
 * Hoá đơn bán ra) trên Chromium 390x844, chạy ĐÚNG mã 39-bien-nhan-tien.js, 16-mua-hang.js
 * thật với API giả lập. Danh mục giả có bốn điểm, điểm thứ tư "Hội chợ" đang tắt.
 *
 * Đo: không cuộn ngang; chip, nút bấm được cao từ 44 điểm; chữ trong vùng màn từ 13 điểm.
 * Bằng chứng loại "tệp trong repo, API giả lập, CSS nền của app (00-nen.js)".
 *
 * Chạy: node cong_cu/chup_diem_ban_689.cjs /thu/muc/anh
 * Mã trả 0: đạt hết; 1: có số đo hỏng; 2: thiếu Playwright/Chromium.
 */
'use strict';
var fs = require('fs');
var path = require('path');
var GOC = path.resolve(__dirname, '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
var RA = process.argv[2] || '/tmp';
var pw;
try { pw = require('playwright'); } catch (e) { console.log('THIẾU Playwright, chưa đo được'); process.exit(2); }

function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
function layHam(src, ten) {
  var dau = src.search(new RegExp('(?:async )?function ' + ten + '\\('));
  if (dau < 0) throw new Error('Khong thay ham ' + ten);
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Ham ' + ten + ' khong dong ngoac');
}
function cssNen() {
  var n = doc('00-nen.js');
  var a = n.indexOf('var CSS = `') + 'var CSS = `'.length;
  return n.slice(a, n.indexOf('`;', a));
}
var NEN = doc('00-nen.js');
var HAM = ['h', 'money', 'today'].map(function (t) { return layHam(NEN, t); }).join('\n') + '\n' +
  layHam(doc('09-tinh-tien-quay.js'), 'posChipNut') + '\n' +
  ['15-khuon-danh-sach.js', '21-ke-toan-khac.js', '49-tru-kho-bu.js', '13-khuyen-mai.js', '16-mua-hang.js', '39-bien-nhan-tien.js'].map(doc).join('\n');

var DIEM = [
  { ma: 'SALES', ten: 'Sales Online', ten_ngan: 'Sales Online' }, { ma: 'TCV', ten: 'The Vagabond District 1', ten_ngan: 'District 1' },
  { ma: 'NVHTN', ten: 'Nhà Văn Hóa Thanh Niên', ten_ngan: 'NVHTN' }, { ma: 'SUKIEN', ten: 'Bán hàng sự kiện - hội chợ', ten_ngan: 'Hội chợ' },
];
var FX = {
  'vagabond.nop_quy.danh_sach': { ds: [
    { name: 'NQ-2026-08208', trang_thai: 'Đã nộp quỹ', ten_diem_ban: 'Sales Online', tu_ngay: '2026-11-12', den_ngay: '2026-11-22', tong_thuc_nhan: 5006000, ten_nguoi_nop: 'Thu ngân', ten_nguoi_nhan: 'Kế toán' },
    { name: 'NQ-2026-08204', trang_thai: 'Chờ ký nhận', ten_diem_ban: 'Nhà Văn Hóa Thanh Niên', tu_ngay: '2026-11-15', den_ngay: '2026-11-22', tong_thuc_nhan: 1840000, ten_nguoi_nop: 'Thu ngân', ten_nguoi_nhan: 'Kế toán' }],
    dem: { '': 2, 'Nháp': 0, 'Chờ ký nhận': 1, 'Đã nộp quỹ': 1, 'Đã huỷ': 0 }, tong: 6846000 },
  'vagabond.nop_quy.doanh_thu_diem': { diem: DIEM, chon: '', theo_ngay: [], tong_tien_mat: 0 },
  'vagabond.ke_toan.ds_hoa_don_ban': { hd: [{ name: 'ACC-SINV-2026-00001', diem: 'SUKIEN', grand_total: 105000, posting_date: '2026-11-21', customer_name: 'Khách lẻ', docstatus: 1 }],
    diem_ds: DIEM.map(function (d) { return { ma: d.ma, ten: d.ten_ngan }; }), tong_dong: 1, bi_cat: 0, dem: {}, nhom: [], tu: '2026-10-24', den: '2026-11-23', tong: 105000, con_thu: 0 },
};

var STUB = [
  'var S = { stack: [1], roles: ["Accounts Manager"] }; var root = document.getElementById("vgb");',
  'function frame(t, html, opt) { opt = opt || {}; root.innerHTML = "<div class=\\"vh\\"><b>" + h(t) + "</b></div><div class=\\"vb\\" id=\\"vgbBody\\">" + html + "</div>"; return document.getElementById("vgbBody"); }',
  'function api(m, a) { var r = FX[m]; return r === undefined ? Promise.reject(new Error("API giả lập thiếu " + m)) : Promise.resolve(JSON.parse(JSON.stringify(r))); }',
  'function go(f) { return f(); } function toast() {} function errMsg(e) { return (e && e.message) || ""; } function hasRole() { return true; } function back() {}',
].join('\n');

async function chay() {
  var b = await pw.chromium.launch();
  var trang = await b.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  var loi = [];
  trang.on('pageerror', function (e) { loi.push(e.message); });
  await trang.setContent('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>' + cssNen() +
    '</style></head><body><div id="vgb"></div></body></html>');
  await trang.addScriptTag({ content: 'var FX = ' + JSON.stringify(FX) + ';\n' + STUB + '\n' + HAM });
  var hong = [];
  async function doDo(ten, vung) {
    var kq = await trang.evaluate(function (vung) {
      var r = { tran: document.scrollingElement.scrollWidth > window.innerWidth + 1, nhoNut: [], nhoChu: [] };
      var goc = Array.prototype.slice.call(document.querySelectorAll(vung));
      function trong(n) { return goc.some(function (g) { return g.contains(n); }); }
      Array.prototype.slice.call(document.querySelectorAll('button, [role=button]')).filter(trong).forEach(function (n) {
        var rc = n.getBoundingClientRect();
        if (rc.width && rc.height < 43.5) r.nhoNut.push((n.textContent || '').trim().slice(0, 30) + ' ' + Math.round(rc.height));
      });
      var tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      while (tw.nextNode()) {
        var t = tw.currentNode, s = (t.nodeValue || '').trim();
        if (!s || !t.parentElement || !trong(t.parentElement)) continue;
        var px = parseFloat(getComputedStyle(t.parentElement).fontSize);
        if (px < 12.95 && t.parentElement.getBoundingClientRect().width) r.nhoChu.push(s.slice(0, 24) + ' ' + px);
      }
      return r;
    }, vung);
    if (kq.tran) hong.push(ten + ': cuộn ngang');
    if (kq.nhoNut.length) hong.push(ten + ': nút thấp hơn 44: ' + kq.nhoNut.slice(0, 5).join(' | '));
    if (kq.nhoChu.length) hong.push(ten + ': chữ dưới 13: ' + kq.nhoChu.slice(0, 5).join(' | '));
  }
  async function chup(ten, ham, vung) {
    await trang.evaluate(ham);
    await trang.waitForTimeout(300);
    await doDo(ten, vung);
    await trang.screenshot({ path: path.join(RA, ten + '.png') });
  }
  /* Đo đúng hàng chip điểm bán là phần PR này đổi. */
  await chup('689-1-bien-nhan', function () { return scrBntDs(); }, '[data-bntdiem]');
  var chipBn = await trang.evaluate(function () { return Array.prototype.slice.call(document.querySelectorAll('[data-bntdiem]')).map(function (x) { return x.textContent.trim(); }); });
  if (chipBn.join('|').indexOf('Hội chợ') < 0) hong.push('689-1: thiếu chip Hội chợ ' + chipBn.join('|'));
  await chup('689-2-hoa-don-ban-ra', function () { return scrHdBan(); }, '[data-ktbquay]');
  var chipHd = await trang.evaluate(function () { return Array.prototype.slice.call(document.querySelectorAll('[data-ktbquay]')).map(function (x) { return x.textContent.trim(); }); });
  if (chipHd.join('|').indexOf('Hội chợ') < 0) hong.push('689-2: thiếu chip Hội chợ ' + chipHd.join('|'));
  await b.close();
  if (loi.length) hong.push('lỗi trang: ' + loi.slice(0, 3).join(' | '));
  console.log('Chip Biên nhận: ' + chipBn.join(' | '));
  console.log('Chip Hoá đơn bán ra: ' + chipHd.join(' | '));
  console.log(hong.length ? 'HỎNG:\n- ' + hong.join('\n- ') : 'Đạt: không cuộn ngang, chip từ 44 điểm, chữ từ 13 điểm.');
  process.exit(hong.length ? 1 : 0);
}
chay().catch(function (e) { console.log('Lỗi chạy: ' + e.message); process.exit(2); });

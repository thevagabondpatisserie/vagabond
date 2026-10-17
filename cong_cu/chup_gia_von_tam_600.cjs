/* Chụp và đo màn "Giá vốn tạm tính" (thẻ kiểu chip, 17/10/2026) trên
 * Chromium 390x844, chạy ĐÚNG mã 53-gia-von-tam.js thật với API giả lập.
 *
 * Dữ liệu dựng bằng chính gia_von_tam.dung_bang / tinh_phieu (python), tên
 * món theo ảnh anh Việt gửi 17/10. Đo: không cuộn ngang, mọi chữ trong thẻ
 * từ 13px, ô số không bị cắt chữ (scrollWidth > clientWidth).
 *
 * Bằng chứng loại "tệp trong repo, API giả lập, CSS nền của app (00-nen.js)
 * cộng CSS của màn". KHÔNG thay được ảnh trên site thật (thiếu CSS Frappe).
 *
 * Chạy: node cong_cu/chup_gia_von_tam_600.cjs /thu/muc/anh
 * Mã trả 0: đạt hết; 1: có số đo hỏng; 2: thiếu Playwright/Chromium.
 */
'use strict';
var fs = require('fs');
var path = require('path');
var cp = require('child_process');
var GOC = path.resolve(__dirname, '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
var RA = process.argv[2] || '/tmp';
var pw;
try { pw = require('playwright'); } catch (e) { console.log('THIẾU Playwright, chưa đo được'); process.exit(2); }

function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
function layHam(src, ten) {
  var dau = src.indexOf('function ' + ten + '(');
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
var HAM = ['h', 'money', 'num', 'kl', 'anhMon', 'vgbChuan', 'vgbKhop'].map(function (t) { return layHam(NEN, t); }).join('\n') +
  '\n' + layHam(doc('09-tinh-tien-quay.js'), 'posChipNut');

var py = [
  'import json, sys', 'sys.path.insert(0, sys.argv[1])',
  'from vagabond.khung.kiem_thu import nen', 'nen.gia_lap()',
  'from vagabond import gia_von_tam as G',
  'ban = [',
  ' {"ma": "B1", "ten": "Bánh Ổ BOHOL Cheesecake, size 18cm", "nhom": "Bánh ổ sinh nhật", "dvt": "Cái"},',
  ' {"ma": "B2", "ten": "Bánh Ổ Epi, size 12cm", "nhom": "Bánh ổ sinh nhật", "dvt": "Cái"},',
  ' {"ma": "B3", "ten": "Bánh Ổ Epi, size 16cm", "nhom": "Bánh ổ sinh nhật", "dvt": "Cái"},',
  ' {"ma": "B4", "ten": "Bánh Ổ Greengold, size 16cm", "nhom": "Bánh ổ sinh nhật", "dvt": "Cái"},',
  ' {"ma": "L1", "ten": "Slice MEKONG Cheesecake", "nhom": "Bánh lạnh", "dvt": "Cái"},',
  ' {"ma": "N1", "ten": "Bánh Dứa Bơ Nâu", "nhom": "Bánh nướng", "dvt": "Cái"},',
  ' {"ma": "N2", "ten": "Shiopan Kem Trứng Muối & Chà Bông Cay", "nhom": "Bánh nướng", "dvt": "Cái"}]',
  'ket = {"K1": {"gia": 174575, "thieu": set(), "vong": False}, "K2": {"gia": 52278, "thieu": set(), "vong": False},',
  ' "K3": {"gia": 90807, "thieu": set(), "vong": False}, "K4": {"gia": 380000, "thieu": set(), "vong": False},',
  ' "K5": {"gia": 23885, "thieu": set(), "vong": False}, "K6": {"gia": 9000, "thieu": {"X1", "X2", "X3"}, "vong": False},',
  ' "K7": {"gia": 379233, "thieu": set(), "vong": False}}',
  'ma_bom = {"B1": "K1", "B2": "K2", "B3": "K3", "B4": "K4", "L1": "K5", "N1": "K6", "N2": "K7"}',
  'gia_ban = {"B1": 1060000, "B2": 600000, "B3": 750000, "B4": 1250000, "L1": 160000, "N1": 45000, "N2": 65000}',
  'ten = {"X1": "BTP Brown Butter", "X2": "BTP Nước ép dứa", "X3": "BTP Thịt bí"}',
  'he_so = {"Bánh ổ sinh nhật": 4, "Bánh lạnh": 5}',
  'b = G.dung_bang(ban, ma_bom, ket, gia_ban, {"B1": ("2026-10-12", 170000)}, he_so, ten, {})',
  'b.update({"he_so": he_so, "cap_nhat_luc": "23:05", "sua_duoc": True})',
  'GM = {"NVL1": {"gia": 30.0, "nguon": "Giá kho", "thieu": 0, "vong": False}, "BTP1": {"gia": 400.0, "nguon": "Công thức", "thieu": 0, "vong": False}}',
  'thu = []',
  'for p in [{"name": "GT-2610-001", "ten_mon": "Tart chanh dây", "nhom": "Bánh lạnh", "so_ra": 4, "gia_ban_du_kien": 95000, "dong": [{"item_code": "NVL1", "so_luong": 1000}, {"item_code": "BTP1", "so_luong": 50}, {"ten": "Chanh dây", "dvt": "Gram", "so_luong": 200, "don_gia_tay": 50}]},',
  '          {"name": "GT-2610-002", "ten_mon": "Mousse xoài cát Hòa Lộc", "nhom": "", "so_ra": 1, "gia_ban_du_kien": 0, "dong": [{"item_code": "NVL1", "so_luong": 300}]}]:',
  '  c = G.chuan_phieu(p); r = dict(c, **G.tinh_phieu(c, lambda m: GM[m], he_so)); r.update(name=p["name"]); thu.append(r)',
  'lt = G.loc_trang_thu(thu); lt.update(tong=len(thu), trang_thai="", nhom="", khoang="", he_so=he_so)',
  'sys.stdout.write(json.dumps({"ban": b, "thu": thu, "lt": lt, "nhom_ban": [{"ten": n, "nhan": G.nhan_nhom(n)} for n in G.NHOM_BAN]}, ensure_ascii=False, default=str))'
].join('\n');
var DL = JSON.parse(cp.execFileSync('python3', ['-c', py, GOC], { encoding: 'utf8' }));

var STUB = [
  'var S = { stack: [], chuaLuu: "", chuaLuuNac: null };',
  'function frame(t, html, opt) { document.getElementById("tieuDe").textContent = t; var b = document.getElementById("vgbBody");',
  '  b.innerHTML = html; document.getElementById("chan").innerHTML = (opt && opt.footer) || ""; b.onclick = null; return b; }',
  'function api(d, ts) { if (d === "vagabond.gia_von_tam.tinh") return Promise.resolve(JSON.parse(JSON.stringify(DL.ban)));',
  '  if (d === "vagabond.gia_von_tam.ds_thu") return Promise.resolve(Object.assign({}, DL.lt, { nhom_ban: DL.nhom_ban, sua_duoc: true, tu_khoa: "" }));',
  '  if (d === "vagabond.gia_von_tam.tinh_thu") return Promise.resolve(DL.thu[0]);',
  '  return Promise.resolve({}); }',
  'function go(f) { S.stack.push(f); return f(); } function back() {} function toast() {} function busy() {}',
  'function vgbBoChuaLuu() {} function baoTin() {} function confirmSheet() { return Promise.resolve(false); }'
].join('\n');

(async function () {
  var b;
  try { b = await pw.chromium.launch(); } catch (e) { console.log('THIẾU Chromium: ' + e.message); process.exit(2); }
  var pg = await b.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  await pg.setContent('<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<style>' + cssNen() + '</style></head><body><div id="vgb"><div style="background:#4dd8ef;padding:18px 16px;font-size:20px;font-weight:700;text-align:center" id="tieuDe"></div>' +
    '<div id="vgbBody" style="padding:12px"></div><div id="chan" style="padding:0 12px 20px"></div></div></body></html>');
  await pg.addScriptTag({ content: 'var DL = ' + JSON.stringify(DL) + ';\n' + HAM + '\n' + STUB + '\n' + doc('53-gia-von-tam.js') });
  var hong = [];
  async function doMan(ten) {
    var so = await pg.evaluate(function () {
      var ra = { cuonNgang: document.documentElement.scrollWidth - window.innerWidth, chuNho: [], cat: [], tran: [] };
      /* Ô nào lòi ra ngoài mép màn (trừ trong hàng chip cuộn ngang) cũng tính là hỏng,
         kể cả khi trang có overflow ẩn làm scrollWidth không đổi. Nền app đặt
         box-sizing trong #vgb nên trang đo phải bọc đúng #vgb như app thật. */
      document.querySelectorAll('#vgb input, #vgb textarea, #vgb button, #vgb .card, .shb, .shb input, .shi').forEach(function (e) {
        for (var a = e.parentElement; a; a = a.parentElement) { var ox = getComputedStyle(a).overflowX; if (ox === 'auto' || ox === 'scroll') return; }
        var r = e.getBoundingClientRect();
        if (r.width && r.right > window.innerWidth + 0.5) ra.tran.push((e.id || e.className || e.tagName) + ' ' + Math.round(r.right) + 'px');
      });
      document.querySelectorAll('.gvt-the *, .gvt-nhom *').forEach(function (e) {
        if (!e.childNodes.length || ![].some.call(e.childNodes, function (n) { return n.nodeType === 3 && n.textContent.trim(); })) return;
        var c = parseFloat(getComputedStyle(e).fontSize);
        if (c < 13) ra.chuNho.push(e.textContent.trim().slice(0, 30) + ' ' + c + 'px');
      });
      document.querySelectorAll('.gvt-o .v, .gvt-o .l, .gvt-c').forEach(function (e) {
        /* Đo chữ thật bằng Range: ellipsis làm scrollWidth đôi khi bằng clientWidth. */
        var r = document.createRange(); r.selectNodeContents(e);
        if (r.getBoundingClientRect().width > e.getBoundingClientRect().width + 0.5 || e.scrollWidth > e.clientWidth + 1) ra.cat.push(e.textContent.trim());
      });
      return ra;
    });
    console.log(ten + ': cuộn ngang ' + so.cuonNgang + 'px, chữ dưới 13px ' + so.chuNho.length + ', ô bị cắt chữ ' + so.cat.length + ', ô lòi mép ' + so.tran.length);
    so.chuNho.concat(so.cat, so.tran).forEach(function (x) { console.log('   ' + x); });
    if (so.cuonNgang > 0 || so.chuNho.length || so.cat.length || so.tran.length) hong.push(ten);
  }
  await pg.evaluate(function () { return scrGiaVonTam(); });
  await pg.waitForTimeout(200);
  await doMan('Món đang bán');
  await pg.screenshot({ path: path.join(RA, 'gvt-mon-ban.png'), fullPage: true });
  await pg.evaluate(function () { return gvtDoiTab('thu'); });
  await pg.waitForTimeout(200);
  await doMan('Món thử');
  await pg.screenshot({ path: path.join(RA, 'gvt-mon-thu.png'), fullPage: true });
  /* Codex #486 v7: màn nhập phiếu có thẻ nhóm bán, chạm mở sheet có ô tìm. */
  await pg.evaluate(function () { return gvtMoPhieu(GVT.thu.ds[0]); });
  await pg.waitForTimeout(200);
  await doMan('Màn nhập phiếu');
  await pg.evaluate(function () { return gvtChonNhom(); });
  await pg.waitForTimeout(100);
  await doMan('Sheet nhóm bán');
  await pg.screenshot({ path: path.join(RA, 'gvt-sheet-nhom.png') });
  await b.close();
  console.log(hong.length ? 'HỎNG: ' + hong.join(', ') : 'ĐẠT');
  process.exit(hong.length ? 1 : 0);
})();

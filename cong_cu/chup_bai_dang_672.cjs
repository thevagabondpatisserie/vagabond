/* Chụp và đo các màn Bài đăng đổi ở v672 (anh Việt 18/11/2026) trên Chromium
 * 390x844, chạy ĐÚNG mã 75-bai-dang.js thật với API giả lập:
 *   1. màn soạn bài Sonneto có chữ Threads dài (chip Sonneto ở dòng Chủ đề, kênh
 *      không có Zalo OA, bảng Kiểm báo số bài nối tiếp, đếm chữ Threads);
 *   2. sheet Sửa chủ đề có mục Thương hiệu;
 *   3. sheet Kết nối kênh hai khối The Vagabond, Sonneto;
 *   4. Kho bản thảo và lịch có chip Sonneto trên thẻ;
 *   5. bài đã đăng mà Threads mới lên một phần (ghi chú vàng);
 *   6. bài The Vagabond bật Google Posts: xem trước một ảnh 4:3 có nút Đặt hàng,
 *      bảng Kiểm chặn chữ có số điện thoại và báo chỉ đăng ảnh đầu (v672 Google);
 *   7. Google Posts loại Ưu đãi: chip loại, ô tiêu đề, giờ, mã giảm giá, điều khoản, không có nút Đặt hàng.
 * Dữ liệu bảng Kiểm dựng bằng chính bai_dang.kiem_bai (python).
 *
 * Đo: không cuộn ngang, không ô nào lòi mép, chữ từ 13px, nút và ô bấm cao từ 44px.
 * Bằng chứng loại "tệp trong repo, API giả lập, CSS nền của app (00-nen.js) cộng CSS
 * của màn". KHÔNG thay được ảnh trên site thật (thiếu CSS Frappe).
 *
 * Chạy: node cong_cu/chup_bai_dang_672.cjs /thu/muc/anh
 * Mã trả 0: đạt hết; 1: có số đo hỏng; 2: thiếu Playwright/Chromium.
 */
'use strict';
var fs = require('fs');
var path = require('path');
var cp = require('child_process');
var GOC = path.resolve(__dirname, '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
var PUB = path.join(GOC, 'vagabond', 'public');
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
var HAM = ['h', 'money'].map(function (t) { return layHam(NEN, t); }).join('\n') + '\n' +
  ['crmTrong', 'crmMoSheet'].map(function (t) { return layHam(doc('58-crm.js'), t); }).join('\n');

var py = [
  'import json, sys', 'sys.path.insert(0, sys.argv[1])',
  'from vagabond.khung.kiem_thu import nen', 'nen.gia_lap()',
  'from vagabond import bai_dang as x',
  'import datetime as dt',
  'th = ("🎓 KHOÁ HỌC ENTREMET CĂN BẢN\\n\\n" + "Một chiếc entremet đẹp bắt đầu từ trụ cột: lớp mousse đủ đứng, lớp insert đủ chua để cân vị, lớp đế giòn giữ nhịp. " * 3 +',
  '  "\\n\\n" + "Khoá học đi qua từng lớp, từ cách cân gelatin tới cách đổ khuôn không bọt khí, để học viên tự dựng được công thức của riêng mình. " * 3 +',
  '  "\\n\\n" + "Học viên thực hành trên khuôn thật, mang về ba chiếc bánh và sổ công thức. " * 2 + "\\n\\n📍 Lớp ở xưởng Tân Bình\\n🗓️ Khai giảng tháng 12")',
  'anh = [{"name": "a1", "ten": "lop.jpg", "url": "/assets/vagabond/images/quay-tcv.jpg", "khung": "4:5", "rong": 1080, "cao": 1350}]',
  'ban = {"fb": {"chu": th}, "ig": {"chu": th[:900]}, "th": {"chu": th}}',
  'bai = {"name": "BD-26-11-7600", "tieu_de": "KHOÁ HỌC ENTREMET CĂN BẢN", "trang_thai": "Nháp", "kieu": "Bài đăng", "y_chinh": "Khoá học entremet căn bản, khai giảng tháng 12.",',
  '  "kenh_chon": ["fb", "ig", "th"], "hen_luc": "2026-11-20 19:30", "ban_luu": 4, "anh": anh, "ban": ban, "kenh": [], "duyet_luc": "", "luu_luc": "10:46",',
  '  "sua": True, "tu_dong": ["fb", "ig"], "hieu": "sonneto", "ten_hieu": "Sonneto", "kenh_hieu": ["fb", "ig", "th"],',
  '  "chu_de": {"ma": "CD-7500", "ten": "Sonneto Social", "bt": "🎓", "cta": []}, "the": ["entremet"], "sao": 0, "chan_bai": [], "yeu_cau_ai": "",',
  '  "cho_gd": 0, "gui_gd": "", "gui_gd_luc": "", "gd_dong_y_luc": "", "ly_do_tra": ""}',
  'bai["kiem"] = x.kiem_bai(bai, dt.datetime(2026, 11, 18, 10, 46), [], [], {"fb", "ig"})',
  'bai["cho_kenh"] = {k: x.anh_cho_kenh(anh, k) for k in bai["kenh_chon"]}',
  'xong = dict(bai, trang_thai="Đã đăng", sua=False, kiem=[], kenh=[',
  '  {"k": "fb", "tt": "Đã đăng", "link": "https://facebook.com/1", "luc": "19:30", "tu": 1, "loi": "", "dang_duoc": 0},',
  '  {"k": "ig", "tt": "Đã đăng", "link": "https://instagram.com/p/1", "luc": "19:31", "tu": 1, "loi": "", "dang_duoc": 0},',
  '  {"k": "th", "tt": "Đã đăng", "link": "https://threads.net/1", "luc": "19:31", "tu": 1, "loi": "Phần 1 đã lên Threads nhưng phần 2/3 chưa lên (Token Threads thiếu quyền đăng bài). Mở Threads, đăng tay tiếp từ phần 2 bằng cách trả lời bài vừa lên. Token Threads cần quyền threads_manage_replies để tự đăng bài nối tiếp.", "dang_duoc": 0}])',
  'cd = {"ds": [{"ma": "CD-7494", "ten": "Giới thiệu bánh ổ", "bt": "🎂", "cta": ["⏰ Đặt trước 48 tiếng"], "so": 16, "hieu": "vagabond"},',
  '  {"ma": "CD-7500", "ten": "Sonneto Social", "bt": "🎓", "cta": [], "so": 41, "hieu": "sonneto"}], "so_sao": 2, "tong": 139, "khong_chu_de": 2, "sua": True}',
  'bt = [{"name": "BD-1", "tieu_de": "[Sonneto Social] Khoá học entremet căn bản", "trich": "Một chiếc entremet đẹp bắt đầu từ trụ cột...", "trang_thai": "Nháp", "luc": "2026-11-18 10:40", "nguoi": "Marketing", "so_anh": 0, "anh": "", "chu_de": "CD-7500", "the": [], "sao": 0, "cho_gd": 0, "tra": 0, "hieu": "sonneto"},',
  '  {"name": "BD-2", "tieu_de": "[Giới thiệu Bánh ổ] 260811 - bánh ổ MONSOON", "trich": "🌧️ MONSOON. Chữ Monsoon đến từ tiếng Ả Rập...", "trang_thai": "Nháp", "luc": "2026-11-18 10:41", "nguoi": "Marketing", "so_anh": 1, "anh": "/assets/vagabond/images/quay-sales.jpg", "chu_de": "CD-7494", "the": ["monsoon"], "sao": 1, "cho_gd": 0, "tra": 0, "hieu": "vagabond"}]',
  'lich = [{"name": "BD-3", "tieu_de": "Khoá học entremet căn bản", "trang_thai": "Đã hẹn giờ", "gio": "19:30", "ngay": "2026-11-20", "luc": "2026-11-20 19:30", "anh": "/assets/vagabond/images/quay-tcv.jpg", "kieu": "Bài đăng", "hieu": "sonneto",',
  '  "kenh": [{"k": "fb", "tt": "Đã hẹn giờ"}, {"k": "ig", "tt": "Đã hẹn giờ"}, {"k": "th", "tt": "Đã hẹn giờ"}]}]',
  'kn = {"fb": {"ok": 1, "chu": "Tự đăng lên Trang The Vagabond Pâtisserie"}, "ig": {"ok": 1, "chu": "Tự đăng lên @thevagabondpatisserie"},',
  '  "th": {"ok": 1, "chu": "Tự đăng lên @thevagabond.patisserie · token dùng tới 15/01/2027"}, "zl": {"ok": 0, "chu": "Zalo chưa duyệt quyền đăng bài viết. Bài lên Zalo OA phải đăng tay."},',
  '  "gg": {"ok": 0, "chu": "Google chưa mở quyền Google Business Profile API cho tiệm (đang chờ Google duyệt) hoặc đang giới hạn số lần gọi. Đăng tay bài này, vài giờ sau bấm Thử lại.", "loi": 1}}',
  'anh2 = anh + [{"name": "a2", "ten": "quay.jpg", "url": "/assets/vagabond/images/quay-sales.jpg", "khung": "1:1", "rong": 1080, "cao": 1080}]',
  'chu_gg = "🎂 MONSOON\\n\\nBánh ổ Monsoon mới ra lò cuối tuần này: lớp mousse xoài chín, insert chanh dây, đế sablé giòn. Đặt trước 48 tiếng, hotline 0901 234 567."',
  'gg = dict(bai, name="BD-26-11-7601", tieu_de="MONSOON", hieu="vagabond", ten_hieu="The Vagabond", kenh_hieu=["fb", "ig", "th", "zl", "gg"], kenh_chon=["fb", "gg"],',
  '  chu_de={"ma": "CD-7494", "ten": "Giới thiệu bánh ổ", "bt": "🎂", "cta": []}, anh=anh2, ban={"fb": {"chu": chu_gg}, "gg": {"chu": chu_gg}})',
  'gg["kiem"] = x.kiem_bai(gg, dt.datetime(2026, 11, 18, 10, 46), [], [], {"fb"})',
  'gg["cho_kenh"] = {k: x.anh_cho_kenh(anh2, k) for k in gg["kenh_chon"]}',
  'uu = dict(gg, name="BD-26-11-7602", ban={"fb": {"chu": chu_gg}, "gg": {"chu": "Giảm 10% bánh ổ Monsoon cho đơn đặt online tuần này.", "loai": "uu_dai", "tieu_de": "Giảm 10% bánh ổ Monsoon",',
  '  "bat_dau": "2026-11-20T08:00", "ket_thuc": "2026-11-23T22:00", "ma_giam": "MONSOON10", "dieu_khoan": "Áp dụng đơn online, không cộng ưu đãi khác."}})',
  'uu["kiem"] = x.kiem_bai(uu, dt.datetime(2026, 11, 18, 10, 46), [], [], {"fb"})',
  'so = {"fb": {"ok": 0, "chu": "Chưa điền Mã Trang Facebook Sonneto ở Cài đặt lõi và API, nên hệ thống chưa biết Trang nào là của Sonneto.", "loi": 1},',
  '  "ig": {"ok": 0, "chu": "Chưa nối được vì token Facebook lỗi.", "loi": 1}, "th": {"ok": 0, "chu": "Chưa nối. Bài lên Threads phải đăng tay."}, "zl": {"ok": 0, "chu": "Sonneto chưa có Zalo OA."}}',
  'sys.stdout.write(json.dumps({"bai": bai, "xong": xong, "cd": cd, "bt": bt, "lich": lich, "kn": kn, "so": so, "gg": gg, "uu": uu}, ensure_ascii=False, default=str))'
].join('\n');
var DL = JSON.parse(cp.execFileSync('python3', ['-c', py, GOC], { encoding: 'utf8' }));

var STUB = [
  'var S = { stack: [], chuaLuu: "", chuaLuuNac: null };',
  'function frame(t, html, opt) { document.getElementById("tieuDe").textContent = t; var b = document.getElementById("vgbBody");',
  '  b.innerHTML = html; document.getElementById("chan").innerHTML = (opt && opt.footer) || ""; b.onclick = null; return b; }',
  'function api(d, ts) {',
  '  if (d === "vagabond.bai_dang.chu_de_ds") return Promise.resolve(JSON.parse(JSON.stringify(DL.cd)));',
  '  if (d === "vagabond.bai_dang.cai_dat") return Promise.resolve({ gio_vang: ["07:30", "11:30", "19:30"], sua: true, quan_tri: true, ket_noi: DL.kn, ket_noi_so: DL.so, kenh_so: ["fb", "ig", "th"] });',
  '  return new Promise(function () {}); }',
  'function go(f) { S.stack.push(f); return f(); } function back() {} function toast() {} function busy() {} function errMsg(e) { return String(e); }',
  'function hasRole() { return true; } function vgbBoChuaLuu() {} function confirmSheet() { return Promise.resolve(false); } function scrCaiDatLoi() {}'
].join('\n');

(async function () {
  var b;
  try { b = await pw.chromium.launch(); } catch (e) { console.log('THIẾU Chromium: ' + e.message); process.exit(2); }
  var pg = await b.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  await pg.route('http://app.test/**', function (r) {
    var u = new URL(r.request().url());
    if (u.pathname.indexOf('/assets/vagabond/') === 0) {
      var t = path.join(PUB, u.pathname.slice('/assets/vagabond/'.length));
      if (fs.existsSync(t)) return r.fulfill({ body: fs.readFileSync(t), contentType: /\.svg$/.test(t) ? 'image/svg+xml' : /\.png$/.test(t) ? 'image/png' : 'image/jpeg' });
      return r.fulfill({ status: 404, body: '' });
    }
    return r.fulfill({ contentType: 'text/html; charset=utf-8', body: '<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
      /* Trang /bep thật nạp CSS nền của Frappe (bootstrap) đặt box-sizing border-box cho mọi phần tử,
         kể cả sheet gắn vào body ngoài #vgb; trang đo phải có đúng nền đó. */
      '<style>*,*::before,*::after{box-sizing:border-box}' + cssNen() + '</style></head><body><div id="vgb"><div style="background:#4dd8ef;padding:18px 16px;font-size:20px;font-weight:700;text-align:center" id="tieuDe"></div>' +
      '<div id="vgbBody" style="padding:12px"></div><div id="chan" style="padding:0 12px 20px"></div></div></body></html>' });
  });
  await pg.goto('http://app.test/');
  await pg.addScriptTag({ content: 'var DL = ' + JSON.stringify(DL) + ';\n' + HAM + '\n' + STUB + '\n' + doc('75-bai-dang.js') });
  var hong = [];
  async function doMan(ten, vung) {
    var so = await pg.evaluate(function (vung) {
      var ra = { cuonNgang: document.documentElement.scrollWidth - window.innerWidth, chuNho: [], tran: [], thap: [] };
      var goc = document.querySelector(vung) || document.body;
      goc.querySelectorAll('input, textarea, button, a, .card, [data-bdbai]').forEach(function (e) {
        var r = e.getBoundingClientRect();
        if (!r.width) return;
        var cuon = false;
        for (var a = e.parentElement; a; a = a.parentElement) { var ox = getComputedStyle(a).overflowX; if (ox === 'auto' || ox === 'scroll') { cuon = true; break; } }
        if (!cuon && r.right > window.innerWidth + 0.5) ra.tran.push((e.getAttribute('data-bdcdhieu') || e.className || e.tagName) + ' ' + Math.round(r.right) + 'px');
        if ((e.tagName === 'BUTTON' || e.tagName === 'A' || e.tagName === 'INPUT') && !e.closest('[aria-hidden]') && r.height < 44 - 0.5 && getComputedStyle(e).display !== 'none')
          ra.thap.push((e.textContent || e.getAttribute('placeholder') || e.tagName).trim().slice(0, 30) + ' ' + Math.round(r.height) + 'px');
      });
      goc.querySelectorAll('*').forEach(function (e) {
        if (![].some.call(e.childNodes, function (n) { return n.nodeType === 3 && n.textContent.trim(); })) return;
        var c = parseFloat(getComputedStyle(e).fontSize);
        if (c < 13 && e.getBoundingClientRect().width) ra.chuNho.push(e.textContent.trim().slice(0, 30) + ' ' + c + 'px');
      });
      return ra;
    }, vung);
    console.log(ten + ': cuộn ngang ' + so.cuonNgang + 'px, chữ dưới 13px ' + so.chuNho.length + ', ô lòi mép ' + so.tran.length + ', nút thấp hơn 44px ' + so.thap.length);
    so.chuNho.concat(so.tran, so.thap).forEach(function (x) { console.log('   ' + x); });
    if (so.cuonNgang > 0 || so.chuNho.length || so.tran.length || so.thap.length) hong.push(ten);
  }
  var dong = function () { return pg.evaluate(function () { document.querySelectorAll('.sh').forEach(function (e) { e.remove(); }); }); };

  await pg.evaluate(function () { BD.xemK = 'th'; return scrBaiDangSoan(DL.bai.name, { bai: DL.bai, duyet: true, gio_vang: ['07:30', '11:30', '19:30'], la_gd: false }); });
  await pg.waitForTimeout(400);
  await doMan('1. Màn soạn bài Sonneto', '#vgb');
  await pg.screenshot({ path: path.join(RA, 'bd672-1-soan-sonneto.png'), fullPage: true });
  await pg.evaluate(function () { var t = document.querySelector('[data-bdthe="th"]'), c = document.querySelector('[data-bdcuon]'); if (t && c) { c.style.scrollSnapType = 'none'; c.scrollLeft = t.offsetLeft - 12; t.scrollIntoView({ block: 'start' }); } });
  await pg.waitForTimeout(200);
  /* Thẻ xem trước Threads nằm trong dải cuộn ngang nên chụp phần tử không ra; đọc chữ đếm. */
  var dem = await pg.evaluate(function () { var e = document.querySelector('[data-bddem="th"]'); return e ? e.textContent + ' | màu ' + getComputedStyle(e).color : ''; });
  console.log('   Đếm chữ Threads: ' + dem);
  if (!/tách thành chuỗi bài nối tiếp/.test(dem) || /quá dài/.test(dem)) hong.push('đếm chữ Threads');
  var kiem = await pg.$('[data-bdkiem]');
  if (kiem) await kiem.screenshot({ path: path.join(RA, 'bd672-1c-bang-kiem.png') });

  await pg.evaluate(function () { return bdSheetChuDe('CD-7500', function () {}); });
  await pg.waitForTimeout(300);
  await doMan('2. Sheet Sửa chủ đề', '.sh');
  await pg.screenshot({ path: path.join(RA, 'bd672-2-sheet-chu-de.png') });
  await pg.evaluate(function () { var e = document.getElementById('bdCdHieu'); if (e) e.scrollIntoView({ block: 'center' }); });
  await pg.screenshot({ path: path.join(RA, 'bd672-2b-sheet-chu-de-thuong-hieu.png') });
  await dong();

  await pg.evaluate(function () { return bdSheetCaiDat(); });
  await pg.waitForTimeout(300);
  await doMan('3. Sheet Kết nối kênh', '.sh');
  await pg.screenshot({ path: path.join(RA, 'bd672-3-ket-noi.png') });
  await dong();

  await pg.evaluate(function () {
    document.getElementById('vgbBody').innerHTML = '<div style="font-size:13px;font-weight:800;color:#667085;margin:4px 2px 8px">KHO BẢN THẢO</div>' +
      DL.bt.map(bdTheBanThao).join('') + '<div style="font-size:13px;font-weight:800;color:#667085;margin:14px 2px 8px">LỊCH TUẦN</div>' + DL.lich.map(bdTheLich).join('');
  });
  await pg.waitForTimeout(300);
  await doMan('4. Thẻ Kho bản thảo và lịch', '#vgbBody');
  await pg.screenshot({ path: path.join(RA, 'bd672-4-the-sonneto.png') });

  await pg.evaluate(function () { return scrBaiDangSoan(DL.xong.name, { bai: DL.xong, duyet: true, gio_vang: [], la_gd: false }); });
  await pg.waitForTimeout(400);
  await doMan('5. Bài đã đăng, Threads mới lên một phần', '#vgb');
  await pg.screenshot({ path: path.join(RA, 'bd672-5-threads-mot-phan.png'), fullPage: true });
  var viec = await pg.evaluateHandle(function () { return [].filter.call(document.querySelectorAll('.card'), function (c) { return /ĐÃ LÊN ĐỦ KÊNH/.test(c.textContent); })[0]; });
  if (viec.asElement()) await viec.asElement().screenshot({ path: path.join(RA, 'bd672-5b-ghi-chu-vang.png') });

  await pg.evaluate(function () { BD.xemK = 'gg'; return scrBaiDangSoan(DL.gg.name, { bai: DL.gg, duyet: true, gio_vang: [], la_gd: false }); });
  await pg.waitForTimeout(400);
  await doMan('6. Bài bật Google Posts', '#vgb');
  await pg.screenshot({ path: path.join(RA, 'bd672-6-google.png'), fullPage: true });
  var kgg = await pg.$('[data-bdkiem]');
  if (kgg) await kgg.screenshot({ path: path.join(RA, 'bd672-6b-bang-kiem-google.png') });
  var kiemGg = await pg.evaluate(function () { var e = document.querySelector('[data-bdkiem]'); return e ? e.textContent : ''; });
  if (!/số điện thoại/.test(kiemGg) || !/ảnh đầu tiên/.test(kiemGg)) hong.push('bảng Kiểm Google');
  var theGg = await pg.evaluate(function () {
    var t = document.querySelector('[data-bdthe="gg"]'); if (!t) return null;
    var c = document.querySelector('[data-bdcuon]'); if (c) { c.style.scrollSnapType = 'none'; c.scrollLeft = t.offsetLeft - 12; }
    return { nut: /Đặt hàng/.test(t.textContent), dem: (t.querySelector('[data-bddem]') || {}).textContent };
  });
  console.log('   Thẻ Google: ' + JSON.stringify(theGg));
  if (!theGg || !theGg.nut || !/1\.500/.test(theGg.dem || '')) hong.push('thẻ xem trước Google');
  var tg = await pg.$('[data-bdthe="gg"]');
  if (tg) await tg.screenshot({ path: path.join(RA, 'bd672-6c-the-google.png') });
  await pg.evaluate(function () { BD.xemK = 'gg'; return scrBaiDangSoan(DL.uu.name, { bai: DL.uu, duyet: true, gio_vang: [], la_gd: false }); });
  await pg.waitForTimeout(400);
  await doMan('7. Google Posts loại Ưu đãi', '#vgb');
  var tu = await pg.evaluate(function () {
    var t = document.querySelector('[data-bdthe="gg"]'); if (!t) return null;
    var c = document.querySelector('[data-bdcuon]'); if (c) { c.style.scrollSnapType = 'none'; c.scrollLeft = t.offsetLeft - 12; }
    return { chon: (t.querySelector('[data-bdggloai="uu_dai"]') || {}).style.background, o: t.querySelectorAll('[data-bdgg]').length, nut: /Đặt hàng/.test(t.textContent) };
  });
  console.log('   Thẻ Ưu đãi: ' + JSON.stringify(tu));
  if (!tu || tu.o !== 5 || tu.nut) hong.push('thẻ Ưu đãi Google Posts');
  /* Thẻ nằm trong dải cuộn ngang: tách riêng ra khung đầy bề ngang mới chụp trọn được. */
  await pg.evaluate(function () { var t = document.querySelector('[data-bdthe="gg"]'), v = document.getElementById('vgbBody');
    if (t && v) { var c = t.cloneNode(true); c.style.flex = 'none'; c.style.width = '100%'; c.id = 'bdGgChup'; v.innerHTML = ''; v.appendChild(c); } });
  var tg2 = await pg.$('#bdGgChup');
  if (tg2) await tg2.screenshot({ path: path.join(RA, 'bd672-7-uu-dai.png') });
  await b.close();
  console.log(hong.length ? 'HỎNG: ' + hong.join(', ') : 'ĐẠT HẾT');
  process.exit(hong.length ? 1 : 0);
})();

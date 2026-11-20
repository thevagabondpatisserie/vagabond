/* Máy chụp và đo chung cho app /bep (UI Nghệ sĩ công nghệ, bản 4 mục 7).
 *
 * Chạy ĐÚNG tệp ghép vagabond/public/js/app_bep.js trong Chromium hoặc WebKit, với
 * máy chủ GIẢ: mọi lời gọi /api/ được trả từ cong_cu/ui_b/du_lieu_thu.cjs. Không
 * chạm site thật, không cần mạng. Đoạn <head> lấy từ chính hàm máy chủ
 * vagabond.giao_dien.dau_trang_html nên bật hay tắt đi đúng đường thật.
 *
 * Bằng chứng loại "tệp trong repo, API giả lập". Không thay kiểm trên site thật và
 * máy thật (bàn phím ảo, safe area).
 *
 *   node cong_cu/ui_b/chup.cjs --ra /tmp/anh                 chụp và đo, cả hai chế độ
 *   node cong_cu/ui_b/chup.cjs --ra /tmp/anh --che-do bat --khung 390x844 --man trang-chu
 *   node cong_cu/ui_b/chup.cjs --ra /tmp/anh --may webkit
 *
 * Mã trả 0: mọi phép đo đạt; 1: có phép đo trượt; 2: thiếu Playwright hoặc trình duyệt.
 */
'use strict';
var fs = require('fs');
var path = require('path');
var cp = require('child_process');
var GOC = path.resolve(__dirname, '..', '..');
var CONG = path.join(GOC, 'vagabond', 'public');
var DL = require('./du_lieu_thu.cjs');
var MAN = require('./kich_ban.cjs');

function thamSo(ten, macDinh) {
  var i = process.argv.indexOf('--' + ten);
  return i > 0 && process.argv[i + 1] ? process.argv[i + 1] : macDinh;
}
var RA = thamSo('ra', '/tmp/ui-b-anh');
var CHE_DO = thamSo('che-do', 'ca-hai') === 'ca-hai' ? ['tat', 'bat'] : [thamSo('che-do')];
var KHUNG = thamSo('khung', '360x780,390x844,1366x768').split(',').map(function (k) { var a = k.split('x'); return { w: +a[0], h: +a[1], ten: k }; });
var CHON = thamSo('man', '');
var MAY = thamSo('may', 'chromium');
var VAI = thamSo('vai', 'quan-tri');
/* KHÔNG có tuỳ chọn phóng cỡ chữ (Codex #599): app khai chữ bằng px nên đổi cỡ chữ gốc của trang
   không làm chữ to lên, ảnh chụp sẽ đạt giả. Máy tính quầy phóng 200% chụp bằng khung 683x384
   (đúng bằng 1366x768 phóng đôi). Cỡ chữ 150% và 200% trên điện thoại là cài đặt của máy, phải
   chụp trên máy thật: ghi Chưa kiểm. */
if (process.argv.indexOf('--co-chu') > 0) {
  console.log('KHÔNG HỖ TRỢ --co-chu: máy chụp không giả lập được cỡ chữ của điện thoại. Dùng khung 683x384 cho máy tính quầy phóng 200%.');
  process.exit(1);
}
/* --app <tệp>: chạy một bản app_bep.js khác (ví dụ bản của main) để so chế độ tắt. */
var APP = thamSo('app', '');
var ORIGIN = 'http://vgb.thu';

function dauTrang(bat) {
  var ma = 'import sys; sys.path.insert(0, %r); from vagabond.giao_dien import dau_trang_html, doc_appver; sys.stdout.write(dau_trang_html(%d, doc_appver()))';
  var r = cp.spawnSync('python3', ['-B', '-c', ma.replace('%r', JSON.stringify(GOC)).replace('%d', bat ? 1 : 0)], { encoding: 'utf8' });
  if (r.status !== 0) throw new Error('Không lấy được đoạn head từ vagabond.giao_dien: ' + r.stderr);
  return r.stdout;
}

function trangHtml(bat) {
  return '<!doctype html><html lang="vi"><head><meta charset="utf-8">' +
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">' +
    '<title>Màn hình nghiệp vụ</title>' + dauTrang(bat) +
    '<script>window.frappe={csrf_token:"thu",session:{user:' + JSON.stringify(DL.tra('/api/method/frappe.auth.get_logged_user', {}, VAI).message) + '},boot:{}};</script></head><body><div id="vgb"></div>' +
    '<script src="/assets/vagabond/js/app_bep.js"></script></body></html>';
}

var LOAI = { '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.woff2': 'font/woff2', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.json': 'application/json' };
var ANH_TRONG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');

async function moTrang(trinh, khung, bat, thieu) {
  var ctx = await trinh.newContext({ viewport: { width: khung.w, height: khung.h }, deviceScaleFactor: 2, locale: 'vi-VN', timezoneId: 'Asia/Ho_Chi_Minh',
    isMobile: MAY !== 'firefox' && khung.w < 700, hasTouch: khung.w < 700, reducedMotion: 'reduce' });
  var trang = await ctx.newPage();
  var loi = [];
  trang.on('pageerror', function (e) { loi.push(String(e.message || e)); });
  await ctx.route('**/*', function (route) {
    var u = new URL(route.request().url());
    if (u.origin !== ORIGIN) return route.abort();
    var p = decodeURIComponent(u.pathname);
    if (p.indexOf('/api/') === 0) {
      var than = {};
      try { than = JSON.parse(route.request().postData() || '{}'); } catch (e) {
        try { new URLSearchParams(route.request().postData() || '').forEach(function (v, k) { than[k] = v; }); } catch (e2) { }
      }
      u.searchParams.forEach(function (v, k) { if (!(k in than)) than[k] = v; });
      var kq = DL.tra(p, than, VAI);
      if (kq === undefined) { thieu[p] = (thieu[p] || 0) + 1; kq = { message: null }; }
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(kq) });
    }
    if (p.indexOf('/assets/vagabond/') === 0) {
      var tep = path.join(CONG, p.slice('/assets/vagabond/'.length));
      if (APP && p === '/assets/vagabond/js/app_bep.js') tep = APP;
      if (fs.existsSync(tep)) return route.fulfill({ status: 200, contentType: LOAI[path.extname(tep)] || 'application/octet-stream', body: fs.readFileSync(tep) });
      return route.fulfill({ status: 404, body: '' });
    }
    if (/\.(png|jpe?g|webp|gif|ico)$/i.test(p) || p.indexOf('/files/') === 0) return route.fulfill({ status: 200, contentType: 'image/png', body: ANH_TRONG });
    if (p === '/sw.js') return route.fulfill({ status: 404, body: '' });
    return route.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: trangHtml(bat) });
  });
  await trang.addInitScript(function () {
    /* Giờ cố định để ảnh hai lần chạy giống nhau. */
    var moc = new Date('2026-11-20T09:30:00+07:00').getTime(), That = Date;
    function Gia(a, b, c, d, e, f, g) { return arguments.length ? (arguments.length === 1 ? new That(a) : new That(a, b, c || 1, d || 0, e || 0, f || 0, g || 0)) : new That(moc); }
    Gia.prototype = That.prototype; Gia.now = function () { return moc; }; Gia.parse = That.parse; Gia.UTC = That.UTC;
    window.Date = Gia;
    try { Object.defineProperty(navigator, 'serviceWorker', { get: function () { return undefined; } }); } catch (e) { }
  });
  return { ctx: ctx, trang: trang, loi: loi };
}

/* Phép đo trên màn. Chạy trong trang. */
function doTrongTrang(thamSo) {
  var bat = thamSo.bat, chiDau = thamSo.chiDau;
  var r = { tran: false, nhoNut: [], nhoChu: [], che: [], phong: {}, emoji: [], tuongPhan: [], xemAnh: 0 };
  var de = document.scrollingElement || document.documentElement;
  r.tran = de.scrollWidth > window.innerWidth + 1;
  var vgb = document.getElementById('vgb');
  if (!vgb) return r;
  function hien(n) {
    var rc = n.getBoundingClientRect(), cs = getComputedStyle(n);
    return rc.width > 0 && rc.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && +cs.opacity > 0.01;
  }
  function nhan(n) { return ((n.getAttribute('aria-label') || n.textContent || n.id || n.className || '') + '').replace(/\s+/g, ' ').trim().slice(0, 32) || n.tagName; }
  var bam = Array.prototype.slice.call(document.querySelectorAll('#vgb button, #vgb [data-go], #vgb [data-nhom], #vgb .chip, #vgb a[href], #vgb input, #vgb textarea, #vgb select, #vgb [role=button], .sh button, .sh .chip, .sh input'));
  /* Có bảng trượt hay hộp thoại đang mở thì chỉ đo trong lớp trên cùng: phần bên dưới bị lớp mờ che là có chủ ý. */
  var lopTren = document.querySelectorAll('.sh');
  lopTren = lopTren.length ? lopTren[lopTren.length - 1] : null;
  bam.forEach(function (n) {
    if (!hien(n) || n.type === 'file' || n.type === 'hidden') return;
    if (lopTren && !lopTren.contains(n)) return;
    /* Màn chưa chuyển: chỉ chấm phần khung đã chuyển, tức đầu trang. */
    if (chiDau && !n.closest('.vh')) return;
    var rc = n.getBoundingClientRect();
    if (rc.height < 43.5 || rc.width < 43.5) r.nhoNut.push(nhan(n) + ' ' + Math.round(rc.width) + 'x' + Math.round(rc.height));
    if (rc.top >= 0 && rc.bottom <= window.innerHeight && rc.left >= 0 && rc.right <= window.innerWidth) {
      var e = document.elementFromPoint(rc.left + rc.width / 2, rc.top + rc.height / 2);
      if (e && e !== n && !n.contains(e) && !e.contains(n)) r.che.push(nhan(n) + ' bị ' + nhan(e) + ' che');
    }
  });
  function mau(s) {
    var m = /rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?\)/.exec(s);
    return m ? [+m[1], +m[2], +m[3], m[4] === undefined ? 1 : +m[4]] : null;
  }
  function tron(tren, duoi) { var a = tren[3]; return [tren[0] * a + duoi[0] * (1 - a), tren[1] * a + duoi[1] * (1 - a), tren[2] * a + duoi[2] * (1 - a), 1]; }
  function sang(c) { function k(v) { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); } return 0.2126 * k(c[0]) + 0.7152 * k(c[1]) + 0.0722 * k(c[2]); }
  function nenCua(n) {
    /* Trộn các lớp nền từ phần tử lên tới gốc. Gặp ảnh nền hay gradient thì báo cần xem ảnh. */
    var lop = [], coAnh = false;
    for (var p = n; p && p.nodeType === 1; p = p.parentElement) {
      var cs = getComputedStyle(p);
      if (cs.backgroundImage && cs.backgroundImage !== 'none') coAnh = true;
      var c = mau(cs.backgroundColor);
      if (c && c[3] > 0) { lop.push(c); if (c[3] >= 0.999) break; }
    }
    var nen = [243, 239, 231, 1];
    if (!bat) nen = [238, 240, 245, 1];
    for (var i = lop.length - 1; i >= 0; i--) nen = tron(lop[i], nen);
    return { mau: nen, coAnh: coAnh };
  }
  var tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT), nut;
  var daXet = new Set();
  while ((nut = tw.nextNode())) {
    var chu = nut.nodeValue.replace(/\s+/g, ' ').trim();
    var cha = nut.parentElement;
    if (!chu || !cha || daXet.has(cha) || !hien(cha)) continue;
    if (cha.closest('script,style')) continue;
    if (chiDau && !cha.closest('.vh')) continue;
    daXet.add(cha);
    var cs = getComputedStyle(cha), co = parseFloat(cs.fontSize);
    if (co < 12.95) r.nhoChu.push(chu.slice(0, 28) + ' ' + co);
    var ho = cs.fontFamily.split(',')[0].replace(/["']/g, '').trim();
    r.phong[ho] = (r.phong[ho] || 0) + 1;
    if (/[\u{1F000}-\u{1FAFF}☀-➿]/u.test(chu) && cha.closest('button, .vh, .sec, .chip, .h1, .gn')) r.emoji.push(chu.slice(0, 28));
    if (bat) {
      var fg = mau(cs.color), nn = nenCua(cha);
      if (fg) {
        var f2 = tron(fg, nn.mau), l1 = sang(f2), l2 = sang(nn.mau), tp = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
        var dam = parseInt(cs.fontWeight, 10) >= 700;
        var can = (co >= 24 || (dam && co >= 18.66)) ? 3 : 4.5;
        if (nn.coAnh) r.xemAnh++;
        if (tp < can - 0.005) r.tuongPhan.push(chu.slice(0, 24) + ' ' + tp.toFixed(2) + (nn.coAnh ? ' (trên gradient, xem ảnh)' : ''));
      }
    }
  }
  return r;
}

/* Kiểm tham số TRƯỚC khi cần tới trình duyệt: gõ sai tên màn hay khung thì trượt ngay, không
   được chạy 0 ô rồi báo xong (Codex #599: cổng kiểm không được xanh khi chưa kiểm gì). */
function chonMan() {
  var ten = CHON ? CHON.split(',') : [];
  var la = ten.filter(function (t) { return !MAN.some(function (m) { return m.ten === t; }); });
  if (la.length) { console.log('KHÔNG CÓ màn: ' + la.join(', ') + '. Màn có sẵn: ' + MAN.map(function (m) { return m.ten; }).join(', ')); process.exit(1); }
  if (KHUNG.some(function (k) { return !(k.w > 0 && k.h > 0); })) { console.log('Khung không hợp lệ, viết dạng 390x844.'); process.exit(1); }
  var ds = MAN.filter(function (m) { return !ten.length || ten.indexOf(m.ten) >= 0; });
  if (!ds.length) { console.log('KHÔNG CÓ màn nào để chụp.'); process.exit(1); }
  return ds;
}

async function chay() {
  var ds = chonMan();
  var pw;
  try { pw = require('playwright'); } catch (e) {
    try { pw = require('/opt/npm-tools/node_modules/playwright'); } catch (e2) { console.log('THIẾU Playwright, chưa chụp được'); process.exit(2); }
  }
  var trinh;
  try { trinh = await pw[MAY].launch(); } catch (e) { console.log('THIẾU trình duyệt ' + MAY + ': ' + String(e.message).split('\n')[0]); process.exit(2); }
  fs.mkdirSync(RA, { recursive: true });
  var bang = [], thieu = {}, truot = 0;
  for (var c = 0; c < CHE_DO.length; c++) for (var k = 0; k < KHUNG.length; k++) for (var i = 0; i < ds.length; i++) {
    var m = ds[i], bat = CHE_DO[c] === 'bat', khung = KHUNG[k];
    if (m.chi && m.chi.indexOf(khung.ten) < 0) continue;
    var o = await moTrang(trinh, khung, bat, thieu);
    var thieuTruoc = JSON.stringify(thieu);
    var dong = { man: m.ten, che_do: CHE_DO[c], khung: khung.ten, may: MAY, vai: m.vai || VAI, loi: [] };
    try {
      DL.dat(m.du_lieu || {});
      await o.trang.goto(ORIGIN + '/bep');
      await o.trang.waitForSelector(m.cho || '#vgb .vh, #vgb .lgw', { timeout: 15000 });
      if (m.mo) await m.mo(o.trang);
      await o.trang.evaluate(function () { return document.fonts && document.fonts.ready; });
      await o.trang.waitForTimeout(250);
      var coUi = await o.trang.evaluate(function () { return document.documentElement.classList.contains('ui-b'); });
      if (coUi !== bat) dong.loi.push('class ui-b ' + (coUi ? 'CÓ' : 'KHÔNG CÓ') + ' trong khi chế độ là ' + CHE_DO[c]);
      var ten = [m.ten, CHE_DO[c], khung.ten, MAY].join('__') + '.png';
      await o.trang.screenshot({ path: path.join(RA, ten), fullPage: false });
      dong.anh = ten;
      var d = await o.trang.evaluate(doTrongTrang, { bat: bat, chiDau: bat && !!m.chua_chuyen });
      dong.do = d;
      if (d.tran) dong.loi.push('cuộn ngang cả trang');
      if (o.loi.length) dong.loi.push('lỗi JS: ' + o.loi.slice(0, 2).join(' | '));
      if (bat) {
        /* Chỉ phần ĐÃ CHUYỂN phải đạt chuẩn mới (bản 4 mục 7). Màn chưa chuyển thì phép đo ở trên đã
           chỉ lấy phần đầu trang (khung chung đã chuyển). */
        if (d.nhoNut.length) dong.loi.push('vùng bấm dưới 44: ' + d.nhoNut.slice(0, 4).join('; ') + (d.nhoNut.length > 4 ? ' (+' + (d.nhoNut.length - 4) + ')' : ''));
        if (d.nhoChu.length) dong.loi.push('chữ dưới 13: ' + d.nhoChu.slice(0, 4).join('; ') + (d.nhoChu.length > 4 ? ' (+' + (d.nhoChu.length - 4) + ')' : ''));
        if (d.che.length) dong.loi.push('bị che: ' + d.che.slice(0, 3).join('; '));
        if (d.emoji.length) dong.loi.push('còn emoji: ' + d.emoji.slice(0, 4).join('; '));
        var la = Object.keys(d.phong).filter(function (p) { return p !== 'Be Vietnam Pro' && p !== 'Doto'; });
        if (la.length) dong.loi.push('phông lạ: ' + la.join(', '));
        if (d.tuongPhan.length) dong.loi.push('tương phản thấp: ' + d.tuongPhan.slice(0, 4).join('; ') + (d.tuongPhan.length > 4 ? ' (+' + (d.tuongPhan.length - 4) + ')' : ''));
      }
    } catch (e) {
      dong.loi.push('không mở được: ' + String(e.message || e).split('\n')[0]);
      if (o.loi.length) dong.loi.push('lỗi JS: ' + o.loi.slice(0, 3).join(' | '));
      try { dong.loi.push('màn đang hiện: ' + (await o.trang.evaluate(function () { return (document.body.innerText || '').slice(0, 160); }))); } catch (e2) { }
    }
    /* Lời gọi máy chủ mà dữ liệu thử chưa có (đã trả rỗng) trong đúng ô này: ghi lại để người đọc biết màn chụp trong điều kiện nào. */
    var truoc = JSON.parse(thieuTruoc);
    dong.api_thieu = Object.keys(thieu).filter(function (k) { return thieu[k] !== (truoc[k] || 0); }).map(function (k) { return k.replace('/api/method/', ''); });
    dong.ket_qua = dong.loi.length ? 'Trượt' : (bat && m.chua_chuyen ? 'Chưa chuyển' : 'Đạt');
    if (dong.ket_qua === 'Trượt') truot++;
    bang.push(dong);
    console.log([dong.ket_qua.toUpperCase(), m.ten, CHE_DO[c], khung.ten].join('  ') + (dong.loi.length ? '\n      ' + dong.loi.join('\n      ') : ''));
    await o.ctx.close();
  }
  await trinh.close();
  var tt = Object.keys(thieu);
  if (tt.length) console.log('API giả chưa có dữ liệu (đã trả rỗng): ' + tt.map(function (t) { return t.replace('/api/method/', '') + ' x' + thieu[t]; }).join(', '));
  if (!bang.length) { console.log('KHÔNG có ô nào được chụp.'); process.exit(1); }
  fs.writeFileSync(path.join(RA, 'ket-qua.json'), JSON.stringify({ may: MAY, bang: bang, api_thieu: thieu }, null, 1));
  console.log(bang.length + ' ô: ' + bang.filter(function (b) { return b.ket_qua === 'Đạt'; }).length + ' Đạt, ' + truot + ' Trượt, ' +
    bang.filter(function (b) { return b.ket_qua === 'Chưa chuyển'; }).length + ' Chưa chuyển.');
  process.exit(truot ? 1 : 0);
}
chay().catch(function (e) { console.error(e); process.exit(1); });

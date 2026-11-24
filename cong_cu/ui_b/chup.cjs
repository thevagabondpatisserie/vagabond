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
var DO = require('./do.cjs');
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
/* --chan <chuỗi>: chặn mọi tài nguyên có đường dẫn chứa chuỗi này (trả 404). Chỉ để chứng minh
   phép đo biết đỏ, ví dụ --chan /fonts/ui/ thì các ô giao diện mới PHẢI trượt vì phông không tải. */
var CHAN = thamSo('chan', '');
/* --nap sau-load (mặc định) | thang. Trang /bep thật chèn app_bep.js bằng thẻ script động
   (vagabond/trang/bep.js), lúc đó trang đã nạp xong và __boot chạy ngay giữa tệp. Mặc định đi
   đúng đường đó (Codex #600). "thang" là thẻ script viết thẳng trong HTML, chỉ để so. */
var NAP = thamSo('nap', 'sau-load');
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
    (NAP === 'thang' ? '<script src="/assets/vagabond/js/app_bep.js"></script>' :
      '<script>window.addEventListener("load",function(){var s=document.createElement("script");' +
      's.src="/assets/vagabond/js/app_bep.js";document.body.appendChild(s);});</script>') + '</body></html>';
}

var LOAI = { '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.woff2': 'font/woff2', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.json': 'application/json' };
var ANH_TRONG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');

async function moTrang(trinh, khung, bat, thieu, taiHong) {
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
      if (CHAN && p.indexOf(CHAN) >= 0) { taiHong.push({ duong: p, ma: 404 }); return route.fulfill({ status: 404, body: '' }); }
      if (!fs.existsSync(tep)) taiHong.push({ duong: p, ma: 404 });
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
  var r = { tran: false, nhoNut: [], nhoChu: [], che: [], phong: {}, phongDung: [], phongMat: [], emoji: [], tuongPhan: [], xemAnh: 0,
    chongSo: [], cat: [], xuongDong: [], tenDong: [], mauVo: '' };
  var meta = document.querySelector('meta[name="theme-color"]');
  r.mauVo = meta ? String(meta.content || '').toUpperCase() : '';
  var daGhiPhong = {};
  var de = document.scrollingElement || document.documentElement;
  r.tran = de.scrollWidth > window.innerWidth + 1;
  var vgb = document.getElementById('vgb');
  if (!vgb) return r;
  function hien(n) {
    var rc = n.getBoundingClientRect(), cs = getComputedStyle(n);
    return rc.width > 0 && rc.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && +cs.opacity > 0.01;
  }
  function nhan(n) { return ((n.getAttribute('aria-label') || n.textContent || n.id || n.className || '') + '').replace(/\s+/g, ' ').trim().slice(0, 32) || n.tagName; }
  var bam = Array.prototype.slice.call(document.querySelectorAll('#vgb button, #vgb [data-go], #vgb [data-nhom], #vgb .chip, #vgb a[href], #vgb input, #vgb textarea, #vgb select, #vgb [role=button], ' +
    '#vgb .hub, #vgb .gt, #vgb .vgbgo, #vgb .vgbgs, #vgb .vgbgb, #vgb [data-suaghim], #vgb [data-themghim], #vgb .lgfp, .sh button, .sh .chip, .sh input, .sh textarea, .sh .shi, .sh .x'));
  /* Thành phần dựng thử ngoài #vgb (pham_vi) cũng phải đo vùng bấm (Codex 21/11: thử phá bằng nút 38). */
  if (thamSo.phamVi) bam = bam.concat(Array.prototype.slice.call(document.querySelectorAll(
    thamSo.phamVi + ' button, ' + thamSo.phamVi + ' .chip, ' + thamSo.phamVi + ' [role=button], ' + thamSo.phamVi + ' input')));
  bam = bam.filter(function (n, i) { return bam.indexOf(n) === i; });
  /* Có bảng trượt hay hộp thoại đang mở thì chỉ đo trong lớp trên cùng: phần bên dưới bị lớp mờ che là có chủ ý. */
  var lopTren = document.querySelectorAll('.sh');
  lopTren = lopTren.length ? lopTren[lopTren.length - 1] : null;
  /* Trợ lý không phải .sh nhưng cũng là lớp phủ trên cùng khi đang mở. */
  var tl = document.getElementById('tlKhung');
  if (!lopTren && tl && getComputedStyle(tl).display !== 'none') lopTren = tl;
  /* Kịch bản dựng thử một thành phần (pham_vi) thì chỉ đo trong thành phần đó. */
  if (thamSo.phamVi) lopTren = document.querySelector(thamSo.phamVi) || lopTren;
  bam.forEach(function (n) {
    if (!hien(n) || n.type === 'file' || n.type === 'hidden') return;
    if (lopTren && !lopTren.contains(n)) return;
    /* Màn chưa chuyển: chỉ chấm phần khung đã chuyển, tức đầu trang. */
    if (chiDau && !n.closest('.vh')) return;
    /* Ô tích nằm trong nhãn: bấm cả nhãn đều tích, nên vùng bấm là hộp của nhãn. */
    var vung = (n.type === 'checkbox' || n.type === 'radio') && n.closest('label') ? n.closest('label') : n;
    var rc = vung.getBoundingClientRect();
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
    var khoaPhong = ho + '|' + cs.fontWeight;
    if (!daGhiPhong[khoaPhong]) { daGhiPhong[khoaPhong] = 1; r.phongDung.push({ ho: ho, dam: cs.fontWeight }); }
    /* Codex UI04: soi emoji ở MỌI chữ của app và hộp đang mở, không chỉ nút và tiêu đề. */
    /* v691: chữ sẽ gửi đi hoặc người dùng tự viết (ô soạn, [data-giu-emoji], xem trước bài đăng) phải
       giữ nguyên emoji (đặc tả bản 4 mục 1), cùng danh sách UIB_GIU_CHU của 81-ui-b.js. */
    if (/[\u{1F000}-\u{1FAFF}☀-➿]/u.test(chu) && cha.closest('#vgb, .sh, #tlKhung, .vf') &&
      !cha.closest('textarea, [contenteditable], [data-giu-emoji], .bd-phai')) r.emoji.push(chu.slice(0, 28));
    /* Codex UI07: chữ bị cắt TRONG thẻ dù cả trang không cuộn ngang. Tìm lớp cha gần nhất có
       cắt tràn (hidden hoặc clip, không tính lớp cuộn được), không có thì lấy khung màn. */
    if (!lopTren || lopTren.contains(cha)) {
      var rcc = cha.getBoundingClientRect(), ke = { left: 0, right: window.innerWidth }, kn = 'khung màn';
      for (var pa = cha.parentElement; pa && pa !== document.body; pa = pa.parentElement) {
        var ox = getComputedStyle(pa).overflowX;
        if (ox === 'hidden' || ox === 'clip') { ke = pa.getBoundingClientRect(); kn = nhan(pa); break; }
        if (ox === 'auto' || ox === 'scroll') { ke = null; break; }
      }
      if (ke && (rcc.right > ke.right + 0.5 || rcc.left < ke.left - 0.5)) r.cat.push(chu.slice(0, 24) + ' tới x' + rcc.right.toFixed(1) + ' trong ' + kn + ' tới x' + ke.right.toFixed(1));
      if (cs.textOverflow === 'ellipsis' && cha.scrollWidth > cha.clientWidth + 1) r.cat.push(chu.slice(0, 24) + ' bị cắt bằng dấu ba chấm');
    }
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
  /* Codex UI02: số trên ô nhóm không chồng biểu tượng (hay chữ của ô Việc cần làm), không ra khỏi ô. */
  document.querySelectorAll('#vgb .gt .gb').forEach(function (gb) {
    if (!hien(gb) || !gb.textContent.trim()) return;
    var o = gb.closest('.gt'), r1 = gb.getBoundingClientRect(), t1 = o.getBoundingClientRect();
    var vat = o.classList.contains('vcl') ? (o.querySelector('.gn') || {}).parentElement : o.querySelector('.gi');
    var ten = (o.querySelector('.gn') || {}).textContent || '';
    if (r1.left < t1.left || r1.right > t1.right) r.chongSo.push('số ' + gb.textContent + ' ra khỏi ô ' + ten);
    var rgs = document.createRange(); rgs.selectNodeContents(gb);
    var qs = Array.prototype.filter.call(rgs.getClientRects(), function (x) { return x.width > 1; }).sort(function (a, b) { return a.top - b.top; });
    var nd = 0, dy = -1e9;
    qs.forEach(function (x) { var g = (x.top + x.bottom) / 2; if (g > dy) { nd++; dy = x.bottom; } else if (x.bottom > dy) dy = x.bottom; });
    if (nd > 1) r.chongSo.push('số ' + gb.textContent + ' gãy ' + nd + ' dòng ở ô ' + ten);
    if (vat && vat.getBoundingClientRect) {
      var v = vat.getBoundingClientRect();
      if (r1.top < v.bottom && r1.bottom > v.top && r1.left < v.right && r1.right > v.left) {
        r.chongSo.push('số ' + gb.textContent + ' chồng ' + (o.classList.contains('vcl') ? 'chữ' : 'biểu tượng') + ' ô ' + ten + ' ' + (Math.min(r1.right, v.right) - Math.max(r1.left, v.left)).toFixed(1) + 'px');
      }
    }
  });
  /* Codex UI03: nhãn ngắn của nút, chip xuống dòng. Nhãn dài hơn 24 ký tự được xuống dòng. */
  document.querySelectorAll('#vgb .btn, #vgb .chip, .vf .btn, .sh .btn, .sh .chip').forEach(function (b) {
    if (!hien(b) || (lopTren && !lopTren.contains(b)) || (chiDau && !b.closest('.vh'))) return;
    var t = (b.textContent || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 24) return;
    var rg = document.createRange(); rg.selectNodeContents(b);
    /* Đếm dòng theo dải dọc chồng nhau: biểu tượng lệch vài điểm cạnh chữ vẫn là cùng dòng. */
    var qs = Array.prototype.filter.call(rg.getClientRects(), function (x) { return x.width > 1 && x.height > 4; })
      .sort(function (a, b) { return a.top - b.top; });
    var soDong = 0, day = -1e9;
    qs.forEach(function (x) { var g = (x.top + x.bottom) / 2; if (g > day) { soDong++; day = x.bottom; } else if (x.bottom > day) day = x.bottom; });
    /* Nhãn có số tiền lớn (6 chữ số trở lên) được hai dòng (bản 4 mục 4, tiền lớn có bố cục rõ). */
    if (soDong > (/\d[\d.,]{5,}/.test(t) ? 2 : 1)) r.xuongDong.push(t + ' (' + soDong + ' dòng)');
  });
  /* Codex UI05: nút đóng của hộp đang mở có vai trò nút và tên "Đóng". */
  document.querySelectorAll('.sh .x, #tlDong').forEach(function (x) {
    if (!hien(x) || (lopTren && !lopTren.contains(x) && x.id !== 'tlDong')) return;
    var vaiTro = x.tagName === 'BUTTON' || x.getAttribute('role') === 'button';
    var ten = x.getAttribute('aria-label') || '';
    if (!vaiTro || ten !== 'Đóng') r.tenDong.push((x.id || x.className) + ' vai trò ' + (vaiTro ? 'nút' : 'không') + ', tên "' + ten + '"');
  });
  /* Lớp vẽ: số thẻ bảng kiểu, nội dung, các nhóm đang hiện trên màn. */
  var the = document.querySelectorAll('style#vgbUiB');
  r.lopVe = { soThe: the.length, css: the.length ? the[0].textContent : '', nhom: [] };
  document.querySelectorAll('[data-nhom], [data-uinhom]').forEach(function (n) {
    var k = n.getAttribute('data-uinhom') || n.getAttribute('data-nhom');
    if (k && r.lopVe.nhom.indexOf(k) < 0) r.lopVe.nhom.push(k);
  });
  /* Mặt phông của trang và trạng thái tải THẬT (không phải tên khai trong CSS). */
  try {
    document.fonts.forEach(function (f) {
      r.phongMat.push({ ho: String(f.family).replace(/["']/g, ''), dam: String(f.weight), trang_thai: f.status });
    });
  } catch (e) { }
  return r;
}

/* Kiểm tham số TRƯỚC khi cần tới trình duyệt: gõ sai tên màn hay khung thì trượt ngay, không
   được chạy 0 ô rồi báo xong (Codex #599: cổng kiểm không được xanh khi chưa kiểm gì). */
function chonMan() {
  var ten = CHON ? CHON.split(',') : [];
  var la = ten.filter(function (t) { return !MAN.some(function (m) { return m.ten === t; }); });
  if (la.length) { console.log('KHÔNG CÓ màn: ' + la.join(', ') + '. Màn có sẵn: ' + MAN.map(function (m) { return m.ten; }).join(', ')); process.exit(1); }
  if (NAP !== 'sau-load' && NAP !== 'thang') { console.log('--nap chỉ nhận sau-load hoặc thang.'); process.exit(1); }
  /* Chế độ lạ (ví dụ "bat,tat") từng chạy như chế độ tắt và báo Đạt mà không kiểm gì của giao diện mới. */
  if (CHE_DO.some(function (c) { return c !== 'bat' && c !== 'tat'; })) { console.log('--che-do chỉ nhận bat, tat hoặc ca-hai, nhận được: ' + CHE_DO.join(',')); process.exit(1); }
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
    var taiHong = [];
    var o = await moTrang(trinh, khung, bat, thieu, taiHong);
    var thieuTruoc = JSON.stringify(thieu);
    var dong = { man: m.ten, che_do: CHE_DO[c], khung: khung.ten, may: MAY, vai: m.vai || VAI, loi: [] };
    try {
      DL.dat(m.du_lieu || {});
      await o.trang.goto(ORIGIN + '/bep');
      await o.trang.waitForSelector(m.cho || '#vgb .vh, #vgb .lgw', { timeout: 15000 });
      if (m.mo) await m.mo(o.trang);
      if (m.kiem) (await m.kiem(o.trang, bat)).forEach(function (x) { dong.loi.push(x); });
      await o.trang.evaluate(function () { return document.fonts && document.fonts.ready; });
      await o.trang.waitForTimeout(250);
      var coUi = await o.trang.evaluate(function () { return document.documentElement.classList.contains('ui-b'); });
      if (coUi !== bat) dong.loi.push('class ui-b ' + (coUi ? 'CÓ' : 'KHÔNG CÓ') + ' trong khi chế độ là ' + CHE_DO[c]);
      var ten = [m.ten, CHE_DO[c], khung.ten, MAY].join('__') + '.png';
      /* App cuộn trong khung riêng nên fullPage không lấy thêm được gì. Muốn xem phần dưới
         màn đầu thì chụp bằng khung cao, ví dụ --khung 390x2600 (Codex #600). */
      await o.trang.screenshot({ path: path.join(RA, ten), fullPage: false });
      dong.anh = ten;
      var d = await o.trang.evaluate(doTrongTrang, { bat: bat, chiDau: bat && !!m.chua_chuyen, phamVi: m.pham_vi || '' });
      dong.do = d;
      if (d.tran) dong.loi.push('cuộn ngang cả trang');
      /* Codex UI01: màu vỏ app theo giao diện đang hiện. */
      var mauVo = bat ? '#EAF4F3' : '#50DBF2';
      if (d.mauVo !== mauVo) dong.loi.push('màu vỏ app (theme-color) là ' + (d.mauVo || 'không có') + ', phải là ' + mauVo);
      /* Nút đóng dùng chung cho hai giao diện: kiểm ở chế độ bật là đủ, chế độ tắt chỉ so điểm ảnh với main. */
      if (bat && d.tenDong.length) dong.loi.push('nút đóng thiếu tên hoặc vai trò: ' + d.tenDong.slice(0, 3).join('; '));
      if (o.loi.length) dong.loi.push('lỗi JS: ' + o.loi.slice(0, 2).join(' | '));
      DO.danhGiaTaiNguyen(taiHong).forEach(function (x) { dong.loi.push(x); });
      if (bat) {
        /* Chỉ phần ĐÃ CHUYỂN phải đạt chuẩn mới (bản 4 mục 7). Màn chưa chuyển thì phép đo ở trên đã
           chỉ lấy phần đầu trang (khung chung đã chuyển). */
        if (d.nhoNut.length) dong.loi.push('vùng bấm dưới 44: ' + d.nhoNut.slice(0, 4).join('; ') + (d.nhoNut.length > 4 ? ' (+' + (d.nhoNut.length - 4) + ')' : ''));
        if (d.nhoChu.length) dong.loi.push('chữ dưới 13: ' + d.nhoChu.slice(0, 4).join('; ') + (d.nhoChu.length > 4 ? ' (+' + (d.nhoChu.length - 4) + ')' : ''));
        if (d.che.length) dong.loi.push('bị che: ' + d.che.slice(0, 3).join('; '));
        if (d.emoji.length) dong.loi.push('còn emoji: ' + d.emoji.slice(0, 4).join('; ') + (d.emoji.length > 4 ? ' (+' + (d.emoji.length - 4) + ')' : ''));
        if (d.chongSo.length) dong.loi.push('số chồng: ' + d.chongSo.slice(0, 4).join('; '));
        if (d.cat.length) dong.loi.push('chữ bị cắt: ' + d.cat.slice(0, 4).join('; ') + (d.cat.length > 4 ? ' (+' + (d.cat.length - 4) + ')' : ''));
        if (d.xuongDong.length) dong.loi.push('nhãn ngắn xuống dòng: ' + d.xuongDong.slice(0, 4).join('; '));
        DO.danhGiaPhong(d.phongDung, d.phongMat).forEach(function (x) { dong.loi.push(x); });
        DO.danhGiaLopVe(d.lopVe.soThe, d.lopVe.css, d.lopVe.nhom).forEach(function (x) { dong.loi.push(x); });
        dong.xem_anh = d.xemAnh;
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
  var canXem = bang.reduce(function (t, b) { return t + (b.xem_anh || 0); }, 0);
  if (canXem) console.log('Chữ nằm trên gradient hoặc ảnh nền: ' + canXem + ' chỗ. Phép đo tương phản ở các chỗ này chỉ là ước lượng trên màu nền đặc, PHẢI mở ảnh xem (bản 4 mục 7).');
  console.log(bang.length + ' ô: ' + bang.filter(function (b) { return b.ket_qua === 'Đạt'; }).length + ' Đạt, ' + truot + ' Trượt, ' +
    bang.filter(function (b) { return b.ket_qua === 'Chưa chuyển'; }).length + ' Chưa chuyển.');
  process.exit(truot ? 1 : 0);
}
/* Công cụ khác (quet_man.cjs) dùng lại cách mở trang và phép đo, không chạy bộ chụp. */
if (require.main === module) chay().catch(function (e) { console.error(e); process.exit(1); });
module.exports = { moTrang: moTrang, doTrongTrang: doTrongTrang, ORIGIN: ORIGIN };

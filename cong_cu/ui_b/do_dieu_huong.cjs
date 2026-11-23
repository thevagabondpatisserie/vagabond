/* Đo điều hướng của app /bep (PR B, vòng 2 kiểm giao diện 22/11/2026).
 *
 * Chạy ĐÚNG tệp app_bep.js trong Chromium với máy chủ GIẢ (cong_cu/ui_b/du_lieu_thu.cjs),
 * mỗi lời gọi /api/ trả chậm --tre mili giây để giống máy chủ thật. Không chạm site thật.
 *
 * Hai việc:
 *   1. Từ 5 màn (Báo cáo, Đối soát COD, Đơn còn treo, Đặt bàn, Tính tiền), bấm nút Trang chủ:
 *      đo từ lúc bấm tới lúc lưới ô lớn hiện, số lời gọi máy chủ phát ra trong lúc đó, và lúc
 *      lời gọi cuối trả xong. Mở lần hai liền tay đo riêng (số đếm còn mới thì không gọi lại).
 *   2. Màn cũ vẽ đè: mở Vận đơn (danh sách trả chậm --tre-vd), chưa kịp về thì sang Đối soát COD.
 *      Chờ danh sách Vận đơn về rồi đọc tiêu đề màn: phải còn là Đối soát COD.
 *
 *   node cong_cu/ui_b/do_dieu_huong.cjs                       đo bản đang có trong repo
 *   node cong_cu/ui_b/do_dieu_huong.cjs --app /tmp/main.js    đo một bản app_bep.js khác (bản main)
 *   node cong_cu/ui_b/do_dieu_huong.cjs --tre 150 --tre-vd 1500 --che-do bat --json /tmp/kq.json
 *
 * Mã trả 0: hai việc đạt; 1: có việc trượt; 2: thiếu Playwright.
 * Bằng chứng loại "tệp trong repo, API giả lập": con số tuyệt đối khác site thật, dùng để SO
 * trước và sau trên cùng một máy, cùng độ trễ. */
'use strict';
var fs = require('fs');
var path = require('path');
var cp = require('child_process');
var GOC = path.resolve(__dirname, '..', '..');
var CONG = path.join(GOC, 'vagabond', 'public');
var DL = require('./du_lieu_thu.cjs');

function thamSo(ten, macDinh) {
  var i = process.argv.indexOf('--' + ten);
  return i > 0 && process.argv[i + 1] ? process.argv[i + 1] : macDinh;
}
var APP = thamSo('app', '');
var TRE = +thamSo('tre', '150');
var TRE_VD = +thamSo('tre-vd', '1500');
var BAT = thamSo('che-do', 'bat') === 'bat';
var RA_JSON = thamSo('json', '');
var ORIGIN = 'http://vgb.thu';
var MAN = [
  { ten: 'Báo cáo', nhom: 'BC', go: 'BCHUB' },
  { ten: 'Đối soát COD', nhom: 'GH', go: 'DSCOD' },
  { ten: 'Đơn còn treo', nhom: 'BH', go: 'DTREO' },
  { ten: 'Đặt bàn', nhom: 'BH', go: 'DATBAN' },
  { ten: 'Tính tiền', nhom: 'BH', go: 'POS' }
];

var pw;
try { pw = require('playwright'); } catch (e) { console.log('Thiếu Playwright: npm i playwright'); process.exit(2); }

function dauTrang(bat) {
  var ma = 'import sys; sys.path.insert(0, %r); from vagabond.giao_dien import dau_trang_html, doc_appver; sys.stdout.write(dau_trang_html(%d, doc_appver()))';
  var r = cp.spawnSync('python3', ['-B', '-c', ma.replace('%r', JSON.stringify(GOC)).replace('%d', bat ? 1 : 0)], { encoding: 'utf8' });
  if (r.status !== 0) throw new Error('Không lấy được đoạn head: ' + r.stderr);
  return r.stdout;
}
function trangHtml() {
  var user = DL.tra('/api/method/frappe.auth.get_logged_user', {}, 'quan-tri').message;
  return '<!doctype html><html lang="vi"><head><meta charset="utf-8">' +
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">' +
    '<title>Màn hình nghiệp vụ</title>' + dauTrang(BAT) +
    '<script>window.frappe={csrf_token:"thu",session:{user:' + JSON.stringify(user) + '},boot:{}};</script></head>' +
    '<body><div id="vgb"></div><script>window.addEventListener("load",function(){var s=document.createElement("script");' +
    's.src="/assets/vagabond/js/app_bep.js";document.body.appendChild(s);});</script></body></html>';
}
var LOAI = { '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.woff2': 'font/woff2', '.svg': 'image/svg+xml', '.json': 'application/json' };
var ANH = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');

/* Mọi lời gọi /api/ ghi vào nhật ký với mốc gửi và mốc trả, theo đồng hồ của Node. */
var NHAT = [];
var RONG = {
  'vagabond.van_don.danh_sach': function () { return []; },
  'vagabond.van_don.ds_shipper': function () { return []; },
  'vagabond.van_don.doi_soat_cod': function () { return []; }
};
function cho(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

async function moTrang(trinh) {
  var ctx = await trinh.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, locale: 'vi-VN',
    timezoneId: 'Asia/Ho_Chi_Minh', isMobile: true, hasTouch: true, reducedMotion: 'reduce' });
  var trang = await ctx.newPage();
  var loi = [];
  trang.on('pageerror', function (e) { loi.push(String(e.message || e)); });
  await ctx.route('**/*', async function (route) {
    var u = new URL(route.request().url());
    if (u.origin !== ORIGIN) return route.abort();
    var p = decodeURIComponent(u.pathname);
    if (p.indexOf('/api/') === 0) {
      var than = {};
      try { than = JSON.parse(route.request().postData() || '{}'); } catch (e) {
        try { new URLSearchParams(route.request().postData() || '').forEach(function (v, k) { than[k] = v; }); } catch (e2) { }
      }
      u.searchParams.forEach(function (v, k) { if (!(k in than)) than[k] = v; });
      var m = p.replace('/api/method/', '');
      var dong = { m: m, dt: than.doctype || '', gui: Date.now(), tra: 0 };
      NHAT.push(dong);
      var tre = m === 'vagabond.van_don.danh_sach' ? TRE_VD : TRE;
      await cho(tre);
      var kq = DL.tra(p, than, 'quan-tri');
      /* Dữ liệu thử chung chưa có vận đơn: trả danh sách rỗng đúng dạng, để màn Vận đơn đi hết
         đường vẽ thật (trả null thì màn hỏng trước khi vẽ, phép đo vẽ đè thành đạt giả). */
      if (kq === undefined || (kq && kq.message == null && RONG[m])) kq = { message: RONG[m] ? RONG[m]() : null };
      dong.tra = Date.now();
      try { await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(kq) }); } catch (e) { }
      return;
    }
    if (p.indexOf('/assets/vagabond/') === 0) {
      var tep = path.join(CONG, p.slice('/assets/vagabond/'.length));
      if (APP && p === '/assets/vagabond/js/app_bep.js') tep = APP;
      if (fs.existsSync(tep)) return route.fulfill({ status: 200, contentType: LOAI[path.extname(tep)] || 'application/octet-stream', body: fs.readFileSync(tep) });
      return route.fulfill({ status: 404, body: '' });
    }
    if (/\.(png|jpe?g|webp|gif|ico)$/i.test(p) || p.indexOf('/files/') === 0) return route.fulfill({ status: 200, contentType: 'image/png', body: ANH });
    if (p === '/sw.js') return route.fulfill({ status: 404, body: '' });
    return route.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: trangHtml() });
  });
  await trang.addInitScript(function () {
    try { Object.defineProperty(navigator, 'serviceWorker', { get: function () { return undefined; } }); } catch (e) { }
  });
  return { ctx: ctx, trang: trang, loi: loi };
}

/* Chờ trang chủ có lưới ô lớn, trả mốc Date.now() của Node lúc thấy. Hỏi trang mỗi 10 ms. */
async function choLuoi(trang, han) {
  var den = Date.now() + (han || 15000);
  while (Date.now() < den) {
    var co = await trang.evaluate(function () {
      return !!document.querySelector('#vgbBody .gwrap .gt[data-nhom]') && !document.getElementById('vgbBack');
    });
    if (co) return Date.now();
    await cho(10);
  }
  return 0;
}
async function choYen(ms) {
  /* Chờ tới khi không còn lời gọi nào đang treo, tối đa ms. */
  var den = Date.now() + ms;
  while (Date.now() < den) {
    if (!NHAT.some(function (x) { return !x.tra; })) { await cho(TRE + 50); if (!NHAT.some(function (x) { return !x.tra; })) return; }
    await cho(20);
  }
}

/* Mở một màn đúng đường người dùng đi: bấm ô lớn của phân hệ, rồi bấm ô nghiệp vụ. Đang không ở
   trang chủ thì bấm nút Trang chủ trước. */
async function moMan(trang, nhom, go) {
  if (await trang.evaluate(function () { return !!document.getElementById('vgbHome'); })) {
    await trang.evaluate(function () { document.getElementById('vgbHome').click(); });
    if (!await choLuoi(trang)) throw new Error('Không về được trang chủ');
  }
  await trang.click('.gt[data-nhom="' + nhom + '"]');
  await trang.waitForSelector('#vgbBody [data-go="' + go + '"]', { timeout: 15000 });
  await trang.click('#vgbBody [data-go="' + go + '"]');
}

async function bamTrangChu(trang, nhan) {
  var moc = NHAT.length;
  var t0 = Date.now();
  await trang.evaluate(function () { document.getElementById('vgbHome').click(); });
  var t1 = await choLuoi(trang);
  await choYen(20000);
  var goi = NHAT.slice(moc).filter(function (x) { return x.gui >= t0; });
  var cuoi = goi.reduce(function (a, x) { return Math.max(a, x.tra); }, t0);
  var so = await trang.evaluate(function () {
    return Array.prototype.map.call(document.querySelectorAll('#vgbBody .gt[data-nhom] .gb'), function (b) {
      return b.closest('.gt').getAttribute('data-nhom') + ':' + b.textContent;
    }).join(' ');
  });
  return { man: nhan, luoi_ms: t1 ? t1 - t0 : -1, api: goi.length, api_xong_ms: cuoi - t0, so_tren_o: so };
}

(async function () {
  var trinh = await pw.chromium.launch();
  var kq = { tre_ms: TRE, che_do: BAT ? 'bat' : 'tat', app: APP || 'repo', trang_chu: [], ve_de: null, loi: [] };
  try {
    var t = await moTrang(trinh);
    var trang = t.trang;
    await trang.goto(ORIGIN + '/bep');
    if (!await choLuoi(trang, 30000)) throw new Error('Trang chủ không hiện lưới sau 30 giây');
    await choYen(20000);
    for (var i = 0; i < MAN.length; i++) {
      var m = MAN[i];
      await moMan(trang, m.nhom, m.go);
      await choYen(20000);
      /* Lần đầu: số đếm đã cũ hơn hạn giữ (đợi quá hạn trước khi bấm) để đo đường đếm lại. */
      await cho(+thamSo("cho-het-han", "16000"));
      kq.trang_chu.push(await bamTrangChu(trang, m.ten));
      if (i === 0) {
        /* Mở lần hai liền tay từ cùng màn. */
        await moMan(trang, m.nhom, m.go);
        await choYen(20000);
        var r2 = await bamTrangChu(trang, m.ten + ' (lần hai, liền tay)');
        kq.trang_chu.push(r2);
      }
    }
    /* Màn cũ vẽ đè. */
    await moMan(trang, 'GH', 'VD');
    await cho(200);
    /* Vận đơn còn đang chờ danh sách: lùi về phân hệ Giao hàng, bấm Đối soát COD. */
    await trang.evaluate(function () { document.getElementById('vgbBack').click(); });
    await trang.waitForSelector('#vgbBody [data-go="DSCOD"]', { timeout: 15000 });
    await trang.click('#vgbBody [data-go="DSCOD"]');
    await cho(TRE_VD + 1500);
    await choYen(20000);
    var tieuDe = await trang.evaluate(function () {
      var b = document.querySelector('#vgb .vh b, #vgb .vh h1, #vgb .vh .ui-td');
      return { title: document.title, chu: b ? b.textContent.trim() : '' };
    });
    kq.ve_de = { mong: 'Đối soát COD', thay: tieuDe.title, dat: tieuDe.title.indexOf('Đối soát COD') === 0 };
    kq.loi = t.loi;
    await t.ctx.close();
  } finally { await trinh.close(); }
  console.log('Độ trễ mỗi lời gọi: ' + TRE + ' ms; giao diện ' + kq.che_do + '; bản ' + kq.app);
  console.log('| Màn xuất phát | Lưới hiện (ms) | Lời gọi máy chủ | Lời gọi cuối xong (ms) |');
  console.log('|---|---:|---:|---:|');
  kq.trang_chu.forEach(function (r) { console.log('| ' + r.man + ' | ' + r.luoi_ms + ' | ' + r.api + ' | ' + r.api_xong_ms + ' |'); });
  console.log('Số trên ô lớn sau lần cuối: ' + (kq.trang_chu.length ? kq.trang_chu[kq.trang_chu.length - 1].so_tren_o : ''));
  console.log('Màn cũ vẽ đè: mở Vận đơn rồi sang Đối soát COD, sau khi Vận đơn về màn đang hiện là "' + kq.ve_de.thay + '": ' + (kq.ve_de.dat ? 'ĐẠT' : 'TRƯỢT'));
  if (kq.loi.length) console.log('Lỗi trang: ' + kq.loi.slice(0, 5).join(' | '));
  if (RA_JSON) fs.writeFileSync(RA_JSON, JSON.stringify(kq, null, 1));
  var nhanh = kq.trang_chu.every(function (r) { return r.luoi_ms >= 0 && r.luoi_ms < 1000; });
  process.exit(nhanh && kq.ve_de.dat ? 0 : 1);
})().catch(function (e) { console.log('Lỗi: ' + (e && e.stack || e)); process.exit(1); });

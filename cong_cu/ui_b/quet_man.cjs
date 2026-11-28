/* Quét MỌI màn mở được từ menu app /bep ở giao diện mới (ui-b), máy chủ giả, không chạm site.
 *
 * Máy chụp (chup.cjs) chỉ có kịch bản cho khung chung. Công cụ này đọc danh sách mã màn
 * trong vgbGo, mở từng mã từ trang chủ (như bấm một ô [data-go]), rồi dùng lại đúng phép
 * đo của máy chụp: emoji còn sót, nhãn ngắn xuống dòng, chữ bị cắt, vùng bấm dưới 44.
 * Dữ liệu thử phần lớn trả rỗng, nên phép quét này soi KHUNG màn (tiêu đề, nút, chip, dòng
 * trống, ô tìm), không soi dòng dữ liệu. Không thay việc mở ảnh ra nhìn.
 *
 *   node cong_cu/ui_b/quet_man.cjs --ra /tmp/quet                 cả danh sách, 390x844
 *   node cong_cu/ui_b/quet_man.cjs --ra /tmp/quet --ma POS,VD     vài mã
 *   node cong_cu/ui_b/quet_man.cjs --ra /tmp/quet --anh            chụp ảnh từng màn
 *
 * Mã trả 0: không màn nào còn emoji ở lớp vẽ; 1: còn; 2: thiếu Playwright.
 */
'use strict';
var fs = require('fs');
var path = require('path');
var C = require('./chup.cjs');

function thamSo(ten, macDinh) {
  var i = process.argv.indexOf('--' + ten);
  return i > 0 && process.argv[i + 1] ? process.argv[i + 1] : macDinh;
}
var RA = thamSo('ra', '/tmp/ui-b-quet');
var KH = thamSo('khung', '390x844').split('x');
var KHUNG = { w: +KH[0], h: +KH[1], ten: KH.join('x') };
var ANH = process.argv.indexOf('--anh') > 0;
var GOC = path.resolve(__dirname, '..', '..');

/* Mã màn đọc thẳng từ thân vgbGo: thêm màn mới vào vgbGo là công cụ tự quét. */
function dsMa() {
  var src = fs.readFileSync(path.join(GOC, 'vagabond/public/js/bep/02-trang-chu.js'), 'utf8');
  var i = src.indexOf('\nfunction vgbGo(k) {');
  if (i < 0) throw new Error('Không thấy function vgbGo trong 02-trang-chu.js');
  var than = src.slice(i, src.indexOf('\n}\n', i));
  var ds = [];
  var re = /k === '([A-Z0-9_:]+)'/g, m;
  while ((m = re.exec(than))) if (ds.indexOf(m[1]) < 0) ds.push(m[1]);
  return ds;
}
/* Mã rời app (đổi trang) thì bỏ: không còn là màn của app. */
var BO = ['KBD', 'BTPO'];

async function chay() {
  var pw;
  try { pw = require('playwright'); } catch (e) {
    try { pw = require('/opt/npm-tools/node_modules/playwright'); } catch (e2) { console.log('THIẾU Playwright'); process.exit(2); }
  }
  var chon = thamSo('ma', '');
  var ma = chon ? chon.split(',') : dsMa().filter(function (x) { return BO.indexOf(x) < 0; });
  fs.mkdirSync(RA, { recursive: true });
  var trinh = await pw.chromium.launch();
  var bang = [], thieu = {};
  for (var i = 0; i < ma.length; i++) {
    var o = await C.moTrang(trinh, KHUNG, true, thieu, []);
    var dong = { ma: ma[i], tieu_de: '', emoji: [], xuong_dong: [], cat: [], nho_nut: [], loi_js: [] };
    try {
      /* Hàm máy chủ chưa có dữ liệu thử thì trả "rỗng vô hạn" thay cho null: đọc trường nào
         cũng được, danh sách nào cũng rỗng, số là 0, chữ là rỗng. Nhờ vậy màn đi tới trạng
         thái rỗng của nó (tiêu đề, nút, chip, dòng trống) thay vì nổ ở dòng đầu, và phép quét
         soi được khung màn. Chỉ dùng trong công cụ này, không dùng trong máy chụp. */
      await o.trang.addInitScript(function () {
        var MANG = ['map', 'filter', 'forEach', 'reduce', 'some', 'every', 'find', 'findIndex', 'indexOf', 'includes', 'slice', 'concat', 'join', 'sort', 'flatMap', 'flat'];
        var XU = {
          get: function (t, k) {
            if (k === 'then' || k === 'toJSON') return undefined;
            if (k === Symbol.toPrimitive) return function (h) { return h === 'number' ? 0 : ''; };
            if (k === 'length') return 0;
            if (k === Symbol.iterator) return [][Symbol.iterator].bind([]);
            if (typeof k === 'string' && MANG.indexOf(k) >= 0) return Array.prototype[k].bind([]);
            if (k === 'toString' || k === 'valueOf') return function () { return ''; };
            return rong();
          },
          has: function () { return false; },
          apply: function () { return rong(); }
        };
        function rong() { return new Proxy(function () {}, XU); }
        /* App đọc lời đáp bằng r.text() rồi JSON.parse. Máy chụp trả đúng {"message": null}
           cho hàm chưa có dữ liệu thử: chỉ đổi đúng dạng đó. */
        var parse = JSON.parse;
        JSON.parse = function (t, f) {
          var o = parse.call(JSON, t, f);
          if (o && typeof o === 'object' && o.message === null && Object.keys(o).length === 1) o.message = rong();
          return o;
        };
      });
      await o.trang.goto(C.ORIGIN + '/bep');
      await o.trang.waitForSelector('.gwrap', { timeout: 15000 });
      await o.trang.evaluate(function (k) {
        var b = document.querySelector('#vgbBody') || document.querySelector('#vgb');
        var a = document.createElement('div'); a.setAttribute('data-go', k); b.appendChild(a); a.click();
      }, ma[i]);
      await o.trang.waitForTimeout(900);
      dong.tieu_de = await o.trang.evaluate(function () { var t = document.querySelector('#vgb .vh .t, #vgb .vh h1, #vgb .vh'); return t ? (t.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 60) : ''; });
      var d = await o.trang.evaluate(C.doTrongTrang, { bat: true, chiDau: false, phamVi: '' });
      /* Emoji kèm phần tử chứa nó, để biết sửa ở đâu. */
      dong.emoji = await o.trang.evaluate(function () {
        var r = [], w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        var re = /([\u{1F000}-\u{1FAFF}←-⇿⌀-⏿☀-➿⬀-⯿ℹ‼⁉⤴⤵〰〽㊗㊙])️?/u;
        for (var n = w.nextNode(); n; n = w.nextNode()) {
          var cha = n.parentElement; if (!cha || cha.closest('svg, script, style')) continue;
          if (!cha.closest('#vgb, .sh, #tlKhung, .vf')) continue;
          var rc = cha.getBoundingClientRect(); if (!(rc.width > 0 && rc.height > 0)) continue;
          var m = re.exec(n.nodeValue); if (!m) continue;
          var lop = cha.tagName.toLowerCase() + (cha.className && typeof cha.className === 'string' ? '.' + cha.className.trim().split(/\s+/).join('.') : '');
          var cn = cha.parentElement, lopCha = cn ? cn.tagName.toLowerCase() + (typeof cn.className === 'string' && cn.className ? '.' + cn.className.trim().split(/\s+/)[0] : '') : '';
          r.push({ ky: m[1], chu: n.nodeValue.replace(/\s+/g, ' ').trim().slice(0, 50), the: lop.slice(0, 40), cha: lopCha.slice(0, 30), dau: n.nodeValue.trim().indexOf(m[0]) === 0 });
        }
        return r;
      });
      dong.xuong_dong = d.xuongDong; dong.cat = d.cat; dong.nho_nut = d.nhoNut;
      /* Test live #614 UI99: chip, nút đủ cao 44 mà chữ bên trong bị co cắt (rộng nội dung lớn hơn
         rộng hộp). Đo chữ trong từng hộp, không chỉ trang có tràn ngang hay không. */
      dong.chip_cat = await o.trang.evaluate(function () {
        var r = [];
        document.querySelectorAll('#vgb .posc, #vgb .chip, #vgb .btn, .sh .posc, .sh .chip, .sh .btn').forEach(function (e) {
          if (!e.offsetParent || getComputedStyle(e).whiteSpace.indexOf('nowrap') < 0) return;
          if (e.scrollWidth > e.clientWidth + 1) r.push((e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 24) + ' ' + e.clientWidth + '/' + e.scrollWidth);
        });
        return r;
      });
      dong.tran_ngang = await o.trang.evaluate(function () { return document.documentElement.scrollWidth > innerWidth + 1; });
      if (ANH) await o.trang.screenshot({ path: path.join(RA, ma[i] + '.png') });
    } catch (e) { dong.loi_js.push('không mở được: ' + String(e.message || e).split('\n')[0]); }
    if (o.loi.length) dong.loi_js = dong.loi_js.concat(o.loi.slice(0, 3));
    bang.push(dong);
    console.log((dong.emoji.length ? 'EMOJI ' + dong.emoji.length : 'sạch   ') + '  ' + ma[i] + '  ' + dong.tieu_de.slice(0, 40) +
      (dong.xuong_dong.length ? '  | xuống dòng ' + dong.xuong_dong.length : '') + (dong.nho_nut.length ? '  | nút nhỏ ' + dong.nho_nut.length : '') + (dong.chip_cat && dong.chip_cat.length ? '  | chữ bị cắt ' + dong.chip_cat.length : '') + (dong.tran_ngang ? '  | TRÀN NGANG' : '') +
      (dong.loi_js.length ? '  | LỖI ' + dong.loi_js[0].slice(0, 80) : ''));
    await o.ctx.close();
  }
  await trinh.close();
  fs.writeFileSync(path.join(RA, 'quet-man.json'), JSON.stringify({ khung: KHUNG.ten, bang: bang }, null, 1));
  var coEmoji = bang.filter(function (b) { return b.emoji.length; }).length;
  console.log(bang.length + ' màn: ' + coEmoji + ' màn còn emoji, tổng ' + bang.reduce(function (t, b) { return t + b.emoji.length; }, 0) + ' chỗ.');
  process.exit(coEmoji ? 1 : 0);
}
chay().catch(function (e) { console.error(e); process.exit(1); });

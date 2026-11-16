/* ĐO THẬT trên Chromium: bảng "Chọn chuông và âm báo" và bảng mã QR chuyển khoản
 * cuộn được trên màn thấp, mọi lựa chọn và nút đều chạm tới được (Codex #575,
 * 16/11/2026: bảng chọn dùng .shb có overflow:hidden, điện thoại nằm ngang
 * không với tới chip âm báo tiền và nút Nghe thử).
 *
 * HTML lấy từ chính hàm vẽ thật (gmbMoChonChuong, posQrSheet) chạy trong DOM giả,
 * CSS là biến CSS nguyên văn của 00-nen.js. Với mỗi nút: cuộn nó vào giữa vùng
 * cuộn gần nhất rồi chạm thử bằng document.elementFromPoint ở tâm nút; nút
 * không nhận được chạm là hỏng.
 *
 * Chạy:  node cong_cu/do_cuon_chuong_664.cjs
 * Mã 0 là đạt; thiếu Playwright hoặc Chromium thì trả 2 và nói rõ chưa đo được.
 * Không nằm trong kiem_truoc_deploy.sh (máy CI không có trình duyệt).
 * Bằng chứng loại "tệp trong repo, CSS nền của app", không thay ảnh chụp site thật.
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');

var GOC = path.resolve(__dirname, '..');
var dg = require(path.join(GOC, 'vagabond', 'khung', 'kiem_thu', 'hanh_vi', 'dom_gia.js'));
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
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

function dungHtml() {
  var NEN = doc('00-nen.js'), POS = doc('09-tinh-tien-quay.js');
  var MA = ['h', 'money'].map(function (t) { return layHam(NEN, t); }).join('\n') + '\n' +
    'var posPollId = null, posSepayNhan = 0, posSepayGoiY = 0;\n' + layHam(POS, 'posQrSheet') + '\n' +
    doc('66-goi-mon-tai-ban.js') + '\n' + doc('77-chuong-mau.js');
  var tai = dg.taiLieuGia();
  var g = {
    console: console, document: tai, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, Number: Number, Date: Date, parseInt: parseInt, parseFloat: parseFloat,
    encodeURIComponent: encodeURIComponent, localStorage: { getItem: function () { return null; }, setItem: function () {} },
    sessionStorage: { getItem: function () { return null; }, setItem: function () {} },
    setTimeout: function () { return 0; }, setInterval: function () { return 0; }, clearInterval: function () {},
    toast: function () {}, api: function () { return new Promise(function () {}); },
    posTaiKhoan: function () { return { ten: 'The Vagabond Patisserie', bank: 'MB', stk: '0001234567' }; },
    posQrUrl: function () { return 'data:image/gif;base64,R0lGODlhAQABAAAAACw='; },
    posQrLoi: function () { return ''; }, posNutIn: function () { return ''; }, posBillVua: 'TCVG8FRJ', siName: 'TCVG8FRJ'
  };
  g.window = g;
  vm.runInNewContext(MA, g, { filename: 'do-cuon.js' });
  g.gmbMoChonChuong();
  var chon = tai.body.children[tai.body.children.length - 1].outerHTML;
  g.posQrSheet('TCVG8FRJ', 95000, 'TCVG8FRJ', '', 'TCV');
  var qr = tai.body.children[tai.body.children.length - 1].outerHTML;
  function trang(than) {
    return '<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
      '<style>html,body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}' + cssNen() +
      '</style></head><body>' + than + '</body></html>';
  }
  return { chon: trang(chon), qr: trang(qr) };
}

var NUT = {
  chon: ['[data-gmbmau]', '[data-gmbnghe]', '[data-tienmau]', '[data-tiennghe]', '[data-gmbdong]'],
  qr: ['[data-amchon]', '[data-y]', '[data-in]']
};
var MAN = [{ ten: 'điện thoại nằm ngang 667x375', w: 667, h: 375 }, { ten: 'điện thoại đứng 390x844', w: 390, h: 844 },
  { ten: 'điện thoại nhỏ nằm ngang 568x320', w: 568, h: 320 }];

(async function () {
  var pw;
  try { pw = require('playwright'); } catch (e) { console.log('CHƯA ĐO: thiếu Playwright'); process.exit(2); }
  var br;
  try { br = await pw.chromium.launch(); } catch (e) { console.log('CHƯA ĐO: không mở được Chromium'); process.exit(2); }
  var html = dungHtml(), hong = 0, dat = 0;
  for (var m of MAN) {
    var p = await br.newPage({ viewport: { width: m.w, height: m.h } });
    for (var k of ['chon', 'qr']) {
      await p.setContent(html[k]);
      var ds = await p.evaluate(function (chon) {
        var ra = [];
        chon.forEach(function (c) { document.querySelectorAll(c).forEach(function (el, i) { ra.push([c, i]); }); });
        return ra;
      }, NUT[k]);
      if (!ds.length) { hong++; console.log('  HONG  ' + m.ten + ' ' + k + ' không thấy nút nào'); }
      for (var d of ds) {
        /* Như ngón tay: mỗi nút đo trên trang mới, chỉ cuộn bằng bánh xe chuột
           ở giữa bảng (vùng overflow:hidden không cuộn theo bánh xe), tối đa 30 lần. */
        await p.setContent(html[k]);
        var x = null;
        for (var lan = 0; lan <= 30; lan++) {
          x = await p.evaluate(function (a) {
            var el = document.querySelectorAll(a[0])[a[1]], r = el.getBoundingClientRect();
            var cx = r.left + r.width / 2, cy = r.top + r.height / 2;
            var t = cy >= 0 && cy <= innerHeight ? document.elementFromPoint(cx, cy) : null;
            return { chon: a[0] + (el.getAttribute('data-gmbmau') || el.getAttribute('data-tienmau') || ''),
              ok: !!(t && (t === el || el.contains(t))), cao: Math.round(r.height) };
          }, d);
          if (x.ok) break;
          var hop = await p.evaluate(function () { var r = document.querySelector('.shb').getBoundingClientRect(); return [r.left + r.width / 2, Math.max(r.top, 0) + 40]; });
          await p.mouse.move(hop[0], hop[1]);
          await p.mouse.wheel(0, 120);
          await p.waitForTimeout(30);
        }
        var tot = x.ok && (x.chon === '[data-gmbdong]' || x.cao >= 44);
        if (tot) dat++; else { hong++; console.log('  HONG  ' + m.ten + ' ' + k + ' ' + x.chon + ' chạm=' + x.ok + ' cao=' + x.cao); }
      }
    }
    await p.close();
  }
  await br.close();
  console.log(dat + ' nút chạm được, ' + hong + ' hỏng.');
  process.exit(hong ? 1 : 0);
})();

/* DO VUNG BAM THAT cua o tim, o ghim va nut ghim tren man dien thoai 390x844.
 *
 * Vi sao co tep nay (bai hoc dat nhat cua PR #426, 03/10/2026).
 * ------------------------------------------------------------
 * AGENTS.md dieu 13 chot: nut, chip, dong cao it nhat 44 diem; chu toi thieu
 * 13 diem; khong cuon ngang ca trang. Ban dau bo kiem chot dieu do bang cach
 * DO CHUOI trong tep CSS: tim thay "width:44px" la coi nhu dat.
 *
 * Do chuoi xanh suot, ma do that tren Chromium ra 21x19:
 *   - `.vgbgb` la the <span>, ma span mac dinh `display:inline`. Trinh duyet
 *     BO QUA width va height tren the inline. Chuoi van co trong tep.
 *   - Dau X treo ra ngoai mep o, ma dai o ghim co `overflow-x:auto` nen
 *     trinh duyet bien luon truc doc thanh `overflow-y:auto` va CAT phan tran.
 *     Do duoc 44 ngang nhung chi 29 doc.
 *
 * Nen tep nay khong do chuoi. No ban tia tu tam nut ra bon huong bang
 * `document.elementFromPoint`, dung nhu ngon tay cham vao man, va chi nhan
 * nhung diem ma trinh duyet thuc su giao cho dung nut do.
 *
 * Cach chay:
 *     node vagabond/khung/kiem_thu/do_vung_bam_565.js
 *     node vagabond/khung/kiem_thu/do_vung_bam_565.js --anh /duong/dan.png
 *
 * Ma tra ve 0 la moi so do dat nguong. Thieu Playwright hoac thieu Chromium
 * thi tra ve 2 va NOI RO la chua do duoc - khong bao gio tra ve 0.
 *
 * KHONG nam trong kiem_truoc_deploy.sh: may chay CI cua GitHub tay khong,
 * khong co trinh duyet. Day la buoc chay tay truoc khi ban giao giao dien,
 * va so do phai dinh len PR (CLAUDE.md dieu 20).
 *
 * Bang chung tep nay cho ra la loai "tep trong repo mo bang file:// voi API
 * gia lap, chi co CSS noi trong tep". No KHONG thay duoc anh chup tren site
 * that, noi con co them CSS cua khung Frappe.
 */
'use strict';

var fs = require('fs');
var os = require('os');
var path = require('path');
var vm = require('vm');

var GOC = path.resolve(__dirname, '..', '..', '..');
var dg = require(path.join(__dirname, 'hanh_vi', 'dom_gia.js'));
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
var SRC = fs.readFileSync(path.join(BEP, '02-trang-chu.js'), 'utf8');

/* CSS NEN that cua app (bien CSS trong 00-nen.js). Thieu no thi `.hub`,
   `.h1`, `.h2` khong co co chu that va phep do co chu ra so cua trinh duyet
   chu khong phai so cua app. Lay nguyen van, khong chep tay. */
function cssNen() {
  var n = fs.readFileSync(path.join(BEP, '00-nen.js'), 'utf8');
  var a = n.indexOf('var CSS = `');
  if (a < 0) throw new Error('khong thay bien CSS trong 00-nen.js');
  a += 'var CSS = `'.length;
  var b = n.indexOf('`;', a);
  if (b < 0) throw new Error('bien CSS trong 00-nen.js khong dong ngoac');
  return n.slice(a, b);
}

var NGUONG_BAM = 44;   /* AGENTS.md dieu 13 */
var NGUONG_CHU = 13;

/* ---------- dung HTML that tu chinh ham ve cua man hinh ---------- */

function dong(k, ic, t1, t2) {
  return '<div class="hub" data-go="' + k + '"><div class="hi">' + ic + '</div>' +
    '<div class="ht"><div class="h1">' + t1 + '</div><div class="h2">' + t2 + '</div></div></div>';
}

function dungTrang() {
  var tai = dg.taiLieuGia();
  tai.head = new dg.ElementGia('head');
  var than = new dg.ElementGia('div');
  than.attrs.id = 'vgbBody';
  tai.body.appendChild(than);
  than.innerHTML = [
    dong('POS', '🧾', 'Tính tiền - hoá đơn bán hàng', 'Bán tại quầy'),
    dong('CNPT', '💸', 'Công nợ phải trả', 'Còn nợ nhà cung cấp nào'),
    dong('HDMUA', '🛒', 'Hoá đơn mua vào', 'Lọc theo nhà cung cấp'),
    dong('VD', '🛵', 'Vận đơn', 'Giao hàng trong ngày'),
    dong('APPTT', '📁', 'Tạo APP - Hồ sơ thanh toán', 'Lập hồ sơ trả tiền')
  ].join('');
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array,
    Object: Object, RegExp: RegExp, Date: Date, Promise: Promise, parseInt: parseInt,
    parseFloat: parseFloat, isNaN: isNaN, setTimeout: setTimeout,
    h: function (s) { return String(s == null ? '' : s); },
    api: function (d) {
      if (d === 'vagabond.ghim.lay') {
        return Promise.resolve({ ghim: ['POS', 'CNPT', 'HDMUA', 'VD', 'APPTT'], toi_da: 5 });
      }
      return Promise.resolve({});
    },
    toast: function () { }, coQuyenKeToan: function () { return true; },
    coQuyenMua: function () { return true; }, nenCoQuyen: function () { return false; },
    frame: function (t, html) { var e = new dg.ElementGia('div'); tai.body.appendChild(e); e.innerHTML = html; return e; },
    root: new dg.ElementGia('div'), location: { pathname: '/x' }, history: { pushState: function () { } },
    money: String, today: function () { return ''; }, errMsg: String
  };
  that.globalThis = that;
  that.window = that;
  vm.runInNewContext(SRC, that, { filename: '02-trang-chu.js' });
  that.vgbGo = function () { };
  that.S = { stack: [that.scrHome], cuon: [0] };
  return { g: that, tai: tai, than: than };
}

function soanHtml(cb) {
  var m = dungTrang();
  m.g.vgbGomNhom();
  setTimeout(function () {
    var css = m.tai.head.children.map(function (x) { return x.textContent; }).join('\n');
    m.g.VGB_SUA_GHIM = false; m.g.vgbVeGhim();
    var thuong = m.tai.getElementById('vgbGhimW').innerHTML;
    m.g.VGB_SUA_GHIM = true; m.g.vgbVeGhim();
    var sua = m.tai.getElementById('vgbGhimW').innerHTML;
    var o = m.tai.getElementById('vgbTim');
    o.value = 'cong no'; o.oninput();
    var kq = m.tai.getElementById('vgbKQ').innerHTML;
    cb('<!doctype html><html lang="vi"><head><meta charset="utf-8">' +
      '<meta name="viewport" content="width=device-width,initial-scale=1">' +
      '<title>Do vung bam o ghim v565</title><style>' +
      'html,body{margin:0;padding:0;background:#eef1f5;' +
      'font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;color:#101828}' +
      '#vgbBody{padding-bottom:24px}.vgbtimw{padding:12px 12px 0}' +
      '.nhan{font-size:12px;color:#667085;padding:14px 12px 4px;font-weight:700;' +
      'text-transform:uppercase;letter-spacing:.4px}' +
      cssNen() + '\n' + css + '</style></head><body>' +
      '<div id="vgbBody"><div class="vgbtimw">' +
      '<input id="vgbTim" class="vgbtim" type="search" value="cong no" autocomplete="off"></div>' +
      '<div id="vgbDuoi">' +
      '<div class="nhan">Khoi ghim - che do thuong</div><div id="ghimThuong">' + thuong + '</div>' +
      '<div class="nhan">Khoi ghim - che do Sua ghim</div><div id="ghimSua">' + sua + '</div>' +
      '<div class="nhan">Ket qua tim, moi dong co nut ghim</div>' +
      '<div id="vgbKQ" class="vgbkq">' + kq + '</div>' +
      '</div></div></body></html>');
  }, 30);
}

/* ---------- do ---------- */

function doTrongTrang() {
  var ra = {};
  function vung(el, ten) {
    if (!el) { ra[ten] = { thieu: 1 }; return; }
    var r = el.getBoundingClientRect();
    var cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    function xa(dx, dy) {
      var d = 0;
      for (var i = 1; i <= 80; i++) {
        var x = cx + dx * i, y = cy + dy * i;
        if (x < 0 || y < 0 || x > window.innerWidth || y > window.innerHeight) break;
        var t = document.elementFromPoint(x, y);
        if (!t || !(t === el || el.contains(t))) break;
        d = i;
      }
      return d;
    }
    var t0 = document.elementFromPoint(cx, cy);
    ra[ten] = {
      the: { w: Math.round(r.width), h: Math.round(r.height) },
      bam: { w: xa(-1, 0) + xa(1, 0) + 1, h: xa(0, -1) + xa(0, 1) + 1 },
      tam_trung: !!(t0 && (t0 === el || el.contains(t0)))
    };
  }
  vung(document.querySelector('#vgbKQ .vgbgb'), 'nut_ghim_trong_ket_qua');
  vung(document.querySelector('#ghimSua .vgbgx'), 'dau_X_tren_o_ghim');
  vung(document.querySelector('#ghimThuong .vgbgo'), 'o_ghim');
  vung(document.querySelector('#vgbKQ .vgbkqd'), 'dong_ket_qua');
  vung(document.querySelector('.vgbtim'), 'o_tim');
  /* Chu do v565 dat ra. Day la phan PR nay chiu trach nhiem. */
  ra.chu = {
    o_tim: getComputedStyle(document.querySelector('.vgbtim')).fontSize,
    ten_o_ghim: getComputedStyle(document.querySelector('#ghimThuong .vgbgn')).fontSize
  };
  /* Chu do CSS NEN cua app dat ra tu truoc (`.hub .h1`, `.hub .h2` trong
     00-nen.js). Moi dong nghiep vu trong app deu dung co nay, khong rieng
     man nay. Chi GHI NHAN de bao lai, khong tinh vao ma tra ve: sua no la
     doi giao dien ca app, viec do phai do anh Viet quyet. */
  ra.chu_nen = {
    ten_dong: getComputedStyle(document.querySelector('#vgbKQ .h1')).fontSize,
    mo_ta_dong: getComputedStyle(document.querySelector('#vgbKQ .h2')).fontSize
  };
  ra.cuon = {
    trang_cuon_ngang: document.documentElement.scrollWidth > window.innerWidth,
    dai_ghim_cuon_ngang: (function () {
      var gl = document.querySelector('#ghimThuong .vgbgl');
      return !!gl && gl.scrollWidth > gl.clientWidth;
    })()
  };
  return ra;
}

/* ---------- chay ---------- */

(function () {
  var cmd = process.argv.slice(2);
  var duongAnh = '';
  var i = cmd.indexOf('--anh');
  if (i >= 0) duongAnh = cmd[i + 1] || '';

  var chromium;
  try {
    chromium = require('playwright').chromium;
  } catch (e) {
    console.error('CHUA DO DUOC: may nay khong co playwright.');
    console.error('  npm install playwright   (Chromium da co san o /opt/pw-browsers)');
    console.error('  Dung bao la dat khi chua do duoc.');
    process.exit(2);
  }

  soanHtml(function (html) {
    var tep = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'vgbdo-')), 'trang.html');
    fs.writeFileSync(tep, html);
    (async function () {
      var moc = { executablePath: '/opt/pw-browsers/chromium' };
      var b;
      try {
        b = await chromium.launch(moc);
      } catch (e) {
        try { b = await chromium.launch(); } catch (e2) {
          console.error('CHUA DO DUOC: khong mo duoc Chromium. ' + e2.message);
          process.exit(2);
        }
      }
      var pg = await b.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
      await pg.goto('file://' + tep);
      await pg.waitForTimeout(200);
      var ra = await pg.evaluate(doTrongTrang);
      if (duongAnh) await pg.screenshot({ path: duongAnh, fullPage: true });
      await b.close();

      console.log('Man 390x844, Chromium, file:// voi API gia lap.\n');
      var hong = [];
      [['nut_ghim_trong_ket_qua', 1], ['dau_X_tren_o_ghim', 1], ['o_ghim', 1],
       ['dong_ket_qua', 1], ['o_tim', 1]].forEach(function (x) {
        var k = x[0], v = ra[k];
        if (!v || v.thieu) { hong.push(k + ': khong tim thay tren trang'); return; }
        var dat = v.bam.w >= NGUONG_BAM && v.bam.h >= NGUONG_BAM && v.tam_trung;
        console.log('  ' + k.padEnd(26) + ' the ' + v.the.w + 'x' + v.the.h +
          ', VUNG BAM ' + v.bam.w + 'x' + v.bam.h + '  ' + (dat ? 'DAT' : 'HONG'));
        if (!dat) hong.push(k + ': vung bam ' + v.bam.w + 'x' + v.bam.h + ', can >= ' + NGUONG_BAM);
      });
      console.log('');
      Object.keys(ra.chu).forEach(function (k) {
        var px = parseFloat(ra.chu[k]);
        var dat = px >= NGUONG_CHU;
        console.log('  chu ' + k.padEnd(22) + ' ' + ra.chu[k] + '  ' + (dat ? 'DAT' : 'HONG'));
        if (!dat) hong.push('chu ' + k + ' = ' + ra.chu[k] + ', can >= ' + NGUONG_CHU + 'px');
      });
      console.log('');
      console.log('  CSS NEN CUA APP (co tu truoc, ngoai pham vi v565):');
      Object.keys(ra.chu_nen).forEach(function (k) {
        var px = parseFloat(ra.chu_nen[k]);
        console.log('  chu ' + k.padEnd(22) + ' ' + ra.chu_nen[k] +
          (px >= NGUONG_CHU ? '  dat' : '  DUOI 13 DIEM - can bao lai, khong tu sua'));
      });
      console.log('');
      console.log('  trang cuon ngang           ' + ra.cuon.trang_cuon_ngang +
        '  ' + (ra.cuon.trang_cuon_ngang ? 'HONG' : 'DAT'));
      if (ra.cuon.trang_cuon_ngang) hong.push('ca trang bi cuon ngang');
      console.log('  dai o ghim cuon ngang      ' + ra.cuon.dai_ghim_cuon_ngang +
        '  (trong khoi, khong phai ca trang)');
      if (duongAnh) console.log('\n  anh: ' + duongAnh);
      console.log('');
      if (hong.length) {
        console.log('KHONG DAT:');
        hong.forEach(function (c) { console.log('  - ' + c); });
        process.exit(1);
      }
      console.log('Moi so do dat nguong AGENTS.md dieu 13.');
    })();
  });
})();

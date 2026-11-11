/* v649 (anh Việt 11/11/2026, ảnh màn Lệnh sản xuất "xô lệch quá thể"): thẻ
 * lệnh sản xuất chỉ còn ba cột (ảnh, nội dung, nút ✓); số lượng và trạng thái
 * nằm trên MỘT dòng riêng dưới tên món, không còn cột phải chữ to.
 *
 * Nạp THẬT scrMfgList của 05-san-xuat.js vào DOM giả, cho máy chủ giả trả đúng
 * ba lệnh trong ảnh anh gửi (LSX-111126-000599, 000598, 000597), rồi đọc cây
 * DOM màn vẽ ra. Không gọi thêm hàm nào ngoài lối mở màn của bếp.
 *
 * Chạy: node vagabond/khung/kiem_thu/hanh_vi/the_lenh_649.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var SRC = fs.readFileSync(path.join(GOC, 'vagabond', 'public', 'js', 'bep', '05-san-xuat.js'), 'utf8');

function layHam(src, ten) {
  var dau = src.indexOf('function ' + ten + '(');
  if (dau < 0) throw new Error('Khong thay ham ' + ten);
  if (src.slice(Math.max(0, dau - 6), dau) === 'async ') dau -= 6;
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Ham ' + ten + ' khong dong ngoac');
}

var LENH = [
  { ten: 'LSX-111126-000599', ma_mon: 'NBTP00033', ten_mon: 'BTP Cấp 1 Bánh Ổ Hannari size 12cm', so_can: 9, so_da: 0, dvt: 'Cái',
    ngay_lam: '2026-11-11', trang_thai: 'Not Started', ten_trang_thai: 'Chưa bắt đầu', xong: 0, bep: 'Pastry',
    thieu: [{ ma: 'A' }, { ma: 'B' }], chip: [] },
  { ten: 'LSX-111126-000598', ma_mon: 'NBTP00036', ten_mon: 'BTP Cấp 2 Bánh Ổ Hannari size 12cm', so_can: 24, so_da: 0, dvt: 'Cái',
    ngay_lam: '2026-11-11', trang_thai: 'Not Started', ten_trang_thai: 'Chưa bắt đầu', xong: 0, bep: 'Pastry',
    thieu: [{ ma: 'A' }, { ma: 'B' }], chip: [] },
  { ten: 'LSX-111126-000597', ma_mon: 'BAWC00090', ten_mon: 'Bánh Ổ Hannari, size 16cm', so_can: 2, so_da: 0, dvt: 'Món',
    ngay_lam: '2026-11-11', trang_thai: 'Not Started', ten_trang_thai: 'Chưa bắt đầu', xong: 0, bep: 'Pastry',
    thieu: [{ ma: 'A' }], chip: [] }
];

function moMan(lenh) {
  var tai = dg.taiLieuGia();
  var khung = { el: null };
  var the = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    Promise: Promise, parseFloat: parseFloat, setTimeout: setTimeout,
    h: function (s) {
      return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
      });
    },
    mfg: { tab: 'open', bep: '', han: '', mon: '' }, mfgMo: {},
    loadMasters: async function () {}, mfgInitWh: function () {},
    api: async function (m) {
      if (m === 'vagabond.ke_hoach_sx.ds_lenh') return { lenh: lenh, cac_bep: [{ ma: 'Baker', ten: 'Baker' }, { ma: 'Pastry', ten: 'Pastry' }] };
      throw new Error('api la: ' + m);
    },
    frame: function (t, html) {
      var el = new dg.ElementGia('div');
      el.parentNode = tai.body;
      tai.body.children = [el];
      el.innerHTML = html;
      khung.el = el;
      return el;
    },
    anhMon: function () { return '<div class="hi">🍰</div>'; },
    kl: function (n, d) { return n + ' ' + d; },
    dmy: function (s) { return s.split('-').reverse().join('/'); },
    today: function () { return '2026-11-11'; },
    r3: function (n) { return Math.round(n * 1000) / 1000; },
    toast: function () {}, errMsg: function (e) { return String(e); }, go: function () {}
  };
  vm.createContext(the);
  ['mfgDongSo', 'mfgGomMon', 'scrMfgList'].forEach(function (t) { vm.runInContext(layHam(SRC, t), the); });
  return the.scrMfgList().then(function () { return khung.el; });
}

var ket = { dat: 0, hong: 0 };
async function ca(ten, fn) {
  try { await fn(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); }
}
function bang(mo, a, b) {
  var x = JSON.stringify(a), y = JSON.stringify(b);
  if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y);
}

(async function () {
  await ca('1. ba lenh trong anh anh Viet: moi the dung ba cot (anh, noi dung, nut), khong con cot phai chu to', async function () {
    var el = await moMan(LENH);
    var the = el.querySelectorAll('.li');
    bang('ba the', the.length, 3);
    the.forEach(function (t) {
      bang('the moi ' + t.dataset.n, t.attrs['class'], 'li lm');
      bang('khong con o so chu to (.amt)', t.querySelectorAll('.amt').length, 0);
      bang('ba con truc tiep: anh, noi dung, nut', t.children.map(function (c) { return c.attrs['class']; }), ['hi', 'lt', 'lok']);
    });
  });

  await ca('2. so luong va trang thai nam tren mot dong rieng duoi ten mon, dung so trong anh', async function () {
    var el = await moMan(LENH);
    var dong = el.querySelectorAll('.lso').map(function (d) { return d.textContent; });
    bang('dong so', dong, ['0 Cái / 9 CáiChưa bắt đầu', '0 Cái / 24 CáiChưa bắt đầu', '0 Món / 2 MónChưa bắt đầu']);
    var thu = el.querySelectorAll('.lt')[0].children.map(function (c) { return c.attrs['class']; });
    bang('thu tu trong noi dung: ten, ma lenh, so, chip', thu, ['l1', 'l2', 'lso', 'noi']);
  });

  await ca('3. nut ✓ van bam duoc va chip Thieu nguyen lieu van hien', async function () {
    var el = await moMan(LENH);
    bang('nut', el.querySelectorAll('[data-ok]').map(function (b) { return b.dataset.ok; }),
      ['LSX-111126-000599', 'LSX-111126-000598', 'LSX-111126-000597']);
    bang('chip thieu', el.querySelectorAll('.q').map(function (i) { return i.textContent; }),
      ['⚠️ Thiếu 2 nguyên liệu', '⚠️ Thiếu 2 nguyên liệu', '⚠️ Thiếu 1 nguyên liệu']);
  });

  await ca('4. hai lenh cung mon thanh the gop: the gop cung bo cuc moi, so tong o dong rieng', async function () {
    var hai = [LENH[0], Object.assign({}, LENH[0], { ten: 'LSX-111126-000600', so_can: 3 })];
    var el = await moMan(hai);
    var g = el.querySelectorAll('.lgop')[0].children[0];
    bang('the gop bo cuc moi', g.attrs['class'], 'li lm');
    bang('so tong', g.querySelectorAll('.lsq')[0].textContent, '0 Cái / 12 Cái');
    bang('nut xem lenh nam tren dong so', g.querySelectorAll('.lso')[0].querySelectorAll('.lsl')[0].textContent, 'Xem 2 lệnh');
  });

  console.log('\n' + ket.dat + ' dat, ' + ket.hong + ' hong');
  process.exit(ket.hong ? 1 : 0);
})();

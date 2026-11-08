/* Ca kiem HANH VI v645 dot 4 (anh Viet 08/11/2026):
 *  1. Man Khuyen mai co the "Den bu khach gap su co": quan ly mo tam, go ma don,
 *     bam Tim don, chon muc va ly do, bam Cap ma; man hien ma va noi co gui Zalo.
 *  2. Man tinh tien: hoa don da chon khach thi tam "Ma uu dai cua khach" hien san
 *     ma rieng con han cua khach, bam la ap (khoi bat khach doc ma).
 *
 * CHAY THAT: nap nguyen 13-khuyen-mai.js (cung posChipNut that cua 09) vao DOM
 * gia, bam dung chuoi nut cua nguoi dung. May chu la ban gia ghi lai loi goi;
 * phep cap ma, khoa mot don mot ma nam o may chu (thu_zalo_uu_dai_645.py).
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/km_den_bu_645.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var domGia = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
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

var ket = { dat: 0, hong: 0, loi: [] };
function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 4).join('\n         ') : String(e))); }
}
async function nghi() { for (var i = 0; i < 12; i++) await Promise.resolve(); await new Promise(function (r) { setImmediate(r); }); }
function chu(el) { var s = el._chu || ''; (el.children || []).forEach(function (c) { s += chu(c); }); return s; }

var MUC = [
  { ma: 'nhe', ten: 'Nhẹ', giai_thich: 'Giao trễ hơn 30 phút, thiếu nến hoặc thiệp.', uu_dai: 'Giảm 30.000đ', chua_cai: 0 },
  { ma: 'vua', ten: 'Vừa', giai_thich: 'Sai trang trí, sai lời chúc, thiếu món.', uu_dai: 'Giảm 15%', chua_cai: 0 },
  { ma: 'nang', ten: 'Nặng', giai_thich: 'Bánh hỏng không dùng được.', uu_dai: '', chua_cai: 1 },
];
var LY = ['Giao trễ', 'Thiếu nến, thiệp', 'Sai trang trí', 'Sai lời chúc', 'Thiếu món', 'Bánh hỏng', 'Khác'];

function khoi(o) {
  o = o || {};
  var goi = [], tin = [];
  var tai = domGia.taiLieuGia();
  var g = { console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array,
    Promise: Promise, Error: Error, RegExp: RegExp, parseInt: parseInt, setTimeout: function () { return 1; }, clearTimeout: function () {},
    document: tai, __goi: goi, __tin: tin };
  g.__api = function (m, a) {
    goi.push({ m: m, a: JSON.parse(JSON.stringify(a || {})) });
    if (m === 'vagabond.khuyen_mai.ds_ctkm') return Promise.resolve({ km: [] });
    if (m === 'vagabond.khuyen_mai.ds_combo') return Promise.resolve({ combo: [] });
    if (m === 'vagabond.don_dau_web.doc_cai_dat') return Promise.resolve({ cai_dat: { bat: 1, giam: 50000, toi_thieu: 300000, can_otp: 1, hien_thanh_toan: 1, hien_uu_dai: 1 }, otp_mo: 1 });
    if (m === 'vagabond.den_bu.xem_don') {
      if (!a.q) return Promise.resolve({ ok: 0, muc: MUC, ds_ly_do: LY, ly_do: '' });
      return Promise.resolve(Object.assign({ ok: 1, muc: MUC, ds_ly_do: LY, hoa_don: 'ACC-SINV-1', ma_don: '97077', ngay: '08/11/2026',
        tien: '450.000đ', khach: 'Lan Anh', sdt: '090***4567', dong_y: 1, khach_le: 0, da_cap: '', da_cap_muc: '' }, o.don || {}));
    }
    if (m === 'vagabond.den_bu.cap_ma') return Promise.resolve(Object.assign({ ok: 1, ma: 'K7M2QP', han: '07/01/2027', uu_dai: 'Giảm 15%', zalo: 1, ly_do: '' }, o.cap || {}));
    if (m === 'vagabond.khuyen_mai.ma_cua_khach') return Promise.resolve({ ds: o.maKhach || [] });
    if (m === 'vagabond.khuyen_mai.tra_ma') return Promise.resolve({ dung_duoc: 1, ten: 'Quà sinh nhật', danh_cho: 'KH-1', ten_khach: 'Lan Anh', rang_buoc: 1 });
    return Promise.reject(new Error('api la: ' + m));
  };
  g.window = g;
  vm.createContext(g);
  vm.runInContext([
    'var __stack = []; var posDon = { khach_ma: "", maVc: "" }; var posQuay = { ma: "TCV" };',
    'function frame(t, html, opt) { document.body.children = []; var vb = document.createElement("div"); vb.setAttribute("id", "vgbBody"); vb.innerHTML = html; document.body.appendChild(vb); return vb; }',
    'function go(fn) { __stack.push(fn); return fn(); } function toast(s) { __tin.push(String(s)); } function busy() {}',
    'function h(s) { return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;"); } function money(x) { return String(x); }',
    'function api(m, a) { return __api(m, a); }',
    'function posDoc() {} function posNguonThuc() { return "Tại quầy"; } function scrPosQuay() {}',
    layHam(fs.readFileSync(path.join(BEP, '09-tinh-tien-quay.js'), 'utf8'), 'posChipNut'),
  ].join('\n'), g);
  vm.runInContext(fs.readFileSync(path.join(BEP, '13-khuyen-mai.js'), 'utf8'), g);
  return g;
}
async function moMan(o) { var g = khoi(o); await g.go(g.scrKhuyenMai); await nghi(); return g; }
function than(g) { return g.document.getElementById('vgbBody'); }
async function bamMan(g, chon) { var b = than(g), el = b.querySelector(chon); if (!el) throw new Error('khong thay ' + chon); b.onclick({ target: el }); await nghi(); }
function tam(g) { var ds = g.document.body.children; return ds[ds.length - 1]; }
async function bamTam(g, chon) { var t = tam(g), el = t.querySelector(chon); if (!el) throw new Error('khong thay ' + chon); await t.onclick({ target: el }); await nghi(); }
function goiCua(g, m) { return g.__goi.filter(function (x) { return x.m === m; }); }

async function moTamTimDon(o) {
  var g = await moMan(o);
  await bamMan(g, '#kmDbMo');
  tam(g).querySelector('#kmDbQ').value = '97077';
  await bamTam(g, '#kmDbTim');
  return g;
}

(async function () {
  console.log('v645 dot 4: den bu tren man Khuyen mai, ma cua khach tren man tinh tien');

  await ca('màn Khuyến mãi có thẻ Đền bù với nút Cấp mã đền bù cao 44; bấm mở tấm và đọc ba mức từ máy chủ', async function () {
    var g = await moMan();
    var the = than(g).querySelector('#kmDenBu');
    dung('có thẻ', !!the);
    dung('nói rõ mỗi đơn một mã', chu(the).indexOf('mỗi đơn một mã') >= 0);
    dung('nút cao 44', /min-height:44px/.test(the.querySelector('#kmDbMo').getAttribute('style')));
    await bamMan(g, '#kmDbMo');
    bang('đọc ba mức một lần, chưa có đơn', goiCua(g, 'vagabond.den_bu.xem_don').map(function (x) { return x.a.q; }), ['']);
    var t = chu(tam(g));
    dung('ba mức có ưu đãi đang cài', t.indexOf('Nhẹ: Giảm 30.000đ') >= 0 && t.indexOf('Vừa: Giảm 15%') >= 0);
    dung('mức chưa cài nói chỗ cài', t.indexOf('Chưa chọn chương trình cho mức này') >= 0);
    dung('nút Cấp khoá khi chưa có đơn', tam(g).querySelector('#kmDbCap').hasAttribute('disabled'));
  });

  await ca('tìm đơn 97077, chọn mức Vừa và lý do Sai trang trí, bấm Cấp: gửi đúng đơn, mức, lý do; màn hiện mã và báo gửi Zalo', async function () {
    var g = await moTamTimDon();
    bang('tra đúng mã khách gõ', goiCua(g, 'vagabond.den_bu.xem_don').map(function (x) { return x.a.q; }), ['', '97077']);
    dung('hiện đơn và khách', chu(tam(g)).indexOf('97077') >= 0 && chu(tam(g)).indexOf('Lan Anh') >= 0);
    await bamTam(g, '#kmDbCap');
    dung('chưa chọn mức thì nhắc, không cấp', g.__tin.indexOf('Chọn mức đền bù.') >= 0 && !goiCua(g, 'vagabond.den_bu.cap_ma').length);
    await bamTam(g, '[data-kmdbmuc="nang"]');
    dung('mức chưa cài bấm không chọn được', tam(g).querySelector('[data-kmdbmuc="nang"]').getAttribute('aria-pressed') === 'false');
    await bamTam(g, '[data-kmdbmuc="vua"]');
    await bamTam(g, '#kmDbCap');
    dung('chưa chọn lý do thì nhắc', g.__tin.indexOf('Chọn lý do.') >= 0 && !goiCua(g, 'vagabond.den_bu.cap_ma').length);
    await bamTam(g, '[data-kmdbly="Sai trang trí"]');
    await bamTam(g, '#kmDbCap');
    var cap = goiCua(g, 'vagabond.den_bu.cap_ma');
    bang('gửi đúng một lần', cap.map(function (x) { return [x.a.q, x.a.muc, x.a.ly_do, x.a.ghi_chu]; }), [['ACC-SINV-1', 'vua', 'Sai trang trí', '']]);
    bang('hiện mã', chu(tam(g).querySelector('#kmDbMa')), 'K7M2QP');
    dung('báo gửi Zalo trong giờ 8:00 tới 20:00', chu(tam(g)).indexOf('8:00 tới 20:00') >= 0);
  });

  await ca('khách chưa đồng ý nhận tin: kết quả nói chưa gửi Zalo và bảo đọc mã cho khách', async function () {
    var g = await moTamTimDon({ don: { dong_y: 0 }, cap: { zalo: 0, ly_do: 'Khách chưa đồng ý nhận tin Zalo.' } });
    dung('báo trước khi cấp', chu(tam(g)).indexOf('quản lý đọc mã cho khách') >= 0);
    await bamTam(g, '[data-kmdbmuc="nhe"]');
    await bamTam(g, '[data-kmdbly="Giao trễ"]');
    await bamTam(g, '#kmDbCap');
    var t = chu(tam(g));
    dung('nói chưa gửi và lý do', t.indexOf('Chưa gửi Zalo: Khách chưa đồng ý nhận tin Zalo.') >= 0 && t.indexOf('Đọc mã này cho khách') >= 0);
  });

  await ca('đơn đã có mã đền bù: nói mã cũ, nút Cấp khoá, bấm cũng không gọi máy chủ', async function () {
    var g = await moTamTimDon({ don: { da_cap: 'ABC123', da_cap_muc: 'Vừa' } });
    dung('nói mã cũ', chu(tam(g)).indexOf('đã được cấp mã đền bù ABC123 (mức Vừa)') >= 0);
    dung('nút khoá', tam(g).querySelector('#kmDbCap').hasAttribute('disabled'));
    await bamTam(g, '[data-kmdbmuc="nhe"]');
    await bamTam(g, '[data-kmdbly="Giao trễ"]');
    await bamTam(g, '#kmDbCap');
    bang('không cấp thêm', goiCua(g, 'vagabond.den_bu.cap_ma').length, 0);
  });

  await ca('màn tính tiền: hoá đơn đã chọn khách thì tấm mã hiện sẵn mã còn hạn của khách; bấm một mã là áp đúng mã đó', async function () {
    var g = khoi({ maKhach: [{ ma: 'SN2026', ten: 'Quà sinh nhật', han: '2026-11-30' }, { ma: 'DB7788', ten: 'Đền bù mức nhẹ', han: '2027-01-07' }] });
    vm.runInContext('posDon.khach_ma = "KH-1";', g);
    g.posSheetMaVc();
    await nghi();
    bang('hỏi đúng khách', goiCua(g, 'vagabond.khuyen_mai.ma_cua_khach').map(function (x) { return x.a.khach; }), ['KH-1']);
    var t = chu(tam(g));
    dung('hiện hai mã kèm hạn', t.indexOf('SN2026') >= 0 && t.indexOf('DB7788') >= 0 && t.indexOf('hạn 30/11/2026') >= 0);
    var nut = tam(g).querySelector('[data-vcma="DB7788"]');
    dung('nút mã cao 44', /min-height:44px/.test(nut.getAttribute('style')));
    tam(g).onclick({ target: nut });
    await nghi();
    bang('áp đúng mã vừa bấm', goiCua(g, 'vagabond.khuyen_mai.tra_ma').map(function (x) { return x.a.ma; }), ['DB7788']);
  });

  await ca('màn tính tiền: chưa chọn khách thì không hỏi máy chủ, tấm vẫn cho gõ mã như cũ', async function () {
    var g = khoi({ maKhach: [{ ma: 'SN2026', ten: 'Quà', han: '2026-11-30' }] });
    g.posSheetMaVc();
    await nghi();
    bang('không hỏi', goiCua(g, 'vagabond.khuyen_mai.ma_cua_khach').length, 0);
    dung('vẫn có ô gõ mã', !!tam(g).querySelector('#vcO'));
  });

  console.log('\n' + ket.dat + ' ca dat, ' + ket.hong + ' ca hong');
  if (ket.hong) { console.log(ket.loi.join('\n\n')); process.exit(1); }
})();

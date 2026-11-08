/* Ca kiem HANH VI v645 ban 2 (anh Viet 08/11/2026): cong tac uu dai don dau
 * tien tren web trong man Khuyen mai cua app, chon cho hien thi, chon co bat
 * ma Zalo hay khong, sua muc giam va tien banh toi thieu.
 *
 * CHAY THAT: nap nguyen 13-khuyen-mai.js (cung posChipNut that cua 09) vao DOM
 * gia, mo man Khuyen mai nhu quan ly, bam cong tac, mo tam, bam lua chon, go
 * so, bam Luu. May chu la ban gia ghi lai tung loi goi; phep lam sach va bao
 * loi so nam o may chu (don_dau_web.chuan, ca kiem thu_don_dau_cai_dat_645.py).
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/km_don_dau_645.js
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

var MAC = { bat: 1, giam: 50000, toi_thieu: 300000, can_otp: 1, hien_thanh_toan: 1, hien_uu_dai: 1 };

function khoi(o) {
  o = o || {};
  var goi = [], tin = [];
  var may = { cai_dat: Object.assign({}, MAC, o.cai_dat || {}), otp_mo: o.otp_mo == null ? 1 : o.otp_mo };
  var tai = domGia.taiLieuGia();
  var g = { console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array,
    Promise: Promise, Error: Error, RegExp: RegExp, parseInt: parseInt, setTimeout: function () { return 1; }, clearTimeout: function () {},
    document: tai, __goi: goi, __tin: tin, __may: may };
  g.__api = function (m, a) {
    goi.push({ m: m, a: JSON.parse(JSON.stringify(a || {})) });
    if (m === 'vagabond.khuyen_mai.ds_ctkm') return Promise.resolve({ km: [] });
    if (m === 'vagabond.khuyen_mai.ds_combo') return Promise.resolve({ combo: [] });
    if (m === 'vagabond.khuyen_mai.danh_muc') return Promise.resolve({});
    if (m === 'vagabond.don_dau_web.doc_cai_dat') {
      if (o.docLoi) return Promise.reject(new Error('mất mạng'));
      return Promise.resolve({ cai_dat: Object.assign({}, may.cai_dat), otp_mo: may.otp_mo });
    }
    if (m === 'vagabond.don_dau_web.luu_cai_dat') {
      if (o.luuLoi) return Promise.reject(new Error(o.luuLoi));
      var c = JSON.parse(a.cai_dat);
      /* May chu gia lam sach so giong ban that: bo dau cham. */
      ['giam', 'toi_thieu'].forEach(function (k) { c[k] = parseInt(String(c[k]).replace(/\D/g, ''), 10); });
      if (+c.can_otp) c.hien_thanh_toan = 1;
      may.cai_dat = c;
      return Promise.resolve({ cai_dat: c, otp_mo: may.otp_mo });
    }
    return Promise.reject(new Error('api la: ' + m));
  };
  g.window = g;
  vm.createContext(g);
  vm.runInContext([
    'var __stack = [];',
    'function frame(t, html, opt) { document.body.children = []; var vb = document.createElement("div"); vb.setAttribute("id", "vgbBody"); vb.innerHTML = html; document.body.appendChild(vb); return vb; }',
    'function go(fn) { __stack.push(fn); return fn(); } function toast(s) { __tin.push(String(s)); }',
    'function h(s) { return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;"); } function money(x) { return String(x); }',
    'function api(m, a) { return __api(m, a); }',
    layHam(fs.readFileSync(path.join(BEP, '09-tinh-tien-quay.js'), 'utf8'), 'posChipNut'),
  ].join('\n'), g);
  vm.runInContext(fs.readFileSync(path.join(BEP, '13-khuyen-mai.js'), 'utf8'), g);
  return g;
}
async function moMan(o) { var g = khoi(o); await g.go(g.scrKhuyenMai); await nghi(); return g; }
function than(g) { return g.document.getElementById('vgbBody'); }
async function bamMan(g, chon) { var b = than(g), el = b.querySelector(chon); if (!el) throw new Error('khong thay ' + chon); b.onclick({ target: el }); await nghi(); }
function tam(g) { var ds = g.document.body.children; return ds[ds.length - 1]; }
async function bamTam(g, chon) { var el = tam(g).querySelector(chon); if (!el) throw new Error('khong thay ' + chon); el.onclick(); await nghi(); }
function luuCuoi(g) { var ds = g.__goi.filter(function (x) { return x.m === 'vagabond.don_dau_web.luu_cai_dat'; }); return ds.length ? JSON.parse(ds[ds.length - 1].a.cai_dat) : null; }

(async function () {
  console.log('v645 ban 2: uu dai don dau tien tren web trong man Khuyen mai');

  await ca('màn Khuyến mãi có thẻ "Ưu đãi đơn đầu tiên trên web": tóm tắt đọc được, công tắc bật, nút chỉnh cao 44; chưa cài mẫu tin mã Zalo thì cảnh báo rõ', async function () {
    var g = await moMan();
    var the = than(g).querySelector('#kmDonDau');
    dung('có thẻ', !!the);
    var t = chu(the);
    dung('tóm tắt: ' + t, t.indexOf('Giảm 50.000 đ cho đơn bánh từ 300.000 đ') >= 0 && t.indexOf('mã Zalo') >= 0 && t.indexOf('bước thanh toán và trang Ưu đãi') >= 0);
    bang('công tắc', the.querySelector('[data-kmddbat]').getAttribute('aria-checked'), 'true');
    dung('nút chỉnh cao 44', /min-height:44px/.test(the.querySelector('#kmDdMo').getAttribute('style')));
    dung('không cảnh báo khi đã có mẫu tin', !than(g).querySelector('#kmDdCanhBao'));
    var g2 = await moMan({ otp_mo: 0 });
    dung('cảnh báo chưa cài mẫu tin', chu(than(g2).querySelector('#kmDdCanhBao')).indexOf('Chưa cài mẫu tin gửi mã Zalo') >= 0);
  });

  await ca('bấm công tắc: lưu bat 0, giữ nguyên các ô khác; màn vẽ lại ghi Đang tắt, công tắc tắt', async function () {
    var g = await moMan();
    await bamMan(g, '[data-kmddbat]');
    bang('gửi máy chủ', luuCuoi(g), Object.assign({}, MAC, { bat: 0 }));
    dung('báo đã tắt', g.__tin.some(function (x) { return x.indexOf('Đã tắt ưu đãi đơn đầu tiên') >= 0; }));
    dung('màn ghi Đang tắt', chu(than(g).querySelector('#kmDonDau')).indexOf('Đang tắt') >= 0);
    bang('công tắc tắt', than(g).querySelector('[data-kmddbat]').getAttribute('aria-checked'), 'false');
  });

  await ca('mở tấm chỉnh: gõ 40.000 và 250.000, chọn Không cần mã Zalo (ô số giữ chữ đã gõ), tắt Bước thanh toán, Lưu: gửi đúng lựa chọn, màn tóm tắt đổi theo', async function () {
    var g = await moMan();
    await bamMan(g, '#kmDdMo');
    var sh = tam(g);
    dung('tấm mở', chu(sh).indexOf('XÁC THỰC SỐ ĐIỆN THOẠI') >= 0 && chu(sh).indexOf('CHỖ HIỂN THỊ TRÊN WEB') >= 0);
    dung('đang bắt mã: thẻ thanh toán ghi luôn hiện', chu(sh.querySelector('[data-dd="hien_thanh_toan"]')).indexOf('Luôn hiện khi bắt mã Zalo') >= 0);
    sh.querySelector('#kmDdGiam').value = '40.000';
    sh.querySelector('#kmDdToi').value = '250.000';
    await bamTam(g, '[data-dd="otp0"]');
    bang('ô số giữ chữ đã gõ sau khi vẽ lại', [tam(g).querySelector('#kmDdGiam').value, tam(g).querySelector('#kmDdToi').value], ['40.000', '250.000']);
    bang('lựa chọn đang bật', tam(g).querySelector('[data-dd="otp0"]').getAttribute('aria-pressed'), 'true');
    await bamTam(g, '[data-dd="hien_thanh_toan"]');
    bang('thẻ thanh toán tắt', tam(g).querySelector('[data-dd="hien_thanh_toan"]').getAttribute('aria-pressed'), 'false');
    await bamTam(g, '#kmDdLuu');
    bang('gửi máy chủ', luuCuoi(g), { bat: 1, giam: '40.000', toi_thieu: '250.000', can_otp: 0, hien_thanh_toan: 0, hien_uu_dai: 1 });
    var t = chu(than(g).querySelector('#kmDonDau'));
    dung('màn đổi theo: ' + t, t.indexOf('Giảm 40.000 đ cho đơn bánh từ 250.000 đ') >= 0 && t.indexOf('không cần mã Zalo') >= 0 && t.indexOf('hiện ở trang Ưu đãi') >= 0);
  });

  await ca('đang bắt mã Zalo: bấm Bước thanh toán không tắt được và báo vì sao; chọn lại Bắt mã thì thẻ thanh toán tự bật lại', async function () {
    var g = await moMan({ cai_dat: { can_otp: 0, hien_thanh_toan: 0 } });
    await bamMan(g, '#kmDdMo');
    await bamTam(g, '[data-dd="otp1"]');
    bang('thẻ thanh toán bật lại', tam(g).querySelector('[data-dd="hien_thanh_toan"]').getAttribute('aria-pressed'), 'true');
    await bamTam(g, '[data-dd="hien_thanh_toan"]');
    bang('vẫn bật', tam(g).querySelector('[data-dd="hien_thanh_toan"]').getAttribute('aria-pressed'), 'true');
    dung('báo vì sao', g.__tin.some(function (x) { return x.indexOf('luôn hiện') >= 0; }));
  });

  await ca('máy chủ báo số sai: tấm vẫn mở, nút Lưu trở lại, báo đúng câu máy chủ; không có thay đổi nào', async function () {
    var g = await moMan({ luuLoi: 'Tiền bánh tối thiểu phải lớn hơn mức giảm, để đơn không bao giờ âm tiền.' });
    await bamMan(g, '#kmDdMo');
    tam(g).querySelector('#kmDdGiam').value = '400.000';
    await bamTam(g, '#kmDdLuu');
    dung('tấm còn mở', !!tam(g).querySelector('#kmDdLuu'));
    bang('nút', [tam(g).querySelector('#kmDdLuu').disabled, chu(tam(g).querySelector('#kmDdLuu'))], [false, 'Lưu']);
    bang('báo câu máy chủ', g.__tin[g.__tin.length - 1], 'Tiền bánh tối thiểu phải lớn hơn mức giảm, để đơn không bao giờ âm tiền.');
    bang('máy chủ giữ nguyên', g.__may.cai_dat, MAC);
  });

  await ca('đọc cài đặt lỗi: màn Khuyến mãi vẫn mở bình thường, chỉ không có thẻ đơn đầu', async function () {
    var g = await moMan({ docLoi: 1 });
    dung('không thẻ', !than(g).querySelector('#kmDonDau'));
    dung('màn vẫn có hàng chip', !!than(g).querySelector('[data-kmthe]'));
  });

  await ca('phép thuần: tóm tắt khi không chọn chỗ nào; cảnh báo chỉ khi đang bật, bắt mã và chưa cài mẫu tin', async function () {
    var g = khoi();
    dung('không chỗ nào', g.kmDonDauTom(Object.assign({}, MAC, { can_otp: 0, hien_thanh_toan: 0, hien_uu_dai: 0 })).indexOf('chỉ tự trừ tiền') >= 0);
    bang('cảnh báo', [!!g.kmDonDauCanhBao(MAC, 0), !!g.kmDonDauCanhBao(MAC, 1), !!g.kmDonDauCanhBao(Object.assign({}, MAC, { bat: 0 }), 0),
      !!g.kmDonDauCanhBao(Object.assign({}, MAC, { can_otp: 0 }), 0)], [true, false, false, false]);
  });

  ket.loi.forEach(function (l) { console.log('  HONG  ' + l); });
  console.log('\n' + ket.dat + ' ca dat, ' + ket.hong + ' ca hong');
  process.exit(ket.hong ? 1 : 0);
})();

/* Bo ca kiem HANH VI v582: mot nguoi giu NHIEU goi chuc vu, quyen cong don.
 *
 * Anh Viet chot 06/10/2026 (docs/quyen-theo-phan-he.md): De giu Quan ly cua
 * hang kem Quan ly nguoi dung. Hop "Doi goi chuc vu" truoc day chi chon duoc
 * MOT goi (hoiChon), bam vao la tra ve ngay. Nay doi sang hoiChonNhieu.
 *
 * Nap THAT 01-khung-app.js, 07-hop-thoai.js, 15-khuon-danh-sach.js va
 * 20-danh-muc-quyen.js; chi may chu la ban gia. Ca kiem chi bam nhu nguoi
 * dung (quy tac 15).
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/goi_nhieu_582.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var domGia = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }

var ket = { dat: 0, hong: 0, loi: [] };
var xongHet = false;
process.on('exit', function () {
  if (!xongHet) { console.log('  HONG  bo kiem dung giua chung: co loi hua treo mai'); process.exitCode = 1; }
});
function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; }
  catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 4).join('\n         ') : String(e))); }
}
async function nghi() { for (var i = 0; i < 12; i++) await Promise.resolve(); await new Promise(function (r) { setImmediate(r); }); }

var GOI = [
  { k: 'quay', ten: 'Quầy', icon: 'Q', mo_ta: 'q', so_nguoi: 8 },
  { k: 'sales', ten: 'Sales', icon: 'S', mo_ta: 's', so_nguoi: 7 },
  { k: 'qlch', ten: 'Quản lý cửa hàng', icon: 'C', mo_ta: 'c', so_nguoi: 2 },
  { k: 'ketoan', ten: 'Kế toán', icon: 'K', mo_ta: 'k', so_nguoi: 2 },
  { k: 'nhansu', ten: 'Quản lý người dùng', icon: 'N', mo_ta: 'n', so_nguoi: 1 },
];

function mayChu(chiTiet, dsGoi) {
  var goi = [];
  return {
    goi: goi,
    dem: function (m) { return goi.filter(function (x) { return x.m === m; }).length; },
    cuoi: function (m) { var r = goi.filter(function (x) { return x.m === m; }); return r[r.length - 1]; },
    api: async function (m, a) {
      goi.push({ m: m, a: JSON.parse(JSON.stringify(a || {})) });
      if (m === 'vagabond.nguoi_dung.chi_tiet') return chiTiet;
      if (m === 'vagabond.nguoi_dung.danh_sach_goi') return { goi: dsGoi || GOI };
      if (m === 'vagabond.nguoi_dung.dat_goi') return { ok: 1, loi_nhan: 'Đã xếp' };
      if (m === 'vagabond.nguoi_dung.moi') return { ok: 1, loi_nhan: 'Đã tạo' };
      throw new Error('may chu gia khong biet ' + m);
    },
  };
}

function appMoi(chiTiet, dsGoi) {
  var tl = domGia.taiLieuGia();
  var vgb = tl.createElement('div'); vgb.id = 'vgb'; tl.body.appendChild(vgb);
  var mc = mayChu(chiTiet, dsGoi);
  var tin = [], hoi = [], chu = [];
  var g = {
    console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array,
    Promise: Promise, Error: Error, RegExp: RegExp, parseFloat: parseFloat, parseInt: parseInt, isNaN: isNaN, Date: Date,
    encodeURIComponent: encodeURIComponent,
    document: tl,
    frappe: { session: { user: 'de@vgb' } },
    location: { href: 'https://app.x/bep', pathname: '/bep', hostname: 'app.x', search: '', hash: '', replace: function () {} },
    history: { pushState: function () {}, replaceState: function () {}, back: function () {} },
    requestAnimationFrame: function (f) { f(); },
    setTimeout: function (f) { f(); return 1; }, clearTimeout: function () {},
    S: { me: { full_name: 'Dễ' }, user: 'de@vgb' },
  };
  g.window = g;
  vm.createContext(g);
  vm.runInContext([
    'var root = document.getElementById("vgb");',
    'function h(s) { return String(s == null ? "" : s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;"); }',
    'function toast(s) { __tin.push("toast:" + s); }',
    'function busy() {}',
    'function dSkin() {}',
    'function hsNgayVn(x) { return String(x || ""); }',
    'function errMsg(e) { return String((e && e.message) || e); }',
    'function api(m, a) { return __mc.api(m, a); }',
    /* Ban that o 11-khach-ca-hop-dong.js, o tim cua hop chon dung no. */
    'function mvKhongDau(s) { s = String(s || "").toLowerCase(); try { s = s.normalize("NFD").replace(/[\\u0300-\\u036f]/g, ""); } catch (e) {} return s.replace(/đ/g, "d"); }',
  ].join('\n'), Object.assign(g, { __tin: tin, __mc: mc, __hoi: hoi }));
  vm.runInContext(require('./tim_chung.js'), g);
  vm.runInContext(doc('01-khung-app.js'), g);
  vm.runInContext(doc('07-hop-thoai.js'), g);
  vm.runInContext(doc('15-khuon-danh-sach.js'), g);
  vm.runInContext(doc('20-danh-muc-quyen.js'), g);
  vm.runInContext('go = function () { __tin.push("go"); };', g);
  /* Ba hop nhap chu va hop hoi co cua luong Moi: tra loi san theo thu tu. */
  vm.runInContext('hoiChu = function () { return Promise.resolve(__chu.shift()); };' +
    'hoiCo = function (t, m) { __hoi.push(t + "\\n" + m); return Promise.resolve(true); };' +
    'baoTin = function (m) { __tin.push("bao:" + m); return Promise.resolve(); };', Object.assign(g, { __chu: chu }));
  return {
    g: g, tl: tl, mc: mc, tin: tin, hoi: hoi, chu: chu,
    tim: function (chon) { return tl.body.querySelectorAll(chon); },
    mot: function (chon) { var r = tl.body.querySelectorAll(chon); if (r.length !== 1) throw new Error('mong dung 1 ' + chon + ', co ' + r.length); return r[0]; },
    bam: async function (el) { el.dispatchEvent(domGia.suKien('click', {}, el)); await nghi(); await nghi(); },
    dangChon: function () {
      return Array.prototype.filter.call(tl.body.querySelectorAll('[data-hcn]'), function (el) {
        var o = el.querySelector('[data-hcn-o]'); return o && String(o.textContent) === '✓';
      }).map(function (el) { return el.getAttribute('data-hcn'); });
    },
  };
}

var CT = {
  email: 'de@vgb', ten: 'Dễ', bat: 1, sdt: '', lan_cuoi: null, tao_luc: null,
  goi: 'nhansu', cac_goi: ['qlch', 'nhansu'], goi_ten: 'Quản lý người dùng + Quản lý cửa hàng',
  lam_duoc: ['a'], vai: ['Sales User'], vai_thua: [], la_toi: 0,
};

(async function () {
  await ca('Doi goi: hop mo san DUNG ca hai goi dang giu, bam muc khong dong hop', async function () {
    var app = appMoi(CT);
    await app.g.scrNguoiDungXem('de@vgb'); await nghi();
    await app.bam(app.mot('#qndDoiGoi'));
    bang('dang chon san hai goi', app.dangChon(), ['qlch', 'nhansu']);
    await app.bam(app.mot('[data-hcn="ketoan"]'));
    bang('bam them ke toan, hop van mo', app.dangChon(), ['qlch', 'ketoan', 'nhansu']);
    bang('chua goi dat_goi khi moi bam muc', app.mc.dem('vagabond.nguoi_dung.dat_goi'), 0);
  });

  await ca('Doi goi: bo mot goi, them mot goi, Luu gui DUNG danh sach theo thu tu goi', async function () {
    var app = appMoi(CT);
    await app.g.scrNguoiDungXem('de@vgb'); await nghi();
    await app.bam(app.mot('#qndDoiGoi'));
    await app.bam(app.mot('[data-hcn="nhansu"]'));
    await app.bam(app.mot('[data-hcn="ketoan"]'));
    await app.bam(app.mot('[data-hcn-xong]'));
    bang('goi dat_goi mot lan', app.mc.dem('vagabond.nguoi_dung.dat_goi'), 1);
    bang('tham so', app.mc.cuoi('vagabond.nguoi_dung.dat_goi').a, { email: 'de@vgb', goi: 'qlch,ketoan' });
    bang('hop da dong', app.tim('[data-hcn]').length, 0);
  });

  await ca('Doi goi: bo het moi goi thi nut Luu khong an, khong goi may chu', async function () {
    var app = appMoi(CT);
    await app.g.scrNguoiDungXem('de@vgb'); await nghi();
    await app.bam(app.mot('#qndDoiGoi'));
    await app.bam(app.mot('[data-hcn="qlch"]'));
    await app.bam(app.mot('[data-hcn="nhansu"]'));
    bang('khong con goi nao', app.dangChon(), []);
    await app.bam(app.mot('[data-hcn-xong]'));
    bang('hop van mo', app.tim('[data-hcn]').length, GOI.length);
    bang('khong goi dat_goi', app.mc.dem('vagabond.nguoi_dung.dat_goi'), 0);
  });

  await ca('Doi goi: bam Thoi thi khong goi may chu', async function () {
    var app = appMoi(CT);
    await app.g.scrNguoiDungXem('de@vgb'); await nghi();
    await app.bam(app.mot('#qndDoiGoi'));
    await app.bam(app.mot('[data-hcn="ketoan"]'));
    await app.bam(app.mot('[data-hcx]'));
    bang('khong goi dat_goi', app.mc.dem('vagabond.nguoi_dung.dat_goi'), 0);
  });

  await ca('Doi goi: may chu cu chi tra goi (chua co cac_goi) thi van chon san goi do', async function () {
    var ct = Object.assign({}, CT, { goi: 'sales' }); delete ct.cac_goi;
    var app = appMoi(ct);
    await app.g.scrNguoiDungXem('de@vgb'); await nghi();
    await app.bam(app.mot('#qndDoiGoi'));
    bang('chon san sales', app.dangChon(), ['sales']);
  });

  await ca('Moi tai khoan: chon hai goi, hop xac nhan ghi ca hai, may chu nhan ca hai', async function () {
    var app = appMoi(CT);
    app.chu.push('Nguyễn Văn A', 'a@x.vn', '');
    var p = app.g.qndMoi(); await nghi(); await nghi();
    await app.bam(app.mot('[data-hcn="sales"]'));
    await app.bam(app.mot('[data-hcn="nhansu"]'));
    await app.bam(app.mot('[data-hcn-xong]'));
    await p;
    dung('hop xac nhan ghi hai goi: ' + app.hoi[0], app.hoi.length === 1 && app.hoi[0].indexOf('Gói: Sales + Quản lý người dùng') >= 0);
    bang('moi nhan goi', app.mc.cuoi('vagabond.nguoi_dung.moi').a.goi, 'sales,nhansu');
  });

  /* Codex #449 P2: hop that co 13 goi, phai co o tim nhu hoiChon. */
  var GOI13 = ['quay', 'sales', 'qlch', 'bep', 'bepql', 'kho', 'shipper', 'marketing', 'muahang', 'ketoan', 'nhansu', 'giamdoc', 'chucongty']
    .map(function (k) { return { k: k, ten: k === 'kho' ? 'Kho' : 'Gói ' + k, icon: '', mo_ta: k === 'kho' ? 'Nhập xuất kho' : 'mô tả ' + k, so_nguoi: 1 }; });
  await ca('Codex #449 P2: hop 13 goi co o tim, go chu loc dung muc, chon muc da loc roi Luu', async function () {
    var app = appMoi(CT, GOI13);
    await app.g.scrNguoiDungXem('de@vgb'); await nghi();
    await app.bam(app.mot('#qndDoiGoi'));
    var o = app.mot('#hcnTim');
    o.value = 'nhập xuất';
    o.dispatchEvent(domGia.suKien('input', {}, o)); await nghi();
    var hien = Array.prototype.filter.call(app.tim('[data-hcn]'), function (el) { return el.style.display !== 'none'; })
      .map(function (el) { return el.getAttribute('data-hcn'); });
    bang('chi con Kho', hien, ['kho']);
    await app.bam(app.mot('[data-hcn="kho"]'));
    await app.bam(app.mot('[data-hcn-xong]'));
    bang('gui ca goi cu lan Kho', app.mc.cuoi('vagabond.nguoi_dung.dat_goi').a.goi, 'qlch,kho,nhansu');
  });

  await ca('Codex #449 P2: hop it muc (5 goi) khong ve o tim, giong hoiChon', async function () {
    var app = appMoi(CT);
    await app.g.scrNguoiDungXem('de@vgb'); await nghi();
    await app.bam(app.mot('#qndDoiGoi'));
    bang('khong co o tim', app.tim('#hcnTim').length, 0);
  });

  console.log('Bo ca kiem HANH VI v582: chon nhieu goi chuc vu');
  ket.loi.forEach(function (d) { console.log('  HONG  ' + d); });
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  xongHet = true;
  process.exit(ket.hong ? 1 : 0);
})();

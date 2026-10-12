/* Bo ca kiem HANH VI #456: khoi "Ten khach xuat hoa don" tren man Chi tiet
 * don Sales (scrDsView trong 08-doanh-so-sales.js) voi nguoi mua KHONG co
 * ma so thue Viet Nam (cong doan, truong, hoi, khach nuoc ngoai).
 *
 * CHAY THAT: khung app that (01-khung-app.js) va NGUYEN tep
 * 08-doanh-so-sales.js. May chu la ban gia; cac ham cua man khac ma
 * scrDsView goi toi (the thanh vien, hoan ung, kho...) la ban gia rong.
 * Ca kiem bam dung chuoi thao tac cua Sales: mo don, bam nut loai nguoi mua,
 * go ten, dia chi, ma so thue nuoc ngoai, bam Luu thong tin don; roi doc
 * dung tham so may chu nhan duoc. Khong goi them ham nao cua man.
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/xhd_khong_mst_456.js
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
function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; }
  catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 4).join('\n         ') : String(e))); }
}
async function nghi() { for (var i = 0; i < 12; i++) await Promise.resolve(); await new Promise(function (r) { setImmediate(r); }); }

/* ---------------- may chu gia ---------------- */
function mayChu(don) {
  var goi = [];
  return {
    goi: goi,
    cuoi: function (m) { for (var i = goi.length - 1; i >= 0; i--) if (goi[i].m === m) return goi[i]; return null; },
    api: function (m, a) {
      goi.push({ m: m, a: a });
      if (m === 'frappe.client.get') return Promise.resolve(don);
      if (m === 'vagabond.ban_hang.luu_xhd') return Promise.resolve({ ok: 1 });
      if (m === 'vagabond.ban_hang.luu_thanh_toan') return Promise.resolve({ ok: 1 });
      return Promise.resolve({});
    },
  };
}

function donMau(them) {
  return Object.assign({
    name: 'ACC-SINV-2026-00001', docstatus: 0, posting_date: '2026-10-08', custom_nguon: 'Pancake',
    custom_pancake_display_id: '91234', items: [{ item_name: 'Bánh', qty: 1, rate: 100000, price_list_rate: 100000, amount: 100000 }],
    grand_total: 100000, vgb_xhd_ten: '', vgb_xhd_mst: '', vgb_xhd_dia_chi: '', vgb_xhd_email: '',
  }, them || {});
}

/* Cac ham ngoai tep 08 ma scrDsView goi toi: ban gia rong, chi de man ve
   duoc toi khoi hoa don. Khong ham nao trong so nay dung toi khoi xhd. */
var GIA_RONG = ['khachTrenDon', 'khachMotDong', 'veKhachNo', 'dsvTaiHt', 'dsvVeHt', 'dsvKhoiHt', 'dsvVeQr', 'dsvVeThayThe',
  'dsvVeThu', 'dsvVeDiem', 'dsvVeTruDiem', 'dsvTheAnh', 'dsvHoiHt', 'dsvGanTruDiem', 'dsvGanHt', 'dsvChayDongHo', 'dsvTuPancake',
  'dsvnNapKhoiHd', 'dsvnKhoiHd', 'dsvOSo', 'dsvNapLai', 'dsvTaiThe', 'ttnVe', 'tkNapKhoi', 'tkKhoiChiTiet', 'sheetTimKhach',
  'promptSheet', 'posXinPhep', 'posTaiKhoan', 'posQrUrl', 'posNoiDungCk', 'hopKhung', 'hoanMoFormHuy', 'hoanMoFormDu', 'hoanMoForm',
  'hddtChoXuatChu', 'hdGanBind', 'hdAiLamGi', 'dstGanNganCach', 'dstDiemDs', 'dstSoThuan', 'dstNganCach', 'dsTayDoc', 'cfgBanHang',
  'ptTheoNguon', 'nguonBH', 'veOMtc', 'xacNhan', 'confirmSheet', 'dsvGanThe', 'veTruDiem'];

function appMoi(don) {
  var tl = domGia.taiLieuGia();
  var vgb = tl.createElement('div'); vgb.id = 'vgb'; tl.body.appendChild(vgb);
  var mc = mayChu(don);
  var tin = [];
  var g = {
    console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array,
    Promise: Promise, Error: Error, RegExp: RegExp, parseFloat: parseFloat, parseInt: parseInt, isNaN: isNaN, Date: Date,
    document: tl,
    frappe: { session: { user: 'sales@vagabond.vn' } },
    location: { href: 'https://app.x/bep', pathname: '/bep', hostname: 'app.x', search: '', hash: '', replace: function () {} },
    history: { pushState: function () {}, replaceState: function () {}, back: function () {} },
    requestAnimationFrame: function (f) { f(); },
    setTimeout: function () { return 1; }, clearTimeout: function () {}, setInterval: function () { return 1; }, clearInterval: function () {},
  };
  g.window = g;
  vm.createContext(g);
  vm.runInContext([
    'var root = document.getElementById("vgb");',
    'function h(s) { return String(s == null ? "" : s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;"); }',
    'function toast(s) { __tin.push("toast:" + s); }',
    'function busy() {}',
    'function baoTin(s) { __tin.push("baoTin:" + s); return Promise.resolve(); }',
    'function dSkin() {}',
    'function money(x) { return String(x); }',
    'function num(x) { return Number(x) || 0; }',
    'function today() { return "2026-10-08"; }',
    'function posNgayVn(x) { return x; }',
    'function hasRole() { return true; }',
    'function errMsg(e) { return String((e && e.message) || e); }',
    'function api(m, a) { return __mc.api(m, a); }',
    'var DSV_PT = "Tiền mặt", DS_MAU_HD = {}, KHACH_NO = {};',
    'var dsvKhach = { ma: "" };',
    'async function scrHome() { frame(APPNAME, "<div></div>"); }',
  ].concat(GIA_RONG.map(function (t) { return 'function ' + t + '() { return ""; }'; })).join('\n'),
  Object.assign(g, { __tin: tin, __mc: mc }));
  vm.runInContext(doc('01-khung-app.js'), g);
  vm.runInContext(doc('08-doanh-so-sales.js'), g);
  return {
    g: g, tl: tl, mc: mc, tin: tin,
    mot: function (chon) { var r = tl.body.querySelectorAll(chon); if (r.length !== 1) throw new Error('mong dung 1 ' + chon + ', co ' + r.length); return r[0]; },
    bam: async function (el) { el.dispatchEvent(domGia.suKien('click', {}, el)); await nghi(); await nghi(); },
    go: function (id, v) { tl.getElementById(id).value = v; },
  };
}
async function moDon(them) {
  var app = appMoi(donMau(them));
  await app.g.scrDsView('ACC-SINV-2026-00001'); await nghi(); await nghi();
  return app;
}
function hien(el) { return el.style.display !== 'none'; }

(async function () {
  await ca('Mở đơn mới: có ba nút loại người mua, mặc định Bán cho người tiêu dùng, form ẩn', async function () {
    var app = await moDon();
    dung('có nút ca_nhan', !!app.mot('[data-loai="ca_nhan"]'));
    dung('có nút cong_ty', !!app.mot('[data-loai="cong_ty"]'));
    dung('có nút khong_mst', !!app.mot('[data-loai="khong_mst"]'));
    dung('form ẩn', !hien(app.tl.getElementById('xhdForm')));
  });

  await ca('Bấm Không có MST Việt Nam: form hiện, ô MST Việt Nam ẩn, ô MST nước ngoài và lời dặn hiện', async function () {
    var app = await moDon();
    await app.bam(app.mot('[data-loai="khong_mst"]'));
    dung('form hiện', hien(app.tl.getElementById('xhdForm')));
    dung('ô MST VN ẩn', !hien(app.tl.getElementById('xhdMst')));
    dung('ô MST nước ngoài hiện', hien(app.tl.getElementById('xhdMstNN')));
    dung('lời dặn hiện', hien(app.tl.getElementById('xhdGhiNN')));
    await app.bam(app.mot('[data-loai="cong_ty"]'));
    dung('về công ty thì ô MST VN hiện lại', hien(app.tl.getElementById('xhdMst')));
    dung('ô MST nước ngoài ẩn', !hien(app.tl.getElementById('xhdMstNN')));
  });

  await ca('Công đoàn không MST: gõ tên và địa chỉ, bấm Lưu, máy chủ nhận tên, địa chỉ, MST rỗng (lỗi cũ: bị chặn phải có MST)', async function () {
    var app = await moDon();
    await app.bam(app.mot('[data-loai="khong_mst"]'));
    app.go('xhdTen', 'Công đoàn Công ty TNHH ABC');
    app.go('xhdDc', '12 Lê Lợi, Quận 1, TP HCM');
    await app.bam(app.tl.getElementById('xhdLuu'));
    var g = app.mc.cuoi('vagabond.ban_hang.luu_xhd');
    dung('máy chủ có nhận', !!g);
    bang('tên, mst, địa chỉ', [g.a.ten, g.a.mst, g.a.dia_chi], ['Công đoàn Công ty TNHH ABC', '', '12 Lê Lợi, Quận 1, TP HCM']);
    dung('báo đã lưu', app.tin.some(function (t) { return t.indexOf('toast:Đã lưu') === 0; }));
  });

  await ca('Khách nước ngoài có mã số thuế nước ngoài: mã ghi kèm sau tên, MST Việt Nam rỗng, địa chỉ đúng như khách đưa', async function () {
    var app = await moDon();
    await app.bam(app.mot('[data-loai="khong_mst"]'));
    app.go('xhdTen', 'ACME PTE. LTD.');
    app.go('xhdMstNN', ' 201912345K ');
    app.go('xhdDc', '10 Anson Road, #10-01, Singapore 079903');
    await app.bam(app.tl.getElementById('xhdLuu'));
    var g = app.mc.cuoi('vagabond.ban_hang.luu_xhd');
    bang('tên kèm MST nước ngoài', g.a.ten, 'ACME PTE. LTD. (MST nước ngoài: 201912345K)');
    bang('mst VN rỗng', g.a.mst, '');
    bang('địa chỉ nguyên văn', g.a.dia_chi, '10 Anson Road, #10-01, Singapore 079903');
  });

  await ca('Không MST mà thiếu địa chỉ thì chặn ngay trên màn, máy chủ không nhận gì', async function () {
    var app = await moDon();
    await app.bam(app.mot('[data-loai="khong_mst"]'));
    app.go('xhdTen', 'Hội Phụ nữ Phường 5');
    await app.bam(app.tl.getElementById('xhdLuu'));
    dung('không gọi luu_xhd', !app.mc.cuoi('vagabond.ban_hang.luu_xhd'));
    dung('có lời báo thiếu địa chỉ', app.tin.some(function (t) { return t.indexOf('baoTin:') === 0 && t.indexOf('địa chỉ') >= 0; }));
  });

  await ca('Công ty / HKD vẫn bắt buộc MST như cũ, và lời báo chỉ sang nút Không có MST', async function () {
    var app = await moDon();
    await app.bam(app.mot('[data-loai="cong_ty"]'));
    app.go('xhdTen', 'Công ty TNHH ABC');
    await app.bam(app.tl.getElementById('xhdLuu'));
    dung('không gọi luu_xhd', !app.mc.cuoi('vagabond.ban_hang.luu_xhd'));
    dung('lời báo chỉ sang nút mới', app.tin.some(function (t) { return t.indexOf('Không có MST Việt Nam') >= 0; }));
  });

  await ca('Mở lại đơn đã lưu tên kèm MST nước ngoài: tự chọn nút Không có MST, tách lại tên và mã vào đúng ô', async function () {
    var app = await moDon({ vgb_xhd_ten: 'ACME PTE. LTD. (MST nước ngoài: 201912345K)', vgb_xhd_dia_chi: 'Singapore' });
    dung('form hiện', hien(app.tl.getElementById('xhdForm')));
    dung('ô MST nước ngoài hiện', hien(app.tl.getElementById('xhdMstNN')));
    bang('tên tách', app.tl.getElementById('xhdTen').value, 'ACME PTE. LTD.');
    bang('mã tách', app.tl.getElementById('xhdMstNN').value, '201912345K');
    /* Luu lai khong go gi them: ten ghep ve y nhu cu, khong nhan doi phan mo ngoac. */
    await app.bam(app.tl.getElementById('xhdLuu'));
    bang('ghép lại y cũ', app.mc.cuoi('vagabond.ban_hang.luu_xhd').a.ten, 'ACME PTE. LTD. (MST nước ngoài: 201912345K)');
  });

  await ca('Codex #458: ba nút loại người mua cao tối thiểu 44 điểm (AGENTS 2b.13)', async function () {
    var app = await moDon();
    ['ca_nhan', 'cong_ty', 'khong_mst'].forEach(function (k) {
      var st = app.mot('[data-loai="' + k + '"]').getAttribute('style') || '';
      dung('nút ' + k + ' có min-height:44px', /min-height:\s*44px/.test(st));
    });
  });

  await ca('Mở lại đơn công ty có MST: vẫn vào nút Công ty / HKD như cũ', async function () {
    var app = await moDon({ vgb_xhd_ten: 'Công ty TNHH ABC', vgb_xhd_mst: '0311638525' });
    dung('ô MST VN hiện', hien(app.tl.getElementById('xhdMst')));
    dung('ô MST nước ngoài ẩn', !hien(app.tl.getElementById('xhdMstNN')));
  });

  console.log(ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng, tổng ' + (ket.dat + ket.hong) + ' ca.');
  if (ket.hong) { console.log(ket.loi.join('\n')); process.exit(1); }
})();

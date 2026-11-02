/* Ca kiểm HÀNH VI v630: màn "Đơn sỉ web" và "Khách sỉ web" (bánh sỉ) trên app.
 *
 * Nạp THẬT 64-banh-si.js cùng các hàm nền nó gọi (h, money, anhMon, sheet,
 * confirmSheet, promptSheet, dsCongCu, posChipNut, kmHangChip...) vào DOM giả;
 * máy chủ giả trả đúng hình dạng của banh_si.ds_don, xem_don, ds_dang_ky,
 * ds_khach, bang_gia. Mỗi ca bấm đúng chuỗi thao tác của Sales, kho, bếp,
 * kế toán.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/banh_si_app_630.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
var NEN = doc('00-nen.js'), POS = doc('09-tinh-tien-quay.js'), KHUON = doc('15-khuon-danh-sach.js');
var KM = doc('13-khuyen-mai.js'), KHO = doc('03-kho-chung-tu.js');
var MAN = doc('64-banh-si.js');

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
var HAM = ['h', 'money', 'today', 'vgbChuan', 'vgbKhop', 'anhMon', 'sheet', 'confirmSheet', 'promptSheet'].map(function (t) { return layHam(NEN, t); })
  .concat([layHam(POS, 'posChipNut')])
  .concat(['dsccHang', 'dsCongCu', 'dsCongCuNoi', 'dsKhoangToi', 'dsTrongKhoangToi', 'dsDemTheo', 'dsDemKhoangToi', 'dsNhanGon'].map(function (t) { return layHam(KHUON, t); }))
  .concat(['var scanBarcode = function () { return Promise.resolve(null); };'])
  .concat([layHam(KM, 'kmHangChip'), layHam(KHO, 'errMsg')]).join('\n');

var HOM = '2026-11-05';
function dong(ma, sl, gia) { return { ma: ma, ten: 'Bánh ' + ma, sl: sl, gia: gia, tien: sl * gia, anh: '' }; }
function don(ten, ma, tt, nhan, ngay, traTruoc, con, phieu) {
  var d = [dong('BANU00001', 30, 28000), dong('BANU00002', 20, 32000)];
  return { name: ten, ma: ma, trang_thai: tt, nhan: nhan, khach: 'Café Lá Me', ma_khach: 'SI00012', ngay: ngay, dat_luc: '2026-11-02 09:30',
    tra_truoc: traTruoc, cach_tra: traTruoc ? 'Trả trước' : 'Công nợ', tong: 1480000, chua_vat: 1370370, vat: 109630, con_lai: con,
    so_cai: 50, dong: d, ghi_chu: '', hoa_don: tt === 'da_giao' ? 'HDB-26-11-00009' : '', han_no: tt === 'da_giao' && !traTruoc ? '2026-11-20' : '',
    phieu: phieu || [] };
}
var DON = {
  'SO-1': don('SO-1', 'BSI26110001', 'cho_giao', 'Chờ giao', HOM, 0, 0),
  'SO-2': don('SO-2', 'BSI26110002', 'cho_tt', 'Chờ chuyển khoản', '2026-11-06', 1, 1480000),
  'SO-3': don('SO-3', 'BSI26110003', 'cho_giao', 'Chờ giao', '2026-11-06', 1, 0, [{ name: 'PE-B', so_tien: 1480000, docstatus: 0, ngay: '2026-11-03' }]),
  'SO-4': don('SO-4', 'BSI26110004', 'da_giao', 'Đã giao', '2026-11-04', 0, 0),
};
var TT = [{ k: 'cho_tt', ten: 'Chờ chuyển khoản' }, { k: 'cho_giao', ten: 'Chờ giao' }, { k: 'da_giao', ten: 'Đã giao' }, { k: 'da_huy', ten: 'Đã huỷ' }];
var KHO_DS = [{ ma: 'Kho Sỉ - VGB', ten: 'Kho Sỉ' }, { ma: 'Kho TCV - VGB', ten: 'Kho TCV' }];
var DK = [{ name: 'dk1', ten_quan: 'Café Lá Me', mst: '0312345678', sdt: '0909123456', loai_hinh: 'Quán cà phê', luong_tuan: '50 - 200 cái',
  trang_thai: 'Chờ duyệt', khach: '', ten_khach: '', xu_ly: '', luc: '2026-11-02 08:00' }];
var KE_TOAN = 0, CO_TIEN = 1, TRA = {}, LOI = {};

function anTien(r) {
  r = JSON.parse(JSON.stringify(r));
  ['tong', 'chua_vat', 'vat', 'con_lai'].forEach(function (k) { r[k] = null; });
  r.phieu = []; r.dong.forEach(function (d) { d.gia = null; d.tien = null; });
  return r;
}

function dungMoi(vai) {
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);
  var goi = [], toastDs = [], dieuHuong = [], kho = {};
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, Number: Number, Date: Date, setTimeout: setTimeout, clearTimeout: clearTimeout, isNaN: isNaN, encodeURIComponent: encodeURIComponent,
    localStorage: { getItem: function (k) { return kho[k] || null; }, setItem: function (k, v) { kho[k] = String(v); } },
    FileReader: function () { var fr = this; this.readAsDataURL = function (f) { fr.result = 'data:image/png;base64,' + f.noiDung; setTimeout(function () { fr.onload(); }, 0); }; },
    S: { roles: vai, stack: [] },
    hasRole: function (r) { return vai.indexOf(r) >= 0; },
    frame: function (t, html, opt) {
      khung.innerHTML = html + (opt && opt.footer ? '<div class="vf">' + opt.footer + '</div>' : ''); khung._nghe = {}; khung.onclick = null; that._t = t; return khung;
    },
    go: function (fn) { dieuHuong.push(fn.name || 'anDanh'); return fn(); },
    busy: function () {},
    toast: function (m) { toastDs.push(m); },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: ts });
      if (LOI[duong]) return Promise.reject(new Error(LOI[duong]));
      if (duong === 'vagabond.banh_si.ds_don') {
        var rows = Object.keys(DON).map(function (k) { return CO_TIEN ? DON[k] : anTien(DON[k]); });
        var dem = {}; rows.forEach(function (r) { dem[r.trang_thai] = (dem[r.trang_thai] || 0) + 1; });
        return Promise.resolve({ rows: rows, dem: dem, hom_nay: HOM, trang_thai: TT, co_tien: CO_TIEN, kho: CO_TIEN ? KHO_DS : [], la_ke_toan: KE_TOAN });
      }
      if (duong === 'vagabond.banh_si.xem_don') {
        var r = JSON.parse(JSON.stringify(DON[ts.name]));
        if (!CO_TIEN) return Promise.resolve(anTien(r));
        r.kho = KHO_DS; r.la_ke_toan = KE_TOAN;
        r.qr = r.trang_thai === 'cho_tt' ? { anh: 'data:image/svg+xml;base64,QR', ngan_hang: 'MB', stk: '0931224334', noi_dung: r.ma } : null;
        r.loi_giao = r.phieu.some(function (p) { return p.docstatus === 0; }) ? 'Phiếu thu PE-B chờ kế toán ghi sổ' : '';
        return Promise.resolve(r);
      }
      if (duong === 'vagabond.banh_si.ds_dang_ky') return Promise.resolve({ rows: DK, dem: { 'Chờ duyệt': 1, 'Đã duyệt': 3, 'Từ chối': 0 }, trang_thai: ['Chờ duyệt', 'Đã duyệt', 'Từ chối'] });
      if (duong === 'vagabond.banh_si.ds_khach') return Promise.resolve({ rows: [{ name: 'SI00012', customer_name: 'Café Lá Me', vgb_si_sdt: '0909123456', vgb_si_cuoi_ky: 1, so_mon: 2 },
        { name: 'SI00013', customer_name: 'Hotel Sen', vgb_si_sdt: '0911000111', vgb_si_cuoi_ky: 0, so_mon: 0 }] });
      if (duong === 'vagabond.banh_si.tim_khach') return Promise.resolve([{ name: 'SI00020', customer_name: 'Công ty Lá Me', tax_id: '0312345678', customer_group: 'Khách sỉ B2B' }]);
      if (duong === 'vagabond.banh_si.bang_gia') return Promise.resolve({ khach: { name: 'SI00012', customer_name: 'Café Lá Me', vgb_si_web: 1, vgb_si_cuoi_ky: 0, vgb_si_sdt: '0909123456' },
        gia: [{ ma: 'BANU00001', ten: 'Croissant bơ', gia: 28000, anh: '', dvt: 'Cái' }],
        goi_y: [{ ma: 'BANU00002', ten: 'Pain au chocolat', gia: 31000, ngay: '2026-10-20', hoa_don: 'HD-5', tu_ma: 'BAWS00011', anh: '', dvt: 'Cái' }] });
      if (duong === 'vagabond.banh_si.tim_mon') return Promise.resolve([{ name: 'BANU00007', item_name: 'Tart trứng', image: '', stock_uom: 'Cái', item_group: 'Tart' }]);
      return Promise.resolve(TRA[duong] || { ok: 1 });
    },
  };
  that.window = that;
  vm.runInNewContext(HAM, that, { filename: 'ham-nen.js' });
  vm.runInNewContext(MAN, that, { filename: '64-banh-si.js' });
  return { g: that, tai: tai, khung: khung, goi: goi, toast: toastDs, dieuHuong: dieuHuong, kho: kho };
}

var ket = { dat: 0, hong: 0 };
function dung(mo, dk) { if (!dk) throw new Error(mo); }
function bang(mo, a, b) { var x = JSON.stringify(a), y = JSON.stringify(b); if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y); }
function tick() { return new Promise(function (r) { setTimeout(r, 5); }); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); }
}
function chu(el) { var s = el._chu || ''; (el.children || []).forEach(function (c) { s += chu(c); }); return s; }
function sheet(m) { var ds = m.tai.body.children; return ds.length > 1 ? ds[ds.length - 1] : null; }
function bam(el) { if (!el) throw new Error('khong co nut de bam'); el.dispatchEvent(dg.suKien('click', {}, el)); }
function q(el, chon) { return el.querySelectorAll(chon)[0]; }
function goiTen(m, t) { return m.goi.filter(function (x) { return x.duong === 'vagabond.banh_si.' + t; }); }

async function moDs(vai) {
  var m = dungMoi(vai || ['Sales User']);
  vm.runInNewContext('bsiTt = ""; bsiTim = ""; bsiMo = ""; if (typeof bsiKhach !== "undefined") { bsiKhach = ""; bsiNgay = ""; }', m.g);
  await m.g.scrDonSiWeb(); await tick();
  return m;
}
async function moCt(ten, vai) {
  var m = dungMoi(vai || ['Sales User']);
  vm.runInNewContext('bsiMo = "' + ten + '";', m.g);
  await m.g.scrDonSiWebCt(); await tick();
  return m;
}
async function moKh(vai, tab) {
  var m = dungMoi(vai || ['Sales User']);
  vm.runInNewContext('bsiKhTab = "' + (tab || 'dk') + '"; bsiDkTt = "Chờ duyệt"; bsiKhTim = ""; bsiKhMo = "";', m.g);
  await m.g.scrKhachSiWeb(); await tick();
  return m;
}
async function moGia() {
  var m = dungMoi(['Sales User']);
  vm.runInNewContext('bsiKhMo = "SI00012";', m.g);
  await m.g.scrGiaSi(); await tick();
  return m;
}

(async function () {
  console.log('v630 Bánh sỉ: hai màn app thật trên DOM giả');

  await ca('không có vai: Đơn sỉ web và Khách sỉ web không gọi máy chủ, câu nói ai được mở', async function () {
    var m = await moDs(['Bộ phận đặt hàng']);
    dung('khoá đơn', chu(m.khung).indexOf('Màn này mở cho Sales') >= 0);
    var k = await moKh(['VGB - Quản lý cửa hàng']);
    dung('khoá khách sỉ: quản lý cửa hàng không duyệt giá', chu(k.khung).indexOf('Màn này mở cho Sales và giám đốc') >= 0);
    bang('không gọi máy chủ', m.goi.length + k.goi.length, 0);
  });

  await ca('danh sách: thẻ tóm tắt đếm đơn chưa giao và số cái, nhóm theo ngày giao, chip lọc Chờ chuyển khoản', async function () {
    var m = await moDs();
    dung('tóm tắt', chu(q(m.khung, '[data-bsitom]')).indexOf('3 đơn · 150 cái') >= 0);
    dung('nhãn hôm nay', chu(m.khung).indexOf('HÔM NAY · THỨ NĂM 05/11') >= 0);
    bang('bốn thẻ', m.khung.querySelectorAll('[data-bsithe]').length, 4);
    dung('thẻ trả trước nói số chờ', chu(q(m.khung, '[data-bsithe="SO-2"]')).indexOf('Chờ 1.480.000đ') >= 0);
    dung('thẻ có phiếu nháp nhắc kế toán', chu(q(m.khung, '[data-bsithe="SO-3"]')).indexOf('1 phiếu chuyển khoản chờ kế toán ghi sổ') >= 0);
    bam(q(m.khung, '[data-bsiso="cho_tt"]')); await tick();
    bang('lọc', m.khung.querySelectorAll('[data-bsithe]').map(function (x) { return x.getAttribute('data-bsithe'); }), ['SO-2']);
  });

  /* Codex #531 vòng 3 (AGENTS 2b.3): ba hàng chip trạng thái, khách, khoảng ngày
     giao; lọc áp cả danh sách lẫn thẻ tóm tắt; "Mọi ngày" mở rộng lại. */
  function chipLoc(m, ho, k) {
    return m.khung.querySelectorAll('[data-dscc]').filter(function (x) { return x.getAttribute('data-dscc') === ho + '|' + k; })[0];
  }
  function theDs(m) { return m.khung.querySelectorAll('[data-bsithe]').map(function (x) { return x.getAttribute('data-bsithe'); }); }
  await ca('Codex #531 v3: hàng chip khách và khoảng ngày giao, bấm lọc thật áp cả danh sách lẫn thẻ tóm tắt; Mọi ngày mở rộng lại', async function () {
    var cu = DON['SO-2'].khach;
    DON['SO-2'].khach = 'Khách sạn Sông Sài Gòn';
    try {
      var m = await moDs();
      dung('có chip khách', chipLoc(m, 'khach', 'Khách sạn Sông Sài Gòn') && chipLoc(m, 'khach', 'Café Lá Me'));
      dung('có chip mở rộng Mọi ngày', chipLoc(m, 'ngay', '') && chu(chipLoc(m, 'ngay', '')).indexOf('Mọi ngày') >= 0);
      bam(chipLoc(m, 'ngay', 'ngay_mai')); await tick();
      bang('giao ngày mai', theDs(m), ['SO-2', 'SO-3']);
      dung('tóm tắt theo bộ lọc', chu(q(m.khung, '[data-bsitom]')).indexOf('2 đơn · 100 cái') >= 0);
      dung('ô Chờ giao đếm theo bộ lọc', chu(q(m.khung, '[data-bsiso="cho_giao"]')).indexOf('1 đơn') >= 0);
      bam(chipLoc(m, 'khach', 'Khách sạn Sông Sài Gòn')); await tick();
      bang('khách và ngày cùng áp', theDs(m), ['SO-2']);
      dung('tóm tắt khách', chu(q(m.khung, '[data-bsitom]')).indexOf('1 đơn · 50 cái') >= 0);
      bam(chipLoc(m, 'ngay', '')); await tick();
      bam(chipLoc(m, 'khach', '')); await tick();
      bang('Mọi ngày, Mọi khách mở rộng lại', theDs(m).length, 4);
      bam(chipLoc(m, 'ngay', 'da_qua')); await tick();
      bang('đã qua', theDs(m), ['SO-4']);
    } finally { DON['SO-2'].khach = cu; }
  });

  await ca('bếp: thấy món và số lượng theo ngày giao, không thấy tiền, không có nút giao', async function () {
    CO_TIEN = 0;
    try {
      var m = await moDs(['Manufacturing User']);
      dung('không chữ đ tiền', !/[0-9]đ/.test(chu(m.khung)));
      dung('có số cái', chu(q(m.khung, '[data-bsithe="SO-1"]')).indexOf('50 cái') >= 0);
      var c = await moCt('SO-1', ['Manufacturing User']);
      bang('không nút đáy', c.g.document.getElementById('bsiChinh'), null);
      dung('dòng món có số lượng', chu(q(c.khung, '[data-bsidong="BANU00001"]')).indexOf('30') >= 0);
      dung('dòng món không giá', chu(q(c.khung, '[data-bsidong="BANU00001"]')).indexOf('28.000') < 0);
    } finally { CO_TIEN = 1; }
  });

  await ca('công nợ chờ giao: nút đáy Giao hàng; thiếu kho thì nhắc, chọn kho thì gửi đúng kho, người nhận, và nhớ kho', async function () {
    var m = await moCt('SO-1');
    var nut = m.g.document.getElementById('bsiChinh');
    dung('nút giao', chu(nut).indexOf('Giao hàng và xuất hoá đơn') >= 0);
    dung('chi tiết nói cuối kỳ', chu(m.khung).indexOf('Cuối kỳ 15 ngày') >= 0);
    bam(nut);
    var s = sheet(m);
    dung('sheet nói công nợ hạn 15', chu(s).indexOf('Công nợ, hạn trả 15 ngày') >= 0);
    bam(q(s, '[data-bsigiaook]')); await tick();
    dung('nhắc chọn kho', m.toast.join('|').indexOf('Chọn kho') >= 0);
    bang('chưa gọi', goiTen(m, 'giao_hang').length, 0);
    bam(q(s, '[data-bsichonkho]'));
    var ds = sheet(m);
    bam(q(ds, '.shi'));
    q(s, '#bsiNguoiNhan').value = 'chị Lan';
    bam(q(s, '[data-bsigiaook]')); await tick();
    bang('gọi giao', goiTen(m, 'giao_hang').map(function (x) { return x.ts; }), [{ name: 'SO-1', kho: 'Kho Sỉ - VGB', nguoi_nhan: 'chị Lan' }]);
    bang('nhớ kho', m.kho.vgb_bsi_kho, 'Kho Sỉ - VGB');
  });

  await ca('giao hỏng ở máy chủ: câu máy chủ hiện ra, sheet còn, nút bấm lại được', async function () {
    var m = await moCt('SO-1');
    m.kho.vgb_bsi_kho = 'Kho TCV - VGB';
    LOI['vagabond.banh_si.giao_hang'] = 'Số lượng xuất vượt quá tồn kho: BANU00001 (tồn 10, xuất 30)';
    try {
      bam(m.g.document.getElementById('bsiChinh'));
      var s = sheet(m), ok = q(s, '[data-bsigiaook]');
      bam(ok); await tick();
      dung('câu tồn', m.toast.join('|').indexOf('vượt quá tồn kho') >= 0);
      dung('sheet còn', m.tai.body.children.indexOf(s) >= 0);
      dung('bấm lại được', !ok.disabled);
      bang('kho nhớ dùng ngay', goiTen(m, 'giao_hang')[0].ts.kho, 'Kho TCV - VGB');
    } finally { delete LOI['vagabond.banh_si.giao_hang']; }
  });

  await ca('trả trước chờ chuyển khoản: nút đáy mở QR mã đơn; kiểm tiền về chưa thấy thì nói chờ, thấy thì báo lập phiếu', async function () {
    var m = await moCt('SO-2');
    var nut = m.g.document.getElementById('bsiChinh');
    dung('nút chờ', chu(nut).indexOf('Chờ chuyển khoản 1.480.000đ') >= 0);
    bam(nut);
    var s = sheet(m);
    dung('QR', q(s, 'img').getAttribute('src').indexOf('data:image/svg') === 0);
    dung('nội dung mã đơn', chu(s).indexOf('BSI26110002') >= 0);
    TRA['vagabond.banh_si.kiem_tien_ve'] = { ok: 1, lap: 0 };
    bam(q(s, '[data-bsikiem]')); await tick();
    dung('chưa thấy', m.toast.join('|').indexOf('Chưa thấy tiền về') >= 0);
    TRA['vagabond.banh_si.kiem_tien_ve'] = { ok: 1, lap: 1 };
    bam(q(s, '[data-bsikiem]')); await tick();
    dung('đã thấy', m.toast.join('|').indexOf('máy lập phiếu thu chờ kế toán ghi sổ') >= 0);
    delete TRA['vagabond.banh_si.kiem_tien_ve'];
  });

  await ca('trả trước còn phiếu nháp: nút giao khoá; Sales không thấy ô ghi sổ, kế toán đính ảnh và ghi sổ đúng phiếu', async function () {
    var m = await moCt('SO-3');
    var nut = m.g.document.getElementById('bsiChinh');
    dung('khoá', nut.hasAttribute('disabled') && chu(nut).indexOf('Chờ kế toán') >= 0);
    bang('Sales không có ô ghi sổ', m.khung.querySelectorAll('[data-bsighiso]').length, 0);
    KE_TOAN = 1;
    try {
      var k = await moCt('SO-3', ['Accounts User']);
      var o = q(k.khung, '[data-bsighiso]');
      o.files = [{ name: 'giay-bao-co.png', noiDung: 'AAA' }];
      o.dispatchEvent(dg.suKien('change', {}, o));
      await tick(); await tick();
      bang('ghi sổ', goiTen(k, 'ghi_so_phieu').map(function (x) { return [x.ts.name, x.ts.phieu, JSON.parse(x.ts.anh)[0].ten]; }), [['SO-3', 'PE-B', 'giay-bao-co.png']]);
    } finally { KE_TOAN = 0; }
  });

  await ca('huỷ: chỉ đơn chưa giao, chưa có tiền; lý do ngắn bị nhắc, đủ thì gửi; đơn có phiếu hay đã giao không có nút huỷ', async function () {
    var m = await moCt('SO-1');
    bam(q(m.khung, '[data-bsihuy]'));
    var s = sheet(m);
    q(s, '#bsiLyDo').value = 'abc';
    bam(q(s, '[data-bsihuyok]')); await tick();
    bang('ngắn không gửi', goiTen(m, 'huy_don').length, 0);
    q(s, '#bsiLyDo').value = 'Khách báo đổi ngày giao';
    bam(q(s, '[data-bsihuyok]')); await tick();
    bang('gửi', goiTen(m, 'huy_don').map(function (x) { return x.ts; }), [{ name: 'SO-1', ly_do: 'Khách báo đổi ngày giao' }]);
    var a = await moCt('SO-3');
    bang('có phiếu không huỷ', a.khung.querySelectorAll('[data-bsihuy]').length, 0);
    var b = await moCt('SO-4');
    bang('đã giao không huỷ', b.khung.querySelectorAll('[data-bsihuy]').length, 0);
    dung('đã giao hiện hoá đơn và hạn', chu(b.khung).indexOf('HDB-26-11-00009') >= 0 && chu(b.khung).indexOf('hạn trả 20/11') >= 0);
  });

  await ca('duyệt đăng ký, tạo khách mới: tên điền sẵn, bật trả cuối kỳ, gửi đúng gói rồi mở màn giá riêng của khách vừa tạo', async function () {
    var m = await moKh();
    dung('chip đếm chờ', chu(q(m.khung, '[data-dscc="tab|dk"]')).indexOf('Đăng ký chờ duyệt 1') >= 0);
    bam(q(m.khung, '[data-bsidk="dk1"]'));
    var s = sheet(m);
    bang('tên điền sẵn', q(s, '#bsiTenMoi').value, 'Café Lá Me');
    bam(q(s, '[data-bsict="ky"]'));
    TRA['vagabond.banh_si.duyet'] = { ok: 1, khach: 'SI00030' };
    bam(q(s, '[data-bsiduyetok]')); await tick(); await tick();
    bang('gói duyệt', goiTen(m, 'duyet').map(function (x) { return x.ts; }), [{ name: 'dk1', dat_web: 1, cuoi_ky: 1, ten_khach: 'Café Lá Me' }]);
    bang('mở bảng giá khách mới', goiTen(m, 'bang_gia').map(function (x) { return x.ts.khach; }), ['SI00030']);
    delete TRA['vagabond.banh_si.duyet'];
  });

  await ca('duyệt gắn khách có sẵn: chưa chọn thì nhắc; tìm và chọn thì gửi mã khách, không gửi tên mới', async function () {
    var m = await moKh();
    bam(q(m.khung, '[data-bsidk="dk1"]'));
    var s = sheet(m);
    bam(q(s, '[data-bsicach="co"]'));
    bam(q(s, '[data-bsiduyetok]')); await tick();
    dung('nhắc chọn', m.toast.join('|').indexOf('Chọn khách có sẵn') >= 0);
    bam(q(s, '[data-bsichonkh]')); await tick();
    var t = sheet(m);
    bam(q(t, '[data-bsikhchon="SI00020"]'));
    TRA['vagabond.banh_si.duyet'] = { ok: 1, khach: 'SI00020' };
    bam(q(s, '[data-bsiduyetok]')); await tick(); await tick();
    bang('gói', goiTen(m, 'duyet').map(function (x) { return x.ts; }), [{ name: 'dk1', dat_web: 1, cuoi_ky: 0, khach: 'SI00020' }]);
    delete TRA['vagabond.banh_si.duyet'];
  });

  await ca('từ chối cần lý do; khách đang đặt hiện cuối kỳ và nhắc khách chưa có giá riêng', async function () {
    var m = await moKh();
    bam(q(m.khung, '[data-bsidk="dk1"]'));
    bam(q(sheet(m), '[data-bsituchoi]'));
    var s = sheet(m);
    q(s, '#bsiLyDoTc').value = 'ngoài khu vực giao';
    bam(q(s, '[data-bsitcok]')); await tick();
    bang('gửi từ chối', goiTen(m, 'tu_choi').map(function (x) { return x.ts; }), [{ name: 'dk1', ly_do: 'ngoài khu vực giao' }]);
    var k = await moKh(null, 'kh');
    dung('cuối kỳ', chu(q(k.khung, '[data-bsikh="SI00012"]')).indexOf('Cuối kỳ 15 ngày') >= 0);
    dung('nhắc chưa có giá', chu(q(k.khung, '[data-bsikh="SI00013"]')).indexOf('Chưa khai giá riêng') >= 0);
  });

  await ca('giá riêng: chạm gợi ý thì điền sẵn giá đã trả và nguồn hoá đơn, lưu gửi số không dấu chấm', async function () {
    var m = await moGia();
    bam(q(m.khung, '[data-bsigoiy="BANU00002"]'));
    var s = sheet(m);
    bang('giá gợi ý', q(s, '#bsiGia').value, '31000');
    dung('nguồn gợi ý', chu(s).indexOf('mã sỉ BAWS00011') >= 0 && chu(s).indexOf('HD-5') >= 0);
    q(s, '#bsiGia').value = '30.500';
    bam(q(s, '[data-bsigiaok]')); await tick();
    bang('lưu', goiTen(m, 'luu_gia').map(function (x) { return x.ts; }), [{ khach: 'SI00012', ma: 'BANU00002', gia: '30500' }]);
  });

  await ca('giá riêng: thôi bán món hỏi xác nhận trước khi gửi; thêm món tìm rồi khai giá', async function () {
    var m = await moGia();
    bam(q(m.khung, '[data-bsigiamon="BANU00001"]'));
    var s = sheet(m);
    bam(q(s, '[data-bsibo]')); await tick();
    var xn = sheet(m);
    dung('hỏi xác nhận', chu(xn).indexOf('Thôi bán') >= 0);
    bang('chưa gửi khi chưa xác nhận', goiTen(m, 'bo_gia').length, 0);
    bam(q(xn, '[data-y]')); await tick(); await tick();
    bang('gửi thôi bán', goiTen(m, 'bo_gia').map(function (x) { return x.ts; }), [{ khach: 'SI00012', ma: 'BANU00001' }]);
    var g = await moGia();
    bam(g.g.document.getElementById('bsiThemMon')); await tick();
    bam(q(sheet(g), '[data-bsimon="BANU00007"]'));
    var p = sheet(g);
    q(p, '#bsiGia').value = '18000';
    bam(q(p, '[data-bsigiaok]')); await tick();
    bang('thêm món', goiTen(g, 'luu_gia').map(function (x) { return x.ts; }), [{ khach: 'SI00012', ma: 'BANU00007', gia: '18000' }]);
  });

  await ca('bật trả cuối kỳ hỏi xác nhận rồi mới gửi; tắt đặt sỉ web gửi ngay', async function () {
    var m = await moGia();
    bam(q(m.khung, '[data-bsict="ky"]')); await tick();
    bang('chưa gửi', goiTen(m, 'luu_khach').length, 0);
    bam(q(sheet(m), '[data-y]')); await tick(); await tick();
    bang('gửi bật', goiTen(m, 'luu_khach').map(function (x) { return x.ts; }), [{ khach: 'SI00012', cuoi_ky: 1 }]);
    var w = await moGia();
    bam(q(w.khung, '[data-bsict="web"]')); await tick();
    bang('tắt web', goiTen(w, 'luu_khach').map(function (x) { return x.ts; }), [{ khach: 'SI00012', dat_web: 0 }]);
  });

  console.log('v630 Bánh sỉ app: ' + ket.dat + ' ca dat, ' + ket.hong + ' ca hong');
  if (ket.hong) process.exit(1);
})();

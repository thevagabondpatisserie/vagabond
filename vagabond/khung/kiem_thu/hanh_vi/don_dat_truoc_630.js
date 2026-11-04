/* Ca kiểm HÀNH VI v630: màn "Đơn đặt trước" (bánh thiết kế riêng) trên app.
 *
 * Nạp THẬT 63-don-dat-truoc.js cùng các hàm nền nó gọi (h, money, dsCongCu,
 * posChipNut, kmHangChip...) vào DOM giả, máy chủ giả trả đúng hình dạng của
 * thiet_ke_rieng.ds_don và thiet_ke_rieng.xem. Mỗi ca bấm đúng chuỗi thao
 * tác của Sales, quản lý cửa hàng hay kế toán.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/don_dat_truoc_630.js
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
var MAN = doc('63-don-dat-truoc.js');

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
var HAM = ['h', 'money', 'today', 'vgbChuan', 'vgbKhop', 'anhMon'].map(function (t) { return layHam(NEN, t); })
  .concat([layHam(POS, 'posChipNut')])
  .concat(['dsccHang', 'dsCongCu', 'dsCongCuNoi', 'dsKhoangToi', 'dsTrongKhoangToi', 'dsDemTheo', 'dsDemKhoangToi', 'dsNhanGon'].map(function (t) { return layHam(KHUON, t); }))
  .concat(['var scanBarcode = function () { return Promise.resolve(null); };'])
  .concat([layHam(KM, 'kmHangChip'), layHam(KHO, 'errMsg')]).join('\n');

var HOM = '2026-11-14';
function phieu(name, so, ds, pt) { return { name: name, so_tien: so, docstatus: ds, pt: pt || 'Chuyển khoản', quay: 'SALES', ngay: '2026-11-03', gd: 'BT-1' }; }
function don(ten, ma, tt, nhan, ngay, con, ds) {
  return { name: ten, ma: ma, trang_thai: tt, nhan: nhan, khach: 'Nguyễn An', sdt: '0909123456', tac_pham: 'Croquembouche', kich_co: 'M',
    ngay: ngay, gio: '17:00', diem_nhan: 'The Vagabond District 1', tong: 7560000, coc: 3780000, con_lai: con,
    bang_ke: ['Bánh thiết kế riêng: Croquembouche', 'Size: M (45-55 cm, 130-160 bánh)', 'Trang trí: Hoa lan trắng', 'Ngày tiệc: 14/11/2026 lúc 17:00'],
    hoa_don: tt === 'da_giao' ? 'HDB-26-11-00001' : '', phieu: ds || [] };
}
var DON = {
  'SO-1': don('SO-1', 'TKR26110001', 'cho_coc', 'Chờ cọc', '2026-11-20', 7560000, []),
  'SO-2': don('SO-2', 'TKR26110002', 'da_coc', 'Đã cọc', HOM, 3780000, [phieu('PE-COC', 3780000, 1)]),
  'SO-3': don('SO-3', 'TKR26110003', 'du_tien', 'Đã thu đủ', HOM, 0, [phieu('PE-A', 3780000, 1), phieu('PE-B', 3780000, 0)]),
  'SO-4': don('SO-4', 'TKR26110004', 'du_tien', 'Đã thu đủ', HOM, 0, [phieu('PE-C', 3780000, 1), phieu('PE-D', 3780000, 1, 'Tiền mặt')]),
  'SO-5': don('SO-5', 'TKR26110005', 'da_giao', 'Đã giao', '2026-11-10', 0, [phieu('PE-E', 7560000, 1)]),
};
var QUAY = [{ ma: 'TCV', ten: 'District 1' }, { ma: 'NVHTN', ten: 'NVHTN' }];
var TT = [{ k: 'cho_coc', ten: 'Chờ cọc' }, { k: 'da_coc', ten: 'Đã cọc' }, { k: 'du_tien', ten: 'Đã thu đủ' }, { k: 'da_giao', ten: 'Đã giao' }, { k: 'da_huy', ten: 'Đã huỷ' }];
var KE_TOAN = 0, LOI = {}, TRA = {}, ONEPAY = 0;

function dungMoi(vai) {
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);
  var goi = [], toastDs = [], dieuHuong = [], kho = {};
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, Number: Number, Date: Date, setTimeout: setTimeout, isNaN: isNaN, encodeURIComponent: encodeURIComponent,
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
      if (duong === 'vagabond.thiet_ke_rieng.ds_don') {
        var rows = Object.keys(DON).map(function (k) { return DON[k]; });
        var dem = {}; rows.forEach(function (r) { dem[r.trang_thai] = (dem[r.trang_thai] || 0) + 1; });
        return Promise.resolve({ rows: rows, dem: dem, hom_nay: HOM, trang_thai: TT, quay: QUAY, la_ke_toan: KE_TOAN });
      }
      if (duong === 'vagabond.thiet_ke_rieng.xem') {
        var r = JSON.parse(JSON.stringify(DON[ts.name]));
        r.quay = QUAY; r.la_ke_toan = KE_TOAN; r.onepay = ONEPAY;
        r.qr = r.con_lai > 0 ? { anh: 'data:image/svg+xml;base64,QR', ngan_hang: 'MB', stk: '0931224334', noi_dung: r.ma } : null;
        return Promise.resolve(r);
      }
      return Promise.resolve(TRA[duong] || { ok: 1 });
    },
  };
  that.window = that;
  vm.runInNewContext(HAM, that, { filename: 'ham-nen.js' });
  vm.runInNewContext(MAN, that, { filename: '63-don-dat-truoc.js' });
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
function goiTen(m, t) { return m.goi.filter(function (x) { return x.duong === 'vagabond.thiet_ke_rieng.' + t; }); }

async function moDs(vai) {
  var m = dungMoi(vai || ['Sales User']);
  vm.runInNewContext('ddtTt = ""; ddtTim = ""; ddtMo = ""; if (typeof ddtDiem !== "undefined") { ddtDiem = ""; ddtNgay = ""; }', m.g);
  await m.g.scrDonDatTruoc();
  await tick();
  return m;
}
async function moCt(ten, vai) {
  var m = dungMoi(vai || ['Sales User']);
  vm.runInNewContext('ddtMo = "' + ten + '";', m.g);
  await m.g.scrDonDatTruocCt();
  await tick();
  return m;
}

(async function () {
  console.log('v630 Đơn đặt trước: màn app thật trên DOM giả');

  await ca('không có vai: không gọi máy chủ, câu nói ai được mở', async function () {
    var m = await moDs(['Bộ phận đặt hàng']);
    dung('câu khoá', chu(m.khung).indexOf('Màn này mở cho Sales') >= 0);
    bang('không gọi máy chủ', m.goi.length, 0);
  });

  await ca('danh sách: thẻ tóm tắt đếm theo trạng thái, nhóm theo ngày nhận, còn phải thu do máy chủ tính', async function () {
    var m = await moDs();
    var tom = chu(q(m.khung, '[data-ddttom]'));
    dung('tóm tắt: ' + tom, tom.indexOf('4 đơn · còn phải thu 11.340.000đ') >= 0);
    bang('năm thẻ', m.khung.querySelectorAll('[data-ddtthe]').length, 5);
    dung('nhãn ngày hôm nay', chu(m.khung).indexOf('HÔM NAY · THỨ BẢY 14/11') >= 0);
    dung('thẻ chờ cọc ghi còn đủ', chu(q(m.khung, '[data-ddtthe="SO-1"]')).indexOf('Còn 7.560.000đ') >= 0);
    dung('thẻ có phiếu nháp nhắc kế toán', chu(q(m.khung, '[data-ddtthe="SO-3"]')).indexOf('1 phiếu chuyển khoản chờ kế toán ghi sổ') >= 0);
  });

  await ca('bấm ô Đã cọc là lọc, có thanh tổng theo bộ lọc; gõ số điện thoại là tìm', async function () {
    var m = await moDs();
    bam(q(m.khung, '[data-ddtso="da_coc"]'));
    await tick();
    bang('chỉ còn đơn đã cọc', m.khung.querySelectorAll('[data-ddtthe]').map(function (x) { return x.getAttribute('data-ddtthe'); }), ['SO-2']);
    dung('thanh lọc', chu(q(m.khung, '[data-ddtloc]')).indexOf('1 đơn · còn 3.780.000đ') >= 0);
    var o = m.g.document.getElementById('ddtDsTim');
    o.value = '0909'; o.dispatchEvent(dg.suKien('input', {}, o));
    bang('tìm theo số', m.khung.querySelectorAll('[data-ddtthe]').length, 5);
  });

  /* Codex #531 vòng 3 (AGENTS 2b.3): ba hàng chip trạng thái, điểm nhận, khoảng
     ngày nhận; lọc áp cả danh sách lẫn thẻ tóm tắt; "Mọi ngày" mở rộng lại. */
  function chipLoc(m, ho, k) {
    return m.khung.querySelectorAll('[data-dscc]').filter(function (x) { return x.getAttribute('data-dscc') === ho + '|' + k; })[0];
  }
  function theDs(m) { return m.khung.querySelectorAll('[data-ddtthe]').map(function (x) { return x.getAttribute('data-ddtthe'); }); }
  await ca('Codex #531 v3: hàng chip điểm nhận và khoảng ngày nhận, bấm lọc thật áp cả danh sách lẫn thẻ tóm tắt; Mọi ngày mở rộng lại', async function () {
    var cu = DON['SO-1'].diem_nhan;
    DON['SO-1'].diem_nhan = 'Nguyễn Văn Hưởng';
    try {
      var m = await moDs();
      dung('có chip điểm nhận', chipLoc(m, 'diem', 'Nguyễn Văn Hưởng') && chipLoc(m, 'diem', 'The Vagabond District 1'));
      dung('có chip mở rộng Mọi ngày', chipLoc(m, 'ngay', '') && chu(chipLoc(m, 'ngay', '')).indexOf('Mọi ngày') >= 0);
      bam(chipLoc(m, 'ngay', 'hom_nay')); await tick();
      bang('ngày nhận hôm nay', theDs(m), ['SO-2', 'SO-3', 'SO-4']);
      var tom = chu(q(m.khung, '[data-ddttom]'));
      dung('tóm tắt theo bộ lọc: ' + tom, tom.indexOf('3 đơn · còn phải thu 3.780.000đ') >= 0);
      dung('ô Đã thu đủ đếm theo bộ lọc', chu(q(m.khung, '[data-ddtso="du_tien"]')).indexOf('2 đơn') >= 0);
      dung('thanh đang lọc', chu(q(m.khung, '[data-ddtloc]')).indexOf('3 đơn') >= 0);
      bam(chipLoc(m, 'ngay', '')); await tick();
      bang('Mọi ngày mở rộng lại', theDs(m).length, 5);
      bam(chipLoc(m, 'diem', 'Nguyễn Văn Hưởng')); await tick();
      bang('lọc điểm nhận', theDs(m), ['SO-1']);
      dung('tóm tắt điểm nhận', chu(q(m.khung, '[data-ddttom]')).indexOf('1 đơn · còn phải thu 7.560.000đ') >= 0);
      dung('chip Hôm nay ẩn vì điểm này không có đơn nhận hôm nay', !chipLoc(m, 'ngay', 'hom_nay'));
      bam(chipLoc(m, 'ngay', '7_ngay')); await tick();
      bang('điểm nhận và 7 ngày tới cùng áp', theDs(m), ['SO-1']);
      dung('chip 7 ngày tới đếm đúng', chu(chipLoc(m, 'ngay', '7_ngay')).indexOf('1') >= 0);
      bam(chipLoc(m, 'diem', '')); await tick();
      bang('Mọi điểm nhận, 7 ngày tới không gồm đơn ngày đã qua', theDs(m).slice().sort(), ['SO-1', 'SO-2', 'SO-3', 'SO-4']);
    } finally { DON['SO-1'].diem_nhan = cu; }
  });

  /* Codex #531 vòng 7 (AGENTS 2b.4): chỗ nào có tên tác phẩm thì có ảnh qua
     anhMon (00-nen.js thật); đơn chưa có ảnh giữ ô 🍰. */
  await ca('Codex #531 v7: thẻ danh sách và màn chi tiết có ảnh tác phẩm, đơn chưa có ảnh giữ ô 🍰', async function () {
    DON['SO-1'].anh = '/files/croquembouche.jpg';
    try {
      var m = await moDs();
      var the = m.khung.querySelectorAll('[data-ddtthe]');
      bang('mỗi thẻ một ô ảnh', the.map(function (x) { return x.querySelectorAll('.imm').length; }), [1, 1, 1, 1, 1]);
      bang('ảnh thật của SO-1', q(q(m.khung, '[data-ddtthe="SO-1"]'), 'img').getAttribute('src'), '/files/croquembouche.jpg');
      dung('ảnh tải chậm', q(q(m.khung, '[data-ddtthe="SO-1"]'), 'img').getAttribute('loading') === 'lazy');
      var o = q(q(m.khung, '[data-ddtthe="SO-2"]'), '.immp');
      dung('đơn chưa có ảnh giữ ô 🍰', o && chu(o) === '🍰' && !q(q(m.khung, '[data-ddtthe="SO-2"]'), 'img'));
      var c = await moCt('SO-1');
      bang('chi tiết có ảnh', q(q(c.khung, '[data-ddtct]'), 'img').getAttribute('src'), '/files/croquembouche.jpg');
      var c2 = await moCt('SO-2');
      dung('chi tiết chưa có ảnh giữ ô 🍰', chu(q(q(c2.khung, '[data-ddtct]'), '.immp')) === '🍰');
    } finally { delete DON['SO-1'].anh; }
  });

  await ca('bấm thẻ mở chi tiết đúng đơn', async function () {
    var m = await moDs();
    bam(q(m.khung, '[data-ddtthe="SO-2"]'));
    await tick();
    bang('gọi xem', goiTen(m, 'xem').map(function (x) { return x.ts.name; }), ['SO-2']);
    dung('chi tiết', chu(m.khung).indexOf('TKR26110002') >= 0);
  });

  await ca('đã cọc: nút đáy Thu phần còn lại; thu tiền mặt gửi đúng quầy đã chọn và nhớ quầy cho lần sau', async function () {
    var m = await moCt('SO-2');
    var nut = m.g.document.getElementById('ddtChinh');
    dung('nút thu', chu(nut).indexOf('Thu phần còn lại 3.780.000đ') >= 0);
    bam(nut);
    var s = sheet(m);
    dung('sheet có số còn lại', chu(q(s, '[data-ddtcon]')) === '3.780.000đ');
    bam(q(s, '[data-ddtquay="NVHTN"]'));
    bam(q(s, '[data-ddtthutm]'));
    await tick();
    bang('gọi thu tiền mặt', goiTen(m, 'thu_tien_mat').map(function (x) { return x.ts; }), [{ name: 'SO-2', quay: 'NVHTN' }]);
    bang('nhớ quầy', m.kho.vgb_ddt_quay, 'NVHTN');
    dung('báo xong', m.toast.join('|').indexOf('Đã thu tiền mặt 3.780.000đ') >= 0);
  });

  await ca('thu tiền mặt hỏng (chưa khai tài khoản): câu máy chủ hiện ra, sheet còn, bấm lại được', async function () {
    var m = await moCt('SO-2');
    LOI['vagabond.thiet_ke_rieng.thu_tien_mat'] = 'Chưa khai tài khoản cho phương thức Tiền mặt.';
    try {
      bam(m.g.document.getElementById('ddtChinh'));
      var s = sheet(m);
      bam(q(s, '[data-ddtquay="TCV"]'));
      var nut = q(s, '[data-ddtthutm]');
      bam(nut);
      await tick();
      dung('toast câu máy chủ', m.toast.join('|').indexOf('Chưa khai tài khoản') >= 0);
      dung('sheet còn', m.tai.body.children.indexOf(s) >= 0);
      dung('nút bấm lại được', !nut.disabled);
    } finally { delete LOI['vagabond.thiet_ke_rieng.thu_tien_mat']; }
  });

  /* v637 (anh Việt 03/11/2026): khách trả thẻ OnePay ở quầy, không cà máy POS. */
  await ca('v637 Thẻ OnePay: tắt thì không có cách Thẻ; bật thì có, bấm ra mã QR trang trả thẻ của đúng đơn; chờ tới khi tiền về thì tự báo và đóng sheet', async function () {
    ONEPAY = 0;
    var m0 = await moCt('SO-2');
    bam(m0.g.document.getElementById('ddtChinh'));
    dung('tắt thì không có Thẻ', !q(sheet(m0), '[data-ddtcach="the"]'));
    dung('không còn cà máy POS', chu(sheet(m0)).indexOf('POS') < 0);
    ONEPAY = 1;
    try {
      var m = await moCt('SO-2');
      vm.runInNewContext('DDT_HOI_THE = 5;', m.g);
      TRA['vagabond.onepay_dat.ma_the'] = { ma: 'TKR26110002', link: 'https://vagabond.test/tra-the/TKR26110002?k=abc', anh: 'data:image/svg+xml;base64,THE', con_lai: 3780000 };
      TRA['vagabond.onepay_dat.con_lai'] = { con_lai: 3780000, trang_thai: 'da_coc' };
      bam(m.g.document.getElementById('ddtChinh'));
      var s = sheet(m);
      bam(q(s, '[data-ddtcach="the"]'));
      await tick(); await tick();
      bang('hỏi mã thẻ đúng đơn', m.goi.filter(function (x) { return x.duong === 'vagabond.onepay_dat.ma_the'; }).map(function (x) { return x.ts; }), [{ name: 'SO-2' }]);
      dung('ảnh QR trang thẻ', q(s, '[data-ddttheqr]') && q(s, '[data-ddttheqr]').getAttribute('src') === 'data:image/svg+xml;base64,THE');
      dung('nói rõ tiền của Sales, két không cộng', chu(s).indexOf('két quầy không cộng') >= 0 && chu(s).indexOf('Sales') >= 0);
      await new Promise(function (r) { setTimeout(r, 40); });
      dung('đang chờ: đã hỏi lại, sheet còn', m.goi.filter(function (x) { return x.duong === 'vagabond.onepay_dat.con_lai'; }).length >= 1 && m.tai.body.children.indexOf(s) >= 0);
      TRA['vagabond.onepay_dat.con_lai'] = { con_lai: 0, trang_thai: 'du_tien', the: [{ ma: 'TKR26110002-1', so_tien: 3780000, so_ghi: 3780000, du: 0 }] };
      await new Promise(function (r) { setTimeout(r, 40); });
      dung('tiền về: báo đúng số', m.toast.join('|').indexOf('Khách đã trả thẻ 3.780.000đ cho TKR26110002') >= 0);
      dung('đóng sheet, mở lại đơn', m.tai.body.children.indexOf(s) < 0 && m.dieuHuong.indexOf('scrDonDatTruocCt') >= 0);
      var n = m.goi.filter(function (x) { return x.duong === 'vagabond.onepay_dat.con_lai'; }).length;
      await new Promise(function (r) { setTimeout(r, 40); });
      bang('đóng rồi thì thôi hỏi', m.goi.filter(function (x) { return x.duong === 'vagabond.onepay_dat.con_lai'; }).length, n);
      /* Đổi sang tiền mặt giữa chừng thì lượt hỏi thẻ dừng. */
      TRA['vagabond.onepay_dat.con_lai'] = { con_lai: 3780000, trang_thai: 'da_coc' };
      var m2 = await moCt('SO-2');
      vm.runInNewContext('DDT_HOI_THE = 5;', m2.g);
      bam(m2.g.document.getElementById('ddtChinh'));
      var s2 = sheet(m2);
      bam(q(s2, '[data-ddtcach="the"]'));
      await tick(); await tick();
      bam(q(s2, '[data-ddtcach="tien_mat"]'));
      var n2 = m2.goi.filter(function (x) { return x.duong === 'vagabond.onepay_dat.con_lai'; }).length;
      await new Promise(function (r) { setTimeout(r, 40); });
      bang('đổi cách thì thôi hỏi', m2.goi.filter(function (x) { return x.duong === 'vagabond.onepay_dat.con_lai'; }).length, n2);
    } finally { ONEPAY = 0; delete TRA['vagabond.onepay_dat.ma_the']; delete TRA['vagabond.onepay_dat.con_lai']; }
  });

  /* Codex #538 vòng 2 (SHA d740afd3f): số còn phải thu giảm vì một khoản KHÁC (chuyển
     khoản vừa khớp, tiền mặt) không được báo là khách đã trả thẻ. */
  await ca('v637 Codex #538 vòng 2: đang chờ thẻ mà đơn được trả bằng chuyển khoản thì KHÔNG báo đã trả thẻ; ma_the báo đơn đã đủ thì không hiện QR', async function () {
    ONEPAY = 1;
    try {
      var m = await moCt('SO-2');
      vm.runInNewContext('DDT_HOI_THE = 5;', m.g);
      TRA['vagabond.onepay_dat.ma_the'] = { ma: 'TKR26110002', link: 'https://x/tra-the', anh: 'data:image/svg+xml;base64,THE', con_lai: 3780000, trang_thai: 'da_coc', the: [] };
      TRA['vagabond.onepay_dat.con_lai'] = { con_lai: 0, trang_thai: 'du_tien', the: [] };
      bam(m.g.document.getElementById('ddtChinh'));
      var s = sheet(m);
      bam(q(s, '[data-ddtcach="the"]'));
      await new Promise(function (r) { setTimeout(r, 40); });
      dung('không báo đã trả thẻ: ' + m.toast.join('|'), m.toast.join('|').indexOf('Khách đã trả thẻ') < 0);
      dung('báo đơn đã đủ qua cách khác', m.toast.join('|').indexOf('đã thu đủ qua cách khác') >= 0);
      /* Màn mở từ dữ liệu cũ (r.con_lai 3.780.000) nhưng máy chủ nói đơn đã đủ: không hiện QR, không hỏi. */
      TRA['vagabond.onepay_dat.ma_the'] = { ma: 'TKR26110002', link: 'https://x/tra-the', anh: 'data:image/svg+xml;base64,THE', con_lai: 0, trang_thai: 'du_tien', the: [] };
      var m2 = await moCt('SO-2');
      vm.runInNewContext('DDT_HOI_THE = 5;', m2.g);
      bam(m2.g.document.getElementById('ddtChinh'));
      var s2 = sheet(m2);
      bam(q(s2, '[data-ddtcach="the"]'));
      await new Promise(function (r) { setTimeout(r, 40); });
      dung('không QR khi đã đủ', !q(s2, '[data-ddttheqr]'));
      bang('không hỏi lại', m2.goi.filter(function (x) { return x.duong === 'vagabond.onepay_dat.con_lai'; }).length, 0);
      dung('không báo đã trả thẻ', m2.toast.join('|').indexOf('Khách đã trả thẻ') < 0);
    } finally { ONEPAY = 0; delete TRA['vagabond.onepay_dat.ma_the']; delete TRA['vagabond.onepay_dat.con_lai']; }
  });

  await ca('chuyển khoản qua QR: hiện mã QR và nội dung là mã đơn; chưa thấy tiền thì nói chờ, thấy thì báo lập phiếu', async function () {
    var m = await moCt('SO-2');
    bam(m.g.document.getElementById('ddtChinh'));
    var s = sheet(m);
    bam(q(s, '[data-ddtcach="qr"]'));
    dung('ảnh QR', !!q(s, 'img') && q(s, 'img').getAttribute('src').indexOf('data:image/svg') === 0);
    dung('nội dung', chu(s).indexOf('TKR26110002') >= 0);
    TRA['vagabond.thiet_ke_rieng.kiem_tien_ve'] = { ok: 1, lap: 0 };
    bam(q(s, '[data-ddtkiem]'));
    await tick();
    dung('chưa thấy', m.toast.join('|').indexOf('Chưa thấy tiền về') >= 0);
    TRA['vagabond.thiet_ke_rieng.kiem_tien_ve'] = { ok: 1, lap: 1 };
    bam(q(s, '[data-ddtkiem]'));
    await tick();
    dung('đã thấy', m.toast.join('|').indexOf('máy lập phiếu thu chờ kế toán ghi sổ') >= 0);
    bang('hai lần kiểm', goiTen(m, 'kiem_tien_ve').length, 2);
    delete TRA['vagabond.thiet_ke_rieng.kiem_tien_ve'];
  });

  await ca('đủ tiền mà còn phiếu nháp: nút giao bánh bị khoá, nói chờ kế toán; Sales không thấy nút ghi sổ, kế toán thấy', async function () {
    var m = await moCt('SO-3');
    var nut = m.g.document.getElementById('ddtChinh');
    dung('nút khoá', nut.hasAttribute('disabled') && chu(nut).indexOf('Chờ kế toán') >= 0);
    bang('Sales không có ô ghi sổ', m.khung.querySelectorAll('[data-ddtghiso]').length, 0);
    KE_TOAN = 1;
    try {
      var k = await moCt('SO-3', ['Accounts User']);
      var o = q(k.khung, '[data-ddtghiso]');
      dung('kế toán có ô ghi sổ', !!o);
      o.files = [{ name: 'giay-bao-co.png', noiDung: 'AAA' }];
      o.dispatchEvent(dg.suKien('change', {}, o));
      await tick(); await tick();
      var g = goiTen(k, 'ghi_so_phieu');
      bang('ghi sổ đúng phiếu nháp kèm ảnh', g.map(function (x) { return [x.ts.name, x.ts.phieu, JSON.parse(x.ts.anh)[0].ten]; }), [['SO-3', 'PE-B', 'giay-bao-co.png']]);
    } finally { KE_TOAN = 0; }
  });

  await ca('đủ tiền, mọi phiếu đã ghi sổ: Giao bánh và xuất hoá đơn gửi đúng quầy, Để sau thì không gửi gì', async function () {
    var m = await moCt('SO-4');
    var nut = m.g.document.getElementById('ddtChinh');
    dung('nút giao', chu(nut).indexOf('Giao bánh và xuất hoá đơn') >= 0 && !nut.hasAttribute('disabled'));
    bam(nut);
    bam(q(sheet(m), '[data-ddtdong]'));
    bang('Để sau không gửi', goiTen(m, 'giao_banh').length, 0);
    bam(nut);
    var s = sheet(m);
    bam(q(s, '[data-ddtquay="TCV"]'));
    bam(q(s, '[data-ddtgiaook]'));
    await tick();
    bang('gọi giao bánh', goiTen(m, 'giao_banh').map(function (x) { return x.ts; }), [{ name: 'SO-4', quay: 'TCV' }]);
  });

  await ca('chờ cọc: có nút Huỷ đơn chưa cọc; lý do ngắn bị nhắc, đủ thì gửi', async function () {
    var m = await moCt('SO-1');
    bam(q(m.khung, '[data-ddthuy]'));
    var s = sheet(m);
    q(s, '#ddtLyDo').value = 'abc';
    bam(q(s, '[data-ddthuyok]'));
    await tick();
    bang('lý do ngắn không gửi', goiTen(m, 'huy').length, 0);
    q(s, '#ddtLyDo').value = 'Khách đổi ý, không chuyển cọc';
    bam(q(s, '[data-ddthuyok]'));
    await tick();
    bang('gửi huỷ', goiTen(m, 'huy').map(function (x) { return x.ts; }), [{ name: 'SO-1', ly_do: 'Khách đổi ý, không chuyển cọc' }]);
  });

  await ca('đơn đã cọc và đã giao không có nút huỷ; đã giao không còn nút đáy, hiện số hoá đơn', async function () {
    var a = await moCt('SO-2');
    bang('đã cọc không huỷ', a.khung.querySelectorAll('[data-ddthuy]').length, 0);
    var b = await moCt('SO-5');
    bang('đã giao không nút đáy', b.g.document.getElementById('ddtChinh'), null);
    dung('số hoá đơn', chu(b.khung).indexOf('HDB-26-11-00001') >= 0);
  });

  await ca('bảng kê thu về một dòng đếm số, bấm mới mở (2b.17)', async function () {
    var m = await moCt('SO-2');
    dung('đếm dòng', chu(m.khung).indexOf('Bảng kê 4 dòng') >= 0);
    dung('nằm trong details', !!q(m.khung, 'details'));
  });

  console.log('v630 Đơn đặt trước: ' + ket.dat + ' ca dat, ' + ket.hong + ' ca hong');
  if (ket.hong) process.exit(1);
})();

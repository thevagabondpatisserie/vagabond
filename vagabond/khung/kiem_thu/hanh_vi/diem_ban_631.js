/* Ca kiểm HÀNH VI v631: điểm bán tự nhận theo tài khoản và bảng giá riêng NVH.
 *
 * Anh Việt 02/11/2026 duyệt mẫu bốn màn. Nạp THẬT các hàm của 09 (chọn điểm ở
 * quầy, giá món theo điểm), 17 (Cài đặt Điểm bán) và cả tệp 63 (Bảng giá theo
 * điểm bán) vào DOM giả; máy chủ giả chỉ trả dữ liệu và ghi lời gọi. Phép đặt
 * giá thật ở máy chủ chạy trong thu_diem_ban_631.py. Mỗi ca bấm đúng chuỗi thao
 * tác của người dùng (điều 15).
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/diem_ban_631.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
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
var NEN = doc('00-nen.js'), POS = doc('09-tinh-tien-quay.js'), KM = doc('13-khuyen-mai.js'), KHO = doc('03-kho-chung-tu.js'), CD = doc('17-cai-dat.js');
var HAM = ['h', 'money', 'vgbChuan', 'vgbKhop', 'anhMon'].map(function (t) { return layHam(NEN, t); })
  .concat(['posChipNut', 'posDiemCuaToi', 'posDsDiemChon', 'posGiaMon', 'posDiemTheoQuay', 'posDiemVua', 'scrPosChonQuay', 'posDongBoQuay', 'posGiaVuaDoi', 'posDocGiaChung', 'posSuaGiaVuaDoi'].map(function (t) { return layHam(POS, t); }))
  .concat([layHam(KM, 'kmHangChip'), layHam(KM, 'posGiaTang'), layHam(KM, 'posNoiKm'), layHam(KHO, 'errMsg'), "var POS_MA_PHI_GIAO = 'DVBH00001';"])
  .concat(['dbTenNguoi', 'dbChipNguoi', 'scrDiemBanSua', 'dbDoc', 'dbLuu', 'dbChipNguon', 'dbBamNguon', 'dbChuNguon'].map(function (t) { return layHam(CD, t); }))
  .concat(['var dbDs = null, dbSuaDuoc = 0, dbMo = null, dbMoi = 0, dbNguonCoSan = [], dbKhoTang = [], dbGoiY = {}, dbNguoiDung = [], dsItemsCache = null, posSua = null;'])
  .join('\n') + '\n' + doc('63-bang-gia-diem.js');

var DIEM = [
  { ma: 'SALES', ten: 'Sales Online', ten_ngan: 'Sales Online', co_quay: 0, quay: '', gia_rieng: {}, co_bang_gia: 0 },
  { ma: 'TCV', ten: 'The Vagabond District 1', ten_ngan: 'District 1', co_quay: 1, quay: 'TCV', gia_rieng: {}, co_bang_gia: 0 },
  { ma: 'NVHTN', ten: 'Nhà Văn Hóa Thanh Niên', ten_ngan: 'NVHTN', co_quay: 1, quay: 'NVHTN', gia_rieng: { 'TRA-HL-M': 70000 }, co_bang_gia: 1 },
];
var BANG = {
  diem: { ma: 'NVHTN', ten: 'Nhà Văn Hóa Thanh Niên', ten_ngan: 'NVHTN', bang_gia: 'Giá riêng NVHTN' }, so_ngay: 30, sua_duoc: 1,
  mon: [
    { ma: 'TRA-HL-M', ten: 'Trà Hoa Lài Trái Hồng, M', nhom: 'Món nước', gia_chung: 95000, gia_diem: 70000, da_ban: 120, anh: '/files/tra-hoa-lai.jpg' },
    { ma: 'TRA-MC', ten: 'Trà Lài Mãng Cầu', nhom: 'Món nước', gia_chung: 95000, gia_diem: 0, da_ban: 40 },
    { ma: 'BM-SHIO', ten: 'Bánh Mì Bơ Muối Shiopan', nhom: 'Bánh mì', gia_chung: 30000, gia_diem: 0, da_ban: 12 },
    { ma: 'CRO-MINI', ten: 'Plain Croissant, Mini', nhom: 'Bánh mì', gia_chung: 30000, gia_diem: 0, da_ban: 0 },
  ],
};

function dungMoi(o) {
  o = o || {};
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);
  var goi = [], toastDs = [], tin = [], dieuHuong = [], luu = {};
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object, RegExp: RegExp,
    Promise: Promise, Number: Number, Date: Date, setTimeout: setTimeout, clearTimeout: clearTimeout, isNaN: isNaN,
    localStorage: { getItem: function (k) { return luu[k] || null; }, setItem: function (k, v) { luu[k] = String(v); } },
    CFGBH: { diem: DIEM, diem_cua_toi: o.cua || [] },
    /* Như thật: CFGBH bị xoá (null) thì đọc lại từ máy chủ (o.cfgMoi). */
    cfgBanHang: function () { if (!that.CFGBH) { that.docLaiCfg = (that.docLaiCfg || 0) + 1; that.CFGBH = o.cfgMoi || { diem: DIEM, diem_cua_toi: [] }; } return Promise.resolve(that.CFGBH); },
    isSales: function () { return false; }, posDoc: function () {},
    getList: function (dt, ts) { (that.goiList = that.goiList || []).push({ dt: dt, ts: ts }); return Promise.resolve(o.item || []); },
    posQuay: null, posDon: null, posHomNayTxt: null,
    scrPosQuay: function scrPosQuay() { that.vaoQuay = that.posQuay && that.posQuay.ma; },
    frame: function (t, html, opt) {
      khung.innerHTML = html + (opt && opt.footer ? opt.footer : ''); khung._nghe = {}; khung.onclick = null; that._t = t; return khung;
    },
    go: function (fn) { dieuHuong.push(fn.name || 'anDanh'); return fn(); },
    back: function () { dieuHuong.push('back'); },
    busy: function () {}, toast: function (m) { toastDs.push(m); }, baoTin: function (m) { tin.push(m); },
    bcTaiVe: function (t) { that.taiVe = t; },
    sheet: function (t, ds, cur, chon) { that.bangChon = { t: t, ds: ds, chon: chon }; },
    confirmSheet: function () { return Promise.resolve(true); }, promptSheet: function () { return Promise.resolve(null); },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: ts });
      if (duong === 'vagabond.diem_ban.bang_gia_diem') return Promise.resolve(JSON.parse(JSON.stringify(o.bang || BANG)));
      if (duong === 'vagabond.diem_ban.luu') return Promise.resolve({ diem: JSON.parse(ts.diem), sua_duoc: 1 });
      if (duong === 'vagabond.diem_ban.luu_gia') return Promise.resolve({ so: JSON.parse(ts.thay_doi).length });
      if (duong === 'vagabond.diem_ban.xuat_excel_gia') return Promise.resolve({ ten_file: 'bang-gia-nvhtn.xlsx', b64: 'AA' });
      return Promise.resolve({});
    },
  };
  that.window = that;
  vm.runInNewContext(HAM, that, { filename: 'ham-631.js' });
  return { g: that, tai: tai, khung: khung, goi: goi, toast: toastDs, tin: tin, dieuHuong: dieuHuong, luu: luu };
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
function bam(el) { el.dispatchEvent(dg.suKien('click', {}, el)); }
function q(m, s) { return m.khung.querySelectorAll(s); }
function goiTen(m, t) { return m.goi.filter(function (x) { return x.duong === 'vagabond.diem_ban.' + t; }); }

(async function () {
  console.log('v631 Điểm bán tự nhận theo tài khoản, bảng giá riêng NVH');

  await ca('quầy: Gia Bảo chỉ đứng District 1 thì mở Tính tiền vào thẳng District 1, không thấy thẻ Sales Online để bấm nhầm', async function () {
    var m = dungMoi({ cua: ['TCV'] });
    await m.g.scrPosChonQuay(); await tick();
    bang('vào thẳng quầy', [m.g.vaoQuay, m.dieuHuong], ['TCV', ['scrPosQuay']]);
    dung('không vẽ màn chọn điểm', q(m, '[data-q]').length === 0);
  });

  await ca('quầy: quản lý đứng hai điểm chỉ thấy hai điểm đó, điểm vừa đứng lên đầu có nhãn; bấm chọn là nhớ', async function () {
    var m = dungMoi({ cua: ['TCV', 'NVHTN'] });
    m.luu.vgb_diem_vua = 'NVHTN';
    await m.g.scrPosChonQuay(); await tick();
    var the = q(m, '[data-q]').map(function (x) { return chu(x); });
    bang('hai điểm', the.length, 2);
    dung('NVH đứng đầu có nhãn Vừa đứng', the[0].indexOf('Nhà Văn Hóa Thanh Niên') >= 0 && the[0].indexOf('Vừa đứng') >= 0);
    dung('không có Sales Online', chu(m.khung).indexOf('Sales Online') < 0);
    bam(q(m, '[data-q="1"]')[0]); await tick();
    bang('vào District 1 và nhớ', [m.g.vaoQuay, m.luu.vgb_diem_vua], ['TCV', 'TCV']);
  });

  await ca('quầy: tài khoản chưa khai điểm nào thì chọn như cũ đủ ba điểm, kèm dòng nhắc quản lý khai', async function () {
    var m = dungMoi({ cua: [] });
    await m.g.scrPosChonQuay(); await tick();
    bang('đủ ba điểm', q(m, '[data-q]').length, 3);
    dung('có dòng nhắc', chu(q(m, '[data-posnhackhai]')[0]).indexOf('Nhân viên đứng điểm này') >= 0);
  });

  await ca('quầy: giá món ở NVH là giá NVH, món chưa khai và điểm khác là giá chung; bill sửa theo đúng quầy của bill', async function () {
    var m = dungMoi();
    var tra = { name: 'TRA-HL-M', standard_rate: 95000 }, banh = { name: 'BM-SHIO', standard_rate: 30000 };
    bang('NVH', [m.g.posGiaMon(tra, DIEM[2]), m.g.posGiaMon(banh, DIEM[2])], [70000, 30000]);
    bang('District 1', m.g.posGiaMon(tra, DIEM[1]), 95000);
    bang('chưa biết điểm', m.g.posGiaMon(tra, null), 95000);
    bang('bill quầy NVHTN', m.g.posDiemTheoQuay('NVHTN').ma, 'NVHTN');
    bang('bill online không có điểm quầy', m.g.posDiemTheoQuay(''), null);
  });

  await ca('Bảng giá: mặc định chip Đã bán ở NVH 30 ngày; chip Chưa có giá; gõ giá thì nút Lưu đếm đúng, bấm Lưu gửi đúng ô đã đổi', async function () {
    var m = dungMoi();
    await m.g.scrBangGiaDiem('NVHTN'); await tick();
    var mon = function () { return q(m, '[data-bgdmon]').map(function (x) { return x.getAttribute('data-bgdmon'); }); };
    bang('đã bán 30 ngày', mon(), ['TRA-HL-M', 'TRA-MC', 'BM-SHIO']);
    dung('chip có số', chu(q(m, '[data-bgdchip="da_ban"]')[0]).indexOf('Đã bán ở NVHTN 30 ngày · 3') >= 0);
    dung('ô giá NVH hiện số đang lưu', q(m, '[data-bgdgia="TRA-HL-M"]')[0].value === '70.000');
    /* Codex PR #532: dòng món có ảnh món từ danh mục, chưa có ảnh thì ô 🍰 giữ chỗ. */
    var anh = q(m, '[data-bgdmon="TRA-HL-M"]')[0].querySelectorAll('.imm')[0];
    dung('ảnh món từ danh mục', !!anh && anh.tagName.toLowerCase() === 'img' && anh.getAttribute('src') === '/files/tra-hoa-lai.jpg');
    dung('món chưa có ảnh có ô giữ chỗ', chu(q(m, '[data-bgdmon="TRA-MC"]')[0].querySelectorAll('.immp')[0] || {}) === '🍰');
    bam(q(m, '[data-bgdchip="chua_gia"]')[0]); await tick();
    bang('chưa có giá', mon(), ['TRA-MC', 'BM-SHIO']);
    bam(q(m, '[data-bgdchip="tat_ca"]')[0]); await tick();
    var o = q(m, '[data-bgdgia="TRA-MC"]')[0];
    o.value = '70.000';
    o.dispatchEvent(dg.suKien('input', {}, o));
    var o2 = q(m, '[data-bgdgia="TRA-HL-M"]')[0];
    o2.value = '';
    o2.dispatchEvent(dg.suKien('input', {}, o2));
    var nl = q(m, '[data-bgdluu]')[0];
    bang('nút Lưu đếm', [chu(nl), !!nl.disabled], ['Lưu 2 giá đã đổi', false]);
    dung('ô đổi có viền xanh', o.style.borderColor === '#0d9488');
    await nl.onclick(); await tick();
    bang('gửi đúng', JSON.parse(goiTen(m, 'luu_gia')[0].ts.thay_doi), [{ ma: 'TRA-HL-M', gia: '' }, { ma: 'TRA-MC', gia: '70000' }]);
    dung('báo đã lưu', m.toast.join('|').indexOf('Đã lưu 2 giá') >= 0);
  });

  await ca('Bảng giá: Nạp Excel biến dòng đọc được thành ô đã đổi để xem lại (chưa lưu); mã không còn bán thì bỏ, báo số', async function () {
    var m = dungMoi();
    await m.g.scrBangGiaDiem('NVHTN'); await tick();
    m.g.bgdApNap([{ ma: 'TRA-HL-M', gia: 70000 }, { ma: 'BM-SHIO', gia: 25000 }, { ma: 'MA-CU', gia: 1 }]);
    bang('chưa gọi lưu', goiTen(m, 'luu_gia').length, 0);
    bang('một giá khác giá đang lưu', chu(q(m, '[data-bgdluu]')[0]), 'Lưu 1 giá đã đổi');
    dung('báo đọc và bỏ', m.tin[0].indexOf('Đã đọc 2 dòng') === 0 && m.tin[0].indexOf('Bỏ 1 dòng') >= 0);
  });

  await ca('Bảng giá: người không có quyền sửa giá thấy giá nhưng ô khoá, không có nút Lưu, Tải, Nạp', async function () {
    var b = JSON.parse(JSON.stringify(BANG)); b.sua_duoc = 0;
    var m = dungMoi({ bang: b });
    await m.g.scrBangGiaDiem('NVHTN'); await tick();
    dung('ô khoá', q(m, '[data-bgdgia="TRA-HL-M"]')[0].hasAttribute('disabled'));
    bang('không nút', q(m, '[data-bgdluu]').length + q(m, '[data-bgdxuat]').length + q(m, '[data-bgdnap]').length, 0);
  });

  await ca('Bảng giá mở từ trang chủ khi chưa điểm nào bật giá riêng: nói việc cần làm, có nút sang Cài đặt Điểm bán', async function () {
    var m = dungMoi();
    m.g.CFGBH = { diem: DIEM.slice(0, 2), diem_cua_toi: [] };
    vm.runInNewContext('BGD.ma = "";', m.g);
    m.g.scrDiemBan = function scrDiemBan() { m.g.moCaiDat = 1; };
    await m.g.scrBangGiaDiem(''); await tick();
    dung('nói việc', chu(m.khung).indexOf('bật Giá riêng') >= 0);
    bam(q(m, '[data-bgdcd]')[0]);
    bang('sang Cài đặt', m.g.moCaiDat, 1);
  });

  await ca('Cài đặt Điểm bán: chưa khai ai thì gợi sẵn theo bill 30 ngày; bỏ chip, bật Giá riêng NVHTN, Lưu gửi đúng và không gửi cờ nội bộ', async function () {
    var m = dungMoi();
    vm.runInNewContext('dbDs = ' + JSON.stringify([{ ma: 'NVHTN', ten: 'Nhà Văn Hóa Thanh Niên', ten_ngan: 'NVHTN', co_quay: 1, quay: 'NVHTN', nguon: ['Tại chỗ'], bat: 1, nhan_vien: [], bang_gia: '' }]) +
      '; dbMo = 0; dbSuaDuoc = 1; dbGoiY = ' + JSON.stringify({ NVHTN: [{ user: 'truc@vgb.vn', ten: 'Thanh Trúc', so: 415 }, { user: 'de@vgb.vn', ten: 'Hoàng Dễ', so: 6 }] }) +
      '; dbNguoiDung = [{ user: "uyen@vgb.vn", ten: "Phương Uyên" }];', m.g);
    m.g.scrDiemBanSua(); await tick();
    var nv = q(m, '[data-dbnvbo]').map(function (x) { return x.getAttribute('data-dbnvbo'); });
    bang('gợi sẵn hai người', nv, ['truc@vgb.vn', 'de@vgb.vn']);
    dung('chip có số bill', chu(q(m, '[data-dbnvbo="truc@vgb.vn"]')[0]).indexOf('Thanh Trúc · 415 bill') >= 0);
    dung('dòng gợi ý', !!q(m, '[data-dbgoiy]')[0]);
    bam(q(m, '[data-dbnvbo="de@vgb.vn"]')[0]); await tick();
    bang('bỏ Dễ, Dễ thành gợi ý thêm lại được', [q(m, '[data-dbnvbo]').length, q(m, '[data-dbnvthem="de@vgb.vn"]').length], [1, 1]);
    bam(q(m, '[data-dbnvmoi]')[0]);
    bang('bảng thêm người chỉ có người chưa khai', m.g.bangChon.ds.map(function (x) { return x.value; }), ['uyen@vgb.vn']);
    m.g.bangChon.chon(m.g.bangChon.ds[0]); await tick();
    bam(q(m, '[data-dbgia="1"]')[0]); await tick();
    dung('chọn Giá riêng NVHTN', q(m, '[data-dbgia="1"]')[0].getAttribute('aria-pressed') === 'true' && chu(m.khung).indexOf('Giá riêng NVHTN') >= 0);
    m.g.document.getElementById = function (id) { return { dbMa: { value: 'NVHTN' }, dbTen: { value: 'Nhà Văn Hóa Thanh Niên' }, dbTenNgan: { value: 'NVHTN' } }[id] || null; };
    await m.g.dbLuu(); await tick();
    var gui = JSON.parse(goiTen(m, 'luu')[0].ts.diem)[0];
    bang('gửi', [gui.nhan_vien, gui.gia_rieng, '_daGoiY' in gui, '_laGoiY' in gui], [['truc@vgb.vn', 'uyen@vgb.vn'], 1, false, false]);
  });

  await ca('Cài đặt Điểm bán: điểm nhận đơn online không có mục Nhân viên đứng điểm và Bảng giá', async function () {
    var m = dungMoi();
    vm.runInNewContext('dbDs = [{ ma: "SALES", ten: "Sales Online", co_quay: 0, quay: "", nguon: ["Pancake"], bat: 1 }]; dbMo = 0; dbSuaDuoc = 1; dbGoiY = {};', m.g);
    m.g.scrDiemBanSua(); await tick();
    bang('không mục', q(m, '[data-dbnv]').length + q(m, '[data-dbgia]').length, 0);
  });

  /* Codex PR #532 (finding 2): posQuay giữ đối tượng điểm cũ nên giỏ thu theo
     giá cũ sau khi quản lý đổi bảng giá. */
  function nvhGia(g) { var d = JSON.parse(JSON.stringify(DIEM)); d[2].gia_rieng = g; return { diem: d, diem_cua_toi: [] }; }
  function gioNvh(m) {
    m.g.CFGBH = nvhGia({ 'TRA-HL-M': 70000, 'TRA-MC': 80000 });
    m.g.posQuay = m.g.CFGBH.diem[2];
    m.g.posDon = { mon: [
      { item_code: 'TRA-HL-M', ten: 'Trà Hoa Lài', qty: 2, rate: 70000 },
      { item_code: 'TRA-MC', ten: 'Trà Mãng Cầu', qty: 1, rate: 80000 },
      { item_code: 'TRA-HL-M', ten: 'Trà Hoa Lài', qty: 1, rate: 50000, combo: 'KMCB01 - Combo sáng', combo_ma: 'CB-1' },
    ], kmKq: { tong_giam: 10000 } };
    m.g.dsItemsCache = [{ name: 'TRA-HL-M', standard_rate: 95000 }, { name: 'TRA-MC', standard_rate: 95000 }];
  }

  await ca('quầy: quản lý đổi giá NVH lúc giỏ đang có món; cấu hình đọc lại thì quầy dùng điểm MỚI, giỏ sang giá mới, combo giữ giá, món bỏ giá riêng về giá chung', async function () {
    var m = dungMoi();
    gioNvh(m);
    m.g.CFGBH = nvhGia({ 'TRA-HL-M': 65000 });
    var n = m.g.posDongBoQuay();
    bang('hai món đổi', n, 2);
    bang('giá giỏ', m.g.posDon.mon.map(function (x) { return x.rate; }), [65000, 95000, 50000]);
    dung('quầy trỏ điểm mới', m.g.posQuay === m.g.CFGBH.diem[2]);
    bang('khuyến mãi tính lại', m.g.posDon.kmKq, null);
    bang('đọc lại lần nữa không đổi gì', m.g.posDongBoQuay(), 0);
  });

  await ca('quầy: bấm Thu mà máy chủ chặn vì bảng giá vừa đổi thì đọc lại cấu hình, giỏ sang giá mới, về màn quầy, báo thu ngân kiểm lại tổng', async function () {
    var m = dungMoi({ cfgMoi: nvhGia({ 'TRA-HL-M': 65000, 'TRA-MC': 80000 }) });
    gioNvh(m);
    var loi = new Error('Bảng giá của điểm vừa đổi: 1 món đã sang giá mới. Màn đã cập nhật, kiểm lại tổng tiền với khách rồi bấm lưu lại.');
    bang('nhận ra lỗi giá', await m.g.posGiaVuaDoi(loi), true);
    bang('đọc lại cấu hình từ máy chủ', m.g.docLaiCfg, 1);
    bang('giá giỏ', m.g.posDon.mon.map(function (x) { return x.rate; }), [65000, 80000, 50000]);
    bang('về màn quầy', m.dieuHuong, ['scrPosQuay']);
    dung('báo thu ngân', m.toast.join('|').indexOf('kiểm lại tổng tiền') >= 0);
    var m2 = dungMoi();
    gioNvh(m2);
    bang('lỗi khác để màn cũ báo như thường', [await m2.g.posGiaVuaDoi(new Error('Hết phiên')), m2.dieuHuong.length, m2.g.docLaiCfg || 0], [false, 0, 0]);
  });

  /* Codex PR #532 vòng 3: quản lý TẮT bảng giá NVH (hoặc bỏ giá riêng một món)
     lúc giỏ còn giá cũ. Máy chủ chặn; quầy đọc giá chung của món trong giỏ từ
     danh mục (máy chưa nạp bảng món) rồi về đúng giá chung. */
  await ca('quầy: bảng giá NVH vừa tắt, giỏ còn giá cũ, máy chưa nạp bảng món: máy chủ chặn thì giỏ về giá chung đọc từ danh mục; combo và phí giao giữ nguyên', async function () {
    var tat = nvhGia({}); tat.diem[2].co_bang_gia = 0;
    var m = dungMoi({ cfgMoi: tat, item: [{ name: 'TRA-HL-M', standard_rate: 95000 }, { name: 'TRA-MC', standard_rate: 90000 }, { name: 'DVBH00001', standard_rate: 1000 }] });
    gioNvh(m);
    m.g.dsItemsCache = null;
    m.g.posQuay = nvhGia({}).diem[2];
    m.g.posDon.mon.push({ item_code: 'DVBH00001', ten: 'Phí giao', qty: 1, rate: 15000 });
    bang('nhận ra lỗi giá', await m.g.posGiaVuaDoi(new Error('Bảng giá của điểm vừa đổi: 2 món đã sang giá mới.')), true);
    bang('hỏi giá chung mọi món không thuộc combo', m.g.goiList[0].ts.filters.name, ['in', ['TRA-HL-M', 'TRA-MC', 'DVBH00001']]);
    bang('giá giỏ', m.g.posDon.mon.map(function (x) { return x.rate; }), [95000, 90000, 50000, 15000]);
  });

  await ca('Khuyến mãi tặng món: thêm món tặng vào giỏ theo giá quầy đang bán (giá NVH nếu có, không thì giá chung), không theo giá gợi ý của máy chủ', async function () {
    var m = dungMoi();
    m.g.posQuay = DIEM[2];
    m.g.dsItemsCache = [{ name: 'TRA-HL-M', standard_rate: 95000 }, { name: 'BM-SHIO', standard_rate: 30000 }];
    bang('đã nạp bảng món', [m.g.posGiaTang({ item_code: 'TRA-HL-M', rate: 99000 }), m.g.posGiaTang({ item_code: 'BM-SHIO', rate: 99000 })], [70000, 30000]);
    m.g.dsItemsCache = null;
    bang('chưa nạp bảng món', [m.g.posGiaTang({ item_code: 'TRA-HL-M', rate: 99000 }), m.g.posGiaTang({ item_code: 'BM-SHIO', rate: 31000 })], [70000, 31000]);
    /* Bấm đúng nút "+ Thêm món tặng vào đơn" như thu ngân. */
    m.g.dsItemsCache = [{ name: 'TRA-HL-M', standard_rate: 95000 }];
    m.g.posDon = { mon: [], kmKq: { them_mon: [{ item_code: 'TRA-HL-M', qty: 1, rate: 99000, tang: 1 }] } };
    var nutTang = { onclick: null };
    m.g.document.getElementById = function (id) { return id === 'posKmThemTang' ? nutTang : null; };
    m.g.posNoiKm();
    nutTang.onclick();
    bang('món tặng vào giỏ ở giá NVH', m.g.posDon.mon.map(function (x) { return [x.item_code, x.qty, x.rate]; }), [['TRA-HL-M', 1, 70000]]);
  });

  /* Codex PR #532 vòng 5: sửa bill nháp sau khi quản lý đổi giá NVH. Dòng đã
     lưu giữ giá đã chốt; máy chủ chặn vì món thêm mới mang giá cũ thì màn sửa
     bill đặt lại giá đúng các món thêm mới rồi vẽ lại. */
  await ca('sửa bill: máy chủ chặn vì món thêm mới mang giá cũ thì chỉ món thêm mới sang giá mới (giá NVH, không có thì giá chung); dòng đã lưu, combo, phí giao giữ nguyên', async function () {
    var m = dungMoi({ cfgMoi: nvhGia({ 'TRA-HL-M': 80000 }), item: [{ name: 'TRA-MC', standard_rate: 90000 }, { name: 'TRA-HL-M', standard_rate: 95000 }] });
    m.g.posSua = { mon: [
      { item_code: 'TRA-HL-M', qty: 2, rate: 70000, dong_goc: 'D1' },
      { item_code: 'TRA-HL-M', qty: 1, rate: 70000 },
      { item_code: 'TRA-MC', qty: 1, rate: 80000 },
      { item_code: 'TRA-HL-M', qty: 1, rate: 50000, combo: 'KMCB01 - Combo sáng' },
      { item_code: 'DVBH00001', qty: 1, rate: 15000 },
    ] };
    m.g.CFGBH = nvhGia({ 'TRA-HL-M': 70000 });
    bang('nhận ra lỗi giá', await m.g.posSuaGiaVuaDoi(new Error('Bảng giá của điểm vừa đổi: 2 món đã sang giá mới.'), 'NVHTN'), true);
    bang('đọc lại cấu hình', m.g.docLaiCfg, 1);
    bang('giá', m.g.posSua.mon.map(function (x) { return x.rate; }), [70000, 80000, 90000, 50000, 15000]);
    bang('chỉ hỏi giá chung món thêm mới', m.g.goiList[0].ts.filters.name, ['in', ['TRA-HL-M', 'TRA-MC']]);
    var m2 = dungMoi();
    m2.g.posSua = { mon: [{ item_code: 'TRA-HL-M', qty: 1, rate: 1 }] };
    bang('lỗi khác (OTP) để nhánh cũ xử lý', [await m2.g.posSuaGiaVuaDoi(new Error('Thao tác này cần mã OTP'), 'NVHTN'), m2.g.posSua.mon[0].rate], [false, 1]);
  });

  /* Ba chỗ GỌI nằm trong hàm màn quầy quá lớn để nạp vào DOM giả (máy in, ca,
     khuyến mãi...), nên ca này đọc THÂN HÀM THẬT để chốt thứ tự gọi. Hành vi
     của hai hàm được gọi thì hai ca trên chạy thật. Không thay ca hành vi. */
  await ca('quầy: chốt chỗ gọi - vào màn quầy đồng bộ giá TRƯỚC khi cộng tổng và hiện QR; mở bảng món đồng bộ trước khi vẽ giá; lưu bill và tạm tính lỗi giá thì đọc lại', async function () {
    var POS10 = doc('10-bill-quay.js');
    var vao = layHam(POS, 'scrPosQuay');
    var iDb = vao.indexOf('var nGiaDoi = posDongBoQuay();');
    dung('vào màn quầy có đồng bộ, sau khi có điểm', iDb > vao.indexOf('if (!posQuay) return go(scrPosChonQuay, true);') && vao.indexOf('if (!posQuay) return go(scrPosChonQuay, true);') > 0);
    dung('đồng bộ trước khi cộng tổng', iDb < vao.indexOf('var tong = posDon.mon.reduce('));
    var them = layHam(POS, 'posThemMon');
    dung('bảng món đồng bộ trước khi vẽ giá', them.indexOf('posDongBoQuay();') > 0 && them.indexOf('posDongBoQuay();') < them.indexOf('posGiaMon(x, posQuay)'));
    [[layHam(POS, 'posLuuDon'), 'Thu tiền'], [layHam(POS10, 'posInTamTinh'), 'Tạm tính']].forEach(function (x) {
      var f = x[0], iGoi = f.indexOf("'vagabond.ban_hang.tao_don_tay'"), iBat = f.indexOf('if (await posGiaVuaDoi(e)) return;', iGoi);
      dung(x[1] + ': lỗi lưu đi qua posGiaVuaDoi ngay trong catch của lần gọi', iGoi > 0 && iBat > iGoi && f.slice(iGoi, iBat).indexOf('catch (e)') > 0);
    });
  });

  /* Codex PR #532 (finding 3): giá gõ dở ở điểm A không được thành giá lưu
     của điểm B khi mở B từ nút Bảng giá ở Cài đặt. */
  await ca('Bảng giá: gõ giá ở NVH chưa lưu, mở District 1 từ Cài đặt: District 1 không mang giá của NVH; quay lại NVH vẫn còn giá gõ dở', async function () {
    var d = JSON.parse(JSON.stringify(DIEM)); d[1].co_bang_gia = 1; d[1].gia_rieng = {};
    var m = dungMoi();
    m.g.CFGBH = { diem: d, diem_cua_toi: [] };
    await m.g.scrBangGiaDiem('NVHTN'); await tick();
    bam(q(m, '[data-bgdchip="tat_ca"]')[0]); await tick();
    var o = q(m, '[data-bgdgia="TRA-MC"]')[0];
    o.value = '70.000';
    o.dispatchEvent(dg.suKien('input', {}, o));
    bang('NVH có một giá đổi', chu(q(m, '[data-bgdluu]')[0]), 'Lưu 1 giá đã đổi');
    await m.g.scrBangGiaDiem('TCV'); await tick();
    var nl = q(m, '[data-bgdluu]')[0];
    bang('District 1 không có giá đổi', [chu(nl), nl.hasAttribute('disabled')], ['Chưa đổi giá nào', true]);
    await nl.onclick(); await tick();
    bang('không ghi gì vào District 1', goiTen(m, 'luu_gia').length, 0);
    await m.g.scrBangGiaDiem('NVHTN'); await tick();
    bang('NVH còn giá gõ dở', [chu(q(m, '[data-bgdluu]')[0]), q(m, '[data-bgdgia="TRA-MC"]')[0].value], ['Lưu 1 giá đã đổi', '70.000']);
  });

  console.log('\n' + ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng.');
  process.exit(ket.hong ? 1 : 0);
})().catch(function (e) { console.log('NO TUNG: ' + (e && e.stack || e)); process.exit(1); });

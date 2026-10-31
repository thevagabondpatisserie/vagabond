/* Ca kiểm HÀNH VI v625: AI trên màn Tuyển dụng (anh Việt 31/10/2026, mẫu 4).
 *
 * Avatar từ CV, vòng điểm AI, dòng tóm tắt, bảng Hồ sơ AI (thanh tiêu chí, câu
 * nên hỏi, Chấm lại), xếp theo điểm, câu trả lời form trên thẻ, tải CV cho hồ sơ
 * thêm tay, và Tuyển gấp, Ảnh trên web ở màn sửa vị trí.
 *
 * Dùng chung khung với tuyen_dung_622.js (chép phần dựng màn, nạp THẬT
 * 60-tuyen-dung.js); mỗi ca bấm đúng chuỗi thao tác của quản lý.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/tuyen_dung_625.js
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
var MAN = doc('60-tuyen-dung.js');

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
var HAM = ['h', 'money', 'today', 'vgbChuan', 'vgbKhop'].map(function (t) { return layHam(NEN, t); })
  .concat([layHam(POS, 'posChipNut')])
  .concat(['dsccHang', 'dsCongCu', 'dsCongCuNoi'].map(function (t) { return layHam(KHUON, t); }))
  .concat(['var scanBarcode = function () { return Promise.resolve(null); };',
    'var inQrAnh = function (s) { QR.push(s); return Promise.resolve("data:image/png;base64,AA"); };'])
  .concat([layHam(KM, 'kmHangChip'), layHam(KHO, 'errMsg')]).join('\n');

var HOM = '2026-10-30';
function duLieu() {
  return {
    hom_nay: HOM, bay_gio: HOM + ' 09:00:00',
    tom_tat: { moi: 2, qua_han: 1, hen_hom_nay: 1, cong_chua_tra: 1 },
    nguon: ['Web Vagabond', 'QR tại cửa hàng', 'TopCV', 'Trang việc làm khác', 'Facebook, Zalo', 'Người quen giới thiệu', 'Đến trực tiếp'],
    ly_do_dung: ['Không phù hợp', 'Ứng viên rút', 'Không liên lạc được', 'Đã đủ người'],
    hinh_thuc: ['Toàn thời gian', 'Bán thời gian', 'Thời vụ', 'Thực tập'], ca_ranh: ['Sáng', 'Chiều', 'Tối', 'Cuối tuần', 'Linh hoạt'],
    noi_lam: ['The Vagabond District 1', 'Xưởng sản xuất Tân Bình'], bo_phan: [{ k: 'Thu ngân - TV', ten: 'Thu ngân' }],
    tieu_chi_mac_dinh: ['Thái độ, giao tiếp', 'Nhanh nhẹn'], cau_dong_y: 'Tôi đồng ý ... trong 12 tháng ...', thang_luu: 12,
    link_ung_tuyen: 'https://order.thevagabondpatisserie.com/ung-tuyen',
    /* Bản chép của tuyen_dung.MAU_TIN, KET_QUA_GOI (máy chủ gửi qua tong_quan). */
    hotline: '0931 224 334',
    ket_qua_goi: [{ k: 'Nghe máy', p: 'Đã nói chuyện' }, { k: 'Hẹn gọi lại', p: 'Hẹn gọi lại sau' },
      { k: 'Không nghe máy', p: 'Giữ Mới nhận' }, { k: 'Sai số', p: 'Số không liên lạc được' }],
    /* Bản chép của tuyen_dung.buoc_app() (máy chủ chia trạng thái vào bước). */
    buoc: [{ so: 1, ten: 'Liên hệ', tt: ['Mới nhận', 'Đã liên hệ'] }, { so: 2, ten: 'Phỏng vấn', tt: ['Hẹn phỏng vấn'] },
      { so: 3, ten: 'Làm thử', tt: ['Làm thử'] }, { so: 4, ten: 'Nhận việc', tt: ['Đề nghị nhận việc', 'Đã nhận việc'] }],
    mau_theo_trang_thai: { 'Mới nhận': 'da_nhan', 'Hẹn phỏng vấn': 'hen_pv', 'Làm thử': 'lam_thu', 'Dừng': 'cam_on' },
    mau_tin: [
      { k: 'da_nhan', ten: 'Đã nhận hồ sơ', p: 'x', noi_dung: 'Chào {ten}, đã nhận hồ sơ vị trí {vi_tri}. Gọi {hotline}.' },
      { k: 'hen_pv', ten: 'Hẹn phỏng vấn', p: 'x', noi_dung: 'Chào {ten}, hẹn phỏng vấn vị trí {vi_tri} lúc {gio} tại {noi_lam}. Gọi {hotline}.' },
      { k: 'lam_thu', ten: 'Hẹn làm thử', p: 'x', noi_dung: 'Chào {ten}, làm thử {vi_tri} lúc {gio} tại {noi_lam}, có trả công {cong}.' },
      { k: 'cam_on', ten: 'Cảm ơn, chưa phù hợp', p: 'x', noi_dung: 'Chào {ten}, cảm ơn bạn đã ứng tuyển {vi_tri}.' },
    ],
    vi_tri: [
      { name: 'VTT-0001', tieu_de: 'Thu ngân ca tối', ten_bo_phan: 'Thu ngân', noi_lam: 'The Vagabond District 1', hinh_thuc: 'Bán thời gian',
        so_can: 2, dang_tuyen: 1, khach_thay: 1, trang_thai_web: 'Khách đang thấy', so_ho_so: 3, ket_thuc: '',
        ds_tieu_chi: ['Thái độ', 'Nhanh nhẹn'], gio_lam_thu: 4, cong_lam_thu: 100000 },
      { name: 'VTT-0002', tieu_de: 'Phụ bếp Pastry', ten_bo_phan: 'Bếp Pastry', noi_lam: 'Xưởng sản xuất Tân Bình', hinh_thuc: 'Toàn thời gian',
        so_can: 1, dang_tuyen: 0, khach_thay: 0, trang_thai_web: 'Đang tắt trên app, khách không thấy', so_ho_so: 1, ket_thuc: '' },
    ],
    rows: [
      { name: 'UV-1', buoc: { so: 1, xong: 0, dung: 0 }, vi_tri: 'VTT-0001', ten_vi_tri: 'Thu ngân ca tối', ho_ten: 'Nguyễn Văn An', sdt: '0909123456', nguon: 'Web Vagabond',
        trang_thai: 'Mới nhận', creation: '2026-10-29 07:00:00', qua_han: 1, lan_nop: 2, ca_ranh: 'Tối', khu_vuc: 'Quận 3', cham: [] },
      { name: 'UV-2', buoc: { so: 1, xong: 0, dung: 0 }, vi_tri: 'VTT-0001', ten_vi_tri: 'Thu ngân ca tối', ho_ten: 'Trần Thị Bình', sdt: '0912345678', nguon: 'QR tại cửa hàng',
        trang_thai: 'Mới nhận', creation: '2026-10-30 08:00:00', qua_han: 0, lan_nop: 1, cham: [] },
      { name: 'UV-3', buoc: { so: 2, xong: 0, dung: 0 }, vi_tri: 'VTT-0001', ten_vi_tri: 'Thu ngân ca tối', ho_ten: 'Lê Cường', sdt: '0987654321', nguon: 'TopCV',
        trang_thai: 'Hẹn phỏng vấn', lich_hen: HOM + ' 14:00:00', creation: '2026-10-28 08:00:00', qua_han: 0, lan_nop: 1,
        cham: [{ vong: 'Phỏng vấn', nguoi: 'Dễ', ket_luan: 'Cân nhắc', diem_tb: 2.5, nhan_xet: '' }] },
      { name: 'UV-4', buoc: { so: 3, xong: 0, dung: 0 }, vi_tri: 'VTT-0002', ten_vi_tri: 'Phụ bếp Pastry', ho_ten: 'Phạm Dũng', sdt: '0901111222', nguon: 'Đến trực tiếp',
        trang_thai: 'Làm thử', lich_hen: '2026-10-31 08:00:00', tien_cong_thu: 100000, da_tra_cong: 0, creation: '2026-10-27 08:00:00', qua_han: 0, lan_nop: 1, cham: [] },
    ].concat(THEM_HS),
  };
}
var THEM_HS = [];
var SUA_DL = null;
var QL = ['VGB - Quản lý cửa hàng'];
var QUAY = ['Sales User'];
var QR = [];
var HO_SO_AI = null;

function dungMoi(vai, loi) {
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);
  var goi = [], toastDs = [], hoi = [], dieuHuong = [];
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, Number: Number, Date: Date, setTimeout: setTimeout, isNaN: isNaN, QR: QR, encodeURIComponent: encodeURIComponent,
    moTab: [], chep: [], location: {},
    open: function (u) { that.moTab.push(u); },
    navigator: { clipboard: { writeText: function (t) { that.chep.push(t); return Promise.resolve(); } } },
    S: { roles: vai, stack: [] },
    hasRole: function (r) { return vai.indexOf(r) >= 0; },
    frame: function (t, html, opt) {
      khung.innerHTML = html + (opt && opt.footer ? opt.footer : ''); khung._nghe = {}; khung.onclick = null; that._t = t; return khung;
    },
    go: function (fn) { dieuHuong.push(fn.name || 'anDanh'); return fn(); },
    back: function () { dieuHuong.push('back'); },
    busy: function () {},
    toast: function (m) { toastDs.push(m); },
    bangChon: [],
    sheet: function (t, ds, cur, chon, tim) { that.bangChon.push({ t: t, ds: ds, cur: cur, chon: chon, tim: tim }); },
    confirmSheet: function (t, m) { hoi.push(t + '|' + m); return Promise.resolve(true); },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: ts });
      if (duong === 'vagabond.tuyen_dung.tong_quan') { var dl = duLieu(); if (SUA_DL) SUA_DL(dl); return Promise.resolve(dl); }
      if (duong === 'vagabond.tuyen_dung.ho_so_ai') return Promise.resolve(HO_SO_AI);
      if (loi) return Promise.reject(new Error(loi));
      return Promise.resolve({ ok: 1 });
    },
  };
  that.window = that;
  vm.runInNewContext(HAM, that, { filename: 'ham-nen.js' });
  vm.runInNewContext(MAN, that, { filename: '60-tuyen-dung.js' });
  return { g: that, tai: tai, khung: khung, goi: goi, toast: toastDs, hoi: hoi, dieuHuong: dieuHuong };
}

var ket = { dat: 0, hong: 0 };
function dung(mo, dk) { if (!dk) throw new Error(mo); }
function bang(mo, a, b) {
  var x = JSON.stringify(a), y = JSON.stringify(b);
  if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y);
}
function tick() { return new Promise(function (r) { setTimeout(r, 5); }); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); }
}
function chu(el) { var s = el._chu || ''; (el.children || []).forEach(function (c) { s += chu(c); }); return s; }
function sheet(m) { var ds = m.tai.body.children; return ds.length > 1 ? ds[ds.length - 1] : null; }
function bam(el) { el.dispatchEvent(dg.suKien('click', {}, el)); }
function goiTen(m, t) { return m.goi.filter(function (x) { return x.duong === 'vagabond.tuyen_dung.' + t; }); }
function the(m, ten) { return m.khung.querySelectorAll('[data-tdhs="' + ten + '"]')[0]; }
function nut(el, attr) { return el ? el.querySelectorAll('[' + attr + ']')[0] : null; }

async function mo(vai, loi, dat) {
  var m = dungMoi(vai || QL, loi);
  vm.runInNewContext('tdTab = "hs"; tdTt = ""; tdVt = ""; tdTim = ""; tdLoc = "";' + (dat || ''), m.g);
  await m.g.scrTuyenDung();
  await tick();
  return m;
}


function ai(r, k) { return Object.assign(r, k); }
(async function () {
  console.log('v625 Tuyển dụng: AI đọc hồ sơ trên màn app');

  SUA_DL = function (dl) {
    ai(dl.rows[0], { ai_trang_thai: 'Đã đọc', ai_diem: 82, ai_nhan: 'Rất phù hợp', ai_tom_tat: 'Ba năm thu ngân F&B, ở gần.', co_anh: 1, co_cv: 1, ai_luc: '2026-10-30 08:00:00',
      luong_mong_muon: 9000000, tra_loi: [{ ma: 'ho_ten', cau_hoi: 'Họ và tên ứng viên', tra_loi: 'Nguyễn Văn An' },
        { ma: 'hoc_van', cau_hoi: 'Trình độ học vấn cao nhất', tra_loi: 'Tốt nghiệp THPT' }, { ma: 'luong', cau_hoi: 'Tổng thu nhập', tra_loi: '9.000.000 đ/tháng' }] });
    ai(dl.rows[1], { ai_trang_thai: 'Đang đọc', co_cv: 1 });
    ai(dl.rows[2], { ai_trang_thai: 'Chưa đọc được', ai_loi: 'Khoá hết hạn' });
    ai(dl.rows[3], { ai_trang_thai: 'Đã đọc', ai_diem: 45, ai_nhan: 'Chưa phù hợp', ai_tom_tat: 'Chưa làm bếp.' });
    dl.anh_web_chon = [{ url: '/assets/vagabond/web_order/tay-lam-banh-minh-hoa.jpg', ten: 'Bếp làm bánh', mo: 'Tay thợ bánh' },
      { url: '/assets/vagabond/images/quay-sales.jpg', ten: 'Quầy bánh', mo: 'Quầy' }];
  };

  await ca('thẻ ứng viên: avatar từ CV hoặc chữ cái đầu, vòng điểm, dòng tóm tắt AI theo trạng thái', async function () {
    var m = await mo();
    var a = the(m, 'UV-1'), anh = a.querySelectorAll('[data-tdanh]')[0];
    dung('ảnh CV qua cửa riêng tư', anh && anh.getAttribute('src').indexOf('/api/method/vagabond.tuyen_dung.anh_ung_vien?name=UV-1') === 0);
    var vong = nut(a, 'data-tdvongai');
    dung('vòng điểm có số và nhãn đọc màn hình', chu(vong) === '82' && vong.getAttribute('aria-label') === 'AI chấm 82 trên 100, Rất phù hợp');
    var dt = chu(nut(a, 'data-tddongai'));
    /* DOM giả ghép chữ của thẻ trước chữ của con, và giữ nguyên &amp; như innerHTML: so từng phần. */
    dung('dòng tóm tắt: ' + dt, dt.indexOf('✦ Rất phù hợp') >= 0 && dt.indexOf('Ba năm thu ngân F&amp;B, ở gần.') >= 0);
    dung('không ảnh: chữ cái đầu', chu(the(m, 'UV-2')).indexOf('TB') >= 0 && !nut(the(m, 'UV-2'), 'data-tdanh'));
    dung('đang đọc', chu(nut(the(m, 'UV-2'), 'data-tddongai')).indexOf('AI đang đọc') >= 0 && !nut(the(m, 'UV-2'), 'data-tdvongai'));
    dung('lỗi: chỉ đường xem lý do', chu(nut(the(m, 'UV-3'), 'data-tddongai')).indexOf('chưa đọc được') >= 0);
    dung('có CV: Mở CV qua cửa riêng tư', nut(a, 'data-tdmocv').getAttribute('href') === '/api/method/vagabond.tuyen_dung.xem_cv?name=UV-1');
    dung('chưa CV: nút Tải CV', !!nut(the(m, 'UV-3'), 'data-tdtaicv') && !nut(a, 'data-tdtaicv'));
    var ghi = chu(m.khung.querySelectorAll('[data-tdghi="0"]')[0] || a);
    dung('lương mong muốn có đơn vị', chu(a).indexOf('Lương mong muốn: 9.000.000 đ/tháng') >= 0 || ghi.indexOf('Lương mong muốn: 9.000.000 đ/tháng') >= 0);
    dung('câu trả lời form, bỏ câu đã có ô riêng', (chu(a) + ghi).indexOf('Trình độ học vấn cao nhất: Tốt nghiệp THPT') >= 0 &&
      (chu(a) + ghi).indexOf('Họ và tên ứng viên:') < 0 && (chu(a) + ghi).indexOf('Tổng thu nhập:') < 0);
  });

  await ca('Xếp theo điểm AI: điểm cao lên trước, AI chưa đọc xếp cuối; bấm lại về mới nộp trước', async function () {
    var m = await mo();
    var thu = function () { return m.khung.querySelectorAll('[data-tdhs]').map(function (x) { return x.getAttribute('data-tdhs'); }); };
    bang('mặc định theo máy chủ', thu(), ['UV-1', 'UV-2', 'UV-3', 'UV-4']);
    bam(m.khung.querySelectorAll('[data-tdxepai]')[0]); await tick();
    bang('theo điểm', thu(), ['UV-1', 'UV-4', 'UV-2', 'UV-3']);
    dung('dòng giải thích', chu(m.khung).indexOf('hồ sơ AI chưa đọc xếp cuối') >= 0);
    bam(m.khung.querySelectorAll('[data-tdxepai]')[0]); await tick();
    bang('bấm lại', thu(), ['UV-1', 'UV-2', 'UV-3', 'UV-4']);
  });

  await ca('Hồ sơ AI: thanh từng tiêu chí, kinh nghiệm, câu nên hỏi, lời nhắc AI chỉ gợi ý; Chấm lại gọi máy chủ', async function () {
    HO_SO_AI = { name: 'UV-1', trang_thai: 'Đã đọc', luc: '2026-10-30 08:00:00', co_cv: 1, kq: { diem: 82, nhan: 'Rất phù hợp', tom_tat: 'Ba năm thu ngân.',
      tieu_chi: [{ ten: 'Kinh nghiệm đúng vị trí', diem: 90, ly_do: 'Ba năm thu ngân' }, { ten: 'Lương mong muốn so khung', diem: 60, ly_do: 'Cao hơn khung' }],
      kinh_nghiem: [{ noi: 'Tiệm A', viec: 'Thu ngân', thoi_gian: '2022 - nay' }], ky_nang: ['Pancake'], can_hoi: ['Bạn làm ca tối được mấy ngày?'], co_cv: 1 } };
    var m = await mo();
    bam(nut(the(m, 'UV-1'), 'data-tdai')); await tick(); await tick();
    var s = sheet(m);
    dung('mở bảng', !!s && chu(s).indexOf('Hồ sơ AI · Nguyễn Văn An') >= 0);
    bang('hai thanh tiêu chí', s.querySelectorAll('[data-tdtc]').length, 2);
    dung('điểm và lý do', chu(s).indexOf('Kinh nghiệm đúng vị trí90Ba năm thu ngân') >= 0);
    dung('kinh nghiệm rút từ CV', chu(s).indexOf('Thu ngân · Tiệm A · 2022 - nay') >= 0);
    dung('câu nên hỏi', chu(s).indexOf('Bạn làm ca tối được mấy ngày?') >= 0);
    dung('AI chỉ gợi ý, không dùng giới tính tuổi', chu(s).indexOf('AI không dùng giới tính, tuổi') >= 0);
    bang('gọi đúng hồ sơ', goiTen(m, 'ho_so_ai')[0].ts, { name: 'UV-1' });
    bam(nut(s, 'data-tdchamlai')); await tick();
    bang('chấm lại', goiTen(m, 'cham_lai')[0].ts, { name: 'UV-1' });
  });

  await ca('Hồ sơ AI chưa đọc được: nói lý do, vẫn có Chấm lại', async function () {
    HO_SO_AI = { name: 'UV-3', trang_thai: 'Chưa đọc được', loi: 'Khoá hết hạn', kq: null, co_cv: 0 };
    var m = await mo();
    bam(nut(the(m, 'UV-3'), 'data-tdai')); await tick(); await tick();
    var s = sheet(m);
    dung('lý do', chu(s).indexOf('Lý do: Khoá hết hạn') >= 0);
    dung('chấm lại có, mở CV không', !!nut(s, 'data-tdchamlai') && chu(s).indexOf('Mở CV') < 0);
  });

  await ca('Codex #523: Chấm lại thất bại mà còn kết quả cũ: bảng báo lượt mới lỗi và lý do, ghi rõ bên dưới là kết quả lần trước', async function () {
    var cu = { diem: 82, nhan: 'Rất phù hợp', tom_tat: 'Ba năm thu ngân.', tieu_chi: [{ ten: 'Kinh nghiệm đúng vị trí', diem: 90 }], co_cv: 1 };
    HO_SO_AI = { name: 'UV-1', trang_thai: 'Chưa đọc được', loi: 'Đã dùng đủ 300 lượt đọc AI trong tháng', luc: '2026-10-30 08:00:00', co_cv: 1, kq: cu };
    var m = await mo();
    bam(nut(the(m, 'UV-1'), 'data-tdai')); await tick(); await tick();
    var s = sheet(m);
    dung('báo lượt mới lỗi kèm lý do', chu(s).indexOf('Lần chấm lại chưa xong. Lý do: Đã dùng đủ 300 lượt đọc AI trong tháng') >= 0);
    dung('ghi rõ kết quả cũ', chu(s).indexOf('Bên dưới là kết quả lần trước') >= 0);
    bang('vẫn hiện kết quả cũ', s.querySelectorAll('[data-tdtc]').length, 1);
    HO_SO_AI = { name: 'UV-1', trang_thai: 'Đang đọc', loi: '', luc: '2026-10-30 08:00:00', co_cv: 1, kq: cu };
    m = await mo();
    bam(nut(the(m, 'UV-1'), 'data-tdai')); await tick(); await tick();
    s = sheet(m);
    dung('đang đọc lại', chu(s).indexOf('AI đang đọc lại hồ sơ') >= 0 && chu(s).indexOf('Bên dưới là kết quả lần trước') >= 0);
    HO_SO_AI = { name: 'UV-1', trang_thai: 'Đã đọc', loi: '', luc: '2026-10-30 08:00:00', co_cv: 1, kq: cu };
    m = await mo();
    bam(nut(the(m, 'UV-1'), 'data-tdai')); await tick(); await tick();
    s = sheet(m);
    dung('đọc xong: không có dòng báo', chu(s).indexOf('kết quả lần trước') < 0);
  });

  await ca('Sửa vị trí: Tuyển gấp bật tắt, Ảnh trên web chọn bằng thẻ ảnh có dòng giải thích; lưu gửi hai ô mới', async function () {
    var m = await mo();
    vm.runInNewContext('tdKq = null;', m.g);
    await m.g.scrTdViTri('VTT-0001'); await tick();
    var anh = m.khung.querySelectorAll('[data-tdanhweb]');
    bang('ba lựa chọn ảnh', anh.map(function (x) { return x.getAttribute('data-tdanhweb'); }), ['', '/assets/vagabond/web_order/tay-lam-banh-minh-hoa.jpg', '/assets/vagabond/images/quay-sales.jpg']);
    bang('mặc định tự chọn theo bộ phận', anh.map(function (x) { return x.getAttribute('aria-pressed'); }), ['true', 'false', 'false']);
    dung('mỗi ảnh có dòng giải thích', chu(anh[0]).indexOf('Bếp ra ảnh bếp') >= 0);
    bam(anh[2]); await tick();
    bam(m.khung.querySelectorAll('[data-tdgap]')[0]); await tick();
    bang('đã chọn ảnh quầy', m.khung.querySelectorAll('[data-tdanhweb]').map(function (x) { return x.getAttribute('aria-pressed'); }), ['false', 'false', 'true']);
    var luu = m.khung.querySelectorAll('#tdLuuVt')[0];
    await luu.onclick(); await tick();
    var d = JSON.parse(goiTen(m, 'luu_vi_tri')[0].ts.du_lieu);
    bang('gửi hai ô mới', [d.tuyen_gap, d.anh_web], [1, '/assets/vagabond/images/quay-sales.jpg']);
  });

  console.log('\n' + ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng.');
  process.exit(ket.hong ? 1 : 0);
})().catch(function (e) { console.log('NO TUNG: ' + (e && e.stack || e)); process.exit(1); });

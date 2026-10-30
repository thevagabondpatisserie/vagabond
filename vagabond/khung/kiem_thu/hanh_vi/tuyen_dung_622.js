/* Ca kiểm HÀNH VI v622: màn Tuyển dụng (phân hệ Nhân sự).
 *
 * Anh Việt 30/10/2026: mọi quản lý bộ phận xem hồ sơ, chốt nhận người; làm thử
 * có trả công; bật tắt vị trí trên app là web đổi theo.
 *
 * Nạp THẬT 60-tuyen-dung.js cùng các hàm nền nó dùng vào DOM giả. Máy chủ giả
 * chỉ trả dữ liệu màn và ghi lại lời gọi; phép đổi trạng thái, chấm, ghi công
 * chạy thật ở thu_tuyen_dung_622.py. Mỗi ca bấm đúng chuỗi thao tác của quản
 * lý, không gọi thêm hàm nội bộ nào "cho chắc" (điều 15).
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/tuyen_dung_622.js
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
      { name: 'UV-1', vi_tri: 'VTT-0001', ten_vi_tri: 'Thu ngân ca tối', ho_ten: 'Nguyễn Văn An', sdt: '0909123456', nguon: 'Web Vagabond',
        trang_thai: 'Mới nhận', creation: '2026-10-29 07:00:00', qua_han: 1, lan_nop: 2, ca_ranh: 'Tối', khu_vuc: 'Quận 3', cham: [] },
      { name: 'UV-2', vi_tri: 'VTT-0001', ten_vi_tri: 'Thu ngân ca tối', ho_ten: 'Trần Thị Bình', sdt: '0912345678', nguon: 'QR tại cửa hàng',
        trang_thai: 'Mới nhận', creation: '2026-10-30 08:00:00', qua_han: 0, lan_nop: 1, cham: [] },
      { name: 'UV-3', vi_tri: 'VTT-0001', ten_vi_tri: 'Thu ngân ca tối', ho_ten: 'Lê Cường', sdt: '0987654321', nguon: 'TopCV',
        trang_thai: 'Hẹn phỏng vấn', lich_hen: HOM + ' 14:00:00', creation: '2026-10-28 08:00:00', qua_han: 0, lan_nop: 1,
        cham: [{ vong: 'Phỏng vấn', nguoi: 'Dễ', ket_luan: 'Cân nhắc', diem_tb: 2.5, nhan_xet: '' }] },
      { name: 'UV-4', vi_tri: 'VTT-0002', ten_vi_tri: 'Phụ bếp Pastry', ho_ten: 'Phạm Dũng', sdt: '0901111222', nguon: 'Đến trực tiếp',
        trang_thai: 'Làm thử', lich_hen: '2026-10-31 08:00:00', tien_cong_thu: 100000, da_tra_cong: 0, creation: '2026-10-27 08:00:00', qua_han: 0, lan_nop: 1, cham: [] },
    ],
  };
}
var QL = ['VGB - Quản lý cửa hàng'];
var QUAY = ['Sales User'];
var QR = [];

function dungMoi(vai, loi) {
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);
  var goi = [], toastDs = [], hoi = [], dieuHuong = [];
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, Number: Number, Date: Date, setTimeout: setTimeout, isNaN: isNaN, QR: QR,
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
      if (duong === 'vagabond.tuyen_dung.tong_quan') return Promise.resolve(duLieu());
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

(async function () {
  console.log('v622 Tuyển dụng: hồ sơ, cập nhật, chấm, công làm thử, vị trí bật tắt web');

  await ca('nhân viên quầy không có quyền: khoá màn, không hỏi máy chủ', async function () {
    var m = await mo(QUAY);
    dung('câu khoá', chu(m.khung).indexOf('chỉ mở cho quản lý') >= 0);
    bang('không gọi máy chủ', m.goi.length, 0);
  });

  await ca('quản lý mở màn: ba số đầu màn, chip trạng thái và vị trí, thẻ hồ sơ có Gọi, Nhắn, Cập nhật', async function () {
    var m = await mo();
    bang('tiêu đề', m.g._t, 'Tuyển dụng');
    var tom = m.khung.querySelectorAll('[data-tdtom]')[0];
    dung('có thẻ tóm tắt', !!tom);
    dung('chưa gọi 2, có dòng quá 24 giờ', /Chưa gọi2.*1 quá 24 giờ/.test(chu(tom)));
    dung('thẻ tóm tắt là lưới, không phải flex thiếu hướng', tom.style.display === 'grid');
    var chip = m.khung.querySelectorAll('[data-dscc]').map(function (x) { return x.getAttribute('data-dscc'); });
    dung('chip trạng thái', chip.indexOf('tt|Mới nhận') >= 0 && chip.indexOf('tt|Hẹn phỏng vấn') >= 0);
    dung('chip vị trí', chip.indexOf('vt|VTT-0001') >= 0 && chip.indexOf('vt|VTT-0002') >= 0);
    var t1 = the(m, 'UV-1');
    dung('hồ sơ quá 24 giờ ghi đỏ', chu(t1).indexOf('chưa ai gọi') >= 0);
    dung('nộp hai lần được báo', chu(t1).indexOf('nộp 2 lần') >= 0);
    bang('gọi', nut(t1, 'data-tdgoi').getAttribute('href'), 'tel:0909123456');
    dung('có nút Nhắn', !!nut(t1, 'data-tdnhan'));
    dung('có Cập nhật', !!nut(t1, 'data-tdcn'));
    dung('hồ sơ Mới nhận chưa có nút Chấm', !nut(t1, 'data-tdcham'));
    dung('hẹn phỏng vấn có nút Chấm và giờ hẹn', !!nut(the(m, 'UV-3'), 'data-tdcham') && chu(the(m, 'UV-3')).indexOf('14:00 30/10') >= 0);
    dung('làm thử chưa trả công có nút ghi trả', chu(nut(the(m, 'UV-4'), 'data-tdcong')).indexOf('Ghi đã trả công') >= 0);
    m.khung.querySelectorAll('[data-tdhs]').forEach(function (el) {
      (function soat(n) {
        if (n.style && n.style.display === 'flex') dung('dòng flex có hướng', !!n.style.flexDirection);
        (n.children || []).forEach(soat);
      })(el);
    });
  });

  await ca('bấm số Chưa gọi: chỉ còn hồ sơ Mới nhận, có dòng Đang lọc; Bỏ lọc trả hết', async function () {
    var m = await mo();
    bam(m.khung.querySelectorAll('[data-tdthe="moi"]')[0]);
    await tick();
    bang('còn hai hồ sơ mới', m.khung.querySelectorAll('[data-tdhs]').map(function (x) { return x.getAttribute('data-tdhs'); }), ['UV-1', 'UV-2']);
    dung('dòng Đang lọc', chu(m.khung.querySelectorAll('[data-tdloc]')[0]).indexOf('2 hồ sơ') >= 0);
    bam(m.khung.querySelectorAll('[data-tdbo]')[0]);
    await tick();
    bang('hết lọc', m.khung.querySelectorAll('[data-tdhs]').length, 4);
    dung('không còn dòng Đang lọc', !m.khung.querySelectorAll('[data-tdloc]').length);
  });

  await ca('Cập nhật: hẹn phỏng vấn mà chưa chọn giờ thì nhắc, không gửi; chọn giờ thì gửi đúng', async function () {
    var m = await mo();
    bam(nut(the(m, 'UV-1'), 'data-tdcn'));
    var s = sheet(m);
    bam(s.querySelectorAll('[data-tdchon="Hẹn phỏng vấn"]')[0]);
    dung('ô giờ hẹn hiện', s.querySelectorAll('[data-tdhen]')[0].style.display === 'block');
    bam(s.querySelectorAll('[data-tdok]')[0]);
    await tick();
    bang('chưa gửi', goiTen(m, 'cap_nhat').length, 0);
    dung('nhắc chọn giờ', m.toast.join('|').indexOf('ngày giờ hẹn') >= 0);
    s.querySelectorAll('#tdLichHen')[0].value = '2026-10-31T14:00';
    bam(s.querySelectorAll('[data-tdok]')[0]);
    await tick();
    var g = goiTen(m, 'cap_nhat')[0].ts;
    bang('gửi đúng', [g.name, g.trang_thai, g.lich_hen], ['UV-1', 'Hẹn phỏng vấn', '2026-10-31T14:00']);
  });

  await ca('Cập nhật: Dừng bắt lý do, bấm chip lý do là điền', async function () {
    var m = await mo();
    bam(nut(the(m, 'UV-2'), 'data-tdcn'));
    var s = sheet(m);
    bam(s.querySelectorAll('[data-tdchon="Dừng"]')[0]);
    bam(s.querySelectorAll('[data-tdok]')[0]);
    await tick();
    bang('chưa gửi khi thiếu lý do', goiTen(m, 'cap_nhat').length, 0);
    bam(s.querySelectorAll('[data-tdlymau="1"]')[0]);
    bam(s.querySelectorAll('[data-tdok]')[0]);
    await tick();
    bang('gửi lý do chip', goiTen(m, 'cap_nhat')[0].ts.ly_do, 'Ứng viên rút');
  });

  await ca('Chấm: thiếu tiêu chí thì nhắc; đủ tiêu chí và kết luận thì gửi điểm theo tên tiêu chí của vị trí', async function () {
    var m = await mo();
    bam(nut(the(m, 'UV-3'), 'data-tdcham'));
    var s = sheet(m);
    bam(s.querySelectorAll('[data-tdd="0|4"]')[0]);
    bam(s.querySelectorAll('[data-tdkl="Nên nhận"]')[0]);
    bam(s.querySelectorAll('[data-tdok]')[0]);
    await tick();
    bang('chưa gửi', goiTen(m, 'cham').length, 0);
    dung('nhắc tiêu chí còn thiếu', m.toast.join('|').indexOf('Nhanh nhẹn') >= 0);
    bam(s.querySelectorAll('[data-tdd="1|2"]')[0]);
    bam(s.querySelectorAll('[data-tdd="1|3"]')[0]);
    dung('đổi điểm thì chỉ một ô sáng trong hàng', s.querySelectorAll('[data-tdd="1|2"]')[0].getAttribute('aria-pressed') === 'false'
      && s.querySelectorAll('[data-tdd="1|3"]')[0].getAttribute('aria-pressed') === 'true'
      && s.querySelectorAll('[data-tdd="0|4"]')[0].getAttribute('aria-pressed') === 'true');
    bam(s.querySelectorAll('[data-tdok]')[0]);
    await tick();
    var g = goiTen(m, 'cham')[0].ts;
    bang('gửi đúng', [g.name, g.vong, JSON.parse(g.diem), g.ket_luan], ['UV-3', 'Phỏng vấn', { 'Thái độ': 4, 'Nhanh nhẹn': 3 }, 'Nên nhận']);
  });

  await ca('Công làm thử: Đã trả công gửi giờ, tiền gợi ý và da_tra 1', async function () {
    var m = await mo();
    bam(nut(the(m, 'UV-4'), 'data-tdcong'));
    var s = sheet(m);
    bang('giờ gợi ý', s.querySelectorAll('#tdGio')[0].value, '4');
    bang('tiền đã ghi', s.querySelectorAll('#tdTien')[0].value, '100000');
    dung('đã có tiền thì không còn nút trả sau', !s.querySelectorAll('[data-tdghi]').length);
    bam(s.querySelectorAll('[data-tdtra]')[0]);
    await tick();
    var g = goiTen(m, 'ghi_cong_thu')[0].ts;
    bang('gửi', [g.name, g.gio, g.tien, g.da_tra], ['UV-4', '4', '100000', 1]);
  });

  await ca('Vị trí: công tắc hỏi lại rồi tắt, web ẩn ngay; nút số hồ sơ lọc đúng vị trí', async function () {
    var m = await mo(QL, null, 'tdTab = "vt";');
    var tat = m.khung.querySelectorAll('[data-tdbat="0"]')[0];
    bang('công tắc đang bật', tat.getAttribute('aria-checked'), 'true');
    dung('có trạng thái web', chu(m.khung).indexOf('Khách đang thấy') >= 0);
    bam(tat);
    await tick(); await tick();
    dung('hỏi trước khi tắt', m.hoi[0].indexOf('Tắt Đang tuyển?') === 0 && m.hoi[0].indexOf('Web ẩn vị trí này ngay') >= 0);
    bang('gửi tắt', goiTen(m, 'bat_tat_vi_tri')[0].ts, { name: 'VTT-0001', bat: 0 });
    bam(m.khung.querySelectorAll('[data-tdhsvt="1"]')[0]);
    await tick();
    bang('sang thẻ hồ sơ, lọc vị trí 2', m.khung.querySelectorAll('[data-tdhs]').map(function (x) { return x.getAttribute('data-tdhs'); }), ['UV-4']);
  });

  await ca('Mã QR cửa hàng: vẽ từ link miền khách có nguồn qr', async function () {
    var m = await mo(QL, null, 'tdTab = "vt";');
    QR.length = 0;
    bam(m.khung.querySelectorAll('[data-tdqr]')[0]);
    await tick();
    bang('nội dung mã', QR, ['https://order.thevagabondpatisserie.com/ung-tuyen?nguon=qr']);
    dung('có ảnh', !!sheet(m).querySelectorAll('img')[0]);
  });

  await ca('Thêm vị trí: chưa có tên thì nhắc; điền tên rồi lưu gửi đúng dữ liệu, mặc định đang tuyển', async function () {
    var m = await mo(QL, null, 'tdTab = "vt";');
    bam(m.khung.querySelectorAll('[data-tdthemvt]')[0]);
    await tick();
    bang('tiêu đề', m.g._t, 'Thêm vị trí');
    var luu = m.khung.querySelectorAll('#tdLuuVt')[0];
    luu.onclick();
    await tick();
    dung('nhắc tên', m.toast.join('|').indexOf('Điền tên vị trí') >= 0);
    var o = m.khung.querySelectorAll('#tdTen')[0];
    o.value = 'Phụ bếp Baker';
    o.dispatchEvent(dg.suKien('input', {}, o));
    luu.onclick();
    await tick();
    var g = goiTen(m, 'luu_vi_tri')[0].ts, d = JSON.parse(g.du_lieu);
    bang('dữ liệu', [d.tieu_de, d.dang_tuyen, d.hinh_thuc, g.name], ['Phụ bếp Baker', 1, 'Toàn thời gian', '']);
  });

  await ca('Thêm hồ sơ tay: chưa bật ô ứng viên đồng ý thì không lưu', async function () {
    var m = await mo();
    bam(m.khung.querySelectorAll('[data-tdthemhs]')[0]);
    await tick();
    bang('tiêu đề', m.g._t, 'Thêm hồ sơ');
    m.khung.querySelectorAll('#tdLuuHs')[0].onclick();
    await tick();
    bang('không gửi', goiTen(m, 'them_ho_so').length, 0);
    dung('nhắc hỏi ứng viên', m.toast.join('|').indexOf('đồng ý lưu hồ sơ') >= 0);
  });

  await ca('Gọi: bấm Gọi (máy mở trình gọi), quay lại có bảng kết quả; bấm Không nghe máy là ghi nhật ký', async function () {
    var m = await mo();
    bam(nut(the(m, 'UV-1'), 'data-tdgoi'));
    dung('chưa hiện ngay (để máy mở trình gọi trước)', !sheet(m));
    await new Promise(function (r) { setTimeout(r, 760); });
    var s = sheet(m);
    dung('bảng kết quả cuộc gọi', !!s && chu(s).indexOf('Kết quả cuộc gọi') >= 0 && chu(s).indexOf('0909123456') >= 0);
    bang('bốn kết quả có giải thích', s.querySelectorAll('[data-tdkq]').length, 4);
    bam(s.querySelectorAll('[data-tdkq="2"]')[0]);
    await tick();
    bang('gửi đúng', goiTen(m, 'ghi_lien_he')[0].ts, { name: 'UV-1', kenh: 'Gọi', ket_qua: 'Không nghe máy', mau: '' });
  });

  await ca('Nhắn SMS: hồ sơ Hẹn phỏng vấn gợi sẵn mẫu hẹn, điền đủ tên, vị trí, giờ, nơi làm; mở SMS có sẵn tin, ghi nhật ký', async function () {
    var m = await mo();
    bam(nut(the(m, 'UV-3'), 'data-tdnhan'));
    var s = sheet(m);
    bang('mẫu gợi sẵn', s.querySelectorAll('[data-tdmau="hen_pv"]')[0].getAttribute('aria-pressed'), 'true');
    var tin = s.querySelectorAll('#tdNoiDungTin')[0].value;
    bang('nội dung', tin, 'Chào Lê Cường, hẹn phỏng vấn vị trí Thu ngân ca tối lúc 14:00 ngày 30/10 tại The Vagabond District 1. Gọi 0931 224 334.');
    bam(s.querySelectorAll('[data-tdsms]')[0]);
    await tick();
    var u = String(m.g.location.href || '');
    dung('mở SMS đúng số', u.indexOf('sms:0987654321?&body=') === 0);
    bang('tin trong SMS', decodeURIComponent(u.split('body=')[1]), tin);
    bang('ghi nhật ký', goiTen(m, 'ghi_lien_he')[0].ts, { name: 'UV-3', kenh: 'SMS', ket_qua: '', mau: 'hen_pv' });
  });

  await ca('Nhắn Zalo: đổi mẫu thì đổi chữ; sửa chữ rồi bấm là chép đúng chữ đã sửa và mở Zalo đúng số', async function () {
    var m = await mo();
    bam(nut(the(m, 'UV-4'), 'data-tdnhan'));
    var s = sheet(m), o = s.querySelectorAll('#tdNoiDungTin')[0];
    dung('mẫu làm thử có công đã ghi', o.value.indexOf('lúc 08:00 ngày 31/10 tại Xưởng sản xuất Tân Bình, có trả công 100.000đ') >= 0);
    bam(s.querySelectorAll('[data-tdmau="cam_on"]')[0]);
    bang('đổi mẫu', o.value, 'Chào Phạm Dũng, cảm ơn bạn đã ứng tuyển Phụ bếp Pastry.');
    o.value = o.value + ' Hẹn gặp lại.';
    bam(s.querySelectorAll('[data-tdzl]')[0]);
    await tick();
    bang('mở Zalo đúng số', m.g.moTab, ['https://zalo.me/0901111222']);
    bang('chép đúng chữ đã sửa', m.g.chep, ['Chào Phạm Dũng, cảm ơn bạn đã ứng tuyển Phụ bếp Pastry. Hẹn gặp lại.']);
    bang('ghi nhật ký', goiTen(m, 'ghi_lien_he')[0].ts, { name: 'UV-4', kenh: 'Zalo', ket_qua: '', mau: 'cam_on' });
  });

  await ca('điền mẫu (phép thuần): đủ sáu chỗ trống, thiếu giờ hay nơi làm thì nhắc điền, không để lại ngoặc', async function () {
    var m = dungMoi(QL);
    var ra = m.g.tdDienMau('{ten}|{vi_tri}|{gio}|{noi_lam}|{cong}|{hotline}', { ho_ten: 'An', ten_vi_tri: 'Thu ngân' }, {}, '0931 224 334');
    bang('điền', ra, 'An|Thu ngân|(điền giờ hẹn)|(điền nơi làm)|theo số giờ làm|0931 224 334');
    var rows = duLieu().rows;
    rows.push({ name: 'UV-5', trang_thai: 'Mới nhận', lien_he_luc: '2026-10-30 08:00:00', ho_ten: 'Gọi rồi', sdt: '0900000005' });
    bang('ô Chưa gọi bỏ hồ sơ đã gọi', m.g.tdLocHs(rows, { the: 'moi' }, HOM).map(function (r) { return r.name; }), ['UV-1', 'UV-2']);
  });

  await ca('phép lọc thuần: tìm số điện thoại, tìm tên bỏ dấu, lọc công chưa trả', async function () {
    var m = dungMoi(QL);
    var rows = duLieu().rows;
    bang('tìm số', m.g.tdLocHs(rows, { tim: '345 678' }, HOM).map(function (r) { return r.name; }), ['UV-2']);
    bang('tìm tên bỏ dấu', m.g.tdLocHs(rows, { tim: 'cuong' }, HOM).map(function (r) { return r.name; }), ['UV-3']);
    bang('công chưa trả', m.g.tdLocHs(rows, { the: 'cong' }, HOM).map(function (r) { return r.name; }), ['UV-4']);
    bang('hẹn hôm nay', m.g.tdLocHs(rows, { the: 'hen' }, HOM).map(function (r) { return r.name; }), ['UV-3']);
  });

  await ca('Codex #518: ô tìm lọc THÊM cùng chip vị trí và trạng thái, không bỏ qua chúng', async function () {
    var m = dungMoi(QL);
    var rows = duLieu().rows.concat([{ name: 'UV-6', vi_tri: 'VTT-0002', ten_vi_tri: 'Phụ bếp Pastry', ho_ten: 'Nguyễn Văn Bình', sdt: '0911000006', trang_thai: 'Dừng' }]);
    bang('tìm tên + vị trí 2', m.g.tdLocHs(rows, { tim: 'nguyen', vt: 'VTT-0002' }, HOM).map(function (r) { return r.name; }), ['UV-6']);
    bang('tìm tên + vị trí 2 + Mới nhận', m.g.tdLocHs(rows, { tim: 'nguyen', vt: 'VTT-0002', tt: 'Mới nhận' }, HOM).map(function (r) { return r.name; }), []);
    bang('tìm số + thẻ Chưa gọi', m.g.tdLocHs(rows, { tim: '0911', the: 'moi' }, HOM).map(function (r) { return r.name; }), []);
  });

  await ca('Codex #518: quá 8 vị trí thì Thêm hồ sơ mở bảng chọn có ô tìm, không xếp chip dài', async function () {
    var m = dungMoi(QL);
    var d = duLieu();
    for (var i = 3; i <= 9; i++) d.vi_tri.push({ name: 'VTT-000' + i, tieu_de: 'Vị trí ' + i, dang_tuyen: i % 2 });
    m.g.tdKq = d; m.g.tdVt = '';
    await m.g.scrTdThemHs();
    bang('không chip vị trí', m.khung.querySelectorAll('[data-tdhsvt2]').length, 0);
    var nutChon = m.khung.querySelectorAll('[data-tdhsvtchon]')[0];
    dung('nút chọn hiện vị trí đầu', chu(nutChon).indexOf('Thu ngân ca tối') >= 0);
    bam(nutChon);
    var b = m.g.bangChon[0];
    bang('bảng có ô tìm, đủ 9 vị trí, vị trí tắt có ghi chú', [b.tim, b.ds.length, b.ds[1].label], [true, 9, 'Phụ bếp Pastry (đang tắt)']);
    b.chon(b.ds[8]);
    await tick();
    dung('chọn xong hiện đúng vị trí', chu(m.khung.querySelectorAll('[data-tdhsvtchon]')[0]).indexOf('Vị trí 9') >= 0);
    m.g.tdKq = duLieu(); m.g.tdHsKhoiPhuc = null;
    await m.g.scrTdThemHs();
    bang('8 vị trí trở xuống vẫn là chip', m.khung.querySelectorAll('[data-tdhsvt2]').length, 2);
  });

  console.log('\n' + ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng.');
  process.exit(ket.hong ? 1 : 0);
})().catch(function (e) { console.log('NO TUNG: ' + (e && e.stack || e)); process.exit(1); });

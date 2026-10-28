/* Ca kiểm HÀNH VI v617: màn Danh sách khách hàng và thanh bước 1-2-3-4.
 *
 * Anh Việt 28/10/2026 gửi ảnh màn Danh sách khách hàng: chữ lệch tỷ lệ với ô ở
 * hàng hạng thành viên, và "Phần sales làm việc hay những chỗ có tiến độ thì
 * cần phải hiển thị thanh tiến độ kiểu 1, 2, 3, 4". Nạp THẬT các hàm của
 * 00-nen.js, 09, 11, 12, 08, 15 vào DOM giả; máy chủ giả chỉ trả dữ liệu dựng
 * sẵn và ghi lời gọi. Mỗi ca bấm đúng chuỗi thao tác của người dùng.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/khach_ds_617.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var BEP = path.resolve(__dirname, '..', '..', '..', 'public', 'js', 'bep');
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
var NEN = doc('00-nen.js'), POS = doc('09-tinh-tien-quay.js'), KH = doc('11-khach-ca-hop-dong.js');
var VD = doc('12-van-don.js'), DS = doc('08-doanh-so-sales.js'), KHUON = doc('15-khuon-danh-sach.js');
var HAM = ['h', 'money'].map(function (t) { return layHam(NEN, t); })
  .concat(['locTim', 'posChipNut'].map(function (t) { return layHam(POS, t); }))
  .concat(['khChipHang', 'khTongHtml', 'khDongHtml', 'scrKhachHang'].map(function (t) { return layHam(KH, t); }))
  .concat([layHam(VD, 'buocVanDon'), layHam(DS, 'buocDonBan'), layHam(KHUON, 'veBuoc')])
  .concat(["var khDang = '', khHang = '', khTim = '', khData = null, khDangGo = false, khMa = '';"]).join('\n');

function dungMoi(traLoi) {
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);
  var goi = [];
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, Number: Number, Date: Date, setTimeout: setTimeout, clearTimeout: clearTimeout, isNaN: isNaN,
    frame: function (t, html) { khung.innerHTML = html; khung.onclick = null; that._t = t; return khung; },
    go: function (fn) { return fn(); },
    scrKhachChiTiet: function () { that._mo = that.khMa; },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: ts });
      var f = traLoi[duong];
      return Promise.resolve(typeof f === 'function' ? f(ts) : JSON.parse(JSON.stringify(f || {})));
    },
  };
  that.window = that;
  vm.runInNewContext(HAM, that, { filename: 'ham.js' });
  return { g: that, tai: tai, khung: khung, goi: goi };
}

var ket = { dat: 0, hong: 0 };
function dung(mo, dk) { if (!dk) throw new Error(mo); }
function bang(mo, a, b) { var x = JSON.stringify(a), y = JSON.stringify(b); if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y); }
function tick() { return new Promise(function (r) { setTimeout(r, 5); }); }
async function choDen(dk) { for (var i = 0; i < 80 && !dk(); i++) await new Promise(function (r) { setTimeout(r, 25); }); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); }
}
function chu(el) { var s = el._chu || ''; (el.children || []).forEach(function (c) { s += chu(c); }); return s; }
function mot(el, chon) { return el.querySelectorAll(chon)[0]; }
function bam(el) { if (!el) throw new Error('khong co nut'); el.dispatchEvent(dg.suKien('click', {}, el)); }

var HANG = { hang: [
  { name: 'Vàng', ten_hang: 'Vàng', giam_gia: 5, anh: '/files/the-vang.png' },
  { name: 'Kim cương', ten_hang: 'Kim cương', giam_gia: 10, anh: '' }] };
function dsMay(ts) {
  /* Máy chủ đã xếp chi nhiều nhất lên đầu và cộng tổng trên ĐỦ nhóm: 4.812
     khách, dòng tổng không phải tổng của 3 dòng trả về. */
  return { tong_so: 4812, so_si: 12, so_le: 4800, tong_tien: 987654321, da_tai: 3,
    khach: [
      { ma: 'KH-9', ten: 'Trần Văn Tý', si: 0, hang: 'Kim cương', tien: 52000000, tien_erp: 2000000, tieu_cu: 50000000, so_don: 4, dt: '0909123456' },
      { ma: 'KH-3', ten: 'Công ty ABC', si: 1, hang: '', tien: 6151500, tien_erp: 0, tieu_cu: 6151500, so_don: 0, mst: '0312345678' },
      { ma: 'KH-1', ten: 'An', si: 0, hang: 'Vàng', tien: 0, tien_erp: 0, tieu_cu: 0, so_don: 0 }] };
}

(async function () {
  console.log('v617 Danh sách khách hàng và thanh bước');

  await ca('dòng tổng là số máy chủ cộng trên đủ nhóm, không cộng lại từ dòng đã tải', async function () {
    var m = dungMoi({ 'vagabond.khach_hang.ds_khach': dsMay, 'vagabond.khach_hang.ds_hang': HANG });
    await m.g.scrKhachHang();
    var t = chu(mot(m.khung, '[data-khtong]'));
    dung('số khách của nhóm: ' + t, t.indexOf('4.812 khách') >= 0 && t.indexOf('12 sỉ · 4.800 lẻ') >= 0);
    dung('chi tiêu cả nhóm', t.indexOf('987.654.321 đ') >= 0);
    dung('nói rõ đang hiện bao nhiêu', chu(m.khung).indexOf('đang hiện 3 khách chi nhiều nhất') >= 0);
  });

  await ca('giữ đúng thứ tự máy chủ (chi nhiều nhất trước), khách chỉ có chi tiêu Fabi ghi rõ, khách chưa mua ghi rõ', async function () {
    var m = dungMoi({ 'vagabond.khach_hang.ds_khach': dsMay, 'vagabond.khach_hang.ds_hang': HANG });
    await m.g.scrKhachHang();
    bang('thứ tự', m.khung.querySelectorAll('[data-khx]').map(function (x) { return x.getAttribute('data-khx'); }), ['KH-9', 'KH-3', 'KH-1']);
    var d3 = chu(mot(m.khung, '[data-khx="KH-3"]'));
    dung('Fabi: không ghi 0 hoá đơn', d3.indexOf('chi tiêu cũ Fabi') >= 0 && d3.indexOf('0 hoá đơn') < 0);
    dung('chưa mua', chu(mot(m.khung, '[data-khx="KH-1"]')).indexOf('chưa mua 12 tháng') >= 0);
    dung('có hoá đơn thì đếm', chu(mot(m.khung, '[data-khx="KH-9"]')).indexOf('4 hoá đơn') >= 0);
    dung('chip hạng ghi tên và giảm', chu(mot(m.khung, '[data-khx="KH-9"]')).indexOf('Kim cương · giảm 10%') >= 0);
    dung('chưa xếp hạng nói rõ', d3.indexOf('chưa xếp hạng') >= 0);
  });

  await ca('chip hạng: ảnh thẻ và chữ cùng một khuôn .chip-anh; không còn nhãn 8px dưới thẻ', async function () {
    var m = dungMoi({ 'vagabond.khach_hang.ds_khach': dsMay, 'vagabond.khach_hang.ds_hang': HANG });
    await m.g.scrKhachHang();
    var c = mot(m.khung, '[data-khh="Vàng"]');
    dung('chip có khuôn ảnh và chữ', !!mot(c, '.chip-anh') && !!mot(c, 'img') && chu(c).indexOf('Vàng · −5%') >= 0);
    dung('không còn cỡ chữ 8px', m.khung.innerHTML.indexOf('font-size:8px') < 0);
    dung('hàng chip cuộn ngang, không cắt', m.khung.querySelectorAll('.cuon-ngang').length === 2);
    var o = m.tai.getElementById('khO');
    bang('ô tìm đúng khuôn', [o.getAttribute('type'), o.getAttribute('class')], ['search', 'tin tim']);
  });

  await ca('bấm chip Khách sỉ hỏi máy chủ đúng nhóm; chip đang chọn được đánh dấu', async function () {
    var m = dungMoi({ 'vagabond.khach_hang.ds_khach': dsMay, 'vagabond.khach_hang.ds_hang': HANG });
    await m.g.scrKhachHang();
    bam(mot(m.khung, '[data-khd="si"]'));
    await choDen(function () { return m.goi.filter(function (x) { return x.duong === 'vagabond.khach_hang.ds_khach'; }).length > 1; });
    await tick();
    var g = m.goi.filter(function (x) { return x.duong === 'vagabond.khach_hang.ds_khach'; });
    bang('hỏi nhóm sỉ', g[1].ts, { tu_khoa: '', dang: 'si', hang: '' });
    bang('chip sỉ đang chọn', mot(m.khung, '[data-khd="si"]').getAttribute('data-chipchon'), '1');
  });

  await ca('thanh bước dùng chung: bước trước xanh, bước đang làm có dấu, bước lỗi đỏ, xong hết thì xanh cả', async function () {
    var m = dungMoi({});
    m.khung.innerHTML = m.g.veBuoc([{ ten: 'A' }, { ten: 'B', n: 3 }, { ten: 'C' }], 1, 'Thử');
    var b = mot(m.khung, '.buoc');
    bang('trạng thái', b.querySelectorAll('.b').map(function (x) { return x.getAttribute('class'); }), ['b xong', 'b dang', 'b cho']);
    bang('đánh số 1 2 3, bước xong có dấu tích', b.querySelectorAll('.so').map(chu), ['✓', '2', '3']);
    bang('đếm', chu(mot(b, '.n')), '3');
    bang('bước đang làm', mot(b, '[aria-current="step"]').getAttribute('data-buocso'), '2');
    m.khung.innerHTML = m.g.veBuoc([{ ten: 'A' }, { ten: 'B', loi: 1 }], 1);
    bang('lỗi: lớp đỏ và dấu chấm than', [m.khung.querySelectorAll('.b')[1].getAttribute('class'), chu(m.khung.querySelectorAll('.so')[1])], ['b loi', '!']);
    m.khung.innerHTML = m.g.veBuoc([{ ten: 'A' }, { ten: 'B' }], 2);
    bang('xong hết', m.khung.querySelectorAll('.b.xong').length, 2);
  });

  await ca('vận đơn: giao tận nơi 4 bước theo trạng thái; khách tự lấy 3 bước; huỷ và không giao được tô đỏ', async function () {
    var m = dungMoi({});
    var t = function (d) { var r = m.g.buocVanDon(d); return [r.buoc.map(function (b) { return b.ten + (b.loi ? '!' : ''); }).join('>'), r.hienTai]; };
    bang('mới tạo', t({ trang_thai: 'Chờ giao' }), ['Tạo vận đơn>Phân công>Đang giao>Đã giao', 1]);
    bang('đã có tài xế', t({ trang_thai: 'Chờ giao', shipper: 'Tài' }), ['Tạo vận đơn>Phân công>Đang giao>Đã giao', 2]);
    bang('đã giao: xong cả 4', t({ trang_thai: 'Đã giao' })[1], 4);
    bang('không giao được', t({ trang_thai: 'Không giao được' }), ['Tạo vận đơn>Phân công>Không giao được!>Đã giao', 2]);
    bang('khách tự lấy', t({ trang_thai: 'Chờ khách lấy' }), ['Tạo vận đơn>Chờ khách lấy>Khách đã lấy', 1]);
    bang('khách đã lấy', t({ kenh: 'Khách tự lấy', trang_thai: 'Đã giao' })[1], 3);
    bang('huỷ', t({ trang_thai: 'Huỷ' }), ['Tạo vận đơn>Đã huỷ!', 1]);
  });

  await ca('đơn bán Sales: Nhận đơn, Thanh toán, Ghi sổ, Hoá đơn điện tử theo đúng ô của hoá đơn', async function () {
    var m = dungMoi({});
    var t = function (d) { var r = m.g.buocDonBan(d); return [r.buoc.map(function (b) { return b.ten + (b.loi ? '!' : ''); }).join('>'), r.dang]; };
    bang('nháp chưa chọn cách trả', t({ docstatus: 0 })[1], 1);
    bang('đã chọn cách trả: chờ ghi sổ', t({ docstatus: 0, vgb_pt_thanh_toan: 'Tiền mặt' })[1], 2);
    bang('đã ghi sổ, chưa HĐĐT', t({ docstatus: 1 })[1], 3);
    bang('đã có HĐĐT: xong cả 4', t({ docstatus: 1, custom_hddt_so: '123' })[1], 4);
    bang('HĐĐT cần đối chiếu: đỏ', t({ docstatus: 1, vgb_hddt_cho_doi_chieu: 1 })[0], 'Nhận đơn>Thanh toán>Ghi sổ>Hoá đơn điện tử!');
    bang('đơn huỷ', t({ vgb_huy: 1 }), ['Nhận đơn>Đã huỷ!', 1]);
  });

  console.log('\n' + ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng.');
  process.exit(ket.hong ? 1 : 0);
})();

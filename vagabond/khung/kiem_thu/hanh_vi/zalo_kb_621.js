/* Ca kiểm HÀNH VI v621: màn Tin Zalo tự động trong phân hệ Khách hàng.
 *
 * Nạp THẬT 58-crm.js cùng các hàm nền nó dùng vào DOM giả (cùng khuôn với
 * crm_614.js). Máy chủ giả trả đúng hình dạng vagabond/zalo_kich_ban.py và ghi
 * lại lời gọi; luật gửi, trần, hạn mức, đồng ý chạy thật ở
 * thu_zalo_kich_ban_621.py. Mỗi ca bấm đúng chuỗi thao tác của quản lý, không
 * gọi thêm hàm nội bộ nào "cho chắc".
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/zalo_kb_621.js
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
var KM = doc('13-khuyen-mai.js'), KHO = doc('03-kho-chung-tu.js'), TC = doc('02-trang-chu.js');
var MAN = doc('58-crm.js');

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
var HAM = ['h', 'money', 'today', 'vgbChuan', 'vgbKhop', 'anhMon', 'sheet'].map(function (t) { return layHam(NEN, t); })
  .concat([layHam(POS, 'posChipNut')])
  .concat(['dsccHang', 'dsCongCu', 'dsCongCuNoi', 'veBuoc'].map(function (t) { return layHam(KHUON, t); }))
  .concat(['var scanBarcode = function () { return Promise.resolve(null); };'])
  .concat([layHam(KM, 'kmHangChip'), layHam(KHO, 'errMsg')]).join('\n');

var QL = ['Sales Manager'];
var SALES = ['Sales User'];
var P = 'vagabond.zalo_kich_ban.';

function dlMau(them) {
  var d = {
    sua: 1, ctkm: [{ name: 'KM-SN', ten: 'Quà sinh nhật 10%' }, { name: 'KM-QL', ten: 'Mời quay lại 50k' }],
    han_muc: { ok: 1, ngay: 5000, con_ngay: 4999, km_thang: 0, con_km_thang: 0, con_km_ngay: 0, km_thang_sau: 0 },
    ds: [
      { ma: 'sau_mua', ten: 'Cảm ơn sau mua hàng, báo điểm', giai_thich: 'Gửi một lần cho mỗi hoá đơn có tích điểm.', km: 0, bat: 1, san_sang: 1, ly_do: '',
        ma_mau: '659376', mau_trang_thai: 'Đã duyệt', mau_duyet: 1, mau_ly_do: '', mau_gia: '400', tham_so: [], so_ngay: 0, nhac_lai_ngay: 0, ctkm: '',
        han_ngay: 14, ten_uu_dai: '', dieu_kien: '', tran_ngay: 300, gio_tu: 8, gio_den: 20, ket_qua_luot: '10:05 29/10 Đã gửi 3 tin.',
        dem: { hom_nay: { 'Đã gửi': 3, 'Chờ gửi': 1 }, ba_muoi: { 'Đã gửi': 3 }, phi: 1200 } },
      { ma: 'sinh_nhat', ten: 'Chúc mừng sinh nhật kèm voucher', giai_thich: 'Gửi trước sinh nhật.', km: 1, bat: 0, san_sang: 0, ly_do: 'Kịch bản đang tắt.',
        ma_mau: '659377', mau_trang_thai: 'Đang chờ Zalo duyệt', mau_duyet: 0, mau_ly_do: '', mau_gia: '500', tham_so: [], so_ngay: 3, nhac_lai_ngay: 0, ctkm: '',
        han_ngay: 14, ten_uu_dai: '', dieu_kien: '', tran_ngay: 300, gio_tu: 8, gio_den: 20, ket_qua_luot: '', dem: {} },
      { ma: 'quay_lai', ten: 'Mời khách lâu chưa quay lại', giai_thich: 'Khách quá số ngày chưa mua.', km: 1, bat: 0, san_sang: 0, ly_do: 'Kịch bản đang tắt.',
        ma_mau: '659378', mau_trang_thai: 'Bị từ chối', mau_duyet: 0, mau_ly_do: 'Nội dung chưa rõ ràng', mau_gia: '500', tham_so: [], so_ngay: 60, nhac_lai_ngay: 120,
        ctkm: 'KM-QL', han_ngay: 14, ten_uu_dai: '', dieu_kien: '', tran_ngay: 300, gio_tu: 8, gio_den: 20, ket_qua_luot: '', dem: {} }
    ]
  };
  Object.keys(them || {}).forEach(function (k) { d[k] = them[k]; });
  return d;
}

function dungMoi(vai, traLoi) {
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);
  var goi = [], toastDs = [], hoi = [];
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, Number: Number, Date: Date, setTimeout: setTimeout, isNaN: isNaN, parseInt: parseInt,
    navigator: {}, S: { roles: vai, stack: [] }, khMa: '',
    scrKhachChiTiet: function () { that._moKh = that.khMa; },
    hasRole: function (r) { return vai.indexOf(r) >= 0; },
    frame: function (t, html) { khung.innerHTML = html; khung._nghe = {}; khung.onclick = null; that._t = t; return khung; },
    go: function (fn) { return fn(); },
    busy: function () {},
    toast: function (m) { toastDs.push(m); },
    baoTin: function (m, t) { toastDs.push('BAOTIN ' + t + '|' + m); },
    hoiCo: function (t, m) { hoi.push(t + '|' + m); return Promise.resolve(that._dongY !== false); },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: ts });
      var f = (traLoi || {})[duong.replace(P, '')];
      if (typeof f === 'function') { try { return Promise.resolve(f(ts)); } catch (e) { return Promise.reject(e); } }
      if (f !== undefined) return Promise.resolve(JSON.parse(JSON.stringify(f)));
      return Promise.resolve(dlMau());
    },
  };
  that.window = that;
  vm.runInNewContext(HAM, that, { filename: 'ham-nen.js' });
  vm.runInNewContext(MAN, that, { filename: '58-crm.js' });
  return { g: that, tai: tai, khung: khung, goi: goi, toast: toastDs, hoi: hoi };
}

var ket = { dat: 0, hong: 0 };
function dung(mo, dk) { if (!dk) throw new Error(mo); }
function bang(mo, a, b) { var x = JSON.stringify(a), y = JSON.stringify(b); if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y); }
async function choDen(dk) { for (var i = 0; i < 80 && !dk(); i++) await new Promise(function (r) { setTimeout(r, 10); }); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); }
}
function chu(el) { var s = el._chu || ''; (el.children || []).forEach(function (c) { s += chu(c); }); return s; }
function sheet(m) { var ds = m.tai.body.children; return ds.length > 1 ? ds[ds.length - 1] : null; }
function bam(m, el) { if (!el) throw new Error('khong co nut de bam'); el.dispatchEvent(dg.suKien('click', {}, el)); }
function goiTen(m, t) { return m.goi.filter(function (x) { return x.duong === P + t; }); }
function mot(el, chon) { return el.querySelectorAll(chon)[0]; }

(async function () {
  console.log('v621 Tin Zalo tự động: màn trong phân hệ Khách hàng');

  await ca('màn: ba thẻ kịch bản đúng trạng thái, mẫu, số đếm; hạn mức khuyến mãi 0 thì nói rõ; KHÔNG có ô soạn tin tự do', async function () {
    var m = dungMoi(QL);
    await m.g.scrCrmZalo();
    var t = chu(m.khung);
    bang('tiêu đề', m.g._t, 'Tin Zalo tự động');
    bang('ba thẻ', m.khung.querySelectorAll('[data-crmzlthe]').length, 3);
    dung('đang chạy', t.indexOf('Đang chạy') >= 0);
    dung('đang tắt', t.indexOf('Đang tắt') >= 0);
    dung('mẫu chờ duyệt hiện chữ', t.indexOf('Đang chờ Zalo duyệt') >= 0);
    dung('mẫu bị từ chối kèm lý do Zalo ghi', t.indexOf('Zalo ghi: Nội dung chưa rõ ràng') >= 0);
    var dem = mot(m.khung, '[data-crmzldem="sau_mua"]').querySelectorAll('b').map(function (b) { return chu(b); });
    bang('số đếm hôm nay: gửi, chờ, lỗi', dem, ['3', '1', '0']);
    dung('hạn mức 0 có câu giải thích', t.indexOf('Zalo chưa cấp hạn mức tin khuyến mãi') >= 0);
    dung('không có ô soạn tin', m.khung.querySelectorAll('textarea').length === 0);
    bang('hỏi máy chủ đúng một lần', goiTen(m, 'ds_kich_ban').length, 1);
  });

  await ca('vai chỉ xem: không công tắc, không Cài đặt, không Gửi thử; vẫn xem được tin đã gửi', async function () {
    var m = dungMoi(SALES, { ds_kich_ban: dlMau({ sua: 0 }) });
    await m.g.scrCrmZalo();
    bang('không công tắc', m.khung.querySelectorAll('[data-crmzlbat]').length, 0);
    bang('không cài đặt', m.khung.querySelectorAll('[data-crmzlcd]').length, 0);
    bang('không gửi thử', m.khung.querySelectorAll('[data-crmzlthu]').length, 0);
    bang('vẫn có tin đã gửi', m.khung.querySelectorAll('[data-crmzltin]').length, 3);
    dung('có câu nói ai được sửa', chu(m.khung).indexOf('Chỉ Sales Manager và quản trị') >= 0);
  });

  await ca('bật công tắc: hỏi xác nhận nói rõ máy sẽ gửi tin thật; đồng ý thì lưu bat=1; bấm Thôi thì không gọi máy chủ', async function () {
    var m = dungMoi(QL);
    await m.g.scrCrmZalo();
    m.g._dongY = false;
    bam(m, mot(m.khung, '[data-crmzlbat="sinh_nhat"]'));
    await choDen(function () { return m.hoi.length; });
    bang('Thôi: không lưu', goiTen(m, 'luu_kich_ban').length, 0);
    dung('câu hỏi nói phát voucher và trần', m.hoi[0].indexOf('phát voucher') >= 0 && m.hoi[0].indexOf('300 tin mỗi ngày') >= 0);
    dung('mẫu chưa duyệt thì nói máy chờ', m.hoi[0].indexOf('chưa được Zalo duyệt') >= 0);
    m.g._dongY = true;
    bam(m, mot(m.khung, '[data-crmzlbat="sinh_nhat"]'));
    await choDen(function () { return goiTen(m, 'luu_kich_ban').length; });
    var g = goiTen(m, 'luu_kich_ban')[0].ts;
    bang('lưu đúng kịch bản và bật', [g.ma, JSON.parse(g.dat)], ['sinh_nhat', { bat: 1 }]);
  });

  await ca('tắt công tắc: không hỏi, lưu bat=0', async function () {
    var m = dungMoi(QL);
    await m.g.scrCrmZalo();
    bam(m, mot(m.khung, '[data-crmzlbat="sau_mua"]'));
    await choDen(function () { return goiTen(m, 'luu_kich_ban').length; });
    bang('không hỏi', m.hoi.length, 0);
    bang('tắt', JSON.parse(goiTen(m, 'luu_kich_ban')[0].ts.dat), { bat: 0 });
  });

  await ca('cài đặt sinh nhật: chọn chương trình không làm mất số vừa gõ; lưu gửi đủ ô, đúng chương trình', async function () {
    var m = dungMoi(QL);
    await m.g.scrCrmZalo();
    bam(m, mot(m.khung, '[data-crmzlcd="sinh_nhat"]'));
    var sh = sheet(m);
    dung('có ô số ngày trước sinh nhật', chu(sh).indexOf('GỬI TRƯỚC SINH NHẬT') >= 0);
    dung('không có ô không gửi lại (chỉ của quay lại)', !mot(sh, '#crmZlNhac'));
    mot(sh, '#crmZlTran').value = '150';
    mot(sh, '#crmZlNgay').value = '5';
    bam(m, mot(sh, '[data-crmzlkm="KM-SN"]'));
    bang('số vừa gõ còn nguyên', [mot(sheet(m), '#crmZlTran').value, mot(sheet(m), '#crmZlNgay').value], ['150', '5']);
    mot(sheet(m), '#crmZlTenUd').value = 'Quà sinh nhật';
    bam(m, mot(sheet(m), '[data-crmzlluu]'));
    await choDen(function () { return goiTen(m, 'luu_kich_ban').length; });
    var dat = JSON.parse(goiTen(m, 'luu_kich_ban')[0].ts.dat);
    bang('ô lưu', [dat.ctkm, dat.tran_ngay, dat.so_ngay, dat.ten_uu_dai, dat.ma_mau, dat.gio_tu, dat.gio_den],
      ['KM-SN', '150', '5', 'Quà sinh nhật', '659377', '8', '20']);
  });

  await ca('PR517 Codex: hơn 8 chương trình thì hiện thẻ chọn, mở tấm có ô tìm; gõ tìm, chọn, số vừa gõ còn nguyên, lưu đúng chương trình', async function () {
    /* Tái hiện finding Codex trên 5ed80e8: 12 chương trình đổ thành 12 chip,
       không có ô tìm (AGENTS.md mục 2b.2: hơn 8 lựa chọn phải mở tấm có ô tìm). */
    var nhieu = [];
    for (var i = 1; i <= 12; i++) nhieu.push({ name: 'KM-' + i, ten: 'Chương trình ' + i, phu: 'Đến hết 30/11/2026' });
    nhieu.push({ name: 'KM-SN', ten: 'Quà sinh nhật 10%', phu: 'Không giới hạn ngày' });
    var m = dungMoi(QL, { ds_kich_ban: dlMau({ ctkm: nhieu }) });
    await m.g.scrCrmZalo();
    bam(m, mot(m.khung, '[data-crmzlcd="sinh_nhat"]'));
    var sh = sheet(m);
    bang('không đổ chip', sh.querySelectorAll('[data-crmzlkm]').length, 0);
    var the = mot(sh, '[data-crmzlkmchon]');
    dung('có thẻ chọn', !!the);
    dung('thẻ mời chọn khi chưa chọn', chu(the).indexOf('Chọn chương trình') >= 0);
    mot(sh, '#crmZlTran').value = '120';
    bam(m, the);
    var tam = sheet(m);
    var o = mot(tam, 'input');
    dung('tấm có ô tìm', !!o);
    bang('tấm liệt kê đủ', tam.querySelectorAll('.shi').length, 13);
    o.value = 'sinh nhat';
    o.oninput();
    var hang = tam.querySelectorAll('.shi');
    bang('gõ không dấu vẫn tìm ra', hang.map(function (x) { return chu(x).indexOf('Quà sinh nhật 10%') >= 0; }), [true]);
    bam(m, hang[0]);
    var sh2 = sheet(m);
    dung('thẻ hiện chương trình vừa chọn', chu(mot(sh2, '[data-crmzlkmchon]')).indexOf('Quà sinh nhật 10%') >= 0);
    bang('số vừa gõ còn nguyên', mot(sh2, '#crmZlTran').value, '120');
    bam(m, mot(sh2, '[data-crmzlluu]'));
    await choDen(function () { return goiTen(m, 'luu_kich_ban').length; });
    var dat = JSON.parse(goiTen(m, 'luu_kich_ban')[0].ts.dat);
    bang('lưu đúng', [dat.ctkm, dat.tran_ngay], ['KM-SN', '120']);
  });

  await ca('PR517: chương trình đã chọn không còn trong danh sách (hết hạn, đã tắt) thì nói rõ phải chọn lại', async function () {
    var m = dungMoi(QL);
    await m.g.scrCrmZalo();
    bam(m, mot(m.khung, '[data-crmzlcd="quay_lai"]'));
    dung('không cảnh báo khi còn', chu(sheet(m)).indexOf('chọn lại') < 0);
    var d = dlMau(); d.ds[2].ctkm = 'KM-CU';
    m = dungMoi(QL, { ds_kich_ban: d });
    await m.g.scrCrmZalo();
    bam(m, mot(m.khung, '[data-crmzlcd="quay_lai"]'));
    dung('có câu chọn lại', chu(sheet(m)).indexOf('đã hết hạn hoặc đã tắt, chọn lại') >= 0);
    dung('không hiện mã nội bộ', chu(sheet(m)).indexOf('KM-CU') < 0);
  });

  await ca('cài đặt sau mua: không có ô chương trình, voucher, số ngày', async function () {
    var m = dungMoi(QL);
    await m.g.scrCrmZalo();
    bam(m, mot(m.khung, '[data-crmzlcd="sau_mua"]'));
    var sh = sheet(m);
    bang('không ô voucher', [!!mot(sh, '#crmZlHan'), !!mot(sh, '#crmZlNgay'), sh.querySelectorAll('[data-crmzlkm]').length], [false, false, 0]);
    bam(m, mot(sh, '[data-crmzlluu]'));
    await choDen(function () { return goiTen(m, 'luu_kich_ban').length; });
    var dat = JSON.parse(goiTen(m, 'luu_kich_ban')[0].ts.dat);
    bang('không gửi ô của tin khuyến mãi', [dat.ctkm, dat.so_ngay, dat.ten_uu_dai], [undefined, undefined, undefined]);
  });

  await ca('gửi thử: mẫu đã duyệt thì gửi đúng số đã gõ; mẫu chưa duyệt thì nút khoá', async function () {
    var m = dungMoi(QL, { gui_thu: { ok: 1, loi: '', sdt: '•••• 6556' } });
    await m.g.scrCrmZalo();
    bam(m, mot(m.khung, '[data-crmzlthu="sau_mua"]'));
    mot(sheet(m), '#crmZlSdt').value = '0901486556';
    bam(m, mot(sheet(m), '[data-crmzlgui]'));
    await choDen(function () { return goiTen(m, 'gui_thu').length; });
    bang('gửi', goiTen(m, 'gui_thu')[0].ts, { ma: 'sau_mua', sdt: '0901486556' });
    await choDen(function () { return m.toast.length; });
    dung('báo đã gửi', m.toast[m.toast.length - 1].indexOf('Đã gửi tin thử tới •••• 6556') >= 0);
    bam(m, mot(m.khung, '[data-crmzlthu="sinh_nhat"]'));
    var nut = mot(sheet(m), '[data-crmzlgui]');
    dung('nút khoá', nut.getAttribute('disabled') != null);
  });

  await ca('tin đã gửi: mở đúng kịch bản; chip Lỗi hỏi máy chủ lọc Lỗi; bấm dòng mở hồ sơ khách', async function () {
    var m = dungMoi(['Sales Manager', 'System Manager'], { ds_tin: function (ts) {
      return { ds: [{ kich_ban: 'sau_mua', khach: 'KH-1', ten_khach: 'Lan Anh', sdt: '•••• 6556', hoa_don: 'HDB-1', voucher: '', trang_thai: ts.trang_thai || 'Đã gửi',
        loi: ts.trang_thai === 'Lỗi' ? 'Số này chưa dùng Zalo (mã -118)' : '', luc: '2026-10-29 10:05:00' }], con_nua: 0 }; } });
    await m.g.scrCrmZalo();
    bam(m, mot(m.khung, '[data-crmzltin="sau_mua"]'));
    await choDen(function () { return chu(m.khung).indexOf('Lan Anh') >= 0; });
    bang('đúng kịch bản', goiTen(m, 'ds_tin')[0].ts.ma, 'sau_mua');
    dung('dòng có hoá đơn', chu(m.khung).indexOf('HDB-1') >= 0);
    var nutLoi = m.khung.querySelectorAll('button').filter(function (b) { return chu(b).indexOf('Lỗi') >= 0; })[0];
    bam(m, nutLoi);
    await choDen(function () { return chu(m.khung).indexOf('mã -118') >= 0; });
    bang('lọc Lỗi', goiTen(m, 'ds_tin')[1].ts.trang_thai, 'Lỗi');
    dung('hiện lý do lỗi', chu(m.khung).indexOf('mã -118') >= 0);
    bam(m, mot(m.khung, '[data-crmzltinkh="KH-1"]'));
    bang('mở hồ sơ', m.g._moKh, 'KH-1');
  });

  await ca('PR517 Codex vòng 2: sổ tin có ô tìm (tên, số, hoá đơn, voucher); tìm hỏi máy chủ; mở kịch bản khác thì ô tìm trống', async function () {
    /* Tái hiện finding Codex trên 87c103b: màn sổ tin chỉ có chip trạng thái
       và nút tải thêm 50 dòng, không có ô tìm (AGENTS.md 2b.5). */
    var m = dungMoi(QL, { ds_tin: function (ts) {
      var ds = ts.tim ? [{ kich_ban: 'sau_mua', khach: 'KH-9', ten_khach: 'Bảo Ngọc', sdt: '•••• 1234', hoa_don: 'HDB-26-0012', voucher: '', trang_thai: 'Đã gửi', loi: '', luc: '2026-10-20 10:05:00' }]
        : [{ kich_ban: 'sau_mua', khach: 'KH-1', ten_khach: 'Lan Anh', sdt: '•••• 6556', hoa_don: 'HDB-1', voucher: '', trang_thai: 'Đã gửi', loi: '', luc: '2026-10-29 10:05:00' }];
      return { ds: ds, con_nua: ts.tim ? 0 : 1 }; } });
    await m.g.scrCrmZalo();
    bam(m, mot(m.khung, '[data-crmzltin="sau_mua"]'));
    await choDen(function () { return chu(m.khung).indexOf('Lan Anh') >= 0; });
    var o = mot(m.khung, '#crmZlTinDsTim');
    dung('có ô tìm', !!o);
    dung('gợi ý nói tìm được gì', (o.getAttribute('placeholder') || '').indexOf('hoá đơn') >= 0);
    o.value = 'HDB-26-0012';
    o.dispatchEvent(dg.suKien('change', {}, o));
    await choDen(function () { return chu(m.khung).indexOf('Bảo Ngọc') >= 0; });
    var g = goiTen(m, 'ds_tin');
    bang('hỏi máy chủ đúng chữ tìm, từ đầu', [g[g.length - 1].ts.tim, g[g.length - 1].ts.bat_dau], ['HDB-26-0012', 0]);
    dung('ra dòng cũ chưa tải', chu(m.khung).indexOf('HDB-26-0012') >= 0);
    bang('ô tìm giữ chữ', mot(m.khung, '#crmZlTinDsTim').value, 'HDB-26-0012');
    await m.g.scrCrmZalo();
    bam(m, mot(m.khung, '[data-crmzltin="sinh_nhat"]'));
    await choDen(function () { return goiTen(m, 'ds_tin').length >= 3; });
    var g2 = goiTen(m, 'ds_tin');
    bang('mở kịch bản khác: không tìm, không lọc', [g2[g2.length - 1].ts.ma, g2[g2.length - 1].ts.tim, g2[g2.length - 1].ts.trang_thai], ['sinh_nhat', '', '']);
  });

  await ca('đường vào: thẻ Tin Zalo tự động có trong phân hệ Khách hàng, đường dẫn tin-zalo-tu-dong mở màn này', async function () {
    var nhom = TC.slice(TC.indexOf("k: 'KHG'"), TC.indexOf("k: 'KHG'") + 600);
    dung('có trong danh sách khoá của phân hệ', /keys: \[[^\]]*'CRMZL'/.test(nhom));
    var duong = {}; vm.runInNewContext('var X = {' + TC.slice(TC.indexOf("'cai-dat-cuoi-ngay'"), TC.indexOf("'ton-kho'")) + '};', duong);
    bang('đường dẫn', duong.X['tin-zalo-tu-dong'], 'CRMZL');
    var mo = [];
    var g = { go: function (f) { mo.push(f); }, scrCrmZalo: function () { mo.push('ZL'); } };
    vm.runInNewContext("function moKey(k) {\n" + TC.slice(TC.indexOf("  if (k === 'CRMZL')"), TC.indexOf("  if (k === 'CRMZL')") + 50).split('\n')[0] + '\n}', g);
    g.moKey('CRMZL');
    bang('mở đúng màn', mo.length === 1 && mo[0] === g.scrCrmZalo, true);
  });

  console.log('\n' + ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng.');
  process.exit(ket.hong ? 1 : 0);
})();

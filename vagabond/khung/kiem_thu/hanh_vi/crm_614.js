/* Ca kiểm HÀNH VI v614: phân hệ Khách hàng (CRM) đợt 1.
 *
 * Anh Việt 27/10/2026 duyệt 8 màn mẫu. Nạp THẬT 58-crm.js cùng các hàm nền nó
 * dùng vào DOM giả. Máy chủ giả chỉ trả dữ liệu dựng sẵn và ghi lại lời gọi;
 * luật đồng ý, đối chứng, chốt danh sách chạy thật ở thu_crm_614.py. Mỗi ca bấm
 * đúng chuỗi thao tác của thu ngân, Sales hay quản lý, không gọi thêm hàm nội
 * bộ nào "cho chắc" (điều 15).
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/crm_614.js
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
var HAM = ['h', 'money', 'today', 'vgbChuan', 'vgbKhop'].map(function (t) { return layHam(NEN, t); })
  .concat([layHam(POS, 'posChipNut')])
  .concat(['dsccHang', 'dsCongCu', 'dsCongCuNoi'].map(function (t) { return layHam(KHUON, t); }))
  .concat(['var scanBarcode = function () { return Promise.resolve(null); };'])
  .concat([layHam(KM, 'kmHangChip'), layHam(KHO, 'errMsg')]).join('\n');

var SALES = ['Sales User'];
var QL = ['Sales Manager'];
var GD = ['Sales Manager', 'System Manager'];
var KHO_VAI = ['Stock User'];
var CAU = 'Dạ anh/chị có muốn tiệm báo món mới và ưu đãi dịp lễ qua Zalo hoặc gọi điện không ạ? Anh/chị đổi ý lúc nào cũng được.';
var KQ = ['Quan tâm', 'Đã đặt đơn', 'Không nghe máy', 'Hẹn gọi lại', 'Không muốn nhận tin nữa'];

function dongGoi() {
  return [
    { name: 'L1', chien_dich: 'CD-26-0001', ten_chien_dich: 'Giáng sinh 2026', khach: 'KH-1', ten_khach: 'Nguyễn Minh Anh', sdt: '0909 123 456',
      trang_thai: 'Chưa gọi', kenh_duoc: 'Gọi điện, Zalo', tin_zalo: 'Chào Nguyễn Minh Anh, tiệm có món mới', kich_ban: 'Dạ chào anh chị', mua_cuoi: '2025-12-20', nhom: 'Sắp rời đi', hang: 'Vàng' },
    { name: 'L2', chien_dich: 'CD-26-0001', ten_chien_dich: 'Giáng sinh 2026', khach: 'KH-2', ten_khach: 'Trần Hoàng Long', sdt: '0912345678',
      trang_thai: 'Chưa gọi', kenh_duoc: 'Zalo', tin_zalo: 'Chào Trần Hoàng Long', kich_ban: 'Dạ chào anh chị', nhom: 'Đã ngủ' },
    { name: 'L3', chien_dich: 'CD-26-0001', ten_chien_dich: 'Giáng sinh 2026', khach: 'KH-3', ten_khach: 'Lê Thu', sdt: '0987654321',
      trang_thai: 'Hẹn gọi lại', kenh_duoc: 'Gọi điện', ket_qua: 'Không nghe máy', lan_cuoi: '2026-10-27 10:12:00', kich_ban: 'Dạ chào anh chị' },
    { name: 'L4', chien_dich: 'CD-26-0002', ten_chien_dich: 'Tết 2027', khach: 'KH-4', ten_khach: 'Phạm Thu Hà', sdt: '0901111222',
      trang_thai: 'Đã xong', kenh_duoc: 'Gọi điện', ket_qua: 'Đã đặt đơn' },
  ];
}

function cdMau(them) {
  var c = { name: 'CD-26-0001', ten: 'Giáng sinh 2026', trang_thai: 'Nháp', loc: { nhom: ['Sắp rời đi'] }, bo_loc: '', mo_ta_loc: 'Nhóm Sắp rời đi',
    kenh_goi: 1, kenh_zalo: 0, ty_le_doi_chung: 10, mon: [], sales: [{ nguoi: 'a@x', ten: 'Loan Anh' }, { nguoi: 'b@x', ten: 'Sales 2' },
      { nguoi: 'c@x', ten: 'Sales 3' }, { nguoi: 'd@x', ten: 'Sales 4' }],
    kich_ban: 'Dạ chào anh chị, tiệm có món mới mùa Giáng sinh', noi_dung_zalo: '', ctkm: '', ma_uu_dai: '', han: '',
    kich_ban_duyet: 1, duoc_lap: 1, duoc_duyet: 0, ly_do_chua_chot: '',
    dong_chay: { trong_nhom: 4446, chua_dong_y: 3180, khong_quang_cao: 12, du_dieu_kien: 1254, doi_chung: 125, nhan: 1129, so_sales: 4 } };
  Object.keys(them || {}).forEach(function (k) { c[k] = them[k]; });
  return c;
}

function dungMoi(vai, traLoi) {
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);
  var goi = [], toastDs = [], hoi = [], dongY = [];
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, Number: Number, Date: Date, setTimeout: setTimeout, isNaN: isNaN, parseInt: parseInt,
    navigator: {}, S: { roles: vai, stack: [] },
    hasRole: function (r) { return vai.indexOf(r) >= 0; },
    frame: function (t, html) {
      khung.innerHTML = html; khung._nghe = {}; khung.onclick = null; that._t = t; return khung;
    },
    go: function (fn) { return fn(); },
    busy: function () {},
    toast: function (m) { toastDs.push(m); },
    baoTin: function (m, t) { toastDs.push('BAOTIN ' + t + '|' + m); },
    confirmSheet: function (t, m) { hoi.push(t + '|' + m); return Promise.resolve(that._dongY !== false); },
    hoiChon: function () { return Promise.resolve(that._chon || null); },
    hoiChonNhieu: function () { return Promise.resolve(that._chonNhieu || null); },
    vgbChonMon: function () { return Promise.resolve(that._mon || []); },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: ts });
      var f = (traLoi || {})[duong.replace('vagabond.crm.', '')];
      if (typeof f === 'function') { try { return Promise.resolve(f(ts)); } catch (e) { return Promise.reject(e); } }
      if (f !== undefined) return Promise.resolve(JSON.parse(JSON.stringify(f)));
      return Promise.resolve({ ok: 1, doi: 2, trang_thai: 'Đã xong' });
    },
  };
  that.window = that;
  vm.runInNewContext(HAM, that, { filename: 'ham-nen.js' });
  vm.runInNewContext(MAN, that, { filename: '58-crm.js' });
  return { g: that, tai: tai, khung: khung, goi: goi, toast: toastDs, hoi: hoi, dongY: dongY };
}

var ket = { dat: 0, hong: 0 };
function dung(mo, dk) { if (!dk) throw new Error(mo); }
function bang(mo, a, b) {
  var x = JSON.stringify(a), y = JSON.stringify(b);
  if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y);
}
function tick() { return new Promise(function (r) { setTimeout(r, 5); }); }
async function choDen(dk) { for (var i = 0; i < 80 && !dk(); i++) await new Promise(function (r) { setTimeout(r, 25); }); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); }
}
function chu(el) { var s = el._chu || ''; (el.children || []).forEach(function (c) { s += chu(c); }); return s; }
function sheet(m) { var ds = m.tai.body.children; return ds.length > 1 ? ds[ds.length - 1] : null; }
function bam(m, el) { if (!el) throw new Error('khong co nut de bam'); el.dispatchEvent(dg.suKien('click', {}, el)); }
function goiTen(m, t) { return m.goi.filter(function (x) { return x.duong === 'vagabond.crm.' + t; }); }
function mot(el, chon) { return el.querySelectorAll(chon)[0]; }

(async function () {
  console.log('v614 Khách hàng (CRM): hỏi đồng ý, danh sách gọi, chiến dịch, hiệu quả');

  /* ------------------------------------------------ đồng ý ở quầy */

  await ca('quầy: dải nhắc chỉ hiện khi khách chưa được hỏi cả gọi điện lẫn Zalo', async function () {
    var m = dungMoi(SALES);
    var t = function (dy) { return m.g.crmTheHoi(dy); };
    dung('chưa hỏi: có dải và nút Hỏi khách', t({ co: 1, can_hoi: 1 }).indexOf('data-crmhoimo') >= 0 && t({ co: 1, can_hoi: 1 }).indexOf('Chưa hỏi khách nhận tin ưu đãi') >= 0);
    bang('đã hỏi rồi: không hiện', t({ co: 1, can_hoi: 0 }), '');
    bang('giỏ dùng chung: không hiện', t({ co: 0, khach: 'Khách lẻ' }), '');
    bang('chưa đọc được (lỗi mạng): không hiện, không chặn thu tiền', t(null), '');
  });

  await ca('tấm hỏi: đọc câu cho khách, bật Zalo, tắt gọi điện đang đồng ý thì ghi Từ chối, kênh chưa hỏi để nguyên', async function () {
    var m = dungMoi(SALES);
    var xong = [];
    m.g.crmSheetDongY('KH-1', 'Nguyễn Minh Anh', { co: 1, 'Zalo': 'Chưa hỏi', 'Gọi điện': 'Đồng ý', 'Email': 'Chưa hỏi', cau_hoi: CAU }, 'Quầy',
      function (kq) { xong.push(kq); });
    var sh = sheet(m), s = chu(sh);
    dung('có câu đọc nguyên văn', chu(mot(sh, '[data-crmcau]')).indexOf(CAU) >= 0);
    dung('có tên khách', s.indexOf('Nguyễn Minh Anh') >= 0);
    dung('dặn bấm ra ngoài là chưa hỏi', s.indexOf('khách vẫn là "chưa hỏi"') >= 0);
    var sw = function (k) { return mot(sh, '[data-crmsw="' + k + '"]'); };
    bang('công tắc theo trạng thái cũ', ['Zalo', 'Gọi điện', 'Email'].map(function (k) { return sw(k).getAttribute('aria-checked'); }), ['false', 'true', 'false']);
    bam(m, sw('Zalo'));
    bam(m, sw('Gọi điện'));
    bang('công tắc đổi', [sw('Zalo').getAttribute('aria-checked'), sw('Gọi điện').getAttribute('aria-checked')], ['true', 'false']);
    bam(m, mot(sh, '[data-crmluu]'));
    await choDen(function () { return goiTen(m, 'ghi_dong_y').length; });
    var g = goiTen(m, 'ghi_dong_y')[0].ts;
    bang('gọi đúng khách và nơi ghi', [g.khach, g.noi_ghi], ['KH-1', 'Quầy']);
    bang('Zalo đồng ý, gọi điện rút lại, Email không gửi', JSON.parse(g.dat), { 'Zalo': 'Đồng ý', 'Gọi điện': 'Từ chối' });
    await choDen(function () { return xong.length; });
    dung('đóng tấm và báo số kênh', sheet(m) === null && m.toast[0] === 'Đã ghi 2 kênh vào sổ đồng ý');
    bang('báo về cho quầy vẽ lại', xong.length, 1);
  });

  await ca('tấm hỏi: Khách từ chối hết ghi Từ chối cả ba kênh; bấm ra ngoài thì không ghi gì', async function () {
    var m = dungMoi(SALES);
    m.g.crmSheetDongY('KH-2', 'Long', { co: 1, cau_hoi: CAU }, 'Quầy');
    bam(m, mot(sheet(m), '[data-crmtuchoi]'));
    await choDen(function () { return goiTen(m, 'ghi_dong_y').length; });
    bang('ba kênh từ chối', JSON.parse(goiTen(m, 'ghi_dong_y')[0].ts.dat), { 'Zalo': 'Từ chối', 'Gọi điện': 'Từ chối', 'Email': 'Từ chối' });
    var m2 = dungMoi(SALES);
    var ov = m2.g.crmSheetDongY('KH-2', 'Long', { co: 1, cau_hoi: CAU }, 'Quầy');
    bam(m2, ov);
    dung('đóng tấm', sheet(m2) === null);
    bang('không gọi máy chủ', m2.goi.length, 0);
  });

  await ca('tấm hỏi: bật hết rồi Lưu khi khách chưa hỏi gì gửi đủ ba Đồng ý; không bật gì thì không tự ghi Từ chối', async function () {
    var m = dungMoi(SALES);
    m.g.crmSheetDongY('KH-3', 'Thu', { co: 1 }, 'Hồ sơ khách');
    var sh = sheet(m);
    bam(m, mot(sh, '[data-crmluu]'));
    await choDen(function () { return goiTen(m, 'ghi_dong_y').length; });
    bang('im lặng không thành từ chối', JSON.parse(goiTen(m, 'ghi_dong_y')[0].ts.dat), {});
    bang('nơi ghi hồ sơ', goiTen(m, 'ghi_dong_y')[0].ts.noi_ghi, 'Hồ sơ khách');
    var m2 = dungMoi(SALES);
    m2.g.crmSheetDongY('KH-3', 'Thu', { co: 1 }, 'Quầy');
    var s2 = sheet(m2);
    ['Zalo', 'Gọi điện', 'Email'].forEach(function (k) { bam(m2, mot(s2, '[data-crmsw="' + k + '"]')); });
    bam(m2, mot(s2, '[data-crmluu]'));
    await choDen(function () { return goiTen(m2, 'ghi_dong_y').length; });
    bang('ba kênh đồng ý', JSON.parse(goiTen(m2, 'ghi_dong_y')[0].ts.dat), { 'Zalo': 'Đồng ý', 'Gọi điện': 'Đồng ý', 'Email': 'Đồng ý' });
  });

  await ca('tấm hỏi: máy chủ từ chối thì báo đúng câu, tấm vẫn mở để bấm lại', async function () {
    var m = dungMoi(SALES, { ghi_dong_y: function () { throw new Error('Tài khoản của bạn chưa được ghi đồng ý nhận tin.'); } });
    m.g.crmSheetDongY('KH-1', 'Minh Anh', { co: 1 }, 'Quầy');
    var sh = sheet(m);
    bam(m, mot(sh, '[data-crmtuchoi]'));
    await choDen(function () { return m.toast.length; });
    dung('báo câu máy chủ: ' + m.toast[0], m.toast[0].indexOf('chưa được ghi đồng ý') >= 0);
    dung('tấm còn', sheet(m) === sh);
  });

  /* ------------------------------------------------ danh sách gọi */

  async function moGoi(vai) {
    var m = dungMoi(vai || SALES, { ds_goi_cua_toi: { dong: dongGoi(), ket_qua: KQ } });
    vm.runInNewContext('crmGoiTt = "Chưa gọi"; crmGoiCd = ""; crmGoiTim = "";', m.g);
    await m.g.scrCrmGoi();
    await tick();
    return m;
  }
  function dongHien(m) { return m.khung.querySelectorAll('[data-crmdong]').map(function (x) { return x.getAttribute('data-crmdong'); }); }

  await ca('danh sách gọi: mặc định khách Chưa gọi, chip có đếm, tiến độ từng chiến dịch, nút theo kênh khách đồng ý', async function () {
    var m = await moGoi();
    bang('tiêu đề', m.g._t, 'Danh sách gọi của tôi');
    bang('hỏi máy chủ một lần', goiTen(m, 'ds_goi_cua_toi').length, 1);
    bang('chỉ khách chưa gọi', dongHien(m), ['L1', 'L2']);
    var chip = m.khung.querySelectorAll('[data-dscc]').map(function (x) { return x.getAttribute('data-dscc') + '=' + chu(x); });
    bang('chip trạng thái và chiến dịch có đếm', chip, ['chang|=Tất cả 4', 'chang|Chưa gọi=Chưa gọi 2', 'chang|Hẹn gọi lại=Hẹn gọi lại 1',
      'chang|Đã xong=Đã xong 1', 'cd|=Mọi chiến dịch 4', 'cd|CD-26-0001=Giáng sinh 2026 3', 'cd|CD-26-0002=Tết 2027 1']);
    dung('tiến độ', chu(mot(m.khung, '[data-crmcd="CD-26-0001"]')).indexOf('Đã gọi 1 / 3') >= 0);
    var l1 = mot(m.khung, '[data-crmdong="L1"]'), l2 = mot(m.khung, '[data-crmdong="L2"]');
    bang('L1 đồng ý cả hai: Gọi số không dấu cách', mot(l1, '[data-crmgoi]').getAttribute('href'), 'tel:0909123456');
    dung('L1 có Chép tin', !!mot(l1, '[data-crmchep]'));
    dung('L2 chỉ đồng ý Zalo: không có nút Gọi', !mot(l2, '[data-crmgoi]') && !!mot(l2, '[data-crmchep]'));
    dung('dòng nêu nhóm, ngày mua, kênh', chu(l1).indexOf('Mua lần cuối 20/12/2025 · Sắp rời đi · đồng ý: Gọi điện, Zalo') >= 0);
    dung('nhắc luật từ chối', chu(m.khung).indexOf('ghi ngay vào Sổ đồng ý') >= 0);
  });

  await ca('danh sách gọi: bấm chip Hẹn gọi lại, chip chiến dịch, gõ số có dấu cách; không hỏi lại máy chủ', async function () {
    var m = await moGoi();
    bam(m, mot(m.khung, '[data-dscc="chang|Hẹn gọi lại"]'));
    bang('hẹn gọi lại', dongHien(m), ['L3']);
    var s3 = chu(mot(m.khung, '[data-crmdong="L3"]')); dung('lần trước: ' + s3, s3.indexOf('Lần trước:') >= 0 && s3.indexOf('Không nghe máy') >= 0 && s3.indexOf('lúc 10:12 27/10') >= 0);
    bam(m, mot(m.khung, '[data-dscc="chang|"]'));
    bam(m, mot(m.khung, '[data-dscc="cd|CD-26-0002"]'));
    bang('một chiến dịch', dongHien(m), ['L4']);
    bam(m, mot(m.khung, '[data-dscc="cd|"]'));
    var o = m.tai.getElementById('crmGoiDsTim');
    o.value = '909 123';
    o.dispatchEvent(dg.suKien('change', {}, o));
    bang('tìm số có dấu cách', dongHien(m), ['L1']);
    dung('thanh đang tìm', chu(mot(m.khung, '[data-crmgoiloc]')).indexOf('1 khách') >= 0);
    o = m.tai.getElementById('crmGoiDsTim');
    o.value = 'tran hoang';
    o.dispatchEvent(dg.suKien('change', {}, o));
    bang('tìm tên không dấu', dongHien(m), ['L2']);
    bang('không hỏi lại máy chủ', goiTen(m, 'ds_goi_cua_toi').length, 1);
  });

  await ca('kết quả gọi: chưa chọn thì không gửi; chọn Không muốn nhận tin nữa gửi đúng tham số, dòng rời nhóm Chưa gọi', async function () {
    var m = await moGoi();
    bam(m, mot(mot(m.khung, '[data-crmdong="L1"]'), '[data-crmkq]'));
    var sh = sheet(m);
    bang('năm kết quả', sh.querySelectorAll('[data-crmkqc]').map(chu), KQ);
    bam(m, mot(sh, '[data-crmkqluu]'));
    await tick();
    bang('chưa chọn: không gửi', goiTen(m, 'ghi_ket_qua').length, 0);
    dung('nhắc chọn', m.toast[0] === 'Chọn một kết quả trước.');
    bam(m, mot(sh, '[data-crmkqc="Không muốn nhận tin nữa"]'));
    mot(sh, '#crmKqGhi').value = '  khách bảo đừng gọi  ';
    bam(m, mot(sh, '[data-crmkqluu]'));
    await choDen(function () { return goiTen(m, 'ghi_ket_qua').length; });
    await tick();
    bang('gửi', goiTen(m, 'ghi_ket_qua')[0].ts, { name: 'L1', ket_qua: 'Không muốn nhận tin nữa', ghi_chu: 'khách bảo đừng gọi' });
    dung('báo khách bị loại', m.toast[m.toast.length - 1].indexOf('không được gọi hay nhắn quảng cáo nữa') >= 0);
    bang('L1 rời nhóm Chưa gọi', dongHien(m), ['L2']);
    bang('vẽ lại không hỏi máy chủ', goiTen(m, 'ds_goi_cua_toi').length, 1);
  });

  await ca('Chép tin: chép đúng tin của khách; trình duyệt không cho chép thì hiện tin để chép tay', async function () {
    var m = await moGoi();
    var chep = [];
    m.g.navigator.clipboard = { writeText: function (t) { chep.push(t); return Promise.resolve(); } };
    bam(m, mot(mot(m.khung, '[data-crmdong="L2"]'), '[data-crmchep]'));
    await tick();
    bang('chép tin L2', chep, ['Chào Trần Hoàng Long']);
    dung('báo mở Zalo dán', m.toast[0].indexOf('Đã chép tin cho Trần Hoàng Long') === 0);
    var m2 = await moGoi();
    bam(m2, mot(mot(m2.khung, '[data-crmdong="L1"]'), '[data-crmchep]'));
    dung('hiện tin chép tay', m2.toast[0].indexOf('BAOTIN Chép tin này gửi khách|Chào Nguyễn Minh Anh') === 0);
  });

  await ca('không có quyền: không hỏi máy chủ, nói rõ ai dùng được', async function () {
    var m = dungMoi(KHO_VAI);
    await m.g.scrCrmGoi();
    await m.g.scrCrmNhom();
    await m.g.scrCrmDongY();
    await m.g.scrCrmCdDs();
    bang('không gọi', m.goi.length, 0);
    dung('câu khoá', chu(m.khung).indexOf('chỉ mở cho Sales, quản lý cửa hàng và Marketing') >= 0);
    dung('Sales User có quyền', dungMoi(SALES).g.coQuyenCrm() && !dungMoi(SALES).g.crmCoLap());
    dung('Sales Manager lập được', dungMoi(QL).g.crmCoLap());
  });

  /* ------------------------------------------------ chiến dịch */

  async function moCd(vai, cd, them) {
    var tl = Object.assign({ doc_chien_dich: cd, chot_chien_dich: cdMau({ trang_thai: 'Đang chạy', ngay_chot: '2026-10-27 15:00:00' }) }, them || {});
    var m = dungMoi(vai || QL, tl);
    await m.g.scrCrmCd(cd ? cd.name : '');
    await tick();
    return m;
  }

  await ca('chiến dịch nháp: khung Ai sẽ được liên hệ hiện đúng số máy chủ tính (4.446 -> 1.129)', async function () {
    var m = await moCd(QL, cdMau());
    var dc = m.khung.querySelectorAll('[data-crmdcd]').map(function (x) { return x.getAttribute('data-crmdcd') + '=' + chu(x); });
    bang('năm dòng', dc, ['tong=Trong nhóm4.446', 'loai=Loại: chưa đồng ý kênh đã chọn− 3.180',
      'loai=Loại: trong Danh sách không quảng cáo− 12', 'dc=Đối chứng 10%: giữ lại, không liên hệ125', 'ok=Chia cho 4 Sales1.129']);
    dung('nói rõ đối chứng ngẫu nhiên và khoá', chu(m.khung).indexOf('Máy chọn đối chứng ngẫu nhiên và khoá cố định lúc chốt') >= 0);
    dung('Zalo OA để đợt 2', chu(m.khung).indexOf('Zalo OA hàng loạt · đợt 2') >= 0);
  });

  await ca('chốt: còn lý do thì nút khoá, bấm không gọi máy chủ; hết lý do thì hỏi xác nhận kèm số rồi chốt', async function () {
    var m = await moCd(QL, cdMau({ kich_ban_duyet: 0, ly_do_chua_chot: 'Kịch bản gọi chưa được duyệt. Nhờ giám đốc duyệt rồi chốt.' }));
    var nut = mot(m.khung, '[data-crmcdchot]');
    dung('nút khoá', nut.hasAttribute('disabled'));
    dung('nói lý do', chu(mot(m.khung, '[data-crmlydo]')).indexOf('Kịch bản gọi chưa được duyệt') === 0);
    dung('Sales Manager không thấy nút Duyệt', !mot(m.khung, '[data-crmcdduyet]'));
    bam(m, nut);
    await tick();
    bang('không gọi chốt', goiTen(m, 'chot_chien_dich').length, 0);
    bang('không hỏi xác nhận', m.hoi.length, 0);

    var m2 = await moCd(QL, cdMau());
    bam(m2, mot(m2.khung, '[data-crmcdchot]'));
    await choDen(function () { return goiTen(m2, 'chot_chien_dich').length; });
    dung('hỏi kèm số: ' + m2.hoi[0], m2.hoi[0] === 'Chốt danh sách?|Máy giữ 125 khách làm đối chứng và chia 1.129 khách cho 4 Sales. Sau khi chốt, danh sách không đổi nữa.');
    bang('chốt đúng chiến dịch', goiTen(m2, 'chot_chien_dich')[0].ts, { name: 'CD-26-0001' });
    await tick();
    dung('sau chốt: khoá, có Xem hiệu quả, hết nút chốt', !mot(m2.khung, '[data-crmcdchot]') && !!mot(m2.khung, '[data-crmcdhq]'));

    var m3 = await moCd(QL, cdMau());
    m3.g._dongY = false;
    bam(m3, mot(m3.khung, '[data-crmcdchot]'));
    await tick(); await tick();
    bang('bấm Không ở hộp xác nhận: không chốt', goiTen(m3, 'chot_chien_dich').length, 0);
  });

  await ca('đã chốt: mọi ô khoá, không còn Lưu, Chốt, Thêm Sales; bấm ô khoá không gọi gì', async function () {
    var m = await moCd(QL, cdMau({ trang_thai: 'Đang chạy', ngay_chot: '2026-10-27 15:00:00' }));
    dung('ô tên khoá', mot(m.khung, '#crmCdTen').hasAttribute('disabled'));
    dung('kịch bản khoá', mot(m.khung, '#crmCdKb').hasAttribute('disabled'));
    dung('không Lưu, Chốt, Thêm Sales, Thêm món', !mot(m.khung, '[data-crmcdluu]') && !mot(m.khung, '[data-crmcdchot]') &&
      !mot(m.khung, '[data-crmcdsl]') && !mot(m.khung, '[data-crmcdmon]') && !mot(m.khung, '[data-crmcdk]'));
    dung('nói danh sách đã khoá', chu(m.khung).indexOf('Danh sách đã khoá, không đổi theo nhóm chạy đêm') >= 0);
    dung('có Kết thúc cho người lập', !!mot(m.khung, '[data-crmcdkt]'));
    var truoc = m.goi.length;
    bam(m, mot(m.khung, '[data-crmcdloc]'));
    await tick();
    bang('nút nhóm khoá không gọi', m.goi.length, truoc);
    var m2 = await moCd(SALES, cdMau({ trang_thai: 'Đang chạy', duoc_lap: 0 }));
    dung('Sales không có Kết thúc', !mot(m2.khung, '[data-crmcdkt]'));
  });

  await ca('giám đốc duyệt kịch bản: chỉ System Manager thấy nút, bấm gọi đúng hàm', async function () {
    var m = await moCd(GD, cdMau({ kich_ban_duyet: 0, duoc_duyet: 1, ly_do_chua_chot: 'Kịch bản gọi chưa được duyệt. Nhờ giám đốc duyệt rồi chốt.' }),
      { duyet_kich_ban: cdMau({ duoc_duyet: 1 }) });
    bam(m, mot(m.khung, '[data-crmcdduyet]'));
    await choDen(function () { return goiTen(m, 'duyet_kich_ban').length; });
    bang('duyệt', goiTen(m, 'duyet_kich_ban')[0].ts, { name: 'CD-26-0001' });
    await tick();
    dung('nhãn đã duyệt, hết nút', chu(m.khung).indexOf('· đã duyệt') >= 0 && !mot(m.khung, '[data-crmcdduyet]'));
  });

  await ca('chiến dịch mới từ nhóm: đổi kênh, thêm Sales, gõ tên và kịch bản; Lưu gửi đủ dữ liệu', async function () {
    var m = dungMoi(QL, {
      ds_sales: { ds: [{ name: 'a@x', ten: 'Loan Anh' }, { name: 'b@x', ten: 'Sales 2' }] },
      luu_chien_dich: function (ts) { return cdMau({ ten: JSON.parse(ts.dat).ten }); },
    });
    vm.runInNewContext('crmCdMoi = { loc: { nhom: ["Đã ngủ"] }, ten_loc: "Nhóm Đã ngủ" };', m.g);
    await m.g.scrCrmCd('');
    bang('tiêu đề', m.g._t, 'Chiến dịch mới');
    dung('nhóm điền sẵn', chu(mot(m.khung, '[data-crmcdloc]')).indexOf('Nhóm Đã ngủ') >= 0);
    dung('chưa có nút chốt khi chưa lưu', !mot(m.khung, '[data-crmcdchot]'));
    mot(m.khung, '#crmCdTen').value = 'Gọi khách đã ngủ';
    mot(m.khung, '#crmCdKb').value = 'Dạ chào anh chị, lâu rồi chưa ghé tiệm';
    bam(m, mot(m.khung, '[data-crmcdk="zalo"]'));
    dung('giữ chữ đã gõ khi vẽ lại', mot(m.khung, '#crmCdTen').value === 'Gọi khách đã ngủ');
    m.g._chonNhieu = ['b@x', 'a@x'];
    bam(m, mot(m.khung, '[data-crmcdsl]'));
    await choDen(function () { return chu(m.khung).indexOf('Sales 2') >= 0; });
    bam(m, mot(m.khung, '[data-crmcdluu]'));
    await choDen(function () { return goiTen(m, 'luu_chien_dich').length; });
    var dat = JSON.parse(goiTen(m, 'luu_chien_dich')[0].ts.dat);
    bang('dữ liệu lưu', [dat.name, dat.ten, dat.loc, dat.kenh_goi, dat.kenh_zalo, dat.kich_ban, dat.sales, dat.ty_le_doi_chung],
      ['', 'Gọi khách đã ngủ', { nhom: ['Đã ngủ'] }, 1, 1, 'Dạ chào anh chị, lâu rồi chưa ghé tiệm', ['b@x', 'a@x'], 10]);
    await tick();
    dung('lưu xong có khung số và nút chốt', !!mot(m.khung, '[data-crmdc]') && !!mot(m.khung, '[data-crmcdchot]'));
  });

  await ca('mã ưu đãi: chưa có CTKM mã cố định thì chỉ đường tạo; có thì chọn và ghi mã', async function () {
    var m = await moCd(QL, cdMau(), { ds_ctkm_ma: { ds: [] } });
    bam(m, mot(m.khung, '[data-crmcdkm]'));
    await choDen(function () { return m.toast.length; });
    dung('chỉ đường: ' + m.toast[0], m.toast[0].indexOf('BAOTIN Chưa có mã để chọn|') === 0 && m.toast[0].indexOf('Mã cố định') >= 0);
    var m2 = await moCd(QL, cdMau(), { ds_ctkm_ma: { ds: [{ name: 'CTKM-9', ten: 'Giáng sinh giảm 10%', ma: 'XMAS10' }] } });
    m2.g._chon = 'CTKM-9';
    bam(m2, mot(m2.khung, '[data-crmcdkm]'));
    await choDen(function () { return chu(m2.khung).indexOf('XMAS10') >= 0; });
    dung('hiện mã', chu(mot(m2.khung, '[data-crmcdkm]')).indexOf('CTKM-9 · mã XMAS10') >= 0);
  });

  /* ------------------------------------------------ hiệu quả */

  await ca('hiệu quả: so bình quân mỗi khách, ghi phép tính; không có đối chứng thì nói rõ', async function () {
    var d = { ten: 'Giáng sinh 2026', tu: '2026-10-27', den: '2026-11-10', dang_do: 1, co_doi_chung: 1, mang_ve_them: 73385000,
      nhan: { so_khach: 1129, ty_le_mua: 18.4, binh_quan: 120000 }, doi_chung: { so_khach: 125, ty_le_mua: 9.6, binh_quan: 55000 },
      ctkm: 'CTKM-9', ma_uu_dai: 'XMAS10', don_dung_ma: 86, khach_tu_choi: 14, theo_sales: [{ ten: 'Loan Anh', so_khach: 283, da_xong: 120, so_don: 31 }] };
    var m = dungMoi(QL, { hieu_qua_chien_dich: d });
    await m.g.scrCrmHieuQua('CD-26-0001');
    var s = chu(m.khung);
    bang('số mang về thêm', chu(mot(m.khung, '[data-crmhqthem]')), '≈ 73.385.000 đ');
    dung('phép tính', s.indexOf('(120.000 − 55.000) × 1.129 khách') >= 0);
    dung('đang đo', s.indexOf('đang đo, số còn tăng') >= 0);
    dung('tỉ lệ mua dấu phẩy', s.indexOf('18,4%') >= 0 && s.indexOf('9,6%') >= 0);
    dung('đơn dùng mã', s.indexOf('Đơn dùng mã XMAS10') >= 0 && s.indexOf('86 đơn') >= 0);
    dung('theo Sales', s.indexOf('Loan Anh · 283 khách, đã gọi xong 120') >= 0);
    var d2 = JSON.parse(JSON.stringify(d)); d2.co_doi_chung = 0; d2.mang_ve_them = null;
    var m2 = dungMoi(QL, { hieu_qua_chien_dich: d2 });
    await m2.g.scrCrmHieuQua('CD-26-0001');
    dung('không đối chứng: không có số mang về thêm', !mot(m2.khung, '[data-crmhqthem]'));
    dung('nói lý do', chu(m2.khung).indexOf('không giữ nhóm đối chứng (dưới 10 khách đủ điều kiện)') >= 0);
  });

  /* ------------------------------------------------ Codex PR #505 vòng 1 */

  await ca('Codex #505: khách rút đồng ý sau khi chốt thì dòng gọi không còn nút Gọi, Chép tin, có dòng nhắc, vẫn ghi kết quả', async function () {
    var ds = [{ name: 'N1', chien_dich: 'CD-1', ten_chien_dich: 'Giáng sinh', khach: 'KH-9', ten_khach: 'Khách rút', sdt: '0909 111 222',
      trang_thai: 'Chưa gọi', kenh_duoc: '', ngung: 1, tin_zalo: '' },
      { name: 'N2', chien_dich: 'CD-1', ten_chien_dich: 'Giáng sinh', khach: 'KH-8', ten_khach: 'Khách còn', sdt: '0909 333 444',
      trang_thai: 'Chưa gọi', kenh_duoc: 'Gọi điện', ngung: 0, tin_zalo: '' }];
    var m = dungMoi(SALES, { ds_goi_cua_toi: { dong: ds, ket_qua: KQ } });
    vm.runInNewContext('crmGoiTt = "Chưa gọi"; crmGoiCd = ""; crmGoiTim = "";', m.g);
    await m.g.scrCrmGoi();
    var n1 = mot(m.khung, '[data-crmdong="N1"]'), n2 = mot(m.khung, '[data-crmdong="N2"]');
    dung('không nút Gọi, không Chép tin', !mot(n1, '[data-crmgoi]') && !mot(n1, '[data-crmchep]'));
    dung('có dòng nhắc', chu(mot(n1, '[data-crmngung]')).indexOf('Khách đã rút đồng ý hoặc xin không nhận quảng cáo') === 0);
    dung('vẫn có nút Kết quả', !!mot(n1, '[data-crmkq]'));
    dung('khách còn đồng ý: có Gọi, không nhắc', !!mot(n2, '[data-crmgoi]') && !mot(n2, '[data-crmngung]'));
  });

  await ca('Codex #505: bản nháp chiến dịch mới mở lại đủ tên, kịch bản, kênh, Sales; bản nháp của chiến dịch khác hay đã chốt thì không ghép', async function () {
    var m = dungMoi(QL, {});
    var nhap = { name: '', ten: 'Gọi khách đã ngủ', loc: { nhom: ['Đã ngủ'] }, mo_ta_loc: 'Nhóm Đã ngủ', kenh_goi: 1, kenh_zalo: 1,
      mon: [{ item: 'BANH-1', ten: 'Entremet' }], sales: [{ nguoi: 'b@x', ten: 'Sales 2' }], kich_ban: 'Dạ chào anh chị, lâu rồi chưa ghé tiệm',
      noi_dung_zalo: 'Chào {ten}', ty_le_doi_chung: 10 };
    m.g.crmCdKhoiPhuc = JSON.parse(JSON.stringify(nhap));
    await m.g.scrCrmCd('');
    bang('tên', mot(m.khung, '#crmCdTen').getAttribute('value'), 'Gọi khách đã ngủ');
    dung('kịch bản', chu(mot(m.khung, '#crmCdKb')).indexOf('lâu rồi chưa ghé tiệm') >= 0);
    dung('nhóm, món, Sales', chu(m.khung).indexOf('Nhóm Đã ngủ') >= 0 && chu(m.khung).indexOf('Entremet') >= 0 && chu(m.khung).indexOf('Sales 2') >= 0);
    bang('đã dùng xong bản nháp', m.g.crmCdKhoiPhuc, null);
    var lay = m.g.crmCdNhap();
    bang('đọc lại để tự lưu', [lay.ten, lay.kenh_zalo, lay.sales.length, lay.kich_ban], ['Gọi khách đã ngủ', 1, 1, 'Dạ chào anh chị, lâu rồi chưa ghé tiệm']);
    m.g.crmCdKhoiPhuc = JSON.parse(JSON.stringify(nhap));
    m.g.crmCdKhoiPhuc.name = 'CD-26-0009';
    await m.g.scrCrmCd('');
    bang('bản nháp của chiến dịch khác: không ghép', mot(m.khung, '#crmCdTen').getAttribute('value'), '');
    var m2 = await moCd(QL, cdMau({ trang_thai: 'Đang chạy' }));
    bang('đã chốt: không tự lưu bản nháp', m2.g.crmCdNhap(), null);
    var m3 = await moCd(SALES, cdMau({ duoc_lap: 0 }));
    bang('không quyền lập: không tự lưu', m3.g.crmCdNhap(), null);
  });

  await ca('Codex #505: màn hiệu quả ghi mốc đo theo giờ chốt', async function () {
    var d = { ten: 'Giáng sinh 2026', tu: '2026-10-27 18:00:00', den: '2026-11-10 18:00:00', dang_do: 0, co_doi_chung: 0,
      nhan: { so_khach: 9, ty_le_mua: 0, binh_quan: 0 }, doi_chung: { so_khach: 0, ty_le_mua: 0, binh_quan: 0 }, ctkm: '', khach_tu_choi: 0, theo_sales: [] };
    var m = dungMoi(QL, { hieu_qua_chien_dich: d });
    await m.g.scrCrmHieuQua('CD-26-0001');
    bang('mốc đo', chu(mot(m.khung, '[data-crmhqmoc]')), 'Đo từ 18:00 27/10 (lúc chốt) tới 18:00 10/11, cùng mốc cho cả hai nhóm');
  });

  /* ------------------------------------------------ Codex PR #505 vòng 2 (rà 9ffd042) */

  await ca('Codex #505 v2: ghi Không muốn nhận tin nữa rồi sang chip Đã xong: không còn Gọi, Chép tin; dòng cùng khách ở chiến dịch khác cũng khoá', async function () {
    var ds = dongGoi();
    ds.push({ name: 'L5', chien_dich: 'CD-26-0002', ten_chien_dich: 'Tết 2027', khach: 'KH-1', ten_khach: 'Nguyễn Minh Anh', sdt: '0909 123 456',
      trang_thai: 'Chưa gọi', kenh_duoc: 'Gọi điện, Zalo', tin_zalo: 'Chào Minh Anh, Tết này', kich_ban: 'Dạ chào' });
    var m = dungMoi(SALES, { ds_goi_cua_toi: { dong: ds, ket_qua: KQ } });
    vm.runInNewContext('crmGoiTt = "Chưa gọi"; crmGoiCd = ""; crmGoiTim = "";', m.g);
    await m.g.scrCrmGoi();
    await tick();
    bam(m, mot(mot(m.khung, '[data-crmdong="L1"]'), '[data-crmkq]'));
    var sh = sheet(m);
    bam(m, mot(sh, '[data-crmkqc="Không muốn nhận tin nữa"]'));
    bam(m, mot(sh, '[data-crmkqluu]'));
    await choDen(function () { return goiTen(m, 'ghi_ket_qua').length; });
    await tick();
    bam(m, mot(m.khung, '[data-dscc="chang|Đã xong"]'));
    var l1 = mot(m.khung, '[data-crmdong="L1"]');
    dung('L1 nằm ở Đã xong', !!l1);
    dung('L1 không còn Gọi, Chép tin', !mot(l1, '[data-crmgoi]') && !mot(l1, '[data-crmchep]'));
    dung('L1 có dòng nhắc rút đồng ý', !!mot(l1, '[data-crmngung]'));
    bam(m, mot(m.khung, '[data-dscc="chang|Chưa gọi"]'));
    var l5 = mot(m.khung, '[data-crmdong="L5"]');
    dung('L5 cùng khách, chiến dịch khác: không Gọi, Chép tin', !!l5 && !mot(l5, '[data-crmgoi]') && !mot(l5, '[data-crmchep]') && !!mot(l5, '[data-crmngung]'));
    var l2 = mot(m.khung, '[data-crmdong="L2"]');
    dung('khách khác giữ nguyên', !!mot(l2, '[data-crmchep]'));
    var chep = [];
    m.g.navigator.clipboard = { writeText: function (t) { chep.push(t); return Promise.resolve(); } };
    m.g.crmChep(m.g.crmGoiDs.filter(function (r) { return r.name === 'L5'; })[0]);
    bang('không chép được tin của khách đã rút', chep.length, 0);
    bang('vẫn không hỏi lại máy chủ', goiTen(m, 'ds_goi_cua_toi').length, 1);
  });

  await ca('Codex #505 v2: sửa kịch bản chưa Lưu nháp rồi bấm Chốt: không chốt, nhắc lưu; Lưu xong mới chốt được', async function () {
    var m = await moCd(QL, cdMau(), { luu_chien_dich: function (ts) { var x = JSON.parse(ts.dat); return cdMau({ kich_ban: x.kich_ban, kich_ban_duyet: 0,
      ly_do_chua_chot: 'Kịch bản gọi chưa được duyệt. Nhờ giám đốc duyệt rồi chốt.' }); } });
    dung('mở ra chưa sửa: nút chốt sáng', !mot(m.khung, '[data-crmcdchot]').hasAttribute('disabled'));
    mot(m.khung, '#crmCdKb').value = 'Kịch bản mới chưa ai đọc';
    bam(m, mot(m.khung, '[data-crmcdchot]'));
    await tick(); await tick();
    bang('không gọi chốt', goiTen(m, 'chot_chien_dich').length, 0);
    bang('không hỏi xác nhận', m.hoi.length, 0);
    dung('nhắc lưu: ' + m.toast[0], m.toast[0].indexOf('Có thay đổi chưa lưu') === 0);
    dung('vẽ lại: giữ chữ đang sửa, nút chốt khoá kèm lý do', mot(m.khung, '#crmCdKb').value === 'Kịch bản mới chưa ai đọc' &&
      mot(m.khung, '[data-crmcdchot]').hasAttribute('disabled') && chu(mot(m.khung, '[data-crmlydo]')).indexOf('Có thay đổi chưa lưu') === 0);
    bam(m, mot(m.khung, '[data-crmcdluu]'));
    await choDen(function () { return goiTen(m, 'luu_chien_dich').length; });
    await tick();
    bang('lưu đúng bản đang sửa', JSON.parse(goiTen(m, 'luu_chien_dich')[0].ts.dat).kich_ban, 'Kịch bản mới chưa ai đọc');
    dung('lưu xong: lý do là chờ duyệt lại, không còn chưa lưu', chu(mot(m.khung, '[data-crmlydo]')).indexOf('Kịch bản gọi chưa được duyệt') === 0);

    var m2 = await moCd(QL, cdMau());
    bam(m2, mot(m2.khung, '[data-crmcdk="zalo"]'));
    dung('đổi kênh bằng chip: nút chốt khoá ngay', mot(m2.khung, '[data-crmcdchot]').hasAttribute('disabled'));
    bam(m2, mot(m2.khung, '[data-crmcdk="zalo"]'));
    dung('đổi lại như cũ: nút chốt sáng lại', !mot(m2.khung, '[data-crmcdchot]').hasAttribute('disabled'));
    bam(m2, mot(m2.khung, '[data-crmcdbosl="0"]'));
    bam(m2, mot(m2.khung, '[data-crmcdchot]'));
    await tick();
    bang('bỏ một Sales chưa lưu: không chốt', goiTen(m2, 'chot_chien_dich').length, 0);

    var m3 = await moCd(QL, cdMau(), { luu_chien_dich: function (ts) { return cdMau({ noi_dung_zalo: JSON.parse(ts.dat).noi_dung_zalo }); } });
    mot(m3.khung, '#crmCdZalo').value = 'Chào {ten}, tiệm có quà';
    bam(m3, mot(m3.khung, '[data-crmcdluu]'));
    await choDen(function () { return goiTen(m3, 'luu_chien_dich').length; });
    await tick();
    dung('lưu xong, máy chủ không đòi gì thêm: nút chốt sáng', !mot(m3.khung, '[data-crmcdchot]').hasAttribute('disabled') && !mot(m3.khung, '[data-crmlydo]'));
    bam(m3, mot(m3.khung, '[data-crmcdchot]'));
    await choDen(function () { return goiTen(m3, 'chot_chien_dich').length; });
    bang('chốt bản vừa lưu', goiTen(m3, 'chot_chien_dich').length, 1);
  });

  await ca('Codex #505 v2: giám đốc sửa kịch bản chưa lưu rồi bấm Duyệt: không duyệt bản cũ', async function () {
    var m = await moCd(GD, cdMau({ kich_ban_duyet: 0, duoc_duyet: 1, ly_do_chua_chot: 'Kịch bản gọi chưa được duyệt.' }), { duyet_kich_ban: cdMau({ duoc_duyet: 1 }) });
    mot(m.khung, '#crmCdKb').value = 'Kịch bản giám đốc vừa sửa';
    bam(m, mot(m.khung, '[data-crmcdduyet]'));
    await tick(); await tick();
    bang('không gọi duyệt', goiTen(m, 'duyet_kich_ban').length, 0);
    dung('nút Duyệt khoá sau khi vẽ lại', mot(m.khung, '[data-crmcdduyet]').hasAttribute('disabled'));
    /* Duyệt trả về bản máy chủ (người khác vừa lưu tin Zalo): màn hiện bản đó, không coi là chưa lưu. */
    var m2 = await moCd(GD, cdMau({ kich_ban_duyet: 0, duoc_duyet: 1, ly_do_chua_chot: 'Kịch bản gọi chưa được duyệt.' }),
      { duyet_kich_ban: cdMau({ duoc_duyet: 1, noi_dung_zalo: 'Chào {ten}, bản người khác vừa lưu' }) });
    bam(m2, mot(m2.khung, '[data-crmcdduyet]'));
    await choDen(function () { return goiTen(m2, 'duyet_kich_ban').length; });
    await tick();
    dung('duyệt xong: nút chốt sáng theo bản máy chủ', !mot(m2.khung, '[data-crmcdchot]').hasAttribute('disabled'));
  });

  await ca('Codex #505 v2: Sổ đồng ý tìm khách cũ qua máy chủ, chip trạng thái, Xem thêm lấy tiếp dòng cũ hơn', async function () {
    var trang = function (tu, n) { var r = []; for (var i = 0; i < n; i++) r.push({ name: 'NK-' + (tu + i), khach: 'KH-' + (tu + i), ten_khach: 'Khách ' + (tu + i), kenh: 'Zalo', trang_thai: 'Đồng ý', noi_ghi: 'Quầy', ten_nguoi: 'Thu ngân', luc: '2026-10-27 10:00:00' }); return r; };
    var tong = { 'Zalo': { 'Đồng ý': 300 }, 'Gọi điện': {}, 'Email': {} };
    var m = dungMoi(QL, { so_dong_y: function (ts) {
      if (ts.tim) return { tong: tong, dong: [{ name: 'NK-7', khach: 'KH-7', ten_khach: 'Nguyễn Minh Anh', kenh: 'Gọi điện', trang_thai: 'Từ chối', noi_ghi: 'Sales gọi', ten_nguoi: 'Loan', luc: '2025-11-02 09:00:00' }], khong_quang_cao: 0, con_nua: 0 };
      return { tong: tong, dong: trang(+ts.bat_dau || 0, 100), khong_quang_cao: 0, con_nua: (+ts.bat_dau || 0) < 200 ? 1 : 0 };
    } });
    vm.runInNewContext('crmDyLoc = ""; crmDyTim = "";', m.g);
    await m.g.scrCrmDongY();
    bang('trang đầu 100 dòng', m.khung.querySelectorAll('[data-crmdykh]').length, 100);
    bang('hỏi lần đầu', goiTen(m, 'so_dong_y')[0].ts, { trang_thai: '', tim: '', bat_dau: 0 });
    bam(m, mot(m.khung, '[data-crmdythem]'));
    await choDen(function () { return goiTen(m, 'so_dong_y').length > 1; });
    await tick();
    bang('Xem thêm lấy từ dòng 100', goiTen(m, 'so_dong_y')[1].ts.bat_dau, 100);
    bang('nối thêm, không thay', m.khung.querySelectorAll('[data-crmdykh]').length, 200);
    dung('dòng cũ hơn hiện ra', !!mot(m.khung, '[data-crmdykh="KH-150"]') && !!mot(m.khung, '[data-crmdykh="KH-0"]'));
    var o = m.tai.getElementById('crmDyDsTim');
    dung('có ô tìm', !!o);
    o.value = 'Minh Anh';
    o.dispatchEvent(dg.suKien('change', {}, o));
    await choDen(function () { return goiTen(m, 'so_dong_y').length > 2; });
    await tick();
    bang('tìm hỏi máy chủ, từ đầu', goiTen(m, 'so_dong_y')[2].ts, { trang_thai: '', tim: 'Minh Anh', bat_dau: 0 });
    bang('chỉ dòng khớp', m.khung.querySelectorAll('[data-crmdykh]').map(function (x) { return x.getAttribute('data-crmdykh'); }), ['KH-7']);
    dung('thanh đang tìm', chu(mot(m.khung, '[data-crmdyloc]')).indexOf('1 dòng') >= 0);
    dung('hết dòng thì không còn Xem thêm', !mot(m.khung, '[data-crmdythem]'));
    bam(m, mot(m.khung, '[data-dscc="chang|Từ chối"]'));
    await choDen(function () { return goiTen(m, 'so_dong_y').length > 3; });
    bang('chip giữ chữ tìm', goiTen(m, 'so_dong_y')[3].ts, { trang_thai: 'Từ chối', tim: 'Minh Anh', bat_dau: 0 });
  });

  console.log('\n' + ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng.');
  process.exit(ket.hong ? 1 : 0);
})();

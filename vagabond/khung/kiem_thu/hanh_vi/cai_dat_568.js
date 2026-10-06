/* Bộ ca kiểm phép THUẦN của trang Cài đặt Vagabond (v568).
 *
 * Anh Việt 04/10/2026: trang Cài đặt đầy ô mã máy tự ghi, chữ hướng dẫn
 * không dấu; nhờ quy hoạch lại thành tab, chip trạng thái, chip chọn.
 *
 * Nạp THẬT tệp vagabond_settings.js với frappe giả chỉ có chỗ đăng ký sự
 * kiện (phần vẽ form cần Desk của Frappe nên không chạy ở đây; phần đó kiểm
 * trên site thật và đính ảnh lên PR). Ở đây chạy thật bốn phép quyết định
 * nội dung trang: chip tình trạng kết nối, chip trên đầu mục, thẻ tóm tắt dữ
 * liệu app tự ghi, và ô tìm cài đặt.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/cai_dat_568.js
 */
'use strict';

var path = require('path');
var GOC = path.resolve(__dirname, '..', '..', '..', '..');
/* v581 Codex #447: giữ lại mọi bộ xử lý form.on để ca kiểm chạy được nút trên thanh công cụ. */
var DANG_KY = [];
global.frappe = { ui: { form: { on: function (dt, h) { DANG_KY.push([dt, h]); } } } };
/* v570: phép thuần dời sang tệp dùng chung Desk và app. */
var V = require(path.join(GOC, 'vagabond', 'public', 'js', 'cai_dat_loi_chung.js'));
/* Phần chạm form Desk vẫn ở vagabond_settings.js và gọi VGB_CD như biến toàn cục,
   đúng như trên trình duyệt sau khi tệp chung đã nạp. */
global.VGB_CD = V;
V._desk = require(path.join(GOC, 'vagabond', 'vagabond', 'doctype', 'vagabond_settings', 'vagabond_settings.js'))._desk;

var dat = 0, hong = 0;
function ca(ten, ham) {
  try { ham(); dat++; console.log('  DAT   ' + ten); }
  catch (e) { hong++; console.log('  HONG  ' + ten + '\n        ' + (e && e.message)); }
}
function la(nhan, duoc, mong) {
  var a = JSON.stringify(duoc), b = JSON.stringify(mong);
  if (a !== b) throw new Error(nhan + ': được ' + a + ' | mong ' + b);
}
function dung(nhan, dk) { if (!dk) throw new Error(nhan); }
function tim(ds, ten) { return ds.filter(function (x) { return x.ten === ten; })[0]; }

var BAY_GIO = Date.parse('2026-10-04T10:00:00');

ca('tình trạng: chưa khai gì thì mọi kết nối xám, không ô nào xanh', function () {
  var tt = V.tinhTrang({}, BAY_GIO);
  la('số chip', tt.length, V.KET_NOI.length + 1);
  dung('không chip nào xanh', tt.every(function (t) { return t.trang === 'no'; }));
});

ca('tình trạng: m-invoice thiếu mật khẩu là CHƯA khai, đủ ba ô mới xanh', function () {
  var d = { minvoice_host: 'h', minvoice_username: 'u' };
  la('thiếu mật khẩu', tim(V.tinhTrang(d, BAY_GIO), 'Hoá đơn điện tử m-invoice').trang, 'no');
  d.minvoice_password = '*********';
  la('đủ ba ô', tim(V.tinhTrang(d, BAY_GIO), 'Hoá đơn điện tử m-invoice').trang, 'ok');
});

ca('tình trạng: khai đủ mà công tắc đang tắt là vàng, bật lên mới xanh', function () {
  var d = { zalo_bot_token: '****', zalo_bot_bat: 0, zalo_nhom: [{ ten_nhom: 'Vận hành', chat_id: 'g1', bat: 1 }] };
  la('đang tắt', tim(V.tinhTrang(d, BAY_GIO), 'Zalo bắn tin nhóm').trang, 'off');
  d.zalo_bot_bat = 1;
  la('đã bật', tim(V.tinhTrang(d, BAY_GIO), 'Zalo bắn tin nhóm').trang, 'ok');
  // Công tắc bật mà chưa khai token thì vẫn XÁM: không có gì để chạy.
  la('bật mà chưa khai', tim(V.tinhTrang({ zalo_bot_bat: 1 }, BAY_GIO), 'Zalo bắn tin nhóm').trang, 'no');
});

ca('Codex #433 vòng 3 G2: GreenSM thiếu token_url, Zalo ZNS thiếu App Secret, Ahamove thiếu base, Thông báo đẩy thiếu khoá riêng thì CHƯA khai', function () {
  // Trên 8159e6c cả bốn ra xanh, dù máy chủ chắc chắn từ chối cấu hình đó
  // (van_don._greensm_dat_don, zalo.py, van_don.py Ahamove, thong_bao.py).
  var g = { greensm_client_id: 'a', greensm_client_secret: '*' };
  la('GreenSM thiếu token_url', tim(V.tinhTrang(g, BAY_GIO), 'GreenSM').trang, 'no');
  g.greensm_token_url = 'https://x/token';
  la('GreenSM đủ ba ô', tim(V.tinhTrang(g, BAY_GIO), 'GreenSM').trang, 'ok');
  la('chỉ be_token (máy chủ không đọc) thì không xanh', tim(V.tinhTrang({ be_token: '*' }, BAY_GIO), 'GreenSM').trang, 'no');
  var z = { zalo_app_id: '1', zalo_refresh_token: '*' };
  la('ZNS thiếu App Secret', tim(V.tinhTrang(z, BAY_GIO), 'Zalo ZNS gửi khách').trang, 'no');
  z.zalo_app_secret = '*';
  z.zns_template_otp = 'T1';  // Codex #435: phải có ít nhất một mẫu ZNS
  la('ZNS đủ', tim(V.tinhTrang(z, BAY_GIO), 'Zalo ZNS gửi khách').trang, 'ok');
  var h = { ahamove_api_key: '*', ahamove_mobile: '09' };
  la('Ahamove thiếu base', tim(V.tinhTrang(h, BAY_GIO), 'Ahamove').trang, 'no');
  h.ahamove_base = 'https://api.ahamove.com';
  la('Ahamove đủ', tim(V.tinhTrang(h, BAY_GIO), 'Ahamove').trang, 'ok');
  la('Thông báo đẩy chỉ có khoá công khai', tim(V.tinhTrang({ push_khoa_cong_khai: 'B' }, BAY_GIO), 'Thông báo đẩy').trang, 'no');
  la('Thông báo đẩy đủ hai khoá', tim(V.tinhTrang({ push_khoa_cong_khai: 'B', push_khoa_rieng: '*' }, BAY_GIO), 'Thông báo đẩy').trang, 'ok');
});

ca('Codex #433 vòng 3 G1: bấm chip hay kết quả tìm thì MỞ đúng tab và mục thu gọn trước khi cuộn', function () {
  // frm giả KHÔNG tự mở tab trong scroll_to_field: ca này đỏ nếu chỉ còn dựa vào Frappe.
  var nhat = [];
  var tab = { dang: false, is_active: function () { return this.dang; }, set_active: function () { this.dang = true; nhat.push('tab'); } };
  var muc = { gon: true, is_collapsed: function () { return this.gon; }, collapse: function (v) { this.gon = v; nhat.push('mo_muc'); } };
  var frm = { fields_dict: { sepay_bat: { tab: tab, section: muc } }, scroll_to_field: function (fn) { nhat.push('cuon:' + fn); } };
  la('mở được', V.moToi(frm, 'sepay_bat'), true);
  la('thứ tự: mở tab, mở mục, rồi cuộn', nhat, ['tab', 'mo_muc', 'cuon:sepay_bat']);
  nhat.length = 0;
  V.moToi(frm, 'sepay_bat');
  la('tab đã mở, mục đã mở thì chỉ cuộn', nhat, ['cuon:sepay_bat']);
  la('ô không có thì không làm gì', V.moToi(frm, 'o_la'), false);
});

ca('Codex #433 vòng 3 G1: thanh chip Desk gọi moToi chứ không gọi thẳng scroll_to_field', function () {
  // Dò chuỗi chỉ để chốt "không còn chỗ nào cuộn thẳng" (điều 16); hành vi moToi chạy thật ở ca trên.
  var s = require('fs').readFileSync(path.join(GOC, 'vagabond', 'vagabond', 'doctype', 'vagabond_settings', 'vagabond_settings.js'), 'utf8');
  /* v572: moToi dời sang tệp chung cai_dat_loi_chung.js; tệp Desk không còn cuộn thẳng chỗ nào. */
  var c = require('fs').readFileSync(path.join(GOC, 'vagabond', 'public', 'js', 'cai_dat_loi_chung.js'), 'utf8');
  la('tệp Desk không gọi thẳng scroll_to_field', (s.match(/scroll_to_field\(/g) || []).length, 0);
  la('chỉ một chỗ gọi scroll_to_field, nằm trong moToi ở tệp chung', (c.match(/scroll_to_field\(/g) || []).length, 1);
});

ca('tình trạng: ô chỉ có dấu cách coi như trống', function () {
  la('dấu cách', tim(V.tinhTrang({ goong_api_key: '   ' }, BAY_GIO), 'Goong bản đồ').trang, 'no');
});

ca('thư cảnh báo: hú còi trong 24 giờ là ĐỎ kèm số giờ, quá 24 giờ thì về bình thường', function () {
  var d = { email_canh_bao: 'a@b.c', email_bao_dong_lan_cuoi: '2026-10-04 08:00:00' };
  var t = tim(V.tinhTrang(d, BAY_GIO), 'Thư cảnh báo');
  la('đỏ', t.trang, 'err');
  la('ghi số giờ', t.ghi, 'hú còi 2 giờ trước');
  d.email_bao_dong_lan_cuoi = '2026-10-04 09:40:00';
  la('dưới một giờ', tim(V.tinhTrang(d, BAY_GIO), 'Thư cảnh báo').ghi, 'hú còi chưa tới 1 giờ trước');
  d.email_bao_dong_lan_cuoi = '2026-10-02 08:00:00';
  la('quá 24 giờ', tim(V.tinhTrang(d, BAY_GIO), 'Thư cảnh báo').trang, 'ok');
  la('không có đường gửi', tim(V.tinhTrang({}, BAY_GIO), 'Thư cảnh báo').trang, 'no');
});

ca('mỗi chip tình trạng nhảy tới một ô và nằm ở một mục có thật', function () {
  V.tinhTrang({}, BAY_GIO).forEach(function (t) {
    dung(t.ten + ' có ô để nhảy tới', !!t.toi);
    dung(t.ten + ' có mục', !!t.muc);
  });
});

ca('chip trên đầu mục Tự động hoá đếm đúng số công tắc đang bật', function () {
  var m = V.tinhTrangMuc({ tu_xuat_hddt: 1, tu_ghi_so_bat: 0, hang_tang_xuat_kho_that: 1 }, BAY_GIO);
  la('hai trên ba', m.sec_vgb_tu_dong, { trang: 'ok', ghi: 'Đang bật 2/3' });
  la('không cái nào', V.tinhTrangMuc({}, BAY_GIO).sec_vgb_tu_dong, { trang: 'no', ghi: 'Đang bật 0/3' });
  la('mục m-invoice lấy theo kết nối', V.tinhTrangMuc({}, BAY_GIO).sec_minvoice.trang, 'no');
});

var MAU = {
  vgb_diem_ban: JSON.stringify([
    { ma: 'TCV', ten: 'Trần Cao Văn', co_quay: 1 },
    { ma: 'NVHTN', ten: 'Nhà Văn hoá TN', co_quay: 1 },
    { ma: 'SALES', ten: 'Sales', co_quay: 0 }]),
  vgb_tai_khoan_nhan: JSON.stringify({
    mac_dinh: { bank: 'MB', stk: 'VQRQ00033k5p6', ten: 'X' },
    theo_nguon: [
      { bank: 'MB', stk: 'VQRQALEAF2999', nguon: '@diem:TCV', dung: 1 },
      { bank: 'MB', stk: 'VQRQALEAI0938', nguon: '@diem:NVHTN', dung: 1 },
      { bank: 'MB', stk: 'VQRQZZ1111', nguon: '@phieu_cong_no', dung: 0 },
      { bank: 'MB', stk: 'VQRQZZ2222', nguon: '@diem:LA', dung: 1 }] }),
  vgb_pt_thanh_toan_ds: JSON.stringify([
    { ten: 'TM', nhan: 'Tiền mặt', bat: 1 }, { ten: 'CK', nhan: 'Chuyển khoản', bat: 1 },
    { ten: 'THE', nhan: 'Thẻ', bat: 0 }]),
  vgb_may_in: JSON.stringify([{ ma: 'a' }, { ma: 'b' }]),
  vgb_pancake_nhip: JSON.stringify({ luc_ok: 1, ok_luc_nao: '04/10 09:55', loi: '', luc_hong: 0 }),
  vgb_hddt_quay: 'TCV,NVHTN',
  vgb_quyen_bo_mon: 'gioi_han',
};

ca('tóm tắt tài khoản: nguồn @diem hiện TÊN điểm bán, số tài khoản chỉ hiện bốn số cuối', function () {
  var tk = V.tomTat(MAU).the[0];
  la('tên thẻ', tk.ten, 'Tài khoản nhận chuyển khoản');
  la('dòng phụ', tk.phu, 'Mặc định: MB …k5p6');
  la('dòng đầu', tk.dong[0], { trai: 'Trần Cao Văn', giua: 'MB …2999', trang: 'ok', nhan: 'Dùng' });
  la('phiếu đòi nợ đang tắt', tk.dong[2], { trai: 'Phiếu đòi nợ khách sỉ', giua: 'MB …1111', trang: 'no', nhan: 'Tắt' });
  var la1 = V.tomTat({ vgb_tai_khoan_nhan: JSON.stringify({ theo_nguon: [{ bank: 'MB', stk: 'VQRQZZ2222', nguon: '@diem:LA' }] }) }).the[0];
  la('mã điểm chưa có trong danh sách thì hiện mã', la1.dong[0].trai, 'Điểm LA');
  dung('không lộ số tài khoản đầy đủ', JSON.stringify(V.tomTat(MAU)).indexOf('VQRQALEAF2999') < 0);
  la('mở đúng màn sửa trong app', tk.duong, '/tai-khoan-ke-toan');
});

ca('tóm tắt: ô mã hỏng định dạng thì báo đỏ, không làm hỏng cả trang', function () {
  var t = V.tomTat({ vgb_tai_khoan_nhan: '{"mac_dinh": ', vgb_diem_ban: '[{' });
  dung('thẻ tài khoản báo lỗi', t.the[0].loi === 1);
  dung('thẻ điểm bán báo lỗi', t.the[1].loi === 1);
  la('vẫn đủ ba thẻ', t.the.length, 3);
});

ca('tóm tắt: điểm bán, phương thức thanh toán, máy in đếm đúng', function () {
  var t = V.tomTat(MAU);
  la('điểm bán', t.the[1].phu, '3 điểm, 2 điểm có quầy');
  la('phương thức', t.the[2].phu, '3 phương thức, 2 đang bật');
  la('chip phương thức chỉ lấy cái đang bật', t.the[2].chip, ['Tiền mặt', 'Chuyển khoản']);
  la('máy in', tim(t.dong, 'Danh sách máy in').ghi, '2 máy');
  la('cân tem chưa khai', tim(t.dong, 'Cân in tem').ghi, 'Chưa khai');
});

ca('tóm tắt: ô lưu chữ thường (không phải mã) hiện nguyên chữ, không coi là hỏng', function () {
  var t = V.tomTat(MAU);
  la('hoá đơn điện tử quầy', tim(t.dong, 'Điểm bán tự xuất hoá đơn điện tử').ghi, 'TCV,NVHTN');
  la('quyền bỏ món', tim(t.dong, 'Quyền bỏ món khỏi bill').ghi, 'Giới hạn theo quyền');
});

ca('tóm tắt: nhịp Pancake báo lỗi thì dòng đó đỏ', function () {
  la('đang chạy', tim(V.tomTat(MAU).dong, 'Nhịp kéo đơn Pancake').ghi, 'Kéo được lần cuối 04/10 09:55');
  var d = Object.assign({}, MAU, { vgb_pancake_nhip: JSON.stringify({ loi: 'Timeout', ok_luc_nao: 'x' }) });
  dung('có lỗi là đỏ', tim(V.tomTat(d).dong, 'Nhịp kéo đơn Pancake').loi === 1);
});

ca('tóm tắt: trang trống hoàn toàn vẫn vẽ đủ thẻ và dòng', function () {
  var t = V.tomTat({});
  la('ba thẻ', t.the.length, 3);
  dung('tài khoản báo chưa khai', /Chưa khai/.test(t.the[0].phu));
  dung('mọi dòng có đường sửa', t.dong.every(function (r) { return r.duong && r.duong.charAt(0) === '/'; }));
});

var DS = [
  { fn: 'ahamove_api_key', nhan: 'Khoá API Ahamove', mo: '', tab: 'Giao hàng', muc: 'Ahamove' },
  { fn: 'ngan_hang_bin', nhan: 'Mã BIN ngân hàng', mo: 'Bấm chọn ngân hàng', tab: 'Bán hàng & thanh toán', muc: 'Chuyển khoản VietQR' },
  { fn: 'qz_may_in_tem', nhan: 'Mảnh tên máy in TEM ly, tem hộp', mo: '', tab: 'Thiết bị & trợ lý', muc: 'In ngầm QZ Tray' },
  { fn: 'qz_may_in_hoa_don', nhan: 'Mảnh tên máy in HOÁ ĐƠN', mo: '', tab: 'Thiết bị & trợ lý', muc: 'In ngầm QZ Tray' },
  { fn: 'diem_quy_doi', nhan: '1 điểm bằng bao nhiêu đồng', mo: '', tab: 'Khách hàng & điểm', muc: 'Điểm thành viên' },
];

ca('ô tìm: gõ không dấu vẫn ra, khớp mọi từ, khớp cả tên mục và tab', function () {
  la('khoa ahamove', V.timTruong('khoa ahamove', DS).map(function (x) { return x.fn; }), ['ahamove_api_key']);
  la('may in', V.timTruong('may in', DS).map(function (x) { return x.fn; }).sort(), ['qz_may_in_hoa_don', 'qz_may_in_tem']);
  la('theo tên mục', V.timTruong('vietqr', DS).map(function (x) { return x.fn; }), ['ngan_hang_bin']);
  la('chữ đ', V.timTruong('diem thanh vien', DS).map(function (x) { return x.fn; }), ['diem_quy_doi']);
  la('trống', V.timTruong('   ', DS), []);
  la('không khớp', V.timTruong('xyz', DS), []);
});

ca('ô tìm: khớp ở NHÃN xếp trên khớp ở tên mục', function () {
  var ds = [
    { fn: 'a', nhan: 'Địa chỉ API Ahamove', mo: '', tab: 'Giao hàng', muc: 'Ahamove' },
    { fn: 'b', nhan: 'Mã dịch vụ', mo: '', tab: 'Giao hàng', muc: 'Ahamove' },
  ];
  la('nhãn lên trước', V.timTruong('ahamove', ds).map(function (x) { return x.fn; }), ['a', 'b']);
});

ca('Codex #433 F1: SePay chỉ còn khoá ở khe thứ hai hoặc thứ ba vẫn là ĐÃ KHAI', function () {
  // Trước khi sửa (3364c30): chỉ có sepay_hmac_2 thì chip xám "chưa khai" dù
  // webhook vẫn chạy vì sepay._cac_khoa() thử cả ba khe.
  ['sepay_khoa_2', 'sepay_hmac_2', 'sepay_hmac_3', 'sepay_khoa', 'sepay_hmac'].forEach(function (k) {
    var d = { sepay_bat: 1 }; d[k] = '****';
    la(k, tim(V.tinhTrang(d, BAY_GIO), 'SePay ngân hàng').trang, 'ok');
  });
  la('không khe nào', tim(V.tinhTrang({ sepay_bat: 1 }, BAY_GIO), 'SePay ngân hàng').trang, 'no');
});

ca('Codex #433 F3: thẻ tài khoản 12 dòng chỉ hiện 3 dòng đầu và đếm phần còn lại', function () {
  // Trước khi sửa: 12 dòng hiện đủ 12, đẩy nút Sửa ở app và các thẻ khác xuống.
  var tn = [];
  for (var i = 0; i < 12; i++) tn.push({ bank: 'MB', stk: 'VQR' + i + '0000', nguon: '@diem:D' + i, dung: 1 });
  var the = V.tomTat({ vgb_tai_khoan_nhan: JSON.stringify({ mac_dinh: { bank: 'MB', stk: 'x' }, theo_nguon: tn }) }).the[0];
  la('số dòng hiện', the.dong.length, 3);
  la('còn lại', the.con, 9);
  var it = V.tomTat(MAU).the[0];
  la('đúng 3 dòng thì không có dòng còn lại', [it.dong.length, it.con || 0], [3, 1]);
  var db = V.tomTat({ vgb_diem_ban: JSON.stringify([{ ma: 'a' }, { ma: 'b' }]) }).the[1];
  la('ít dòng thì hiện đủ', [db.dong.length, db.con || 0], [2, 0]);
});

var DM_NH = [
  { bin: '970422', ten: 'MB Bank', ma: 'MB' }, { bin: '970448', ten: 'OCB', ma: 'OCB' },
  { bin: '970405', ten: 'Agribank', ma: 'VBA' }, { bin: '970432', ten: 'VPBank', ma: 'VPB' },
  { bin: '970436', ten: 'Vietcombank', ma: 'VCB' },
];
ca('Codex #433 F2: ô chọn ngân hàng tìm trong danh mục máy chủ, kể cả ngân hàng ngoài nhóm hay dùng', function () {
  la('agribank', V.timNganHang('agri', DM_NH).map(function (n) { return n.bin; }), ['970405']);
  la('theo mã viết tắt', V.timNganHang('vpb', DM_NH).map(function (n) { return n.bin; }), ['970432']);
  la('theo BIN', V.timNganHang('970448', DM_NH).map(function (n) { return n.ten; }), ['OCB']);
  la('trống', V.timNganHang('', DM_NH), []);
  la('BIN đang lưu ra đúng tên', V.nganHangTheoBin(DM_NH, ' 970422 ').ten, 'MB Bank');
  la('BIN lạ', V.nganHangTheoBin(DM_NH, '123456'), null);
  dung('JS không còn giữ danh sách ngân hàng riêng', V.NGAN_HANG === undefined);
});

ca('hộp chọn Zalo: mọi mã loại tin và chủ đề đều có tên, biểu tượng và dòng giải thích', function () {
  // Anh Việt 04/10/2026, kèm ảnh hộp chọn chỉ có mã ban_tin, canh_bao: "không có
  // subtext để biết tin đó là tin gì". Mã mới thêm vào danh mục mà quên giải
  // thích thì ca này đỏ.
  ['loai_tin', 'chu_de'].forEach(function (k) {
    V.ZALO_DANH_MUC[k].forEach(function (ma) {
      var n = V.ZALO_NHAN[k][ma];
      dung(k + '.' + ma + ' có nhãn', !!n);
      dung(k + '.' + ma + ' có biểu tượng', !!(n && n[0]));
      dung(k + '.' + ma + ' tên có dấu, không phải mã', n && n[1] && n[1] !== ma && /[^\x00-\x7f]/.test(n[1] + n[2]));
      dung(k + '.' + ma + ' giải thích đủ một câu', n && n[2] && n[2].length >= 15);
    });
    la(k + ' không thừa nhãn ngoài danh mục', Object.keys(V.ZALO_NHAN[k]).sort(), V.ZALO_DANH_MUC[k].slice().sort());
  });
  dung('Cảnh báo nói rõ là loại vẫn gửi trong giờ im', /giờ im/.test(V.ZALO_NHAN.loai_tin.canh_bao[2]));
});

/* ---- Ô chọn ngân hàng trên Desk khi tải danh mục hỏng (Codex #433 vòng 3 G3) ----
   Chạy THẬT veNganHang trên DOM giả với một $ tối thiểu (chỉ các hàm hàm này dùng)
   và frappe.call giả trả về ngay (đồng bộ) để ca chạy tuần tự. */
var dg = require('./dom_gia.js');
function W(els) {
  var w = {
    els: els, length: els.length,
    find: function (sel) { var r = []; els.forEach(function (e) { r = r.concat(e.querySelectorAll(sel)); }); return W(r); },
    first: function () { return W(els.slice(0, 1)); },
    addClass: function (c) { els.forEach(function (e) { var l = String(e.getAttribute('class') || '').split(/\s+/).filter(Boolean); if (l.indexOf(c) < 0) l.push(c); e.setAttribute('class', l.join(' ')); }); return w; },
    removeClass: function (c) { els.forEach(function (e) { e.setAttribute('class', String(e.getAttribute('class') || '').split(/\s+/).filter(function (x) { return x && x !== c; }).join(' ')); }); return w; },
    remove: function () { els.forEach(function (e) { e.remove(); }); return w; },
    appendTo: function (t) { t.els[0].appendChild(els[0]); return w; },
    html: function (h) { els.forEach(function (e) { e.innerHTML = h; }); return w; },
    on: function (ev, sel, fn) { els.forEach(function (e) { (e._jq = e._jq || []).push({ ev: ev, sel: sel, fn: fn }); }); return w; },
    append: function (h) { els.forEach(function (e) { var c = new dg.ElementGia('div'); c.innerHTML = h; c.children.slice().forEach(function (k) { e.appendChild(k); }); }); return w; },
    val: function (v) { if (v === undefined) return els[0] ? els[0].value : undefined; els.forEach(function (e) { e.value = v; }); return w; },
    is: function (sel) { return els.some(function (e) { return e.closest(sel) === e; }); },
    text: function (t) { if (t === undefined) return els.map(chuEl).join(''); els.forEach(function (e) { e.innerHTML = ''; e._chu = String(t); }); return w; },
    insertBefore: function (t) { var d = t.els[0], cha = d.parentNode; cha.insertBefore(els[0], d); return w; },
    prependTo: function (t) { t.els[0].appendChild(els[0]); return w; },
    off: function () { els.forEach(function (e) { e._jq = []; }); return w; },
    attr: function (k) { return els[0] ? els[0].getAttribute(k) : undefined; },
    hasClass: function (c) { return els.some(function (e) { return String(e.getAttribute('class') || '').split(/\s+/).indexOf(c) >= 0; }); },
  };
  return w;
}
function $(x) {
  if (typeof x === 'string') { var c = new dg.ElementGia('div'); c.innerHTML = x; return W(c.children.slice()); }
  return W([].concat(x));
}
function bamJq(goc, dich) {
  (goc._jq || []).forEach(function (hd) { if (String(hd.ev).split('.')[0] === 'click' && dich.closest(hd.sel)) hd.fn.call(dich, { preventDefault: function () {} }); });
}
global.frappe.utils = global.frappe.utils || { escape_html: function (x) { return String(x == null ? '' : x).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); } };
function lop(el) { return String(el.getAttribute('class') || ''); }
function chuEl(el) { var s = el._chu || ''; (el.children || []).forEach(function (c) { s += chuEl(c); }); return s; }

// Codex #435 I1 ĐỔI yêu cầu của vòng 3: tải hỏng thì KHÔNG được lộ ô BIN gốc (gõ tay
// được một BIN lạ mà tên ngân hàng không đổi theo). Ba ca dưới vì vậy chốt: ô gốc
// luôn ẩn, nhưng mã đang lưu vẫn hiện, có báo lỗi và nút Thử lại.
ca('Codex #433 vòng 3 G3 + #435 I1: tải danh mục hỏng thì hiện mã đang lưu, báo lỗi, nút Thử lại, KHÔNG cho gõ tay; thử lại được thì ra ô chọn', function () {
  global.$ = $;
  var goc = new dg.ElementGia('div');
  goc.innerHTML = '<div class="control-input"><input></div>';
  var lanGoi = 0, hong = true;
  global.frappe.call = function () {
    lanGoi++;
    return { then: function (ok, loi) { if (hong) loi(new Error('mất mạng')); else ok({ message: { ngan_hang: DM_NH } }); } };
  };
  var frm = { fields_dict: { ngan_hang_bin: { $wrapper: W([goc]) } }, doc: { ngan_hang_bin: '970422', ngan_hang_hien_thi: 'MB Bank' }, set_value: function () {} };
  V._desk.veNganHang(frm);
  var ci = goc.querySelectorAll('.control-input')[0];
  dung('ô BIN gốc bị ẩn, không gõ tay được', lop(ci).indexOf('vgbc-anchon-in') >= 0);
  var k = goc.querySelectorAll('.vgbc-nh')[0];
  dung('vẫn thấy ngân hàng đang lưu', chuEl(k).indexOf('Đang lưu: MB Bank · BIN 970422') >= 0);
  dung('báo không tải được', chuEl(k).indexOf('Không tải được danh mục ngân hàng') >= 0);
  la('không có ô nhập nào trong khung', k.querySelectorAll('input').length, 0);
  var nut = goc.querySelectorAll('.vgbc-thu-lai');
  la('có nút Thử lại', nut.length, 1);
  hong = false;
  bamJq(k, nut[0]);
  la('gọi lại máy chủ', lanGoi, 2);
  ci = goc.querySelectorAll('.control-input')[0];
  dung('tải được thì mới ẩn ô BIN gốc', lop(ci).indexOf('vgbc-anchon-in') >= 0);
  la('chỉ còn một khung chọn', goc.querySelectorAll('.vgbc-nh').length, 1);
  dung('chip đang dùng MB Bank', chuEl(goc.querySelectorAll('.vgbc-nh')[0]).indexOf('Đang dùng: MB Bank') >= 0);
  dung('có ô tìm ngân hàng', goc.querySelectorAll('.vgbc-tim').length === 1);
});

ca('Codex #433 vòng 3 G3 + #435 I1: đang chờ tải danh mục thì hiện mã đang lưu và chữ Đang tải, không khung trống, không gõ tay', function () {
  global.$ = $;
  var goc = new dg.ElementGia('div');
  goc.innerHTML = '<div class="control-input"><input></div>';
  global.frappe.call = function () { return { then: function () {} }; };
  V._desk.veNganHang({ fields_dict: { ngan_hang_bin: { $wrapper: W([goc]) } }, doc: { ngan_hang_bin: '970405' }, set_value: function () {} });
  dung('ô BIN gốc ẩn khi đang chờ', lop(goc.querySelectorAll('.control-input')[0]).indexOf('vgbc-anchon-in') >= 0);
  var k = goc.querySelectorAll('.vgbc-nh')[0];
  dung('thấy BIN đang lưu', chuEl(k).indexOf('BIN 970405') >= 0);
  dung('có chữ đang tải', chuEl(k).indexOf('Đang tải danh mục ngân hàng') >= 0);
});

ca('Codex #435 I2: Zalo ZNS cần ít nhất một mã mẫu, WhatsApp cần mẫu thanh toán, mới là đã khai', function () {
  // Trên 83fdbcf cả hai ra xanh khi thiếu mẫu, dù zalo.gui_tin và whatsapp.gui_mau từ chối đúng cấu hình đó.
  var z = { zalo_app_id: '1', zalo_app_secret: '*', zalo_refresh_token: '*' };
  la('ZNS chưa có mẫu nào', tim(V.tinhTrang(z, BAY_GIO), 'Zalo ZNS gửi khách').trang, 'no');
  ['zns_template_otp', 'zns_template_thanh_toan', 'zns_template_diem'].forEach(function (m) {
    var d = Object.assign({}, z); d[m] = 'T';
    la('ZNS có mẫu ' + m, tim(V.tinhTrang(d, BAY_GIO), 'Zalo ZNS gửi khách').trang, 'ok');
  });
  var w = { wa_phone_id: '1', wa_token: '*' };
  la('WhatsApp thiếu mẫu thanh toán', tim(V.tinhTrang(w, BAY_GIO), 'WhatsApp').trang, 'no');
  w.wa_template_thanh_toan = 'thanh_toan_vi';
  la('WhatsApp đủ', tim(V.tinhTrang(w, BAY_GIO), 'WhatsApp').trang, 'ok');
});

ca('Codex #435 vòng 6: BIN đang lưu ngoài danh mục không bị báo lỗi; khai ngân hàng ngoài danh sách phải đủ BIN 6 số và tên, ghi cả hai một lượt', function () {
  // Trên a2419ff: BIN 546034 (ngoài 43 ngân hàng) hiện chip ĐỎ "không có trong danh
  // mục" và không có cách nào chọn lại, vì ô BIN gốc đã ẩn.
  global.$ = $;
  var goc = new dg.ElementGia('div');
  goc.innerHTML = '<div class="control-input"><input></div>';
  var ghi = [];
  global.frappe.call = function () { return { then: function (ok) { ok({ message: { ngan_hang: DM_NH } }); } }; };
  var frm = { fields_dict: { ngan_hang_bin: { $wrapper: W([goc]) } }, doc: { ngan_hang_bin: '546034', ngan_hang_hien_thi: 'CAKE by VPBank' },
    set_value: function (k, v) { ghi.push([k, v]); } };
  V._desk.veNganHang(frm);
  var k = goc.querySelectorAll('.vgbc-nh')[0];
  var c = k.querySelectorAll('.vgbc-chip')[0];
  dung('chip vàng, không đỏ', lop(c).indexOf('vgbc-off') >= 0 && lop(c).indexOf('vgbc-err') < 0);
  dung('chip ghi tên và BIN đang lưu', chuEl(c).indexOf('CAKE by VPBank · BIN 546034') >= 0);
  bamJq(k, k.querySelectorAll('.vgbc-khac')[0]);
  la('hiện ô BIN và ô tên', [k.querySelectorAll('.vgbc-bin-moi').length, k.querySelectorAll('.vgbc-ten-moi').length], [1, 1]);
  k.querySelectorAll('.vgbc-bin-moi')[0].value = '12345';
  k.querySelectorAll('.vgbc-ten-moi')[0].value = 'Ngân hàng X';
  bamJq(k, k.querySelectorAll('.vgbc-dung-khac')[0]);
  la('BIN sai thì không ghi gì', ghi, []);
  dung('báo lỗi 6 chữ số', chuEl(k.querySelectorAll('.vgbc-loi-khac')[0]).indexOf('6 chữ số') >= 0);
  k.querySelectorAll('.vgbc-bin-moi')[0].value = '970999';
  k.querySelectorAll('.vgbc-ten-moi')[0].value = '';
  bamJq(k, k.querySelectorAll('.vgbc-dung-khac')[0]);
  la('thiếu tên thì không ghi gì', ghi, []);
  k.querySelectorAll('.vgbc-ten-moi')[0].value = ' Ngân hàng X ';
  bamJq(k, k.querySelectorAll('.vgbc-dung-khac')[0]);
  la('đủ thì ghi cả hai ô một lượt', ghi, [['ngan_hang_bin', '970999'], ['ngan_hang_hien_thi', 'Ngân hàng X']]);
});

ca('Codex #435 vòng 7: Zalo bắn tin nhóm chỉ xanh khi có ít nhất một nhóm ĐANG BẬT và CÓ mã chat', function () {
  // Trên 7c36d4d: token + công tắc bật mà bảng nhóm rỗng vẫn xanh, trong khi
  // kenh_zalo.chon_nhom trả rỗng và mọi tin tự động bị bỏ âm thầm.
  var d = { zalo_bot_token: '*', zalo_bot_bat: 1 };
  la('không có bảng nhóm', tim(V.tinhTrang(d, BAY_GIO), 'Zalo bắn tin nhóm').trang, 'no');
  d.zalo_nhom = [];
  la('bảng nhóm rỗng', tim(V.tinhTrang(d, BAY_GIO), 'Zalo bắn tin nhóm').trang, 'no');
  d.zalo_nhom = [{ chat_id: 'g1', bat: 0 }, { chat_id: '', bat: 1 }, { chat_id: '  ', bat: 1 }];
  la('mọi nhóm tắt hoặc thiếu mã chat', tim(V.tinhTrang(d, BAY_GIO), 'Zalo bắn tin nhóm').trang, 'no');
  d.zalo_nhom.push({ chat_id: 'g2', bat: 1 });
  la('có một nhóm bật và có mã chat', tim(V.tinhTrang(d, BAY_GIO), 'Zalo bắn tin nhóm').trang, 'ok');
});

ca('Codex #435 vòng 7: chỉ có tên ngân hàng mà không BIN thì bị chặn; nút Thử lại và Dùng ngân hàng này cao 44px', function () {
  la('trống cả hai là hợp lệ (dùng MB)', V.kiemCapNganHang('', ''), null);
  dung('chỉ có tên thì báo lỗi', /phải có Mã BIN/.test(V.kiemCapNganHang('', 'Ngân hàng X') || ''));
  dung('tên toàn dấu cách coi như trống', V.kiemCapNganHang('', '   ') === null);
  // CSS không chạy trong node; dò chuỗi chỉ để ghim con số (điều 16).
  var s = require('fs').readFileSync(path.join(GOC, 'vagabond', 'vagabond', 'doctype', 'vagabond_settings', 'vagabond_settings.js'), 'utf8');
  dung('luật 44px cho hai nút ngân hàng', /\.vgbc-thu-lai,\.vgb-cd \.vgbc-dung-khac\{min-height:44px/.test(s));
});

ca('Codex #435 H1: chip tình trạng hiện TRÊN đầu mục (s.head chính là .section-head như Frappe 16)', function () {
  // Dựng đúng hình dạng đo trên site thật: s.head có lớp section-head, con duy nhất
  // là .collapse-indicator. Trên 0613faa chip tìm .section-head BÊN TRONG nên rỗng.
  global.$ = $;
  var head = new dg.ElementGia('div');
  head.setAttribute('class', 'section-head collapsible');
  head.innerHTML = 'Goong bản đồ<span class="collapse-indicator"></span>';
  var frm = { doc: { goong_api_key: '*' }, layout: { sections: [{ df: { fieldname: 'sec_goong' }, head: W([head]) }, { df: { fieldname: 'sec_khong_co' }, head: W([new dg.ElementGia('div')]) }] } };
  V._desk.veChipMuc(frm);
  var c = head.querySelectorAll('.vgbc-chip');
  la('một chip trên đầu mục Goong', c.length, 1);
  dung('chip ghi đã khai', chuEl(c[0]).indexOf('đã khai') >= 0);
  V._desk.veChipMuc(frm);
  la('vẽ lại không nhân đôi chip', head.querySelectorAll('.vgbc-chip').length, 1);
});

ca('Codex #435 H2: thanh tình trạng thu gọn hai dòng, chip cần để ý xếp lên đầu, nút Xem đủ mở và thu lại', function () {
  global.$ = $;
  var goc = new dg.ElementGia('div');
  goc.innerHTML = '<div class="form-tabs-list"></div>';
  var frm = { doc: { goong_api_key: '*', pancake_api_key: '*', pancake_shop_id: '1', zalo_bot_token: '*', zalo_bot_bat: 0, zalo_nhom: [{ chat_id: 'g1', bat: 1 }] },
    layout: { wrapper: goc }, fields_dict: {}, meta: { fields: [] } };
  V._desk.veThanh(frm);
  var tt = goc.querySelectorAll('.vgbc-tt')[0];
  dung('mặc định thu gọn', lop(tt).split(' ').indexOf('gon') >= 0);
  var chips = tt.querySelectorAll('.vgbc-chip');
  la('đủ mọi kết nối', chips.length, V.KET_NOI.length + 1);
  dung('chip đầu là vàng (Zalo khai rồi mà tắt), không phải xanh', lop(chips[0]).indexOf('vgbc-off') >= 0);
  dung('chip xanh nằm cuối', lop(chips[chips.length - 1]).indexOf('vgbc-ok') >= 0);
  var nut = goc.querySelectorAll('.vgbc-xem')[0];
  dung('nút ghi số kết nối và số cần để ý', /Xem đủ \d+ kết nối \(\d+ cần để ý/.test(chuEl(nut)));
  bamJq(goc.querySelectorAll('.vgbc-bar')[0], nut);
  tt = goc.querySelectorAll('.vgbc-tt')[0];
  dung('bấm Xem đủ thì mở', lop(tt).split(' ').indexOf('gon') < 0);
  la('nút đổi thành Thu gọn', chuEl(goc.querySelectorAll('.vgbc-xem')[0]), 'Thu gọn');
  la('vẽ lại không nhân đôi thanh', goc.querySelectorAll('.vgbc-bar').length, 1);
});

ca('Codex #435 H2: xếp chip đỏ, vàng, xám rồi xanh; cùng màu giữ thứ tự gốc', function () {
  var ds = [{ ten: 'a', trang: 'ok' }, { ten: 'b', trang: 'no' }, { ten: 'c', trang: 'err' }, { ten: 'd', trang: 'no' }, { ten: 'e', trang: 'off' }];
  la('thứ tự', V.xepTinhTrang(ds).map(function (t) { return t.ten; }), ['c', 'e', 'b', 'd', 'a']);
  la('không đổi mảng gốc', ds.map(function (t) { return t.ten; }), ['a', 'b', 'c', 'd', 'e']);
});

ca('Codex #435 H3: chip bấm được cao 44px, hai dòng chip đúng bằng chiều cao thu gọn', function () {
  // CSS không chạy trong node; dò chuỗi chỉ để GHIM con số (điều 16). Ảnh site thật đính sau deploy.
  var s = require('fs').readFileSync(path.join(GOC, 'vagabond', 'vagabond', 'doctype', 'vagabond_settings', 'vagabond_settings.js'), 'utf8');
  var m = /\.vgbc-chip\[data-toi\]\{min-height:(\d+)px\}/.exec(s);
  dung('có luật chiều cao cho chip bấm được', !!m);
  la('cao 44px', m && +m[1], 44);
  var g = /\.vgbc-tt\.gon\{max-height:(\d+)px/.exec(s);
  var khe = /\.vgbc-chips\{display:flex;flex-wrap:wrap;gap:(\d+)px\}/.exec(s);
  la('thu gọn = 2 dòng chip + 1 khe', g && +g[1], 2 * 44 + (khe ? +khe[1] : -1));
});

ca('v571: công tắc đủ 42x24 trên site thật, hộp chứa không bị Frappe ép còn 26px', function () {
  // Lỗi đo trên site thật sau deploy v570: Frappe ép ô tích 18px, .input-area flex
  // rộng 26px, công tắc thành nửa hình tròn đè chữ. CSS không chạy trong node; dò
  // chuỗi chỉ để GHIM luật đã thử đúng trên site (điều 16), bằng chứng là ảnh trên PR.
  var s = require('fs').readFileSync(path.join(GOC, 'vagabond', 'vagabond', 'doctype', 'vagabond_settings', 'vagabond_settings.js'), 'utf8');
  dung('hộp chứa không co theo flex', /\[data-fieldtype="Check"\] \.input-area\{flex:none!important;width:auto!important;min-width:52px\}/.test(s));
  dung('công tắc ép rộng 42 có !important', /input\[type="checkbox"\]\{width:42px!important;min-width:42px!important;max-width:42px!important;height:24px!important/.test(s));
});

ca('Codex #433 vòng 3 G3: máy chủ trả danh mục rỗng cũng coi là hỏng, không để khung trống', function () {
  global.$ = $;
  var goc = new dg.ElementGia('div');
  goc.innerHTML = '<div class="control-input"><input></div>';
  global.frappe.call = function () { return { then: function (ok) { ok({ message: { ngan_hang: [] } }); } }; };
  V._desk.veNganHang({ fields_dict: { ngan_hang_bin: { $wrapper: W([goc]) } }, doc: {}, set_value: function () {} });
  dung('ô BIN gốc ẩn', lop(goc.querySelectorAll('.control-input')[0]).indexOf('vgbc-anchon-in') >= 0);
  dung('báo chưa chọn ngân hàng', chuEl(goc.querySelectorAll('.vgbc-nh')[0]).indexOf('Chưa chọn ngân hàng') >= 0);
  la('có nút Thử lại', goc.querySelectorAll('.vgbc-thu-lai').length, 1);
});

// ====================================================================
// v579: mục Bắn tin vào nhóm Zalo trên Desk. Anh Việt 06/10/2026, kèm ảnh bảng
// Nhóm nhận tin chật nửa cột chỉ thấy "ERP ...", "zgr-d...", "thong...": "Lỗi
// hiển thị, quá khó để nhập liệu ... có nút để gửi thử tin vào nhóm Zalo không?"
// Chạy THẬT veZalo và suaNhomZalo của vagabond_settings.js trên DOM giả.
// ====================================================================
var MA_ZALO = V.ZALO_DANH_MUC.loai_tin.concat(V.ZALO_DANH_MUC.chu_de);
function khongLoMa(chu) { return MA_ZALO.filter(function (m) { return m.indexOf('_') > 0 && chu.indexOf(m) >= 0; }); }
function frmZalo(rows, them) {
  var nut = new dg.ElementGia('div'), the = new dg.ElementGia('div');
  var f = { an: [], con: [], dat: [], ban: 0, ve: 0,
    fields_dict: { zalo_tac_vu: { $wrapper: W([nut]) }, zalo_nhom_the: { $wrapper: W([the]) }, zalo_nhom: {} },
    doc: Object.assign({ zalo_nhom: rows, zalo_chat_moi: JSON.stringify([{ chat_id: 'zgr-ke-toan', loai: 'GROUP', ten: 'Kế toán Vagabond' },
      { chat_id: 'u-123', loai: 'PRIVATE', ten: 'Dung' }]) }, them || {}),
    toggle_display: function (fn, hien) { f.an.push([fn, hien]); },
    add_child: function () { var r = { doctype: 'Vagabond Kenh Zalo', name: 'moi' + (f.con.length + 1) }; f.con.push(r); f.doc.zalo_nhom.push(r); return r; },
    refresh_field: function () {}, dirty: function () { f.ban++; }, is_dirty: function () { return false; }, reload_doc: function () {} };
  return { frm: f, nut: nut, the: the };
}
function giaFrappe(f) {
  var goi = [], hop = [], bao = [];
  global.frappe.call = function (o) { goi.push(o); return { then: function () {} }; };
  global.frappe.msgprint = function (m) { bao.push(m); };
  global.frappe.show_alert = function (m) { bao.push(m); };
  global.frappe.confirm = function (m, ok) { ok(); };
  global.frappe.model = { set_value: function (dt, ten, k, v) { var r = f.doc.zalo_nhom.filter(function (x) { return x.name === ten; })[0]; if (r) r[k] = v; f.dat.push([ten, k, v]); },
    clear_doc: function (dt, ten) { f.doc.zalo_nhom = f.doc.zalo_nhom.filter(function (x) { return x.name !== ten; }); } };
  global.frappe.ui.Dialog = function (o) { this.o = o; this.an = 0; hop.push(this); };
  global.frappe.ui.Dialog.prototype = { show: function () {}, hide: function () { this.an = 1; },
    set_secondary_action_label: function (t) { this.phu = t; }, set_secondary_action: function (fn) { this.phuFn = fn; } };
  return { goi: goi, hop: hop, bao: bao };
}
var ROWS = function () {
  return [{ doctype: 'Vagabond Kenh Zalo', name: 'r1', ten_nhom: 'ERP Vagabond', chat_id: 'zgr-dau', loai_tin: 'thong_bao, canh_bao', chu_de: '', bat: 1, im_tu: '22:00', im_den: '07:00' },
    { doctype: 'Vagabond Kenh Zalo', name: 'r2', ten_nhom: 'Bếp', chat_id: '', loai_tin: '', chu_de: 'kho', bat: 1 }];
};

ca('v579: mỗi nhóm Zalo là một thẻ đọc được, không lộ mã nội bộ; bảng gốc chật bị ẩn', function () {
  global.$ = $;
  var z = frmZalo(ROWS()); giaFrappe(z.frm);
  V._desk.veZalo(z.frm);
  var chu = chuEl(z.the);
  la('hai thẻ', z.the.querySelectorAll('.vgbc-card').length, 2);
  dung('tên loại tin tiếng Việt', chu.indexOf('Thông báo, Cảnh báo') >= 0);
  dung('nhóm không chọn loại là nhận mọi loại', chu.indexOf('Mọi loại tin') >= 0);
  dung('chủ đề tiếng Việt', chu.indexOf('Kho') >= 0);
  dung('giờ im đọc được', chu.indexOf('Từ 22:00 đến 07:00') >= 0);
  la('không lộ mã loại tin, chủ đề', khongLoMa(chu), []);
  dung('không lộ mã nhóm Zalo', chu.indexOf('zgr-') < 0);
  dung('báo nhóm chưa chọn nhóm Zalo', chu.indexOf('Chưa chọn nhóm Zalo') >= 0);
  la('bảng gốc bị ẩn', z.frm.an, [['zalo_nhom', false]]);
  la('chỉ nhóm có mã chat mới có nút Gửi thử', z.the.querySelectorAll('[data-zlg]').length, 1);
  la('mỗi thẻ có nút Sửa, cộng nút Thêm', z.the.querySelectorAll('[data-zls]').length, 3);
});

ca('v579: bấm Gửi thử trên thẻ gửi đúng mã nhóm đó', function () {
  global.$ = $;
  var z = frmZalo(ROWS()), g = giaFrappe(z.frm);
  V._desk.veZalo(z.frm);
  bamJq(z.the, z.the.querySelectorAll('[data-zlg]')[0]);
  la('gọi gửi thử', g.goi.map(function (o) { return [o.method, o.args.chat_id]; }), [['vagabond.kenh_zalo.gui_thu', 'zgr-dau']]);
});

ca('v579: hàng nút Zalo ngay trong mục: tình trạng nối bot, Gửi thử đi thẳng khi chỉ có một nhóm, tắt khi chưa có nhóm', function () {
  global.$ = $;
  var z = frmZalo(ROWS()), g = giaFrappe(z.frm);
  V._desk.veZalo(z.frm);
  dung('chưa nối bot thì nói rõ cách làm', chuEl(z.nut).indexOf('Chưa nối bot') >= 0);
  bamJq(z.nut, z.nut.querySelectorAll('[data-zl="guithu"]')[0]);
  la('một nhóm có mã chat thì gửi luôn', g.goi.map(function (o) { return o.args && o.args.chat_id; }), ['zgr-dau']);
  var z2 = frmZalo([], { zalo_noi_trang_thai: 'Đã xác minh lúc 2026-10-06 05:30. ' }); giaFrappe(z2.frm);
  V._desk.veZalo(z2.frm);
  dung('đã nối bot', chuEl(z2.nut).indexOf('Đã nối bot') >= 0);
  dung('chưa có nhóm thì nút Gửi thử tắt', z2.nut.querySelectorAll('[data-zl="guithu"]')[0].getAttribute('disabled') !== null);
  dung('chưa có nhóm thì có lời dẫn Thêm nhóm', chuEl(z2.the).indexOf('Chưa có nhóm nào') >= 0);
});

ca('v579: hộp Thêm nhóm hiện tên và dòng giải thích từng loại tin, chỉ gợi ý nhóm (không chat riêng), lưu mã đúng cách cũ', function () {
  global.$ = $;
  var z = frmZalo(ROWS()), g = giaFrappe(z.frm);
  V._desk.veZalo(z.frm);
  bamJq(z.the, z.the.querySelectorAll('[data-zls="-1"]')[0]);
  la('mở một hộp', g.hop.length, 1);
  var o = g.hop[0].o, fs = o.fields;
  var nz = fs.filter(function (x) { return x.fieldname === 'nhom_zalo'; })[0];
  la('chỉ gợi ý nhóm đã nhắn bot', nz.options, ['Kế toán Vagabond (zgr-ke-toan)']);
  V.ZALO_DANH_MUC.loai_tin.forEach(function (ma) {
    var x = fs.filter(function (y) { return y.fieldname === 'loai_tin__' + ma; })[0];
    dung('có ô ' + ma, x && x.fieldtype === 'Check');
    dung('nhãn tiếng Việt, không lộ mã ' + ma, x.label.indexOf(V.ZALO_NHAN.loai_tin[ma][1]) >= 0 && x.label.indexOf(ma) < 0);
    dung('có dòng giải thích ' + ma, String(x.description || '').length > 10);
  });
  la('đủ ô chủ đề', fs.filter(function (y) { return /^chu_de__/.test(y.fieldname || ''); }).length, V.ZALO_DANH_MUC.chu_de.length);
  dung('nói rõ nghĩa để trống', fs.some(function (y) { return /Không tích ô nào là nhóm nhận tất cả loại tin/.test(y.description || ''); }));
  o.primary_action({ nhom_zalo: 'Kế toán Vagabond (zgr-ke-toan)', ten_nhom: ' Kế toán ', bat: 1, loai_tin__canh_bao: 1, loai_tin__viec: 1,
    chu_de__cong_no: 1, im_tu: '22:00', im_den: '07:00' });
  la('thêm một dòng', z.frm.con.length, 1);
  var r = z.frm.con[0];
  la('giá trị lưu', [r.ten_nhom, r.chat_id, r.bat, r.loai_tin, r.chu_de, r.im_tu, r.im_den],
    ['Kế toán', 'zgr-ke-toan', 1, 'viec, canh_bao', 'cong_no', '22:00', '07:00']);
  dung('đánh dấu chưa lưu và nhắc bấm Lưu', z.frm.ban === 1 && g.bao.some(function (m) { return /Bấm Lưu/.test(m.message || m); }));
  la('thẻ vẽ lại có ba nhóm', z.the.querySelectorAll('.vgbc-card').length, 3);
});

ca('v579: nhóm đã lưu nhưng không còn trong 20 chat gần nhất vẫn sửa được, không bắt chọn lại; gõ nhóm lạ thì không ghi', function () {
  global.$ = $;
  var z = frmZalo(ROWS()), g = giaFrappe(z.frm);
  var d = V._desk.suaNhomZalo(z.frm, 0);
  var nz = d.o.fields.filter(function (x) { return x.fieldname === 'nhom_zalo'; })[0];
  la('nhóm đang lưu đứng đầu gợi ý và là mặc định', [nz.options[0], nz.default], ['ERP Vagabond (zgr-dau)', 'ERP Vagabond (zgr-dau)']);
  la('ô loại tin tích sẵn đúng như đang lưu', d.o.fields.filter(function (x) { return /^loai_tin__/.test(x.fieldname || '') && x.default; }).map(function (x) { return x.fieldname; }),
    ['loai_tin__thong_bao', 'loai_tin__canh_bao']);
  d.o.primary_action({ nhom_zalo: nz.default, ten_nhom: 'ERP Vagabond', bat: 0, loai_tin__thong_bao: 1 });
  var r = z.frm.doc.zalo_nhom[0];
  la('giữ mã nhóm, đổi công tắc và loại tin', [r.chat_id, r.bat, r.loai_tin, r.chu_de], ['zgr-dau', 0, 'thong_bao', '']);
  la('không thêm dòng mới', z.frm.con.length, 0);
  dung('tắt nhóm thì thẻ vẽ lại báo Đang tắt (chip vàng)', chuEl(z.the).indexOf('Đang tắt') >= 0 && z.the.querySelectorAll('.vgbc-off').length === 1);
  var d2 = V._desk.suaNhomZalo(z.frm, -1);
  d2.o.primary_action({ nhom_zalo: 'gõ bừa', ten_nhom: 'X', bat: 1 });
  la('nhóm lạ không ghi', z.frm.con.length, 0);
  dung('báo chọn trong gợi ý', g.bao.some(function (m) { return /Chọn đúng một nhóm Zalo/.test(m); }));
  la('sửa nhóm có nút Xoá', d.phu, 'Xoá nhóm này');
  d.phuFn();
  la('xoá đúng nhóm', z.frm.doc.zalo_nhom.map(function (x) { return x.name; }), ['r2']);
});


// v581 Codex #447 (finding 1): menu Zalo trên thanh công cụ (Nối Zalo Bot, Kiểm lại
// đường nhận) gọi máy chủ rồi reload_doc mà KHÔNG chặn khi form chưa lưu, nên vừa
// chạy trên cấu hình cũ vừa xoá bản nháp. Ca này chạy THẬT mọi hàm refresh đã đăng
// ký và bấm THẬT nút trên thanh công cụ, không gọi hàm nội bộ nào khác.
ca('v581: menu Zalo trên thanh công cụ cũng chặn khi form chưa lưu, không xoá bản nháp', function () {
  global.$ = $;
  ['Nối Zalo Bot', 'Kiểm lại đường nhận'].forEach(function (ten) {
    [true, false].forEach(function (ban) {
      var nut = {}, tai = 0;
      var frm = { doc: { zalo_nhom: [] }, fields_dict: {}, wrapper: new dg.ElementGia('div'),
        is_dirty: function () { return ban; }, reload_doc: function () { tai++; },
        add_custom_button: function (t, fn, nhom) { if (nhom === 'Zalo') (nut[t] = nut[t] || []).push(fn); } };
      var g = giaFrappe(frm);
      global.frappe.call = function (o) { g.goi.push(o); return { then: function (fn) { fn({ message: { ok: 1, loi_nhan: 'x' } }); } }; };
      DANG_KY.filter(function (x) { return x[0] === 'Vagabond Settings' && x[1].refresh; })
        .forEach(function (x) { try { x[1].refresh(frm); } catch (e) { /* phần vẽ cần Desk thật */ } });
      // Bấm MỌI nút cùng tên: lỡ còn khối đăng ký cũ đứng song song thì cũng lộ.
      la('đúng một nút ' + ten + ' trong menu Zalo', (nut[ten] || []).length, 1);
      nut[ten][0]();
      if (ban) {
        la(ten + ' khi chưa lưu: không gọi máy chủ', g.goi.length, 0);
        la(ten + ' khi chưa lưu: không tải lại form', tai, 0);
        dung(ten + ' khi chưa lưu: nhắc bấm Lưu', g.bao.some(function (m) { return String(m).indexOf('Lưu') >= 0; }));
      } else {
        la(ten + ' khi đã lưu: gọi máy chủ đúng một lần', g.goi.length, 1);
      }
    });
  });
});

console.log('\n' + dat + ' ca dat, ' + hong + ' ca hong.');
process.exit(hong ? 1 : 0);

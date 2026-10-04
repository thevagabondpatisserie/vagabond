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
global.frappe = { ui: { form: { on: function () {} } } };
var V = require(path.join(GOC, 'vagabond', 'vagabond', 'doctype', 'vagabond_settings', 'vagabond_settings.js'));

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
  var d = { zalo_bot_token: '****', zalo_bot_bat: 0 };
  la('đang tắt', tim(V.tinhTrang(d, BAY_GIO), 'Zalo bắn tin nhóm').trang, 'off');
  d.zalo_bot_bat = 1;
  la('đã bật', tim(V.tinhTrang(d, BAY_GIO), 'Zalo bắn tin nhóm').trang, 'ok');
  // Công tắc bật mà chưa khai token thì vẫn XÁM: không có gì để chạy.
  la('bật mà chưa khai', tim(V.tinhTrang({ zalo_bot_bat: 1 }, BAY_GIO), 'Zalo bắn tin nhóm').trang, 'no');
});

ca('tình trạng: GreenSM / BE xanh khi đủ MỘT trong hai nhóm khoá', function () {
  la('chỉ có client id', tim(V.tinhTrang({ greensm_client_id: 'a' }, BAY_GIO), 'GreenSM / BE').trang, 'no');
  la('đủ GreenSM', tim(V.tinhTrang({ greensm_client_id: 'a', greensm_client_secret: '*' }, BAY_GIO), 'GreenSM / BE').trang, 'ok');
  la('chỉ BE', tim(V.tinhTrang({ be_token: '*' }, BAY_GIO), 'GreenSM / BE').trang, 'ok');
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
  la('mã điểm chưa có trong danh sách thì hiện mã', tk.dong[3].trai, 'Điểm LA');
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

ca('chip ngân hàng: mã BIN không trùng nhau, mỗi chip có tên hiện cho khách', function () {
  var bin = V.NGAN_HANG.map(function (b) { return b.bin; });
  la('không trùng', bin.length, new Set(bin).size);
  dung('đủ sáu số', bin.every(function (b) { return /^\d{6}$/.test(b); }));
  dung('có tên hiện', V.NGAN_HANG.every(function (b) { return b.hien && b.hien.indexOf(b.ten.split(' ')[0]) === 0; }));
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

console.log('\n' + dat + ' ca dat, ' + hong + ' ca hong.');
process.exit(hong ? 1 : 0);

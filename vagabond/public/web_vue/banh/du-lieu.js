/* Dữ liệu tĩnh của trang đặt bánh, chép nguyên từ banh.html cũ (nguồn gốc
   và lý do từng con số ghi ở bản cũ). Tên, giá, ảnh thật được làm tươi từ
   máy chủ qua tronMon(); danh sách ở đây chỉ là nền khi máy chủ chưa trả. */
import {ROSE, ANH_DUNG_CU, ANH_NEN_SO, ANH_PHU_KIEN} from './anh.js';

export const CONFIG = {
  messenger: 'https://m.me/thevagabond.saigon',
  prepHours: 4,      /* bếp cần tối thiểu 4 tiếng cho đơn trong ngày */
  tomorrowFrom: 13   /* đơn cho NGÀY MAI chỉ nhận từ 13h */
};

/* Thẻ Pancake shop 67355: xuất hoá đơn, bánh tặng. */
export const THE_XUAT_HOA_DON = 74;
export const THE_BANH_TANG = 68;
const CDN = 'https://content.pancake.vn/';
export const ANH_NEN = '/assets/vagabond/web_order/anh-bia.png';

/* Khung giờ = thẻ Pancake, id = giờ bắt đầu + 76. */
export const SLOTS = [
  {id: 83, t: '7h - 9h', from: 7}, {id: 84, t: '8h - 10h', from: 8}, {id: 85, t: '9h - 11h', from: 9},
  {id: 86, t: '10h - 12h', from: 10}, {id: 87, t: '11h - 13h', from: 11}, {id: 88, t: '12h - 14h', from: 12},
  {id: 89, t: '13h - 15h', from: 13}, {id: 90, t: '14h - 16h', from: 14}, {id: 91, t: '15h - 17h', from: 15},
  {id: 92, t: '16h - 18h', from: 16}, {id: 93, t: '17h - 19h', from: 17}, {id: 94, t: '18h - 20h', from: 18},
  {id: 95, t: '19h - 21h', from: 19}, {id: 96, t: '20h - 22h', from: 20}
];

export function cakesGoc() {
  return [
    {k: 'CANDLE', img: CDN + '2-2606/2026/6/30/139b1df386ce67703afce4788cf08cdef7a420be.png',
      desc: 'Nền 70% Callebaut Dark Chocolate Crunch giòn đậm vị, Extra Brute Cocoa Biscuit Sponge đắng sâu. Pistachio Chantilly Cream và Pistachio Praliné bùi béo tạo lớp tương phản. Mocha Ganache Montée cà phê chocolate phủ mượt trên cùng. Thổi bay đi rồi nếm.',
      layers: [['70% Callebaut Dark Chocolate Crunch', 'Lớp sô cô la đen 70% giòn'], ['Extra Brute Cocoa Biscuit Sponge', 'Cốt bánh bông lan ca cao đắng sâu'],
        ['Pistachio Chantilly Cream', 'Kem Chantilly hạt dẻ cười'], ['Pistachio Praliné', 'Praliné hạt dẻ cười'], ['Mocha Ganache Montée', 'Ganache đánh bông vị cà phê sô cô la']],
      sizes: [{cm: 12, p: 650000, id: 'BAWC00139'}, {cm: 16, p: 880000, id: 'BAWC00140'}, {cm: 18, p: 1100000, id: 'BAWC00141'}]},
    {k: 'Phi Tử Tiếu', img: CDN + '2-2606/2026/6/15/91be1cf434f8adadd8782baab5422eee03463a84.png',
      desc: 'Phi Tử Tiếu, nụ cười Dương Quý Phi, cũng là giống vải thiều quý nhất. Almond Ladyfinger và Castella Sponge ẩm mềm, Butter Streusel giòn bùi. Earl Grey Chantilly thơm bergamot, Raspberry Lychee Confit và Pu Nhi Plum Compote chua ngọt.',
      layers: [['Almond Ladyfinger', 'Vòng bánh sâm-panh hạnh nhân'], ['Castella Sponge', 'Cốt bánh bông lan Castella'], ['Pure Butter Streusel', 'Lớp vụn bơ giòn'],
        ['Earl Grey Chantilly', 'Kem Chantilly vị trà Bá tước'], ['Raspberry & Lychee Confit', 'Vải hầm phúc bồn tử'], ['Pu Nhi Plum Compote', 'Mận hậu Pu Nhi nấu chậm'], ['Fresh Cherry', 'Cherry tươi theo mùa']],
      sizes: [{cm: 12, p: 660000, id: 'BAWC00135'}, {cm: 16, p: 880000, id: 'BAWC00136'}, {cm: 18, p: 1060000, id: 'BAWC00137'}, {cm: 20, p: 1300000, id: 'BAWC00138'}]},
    {k: 'Roman de la Rose', img: ROSE, seasonal: 'Bánh theo mùa',
      desc: 'Sô cô la đen nguyên chất gặp cherry dại và phúc bồn tử. Bánh đọc như một bài thơ tình thời Trung cổ.',
      layers: [['80% Dark Chocolate Biscuit', 'Bánh giòn sô cô la đen nguyên chất 80%'], ['Wild Cherry Compoté', 'Mứt quả cherry dại nấu chậm'],
        ['Raspberry Ganache Monteé', 'Kem mềm vị phúc bồn tử'], ['36% Milk Chocolate Cremeux', 'Kem mềm vị sô cô la sữa 36% cacao']],
      sizes: [{cm: 12, p: 660000, id: 'BAWC00066', serve: '2-4 người'}, {cm: 16, p: 880000, id: 'BAWC00067', serve: '6-8 người'}, {cm: 18, p: 1060000, id: 'BAWC00068', serve: '8-10 người'}]},
    {k: 'Kankin', img: CDN + '2-2604/2026/4/16/17b4c63d0601ba527e237131c0860ad0f167cb8b.jpg',
      desc: 'Avocado Mousse béo mịn bao trọn thân bánh hình dạng Saint-Honoré, nền Vanilla Sponge ẩm mềm. Pistachio Kataifi Crunch giòn sợi và 70% Dark Chocolate Crunch tạo lớp giòn tương phản. Avocado Chantilly mát nhẹ, điểm Craquelin Choux vỏ giòn rụm trên cùng.',
      layers: [['Avocado Mousse', 'Mousse bơ'], ['Vanilla Sponge', 'Cốt bánh bông lan vani'], ['Pistachio Kataifi Crunch', 'Sợi Kataifi hạt dẻ cười giòn'],
        ['70% Dark Chocolate Crunch', 'Lớp sô cô la đen 70% giòn'], ['Avocado Chantilly', 'Kem Chantilly bơ'], ['Craquelin Choux', 'Bánh su vỏ giòn']],
      sizes: [{cm: 12, p: 680000, id: 'BAWC00122'}, {cm: 16, p: 910000, id: 'BAWC00123'}, {cm: 18, p: 1090000, id: 'BAWC00124'}]},
    {k: 'BOHOL Cheesecake', img: CDN + '2-2604/2026/4/8/85760695886bee709e8e23064b23c69891918140.jpg',
      sizes: [{cm: 12, p: 600000, id: 'BAWC00125'}, {cm: 16, p: 750000, id: 'BAWC00126'}, {cm: 18, p: 1060000, id: 'BAWC00120'}]},
    {k: 'MEKONG Cheesecake', img: CDN + '2-2604/2026/4/14/9a782d9a301b7f2be3bfd2891f699943f786ffdf.png',
      sizes: [{cm: 12, p: 600000, id: 'BAWC00117'}, {cm: 16, p: 750000, id: 'BAWC00118'}, {cm: 18, p: 1060000, id: 'BAWC00119'}]},
    {k: 'VERGER Cheesecake', img: CDN + '2-2605/2026/5/8/23464664f9a9f707557968343d22124a6f43a076.jpg',
      sizes: [{cm: 12, p: 600000, id: 'BAWC00127'}, {cm: 16, p: 750000, id: 'BAWC00128'}, {cm: 18, p: 1060000, id: 'BAWC00129'}]},
    {k: 'Meraki', img: CDN + '2-2604/2026/4/29/ef3303b65f4a7a68064cf6590eb223ad51a93be6.png',
      sizes: [{cm: 16, p: 740000, id: 'BAWC00131'}, {cm: 18, p: 1060000, id: 'BAWC00132'}]}
  ];
}

/* Phụ kiện có sẵn trong hộp bánh (chỉ để hiện). Tên đi qua t() lúc vẽ.
   v597 (Minh Vũ báo): khách tưởng phải mua thêm hộp, túi. Hộp và túi lấy đúng
   ảnh của dòng mua thêm, một nguồn ảnh. Nĩa, dĩa chuyển xuống ô ghi số. */
export const ACC = [
  {k: 'pk_hop_banh', n: 'Hộp bánh', ks: 'pk_hop_banh_mo', sub: 'hộp giấy Vagabond, vừa size bánh', i: ANH_PHU_KIEN.BAPK00016},
  {k: 'pk_tui_vai', n: 'Túi vải đen The Vagabond', ks: 'pk_tui_vai_mo', sub: 'xách đi tiện, dùng lại được', i: ANH_PHU_KIEN.BAPK00015},
  {k: 'phu_kien_262b4eaaa', n: 'Dao gỗ cắt bánh', ks: '', sub: '', i: ANH_DUNG_CU[2]},
  {k: 'phu_kien_e0fe21772', n: 'Nến xoắn', ks: 'pk_nen_xoan_mo', sub: 'vỉ 6 cây', i: ANH_DUNG_CU[0]},
  {k: 'phu_kien_8034a0777', n: 'Cờ cắm in lời chúc', ks: 'pk_co_cam_mo', sub: 'in đúng lời chúc quý khách ghi ở mục 02', i: ANH_DUNG_CU[1]}
];

/* Hướng dẫn chọn size (poster Serving & Cutting Guide của bếp). Chữ sửa trong Editor. */
export const HUONG_SIZE = [
  {cm: 12, lat: 4, mieng: '4', nguoi: '2 - 4'},
  {cm: 16, lat: 8, mieng: '8', nguoi: '6 - 8'},
  {cm: 18, lat: 12, mieng: '12', nguoi: '8 - 10'},
  {cm: 20, lat: 16, mieng: '14 - 16', nguoi: '10 - 12'}
];

/* Nến số BAPK00003..12 và phụ kiện mua thêm (nhóm BAPK Pancake). */
export const NUMS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map(n => ({n, id: 'BAPK000' + String(3 + n).padStart(2, '0'), p: 17000, img: ANH_NEN_SO[n]}));
export const ADDONS = [
  {k: 'phu_kien_9908ba265', n: 'Nến xoắn (vỉ 6 cây)', id: 'BAPK00001', p: 11000, du_phong: true},
  {k: 'phu_kien_91d4d0b6f', n: 'Thiệp chúc mừng sinh nhật', id: 'BAPK00002', p: 17000},
  {k: 'phu_kien_f5af63739', n: 'Nón sinh nhật', id: 'BAPK00024', p: 20000},
  {k: 'phu_kien_55065e4f5', n: 'Sash sinh nhật', id: 'BAPK00025', p: 40000},
  {k: 'phu_kien_9ed7b3e1a', n: 'Hộp bánh kem', id: 'BAPK00016', p: 22000, du_phong: true},
  {k: 'phu_kien_4decf2ff4', n: 'Túi vải đen The Vagabond', id: 'BAPK00015', p: 17000, du_phong: true}
].map(a => ({...a, img: ANH_PHU_KIEN[a.id]}));

export const DAYS = ['Chủ nhật', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7'];

export const PICKUPS_GOC = [
  {id: 'bep-tan-son-hoa', n: 'Bếp Tân Sơn Hoà', a: '307/1 Nguyễn Văn Trỗi, P. Tân Sơn Hoà'},
  {id: 'cua-hang-sai-gon', n: 'Cửa hàng Sài Gòn', a: '9 Trần Cao Vân, P. Sài Gòn'}
];

export const PAYS = [
  {k: 'bank', kn: 'dat_banh_983bba817', n: 'Chuyển khoản', kd: 'dat_banh_d2684b2c6', d: 'Hiện mã VietQR, quét là xong, nội dung đã điền sẵn mã đơn'},
  {k: 'card', kn: 'dat_banh_ca5ee988f', n: 'Thẻ tín dụng', kd: 'dat_banh_8483dcf77', d: 'Nhận link thanh toán OnePay, nhập thẻ trên trang bảo mật của ngân hàng'}
];

/* Điểm lấy hàng máy chủ trả về (diem_lay) -> tên cho khách. */
export const TEN_DIEM = {
  'Bep Vagabond': ['dat_banh_bd6afbdb9', 'Bếp Nguyễn Văn Trỗi'],
  'Cua hang Sai Gon': ['dat_banh_5dda87f4a', 'Cửa hàng Trần Cao Vân']
};

/* Lý do máy chủ trả về -> câu cho khách. */
export const LY_DO = {
  khong_con_diem_nhan: ['dat_banh_khong_con_diem_nhan', 'Hiện chưa nhận tự đến lấy. Quý khách chọn giao tận nơi.'],
  diem_nhan_khong_con: ['dat_banh_diem_nhan_khong_con', 'Điểm nhận bánh vừa thay đổi. Quý khách tải lại trang rồi chọn lại điểm nhận.'],
  chua_dien_khoa_pancake: ['dat_banh_dda0df2c0', 'Hệ thống của chúng tôi đang trục trặc.'],
  gio_hang_rong: ['dat_banh_d3470ca1b', 'Giỏ hàng trống hoặc món đã hết mã.'],
  thieu_ten_hoac_so_dien_thoai: ['dat_banh_3261b803a', 'Thiếu tên hoặc số điện thoại.'],
  thieu_dia_chi_giao: ['dat_banh_1c040d123', 'Thiếu địa chỉ giao.'],
  ngoai_vung_giao: ['dat_banh_f578cc0d6', 'Địa chỉ này ngoài vùng giao bánh kem của chúng tôi. Quý khách chọn tự lấy tại cửa hàng'],
  khong_tim_thay_ma_hang: ['dat_banh_35ec19a18', 'Một món trong giỏ không tra được mã bán hàng, chúng tôi sẽ kiểm tra lại ngay.'],
  chua_dien_toa_do_diem_lay: ['dat_banh_dda0df2c0', 'Hệ thống của chúng tôi đang trục trặc.'],
  pancake_tu_choi: ['dat_banh_3baaae33b', 'Hệ thống bán hàng của chúng tôi từ chối đơn này.'],
  pancake_loi: ['dat_banh_4d688887d', 'Không kết nối được với hệ thống bán hàng.'],
  du_lieu_khong_doc_duoc: ['dat_banh_dd0cf091b', 'Dữ liệu đơn bị lỗi.'],
  thieu_du_lieu: ['dat_banh_cdfac34b3', 'Dữ liệu đơn bị thiếu.'],
  can_tai_lai_trang: ['dat_banh_b608d6713', 'Trang đặt bánh vừa được cập nhật. Quý khách tải lại trang rồi gửi lại, giỏ hàng cần chọn lại.'],
  chua_dong_y_chinh_sach: ['dat_banh_ea9153cee', 'Quý khách chọn ô đồng ý ngay trên nút gửi.'],
  het_hang_mua_vu: ['dat_banh_b221cfead', 'Một món mùa vụ trong giỏ vừa hết phần. Quý khách bớt số lượng rồi gửi lại.']
};

/* Nhãn câu có số (v532), mặc định TRÙNG noi_dung_web.NHAN. */
export const NHAN_MAC_DINH = {
  cau_co_san: '{so} bánh có sẵn',
  cau_nhan_tu: 'nhận từ {khung}',
  cau_het_khung: 'hôm nay đã hết khung giờ nhận',
  cau_chuan_bi: 'Bếp cần khoảng {gio} tiếng để chuẩn bị và đóng gói, nên hôm nay nhận được từ khung {khung} trở đi.',
  cau_chuan_bi_het: 'Hôm nay đã hết khung giờ nhận. Quý khách vui lòng chọn ngày mai.'
};

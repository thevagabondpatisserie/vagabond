/* v692 (anh Việt 24/11/2026): ca kiểm các hàm THUẦN của đường sạch trang đặt bánh
   (web_vue/banh/duong-sach.js): bỏ "/banh#" trong mọi link, link cũ vẫn mở được.

   Chạy: node vagabond/khung/kiem_thu/hanh_vi/duong_sach_692.mjs */
import {laMienSach, chuanMan, manHienTai, diaChiMan, doiLinkCu, linkChiaSe, hrefMan} from '../../../public/web_vue/banh/duong-sach.js';

let dat = 0, hong = 0;
const loi = [];
function ca(ten, ham) {
  try { ham(); dat++; } catch (e) { hong++; loi.push(ten + '\n      ' + (e && e.message)); }
}
function la(ten, co, can) {
  const a = JSON.stringify(co), b = JSON.stringify(can);
  if (a !== b) throw new Error(ten + ': được ' + a + ', cần ' + b);
}

const CHINH = 'thevagabondpatisserie.com';

ca('tên miền khách dùng đường sạch, tên miền khác giữ #/', () => {
  for (const h of [CHINH, 'www.' + CHINH, 'order.' + CHINH, 'THEVAGABONDPATISSERIE.COM'])
    la(h, laMienSach(h), true);
  for (const h of ['app.' + CHINH, 'erpnext-qwy-acq.s.frappe.cloud', 'localhost', '', null])
    la(String(h), laMienSach(h), false);
});

ca('chuẩn hoá màn: #/, rỗng là trang chủ', () => {
  la('#/', chuanMan('#/'), '/');
  la('rỗng', chuanMan(''), '/');
  la('#/uu-dai', chuanMan('#/uu-dai'), '/uu-dai');
  la('tuyen-dung/VT-1', chuanMan('tuyen-dung/VT-1'), '/tuyen-dung/VT-1');
});

ca('màn hiện tại: đường sạch đọc pathname, /banh cũ là trang chủ; bản cũ đọc hash', () => {
  la('/', manHienTai(true, '/', ''), '/');
  la('/banh', manHienTai(true, '/banh', ''), '/');
  la('/banh/', manHienTai(true, '/banh/', ''), '/');
  la('/tuyen-dung/VT-1/', manHienTai(true, '/tuyen-dung/VT-1/', ''), '/tuyen-dung/VT-1');
  la('/banh/<bánh> là trang một bánh', manHienTai(true, '/banh/bo-mon', ''), '/banh/bo-mon');
  la('bản cũ', manHienTai(false, '/banh', '#/dat-truoc'), '/dat-truoc');
  la('bản cũ trang chủ', manHienTai(false, '/banh', ''), '/');
});

ca('địa chỉ màn: không còn /banh# trên tên miền khách, giữ chuỗi hỏi', () => {
  la('tuyển dụng', diaChiMan(true, '#/tuyen-dung', '/', ''), '/tuyen-dung');
  la('trang chủ', diaChiMan(true, '#/', '/uu-dai', ''), '/');
  la('giữ ?ban', diaChiMan(true, '#/in-store', '/', '?diem=TCV&ban=5&k=abc'), '/in-store?diem=TCV&ban=5&k=abc');
  for (const h of ['#/', '#/dat-truoc', '#/tuyen-dung/VT-1', '#/gio-hang'])
    la('không chứa banh# ' + h, diaChiMan(true, h, '/banh', '').includes('#'), false);
  la('bản cũ giữ #/', diaChiMan(false, '#/uu-dai', '/banh', '?x=1'), '/banh?x=1#/uu-dai');
  la('bản cũ trang chủ', diaChiMan(false, '#/', '/web_moi/banh', ''), '/web_moi/banh');
});

ca('link cũ đã gửi khách tự đổi sang đường sạch, giữ chuỗi hỏi', () => {
  la('/banh#/tuyen-dung', doiLinkCu(true, '/banh', '#/tuyen-dung', ''), '/tuyen-dung');
  la('/banh#/uu-dai/x', doiLinkCu(true, '/banh', '#/uu-dai/x', ''), '/uu-dai/x');
  la('QR bàn cũ', doiLinkCu(true, '/banh', '#/in-store', '?diem=NVHTN&ban=3&k=0123456789abcdef'),
    '/in-store?diem=NVHTN&ban=3&k=0123456789abcdef');
  la('/banh trơn', doiLinkCu(true, '/banh', '', '?utm_source=zalo'), '/?utm_source=zalo');
  la('/banh/ có gạch cuối', doiLinkCu(true, '/banh/', '', ''), '/');
  la('/banh#/ về trang chủ', doiLinkCu(true, '/banh', '#/', ''), '/');
  la('đã sạch thì không đổi', doiLinkCu(true, '/tuyen-dung', '', ''), '');
  la('trang chủ sạch thì không đổi', doiLinkCu(true, '/', '', ''), '');
  la('neo thường (#muc) không đổi', doiLinkCu(true, '/', '#muc', ''), '');
  la('trang một bánh không đổi', doiLinkCu(true, '/banh/bo-mon', '', ''), '');
  la('tên miền khác không đổi', doiLinkCu(false, '/banh', '#/tuyen-dung', ''), '');
});

ca('href thẻ <a>: tên miền khách là đường sạch, nơi khác giữ #/', () => {
  la('sạch', hrefMan(true, '#/tuyen-dung/VT-1'), '/tuyen-dung/VT-1');
  la('sạch trang chủ', hrefMan(true, '#/'), '/');
  la('cũ', hrefMan(false, '#/uu-dai'), '#/uu-dai');
});

ca('link chia sẻ đúng kiểu đường', () => {
  la('sạch', linkChiaSe(true, '#/uu-dai/km1', 'https://' + CHINH, '/', ''), 'https://' + CHINH + '/uu-dai/km1');
  la('cũ', linkChiaSe(false, '#/uu-dai/km1', 'https://x.s.frappe.cloud', '/banh', ''), 'https://x.s.frappe.cloud/banh#/uu-dai/km1');
});

console.log(dat + ' ca dat, ' + hong + ' ca hong');
for (const x of loi) console.log('  HONG ' + x);
process.exit(hong ? 1 : 0);

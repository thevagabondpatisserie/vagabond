/* Ca kiểm HÀNH VI v630: tab "Thiết kế riêng" trên web bản Vue (mẫu m1 anh Việt
   duyệt 02/11/2026).

   Chạy THẬT kho và thành phần của web_vue/banh/thiet-ke-rieng.js với Vue thật
   (bản ESM trong repo). Tác phẩm dựng bằng ĐÚNG khối mẫu máy chủ gieo
   (noi_dung_web.TKR_MAU qua chuan_tkr, python3 với Frappe giả), không chép
   tay. Mạng, đồng hồ, hẹn giờ là bản giả ghi vết. Mỗi ca bấm đúng chuỗi thao
   tác của khách, không gọi thêm hàm "cho chắc".

   Chạy: node vagabond/khung/kiem_thu/hanh_vi/thiet_ke_rieng_630.mjs */
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {ND} from '../../../public/web_vue/kho/chu.js';
import {MAU} from '../../../public/web_vue/banh/mau.js';
import {ThietKeRieng, TKR, datMoiTruong, moTacPham, veDanhSach, dsTacPham} from '../../../public/web_vue/banh/thiet-ke-rieng.js';

const GOC = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..', '..');
const MAY = JSON.parse(execFileSync('python3', ['-B', '-c', `
import json, sys
sys.path.insert(0, sys.argv[1])
from vagabond.khung.kiem_thu import nen
nen.gia_lap()
from vagabond import noi_dung_web as nw
print(json.dumps(nw.chuan_tkr(nw.TKR_MAU), ensure_ascii=False))
`, GOC]).toString());

let dat = 0, hong = 0;
const loi = [];
async function ca(ten, ham) {
  try { await ham(); dat++; } catch (e) { hong++; loi.push(ten + '\n      ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n      ') : e)); }
}
function la(ten, co, can) { const a = JSON.stringify(co), b = JSON.stringify(can); if (a !== b) throw new Error(ten + ': được ' + a + ', cần ' + b); }
function dung(ten, x) { if (!x) throw new Error(ten); }

/* Dựng cây như Vue: gặp thành phần thì gọi render(). */
function cay(v) {
  if (v == null || v === false) return null;
  if (Array.isArray(v)) return v.map(cay).filter(Boolean);
  if (typeof v !== 'object') return String(v);
  if (typeof v.type === 'object' && v.type.render) return cay(v.type.render.call(Object.assign({}, v.props || {})));
  const con = typeof v.children === 'string' ? [v.children] : cay(v.children || []);
  return {the: typeof v.type === 'string' ? v.type : '', props: v.props || {}, con};
}
const chu = n => (n == null ? '' : typeof n === 'string' ? n : Array.isArray(n) ? n.map(chu).join('') : chu(n.con));
function tim(n, dk, ra = []) {
  if (!n || typeof n === 'string') return ra;
  if (Array.isArray(n)) { n.forEach(x => tim(x, dk, ra)); return ra; }
  if (dk(n)) ra.push(n);
  tim(n.con, dk, ra);
  return ra;
}
const coThuocTinh = (k, v) => n => n.props && Object.prototype.hasOwnProperty.call(n.props, k) && (v === undefined || n.props[k] === v);
const mot = (goc, dk, ten) => { const ds = tim(goc, dk); if (ds.length !== 1) throw new Error('cần đúng một ' + ten + ', thấy ' + ds.length); return ds[0]; };
const ve = () => cay(ThietKeRieng.render.call({}));

/* Môi trường giả. */
let VET = [], HEN = [], TRA = {};
datMoiTruong({
  homNay: () => '2026-11-02',
  uuid: () => '123e4567-e89b-42d3-a456-426614174000',
  hen: (f, ms) => { HEN.push({f, ms}); return HEN.length; },
  huyHen: id => { if (HEN[id - 1]) HEN[id - 1].huy = true; },
  ghi: async (phuong, than) => { VET.push([phuong, JSON.parse(JSON.stringify(than))]); const f = TRA[phuong]; if (typeof f === 'function') return f(than); return f; },
  taiTep: async (phuong, tep) => { VET.push([phuong, tep.name]); if (tep.hong) throw new Error('Không đọc được ảnh. Chọn ảnh JPG, PNG hoặc WebP.'); return {ok: 1, ma_anh: 'a'.repeat(24)}; }
});
function moi() {
  VET = []; HEN = []; TRA = {};
  ND.khoi = [JSON.parse(JSON.stringify(MAY))]; ND.daTai = true; ND.loiTai = false; ND.xemThu = false;
  ND.diem_nhan = [{id: 'tcv', n: 'The Vagabond District 1', a: '9 Trần Cao Vân'}, {id: 'bep', n: 'Bếp Tân Bình', a: '307/1 Nguyễn Văn Trỗi'}];
  TKR.id = ''; TKR.kc = ''; veDanhSach();
}
const KQ = {ok: 1, ma: 'TKR26110001', khoa: 'b'.repeat(24), tong: 7560000, coc: 3780000, con_lai: 3780000, ngay: '2026-11-14',
  qr: {ngan_hang: 'MB', stk: 'VQRQ00033k5p6', ten_tk: 'PATISSERIE VAGABOND', so_tien: 3780000, noi_dung: 'TKR26110001', anh: 'data:image/svg+xml;base64,AA'}};
function dienDon() {
  const c = ve();
  mot(c, coThuocTinh('data-tkr-ngay'), 'ô ngày').props.onInput({target: {value: '2026-11-14'}});
  tim(ve(), n => n.props.name === 'tkr_ten')[0].props.onInput({target: {value: 'Nguyễn An'}});
  tim(ve(), n => n.props.name === 'tkr_sdt')[0].props.onInput({target: {value: '0909 123 456'}});
  mot(ve(), coThuocTinh('data-diem', 'tcv'), 'chip nơi nhận').props.onClick();
}
const cho = () => new Promise(r => setTimeout(r, 0));

await ca('nội dung web chưa tải xong: hiện "Đang tải", không báo "chưa có tác phẩm"', async () => {
  moi(); ND.daTai = false;
  const c = ve();
  dung('đang tải', chu(c).includes('Đang tải các tác phẩm'));
  dung('không báo rỗng', !chu(c).includes('Chưa có tác phẩm'));
});

await ca('danh sách: thẻ Croquembouche ghi giá từ, số size, số ngày đặt trước; tab ẩn khi không có tác phẩm', async () => {
  moi();
  const c = ve(), the = mot(c, coThuocTinh('data-tkr', 'tkr-croquembouche'), 'thẻ');
  const s = chu(the);
  dung('tên', s.includes('Croquembouche'));
  dung('giá từ: ' + s, s.includes('Từ 5.940.000 đ · 3 size'));
  dung('ngày', s.includes('Đặt trước 7 ngày'));
  dung('ảnh repo', tim(the, n => n.the === 'img')[0].props.src === '/assets/vagabond/web_order/croquembouche.jpg');
  dung('tab có điều kiện', MAU.includes(`data-tab="thiet_ke_rieng" :hidden="!coTkr"`));
  ND.khoi = [Object.assign({}, MAY, {hien: false})];
  la('tác phẩm ẩn thì không có trong danh sách', dsTacPham().length, 0);
});

await ca('trang tác phẩm: chọn sẵn size M và Hoa lan trắng (đã gồm), ba size kèm giá, bánh gồm gì, đặt trước 7 ngày', async () => {
  moi(); moTacPham('tkr-croquembouche');
  const c = ve();
  la('size đang chọn', tim(c, n => n.props['aria-checked'] === 'true').map(n => n.props['data-size']), ['M']);
  la('giá size', tim(c, coThuocTinh('data-size')).map(n => chu(n)), ['S35-40 cm, 110-120 bánh5.940.000 đ', 'M45-55 cm, 130-160 bánh7.560.000 đ', 'L55-65 cm, 170-190 bánh10.800.000 đ']);
  dung('bánh gồm gì', chu(c).includes('Đế nougatine caramel'));
  dung('thời gian', chu(c).includes('Đặt trước ít nhất 7 ngày'));
  la('trang trí mặc định', TKR.tt, ['Hoa lan trắng']);
});

await ca('đặt cọc: ngày nhỏ nhất là hôm nay + 7, tóm tắt cọc 50% và phần trả khi nhận', async () => {
  moi(); moTacPham('tkr-croquembouche');
  mot(ve(), coThuocTinh('data-size', 'L'), 'size L').props.onClick();
  mot(ve(), coThuocTinh('data-tkr-dat'), 'nút đặt').props.onClick();
  const c = ve();
  la('min ngày', mot(c, coThuocTinh('data-tkr-ngay'), 'ô ngày').props.min, '2026-11-09');
  dung('câu ngày sớm', chu(c).includes('Ngày sớm nhất còn nhận: 09/11/2026'));
  const tong = chu(mot(c, coThuocTinh('data-tkr-tong'), 'tóm tắt'));
  dung('tóm tắt: ' + tong, tong.includes('10.800.000 đ') && tong.includes('Đặt cọc 50% hôm nay5.400.000 đ') && tong.includes('Trả khi nhận bánh5.400.000 đ'));
});

await ca('trang trí: bấm Không hoa thay Hoa lan trắng (cùng nhóm), Thêm bục trắng bật thêm, bấm lại thì tắt', async () => {
  moi(); moTacPham('tkr-croquembouche');
  mot(ve(), coThuocTinh('data-tkr-dat'), 'nút đặt').props.onClick();
  mot(ve(), coThuocTinh('data-tt', 'Không hoa'), 'chip').props.onClick();
  la('cùng nhóm thay', TKR.tt, ['Không hoa']);
  mot(ve(), coThuocTinh('data-tt', 'Thêm bục trắng'), 'chip').props.onClick();
  la('khác nhóm thêm', TKR.tt, ['Không hoa', 'Thêm bục trắng']);
  la('chip sáng', tim(ve(), n => n.props['aria-pressed'] === 'true' && n.props['data-tt']).map(n => n.props['data-tt']), ['Không hoa', 'Thêm bục trắng']);
  mot(ve(), coThuocTinh('data-tt', 'Thêm bục trắng'), 'chip').props.onClick();
  la('bấm lại tắt', TKR.tt, ['Không hoa']);
});

await ca('gửi thiếu ngày hoặc ngày quá sớm: báo ngay, KHÔNG gọi máy chủ', async () => {
  moi(); moTacPham('tkr-croquembouche');
  mot(ve(), coThuocTinh('data-tkr-dat'), 'nút đặt').props.onClick();
  await mot(ve(), coThuocTinh('data-tkr-gui'), 'nút gửi').props.onClick();
  dung('báo thiếu ngày', chu(mot(ve(), coThuocTinh('data-tkr-loi'), 'lỗi')).includes('Chọn ngày cần bánh'));
  mot(ve(), coThuocTinh('data-tkr-ngay'), 'ô ngày').props.onInput({target: {value: '2026-11-05'}});
  await mot(ve(), coThuocTinh('data-tkr-gui'), 'nút gửi').props.onClick();
  dung('báo ngày sớm', chu(mot(ve(), coThuocTinh('data-tkr-loi'), 'lỗi')).includes('09/11/2026'));
  la('không gọi mạng', VET.length, 0);
});

await ca('gửi đủ: KHÔNG gửi giá lên máy chủ, màn QR hiện số máy chủ trả về (kể cả khi khác số tạm tính)', async () => {
  moi(); moTacPham('tkr-croquembouche');
  mot(ve(), coThuocTinh('data-tkr-dat'), 'nút đặt').props.onClick();
  dienDon();
  TRA['vagabond.thiet_ke_rieng.dat'] = () => Object.assign({}, KQ, {tong: 8000000, coc: 4000000, con_lai: 4000000, qr: Object.assign({}, KQ.qr, {so_tien: 4000000})});
  await mot(ve(), coThuocTinh('data-tkr-gui'), 'nút gửi').props.onClick();
  la('một lần gửi', VET.map(v => v[0]), ['vagabond.thiet_ke_rieng.dat']);
  const du = VET[0][1].du_lieu;
  la('các ô gửi', Object.keys(du).sort(), ['diem_nhan', 'ghi_chu', 'gio', 'kich_co', 'ma_anh', 'ngay', 'sdt', 'tac_pham', 'ten', 'trang_tri']);
  la('giá trị', [du.tac_pham, du.kich_co, du.trang_tri, du.ngay, du.diem_nhan], ['tkr-croquembouche', 'M', ['Hoa lan trắng'], '2026-11-14', 'tcv']);
  la('mã lần gửi', VET[0][1].ma_lan_gui, '123e4567-e89b-42d3-a456-426614174000');
  const c = ve();
  la('sang QR', mot(c, coThuocTinh('data-tkr-buoc'), 'bước').props['data-tkr-buoc'], 'qr');
  la('tiền QR là số máy chủ', chu(mot(c, coThuocTinh('data-tkr-qr-tien'), 'tiền')), '4.000.000 đ');
  la('nội dung chuyển khoản', chu(mot(c, coThuocTinh('data-tkr-qr-nd'), 'nội dung')), 'TKR26110001');
  dung('ảnh QR', tim(c, n => n.the === 'img' && String(n.props.src).startsWith('data:image/svg')).length === 1);
  dung('đang chờ cọc', chu(c).includes('Đang chờ tiền cọc về'));
  la('đã hẹn hỏi trạng thái', HEN.filter(x => !x.huy).length, 1);
});

await ca('hỏi trạng thái: gửi đúng mã và khoá, tiền về thì báo Đã nhận cọc, ngừng hỏi; chưa về thì hẹn hỏi tiếp', async () => {
  moi(); moTacPham('tkr-croquembouche');
  mot(ve(), coThuocTinh('data-tkr-dat'), 'nút đặt').props.onClick();
  dienDon();
  TRA['vagabond.thiet_ke_rieng.dat'] = KQ;
  await mot(ve(), coThuocTinh('data-tkr-gui'), 'nút gửi').props.onClick();
  TRA['vagabond.thiet_ke_rieng.trang_thai_don'] = {trang_thai: 'cho_coc', nhan: 'Chờ cọc'};
  await HEN[0].f();
  la('hỏi đúng đơn', VET[1], ['vagabond.thiet_ke_rieng.trang_thai_don', {ma: 'TKR26110001', khoa: 'b'.repeat(24)}]);
  la('chưa về thì hẹn tiếp', HEN.length, 2);
  TRA['vagabond.thiet_ke_rieng.trang_thai_don'] = {trang_thai: 'da_coc', nhan: 'Đã cọc'};
  await HEN[1].f();
  const c = ve();
  dung('báo đã nhận cọc', chu(mot(c, coThuocTinh('data-tkr-tt'), 'trạng thái')).includes('Đã nhận cọc'));
  dung('ẩn QR sau khi nhận cọc', !tim(c, n => n.the === 'img').length);
  la('không hẹn thêm', HEN.length, 2);
});

await ca('mất mạng khi gửi: báo lỗi, bấm lại dùng CÙNG mã lần gửi (máy chủ trả đơn cũ, không tạo đơn thứ hai)', async () => {
  moi(); moTacPham('tkr-croquembouche');
  mot(ve(), coThuocTinh('data-tkr-dat'), 'nút đặt').props.onClick();
  dienDon();
  TRA['vagabond.thiet_ke_rieng.dat'] = () => { throw new Error('Failed to fetch'); };
  await mot(ve(), coThuocTinh('data-tkr-gui'), 'nút gửi').props.onClick();
  dung('báo lỗi', chu(mot(ve(), coThuocTinh('data-tkr-loi'), 'lỗi')).includes('Failed to fetch'));
  TRA['vagabond.thiet_ke_rieng.dat'] = KQ;
  await mot(ve(), coThuocTinh('data-tkr-gui'), 'nút gửi').props.onClick();
  la('cùng mã lần', VET.map(v => v[1].ma_lan_gui), ['123e4567-e89b-42d3-a456-426614174000', '123e4567-e89b-42d3-a456-426614174000']);
});

await ca('máy chủ từ chối (ví dụ ngày đã kín): câu của máy chủ hiện nguyên văn, vẫn ở bước đặt', async () => {
  moi(); moTacPham('tkr-croquembouche');
  mot(ve(), coThuocTinh('data-tkr-dat'), 'nút đặt').props.onClick();
  dienDon();
  TRA['vagabond.thiet_ke_rieng.dat'] = {exc_type: 'ValidationError', _server_messages: JSON.stringify([JSON.stringify({message: 'Tác phẩm này cần đặt trước ít nhất 7 ngày.'})])};
  await mot(ve(), coThuocTinh('data-tkr-gui'), 'nút gửi').props.onClick();
  la('câu máy chủ', chu(mot(ve(), coThuocTinh('data-tkr-loi'), 'lỗi')), 'Tác phẩm này cần đặt trước ít nhất 7 ngày.');
  la('vẫn ở bước đặt', TKR.buoc, 'dat');
});

await ca('ảnh tham khảo: tải lên trước, gửi đơn kèm mã ảnh; ảnh hỏng thì báo và không gửi mã', async () => {
  moi(); moTacPham('tkr-croquembouche');
  mot(ve(), coThuocTinh('data-tkr-dat'), 'nút đặt').props.onClick();
  const o = tim(ve(), n => n.the === 'input' && n.props.type === 'file')[0];
  await o.props.onChange({target: {files: [{name: 'hong.png', size: 10, hong: true}]}});
  la('ảnh hỏng không có mã', TKR.maAnh, '');
  dung('báo lỗi ảnh', TKR.loi.includes('Không đọc được ảnh'));
  await o.props.onChange({target: {files: [{name: 'y-tuong.jpg', size: 1000}]}});
  dung('đã gửi ảnh', chu(ve()).includes('Đã gửi ảnh tham khảo: y-tuong.jpg'));
  await o.props.onChange({target: {files: [{name: 'to.jpg', size: 9 * 1024 * 1024}]}});
  dung('ảnh trên 8 MB bị chặn trước khi gửi', TKR.loi.includes('8 MB') && VET.filter(v => v[1] === 'to.jpg').length === 0);
  dienDon();
  TRA['vagabond.thiet_ke_rieng.dat'] = KQ;
  await mot(ve(), coThuocTinh('data-tkr-gui'), 'nút gửi').props.onClick();
  la('mã ảnh đi kèm đơn', VET.filter(v => v[0] === 'vagabond.thiet_ke_rieng.dat')[0][1].du_lieu.ma_anh, 'a'.repeat(24));
});

await ca('Nhờ Sales tư vấn: số sai báo ngay; đúng thì gửi tên, số, tác phẩm, không tạo đơn', async () => {
  moi(); moTacPham('tkr-croquembouche');
  mot(ve(), coThuocTinh('data-tkr-tv'), 'nút tư vấn').props.onClick();
  tim(ve(), n => n.props.name === 'tv_ten')[0].props.onInput({target: {value: 'Lê Bình'}});
  tim(ve(), n => n.props.name === 'tv_sdt')[0].props.onInput({target: {value: '12345'}});
  await mot(ve(), coThuocTinh('data-tkr-tv-form'), 'form').props.onSubmit({preventDefault() {}});
  la('không gọi mạng', VET.length, 0);
  tim(ve(), n => n.props.name === 'tv_sdt')[0].props.onInput({target: {value: '0912 345 678'}});
  TRA['vagabond.thiet_ke_rieng.nho_tu_van'] = {ok: 1};
  await mot(ve(), coThuocTinh('data-tkr-tv-form'), 'form').props.onSubmit({preventDefault() {}});
  la('gửi tư vấn', VET, [['vagabond.thiet_ke_rieng.nho_tu_van', {du_lieu: {tac_pham: 'tkr-croquembouche', ten: 'Lê Bình', sdt: '0912 345 678'}}]]);
  dung('báo đã nhận', chu(ve()).includes('Sales sẽ gọi'));
});

await ca('khung xem thử của trình biên tập: không gửi đơn, không gửi tư vấn', async () => {
  moi(); moTacPham('tkr-croquembouche'); ND.xemThu = true;
  mot(ve(), coThuocTinh('data-tkr-dat'), 'nút đặt').props.onClick();
  dienDon();
  await mot(ve(), coThuocTinh('data-tkr-gui'), 'nút gửi').props.onClick();
  la('không gọi mạng', VET.length, 0);
  dung('báo xem thử', TKR.loi.includes('bản xem trước'));
});

await ca('link tác phẩm đã gỡ: báo không còn nhận đặt và có nút xem tác phẩm khác', async () => {
  moi(); moTacPham('khong-con');
  const c = ve();
  dung('câu', chu(c).includes('không còn nhận đặt'));
  dung('nút', chu(c).includes('Xem các tác phẩm khác'));
});

console.log('v630 Thiết kế riêng trên web Vue: ' + dat + ' ca dat, ' + hong + ' ca hong');
if (hong) { loi.forEach(x => console.log('  HONG  ' + x)); process.exit(1); }

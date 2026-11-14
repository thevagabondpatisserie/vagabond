/* Ca kiểm HÀNH VI v658: Vành nghiêng và Vé sự kiện của trang đặt bánh (anh Việt
   duyệt bản thử 14/11/2026, chọn A cho Vé sự kiện cùng ngày).

   Chạy THẬT các hàm thuần của web_vue/banh/vanh.js (thứ tự mục, hình học, luật
   vuốt) và web_vue/banh/ve-su-kien.js (sự kiện khách thấy, còn chỗ, số vé tối
   đa). Thao tác trên trình duyệt thật (vuốt, chạm, thanh gọn, sheet) kiểm ở
   cong_cu/kiem_web_vue_dom.cjs F46, F47. */
import {THU_TU_MUC, HINH, xepMuc, lech, viTri, kieuVuot, viTriKeo, dichBuong, dichToi, coGian, vongQuanh} from '../../../public/web_vue/banh/vanh.js';
import {ND} from '../../../public/web_vue/kho/chu.js';
import {LOAI_SU_KIEN, dsSuKien, trangThaiVe, veToiDa, oNgay, loaiCua} from '../../../public/web_vue/banh/ve-su-kien.js';

let dat = 0, hong = 0;
const dung = (ten, ok) => { if (!ok) throw new Error(ten); };
const la = (ten, a, b) => { const x = JSON.stringify(a), y = JSON.stringify(b); if (x !== y) throw new Error(ten + ': được ' + x + ' mong ' + y); };
async function ca(ten, fn) { try { await fn(); dat++; console.log('  DAT  ' + ten); } catch (e) { hong++; console.log('  HONG ' + ten + ' -> ' + e.message); } }

console.log('Bo ca kiem HANH VI v658 (Vành nghiêng, Vé sự kiện)');

await ca('thứ tự mục đúng bản anh duyệt; tab theo mùa chen cạnh nhóm mua bánh; chỉ các tab đang hiện', () => {
  /* Đúng thứ tự khai trong app.js (DOM cũ: Tại quầy, Ưu đãi, Tuyển dụng đứng trước). */
  const goc = ['season', 'store', 'uu_dai', 'tiec', 'tuyen_dung', 'today', 'order', 'thiet_ke_rieng'].map(tab => ({tab}));
  la('đủ mục', xepMuc(goc).map(m => m.tab), ['today', 'order', 'season', 'thiet_ke_rieng', 'tiec', 'store', 'uu_dai', 'tuyen_dung']);
  /* Thiết kế riêng và In season tắt (không có dữ liệu): vành chỉ còn các tab đang hiện, giữ thứ tự. */
  la('tab tắt biến mất', xepMuc(goc.filter(m => !['season', 'thiet_ke_rieng'].includes(m.tab))).map(m => m.tab), ['today', 'order', 'tiec', 'store', 'uu_dai', 'tuyen_dung']);
  la('mục lạ đứng cuối, giữ thứ tự', xepMuc([{tab: 'x'}, {tab: 'today'}, {tab: 'y'}]).map(m => m.tab), ['today', 'x', 'y']);
  la('danh sách thứ tự', THU_TU_MUC.slice(0, 5), ['today', 'order', 'season', 'thiet_ke_rieng', 'tiec']);
});

await ca('mục ngay trước mặt to và rõ nhất; nửa sau mờ dần, k dưới 0,2 ẩn hẳn và không cho chạm', () => {
  const t = viTri(0, 8);
  dung('trước mặt', t.truoc && !t.an && t.k > 0.99);
  la('to theo k', +t.co.toFixed(2), 1.05);
  const sau = viTri(4, 8);
  dung('sau lưng ẩn', sau.an && sau.k < HINH.AN_DUOI);
  /* Mọi mục hiện đều có k từ 0,2 trở lên; mục càng xa càng mờ hơn mục gần. */
  const ds = [0, 1, 2, 3].map(d => viTri(d, 8));
  dung('mờ dần', ds.every((v, i) => i === 0 || v.dTrong < ds[i - 1].dTrong));
  dung('giảm chuyển động thì không mờ', viTri(2, 8, 1, true).mo === 0);
  /* Chữ mọi mục cùng góc nghiêng: góc nằm ở HINH, không tính theo vị trí. */
  la('góc nghiêng', HINH.TILT, -11);
});

await ca('vuốt: ngang hơn dọc và quá 7 điểm mới là đổi mục; vuốt dọc để trình duyệt cuộn trang', () => {
  la('chưa đủ ngưỡng', kieuVuot(6, 1), null);
  la('ngang', kieuVuot(-8, 3), 'h');
  la('dọc trên vành', kieuVuot(5, -40), 'v');
  la('chéo nghiêng dọc', kieuVuot(30, 31), 'v');
});

await ca('buông tay: vuốt ngắn dưới 140 điểm luôn qua đúng một mục; kéo dài dừng ở mục gần nhất', () => {
  la('ngắn sang trái', dichBuong(2, viTriKeo(2, -30), -30), 3);
  la('ngắn sang phải', dichBuong(2, viTriKeo(2, 20), 20), 1);
  la('dài theo ngón', dichBuong(2, viTriKeo(2, -250), -250), Math.round(2 + 250 / HINH.PX_MOT_MUC));
  la('không kéo', dichBuong(2, 2, 0), 2);
});

await ca('quay tới mục đường ngắn nhất, vòng quanh đúng; mở màn quay thêm một vòng rồi dừng đúng mục', () => {
  la('đi lùi qua mép', vongQuanh(dichToi(7, 0, 8), 8), 7);
  la('ngắn nhất', dichToi(7, 0, 8), -1);
  la('mở màn thêm vòng', dichToi(2, 0, 8, 8), 10);
  la('lệch', lech(7, 0, 8), -1);
  la('màn rộng to có trần', [coGian(390), coGian(1440)], [1, 1.45]);
});

await ca('Vé sự kiện: chỉ sự kiện đang hiện và chưa diễn ra ra web, xếp ngày gần trước', () => {
  ND.xemThu = false;
  ND.khoi = [
    {id: 'a', loai: 'tiec', hien: true, tieu_de: 'Sau', bat_dau: '2026-12-20'},
    {id: 'b', loai: 'tiec', hien: true, tieu_de: 'Đã qua', bat_dau: '2026-11-01'},
    {id: 'c', loai: 'tiec', hien: false, tieu_de: 'Nháp', bat_dau: '2026-12-01'},
    {id: 'd', loai: 'tiec', hien: true, tieu_de: 'Gần', bat_dau: '2026-11-20'},
    {id: 'e', loai: 'uu_dai', hien: true, tieu_de: 'Không phải sự kiện'}];
  la('khách thấy', dsSuKien('2026-11-14').map(k => k.id), ['d', 'a']);
});

await ca('Vé sự kiện: còn chỗ đọc từ máy chủ, không âm; hết chỗ, hết hạn thì khoá nút; chọn vé không vượt số còn và 10', () => {
  ND.ve = {s1: 12, s2: 7};
  const k1 = {id: 's1', so_ve: '10', bat_dau: '2026-12-01'};
  la('bán lố từ trước vẫn không âm', trangThaiVe(k1, '2026-11-14').con, 0);
  dung('hết vé khoá', !trangThaiVe(k1, '2026-11-14').mo);
  const k2 = {id: 's2', so_ve: '10', bat_dau: '2026-12-01', han_ban: '2026-11-10'};
  dung('hết hạn khoá', !trangThaiVe(k2, '2026-11-14').mo);
  dung('còn hạn mở', trangThaiVe(k2, '2026-11-09').mo);
  la('tối đa', [veToiDa(3), veToiDa(null), veToiDa(25), veToiDa(0)], [3, 10, 10, 0]);
});

await ca('Vé sự kiện: ô ngày (tháng, ngày, thứ); loại trống là Tiệc; loại trùng máy chủ', () => {
  la('ô ngày', oNgay('2026-11-22'), {thang: 'Tháng 11', ngay: '22', thu: 'CN'});
  la('chưa có ngày', oNgay(''), null);
  la('loại trống', loaiCua({}), 'tiec');
  la('loại lạ', loaiCua({loai_su_kien: 'x'}), 'tiec');
  la('ba loại', LOAI_SU_KIEN, {tiec: 'Tiệc', ra_mat: 'Ra mắt món', dien_gia: 'Diễn giả'});
});

console.log(`${dat} ca dat, ${hong} ca hong, tong ${dat + hong} ca.`);
if (hong) process.exitCode = 1;

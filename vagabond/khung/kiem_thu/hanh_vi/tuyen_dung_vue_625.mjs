/* Ca kiểm HÀNH VI v625: mục Tuyển dụng trên web bản Vue, phương án A anh Việt
   duyệt 31/10/2026 (danh sách thẻ ảnh gọn, bấm mới ra trang chi tiết).

   Chạy THẬT các thành phần của web_vue/banh/noi-dung.js với Vue thật (bản ESM
   trong repo). Thẻ vị trí dựng bằng ĐÚNG phép máy chủ tuyen_dung.the_web trên
   hai vị trí thật ngày 31/10 (python3, Frappe giả), không chép tay. Một bộ dựng
   cây nhỏ gọi render() của từng thành phần như Vue rồi đọc chữ và thuộc tính.
   Phần bấm trên trình duyệt thật (đường dẫn #/tuyen-dung/<mã>, nút quay lại)
   kiểm ở cong_cu/kiem_tuyen_dung_dom.cjs.

   Chạy: node vagabond/khung/kiem_thu/hanh_vi/tuyen_dung_vue_625.mjs */
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {ND} from '../../../public/web_vue/kho/chu.js';
import {ChuyenMuc, TD, oTomTat, quyenLoi, ngayCon, moViTri} from '../../../public/web_vue/banh/noi-dung.js';

const GOC = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..', '..');
const MAY = JSON.parse(execFileSync('python3', ['-B', '-c', `
import json, sys
sys.path.insert(0, sys.argv[1])
from vagabond.khung.kiem_thu import nen
nen.gia_lap()
from vagabond import tuyen_dung as td, tuyen_dung_form as tf
ds = json.load(open(sys.argv[1] + '/cong_cu/tuyen_dung_mau.json'))
f = tf.mac_dinh()
print(json.dumps({'the': [td.the_web(v, '2026-10-31') for v in ds], 'chung': {'phuc_loi': f['phuc_loi'], 'gioi_thieu': f['gioi_thieu']}}, ensure_ascii=False))
`, GOC]).toString());

let dat = 0, hong = 0;
const loi = [];
async function ca(ten, ham) {
  try { await ham(); dat++; } catch (e) { hong++; loi.push(ten + '\n      ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n      ') : e)); }
}
function la(ten, co, can) { const a = JSON.stringify(co), b = JSON.stringify(can); if (a !== b) throw new Error(ten + ': được ' + a + ', cần ' + b); }
function dung(ten, x) { if (!x) throw new Error(ten); }

/* Dựng cây như Vue: gặp thành phần thì gọi render() với props và data() của nó. */
function dung_cay(v) {
  if (v == null || v === false) return null;
  if (Array.isArray(v)) return v.map(dung_cay).filter(Boolean);
  if (typeof v !== 'object') return String(v);
  if (typeof v.type === 'object' && v.type.render) {
    const ctx = Object.assign({}, v.props || {}, v.type.data ? v.type.data() : {});
    return dung_cay(v.type.render.call(ctx));
  }
  const con = typeof v.children === 'string' ? [v.children] : dung_cay(v.children || []);
  return {the: typeof v.type === 'string' ? v.type : '', props: v.props || {}, con};
}
function chu(n) { return n == null ? '' : typeof n === 'string' ? n : Array.isArray(n) ? n.map(chu).join('') : chu(n.con); }
function tim(n, dk, ra = []) {
  if (!n || typeof n === 'string') return ra;
  if (Array.isArray(n)) { n.forEach(x => tim(x, dk, ra)); return ra; }
  if (dk(n)) ra.push(n);
  tim(n.con, dk, ra);
  return ra;
}
const lop = c => n => String(n.props.class || '').split(' ').includes(c);
function ve() { return dung_cay(ChuyenMuc.render.call({loai: 'tuyen_dung'})); }
function napXong() {
  ND.khoi = MAY.the; ND.daTai = true; ND.tuyen_dung_chung = MAY.chung; ND.xemThu = false; TD.mo = '';
}

await ca('chưa tải xong nội dung: hiện "Đang tải", KHÔNG báo "chưa có vị trí" (đo 31/10 thấy báo rỗng trong lúc chờ)', async () => {
  ND.khoi = []; ND.daTai = false; TD.mo = '';
  const c = ve();
  dung('đang tải', chu(c).includes('Đang tải các vị trí đang tuyển'));
  dung('không báo rỗng', !chu(c).includes('chưa có vị trí'));
});

await ca('danh sách phương án A: thẻ ảnh gọn (bộ phận, Tuyển gấp, tên, nơi làm, lương gọn, mũi tên), không đổ cả mô tả ra', async () => {
  napXong();
  const c = ve(), the = tim(c, lop('td-the'));
  la('hai thẻ', the.map(t => t.props.href), ['#/tuyen-dung/VTT-0002', '#/tuyen-dung/VTT-0001']);
  const a = the[0];
  la('bộ phận', chu(tim(a, lop('td-bp'))), 'Sales');
  la('tuyển gấp', chu(tim(a, lop('td-gap'))), 'Tuyển gấp');
  la('không tuyển gấp thì không nhãn', tim(the[1], lop('td-gap')).length, 0);
  la('lương gọn', chu(tim(a, lop('td-luong'))), 'Từ 7,5 triệu/tháng');
  la('lương bếp', chu(tim(the[1], lop('td-luong'))), 'Từ 7 triệu · 32.000đ/giờ');
  la('nơi làm, hình thức', chu(tim(a, lop('td-meta'))), 'Xưởng sản xuất Tân Bình · Toàn thời gian');
  la('ảnh theo bộ phận', tim(a, n => n.the === 'img')[0].props.src, '/assets/vagabond/images/quay-sales.jpg');
  dung('không đổ mô tả dài ra danh sách', !chu(c).includes('Tư vấn, trả lời khách hàng') && !chu(c).includes('BHXH'));
  dung('chip lọc theo bộ phận vẫn có', chu(tim(c, lop('cm-chips'))).includes('Bếp Pastry'));
});

await ca('trang chi tiết: bốn ô tóm tắt, mục mô tả, Thu nhập đầy đủ, Chúng tôi cần, Quyền lợi cộng phúc lợi chung, nút Ứng tuyển ngay', async () => {
  napXong(); TD.mo = 'VTT-0002';
  const c = ve(), ct = tim(c, lop('td-chi-tiet'))[0];
  dung('mở chi tiết', !!ct && tim(c, lop('td-the')).length === 0);
  la('tên trên ảnh', chu(tim(ct, n => n.the === 'h1')), 'Nhân Viên Bán Hàng Online Qua Fanpage (Sales Online)');
  la('dòng trên tên', chu(tim(ct, lop('td-tren'))), 'Sales · Tuyển gấp');
  const o = tim(ct, n => String(n.props.class || '').startsWith('td-o')).map(chu);
  la('ô lương, nơi làm, hình thức', o.slice(0, 3), ['LươngTừ 7,5 triệu/tháng', 'Nơi làmXưởng sản xuất Tân Bình', 'Hình thứcToàn thời gian']);
  dung('ô hạn', /^Hạn nhận hồ sơ30\/11/.test(o[3]));
  const muc = tim(ct, lop('td-muc')).map(m => chu(tim(m, n => n.the === 'h3')));
  la('các mục', muc, ['Bạn sẽ làm', 'Thời gian làm việc', 'Thu nhập', 'Chúng tôi cần', 'Quyền lợi']);
  dung('thu nhập đầy đủ (thử việc 85%)', chu(tim(ct, lop('td-thu-nhap'))).includes('thử việc 2 tháng, nhận 85% lương'));
  const ql = tim(ct, lop('td-ql'))[0].con.map(chu);
  la('quyền lợi riêng rồi phúc lợi chung', ql, ['Có phụ cấp ăn trưa (30,000/ngày).', 'Tham gia đầy đủ BHXH, BHYT, BHTN khi ký hợp đồng.', 'Thưởng KPI hàng tháng.',
    'Ưu đãi 20% sản phẩm, dịch vụ của The Vagabond', 'Voucher sinh nhật, voucher nhân viên xuất sắc', 'Nghỉ phép, BHXH, BHTN đầy đủ theo Luật Lao động']);
  la('ba bước', tim(ct, lop('td-buoc'))[0].con.map(chu), ['1Gửi hồ sơ', '2Phỏng vấn', '3Làm thử có công']);
  la('nút ứng tuyển', tim(ct, lop('td-ung'))[0].props.href, '/ung-tuyen?vt=VTT-0002');
  la('nút quay lại', tim(ct, lop('td-lui'))[0].props.href, '#/tuyen-dung');
});

await ca('mô tả dài: mục Bạn sẽ làm hiện 4 việc và nút Xem thêm đúng số việc còn lại', async () => {
  napXong();
  ND.khoi = [Object.assign({}, MAY.the[0], {muc: [{tieu_de: 'Bạn sẽ làm', dong: ['a', 'b', 'c', 'd', 'e', 'f', 'g']}]})];
  TD.mo = 'VTT-0002';
  const ct = tim(ve(), lop('td-chi-tiet'))[0], m = tim(ct, lop('td-muc'))[0];
  la('4 việc', tim(m, n => n.the === 'li').length, 4);
  la('nút', chu(tim(m, lop('td-them'))), 'Xem thêm 3 việc ▾');
});

await ca('mở link vị trí đã ngừng nhận: báo, có nút xem vị trí khác', async () => {
  napXong(); TD.mo = 'VTT-0099';
  const c = ve();
  dung('báo', chu(c).includes('đã ngừng nhận hồ sơ'));
  la('nút', tim(c, n => n.props.href === '#/tuyen-dung').length, 1);
});

await ca('phép thuần: số ngày còn, ô hạn, ô trống, phúc lợi bỏ trùng', async () => {
  la('ngày còn', [ngayCon('2026-11-30', '2026-10-31'), ngayCon('2026-10-31', '2026-10-31'), ngayCon('', '2026-10-31')], [30, 0, null]);
  const o = oTomTat({ket_thuc: '2026-11-30'}, '2026-10-31');
  la('ô trống có chữ', o.map(x => x.chu), ['Thoả thuận khi phỏng vấn', 'The Vagabond Pâtisserie', 'Trao đổi khi phỏng vấn', '30/11 · còn 30 ngày']);
  la('không hạn', oTomTat({}, '2026-10-31')[3].chu, 'Đến khi đủ người');
  la('hôm nay hết hạn', oTomTat({ket_thuc: '2026-10-31'}, '2026-10-31')[3].chu, '31/10 · hôm nay');
  la('bỏ trùng không phân biệt hoa thường', quyenLoi({quyen_loi: ['Thưởng KPI']}, {phuc_loi: ['thưởng kpi', ' ', 'BHXH']}), ['Thưởng KPI', 'BHXH']);
});

await ca('bấm thẻ: đổi đường dẫn bằng pushState rồi phát popstate cho bộ định tuyến, cuộn về đầu', async () => {
  const vet = [];
  const win = {location: {pathname: '/banh', search: '?x=1'}, history: {pushState: (s, t, u) => vet.push(['push', s, u])},
    dispatchEvent: e => vet.push(['su_kien', e.type]), PopStateEvent: class { constructor(t) { this.type = t; } }, scrollTo: (x, y) => vet.push(['cuon', x, y])};
  moViTri('VTT-0002', win);
  moViTri('', win);
  la('vết', vet, [['push', {vgb: 1}, '/banh?x=1#/tuyen-dung/VTT-0002'], ['su_kien', 'popstate'], ['cuon', 0, 0],
    ['push', {vgb: 1}, '/banh?x=1#/tuyen-dung'], ['su_kien', 'popstate'], ['cuon', 0, 0]]);
});

console.log('Ca hanh vi web Vue Tuyen dung v625');
loi.forEach(l => console.log('  HONG  ' + l));
console.log(dat + ' ca dat, ' + hong + ' ca hong');
process.exit(hong ? 1 : 0);

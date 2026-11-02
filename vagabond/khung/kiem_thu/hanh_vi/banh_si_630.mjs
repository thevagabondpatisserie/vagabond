/* Ca kiểm HÀNH VI v630: trang Bánh sỉ (/banh-si) bản Vue (mẫu m2 anh Việt
   duyệt 02/11/2026).

   Chạy THẬT kho (web_vue/si/kho-si.js) và thành phần (web_vue/si/app.js) với
   Vue thật (bản ESM trong repo). Mạng, đồng hồ, hẹn giờ là bản giả ghi vết,
   trả ĐÚNG hình dạng của banh_si.toi / dat / qr_no. Mỗi ca bấm đúng chuỗi
   thao tác của khách, không gọi thêm hàm "cho chắc".

   Chạy: node vagabond/khung/kiem_thu/hanh_vi/banh_si_630.mjs */
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {ND} from '../../../public/web_vue/kho/chu.js';
import {SI, datMoiTruong, khoiDong, dsNgay, tamTinh} from '../../../public/web_vue/si/kho-si.js';
import {TrangSi} from '../../../public/web_vue/si/app.js';

const GOC = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..', '..');
let dat = 0, hong = 0;
const loi = [];
async function ca(ten, ham) {
  try { await ham(); dat++; } catch (e) { hong++; loi.push(ten + '\n      ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n      ') : e)); }
}
function la(ten, co, can) { const a = JSON.stringify(co), b = JSON.stringify(can); if (a !== b) throw new Error(ten + ': được ' + a + ', cần ' + b); }
function dung(ten, x) { if (!x) throw new Error(ten); }

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
const co = (k, v) => n => n.props && Object.prototype.hasOwnProperty.call(n.props, k) && (v === undefined || n.props[k] === v);
const mot = (goc, dk, ten) => { const ds = tim(goc, dk); if (ds.length !== 1) throw new Error('cần đúng một ' + ten + ', thấy ' + ds.length); return ds[0]; };
const ve = () => cay(TrangSi.render.call({}));
const cho = () => new Promise(r => setTimeout(r, 0));

let VET = [], HEN = [], TRA = {};
datMoiTruong({
  homNay: () => '2026-11-02',
  uuid: () => '123e4567-e89b-42d3-a456-426614174000',
  hen: (f, ms) => { HEN.push({f, ms}); return HEN.length; },
  huyHen: id => { if (HEN[id - 1]) HEN[id - 1].huy = true; },
  ghi: async (p, than) => { VET.push([p, JSON.parse(JSON.stringify(than))]); const f = TRA[p]; return typeof f === 'function' ? f(than) : f; },
  doc: async p => { VET.push([p, null]); const f = TRA[p]; return typeof f === 'function' ? f() : f; }
});

const TOI = () => ({ok: 1, ten: 'Café Lá Me', cuoi_ky: 1, ky_no: 15, hom_nay: '2026-11-02', ngay_som: '2026-11-05', so_ngay: 3,
  mon: [{ma: 'BANU00001', ten: 'Croissant bơ', gia: 28000, anh: '/files/cr.jpg', dvt: 'Cái', nhom: 'Bánh mì'},
    {ma: 'BANU00002', ten: 'Pain au chocolat', gia: 32000, anh: '', dvt: 'Cái', nhom: 'Bánh mì'}],
  sap_giao: [{ma: 'BSI26100007', ngay: '2026-11-03', so_cai: 50, nhan: 'Chờ giao', tong: 1500000, trang_thai: 'cho_giao'}],
  lich_su: [{ma: 'BSI26100003', ngay: '2026-10-31', so_cai: 74, nhan: 'Đã giao', tong: 2064960, trang_thai: 'da_giao'}],
  don_truoc: {ma: 'BSI26100003', ngay: '2026-10-31', dong: [{ma: 'BANU00001', sl: 30}], bo: 1},
  no: {tong: 6194880, han_gan: '2026-11-10', so_qua_han: 0, dong: [
    {hoa_don: 'HDB-1', ngay: '2026-10-26', tien: 2064960, han: '2026-11-10'}, {hoa_don: 'HDB-2', ngay: '2026-10-29', tien: 2064960, han: '2026-11-13'}]}});

async function moi(toi) {
  VET = []; HEN = [];
  ND.nhan = {}; ND.daTai = true; ND.xemThu = false;
  Object.assign(SI, {man: 'cho', otp: 1, toi: null, ngay: '', sl: {}, ghiChu: '', dangGui: false, loi: '', maLan: '', bao: '', kq: null,
    trangThai: '', lanHoi: 0, henHoi: null, qrNo: null, dangQr: false, loiQr: ''});
  SI.dk = {ten_quan: '', mst: '', sdt: '', loai_hinh: '', luong: '', ghi_chu: '', gui: false, xong: '', loi: '', maLan: ''};
  SI.dn = {mo: false, sdt: '', ma: '', buoc: 'sdt', gui: false, loi: '', song: 0};
  TRA = {'vagabond.banh_si.san_sang': {otp: 1, so_ngay: 3}, 'vagabond.banh_si.toi': toi || {ok: 0, ly_do: 'chua_dang_nhap'}};
  await khoiDong();
}

await ca('người ngoài: trang hợp tác KHÔNG hiện giá, có form đăng ký và nút đăng nhập sỉ', async () => {
  await moi();
  const c = ve();
  la('màn ngoài', SI.man, 'ngoai');
  dung('có form', tim(c, co('id', 'siDangKy')).length === 1);
  dung('không có số tiền nào', !/[0-9][0-9.]* ?đ\b/.test(chu(c)));
  dung('không có bảng món', tim(c, co('data-si-mon')).length === 0);
  mot(c, co('data-si-mo-dn'), 'nút đăng nhập');
});

await ca('đăng ký: thiếu loại hình bị chặn ở máy khách, đủ thì gửi đúng gói, gửi lại cùng mã lần gửi', async () => {
  await moi();
  const o = n => tim(ve(), x => x.props.name === n)[0];
  o('si_dk_ten_quan').props.onInput({target: {value: 'Café Lá Me'}});
  o('si_dk_sdt').props.onInput({target: {value: '0909 123 456'}});
  mot(ve(), co('data-si-luong', '50_200'), 'chip lượng').props.onClick();
  mot(ve(), co('id', 'siDangKy'), 'form').props.onSubmit({preventDefault() {}});
  await cho();
  dung('báo thiếu loại hình', chu(mot(ve(), co('data-si-loi-dk'), 'lỗi')).includes('loại hình'));
  la('chưa gọi máy chủ', VET.filter(v => v[0] === 'vagabond.banh_si.dang_ky').length, 0);
  mot(ve(), co('data-si-loai', 'cafe'), 'chip loại').props.onClick();
  TRA['vagabond.banh_si.dang_ky'] = {ok: 1, ma: 'AB12CD34'};
  mot(ve(), co('id', 'siDangKy'), 'form').props.onSubmit({preventDefault() {}});
  await cho(); await cho();
  const g = VET.filter(v => v[0] === 'vagabond.banh_si.dang_ky');
  la('gói gửi', g[0][1], {ma_lan_gui: '123e4567-e89b-42d3-a456-426614174000', du_lieu: {ten_quan: 'Café Lá Me', mst: '', sdt: '0909 123 456', loai_hinh: 'cafe', luong: '50_200', ghi_chu: ''}});
  dung('hiện đã nhận', chu(mot(ve(), co('id', 'siDangKyXong'), 'xong')).includes('Café Lá Me'));
});

await ca('đăng nhập: số chưa mở đặt sỉ thì báo đăng ký; đúng mã thì tải bảng giá riêng và sang màn đặt hàng', async () => {
  await moi();
  mot(ve(), co('data-si-mo-dn'), 'nút').props.onClick();
  tim(ve(), x => x.props.name === 'si_dn_sdt')[0].props.onInput({target: {value: '0909123456'}});
  TRA['vagabond.banh_si.gui_ma'] = {ok: 0, ly_do: 'chua_mo_si'};
  tim(ve(), co('data-si-gui-ma'))[0];
  tim(ve(), n => n.the === 'form' && tim(n, co('data-si-gui-ma')).length)[0].props.onSubmit({preventDefault() {}});
  await cho(); await cho();
  dung('báo chưa mở', chu(mot(ve(), co('data-si-loi-dn'), 'lỗi')).includes('chưa được mở đặt sỉ'));
  TRA['vagabond.banh_si.gui_ma'] = {ok: 1, song_giay: 300};
  tim(ve(), n => n.the === 'form' && tim(n, co('data-si-gui-ma')).length)[0].props.onSubmit({preventDefault() {}});
  await cho(); await cho();
  tim(ve(), x => x.props.name === 'si_dn_ma')[0].props.onInput({target: {value: '123456'}});
  TRA['vagabond.banh_si.xac_thuc'] = {ok: 1};
  TRA['vagabond.banh_si.toi'] = TOI();
  tim(ve(), n => n.the === 'form' && tim(n, co('data-si-xac-thuc')).length)[0].props.onSubmit({preventDefault() {}});
  for (let i = 0; i < 5; i++) await cho();
  la('màn đặt', SI.man, 'dat');
  la('hai món giá riêng', tim(ve(), co('data-si-mon')).map(n => n.props['data-si-mon']), ['BANU00001', 'BANU00002']);
  la('ngày chọn sẵn là ngày sớm nhất', SI.ngay, '2026-11-05');
});

await ca('ngày giao: sáu chip từ ngày sớm nhất (đặt + 3), ô ngày khác có min đúng', async () => {
  await moi(TOI());
  la('chip', tim(ve(), co('data-si-ngay')).map(n => n.props['data-si-ngay']), dsNgay('2026-11-05'));
  la('ngày đầu', dsNgay('2026-11-05')[0], '2026-11-05');
  la('min ô ngày', tim(ve(), x => x.props.name === 'si_ngay')[0].props.min, '2026-11-05');
  mot(ve(), co('data-si-ngay', '2026-11-07'), 'chip').props.onClick();
  la('đổi ngày', SI.ngay, '2026-11-07');
});

await ca('số lượng: cộng trừ, gõ tay kẹp 0..5000, tổng tạm tính cập nhật ngay', async () => {
  await moi(TOI());
  mot(ve(), co('data-si-cong', 'BANU00001'), 'cộng').props.onClick();
  mot(ve(), co('data-si-cong', 'BANU00001'), 'cộng').props.onClick();
  mot(ve(), co('data-si-sl', 'BANU00002'), 'ô').props.onInput({target: {value: '20'}});
  la('tạm tính', tamTinh(), {so_mon: 2, so_cai: 22, tong: 2 * 28000 + 20 * 32000});
  dung('màn hiện tổng', chu(mot(ve(), co('data-si-tam'), 'tổng')).includes('696.000'));
  mot(ve(), co('data-si-sl', 'BANU00002'), 'ô').props.onInput({target: {value: '99999'}});
  la('kẹp trần', SI.sl.BANU00002, 5000);
  mot(ve(), co('data-si-sl', 'BANU00002'), 'ô').props.onInput({target: {value: '-3'}});
  la('không âm', SI.sl.BANU00002, 3);
});

await ca('đặt lại như đơn trước: chép số lượng, báo món thôi bán, không gửi giá', async () => {
  await moi(TOI());
  mot(ve(), co('data-si-dat-lai'), 'nút đặt lại').props.onClick();
  la('số lượng', SI.sl, {BANU00001: 30});
  dung('báo thôi bán', SI.bao.includes('1 món thôi bán'));
});

await ca('gửi đơn công nợ: gói chỉ có mã và số lượng (không giá), kết quả đọc tổng và VAT từ máy chủ, không hỏi trạng thái', async () => {
  await moi(TOI());
  mot(ve(), co('data-si-sl', 'BANU00001'), 'ô').props.onInput({target: {value: '30'}});
  TRA['vagabond.banh_si.dat'] = {ok: 1, ma: 'BSI26110001', ngay: '2026-11-05', trang_thai: 'cho_giao', tra_truoc: 0, tong: 840000, chua_vat: 777778, vat: 62222,
    dong: [{ma: 'BANU00001', ten: 'Croissant bơ', sl: 30, tien: 840000}]};
  mot(ve(), co('data-si-gui'), 'nút gửi').props.onClick();
  await cho(); await cho();
  const g = VET.filter(v => v[0] === 'vagabond.banh_si.dat')[0][1];
  la('gói', g, {ma_lan_gui: '123e4567-e89b-42d3-a456-426614174000', du_lieu: {ngay: '2026-11-05', ghi_chu: '', dong: [{ma: 'BANU00001', sl: 30}]}});
  la('màn xong', SI.man, 'xong');
  dung('VAT máy chủ', chu(mot(ve(), co('data-si-vat'), 'vat')).includes('62.222'));
  la('không hẹn hỏi trạng thái', HEN.length, 0);
  dung('không QR', tim(ve(), n => n.the === 'img' && /QR/.test(n.props.alt || '')).length === 0);
});

await ca('gửi đơn trả trước: hiện QR mã đơn đúng số máy chủ, hỏi trạng thái mỗi 8 giây, tiền về thì đổi câu', async () => {
  const toi = TOI(); toi.cuoi_ky = 0; toi.no = null;
  await moi(toi);
  mot(ve(), co('data-si-sl', 'BANU00002'), 'ô').props.onInput({target: {value: '10'}});
  TRA['vagabond.banh_si.dat'] = {ok: 1, ma: 'BSI26110002', ngay: '2026-11-05', trang_thai: 'cho_tt', tra_truoc: 1, tong: 320000, chua_vat: 296296, vat: 23704,
    dong: [{ma: 'BANU00002', ten: 'Pain au chocolat', sl: 10, tien: 320000}],
    qr: {ngan_hang: 'MB', stk: '0931224334', ten_tk: 'PATISSERIE VAGABOND', so_tien: 320000, noi_dung: 'BSI26110002', anh: 'data:image/svg+xml;base64,AA'}};
  mot(ve(), co('data-si-gui'), 'nút gửi').props.onClick();
  await cho(); await cho();
  la('nội dung QR', chu(mot(ve(), co('data-si-qr-nd'), 'nd')), 'BSI26110002');
  dung('số tiền QR', chu(mot(ve(), co('data-si-qr-tien'), 'tiền')).includes('320.000'));
  la('hẹn 8 giây', HEN.map(x => x.ms), [8000]);
  TRA['vagabond.banh_si.trang_thai_don'] = {trang_thai: 'cho_giao', nhan: 'Chờ giao', con_lai: 0};
  await HEN[0].f();
  la('hỏi đúng mã', VET.filter(v => v[0] === 'vagabond.banh_si.trang_thai_don')[0][1], {ma: 'BSI26110002'});
  la('đổi trạng thái', mot(ve(), co('data-si-tt'), 'tt').props['data-si-tt'], 'cho_giao');
  la('không hẹn thêm', HEN.length, 1);
});

await ca('gửi lỗi mạng giữ mã lần gửi: bấm lại dùng CÙNG mã, máy chủ trả đơn cũ, không gửi trùng', async () => {
  await moi(TOI());
  mot(ve(), co('data-si-sl', 'BANU00001'), 'ô').props.onInput({target: {value: '5'}});
  let lan = 0;
  TRA['vagabond.banh_si.dat'] = () => { lan++; if (lan === 1) throw new Error('mất mạng'); return {ok: 1, ma: 'BSI26110003', trang_thai: 'cho_giao', dong: []}; };
  mot(ve(), co('data-si-gui'), 'nút').props.onClick(); await cho(); await cho();
  dung('báo lỗi', SI.loi.length > 0);
  mot(ve(), co('data-si-gui'), 'nút').props.onClick(); await cho(); await cho();
  const ma = VET.filter(v => v[0] === 'vagabond.banh_si.dat').map(v => v[1].ma_lan_gui);
  la('cùng mã lần gửi', ma, ['123e4567-e89b-42d3-a456-426614174000', '123e4567-e89b-42d3-a456-426614174000']);
});

await ca('chưa chọn món hoặc ngày trước ngày sớm nhất: chặn ở máy khách, không gọi máy chủ', async () => {
  await moi(TOI());
  mot(ve(), co('data-si-gui'), 'nút').props.onClick(); await cho();
  dung('báo chọn món', SI.loi.includes('ít nhất một món'));
  mot(ve(), co('data-si-sl', 'BANU00001'), 'ô').props.onInput({target: {value: '5'}});
  tim(ve(), x => x.props.name === 'si_ngay')[0].props.onInput({target: {value: '2026-11-04'}});
  mot(ve(), co('data-si-gui'), 'nút').props.onClick(); await cho();
  dung('báo ngày sớm nhất', SI.loi.includes('05/11'));
  la('không gọi dat', VET.filter(v => v[0] === 'vagabond.banh_si.dat').length, 0);
});

await ca('khách chưa có giá riêng nào: không có bảng món, câu chỉ gọi Sales', async () => {
  const toi = TOI(); toi.mon = [];
  await moi(toi);
  dung('câu rỗng', chu(mot(ve(), co('data-si-rong'), 'rỗng')).includes('chưa mở giá'));
  dung('không nút gửi', tim(ve(), co('data-si-gui')).length === 0);
});

await ca('tài khoản công nợ: tổng, hạn gần nhất; bấm Thanh toán qua QR thì hiện QR phiếu đòi nợ mã DNTT', async () => {
  await moi(TOI());
  mot(ve(), co('data-si-tab', 'tai_khoan'), 'tab').props.onClick();
  const c = ve();
  dung('tổng nợ', chu(mot(c, co('data-si-no'), 'nợ')).includes('6.194.880'));
  dung('hạn gần nhất', chu(mot(c, co('data-si-no'), 'nợ')).includes('10/11'));
  la('hoá đơn chưa trả', tim(c, co('data-si-hd')).map(n => n.props['data-si-hd']), ['HDB-1', 'HDB-2']);
  TRA['vagabond.banh_si.qr_no'] = {ok: 1, phieu: [{ma_phieu: 'DNTT-26-11-00003', con_thieu: 6194880, hoa_don: ['HDB-1', 'HDB-2', 'HDB-0'],
    qr: {so_tien: 6194880, noi_dung: 'DNTT-26-11-00003', anh: 'data:image/svg+xml;base64,BB', ngan_hang: 'MB', stk: '1', ten_tk: 'X'}}], no: TOI().no};
  mot(ve(), co('data-si-qr-no'), 'nút QR').props.onClick(); await cho(); await cho();
  la('QR phiếu đòi nợ', chu(mot(ve(), co('data-si-qr-nd'), 'nd')), 'DNTT-26-11-00003');
  la('gọi một lần, gói rỗng', VET.filter(v => v[0] === 'vagabond.banh_si.qr_no').map(v => v[1]), [{}]);
});

await ca('khách trả trước: tài khoản không có khối công nợ; đăng xuất về trang ngoài', async () => {
  const toi = TOI(); toi.cuoi_ky = 0; toi.no = null;
  await moi(toi);
  mot(ve(), co('data-si-tab', 'tai_khoan'), 'tab').props.onClick();
  dung('không khối nợ', tim(ve(), co('data-si-no')).length === 0);
  TRA['vagabond.banh_si.thoat'] = {ok: 1};
  mot(ve(), co('data-si-thoat'), 'thoát').props.onClick(); await cho();
  la('về ngoài', SI.man, 'ngoai');
  la('xoá phiên', SI.toi, null);
});

await ca('mọi khoá chữ của trang gọi khi vẽ có trong sổ nhãn, chữ mặc định trùng, không đại từ cũ, không markup', async () => {
  const so = JSON.parse(readFileSync(path.join(GOC, 'vagabond/public/web_order/chu-mac-dinh.json'), 'utf8'));
  const doc = new Set();
  ND.nhan = new Proxy({}, {get: (o, k) => { if (typeof k === 'string' && /^[a-z][a-z0-9_]*$/.test(k)) doc.add(k); return undefined; }});
  await moi(); ND.nhan = new Proxy({}, {get: (o, k) => { if (typeof k === 'string' && /^[a-z][a-z0-9_]*$/.test(k)) doc.add(k); return undefined; }});
  ve(); SI.dn.mo = true; ve(); SI.dk.xong = 'x'; ve();
  SI.toi = TOI(); SI.man = 'dat'; SI.ngay = '2026-11-05'; ve(); SI.man = 'tai_khoan'; ve();
  la('khoá thiếu', [...doc].filter(k => !so[k] && k !== 'dat_banh_913466c0d'), []);
  for (const f of ['si/app.js', 'si/kho-si.js']) {
    const nguon = readFileSync(path.join(GOC, 'vagabond/public/web_vue', f), 'utf8');
    for (const [, k, d] of nguon.matchAll(/\bt\(\s*'([a-z0-9_]+)'\s*,\s*'((?:[^'\\]|\\.)*)'/g)) la('mặc định ' + k, d, so[k] && so[k].mac_dinh);
  }
  for (const k of Object.keys(so).filter(k => k.startsWith('bsi_'))) {
    dung(k + ' không có đại từ cũ', !/(^|[^\p{L}])(tiệm|mình|anh chị|em)([^\p{L}]|$)/iu.test(so[k].mac_dinh));
    dung(k + ' không có markup', !/[<>]/.test(so[k].mac_dinh));
    dung(k + ' không dấu gạch dài', !/[–—]/.test(so[k].mac_dinh + so[k].ten));
  }
  ND.nhan = {};
});

for (const l of loi) console.log('  HONG  ' + l);
console.log('banh_si_630: ' + dat + ' ca dat, ' + hong + ' ca hong');
process.exit(hong ? 1 : 0);

/* v667 (anh Việt duyệt 17/11/2026): tab "Đặc biệt tuần này" của trang /banh.

   Chạy THẬT phép thuần dbt-thuan.js, kho trang đặt bánh (kho-banh.js) với Vue
   thật, đồng hồ cố định, mạng giả; và vẽ THẬT thành phần DacBietTuan bằng bộ
   dựng cây của Vue. Mỗi ca dựng đúng chuỗi bấm của khách. Luật phía máy chủ
   (chặn khi gửi đơn) kiểm ở thu_dac_biet_tuan_667.py, cùng bảng mẫu.

   Chạy: node vagabond/khung/kiem_thu/hanh_vi/dac_biet_tuan_667.mjs */
import {createRenderer, h, nextTick} from '../../../public/web_vue/lib/vue.esm-browser.prod.js';
import {taoKho} from '../../../public/web_vue/banh/kho-banh.js';
import {t0} from '../../../public/web_vue/kho/thuan.js';
import {ND} from '../../../public/web_vue/kho/chu.js';
import * as D from '../../../public/web_vue/banh/dbt-thuan.js';
import {DacBietTuan} from '../../../public/web_vue/banh/dac-biet-tuan.js';
import {tenQuayHaiDong} from '../../../public/web_vue/banh/kho-goi-ban.js';

let dat = 0, hong = 0;
const loi = [];
async function ca(ten, ham) {
  try { await ham(); dat++; console.log('  DAT   ' + ten); } catch (e) { hong++; loi.push(ten); console.log('  HONG  ' + ten + '\n        ' + (e && e.message || e)); }
}
function la(ten, co, can) { const a = JSON.stringify(co), b = JSON.stringify(can); if (a !== b) throw new Error(ten + ': được ' + a + ', cần ' + b); }
function dung(ten, x) { if (!x) throw new Error(ten); }

/* Đợt mẫu: mở thứ hai 16/11 8g, chốt thứ sáu 20/11 20g, giao 21 và 22/11. */
function dotMau(them = {}) {
  return Object.assign({id: 'dbt-1', loai: 'dac_biet_tuan', hien: true, nhan: 'CHỈ CUỐI TUẦN', tieu_de: 'CUỐI TUẦN\n21 · 22/11',
    noi_dung: 'Món đặc biệt của tuần này.', bat_dau: '2026-11-15', ket_thuc: '2026-11-22',
    mo_don: '2026-11-16T08:00', chot_don: '2026-11-20T20:00', ngay_giao: ['2026-11-21', '2026-11-22'],
    dem_nguoc: '1', dem_chu_1: 'còn lại để đặt', dem_chu_2: 'Chốt hết thứ sáu 20/11',
    moc: [{nhan: 'MỞ ĐƠN', chu_ngay: 'T2 16/11', luc: '2026-11-16T08:00'}, {nhan: 'CHỐT ĐƠN', chu_ngay: 'T6 20/11', luc: '2026-11-20T20:00'},
      {nhan: 'BẾP LÀM', chu_ngay: 'T6 · T7', luc: '2026-11-20T20:01'}, {nhan: 'GIAO NHẬN', chu_ngay: 'T7 · CN', luc: '2026-11-21T08:00'}],
    mon_dt: [{khoa: 'candle', mo_ta: 'Vani Tahiti', anh: '', nhan_goc: '', toi_da: '2'}]}, them);
}
/* Giờ Việt Nam viết kèm múi giờ, không phụ thuộc múi giờ máy chạy ca. */
function moiTruong(gio, dot = dotMau(), daDat = {}) {
  const toast = [];
  const mt = {
    t: t0, tMon: (ma, tr, d) => d || '', bayGio: () => new Date(gio),
    hen: (f) => { return 0; }, huyHen: () => {},
    doc: async () => ({}), ghi: async () => ({ok: true}),
    luuTru: null, suKien: () => {}, nd: {nhan: {}, khoi: dot ? [dot] : [], dac_biet_da_dat: daDat}
  };
  const k = taoKho(mt);
  return {k, toast: () => k.S.toast.chu};
}
function them(k, tab = 'dac_biet', ten = 'CANDLE', sl = 1) {
  k.S.tab = tab; k.moBanh(k.S.CAKES.find(c => c.k === ten)); k.S.soLuong = sl; return k.addToCart();
}
const iso = k => k.T.isoNgay(k.ngayDangChon.value);

await ca('1. Phép thuần: giờ Việt Nam không theo múi giờ máy; trạng thái đúng mốc mở và chốt', async () => {
  la('01:30 UTC là 08:30 Việt Nam', D.lucVN(new Date('2026-11-17T01:30:00Z')), '2026-11-17T08:30');
  const d = dotMau();
  la('trước mở 1 phút', D.trangThaiDot(d, '2026-11-16T07:59'), 'chua_mo');
  la('đúng giờ mở', D.trangThaiDot(d, '2026-11-16T08:00'), 'mo');
  la('trước chốt 1 phút', D.trangThaiDot(d, '2026-11-20T19:59'), 'mo');
  la('đúng giờ chốt', D.trangThaiDot(d, '2026-11-20T20:00'), 'da_chot');
  la('3 ngày 5 giờ trước chốt: 3 ngày', D.demNguoc(d, '2026-11-17T15:00'), {so: 3, don_vi: 'ngay'});
  la('đúng 24 giờ: 1 ngày', D.demNguoc(d, '2026-11-19T20:00'), {so: 1, don_vi: 'ngay'});
  la('23 giờ 20 phút: 24 giờ', D.demNguoc(d, '2026-11-19T20:40'), {so: 24, don_vi: 'gio'});
  la('40 phút: 1 giờ', D.demNguoc(d, '2026-11-20T19:20'), {so: 1, don_vi: 'gio'});
  la('đã chốt: không đếm', D.demNguoc(d, '2026-11-20T20:00'), null);
  la('qua giờ chốt sang tháng sau (28/02, 31/12)', [D.demNguoc(dotMau({chot_don: '2027-03-01T00:00'}), '2027-02-28T00:00'),
    D.demNguoc(dotMau({chot_don: '2027-01-01T08:00'}), '2026-12-31T08:00')], [{so: 1, don_vi: 'ngay'}, {so: 1, don_vi: 'ngay'}]);
  la('mốc hiện tại', [D.mocHienTai(d, '2026-11-15T10:00'), D.mocHienTai(d, '2026-11-17T10:00'), D.mocHienTai(d, '2026-11-21T09:00')], [-1, 0, 3]);
  la('đợt ẩn, chưa tới, đã qua ngày hiện: không có', [D.dotDangHien([dotMau({hien: false})], '2026-11-17'),
    D.dotDangHien([dotMau({bat_dau: '2026-11-18'})], '2026-11-17'), D.dotDangHien([dotMau({ket_thuc: '2026-11-16'})], '2026-11-17')], [null, null, null]);
  la('số còn: tối đa 2, đã đặt 1, trong giỏ 1', D.conSuat({khoa: 'candle', toi_da: '2'}, {candle: 1}, 1), 0);
  la('không giới hạn', D.conSuat({khoa: 'candle', toi_da: ''}, {candle: 9}, 0), null);
});

await ca('2. Giỏ có món cuối tuần: lịch chỉ còn ngày giao của đợt, ngày đang chọn tự dời sang 21/11 và nhờ khách xác nhận lại', async () => {
  const {k} = moiTruong('2026-11-17T10:00:00+07:00');
  la('giỏ trống: ngày 19/11 chọn được', k.ngayRail.value.find(d => d.i === 2).off, false);
  la('thêm Candle ở tab Đặc biệt tuần này', them(k), 'them');
  la('dòng giỏ là đơn đặt trước', k.S.CART[0].nguon, 'order');
  la('ngày đang chọn dời sang ngày giao đầu tiên', iso(k), '2026-11-21');
  la('chưa coi là khách đã chọn ngày', k.S.daChonNgay, false);
  const off = k.ngayRail.value.filter(d => !d.off).map(d => d.i);
  la('chỉ còn 21 và 22/11 (cách hôm nay 4 và 5 ngày)', off, [4, 5]);
  const cu = iso(k);
  k.pick(2);
  la('bấm 19/11: không đổi ngày', iso(k), cu);
  dung('bấm 19/11: nhắc đúng ngày giao', /21\/11, 22\/11/.test(k.S.toast.chu));
  k.pick(5);
  la('bấm 22/11: chọn được', [iso(k), k.S.daChonNgay], ['2026-11-22', true]);
});

await ca('3. Bánh không thuộc đợt không bị khoá ngày vì đợt; bỏ món cuối tuần khỏi giỏ thì lịch mở lại', async () => {
  const {k} = moiTruong('2026-11-17T10:00:00+07:00');
  la('thêm Phi Tử Tiếu ở tab Đặt bánh trước', them(k, 'order', 'Phi Tử Tiếu'), 'them');
  /* v671 (Sales góp ý 18/11/2026, giám đốc chốt): bánh đặt trước thường chỉ nhận
     ngày mai 18/11, các ngày sau mờ vì luật đó, không phải vì đợt. */
  la('chỉ còn ngày mai', k.ngayRail.value.filter(d => !d.off).map(d => d.i), [1]);
  la('thêm món của đợt (giao 21, 22/11) vào giỏ nhận ngày mai: báo đặt đơn riêng', them(k), false);
  dung('câu nhắc không có chung ngày', /không có chung ngày nhận/.test(k.S.toast.chu));
  k.S.CART.splice(0);
  la('giỏ chỉ có món của đợt', them(k), 'them');
  dung('có Candle: 19/11 bị khoá', k.ngayRail.value.find(d => d.i === 2).off);
  k.S.CART.splice(k.S.CART.findIndex(o => o.k === 'CANDLE'), 1);
  la('bỏ Candle: 19/11 mở lại', k.ngayRail.value.find(d => d.i === 2).off, false);
});


await ca('4. Số lượng tối đa của đợt: đã đặt 1 trên 2 thì chỉ thêm được 1; thêm qua tab Đặt bánh trước cũng bị giữ', async () => {
  const {k} = moiTruong('2026-11-17T10:00:00+07:00', dotMau(), {candle: 1});
  la('thêm 2 cái: bị giữ', them(k, 'dac_biet', 'CANDLE', 2), false);
  dung('nhắc còn 1', /chỉ còn nhận 1 bánh/.test(k.S.toast.chu));
  la('giỏ vẫn trống', k.S.CART.length, 0);
  la('thêm 1 cái: được', them(k, 'dac_biet', 'CANDLE', 1), 'them');
  la('thêm tiếp 1 cái ở tab Đặt bánh trước: bị giữ', them(k, 'order', 'CANDLE', 1), false);
});

await ca('5. Qua giờ chốt hoặc chưa mở đơn: không thêm được món của đợt, bánh khác vẫn đặt bình thường', async () => {
  const a = moiTruong('2026-11-20T20:00:00+07:00').k;
  la('đúng giờ chốt: không thêm', them(a), false);
  dung('nhắc đã chốt', /đã chốt đơn/.test(a.S.toast.chu));
  la('Phi Tử Tiếu vẫn thêm được', them(a, 'order', 'Phi Tử Tiếu'), 'them');
  const b = moiTruong('2026-11-16T07:59:00+07:00').k;
  la('trước giờ mở: không thêm', them(b), false);
  dung('nhắc chưa mở đơn', /chưa mở đơn/.test(b.S.toast.chu));
});

await ca('6. Gửi đơn: giỏ có món của đợt mà đã qua giờ chốt thì dừng trước khi gọi máy chủ', async () => {
  let goi = 0;
  const {k} = moiTruong('2026-11-17T10:00:00+07:00');
  them(k);
  k.S.nhip = 0;
  const d = new Date('2026-11-20T20:30:00+07:00');
  /* Khách để trang mở tới sau giờ chốt rồi mới bấm gửi. */
  const k2 = taoKho({t: t0, tMon: (m, tr, x) => x || '', bayGio: () => d, hen: () => 0, huyHen: () => {}, doc: async () => ({}),
    ghi: async () => { goi++; return {ok: true}; }, luuTru: null, suKien: () => {}, nd: {nhan: {}, khoi: [dotMau()], dac_biet_da_dat: {}}});
  k2.S.CART.push(Object.assign({}, k.S.CART[0]));
  const kq = await k2.submitOrder();
  la('dừng ở giỏ', kq && kq.buoc, 'gio');
  la('không gọi máy chủ', goi, 0);
  dung('nhắc đã chốt', /đã chốt đơn/.test(k2.S.toast.chu));
});

await ca('6b. (Codex #579) Bảng đặt trước đang lọc, Candle chỉ làm cho đợt: thêm ở tab Đặc biệt rồi bấm Sửa bánh, đổi lời chúc, Lưu thay đổi thì lưu được', async () => {
  const {k} = moiTruong('2026-11-17T10:00:00+07:00');
  k.S.TRUOC = {BAWC00068: 5};
  la('thêm Candle ở tab Đặc biệt tuần này', them(k), 'them');
  const c = k.suaDongGio(0);
  dung('mở lại đúng bánh', c && c.k === 'CANDLE');
  dung('size đang sửa nằm trong các size đang nhận', k.kichThuocDangBan(c).some(s => s.id === k.S.CART[0].id));
  /* v681: lời chúc nằm ở từng chiếc (bước Thông tin đơn hàng); Sửa bánh rồi Lưu giữ nguyên lời chúc. */
  k.S.CART[0].chiec[0].wish = 'Mừng sinh nhật';
  la('Lưu thay đổi', k.addToCart(), 'sua');
  la('giỏ vẫn 1 dòng, đã có lời chúc', [k.S.CART.length, k.S.CART[0].chiec[0].wish, k.S.CART[0].qty], [1, 'Mừng sinh nhật', 1]);
  la('mở chi tiết từ tab Đặt bánh trước (đường dẫn bánh) cũng thấy size của đợt', k.kichThuocDangBan(c, 'order').length > 0, true);
  la('tab Có sẵn hôm nay không đổi luật: chỉ size có sẵn', k.kichThuocDangBan(c, 'today').length, c.sizes.length);
  const b = moiTruong('2026-11-17T10:00:00+07:00', null).k;
  b.S.TRUOC = {BAWC00068: 5};
  la('không có đợt: Candle ở tab Đặt bánh trước vẫn theo bảng đặt trước', b.kichThuocDangBan(b.S.CAKES.find(x => x.k === 'CANDLE'), 'order'), []);
});

await ca('6c. (Codex #579) Nút + trong giỏ giữ số lượng tối đa của đợt; nút - và bánh khác không bị ảnh hưởng', async () => {
  const {k} = moiTruong('2026-11-17T10:00:00+07:00', dotMau(), {candle: 1});
  la('thêm 1 cái (còn 1)', them(k), 'them');
  k.cartQty(0, 1);
  la('bấm +: vẫn 1', k.S.CART[0].qty, 1);
  dung("nhắc đã đủ số lượng", /đủ số lượng nhận/.test(k.S.toast.chu));
  const c = moiTruong('2026-11-17T10:00:00+07:00', dotMau({mon_dt: [{khoa: 'candle', toi_da: '3'}]}), {candle: 1}).k;
  them(c); c.cartQty(0, 1);
  la('tối đa 3, đã đặt 1: bấm + lên 2 được', c.S.CART[0].qty, 2);
  c.cartQty(0, 1);
  la('bấm + lần nữa: giữ 2', c.S.CART[0].qty, 2);
  c.cartQty(0, -1);
  la('bấm -: xuống 1', c.S.CART[0].qty, 1);
  const q = moiTruong('2026-11-20T19:00:00+07:00').k;
  them(q);
  q.S.tab = 'order';
  const d = moiTruong('2026-11-20T20:01:00+07:00').k;
  d.S.CART.push(Object.assign({}, q.S.CART[0]));
  d.cartQty(0, 1);
  la('qua giờ chốt: bấm + không tăng', d.S.CART[0].qty, 1);
  la('Phi Tử Tiếu: bấm + vẫn tăng', (() => { them(d, 'order', 'Phi Tử Tiếu'); const i = d.S.CART.findIndex(o => o.k !== 'CANDLE'); d.cartQty(i, 1); return d.S.CART[i].qty; })(), 2);
});

await ca('6d. (Codex #579) Giỏ lưu từ trước vượt số lượng của đợt: dừng ở giỏ trước khi gọi máy chủ', async () => {
  let goi = 0;
  const k = taoKho({t: t0, tMon: (m, tr, x) => x || '', bayGio: () => new Date('2026-11-17T10:00:00+07:00'), hen: () => 0, huyHen: () => {},
    doc: async () => ({}), ghi: async () => { goi++; return {ok: true}; }, luuTru: null, suKien: () => {},
    nd: {nhan: {}, khoi: [dotMau()], dac_biet_da_dat: {candle: 1}}});
  const c = k.S.CAKES.find(x => x.k === 'CANDLE'), z = c.sizes[0];
  k.S.CART.push({k: c.k, img: c.img, id: z.id, cm: z.cm, price: z.p, nguon: 'order', wish: '', adds: [], qty: 2});
  const kq = await k.submitOrder();
  la('dừng ở giỏ', kq && kq.buoc, 'gio');
  la('không gọi máy chủ', goi, 0);
  dung('nhắc còn nhận 1', /chỉ còn nhận 1 bánh/.test(k.S.toast.chu));
});

/* ---------- vẽ thành phần bằng bộ dựng cây của Vue ---------- */
const nut = the => ({the, props: {}, con: [], cha: null, nghe: {},
  addEventListener(ev, f) { (this.nghe[ev] = this.nghe[ev] || []).push(f); },
  removeEventListener(ev, f) { this.nghe[ev] = (this.nghe[ev] || []).filter(x => x !== f); }});
const {createApp} = createRenderer({
  createElement: the => nut(the), createText: chu => ({chu, cha: null}), createComment: chu => ({ghiChu: chu, cha: null}),
  setText: (n, chu) => { n.chu = chu; }, setElementText: (n, chu) => { n.con = chu ? [{chu, cha: n}] : []; },
  insert: (con, cha, moc) => { if (con.cha) con.cha.con.splice(con.cha.con.indexOf(con), 1); const i = moc ? cha.con.indexOf(moc) : -1; if (i >= 0) cha.con.splice(i, 0, con); else cha.con.push(con); con.cha = cha; },
  remove: con => { if (con.cha) { con.cha.con.splice(con.cha.con.indexOf(con), 1); con.cha = null; } },
  parentNode: n => n.cha, nextSibling: n => (n.cha ? n.cha.con[n.cha.con.indexOf(n) + 1] || null : null),
  patchProp: (n, k, cu, moi) => { if (moi == null) delete n.props[k]; else n.props[k] = moi; },
  setScopeId: () => {}, insertStaticContent: () => { throw new Error('không dùng'); }
});
const chu = n => (n == null ? '' : n.chu != null ? n.chu : (n.con || []).map(chu).join(''));
function tim(n, dk, ra = []) { if (!n || !n.con) return ra; if (n.the && dk(n)) ra.push(n); n.con.forEach(x => tim(x, dk, ra)); return ra; }
const lop = (n, l) => String(n.props.class || '').split(' ').includes(l);
async function ve(gio, dot, daDat = {}) {
  const {k} = moiTruong(gio, dot, daDat);
  ND.dac_biet_da_dat = daDat;
  const mo = [];
  const goc = nut('div');
  createApp({render: () => h(DacBietTuan, {kho: k, mo: c => mo.push(c.k)})}).mount(goc);
  await nextTick();
  return {goc, mo};
}

await ca('7. Đợt 1 món: một thẻ lớn, tầng hương, nút chính Đặt món này mở khung chọn bánh; đầu tab đúng chữ đợt và đếm ngược', async () => {
  const {goc, mo} = await ve('2026-11-17T15:00:00+07:00', dotMau());
  la('một thẻ lớn', tim(goc, n => lop(n, 'dbt-mot')).length, 1);
  la('không có băng chuyền, chấm vị trí', [tim(goc, n => lop(n, 'dbt-bang')).length, tim(goc, n => lop(n, 'dbt-cham')).length], [0, 0]);
  const nutDat = tim(goc, n => lop(n, 'dbt-dat'))[0];
  la('chữ nút', chu(nutDat), 'Đặt món này');
  dung('có nhãn Tầng hương', /Tầng hương/.test(chu(goc)));
  nutDat.props.onClick();
  la('bấm nút mở khung chọn Candle', mo, ['CANDLE']);
  la('tiêu đề hai dòng', chu(tim(goc, n => lop(n, 'dbt-tieu'))[0]), 'CUỐI TUẦN21 · 22/11');
  la('đếm ngược 3 ngày', chu(tim(goc, n => lop(n, 'dbt-dem'))[0]).slice(0, 6), '3 ngày');
  la('mốc đang diễn ra là Mở đơn', chu(tim(goc, n => n.the === 'li' && lop(n, 'on'))[0]), 'MỞ ĐƠNT2 16/11');
});

await ca('8. Đợt 2 món: băng chuyền hai thẻ có nút +, hàng chấm vị trí, thẻ đầu có vành', async () => {
  const dot = dotMau({mon_dt: [{khoa: 'candle', mo_ta: '', anh: '', nhan_goc: '', toi_da: ''}, {khoa: 'phi tử tiếu', mo_ta: '', anh: '', nhan_goc: 'Số lượng có hạn', toi_da: ''}]});
  const {goc, mo} = await ve('2026-11-17T15:00:00+07:00', dot);
  la('hai thẻ trong băng chuyền', tim(goc, n => lop(n, 'dbt-bang'))[0].con.length, 2);
  la('hai chấm, chấm đầu sáng', tim(goc, n => lop(n, 'dbt-cham'))[0].con.map(x => x.props.class), ['on', '']);
  la('thẻ đầu đang xem', tim(goc, n => lop(n, 'dbt-the')).map(n => lop(n, 'dang')), [true, false]);
  const cong = tim(goc, n => lop(n, 'dbt-cong'));
  la('mỗi thẻ một nút +', cong.length, 2);
  cong[1].props.onClick();
  la('bấm + thẻ hai mở Phi Tử Tiếu', mo, ['Phi Tử Tiếu']);
  dung('nhãn góc riêng', /Số lượng có hạn/.test(chu(goc)));
});

await ca('9. Đã chốt đơn và chưa mở đơn: nút khoá, thẻ vẫn hiện món; hết số lượng cũng là Đã chốt đơn tuần này', async () => {
  let r = await ve('2026-11-20T21:00:00+07:00', dotMau());
  let nutDat = tim(r.goc, n => lop(n, 'dbt-dat'))[0];
  la('đã chốt: nút khoá, chữ', [nutDat.props.disabled, chu(nutDat)], [true, 'Đã chốt đơn tuần này']);
  dung('vẫn hiện tên món', /CANDLE/.test(chu(r.goc)));
  la('không đếm ngược', tim(r.goc, n => lop(n, 'dbt-dem')).length, 0);
  r = await ve('2026-11-15T20:00:00+07:00', dotMau());
  nutDat = tim(r.goc, n => lop(n, 'dbt-dat'))[0];
  la('chưa mở: nút khoá, ghi ngày mở đơn', [nutDat.props.disabled, chu(nutDat)], [true, 'Mở đơn T2 16/11']);
  r = await ve('2026-11-17T15:00:00+07:00', dotMau(), {candle: 2});
  nutDat = tim(r.goc, n => lop(n, 'dbt-dat'))[0];
  la('đủ 2/2: khoá, Đã chốt đơn tuần này', [nutDat.props.disabled, chu(nutDat)], [true, 'Đã chốt đơn tuần này']);
});

await ca('10. Không có đợt: tab ẩn khỏi vành (kho không có đợt), đường dẫn cũ hiện câu dẫn sang đặt trước', async () => {
  const {goc} = await ve('2026-11-17T15:00:00+07:00', null);
  dung('câu rỗng', /chưa có món đặc biệt/.test(chu(goc)));
  const {k} = moiTruong('2026-11-17T15:00:00+07:00', null);
  la('kho không có đợt', k.dotDbt.value, null);
});

await ca('11. Tab Tại quầy: tên cửa hàng ngắt dòng cố định (THE VAGABOND / QUẬN 1, NHÀ VĂN HOÁ / THANH NIÊN), cửa hàng khác chia đôi theo chữ', async () => {
  la('District 1', tenQuayHaiDong('The Vagabond District 1'), ['THE VAGABOND', 'QUẬN 1']);
  la('tên cũ Trần Cao Vân', tenQuayHaiDong('Trần Cao Vân'), ['THE VAGABOND', 'QUẬN 1']);
  la('hoá/hóa đều ra Hoá', [tenQuayHaiDong('Nhà Văn hóa Thanh Niên'), tenQuayHaiDong('Nhà văn hoá thanh niên')], [['NHÀ VĂN HOÁ', 'THANH NIÊN'], ['NHÀ VĂN HOÁ', 'THANH NIÊN']]);
  la('Quận 10 không nhầm Quận 1', tenQuayHaiDong('Vagabond Quận 10'), ['VAGABOND', 'QUẬN 10']);
  la('cửa hàng khác chia đôi', tenQuayHaiDong('Cửa hàng Thảo Điền Mới'), ['CỬA HÀNG THẢO', 'ĐIỀN MỚI']);
  la('một chữ, trống', [tenQuayHaiDong('Solo'), tenQuayHaiDong('')], [['SOLO'], []]);
});

console.log(`\n${dat} đạt, ${hong} hỏng`);
if (hong) { console.log('Hỏng: ' + loi.join(' | ')); process.exit(1); }

/* v668 Gợi ý mua thêm (phần F prompt /banh, anh Việt duyệt 17/11/2026).

   Chạy THẬT kho trang đặt bánh (kho-banh.js) và kho Tại quầy (kho-goi-ban.js) với Vue
   thật, đồng hồ cố định, máy chủ giả trả đúng hình dạng goi_y_mua.goi_y_dat_truoc,
   cap_quay. Vẽ THẬT khối GoiYMua bằng bộ dựng cây của Vue. Luật chọn món, luật tồn
   ở máy chủ kiểm trong thu_goi_y_mua_668.py.

   Chạy: node vagabond/khung/kiem_thu/hanh_vi/goi_y_mua_668.mjs */
import {createRenderer, h, nextTick} from '../../../public/web_vue/lib/vue.esm-browser.prod.js';
import {taoKho} from '../../../public/web_vue/banh/kho-banh.js';
import {t0} from '../../../public/web_vue/kho/thuan.js';
import {GoiYMua, goiYQuay, monBay, thanhMienPhi} from '../../../public/web_vue/banh/goi-y-mua.js';

let dat = 0, hong = 0;
const loi = [];
async function ca(ten, ham) {
  try { await ham(); dat++; console.log('  DAT   ' + ten); } catch (e) { hong++; loi.push(ten); console.log('  HONG  ' + ten + '\n        ' + (e && e.message || e)); }
}
function la(ten, co, can) { const a = JSON.stringify(co), b = JSON.stringify(can); if (a !== b) throw new Error(ten + ': được ' + a + ', cần ' + b); }
function dung(ten, x) { if (!x) throw new Error(ten); }
const cho = () => new Promise(r => setTimeout(r, 0));

const GY = (mon, them = {}) => Object.assign({bat: 1, toi_da: 4, thanh_mien_phi: 1, mon}, them);
const BIS = {ma: 'BACF00027', ten: 'Biscotti Strawberry, Hũ 200 gr', anh: '/f/b.jpg', gia: 190000, ly_do_vn: 'Dâu tây hợp vị quả mọng', ly_do_en: '', ghim: 0};
const CROI = {ma: 'BANU00015', ten: 'Bánh Plain Croissant, Full size', anh: '/f/c.jpg', gia: 60000, ly_do_vn: 'Croissant bơ cho bữa sáng', ly_do_en: '', ghim: 0};
const CAN = {ma: 'BACF00034', ten: 'Bánh Canelé vị Tahitian Vanilla', anh: '/f/v.jpg', gia: 65000, ly_do_vn: 'Vani Tahiti', ly_do_en: '', ghim: 0};

function moiTruong(traGoiY, cauHinh = {mien_phi_tu: 1000000}) {
  const goi = [];
  const k = taoKho({
    t: t0, tMon: (ma, tr, d) => d || '', bayGio: () => new Date('2026-11-17T10:00:00+07:00'), hen: () => 0, huyHen: () => {},
    doc: async (m, a) => {
      goi.push([m, a]);
      if (m === 'vagabond.goi_y_mua.goi_y_dat_truoc') return typeof traGoiY === 'function' ? traGoiY(a) : traGoiY;
      if (m === 'vagabond.don_web.cau_hinh_web') return cauHinh;
      return {};
    },
    ghi: async (m, a) => { goi.push([m, a]); return {ok: 0, ly_do: 'gia_lap'}; }, luuTru: null, suKien: () => {},
    nd: {nhan: {}, khoi: [], dac_biet_da_dat: {}}
  });
  k.S.mienPhiTu = cauHinh.mien_phi_tu;
  return {k, goi};
}
function themBanh(k, ten = 'CANDLE', size = 0) {
  k.S.tab = 'order'; const c = k.S.CAKES.find(x => x.k === ten); k.moBanh(c); k.S.curSizeId = c.sizes[size].id; return k.addToCart();
}
const daGoiGoiY = goi => goi.filter(x => x[0] === 'vagabond.goi_y_mua.goi_y_dat_truoc');

await ca('1. Giỏ đặt trước: thêm bánh thì hỏi máy chủ với mã bánh (món gốc) và mọi mã trong giỏ; bày tối đa 4 món, món đã trong giỏ không bày', async () => {
  const {k, goi} = moiTruong(GY([BIS, CROI, CAN, {...CAN, ma: 'X4'}, {...CAN, ma: 'X5'}]));
  la('giỏ trống: không hỏi', daGoiGoiY(goi).length, 0);
  la('thêm Candle 12cm', themBanh(k), 'them');
  await cho(); await cho();
  const a = daGoiGoiY(goi).pop()[1];
  la('mã gửi', [JSON.parse(a.ma), JSON.parse(a.bo)], [['BAWC00139'], ['BAWC00139']]);
  la('bày 4 món', k.goiYGio.value.map(u => u.ma), ['BACF00027', 'BANU00015', 'BACF00034', 'X4']);
});

await ca('2. (thử theo prompt) Bấm + thêm ĐÚNG 1 cái, giỏ có dòng đánh dấu thêm từ gợi ý; tổng tiền và thanh miễn phí giao cập nhật; thẻ đó nhường chỗ món kế', async () => {
  const {k} = moiTruong(GY([BIS, CROI, CAN, {...CAN, ma: 'X4'}, {...CAN, ma: 'X5'}]));
  themBanh(k); await cho(); await cho();
  la('tiền bánh trước', k.tienBanh.value, 650000);
  la('thanh miễn phí: còn 350.000', k.thanhMienPhiGio.value, {con: 350000, phan: 65});
  la('bấm + Biscotti', k.themGoiY(k.goiYGio.value[0]), true);
  const d = k.S.CART.find(o => o.id === 'BACF00027');
  la('đúng 1 cái, đánh dấu gợi ý, đặt trước', [d.qty, d.goi_y, d.nguon, d.cm], [1, 1, 'order', 0]);
  la('tổng tiền tăng đúng giá', k.tienBanh.value, 840000);
  la('thanh còn 160.000', k.thanhMienPhiGio.value.con, 160000);
  la('thẻ Biscotti nhường chỗ X5', k.goiYGio.value.map(u => u.ma), ['BANU00015', 'BACF00034', 'X4', 'X5']);
  la('bấm + lần nữa cùng món: không thêm', k.themGoiY(BIS), false);
  dung('nhắc đã thêm', /Đã thêm Biscotti/.test(k.S.toast.chu));
  const tt = k.tong.value;
  la('phí giao và tổng tính lại từ giỏ mới', tt.items, 840000);
});

await ca('3. Đủ mốc miễn phí giao thì ẩn thanh; tự lấy tại quầy thì ẩn; mốc tắt (0) thì ẩn; cài đặt tắt thanh thì ẩn', async () => {
  const {k} = moiTruong(GY([CROI]));
  themBanh(k, 'CANDLE', 2); await cho(); await cho();
  la('Candle 18cm 1.100.000 đủ mốc', k.thanhMienPhiGio.value, null);
  const b = moiTruong(GY([CROI])).k;
  themBanh(b); await cho(); await cho();
  b.S.CO.mode = 'pick';
  la('tự lấy', b.thanhMienPhiGio.value, null);
  la('mốc 0', thanhMienPhi(500000, 0, true, true), null);
  const c = moiTruong(GY([CROI], {thanh_mien_phi: 0})).k;
  themBanh(c); await cho(); await cho();
  la('cài đặt tắt thanh', c.thanhMienPhiGio.value, null);
});

await ca('4. Món thêm từ gợi ý không là món gốc: không hỏi lại theo nó, chỉ báo để không gợi ý lại; gửi đơn kèm danh sách mã thêm từ gợi ý', async () => {
  const {k, goi} = moiTruong(GY([BIS, CROI]));
  themBanh(k); await cho(); await cho();
  k.themGoiY(k.goiYGio.value[0]); await cho(); await cho();
  const a = daGoiGoiY(goi).pop()[1];
  la('món gốc vẫn chỉ Candle, bỏ cả Biscotti', [JSON.parse(a.ma), JSON.parse(a.bo).sort()], [['BAWC00139'], ['BACF00027', 'BAWC00139']]);
  la('phần gửi đơn có goi_y', k.S.CART.filter(o => o.goi_y).map(o => o.id), ['BACF00027']);
});

await ca('5. Máy chủ tắt, không món, lỗi mạng: không bày khối món, không làm hỏng giỏ', async () => {
  for (const [ten, tra] of [['tắt', GY([BIS], {bat: 0})], ['rỗng', GY([])], ['lỗi', () => { throw new Error('mạng'); }], ['rác', 'abc']]) {
    const {k} = moiTruong(tra);
    themBanh(k); await cho(); await cho();
    la(ten + ': không món', k.goiYGio.value, []);
    la(ten + ': giỏ còn bánh', k.S.CART.length, 1);
  }
});

/* ---------- Tại quầy: luật thuần trên món của đúng cửa hàng ---------- */
const MENU = [
  {loai: 'banh', ma: 'BL01', ten: 'Mousse Xoài', anh: '/m.jpg', gia: 85000, con: 6, nhom: 'Bánh lạnh', bienThe: [{ma: 'BL01', gia: 85000, ten: 'Mousse Xoài'}]},
  {loai: 'banh', ma: 'BL02', ten: 'Tart Chanh', anh: '/t.jpg', gia: 75000, con: 2, nhom: 'Bánh lạnh', bienThe: [{ma: 'BL02', gia: 75000, ten: 'Tart Chanh'}]},
  {loai: 'banh', ma: 'BN01', ten: 'Croissant', anh: '/c.jpg', gia: 60000, con: 9, nhom: 'Bánh nướng', bienThe: [{ma: 'BN01', gia: 60000, ten: 'Croissant'}]},
  {loai: 'nuoc', ma: 'NUCF00006', ten: 'Cà Phê Caramel Muối', anh: '/cm.jpg', gia: 95000, nhom_goc: 'Cà phê', tc: [{nhom: 'Đường'}],
    bienThe: [{ma: 'NUCF00006', size: '', gia: 95000, ten: 'Cà Phê Caramel Muối, Nóng/Hot'}, {ma: 'NUCF00007', size: '', gia: 95000, ten: 'Cà Phê Caramel Muối, Đá/Iced'}]},
  {loai: 'nuoc', ma: 'NUTR00017', ten: 'Tách trà Xanh Hoa Lài', anh: '/tl.jpg', gia: 75000, nhom_goc: 'Trà', bienThe: [{ma: 'NUTR00017', gia: 75000, ten: 'Tách trà Xanh Hoa Lài'}]},
  {loai: 'nuoc', ma: 'NUMC00008', ten: 'Matcha Latte', anh: '', gia: 95000, nhom_goc: 'Matcha', bienThe: [{ma: 'NUMC00008', gia: 95000, ten: 'Matcha Latte'}]}
];
const CFG = {bat: 1, toi_da: 4, nguong: 3, thanh_mien_phi: 1, mien_phi_tu: 500000, ghim: [], hom_nay: '2026-11-17',
  ly_do_nhom: {'Đồ uống': ['Uống kèm cho hợp', 'A drink'], 'Bánh trên tủ': ['Bánh còn trên tủ hôm nay', 'On the counter']},
  cap: [{mon_goc: '', nhom_goc: 'Bánh lạnh', mon_goi_y: 'NUCF00007', ly_do_vn: 'Caramel muối hợp kem béo', uu_tien: 10},
    {mon_goc: '', nhom_goc: 'Bánh lạnh', mon_goi_y: 'NUTR00017', ly_do_vn: 'Trà lài thanh vị', uu_tien: 20},
    {mon_goc: '', nhom_goc: 'Bánh lạnh', mon_goi_y: 'NUMC00008', ly_do_vn: 'Thiếu ảnh', uu_tien: 5}]};

await ca('6. Tại quầy, giỏ có bánh: UỐNG KÈM theo cặp đã duyệt của nhóm bánh, đúng size trong cặp (Caramel muối đá), món thiếu ảnh không bày', async () => {
  const r = goiYQuay([{ma: 'BL01', loai: 'banh'}], MENU, CFG);
  la('loại', r.loai, 'uong');
  la('món và câu', r.ds.map(u => [u.ma, u.ly_do_vn]), [['NUCF00007', 'Caramel muối hợp kem béo'], ['NUTR00017', 'Trà lài thanh vị']]);
  la('size theo cặp', r.ds[0].bt.ma, 'NUCF00007');
  const g = goiYQuay([{ma: 'BN01', loai: 'banh'}], MENU, Object.assign({}, CFG, {cap: []}));
  la('nhóm chưa có cặp: đồ uống không cần chọn, câu chung', g.ds.map(u => [u.ma, u.ly_do_vn]), [['NUTR00017', 'Uống kèm cho hợp']]);
});

await ca('7. Tại quầy, giỏ chỉ có đồ uống: ĂN KÈM bánh còn trên tủ từ ngưỡng 3, nhiều trước; tắt thì không có', async () => {
  const r = goiYQuay([{ma: 'NUTR00017', loai: 'nuoc'}], MENU, CFG);
  la('bánh trên tủ', [r.loai, r.ds.map(u => u.ma)], ['an', ['BN01', 'BL01']]);
  la('câu', r.ds[0].ly_do_vn, 'Bánh còn trên tủ hôm nay');
  la('tắt', goiYQuay([{ma: 'NUTR00017', loai: 'nuoc'}], MENU, Object.assign({}, CFG, {bat: 0})).ds, []);
  la('giỏ rỗng', goiYQuay([], MENU, CFG).ds, []);
});

await ca('8. Kho Tại quầy thật: bấm + thêm đúng 1 ly đúng size, đánh dấu để gửi đơn; tổng và thanh miễn phí giao cập nhật', async () => {
  const {k} = moiTruong(GY([]));
  const gb = k.goiBan;
  k.S.STORE = {quay: [{ma: 'TCV', ten: 'The Vagabond Quận 1', mon: MENU.filter(m => m.loai === 'banh').map(m => ({ma: m.ma, ten: m.ten, anh: m.anh, gia: m.gia, con: m.con, nhom: m.nhom, giao: 1})),
    do_uong: [{ma: 'NUCF00006', ten: 'Cà Phê Caramel Muối, Nóng/Hot', anh: '/cm.jpg', gia: 95000, nhom_goc: 'Cà phê', giao: 1},
      {ma: 'NUCF00007', ten: 'Cà Phê Caramel Muối, Đá/Iced', anh: '/cm.jpg', gia: 95000, nhom_goc: 'Cà phê', giao: 1},
      {ma: 'NUTR00017', ten: 'Tách trà Xanh Hoa Lài', anh: '/tl.jpg', gia: 75000, nhom_goc: 'Trà', giao: 1}], topping: []}]};
  k.S.storeDaTai = true; k.S.tab = 'store'; k.S.quayChon = 'TCV';
  gb.G.daKiem = true; gb.G.ban = {ok: 0};
  gb.G.gy.cfg = CFG;
  la('chế độ giao', gb.cheDo.value, 'giao');
  const banh = {...MENU[0], ma: 'BL01', con: 6};
  gb.bamThem(banh);
  la('giỏ có Mousse', gb.G.gio.map(x => x.ma), ['BL01']);
  const ds = gb.goiYQuayHien.value;
  la('khối Uống kèm', [ds.loai, ds.ds.map(u => u.ma)], ['uong', ['NUCF00007', 'NUTR00017']]);
  la('thanh: còn 415.000', gb.thanhMienPhiQuay.value.con, 415000);
  la('bấm +', gb.themGoiYQuay(ds.ds[0]), true);
  const dong = gb.G.gio.find(x => x.ma === 'NUCF00007');
  la('đúng 1 ly, đúng size đá của cặp', [dong && dong.sl, dong && dong.ma], [1, 'NUCF00007']);
  la('tổng', gb.tong.value, 180000);
  la('thanh còn 320.000', gb.thanhMienPhiQuay.value.con, 320000);
  la('thẻ nhường chỗ', gb.goiYQuayHien.value.ds.map(u => u.ma), ['NUTR00017']);
  la('đánh dấu gửi đơn', gb.G.gy.da, ['NUCF00007']);
  gb.G.web.gia = {tien_hang: 180000, giam: 50000, phi: 30000};
  la('có báo giá: mốc tính trên tiền hàng SAU ưu đãi như máy chủ (còn 370.000)', gb.thanhMienPhiQuay.value.con, 370000);
  gb.G.web.tuLay = true;
  la('tự lấy: ẩn thanh', gb.thanhMienPhiQuay.value, null);
});

/* ---------- vẽ khối bằng bộ dựng cây của Vue ---------- */
const nut = the => ({the, props: {}, con: [], cha: null});
const {createApp} = createRenderer({
  createElement: the => nut(the), createText: chu => ({chu, cha: null}), createComment: chu => ({ghiChu: chu, cha: null}),
  setText: (n, chu) => { n.chu = chu; }, setElementText: (n, chu) => { n.con = [{chu, cha: n}]; },
  insert: (c, cha, mo) => { c.cha = cha; const i = mo ? cha.con.indexOf(mo) : -1; if (i >= 0) cha.con.splice(i, 0, c); else cha.con.push(c); },
  remove: c => { if (c.cha) { const i = c.cha.con.indexOf(c); if (i >= 0) c.cha.con.splice(i, 1); } },
  patchProp: (n, k, cu, moi) => { n.props[k] = moi; }, parentNode: n => n.cha, nextSibling: n => { const c = n.cha && n.cha.con; return c ? c[c.indexOf(n) + 1] || null : null; }
});
const chuCua = n => n.chu !== undefined ? n.chu : (n.con || []).map(chuCua).join('');
const tim = (n, lop, ra = []) => { if (n.props && String(n.props.class || '').split(' ').includes(lop)) ra.push(n); (n.con || []).forEach(c => tim(c, lop, ra)); return ra; };

await ca('9. Khối vẽ thật: tiêu đề in hoa, thẻ có ảnh, + (nhãn đọc màn hình), tên, câu lý do, giá; không món và không thanh thì không vẽ gì; thẻ nhỏ trong khung Đặt giao', async () => {
  const goc = nut('div'); const da = [];
  createApp({render: () => h(GoiYMua, {tieu: 'GIAO KÈM CÙNG CHUYẾN', ds: [BIS, CROI], them: u => da.push(u.ma), thanh: {con: 350000, phan: 65}, idKhoi: 'gyGio'})}).mount(goc);
  await nextTick();
  la('tiêu đề', chuCua(tim(goc, 'gy-tieu')[0]), 'GIAO KÈM CÙNG CHUYẾN');
  la('số thẻ', tim(goc, 'gy-the').length, 2);
  la('câu lý do', chuCua(tim(goc, 'gy-ly')[0]), 'Dâu tây hợp vị quả mọng');
  la('giá', chuCua(tim(goc, 'gy-gia')[0]).replace(/\s/g, ' '), '190.000 đ');
  la('thanh', chuCua(tim(goc, 'gy-mp')[0]), 'Thêm 350.000 đ nữa được miễn phí giao');
  const cong = tim(goc, 'gy-cong')[0];
  dung('nút + có nhãn', /Thêm Biscotti/.test(cong.props['aria-label']));
  cong.props.onClick(); la('bấm + gọi thêm đúng món', da, ['BACF00027']);
  const g2 = nut('div');
  createApp({render: () => h(GoiYMua, {tieu: 'X', ds: [], them: () => {}, thanh: null})}).mount(g2);
  await nextTick();
  la('không món không thanh: không vẽ', tim(g2, 'gy').length, 0);
  const g3 = nut('div');
  createApp({render: () => h(GoiYMua, {tieu: 'UỐNG KÈM CHO HỢP', ds: [BIS], them: () => {}, nho: true})}).mount(g3);
  await nextTick();
  dung('khung Đặt giao dùng thẻ nhỏ', String(tim(g3, 'gy')[0].props.class).includes('gy-nho'));
  la('monBay', monBay([BIS, CROI, CAN], ['BANU00015'], 1).map(u => u.ma), ['BACF00027']);
});

console.log(`\n${dat} đạt, ${hong} hỏng`);
if (hong) { console.log('Hỏng: ' + loi.join(' | ')); process.exit(1); }

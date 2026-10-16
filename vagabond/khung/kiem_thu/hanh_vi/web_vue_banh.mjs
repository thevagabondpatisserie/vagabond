/* Ca kiểm HÀNH VI của kho trang đặt bánh bản Vue (web_vue/banh/kho-banh.js).

   Chạy THẬT kho với Vue thật (bản ESM trong repo), mạng giả, đồng hồ tua
   được, hẹn giờ bấm tay. Mỗi ca dựng đúng chuỗi thao tác của khách, không gọi
   thêm hàm "cho chắc" (bài học 06/09: ca gọi thêm hàm đồng bộ đã che mất lỗi).

   Chạy: node vagabond/khung/kiem_thu/hanh_vi/web_vue_banh.mjs */
import {taoKho} from '../../../public/web_vue/banh/kho-banh.js';
import {bienNhan} from '../../../public/web_vue/trang/app.js';
import {MAU} from '../../../public/web_vue/banh/mau.js';
import {t0, tienVN, hangGui} from '../../../public/web_vue/kho/thuan.js';
import {nextTick} from '../../../public/web_vue/lib/vue.esm-browser.prod.js';

let dat = 0, hong = 0;
const loi = [];
async function ca(ten, ham) {
  try { await ham(); dat++; } catch (e) { hong++; loi.push(ten + '\n      ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n      ') : e)); }
}
function la(ten, co, can) {
  const a = JSON.stringify(co), b = JSON.stringify(can);
  if (a !== b) throw new Error(ten + ': được ' + a + ', cần ' + b);
}
function dung(ten, x) { if (!x) throw new Error(ten); }

/* Môi trường giả: đồng hồ, hẹn giờ bấm tay, mạng ghi vết, kho phiên. */
function moiTruong(gio, mang = {}) {
  const dong = {gio: new Date(gio)};
  const hen = [];
  const vet = [];
  const kho = new Map();
  const mt = {
    t: t0, tMon: (ma, tr, d) => d || '',
    bayGio: () => new Date(dong.gio),
    hen: (f, ms) => { hen.push({f, ms}); return hen.length; },
    huyHen: id => { if (id && hen[id - 1]) hen[id - 1].huy = true; },
    doc: async (phuong, p) => { vet.push(['GET', phuong, p]); return mang[phuong] ? mang[phuong](p) : {}; },
    ghi: async (phuong, than) => { vet.push(['POST', phuong, than]); return mang[phuong] ? mang[phuong](than) : {ok: true}; },
    luuTru: {getItem: k => (kho.has(k) ? kho.get(k) : null), setItem: (k, v) => kho.set(k, v), removeItem: k => kho.delete(k)},
    suKien: () => {}, nd: {nhan: {}}
  };
  const chayHen = async () => {
    await nextTick();
    /* Chạy các hẹn đang chờ; lời hứa mạng chưa trả thì không đợi mãi. */
    const cho = [];
    for (let i = 0; i < hen.length; i++) { const h = hen[i]; if (!h.huy && !h.da) { h.da = true; cho.push(Promise.resolve(h.f())); } }
    await Promise.race([Promise.all(cho), new Promise(r => setTimeout(r, 30))]);
    await nextTick();
  };
  return {mt, dong, hen, vet, kho, chayHen};
}
const coThem = (k, ten = 'CANDLE') => { k.moBanh(k.S.CAKES.find(c => c.k === ten)); return k.addToCart(); };

await ca('#471 Pixel biên nhận gỡ token trước PageView, GuiDon khớp event_id CAPI, reload không bắn lại', async () => {
  const events = [], storage = new Map();
  const win = {location: {pathname: '/web_moi/banh/xong/SECRET'},
    history: {replaceState(a,b,path) { win.location.pathname = path; }},
    sessionStorage: {getItem:k=>storage.get(k), setItem:(k,v)=>storage.set(k,v)},
    fbq: (...args) => events.push([win.location.pathname, args])};
  const D = {bien_nhan:{ma:'DW-THU', mon:[], tong:'100.000 đ'}, pixel_id:'123',
    su_kien:{event_id:'uuid-capi-gui-don', ban:true, gia_tri:100000, ma_mon:['BANH']}};
  bienNhan(D, win);
  dung('mọi sự kiện đã gỡ token', events.every(x => !x[0].includes('SECRET')));
  const gui = events.filter(x => x[1][0] === 'trackCustom');
  la('cùng event_id do máy chủ cấp', gui[0][1][3], {eventID:'uuid-capi-gui-don'});
  bienNhan(D, win);
  la('gửi lại không lặp GuiDon', events.filter(x => x[1][0] === 'trackCustom').length, 1);
  const n = events.length;
  la('reload không token đọc đúng biên nhận', bienNhan({khong_token:1}, win), D.bien_nhan);
  la('reload không bắn Meta', events.length, n);
  win.history.replaceState = () => { throw new Error('history chặn'); };
  win.location.pathname = '/web_moi/banh/xong/SECRET';
  bienNhan(D, win); la('không gỡ được token thì không Meta', events.length, n);
});

await ca('#471 nhấp kép và mất phản hồi: giữ nonce, một đơn, trả biên nhận cũ', async () => {
  const don = new Map(), gui = []; let tha;
  const {mt} = moiTruong('2026-10-11T08:00:00', {
    'vagabond.don_hang.tao_don': async p => {
      const d = JSON.parse(p.don); gui.push(d);
      if (!don.has(d.nonce)) {
        don.set(d.nonce, '/banh/xong/token-cu');
        await new Promise(r => { tha = r; });
        throw new Error('Máy chủ nhận, mạng mất phản hồi');
      }
      return {ok: 1, duong_dan: don.get(d.nonce)};
    }
  });
  const k = taoKho(mt); coThem(k); k.pick(3); k.pickSlot(6);
  Object.assign(k.S.f, {name: 'Khách', phone: '0901234567', addr: '12 Nguyễn Huệ'});
  k.S.CO.dongy = true;
  const a = k.submitOrder(), b = k.submitOrder();
  la('hai lần bấm chỉ một POST', gui.length, 1);
  tha(); la('báo lỗi mạng', (await a).buoc, 'loi'); await b;
  la('giữ giỏ', k.S.CART.length, 1);
  const kq = await k.submitOrder();
  la('biên nhận cũ', kq.duong_dan, '/banh/xong/token-cu');
  la('nonce không đổi', gui[1].nonce, gui[0].nonce);
  la('chỉ một đơn bên máy chủ giả', don.size, 1);
  la('bấm lại sau thành công vẫn biên nhận cũ', (await k.submitOrder()).duong_dan, kq.duong_dan);
  la('không POST sau thành công', gui.length, 2);
});

await ca('Bấm + trong giỏ: tiền bánh và tổng đổi NGAY, không cần vẽ lại (lỗi PR #460)', async () => {
  const {mt} = moiTruong('2026-10-11T08:00:00');
  const k = taoKho(mt);
  coThem(k); coThem(k, 'Kankin');
  la('trước', k.tong.value.total, 650000 + 680000);
  k.cartQty(0, 1);
  la('tiền bánh sau +', k.tienBanh.value, 2 * 650000 + 680000);
  la('tổng sau +', k.tong.value.total, 2 * 650000 + 680000);
  la('dòng giỏ sau +', k.dongGio.value[0].tien, tienVN(1300000));
  k.cartRemove(1);
  la('tổng sau bỏ', k.tong.value.total, 1300000);
  la('thanh giỏ', k.soBanh.value, 2);
});

await ca('Ưu đãi: đổi giỏ, mã, số điện thoại hay ngày là hỏi lại; số giảm cũ không hiện', async () => {
  const hoi = [];
  const {mt, chayHen} = moiTruong('2026-10-11T08:00:00', {'vagabond.don_hang.xem_uu_dai': th => { const d = JSON.parse(th.don); hoi.push(d); return {ok: true, giam: d.ma_uu_dai === 'GIAM10' ? 100000 : 0, ap: [{ten: 'x'}]}; }});
  const k = taoKho(mt);
  coThem(k); k.moGio(); await chayHen();
  la('lần hỏi đầu', hoi.length, 1);
  k.S.f.ma = 'giam10'; k.apMaUuDai(); await chayHen();
  la('giảm theo mã', k.giam.value, 100000);
  k.cartQty(0, 1); await nextTick();
  la('giỏ đổi chưa hỏi lại thì coi như 0', k.giam.value, 0);
  await chayHen();
  la('hỏi lại sau khi đổi giỏ', hoi.length, 3);
  la('giảm lại sau khi hỏi', k.giam.value, 100000);
  k.S.f.phone = '0901234567'; await chayHen();
  la('đổi số là hỏi lại', hoi.length, 4);
  la('số gửi đi', hoi[3].dien_thoai, '0901234567');
  k.pick(5); await chayHen();
  dung('đổi ngày là hỏi lại', hoi.length >= 5 && hoi[hoi.length - 1].ngay_nhan.startsWith('2026-10-16'));
});

await ca('Ưu đãi: kết quả lần hỏi CŨ về muộn không đè kết quả mới', async () => {
  let tra = [];
  const {mt} = moiTruong('2026-10-11T08:00:00', {'vagabond.don_hang.xem_uu_dai': () => new Promise(r => tra.push(r))});
  const k = taoKho(mt);
  coThem(k);
  const cu = k.xemUuDai();
  k.cartQty(0, 1);
  const moi = k.xemUuDai();
  tra[1]({ok: true, giam: 7000, ap: []}); await moi;
  tra[0]({ok: true, giam: 99000, ap: []}); await cu;
  la('giữ số của lần mới', k.giam.value, 7000);
});

await ca('Qua nửa đêm: thẻ tóm tắt, bảng tổng và ngày gửi đi cùng MỘT ngày', async () => {
  const {mt, dong} = moiTruong('2026-10-11T23:50:00');
  const k = taoKho(mt);
  coThem(k); k.pick(3); k.pickSlot(8);
  la('ngày neo', k.mocGioNhan(), '2026-10-14T15:00:00');
  dong.gio = new Date('2026-10-12T00:10:00'); k.nhip();
  la('vẫn đúng ngày sau nửa đêm', k.mocGioNhan(), '2026-10-14T15:00:00');
  la('độ lệch tự tính lại', k.picked.value, 2);
  la('bảng tổng cùng ngày', k.T.dmy(k.ngayDangChon.value), '14/10');
});

await ca('Khung giờ đã qua khi tab mở lâu: không gửi, mở lại bộ chọn', async () => {
  const {mt, dong} = moiTruong('2026-10-11T08:00:00');
  const k = taoKho(mt);
  coThem(k); k.pick(0); k.pickSlot(6); /* 13h hôm nay, cần >= 12h */
  dung('lúc chọn còn kịp', k.gioHopLe.value && k.daChot.value);
  dong.gio = new Date('2026-10-11T10:30:00'); k.nhip();
  la('giờ không còn kịp', k.gioHopLe.value, false);
  k.S.f.name = 'A'; k.S.f.phone = '0901234567'; k.S.f.addr = '12 Nguyen Hue Q1'; k.S.CO.dongy = true;
  const kq = await k.submitOrder();
  la('dừng ở lịch', kq.buoc, 'lich');
  la('mở bộ chọn', k.S.moLich, true);
});

await ca('Chưa tự chọn đủ ngày và giờ thì không lấy giá trị mặc định làm lịch', async () => {
  const {mt} = moiTruong('2026-10-11T08:00:00');
  const k = taoKho(mt);
  coThem(k); k.S.f.name = 'A'; k.S.f.phone = '0901234567'; k.S.f.addr = '12 Nguyen Hue Q1'; k.S.CO.dongy = true;
  la('chưa chọn gì', (await k.submitOrder()).buoc, 'lich');
  k.pick(3);
  la('chọn ngày chưa chọn giờ', (await k.submitOrder()).buoc, 'lich');
});

await ca('Gửi đơn: thứ tự chặn và đơn gửi đi đúng như trang cũ', async () => {
  const {mt} = moiTruong('2026-10-11T08:00:00', {'vagabond.don_hang.tao_don': () => ({ok: true, duong_dan: '/banh/xong/abc123'})});
  const k = taoKho(mt);
  coThem(k); k.S.wish = ''; k.pick(3); k.pickSlot(6);
  la('thiếu tên', (await k.submitOrder()).buoc, 'ten');
  k.S.f.name = 'Khách';
  la('thiếu số', (await k.submitOrder()).buoc, 'sdt');
  k.S.f.phone = '0901 234 567';
  la('thiếu địa chỉ', (await k.submitOrder()).buoc, 'dia_chi');
  k.S.f.addr = '12 Nguyễn Huệ Quận 1';
  la('chưa đồng ý', (await k.submitOrder()).buoc, 'dong_y');
  k.S.CO.dongy = true; k.S.CO.gift = true;
  const kq = await k.submitOrder();
  la('xong', [kq.buoc, kq.duong_dan], ['xong', '/banh/xong/abc123']);
  la('ngày', kq.don.ngay_nhan, '2026-10-14T13:00:00');
  la('thẻ khung giờ và bánh tặng', kq.don.tags, [89, 68]);
  la('món', kq.don.items, [{variation_id: 'BAWC00139', quantity: 1}]);
  la('số chỉ còn chữ số', kq.don.dien_thoai, '0901234567');
  dung('note_print có dòng bánh tặng', kq.don.note_print.startsWith('BÁNH TẶNG'));
  la('giỏ trống sau khi gửi', k.S.CART.length, 0);
});

await ca('Đang có ưu đãi mà giỏ vừa đổi: hỏi lại trước khi gửi, số đổi thì dừng cho khách xem', async () => {
  let giam = 50000;
  const {mt, vet} = moiTruong('2026-10-11T08:00:00', {'vagabond.don_hang.xem_uu_dai': () => ({ok: true, giam, ap: []}), 'vagabond.don_hang.tao_don': () => ({ok: true})});
  const k = taoKho(mt);
  coThem(k); k.pick(3); k.pickSlot(6);
  Object.assign(k.S.f, {name: 'A', phone: '0901234567', addr: '12 Nguyễn Huệ Q1'}); k.S.CO.dongy = true;
  k.S.f.ma = 'X'; k.apMaUuDai(); await k.xemUuDai();
  la('đang giảm', k.giam.value, 50000);
  k.cartQty(0, 1); giam = 80000;
  const kq = await k.submitOrder();
  la('dừng cho khách xem', kq.buoc, 'uu_dai');
  la('chưa gửi đơn', vet.filter(v => v[1] === 'vagabond.don_hang.tao_don').length, 0);
  la('tổng mới', k.tong.value.total, 1300000 - 80000);
});

await ca('Phí giao: lần hỏi cũ về muộn bị bỏ; Ahamove lỗi thì không hiện 0 hay miễn phí', async () => {
  const tra = [];
  const {mt, chayHen} = moiTruong('2026-10-11T08:00:00', {'vagabond.giao_hang.phi_giao': () => new Promise(r => tra.push(r))});
  const k = taoKho(mt);
  coThem(k);
  k.S.f.addr = '12 Nguyen Hue Q1'; k.quoteShip(); await chayHen();
  k.S.f.addr = '99 Le Loi Q1 HCM'; k.quoteShip(); await chayHen();
  la('hai lần hỏi', tra.length, 2);
  tra[1]({ok: false}); await new Promise(r => setTimeout(r, 0));
  tra[0]({ok: true, total_fee: 30000}); await new Promise(r => setTimeout(r, 0));
  la('trạng thái chưa rõ, không lấy số cũ', k.S.CO.shipTrangThai, 'chua_ro');
  la('không tính phí', k.tong.value.ship, 0);
  la('nhãn tổng', k.tong.value.tt.tong_nhan, 'Tạm tính, chưa gồm phí giao');
  la('có nút thử lại', k.S.goi.phiThuLai, true);
});

await ca('Giới hạn số còn nhận theo ô Dư decor, kể cả khi bấm + trong giỏ', async () => {
  const {mt} = moiTruong('2026-10-11T08:00:00');
  const k = taoKho(mt);
  k.S.TRUOC = {BAWC00139: 2}; k.S.tab = 'order';
  k.moBanh(k.S.CAKES[0]); k.S.soLuong = 2;
  la('thêm 2', k.addToCart(), 'them');
  k.cartQty(0, 1);
  la('chặn quá 2', k.S.CART[0].qty, 2);
  dung('báo khách', /chỉ còn nhận 2/.test(k.S.toast.chu));
});

await ca('Lưu giỏ trong phiên rồi tải lại trang: giỏ, lịch, ô nhập về đủ, giá lấy từ danh mục', async () => {
  const a = moiTruong('2026-10-11T08:00:00');
  const k = taoKho(a.mt);
  k.phucHoiGio();
  coThem(k); k.pick(3); k.pickSlot(6); k.S.f.name = 'Lan'; k.S.CO.mode = 'pick';
  const luu = JSON.parse(a.kho.get('vgb-gio-v1'));
  luu.gio[0].price = 1; a.kho.set('vgb-gio-v1', JSON.stringify(luu));
  const k2 = taoKho(a.mt);
  k2.phucHoiGio();
  la('giỏ', k2.S.CART.map(o => [o.id, o.qty, o.price]), [['BAWC00139', 1, 650000]]);
  la('lịch', [k2.S.ngayChon, k2.S.pickedSlot, k2.daChot.value], ['2026-10-14', 6, true]);
  la('ô nhập', k2.S.f.name, 'Lan');
  la('cách nhận', k2.S.CO.mode, 'pick');
});

await ca('PR #462: nháp trang cũ khôi phục đủ ô và Vue vẫn ghi kiểu cũ để quay lại an toàn', async () => {
  const a = moiTruong('2026-10-11T08:00:00');
  const giaTri = {phone: '0901234567', name: 'Lan', mail: 'lan@example.com', addr: '12 Nguyễn Huệ', rname: 'Minh',
    rphone: '0912345678', note: 'Giao trước 10 giờ', mst: '0318561568', cname: 'Công ty ABC',
    cmail: 'ketoan@example.com', caddr: '1 Lê Lợi', ma: 'SINHNHAT10'};
  const truongCu = {};
  Object.entries(giaTri).forEach(([k, v]) => { truongCu['f-' + k] = v; });
  a.kho.set('vgb-gio-v1', JSON.stringify({luc: new Date('2026-10-11T07:00:00').getTime(),
    gio: [{id: 'BAWC00139', qty: 1, cm: 12}], truong: truongCu}));
  const k = taoKho(a.mt);
  k.phucHoiGio();
  la('mọi ô từ nháp cũ', k.S.f, giaTri);
  k.S.f.note = 'Giữ lạnh';
  const luu = JSON.parse(a.kho.get('vgb-gio-v1'));
  dung('ghi id DOM cho trang cũ đọc lại', luu.truong['f-note'] === 'Giữ lạnh' && !('note' in luu.truong));
});

await ca('PR #462: quầy trả lỗi vẫn hiện tab In store và nút thử lại gọi lại máy chủ', async () => {
  let soLan = 0;
  const {mt, vet} = moiTruong('2026-10-11T08:00:00', {'vagabond.kiem_kho.con_tren_quay_web': () => {
    soLan++;
    if (soLan === 1) throw new Error('HTTP 500');
    return {quay: [{ma: 'D1', ten: 'D1', mon: []}]};
  }});
  const k = taoKho(mt);
  await k.napQuay();
  la('ghi nhận lỗi lần đầu', [k.S.storeLoi, k.S.storeDaTai], [true, false]);
  dung('tab hiện khi lỗi', MAU.includes(':hidden="!S.storeDaTai && !S.storeLoi"'));
  dung('nút thử lại gọi đúng cửa', MAU.includes('@click="kho.napQuay()"'));
  await k.napQuay();
  la('bấm thử gọi lại API', vet.filter(x => x[1] === 'vagabond.kiem_kho.con_tren_quay_web').length, 2);
  la('lần sau tải được', [k.S.storeLoi, k.S.storeDaTai], [false, true]);
});

await ca('Trước khi khôi phục xong thì không ghi đè giỏ đã cất (Codex #450)', async () => {
  const a = moiTruong('2026-10-11T08:00:00');
  a.kho.set('vgb-gio-v1', JSON.stringify({luc: new Date('2026-10-11T07:00:00').getTime(), gio: [{id: 'BAWC00139', qty: 2, cm: 12}]}));
  const k = taoKho(a.mt);
  k.S.f.name = 'x'; /* một thay đổi trước khi khôi phục */
  dung('chưa xoá bản cất', a.kho.has('vgb-gio-v1'));
  k.phucHoiGio();
  la('khôi phục', k.S.CART.map(o => o.qty), [2]);
});

await ca('Hàng mùa vụ: không thêm quá số còn của mùa', async () => {
  const {mt} = moiTruong('2026-10-11T08:00:00');
  const k = taoKho(mt);
  k.S.MUA = {co: 1, mon: [{ma: 'TT1', ten: 'Hộp', gia: 500000, con: 1, het: 0}]};
  la('lần 1', k.themHangMua('TT1'), true);
  la('lần 2 bị chặn', k.themHangMua('TT1'), false);
  la('giỏ', k.S.CART[0].qty, 1);
});

await ca('Thêm nhanh: nhiều cỡ thì mở chi tiết, một cỡ thì thêm thẳng', async () => {
  const {mt} = moiTruong('2026-10-11T08:00:00');
  const k = taoKho(mt);
  k.S.TODAY = {BAWC00122: 3};
  la('một cỡ hôm nay', k.themNhanh(k.S.CAKES.find(c => c.k === 'Kankin'), 'today'), 'them');
  la('nhiều cỡ', k.themNhanh(k.S.CAKES[0], 'order'), 'mo');
});

await ca('Danh mục máy chủ trộn vào bánh có sẵn, giá trong giỏ làm tươi theo giá mới', async () => {
  const {mt} = moiTruong('2026-10-11T08:00:00', {'vagabond.kiem_banh.co_the_ban_hom_nay': () => ({banh: {BAWC00139: 3}, nhom: [{ten: 'CANDLE', sizes: [{cm: 12, ma: 'BAWC00139', gia: 700000}]}, {ten: 'Món Mới', sizes: [{cm: 14, ma: 'BAWC09999', gia: 500000}]}]})});
  const k = taoKho(mt);
  coThem(k);
  await k.napTon();
  la('giá mới trong giỏ', k.S.CART[0].price, 700000);
  dung('món mới lên danh mục', k.S.CAKES.some(c => c.k === 'Món Mới'));
  la('bánh có sẵn', k.banhHomNay.value.map(c => c.k), ['CANDLE']);
});

await ca('#463: napTon giữ đúng mã và số Sales online từ co_the_ban_hom_nay', async () => {
  const tra = {
    banh: {BAWC00463: 4, BAWC00464: 2},
    nhom: [
      {ten: 'Bánh kiểm đồng bộ', sizes: [
        {cm: 12, ma: 'BAWC00463', gia: 463000, con: 4},
        {cm: 16, ma: 'BAWC00464', gia: 664000, con: 2}
      ]}
    ]
  };
  const {mt, vet} = moiTruong('2026-10-12T08:00:00', {
    'vagabond.kiem_banh.co_the_ban_hom_nay': () => tra
  });
  const k = taoKho(mt);
  await k.napTon();
  la('chỉ gọi đúng cửa Sales online', vet.map(x => x[1]), ['vagabond.kiem_banh.co_the_ban_hom_nay']);
  la('kho TODAY giữ nguyên cặp mã-số', k.S.TODAY, tra.banh);
  const nhom = k.S.CAKES.find(x => x.k === 'Bánh kiểm đồng bộ');
  dung('nhóm máy chủ lên danh mục', nhom);
  la('hai cỡ giữ đúng mã để tra số ở một nguồn TODAY', nhom.sizes.map(x => x.id),
    ['BAWC00463', 'BAWC00464']);
  la('computed Có sẵn hôm nay đọc cùng nguồn', k.banhHomNay.value.map(x => x.k),
    ['Bánh kiểm đồng bộ']);
  la('tổng tồn computed từ cùng bản đồ', k.tongTon.value, 6);
});

await ca('hangGui gộp dòng trùng mã và phụ kiện theo số bánh', async () => {
  la('gộp', hangGui([{id: 'A', qty: 2, adds: [{id: 'P'}]}, {id: 'A', qty: 1, adds: [{id: 'P'}]}]),
    [{variation_id: 'A', quantity: 3}, {variation_id: 'P', quantity: 3}]);
});

await ca('Codex #462: MST 12 số của hộ kinh doanh được tra tên; 11 số bị báo đúng câu mới', async () => {
  const goi = [];
  const {mt, chayHen} = moiTruong('2026-10-11T08:00:00', {'vagabond.api.tra_mst': p => { goi.push(p.mst); return {ok: true, ten: 'HKD NGUYEN VAN A', dia_chi: '1 Lê Lợi'}; }});
  const k = taoKho(mt);
  k.S.f.mst = '079123456789'; k.lookupMst(); await chayHen();
  la('gọi tra mã số thuế với 12 số', goi, ['079123456789']);
  la('hiện tên tra về', k.S.goi.mst[1].chu, 'HKD NGUYEN VAN A');
  k.S.f.mst = '07912345678'; k.lookupMst(); await chayHen();
  la('11 số không gọi máy chủ', goi.length, 1);
  la('câu báo độ dài nói cả 12 số', k.S.goi.mst[0].chu, 'Mã số thuế phải là 10 số, 12 số nếu là hộ kinh doanh, hoặc 13 số nếu là chi nhánh.');
});

await ca('Codex #462: tonDaThu chỉ bật sau lần hỏi tồn đầu, kể cả khi máy chủ lỗi (link chia sẻ chờ tới lúc này mới bị coi là hỏng)', async () => {
  const {mt} = moiTruong('2026-10-11T08:00:00', {'vagabond.kiem_banh.co_the_ban_hom_nay': () => ({banh: {BAWC09999: 3}, nhom: [{ten: 'Banh Moi Thu', sizes: [{cm: 14, ma: 'BAWC09999', gia: 700000, con: 3}]}]})});
  const k = taoKho(mt);
  la('trước khi nạp', k.S.tonDaThu, false);
  dung('bánh bếp thêm chưa có', !k.S.CAKES.some(c => c.k === 'Banh Moi Thu'));
  await k.napTon();
  la('sau khi nạp', k.S.tonDaThu, true);
  dung('bánh bếp thêm đã có', k.S.CAKES.some(c => c.k === 'Banh Moi Thu'));
  const loiMang = moiTruong('2026-10-11T08:00:00', {'vagabond.kiem_banh.co_the_ban_hom_nay': () => { throw new Error('mat mang'); }});
  const k2 = taoKho(loiMang.mt);
  await k2.napTon();
  la('máy chủ lỗi vẫn bật', k2.S.tonDaThu, true);
  la('lỗi thì chưa coi là nạp xong', k2.S.tonNapXong, false);
});

for (const moi of [0, 80000]) await ca('Máy chủ đổi giảm sang ' + moi + ': xem lại rồi bấm gửi, giữ nonce', async () => {
  const gui = [];
  const {mt} = moiTruong('2026-10-11T08:00:00', {
    'vagabond.don_hang.xem_uu_dai': () => ({ok: true, giam: 50000, ap: []}),
    'vagabond.don_hang.tao_don': p => {
      gui.push(JSON.parse(p.don));
      return gui.length === 1 ? {ok: 0, ly_do: 'uu_dai_doi', uu: {giam: moi, ap: []}} : {ok: 1};
    }
  });
  const k = taoKho(mt);
  coThem(k); k.pick(3); k.pickSlot(6);
  Object.assign(k.S.f, {name: 'A', phone: '0901234567', addr: '12 Nguyễn Huệ Q1'});
  k.S.CO.dongy = true;
  await k.xemUuDai();
  la('dừng', (await k.submitOrder()).buoc, 'uu_dai');
  la('gửi số khách thấy', gui[0].giam_da_xem, 50000);
  la('tổng mới', k.tong.value.total, 650000 - moi);
  la('chưa gửi lại tự động', gui.length, 1);
  la('giữ giỏ', k.S.CART.length, 1);
  la('mở nút', k.S.dangGui, false);
  la('bấm lần hai thành công', (await k.submitOrder()).buoc, 'xong');
  la('gửi số đã xác nhận', gui[1].giam_da_xem, moi);
  la('giữ nonce', gui[1].nonce, gui[0].nonce);
});

await ca('Mã đã dùng: lần gửi đầu hiện lý do, bỏ mã, không tự gửi lại', async () => {
  const gui = [];
  const {mt} = moiTruong('2026-10-11T08:00:00', {
    'vagabond.don_hang.xem_uu_dai': () => ({ok: true, giam: 50000, ap: []}),
    'vagabond.don_hang.tao_don': p => {
      gui.push(JSON.parse(p.don));
      return {ok: 0, ly_do: 'ma_uu_dai', chi_tiet: 'Mã TET26: mã đã được dùng.'};
    }
  });
  const k = taoKho(mt);
  coThem(k); k.pick(3); k.pickSlot(6);
  Object.assign(k.S.f, {name: 'A', phone: '0901234567', addr: '12 Nguyễn Huệ Q1', ma: 'TET26'});
  k.S.CO.dongy = true; k.S.CO.uuMa = 'TET26';
  k.S.CO.uu = {khoa: k.khoaUuDai.value, giam: 50000, ap: [], loi: ''};
  la('dừng ngay lần đầu', (await k.submitOrder()).buoc, 'loi');
  la('chỉ gửi một lần', gui.length, 1);
  dung('hiện đúng lý do', k.S.goi.gui.some(x => JSON.stringify(x).includes('mã đã được dùng')));
  la('bỏ mã khỏi ô và trạng thái', [k.S.f.ma, k.S.CO.uuMa], ['', '']);
  la('giữ giỏ để khách sửa', k.S.CART.length, 1);
});

await ca('v590: gợi ý mã hiện tổng sau giảm và nút Áp dụng không giả ô nhập', async () => {
  const {mt} = moiTruong('2026-10-11T08:00:00', {
    'vagabond.don_hang.xem_uu_dai': () => ({ok: true, giam: 50000, ap: [{ten: 'Giảm sinh nhật'}]})
  });
  const k = taoKho(mt);
  coThem(k); k.S.CO.ship = 10000; k.S.CO.shipTrangThai = 'chinh_xac';
  k.S.f.ma = 'SN50'; k.S.CO.uuMa = 'SN50'; await k.xemUuDai();
  la('tổng = bánh - giảm + phí', k.tong.value.total, 610000);
  dung('gợi ý có số giảm và tổng mới', JSON.stringify(k.goiYMa.value).includes('50.000') && JSON.stringify(k.goiYMa.value).includes('610.000'));
  dung('nút là nút chính, không phải thẻ chọn giả ô nhập', MAU.includes('class="btn btn-xs" id="btnMa"'));
  dung('đáy chừa đủ nút dính', MAU.includes('padding-bottom:140px'));
});

await ca('#471 phản hồi địa chỉ cũ không ghi đè chữ và tọa độ mới', async () => {
  let traGoiY, traChiTiet;
  const {mt,chayHen} = moiTruong('2026-10-11T08:00:00', {
    'vagabond.dia_chi.goi_y_dia_chi': () => new Promise(r=>{traGoiY=r;}),
    'vagabond.dia_chi.chi_tiet_dia_chi': () => new Promise(r=>{traChiTiet=r;})
  });
  const k = taoKho(mt); k.S.f.addr='Địa chỉ cũ'; k.goiYDiaChi(); await chayHen();
  k.S.f.addr='Mới'; k.goiYDiaChi(); traGoiY({suggestions:[{mo_ta:'Cũ',place_id:'cu'}]}); await nextTick();
  la('gợi ý cũ bị bỏ',k.S.goiY,[]);
  k.S.goiY=[{mo_ta:'Địa chỉ cũ',place_id:'cu'}]; const doi=k.chonGoiY(0);
  k.S.f.addr='Mới'; k.goiYDiaChi(); traChiTiet({lat:10,lng:106,dia_chi:'Địa chỉ cũ'}); await doi;
  la('giữ chữ mới',k.S.f.addr,'Mới'); la('không tọa độ cũ',k.S.CO.pickedLoc,null);
});

await ca('F21 máy chủ hết hàng giữ giỏ, nonce, tải lại tồn và chỉ dẫn Sales', async () => {
  let nap=0;
  const {mt}=moiTruong('2026-10-13T08:00:00', {
    'vagabond.don_hang.tao_don':()=>({ok:0,ly_do:'het_hang',nhac:['CANDLE chỉ còn 0 cái.']}),
    'vagabond.kiem_banh.co_the_ban_hom_nay':()=>{nap++;return {banh:{},dat_truoc:{nhom:[]}};}
  });
  const k=taoKho(mt);coThem(k);k.pick(3);k.pickSlot(6);
  Object.assign(k.S.f,{name:'A',phone:'0901234567',addr:'12 Nguyễn Huệ Q1'});k.S.CO.dongy=true;
  const gio=JSON.stringify(k.S.CART);
  la('chặn',(await k.submitOrder()).buoc,'het_hang');await nextTick();
  la('giỏ giữ nguyên',JSON.stringify(k.S.CART),gio);dung('giữ nonce',!!k.S.CO.nonce);
  dung('tải lại',nap>0);dung('nói số và cách xử lý',JSON.stringify(k.S.goi.gui).includes('còn 0 cái')&&JSON.stringify(k.S.goi.gui).includes('đổi ngày'));
});

await ca('v598 port v597: thiệp nhỏ đi cùng dòng giỏ qua cộng dồn, sửa dòng và tải lại trang; số kẹp 0 tới 30', async () => {
  const a = moiTruong('2026-10-11T08:00:00');
  const k = taoKho(a.mt);
  k.phucHoiGio();
  const ban = k.S.CAKES.find(c => c.k === 'CANDLE');
  k.moBanh(ban); k.S.nia = 1; k.S.thiep = 2; k.addToCart();
  k.moBanh(ban); la('mở bánh mới thì ô thiệp về 0', k.S.thiep, 0); k.S.nia = 1; k.S.thiep = 3; k.addToCart();
  la('khác số thiệp là hai dòng, không cộng dồn', k.S.CART.map(o => [o.qty, o.dung_cu]), [[1, {nia: 1, dia: 0, thiep: 2}], [1, {nia: 1, dia: 0, thiep: 3}]]);
  k.moBanh(ban); k.S.nia = 1; k.S.thiep = 2; k.addToCart();
  la('cùng cấu hình thì cộng dồn', k.S.CART.map(o => o.qty), [2, 1]);
  la('phiếu bếp nhân số lượng', k.T.chuDungCu(k.S.CART[0]), '2 nĩa gỗ, 0 dĩa bã mía, 4 thiệp nhỏ');
  la('chỉ thiệp thì không ghi nĩa dĩa', k.T.chuDungCu({qty: 1, dung_cu: {nia: 0, dia: 0, thiep: 1}}), '1 thiệp nhỏ');
  la('kẹp số', k.T.chuanDungCu({nia: -3, dia: '99', thiep: 'x'}), {nia: 0, dia: 30, thiep: 0});
  k.suaDongGio(1); la('sửa dòng giỏ mở lại đúng số thiệp', [k.S.nia, k.S.thiep], [1, 3]);
  k.luuGio();
  const k2 = taoKho(a.mt); k2.phucHoiGio();
  la('tải lại trang giữ thiệp', k2.S.CART.map(o => o.dung_cu.thiep), [2, 3]);
});

console.log('Bo ca kiem HANH VI trang dat banh ban Vue');
loi.forEach(d => console.log('  HONG  ' + d));
console.log(dat + ' ca dat, ' + hong + ' ca hong, tong ' + (dat + hong) + ' ca.');
process.exit(hong ? 1 : 0);

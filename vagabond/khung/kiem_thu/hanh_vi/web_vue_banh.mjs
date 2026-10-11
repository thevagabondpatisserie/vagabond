/* Ca kiểm HÀNH VI của kho trang đặt bánh bản Vue (web_vue/banh/kho-banh.js).

   Chạy THẬT kho với Vue thật (bản ESM trong repo), mạng giả, đồng hồ tua
   được, hẹn giờ bấm tay. Mỗi ca dựng đúng chuỗi thao tác của khách, không gọi
   thêm hàm "cho chắc" (bài học 06/09: ca gọi thêm hàm đồng bộ đã che mất lỗi).

   Chạy: node vagabond/khung/kiem_thu/hanh_vi/web_vue_banh.mjs */
import {taoKho} from '../../../public/web_vue/banh/kho-banh.js';
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

await ca('hangGui gộp dòng trùng mã và phụ kiện theo số bánh', async () => {
  la('gộp', hangGui([{id: 'A', qty: 2, adds: [{id: 'P'}]}, {id: 'A', qty: 1, adds: [{id: 'P'}]}]),
    [{variation_id: 'A', quantity: 3}, {variation_id: 'P', quantity: 3}]);
});

console.log('Bo ca kiem HANH VI trang dat banh ban Vue');
loi.forEach(d => console.log('  HONG  ' + d));
console.log(dat + ' ca dat, ' + hong + ' ca hong, tong ' + (dat + hong) + ' ca.');
process.exit(hong ? 1 : 0);

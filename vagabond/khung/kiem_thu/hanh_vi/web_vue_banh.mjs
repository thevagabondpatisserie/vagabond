/* Ca kiểm HÀNH VI của kho trang đặt bánh bản Vue (web_vue/banh/kho-banh.js).

   Chạy THẬT kho với Vue thật (bản ESM trong repo), mạng giả, đồng hồ tua
   được, hẹn giờ bấm tay. Mỗi ca dựng đúng chuỗi thao tác của khách, không gọi
   thêm hàm "cho chắc" (bài học 06/09: ca gọi thêm hàm đồng bộ đã che mất lỗi).

   Chạy: node vagabond/khung/kiem_thu/hanh_vi/web_vue_banh.mjs */
import {taoKho} from '../../../public/web_vue/banh/kho-banh.js';
import {bienNhan} from '../../../public/web_vue/trang/app.js';
import {MAU} from '../../../public/web_vue/banh/mau.js';
import {readFileSync} from 'node:fs';
const APP = readFileSync(new URL('../../../public/web_vue/banh/app.js', import.meta.url), 'utf8');
import {t0, tienVN, hangGui, tronMon} from '../../../public/web_vue/kho/thuan.js';
import {nextTick} from '../../../public/web_vue/lib/vue.esm-browser.prod.js';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import pathMod from 'node:path';
const GOC_REPO = pathMod.resolve(pathMod.dirname(fileURLToPath(import.meta.url)), '..', '..', '..', '..');

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
/* v681: bánh mới mặc định Cần cờ, lời chúc trống, bước gửi nhắc nhập lời chúc. Các ca
   cũ không nói về cờ thì chọn Không cần cờ (đúng một thao tác của khách) cho mọi chiếc. */
const khongCo = k => k.S.CART.forEach(o => (o.chiec || []).forEach(c => { c.co = false; }));
const coThem = (k, ten = 'CANDLE') => { k.moBanh(k.S.CAKES.find(c => c.k === ten)); const kq = k.addToCart(); khongCo(k); return kq; };

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
  k.cartQty(0, 1); khongCo(k); giam = 80000;
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

await ca('Codex #594: giỏ đã lưu cách Tiền mặt (nay không còn) mở lại thì về Chuyển khoản VÀ có dòng báo khách xem lại; giỏ lưu cách còn hợp lệ thì không báo', async () => {
  const a = moiTruong('2026-11-19T08:00:00');
  const k = taoKho(a.mt);
  k.phucHoiGio(); coThem(k); k.pick(3); k.pickSlot(6);
  const luu = JSON.parse(a.kho.get('vgb-gio-v1'));
  la('giỏ mới lưu chuyển khoản, không báo', [luu.co.pay, k.S.CO.payBao], ['bank', false]);
  luu.co.pay = 'cash'; a.kho.set('vgb-gio-v1', JSON.stringify(luu));
  const k2 = taoKho(a.mt); k2.phucHoiGio();
  la('tiền mặt cũ: về chuyển khoản, có báo', [k2.S.CO.pay, k2.S.CO.payBao], ['bank', true]);
  luu.co.pay = 'bank'; a.kho.set('vgb-gio-v1', JSON.stringify(luu));
  const k3 = taoKho(a.mt); k3.phucHoiGio();
  la('cách còn hợp lệ: không báo', [k3.S.CO.pay, k3.S.CO.payBao], ['bank', false]);
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
  /* v638: ô Mã giới thiệu mới, nháp trang cũ không có thì để trống. */
  la('mọi ô từ nháp cũ', k.S.f, {...giaTri, gt: ''});
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
  /* v658: dải tab thay bằng Vành nghiêng; điều kiện hiện tab Tại quầy nằm ở mucVanh (app.js). */
  dung('tab hiện khi lỗi', APP.includes("{tab: 'store', nhan: t('tab_store', 'Tại quầy'), hien: !!(S.storeDaTai || S.storeLoi), lop: 'store'}"));
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
  /* v681 (BẢN 2 mục 2.7): nút viên viền Robin cùng hàng ô mã, không phải thẻ chọn giả ô nhập. */
  dung('nút Áp dụng là nút viên cùng hàng ô mã', MAU.includes('<div class="ma-hang"><input id="f-ma"') && MAU.includes('class="nut-vien" id="btnMa"'));
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

await ca('v598 sang v681: thiệp nhỏ giỏ bản trước chuyển thành thiệp nhỏ theo từng chiếc; chữ phiếu bếp đếm đúng số chiếc', async () => {
  const a = moiTruong('2026-10-11T08:00:00');
  a.kho.set('vgb-gio-v1', JSON.stringify({luc: new Date('2026-10-11T07:00:00').getTime(), gio: [
    {k: 'CANDLE', id: 'BAWC00139', cm: 12, price: 1, nguon: 'order', qty: 2, wish: '', adds: [], dung_cu: {nia: 0, dia: 0, thiep: 2}},
    {k: 'CANDLE', id: 'BAWC00139', cm: 12, price: 1, nguon: 'order', qty: 1, wish: '', adds: [], dung_cu: {nia: 0, dia: 0, thiep: 0}}]}));
  const k = taoKho(a.mt); k.phucHoiGio();
  la('dòng có thiệp: mỗi chiếc thiệp nhỏ', k.S.CART.map(o => o.chiec.map(c => c.thiep)), [['nho', 'nho'], ['khong']]);
  la('số thiệp của dòng không còn nằm ở dung_cu', k.S.CART.map(o => o.dung_cu.thiep), [0, 0]);
  la('phiếu bếp đếm số chiếc chọn thiệp nhỏ', k.T.chuDungCu(k.S.CART[0]), '2 thiệp nhỏ');
  la('dòng giỏ bản trước (chưa có chiếc) vẫn in đúng', k.T.chuDungCu({qty: 2, dung_cu: {nia: 1, dia: 0, thiep: 2}}), '2 nĩa gỗ, 0 dĩa bã mía, 4 thiệp nhỏ');
  la('kẹp số', k.T.chuanDungCu({nia: -3, dia: '99', thiep: 'x'}), {nia: 0, dia: 30, thiep: 0});
  dung('trang chọn bánh không còn ô Số thiệp nhỏ và ô lời chúc', !MAU.includes('id="s-thiep"') && !MAU.includes('id="s-wish"'));
});

await ca('Dĩa, nĩa tặng kèm (anh Việt 20/11/2026): chọn một lần cho cả đơn, gửi thành dòng món giá 0, kẹp 0 tới 20, giữ qua tải lại, giỏ bản trước dồn số về đơn, gửi xong về 0', async () => {
  const {mt, kho} = moiTruong('2026-10-11T08:00:00', {'vagabond.don_hang.tao_don': () => ({ok: true, duong_dan: '/banh/xong/dc1'})});
  const k = taoKho(mt); k.phucHoiGio();
  la('mặc định không gửi', [k.S.DC.dia, k.S.DC.nia], [0, 0]);
  la('giỏ trống: không gửi dĩa, nĩa dù đã bấm', (k.doiDc('dia', 1), k.T.hangGui(k.S.CART, k.S.DC)), []);
  la('v692 giỏ trống: trần 0, bấm Thêm không lên số', [k.S.DC.dia, k.tranDc.value], [0, 0]);
  coThem(k); coThem(k);
  la('v692 hai bánh 12cm: trần 20 bộ', k.tranDc.value, 20);
  k.doiDc('dia', 4); k.doiDc('nia', 1); k.doiDc('nia', -1); k.doiDc('nia', -1); k.doiDc('nia', 2);
  la('nút − không xuống dưới 0', [k.S.DC.dia, k.S.DC.nia], [4, 2]);
  for (let i = 0; i < 40; i++) k.doiDc('nia', 1);
  la('kẹp 20 (bằng trần số lượng của máy chủ)', k.S.DC.nia, 20);
  k.doiDc('nia', -18); k.doiDc('khac', 5);
  la('mã lạ bỏ qua', Object.keys(k.S.DC).sort(), ['dia', 'nia']);
  la('món gửi: bánh rồi dĩa, nĩa, không nhân số bánh', k.T.hangGui(k.S.CART, k.S.DC),
    [{variation_id: 'BAWC00139', quantity: 2}, {variation_id: 'BAPK00020', quantity: 4}, {variation_id: 'BAPK00018', quantity: 2}]);
  la('khoá ưu đãi đổi khi đổi số dĩa', (() => { const a = k.khoaUuDai.value; k.doiDc('dia', 1); const b = k.khoaUuDai.value; k.doiDc('dia', -1); return a !== b; })(), true);
  /* Tải lại trang giữ số. */
  const k2 = taoKho(mt); k2.phucHoiGio();
  la('tải lại giữ số', [k2.S.DC.dia, k2.S.DC.nia], [4, 2]);
  /* Giỏ lưu bản trước: nĩa, dĩa theo từng bánh, nhân số bánh, dồn về đơn. */
  const luu = JSON.parse(kho.get([...kho.keys()][0]));
  luu.gio[0].dung_cu = {nia: 2, dia: 1, thiep: 1}; luu.gio[0].qty = 2; delete luu.dc; delete luu.gio[0].chiec;
  kho.set([...kho.keys()][0], JSON.stringify(luu));
  const k3 = taoKho(mt); k3.phucHoiGio();
  la('giỏ bản trước: dồn số về đơn', [k3.S.DC.dia, k3.S.DC.nia], [2, 4]);
  la('dòng bánh không còn nĩa, dĩa', k3.S.CART[0].dung_cu, {nia: 0, dia: 0, thiep: 0});
  la('v681: thiệp giỏ bản trước chuyển sang từng chiếc', k3.S.CART[0].chiec.map(c => c.thiep), ['nho', 'nho']);
  la('không gửi hai lần', k3.T.hangGui(k3.S.CART, k3.S.DC).filter(x => x.variation_id.startsWith('BAPK')), [{variation_id: 'BAPK00020', quantity: 2}, {variation_id: 'BAPK00018', quantity: 4}]);
  dung('ghi chú bếp không còn nĩa, dĩa theo bánh', !/nĩa/.test(k3.T.chuDungCu(k3.S.CART[0])));
  /* Gửi đơn. */
  k.pick(3); k.pickSlot(6);
  Object.assign(k.S.f, {name: 'Khách', phone: '0901234567', addr: '12 Nguyễn Huệ Quận 1'}); k.S.CO.dongy = true;
  const kq = await k.submitOrder();
  la('đơn gửi có dòng dĩa, nĩa', kq.don.items.filter(x => x.variation_id.startsWith('BAPK')), [{variation_id: 'BAPK00020', quantity: 4}, {variation_id: 'BAPK00018', quantity: 2}]);
  la('gửi xong về 0', [k.S.DC.dia, k.S.DC.nia], [0, 0]);
});

await ca('v644 bánh có bộ nội dung web: mô tả, tầng chỉ lấy từ thẻ Bánh, kể cả khi để trống; bánh cũ giữ đường cũ', async () => {
  const cakes = [{k: 'Very Berry', img: '/cu.png', desc: 'Mô tả tĩnh cũ', layers: [['Cũ', '']], sizes: [{cm: 12, p: 1, id: 'BAWC00086'}]},
    {k: 'Kankin', img: '/k.png', desc: 'Kankin tĩnh', layers: [], sizes: [{cm: 16, p: 1, id: 'BAWC00124'}]}];
  tronMon(cakes, [
    {ten: 'Very Berry', anh: '/files/vb.png', anhs: ['/files/vb.png', '/files/can.jpg'], mo_ta: '', tang: [], tu_web: 1, sizes: [{cm: 12, ma: 'BAWC00086', gia: 620000}]},
    {ten: 'Kankin', anh: '/files/k2.png', anhs: ['/files/k2.png'], mo_ta: '', tang: [], sizes: [{cm: 16, ma: 'BAWC00124', gia: 900000}]}]);
  la('Very Berry theo thẻ Bánh', [cakes[0].tuWeb, cakes[0].desc, cakes[0].layers, cakes[0].anhs], [1, '', [], ['/files/vb.png', '/files/can.jpg']]);
  la('Kankin (đường cũ) giữ chữ tĩnh khi máy chủ không gửi', [cakes[1].tuWeb, cakes[1].desc], [undefined, 'Kankin tĩnh']);
});

await ca('v675 dị ứng và bảo quản: bánh có thẻ Bánh nhận hai mục từ máy chủ, để trống thì rỗng (trang ẩn mục)', async () => {
  const cakes = [{k: 'Very Berry', img: '', desc: '', layers: [], sizes: [{cm: 12, p: 1, id: 'BAWC00086'}]},
    {k: 'Kankin', img: '', desc: '', layers: [], sizes: [{cm: 16, p: 1, id: 'BAWC00124'}]}];
  tronMon(cakes, [
    {ten: 'Very Berry', anh: '/a.png', anhs: ['/a.png'], mo_ta: '', tang: [], di_ung: 'Sữa, trứng', bao_quan: 'Giữ lạnh', tu_web: 1, sizes: [{cm: 12, ma: 'BAWC00086', gia: 1}]},
    {ten: 'Kankin', anh: '/k.png', anhs: ['/k.png'], mo_ta: '', tang: [], di_ung: '', bao_quan: '', tu_web: 1, sizes: [{cm: 16, ma: 'BAWC00124', gia: 1}]}]);
  la('đã điền', [cakes[0].diUng, cakes[0].baoQuan], ['Sữa, trứng', 'Giữ lạnh']);
  la('chưa điền', [cakes[1].diUng, cakes[1].baoQuan], ['', '']);
});

/* Codex PR #547 (1c8d221f): máy chủ lọc hết bánh bị ẩn khỏi hai danh sách, kho
   Vue cũ coi đặt trước rỗng là chưa có dữ liệu và đưa ra 8/8 bánh mặc định. */
await ca('Codex 547: bảng Bánh trên web đang dùng, hai danh sách rỗng thì tab đặt trước không còn bánh mặc định nào', async () => {
  const {mt} = moiTruong('2026-11-07T08:00:00', {'vagabond.kiem_banh.co_the_ban_hom_nay': () => ({banh: {}, nhom: [], dat_truoc: {nhom: []}, chi_hien: 1})});
  const k = taoKho(mt);
  const mac = k.S.CAKES.length;
  await k.napTon();
  dung('có bánh mặc định trước khi nạp', mac > 0);
  la('đặt trước', k.banhDatTruoc.value.length, 0);
  la('danh mục', k.S.CAKES.length, 0);
  /* Bánh có sẵn hôm nay mà không nhận đặt trước: không được lọt sang tab đặt trước. */
  const goc = taoKho(moiTruong('2026-11-07T08:00:00').mt).S.CAKES[0];
  const m2 = moiTruong('2026-11-07T08:00:00', {'vagabond.kiem_banh.co_the_ban_hom_nay': () => ({banh: {[goc.sizes[0].id]: 2},
    nhom: [{ten: goc.k, anh: '/files/x.png', sizes: [{cm: goc.sizes[0].cm, ma: goc.sizes[0].id, gia: 700000}]}], dat_truoc: {nhom: []}, chi_hien: 1})});
  const k2 = taoKho(m2.mt);
  await k2.napTon();
  la('hôm nay có một bánh', k2.banhHomNay.value.map(c => c.k), [goc.k]);
  la('đặt trước vẫn rỗng', k2.banhDatTruoc.value.length, 0);
});

await ca('Codex 547: đang dùng thì chỉ bánh và cỡ máy chủ trả mới lên tab đặt trước; chưa dùng thì giữ danh mục mặc định như cũ', async () => {
  const goc = taoKho(moiTruong('2026-11-07T08:00:00').mt).S.CAKES;
  const c0 = goc[0], s0 = c0.sizes[0];
  const tra = {banh: {}, nhom: [], dat_truoc: {nhom: [{ten: c0.k, anh: '/files/x.png', sizes: [{cm: s0.cm, ma: s0.id, gia: 700000, con: 2}]}]}, chi_hien: 1};
  const {mt} = moiTruong('2026-11-07T08:00:00', {'vagabond.kiem_banh.co_the_ban_hom_nay': () => tra});
  const k = taoKho(mt);
  await k.napTon();
  la('một bánh', k.banhDatTruoc.value.map(c => c.k), [c0.k]);
  la('đúng cỡ máy chủ trả', k.kichThuocDangBan(k.banhDatTruoc.value[0], 'order').map(z => z.id), [s0.id]);
  const cu = moiTruong('2026-11-07T08:00:00', {'vagabond.kiem_banh.co_the_ban_hom_nay': () => ({banh: {}, nhom: [], dat_truoc: {nhom: []}})});
  const k2 = taoKho(cu.mt);
  await k2.napTon();
  la('chưa dùng: danh mục mặc định', k2.banhDatTruoc.value.length, goc.length);
});

/* ---------------- v645 ưu đãi đơn đầu tiên trên web ----------------
   Máy chủ giả giữ ĐÚNG luật của don_dau_web: chưa xác thực thì can_xac_thuc,
   xác thực xong (phiên mở) thì du và giảm 50.000. Trang không tự tính số. */
function mayChuDonDau({tien = 'du_tien', maGiam = 0} = {}) {
  const v = {hoi: [], gui: [], xac: [], phien: ''};
  const mang = {
    'vagabond.don_hang.xem_uu_dai': th => {
      const d = JSON.parse(th.don); v.hoi.push(d);
      const so = String(d.dien_thoai || '').replace(/\D/g, '');
      const base = {giam: 50000, toi_thieu: 300000};
      if (tien === 'thieu') return {ok: 1, giam: 0, ap: [], don_dau: {...base, trang_thai: 'chua_du_tien', ap_dung: 0, bo_ma: 0}};
      if (v.phien !== so) return {ok: 1, giam: d.ma_uu_dai ? maGiam : 0, ap: d.ma_uu_dai && maGiam ? [{ten: 'Mã', giam: maGiam}] : [],
        don_dau: {...base, trang_thai: 'can_xac_thuc', ap_dung: 0, bo_ma: 0}};
      if (d.ma_uu_dai && maGiam >= 50000) return {ok: 1, giam: maGiam, ap: [{ten: 'Mã', giam: maGiam}], don_dau: {...base, trang_thai: 'du', ap_dung: 0, bo_ma: 0}};
      return {ok: 1, giam: 50000, ap: [{ten: 'Ưu đãi đơn đầu tiên trên web', giam: 50000}],
        don_dau: {...base, trang_thai: 'du', ap_dung: 1, bo_ma: d.ma_uu_dai ? 1 : 0}};
    },
    'vagabond.thanh_vien.gui_ma': th => { v.gui.push(th); return v.loiGui ? {ok: 0, ly_do: v.loiGui} : {ok: 1, song_giay: 300}; },
    'vagabond.thanh_vien.xac_thuc': th => { v.xac.push(th); if (th.ma !== '123456') return {ok: 0, ly_do: 'ma_khong_dung'}; v.phien = th.sdt; return {ok: 1}; },
  };
  return {v, mang};
}

await ca('v645 đơn đầu: số chưa xác thực hiện thẻ mời; gửi mã đúng số; mã 5 số không gọi máy; mã sai báo câu dễ hiểu; mã đúng thì hỏi lại và tổng trừ 50.000', async () => {
  const {v, mang} = mayChuDonDau();
  const {mt, chayHen} = moiTruong('2026-11-08T08:00:00', mang);
  const k = taoKho(mt);
  coThem(k); k.S.f.phone = '0931 224 334'; k.moGio(); await chayHen();
  la('thẻ mời xác thực', k.theDonDau.value && k.theDonDau.value.kieu, 'xac_thuc');
  dung('thẻ nói số và mức giảm', k.theDonDau.value.tieu.includes('50.000') && k.theDonDau.value.phu.includes('0931224334'));
  la('chưa giảm', k.giam.value, 0);
  await k.guiMaDonDau();
  la('gửi mã đúng số', v.gui.map(x => x.sdt), ['0931224334']);
  la('sang bước nhập mã', k.S.CO.dd.buoc, 'ma');
  k.S.CO.dd.ma = '12345'; await k.xacThucDonDau();
  la('mã 5 số: không gọi máy', v.xac.length, 0);
  dung('báo cần 6 số', /6 số/.test(k.S.CO.dd.loi));
  k.S.CO.dd.ma = '111111'; await k.xacThucDonDau();
  la('mã sai: câu dùng chung đăng nhập', k.S.CO.dd.loi, 'Mã chưa đúng. Kiểm tra tin nhắn Zalo.');
  la('vẫn ở bước nhập mã', k.S.CO.dd.buoc, 'ma');
  const truoc = v.hoi.length;
  k.S.CO.dd.ma = '123 456'; await k.xacThucDonDau(); await chayHen();
  la('xác thực bằng số đã bỏ khoảng trắng', v.xac[v.xac.length - 1], {sdt: '0931224334', ma: '123456'});
  la('xác thực xong thì hỏi lại ưu đãi một lần', v.hoi.length - truoc, 1);
  la('thẻ Đã giảm', k.theDonDau.value.kieu, 'da_ap');
  la('tổng trừ 50.000', k.giam.value, 50000);
});

await ca('v645 đơn đầu: đổi số giữa chừng thì về bước đầu, không giữ mã của số cũ; Zalo không gửi được thì báo câu cho khách web (không nhắc thu ngân)', async () => {
  const {v, mang} = mayChuDonDau();
  const {mt, chayHen} = moiTruong('2026-11-08T08:00:00', mang);
  const k = taoKho(mt);
  coThem(k); k.S.f.phone = '0931224334'; k.moGio(); await chayHen();
  await k.guiMaDonDau(); k.S.CO.dd.ma = '123';
  k.S.f.phone = '0901234567'; await chayHen();
  la('về bước đầu, xoá ô mã', [k.S.CO.dd.buoc, k.S.CO.dd.ma], ['nut', '']);
  v.loiGui = 'khong_gui_duoc';
  await k.guiMaDonDau();
  dung('câu web, không nhắc thu ngân', /thử lại sau ít phút/.test(k.S.CO.dd.loi) && !/thu ngân/.test(k.S.CO.dd.loi));
  la('vẫn bước đầu', k.S.CO.dd.buoc, 'nut');
  v.loiGui = 'gui_qua_nhieu';
  await k.guiMaDonDau();
  la('câu gửi quá nhiều', k.S.CO.dd.loi, 'Đã gửi nhiều mã. Chờ 30 phút rồi thử lại.');
});

await ca('v645 đơn đầu: tiền bánh dưới 300.000 nói còn thiếu; mã lớn hơn thì thẻ nói máy giữ mã; mã nhỏ hơn bị thay và nói rõ; máy chủ cũ không trả thẻ thì không hiện gì', async () => {
  const a = mayChuDonDau({tien: 'thieu'});
  const m1 = moiTruong('2026-11-08T08:00:00', a.mang);
  const k1 = taoKho(m1.mt);
  coThem(k1); k1.S.f.phone = '0931224334'; k1.moGio(); await m1.chayHen();
  la('gợi ý', k1.theDonDau.value.kieu, 'goi_y');
  dung('nêu ngưỡng 300.000', k1.theDonDau.value.phu.includes('300.000'));

  const b = mayChuDonDau({maGiam: 90000}); b.v.phien = '0931224334';
  const m2 = moiTruong('2026-11-08T08:00:00', b.mang);
  const k2 = taoKho(m2.mt);
  coThem(k2); k2.S.f.phone = '0931224334'; k2.moGio(); await m2.chayHen();
  k2.S.f.ma = 'vip90'; k2.apMaUuDai(); await m2.chayHen();
  la('mã 90.000 giữ', k2.giam.value, 90000);
  la('thẻ nói mã đang lớn hơn', k2.theDonDau.value.kieu, 'goi_y');
  dung('tiêu đề', /nhiều hơn/.test(k2.theDonDau.value.tieu));

  const c = mayChuDonDau({maGiam: 30000}); c.v.phien = '0931224334';
  const m3 = moiTruong('2026-11-08T08:00:00', c.mang);
  const k3 = taoKho(m3.mt);
  coThem(k3); k3.S.f.phone = '0931224334'; k3.moGio(); await m3.chayHen();
  k3.S.f.ma = 'GIAM30'; k3.apMaUuDai(); await m3.chayHen();
  la('đơn đầu thắng', k3.giam.value, 50000);
  dung('nói rõ không cộng', k3.theDonDau.value.kieu === 'da_ap' && /không cộng/.test(k3.theDonDau.value.phu));

  const m4 = moiTruong('2026-11-08T08:00:00', {'vagabond.don_hang.xem_uu_dai': () => ({ok: 1, giam: 0, ap: []})});
  const k4 = taoKho(m4.mt);
  coThem(k4); k4.S.f.phone = '0931224334'; k4.moGio(); await m4.chayHen();
  la('không thẻ', k4.theDonDau.value, null);
});

/* Anh Việt 08/11 (bản 2): màn Khuyến mãi chọn không bắt mã Zalo, mức giảm
   khác 50.000, và có hay không hiện thẻ ở bước thanh toán. Phần don_dau dựng
   bằng ĐÚNG don_dau_web.phan_hoi của máy chủ (python), không chép tay. */
const DD_MAY = JSON.parse(execFileSync('python3', ['-B', '-c', `
import json, sys
sys.path.insert(0, sys.argv[1])
from vagabond.khung.kiem_thu import nen
nen.gia_lap()
from vagabond import don_dau_web as dd
ch = {"giam": 30000, "toi_thieu": 200000, "can_otp": 0}
print(json.dumps({"hien": dd.phan_hoi(dd.DU, dict(ch, hien_thanh_toan=1)),
  "an": dd.phan_hoi(dd.DU, dict(ch, hien_thanh_toan=0)),
  "otp_an": dd.phan_hoi(dd.CAN_XAC_THUC, {"can_otp": 1, "hien_thanh_toan": 0})}))
`, GOC_REPO]).toString());
function mayChuKhongOtp(dd) {
  const v = {hoi: [], gui: []};
  return {v, mang: {
    'vagabond.don_hang.xem_uu_dai': th => { v.hoi.push(JSON.parse(th.don));
      return {ok: 1, giam: 30000, ap: [{ten: 'Ưu đãi đơn đầu tiên trên web', giam: 30000}], don_dau: {...dd, ap_dung: 1, bo_ma: 0}}; },
    'vagabond.thanh_vien.gui_ma': th => { v.gui.push(th); return {ok: 1}; },
  }};
}
await ca('v645 bản 2: không bắt mã Zalo thì thẻ Đã giảm ngay, không nút gửi mã, không nhắc xác thực; biểu tượng theo mức giảm (-30K)', async () => {
  la('máy chủ gửi cờ', [DD_MAY.hien.can_otp, DD_MAY.hien.hien, DD_MAY.hien.giam], [0, 1, 30000]);
  const {v, mang} = mayChuKhongOtp(DD_MAY.hien);
  const {mt, chayHen} = moiTruong('2026-11-08T08:00:00', mang);
  const k = taoKho(mt);
  coThem(k); k.S.f.phone = '0931224334'; k.moGio(); await chayHen();
  const th = k.theDonDau.value;
  la('thẻ đã giảm', th && th.kieu, 'da_ap');
  la('biểu tượng', th.ic, '-30K');
  dung('nói số, không nhắc xác thực: ' + th.phu, th.phu.includes('0931224334') && !/xác thực/i.test(th.phu));
  dung('tiêu đề theo mức giảm', th.tieu.includes('30.000'));
  la('tổng trừ 30.000', k.giam.value, 30000);
  la('không gửi mã nào', v.gui.length, 0);
});
await ca('v645 bản 2: Khuyến mãi tắt "hiện ở bước thanh toán" thì không có thẻ nhưng tổng vẫn trừ; bắt mã Zalo thì máy chủ luôn bật lại thẻ', async () => {
  la('máy chủ: tắt thẻ', DD_MAY.an.hien, 0);
  const {mang} = mayChuKhongOtp(DD_MAY.an);
  const {mt, chayHen} = moiTruong('2026-11-08T08:00:00', mang);
  const k = taoKho(mt);
  coThem(k); k.S.f.phone = '0931224334'; k.moGio(); await chayHen();
  la('không thẻ', k.theDonDau.value, null);
  la('tổng vẫn trừ', k.giam.value, 30000);
  la('bắt mã Zalo: thẻ luôn hiện', DD_MAY.otp_an.hien, 1);
});

/* v646 Refill (anh Việt duyệt 09/11): tab Đặt trước dựng bằng kiem_banh._dat_truoc_theo_decor
   THẬT (thu_refill_646.du_lieu_web, Frappe giả), không chép tay hình dạng. */
const RF_MAY = JSON.parse(execFileSync('python3', ['-B', '-c', `
import json, sys
sys.path.insert(0, sys.argv[1])
from vagabond.khung.kiem_thu import nen
nen.gia_lap()
from vagabond.khung.kiem_thu import thu_refill_646 as t
print(json.dumps(t.du_lieu_web(), ensure_ascii=False, default=str))
`, GOC_REPO]).toString());

await ca('Codex #594: giỏ lưu bánh đặt trước nhận ngày kia (12/11), mở lại khi số tồn về chậm: giữ ngày 12/11 suốt lúc chờ và sau khi số về (con_xa 3); số về mà ngày đó hết thì mới dời', async () => {
  const doi = [];
  const tra = () => new Promise(r => doi.push(r));
  const a = moiTruong('2026-11-10T08:00:00', {'vagabond.kiem_banh.co_the_ban_hom_nay': () => ({banh: {}, nhom: [], dat_truoc: RF_MAY})});
  const k = taoKho(a.mt);
  k.phucHoiGio(); await k.napTon();
  k.S.tab = 'order'; coThem(k, 'Kankin'); k.pick(2); k.pickSlot(6);
  la('ngày đã chọn', k.S.ngayChon, '2026-11-12');
  /* Mở lại: máy chủ trả số chậm. */
  const cham = moiTruong('2026-11-10T08:00:00', {'vagabond.kiem_banh.co_the_ban_hom_nay': tra});
  cham.kho.set('vgb-gio-v1', a.kho.get('vgb-gio-v1'));
  const k2 = taoKho(cham.mt);
  k2.phucHoiGio();
  const dang = k2.napTon();
  la('đang chờ số: giữ 12/11', k2.S.ngayChon, '2026-11-12');
  dung('bản lưu không bị ghi đè sang ngày khác', JSON.parse(cham.kho.get('vgb-gio-v1')).ngay === '2026-11-12');
  doi.shift()({banh: {}, nhom: [], dat_truoc: RF_MAY}); await dang;
  la('số về, ngày kia còn 3: vẫn 12/11', [k2.S.ngayChon, k2.S.CART.map(o => o.id)], ['2026-11-12', ['BAWC00123']]);
  /* Số về mà ngày kia đã hết: lúc đó mới dời và nhờ khách chọn lại. */
  const het = JSON.parse(JSON.stringify(RF_MAY));
  het.nhom.forEach(g => g.sizes.forEach(y => { if (y.ma === 'BAWC00123') y.con_xa = 0; }));
  const c3 = moiTruong('2026-11-10T08:00:00', {'vagabond.kiem_banh.co_the_ban_hom_nay': tra});
  c3.kho.set('vgb-gio-v1', a.kho.get('vgb-gio-v1'));
  const k3 = taoKho(c3.mt);
  k3.phucHoiGio();
  const d3 = k3.napTon();
  la('chờ số: giữ', k3.S.ngayChon, '2026-11-12');
  doi.shift()({banh: {}, nhom: [], dat_truoc: het}); await d3;
  dung('ngày kia hết: dời khỏi 12/11 và bỏ cờ đã chọn ngày', k3.S.ngayChon !== '2026-11-12' && k3.S.daChonNgay === false);
});

await ca('Codex #594 vòng 2: khách chọn 14/11 thuộc mẻ refill (Đủ decor lúc đó 0, ngày mai còn 1); lần làm tươi sau mẻ đã đủ đơn nhưng Đủ decor còn 5: giữ 14/11, không dời giữa lúc đang gán bảng số', async () => {
  let lan = 0;
  /* Ngày mai (13/11) còn 1 theo phiếu, nên giữa chừng có chỗ để dời sai. */
  const dau = JSON.parse(JSON.stringify(RF_MAY));
  dau.nhom.forEach(g => g.sizes.forEach(y => { if (y.ma === 'BAWC00068') y.con_mai = 1; }));
  const day = JSON.parse(JSON.stringify(dau));
  day.nhom.forEach(g => g.sizes.forEach(y => { if (y.ma === 'BAWC00068') { delete y.refill; y.con = 5; y.con_xa = 5; } }));
  const a = moiTruong('2026-11-12T08:00:00', {'vagabond.kiem_banh.co_the_ban_hom_nay': () => ({banh: {}, nhom: [], dat_truoc: lan++ ? day : dau})});
  const k = taoKho(a.mt);
  k.phucHoiGio(); await k.napTon();
  k.S.tab = 'order'; coThem(k, 'Roman de la Rose'); k.pick(2); k.pickSlot(6);
  la('chọn 14/11 trong mẻ', k.S.ngayChon, '2026-11-14');
  await k.napTon();
  la('mẻ đủ đơn, BTP sẵn còn 5 (v677): vẫn 14/11', [k.S.ngayChon, k.S.TRUOC_XA.BAWC00068], ['2026-11-14', 5]);
  dung('nháp lưu vẫn 14/11', JSON.parse(a.kho.get('vgb-gio-v1')).ngay === '2026-11-14');
});

await ca('v646 refill: bánh chỉ có mẻ refill hiện "Có từ 14/11"; giỏ có bánh đó thì lịch mờ ngày ngoài 14/11 tới 20/11, bấm ngày mờ thì báo và không đổi ngày', async () => {
  const {mt} = moiTruong('2026-11-10T08:00:00', {'vagabond.kiem_banh.co_the_ban_hom_nay': () => ({banh: {}, nhom: [], dat_truoc: RF_MAY})});
  const k = taoKho(mt);
  await k.napTon();
  k.S.tab = 'order';  /* khách bấm tab Đặt trước */
  la('số còn nhận', [k.S.TRUOC.BAWC00068, k.S.TRUOC.BAWC00123], [13, 3]);
  la('nhãn refill', [k.nhanRefill('BAWC00068'), k.nhanRefill('BAWC00123')], ['Có từ 14/11', '']);
  la('giỏ trống: không ngày nào mờ', k.ngayRail.value.filter(d => d.off).length, 0);
  /* v675 (Sales nhắn 19/11/2026, giám đốc chốt nhận tới 3 ngày tới): ngày mai theo
     phiếu Kiểm bánh ngày mai, ngày kia và ngày thứ ba theo BTP sẵn (v677; Kankin: BTP
     6 trừ 2 đơn ngày mai còn 4, Đủ decor 5 không tính). Lịch tab Đặt trước: ba ngày
     tới và các ngày của mẻ refill. */
  la('số ngày mai và ngày kia của Kankin', [k.S.TRUOC_MAI.BAWC00123, k.S.TRUOC_XA.BAWC00123], [3, 4]);
  la('lịch tab Đặt trước: ba ngày tới và 14 tới 20/11 của mẻ', k.ngayRailDatTruoc.value.map(d => d.i), [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
  coThem(k, 'Kankin');
  la('giỏ có bánh đặt trước thường: còn ba ngày tới', k.ngayRail.value.filter(d => d.off).map(d => d.i), [0, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]);
  k.pick(5);
  dung('bấm ngày xa: báo nhận trong 3 ngày tới', /trong 3 ngày tới/.test(k.S.toast.chu));
  /* Thêm bánh chỉ có mẻ 14 tới 20/11 vào giỏ đang có bánh nhận ngày mai: không có
     ngày chung, báo đặt đơn riêng, không thêm. */
  const dai = k.S.CART.length;
  k.moBanh(k.S.CAKES.find(c => c.k === 'Roman de la Rose')); k.S.soLuong = 1;
  la('không thêm được', k.addToCart(), false);
  dung('báo không có chung ngày', /không có chung ngày nhận/.test(k.S.toast.chu));
  la('giỏ giữ nguyên', k.S.CART.length, dai);
  k.S.CART.splice(0);
  coThem(k, 'Roman de la Rose');
  la('giỏ chỉ có bánh của mẻ: mờ 10 tới 13/11 và 21 tới 23/11', k.ngayRail.value.filter(d => d.off).map(d => d.i), [0, 1, 2, 3, 11, 12, 13]);
  const truoc = k.S.ngayChon;
  k.pick(1);
  la('không đổi ngày', k.S.ngayChon, truoc);
  dung('báo khách khoảng ngày', /từ 14\/11 tới 20\/11/.test(k.S.toast.chu));
  k.pick(5);
  la('chọn được 15/11', k.S.ngayChon, '2026-11-15');
});

/* v675 ca gốc (Sales báo 19/11/2026): Tira-Missing-U 12cm, đợt refill 17 tới 23/11 đã nhận đủ đơn,
   đợt 24 tới 30/11 còn 10, phiếu ngày mai 20/11 Còn bán 2, Đủ decor 6. Dựng THẬT từ máy chủ. */
const TIRA_MAY = JSON.parse(execFileSync('python3', ['-B', '-c', `
import json, sys
sys.path.insert(0, sys.argv[1])
from vagabond.khung.kiem_thu import nen
nen.gia_lap()
from vagabond.khung.kiem_thu import thu_refill_du_don_675 as t
print(json.dumps(t.du_lieu_web(), ensure_ascii=False, default=str))
`, GOC_REPO]).toString());

await ca('v675 ca gốc: đợt refill đủ đơn thì ngày mai 20/11 đặt được theo phiếu (tối đa 2), ngày kia theo Đủ decor (tối đa 6), ngày 23/11 mờ, 24/11 theo đợt còn nhận', async () => {
  const {mt} = moiTruong('2026-11-19T08:00:00', {'vagabond.kiem_banh.co_the_ban_hom_nay': () => ({banh: {}, nhom: [], dat_truoc: TIRA_MAY})});
  const k = taoKho(mt);
  await k.napTon();
  k.S.tab = 'order';
  k.pick(1);
  la('chọn được ngày mai 20/11', k.S.ngayChon, '2026-11-20');
  const banh = k.S.CAKES.find(c => c.sizes.some(z => z.id === 'BAWC00077'));
  k.moBanh(banh); k.S.curSizeId = 'BAWC00077'; k.S.soLuong = 3;
  la('ngày mai đặt 3: chặn (còn 2)', k.addToCart(), false);
  dung('báo còn 2', /chỉ còn nhận 2/.test(k.S.toast.chu));
  k.S.soLuong = 1;
  la('ngày mai đặt 1: thêm được', k.addToCart(), 'them');
  la('giỏ: 20 tới 22/11 mở, 23/11 mờ, 24 tới 30/11 theo đợt 2, sau đó mờ', k.ngayRail.value.filter(d => d.off).map(d => d.i), [0, 4, 12, 13]);
  k.pick(2);
  la('ngày kia 21/11 chọn được', k.S.ngayChon, '2026-11-21');
  for (let j = 0; j < 9; j++) k.cartQty(0, 1);
  la('ngày kia: bấm + tới tối đa 6 theo Đủ decor', k.S.CART[0].qty, 6);
  const truoc = k.S.ngayChon;
  k.pick(4);
  la('23/11 không đổi ngày', k.S.ngayChon, truoc);
});

await ca('v677 (Codex, anh Việt 19/11): thẻ bánh, cỡ và giới hạn giỏ cùng ghi số của ĐÚNG ngày nhận đang chọn; ngày mai hết theo phiếu thì ghi "hết ngày", không lấy số ngày kia hay số đợt', async () => {
  /* Tira-Missing-U 12cm dựng thật từ máy chủ, phiếu ngày mai 20/11 hết (0): ngày kia, ngày thứ ba
     còn 6 theo BTP sẵn, đợt 24 tới 30/11 còn 10. Bản cũ: thẻ ghi số dương đầu tiên (6) cho mọi ngày. */
  const may = JSON.parse(JSON.stringify(TIRA_MAY));
  may.nhom.forEach(g => g.sizes.forEach(y => { if (y.ma === 'BAWC00077') { y.con_mai = 0; y.con = 6; } }));
  const {mt} = moiTruong('2026-11-19T08:00:00', {'vagabond.kiem_banh.co_the_ban_hom_nay': () => ({banh: {}, nhom: [], dat_truoc: may})});
  const k = taoKho(mt);
  await k.napTon();
  k.S.tab = 'order';
  const banh = k.S.CAKES.find(c => c.sizes.some(z => z.id === 'BAWC00077'));
  const chip = () => k.theBanh(banh, 'order').chips.find(x => /^12cm/.test(x.chu));
  k.pick(1);
  la('20/11: số của ngày mai là 0', k.soDatTruoc('BAWC00077'), 0);
  la('20/11: chip ghi hết ngày, không sáng', [chip().chu, chip().co], ['12cm · hết ngày 20/11', false]);
  k.pick(2);
  la('21/11: theo BTP sẵn 6', [k.soDatTruoc('BAWC00077'), k.gioiHanNhan('BAWC00077', 'order')], [6, 6]);
  la('21/11: chip ghi 6', [chip().chu, chip().co], ['12cm · Chỉ còn 6 bánh', true]);
  k.pick(6);
  la('25/11: theo đợt 24 tới 30/11', [k.soDatTruoc('BAWC00077'), k.gioiHanNhan('BAWC00077', 'order')], [10, 10]);
  dung('25/11: chip ghi 10', /12cm · .*10 bánh/.test(chip().chu));
  k.S.tab = 'today';
  la('tab Có sẵn hôm nay: giới hạn theo tủ, không theo ngày đặt trước', k.gioiHanNhan('BAWC00077', 'today'), 0);
});

await ca('#463 (Codex, anh Việt 20/11): ngày đã xác nhận mà cỡ bánh hết ngày đó thì cả nút + trên thẻ và Thêm vào giỏ đều báo hết, GIỮ ngày và giỏ; khách tự chọn ngày còn bánh thì thêm được; sửa món trong giỏ không đổi ngày', async () => {
  /* Tira-Missing-U 12cm: phiếu ngày mai 20/11 hết (0), ngày kia 21/11 còn 6 theo BTP sẵn.
     Bản cũ: hai nút vẫn thêm rồi tự dời ngày nhận sang 21/11. Không đổi luật tồn. */
  const may = JSON.parse(JSON.stringify(TIRA_MAY));
  may.nhom.forEach(g => g.sizes.forEach(y => { if (y.ma === 'BAWC00077') { y.con_mai = 0; y.con = 6; } }));
  /* Bánh khác còn cả hai ngày, để thử giỏ đã có món. */
  may.nhom.push({...may.nhom[0], ten: 'Bánh còn hai ngày', sizes: [{ma: 'BAWC09001', cm: 16, gia: 600000, con: 3, con_mai: 3, con_xa: 3}]});
  const dung1 = async () => {
    const {mt} = moiTruong('2026-11-19T08:00:00', {'vagabond.kiem_banh.co_the_ban_hom_nay': () => ({banh: {}, nhom: [], dat_truoc: may})});
    const k = taoKho(mt); await k.napTon(); k.S.tab = 'order'; return k;
  };
  const tira = k => k.S.CAKES.find(c => c.sizes.some(z => z.id === 'BAWC00077'));
  for (const coSan of [false, true]) {
    const k = await dung1();
    if (coSan) { k.S.CART.push({k: 'Bánh còn hai ngày', id: 'BAWC09001', cm: 16, price: 600000, nguon: 'order', wish: '', adds: [], qty: 1}); }
    k.pick(1);
    la((coSan ? 'giỏ có món' : 'giỏ trống') + ': đã xác nhận 20/11', [k.S.ngayChon, k.S.daChonNgay], ['2026-11-20', true]);
    const gio = JSON.stringify(k.S.CART);
    /* Nút Thêm vào giỏ trong chi tiết. */
    k.moBanh(tira(k)); k.S.curSizeId = 'BAWC00077'; k.S.soLuong = 1;
    la('chi tiết: không thêm', k.addToCart(), false);
    dung('chi tiết: báo hết ngày 20/11, chỉ chọn ngày khác: ' + k.S.toast.chu, /hết ngày 20\/11/.test(k.S.toast.chu));
    la('chi tiết: giữ ngày và giỏ', [k.S.ngayChon, k.S.daChonNgay, JSON.stringify(k.S.CART)], ['2026-11-20', true, gio]);
    /* Nút + trên thẻ (bánh một cỡ đang bán thì thêm thẳng). */
    const c1 = {...tira(k), sizes: tira(k).sizes.filter(z => z.id === 'BAWC00077')};
    k.S.toast.chu = '';
    la('nút +: không thêm', k.themNhanh(c1, 'order'), 'chan');
    dung('nút +: báo hết ngày 20/11', /hết ngày 20\/11/.test(k.S.toast.chu));
    la('nút +: giữ ngày và giỏ', [k.S.ngayChon, JSON.stringify(k.S.CART)], ['2026-11-20', gio]);
    /* Khách tự chọn 21/11: thêm được, ngày là 21/11. */
    k.pick(2);
    k.moBanh(tira(k)); k.S.curSizeId = 'BAWC00077'; k.S.soLuong = 1;
    la('chọn 21/11 rồi thêm được', [k.addToCart(), k.S.ngayChon], ['them', '2026-11-21']);
  }
  /* Khách CHƯA xác nhận ngày (ngày do hệ thống đặt, ví dụ giỏ lưu hôm trước): luật
     này không chặn, giữ như cũ (lịch vẫn chờ khách xác nhận trước khi gửi đơn). */
  const k0 = await dung1();
  k0.pick(1); k0.S.daChonNgay = false;
  k0.moBanh(tira(k0)); k0.S.curSizeId = 'BAWC00077'; k0.S.soLuong = 1;
  la('chưa xác nhận ngày: không chặn, lịch chờ xác nhận', [k0.addToCart(), k0.S.daChonNgay], ['them', false]);
  /* Sửa món từ giỏ: còn bánh ngày đang chọn thì lưu, không đổi ngày. */
  const k = await dung1();
  k.pick(2);
  k.moBanh(tira(k)); k.S.curSizeId = 'BAWC00077'; k.S.soLuong = 1; k.addToCart();
  k.suaDongGio(0); k.S.soLuong = 2;
  la('sửa món trong giỏ: lưu, giữ 21/11', [k.addToCart(), k.S.ngayChon, k.S.CART[0].qty], ['sua', '2026-11-21', 2]);
  /* Cùng loại (H2): số còn của ngày đã chọn về 0 khi bánh đã trong giỏ thì nút + trong giỏ báo hết, không tăng. */
  k.S.TRUOC_XA.BAWC00077 = 0;
  k.cartQty(0, 1);
  la('nút + trong giỏ: không tăng, báo hết ngày 21/11', [k.S.CART[0].qty, /hết ngày 21\/11/.test(k.S.toast.chu), k.S.ngayChon], [2, true, '2026-11-21']);
});

await ca('v675 thêm bánh Có sẵn hôm nay: ngày nhận về HÔM NAY với khung giờ gần nhất (trước: giữ ngày kia mặc định); đã tự chọn ngày thì giữ; hôm nay hết giờ thì báo, không tự nhảy ngày', async () => {
  const {mt} = moiTruong('2026-11-19T08:00:00');
  const k = taoKho(mt);
  k.S.TODAY = {BAWC00139: 3, BAWC00140: 2}; k.S.tab = 'today';
  la('giỏ trống: ngày mặc định là ngày kia', k.picked.value, 2);
  la('thêm bánh hôm nay', coThem(k), 'them');
  la('ngày nhận về hôm nay 19/11', [k.picked.value, k.S.ngayChon], [0, '2026-11-19']);
  dung('khung giờ còn nhận hôm nay', k.slotOk(0, k.slotDangChon.value));
  la('dòng chốt trên nút gửi: đúng ngày', /19\/11/.test(k.chotDon.value.ngay), true);
  /* Quý khách đã tự chọn ngày mai rồi mới thêm bánh: giữ ngày đã chọn. */
  const a = moiTruong('2026-11-19T08:00:00'); const k2 = taoKho(a.mt);
  k2.S.TODAY = {BAWC00139: 3}; k2.S.tab = 'today';
  k2.pick(1);
  coThem(k2);
  la('đã tự chọn ngày mai: giữ', k2.S.ngayChon, '2026-11-20');
  /* 22 giờ: hôm nay hết khung giờ nhận. */
  const b = moiTruong('2026-11-19T22:00:00'); const k3 = taoKho(b.mt);
  k3.S.TODAY = {BAWC00139: 3}; k3.S.tab = 'today';
  const truoc = k3.picked.value;
  coThem(k3);
  la('hết giờ: không tự nhảy ngày', k3.picked.value, truoc);
  dung('báo hết khung giờ và mở lịch', /hết khung giờ nhận/.test(k3.S.toast.chu) && k3.S.moLich === true);
});

await ca('v675 miễn phí giao trong bán kính 7 km: đơn đủ 1 triệu ở 3 km miễn phí, ở 9 km tính phí và nói rõ lý do; không giới hạn (0) thì như cũ; thẻ hôm nay nhiều cỡ ghi "từ"', async () => {
  const {mt} = moiTruong('2026-11-19T08:00:00');
  const k = taoKho(mt);
  k.S.mienPhiTu = 1000000; k.S.mienPhiKm = 7; k.S.tab = 'order';
  k.S.CART.push({k: 'CANDLE', id: 'BAWC00139', cm: 12, price: 1200000, nguon: 'order', wish: '', adds: [], qty: 1});
  la('Codex #594: chưa có địa chỉ thì chưa hứa miễn phí', k.mienPhi.value, false);
  dung('chỉ nêu điều kiện, không nói đơn này được miễn', /Miễn phí giao cho đơn từ .* trong bán kính 7 km/.test(k.dongMienPhi.value) && !/Đơn này được miễn phí/.test(k.dongMienPhi.value));
  k.apPhiGiao({ok: 0, ly_do: 'khong_tim_thay_dia_chi'}, 'chinh_xac');
  la('không định vị được địa chỉ: không hứa miễn phí, phí chưa rõ', [k.mienPhi.value, k.S.CO.ship, k.S.CO.shipTrangThai], [false, null, 'chua_ro']);
  k.S.CO.mode = 'pick';
  la('tự lấy không cần khoảng cách', k.tong.value.tt.phi, 0);
  k.S.CO.mode = 'ship';
  k.apPhiGiao({ok: 1, total_fee: 42000, km_thang: 3.2, diem_lay: 'bep'}, 'chinh_xac');
  la('3,2 km: miễn phí', k.mienPhi.value, true);
  k.apPhiGiao({ok: 1, total_fee: 42000, km_thang: 9.1, diem_lay: 'bep'}, 'chinh_xac');
  la('9,1 km: tính phí', [k.mienPhi.value, k.S.CO.ship], [false, 42000]);
  dung('nói rõ ngoài bán kính 7 km', /ngoài bán kính 7 km/.test(k.dongMienPhi.value));
  k.S.mienPhiKm = 0;
  la('không giới hạn bán kính: 9,1 km vẫn miễn', k.mienPhi.value, true);
  la('phép thuần', [k.T.trongKmMienPhi(7, 7), k.T.trongKmMienPhi(7.01, 7), k.T.trongKmMienPhi(null, 7), k.T.trongKmMienPhi(50, 0)], [true, false, true, true]);
  k.S.TODAY = {BAWC00139: 3, BAWC00140: 2};
  const c = k.S.CAKES.find(x => x.k === 'CANDLE');
  dung('thẻ hôm nay hai cỡ khác giá: ghi từ', /^từ /.test(k.theBanh(c, 'today').gia));
  k.S.TODAY = {BAWC00139: 3};
  dung('một cỡ: không ghi từ', !/^từ /.test(k.theBanh(c, 'today').gia));
});

/* v660 (Loan Anh, bếp báo 15/11/2026): một bánh HAI đợt refill, 14/11 tới 17/11 (20 bánh) và 20/11 tới 23/11
   (9 bánh), dựng THẬT từ máy chủ. */
const RF2_MAY = JSON.parse(execFileSync('python3', ['-B', '-c', `
import json, sys
sys.path.insert(0, sys.argv[1])
from vagabond.khung.kiem_thu import nen
nen.gia_lap()
from vagabond.khung.kiem_thu import thu_refill_646 as t
t.ROMAN = dict(t.ROMAN, so_refill=0, refill_tu=None, refill_den=None, refill_dot=json.dumps([
	{"id": "d1", "so": 20, "tu": "2026-11-14", "den": "2026-11-17"}, {"id": "d2", "so": 9, "tu": "2026-11-20", "den": "2026-11-23"}]))
print(json.dumps(t.du_lieu_web(), ensure_ascii=False, default=str))
`, GOC_REPO]).toString());

await ca('v660 refill nhiều đợt: lịch chỉ mở ngày thuộc MỘT trong hai đợt, ngày giữa hai đợt mờ và báo đủ hai khoảng; số được đặt lấy theo đúng đợt chứa ngày nhận', async () => {
  const {mt} = moiTruong('2026-11-10T08:00:00', {'vagabond.kiem_banh.co_the_ban_hom_nay': () => ({banh: {}, nhom: [], dat_truoc: RF2_MAY})});
  const k = taoKho(mt);
  await k.napTon();
  k.S.tab = 'order';
  coThem(k, 'Roman de la Rose');
  /* Hôm nay 10/11 là ô 0. Mở: 14 tới 17/11 (ô 4 tới 7) và 20 tới 23/11 (ô 10 tới 13). */
  la('ngày mờ', k.ngayRail.value.filter(d => d.off).map(d => d.i), [0, 1, 2, 3, 8, 9]);
  const truoc = k.S.ngayChon;
  k.pick(8);
  la('ngày 18/11 giữa hai đợt: không đổi ngày', k.S.ngayChon, truoc);
  dung('báo đủ hai khoảng', /từ 14\/11 tới 17\/11 hoặc từ 20\/11 tới 23\/11/.test(k.S.toast.chu));
  k.pick(5);
  la('15/11 thuộc đợt 1: giới hạn theo số còn của đợt 1 (20 trừ 6 đơn giao 14 tới 17/11)', [k.S.ngayChon, k.gioiHanNhan('BAWC00068')], ['2026-11-15', 14]);
  k.pick(11);
  la('21/11 thuộc đợt 2: giới hạn theo số còn của đợt 2 (9 trừ 1 đơn giao 20/11)', [k.S.ngayChon, k.gioiHanNhan('BAWC00068')], ['2026-11-21', 8]);
});

/* Codex 549 (1eefda8): Kankin vừa còn decor 3 vừa có mẻ refill 15 (14/11 tới 20/11), dựng THẬT từ máy chủ. */
const RF_HAI = JSON.parse(execFileSync('python3', ['-B', '-c', `
import json, sys
sys.path.insert(0, sys.argv[1])
from vagabond.khung.kiem_thu import nen
nen.gia_lap()
from vagabond.khung.kiem_thu import thu_refill_646 as t
kk = dict(t.KANKIN, so_refill=15, refill_tu=t.D8(2026, 11, 14), refill_den=t.D8(2026, 11, 20))
print(json.dumps(t.du_lieu_web(kankin=kk), ensure_ascii=False, default=str))
`, GOC_REPO]).toString());

await ca('Codex 549 (1eefda8): bánh vừa còn decor vừa có refill: ngày nhận trong khoảng refill thì giới hạn theo refill (15), ngoài khoảng theo decor (3)', async () => {
  const {mt} = moiTruong('2026-11-10T08:00:00', {'vagabond.kiem_banh.co_the_ban_hom_nay': () => ({banh: {}, nhom: [], dat_truoc: RF_HAI})});
  const k = taoKho(mt);
  await k.napTon();
  k.S.tab = 'order';
  la('máy chủ trả cả hai số', [k.S.TRUOC.BAWC00123, (k.S.TRUOC_RF.BAWC00123 || {}).con], [3, 15]);
  k.pick(5);
  la('chọn 15/11', k.S.ngayChon, '2026-11-15');
  la('giới hạn ngày 15/11 theo refill', k.gioiHanNhan('BAWC00123'), 15);
  k.moBanh(k.S.CAKES.find(c => c.k === 'Kankin')); k.S.soLuong = 5;
  la('thêm 5 bánh ngày 15/11 được (trước: chặn ở 3)', k.addToCart(), 'them');
  k.pick(1);
  la('ngày 11/11 ngoài khoảng: giới hạn theo decor', k.gioiHanNhan('BAWC00123'), 3);
});

await ca('Codex 549 (1eefda8): bánh có sẵn hôm nay thêm từ tab Hôm nay không bị khoá ngày vì mẻ refill tương lai', async () => {
  const {mt} = moiTruong('2026-11-10T08:00:00', {'vagabond.kiem_banh.co_the_ban_hom_nay': () => ({banh: {BAWC00068: 4}, nhom: [], dat_truoc: RF_MAY})});
  const k = taoKho(mt);
  await k.napTon();
  k.S.tab = 'today';
  la('thêm Roman từ tab Hôm nay', coThem(k, 'Roman de la Rose'), 'them');
  la('dòng giỏ lấy bánh hôm nay', k.S.CART[0].nguon, 'today');
  la('không ngày nào mờ (trước: mờ 10 tới 13/11)', k.ngayRail.value.filter(d => d.off).length, 0);
  k.pick(0);
  la('chọn được hôm nay 10/11', k.S.ngayChon, '2026-11-10');
  /* Codex 549 (58ba797): số lượng cũng theo bánh có sẵn hôm nay (4), không theo mẻ refill (13). */
  la('giới hạn dòng hôm nay theo số có sẵn', k.gioiHanNhan('BAWC00068', 'today'), 4);
  k.moBanh(k.S.CAKES.find(c => c.k === 'Roman de la Rose')); k.S.soLuong = 4;
  la('đã có 1, thêm 4 nữa vượt 4 có sẵn thì chặn', k.addToCart(), false);
});

await ca('Codex 549 (58ba797): mẻ refill chỉ còn 1 không chặn khách mua 2 bánh có sẵn hôm nay', async () => {
  const rf1 = JSON.parse(JSON.stringify(RF_MAY));
  rf1.nhom.forEach(g => g.sizes.forEach(z => { if (z.refill) { z.refill.con = 1; z.con = 1; } }));
  const {mt} = moiTruong('2026-11-10T08:00:00', {'vagabond.kiem_banh.co_the_ban_hom_nay': () => ({banh: {BAWC00068: 4}, nhom: [], dat_truoc: rf1})});
  const k = taoKho(mt);
  await k.napTon();
  k.S.tab = 'today';
  k.moBanh(k.S.CAKES.find(c => c.k === 'Roman de la Rose')); k.S.soLuong = 2;
  la('thêm 2 bánh hôm nay được (trước: chặn ở 1)', k.addToCart(), 'them');
  la('nút + trong giỏ còn tăng được tới 4', (k.cartQty(0, 1), k.S.CART[0].qty), 3);
});

await ca('v652 điểm thành viên: số chưa xác thực thì thẻ mời xác thực; xác thực rồi thẻ báo số điểm dùng được; bấm Dùng điểm thì hỏi lại máy chủ kèm dung_diem, tổng trừ điểm nhưng vẫn miễn phí giao theo tiền trước điểm; gửi đơn mang dung_diem; máy chủ báo diem_doi thì bỏ chọn và hỏi lại', async () => {
  let co = false, diemDoi = false;
  const hoi = [], gui = [];
  const {mt, chayHen} = moiTruong('2026-10-11T08:00:00', {
    'vagabond.don_hang.xem_uu_dai': th => {
      const d = JSON.parse(th.don); hoi.push(d);
      if (!co) return {ok: true, giam: 0, ap: [], diem: {trang_thai: 'can_xac_thuc', so_du: 0, toi_da: 0, tien_toi_da: 0, dung: 0, tien: 0}};
      const tien = d.dung_diem ? 400000 : 0;
      return {ok: true, giam: tien, ap: tien ? [{ten: 'Điểm thành viên', giam: tien}] : [],
        diem: {trang_thai: 'dung_duoc', so_du: 900000, toi_da: 400000, tien_toi_da: 400000, dung: d.dung_diem ? 400000 : 0, tien,
          len_hang: {con_thieu: 2500000, hang_tiep: 'AMBASSADOR', so_thang: 12}}};
    },
    'vagabond.don_hang.tao_don': th => { const d = JSON.parse(th.don); gui.push(d); return diemDoi ? {ok: 0, ly_do: 'diem_doi'} : {ok: 1, duong_dan: '/banh/xong/t'}; }
  });
  const k = taoKho(mt);
  coThem(k); k.pick(3); k.pickSlot(6);
  Object.assign(k.S.f, {name: 'Lan', phone: '0931224334', addr: '12 Nguyễn Huệ Q1'}); k.S.CO.dongy = true;
  await k.xemUuDai(); await chayHen();
  la('chưa xác thực: thẻ mời, không số dư', [k.theDiem.value && k.theDiem.value.kieu, /\d{3}\.\d{3} điểm/.test(JSON.stringify(k.theDiem.value))], ['xac_thuc', false]);
  co = true; k.S.CO.uu = null; await k.xemUuDai(); await chayHen();
  la('xác thực rồi: báo dùng được', k.theDiem.value.kieu, 'dung');
  dung('câu số điểm và tiền', k.theDiem.value.phu.indexOf('400.000') >= 0 && k.theDiem.value.tieu.indexOf('900.000') >= 0);
  dung('dòng lên hạng', k.theDiem.value.lh.indexOf('AMBASSADOR') >= 0);
  const tienBanh = k.tienBanh.value;
  k.dungDiem(true); await k.xemUuDai(); await chayHen();
  la('hỏi lại kèm dung_diem', hoi[hoi.length - 1].dung_diem, 1);
  la('thẻ đã áp', k.theDiem.value.kieu, 'da_ap');
  la('tổng trừ điểm', k.tong.value.total, tienBanh - 400000 + k.tong.value.ship);
  la('tiền điểm', k.tienDiem.value, 400000);
  await k.submitOrder();
  la('gửi đơn mang dung_diem và giảm đã xem', [gui[0].dung_diem, gui[0].giam_da_xem], [1, 400000]);
  la('gửi xong thì bỏ chọn dùng điểm cho đơn sau', k.S.CO.dungDiem, false);
  diemDoi = true;
  const k2 = taoKho(mt);
  coThem(k2); k2.pick(3); k2.pickSlot(6);
  Object.assign(k2.S.f, {name: 'Lan', phone: '0931224334', addr: '12 Nguyễn Huệ Q1'}); k2.S.CO.dongy = true;
  k2.dungDiem(true); await k2.xemUuDai(); await chayHen();
  const n = hoi.length;
  const kq = await k2.submitOrder(); await chayHen();
  la('diem_doi: dừng cho khách xem, bỏ chọn', [kq && kq.buoc, k2.S.CO.dungDiem], ['uu_dai', false]);
  dung('hỏi lại tổng không dùng điểm', hoi.length > n && hoi[hoi.length - 1].dung_diem === 0);
});

/* ===== v681 (BẢN 2): lời chúc, cờ, thiệp theo TỪNG CHIẾC; ghi chú chọn nhanh ===== */
const gioThu = (k, f = {}) => { k.pick(3); k.pickSlot(6); Object.assign(k.S.f, {name: 'Khách', phone: '0901234567', addr: '12 Nguyễn Huệ Quận 1'}, f); k.S.CO.dongy = true; };
const moiChiec = k => k.S.CART.flatMap(o => (o.chiec || []).map(c => [o.id, c.id, c.wish, c.thiep, c.loi_thiep]));

await ca('v681 thêm bánh mới: Cần cờ, lời chúc trống, không thiệp; thêm lần hai cùng bánh là chiếc MỚI nối sau, không đè chiếc cũ', async () => {
  const {mt} = moiTruong('2026-10-11T08:00:00');
  const k = taoKho(mt); k.phucHoiGio();
  const ban = k.S.CAKES.find(c => c.k === 'CANDLE');
  k.moBanh(ban); k.addToCart();
  la('một chiếc mặc định', k.S.CART[0].chiec.map(c => [c.co, c.wish, c.thiep]), [[true, '', 'khong']]);
  k.S.CART[0].chiec[0].wish = 'Mừng mẹ';
  k.moBanh(ban); k.addToCart();
  la('một dòng hai chiếc', [k.S.CART.length, k.S.CART[0].qty, k.S.CART[0].chiec.length], [1, 2, 2]);
  la('chiếc cũ giữ lời chúc, chiếc mới trống', k.S.CART[0].chiec.map(c => c.wish), ['Mừng mẹ', '']);
  dung('hai định danh khác nhau', k.S.CART[0].chiec[0].id !== k.S.CART[0].chiec[1].id);
});

await ca('v681 một dòng số lượng 2, hai lời chúc và hai loại thiệp: tăng, giảm, sửa bánh, bỏ dòng khác, tải lại không chuyển nhầm nội dung', async () => {
  const a = moiTruong('2026-10-11T08:00:00');
  const k = taoKho(a.mt); k.phucHoiGio();
  const ban = k.S.CAKES.find(c => c.k === 'CANDLE');
  k.moBanh(ban); k.doiSoLuong(1); k.addToCart();
  k.moBanh(k.S.CAKES.find(c => c.k !== 'CANDLE' && c.sizes.length)); k.addToCart();
  const [c1, c2] = k.S.CART[0].chiec;
  c1.wish = 'Chúc A'; k.batThiep(c1.id, true); k.datThiep(c1.id, 'ep_kim'); c1.loi_thiep = 'Thương A';
  c2.wish = 'Chúc B'; k.batThiep(c2.id, true);
  la('chiếc 2 bật thiệp thì chọn sẵn thiệp nhỏ', c2.thiep, 'nho');
  const truoc = moiChiec(k);
  k.cartQty(0, 1);
  la('tăng: thêm chiếc thứ ba trống ở cuối', moiChiec(k).slice(0, 2), truoc.slice(0, 2));
  la('chiếc ba mặc định', [k.S.CART[0].chiec[2].wish, k.S.CART[0].chiec[2].thiep], ['', 'khong']);
  la('giảm chiếc trống: bỏ ngay, không hỏi', [k.cartQty(0, -1), k.S.CART[0].qty, k.S.hoiBo], [undefined, 2, null]);
  la('sau giảm còn đúng hai chiếc cũ', moiChiec(k).slice(0, 2), truoc.slice(0, 2));
  /* Bỏ dòng bánh khác: chiếc của dòng này không đổi. */
  k.cartRemove(1);
  la('bỏ dòng khác', moiChiec(k), truoc.slice(0, 2));
  /* Sửa bánh (đổi phụ kiện, giữ số lượng): giữ nguyên chiếc. */
  k.suaDongGio(0); k.toggleNum(2); la('lưu sửa', k.addToCart(), 'sua');
  la('sửa bánh giữ lời chúc, thiệp từng chiếc', moiChiec(k), truoc.slice(0, 2));
  /* Tải lại trang. */
  k.luuGio();
  const k2 = taoKho(a.mt); k2.phucHoiGio();
  la('tải lại giữ định danh và nội dung', moiChiec(k2), truoc.slice(0, 2));
  la('thiệp ép kim: đúng một BAPK00002', k2.T.hangGui(k2.S.CART, k2.S.DC).filter(x => x.variation_id === 'BAPK00002'), [{variation_id: 'BAPK00002', quantity: 1}]);
});

await ca('v681 giảm số lượng mà chiếc cuối đã có lời chúc hoặc thiệp: hỏi lại; Giữ lại không đổi gì, Đồng ý bỏ đúng chiếc cuối', async () => {
  const {mt} = moiTruong('2026-10-11T08:00:00');
  const k = taoKho(mt); k.phucHoiGio();
  k.moBanh(k.S.CAKES.find(c => c.k === 'CANDLE')); k.doiSoLuong(2); k.addToCart();
  const ds = k.S.CART[0].chiec; ds[0].wish = 'Một'; ds[2].wish = 'Ba';
  la('hỏi lại', k.cartQty(0, -1), 'hoi');
  dung('câu hỏi nói chiếc 3', /3/.test(k.S.hoiBo.chu));
  k.giuLai();
  la('Giữ lại: vẫn ba chiếc', k.S.CART[0].chiec.map(c => c.wish), ['Một', '', 'Ba']);
  k.cartQty(0, -1); k.dongYBo();
  la('Đồng ý: bỏ chiếc cuối', k.S.CART[0].chiec.map(c => c.wish), ['Một', '']);
  /* Sửa bánh mà giảm số lượng làm mất chiếc có nội dung: hỏi trước khi lưu. */
  k.S.CART[0].chiec[1].thiep = 'nho';
  k.suaDongGio(0); k.doiSoLuong(-1);
  la('sửa giảm: hỏi', k.addToCart(), 'hoi');
  la('chưa đổi giỏ', k.S.CART[0].qty, 2);
  la('đồng ý thì lưu', k.dongYBo(), 'sua');
  la('còn một chiếc', k.S.CART[0].chiec.map(c => c.wish), ['Một']);
});

await ca('v681 thiệp ép kim đổi qua lại nhiều lần, mở lại checkout: số BAPK00002 và tiền luôn bằng số chiếc ép kim; giá theo máy chủ', async () => {
  const {mt} = moiTruong('2026-10-11T08:00:00', {'vagabond.don_web.cau_hinh_web': () => ({gia_thiep_ep_kim: 19000, onepay: 0})});
  const k = taoKho(mt); k.phucHoiGio(); await k.napCauHinh();
  la('giá thiệp máy chủ trả', k.giaThiep.value, 19000);
  k.moBanh(k.S.CAKES.find(c => c.k === 'CANDLE')); k.doiSoLuong(2); k.addToCart();
  const goc = k.tienBanh.value, ds = k.S.CART[0].chiec;
  for (let i = 0; i < 5; i++) { ds.forEach(c => { k.batThiep(c.id, true); k.datThiep(c.id, 'ep_kim'); }); k.datThiep(ds[1].id, 'nho'); k.batThiep(ds[2].id, false); }
  k.moGio(); k.roiGio(); k.moGio();
  const ek = () => (k.T.hangGui(k.S.CART, k.S.DC).find(x => x.variation_id === 'BAPK00002') || {quantity: 0}).quantity;
  la('một chiếc ép kim', ek(), 1);
  la('tiền cộng đúng một thiệp', k.tienBanh.value - goc, 19000);
  k.cartQty(0, -1); k.dongYBo();
  la('bỏ chiếc cuối (không thiệp): vẫn một', ek(), 1);
  k.datThiep(ds[0].id, 'nho');
  la('đổi sang thiệp nhỏ: không còn ép kim', [ek(), k.tienBanh.value - goc + k.S.CART[0].price], [0, 0]);
  dung('thiệp ép kim không còn là món mua thêm ở trang chọn bánh', !k.T.hangGui([{id: 'X', qty: 1, adds: [], nguon: 'order', chiec: []}], {}).some(x => x.variation_id === 'BAPK00002'));
});

await ca('v681 giỏ lưu bản trước: lời chúc theo dòng và thiệp ép kim mua thêm chuyển sang từng chiếc, không tính tiền hai lần', async () => {
  const a = moiTruong('2026-10-11T08:00:00');
  a.kho.set('vgb-gio-v1', JSON.stringify({luc: new Date('2026-10-11T07:00:00').getTime(), gio: [
    {k: 'CANDLE', id: 'BAWC00139', cm: 12, price: 1, nguon: 'order', qty: 2, wish: 'Mừng thọ', adds: [{id: 'BAPK00002', n: 'Thiệp', p: 17000}, {id: 'BAPK00005', n: 'Nến số 2', p: 17000}]}]}));
  const k = taoKho(a.mt); k.phucHoiGio();
  la('mỗi chiếc giữ lời chúc và thiệp ép kim', k.S.CART[0].chiec.map(c => [c.co, c.wish, c.thiep]), [[true, 'Mừng thọ', 'ep_kim'], [true, 'Mừng thọ', 'ep_kim']]);
  la('phụ kiện còn nến số, bỏ thiệp khỏi phụ kiện', k.S.CART[0].adds.map(x => x.id), ['BAPK00005']);
  la('BAPK00002 đúng hai, không bốn', k.T.hangGui(k.S.CART, k.S.DC).find(x => x.variation_id === 'BAPK00002').quantity, 2);
});

await ca('v681 gửi đơn: Cần cờ mà trống lời chúc thì nhắc và chỉ đúng thẻ; ghi chú in mỗi chiếc một dòng; máy chủ nhận danh sách từng chiếc', async () => {
  const {mt, vet} = moiTruong('2026-10-11T08:00:00', {'vagabond.don_hang.tao_don': () => ({ok: true, duong_dan: '/banh/xong/lc1'})});
  const k = taoKho(mt); k.phucHoiGio();
  k.moBanh(k.S.CAKES.find(c => c.k === 'CANDLE')); k.doiSoLuong(1); k.toggleNum(2); k.addToCart();
  gioThu(k);
  const [c1, c2] = k.S.CART[0].chiec;
  const kq1 = await k.submitOrder();
  la('nhắc lời chúc', [kq1.buoc, kq1.sel], ['loi_chuc', '#lc-' + c1.id + ' input']);
  la('chưa gửi', vet.filter(v => v[1] === 'vagabond.don_hang.tao_don').length, 0);
  c1.wish = 'Happy 30'; k.batThiep(c1.id, true); k.datThiep(c1.id, 'ep_kim'); c1.loi_thiep = 'Thương em';
  const kq2 = await k.submitOrder();
  la('chiếc hai còn thiếu: chỉ đúng chiếc hai', kq2.sel, '#lc-' + c2.id + ' input');
  k.datCo(c2.id, false); k.batThiep(c2.id, true);
  const kq = await k.submitOrder();
  la('gửi được', kq.buoc, 'xong');
  la('ghi chú in mỗi chiếc một dòng', kq.don.note_print.split('\n'), [
    '1. CANDLE Ø12cm | lời chúc: Happy 30 | thiệp ép kim: Thương em | kèm: Nến số 2',
    '2. CANDLE Ø12cm | không cắm cờ | thiệp nhỏ: để trắng | kèm: Nến số 2']);
  la('từng chiếc gửi máy chủ', kq.don.chiec.map(c => [c.ma, c.co, c.loi_chuc, c.thiep, c.loi_thiep]),
    [['BAWC00139', true, 'Happy 30', 'ep_kim', 'Thương em'], ['BAWC00139', false, '', 'nho', '']]);
  la('thiệp ép kim một dòng đúng một cái', kq.don.items.filter(x => x.variation_id === 'BAPK00002'), [{variation_id: 'BAPK00002', quantity: 1}]);
  dung('thẻ Viết thiệp vì có lời thiệp', kq.don.tags.includes(98));
  la('tên web lúc đặt', kq.don.chiec[0].ten, 'CANDLE · Ø 12cm');
});

await ca('v681 ghi chú chọn nhanh: 0, 1, nhiều viên; giờ trễ nhất theo khung; đổi sang Tự lấy không gửi viên giao hàng; dị ứng trống thì nhắc; đổi nhãn không mất chức năng', async () => {
  let nhan = {};
  const {mt} = moiTruong('2026-10-11T08:00:00', {'vagabond.don_hang.tao_don': () => ({ok: true, duong_dan: '/banh/xong/gc1'})});
  mt.t = (key, d, thay) => t0(key, nhan[key] || d, thay);
  const k = taoKho(mt); k.phucHoiGio();
  coThem(k); gioThu(k);
  la('mặc định không viên nào', k.S.CO.gc, []);
  la('năm viên khi giao', k.gcHien.value.map(x => x.ma), ['goi_truoc', 'gui_le_tan', 'chup_hinh', 'gio_tre_nhat', 'di_ung']);
  let kq = await k.submitOrder();
  la('0 viên: ghi chú chung không có dòng chọn nhanh', [kq.buoc, kq.don.note, kq.don.ghi_chu_nhanh], ['xong', '', []]);
  const k2 = taoKho(mt); coThem(k2); gioThu(k2, {note: 'Để trước cửa'});
  k2.doiGc('goi_truoc'); k2.doiGc('gui_le_tan'); k2.doiGc('gio_tre_nhat');
  la('giờ trễ nhất chỉ trong khung 13h - 15h', k2.gioTreChon.value, ['13:30', '14:00', '14:30']);
  la('chưa chọn giờ thì nhắc', (await k2.submitOrder()).buoc, 'ghi_chu');
  k2.chonGioTre('14:30'); k2.chonGioTre('19:00');
  la('giờ ngoài khung bỏ qua', k2.S.CO.gcGio, '14:30');
  k2.pickSlot(8);
  la('đổi khung giờ: giờ không còn hợp lệ thì xoá và nhắc', [k2.S.CO.gcGio, !!k2.S.goi.gcGio], ['', true]);
  k2.chonGioTre('15:30');
  nhan = {gc_goi_truoc: 'Alo trước nhé'};
  kq = await k2.submitOrder();
  la('ghi chú: dòng đầu là các viên nối bằng chấm giữa, rồi chữ khách gõ', kq.don.note.split('\n'), ['Alo trước nhé · Không ai nghe máy thì gửi lễ tân · Trễ nhất 15:30', 'Để trước cửa']);
  la('mã viên lưu kèm', [kq.don.ghi_chu_nhanh, kq.don.gio_tre_nhat], [['goi_truoc', 'gui_le_tan', 'gio_tre_nhat'], '15:30']);
  dung('đổi nhãn vẫn gắn thẻ Gọi trước khi giao theo mã', kq.don.tags.includes(33));
  /* Tự lấy: bốn viên giao hàng ẩn và không gửi; dị ứng luôn hiện, trống thì nhắc. */
  const k3 = taoKho(mt); coThem(k3); gioThu(k3);
  k3.doiGc('goi_truoc'); k3.doiGc('chup_hinh'); k3.doiGc('di_ung'); k3.setMode('pick'); k3.setPickup(k3.S.PICKUPS[0].id);
  la('tự lấy chỉ còn viên dị ứng', k3.gcHien.value.map(x => x.ma), ['di_ung']);
  la('dị ứng trống: nhắc', [(await k3.submitOrder()).buoc], ['ghi_chu']);
  k3.S.f.note = 'Dị ứng hạt điều';
  kq = await k3.submitOrder();
  la('không gửi viên giao hàng đang ẩn', [kq.don.ghi_chu_nhanh, kq.don.tags.includes(33), kq.don.tags.includes(32)], [['di_ung'], false, false]);
  la('phiếu bếp có dòng dị ứng', kq.don.note_print.split('\n')[0], 'DỊ ỨNG: Dị ứng hạt điều');
  la('ghi chú chung', kq.don.note.split('\n'), ['Có người dị ứng', 'Dị ứng hạt điều']);
});

await ca('v681 thẻ tóm tắt: phí giao ba trạng thái tách rõ, thiếu giờ, thiếu địa chỉ hiện chữ nhắc; không còn ô nhắc trên nút gửi', async () => {
  const {mt} = moiTruong('2026-10-11T08:00:00');
  const k = taoKho(mt); k.phucHoiGio(); coThem(k);
  let tt = k.theTomTat.value;
  la('chưa chọn giờ, chưa địa chỉ', [tt.nhan, tt.giao, tt.kieuPhi, tt.dayNhan], ['', '', 'chua', 'Tạm tính']);
  gioThu(k);
  k.S.CO.ship = 30000; k.S.CO.shipTrangThai = 'du_kien';
  tt = k.theTomTat.value;
  la('phí dự kiến', [tt.kieuPhi, tt.phi, tt.dayNhan, tt.dayPhu], ['du_kien', 'dự kiến 30.000 đ', 'Tổng cộng', 'đã gồm phí giao dự kiến']);
  k.S.CO.shipTrangThai = 'chua_ro';
  la('chưa tính được (không hiện 0 đ)', [k.theTomTat.value.kieuPhi, k.theTomTat.value.phi], ['chua', 'chưa tính được']);
  dung('có dòng nhận', /13h - 15h/.test(k.theTomTat.value.nhan));
  dung('bỏ ô nhắc lại trên nút gửi', !MAU.includes('id="chotDon"'));
  dung('bỏ dòng Tiền bánh trùng lặp', !MAU.includes("t('gio_hang_tien_banh'"));
});

await ca('v681 luật mọi ảnh trên web chính sửa được ở trình biên tập: mỗi ô ảnh trong sổ nhãn có ảnh có sẵn, trang dùng anhWeb; ảnh đã tải lên thay ảnh có sẵn, giá trị lạ không lọt', async () => {
  const {ANH_O_MAC_DINH} = await import('../../../public/web_vue/banh/du-lieu.js');
  const {ND, anhWeb} = await import('../../../public/web_vue/kho/chu.js');
  const SO = JSON.parse(readFileSync(new URL('../../../public/web_order/chu-mac-dinh.json', import.meta.url), 'utf8'));
  const oAnh = Object.keys(SO).filter(k => SO[k].anh).sort();
  la('sổ nhãn và bảng ảnh có sẵn cùng một bộ khoá', Object.keys(ANH_O_MAC_DINH).sort(), oAnh);
  dung('đủ 25 ô ảnh', oAnh.length === 25);
  /* Mọi khoá anhWeb('...') viết thẳng trong trang đều có trong sổ, và ngược lại mọi ô đều được trang dùng. */
  const nguon = MAU + readFileSync(new URL('../../../public/web_vue/banh/du-lieu.js', import.meta.url), 'utf8');
  const dung1 = [...nguon.matchAll(/anhWeb\('([a-z0-9_]+)'/g)].map(m => m[1]);
  dung1.forEach(k => dung('khoá ' + k + ' có trong sổ', oAnh.includes(k)));
  /* Luật: mọi <img :src> trong mẫu trang hoặc đi qua anhWeb, hoặc là ảnh lấy từ dữ liệu máy chủ đã sửa được
     ở thẻ Bánh, Banner, Món (danh sách dưới), hoặc logo thương hiệu, logo đơn vị thanh toán. Thêm ảnh gắn cứng mới thì ca đỏ. */
  const TU_MAY_CHU = new Set(['x.m.anh', 'm.anh', 'x.c.img', 'd.o.img', 'x.o.img', 'b.img', 'muaXem.m.anh', 'chiTiet.anhs[anhChon] || chiTiet.c.img', 'u', 'LOGO', 'LOGO_TT[l].src']);
  const src = [...MAU.matchAll(/:src="([^"]+)"/g)].map(m => m[1]);
  const la1 = src.filter(e => !e.startsWith('anhWeb(') && !TU_MAY_CHU.has(e));
  la('ảnh gắn cứng chưa vào trình biên tập', la1, []);
  dung('trang có dùng anhWeb', src.filter(e => e.startsWith('anhWeb(')).length >= 8);
  /* anhWeb: ảnh đã tải lên thay ảnh có sẵn; trống, link ngoài, svg, đi lùi thư mục thì về ảnh có sẵn. */
  const cu = ND.nhan; ND.nhan = {anh_co_mau: '/files/web-abc123.webp'};
  la('ảnh đã tải lên', anhWeb('anh_co_mau', 'co-san'), '/files/web-abc123.webp');
  for (const v of ['', '  ', 'https://evil.example/a.png', '/files/a.svg', '/files/../private/files/x.png', 'javascript:alert(1)', '/private/files/x.png', 12]) {
    ND.nhan = {anh_co_mau: v};
    la('giá trị lạ ' + JSON.stringify(v), anhWeb('anh_co_mau', 'co-san'), 'co-san');
  }
  ND.nhan = {}; la('chưa sửa thì ảnh có sẵn', anhWeb('anh_thiep_nho', ''), '');
  ND.nhan = cu;
});

/* ---------------- v682 thẻ Thành viên dưới ô số điện thoại (BẢN 2 mục 2.2) ----------------
   Máy chủ giả giữ luật của xem_uu_dai: số đã đặt web thì don_dau khong; khach.da_dat, khach.xac_thuc
   theo phiên; điểm chỉ lộ sau xác thực. Gửi mã, xác thực có thể trả chậm (hứa tự giải). */
function mayChuTv({daDat = [], phienSan = '', diem = true, uuDai = true} = {}) {
  const v = {hoi: [], gui: [], xac: [], tra: [], phien: phienSan, cho: null, choTra: null};
  const mang = {
    'vagabond.don_hang.xem_uu_dai': th => {
      const d = JSON.parse(th.don); v.hoi.push(d);
      const so = String(d.dien_thoai || '').replace(/\D/g, '');
      const cu = daDat.includes(so), xac = !!so && v.phien === so;
      const dd = {giam: 50000, toi_thieu: 300000, ap_dung: 0, bo_ma: 0,
        trang_thai: !uuDai || cu ? 'khong' : (xac ? 'du' : 'can_xac_thuc')};
      if (dd.trang_thai === 'du') dd.ap_dung = 1;
      const dv = !diem ? null : (!xac ? {trang_thai: 'can_xac_thuc'}
        : {trang_thai: 'dung_duoc', so_du: 1200, toi_da: 400, tien_toi_da: 400000, dung: d.dung_diem ? 400 : 0, tien: d.dung_diem ? 400000 : 0});
      return {ok: 1, giam: (dd.ap_dung ? 50000 : 0) + (dv && dv.tien || 0), ap: [], don_dau: dd, diem: dv, khach: so ? {da_dat: cu ? 1 : 0, xac_thuc: xac ? 1 : 0} : null};
    },
    'vagabond.thanh_vien.gui_ma': th => { v.gui.push(th); if (v.cho) return new Promise(res => { v.cho.push(() => res({ok: 1})); }); return {ok: 1, song_giay: 300}; },
    'vagabond.thanh_vien.xac_thuc': th => { v.xac.push(th); const lam = () => { if (th.ma !== '123456') return {ok: 0, ly_do: 'ma_khong_dung'}; v.phien = String(th.sdt); return {ok: 1}; };
      if (v.cho) return new Promise(res => { v.cho.push(() => res(lam())); }); return lam(); },
    'vagabond.api.tra_khach': p => { v.tra.push(p.phone); const kq = v.phien === p.phone ? {addresses: [{ho_ten: 'Khách', phone: p.phone, dia_chi: '12 Nguyễn Huệ'}]} : {addresses: [], ly_do: 'can_xac_thuc'};
      /* choTra: máy chủ đã đọc xong lúc phiên còn hạn nhưng trả muộn (Codex #605 vòng 3). */
      if (v.choTra) return new Promise((res, rej) => { v.choTra.push(loi => loi ? rej(new Error('mạng rớt')) : res(kq)); }); return kq; },
  };
  return {v, mang};
}

await ca('v682 thẻ Thành viên: chưa đủ số thì ẩn; số mới mời giảm 50.000; số đã đặt chào quay lại; tắt ưu đãi đơn đầu thì mời tích điểm, không nói "quay lại" với số mới', async () => {
  const {mang} = mayChuTv({daDat: ['0909111222'], uuDai: true});
  const {mt, chayHen} = moiTruong('2026-11-21T08:00:00', mang);
  const k = taoKho(mt);
  coThem(k); k.moGio(); k.S.f.phone = '0931'; await chayHen();
  la('chưa đủ số: ẩn', k.theThanhVien.value, null);
  k.S.f.phone = '0931224334'; await chayHen();
  let th = k.theThanhVien.value;
  la('số mới', [th.kieu, th.dia, th.nut], ['moi', '-50K', true]);
  dung('tiêu đề nói mức giảm', /50\.000/.test(th.tieu) && /đơn đầu tiên/.test(th.tieu));
  dung('dòng phụ nói ưu đãi, điểm, địa chỉ', /tích điểm/.test(th.phu) && /địa chỉ/.test(th.phu));
  k.S.f.phone = '0909111222'; await chayHen();
  th = k.theThanhVien.value;
  la('số đã đặt', [th.kieu, th.dia, th.tieu], ['cu', '★', 'Chào mừng quý khách quay lại']);
  const tat = mayChuTv({uuDai: false});
  const m2 = moiTruong('2026-11-21T08:00:00', tat.mang);
  const k2 = taoKho(m2.mt); coThem(k2); k2.moGio(); k2.S.f.phone = '0931224334'; await m2.chayHen();
  la('tắt ưu đãi, số mới: mời tích điểm', [k2.theThanhVien.value.kieu, k2.theThanhVien.value.tieu], ['cu', 'Tích điểm thành viên cho số này']);
});

await ca('v682 thẻ Thành viên: gửi mã thì sang 6 ô và đếm 60 giây; dán đủ 6 số vào ô đầu thì tự xác nhận; xác thực xong một lần dùng chung ưu đãi, điểm, địa chỉ đã lưu', async () => {
  const {v, mang} = mayChuTv();
  const {mt, chayHen} = moiTruong('2026-11-21T08:00:00', mang);
  const k = taoKho(mt);
  coThem(k); k.moGio(); k.S.f.phone = '0931224334'; await chayHen();
  await k.guiMaDonDau();
  la('bước nhập mã', [k.theThanhVien.value.kieu, k.theThanhVien.value.tieu, k.S.CO.dd.cho], ['ma', 'Nhập mã 6 số Zalo vừa gửi', 60]);
  await chayHen();
  la('đếm lùi từng giây tới 0 thì gửi lại được', k.S.CO.dd.cho, 0);
  la('gõ ô đầu: con trỏ sang ô 2', k.nhapMa(0, '1'), 1);
  la('gõ ô 2', [k.nhapMa(1, '9'), k.S.CO.dd.ma], [2, '19']);
  la('xoá lùi ô 3 trống: bỏ số ô 2', [k.xoaLuiMa(2), k.S.CO.dd.ma], [1, '1']);
  la('dán 6 số vào ô đầu: đủ mã', k.nhapMa(0, '123 456'), 5);
  await chayHen(); await chayHen();
  la('tự xác nhận đúng số, đúng mã', v.xac[v.xac.length - 1], {sdt: '0931224334', ma: '123456'});
  const th = k.theThanhVien.value;
  la('đã xác thực', [th.kieu, th.tieu], ['xac', '✓ ĐÃ XÁC THỰC SỐ 0931224334']);
  dung('ưu đãi đơn đầu nằm trong thẻ', /Đã giảm 50\.000/.test(th.phu));
  la('công tắc điểm', [th.diem.co, th.diem.so, th.diem.tien], [false, (400).toLocaleString('vi-VN'), '400.000 đ']);
  la('đọc địa chỉ của đúng số sau xác thực', v.tra[v.tra.length - 1], '0931224334');
  await chayHen();
  la('dòng địa chỉ đã lưu', k.theThanhVien.value.soDc, 1);
  k.dungDiem(true); await chayHen(); await k.xemUuDai(); await chayHen();
  la('bật công tắc: dùng 400 điểm', [k.theThanhVien.value.diem.co, k.theThanhVien.value.diem.tien], [true, '400.000 đ']);
  la('chỉ gửi mã một lần cho cả ba thứ', v.gui.length, 1);
});

await ca('v682 đổi số: xoá ngay xác thực, ưu đãi, điểm, địa chỉ của số cũ; phản hồi chậm của số cũ (gửi mã, xác thực) bị bỏ qua; nút Đổi số về bước đầu', async () => {
  const {v, mang} = mayChuTv();
  const {mt, chayHen} = moiTruong('2026-11-21T08:00:00', mang);
  const k = taoKho(mt);
  coThem(k); k.moGio(); k.S.f.phone = '0931224334'; await chayHen();
  await k.guiMaDonDau(); k.S.CO.dd.ma = '123456';
  await k.xacThucDonDau(); await chayHen(); await chayHen();
  la('số cũ đã xác thực, có địa chỉ, bật điểm', [k.theThanhVien.value.kieu, k.S.CO.addrList.length], ['xac', 1]);
  k.dungDiem(true);
  k.S.f.phone = '0901234567'; k.lookupPhone(); await chayHen();
  la('đổi số: không còn xác thực, điểm, địa chỉ', [k.theThanhVien.value.kieu, k.S.CO.dungDiem, k.S.CO.addrList.length, k.S.CO.dd.daXac], ['moi', false, 0, '']);
  /* Phản hồi chậm: gửi mã cho số B, đổi sang số C trước khi máy trả. */
  v.cho = [];
  const p1 = k.guiMaDonDau();
  k.S.f.phone = '0912345678'; await chayHen();
  v.cho.shift()(); await p1; await chayHen();
  la('gửi mã trả muộn của số cũ: không sang bước nhập mã', k.S.CO.dd.buoc, 'nut');
  v.cho = null; await k.guiMaDonDau(); v.cho = [];
  k.S.CO.dd.ma = '123456';
  const p2 = k.xacThucDonDau();
  k.S.f.phone = '0987654321'; await chayHen();
  v.cho.shift()(); await p2; await chayHen();
  dung('xác thực trả muộn của số cũ: số mới không thành đã xác thực', k.S.CO.dd.daXac !== '0987654321' && k.theThanhVien.value.kieu !== 'xac');
  /* Mã sai của số cũ trả muộn: không hiện câu lỗi dưới số mới. */
  v.cho = null; await k.guiMaDonDau(); v.cho = [];
  k.S.CO.dd.ma = '000000';
  const p3 = k.xacThucDonDau();
  k.S.f.phone = '0977777777'; await chayHen();
  v.cho.shift()(); await p3; await chayHen();
  la('lỗi mã của số cũ không hiện dưới số mới', k.S.CO.dd.loi, '');
  v.cho = null; await k.guiMaDonDau();
  la('đang nhập mã', k.S.CO.dd.buoc, 'ma');
  k.doiSo();
  la('Đổi số: về bước đầu', [k.S.CO.dd.buoc, k.S.CO.dd.ma, k.S.CO.dd.cho], ['nut', '', 0]);
});

await ca('Codex #605: đã xác thực, chọn địa chỉ đã lưu rồi bật Dùng điểm hay sửa giỏ: địa chỉ đang chọn giữ nguyên, không tra lại khách, thẻ không nháy mất trong lúc hỏi lại ưu đãi', async () => {
  const {v, mang} = mayChuTv({phienSan: '0931224334'});
  const {mt, chayHen} = moiTruong('2026-11-21T08:00:00', mang);
  const k = taoKho(mt);
  coThem(k); k.moGio(); k.S.f.phone = '0931224334'; await chayHen(); await chayHen();
  la('đã xác thực, có địa chỉ', [k.theThanhVien.value.kieu, k.S.CO.addrList.length], ['xac', 1]);
  k.selAddr(0);
  const traTruoc = v.tra.length;
  k.dungDiem(true);
  la('đang hỏi lại: thẻ vẫn là Đã xác thực', k.theThanhVien.value && k.theThanhVien.value.kieu, 'xac');
  await chayHen(); await chayHen();
  la('bật điểm: địa chỉ đang chọn giữ nguyên', k.S.CO.addrSel, 0);
  k.cartQty(0, 1);
  la('sửa giỏ, đang hỏi lại: thẻ vẫn còn', k.theThanhVien.value && k.theThanhVien.value.kieu, 'xac');
  await chayHen(); await chayHen();
  la('sửa giỏ: địa chỉ giữ nguyên', k.S.CO.addrSel, 0);
  la('không tra lại khách', v.tra.length - traTruoc, 0);
});

await ca('Codex #605 vòng 2: xác thực ngay trong checkout rồi hết phiên (đăng xuất ở tab khác): lượt hỏi lại báo chưa xác thực thì thẻ bỏ Đã xác thực, hiện lại nút gửi mã', async () => {
  const {v, mang} = mayChuTv();
  const {mt, chayHen} = moiTruong('2026-11-21T08:00:00', mang);
  const k = taoKho(mt);
  coThem(k); k.moGio(); k.S.f.phone = '0931224334'; await chayHen();
  await k.guiMaDonDau(); k.S.CO.dd.ma = '123456'; await k.xacThucDonDau(); await chayHen(); await chayHen();
  la('đã xác thực', k.theThanhVien.value.kieu, 'xac');
  k.selAddr(0); k.dungDiem(true); await chayHen(); await chayHen();
  v.phien = '';
  k.cartQty(0, 1); await chayHen(); await chayHen();
  const th = k.theThanhVien.value;
  la('hết phiên: không còn Đã xác thực, có nút gửi mã', [th.kieu !== 'xac', !!th.nut, k.daXacThuc.value], [true, true, false]);
  la('hết phiên: bỏ địa chỉ đã lấy và công tắc điểm', [k.S.CO.addrList.length, k.S.CO.addrSel, k.S.CO.dungDiem], [0, -1, false]);
});

await ca('Codex #605 vòng 3: lượt tra địa chỉ bắt đầu lúc phiên còn hạn nhưng trả muộn, giữa chừng hết phiên: phản hồi muộn bị bỏ, danh sách địa chỉ vẫn rỗng', async () => {
  const {v, mang} = mayChuTv();
  const {mt, chayHen} = moiTruong('2026-11-21T08:00:00', mang);
  const k = taoKho(mt);
  coThem(k); k.moGio(); k.S.f.phone = '0931224334'; await chayHen();
  v.choTra = [];
  await k.guiMaDonDau(); k.S.CO.dd.ma = '123456'; await k.xacThucDonDau(); await chayHen(); await chayHen();
  la('đã xác thực, lượt tra địa chỉ đang chờ', [k.daXacThuc.value, v.choTra.length, k.S.CO.addrList.length], [true, 1, 0]);
  v.phien = '';
  k.cartQty(0, 1); await chayHen(); await chayHen();
  la('hết phiên', k.daXacThuc.value, false);
  v.choTra.shift()(); await chayHen(); await chayHen();
  la('phản hồi muộn không ghi lại địa chỉ', [k.S.CO.addrList.length, k.S.CO.addrSel, k.daXacThuc.value], [0, -1, false]);
  la('không hiện câu "Tìm thấy N địa chỉ"', k.S.goi.phone, null);
  /* Xác thực lại thì vẫn tra được bình thường. */
  v.choTra = null;
  await k.guiMaDonDau(); k.S.CO.dd.ma = '123456'; await k.xacThucDonDau(); await chayHen(); await chayHen();
  la('xác thực lại: địa chỉ trở lại', [k.daXacThuc.value, k.S.CO.addrList.length], [true, 1]);
  /* Lượt tra cũ báo lỗi mạng sau khi lượt mới đã trả: không xoá danh sách của lượt mới. */
  v.choTra = [];
  k.lookupPhone(); await chayHen();
  k.lookupPhone(); await chayHen();
  la('hai lượt tra đang chờ', v.choTra.length, 2);
  v.choTra[1](); await chayHen();
  la('lượt mới trả: có địa chỉ', k.S.CO.addrList.length, 1);
  v.choTra[0](true); await chayHen();
  la('lượt cũ báo lỗi muộn: danh sách của lượt mới giữ nguyên', k.S.CO.addrList.length, 1);
});

await ca('v682 mở lại checkout (đã xác thực trong phiên trước, cookie còn): thẻ hiện Đã xác thực ngay, không bắt gửi mã lại', async () => {
  const {v, mang} = mayChuTv({phienSan: '0931224334'});
  const {mt, chayHen} = moiTruong('2026-11-21T08:00:00', mang);
  const k = taoKho(mt);
  coThem(k); k.moGio(); k.S.f.phone = '0931224334'; await chayHen();
  la('đã xác thực theo máy chủ', k.theThanhVien.value.kieu, 'xac');
  la('không gửi mã', v.gui.length, 0);
  dung('mẫu trang: thẻ ngay dưới ô số, hai thẻ cũ ở Thanh toán đã bỏ', MAU.indexOf('id="theTv"') > MAU.indexOf('id="f-phone"') && MAU.indexOf('id="theTv"') < MAU.indexOf('id="f-name"') && !MAU.includes('id="donDau"') && !MAU.includes('id="theDiem"'));
});

/* ---------------- v684 (BẢN 2 mục 2.3): ô Phường giao ---------------- */
const PH = [
  {ma: '84_VN12901', ten: 'Phường Sài Gòn', khu: 'q1', quan_cu: 'Quận 1', cu: ['Bến Nghé', 'Đa Kao', 'Nguyễn Thái Bình'], loai: ''},
  {ma: '84_VN12902', ten: 'Phường Tân Định', khu: 'q1', quan_cu: 'Quận 1', cu: ['Tân Định', 'Đa Kao'], loai: ''},
  {ma: '84_VN12903', ten: 'Phường Bến Thành', khu: 'q1', quan_cu: 'Quận 1', cu: ['Bến Thành', 'Phạm Ngũ Lão'], loai: ''},
  {ma: '84_VN129015', ten: 'Phường Bàn Cờ', khu: 'q3', quan_cu: 'Quận 3', cu: ['Phường 1', 'Phường 2', 'Phường 5'], loai: ''},
  {ma: '84_VN12924', ten: 'Phường Bình Đông', khu: 'q8', quan_cu: 'Quận 8', cu: ['Phường 6', 'An Phú Tây (Bình Chánh)'], loai: 'mot_phan'},
];
function mayChuPh(them = {}) {
  const v = {phiGiao: 0, gui: []};
  const mang = Object.assign({
    'vagabond.don_web.cau_hinh_web': () => ({phuong: PH, mien_phi_tu: 0}),
    'vagabond.giao_hang.phi_giao': () => { v.phiGiao++; return {ok: 1, total_fee: 41000, diem_lay: 'tan-son-hoa'}; },
    'vagabond.don_hang.tao_don': p => { v.gui.push(JSON.parse(p.don)); return {ok: 1}; },
  }, them);
  return {v, mang};
}

await ca('v684 ô Phường giao: gõ tên phường mới, quận cũ, phường cũ, không dấu đều tìm được; phường cũ khớp được tô; không có phí dự kiến', async () => {
  const {mang} = mayChuPh();
  const {mt, chayHen} = moiTruong('2026-11-22T08:00:00', mang);
  const k = taoKho(mt); await k.napCauHinh();
  k.moPhuong(); await chayHen();
  k.goPhuong('sai gon');
  la('không dấu: tên mới', k.goiYPhuong.value.map(p => p.ten), ['Phường Sài Gòn']);
  k.goPhuong('Đa Kao');
  la('phường cũ: cả hai phường mới có phần Đa Kao', k.goiYPhuong.value.map(p => [p.ten, p.khop]), [['Phường Sài Gòn', 'Đa Kao'], ['Phường Tân Định', 'Đa Kao']]);
  dung('dòng phụ ghi quận cũ và phường cũ', k.goiYPhuong.value[0].phu.startsWith('Quận 1 cũ · ') && k.goiYPhuong.value[0].phu.includes('Đa Kao'));
  k.goPhuong('quan 3');
  la('quận cũ', k.goiYPhuong.value.map(p => p.ten), ['Phường Bàn Cờ']);
  dung('dòng không mang phí', !('phi' in k.goiYPhuong.value[0]));
  k.goPhuong('binh dong');
  la('phường có phần ngoài vùng được đánh dấu', k.goiYPhuong.value[0].ngoai, true);
  k.goPhuong('Thủ Thiêm');
  la('không có trong vùng: danh sách rỗng', k.goiYPhuong.value.length, 0);
});

await ca('v684 chọn phường: chưa có địa chỉ thì không có phí (không dự kiến, không gọi hãng giao); ô hiện "Phường … · Quận X cũ"; gõ đủ địa chỉ thì ra phí chính xác', async () => {
  const {v, mang} = mayChuPh();
  const {mt, chayHen} = moiTruong('2026-11-22T08:00:00', mang);
  const k = taoKho(mt); await k.napCauHinh();
  coThem(k); k.moPhuong(); await chayHen();
  k.chonPhuong('84_VN12903'); await chayHen();
  la('chưa có phí', [k.S.CO.shipTrangThai, k.S.CO.ship], [null, null]);
  la('ô hiện tên và quận cũ', k.theoPhuong.value.chu, 'Phường Bến Thành · Quận 1 cũ');
  dung('câu mời gõ địa chỉ nêu đúng phường', JSON.stringify(k.S.goi.ship).includes('Phường Bến Thành') && JSON.stringify(k.S.goi.ship).includes('gõ địa chỉ'));
  la('không gọi hãng giao', v.phiGiao, 0);
  k.S.f.addr = '12 Nguyễn Huệ, Phường Sài Gòn'; k.quoteShip(); await chayHen(); await chayHen();
  la('đủ địa chỉ: phí chính xác', [k.S.CO.shipTrangThai, k.S.CO.ship, v.phiGiao], ['chinh_xac', 41000, 1]);
});

await ca('v684 Codex #606: hỏi phí gửi kèm mã phường đang chọn (máy chủ ghép phường như lúc gửi đơn); đổi phường là hỏi lại với phường mới; bỏ phường thì không gửi', async () => {
  const hoi = [];
  const {mang} = mayChuPh({'vagabond.giao_hang.phi_giao': p => { hoi.push(Object.assign({}, p)); return {ok: 1, total_fee: 41000}; }});
  const {mt, chayHen} = moiTruong('2026-11-22T08:00:00', mang);
  const k = taoKho(mt); await k.napCauHinh();
  coThem(k); k.moPhuong(); await chayHen();
  k.chonPhuong('84_VN12903'); await chayHen();
  k.S.f.addr = '12 Nguyễn Huệ'; k.quoteShip(); await chayHen(); await chayHen();
  la('lần một: phường Bến Thành', [hoi.length, hoi[0].addr, hoi[0].phuong], [1, '12 Nguyễn Huệ', '84_VN12903']);
  k.moPhuong(); k.chonPhuong('84_VN12901'); await chayHen(); await chayHen();
  la('đổi phường: hỏi lại với phường mới', [hoi.length, hoi[hoi.length - 1].phuong], [2, '84_VN12901']);
  k.boPhuong(); await chayHen(); await chayHen();
  dung('bỏ phường: không gửi mã phường', !('phuong' in hoi[hoi.length - 1]));
  /* Marketing sửa chữ "cũ" ở bảng chữ thì dòng quận cũ đổi theo (Codex #606). */
  const e2 = moiTruong('2026-11-22T08:00:00', mayChuPh().mang);
  e2.mt.t = (key, d, thay) => t0(key, key === 'ph684_cu' ? '(trước 7/2025)' : d, thay);
  const k2 = taoKho(e2.mt); await k2.napCauHinh();
  k2.chonPhuong('84_VN12903'); await e2.chayHen();
  la('chữ "cũ" theo bảng chữ', k2.theoPhuong.value.chu, 'Phường Bến Thành · Quận 1 (trước 7/2025)');
});

await ca('v684 Codex #606: địa chỉ đã lưu kiểu cũ (Phường Tân Phú, Quận 7) không tự đổi phường khách đã chọn sang phường Tân Phú mới, cũng không bỏ chọn; luật thuần khớp máy chủ', async () => {
  const PH2 = PH.concat([{ma: '84_VN12920', ten: 'Phường Tân Mỹ', khu: 'q7', quan_cu: 'Quận 7', cu: ['Tân Phú', 'Phú Mỹ'], loai: ''},
    {ma: '84_VN12965', ten: 'Phường Tân Phú', khu: 'tan-phu', quan_cu: 'Tân Phú', cu: ['Phú Trung'], loai: ''}]);
  const {mang} = mayChuPh({'vagabond.don_web.cau_hinh_web': () => ({phuong: PH2, mien_phi_tu: 0})});
  const {mt, chayHen} = moiTruong('2026-11-22T08:00:00', mang);
  const k = taoKho(mt); await k.napCauHinh();
  coThem(k); k.moPhuong(); await chayHen();
  k.chonPhuong('84_VN12920'); await chayHen();
  const cu = '10 Nguyễn Lương Bằng, Phường Tân Phú, Quận 7, TP. Hồ Chí Minh';
  const {phuongTrongDiaChi, laDiaChiCu} = await import('../../../public/web_vue/kho/thuan.js');
  la('kiểu cũ: không đoán phường', [laDiaChiCu(cu), phuongTrongDiaChi(PH2, cu)], [true, null]);
  k.S.CO.addrList = [{full_address: cu}]; k.selAddr(0); await chayHen();
  la('giữ Tân Mỹ khách đã chọn', k.S.CO.phuong, '84_VN12920');
  la('kiểu mới vẫn tự điền', phuongTrongDiaChi(PH2, '7 Lũy Bán Bích, Phường Tân Phú, Thành phố Hồ Chí Minh').ma, '84_VN12965');
});

await ca('v684 Codex #606 vòng 2: phường là MỘT phần riêng của địa chỉ, cùng luật máy chủ: đường trùng tên không tính, Tân Sơn khác Tân Sơn Nhì, P. viết tắt được', async () => {
  const {phuongTrongDiaChi, coPhuong} = await import('../../../public/web_vue/kho/thuan.js');
  const ds = [{ma: 'ts', ten: 'Phường Tân Sơn'}, {ma: 'tsn', ten: 'Phường Tân Sơn Nhì'}];
  la('đường trùng tên', [coPhuong('10 Tân Sơn', ds[0]), phuongTrongDiaChi(ds, '10 Tân Sơn')], [false, null]);
  la('phường dài hơn', phuongTrongDiaChi(ds, '7 Lũy Bán Bích, Phường Tân Sơn Nhì, Thành phố Hồ Chí Minh').ma, 'tsn');
  la('viết tắt', ['10 Tân Sơn, P. Tân Sơn', '10 x, p tan son', '10 x, P.Tân Sơn'].map(a => (phuongTrongDiaChi(ds, a) || {}).ma), ['ts', 'ts', 'ts']);
});

await ca('v684 phường có phần ngoài vùng giao: không nhận nguyên phường, phí "chưa tính được", mời gõ địa chỉ; không bao giờ thành 0 đ', async () => {
  const {v, mang} = mayChuPh();
  const {mt, chayHen} = moiTruong('2026-11-22T08:00:00', mang);
  const k = taoKho(mt); await k.napCauHinh();
  coThem(k); k.moPhuong(); await chayHen();
  k.chonPhuong('84_VN12924'); await chayHen();
  la('chưa tính được', [k.S.CO.shipTrangThai, k.S.CO.ship], ['chua_ro', null]);
  dung('câu nói rõ phần ngoài vùng', JSON.stringify(k.S.goi.ship).includes('ngoài vùng giao') && JSON.stringify(k.S.goi.ship).includes('chưa tính được'));
  la('không gọi hãng giao', v.phiGiao, 0);
});

await ca('v684 địa chỉ chọn từ gợi ý ghi đúng một phường mới thì tự điền phường; ghi phường khác thì bỏ chọn để khách chọn lại; gửi đơn mang mã phường, tự lấy thì không', async () => {
  const {v, mang} = mayChuPh({
    'vagabond.dia_chi.goi_y_dia_chi': () => ({suggestions: [{mo_ta: '10 Lê Lợi, Phường Bến Thành, Thành phố Hồ Chí Minh', place_id: 'A'}, {mo_ta: '5 Hai Bà Trưng, Phường Tân Định, Thành phố Hồ Chí Minh', place_id: 'B'}]}),
    'vagabond.dia_chi.chi_tiet_dia_chi': p => ({lat: 10.77, lng: 106.7, dia_chi: p.place_id === 'A' ? '10 Lê Lợi, Phường Bến Thành, Thành phố Hồ Chí Minh' : '5 Hai Bà Trưng, Phường Tân Định, Thành phố Hồ Chí Minh'}),
  });
  const {mt, chayHen} = moiTruong('2026-11-22T08:00:00', mang);
  const k = taoKho(mt); await k.napCauHinh();
  coThem(k); k.pick(3); k.pickSlot(6);
  k.S.f.addr = '10 Lê Lợi'; k.goiYDiaChi(); await chayHen();
  await k.chonGoiY(0); await chayHen();
  la('tự điền phường theo địa chỉ', k.S.CO.phuong, '84_VN12903');
  k.S.f.addr = '5 Hai Bà'; k.goiYDiaChi(); await chayHen();
  await k.chonGoiY(1); await chayHen();
  la('địa chỉ mới ghi phường khác: đổi theo', k.S.CO.phuong, '84_VN12902');
  Object.assign(k.S.f, {name: 'A', phone: '0901234567'}); k.S.CO.dongy = true;
  await k.submitOrder();
  la('gửi đơn mang mã phường', v.gui[v.gui.length - 1].phuong, '84_VN12902');
  /* Tự lấy: giỏ mới (đơn trước đã gửi xong). */
  const e2 = moiTruong('2026-11-22T08:00:00', mang);
  const k2 = taoKho(e2.mt); await k2.napCauHinh();
  coThem(k2); k2.pick(3); k2.pickSlot(6);
  k2.S.CO.phuong = '84_VN12902'; k2.setMode('pick'); await e2.chayHen();
  Object.assign(k2.S.f, {name: 'A', phone: '0901234567'}); k2.S.CO.dongy = true;
  const kq = await k2.submitOrder();
  la('tự lấy gửi được', kq.buoc, 'xong');
  la('tự lấy: không gửi phường', [v.gui.length, v.gui[v.gui.length - 1].tu_lay, v.gui[v.gui.length - 1].phuong], [2, true, '']);
});

console.log('Bo ca kiem HANH VI trang dat banh ban Vue');
loi.forEach(d => console.log('  HONG  ' + d));
console.log(dat + ' ca dat, ' + hong + ' ca hong, tong ' + (dat + hong) + ' ca.');
process.exit(hong ? 1 : 0);

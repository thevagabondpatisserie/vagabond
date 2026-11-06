/* KHO gọi món tại bàn (v638, anh Việt duyệt 04/11/2026; v639 vòng 2 duyệt mẫu
   05/11/2026).

   Khách quét QR dán bàn: /banh?diem=TCV&ban=5&k=<16 hex>#/in-store. Link đúng
   (máy chủ kiểm khoá HMAC, goi_mon_ban.mo_ban) thì tab Tại quầy chuyển sang
   chế độ gọi món của ĐÚNG quầy đó: ô tìm món, chip theo nhóm (Bánh trên tủ,
   Trà, Cà phê, Matcha, Cacao, Kem), mỗi món một dòng có ảnh, mô tả, giá, nút
   "+"; đồ uống mở bảng chọn size (các size của cùng một tên gộp một dòng), đá
   đường, topping có giá, số lượng; thanh giỏ dưới cùng; giỏ có ghi chú, tên
   để quầy gọi, mã giới thiệu, nút Gọi món; chuông Gọi nhân viên (lý do một
   chạm). Link sai hay không có thì tab giữ chế độ xem, có banner nhắc quét QR.

   Giỏ này TÁCH khỏi giỏ đặt bánh (S.CART): đơn tại bàn trả tại quầy khi dùng
   xong, không đi Pancake. Mọi số trên màn là computed từ kho này; giá chỉ để
   hiện, máy chủ tính lại (QT-19). Phụ thuộc bên ngoài tiêm vào để bộ kiểm chạy
   được trong node với Vue thật. */
import {reactive, computed} from '../lib/vue.esm-browser.prod.js';
import * as T from '../kho/thuan.js';

export const NHIP_TRANG_THAI = 10000;
export const SL_TOI_DA = 20;
export const TOPPING_TOI_DA = 5;
/* Thứ tự chip đồ uống, trùng goi_mon_ban.NHOM_NUOC; nhãn ngắn cho chip. */
export const NHOM_NUOC = [['Trà', 'Trà'], ['Cà phê', 'Cà phê'], ['Matcha', 'Matcha'], ['Cacao', 'Cacao'], ['Ice Cream - Kem', 'Kem']];
/* Lý do bấm chuông, trùng goi_mon_ban.LY_DO_GOI (máy chủ chỉ nhận đúng các câu này). */
export const LY_DO_GOI = ['Gọi nhân viên tới bàn', 'Xin tính tiền', 'Xin thêm nước lọc, đá', 'Xin thêm dao, nĩa, khăn giấy', 'Việc khác'];

/* v642 (anh Việt 06/11/2026, mẫu 4 và 6 đã duyệt): hai cách thanh toán khi
   chưa mở trả online tại bàn. Khách chọn một, máy báo quầy qua đúng chuông
   "Xin tính tiền" (lý do LY_DO_GOI[1]); phần chi tiết nói cách trả và thông
   tin xuất hoá đơn để thu ngân chuẩn bị bill. */
export const CACH_TRA = [
  {ma: 'ban', ten: 'Nhân viên mang bill ra bàn', phu: 'Tiền mặt, chuyển khoản hoặc quẹt thẻ ngay tại bàn', chi: 'Mang bill ra bàn'},
  {ma: 'quay', ten: 'Trả tại quầy', phu: 'Quý khách ra quầy, báo số bàn với thu ngân', chi: 'Khách ra quầy trả'}];
/* Đơn còn tính tiền: bỏ đơn quầy từ chối hoặc hết hạn (quầy chưa nhận nên
   không vào bill). */
export const TT_KHONG_TINH = ['Từ chối', 'Hết hạn'];

/* Ô xuất hoá đơn điện tử (không bắt buộc): mã số thuế 10 số, 12 số, 10-3 số
   chi nhánh, hoặc email. Trả {ok, gt (đã chuẩn), cau (lỗi)}. Rỗng là hợp lệ.
   THUẦN. Cùng luật mã số thuế của màn quầy (ban_hang._chuan_mst). */
export function chuanHoaDon(v) {
  const s = String(v || '').trim();
  if (!s) return {ok: true, gt: ''};
  if (s.includes('@')) {
    const e = s.toLowerCase().replace(/\s+/g, '');
    return /^[^@\s]+@[^@\s]+\.[a-z]{2,}$/.test(e) && e.length <= 80 ? {ok: true, gt: e} : {ok: false, cau: 'Email chưa đúng dạng, ví dụ ketoan@congty.vn.'};
  }
  const so = s.replace(/[\s.]/g, '');
  if (/^\d{10}$/.test(so) || /^\d{12}$/.test(so)) return {ok: true, gt: so};
  if (/^\d{10}-?\d{3}$/.test(so)) return {ok: true, gt: so.slice(0, 10) + '-' + so.replace('-', '').slice(10)};
  return {ok: false, cau: 'Mã số thuế gồm 10 số, 12 số, hoặc 10 số - 3 số cho chi nhánh.'};
}

/* Chi tiết gửi quầy khi khách bấm Thanh toán: cách trả, rồi thông tin hoá
   đơn. Cắt đúng trần 120 ký tự của máy chủ (goi_mon_ban.DAI_CHI_TIET). THUẦN. */
export function chiTietTra(cach, hd) {
  const c = CACH_TRA.find(x => x.ma === cach);
  if (!c) return '';
  return (c.chi + (hd ? ' · Xuất hoá đơn: ' + hd : '')).slice(0, 120);
}

/* Tổng hợp các lượt gọi của bàn cho thanh đơn và màn Đơn của bàn. THUẦN theo
   G.don. Tạm tính lấy số máy chủ chốt lúc gọi; lượt bị từ chối, hết hạn
   không tính. */
export function tomDon(don) {
  const tinh = (don || []).filter(d => !TT_KHONG_TINH.includes((d.tt && d.tt.trang_thai) || 'Chờ nhận'));
  return {
    soLuot: tinh.length,
    soMon: tinh.reduce((a, d) => a + ((d.tt && d.tt.mon) || []).reduce((b, x) => b + (Number(x.sl) || 0), 0), 0),
    tamTinh: tinh.reduce((a, d) => a + (Number(d.tt && d.tt.tam_tinh) || 0), 0),
    choNhan: tinh.filter(d => ((d.tt && d.tt.trang_thai) || 'Chờ nhận') === 'Chờ nhận').length,
  };
}

/* Codex PR #545 vòng 4: trước đây chỉ lưu 10 lượt gần nhất, bàn gọi hơn mười
   lượt chưa trả mà tải lại trang thì tổng cần thanh toán hụt. Lượt còn tính
   tiền (chờ nhận, đã nhận mà bill chưa chốt) KHÔNG BAO GIỜ bị cắt; khi quá
   trần chỉ bỏ lượt cũ bị từ chối, hết hạn. Lượt đã trả đã rời G.don từ trước
   (boLuotDaTra). Trần chỉ để chặn bộ nhớ phình vô hạn. THUẦN. */
export const LUOT_LUU_TOI_DA = 200;
export function donCanLuu(don) {
  const ds = (don || []).slice();
  let thua = ds.length - LUOT_LUU_TOI_DA;
  if (thua <= 0) return ds;
  return ds.filter(d => {
    if (thua > 0 && TT_KHONG_TINH.includes((d.tt && d.tt.trang_thai) || 'Chờ nhận')) { thua -= 1; return false; }
    return true;
  });
}

/* ?diem=TCV&ban=5&k=... -> {diem, ban, k} hoặc null. THUẦN. */
export function docLinkBan(timKiem) {
  let q;
  try { q = new URLSearchParams(String(timKiem || '')); } catch (e) { return null; }
  const diem = String(q.get('diem') || '').toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 20);
  const ban = String(q.get('ban') || '').trim();
  const k = String(q.get('k') || '').trim().toLowerCase();
  if (!diem || !/^\d{1,3}$/.test(ban) || !/^[0-9a-f]{16}$/.test(k)) return null;
  return {diem, ban: Number(ban), k};
}

/* Khoá một dòng giỏ: cùng món cùng lựa chọn cùng topping thì gộp. THUẦN. */
export function khoaDong(ma, tc, tp) {
  const p = Object.keys(tc || {}).sort().filter(k => tc[k]).map(k => k + '=' + tc[k]);
  const q = (tp || []).map(x => x.ma).slice().sort();
  return ma + '|' + p.join(';') + (q.length ? '|' + q.join(',') : '');
}

/* Số đã có trong giỏ của một mã (mọi lựa chọn). THUẦN. */
export function daCo(gio, ma) { return (gio || []).filter(x => x.ma === ma).reduce((a, x) => a + x.sl, 0); }

/* Chuỗi lựa chọn hiện trên dòng giỏ, đúng thứ tự nhóm của món. THUẦN. */
export function chuTuyChon(tc, nhom) {
  return (nhom || []).map(n => (tc || {})[n.nhom]).filter(Boolean).join(', ');
}

/* Đơn giá một dòng giỏ kể cả topping. THUẦN. */
export function giaDong(x) { return (Number(x.gia) || 0) + (x.tp || []).reduce((a, t) => a + (Number(t.gia) || 0), 0); }

/* Chữ không dấu, thường, chỉ chữ số và khoảng trắng để tìm. THUẦN. */
export function chuanTim(s) {
  return String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd')
    .replace(/[^a-z0-9]+/g, ' ').trim();
}
/* Mọi từ khách gõ đều có trong tên (hoặc mô tả) món. THUẦN. */
export function khopTim(ten, moTa, q) {
  const tu = chuanTim(q).split(' ').filter(Boolean);
  if (!tu.length) return true;
  const trong = ' ' + chuanTim(ten) + ' ' + chuanTim(moTa) + ' ';
  return tu.every(x => trong.includes(x));
}

/* Tách size khỏi tên đồ uống của danh mục: "Hồng Trà Vải Thiều, Size L, Đá/Iced"
   -> {goc: "Hồng Trà Vải Thiều", size: "L", nong: false}. Tên không có size thì
   size rỗng. "Đá/Iced", "Nóng/Hot" là cách pha, bỏ khỏi tên hiện, giữ cờ nóng. THUẦN. */
export const MAU_SIZE = /,?\s*size\s*([SML]|XL)\b/i;
export function tachSize(ten) {
  let s = String(ten || '');
  const m = MAU_SIZE.exec(s);
  const size = m ? m[1].toUpperCase() : '';
  if (m) s = s.slice(0, m.index) + s.slice(m.index + m[0].length);
  const nong = /\b(?:nóng|hot)\b/i.test(s);
  s = s.replace(/,?\s*(?:đá\s*\/\s*iced|iced|nóng\s*\/\s*hot|hot)\s*$/i, '');
  s = s.replace(/\s*,\s*,/g, ',').replace(/\s+,/g, ',').replace(/\s{2,}/g, ' ').replace(/^[,\s]+|[,\s]+$/g, '');
  return {goc: s || String(ten || ''), size, nong};
}
const THU_TU_SIZE = {S: 0, M: 1, L: 2, XL: 3};
/* Gộp các size của cùng một tên thành MỘT dòng để danh sách ngắn một nửa.
   Mỗi dòng: ma (size rẻ nhất), ten gốc, bienThe [{ma, size, gia, ten}] theo
   S, M, L; gia là giá thấp nhất. Tên không size hay chỉ có một size thì giữ
   nguyên dòng, bienThe có đúng một phần tử. THUẦN. */
export function gomSize(ds) {
  const theoTen = new Map();
  for (const m of ds || []) {
    const {goc, size, nong} = tachSize(m.ten);
    /* v640: gộp size trong CÙNG một nhóm menu (quản lý có thể để M và L ở hai nhóm). */
    const k = chuanTim(goc) + (nong ? '|nong' : '') + '|' + (m.nhom_hien || '');
    if (!theoTen.has(k)) theoTen.set(k, {goc, nong, ds: []});
    theoTen.get(k).ds.push({m, size});
  }
  const ra = [];
  for (const g of theoTen.values()) {
    g.ds.sort((a, b) => (THU_TU_SIZE[a.size] ?? 9) - (THU_TU_SIZE[b.size] ?? 9) || (Number(a.m.gia) || 0) - (Number(b.m.gia) || 0));
    const bienThe = g.ds.map(x => ({ma: x.m.ma, size: x.size, gia: Number(x.m.gia) || 0, ten: x.m.ten, tp: x.m.tp, tc: x.m.tc}));
    const dau = g.ds[0].m;
    const gop = g.ds.length > 1;
    ra.push({...dau, ten: gop ? g.goc + (g.nong ? ' (nóng)' : '') : dau.ten, ma: dau.ma, gia: Math.min(...bienThe.map(b => b.gia)),
      bienThe, gop, nong: g.nong,
      mo_ta: g.ds.map(x => x.m.mo_ta).find(Boolean) || '', anh: g.ds.map(x => x.m.anh).find(Boolean) || ''});
  }
  return ra;
}

/* v640: menu đang chạy của điểm (Bán hàng > Biên tập menu) gửi kèm nhom_menu
   [{ma, ten, loai}] theo thứ tự quản lý kéo thả; mỗi đồ uống mang nhom_hien.
   Trả {nhom (chip), ds (món theo thứ tự nhóm rồi thứ tự món)}. THUẦN. */
export function theoMenu(nhomMenu, banh, nuoc, t) {
  const nhom = [{n: '', ten: t('tat_ca_muc', 'Tất cả'), so: 0}], ds = [];
  for (const g of nhomMenu || []) {
    if (g.loai === 'banh') {
      if (!banh.length) continue;
      nhom.push({n: 'banh', ten: g.ten || t('quay_chip_banh', 'Bánh trên tủ'), so: banh.length});
      ds.push(...banh.map(m => ({...m, nhomTen: g.ten || ''})));
      continue;
    }
    const cac = nuoc.filter(m => m.nhom_hien === g.ma);
    if (!cac.length) continue;
    nhom.push({n: 'g:' + g.ma, ten: g.ten, so: cac.length});
    ds.push(...cac.map(m => ({...m, nhomTen: g.ten})));
  }
  nhom[0].so = ds.length;
  return {nhom, ds};
}

/* Chip nhóm của tab Tại quầy: Tất cả, Bánh trên tủ, rồi từng nhóm đồ uống có
   món (theo nhom_goc); đồ uống không có nhom_goc (bản cũ) gom chip Đồ uống. THUẦN. */
export function chipNhom(banh, nuoc, t) {
  const nhom = [{n: '', ten: t('tat_ca_muc', 'Tất cả'), so: banh.length + nuoc.length}];
  if (banh.length) nhom.push({n: 'banh', ten: t('quay_chip_banh', 'Bánh trên tủ'), so: banh.length});
  for (const [goc, nhan] of NHOM_NUOC) {
    const so = nuoc.filter(m => m.nhom_goc === goc).length;
    if (so) nhom.push({n: 'nuoc:' + goc, ten: nhan, so});
  }
  const le = nuoc.filter(m => !NHOM_NUOC.some(([goc]) => goc === m.nhom_goc)).length;
  if (le) nhom.push({n: 'nuoc', ten: t('quay_chip_nuoc', 'Đồ uống'), so: le});
  return nhom;
}
/* v642: món thành phần của combo để hiện: "2 Trà Lài Đào (M), Canelé". THUẦN. */
export function moTaCombo(tp) {
  return (tp || []).map(x => ((Number(x.sl) || 0) > 1 ? x.sl + ' ' : '') + (x.ten || x.ma)).join(', ');
}
/* v642 (anh Việt 06/11/2026): combo cố định quầy đang chạy (máy chủ đã lọc theo
   luật bán của hoá đơn và theo bánh, nước đang bày) đứng đầu danh sách, có chip
   Combo riêng. Giá bộ do máy chủ tính, hoá đơn tự rã thành món. THUẦN. */
export function dungCombo(ds) {
  return (ds || []).filter(c => c && c.ma && Number(c.gia) > 0 && Number(c.con) > 0).map(c => ({
    ...c, loai: 'combo', con: Number(c.con) || 0, gia: Number(c.gia) || 0,
    gocHien: Number(c.goc) > Number(c.gia) ? Number(c.goc) : 0,
    mo_ta: moTaCombo(c.thanh_phan) + (c.mo_ta ? ' · ' + c.mo_ta : ''),
    bienThe: [{ma: c.ma, size: '', gia: Number(c.gia) || 0, ten: c.ten}]}));
}
function thuocChip(m, chip) {
  if (!chip) return true;
  if (chip === 'combo') return m.loai === 'combo';
  if (chip === 'banh') return m.loai === 'banh';
  if (chip.startsWith('g:')) return m.loai === 'nuoc' && m.nhom_hien === chip.slice(2);
  if (chip === 'nuoc') return m.loai === 'nuoc' && !NHOM_NUOC.some(([goc]) => goc === m.nhom_goc);
  if (chip.startsWith('nuoc:')) return m.loai === 'nuoc' && m.nhom_goc === chip.slice(5);
  return true;
}

/* Phần tab Tại quầy đang bày: quầy chọn, món theo chip và ô tìm, tổng bánh
   còn. THUẦN theo S và G. Bánh trên tủ (đếm "còn") và đồ uống (gộp size)
   chung một danh sách. Mở từ QR một bàn thì chỉ còn đúng quầy của bàn đó. */
export function dungQuayHien(S, G, t) {
  let quay = (S.STORE && S.STORE.quay) || [];
  if (G && G.ban && G.ban.ok) quay = quay.filter(q => q.ma === G.ban.diem);
  if (!quay.length) return null;
  const chon = quay.find(q => q.ma === S.quayChon) || quay[0];
  const banh = (chon.mon || []).map(m => ({...m, loai: 'banh', bienThe: [{ma: m.ma, size: '', gia: Number(m.gia) || 0, ten: m.ten}]}));
  const nuoc = gomSize((chon.do_uong || []).map(m => ({...m, loai: 'nuoc'})));
  const tim = (S.timQuay || '').trim();
  let ds, nhom;
  /* Có trường nhom_menu (kể cả mảng RỖNG: quản lý tắt hết nhóm) là đi theo menu;
     chỉ khi máy chủ bản cũ không gửi trường này mới bày kiểu cũ (Codex PR #543:
     coi mảng rỗng là bản cũ thì bánh đã tắt hiện lại cùng nút gọi món). */
  const coMenu = Array.isArray(chon.nhom_menu);
  if (coMenu) ({nhom, ds} = theoMenu(chon.nhom_menu, banh, nuoc, t));
  else { ds = banh.concat(nuoc); nhom = chipNhom(banh, nuoc, t); }
  /* Combo chỉ bày ở chế độ gọi món tại bàn (khách xem tủ bánh không cần). */
  const combo = (G && G.ban && G.ban.ok) ? dungCombo(chon.combo) : [];
  if (combo.length) {
    ds = combo.concat(ds);
    nhom.splice(1, 0, {n: 'combo', ten: t('goi_ban_chip_combo', 'Combo'), so: combo.length});
    nhom[0].so += combo.length;
  }
  /* Đầu mục "Còn N bánh" chỉ đếm bánh đang hiện theo menu. */
  const banhHien = coMenu && !chon.nhom_menu.some(g => g.loai === 'banh') ? [] : banh;
  /* Chip đang chọn không còn món (đổi quầy, bán hết) thì coi như Tất cả. */
  const chip = nhom.some(n => n.n === S.nhomQuay) ? S.nhomQuay : '';
  const mon = ds.filter(m => thuocChip(m, chip) && khopTim(m.ten, m.mo_ta, tim));
  const rong = mon.length ? '' : (tim ? 'tim' : 'het');
  return {quay, chon, mon, tong: banhHien.reduce((a, m) => a + (m.con || 0), 0), soBanh: banhHien.length, nhom, chip, tim, rong,
    topping: chon.topping || []};
}

export function taoGoiBan(moiTruong, S) {
  const {t, doc, ghi, luuTru = null, ngauNhien = null, hen = (f, ms) => setTimeout(f, ms), huyHen = id => clearTimeout(id),
    timKiem = () => '', toast = () => {}} = moiTruong;

  const G = reactive({
    link: docLinkBan(timKiem()),
    ban: null, daKiem: false,
    gio: [],
    chon: null,          // bảng chọn một món: {m, bt (biến thể đang chọn), tc, tp: {ma: 1}, sl}
    moGio: false,
    ghiChu: '', ten: '', gt: '', gtHien: '',
    nonce: '', dangGui: false, loi: '',
    don: [],             // [{ma, token, tt}]
    chuong: {mo: false, lyDo: '', chiTiet: '', dangGui: false, loi: '', xong: null, nonce: '', nonceNd: ''},
    moDon: false,        // v642: màn "Đơn của bàn"
    tra: {mo: false, cach: '', hd: '', dangGui: false, loi: '', xong: null, nonce: '', nonceNd: ''},
  });

  const khoaLuu = () => (G.link ? 'vgb-goi-ban-' + G.link.diem + '-' + G.link.ban : '');
  function luuDon() {
    if (!luuTru || !khoaLuu()) return;
    try { luuTru.setItem(khoaLuu(), JSON.stringify(donCanLuu(G.don).map(d => ({ma: d.ma, token: d.token})))); } catch (e) { /* bỏ qua */ }
  }
  function docDonLuu() {
    if (!luuTru || !khoaLuu()) return [];
    try {
      const v = JSON.parse(luuTru.getItem(khoaLuu()) || '[]');
      return Array.isArray(v) ? v.filter(d => d && /^[A-Za-z0-9-]{3,40}$/.test(d.ma || '') && /^[0-9a-f]{32}$/.test(d.token || '')) : [];
    } catch (e) { return []; }
  }

  /* Đang ở chế độ gọi món (link đúng) và quầy đang mở cửa. */
  const cheDo = computed(() => (!G.ban || !G.ban.ok) ? '' : (G.ban.mo_cua ? 'goi' : 'dong'));
  const nhanBan = computed(() => (G.ban && G.ban.ok) ? (G.ban.ten + ' · ' + t('goi_ban_ban', 'Bàn') + ' ' + G.ban.ban) : '');
  const soMon = computed(() => G.gio.reduce((a, x) => a + x.sl, 0));
  const tong = computed(() => G.gio.reduce((a, x) => a + giaDong(x) * x.sl, 0));
  const quayCua = () => ((S.STORE && S.STORE.quay) || []).find(q => G.ban && q.ma === G.ban.diem) || null;
  const toppingQuay = () => ((quayCua() || {}).topping) || [];
  /* Thanh giỏ hiện khi có món và không bảng nào đang mở (nút nổi Zalo, Grab
     nâng lên theo, xem KenhNoi). */
  const coBang = () => G.moGio || !!G.chon || G.chuong.mo || G.moDon || G.tra.mo;
  const barMo = computed(() => cheDo.value === 'goi' && G.gio.length > 0 && !coBang());
  /* v642 (anh Việt 06/11/2026: gọi xong màn co lại, không xem được đơn, không
     có chỗ tính tiền): bàn đã gọi mà giỏ trống thì thanh đơn LUÔN hiện ở đáy
     (Bàn 5 · Đã gọi n lượt · Tạm tính · Xem đơn). Giỏ có món thì thanh giỏ
     đứng chỗ đó, vì việc trước mắt là gửi món. */
  const tom = computed(() => tomDon(G.don));
  const barDon = computed(() => cheDo.value === 'goi' && G.don.length > 0 && !G.gio.length && !coBang());

  async function kiemLink() {
    if (!G.link) { G.daKiem = true; return null; }
    let m = null;
    try { m = await doc('vagabond.goi_mon_ban.mo_ban', {diem: G.link.diem, ban: G.link.ban, k: G.link.k}); } catch (e) { m = null; }
    G.ban = m && m.ok ? m : {ok: 0};
    G.daKiem = true;
    if (G.ban.ok) {
      S.quayChon = G.ban.diem; S.nhomQuay = ''; S.timQuay = '';
      G.don = docDonLuu().map(d => ({ma: d.ma, token: d.token, tt: null}));
      if (G.don.length) void hoiTrangThai();
    }
    return G.ban;
  }

  /* Món còn thêm được bao nhiêu: bánh theo số "còn", đồ uống theo trần dòng. */
  function conThem(m) {
    const da = daCo(G.gio, m.ma);
    return m.loai === 'nuoc' ? SL_TOI_DA - da : Math.min(SL_TOI_DA, Number(m.con) || 0) - da;
  }
  /* Dòng món đã có trong giỏ (size nào cũng tính): nút + tô đặc. */
  const daChon = m => G.gio.some(x => (m.bienThe || [{ma: m.ma}]).some(b => b.ma === x.ma));
  /* Đồ uống pha (không phải chai, lon) được kèm topping của quầy; v640: chỉ
     các topping menu của điểm khai cho món đó (mã trong "tp", theo size đang chọn). */
  const toppingCho = (m, bt) => {
    if (m.loai !== 'nuoc' || m.khong_pha) return [];
    const cho = (bt && Array.isArray(bt.tp)) ? bt.tp : m.tp;
    return Array.isArray(cho) ? toppingQuay().filter(x => cho.includes(x.ma)) : toppingQuay();
  };
  /* Nhóm tuỳ chọn của đúng size đang chọn: quản lý có thể tắt riêng cho size L mà
     giữ cho size M (Codex PR #543). Món không gộp size dùng tc của chính món. */
  const tcCho = (m, bt) => ((bt && Array.isArray(bt.tc)) ? bt.tc : (m.tc || []));
  /* Mức mặc định của một nhóm tuỳ chọn ("Bình thường"): sáng sẵn, không ghi lên bill. */
  const macDinh = (m, nhom, bt) => ((tcCho(m, bt).find(n => n.nhom === nhom) || {}).mac_dinh || '');
  const coBangChon = m => m.loai === 'nuoc' && ((m.bienThe || []).length > 1 || (m.tc || []).length > 0 || toppingCho(m).length > 0);
  /* Bấm "+" trên dòng: đồ uống có size, đá đường hay topping thì mở bảng chọn, còn lại thêm luôn. */
  function bamThem(m) {
    if (cheDo.value !== 'goi') return false;
    if (conThem(m) <= 0) {
      toast(m.loai === 'nuoc' ? t('goi_ban_qua_nhieu', 'Mỗi lần gọi tối đa 20 ly một món.')
        : (m.loai === 'combo' ? t('goi_ban_combo_het', 'Combo này hiện gọi được tối đa {so} bộ.', {so: Number(m.con) || 0})
          : t('goi_ban_het_con', 'Món này trên tủ chỉ còn {so}.', {so: Number(m.con) || 0})));
      return false;
    }
    if (coBangChon(m)) { moBangChon(m); return 'chon'; }
    them(m, {});
    return true;
  }
  function moBangChon(m) {
    const bt = (m.bienThe || [])[0] || {ma: m.ma, size: '', gia: Number(m.gia) || 0, ten: m.ten};
    const tc = {}, nhomTc = tcCho(m, bt);
    nhomTc.forEach(n => { if (n.mac_dinh) tc[n.nhom] = n.mac_dinh; });
    G.chon = {m, bt, tc, nhomTc, tp: {}, sl: 1, topping: toppingCho(m, bt)};
  }
  function chonBienThe(bt) {
    if (!G.chon) return;
    G.chon.bt = bt;
    /* Nhóm tuỳ chọn theo size mới: giữ mức đã chọn nếu size mới còn mức đó, nhóm
       mới thì sáng mặc định, nhóm size mới không có thì bỏ hẳn. */
    const nhomTc = tcCho(G.chon.m, bt), tc = {};
    nhomTc.forEach(n => {
      const cu = G.chon.tc[n.nhom];
      if (cu && n.lua_chon.includes(cu)) tc[n.nhom] = cu;
      else if (n.mac_dinh) tc[n.nhom] = n.mac_dinh;
    });
    G.chon.nhomTc = nhomTc;
    G.chon.tc = tc;
    G.chon.topping = toppingCho(G.chon.m, bt);
    Object.keys(G.chon.tp).forEach(ma => { if (!G.chon.topping.some(x => x.ma === ma)) delete G.chon.tp[ma]; });
  }
  /* Mỗi nhóm chọn MỘT mức; bấm lại mức đang chọn thì về mặc định. */
  function chonTc(nhom, lc) {
    if (!G.chon) return;
    const md = macDinh(G.chon.m, nhom, G.chon.bt);
    G.chon.tc[nhom] = G.chon.tc[nhom] === lc ? md : lc;
  }
  function chonTp(ma) {
    if (!G.chon) return;
    if (G.chon.tp[ma]) { delete G.chon.tp[ma]; return; }
    if (Object.keys(G.chon.tp).length >= TOPPING_TOI_DA) { toast(t('goi_ban_tp_toi_da', 'Mỗi ly tối đa 5 topping.')); return; }
    G.chon.tp[ma] = 1;
  }
  function doiSlChon(d) { if (G.chon) G.chon.sl = Math.max(1, Math.min(SL_TOI_DA, G.chon.sl + d)); }
  /* Đơn giá đang chọn trong bảng (size + topping) và tổng theo số lượng. */
  const giaChon = computed(() => {
    if (!G.chon) return 0;
    const tp = G.chon.topping.filter(x => G.chon.tp[x.ma]);
    return (Number(G.chon.bt.gia) || 0) + tp.reduce((a, x) => a + (Number(x.gia) || 0), 0);
  });
  const tongChon = computed(() => (G.chon ? giaChon.value * G.chon.sl : 0));
  function xongChon() {
    if (!G.chon) return;
    const c = G.chon;
    const tp = c.topping.filter(x => c.tp[x.ma]);
    them(c.m, c.tc, {bt: c.bt, tp, sl: c.sl});
    G.chon = null;
  }
  function them(m, tc, o = {}) {
    const bt = o.bt || (m.bienThe || [])[0] || {ma: m.ma, size: '', gia: Number(m.gia) || 0, ten: m.ten};
    /* Chỉ mang mức của nhóm mà ĐÚNG size này có (Codex PR #543). */
    const nhomTc = tcCho(m, bt), sach = {};
    nhomTc.forEach(n => {
      if (tc && tc[n.nhom] && n.lua_chon.includes(tc[n.nhom]) && tc[n.nhom] !== (n.mac_dinh || '')) sach[n.nhom] = tc[n.nhom];
    });
    const chuaCo = toppingCho(m, bt);
    const tp = (o.tp || []).filter(x => chuaCo.some(y => y.ma === x.ma)).map(x => ({ma: x.ma, ten: x.ten, gia: Number(x.gia) || 0}));
    const sl = Math.max(1, Math.min(SL_TOI_DA, Number(o.sl) || 1));
    const k = khoaDong(bt.ma, sach, tp);
    const cu = G.gio.find(x => x.khoa === k);
    const tenHien = m.ten + (bt.size ? ' (' + bt.size + ')' : '');
    if (cu) cu.sl = Math.min(SL_TOI_DA, cu.sl + sl);
    else G.gio.push({khoa: k, ma: bt.ma, ten: tenHien, gia: Number(bt.gia) || 0, sl, tc: sach, tp, nhom: nhomTc, loai: m.loai, con: m.con,
      anh: m.anh || '', thanhPhan: m.loai === 'combo' ? (m.thanh_phan || []) : null});
    if (!G.nonce) G.nonce = T.taoNonce(ngauNhien);
    G.loi = '';
    toast(t('goi_ban_da_them', 'Đã thêm {ten}', {ten: tenHien}));
  }
  function doiSl(i, d) {
    const x = G.gio[i]; if (!x) return;
    if (d > 0) {
      const m = {ma: x.ma, loai: x.loai, con: x.con};
      if (conThem(m) <= 0) return;
    }
    x.sl += d;
    if (x.sl <= 0) G.gio.splice(i, 1);
    if (!G.gio.length) G.moGio = false;
  }

  /* Mã giới thiệu: số điện thoại nhân viên. Rời ô thì hỏi tên nhân viên qua
     cửa vagabond.gioi_thieu.kiem; lỗi hay cửa chưa có thì im lặng, không bao
     giờ chặn gọi món. Cùng luật ô Mã giới thiệu của bước đặt bánh. */
  const soGt = () => { const so = String(G.gt || '').replace(/\D/g, ''); return so.length >= 8 && so.length <= 12 ? so : ''; };
  let luotGt = 0;
  async function kiemGt() {
    const so = soGt(), luot = ++luotGt;
    G.gtHien = '';
    if (!so) return;
    let m = null;
    try { m = await ghi('vagabond.gioi_thieu.kiem', {sdt: so}, {choXemThu: true}); } catch (e) { return; }
    if (luot !== luotGt || so !== soGt() || !m || typeof m !== 'object') return;
    const ten = String(m.ten || '').trim();
    G.gtHien = ten ? t('goi_ban_gt_co', 'Nhân viên giới thiệu: {ten}', {ten}) : '';
  }

  async function goiMon() {
    if (G.dangGui || cheDo.value !== 'goi' || !G.gio.length) return null;
    if (!G.nonce) G.nonce = T.taoNonce(ngauNhien);
    G.dangGui = true; G.loi = '';
    const than = {diem: G.ban.diem, ban: G.ban.ban, k: G.link.k, nonce: G.nonce,
      mon: JSON.stringify(G.gio.map(x => Object.assign({ma: x.ma, sl: x.sl, tc: x.tc}, (x.tp || []).length ? {tp: x.tp.map(y => y.ma)} : {}))),
      ghi_chu: String(G.ghiChu || '').trim().slice(0, 300), ten: String(G.ten || '').trim().slice(0, 40), sdt_gioi_thieu: soGt()};
    let m = null;
    try { m = await ghi('vagabond.goi_mon_ban.goi', than); } catch (e) { m = null; }
    G.dangGui = false;
    if (!m || !m.ok) {
      G.loi = (m && m.cau) || t('goi_ban_loi', 'Chưa gửi được. Quý khách thử lại hoặc nhắn nhân viên gần nhất.');
      if (m && m.tai_lai && moiTruong.napQuay) void moiTruong.napQuay();
      return m;
    }
    /* Chép dòng vừa gọi để màn Đơn của bàn có ngay, trước lượt hỏi trạng thái
       đầu tiên; lượt hỏi thay bằng số máy chủ. */
    const tam = G.gio.map(x => ({ten: x.ten, sl: x.sl, tc: (x.thanhPhan ? [moTaCombo(x.thanhPhan)] : [chuTuyChon(x.tc, x.nhom)]).filter(Boolean)
      .concat((x.tp || []).map(y => '+ ' + y.ten)),
      gia: giaDong(x), tien: giaDong(x) * x.sl}));
    if (!G.don.some(d => d.ma === m.ma)) G.don.push({ma: m.ma, token: m.token, tt: {trang_thai: 'Chờ nhận', mon: tam, ban: G.ban.ban, tam_tinh: tong.value, luc: ''}});
    luuDon();
    G.gio.splice(0); G.ghiChu = ''; G.nonce = ''; G.moGio = false;
    hen(() => hoiTrangThai(true), 1500);
    return m;
  }

  let henTt = null;
  /* tatCa: hỏi lại cả lượt đã xong (đã nhận), để biết bill của nó đã tính
     tiền chưa. Nhịp tự động chỉ hỏi lượt còn chờ (trần 120 lần hỏi mỗi 10
     phút của máy chủ); hỏi tất cả lúc vừa gọi thêm, mở Đơn của bàn, Thanh toán. */
  async function hoiTrangThai(tatCa = false) {
    huyHen(henTt); henTt = null;
    for (const d of G.don.slice()) {
      if (!tatCa && d.tt && ['Đã nhận', 'Từ chối', 'Hết hạn'].includes(d.tt.trang_thai) && d.xong) continue;
      let m = null;
      try { m = await doc('vagabond.goi_mon_ban.trang_thai', {ma: d.ma, token: d.token}); } catch (e) { m = null; }
      if (m && m.ok) { d.tt = m; d.xong = m.trang_thai !== 'Chờ nhận'; }
    }
    boLuotDaTra();
    if (G.don.some(d => !d.tt || d.tt.trang_thai === 'Chờ nhận')) henTt = hen(() => hoiTrangThai(), NHIP_TRANG_THAI);
  }
  /* Codex PR #545 vòng 1: khách trả bill xong rồi gọi tiếp mà không tải lại
     trang thì lượt của bill cũ không được cộng vào bill mới. Máy chủ báo
     da_tra khi phiếu tạm tính của lượt đã chốt; bỏ các lượt tới lượt đã trả
     cuối cùng (kể cả lượt bị từ chối, hết hạn đứng trước nó), lưu lại. */
  function boLuotDaTra() {
    const cuoi = G.don.map(d => !!(d.tt && d.tt.da_tra)).lastIndexOf(true);
    if (cuoi < 0) return;
    /* Lượt đứng trước lượt đã trả cuối cùng: giữ lượt còn sống (chờ nhận, đã
       nhận mà bill chưa chốt), bỏ lượt đã trả và lượt từ chối, hết hạn cũ. */
    const giu = G.don.filter((d, i) => i > cuoi || (!(d.tt && d.tt.da_tra) && !TT_KHONG_TINH.includes((d.tt && d.tt.trang_thai) || 'Chờ nhận')));
    G.don.splice(0, G.don.length, ...giu);
    luuDon();
  }
  /* Câu trạng thái một đơn cho khách. THUẦN theo đơn. */
  function cauDon(d) {
    const tt = (d.tt && d.tt.trang_thai) || 'Chờ nhận';
    if (tt === 'Đã nhận') return t('goi_ban_tt_nhan', 'Đã nhận lúc {gio}, đang pha chế', {gio: (d.tt && d.tt.nhan_luc) || ''});
    if (tt === 'Từ chối') return t('goi_ban_tt_tu_choi', 'Quầy từ chối: {ly_do}', {ly_do: (d.tt && d.tt.ly_do) || ''});
    if (tt === 'Hết hạn') return t('goi_ban_tt_het_han', 'Quầy đang bận, quý khách nhắn nhân viên gần nhất');
    return t('goi_ban_tt_cho', 'Chờ quầy nhận');
  }

  /* ---------------- đơn của bàn và thanh toán (v642) ---------------- */
  function moDon() { if (cheDo.value !== 'goi' || !G.don.length) return false; G.moDon = true; void hoiTrangThai(true); return true; }
  function dongDon() { G.moDon = false; }
  function moTra() {
    if (cheDo.value !== 'goi' || !G.don.length) return false;
    const c = G.tra;
    G.moDon = false;
    c.mo = true; c.loi = ''; c.xong = null;
    void hoiTrangThai(true);
    return true;
  }
  function dongTra() { G.tra.mo = false; }
  async function guiTra() {
    const c = G.tra;
    if (c.dangGui || cheDo.value !== 'goi') return null;
    if (!CACH_TRA.some(x => x.ma === c.cach)) { c.loi = t('goi_ban_tra_chon', 'Quý khách chọn cách thanh toán.'); return null; }
    const hd = chuanHoaDon(c.hd);
    if (!hd.ok) { c.loi = hd.cau; return null; }
    const chiTiet = chiTietTra(c.cach, hd.gt);
    const nonce = nonceTheo(c, LY_DO_GOI[1] + '|' + chiTiet);
    c.dangGui = true; c.loi = '';
    const than = {diem: G.ban.diem, ban: G.ban.ban, k: G.link.k, nonce, ly_do: LY_DO_GOI[1], chi_tiet: chiTiet};
    let m = null;
    try { m = await ghi('vagabond.goi_mon_ban.goi_nhan_vien', than); } catch (e) { m = null; }
    c.dangGui = false;
    if (!m || !m.ok) {
      c.loi = (m && m.cau) || t('goi_ban_loi', 'Chưa gửi được. Quý khách thử lại hoặc nhắn nhân viên gần nhất.');
      return m;
    }
    c.xong = {ma: m.ma, cach: c.cach, luc: m.luc || ''};
    c.nonce = ''; c.nonceNd = '';
    return m;
  }

  /* ---------------- chuông gọi nhân viên (v639) ---------------- */
  function moChuong(lyDo = '') {
    if (cheDo.value !== 'goi') return false;
    G.moDon = false; G.tra.mo = false;
    const c = G.chuong;
    c.mo = true; c.loi = ''; c.lyDo = lyDo; c.chiTiet = ''; c.xong = null;
    return true;
  }
  function dongChuong() { G.chuong.mo = false; }
  /* Nonce gắn với NỘI DUNG (lý do + chi tiết): thử lại cùng nội dung sau khi mất mạng
     thì giữ nonce để máy chủ gộp; đổi lý do thì nonce mới, máy chủ không trả nhầm
     lời cũ (Codex PR #542 vòng 1). */
  function nonceTheo(c, nd) {
    if (!c.nonce || c.nonceNd !== nd) { c.nonce = T.taoNonce(ngauNhien); c.nonceNd = nd; }
    return c.nonce;
  }
  const nonceChuong = c => nonceTheo(c, c.lyDo + '|' + String(c.chiTiet || '').trim().slice(0, 120));
  async function goiNhanVien(lyDo) {
    const c = G.chuong;
    if (c.dangGui || cheDo.value !== 'goi') return null;
    if (lyDo) c.lyDo = lyDo;
    if (!LY_DO_GOI.includes(c.lyDo)) { c.loi = t('goi_ban_chuong_chon', 'Quý khách chọn một lý do.'); return null; }
    const nonce = nonceChuong(c);
    c.dangGui = true; c.loi = '';
    const than = {diem: G.ban.diem, ban: G.ban.ban, k: G.link.k, nonce, ly_do: c.lyDo, chi_tiet: String(c.chiTiet || '').trim().slice(0, 120)};
    let m = null;
    try { m = await ghi('vagabond.goi_mon_ban.goi_nhan_vien', than); } catch (e) { m = null; }
    c.dangGui = false;
    if (!m || !m.ok) {
      c.loi = (m && m.cau) || t('goi_ban_loi', 'Chưa gửi được. Quý khách thử lại hoặc nhắn nhân viên gần nhất.');
      return m;
    }
    c.xong = {ma: m.ma, lyDo: c.lyDo, luc: m.luc || ''};
    c.nonce = ''; c.nonceNd = ''; c.chiTiet = '';
    return m;
  }

  return {G, cheDo, nhanBan, soMon, tong, barMo, quayCua, toppingQuay, macDinh, kiemLink, conThem, daChon, coBangChon, bamThem, moBangChon, chonBienThe,
    chonTc, chonTp, doiSlChon, giaChon, tongChon, xongChon, them, doiSl, kiemGt, goiMon, hoiTrangThai, cauDon, chuTuyChon,
    moChuong, dongChuong, goiNhanVien, tom, barDon, moDon, dongDon, moTra, dongTra, guiTra};
}

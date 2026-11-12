/* KHO TRẠNG THÁI của trang đặt bánh bản Vue.

   Mọi con số khách thấy (tiền bánh, ưu đãi, phí giao, tổng, ngày nhận) đều
   là computed từ MỘT nguồn trong kho này (AGENTS.md, bài học #205 điều 18).
   Trang cũ phải nhớ gọi drawCo()/drawCart()/drawBar() sau mỗi thao tác, quên
   một chỗ là số trên màn lệch nhau (lỗi tổng không đổi khi bấm +/- trong giỏ
   ở PR #460). Ở đây không có hàm "vẽ lại": đổi dữ liệu là màn tự đổi.

   Các phụ thuộc bên ngoài đều tiêm vào (đồng hồ, mạng, kho phiên, sự kiện
   quảng cáo), để bộ kiểm chạy được trong node và tua được đồng hồ. */
import {reactive, computed, watch} from '../lib/vue.esm-browser.prod.js';
import * as T from '../kho/thuan.js';
import {CONFIG, SLOTS, cakesGoc, NUMS, ADDONS, PICKUPS_GOC, LY_DO, TEN_DIEM, NHAN_MAC_DINH,
  THE_XUAT_HOA_DON, THE_BANH_TANG, DAYS, PAYS} from './du-lieu.js';
import {thuong, dam, mau, lienKet, cauCoSo, noi} from './chu-giau.js';
import {taoGoiBan, cauDn} from './kho-goi-ban.js';

const KHOA_LUU = 'vgb-gio-v1';
/* v638: bốn cách thanh toán khách chọn được. */
const PT_HOP_LE = PAYS.map(p => p.k);

export function taoKho(moiTruong) {
  const {t, tMon, doc, ghi, bayGio = () => new Date(), luuTru = null, suKien = () => {},
    ngauNhien = null, hen = (f, ms) => setTimeout(f, ms), huyHen = id => clearTimeout(id),
    xemThu = () => false, mxh = (k, d) => d, nd = {}} = moiTruong;

  const S = reactive({
    /* nhịp đồng hồ: tăng mỗi 30 giây và sau mỗi thao tác, để computed đọc
       giờ HIỆN TẠI (bài học #205: không dùng bản chụp giờ lúc tải trang). */
    nhip: 0,
    CAKES: cakesGoc(),
    TODAY: {}, TRUOC: {}, TRUOC_RF: {}, chiHien: false, tonNapXong: false, tonLoi: false, tonDaThu: false, gioTon: null,
    MUA: {co: 0, mon: []},
    STORE: {quay: []}, storeLoi: false, storeDaTai: false, quayChon: '', nhomQuay: '', timQuay: '',
    tab: 'today',
    /* lịch: ngày THẬT đã chọn (yyyy-mm-dd) là nguồn; độ lệch suy ra từ đó. */
    ngayChon: null, lechMacDinh: 2,
    pickedSlot: SLOTS.findIndex(s => s.from >= 13),
    daChonNgay: false, daChonGio: false, moLich: false, gioBiDoi: false,
    CART: [],
    gioCho: {mua: [], banh: []}, daPhucHoi: false,
    /* bảng chi tiết đang mở */
    cur: null, curSizeId: '', soLuong: 1, wish: '', nia: 0, dia: 0, thiep: 0, nums: [], adds: [], dongDangSua: -1, huongSize: false,
    muaDangXem: null,
    CO: {mode: 'ship', pickupId: 'bep-tan-son-hoa', pay: 'bank', other: false, gift: false, vat: false, dongy: false, uudai: false,
      ship: null, shipTrangThai: null, quan: '', nonce: '', daBaoDat: '', addrList: [], addrSel: -1, pickedLoc: null,
      ngoaiVung: false, uuMa: '', uu: null, uuDangHoi: null,
      /* v645 ưu đãi đơn đầu tiên trên web: bước xác thực số qua Zalo. */
      dd: {buoc: 'nut', ma: '', loi: '', bao: '', dangGui: false, lan: 0},
      /* v652: khách bấm Dùng điểm thành viên (máy chủ quyết số điểm, diem_web). */
      dungDiem: false},
    f: {phone: '', name: '', mail: '', addr: '', rname: '', rphone: '', note: '', mst: '', cname: '', cmail: '', caddr: '', ma: '', gt: ''},
    goiY: [],
    goi: {phone: null, ship: null, mst: null, gui: null, phiThuLai: false, gt: null},
    dangGui: false, guiXong: false,
    PICKUPS: PICKUPS_GOC.slice(),
    cauHinh: null, mienPhiTu: 0,
    toast: {chu: '', on: false, so: 0},
    /* lớp giao diện: đang xem danh mục, chi tiết bánh, hàng mùa hay giỏ */
    trang: 'danh_muc', anhChon: 0, nhich: 0
  });

  const tmon = (ma, truong, d) => tMon(ma, truong, d);
  const bay = () => { void S.nhip; return bayGio(); };
  const nhan = khoa => { const n = (nd.nhan || {})[khoa]; return typeof n === 'string' && n.trim() ? n : (NHAN_MAC_DINH[khoa] || ''); };
  const lyDo = k => (LY_DO[k] ? t(LY_DO[k][0], LY_DO[k][1]) : '');
  const dongHoNhich = () => { S.nhip++; };

  /* ---------------- toast ---------------- */
  let toastHen = null;
  function toast(chu) {
    S.toast.chu = chu; S.toast.on = true; S.toast.so++;
    huyHen(toastHen); toastHen = hen(() => { S.toast.on = false; }, 2200);
  }

  /* ---------------- lịch nhận ---------------- */
  const homNayIso = () => T.isoNgay(bay());
  const picked = computed(() => {
    if (!S.ngayChon) return S.lechMacDinh;
    const l = T.lechNgay(homNayIso(), S.ngayChon);
    return l === null ? S.lechMacDinh : l;
  });
  const gioNay = () => bay().getHours();
  const slotOk = (lech, s) => !!s && T.lichConHopLe(lech, s.from, gioNay(), CONFIG.prepHours, CONFIG.tomorrowFrom);
  const firstOk = lech => SLOTS.find(s => slotOk(lech, s));
  const ngayDangChon = computed(() => T.ngayTuNeo(S.ngayChon, picked.value, bay()));
  const slotDangChon = computed(() => SLOTS[S.pickedSlot]);
  const gioHopLe = computed(() => slotOk(picked.value, slotDangChon.value));
  const daChot = computed(() => T.daChotLich(S.daChonNgay, S.daChonGio));
  const hienTomTat = computed(() => T.hienTomTatLich(daChot.value, S.moLich, gioHopLe.value));
  function nhanNgayDangChon() {
    const l = T.lechNgay(homNayIso(), T.isoNgay(ngayDangChon.value));
    return T.nhanNgay(l === null ? picked.value : l, bay(), DAYS, t);
  }
  /* v646 Refill: bánh chỉ còn mẻ refill trong giỏ thì ngày ngoài khoảng có bánh
     tới nhận tới bị mờ (máy chủ vẫn chặn lại ở ton_don_web). */
  function isoNgayThu(i) { const d = new Date(bay()); d.setHours(0, 0, 0, 0); d.setDate(d.getDate() + i); return T.isoNgay(d); }
  function refillChan(i) {
    /* Codex 549 (1eefda8): dòng thêm từ tab Hôm nay lấy bánh có sẵn, không
       thuộc mẻ refill tương lai, nên không khoá ngày. */
    const iso = isoNgayThu(i);
    return S.CART.filter(o => o.nguon !== 'today').map(o => S.TRUOC_RF[o.id])
      .find(r => r && r.chi_refill && (iso < r.tu || iso > r.den)) || null;
  }
  function ngayNgan(iso) { return iso ? iso.slice(8, 10) + '/' + iso.slice(5, 7) : ''; }
  function nhanRefill(id) {
    const r = S.TRUOC_RF[id];
    return r && r.chi_refill ? t('refill_co_tu', 'Có từ {ngay}', {ngay: ngayNgan(r.tu)}) : '';
  }
  /* v649: giỏ có bánh đặt trước thì không nhận hôm nay (tách đơn). */
  const homNayBiChan = computed(() => T.chanHomNay(S.CART));
  const cauTachDon = k => k === 'co_hom_nay'
    ? t('tach_don_co_hom_nay', 'Giỏ đang có bánh có sẵn hôm nay. Bánh đặt trước nhận từ ngày mai nên đặt đơn riêng: quý khách gửi đơn đang có trước rồi đặt tiếp.')
    : k === 'co_dat_truoc'
      ? t('tach_don_co_dat_truoc', 'Giỏ đang có bánh đặt trước, nhận từ ngày mai. Bánh có sẵn hôm nay đặt đơn riêng: quý khách gửi đơn đang có trước rồi đặt tiếp.')
      : t('dat_truoc_tu_mai', 'Giỏ có bánh đặt trước nên nhận từ ngày mai. Muốn nhận bánh có sẵn hôm nay thì đặt đơn riêng.');
  const ngayRail = computed(() => {
    const goc = bay(); const ra = [];
    for (let i = 0; i < 14; i++) { const nh = T.nhanNgay(i, goc, DAYS, t); ra.push({i, ten: nh.ten, ngay: nh.ngay, on: i === picked.value, best: i >= 2, off: !!refillChan(i) || (i === 0 && homNayBiChan.value)}); }
    return ra;
  });
  /* Lịch của tab Đặt bánh trước bắt đầu từ ngày mai (Loan Anh 11/11/2026: chọn
     Hôm nay ở đây thì số hiện theo BTP của bếp, không phải bánh có trong tủ). */
  const ngayRailDatTruoc = computed(() => ngayRail.value.filter(d => d.i > 0));
  const khungRail = computed(() => SLOTS.map((s, i) => {
    const off = !slotOk(picked.value, s);
    return {i, t: s.t, off, on: i === S.pickedSlot && !off};
  }));
  function neoNgay(i) {
    const d = new Date(bay()); d.setHours(0, 0, 0, 0); d.setDate(d.getDate() + i);
    S.ngayChon = T.isoNgay(d);
  }
  function fixSlot() {
    /* Máy tự đổi khung giờ: trả true để nơi gọi hạ cờ đã chọn giờ. */
    if (slotOk(picked.value, slotDangChon.value)) return false;
    const f = firstOk(picked.value);
    S.pickedSlot = f ? SLOTS.indexOf(f) : SLOTS.length - 1;
    return true;
  }
  function pick(i) {
    if (i === 0 && homNayBiChan.value) { toast(cauTachDon('')); return; }
    const rc = refillChan(i);
    if (rc) { toast(t('refill_ngoai_khoang', 'Bánh làm theo mẻ chỉ nhận giao từ {tu} tới {den}. Quý khách chọn ngày trong khoảng này.', {tu: ngayNgan(rc.tu), den: ngayNgan(rc.den)})); return; }
    dongHoNhich(); neoNgay(i); S.daChonNgay = true; S.gioBiDoi = false;
    if (fixSlot()) { S.daChonGio = false; S.moLich = true; S.gioBiDoi = true; }
    quoteShip();
  }
  function pickSlot(i) {
    dongHoNhich();
    if (!SLOTS[i] || !slotOk(picked.value, SLOTS[i])) return;
    S.pickedSlot = i; S.daChonGio = true; S.moLich = false; S.gioBiDoi = false;
    if (!S.ngayChon) neoNgay(picked.value);
    quoteShip();
  }
  function doiLich() { S.moLich = true; }
  function mocGioNhan() {
    /* Một nguồn cho ngày giờ nhận: hỏi phí, hỏi ưu đãi và gửi đơn dùng chung. */
    const gio = String(slotDangChon.value.from).padStart(2, '0');
    return `${T.isoNgay(ngayDangChon.value)}T${gio}:00:00`;
  }
  const ghiChuDatTruoc = computed(() => {
    const d = ngayDangChon.value, p = picked.value;
    const khung = S.daChonGio && gioHopLe.value ? slotDangChon.value.t : t('chon_lai_gio', 'Vui lòng chọn khung giờ còn nhận');
    const dau = noi(thuong(t('dat_banh_c3baf86a6', 'Nhận bánh') + ' '), dam(DAYS[d.getDay()] + ' ' + T.dmy(d)), thuong(', khung '), dam(khung), thuong('.'));
    let them;
    if (p === 0) them = noi(thuong(' ' + t('dat_banh_342df54b8', 'Đơn trong ngày cần trước') + ' '), dam(t('dat_banh_ebdea35ca', '{gia_tri_a} tiếng', {gia_tri_a: CONFIG.prepHours})), thuong('.'));
    else if (p === 1) them = noi(thuong(' ' + t('dat_banh_473907822', 'Đơn cho ngày mai chỉ nhận') + ' '), dam(t('dat_banh_5d91a62f2', 'từ {gia_tri_a}h trở đi', {gia_tri_a: CONFIG.tomorrowFrom})), thuong(t('dat_banh_5551ce67c', ', vì bếp cần thời gian chuẩn bị nguyên liệu.')));
    else them = noi(thuong(' ' + t('dat_banh_62b9a66ce', 'Đặt trước từ 2 ngày là') + ' '), dam(t('dat_banh_dcc009366', 'tốt nhất')), thuong(t('dat_banh_223f30099', ', bếp chủ động được nguyên liệu và quý khách chọn được mọi khung giờ.')));
    return noi(dau, them);
  });
  const ghiChuGio = computed(() => {
    /* Dòng ghi chú dưới mục 02 của giỏ (c-prep cũ). */
    const d = ngayDangChon.value, p = picked.value, ngayQua = p < 0, hong = !gioHopLe.value;
    let ra;
    if (ngayQua) ra = [thuong(t('dat_banh_e8c542574', 'Ngày quý khách chọn lúc nãy đã qua rồi.'))];
    else if (p === 0) ra = noi(thuong(t('dat_banh_f7b357518', 'Nhận') + ' '), dam(t('dat_banh_95cee3e1c', 'hôm nay')), thuong(t('dat_banh_b3193b5f1', '. Bếp cần {gia_tri_a} tiếng nên các khung sớm hơn đã đóng.', {gia_tri_a: CONFIG.prepHours})));
    else if (p === 1) ra = noi(thuong(t('dat_banh_f7b357518', 'Nhận') + ' '), dam(t('dat_banh_02d0b5c10', 'ngày mai {gia_tri_a}', {gia_tri_a: T.dmy(d)})), thuong(t('dat_banh_90baf9c6b', ', chỉ từ {gia_tri_a}h trở đi.', {gia_tri_a: CONFIG.tomorrowFrom})));
    else ra = noi(thuong(t('dat_banh_f7b357518', 'Nhận') + ' '), dam(DAYS[d.getDay()] + ' ' + T.dmy(d)), thuong(', khung '),
      dam(S.daChonGio && gioHopLe.value ? slotDangChon.value.t : t('chon_lai_gio', 'Vui lòng chọn khung giờ còn nhận')), thuong('.'));
    if (!ngayQua) ra.push(thuong(' ' + t('dat_banh_7c2aa6fdc', 'Cả đơn được giao một lần vào khung này.')));
    if (ngayQua) ra.push(thuong(' '), dam(t('dat_banh_417ae3e9f', 'Quý khách chọn lại ngày nhận')));
    else if (hong) ra.push(thuong(' '), dam(t('dat_banh_967f3cc7d', 'Khung giờ quý khách chọn lúc nãy không còn kịp nữa, quý khách chọn lại một khung khác.')));
    if (!hong && S.gioBiDoi) ra.push(thuong(' '), dam(t('dat_banh_5ca501e79', 'Khung giờ quý khách chọn lúc nãy không dùng được cho ngày này, quý khách chọn lại một khung khác.')));
    else if (!hong && !daChot.value) ra.push(thuong(' '), dam(t('dat_banh_56b5e229a', 'Quý khách chọn cả ngày và khung giờ nhận')));
    return ra;
  });

  /* ---------------- danh mục ---------------- */
  /* Codex PR #547: máy chủ báo chi_hien (bảng Bánh trên web đang dùng) thì
     danh sách đặt trước rỗng nghĩa là KHÔNG bánh nào được hiện, không được
     quay về danh mục mặc định (làm lộ bánh Marketing đang ẩn). */
  const coTruoc = computed(() => S.chiHien || Object.keys(S.TRUOC).length > 0);
  const banhHomNay = computed(() => S.CAKES.filter(c => c.sizes.some(s => S.TODAY[s.id] > 0)));
  const banhDatTruoc = computed(() => coTruoc.value ? S.CAKES.filter(c => c.sizes.some(s => S.TRUOC[s.id] > 0)) : S.CAKES);
  const tongTon = computed(() => Object.values(S.TODAY).reduce((a, b) => a + b, 0));
  function kichThuocDangBan(c, tab = S.tab) {
    const bang = tab === 'today' ? S.TODAY : S.TRUOC;
    const loc = tab === 'today' ? Object.keys(bang).length > 0 : coTruoc.value;
    return loc ? c.sizes.filter(s => bang[s.id] > 0) : c.sizes;
  }
  const dongTrangThai = computed(() => {
    /* "13 bánh có sẵn · nhận từ 13h - 15h · cập nhật 09:59". */
    const f = firstOk(0), b = bay();
    const ra = [];
    if (S.tonNapXong) ra.push(cauCoSo(nhan('cau_co_san'), {so: tongTon.value}));
    ra.push(f ? cauCoSo(nhan('cau_nhan_tu'), {khung: f.t}) : cauCoSo(nhan('cau_het_khung'), {}));
    return {phan: ra, gio: S.gioTon || (String(b.getHours()).padStart(2, '0') + ':' + String(b.getMinutes()).padStart(2, '0'))};
  });
  const ghiChuHomNay = computed(() => {
    const f = firstOk(0);
    return f ? cauCoSo(nhan('cau_chuan_bi'), {gio: CONFIG.prepHours, khung: f.t}) : cauCoSo(nhan('cau_chuan_bi_het'), {});
  });
  function theBanh(c, cheDo) {
    /* Dữ liệu của MỘT thẻ bánh (card cũ), dùng chung cho hôm nay và đặt trước. */
    const homNay = cheDo === 'today';
    const avail = c.sizes.filter(s => S.TODAY[s.id] > 0);
    const truocSz = coTruoc.value ? c.sizes.filter(s => S.TRUOC[s.id] > 0) : c.sizes;
    const banh = t('dat_banh_3556aabb5', 'bánh');
    const chips = homNay
      ? avail.map(s => ({chu: (s.cm ? s.cm + 'cm' : t('dat_banh_8a6c6356d', '1 cỡ')) + ' · ' + T.nhanTon(S.TODAY[s.id], banh, t), co: true}))
      : truocSz.map(s => {
        const nh = coTruoc.value ? T.nhanTon(S.TRUOC[s.id], banh, t) : '';
        return {chu: (s.cm ? s.cm + 'cm' : t('dat_banh_8a6c6356d', '1 cỡ')) + (nh ? ' · ' + nh : ''), co: coTruoc.value};
      });
    const gia = homNay ? T.tienVN(Math.min(...avail.map(s => s.p)))
      : t('dat_banh_c826c3782', 'từ') + ' ' + T.tienVN(Math.min(...(truocSz.length ? truocSz : c.sizes).map(s => s.p)));
    const ma = c.sizes[0].id;
    return {c, ten: tmon(ma, 'ten', c.k), nhanMua: tmon(ma, 'theo_mua', c.seasonal), gia, chips, vi: T.laChuViet(c.k), homNay};
  }

  /* ---------------- bảng chi tiết bánh ---------------- */
  const curSize = computed(() => S.cur ? (S.cur.sizes.find(s => s.id === S.curSizeId) || null) : null);
  function moBanh(c) {
    S.cur = c; S.soLuong = 1; S.wish = ''; S.nia = 0; S.dia = 0; S.thiep = 0; S.nums = []; S.adds = []; S.huongSize = false;
    const avail = kichThuocDangBan(c);
    S.curSizeId = (avail[0] || c.sizes[0]).id;
    suKien('ViewContent', {content_ids: c.sizes.map(s => s.id), content_type: 'product', content_name: c.k,
      value: Math.min(...c.sizes.map(s => s.p || 0)), currency: 'VND'});
  }
  function dongBanh() { S.cur = null; S.dongDangSua = -1; }
  function setSize(id) { if (S.cur && S.cur.sizes.some(s => s.id === id)) S.curSizeId = id; }
  function doiSoLuong(d) { S.soLuong = Math.max(1, S.soLuong + d); }
  function toggleNum(n) { if (S.nums.length < 3) S.nums.push(n); }
  function clearNums() { S.nums = []; }
  function toggleAdd(id) { const i = S.adds.indexOf(id); if (i >= 0) S.adds.splice(i, 1); else S.adds.push(id); }
  const phuKienChon = computed(() => {
    const ra = [];
    S.nums.forEach(n => { const x = NUMS.find(z => z.n === n); ra.push({n: t('dat_banh_909dfa9ae', 'Nến số') + ' ' + n, id: x.id, p: x.p}); });
    ADDONS.filter(a => S.adds.includes(a.id)).forEach(a => ra.push({n: t(a.k, a.n), id: a.id, p: a.p}));
    return ra;
  });
  const tienNutThem = computed(() => curSize.value ? (curSize.value.p + phuKienChon.value.reduce((a, x) => a + x.p, 0)) * S.soLuong : 0);
  function gioiHanNhan(id, nguon) {
    /* Số còn nhận theo ô Dư decor; mã ngoài danh mục decor thì không giới hạn.
       Codex 549 (1eefda8): bánh có mẻ refill thì ngày nhận đang chọn nằm trong
       khoảng refill (hoặc bánh chỉ còn refill) lấy số còn của refill.
       Codex 549 (58ba797): dòng lấy từ tab Hôm nay giới hạn theo số có sẵn hôm
       nay, không theo mẻ refill tương lai. */
    if (nguon === 'today') return S.TODAY[id] || 0;
    if (!coTruoc.value) return 0;
    const r = S.TRUOC_RF[id];
    if (r) {
      const iso = isoNgayThu(picked.value);
      if (r.chi_refill || (iso >= r.tu && iso <= r.den)) return r.con || 0;
    }
    return S.TRUOC[id] || 0;
  }
  const daCo = id => T.daCoTrongGio(S.CART, id);
  const tenMonGio = o => tmon(o.id, 'ten', o.k);
  function addToCart() {
    const c = S.cur, sz = curSize.value;
    if (!c || !sz) return false;
    if (!kichThuocDangBan(c).some(s => s.id === sz.id)) { toast(t('het_size', 'Kích thước này hiện chưa nhận đặt. Quý khách chọn kích thước khác.')); return false; }
    const xd = T.xungDotGio(S.CART, {cm: sz.cm, nguon: S.tab === 'today' ? 'today' : 'order'}, S.dongDangSua);
    if (xd) { toast(cauTachDon(xd)); return false; }
    const gh = gioiHanNhan(sz.id, S.tab === 'today' ? 'today' : 'order');
    const dangSua = S.dongDangSua >= 0 && S.CART[S.dongDangSua] && S.CART[S.dongDangSua].id === sz.id ? S.CART[S.dongDangSua].qty : 0;
    if (gh && daCo(sz.id) - dangSua + S.soLuong > gh) {
      toast(t('dat_banh_04267831d', 'Size này chỉ còn nhận {gia_tri_a} bánh trong 3 ngày tới. Cần nhiều hơn quý khách gọi 0931 224 334', {gia_tri_a: gh}));
      return false;
    }
    const o = {k: c.k, img: c.img, id: sz.id, cm: sz.cm, price: sz.p, nguon: S.tab === 'today' ? 'today' : 'order',
      wish: (S.wish || '').trim(), adds: phuKienChon.value.map(x => ({...x})), qty: S.soLuong,
      dung_cu: T.chuanDungCu({nia: S.nia, dia: S.dia, thiep: S.thiep})};
    if (S.dongDangSua >= 0) {
      S.CART.splice(S.dongDangSua, 1, o); S.dongDangSua = -1;
      toast(t('gio_da_sua', 'Đã cập nhật bánh trong giỏ'));
      return 'sua';
    }
    const hit = T.themVaoGio(S.CART, o);
    suKien('AddToCart', {content_ids: [o.id], content_type: 'product', value: T.lineUnit(o) * o.qty, currency: 'VND'});
    toast(hit ? t('them_so_luong_banh', 'Đã thêm {so} bánh, giỏ có {tong} bánh', {so: o.qty, tong: T.cartCount(S.CART)})
      : t('dat_banh_01548bfbc', 'Đã thêm {gia_tri_a} vào giỏ', {gia_tri_a: tenMonGio(o)}));
    return 'them';
  }
  function themNhanh(c, cheDo) {
    /* Nút "+" trên thẻ: chỉ thêm thẳng khi bánh có ĐÚNG MỘT size đang bán;
       nhiều size thì mở chi tiết cho khách chọn (trả 'mo'). */
    const ds = cheDo === 'today' ? c.sizes.filter(s => S.TODAY[s.id] > 0) : (coTruoc.value ? c.sizes.filter(s => S.TRUOC[s.id] > 0) : c.sizes);
    if (ds.length !== 1) return 'mo';
    const sz = ds[0], gh = gioiHanNhan(sz.id, cheDo === 'today' ? 'today' : 'order');
    const xd = T.xungDotGio(S.CART, {cm: sz.cm, nguon: cheDo === 'today' ? 'today' : 'order'});
    if (xd) { toast(cauTachDon(xd)); return 'chan'; }
    if (gh && daCo(sz.id) >= gh) {
      toast(t('dat_banh_04267831d', 'Size này chỉ còn nhận {gia_tri_a} bánh trong 3 ngày tới. Cần nhiều hơn quý khách gọi 0931 224 334', {gia_tri_a: gh}));
      return 'chan';
    }
    const o = {k: c.k, img: c.img, id: sz.id, cm: sz.cm, price: sz.p, nguon: cheDo === 'today' ? 'today' : 'order', wish: '', adds: [], qty: 1};
    T.themVaoGio(S.CART, o);
    suKien('AddToCart', {content_ids: [o.id], content_type: 'product', value: T.lineUnit(o) * o.qty, currency: 'VND'});
    toast(t('dat_banh_7e42d2e7b', 'Đã thêm {gia_tri_a}{gia_tri_b}. Vào giỏ, chọn Sửa bánh để thêm lời chúc, phụ kiện.', {gia_tri_a: tenMonGio(o), gia_tri_b: sz.cm ? ' ' + sz.cm + 'cm' : ''}));
    return 'them';
  }
  function suaDongGio(i) {
    /* Mở lại chi tiết bánh với đúng cấu hình của dòng giỏ. Trả về bánh để
       lớp điều hướng mở đúng đường dẫn. */
    const o = S.CART[i]; if (!o) return null;
    const c = S.CAKES.find(x => x.sizes.some(s => s.id === o.id)); if (!c) return null;
    S.tab = o.nguon || (S.TODAY[o.id] > 0 ? 'today' : 'order');
    moBanh(c);
    S.dongDangSua = i; S.soLuong = o.qty; S.curSizeId = o.id;
    S.wish = o.wish || ''; const dc = T.chuanDungCu(o.dung_cu); S.nia = dc.nia; S.dia = dc.dia; S.thiep = dc.thiep;
    S.nums = o.adds.map(a => NUMS.find(n => n.id === a.id)?.n).filter(n => n !== undefined);
    S.adds = o.adds.filter(a => !NUMS.some(n => n.id === a.id)).map(a => a.id);
    return c;
  }

  /* ---------------- giỏ ---------------- */
  const soBanh = computed(() => T.cartCount(S.CART));
  const tienBanh = computed(() => T.cartTotal(S.CART));
  function cartQty(i, d) {
    const o = S.CART[i]; if (!o) return;
    if (d > 0) {
      const gh = o.cm === 0 ? 0 : gioiHanNhan(o.id, o.nguon);
      const m = o.cm === 0 ? (S.MUA.mon || []).find(x => x.ma === o.id) : null;
      if (gh && daCo(o.id) >= gh) { toast(t('dat_banh_abecb98cf', 'Size này chỉ còn nhận {gia_tri_a} bánh trong 3 ngày tới.', {gia_tri_a: gh})); return; }
      if (m && daCo(o.id) >= m.con) { toast(t('dat_banh_3b1a7e8cc', 'Mùa này chỉ còn') + ' ' + m.con + ' ' + t('dat_banh_5faac70d7', 'phần. Cần nhiều hơn quý khách gọi 0931 224 334')); return; }
    }
    o.qty += d;
    if (o.qty <= 0) S.CART.splice(i, 1);
  }
  function cartRemove(i) { S.CART.splice(i, 1); }
  const dongGio = computed(() => S.CART.map((o, i) => {
    const ex = [];
    const dc = o.dung_cu || {};
    const chuDc = [(dc.nia || dc.dia) ? t('dung_cu_gio', '{nia} nĩa gỗ, {dia} dĩa bã mía', {nia: dc.nia || 0, dia: dc.dia || 0}) : '',
      dc.thiep ? t('dung_cu_thiep_gio', '{so} thiệp nhỏ', {so: dc.thiep}) : ''].filter(Boolean).join(', ');
    if (chuDc) ex.push([thuong(chuDc)]);
    if (o.wish) ex.push([thuong(t('dat_banh_1970655ae', 'Lời chúc:') + ' '), {chu: o.wish, nghieng: true}]);
    if (o.adds.length) ex.push([thuong(t('dat_banh_2c04193c6', 'Thêm: {gia_tri_a}', {gia_tri_a: o.adds.map(a => a.n).join(', ')}))]);
    return {i, o, ten: tenMonGio(o), phu: t('dat_banh_7498bc8a8', 'Ø {gia_tri_a}cm · mã {gia_tri_b}', {gia_tri_a: o.cm, gia_tri_b: o.id}),
      ex, tien: T.tienVN(T.lineUnit(o) * o.qty)};
  }));

  /* ---------------- ưu đãi (v589) ---------------- */
  const sdtUuDai = () => { const v = (S.f.phone || '').replace(/\D/g, ''); return v.length >= 9 ? v : ''; };
  const ngayUuDai = () => { try { return mocGioNhan(); } catch (e) { return ''; } };
  /* Số giảm tuỳ giỏ, mã, số điện thoại (lượt mỗi khách) và ngày nhận (lượt
     mỗi ngày): bốn thứ nằm trong khoá, đổi là hỏi lại (Codex #460). */
  /* v645: thêm lượt xác thực số (S.CO.dd.lan): xác thực xong thì hỏi lại để máy chủ thấy phiên. */
  const khoaUuDai = computed(() => JSON.stringify([T.hangGui(S.CART), S.CO.uuMa || '', sdtUuDai(), ngayUuDai(), S.CO.dd.lan, !!S.CO.dungDiem]));
  const uuHienTai = computed(() => (S.CO.uu && S.CO.uu.khoa === khoaUuDai.value ? S.CO.uu : null));
  const giam = computed(() => (uuHienTai.value ? (Number(uuHienTai.value.giam) || 0) : 0));
  async function xemUuDai() {
    const khoa = khoaUuDai.value;
    S.CO.uuDangHoi = khoa;
    if (!S.CART.length) return;
    let m = null;
    try {
      m = await ghi('vagabond.don_hang.xem_uu_dai', {don: JSON.stringify({items: T.hangGui(S.CART), ma_uu_dai: S.CO.uuMa || '', dien_thoai: sdtUuDai(), ngay_nhan: ngayUuDai(), dung_diem: S.CO.dungDiem ? 1 : 0})});
    } catch (e) { m = null; }
    if (S.CO.uuDangHoi !== khoa) return; /* đã có lần hỏi mới hơn */
    S.CO.uu = {khoa, giam: (m && m.ok) ? (Number(m.giam) || 0) : 0, ap: (m && m.ok && m.ap) || [],
      dd: (m && m.don_dau && typeof m.don_dau === 'object') ? m.don_dau : null,
      diem: (m && m.ok && m.diem && typeof m.diem === 'object') ? m.diem : null,
      loi: (m && !m.ok && m.ly_do === 'ma_uu_dai') ? String(m.chi_tiet || '') : ((!m && S.CO.uuMa) ? t('dat_banh_ma_chua_kiem', 'Chưa kiểm được mã lúc này, quý khách thử lại sau ít phút.') : '')};
  }
  let uuHen = null;
  /* Giỏ, mã, số, ngày đổi khi giỏ đang mở thì hỏi lại sau 300ms (bấm +/- liên
     tục chỉ hỏi một lần). Theo dõi khoá thay cho việc nhớ gọi ở từng chỗ. */
  let gioDangMo = false;
  function hoiUuDaiNeuCan() {
    if (!gioDangMo || !S.CART.length || xemThu()) return;
    if (uuHienTai.value || S.CO.uuDangHoi === khoaUuDai.value) return;
    huyHen(uuHen); S.CO.uuDangHoi = khoaUuDai.value; uuHen = hen(xemUuDai, 300);
  }
  watch(khoaUuDai, hoiUuDaiNeuCan);
  function apMaUuDai() {
    S.CO.uuMa = String(S.f.ma || '').trim().toUpperCase();
    S.f.ma = S.CO.uuMa; S.CO.uu = null; S.CO.uuDangHoi = null;
    hoiUuDaiNeuCan();
  }
  const goiYMa = computed(() => {
    const u = uuHienTai.value;
    if (!u) return S.CO.uuMa ? [thuong(t('dat_banh_dang_kiem_ma', 'Đang kiểm mã...'))] : [];
    if (u.loi) return [dam(u.loi, 'do')];
    if (u.giam > 0) return [dam(t('dat_banh_da_giam_con', 'Đã giảm {tien}, còn {tong}', {tien: T.tienVN(u.giam), tong: T.tienVN(tong.value.total)}), 'cyan'), thuong(' · ' + u.ap.map(a => a.ten).join(', '))];
    return S.CO.uuMa ? [thuong(t('dat_banh_ma_chua_giam', 'Mã hợp lệ nhưng đơn chưa đủ điều kiện giảm.'))] : [];
  });

  /* ---------------- ưu đãi đơn đầu tiên trên web (v645) ----------------
     Anh Việt duyệt mẫu 08/11/2026. Số khách gõ chưa từng có đơn web thì máy
     tự giảm 50.000 đ sau khi khách xác thực số qua mã Zalo (cùng phiên Thành
     viên: thanh_vien.gui_ma, xac_thuc). Không cộng với mã: máy chủ giữ cái
     lớn hơn. Số giảm luôn do máy chủ tính (xem_uu_dai, tao_don). */
  /* Anh Việt 08/11 (bản 2): màn Khuyến mãi trong app chọn có hiện thẻ ở bước
     thanh toán không (dd.hien) và có bắt mã Zalo không (dd.can_otp). Tắt thẻ
     thì ưu đãi vẫn trừ vào tổng tiền như mọi ưu đãi khác, chỉ không có thẻ.
     Thiếu hai cờ (máy chủ cũ) thì hiểu như bản duyệt mẫu: hiện, bắt mã. */
  const theDonDau = computed(() => {
    const u = uuHienTai.value;
    const dd = u && u.dd;
    if (!dd || !sdtUuDai() || dd.hien === 0 || dd.hien === '0') return null;
    const giam = Number(dd.giam) || 0;
    const tien = T.tienVN(giam);
    const ic = '-' + (giam && giam % 1000 === 0 ? (giam / 1000) + 'K' : tien);
    const coOtp = !(dd.can_otp === 0 || dd.can_otp === '0');
    const kq = theDonDauTho(dd, tien, coOtp);
    return kq ? Object.assign({ic}, kq) : null;
  });
  function theDonDauTho(dd, tien, coOtp) {
    switch (dd.trang_thai) {
      case 'chua_du_tien':
        return {kieu: 'goi_y', tieu: t('dat_banh_dd_tieu_goi_y', 'Đơn đầu tiên trên web được giảm {tien}', {tien}),
          phu: t('dat_banh_dd_chua_du', 'Áp cho tiền bánh từ {toi_thieu}. Thêm bánh để nhận ưu đãi.', {toi_thieu: T.tienVN(Number(dd.toi_thieu) || 0)})};
      case 'can_xac_thuc':
        return {kieu: 'xac_thuc', tieu: S.CO.dd.buoc === 'ma' ? t('dat_banh_dd_tieu_nhap_ma', 'Nhập mã 6 số Zalo vừa gửi')
          : t('dat_banh_dd_tieu', 'Giảm {tien} cho đơn đầu tiên trên web', {tien}),
          phu: S.CO.dd.buoc === 'ma' ? t('dat_banh_dd_phu_ma', 'Mã gửi tới Zalo của số {so}, có hiệu lực 5 phút.', {so: sdtUuDai()})
            : t('dat_banh_dd_phu', 'Số {so} chưa từng đặt bánh trên web. Xác thực số điện thoại qua Zalo để nhận ưu đãi.', {so: sdtUuDai()})};
      case 'du':
        if (Number(dd.ap_dung)) {
          if (!coOtp) {
            return {kieu: 'da_ap', tieu: t('dat_banh_dd_da_giam', 'Đã giảm {tien} cho đơn đầu tiên', {tien}),
              phu: Number(dd.bo_ma) ? t('dat_banh_dd_bo_ma_ko_otp', 'Mã ưu đãi quý khách nhập giảm ít hơn nên máy giữ ưu đãi đơn đầu tiên (không cộng chung).')
                : t('dat_banh_dd_da_giam_ko_otp', 'Số {so} chưa từng đặt bánh trên web. Ưu đãi đã trừ vào tổng tiền bên dưới.', {so: sdtUuDai()})};
          }
          return {kieu: 'da_ap', tieu: t('dat_banh_dd_da_giam', 'Đã giảm {tien} cho đơn đầu tiên', {tien}),
            phu: Number(dd.bo_ma) ? t('dat_banh_dd_bo_ma', 'Đã xác thực số {so}. Mã ưu đãi quý khách nhập giảm ít hơn nên máy giữ ưu đãi đơn đầu tiên (không cộng chung).', {so: sdtUuDai()})
              : t('dat_banh_dd_da_giam_phu', 'Đã xác thực số {so}. Ưu đãi đã trừ vào tổng tiền bên dưới.', {so: sdtUuDai()})};
        }
        return {kieu: 'goi_y', tieu: t('dat_banh_dd_ma_lon_hon', 'Mã ưu đãi đang giảm nhiều hơn {tien}', {tien}),
          phu: t('dat_banh_dd_ma_lon_hon_phu', 'Ưu đãi đơn đầu tiên không cộng chung với mã khác; máy giữ mức giảm lớn hơn cho quý khách.')};
      default:
        return null;
    }
  }
  /* Câu lỗi đăng nhập dùng chung với trang gọi món tại bàn (cauDn), trừ hai
     câu nhắc "nhờ thu ngân": khách web không đứng ở quầy. */
  const cauLoiDd = ly => (ly === 'khong_gui_duoc' || ly === 'chua_mo'
    ? t('dat_banh_dd_khong_gui', 'Chưa gửi được mã qua Zalo. Quý khách thử lại sau ít phút.') : cauDn(ly, t));
  async function guiMaDonDau() {
    const c = S.CO.dd;
    const so = sdtUuDai();
    if (c.dangGui || !so) return null;
    c.dangGui = true; c.loi = ''; c.bao = '';
    let m = null;
    try { m = await ghi('vagabond.thanh_vien.gui_ma', {sdt: so}); } catch (e) { m = null; }
    c.dangGui = false;
    if (!m || !m.ok) { c.loi = cauLoiDd(m && m.ly_do) || t('dat_banh_dd_chua_gui', 'Chưa gửi được mã. Quý khách thử lại sau.'); return m; }
    c.buoc = 'ma'; c.ma = '';
    c.bao = t('dat_banh_dd_da_gui', 'Đã gửi mã qua Zalo.');
    return m;
  }
  async function xacThucDonDau() {
    const c = S.CO.dd;
    if (c.dangGui) return null;
    const ma = String(c.ma || '').replace(/\D/g, '');
    if (ma.length !== 6) { c.loi = t('dat_banh_dd_ma_6', 'Mã gồm 6 số trong tin nhắn Zalo.'); return null; }
    c.dangGui = true; c.loi = '';
    let m = null;
    try { m = await ghi('vagabond.thanh_vien.xac_thuc', {sdt: sdtUuDai(), ma}); } catch (e) { m = null; }
    c.dangGui = false;
    if (!m || !m.ok) { c.loi = cauLoiDd(m && m.ly_do) || t('dat_banh_dd_chua_xac', 'Không xác thực được. Gửi mã mới.'); return m; }
    /* Hỏi lại ưu đãi: máy chủ đọc phiên vừa mở và trả số giảm. */
    c.buoc = 'nut'; c.ma = ''; c.bao = ''; c.lan += 1;
    return m;
  }
  /* Đổi số điện thoại thì quay về bước đầu (mã đã gửi là của số cũ). */
  watch(sdtUuDai, () => { const c = S.CO.dd; c.buoc = 'nut'; c.ma = ''; c.loi = ''; c.bao = ''; S.CO.dungDiem = false; });

  /* ---------------- điểm thành viên (v652) ----------------
     Anh Việt chốt 12/11/2026: khách online dùng điểm ở bước thanh toán, xác thực
     số qua Zalo (cùng phiên Thành viên với ưu đãi đơn đầu). Máy chủ quyết số điểm
     (tối đa 50% tiền bánh sau ưu đãi, bill còn tối thiểu); trình duyệt chỉ hiện.
     Xác thực xong thì máy chủ mới trả số dư: không cho đọc điểm của số khác. */
  const soDiem = v => (Number(v) || 0).toLocaleString('vi-VN');
  const theDiem = computed(() => {
    const u = uuHienTai.value;
    const so = sdtUuDai();
    if (!so || !u || !u.diem) return null;
    const d = u.diem;
    const lh = d.len_hang && Number(d.len_hang.con_thieu) > 0 && d.len_hang.hang_tiep
      ? t('dat_banh_dv_len_hang', 'Mua thêm {tien} trong {thang} tháng để lên hạng {hang}.', {tien: T.tienVN(Number(d.len_hang.con_thieu)), thang: d.len_hang.so_thang || 12, hang: d.len_hang.hang_tiep}) : '';
    const coThe = !!theDonDau.value && theDonDau.value.kieu === 'xac_thuc';
    switch (d.trang_thai) {
      case 'can_xac_thuc':
        return {kieu: coThe ? 'goi_y' : 'xac_thuc', tieu: t('dat_banh_dv_tieu', 'Dùng điểm thành viên'),
          phu: coThe ? t('dat_banh_dv_xac_tren', 'Xác thực số ở thẻ phía trên là xem được điểm của số {so}.', {so})
            : (S.CO.dd.buoc === 'ma' ? t('dat_banh_dd_phu_ma', 'Mã gửi tới Zalo của số {so}, có hiệu lực 5 phút.', {so})
              : t('dat_banh_dv_xac', 'Xác thực số {so} qua Zalo để xem và dùng điểm cho đơn này.', {so})), lh: ''};
      case 'khong_co':
        return {kieu: 'goi_y', tieu: t('dat_banh_dv_moi', 'Đơn này sẽ tích điểm cho số {so}', {so}),
          phu: t('dat_banh_dv_moi_phu', 'Số này chưa có điểm. Nhận bánh xong, điểm vào tài khoản thành viên.'), lh: ''};
      case 'cam':
        return {kieu: 'goi_y', tieu: t('dat_banh_dv_cam', 'Hạng của quý khách đã có ưu đãi giảm thẳng'),
          phu: t('dat_banh_dv_cam_phu', 'Hạng này không dùng điểm. Nhân viên áp mức giảm của hạng khi xác nhận đơn.'), lh};
      case 'chua_du':
        return {kieu: 'goi_y', tieu: t('dat_banh_dv_co', 'Quý khách có {diem} điểm', {diem: soDiem(d.so_du)}),
          phu: t('dat_banh_dv_chua_du', 'Đơn này chưa dùng được điểm (tối đa một nửa tiền bánh, bill còn lại tối thiểu).'), lh};
      case 'dung_duoc':
        if (Number(d.dung) > 0) {
          return {kieu: 'da_ap', tieu: t('dat_banh_dv_da', 'Đã dùng {diem} điểm, giảm {tien}', {diem: soDiem(d.dung), tien: T.tienVN(Number(d.tien))}),
            phu: t('dat_banh_dv_con', 'Còn {con} điểm sau đơn này. Đơn không thành thì điểm tự hoàn.', {con: soDiem(Math.max(0, Number(d.so_du) - Number(d.dung)))}), lh, bo: true};
        }
        return {kieu: 'dung', tieu: t('dat_banh_dv_co', 'Quý khách có {diem} điểm', {diem: soDiem(d.so_du)}),
          phu: t('dat_banh_dv_dung_duoc', 'Đơn này dùng được {diem} điểm, giảm {tien}. Điểm trừ sau mọi ưu đãi, chỉ trên tiền bánh.', {diem: soDiem(d.toi_da), tien: T.tienVN(Number(d.tien_toi_da) || 0)}), lh};
      default:
        return null;
    }
  });
  function dungDiem(co) {
    S.CO.dungDiem = !!co;
    S.CO.uu = null; S.CO.uuDangHoi = null;
    hoiUuDaiNeuCan();
  }

  /* ---------------- phí giao ---------------- */
  /* v652: điểm thành viên là phần trả bằng điểm, không làm đơn mất miễn phí giao
     (máy chủ xét ngưỡng trên tiền bánh sau ưu đãi, chưa trừ điểm). */
  const tienDiem = computed(() => (uuHienTai.value && uuHienTai.value.diem ? (Number(uuHienTai.value.diem.tien) || 0) : 0));
  const mienPhi = computed(() => T.laMienPhi(tienBanh.value - (giam.value - tienDiem.value), S.mienPhiTu));
  const timQuan = ma => (!ma ? null : (((S.cauHinh && S.cauHinh.quan) || []).find(q => q.ma === ma) || null));
  let soPhi = 0, phiHen = null;
  const goiYPhiGoc = () => [thuong(t('dat_banh_e347a8e6c', 'Chọn khu vực hoặc gõ địa chỉ, hệ thống báo phí giao dự kiến.'))];
  function quoteShip() {
    const a = (S.f.addr || '').trim();
    S.CO.ngoaiVung = false; S.goi.phiThuLai = false;
    if (S.CO.mode !== 'ship') { S.CO.ship = 0; S.CO.shipTrangThai = null; return; }
    const q = timQuan(S.CO.quan), duDai = a.length >= 8;
    if (!duDai && !q) { soPhi++; S.CO.ship = null; S.CO.shipTrangThai = null; S.goi.ship = goiYPhiGoc(); return; }
    const kieu = duDai ? 'chinh_xac' : 'du_kien';
    const so = ++soPhi;
    S.goi.ship = [mau(t('dat_banh_9e52d8e6b', 'Đang hỏi phí giao...'), 'cyan')];
    huyHen(phiHen);
    phiHen = hen(async () => {
      let m = null;
      try {
        const p = duDai ? (S.CO.pickedLoc ? {lat: S.CO.pickedLoc.lat, lng: S.CO.pickedLoc.lng, addr: a} : {addr: a})
          : {lat: q.lat, lng: q.lng, addr: q.ten + t('dat_banh_ddfe89cb9', ', TP. Hồ Chí Minh')};
        p.luc_giao = mocGioNhan();
        m = await doc('vagabond.giao_hang.phi_giao', p);
      } catch (e) { m = null; }
      if (so !== soPhi) return; /* kết quả của lần hỏi cũ về muộn: bỏ */
      apPhiGiao(m, kieu, q);
    }, duDai ? 700 : 0);
  }
  function apPhiGiao(m, kieu, q) {
    const mp = mienPhi.value;
    if (m && m.ly_do === 'ngoai_vung_giao') {
      S.CO.ship = null; S.CO.shipTrangThai = 'chua_ro';
      if (kieu === 'du_kien') {
        S.goi.ship = noi(thuong(t('dat_banh_bb3c6100a', 'Một phần khu vực') + ' '), dam(q ? q.ten : ''), thuong(' ' + t('dat_banh_aeed77c8c', 'nằm ngoài bán kính giao bánh kem. Quý khách gõ địa chỉ để chúng tôi kiểm tra chính xác.')));
        return;
      }
      S.CO.ngoaiVung = true;
      S.goi.ship = [thuong(t('giao_ngoai_vung', 'Chúng tôi chưa hỗ trợ giao đến địa chỉ này. Bánh kem chỉ giao trong bán kính {km} km quanh bếp và cửa hàng. Quý khách có thể chọn tự đến lấy tại cửa hàng.', {km: m.ban_kinh || 12}))];
      return;
    }
    if (!m || !m.ok || !(m.total_fee > 0)) {
      /* Không đoán bừa một con số, không hiện thành miễn phí. */
      S.CO.ship = null; S.CO.shipTrangThai = 'chua_ro';
      S.goi.ship = mp
        ? noi(thuong(t('dat_banh_e54218837', 'Đơn này được') + ' '), dam(t('dat_banh_aea590df5', 'miễn phí giao'), 'cyan'), thuong(t('dat_banh_fc72cffcb', '. Chúng tôi chưa kiểm được địa chỉ và sẽ gọi xác nhận.')))
        : noi(thuong(t('dat_banh_b4bab6e2c', 'Chưa lấy được phí giao cho địa chỉ này.') + ' '), dam(t('dat_banh_832bb0406', 'Chúng tôi sẽ báo phí khi xác nhận đơn.'), 'cyan'));
      S.goi.phiThuLai = true;
      return;
    }
    S.CO.ship = m.total_fee; S.CO.shipTrangThai = kieu;
    const dd = TEN_DIEM[m.diem_lay], diem = dd ? t(dd[0], dd[1]) : m.diem_lay;
    if (mp) {
      S.goi.ship = noi(thuong(t('dat_banh_e54218837', 'Đơn này được') + ' '), dam(t('dat_banh_aea590df5', 'miễn phí giao'), 'cyan'),
        diem ? thuong(t('dat_banh_8509dcd93', ', giao từ {gia_tri_a}', {gia_tri_a: diem})) : null, thuong(t('dat_banh_6ea269703', '. Chúng tôi gọi xác nhận lại trước khi giao.')));
      return;
    }
    S.goi.ship = kieu === 'du_kien'
      ? noi(thuong(t('dat_banh_35e7005c4', 'Phí giao dự kiến cho khu vực') + ' '), dam(q ? q.ten : ''), thuong(': '), dam(T.tienVN(S.CO.ship), 'cyan'), thuong(t('dat_banh_d6e63e5f0', '. Gõ địa chỉ để có số chính xác.')))
      : noi(thuong(t('dat_banh_06a446f5c', 'Phí giao') + ' '), dam(T.tienVN(S.CO.ship), 'cyan'),
        m.distance ? thuong(' ' + t('dat_banh_7238a477f', 'cho khoảng {gia_tri_a} km', {gia_tri_a: Number(m.distance).toFixed(1)})) : null,
        diem ? thuong(t('dat_banh_8509dcd93', ', giao từ {gia_tri_a}', {gia_tri_a: diem})) : null,
        m.theo_gio ? noi(thuong(t('dat_banh_d60cf33fc', ', tính đúng khung') + ' '), dam(slotDangChon.value.t), thuong(' ' + t('dat_banh_988f4d65a', 'quý khách chọn.')))
          : thuong(t('dat_banh_13d8a57e8', '. Đây là giá giờ hiện tại, khung giờ cao điểm có thể cao hơn.')),
        thuong(' ' + t('dat_banh_5956a13dc', 'Chúng tôi gọi xác nhận lại trước khi giao.')));
  }
  function chonQuan(ma) { S.CO.quan = String(ma || ''); quoteShip(); }
  function setMode(m) {
    S.CO.mode = m;
    if (m === 'pick') { S.CO.ship = 0; } else { S.CO.ship = null; S.CO.shipTrangThai = null; quoteShip(); }
  }
  /* Điểm nhận giữ bằng MÃ (Codex #453): mã không còn thì bỏ chọn. */
  const diemNhanChon = computed(() => S.PICKUPS.find(x => x.id === S.CO.pickupId) || null);
  function setPickup(id) { if (S.PICKUPS.some(x => x.id === id)) S.CO.pickupId = id; }
  function capNhatDiemNhan(ds) {
    if (!Array.isArray(ds)) return;
    S.PICKUPS = ds.map(x => ({id: String(x.id || ''), n: String(x.n || ''), a: String(x.a || '')})).filter(x => x.id && x.n && x.a);
    if (S.CO.pickupId && !S.PICKUPS.some(x => x.id === S.CO.pickupId)) {
      const daChon = !!S.CO.pickupId;
      S.CO.pickupId = '';
      if (daChon && S.CO.mode === 'pick') toast(lyDo('diem_nhan_khong_con'));
    }
    if (!S.PICKUPS.length && S.CO.mode === 'pick') setMode('ship');
  }
  const tong = computed(() => {
    /* Chỉ để HIỆN. Tiền thật máy chủ tính lại ở tao_don (QT-19). */
    const tt = T.trangThaiPhi(S.CO.mode === 'pick', mienPhi.value, S.CO.ship, S.CO.shipTrangThai, t);
    return {items: tienBanh.value, giam: giam.value, ship: tt.phi || 0, total: tienBanh.value - giam.value + (tt.phi || 0), tt};
  });
  const dongMienPhi = computed(() => T.dongMienPhi(tienBanh.value, S.mienPhiTu, t));

  /* ---------------- thanh toán (v638) ---------------- */
  /* Cách thanh toán hiện cho khách: hai cách thẻ chỉ hiện khi máy chủ báo cổng
     OnePay đang dùng được (cau_hinh_web.onepay). Chưa nạp cấu hình thì chưa hiện
     thẻ, không hứa một cách trả có thể đang tắt. */
  const paysHien = computed(() => PAYS.filter(p => !p.the || !!(S.cauHinh && Number(S.cauHinh.onepay) === 1)));
  /* Cách đang chọn mà vừa bị ẩn (cổng tắt) thì về chuyển khoản. Chỉ xét khi đã
     có cấu hình: giỏ phục hồi chọn thẻ không bị đổi trước lúc biết cổng. */
  watch(() => [S.cauHinh, S.CO.pay], () => {
    if (S.cauHinh && !paysHien.value.some(p => p.k === S.CO.pay)) S.CO.pay = 'bank';
  }, {flush: 'sync'});
  /* Câu dưới tổng tiền nói đúng điều sẽ xảy ra sau khi gửi đơn (trước v638 câu
     này hứa link OnePay, mã 15 phút, tự huỷ mà máy chủ không làm gì). */
  const cauThanhToan = computed(() => {
    const p = S.CO.pay;
    const cau = p === 'cash' ? t('dat_banh_tt_tien_mat', 'Quý khách thanh toán tiền mặt khi nhận bánh, tại quầy hoặc cho người giao.')
      : (p === 'card' || p === 'atm') ? t('dat_banh_tt_the', 'Gửi đơn xong, quý khách bấm Thanh toán bằng thẻ trên trang biên nhận và nhập thẻ trên trang bảo mật OnePay.')
      : t('dat_banh_tt_ck', 'Gửi đơn xong, trang biên nhận hiện mã VietQR đúng số tiền. Quý khách quét để chuyển khoản, hệ thống tự xác nhận khi tiền về.');
    const ds = [cau];
    if (p !== 'cash' && S.CO.mode !== 'pick' && !mienPhi.value && S.CO.shipTrangThai === 'chua_ro') {
      ds.push(t('dat_banh_tt_phi_sau', 'Phí giao chưa tính được lúc này: số thu online là tiền bánh, phí giao quý khách trả khi nhận.'));
    }
    return ds;
  });
  /* Mã giới thiệu: số điện thoại nhân viên. Rời ô thì hỏi tên nhân viên (cửa
     vagabond.gioi_thieu.kiem); cửa lỗi hay chưa có thì im lặng, không bao giờ
     chặn đặt đơn. Máy chủ tự chuẩn hoá lại khi nhận đơn.
     v638: công tắc Hoa hồng giới thiệu tắt (cau_hinh_web.gioi_thieu = 0) thì ô
     ẩn và đơn không gửi mã. Chưa nạp cấu hình thì vẫn hiện: máy chủ tự bỏ mã
     khi công tắc tắt. Cửa kiem chỉ nhận POST (giới hạn lượt theo IP). */
  const coGioiThieu = computed(() => !(S.cauHinh && Number(S.cauHinh.gioi_thieu) === 0));
  const soGioiThieu = () => {
    if (!coGioiThieu.value) return '';
    const so = String(S.f.gt || '').replace(/\D/g, '');
    return so.length >= 8 && so.length <= 12 ? so : '';
  };
  let luotGt = 0;
  async function kiemGioiThieu() {
    const so = soGioiThieu(), luot = ++luotGt;
    S.goi.gt = null;
    if (!so) return;
    let m = null;
    try { m = await ghi('vagabond.gioi_thieu.kiem', {sdt: so}, {choXemThu: true}); } catch (e) { return; }
    if (luot !== luotGt || so !== soGioiThieu() || !m || typeof m !== 'object' || !('ok' in m)) return;
    if (Number(m.tat) === 1) return;
    const ten = String(m.ten || '').trim();
    S.goi.gt = ten ? [dam(t('dat_banh_ma_gt_co', 'Nhân viên giới thiệu: {ten}', {ten}), 'cyan')]
      : [thuong(t('dat_banh_ma_gt_khong', 'Không tìm thấy nhân viên với số này. Quý khách vẫn đặt bánh bình thường.'))];
  }

  /* ---------------- tra số điện thoại, địa chỉ, MST ---------------- */
  let phHen = null, gyHen = null, mstHen = null;
  function lookupPhone() {
    huyHen(phHen);
    const v = (S.f.phone || '').replace(/\D/g, '');
    /* v603 (F34): đổi số là bỏ ngay câu "Tìm thấy N địa chỉ" của số cũ, kể cả
       khi số mới chưa đủ dài để tra; không để khách đọc kết quả của số khác. */
    S.CO.addrList = []; S.CO.addrSel = -1; S.goi.phone = null;
    if (v.length < 9) return;
    phHen = hen(async () => {
      let ds = [];
      try {
        const m = await doc('vagabond.api.tra_khach', {phone: v});
        if (v !== (S.f.phone || '').replace(/\D/g, '')) return;
        ds = (m.addresses || []).map(a => ({full_name: a.ho_ten, phone_number: a.phone, full_address: a.dia_chi}));
      } catch (e) { ds = []; }
      S.CO.addrList = ds;
      S.goi.phone = ds.length
        ? noi(thuong(t('dat_banh_1a6a68ddf', 'Tìm thấy') + ' '), dam(t('dat_banh_ed129760c', '{gia_tri_a} địa chỉ', {gia_tri_a: ds.length}), 'cyan'), thuong(' ' + t('dat_banh_55044016e', 'đã lưu của số này.')))
        : [thuong(t('dat_banh_dd5afcc96', 'Quý khách nhập địa chỉ bên dưới.'))];
    }, 400);
  }
  const diaChiLuu = computed(() => S.CO.addrList.map((a, i) => {
    const on = S.CO.addrSel === i;
    return {i, on, dau: a.full_name + ' · ' + (on ? a.phone_number : T.maskPhone(a.phone_number)), duoi: on ? a.full_address : T.maskAddr(a.full_address)};
  }));
  function selAddr(i) { S.CO.addrSel = i; S.CO.pickedLoc = null; S.goiY = []; S.f.addr = S.CO.addrList[i].full_address; quoteShip(); }
  let lanDiaChi = 0;
  function goiYDiaChi() {
    const lan = ++lanDiaChi;
    S.CO.pickedLoc = null;
    const q = (S.f.addr || '').trim();
    huyHen(gyHen);
    if (q.length < 5) { S.goiY = []; quoteShip(); return; }
    gyHen = hen(async () => {
      try { const m = await doc('vagabond.dia_chi.goi_y_dia_chi', {q}); if (lan !== lanDiaChi) return; S.goiY = ((m || {}).suggestions || []).slice(0, 6); }
      catch (e) { if (lan !== lanDiaChi) return; S.goiY = []; }
      quoteShip();
    }, 450);
  }
  async function chonGoiY(i) {
    const g = S.goiY[i]; if (!g) return;
    const lan = ++lanDiaChi;
    S.f.addr = g.mo_ta; S.goiY = [];
    S.goi.ship = [mau(t('dat_banh_ddbf6a5fc', 'Đang lấy toạ độ...'), 'cyan')];
    try {
      const m = await doc('vagabond.dia_chi.chi_tiet_dia_chi', {place_id: g.place_id}) || {};
      if (lan !== lanDiaChi) return;
      if (m.lat && m.lng) { S.CO.pickedLoc = {lat: m.lat, lng: m.lng}; if (m.dia_chi) S.f.addr = m.dia_chi; }
    } catch (e) { if (lan !== lanDiaChi) return; S.CO.pickedLoc = null; }
    S.CO.addrSel = null;
    quoteShip();
  }
  function lookupMst() {
    const raw = (S.f.mst || '').replace(/[^0-9]/g, '');
    if (raw !== S.f.mst) S.f.mst = raw;
    huyHen(mstHen);
    /* Codex #462: 12 số là định danh cá nhân của chủ hộ kinh doanh, vagabond.api.tra_mst nhận 10, 12, 13. */
    if (raw.length !== 10 && raw.length !== 12 && raw.length !== 13) { S.goi.mst = [thuong(t('mst_sai_do_dai', 'Mã số thuế phải là 10 số, 12 số nếu là hộ kinh doanh, hoặc 13 số nếu là chi nhánh.'))]; return; }
    S.goi.mst = [mau(t('dat_banh_6566710b9', 'Đang tra mã số thuế...'), 'cyan')];
    mstHen = hen(async () => {
      try {
        const d = await doc('vagabond.api.tra_mst', {mst: raw});
        if (!d || !d.ok || !d.ten) throw 0;
        S.f.cname = d.ten; S.f.caddr = d.dia_chi || '';
        const ngung = /ngừng|đóng|không hoạt động|tạm/i.test(d.trang_thai || '');
        if (d.nghi_thieu) {
          S.goi.mst = noi(dam(t('dat_banh_d329d680f', 'Tên công ty tra về bị thiếu.'), 'do'), thuong(' ' + t('dat_banh_e929e0d93', 'Cổng thuế chỉ trả về "{gia_tri_a}". Quý khách xem giấy phép kinh doanh rồi gõ đủ tên vào ô Tên công ty.', {gia_tri_a: d.ten})));
          S.goi.mstFocus = (S.goi.mstFocus || 0) + 1;
        } else {
          S.goi.mst = noi(thuong(t('dat_banh_0f9188544', 'Đã tìm thấy') + ' '), dam(d.ten, 'cyan'), thuong('.'),
            ngung ? noi(thuong(' '), dam(t('dat_banh_e9d253bb6', 'Trạng thái thuế: {gia_tri_a}', {gia_tri_a: d.trang_thai}), 'do'), thuong(' ' + t('dat_banh_30ed2f4a8', '- quý khách kiểm tra lại.'))) : null);
        }
      } catch (e) {
        S.goi.mst = [thuong(t('dat_banh_179f87055', 'Không tra được mã số thuế này. Quý khách điền tay tên và địa chỉ công ty, kế toán sẽ kiểm tra lại.'))];
      }
    }, 600);
  }

  /* ---------------- mở và đóng giỏ ---------------- */
  function moGio() {
    /* Mỗi lần mở lại giỏ: thu bộ chọn lịch về thẻ tóm tắt, sinh nonce MỘT lần
       cho một lần đặt (#367), báo InitiateCheckout một lần cho một nonce. */
    gioDangMo = true;
    S.moLich = false; dongHoNhich();
    if (!S.CO.nonce) S.CO.nonce = T.taoNonce(ngauNhien);
    if (S.CO.daBaoDat !== S.CO.nonce) {
      S.CO.daBaoDat = S.CO.nonce;
      suKien('InitiateCheckout', {content_ids: S.CART.map(o => o.id), content_type: 'product', num_items: soBanh.value, value: tienBanh.value, currency: 'VND'});
    }
    hoiUuDaiNeuCan();
  }
  function roiGio() { gioDangMo = false; }

  /* ---------------- gửi đơn ---------------- */
  const loiGui = (vi, linkMsg) => noi(dam(t('dat_banh_a9adfd6de', 'Chưa gửi được đơn.'), 'do'),
    thuong(' ' + t('dat_banh_ecb3ec835', '{gia_tri_a}\n Quý khách nhắn qua', {gia_tri_a: vi}) + ' '),
    linkMsg ? lienKet(t('dat_banh_68074b808', 'Messenger'), linkMsg, true) : thuong(t('dat_banh_68074b808', 'Messenger')),
    thuong(t('dat_banh_a1018afe8', ',\n hoặc bấm gửi lại sau ít phút.')));

  // Khóa cả lượt kiểm ưu đãi bất đồng bộ, không chỉ lúc POST. Hai lần
  // bấm khi lời hứa chưa xong cùng nhận một biên nhận, không gửi lần hai.
  let luotGui = null, bienNhanVuaGui = null;
  function submitOrder() {
    if (luotGui) return luotGui;
    if (S.guiXong && bienNhanVuaGui) return Promise.resolve(bienNhanVuaGui);
    luotGui = guiDonMotLan().then(kq => {
      if (kq.buoc === 'xong') bienNhanVuaGui = kq;
      return kq;
    }).finally(() => { luotGui = null; });
    return luotGui;
  }
  async function guiDonMotLan() {
    /* Trả về {buoc} cho lớp giao diện cuộn tới ô cần sửa. */
    dongHoNhich();
    if (!S.CART.length) { toast(t('dat_banh_28c1cf2d1', 'Giỏ chưa có bánh nào')); return {buoc: 'gio'}; }
    /* v649: giỏ cũ lưu từ trước có cả hai loại bánh thì nhờ khách tách đơn. */
    if (T.gioTron(S.CART)) { toast(cauTachDon('co_hom_nay')); return {buoc: 'gio'}; }
    const lichHong = !gioHopLe.value;
    if (!daChot.value || lichHong) {
      S.moLich = true;
      toast(lichHong ? t('dat_banh_e8bc4dce3', 'Khung giờ đã chọn không còn kịp, quý khách chọn lại') : t('dat_banh_3c3291881', 'Quý khách chọn ngày và khung giờ nhận bánh.'));
      return {buoc: 'lich'};
    }
    const ten = (S.f.name || '').trim(), sdt = (S.f.phone || '').replace(/\D/g, '');
    if (!ten) { toast(t('dat_banh_bff348432', 'Quý khách điền tên')); return {buoc: 'ten'}; }
    if (sdt.length < 9) { toast(t('dat_banh_971b60e8f', 'Số điện thoại chưa đúng')); return {buoc: 'sdt'}; }
    const tuLay = S.CO.mode === 'pick';
    if (tuLay && !S.PICKUPS.length) { toast(lyDo('khong_con_diem_nhan')); setMode('ship'); return {buoc: 'cach_nhan'}; }
    if (tuLay && !diemNhanChon.value) { toast(t('dat_banh_chua_chon_diem_gui', 'Quý khách chọn điểm nhận bánh trước khi gửi.')); return {buoc: 'diem_nhan'}; }
    const diaChi = tuLay ? diemNhanChon.value.a : (S.f.addr || '').trim();
    if (!tuLay && diaChi.length < 8) { toast(t('dat_banh_147c2c4a9', 'Quý khách điền địa chỉ giao')); return {buoc: 'dia_chi'}; }
    if (!tuLay && S.CO.ngoaiVung) { toast(t('dat_banh_0e39768bd', 'Địa chỉ ngoài vùng giao. Quý khách chọn "Tự lấy tại cửa hàng"')); return {buoc: 'cach_nhan'}; }
    if (!S.CO.dongy) { toast(t('dat_banh_ea9153cee', 'Quý khách chọn ô đồng ý ngay trên nút gửi.')); return {buoc: 'dong_y'}; }
    if (!S.CO.nonce) S.CO.nonce = T.taoNonce(ngauNhien);

    /* note_print bếp đọc khi in phiếu: lời chúc, phụ kiện, dụng cụ từng bánh. */
    const lines = [];
    if (S.CO.gift) lines.push('BÁNH TẶNG - KHÔNG KÈM HOÁ ĐƠN');
    S.CART.forEach((o, i) => {
      const bits = [`${o.k} Ø${o.cm}cm${o.qty > 1 ? ' x' + o.qty : ''}`];
      if (o.wish) bits.push(`lời chúc: ${o.wish}`);
      if (o.adds.length) bits.push(`kèm: ${o.adds.map(a => a.n).join(', ')}`);
      const dc = T.chuDungCu(o); if (dc) bits.push(`dụng cụ: ${dc}`);
      lines.push(`${i + 1}. ${bits.join(' | ')}`);
    });
    const vat = S.CO.vat ? {tax_code: (S.f.mst || '').replace(/[^0-9]/g, ''), name: (S.f.cname || '').trim(), address: (S.f.caddr || '').trim(), email: (S.f.cmail || '').trim()} : null;
    const vatLine = vat ? `[HOÁ ĐƠN] MST ${vat.tax_code} · ${vat.name} · ${vat.address} · mail ${vat.email}` : '';
    const dungCu = S.CART.filter(o => T.chuDungCu(o)).map(o => `${tenMonGio(o)} x${o.qty}: ${T.chuDungCu(o)}`).join('; ');
    const note = [(S.f.note || '').trim(), dungCu, vatLine].filter(Boolean).join('\n');

    /* Ưu đãi đang hiện chưa tính cho đúng giỏ, mã, số, ngày hiện tại thì hỏi
       lại trước; số giảm đổi thì dừng cho khách xem tổng mới (Codex #460). */
    if ((S.CO.uuMa || (S.CO.uu && Number(S.CO.uu.giam) > 0)) && !uuHienTai.value) {
      const cu = S.CO.uu ? (Number(S.CO.uu.giam) || 0) : 0;
      huyHen(uuHen);
      await xemUuDai();
      if (giam.value !== cu) { toast(t('dat_banh_uu_dai_cap_nhat', 'Tổng tiền vừa cập nhật theo ưu đãi. Quý khách xem lại rồi bấm gửi.')); return {buoc: 'uu_dai'}; }
    }
    const tags = [slotDangChon.value.id];
    if (vat) tags.push(THE_XUAT_HOA_DON);
    if (S.CO.gift) tags.push(THE_BANH_TANG);
    const fb = T.docFb(moiTruong.cookie ? moiTruong.cookie() : '', moiTruong.timKiem ? moiTruong.timKiem() : '', bayGio().getTime());
    const don = {
      ho_ten: ten, dien_thoai: sdt, email: (S.f.mail || '').trim(),
      nguoi_nhan: S.CO.other ? {ho_ten: (S.f.rname || '').trim(), dien_thoai: (S.f.rphone || '').trim()} : null,
      tu_lay: tuLay, dia_chi: diaChi,
      lat: S.CO.pickedLoc ? S.CO.pickedLoc.lat : null, lng: S.CO.pickedLoc ? S.CO.pickedLoc.lng : null,
      items: T.hangGui(S.CART), tags, ngay_nhan: mocGioNhan(),
      note_print: lines.join('\n'), note, hoa_don: vat,
      nonce: S.CO.nonce, dong_y: true, nhan_uu_dai: S.CO.uudai === true,
      thanh_toan: paysHien.value.some(p => p.k === S.CO.pay) ? S.CO.pay : 'bank', ma_gioi_thieu: soGioiThieu(),
      diem_lay_ten: tuLay ? diemNhanChon.value.n : '', diem_lay_id: tuLay ? diemNhanChon.value.id : '',
      ma_uu_dai: S.CO.uuMa || '', giam_da_xem: giam.value, dung_diem: S.CO.dungDiem ? 1 : 0, fbp: fb.fbp, fbc: fb.fbc
    };
    const khoaLucGui = khoaUuDai.value;
    S.dangGui = true; S.goi.gui = null;
    let m = null;
    try { m = await ghi('vagabond.don_hang.tao_don', {don: JSON.stringify(don)}); } catch (e) { m = null; }
    if (!m || !m.ok) {
      /* Cùng giao thức máy chủ với /banh: khách phải bấm lại sau đổi giá. */
      if (m && m.ly_do === 'uu_dai_doi') {
        const moi = m.uu || {};
        S.CO.uuDangHoi = null;
        S.CO.uu = {khoa: khoaLucGui, giam: Number(moi.giam) || 0,
          ap: Array.isArray(moi.ap) ? moi.ap : [], loi: '', diem: (m.diem && typeof m.diem === 'object') ? m.diem : null};
        S.dangGui = false;
        S.goi.gui = [thuong(t('dat_banh_uu_dai_cap_nhat', 'Tổng tiền vừa cập nhật theo ưu đãi. Quý khách xem lại rồi bấm gửi.'))];
        return {buoc: 'uu_dai', don};
      }
      if (m && m.ly_do === 'diem_doi') {
        /* v652: điểm không còn dùng được như lúc khách xem (phiên hết, số dư hay
           giỏ đổi). Bỏ chọn dùng điểm, hỏi lại tổng, khách xem rồi bấm gửi. */
        S.CO.dungDiem = false; S.CO.uu = null; S.CO.uuDangHoi = null;
        S.dangGui = false;
        S.goi.gui = [thuong(t('dat_banh_dv_doi', 'Điểm thành viên vừa thay đổi nên chưa trừ điểm. Quý khách xem lại tổng tiền rồi bấm gửi.'))];
        void xemUuDai();
        return {buoc: 'uu_dai', don};
      }
      if (m && ['het_hang', 'het_hang_mua_vu'].includes(m.ly_do)) {
        const vi = (m.nhac || []).join(' ') + ' Quý khách giảm số lượng, đổi ngày nhận hoặc nhắn Sales.';
        S.dangGui = false;
        S.goi.gui = loiGui(vi, mxh('messenger', CONFIG.messenger));
        // Chỉ nạp số mới; không cắt lượng hay xoá giỏ khách đã soạn.
        void napTon(); void napMua();
        return {buoc: 'het_hang', don};
      }
      const vi = (m && m.ly_do === 'ma_uu_dai' && m.chi_tiet) ? String(m.chi_tiet) : ((m && lyDo(m.ly_do)) || t('dat_banh_5db00ac93', 'Không gửi được đơn lúc này.'));
      if (m && m.ly_do === 'ma_uu_dai') {
        S.CO.uuMa = ''; S.f.ma = ''; S.CO.uu = null; S.CO.uuDangHoi = null;
      }
      S.dangGui = false;
      S.goi.gui = loiGui(vi, mxh('messenger', CONFIG.messenger));
      return {buoc: 'loi', don};
    }
    /* Gửi được: khoá nút trong lúc chuyển sang biên nhận, không bấm hai lần. */
    S.guiXong = true;
    S.CART.splice(0); S.CO.nonce = ''; S.CO.uuMa = ''; S.CO.uu = null; S.CO.dungDiem = false;
    if (m.duong_dan && /^\/banh\/xong\/[A-Za-z0-9_-]+$/.test(m.duong_dan)) {
      S.goi.gui = noi(dam(t('dat_banh_01d9e68a4', 'Chúng tôi đã nhận yêu cầu.'), 'cyan'), thuong(' ' + t('dat_banh_f977b08ed', 'Đang mở biên nhận...')));
      return {buoc: 'xong', duong_dan: m.duong_dan, don};
    }
    S.dangGui = false;
    S.goi.gui = [thuong(t('don_da_tiep_nhan', 'Chúng tôi đã tiếp nhận yêu cầu {ma}. Quý khách lưu lại mã này. Nhân viên sẽ liên hệ xác nhận và hướng dẫn thanh toán.', {ma: m.ma_yeu_cau || m.ma_don || ''}))];
    return {buoc: 'xong', don};
  }

  /* ---------------- nạp dữ liệu máy chủ ---------------- */
  async function napTon() {
    try {
      const m = await doc('vagabond.kiem_banh.co_the_ban_hom_nay') || {};
      S.TODAY = m.banh || {};
      T.tronMon(S.CAKES, m.nhom);
      const dt = (m.dat_truoc && m.dat_truoc.nhom) || [];
      T.tronMon(S.CAKES, dt);
      const truoc = {};
      dt.forEach(g => (g.sizes || []).forEach(y => { if (y.con > 0) truoc[y.ma] = y.con; }));
      S.TRUOC = truoc;
      const rf = {};
      dt.forEach(g => (g.sizes || []).forEach(y => { if (y.refill && y.con > 0) rf[y.ma] = y.refill; }));
      S.TRUOC_RF = rf;
      S.chiHien = !!m.chi_hien;
      if (S.chiHien) {
        /* Bánh mặc định máy chủ không trả (chưa đưa lên web, Chờ ảnh, Đã ẩn)
           bỏ khỏi danh mục: không thẻ, không link chia sẻ, không khôi phục giỏ. */
        const duoc = new Set();
        [...(m.nhom || []), ...dt].forEach(g => (g.sizes || []).forEach(y => duoc.add(y.ma)));
        S.CAKES = S.CAKES.filter(c => c.sizes.some(z => duoc.has(z.id)));
      }
      S.tonNapXong = true; S.tonLoi = false;
      const b = bayGio();
      S.gioTon = String(b.getHours()).padStart(2, '0') + ':' + String(b.getMinutes()).padStart(2, '0');
      ganGioCho(); lamTuoiGiaGio();
    } catch (e) { S.tonLoi = true; /* Giữ số cũ và báo chưa cập nhật được. */ }
    /* Codex #462: đã hỏi máy chủ ít nhất một lần (được hay lỗi), link chia sẻ
       tới bánh không có mới được coi là link hỏng. */
    S.tonDaThu = true;
  }
  async function napMua() {
    try {
      S.MUA = await doc('vagabond.mua_vu.hang_theo_mua') || {co: 0, mon: []};
      if (S.gioCho.mua.length) {
        S.gioCho.mua.forEach(o => {
          const m = (S.MUA.mon || []).find(x => x.ma === o.id);
          if (m && !m.het) S.CART.push({k: m.ten, img: m.anh || '', id: m.ma, cm: 0, price: m.gia || 0, wish: '', adds: [], qty: Math.min(o.qty, m.con)});
        });
        S.gioCho.mua = [];
      }
      if (!(S.MUA.co && (S.MUA.mon || []).length) && S.tab === 'season') S.tab = 'today';
    } catch (e) { /* không có mùa thì thôi */ }
  }
  async function napQuay() {
    try { S.STORE = await doc('vagabond.kiem_kho.con_tren_quay_web') || {quay: []}; S.storeLoi = false; S.storeDaTai = true; }
    catch (e) { S.storeLoi = true; }
  }
  async function napCauHinh() {
    try {
      const ch = await doc('vagabond.don_web.cau_hinh_web');
      if (!ch || typeof ch !== 'object') return null;
      S.cauHinh = ch; S.mienPhiTu = Number(ch.mien_phi_tu) || 0;
      return ch;
    } catch (e) { return null; }
  }

  /* ---------------- hàng mùa vụ ---------------- */
  const coMua = computed(() => !!(S.MUA.co && (S.MUA.mon || []).length));
  const timMonMua = ma => (S.MUA.mon || []).find(x => x.ma === ma) || null;
  function themHangMua(ma) {
    const m = timMonMua(ma);
    if (!m || m.het) return false;
    if (daCo(ma) >= m.con) { toast(t('dat_banh_3b1a7e8cc', 'Mùa này chỉ còn') + ' ' + m.con + ' ' + t('dat_banh_5faac70d7', 'phần. Cần nhiều hơn quý khách gọi 0931 224 334')); return false; }
    const o = {k: m.ten, img: m.anh || '', id: m.ma, cm: 0, price: m.gia || 0, wish: '', adds: [], qty: 1};
    const hit = T.themVaoGio(S.CART, o);
    suKien('AddToCart', {content_ids: [o.id], content_type: 'product', value: o.price, currency: 'VND'});
    toast(hit ? t('dat_banh_cf8a493c0', 'Thêm 1 phần nữa, giỏ có') + ' ' + soBanh.value + ' ' + t('dat_banh_9900d8257', 'món')
      : t('dat_banh_1998bbe74', 'Đã thêm') + ' ' + tmon(m.ma, 'ten', m.ten) + ' ' + t('dat_banh_478beb847', 'vào giỏ'));
    return true;
  }
  const hanMua = computed(() => {
    if (!S.MUA.den_ngay) return '';
    const d = new Date(S.MUA.den_ngay + 'T00:00:00');
    const con = Math.ceil((d - bay()) / 86400000);
    return con > 0 ? t('dat_banh_0474d5ceb', 'Nhận đặt tới hết') + ' ' + T.dmy(d) + ' ' + t('dat_banh_971a4e76d', '· còn') + ' ' + con + ' ' + t('dat_banh_8ccdd0407', 'ngày')
      : t('dat_banh_0474d5ceb', 'Nhận đặt tới hết') + ' ' + T.dmy(d);
  });

  /* ---------------- lưu và khôi phục giỏ trong phiên ---------------- */
  function dongGioTuLuu(o) {
    /* Giá, cỡ, tên lấy từ CAKES hiện có, KHÔNG lấy giá trong bản lưu. */
    const c = S.CAKES.find(x => x.sizes.some(s => s.id === o.id)), z = c?.sizes.find(s => s.id === o.id);
    if (!z) return null;
    const adds = (o.adds || []).slice(0, 20).map(a => {
      const n = NUMS.find(x => x.id === a.id);
      if (n) return {id: n.id, n: 'Nến số ' + n.n, p: n.p};
      const x = ADDONS.find(y => y.id === a.id);
      return x ? {id: x.id, n: t(x.k, x.n), p: x.p} : null;
    }).filter(Boolean);
    return {k: c.k, img: c.img, id: z.id, cm: z.cm, price: z.p, nguon: o.nguon === 'today' ? 'today' : 'order', qty: o.qty,
      wish: String(o.wish || '').slice(0, 60), adds, dung_cu: T.chuanDungCu(o.dung_cu)};
  }
  function ganGioCho() {
    if (!S.gioCho.banh.length) return;
    const con = [];
    S.gioCho.banh.forEach(o => { const d = dongGioTuLuu(o); if (d) S.CART.push(d); else con.push(o); });
    /* Danh mục đã về mà vẫn không có món: món đã ngừng bán, không giữ nữa. */
    S.gioCho.banh = S.tonNapXong ? [] : con;
  }
  function lamTuoiGiaGio() {
    S.CART.forEach(o => {
      if (!o.cm) return;
      const c = S.CAKES.find(x => x.sizes.some(s => s.id === o.id)), z = c?.sizes.find(s => s.id === o.id);
      if (z && Number.isFinite(z.p) && o.price !== z.p) o.price = z.p;
    });
  }
  function luuGio() {
    if (!S.daPhucHoi || !luuTru || xemThu()) return;
    try {
      if (!S.CART.length && !S.gioCho.mua.length && !S.gioCho.banh.length) { luuTru.removeItem(KHOA_LUU); return; }
      const truong = {};
      /* Trang /banh cũ đọc id DOM. Tiếp tục ghi dạng đó để nếu phải quay lại
         trang cũ thì thông tin khách vừa nhập ở Vue vẫn còn nguyên. */
      Object.keys(S.f).forEach(k => { truong['f-' + k] = S.f[k]; });
      luuTru.setItem(KHOA_LUU, JSON.stringify({luc: bayGio().getTime(), gio: S.CART.concat(S.gioCho.mua, S.gioCho.banh),
        ngay: S.ngayChon, slot: S.pickedSlot, daChonNgay: S.daChonNgay, daChonGio: S.daChonGio, truong,
        co: {mode: S.CO.mode, pickupId: S.CO.pickupId, pay: S.CO.pay, other: S.CO.other, gift: S.CO.gift, vat: S.CO.vat, quan: S.CO.quan, nonce: S.CO.nonce}}));
    } catch (e) { /* kho phiên bị chặn: bỏ qua */ }
  }
  function phucHoiGio() {
    if (xemThu()) return;
    try {
      const d = JSON.parse((luuTru && luuTru.getItem(KHOA_LUU)) || 'null');
      if (!d || bayGio().getTime() - d.luc > 86400000 || !Array.isArray(d.gio)) return;
      const hop = o => typeof o.id === 'string' && Number.isInteger(o.qty) && o.qty > 0 && o.qty <= 99;
      S.gioCho.mua = d.gio.slice(0, 50).filter(o => o.cm === 0 && hop(o));
      const luu = d.gio.slice(0, 50).filter(o => o.cm !== 0 && hop(o));
      S.CART.splice(0); S.gioCho.banh = [];
      luu.forEach(o => { const x = dongGioTuLuu(o); if (x) S.CART.push(x); else S.gioCho.banh.push(o); });
      if (S.tonNapXong) ganGioCho();
      if (/^\d{4}-\d{2}-\d{2}$/.test(d.ngay || '')) S.ngayChon = d.ngay;
      if (Number.isInteger(d.slot) && SLOTS[d.slot]) S.pickedSlot = d.slot;
      S.daChonNgay = d.daChonNgay === true && picked.value >= 0;
      S.daChonGio = d.daChonGio === true && gioHopLe.value;
      const c = d.co || {};
      S.CO.mode = c.mode === 'pick' ? 'pick' : 'ship';
      S.CO.pay = PT_HOP_LE.includes(c.pay) ? c.pay : 'bank';
      S.CO.pickupId = typeof c.pickupId === 'string' ? c.pickupId : '';
      if (S.CO.pickupId && !S.PICKUPS.some(x => x.id === S.CO.pickupId)) S.CO.pickupId = '';
      if (!S.PICKUPS.length) S.CO.mode = 'ship';
      ['other', 'gift', 'vat'].forEach(k => { S.CO[k] = c[k] === true; });
      S.CO.quan = typeof c.quan === 'string' ? c.quan : '';
      S.CO.nonce = /^[A-Za-z0-9_-]{32}$/.test(c.nonce || '') ? c.nonce : '';
      /* Nháp Vue đời đầu dùng tên kho, còn trang cũ dùng id DOM f-*. Ưu tiên
         tên mới nếu một bản nháp hiếm gặp chứa cả hai kiểu. */
      Object.keys(S.f).forEach(k => {
        const v = typeof d.truong?.[k] === 'string' ? d.truong[k] : d.truong?.['f-' + k];
        if (typeof v === 'string') S.f[k] = v.slice(0, 4000);
      });
    } catch (e) { S.CART.splice(0); }
    finally { S.daPhucHoi = true; }
  }
  /* Lưu sau mỗi thay đổi giỏ, lịch, lựa chọn và ô nhập. Theo dõi sâu thay cho
     việc nhớ gọi luuGioDangSoan() ở từng chỗ như trang cũ. */
  watch(() => [S.CART, S.f, S.CO.mode, S.CO.pickupId, S.CO.pay, S.CO.other, S.CO.gift, S.CO.vat, S.CO.quan, S.CO.nonce,
    S.ngayChon, S.pickedSlot, S.daChonNgay, S.daChonGio, S.gioCho], luuGio, {deep: true, flush: 'sync'});
  /* v649: ngày nhận đang là hôm nay mà giỏ có bánh đặt trước (hay khách đang ở
     tab Đặt bánh trước, giỏ không có bánh Có sẵn hôm nay) thì dời sang ngày mai
     và nhờ khách xác nhận lại lịch. Ngày cũ có thể đến từ giỏ lưu hôm trước. */
  function tranhHomNay() {
    if (picked.value !== 0) return;
    const datTruoc = homNayBiChan.value || (S.tab === 'order' && !S.CART.some(T.laBanhHomNay));
    if (!datTruoc) return;
    neoNgay(1); S.daChonNgay = false;
    if (fixSlot()) S.daChonGio = false;
  }
  watch(() => [homNayBiChan.value, picked.value, S.tab], tranhHomNay, {flush: 'sync', immediate: true});

  /* v638: gọi món tại bàn qua QR, kho riêng (kho-goi-ban.js) dùng chung S. */
  const goiBan = taoGoiBan({t, doc, ghi, luuTru, ngauNhien, hen, huyHen, toast, napQuay,
    timKiem: moiTruong.timKiem || (() => '')}, S);

  return {S, T, goiBan, picked, slotOk, firstOk, ngayDangChon, slotDangChon, gioHopLe, daChot, hienTomTat, nhanNgayDangChon,
    ngayRail, ngayRailDatTruoc, homNayBiChan, khungRail, pick, pickSlot, nhanRefill, doiLich, mocGioNhan, ghiChuDatTruoc, ghiChuGio, fixSlot,
    coTruoc, banhHomNay, banhDatTruoc, tongTon, kichThuocDangBan, dongTrangThai, ghiChuHomNay, theBanh,
    curSize, moBanh, dongBanh, setSize, doiSoLuong, toggleNum, clearNums, toggleAdd, phuKienChon, tienNutThem,
    gioiHanNhan, addToCart, themNhanh, suaDongGio,
    soBanh, tienBanh, cartQty, cartRemove, dongGio, khoaUuDai, uuHienTai, giam, xemUuDai, apMaUuDai, goiYMa,
    theDonDau, guiMaDonDau, xacThucDonDau, theDiem, dungDiem, tienDiem,
    mienPhi, quoteShip, apPhiGiao, chonQuan, setMode, diemNhanChon, setPickup, capNhatDiemNhan, tong, dongMienPhi,
    paysHien, cauThanhToan, kiemGioiThieu, coGioiThieu,
    lookupPhone, diaChiLuu, selAddr, goiYDiaChi, chonGoiY, lookupMst,
    moGio, roiGio, submitOrder,
    napTon, napMua, napQuay, napCauHinh, coMua, timMonMua, themHangMua, hanMua,
    phucHoiGio, luuGio, toast, nhip: dongHoNhich, lyDo};
}

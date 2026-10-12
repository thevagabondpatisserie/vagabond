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
  THE_XUAT_HOA_DON, THE_BANH_TANG, DAYS} from './du-lieu.js';
import {thuong, dam, mau, lienKet, cauCoSo, noi} from './chu-giau.js';

const KHOA_LUU = 'vgb-gio-v1';

export function taoKho(moiTruong) {
  const {t, tMon, doc, ghi, bayGio = () => new Date(), luuTru = null, suKien = () => {},
    ngauNhien = null, hen = (f, ms) => setTimeout(f, ms), huyHen = id => clearTimeout(id),
    xemThu = () => false, mxh = (k, d) => d, nd = {}} = moiTruong;

  const S = reactive({
    /* nhịp đồng hồ: tăng mỗi 30 giây và sau mỗi thao tác, để computed đọc
       giờ HIỆN TẠI (bài học #205: không dùng bản chụp giờ lúc tải trang). */
    nhip: 0,
    CAKES: cakesGoc(),
    TODAY: {}, TRUOC: {}, tonNapXong: false, tonDaThu: false, gioTon: null,
    MUA: {co: 0, mon: []},
    STORE: {quay: []}, storeLoi: false, storeDaTai: false, quayChon: '', nhomQuay: '',
    tab: 'today',
    /* lịch: ngày THẬT đã chọn (yyyy-mm-dd) là nguồn; độ lệch suy ra từ đó. */
    ngayChon: null, lechMacDinh: 2,
    pickedSlot: SLOTS.findIndex(s => s.from >= 13),
    daChonNgay: false, daChonGio: false, moLich: false, gioBiDoi: false,
    CART: [],
    gioCho: {mua: [], banh: []}, daPhucHoi: false,
    /* bảng chi tiết đang mở */
    cur: null, curSizeId: '', soLuong: 1, wish: '', nia: 0, dia: 0, nums: [], adds: [], dongDangSua: -1,
    muaDangXem: null,
    CO: {mode: 'ship', pickupId: 'bep-tan-son-hoa', pay: 'bank', other: false, gift: false, vat: false, dongy: false,
      ship: null, shipTrangThai: null, quan: '', nonce: '', daBaoDat: '', addrList: [], addrSel: -1, pickedLoc: null,
      ngoaiVung: false, uuMa: '', uu: null, uuDangHoi: null},
    f: {phone: '', name: '', mail: '', addr: '', rname: '', rphone: '', note: '', mst: '', cname: '', cmail: '', caddr: '', ma: ''},
    goiY: [],
    goi: {phone: null, ship: null, mst: null, gui: null, phiThuLai: false},
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
  const ngayRail = computed(() => {
    const goc = bay(); const ra = [];
    for (let i = 0; i < 14; i++) { const nh = T.nhanNgay(i, goc, DAYS, t); ra.push({i, ten: nh.ten, ngay: nh.ngay, on: i === picked.value, best: i >= 2}); }
    return ra;
  });
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
  const coTruoc = computed(() => Object.keys(S.TRUOC).length > 0);
  const banhHomNay = computed(() => S.CAKES.filter(c => c.sizes.some(s => S.TODAY[s.id] > 0)));
  const banhDatTruoc = computed(() => coTruoc.value ? S.CAKES.filter(c => c.sizes.some(s => S.TRUOC[s.id] > 0)) : S.CAKES);
  const tongTon = computed(() => Object.values(S.TODAY).reduce((a, b) => a + b, 0));
  function kichThuocDangBan(c, tab = S.tab) {
    const bang = tab === 'today' ? S.TODAY : S.TRUOC;
    return Object.keys(bang).length ? c.sizes.filter(s => bang[s.id] > 0) : c.sizes;
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
    S.cur = c; S.soLuong = 1; S.wish = ''; S.nia = 0; S.dia = 0; S.nums = []; S.adds = [];
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
  function gioiHanNhan(id) {
    /* Số còn nhận theo ô Dư decor; mã ngoài danh mục decor thì không giới hạn. */
    if (!coTruoc.value) return 0;
    return S.TRUOC[id] || 0;
  }
  const daCo = id => T.daCoTrongGio(S.CART, id);
  const tenMonGio = o => tmon(o.id, 'ten', o.k);
  const kepDungCu = v => Math.min(30, Math.max(0, parseInt(v) || 0));
  function addToCart() {
    const c = S.cur, sz = curSize.value;
    if (!c || !sz) return false;
    if (!kichThuocDangBan(c).some(s => s.id === sz.id)) { toast(t('het_size', 'Kích thước này hiện chưa nhận đặt. Quý khách chọn kích thước khác.')); return false; }
    const gh = gioiHanNhan(sz.id);
    const dangSua = S.dongDangSua >= 0 && S.CART[S.dongDangSua] && S.CART[S.dongDangSua].id === sz.id ? S.CART[S.dongDangSua].qty : 0;
    if (gh && daCo(sz.id) - dangSua + S.soLuong > gh) {
      toast(t('dat_banh_04267831d', 'Size này chỉ còn nhận {gia_tri_a} bánh trong 3 ngày tới. Cần nhiều hơn quý khách gọi 0931 224 334', {gia_tri_a: gh}));
      return false;
    }
    const o = {k: c.k, img: c.img, id: sz.id, cm: sz.cm, price: sz.p, nguon: S.tab === 'today' ? 'today' : 'order',
      wish: (S.wish || '').trim(), adds: phuKienChon.value.map(x => ({...x})), qty: S.soLuong,
      dung_cu: {nia: kepDungCu(S.nia), dia: kepDungCu(S.dia)}};
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
    const sz = ds[0], gh = gioiHanNhan(sz.id);
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
    S.wish = o.wish || ''; S.nia = o.dung_cu?.nia || 0; S.dia = o.dung_cu?.dia || 0;
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
      const gh = o.cm === 0 ? 0 : gioiHanNhan(o.id);
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
    if (o.dung_cu && (o.dung_cu.nia || o.dung_cu.dia)) ex.push([thuong(t('dung_cu_gio', '{nia} nĩa gỗ, {dia} dĩa giấy', {nia: o.dung_cu.nia, dia: o.dung_cu.dia}))]);
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
  const khoaUuDai = computed(() => JSON.stringify([T.hangGui(S.CART), S.CO.uuMa || '', sdtUuDai(), ngayUuDai()]));
  const uuHienTai = computed(() => (S.CO.uu && S.CO.uu.khoa === khoaUuDai.value ? S.CO.uu : null));
  const giam = computed(() => (uuHienTai.value ? (Number(uuHienTai.value.giam) || 0) : 0));
  async function xemUuDai() {
    const khoa = khoaUuDai.value;
    S.CO.uuDangHoi = khoa;
    if (!S.CART.length) return;
    let m = null;
    try {
      m = await ghi('vagabond.don_hang.xem_uu_dai', {don: JSON.stringify({items: T.hangGui(S.CART), ma_uu_dai: S.CO.uuMa || '', dien_thoai: sdtUuDai(), ngay_nhan: ngayUuDai()})});
    } catch (e) { m = null; }
    if (S.CO.uuDangHoi !== khoa) return; /* đã có lần hỏi mới hơn */
    S.CO.uu = {khoa, giam: (m && m.ok) ? (Number(m.giam) || 0) : 0, ap: (m && m.ok && m.ap) || [],
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

  /* ---------------- phí giao ---------------- */
  const mienPhi = computed(() => T.laMienPhi(tienBanh.value - giam.value, S.mienPhiTu));
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

  /* ---------------- tra số điện thoại, địa chỉ, MST ---------------- */
  let phHen = null, gyHen = null, mstHen = null;
  function lookupPhone() {
    huyHen(phHen);
    const v = (S.f.phone || '').replace(/\D/g, '');
    S.CO.addrList = []; S.CO.addrSel = -1;
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
  function goiYDiaChi() {
    S.CO.pickedLoc = null;
    const q = (S.f.addr || '').trim();
    huyHen(gyHen);
    if (q.length < 5) { S.goiY = []; quoteShip(); return; }
    gyHen = hen(async () => {
      try { const m = await doc('vagabond.dia_chi.goi_y_dia_chi', {q}); S.goiY = ((m || {}).suggestions || []).slice(0, 6); }
      catch (e) { S.goiY = []; }
      quoteShip();
    }, 450);
  }
  async function chonGoiY(i) {
    const g = S.goiY[i]; if (!g) return;
    S.f.addr = g.mo_ta; S.goiY = [];
    S.goi.ship = [mau(t('dat_banh_ddbf6a5fc', 'Đang lấy toạ độ...'), 'cyan')];
    try {
      const m = await doc('vagabond.dia_chi.chi_tiet_dia_chi', {place_id: g.place_id}) || {};
      if (m.lat && m.lng) { S.CO.pickedLoc = {lat: m.lat, lng: m.lng}; if (m.dia_chi) S.f.addr = m.dia_chi; }
    } catch (e) { S.CO.pickedLoc = null; }
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

  async function submitOrder() {
    /* Trả về {buoc} cho lớp giao diện cuộn tới ô cần sửa. */
    dongHoNhich();
    if (!S.CART.length) { toast(t('dat_banh_28c1cf2d1', 'Giỏ chưa có bánh nào')); return {buoc: 'gio'}; }
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
      nonce: S.CO.nonce, dong_y: true, thanh_toan: S.CO.pay,
      diem_lay_ten: tuLay ? diemNhanChon.value.n : '', diem_lay_id: tuLay ? diemNhanChon.value.id : '',
      ma_uu_dai: S.CO.uuMa || '', giam_da_xem: giam.value, fbp: fb.fbp, fbc: fb.fbc
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
          ap: Array.isArray(moi.ap) ? moi.ap : [], loi: ''};
        S.dangGui = false;
        S.goi.gui = [thuong(t('dat_banh_uu_dai_cap_nhat', 'Tổng tiền vừa cập nhật theo ưu đãi. Quý khách xem lại rồi bấm gửi.'))];
        return {buoc: 'uu_dai', don};
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
    S.CART.splice(0); S.CO.nonce = ''; S.CO.uuMa = ''; S.CO.uu = null;
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
      S.tonNapXong = true;
      const b = bayGio();
      S.gioTon = String(b.getHours()).padStart(2, '0') + ':' + String(b.getMinutes()).padStart(2, '0');
      ganGioCho(); lamTuoiGiaGio();
    } catch (e) { /* giữ số cũ, không đoán */ }
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
      wish: String(o.wish || '').slice(0, 60), adds, dung_cu: {nia: kepDungCu(o.dung_cu?.nia), dia: kepDungCu(o.dung_cu?.dia)}};
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
      S.CO.pay = c.pay === 'card' ? 'card' : 'bank';
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

  return {S, T, picked, slotOk, firstOk, ngayDangChon, slotDangChon, gioHopLe, daChot, hienTomTat, nhanNgayDangChon,
    ngayRail, khungRail, pick, pickSlot, doiLich, mocGioNhan, ghiChuDatTruoc, ghiChuGio, fixSlot,
    coTruoc, banhHomNay, banhDatTruoc, tongTon, kichThuocDangBan, dongTrangThai, ghiChuHomNay, theBanh,
    curSize, moBanh, dongBanh, setSize, doiSoLuong, toggleNum, clearNums, toggleAdd, phuKienChon, tienNutThem,
    gioiHanNhan, addToCart, themNhanh, suaDongGio,
    soBanh, tienBanh, cartQty, cartRemove, dongGio, khoaUuDai, uuHienTai, giam, xemUuDai, apMaUuDai, goiYMa,
    mienPhi, quoteShip, apPhiGiao, chonQuan, setMode, diemNhanChon, setPickup, capNhatDiemNhan, tong, dongMienPhi,
    lookupPhone, diaChiLuu, selAddr, goiYDiaChi, chonGoiY, lookupMst,
    moGio, roiGio, submitOrder,
    napTon, napMua, napQuay, napCauHinh, coMua, timMonMua, themHangMua, hanMua,
    phucHoiGio, luuGio, toast, nhip: dongHoNhich, lyDo};
}

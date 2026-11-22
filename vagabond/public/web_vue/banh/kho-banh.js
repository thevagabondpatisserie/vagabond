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
  THE_XUAT_HOA_DON, THE_BANH_TANG, DAYS, PAYS, THIEP_EP_KIM, GHI_CHU_NHANH, THE_VIET_THIEP} from './du-lieu.js';
import {thuong, dam, mau, lienKet, cauCoSo, noi} from './chu-giau.js';
import {taoGoiBan, cauDn} from './kho-goi-ban.js';
import * as D from './dbt-thuan.js';
import {monBay, thanhMienPhi} from './goi-y-mua.js';

const KHOA_LUU = 'vgb-gio-v1';
/* v638: bốn cách thanh toán khách chọn được. */
const PT_HOP_LE = PAYS.map(p => p.k);

export function taoKho(moiTruong) {
  const {t, tMon, doc, ghi, bayGio = () => new Date(), luuTru = null, suKien = () => {},
    ngauNhien = null, hen = (f, ms) => setTimeout(f, ms), huyHen = id => clearTimeout(id),
    xemThu = () => false, mxh = (k, d) => d, nd = {}} = moiTruong;

  /* Codex #594 vòng 2: đang gán bảng số của một phản hồi tồn (xem napTon). */
  let dangApTon = false;
  const S = reactive({
    /* nhịp đồng hồ: tăng mỗi 30 giây và sau mỗi thao tác, để computed đọc
       giờ HIỆN TẠI (bài học #205: không dùng bản chụp giờ lúc tải trang). */
    nhip: 0,
    CAKES: cakesGoc(),
    TODAY: {}, TRUOC: {}, TRUOC_RF: {}, TRUOC_MAI: {}, TRUOC_XA: {}, DBT: {}, chiHien: false, tonNapXong: false, tonLoi: false, tonDaThu: false, gioTon: null,
    MUA: {co: 0, mon: []},
    STORE: {quay: []}, storeLoi: false, storeDaTai: false, quayChon: '', nhomQuay: '', tangQuay: '', timQuay: '',
    tab: 'today',
    /* lịch: ngày THẬT đã chọn (yyyy-mm-dd) là nguồn; độ lệch suy ra từ đó. */
    ngayChon: null, lechMacDinh: 2,
    pickedSlot: SLOTS.findIndex(s => s.from >= 13),
    daChonNgay: false, daChonGio: false, moLich: false, gioBiDoi: false,
    CART: [],
    /* Dĩa, nĩa tặng kèm cho cả đơn (anh Việt 20/11/2026), chọn ở trang Thông tin đơn hàng. */
    DC: {dia: 0, nia: 0},
    gioCho: {mua: [], banh: []}, daPhucHoi: false,
    /* bảng chi tiết đang mở */
    cur: null, curSizeId: '', soLuong: 1, wish: '', nia: 0, dia: 0, thiep: 0, nums: [], adds: [], dongDangSua: -1, huongSize: false,
    muaDangXem: null,
    CO: {mode: 'ship', pickupId: 'bep-tan-son-hoa', pay: 'bank', other: false, gift: false, vat: false, dongy: false, uudai: false,
      ship: null, shipTrangThai: null, shipKm: null, payBao: false, phuong: '', phTim: '', phMo: false, nonce: '', daBaoDat: '', addrList: [], addrSel: -1, pickedLoc: null,
      ngoaiVung: false, uuMa: '', uu: null, uuDangHoi: null,
      /* v645 ưu đãi đơn đầu tiên trên web: bước xác thực số qua Zalo. */
      dd: {buoc: 'nut', ma: '', loi: '', bao: '', dangGui: false, lan: 0, cho: 0, daXac: '', xacSo: ''}, uuTv: null,
      /* v652: khách bấm Dùng điểm thành viên (máy chủ quyết số điểm, diem_web). */
      dungDiem: false,
      /* v681: mã các viên Ghi chú chọn nhanh đang chọn và giờ trễ nhất (HH:MM). */
      gc: [], gcGio: ''},
    f: {phone: '', name: '', mail: '', addr: '', rname: '', rphone: '', note: '', mst: '', cname: '', cmail: '', caddr: '', ma: '', gt: ''},
    goiY: [],
    goi: {phone: null, ship: null, mst: null, gui: null, phiThuLai: false, gt: null, gcGio: ''},
    /* v681: hộp hỏi lại trước khi bỏ một chiếc đã có lời chúc, thiệp ({chu, lam}); chiếc đang xem mẫu cờ. */
    hoiBo: null, mauCo: '',
    dangGui: false, guiXong: false,
    PICKUPS: PICKUPS_GOC.slice(),
    cauHinh: null, mienPhiTu: 0, mienPhiKm: 0,
    /* v668 Gợi ý mua thêm ở giỏ đặt trước (goi_y_mua.goi_y_dat_truoc). */
    GY: {bat: 0, toi_da: 4, thanh: 0, mon: [], khoa: ''},
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
  function refillChan(i, gio = S.CART) {
    /* Codex 549 (1eefda8): dòng thêm từ tab Hôm nay lấy bánh có sẵn, không
       thuộc mẻ refill tương lai, nên không khoá ngày. */
    const iso = isoNgayThu(i);
    return gio.filter(o => o.nguon !== 'today').map(o => S.TRUOC_RF[o.id])
      .find(r => r && r.chi_refill && !dotRefill(r, iso)) || null;
  }
  /* v660: một bánh nhiều đợt refill. Trả đợt có khoảng ngày chứa ngày iso
     (r.ds là mọi đợt còn suất; máy chủ bản cũ chỉ có r.tu, r.den). */
  function dsDotRefill(r) { return r && r.ds && r.ds.length ? r.ds : (r ? [r] : []); }
  function dotRefill(r, iso) { return dsDotRefill(r).find(k => iso >= k.tu && iso <= k.den) || null; }
  function ngayNgan(iso) { return iso ? iso.slice(8, 10) + '/' + iso.slice(5, 7) : ''; }
  function nhanRefill(id) {
    const r = S.TRUOC_RF[id];
    return r && r.chi_refill ? t('refill_co_tu', 'Có từ {ngay}', {ngay: ngayNgan(r.tu)}) : '';
  }
  /* v667: đợt Đặc biệt tuần này. Giỏ có món của đợt thì chỉ chọn được ngày giao
     của đợt (máy chủ chặn lại ở don_hang.tao_don). Giờ Việt Nam, không theo máy khách. */
  const lucDbt = () => D.lucVN(bay());
  const dotDbt = computed(() => D.dotDangHien(nd.khoi, lucDbt().slice(0, 10)));
  const maDbt = computed(() => D.maTheoKhoa(dotDbt.value, S.CAKES));
  const dbtChan = (i, gio = S.CART) => D.ngayBiKhoa(dotDbt.value, gio, maDbt.value, isoNgayThu(i));
  const ngayGiaoDbt = () => ((dotDbt.value && dotDbt.value.ngay_giao) || []).map(ngayNgan).join(', ');
  const monDbtCua = id => { const k = D.khoaCuaMa(maDbt.value, id); return k ? (dotDbt.value.mon_dt || []).find(m => m.khoa === k) : null; };
  /* Số món của đợt (cùng bánh) đang có trong giỏ, trừ dòng đang sửa. */
  const trongGioDbt = (m, boDong = -1) => S.CART.reduce((a, o, i) => a + (i !== boDong && D.khoaCuaMa(maDbt.value, o.id) === m.khoa ? o.qty : 0), 0);
  function chanThemDbt(id, them, boDong = -1) {
    const m = monDbtCua(id);
    if (!m) return false;
    const tt = D.trangThaiMon(dotDbt.value, m, lucDbt(), nd.dac_biet_da_dat);
    if (tt !== 'mo') { toast(lyDo(tt === 'chua_mo' ? 'dac_biet_chua_mo' : 'dac_biet_da_chot')); return true; }
    const con = D.conSuat(m, nd.dac_biet_da_dat, trongGioDbt(m, boDong));
    if (con !== null && them > con) { toast(cauSuat(con)); return true; }
    return false;
  }
  const cauSuat = con => con > 0 ? t('dbt_con_suat', 'Món cuối tuần này chỉ còn nhận {so} bánh.', {so: con})
    : t('dbt_du_suat', 'Món cuối tuần này đã đủ số lượng nhận.');
  /* Codex #579: món của đợt vượt số lượng ngay trong giỏ (giỏ lưu từ trước,
     đã đặt tăng lên trong lúc khách chọn). Trả câu nhắc hoặc ''. */
  function gioVuotSuat() {
    for (const m of (dotDbt.value && dotDbt.value.mon_dt) || []) {
      const con = D.conSuat(m, nd.dac_biet_da_dat, 0);
      if (con !== null && trongGioDbt(m) > con) return cauSuat(con);
    }
    return '';
  }
  /* Bánh thuộc đợt đang hiện (theo mọi size của bánh). */
  const laBanhDot = c => c.sizes.some(s => !!D.khoaCuaMa(maDbt.value, s.id));
  /* v649: giỏ có bánh đặt trước thì không nhận hôm nay (tách đơn). */
  const homNayBiChan = computed(() => T.chanHomNay(S.CART));
  const cauTachDon = k => k === 'co_hom_nay'
    ? t('tach_don_co_hom_nay', 'Giỏ đang có bánh có sẵn hôm nay. Bánh đặt trước nhận từ ngày mai nên đặt đơn riêng: quý khách gửi đơn đang có trước rồi đặt tiếp.')
    : k === 'co_dat_truoc'
      ? t('tach_don_co_dat_truoc', 'Giỏ đang có bánh đặt trước, nhận từ ngày mai. Bánh có sẵn hôm nay đặt đơn riêng: quý khách gửi đơn đang có trước rồi đặt tiếp.')
      : t('dat_truoc_tu_mai', 'Giỏ có bánh đặt trước nên nhận từ ngày mai. Muốn nhận bánh có sẵn hôm nay thì đặt đơn riêng.');
  /* v671 (Loan Anh góp ý 18/11/2026, anh Việt chốt): bánh đặt trước chỉ nhận
     NGÀY MAI, số theo cột Có thể bán của phiếu Kiểm bánh ngày mai. Bánh làm
     theo mẻ (refill) vẫn chọn ngày trong khoảng của mẻ, món của đợt theo ngày
     giao của đợt, món gợi ý đi kèm theo bánh. Máy chủ chặn lại ở ton_don_web. */
  /* Dòng bánh đặt trước thường: không phải món của đợt, món gợi ý đi kèm, hay
     bánh chỉ còn mẻ refill (refillChan đã giữ khoảng ngày của mẻ). */
  const laDatTruocThuong = o => T.laBanhDatTruoc(o) && !o.goi_y && !D.khoaCuaMa(maDbt.value, o.id)
    && !(S.TRUOC_RF[o.id] && S.TRUOC_RF[o.id].chi_refill);
  /* v675 (Loan Anh nhắn 19/11/2026, anh Việt chốt nhận tới 3 ngày tới): số bánh
     đặt trước thường còn nhận cho ngày i. Ngày mai theo cột Còn bán của phiếu
     Kiểm bánh ngày mai (TRUOC_MAI), ngày kia và ngày thứ ba theo BTP sẵn còn
     nhận (TRUOC_XA, v677; trước đó Đủ decor), xa hơn không nhận. Mã máy chủ không trả (null) thì ngày mai
     để máy chủ quyết như v671. Cùng luật ton_don_web.kiem. */
  const SO_NGAY_DAT_TRUOC = 3;
  function soThuong(id, i) {
    if (i < 1 || i > SO_NGAY_DAT_TRUOC) return 0;
    if (!(id in S.TRUOC_MAI || id in S.TRUOC_XA)) return null;
    return (i === 1 ? S.TRUOC_MAI[id] : S.TRUOC_XA[id]) || 0;
  }
  /* Ngày i đóng với giỏ: có dòng bánh đặt trước thường không thuộc mẻ refill của
     ngày đó mà số của ngày đó bằng 0. Mã máy chủ không trả số riêng thì như v671:
     ngày mai để máy chủ quyết, ngày xa hơn đóng. */
  function datTruocChan(i, gio = S.CART) {
    if (i < 1) return false;
    const iso = isoNgayThu(i);
    return gio.some(o => {
      if (!laDatTruocThuong(o) || dotRefill(S.TRUOC_RF[o.id], iso)) return false;
      const n = soThuong(o.id, i);
      return n === null ? i > 1 : n <= 0;
    });
  }
  /* Ngày i có trên lịch của tab Đặt bánh trước: ngày mai, ngày thuộc một mẻ
     refill đang nhận (khách có thể chọn ngày trước rồi chọn bánh của mẻ), hay
     ngày giao của đợt khi giỏ có món của đợt. */
  function ngayCuaTabTruoc(i) {
    if (i === 1) return true;
    if (i < 1) return false;
    if (i <= SO_NGAY_DAT_TRUOC && Object.values(S.TRUOC_XA).some(n => n > 0)) return true;
    const iso = isoNgayThu(i);
    if (Object.values(S.TRUOC_RF).some(r => dotRefill(r, iso))) return true;
    return !!dotDbt.value && D.gioCoMonDot(S.CART, maDbt.value) && !dbtChan(i);
  }
  /* Thêm dòng `o` vào giỏ thì còn ngày nào nhận được cả giỏ không (ngày mai tới
     13 ngày sau). Không còn thì khách đặt đơn riêng: bánh đặt trước nhận ngày
     mai, bánh của mẻ chỉ nhận trong khoảng của mẻ. */
  function conNgayChung(o, boDong = -1) {
    if (!T.laBanhDatTruoc(o)) return true;
    const gio = S.CART.filter((_x, j) => j !== boDong).concat([o]);
    for (let i = 1; i < 14; i++) if (!refillChan(i, gio) && !datTruocChan(i, gio) && !dbtChan(i, gio)) return true;
    return false;
  }
  const cauKhongNgayChung = () => t('dat_truoc_khac_ngay', 'Bánh này và bánh trong giỏ không có chung ngày nhận (bánh đặt trước nhận trong 3 ngày tới theo số còn của từng ngày, bánh làm theo mẻ nhận trong khoảng của mẻ). Quý khách gửi đơn đang có trước rồi đặt tiếp.');
  const ngayRail = computed(() => {
    const goc = bay(); const ra = [];
    for (let i = 0; i < 14; i++) { const nh = T.nhanNgay(i, goc, DAYS, t); ra.push({i, ten: nh.ten, ngay: nh.ngay, on: i === picked.value, best: i >= 2, off: !!refillChan(i) || dbtChan(i) || datTruocChan(i) || (i === 0 && homNayBiChan.value)}); }
    return ra;
  });
  /* Lịch của tab Đặt bánh trước bắt đầu từ ngày mai (Loan Anh 11/11/2026: chọn
     Hôm nay ở đây thì số hiện theo BTP của bếp, không phải bánh có trong tủ).
     v671: chỉ còn ngày mai, cộng ngày của mẻ refill và của đợt đang có trong giỏ. */
  const ngayRailDatTruoc = computed(() => ngayRail.value.filter(d => ngayCuaTabTruoc(d.i)));
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
    if (datTruocChan(i)) { toast(t('dat_truoc_chi_mai', 'Ngày này không còn nhận bánh đặt trước trong giỏ. Bánh đặt trước nhận trong 3 ngày tới, quý khách chọn ngày còn sáng hoặc gọi 0931 224 334.')); return; }
    if (dbtChan(i)) { toast(t('dbt_chi_giao', 'Món cuối tuần chỉ giao, nhận vào {ngay}. Quý khách chọn một trong các ngày này.', {ngay: ngayGiaoDbt()})); return; }
    const rc = refillChan(i);
    if (rc) {
      const ds = dsDotRefill(rc);
      if (ds.length > 1) toast(t('refill_ngoai_khoang_nhieu', 'Bánh làm theo mẻ chỉ nhận giao {khoang}. Quý khách chọn ngày trong các khoảng này.',
        {khoang: ds.map(k => t('refill_khoang', 'từ {tu} tới {den}', {tu: ngayNgan(k.tu), den: ngayNgan(k.den)})).join(t('refill_hoac', ' hoặc '))}));
      else toast(t('refill_ngoai_khoang', 'Bánh làm theo mẻ chỉ nhận giao từ {tu} tới {den}. Quý khách chọn ngày trong khoảng này.', {tu: ngayNgan(rc.tu), den: ngayNgan(rc.den)}));
      return;
    }
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
  /* v675 (tester 19/11/2026): thêm bánh Có sẵn hôm nay thì ngày nhận là HÔM NAY,
     khung giờ gần nhất còn nhận. Trước: giỏ giữ ngày mặc định (ngày kia), khách
     không để ý là đặt nhầm ngày. Quý khách đã tự chọn một ngày nhận thì giữ ngày
     đó. Hôm nay hết khung giờ thì báo ngay và mở lịch, không tự nhảy ngày. */
  function veHomNay() {
    if (S.daChonNgay && picked.value !== 0) return;
    if (!firstOk(0)) {
      if (picked.value !== 0) { S.moLich = true; toast(t('hom_nay_het_khung', 'Hôm nay đã hết khung giờ nhận. Quý khách chọn ngày nhận khác ở bước Ngày và giờ nhận.')); }
      return;
    }
    if (picked.value !== 0) { dongHoNhich(); neoNgay(0); S.gioBiDoi = false; }
    if (fixSlot()) S.daChonGio = false;
    quoteShip();
  }
  /* Dòng chốt ngay trên nút gửi đơn: ngày, giờ, nơi nhận. */
  const chotDon = computed(() => {
    const nh = nhanNgayDangChon();
    const noi = S.CO.mode === 'pick'
      ? (diemNhanChon.value ? t('chot_tu_lay', 'Tự đến lấy tại {diem}', {diem: diemNhanChon.value.n}) : t('chot_tu_lay_chua', 'Tự đến lấy, chưa chọn điểm nhận'))
      : ((S.f.addr || '').trim() ? t('chot_giao', 'Giao tới {dia_chi}', {dia_chi: S.f.addr.trim()}) : t('chot_giao_chua', 'Giao tận nơi, chưa có địa chỉ'));
    return {ngay: nh.ten + ', ' + nh.ngay, gio: gioHopLe.value ? slotDangChon.value.t : t('chot_chua_gio', 'chưa chọn khung giờ'), noi};
  });
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
    /* v675: ngày kia và ngày thứ ba nhận bánh đặt trước theo Đủ decor (chữ cũ
       trước v671); xa hơn là ngày của mẻ refill hay của đợt. */
    else if (p <= SO_NGAY_DAT_TRUOC) them = noi(thuong(' ' + t('dat_banh_62b9a66ce', 'Đặt trước từ 2 ngày là') + ' '), dam(t('dat_banh_dcc009366', 'tốt nhất')), thuong(t('dat_banh_223f30099', ', bếp chủ động được nguyên liệu và quý khách chọn được mọi khung giờ.')));
    else them = noi(thuong(' ' + t('dat_truoc_ngay_me', 'Ngày này dành cho bánh làm theo mẻ hoặc món cuối tuần trong giỏ.')));
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
  /* v671: bánh chỉ có mặt vì thuộc đợt (chiDot) không lọt sang tab Đặt bánh trước. */
  const banhDatTruoc = computed(() => coTruoc.value ? S.CAKES.filter(c => c.sizes.some(s => S.TRUOC[s.id] > 0)) : S.CAKES.filter(c => !c.chiDot));
  const tongTon = computed(() => Object.values(S.TODAY).reduce((a, b) => a + b, 0));
  function kichThuocDangBan(c, tab = S.tab) {
    /* v667: món của đợt cuối tuần lấy size đang nhận đặt trước; bánh không có
       trong bảng đặt trước (chỉ làm cho đợt) thì mọi size, số lượng giữ theo đợt. */
    /* Codex #579: MỘT luật cho mọi đường mở bánh của đợt (tab Đặc biệt, Sửa
       bánh từ giỏ, đường dẫn bánh); riêng tab Có sẵn hôm nay theo hàng có sẵn. */
    /* v671 (Minh Vũ 18/11/2026): size của món đợt theo ĐỢT (máy chủ trả mọi size
       bán được của thẻ Bánh), không theo tồn tủ hay Đủ decor; máy chủ chưa trả
       (đang tải) thì theo luật cũ. */
    if (tab === 'dac_biet' || (tab !== 'today' && laBanhDot(c))) {
      const dot = c.sizes.filter(s => S.DBT[s.id]);
      if (dot.length) return dot;
      const co = c.sizes.filter(s => S.TRUOC[s.id] > 0); return co.length ? co : c.sizes;
    }
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
        /* v677: số của ĐÚNG ngày đang chọn (soDatTruoc), cùng số với màn chi tiết và giỏ. */
        const n = coTruoc.value ? soDatTruoc(s.id) : null;
        const het = n !== null && n <= 0;
        const nh = n === null ? '' : (het ? chuHetNgay() : T.nhanTon(n, banh, t));
        return {chu: (s.cm ? s.cm + 'cm' : t('dat_banh_8a6c6356d', '1 cỡ')) + (nh ? ' · ' + nh : ''), co: coTruoc.value && !het};
      });
    /* v675: nhiều cỡ khác giá thì ghi "từ" (trước: chỉ hiện giá cỡ nhỏ nhất, khách tưởng là giá duy nhất). */
    const giaHN = avail.map(s => s.p);
    const gia = homNay ? (Math.min(...giaHN) !== Math.max(...giaHN) ? t('dat_banh_c826c3782', 'từ') + ' ' : '') + T.tienVN(Math.min(...giaHN))
      : t('dat_banh_c826c3782', 'từ') + ' ' + T.tienVN(Math.min(...(truocSz.length ? truocSz : c.sizes).map(s => s.p)));
    const ma = c.sizes[0].id;
    return {c, ten: tmon(ma, 'ten', c.k), nhanMua: tmon(ma, 'theo_mua', c.seasonal), gia, chips, vi: T.laChuViet(c.k), homNay};
  }

  /* ---------------- bảng chi tiết bánh ---------------- */
  const curSize = computed(() => S.cur ? (S.cur.sizes.find(s => s.id === S.curSizeId) || null) : null);
  function moBanh(c) {
    S.cur = c; S.soLuong = 1; S.nums = []; S.adds = []; S.huongSize = false;
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
  /* v677 (Codex và anh Việt 19/11/2026: chọn nhận 20/11, thẻ Tira-Missing-U ghi
     còn 10, mở chi tiết ghi 1): số bánh đặt trước còn nhận của mã `id` cho ĐÚNG
     ngày đang chọn. MỘT phép cho thẻ, danh sách cỡ, màn chi tiết và giới hạn giỏ.
     null: mã không theo bảng đặt trước (món của đợt, trang chưa có bảng). */
  /* Chữ "hết ngày 21/11" cho cỡ không còn nhận đúng ngày đang chọn (v677). */
  function chuHetNgay() {
    const iso = isoNgayThu(picked.value);
    return t('dat_truoc_het_ngay', 'hết ngày {ngay}', {ngay: iso.slice(8, 10) + '/' + iso.slice(5, 7)});
  }
  function soDatTruoc(id) {
    if (D.khoaCuaMa(maDbt.value, id)) return null;
    if (!coTruoc.value) return null;
    const r = S.TRUOC_RF[id];
    if (r) {
      const iso = isoNgayThu(picked.value);
      /* v660: số còn của ĐÚNG đợt chứa ngày nhận đang chọn. */
      const k = dotRefill(r, iso);
      if (k) return k.con || 0;
      if (r.chi_refill) return r.con || 0;
    }
    /* v675: số của đúng ngày đang chọn (ngày mai theo phiếu, ngày kia và ngày
       thứ ba theo BTP sẵn); chưa chọn ngày của tab thì số đầu tiên còn nhận. */
    const n = soThuong(id, picked.value);
    if (n !== null && picked.value >= 1 && picked.value <= SO_NGAY_DAT_TRUOC) return n;
    return S.TRUOC[id] || 0;
  }
  function gioiHanNhan(id, nguon) {
    /* v671: số còn nhận cho ngày mai theo cột Có thể bán của phiếu Kiểm bánh
       ngày mai (trước đây theo ô Dư decor); mã ngoài danh mục thì không giới hạn.
       Codex 549 (1eefda8): bánh có mẻ refill thì ngày nhận đang chọn nằm trong
       khoảng refill (hoặc bánh chỉ còn refill) lấy số còn của refill.
       Codex 549 (58ba797): dòng lấy từ tab Hôm nay giới hạn theo số có sẵn hôm
       nay, không theo mẻ refill tương lai. v677: phần đặt trước là soDatTruoc.
       v671: món của đợt giữ số theo đợt (chanThemDbt), cùng luật máy chủ (bo_mon_dot). */
    if (nguon === 'today') return S.TODAY[id] || 0;
    const n = soDatTruoc(id);
    return n === null ? 0 : n;
  }
  const daCo = id => T.daCoTrongGio(S.CART, id);
  const tenMonGio = o => tmon(o.id, 'ten', o.k);
  /* #463 (Codex, anh Việt 20/11/2026): khách đã xác nhận ngày nhận mà cỡ bánh hết
     ĐÚNG ngày đó thì không thêm. Trước đây số 0 bị hiểu là "không giới hạn" nên
     bánh vẫn vào giỏ, rồi giỏ tự dời ngày nhận sang ngày còn bánh. Giữ ngày, giữ
     giỏ, nhờ khách tự chọn ngày khác. Không đổi luật tồn (soDatTruoc). */
  function hetNgayDaChon(id, nguon) {
    return nguon !== 'today' && !!S.daChonNgay && soDatTruoc(id) === 0;
  }
  const cauHetNgayDaChon = () => t('dat_truoc_het_ngay_chon', 'Cỡ bánh này {het}. Quý khách chọn ngày nhận khác rồi thêm lại.', {het: chuHetNgay()});
  function addToCart() {
    const c = S.cur, sz = curSize.value;
    if (!c || !sz) return false;
    if (!kichThuocDangBan(c).some(s => s.id === sz.id)) { toast(t('het_size', 'Kích thước này hiện chưa nhận đặt. Quý khách chọn kích thước khác.')); return false; }
    const xd = T.xungDotGio(S.CART, {cm: sz.cm, nguon: S.tab === 'today' ? 'today' : 'order'}, S.dongDangSua);
    if (xd) { toast(cauTachDon(xd)); return false; }
    if (chanThemDbt(sz.id, S.soLuong, S.dongDangSua)) return false;
    if (!conNgayChung({id: sz.id, nguon: S.tab === 'today' ? 'today' : 'order'}, S.dongDangSua)) { toast(cauKhongNgayChung()); return false; }
    if (hetNgayDaChon(sz.id, S.tab === 'today' ? 'today' : 'order')) { toast(cauHetNgayDaChon()); return false; }
    const gh = gioiHanNhan(sz.id, S.tab === 'today' ? 'today' : 'order');
    const dangSua = S.dongDangSua >= 0 && S.CART[S.dongDangSua] && S.CART[S.dongDangSua].id === sz.id ? S.CART[S.dongDangSua].qty : 0;
    if (gh && daCo(sz.id) - dangSua + S.soLuong > gh) {
      toast(t('dat_truoc_con_mai', 'Size này chỉ còn nhận {gia_tri_a} bánh. Cần nhiều hơn quý khách gọi 0931 224 334', {gia_tri_a: gh}));
      return false;
    }
    /* v681: lời chúc, cờ, thiệp chọn theo từng chiếc ở bước Thông tin đơn hàng.
       Bánh thêm mới: chiếc mặc định (Cần cờ, lời chúc trống, không thiệp). Sửa
       bánh đã có: GIỮ chiếc cũ của dòng, số lượng giảm thì bỏ chiếc cuối. */
    const o = {k: c.k, img: c.img, id: sz.id, cm: sz.cm, price: sz.p, nguon: S.tab === 'today' ? 'today' : 'order',
      wish: '', adds: phuKienChon.value.map(x => ({...x})), qty: S.soLuong,
      dung_cu: T.chuanDungCu({}), chiec: []};
    if (S.dongDangSua >= 0) {
      const cu = S.CART[S.dongDangSua];
      o.chiec = cu && Array.isArray(cu.chiec) ? cu.chiec.slice() : [];
      const mat = o.chiec.slice(o.qty).filter(T.chiecCoNoiDung).length;
      const luu = () => {
        T.dongBoChiec(o);
        S.CART.splice(S.dongDangSua, 1, o); S.dongDangSua = -1;
        toast(t('gio_da_sua', 'Đã cập nhật bánh trong giỏ'));
      };
      if (mat && !S.hoiBo) {
        S.hoiBo = {chu: t('hoi_bo_chiec_sua', 'Giảm số lượng sẽ bỏ {so} chiếc cuối đã có lời chúc hoặc thiệp. Bỏ các chiếc này?', {so: mat}),
          nut: t('hoi_bo_chiec_nut_sua', 'Bỏ và lưu'), lam: () => { luu(); return 'sua'; }};
        return 'hoi';
      }
      luu();
      return 'sua';
    }
    const hit = T.themVaoGio(S.CART, o);
    suKien('AddToCart', {content_ids: [o.id], contents: [{id: o.id, quantity: o.qty}], content_type: 'product', value: T.lineUnit(o) * o.qty, currency: 'VND'});
    toast(hit ? t('them_so_luong_banh', 'Đã thêm {so} bánh, giỏ có {tong} bánh', {so: o.qty, tong: T.cartCount(S.CART)})
      : t('dat_banh_01548bfbc', 'Đã thêm {gia_tri_a} vào giỏ', {gia_tri_a: tenMonGio(o)}));
    if (o.nguon === 'today') veHomNay();
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
    if (chanThemDbt(sz.id, 1)) return 'chan';
    if (!conNgayChung({id: sz.id, nguon: cheDo === 'today' ? 'today' : 'order'})) { toast(cauKhongNgayChung()); return 'chan'; }
    if (hetNgayDaChon(sz.id, cheDo === 'today' ? 'today' : 'order')) { toast(cauHetNgayDaChon()); return 'chan'; }
    if (gh && daCo(sz.id) >= gh) {
      toast(t('dat_truoc_con_mai', 'Size này chỉ còn nhận {gia_tri_a} bánh. Cần nhiều hơn quý khách gọi 0931 224 334', {gia_tri_a: gh}));
      return 'chan';
    }
    const o = {k: c.k, img: c.img, id: sz.id, cm: sz.cm, price: sz.p, nguon: cheDo === 'today' ? 'today' : 'order', wish: '', adds: [], qty: 1, chiec: []};
    T.themVaoGio(S.CART, o);
    suKien('AddToCart', {content_ids: [o.id], contents: [{id: o.id, quantity: o.qty}], content_type: 'product', value: T.lineUnit(o) * o.qty, currency: 'VND'});
    toast(t('them_nhanh_681', 'Đã thêm {gia_tri_a}{gia_tri_b}. Lời chúc và thiệp chọn ở bước Thông tin đơn hàng.', {gia_tri_a: tenMonGio(o), gia_tri_b: sz.cm ? ' ' + sz.cm + 'cm' : ''}));
    if (o.nguon === 'today') veHomNay();
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
    S.nums = o.adds.map(a => NUMS.find(n => n.id === a.id)?.n).filter(n => n !== undefined);
    S.adds = o.adds.filter(a => !NUMS.some(n => n.id === a.id)).map(a => a.id);
    return c;
  }

  /* ---------------- giỏ ---------------- */
  const soBanh = computed(() => T.cartCount(S.CART));
  /* v681: giá thiệp ép kim máy chủ trả (giá hiện hành của BAPK00002 trên ERPNext). */
  const giaThiep = computed(() => {
    const g = S.cauHinh ? Number(S.cauHinh.gia_thiep_ep_kim) : NaN;
    return Number.isFinite(g) && g >= 0 ? g : THIEP_EP_KIM.p;
  });
  const tienBanh = computed(() => T.cartTotal(S.CART, giaThiep.value));
  function cartQty(i, d) {
    const o = S.CART[i]; if (!o) return;
    /* v681: giảm là bỏ chiếc CUỐI. Chiếc đó có lời chúc hoặc thiệp thì hỏi lại. */
    if (d < 0 && T.laDongBanh(o) && Array.isArray(o.chiec) && T.chiecCoNoiDung(o.chiec[o.qty - 1]) && !S.hoiBo) {
      S.hoiBo = {chu: t('hoi_bo_chiec', 'Bỏ chiếc {so}? Lời chúc và thiệp của chiếc này sẽ mất.', {so: o.qty}),
        nut: t('hoi_bo_chiec_nut', 'Bỏ chiếc này'), lam: () => { o.qty -= 1; if (o.qty <= 0) S.CART.splice(S.CART.indexOf(o), 1); else T.dongBoChiec(o); }};
      return 'hoi';
    }
    if (d > 0) {
      const gh = o.cm === 0 ? 0 : gioiHanNhan(o.id, o.nguon);
      const m = o.cm === 0 ? (S.MUA.mon || []).find(x => x.ma === o.id) : null;
      /* #463 cùng loại: số 0 không phải "không giới hạn" khi ngày đã xác nhận đã hết. */
      if (o.cm !== 0 && hetNgayDaChon(o.id, o.nguon)) { toast(cauHetNgayDaChon()); return; }
      if (gh && daCo(o.id) >= gh) { toast(t('dat_truoc_con_mai_ngan', 'Size này chỉ còn nhận {gia_tri_a} bánh.', {gia_tri_a: gh})); return; }
      if (m && daCo(o.id) >= m.con) { toast(t('dat_banh_3b1a7e8cc', 'Mùa này chỉ còn') + ' ' + m.con + ' ' + t('dat_banh_5faac70d7', 'phần. Cần nhiều hơn quý khách gọi 0931 224 334')); return; }
      /* Codex #579: nút + trong giỏ cũng giữ giờ chốt và số lượng của đợt. */
      if (chanThemDbt(o.id, 1)) return;
    }
    o.qty += d;
    if (o.qty <= 0) S.CART.splice(i, 1);
    else T.dongBoChiec(o);
  }
  /* Hộp hỏi lại: Đồng ý thì làm việc đã hẹn, Giữ lại thì đóng hộp, không đổi gì. */
  function dongYBo() { const h = S.hoiBo; S.hoiBo = null; return h && typeof h.lam === 'function' ? h.lam() : null; }
  function giuLai() { S.hoiBo = null; }
  /* Mọi đường đổi số lượng (gồm các phép kẹp số theo tồn) giữ o.chiec dài đúng o.qty. */
  watch(() => S.CART.map(o => o.qty), () => S.CART.forEach(o => T.dongBoChiec(o)), {flush: 'sync'});

  /* ---------------- lời chúc và thiệp từng chiếc (v681) ---------------- */
  const dsChiec = computed(() => {
    const ra = [];
    S.CART.forEach((o, i) => {
      if (!T.laDongBanh(o) || !Array.isArray(o.chiec)) return;
      o.chiec.forEach((c, j) => ra.push({o, c, i, j, ten: tenMonGio(o),
        phu: (o.cm ? 'Ø ' + o.cm + 'cm · ' : '') + t('chiec_phu', 'bánh {so}/{tong}', {so: j + 1, tong: o.qty})}));
    });
    return ra;
  });
  const timChiec = id => { for (const o of S.CART) { const c = (o.chiec || []).find(x => x.id === id); if (c) return c; } return null; };
  function datCo(id, co) { const c = timChiec(id); if (c) c.co = !!co; }
  function datThiep(id, loai) { const c = timChiec(id); if (c && T.LOAI_THIEP.includes(loai)) c.thiep = loai; }
  /* Công tắc Cần thiệp: bật thì chọn sẵn Thiệp nhỏ (miễn phí), khách đổi được sang ép kim. */
  function batThiep(id, bat) { const c = timChiec(id); if (c) c.thiep = bat ? (c.thiep === 'khong' ? 'nho' : c.thiep) : 'khong'; }
  function moMauCo(id) { S.mauCo = id || ''; }
  const chiecMauCo = computed(() => (S.mauCo ? timChiec(S.mauCo) : null));
  const soThiepEpKim = computed(() => S.CART.reduce((a, o) => a + T.soEpKim(o), 0));

  /* ---------------- ghi chú chọn nhanh (v681) ---------------- */
  const gcHien = computed(() => GHI_CHU_NHANH.filter(x => !x.giao || S.CO.mode !== 'pick'));
  const gioTreChon = computed(() => T.gioTreTrongKhung(slotDangChon.value));
  function doiGc(ma) {
    if (!GHI_CHU_NHANH.some(x => x.ma === ma)) return;
    const i = S.CO.gc.indexOf(ma);
    if (i >= 0) { S.CO.gc.splice(i, 1); if (ma === 'gio_tre_nhat') { S.CO.gcGio = ''; S.goi.gcGio = ''; } } else S.CO.gc.push(ma);
  }
  function chonGioTre(g) { if (gioTreChon.value.includes(g)) { S.CO.gcGio = g; S.goi.gcGio = ''; } }
  /* Đổi ngày hoặc khung giờ: giờ trễ nhất không còn trong khung thì xoá và nhắc chọn lại. */
  watch(() => [S.pickedSlot, S.ngayChon], () => {
    if (S.CO.gcGio && !gioTreChon.value.includes(S.CO.gcGio)) {
      S.CO.gcGio = '';
      S.goi.gcGio = t('gc_gio_doi', 'Khung giờ nhận vừa đổi. Quý khách chọn lại giờ trễ nhất.');
    }
  }, {flush: 'sync'});
  /* Mã các viên đang hiện và đang chọn: viên giao hàng đang ẩn (Tự lấy) KHÔNG gửi. */
  const gcGui = () => gcHien.value.filter(x => S.CO.gc.includes(x.ma)).map(x => x.ma);
  function dongGhiChuNhanh() {
    return gcGui().map(ma => {
      if (ma === 'gio_tre_nhat') return t('gc_tre_nhat_gui', 'Trễ nhất {gio}', {gio: S.CO.gcGio});
      const x = GHI_CHU_NHANH.find(z => z.ma === ma);
      return t(x.k, x.n);
    }).join(' · ');
  }
  function cartRemove(i) { S.CART.splice(i, 1); }
  /* Nút − và + của dĩa, nĩa tặng kèm, kẹp 0 tới 30. */
  function doiDc(k, d) {
    if (k !== 'dia' && k !== 'nia') return;
    S.DC[k] = T.chuanDcDon({...S.DC, [k]: (S.DC[k] || 0) + d})[k];
  }
  const dongGio = computed(() => S.CART.map((o, i) => {
    const ex = [];
    const dc = o.dung_cu || {};
    const chuDc = [(dc.nia || dc.dia) ? t('dung_cu_gio', '{nia} nĩa gỗ, {dia} dĩa bã mía', {nia: dc.nia || 0, dia: dc.dia || 0}) : '',
      dc.thiep ? t('dung_cu_thiep_gio', '{so} thiệp nhỏ', {so: dc.thiep}) : ''].filter(Boolean).join(', ');
    if (chuDc) ex.push([thuong(chuDc)]);
    if (o.adds.length) ex.push([thuong(t('dat_banh_2c04193c6', 'Thêm: {gia_tri_a}', {gia_tri_a: o.adds.map(a => a.n).join(', ')}))]);
    return {i, o, ten: tenMonGio(o), phu: o.goi_y ? t('gy_dong_phu', 'Giao kèm cùng chuyến, mã {ma}', {ma: o.id})
      : (o.cm ? t('dat_banh_7498bc8a8', 'Ø {gia_tri_a}cm · mã {gia_tri_b}', {gia_tri_a: o.cm, gia_tri_b: o.id}) : t('gio_ma_mot_co', 'Một cỡ, mã {ma}', {ma: o.id})),
      ex, tien: T.tienVN(T.tienDong(o, giaThiep.value))};
  }));

  /* ---------------- ưu đãi (v589) ---------------- */
  const sdtUuDai = () => { const v = (S.f.phone || '').replace(/\D/g, ''); return v.length >= 9 ? v : ''; };
  const ngayUuDai = () => { try { return mocGioNhan(); } catch (e) { return ''; } };
  /* Số giảm tuỳ giỏ, mã, số điện thoại (lượt mỗi khách) và ngày nhận (lượt
     mỗi ngày): bốn thứ nằm trong khoá, đổi là hỏi lại (Codex #460). */
  /* v645: thêm lượt xác thực số (S.CO.dd.lan): xác thực xong thì hỏi lại để máy chủ thấy phiên. */
  const khoaUuDai = computed(() => JSON.stringify([T.hangGui(S.CART, S.DC), S.CO.uuMa || '', sdtUuDai(), ngayUuDai(), S.CO.dd.lan, !!S.CO.dungDiem]));
  const uuHienTai = computed(() => (S.CO.uu && S.CO.uu.khoa === khoaUuDai.value ? S.CO.uu : null));
  /* Codex #605: thẻ Thành viên, ưu đãi đơn đầu, điểm chỉ để HIỆN; trong lúc hỏi lại (bật điểm,
     sửa giỏ) giữ phản hồi gần nhất của CÙNG số, không để thẻ nháy mất hay coi như chưa xác thực.
     Tiền giảm vẫn chỉ lấy từ uuHienTai (đúng giỏ, đúng mã, đúng điểm). */
  const uuGanNhat = computed(() => {
    if (uuHienTai.value) return uuHienTai.value;
    const so = sdtUuDai(), u = S.CO.uuTv;
    return so && u && u.sdt === so ? u : null;
  });
  const giam = computed(() => (uuHienTai.value ? (Number(uuHienTai.value.giam) || 0) : 0));
  async function xemUuDai() {
    const khoa = khoaUuDai.value, soHoi = sdtUuDai();
    S.CO.uuDangHoi = khoa;
    if (!S.CART.length) return;
    let m = null;
    try {
      m = await ghi('vagabond.don_hang.xem_uu_dai', {don: JSON.stringify({items: T.hangGui(S.CART, S.DC), ma_uu_dai: S.CO.uuMa || '', dien_thoai: sdtUuDai(), ngay_nhan: ngayUuDai(), dung_diem: S.CO.dungDiem ? 1 : 0})});
    } catch (e) { m = null; }
    if (S.CO.uuDangHoi !== khoa) return; /* đã có lần hỏi mới hơn */
    S.CO.uuTv = S.CO.uu = {khoa, giam: (m && m.ok) ? (Number(m.giam) || 0) : 0, ap: (m && m.ok && m.ap) || [],
      dd: (m && m.don_dau && typeof m.don_dau === 'object') ? m.don_dau : null,
      diem: (m && m.ok && m.diem && typeof m.diem === 'object') ? m.diem : null,
      khach: (m && m.khach && typeof m.khach === 'object') ? m.khach : null, sdt: soHoi,
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
    const u = uuGanNhat.value;
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
    /* v682 (BẢN 2 mục 2.2): khách đã đổi số trong lúc chờ thì bỏ qua phản hồi của số cũ. */
    if (sdtUuDai() !== so) return null;
    if (!m || !m.ok) { c.loi = cauLoiDd(m && m.ly_do) || t('dat_banh_dd_chua_gui', 'Chưa gửi được mã. Quý khách thử lại sau.'); return m; }
    c.buoc = 'ma'; c.ma = '';
    batDemNguoc();
    /* v653: Zalo hỏng thì mã đi WhatsApp; câu báo nói đúng kênh. */
    c.bao = m.kenh === 'whatsapp' ? t('tv653_da_gui_wa', 'Mã đã gửi qua WhatsApp tới số {so}. Mã có hiệu lực 5 phút.', {so: m.so || ''}) : t('dat_banh_dd_da_gui', 'Đã gửi mã qua Zalo.');
    return m;
  }
  async function xacThucDonDau() {
    const c = S.CO.dd;
    if (c.dangGui) return null;
    const ma = String(c.ma || '').replace(/\D/g, '');
    if (ma.length !== 6) { c.loi = t('dat_banh_dd_ma_6', 'Mã gồm 6 số trong tin nhắn Zalo.'); return null; }
    const so = sdtUuDai();
    c.dangGui = true; c.loi = '';
    let m = null;
    try { m = await ghi('vagabond.thanh_vien.xac_thuc', {sdt: so, ma}); } catch (e) { m = null; }
    c.dangGui = false;
    if (sdtUuDai() !== so) return null;
    if (!m || !m.ok) { c.loi = cauLoiDd(m && m.ly_do) || t('dat_banh_dd_chua_xac', 'Không xác thực được. Gửi mã mới.'); return m; }
    /* Hỏi lại ưu đãi: máy chủ đọc phiên vừa mở và trả số giảm. */
    c.buoc = 'nut'; c.ma = ''; c.bao = ''; c.lan += 1; c.daXac = so; c.cho = 0;
    return m;
  }
  /* "Gửi lại sau 0:xx": đếm 60 giây sau mỗi lần gửi mã. Mỗi lần gửi một lượt đếm mới. */
  let luotDem = 0;
  function batDemNguoc() {
    const c = S.CO.dd, luot = ++luotDem;
    c.cho = 60;
    const nhip = () => { if (luot !== luotDem || c.buoc !== 'ma') return; c.cho = Math.max(0, c.cho - 1); if (c.cho > 0) hen(nhip, 1000); };
    hen(nhip, 1000);
  }
  /* Ô mã 6 số: gõ hay dán vào ô thứ i. Trả vị trí ô nên đưa con trỏ tới. Đủ 6 số thì tự xác nhận. */
  function nhapMa(i, v) {
    const c = S.CO.dd, so = String(v || '').replace(/\D/g, '');
    const cu = String(c.ma || '').replace(/\D/g, '');
    const vt = Math.min(Math.max(0, i | 0), cu.length);
    c.ma = (so ? cu.slice(0, vt) + so + cu.slice(vt + so.length) : cu.slice(0, vt) + cu.slice(vt + 1)).slice(0, 6);
    c.loi = '';
    if (c.ma.length === 6 && so) xacThucDonDau();
    return Math.min(vt + so.length, 5);
  }
  /* Xoá lùi ở ô trống: bỏ số trước đó. */
  function xoaLuiMa(i) {
    const c = S.CO.dd, cu = String(c.ma || '');
    const vt = Math.min(i, cu.length) - 1;
    if (vt < 0) return 0;
    c.ma = cu.slice(0, vt) + cu.slice(vt + 1);
    return vt;
  }
  /* "Đổi số": bỏ bước nhập mã, trang đưa con trỏ về ô số điện thoại. */
  function doiSo() { const c = S.CO.dd; luotDem++; c.buoc = 'nut'; c.ma = ''; c.loi = ''; c.bao = ''; c.cho = 0; }
  /* Đổi số điện thoại thì quay về bước đầu (mã đã gửi là của số cũ). */
  /* v682 (mục 2.2): đổi số là xoá NGAY xác thực, ưu đãi, điểm, địa chỉ đã lấy của số cũ
     (địa chỉ: lookupPhone; ưu đãi, điểm: uuHienTai theo khoá có số). */
  watch(sdtUuDai, () => { const c = S.CO.dd; luotDem++; c.buoc = 'nut'; c.ma = ''; c.loi = ''; c.bao = ''; c.cho = 0; c.daXac = ''; S.CO.uuTv = null; S.CO.dungDiem = false; });

  /* ---------------- điểm thành viên (v652) ----------------
     Anh Việt chốt 12/11/2026: khách online dùng điểm ở bước thanh toán, xác thực
     số qua Zalo (cùng phiên Thành viên với ưu đãi đơn đầu). Máy chủ quyết số điểm
     (tối đa 50% tiền bánh sau ưu đãi, bill còn tối thiểu); trình duyệt chỉ hiện.
     Xác thực xong thì máy chủ mới trả số dư: không cho đọc điểm của số khác. */
  const soDiem = v => (Number(v) || 0).toLocaleString('vi-VN');
  const theDiem = computed(() => {
    const u = uuGanNhat.value;
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

  /* ---------------- thẻ Thành viên (v682, BẢN 2 mục 2.2) ----------------
     Ưu đãi đơn đầu và điểm chuyển từ mục Thanh toán lên ngay dưới ô số điện
     thoại. Dùng lại luật và API đang có (xem_uu_dai, gui_ma, xac_thuc); thẻ
     chỉ ghép trạng thái. Một lần xác thực dùng chung cho ưu đãi, điểm, địa chỉ. */
  /* Codex #605: xác thực theo SỐ, không theo từng lượt hỏi ưu đãi: trong lúc chờ lượt hỏi lại
     thì giữ nguyên. Lượt hỏi MỚI (đúng giỏ, đúng số) báo hết phiên, ví dụ đã đăng xuất ở tab
     khác, thì bỏ cả hai dấu (máy chủ báo và trang tự ghi) để thẻ mời xác thực lại. */
  watch(uuHienTai, u => {
    const so = sdtUuDai();
    if (!u || !u.khach || u.sdt !== so) return;
    if (Number(u.khach.xac_thuc)) { S.CO.dd.xacSo = so; return; }
    if (S.CO.dd.xacSo === so) S.CO.dd.xacSo = '';
    if (S.CO.dd.daXac === so) S.CO.dd.daXac = '';
  });
  const daXacThuc = computed(() => {
    const so = sdtUuDai();
    return !!so && (S.CO.dd.daXac === so || S.CO.dd.xacSo === so);
  });
  const theThanhVien = computed(() => {
    const so = sdtUuDai(), u = uuGanNhat.value;
    if (!so || !u) return null;
    const dd = u.dd || {}, dk = theDonDau.value;
    /* Máy chủ không trả phần đơn đầu (bản cũ, lỗi) hay chưa mở gửi mã Zalo: không mời xác thực. */
    if ((!u.dd || dd.trang_thai === 'chua_mo') && !daXacThuc.value) return null;
    if (S.CO.dd.buoc === 'ma') {
      return {kieu: 'ma', dia: '', tieu: t('tv682_nhap_ma', 'Nhập mã 6 số Zalo vừa gửi'),
        phu: S.CO.dd.bao || t('dat_banh_dd_phu_ma', 'Mã gửi tới Zalo của số {so}, có hiệu lực 5 phút.', {so})};
    }
    if (daXacThuc.value) {
      const d = u.diem || null;
      const diem = d && d.trang_thai === 'dung_duoc'
        ? {co: Number(d.dung) > 0, so: soDiem(Number(d.dung) > 0 ? d.dung : d.toi_da), tien: T.tienVN(Number(Number(d.dung) > 0 ? d.tien : d.tien_toi_da) || 0)} : null;
      const td = theDiem.value;
      return {kieu: 'xac', dia: '★', tieu: '✓ ' + t('tv682_da_xac', 'ĐÃ XÁC THỰC SỐ {so}', {so}),
        phu: dk && dk.kieu === 'da_ap' ? dk.tieu : '', diem,
        diemChu: !diem && td && td.kieu !== 'xac_thuc' ? td.tieu + '. ' + td.phu : '',
        soDc: S.CO.addrList.length};
    }
    const moi = ['can_xac_thuc', 'chua_du_tien', 'du'].includes(dd.trang_thai);
    if (moi && dd.trang_thai === 'chua_du_tien' && dk) {
      return {kieu: 'moi', dia: dk.ic, tieu: dk.tieu, phu: dk.phu, nut: true};
    }
    if (moi && dk) {
      return {kieu: 'moi', dia: dk.ic, tieu: t('tv682_moi_tieu', 'Số này được giảm {tien} cho đơn đầu tiên trên web', {tien: T.tienVN(Number(dd.giam) || 0)}),
        phu: t('tv682_moi_phu', 'Xác thực qua Zalo để nhận ưu đãi, tích điểm và lưu địa chỉ cho lần sau.'), nut: true};
    }
    if (u.khach && Number(u.khach.da_dat)) {
      return {kieu: 'cu', dia: '★', tieu: t('tv682_cu_tieu', 'Chào mừng quý khách quay lại'),
        phu: t('tv682_cu_phu', 'Xác thực qua Zalo để xem và dùng điểm, lấy địa chỉ đã lưu.'), nut: true};
    }
    return {kieu: 'cu', dia: '★', tieu: t('tv682_tich_tieu', 'Tích điểm thành viên cho số này'),
      phu: t('tv682_tich_phu', 'Xác thực qua Zalo để tích điểm và lưu địa chỉ cho lần sau.'), nut: true};
  });
  /* Xác thực xong thì đọc địa chỉ đã lưu của đúng số này. Mất xác thực (hết phiên) thì bỏ
     địa chỉ đã lấy và công tắc điểm, như khi đổi số (Codex #605 vòng 2, quét cùng loại). */
  watch(daXacThuc, co => {
    if (co) { lookupPhone(); return; }
    boLuotTra(); S.CO.addrList = []; S.CO.addrSel = -1; S.CO.dungDiem = false; S.goi.phone = null;
  });

  /* ---------------- phí giao ---------------- */
  /* v652: điểm thành viên là phần trả bằng điểm, không làm đơn mất miễn phí giao
     (máy chủ xét ngưỡng trên tiền bánh sau ưu đãi, chưa trừ điểm). */
  const tienDiem = computed(() => (uuHienTai.value && uuHienTai.value.diem ? (Number(uuHienTai.value.diem.tien) || 0) : 0));
  /* v675: đủ mức tiền VÀ địa chỉ trong bán kính miễn phí (máy chủ quyết lại ở don_web.quyet_phi_giao). */
  const trongKmMien = computed(() => T.trongKmMienPhi(S.CO.shipKm, S.mienPhiKm));
  /* Codex #594: có luật bán kính mà CHƯA biết khoảng cách (chưa gõ địa chỉ, mới có
     phí dự kiến theo khu vực, chưa định vị được) thì không hứa miễn phí giao. */
  const chuaBietKm = computed(() => S.mienPhiKm > 0 && S.CO.mode !== 'pick' && (S.CO.shipKm === null || S.CO.shipKm === undefined));
  const mienPhi = computed(() => T.laMienPhi(tienBanh.value - (giam.value - tienDiem.value), S.mienPhiTu) && trongKmMien.value && !chuaBietKm.value);
  /* ---------------- v668 gợi ý mua thêm ---------------- */
  /* Món gốc là BÁNH ĐẶT TRƯỚC khách chọn, phân theo NGUỒN dòng giỏ, không theo đường
     kính (bánh một cỡ có cm 0). Món thêm từ gợi ý chỉ để không gợi ý lại. Giỏ có bánh
     Có sẵn hôm nay thì không gợi ý: món gợi ý là hàng đặt trước, thêm vào thành giỏ
     trộn hai loại, bước gửi đơn chặn (Codex #581 vòng 2). */
  const coHomNay = () => S.CART.some(T.laBanhHomNay) || S.gioCho.banh.some(T.laBanhHomNay);
  const maBanhGio = () => S.CART.filter(o => T.laBanhDatTruoc(o) && !o.goi_y).map(o => o.id);
  async function napGoiY() {
    const goc = maBanhGio(), khoa = goc.slice().sort().join(',') + '|' + S.CART.map(o => o.id + ':' + (o.nguon || '')).sort().join(',');
    if (!goc.length) { S.GY.mon = []; S.GY.khoa = khoa; return; }
    if (khoa === S.GY.khoa) return;
    S.GY.khoa = khoa;
    let m = null;
    try { m = await doc('vagabond.goi_y_mua.goi_y_dat_truoc', {ma: JSON.stringify(goc), bo: JSON.stringify(S.CART.map(o => o.id))}); } catch (e) { m = null; }
    if (S.GY.khoa !== khoa) return; /* giỏ đã đổi, chờ lượt mới */
    if (!m || typeof m !== 'object') { S.GY.mon = []; return; }
    S.GY.bat = Number(m.bat) ? 1 : 0; S.GY.toi_da = Number(m.toi_da) || 4; S.GY.thanh = Number(m.thanh_mien_phi) ? 1 : 0;
    /* v681: thiệp ép kim chọn theo từng chiếc, không gợi ý thành dòng riêng (máy chủ chốt số BAPK00002 theo chiếc). */
    S.GY.mon = Array.isArray(m.mon) ? m.mon.filter(u => u && typeof u.ma === 'string' && Number(u.gia) > 0 && u.ma !== T.MA_THIEP_EP_KIM) : [];
  }
  const goiYGio = computed(() => (S.GY.bat && !coHomNay() ? monBay(S.GY.mon, S.CART.map(o => o.id), S.GY.toi_da) : []));
  const thanhMienPhiGio = computed(() => (S.CART.length ? thanhMienPhi(tienBanh.value - (giam.value - tienDiem.value), S.mienPhiTu,
    S.CO.mode !== 'pick' && trongKmMien.value, !!S.GY.thanh) : null));
  function themGoiY(u) {
    /* Bấm + là thêm NGAY một cái. Món gợi ý không cần chọn size hay tuỳ chọn. */
    if (!u || S.CART.some(o => o.id === u.ma)) return false;
    const o = {k: u.ten, img: u.anh || '', id: u.ma, cm: 0, price: Number(u.gia) || 0, nguon: 'order', wish: '', adds: [], qty: 1, goi_y: 1};
    const xd = T.xungDotGio(S.CART.concat(S.gioCho.banh), o);
    if (xd) { toast(cauTachDon(xd)); return false; }
    S.CART.push(o);
    suKien('AddToCart', {content_ids: [o.id], contents: [{id: o.id, quantity: 1}], content_type: 'product', value: o.price, currency: 'VND'});
    toast(t('gy_da_them', 'Đã thêm {ten} vào giỏ', {ten: u.ten}));
    return true;
  }
  /* ---------------- Phường giao (v684, BẢN 2 mục 2.3) ----------------
     Ô gõ tìm thay ô chọn 20 khu vực theo quận cũ. Bảng phường đến từ máy chủ
     (cau_hinh_web.phuong). Ô chỉ để CHỌN phường: không có phí dự kiến (anh Việt
     bỏ 22/11/2026), phí giao chỉ tính theo địa chỉ khách gõ. Phường có phần
     ngoài vùng giao thì báo "chưa tính được", không nhận nguyên phường. */
  const dsPhuong = () => (S.cauHinh && S.cauHinh.phuong) || [];
  const timPhuong = ma => (!ma ? null : dsPhuong().find(p => p.ma === ma) || null);
  const phuongDangChon = computed(() => timPhuong(S.CO.phuong));
  const goiYPhuong = computed(() => {
    if (!S.CO.phMo) return [];
    return T.locPhuong(dsPhuong(), S.CO.phTim).map(p => ({ma: p.ma, ten: p.ten, khop: p.khop || '',
      phu: p.quan_cu + (p.cu && p.cu.length ? ' · ' + (p.khop && p.khop !== p.quan_cu ? p.khop : p.cu.slice(0, 3).join(', ')) : ''),
      ngoai: p.loai === 'mot_phan'}));
  });
  /* Chữ hiện trong ô khi đã chọn: "Phường … · Quận X cũ". */
  const theoPhuong = computed(() => { const p = phuongDangChon.value; return p ? {chu: p.ten + ' · ' + p.quan_cu} : null; });
  function moPhuong() { S.CO.phMo = true; S.CO.phTim = ''; }
  function goPhuong(v) { S.CO.phTim = String(v || ''); S.CO.phMo = true; }
  function dongPhuong() { S.CO.phMo = false; S.CO.phTim = ''; }
  function chonPhuong(ma) { const p = timPhuong(ma); if (!p) return; S.CO.phuong = p.ma; dongPhuong(); quoteShip(); }
  function boPhuong() { S.CO.phuong = ''; dongPhuong(); quoteShip(); }
  /* Địa chỉ chọn từ gợi ý hay địa chỉ đã lưu: ghi đúng một phường mới thì tự điền;
     ghi một phường không khớp phường đang chọn thì bỏ chọn để khách chọn lại, không đoán. */
  function phuongTheoDiaChi(diaChi) {
    const p = T.phuongTrongDiaChi(dsPhuong(), diaChi);
    if (p) { S.CO.phuong = p.ma; return; }
    const dang = phuongDangChon.value, a = T.boDauPhuong(diaChi);
    if (dang && /\b(phuong|xa)\b/.test(a) && !a.includes(T.boDauPhuong(dang.ten))) S.CO.phuong = '';
  }
  let soPhi = 0, phiHen = null;
  const goiYPhiGoc = () => [thuong(t('ph684_goi_y_goc', 'Gõ địa chỉ, hệ thống báo phí giao.'))];
  function quoteShip() {
    const a = (S.f.addr || '').trim();
    S.CO.ngoaiVung = false; S.goi.phiThuLai = false;
    if (S.CO.mode !== 'ship') { S.CO.ship = 0; S.CO.shipTrangThai = null; return; }
    const ph = phuongDangChon.value, duDai = a.length >= 8;
    if (!duDai && !ph) { soPhi++; S.CO.ship = null; S.CO.shipTrangThai = null; S.CO.shipKm = null; S.goi.ship = goiYPhiGoc(); return; }
    if (!duDai) {
      /* Đã chọn phường, chưa gõ đủ địa chỉ: chưa có phí (không có phí dự kiến). */
      soPhi++; huyHen(phiHen); S.CO.ship = null; S.CO.shipKm = null;
      S.CO.shipTrangThai = ph.loai === 'mot_phan' ? 'chua_ro' : null;
      S.goi.ship = ph.loai === 'mot_phan'
        ? noi(dam(ph.ten), thuong(' ' + t('ph684_mot_phan', 'có một phần nằm ngoài vùng giao, phí giao chưa tính được. Quý khách gõ địa chỉ để có phí.')))
        : noi(thuong(t('ph684_go_dia_chi', 'Quý khách gõ địa chỉ trong') + ' '), dam(ph.ten), thuong(' ' + t('ph684_de_co_phi', 'để có phí giao.')));
      return;
    }
    const q = null, kieu = 'chinh_xac';
    const so = ++soPhi;
    S.goi.ship = [mau(t('dat_banh_9e52d8e6b', 'Đang hỏi phí giao...'), 'cyan')];
    huyHen(phiHen);
    phiHen = hen(async () => {
      let m = null;
      try {
        const p = S.CO.pickedLoc ? {lat: S.CO.pickedLoc.lat, lng: S.CO.pickedLoc.lng, addr: a} : {addr: a};
        p.luc_giao = mocGioNhan();
        m = await doc('vagabond.giao_hang.phi_giao', p);
      } catch (e) { m = null; }
      if (so !== soPhi) return; /* kết quả của lần hỏi cũ về muộn: bỏ */
      apPhiGiao(m, kieu, q);
    }, 700);
  }
  function apPhiGiao(m, kieu, q) {
    S.CO.shipKm = m && typeof m.km_thang === 'number' && kieu !== 'du_kien' ? m.km_thang : null;
    const mp = mienPhi.value;
    if (m && m.ly_do === 'ngoai_vung_giao') {
      S.CO.ship = null; S.CO.shipTrangThai = 'chua_ro';
      if (kieu === 'du_kien') {
        S.goi.ship = noi(thuong(t('dat_banh_bb3c6100a', 'Một phần khu vực') + ' '), dam(q ? q.ten : ''), thuong(' ' + t('dat_banh_aeed77c8c', 'nằm ngoài bán kính giao bánh kem. Quý khách gõ địa chỉ để chúng tôi kiểm tra chính xác.')));
        return;
      }
      S.CO.ngoaiVung = true;
      S.goi.ship = [thuong(t('giao_ngoai_vung', 'Địa chỉ này chưa hỗ trợ giao hàng đảm bảo, vui lòng nhận tại cửa hàng.', {km: m.ban_kinh || 12}))];
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
  function setMode(m) {
    S.CO.mode = m;
    if (m === 'pick') { S.CO.ship = 0; S.CO.shipKm = null; } else { S.CO.ship = null; S.CO.shipTrangThai = null; S.CO.shipKm = null; quoteShip(); }
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
  /* v681 (BẢN 2 mục 2.8): thẻ tóm tắt đơn. Chỉ để HIỆN, máy chủ chốt mọi con số. */
  const theTomTat = computed(() => {
    const banh = S.CART.map((o, i) => ({k: o.id + '|' + i, img: o.img, ten: tenMonGio(o),
      phu: [o.cm ? 'Ø ' + o.cm + 'cm' : '', '× ' + o.qty].filter(Boolean).join(' · '), gia: T.tienVN(o.price * o.qty)}));
    const gom = {};
    S.CART.forEach(o => (o.adds || []).forEach(a => {
      const x = gom[a.id] || (gom[a.id] = {ten: a.n, sl: 0, p: a.p}); x.sl += o.qty;
    }));
    const them = Object.keys(gom).map(id => ({k: id, ten: gom[id].ten, sl: gom[id].sl, gia: T.tienVN(gom[id].p * gom[id].sl)}));
    const ek = soThiepEpKim.value;
    if (ek) them.unshift({k: THIEP_EP_KIM.id, ten: t(THIEP_EP_KIM.k, THIEP_EP_KIM.n), sl: ek, gia: T.tienVN(ek * giaThiep.value)});
    const nh = nhanNgayDangChon();
    const nhan = daChot.value && gioHopLe.value ? nh.ten + ', ' + nh.ngay + ' · ' + slotDangChon.value.t : '';
    const tuLay = S.CO.mode === 'pick';
    const dc = (S.f.addr || '').trim();
    const giao = tuLay ? (diemNhanChon.value ? t('tt_tu_lay_tai', 'Tự lấy tại {ten}', {ten: diemNhanChon.value.n}) : '')
      : (dc.length >= 8 ? dc : '');
    /* Phí giao ba trạng thái tách rõ: 0 đ (miễn phí thật), dự kiến, chưa tính được. */
    const p = Number(S.CO.ship) || 0;
    let phi, kieuPhi;
    if (tuLay) { phi = t('tt_phi_tu_lay', 'không tính phí'); kieuPhi = 'tu_lay'; }
    else if (mienPhi.value) { phi = T.tienVN(0); kieuPhi = 'mien'; }
    else if (S.CO.shipTrangThai === 'chinh_xac' && p > 0) { phi = T.tienVN(p); kieuPhi = 'chinh_xac'; }
    else if (S.CO.shipTrangThai === 'du_kien' && p > 0) { phi = t('tt_phi_du_kien', 'dự kiến {tien}', {tien: T.tienVN(p)}); kieuPhi = 'du_kien'; }
    else { phi = t('tt_phi_chua_tinh', 'chưa tính được'); kieuPhi = 'chua'; }
    const daGom = kieuPhi !== 'chua';
    return {banh, them, nhan, giao, tuLay, phi, kieuPhi,
      uuDai: tong.value.giam - tienDiem.value > 0 ? T.tienVN(tong.value.giam - tienDiem.value) : '',
      diem: tienDiem.value > 0 ? T.tienVN(tienDiem.value) : '',
      dayNhan: daGom ? t('tt_tong_cong', 'Tổng cộng') : t('tt_tam_tinh', 'Tạm tính'),
      dayPhu: tuLay ? '' : kieuPhi === 'du_kien' ? t('tt_gom_phi_du_kien', 'đã gồm phí giao dự kiến') : daGom ? t('tt_gom_phi', 'đã gồm phí giao') : t('tt_chua_gom_phi', 'chưa gồm phí giao'),
      tong: T.tienVN(tong.value.total)};
  });
  const dongMienPhi = computed(() => T.dongMienPhi(tienBanh.value, S.mienPhiTu, t, S.mienPhiKm, trongKmMien.value, chuaBietKm.value));

  /* ---------------- thanh toán (v638) ---------------- */
  /* Cách thanh toán hiện cho khách: hai cách thẻ chỉ hiện khi máy chủ báo cổng
     OnePay đang dùng được (cau_hinh_web.onepay). Chưa nạp cấu hình thì chưa hiện
     thẻ, không hứa một cách trả có thể đang tắt. */
  const paysHien = computed(() => PAYS.filter(p => !p.the || !!(S.cauHinh && Number(S.cauHinh.onepay) === 1)));
  /* Cách đang chọn mà vừa bị ẩn (cổng tắt) thì về chuyển khoản. Chỉ xét khi đã
     có cấu hình: giỏ phục hồi chọn thẻ không bị đổi trước lúc biết cổng. */
  watch(() => [S.cauHinh, S.CO.pay], () => {
    /* Codex #594: không đổi cách thanh toán âm thầm, báo khách xem lại. */
    if (S.cauHinh && !paysHien.value.some(p => p.k === S.CO.pay)) { S.CO.pay = 'bank'; S.CO.payBao = true; }
  }, {flush: 'sync'});
  /* Câu dưới tổng tiền nói đúng điều sẽ xảy ra sau khi gửi đơn (trước v638 câu
     này hứa link OnePay, mã 15 phút, tự huỷ mà máy chủ không làm gì). */
  const cauThanhToan = computed(() => {
    const p = S.CO.pay;
    const cau = (p === 'card' || p === 'atm') ? t('dat_banh_tt_the', 'Gửi đơn xong, quý khách bấm Thanh toán bằng thẻ trên trang biên nhận và nhập thẻ trên trang bảo mật OnePay.')
      : t('tt_ck_681', 'Sau khi gửi đơn, quý khách có thể mở app ngân hàng hoặc quét mã QR để thanh toán.');
    const ds = [cau];
    if (S.CO.mode !== 'pick' && !mienPhi.value && S.CO.shipTrangThai === 'chua_ro') {
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
  let phHen = null, gyHen = null, mstHen = null, lanTra = 0;
  /* Mỗi lượt tra địa chỉ có số lượt riêng; đổi số hay mất xác thực thì tăng số lượt để
     phản hồi muộn của lượt cũ bị bỏ (Codex #605 vòng 3). */
  function boLuotTra() { lanTra++; huyHen(phHen); }
  function lookupPhone() {
    boLuotTra();
    const lan = lanTra;
    const v = (S.f.phone || '').replace(/\D/g, '');
    /* v603 (F34): đổi số là bỏ ngay câu "Tìm thấy N địa chỉ" của số cũ, kể cả
       khi số mới chưa đủ dài để tra; không để khách đọc kết quả của số khác. */
    S.CO.addrList = []; S.CO.addrSel = -1; S.goi.phone = null;
    if (v.length < 9) return;
    phHen = hen(async () => {
      let ds = [];
      try {
        const m = await doc('vagabond.api.tra_khach', {phone: v});
        if (lan !== lanTra || v !== (S.f.phone || '').replace(/\D/g, '')) return;
        ds = (m.addresses || []).map(a => ({full_name: a.ho_ten, phone_number: a.phone, full_address: a.dia_chi}));
      } catch (e) { if (lan !== lanTra) return; ds = []; }
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
  function selAddr(i) { S.CO.addrSel = i; S.CO.pickedLoc = null; S.goiY = []; S.f.addr = S.CO.addrList[i].full_address; phuongTheoDiaChi(S.f.addr); quoteShip(); }
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
    phuongTheoDiaChi(S.f.addr);
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
      suKien('InitiateCheckout', {content_ids: S.CART.map(o => o.id), contents: S.CART.map(o => ({id: o.id, quantity: o.qty})), content_type: 'product', num_items: soBanh.value, value: tienBanh.value, currency: 'VND'});
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
    /* v667: món của đợt cuối tuần: giờ mở, chốt đơn và ngày giao của đợt. */
    if (dotDbt.value && D.gioCoMonDot(S.CART, maDbt.value)) {
      const tt = D.trangThaiDot(dotDbt.value, lucDbt());
      if (tt !== 'mo') { toast(lyDo(tt === 'chua_mo' ? 'dac_biet_chua_mo' : 'dac_biet_da_chot')); return {buoc: 'gio'}; }
      const vuot = gioVuotSuat();
      if (vuot) { toast(vuot); return {buoc: 'gio'}; }
      if (dbtChan(picked.value)) { S.moLich = true; toast(t('dbt_chi_giao', 'Món cuối tuần chỉ giao, nhận vào {ngay}. Quý khách chọn một trong các ngày này.', {ngay: ngayGiaoDbt()})); return {buoc: 'lich'}; }
    }
    /* v681: chiếc chọn Cần cờ mà chưa có lời chúc thì nhắc và cuộn tới đúng thẻ. */
    const thieuChuc = dsChiec.value.find(x => x.c.co !== false && !String(x.c.wish || '').trim());
    if (thieuChuc) { toast(t('lc_thieu', 'Nhập lời chúc hoặc chọn Không cần cờ')); return {buoc: 'loi_chuc', sel: '#lc-' + thieuChuc.c.id + ' input'}; }
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
    if (!tuLay && S.CO.ngoaiVung) { toast(t('dat_banh_0e39768bd', 'Địa chỉ này chưa hỗ trợ giao hàng đảm bảo, vui lòng nhận tại cửa hàng')); return {buoc: 'cach_nhan'}; }
    /* v681: ghi chú chọn nhanh. Dị ứng phải ghi rõ; giờ trễ nhất phải chọn trong khung. */
    const gcMa = gcGui();
    if (gcMa.includes('gio_tre_nhat') && !gioTreChon.value.includes(S.CO.gcGio)) {
      toast(t('gc_thieu_gio', 'Quý khách chọn giờ trễ nhất trong khung giờ đã chọn.')); return {buoc: 'ghi_chu', sel: '#gcGio'};
    }
    if (gcMa.includes('di_ung') && !(S.f.note || '').trim()) {
      toast(t('gc_thieu_di_ung', 'Quý khách ghi rõ dị ứng với gì để bếp chuẩn bị đúng.')); return {buoc: 'ghi_chu', sel: '#f-note'};
    }
    if (!S.CO.dongy) { toast(t('dat_banh_ea9153cee', 'Quý khách chọn ô đồng ý ngay trên nút gửi.')); return {buoc: 'dong_y'}; }
    if (!S.CO.nonce) S.CO.nonce = T.taoNonce(ngauNhien);

    /* note_print bếp đọc khi in phiếu: lời chúc, phụ kiện, dụng cụ từng bánh. */
    /* v681: mỗi CHIẾC bánh một dòng (lời chúc, cờ, thiệp của đúng chiếc đó), giữ
       định dạng "1. Tên Ø12cm | ..." bếp đang đọc. Dòng không phải bánh giữ như cũ. */
    const lines = [];
    if (S.CO.gift) lines.push('BÁNH TẶNG - KHÔNG KÈM HOÁ ĐƠN');
    if (gcMa.includes('di_ung')) lines.push('DỊ ỨNG: ' + (S.f.note || '').trim().replace(/\s+/g, ' ').slice(0, 300));
    let soDong = 0;
    S.CART.forEach(o => {
      const ten = `${o.k}${o.cm ? ' Ø' + o.cm + 'cm' : ''}`;
      const kem = o.adds.length ? `kèm: ${o.adds.map(a => a.n).join(', ')}` : '';
      if (T.laDongBanh(o) && Array.isArray(o.chiec) && o.chiec.length) {
        const dc = T.chuDungCuNiaDia(o);
        o.chiec.forEach((c, j) => {
          const bits = [ten];
          bits.push(c.co === false ? 'không cắm cờ' : `lời chúc: ${String(c.wish || '').trim()}`);
          if (c.thiep !== 'khong') {
            const loai = c.thiep === 'ep_kim' ? 'thiệp ép kim' : 'thiệp nhỏ';
            bits.push(`${loai}: ${String(c.loi_thiep || '').trim() || 'để trắng'}`);
          }
          if (kem) bits.push(kem);
          if (dc && j === 0) bits.push(`dụng cụ: ${dc}`);
          lines.push(`${++soDong}. ${bits.join(' | ')}`);
        });
        return;
      }
      const bits = [`${ten}${o.qty > 1 ? ' x' + o.qty : ''}`];
      if (o.wish) bits.push(`lời chúc: ${o.wish}`);
      if (kem) bits.push(kem);
      const dc = T.chuDungCu(o); if (dc) bits.push(`dụng cụ: ${dc}`);
      lines.push(`${++soDong}. ${bits.join(' | ')}`);
    });
    const vat = S.CO.vat ? {tax_code: (S.f.mst || '').replace(/[^0-9]/g, ''), name: (S.f.cname || '').trim(), address: (S.f.caddr || '').trim(), email: (S.f.cmail || '').trim()} : null;
    const vatLine = vat ? `[HOÁ ĐƠN] MST ${vat.tax_code} · ${vat.name} · ${vat.address} · mail ${vat.email}` : '';
    const dungCu = S.CART.filter(o => T.chuDungCu(o)).map(o => `${tenMonGio(o)} x${o.qty}: ${T.chuDungCu(o)}`).join('; ');
    /* v681: dòng đầu ghi chú chung là các viên chọn nhanh nối bằng " · ", rồi tới chữ khách gõ. */
    const note = [dongGhiChuNhanh(), (S.f.note || '').trim(), dungCu, vatLine].filter(Boolean).join('\n');

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
    GHI_CHU_NHANH.forEach(x => { if (x.the && gcMa.includes(x.ma)) tags.push(x.the); });
    if (S.CART.some(o => (o.chiec || []).some(c => c.thiep !== 'khong' && String(c.loi_thiep || '').trim()))) tags.push(THE_VIET_THIEP);
    const fb = T.docFb(moiTruong.cookie ? moiTruong.cookie() : '', moiTruong.timKiem ? moiTruong.timKiem() : '', bayGio().getTime());
    const don = {
      ho_ten: ten, dien_thoai: sdt, email: (S.f.mail || '').trim(),
      nguoi_nhan: S.CO.other ? {ho_ten: (S.f.rname || '').trim(), dien_thoai: (S.f.rphone || '').trim()} : null,
      tu_lay: tuLay, dia_chi: diaChi, phuong: tuLay ? '' : (S.CO.phuong || ''),
      lat: S.CO.pickedLoc ? S.CO.pickedLoc.lat : null, lng: S.CO.pickedLoc ? S.CO.pickedLoc.lng : null,
      items: T.hangGui(S.CART, S.DC), tags, ngay_nhan: mocGioNhan(),
      goi_y: S.CART.filter(o => o.goi_y).map(o => o.id),
      /* v681: từng chiếc bánh và mã viên ghi chú (máy chủ lưu vào bản ghi đơn web, chốt số thiệp ép kim). */
      chiec: T.chiecGui(S.CART, tenMonGio), ghi_chu_nhanh: gcMa, gio_tre_nhat: gcMa.includes('gio_tre_nhat') ? S.CO.gcGio : '',
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
      /* v667: sai ngày giao của đợt cuối tuần thì mở lịch cho khách chọn lại. */
      if (m && m.ly_do === 'dac_biet_sai_ngay') { S.moLich = true; return {buoc: 'lich', don}; }
      return {buoc: 'loi', don};
    }
    /* Gửi được: khoá nút trong lúc chuyển sang biên nhận, không bấm hai lần. */
    S.guiXong = true;
    S.CART.splice(0); S.CO.nonce = ''; S.CO.uuMa = ''; S.CO.uu = null; S.CO.dungDiem = false; S.CO.gc = []; S.CO.gcGio = '';
    S.DC.dia = 0; S.DC.nia = 0;
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
      /* Codex #594 vòng 2: mỗi phản hồi gán nhiều bảng số lần lượt; các watch đồng bộ
         đổi ngày không được xét giữa chừng (bảng refill mới với số Đủ decor cũ). Chặn
         tới khi gán xong cả phản hồi rồi mới xét một lần. */
      dangApTon = true;
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
      /* v675: số ngày mai (phiếu) và ngày kia, ngày thứ ba (Đủ decor) riêng từng mã. */
      const sMai = {}, sXa = {};
      dt.forEach(g => (g.sizes || []).forEach(y => {
        if (y.con_mai !== undefined) sMai[y.ma] = y.con_mai || 0;
        if (y.con_xa !== undefined) sXa[y.ma] = y.con_xa || 0;
      }));
      S.TRUOC_MAI = sMai; S.TRUOC_XA = sXa;
      /* v671 (Minh Vũ 18/11/2026): món của đợt Đặc biệt tuần này máy chủ trả riêng,
         theo đợt, không cần tồn tủ hay Đủ decor. Chỉ vào danh mục và bảng size
         của đợt, KHÔNG vào bảng số hai tab kia. Bánh chỉ có mặt nhờ đợt mang cờ chiDot. */
      const db = m.dac_biet || [];
      const daCo = new Set(S.CAKES);
      T.tronMon(S.CAKES, db);
      const dbt = {};
      db.forEach(g => (g.sizes || []).forEach(y => { dbt[y.ma] = 1; }));
      S.DBT = dbt;
      S.CAKES.forEach(c => { if (!daCo.has(c) && c.sizes.some(z => dbt[z.id])) c.chiDot = 1; });
      S.chiHien = !!m.chi_hien;
      if (S.chiHien) {
        /* Bánh mặc định máy chủ không trả (chưa đưa lên web, Chờ ảnh, Đã ẩn)
           bỏ khỏi danh mục: không thẻ, không link chia sẻ, không khôi phục giỏ. */
        const duoc = new Set();
        [...(m.nhom || []), ...dt, ...db].forEach(g => (g.sizes || []).forEach(y => duoc.add(y.ma)));
        S.CAKES = S.CAKES.filter(c => c.sizes.some(z => duoc.has(z.id)));
      }
      S.tonNapXong = true; S.tonLoi = false;
      const b = bayGio();
      S.gioTon = String(b.getHours()).padStart(2, '0') + ':' + String(b.getMinutes()).padStart(2, '0');
      ganGioCho(); lamTuoiGiaGio();
    } catch (e) { S.tonLoi = true; /* Giữ số cũ và báo chưa cập nhật được. */ }
    if (dangApTon) { dangApTon = false; theoNgayDot(); theoNgayMai(); }
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
      S.cauHinh = ch; S.mienPhiTu = Number(ch.mien_phi_tu) || 0; S.mienPhiKm = Number(ch.mien_phi_km) || 0;
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
    suKien('AddToCart', {content_ids: [o.id], contents: [{id: o.id, quantity: 1}], content_type: 'product', value: o.price, currency: 'VND'});
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
      const x = ADDONS.find(y => y.id === a.id) || (a.id === THIEP_EP_KIM.id ? THIEP_EP_KIM : null);
      return x ? {id: x.id, n: t(x.k, x.n), p: x.p} : null;
    }).filter(Boolean);
    /* v681: giữ nguyên lời chúc, cờ, thiệp từng chiếc; giỏ bản trước thì chuyển sang từng chiếc. */
    return T.chiecTuDongCu({k: c.k, img: c.img, id: z.id, cm: z.cm, price: z.p, nguon: o.nguon === 'today' ? 'today' : 'order', qty: o.qty,
      wish: String(o.wish || '').slice(0, 60), adds, dung_cu: T.chuanDungCu(o.dung_cu), chiec: Array.isArray(o.chiec) ? o.chiec : undefined});
  }
  /* v668 (Codex #581 vòng 2, 3): dòng thêm từ gợi ý là hàng đặt trước. Giỏ có bánh Có
     sẵn hôm nay, kể cả dòng lưu còn chờ danh mục máy chủ, thì bỏ dòng gợi ý để giỏ không
     trộn hai loại. Gọi ở MỌI đường đưa dòng lưu vào giỏ: phục hồi ngay và gắn sau khi
     danh mục về. */
  function boGoiYNeuHomNay() {
    if (!coHomNay()) return;
    for (let i = S.CART.length - 1; i >= 0; i--) if (S.CART[i].goi_y) S.CART.splice(i, 1);
  }
  function ganGioCho() {
    if (!S.gioCho.banh.length) return;
    const con = [];
    S.gioCho.banh.forEach(o => { const d = dongGioTuLuu(o); if (d) S.CART.push(d); else con.push(o); });
    /* Danh mục đã về mà vẫn không có món: món đã ngừng bán, không giữ nữa. */
    S.gioCho.banh = S.tonNapXong ? [] : con;
    boGoiYNeuHomNay();
  }
  function lamTuoiGiaGio() {
    S.CART.forEach(o => {
      /* v671: bỏ dòng hàng mùa vụ (cm 0, không nguồn) và món gợi ý; bánh một cỡ (cm 0, có nguồn) vẫn làm tươi giá. */
      if (!o.cm && (!o.nguon || o.goi_y)) return;
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
      /* v681: trang /banh cũ (dự phòng) chỉ đọc lời chúc theo dòng: ghi kèm lời chúc chiếc đầu. */
      const gioLuu = S.CART.map(o => (Array.isArray(o.chiec) ? Object.assign({}, o, {wish: (o.chiec.find(c => c.co !== false && c.wish) || {}).wish || ''}) : o));
      luuTru.setItem(KHOA_LUU, JSON.stringify({luc: bayGio().getTime(), gio: gioLuu.concat(S.gioCho.mua, S.gioCho.banh),
        ngay: S.ngayChon, slot: S.pickedSlot, daChonNgay: S.daChonNgay, daChonGio: S.daChonGio, truong, dc: {...S.DC},
        co: {mode: S.CO.mode, pickupId: S.CO.pickupId, pay: S.CO.pay, other: S.CO.other, gift: S.CO.gift, vat: S.CO.vat, phuong: S.CO.phuong, nonce: S.CO.nonce,
          gc: S.CO.gc.slice(), gcGio: S.CO.gcGio}}));
    } catch (e) { /* kho phiên bị chặn: bỏ qua */ }
  }
  function phucHoiGio() {
    if (xemThu()) return;
    try {
      const d = JSON.parse((luuTru && luuTru.getItem(KHOA_LUU)) || 'null');
      if (!d || bayGio().getTime() - d.luc > 86400000 || !Array.isArray(d.gio)) return;
      const hop = o => typeof o.id === 'string' && Number.isInteger(o.qty) && o.qty > 0 && o.qty <= 99;
      /* v671: dòng cm 0 có nguồn (hôm nay, đặt trước) là bánh một cỡ (hũ, hộp của đợt
         Đặc biệt tuần này), không phải hàng mùa vụ; trước đây bị bỏ khi khôi phục giỏ. */
      const laMua = o => o.cm === 0 && !o.nguon;
      S.gioCho.mua = d.gio.slice(0, 50).filter(o => laMua(o) && !o.goi_y && hop(o));
      const luu = d.gio.slice(0, 50).filter(o => (o.cm !== 0 || (o.nguon && !o.goi_y)) && hop(o));
      S.CART.splice(0); S.gioCho.banh = [];
      /* Giỏ lưu bản trước ghi nĩa, dĩa theo từng bánh: dồn về số của đơn, không mất yêu cầu của khách. */
      Object.assign(S.DC, T.gomDcCu(luu, d.dc));
      /* v668: món thêm từ gợi ý giữ nguyên dòng; máy chủ tính lại giá khi gửi. */
      d.gio.slice(0, 50).filter(o => o.cm === 0 && o.goi_y && hop(o) && /^[A-Z0-9-]{3,40}$/.test(o.id)).forEach(o => S.CART.push({
        k: String(o.k || o.id).slice(0, 120), img: typeof o.img === 'string' ? o.img : '', id: o.id, cm: 0, price: Number(o.price) || 0,
        nguon: 'order', wish: '', adds: [], qty: o.qty, goi_y: 1}));
      luu.forEach(o => { const x = dongGioTuLuu(o); if (x) S.CART.push(x); else S.gioCho.banh.push(o); });
      boGoiYNeuHomNay();
      if (S.tonNapXong) ganGioCho();
      if (/^\d{4}-\d{2}-\d{2}$/.test(d.ngay || '')) S.ngayChon = d.ngay;
      if (Number.isInteger(d.slot) && SLOTS[d.slot]) S.pickedSlot = d.slot;
      S.daChonNgay = d.daChonNgay === true && picked.value >= 0;
      S.daChonGio = d.daChonGio === true && gioHopLe.value;
      const c = d.co || {};
      S.CO.mode = c.mode === 'pick' ? 'pick' : 'ship';
      S.CO.pay = PT_HOP_LE.includes(c.pay) ? c.pay : 'bank';
      /* Codex #594: giỏ lưu cách thanh toán nay không còn (tiền mặt) thì báo khách xem lại. */
      if (typeof c.pay === 'string' && c.pay && !PT_HOP_LE.includes(c.pay)) S.CO.payBao = true;
      S.CO.pickupId = typeof c.pickupId === 'string' ? c.pickupId : '';
      if (S.CO.pickupId && !S.PICKUPS.some(x => x.id === S.CO.pickupId)) S.CO.pickupId = '';
      if (!S.PICKUPS.length) S.CO.mode = 'ship';
      ['other', 'gift', 'vat'].forEach(k => { S.CO[k] = c[k] === true; });
      /* v684: giỏ lưu từ trước bản này có khoá quan (khu vực cũ): bỏ, khách chọn lại phường. */
      S.CO.phuong = typeof c.phuong === 'string' && timPhuong(c.phuong) ? c.phuong : '';
      S.CO.gc = Array.isArray(c.gc) ? c.gc.filter(ma => GHI_CHU_NHANH.some(x => x.ma === ma)).slice(0, 10) : [];
      S.CO.gcGio = typeof c.gcGio === 'string' && gioTreChon.value.includes(c.gcGio) ? c.gcGio : '';
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
  watch(() => [S.CART, S.DC, S.f, S.CO.mode, S.CO.pickupId, S.CO.pay, S.CO.other, S.CO.gift, S.CO.vat, S.CO.phuong, S.CO.nonce, S.CO.gc, S.CO.gcGio,
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
  /* v667: giỏ vừa có món của đợt cuối tuần mà ngày đang chọn không phải ngày giao
     thì dời sang ngày giao gần nhất còn trên lịch, nhờ khách xác nhận lại lịch. */
  function theoNgayDot() {
    if (dangApTon) return;
    if (!dotDbt.value || !D.gioCoMonDot(S.CART, maDbt.value) || !dbtChan(picked.value)) return;
    const i = ngayRail.value.findIndex(d => d.i > 0 && !d.off);
    if (i < 0) return;
    neoNgay(ngayRail.value[i].i); S.daChonNgay = false;
    if (fixSlot()) S.daChonGio = false;
  }
  watch(() => [S.CART.length, dotDbt.value, maDbt.value, picked.value], theoNgayDot, {flush: 'sync'});
  /* v671: ngày nhận đang chọn xa hơn ngày mai mà giỏ có bánh đặt trước thường
     (hay khách đang ở tab Đặt bánh trước, ngày đó không thuộc mẻ hay đợt trong
     giỏ) thì dời về ngày còn nhận gần nhất và nhờ khách xác nhận lại lịch.
     Ngày cũ có thể đến từ giỏ lưu hôm trước. */
  function theoNgayMai() {
    /* Đang phục hồi giỏ lưu thì chờ xong (cờ đã chọn ngày được phục hồi sau ngày).
       Codex #594: chưa áp xong số tồn (bảng số còn rỗng) thì chưa xét, giữ ngày khách
       đã chọn; tải tồn lỗi thì cũng giữ, máy chủ kiểm lại lúc gửi đơn. */
    if (!S.daPhucHoi || !S.tonNapXong || dangApTon) return;
    const p = picked.value;
    if (!(datTruocChan(p) || (S.tab === 'order' && p > 1 && !ngayCuaTabTruoc(p)))) return;
    const d = ngayRail.value.find(x => x.i > 0 && !x.off && (S.tab !== 'order' || ngayCuaTabTruoc(x.i)));
    if (!d) return;
    neoNgay(d.i); S.daChonNgay = false;
    if (fixSlot()) S.daChonGio = false;
  }
  watch(() => [S.CART.map(o => o.id + ':' + (o.goi_y ? 1 : 0)).join(','), maDbt.value, picked.value, S.tab, S.TRUOC_RF, S.daPhucHoi, S.tonNapXong], theoNgayMai, {flush: 'sync', immediate: true});
  /* v668: giỏ đổi bánh thì hỏi lại khối gợi ý (không gọi dịch vụ ngoài, máy chủ tự xếp). */
  watch(() => S.CART.map(o => o.id).join(','), () => { void napGoiY(); });

  /* v638: gọi món tại bàn qua QR, kho riêng (kho-goi-ban.js) dùng chung S. */
  /* v678: chep (chép vào bộ nhớ tạm) đọc lúc gọi, để bộ kiểm cấp được. */
  const goiBan = taoGoiBan({t, doc, ghi, luuTru, ngauNhien, hen, huyHen, toast, napQuay,
    timKiem: moiTruong.timKiem || (() => ''), chep: s => (moiTruong.chep ? moiTruong.chep(s) : (typeof navigator !== 'undefined'
      && navigator.clipboard ? navigator.clipboard.writeText(s) : null))}, S);

  return {S, T, goiBan, picked, slotOk, firstOk, ngayDangChon, slotDangChon, gioHopLe, daChot, hienTomTat, nhanNgayDangChon, chotDon, veHomNay,
    ngayRail, ngayRailDatTruoc, homNayBiChan, khungRail, pick, pickSlot, nhanRefill, doiLich, mocGioNhan, ghiChuDatTruoc, ghiChuGio, fixSlot,
    dotDbt, maDbt, lucDbt, goiYGio, thanhMienPhiGio, themGoiY, napGoiY,
    coTruoc, banhHomNay, banhDatTruoc, tongTon, kichThuocDangBan, dongTrangThai, ghiChuHomNay, theBanh,
    curSize, moBanh, dongBanh, setSize, doiSoLuong, toggleNum, clearNums, toggleAdd, phuKienChon, tienNutThem,
    gioiHanNhan, soDatTruoc, chuHetNgay, addToCart, themNhanh, suaDongGio,
    soBanh, tienBanh, cartQty, cartRemove, doiDc, dongGio,
    giaThiep, dsChiec, datCo, datThiep, batThiep, moMauCo, chiecMauCo, soThiepEpKim, dongYBo, giuLai,
    gcHien, gioTreChon, doiGc, chonGioTre, theTomTat, khoaUuDai, uuHienTai, giam, xemUuDai, apMaUuDai, goiYMa,
    theDonDau, guiMaDonDau, xacThucDonDau, theDiem, dungDiem, tienDiem, theThanhVien, daXacThuc, nhapMa, xoaLuiMa, doiSo,
    mienPhi, quoteShip, apPhiGiao, setMode, phuongDangChon, goiYPhuong, theoPhuong, moPhuong, goPhuong, dongPhuong, chonPhuong, boPhuong, diemNhanChon, setPickup, capNhatDiemNhan, tong, dongMienPhi,
    paysHien, cauThanhToan, kiemGioiThieu, coGioiThieu,
    lookupPhone, diaChiLuu, selAddr, goiYDiaChi, chonGoiY, lookupMst,
    moGio, roiGio, submitOrder,
    napTon, napMua, napQuay, napCauHinh, coMua, timMonMua, themHangMua, hanMua,
    phucHoiGio, luuGio, toast, nhip: dongHoNhich, lyDo};
}

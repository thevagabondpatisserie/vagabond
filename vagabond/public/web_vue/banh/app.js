/* Trang đặt bánh bản Vue. Giao diện giữ ĐÚNG Rocca đã duyệt: cùng CSS, cùng
   thẻ và lớp như banh.html (a20e85054). Khác bản cũ ở phần chạy bên trong:
   mọi chỗ hiện số đọc từ kho (kho-banh.js), đổi dữ liệu là màn tự đổi.

   Đường dẫn giữ như cũ để link đã gửi khách vẫn mở đúng:
     #/            bánh có sẵn hôm nay       #/dat-truoc   đặt bánh trước
     #/banh/<ten>  chi tiết một bánh         #/gio-hang    thông tin đơn
     #/in-season[/<ma>]  hàng mùa vụ         #/in-store    bánh trên tủ quầy
     #/uu-dai  #/ve-su-kien  #/tuyen-dung    ba chuyên mục (#/tiec cũ mở Vé sự kiện)
     #/tuyen-dung/<mã vị trí>                chi tiết một vị trí (v625) */
import {createApp, computed, watch, nextTick} from '../lib/vue.esm-browser.prod.js';
import {ND, t, tMon, napNoiDung, laXemThu, telChu, telSo, mxh, anhWeb} from '../kho/chu.js';
import {doc, ghi} from '../kho/api.js';
import {taoKho} from './kho-banh.js';
import {DAYS, ACC, NUMS, ADDONS, PAYS, ANH_NEN, HUONG_SIZE, DUNG_CU_DON, THIEP_EP_KIM, ANH_CO, LOGO_TT} from './du-lieu.js';
import {LOGO} from './anh.js';
import {DongChu, BieuTuong, AnhMon} from './thanh-phan.js';
import {KhoiNoiDung, TieuDeMuc, KenhNoi, ChuyenMuc, dsMuc, TD, UD} from './noi-dung.js';
import {thuong} from './chu-giau.js';
import {MAU} from './mau.js';
import {ChanTrang, locChinhSach} from './chan-trang.js';
import {ThietKeRieng, moTacPham, veDanhSach, dsTacPham} from './thiet-ke-rieng.js';
import {GoiTaiBan, GoiTaiBanNoi} from './goi-tai-ban.js';
import {dungQuayHien, tenQuayHaiDong} from './kho-goi-ban.js';
import {VanhNghieng, xepMuc} from './vanh.js';
import {VeSuKien, dongSheet as dongSheetVe} from './ve-su-kien.js';
import {DacBietTuan} from './dac-biet-tuan.js';
import {GoiYMua} from './goi-y-mua.js';
import {gaTuMeta} from '../kho/thuan.js';
import {laMienSach, manHienTai, diaChiMan, doiLinkCu, hrefMan} from './duong-sach.js';

function luuTruAnToan() {
  try { const s = window.sessionStorage; s.getItem('x'); return s; } catch (e) { return null; }
}
function ngauNhien(n) {
  try { const a = new Uint8Array(n); (window.crypto || self.crypto).getRandomValues(a); return Array.from(a); } catch (e) { return null; }
}

export function khoiDong(goc = '#app') {
  /* Codex #489 P2: biết mình là khung xem thử của Editor NGAY từ đầu, trước khi
     kho phục hồi giỏ của phiên (cùng sessionStorage với tab Editor). Trước đây
     cờ này chỉ được đặt trong napNoiDung, chạy SAU phucHoiGio, nên khung xem
     thử hiện giỏ và thông tin khách cũ. Cùng một hàm laXemThu với napNoiDung. */
  ND.xemThu = laXemThu(window);
  const pixel = {id: ''};
  const suKien = (ten, du) => {
    try { if (pixel.id && typeof window.fbq === 'function') window.fbq('track', ten, du); } catch (e) { /* im lặng */ }
    /* v664: cùng chỗ bắn Pixel thì bắn GA4. Thẻ GA trong <head> chỉ nạp khi Cài đặt có mã
       và không ở khung xem thử, nên không có window.gtag là không gửi. */
    try { const g = ND.xemThu ? null : gaTuMeta(ten, du); if (g && typeof window.gtag === 'function') window.gtag('event', g[0], g[1]); } catch (e) { /* im lặng */ }
  };
  const kho = taoKho({t, tMon, doc, ghi, luuTru: luuTruAnToan(), suKien, ngauNhien, xemThu: () => ND.xemThu, mxh, nd: ND,
    cookie: () => document.cookie, timKiem: () => location.search});
  const S = kho.S;

  /* v598 (port v597): hộp Cách chọn size. Đóng bảng chi tiết hay đổi đường dẫn thì hộp đóng theo. */
  function moHuongSize() { S.huongSize = true; }
  function dongHuongSize() { S.huongSize = false; }
  watch(() => S.trang, v => { if (v !== 'banh') S.huongSize = false; });
  watch(() => S.huongSize, mo => document.body.classList.toggle('hs-mo', !!mo));
  /* Escape chỉ đóng hộp, không đóng luôn bảng chi tiết phía sau: bắt ở pha capture
     và chặn lan truyền khi hộp đang mở. */
  document.addEventListener('keydown', e => {
    if (e.key !== 'Escape' || !(S.hoiBo || S.mauCo || S.huongSize)) return;
    e.stopImmediatePropagation(); e.preventDefault();
    /* Codex #603: Escape đóng hộp trên cùng; hỏi bỏ chiếc thì Escape là Giữ lại. */
    if (S.hoiBo) kho.giuLai(); else if (S.mauCo) kho.moMauCo(''); else dongHuongSize();
  }, true);

  const app = createApp({
    template: MAU,
    components: {DongChu, BieuTuong, AnhMon, KhoiNoiDung, TieuDeMuc, KenhNoi, ChuyenMuc, ChanTrang, ThietKeRieng, GoiTaiBan, GoiTaiBanNoi, VanhNghieng, VeSuKien, DacBietTuan, GoiYMua},
    setup() {
      const tab = computed(() => S.tab);
      const gioMo = computed(() => S.trang === 'gio');
      const coTiec = computed(() => dsMuc('tiec').length > 0);
      /* v630: tab Thiết kế riêng chỉ hiện khi có tác phẩm đang nhận đặt. */
      const coTkr = computed(() => dsTacPham().length > 0);
      const coQuay = computed(() => true);
      /* v662 (anh Việt 15/11/2026): O2O là trang riêng chỉ mở bằng QR dán trên bàn.
         Link QR đúng thì vành chỉ còn Tại quầy (menu của đúng quầy đó), khách không
         lạc sang đặt bánh trước; link QR đã in vẫn dùng được, không in lại. */
      const coQr = computed(() => !!(kho.goiBan.G.ban && kho.goiBan.G.ban.ok));
      /* v658: các mục của Vành nghiêng = các tab đang hiện, cùng điều kiện ẩn hiện
         của dải tab cũ (In season, Tại quầy, Thiết kế riêng bật tắt theo dữ liệu),
         xếp theo thứ tự anh Việt duyệt (vanh.js THU_TU_MUC). */
      const mucVanh = computed(() => xepMuc([
        {tab: 'season', nhan: t('tab_season', 'In season'), hien: !!kho.coMua.value, lop: 'mua'},
        {tab: 'store', nhan: t('tab_store', 'Tại quầy'), hien: !!(S.storeDaTai || S.storeLoi), lop: 'store'},
        {tab: 'uu_dai', nhan: t('tab_uu_dai', 'Ưu đãi'), hien: true},
        /* Tab Tiệc nâng thành Vé sự kiện (anh Việt chọn A 14/11/2026): luôn hiện, chưa có sự kiện thì mời theo dõi tiệm. */
        {tab: 'tiec', nhan: t('tab_ve_su_kien', 'Vé sự kiện'), hien: true, moi: true},
        /* v667: Đặc biệt tuần này, chỉ hiện khi có đợt đang hiện (trình biên tập, thẻ Cuối tuần). */
        {tab: 'dac_biet', nhan: t('tab_dac_biet', 'Đặc biệt tuần này'), hien: !!kho.dotDbt.value},
        {tab: 'tuyen_dung', nhan: t('tab_tuyen_dung', 'Tuyển dụng'), hien: true},
        {tab: 'today', nhan: t('tab_today', 'Có sẵn hôm nay'), hien: true},
        {tab: 'order', nhan: t('tab_order', 'Đặt bánh trước'), hien: true},
        {tab: 'thiet_ke_rieng', nhan: t('tab_thiet_ke_rieng', 'Thiết kế riêng'), hien: coTkr.value},
      ].filter(m => m.hien && (!coQr.value || m.tab === 'store'))));
      /* v638: tab Tại quầy có bánh trên tủ và đồ uống; chip Tất cả, Bánh trên tủ,
         Đồ uống; mở từ QR một bàn thì chỉ còn quầy của bàn đó (kho-goi-ban.js). */
      const quayHien = computed(() => dungQuayHien(S, kho.goiBan.G, t));
      /* v639: nút chuông nổi chỉ khi đang ở tab Tại quầy ở chế độ gọi món; banner
         nhắc quét QR khi mở tab mà không có mã bàn (biểu thức && để ngoài khuôn). */
      const chuongQuay = computed(() => (kho.goiBan.cheDo.value === 'goi' && S.tab === 'store') ? kho.goiBan.moChuong : null);
      const nhacQr = computed(() => kho.goiBan.G.daKiem && !!quayHien.value);
      /* v667 (anh Việt 17/11/2026): tab Tại quầy trên trang chủ (chế độ giao) bỏ khung chú
         thích đầu tab; khung vẫn giữ cho gọi món tại bàn và ngoài giờ. */
      const gbDauHien = computed(() => !!kho.goiBan.cheDo.value && kho.goiBan.cheDo.value !== 'giao');
      const nhacQrHien = computed(() => nhacQr.value && !kho.goiBan.cheDo.value);
      const chinhSach = computed(() => locChinhSach(S.cauHinh && S.cauHinh.chinh_sach, location.pathname));
      const baoMat = computed(() => chinhSach.value.find(c => c.khoa === 'chinh_sach_bao_mat') || null);
      const ngayBan = computed(() => { void S.nhip; const b = new Date(); return DAYS[b.getDay()] + ', ' + kho.T.dmy(b); });
      const theHomNay = computed(() => kho.banhHomNay.value.map(c => kho.theBanh(c, 'today')));
      const theDatTruoc = computed(() => kho.banhDatTruoc.value.map(c => kho.theBanh(c, 'order')));
      const kichThuoc = computed(() => (S.cur ? kho.kichThuocDangBan(S.cur) : []));
      const chiTiet = computed(() => {
        const c = S.cur, sz = kho.curSize.value;
        if (!c || !sz) return null;
        const ma = sz.id, banh = t('dat_banh_3556aabb5', 'bánh');
        /* v677 (Codex và anh Việt 19/11/2026): mở bánh từ tab Đặt bánh trước thì
           không ghi "Có sẵn hôm nay" theo tủ hôm nay; ghi số của ngày nhận đang
           chọn, cùng số với thẻ và giỏ (kho.soDatTruoc). */
        const homNay = S.tab === 'today';
        const avail = homNay ? c.sizes.filter(s => S.TODAY[s.id] > 0) : [];
        const nTruoc = homNay ? null : kho.soDatTruoc(ma);
        const nh = kho.nhanNgayDangChon();
        const nhanMua = tMon(c.sizes[0].id, 'theo_mua', c.seasonal);
        const tangChu = tMon(ma, 'tang', '');
        /* v644: bánh có bộ nội dung web thì chữ riêng từng mã ở mục Nội dung bánh (Nâng cao) không đè lên. */
        const tang = !c.tuWeb && tangChu ? tangChu.split('\n').filter(x => x.trim()).map(x => [x, '']) : c.layers;
        const anhs = (c.anhs && c.anhs.length ? c.anhs : (c.img ? [c.img] : [])).slice(0, 5);
        return {c, ten: tMon(ma, 'ten', c.k), vi: kho.T.laChuViet(c.k), moTa: c.tuWeb ? c.desc : tMon(ma, 'mo_ta', c.desc), tang, anhs, diUng: c.diUng || '', baoQuan: c.baoQuan || '',
          tinhTrang: avail.length ? 'co' : (nTruoc !== null ? 'dat' : (nhanMua ? 'mua' : 'truoc')), nhanMua,
          datChu: nTruoc === null ? '' : t('ct677_dat_truoc_ngay', 'Đặt trước, nhận {ngay}', {ngay: nh.ngay}) + ' · '
            + (nTruoc > 0 ? kho.T.nhanTon(nTruoc, banh, t) : t('ct677_het_ngay_nay', 'hết ngày này, quý khách chọn ngày khác')),
          tonChu: avail.length ? kho.T.nhanTon(avail.reduce((a, s) => a + S.TODAY[s.id], 0), banh, t) : ''};
      });
      const anhChon = computed({get: () => S.anhChon || 0, set: v => { S.anhChon = v; }});
      const kichThuocDong = computed(() => kichThuoc.value.map(s => {
        /* v677: tab Có sẵn hôm nay theo tủ; tab khác theo số của ngày đang chọn (kho.soDatTruoc). */
        const homNay = S.tab === 'today', banh = t('dat_banh_3556aabb5', 'bánh');
        const n = homNay ? (S.TODAY[s.id] || 0) : 0;
        const so = homNay ? null : kho.soDatTruoc(s.id);
        const tr = so === null ? (homNay ? 0 : (S.TRUOC[s.id] || 0)) : so;
        const kp = tMon(s.id, 'khau_phan', s.serve);
        return {s, gia: kho.T.tienVN(s.p), nhan: s.cm ? t('dat_banh_2540d6d0f', 'Ø {gia_tri_a}cm{gia_tri_b}', {gia_tri_a: s.cm, gia_tri_b: kp ? ' · ' + kp : ''})
          : t('dat_banh_8a6c6356d', '1 cỡ') + (kp ? ' · ' + kp : ''),
          em: n ? kho.T.nhanTon(n, banh, t) : (tr > 0 ? (kho.nhanRefill(s.id) || t('san_pham_dat_truoc', 'Đặt trước')) + ' · ' + kho.T.nhanTon(tr, banh, t)
            : (so !== null ? kho.chuHetNgay() : ''))};
      }));
      const tomTatLich = computed(() => { const nh = kho.nhanNgayDangChon(); return nh.ten + ', ' + nh.ngay + ' · ' + kho.slotDangChon.value.t; });
      const hangTomTat = computed(() => {
        const ra = [];
        S.CART.forEach(o => {
          const x = o.qty > 1 ? ' ' + t('dat_banh_67fba2f35', '×') + ' ' + o.qty : '';
          ra.push({k: o.id + 'b' + ra.length, nhan: tMon(o.id, 'ten', o.k) + (o.cm ? ' · Ø ' + o.cm + 'cm' : '') + x, gia: kho.T.tienVN(o.price * o.qty)});
          o.adds.forEach(a => ra.push({k: a.id + 'a' + ra.length, nhan: '+ ' + a.n + x, gia: kho.T.tienVN(a.p * o.qty)}));
        });
        return ra;
      });
      const monMua = computed(() => (S.MUA.mon || []).map(m => ({m, ten: tMon(m.ma, 'ten', m.ten), moTa: tMon(m.ma, 'mo_ta', m.ruot),
        chip: m.het ? t('dat_banh_053152152', 'Tạm hết') : kho.T.nhanTon(m.con, t('dat_banh_d2cd4ec77', 'phần'), t)})));
      const muaXem = computed(() => {
        const m = S.muaDangXem; if (!m) return null;
        const moTa = tMon(m.ma, 'mo_ta', m.ruot);
        return {m, ten: tMon(m.ma, 'ten', m.ten), ruot: kho.T.tachRuot(moTa),
          tinh: m.het ? t('dat_banh_7fbd55eb5', 'Hết hàng mùa này') : (S.MUA.ten_mua || t('dat_banh_d7e8f3298', 'Hàng theo mùa')) + ' · ' + kho.T.nhanTon(m.con, t('dat_banh_d2cd4ec77', 'phần'), t)};
      });
      const tienTom = n => kho.T.tienVN(n);
      return {S, ND, kho, t, tMon, telChu, telSo, LOGO, ANH_NEN, ACC, NUMS, ADDONS, DUNG_CU_DON, PAYS, HUONG_SIZE, THIEP_EP_KIM, ANH_CO, LOGO_TT, anhWeb, moHuongSize, dongHuongSize, tab, gioMo, coTiec, coTkr, coQuay, mucVanh, quayHien, tenQuayHaiDong, chuongQuay, nhacQr, gbDauHien, nhacQrHien, chinhSach, baoMat,
        ngayBan, theHomNay, theDatTruoc, chiTiet, anhChon, kichThuocDong, tomTatLich, hangTomTat, monMua, muaXem, tienTom, thuong,
        go, nav, navBack, hm: x => hrefMan(SACH, x), moBanh: c => nav('#/banh/' + kho.T.slug(c.k)), themNhanh, themVaoGio, suaDongGio, moGio, guiDon,
        moMua: m => nav('#/in-season/' + m.ma), themTuMua, tgl, gioMo2: () => nav('#/gio-hang'), mxh, chonNguoiNhan, cuonToi, dongYBo, nhapOMa, phimOMa, doiSoDt};
    }
  });

  /* ---------------- điều hướng ---------------- */
  /* v692: tên miền khách dùng đường sạch /<màn>, tên miền khác giữ #/<màn> (duong-sach.js). */
  const SACH = laMienSach(location.hostname);
  function man() { return manHienTai(SACH, location.pathname, location.hash); }
  function nav(h, thay) {
    const url = diaChiMan(SACH, h, location.pathname, location.search);
    if (thay) history.replaceState({vgb: 1}, '', url); else history.pushState({vgb: 1}, '', url);
    apDuongDan();
  }
  function navBack() {
    if (history.state && history.state.vgb) history.back();
    else nav(S.tab === 'order' ? '#/dat-truoc' : S.tab === 'dac_biet' ? '#/dac-biet-tuan-nay' : '#/', true);
  }
  function go(tab) {
    if (tab === 'uu_dai' || tab === 'tuyen_dung') { nav('#/' + tab.replace('_', '-')); window.scrollTo(0, 0); return; }
    if (tab === 'tiec') { nav('#/ve-su-kien'); window.scrollTo(0, 0); return; }
    if (tab === 'dac_biet') { nav('#/dac-biet-tuan-nay'); window.scrollTo(0, 0); return; }
    if (tab === 'thiet_ke_rieng') { nav('#/thiet-ke-rieng'); window.scrollTo(0, 0); return; }
    nav(tab === 'season' ? '#/in-season' : tab === 'store' ? '#/in-store' : tab === 'order' ? '#/dat-truoc' : '#/');
    window.scrollTo({top: 0, behavior: 'smooth'});
  }
  S.trang = 'danh_muc';
  function apDuongDan() {
    kho.nhip();
    const h = man();
    const mBanh = h.match(/^\/banh\/(.+)$/), mMua = h.match(/^\/in-season\/(.+)$/);
    const truocDo = S.trang;
    /* v625: trang chi tiết một vị trí tuyển dụng. */
    const mTd = h.match(/^\/tuyen-dung\/(.+)$/);
    TD.mo = mTd ? decodeURIComponent(mTd[1]) : '';
    if (mTd) { dongHet(); S.tab = 'tuyen_dung'; return; }
    /* v645: trang chi tiết một ưu đãi. */
    const mUd = h.match(/^\/uu-dai\/(.+)$/);
    UD.mo = mUd ? decodeURIComponent(mUd[1]) : '';
    if (mUd) { dongHet(); S.tab = 'uu_dai'; return; }
    /* v630: #/thiet-ke-rieng (danh sách) và #/thiet-ke-rieng/<mã tác phẩm>. */
    const mTkr = h.match(/^\/thiet-ke-rieng(?:\/(.+))?$/);
    if (mTkr) { dongHet(); S.tab = 'thiet_ke_rieng'; if (mTkr[1]) moTacPham(decodeURIComponent(mTkr[1])); else veDanhSach(); return; }
    if (h === '/uu-dai' || h === '/tuyen-dung') { dongHet(); S.tab = h.slice(1).replace('-', '_'); return; }
    /* v658: Vé sự kiện; link #/tiec cũ đã gửi khách vẫn mở đúng tab. */
    if (h === '/ve-su-kien' || h === '/tiec') { dongHet(); S.tab = 'tiec'; return; }
    if (h === '/dac-biet-tuan-nay') { dongHet(); S.tab = 'dac_biet'; return; }
    if (mBanh) {
      const c = S.CAKES.find(x => kho.T.slug(x.k) === mBanh[1]);
      /* Codex #462: bánh bếp thêm tay chỉ có sau lần nạp tồn đầu. Chưa nạp
         xong thì GIỮ đường dẫn, napTon().then(apDuongDanNeuBanh) mở lại sau. */
      if (!c) { if (S.tonDaThu) nav('#/', true); return; }
      /* Link chia sẻ mở mới: bánh không còn hôm nay vẫn cho chọn cỡ đặt trước. */
      /* v675: chỉ kết luận "không còn hôm nay" SAU khi đã nạp tồn. Trước: mở thẳng link bánh thì tồn chưa
         về, bánh có sẵn hôm nay bị thêm vào giỏ thành bánh đặt trước nhận ngày mai dù trang ghi Có sẵn hôm nay. */
      if (S.tab === 'today' && S.tonDaThu && !c.sizes.some(s => S.TODAY[s.id] > 0)) S.tab = 'order';
      if (!(S.dongDangSua >= 0 && S.cur === c)) { S.dongDangSua = -1; kho.moBanh(c); }
      S.anhChon = 0;
      if (truocDo === 'gio') kho.roiGio();
      S.muaDangXem = null; S.trang = 'banh';
      return;
    }
    if (mMua) {
      const m = kho.timMonMua(decodeURIComponent(mMua[1]));
      S.cur = null; if (truocDo === 'gio') kho.roiGio();
      S.tab = 'season'; S.muaDangXem = m; S.trang = m ? 'mua' : 'danh_muc';
      return;
    }
    if (/^\/gio-hang/.test(h)) {
      if (!S.CART.length) { nav('#/', true); return; }
      S.cur = null; S.muaDangXem = null; S.trang = 'gio';
      if (truocDo !== 'gio') { kho.moGio(); nextTick(() => { const co = document.getElementById('checkout'); if (co) co.scrollTop = 0; }); }
      return;
    }
    dongHet();
    S.tab = /^\/in-season/.test(h) ? 'season' : /^\/in-store/.test(h) ? 'store' : /^\/dat-truoc/.test(h) ? 'order' : 'today';
  }
  function dongHet() {
    dongSheetVe();
    if (S.trang === 'gio') kho.roiGio();
    S.cur = null; S.dongDangSua = -1; S.muaDangXem = null; S.trang = 'danh_muc';
  }
  window.addEventListener('popstate', apDuongDan);

  function themNhanh(c, cheDo) { if (kho.themNhanh(c, cheDo) === 'mo') nav('#/banh/' + kho.T.slug(c.k)); else nhichThanh(); }
  function themVaoGio() {
    const kq = kho.addToCart();
    /* v681: 'hoi' là đang hỏi lại khách trước khi bỏ chiếc có lời chúc (hộp #hoiBo). */
    if (kq === 'sua') nav('#/gio-hang', true);
    else if (kq === 'them') { nhichThanh(); navBack(); }
  }
  function suaDongGio(i) { const c = kho.suaDongGio(i); if (!c) return; const giu = S.dongDangSua; nav('#/banh/' + kho.T.slug(c.k)); S.dongDangSua = giu; }
  function moGio() { if (!S.CART.length) { kho.toast(t('dat_banh_28c1cf2d1', 'Giỏ chưa có bánh nào')); return; } nav('#/gio-hang'); }
  function themTuMua() { if (S.muaDangXem && kho.themHangMua(S.muaDangXem.ma)) nhichThanh(); }
  function tgl(k) {
    S.CO[k] = !S.CO[k];
    if ((k === 'other' || k === 'vat') && S.CO[k]) nextTick(() => { const o = document.querySelector(k === 'other' ? '#otherBlock input' : '#vatBlock input'); if (o) o.focus(); });
  }
  function nhichThanh() { S.nhich = (S.nhich || 0) + 1; }
  /* v681: Người nhận chọn MỘT (nút tròn). Chọn Người khác nhận thì mở ô và đưa con trỏ vào. */
  /* v682 (BẢN 2 mục 2.2): sáu ô mã Zalo. Kho giữ mã, ở đây chỉ dời con trỏ giữa các ô. */
  const oMa = i => document.getElementById(i === 0 ? 'ddMa' : 'ddMa' + (i + 1));
  function nhapOMa(i, e) {
    const toi = kho.nhapMa(i, e.target.value);
    e.target.value = (S.CO.dd.ma || '')[i] || '';
    nextTick(() => { const o = oMa(toi); if (o && S.CO.dd.buoc === 'ma') o.focus(); });
  }
  function phimOMa(i, e) {
    if (e.key === 'Backspace' && !e.target.value && i > 0) { e.preventDefault(); const toi = kho.xoaLuiMa(i); nextTick(() => { const o = oMa(toi); if (o) o.focus(); }); }
    else if (e.key === 'ArrowLeft' && i > 0) { e.preventDefault(); oMa(i - 1).focus(); }
    else if (e.key === 'ArrowRight' && i < 5) { e.preventDefault(); oMa(i + 1).focus(); }
    else if (e.key === 'Enter') { e.preventDefault(); kho.xacThucDonDau(); }
  }
  function doiSoDt() { kho.doiSo(); nextTick(() => { const o = document.getElementById('f-phone'); if (o) { o.focus(); if (o.select) o.select(); } }); }
  function chonNguoiNhan(khac) {
    S.CO.other = !!khac;
    if (khac) nextTick(() => { const o = document.querySelector('#otherBlock input'); if (o) o.focus(); });
  }
  function dongYBo() { if (kho.dongYBo() === 'sua') nav('#/gio-hang', true); }

  const CHO = {lich: '#c-days', ten: '#f-name', sdt: '#f-phone', diem_nhan: '#pickList', dia_chi: '#f-addr', cach_nhan: '#m-pick', dong_y: '#c-dongy', uu_dai: '#sum', ghi_chu: '#f-note'};
  async function guiDon() {
    const kq = await kho.submitOrder();
    if (kq.buoc === 'xong' && kq.duong_dan) { location.assign(location.pathname.startsWith('/web_moi/') ? '/web_moi' + kq.duong_dan : kq.duong_dan); return; }
    await cuonToi(kq.buoc, kq.sel);
  }
  /* Cuộn tới ô cần sửa. v681: thẻ tóm tắt bấm "Chọn giờ", "Nhập địa chỉ" cũng về đây;
     bước gửi đơn có thể chỉ đúng ô (kq.sel, ví dụ thẻ lời chúc của một chiếc). */
  async function cuonToi(buoc, selRieng) {
    if (buoc === 'lich') kho.doiLich();
    const sel = selRieng || CHO[buoc]; if (!sel) return;
    await nextTick();
    const o = document.querySelector(sel); if (!o) return;
    if (o.scrollIntoView) o.scrollIntoView({behavior: 'smooth', block: 'center'});
    const f = buoc === 'lich' ? (o.querySelector('.day.on') || o.querySelector('.day')) : o;
    if (f && f.focus) f.focus();
  }
  /* v681 (BẢN 2 mục 1.2): dòng Mua thêm phụ kiện lấp lánh MỘT lần khi lần đầu lọt vào
     màn hình rồi đứng yên. Máy đặt giảm chuyển động thì không chạy. */
  const giamChuyenDong = () => { try { return !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches); } catch (e) { return true; } };
  watch(() => S.cur, () => nextTick(() => {
    const el = document.getElementById('s-phu-kien');
    if (!el || el.dataset.daLap || giamChuyenDong() || typeof IntersectionObserver !== 'function') return;
    el.dataset.daLap = '1';
    const ob = new IntersectionObserver(ds => {
      if (!ds.some(d => d.isIntersecting)) return;
      el.classList.add('lap'); ob.disconnect();
    }, {threshold: 0.6});
    ob.observe(el);
  }), {flush: 'post'});

  /* Bàn phím trong bảng đang mở (thao-tac.js #460): mở bảng thì đưa con trỏ
     vào nút đầu tiên, Tab quay vòng trong bảng, đóng bảng thì trả con trỏ về
     chỗ cũ. */
  const CHON = 'button:not([disabled]),a[href],input:not([disabled]),select:not([disabled]),textarea:not([disabled]),summary,[tabindex="0"]';
  const nutTrong = el => Array.from(el.querySelectorAll(CHON)).filter(n => n.getClientRects().length);
  /* Hộp nổi nằm trên bảng (Cách chọn size, Mẫu cờ, Hỏi bỏ chiếc; Codex #603): hộp đang mở là
     lớp trên cùng, Tab quay vòng trong hộp. Đóng hộp mà bảng dưới vẫn mở thì con trỏ về đúng
     nút đã mở hộp; đóng hết thì về chỗ cũ trên trang. Ngăn xếp giữ chỗ trả về của từng lớp. */
  const HOP_NOI = ['#hoiBo', '#mauCo', '#huongSize'].map(s => s + ':not([hidden])');
  const BANG = '#sheet.open,#sheetMua.open,#checkout.open';
  const bangMo = () => { for (const s of HOP_NOI) { const el = document.querySelector(s); if (el) return el; } return document.querySelector(BANG); };
  const dangMo = el => el.isConnected && el.matches(HOP_NOI.join(',') + ',' + BANG);
  const dungDuoc = el => !!(el && el.isConnected && el.getClientRects().length && !el.closest('[hidden]'));
  let ngan = [];
  watch(() => [S.trang, S.huongSize, !!S.hoiBo, !!S.mauCo], () => nextTick(() => {
    const moi = bangMo(), dinh = ngan[ngan.length - 1];
    if ((dinh ? dinh.bang : null) === moi) return;
    let traVe = null, dongId = '';
    while (ngan.length && !dangMo(ngan[ngan.length - 1].bang)) { const x = ngan.pop(); traVe = x.truoc; dongId = x.bang.id; }
    ngan = ngan.filter(x => dangMo(x.bang));
    const dinh2 = ngan[ngan.length - 1];
    if (moi && (!dinh2 || dinh2.bang !== moi)) {
      /* Lớp mới: bảng thay bảng (giỏ sang thanh toán) thì giữ chỗ trả về của bảng cũ. */
      ngan.push({bang: moi, truoc: traVe || document.activeElement});
      const n = nutTrong(moi)[0]; if (n) n.focus({preventScroll: true});
      return;
    }
    const nutHs = dongId === 'huongSize' ? document.getElementById('s-huongsize') : null;
    const dich = dungDuoc(traVe) && (!moi || moi.contains(traVe)) ? traVe
      : moi ? (dungDuoc(nutHs) ? nutHs : nutTrong(moi)[0]) : null;
    if (dich) dich.focus({preventScroll: true});
  }), {flush: 'post'});
  document.addEventListener('keydown', e => {
    const bang = bangMo();
    if (e.key !== 'Tab' || !bang) return;
    const nuts = nutTrong(bang); if (!nuts.length) return;
    const dau = nuts[0], cuoi = nuts[nuts.length - 1], hien = document.activeElement;
    if (e.shiftKey && (hien === dau || !bang.contains(hien))) { e.preventDefault(); cuoi.focus(); }
    else if (!e.shiftKey && (hien === cuoi || !bang.contains(hien))) { e.preventDefault(); dau.focus(); }
  });

  /* Hết giờ thì nhãn ngày, khung giờ, tồn đọc lại (đồng hồ tiến mỗi 30 giây). */
  setInterval(() => kho.nhip(), 30000);
  /* Thanh giỏ nhích nhẹ 150 ms khi vừa thêm bánh. */
  watch(() => S.nhich, () => { const b = document.getElementById('bar'); if (!b) return; b.classList.remove('nhich'); void b.offsetWidth; b.classList.add('nhich'); });
  /* Có bảng mở thì khoá cuộn trang nền; Escape đóng bảng. */
  watch(() => S.trang, v => { document.body.style.overflow = (v === 'banh' || v === 'mua') ? 'hidden' : ''; });
  watch(() => S.CART.length > 0, co => document.body.classList.toggle('has-bar', co), {immediate: true});
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && S.trang !== 'danh_muc') navBack(); });
  /* v658: dải tab cuộn ngang đã thay bằng Vành nghiêng (vanh.js), vành tự quay tới mục đang xem. */
  /* Điểm nhận bánh đến từ thẻ Cửa hàng của nội dung web (Codex #453). */
  watch(() => ND.diem_nhan, ds => kho.capNhatDiemNhan(ds));
  /* Trình biên tập chọn khối ưu đãi/tuyển dụng thì mở đúng chuyên mục. */
  window.addEventListener('vgb-xem-thu-chon', e => {
    const nd = e.detail && e.detail.noi_dung, chon = ((nd && nd.khoi) || []).find(k => k.id === e.detail.chon);
    if (chon && ['uu_dai', 'tuyen_dung'].includes(chon.loai) && man() !== '/' + chon.loai.replace('_', '-')) go(chon.loai);
    if (chon && chon.loai === 'tiec' && man() !== '/ve-su-kien') go('tiec');
    if (chon && chon.loai === 'thiet_ke_rieng' && man() !== '/thiet-ke-rieng/' + encodeURIComponent(chon.id)) nav('#/thiet-ke-rieng/' + encodeURIComponent(chon.id));
  });

  const vm = app.mount(goc);

  /* ---------------- nạp dữ liệu ---------------- */
  kho.phucHoiGio();
  /* v692: link cũ /banh#/<màn> (đã gửi khách, in trên QR bàn) đổi ngay sang đường sạch. */
  const cu = doiLinkCu(SACH, location.pathname, location.hash, location.search);
  if (cu) history.replaceState(history.state, '', cu);
  /* Thẻ <a href="#/..."> trong mẫu: đường sạch thì chặn lại, đi bằng nav để không gắn #. */
  if (SACH) document.addEventListener('click', e => {
    const a = e.target && e.target.closest ? e.target.closest('a[href^="#/"]') : null;
    if (!a || e.defaultPrevented || e.button || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    e.preventDefault(); nav(a.getAttribute('href')); window.scrollTo(0, 0);
  });
  apDuongDan();
  napNoiDung().then(() => {
    if (ND.diem_nhan) kho.capNhatDiemNhan(ND.diem_nhan);
    /* Link chia sẻ #/thiet-ke-rieng/<mã> mở trước khi nội dung về: chọn sẵn size sau khi có tác phẩm. */
    const m = man().match(/^\/thiet-ke-rieng\/(.+)$/); if (m) moTacPham(decodeURIComponent(m[1]));
  });
  kho.napTon().then(apDuongDanNeuBanh);
  /* v693 (sự cố 25/11/2026, site hết trần thời gian máy chủ): tab trình duyệt đang
     ẩn (máy khoá, chuyển app, tab nền) thì không hỏi máy chủ theo nhịp; mở lại thì
     đọc ngay một lượt. Màn hình quầy để mở cả ngày không còn gọi suông. */
  const khiHien = f => () => { if (!document.hidden) f(); };
  setInterval(khiHien(kho.napTon), 60000);
  kho.napMua().then(() => { if (/^\/in-season\//.test(man())) apDuongDan(); });
  setInterval(khiHien(kho.napMua), 300000);
  kho.napQuay();
  setInterval(khiHien(kho.napQuay), 60000);
  let anTu = 0;
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) { anTu = Date.now(); return; }
    if (anTu && Date.now() - anTu >= 60000) { kho.napTon(); kho.napQuay(); if (Date.now() - anTu >= 300000) kho.napMua(); }
    anTu = 0;
  });
  /* v638: link QR một bàn. Đúng thì mở thẳng tab Tại quầy ở chế độ gọi món;
     mất phần #/in-store (vài app quét QR cắt) thì tự thêm lại. */
  kho.goiBan.kiemLink().then(b => {
    if (b && b.ok && !/^\/in-store/.test(man())) nav('#/in-store', true);
  });
  kho.napCauHinh().then(ch => {
    const px = ch ? String(ch.pixel_id || '').replace(/\D/g, '') : '';
    if (px && !pixel.id && !ND.xemThu) { pixel.id = px; napPixel(px); }
  });
  function apDuongDanNeuBanh() {
    if (!/^\/banh\//.test(man())) return;
    if (!S.cur) { apDuongDan(); return; }
    if (S.tab === 'today' && !S.cur.sizes.some(s => S.TODAY[s.id] > 0)) S.tab = 'order';
  }
  window.addEventListener('pagehide', kho.luuGio);
  return {app, vm, kho};
}

function napPixel(id) {
  if (window.fbq) return;
  const n = window.fbq = function () { n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments); };
  if (!window._fbq) window._fbq = n;
  n.push = n; n.loaded = true; n.version = '2.0'; n.queue = [];
  const s = document.createElement('script'); s.async = true; s.src = 'https://connect.facebook.net/en_US/fbevents.js';
  document.head.appendChild(s);
  window.fbq('init', id); window.fbq('track', 'PageView');
}

/* Trang đặt bánh bản Vue. Giao diện giữ ĐÚNG Rocca đã duyệt: cùng CSS, cùng
   thẻ và lớp như banh.html (a20e85054). Khác bản cũ ở phần chạy bên trong:
   mọi chỗ hiện số đọc từ kho (kho-banh.js), đổi dữ liệu là màn tự đổi.

   Đường dẫn giữ như cũ để link đã gửi khách vẫn mở đúng:
     #/            bánh có sẵn hôm nay       #/dat-truoc   đặt bánh trước
     #/banh/<ten>  chi tiết một bánh         #/gio-hang    thông tin đơn
     #/in-season[/<ma>]  hàng mùa vụ         #/in-store    bánh trên tủ quầy
     #/uu-dai  #/tiec  #/tuyen-dung          ba chuyên mục */
import {createApp, computed, watch, nextTick} from '../lib/vue.esm-browser.prod.js';
import {ND, t, tMon, napNoiDung, telChu, telSo, mxh} from '../kho/chu.js';
import {doc, ghi} from '../kho/api.js';
import {taoKho} from './kho-banh.js';
import {DAYS, ACC, NUMS, ADDONS, PAYS, ANH_NEN} from './du-lieu.js';
import {LOGO} from './anh.js';
import {DongChu, BieuTuong, AnhMon} from './thanh-phan.js';
import {KhoiNoiDung, TieuDeMuc, CuaHang, KenhNoi, ChuyenMuc, dsMuc} from './noi-dung.js';
import {thuong} from './chu-giau.js';
import {MAU} from './mau.js';

function luuTruAnToan() {
  try { const s = window.sessionStorage; s.getItem('x'); return s; } catch (e) { return null; }
}
function ngauNhien(n) {
  try { const a = new Uint8Array(n); (window.crypto || self.crypto).getRandomValues(a); return Array.from(a); } catch (e) { return null; }
}

export function khoiDong(goc = '#app') {
  const pixel = {id: ''};
  const suKien = (ten, du) => { try { if (pixel.id && typeof window.fbq === 'function') window.fbq('track', ten, du); } catch (e) { /* im lặng */ } };
  const kho = taoKho({t, tMon, doc, ghi, luuTru: luuTruAnToan(), suKien, ngauNhien, xemThu: () => ND.xemThu, mxh, nd: ND,
    cookie: () => document.cookie, timKiem: () => location.search});
  const S = kho.S;

  const app = createApp({
    template: MAU,
    components: {DongChu, BieuTuong, AnhMon, KhoiNoiDung, TieuDeMuc, CuaHang, KenhNoi, ChuyenMuc},
    setup() {
      const tab = computed(() => S.tab);
      const gioMo = computed(() => S.trang === 'gio');
      const coTiec = computed(() => dsMuc('tiec').length > 0);
      const coQuay = computed(() => true);
      const quayHien = computed(() => {
        const quay = S.STORE.quay || [];
        if (!quay.length) return null;
        const chon = quay.find(q => q.ma === S.quayChon) || quay[0];
        const mon = (chon.mon || []).filter(m => !S.nhomQuay || m.nhom === S.nhomQuay);
        const ds = chon.mon || [];
        return {quay, chon, mon, tong: mon.reduce((a, m) => a + (m.con || 0), 0),
          nhom: ['', ...new Set(ds.map(m => m.nhom).filter(Boolean))].map(n => ({n, so: ds.filter(m => !n || m.nhom === n).length}))};
      });
      const chinhSach = computed(() => ((S.cauHinh && S.cauHinh.chinh_sach) || []).filter(c => /^\/[a-z-]+$/.test(String(c.duong || ''))).map(c => ({...c, duong: location.pathname.startsWith('/web_moi/') ? '/web_moi' + c.duong : c.duong})));
      const baoMat = computed(() => chinhSach.value.find(c => c.khoa === 'chinh_sach_bao_mat') || null);
      const lienHe = computed(() => (S.cauHinh && S.cauHinh.lien_he) || {});
      const ngayBan = computed(() => { void S.nhip; const b = new Date(); return DAYS[b.getDay()] + ', ' + kho.T.dmy(b); });
      const theHomNay = computed(() => kho.banhHomNay.value.map(c => kho.theBanh(c, 'today')));
      const theDatTruoc = computed(() => kho.banhDatTruoc.value.map(c => kho.theBanh(c, 'order')));
      const kichThuoc = computed(() => (S.cur ? kho.kichThuocDangBan(S.cur) : []));
      const chiTiet = computed(() => {
        const c = S.cur, sz = kho.curSize.value;
        if (!c || !sz) return null;
        const ma = sz.id, banh = t('dat_banh_3556aabb5', 'bánh');
        const avail = c.sizes.filter(s => S.TODAY[s.id] > 0);
        const nhanMua = tMon(c.sizes[0].id, 'theo_mua', c.seasonal);
        const tangChu = tMon(ma, 'tang', '');
        const tang = tangChu ? tangChu.split('\n').filter(x => x.trim()).map(x => [x, '']) : c.layers;
        const anhs = (c.anhs && c.anhs.length ? c.anhs : (c.img ? [c.img] : [])).slice(0, 5);
        return {c, ten: tMon(ma, 'ten', c.k), vi: kho.T.laChuViet(c.k), moTa: tMon(ma, 'mo_ta', c.desc), tang, anhs,
          tinhTrang: avail.length ? 'co' : (nhanMua ? 'mua' : 'truoc'), nhanMua,
          tonChu: avail.length ? kho.T.nhanTon(avail.reduce((a, s) => a + S.TODAY[s.id], 0), banh, t) : ''};
      });
      const anhChon = computed({get: () => S.anhChon || 0, set: v => { S.anhChon = v; }});
      const kichThuocDong = computed(() => kichThuoc.value.map(s => {
        const n = S.TODAY[s.id] || 0, tr = S.TRUOC[s.id] || 0, banh = t('dat_banh_3556aabb5', 'bánh');
        const kp = tMon(s.id, 'khau_phan', s.serve);
        return {s, gia: kho.T.tienVN(s.p), nhan: t('dat_banh_2540d6d0f', 'Ø {gia_tri_a}cm{gia_tri_b}', {gia_tri_a: s.cm, gia_tri_b: kp ? ' · ' + kp : ''}),
          em: n ? kho.T.nhanTon(n, banh, t) : (tr ? t('san_pham_dat_truoc', 'Đặt trước') + ' · ' + kho.T.nhanTon(tr, banh, t) : '')};
      }));
      const tomTatLich = computed(() => { const nh = kho.nhanNgayDangChon(); return nh.ten + ', ' + nh.ngay + ' · ' + kho.slotDangChon.value.t; });
      const hangTomTat = computed(() => {
        const ra = [];
        S.CART.forEach(o => {
          const x = o.qty > 1 ? ' ' + t('dat_banh_67fba2f35', '×') + ' ' + o.qty : '';
          ra.push({k: o.id + 'b' + ra.length, nhan: tMon(o.id, 'ten', o.k) + ' · Ø ' + o.cm + 'cm' + x, gia: kho.T.tienVN(o.price * o.qty)});
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
      return {S, ND, kho, t, tMon, telChu, telSo, LOGO, ANH_NEN, ACC, NUMS, ADDONS, PAYS, tab, gioMo, coTiec, coQuay, quayHien, chinhSach, baoMat,
        lienHe, ngayBan, theHomNay, theDatTruoc, chiTiet, anhChon, kichThuocDong, tomTatLich, hangTomTat, monMua, muaXem, tienTom, thuong,
        go, nav, navBack, moBanh: c => nav('#/banh/' + kho.T.slug(c.k)), themNhanh, themVaoGio, suaDongGio, moGio, guiDon,
        moMua: m => nav('#/in-season/' + m.ma), themTuMua, tgl, gioMo2: () => nav('#/gio-hang'), mxh};
    }
  });

  /* ---------------- điều hướng ---------------- */
  function nav(h, thay) {
    const url = location.pathname + location.search + (h === '#/' ? '' : h);
    if (thay) history.replaceState({vgb: 1}, '', url); else history.pushState({vgb: 1}, '', url);
    apDuongDan();
  }
  function navBack() {
    if (history.state && history.state.vgb) history.back();
    else nav(S.tab === 'order' ? '#/dat-truoc' : '#/', true);
  }
  function go(tab) {
    if (tab === 'uu_dai' || tab === 'tuyen_dung' || tab === 'tiec') { nav('#/' + tab.replace('_', '-')); window.scrollTo(0, 0); return; }
    nav(tab === 'season' ? '#/in-season' : tab === 'store' ? '#/in-store' : tab === 'order' ? '#/dat-truoc' : '#/');
    window.scrollTo({top: 0, behavior: 'smooth'});
  }
  S.trang = 'danh_muc';
  function apDuongDan() {
    kho.nhip();
    const h = (location.hash || '#/').replace(/^#/, '');
    const mBanh = h.match(/^\/banh\/(.+)$/), mMua = h.match(/^\/in-season\/(.+)$/);
    const truocDo = S.trang;
    if (h === '/uu-dai' || h === '/tuyen-dung' || h === '/tiec') { dongHet(); S.tab = h.slice(1).replace('-', '_'); return; }
    if (mBanh) {
      const c = S.CAKES.find(x => kho.T.slug(x.k) === mBanh[1]);
      /* Codex #462: bánh bếp thêm tay chỉ có sau lần nạp tồn đầu. Chưa nạp
         xong thì GIỮ đường dẫn, napTon().then(apDuongDanNeuBanh) mở lại sau. */
      if (!c) { if (S.tonDaThu) nav('#/', true); return; }
      /* Link chia sẻ mở mới: bánh không còn hôm nay vẫn cho chọn cỡ đặt trước. */
      if (S.tab === 'today' && !c.sizes.some(s => S.TODAY[s.id] > 0)) S.tab = 'order';
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
    if (S.trang === 'gio') kho.roiGio();
    S.cur = null; S.dongDangSua = -1; S.muaDangXem = null; S.trang = 'danh_muc';
  }
  window.addEventListener('popstate', apDuongDan);

  function themNhanh(c, cheDo) { if (kho.themNhanh(c, cheDo) === 'mo') nav('#/banh/' + kho.T.slug(c.k)); else nhichThanh(); }
  function themVaoGio() {
    const kq = kho.addToCart();
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

  const CHO = {lich: '#c-days', ten: '#f-name', sdt: '#f-phone', diem_nhan: '#pickList', dia_chi: '#f-addr', cach_nhan: '#m-pick', dong_y: '#c-dongy', uu_dai: '#sum'};
  async function guiDon() {
    const kq = await kho.submitOrder();
    if (kq.buoc === 'xong' && kq.duong_dan) { location.assign(location.pathname.startsWith('/web_moi/') ? '/web_moi' + kq.duong_dan : kq.duong_dan); return; }
    const sel = CHO[kq.buoc]; if (!sel) return;
    await nextTick();
    const o = document.querySelector(sel); if (!o) return;
    if (o.scrollIntoView) o.scrollIntoView({behavior: 'smooth', block: 'center'});
    const f = kq.buoc === 'lich' ? (o.querySelector('.day.on') || o.querySelector('.day')) : o;
    if (f && f.focus) f.focus();
  }

  /* Bàn phím trong bảng đang mở (thao-tac.js #460): mở bảng thì đưa con trỏ
     vào nút đầu tiên, Tab quay vòng trong bảng, đóng bảng thì trả con trỏ về
     chỗ cũ. */
  const CHON = 'button:not([disabled]),a[href],input:not([disabled]),select:not([disabled]),textarea:not([disabled]),summary,[tabindex="0"]';
  const nutTrong = el => Array.from(el.querySelectorAll(CHON)).filter(n => n.getClientRects().length);
  const bangMo = () => document.querySelector('#sheet.open,#sheetMua.open,#checkout.open');
  let bangCu = null, conTroTruoc = null;
  watch(() => S.trang, () => nextTick(() => {
    const moi = bangMo();
    if (moi === bangCu) return;
    if (moi) { if (!bangCu) conTroTruoc = document.activeElement; bangCu = moi; const n = nutTrong(moi)[0]; if (n) n.focus({preventScroll: true}); }
    else { bangCu = null; if (conTroTruoc && conTroTruoc.isConnected && conTroTruoc.getClientRects().length) conTroTruoc.focus({preventScroll: true}); conTroTruoc = null; }
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
  /* Thanh tab cuộn ngang: tab đang mở phải lọt vào tầm mắt. */
  watch(() => S.tab, tb => nextTick(() => { const n = document.querySelector('.tab[data-tab="' + tb + '"]'); if (n && n.scrollIntoView) try { n.scrollIntoView({block: 'nearest', inline: 'center'}); } catch (e) { /* bỏ qua */ } }), {immediate: true});
  /* Điểm nhận bánh đến từ thẻ Cửa hàng của nội dung web (Codex #453). */
  watch(() => ND.diem_nhan, ds => kho.capNhatDiemNhan(ds));
  /* Trình biên tập chọn khối ưu đãi/tuyển dụng thì mở đúng chuyên mục. */
  window.addEventListener('vgb-xem-thu-chon', e => {
    const nd = e.detail && e.detail.noi_dung, chon = ((nd && nd.khoi) || []).find(k => k.id === e.detail.chon);
    if (chon && ['uu_dai', 'tuyen_dung', 'tiec'].includes(chon.loai) && location.hash !== '#/' + chon.loai.replace('_', '-')) go(chon.loai);
  });

  const vm = app.mount(goc);

  /* ---------------- nạp dữ liệu ---------------- */
  kho.phucHoiGio();
  apDuongDan();
  napNoiDung().then(() => { if (ND.diem_nhan) kho.capNhatDiemNhan(ND.diem_nhan); });
  kho.napTon().then(apDuongDanNeuBanh);
  setInterval(kho.napTon, 60000);
  kho.napMua().then(() => { if (/^#\/in-season\//.test(location.hash || '')) apDuongDan(); });
  setInterval(kho.napMua, 300000);
  kho.napQuay();
  setInterval(kho.napQuay, 60000);
  kho.napCauHinh().then(ch => {
    const px = ch ? String(ch.pixel_id || '').replace(/\D/g, '') : '';
    if (px && !pixel.id && !ND.xemThu) { pixel.id = px; napPixel(px); }
  });
  function apDuongDanNeuBanh() { if (/^#\/banh\//.test(location.hash || '') && !S.cur) apDuongDan(); }
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

/* Phần NỘI DUNG marketing của trang: khối giới thiệu, tiêu đề mục, ghé cửa
   hàng, nút kênh đặt hàng nổi, và ba chuyên mục Ưu đãi / Tiệc / Tuyển dụng.
   Chép luật từ khoi.js, cua-hang.js, kenh-noi.js, chuyen-muc.js của trang cũ;
   chữ người soạn luôn là chữ (Vue tự thoát), ảnh và link qua chuẩn hoá. */
import {h, reactive} from '../lib/vue.esm-browser.prod.js';
import {ND, t, chonKhoi, telChu, telSo} from '../kho/chu.js';
import {ghi} from '../kho/api.js';

const LOAI_RIENG = ['tieu_de_muc', 'kenh_dat_hang', 'zalo_oa', 'nut_kenh', 'uu_dai', 'tuyen_dung', 'tiec'];
const lopChon = k => (ND.xemThu && ND.khoiChon === k.id ? ' vgb-dang-chon' : '');
const bamKhoi = k => (ND.xemThu ? e => { e.preventDefault(); chonKhoi(k.id); } : undefined);

/* ---------- khối nội dung theo vị trí (khoi.js) ---------- */
export const KhoiNoiDung = {
  name: 'KhoiNoiDung',
  props: {viTri: String},
  render() {
    const ds = (ND.khoi || []).filter(k => k.hien && !LOAI_RIENG.includes(k.loai) && (k.vi_tri || 'cuoi_trang') === this.viTri);
    return ds.map(k => {
      if (k.loai === 'hoi_dap') {
        return h('details', {class: 'web-khoi web-hoi-dap' + lopChon(k), 'data-khoi': k.id, onClick: bamKhoi(k)},
          [h('summary', null, k.tieu_de), h('p', {class: 'web-doan'}, k.noi_dung)]);
      }
      const con = [];
      if (k.anh) con.push(h('img', {class: 'web-anh', src: k.anh, alt: k.mo_ta_anh || '', loading: k.loai === 'anh_bia' ? 'eager' : 'lazy'}));
      const chu = [h('p', {class: 'web-nhan'}, k.nhan), h('h2', {class: 'web-tieu-de'}, k.tieu_de), h('p', {class: 'web-doan'}, k.noi_dung)];
      if (k.nut && k.lien_ket) chu.push(h('a', {class: 'web-nut', href: k.lien_ket}, k.nut));
      con.push(h('div', {class: 'web-chu'}, chu));
      return h('section', {class: 'web-khoi web-' + k.loai + lopChon(k), 'data-khoi': k.id, onClick: bamKhoi(k)}, con);
    });
  }
};

/* ---------- tiêu đề mục có thể thay (data-vgb-tieu-de cũ) ---------- */
export const TieuDeMuc = {
  name: 'TieuDeMuc',
  props: {viTri: String, dong: Array},
  render() {
    const k = (ND.khoi || []).find(x => x.loai === 'tieu_de_muc' && x.vi_tri === this.viTri);
    if (k && k.hien) return h('span', {'data-vgb-tieu-de': this.viTri, 'data-khoi': k.id, class: lopChon(k).trim() || undefined, onClick: bamKhoi(k)}, k.tieu_de);
    const ra = [];
    (this.dong || []).forEach((d, i) => { if (i) ra.push(h('br')); ra.push(d); });
    return h('span', {'data-vgb-tieu-de': this.viTri, 'data-khoi': k ? k.id : undefined}, ra);
  }
};

/* ---------- ghé cửa hàng (cua-hang.js veCuaHang) ---------- */
export const CuaHang = {
  name: 'CuaHang',
  render() {
    const ds = Array.isArray((ND.thong_tin || {}).cua_hang) ? ND.thong_tin.cua_hang : [];
    const hien = ds.filter(c => c.hien && c.dia_chi);
    if (!hien.length) return null;
    const lh = ND.lien_he || {};
    return h('section', {class: 'wrap cw-khung', id: 'cuaHangWeb', 'aria-labelledby': 'cwTieuDe'}, [
      h('h2', {class: 'cw-tieu-de', id: 'cwTieuDe'}, t('cua_hang_tieu_de', 'Ghé cửa hàng')),
      h('div', {class: 'cw-ds', id: 'cuaHangDs'}, hien.map(c => {
        const dt = c.hotline || lh.dien_thoai || '', so = String(dt).replace(/[^0-9+]/g, '');
        const nut = [];
        if (so) nut.push(h('a', {href: 'tel:' + so}, t('cua_hang_goi', 'Gọi') + ' ' + dt));
        if (/^https:\/\/[^\s/@\\]+(\/|$)/.test(c.chi_duong || '') && !/\s/.test(c.chi_duong)) nut.push(h('a', {href: c.chi_duong, target: '_blank', rel: 'noopener'}, t('cua_hang_chi_duong', 'Chỉ đường') + ' ↗'));
        return h('article', {class: 'cw-the'}, [h('h3', null, c.ten), h('p', {class: 'cw-dia-chi'}, c.dia_chi),
          c.gio_mo_cua ? h('p', {class: 'cw-gio'}, c.gio_mo_cua) : null, h('div', {class: 'cw-nut'}, nut)]);
      }))
    ]);
  }
};

/* ---------- nút kênh đặt hàng nổi (kenh-noi.js) ---------- */
function linkAnToan(v, zalo) {
  try {
    const u = new URL(v);
    return u.protocol === 'https:' && !u.username && !u.password && (!zalo || (u.hostname === 'zalo.me' && /^\/(?:[0-9]{15,25}|[A-Za-z][A-Za-z0-9._-]{2,59})\/?$/.test(u.pathname))) ? u.href : '';
  } catch (_) { return ''; }
}
function anhAnToan(v) {
  if (!v || /[\s\\]/.test(v) || v.startsWith('/private/') || /\.svg(?:[?#]|$)/i.test(v)) return '';
  return (v.startsWith('/') && !v.startsWith('//')) || linkAnToan(v) ? v : '';
}
const LogoKenh = {
  props: {k: Object, lop: String, duPhong: String},
  data() { return {hong: false}; },
  render() {
    const src = anhAnToan(this.k.anh);
    const chu = this.duPhong || this.k.nut || (this.k.tieu_de || '').slice(0, 2) || '↗';
    return h('span', {class: this.lop, 'aria-hidden': 'true'}, [
      src && !this.hong ? h('img', {alt: '', src, decoding: 'async', onError: () => { this.hong = true; }}) : null,
      h('span', {class: 'kenh-logo-du-phong', hidden: !!(src && !this.hong)}, chu)
    ]);
  }
};
export const KenhNoi = {
  name: 'KenhNoi',
  data() { return {mo: false, day: 0}; },
  mounted() {
    /* Nút nổi đứng trên thanh giỏ: đo chiều cao thật của thanh (leDay cũ). */
    const bar = document.getElementById('bar');
    this._le = () => { this.day = bar && bar.classList.contains('on') ? bar.getBoundingClientRect().height : 0; };
    if (bar) { this._mo = new MutationObserver(this._le); this._mo.observe(bar, {attributes: true, attributeFilter: ['class']}); if (window.ResizeObserver) { this._ro = new ResizeObserver(this._le); this._ro.observe(bar); } }
    window.addEventListener('resize', this._le); this._le();
    this._phim = e => { if (e.key === 'Escape' && this.mo) { e.preventDefault(); e.stopImmediatePropagation(); this.dong(true); } };
    this._bam = e => { if (this.$el && this.$el.contains && !this.$el.contains(e.target)) this.dong(false); };
    this._hash = () => this.dong(false);
    document.addEventListener('keydown', this._phim, true);
    document.addEventListener('click', this._bam);
    window.addEventListener('hashchange', this._hash);
  },
  unmounted() {
    if (this._mo) this._mo.disconnect(); if (this._ro) this._ro.disconnect(); window.removeEventListener('resize', this._le);
    document.removeEventListener('keydown', this._phim, true);
    document.removeEventListener('click', this._bam);
    window.removeEventListener('hashchange', this._hash);
  },
  methods: {
    dong(layLai) { const da = this.mo; this.mo = false; if (da && layLai && this.$refs.nut) this.$refs.nut.focus(); },
    bat() { this.mo = !this.mo; if (this.mo) this.$nextTick(() => this.$refs.tat && this.$refs.tat.focus()); }
  },
  render() {
    const kenh = (ND.khoi || []).filter(k => k.loai === 'kenh_dat_hang' && k.hien && linkAnToan(k.lien_ket));
    const zalo = (ND.khoi || []).find(k => k.loai === 'zalo_oa' && k.hien && linkAnToan(k.lien_ket, true));
    const cauHinh = (ND.khoi || []).find(k => k.loai === 'nut_kenh') || {hien: true, anh: '/assets/vagabond/web_order/logo-kenh/grab.png'};
    const coApp = kenh.length && cauHinh.hien;
    const con = [];
    if (coApp) {
      const ten = cauHinh.tieu_de || t('kenh_noi_nut', 'Đặt qua app');
      con.push(h('div', {class: 'kenh-bang', id: 'kenh-dat-hang', hidden: !this.mo}, [
        h('div', {class: 'kenh-dau'}, [h('strong', null, t('kenh_noi_tieu_de', 'Đặt qua ứng dụng')),
          h('button', {class: 'kenh-dong', type: 'button', ref: 'tat', 'aria-label': t('kenh_noi_dong', 'Đóng kênh đặt hàng'), onClick: () => this.dong(true)}, '×')]),
        h('p', {class: 'kenh-mo-ta'}, t('kenh_noi_mo_ta', 'Quý khách chọn ứng dụng để xem thực đơn và đặt món.')),
        h('div', {class: 'kenh-danh-sach'}, kenh.map(k => h('a', {class: 'kenh-lien-ket', href: linkAnToan(k.lien_ket), target: '_blank', rel: 'noopener noreferrer', 'data-khoi': k.id},
          [h(LogoKenh, {k, lop: 'kenh-logo'}), h('span', null, k.tieu_de), h('span', {class: 'kenh-mui-ten'}, '↗')]))),
        h('p', {class: 'kenh-chu-thich'}, t('kenh_noi_tab_moi', 'Liên kết mở trong tab mới.'))
      ]));
      con.push(h('button', {class: 'kenh-bong kenh-app', type: 'button', ref: 'nut', 'aria-expanded': String(this.mo), 'aria-controls': 'kenh-dat-hang',
        'aria-label': ten, title: ten, onClick: this.bat}, [h(LogoKenh, {k: cauHinh, lop: 'kenh-logo-nut', duPhong: '↗'})]));
    }
    if (zalo) con.push(h('a', {class: 'kenh-bong kenh-zalo', href: linkAnToan(zalo.lien_ket, true), target: '_blank', rel: 'noopener noreferrer', 'data-khoi': zalo.id},
      [h(LogoKenh, {k: zalo, lop: 'kenh-logo-zalo', duPhong: zalo.nut || 'Zalo'}), h('span', null, zalo.tieu_de)]));
    return h('aside', {class: 'kenh-noi', hidden: !coApp && !zalo, 'aria-label': t('kenh_noi_nhan', 'Kênh đặt hàng và hỗ trợ'),
      style: 'bottom:calc(' + (this.day + 16) + 'px + env(safe-area-inset-bottom))'}, con);
  }
};

/* ---------- chuyên mục Ưu đãi / Tiệc / Tuyển dụng (chuyen-muc.js) ---------- */
export function ngayVN() { return new Intl.DateTimeFormat('en-CA', {timeZone: 'Asia/Ho_Chi_Minh', year: 'numeric', month: '2-digit', day: '2-digit'}).format(new Date()); }
const anToan = u => typeof u === 'string' && !/[\s\\]/.test(u) && ((u[0] === '/' && u[1] !== '/') || u[0] === '#' || /^https:\/\/[^/@]+(?:\/|$)/.test(u));
const RE_EMAIL = /^[A-Za-z0-9_.+%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
const ngay = s => String(s || '').split('-').reverse().join('/');
const gio = s => String(s || '').replace(/^0(\d)/, '$1').replace(':', 'g');
const tien = s => String(parseInt(s, 10) || 0).replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ' đ';
const dong = s => String(s || '').split('\n').map(x => x.trim()).filter(Boolean);
export function khachThay(k, homNay) {
  if (!k.hien) return false;
  if (k.loai === 'tiec') return !k.bat_dau || k.bat_dau >= homNay;
  return !k.ket_thuc || k.ket_thuc >= homNay;
}
export function dieuKien(k) {
  const ra = [];
  if (k.don_toi_thieu && +k.don_toi_thieu > 0) ra.push(t('cm_don_tu', 'Đơn từ') + ' ' + tien(k.don_toi_thieu));
  if (k.gio_bat_dau && k.gio_ket_thuc) ra.push(t('cm_khung_gio', 'Khung giờ') + ' ' + gio(k.gio_bat_dau) + ' - ' + gio(k.gio_ket_thuc));
  return ra.join(' · ');
}
function veVe(k) {
  const da = +((ND.ve || {})[k.id] || 0);
  if (!k.so_ve) return {con: null, chu: ''};
  const con = Math.max(0, +k.so_ve - da);
  return {con, chu: con ? t('cm_con_ve', 'Còn {so} vé', {so: con}) : t('cm_het_ve', 'Đã hết vé')};
}
const GAP_TU = 420, MON_HIEN = 8;
const DoanGap = {
  props: {chu: String, lop: String},
  data() { return {mo: false}; },
  render() {
    const dai = String(this.chu || '').length > GAP_TU;
    return h('div', {class: 'cm-gap-khung'}, [
      h('p', {class: 'cm-doan' + (this.lop ? ' ' + this.lop : '') + (dai && !this.mo ? ' cm-gap' : '')}, this.chu),
      dai ? h('button', {class: 'cm-doc-tiep', type: 'button', 'aria-expanded': String(this.mo), onClick: () => { this.mo = !this.mo; }},
        this.mo ? t('cm_thu_gon', 'Thu gọn') : t('cm_doc_tiep', 'Đọc tiếp')) : null
    ]);
  }
};
const NhanMon = {
  props: {ds: Array},
  data() { return {het: false}; },
  render() {
    const hien = this.het ? this.ds : this.ds.slice(0, MON_HIEN), con = this.ds.length - hien.length;
    return h('div', {class: 'cm-mon'}, [...hien.map(x => h('span', {class: 'cm-mon-nhan'}, x)),
      con > 0 ? h('button', {class: 'cm-mon-nhan cm-mon-them', type: 'button', onClick: () => { this.het = true; }}, t('cm_mon_nua', '+ {so} món nữa', {so: con})) : null]);
  }
};
const DangKyTiec = {
  props: {k: Object, conVe: Number},
  data() { return {ten: '', sdt: '', so: 1, ghi: '', bao: '', dangGui: false, xong: '', ma: ''}; },
  methods: {
    async gui(e) {
      e.preventDefault();
      if (ND.xemThu) { this.bao = 'Đây là bản xem trước, không gửi đăng ký.'; return; }
      this.ma = this.ma || (window.crypto && crypto.randomUUID ? crypto.randomUUID() : 'xxxxxxxx-xxxx-4xxx-8xxx-xxxxxxxxxxxx'.replace(/x/g, () => (Math.random() * 16 | 0).toString(16)));
      this.dangGui = true; this.bao = t('cm_dk_dang_gui', 'Đang gửi...');
      try {
        const m = await ghi('vagabond.tiec_web.dang_ky', {du_lieu: {tiec_id: this.k.id, ten: this.ten, sdt: this.sdt, so_ve: this.so, ghi_chu: this.ghi}, ma_lan_gui: this.ma});
        if (!m || !m.ma) throw new Error(t('cm_dk_loi', 'Chưa gửi được. Kiểm tra mạng rồi bấm Gửi lại.'));
        this.xong = t('cm_dk_xong', 'Đã nhận đăng ký, mã {ma}. Chúng tôi sẽ gọi xác nhận và hướng dẫn thanh toán.', {ma: m.ma});
      } catch (er) { this.bao = er.message || t('cm_dk_loi', 'Chưa gửi được. Kiểm tra mạng rồi bấm Gửi lại.'); this.dangGui = false; }
    }
  },
  render() {
    if (this.xong) return h('form', {class: 'cm-dk'}, [h('p', {class: 'cm-dk-xong'}, this.xong)]);
    const toi = Math.min(10, this.conVe == null ? 10 : this.conVe);
    const o = (nhan, ten, kieu, them) => h('label', null, [nhan, h(kieu === 'area' ? 'textarea' : 'input', {type: kieu === 'area' ? undefined : kieu, name: ten,
      value: this[ten === 'so_ve' ? 'so' : ten === 'ghi_chu' ? 'ghi' : ten], onInput: e => { this[ten === 'so_ve' ? 'so' : ten === 'ghi_chu' ? 'ghi' : ten] = e.target.value; }, ...them})]);
    return h('form', {class: 'cm-dk', onSubmit: this.gui}, [
      o(t('cm_dk_ten', 'Họ tên'), 'ten', 'text', {required: true, autocomplete: 'name', maxlength: 120}),
      o(t('cm_dk_sdt', 'Số điện thoại'), 'sdt', 'tel', {required: true, autocomplete: 'tel', inputmode: 'numeric'}),
      o(t('cm_dk_so_ve', 'Số vé') + ' (1 - ' + toi + ')', 'so_ve', 'number', {required: true, min: 1, max: toi}),
      o(t('cm_dk_ghi_chu', 'Ghi chú (không bắt buộc)'), 'ghi_chu', 'area', {maxlength: 500}),
      h('p', {class: 'cm-dk-luu-y'}, t('cm_dk_luu_y', 'Gửi đăng ký chưa phải đã có vé. Chúng tôi sẽ gọi xác nhận và hướng dẫn thanh toán.')),
      h('button', {class: 'cm-nut', type: 'submit', disabled: this.dangGui}, t('cm_dk_gui', 'Gửi đăng ký')),
      h('p', {class: 'cm-dk-bao', role: 'status'}, this.bao)
    ]);
  }
};
const TheTiec = {
  props: {k: Object, homNay: String},
  data() { return {moDk: false}; },
  render() {
    const k = this.k, v = veVe(k), han = k.han_ban || k.bat_dau, hetHan = !!(han && han < this.homNay);
    const nhan = [k.nhan || k.nhom, hetHan ? t('cm_het_han_dk', 'Đã hết hạn đăng ký') : (k.bat_dau && k.bat_dau > this.homNay ? t('sap_dien_ra', 'Sắp diễn ra') : ''), hetHan ? '' : v.chu].filter(Boolean).join(' · ');
    const thoi = [k.bat_dau ? ngay(k.bat_dau) : '', k.gio_bat_dau && k.gio_ket_thuc ? gio(k.gio_bat_dau) + ' - ' + gio(k.gio_ket_thuc) : ''].filter(Boolean).join(' · ');
    const hop = [h('p', {class: 'cm-nhan'}, nhan), h('h2', null, k.tieu_de)];
    if (thoi) hop.push(h('p', {class: 'cm-ngay'}, thoi));
    if (k.dia_diem) hop.push(h('p', {class: 'cm-thong-tin'}, k.dia_diem));
    hop.push(h('p', {class: 'cm-gia'}, +k.gia_ve > 0 ? tien(k.gia_ve) + ' / ' + t('cm_ve', 'vé') : t('cm_mien_phi', 'Miễn phí')));
    if (v.con != null) hop.push(h('p', {class: 'cm-vach'}, [h('span', {class: 'cm-vach-thanh'}, [h('i', {style: 'width:' + Math.round(100 * (+k.so_ve - v.con) / +k.so_ve) + '%'})]), h('span', null, v.chu)]));
    if (k.han_ban && !hetHan) hop.push(h('p', {class: 'cm-ngay cm-han'}, t('cm_han_dk', 'Đăng ký trước') + ' ' + ngay(k.han_ban)));
    if (!hetHan && v.con !== 0 && !this.moDk) hop.push(h('button', {class: 'cm-nut', type: 'button', onClick: () => { this.moDk = true; }}, t('cm_dang_ky', 'Đăng ký tham gia')));
    const ds = dong(k.yeu_cau);
    const than = [
      h('div', {class: 'cm-cau-chuyen'}, k.noi_dung ? [h('p', {class: 'cm-nhan'}, t('cm_cau_chuyen', 'Câu chuyện')), h(DoanGap, {chu: k.noi_dung})] : []),
      h('div', {class: 'cm-thuc-don'}, ds.length ? [h('p', {class: 'cm-nhan'}, [h('span', null, t('cm_bao_gom', 'Bao gồm')), h('span', {class: 'cm-dem'}, ds.length + ' ' + t('cm_mon', 'món'))]), h(NhanMon, {ds})] : [])
    ];
    if (this.moDk) than.push(h(DangKyTiec, {k, conVe: v.con}));
    return h('article', {class: 'cm-the cm-tiec' + lopChon(k), 'data-khoi': k.id, onClick: bamKhoi(k)}, [
      h('div', {class: 'cm-hero'}, [
        k.anh && anToan(k.anh) ? h('img', {class: 'cm-anh', src: k.anh, alt: k.mo_ta_anh || '', loading: 'lazy'})
          : h('div', {class: 'cm-anh cm-anh-nen', 'aria-hidden': 'true'}, [h('span', null, k.tieu_de)]),
        h('div', {class: 'cm-hop'}, hop)]),
      h('div', {class: 'cm-than'}, than)
    ]);
  }
};
export const TheMuc = {
  name: 'TheMuc',
  props: {k: Object, homNay: String},
  render() {
    const k = this.k, loai = k.loai, homNay = this.homNay;
    if (loai === 'tiec') return h(TheTiec, {k, homNay});
    const nd = [h('p', {class: 'cm-nhan'}, [k.nhan || k.nhom, k.bat_dau > homNay ? t('sap_dien_ra', 'Sắp diễn ra') : ''].filter(Boolean).join(' · ')), h('h2', null, k.tieu_de)];
    if (k.bat_dau || k.ket_thuc) nd.push(h('p', {class: 'cm-ngay'}, [...new Set([k.bat_dau, k.ket_thuc].filter(Boolean))].map(ngay).join(' - ')));
    nd.push(h(DoanGap, {chu: k.noi_dung}));
    if (loai === 'uu_dai') {
      if (k.ma_uu_dai) nd.push(h('p', {class: 'cm-ma'}, [h('span', null, t('ma_uu_dai', 'Mã ưu đãi')), h('b', null, k.ma_uu_dai)]));
      const dk = dieuKien(k); if (dk) nd.push(h('p', {class: 'cm-dieu-kien'}, dk));
    }
    const ds = dong(loai === 'uu_dai' ? k.dieu_kien : k.yeu_cau);
    if (ds.length) {
      if (loai !== 'uu_dai') nd.push(h('p', {class: 'cm-nhan'}, t('cm_yeu_cau', 'Yêu cầu và quyền lợi')));
      nd.push(h('ul', {class: 'cm-ds'}, ds.map(x => h('li', null, x))));
    }
    if (loai === 'tuyen_dung' && !k.ket_thuc) nd.push(h('p', {class: 'cm-ngay'}, t('chua_han', 'Đến khi đủ người')));
    if (loai === 'tuyen_dung') nd.push(h('p', {class: 'cm-thong-tin'}, [k.noi_lam, k.hinh_thuc].filter(Boolean).join(' · ')));
    let duong = anToan(k.lien_ket) ? k.lien_ket : '';
    const email = k.email || (((ND.thong_tin || {}).lien_he || {}).email) || '';
    if (loai === 'tuyen_dung' && !duong && RE_EMAIL.test(email)) duong = 'mailto:' + email + '?subject=' + encodeURIComponent('Ứng tuyển - ' + k.tieu_de);
    if (duong) nd.push(h('a', {class: 'cm-nut', href: duong}, k.nut || (loai === 'tuyen_dung' ? t('ung_tuyen', 'Ứng tuyển vị trí này') : t('xem_chi_tiet_muc', 'Xem chi tiết'))));
    return h('article', {class: 'cm-the cm-' + loai + lopChon(k), 'data-khoi': k.id, onClick: bamKhoi(k)}, [
      k.anh && anToan(k.anh) ? h('img', {class: 'cm-anh', src: k.anh, alt: k.mo_ta_anh || '', loading: 'lazy'})
        : (loai !== 'tuyen_dung' ? h('div', {class: 'cm-anh cm-anh-nen', 'aria-hidden': 'true'}, [h('span', null, k.tieu_de)]) : null),
      h('div', {class: 'cm-noi-dung'}, nd)
    ]);
  }
};
const LOC = reactive({uu_dai: {tim: '', nhom: ''}, tuyen_dung: {tim: '', nhom: ''}, tiec: {tim: '', nhom: ''}});
export function dsMuc(loai, homNay = ngayVN()) {
  return (ND.khoi || []).filter(k => k.loai === loai && (ND.xemThu || khachThay(k, homNay)));
}
const RONG = {uu_dai: 'Chưa có ưu đãi trong nhóm này. Quý khách có thể xem các nhóm khác.', tiec: 'Chưa có tiệc nào đang mở. Quý khách vui lòng quay lại sau.', tuyen_dung: 'Chưa có vị trí phù hợp trong nhóm này. Quý khách vui lòng quay lại sau.'};
export const ChuyenMuc = {
  name: 'ChuyenMuc',
  props: {loai: String},
  render() {
    const loai = this.loai, homNay = ngayVN(), tt = LOC[loai], ds = dsMuc(loai, homNay);
    const nhom = [...new Set(ds.map(k => k.nhom).filter(Boolean))];
    const loc = ds.filter(k => (!tt.nhom || k.nhom === tt.nhom) && [k.tieu_de, k.nhom, k.noi_lam, k.dia_diem, k.noi_dung].join(' ').toLocaleLowerCase('vi').includes(tt.tim.toLocaleLowerCase('vi')));
    const goiY = t('tim_muc', 'Tìm theo tên, nhóm hoặc nơi làm');
    return h('div', {id: 'noi-' + loai}, [
      h('div', {class: 'cm-loc'}, ds.length > 3 ? [h('input', {type: 'search', placeholder: goiY, 'aria-label': goiY, value: tt.tim, onInput: e => { tt.tim = e.target.value; }})] : []),
      h('div', {class: 'cm-chips'}, nhom.length ? ['', ...nhom].map(n => h('button', {'aria-pressed': String(n === tt.nhom), onClick: () => { tt.nhom = n; }}, n || t('tat_ca_muc', 'Tất cả'))) : []),
      h('div', {class: 'cm-danh-sach'}, loc.length ? loc.map(k => h(TheMuc, {k, homNay, key: k.id})) : [h('p', {class: 'cm-rong'}, t(loai + '_rong', RONG[loai]))])
    ]);
  }
};

export {telChu, telSo};

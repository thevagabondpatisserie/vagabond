/* Chân trang trang đặt bánh bản Vue (v630, anh Việt duyệt mẫu 4 ngày 02/11/2026).

   Chân trang cũ chỉ là một khối chữ xám: khách không thấy nút quay lại chọn
   bánh, không thấy giờ mở cửa, mạng xã hội nằm rải ở chỗ khác. Bản mới chia
   ba tầng: dải mời chọn bánh và đặt bàn; bốn cột (thương hiệu và mạng xã hội,
   cửa hàng, liên hệ, mua bánh); dòng cam kết và dòng pháp lý. Điện thoại gấp
   các cột thành mục bấm mở, mục Cửa hàng mở sẵn.

   Mọi chữ và link lấy từ MỘT nguồn đang có: thẻ Liên hệ (ô web_* của Settings,
   don_web.lien_he), thẻ Cửa hàng trong trình biên tập (cuaHangHien dùng chung
   với khối Ghé cửa hàng), danh sách chính sách đang hiện, ngưỡng miễn phí giao
   của kho. Ô người điền tay là đầu vào không tin được: link mạng xã hội chỉ
   nhận https, email phải đúng dạng mới thành mailto. Không có mạng nào thì
   không vẽ ô trống. Thông tin pháp lý của chân trang cũ (tên công ty, mã số
   thuế, hai địa chỉ, điện thoại, email) giữ đủ. */
import {h} from '../lib/vue.esm-browser.prod.js';
import {ND, t, telChu, telSo} from '../kho/chu.js';
import {linkHopLe} from '../kho/thuan.js';
import {LOGO} from './anh.js';
import {cuaHangHien, chiDuongAnToan, dsMuc, ngayVN} from './noi-dung.js';

/* ---------- phần thuần ---------- */

/* Chính sách đang hiện: chỉ đường dẫn nội bộ dạng /chinh-sach-x; trang chạy ở
   /web_moi thì giữ khách trong bản đang xem. app.js dùng lại cho link đọc
   chính sách dưới ô đồng ý. */
export function locChinhSach(ds, duong) {
  const moi = String(duong || '').startsWith('/web_moi/');
  return (Array.isArray(ds) ? ds : []).filter(c => c && /^\/[a-z-]+$/.test(String(c.duong || '')))
    .map(c => ({...c, duong: moi ? '/web_moi' + c.duong : c.duong}));
}

const MXH = [['instagram', 'Instagram'], ['facebook', 'Facebook'], ['zalo', 'Zalo'], ['tiktok', 'TikTok']];
/* Mạng xã hội có link https hợp lệ trong thẻ Liên hệ, đúng thứ tự mẫu duyệt. */
export function mangXaHoi(lh) {
  const o = lh || {};
  return MXH.map(([k, ten]) => ({k, ten, url: linkHopLe(o[k])})).filter(x => x.url);
}

const RE_EMAIL = /^[A-Za-z0-9_.+%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
/* Điện thoại, email, Zalo cho cột Liên hệ. Chưa điền số thì dùng số gốc như
   chân trang cũ (telChu/telSo). */
export function lienHeChanTrang(lh) {
  const o = lh || {};
  const dt = String(o.dien_thoai || '').trim();
  const so = String(o.dien_thoai_so || dt).replace(/[^0-9+]/g, '');
  const email = String(o.email || '').trim();
  return {dt: dt && so ? dt : telChu(), so: dt && so ? so : telSo(), email: RE_EMAIL.test(email) ? email : '', zalo: linkHopLe(o.zalo)};
}

/* Các mục đang có trên trang, gọi đúng chữ trên thanh tab. */
export function lienKetMua(coMua, coTiec) {
  const ra = [
    {k: 'today', ten: t('tab_today', 'Có sẵn hôm nay'), href: '#/'},
    {k: 'order', ten: t('tab_order', 'Đặt bánh trước'), href: '#/dat-truoc'}
  ];
  if (coMua) ra.push({k: 'season', ten: t('tab_season', 'In season'), href: '#/in-season'});
  ra.push({k: 'uu_dai', ten: t('tab_uu_dai', 'Ưu đãi'), href: '#/uu-dai'});
  if (coTiec) ra.push({k: 'tiec', ten: t('tab_tiec', 'Tiệc'), href: '#/tiec'});
  ra.push({k: '', ten: t('nut_thanh_vien', 'Thành viên'), href: '/thanh-vien'});
  /* v630: trang riêng cho quán, khách sạn, nhà hàng đặt sỉ (không phải tab). */
  ra.push({k: '', ten: t('ct630_banh_si', 'Bánh sỉ cho quán'), href: '/banh-si'});
  ra.push({k: 'tuyen_dung', ten: t('tab_tuyen_dung', 'Tuyển dụng'), href: '#/tuyen-dung'});
  return ra;
}

const TAB_BANH = ['today', 'order', 'season', 'store'];

/* Biểu tượng mạng xã hội vẽ bằng nét, không tải ảnh ngoài. */
const svg = (con, to) => h('svg', {viewBox: '0 0 24 24', 'aria-hidden': 'true', fill: to ? 'currentColor' : 'none', stroke: to ? 'none' : 'currentColor',
  'stroke-width': '1.6', 'stroke-linecap': 'round', 'stroke-linejoin': 'round'}, con);
const BIEU_TUONG = {
  instagram: () => svg([h('rect', {x: 3.5, y: 3.5, width: 17, height: 17, rx: 5}), h('circle', {cx: 12, cy: 12, r: 4}),
    h('circle', {cx: 17, cy: 7, r: .9, fill: 'currentColor', stroke: 'none'})]),
  facebook: () => svg([h('path', {d: 'M13.5 21v-7.2h2.6l.4-3h-3V8.9c0-.9.3-1.5 1.5-1.5h1.6V4.7c-.3 0-1.2-.1-2.3-.1-2.3 0-3.8 1.4-3.8 3.9v2.3H7.9v3h2.6V21z'})], true),
  zalo: () => h('span', {class: 'ctr-mxh-chu', 'aria-hidden': 'true'}, 'Zalo'),
  tiktok: () => svg([h('path', {d: 'M14 3.5v11.2a3.6 3.6 0 1 1-3.6-3.6'}), h('path', {d: 'M14 3.5c.4 2.7 2.2 4.4 5 4.6'})])
};

/* ---------- thành phần ---------- */
export const ChanTrang = {
  name: 'ChanTrang',
  props: {kho: Object, go: Function},
  data() { return {mo: {cua_hang: true, lien_he: false, mua: false, chinh_sach: false}}; },
  methods: {
    bat(k) { this.mo[k] = !this.mo[k]; },
    chonBanh() {
      const tab = this.kho && this.kho.S ? this.kho.S.tab : '';
      if (this.go) this.go(TAB_BANH.includes(tab) ? tab : 'today');
    },
    muc(k, ten, con, id) {
      const mo = !!this.mo[k];
      return h('section', {class: 'ctr-muc ctr-' + k.replace('_', '-') + (mo ? ' mo' : ''), 'data-muc': k}, [
        h('h3', {class: 'ctr-h'}, ten),
        h('button', {class: 'ctr-mo', type: 'button', 'aria-expanded': String(mo), 'aria-controls': id, onClick: () => this.bat(k)},
          [h('span', null, ten), h('i', {class: 'ctr-dau', 'aria-hidden': 'true'})]),
        h('div', {class: 'ctr-than', id}, con)
      ]);
    }
  },
  render() {
    const kho = this.kho || {}, S = kho.S || {};
    const ch = S.cauHinh || {};
    const lh = ND.lien_he || ch.lien_he || {};
    const lien = lienHeChanTrang(lh);
    const mxh = mangXaHoi(lh);
    const cuaHang = cuaHangHien();
    const duong = typeof location === 'object' && location ? location.pathname : '';
    const chinhSach = locChinhSach(ch.chinh_sach, duong);
    const coMua = !!(kho.coMua && kho.coMua.value);
    const mua = lienKetMua(coMua, dsMuc('tiec').length > 0);
    const tien = n => (kho.T && kho.T.tienVN ? kho.T.tienVN(n) : String(n));
    const mienPhi = Number(S.mienPhiTu) || 0;
    const camKet = mienPhi > 0
      ? [{chu: t('ct630_gtgt', 'Giá đã gồm thuế GTGT')}, {chu: t('ct630_mien_phi', 'Miễn phí giao cho đơn từ {tien}', {tien: tien(mienPhi)}), id: 'fNotePhi'}]
      : [{chu: t('dat_banh_8b550092a', 'Giá đã gồm thuế GTGT, chưa gồm phí vận chuyển'), id: 'fNotePhi'}];
    camKet.push({chu: t('ct630_hoa_don', 'Xuất hoá đơn điện tử theo yêu cầu')});
    camKet.push({chu: t('dat_banh_4c203e5ec', 'Giá và tồn kho thay đổi theo mùa và nguyên liệu nhập khẩu')});
    const chiDuong = t('cua_hang_chi_duong', 'Chỉ đường') + ' ›';

    const luoi = [
      h('div', {class: 'ctr-thuong-hieu'}, [
        h('img', {class: 'ctr-logo', src: LOGO, alt: t('dat_banh_913466c0d', 'The Vagabond Pâtisserie')}),
        h('p', {class: 'ctr-cau'}, t('ct630_thuong_hieu', 'Bánh Pháp thủ công ở Sài Gòn.')),
        mxh.length ? h('nav', {class: 'ctr-mxh', id: 'ctrMxh', 'aria-label': t('ct630_mxh', 'Mạng xã hội')},
          mxh.map(x => h('a', {class: 'ctr-mxh-nut', href: x.url, target: '_blank', rel: 'noopener noreferrer', 'data-mxh': x.k, 'aria-label': x.ten, title: x.ten}, [BIEU_TUONG[x.k]()]))) : null
      ]),
      cuaHang.length ? this.muc('cua_hang', t('ct630_cua_hang', 'Cửa hàng'), cuaHang.map(c => h('div', {class: 'ctr-ch', 'data-cua-hang': c.id}, [
        h('b', null, c.ten), h('p', null, c.dia_chi), c.gio_mo_cua ? h('p', {class: 'ctr-gio'}, c.gio_mo_cua) : null,
        chiDuongAnToan(c.chi_duong) ? h('a', {class: 'ctr-chi-duong', href: c.chi_duong, target: '_blank', rel: 'noopener'}, chiDuong) : null
      ])), 'ctrCuaHang') : null,
      this.muc('lien_he', t('ct630_lien_he', 'Liên hệ'), [h('div', {id: 'fLienHe'}, [
        h('a', {class: 'ctr-dt', href: 'tel:' + lien.so}, [h('b', null, lien.dt)]),
        lien.email ? h('a', {href: 'mailto:' + lien.email}, lien.email) : null,
        lien.zalo ? h('a', {href: lien.zalo, target: '_blank', rel: 'noopener noreferrer'}, t('ct630_zalo', 'Nhắn Zalo')) : null,
        h('p', null, t('dat_banh_cc4a76159', 'Bếp Tân Sơn Hoà: 307/1 Nguyễn Văn Trỗi, Phường Tân Sơn Hoà (Tân Bình cũ), TP. Hồ Chí Minh'))
      ])], 'ctrLienHe'),
      this.muc('mua', t('ct630_mua_banh', 'Mua bánh'), [h('nav', {class: 'ctr-ds', 'aria-label': t('ct630_mua_banh', 'Mua bánh')},
        mua.map(m => h('a', {href: m.href, 'data-tab': m.k || undefined,
          onClick: m.k && this.go ? e => { e.preventDefault(); this.go(m.k); } : undefined}, m.ten)))], 'ctrMua')
    ];
    const day = [
      h('div', {class: 'ctr-phap-ly', id: 'fPhapNhan'}, [
        h('p', null, [h('span', null, '© ' + ngayVN().slice(0, 4) + ' ' + t('dat_banh_15f2c7f29', 'Công ty TNHH Patisserie Vagabond')),
          h('span', {class: 'ctr-cham', 'aria-hidden': 'true'}, ' · '), h('span', null, t('dat_banh_2085c9658', 'Mã số thuế 0318561568'))]),
        h('p', null, t('dat_banh_2f7b911ea', 'Cửa hàng Sài Gòn: 9 Trần Cao Vân, Phường Sài Gòn (Quận 1 cũ), TP. Hồ Chí Minh'))
      ]),
      chinhSach.length ? this.muc('chinh_sach', t('dat_banh_e9ba7dd58', 'Chính sách'), [
        h('nav', {class: 'ctr-cs', id: 'fChinhSach', 'aria-label': t('dat_banh_e9ba7dd58', 'Chính sách')}, chinhSach.map(c => h('a', {key: c.duong, href: c.duong}, c.ten)))
      ], 'ctrChinhSach') : null
    ];
    return h('footer', {class: 'ctr', id: 'chanTrang'}, [h('div', {class: 'wrap ctr-khung'}, [
      h('section', {class: 'ctr-moi', 'aria-labelledby': 'ctrMoiH'}, [
        h('h2', {class: 'ctr-moi-h', id: 'ctrMoiH'}, [t('ct630_moi_tieu_de', 'Cùng ngồi lại'), h('em', null, t('ct630_moi_phu', 'Bánh mới mỗi sáng'))]),
        h('div', {class: 'ctr-moi-nut'}, [
          h('button', {class: 'ctr-nut ctr-nut-chinh', type: 'button', id: 'ctrChonBanh', onClick: () => this.chonBanh()}, t('ct630_chon_banh', 'Chọn bánh')),
          h('a', {class: 'ctr-nut ctr-nut-vien', href: '/dat-ban', id: 'ctrDatBan'}, t('nut_dat_ban', 'Đặt bàn'))
        ])
      ]),
      h('div', {class: 'ctr-luoi'}, luoi),
      h('ul', {class: 'ctr-cam-ket', id: 'ctrCamKet'}, camKet.map(x => h('li', {id: x.id}, [h('i', {'aria-hidden': 'true'}, '✓'), x.chu]))),
      h('div', {class: 'ctr-day'}, day)
    ])]);
  }
};

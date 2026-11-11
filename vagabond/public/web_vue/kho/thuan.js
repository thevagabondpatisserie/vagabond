/* Các phép THUẦN của trang đặt bánh bản Vue. Không chạm DOM, không gọi mạng,
   không đọc biến toàn cục: node chạy thẳng được (vagabond/khung/kiem_thu/
   hanh_vi/web_vue_thuan.mjs).

   Phần lớn chép NGUYÊN luật từ banh.html cũ (#205, #367, v589), đổi duy nhất
   một chỗ: chữ hiện cho khách đi qua tham số `t(khoa, macDinh, thay)` thay vì
   gọi thẳng chuWeb toàn cục. */

export const NGUONG_TON = 10; /* trên mức này thì không khoe số nữa */

export const t0 = (k, macDinh, thay) => String(macDinh || '').replace(/\{([a-z_]+)\}/g,
  (g, x) => (thay && Object.prototype.hasOwnProperty.call(thay, x) ? String(thay[x]) : g));

export function tienVN(n) {
  /* 1250000 -> "1.250.000 đ". Không dùng toLocaleString vì node của máy CI có
     thể thiếu dữ liệu ngôn ngữ vi-VN. */
  return String(Math.round(Number(n) || 0)).replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ' đ';
}

export function dmy(d) {
  return String(d.getDate()).padStart(2, '0') + '/' + String(d.getMonth() + 1).padStart(2, '0');
}

export function isoNgay(d) {
  /* yyyy-mm-dd theo giờ địa phương. KHÔNG dùng toISOString vì quy về UTC,
     ở múi +07 buổi tối bị lùi mất một ngày. */
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
}

export function lechNgay(homNayIso, ngayIso) {
  if (!homNayIso || !ngayIso) return null;
  const a = new Date(homNayIso + 'T00:00:00'), b = new Date(ngayIso + 'T00:00:00');
  if (isNaN(a.getTime()) || isNaN(b.getTime())) return null;
  return Math.round((b - a) / 86400000);
}

export function ngayTuNeo(ngayIso, lech, moc) {
  /* NGÀY THẬT đang chọn. Ưu tiên ngày đã neo; không có neo mới tính từ độ lệch
     (#205: độ lệch tự nó sai sau nửa đêm). */
  if (ngayIso) {
    const a = new Date(ngayIso + 'T00:00:00');
    if (!isNaN(a.getTime())) return a;
  }
  const t = moc ? new Date(moc) : new Date();
  t.setHours(0, 0, 0, 0);
  const d = new Date(t);
  d.setDate(t.getDate() + (Number(lech) || 0));
  return d;
}

export function nhanNgay(lech, moc, tenThu, t = t0) {
  const tg = moc ? new Date(moc) : new Date();
  tg.setHours(0, 0, 0, 0);
  const d = new Date(tg);
  d.setDate(tg.getDate() + (Number(lech) || 0));
  const thu = (tenThu && tenThu.length === 7) ? tenThu[d.getDay()] : '';
  return {
    ten: lech === 0 ? t('dat_banh_0048b6a40', 'Hôm nay') : lech === 1 ? t('dat_banh_b2d702504', 'Ngày mai') : thu,
    ngay: dmy(d)
  };
}

export function gioToiThieu(lech, gioHienTai, prepHours, tomorrowFrom) {
  if (lech === 0) return Number(gioHienTai) + Number(prepHours);
  if (lech === 1) return Number(tomorrowFrom);
  return 0;
}

export function lichConHopLe(lech, gioBatDau, gioHienTai, prepHours, tomorrowFrom) {
  if (lech === null || lech === undefined) return false;
  if (Number(lech) < 0) return false;
  return Number(gioBatDau) >= gioToiThieu(Number(lech), gioHienTai, prepHours, tomorrowFrom);
}

export function daChotLich(daChonNgay, daChonGio) { return !!daChonNgay && !!daChonGio; }

export function hienTomTatLich(daChon, dangMoLich, gioConHopLe) { return !!daChon && !dangMoLich && !!gioConHopLe; }

export function nhanTon(con, donVi, t = t0) {
  /* Nhãn tồn cho khách đọc, không đổi số thật. Chưa tải hay lỗi thì rỗng:
     không đoán bừa còn hay hết. */
  if (con === null || con === undefined || con === '') return '';
  const n = Number(con);
  if (!isFinite(n)) return '';
  if (n <= 0) return t('dat_banh_053152152', 'Tạm hết');
  if (n <= NGUONG_TON) return t('dat_banh_65a87a844', 'Chỉ còn') + ' ' + n + (donVi ? ' ' + donVi : '');
  return t('dat_banh_9c6b482c5', 'Còn hàng');
}

export function laMienPhi(tienBanh, nguong) {
  const g = Number(nguong) || 0;
  return g > 0 && (Number(tienBanh) || 0) >= g;
}

export function dongMienPhi(tienBanh, nguong, t = t0) {
  const g = Number(nguong) || 0;
  if (g <= 0) return t('dat_banh_8b2c2134b', 'chưa gồm phí giao');
  if (laMienPhi(tienBanh, g)) return t('dat_banh_7cdc938e9', 'Đơn này được miễn phí giao');
  return t('dat_banh_d6d862911', 'Miễn phí giao cho đơn từ') + ' ' + tienVN(g);
}

export function trangThaiPhi(tuLay, mienPhi, phi, kieu, t = t0) {
  /* Bốn trạng thái như máy chủ (don_web.quyet_phi_giao) cộng "dự kiến" và
     "chưa chọn". Chưa rõ thì KHÔNG hiện 0 và KHÔNG hiện miễn phí. */
  const p = Number(phi) || 0;
  const phiGiao = t('dat_banh_06a446f5c', 'Phí giao'), tong = t('dat_banh_de995d836', 'Tổng');
  const tamTinh = t('dat_banh_a68e4733f', 'Tạm tính, chưa gồm phí giao');
  if (tuLay) return {nhan: phiGiao, gia_tri: t('dat_banh_750c8c2d4', 'Tự lấy, không tính phí'), phi: 0, tong_nhan: tong};
  if (mienPhi) return {nhan: phiGiao, gia_tri: t('dat_banh_18b7b9c03', 'Miễn phí giao'), phi: 0, tong_nhan: tong};
  if (kieu === 'chinh_xac' && p > 0) return {nhan: phiGiao, gia_tri: tienVN(p), phi: p, tong_nhan: tong};
  if (kieu === 'du_kien' && p > 0) return {nhan: t('dat_banh_c78196e46', 'Phí giao dự kiến'), gia_tri: tienVN(p), phi: p, tong_nhan: t('dat_banh_d38ede0d6', 'Tạm tính, theo phí dự kiến')};
  if (kieu === 'chua_ro') return {nhan: phiGiao, gia_tri: t('dat_banh_a3dc0c8d7', 'Chúng tôi báo phí khi xác nhận'), phi: 0, tong_nhan: tamTinh};
  return {nhan: phiGiao, gia_tri: t('dat_banh_05ba51b4a', 'Chọn khu vực hoặc nhập địa chỉ'), phi: 0, tong_nhan: tamTinh};
}

export function laChuViet(s) {
  return /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/i.test(String(s || ''));
}

export function taoNonce(ngauNhien) {
  let b = ngauNhien ? ngauNhien(24) : null;
  if (!b || b.length < 24) { b = []; for (let i = 0; i < 24; i++) b.push(Math.floor(Math.random() * 256)); }
  const bang = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_';
  let ra = '';
  for (let j = 0; j < 24; j += 3) {
    const n = (b[j] << 16) | (b[j + 1] << 8) | b[j + 2];
    ra += bang[(n >> 18) & 63] + bang[(n >> 12) & 63] + bang[(n >> 6) & 63] + bang[n & 63];
  }
  return ra;
}

export function docFb(cookie, timKiem, bayGioMs) {
  const lay = ten => { const m = String(cookie || '').match(new RegExp('(?:^|;\\s*)' + ten + '=([^;]*)')); return m ? decodeURIComponent(m[1]) : ''; };
  let fbp = lay('_fbp'), fbc = lay('_fbc');
  if (!fbc) {
    const m = String(timKiem || '').match(/[?&]fbclid=([^&#]+)/);
    if (m) fbc = 'fb.1.' + Math.floor(Number(bayGioMs) || 0) + '.' + decodeURIComponent(m[1]);
  }
  return {fbp, fbc};
}

export function slug(s) {
  return String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/đ/g, 'd').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}

export function vgbChuan(s) {
  return String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd').replace(/[^a-z0-9]/g, '');
}

/* ---------------- Giỏ ---------------- */

/* v598: MỘT nguồn cho dụng cụ tặng theo yêu cầu (nĩa gỗ, dĩa bã mía, thiệp nhỏ),
   như chuanDungCu của banh.html v597. Mỗi loại kẹp 0 tới 30. */
export function chuanDungCu(d) {
  const so = x => Math.min(30, Math.max(0, parseInt(x) || 0));
  d = d || {};
  return {nia: so(d.nia), dia: so(d.dia), thiep: so(d.thiep)};
}
export function cartKey(o) {
  return [o.id, o.wish, (o.adds || []).map(a => a.id).join('+'), [o.dung_cu?.nia || 0, o.dung_cu?.dia || 0, o.dung_cu?.thiep || 0].join(',')].join('|');
}
export function lineUnit(o) { return o.price + (o.adds || []).reduce((a, x) => a + x.p, 0); }
export function cartCount(gio) { return gio.reduce((a, x) => a + x.qty, 0); }
export function cartTotal(gio) { return gio.reduce((a, x) => a + lineUnit(x) * x.qty, 0); }
export function daCoTrongGio(gio, id) { return gio.filter(x => x.id === id).reduce((a, x) => a + x.qty, 0); }

/* v649 (Loan Anh báo, anh Việt chọn tách đơn 11/11/2026): bánh đặt trước nhận
   từ ngày mai; bánh nhận trong ngày lấy ở tab Có sẵn hôm nay. Một giỏ không
   trộn hai loại. Hàng mùa vụ, hàng quầy (cm 0) không thuộc hai loại này. */
export function laBanhDatTruoc(o) { return !!o && Number(o.cm) > 0 && o.nguon !== 'today'; }
export function laBanhHomNay(o) { return !!o && Number(o.cm) > 0 && o.nguon === 'today'; }
export function chanHomNay(gio) { return (gio || []).some(laBanhDatTruoc); }
export function gioTron(gio) { return chanHomNay(gio) && (gio || []).some(laBanhHomNay); }
export function xungDotGio(gio, o, boQua = -1) {
  /* Thêm dòng o vào giỏ có làm giỏ trộn hai loại không. boQua: dòng đang sửa. */
  if (!o || !(Number(o.cm) > 0)) return '';
  const con = (gio || []).filter((x, i) => i !== boQua);
  if (laBanhDatTruoc(o) && con.some(laBanhHomNay)) return 'co_hom_nay';
  if (laBanhHomNay(o) && con.some(laBanhDatTruoc)) return 'co_dat_truoc';
  return '';
}

export function hangGui(gio) {
  /* v589: MỘT nguồn cho danh sách món gửi máy chủ, dùng chung lúc gửi đơn và
     lúc hỏi ưu đãi. Gộp dòng trùng mã. */
  const qty = {};
  gio.forEach(o => {
    qty[o.id] = (qty[o.id] || 0) + o.qty;
    (o.adds || []).forEach(a => { qty[a.id] = (qty[a.id] || 0) + o.qty; });
  });
  return Object.keys(qty).map(id => ({variation_id: id, quantity: qty[id]}));
}

export function themVaoGio(gio, o) {
  /* Cấu hình giống hệt thì cộng dồn số lượng. Trả về dòng trùng (nếu có). */
  const key = cartKey(o);
  const hit = gio.find(x => cartKey(x) === key);
  if (hit) hit.qty += o.qty; else gio.push(o);
  return hit || null;
}

/* Hình cắt bánh của hộp Cách chọn size: n đường từ tâm ra mép vòng bán kính 44
   trong khung 100 x 100, cùng phép vẽ veHinhCat của banh.html v597. */
export function duongCat(n) {
  const ra = [];
  for (let i = 0; i < n; i++) {
    const g = 2 * Math.PI * i / n;
    ra.push({x2: (50 + 44 * Math.cos(g)).toFixed(1), y2: (50 + 44 * Math.sin(g)).toFixed(1)});
  }
  return ra;
}
export function chuDungCu(o) {
  /* Chữ in phiếu bếp: nhân số lượng bánh, cùng chữ với banh.html v597. */
  if (!o || !o.dung_cu) return '';
  const d = o.dung_cu;
  return [(d.nia || d.dia) ? `${(d.nia || 0) * o.qty} nĩa gỗ, ${(d.dia || 0) * o.qty} dĩa bã mía` : '',
    d.thiep ? `${d.thiep * o.qty} thiệp nhỏ` : ''].filter(Boolean).join(', ');
}

/* ---------------- Danh mục ---------------- */

export function tronMon(cakes, nhom) {
  /* Gom danh sách "có thể bán" của máy chủ vào CAKES (BANHVER 6, 08/08/2026).
     Mã bếp thêm tay ở màn kiểm bánh cũng tự lên đây. */
  if (!nhom || !nhom.length) return;
  nhom.forEach(g => {
    if (!g.sizes || !g.sizes.length) return;
    const ten = vgbChuan(g.ten);
    let c = cakes.find(x => vgbChuan(x.k) === ten) || cakes.find(x => x.sizes.some(s => g.sizes.some(y => y.ma === s.id))) || null;
    if (!c) { c = {k: g.ten, img: g.anh || '', sizes: [], themTay: 1}; cakes.push(c); }
    g.sizes.forEach(y => {
      const s = c.sizes.find(z => z.cm === y.cm);
      if (s) { s.id = y.ma; if (Number.isFinite(y.gia) && y.gia >= 0) s.p = y.gia; }
      else c.sizes.push({cm: y.cm, p: y.gia || 0, id: y.ma});
    });
    c.sizes.sort((a, b) => (a.cm || 0) - (b.cm || 0));
    if (g.anh) c.img = g.anh;
    if (g.anhs && g.anhs.length) c.anhs = g.anhs;
    /* v644: bánh có bộ nội dung web (Marketing sửa ở trình biên tập, thẻ Bánh)
       thì mô tả, tầng hương vị chỉ lấy từ đó, kể cả khi để trống. */
    if (g.tu_web) { c.tuWeb = 1; c.desc = g.mo_ta || ''; c.layers = []; }
    else if (g.mo_ta) c.desc = g.mo_ta;
    if (g.tang && g.tang.length) {
      c.layers = g.tang.map(x => {
        const v = String(x).split(/\s*[:–—-]\s+/);
        return v.length > 1 ? [v[0], v.slice(1).join(' - ')] : [x, ''];
      });
    }
  });
}

export function tachRuot(moTa) {
  /* "1 x Dừa, 80gram, 1 x ..." -> [[so, ten], ...] cho bảng hàng mùa vụ. */
  if (!moTa) return [];
  return String(moTa).split(/,\s*(?=\d+\s*x\s)/).map(d => {
    const c = d.trim().match(/^(\d+)\s*x\s*(.+)$/);
    return c ? [c[1] + ' x', c[2]] : ['', d.trim()];
  });
}

export function lienKetAnToan(u) {
  u = String(u || '').trim();
  if (/^https:\/\/[^\s"'<>]+$/i.test(u) || /^\/[A-Za-z0-9\/_-]*$/.test(u)) return u;
  return '';
}

export function linkHopLe(u) { u = String(u || ''); return (/^https:\/\/[^\s/@\\]+(\/|$)/.test(u) && !/\s/.test(u)) ? u : ''; }

export function maskAddr(s) { return String(s || '').replace(/^\s*[0-9]+([\/\-][0-9A-Za-z]+)*/, '***'); }
export function maskPhone(s) { return String(s || '').replace(/(\d{3})$/, '***'); }

/* ---------- v630: bánh thiết kế riêng ----------
   Bản JS của thiet_ke_rieng.tien_coc, tinh_gia, so_ngay_cua. Màn chỉ HIỆN tạm
   trước khi gửi; máy chủ tính lại và số trên màn QR là số máy chủ trả về.
   Ca thu_thiet_ke_rieng_630 chạy hai bản trên cùng một bảng ca. */
export const TKR_NGAY_TOI_THIEU = 7;
export function tkrCoc(tong) {
  const t = Math.round(Number(tong) || 0);
  return t > 0 ? Math.ceil(t / 2 / 1000) * 1000 : 0;
}
export function tkrSoNgay(tp) {
  const n = parseInt(String((tp && tp.so_ngay) || TKR_NGAY_TOI_THIEU), 10);
  return Math.max(TKR_NGAY_TOI_THIEU, isNaN(n) ? TKR_NGAY_TOI_THIEU : n);
}
export function tkrNgaySomNhat(homNayIso, tp) {
  const p = String(homNayIso || '').slice(0, 10).split('-').map(Number);
  const d = new Date(Date.UTC(p[0], (p[1] || 1) - 1, p[2] || 1));
  d.setUTCDate(d.getUTCDate() + tkrSoNgay(tp));
  return d.toISOString().slice(0, 10);
}
export function tkrTuGia(tp) {
  const ds = ((tp && tp.kich_co) || []).map(x => parseInt(x.gia, 10) || 0).filter(x => x > 0);
  return ds.length ? Math.min(...ds) : 0;
}
/* Trả {tong, coc, con_lai} hoặc {loi}. Cùng luật nhóm trang trí với máy chủ. */
export function tkrTinh(tp, tenKichCo, dsTrangTri) {
  const kc = ((tp && tp.kich_co) || []).find(x => x.ten === tenKichCo);
  if (!kc) return {loi: 'Chọn một size của tác phẩm.'};
  const co = {};
  ((tp && tp.trang_tri) || []).forEach(x => { co[x.ten] = x; });
  const chon = [], nhom = {};
  for (const t of dsTrangTri || []) {
    if (!co[t]) return {loi: 'Trang trí "' + String(t).slice(0, 60) + '" không còn trong danh sách. Tải lại trang.'};
    if (!chon.includes(t)) chon.push(t);
  }
  for (const t of chon) {
    const n = String(co[t].nhom || '');
    if (n) { if (nhom[n]) return {loi: 'Nhóm ' + n + ' chỉ chọn một: ' + nhom[n] + ' hoặc ' + t + '.'}; nhom[n] = t; }
  }
  const giaKc = parseInt(kc.gia, 10) || 0;
  const tong = giaKc + chon.reduce((a, t) => a + (parseInt(co[t].gia_them, 10) || 0), 0);
  if (giaKc <= 0 || tong <= 0) return {loi: 'Tác phẩm này chưa có giá. Nhờ Sales tư vấn trước.'};
  const coc = tkrCoc(tong);
  return {tong, coc, con_lai: tong - coc};
}
/* Bấm một chip trang trí: cùng nhóm thì thay, khác nhóm (hoặc không nhóm) thì bật tắt. */
export function tkrBatTrangTri(tp, dang, ten) {
  const co = {};
  ((tp && tp.trang_tri) || []).forEach(x => { co[x.ten] = x; });
  if (!co[ten]) return (dang || []).slice();
  if ((dang || []).includes(ten)) return dang.filter(x => x !== ten);
  const n = String(co[ten].nhom || '');
  return [...(dang || []).filter(x => !n || String((co[x] || {}).nhom || '') !== n), ten];
}

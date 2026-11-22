import {createApp, h, reactive} from '../lib/vue.esm-browser.prod.js';
import {ghi as ghiMang} from '../kho/api.js';
import {itemsGuiDon} from '../kho/thuan.js';
import * as NH from './ngan-hang.js';

// Chỉ dựng thẻ được máy chủ làm sạch, chữ là text node, không thành template.
export function veCay(cay) {
  return (cay || []).map(n => typeof n === 'string' ? n : h(n.tag, n.props || {}, veCay(n.con)));
}
const KHOA_BN = 'vgb_bien_nhan_vue', KHOA_TOKEN = 'vgb_bien_nhan_token';

/* v647 (anh Việt 10/11/2026): banner chỗ "Đặt xong" trên biên nhận. Máy chủ
   (noi_dung_web.banner_hien) đã lọc ngày và ảnh; ở đây chỉ vẽ, link và ảnh vẫn
   qua phép an toàn: đường dẫn trong web hoặc HTTPS. Kiểu viết thẳng vào thẻ để
   không đụng mã băm của trang-khach.css ở bốn trang. */
const anToanBn = u => typeof u === 'string' && !/[\s\\]/.test(u) && ((u[0] === '/' && u[1] !== '/') || /^https:\/\/[^/@]+(?:\/|$)/.test(u));
export function veBanner(ds) {
  return (Array.isArray(ds) ? ds : []).filter(b => b && anToanBn(b.anh)).map(b => {
    const nguon = [];
    if (anToanBn(b.anh_dt)) nguon.push(h('source', {media: '(max-width: 640px)', srcset: b.anh_dt}));
    nguon.push(h('img', {src: b.anh, alt: b.mo_ta_anh || b.tieu_de || '', loading: 'lazy', decoding: 'async',
      style: {display: 'block', width: '100%', height: 'auto'}}));
    const the = {class: 'bn-banner', 'data-banner': 'dat_xong', style: {display: 'block', margin: '20px 0', borderRadius: '12px', overflow: 'hidden', lineHeight: 0}};
    return anToanBn(b.lien_ket) ? h('a', Object.assign(the, {href: b.lien_ket}), [h('picture', null, nguon)]) : h('div', the, [h('picture', null, nguon)]);
  });
}
const RE_TOKEN = /\/xong\/([A-Za-z0-9_-]{43})$/;
function phien(win) {
  return {
    doc: k => { try { return win.sessionStorage.getItem(k); } catch (_) { return null; } },
    ghi: (k, v) => { try { win.sessionStorage.setItem(k, v); } catch (_) {} }
  };
}
export function bienNhan(D, win = window) {
  const {doc, ghi} = phien(win);
  /* v638: giữ token trong kho phiên của CHÍNH tab này (token vốn đã nằm trên
     đường dẫn của tab) để trang hỏi lại trạng thái thanh toán, kể cả khi khách
     quay về /banh/xong sau trang OnePay. Không gửi token đi đâu ngoài máy chủ. */
  try {
    const m = String(win.location.pathname || '').match(RE_TOKEN);
    if (m && D.bien_nhan) ghi(KHOA_TOKEN, m[1]);
  } catch (_) {}
  // Gỡ token TRƯỚC Pixel. Nếu không gỡ được thì không tải Pixel.
  let anToan = false;
  try {
    win.history.replaceState(null, '', win.location.pathname.replace(/\/xong\/[^/]+$/, '/xong'));
    anToan = !/\/xong\//.test(win.location.pathname);
  } catch (_) {}
  if (D.khong_token) {
    /* v603 (Codex #489): công tắc đổi giữa chừng thì tải lại /banh/xong ra trang
       kia. Tab chỉ có bản tóm tắt của biên nhận trang cũ thì chuyển sang đúng
       trang cũ (?ban=cu) để khách vẫn thấy biên nhận của mình. */
    if (!doc(KHOA_BN) && doc('vgb_bien_nhan')) {
      try { win.location.replace('/banh/xong?ban=cu'); return null; } catch (_) { /* để trang mặc định */ }
    }
    try { return JSON.parse(doc(KHOA_BN) || 'null'); } catch (_) { return null; }
  }
  const bn = D.bien_nhan;
  if (bn) ghi(KHOA_BN, JSON.stringify(bn));
  const px = String(D.pixel_id || '').replace(/\D/g, ''), ev = D.su_kien || {};
  if (anToan && px) {
    if (!win.fbq) {
      const f = win.fbq = function() { f.callMethod ? f.callMethod.apply(f, arguments) : f.queue.push(arguments); };
      f.queue = []; f.loaded = true; f.version = '2.0';
      const script = win.document.createElement('script'); script.async = true;
      script.src = 'https://connect.facebook.net/en_US/fbevents.js'; win.document.head.appendChild(script);
    }
    win.fbq('init', px); win.fbq('track', 'PageView');
    if (ev.ban && ev.event_id && !doc('vgb_ev_' + ev.event_id)) {
      win.fbq('trackCustom', 'GuiDon', {value: Number(ev.gia_tri) || 0, currency: 'VND',
        content_ids: ev.ma_mon || [], content_type: 'product'}, {eventID: String(ev.event_id)});
      ghi('vgb_ev_' + ev.event_id, '1');
    }
  }
  /* v664: gửi đơn sang GA4 (purchase), mã giao dịch là mã sự kiện của đơn; mở lại
     biên nhận không gửi lần hai. Chỉ khi đã gỡ token khỏi đường dẫn. */
  if (anToan && ev.ban && ev.event_id && typeof win.gtag === 'function' && !doc('vgb_ga_' + ev.event_id)) {
    win.gtag('event', 'purchase', {transaction_id: String(ev.event_id), value: Number(ev.gia_tri) || 0, currency: 'VND',
      items: itemsGuiDon(ev)});
    ghi('vgb_ga_' + ev.event_id, '1');
  }
  return bn;
}

/* v638: hỏi lại trạng thái thanh toán mỗi 5 giây, tối đa 30 phút. */
export const NHIP_HOI = 5000, SO_LAN_HOI = 360;
const RE_ANH_QR = /^data:image\/svg\+xml;base64,[A-Za-z0-9+/=]+$/;
const CON_CHO = ['cho', 'thieu'];

/* Thành phần trang khách (biên nhận, chính sách). `mt` tiêm môi trường cho bộ
   kiểm node: cửa sổ, mạng, hẹn giờ, chuyển trang, chép chữ. */
export function taoTrang(D, mt = {}) {
  const win = mt.win || (typeof window !== 'undefined' ? window : {});
  const ghi = mt.ghi || ghiMang;
  const hen = mt.hen || ((f, ms) => win.setTimeout(f, ms));
  const dieuHuong = mt.dieuHuong || (u => { win.location.href = u; });
  const chep = mt.chep || (s => win.navigator.clipboard.writeText(s));
  const bn = D.loai === 'bien_nhan' ? bienNhan(D, win) : null;
  const ph = phien(win);
  const token = bn ? (ph.doc(KHOA_TOKEN) || '') : '';
  const chu = (k, macDinh) => (D.nhan || {})[k] || macDinh;
  /* Codex #484: câu nghiệp vụ (cách nhận, thanh toán, phí giao, tổng) đổi thành
     nhãn Editor theo bảng máy chủ gửi, cùng nguồn với biên nhận trang cũ. */
  const bang = D.bang || {}, tienTo = bang.tien_to || [];
  const giaTri = v => {
    const s = String(v == null ? '' : v);
    if (tienTo[0] && s.startsWith(tienTo[0])) return chu(tienTo[1], tienTo[2]) + ' ' + s.slice(tienTo[0].length);
    const m = (bang.gia_tri || {})[s];
    return m ? chu(m[0], m[1]) : s;
  };
  if (D.loai === 'bien_nhan') try { win.document.title = chu('bien_nhan_8d4e8c5d8', 'Biên nhận yêu cầu đặt bánh · The Vagabond Pâtisserie'); } catch (_) {}
  const dong = (nhan, gia, lop = '') => h('div', {class:lop}, [h('dt', nhan), h('dd', gia || '')]);

  /* ---------------- thanh toán (v638) ---------------- */
  const st = reactive({tt: (bn && bn.tt) || null, dangTra: false, loiThe: '', daChep: false, lan: 0});
  const canHoi = () => !!(token && st.tt && CON_CHO.includes(st.tt.trang_thai) && st.tt.cach !== 'cash');
  async function hoiLai() {
    if (!canHoi()) return;
    st.lan++;
    let m = null;
    try { m = await ghi('vagabond.thanh_toan_web.trang_thai', {token}); } catch (_) { m = null; }
    if (m && typeof m === 'object' && typeof m.trang_thai === 'string') {
      st.tt = m;
      if (bn) { bn.tt = m; ph.ghi(KHOA_BN, JSON.stringify(bn)); }
    }
    if (canHoi() && st.lan < SO_LAN_HOI) hen(hoiLai, NHIP_HOI);
  }
  async function traThe() {
    const th = st.tt && st.tt.the;
    if (!th || st.dangTra) return;
    st.dangTra = true; st.loiThe = '';
    let m = null;
    try { m = await ghi('vagabond.onepay.tao_gd', {ma: th.ma, k: th.k}); } catch (_) { m = null; }
    if (m && typeof m.url === 'string' && /^https:\/\//.test(m.url)) { dieuHuong(m.url); return; }
    let cau = '';
    try { cau = JSON.parse(JSON.parse(m._server_messages)[0]).message || ''; } catch (_) {}
    st.loiThe = String(cau || chu('bien_nhan_tt_loi_the', 'Chưa tạo được giao dịch thẻ. Quý khách thử lại sau ít phút hoặc nhắn The Vagabond.'));
    st.dangTra = false;
  }
  /* v684: chép một giá trị (số tài khoản, số tiền, nội dung, mã đơn), báo đúng ô vừa chép. */
  async function chepGiaTri(khoa, v) {
    if (!v) return;
    try { await chep(String(v)); st.daChep = khoa; } catch (_) { st.daChep = ''; }
  }
  async function chepNoiDung() { return chepGiaTri('nd', st.tt && st.tt.ck && st.tt.ck.noi_dung); }

  /* ---------------- v684 (BẢN 2 mục 3): biên nhận mới ----------------
     Ba bước Nhận đơn, Thanh toán, Nhận bánh. Trạng thái lấy từ máy chủ. Mở app
     ngân hàng hay quay về từ OnePay KHÔNG có nghĩa là đã trả: chỉ đổi khi máy
     chủ xác nhận (hoiLai đọc thanh_toan_web.trang_thai). */
  const ua = (win.navigator && win.navigator.userAgent) || '';
  const he = NH.heDieuHanh(ua), laDienThoai = !!he;
  const KHOA_APP = 'vgb_app_nh';
  const nhoApp = () => { try { return win.localStorage.getItem(KHOA_APP) || ''; } catch (_) { return ''; } };
  const luuApp = ma => { try { win.localStorage.setItem(KHOA_APP, ma); } catch (_) {} };
  const appLanTruoc = nhoApp();
  Object.assign(st, {app: NH.timApp(appLanTruoc, he) ? appLanTruoc : '', moKhac: false, timNh: '', hienQr: !laDienThoai, xemDu: {}});
  function chonApp(ma) { st.app = ma; st.moKhac = false; st.timNh = ''; luuApp(ma); }
  function buocMoi() {
    /* 1 = đang ở Thanh toán (chưa trả, trả thiếu); 2 = đang ở Nhận bánh (đã trả, tiền mặt). */
    const k = st.tt;
    if (!k || !k.trang_thai) return 1;
    return k.trang_thai === 'da_thu' || k.trang_thai === 'tien_mat' ? 2 : 1;
  }
  function tienTrinh(huy) {
    if (huy) return h('div', {class: 'bn6-xam', id: 'bn-huy', role: 'status'}, [h('b', chu('bn684_da_huy', 'Đơn này đã huỷ')),
      lienKetNhan() ? h('a', {class: 'bn6-gach', href: lienKetNhan(), rel: 'noopener noreferrer', onClick: chepMa}, chu('bn684_nhan_tiem', 'Nhắn The Vagabond')) : null]);
    const b = buocMoi();
    const ten = [chu('bn684_buoc_1', 'Nhận đơn'), chu('bn684_buoc_2', 'Thanh toán'), chu('bn684_buoc_3', 'Nhận bánh')];
    return h('ol', {class: 'bn6-buoc', id: 'bn-buoc', 'aria-label': chu('bien_nhan_buoc_nhan', 'Tiến độ đơn')},
      ten.map((x, i) => { const lop = i < b ? 'xong' : (i === b ? 'dang' : ''); return h('li', {class: lop, 'aria-current': i === b ? 'step' : null}, [h('i'), h('span', x)]); }));
  }
  const lienKetNhan = () => { const z = (D.lien_he || []).find(a => /zalo/i.test(String(a.href || ''))) || (D.lien_he || [])[0]; return z ? z.href : ''; };
  function chepMa() { if (bn && bn.ma) chepGiaTri('ma', bn.ma); }
  function logoCach(cach) {
    const tep = cach === 'bank' ? 'vietqr.svg' : 'napas.svg';
    return h('img', {class: 'bn6-logo-tt', src: '/assets/vagabond/web_vue/banh/logo-tt/' + tep, alt: '', width: 56, height: 20});
  }
  function nutChep(khoa, nhan, v, id) {
    return h('button', {type: 'button', class: 'bn6-chep', id: id || null, 'data-chep': khoa, onClick: () => chepGiaTri(khoa, v)},
      [h('span', nhan), h('b', String(v || '')), h('em', st.daChep === khoa ? chu('bn684_da_chep', 'Đã chép') : chu('bn684_chep', 'Chép'))]);
  }
  function theTraTien() {
    const k = st.tt;
    if (!k || !k.trang_thai || k.trang_thai === 'huy') return null;
    if (k.trang_thai === 'tien_mat') return h('section', {class: 'bn6-tt', id: 'bn-tt'}, [h('p', chu('bien_nhan_tt_tien_mat', 'Quý khách thanh toán tiền mặt khi nhận bánh.'))]);
    if (k.trang_thai === 'da_thu') return h('section', {class: 'bn6-tt ok', id: 'bn-tt', role: 'status'}, [
      h('p', {class: 'bn6-nhan'}, chu('bn684_da_tt', 'ĐÃ THANH TOÁN')), h('p', {class: 'bn6-so'}, ['✓ ', k.da_thu_chu || k.so_chu]),
      k.cach_thu ? h('p', {class: 'bn6-phu'}, k.cach_thu) : null]);
    const con = [h('p', {class: 'bn6-nhan'}, chu('bn684_cho_tt', 'CÒN CHỜ THANH TOÁN')), h('p', {class: 'bn6-so', id: 'bn-con'}, k.con_chu)];
    if (k.trang_thai === 'thieu') con.push(h('p', {class: 'bn6-phu'}, chu('bn684_thieu', 'Đã nhận {da}, còn thiếu {con}').replace('{da}', k.da_thu_chu || '').replace('{con}', k.con_chu || '')));
    con.push(h('p', {class: 'bn6-cach'}, [logoCach(k.the ? 'the' : 'bank'), h('span', giaTri(bn.thanh_toan))]));
    if (k.the) {
      con.push(h('button', {type: 'button', class: 'bn6-nut', id: 'nut-the', disabled: st.dangTra, onClick: traThe},
        [h('svg', {viewBox: '0 0 24 24', 'aria-hidden': 'true'}, [h('path', {d: 'M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5z'})]),
          st.dangTra ? chu('bien_nhan_tt_dang_chuyen', 'Đang chuyển sang OnePay...') : chu('bn684_nut_onepay', 'THANH TOÁN QUA ONEPAY')]));
      con.push(h('p', {class: 'bn6-phu'}, chu('bien_nhan_tt_the_mo', 'Quý khách được chuyển sang trang bảo mật của OnePay để nhập thẻ và mã OTP.')));
      if (st.loiThe) con.push(h('p', {class: 'bn6-loi', role: 'status'}, st.loiThe));
    } else if (k.ck) {
      const ck = k.ck;
      if (k.the_tat) con.push(h('p', {class: 'bn6-phu'}, chu('bien_nhan_tt_the_tat', 'Thanh toán thẻ đang tạm ngưng. Quý khách chuyển khoản theo mã dưới đây.')));
      if (laDienThoai) {
        const app = NH.timApp(st.app, he);
        const ds = NH.appCho(he), luoi = NH.LUOI.map(m => NH.timApp(m, he)).filter(Boolean);
        con.push(h('p', {class: 'bn6-nho'}, chu('bn684_chon_app', 'CHỌN APP NGÂN HÀNG CỦA QUÝ KHÁCH')));
        con.push(h('div', {class: 'bn6-luoi', role: 'radiogroup'}, luoi.map(a => h('button', {type: 'button', role: 'radio', 'aria-checked': st.app === a.ma ? 'true' : 'false',
          class: {'bn6-app': 1, on: st.app === a.ma}, 'data-app': a.ma, 'aria-label': a.ten, onClick: () => chonApp(a.ma)},
          [h('img', {src: NH.LOGO(a.ma), alt: '', width: 40, height: 40}), h('span', NH.TEN_NGAN[a.ma] || a.ten),
            appLanTruoc === a.ma ? h('small', chu('bn684_lan_truoc', 'Lần trước')) : null])).concat([
          h('button', {type: 'button', class: {'bn6-app': 1, khac: 1, on: !!app && !NH.LUOI.includes(app.ma)}, 'data-app': 'khac', onClick: () => { st.moKhac = true; }},
            [h('b', '···'), h('span', app && !NH.LUOI.includes(app.ma) ? app.ten : chu('bn684_khac', 'Khác'))])])));
        if (st.moKhac) con.push(h('div', {class: 'bn6-bang', role: 'dialog', 'aria-label': chu('bn684_khac_tieu', 'Chọn app ngân hàng')}, [
          h('input', {type: 'search', class: 'bn6-tim', placeholder: chu('bn684_khac_tim', 'Tìm tên ngân hàng'), value: st.timNh, onInput: e => { st.timNh = e.target.value; }}),
          h('div', {class: 'bn6-ds'}, NH.locApp(ds, st.timNh).map(a => h('button', {type: 'button', class: 'bn6-dong', 'data-app': a.ma, onClick: () => chonApp(a.ma)},
            [h('span', a.ten), a.tuDien ? h('small', chu('bn684_tu_dien', 'tự điền')) : null]))),
          h('button', {type: 'button', class: 'bn6-gach', onClick: () => { st.moKhac = false; }}, chu('bn684_dong', 'Đóng'))]));
        const link = app ? NH.linkMoApp(app, ck, k.con, (win.location && win.location.origin ? win.location.origin : '') + '/banh/xong') : null;
        if (link) {
          con.push(h('a', {class: 'bn6-nut', id: 'nut-mo-app', href: link, rel: 'noopener noreferrer'}, chu('bn684_mo_app', 'MỞ APP {ten}').replace('{ten}', app.ten.toUpperCase())));
          con.push(h('p', {class: 'bn6-phu', id: 'bn-cau-app'}, app.tuDien
            ? chu('bn684_tu_dien_cau', 'Số tiền và nội dung đã điền sẵn trong app. Quý khách chỉ cần xác nhận.')
            : chu('bn684_chi_mo_cau', 'App sẽ mở, quý khách dán số tài khoản, số tiền và nội dung đã chép bên dưới.')));
        } else con.push(h('p', {class: 'bn6-phu'}, chu('bn684_chua_chon_app', 'Chọn app ngân hàng để mở và chuyển khoản.')));
        con.push(h('p', {class: 'bn6-phu'}, chu('bn684_giu_nd', 'Vui lòng giữ nguyên nội dung chuyển khoản.')));
        if (!st.hienQr) con.push(h('button', {type: 'button', class: 'bn6-gach', id: 'nut-hien-qr', onClick: () => { st.hienQr = true; }}, chu('bn684_hien_qr', 'Mở trên máy tính? Hiện mã QR để quét')));
      }
      if (st.hienQr && RE_ANH_QR.test(String(ck.anh || ''))) con.push(h('img', {class: 'bn-tt-qr', id: 'bn-qr', src: ck.anh, alt: 'VietQR', width: 220, height: 220}));
      con.push(h('div', {class: 'bn6-chep-ds'}, [
        h('p', {class: 'bn6-phu'}, [ck.ngan_hang, ck.ten].filter(Boolean).join(' · ')),
        nutChep('stk', chu('bien_nhan_tt_stk', 'Số tài khoản'), ck.stk),
        nutChep('so', chu('bn684_so_tien', 'Số tiền'), String(k.con || '')),
        nutChep('nd', chu('bien_nhan_tt_noi_dung', 'Nội dung chuyển khoản'), ck.noi_dung, 'nut-chep')]));
      if (token) con.push(h('p', {class: 'bn6-cho', role: 'status'}, chu('bn684_cho_tien', 'Đang chờ tiền về. Trang này tự báo khi nhận được.')));
    }
    if (k.phi_sau) con.push(h('p', {class: 'bn6-phu'}, chu('bien_nhan_tt_phi_sau', 'Số này là tiền bánh. Phí giao quý khách trả khi nhận bánh.')));
    return h('section', {class: 'bn6-tt', id: 'bn-tt'}, con);
  }
  function theNhan() {
    const nb = bn.nhan_banh || {};
    /* Câu cách nhận giữ nhãn Editor (Codex #484): cùng bảng giaTri với trang cũ. */
    const dongNoi = nb.tu_lay
      ? [giaTri(bn.cach_nhan) + ' ', h('a', {class: 'bn6-gach', href: 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent('The Vagabond ' + (nb.noi || '')), rel: 'noopener noreferrer', target: '_blank'}, chu('bn684_chi_duong', 'Chỉ đường'))]
      : [giaTri(bn.cach_nhan) + (nb.noi ? ' · ' + nb.noi : '')];
    return h('section', {class: 'bn6-the', id: 'bn-nhan'}, [h('h2', chu('bn684_nhan_banh', 'NHẬN BÁNH')),
      h('p', {class: 'bn6-dong-i lich'}, [bn.ngay_nhan, bn.khung_gio].filter(Boolean).join(' · ')),
      h('p', {class: 'bn6-dong-i ghim'}, dongNoi),
      nb.nguoi_nhan || bn.ten ? h('p', {class: 'bn6-dong-i nguoi'}, (nb.nguoi_nhan || bn.ten) + (nb.la_nguoi_dat ? ' · ' + chu('bn684_nguoi_dat', 'người đặt') : '')) : null]);
  }
  /* Codex #606: máy chủ chỉ trả lựa chọn đã lưu (có cờ không, mã thiệp, mã quà);
     chữ khách thấy lấy từ bảng chữ Marketing sửa được. Lời chúc, lời thiệp là
     chữ của khách nên giữ nguyên. */
  function chuChiec(c) {
    const co = c.co === false ? chu('bn684_khong_co', 'Không cờ')
      : (c.loi_chuc ? chu('bn684_co', 'Cờ') + ': “' + c.loi_chuc + '”' : chu('bn684_co_trong', 'Cờ chưa ghi lời chúc'));
    const thiep = c.thiep === 'nho' ? chu('bn684_thiep_nho', 'Thiệp nhỏ')
      : (c.thiep === 'ep_kim' ? chu('bn684_thiep_ep_kim', 'Thiệp ép kim') : chu('bn684_khong_thiep', 'Không thiệp'));
    return [co, thiep + (c.thiep && c.loi_thiep ? ': “' + c.loi_thiep + '”' : '')].join(' · ');
  }
  function chuTang(muc) {
    const s = (muc || []).map(m => (m.ma === 'dia' ? chu('bn684_dia', 'dĩa giấy bã mía') : chu('bn684_nia', 'nĩa gỗ')) + ' x' + m.sl).join(', ');
    return s.charAt(0).toUpperCase() + s.slice(1);
  }
  function theDon() {
    const anh = bn.anh || {}, ds = bn.dong;
    const dong = Array.isArray(ds) && ds.length ? ds.map((d, i) => {
      if (d.loai === 'banh') {
        const phu = (d.chiec || []).map(chuChiec).join(' / ');
        const du = !!st.xemDu[i];
        return h('li', {class: 'bn6-mon'}, [anh[d.ma] ? h('img', {src: anh[d.ma], alt: '', width: 52, height: 52, loading: 'lazy'}) : h('i', {class: 'bn6-anh-trong'}),
          h('div', {class: 'bn6-mon-chu'}, [h('b', d.ten + (d.sl > 1 ? ' x' + d.sl : '')),
            phu ? h('small', {class: {du}}, phu) : null,
            phu && phu.length > 48 && !du ? h('button', {type: 'button', class: 'bn6-gach', onClick: () => { st.xemDu = Object.assign({}, st.xemDu, {[i]: true}); }}, chu('bn684_xem_du', 'Xem đủ')) : null]),
          h('span', {class: 'tien'}, d.gia)]);
      }
      if (d.loai === 'tang') return h('li', {class: 'bn6-mon tang'}, [h('div', {class: 'bn6-mon-chu'}, [h('b', chuTang(d.muc))]), h('span', {class: 'tien'}, chu('bn684_tang_kem', 'tặng kèm'))]);
      return h('li', {class: 'bn6-mon ' + d.loai}, [h('div', {class: 'bn6-mon-chu'}, [h('b', d.ten + (d.sl > 1 ? ' x' + d.sl : ''))]), h('span', {class: 'tien'}, d.gia)]);
    }) : (bn.mon || []).map(m => h('li', {class: 'bn6-mon'}, [h('div', {class: 'bn6-mon-chu'}, [h('b', m.ten + ' x' + m.sl)]), h('span', {class: 'tien'}, m.thanh_tien)]));
    const k = st.tt || {};
    return h('section', {class: 'bn6-the', id: 'bn-don'}, [h('h2', chu('bn684_don_hang', 'ĐƠN HÀNG')), h('ul', {class: 'bn6-ds-mon'}, dong),
      h('dl', {class: 'bn6-tien'}, [
        bn.giam ? dong6(chu('bien_nhan_uu_dai', 'Ưu đãi') + (bn.uu_dai ? ' (' + bn.uu_dai + ')' : ''), bn.giam.replace(/^- /, '− '), 'giam') : null,
        dong6(chu('bien_nhan_06a446f5c', 'Phí giao'), giaTri(bn.phi_giao)),
        dong6(chu('bien_nhan_9d5a6614c', 'Thanh toán'), giaTri(bn.thanh_toan))]),
      h('div', {class: 'bn6-tong'}, [h('span', chu('bn684_tong', 'Tổng cộng')), h('b', giaTri(bn.tong))]),
      k.trang_thai === 'thieu' ? h('dl', {class: 'bn6-tien'}, [dong6(chu('bn684_da_tra', 'Đã trả'), k.da_thu_chu), dong6(chu('bn684_con_thieu', 'Còn thiếu'), k.con_chu, 'thieu')]) : null]);
  }
  const dong6 = (nhan, gia, lop = '') => h('div', {class: lop}, [h('dt', nhan), h('dd', gia || '')]);

  return {
    setup() {
      if (canHoi()) hen(hoiLai, D.khong_token ? 0 : NHIP_HOI);
      return {};
    },
    render() {
      if (D.loai === 'chinh_sach') return h('main', {class: 'cs'}, [h('article', {class:'cs-in'}, [
        h('h1', D.ten), h('p', {class:'cs-mo'}, D.mo || ''), ...veCay(D.cay)])]);
      if (!bn) return h('main', {class:'bn'}, [h('div', {class:'bn-in'}, [
        h('p', {class:'bn-nhan'}, chu('bien_nhan_fae8f9966', 'BIÊN NHẬN')),
        h('h1', chu('bien_nhan_37a6f269e', 'Biên nhận chỉ mở được từ đường dẫn The Vagabond hiện ngay sau khi đặt.')),
        h('p', {class:'bn-cau'}, chu('bien_nhan_bbd687e19', 'Quý khách xem lại mã yêu cầu trong tin nhắn của The Vagabond, hoặc nhắn The Vagabond qua Zalo, Messenger ở cuối trang.')),
        h('div', {class:'bn-nut'}, [h('a', {class:'nut chinh', href:D.trang_chu || '/web_moi/banh'}, chu('bien_nhan_6be58a5f5', 'Về trang đặt bánh'))])])]);
      const huy = !!bn.da_huy || (st.tt && st.tt.trang_thai === 'huy');
      return h('main', {class:'bn bn6'}, [h('div', {class:'bn-in'}, [
        h('div', {class: 'bn6-dau'}, [h('span', {class: 'bn6-dia', 'aria-hidden': 'true'}, '✓'),
          h('h1', chu('bn684_tieu_de', 'Đã nhận yêu cầu đặt bánh')),
          h('button', {type: 'button', class: 'bn6-ma', id: 'bn-ma', onClick: chepMa, 'aria-label': chu('bn684_chep_ma', 'Chép mã đơn') + ' ' + bn.ma},
            st.daChep === 'ma' ? chu('bn684_da_chep_ma', 'Đã chép mã đơn') : bn.ma)]),
        tienTrinh(huy),
        huy ? null : h('p', {class: 'bn-cau'}, buocMoi() === 2 && st.tt && st.tt.trang_thai === 'da_thu'
          ? chu('bien_nhan_da_xac_nhan', 'The Vagabond đã nhận thanh toán và xác nhận đơn của quý khách.')
          : chu('bien_nhan_' + (bn.dang_xac_nhan ? 'cho' : 'nhan'), bn.dang_xac_nhan ? 'Chúng tôi đã tiếp nhận yêu cầu và đang kiểm tra. Quý khách không cần đặt lại.' : 'The Vagabond đã nhận yêu cầu. Đơn được xác nhận sau khi quý khách thanh toán.')),
        huy ? null : theTraTien(),
        theNhan(),
        theDon(),
        ...veBanner(D.banner),
        h('div', {class: 'bn6-cuoi'}, [
          h('button', {type: 'button', class: 'bn6-vien', id: 'nut-luu', onClick: () => { try { win.print(); } catch (_) {} }}, chu('bn684_luu', 'Lưu biên nhận')),
          lienKetNhan() ? h('a', {class: 'bn6-vien', id: 'nut-nhan', href: lienKetNhan(), rel: 'noopener noreferrer', onClick: chepMa}, chu('bn684_nhan_tiem', 'Nhắn The Vagabond')) : null]),
        lienKetNhan() ? h('p', {class: 'bn6-phu in-an'}, chu('bn684_nhan_kem_ma', 'Bấm Nhắn The Vagabond, mã đơn được chép sẵn để quý khách dán vào tin nhắn.')) : null,
        /* Nút Nhắn Zalo, Messenger, Gọi giữ làm phụ (hỗ trợ), nhãn Editor như cũ. */
        (D.lien_he || []).length ? h('p', {class:'bn-luu-y in-an'}, chu('bien_nhan_tt_ho_tro', 'Cần hỗ trợ thanh toán? Quý khách nhắn hoặc gọi The Vagabond:')) : null,
        h('div', {class:'bn-nut in-an'}, [
          ...(D.lien_he || []).map(a => h('a', {class:a.lop === 'phu' ? 'nut phu' : 'nut',href:a.href,rel:'noopener noreferrer'},a.khoa ? chu(a.khoa, a.ten) : a.ten)),
          h('a', {class:'nut chinh', href:D.trang_chu || '/web_moi/banh'}, chu('bien_nhan_3f197d985','Đặt thêm bánh'))])
      ])]);
    }
  };
}
export function khoiDongTrang(D, goc = '#app') {
  return createApp(taoTrang(D)).mount(goc);
}

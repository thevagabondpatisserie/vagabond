import {createApp, h, reactive} from '../lib/vue.esm-browser.prod.js';
import {ghi as ghiMang} from '../kho/api.js';

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
    st.loiThe = String(cau || chu('bien_nhan_tt_loi_the', 'Chưa tạo được giao dịch thẻ. Quý khách thử lại sau ít phút hoặc nhắn chúng tôi.'));
    st.dangTra = false;
  }
  async function chepNoiDung() {
    const nd = st.tt && st.tt.ck && st.tt.ck.noi_dung;
    if (!nd) return;
    try { await chep(nd); st.daChep = true; } catch (_) { st.daChep = false; }
  }
  function khoiThanhToan() {
    const k = st.tt;
    if (!k || !k.trang_thai || k.trang_thai === 'huy') return null;
    const con = [h('h2', chu('bien_nhan_tt_tieu_de', 'Thanh toán'))];
    if (k.trang_thai === 'tien_mat') {
      con.push(h('p', chu('bien_nhan_tt_tien_mat', 'Quý khách thanh toán tiền mặt khi nhận bánh.')));
    } else if (k.trang_thai === 'da_thu') {
      con.push(h('p', {class: 'bn-tt-ok', role: 'status'}, [h('b', chu('bien_nhan_tt_da_nhan', 'Đã nhận tiền')),
        [k.da_thu_chu, k.cach_thu].filter(Boolean).join(' · ')]));
    } else {
      if (k.trang_thai === 'thieu') con.push(h('p', {class: 'bn-tt-thieu'}, chu('bien_nhan_tt_thieu', 'Đã nhận một phần, còn thiếu') + ' ' + (k.con_chu || '')));
      if (k.the) {
        con.push(h('p', {class: 'bn-tt-so'}, [chu('bien_nhan_tt_so_the', 'Số tiền thanh toán'), h('b', k.con_chu)]));
        con.push(h('button', {type: 'button', class: 'nut chinh', id: 'nut-the', disabled: st.dangTra, onClick: traThe},
          st.dangTra ? chu('bien_nhan_tt_dang_chuyen', 'Đang chuyển sang OnePay...') : chu('bien_nhan_tt_the_nut', 'Thanh toán bằng thẻ')));
        con.push(h('p', {class: 'bn-tt-phu'}, chu('bien_nhan_tt_the_mo', 'Quý khách được chuyển sang trang bảo mật của OnePay để nhập thẻ và mã OTP.')));
        if (st.loiThe) con.push(h('p', {class: 'bn-tt-thieu', role: 'status'}, st.loiThe));
      } else if (k.ck) {
        const ck = k.ck;
        if (k.the_tat) con.push(h('p', {class: 'bn-tt-phu'}, chu('bien_nhan_tt_the_tat', 'Thanh toán thẻ đang tạm ngưng. Quý khách chuyển khoản theo mã dưới đây.')));
        con.push(h('p', {class: 'bn-tt-so'}, [chu('bien_nhan_tt_so_ck', 'Số tiền chuyển khoản'), h('b', k.con_chu)]));
        if (RE_ANH_QR.test(String(ck.anh || ''))) con.push(h('img', {class: 'bn-tt-qr', src: ck.anh, alt: 'VietQR', width: 220, height: 220}));
        con.push(h('dl', {class: 'bn-dong'}, [
          dong(chu('bien_nhan_tt_ngan_hang', 'Ngân hàng'), ck.ngan_hang), dong(chu('bien_nhan_tt_stk', 'Số tài khoản'), ck.stk),
          dong(chu('bien_nhan_tt_chu_tk', 'Chủ tài khoản'), ck.ten), dong(chu('bien_nhan_tt_noi_dung', 'Nội dung chuyển khoản'), ck.noi_dung)]));
        con.push(h('button', {type: 'button', class: 'nut phu', id: 'nut-chep', onClick: chepNoiDung},
          st.daChep ? chu('bien_nhan_tt_da_chep', 'Đã chép nội dung') : chu('bien_nhan_tt_chep', 'Chép nội dung')));
        con.push(h('p', {class: 'bn-tt-phu'}, chu('bien_nhan_tt_quet', 'Quét mã bằng ứng dụng ngân hàng, giữ nguyên nội dung. Hệ thống tự xác nhận khi tiền về, quý khách không cần nhắn lại.')));
        if (token) con.push(h('p', {class: 'bn-tt-phu', role: 'status'}, chu('bien_nhan_tt_cho_tien', 'Đang chờ tiền về...')));
      }
      if (k.phi_sau) con.push(h('p', {class: 'bn-tt-phu'}, chu('bien_nhan_tt_phi_sau', 'Số này là tiền bánh. Phí giao quý khách trả khi nhận bánh.')));
    }
    return h('section', {class: 'bn-tt', id: 'bn-tt'}, con);
  }

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
        h('h1', chu('bien_nhan_37a6f269e', 'Biên nhận chỉ mở được từ đường dẫn chúng tôi hiện ngay sau khi đặt.')),
        h('p', {class:'bn-cau'}, chu('bien_nhan_bbd687e19', 'Quý khách xem lại mã yêu cầu trong tin nhắn của chúng tôi, hoặc nhắn chúng tôi qua Zalo, Messenger ở cuối trang.')),
        h('div', {class:'bn-nut'}, [h('a', {class:'nut chinh', href:D.trang_chu || '/web_moi/banh'}, chu('bien_nhan_6be58a5f5', 'Về trang đặt bánh'))])])]);
      const tt = bn.dang_xac_nhan ? 'cho' : (bn.da_huy ? 'huy' : 'nhan');
      const cau = {cho:'Chúng tôi đã tiếp nhận yêu cầu và đang kiểm tra. Quý khách không cần đặt lại.',
        huy:'Đơn này đã được huỷ. Quý khách có thể đặt đơn mới hoặc liên hệ để được hỗ trợ.',
        nhan:'Chúng tôi đã nhận đơn. Nhân viên sẽ liên hệ xác nhận đơn.'};
      const lienHe = D.lien_he || [];
      return h('main', {class:'bn'}, [h('div', {class:'bn-in'}, [
        h('p', {class:'bn-nhan'}, chu('bien_nhan_ee537c03e','ĐÃ TIẾP NHẬN YÊU CẦU')),
        h('h1', [chu('bien_nhan_65781f4fe','Mã yêu cầu '), h('b', bn.ma)]),
        h('p', {class:'bn-trang-thai ' + tt}, chu('bien_nhan_tt_'+tt, {cho:'Đang xác nhận',huy:'Đã huỷ',nhan:'Đã nhận'}[tt])),
        h('p', {class:'bn-cau'}, chu('bien_nhan_'+tt,cau[tt])),
        h('dl', {class:'bn-dong'}, [
          bn.ten ? dong(chu('bien_nhan_bd76ef893','Người đặt'), bn.ten) : null,
          dong(chu('bien_nhan_c3baf86a6','Nhận bánh'), [bn.ngay_nhan,bn.khung_gio].filter(Boolean).join(' · ')),
          dong(chu('bien_nhan_d5ba29353','Cách nhận'), giaTri(bn.cach_nhan)),
          dong(chu('bien_nhan_9d5a6614c','Thanh toán'), giaTri(bn.thanh_toan))]),
        h('ul', {class:'bn-mon'}, (bn.mon || []).map(m => h('li', [h('span', m.ten), h('b', 'x'+m.sl), h('span',{class:'tien'},m.thanh_tien)]))),
        h('dl', {class:'bn-tien'}, [dong(chu('bien_nhan_ea3b9f8b1','Tiền bánh'), bn.tien_banh),
          bn.giam ? dong(chu('bien_nhan_uu_dai','Ưu đãi') + (bn.uu_dai ? ' ('+bn.uu_dai+')' : ''), bn.giam) : null,
          dong(chu('bien_nhan_06a446f5c','Phí giao'), giaTri(bn.phi_giao)), dong(chu('bien_nhan_de995d836','Tổng'), giaTri(bn.tong), 'tong')]),
        khoiThanhToan(),
        ...veBanner(D.banner),
        /* Nút Nhắn Zalo, Messenger, Gọi giữ làm phụ (hỗ trợ), không còn là bước bắt buộc. */
        lienHe.length ? h('p', {class:'bn-luu-y'}, chu('bien_nhan_tt_ho_tro', 'Cần hỗ trợ thanh toán? Quý khách nhắn hoặc gọi chúng tôi:')) : null,
        h('div', {class:'bn-nut'}, [
          ...lienHe.map(a => h('a', {class:a.lop === 'phu' ? 'nut phu' : 'nut',href:a.href,rel:'noopener noreferrer'},a.khoa ? chu(a.khoa, a.ten) : a.ten)),
          h('a', {class:'nut chinh', href:D.trang_chu || '/web_moi/banh'}, chu('bien_nhan_3f197d985','Đặt thêm bánh'))])
      ])]);
    }
  };
}
export function khoiDongTrang(D, goc = '#app') {
  return createApp(taoTrang(D)).mount(goc);
}

import {createApp, h} from '../lib/vue.esm-browser.prod.js';

// Chỉ dựng thẻ được máy chủ làm sạch, chữ là text node, không thành template.
export function veCay(cay) {
  return (cay || []).map(n => typeof n === 'string' ? n : h(n.tag, n.props || {}, veCay(n.con)));
}
export function bienNhan(D, win = window) {
  const key = 'vgb_bien_nhan_vue';
  const doc = k => { try { return win.sessionStorage.getItem(k); } catch (_) { return null; } };
  const ghi = (k,v) => { try { win.sessionStorage.setItem(k,v); } catch (_) {} };
  // Gỡ token TRƯỚC Pixel. Nếu không gỡ được thì không tải Pixel.
  let anToan = false;
  try {
    win.history.replaceState(null, '', win.location.pathname.replace(/\/xong\/[^/]+$/, '/xong'));
    anToan = !/\/xong\//.test(win.location.pathname);
  } catch (_) {}
  if (D.khong_token) {
    try { return JSON.parse(doc(key) || 'null'); } catch (_) { return null; }
  }
  const bn = D.bien_nhan;
  if (bn) ghi(key, JSON.stringify(bn));
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
export function khoiDongTrang(D, goc = '#app') {
  const bn = D.loai === 'bien_nhan' ? bienNhan(D) : null;
  const chu = (k, macDinh) => (D.nhan || {})[k] || macDinh;
  const dong = (nhan, gia, lop = '') => h('div', {class:lop}, [h('dt', nhan), h('dd', gia || '')]);
  return createApp({render() {
    if (D.loai === 'chinh_sach') return h('main', {class: 'cs'}, [h('article', {class:'cs-in'}, [
      h('h1', D.ten), h('p', {class:'cs-mo'}, D.mo || ''), ...veCay(D.cay)])]);
    if (!bn) return h('main', {class:'bn'}, [h('p', 'Biên nhận chỉ mở được từ đường dẫn sau khi đặt bánh.'),
      h('a', {href:'/web_moi/banh'}, chu('bien_nhan_3f197d985', 'Đặt thêm bánh'))]);
    const tt = bn.dang_xac_nhan ? 'cho' : (bn.da_huy ? 'huy' : 'nhan');
    const cau = {cho:'Chúng tôi đã tiếp nhận yêu cầu và đang kiểm tra. Quý khách không cần đặt lại.',
      huy:'Đơn này đã được huỷ. Quý khách có thể đặt đơn mới hoặc liên hệ để được hỗ trợ.',
      nhan:'Chúng tôi đã nhận đơn. Nhân viên sẽ liên hệ xác nhận và hướng dẫn thanh toán.'};
    return h('main', {class:'bn'}, [h('div', {class:'bn-in'}, [
      h('p', {class:'bn-nhan'}, chu('bien_nhan_ee537c03e','ĐÃ TIẾP NHẬN YÊU CẦU')),
      h('h1', [chu('bien_nhan_65781f4fe','Mã yêu cầu '), h('b', bn.ma)]),
      h('p', {class:'bn-trang-thai ' + tt}, chu('bien_nhan_tt_'+tt, {cho:'Đang xác nhận',huy:'Đã huỷ',nhan:'Đã nhận'}[tt])),
      h('p', {class:'bn-cau'}, chu('bien_nhan_'+tt,cau[tt])),
      h('dl', {class:'bn-dong'}, [
        bn.ten ? dong(chu('bien_nhan_bd76ef893','Người đặt'), bn.ten) : null,
        dong(chu('bien_nhan_c3baf86a6','Nhận bánh'), [bn.ngay_nhan,bn.khung_gio].filter(Boolean).join(' · ')),
        dong(chu('bien_nhan_d5ba29353','Cách nhận'), bn.cach_nhan),
        dong(chu('bien_nhan_9d5a6614c','Thanh toán'), bn.thanh_toan)]),
      h('ul', {class:'bn-mon'}, (bn.mon || []).map(m => h('li', [h('span', m.ten), h('b', 'x'+m.sl), h('span',{class:'tien'},m.thanh_tien)]))),
      h('dl', {class:'bn-tien'}, [dong(chu('bien_nhan_ea3b9f8b1','Tiền bánh'), bn.tien_banh),
        bn.giam ? dong(chu('bien_nhan_uu_dai','Ưu đãi') + (bn.uu_dai ? ' ('+bn.uu_dai+')' : ''), bn.giam) : null,
        dong(chu('bien_nhan_06a446f5c','Phí giao'), bn.phi_giao), dong(chu('bien_nhan_de995d836','Tổng'), bn.tong, 'tong')]),
      h('p', {class:'bn-luu-y'}, chu('bien_nhan_0ea4a5a10','Chúng tôi chưa thu tiền ở bước này. Chúng tôi sẽ gọi xác nhận rồi gửi hướng dẫn thanh toán.')),
      h('div', {class:'bn-nut'}, [
        ...(D.lien_he || []).map(a => h('a', {class:'nut',href:a.href,rel:'noopener noreferrer'},a.khoa ? chu(a.khoa, a.ten) : a.ten)),
        h('a', {class:'nut chinh', href:'/web_moi/banh'}, chu('bien_nhan_3f197d985','Đặt thêm bánh'))])
    ])]);
  }}).mount(goc);
}

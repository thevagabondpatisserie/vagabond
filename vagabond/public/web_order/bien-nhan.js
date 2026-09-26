/* #367: trang biên nhận đặt bánh.

   VIỆC ĐẦU TIÊN là gỡ token khỏi đường dẫn, TRƯỚC khi nạp Meta Pixel: Pixel
   tự gửi địa chỉ trang trong sự kiện PageView, để token trên đó là giao chìa
   khoá biên nhận của khách cho một bên thứ ba. Dữ liệu biên nhận giữ trong
   bộ nhớ phiên của chính tab này, nên khách tải lại trang vẫn thấy.

   Sự kiện GuiDon chỉ bắn MỘT lần cho một event_id (cờ trong bộ nhớ phiên).
   Máy chủ gửi cùng event_id qua Conversions API; Meta tự khử trùng. */
(function () {
  'use strict';
  var D = window.VGB_BIEN_NHAN || {};
  var KHOA = 'vgb_bien_nhan';
  function doc(k) { try { return window.sessionStorage.getItem(k); } catch (e) { return null; } }
  function ghi(k, v) { try { window.sessionStorage.setItem(k, v); } catch (e) { /* che do rieng tu */ } }

  try {
    if (/^\/banh\/xong\/./.test(window.location.pathname)) window.history.replaceState(null, '', '/banh/xong');
  } catch (e) { /* trinh duyet cu */ }

  var o = document.getElementById('bien-nhan');
  if (D.khong_token) {
    var cu = doc(KHOA);
    if (o) {
      o.innerHTML = cu || ('<main class="bn"><div class="bn-in"><p class="bn-nhan">BIÊN NHẬN</p>'
        + '<h1>Biên nhận chỉ mở được từ đường dẫn tiệm hiện ngay sau khi đặt.</h1>'
        + '<p class="bn-cau">Anh chị xem lại mã yêu cầu trong tin nhắn của tiệm, hoặc nhắn tiệm qua Zalo, Messenger ở cuối trang.</p>'
        + '<div class="bn-nut"><a class="nut chinh" href="/banh">Về trang đặt bánh</a></div></div></main>');
    }
    return;
  }
  if (D.than) ghi(KHOA, D.than);

  var px = String(D.pixel_id || '').replace(/\D/g, '');
  var ev = D.su_kien || {};
  if (!px) return;
  /* Doan nap chuan cua Meta, viet lai cho doc duoc. */
  if (!window.fbq) {
    var n = window.fbq = function () { n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments); };
    if (!window._fbq) window._fbq = n;
    n.push = n; n.loaded = true; n.version = '2.0'; n.queue = [];
    var t = document.createElement('script'); t.async = true; t.src = 'https://connect.facebook.net/en_US/fbevents.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(t, s);
  }
  window.fbq('init', px);
  window.fbq('track', 'PageView');
  if (ev.ban && ev.event_id && !doc('vgb_ev_' + ev.event_id)) {
    window.fbq('trackCustom', 'GuiDon',
      {value: Number(ev.gia_tri) || 0, currency: 'VND', content_ids: ev.ma_mon || [], content_type: 'product'},
      {eventID: String(ev.event_id)});
    ghi('vgb_ev_' + ev.event_id, '1');
  }
}());

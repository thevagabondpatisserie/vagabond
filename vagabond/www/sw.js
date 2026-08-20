/* Service Worker cua app Vagabond.

   VI SAO TEP NAY NAM O vagabond/www/ CHU KHONG PHAI vagabond/public/
   -------------------------------------------------------------------
   Pham vi cua mot Service Worker bi gioi han boi CHINH duong dan cua no.
   De o /assets/vagabond/sw.js thi no chi dieu khien duoc /assets/vagabond/...,
   tuc la khong dieu khien duoc /bep - dung cai trang minh can.

   Frappe phuc vu thu muc www/ ngay tai goc site, nen tep nay ra
   https://<site>/sw.js va co pham vi toan bo site. Day la cach duy nhat lam
   duoc ma van giu ma nguon trong git (khong dung Client Script tren co so
   du lieu, xem quy tac cua du an).

   TEP NAY CO Y KHONG LAM BO NHO DEM
   ---------------------------------
   Chi lam mot viec: nhan thong bao day. Bo nho dem ngoai tuyen cho mot app
   ke toan la con dao hai luoi - nhan vien mo app ra thay so lieu cu ma
   tuong la so moi thi nguy hon han viec khong mo duoc app.
*/

self.addEventListener('install', function (e) {
  /* Nhan quyen dieu khien ngay, khong doi tab cu dong het. */
  self.skipWaiting();
});

self.addEventListener('activate', function (e) {
  e.waitUntil(self.clients.claim());
});

self.addEventListener('push', function (e) {
  var d = {};
  try { d = e.data ? e.data.json() : {}; } catch (err) { d = { than: e.data ? e.data.text() : '' }; }
  var tieu = d.tieu_de || 'Vagabond';
  var tuy = {
    body: d.than || '',
    icon: '/assets/vagabond/pwa/icon-192.png',
    badge: '/assets/vagabond/pwa/icon-192.png',
    /* Rung dien thoai nhu anh Viet yeu cau. */
    vibrate: [200, 100, 200],
    tag: d.tag || 'vagabond',
    renotify: true,
    data: { url: d.duong_dan || '/bep' }
  };
  e.waitUntil(self.registration.showNotification(tieu, tuy));
});

self.addEventListener('notificationclick', function (e) {
  e.notification.close();
  var u = (e.notification.data && e.notification.data.url) || '/bep';
  e.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (ds) {
      /* Da mo app roi thi dua tab do len, khong mo them tab thu hai. */
      for (var i = 0; i < ds.length; i++) {
        if (ds[i].url.indexOf('/bep') >= 0 && 'focus' in ds[i]) return ds[i].focus();
      }
      if (self.clients.openWindow) return self.clients.openWindow(u);
    })
  );
});

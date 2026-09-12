/* #245: renderer dùng chung cho trang khách và preview của marketing.
   textContent giữ nội dung người soạn là chữ, không trở thành HTML/JS. */
(function () {
  'use strict';
  function tao(the, lop, chu) {
    const e = document.createElement(the);
    if (lop) e.className = lop;
    if (chu) e.textContent = chu;
    return e;
  }
  function ve(goc, duLieu) {
    goc.replaceChildren();
    (duLieu.khoi || []).filter(k => k.hien).forEach(k => {
      const khung = tao('section', 'web-khoi web-' + k.loai);
      khung.dataset.khoi = k.id;
      if (k.anh) {
        const anh = tao('img', 'web-anh');
        anh.src = k.anh; anh.alt = k.mo_ta_anh || '';
        anh.loading = k.loai === 'anh_bia' ? 'eager' : 'lazy';
        khung.append(anh);
      }
      const chu = tao('div', 'web-chu');
      chu.append(tao('p', 'web-nhan', k.nhan), tao('h2', 'web-tieu-de', k.tieu_de), tao('p', 'web-doan', k.noi_dung));
      if (k.nut && k.lien_ket) {
        const nut = tao('a', 'web-nut', k.nut); nut.href = k.lien_ket;
        chu.append(nut);
      }
      khung.append(chu); goc.append(khung);
    });
  }
  window.VgbKhoi = {ve};
}());

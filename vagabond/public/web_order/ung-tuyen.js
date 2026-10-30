/* v622: form ứng tuyển của mục Tuyển dụng trên web (anh Việt 30/10/2026).
   Vị trí lấy thẳng từ app (vagabond.tuyen_dung.vi_tri_cong_khai); bật tắt trên
   app là trang này đổi theo. Gửi lại cùng một mã lần gửi khi mất mạng, máy chủ
   trả kết quả cũ chứ không tạo hồ sơ thứ hai (khuôn trang đặt bàn). */
(async function () {
  'use strict';
  const tim = id => document.getElementById(id);
  const ma = (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : 'xxxxxxxx-xxxx-4xxx-8xxx-xxxxxxxxxxxx'.replace(/x/g, () => (Math.random() * 16 | 0).toString(16));
  const thamSo = new URLSearchParams(location.search);
  const nguon = thamSo.get('nguon') === 'qr' ? 'QR tại cửa hàng' : 'Web Vagabond';
  let dsViTri = [], viTri = '', ca = [], dangGui = false, hoSo = null;
  const nutGui = tim('gui').textContent;

  function bao(chu, loi) {
    const o = tim('trang-thai'); o.textContent = chu; o.classList.toggle('loi', !!loi);
    if (loi && o.scrollIntoView) o.scrollIntoView({block: 'center', behavior: 'smooth'});
  }
  function chonViTri(ten) {
    viTri = ten;
    tim('vi-tri').querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.vt === ten)));
    const v = dsViTri.find(x => x.lien_ket.split('vt=')[1] === ten);
    tim('vt-chi-tiet').textContent = v ? [v.noi_dung, v.yeu_cau].filter(Boolean).join('\n') : '';
  }
  function veViTri() {
    const khung = tim('vi-tri'); khung.replaceChildren();
    dsViTri.forEach(v => {
      const ten = v.lien_ket.split('vt=')[1];
      const b = document.createElement('button'); b.type = 'button'; b.className = 'vt-the'; b.dataset.vt = ten;
      b.setAttribute('aria-pressed', 'false');
      const tenVt = document.createElement('span'); tenVt.textContent = v.tieu_de;
      const phu = document.createElement('small');
      phu.textContent = [v.noi_lam, v.hinh_thuc, v.ket_thuc ? 'hạn ' + v.ket_thuc.split('-').reverse().join('/') : 'nhận tới khi đủ người'].filter(Boolean).join(' · ');
      b.append(tenVt, phu);
      b.onclick = () => chonViTri(ten);
      khung.append(b);
    });
  }
  function veCa(ds) {
    ds.forEach(c => {
      const b = document.createElement('button'); b.type = 'button'; b.textContent = c; b.setAttribute('aria-pressed', 'false');
      b.onclick = () => {
        const co = ca.indexOf(c) >= 0;
        ca = co ? ca.filter(x => x !== c) : ca.concat([c]);
        b.setAttribute('aria-pressed', String(!co));
      };
      tim('ca-ranh').append(b);
    });
  }

  try {
    const r = await fetch('/api/method/vagabond.tuyen_dung.vi_tri_cong_khai', {credentials: 'same-origin'});
    const d = await r.json();
    if (!r.ok || !d.message) throw new Error();
    dsViTri = d.message.vi_tri || [];
    tim('cau-dong-y').textContent = d.message.cau_dong_y || '';
    if (!dsViTri.length) {
      bao('Hiện chưa có vị trí nào đang tuyển. Bạn quay lại sau hoặc gọi cho chúng tôi nhé.');
      return;
    }
    veViTri(); veCa(d.message.ca_ranh || []);
    const muon = thamSo.get('vt');
    if (muon && dsViTri.some(v => v.lien_ket.split('vt=')[1] === muon)) chonViTri(muon);
    else if (dsViTri.length === 1) chonViTri(dsViTri[0].lien_ket.split('vt=')[1]);
    else if (muon) bao('Vị trí bạn mở đã ngừng nhận hồ sơ. Chọn một vị trí khác đang tuyển bên dưới.', true);
    tim('ung-tuyen').hidden = false;
    if (!muon || dsViTri.some(v => v.lien_ket.split('vt=')[1] === muon)) bao('');
  } catch (_) {
    bao('Chưa tải được danh sách vị trí. Tải lại trang hoặc gọi cho chúng tôi.', true);
    return;
  }

  tim('ung-tuyen').onsubmit = async e => {
    e.preventDefault();
    if (dangGui) return;
    if (!viTri) { bao('Chọn vị trí bạn muốn ứng tuyển.', true); return; }
    if (!tim('ho-ten').value.trim() || !tim('sdt').value.trim()) { bao('Điền họ tên và số điện thoại để chúng tôi gọi lại.', true); return; }
    if (!tim('dong-y').checked) { bao('Tích ô đồng ý lưu hồ sơ để gửi.', true); return; }
    if (!hoSo) {
      hoSo = {vi_tri: viTri, ho_ten: tim('ho-ten').value, sdt: tim('sdt').value, email: tim('email').value,
        khu_vuc: tim('khu-vuc').value, ca_ranh: ca.slice(), kinh_nghiem: tim('kinh-nghiem').value,
        gioi_thieu: tim('gioi-thieu').value, lien_ket_cv: tim('cv').value.trim(),
        nguoi_gioi_thieu: tim('gioi-thieu-boi').value, nguon: nguon, dong_y: 1, web: tim('web').value};
    }
    dangGui = true; tim('gui').disabled = true;
    tim('ung-tuyen').querySelectorAll('input,textarea,button').forEach(x => { x.disabled = true; });
    bao('Đang gửi hồ sơ...');
    try {
      const m = document.querySelector('meta[name=csrf-token]');
      const r = await fetch('/api/method/vagabond.tuyen_dung.ung_tuyen', {method: 'POST', credentials: 'same-origin',
        headers: {'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': m ? m.content : ''},
        body: JSON.stringify({du_lieu: hoSo, ma_lan_gui: ma})});
      let d = {};
      try { d = await r.json(); } catch (_) { /* phản hồi không phải JSON: dùng câu chung */ }
      if (!r.ok || !(d.message && d.message.ok)) {
        if (r.status >= 400 && r.status < 500 && r.status !== 408) {
          /* Lỗi dữ liệu: mở lại form để sửa, lần gửi sau lấy dữ liệu mới. */
          hoSo = null;
          let chu = 'Kiểm tra lại thông tin hoặc chờ vài phút rồi gửi lại.';
          try { chu = JSON.parse(d._server_messages || '[]').map(x => JSON.parse(x).message).join(' ') || chu; } catch (_) { /* giữ câu chung */ }
          throw new Error(chu);
        }
        throw new Error('Chưa nhận được kết quả. Bấm Gửi lại để kiểm tra, không cần nhập lại.');
      }
      tim('ung-tuyen').hidden = true;
      bao('Đã nhận hồ sơ ' + d.message.ma + '. Cảm ơn bạn, quản lý bộ phận sẽ gọi lại cho bạn sớm.');
    } catch (err) {
      bao(err.message === 'Failed to fetch' ? 'Mất kết nối. Bấm Gửi lại để kiểm tra, không cần nhập lại.' : err.message, true);
      tim('gui').textContent = hoSo ? 'Gửi lại' : nutGui;
      tim('ung-tuyen').querySelectorAll('input,textarea,button').forEach(x => { x.disabled = !!hoSo && x.id !== 'gui'; });
    } finally {
      dangGui = false; tim('gui').disabled = false;
    }
  };
})();

/* v625: form ứng tuyển 3 bước (anh Việt 31/10/2026, duyệt mẫu 3).

   Câu hỏi KHÔNG chép cứng ở đây: trang đọc danh sách câu từ máy chủ
   (vagabond.tuyen_dung.vi_tri_cong_khai), nơi Minh Vũ sửa trong trình biên tập
   web. Mặc định là 14 câu của form Lark. Vị trí lấy thẳng từ app; câu nào chỉ
   hỏi ở vài vị trí thì đổi vị trí là danh sách câu đổi theo.

   Giữ ba điều của v622: bắt buộc tích đồng ý lưu hồ sơ; mất mạng thì gửi lại
   CÙNG mã lần gửi, máy chủ trả kết quả cũ chứ không tạo hồ sơ thứ hai; ô bẫy
   cho máy tự điền. CV chọn là tải lên ngay (vagabond.tuyen_dung.tai_cv), gửi
   hồ sơ chỉ mang mã tạm của tệp. */
(async function () {
  'use strict';
  const tim = id => document.getElementById(id);
  const ma = (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : 'xxxxxxxx-xxxx-4xxx-8xxx-xxxxxxxxxxxx'.replace(/x/g, () => (Math.random() * 16 | 0).toString(16));
  const thamSo = new URLSearchParams(location.search);
  const nguon = thamSo.get('nguon') === 'qr' ? 'QR tại cửa hàng' : 'Web Vagabond';
  let dsViTri = [], cauHoi = [], tenBuoc = {}, viTri = '', buoc = 0, dangGui = false, hoSo = null, cvToiDa = 8;
  const tl = {};          /* câu trả lời theo mã câu */
  const khac = {};        /* câu chọn một đang mở ô "Khác" */
  let cv = null;          /* {ma_cv, ten, kb} sau khi tải lên */
  let dangTaiCv = false;

  const maVt = v => String(v.ma || (v.lien_ket || '').split('vt=')[1] || '');
  const tao = (t, lop, chu) => { const e = document.createElement(t); if (lop) e.className = lop; if (chu != null) e.textContent = chu; return e; };
  const chamNghin = s => String(s || '').replace(/[^0-9]/g, '').replace(/^0+(?=\d)/, '').replace(/\B(?=(\d{3})+(?!\d))/g, '.');

  function bao(chu, loi) {
    const o = tim('trang-thai'); o.textContent = chu; o.classList.toggle('loi', !!loi);
    if (loi && o.scrollIntoView) o.scrollIntoView({block: 'center', behavior: 'smooth'});
  }
  function vtDangChon() { return dsViTri.find(v => maVt(v) === viTri) || null; }
  /* Câu áp cho vị trí đang chọn (câu không giới hạn vị trí áp mọi vị trí). */
  function cauApDung() { return cauHoi.filter(c => !(c.vi_tri || []).length || (viTri && c.vi_tri.indexOf(viTri) >= 0)); }
  function cacBuoc() { return [...new Set(cauApDung().map(c => +c.buoc || 1))].sort((a, b) => a - b); }

  /* ---------------- vẽ một câu ---------------- */
  function oChu(c, kieu, thuoc) {
    const i = tao(kieu === 'doan' ? 'textarea' : 'input');
    if (kieu !== 'doan') i.type = thuoc.type || 'text';
    Object.keys(thuoc).forEach(k => { if (k !== 'type') i.setAttribute(k, thuoc[k]); });
    i.value = tl[c.ma] == null ? '' : tl[c.ma];
    i.oninput = () => { tl[c.ma] = i.value; };
    return i;
  }
  function chip(chu, bat, bam) {
    const b = tao('button', '', chu); b.type = 'button'; b.setAttribute('aria-pressed', String(!!bat)); b.onclick = bam; return b;
  }
  function veCau(c) {
    const khung = tao('div', 'ut-cau'); khung.dataset.ma = c.ma;
    const nhan = tao('p', 'ut-hoi', c.hoi); if (c.bat_buoc) nhan.append(tao('em', '', ' *'));
    khung.append(nhan);
    const vt = vtDangChon();
    let goiY = c.goi_y || '';
    if (c.loai === 'so_tien' && vt && vt.luong_gon) goiY = 'Vị trí này ' + vt.luong_gon.charAt(0).toLowerCase() + vt.luong_gon.slice(1) + '. ' + goiY;
    if (goiY) khung.append(tao('p', 'ut-goi', goiY));
    if (c.loai === 'chu') khung.append(oChu(c, 'chu', {maxlength: 300, autocomplete: c.ma === 'ho_ten' ? 'name' : 'off'}));
    else if (c.loai === 'doan') khung.append(oChu(c, 'doan', {maxlength: 1500}));
    else if (c.loai === 'so_dt') khung.append(oChu(c, 'chu', {type: 'tel', inputmode: 'tel', autocomplete: 'tel', maxlength: 20, placeholder: '0909 123 456'}));
    else if (c.loai === 'email') khung.append(oChu(c, 'chu', {type: 'email', autocomplete: 'email', maxlength: 140, placeholder: 'ten@email.com'}));
    else if (c.loai === 'so_tien') {
      const h = tao('div', 'ut-tien-o');
      const i = oChu(c, 'chu', {inputmode: 'numeric', maxlength: 16, placeholder: '9.000.000', 'aria-label': c.hoi});
      i.value = chamNghin(tl[c.ma]);
      i.oninput = () => { const ve = chamNghin(i.value); i.value = ve; tl[c.ma] = ve; };
      h.append(i, tao('span', '', 'đ / tháng')); khung.append(h);
    } else if (c.loai === 'ngay') {
      const g = String(tl[c.ma] || '').split('-');
      const h = tao('div', 'ut-ngay');
      const o = (ph, gt, dai) => { const i = tao('input'); i.setAttribute('inputmode', 'numeric'); i.setAttribute('placeholder', ph); i.setAttribute('maxlength', dai); i.setAttribute('aria-label', ph); i.value = gt || ''; return i; };
      const ngay = o('Ngày', g[2], 2), thang = o('Tháng', g[1], 2), nam = o('Năm', g[0], 4);
      const ghep = () => {
        const d = ngay.value.replace(/\D/g, ''), m = thang.value.replace(/\D/g, ''), y = nam.value.replace(/\D/g, '');
        tl[c.ma] = (d && m && y.length === 4) ? y + '-' + m.padStart(2, '0') + '-' + d.padStart(2, '0') : (d || m || y ? 'thieu' : '');
      };
      [ngay, thang, nam].forEach(i => { i.oninput = ghep; });
      h.append(ngay, thang, nam); khung.append(h);
    } else if (c.loai === 'chon_mot' || c.loai === 'chon_nhieu') {
      const h = tao('div', 'chips'); const nhieu = c.loai === 'chon_nhieu';
      const dang = () => nhieu ? (Array.isArray(tl[c.ma]) ? tl[c.ma] : []) : tl[c.ma];
      (c.lua_chon || []).forEach(x => h.append(chip(x, nhieu ? dang().indexOf(x) >= 0 : (dang() === x && !khac[c.ma]), () => {
        if (nhieu) { const d = dang(); tl[c.ma] = d.indexOf(x) >= 0 ? d.filter(y => y !== x) : d.concat([x]); }
        else { tl[c.ma] = x; khac[c.ma] = false; }
        veBuoc();
      })));
      if (!nhieu && c.cho_khac) {
        h.append(chip('Khác...', !!khac[c.ma], () => { khac[c.ma] = true; tl[c.ma] = ''; veBuoc(); }));
      }
      khung.append(h);
      if (khac[c.ma]) khung.append(oChu(c, 'chu', {maxlength: 100, placeholder: 'Ghi cụ thể', 'aria-label': 'Ghi cụ thể'}));
    } else if (c.loai === 'tep') {
      khung.append(veTep());
    } else if (c.loai === 'vi_tri') {
      const h = tao('div', 'ut-vts');
      dsViTri.forEach(v => {
        const b = tao('button', 'ut-vt-the'); b.type = 'button'; b.dataset.vt = maVt(v);
        b.setAttribute('aria-pressed', String(maVt(v) === viTri));
        b.append(tao('span', '', v.tieu_de), tao('small', '', [v.luong_gon, v.noi_lam, v.hinh_thuc].filter(Boolean).join(' · ')));
        b.onclick = () => { chonViTri(maVt(v)); veBuoc(); };
        h.append(b);
      });
      khung.append(h);
    }
    return khung;
  }

  function veTep() {
    const h = tao('div', 'ut-tep');
    const vao = tao('input'); vao.type = 'file'; vao.id = 'tep-cv'; vao.setAttribute('accept', 'application/pdf,image/jpeg,image/png'); vao.hidden = true;
    const nut = tao('button', 'ut-tai'); nut.type = 'button';
    nut.append(tao('span', 'ut-tai-ic', '⇪'), tao('b', '', cv ? 'Đổi tệp CV' : 'Chụp hoặc chọn tệp CV'),
      tao('small', '', 'PDF hoặc ảnh, tối đa ' + cvToiDa + ' MB. Không có cũng được.'));
    nut.onclick = () => vao.click();
    vao.onchange = () => { const f = vao.files && vao.files[0]; if (f) taiCv(f); };
    h.append(vao, nut);
    if (dangTaiCv) h.append(tao('p', 'ut-tep-dong', 'Đang tải CV lên...'));
    else if (cv) {
      const d = tao('p', 'ut-tep-dong'); d.append(tao('i', '', /\.pdf$/i.test(cv.ten) ? 'PDF' : 'ẢNH'), tao('span', '', cv.ten), tao('em', '', '✓ Đã tải lên'));
      h.append(d);
    }
    return h;
  }

  async function taiCv(f) {
    if (f.size > cvToiDa * 1024 * 1024) { bao('Tệp CV lớn hơn ' + cvToiDa + ' MB. Chọn tệp nhỏ hơn hoặc chụp ảnh CV.', true); return; }
    if (!/^(application\/pdf|image\/jpeg|image\/png)$/.test(f.type || '') && !/\.(pdf|jpe?g|png)$/i.test(f.name || '')) {
      bao('Chỉ nhận CV dạng PDF, JPG hoặc PNG.', true); return;
    }
    dangTaiCv = true; veBuoc();
    try {
      const fd = new FormData(); fd.append('tep', f, f.name || 'cv');
      const m = document.querySelector('meta[name=csrf-token]');
      const r = await fetch('/api/method/vagabond.tuyen_dung.tai_cv', {method: 'POST', credentials: 'same-origin',
        headers: {'X-Frappe-CSRF-Token': m ? m.content : ''}, body: fd});
      let d = {};
      try { d = await r.json(); } catch (_) { /* giữ câu chung */ }
      if (!r.ok || !(d.message && d.message.ma_cv)) {
        let chu = 'Chưa tải được CV. Thử lại hoặc gửi hồ sơ không kèm CV.';
        try { chu = JSON.parse(d._server_messages || '[]').map(x => JSON.parse(x).message).join(' ') || chu; } catch (_) { /* giữ câu chung */ }
        throw new Error(chu);
      }
      cv = {ma_cv: d.message.ma_cv, ten: d.message.ten || f.name || 'CV', kb: d.message.kb};
      hoSo = null; bao('');
    } catch (e) {
      bao(e.message === 'Failed to fetch' ? 'Mất kết nối khi tải CV. Chọn lại tệp để thử lại.' : e.message, true);
    } finally {
      dangTaiCv = false; veBuoc();
    }
  }

  function chonViTri(ten) {
    viTri = ten;
    const v = vtDangChon();
    tim('ten-vt').textContent = v ? v.tieu_de : 'Làm việc cùng Vagabond';
    const ds = cacBuoc();
    if (buoc >= ds.length) buoc = ds.length - 1;
  }

  /* ---------------- vẽ một bước ---------------- */
  function veBuoc() {
    const ds = cacBuoc(), so = ds[buoc], cuoi = buoc === ds.length - 1;
    const tien = tim('tien'); tien.replaceChildren();
    ds.forEach((_, k) => tien.append(tao('i', k <= buoc ? 'on' : '')));
    tim('buoc-nhan').textContent = 'BƯỚC ' + (buoc + 1) + ' / ' + ds.length;
    tim('buoc-ten').textContent = String(tenBuoc[so] || '').toUpperCase();
    tim('gioi-thieu').hidden = buoc !== 0 || !tim('gioi-thieu').textContent;
    const khung = tim('cau'); khung.replaceChildren();
    cauApDung().filter(c => (+c.buoc || 1) === so).forEach(c => khung.append(veCau(c)));
    tim('khung-dong-y').hidden = !cuoi;
    /* Lần gửi trước chưa rõ kết quả (mất mạng): khoá ô để lần Gửi lại mang ĐÚNG
       dữ liệu cũ; sửa được lại khi máy chủ trả lời (v622 giữ nguyên). */
    const khoa = !!hoSo;
    khung.querySelectorAll('input,textarea,button').forEach(x => { x.disabled = khoa; });
    tim('dong-y').disabled = khoa;
    tim('lui').hidden = buoc === 0 || khoa;
    tim('gui').textContent = cuoi ? (hoSo ? 'Gửi lại' : 'Gửi hồ sơ') : 'Tiếp tục →';
    tim('gui').disabled = dangTaiCv;
  }

  /* Kiểm nhanh ở máy khách để khỏi đi tới bước cuối mới biết thiếu; máy chủ vẫn là nơi quyết. */
  function thieuO(so) {
    for (const c of cauApDung().filter(x => (+x.buoc || 1) === so)) {
      const v = tl[c.ma];
      if (c.loai === 'vi_tri') { if (!viTri) return 'Chọn vị trí bạn muốn ứng tuyển.'; continue; }
      if (c.loai === 'tep') { if (c.bat_buoc && !cv) return 'Tải CV lên ở câu "' + c.hoi + '".'; continue; }
      if (c.loai === 'ngay' && v === 'thieu') return 'Câu "' + c.hoi + '": điền đủ ngày, tháng và năm (4 số).';
      const rong = v == null || (Array.isArray(v) ? !v.length : !String(v).trim());
      if (c.bat_buoc && rong) return 'Trả lời câu "' + c.hoi + '".';
      if (c.loai === 'email' && !rong && !/^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]{2,}$/.test(String(v).trim())) return 'Kiểm tra lại email, ví dụ ten@gmail.com.';
    }
    return '';
  }

  try {
    const r = await fetch('/api/method/vagabond.tuyen_dung.vi_tri_cong_khai', {credentials: 'same-origin'});
    const d = await r.json();
    if (!r.ok || !d.message) throw new Error();
    dsViTri = d.message.vi_tri || [];
    cauHoi = d.message.cau_hoi || [];
    tenBuoc = d.message.buoc || {1: 'Về bạn', 2: 'Kinh nghiệm', 3: 'Mong muốn'};
    cvToiDa = +d.message.cv_toi_da_mb || 8;
    tim('cau-dong-y').textContent = d.message.cau_dong_y || '';
    tim('gioi-thieu').textContent = d.message.gioi_thieu || '';
    if (!dsViTri.length || !cauHoi.length) {
      bao('Hiện chưa có vị trí nào đang tuyển. Bạn quay lại sau hoặc gọi cho chúng tôi nhé.');
      return;
    }
    const muon = thamSo.get('vt');
    if (muon && dsViTri.some(v => maVt(v) === muon)) chonViTri(muon);
    else if (dsViTri.length === 1) chonViTri(maVt(dsViTri[0]));
    tim('ung-tuyen').hidden = false;
    if (muon && !dsViTri.some(v => maVt(v) === muon)) bao('Vị trí bạn mở đã ngừng nhận hồ sơ. Chọn một vị trí khác đang tuyển ở bước 2.', true);
    else bao('');
    veBuoc();
  } catch (_) {
    bao('Chưa tải được danh sách vị trí. Tải lại trang hoặc gọi cho chúng tôi.', true);
    return;
  }

  tim('lui').onclick = () => { if (buoc > 0 && !dangGui) { buoc -= 1; bao(''); veBuoc(); if (window.scrollTo) window.scrollTo(0, 0); } };

  tim('ung-tuyen').onsubmit = async e => {
    e.preventDefault();
    if (dangGui || dangTaiCv) return;
    const ds = cacBuoc();
    const thieu = thieuO(ds[buoc]);
    if (thieu) { bao(thieu, true); return; }
    if (buoc < ds.length - 1) { buoc += 1; bao(''); veBuoc(); if (window.scrollTo) window.scrollTo(0, 0); return; }
    for (let k = 0; k < ds.length; k++) {
      const t = thieuO(ds[k]);
      if (t) { buoc = k; veBuoc(); bao(t, true); return; }
    }
    if (!tim('dong-y').checked) { bao('Tích ô đồng ý lưu hồ sơ để gửi.', true); return; }
    if (!hoSo) {
      const traLoi = {};
      cauApDung().forEach(c => {
        if (c.loai === 'vi_tri' || c.loai === 'tep' || tl[c.ma] == null) return;
        traLoi[c.ma] = c.loai === 'so_tien' ? String(tl[c.ma]).replace(/\./g, '') : tl[c.ma];
      });
      hoSo = {vi_tri: viTri, tra_loi: traLoi, ma_cv: cv ? cv.ma_cv : '', nguon: nguon, dong_y: 1, web: tim('web').value};
    }
    dangGui = true; tim('gui').disabled = true;
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
      tim('ung-tuyen').hidden = true; tim('tien').hidden = true;
      tim('xong').hidden = false;
      tim('xong-chu').textContent = 'Đã nhận hồ sơ ' + d.message.ma + '. Quản lý bộ phận sẽ gọi lại cho bạn sớm.';
      bao('');
      if (window.scrollTo) window.scrollTo(0, 0);
    } catch (err) {
      bao(err.message === 'Failed to fetch' ? 'Mất kết nối. Bấm Gửi lại để kiểm tra, không cần nhập lại.' : err.message, true);
    } finally {
      dangGui = false;
      if (!tim('ung-tuyen').hidden) veBuoc();
    }
  };
})();

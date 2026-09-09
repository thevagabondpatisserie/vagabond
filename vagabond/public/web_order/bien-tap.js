/* #245: bản nháp chỉ ra website sau hành động Xuất bản thành công. */
(function () {
  'use strict';
  const tim = id => document.getElementById(id);
  const tenLoai = {anh_bia: 'Ảnh bìa', cau_chuyen: 'Câu chuyện', anh_chu: 'Ảnh và chữ', thong_bao: 'Thông báo'};
  let bang, nhap, chon = '', doi = false, ban = false, keo = '';
  function tao(the, chu, lop) { const e = document.createElement(the); if (chu) e.textContent = chu; if (lop) e.className = lop; return e; }
  function bao(chu, loi) { tim('trang-thai').textContent = chu; tim('trang-thai').classList.toggle('loi', !!loi); }
  async function api(ham, duLieu) {
    const cau = {credentials: 'same-origin', headers: {Accept: 'application/json'}};
    if (duLieu) {
      cau.method = 'POST'; cau.headers['Content-Type'] = 'application/json';
      cau.headers['X-Frappe-CSRF-Token'] = document.querySelector('meta[name=csrf-token]').content;
      cau.body = JSON.stringify(duLieu);
    }
    const r = await fetch('/api/method/vagabond.noi_dung_web.' + ham, cau);
    const d = await r.json();
    if (!r.ok || d.exc) {
      let chu = 'Không lưu được. Giữ bản đang sửa và thử tải lại khi kết nối ổn định.';
      if (r.status === 403) chu = 'Phiên đăng nhập hết hạn hoặc tài khoản chưa có quyền Marketing. Đăng nhập lại để tiếp tục.';
      try { const thongBao = JSON.parse(d._server_messages || '[]').map(s => JSON.parse(s).message); if (thongBao.length) chu = thongBao.join(' '); } catch (_) { /* Giữ thông báo có hướng xử lý. */ }
      throw new Error(chu);
    }
    return d.message;
  }
  function khoa(b) { ban = b; ['luu-nhap', 'xuat-ban', 'tai-lai'].forEach(id => tim(id).disabled = b); tim('thuoc-tinh').inert = b; tim('danh-sach').inert = b; tim('them-khoi').inert = b; tim('lich-su').inert = b; }
  function thongKe() {
    tim('so-khoi').textContent = nhap.khoi.length;
    tim('so-hien').textContent = nhap.khoi.filter(k => k.hien).length;
    tim('phien-ban').textContent = bang.phien_ban;
    tim('tinh-trang').textContent = doi ? 'Chưa lưu' : JSON.stringify(nhap) === JSON.stringify(bang.cong_khai) ? 'Đã xuất bản' : 'Bản nháp';
  }
  function xem() {
    const d = tim('preview').contentDocument;
    if (!nhap || !d || !d.getElementById('khoi')) return;
    window.VgbKhoi.ve(d.getElementById('khoi'), nhap);
    d.querySelectorAll('a').forEach(a => a.addEventListener('click', e => e.preventDefault()));
  }
  function daDoi() { doi = true; thongKe(); xem(); }
  function doiCho(id, buoc) {
    if (ban) return;
    const i = nhap.khoi.findIndex(k => k.id === id), j = i + buoc;
    if (j < 0 || j >= nhap.khoi.length) return;
    [nhap.khoi[i], nhap.khoi[j]] = [nhap.khoi[j], nhap.khoi[i]];
    daDoi(); danhSach();
  }
  function danhSach() {
    const g = tim('danh-sach'); g.replaceChildren();
    if (!nhap.khoi.length) g.append(tao('p', 'Chưa có khối. Chọn một loại bên dưới để thêm.'));
    nhap.khoi.forEach((k, i) => {
      const dong = tao('div', '', 'dong-khoi' + (chon === k.id ? ' on' : '')); dong.draggable = true;
      const nut = tao('button', (i + 1) + '. ' + (k.tieu_de || tenLoai[k.loai]) + (k.hien ? '' : ' · Ẩn'), 'chon-khoi');
      nut.onclick = () => { chon = k.id; danhSach(); thuocTinh(); }; dong.append(nut);
      const ds = tao('div', '', 'sap-xep');
      [['↑', -1, 'Đưa khối lên'], ['↓', 1, 'Đưa khối xuống']].forEach(([chu, buoc, nhan]) => {
        const b = tao('button', chu); b.setAttribute('aria-label', nhan); b.disabled = i + buoc < 0 || i + buoc >= nhap.khoi.length;
        b.onclick = () => doiCho(k.id, buoc); ds.append(b);
      });
      const an = tao('button', k.hien ? 'Ẩn' : 'Hiện'); an.onclick = () => { k.hien = !k.hien; daDoi(); danhSach(); thuocTinh(); }; ds.append(an); dong.append(ds);
      dong.ondragstart = e => { keo = k.id; e.dataTransfer.setData('text/plain', k.id); };
      dong.ondragover = e => e.preventDefault();
      dong.ondrop = e => { e.preventDefault(); if (ban || !keo) return; const a = nhap.khoi.findIndex(x => x.id === keo); const b = nhap.khoi.findIndex(x => x.id === k.id); if (a >= 0 && b >= 0) { const [x] = nhap.khoi.splice(a, 1); nhap.khoi.splice(b, 0, x); daDoi(); danhSach(); } keo = ''; };
      dong.ondragend = () => { keo = ''; }; g.append(dong);
    });
  }
  function thuocTinh() {
    const g = tim('thuoc-tinh'); g.replaceChildren(); const k = nhap.khoi.find(x => x.id === chon);
    if (!k) { g.append(tao('p', 'Chọn một khối để chỉnh nội dung.')); return; }
    [['nhan','Dòng giới thiệu'],['tieu_de','Tiêu đề'],['noi_dung','Nội dung'],['anh','Đường dẫn ảnh công khai'],['mo_ta_anh','Mô tả ảnh'],['nut','Chữ trên nút'],['lien_ket','Liên kết của nút']].forEach(([ma, ten]) => {
      const nhan = tao('label', '', 'truong'); nhan.append(tao('span', ten));
      const o = tao(ma === 'noi_dung' || ma === 'tieu_de' ? 'textarea' : 'input');
      o.value = k[ma] || ''; o.maxLength = ma === 'noi_dung' ? 4000 : 1000;
      o.oninput = () => { k[ma] = o.value; daDoi(); }; o.onchange = () => danhSach();
      nhan.append(o); g.append(nhan);
    });
    const taiNhan = tao('label', '', 'truong'); taiNhan.append(tao('span', 'Tải ảnh từ máy (ảnh sẽ công khai)'));
    const tep = tao('input'); tep.type = 'file'; tep.accept = 'image/png,image/jpeg,image/webp';
    tep.onchange = async () => {
      if (!tep.files[0]) return;
      const f = tep.files[0]; if (f.size > 10 * 1024 * 1024) { bao('Chọn ảnh dưới 10 MB.', true); return; }
      khoa(true); bao('Đang tải ảnh...');
      try {
        const form = new FormData(); form.append('file', f);
        const r = await fetch('/api/method/vagabond.noi_dung_web.tai_anh', {method:'POST', credentials:'same-origin', headers:{'X-Frappe-CSRF-Token':document.querySelector('meta[name=csrf-token]').content}, body:form});
        const d = await r.json(); if (!r.ok || !d.message?.url) throw new Error('Không tải được ảnh. Kiểm tra quyền Marketing và định dạng PNG, JPG hoặc WebP.');
        k.anh = d.message.url; daDoi(); thuocTinh(); bao('Đã tải ảnh công khai. Lưu nháp hoặc xuất bản để gắn ảnh vào trang.');
      } catch(e) { bao(e.message, true); } finally { khoa(false); }
    };
    taiNhan.append(tep); g.append(taiNhan);
    g.append(tao('p', 'Ảnh: dán link HTTPS hoặc /files/ từ thư viện ảnh. Nút chọn bánh: #danh-muc-banh. Đặt trước: #/dat-truoc.', 'goi-y'));
    const nhan = tao('label', '', 'truong'), o = tao('input'); o.type = 'checkbox'; o.checked = k.hien;
    o.onchange = () => { k.hien = o.checked; daDoi(); danhSach(); }; nhan.append(o, document.createTextNode(' Hiển thị khối')); g.append(nhan);
  }
  function lichSu() {
    const g = tim('lich-su'); g.replaceChildren();
    if (!bang.lich_su.length) g.append(tao('p', 'Chưa có bản trước để khôi phục.'));
    bang.lich_su.forEach(v => {
      const dong = tao('div', '', 'lich-su-item'); dong.append(tao('b', 'Bản trước lần xuất bản ' + v.luc), tao('small', v.nguoi));
      const b = tao('button', 'Khôi phục vào nháp'); b.onclick = () => {
        if (doi && !window.confirm('Thay bản đang sửa bằng nội dung đã chọn trong lịch sử?')) return;
        nhap = structuredClone(v.noi_dung); chon = nhap.khoi[0]?.id || ''; daDoi(); danhSach(); thuocTinh(); bao('Đã khôi phục vào nháp trên màn hình. Xem lại rồi lưu hoặc xuất bản.');
      }; dong.append(b); g.append(dong);
    });
  }
  function nhanBang(d) { bang = d; nhap = structuredClone(d.nhap); doi = false; if (!nhap.khoi.some(k => k.id === chon)) chon = nhap.khoi[0]?.id || ''; thongKe(); danhSach(); thuocTinh(); lichSu(); xem(); }
  async function tai() {
    if (doi && !window.confirm('Tải lại sẽ bỏ phần chưa lưu trên màn hình. Tiếp tục?')) return;
    khoa(true); try { nhanBang(await api('doc_bang')); bao('Đã tải nội dung. Thay đổi chỉ ra website khi bấm Xuất bản.'); } catch (e) { bao(e.message, true); } finally { khoa(false); }
  }
  async function luu(hanhDong) {
    if (!bang || ban) return;
    if (hanhDong === 'xuat_ban' && !window.confirm('Xuất bản nội dung đang xem lên website đặt bánh?')) return;
    khoa(true); try {
      const d = await api('luu', {noi_dung: JSON.stringify(nhap), phien_ban: bang.phien_ban, hanh_dong: hanhDong});
      nhanBang(d); bao(hanhDong === 'xuat_ban' ? 'Đã xuất bản. Khách tải lại website sẽ thấy nội dung mới.' : 'Đã lưu nháp. Website đang giữ bản đã xuất bản.');
    } catch (e) { bao(e.message, true); } finally { khoa(false); }
  }
  Object.entries(tenLoai).forEach(([ma, ten]) => { const b = tao('button', '+ ' + ten); b.onclick = () => {
    if (!nhap || ban) return; if (nhap.khoi.length >= 30) { bao('Tối đa 30 khối mỗi trang.', true); return; }
    const k = {id: 'k-' + crypto.randomUUID(), loai: ma, hien: true, nhan: '', tieu_de: ten, noi_dung: '', anh: '', mo_ta_anh: '', nut: '', lien_ket: ''};
    nhap.khoi.push(k); chon = k.id; daDoi(); danhSach(); thuocTinh();
  }; tim('them-khoi').append(b); });
  tim('tai-lai').onclick = tai; tim('luu-nhap').onclick = () => luu('nhap'); tim('xuat-ban').onclick = () => luu('xuat_ban');
  ['desktop', 'mobile'].forEach(id => tim(id).onclick = () => { tim('preview').classList.toggle('mobile', id === 'mobile'); ['desktop','mobile'].forEach(x => tim(x).setAttribute('aria-pressed', String(x === id))); });
  tim('preview').onload = xem;
  tim('preview').srcdoc = '<!doctype html><html lang="vi"><head><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/assets/vagabond/web_order/khoi.css"><style>body{margin:0;background:#000}</style></head><body><div id="khoi"></div></body></html>';
  window.addEventListener('beforeunload', e => { if (doi) { e.preventDefault(); e.returnValue = ''; } });
  tai();
}());

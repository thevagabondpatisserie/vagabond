/* #245: bản nháp chỉ ra website sau hành động Xuất bản thành công. */
(function () {
  'use strict';
  const tim = id => document.getElementById(id);
  const tenLoai = {tieu_de_muc: 'Tiêu đề mục bán hàng', anh_bia: 'Ảnh bìa', cau_chuyen: 'Câu chuyện', anh_chu: 'Ảnh và chữ', thong_bao: 'Thông báo', hoi_dap: 'Câu hỏi thường gặp', uu_dai:'Ưu đãi', tuyen_dung:'Tuyển dụng', kenh_dat_hang:'Kênh đặt hàng', zalo_oa:'Zalo OA', nut_kenh:'Nút mở kênh đặt hàng'};
  let bang, nhap, chon = '', doi = false, ban = false, keo = '', mobile = false;
  let cacBuoc = [], buoc = -1, nhomChu = '', tuTim = '', locKhoi = '', timKhoi = '', locTrangThai = '';
  const khoaPhucHoi = 'vgb-web-nhap:' + document.body.dataset.nguoi;
  function ghiBuoc() {
    const chu = JSON.stringify(nhap);
    if (cacBuoc[buoc] !== chu) { cacBuoc = cacBuoc.slice(0, buoc + 1); cacBuoc.push(chu); if (cacBuoc.length > 60) cacBuoc.shift(); buoc = cacBuoc.length - 1; }
    nutHoanTac();
  }
  function nutHoanTac() { tim('hoan-tac').disabled = ban || buoc <= 0; tim('lam-lai').disabled = ban || buoc >= cacBuoc.length - 1; }
  function giuBanTrenMay() {
    try { sessionStorage.setItem(khoaPhucHoi, JSON.stringify({phien_ban:bang.phien_ban, noi_dung:nhap})); }
    catch (_) { bao('Bộ nhớ tab không lưu được bản phục hồi. Hãy Lưu nháp hoặc Tải bản đang sửa.', true); }
  }
  function veTatCa() { thongKe(); danhSach(); veChinhSach(); veNhanWeb(); thuocTinh(); xem(); }
  function hoanTac(huong) {
    const moi = buoc + huong; if (ban || moi < 0 || moi >= cacBuoc.length) return;
    buoc = moi; nhap = JSON.parse(cacBuoc[buoc]); doi = JSON.stringify(nhap) !== JSON.stringify(bang.nhap);
    giuBanTrenMay(); nutHoanTac(); veTatCa();
  }
  /* #367: ba trang chính sách đi chung luồng nháp và xuất bản của trang. */
  const CS = {chinh_sach_bao_mat: 'Chính sách bảo mật', dieu_khoan: 'Điều khoản sử dụng', giao_hang_doi_tra: 'Giao hàng và đổi trả'};
  const RE_CHO_TRONG = /\[[^\]\n]{1,80}\](?!\()/g;
  const choTrong = md => (String(md || '').match(RE_CHO_TRONG) || []);
  function csCua(khoa) {
    nhap.chinh_sach = nhap.chinh_sach || {};
    if (!nhap.chinh_sach[khoa]) nhap.chinh_sach[khoa] = {hien: false, vn: '', en: ''};
    return nhap.chinh_sach[khoa];
  }
  function veChinhSach() {
    const g = tim('chinh-sach'); if (!g || !nhap) return; g.replaceChildren();
    Object.entries(CS).forEach(([khoa, ten]) => {
      const v = (nhap.chinh_sach || {})[khoa] || {};
      const con = choTrong(v.vn).length + choTrong(v.en).length;
      const b = tao('button', ten + (v.hien ? ' · Đang hiện' : ' · Ẩn') + (con ? ' · còn ' + con + ' chỗ trống' : ''));
      b.setAttribute('aria-pressed', String(chon === 'cs:' + khoa));
      b.onclick = () => { chon = 'cs:' + khoa; danhSach(); veChinhSach(); veNhanWeb(); thuocTinh(); };
      g.append(b);
    });
  }
  function suaChinhSach(g, khoa) {
    const v = csCua(khoa);
    g.append(tao('p', CS[khoa] + '. Viết bằng Markdown: # tiêu đề, **chữ đậm**, - gạch đầu dòng. Trang công khai chỉ hiện khi đã bật hiện và bấm Xuất bản.', 'goi-y'));
    const canh = tao('p', '', 'goi-y cs-canh');
    function veCanh() {
      const con = choTrong(v.vn).concat(choTrong(v.en));
      canh.replaceChildren();
      if (con.length) { canh.append(tao('b', 'Còn ' + con.length + ' chỗ chưa điền: ')); canh.append(document.createTextNode(con.slice(0, 6).join(', ') + '. Chưa điền hết thì bật hiện sẽ không xuất bản được.')); }
      else canh.append(document.createTextNode('Đã điền hết các chỗ trong ngoặc vuông.'));
    }
    const hien = tao('label', '', 'truong'); const o = tao('input'); o.type = 'checkbox'; o.checked = !!v.hien;
    o.onchange = () => { v.hien = o.checked; daDoi(); veChinhSach(); };
    hien.append(o, document.createTextNode(' Hiện trang này trên website và chân trang')); g.append(hien, canh);
    [['vn', 'Nội dung tiếng Việt'], ['en', 'Nội dung tiếng Anh (để trống nếu chưa dịch)']].forEach(([ngu, ten]) => {
      const nhan = tao('label', '', 'truong cs-sua'); nhan.append(tao('span', ten));
      const t = tao('textarea'); t.maxLength = 30000; t.value = v[ngu] || '';
      t.oninput = () => { v[ngu] = t.value; daDoi(); veCanh(); }; t.onchange = veChinhSach;
      nhan.append(t); g.append(nhan);
    });
    veCanh();
  }
  /* v532: nhãn cố định (tab, nút, câu có số, trang đặt bàn). Danh sách khoá
     và mặc định do máy chủ trả trong doc_bang().nhan_mau; JS không chép cứng. */
  const RE_CHO_DIEN = /\{[a-z_]+\}/g;
  const choDien = chu => [...new Set(String(chu || '').match(RE_CHO_DIEN) || [])].sort();
  function nhanCua() { nhap.nhan = nhap.nhan || {}; return nhap.nhan; }
  function soNhanDaSua() { return Object.values(nhap.nhan || {}).filter(v => String(v || '').trim()).length; }
  function veNhanWeb() {
    const g = tim('nhan-web'); if (!g || !nhap) return; g.replaceChildren();
    const so = soNhanDaSua();
    const b = tao('button', 'Nhãn và câu chữ' + (so ? ' · ' + so + ' đã sửa' : ' · mặc định'));
    b.setAttribute('aria-pressed', String(chon === 'nhan'));
    b.onclick = () => { chon = 'nhan'; danhSach(); veChinhSach(); veNhanWeb(); thuocTinh(); xem(); };
    g.append(b);
  }
  function suaNhanWeb(g) {
    const mau = bang.nhan_mau || {}, nhan = nhanCua();
    g.append(tao('p', 'Mỗi ô là một chỗ chữ trên website. Để trống thì dùng chữ mặc định ghi dưới ô. Chỗ trong ngoặc nhọn như {so}, {khung}, {gio} là chỗ máy tự điền số, phải giữ lại. Bấm Xuất bản để khách thấy.', 'goi-y'));
    const timChu = tao('input'); timChu.type = 'search'; timChu.placeholder = 'Tìm câu chữ, nút hoặc nội dung đang sửa'; timChu.value = tuTim; timChu.setAttribute('aria-label', 'Tìm nội dung website');
    const locNhom = tao('div', '', 'them-khoi loc-nhom'), ds = tao('div'), dem = tao('p', '', 'goi-y');
    const tenNhom = {chung:'Điều hướng', dat_banh:'Chọn bánh', gio_hang:'Giỏ hàng và checkout', san_pham:'Chi tiết bánh', dat_ban:'Đặt bàn', thanh_vien:'Thành viên', bien_nhan:'Biên nhận', chinh_sach:'Chính sách', chan_trang:'Chân trang'};
    ['', ...new Set(Object.values(mau).map(m => m.nhom || 'chung'))].forEach(n => {
      const b = tao('button', n ? (tenNhom[n] || n) : 'Tất cả'); b.setAttribute('aria-pressed', String(nhomChu === n));
      b.onclick = () => { nhomChu = n; locNhom.querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', String(x === b))); veO(); }; locNhom.append(b);
    });
    g.append(timChu, locNhom, dem, ds);
    function veO() {
      ds.replaceChildren(); const q = tuTim.toLocaleLowerCase('vi');
      const cac = Object.entries(mau).filter(([k, m]) => (!nhomChu || (m.nhom || 'chung') === nhomChu) && (!q || [m.ten, m.mac_dinh, nhan[k], k].join(' ').toLocaleLowerCase('vi').includes(q)));
      dem.textContent = cac.length + ' nội dung' + (cac.length ? '' : '. Thử từ khác hoặc chọn Tất cả.');
      cac.forEach(([khoa, m]) => {
        const nhanO = tao('label', '', 'truong'); nhanO.append(tao('span', m.ten));
        const o = tao(m.nhieu_dong || khoa.startsWith('dat_ban_') || (m.mac_dinh || '').length > 60 ? 'textarea' : 'input');
        o.maxLength = m.nhieu_dong ? 4000 : 300; o.value = nhan[khoa] || ''; o.placeholder = m.mac_dinh; o.dataset.khoaChu = khoa;
        const canh = tao('small', '', 'goi-y');
        function veCanh() {
          const chu = o.value; const cacCho = choDien(chu), goc = choDien(m.mac_dinh);
          const sai = goc.filter(x => !cacCho.includes(x)).concat(cacCho.filter(x => !goc.includes(x)));
          canh.textContent = chu.trim() && sai.length ? 'Giữ đúng các chỗ điền: ' + goc.join(', ') : 'Mặc định: ' + m.mac_dinh;
          canh.classList.toggle('loi', !!(chu.trim() && sai.length)); o.setAttribute('aria-invalid', String(!!(chu.trim() && sai.length)));
        }
        o.oninput = () => { if (o.value.trim()) nhan[khoa] = o.value; else delete nhan[khoa]; daDoi(); veCanh(); };
        o.onchange = veNhanWeb;
        nhanO.append(o, canh); ds.append(nhanO); veCanh();
      });
    }
    timChu.oninput = () => { tuTim = timChu.value; veO(); }; veO();
  }

  let monMau = null;
  async function suaSanPham(g) {
    g.append(tao('p', 'Nội dung riêng theo mã bánh. Để trống để dùng danh mục gốc. Giá, tồn và mã đặt hàng giữ theo hệ thống.', 'goi-y'));
    const timMon = tao('input'); timMon.type = 'search'; timMon.placeholder = 'Tìm tên bánh hoặc mã'; timMon.setAttribute('aria-label','Tìm sản phẩm');
    const ds = tao('div'); g.append(timMon, ds);
    ds.textContent = 'Đang tải danh mục...';
    try { if (!monMau) monMau = await api('san_pham_bien_tap'); }
    catch (e) { ds.textContent = 'Chưa tải được danh mục. Chọn lại mục Nội dung bánh để thử lại.'; return; }
    if (chon !== 'san_pham') return;
    function veMon() {
      ds.replaceChildren(); const q = timMon.value.toLocaleLowerCase('vi');
      const cac = monMau.filter(m => (m.ten + ' ' + m.ma).toLocaleLowerCase('vi').includes(q));
      if (!cac.length) ds.append(tao('p', 'Chưa có bánh phù hợp. Thử từ khác hoặc kiểm danh mục bán.'));
      cac.forEach(m => {
        const muc = tao('details'); muc.append(tao('summary', m.ten + ' · ' + m.ma));
        [['ten','Tên hiển thị'],['mo_ta','Mô tả'],['tang','Tầng hương lớp vị (mỗi dòng một tầng)'],['theo_mua','Nhãn theo mùa'],['khau_phan','Khẩu phần']].forEach(([k,ten]) => {
          const l = tao('label','','truong'), o = tao('textarea'); l.append(tao('span',ten));
          o.maxLength=4000; o.value=(nhap.san_pham || {})[m.ma]?.[k] || ''; o.placeholder=m[k] || '';
          o.oninput=()=>{ nhap.san_pham=nhap.san_pham || {}; nhap.san_pham[m.ma]=nhap.san_pham[m.ma] || {}; nhap.san_pham[m.ma][k]=o.value; daDoi(); }; l.append(o); muc.append(l);
        }); ds.append(muc);
      });
    }
    timMon.oninput=veMon; veMon();
  }
  function coPreview() {
    const khung = document.querySelector('.khung-preview'), f = tim('preview');
    const rong = mobile ? 375 : 1440, cao = mobile ? 812 : 900, tyLe = Math.min(1, khung.clientWidth / rong);
    if (!tyLe) return;
    f.style.width = rong + 'px'; f.style.height = cao + 'px'; khung.style.height = (cao * tyLe) + 'px';
    f.style.marginLeft = (-rong / 2) + 'px'; f.style.transform = 'scale(' + tyLe + ')';
  }
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
  function khoa(b) { ban = b; ['luu-nhap', 'xuat-ban', 'tai-lai'].forEach(id => tim(id).disabled = b); tim('thuoc-tinh').inert = b; tim('danh-sach').inert = b; tim('them-khoi').inert = b; tim('lich-su').inert = b; if (tim('chinh-sach')) tim('chinh-sach').inert = b; if (tim('nhan-web')) tim('nhan-web').inert = b; nutHoanTac(); }
  function thongKe() {
    tim('so-khoi').textContent = nhap.khoi.length;
    tim('so-hien').textContent = nhap.khoi.filter(k => k.hien).length;
    tim('phien-ban').textContent = bang.phien_ban;
    tim('tinh-trang').textContent = doi ? 'Chưa lưu' : JSON.stringify(nhap) === JSON.stringify(bang.cong_khai) ? 'Đã xuất bản' : 'Bản nháp';
  }
  function xem() {
    if (nhap) tim('preview').contentWindow.postMessage({loai:'vgb-noi-dung',noi_dung:nhap,chon:chon}, location.origin);
  }
  function daDoi() { doi = true; ghiBuoc(); giuBanTrenMay(); thongKe(); xem(); }
  function doiCho(id, buoc) {
    if (ban) return;
    const i = nhap.khoi.findIndex(k => k.id === id), j = i + buoc;
    if (j < 0 || j >= nhap.khoi.length) return;
    [nhap.khoi[i], nhap.khoi[j]] = [nhap.khoi[j], nhap.khoi[i]];
    daDoi(); danhSach();
  }
  function trangThaiKhoi(k) {
    if(!k.hien)return 'Đang ẩn';
    const n=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Ho_Chi_Minh',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
    if(k.ket_thuc&&k.ket_thuc<n)return 'Đã kết thúc';
    if(k.bat_dau&&k.bat_dau>n)return 'Sắp diễn ra';
    return 'Đang diễn ra';
  }
  function danhSach() {
    const g = tim('danh-sach'); g.replaceChildren();
    const locTT=tim('loc-trang-thai'); if(locTT){locTT.replaceChildren();['','Đang diễn ra','Sắp diễn ra','Đã kết thúc','Đang ẩn'].forEach(tt=>{const ds=nhap.khoi.filter(k=>(!locKhoi||k.loai===locKhoi)&&(!tt||trangThaiKhoi(k)===tt));const b=tao('button',(tt||'Tất cả trạng thái')+' '+ds.length);b.setAttribute('aria-pressed',String(tt===locTrangThai));b.onclick=()=>{locTrangThai=tt;danhSach();};locTT.append(b);});}
    let soHien=0;
    if (!nhap.khoi.length) g.append(tao('p', 'Chưa có khối. Chọn một loại bên dưới để thêm.'));
    nhap.khoi.forEach((k, i) => {
      if (locKhoi && k.loai !== locKhoi) return;
      if(locTrangThai&&trangThaiKhoi(k)!==locTrangThai)return;
      if (timKhoi && ![k.tieu_de,k.nhom,k.ma_uu_dai,k.noi_lam].join(' ').toLocaleLowerCase('vi').includes(timKhoi)) return;
      soHien++;
      const dong = tao('div', '', 'dong-khoi' + (chon === k.id ? ' on' : '')); dong.draggable = true;
      const nut = tao('button', (i + 1) + '. ' + (k.tieu_de || tenLoai[k.loai]) + (k.hien ? '' : ' · Ẩn'), 'chon-khoi');
      nut.onclick = () => { chon = k.id; danhSach(); veChinhSach(); veNhanWeb(); thuocTinh(); xem(); }; dong.append(nut);
      if(['uu_dai','tuyen_dung'].includes(k.loai))dong.append(tao('small',trangThaiKhoi(k)+' · '+(k.nhom||tenLoai[k.loai]),'goi-y'));
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
    if(!soHien&&nhap.khoi.length)g.append(tao('p','Không có nội dung khớp bộ lọc. Chọn Tất cả hoặc xoá từ tìm.','goi-y'));
  }
  function thuocTinh() {
    const g = tim('thuoc-tinh'); g.replaceChildren();
    if (chon.startsWith('cs:') && CS[chon.slice(3)]) { suaChinhSach(g, chon.slice(3)); return; }
    if (chon === 'san_pham') { suaSanPham(g); return; }
    if (chon === 'nhan') { suaNhanWeb(g); return; }
    const k = nhap.khoi.find(x => x.id === chon);
    if (!k) { g.append(tao('p', 'Chọn một khối để chỉnh nội dung.')); return; }
    if (k.loai === 'tieu_de_muc') {
      g.append(tao('p', 'Tiêu đề trên mục ' + ({today:'Có sẵn hôm nay',order:'Đặt bánh trước',store:'In store'}[k.vi_tri]) + '. Ngày, giá và tồn tiếp tục lấy từ hệ thống.', 'goi-y'));
      const nhan = tao('label','','truong'); nhan.append(tao('span','Tiêu đề mục'));
      const o = tao('textarea'); o.maxLength=120; o.value=k.tieu_de; o.oninput=()=>{k.tieu_de=o.value;daDoi();}; o.onchange=danhSach;
      nhan.append(o);g.append(nhan);return;
    }
    const sao = tao('button', 'Nhân bản khối'); sao.onclick = () => {
      if(k.loai==='nut_kenh'){bao('Chỉ có một nút mở kênh. Sửa logo của nút này.',true);return;}
      if (ban || nhap.khoi.length >= 30) { bao('Tối đa 30 khối. Tái sử dụng một khối đang ẩn.', true); return; }
      const moi = structuredClone(k); moi.id = 'k-' + crypto.randomUUID(); moi.hien = false;
      nhap.khoi.splice(nhap.khoi.indexOf(k) + 1, 0, moi); chon = moi.id; daDoi(); veTatCa();
    }; g.append(sao);
    g.append(tao('p', 'Loại khối · có thể đổi để tái sử dụng khối cũ', 'goi-y'));
    const cacLoai = tao('div', '', 'them-khoi');
    Object.entries(tenLoai).filter(([ma]) => ma !== 'tieu_de_muc').forEach(([ma, ten]) => { const b = tao('button', ten); b.setAttribute('aria-pressed', String(k.loai === ma)); b.onclick = () => { if(ma==='nut_kenh'&&nhap.khoi.some(x=>x!==k&&x.loai===ma)){bao('Nút mở kênh đã có. Chọn nút đó trong danh sách để sửa.',true);return;} k.loai = ma; if(['uu_dai','tuyen_dung'].includes(ma))k.vi_tri=ma;else if(['uu_dai','tuyen_dung'].includes(k.vi_tri))k.vi_tri='cuoi_trang'; daDoi(); danhSach(); thuocTinh(); }; cacLoai.append(b); });
    g.append(cacLoai);
    if (['uu_dai','tuyen_dung'].includes(k.loai)) { g.append(tao('p', 'Hiển thị tại trang '+tenLoai[k.loai]+'. Ảnh bên dưới có thể thay bất cứ lúc nào. Ngày tính theo giờ Việt Nam.', 'goi-y')); }
    if(['kenh_dat_hang','zalo_oa','nut_kenh'].includes(k.loai))g.append(tao('p', k.loai==='nut_kenh'?'Logo trên nút nổi mở danh sách ứng dụng. Tên dùng cho trình đọc màn hình; tắt hiển thị để ẩn nút và danh sách.':k.loai==='zalo_oa'?'Nút Zalo riêng. Có thể thay logo, tên và đường dẫn OA.':'Thay logo, tên và đường dẫn ứng dụng. Dùng mũi tên ở danh sách khối để đổi thứ tự; tắt hiển thị để ẩn kênh.', 'goi-y'));
    if(!['uu_dai','tuyen_dung','kenh_dat_hang','zalo_oa','nut_kenh'].includes(k.loai)){g.append(tao('p', 'Vị trí trên trang order', 'goi-y'));
    const viTri = tao('div', '', 'them-khoi');
    Object.entries({dau_trang:'Dưới logo',today:'Có sẵn hôm nay',order:'Đặt bánh trước',store:'In store',season:'In season',cuoi_trang:'Cuối trang'}).forEach(([ma,ten]) => {
      const b = tao('button', ten); b.setAttribute('aria-pressed', String((k.vi_tri || 'cuoi_trang') === ma));
      b.onclick = () => { k.vi_tri = ma; daDoi(); thuocTinh(); }; viTri.append(b);
    }); g.append(viTri);}
    const kenhNoi=['kenh_dat_hang','zalo_oa','nut_kenh'].includes(k.loai);
    (kenhNoi?(k.loai==='nut_kenh'?[['tieu_de','Tên trợ năng của nút'],['anh','Đường dẫn logo nút nổi']]:[['tieu_de','Tên nút / ứng dụng'],['anh','Đường dẫn logo ứng dụng'],['nut','Chữ dự phòng khi logo không tải được'],['lien_ket','Liên kết HTTPS']]):[['nhan','Dòng giới thiệu'],['tieu_de','Tiêu đề'],['noi_dung','Nội dung'],['anh','Đường dẫn ảnh công khai'],['mo_ta_anh','Mô tả ảnh'],['nut','Chữ trên nút'],['lien_ket','Liên kết của nút']]).forEach(([ma, ten]) => {
      const nhan = tao('label', '', 'truong'); nhan.append(tao('span', ten));
      const o = tao(ma === 'noi_dung' || ma === 'tieu_de' ? 'textarea' : 'input');
      o.value = k[ma] || ''; o.maxLength = ma === 'noi_dung' ? 4000 : 1000;
      o.oninput = () => { k[ma] = o.value; daDoi(); }; o.onchange = () => danhSach();
      nhan.append(o); g.append(nhan);
    });
    if (['uu_dai','tuyen_dung'].includes(k.loai)) {
      const truong = [['bat_dau','Ngày bắt đầu','date'],['ket_thuc','Ngày kết thúc (trống: chưa có hạn)','date'],['nhom','Nhóm / đối tượng','text']];
      if(k.loai==='uu_dai') truong.push(['ma_uu_dai','Mã ưu đãi để giới thiệu (không tự giảm tiền)','text']);
      else truong.push(['noi_lam','Nơi làm việc','text'],['hinh_thuc','Hình thức làm việc','text'],['email','Email nhận hồ sơ','email']);
      truong.forEach(([ma,ten,loai])=>{const l=tao('label','','truong'),o=tao('input');l.append(tao('span',ten));o.type=loai;o.value=k[ma]||'';o.maxLength=1000;o.oninput=()=>{k[ma]=o.value;daDoi();};l.append(o);g.append(l);});
    }
    const taiNhan = tao('label', '', 'truong'); taiNhan.append(tao('span', kenhNoi?'Tải logo từ máy (PNG, JPG, WebP)':'Tải ảnh từ máy (ảnh sẽ công khai)'));
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
    g.append(tao('p', kenhNoi?'Logo hiển thị nguyên tỉ lệ. Dùng PNG nền trong suốt hoặc ảnh vuông; có thể dán link HTTPS hoặc /files/.':'Ảnh: dán link HTTPS hoặc /files/ từ thư viện ảnh. Nút chọn bánh: #danh-muc-banh. Đặt trước: #/dat-truoc.', 'goi-y'));
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
        nhap = structuredClone(v.noi_dung); chon = nhap.khoi[0]?.id || ''; daDoi(); veTatCa(); bao('Đã khôi phục vào nháp trên màn hình. Xem lại rồi lưu hoặc xuất bản.');
      }; dong.append(b); g.append(dong);
    });
  }
  function nhanBang(d) { bang = d; nhap = structuredClone(d.nhap); doi = false; cacBuoc = []; buoc = -1; ghiBuoc(); if (!chon.startsWith('cs:') && chon !== 'nhan' && chon !== 'san_pham' && !nhap.khoi.some(k => k.id === chon)) chon = nhap.khoi[0]?.id || ''; thongKe(); danhSach(); veChinhSach(); veNhanWeb(); thuocTinh(); lichSu(); xem(); }
  async function tai() {
    if (doi && !window.confirm('Tải lại sẽ bỏ phần chưa lưu trên màn hình. Tiếp tục?')) return;
    khoa(true); try { nhanBang(await api('doc_bang')); kiemBanPhucHoi(); bao('Đã tải nội dung. Thay đổi chỉ ra website khi bấm Xuất bản.'); } catch (e) { bao(e.message, true); } finally { khoa(false); }
  }
  async function luu(hanhDong) {
    if (!bang || ban) return;
    if (hanhDong === 'xuat_ban' && !window.confirm('Xuất bản nội dung đang xem lên website đặt bánh?')) return;
    khoa(true); try {
      const d = await api('luu', {noi_dung: JSON.stringify(nhap), phien_ban: bang.phien_ban, hanh_dong: hanhDong});
      try { sessionStorage.removeItem(khoaPhucHoi); } catch (_) {} tim('phuc-hoi').hidden = true; nhanBang(d); bao(hanhDong === 'xuat_ban' ? 'Đã xuất bản. Khách tải lại website sẽ thấy nội dung mới.' : 'Đã lưu nháp. Website đang giữ bản đã xuất bản.');
    } catch (e) { bao(e.message, true); } finally { khoa(false); }
  }
  Object.entries(tenLoai).filter(([ma]) => ma !== 'tieu_de_muc').forEach(([ma, ten]) => { const b = tao('button', '+ ' + ten); b.onclick = () => {
    if (!nhap || ban) return; if(ma==='nut_kenh'&&nhap.khoi.some(k=>k.loai===ma)){chon=nhap.khoi.find(k=>k.loai===ma).id;thuocTinh();bao('Đã chọn nút mở kênh hiện có.');return;} if (nhap.khoi.length >= 30) { bao('Đã có 30 khối. Chọn khối cũ, đổi loại và nội dung để tái sử dụng.', true); return; }
    const k = {id: 'k-' + crypto.randomUUID(), loai: ma, hien: !['uu_dai','tuyen_dung','kenh_dat_hang','zalo_oa','nut_kenh'].includes(ma), vi_tri: ['uu_dai','tuyen_dung'].includes(ma)?ma:'cuoi_trang', nhan: '', tieu_de: ten, noi_dung: '', anh: ma==='tuyen_dung'?'/assets/vagabond/web_order/tay-lam-banh-minh-hoa.jpg':'', mo_ta_anh: ma==='tuyen_dung'?'Ảnh minh hoạ tay làm bánh':'', nut: '', lien_ket: ''};
    nhap.khoi.push(k); chon = k.id; daDoi(); danhSach(); thuocTinh();
  }; tim('them-khoi').append(b); });
  const loc = tao('div','','them-khoi');
  [['','Tất cả'],['uu_dai','Ưu đãi'],['tuyen_dung','Tuyển dụng']].forEach(([ma,ten])=>{const b=tao('button',ten);b.onclick=()=>{locKhoi=ma;locTrangThai='';loc.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));danhSach();};loc.append(b);});
  const timK=tao('input');timK.placeholder='Tìm tiêu đề, mã ưu đãi, nơi làm';timK.setAttribute('aria-label',timK.placeholder);timK.oninput=()=>{timKhoi=timK.value.toLocaleLowerCase('vi');danhSach();};
  const locTT=tao('div','','loc-trang-thai');locTT.id='loc-trang-thai';tim('danh-sach').before(loc,timK,locTT);
  function kiemBanPhucHoi() {
    const g = tim('phuc-hoi'); g.replaceChildren(); g.hidden = true;
    let cu; try { cu = JSON.parse(sessionStorage.getItem(khoaPhucHoi)); } catch (_) { return; }
    if (!cu || !cu.noi_dung || JSON.stringify(cu.noi_dung) === JSON.stringify(nhap)) return;
    g.hidden = false;
    g.append(tao('p', 'Tab này có nội dung chưa lưu.' + (cu.phien_ban !== bang.phien_ban ? ' Website đã có phiên bản mới. So sánh trước khi lưu lại.' : '')));
    const b = tao('button', 'Mở bản phục hồi'); b.onclick = () => { if (ban) return; if (cu.phien_ban !== bang.phien_ban && !window.confirm('Bản phục hồi có thể thay nội dung mới của người khác. Tải bản đang sửa để đối chiếu trước. Vẫn mở bản phục hồi?')) return; nhap = structuredClone(cu.noi_dung); daDoi(); veTatCa(); g.hidden = true; bao('Đã phục hồi trên màn hình. Chưa xuất bản.'); };
    const bo = tao('button', 'Bỏ bản phục hồi'); bo.onclick = () => { try { sessionStorage.removeItem(khoaPhucHoi); } catch (_) {} g.hidden = true; };
    g.append(b, bo);
  }
  tim('hoan-tac').onclick = () => hoanTac(-1); tim('lam-lai').onclick = () => hoanTac(1);
  tim('tai-ban').onclick = () => { if (!nhap) return; const u = URL.createObjectURL(new Blob([JSON.stringify(nhap, null, 2)], {type:'application/json'})); const a = tao('a'); a.href = u; a.download = 'noi-dung-web-chua-xuat-ban.json'; a.click(); setTimeout(() => URL.revokeObjectURL(u), 1000); };
  tim('sua-san-pham').onclick = () => { chon = 'san_pham'; veTatCa(); };
  tim('tai-lai').onclick = tai; tim('luu-nhap').onclick = () => luu('nhap'); tim('xuat-ban').onclick = () => luu('xuat_ban');
  ['desktop', 'mobile'].forEach(id => tim(id).onclick = () => { mobile = id === 'mobile'; coPreview(); ['desktop','mobile'].forEach(x => tim(x).setAttribute('aria-pressed', String(x === id))); });
  new ResizeObserver(coPreview).observe(document.querySelector('.khung-preview'));
  tim('preview').onload = xem;
  window.addEventListener('message', e => {
    if (e.origin !== location.origin || e.source !== tim('preview').contentWindow) return;
    if (e.data?.loai === 'vgb-san-sang') xem();
    if (e.data?.loai === 'vgb-chon-khoi' && nhap?.khoi.some(k => k.id === e.data.id)) { chon = e.data.id; danhSach(); veChinhSach(); veNhanWeb(); thuocTinh(); xem(); }
  });
  tim('preview').src = '/banh?bien_tap=1';
  window.addEventListener('beforeunload', e => { if (doi) { e.preventDefault(); e.returnValue = ''; } });
  tai();
}());

/* ========== QUAN LY HOP DONG MUA BAN: BAO GIA + HOP DONG ==========
   (anh Viet 14/08/2026, lam lai theo gop y buoi chieu)

Ba thu anh Viet chi ra va da sua:
  1. Bang chon mon PHAI co hinh - gio goi chung mot cho `vgbChonMon`, du
     lieu lay tu `vagabond.chon_mon.nguon`, man nao cung dung ham nay.
  2. Khong bat nguoi dung tra loi tung hop thoai nua - chon NHIEU mon mot
     luot, roi moi dong nhap thang tai cho: so luong, don gia, chiet khau.
  3. Mon thiet ke rieng va cac khoan phi nam trong Thu vien bao gia, co
     hinh va song ngu, chon lai duoc cho to sau.
*/

var BG_CAI = null;
async function bgCaiDat(lam_moi) {
  if (BG_CAI && !lam_moi) return BG_CAI;
  BG_CAI = await api('vagabond.bao_gia.cai_dat', {});
  return BG_CAI;
}

var BGTT_ICON = {
  'Nháp': '📝', 'Đã gửi khách': '📤', 'Khách duyệt': '✅',
  'Khách từ chối': '⛔', 'Hết hiệu lực': '⌛', 'Đã lên hợp đồng': '📑'
};
var BGNHAN = 'style="font-size:12.5px;color:#8a8f9c;line-height:1.35;margin-top:2px"';

/* Bo dau tieng Viet, bo moi ky tu khong phai chu hoac so. Dung cho MOI o
   tim trong app: go "banh nuong" ra "Bánh nướng", go thua mot dau cach hay
   dau phay cung khong hut mat ket qua.
   Anh Viet 15/08/2026 bat duoc: go "moonlapis" khong ra "HỘP MOONLAPIS,
   năm 2026" chi vi o tim con thua mot dau cach o cuoi. */
function vgbChuan(s) {
  return String(s == null ? '' : s).toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
}
/* Tim theo TU: moi tu go ra deu phai co mat, khong cần dung thu tu. */
function vgbKhop(kho, tim) {
  var t = vgbChuan(tim);
  if (!t) return true;
  var k = vgbChuan(kho);
  var tu = t.split(' ');
  for (var i = 0; i < tu.length; i++) if (k.indexOf(tu[i]) < 0) return false;
  return true;
}
/* Doc so tien nguoi dung go: bo dau cham ngan nghin, bo chu, bo khoang trang. */
function vgbSo(v) { return Number(String(v == null ? '' : v).replace(/[^0-9]/g, '')) || 0; }
/* Hien so tien co dau cham ngan nghin. Anh Viet 15/08/2026: "tất cả giá tiền
   phải có dấu thập phân cho dễ nhìn". */
function vgbTien(v) { return (Math.round(Number(v) || 0)).toLocaleString('vi-VN'); }
var BGTA = 'class="tin" style="height:auto;font-size:15px;font-weight:500;text-align:left;padding:10px 12px;line-height:1.5"';
var BGO = 'class="tin" style="height:auto;font-size:15px;font-weight:500;text-align:left;padding:9px 11px"';

function bgNgayVn(s) { var p = String(s || '').split('-'); return p.length === 3 ? p[2] + '/' + p[1] + '/' + p[0] : (s || ''); }
function bgAnhO(url, cao) {
  cao = cao || 42;
  return url
    ? '<img src="' + h(url) + '" loading="lazy" style="width:' + cao + 'px;height:' + cao + 'px;object-fit:cover;border-radius:9px;border:1px solid #e5e7eb;flex:none;background:#fff">'
    : '<div style="width:' + cao + 'px;height:' + cao + 'px;border-radius:9px;border:1px dashed #d7dce5;display:flex;align-items:center;justify-content:center;font-size:' + Math.round(cao / 2.2) + 'px;flex:none;color:#c3c8d4">🍰</div>';
}

/* Tai mot tep hinh tu may cua sales len /files, tra ve duong dan.
   Anh Viet 15/08/2026: *"chỗ hình ảnh phải có thêm nút Tải lên tệp từ máy
   tính của sales"*. Anh may anh chup dien thoai nang vai chuc MB, nhung
   PDF bao gia phai gui duoc qua email, nen thu nho ve toi da 1200px truoc
   khi day len - dung quy tac chung "anh luon thu nho truoc khi nhung". */
function vgbTaiAnh() {
  return new Promise(function (xong) {
    var inp = document.createElement('input');
    inp.type = 'file'; inp.accept = 'image/*';
    inp.onchange = function () {
      var f = inp.files && inp.files[0];
      try { inp.remove(); } catch (e) { }
      if (!f) return xong('');
      if (!/^image\//.test(f.type || '')) { baoTin('Chỉ tải lên được tệp hình.'); return xong(''); }
      busy(true);
      var url = URL.createObjectURL(f);
      var img = new Image();
      img.onload = function () {
        var w = img.width, h2 = img.height, M = 1200;
        if (w > M || h2 > M) { var t = M / Math.max(w, h2); w = Math.round(w * t); h2 = Math.round(h2 * t); }
        var cv = document.createElement('canvas'); cv.width = w; cv.height = h2;
        cv.getContext('2d').drawImage(img, 0, 0, w, h2);
        cv.toBlob(function (b) {
          URL.revokeObjectURL(url);
          var fd = new FormData();
          fd.append('file', new File([b], 'baogia-' + Date.now() + '.jpg', { type: 'image/jpeg' }));
          fd.append('is_private', '0');
          var hd = {};
          hd['X-Frappe-' + 'CSRF-' + 'Token'] = frappe.csrf_token;
          fetch('/api/method/upload_file', { method: 'POST', headers: hd, body: fd })
            .then(function (r) { return r.json().then(function (j) { return { r: r, j: j }; }); })
            .then(function (x) {
              busy(false);
              if (!x.r.ok || !x.j.message || !x.j.message.file_url) { baoTin('Tải hình lên lỗi, thử lại giúp em.'); return xong(''); }
              xong(x.j.message.file_url);
            })
            .catch(function (e) { busy(false); baoTin('Tải hình lên lỗi: ' + ((e && e.message) || '')); xong(''); });
        }, 'image/jpeg', 0.82);
      };
      img.onerror = function () { busy(false); URL.revokeObjectURL(url); baoTin('Không đọc được tệp hình này.'); xong(''); };
      img.src = url;
    };
    inp.style.display = 'none';
    document.body.appendChild(inp);
    inp.click();
  });
}

/* Dich sang tieng Anh bang Gemini. Nhan mang chuoi, tra mang chuoi cung do
   dai. Dich CA CUM mot lan chu khong tung o le, de cau chu dong nhat.
   Anh Viet 15/08/2026: *"'Name in English' các phần này có thể nối với API
   google translate hay tool gì đó (AI?) để tự động dịch cho Loan Anh"*. */
async function vgbDich(ds) {
  var kq;
  try { kq = await api('vagabond.dich.dich', { chuoi: JSON.stringify(ds) }); }
  catch (e) { throw new Error((e && e.message) || 'Không gọi được dịch vụ dịch'); }
  if (!kq || !kq.ok) {
    throw new Error('Chưa dịch được (' + ((kq && kq.ly_do) || 'không rõ') +
      '). Kiểm tra ô Gemini API key trong Cài đặt Vagabond giúp em.');
  }
  return kq.ra || [];
}

/* Cac cap o Viet - Anh cua mot dong san pham va cua ca to. */
var BGCAP_DONG = [['ten_mon', 'ten_en'], ['dvt', 'dvt_en'], ['kich_thuoc', 'kich_thuoc'],
  ['mo_ta', 'mo_ta_en'], ['di_ung_vi', 'di_ung_en'], ['danh_muc_vi', 'danh_muc_en']]
  .filter(function (c) { return c[0] !== c[1]; });
var BGCAP_TO = [['ten', 'ten_en'], ['loi_mo', 'loi_mo_en'], ['thanh_toan', 'thanh_toan_en'],
  ['yeu_cau_vi', 'yeu_cau_en'], ['chinh_sach_huy_vi', 'chinh_sach_huy_en'],
  ['luu_y_vi', 'luu_y_en']];
/* Chi lay o nao co tieng Viet MA CHUA co tieng Anh: ban may dich khong bao
   gio de len chu nguoi that da go. */
function bgCanDich(o, cap, ra) {
  cap.forEach(function (c) {
    if (String(o[c[0]] == null ? '' : o[c[0]]).trim() && !String(o[c[1]] == null ? '' : o[c[1]]).trim()) {
      ra.push({ o: o, a: c[0], b: c[1] });
    }
  });
  return ra;
}

/* ---------- Bang chon mon DUNG CHUNG cho ca he ----------
   Tra ve Promise mot mang mon da chon. Luon co hinh, co hang chip nhom,
   co o tim, va chon duoc nhieu mon mot luot. */
var VGB_MON_CACHE = null;
async function vgbChonMon(o) {
  o = o || {};
  var nhieu = o.nhieu !== false;
  var kho;
  busy(true);
  try {
    kho = await api('vagabond.chon_mon.nguon', {
      ke_thu_vien: o.ke_thu_vien ? 1 : 0,
      chi_thu_vien: o.chi_thu_vien ? 1 : 0,
      gioi_han: 900
    });
  } catch (e) { busy(false); baoTin((e && e.message) || 'Không tải được danh mục'); return []; }
  busy(false);
  VGB_MON_CACHE = kho;

  return new Promise(function (xong) {
    var chon = {}, nhomChon = '', q = '';
    var ov = document.createElement('div'); ov.className = 'sh';
    var box = document.createElement('div'); box.className = 'shb';
    box.innerHTML =
      '<div class="shh"><b>' + h(o.tieu_de || 'Chọn sản phẩm') + '</b><div class="x">&times;</div></div>' +
      '<div style="padding:10px 14px 6px"><input class="nt" id="cmTim" placeholder="Tìm tên món hoặc mã..." style="height:46px;padding:0 12px;width:100%;box-sizing:border-box"></div>' +
      '<div id="cmNhom" style="padding:0 14px 8px;display:flex;flex-direction:row;flex-wrap:wrap;gap:6px"></div>' +
      '<div class="shl" id="cmDs" style="padding:0 10px"></div>' +
      '<div id="cmChan" style="padding:10px 14px calc(env(safe-area-inset-bottom,0px) + 12px);border-top:1px solid #eef0f4"></div>';
    ov.appendChild(box); document.body.appendChild(ov);

    var eNhom = box.querySelector('#cmNhom'), eDs = box.querySelector('#cmDs'), eChan = box.querySelector('#cmChan');

    /* Truoc day khoi chip bi dat max-height nen hang cuoi bi cat ngang, nhin
       ra mot day o trong (anh Viet bat duoc 15/08/2026). Gio khong cat nua:
       mac dinh chi bay 8 nhom dong nhat, bam "Thêm nhóm" moi mo het. */
    var moNhom = false;
    function veNhom() {
      var ds = moNhom ? kho.nhom : kho.nhom.slice(0, 8);
      var s = posChipNut('data-cmn=""', 'Tất cả · ' + kho.mon.length, !nhomChon);
      ds.forEach(function (n) {
        s += posChipNut('data-cmn="' + h(n.ten) + '"', h(n.ten) + ' · ' + n.so, nhomChon === n.ten);
      });
      if (kho.nhom.length > 8) {
        s += posChipNut('data-cmmo="1"', moNhom ? 'Thu gọn ▴' : ('Thêm ' + (kho.nhom.length - 8) + ' nhóm ▾'), false);
      }
      eNhom.innerHTML = s;
    }
    function loc() {
      return kho.mon.filter(function (m) {
        if (nhomChon && m.nhom !== nhomChon) return false;
        return vgbKhop((m.ten || '') + ' ' + (m.ten_en || '') + ' ' + (m.tim || '') + ' ' + (m.nhom || ''), q);
      });
    }
    function veDs() {
      var ds = loc();
      if (!ds.length) { eDs.innerHTML = '<div class="emp" style="padding:26px"><div class="e1">🔍</div><div>Không tìm thấy món nào</div></div>'; return; }
      eDs.innerHTML = ds.slice(0, 300).map(function (m) {
        var dc = !!chon[m.ma];
        return '<div data-cmm="' + h(m.ma) + '" style="display:flex;align-items:center;gap:11px;padding:9px 10px;border-radius:12px;margin-bottom:6px;cursor:pointer;border:1.5px solid ' + (dc ? '#0d9488' : 'transparent') + ';background:' + (dc ? '#effbf9' : '#f7f8fa') + '">' +
          bgAnhO(m.hinh, 46) +
          '<div style="flex:1;min-width:0">' +
          '<div style="font-size:14.5px;font-weight:700;line-height:1.3">' + h(m.ten) + '</div>' +
          (m.ten_en ? '<div style="font-size:12px;color:#8a8f9c;font-style:italic">' + h(m.ten_en) + '</div>' : '') +
          '<div style="font-size:12px;color:#6b7280;margin-top:2px">' +
          (m.gia ? money(m.gia) + ' đ' : (m.gia_chu_vi ? h(m.gia_chu_vi) : 'chưa có giá')) +
          (m.dvt ? ' / ' + h(m.dvt) : '') +
          (m.nguon === 'thu_vien' ? ' · <b style="color:#0d9488">thư viện</b>' : '') +
          (m.loai && m.loai !== 'Món' ? ' · ' + h(m.loai) : '') + '</div></div>' +
          '<div style="font-size:20px;flex:none;color:' + (dc ? '#0d9488' : '#c3c8d4') + '">' + (dc ? '&#10003;' : '+') + '</div></div>';
      }).join('') + (ds.length > 300 ? '<div style="text-align:center;color:#8a8f9c;font-size:12.5px;padding:8px">Còn ' + (ds.length - 300) + ' món nữa, gõ vào ô tìm để lọc bớt.</div>' : '');
    }
    function veChan() {
      var n = Object.keys(chon).length;
      eChan.innerHTML = nhieu
        ? '<button class="btn" id="cmXong" style="margin:0"' + (n ? '' : ' disabled') + '>' + (n ? 'Thêm ' + n + ' món đã chọn' : 'Chọn ít nhất một món') + '</button>'
        : '<div style="text-align:center;color:#8a8f9c;font-size:12.5px">Bấm vào một món để chọn</div>';
      var b = eChan.querySelector('#cmXong');
      if (b) b.onclick = function () { tra(Object.keys(chon).map(function (k) { return chon[k]; })); };
    }
    function ve() { veNhom(); veDs(); veChan(); }
    function tra(v) { try { ov.remove(); } catch (e) { } xong(v || []); }

    box.querySelector('#cmTim').oninput = function () { q = this.value; veDs(); };
    box.onclick = function (e) {
      if (e.target.closest('.x')) return tra([]);
      if (e.target.closest('[data-cmmo]')) { moNhom = !moNhom; return veNhom(); }
      var n = e.target.closest('[data-cmn]');
      if (n) { nhomChon = n.getAttribute('data-cmn') || ''; return ve(); }
      var m = e.target.closest('[data-cmm]');
      if (m) {
        var ma = m.getAttribute('data-cmm');
        var mon = kho.mon.filter(function (x) { return x.ma === ma; })[0];
        if (!mon) return;
        if (!nhieu) return tra([mon]);
        if (chon[ma]) delete chon[ma]; else chon[ma] = mon;
        veDs(); veChan();
      }
    };
    ov.onclick = function (e) { if (e.target === ov) tra([]); };
    ve();
    setTimeout(function () { try { box.querySelector('#cmTim').focus(); } catch (e) { } }, 120);
  });
}

/* ---------- Cua vao: Quan ly hop dong mua ban ---------- */
async function scrHopDongHub() {
  frame('Quản lý hợp đồng mua bán', '<div class="emp"><div class="e1">⏳</div><div>Đang đếm...</div></div>');
  var dem = {}, shd = 0, stv = 0, smau = 0;
  try { dem = (await api('vagabond.bao_gia.danh_sach', {})).dem || {}; } catch (e) { }
  try { shd = (await api('vagabond.hop_dong.danh_sach', {})).length; } catch (e) { }
  try { stv = (await api('vagabond.bao_gia.tv_danh_sach', {})).ds.length; } catch (e) { }
  try { smau = (await api('vagabond.bao_gia.mau_ds', {})).length; } catch (e) { }
  var o = function (icon, t1, t2, cnt, k) {
    return '<div class="hub" data-k="' + k + '"><div class="hi">' + icon + '</div>' +
      '<div class="ht"><div class="h1">' + h(t1) + '</div><div class="h2">' + h(t2) + '</div></div>' +
      (cnt ? '<span class="bdg">' + cnt + '</span>' : '') +
      '<span class="fc" style="color:#c3c8d4;font-size:22px">&#8250;</span></div>';
  };
  var html = '<div class="sec">Trước khi ký</div><div class="card">' +
    o('💬', 'Báo giá khách doanh nghiệp', 'Chọn món có hình từ danh mục, xuất PDF song ngữ, gửi thẳng email cho khách', dem.cho_khach || 0, 'BG') +
    o('📚', 'Thư viện báo giá', 'Món thiết kế riêng và các khoản phí nhân công, vận chuyển, set up, khuôn: có hình, song ngữ, sửa giá được', stv, 'TV') +
    o('🗂️', 'Mẫu báo giá', 'Hợp đồng nào quy trình cũng giống nhau thì lưu thành mẫu, tờ sau app tự điền hết', smau, 'MAU') +
    '</div>';
  html += '<div class="sec">Sau khi ký</div><div class="card">' +
    o('📑', 'Hợp đồng đã ký', 'Event, catering, teabreak, bánh thiết kế, B2B sỉ: gắn hoá đơn, theo dõi tiền về', shd, 'HDCU') +
    '</div>';
  html += '<div class="sec">Cài đặt</div><div class="card">' +
    o('⚙️', 'Câu chữ khung tờ báo giá', 'Lời mở đầu, điều khoản thanh toán, chính sách huỷ, timeline mẫu: khai một lần dùng cho mọi tờ', 0, 'CD') +
    '</div>';
  html += '<div class="sec">Đang có trên hệ</div><div class="card" style="padding:12px 14px">' +
    '<div style="display:flex;justify-content:space-between;margin-bottom:6px"><span>Báo giá</span><b>' + (dem.tat_ca || 0) + ' tờ</b></div>' +
    '<div style="display:flex;justify-content:space-between;margin-bottom:6px"><span>Đang chờ khách trả lời</span><b style="color:#b45309">' + (dem.cho_khach || 0) + '</b></div>' +
    '<div style="display:flex;justify-content:space-between;margin-bottom:6px"><span>Khách đã duyệt</span><b style="color:#0a8a4a">' + (dem.duyet || 0) + '</b></div>' +
    '<div style="display:flex;justify-content:space-between"><span>Hợp đồng</span><b>' + shd + '</b></div></div>';
  var b = frame('Quản lý hợp đồng mua bán', html);
  b.addEventListener('click', function (e) {
    var c = e.target.closest('[data-k]'); if (!c) return;
    var k = c.getAttribute('data-k');
    if (k === 'BG') return go(scrBaoGia);
    if (k === 'TV') return go(scrThuVien);
    if (k === 'MAU') return go(scrMauBg);
    if (k === 'HDCU') return go(scrHopDong);
    if (k === 'CD') return go(scrBgCaiDat);
  });
}

/* ---------- Danh sach bao gia: chip loc theo viec can lam ---------- */
var bgLoc = null, bgTT = null, bgTim = '', bgTimNet = 0, bgBanCu = 0;
async function scrBaoGia() {
  frame('Báo giá', '<div class="emp"><div class="e1">⏳</div><div>Đang tải báo giá...</div></div>');
  var kq, ci;
  try {
    ci = await bgCaiDat();
    kq = await api('vagabond.bao_gia.danh_sach', { loc: bgLoc || '', trang_thai: bgTT || '', tim: bgTim || '', ban_cu: bgBanCu ? 1 : '' });
  } catch (e) { frame('Báo giá', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var d = kq.dem, ds = kq.ds;

  /* Chip VIEC CAN LAM dat truoc chip trang thai: mo man ra la thay ngay
     to nao dang cho khach, to nao sap het hieu luc (anh Viet 14/08/2026
     hoi "thêm các chip lọc, chip trạng thái mà em thấy hợp lý nhất"). */
  var c1 = '';
  [['', 'Tất cả', d.tat_ca], ['cho_khach', '⏳ Chờ khách trả lời', d.cho_khach],
   ['sap_het', '🔔 Sắp hết hiệu lực', d.sap_het], ['qua_han', '⚠️ Quá hạn', d.qua_han],
   ['cua_toi', '👤 Tờ của tôi', d.cua_toi], ['gia_tri', '💰 Giá trị lớn nhất', 0]
  ].forEach(function (x) {
    c1 += posChipNut('data-bgl="' + x[0] + '"', h(x[1]) + (x[2] ? ' · ' + x[2] : ''), (bgLoc || '') === x[0] && !bgTT);
  });
  var c2 = '';
  ci.trang_thai.forEach(function (t) {
    c2 += posChipNut('data-bgt="' + h(t) + '"', (BGTT_ICON[t] || '') + ' ' + h(t) + ' · ' + (d['tt:' + t] || 0), bgTT === t);
  });
  /* Mac dinh danh sach chi hien ban moi nhat cua moi cuoc thuong luong.
     Chip nay mo cac vong cu ra khi can tra lai da noi gi voi khach. */
  if (d.ban_cu || bgBanCu) c1 += posChipNut('data-bgcu="1"', '🕓 Xem cả bản cũ · ' + d.ban_cu, !!bgBanCu);

  var html = '<div class="card" style="padding:12px 14px;display:grid;gap:9px">' +
    '<input ' + BGO + ' id="bgTim" placeholder="Tìm theo tên khách, tiêu đề hoặc mã tờ..." value="' + h(bgTim) + '">' +
    '<div ' + BGNHAN + '>Việc cần làm</div>' + kmHangChip(c1) +
    '<div ' + BGNHAN + '>Trạng thái</div>' + kmHangChip(c2) + '</div>';
  html += '<div class="sec">' + ds.length + ' báo giá</div><div class="card">';
  if (!ds.length) html += '<div class="emp" style="padding:24px"><div class="e1">💬</div><div>Không có tờ nào ở bộ lọc này. Bấm dấu ➕ để lập tờ mới.</div></div>';
  ds.forEach(function (r) {
    var canh = r.qua_han ? '<b style="color:#b3261e"> · QUÁ HẠN</b>'
      : (r.sap_het ? '<b style="color:#b45309"> · còn ' + r.con_ngay + ' ngày</b>' : '');
    var vong = r.phien_ban > 1 ? '<span style="font-size:11px;font-weight:700;color:#7c3aed;background:#f3edff;border-radius:6px;padding:1px 6px;margin-left:5px">vòng ' + r.phien_ban + '</span>' : '';
    var cu = r.la_ban_cu ? '<span style="font-size:11px;font-weight:700;color:#6b7280;background:#f1f2f5;border-radius:6px;padding:1px 6px;margin-left:5px">bản cũ</span>' : '';
    html += '<div class="hub" data-bg="' + h(r.name) + '"' + (r.la_ban_cu ? ' style="opacity:.62"' : '') + '><div class="hi">' + (r.la_ban_cu ? '🕓' : (BGTT_ICON[r.trang_thai] || '💬')) + '</div>' +
      '<div class="ht"><div class="h1">' + h(r.ten) + vong + cu + '</div>' +
      '<div class="h2">' + h(r.name) + ' · ' + h(r.ten_khach || r.khach_hang || 'Chưa có khách') + '</div>' +
      '<div class="h2">' + h(r.trang_thai) + ' · ' + bgNgayVn(r.ngay_bao_gia) + canh +
      (r.hop_dong ? ' · ' + h(r.hop_dong) : '') + '</div></div>' +
      '<b style="white-space:nowrap;font-size:13px">' + money(r.tong_cong) + '</b></div>';
  });
  html += '</div>';
  var b = frame('Báo giá', html, ci.duoc_sua ? { action: '➕', onAction: function () { bgMoiHoi(); } } : {});
  var ti = document.getElementById('bgTim');
  if (ti) {
    var hen = null;
    ti.oninput = function () {
      clearTimeout(hen);
      var v = ti.value;
      hen = setTimeout(function () { bgTim = v; bgTimNet = 1; go(scrBaoGia, true); }, 450);
    };
    /* Ve lai man la o tim bi dung mat, phai tra con tro ve cuoi dong -
       khong thi go duoc mot chu lai phai bam vao o mot lan. */
    if (bgTimNet) {
      bgTimNet = 0;
      setTimeout(function () {
        try { ti.focus(); ti.setSelectionRange(ti.value.length, ti.value.length); } catch (e) { }
      }, 30);
    }
  }
  b.addEventListener('click', function (e) {
    if (e.target.closest('[data-bgcu]')) { bgBanCu = bgBanCu ? 0 : 1; return go(scrBaoGia, true); }
    var cl = e.target.closest('[data-bgl]');
    if (cl) { bgLoc = cl.getAttribute('data-bgl') || null; bgTT = null; return go(scrBaoGia, true); }
    var ct = e.target.closest('[data-bgt]');
    if (ct) { bgTT = (bgTT === ct.getAttribute('data-bgt')) ? null : ct.getAttribute('data-bgt'); bgLoc = null; return go(scrBaoGia, true); }
    var r = e.target.closest('[data-bg]'); if (!r) return;
    var nm = r.getAttribute('data-bg');
    go(function () { scrBgXem(nm); });
  });
}

/* ---------- Xem mot to ---------- */
async function scrBgXem(name) {
  frame('Báo giá', '<div class="emp"><div class="e1">⏳</div></div>');
  var d, ci, ls;
  try {
    ci = await bgCaiDat();
    d = await api('vagabond.bao_gia.chi_tiet', { name: name });
    ls = await api('vagabond.bao_gia.lich_su', { name: name });
  }
  catch (e) { frame('Báo giá', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không đọc được') + '</div></div>'); return; }

  /* Bang canh bao dat TREN CUNG, truoc ca tieu de: mo to ra la nguoi dung
     biet ngay minh dang cam ban nao, khong doc nham roi bao gia nham cho
     khach. Mau xam cho ban lich su, mau tim cho ban dang song co nhieu vong. */
  var html = '';
  if (d.thay_the_boi) {
    html += '<div class="card" style="padding:11px 13px;background:#f1f2f5;border-left:4px solid #9aa0ac;line-height:1.55">' +
      '<div style="font-weight:700;font-size:14px">🕓 Bản lịch sử · vòng ' + d.phien_ban + ', chỉ xem</div>' +
      '<div style="font-size:13px;color:#4b5563;margin-top:3px">Đây là bản đã gửi khách ở vòng ' + d.phien_ban + ' và đã được thay bằng <b>' + h(d.thay_the_boi) + '</b>. Bản này giữ nguyên từng dòng làm bằng chứng, không sửa và không xoá được.</div>' +
      (d.ly_do_sua ? '<div style="font-size:13px;color:#4b5563;margin-top:3px">Lý do mở vòng này: ' + h(d.ly_do_sua) + '</div>' : '') +
      '<button class="btn gh" id="bgToiMoi" style="margin:9px 0 0;padding:7px 10px;font-size:13.5px">Mở bản mới nhất ' + h(d.thay_the_boi) + ' &#8250;</button></div>';
  } else if (d.phien_ban > 1) {
    html += '<div class="card" style="padding:11px 13px;background:#f8f4ff;border-left:4px solid #7c3aed;line-height:1.55">' +
      '<div style="font-weight:700;font-size:14px">🟣 Vòng ' + d.phien_ban + ' · bản đang có hiệu lực</div>' +
      (d.ly_do_sua ? '<div style="font-size:13px;color:#4b5563;margin-top:3px">Mở vòng này vì: ' + h(d.ly_do_sua) + '</div>' : '') +
      '<div style="font-size:13px;color:#4b5563;margin-top:3px">Các vòng trước vẫn còn nguyên trong mục Lịch sử thương lượng bên dưới.</div></div>';
  } else if (d.khoa) {
    html += '<div class="card" style="padding:11px 13px;background:#fff8ec;border-left:4px solid #d97706;line-height:1.55">' +
      '<div style="font-weight:700;font-size:14px">🔒 Khách đã cầm bản này</div>' +
      '<div style="font-size:13px;color:#4b5563;margin-top:3px">' + h(d.ly_do_khoa) + ' Cần đổi giá hay đổi món thì bấm <b>Tạo phiên bản kế tiếp</b>, bản khách đang cầm vẫn giữ nguyên.</div></div>';
  }
  html += '<div class="card" style="padding:12px 14px;line-height:1.7">' +
    '<div style="display:flex;justify-content:space-between;gap:8px;align-items:center">' +
    '<b style="flex:1">' + h(d.ten) + '</b>' +
    '<button class="btn gh" id="bgTt" style="margin:0;padding:4px 10px;font-size:13px;width:auto;flex:none;white-space:nowrap">' + h(d.trang_thai) + ' ▾</button></div>' +
    (d.ten_en ? '<div style="font-size:13px;color:#8a8f9c;font-style:italic">' + h(d.ten_en) + '</div>' : '') +
    '<div style="color:#6b7280;font-size:13px">' + h(d.name) + ' · lập ngày ' + bgNgayVn(d.ngay_bao_gia) + (d.song_ngu ? ' · song ngữ' : ' · chỉ tiếng Việt') + '</div>' +
    '<div style="font-size:13px"><b>' + h(d.ten_khach || d.khach_hang || '') + '</b>' + (d.ma_so_thue ? ' · MST ' + h(d.ma_so_thue) : '') + '</div>' +
    (d.nguoi_lien_he ? '<div style="font-size:13px">' + h(d.nguoi_lien_he) + (d.chuc_vu ? ' - ' + h(d.chuc_vu) : '') + (d.dien_thoai ? ' · ' + h(d.dien_thoai) : '') + '</div>' : '') +
    (d.email ? '<div style="font-size:13px">' + h(d.email) + '</div>' : '') +
    (d.hieu_luc_den ? '<div style="font-size:13px">Hiệu lực đến ' + bgNgayVn(d.hieu_luc_den) + '</div>' : '') +
    (d.hop_dong ? '<div style="font-size:13px;color:#0a8a4a">Đã lên hợp đồng ' + h(d.hop_dong) + '</div>' : '') +
    '</div>';
  html += '<div class="sec">' + d.dong.length + ' dòng</div><div class="card">';
  d.dong.forEach(function (x) {
    html += '<div class="hub" style="cursor:default">' + bgAnhO(x.hinh, 42) + '<div class="ht" style="margin-left:10px"><div class="h1">' + h(x.ten_mon) + (x.loai === 'Phí' ? ' <span style="font-size:11px;color:#b45309">(phí)</span>' : '') + '</div>' +
      (x.ten_en ? '<div class="h2" style="font-style:italic">' + h(x.ten_en) + '</div>' : '') +
      '<div class="h2">' + money(x.so_luong) + ' ' + h(x.dvt || '') + ' × ' + money(x.don_gia) + ' đ' +
      (x.chiet_khau ? ' · CK ' + x.chiet_khau + '%' : '') + '</div></div>' +
      '<b style="white-space:nowrap;font-size:13px">' + money(x.thanh_tien) + '</b></div>';
  });
  html += '</div>';
  html += '<div class="card" style="padding:12px 14px">' +
    '<div style="display:flex;justify-content:space-between"><span>Cộng tiền hàng</span><b>' + money(d.tam_tinh) + ' đ</b></div>' +
    (d.chiet_khau_tien ? '<div style="display:flex;justify-content:space-between;margin-top:6px"><span>Chiết khấu ' + d.chiet_khau_pt + '%</span><b>-' + money(d.chiet_khau_tien) + ' đ</b></div>' : '') +
    (d.phi_giao ? '<div style="display:flex;justify-content:space-between;margin-top:6px"><span>Phí giao hàng</span><b>' + money(d.phi_giao) + ' đ</b></div>' : '') +
    (d.thue_tien ? '<div style="display:flex;justify-content:space-between;margin-top:6px"><span>Thuế GTGT ' + d.thue_pt + '%</span><b>' + money(d.thue_tien) + ' đ</b></div>' : '<div style="font-size:12.5px;color:#8a8f9c;margin-top:6px">Đơn giá đã bao gồm VAT</div>') +
    '<hr><div style="display:flex;justify-content:space-between"><span><b>TỔNG CỘNG</b></span><b style="font-size:17px">' + money(d.tong_cong) + ' đ</b></div>' +
    (d.dat_coc_tien ? '<div style="display:flex;justify-content:space-between;margin-top:6px"><span>Đặt cọc ' + d.dat_coc_pt + '%</span><b style="color:#0a8a4a">' + money(d.dat_coc_tien) + ' đ</b></div>' : '') +
    '</div>';
  if (d.dich_vu.length) {
    html += '<div class="sec">Dịch vụ thêm</div><div class="card" style="padding:12px 14px">';
    d.dich_vu.forEach(function (x) {
      html += '<div style="display:flex;justify-content:space-between;gap:10px;margin-bottom:6px"><span style="flex:1">' + h(x.ten_vi) + '</span><b style="white-space:nowrap">' + h(x.gia_vi) + '</b></div>';
    });
    html += '</div>';
  }
  if (d.moc.length) {
    html += '<div class="sec">Quy trình vận hành</div><div class="card" style="padding:12px 14px">';
    d.moc.forEach(function (x) {
      html += '<div style="margin-bottom:8px"><div ' + BGNHAN + '>' + h(x.moc_vi) + ' · ' + h(x.trach_nhiem) + '</div><div style="font-size:13.5px">' + h(x.noi_dung_vi) + '</div></div>';
    });
    html += '</div>';
  }

  /* ---- Lich su thuong luong: cai anh Viet muon nhat o tinh nang nay ----
     Moi vong mot dong, kem muc chiet khau va so tien chenh so voi vong
     lien truoc. Con so chenh do MAY CHU tinh (QT-19), day chi in ra. */
  if (ls.so_vong > 1) {
    html += '<div class="sec">Lịch sử thương lượng · ' + ls.so_vong + ' vòng</div><div class="card" style="padding:10px 12px">';
    ls.ds.forEach(function (v) {
      var chenh = v.chenh > 0 ? '<span style="color:#b45309">+' + money(v.chenh) + ' đ</span>'
        : (v.chenh < 0 ? '<span style="color:#0a8a4a">' + money(v.chenh) + ' đ</span>' : '');
      html += '<div style="display:flex;gap:10px;align-items:flex-start;padding:8px 0' + (v.dang_xem ? ';background:#f8f4ff;border-radius:10px;padding-left:8px;padding-right:8px' : '') + '">' +
        '<div style="flex:none;width:30px;height:30px;border-radius:50%;background:' + (v.la_moi_nhat ? '#7c3aed' : '#c3c8d4') + ';color:#fff;font-weight:700;font-size:12.5px;display:flex;align-items:center;justify-content:center">v' + v.phien_ban + '</div>' +
        '<div style="flex:1;min-width:0">' +
        '<div style="font-size:13.5px;font-weight:600">' + h(v.name) + (v.dang_xem ? ' <span style="font-size:11px;color:#7c3aed">đang xem</span>' : '') + '</div>' +
        '<div ' + BGNHAN + '>' + h(v.trang_thai) + ' · ' + bgNgayVn(v.ngay_bao_gia) +
        (v.chiet_khau_pt ? ' · chiết khấu ' + v.chiet_khau_pt + '%' : ' · không chiết khấu') +
        (v.phi_giao ? ' · phí giao ' + money(v.phi_giao) + ' đ' : '') + '</div>' +
        (v.ly_do_sua ? '<div style="font-size:12.5px;color:#4b5563;margin-top:2px">' + h(v.ly_do_sua) + '</div>' : '') +
        '</div>' +
        '<div style="text-align:right;white-space:nowrap"><b style="font-size:13px">' + money(v.tong_cong) + ' đ</b>' +
        (chenh ? '<div style="font-size:12px">' + chenh + '</div>' : '') + '</div>' +
        '</div>' +
        (v.dang_xem ? '' : '<button class="btn gh" data-vong="' + h(v.name) + '" style="margin:0 0 6px;padding:5px 9px;font-size:12.5px">Mở ' + h(v.name) + ' &#8250;</button>');
    });
    html += '</div>';
  }

  var chan = '<button class="btn" id="bgPdf" style="margin:0;flex:1">📄 Xuất PDF</button>';
  if (ci.duoc_sua && !d.thay_the_boi) {
    /* To da khoa thi nut chinh doi thanh "Tao phien ban ke tiep": sales
       khong phai di tim trong menu ⋯ moi lam duoc viec duy nhat con lai. */
    chan += d.khoa
      ? '<button class="btn" id="bgVong" style="margin:0;flex:1.3">🟣 Tạo phiên bản kế tiếp</button>'
      : '<button class="btn gh" id="bgSua" style="margin:0;flex:1">✏️ Sửa</button>';
  }
  if (ci.duoc_sua) chan += '<button class="btn gh" id="bgMenu" style="margin:0;flex:.8">⋯</button>';
  var b = frame('Báo giá', html, { footer: '<div style="display:flex;gap:8px">' + chan + '</div>' });

  var bm = document.getElementById('bgToiMoi');
  if (bm) bm.onclick = function () { go(function () { scrBgXem(d.thay_the_boi); }); };
  var bs = document.getElementById('bgSua');
  if (bs) bs.onclick = function () { bgTay = null; go(function () { scrBgSua(name); }); };
  var bv = document.getElementById('bgVong');
  if (bv) bv.onclick = function () { bgTaoPhienBan(d); };
  b.addEventListener('click', function (e) {
    var vn = e.target.closest('[data-vong]');
    if (vn) { var t = vn.getAttribute('data-vong'); go(function () { scrBgXem(t); }); }
  });

  document.getElementById('bgPdf').onclick = async function () {
    busy(true);
    try { var fl = await api('vagabond.bao_gia.xuat_pdf', { name: name }); busy(false); bcTaiVe(fl.ten_file, fl.b64, fl.kieu); toast('Đã tải ' + fl.ten_file, 4000); }
    catch (e) { busy(false); baoTin((e && e.message) || 'Xuất PDF lỗi'); }
  };
  var tt = document.getElementById('bgTt');
  if (tt) tt.onclick = function () {
    if (!ci.duoc_sua) return baoTin('Anh chị chỉ có quyền xem báo giá.');
    sheet('Đổi trạng thái', ci.trang_thai.map(function (t) { return { value: t, label: t, icon: BGTT_ICON[t] || '📌' }; }), d.trang_thai, async function (o) {
      busy(true);
      try { await api('vagabond.bao_gia.doi_trang_thai', { name: name, trang_thai: o.value }); busy(false); }
      catch (e) { busy(false); baoTin((e && e.message) || 'Lỗi'); }
      go(function () { scrBgXem(name); }, true);
    });
  };
  var mn = document.getElementById('bgMenu');
  if (mn) mn.onclick = function () {
    /* Ban lich su chi con hai viec lam duoc: xem lai va nhan ban sang khach
       khac. Khong bay ra nhung nut ma bam vao chi de nhan cau bao loi. */
    var muc = [];
    if (!d.thay_the_boi) {
      if (d.khoa) muc.push({ value: 'vong', label: 'Tạo phiên bản kế tiếp', icon: '🟣' });
      else muc.push({ value: 'sua', label: 'Sửa báo giá', icon: '✏️' });
    }
    muc.push({ value: 'mail', label: 'Gửi email cho khách kèm PDF', icon: '📧' });
    muc.push({ value: 'copy', label: 'Nhân bản sang khách khác', icon: '📋' });
    if (!d.thay_the_boi) {
      muc.push({ value: 'hd', label: 'Chốt thành hợp đồng', icon: '📑' });
      muc.push({ value: 'mau', label: 'Lưu thành mẫu báo giá', icon: '🗂️' });
      muc.push({ value: 'xoa', label: 'Xoá báo giá nháp', icon: '🗑️' });
    }
    sheet('Việc với báo giá ' + name, muc, null, async function (o) {
      if (o.value === 'vong') return bgTaoPhienBan(d);
      if (o.value === 'mau') return bgLuuMau(name);
      if (o.value === 'sua') { bgTay = null; return go(function () { scrBgSua(name); }); }
      if (o.value === 'copy') {
        busy(true);
        try { var nm = await api('vagabond.bao_gia.nhan_ban', { name: name }); busy(false); toast('Đã nhân bản thành ' + nm); bgTay = null; go(function () { scrBgSua(nm); }); }
        catch (e) { busy(false); baoTin((e && e.message) || 'Lỗi'); }
        return;
      }
      if (o.value === 'xoa') {
        if (!await hoiCo('Xoá báo giá', 'Xoá hẳn báo giá ' + name + '? Chỉ xoá được tờ còn ở trạng thái Nháp.', 'Xoá', true)) return;
        busy(true);
        try { await api('vagabond.bao_gia.xoa', { name: name }); busy(false); toast('Đã xoá'); go(scrBaoGia, true); }
        catch (e) { busy(false); baoTin((e && e.message) || 'Không xoá được'); }
        return;
      }
      if (o.value === 'mail') return bgGuiMail(d);
      if (o.value === 'hd') return bgChotHopDong(d);
    });
  };
}

/* ---------- Mo mot vong thuong luong moi ---------- */
async function bgTaoPhienBan(d) {
  var vong = (Number(d.phien_ban) || 1) + 1;
  var ly = await hoiChu('Mở vòng ' + vong,
    'Bản ' + d.name + ' sẽ được giữ nguyên từng dòng làm bằng chứng về những gì đã gửi khách. Một bản mới mang toàn bộ nội dung sẽ được tạo để sửa thoải mái. Ghi lại vì sao mở vòng này để sau còn tra.',
    '', { nhieu_dong: true, bat_buoc: true, goi_y: 'Vd: Khách xin giảm 5% và bỏ phần bánh mặn.' });
  if (ly === null) return;
  if (!(ly || '').trim()) return baoTin('Phải ghi lý do mở vòng mới thì mới lưu được vào lịch sử thương lượng.');
  busy(true);
  var kq;
  try { kq = await api('vagabond.bao_gia.tao_phien_ban', { name: d.name, ly_do: ly }); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Không mở được vòng mới'); }
  busy(false);
  toast('Đã mở vòng ' + kq.phien_ban + ': ' + kq.name + '. Bản ' + kq.cu + ' đã đóng băng.', 5000);
  bgTay = null; bgMoRong = {};
  go(function () { scrBgSua(kq.name); });
}

async function bgGuiMail(d) {
  var em = await hoiChu('Gửi báo giá qua email', 'Tờ PDF ' + d.name + ' sẽ được đính kèm và gửi tới địa chỉ dưới đây.', d.email || '', { kieu: 'email', goi_y: 'ten@congty.com', bat_buoc: true });
  if (em === null) return;
  var loi = await hoiChu('Lời nhắn thêm (không bắt buộc)', 'Câu này nằm trong thân thư, trên phần chào cuối.', '', { nhieu_dong: true, goi_y: 'Vd: Bên em còn giữ giá này tới hết ngày 30/08 ạ.' });
  if (loi === null) return;
  if (!await hoiCo('Xác nhận gửi', 'Gửi báo giá ' + d.name + ' (' + money(d.tong_cong) + ' đ) tới ' + em + '?', 'Gửi thư')) return;
  busy(true);
  try { var r = await api('vagabond.bao_gia.gui_email', { name: d.name, email: em, loi_nhan: loi || '' }); busy(false); toast('Đã gửi tới ' + r.toi, 4500); go(function () { scrBgXem(d.name); }, true); }
  catch (e) { busy(false); baoTin((e && e.message) || 'Gửi thư lỗi'); }
}

async function bgChotHopDong(d) {
  if (!d.khach_hang) return baoTin('Hợp đồng phải gắn với một khách hàng có trong hệ thống. Bấm Sửa báo giá, chọn lại ô Khách hàng rồi quay lại nhé.');
  var so = await hoiChu('Số hợp đồng', 'Nhập số hợp đồng hai bên đã thống nhất (để trống cũng được).', '', { goi_y: 'Vd 026-022/PYR-VAGABOND' });
  if (so === null) return;
  var nsk = await hoiNgay(today());
  if (nsk === null) return;
  busy(true);
  try {
    var nm = await api('vagabond.bao_gia.tao_hop_dong', { name: d.name, so_hop_dong: so || '', ngay_ky: today(), ngay_su_kien: nsk });
    busy(false); toast('Đã tạo hợp đồng ' + nm, 4000);
    go(function () { scrHdView(nm); }, true);
  } catch (e) { busy(false); baoTin((e && e.message) || 'Không tạo được hợp đồng'); }
}

/* ---------- Soan bao gia: moi dong nhap thang tai cho ---------- */
var bgTay = null, bgMoRong = {};

function bgTinh() {
  if (!bgTay) return;
  var tam = 0;
  (bgTay.dong || []).forEach(function (x) {
    x.so_luong = Number(x.so_luong) || 0;
    x.don_gia = Number(x.don_gia) || 0;
    x.chiet_khau = Number(x.chiet_khau) || 0;
    x.thanh_tien = Math.round(x.so_luong * x.don_gia * (1 - x.chiet_khau / 100));
    tam += x.thanh_tien;
  });
  bgTay.tam_tinh = tam;
  bgTay.chiet_khau_tien = Math.round(tam * (Number(bgTay.chiet_khau_pt) || 0) / 100);
  var sau = tam - bgTay.chiet_khau_tien;
  if (bgTay.gia_da_gom_vat) { bgTay.thue_tien = 0; bgTay.tong_cong = sau + (Number(bgTay.phi_giao) || 0); }
  else { bgTay.thue_tien = Math.round(sau * (Number(bgTay.thue_pt) || 0) / 100); bgTay.tong_cong = sau + bgTay.thue_tien + (Number(bgTay.phi_giao) || 0); }
  bgTay.dat_coc_tien = Math.round(bgTay.tong_cong * (Number(bgTay.dat_coc_pt) || 0) / 100);
}

/* Doc het o nhap tren man ve lai bgTay. Goi truoc moi lan ve lai man, va
   truoc khi luu - de khong bao gio mat chu nguoi dung vua go. */
function bgDoc() {
  if (!bgTay) return;
  var g = function (id) { var el = document.getElementById(id); return el ? el.value : undefined; };
  ['ten', 'ten_en', 'ten_khach', 'ma_so_thue', 'dia_chi', 'nguoi_lien_he', 'chuc_vu',
    'dien_thoai', 'email', 'ngay_bao_gia', 'loi_mo', 'loi_mo_en', 'thanh_toan',
    'thanh_toan_en', 'yeu_cau_vi', 'yeu_cau_en', 'chinh_sach_huy_vi', 'chinh_sach_huy_en',
    'luu_y_vi', 'luu_y_en', 'giao_hang', 'dong_goi', 'ghi_chu', 'ghi_chu_noi_bo',
    'ten_nguoi_lap_in', 'chuc_vu_lap', 'dt_nguoi_lap', 'email_lap'].forEach(function (f) {
      var v = g('bgf_' + f); if (v !== undefined) bgTay[f] = v;
    });
  var hl = g('bgf_hieu_luc_ngay'); if (hl !== undefined) bgTay.hieu_luc_ngay = Number(String(hl).replace(/\D/g, '')) || 30;
  (bgTay.dong || []).forEach(function (x, i) {
    ['ten_mon', 'ten_en', 'dvt', 'dvt_en', 'kich_thuoc', 'mo_ta', 'mo_ta_en',
      'di_ung_vi', 'di_ung_en', 'danh_muc_vi', 'danh_muc_en'].forEach(function (f) {
        var v = g('dg_' + i + '_' + f); if (v !== undefined) x[f] = v;
      });
    ['so_luong', 'don_gia', 'chiet_khau'].forEach(function (f) {
      var v = g('dg_' + i + '_' + f);
      if (v !== undefined) x[f] = vgbSo(v);
    });
  });
  (bgTay.dich_vu || []).forEach(function (x, i) {
    ['ten_vi', 'ten_en', 'gia_vi', 'gia_en'].forEach(function (f) {
      var v = g('dv_' + i + '_' + f); if (v !== undefined) x[f] = v;
    });
  });
  (bgTay.moc || []).forEach(function (x, i) {
    ['moc_vi', 'moc_en', 'noi_dung_vi', 'noi_dung_en'].forEach(function (f) {
      var v = g('mc_' + i + '_' + f); if (v !== undefined) x[f] = v;
    });
  });
  bgTinh();
}

/* Cap nhat khoi tong tien TAI CHO, khong ve lai ca man - ve lai thi o dang
   go bi mat con tro, nguoi dung phai bam lai tung o (loi anh Viet che
   "vẫn quá thô sơ" 14/08/2026). */
function bgTongHien() {
  bgDoc();
  var el = document.getElementById('bgTong');
  if (el) el.innerHTML = bgTongHtml();
  (bgTay.dong || []).forEach(function (x, i) {
    var t = document.getElementById('dg_' + i + '_tt');
    if (t) t.textContent = money(x.thanh_tien) + ' đ';
  });
}

function bgTongHtml() {
  var d = bgTay;
  return '<div style="display:flex;justify-content:space-between"><span>Cộng tiền hàng</span><b>' + money(d.tam_tinh) + ' đ</b></div>' +
    (Number(d.chiet_khau_pt) ? '<div style="display:flex;justify-content:space-between;margin-top:6px"><span>Chiết khấu ' + (Number(d.chiet_khau_pt) || 0) + '%</span><b>-' + money(d.chiet_khau_tien) + ' đ</b></div>' : '') +
    (Number(d.phi_giao) ? '<div style="display:flex;justify-content:space-between;margin-top:6px"><span>Phí giao hàng</span><b>' + money(d.phi_giao) + ' đ</b></div>' : '') +
    (d.gia_da_gom_vat ? '<div style="font-size:12.5px;color:#8a8f9c;margin-top:6px">Đơn giá đã bao gồm VAT, không cộng thêm thuế lên tổng</div>'
      : '<div style="display:flex;justify-content:space-between;margin-top:6px"><span>Thuế GTGT ' + (Number(d.thue_pt) || 0) + '%</span><b>' + money(d.thue_tien) + ' đ</b></div>') +
    '<hr><div style="display:flex;justify-content:space-between"><span><b>TỔNG CỘNG</b></span><b style="font-size:18px">' + money(d.tong_cong) + ' đ</b></div>' +
    (Number(d.dat_coc_pt) ? '<div style="display:flex;justify-content:space-between;margin-top:6px"><span>Đặt cọc ' + (Number(d.dat_coc_pt) || 0) + '%</span><b style="color:#0a8a4a">' + money(d.dat_coc_tien) + ' đ</b></div>' : '');
}

async function bgMoi(nameMau) {
  busy(true);
  try {
    bgTay = nameMau
      ? await api('vagabond.bao_gia.tu_mau', { name_mau: nameMau })
      : await api('vagabond.bao_gia.moi', {});
    busy(false);
  }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Không mở được'); }
  bgMoRong = {};
  if (nameMau) toast('Đã điền sẵn theo mẫu "' + (bgTay.tu_mau || '') + '", giờ chỉ cần chọn khách và sửa số lượng', 5200);
  go(function () { scrBgSua(''); });
}

/* Bam dau cong o man danh sach: co mau thi hoi lap theo mau nao truoc.
   Anh Viet 15/08/2026: *"Thêm tính năng 'Lưu mẫu báo giá' để sau này dùng
   thì áp lên để app tự điền hết các phần thông tin theo mẫu"*. */
async function bgMoiHoi() {
  var ds = [];
  try { ds = await api('vagabond.bao_gia.mau_ds', {}); } catch (e) { }
  if (!ds.length) return bgMoi();
  var muc = [{ value: '', label: 'Tờ trắng, soạn từ đầu', icon: '📄' }];
  ds.forEach(function (m) { muc.push({ value: m.name, label: m.ten_mau || m.name, icon: '🗂️' }); });
  sheet('Lập báo giá mới', muc, null, function (o) { bgMoi(o.value || ''); });
}

/* ---------- Mau bao gia ---------- */
async function scrMauBg() {
  frame('Mẫu báo giá', '<div class="emp"><div class="e1">⏳</div></div>');
  var ds;
  try { ds = await api('vagabond.bao_gia.mau_ds', {}); }
  catch (e) { frame('Mẫu báo giá', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var html = '<div class="card" style="padding:12px 14px;font-size:13.5px;color:#6b7280;line-height:1.65">' +
    'Mẫu giữ sẵn câu chữ, điều khoản, quy trình vận hành, dịch vụ thêm và cả các dòng sản phẩm. ' +
    'Lập tờ mới chọn mẫu là app điền hết, chỉ còn gõ tên khách và số lượng.<br>' +
    'Tạo mẫu: mở một tờ đã soạn đẹp, bấm "⋯ Việc khác" rồi chọn "Lưu thành mẫu".</div>';
  html += '<div class="sec">' + ds.length + ' mẫu</div><div class="card">';
  if (!ds.length) html += '<div class="emp" style="padding:24px"><div class="e1">🗂️</div><div>Chưa có mẫu nào.</div></div>';
  ds.forEach(function (m) {
    html += '<div class="hub" data-m="' + h(m.name) + '"><div class="hi">🗂️</div>' +
      '<div class="ht"><div class="h1">' + h(m.ten_mau || m.name) + '</div>' +
      '<div class="h2">' + h(m.ten || '') + '</div></div>' +
      '<span class="fc" style="color:#c3c8d4;font-size:22px">&#8250;</span></div>';
  });
  html += '</div>';
  var b = frame('Mẫu báo giá', html);
  b.addEventListener('click', function (e) {
    var r = e.target.closest('[data-m]'); if (!r) return;
    var nm = r.getAttribute('data-m');
    var ten = (ds.filter(function (x) { return x.name === nm; })[0] || {}).ten_mau || nm;
    sheet('Mẫu ' + ten, [
      { value: 'dung', label: 'Lập báo giá mới theo mẫu này', icon: '➕' },
      { value: 'xoa', label: 'Xoá mẫu', icon: '🗑️' }
    ], null, async function (o) {
      if (o.value === 'dung') return bgMoi(nm);
      if (!await hoiCo('Xoá mẫu', 'Xoá mẫu "' + ten + '"? Các tờ báo giá đã lập theo mẫu này vẫn giữ nguyên.', 'Xoá', true)) return;
      busy(true);
      try { await api('vagabond.bao_gia.mau_xoa', { name: nm }); busy(false); toast('Đã xoá mẫu'); go(scrMauBg, true); }
      catch (e2) { busy(false); baoTin((e2 && e2.message) || 'Không xoá được'); }
    });
  });
}

async function bgLuuMau(name) {
  var ten = await hoiChu('Lưu thành mẫu',
    'Đặt tên cho mẫu này để lần sau nhận ra ngay. Mẫu giữ câu chữ, điều khoản, quy trình và các dòng sản phẩm, nhưng KHÔNG giữ thông tin khách của tờ hiện tại.',
    '', { bat_buoc: true, goi_y: 'Vd Mẫu trung thu doanh nghiệp' });
  if (!ten) return;
  busy(true);
  try { var r = await api('vagabond.bao_gia.mau_luu', { name: name, ten_mau: ten }); busy(false); toast('Đã lưu mẫu "' + r.ten_mau + '"', 4500); }
  catch (e) { busy(false); baoTin((e && e.message) || 'Không lưu được mẫu'); }
}

function bgOSo(id, gt, rong, tien) {
  /* tien = true thi hien dau cham ngan nghin ngay trong o nhap. */
  var v = tien ? vgbTien(gt) : (gt == null ? '' : gt);
  return '<input id="' + id + '" inputmode="numeric"' + (tien ? ' data-tien="1"' : '') +
    ' style="width:' + (rong || 74) + 'px;box-sizing:border-box;border:1.5px solid #dfe3ec;border-radius:9px;height:38px;padding:0 8px;font-size:14px;font-weight:600;text-align:right;font-family:inherit" value="' + h(v) + '">';
}
/* Go tien toi dau cham dau cham toi do, con tro van o cuoi phan vua go. */
function vgbTienGo(el) {
  if (!el || el.getAttribute('data-tien') !== '1') return;
  var cuoi = el.value.length - (el.selectionStart == null ? 0 : el.selectionStart);
  var n = vgbSo(el.value);
  el.value = n ? vgbTien(n) : '';
  try {
    var v = Math.max(0, el.value.length - cuoi);
    el.setSelectionRange(v, v);
  } catch (e) { }
}
function bgOChu(id, gt, ph, rong) {
  return '<input id="' + id + '" placeholder="' + h(ph || '') + '" style="' + (rong ? 'width:' + rong + ';' : 'flex:1;min-width:0;') + 'box-sizing:border-box;border:1.5px solid #dfe3ec;border-radius:9px;height:38px;padding:0 10px;font-size:14px;font-family:inherit" value="' + h(gt == null ? '' : gt) + '">';
}

async function scrBgSua(name) {
  var ci = await bgCaiDat();
  if (!bgTay) {
    if (!name) return bgMoi();
    frame('Sửa báo giá', '<div class="emp"><div class="e1">⏳</div></div>');
    busy(true);
    try { bgTay = await api('vagabond.bao_gia.chi_tiet', { name: name }); busy(false); }
    catch (e) { busy(false); return baoTin((e && e.message) || 'Không đọc được'); }
    /* Chan ngay o cua man soan: de sales go xong ca to roi moi bao "khong
       luu duoc" la cach nhanh nhat de mat mot buoi lam viec. May chu van
       chan lan nua o ham luu, day chi la chan som cho do dau (QT-19). */
    if (bgTay.khoa) {
      var td = bgTay;
      bgTay = null;
      return go(function () { scrBgXem(td.name); });
    }
  }
  bgTinh();
  var d = bgTay;
  var oi = function (id, ph, val, kieu) {
    return '<input ' + BGO + ' id="bgf_' + id + '" placeholder="' + h(ph) + '" ' +
      (kieu ? 'type="' + kieu + '" ' : '') + 'value="' + h(val == null ? '' : val) + '">';
  };
  var ota = function (id, val, dong) {
    return '<textarea ' + BGTA + ' id="bgf_' + id + '" rows="' + (dong || 3) + '">' + h(val || '') + '</textarea>';
  };

  var html = '';
  if (Number(d.phien_ban) > 1) {
    html += '<div class="card" style="padding:10px 13px;background:#f8f4ff;border-left:4px solid #7c3aed;line-height:1.5">' +
      '<div style="font-weight:700;font-size:13.5px">🟣 Đang soạn vòng ' + d.phien_ban + ' · ' + h(d.name || '') + '</div>' +
      (d.ly_do_sua ? '<div style="font-size:12.5px;color:#4b5563;margin-top:2px">' + h(d.ly_do_sua) + '</div>' : '') +
      '<div style="font-size:12.5px;color:#4b5563;margin-top:2px">Các vòng trước đã đóng băng, sửa ở đây không đụng tới chúng.</div></div>';
  }
  html += '<div class="card" style="padding:12px 14px;display:grid;gap:9px">' +
    oi('ten', 'Tiêu đề báo giá (bắt buộc)', d.ten) +
    (d.song_ngu ? oi('ten_en', 'Title in English', d.ten_en) : '') +
    '<div style="display:flex;flex-direction:row;gap:8px;flex-wrap:wrap">' +
    posChipNut('data-t="songngu"', d.song_ngu ? '🌐 Song ngữ Việt - Anh' : '🇻🇳 Chỉ tiếng Việt', !!d.song_ngu) +
    posChipNut('data-t="vat"', d.gia_da_gom_vat ? 'Đơn giá đã gồm VAT' : 'Đơn giá chưa gồm VAT', !!d.gia_da_gom_vat) +
    (d.song_ngu ? posChipNut('data-t="dichto"', '🌐 Dịch cả tờ sang tiếng Anh', false) : '') +
    '</div>' +
    '<div class="hub" data-t="khach" style="padding:10px 0;border:none"><div class="ht"><div ' + BGNHAN + '>Khách hàng trong hệ thống</div><div class="h1">' + h(d.khach_hang || 'Chọn khách (để trống nếu khách mới)') + '</div></div><span style="color:#c3c8d4">&#8250;</span></div>' +
    oi('ten_khach', 'Tên công ty khách in lên báo giá (bắt buộc)', d.ten_khach) +
    oi('ma_so_thue', 'Mã số thuế khách', d.ma_so_thue) +
    '<textarea ' + BGTA + ' id="bgf_dia_chi" rows="2" placeholder="Địa chỉ khách">' + h(d.dia_chi) + '</textarea>' +
    '</div>';

  html += '<div class="sec">Người đại diện bên mua</div><div class="card" style="padding:12px 14px;display:grid;gap:9px">' +
    oi('nguoi_lien_he', 'Họ tên người đại diện', d.nguoi_lien_he) +
    oi('chuc_vu', 'Chức vụ', d.chuc_vu) +
    oi('dien_thoai', 'Điện thoại', d.dien_thoai, 'tel') +
    oi('email', 'Email nhận báo giá', d.email, 'email') + '</div>';

  var chipHl = '';
  ci.chip_hieu_luc.forEach(function (n) { chipHl += posChipNut('data-hl="' + n + '"', n + ' ngày', Number(d.hieu_luc_ngay) === n); });
  html += '<div class="sec">Ngày và hiệu lực</div><div class="card" style="padding:12px 14px;display:grid;gap:9px">' +
    '<div style="display:flex;flex-direction:row;align-items:center;gap:10px"><span style="width:110px">Ngày báo giá</span><input type="date" class="hin" id="bgf_ngay_bao_gia" value="' + h(d.ngay_bao_gia) + '" style="flex:1;margin:0"></div>' +
    '<div style="display:flex;flex-direction:row;align-items:center;gap:10px"><span style="width:110px">Hiệu lực</span>' + bgOSo('bgf_hieu_luc_ngay', d.hieu_luc_ngay || 30, 90) + '<span>ngày</span></div>' +
    kmHangChip(chipHl) + '</div>';

  /* ---- Cac dong: mot hang nhap thang, khong hoi tung o mot ---- */
  html += '<div class="sec">Sản phẩm và phí · nhập thẳng trên dòng</div>';
  html += '<div class="card" style="padding:8px 10px">';
  if (!d.dong.length) html += '<div class="emp" style="padding:20px"><div class="e1">🥮</div><div>Chưa có dòng nào. Bấm nút bên dưới để chọn nhiều món một lượt.</div></div>';
  d.dong.forEach(function (x, i) {
    var mo = !!bgMoRong[i];
    html += '<div style="border:1.5px solid #eef0f4;border-radius:13px;padding:9px;margin-bottom:8px;background:#fff">' +
      '<div style="display:flex;align-items:flex-start;gap:9px">' +
      '<div data-anh="' + i + '" style="cursor:pointer">' + bgAnhO(x.hinh, 46) + '</div>' +
      '<div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:6px">' +
      '<div style="display:flex;flex-direction:row;gap:6px">' + bgOChu('dg_' + i + '_ten_mon', x.ten_mon, 'Tên sản phẩm') +
      '<button data-xoa="' + i + '" style="flex:none;width:38px;height:38px;border-radius:9px;border:1.5px solid #fecaca;background:#fff;color:#b3261e;font-size:16px;cursor:pointer">🗑</button></div>' +
      (d.song_ngu ? '<div style="display:flex;flex-direction:row;gap:6px">' + bgOChu('dg_' + i + '_ten_en', x.ten_en, 'Name in English') + '</div>' : '') +
      '<div style="display:flex;flex-direction:row;gap:6px;flex-wrap:wrap;align-items:center">' +
      '<span style="font-size:12px;color:#8a8f9c">SL</span>' + bgOSo('dg_' + i + '_so_luong', x.so_luong, 62) +
      bgOChu('dg_' + i + '_dvt', x.dvt, 'đvt', '62px') +
      '<span style="font-size:12px;color:#8a8f9c">Giá</span>' + bgOSo('dg_' + i + '_don_gia', x.don_gia, 116, true) +
      '<span style="font-size:12px;color:#8a8f9c">CK%</span>' + bgOSo('dg_' + i + '_chiet_khau', x.chiet_khau, 52) +
      '<b id="dg_' + i + '_tt" style="margin-left:auto;font-size:14.5px;white-space:nowrap">' + money(x.thanh_tien) + ' đ</b></div>' +
      '<div style="display:flex;flex-direction:row;gap:8px;align-items:center">' +
      posChipNut('data-loai="' + i + '"', x.loai === 'Phí' ? 'Là khoản phí' : 'Là món bánh', x.loai === 'Phí') +
      posChipNut('data-mo="' + i + '"', mo ? 'Thu gọn ▴' : 'Mô tả, dị ứng, kích thước ▾', mo) +
      posChipNut('data-luutv="' + i + '"', '📚 Lưu vào thư viện', false) +
      (d.song_ngu ? posChipNut('data-dich="' + i + '"', '🌐 Dịch dòng này', false) : '') +
      '</div></div></div>';
    if (mo) {
      html += '<div style="margin-top:9px;display:grid;gap:6px;padding-left:4px">' +
        '<div style="display:flex;flex-direction:row;gap:6px">' + bgOChu('dg_' + i + '_kich_thuoc', x.kich_thuoc, 'Kích thước, vd 50g (5x5cm)') + bgOChu('dg_' + i + '_danh_muc_vi', x.danh_muc_vi, 'Danh mục, vd Bánh trung thu') + '</div>' +
        '<textarea ' + BGTA + ' id="dg_' + i + '_mo_ta" rows="3" placeholder="Mô tả tiếng Việt: vỏ bánh, nhân bánh...">' + h(x.mo_ta) + '</textarea>' +
        (d.song_ngu ? '<textarea ' + BGTA + ' id="dg_' + i + '_mo_ta_en" rows="3" placeholder="Description in English">' + h(x.mo_ta_en) + '</textarea>' : '') +
        '<div style="display:flex;flex-direction:row;gap:6px">' + bgOChu('dg_' + i + '_di_ung_vi', x.di_ung_vi, 'Dị ứng, vd Gluten, trứng, đậu nành') + (d.song_ngu ? bgOChu('dg_' + i + '_di_ung_en', x.di_ung_en, 'Allergen') : '') + '</div>' +
        (d.song_ngu ? '<div style="display:flex;flex-direction:row;gap:6px">' + bgOChu('dg_' + i + '_dvt_en', x.dvt_en, 'Unit in English') + bgOChu('dg_' + i + '_danh_muc_en', x.danh_muc_en, 'Category in English') + '</div>' : '') +
        '</div>';
    }
    html += '</div>';
  });
  html += '</div><div class="card" style="padding:10px 14px;display:grid;gap:8px">' +
    '<button class="btn gh" id="bgThem" style="margin:0">➕ Chọn nhiều món từ danh mục và thư viện</button>' +
    '<button class="btn gh" id="bgThemTay" style="margin:0">✍️ Thêm một dòng trống để gõ tay</button></div>';

  /* Anh Viet 15/08/2026: *"các phần bên trong mục này em phải cho thành chip
     để biết đó là chỗ có thể type vào sửa số"*. Chip co vien va co so ben
     trong thi nhin ra ngay la bam duoc; dong chu tron thi khong ai biet. */
  var cSua = function (khoa, nhan, gt) {
    return posChipNut('data-t="' + khoa + '"', h(nhan) + ': <b>' + gt + '</b> ✎', false);
  };
  html += '<div class="sec">Chiết khấu, phí, đặt cọc · bấm vào chip để sửa số</div>' +
    '<div class="card" style="padding:12px 14px">' + kmHangChip(
      cSua('ck', 'Chiết khấu', (Number(d.chiet_khau_pt) || 0) + '%') +
      cSua('phi', 'Phí giao hàng', money(d.phi_giao) + ' đ') +
      cSua('coc', 'Đặt cọc', (Number(d.dat_coc_pt) || 0) + '%') +
      (d.gia_da_gom_vat ? '' : cSua('vatpt', 'Thuế GTGT', (Number(d.thue_pt) || 0) + '%'))
    ) + '</div>';
  html += '<div class="card" style="padding:12px 14px" id="bgTong">' + bgTongHtml() + '</div>';

  /* ---- Dich vu them ---- */
  html += '<div class="sec">Dịch vụ thêm · giá ghi bằng chữ</div><div class="card" style="padding:9px 10px">';
  if (!d.dich_vu.length) html += '<div style="padding:12px;color:#8a8f9c;font-size:13.5px;text-align:center">Chưa có. Ví dụ: phí vận chuyển ngoại thành, packaging miễn phí.</div>';
  d.dich_vu.forEach(function (x, i) {
    html += '<div style="border:1.5px solid #eef0f4;border-radius:12px;padding:8px;margin-bottom:7px;display:grid;gap:6px">' +
      '<div style="display:flex;flex-direction:row;gap:6px">' + bgOChu('dv_' + i + '_ten_vi', x.ten_vi, 'Hạng mục') +
      '<button data-xdv="' + i + '" style="flex:none;width:38px;height:38px;border-radius:9px;border:1.5px solid #fecaca;background:#fff;color:#b3261e;cursor:pointer">🗑</button></div>' +
      (d.song_ngu ? '<div style="display:flex;flex-direction:row;gap:6px">' + bgOChu('dv_' + i + '_ten_en', x.ten_en, 'Description in English') + '</div>' : '') +
      '<div style="display:flex;flex-direction:row;gap:6px">' + bgOChu('dv_' + i + '_gia_vi', x.gia_vi, 'Đơn giá, vd Miễn phí') + (d.song_ngu ? bgOChu('dv_' + i + '_gia_en', x.gia_en, 'vd Free of charge') : '') + '</div></div>';
  });
  html += '<button class="btn gh" id="bgThemDv" style="margin:6px 0 0">➕ Thêm dịch vụ</button></div>';

  /* ---- Timeline ---- */
  html += '<div class="sec">Quy trình vận hành</div><div class="card" style="padding:9px 10px">';
  d.moc.forEach(function (x, i) {
    html += '<div style="border:1.5px solid #eef0f4;border-radius:12px;padding:8px;margin-bottom:7px;display:grid;gap:6px">' +
      '<div style="display:flex;flex-direction:row;gap:6px">' + bgOChu('mc_' + i + '_moc_vi', x.moc_vi, 'Mốc thời gian') +
      '<button data-xmc="' + i + '" style="flex:none;width:38px;height:38px;border-radius:9px;border:1.5px solid #fecaca;background:#fff;color:#b3261e;cursor:pointer">🗑</button></div>' +
      (d.song_ngu ? bgOChu('mc_' + i + '_moc_en', x.moc_en, 'Timeline in English') : '') +
      '<textarea ' + BGTA + ' id="mc_' + i + '_noi_dung_vi" rows="2" placeholder="Nội dung">' + h(x.noi_dung_vi) + '</textarea>' +
      (d.song_ngu ? '<textarea ' + BGTA + ' id="mc_' + i + '_noi_dung_en" rows="2" placeholder="Action in English">' + h(x.noi_dung_en) + '</textarea>' : '') +
      '<div style="display:flex;flex-direction:row;gap:6px;flex-wrap:wrap">' +
      ['Vagabond / Seller', 'Bên mua / Buyer', 'Hai bên / Both parties'].map(function (t) {
        return posChipNut('data-tn="' + i + '|' + t + '"', h(t), x.trach_nhiem === t);
      }).join('') + '</div></div>';
  });
  html += '<button class="btn gh" id="bgThemMoc" style="margin:6px 0 0">➕ Thêm mốc</button></div>';

  /* ---- Cau chu khung to ---- */
  html += '<div class="sec">Câu chữ in lên tờ · đã điền sẵn từ Cài đặt</div><div class="card" style="padding:12px 14px;display:grid;gap:9px">' +
    '<div ' + BGNHAN + '>Lời mở đầu</div>' + ota('loi_mo', d.loi_mo, 3) +
    (d.song_ngu ? ota('loi_mo_en', d.loi_mo_en, 3) : '') +
    '<div ' + BGNHAN + '>Điều khoản thanh toán</div>' + ota('thanh_toan', d.thanh_toan, 3) +
    (d.song_ngu ? ota('thanh_toan_en', d.thanh_toan_en, 3) : '') +
    '<div ' + BGNHAN + '>Yêu cầu vận hành</div>' + ota('yeu_cau_vi', d.yeu_cau_vi, 3) +
    (d.song_ngu ? ota('yeu_cau_en', d.yeu_cau_en, 3) : '') +
    '<div ' + BGNHAN + '>Chính sách huỷ và thay đổi</div>' + ota('chinh_sach_huy_vi', d.chinh_sach_huy_vi, 4) +
    (d.song_ngu ? ota('chinh_sach_huy_en', d.chinh_sach_huy_en, 4) : '') +
    '<div ' + BGNHAN + '>Lưu ý</div>' + ota('luu_y_vi', d.luu_y_vi, 3) +
    (d.song_ngu ? ota('luu_y_en', d.luu_y_en, 3) : '') +
    '<div ' + BGNHAN + '>Giao hàng, đóng gói, ghi chú thêm</div>' +
    ota('giao_hang', d.giao_hang, 2) + ota('dong_goi', d.dong_goi, 2) + ota('ghi_chu', d.ghi_chu, 2) +
    '</div>';

  html += '<div class="sec">Đại diện bên bán ký tờ này</div><div class="card" style="padding:12px 14px;display:grid;gap:9px">' +
    oi('ten_nguoi_lap_in', 'Họ tên in ở ô ký', d.ten_nguoi_lap_in) +
    oi('chuc_vu_lap', 'Chức vụ', d.chuc_vu_lap) +
    oi('dt_nguoi_lap', 'Điện thoại', d.dt_nguoi_lap, 'tel') +
    oi('email_lap', 'Email', d.email_lap, 'email') +
    '<div ' + BGNHAN + '>Ghi chú nội bộ, không in lên tờ</div>' + ota('ghi_chu_noi_bo', d.ghi_chu_noi_bo, 2) + '</div>';

  var b = frame(d.name ? 'Sửa ' + d.name : 'Báo giá mới', html, {
    footer: '<div style="display:flex;gap:8px"><button class="btn gh" id="bgXemPdf" style="margin:0;flex:1">📄 Lưu và xuất PDF</button>' +
      '<button class="btn" id="bgLuu" style="margin:0;flex:1">Lưu báo giá</button></div>'
  });

  /* Go so lieu tren dong thi tinh lai NGAY, khong ve lai man */
  b.addEventListener('input', function (e) {
    var el = e.target;
    if (el && el.getAttribute && el.getAttribute('data-tien') === '1') vgbTienGo(el);
    var id = (el && el.id) || '';
    if (/^dg_\d+_(so_luong|don_gia|chiet_khau)$/.test(id)) bgTongHien();
  });

  b.addEventListener('click', async function (e) {
    var el;
    if ((el = e.target.closest('[data-hl]'))) { bgDoc(); bgTay.hieu_luc_ngay = Number(el.getAttribute('data-hl')); return go(function () { scrBgSua(name); }, true); }
    if (e.target.closest('[data-t="songngu"]')) { bgDoc(); bgTay.song_ngu = bgTay.song_ngu ? 0 : 1; return go(function () { scrBgSua(name); }, true); }
    if (e.target.closest('[data-t="vat"]')) { bgDoc(); bgTay.gia_da_gom_vat = bgTay.gia_da_gom_vat ? 0 : 1; return go(function () { scrBgSua(name); }, true); }
    if (e.target.closest('[data-t="khach"]')) return bgChonKhach(name);
    if ((el = e.target.closest('[data-mo]'))) { bgDoc(); var k = el.getAttribute('data-mo'); bgMoRong[k] = !bgMoRong[k]; return go(function () { scrBgSua(name); }, true); }
    if ((el = e.target.closest('[data-loai]'))) { bgDoc(); var j = +el.getAttribute('data-loai'); bgTay.dong[j].loai = bgTay.dong[j].loai === 'Phí' ? 'Món' : 'Phí'; return go(function () { scrBgSua(name); }, true); }
    if ((el = e.target.closest('[data-xoa]'))) { bgDoc(); bgTay.dong.splice(+el.getAttribute('data-xoa'), 1); bgMoRong = {}; return go(function () { scrBgSua(name); }, true); }
    if ((el = e.target.closest('[data-xdv]'))) { bgDoc(); bgTay.dich_vu.splice(+el.getAttribute('data-xdv'), 1); return go(function () { scrBgSua(name); }, true); }
    if ((el = e.target.closest('[data-xmc]'))) { bgDoc(); bgTay.moc.splice(+el.getAttribute('data-xmc'), 1); return go(function () { scrBgSua(name); }, true); }
    if ((el = e.target.closest('[data-tn]'))) {
      bgDoc(); var p = el.getAttribute('data-tn').split('|');
      bgTay.moc[+p[0]].trach_nhiem = p[1]; return go(function () { scrBgSua(name); }, true);
    }
    if ((el = e.target.closest('[data-anh]'))) return bgDoiAnh(+el.getAttribute('data-anh'), name);
    if ((el = e.target.closest('[data-luutv]'))) return bgLuuThuVien(+el.getAttribute('data-luutv'), name);
    if ((el = e.target.closest('[data-dich]'))) return bgDichDong(+el.getAttribute('data-dich'), name);
    if (e.target.closest('[data-t="dichto"]')) return bgDichTo(name);
    if (e.target.closest('[data-t="ck"]')) {
      bgDoc();
      var v = await hoiSo('Chiết khấu tổng', 'Phần trăm chiết khấu trên tổng tiền hàng (0 tới 100).', bgTay.chiet_khau_pt || 0);
      if (v === null) return; bgTay.chiet_khau_pt = Math.min(100, Math.max(0, v));
      return go(function () { scrBgSua(name); }, true);
    }
    if (e.target.closest('[data-t="phi"]')) {
      bgDoc();
      var p2 = await hoiSo('Phí giao hàng', 'Số tiền phí giao cộng thêm vào tổng.', bgTay.phi_giao || 0);
      if (p2 === null) return; bgTay.phi_giao = p2;
      return go(function () { scrBgSua(name); }, true);
    }
    if (e.target.closest('[data-t="coc"]')) {
      bgDoc();
      var c2 = await hoiSo('Đặt cọc', 'Phần trăm đặt cọc. Số tiền cọc in lên tờ và mã QR sinh đúng số đó.', bgTay.dat_coc_pt || 0);
      if (c2 === null) return; bgTay.dat_coc_pt = Math.min(100, Math.max(0, c2));
      return go(function () { scrBgSua(name); }, true);
    }
    if (e.target.closest('[data-t="vatpt"]')) {
      bgDoc();
      var v2 = await hoiSo('Thuế GTGT', 'Phần trăm thuế cộng lên tổng.', bgTay.thue_pt || 8);
      if (v2 === null) return; bgTay.thue_pt = Math.min(100, Math.max(0, v2));
      return go(function () { scrBgSua(name); }, true);
    }
  });

  document.getElementById('bgThem').onclick = async function () {
    bgDoc();
    var ds = await vgbChonMon({ tieu_de: 'Chọn sản phẩm và phí', nhieu: true, ke_thu_vien: 1 });
    if (!ds.length) return;
    ds.forEach(function (m) {
      bgTay.dong.push({
        loai: (m.loai === 'Món' || !m.loai) ? 'Món' : 'Phí',
        ma_mon: m.nguon === 'item' ? m.ma : (m.ma_item || ''),
        ma_tv: m.nguon === 'thu_vien' ? m.ma : '',
        ten_mon: m.ten, ten_en: m.ten_en || '', dvt: m.dvt || '', dvt_en: m.dvt_en || '',
        hinh: m.hinh || '', kich_thuoc: m.kich_thuoc || '',
        mo_ta: m.mo_ta || '', mo_ta_en: m.mo_ta_en || '',
        di_ung_vi: m.di_ung_vi || '', di_ung_en: m.di_ung_en || '',
        danh_muc_vi: m.nguon === 'item' ? (m.nhom || '') : '', danh_muc_en: '',
        so_luong: 1, don_gia: m.gia || 0, chiet_khau: 0, thanh_tien: 0
      });
    });
    toast('Đã thêm ' + ds.length + ' dòng, giờ chỉ cần gõ số lượng', 3500);
    go(function () { scrBgSua(name); }, true);
  };
  document.getElementById('bgThemTay').onclick = function () {
    bgDoc();
    bgTay.dong.push({ loai: 'Món', ma_mon: '', ma_tv: '', ten_mon: '', ten_en: '', dvt: '', dvt_en: '', hinh: '', kich_thuoc: '', mo_ta: '', mo_ta_en: '', di_ung_vi: '', di_ung_en: '', danh_muc_vi: '', danh_muc_en: '', so_luong: 1, don_gia: 0, chiet_khau: 0, thanh_tien: 0 });
    go(function () { scrBgSua(name); }, true);
  };
  document.getElementById('bgThemDv').onclick = function () {
    bgDoc(); bgTay.dich_vu.push({ ten_vi: '', ten_en: '', gia_vi: '', gia_en: '' });
    go(function () { scrBgSua(name); }, true);
  };
  document.getElementById('bgThemMoc').onclick = function () {
    bgDoc(); bgTay.moc.push({ moc_vi: '', moc_en: '', noi_dung_vi: '', noi_dung_en: '', trach_nhiem: 'Vagabond / Seller' });
    go(function () { scrBgSua(name); }, true);
  };
  document.getElementById('bgLuu').onclick = function () { bgLuu(false); };
  document.getElementById('bgXemPdf').onclick = function () { bgLuu(true); };
}

/* Dich mot dong. Chi dien vao o tieng Anh dang de trong. */
async function bgDichDong(i, name) {
  bgDoc();
  var x = bgTay.dong[i]; if (!x) return;
  var viec = bgCanDich(x, BGCAP_DONG, []);
  if (!viec.length) return baoTin('Dòng này đã có đủ phần tiếng Anh rồi. Muốn dịch lại thì xoá ô tiếng Anh đi rồi bấm lại nhé.');
  var ra;
  busy(true);
  try { ra = await vgbDich(viec.map(function (v) { return v.o[v.a]; })); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Dịch lỗi'); }
  busy(false);
  viec.forEach(function (v, k) { v.o[v.b] = ra[k] || ''; });
  bgMoRong[i] = true;
  toast('Đã dịch ' + viec.length + ' ô của dòng này, đọc lại rồi sửa nếu cần', 4200);
  go(function () { scrBgSua(name); }, true);
}

/* Dich ca to mot lan: tieu de, cau chu khung to, tung dong, dich vu them
   va timeline. Van chi dien vao o dang de trong. */
async function bgDichTo(name) {
  bgDoc();
  var d = bgTay, viec = [];
  bgCanDich(d, BGCAP_TO, viec);
  (d.dong || []).forEach(function (x) { bgCanDich(x, BGCAP_DONG, viec); });
  (d.dich_vu || []).forEach(function (x) { bgCanDich(x, [['ten_vi', 'ten_en'], ['gia_vi', 'gia_en']], viec); });
  (d.moc || []).forEach(function (x) { bgCanDich(x, [['moc_vi', 'moc_en'], ['noi_dung_vi', 'noi_dung_en']], viec); });
  if (!viec.length) return baoTin('Cả tờ đã có phần tiếng Anh rồi.');
  if (!await hoiCo('Dịch cả tờ sang tiếng Anh',
    'Máy sẽ dịch ' + viec.length + ' ô đang để trống. Ô nào anh chị đã tự gõ thì giữ nguyên. Dịch xong nhớ đọc lại một lượt trước khi gửi khách nhé.',
    'Dịch ' + viec.length + ' ô')) return;
  var ra;
  busy(true);
  try { ra = await vgbDich(viec.map(function (v) { return v.o[v.a]; })); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Dịch lỗi'); }
  busy(false);
  viec.forEach(function (v, k) { v.o[v.b] = ra[k] || ''; });
  toast('Đã dịch ' + viec.length + ' ô', 4500);
  go(function () { scrBgSua(name); }, true);
}

async function bgDoiAnh(i, name) {
  bgDoc();
  var x = bgTay.dong[i]; if (!x) return;
  sheet('Hình minh hoạ dòng này', [
    { value: 'tai', label: 'Tải lên tệp từ máy tính', icon: '📤' },
    { value: 'chon', label: 'Lấy hình từ một món trong danh mục', icon: '🖼️' },
    { value: 'url', label: 'Dán đường dẫn hình', icon: '🔗' },
    { value: 'bo', label: 'Bỏ hình', icon: '🚫' }
  ], null, async function (o) {
    if (o.value === 'bo') { x.hinh = ''; return go(function () { scrBgSua(name); }, true); }
    if (o.value === 'tai') {
      var u2 = await vgbTaiAnh();
      if (!u2) return;
      x.hinh = u2;
      return go(function () { scrBgSua(name); }, true);
    }
    if (o.value === 'url') {
      var u = await hoiChu('Đường dẫn hình', 'Dán đường dẫn hình, vd /files/sp-bacf00001.jpg', x.hinh || '');
      if (u === null) return; x.hinh = u;
      return go(function () { scrBgSua(name); }, true);
    }
    var ds = await vgbChonMon({ tieu_de: 'Lấy hình từ món nào?', nhieu: false, ke_thu_vien: 1 });
    if (!ds.length) return;
    x.hinh = ds[0].hinh || '';
    if (!x.hinh) baoTin('Món này chưa có hình trên hệ.');
    go(function () { scrBgSua(name); }, true);
  });
}

async function bgLuuThuVien(i, name) {
  bgDoc();
  var x = bgTay.dong[i]; if (!x) return;
  if (!(x.ten_mon || '').trim()) return baoTin('Điền tên sản phẩm đã nhé.');
  var nhom = await hoiChu('Lưu vào thư viện', 'Xếp "' + x.ten_mon + '" vào nhóm nào để lần sau dễ tìm?',
    x.danh_muc_vi || (x.loai === 'Phí' ? 'Phí sản xuất' : 'Món thiết kế riêng'), { bat_buoc: true });
  if (!nhom) return;
  busy(true);
  try {
    await api('vagabond.bao_gia.tv_luu', {
      du_lieu: JSON.stringify({
        loai: x.loai || 'Món', nhom: nhom, ten_vi: x.ten_mon, ten_en: x.ten_en,
        ma_item: x.ma_mon, hinh: x.hinh, kich_thuoc: x.kich_thuoc,
        don_gia: x.don_gia, dvt_vi: x.dvt, dvt_en: x.dvt_en,
        mo_ta_vi: x.mo_ta, mo_ta_en: x.mo_ta_en,
        di_ung_vi: x.di_ung_vi, di_ung_en: x.di_ung_en, dung: 1
      })
    });
    busy(false); toast('Đã lưu vào thư viện, lần sau chọn lại được', 4000);
  } catch (e) { busy(false); baoTin((e && e.message) || 'Lưu lỗi'); }
}

async function bgChonKhach(name) {
  bgDoc();
  busy(true);
  var kh;
  try { kh = await api('vagabond.bao_gia.tim_khach', { so_dong: 400 }); } catch (e) { busy(false); return baoTin('Không tải được danh sách khách'); }
  busy(false);
  var muc = [{ value: '', label: 'Khách mới, chưa có trong hệ thống', icon: '✨' }];
  kh.forEach(function (x) { muc.push({ value: x.name, label: (x.customer_name || x.name) + (x.tax_id ? ' · MST ' + x.tax_id : ''), icon: '🏢' }); });
  sheet('Chọn khách hàng', muc, bgTay.khach_hang, async function (o) {
    if (!o.value) { bgTay.khach_hang = ''; return go(function () { scrBgSua(name); }, true); }
    bgTay.khach_hang = o.value;
    busy(true);
    try {
      var t = await api('vagabond.bao_gia.thong_tin_khach', { khach: o.value });
      ['ten_khach', 'ma_so_thue', 'dia_chi', 'nguoi_lien_he', 'chuc_vu', 'dien_thoai', 'email'].forEach(function (f) {
        if (t[f]) bgTay[f] = t[f];
      });
    } catch (e) { }
    busy(false);
    go(function () { scrBgSua(name); }, true);
  }, true);
}

async function bgLuu(raPdf) {
  bgDoc();
  if (!(bgTay.ten || '').trim()) return baoTin('Nhập tiêu đề báo giá đã nhé.');
  if (!(bgTay.ten_khach || '').trim() && !bgTay.khach_hang) return baoTin('Chọn khách hàng hoặc nhập tên công ty khách.');
  var thieu = (bgTay.dong || []).filter(function (x) { return !(x.ten_mon || '').trim(); });
  if (thieu.length) return baoTin('Còn ' + thieu.length + ' dòng chưa có tên sản phẩm.');
  if (!bgTay.dong.length) return baoTin('Báo giá phải có ít nhất một dòng.');
  busy(true);
  var kq;
  try { kq = await api('vagabond.bao_gia.luu', { du_lieu: JSON.stringify(bgTay) }); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Lưu lỗi'); }
  bgTay = null; bgMoRong = {};
  if (raPdf) {
    try { var fl = await api('vagabond.bao_gia.xuat_pdf', { name: kq.name }); busy(false); bcTaiVe(fl.ten_file, fl.b64, fl.kieu); toast('Đã lưu ' + kq.name + ' và tải PDF', 4500); }
    catch (e) { busy(false); toast('Đã lưu ' + kq.name + ' nhưng xuất PDF lỗi: ' + ((e && e.message) || ''), 5000); }
  } else { busy(false); toast('Đã lưu ' + kq.name); }
  go(function () { scrBgXem(kq.name); }, true);
}

/* ---------- Thu vien bao gia ---------- */
var tvLoai = null, tvTay = null;
async function scrThuVien() {
  frame('Thư viện báo giá', '<div class="emp"><div class="e1">⏳</div></div>');
  var kq, ci;
  try { ci = await bgCaiDat(); kq = await api('vagabond.bao_gia.tv_danh_sach', tvLoai ? { loai: tvLoai } : {}); }
  catch (e) { frame('Thư viện báo giá', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var chip = posChipNut('data-tvl=""', 'Tất cả · ' + kq.ds.length, !tvLoai);
  ['Món', 'Phí', 'Dịch vụ thêm', 'Bao bì'].forEach(function (t) {
    chip += posChipNut('data-tvl="' + t + '"', t + (kq.dem[t] ? ' · ' + kq.dem[t] : ''), tvLoai === t);
  });
  var html = '<div class="card" style="padding:12px 14px">' + kmHangChip(chip) +
    '<div ' + BGNHAN + ' style="margin-top:8px">Món thiết kế riêng và các khoản phí nhân công, vận chuyển, set up, gia công khuôn, thử bánh. Khai một lần, mọi tờ báo giá sau chọn lại được và sửa giá tại đây.</div></div>';
  html += '<div class="sec">' + kq.ds.length + ' mục' + (kq.so_thieu_anh ? ' · ' + kq.so_thieu_anh + ' mục chưa có hình' : '') + '</div><div class="card">';
  if (!kq.ds.length) html += '<div class="emp" style="padding:24px"><div class="e1">📚</div><div>Thư viện còn trống. Bấm ➕ để khai mục đầu tiên, hoặc bấm nút "Lưu vào thư viện" ngay trên dòng báo giá.</div></div>';
  kq.ds.forEach(function (r) {
    html += '<div class="hub" data-tv="' + h(r.name) + '">' + bgAnhO(r.hinh, 44) +
      '<div class="ht" style="margin-left:10px"><div class="h1">' + h(r.ten_vi) + (r.dung ? '' : ' <span style="color:#b3261e;font-size:11px">(đã tắt)</span>') + '</div>' +
      (r.ten_en ? '<div class="h2" style="font-style:italic">' + h(r.ten_en) + '</div>' : '') +
      '<div class="h2">' + h(r.loai) + (r.nhom ? ' · ' + h(r.nhom) : '') + (r.kich_thuoc ? ' · ' + h(r.kich_thuoc) : '') + '</div></div>' +
      '<b style="white-space:nowrap;font-size:13px">' + (r.don_gia ? money(r.don_gia) + ' đ' : h(r.gia_chu_vi || '-')) + '</b></div>';
  });
  html += '</div>';
  var b = frame('Thư viện báo giá', html, ci.duoc_sua ? { action: '➕', onAction: function () { tvTay = null; go(function () { scrTvSua(''); }); } } : {});
  b.addEventListener('click', function (e) {
    var cl = e.target.closest('[data-tvl]');
    if (cl) { tvLoai = cl.getAttribute('data-tvl') || null; return go(scrThuVien, true); }
    var r = e.target.closest('[data-tv]'); if (!r) return;
    tvTay = null;
    var nm = r.getAttribute('data-tv');
    go(function () { scrTvSua(nm); });
  });
}

function tvDoc() {
  if (!tvTay) return;
  var g = function (id) { var el = document.getElementById(id); return el ? el.value : undefined; };
  ['nhom', 'ten_vi', 'ten_en', 'kich_thuoc', 'dvt_vi', 'dvt_en', 'gia_chu_vi',
    'gia_chu_en', 'mo_ta_vi', 'mo_ta_en', 'di_ung_vi', 'di_ung_en', 'hinh',
    'ghi_chu_noi_bo'].forEach(function (f) {
      var v = g('tv_' + f); if (v !== undefined) tvTay[f] = v;
    });
  var gia = g('tv_don_gia');
  if (gia !== undefined) tvTay.don_gia = vgbSo(gia);
}

async function scrTvSua(name) {
  if (!tvTay) {
    if (name) {
      busy(true);
      try { tvTay = await api('vagabond.bao_gia.tv_chi_tiet', { name: name }); busy(false); }
      catch (e) { busy(false); return baoTin((e && e.message) || 'Không đọc được'); }
    } else {
      tvTay = { name: '', loai: 'Món', nhom: '', ten_vi: '', ten_en: '', ma_item: '', hinh: '', kich_thuoc: '', don_gia: 0, dvt_vi: '', dvt_en: '', gia_chu_vi: '', gia_chu_en: '', mo_ta_vi: '', mo_ta_en: '', di_ung_vi: '', di_ung_en: '', ghi_chu_noi_bo: '', dung: 1 };
    }
  }
  var d = tvTay;
  var oi = function (id, ph, val) {
    return '<input ' + BGO + ' id="tv_' + id + '" placeholder="' + h(ph) + '" value="' + h(val == null ? '' : val) + '">';
  };
  var chipL = '';
  ['Món', 'Phí', 'Dịch vụ thêm', 'Bao bì'].forEach(function (t) { chipL += posChipNut('data-tvk="' + t + '"', t, d.loai === t); });

  var html = '<div class="card" style="padding:12px 14px;display:grid;gap:9px">' +
    '<div ' + BGNHAN + '>Loại</div>' + kmHangChip(chipL) +
    '<div style="display:flex;align-items:center;gap:10px;margin-top:4px">' + bgAnhO(d.hinh, 64) +
    '<button class="btn gh" id="tvTai" style="margin:0;flex:1;padding:0 6px">📤 Tải lên tệp</button>' +
    '<button class="btn gh" id="tvAnh" style="margin:0;flex:1;padding:0 6px">🖼️ Lấy từ danh mục</button></div>' +
    '<input ' + BGO + ' id="tv_hinh" placeholder="Đường dẫn hình, vd /files/sp-bacf00001.jpg" value="' + h(d.hinh) + '">' +
    oi('ten_vi', 'Tên tiếng Việt (bắt buộc)', d.ten_vi) +
    oi('ten_en', 'Tên tiếng Anh', d.ten_en) +
    oi('nhom', 'Nhóm để gom trong bảng chọn, vd Bánh trung thu', d.nhom) +
    '<div class="hub" data-t="item" style="padding:9px 0;border:none"><div class="ht"><div ' + BGNHAN + '>Nối với món trong danh mục (không bắt buộc)</div><div class="h1">' + h(d.ma_item || 'Chưa nối, đây là món thiết kế riêng') + '</div></div><span style="color:#c3c8d4">&#8250;</span></div>' +
    '</div>';
  html += '<div class="sec">Giá và đơn vị</div><div class="card" style="padding:12px 14px;display:grid;gap:9px">' +
    '<div style="display:flex;flex-direction:row;align-items:center;gap:10px"><span style="width:96px">Đơn giá</span>' + bgOSo('tv_don_gia', d.don_gia, 150, true) + '<span>đ</span></div>' +
    '<div style="display:flex;flex-direction:row;gap:6px">' + bgOChu('tv_dvt_vi', d.dvt_vi, 'Đơn vị tính, vd hộp') + bgOChu('tv_dvt_en', d.dvt_en, 'Unit, vd box') + '</div>' +
    '<div ' + BGNHAN + '>Hoặc ghi giá bằng chữ khi không phải con số</div>' +
    '<div style="display:flex;flex-direction:row;gap:6px">' + bgOChu('tv_gia_chu_vi', d.gia_chu_vi, 'vd Miễn phí') + bgOChu('tv_gia_chu_en', d.gia_chu_en, 'vd Free of charge') + '</div>' +
    oi('kich_thuoc', 'Kích thước / quy cách, vd 50g (5x5cm)', d.kich_thuoc) + '</div>';
  html += '<div class="sec">Mô tả in lên báo giá</div><div class="card" style="padding:12px 14px;display:grid;gap:9px">' +
    '<textarea ' + BGTA + ' id="tv_mo_ta_vi" rows="4" placeholder="Mô tả tiếng Việt: vỏ bánh, nhân bánh...">' + h(d.mo_ta_vi) + '</textarea>' +
    '<textarea ' + BGTA + ' id="tv_mo_ta_en" rows="4" placeholder="Description in English">' + h(d.mo_ta_en) + '</textarea>' +
    '<div style="display:flex;flex-direction:row;gap:6px">' + bgOChu('tv_di_ung_vi', d.di_ung_vi, 'Dị ứng, vd Gluten, trứng') + bgOChu('tv_di_ung_en', d.di_ung_en, 'Allergen') + '</div>' +
    '<textarea ' + BGTA + ' id="tv_ghi_chu_noi_bo" rows="2" placeholder="Ghi chú nội bộ, không in">' + h(d.ghi_chu_noi_bo) + '</textarea>' +
    '<button class="btn gh" id="tvDich" style="margin:0">🌐 Dịch phần tiếng Anh còn trống</button></div>';

  var chan = '<button class="btn" id="tvLuu" style="margin:0;flex:2">Lưu</button>';
  if (d.name) chan = '<button class="btn dg" id="tvXoa" style="margin:0;flex:1">Xoá</button>' + chan;
  var b = frame(d.name ? 'Sửa mục thư viện' : 'Thêm vào thư viện', html, { footer: '<div style="display:flex;gap:8px">' + chan + '</div>' });

  b.addEventListener('click', async function (e) {
    var el;
    if ((el = e.target.closest('[data-tvk]'))) { tvDoc(); tvTay.loai = el.getAttribute('data-tvk'); return go(function () { scrTvSua(name); }, true); }
    if (e.target.closest('[data-t="item"]')) {
      tvDoc();
      var ds = await vgbChonMon({ tieu_de: 'Nối với món nào trong danh mục?', nhieu: false });
      if (!ds.length) return;
      tvTay.ma_item = ds[0].ma;
      if (!tvTay.hinh) tvTay.hinh = ds[0].hinh || '';
      if (!tvTay.ten_vi) tvTay.ten_vi = ds[0].ten;
      if (!tvTay.don_gia) tvTay.don_gia = ds[0].gia || 0;
      if (!tvTay.dvt_vi) tvTay.dvt_vi = ds[0].dvt || '';
      return go(function () { scrTvSua(name); }, true);
    }
  });
  document.getElementById('tvAnh').onclick = async function () {
    tvDoc();
    var ds = await vgbChonMon({ tieu_de: 'Lấy hình từ món nào?', nhieu: false, ke_thu_vien: 1 });
    if (!ds.length) return;
    if (!ds[0].hinh) return baoTin('Món này chưa có hình trên hệ.');
    tvTay.hinh = ds[0].hinh;
    go(function () { scrTvSua(name); }, true);
  };
  document.getElementById('tvTai').onclick = async function () {
    tvDoc();
    var u = await vgbTaiAnh();
    if (!u) return;
    tvTay.hinh = u;
    go(function () { scrTvSua(name); }, true);
  };
  document.getElementById('tvDich').onclick = async function () {
    tvDoc();
    var viec = bgCanDich(tvTay, [['ten_vi', 'ten_en'], ['dvt_vi', 'dvt_en'],
      ['gia_chu_vi', 'gia_chu_en'], ['mo_ta_vi', 'mo_ta_en'], ['di_ung_vi', 'di_ung_en']], []);
    if (!viec.length) return baoTin('Mục này đã có đủ phần tiếng Anh rồi.');
    var ra;
    busy(true);
    try { ra = await vgbDich(viec.map(function (v) { return v.o[v.a]; })); }
    catch (e) { busy(false); return baoTin((e && e.message) || 'Dịch lỗi'); }
    busy(false);
    viec.forEach(function (v, k) { v.o[v.b] = ra[k] || ''; });
    toast('Đã dịch ' + viec.length + ' ô, đọc lại rồi sửa nếu cần', 4200);
    go(function () { scrTvSua(name); }, true);
  };
  document.getElementById('tvLuu').onclick = async function () {
    tvDoc();
    if (!(tvTay.ten_vi || '').trim()) return baoTin('Nhập tên tiếng Việt đã nhé.');
    busy(true);
    try { await api('vagabond.bao_gia.tv_luu', { du_lieu: JSON.stringify(tvTay) }); busy(false); toast('Đã lưu'); tvTay = null; go(scrThuVien, true); }
    catch (e) { busy(false); baoTin((e && e.message) || 'Lưu lỗi'); }
  };
  var xb = document.getElementById('tvXoa');
  if (xb) xb.onclick = async function () {
    if (!await hoiCo('Xoá khỏi thư viện', 'Xoá "' + (tvTay.ten_vi || '') + '"? Các tờ báo giá cũ đã dùng mục này vẫn giữ nguyên nội dung.', 'Xoá', true)) return;
    busy(true);
    try { await api('vagabond.bao_gia.tv_xoa', { name: tvTay.name }); busy(false); toast('Đã xoá'); tvTay = null; go(scrThuVien, true); }
    catch (e) { busy(false); baoTin((e && e.message) || 'Không xoá được'); }
  };
}

/* ---------- Cai dat cau chu khung to ---------- */
var cdTay = null;
async function scrBgCaiDat() {
  if (!cdTay) {
    busy(true);
    try { cdTay = await api('vagabond.bao_gia.cd_doc', {}); busy(false); }
    catch (e) { busy(false); return baoTin((e && e.message) || 'Không đọc được'); }
  }
  var d = cdTay;
  var oi = function (id, ph, val) {
    return '<input ' + BGO + ' id="cd_' + id + '" placeholder="' + h(ph) + '" value="' + h(val == null ? '' : val) + '">';
  };
  var ota = function (id, val, dong) {
    return '<textarea ' + BGTA + ' id="cd_' + id + '" rows="' + (dong || 3) + '">' + h(val || '') + '</textarea>';
  };
  var html = '<div class="card" style="padding:12px 14px">' +
    '<div ' + BGNHAN + '>Khai một lần ở đây, mọi tờ báo giá mới tự chép sang. Sửa ở đây không làm đổi các tờ đã lập.</div></div>';
  html += '<div class="sec">Thông tin bên bán</div><div class="card" style="padding:12px 14px;display:grid;gap:9px">' +
    oi('ten_ban', 'Tên công ty', d.ten_ban) + oi('mst_ban', 'Mã số thuế', d.mst_ban) +
    ota('dia_chi_ban', d.dia_chi_ban, 2) + oi('web_ban', 'Website', d.web_ban) +
    oi('dai_dien_ban', 'Người đại diện mặc định', d.dai_dien_ban) +
    oi('chuc_vu_ban', 'Chức vụ', d.chuc_vu_ban) +
    oi('dt_ban', 'Điện thoại', d.dt_ban) + oi('email_ban', 'Email', d.email_ban) + '</div>';
  html += '<div class="sec">Câu chữ in lên tờ</div><div class="card" style="padding:12px 14px;display:grid;gap:9px">' +
    '<div ' + BGNHAN + '>Lời mở đầu</div>' + ota('loi_mo_vi', d.loi_mo_vi, 3) + ota('loi_mo_en', d.loi_mo_en, 3) +
    '<div ' + BGNHAN + '>Điều khoản thanh toán</div>' + ota('thanh_toan_vi', d.thanh_toan_vi, 3) + ota('thanh_toan_en', d.thanh_toan_en, 3) +
    '<div ' + BGNHAN + '>Yêu cầu vận hành</div>' + ota('yeu_cau_vi', d.yeu_cau_vi, 3) + ota('yeu_cau_en', d.yeu_cau_en, 3) +
    '<div ' + BGNHAN + '>Chính sách huỷ và thay đổi</div>' + ota('chinh_sach_huy_vi', d.chinh_sach_huy_vi, 4) + ota('chinh_sach_huy_en', d.chinh_sach_huy_en, 4) +
    '<div ' + BGNHAN + '>Lưu ý</div>' + ota('luu_y_vi', d.luu_y_vi, 3) + ota('luu_y_en', d.luu_y_en, 3) + '</div>';
  frame('Câu chữ khung tờ báo giá', html, { footer: '<button class="btn" id="cdLuu">Lưu cài đặt</button>' });
  document.getElementById('cdLuu').onclick = async function () {
    var g = function (id) { var el = document.getElementById('cd_' + id); return el ? el.value : undefined; };
    var o = {};
    ['ten_ban', 'mst_ban', 'dia_chi_ban', 'web_ban', 'dai_dien_ban', 'chuc_vu_ban',
      'dt_ban', 'email_ban', 'loi_mo_vi', 'loi_mo_en', 'thanh_toan_vi', 'thanh_toan_en',
      'yeu_cau_vi', 'yeu_cau_en', 'chinh_sach_huy_vi', 'chinh_sach_huy_en',
      'luu_y_vi', 'luu_y_en'].forEach(function (f) { var v = g(f); if (v !== undefined) o[f] = v; });
    busy(true);
    try { await api('vagabond.bao_gia.cd_luu', { du_lieu: JSON.stringify(o) }); busy(false); cdTay = null; BG_CAI = null; toast('Đã lưu cài đặt'); back(); }
    catch (e) { busy(false); baoTin((e && e.message) || 'Lưu lỗi'); }
  };
}


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
              if (!x.r.ok || !x.j.message || !x.j.message.file_url) { baoTin('Tải hình lên lỗi, vui lòng thử lại.'); return xong(''); }
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
    /* May chu tra san cau chu noi PHAI LAM GI TIEP (QT-24). Truoc day cho
       nay in ra ma may kieu "dich_vu_tra_loi_404" - dung ve ky thuat nhung
       doc xong khong ai biet lam gi. Chi rot ve ma may khi may chu cu chua
       kip gui cau chu len. */
    throw new Error((kq && kq.loi) ||
      ('Chưa dịch được (' + ((kq && kq.ly_do) || 'không rõ') +
       '). Anh chị vui lòng gõ tay phần tiếng Anh rồi báo kỹ thuật.'));
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
      (x.chiet_khau ? ' · CK ' + (x.kieu_ck === 'So tien' ? money(x.chiet_khau) + ' đ' : x.chiet_khau + '%') : '') + '</div></div>' +
      '<b style="white-space:nowrap;font-size:13px">' + money(x.thanh_tien) + '</b></div>';
  });
  html += '</div>';
  html += '<div class="card" style="padding:12px 14px">' +
    '<div style="display:flex;justify-content:space-between"><span>Cộng tiền hàng</span><b>' + money(d.tam_tinh) + ' đ</b></div>' +
    /* Man chi doc nay bi bo quen o dot v228: no in thang chiet_khau_pt kem
       dau %, nen mot to giam 2.401.376 d hien ra "Chiet khau 2401376%".
       Loan Anh bao ngay 19/08/2026. Cung mot phep doc voi man sua. */
    (d.chiet_khau_tien ? '<div style="display:flex;justify-content:space-between;margin-top:6px"><span>Chiết khấu' + (d.kieu_ck === 'So tien' ? '' : ' ' + (Number(d.chiet_khau_pt) || 0) + '%') + '</span><b>-' + money(d.chiet_khau_tien) + ' đ</b></div>' : '') +
    (d.phi_giao ? '<div style="display:flex;justify-content:space-between;margin-top:6px"><span>Phí giao hàng</span><b>' + money(d.phi_giao) + ' đ</b></div>' : '') +
    bgXemThueHtml(d) +
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

  var chan = '<button class="btn gh" id="bgXtr2" style="margin:0;flex:.9">👁 Xem trước</button>' +
    '<button class="btn" id="bgPdf" style="margin:0;flex:1">📄 Xuất PDF</button>';
  if (ci.duoc_sua && !d.thay_the_boi) {
    /* To da khoa thi nut chinh doi thanh "Tao phien ban ke tiep": sales
       khong phai di tim trong menu ⋯ moi lam duoc viec duy nhat con lai. */
    chan += d.khoa
      ? '<button class="btn" id="bgVong" style="margin:0;flex:1.3">🟣 Tạo phiên bản kế tiếp</button>'
      : '<button class="btn gh" id="bgSua" style="margin:0;flex:1">✏️ Sửa</button>';
  }
  if (ci.duoc_sua) chan += '<button class="btn gh" id="bgMenu" style="margin:0;flex:.8">⋯</button>';
  var b = frame('Báo giá', html, { footer: '<div style="display:flex;gap:8px">' + chan + '</div>' });

  var bx2 = document.getElementById('bgXtr2');
  if (bx2) bx2.onclick = function () { bgTay = null; bgXemTruoc(name); };

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

/* Hop thoai chon cau goi y roi moi go them.

   Bam mot chip la NOI cau do vao o, bam lai la go ra - ghep duoc nhieu y
   ma khong phai go tay. Cau chua {ngay} duoc thay bang ngay het hieu luc
   CUA CHINH TO DANG MO, vi go tay ngay thang la co ngay cau trong thu lech
   voi con so in tren to. */
function bgHoiLoiNhan(mau, ngay) {
  var cau = (mau || []).map(function (s) { return String(s).replace('{ngay}', bgNgayVn(ngay) || '...'); });
  return new Promise(function (xong) {
    var ov = document.createElement('div'); ov.className = 'sh';
    var box = document.createElement('div'); box.className = 'shb';
    box.innerHTML = '<div class="shh"><b>Lời nhắn thêm (không bắt buộc)</b><div class="x">&times;</div></div>' +
      '<div style="padding:12px 14px;overflow:auto">' +
      '<div ' + BGNHAN + ' style="margin-bottom:8px">Bấm chip để chèn câu có sẵn, bấm lại để gỡ ra. Câu này nằm trong thân thư, trên phần chào cuối.</div>' +
      '<div id="bgLnChip" style="display:flex;flex-wrap:wrap;gap:7px;margin-bottom:10px"></div>' +
      '<textarea ' + BGTA + ' id="bgLnO" rows="5" placeholder="Hoặc gõ thẳng vào đây..."></textarea></div>' +
      '<div style="flex:0 0 auto;display:flex;gap:8px;padding:10px 14px 14px">' +
      '<button class="btn gh" id="bgLnThoi" style="margin:0;flex:1">Thôi</button>' +
      '<button class="btn" id="bgLnOk" style="margin:0;flex:2">Xong</button></div>';
    var chip = box.querySelector('#bgLnChip');
    var o = box.querySelector('#bgLnO');
    var bat = {};
    function veChip() {
      chip.innerHTML = cau.map(function (s, i) {
        return '<span data-ln="' + i + '" style="cursor:pointer;font-size:12.5px;line-height:1.35;padding:7px 11px;border-radius:999px;border:1.5px solid ' +
          (bat[i] ? '#0a8a4a;background:#e8f6ee;color:#0a6b3a' : '#e5e7eb;background:#fff;color:#374151') +
          ';max-width:100%">' + (bat[i] ? '✓ ' : '+ ') + h(s) + '</span>';
      }).join('');
    }
    veChip();
    chip.onclick = function (e) {
      var el = e.target.closest('[data-ln]'); if (!el) return;
      var i = +el.getAttribute('data-ln');
      var ds = String(o.value || '').split('\n').filter(function (x) { return x.trim(); });
      if (bat[i]) { ds = ds.filter(function (x) { return x.trim() !== cau[i]; }); bat[i] = 0; }
      else { ds.push(cau[i]); bat[i] = 1; }
      o.value = ds.join('\n');
      veChip();
    };
    ov.appendChild(box); document.body.appendChild(ov);
    var tra = function (v) { ov.remove(); xong(v); };
    ov.onclick = function (e) { if (e.target === ov) tra(null); };
    box.querySelector('.x').onclick = function () { tra(null); };
    box.querySelector('#bgLnThoi').onclick = function () { tra(null); };
    box.querySelector('#bgLnOk').onclick = function () { tra(String(o.value || '').trim()); };
  });
}

/* ---------- Xem trước bản in ----------

   Anh Việt 16/08/2026: *"Để Sales xem trước bản in ... Tuyệt đối thao tác
   này không được kích hoạt hàm tạo phiên bản hay luồng gửi email"*.

   BA QUYẾT ĐỊNH KỸ THUẬT:

   1. Dùng IFRAME srcdoc chứ không nhét HTML thẳng vào màn. Tờ in khai các
      lớp tên ngắn như .en, .so, .khoi - trùng tên với lớp của app là hai
      bên đè lên nhau, và kiểu lỗi đó rất khó tìm. iframe cắt đứt hoàn
      toàn hai thế giới CSS.
   2. Mở NGAY TRONG APP chứ không mở tab mới. Trên điện thoại, đổi tab là
      mất màn đang soạn; bấm quay lại thì app nạp lại từ đầu.
   3. Thu nhỏ theo BỀ NGANG màn hình. Tờ A4 rộng 210mm; ép vừa màn rồi để
      cuộn dọc, nên Loan Anh thấy đúng tỷ lệ chữ và đúng chỗ ngắt trang. */
function bgXemTruocHien(html, tieuDe) {
  var ov = document.createElement('div');
  ov.style.cssText = 'position:fixed;inset:0;z-index:9999;background:#5a5a5a';
  ov.innerHTML =
    '<div style="position:absolute;top:0;left:0;right:0;height:52px;background:#111;color:#fff;' +
    'display:flex;align-items:center;gap:8px;padding:0 10px;box-sizing:border-box;z-index:2">' +
    '<b style="flex:1;font-size:13.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + h(tieuDe || 'Xem trước bản in') + '</b>' +
    '<button id="bgXtPdf" class="btn" style="margin:0;padding:6px 11px;font-size:13px;width:auto;flex:none">📄 PDF</button>' +
    '<button id="bgXtDong" class="btn gh" style="margin:0;padding:6px 11px;font-size:13px;width:auto;flex:none">Đóng</button></div>' +
    '<div id="bgXtCuon" style="position:absolute;top:52px;left:0;right:0;bottom:0;overflow-y:auto;overflow-x:hidden;-webkit-overflow-scrolling:touch"></div>';
  document.body.appendChild(ov);

  var cuon = ov.querySelector('#bgXtCuon');
  var A4 = 794;                                   /* 210mm ở 96 dpi */
  var ti = Math.min(1, ((cuon.clientWidth || window.innerWidth) - 12) / A4);
  var giay =
    '<!doctype html><html lang="vi"><meta charset="utf-8">' +
    '<style>html,body{margin:0;background:#5a5a5a}' +
    '.to{width:210mm;min-height:297mm;margin:0 auto;background:#fff;' +
    'padding:11mm 9mm;box-sizing:border-box}</style>' +
    '<div class="to">' + html + '</div></html>';

  var kh = document.createElement('div');
  kh.style.cssText = 'width:' + A4 + 'px;height:1123px;transform:scale(' + ti + ');transform-origin:top left';
  var fr = document.createElement('iframe');
  fr.style.cssText = 'width:' + A4 + 'px;height:1123px;border:0;display:block;background:#5a5a5a';
  fr.setAttribute('srcdoc', giay);
  kh.appendChild(fr);
  cuon.appendChild(kh);

  /* Chiều cao thật của tờ chỉ biết được sau khi iframe vẽ xong. Kéo khung
     ngoài theo đúng chiều cao ĐÃ thu nhỏ, không thì thừa hoặc cụt đuôi. */
  fr.onload = function () {
    try {
      var c = fr.contentDocument.documentElement.scrollHeight || 1123;
      fr.style.height = c + 'px';
      kh.style.height = (c * ti) + 'px';
    } catch (e) { }
  };

  var dong = function () { ov.remove(); };
  ov.querySelector('#bgXtDong').onclick = dong;
  return { ov: ov, dong: dong };
}

async function bgXemTruoc(name) {
  /* Gửi nguyên cục đang soạn lên; máy chủ tính lại tiền rồi dựng tờ, nên
     cái nhìn thấy đúng là cái sẽ in (QT-19). Máy chủ KHÔNG lưu gì. */
  var goi = {};
  if (bgTay) { bgDoc(); goi.du_lieu = JSON.stringify(bgTay); }
  else if (name) { goi.name = name; }
  else return baoTin('Chưa có gì để xem trước.');
  busy(true);
  var kq;
  try { kq = await api('vagabond.bao_gia.xem_truoc_nhap', goi); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Không dựng được bản xem trước'); }
  busy(false);
  var k = bgXemTruocHien(kq.html, 'Xem trước · ' + (kq.name || ''));
  k.ov.querySelector('#bgXtPdf').onclick = async function () {
    /* Tệp PDF phải gắn với một mã tờ, mà tờ nháp thì chưa có mã. */
    if (!name) { k.dong(); return baoTin('Lưu báo giá trước đã nhé, rồi mới xuất được tệp PDF gửi khách.'); }
    busy(true);
    try { var fl = await api('vagabond.bao_gia.xuat_pdf', { name: name }); busy(false); bcTaiVe(fl.ten_file, fl.b64, fl.kieu); toast('Đã tải ' + fl.ten_file, 4000); }
    catch (e) { busy(false); baoTin((e && e.message) || 'Xuất PDF lỗi'); }
  };
}

async function bgGuiMail(d) {
  var ci = await bgCaiDat();
  var em = await hoiChu('Gửi báo giá qua email',
    'Tờ PDF ' + d.name + ' sẽ được đính kèm. <b>Nhiều email thì ngăn nhau bằng dấu phẩy</b>, dùng để gửi cho nhiều phòng ban bên khách.',
    d.email || '', { goi_y: 'ten@congty.com, ketoan@congty.com', bat_buoc: true });
  if (em === null) return;

  var loi = await bgHoiLoiNhan((ci.mac_dinh && ci.mac_dinh.loi_nhan_mau) || [], d.hieu_luc_den);
  if (loi === null) return;

  /* May chu tinh lai danh sach nguoi nhan bang DUNG phep loc cua ham gui
     (QT-19), roi bay ra het truoc khi bam. Gui nham cho ca phong ban ben
     khach la loai loi khong rut lai duoc. */
  busy(true);
  var ng;
  try { ng = await api('vagabond.bao_gia.xem_nguoi_nhan', { name: d.name, email: em }); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Không kiểm được danh sách người nhận'); }
  busy(false);
  if (ng.sai && ng.sai.length) return baoTin('Địa chỉ này chưa đúng dạng email: ' + ng.sai.join(', ') + '. Anh chị vui lòng sửa lại.');
  if (!ng.nhan.length) return baoTin('Chưa có địa chỉ nào hợp lệ để gửi.');

  /* hoiCo() tu thoat ky tu va giu xuong dong (white-space:pre-wrap), nen
     cho nay viet chu tran, khong the HTML va khong goi h() lan nua. */
  var mo = 'Báo giá ' + d.name + ' · ' + money(d.tong_cong) + ' đ\n\n' +
    'Gửi tới:\n' + ng.nhan.map(function (x) { return '  • ' + x; }).join('\n');
  if (ng.cc && ng.cc.length) mo += '\n\nCC nội bộ:\n' + ng.cc.map(function (x) { return '  • ' + x; }).join('\n');
  mo += '\n\nNgười gửi: ' + (ng.tu || 'hộp thư mặc định của hệ thống');
  if (!ng.tu_co_that && ng.tu_khai) mo += '\n(Hộp thư ' + ng.tu_khai + ' chưa được bật gửi đi)';
  if (!await hoiCo('Xác nhận gửi', mo, 'Gửi thư')) return;

  busy(true);
  try {
    var r = await api('vagabond.bao_gia.gui_email', { name: d.name, email: em, loi_nhan: loi || '' });
    busy(false);
    toast('Đã gửi tới ' + (r.toi || []).length + ' địa chỉ' + ((r.cc || []).length ? ' và CC ' + r.cc.length + ' nội bộ' : ''), 4500);
    go(function () { scrBgXem(d.name); }, true);
  }
  catch (e) { busy(false); baoTin((e && e.message) || 'Gửi thư lỗi'); }
}

/* ---------- Tạo hồ sơ khách từ chính tờ báo giá ----------

Anh Việt 18/08/2026: "khách hàng nhận báo giá có khi là khách hàng mới thì
sao em, đâu có trong hệ thống đâu... hay là có nút Tạo khách hàng cho Loan
Anh tạo được không?"

Lỗ hổng thật trong luồng: tờ báo giá cho phép để trống ô Khách hàng, và nên
thế vì báo giá thì gửi cho ai cũng được. Nhưng bước chốt thành hợp đồng lại
bắt buộc phải có hồ sơ khách, vì hợp đồng còn gắn hoá đơn và theo dõi công
nợ. Trước hôm nay không có đường nào đi từ cái thứ nhất sang cái thứ hai mà
không bỏ app ra mở Desk.

Hai điều màn này phải làm đúng. Một, tờ đang soạn phải được LƯU trước, vì
máy chủ đọc thông tin khách từ tờ đã lưu chứ không tin cục dữ liệu app gửi
lên (QT-19). Hai, phải bày ra hết các hồ sơ trùng TRƯỚC khi tạo: hệ đang có
43.220 khách, thêm một dòng rác thì không ai đi dọn. */
async function bgTaoKhach(name, dangSoan) {
  var ma = name;
  if (dangSoan) {
    /* Lưu tờ trước. Máy chủ chỉ đọc được tên công ty, MST, địa chỉ khi
       chúng đã nằm trong hồ sơ, không đọc từ các ô đang gõ dở. */
    bgDoc();
    if (!(bgTay.ten_khach || '').trim()) {
      return baoTin('Chưa có tên công ty khách trên tờ này. Anh chị điền ô Tên công ty khách rồi bấm lại nhé.', 'Chưa tạo được');
    }
    busy(true);
    try { var kq = await api('vagabond.bao_gia.luu', { du_lieu: JSON.stringify(bgTay) }); ma = kq.name; }
    catch (e) { busy(false); return baoTin((e && e.message) || 'Lưu tờ báo giá lỗi'); }
    busy(false);
  }

  busy(true);
  var xt;
  try { xt = await api('vagabond.bao_gia.xem_truoc_tao_khach', { name: ma }); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Không đọc được thông tin khách trên tờ'); }
  busy(false);

  if (xt.thieu_ten) {
    return baoTin('Chưa có tên công ty khách trên tờ báo giá. Anh chị bấm Sửa báo giá, điền ô Tên công ty khách rồi tạo lại nhé.', 'Chưa tạo được');
  }
  if (xt.da_gan) {
    return baoTin('Tờ này đã gắn khách ' + xt.da_gan + ' rồi, không cần tạo thêm.', 'Đã có khách');
  }

  var o = function (nhan, gtri) {
    return '<div style="display:flex;gap:10px;padding:7px 0;border-bottom:1px solid #f2f4f7">' +
      '<div style="flex:0 0 38%;font-size:12px;color:#6b7280">' + h(nhan) + '</div>' +
      '<div style="flex:1;font-size:13.5px;font-weight:600;word-break:break-word">' + h(gtri || '(để trống)') + '</div></div>';
  };

  /* Trùng mã số thuế thì KHÔNG tạo mới. Mã số thuế là duy nhất theo luật,
     trùng nghĩa là cùng một pháp nhân - anh Việt chốt 18/08/2026. */
  var canh = '';
  if ((xt.trung_mst || []).length) {
    canh = '<div style="background:#e8f6ee;border:1px solid #a7e0c0;border-radius:10px;padding:11px 13px;margin-bottom:12px;font-size:12.5px;line-height:1.65;color:#0a6b3a">' +
      '<b>Mã số thuế này đã có hồ sơ khách rồi.</b><br>' +
      xt.trung_mst.map(function (k) { return '• ' + h(k.customer_name || k.name) + ' (' + h(k.name) + ')'; }).join('<br>') +
      '<br>Hệ thống sẽ gắn tờ này vào hồ sơ đó thay vì tạo thêm một dòng trùng.</div>';
  } else if ((xt.gan_giong || []).length) {
    canh = '<div style="background:#fff8ec;border:1px solid #f5d9a0;border-radius:10px;padding:11px 13px;margin-bottom:12px;font-size:12.5px;line-height:1.65;color:#8a5a08">' +
      '<b>Có khách tên gần giống, anh chị xem giúp có phải cùng một công ty không:</b><br>' +
      xt.gan_giong.map(function (k) { return '• ' + h(k.customer_name || k.name) + (k.tax_id ? ' · MST ' + h(k.tax_id) : ' · chưa có MST'); }).join('<br>') +
      '<br>Nếu đúng là công ty cũ thì bấm Thôi rồi chọn thẳng trong danh sách khách.</div>';
  }

  var than = canh +
    '<div class="card" style="padding:2px 14px 8px;margin-bottom:10px">' +
    o('Tên công ty', xt.ten_khach) +
    o('Mã số thuế', xt.ma_so_thue) +
    o('Địa chỉ', xt.dia_chi) +
    o('Người đại diện', xt.nguoi_lien_he + (xt.chuc_vu ? ' - ' + xt.chuc_vu : '')) +
    o('Điện thoại', xt.dien_thoai) +
    o('Email', xt.email) +
    o('Nhóm khách', xt.nhom) +
    '</div>' +
    '<div style="font-size:11.5px;color:#9ca3af;line-height:1.6">Địa chỉ và người đại diện được lưu thành hồ sơ riêng của khách, nên lần sau mở lại là có sẵn, không phải gõ tay nữa.</div>';

  var hop = hopKhung((xt.trung_mst || []).length ? 'Gắn vào khách đã có' : 'Tạo hồ sơ khách mới', than,
    '<button class="btn gh" id="bgTkThoi" style="margin:0;flex:1">Thôi</button>' +
    '<button class="btn" id="bgTkOk" style="margin:0;flex:1.4">' +
    ((xt.trung_mst || []).length ? 'Gắn vào hồ sơ có sẵn' : 'Tạo và gắn vào tờ này') + '</button>');
  hop.box.querySelector('.x').onclick = hop.dong;
  hop.box.querySelector('#bgTkThoi').onclick = hop.dong;
  hop.box.querySelector('#bgTkOk').onclick = async function () {
    busy(true);
    var r;
    try { r = await api('vagabond.bao_gia.tao_khach', { name: ma }); }
    catch (e) { busy(false); return baoTin((e && e.message) || 'Không tạo được hồ sơ khách'); }
    busy(false);
    hop.dong();
    baoTin(r.ghi_chu, r.moi ? 'Đã tạo hồ sơ khách' : 'Đã gắn khách');
    bgTay = null; bgMoRong = {};
    go(function () { scrBgXem(ma); }, true);
  };
}


/* ---------- Man hinh tao hop dong ----------

   Anh Viet 18/08/2026 test that va bat ba loi UX:

     1. *"He thong can tu dong generate ra mot ma so hop dong goi y de dien
        san vao o input, user chi can xem lai hoac an chon cho nhanh thay
        vi go tay"*.
     2. *"Popup chon ngay doi tu 'Chon ngay' thanh 'Chon ngay tao hop
        dong'"*.
     3. *"Khoi chu ky cuoi hop dong tuyet doi khong duoc ghi Ms./Mr. va
        khong duoc lay mac dinh ten cua ban Sales. Em phai thiet ke them o
        nhap lieu de user dien 'Ho ten nguoi ky' va 'Chuc vu'"*.

   Va them mot yeu cau nua ve phu luc: *"cho phep Sales upload ban Bao gia
   da scan/chup anh (co chu ky/moc cua 2 ben)"*.

   Truoc hom nay day la ba hop thoai hoi noi tiep nhau. Gio gom lai MOT man
   duy nhat: nhin thay het cac o cung luc, sua o nao truoc cung duoc, bam
   Thoi mot lan la thoat han chu khong phai bam ba lan.

   O so hop dong tu dung lai moi khi doi ngay ky, NHUNG chi khi user chua
   go tay vao o do. Go tay roi ma may van de len thi mat cong go. */
function bgSoHd(ngayIso, vietTat, loai) {
  var so = String(ngayIso || '').replace(/-/g, '').slice(0, 8);
  loai = loai || 'HDMB';
  return vietTat ? so + '/' + loai + '/' + vietTat + '-VGB' : so + '/' + loai + '/VGB';
}

function bgFormHopDong(g) {
  g = g || {};
  return new Promise(function (xong) {
    var f = {
      ngay_ky: g.ngay || today(),
      ngay_su_kien: '',
      nguoi_ky_a: g.nguoi_ky_a || '',
      chuc_vu_ky_a: g.chuc_vu_ky_a || '',
      dt_ky_a: g.dt_ky_a || '',
      email_ky_a: g.email_ky_a || '',
      nguoi_ky_b: g.nguoi_ky_b || '',
      chuc_vu_ky_b: g.chuc_vu_ky_b || '',
      dt_ky_b: g.dt_ky_b || '',
      email_ky_b: g.email_ky_b || '',
      tep: null
    };
    var tuDong = true;   /* so hop dong con do may dung, user chua go tay */

    function o(id, gtri, goiY) {
      return '<input class="tin" id="' + id + '" value="' + h(gtri || '') + '" placeholder="' + h(goiY || '') +
        '" style="height:auto;font-size:15px;font-weight:500;text-align:left;padding:10px 12px;margin:0">';
    }
    function nutNgay(id, nhan) {
      return '<button class="btn gh" id="' + id + '" style="margin:0;text-align:left;padding:10px 12px;font-size:15px">' + h(nhan) + '</button>';
    }
    var than =
      rndLbl('Số hợp đồng') + o('hdSo', bgSoHd(f.ngay_ky, g.viet_tat, g.loai), 'Vd 20260818/HDMB/MOI-VGB') +
      '<div ' + BGNHAN + ' style="margin-bottom:12px">Máy dựng sẵn theo ngày ký và tên viết tắt của khách. Hai bên đã thống nhất số khác thì sửa thẳng vào ô này.</div>' +

      rndLbl('Ngày ký hợp đồng') + nutNgay('hdNgayKy', bgNgayVn(f.ngay_ky)) +
      '<div style="height:12px"></div>' +

      rndLbl('Ngày sự kiện hoặc ngày giao hàng (không bắt buộc)') + nutNgay('hdNgaySk', 'Chưa chọn') +
      '<div style="height:14px"></div>' +

      '<div style="border-top:1px solid #eef0f4;padding-top:12px"></div>' +
      rndLbl('Người ký Bên A (khách hàng)') +
      o('hdKyA', f.nguoi_ky_a, 'Họ và tên người đặt bút ký') +
      '<div style="height:7px"></div>' +
      o('hdCvA', f.chuc_vu_ky_a, 'Chức vụ, vd Giám đốc') +
      '<div style="height:7px"></div>' +
      o('hdDtA', f.dt_ky_a, 'SĐT người ký') +
      '<div style="height:7px"></div>' +
      o('hdEmA', f.email_ky_a, 'Email người ký') +
      '<div style="height:12px"></div>' +

      rndLbl('Người ký Bên B (Vagabond)') +
      o('hdKyB', f.nguoi_ky_b, 'Họ và tên người đặt bút ký') +
      '<div style="height:7px"></div>' +
      o('hdCvB', f.chuc_vu_ky_b, 'Chức vụ, vd Giám đốc') +
      '<div style="height:7px"></div>' +
      o('hdDtB', f.dt_ky_b, 'SĐT người ký') +
      '<div style="height:7px"></div>' +
      o('hdEmB', f.email_ky_b, 'Email người ký') +
      '<div ' + BGNHAN + ' style="margin-bottom:14px">Bốn ô này in thẳng xuống khối chữ ký cuối hợp đồng. Ghi đúng họ tên người đặt bút ký, không ghi Ms./Mr., và thường là Giám đốc chứ không phải bạn làm báo giá.</div>' +

      '<div style="border-top:1px solid #eef0f4;padding-top:12px"></div>' +
      rndLbl('Phụ lục 01: bản báo giá đã ký') +
      '<button class="btn gh" id="hdChonTep" style="margin:0;padding:10px 12px;font-size:15px">📎 Chọn ảnh chụp hoặc bản scan</button>' +
      '<div ' + BGNHAN + ' id="hdTepTen">Chưa chọn tệp. Để trống thì hệ thống vẫn ghép bản báo giá do máy dựng làm phụ lục, nhưng bản đó chưa có chữ ký và mộc hai bên.</div>' +
      '<input type="file" id="hdTep" accept="image/*,application/pdf" style="display:none">';

    var k = hopKhung('Tạo hợp đồng', than,
      '<button class="btn gh" data-hdx style="flex:1;margin:0">Thôi</button>' +
      '<button class="btn" data-hdok style="flex:2;margin:0">Tạo hợp đồng</button>');

    var iSo = k.box.querySelector('#hdSo');
    var bNk = k.box.querySelector('#hdNgayKy');
    var bSk = k.box.querySelector('#hdNgaySk');
    var oTep = k.box.querySelector('#hdTep');
    var lTep = k.box.querySelector('#hdTepTen');

    iSo.oninput = function () { tuDong = false; };
    bNk.onclick = async function () {
      var v = await hoiNgay(f.ngay_ky, 'Chọn ngày tạo hợp đồng');
      if (!v) return;
      f.ngay_ky = v; bNk.textContent = bgNgayVn(v);
      if (tuDong) iSo.value = bgSoHd(v, g.viet_tat, g.loai);
    };
    bSk.onclick = async function () {
      var v = await hoiNgay(f.ngay_su_kien || f.ngay_ky, 'Chọn ngày sự kiện hoặc ngày giao hàng');
      if (!v) return;
      f.ngay_su_kien = v; bSk.textContent = bgNgayVn(v);
    };
    k.box.querySelector('#hdChonTep').onclick = function () { oTep.click(); };
    oTep.onchange = function () {
      var t = oTep.files && oTep.files[0];
      if (!t) return;
      if (t.size > 12 * 1024 * 1024) {
        oTep.value = '';
        return baoTin('Tệp nặng ' + Math.round(t.size / 1048576) + ' MB, quá 12 MB nên máy không nhận. Vui lòng chụp lại ở chế độ thường hoặc nén bớt rồi chọn lại.', 'Tệp quá nặng');
      }
      f.tep = t;
      lTep.textContent = 'Đã chọn: ' + t.name + ' (' + Math.max(1, Math.round(t.size / 1024)) + ' KB). Bản này sẽ được ghép vào cuối PDF hợp đồng làm Phụ lục 01.';
    };

    var tra = function (v) { k.dong(); xong(v); };
    k.ov.onclick = function (e) { if (e.target === k.ov) tra(null); };
    k.box.onclick = function (e) {
      if (e.target.closest('.x') || e.target.closest('[data-hdx]')) return tra(null);
      if (!e.target.closest('[data-hdok]')) return;
      var so = String(iSo.value || '').trim();
      if (!so) { iSo.focus(); return baoTin('Chưa có số hợp đồng. Bấm vào ô Số hợp đồng, lấy lại số máy gợi ý hoặc gõ số hai bên đã thống nhất rồi bấm Tạo hợp đồng.', 'Thiếu số hợp đồng'); }
      f.so = so;
      f.nguoi_ky_a = String(k.box.querySelector('#hdKyA').value || '').trim();
      f.chuc_vu_ky_a = String(k.box.querySelector('#hdCvA').value || '').trim();
      f.dt_ky_a = String(k.box.querySelector('#hdDtA').value || '').trim();
      f.email_ky_a = String(k.box.querySelector('#hdEmA').value || '').trim();
      f.nguoi_ky_b = String(k.box.querySelector('#hdKyB').value || '').trim();
      f.chuc_vu_ky_b = String(k.box.querySelector('#hdCvB').value || '').trim();
      f.dt_ky_b = String(k.box.querySelector('#hdDtB').value || '').trim();
      f.email_ky_b = String(k.box.querySelector('#hdEmB').value || '').trim();
      tra(f);
    };
  });
}

/* Tai ban scan phu luc len va gan thang vao o phu_luc_scan cua hop dong.
   Phai co hop dong roi moi tai duoc, vi Frappe gan tep theo doctype va ten
   ban ghi - tai truoc thi tep nam lo lung khong ai doc duoc. */
async function bgTaiPhuLuc(hopDong, tep) {
  var fd = new FormData();
  fd.append('file', tep, tep.name || ('phu-luc-' + hopDong));
  fd.append('is_private', '1');
  fd.append('doctype', 'Hop Dong Ban Hang');
  fd.append('docname', hopDong);
  fd.append('fieldname', 'phu_luc_scan');
  var hd = {};
  hd['X-Frappe-' + 'CSRF-' + 'Token'] = frappe.csrf_token;
  var r = await fetch('/api/method/upload_file', { method: 'POST', headers: hd, body: fd });
  var j = await r.json();
  if (!r.ok || !j.message) throw new Error('Không tải được bản scan lên');
  return j.message.file_url;
}

async function bgChotHopDong(d) {
  /* Chua co ho so khach thi HOI luon co tao khong, khong bat quay lai sua
     to (anh Viet 18/08/2026). Truoc hom nay cho nay chi bao loi roi bo do,
     ma khach moi thi lam gi da co ho so. */
  if (!d.khach_hang) {
    if (!(d.ten_khach || '').trim()) {
      return baoTin('Tờ này chưa có tên công ty khách. Anh chị bấm Sửa báo giá, điền ô Tên công ty khách rồi quay lại nhé.', 'Chưa lên hợp đồng được');
    }
    if (!await hoiCo('Chưa có hồ sơ khách',
      'Hợp đồng phải gắn với một khách hàng có trong hệ thống, vì còn gắn hoá đơn và theo dõi công nợ.\n\n' +
      'Tờ này đang ghi khách là "' + (d.ten_khach || '') + '". Hệ thống tạo hồ sơ khách từ chính thông tin trên tờ nhé?',
      'Tạo hồ sơ khách')) return;
    return bgTaoKhach(d.name, false);
  }
  busy(true);
  var g;
  try { g = await api('vagabond.bao_gia.goi_y_hop_dong', { name: d.name }); }
  catch (e) { g = {}; }
  busy(false);
  var f = await bgFormHopDong(g);
  if (!f) return;
  busy(true);
  var nm;
  try {
    nm = await api('vagabond.bao_gia.tao_hop_dong', {
      name: d.name, so_hop_dong: f.so, ngay_ky: f.ngay_ky,
      ngay_su_kien: f.ngay_su_kien || '',
      nguoi_ky_a: f.nguoi_ky_a, chuc_vu_ky_a: f.chuc_vu_ky_a,
      dt_ky_a: f.dt_ky_a, email_ky_a: f.email_ky_a,
      nguoi_ky_b: f.nguoi_ky_b, chuc_vu_ky_b: f.chuc_vu_ky_b,
      dt_ky_b: f.dt_ky_b, email_ky_b: f.email_ky_b
    });
  } catch (e) { busy(false); return baoTin((e && e.message) || 'Không tạo được hợp đồng'); }
  /* Hop dong da tao xong roi moi tai tep. Tep hong thi hop dong VAN CON,
     chi bao rieng phan tep de dinh kem lai o man hinh hop dong - khong xoa
     hop dong vua tao. */
  var loiTep = '';
  if (f.tep) {
    try { await bgTaiPhuLuc(nm, f.tep); }
    catch (e2) { loiTep = (e2 && e2.message) || 'Không tải được bản scan'; }
  }
  busy(false);
  if (loiTep) baoTin('Hợp đồng ' + nm + ' đã tạo xong, nhưng bản scan phụ lục chưa lên được: ' + loiTep + '.\n\nAnh chị mở hợp đồng rồi bấm Đính kèm bản scan để thử lại nhé.', 'Đã tạo hợp đồng, thiếu phụ lục');
  else toast('Đã tạo hợp đồng ' + nm, 4000);
  go(function () { scrHdView(nm); }, true);
}

/* ---------- Soan bao gia: moi dong nhap thang tai cho ---------- */
var bgTay = null, bgMoRong = {};

/* Ban sao may khach cua bao_gia.tien_chiet_khau. HAI PHEP NAY PHAI GIONG
   HET NHAU: mot ben tinh de bay len man hinh, mot ben tinh de ghi xuong so.
   Lech nhau la sales doc mot so, khach nhan to in mot so khac.
   Kieu de trong hieu la phan tram, dung y nhu truoc khi co tinh nang chiet
   khau theo so tien (anh Viet 19/08/2026). */
function bgTienCk(goc, kieu, giaTri) {
  var g = Number(goc) || 0;
  var v = Number(giaTri) || 0;
  if (g <= 0 || v <= 0) return 0;
  if (kieu === 'So tien') return Math.min(Math.round(v), Math.round(g));
  return Math.min(Math.round(g * v / 100), Math.round(g));
}

function bgTinh() {
  if (!bgTay) return;
  var tam = 0;
  (bgTay.dong || []).forEach(function (x) {
    x.so_luong = Number(x.so_luong) || 0;
    x.don_gia = Number(x.don_gia) || 0;
    x.chiet_khau = Number(x.chiet_khau) || 0;
    var gocDong = Math.round(x.so_luong * x.don_gia);
    x.ck_tien_dong = bgTienCk(gocDong, x.kieu_ck, x.chiet_khau);
    x.thanh_tien = gocDong - x.ck_tien_dong;
    tam += x.thanh_tien;
  });
  bgTay.tam_tinh = tam;
  bgTay.chiet_khau_tien = bgTienCk(tam, bgTay.kieu_ck, bgTay.chiet_khau_pt);
  var sau = tam - bgTay.chiet_khau_tien;
  if (bgTheoDong()) {
    var bt = bgBangThue();
    bgTay.thue_tien = bt.tien_thue;
    bgTay.tong_cong = bt.tong_cong;
  } else if (bgTay.gia_da_gom_vat) { bgTay.thue_tien = 0; bgTay.tong_cong = sau + (Number(bgTay.phi_giao) || 0); }
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
    ['so_luong', 'don_gia', 'chiet_khau', 'thue_pt'].forEach(function (f) {
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

/* Muc thue mac dinh cho dong moi: lay muc cua to, de sales khong phai go
   lai tung dong khi ca to cung mot muc. */
function bgMucThueMacDinh() {
  var v = Number(bgTay && bgTay.thue_pt);
  return isNaN(v) ? 8 : v;
}

/* To nay tinh thue theo tung dong hay theo ca to. O de trong doc la cach
   cu, dung y do: to dang co tren he khong duoc doi mot dong. */
function bgTheoDong() {
  return (bgTay && bgTay.kieu_thue) === 'Theo từng dòng';
}

/* Tach thue cho ca to NGAY TREN MAN, dung y het phep cua may chu.

   Vi sao lam lai o day: sales sua so nao thi phai thay tong doi ngay, cho
   duoc may chu tra loi thi man giat. Nhung day chi la de NHIN - con so luu
   xuong va con so in ra van do may chu tinh lai (QT-19), nen neu hai ben
   lech nhau thi cai dung la cai cua may chu.

   Hai phep duoi day phai giong het bao_gia.phan_bo_chiet_khau va
   bao_gia.tach_thue. Bo kiem chay CA HAI ban tren cung bo so va so tung
   dong, nen khong the am tham lech nhau. */
function bgBangThue() {
  var ds = (bgTay.dong || []).map(function (x) { return Number(x.thanh_tien) || 0; });
  var tong = ds.reduce(function (a, b) { return a + b; }, 0);
  var ck = Number(bgTay.chiet_khau_tien) || 0;
  var daGom = !!bgTay.gia_da_gom_vat;
  /* Dong cuoi nhan phan du nen tong cac phan chia luon bang dung ck. */
  var tru = [], da = 0;
  ds.forEach(function (t, i) {
    var x = (tong <= 0 || ck <= 0) ? 0
      : (i === ds.length - 1 ? ck - da : Math.round(ck * t / tong));
    tru.push(x); da += x;
  });
  function tach(nen, pt) {
    if (!pt) return { hang: nen, thue: 0 };
    if (daGom) { var h = Math.round(nen * 100 / (100 + pt)); return { hang: h, thue: nen - h }; }
    return { hang: nen, thue: Math.round(nen * pt / 100) };
  }
  var muc = {}, tHang = 0, tThue = 0;
  (bgTay.dong || []).forEach(function (x, i) {
    var pt = Number(x.thue_pt) || 0;
    var r = tach(ds[i] - tru[i], pt);
    muc[pt] = muc[pt] || { thue_pt: pt, tien_hang: 0, tien_thue: 0 };
    muc[pt].tien_hang += r.hang; muc[pt].tien_thue += r.thue;
    tHang += r.hang; tThue += r.thue;
  });
  var pg = Number(bgTay.phi_giao) || 0;
  if (pg) {
    var ppt = Number(bgTay.thue_phi_giao_pt) || 0;
    var rp = tach(pg, ppt);
    muc[ppt] = muc[ppt] || { thue_pt: ppt, tien_hang: 0, tien_thue: 0 };
    muc[ppt].tien_hang += rp.hang; muc[ppt].tien_thue += rp.thue;
    tHang += rp.hang; tThue += rp.thue;
  }
  var dsMuc = Object.keys(muc).map(function (k) { return muc[k]; })
    .sort(function (a, b) { return a.thue_pt - b.thue_pt; });
  return { theo_muc: dsMuc, tien_hang: tHang, tien_thue: tThue, tong_cong: tHang + tThue };
}

/* Ba dong khach hay hoi, hien ngay tren man soan (anh Viet 18/08/2026):
   *"nhieu khach ho yeu cau so tien truoc thue va so tien sau thue, so tien
   thue"*. Sales nhin thay dung cai se in ra to PDF. */
function bgTomTatThueHtml() {
  var bt = bgBangThue();
  var d1 = function (nhan, tien) {
    return '<div style="display:flex;justify-content:space-between;margin-top:6px">' +
      '<span>' + h(nhan) + '</span><b>' + money(tien) + ' đ</b></div>';
  };
  var muc = bt.theo_muc.filter(function (m) { return m.tien_hang || m.tien_thue; });
  var ra = d1('Cộng tiền hàng chưa thuế', bt.tien_hang);
  if (muc.length > 1) {
    muc.forEach(function (m) {
      ra += '<div style="display:flex;justify-content:space-between;margin-top:4px;font-size:12.5px;color:#6b7280">' +
        '<span>VAT ' + m.thue_pt + '% trên ' + money(m.tien_hang) + '</span><span>' + money(m.tien_thue) + ' đ</span></div>';
    });
    ra += d1('Cộng tiền thuế GTGT', bt.tien_thue);
  } else {
    ra += d1('Thuế GTGT ' + (muc.length ? muc[0].thue_pt : 0) + '%', bt.tien_thue);
  }
  if (!bgTay.gia_da_gom_vat) {
    ra += '<div style="font-size:12px;color:#8a8f9c;margin-top:4px">Đơn giá chưa gồm VAT, thuế được cộng thêm lên tổng.</div>';
  }
  return ra;
}

/* Khoi thue cua man CHI DOC.

   Truoc 19/08/2026 cho nay chi biet hai truong hop: co thue_tien thi in
   "Thue GTGT <thue_pt>%", khong thi in "Don gia da bao gom VAT". Ca hai
   deu doc o thue_pt CUA TO, trong khi to co the dang tinh thue theo tung
   dong - luc do thue_pt cua to khong con y nghia gi. Ket qua la man hinh
   noi mot dang con to PDF in mot dang. */
function bgXemThueHtml(d) {
  var d1 = function (nhan, tien) {
    return '<div style="display:flex;justify-content:space-between;margin-top:6px"><span>' +
      nhan + '</span><b>' + money(tien) + ' đ</b></div>';
  };
  if (d.kieu_thue === 'Theo từng dòng') {
    var muc = ((d.tom_tat_thue || {}).theo_muc || []).filter(function (m) {
      return Number(m.tien_hang) || Number(m.tien_thue);
    });
    var ra = d1('Cộng tiền hàng chưa thuế', (d.tom_tat_thue || {}).tien_hang || 0);
    if (muc.length > 1) {
      muc.forEach(function (m) { ra += d1('Thuế GTGT ' + m.thue_pt + '% trên ' + money(m.tien_hang), m.tien_thue); });
      ra += d1('Cộng tiền thuế GTGT', (d.tom_tat_thue || {}).tien_thue || 0);
    } else {
      ra += d1('Thuế GTGT ' + (muc.length ? muc[0].thue_pt : 0) + '%', (d.tom_tat_thue || {}).tien_thue || 0);
    }
    return ra;
  }
  if (Number(d.thue_tien)) return d1('Thuế GTGT ' + (Number(d.thue_pt) || 0) + '%', d.thue_tien);
  return '<div style="font-size:12.5px;color:#8a8f9c;margin-top:6px">Đơn giá đã bao gồm VAT</div>';
}


function bgTongHtml() {
  var d = bgTay;
  return '<div style="display:flex;justify-content:space-between"><span>Cộng tiền hàng</span><b>' + money(d.tam_tinh) + ' đ</b></div>' +
    (Number(d.chiet_khau_tien) ? '<div style="display:flex;justify-content:space-between;margin-top:6px"><span>Chiết khấu' + (d.kieu_ck === 'So tien' ? '' : ' ' + (Number(d.chiet_khau_pt) || 0) + '%') + '</span><b>-' + money(d.chiet_khau_tien) + ' đ</b></div>' : '') +
    (Number(d.phi_giao) ? '<div style="display:flex;justify-content:space-between;margin-top:6px"><span>Phí giao hàng</span><b>' + money(d.phi_giao) + ' đ</b></div>' : '') +
    (bgTheoDong() ? bgTomTatThueHtml()
      : (d.gia_da_gom_vat ? '<div style="font-size:12.5px;color:#8a8f9c;margin-top:6px">Đơn giá đã bao gồm VAT, không cộng thêm thuế lên tổng</div>'
        : '<div style="display:flex;justify-content:space-between;margin-top:6px"><span>Thuế GTGT ' + (Number(d.thue_pt) || 0) + '%</span><b>' + money(d.thue_tien) + ' đ</b></div>')) +
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
  /* Bo cuc to in di theo mau, sales khong phai chon lan hai. */
  go(function () { scrBgSua(''); });
}

/* Bam dau cong o man danh sach: co mau thi hoi lap theo mau nao truoc.
   Anh Viet 15/08/2026: *"Thêm tính năng 'Lưu mẫu báo giá' để sau này dùng
   thì áp lên để app tự điền hết các phần thông tin theo mẫu"*. */
/* Bam nut + la chon mau NGAY, khong phai vao trong to roi moi chon.

   Anh Viet 16/08/2026: *"Anh khong muon Sales phai vao trong to bao gia
   moi di chon mau. Hay chuyen thao tac nay ra ngay nut +"*.

   Khong dung sheet() cho bang nay: sheet() chi hien duoc mot dong nhan,
   ma o day moi mau can hai dong - ten mau va mot cau ta no dung cho viec
   gi - cong mot nhan bo cuc to in. Loan Anh chon mau lan dau ma chi thay
   moi cai ten thi van phai mo tung cai ra xem. */
async function bgMoiHoi() {
  busy(true);
  var kq, ci;
  try { ci = await bgCaiDat(); kq = await api('vagabond.bao_gia.mau_ds', {}); }
  catch (e) { busy(false); return bgMoi(); }
  busy(false);
  var ds = (kq && kq.ds) || [];
  if (!ds.length) return bgMoi();

  var tenBoCuc = {};
  ((kq && kq.mau_in) || []).forEach(function (x) { tenBoCuc[x.ma] = x.ten; });

  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  var html = '<div class="shh"><b>Lập báo giá mới</b><div class="x">&times;</div></div><div class="shl">';
  html += '<div class="shi" data-mau=""><span>📄</span><span style="flex:1;min-width:0">' +
    '<b>Tờ trắng</b><div style="color:#a0a6b4;font-size:12px;margin-top:2px">Soạn từ đầu, câu chữ lấy theo Cài đặt báo giá.</div></span></div>';
  ds.forEach(function (m) {
    var bc = tenBoCuc[m.mau_in || ''] || '';
    html += '<div class="shi" data-mau="' + h(m.name) + '"><span>' + (m.tu_ma_nguon ? '🗂️' : '⭐') + '</span>' +
      '<span style="flex:1;min-width:0"><b>' + h(m.ten_mau || m.name) + '</b>' +
      (m.mo_ta_mau ? '<div style="color:#a0a6b4;font-size:12px;margin-top:2px">' + h(m.mo_ta_mau) + '</div>' : '') +
      (bc ? '<div style="color:#7c3aed;font-size:11.5px;margin-top:2px">Tờ in: ' + h(bc) + '</div>' : '') +
      '</span></div>';
  });
  html += '</div>';
  box.innerHTML = html;
  ov.appendChild(box); document.body.appendChild(ov);
  var dong = function () { ov.remove(); };
  ov.onclick = function (e) { if (e.target === ov) dong(); };
  box.querySelector('.x').onclick = dong;
  box.querySelector('.shl').onclick = function (e) {
    var r = e.target.closest('[data-mau]'); if (!r) return;
    var ma = r.getAttribute('data-mau');
    dong();
    bgMoi(ma || '');
  };
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
    /* Go MST xong roi roi o la may tu tra ten va dia chi. Nut ben canh de
       goi lai khi can. Dung lai vagabond.api.tra_mst da chay san cho hoa
       don - no da xu ly san MST chi nhanh 13 so giu dau gach ngang theo
       Thong tu 86/2024 va co bo nho dem bay ngay. */
    '<div style="display:flex;flex-direction:row;gap:6px">' +
    oi('ma_so_thue', 'Mã số thuế khách, gõ xong máy tự điền tên', d.ma_so_thue) +
    '<button class="btn gh" data-t="tramst" style="flex:none;width:46px;height:44px;margin:0;padding:0;font-size:17px">🔍</button></div>' +
    (d._mst_bao ? '<div ' + BGNHAN + '>' + h(d._mst_bao) + '</div>' : '') +
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
      '<span style="font-size:12px;color:#8a8f9c">' + (x.kieu_ck === 'So tien' ? 'CK đ' : 'CK%') + '</span>' +
      bgOSo('dg_' + i + '_chiet_khau', x.chiet_khau, x.kieu_ck === 'So tien' ? 88 : 52) +
      /* Muc thue cua RIENG dong (anh Viet 18/08/2026). To tron duoc banh 8%
         voi phi dich vu 10% va mon khong chiu thue, nen muc thue la thuoc
         tinh cua dong chu khong phai cua to. */
      '<span style="font-size:12px;color:#8a8f9c">VAT%</span>' + bgOSo('dg_' + i + '_thue_pt', x.thue_pt, 52) +
      '<b id="dg_' + i + '_tt" style="margin-left:auto;font-size:14.5px;white-space:nowrap">' + money(x.thanh_tien) + ' đ</b></div>' +
      '<div style="display:flex;flex-direction:row;gap:8px;align-items:center">' +
      posChipNut('data-loai="' + i + '"', x.loai === 'Phí' ? 'Là khoản phí' : 'Là món bánh', x.loai === 'Phí') +
      posChipNut('data-mo="' + i + '"', mo ? 'Thu gọn ▴' : 'Mô tả, dị ứng, kích thước ▾', mo) +
      /* Tuy bien ruot hop qua (21/08/2026). Chi hien voi dong la hop, va
         hien luon so mon dang co de Sales khoi phai mo ra xem. Xem
         28-hop-qua.js. */
      (hqLaHop(x)
        ? posChipNut('data-hq="' + i + '"', '🎁 Tuỳ biến hộp' +
            (hqNhan(x) ? ' · ' + hqNhan(x) : ''), !!hqNhan(x))
        : '') +
      /* Hai chip chon kieu chiet khau cua RIENG dong nay (anh Viet
         19/08/2026: *"chiet khau theo tung dong hang hoa"*). */
      posChipNut('data-ckd="' + i + ':Phan tram"', 'CK %',
        (x.kieu_ck || 'Phan tram') === 'Phan tram') +
      posChipNut('data-ckd="' + i + ':So tien"', 'CK số tiền', x.kieu_ck === 'So tien') +
      [0, 8, 10].map(function (v) {
        return posChipNut('data-vat="' + i + ':' + v + '"', 'VAT ' + v + '%',
          (Number(x.thue_pt) || 0) === v);
      }).join('') +
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
      /* Hai chip chon kieu chiet khau (anh Viet 19/08/2026, theo yeu cau
         cua Loan Anh). Chip dang dung thi to dam len, bam chip kia la doi
         kieu VA mo luon o nhap so - khoi phai bam hai lan. */
      posChipNut('data-t="ck-pt"', 'Chiết khấu %: <b>' + (Number(d.chiet_khau_pt) || 0) + '%</b> ✎',
                 (d.kieu_ck || 'Phan tram') === 'Phan tram') +
      posChipNut('data-t="ck-tien"', 'Chiết khấu số tiền: <b>' + money(d.kieu_ck === 'So tien' ? d.chiet_khau_pt : 0) + ' đ</b> ✎',
                 d.kieu_ck === 'So tien') +
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
    footer: '<div style="display:flex;gap:7px">' +
      '<button class="btn gh" id="bgXtr" style="margin:0;flex:.9">👁 Xem trước</button>' +
      '<button class="btn gh" id="bgXemPdf" style="margin:0;flex:1.1">📄 Lưu và xuất PDF</button>' +
      '<button class="btn" id="bgLuu" style="margin:0;flex:1">Lưu</button></div>'
  });

  /* Go so lieu tren dong thi tinh lai NGAY, khong ve lai man */
  b.addEventListener('input', function (e) {
    var el = e.target;
    if (el && el.getAttribute && el.getAttribute('data-tien') === '1') vgbTienGo(el);
    var id = (el && el.id) || '';
    if (/^dg_\d+_(so_luong|don_gia|chiet_khau|thue_pt)$/.test(id)) bgTongHien();
  });

  /* Roi o ma so thue la tra luon, khong bat bam nut. Dung 'blur' chu khong
     dung 'input': go tung so ma goi tung lan la ban ra Cong thong tin
     doanh nghiep muoi ba lan cho mot ma. */
  var bxt = document.getElementById('bgXtr');
  if (bxt) bxt.onclick = function () { bgXemTruoc(d.name || ''); };

  var oMst = document.getElementById('bgf_ma_so_thue');
  if (oMst) oMst.addEventListener('blur', function () { bgTraMst(name, false); });

  b.addEventListener('click', async function (e) {
    var el;
    if ((el = e.target.closest('[data-hl]'))) { bgDoc(); bgTay.hieu_luc_ngay = Number(el.getAttribute('data-hl')); return go(function () { scrBgSua(name); }, true); }
    if (e.target.closest('[data-t="songngu"]')) { bgDoc(); bgTay.song_ngu = bgTay.song_ngu ? 0 : 1; return go(function () { scrBgSua(name); }, true); }
    if (e.target.closest('[data-t="vat"]')) { bgDoc(); bgTay.gia_da_gom_vat = bgTay.gia_da_gom_vat ? 0 : 1; return go(function () { scrBgSua(name); }, true); }
    if (e.target.closest('[data-t="khach"]')) return bgChonKhach(name);
    if (e.target.closest('[data-t="tramst"]')) return bgTraMst(name, true);
    if ((el = e.target.closest('[data-mo]'))) { bgDoc(); var k = el.getAttribute('data-mo'); bgMoRong[k] = !bgMoRong[k]; return go(function () { scrBgSua(name); }, true); }
    if ((el = e.target.closest('[data-loai]'))) { bgDoc(); var j = +el.getAttribute('data-loai'); bgTay.dong[j].loai = bgTay.dong[j].loai === 'Phí' ? 'Món' : 'Phí'; return go(function () { scrBgSua(name); }, true); }
    if ((el = e.target.closest('[data-hq]'))) return hqMo(+el.getAttribute('data-hq'), name);
    if ((el = e.target.closest('[data-xoa]'))) { bgDoc(); bgTay.dong.splice(+el.getAttribute('data-xoa'), 1); bgMoRong = {}; return go(function () { scrBgSua(name); }, true); }
    if ((el = e.target.closest('[data-xdv]'))) { bgDoc(); bgTay.dich_vu.splice(+el.getAttribute('data-xdv'), 1); return go(function () { scrBgSua(name); }, true); }
    if ((el = e.target.closest('[data-xmc]'))) { bgDoc(); bgTay.moc.splice(+el.getAttribute('data-xmc'), 1); return go(function () { scrBgSua(name); }, true); }
    if ((el = e.target.closest('[data-tn]'))) {
      bgDoc(); var p = el.getAttribute('data-tn').split('|');
      bgTay.moc[+p[0]].trach_nhiem = p[1]; return go(function () { scrBgSua(name); }, true);
    }
    if ((el = e.target.closest('[data-anh]'))) return bgDoiAnh(+el.getAttribute('data-anh'), name);
    if ((el = e.target.closest('[data-vat]'))) {
      /* Doc man ve bgTay truoc da, khong thi chu nguoi ta vua go o cac o
         khac bi mat khi ve lai. */
      bgDoc();
      var pv = String(el.getAttribute('data-vat')).split(':');
      var dgv = bgTay.dong[+pv[0]];
      if (dgv) dgv.thue_pt = Number(pv[1]) || 0;
      return go(function () { scrBgSua(name); }, true);
    }
    if ((el = e.target.closest('[data-ckd]'))) {
      bgDoc();
      var pk = el.getAttribute('data-ckd').split(':');
      var dck = (bgTay.dong || [])[+pk[0]];
      if (dck && (dck.kieu_ck || 'Phan tram') !== pk[1]) {
        /* Doi kieu thi so cu vo nghia: 10 phan tram khong phai 10 dong.
           Xoa ve 0 de sales go lai, an toan hon la giu mot con so sai. */
        dck.kieu_ck = pk[1] === 'So tien' ? 'So tien' : '';
        dck.chiet_khau = 0;
      }
      return go(function () { scrBgSua(name); }, true);
    }
    if ((el = e.target.closest('[data-luutv]'))) return bgLuuThuVien(+el.getAttribute('data-luutv'), name);
    if ((el = e.target.closest('[data-dich]'))) return bgDichDong(+el.getAttribute('data-dich'), name);
    if (e.target.closest('[data-t="dichto"]')) return bgDichTo(name);
    if (e.target.closest('[data-t="ck-pt"]')) {
      bgDoc();
      var v = await hoiSo('Chiết khấu tổng theo phần trăm',
        'Phần trăm chiết khấu trên tổng tiền hàng (0 tới 100).',
        bgTay.kieu_ck === 'So tien' ? 0 : (bgTay.chiet_khau_pt || 0));
      if (v === null) return;
      bgTay.kieu_ck = 'Phan tram';
      bgTay.chiet_khau_pt = Math.min(100, Math.max(0, v));
      return go(function () { scrBgSua(name); }, true);
    }
    if (e.target.closest('[data-t="ck-tien"]')) {
      bgDoc();
      /* Tran la TONG TIEN HANG: go nhieu hon ca to thi to ra so am. May
         chu cung chan lai lan nua trong bao_gia.tien_chiet_khau. */
      var tam0 = 0;
      (bgTay.dong || []).forEach(function (x) {
        tam0 += Math.round((Number(x.so_luong) || 0) * (Number(x.don_gia) || 0));
      });
      var v2 = await hoiSo('Chiết khấu tổng theo số tiền',
        'Số tiền chiết khấu trừ thẳng vào tổng tiền hàng (tối đa ' + money(tam0) + ' đ).',
        bgTay.kieu_ck === 'So tien' ? (bgTay.chiet_khau_pt || 0) : 0);
      if (v2 === null) return;
      bgTay.kieu_ck = 'So tien';
      bgTay.chiet_khau_pt = Math.max(0, Math.min(tam0, v2));
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
        so_luong: 1, don_gia: m.gia || 0, chiet_khau: 0, thue_pt: bgMucThueMacDinh(), thanh_tien: 0
      });
    });
    toast('Đã thêm ' + ds.length + ' dòng, giờ chỉ cần gõ số lượng', 3500);
    go(function () { scrBgSua(name); }, true);
  };
  document.getElementById('bgThemTay').onclick = function () {
    bgDoc();
    bgTay.dong.push({ loai: 'Món', ma_mon: '', ma_tv: '', ten_mon: '', ten_en: '', dvt: '', dvt_en: '', hinh: '', kich_thuoc: '', mo_ta: '', mo_ta_en: '', di_ung_vi: '', di_ung_en: '', danh_muc_vi: '', danh_muc_en: '', so_luong: 1, don_gia: 0, chiet_khau: 0, thue_pt: bgMucThueMacDinh(), thanh_tien: 0 });
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

/* Bang chon khach: o tim HOI NGUOC LEN MAY CHU moi lan go.

   Khong dung sheet() cho viec nay duoc: sheet() loc ngay trong trinh duyet
   tren dung cai tap da nap san, ma he co 43.186 khach nen tap nap san bao
   nhieu cung khong du. Day la dung ban sheetTimKhach cua man tinh tien
   quay - man do da chay dung tu dau, chi rieng man bao gia lam sai. */
async function bgChonKhach(name) {
  bgDoc();
  busy(true);
  var ds;
  try { ds = await api('vagabond.bao_gia.tim_khach', { tim: '', so_dong: 60 }); }
  catch (e) { busy(false); return baoTin('Không tải được danh sách khách'); }
  busy(false);
  ds = ds || [];

  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>Chọn khách hàng</b><div class="x">&times;</div></div>' +
    '<div style="flex:0 0 auto;padding:10px 14px 4px">' +
    '<input class="nt" id="bgKhTim" placeholder="Gõ tên công ty, mã khách, MST hoặc số điện thoại..." style="height:46px;padding:0 12px;width:100%;box-sizing:border-box"></div>' +
    '<div class="shl"></div>';
  var lst = box.querySelector('.shl');
  function ve(dangTim) {
    /* Hai muc dau, va chung khac han nhau (anh Viet 18/08/2026):

         "Khach moi, chua co trong he thong"  de trong o Khach hang. To bao
             gia van in va van gui duoc - bao gia thi gui cho ai cung duoc.
         "Tao ho so khach tu to nay"          tao that mot Customer. Chi
             can den khi sap len HOP DONG, vi hop dong con gan hoa don va
             theo doi cong no nen bat buoc phai co ho so.

       Truoc hom nay chi co muc thu nhat, nen tu to bao gia khong co duong
       nao di sang hop dong ma khong bo app ra mo Desk. */
    var dau = '<div class="shi" data-kh=""><span>✨</span><span style="flex:1;min-width:0">Khách mới, chưa có trong hệ thống<div style="color:#a0a6b4;font-size:12px;margin-top:2px">Để trống ô khách. Vẫn in và gửi báo giá được.</div></span></div>' +
      '<div class="shi" data-kh="_tao" style="background:#f0fdfa"><span>🏢</span><span style="flex:1;min-width:0"><b style="color:#0f766e">Tạo hồ sơ khách từ tờ này</b><div style="color:#0f766e;font-size:12px;margin-top:2px">Lấy sẵn tên công ty, MST, địa chỉ đã gõ. Cần có hồ sơ mới lên hợp đồng được.</div></span></div>';
    if (dangTim) { lst.innerHTML = dau + '<div class="emp" style="padding:18px"><div class="e2">Đang tìm...</div></div>'; return; }
    lst.innerHTML = dau + (ds.length ? ds.map(function (x) {
      return '<div class="shi' + (x.name === bgTay.khach_hang ? ' on' : '') + '" data-kh="' + h(x.name) + '"><span>🏢</span>' +
        '<span style="flex:1;min-width:0">' + h(x.customer_name || x.name) +
        '<div style="color:#a0a6b4;font-size:12px;margin-top:2px">' + h(x.name) +
        (x.tax_id ? ' · MST ' + h(x.tax_id) : '') +
        (x.mobile_no ? ' · ' + h(x.mobile_no) : '') + '</div></span>' +
        (x.name === bgTay.khach_hang ? '<span>&#10003;</span>' : '') + '</div>';
    }).join('') : '<div class="emp" style="padding:22px"><div class="e2">Không có khách nào khớp. Gõ ít chữ hơn, hoặc chọn "Khách mới" ở trên.</div></div>');
  }
  ve();
  ov.appendChild(box); document.body.appendChild(ov);

  var inp = box.querySelector('#bgKhTim');
  var tre = null;
  inp.oninput = function () {
    if (tre) clearTimeout(tre);
    var q = inp.value;
    ve(true);
    tre = setTimeout(async function () {
      try { ds = (await api('vagabond.bao_gia.tim_khach', { tim: q, so_dong: 60 })) || []; ve(); }
      catch (e) { ds = []; ve(); }
    }, 350);
  };
  function dong() { ov.remove(); }
  ov.onclick = function (e) { if (e.target === ov) dong(); };
  box.querySelector('.x').onclick = dong;

  lst.onclick = async function (e) {
    var r = e.target.closest('[data-kh]'); if (!r) return;
    var ma = r.getAttribute('data-kh');
    dong();
    if (ma === '_tao') { bgTaoKhach(name, true); return; }
    if (!ma) { bgTay.khach_hang = ''; return go(function () { scrBgSua(name); }, true); }
    bgTay.khach_hang = ma;
    busy(true);
    try {
      var t = await api('vagabond.bao_gia.thong_tin_khach', { khach: ma });
      ['ten_khach', 'ma_so_thue', 'dia_chi', 'nguoi_lien_he', 'chuc_vu', 'dien_thoai', 'email'].forEach(function (f) {
        if (t[f]) bgTay[f] = t[f];
      });
    } catch (e2) { }
    busy(false);
    go(function () { scrBgSua(name); }, true);
  };
  setTimeout(function () { try { inp.focus(); } catch (e) { } }, 120);
}

/* ---------- Go ma so thue, may tu dien ten va dia chi ---------- */
async function bgTraMst(name, tuNut) {
  bgDoc();
  var mst = String(bgTay.ma_so_thue || '').trim();
  var so = mst.replace(/\D/g, '');
  if (so.length !== 10 && so.length !== 12 && so.length !== 13) {
    if (tuNut) baoTin('Mã số thuế phải 10, 12 hoặc 13 số. Anh chị vui lòng kiểm lại.');
    return;
  }
  if (bgTay._mst_da_tra === mst && !tuNut) return;
  bgTay._mst_da_tra = mst;
  busy(true);
  var kq;
  try { kq = await api('vagabond.api.tra_mst', { mst: mst }); }
  catch (e) { busy(false); if (tuNut) baoTin('Không gọi được Cổng thông tin doanh nghiệp. Anh chị vui lòng điền tay.'); return; }
  busy(false);
  if (!kq || !kq.ok) {
    /* KHONG chan viec nhap: ho kinh doanh thuong khong co tren cong, ma
       chan o day thi nguoi nhap tuong minh go sai so. */
    bgTay._mst_bao = 'Không tra được mã số thuế này. Anh chị vui lòng điền tay.';
    return go(function () { scrBgSua(name); }, true);
  }
  var ten = kq.ten || '';
  var dc = kq.dia_chi || '';
  var cu = String(bgTay.ten_khach || '').trim();
  /* Luat "may khong de chu nguoi that": o da co chu khac thi phai hoi. */
  if (cu && ten && cu.toLowerCase() !== ten.toLowerCase()) {
    if (!await hoiCo('Thay tên công ty?',
      'Cổng thông tin doanh nghiệp trả về:\n\n' + ten +
      '\n\nÔ đang có: ' + cu + '\n\nThay bằng tên tra được?', 'Thay')) return;
  }
  if (ten) bgTay.ten_khach = ten;
  if (dc && !String(bgTay.dia_chi || '').trim()) bgTay.dia_chi = dc;
  if (kq.ma_so_thue) bgTay.ma_so_thue = kq.ma_so_thue;
  bgTay._mst_bao = 'Đã lấy từ Cổng thông tin doanh nghiệp.';
  go(function () { scrBgSua(name); }, true);
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


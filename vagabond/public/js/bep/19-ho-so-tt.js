/* ============ HO SO THANH TOAN NHA CUNG CAP (APP) ============================
   Anh Viet 13/08/2026: "anh thay thao tac tren desktop bi roi qua nen minh
   lam tren app". Ba man: danh sach co chip, lap ho so bang cach tick hoa don,
   va man chi tiet mang ca chuoi duyet.

   Luong: thu mua lap -> ke toan (FIN) duyet -> giam doc duyet -> ke toan
   chuyen tien, may do SePay khop giao dich roi sinh but toan clear cong no
   -> bam mot nut gui thu bao nha cung cap. */
var hsTT = '', hsNcc = '', hsTu = null, hsDen = null, hsKhoang = 90, hsTim = '', hsLoai = '', hsCpThue = '';
var hsMau = {
  'Nhap': ['#f8fafc', '#e2e8f0', '#475569', '📝'],
  'Cho ke toan': ['#fff7ed', '#fed7aa', '#9a3412', '⏳'],
  'Cho giam doc': ['#eff6ff', '#bfdbfe', '#1e40af', '👔'],
  'Da duyet': ['#f0fdf4', '#bbf7d0', '#166534', '✅'],
  'Da thanh toan': ['#ecfeff', '#a5f3fc', '#0e7490', '💸'],
  'Tu choi': ['#fef2f2', '#fecaca', '#991b1b', '⛔'],
  'Huy': ['#f3f4f6', '#e5e7eb', '#6b7280', '🚫']
};
function hsKhoangNgay() {
  if (hsTu && hsDen) return { tu: hsTu, den: hsDen };
  return { so_ngay: hsKhoang };
}
function hsNgayVn(s) {
  var p = String(s || '').split('-');
  return p.length === 3 ? p[2] + '/' + p[1] + '/' + p[0] : String(s || '');
}

async function scrHoSoTT() {
  frame('Hồ sơ thanh toán', '<div class="emp"><div class="e1">⏳</div><div>Đang tải hồ sơ...</div></div>');
  var kq;
  var ts = hsKhoangNgay();
  if (hsNcc) ts.ncc = hsNcc;
  if (hsTim) ts.tu_khoa = hsTim;
  if (hsLoai) ts.loai = hsLoai;
  if (hsCpThue) ts.loai_cp_thue = hsCpThue;
  try { kq = await api('vagabond.ho_so_tt.danh_sach', ts); }
  catch (e) { frame('Hồ sơ thanh toán', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var rows = kq.rows || [], NH = kq.nhan || {}, Q = kq.quyen || {};

  var html = '<div class="card" style="padding:12px 14px;font-size:13px;line-height:1.6;color:#374151">' +
    'Gom hoá đơn mua đến hạn của một nhà cung cấp thành một hồ sơ, kế toán duyệt rồi giám đốc duyệt, chuyển tiền xong máy dò SePay và tự xoá công nợ. Xong bấm một nút là gửi thư báo nhà cung cấp.</div>';

  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
    [[30, '30 ngày'], [90, '90 ngày'], [180, '6 tháng'], [365, '1 năm']].map(function (x) {
      return posChipNut('data-hsng="' + x[0] + '"', x[1], !hsTu && hsKhoang === x[0]);
    }).join('')) + '</div>';

  /* Chip loai: hai luong khac han nhau nen phai tach nhin duoc ngay. Ho so
     NCC gom hoa don mua da co trong he; ho so hoan ung la tien anh chi ung
     ra mua le, luc lap chua co hoa don nao ca. */
  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
    /* Uyen 03/09/2026: *"cho nay khong co muc Tao phieu thanh toan truoc cho
       NCC, nen khi em tao TT thi ben app se khong hien len a, tren desktop
       thi co hien a"*. Dung: bang chon luc lap co NAM luong, ma bang chip loc
       chi co BON. Luong tra truoc lap duoc ma khong loc ra duoc, va no cung
       khong nam trong bang ho so nen "Tat ca" cung khong bay ra.
       Chip thu nam va nguon du lieu di kem nam o `tra_truoc.gom_phieu`. */
    [['', '📚 Tất cả'], ['NCC', '🏭 Công nợ NCC'], ['Tra truoc', '⏩ Trả trước NCC'], ['Hoan ung HD', '🧾 Hoàn ứng có HĐ'], ['Hoan ung', '🧮 Hoàn ứng không HĐ'], ['TK cong ty', '🏦 Chi từ TK công ty']].map(function (x) {
      return posChipNut('data-hsloai="' + x[0] + '"', x[1], hsLoai === x[0]);
    }).join('')) +
    /* Loc theo loai chi phi thue: cuoi nam quyet toan TNDN chi can bam mot
       chip la ra het cac khoan khong duoc tru, khoi mo lai tung chung tu. */
    (hsLoai === 'TK cong ty' ? '<div style="margin-top:8px">' + kmHangChip(
      [['', '🧾 Mọi loại chi phí'], ['Chi phi hop le', '✅ Hợp lệ tính thuế'], ['Chi phi khong hop le', '🚫 Không hợp lệ']].map(function (x) {
        return posChipNut('data-hscpt="' + x[0] + '"', x[1], hsCpThue === x[0]);
      }).join('')) + '</div>' : '') +
    '</div>';

  /* Chip trang thai: bay dung cac trang thai CO THAT trong ky, kem so ho so
     va so tien - nhin la biet dang ket o khau nao. */
  var TT = [{ k: '', nhan: '📚 Tất cả', loc: function () { return true; } }];
  (kq.trang_thai_co || []).forEach(function (t) {
    var m = hsMau[t] || ['', '', '', '•'];
    TT.push({ k: t, nhan: m[3] + ' ' + h(NH[t] || t), loc: function (r) { return r.trang_thai === t; } });
  });
  if (!locTim(TT, hsTT) || locTim(TT, hsTT).k !== hsTT) hsTT = '';
  var f = locTim(TT, hsTT);
  html += '<div class="card" style="padding:10px 12px">' + locHang(TT, hsTT, 'data-hstt', rows) + '</div>';

  var loc = rows.filter(f.loc);
  var tong = loc.reduce(function (a, r) { return a + Number(r.tong_tien || 0); }, 0);
  var treN = loc.filter(function (r) { return r.tre_ngay > 0; });
  html += '<div class="card" style="padding:12px 14px;background:#f0fdfa;border:1.5px solid #99f6e4">' +
    '<div style="font-size:11.5px;color:#0f766e;font-weight:800;letter-spacing:.3px">TỔNG THEO BỘ LỌC' +
    (hsTT ? ' · ' + h(f.nhan) : '') + '</div>' +
    '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:5px">' +
    '<span style="font-size:13.5px;color:#374151">' + loc.length + ' hồ sơ</span>' +
    '<b style="font-size:20px;color:#0f766e">' + money(tong) + ' đ</b></div>' +
    (treN.length ? '<div style="display:flex;justify-content:space-between;font-size:12.5px;color:#b3261e;margin-top:3px"><span>Đã quá hạn trả ' + treN.length + ' hồ sơ</span><b>' + money(treN.reduce(function (a, r) { return a + Number(r.tong_tien || 0); }, 0)) + ' đ</b></div>' : '') +
    '</div>';

  /* Xuat Excel chay tren bang ho so that. Dang loc chip tra truoc thi bang
     do khong co dong nao, bam ra tep rong - bay mot nut chi de tra ve tep
     rong la mot cach noi doi nhe nhang, nen giau nut di. */
  html += '<div style="display:flex;gap:8px;margin-bottom:10px">' +
    (hsLoai === 'Tra truoc' ? '' : '<button class="btn gh" id="hsXuat" style="flex:1;margin:0">📊 Xuất Excel</button>') +
    (Q.fin ? '<button class="btn gh" id="hsSepay" style="flex:1;margin:0">🏦 Dò SePay</button>' : '') +
    '</div>';

  html += '<div class="sec">Danh sách hồ sơ · bấm để xem và duyệt</div><div class="card">';
  if (!rows.length) html += '<div class="emp" style="padding:24px"><div class="e1">📁</div><div>Chưa có hồ sơ nào trong khoảng này. Bấm dấu ➕ để lập hồ sơ đầu tiên.</div></div>';
  else if (!loc.length) html += '<div class="emp" style="padding:24px"><div class="e1">✅</div><div>Không có hồ sơ nào thuộc nhóm <b>' + h(f.nhan) + '</b>.</div></div>';
  loc.forEach(function (r) {
    var m = hsMau[r.trang_thai] || ['#f3f4f6', '#e5e7eb', '#374151', '•'];
    html += '<div class="hub" data-hs="' + h(r.name) + '"' + (r.la_phieu_chi ? ' data-hspc="1"' : '') + '>' +
      '<div class="hub-i" style="background:' + m[0] + '">' + m[3] + '</div>' +
      '<div class="hub-t"><div class="t1">' + h(r.ten_ncc || r.nha_cung_cap) + '</div>' +
      '<div class="t2">' + h(r.ma) + ' · ' + hsNgayVn(r.ngay) + ' · ' + r.so_hd + (r.la_phieu_chi ? ' đơn mua' : (r.loai === 'Hoan ung' ? ' khoản' : ' hoá đơn')) + '</div>' +
      '<div style="margin-top:4px"><span style="display:inline-block;background:' + m[0] +
      ';border:1px solid ' + m[1] + ';color:' + m[2] + ';border-radius:999px;padding:2px 9px;font-size:11.5px;font-weight:700">' +
      h(r.nhan) + '</span>' +
      (r.loai === 'Hoan ung' || r.loai === 'Hoan ung HD' ? '<span style="margin-left:6px;display:inline-block;background:#fffbeb;border:1px solid #fde68a;color:#92400e;border-radius:999px;padding:2px 9px;font-size:11.5px;font-weight:700">' + (r.loai === 'Hoan ung HD' ? '🧾 hoàn ứng có HĐ' : '🧮 hoàn ứng không HĐ') + '</span>' : '') +
      (r.la_phieu_chi ? '<span style="margin-left:6px;display:inline-block;background:#eff6ff;border:1px solid #bfdbfe;color:#1e40af;border-radius:999px;padding:2px 9px;font-size:11.5px;font-weight:700">⏩ trả trước</span>' : '') +
      /* Phieu tra truoc khong co han tra - no la tien di TRUOC - nen cai
         dang lo la no nam cho bao lau chu khong phai tre han bao nhieu. */
      (r.cho_ngay > 7 ? '<span style="margin-left:7px;font-size:11.5px;color:#b3261e;font-weight:700">nằm chờ ' + r.cho_ngay + ' ngày</span>' : '') +
      (r.tre_ngay > 0 ? '<span style="margin-left:7px;font-size:11.5px;color:#b3261e;font-weight:700">quá hạn ' + r.tre_ngay + ' ngày</span>' : '') +
      (r.email_da_gui ? '<span style="margin-left:7px;font-size:11.5px;color:#0e7490">✉️ đã báo NCC</span>' : '') +
      /* Ho so da duyet ma chua co uy nhiem chi thi khong ghi nhan thanh toan
         duoc. Bay ngay tren danh sach de chi Dung tai UNC ve mot lot, khoi
         mo tung to ra moi biet to nao con thieu. */
      (r.trang_thai === 'Da duyet' && !r.co_unc
        ? '<span style="margin-left:7px;font-size:11.5px;color:#b45309;font-weight:700">📎 chưa có UNC</span>' : '') +
      '</div></div>' +
      '<b style="white-space:nowrap">' + money(r.tong_tien) + ' đ</b></div>';
  });
  html += '</div>';

  var b = frame('Hồ sơ thanh toán', html, Q.lap ? { action: '➕', onAction: hsChonLoaiMoi } : {});
  Array.prototype.forEach.call(document.querySelectorAll('[data-hsng]'), function (el) {
    el.onclick = function () { hsKhoang = +el.getAttribute('data-hsng'); hsTu = null; hsDen = null; go(scrHoSoTT, true); };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-hstt]'), function (el) {
    el.onclick = function () { hsTT = el.getAttribute('data-hstt'); go(scrHoSoTT, true); };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-hsloai]'), function (el) {
    el.onclick = function () { hsLoai = el.getAttribute('data-hsloai'); go(scrHoSoTT, true); };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-hscpt]'), function (el) {
    el.onclick = function () { hsCpThue = el.getAttribute('data-hscpt'); go(scrHoSoTT, true); };
  });
  b.addEventListener('click', function (e) {
    var r = e.target.closest('[data-hs]'); if (!r) return;
    var nm = r.getAttribute('data-hs');
    /* Dong tra truoc la mot phieu chi, khong phai mot ho so. Man chi tiet
       ho so doc bang khac nen mo ra se bao khong tim thay. Duong duyet cua
       no van la man Duyet phieu chi nhu cu - day chi la cua so nhin. */
    if (r.getAttribute('data-hspc') === '1') return go(function () { scrPayView(nm); });
    go(function () { scrHoSoTTView(nm); });
  });
  var bx = document.getElementById('hsXuat');
  if (bx) bx.onclick = async function () {
    busy(true);
    try {
      var t2 = hsKhoangNgay();
      if (hsTT) t2.trang_thai = hsTT;
      if (hsNcc) t2.ncc = hsNcc;
      if (hsLoai) t2.loai = hsLoai;
      var fl = await api('vagabond.ho_so_tt.xuat_excel', t2);
      busy(false); bcTaiVe(fl.ten_file, fl.b64); toast('Đã tải ' + fl.ten_file);
    } catch (er) { busy(false); baoTin((er && er.message) || 'Xuất Excel lỗi'); }
  };
  var bs = document.getElementById('hsSepay');
  if (bs) bs.onclick = async function () {
    busy(true);
    var kq2;
    try { kq2 = await api('vagabond.ho_so_tt.kiem_sepay', {}); } catch (er) { busy(false); return baoTin((er && er.message) || 'Dò lỗi'); }
    busy(false);
    if (!(kq2.rows || []).length) return toast('Không có hồ sơ nào đang chờ chuyển tiền.');
    var mo = kq2.rows.map(function (x) {
      return (x.du ? '✅ ' : '⏳ ') + x.ma + ': ngân hàng đã chi ' + money(x.da_chi) + ' / ' + money(x.tong_tien) + ' đ';
    }).join('\n');
    baoTin('Dò SePay ' + kq2.rows.length + ' hồ sơ, ' + kq2.so_du + ' hồ sơ đã đủ tiền:\n\n' + mo +
      '\n\nMở từng hồ sơ đủ tiền rồi bấm Ghi nhận đã thanh toán để xoá công nợ.');
  };
}

/* ---------- Lap ho so: chon nha cung cap roi tick hoa don ---------- */
var hsTaoNcc = '', hsTaoChon = {}, hsTaoGhiChu = '', hsTaoLoai = 'NCC';
/* Tu khoa dang go o o tim hoa don. PHAI giu ngoai DOM: moi lan tick mot to
   la `go(scrHoSoTTTao, true)` dung lai ca man, o tim ve rong va bang hoa don
   bay lai day du. Codex neu tren PR #198: luc do nut "Chon het dang hien"
   khong con hien cai gi ca ma vo tron danh sach - dung nguoc voi cai ten no
   mang. */
var hsHdTu = '';
/* Nguoi da ung tien mua ho, tuc nguoi NHAN lai tien. Chi dung cho luong
   hoan ung co hoa don. */
/* `hsUngTim` da bo o v333: o go tim khong con giu tu khoa trong bien va
   khong con lam ve lai man, no loc thang tren DOM. */
var hsTaoNguoiUng = '', hsTaoDsUng = null;
/* Tai khoan nhan tien cua man hoan ung CO hoa don. Anh Viet 28/08/2026:
   man nay truoc khong co o chon nen may lay dai tai khoan mac dinh cua
   nguoi ung; anh Viet co ca ACB lan OCB nen doan sai la chuyen nham
   ngan hang. `hsTkDs` cache theo tung nguoi, doi nguoi thi nap lai. */
var hsTkHoan = '', hsTkDs = null, hsTkCua = '';

/* Danh so cac khoi tren form nhap lieu.

   Anh Viet 21/08/2026: "UX cac form nhap lieu hien tai con hoi can". Form
   da chia khoi bang the .sec va .card bo goc tu truoc, nhung khong danh so
   nen nhin vao khong biet con may buoc nua moi xong.

   Dem TANG DAN theo thu tu khoi thuc su duoc dung, chu khong danh so cung.
   Man Chi tu TK cong ty co khoi an hien theo loai chi phi thue; danh so
   cung thi co hom ra "1, 2, 3, 5" va nguoi dung tuong minh bo sot mot buoc.
*/
var hsoBuoc = 0;

function hsoKhoi(ten) {
  hsoBuoc += 1;
  return '<div class="sec">' + hsoBuoc + ' · ' + ten + '</div>';
}

/* ---------- Nối phiếu thanh toán nội bộ vào một dòng hoá đơn ----------

   Anh Việt chốt 04/09/2026: ở màn hoàn ứng CÓ hoá đơn, phiếu nội bộ chỉ
   đóng vai CHỨNG TỪ, không đụng tới số tiền. Số tiền luôn lấy theo hoá đơn.
   Máy kéo ảnh chứng từ của phiếu sang dòng và khoá phiếu lại, để không ai
   nối nó lần nữa bên màn hoàn ứng không hoá đơn rồi đề nghị hoàn tiếp. */
var hsPhieuCua = {};

function hsODongPhieu(maHd) {
  var co = (hsPhieuCua[maHd] || '').trim();
  return '<div data-hsphieu="' + h(maHd) + '" style="cursor:pointer;margin-top:5px;' +
    'display:inline-block;border:1.5px solid ' + (co ? '#c7d2fe' : '#e5e7eb') +
    ';background:' + (co ? '#eef2ff' : '#fff') + ';border-radius:8px;padding:4px 8px;' +
    'font-size:11.5px;font-weight:' + (co ? '700' : '500') + ';color:' +
    (co ? '#4338ca' : '#6b7280') + '">' +
    (co ? '🔗 ' + h(co) : '🔗 Nối phiếu nội bộ') + '</div>';
}

async function hsNoiPhieuVaoHd(maHd) {
  busy(true);
  var kq;
  try { kq = await api('vagabond.ho_so_tt.ds_phieu_noi_bo', {}); }
  catch (e) { busy(false); return baoTin(errMsg(e) || 'Chưa đọc được danh sách phiếu.', 'Lỗi'); }
  busy(false);
  if (kq && kq.loi) {
    return baoTin(kq.loi + '\n\nĐây là lỗi đọc dữ liệu, KHÔNG phải là không có phiếu.',
      'Chưa đọc được danh sách');
  }
  var ds = (kq && kq.ds) || [];
  if (!ds.length) {
    return baoTin('Không có phiếu thanh toán nội bộ nào đã duyệt mà chưa nối hồ sơ.',
      'Chưa có phiếu nào');
  }
  var daDung = {};
  Object.keys(hsPhieuCua).forEach(function (k) {
    var m = (hsPhieuCua[k] || '').trim();
    if (m && k !== maHd) daDung[m] = k;
  });
  var muc = ds.map(function (r) {
    var oHd = daDung[r.ma];
    return {
      value: r.ma,
      label: (oHd ? '⚠️ ' : '') + r.ten + ' · ' + money(r.so_tien) + ' đ',
      phu: (oHd ? 'ĐÃ NỐI Ở HOÁ ĐƠN ' + oHd + ' · ' : '') +
           r.ma + ' · ' + (r.nguoi_ten || r.nguoi_tao) + ' · ' + hsNgayVn(r.ngay) +
           ' · ' + r.trang_thai + (r.so_tep ? ' · ' + r.so_tep + ' tệp' : ' · chưa có tệp'),
      tim: r.ma + ' ' + r.ten + ' ' + (r.nguoi_ten || '') + ' ' + (r.dien_giai || '')
    };
  });
  muc.unshift({ value: '', label: '✖ Bỏ nối phiếu khỏi hoá đơn này', phu: 'Gỡ liên kết, không xoá phiếu', tim: 'bo go' });
  sheet('Chứng từ cho hoá đơn ' + maHd, muc, hsPhieuCua[maHd] || '', function (it) {
    var m = (it.value || '').trim();
    if (m && daDung[m]) {
      return baoTin('Phiếu ' + m + ' đã nối vào hoá đơn ' + daDung[m] + ' trong hồ sơ này rồi.\n\n' +
        'Mỗi phiếu chỉ nối được một lần.', 'Phiếu đã dùng rồi');
    }
    if (m) hsPhieuCua[maHd] = m; else delete hsPhieuCua[maHd];
    go(scrHoSoTTTao, true);
  }, true);
}

/* ==================== Ô CHỌN NHÀ CUNG CẤP (Issue #196) ====================

Anh Việt 05/09/2026: *"danh sách NCC về mặt hiển thị đang hiển thị hết ra nên
rất dài, em gom lại thành dropdown dùm anh, có ô tìm kiếm, kế bên các NCC khi
tìm ra thì có thêm các chip nợ bao nhiêu, còn bao nhiêu hoá đơn chưa ghi sổ"*.

Chữ "dropdown" ở đây KHÔNG được làm bằng thẻ <select>: AGENTS.md mục 2b cấm
thẻ đó trên các màn này. Dùng `sheet()` của 00-nen.js, vốn đã có sẵn ô tìm và
đã chạy ổn ở nhiều màn khác.

Chữ nghĩa của chip nằm ở đây, còn QUYẾT ĐỊNH chip nào hiện và mang con số nào
thì nằm ở phép thuần `vagabond/chon_ncc.py`, để kiểm thử được mà không cần
site. */

var HS_CHIP_NCC = {
  lap_duoc: function (c) { return c.so + ' hoá đơn lập được · ' + money(c.tien) + ' đ'; },
  qua_han: function (c) { return '⚠️ quá hạn ' + money(c.tien) + ' đ'; },
  khong_lap_duoc: function (c) { return money(c.tien) + ' đ không lập được ở đây'; },
  nhap: function (c) { return c.so + ' hoá đơn còn nháp'; }
};

function hsChipNcc(o) {
  var ds = (o && o.chip) || [];
  if (!ds.length) return 'Không còn nợ, không có hoá đơn nháp';
  return ds.map(function (c) {
    var f = HS_CHIP_NCC[c.ma];
    return h(f ? f(c) : c.ma);
  }).join(' · ');
}

function hsMoChonNcc(ncc, laHU, chon) {
  var muc = [];
  /* Luong hoan ung gom duoc nhieu nha mot luc nen phai co duong quay ve
     "tat ca". Luong cong no NCC thi mot ho so chi mang mot nha, khong co
     muc nay. */
  if (laHU) muc.push({ value: '', label: 'Tất cả nhà cung cấp', icon: '📚',
    phu: 'Gộp hoá đơn của mọi nhà vào một hồ sơ' });
  (ncc || []).forEach(function (x) {
    /* `sheet()` cua 00-nen.js chi ha chu thuong chu KHONG bo dau, trong khi
       o tim cu (`vgbNoiOTim`) co `mvKhongDau` ca hai phia. Codex neu tren PR
       #198: doi sang tam truot ma khong bu lai la go "dien luc" khong con ra
       "ĐIỆN LỰC" nua. Nhet ban KHONG DAU vao truong `tim` de bu, con go co
       dau thi da khop o `label`. */
    muc.push({ value: x.ncc, label: x.ten, icon: '🏭', phu: hsChipNcc(x),
      tim: mvKhongDau(x.ten) + ' ' + x.ncc });
  });
  if (!muc.length) return baoTin('Máy chưa đọc được nhà cung cấp nào. ' +
    'Thoát ra rồi mở lại màn này một lần; vẫn trống thì nhờ chị Dung kiểm ' +
    'xem danh mục Nhà cung cấp bên Next có bị tắt hết không.',
    'Không có gì để chọn');
  sheet('Chọn nhà cung cấp', muc, hsTaoNcc || '', function (it) { chon(it.value); }, true);
}

/* ==================== XEM VÌ SAO THIẾU HOÁ ĐƠN ====================

Chị Dung nói *"Nếu list ra mà thiếu có nghĩa là chưa hạch toán"*. Câu đó
KHÔNG đúng với cách hệ đang chạy, và tin theo nó thì hỏng thật:
`hoa_don_cho_tra()` còn lọc theo 365 ngày và còn giấu những tờ đang nằm trong
hồ sơ khác. Gõ tay lại một khoản mà hệ đã có tờ hoá đơn nháp thì tới bước
giám đốc duyệt máy sinh thêm một hoá đơn mua nữa, thành hoá đơn trùng trên sổ.

Nên màn này nói thẳng ra bốn lý do có thật, kèm mã hồ sơ đang giữ tờ đó, và
dặn rõ tờ còn nháp thì nhờ kế toán ghi sổ chứ đừng gõ lại. Anh Việt chốt
hướng này 05/09/2026. */

var HS_NHAN_LY_DO = {
  nhap: 'Còn nháp, chưa ghi sổ',
  ho_so_khac: 'Đang nằm trong hồ sơ khác',
  ngoai_ky: 'Ngoài khoảng ngày đang lọc',
  da_tra: 'Đã trả xong, không còn nợ',
  huy: 'Đã huỷ'
};

var hsVsNcc = '', hsVsDl = null, hsVsTu = '';

/* Ô TÌM LUÔN HIỆN cho màn "Vì sao thiếu".
   ------------------------------------------------------------------
   `vgbOTim` có ngưỡng: danh sách dưới `VGB_NGUONG_TIM` (7) mục thì nó trả
   về chuỗi RỖNG, vì nói chung bày ô tìm cho ba dòng là làm phiền. Màn này
   khác hẳn: ô tìm ở đây không chỉ lọc trên DOM mà còn là CỬA DUY NHẤT để
   hỏi máy chủ, tức là đường duy nhất tra ra tờ nằm ngoài 500 tờ máy chủ
   vừa gửi về. Giấu nó đi là khoá luôn đường đó.

   Vòng trước truyền `vgbOTim('hsVsTim', 2, ...)` vì tưởng tham số thứ hai
   là cờ bật; nó là SỐ MỤC, nên ô tìm không bao giờ được vẽ và cả cơ chế
   Enter chết theo. Codex bắt đúng lỗi này trên PR #200 bằng cách CHẠY thật
   hàm đó chứ không đọc chuỗi nguồn. Giữ nguyên hình dạng thẻ như `vgbOTim`
   để `vgbNoiOTim` nối vào được. */
function hsOTimLuon(idO, goiY) {
  return '<input class="tin" id="' + h(idO) + '" type="search" autocomplete="off" ' +
    'placeholder="' + h(goiY) + '" style="margin:0 0 9px">' +
    '<div id="' + h(idO) + 'Trong" style="display:none;font-size:12.5px;color:#b45309;' +
    'padding:6px 2px 9px;line-height:1.55">Không có tờ nào khớp trong danh sách đang bày. ' +
    'Bấm Enter để tìm cả kho, hoặc xoá bớt chữ.</div>';
}

/* Nối ô tìm của màn tra cứu: gõ là lọc DOM cho nhanh tay, Enter là hỏi
   thẳng máy chủ. Dùng chung cho cả hai nhánh của màn để chúng không lệch. */
function hsVsNoiOTim(b) {
  var oV = document.getElementById('hsVsTim');
  if (!oV) return;
  oV.value = hsVsTu;
  oV.addEventListener('input', function () { hsVsTu = oV.value; });
  oV.addEventListener('keydown', function (e) {
    if (e.key !== 'Enter') return;
    e.preventDefault(); e.stopPropagation();
    hsVsTu = oV.value; hsVsDl = null;
    go(scrViSaoThieu, true);
  }, true);
  vgbNoiOTim(b, 'hsVsTim', '[data-vshd]');
}

function hsViSaoThieu(ncc) {
  if (!ncc) return baoTin('Chọn một nhà cung cấp ở ô phía trên rồi bấm lại nút này.',
    'Chưa chọn nhà');
  hsVsNcc = ncc; hsVsDl = null; hsVsTu = '';
  go(scrViSaoThieu);
}

async function scrViSaoThieu() {
  var ten = hsVsNcc;
  frame('Vì sao thiếu hoá đơn', '<div class="emp"><div class="e1">⏳</div><div>Đang dò từng tờ hoá đơn...</div></div>');
  if (!hsVsDl) {
    try { hsVsDl = await api('vagabond.ho_so_tt.ly_do_thieu_hd',
      { ncc: hsVsNcc, so_ngay: 365, tu_khoa: hsVsTu }); }
    catch (e) {
      /* QT-24: cau bao loi phai noi viec lam tiep. */
      hsVsDl = null;
      frame('Vì sao thiếu hoá đơn',
        '<div class="emp"><div class="e1">⚠️</div><div>' +
        h(errMsg(e) || 'Máy chủ không trả lời') +
        '<br><br>Kiểm lại mạng rồi bấm nút ⬅ quay ra, vào lại màn lập hồ sơ và ' +
        'bấm nút này một lần nữa. Vẫn hỏng thì chụp màn hình gửi anh Việt, ' +
        'trong lúc chờ thì bảng hoá đơn ở màn trước vẫn tick và lập bình thường.</div></div>');
      return;
    }
  }
  var kq = hsVsDl;
  ten = kq.ten || hsVsNcc;

  /* Go het cac nhom thanh MOT bang phang, moi dong mang san nhan ly do cua
     no. Neu de thanh tung khoi co tieu de thi o tim loc mat cac dong con
     tieu de o lai lo lung, ma dung mot o tim cho ca bang moi la cai chi
     Dung can: go so hoa don vao la ra ngay to do nam o nhom nao. */
  var dong = [];
  (kq.nhom || []).forEach(function (g) {
    (g.hoa_don || []).forEach(function (x) { dong.push({ g: g, x: x }); });
  });

  var html = '<div class="card" style="padding:12px 14px;font-size:13px;line-height:1.6;color:#374151">' +
    '<b>' + h(ten) + '</b><br>Đang chọn được <b>' + (kq.chon_duoc || 0) + '</b> hoá đơn ở bảng tick. ' +
    'Những tờ dưới đây KHÔNG hiện ra ở đó, kèm lý do thật của từng tờ.</div>';

  if (!(kq.nhom || []).length) {
    /* BA CANH KHAC NHAU, ba lai khac nhau. Codex neu tren PR #200: to tim
       ra ma DANG CHON DUOC thi may chu tra `chon_duoc > 0` va khong co
       nhom ly do nao, nen man cu vua bao "dang chon duoc 1 hoa don" vua
       bao "khong co to nao khop" - hai cau chan nhau. Dung o man sinh ra
       de chong nhap trung, cau do de day nguoi ta di go tay lai. */
    var daCo = hsVsTu && Number(kq.chon_duoc || 0) > 0;
    html += '<div class="emp" style="padding:24px"><div class="e1">' +
      (daCo ? '✅' : (hsVsTu ? '🔎' : '✅')) + '</div><div>' +
      (daCo
        ? 'Tờ khớp "' + h(hsVsTu) + '" <b>đã có trong hệ và đang chọn được</b>. ' +
          'Nó không nằm ở đây vì đây chỉ là nơi liệt kê tờ bị giấu đi. ' +
          'Quay ra bảng tick ở màn lập hồ sơ, gõ đúng số đó vào ô tìm rồi tick. ' +
          '<b>Đừng gõ tay lại</b> khoản này.'
        : (hsVsTu
          ? 'Không có tờ nào của nhà này khớp "' + h(hsVsTu) + '". Xoá bớt chữ rồi bấm Enter tìm lại.'
          : 'Không có tờ nào bị giấu đi. Mọi hoá đơn của nhà này đều đang hiện ở bảng tick.')) +
      '</div></div>';
    /* Vẫn bày ô tìm ra khi gõ hụt, không thì người dùng kẹt trong màn này
       và phải quay ra vào lại mới tìm được lần hai. */
    if (hsVsTu) {
      html += '<div class="card" style="padding:10px 12px">' +
        hsOTimLuon('hsVsTim', '🔎 Gõ số hoá đơn rồi bấm Enter để tìm cả kho') + '</div>';
    }
    var b0 = frame('Vì sao thiếu hoá đơn', html);
    hsVsNoiOTim(b0);
    return;
  }

  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
    (kq.nhom || []).map(function (g) {
      return posChipNut('', (HS_NHAN_LY_DO[g.ly_do] || g.ly_do) + ': ' + g.so + ' tờ · ' + money(g.tien) + ' đ', false);
    }).join('')) + '</div>';

  var coNhap = (kq.nhom || []).filter(function (g) { return g.ly_do === 'nhap'; })[0];
  if (coNhap) {
    html += '<div class="card" style="padding:12px 14px;background:#fffbeb;border:1.5px solid #fde68a;' +
      'font-size:13px;line-height:1.6;color:#92400e">' +
      'Tờ còn nháp thì nhờ kế toán ghi sổ rồi quay lại đây tick. ' +
      '<b>ĐỪNG gõ tay lại</b> khoản đó ở luồng hoàn ứng: gõ lại là máy sinh thêm ' +
      'một hoá đơn mua nữa, thành hoá đơn trùng trên sổ.</div>';
  }

  html += hsoKhoi('Từng tờ · ' + dong.length + ' tờ' +
      (hsVsTu ? ' · đang tìm "' + h(hsVsTu) + '"' : '')) + '<div class="card">' +
    /* O tim nay co HAI tang. Go la loc ngay tren DOM cho nhanh tay, con
       Enter thi hoi thang may chu. Phai co tang thu hai vi may chu cat 500
       to moi nhom: to thu 501 khong nam trong DOM nen loc kieu gi cung
       khong ra. Codex neu dung diem nay vong hai tren PR #198. */
    hsOTimLuon('hsVsTim', '🔎 Gõ số hoá đơn rồi bấm Enter để tìm cả kho');
  dong.forEach(function (d) {
    html += '<div class="hub" data-vshd="' + h(d.x.name) + '">' +
      '<div class="hub-i">📄</div><div class="hub-t">' +
      '<div class="t1">' + h(d.x.so_hd_ncc || d.x.name) + '</div>' +
      '<div class="t2">' + h(d.x.name) + (d.x.posting_date ? ' · ' + hsNgayVn(d.x.posting_date) : '') + '</div>' +
      '<div class="t2" style="color:#b45309;font-weight:700">' +
      h(HS_NHAN_LY_DO[d.g.ly_do] || d.g.ly_do) +
      (d.x.ho_so_giu ? ' · hồ sơ ' + h(d.x.ho_so_giu) : '') + '</div>' +
      '</div><b style="white-space:nowrap">' + money(d.x.tong) + ' đ</b></div>';
  });
  html += '</div>';

  var biCat = (kq.nhom || []).filter(function (g) { return g.bi_cat; }).length;
  if (biCat) {
    html += '<div style="font-size:12px;color:#b45309;padding:0 2px 10px;line-height:1.6">' +
      'Nhà này có nhóm quá 500 tờ nên máy chỉ bày 500 tờ đầu <b>của nhóm đó</b>. ' +
      'Cần tra một tờ nằm ngoài khoảng này thì gõ số hoá đơn vào ô trên rồi ' +
      '<b>bấm Enter</b>: máy chủ lọc trước khi cắt nên tờ nào cũng ra.</div>';
  }

  var b = frame('Vì sao thiếu hoá đơn', html);
  hsVsNoiOTim(b);
}


async function scrHoSoTTTao() {
  hsoBuoc = 0;
  var laHU = hsTaoLoai === 'Hoan ung HD';
  frame(laHU ? 'Lập hồ sơ hoàn ứng có hoá đơn' : 'Lập hồ sơ thanh toán', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc công nợ phải trả...</div></div>');
  var dsn;
  /* Doi tu `ds_ncc_con_no` sang `ds_ncc_chon` (Issue #196). Ham cu chi
     biet hoa don DA GHI SO, nen nha nao chi con hoa don nhap la khong tim
     ra. Ham moi gom theo lo va tach bach bon con so: no da ghi so, phan
     THAT SU lap duoc, phan qua han, va so to con nhap. */
  try { dsn = await api('vagabond.ho_so_tt.ds_ncc_chon', { so_ngay: 365 }); }
  catch (e) { frame('Lập hồ sơ thanh toán', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var ncc = dsn.ncc || [];
  /* Luong hoan ung mo san o che do TAT CA nha cung cap: Uyen mua le te nen
     mot ho so cua chi thuong tro toi chuc nha khac nhau. Luong cong no NCC
     van chon dung mot nha nhu cu. */
  /* Mac dinh chon nha DAU TIEN CON TICK DUOC. Danh sach moi co ca nha chi
     con hoa don nhap, ma nha do mo ra thi bang trong - mo man hinh len da
     thay trong la cai lam nguoi ta tuong he hong. */
  if (!laHU && !hsTaoNcc && ncc.length) {
    var dau = ncc.filter(function (x) { return (x.lap_duoc_so || 0) > 0; })[0] || ncc[0];
    hsTaoNcc = dau.ncc;
  }
  if (laHU && !hsTaoDsUng) {
    try { hsTaoDsUng = await api('vagabond.ho_so_tt.ds_nguoi_ung', {}); } catch (e3) { hsTaoDsUng = { ncc: [] }; }
  }
  /* Danh sach tai khoan nhan tien phai di THEO nguoi ung dang chon. Doi
     nguoi ma van bay tai khoan cua nguoi cu chinh la duong chuyen nham
     tien, nen cache neo vao `hsTkCua` va doi nguoi la nap lai. */
  if (laHU && hsTaoNguoiUng && hsTkCua !== hsTaoNguoiUng) {
    hsTkCua = hsTaoNguoiUng; hsTkHoan = '';
    try { hsTkDs = await api('vagabond.ho_so_tt.ds_tk_hoan_ung', { nguoi: hsTaoNguoiUng }); }
    catch (e4) { hsTkDs = { tk: [], doan: 0 }; }
    /* Chi co dung MOT tai khoan thi chon san cho do mot nhip bam. Co tu HAI
       tro len thi de trong va bat chon tay: ACB voi OCB nhin luot rat giong
       nhau, may chon ho la may chon sai ma khong ai hay. */
    var dtk = (hsTkDs && hsTkDs.tk) || [];
    if (dtk.length === 1) hsTkHoan = dtk[0].ma;
  }
  if (laHU && !hsTaoNguoiUng) { hsTkDs = null; hsTkCua = ''; hsTkHoan = ''; }

  var hd = { rows: [], tong: 0, qua_han: 0 };
  if (hsTaoNcc || laHU) {
    try { hd = await api('vagabond.ho_so_tt.hoa_don_cho_tra', { ncc: hsTaoNcc, so_ngay: 365 }); } catch (e2) { }
  }

  var tenMan = laHU ? 'Lập hồ sơ hoàn ứng có hoá đơn' : 'Lập hồ sơ thanh toán';
  var html = '<div class="card" style="padding:12px 14px;font-size:13px;line-height:1.6;color:#374151">' +
    (laHU
      ? 'Người đã ứng tiền mua hàng có hoá đơn, hàng đã nhập kho. Chọn các hoá đơn <b>còn nợ</b> để gom chung một hồ sơ, <b>gom được nhiều nhà cung cấp cùng lúc</b>. Công ty trả một lần cho người ứng, công nợ từng nhà cung cấp sạch luôn.'
      : 'Một hồ sơ gom hoá đơn của <b>một</b> nhà cung cấp, vì chuyển tiền là chuyển cho một người.') +
    ' Hoá đơn đang nằm trong hồ sơ khác thì máy giấu đi sẵn.</div>';

  /* Nguoi duoc hoan ung: bat buoc, va phai chon TRUOC khi tick hoa don.
     Do la ben NHAN tien; de may tu dien so tai khoan cua nha cung cap vao
     day nhu truoc la mo duong chuyen nham tien cho ho. */
  if (laHU) {
    /* Ve HET danh sach roi loc tren DOM, thay vi cat con 8 cai roi ve lai
       man moi lan go mot chu. Ban cu goi go(scrHoSoTTTao, true) o su kien
       change nen tren dien thoai ban phim tut xuong sau moi lan go, va
       nguoi hay dung nam ngoai top 8 thi go mai khong ra. */
    var dsu = (hsTaoDsUng && hsTaoDsUng.ncc) || [];
    var hsTk = (hsTkDs && hsTkDs.tk) || [];
    /* Nguoi hay dung xep len truoc cho de cham, phan con lai giu nguyen thu tu. */
    var hay = dsu.filter(function (x) { return x.hay_dung; })
      .concat(dsu.filter(function (x) { return !x.hay_dung; }));
    html += hsoKhoi('Người được hoàn ứng · bắt buộc') +
      '<div class="card" style="padding:10px 12px">' +
      hsOTimNcc('hsUngTim', hay.length) +
      kmHangChip(
        hay.map(function (x) {
          return posChipNut('data-hsu="' + h(x.ncc) + '"', h(x.ten), hsTaoNguoiUng === x.ncc);
        }).join('')) +
      (hsTaoNguoiUng ? '' :
        '<div style="font-size:12px;color:#b3261e;margin-top:8px;line-height:1.6">' +
        'Chưa chọn ai. Đây là người đã bỏ tiền túi mua hộ và sẽ nhận lại tiền, ' +
        'không phải nhà cung cấp trên hoá đơn.</div>') +
      hsKhungTimNcc('hsUngTim', hay.length,
        'Người mới ứng tiền lần đầu thì chưa có hồ sơ. Tạo ở đây rồi chọn luôn.') + '</div>';

    /* HOAN UNG VAO TAI KHOAN NAO
       ----------------------------------------------------------------
       Anh Viet 28/08/2026: "2 cai nay deu la gop hoa don cua cac NCC roi
       can chuyen la chuyen den tai khoan cua Nguyen Hoang Viet ngan hang
       ACB". Man hoan ung KHONG hoa don da co khoi nay tu 22/08, con man CO
       hoa don thi chua - no lang le lay tai khoan mac dinh cua nguoi ung.
       Hai man cung mot viec ma cu xu khac nhau la cho de sinh loi.

       Chi hien sau khi da chon nguoi ung, vi danh sach tai khoan la cua
       CHINH nguoi do. Chua chon nguoi thi chua biet bay tai khoan cua ai. */
    html += hsoKhoi('Hoàn ứng vào tài khoản nào · bắt buộc') +
      '<div class="card" style="padding:10px 12px">' +
      (!hsTaoNguoiUng
        ? '<div style="font-size:12.5px;color:#98a2b3;line-height:1.6">Chọn người được hoàn ứng ở trên trước, máy sẽ bày đúng các tài khoản của người đó.</div>'
        : (hsTk.length
            ? kmHangChip(hsTk.map(function (x) {
                return posChipNut('data-hstk="' + h(x.ma) + '"', h(x.nhan), hsTkHoan === x.ma);
              }).join('')) +
              '<div style="font-size:11.5px;color:' + (hsTkHoan ? '#98a2b3' : '#b3261e') + ';margin-top:8px;line-height:1.6">' +
              (hsTkHoan
                ? ((hsTkDs && hsTkDs.doan)
                    ? '⚠️ Người này chưa gắn tài khoản nào vào quỹ tạm ứng 1411, nên máy bày tạm mọi tài khoản. Nhờ chị Dung gắn đúng tài khoản ứng vào 1411 bên Next.'
                    : 'Tiền hoàn ứng trả về đúng tài khoản đã ứng ra. Số tài khoản hiện cạnh tên vì các tài khoản nhìn lướt rất giống nhau.')
                : 'Chưa chọn tài khoản nhận tiền. Người này có nhiều hơn một tài khoản nên máy không tự chọn thay, phải bấm đúng cái cần chuyển.') +
              '</div>'
            : '<div style="font-size:13px;color:#b45309;line-height:1.6">Người này chưa khai tài khoản ngân hàng nào. ' +
              'Nhờ chị Dung tạo Bank Account cho họ bên Next rồi quay lại chọn.</div>')) +
      '</div>';
  }

  /* O CHON NHA CUNG CAP (Issue #196, anh Viet 05/09/2026).
     ------------------------------------------------------------------
     Truoc day cho nay ve HET nha cung cap thanh mot bang chip, dai muot
     man hinh dien thoai. Gio thu gon thanh MOT dong, cham vao moi mo tam
     truot len co o tim - dung y anh Viet "gom lai thanh dropdown dum anh,
     co o tim kiem". AGENTS.md muc 2b cam the <select> nen dung `sheet()`
     cua 00-nen.js chu khong dung dropdown cua trinh duyet. */
  var nccDangChon = null;
  for (var iN = 0; iN < ncc.length; iN++) if (ncc[iN].ncc === hsTaoNcc) nccDangChon = ncc[iN];
  html += hsoKhoi('Nhà cung cấp' + (ncc.length ? ' · ' + ncc.length + ' nhà' : '')) +
    '<div class="card"><div class="hub" id="hsMoNcc">' +
    '<div class="hub-i">🏭</div><div class="hub-t">' +
    '<div class="t1">' + h(nccDangChon ? nccDangChon.ten : (laHU && !hsTaoNcc ? 'Tất cả nhà cung cấp' : 'Chạm để chọn nhà cung cấp')) + '</div>' +
    '<div class="t2">' + (nccDangChon ? hsChipNcc(nccDangChon) : (laHU ? 'Đang gộp hoá đơn của mọi nhà' : 'Chưa chọn nhà nào')) + '</div>' +
    '</div><b style="color:#2563eb;white-space:nowrap">Đổi</b></div></div>' +
    (laHU ? '<div style="font-size:11.5px;color:#98a2b3;margin:-4px 0 10px;line-height:1.6">' +
      'Ô này chỉ để <b>lọc cho dễ nhìn</b>. Đổi nhà không làm mất hoá đơn đã tick, ' +
      'nên anh chị tick bên nhà này rồi đổi sang nhà khác tick tiếp thoải mái.</div>' : '');

  var rows = hd.rows || [];
  /* Tick nam ngoai danh sach dang loc van phai duoc dem. Neu chi dem tren
     rows thi doi chip mot cai la o "dang chon" tut ve 0 trong khi hoa don
     van dang duoc chon - dung cai lam nguoi dung tuong minh mat du lieu. */
  var maChon = Object.keys(hsTaoChon);
  var tongChon = maChon.reduce(function (a, m) { return a + Number((hsTaoChon[m] && hsTaoChon[m].con_no) || 0); }, 0);
  var nhaChon = {};
  maChon.forEach(function (m) { var t = hsTaoChon[m] && hsTaoChon[m].ten_ncc; if (t) nhaChon[t] = 1; });
  var soNha = Object.keys(nhaChon).length;

  html += '<div class="card" style="padding:12px 14px;background:#f0fdfa;border:1.5px solid #99f6e4">' +
    '<div style="font-size:11.5px;color:#0f766e;font-weight:800">ĐANG CHỌN</div>' +
    '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:5px">' +
    '<span style="font-size:13.5px;color:#374151">' + maChon.length + ' hoá đơn' +
    (laHU && soNha ? ' · ' + soNha + ' nhà cung cấp' : '') + '</span>' +
    '<b style="font-size:20px;color:#0f766e">' + money(tongChon) + ' đ</b></div>' +
    (laHU && soNha > 1
      ? '<div style="font-size:11.5px;color:#0f766e;margin-top:6px;line-height:1.6">' +
        h(Object.keys(nhaChon).sort().join(' · ')) + '</div>' : '') + '</div>';

  html += '<div style="display:flex;gap:8px;margin-bottom:10px">' +
    '<button class="btn gh" id="hsChonHet" style="flex:1;margin:0">☑️ Chọn hết đang hiện</button>' +
    '<button class="btn gh" id="hsChonQH" style="flex:1;margin:0">⚠️ Chỉ quá hạn</button>' +
    '<button class="btn gh" id="hsBoChon" style="flex:1;margin:0">✖ Bỏ chọn</button></div>';

  html += hsoKhoi('Chứng từ tham chiếu · hoá đơn còn nợ · ' + rows.length + ' tờ') + '<div class="card">' +
    /* TIM NGAY LUC LAP (Issue #196). Ho so hoan ung gom hang chuc to cua
       nhieu nha, do bang mat het bang la cach de sot. Loc tren DOM nen tick
       da dat KHONG mat khi go, va ban phim khong tut xuong. */
    vgbOTim('hsHdTim', rows.length, '🔎 Gõ số hoá đơn, mã hoá đơn hoặc tên nhà cung cấp');
  if (!rows.length) html += '<div class="emp" style="padding:24px"><div class="e1">🎉</div><div>Không còn hoá đơn nào chờ trả ở đây.</div></div>';
  rows.forEach(function (r) {
    var da = !!hsTaoChon[r.hoa_don];
    html += '<div class="hub" data-hsh="' + h(r.hoa_don) + '"' + (da ? ' style="background:#dbeafe"' : '') + '>' +
      '<div class="hub-i">' + (da ? '☑️' : '⬜') + '</div>' +
      '<div class="hub-t"><div class="t1">' + h(r.so_hd_ncc || r.hoa_don) + '</div>' +
      /* Hien ten nha cung cap ngay tren dong khi dang gom nhieu nha, neu
         khong thi ba muoi dong hoa don trong nhu nhau. */
      (laHU ? '<div class="t2" style="color:#0f766e;font-weight:700">' + h(r.ten_ncc || r.ncc || '') + '</div>' : '') +
      '<div class="t2">' + h(r.hoa_don) + ' · HĐ ' + hsNgayVn(r.ngay_hd) + (r.han_tra ? ' · hạn ' + hsNgayVn(r.han_tra) : '') + '</div>' +
      (r.tre_ngay > 0 ? '<div class="t2" style="color:#b3261e;font-weight:700">Quá hạn ' + r.tre_ngay + ' ngày</div>' : '') +
      /* Chi hien o luong HOAN UNG va chi khi dong da duoc tick. Luong cong
         no NCC thi tien di thang toi nha cung cap, khong co ai ung tien nen
         khong co phieu noi bo nao de noi. */
      (laHU && da ? hsODongPhieu(r.hoa_don) : '') +
      '</div><b style="white-space:nowrap">' + money(r.con_no) + ' đ</b>' +
      hsONutBanTheHien(r.hoa_don) + '</div>';
  });
  html += '</div>';

  /* XEM VI SAO THIEU (Issue #196, anh Viet chot 05/09/2026).
     ------------------------------------------------------------------
     Chi Dung noi "list ra ma thieu co nghia la chua hach toan". Cau do
     KHONG dung: bang tren con loc theo 365 ngay va con giau nhung to dang
     nam trong ho so khac. Neu tin theo cau do ma go tay lai mot khoan da
     co to hoa don nhap, thi buoc giam doc duyet se sinh them mot hoa don
     mua nua - hoa don trung tren so. Nen bay ra cai nut noi that thay vi
     de nguoi dung tu suy. */
  if (hsTaoNcc) {
    html += '<button class="btn gh" id="hsViSao" style="margin:0 0 10px">' +
      '🔍 Thiếu hoá đơn? Xem vì sao</button>';
  }

  html += '<div class="card" style="padding:12px 14px"><input class="tin" id="hsGc" placeholder="Ghi chú cho hồ sơ (không bắt buộc)" value="' + h(hsTaoGhiChu) + '"></div>';

  var foot = '<div style="display:flex;gap:8px">' +
    '<button class="btn" id="hsLuu" style="flex:2">📤 Lập và gửi kế toán</button>' +
    '<button class="btn gh" id="hsLuuNhap" style="flex:1">💾 Lưu nháp</button></div>';
  var b = frame(tenMan, html, { footer: foot });

  b.addEventListener('click', function (e) {
    var n = e.target.closest('[data-hsphieu]');
    if (!n) return;
    /* Chan noi len, khong thi bam nut nay lai bo tick chinh hoa don do. */
    e.stopPropagation(); e.preventDefault();
    hsNoiPhieuVaoHd(n.getAttribute('data-hsphieu'));
  }, true);

  var ghiChon = function (r) { hsTaoChon[r.hoa_don] = { con_no: Number(r.con_no || 0), ten_ncc: r.ten_ncc || r.ncc || '' }; };

  /* Nut tai ban the hien nam NGAY canh tung hoa don. Bam vao khong duoc lam
     tick chon hoa don do nhay theo, nen phai chan noi len. */
  b.addEventListener('click', function (e) {
    var n = e.target.closest('[data-hsbth]');
    if (!n) return;
    e.stopPropagation();
    hsTaiBanTheHien(n.getAttribute('data-hsbth'));
  }, true);
  hsDemBanTheHien(hd.rows || []);

  var doiNcc = function (ma) {
    /* Doi sang nha khac thi tu khoa hoa don cua nha cu KHONG duoc mang
       theo: bang cua nha moi se trong tron trong khi chip van bao con no,
       nguoi dung tuong he hong. Codex neu tren PR #200.
       Van GIU tu khoa khi ve lai man vi tick mot to, va tuyet doi khong
       dong vao `hsTaoChon` cua luong hoan ung nhieu nha. */
    if ((ma || '') !== hsTaoNcc) hsHdTu = '';
    hsTaoNcc = ma || '';
    /* Luong hoan ung: doi nha la DOI BO LOC, khong phai bo lam lai. Xoa
       tick o day chinh la thu bat Uyen phai lam mot ho so cho moi nha cung
       cap. Luong cong no NCC thi van xoa, vi ho so do chi duoc phep mang
       mot nha. */
    /* Xoa tick toi dau thi xoa phieu noi bo toi do. Hom nay dong
       `hsPhieuCua = {}` nay la thua, vi phieu chi duoc noi o luong hoan ung
       (`laHU && da` cho `hsODongPhieu`) ma nhanh nay lai la `!laHU`. Giu
       lai de bat bien "xoa hsTaoChon la xoa ca hsPhieuCua" dung o MOI cho,
       phong ngay nao do luong cong no NCC cung noi duoc phieu. */
    if (!laHU) { hsTaoChon = {}; hsPhieuCua = {}; }
    go(scrHoSoTTTao, true);
  };
  var moNcc = document.getElementById('hsMoNcc');
  if (moNcc) moNcc.onclick = function () { hsMoChonNcc(ncc, laHU, doiNcc); };
  Array.prototype.forEach.call(document.querySelectorAll('[data-hsu]'), function (el) {
    el.onclick = function () { hsTaoNguoiUng = el.getAttribute('data-hsu'); go(scrHoSoTTTao, true); };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-hstk]'), function (el) {
    el.onclick = function () { hsTkHoan = el.getAttribute('data-hstk'); go(scrHoSoTTTao, true); };
  });
  vgbNoiOTim(b, 'hsUngTim', '[data-hsu]');
  /* O tim hoa don: loc tren DOM nen tick da dat KHONG mat khi go. Khop ca
     so hoa don cua nha cung cap, ma hoa don trong he va ten nha.
     Dat lai gia tri TRUOC khi goi `vgbNoiOTim`, vi ham do chay `chay()` mot
     lan ngay luc noi - nho vay bo loc song lai dung nhu truoc khi tick. */
  var oHd = document.getElementById('hsHdTim');
  if (oHd) {
    oHd.value = hsHdTu;
    oHd.addEventListener('input', function () { hsHdTu = oHd.value; });
  }
  vgbNoiOTim(b, 'hsHdTim', '[data-hsh]');
  /* Cai dang go trong o tim la ten se dien san khi bam Tao nha cung cap moi. */
  var oUt = document.getElementById('hsUngTim');
  hsNoiNutTaoNcc(oUt ? oUt.value.trim() : '', function (ma) {
    /* Tao xong thi nap lai danh sach, khong thi nguoi vua tao khong co
       trong `hsTaoDsUng` da cache va chip moi khong hien ra. */
    hsTaoDsUng = null;
    if (ma) { hsTaoNguoiUng = ma; }
    go(scrHoSoTTTao, true);
  });
  b.addEventListener('click', function (e) {
    var r = e.target.closest('[data-hsh]'); if (!r) return;
    var ma = r.getAttribute('data-hsh');
    if (hsTaoChon[ma]) { delete hsTaoChon[ma]; delete hsPhieuCua[ma]; }
    /* Bo tick hoa don ma van giu phieu da noi thi phieu di theo mot dong
       khong con ton tai, va may chu se khoa nham mot phieu chang cua ai. */
    else {
      var d = rows.filter(function (x) { return x.hoa_don === ma; })[0];
      if (d) ghiChon(d);
    }
    go(scrHoSoTTTao, true);
  });
  /* Codex neu tren #196: "chon het" khi dang loc phai noi ro no ap dung
     cho TAP DANG HIEN. Bam mot nut roi om ca tram hoa don ngoai man hinh
     la cach tao ra mot ho so khong ai co y dinh lap. */
  var dangHien = function () {
    var el = [].slice.call(b.querySelectorAll('[data-hsh]'));
    var ma = {};
    el.forEach(function (x) { if (x.style.display !== 'none') ma[x.getAttribute('data-hsh')] = 1; });
    return rows.filter(function (r) { return ma[r.hoa_don]; });
  };
  var g1 = document.getElementById('hsChonHet');
  if (g1) g1.onclick = function () { dangHien().forEach(ghiChon); go(scrHoSoTTTao, true); };
  var g2 = document.getElementById('hsChonQH');
  if (g2) g2.onclick = function () { hsTaoChon = {}; hsPhieuCua = {}; dangHien().forEach(function (r) { if (r.tre_ngay > 0) ghiChon(r); }); go(scrHoSoTTTao, true); };
  var gV = document.getElementById('hsViSao');
  if (gV) gV.onclick = function () { hsViSaoThieu(hsTaoNcc); };
  var g3 = document.getElementById('hsBoChon');
  if (g3) g3.onclick = function () { hsTaoChon = {}; hsPhieuCua = {}; go(scrHoSoTTTao, true); };

  var luu = async function (guiLuon) {
    var gc = document.getElementById('hsGc');
    hsTaoGhiChu = gc ? gc.value : '';
    /* Gui len dang doi tuong de mang theo `de_nghi_chi`. May chu van nhan
       ca chuoi tran lan doi tuong, nen luong cong no NCC khong doi gi. */
    var ds = Object.keys(hsTaoChon).map(function (m) {
      var o = { hoa_don: m };
      if ((hsPhieuCua[m] || '').trim()) o.de_nghi_chi = hsPhieuCua[m].trim();
      return o;
    });
    if (!ds.length) return baoTin('Chưa chọn hoá đơn nào.');
    if (laHU && !hsTaoNguoiUng) return baoTin('Chưa chọn người được hoàn ứng. Đây là người sẽ nhận lại tiền.');
    /* Chan CA hai nut, ke ca luu nhap. Ho so nhap thieu tai khoan roi de
       do vai ngay thi den luc chuyen tien khong ai nho phai chuyen di dau,
       ma o "hoan thanh ho so" thi khong ai mo lai. */
    if (laHU && !hsTkHoan) return baoTin('Chưa chọn tài khoản nhận tiền hoàn ứng. Chọn đúng ngân hàng thì uỷ nhiệm chi mới đi được.');
    busy(true);
    try {
      var kq = await api('vagabond.ho_so_tt.tao', {
        /* Ho so hoan ung khong gui ncc len: nha cung cap cua tung dong do
           may tu doc ra tu hoa don, con o nay chi la bo loc cua man hinh. */
        ncc: laHU ? '' : hsTaoNcc,
        nguoi_ung: laHU ? hsTaoNguoiUng : '',
        tk_hoan: laHU ? hsTkHoan : '',
        hoa_don: JSON.stringify(ds), ghi_chu: hsTaoGhiChu,
        gui_luon: guiLuon ? 1 : 0, loai: hsTaoLoai
      });
      busy(false);
      hsTaoChon = {}; hsTaoGhiChu = ''; hsTaoNguoiUng = ''; hsPhieuCua = {};
      hsTkHoan = ''; hsTkDs = null; hsTkCua = '';
      toast('Đã lập hồ sơ ' + kq.ma + ' · ' + money(kq.tong_tien) + ' đ', 3500);
      go(function () { scrHoSoTTView(kq.ma); }, true);
    } catch (e) { busy(false); baoTin((e && e.message) || 'Lập hồ sơ lỗi'); }
  };
  document.getElementById('hsLuu').onclick = function () { luu(true); };
  document.getElementById('hsLuuNhap').onclick = function () { luu(false); };
}

/* ---------- Lap ho so HOAN UNG: go tay tung khoan da chi ho ----------
   Anh Viet 13/08/2026: "APP nay co kha nang dinh kem cac hoa don tu nhieu
   NCC nho le khac nhau, bao gom ca hang test khong nhap kho, hang phat
   sinh, chi phi (bao tri,...)".

   Khac han man lap ho so NCC: o kia tick hoa don da co san trong he, o day
   CHUA co hoa don nao ca - Uyen go tay dung nhung gi trong xap chung tu.
   May sinh hoa don mua sau, luc giam doc duyet. */
var huNguoi = '', huDong = [], huGhiChu = '', huTamUng = 0, huTim = '';
/* Tai khoan nhan tien hoan ung (ACB hay OCB). Thay cho viec chon nha cung
   cap o man hoan ung khong hoa don - anh Viet 22/08/2026. */
var huTkHoan = '';
/* Luong 4: chi thang tu TK cong ty. Dung chung man go khoan chi voi hoan
   ung, khac o cho co them tai khoan chi, loai chi phi thue va TK No. */
var huMode = 'hu', huTkChi = '', huCpThue = '', huTkTim = '';
var huChonHd = {};
/* Goi y noi dung chi hay gap, lay tu thong ke chi phi that cua tiem. Van go
   tay duoc: danh sach chi de bam cho nhanh, khong phai de ep. */
var HU_GOI_ND = ['Tiền nước', 'Tiền điện', 'Tiền thuê nhà', 'Tiền hoàn ứng', 'Đóng BHXH', 'Đóng KPCĐ (Liên đoàn lao động)'];
/* HU_CHUNG_TU (danh sach go cung) da bo 24/08/2026: loai chung tu nay lay
   tu danh muc that qua huLayDmCt, va chon rieng cho tung dong. */
function huManHienTai() { return huMode === 'tkct' ? scrChiCongTyTao : scrHoanUngTao; }

/* KHONG THAY TEN THI PHAI TAO DUOC NGAY TAI CHO
   -------------------------------------------------
   Anh Viet 21/08/2026: chi Dung lap phieu dong BHXH, go "BHXH CO SO TAN
   DINH" roi "bao hiem xa hoi" deu khong ra gi, va man hinh khong co duong
   nao tao moi. Ca tiem co 520 nha cung cap ma khong co ben bao hiem nao.
   Bi ket o do thi chi khong lam duoc viec, ma cung khong biet phai di dau.

   Nen moi cho chon nha cung cap deu phai co ba thu: o go tim, cau noi ro
   la khong tim thay, va nut tao moi mang san chu vua go sang man tao. */
/* O GO TIM, dat NGAY TREN bang chip nha cung cap.

   v333 tach lam doi: o tim len tren vi no loc cai nam duoi, con nut tao moi
   o lai duoi cung. Ban cu de ca hai o duoi bang chip, tuc la o loc nam duoi
   cai no loc.

   O nay khong con `value` va khong con lam ve lai man. Loc chay tren DOM
   qua `vgbNoiOTim`, nen go den dau thay den do va ban phim dien thoai khong
   tut xuong sau moi chu. */
function hsOTimNcc(idO, soMuc) {
  return vgbOTim(idO, soMuc, '🔎 Gõ tên để tìm nhà cung cấp');
}

/* DUONG TAO MOI, dat DUOI bang chip.

   Diem quan trong nhat cua khung nay khong phai o tim, ma la NUT TAO MOI
   mang san cai ten vua go sang man tao. Anh Viet 21/08/2026: chi Dung go
   "BHXH CO SO TAN DINH" roi "bao hiem xa hoi", ca hai lan deu khong ra gi,
   man hinh bao "Chua chon ben nhan tien" va het duong. Bat nguoi ta go lai
   lan thu ba cai ten vua go hai lan khong ra la cach nhanh nhat de ho bo
   cuoc va di nhan tin hoi. */
function hsKhungTimNcc(idO, soThay, moTaTao) {
  return '<div style="margin-top:9px;padding-top:9px;border-top:1px dashed #e5e7eb">' +
    '<button class="btn gh" id="hsTaoNccMoi" style="margin:0">➕ Không thấy tên? Tạo nhà cung cấp mới</button>' +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:6px;line-height:1.5">' +
    h(moTaTao || '') + (moTaTao ? ' ' : '') +
    'Máy điền sẵn cái tên đang gõ trong ô tìm sang màn tạo.</div></div>';
}

function hsNoiNutTaoNcc(tuKhoa, chon) {
  var n = document.getElementById('hsTaoNccMoi');
  if (!n) return;
  n.onclick = function () { nccTaoNhanh(tuKhoa, chon); };
}

/* ---------- Lap ho so moi: HOI THEO NHIP thay cho nam nut ----------

   Anh Viet mo issue #196: *"Chi Dung va anh deu cam thay 5 nut cua cho tao
   APP la qua roi. Anh muon lam gon lai"*.

   Nam nut cu bat nguoi ta doc nam doan van roi tu doi chieu nhieu tieu chi
   mot luc. Nay hoi theo nhip, moi nhip mot tieu chi, va KHONG bo luong nao,
   khong doi ma luong nao.

     Cau 1 - khoan chi nay di theo DUONG nao:
       tra nha cung cap qua cong no  -> hoi tiep: ncc | tt
       chi thang tu mot TK cong ty   -> tkct, vao thang, khong hoi them
       hoan lai cho nguoi da ung ra  -> hoi tiep: hu_hd | hu_khd

     Cau 2 - hoa don mua DA NAM TRONG HE chua. Hoi Y HET NHAU o ca hai
     nhanh con lai, nen khai chung mot cho de khong bao gio lech loi.

   VI SAO tkct DUNG O CAU 1 CHU KHONG PHAI CAU 2. Ban dau phien nay xep tkct
   thanh mot the trong cau 2 voi nhan "khong co hoa don mua nao". Codex bat
   duoc tren PR #203 va bat DUNG: `scrChiCongTyTao` co HAI che do theo o
   "Loai chi phi thue" - chi phi hop le thi no goi `hoa_don_cho_tra` roi cho
   TICK hoa don dang no, khong hoa don thi go tay. Nghia la tkct xu ly duoc
   ca to da nam trong he. Dan nhan "khong co hoa don mua nao" cho no la cat
   mat mot nua duong: ai co hoa don trong he ma phai chi tu tai khoan khac
   MB, tra loi that thi bi day sang `ncc` (MB), muon toi dung cho thi phai
   tra loi doi. Bat nguoi ta noi doi voi may de di dung duong la hong nang
   hon cai roi ma minh dinh chua.

   Chuyen that: cai tach `ncc` voi `tkct` KHONG phai la hoa don da vao he
   hay chua, ma la TIEN DI DUONG NAO. `ncc` la dot tra cong no, tien ra tu
   MB (xem ho_so_tt.py dong 62). `tkct` la chi thang tu mot tai khoan cong
   ty tu chon, khong qua cong no Purchasing. Nen no thuoc ve cau 1.

   CAU 2 LA CHO PHAI VIET CAN THAN NHAT. Loi hieu nham da ghi lai tu truoc:
   "co hoa don" o day nghia la hoa don DA NAM TRONG HE ERPNext thanh mot hoa
   don mua con no, chu khong phai la co to hoa don giay trong tay. Uyen cam
   to hoa don VAT that nhung ke toan chua nhap vao he thi van phai di duong
   "chua vao he", vi chinh duong do moi sinh hoa don mua ra. Cau hoi va mo ta
   ben duoi phai noi thang dieu do, dung de nguoi ta suy ra.

   Thoi o cau 2 thi QUAY VE cau 1 chu khong van ra ngoai. Bat nguoi ta bam
   dau cong lai tu dau chi vi lo chon nham nhanh la buoc lui vo ly. */

var HS_LUONG_CONG_NO = [
  { k: 'ncc', icon: '🧾', nhan: 'Đã có, đang nợ trên sổ',
    mo_ta: 'Kế toán đã nhập hoá đơn vào hệ, hàng đã nhập kho, hoá đơn đang nằm ở công nợ nhà cung cấp. Tick các tờ còn nợ rồi chuyển tiền từ tài khoản MB.' },
  /* Luong thu nam, anh Viet giao 21/08/2026. Dat ngay duoi Cong no NCC vi
     hai cai cung la tra tien cho nha cung cap, khac o cho da co hoa don
     hay chua. Than luong nam trong 30-tra-truoc.js. */
  { k: 'tt', icon: '⏩', nhan: 'Chưa có, đây là khoản trả trước',
    mo_ta: 'Trả trước khi chưa có hoá đơn: đơn in ấn, đơn đặt sản xuất có điều khoản cọc. Neo vào đơn mua hàng, hoá đơn về thì tự cấn trừ.' }
];

/* Hai the nay hay bi chon nham, va ten cua chung la nguyen nhan. Tu 04/09/2026
   CA HAI duong deu noi duoc phieu thanh toan noi bo (o duong hoan ung CO hoa
   don thi phieu chi dong vai chung tu, khong dung toi so tien - xem chu thich
   o `hsODongPhieu`). Nen bo hai cau cu "KHONG noi duoc phieu thanh toan noi
   bo o duong nay" va "day la duong DUY NHAT noi duoc phieu thanh toan noi bo
   cua quan ly": ca hai deu da sai su that, ma sai theo huong day nguoi ta
   sang nham duong. */
var HS_LUONG_HOAN_UNG = [
  { k: 'hu_hd', icon: '🧾', nhan: 'Đã có, đang nợ trên sổ',
    mo_ta: 'Kế toán đã nhập hoá đơn vào hệ, hàng đã nhập kho, hoá đơn đang nằm ở công nợ nhà cung cấp. Tick các hoá đơn còn nợ để hoàn lại tiền cho người ứng. Gom được nhiều nhà cung cấp trong một hồ sơ.' },
  { k: 'hu_khd', icon: '🧮', nhan: 'Chưa có',
    mo_ta: 'Gõ tay từng khoản rồi máy tự sinh hoá đơn mua khi giám đốc duyệt. Dùng cho khoản lẻ không hoá đơn, VÀ cho khoản có tờ hoá đơn thật mà kế toán chưa nhập vào hệ.' }
];

/* Cau hoi thu hai hoi y het nhau o ca hai nhanh, nen dung chung mot cho de
   khong bao gio lech loi. `hoiChon` chen `moTa` vao thang HTML (khong qua
   `h()`) nen the <b> o day chay duoc; ba chuoi nay deu la chu cua minh,
   khong phai chu nguoi dung go vao. */
var HS_CAU_HOA_DON = 'Hoá đơn mua đã nằm trong hệ chưa?';
var HS_MO_TA_HOA_DON = 'Hỏi về tờ hoá đơn ĐÃ ĐƯỢC KẾ TOÁN NHẬP VÀO HỆ thành một hoá đơn mua còn nợ. ' +
  'Cầm tờ hoá đơn giấy trong tay mà kế toán chưa nhập thì vẫn chọn "chưa có".';
var HS_CAU_DUONG_TIEN = 'Khoản chi này đi theo đường nào?';

function hsHoiHoaDon(dsMuc) {
  return hoiChon('Lập hồ sơ thanh toán · bước 2',
    '<b>' + HS_CAU_HOA_DON + '</b><br>' + HS_MO_TA_HOA_DON, dsMuc);
}

async function hsChonLoaiMoi() {
  for (;;) {
    var duong = await hoiChon('Lập hồ sơ thanh toán',
      '<b>' + HS_CAU_DUONG_TIEN + '</b><br>Chọn đúng đường thì các bước sau tự bày ra cho hợp.', [
      /* Ma cua cau 1 co y dat khac han nam ma luong (`ncc`, `tt`, `hu_hd`,
         `hu_khd`, `tkct`), tru `tkct` la vao thang nen dung chinh ma luong.
         Dung trung chu `ncc` cho ca nhanh lan luong thi doc code khong biet
         dang noi toi cai nao. */
      { k: 'cong_no', icon: '🏭', nhan: 'Trả cho nhà cung cấp qua công nợ',
        mo_ta: 'Tiền đi từ tài khoản MB tới thẳng bên bán, theo đợt trả công nợ.' },
      { k: 'tkct', icon: '🏦', nhan: 'Chi thẳng từ một tài khoản công ty',
        mo_ta: 'Không qua công nợ Purchasing. Chọn tài khoản chi, rồi tuỳ loại chi phí thuế mà tick hoá đơn đang nợ hoặc gõ tay từng khoản.' },
      { k: 'nguoi_ung', icon: '🙋', nhan: 'Hoàn lại cho người đã ứng tiền ra',
        mo_ta: 'Người trong tiệm đã bỏ tiền túi hoặc tiền tạm ứng mua hộ, giờ công ty trả lại cho họ.' }
    ]);
    if (!duong) return;

    /* Chi tu TK cong ty vao thang, khong hoi cau 2: man cua no da hoi bang
       o "Loai chi phi thue", va chinh o do moi la thu quyet dinh bay bang
       tick hoa don hay bang go tay. Hoi truoc mot lan nua la hoi hai lan
       cung mot chuyen roi con mau thuan duoc voi nhau. */
    if (duong === 'tkct') {
      huDong = []; huGhiChu = ''; huTkChi = ''; huCpThue = ''; huChonHd = {}; huSuaO = -1;
      return go(scrChiCongTyTao);
    }

    var c = await hsHoiHoaDon(
      duong === 'nguoi_ung' ? HS_LUONG_HOAN_UNG : HS_LUONG_CONG_NO);
    /* Thoi o cau 2 la quay lai cau 1, khong van ra ngoai. */
    if (!c) continue;

    if (c === 'tt') { ttReset(); return go(scrTraTruocTao); }
    if (c === 'hu_khd') { huDong = []; huGhiChu = ''; huTamUng = 0; huSuaO = -1; return go(scrHoanUngTao); }
    hsHdTu = '';
    /* `hsPhieuCua` phai xoa cung luc voi `hsTaoChon`, y het ba cho kia trong
       tep nay. Truoc v433 chi cho nay quen xoa: lap ho so hoan ung, noi phieu
       vao mot hoa don, bo giua chung khong luu, lap lai roi tick trung dung
       hoa don do thi phieu cu lang le dinh lai vao. */
    if (c === 'hu_hd') { hsTaoNcc = ''; hsTaoChon = {}; hsPhieuCua = {}; hsTaoNguoiUng = ''; hsTaoDsUng = null; hsTkHoan = ''; hsTkDs = null; hsTkCua = ''; hsTaoLoai = 'Hoan ung HD'; return go(scrHoSoTTTao); }
    hsTaoNcc = ''; hsTaoChon = {}; hsPhieuCua = {}; hsTaoLoai = 'NCC';
    return go(scrHoSoTTTao);
  }
}

function huTong() { return huDong.reduce(function (a, x) { return a + Number(x.so_tien || 0); }, 0); }

async function scrHoanUngTao() {
  hsoBuoc = 0;
  huMode = 'hu';
  frame('Lập hồ sơ hoàn ứng', '<div class="emp"><div class="e1">⏳</div><div>Đang tải danh sách...</div></div>');
  var dstk;
  try { dstk = await api('vagabond.ho_so_tt.ds_tk_hoan_ung', {}); }
  catch (e) { frame('Lập hồ sơ hoàn ứng', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var tkHu = (dstk && dstk.tk) || [];
  /* Chi tu chon khi CHI CO MOT tai khoan. Truoc 28/08/2026 dong nay lay
     `tkHu[0]` tuc la cai dau bang chu cai, ma ACB dung truoc OCB - nghia la
     ho so nao nguoi lap khong de y la mac dinh chay vao ACB. Co hai tai
     khoan tro len thi de trong va bat chon tay. */
  if (!huTkHoan && tkHu.length === 1) huTkHoan = tkHu[0].ma;

  var html = '<div class="card" style="padding:12px 14px;font-size:13px;line-height:1.6;color:#374151">' +
    'Gõ từng khoản đã chi hộ bằng tiền tạm ứng: hàng test không nhập kho, hàng phát sinh, chi phí bảo trì... ' +
    'Nhiều nhà cung cấp nhỏ lẻ gộp chung một hồ sơ được, vì tiền là hoàn lại cho <b>một</b> người.<br>' +
    'Máy chỉ giữ những gì mình gõ. Đến bước <b>giám đốc duyệt</b> mới sinh hoá đơn mua thật, nên hồ sơ bị từ chối giữa chừng không để lại rác trên sổ.</div>';

  /* Anh Viet 22/08/2026: bo han danh sach nha cung cap o day. Khoan hoan
     ung khong hoa don khong thuoc ve nha cung cap nao ca - do la tien nguoi
     ung da bo ra ho o hang chuc cho, gio tra lai vao dung MOT trong hai tai
     khoan ung. Bat chon nha cung cap trong danh sach vai tram dong vua vo
     nghia vua la cho de chon nham nhat man hinh.
     So tai khoan hien ngay canh ten vi hai tai khoan de lan khi chi nhin
     ten ngan hang. */
  html += hsoKhoi('Hoàn ứng về tài khoản nào') + '<div class="card" style="padding:10px 12px">' +
    (tkHu.length
      ? kmHangChip(tkHu.map(function (x) {
          return posChipNut('data-hutk="' + h(x.ma) + '"', h(x.nhan), huTkHoan === x.ma);
        }).join('')) +
        '<div style="font-size:11.5px;color:' + (huTkHoan ? '#98a2b3' : '#b3261e') + ';margin-top:8px;line-height:1.6">' +
        (!huTkHoan
          ? 'Chưa chọn tài khoản nhận tiền. Có nhiều hơn một tài khoản nên máy không tự chọn thay, phải bấm đúng cái cần chuyển.'
          : dstk.doan
          ? '⚠️ Chưa có tài khoản nào gắn vào quỹ tạm ứng ' + '1411' + ', nên hệ thống bày tạm mọi tài khoản công ty. ' +
            'Nhờ chị Dung gắn đúng tài khoản ứng vào 1411 thì danh sách này gọn lại còn đúng tài khoản đang dùng.'
          : 'Tiền hoàn ứng luôn trả về tài khoản đã ứng ra. Chọn đúng tài khoản thì số dư quỹ tạm ứng mới khớp.') +
        '</div>'
      : '<div style="font-size:13px;color:#b45309;line-height:1.6">Chưa khai tài khoản ngân hàng nào. ' +
        'Nhờ chị Dung tạo Bank Account cho quỹ tạm ứng bên Next trước đã.</div>') +
    '</div>';

  html += '<div class="card" style="padding:12px 14px;background:#fffbeb;border:1.5px solid #fde68a">' +
    '<div style="font-size:11.5px;color:#92400e;font-weight:800">ĐANG LẬP</div>' +
    '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:5px">' +
    '<span id="huSoKhoan" style="font-size:13.5px;color:#374151">' + huDong.length + ' khoản</span>' +
    '<b id="huTongTien" style="font-size:20px;color:#92400e">' + money(huTong()) + ' đ</b></div>' +
    (Number(huTamUng) > 0
      ? '<div style="display:flex;justify-content:space-between;font-size:12.5px;color:#6b7280;margin-top:3px"><span>Trừ đã tạm ứng</span><b>' + money(huTamUng) + ' đ</b></div>' +
        '<div style="display:flex;justify-content:space-between;font-size:13px;color:#92400e;margin-top:2px"><span><b>Còn lại phải chuyển</b></span><b id="huConLai">' + money(huTong() - Number(huTamUng)) + ' đ</b></div>'
      : '') +
    '</div>';

  html += huVeBang();

  /* Mot nut cho moi tai khoan that su co giao dich chi ra. Anh Viet
     22/08/2026 bao thieu cua ACB - truoc day ma nguon chi biet moi OCB. */
  var nutSk = tkHu.map(function (x) {
    return '<button class="btn gh" data-husk="' + h(x.ma) + '" style="flex:2;margin:0">🏦 Lấy từ sao kê ' +
      h(x.ngan_hang || x.ten) + '</button>';
  }).join('');
  html += '<div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap">' +
    (nutSk || '<button class="btn gh" id="huSepay" style="flex:2;margin:0">🏦 Lấy từ sao kê</button>') +
    '<button class="btn gh" id="huThem" style="flex:1;margin:0">➕ Gõ tay</button>' +
    '<button class="btn gh" id="huUng" style="flex:1;margin:0">➖ Trừ ứng</button></div>';

  html += '<div class="card" style="padding:12px 14px"><input class="tin" id="huGc" placeholder="Ghi chú cho hồ sơ (không bắt buộc)" value="' + h(huGhiChu) + '"></div>';

  var foot = '<div style="display:flex;gap:8px">' +
    '<button class="btn" id="huLuu" style="flex:2">📤 Lập và gửi kế toán</button>' +
    '<button class="btn gh" id="huNhap" style="flex:1">💾 Lưu nháp</button></div>';
  var b = frame('Lập hồ sơ hoàn ứng', html, { footer: foot });

  Array.prototype.forEach.call(document.querySelectorAll('[data-hutk]'), function (el) {
    el.onclick = function () { huTkHoan = el.getAttribute('data-hutk'); go(scrHoanUngTao, true); };
  });
  huNoiBang(b);
  document.getElementById('huThem').onclick = function () { huThemDongTrong(); };
  var sk0 = document.getElementById('huSepay');
  if (sk0) sk0.onclick = function () { huLaySepay(); };
  Array.prototype.forEach.call(document.querySelectorAll('[data-husk]'), function (el) {
    el.onclick = function () { huLaySepay(el.getAttribute('data-husk')); };
  });
  document.getElementById('huUng').onclick = async function () {
    var v = await hoiNhap('Đã tạm ứng trước bao nhiêu đồng? (gõ 0 nếu không có)', String(huTamUng || 0));
    if (v === null) return;
    huTamUng = Math.max(0, Number(String(v).replace(/[^0-9]/g, '')) || 0);
    go(scrHoanUngTao, true);
  };

  var luu = async function (guiLuon) {
    var gc = document.getElementById('huGc');
    huGhiChu = gc ? gc.value : '';
    if (!huTkHoan) return baoTin('Chưa chọn tài khoản nhận tiền hoàn ứng.');
    if (!huDong.length) return baoTin('Chưa nhập khoản chi nào.');
    if (Number(huTamUng) > huTong()) return baoTin('Số đã tạm ứng lớn hơn tổng hồ sơ, vui lòng xem lại.');
    busy(true);
    try {
      var kq = await api('vagabond.ho_so_tt.tao_hoan_ung', {
        tk_hoan: huTkHoan, dong: JSON.stringify(huDongGuiDi()), ghi_chu: huGhiChu,
        da_tam_ung: huTamUng || 0, gui_luon: guiLuon ? 1 : 0
      });
      busy(false);
      huDong = []; huGhiChu = ''; huTamUng = 0; huSuaO = -1;
      toast('Đã lập hồ sơ ' + kq.ma + ' · ' + money(kq.tong_tien) + ' đ', 3500);
      go(function () { scrHoSoTTView(kq.ma); }, true);
    } catch (e) { busy(false); baoTin((e && e.message) || 'Lập hồ sơ lỗi'); }
  };
  document.getElementById('huLuu').onclick = function () { luu(true); };
  document.getElementById('huNhap').onclick = function () { luu(false); };
}

/* ---------- Lay khoan chi tu sao ke OCB ----------
   Anh Viet 13/08/2026 hoi: "co cach nao goi y nhung hoa don hay NCC can
   hoan ung - co doi chieu voi giao dich SePay cua nguon tien di tu ngan
   hang OCB duoc khong? Boi vi thuc ra tat ca cac loai hoan ung thi deu la
   tra lai tien da ung cho tai khoan OCB cua Uyen?"

   Dung vay, nen nguon dang tin nhat khong phai tri nho ma la sao ke: moi
   khoan da chi deu co mot giao dich mang san ngay, so tien va noi dung.
   Tick tu day thi so tien va ngay khong the go sai, va moi khoan gan dung
   mot giao dich nen so du quy 1411 tu khop. */
var huGdChon = {};

async function huLaySepay(taiKhoan) {
  busy(true);
  var kq;
  var g = { so_ngay: 60 };
  if (taiKhoan) g.tai_khoan = taiKhoan;
  try { kq = await api('vagabond.ho_so_tt.sepay_ocb', g); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Không đọc được sao kê', 'Sao kê ngân hàng'); }
  busy(false);
  var tenNh = (kq && kq.ngan_hang) ? ('Sao kê ' + kq.ngan_hang) : 'Sao kê ngân hàng';
  if (kq.loi) return baoTin(kq.loi, tenNh);
  if (!(kq.rows || []).length) {
    return baoTin('Không còn giao dịch chi nào từ tài khoản này trong 60 ngày mà chưa nằm trong hồ sơ nào.', tenNh);
  }
  huGdChon = {};
  go(function () { scrHuSepay(kq); });
}

async function scrHuSepay(kq) {
  var rows = kq.rows || [];
  var chon = rows.filter(function (r) { return huGdChon[r.ma_giao_dich]; });
  var tong = chon.reduce(function (a, r) { return a + Number(r.so_tien || 0); }, 0);

  var html = '<div class="card" style="padding:12px 14px;font-size:13px;line-height:1.6;color:#374151">'
    + 'Đây là các khoản <b>đã chi ra</b> từ tài khoản ' + h((kq.ngan_hang || 'tạm ứng') + (kq.so_tk ? ' · ' + kq.so_tk : '')) + ' mà chưa nằm trong hồ sơ nào. '
    + 'Tick khoản nào thì máy lấy sẵn ngày, số tiền và mã giao dịch, mình chỉ cần bổ sung nội dung và số hoá đơn nếu có.</div>';

  html += '<div class="card" style="padding:12px 14px;background:#fffbeb;border:1.5px solid #fde68a">'
    + '<div style="font-size:11.5px;color:#92400e;font-weight:800">ĐANG CHỌN</div>'
    + '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:5px">'
    + '<span style="font-size:13.5px;color:#374151">' + chon.length + ' / ' + rows.length + ' giao dịch</span>'
    + '<b style="font-size:20px;color:#92400e">' + money(tong) + ' đ</b></div></div>';

  html += '<div class="sec">Giao dịch chi ra từ quỹ tạm ứng · bấm để chọn</div><div class="card">';
  rows.forEach(function (r) {
    var da = !!huGdChon[r.ma_giao_dich];
    html += '<div class="hub" data-hugd="' + h(r.ma_giao_dich) + '"' + (da ? ' style="background:#dbeafe"' : '') + '>'
      + '<div class="hub-i">' + (da ? '☑️' : '⬜') + '</div>'
      + '<div class="hub-t"><div class="t1">' + h(r.noi_dung || '(không có nội dung)') + '</div>'
      + '<div class="t2">' + hsNgayVn(r.ngay) + ' · ' + h(r.ma_giao_dich) + '</div></div>'
      + '<b style="white-space:nowrap">' + money(r.so_tien) + ' đ</b></div>';
  });
  html += '</div>';

  var foot = '<div style="display:flex;gap:8px">'
    + '<button class="btn" id="huGdXong" style="flex:2">➕ Đưa ' + chon.length + ' khoản vào hồ sơ</button>'
    + '<button class="btn gh" id="huGdVe" style="flex:1">← Quay lại</button></div>';
  var b = frame('Sao kê quỹ tạm ứng', html, { footer: foot });

  b.addEventListener('click', function (e) {
    var r = e.target.closest('[data-hugd]'); if (!r) return;
    var ma = r.getAttribute('data-hugd');
    if (huGdChon[ma]) delete huGdChon[ma]; else huGdChon[ma] = 1;
    go(function () { scrHuSepay(kq); }, true);
  });
  document.getElementById('huGdVe').onclick = function () { go(scrHoanUngTao); };
  document.getElementById('huGdXong').onclick = function () {
    var them = rows.filter(function (r) { return huGdChon[r.ma_giao_dich]; });
    if (!them.length) return baoTin('Chưa tick giao dịch nào.', 'Sao kê quỹ tạm ứng');
    them.forEach(function (r) {
      // Da co khoan nao mang dung ma giao dich nay thi khong them lan hai.
      if (huDong.some(function (x) { return x.ma_giao_dich === r.ma_giao_dich; })) return;
      huDong.push({
        ngay_hd: r.ngay, so_hd_ncc: '', noi_dung: r.noi_dung || '',
        ben_ban: '', loai_chi: '', co_vat: 0,
        so_tien: r.so_tien, ma_giao_dich: r.ma_giao_dich, ghi_chu: ''
      });
    });
    toast('Đã thêm ' + them.length + ' khoản, bấm từng dòng để bổ sung nội dung', 4000);
    go(scrHoanUngTao);
  };
}

/* Sua mot khoan chi. Dung prompt noi tiep nhau chu khong dung bieu mau:
   tren dien thoai ban phim tu bat len tung o mot, go nhanh hon la cuon
   qua lai giua sau o input. i = -1 nghia la them moi. */
/* huSuaDong (chuoi bay tam hop thoai noi duoi nhau) da bo ngay 24/08/2026.

   Thay bang sua thang tren dong - xem huODong va huNoiBang. Ly do anh Viet
   dua ra: *"Cach nhap lieu bang form roi ben duoi dang lam Ke toan mat thoi
   gian"*. Con mot ly do nua thay tu ban cu: bam Huy o hop thoai thu bay la
   mat sach sau buoc truoc do, khong luu lai duoc gi. */


/* ---------- Luong 4: chi thang tu tai khoan cong ty ----------
   Anh Viet 17/08/2026: "thieu luong chi tien truc tiep tu tai khoan cong ty
   cho cac chi phi khong qua bo phan Mua hang. User dang phai dung tam luong
   Hoan ung khong hoa don de ghi nhan" - sai ban chat dong tien.

   Khac ba luong kia o ba cho: tien di tu tai khoan ngan hang cua CONG TY chu
   khong phai quy tam ung; khong sinh hoa don mua nao ca ma ghi thang Journal
   Entry theo dinh khoan ke toan tu chon; va bat buoc phan loai chi phi thue
   ngay luc lap de cuoi nam loc ra khoan khong duoc tru khi quyet toan TNDN. */

async function huChonTaiKhoan(tieu_de, dang_chon) {
  var tu = await hoiNhap(tieu_de + '\n\nGõ số hiệu hoặc tên tài khoản để tìm (ví dụ 6277, chi phi dich vu):', huTkTim || '');
  if (tu === null) return null;
  huTkTim = String(tu || '').trim();
  var kq;
  try { kq = await api('vagabond.ho_so_tt.ds_tai_khoan', { tu_khoa: huTkTim }); }
  catch (e) { baoTin((e && e.message) || 'Không tra được hệ thống tài khoản'); return null; }
  var ds = (kq && kq.tk) || [];
  if (!ds.length) { baoTin('Không thấy tài khoản nào khớp "' + huTkTim + '".'); return null; }
  var c = await hoiChon('Chọn tài khoản', ds.length + ' tài khoản khớp', ds.slice(0, 40).map(function (a) {
    return { k: a.ma, icon: '🔢', nhan: a.ma, mo_ta: a.ten + (a.loai ? ' · ' + a.loai : '') };
  }), dang_chon || '');
  if (c === null) return null;
  return c || '';
}

async function huChonTep() {
  return new Promise(function (res) {
    var inp = document.createElement('input');
    inp.type = 'file';
    inp.accept = 'image/*,application/pdf';
    inp.onchange = function () { res(inp.files && inp.files[0] ? inp.files[0] : null); };
    inp.click();
  });
}

async function huUpTep(f) {
  /* Rieng tep chung tu thi de PRIVATE: ho so thanh toan la giay to tien bac,
     khong de link ai co cung mo duoc nhu anh mon. Gan vao ho so xong thi ai
     doc duoc ho so moi xem duoc tep. */
  function ban() {
    var fd = new FormData();
    fd.append('file', f, f.name);
    fd.append('is_private', '1');
    fd.append('folder', 'Home');
    return fetch('/api/method/upload_file', {
      method: 'POST', credentials: 'same-origin', cache: 'no-store',
      headers: { 'X-Frappe-CSRF-Token': csrfTok() }, body: fd
    });
  }
  var r = await ban();
  if (r.status === 400 || r.status === 403) { if (await refreshCsrf()) r = await ban(); }
  var j = {};
  try { j = await r.json(); } catch (e) { }
  if (!r.ok || !j.message || !j.message.file_url) throw new Error('máy chủ không nhận tệp (mã ' + r.status + ')');
  return { ma: j.message.name, ten: j.message.file_name || f.name, url: j.message.file_url };
}

async function scrChiCongTyTao() {
  hsoBuoc = 0;
  huMode = 'tkct';
  frame('Chi từ TK công ty', '<div class="emp"><div class="e1">⏳</div><div>Đang tải danh sách...</div></div>');
  var hopLe = huCpThue === 'Chi phi hop le';
  var dsn, dstk, hd = { rows: [], tong: 0 };
  try {
    dsn = await api(hopLe ? 'vagabond.ho_so_tt.ds_ncc_con_no' : 'vagabond.ho_so_tt.ds_nguoi_ung', (!hopLe && huTim) ? { tu_khoa: huTim } : {});
    dstk = await api('vagabond.ho_so_tt.ds_tk_cong_ty', {});
    if (hopLe && huNguoi) {
      try { hd = await api('vagabond.ho_so_tt.hoa_don_cho_tra', { ncc: huNguoi, so_ngay: 365 }); } catch (e2) { }
    }
  } catch (e) {
    frame('Chi từ TK công ty', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>');
    return;
  }
  var ncc = dsn.ncc || [];
  var tk = (dstk && dstk.tk) || [];
  if (!huTkChi && tk.length) huTkChi = tk[0].ma;
  var rows = hd.rows || [];
  var tongChon = rows.reduce(function (a, r) { return a + (huChonHd[r.hoa_don] ? Number(r.con_no || 0) : 0); }, 0);

  var html = '<div class="card" style="padding:12px 14px;font-size:13px;line-height:1.6;color:#374151">' +
    'Chi trả trực tiếp từ tài khoản công ty cho chi phí phát sinh, <b>không qua Purchasing</b>.<br>' +
    'Chọn <b>Loại chi phí thuế</b> trước, màn hình bên dưới tự đổi theo: có hoá đơn GTGT thì tick hoá đơn đang nợ, không hoá đơn thì gõ tay và đính kèm chứng từ.</div>';

  if (!tk.length) {
    html += '<div class="card" style="padding:12px 14px;background:#fef2f2;border:1.5px solid #fecaca;font-size:13px;color:#991b1b">' +
      '⚠️ Chưa có tài khoản ngân hàng nào của công ty gắn tài khoản sổ cái. Vui lòng mở Bank Account bên Next điền ô Account.</div>';
  }

  html += hsoKhoi('Tiền đi ra từ tài khoản nào') + '<div class="card" style="padding:10px 12px">' +
    kmHangChip(tk.map(function (x) {
      return posChipNut('data-hutk="' + h(x.ma) + '"', h(x.ten) + (x.so_tk ? ' · ' + h(x.so_tk) : ''), huTkChi === x.ma);
    }).join('')) + '</div>';

  html += hsoKhoi('Loại chi phí thuế · bắt buộc') + '<div class="card" style="padding:10px 12px">' +
    kmHangChip(
      posChipNut('data-hucp="Chi phi hop le"', '✅ Hợp lệ (có hoá đơn GTGT tên Vagabond)', huCpThue === 'Chi phi hop le') +
      posChipNut('data-hucp="Chi phi khong hop le"', '🚫 Không hợp lệ tính thuế', huCpThue === 'Chi phi khong hop le')
    ) +
    '<div style="font-size:12px;color:#6b7280;margin-top:7px;line-height:1.5">Chọn sai chỗ này thì cuối năm quyết toán thuế TNDN phải mở lại từng chứng từ.</div>' +
    '</div>';

  if (!huCpThue) {
    html += '<div class="emp" style="padding:26px 14px"><div class="e1">👆</div><div>Chọn loại chi phí thuế để hệ thống bày tiếp phần nhập liệu.</div></div>';
    var b0 = frame('Chi từ TK công ty', html);
    Array.prototype.forEach.call(document.querySelectorAll('[data-hutk]'), function (el) {
      el.onclick = function () { huTkChi = el.getAttribute('data-hutk'); go(scrChiCongTyTao, true); };
    });
    Array.prototype.forEach.call(document.querySelectorAll('[data-hucp]'), function (el) {
      el.onclick = function () { huCpThue = el.getAttribute('data-hucp'); go(scrChiCongTyTao, true); };
    });
    return;
  }

  var nhanNguoi = hopLe ? 'Trả cho nhà cung cấp nào' : 'Trả cho ai';
  html += hsoKhoi(nhanNguoi) + '<div class="card" style="padding:10px 12px">' +
    (hopLe ? '' : hsOTimNcc('huTim', ncc.length)) +
    kmHangChip(ncc.slice(0, 40).map(function (x) {
      var ten = x.ten || x.ncc;
      return posChipNut('data-hun="' + h(x.ncc) + '"', (x.hay_dung ? '⭐ ' : '') + h(ten) + (hopLe && x.con_no ? ' · ' + money(x.con_no) : ''), huNguoi === x.ncc);
    }).join('')) +
    (hopLe ? '' : hsKhungTimNcc('huTim', ncc.length,
      'Bảo hiểm xã hội, điện, nước, bên cho thuê nhà đều phải có hồ sơ nhà cung cấp mới lập được phiếu chi.')) +
    '</div>';

  html += '<div class="card" style="padding:12px 14px;background:#f0fdfa;border:1.5px solid #99f6e4">' +
    '<div style="font-size:11.5px;color:#0f766e;font-weight:800">ĐANG LẬP</div>' +
    '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:5px">' +
    '<span style="font-size:13.5px;color:#374151">' + (hopLe ? (Object.keys(huChonHd).length + ' hoá đơn') : (huDong.length + ' khoản')) + '</span>' +
    '<b style="font-size:20px;color:#0f766e">' + money(hopLe ? tongChon : huTong()) + ' đ</b></div></div>';

  if (hopLe) {
    /* Tick hoa don GTGT dang no - dung API va cach bay giong het luong cong
       no NCC, ke toan khong phai hoc lai man moi. Khong can dinh kem file vi
       chung tu goc da nam san trong he thong theo hoa don. */
    html += hsoKhoi('Chứng từ tham chiếu · hoá đơn đang nợ') + '<div class="card" style="padding:0;overflow-x:auto">'
      + '<table style="width:100%;border-collapse:collapse;font-size:12.5px;min-width:520px">'
      + '<tr style="background:#f8fafc;color:#6b7280;font-size:11.5px;text-align:left">'
      + '<th style="padding:8px 10px;font-weight:700"></th>'
      + '<th style="padding:8px 10px;font-weight:700">Hoá đơn</th>'
      + '<th style="padding:8px 10px;font-weight:700">Hạn trả</th>'
      + '<th style="padding:8px 10px;font-weight:700;text-align:right">Còn nợ</th></tr>';
    if (!rows.length) {
      html += '<tr><td colspan="4" style="padding:24px;text-align:center;color:#6b7280">'
        + (huNguoi ? 'Nhà cung cấp này không còn hoá đơn nào đang nợ.' : 'Chọn nhà cung cấp ở trên.') + '</td></tr>';
    }
    rows.forEach(function (r) {
      var on = !!huChonHd[r.hoa_don];
      html += '<tr data-huhd="' + h(r.hoa_don) + '" style="border-top:1px solid #eef2f5;cursor:pointer;background:' + (on ? '#ecfeff' : '#fff') + '">'
        + '<td style="padding:9px 10px">' + (on ? '☑️' : '⬜') + '</td>'
        + '<td style="padding:9px 10px">' + h(r.so_hd_ncc || r.hoa_don)
        + '<br><span style="color:#6b7280;font-size:11.5px">' + h(r.hoa_don) + '</span></td>'
        + '<td style="padding:9px 10px;white-space:nowrap;color:' + (r.tre_ngay > 0 ? '#b91c1c' : '#6b7280') + '">'
        + (hsNgayVn(r.han_tra) || '-') + (r.tre_ngay > 0 ? '<br>trễ ' + r.tre_ngay + ' ngày' : '') + '</td>'
        + '<td style="padding:9px 10px;text-align:right;white-space:nowrap;font-weight:700">' + money(r.con_no) + '</td></tr>';
    });
    html += '</table></div>';
  } else {
    html += huVeBang();
    html += '<div style="display:flex;gap:8px;margin-bottom:10px">' +
      '<button class="btn gh" id="huThem" style="flex:1;margin:0">➕ Gõ tay khoản chi</button></div>';
    /* Anh Viet 24/08/2026: *"Khong dung mot o dinh kem tong o cuoi phieu
       nua. Di chuyen chuc nang dinh kem vao TUNG DONG HANG (tung khoan
       chi)."* O tong cu nam o day: mot ho so ba khoan dien nuoc bao tri
       chi khai duoc mot loai chung tu, ba tep nam chung mot ro khong biet
       to nao cua khoan nao. Nay moi dong tu mang loai chung tu va tep cua
       no, hien bang hinh thu nho ngay tren dong nhu man Hoan ung. */
    html += '<div class="card" style="padding:11px 13px;background:#f0fdfa;border:1.5px solid #99f6e4;' +
      'font-size:12.5px;color:#0f766e;line-height:1.6">Chi không hoá đơn thì <b>mỗi khoản phải tự mang chứng từ của nó</b>. ' +
      'Bấm ô <b>Loại chứng từ</b> rồi ô <b>Chứng từ</b> ngay trên dòng để đính kèm.</div>';
  }

  html += '<div class="card" style="padding:12px 14px"><input class="tin" id="huGc" placeholder="Ghi chú cho hồ sơ (không bắt buộc)" value="' + h(huGhiChu) + '"></div>';

  var foot = '<div style="display:flex;gap:8px">' +
    '<button class="btn" id="huLuu" style="flex:2">📤 Lập và gửi kế toán</button>' +
    '<button class="btn gh" id="huNhap" style="flex:1">💾 Lưu nháp</button></div>';
  var b = frame('Chi từ TK công ty', html, { footer: foot });

  Array.prototype.forEach.call(document.querySelectorAll('[data-hun]'), function (el) {
    el.onclick = function () { huNguoi = el.getAttribute('data-hun'); huChonHd = {}; go(scrChiCongTyTao, true); };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-hutk]'), function (el) {
    el.onclick = function () { huTkChi = el.getAttribute('data-hutk'); go(scrChiCongTyTao, true); };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-hucp]'), function (el) {
    el.onclick = function () { huCpThue = el.getAttribute('data-hucp'); go(scrChiCongTyTao, true); };
  });
  /* Hai tang tim tren cung mot o. Go den dau loc ngay 40 chip dang bay ra,
     khong ve lai man nen ban phim khong tut. Bam Enter hoac roi o thi moi
     hoi may chu, vi danh sach nguoi nhan tien dai hon 40 va phan con lai
     nam ben may chu chu khong co san o day. */
  vgbNoiOTim(b, 'huTim', '[data-hun]');
  var ot = document.getElementById('huTim');
  if (ot) ot.onchange = function () { huTim = ot.value.trim(); go(scrChiCongTyTao, true); };
  /* Lay cai DANG go trong o chu khong lay bien da luu: nguoi ta go xong roi
     bam thang nut Tao moi, chua he roi o nen bien van con rong. */
  hsNoiNutTaoNcc(ot ? ot.value.trim() : huTim, function (ma) {
    if (ma) { huNguoi = ma; huTim = ''; }
    go(scrChiCongTyTao, true);
  });
  huNoiBang(b);
  b.addEventListener('click', function (e) {
    var r2 = e.target.closest('[data-huhd]');
    if (r2) {
      var ma = r2.getAttribute('data-huhd');
      if (huChonHd[ma]) delete huChonHd[ma]; else huChonHd[ma] = 1;
      return go(scrChiCongTyTao, true);
    }
  });
  var nt = document.getElementById('huThem');
  if (nt) nt.onclick = function () { huThemDongTrong(); };

  var luu = async function (guiLuon) {
    var gc = document.getElementById('huGc');
    huGhiChu = gc ? gc.value : '';
    if (!huTkChi) return baoTin('Chưa chọn tài khoản ngân hàng của công ty để chi.');
    if (!huCpThue) return baoTin('Chưa chọn loại chi phí thuế.');
    if (!huNguoi) return baoTin('Chưa chọn bên nhận tiền.');
    busy(true);
    try {
      var kq;
      if (hopLe) {
        var ds = Object.keys(huChonHd);
        if (!ds.length) { busy(false); return baoTin('Chưa tick hoá đơn nào.'); }
        kq = await api('vagabond.ho_so_tt.tao', {
          ncc: huNguoi, hoa_don: JSON.stringify(ds), ghi_chu: huGhiChu,
          gui_luon: guiLuon ? 1 : 0, loai: 'TK cong ty',
          tk_chi: huTkChi, loai_cp_thue: huCpThue
        });
      } else {
        if (!huDong.length) { busy(false); return baoTin('Chưa nhập khoản chi nào.'); }
        var thieu = huDong.filter(function (x) { return !x.tk_no; });
        if (thieu.length) { busy(false); return baoTin('Còn ' + thieu.length + ' khoản chưa chọn tài khoản Nợ.'); }
        /* Chung tu nam o TUNG DONG tu 24/08/2026, khong con o tong nua.
           Chan ngay tren man cho no noi ro khoan nao thieu, thay vi de may
           chu tra ve mot cuc loi sau khi da bam Luu. */
        var chuaCt = huDong.filter(function (x) { return !(x.tep || []).length || !(x.loai_chung_tu || '').trim(); });
        if (chuaCt.length) {
          busy(false);
          return baoTin('Còn ' + chuaCt.length + ' khoản chưa đủ chứng từ:\n\n' +
            chuaCt.map(function (x) {
              return '· ' + (x.noi_dung || 'chưa đặt tên') + ': ' +
                (!(x.loai_chung_tu || '').trim() ? 'chưa chọn loại chứng từ' : 'chưa đính kèm tệp');
            }).join('\n') +
            '\n\nBấm vào ô Loại chứng từ rồi ô Chứng từ ngay trên dòng đó.');
        }
        kq = await api('vagabond.ho_so_tt.tao_chi_cong_ty', {
          ncc: huNguoi, tk_chi: huTkChi, loai_cp_thue: huCpThue,
          dong: JSON.stringify(huDongGuiDi()), ghi_chu: huGhiChu, gui_luon: guiLuon ? 1 : 0
        });
      }
      busy(false);
      huDong = []; huGhiChu = ''; huChonHd = {}; huSuaO = -1;
      toast('Đã lập hồ sơ ' + kq.ma, 3500);
      go(function () { scrHoSoTTView(kq.ma); }, true);
    } catch (e) { busy(false); baoTin((e && e.message) || 'Lập hồ sơ lỗi'); }
  };
  document.getElementById('huLuu').onclick = function () { luu(true); };
  document.getElementById('huNhap').onclick = function () { luu(false); };
}


/* ---------- Chi tiet ho so: chuoi duyet, chung tu, SePay, thu bao NCC ---------- */
var hsMoDong = {};

async function hsCopy(chu, nhan) {
  var xong = function () { toast('Đã copy ' + (nhan || '')); };
  /* Trinh duyet chan clipboard (thuong gap khi mo qua khung nhung hay khi
     trang chua duoc bam vao) thi bay chuoi ra cho nguoi copy tay. Khong
     await o day: ham nay khong async va cung khong can doi ket qua. */
  var chepTay = function () { hoiChu('Vui lòng copy tay', 'Chạm giữ rồi chọn Copy:', chu, { nhieu_dong: true }); };
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) return navigator.clipboard.writeText(chu).then(xong, chepTay);
  } catch (e) { }
  chepTay();
}

async function scrHoSoTTView(name) {
  frame('Hồ sơ ' + name, '<div class="emp"><div class="e1">⏳</div><div>Đang mở hồ sơ...</div></div>');
  var d;
  try { d = await api('vagabond.ho_so_tt.chi_tiet', { name: name }); }
  catch (e) { frame('Hồ sơ ' + name, '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>'); return; }
  var hs = d.ho_so, Q = d.quyen || {}, m = hsMau[hs.trang_thai] || ['#f3f4f6', '#e5e7eb', '#374151', '•'];
  var laHU = hs.loai === 'Hoan ung' || hs.loai === 'Hoan ung HD';
  var laTKCT = hs.loai === 'TK cong ty';
  /* Con go duoc giay to ra hay khong. Ho so da thanh toan thi bo ho so la
     giai trinh cua mot lan chuyen tien that, go mot to ra la lam thung bo
     do; may chu chan lan nua chu khong tin mot minh man hinh. */
  var goDuocTep = ['Nhap', 'Tu choi', 'Cho ke toan', 'Cho giam doc'].indexOf(hs.trang_thai) >= 0;
  var nhanLoai = hs.loai === 'Hoan ung' ? '🧮 Hoàn ứng không hoá đơn · '
    : (hs.loai === 'Hoan ung HD' ? '🧾 Hoàn ứng có hoá đơn · '
      : (laTKCT ? '🏦 Chi từ TK công ty · ' : '🏭 '));

  var html = '<div class="card" style="padding:14px;background:' + m[0] + ';border:1.5px solid ' + m[1] + '">' +
    '<div style="font-size:22px">' + m[3] + '</div>' +
    '<div style="font-size:17px;font-weight:800;color:' + m[2] + ';margin-top:4px">' + h(hs.nhan) + '</div>' +
    '<div style="font-size:13.5px;color:#374151;margin-top:6px">' +
    nhanLoai + h(hs.ten_ncc || hs.ncc) +
    /* Ho so hoan ung gom nhieu nha cung cap thi dau ho so mang ten NGUOI
       DUOC HOAN UNG. Phai noi ro so nha ngay day, khong thi doc dau ho so
       lai tuong ca xap hoa don la cua mot minh nguoi do. */
    (hs.loai === 'Hoan ung HD' && Number(hs.so_ncc) > 1
      ? '<div style="font-size:12.5px;color:#0f766e;margin-top:3px">Hoàn lại cho người ứng · gom <b>' +
        Number(hs.so_ncc) + ' nhà cung cấp</b></div>' : '') + '</div>' +
    '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:8px">' +
    '<span style="font-size:12.5px;color:#6b7280">' + h(hs.ma) + ' · lập ' + hsNgayVn(hs.ngay) + '</span>' +
    '<b style="font-size:22px;color:' + m[2] + '">' + money(hs.tong_tien) + ' đ</b></div>' +
    (Number(hs.da_tam_ung) > 0
      ? '<div style="display:flex;justify-content:space-between;font-size:12.5px;color:#6b7280;margin-top:4px"><span>Trừ đã tạm ứng</span><b>' + money(hs.da_tam_ung) + ' đ</b></div>' +
        '<div style="display:flex;justify-content:space-between;font-size:14px;color:' + m[2] + ';margin-top:2px"><span><b>Còn lại phải chuyển</b></span><b>' + money(hs.con_lai) + ' đ</b></div>'
      : '') +
    (laTKCT ? '<div style="margin-top:8px;font-size:12.5px;color:#0f766e">' +
      (hs.tk_chi ? 'Chi từ ' + h(hs.tk_chi) + ' · ' : '') +
      (hs.loai_cp_thue === 'Chi phi hop le' ? '✅ ' : '🚫 ') + h(hs.nhan_cp_thue || 'chưa phân loại chi phí thuế') +
      (hs.loai_chung_tu ? '<br>📎 ' + h(hs.loai_chung_tu) +
        ((hs.tep_dinh_kem || []).length ? ' · ' + hs.tep_dinh_kem.length + ' tệp' : ' · <b style="color:#b91c1c">chưa có tệp</b>') : '') +
      '</div>' : '') +
    (hs.ly_do_tu_choi ? '<div style="margin-top:8px;font-size:13px;color:#991b1b">Lý do: ' + h(hs.ly_do_tu_choi) + '</div>' : '') +
    (hs.ghi_chu ? '<div style="margin-top:6px;font-size:12.5px;color:#4b5563">Ghi chú: ' + h(hs.ghi_chu) + '</div>' : '') +
    '</div>';

  /* Chuoi duyet: hien TEN THAT chu khong hien email (anh Viet 13/08/2026). */
  var buoc = [
    ['Lập hồ sơ', hs.nguoi_tao_ten || hs.nguoi_tao, hs.ngay, 1],
    ['Kế toán duyệt (FIN)', hs.fin_ten || hs.fin_boi, hs.fin_luc, hs.fin_boi ? 1 : 0],
    ['Giám đốc duyệt', hs.gd_ten || hs.gd_boi, hs.gd_luc, hs.gd_boi ? 1 : 0],
    ['Chuyển tiền', hs.ma_giao_dich || (hs.trang_thai === 'Da thanh toan' ? 'đã chuyển' : ''), hs.ngay_thanh_toan, hs.trang_thai === 'Da thanh toan' ? 1 : 0]
  ];
  html += '<div class="sec">Chuỗi duyệt</div><div class="card">';
  buoc.forEach(function (x) {
    html += '<div class="hub" style="cursor:default">' +
      '<div class="hub-i" style="background:' + (x[3] ? '#f0fdf4' : '#f8fafc') + '">' + (x[3] ? '✅' : '⬜') + '</div>' +
      '<div class="hub-t"><div class="t1">' + x[0] + '</div>' +
      '<div class="t2">' + (x[3] ? (h(String(x[1] || '-')) + (x[2] ? ' · ' + hsNgayVn(String(x[2]).split(' ')[0]) : '')) : 'chưa') + '</div></div></div>';
  });
  html += '</div>';

  /* Tai khoan nhan tien va noi dung chuyen khoan cho file lo cua MB. */
  html += '<div class="sec">Chuyển tiền tới</div><div class="card" style="padding:12px 14px;font-size:13px;line-height:1.75;color:#374151">' +
    '<div>Người thụ hưởng: <b>' + h(hs.ten_nhan || hs.ten_ncc || hs.ncc) + '</b></div>' +
    '<div>Số tài khoản: <b>' + h(hs.stk_nhan || '(chưa khai)') + '</b></div>' +
    '<div>Ngân hàng: <b>' + h(hs.ngan_hang_nhan || '(chưa khai)') + '</b></div>' +
    (hs.noi_dung_ck ? '<div style="margin-top:4px">Nội dung: <b>' + h(hs.noi_dung_ck) + '</b></div>' : '') +
    '<div style="display:flex;gap:8px;margin-top:10px">' +
    '<button class="btn gh" data-hsv="noidungck" style="flex:2;margin:0">🏦 Tạo nội dung chuyển khoản</button>' +
    ((Q.lap || Q.fin) && hs.trang_thai !== 'Da thanh toan' ? '<button class="btn gh" data-hsv="chontk" style="flex:1;margin:0">🏦 Chọn TK nhận</button>' : '') +
    ((Q.lap || Q.fin) && hs.trang_thai !== 'Da thanh toan' ? '<button class="btn gh" data-hsv="suatk" style="flex:1;margin:0">✏️ Gõ tay</button>' : '') +
    '</div></div>';

  html += '<div class="sec">' + d.dong.length + (laHU ? ' khoản chi' : ' hoá đơn') + ' trong hồ sơ · bấm để xem chứng từ</div><div class="card">';
  d.dong.forEach(function (x, i) {
    var xong = x.hoa_don && Number(x.con_no_hien_tai || 0) <= 0;
    var mo = !!hsMoDong[i];
    var soCT = (x.po.length + x.pnk.length + x.scan.length);
    html += '<div class="hub" data-hsd="' + i + '"><div class="hub-i">' + (xong ? '✅' : (x.hoa_don ? '🧾' : '📄')) + '</div>' +
      '<div class="hub-t"><div class="t1">' + h(x.noi_dung || x.so_hd_ncc || x.hoa_don || '(chưa đặt tên)') + '</div>' +
      /* Ten nha cung cap cua RIENG dong nay, tren mot hang rieng khi ho so
         gom nhieu nha. Nhet chung vao hang so hoa don thi ke toan phai doc
         het ca hang moi biet dong nay cua ai. */
      (Number(hs.so_ncc) > 1
        ? '<div class="t2" style="color:#0f766e;font-weight:700">' + h(x.ben_ban || x.ncc_hd || '') + '</div>' : '') +
      '<div class="t2">' +
      (x.so_hd_ncc ? 'HĐ số <b>' + h(x.so_hd_ncc) + '</b>' : 'chưa có số hoá đơn') +
      (x.ngay_hd ? ' · ' + hsNgayVn(x.ngay_hd) : '') +
      (Number(hs.so_ncc) > 1 ? '' : ((x.ben_ban || x.ncc_hd) ? ' · ' + h(x.ben_ban || x.ncc_hd) : '')) + '</div>' +
      (x.hoa_don
        ? '<div class="t2">' + h(x.hoa_don) + (x.trang_thai_hd ? ' · ' + h(x.trang_thai_hd) : '') +
          ' · còn nợ ' + money(x.con_no_hien_tai) + ' đ</div>'
        : '<div class="t2" style="color:#92400e">Chưa sinh hoá đơn mua · máy lập khi giám đốc duyệt</div>') +
      (soCT ? '<div class="t2" style="color:#0e7490">' + (mo ? '▾' : '▸') + ' ' + soCT + ' chứng từ kèm theo</div>' : '') +
      '</div><b style="white-space:nowrap">' + money(x.so_tien) + ' đ</b></div>';

    if (mo) {
      var ct = '';
      if (x.hddt.length) ct += '<div style="margin-bottom:6px"><b>Hoá đơn điện tử</b><br>' +
        x.hddt.map(function (t) { return h(t.nhan) + ': <b>' + h(t.gia_tri) + '</b>'; }).join('<br>') + '</div>';
      if (x.so_hd_ncc || x.ngay_hd) ct += '<div style="margin-bottom:6px"><b>Hoá đơn nhà cung cấp</b><br>Số ' +
        h(x.so_hd_ncc || '-') + ' · ngày ' + (hsNgayVn(x.ngay_hd) || '-') +
        (x.tong_hd ? ' · tổng ' + money(x.tong_hd) + ' đ' : '') + '</div>';
      if (x.po.length) ct += '<div style="margin-bottom:6px"><b>Đơn mua hàng</b><br>' + x.po.map(h).join('<br>') + '</div>';
      if (x.pnk.length) ct += '<div style="margin-bottom:6px"><b>Phiếu nhập kho</b><br>' + x.pnk.map(h).join('<br>') + '</div>';
      if (x.scan.length) {
        /* Anh chup chung tu thi bay anh nho ra luon, bam vao mo to. Doc mot
           danh sach ten tep kieu "dia giay1676af.jpg" thi khong ai biet to
           nao vao to nao (anh Viet 13/08/2026). */
        /* Nut X o goc tung o (anh Viet 24/08/2026). Chi bay ra voi to dinh
           THANG vao to hoa don nay va khi ho so con sua duoc: to dinh vao
           don mua hay phieu nhap thi go tu day la go trong tay nguoi khac,
           con ho so da thanh toan thi bo giay to la giai trinh cua mot lan
           chuyen tien that. */
        ct += '<div><b>Bản scan · ' + x.scan.length + ' tệp</b>'
          + '<div style="display:flex;flex-wrap:wrap;gap:13px 10px;margin-top:9px">'
          + x.scan.map(function (f) {
            var laAnh = /\.(jpe?g|png|gif|bmp|webp)$/i.test(f.ten || '');
            var cuaHd = x.hoa_don && f.tu === 'Purchase Invoice ' + x.hoa_don;
            return oTep({
              url: f.url, ten: f.ten, anh: laAnh ? 1 : 0, co: 66,
              mo: laAnh ? 'data-scan="' + h(f.url) + '"' : 'data-motep="' + h(f.url) + '"',
              go: (goDuocTep && cuaHd && f.file)
                ? 'data-hsgohd="' + h(x.hoa_don) + '|' + h(f.file) + '" data-ten="' + h(f.ten || '') + '"'
                : ''
            });
          }).join('')
          + '</div></div>';
      }
      if (!ct) ct = '<span style="color:#6b7280">Chưa có chứng từ nào đính kèm hoá đơn này.</span>';
      html += '<div style="padding:10px 14px 12px 56px;font-size:12.5px;line-height:1.7;color:#374151;background:#f8fafc;border-top:1px solid #eef2f5">' + ct + '</div>';
    }
  });
  html += '</div>';

  /* Khối "Tệp đính kèm thẳng vào hồ sơ" ĐÃ BỎ ô tải lên (anh Việt 23/08/2026:
     *"do đã có nút đính kèm Bản thể hiện hoá đơn ở từng hoá đơn rồi nên bỏ ô
     này đi"*). Mỗi dòng hoá đơn đã có nút đính kèm riêng, mà đính theo dòng
     thì tệp bám đúng khoản chi và bản in ghi được nhãn "Khoản 3"; đính chung
     cả hồ sơ thì không ai biết tờ đó của khoản nào.

     Nhưng KHÔNG xoá hẳn khối: hồ sơ cũ đã đính tệp theo đường này thì tệp đó
     vẫn phải nhìn thấy và gỡ được, không thì nó nằm trong bộ hồ sơ xuất ra mà
     trên màn hình không còn dấu vết nào. Hết tệp thì khối tự biến mất. */
  /* UY NHIEM CHI
     ------------------------------------------------------------------
     Anh Viet chot 28/08/2026: dinh UNC len ho so ROI moi ghi nhan thanh
     toan duoc, ap cho MOI loai ho so. May chu chan that, khoi nay chi la
     cho de bam va de nhin.

     Vi sao tach thanh khoi rieng chu khong tron vao "Tep dinh kem": UNC la
     to giay quyet dinh duoc bam nut hay khong, tron vao mot dong tep chung
     thi khong ai thay no thieu. */
  var uncDs = d.unc || [];
  var uncGo = Number(d.unc_go_duoc || 0) && (Q.fin || Q.gd);
  if (Q.fin || Q.gd || uncDs.length) {
    html += '<div class="sec">Uỷ nhiệm chi</div><div class="card" style="padding:12px 14px">';
    if (uncDs.length) {
      html += '<div style="display:flex;flex-wrap:wrap;gap:14px 11px;padding:2px 0 4px">' +
        uncDs.map(function (f) {
          var laAnh = /\.(jpe?g|png|gif|bmp|webp)$/i.test(f.ten || '');
          return oTep({
            url: f.url, ten: f.ten, anh: laAnh ? 1 : 0, co: 72, nhan: 1,
            mo: laAnh ? 'data-scan="' + h(f.url) + '"' : 'data-motep="' + h(f.url) + '"',
            go: uncGo ? 'data-hsgounc="' + h(f.file) + '"' : ''
          });
        }).join('') + '</div>';
    } else {
      html += '<div style="font-size:13px;line-height:1.6;color:#92400e;background:#fffbeb;' +
        'border:1px solid #fde68a;border-radius:9px;padding:10px 12px">' +
        'Chưa có uỷ nhiệm chi. Tải UNC từ e-banking về máy rồi bấm nút dưới đây. ' +
        'Chưa có tờ này thì máy chưa cho ghi nhận thanh toán.</div>';
    }
    if (Q.fin || Q.gd) {
      html += '<button class="btn gh" data-hsv="dinhunc" style="width:100%;margin:10px 0 0">' +
        '📎 Đính kèm uỷ nhiệm chi</button>';
    }
    html += '<div style="font-size:11.5px;color:#98a2b3;margin-top:8px;line-height:1.5">' +
      'Tờ này đi theo bút toán chi và đính vào thư báo gửi nhà cung cấp.</div></div>';
  }

  /* Tep dinh kem chung cua ho so. Loc bo cac to UNC da bay o khoi tren,
     khong thi mot to hien hai lan. */
  var uncMa = {};
  uncDs.forEach(function (f) { uncMa[f.file] = 1; });
  var tepChung = (d.ho_so_dinh_kem || []).filter(function (f) { return !uncMa[f.file]; });
  if (tepChung.length) {
    html += '<div class="sec">Tệp đính kèm thẳng vào hồ sơ</div><div class="card" style="padding:12px 14px">';
    html += '<div style="display:flex;flex-wrap:wrap;gap:14px 11px;padding-top:4px">' +
      tepChung.map(function (f) {
        var laAnh = /\.(jpe?g|png|gif|bmp|webp)$/i.test(f.ten || '');
        return oTep({
          url: f.url, ten: f.ten, anh: laAnh ? 1 : 0, co: 72, nhan: 1,
          mo: laAnh ? 'data-scan="' + h(f.url) + '"' : 'data-motep="' + h(f.url) + '"',
          go: f.file ? 'data-hsgotep="' + h(f.file) + '"' : ''
        });
      }).join('') + '</div>';
    html += '<div style="font-size:11.5px;color:#98a2b3;margin-top:8px;line-height:1.5">' +
      'Tệp cũ đính chung cả hồ sơ. Từ nay đính bản thể hiện vào <b>từng dòng hoá đơn</b> ở trên.</div></div>';
  }

  html += '<div style="display:flex;gap:8px;margin-bottom:10px">' +
    '<button class="btn gh" data-hsv="xuatbo" style="flex:1;margin:0">📦 Xuất bộ hồ sơ</button>' +
    '<button class="btn gh" data-hsv="xemto" style="flex:1;margin:0">👁 Xem tờ đề nghị</button></div>';

  /* Thu bao chi danh cho ho so cong no nha cung cap. Ho so hoan ung thi
     nha cung cap da duoc tra tien tu luc mua, gui thu "chung toi da thanh
     toan" cho ho la bao mot viec khong xay ra. May chu cung chan. */
  /* Khoi thu bao hien o MOI trang thai cua ho so nha cung cap, khong chi
     khi da tra. Ly do: nut Gui thu de xem mat la thu phai dung duoc TRUOC
     khi tra tien, khong thi khong ai kiem lai duoc noi dung truoc luc no
     den tay nha cung cap. Rieng nut gui that thi van doi da thanh toan. */
  if (!laHU) {
    var daTra = hs.trang_thai === 'Da thanh toan';
    html += '<div class="sec">Thư báo nhà cung cấp</div><div class="card" style="padding:12px 14px;font-size:13px;line-height:1.6;color:#374151">' +
      (hs.email_da_gui
        ? '✉️ Đã gửi tới <b>' + h(hs.email_gui_toi) + '</b>' + (hs.email_gui_luc ? ' lúc ' + h(hs.email_gui_luc) : '') + '.<br>Gửi lại được nếu nhà cung cấp báo chưa nhận.'
        : (daTra ? 'Chưa gửi thư báo. ' : 'Thư tự gửi ngay khi ghi nhận thanh toán. ') +
          'Email đang lưu trên hồ sơ nhà cung cấp: <b>' + h(hs.email_ncc || '(chưa có)') + '</b>') +
      '<div style="display:flex;gap:8px;margin-top:10px">' +
      '<button class="btn gh" data-hsv="xemthu" style="flex:1;margin:0">👁 Xem trước</button>' +
      '<button class="btn gh" data-hsv="guithuthu" style="flex:1;margin:0">🧪 Gửi thử</button>' +
      (daTra ? '<button class="btn" data-hsv="guithu" style="flex:1;margin:0">✉️ ' + (hs.email_da_gui ? 'Gửi lại' : 'Gửi thư báo') + '</button>' : '') +
      '</div>' +
      '<div style="font-size:11.5px;color:#98a2b3;margin-top:8px;line-height:1.5">' +
      'Gửi thử đi đúng một địa chỉ anh chị gõ vào, tiêu đề có chữ GỬI THỬ, không gửi bản sao cho ai.</div></div>';
  }

  var nut = [];
  if (Q.lap && (hs.trang_thai === 'Nhap' || hs.trang_thai === 'Tu choi')) nut.push('<button class="btn" data-hsv="gui_fin" style="flex:2">📤 Gửi kế toán duyệt</button>');
  if (Q.fin && hs.trang_thai === 'Cho ke toan') nut.push('<button class="btn" data-hsv="fin" style="flex:2">✅ Kế toán duyệt</button>');
  if (Q.gd && hs.trang_thai === 'Cho giam doc') nut.push('<button class="btn" data-hsv="gd" style="flex:2">👔 Giám đốc duyệt</button>');
  if (Q.fin && hs.trang_thai === 'Da duyet') {
    nut.push('<button class="btn gh" data-hsv="sepay" style="flex:1">🏦 Dò SePay</button>');
    nut.push('<button class="btn" data-hsv="datra" style="flex:2">💸 Ghi nhận đã thanh toán</button>');
  }
  if (Q.fin && hs.trang_thai === 'Da thanh toan' && !hs.ma_giao_dich) nut.push('<button class="btn gh" data-hsv="khoptay" style="flex:2">🔎 Khớp tay giao dịch</button>');
  if ((Q.fin || Q.gd) && ['Cho ke toan', 'Cho giam doc', 'Da duyet'].indexOf(hs.trang_thai) >= 0) nut.push('<button class="btn gh" data-hsv="tu_choi" style="flex:1">⛔ Từ chối</button>');
  if (Q.lap && ['Nhap', 'Tu choi'].indexOf(hs.trang_thai) >= 0) nut.push('<button class="btn gh" data-hsv="huy" style="flex:1">🗑 Huỷ</button>');
  var foot = nut.length ? '<div style="display:flex;gap:8px">' + nut.join('') + '</div>' : '';

  var b = frame('Hồ sơ ' + hs.ma, html, foot ? { footer: foot } : {});
  b.addEventListener('click', function (e) {
    var el = e.target.closest('[data-hsv]');
    if (el) return hsHanh(el.getAttribute('data-hsv'), hs);
    if (e.target.closest('a')) return;
    var sc = e.target.closest('[data-scan]');
    if (sc) return rndXemAnh(sc.getAttribute('data-scan'));
    var mt = e.target.closest('[data-motep]');
    if (mt) { window.open(mt.getAttribute('data-motep'), '_blank'); return; }
    var gh = e.target.closest('[data-hsgohd]');
    if (gh) {
      e.stopPropagation();
      var pp = gh.getAttribute('data-hsgohd').split('|');
      return hsGoBanTheHien(hs, pp[0], pp[1], gh.getAttribute('data-ten'));
    }
    var r = e.target.closest('[data-hsd]');
    if (r) {
      var i = r.getAttribute('data-hsd');
      if (hsMoDong[i]) delete hsMoDong[i]; else hsMoDong[i] = 1;
      go(function () { scrHoSoTTView(hs.ma); }, true);
    }
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-hsv]'), function (el) {
    el.onclick = function (ev) { ev.stopPropagation(); hsHanh(el.getAttribute('data-hsv'), hs); };
  });

  Array.prototype.forEach.call(document.querySelectorAll('[data-hsgounc]'), function (el) {
    el.onclick = async function (ev) {
      ev.stopPropagation();
      var ma = el.getAttribute('data-hsgounc');
      if (!ma) return;
      if (!await hoiCo('Gỡ uỷ nhiệm chi',
        'Tệp không bị xoá, chỉ thôi không nằm trên hồ sơ này nữa. Hồ sơ đã thanh toán thì không gỡ được.',
        'Gỡ')) return;
      busy(true);
      try { await api('vagabond.tra_tien_app.go_unc', { name: hs.ma, tep: ma }); busy(false); toast('Đã gỡ uỷ nhiệm chi'); }
      catch (e) { busy(false); return baoTin(errMsg(e) || 'Không gỡ được'); }
      go(function () { scrHoSoTTView(hs.ma); }, true);
    };
  });

  Array.prototype.forEach.call(document.querySelectorAll('[data-hsgotep]'), function (el) {
    el.onclick = async function (ev) {
      ev.stopPropagation();
      var ma = el.getAttribute('data-hsgotep');
      if (!ma) return toast('Tệp này không gỡ được từ app, nhờ chị Dung gỡ trên Desk giúp.', 5000);
      if (!await hoiCo('Gỡ tệp khỏi hồ sơ', 'Tệp không bị xoá, chỉ thôi không nằm trên hồ sơ này nữa.', 'Gỡ')) return;
      busy(true);
      try { await api('vagabond.ho_so_tt.go_tep', { name: hs.ma, tep: ma }); }
      catch (e2) { busy(false); return toast((e2 && e2.message) || 'Không gỡ được tệp', 6000); }
      busy(false);
      toast('Đã gỡ tệp khỏi hồ sơ.', 3500);
      go(function () { scrHoSoTTView(hs.ma); }, true);
    };
  });
}

/* Go mot ban the hien dinh nham khoi to hoa don. Hoi lai truoc khi go: to
   nay se di theo ca bo ho so PDF gui di duyet chi tien. */
async function hsGoBanTheHien(hs, hoaDon, tep, ten) {
  if (!tep) return toast('Tệp này không gỡ được từ app, nhờ chị Dung gỡ trên Desk giúp.', 5000);
  if (!await hoiCo('Gỡ bản thể hiện',
    'Gỡ "' + (ten || tep) + '" khỏi hoá đơn ' + hoaDon + '?\n\n' +
    'Tệp vẫn còn trên máy chủ, chỉ thôi không nằm trên hoá đơn này nữa.', 'Gỡ')) return;
  busy(true);
  try { await api('vagabond.ho_so_tt.go_tep_hoa_don', { name: hs.ma, hoa_don: hoaDon, tep: tep }); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Không gỡ được tệp'); }
  busy(false);
  toast('Đã gỡ ' + (ten || tep), 3000);
  go(function () { scrHoSoTTView(hs.ma); }, true);
}

/* Tai ban the hien hoa don len ho so.

   Duong nay thay cho viec keo PDF tu API M-Invoice: da do ba bien the ten
   tep ngay 20-21/08/2026, ca ba deu tra 400, ma tai lieu API cong khai cua
   ho khong noi dinh dang dung. Nguoi lap ho so mo M-Invoice bam tai ve roi
   dinh len day - mot thao tac chac chan, hon la mot nhip tu dong khong bao
   gio chay. */
async function hsHanh(k, hs) {
  if (k === 'khoptay') return go(function () { scrTimGiaoDich(hs.ma, hs.tong_tien); });
  if (k === 'noidungck') {
    busy(true);
    var ck;
    try { ck = await api('vagabond.ho_so_tt.noi_dung_chuyen_khoan', { name: hs.ma }); }
    catch (e) { busy(false); return baoTin((e && e.message) || 'Không dựng được nội dung'); }
    busy(false);
    return go(function () { scrNoiDungCK(hs, ck); });
  }
  /* CHON TAI KHOAN TREN HO SO DA LAP
     ------------------------------------------------------------------
     QT-31: o ngan hang phai la o CHON. Duong go tay ba o van con o duoi,
     nhung chi dung khi that su chua co Bank Account nao - go tay sai mot
     chu trong ten ngan hang la uy nhiem chi bi tra ve. */
  if (k === 'chontk') {
    busy(true);
    var dtk;
    try { dtk = await api('vagabond.ho_so_tt.ds_tk_hoan_ung', { nguoi: hs.nguoi_ung || hs.nha_cung_cap || '' }); }
    catch (e) { busy(false); return baoTin((e && e.message) || 'Không tải được danh sách tài khoản'); }
    busy(false);
    var ds = (dtk && dtk.tk) || [];
    if (!ds.length) return baoTin('Chưa khai tài khoản ngân hàng nào cho người này. Nhờ chị Dung tạo Bank Account bên Next, hoặc dùng nút Gõ tay.');
    var c = await hoiChon('Hoàn ứng vào tài khoản nào', 'Chọn tài khoản thì tên, số tài khoản và ngân hàng lấy nguyên từ hồ sơ ngân hàng, không lệch một chữ.',
      ds.map(function (x) { return { k: x.ma, icon: '🏦', nhan: x.nhan, mo_ta: x.ten || '' }; }));
    if (!c) return;
    busy(true);
    try { await api('vagabond.ho_so_tt.doi_tk_nhan', { name: hs.ma, tk_hoan: c }); busy(false); toast('Đã chọn tài khoản nhận'); }
    catch (e) { busy(false); return baoTin((e && e.message) || 'Lưu lỗi'); }
    return go(function () { scrHoSoTTView(hs.ma); }, true);
  }
  if (k === 'suatk') {
    var t1 = await hoiNhap('Tên người thụ hưởng (đúng như trên tài khoản ngân hàng):', hs.ten_nhan || hs.ten_ncc || '');
    if (t1 === null) return;
    var t2 = await hoiNhap('Số tài khoản:', hs.stk_nhan || '');
    if (t2 === null) return;
    var t3 = await hoiNhap('Ngân hàng (viết tắt cũng được, ví dụ ACB, MB, VCB):', hs.ngan_hang_nhan || '');
    if (t3 === null) return;
    busy(true);
    try { await api('vagabond.ho_so_tt.sua_tk_nhan', { name: hs.ma, ten_nhan: t1, stk_nhan: t2, ngan_hang_nhan: t3 }); busy(false); toast('Đã lưu tài khoản nhận'); }
    catch (e) { busy(false); return baoTin((e && e.message) || 'Lưu lỗi'); }
    return go(function () { scrHoSoTTView(hs.ma); }, true);
  }
  if (k === 'xuatbo') {
    busy(true);
    var bo;
    try { bo = await api('vagabond.ho_so_tt.xuat_ho_so', { name: hs.ma }); }
    catch (e) { busy(false); return baoTin((e && e.message) || 'Xuất bộ hồ sơ lỗi'); }
    busy(false);
    bcTaiVe(bo.ten_file, bo.b64, 'application/pdf');
    return baoTin('Đã tải ' + bo.ten_file + '\n\nMột tệp PDF khổ A4 dọc gồm ' + bo.so_tep + ' phần, trang cuối là mục lục.' +
      ((bo.hong || []).length ? '\n\n⚠️ Còn ' + bo.hong.length + ' tệp chưa gộp được, xem trang mục lục:\n' + bo.hong.slice(0, 8).join('\n') : ''),
      'Xuất bộ hồ sơ');
  }
  if (k === 'xemto') {
    busy(true);
    var t0;
    try { t0 = await api('vagabond.ho_so_tt.xem_to_app', { name: hs.ma }); }
    catch (e) { busy(false); return baoTin((e && e.message) || 'Không dựng được tờ'); }
    busy(false);
    var w0 = window.open('', '_blank');
    if (w0) { w0.document.write(t0.html); w0.document.close(); }
    else baoTin('Trình duyệt chặn cửa sổ mới. Vui lòng cho phép rồi bấm lại.');
    return;
  }
  if (k === 'sepay') {
    busy(true);
    var kq;
    try { kq = await api('vagabond.ho_so_tt.kiem_sepay', { name: hs.ma }); } catch (e) { busy(false); return baoTin((e && e.message) || 'Dò lỗi'); }
    busy(false);
    var x = (kq.rows || [])[0] || {};
    return baoTin('Ngân hàng đã chi ' + money(x.da_chi) + ' / ' + money(x.tong_tien) + ' đ' +
      (x.so_gd ? '\n' + x.so_gd + ' giao dịch' + (x.ma_gd ? ', mã ' + x.ma_gd : '') + (x.ngay ? ', ngày ' + hsNgayVn(x.ngay) : '') : '\nChưa thấy giao dịch nào mang mã ' + hs.ma) +
      (x.du ? '\n\n✅ Đã đủ tiền, bấm Ghi nhận đã thanh toán được rồi.' : '\n\n⏳ Chưa đủ. Khi chuyển khoản nhớ ghi mã ' + hs.ma + ' vào nội dung để máy tự khớp.'));
  }
  if (k === 'datra') {
    if (!await xacNhan('Ghi nhận đã thanh toán ' + money(hs.tong_tien) + ' đ cho ' + (hs.ten_ncc || hs.ncc) + '?\n\n' +
      'Máy sẽ sinh bút toán chi tiền và xoá công nợ trên các hoá đơn trong hồ sơ. Việc này không lui lại được.')) return;
    if (Number(hs.da_tam_ung) > 0 && !await xacNhan(
      'Hồ sơ này có trừ tạm ứng ' + money(hs.da_tam_ung) + ' đ.\n\n' +
      'Máy chỉ sinh bút toán chi ' + money(hs.tong_tien) + ' đ để xoá công nợ, KHÔNG tự bù trừ phần tạm ứng ' +
      '(máy không biết bút toán tạm ứng nào là của khoản này).\n\nChị Dung phải bù trừ tay phần đó bên Next. Tiếp tục?')) return;
    var mgd = await hoiNhap('Mã giao dịch ngân hàng (bỏ trống cũng được):', hs.ma_giao_dich || '') || '';
    busy(true);
    try {
      var kq2 = await api('vagabond.ho_so_tt.danh_dau_da_tra', { name: hs.ma, ma_giao_dich: mgd });
      busy(false);
      toast('Đã ghi nhận thanh toán' + (kq2.but_toan ? ' · bút toán ' + kq2.but_toan : ''), 4000);
      /* Thu bao di tu dong. Gui duoc thi bao mot dong, gui khong duoc thi
         noi ro vi sao de nguoi bam con gui tay, dung de im lang. */
      var th = kq2.thu || {};
      if (th.gui) toast('✉️ Đã gửi thư báo và uỷ nhiệm chi tới ' + th.toi, 5200);
      else if (th.vi_sao) baoTin(th.vi_sao, 'Chưa gửi được thư báo');
    } catch (e) { busy(false); return baoTin((e && e.message) || 'Ghi nhận lỗi'); }
    return go(function () { scrHoSoTTView(hs.ma); }, true);
  }
  if (k === 'dinhunc') {
    var fu = await huChonTep();
    if (!fu) return;
    if (fu.size > 12 * 1024 * 1024) {
      return baoTin('Tệp nặng quá 12 MB nên máy không nhận. Vui lòng xuất lại bản PDF nhỏ hơn.', 'Tệp quá nặng');
    }
    busy(true);
    var tu;
    try { tu = await huUpTep(fu); }
    catch (e) { busy(false); return baoTin('Không tải tệp lên được: ' + ((e && e.message) || '')); }
    try {
      await api('vagabond.tra_tien_app.dinh_unc', { name: hs.ma, tep: JSON.stringify([tu]) });
      busy(false);
      toast('Đã đính uỷ nhiệm chi vào hồ sơ ' + hs.ma, 3800);
    } catch (e2) {
      busy(false);
      return baoTin(errMsg(e2) || 'Không đính được uỷ nhiệm chi.', 'Chưa đính được');
    }
    return go(function () { scrHoSoTTView(hs.ma); }, true);
  }
  if (k === 'xemthu') {
    busy(true);
    var t;
    try { t = await api('vagabond.ho_so_tt.gui_email_ncc', { name: hs.ma, gui_that: 0 }); } catch (e) { busy(false); return baoTin((e && e.message) || 'Không dựng được thư'); }
    busy(false);
    var w = window.open('', '_blank');
    if (w) { w.document.write(t.html); w.document.close(); }
    else baoTin('Trình duyệt chặn cửa sổ mới. Vui lòng cho phép rồi bấm lại.');
    return;
  }
  if (k === 'guithuthu') {
    var toiThu = await hoiNhap('Gửi thử lá thư này tới email nào?', ((S && S.me && S.me.user) || ''));
    if (!toiThu) return;
    busy(true);
    try {
      await api('vagabond.ho_so_tt.gui_email_ncc', { name: hs.ma, email: toiThu, gui_that: 1, thu_nghiem: 1 });
      busy(false);
      toast('Đã gửi thử tới ' + toiThu + '. Thư có chữ GỬI THỬ ở tiêu đề.', 5200);
    } catch (e) { busy(false); return baoTin(errMsg(e) || 'Không gửi thử được'); }
    return;
  }
  if (k === 'guithu') {
    var toi = await hoiNhap('Gửi thư báo thanh toán tới email nào?', hs.email_ncc || '');
    if (!toi) return;
    busy(true);
    try { await api('vagabond.ho_so_tt.gui_email_ncc', { name: hs.ma, email: toi, gui_that: 1 }); busy(false); toast('Đã gửi thư tới ' + toi, 3500); }
    catch (e) { busy(false); return baoTin((e && e.message) || 'Gửi thư lỗi'); }
    return go(function () { scrHoSoTTView(hs.ma); }, true);
  }
  var ly = '';
  if (k === 'tu_choi') {
    ly = await hoiNhap('Từ chối vì sao? (bắt buộc, để người lập còn biết sửa gì)', '') || '';
    if (!ly.trim()) return;
  }
  if (k === 'huy' && !await xacNhan('Huỷ hồ sơ ' + hs.ma + '?')) return;
  if (k === 'gd' && !await xacNhan('Giám đốc duyệt chi ' + money(hs.tong_tien) + ' đ cho ' + (hs.ten_ncc || hs.ncc) + '?' +
    (hs.loai === 'Hoan ung' ? '\n\nDuyệt xong máy sẽ lập hoá đơn mua cho từng khoản trong hồ sơ. Đây là lúc số liệu vào sổ.' : ''))) return;
  busy(true);
  try { await api('vagabond.ho_so_tt.duyet', { name: hs.ma, buoc: k, ly_do: ly }); busy(false); toast('Đã cập nhật'); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Lỗi'); }
  hsMoDong = {};
  go(function () { scrHoSoTTView(hs.ma); }, true);
}

/* ---------- Noi dung chuyen khoan cho file lo cua MB ----------
   Anh Viet 13/08/2026: "generate ra stk, ten nguoi thu huong, noi dung
   chuyen khoan (kem ma) de chi Dung chi viec copy paste vao file chuyen
   khoan theo lo cua MB". Moi o mot nut copy rieng, cong mot nut copy ca
   dong da ngan cach bang Tab - dan thang vao Excel la moi cot mot o. */
async function scrNoiDungCK(hs, ck) {
  var o = function (nhan, gt, khoa) {
    return '<div style="padding:10px 0;border-bottom:1px solid #eef2f5">' +
      '<div style="font-size:11.5px;color:#6b7280;font-weight:700;letter-spacing:.3px">' + nhan + '</div>' +
      '<div style="display:flex;gap:8px;align-items:center;margin-top:3px">' +
      '<b style="flex:1 1 auto;min-width:0;font-size:14.5px;word-break:break-word;overflow-wrap:anywhere">' + h(gt || '(chưa có)') + '</b>' +
      (gt ? '<button class="btn gh" data-ckc="' + khoa + '" style="flex:0 0 auto;width:auto;margin:0;padding:5px 11px;font-size:12px;white-space:nowrap">📋</button>' : '') +
      '</div></div>';
  };
  var html = '<div class="card" style="padding:12px 14px;font-size:13px;line-height:1.6;color:#374151">' +
    'Copy từng ô, hoặc bấm <b>Copy cả dòng</b> rồi dán thẳng vào file chuyển khoản theo lô của MB.<br>' +
    'Nội dung có sẵn mã <b>' + h(hs.ma) + '</b>: chuyển xong máy dò SePay là tự khớp, khỏi đối chiếu tay.</div>';

  if ((ck.thieu || []).length) {
    html += '<div class="card" style="padding:12px 14px;background:#fef2f2;border:1.5px solid #fecaca;font-size:13px;color:#991b1b">' +
      '⚠️ Còn thiếu ' + ck.thieu.join(' và ') + '. Bấm <b>✏️ Sửa TK</b> ở màn hồ sơ để điền, hoặc khai vào Tài khoản ngân hàng của nhà cung cấp bên Next.</div>';
  }

  html += '<div class="card" style="padding:2px 14px 10px">' +
    o('SỐ TÀI KHOẢN', ck.stk, 'stk') +
    o('TÊN NGƯỜI THỤ HƯỞNG', ck.ten_nhan_ck, 'ten') +
    o('NGÂN HÀNG', ck.ngan_hang, 'nh') +
    o('SỐ TIỀN', String(Math.round(ck.so_tien)), 'tien') +
    o('NỘI DUNG CHUYỂN KHOẢN', ck.noi_dung, 'nd') +
    '</div>';

  html += '<div class="card" style="padding:12px 14px;background:#f0fdfa;border:1.5px solid #99f6e4">' +
    '<div style="font-size:11.5px;color:#0f766e;font-weight:800">SỐ TIỀN CHUYỂN</div>' +
    '<div style="font-size:24px;font-weight:800;color:#0f766e;margin-top:2px">' + money(ck.so_tien) + ' đ</div>' +
    (Number(ck.da_tam_ung) > 0 ? '<div style="font-size:12.5px;color:#0f766e;margin-top:3px">Tổng hồ sơ ' + money(ck.tong_tien) + ' đ, đã trừ tạm ứng ' + money(ck.da_tam_ung) + ' đ</div>' : '') +
    '</div>';

  var foot = '<div style="display:flex;gap:8px">' +
    '<button class="btn" id="ckDong" style="flex:2">📋 Copy cả dòng cho file MB</button>' +
    '<button class="btn gh" id="ckVe" style="flex:1">← Về hồ sơ</button></div>';
  var b = frame('Nội dung chuyển khoản', html, { footer: foot });

  var BANG = { stk: [ck.stk, 'số tài khoản'], ten: [ck.ten_nhan_ck, 'tên thụ hưởng'], nh: [ck.ngan_hang, 'ngân hàng'], tien: [String(Math.round(ck.so_tien)), 'số tiền'], nd: [ck.noi_dung, 'nội dung'] };
  b.addEventListener('click', function (e) {
    var el = e.target.closest('[data-ckc]'); if (!el) return;
    var x = BANG[el.getAttribute('data-ckc')];
    if (x) hsCopy(x[0], x[1]);
  });
  document.getElementById('ckDong').onclick = function () { hsCopy(ck.dong_mb, 'cả dòng (' + ck.cot.join(', ') + ')'); };
  document.getElementById('ckVe').onclick = function () { go(function () { scrHoSoTTView(hs.ma); }); };
}



/* ============================================================================
   SIẾT HỒ SƠ HOÀN ỨNG: loại chứng từ, tệp chứng từ, nối phiếu nội bộ
   ============================================================================

   Anh Việt 22/08/2026: *"Luồng 'Hoàn ứng không hóa đơn' hiện tại đang có rủi
   ro gian lận cao. Kế toán trưởng yêu cầu siết chặt hồ sơ, bắt buộc phải có
   chứng từ đính kèm"*.

   Lỗ hổng thật: một dòng hoàn ứng chỉ cần nội dung, số tiền và mã giao dịch.
   Mã giao dịch chứng minh TIỀN ĐÃ ĐI, không chứng minh tiền đi mua cái gì.

   Ba thứ thêm vào, tất cả gắn theo TỪNG DÒNG chứ không phải cả hồ sơ, vì một
   hồ sơ hoàn ứng gom hàng chục khoản của nhiều người bán. Đính một xấp ảnh
   vào hồ sơ thì kế toán vẫn phải ngồi đoán ảnh nào của khoản nào.

   Tệp tải lên NGAY lúc bấm, không đợi tới lúc lưu hồ sơ: máy chủ trả về mã
   tệp, dòng giữ mã đó. Làm vậy để ảnh chụp xong là thấy ngay hình thu nhỏ,
   và để lỗi mạng lộ ra tại chỗ chứ không đợi tới lúc bấm Lập rồi mới đổ. */

var HU_DM_CT = null;   /* danh mục loại chứng từ, tải một lần rồi giữ */

async function huLayDmCt() {
  if (!HU_DM_CT) {
    var kq = await api('vagabond.ho_so_tt.ds_loai_chung_tu', {});
    HU_DM_CT = (kq && kq.ds) || [];
  }
  return HU_DM_CT;
}

/* ---------- Cột 1: loại chứng từ ---------- */

function huOLoaiCt(x, i) {
  var co = (x.loai_chung_tu || '').trim();
  return '<td style="padding:7px 8px">' +
    '<div data-hulct="' + i + '" style="cursor:pointer;border:1.5px solid ' +
    (co ? '#99f6e4' : '#e5e7eb') + ';background:' + (co ? '#f0fdfa' : '#fff') +
    ';border-radius:8px;padding:5px 8px;font-size:11.5px;color:' +
    (co ? '#0f766e' : '#9ca3af') + ';font-weight:' + (co ? '700' : '500') +
    ';white-space:nowrap;display:flex;align-items:center;gap:5px">' +
    '<span style="flex:1;overflow:hidden;text-overflow:ellipsis;max-width:120px">' +
    h(co || 'Chọn loại') + '</span><span style="font-size:9px">▾</span></div></td>';
}

async function huChonLoaiCt(i) {
  var ds;
  busy(true);
  try { ds = await huLayDmCt(); } catch (e) {
    busy(false); return baoTin(errMsg(e) || 'Chưa đọc được danh mục chứng từ.', 'Lỗi');
  }
  busy(false);
  if (!ds.length) return baoTin('Danh mục loại chứng từ đang trống. Báo bộ phận kỹ thuật để nạp lại.', 'Chưa có dữ liệu');
  sheet('Loại chứng từ · ' + ds.length + ' loại',
    ds.map(function (r) {
      return {
        value: r.ma, label: r.ten,
        phu: (r.bat_buoc_tep ? 'bắt buộc có tệp' : 'không bắt buộc tệp') +
             (r.vat ? ' · hoá đơn VAT' : '') + (r.mo_ta ? ' · ' + r.mo_ta : ''),
        tim: r.ten
      };
    }),
    huDong[i] ? (huDong[i].loai_chung_tu || '') : '',
    function (it) {
      if (!huDong[i]) return;
      huDong[i].loai_chung_tu = it.value;
      go(huManHienTai(), true);
    }, true);
}

/* ---------- Cột 2: tệp chứng từ, hiện hình thu nhỏ ----------

   Kế toán nhìn lướt bảng là biết dòng nào đã có giấy tờ, dòng nào chưa. Chữ
   "đã có 2 tệp" không làm được việc đó bằng hai cái hình nhỏ. */

function huOTep(x, i) {
  var ds = x.tep || [];
  var o = '<td style="padding:7px 8px;white-space:nowrap">';
  if (ds.length) {
    /* Chua nut X vao goc tung o (anh Viet 24/08/2026). Truoc do phai cham
       vao chinh o anh moi go duoc, khong ai doan ra: ke toan dinh nham mot
       to roi ngoi tim nut go. Nay cham vao anh la MO ra xem, cham vao X moi
       go - hai viec khac nhau thi hai cho bam khac nhau. */
    o += '<div style="display:flex;gap:9px 7px;align-items:center;flex-wrap:wrap;max-width:150px;padding-top:5px">';
    ds.slice(0, 3).forEach(function (t) {
      o += oTep({
        url: t.url, ten: t.ten, anh: t.la_anh, co: 38,
        mo: 'data-huxemtep="' + h(t.url) + '"',
        go: 'data-hugotep="' + i + '|' + h(t.ma) + '"'
      });
    });
    if (ds.length > 3) {
      o += '<span style="font-size:11px;color:#6b7280">+' + (ds.length - 3) + '</span>';
    }
    o += '<span data-hutep="' + i + '" style="cursor:pointer;font-size:16px;color:#0f766e;padding:0 3px">＋</span>';
    o += '</div>';
  } else {
    o += '<div data-hutep="' + i + '" style="cursor:pointer;border:1.5px dashed #fca5a5;background:#fef2f2;' +
      'border-radius:8px;padding:6px 8px;font-size:11.5px;color:#b91c1c;font-weight:700;text-align:center">' +
      '📎 Tải chứng từ</div>';
  }
  return o + '</td>';
}

async function huThemTepDong(i) {
  if (!huDong[i]) return;
  var f = await huChonTep();
  if (!f) return;
  if (f.size > 12 * 1024 * 1024) {
    return toast('Tệp nặng quá 12 MB nên máy không nhận. Vui lòng chụp lại nhỏ hơn.', 5500);
  }
  busy(true);
  var t;
  try { t = await huUpTep(f); }
  catch (e) { busy(false); return toast('Không tải tệp lên được: ' + ((e && e.message) || ''), 6500); }
  busy(false);
  var ten = t.ten || '';
  var duoi = ten.indexOf('.') >= 0 ? ten.split('.').pop().toLowerCase() : '';
  huDong[i].tep = (huDong[i].tep || []).concat([{
    ma: t.ma, ten: ten, url: t.url,
    la_anh: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].indexOf(duoi) >= 0 ? 1 : 0
  }]);
  toast('Đã đính ' + ten + ' vào khoản số ' + (i + 1), 3000);
  go(huManHienTai(), true);
}

async function huGoTepDong(i, ma) {
  if (!huDong[i]) return;
  var ds = huDong[i].tep || [];
  var t = ds.filter(function (x) { return x.ma === ma; })[0];
  var ok = await xacNhan('Gỡ "' + ((t && t.ten) || ma) + '" khỏi khoản số ' + (i + 1) + '?',
    'Gỡ chứng từ', 'Gỡ');
  if (!ok) return;
  huDong[i].tep = ds.filter(function (x) { return x.ma !== ma; });
  go(huManHienTai(), true);
}

/* ---------- Cột 3: nối phiếu thanh toán nội bộ ----------

   Khoản nào quản lý đã lập phiếu và đã được duyệt thì không việc gì phải
   khai lại từ đầu. Bấm một nút, máy kéo số tiền, nội dung và TẤT CẢ tệp của
   phiếu đó sang dòng này.

   Chỉ hiện phiếu đã duyệt và CHƯA nối hồ sơ nào. Một phiếu nối hai lần là
   công ty trả tiền hai lần cho cùng một khoản, nên backend chặn thêm lần
   nữa lúc ghi chứ không tin mỗi màn hình. */

function huOPhieu(x, i) {
  var co = (x.de_nghi_chi || '').trim();
  return '<td style="padding:7px 8px;white-space:nowrap">' +
    '<div data-huphieu="' + i + '" style="cursor:pointer;border:1.5px solid ' +
    (co ? '#c7d2fe' : '#e5e7eb') + ';background:' + (co ? '#eef2ff' : '#fff') +
    ';border-radius:8px;padding:5px 8px;font-size:11.5px;color:' +
    (co ? '#4338ca' : '#6b7280') + ';font-weight:' + (co ? '700' : '500') + '">' +
    (co ? '🔗 ' + h(co) : '🔗 Nối phiếu') + '</div></td>';
}

async function huNoiPhieuNoiBo(i) {
  if (!huDong[i]) return;
  busy(true);
  var kq;
  try { kq = await api('vagabond.ho_so_tt.ds_phieu_noi_bo', {}); }
  catch (e) { busy(false); return baoTin(errMsg(e) || 'Chưa đọc được danh sách phiếu.', 'Lỗi'); }
  busy(false);
  /* Doc kq.loi TRUOC. May chu tra {ds: [], loi: "..."} khi doc bang hong,
     ma cau "khong co phieu nao" thi Uyen tin la quan ly chua lap phieu roi
     go tay lai toan bo khoan chi - dung duong sinh ra chi hai lan. */
  if (kq && kq.loi) {
    return baoTin(kq.loi + '\n\nĐây là lỗi đọc dữ liệu, KHÔNG phải là không có phiếu. ' +
      'Thử lại sau một phút, còn nếu vẫn vậy thì báo anh Việt, đừng gõ tay lại khoản đã có phiếu.',
      'Chưa đọc được danh sách');
  }
  var ds = (kq && kq.ds) || [];
  if (!ds.length) {
    return baoTin('Không có phiếu thanh toán nội bộ nào đã duyệt mà chưa nối hồ sơ.\n\n' +
      'Phiếu còn nháp hoặc đang chờ duyệt thì chưa nối được, và phiếu đã nối vào hồ sơ ' +
      'khác cũng không hiện ra ở đây để tránh trả tiền hai lần.', 'Chưa có phiếu nào');
  }
  /* Phieu da noi o mot dong KHAC cua chinh to nay thi phai noi ro ra.
     Bang chon truoc day khong danh dau gi, nen chon nham cung mot phieu cho
     hai dong la chuyen thuong, va moi lan nhan lai de so tien phieu len
     dong - tong ho so doi len dung mot lan so tien do. May chu nay da chan
     (`_soi_phieu_noi_bo`), nhung chan o day thi nguoi ta khong mat cong go
     xong 12 dong roi moi bi tra ve. */
  var daDung = {};
  huDong.forEach(function (d, j) {
    var m = (d && d.de_nghi_chi || '').trim();
    if (m && j !== i) daDung[m] = j + 1;
  });
  sheet('Phiếu thanh toán nội bộ · ' + ds.length + ' phiếu',
    ds.map(function (r) {
      var oDong = daDung[r.ma];
      return {
        value: r.ma,
        label: (oDong ? '⚠️ ' : '') + r.ten + ' · ' + money(r.so_tien) + ' đ',
        phu: (oDong ? 'ĐÃ NỐI Ở KHOẢN SỐ ' + oDong + ' · ' : '') +
             r.ma + ' · ' + (r.nguoi_ten || r.nguoi_tao) + ' · ' + hsNgayVn(r.ngay) +
             ' · ' + r.trang_thai + (r.so_tep ? ' · ' + r.so_tep + ' tệp' : ' · chưa có tệp'),
        tim: r.ma + ' ' + r.ten + ' ' + (r.nguoi_ten || '') + ' ' + (r.dien_giai || '')
      };
    }), huDong[i].de_nghi_chi || '',
    function (it) { huXemVaNoiPhieu(i, it.value); }, true);
}

async function huXemVaNoiPhieu(i, ma) {
  var oDong = -1;
  huDong.forEach(function (d, j) {
    if (j !== i && (d && d.de_nghi_chi || '').trim() === ma) oDong = j + 1;
  });
  if (oDong > 0) {
    return baoTin('Phiếu ' + ma + ' đã nối vào khoản số ' + oDong + ' của hồ sơ này rồi.\n\n' +
      'Mỗi phiếu chỉ nối được một lần. Nối hai lần là tổng hồ sơ dôi lên đúng một lần ' +
      'số tiền của phiếu, mà người duyệt không nhìn ra vì màn hồ sơ không hiện mã phiếu.',
      'Phiếu đã dùng rồi');
  }
  busy(true);
  var p;
  try { p = await api('vagabond.ho_so_tt.xem_phieu_noi_bo', { phieu: ma }); }
  catch (e) { busy(false); return baoTin(errMsg(e) || 'Không đọc được phiếu này.', 'Không nối được'); }
  busy(false);
  var cu = huDong[i] || {};
  var doiTien = Number(cu.so_tien || 0) > 0 && Math.abs(Number(cu.so_tien) - Number(p.so_tien)) > 1;
  var noi = '<div class="card" style="padding:0"><div class="kv"><span>Phiếu</span><b>' + h(p.ma) + '</b></div>' +
    '<div class="kv"><span>Nội dung</span><b style="text-align:right">' + h(p.noi_dung) + '</b></div>' +
    '<div class="kv"><span>Số tiền</span><b>' + money(p.so_tien) + ' đ</b></div>' +
    '<div class="kv"><span>Người lập</span><b>' + h(p.nguoi_ten || p.nguoi_tao) + '</b></div>' +
    '<div class="kv"><span>Trạng thái</span><b>' + h(p.trang_thai) + '</b></div>' +
    '<div class="kv"><span>Tệp đính kèm</span><b>' + ((p.tep || []).length || 'chưa có') + '</b></div></div>';
  if ((p.tep || []).length) {
    noi += '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:10px">' +
      p.tep.map(function (t) {
        return '<img src="' + h(t.url) + '" style="width:54px;height:54px;object-fit:cover;border-radius:8px;border:1px solid #d1d5db">';
      }).join('') + '</div>';
  }
  noi += '<div style="font-size:12.5px;color:#5a6070;line-height:1.55;margin-top:12px">' +
    'Nhận thì máy đắp <b>số tiền, nội dung và toàn bộ tệp</b> của phiếu này vào khoản số ' +
    (i + 1) + '.' +
    (doiTien
      ? '<div style="color:#b45309;margin-top:6px"><b>Khoản này đang ghi ' + money(cu.so_tien) +
        ' đ, phiếu ghi ' + money(p.so_tien) + ' đ.</b> Nhận thì số của phiếu đè lên số đang có.</div>'
      : '') +
    '</div>';
  var hop = hopKhung('Nối phiếu ' + p.ma, noi,
    '<button class="btn gh" data-hpdong style="flex:1">Thôi</button>' +
    '<button class="btn" data-hpok style="flex:2">Nhận vào khoản ' + (i + 1) + '</button>');
  hop.box.querySelector('.x').onclick = hop.dong;
  hop.ov.onclick = function (e) {
    if (e.target === hop.ov || e.target.closest('[data-hpdong]')) return hop.dong();
    if (!e.target.closest('[data-hpok]')) return;
    hop.dong();
    var d = huDong[i];
    d.de_nghi_chi = p.ma;
    d.so_tien = Number(p.so_tien) || d.so_tien;
    if (p.noi_dung) d.noi_dung = p.noi_dung;
    if (p.ben_ban && !d.ben_ban) d.ben_ban = p.ben_ban;
    if (p.so_hoa_don && !d.so_hd_ncc) d.so_hd_ncc = p.so_hoa_don;
    if (p.loai_chung_tu && !d.loai_chung_tu) d.loai_chung_tu = p.loai_chung_tu;
    if (p.co_vat) d.co_vat = 1;
    var daCo = (d.tep || []).map(function (t) { return t.ma; });
    (p.tep || []).forEach(function (t) {
      if (daCo.indexOf(t.ma) >= 0) return;
      var ten = t.ten || '';
      var duoi = ten.indexOf('.') >= 0 ? ten.split('.').pop().toLowerCase() : '';
      d.tep = (d.tep || []).concat([{
        ma: t.ma, ten: ten, url: t.url,
        la_anh: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].indexOf(duoi) >= 0 ? 1 : 0
      }]);
    });
    toast('Đã nối phiếu ' + p.ma + ' vào khoản số ' + (i + 1), 3600);
    go(scrHoanUngTao, true);
  };
}

/* Gửi lên máy chủ thì chỉ cần MÃ tệp, phần tên và đường dẫn là để vẽ màn
   hình. Gửi cả cục cũng không sai nhưng nặng vô ích khi hồ sơ ba chục dòng. */
/* ---------- Bảng khoản chi: gõ thẳng trên dòng, kiểu Excel ----------

Anh Việt 24/08/2026: *"Cách nhập liệu bằng form rời bên dưới đang làm Kế
toán mất thời gian. Sửa lại logic nút 'Gõ tay': Khi bấm vào nút này, hệ
thống sẽ sinh ra một dòng trắng trực tiếp ngay trên bảng (Grid/Table) phía
trên. Cho phép user nhập liệu (Inline Editing) số tiền, nội dung, chọn
chứng từ... trực tiếp ngay trên dòng hàng đó, giống hệt thao tác trên
Excel."*

Cách cũ là một chuỗi bảy tám hộp thoại nối đuôi nhau: nội dung, số tiền,
ngày, số hoá đơn, bên bán, loại chi, hoá đơn VAT, tài khoản Nợ. Bấm Huỷ ở
bước thứ bảy là mất sạch sáu bước trước. Một xấp hai mươi tờ hoá đơn là một
trăm sáu mươi lần chạm.

BA ĐIỀU PHẢI GIỮ, không thì mất chữ đang gõ:

  1. Ô nhập ghi thẳng vào `huDong[i]` ngay lúc gõ (`oninput`), không đợi.
  2. Gõ chữ TUYỆT ĐỐI không vẽ lại màn. Vẽ lại là ô mất tiêu điểm, bàn phím
     điện thoại tụt xuống, và con trỏ nhảy về đầu ô. Uyên gặp đúng cảnh đó
     ở màn duyệt mua hàng ngày 21/08/2026.
  3. Những thứ phải mở hộp thoại (loại chứng từ, tệp, phiếu nội bộ, tài
     khoản Nợ) thì được vẽ lại, vì lúc đó ô nhập đã ghi xong vào mảng rồi.

Tổng tiền ở đầu màn không nằm trong bảng nên không được vẽ lại: cập nhật
riêng bằng `huCapNhatTong`, không thì gõ số xong nhìn lên vẫn thấy số cũ. */

var huSuaO = -1;

function huLaTkct() { return huMode === 'tkct'; }

/* Một ô nhập trong dòng đang sửa. `khoa` là tên trường trong huDong[i]. */
function huONhap(i, khoa, gt, opt) {
  opt = opt || {};
  return '<input data-hug="' + i + '|' + h(khoa) + '"' +
    ' type="' + (opt.kieu || 'text') + '"' +
    (opt.kieu === 'number' ? ' inputmode="numeric" step="any"' : '') +
    ' value="' + h(gt == null ? '' : gt) + '"' +
    ' placeholder="' + h(opt.ph || '') + '"' +
    ' style="width:100%;box-sizing:border-box;border:1.5px solid #99f6e4;border-radius:7px;' +
    'padding:6px 7px;font-size:' + (opt.co || '12.5') + 'px;font-weight:' + (opt.dam ? '700' : '400') +
    ';background:#f0fdfa;color:#0f172a' + (opt.phai ? ';text-align:right' : '') + '">';
}

function huChipNho(thuoc_tinh, nhan, dang_bat) {
  return '<span ' + thuoc_tinh + ' style="cursor:pointer;display:inline-block;padding:3px 8px;' +
    'border-radius:11px;font-size:11px;font-weight:700;border:1.5px solid ' +
    (dang_bat ? '#0e7490;background:#cffafe;color:#0e7490' : '#e5e7eb;background:#fff;color:#9ca3af') +
    '">' + h(nhan) + '</span>';
}

/* Cột Tài khoản Nợ, chỉ có ở màn Chi từ TK công ty. */
function huOTkNo(x, i) {
  var co = (x.tk_no || '').trim();
  return '<td style="padding:7px 8px">' +
    '<div data-hutkno="' + i + '" style="cursor:pointer;border:1.5px solid ' +
    (co ? '#99f6e4' : '#fca5a5') + ';background:' + (co ? '#f0fdfa' : '#fef2f2') +
    ';border-radius:8px;padding:5px 8px;font-size:11.5px;color:' + (co ? '#0f766e' : '#b91c1c') +
    ';font-weight:700;white-space:nowrap">' + h(co || '⚠️ chọn TK Nợ') + '</div></td>';
}

function huODong(x, i) {
  var sua = i === huSuaO;
  var o = '<tr data-hux="' + i + '" style="border-top:1px solid #eef2f5;cursor:pointer' +
    (sua ? ';background:#f0fdfa' : '') + '">';
  o += '<td style="padding:9px 10px;color:#6b7280">' + (i + 1) + '</td>';

  if (!sua) {
    o += '<td style="padding:9px 10px;white-space:nowrap">' + (hsNgayVn(x.ngay_hd) || '-') + '</td>'
      + '<td style="padding:9px 10px">' + h(x.noi_dung || '(chưa ghi)')
      + (x.so_hd_ncc ? '<br><span style="color:#6b7280;font-size:11.5px">HĐ ' + h(x.so_hd_ncc) + '</span>' : '')
      + (x.ben_ban ? '<br><span style="color:#6b7280;font-size:11.5px">' + h(x.ben_ban) + '</span>' : '')
      + '<br><span style="font-size:11.5px;color:' + (x.co_vat ? '#0e7490' : '#92400e') + '">'
      + (x.co_vat ? '🧾 có hoá đơn VAT' : '📄 không hoá đơn') + (x.loai_chi ? ' · ' + h(x.loai_chi) : '') + '</span></td>';
  } else {
    o += '<td style="padding:7px 8px;min-width:118px">' + huONhap(i, 'ngay_hd', x.ngay_hd, { kieu: 'date' }) + '</td>'
      + '<td style="padding:7px 8px;min-width:230px">'
      + huONhap(i, 'noi_dung', x.noi_dung, { ph: 'Nội dung chi (mua gì, sửa gì)', dam: 1, co: '13.5' })
      + '<div style="display:flex;gap:5px;margin-top:5px">'
      + '<div style="flex:1">' + huONhap(i, 'so_hd_ncc', x.so_hd_ncc, { ph: 'Số hoá đơn' }) + '</div>'
      + '<div style="flex:1">' + huONhap(i, 'ben_ban', x.ben_ban, { ph: 'Bên bán' }) + '</div></div>'
      + '<div style="display:flex;gap:5px;margin-top:6px;flex-wrap:wrap;align-items:center">'
      + huChipNho('data-huvat="' + i + '"', x.co_vat ? '🧾 có hoá đơn VAT' : '📄 không hoá đơn', !!x.co_vat)
      + huChipNho('data-hulc="' + i + '"', x.loai_chi ? '📦 ' + x.loai_chi : '📦 Loại chi', !!x.loai_chi)
      + huChipNho('data-hugy="' + i + '"', '💡 Khoản hay gặp', false)
      + '</div></td>';
  }

  o += huOLoaiCt(x, i) + huOTep(x, i);
  if (huLaTkct()) o += huOTkNo(x, i); else o += huOPhieu(x, i);

  if (!sua) {
    o += '<td style="padding:9px 10px;text-align:right;white-space:nowrap;font-weight:700">' + money(x.so_tien) + '</td>';
  } else {
    o += '<td style="padding:7px 8px;min-width:120px">' +
      huONhap(i, 'so_tien', x.so_tien || '', { kieu: 'number', ph: '0', dam: 1, phai: 1, co: '14' }) + '</td>';
  }

  if (!huLaTkct()) {
    o += sua
      ? '<td style="padding:7px 8px;min-width:130px">' + huONhap(i, 'ma_giao_dich', x.ma_giao_dich, { ph: 'Mã giao dịch' }) + '</td>'
      : '<td style="padding:9px 10px;white-space:nowrap;font-size:11.5px;color:' + (x.ma_giao_dich ? '#0e7490' : '#b45309') + '">'
        + (x.ma_giao_dich ? h(x.ma_giao_dich) : '⚠️ chưa gắn') + '</td>';
  }

  o += huOXoa(i, sua);
  return o + '</tr>';
}

/* Cả bảng. Dùng chung cho màn Hoàn ứng và màn Chi từ TK công ty: hai màn
   khác nhau ở hai cột (bên kia có Phiếu nội bộ và Mã giao dịch, bên này có
   Tài khoản Nợ), còn lại giống hệt. Trước đây mỗi màn tự vẽ một bảng riêng,
   nên cột Chứng từ chỉ có ở màn Hoàn ứng - đúng cái anh Việt yêu cầu sửa. */
function huVeBang() {
  var tkct = huLaTkct();
  var cot = ['STT', 'Ngày mua', 'Nội dung', 'Loại chứng từ', 'Chứng từ',
    tkct ? 'Tài khoản Nợ' : 'Phiếu nội bộ', 'Số tiền'];
  if (!tkct) cot.push('Mã giao dịch');
  cot.push('Xoá');
  var html = hsoKhoi('Các khoản đã chi · bấm một dòng để sửa ngay trên dòng đó')
    + '<div class="card" style="padding:0;overflow-x:auto">'
    + '<table style="width:100%;border-collapse:collapse;font-size:12.5px;min-width:' + (tkct ? '820' : '900') + 'px">'
    + '<tr style="background:#f8fafc;color:#6b7280;font-size:11.5px;text-align:left">'
    + cot.map(function (c) {
      return '<th style="padding:8px 10px;font-weight:700' +
        (c === 'Số tiền' ? ';text-align:right' : (c === 'Xoá' ? ';text-align:center' : '')) + '">' + h(c) + '</th>';
    }).join('') + '</tr>';
  if (!huDong.length) {
    html += '<tr><td colspan="' + cot.length + '" style="padding:24px;text-align:center;color:#6b7280">' +
      'Chưa có khoản nào. Bấm <b>➕ Gõ tay</b> ở dưới để thêm một dòng trắng.</td></tr>';
  }
  huDong.forEach(function (x, i) { html += huODong(x, i); });
  return html + '</table></div>';
}

/* Thêm một dòng trắng rồi mở luôn nó ra cho gõ. */
function huThemDongTrong() {
  huDong.push({
    ngay_hd: today(), so_hd_ncc: '', noi_dung: '', ben_ban: '',
    loai_chi: 'Hang hoa', co_vat: 0, so_tien: 0, tk_no: '',
    ma_giao_dich: '', ghi_chu: '', tep: []
  });
  huSuaO = huDong.length - 1;
  go(huManHienTai(), true);
  /* Đưa con trỏ vào ô Nội dung của dòng vừa thêm, để gõ được ngay mà không
     phải chạm thêm một lần nữa. Đợi một nhịp cho màn vẽ xong. */
  setTimeout(function () {
    var o = document.querySelector('[data-hug="' + huSuaO + '|noi_dung"]');
    if (o) o.focus();
  }, 60);
}

function huCapNhatTong() {
  var a = document.getElementById('huTongTien');
  if (a) a.textContent = money(huTong()) + ' đ';
  var b2 = document.getElementById('huConLai');
  if (b2) b2.textContent = money(huTong() - Number(huTamUng)) + ' đ';
  var c = document.getElementById('huSoKhoan');
  if (c) c.textContent = huDong.length + ' khoản';
}

/* Nối sự kiện cho bảng. Gọi một lần sau khi frame() đã dựng xong màn. */
function huNoiBang(b) {
  /* Gõ chữ: ghi thẳng vào mảng, KHÔNG vẽ lại. Xem ghi chú đầu mục. */
  b.addEventListener('input', function (e) {
    var el = e.target.closest ? e.target.closest('[data-hug]') : null;
    if (!el) return;
    var p = String(el.getAttribute('data-hug')).split('|');
    var i = +p[0], k = p[1];
    if (!huDong[i]) return;
    huDong[i][k] = k === 'so_tien'
      ? Math.max(0, Number(String(el.value).replace(/[^0-9.]/g, '')) || 0)
      : el.value;
    if (k === 'so_tien') huCapNhatTong();
  });

  b.addEventListener('click', function (e) {
    /* Ô nhập nằm trong dòng, mà cả dòng lại là nút mở dòng khác. Chạm vào ô
       nhập không được coi là chạm vào dòng, không thì bấm vào ô là đóng
       dòng đang gõ lại. */
    if (e.target.closest('[data-hug]')) return;

    var n = e.target.closest('[data-hulct],[data-hutep],[data-huphieu],[data-hugotep],' +
      '[data-huxoa],[data-huxong],[data-huvat],[data-hulc],[data-hugy],[data-hutkno],[data-huxemtep]');
    if (n) {
      e.stopPropagation();
      if (n.hasAttribute('data-huxemtep')) {
        var u = n.getAttribute('data-huxemtep');
        if (u) window.open(u, '_blank');
        return;
      }
      if (n.hasAttribute('data-huxoa')) return huXoaDong(+n.getAttribute('data-huxoa'));
      if (n.hasAttribute('data-huxong')) { huSuaO = -1; return go(huManHienTai(), true); }
      if (n.hasAttribute('data-huvat')) {
        var iv = +n.getAttribute('data-huvat');
        if (huDong[iv]) huDong[iv].co_vat = huDong[iv].co_vat ? 0 : 1;
        return go(huManHienTai(), true);
      }
      if (n.hasAttribute('data-hulc')) return huChonLoaiChi(+n.getAttribute('data-hulc'));
      if (n.hasAttribute('data-hugy')) return huChonGoiY(+n.getAttribute('data-hugy'));
      if (n.hasAttribute('data-hutkno')) return huChonTkNoDong(+n.getAttribute('data-hutkno'));
      if (n.hasAttribute('data-hulct')) return huChonLoaiCt(+n.getAttribute('data-hulct'));
      if (n.hasAttribute('data-hutep')) return huThemTepDong(+n.getAttribute('data-hutep'));
      if (n.hasAttribute('data-hugotep')) {
        var p2 = n.getAttribute('data-hugotep').split('|');
        return huGoTepDong(+p2[0], p2[1]);
      }
      return huNoiPhieuNoiBo(+n.getAttribute('data-huphieu'));
    }
    var r = e.target.closest('[data-hux]');
    if (!r) return;
    var i2 = +r.getAttribute('data-hux');
    if (i2 === huSuaO) return;
    huSuaO = i2;
    go(huManHienTai(), true);
  });
}

/* Danh sách khoản hay gặp. Trước đây chỉ màn Chi từ TK công ty có, và nằm
   trong chuỗi hộp thoại. Nay cả hai màn đều bấm được, ngay trên dòng. */
async function huChonGoiY(i) {
  if (!huDong[i]) return;
  var gy = await hoiChon('Khoản hay gặp', 'Chọn cho nhanh, hoặc bấm Huỷ rồi gõ tay.',
    HU_GOI_ND.map(function (t) { return { k: t, icon: '•', nhan: t }; }),
    huDong[i].noi_dung || '');
  if (gy === null || !gy) return;
  huDong[i].noi_dung = gy;
  go(huManHienTai(), true);
}

async function huChonLoaiChi(i) {
  if (!huDong[i]) return;
  var lc = await hoiChon('Loại chi', 'Khoản này thuộc nhóm nào?', [
    { k: 'Hang hoa', icon: '📦', nhan: 'Hàng hoá' },
    { k: 'Hang test', icon: '🧪', nhan: 'Hàng test', mo_ta: 'Mua thử, không nhập kho' },
    { k: 'Hang phat sinh', icon: '➕', nhan: 'Hàng phát sinh' },
    { k: 'Chi phi', icon: '🔧', nhan: 'Chi phí', mo_ta: 'Bảo trì, sửa chữa, dịch vụ' },
    { k: 'Khac', icon: '❓', nhan: 'Khác' }
  ], huDong[i].loai_chi || 'Hang hoa');
  if (lc === null) return;
  huDong[i].loai_chi = lc || '';
  go(huManHienTai(), true);
}

async function huChonTkNoDong(i) {
  if (!huDong[i]) return;
  var tk = await huChonTaiKhoan('Tài khoản Nợ cho khoản "' +
    (huDong[i].noi_dung || 'chưa đặt tên') + '"', huDong[i].tk_no || '');
  if (tk === null) return;
  huDong[i].tk_no = tk || '';
  go(huManHienTai(), true);
}

function huDongGuiDi() {
  return huDong.map(function (x) {
    var d = {};
    Object.keys(x).forEach(function (k) { if (k !== 'tep') d[k] = x[k]; });
    d.tep = (x.tep || []).map(function (t) { return t.ma; });
    return d;
  });
}

/* ---------- Xoá một khoản chi ----------

Anh Việt 22/08/2026: *"Em cho anh thêm nút xoá cái dòng nữa để có thể xoá
dòng nếu add nhầm."*

Thêm nhầm một dòng là chuyện xảy ra hàng ngày, mà trước đây muốn bỏ thì phải
mở bảng sửa dòng rồi tìm nút xoá trong đó - không ai biết là có. Nay có dấu
nhân ngay cuối dòng, nhìn là thấy.

Hỏi lại trước khi xoá vì thao tác này không lùi được, và trên điện thoại thì
ngón tay chạm nhầm rất dễ. */

function huOXoa(i, dang_sua) {
  /* Dong dang mo thi co them dau tich de dong lai. Khong bat buoc bam: go
     xong bam sang dong khac hay bam Luu deu duoc, vi chu da ghi vao mang
     ngay luc go. Dau tich chi de nguoi dung yen tam la da xong dong nay. */
  return '<td style="padding:7px 8px;text-align:center;white-space:nowrap">' +
    (dang_sua
      ? '<span data-huxong="' + i + '" title="Xong dòng này" ' +
        'style="display:inline-flex;width:30px;height:30px;align-items:center;justify-content:center;' +
        'border:1.5px solid #99f6e4;background:#f0fdfa;color:#0f766e;border-radius:8px;' +
        'cursor:pointer;font-size:15px;line-height:1;margin-right:5px">&check;</span>'
      : '') +
    '<span data-huxoa="' + i + '" title="Xoá khoản này" ' +
    'style="display:inline-flex;width:30px;height:30px;align-items:center;justify-content:center;' +
    'border:1.5px solid #fecaca;background:#fef2f2;color:#b91c1c;border-radius:8px;' +
    'cursor:pointer;font-size:16px;line-height:1">&times;</span></td>';
}

async function huXoaDong(i) {
  var x = huDong[i];
  if (!x) return;
  var ten = (x.noi_dung || '').trim() || 'khoản số ' + (i + 1);
  var ok = await xacNhan(
    'Xoá "' + ten + '" (' + money(x.so_tien) + ' đ) khỏi hồ sơ đang lập?' +
    ((x.tep || []).length ? '\n\nKhoản này đang có ' + x.tep.length + ' tệp chứng từ, xoá dòng là bỏ luôn.' : '') +
    ((x.de_nghi_chi || '') ? '\n\nPhiếu nội bộ ' + x.de_nghi_chi + ' sẽ được trả lại để nối vào hồ sơ khác.' : ''),
    'Xoá khoản chi', 'Xoá');
  if (!ok) return;
  huDong.splice(i, 1);
  /* Xoa mot dong lam moi chi so phia sau tut xuong mot bac. Khong doi
     huSuaO theo thi con tro sua nhay sang dong khac, hoac tro ra ngoai
     mang va man hinh hien mot dong trang khong co that. */
  if (huSuaO === i) huSuaO = -1;
  else if (huSuaO > i) huSuaO = huSuaO - 1;
  toast('Đã xoá ' + ten, 2800);
  go(huManHienTai(), true);
}

/* ---------- Xoá một khoản khỏi hồ sơ ĐÃ LẬP ----------

Khác hẳn ở trên: hồ sơ đã lập thì mảng nằm trong cơ sở dữ liệu, phải qua
backend. Backend giữ ba điều mà màn hình không được tự quyết: chỉ xoá khi hồ
sơ chưa qua cửa duyệt nào, không cho xoá dòng cuối cùng, và trả lại phiếu
nội bộ đã nối. */

async function hsXoaDongHoSo(hs, stt, ten) {
  var ok = await xacNhan(
    'Xoá "' + (ten || ('khoản số ' + stt)) + '" khỏi hồ sơ ' + hs.ma + '?\n\n' +
    'Tệp chứng từ vẫn giữ trên máy chủ, chỉ dòng này bị bỏ.',
    'Xoá khoản chi', 'Xoá');
  if (!ok) return;
  busy(true);
  try {
    var r = await api('vagabond.ho_so_tt.xoa_dong', { name: hs.ma, dong: stt });
    busy(false);
    toast((r && r.ghi_chu) || 'Đã xoá khoản chi.', 4000);
    go(function () { scrHoSoTTView(hs.ma); }, true);
  } catch (e) {
    busy(false);
    baoTin(errMsg(e) || 'Không xoá được khoản chi.', 'Chưa xoá được');
  }
}

/* ---------- Bản thể hiện của hoá đơn, tải ngay lúc chọn hoá đơn ----------

Anh Việt 22/08/2026: *"khi chọn hoá đơn để hoàn ứng cho đơn vị đó thì em cho
luôn nút tải lên tệp thể hiện hoá đơn ở kế bên, bỏ cái nút đó ở bước sau cho
nó chặt chẽ, rồi combine luôn vào file để in ra trong bộ hồ sơ pdf."*

Vì sao chặt hơn hẳn cách cũ: trước đây nút tải nằm ở màn xem hồ sơ, tức là
SAU khi đã lập xong. Thiếu bản thể hiện thì phải quay lại tìm từng hoá đơn
một, mà lúc đó không ai còn nhớ tờ nào đã có tờ nào chưa. Nay nút nằm ngay
cạnh hoá đơn lúc đang chọn, và số tệp hiện luôn trên nút.

Tệp đính vào chính HOÁ ĐƠN chứ không vào hồ sơ: bản thể hiện là giấy tờ của
tờ hoá đơn, không phải của hồ sơ. Đính vào hoá đơn thì lần sau hoá đơn ấy
nằm trong hồ sơ khác vẫn có sẵn, và bộ hồ sơ PDF tự gộp vào qua đường `scan`
mà không phải nối thêm dây nào. */

var HS_DEM_BTH = {};   /* mã hoá đơn -> số bản thể hiện đang có */

function hsONutBanTheHien(maHd) {
  var n = HS_DEM_BTH[maHd];
  var co = n > 0;
  return '<span data-hsbth="' + h(maHd) + '" title="Tải bản thể hiện của hoá đơn" ' +
    'style="flex:none;margin-left:8px;display:inline-flex;align-items:center;gap:4px;' +
    'padding:6px 9px;border-radius:8px;cursor:pointer;font-size:11.5px;font-weight:700;' +
    'border:1.5px ' + (co ? 'solid #99f6e4' : 'dashed #fca5a5') + ';' +
    'background:' + (co ? '#f0fdfa' : '#fef2f2') + ';color:' + (co ? '#0f766e' : '#b91c1c') + '">' +
    (co ? '📄 ' + n + ' bản' : '📎 Bản thể hiện') + '</span>';
}

/* Dem mot luot cho ca danh sach roi ve lai, chu khong hoi tung dong: man
   chon hoa don bay vai chuc dong, hoi tung dong la vai chuc luot goi mang. */
async function hsDemBanTheHien(rows) {
  var ma = (rows || []).map(function (r) { return r.hoa_don; }).filter(Boolean);
  if (!ma.length) return;
  var chuaBiet = ma.filter(function (m) { return HS_DEM_BTH[m] === undefined; });
  if (!chuaBiet.length) return;
  try {
    var kq = await api('vagabond.ho_so_tt.dem_tep_hoa_don', { hoa_don: JSON.stringify(chuaBiet) });
    var d = (kq && kq.dem) || {};
    var doi = false;
    Object.keys(d).forEach(function (m) {
      if (HS_DEM_BTH[m] !== d[m]) { HS_DEM_BTH[m] = d[m]; doi = true; }
    });
    /* Chi ve lai khi that su co so moi. Ve lai vo co la cuop mat cai o
       nguoi ta dang go do. */
    if (doi) veLaiNutBanTheHien();
  } catch (e) { /* dem hong thi nut van bam duoc, khong chan luong */ }
}

function veLaiNutBanTheHien() {
  Array.prototype.forEach.call(document.querySelectorAll('[data-hsbth]'), function (el) {
    var ma = el.getAttribute('data-hsbth');
    var moi = document.createElement('div');
    moi.innerHTML = hsONutBanTheHien(ma);
    if (moi.firstChild) el.parentNode.replaceChild(moi.firstChild, el);
  });
}

async function hsTaiBanTheHien(maHd) {
  var f = await huChonTep();
  if (!f) return;
  if (f.size > 12 * 1024 * 1024) {
    return toast('Tệp nặng quá 12 MB nên máy không nhận. Vui lòng xuất lại bản PDF nhỏ hơn.', 5500);
  }
  busy(true);
  var t;
  try { t = await huUpTep(f); }
  catch (e) { busy(false); return toast('Không tải tệp lên được: ' + ((e && e.message) || ''), 6500); }
  try {
    await api('vagabond.ho_so_tt.dinh_tep_hoa_don', { hoa_don: maHd, tep: JSON.stringify([t]) });
    busy(false);
    HS_DEM_BTH[maHd] = (HS_DEM_BTH[maHd] || 0) + 1;
    veLaiNutBanTheHien();
    toast('Đã đính bản thể hiện vào hoá đơn ' + maHd, 3600);
  } catch (e2) {
    busy(false);
    baoTin(errMsg(e2) || 'Không đính được bản thể hiện.', 'Chưa đính được');
  }
}

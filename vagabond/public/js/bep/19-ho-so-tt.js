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
    [['', '📚 Tất cả'], ['NCC', '🏭 Công nợ NCC'], ['Hoan ung HD', '🧾 Hoàn ứng có HĐ'], ['Hoan ung', '🧮 Hoàn ứng không HĐ'], ['TK cong ty', '🏦 Chi từ TK công ty']].map(function (x) {
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

  html += '<div style="display:flex;gap:8px;margin-bottom:10px">' +
    '<button class="btn gh" id="hsXuat" style="flex:1;margin:0">📊 Xuất Excel</button>' +
    (Q.fin ? '<button class="btn gh" id="hsSepay" style="flex:1;margin:0">🏦 Dò SePay</button>' : '') +
    '</div>';

  html += '<div class="sec">Danh sách hồ sơ · bấm để xem và duyệt</div><div class="card">';
  if (!rows.length) html += '<div class="emp" style="padding:24px"><div class="e1">📁</div><div>Chưa có hồ sơ nào trong khoảng này. Bấm dấu ➕ để lập hồ sơ đầu tiên.</div></div>';
  else if (!loc.length) html += '<div class="emp" style="padding:24px"><div class="e1">✅</div><div>Không có hồ sơ nào thuộc nhóm <b>' + h(f.nhan) + '</b>.</div></div>';
  loc.forEach(function (r) {
    var m = hsMau[r.trang_thai] || ['#f3f4f6', '#e5e7eb', '#374151', '•'];
    html += '<div class="hub" data-hs="' + h(r.name) + '">' +
      '<div class="hub-i" style="background:' + m[0] + '">' + m[3] + '</div>' +
      '<div class="hub-t"><div class="t1">' + h(r.ten_ncc || r.nha_cung_cap) + '</div>' +
      '<div class="t2">' + h(r.ma) + ' · ' + hsNgayVn(r.ngay) + ' · ' + r.so_hd + (r.loai === 'Hoan ung' ? ' khoản' : ' hoá đơn') + '</div>' +
      '<div style="margin-top:4px"><span style="display:inline-block;background:' + m[0] +
      ';border:1px solid ' + m[1] + ';color:' + m[2] + ';border-radius:999px;padding:2px 9px;font-size:11.5px;font-weight:700">' +
      h(r.nhan) + '</span>' +
      (r.loai === 'Hoan ung' || r.loai === 'Hoan ung HD' ? '<span style="margin-left:6px;display:inline-block;background:#fffbeb;border:1px solid #fde68a;color:#92400e;border-radius:999px;padding:2px 9px;font-size:11.5px;font-weight:700">' + (r.loai === 'Hoan ung HD' ? '🧾 hoàn ứng có HĐ' : '🧮 hoàn ứng không HĐ') + '</span>' : '') +
      (r.tre_ngay > 0 ? '<span style="margin-left:7px;font-size:11.5px;color:#b3261e;font-weight:700">quá hạn ' + r.tre_ngay + ' ngày</span>' : '') +
      (r.email_da_gui ? '<span style="margin-left:7px;font-size:11.5px;color:#0e7490">✉️ đã báo NCC</span>' : '') +
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
/* Nguoi da ung tien mua ho, tuc nguoi NHAN lai tien. Chi dung cho luong
   hoan ung co hoa don. */
var hsTaoNguoiUng = '', hsTaoDsUng = null, hsUngTim = '';

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

async function scrHoSoTTTao() {
  hsoBuoc = 0;
  var laHU = hsTaoLoai === 'Hoan ung HD';
  frame(laHU ? 'Lập hồ sơ hoàn ứng có hoá đơn' : 'Lập hồ sơ thanh toán', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc công nợ phải trả...</div></div>');
  var dsn;
  try { dsn = await api('vagabond.ho_so_tt.ds_ncc_con_no', {}); }
  catch (e) { frame('Lập hồ sơ thanh toán', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var ncc = dsn.ncc || [];
  /* Luong hoan ung mo san o che do TAT CA nha cung cap: Uyen mua le te nen
     mot ho so cua chi thuong tro toi chuc nha khac nhau. Luong cong no NCC
     van chon dung mot nha nhu cu. */
  if (!laHU && !hsTaoNcc && ncc.length) hsTaoNcc = ncc[0].ncc;
  if (laHU && !hsTaoDsUng) {
    try { hsTaoDsUng = await api('vagabond.ho_so_tt.ds_nguoi_ung', {}); } catch (e3) { hsTaoDsUng = { ncc: [] }; }
  }

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
    var dsu = (hsTaoDsUng && hsTaoDsUng.ncc) || [];
    var q = hsUngTim.trim().toLowerCase();
    if (q) dsu = dsu.filter(function (x) { return String(x.ten || x.ncc).toLowerCase().indexOf(q) >= 0; });
    var hay = dsu.filter(function (x) { return x.hay_dung; }).slice(0, 8);
    if (!hay.length) hay = dsu.slice(0, 8);
    html += hsoKhoi('Người được hoàn ứng · bắt buộc') +
      '<div class="card" style="padding:10px 12px">' + kmHangChip(
        hay.map(function (x) {
          return posChipNut('data-hsu="' + h(x.ncc) + '"', h(x.ten), hsTaoNguoiUng === x.ncc);
        }).join('')) +
      (hsTaoNguoiUng ? '' :
        '<div style="font-size:12px;color:#b3261e;margin-top:8px;line-height:1.6">' +
        'Chưa chọn ai. Đây là người đã bỏ tiền túi mua hộ và sẽ nhận lại tiền, ' +
        'không phải nhà cung cấp trên hoá đơn.</div>') +
      hsKhungTimNcc('hsUngTim', hsUngTim, hay.length,
        'Người mới ứng tiền lần đầu thì chưa có hồ sơ. Tạo ở đây rồi chọn luôn.') + '</div>';
  }

  html += hsoKhoi('Nhà cung cấp còn nợ · ' + ncc.length + ' nhà, tổng ' + money(dsn.tong) + ' đ') +
    '<div class="card" style="padding:10px 12px">' + kmHangChip(
    (laHU ? posChipNut('data-hsn=""', '📚 Tất cả nhà cung cấp', !hsTaoNcc) : '') +
    ncc.map(function (x) {
      return posChipNut('data-hsn="' + h(x.ncc) + '"',
        h(x.ten) + ' · ' + money(x.tien) + (x.qua_han ? ' ⚠️' : ''), hsTaoNcc === x.ncc);
    }).join('')) +
    (laHU ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:8px;line-height:1.6">' +
      'Chip này chỉ để <b>lọc cho dễ nhìn</b>. Đổi chip không làm mất hoá đơn đã tick, ' +
      'nên anh chị tick bên nhà này rồi đổi sang nhà khác tick tiếp thoải mái.</div>' : '') + '</div>';

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
    '<button class="btn gh" id="hsChonHet" style="flex:1;margin:0">☑️ Chọn hết</button>' +
    '<button class="btn gh" id="hsChonQH" style="flex:1;margin:0">⚠️ Chỉ quá hạn</button>' +
    '<button class="btn gh" id="hsBoChon" style="flex:1;margin:0">✖ Bỏ chọn</button></div>';

  html += hsoKhoi('Chứng từ tham chiếu · hoá đơn còn nợ') + '<div class="card">';
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
      '</div><b style="white-space:nowrap">' + money(r.con_no) + ' đ</b></div>';
  });
  html += '</div>';

  html += '<div class="card" style="padding:12px 14px"><input class="tin" id="hsGc" placeholder="Ghi chú cho hồ sơ (không bắt buộc)" value="' + h(hsTaoGhiChu) + '"></div>';

  var foot = '<div style="display:flex;gap:8px">' +
    '<button class="btn" id="hsLuu" style="flex:2">📤 Lập và gửi kế toán</button>' +
    '<button class="btn gh" id="hsLuuNhap" style="flex:1">💾 Lưu nháp</button></div>';
  var b = frame(tenMan, html, { footer: foot });

  var ghiChon = function (r) { hsTaoChon[r.hoa_don] = { con_no: Number(r.con_no || 0), ten_ncc: r.ten_ncc || r.ncc || '' }; };

  Array.prototype.forEach.call(document.querySelectorAll('[data-hsn]'), function (el) {
    el.onclick = function () {
      hsTaoNcc = el.getAttribute('data-hsn');
      /* Luong hoan ung: doi chip la DOI BO LOC, khong phai bo lam lai.
         Xoa tick o day chinh la thu bat Uyen phai lam mot ho so cho moi
         nha cung cap. Luong cong no NCC thi van xoa, vi ho so do chi duoc
         phep mang mot nha. */
      if (!laHU) hsTaoChon = {};
      go(scrHoSoTTTao, true);
    };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-hsu]'), function (el) {
    el.onclick = function () { hsTaoNguoiUng = el.getAttribute('data-hsu'); go(scrHoSoTTTao, true); };
  });
  var oUt = document.getElementById('hsUngTim');
  if (oUt) oUt.onchange = function () { hsUngTim = oUt.value.trim(); go(scrHoSoTTTao, true); };
  hsNoiNutTaoNcc(hsUngTim, function (ma) {
    /* Tao xong thi nap lai danh sach, khong thi nguoi vua tao khong co
       trong `hsTaoDsUng` da cache va chip moi khong hien ra. */
    hsTaoDsUng = null;
    if (ma) { hsTaoNguoiUng = ma; hsUngTim = ''; }
    go(scrHoSoTTTao, true);
  });
  b.addEventListener('click', function (e) {
    var r = e.target.closest('[data-hsh]'); if (!r) return;
    var ma = r.getAttribute('data-hsh');
    if (hsTaoChon[ma]) delete hsTaoChon[ma];
    else {
      var d = rows.filter(function (x) { return x.hoa_don === ma; })[0];
      if (d) ghiChon(d);
    }
    go(scrHoSoTTTao, true);
  });
  var g1 = document.getElementById('hsChonHet');
  if (g1) g1.onclick = function () { rows.forEach(ghiChon); go(scrHoSoTTTao, true); };
  var g2 = document.getElementById('hsChonQH');
  if (g2) g2.onclick = function () { hsTaoChon = {}; rows.forEach(function (r) { if (r.tre_ngay > 0) ghiChon(r); }); go(scrHoSoTTTao, true); };
  var g3 = document.getElementById('hsBoChon');
  if (g3) g3.onclick = function () { hsTaoChon = {}; go(scrHoSoTTTao, true); };

  var luu = async function (guiLuon) {
    var gc = document.getElementById('hsGc');
    hsTaoGhiChu = gc ? gc.value : '';
    var ds = Object.keys(hsTaoChon);
    if (!ds.length) return baoTin('Chưa chọn hoá đơn nào.');
    if (laHU && !hsTaoNguoiUng) return baoTin('Chưa chọn người được hoàn ứng. Đây là người sẽ nhận lại tiền.');
    busy(true);
    try {
      var kq = await api('vagabond.ho_so_tt.tao', {
        /* Ho so hoan ung khong gui ncc len: nha cung cap cua tung dong do
           may tu doc ra tu hoa don, con o nay chi la bo loc cua man hinh. */
        ncc: laHU ? '' : hsTaoNcc,
        nguoi_ung: laHU ? hsTaoNguoiUng : '',
        hoa_don: JSON.stringify(ds), ghi_chu: hsTaoGhiChu,
        gui_luon: guiLuon ? 1 : 0, loai: hsTaoLoai
      });
      busy(false);
      hsTaoChon = {}; hsTaoGhiChu = ''; hsTaoNguoiUng = '';
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
/* Luong 4: chi thang tu TK cong ty. Dung chung man go khoan chi voi hoan
   ung, khac o cho co them tai khoan chi, loai chi phi thue va TK No. */
var huMode = 'hu', huTkChi = '', huCpThue = '', huTkTim = '';
var huChonHd = {}, huLoaiCt = '', huTep = [];
/* Goi y noi dung chi hay gap, lay tu thong ke chi phi that cua tiem. Van go
   tay duoc: danh sach chi de bam cho nhanh, khong phai de ep. */
var HU_GOI_ND = ['Tiền nước', 'Tiền điện', 'Tiền thuê nhà', 'Tiền hoàn ứng', 'Đóng BHXH', 'Đóng KPCĐ (Liên đoàn lao động)'];
var HU_CHUNG_TU = ['Bảng báo giá', 'Hợp đồng mua bán hàng hóa giữa hai bên', 'Hóa đơn giá trị gia tăng đầu vào',
  'Chứng từ thanh toán cho người bán', 'Phiếu chi', 'Ủy nhiệm chi đã chi tiền',
  'Phiếu nhập kho vật liệu, hàng hóa', 'Phiếu xuất kho của bên bán hàng',
  'Biên bản bàn giao hàng hóa', 'Biên bản thanh lý hợp đồng', 'Biên bản nghiệm thu'];
function huManHienTai() { return huMode === 'tkct' ? scrChiCongTyTao : scrHoanUngTao; }

/* KHONG THAY TEN THI PHAI TAO DUOC NGAY TAI CHO
   -------------------------------------------------
   Anh Viet 21/08/2026: chi Dung lap phieu dong BHXH, go "BHXH CO SO TAN
   DINH" roi "bao hiem xa hoi" deu khong ra gi, va man hinh khong co duong
   nao tao moi. Ca tiem co 520 nha cung cap ma khong co ben bao hiem nao.
   Bi ket o do thi chi khong lam duoc viec, ma cung khong biet phai di dau.

   Nen moi cho chon nha cung cap deu phai co ba thu: o go tim, cau noi ro
   la khong tim thay, va nut tao moi mang san chu vua go sang man tao. */
function hsKhungTimNcc(idO, tuKhoa, soThay, moTaTao) {
  return '<input class="tin" id="' + idO + '" placeholder="Gõ tên để tìm nhà cung cấp" value="' +
    h(tuKhoa || '') + '" style="margin-top:9px">' +
    ((tuKhoa && !soThay)
      ? '<div style="font-size:12.5px;color:#b45309;margin-top:8px;line-height:1.55">Không có nhà cung cấp nào tên giống "' +
        h(tuKhoa) + '". Bấm nút dưới để lập hồ sơ mới, máy điền sẵn cái tên vừa gõ.</div>'
      : '') +
    '<div style="margin-top:9px;padding-top:9px;border-top:1px dashed #e5e7eb">' +
    '<button class="btn gh" id="hsTaoNccMoi" style="margin:0">➕ Không thấy tên? Tạo nhà cung cấp mới</button>' +
    (moTaTao ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:6px;line-height:1.5">' + h(moTaTao) + '</div>' : '') +
    '</div>';
}

function hsNoiNutTaoNcc(tuKhoa, chon) {
  var n = document.getElementById('hsTaoNccMoi');
  if (!n) return;
  n.onclick = function () { nccTaoNhanh(tuKhoa, chon); };
}

async function hsChonLoaiMoi() {
  var c = await hoiChon('Lập hồ sơ thanh toán', 'Năm luồng khác nhau về chứng từ lẫn về tiền, chọn đúng loại thì các bước sau tự bày ra cho hợp.', [
    { k: 'ncc', icon: '🏭', nhan: 'Công nợ nhà cung cấp',
      mo_ta: 'Gom hoá đơn mua đến hạn của một nhà cung cấp, công ty trả thẳng cho họ từ tài khoản MB.' },
    /* Luong thu nam, anh Viet giao 21/08/2026. Dat ngay duoi Cong no NCC vi
       hai cai cung la tra tien cho nha cung cap, khac o cho da co hoa don
       hay chua. Than luong nam trong 30-tra-truoc.js. */
    { k: 'tt', icon: '⏩', nhan: 'Tạo phiếu thanh toán trước cho NCC',
      mo_ta: 'Trả trước khi chưa có hoá đơn: đơn in ấn, đơn đặt sản xuất có điều khoản cọc. Neo vào đơn mua hàng, hoá đơn về thì tự cấn trừ.' },
    { k: 'hu_hd', icon: '🧾', nhan: 'Hoàn ứng có hoá đơn',
      mo_ta: 'Uyên đã ứng tiền OCB mua hàng có hoá đơn, hàng đã nhập kho. Chọn nhiều hoá đơn gom chung một hồ sơ để hoàn lại tiền.' },
    { k: 'hu_khd', icon: '🧮', nhan: 'Hoàn ứng không hoá đơn',
      mo_ta: 'Khoản lẻ không có hoá đơn: hàng test, hàng phát sinh, chi phí bảo trì. Gõ tay từng khoản, gắn với giao dịch OCB.' },
    { k: 'tkct', icon: '🏦', nhan: 'Thanh toán từ TK công ty',
      mo_ta: 'Chi trả trực tiếp từ tài khoản công ty cho chi phí phát sinh, không qua Purchasing. Kế toán chủ động định khoản.' }
  ]);
  if (!c) return;
  if (c === 'tt') { ttReset(); return go(scrTraTruocTao); }
  if (c === 'tkct') { huDong = []; huGhiChu = ''; huTkChi = ''; huCpThue = ''; huChonHd = {}; huLoaiCt = ''; huTep = []; return go(scrChiCongTyTao); }
  if (c === 'hu_khd') { huDong = []; huGhiChu = ''; huTamUng = 0; return go(scrHoanUngTao); }
  if (c === 'hu_hd') { hsTaoNcc = ''; hsTaoChon = {}; hsTaoNguoiUng = ''; hsTaoDsUng = null; hsTaoLoai = 'Hoan ung HD'; return go(scrHoSoTTTao); }
  hsTaoNcc = ''; hsTaoChon = {}; hsTaoLoai = 'NCC';
  go(scrHoSoTTTao);
}

function huTong() { return huDong.reduce(function (a, x) { return a + Number(x.so_tien || 0); }, 0); }

async function scrHoanUngTao() {
  hsoBuoc = 0;
  huMode = 'hu';
  frame('Lập hồ sơ hoàn ứng', '<div class="emp"><div class="e1">⏳</div><div>Đang tải danh sách...</div></div>');
  var dsn;
  try { dsn = await api('vagabond.ho_so_tt.ds_nguoi_ung', huTim ? { tu_khoa: huTim } : {}); }
  catch (e) { frame('Lập hồ sơ hoàn ứng', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var ncc = dsn.ncc || [];
  if (!huNguoi && ncc.length) huNguoi = ncc[0].ncc;

  var html = '<div class="card" style="padding:12px 14px;font-size:13px;line-height:1.6;color:#374151">' +
    'Gõ từng khoản đã chi hộ bằng tiền tạm ứng: hàng test không nhập kho, hàng phát sinh, chi phí bảo trì... ' +
    'Nhiều nhà cung cấp nhỏ lẻ gộp chung một hồ sơ được, vì tiền là hoàn lại cho <b>một</b> người.<br>' +
    'Máy chỉ giữ những gì mình gõ. Đến bước <b>giám đốc duyệt</b> mới sinh hoá đơn mua thật, nên hồ sơ bị từ chối giữa chừng không để lại rác trên sổ.</div>';

  var hay = ncc.filter(function (x) { return x.hay_dung; });
  var khac = ncc.filter(function (x) { return !x.hay_dung; });
  html += hsoKhoi('Hoàn ứng cho ai') + '<div class="card" style="padding:10px 12px">' +
    kmHangChip((hay.concat(khac.slice(0, 24))).map(function (x) {
      return posChipNut('data-hun="' + h(x.ncc) + '"', (x.hay_dung ? '⭐ ' : '') + h(x.ten), huNguoi === x.ncc);
    }).join('')) +
    hsKhungTimNcc('huTim', huTim, (hay.concat(khac)).length,
      'Người nhận tiền nào cũng phải có hồ sơ nhà cung cấp thì máy mới ghi sổ và theo dõi công nợ được.') +
    '</div>';

  html += '<div class="card" style="padding:12px 14px;background:#fffbeb;border:1.5px solid #fde68a">' +
    '<div style="font-size:11.5px;color:#92400e;font-weight:800">ĐANG LẬP</div>' +
    '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:5px">' +
    '<span style="font-size:13.5px;color:#374151">' + huDong.length + ' khoản</span>' +
    '<b style="font-size:20px;color:#92400e">' + money(huTong()) + ' đ</b></div>' +
    (Number(huTamUng) > 0
      ? '<div style="display:flex;justify-content:space-between;font-size:12.5px;color:#6b7280;margin-top:3px"><span>Trừ đã tạm ứng</span><b>' + money(huTamUng) + ' đ</b></div>' +
        '<div style="display:flex;justify-content:space-between;font-size:13px;color:#92400e;margin-top:2px"><span><b>Còn lại phải chuyển</b></span><b>' + money(huTong() - Number(huTamUng)) + ' đ</b></div>'
      : '') +
    '</div>';

  /* Bay dang BANG dung nam cot anh Viet chot 13/08/2026: So TT, Ngay mua
     hang, Noi dung, So tien, Ma giao dich. Cuon ngang tren dien thoai chu
     khong bo cot nao - thieu cot ma giao dich la mat duong doi chieu voi
     sao ke OCB. */
  html += hsoKhoi('Các khoản đã chi · bấm một dòng để sửa hoặc xoá')
    + '<div class="card" style="padding:0;overflow-x:auto">'
    + '<table style="width:100%;border-collapse:collapse;font-size:12.5px;min-width:560px">'
    + '<tr style="background:#f8fafc;color:#6b7280;font-size:11.5px;text-align:left">'
    + '<th style="padding:8px 10px;font-weight:700">STT</th>'
    + '<th style="padding:8px 10px;font-weight:700">Ngày mua</th>'
    + '<th style="padding:8px 10px;font-weight:700">Nội dung</th>'
    + '<th style="padding:8px 10px;font-weight:700;text-align:right">Số tiền</th>'
    + '<th style="padding:8px 10px;font-weight:700">Mã giao dịch</th></tr>';
  if (!huDong.length) {
    html += '<tr><td colspan="5" style="padding:24px;text-align:center;color:#6b7280">Chưa có khoản nào. Bấm <b>➕ Thêm khoản chi</b> ở dưới.</td></tr>';
  }
  huDong.forEach(function (x, i) {
    html += '<tr data-hux="' + i + '" style="border-top:1px solid #eef2f5;cursor:pointer">'
      + '<td style="padding:9px 10px;color:#6b7280">' + (i + 1) + '</td>'
      + '<td style="padding:9px 10px;white-space:nowrap">' + (hsNgayVn(x.ngay_hd) || '-') + '</td>'
      + '<td style="padding:9px 10px">' + h(x.noi_dung || '(chưa ghi)')
      + (x.so_hd_ncc ? '<br><span style="color:#6b7280;font-size:11.5px">HĐ ' + h(x.so_hd_ncc) + '</span>' : '')
      + (x.ben_ban ? '<br><span style="color:#6b7280;font-size:11.5px">' + h(x.ben_ban) + '</span>' : '')
      + '<br><span style="font-size:11.5px;color:' + (x.co_vat ? '#0e7490' : '#92400e') + '">'
      + (x.co_vat ? '🧾 có hoá đơn VAT' : '📄 không hoá đơn') + (x.loai_chi ? ' · ' + h(x.loai_chi) : '') + '</span></td>'
      + '<td style="padding:9px 10px;text-align:right;white-space:nowrap;font-weight:700">' + money(x.so_tien) + '</td>'
      + '<td style="padding:9px 10px;white-space:nowrap;font-size:11.5px;color:' + (x.ma_giao_dich ? '#0e7490' : '#b45309') + '">'
      + (x.ma_giao_dich ? h(x.ma_giao_dich) : '⚠️ chưa gắn') + '</td></tr>';
  });
  html += '</table></div>';

  html += '<div style="display:flex;gap:8px;margin-bottom:10px">' +
    '<button class="btn gh" id="huSepay" style="flex:2;margin:0">🏦 Lấy từ sao kê OCB</button>' +
    '<button class="btn gh" id="huThem" style="flex:1;margin:0">➕ Gõ tay</button>' +
    '<button class="btn gh" id="huUng" style="flex:1;margin:0">➖ Trừ ứng</button></div>';

  html += '<div class="card" style="padding:12px 14px"><input class="tin" id="huGc" placeholder="Ghi chú cho hồ sơ (không bắt buộc)" value="' + h(huGhiChu) + '"></div>';

  var foot = '<div style="display:flex;gap:8px">' +
    '<button class="btn" id="huLuu" style="flex:2">📤 Lập và gửi kế toán</button>' +
    '<button class="btn gh" id="huNhap" style="flex:1">💾 Lưu nháp</button></div>';
  var b = frame('Lập hồ sơ hoàn ứng', html, { footer: foot });

  Array.prototype.forEach.call(document.querySelectorAll('[data-hun]'), function (el) {
    el.onclick = function () { huNguoi = el.getAttribute('data-hun'); go(scrHoanUngTao, true); };
  });
  var ot = document.getElementById('huTim');
  if (ot) ot.onchange = function () { huTim = ot.value.trim(); go(scrHoanUngTao, true); };
  hsNoiNutTaoNcc(huTim, function (ma) {
    if (ma) { huNguoi = ma; huTim = ''; }
    go(scrHoanUngTao, true);
  });
  b.addEventListener('click', function (e) {
    var r = e.target.closest('[data-hux]'); if (!r) return;
    huSuaDong(+r.getAttribute('data-hux'));
  });
  document.getElementById('huThem').onclick = function () { huSuaDong(-1); };
  document.getElementById('huSepay').onclick = function () { huLaySepay(); };
  document.getElementById('huUng').onclick = async function () {
    var v = await hoiNhap('Đã tạm ứng trước bao nhiêu đồng? (gõ 0 nếu không có)', String(huTamUng || 0));
    if (v === null) return;
    huTamUng = Math.max(0, Number(String(v).replace(/[^0-9]/g, '')) || 0);
    go(scrHoanUngTao, true);
  };

  var luu = async function (guiLuon) {
    var gc = document.getElementById('huGc');
    huGhiChu = gc ? gc.value : '';
    if (!huNguoi) return baoTin('Chưa chọn người được hoàn ứng.');
    if (!huDong.length) return baoTin('Chưa nhập khoản chi nào.');
    if (Number(huTamUng) > huTong()) return baoTin('Số đã tạm ứng lớn hơn tổng hồ sơ, xem lại giúp em.');
    busy(true);
    try {
      var kq = await api('vagabond.ho_so_tt.tao_hoan_ung', {
        nguoi_ung: huNguoi, dong: JSON.stringify(huDong), ghi_chu: huGhiChu,
        da_tam_ung: huTamUng || 0, gui_luon: guiLuon ? 1 : 0
      });
      busy(false);
      huDong = []; huGhiChu = ''; huTamUng = 0;
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

async function huLaySepay() {
  busy(true);
  var kq;
  try { kq = await api('vagabond.ho_so_tt.sepay_ocb', { so_ngay: 60 }); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Không đọc được sao kê', 'Sao kê OCB'); }
  busy(false);
  if (kq.loi) return baoTin(kq.loi, 'Sao kê OCB');
  if (!(kq.rows || []).length) return baoTin('Không còn giao dịch chi nào từ quỹ OCB trong 60 ngày mà chưa nằm trong hồ sơ nào.', 'Sao kê OCB');
  huGdChon = {};
  go(function () { scrHuSepay(kq); });
}

async function scrHuSepay(kq) {
  var rows = kq.rows || [];
  var chon = rows.filter(function (r) { return huGdChon[r.ma_giao_dich]; });
  var tong = chon.reduce(function (a, r) { return a + Number(r.so_tien || 0); }, 0);

  var html = '<div class="card" style="padding:12px 14px;font-size:13px;line-height:1.6;color:#374151">'
    + 'Đây là các khoản <b>đã chi ra</b> từ quỹ tạm ứng OCB mà chưa nằm trong hồ sơ nào. '
    + 'Tick khoản nào thì máy lấy sẵn ngày, số tiền và mã giao dịch, mình chỉ cần bổ sung nội dung và số hoá đơn nếu có.</div>';

  html += '<div class="card" style="padding:12px 14px;background:#fffbeb;border:1.5px solid #fde68a">'
    + '<div style="font-size:11.5px;color:#92400e;font-weight:800">ĐANG CHỌN</div>'
    + '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:5px">'
    + '<span style="font-size:13.5px;color:#374151">' + chon.length + ' / ' + rows.length + ' giao dịch</span>'
    + '<b style="font-size:20px;color:#92400e">' + money(tong) + ' đ</b></div></div>';

  html += '<div class="sec">Giao dịch chi ra từ quỹ OCB · bấm để chọn</div><div class="card">';
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
  var b = frame('Sao kê quỹ OCB', html, { footer: foot });

  b.addEventListener('click', function (e) {
    var r = e.target.closest('[data-hugd]'); if (!r) return;
    var ma = r.getAttribute('data-hugd');
    if (huGdChon[ma]) delete huGdChon[ma]; else huGdChon[ma] = 1;
    go(function () { scrHuSepay(kq); }, true);
  });
  document.getElementById('huGdVe').onclick = function () { go(scrHoanUngTao); };
  document.getElementById('huGdXong').onclick = function () {
    var them = rows.filter(function (r) { return huGdChon[r.ma_giao_dich]; });
    if (!them.length) return baoTin('Chưa tick giao dịch nào.', 'Sao kê OCB');
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
async function huSuaDong(i) {
  var x = i >= 0 ? huDong[i] : { ngay_hd: '', so_hd_ncc: '', noi_dung: '', ben_ban: '', loai_chi: '', co_vat: 0, so_tien: 0, tk_no: '', ma_giao_dich: '', ghi_chu: '' };
  if (i >= 0) {
    var lam = await hoiChon(x.noi_dung || 'Khoản chi', money(x.so_tien) + ' đ', [
      { k: 'sua', icon: '✏️', nhan: 'Sửa khoản này' },
      { k: 'xoa', icon: '🗑', nhan: 'Xoá khỏi hồ sơ' }
    ]);
    if (!lam) return;
    if (lam === 'xoa') {
      if (!await hoiCo('Xoá khoản chi', 'Xoá "' + (x.noi_dung || '') + '" khỏi hồ sơ?', 'Xoá', true)) return;
      huDong.splice(i, 1);
      return go(huManHienTai(), true);
    }
  }
  var nd = x.noi_dung || '';
  if (huMode === 'tkct') {
    var gy = await hoiChon('Nội dung chi', 'Chọn khoản hay gặp cho nhanh, hoặc bấm Gõ tay nếu không có trong danh sách.',
      HU_GOI_ND.map(function (t) { return { k: t, icon: '•', nhan: t }; })
        .concat([{ k: '__go__', icon: '✍️', nhan: 'Gõ tay nội dung khác' }]), nd || '');
    if (gy === null) return;
    if (gy && gy !== '__go__') nd = gy;
    else {
      nd = await hoiNhap('Nội dung chi (mua gì, sửa gì):', nd);
      if (nd === null) return;
    }
  } else {
    nd = await hoiNhap('Nội dung chi (mua gì, sửa gì):', nd);
    if (nd === null) return;
  }
  nd = String(nd || '').trim();
  if (!nd) return baoTin('Phải ghi nội dung chi.');

  var st = await hoiNhap('Số tiền (đồng):', x.so_tien ? String(x.so_tien) : '');
  if (st === null) return;
  st = Number(String(st).replace(/[^0-9]/g, '')) || 0;
  if (st <= 0) return baoTin('Số tiền phải lớn hơn 0.');

  var ng = await hoiNhap('Ngày hoá đơn (dd/mm/yyyy, bỏ trống là hôm nay):', x.ngay_hd ? hsNgayVn(x.ngay_hd) : '');
  if (ng === null) return;
  var ngIso = '';
  ng = String(ng).trim();
  if (ng) {
    var pp = ng.split(/[\/\-\.]/);
    if (pp.length === 3) {
      var dd = pp[0], mm = pp[1], yy = pp[2];
      if (dd.length === 4) { ngIso = dd + '-' + ('0' + mm).slice(-2) + '-' + ('0' + yy).slice(-2); }
      else { if (yy.length === 2) yy = '20' + yy; ngIso = yy + '-' + ('0' + mm).slice(-2) + '-' + ('0' + dd).slice(-2); }
    } else return baoTin('Ngày gõ chưa đúng dạng ngày/tháng/năm.');
  }

  var sh = await hoiNhap('Số hoá đơn (bỏ trống nếu không có hoá đơn):', x.so_hd_ncc || '');
  if (sh === null) return;
  var bb = await hoiNhap('Mua của ai / bên bán (bỏ trống cũng được):', x.ben_ban || '');
  if (bb === null) return;
  var lc = await hoiChon('Loại chi', 'Khoản này thuộc nhóm nào?', [
    { k: 'Hang hoa', icon: '📦', nhan: 'Hàng hoá' },
    { k: 'Hang test', icon: '🧪', nhan: 'Hàng test', mo_ta: 'Mua thử, không nhập kho' },
    { k: 'Hang phat sinh', icon: '➕', nhan: 'Hàng phát sinh' },
    { k: 'Chi phi', icon: '🔧', nhan: 'Chi phí', mo_ta: 'Bảo trì, sửa chữa, dịch vụ' },
    { k: 'Khac', icon: '❓', nhan: 'Khác' }
  ], x.loai_chi || 'Hang hoa');
  if (lc === null) return;

  var vatK = await hoiChon('Hoá đơn VAT', 'Khoản này có hoá đơn VAT đỏ không? Việc này quyết định mã món khi máy lập hoá đơn mua.', [
    { k: 'co', icon: '🧾', nhan: 'Có hoá đơn VAT', mo_ta: 'Máy lập hoá đơn riêng theo số hoá đơn để còn kê khai thuế' },
    { k: 'khong', icon: '📄', nhan: 'Không có hoá đơn', mo_ta: 'Gom chung vào một hoá đơn mua cho gọn sổ' }
  ], 'co');
  if (vatK === null) return;
  var vat = vatK === 'co';

  var tkNo = x.tk_no || '';
  if (huMode === 'tkct') {
    tkNo = await huChonTaiKhoan('Tài khoản Nợ cho khoản "' + nd + '"', tkNo);
    if (tkNo === null) return;
    if (!tkNo) return baoTin('Khoản chi phải có tài khoản Nợ thì mới hạch toán được.');
  }

  var moi = {
    ngay_hd: ngIso, so_hd_ncc: String(sh || '').trim(), noi_dung: nd,
    ben_ban: String(bb || '').trim(), loai_chi: lc || '',
    co_vat: vat ? 1 : 0, so_tien: st, tk_no: tkNo,
    ma_giao_dich: x.ma_giao_dich || '', ghi_chu: x.ghi_chu || ''
  };
  if (i >= 0) huDong[i] = moi; else huDong.push(moi);
  go(huManHienTai(), true);
}


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
      '⚠️ Chưa có tài khoản ngân hàng nào của công ty gắn tài khoản sổ cái. Mở Bank Account bên Next điền ô Account giúp em.</div>';
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
    html += '<div class="emp" style="padding:26px 14px"><div class="e1">👆</div><div>Chọn loại chi phí thuế để em bày tiếp phần nhập liệu.</div></div>';
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
    kmHangChip(ncc.slice(0, 40).map(function (x) {
      var ten = x.ten || x.ncc;
      return posChipNut('data-hun="' + h(x.ncc) + '"', (x.hay_dung ? '⭐ ' : '') + h(ten) + (hopLe && x.con_no ? ' · ' + money(x.con_no) : ''), huNguoi === x.ncc);
    }).join('')) +
    (hopLe ? '' : hsKhungTimNcc('huTim', huTim, ncc.length,
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
    html += hsoKhoi('Các khoản chi · bấm một dòng để sửa hoặc xoá')
      + '<div class="card" style="padding:0;overflow-x:auto">'
      + '<table style="width:100%;border-collapse:collapse;font-size:12.5px;min-width:560px">'
      + '<tr style="background:#f8fafc;color:#6b7280;font-size:11.5px;text-align:left">'
      + '<th style="padding:8px 10px;font-weight:700">STT</th>'
      + '<th style="padding:8px 10px;font-weight:700">Ngày</th>'
      + '<th style="padding:8px 10px;font-weight:700">Nội dung</th>'
      + '<th style="padding:8px 10px;font-weight:700">TK Nợ</th>'
      + '<th style="padding:8px 10px;font-weight:700;text-align:right">Số tiền</th></tr>';
    if (!huDong.length) {
      html += '<tr><td colspan="5" style="padding:24px;text-align:center;color:#6b7280">Chưa có khoản nào. Bấm <b>➕ Thêm khoản chi</b> ở dưới.</td></tr>';
    }
    huDong.forEach(function (x, i) {
      html += '<tr data-hux="' + i + '" style="border-top:1px solid #eef2f5;cursor:pointer">'
        + '<td style="padding:9px 10px;color:#6b7280">' + (i + 1) + '</td>'
        + '<td style="padding:9px 10px;white-space:nowrap">' + (hsNgayVn(x.ngay_hd) || '-') + '</td>'
        + '<td style="padding:9px 10px">' + h(x.noi_dung || '(chưa ghi)')
        + (x.ben_ban ? '<br><span style="color:#6b7280;font-size:11.5px">' + h(x.ben_ban) + '</span>' : '') + '</td>'
        + '<td style="padding:9px 10px;white-space:nowrap;font-size:11.5px;color:' + (x.tk_no ? '#0e7490' : '#b45309') + '">'
        + (x.tk_no ? h(x.tk_no) : '⚠️ chưa chọn') + '</td>'
        + '<td style="padding:9px 10px;text-align:right;white-space:nowrap;font-weight:700">' + money(x.so_tien) + '</td></tr>';
    });
    html += '</table></div>';
    html += '<div style="display:flex;gap:8px;margin-bottom:10px">' +
      '<button class="btn gh" id="huThem" style="flex:1;margin:0">➕ Thêm khoản chi</button></div>';

    /* Khong co hoa don he thong thi ho so chi con dua vao chung tu roi: phai
       noi ro chung tu gi, roi moi cho dinh kem dung loai do. */
    html += hsoKhoi('Chứng từ đính kèm · bắt buộc') + '<div class="card" style="padding:10px 12px">' +
      kmHangChip(HU_CHUNG_TU.map(function (x) {
        return posChipNut('data-huct="' + h(x) + '"', h(x), huLoaiCt === x);
      }).join(''));
    if (!huLoaiCt) {
      html += '<div style="font-size:12.5px;color:#b45309;margin-top:8px">Chọn loại chứng từ trước, em mới bày nút đính kèm.</div>';
    } else {
      html += '<div style="margin-top:9px">';
      huTep.forEach(function (t, i) {
        html += '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;padding:6px 0;border-top:1px solid #f1f5f9">' +
          '<span style="flex:1 1 auto;min-width:0;font-size:12.5px;color:#0f766e;overflow-wrap:anywhere">📎 ' + h(t.ten) + '</span>' +
          '<button class="btn gh" data-hutx="' + i + '" style="flex:0 0 auto;width:auto;margin:0;padding:4px 9px;font-size:12px">Bỏ</button></div>';
      });
      html += '<button class="btn gh" id="huGanTep" style="margin-top:9px">➕ Đính kèm ' + h(huLoaiCt) + '</button></div>';
    }
    html += '</div>';
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
  Array.prototype.forEach.call(document.querySelectorAll('[data-huct]'), function (el) {
    el.onclick = function () { huLoaiCt = el.getAttribute('data-huct'); go(scrChiCongTyTao, true); };
  });
  var ot = document.getElementById('huTim');
  if (ot) ot.onchange = function () { huTim = ot.value.trim(); go(scrChiCongTyTao, true); };
  hsNoiNutTaoNcc(huTim, function (ma) {
    if (ma) { huNguoi = ma; huTim = ''; }
    go(scrChiCongTyTao, true);
  });
  b.addEventListener('click', function (e) {
    var r1 = e.target.closest('[data-hux]');
    if (r1) return huSuaDong(+r1.getAttribute('data-hux'));
    var r2 = e.target.closest('[data-huhd]');
    if (r2) {
      var ma = r2.getAttribute('data-huhd');
      if (huChonHd[ma]) delete huChonHd[ma]; else huChonHd[ma] = 1;
      return go(scrChiCongTyTao, true);
    }
    var r3 = e.target.closest('[data-hutx]');
    if (r3) { huTep.splice(+r3.getAttribute('data-hutx'), 1); return go(scrChiCongTyTao, true); }
  });
  var nt = document.getElementById('huThem');
  if (nt) nt.onclick = function () { huSuaDong(-1); };
  var ng = document.getElementById('huGanTep');
  if (ng) ng.onclick = async function () {
    var f = await huChonTep();
    if (!f) return;
    busy(true);
    try { huTep.push(await huUpTep(f)); busy(false); go(scrChiCongTyTao, true); }
    catch (e) { busy(false); baoTin((e && e.message) || 'Không tải được tệp'); }
  };

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
        if (!huLoaiCt) { busy(false); return baoTin('Chưa chọn loại chứng từ đính kèm.'); }
        if (!huTep.length) { busy(false); return baoTin('Chưa đính kèm chứng từ nào. Khoản không hoá đơn thì bắt buộc phải có chứng từ.'); }
        kq = await api('vagabond.ho_so_tt.tao_chi_cong_ty', {
          ncc: huNguoi, tk_chi: huTkChi, loai_cp_thue: huCpThue,
          dong: JSON.stringify(huDong), ghi_chu: huGhiChu, gui_luon: guiLuon ? 1 : 0,
          loai_chung_tu: huLoaiCt, tep: JSON.stringify(huTep)
        });
      }
      busy(false);
      huDong = []; huGhiChu = ''; huChonHd = {}; huTep = []; huLoaiCt = '';
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
  var chepTay = function () { hoiChu('Copy tay giúp em', 'Chạm giữ rồi chọn Copy:', chu, { nhieu_dong: true }); };
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
    ((Q.lap || Q.fin) && hs.trang_thai !== 'Da thanh toan' ? '<button class="btn gh" data-hsv="suatk" style="flex:1;margin:0">✏️ Sửa TK</button>' : '') +
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
        ct += '<div><b>Bản scan · ' + x.scan.length + ' tệp</b>'
          + '<div style="display:flex;flex-wrap:wrap;gap:7px;margin-top:6px">'
          + x.scan.map(function (f) {
            var laAnh = /\.(jpe?g|png|gif|bmp|webp)$/i.test(f.ten || '');
            return laAnh
              ? '<div data-scan="' + h(f.url) + '" style="width:66px;height:66px;border-radius:9px;overflow:hidden;border:1px solid #e3e6ec;background:#f5f6f8;cursor:pointer">'
                + '<img src="' + h(f.url) + '" loading="lazy" style="width:100%;height:100%;object-fit:cover;display:block"></div>'
              : '<a href="' + h(f.url) + '" target="_blank" rel="noopener" style="display:flex;align-items:center;justify-content:center;width:66px;height:66px;border-radius:9px;border:1px solid #e3e6ec;background:#f8fafc;color:#0e7490;font-size:11px;text-align:center;padding:4px;line-height:1.3">📄 '
                + h((f.ten || '').slice(-12)) + '</a>';
          }).join('')
          + '</div></div>';
      }
      if (!ct) ct = '<span style="color:#6b7280">Chưa có chứng từ nào đính kèm hoá đơn này.</span>';
      html += '<div style="padding:10px 14px 12px 56px;font-size:12.5px;line-height:1.7;color:#374151;background:#f8fafc;border-top:1px solid #eef2f5">' + ct + '</div>';
    }
  });
  html += '</div>';

  /* Tep dinh thang vao ho so: ban the hien hoa don, bang ke, giay to kem.
     Nut tai len nam ngay day chu khong bat mo Desk (anh Viet 21/08/2026).
     Duong keo PDF tu API M-Invoice da bo: no tra 400 o moi bien the ten tep,
     ma ke toan truong thi van can to hoa don de duyet ngay hom nay. */
  html += '<div class="sec">Tệp đính kèm thẳng vào hồ sơ</div><div class="card" style="padding:12px 14px">';
  if ((d.ho_so_dinh_kem || []).length) {
    html += '<div style="font-size:13px;line-height:1.9">' +
      d.ho_so_dinh_kem.map(function (f) {
        return '<div style="display:flex;gap:8px;align-items:center">' +
          '<a href="' + h(f.url) + '" target="_blank" rel="noopener" style="color:#0e7490;flex:1;min-width:0;word-break:break-all">📎 ' + h(f.ten) + '</a>' +
          '<button data-hsgotep="' + h(f.file || '') + '" style="flex:none;border:1px solid #e5e7eb;background:#fff;color:#98a2b3;' +
          'border-radius:8px;padding:3px 9px;font-size:12px">Gỡ</button></div>';
      }).join('') + '</div>';
  } else {
    html += '<div style="font-size:12.5px;color:#6b7280;line-height:1.6">Chưa có tệp nào. ' +
      'Kế toán trưởng cần nhìn <b>bản thể hiện hoá đơn</b> mới duyệt được, nên tải từ M-Invoice về rồi đính lên đây.</div>';
  }
  html += '<button class="btn gh" id="hsThemTep" style="margin:10px 0 0;width:100%">📄 Tải bản thể hiện hoá đơn lên</button>' +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px;line-height:1.5">Nhận ảnh chụp hoặc tệp PDF. Tệp để riêng tư: chỉ người xem được hồ sơ mới mở được.</div></div>';

  html += '<div style="display:flex;gap:8px;margin-bottom:10px">' +
    '<button class="btn gh" data-hsv="xuatbo" style="flex:1;margin:0">📦 Xuất bộ hồ sơ</button>' +
    '<button class="btn gh" data-hsv="xemto" style="flex:1;margin:0">👁 Xem tờ đề nghị</button></div>';

  /* Thu bao chi danh cho ho so cong no nha cung cap. Ho so hoan ung thi
     nha cung cap da duoc tra tien tu luc mua, gui thu "chung toi da thanh
     toan" cho ho la bao mot viec khong xay ra. May chu cung chan. */
  if (hs.trang_thai === 'Da thanh toan' && !laHU) {
    html += '<div class="sec">Thư báo nhà cung cấp</div><div class="card" style="padding:12px 14px;font-size:13px;line-height:1.6;color:#374151">' +
      (hs.email_da_gui
        ? '✉️ Đã gửi tới <b>' + h(hs.email_gui_toi) + '</b>' + (hs.email_gui_luc ? ' lúc ' + h(hs.email_gui_luc) : '') + '.<br>Gửi lại được nếu nhà cung cấp báo chưa nhận.'
        : 'Chưa gửi thư báo. Email đang lưu trên hồ sơ nhà cung cấp: <b>' + h(hs.email_ncc || '(chưa có)') + '</b>') +
      '<div style="display:flex;gap:8px;margin-top:10px">' +
      '<button class="btn gh" data-hsv="xemthu" style="flex:1;margin:0">👁 Xem trước thư</button>' +
      '<button class="btn" data-hsv="guithu" style="flex:1;margin:0">✉️ ' + (hs.email_da_gui ? 'Gửi lại' : 'Gửi thư báo') + '</button></div></div>';
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

  var nTep = document.getElementById('hsThemTep');
  if (nTep) nTep.onclick = function () { hsDinhTep(hs); };
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

/* Tai ban the hien hoa don len ho so.

   Duong nay thay cho viec keo PDF tu API M-Invoice: da do ba bien the ten
   tep ngay 20-21/08/2026, ca ba deu tra 400, ma tai lieu API cong khai cua
   ho khong noi dinh dang dung. Nguoi lap ho so mo M-Invoice bam tai ve roi
   dinh len day - mot thao tac chac chan, hon la mot nhip tu dong khong bao
   gio chay. */
async function hsDinhTep(hs) {
  var f = await huChonTep();
  if (!f) return;
  if (f.size > 12 * 1024 * 1024) {
    return toast('Tệp nặng quá 12 MB nên máy không nhận. Xuất lại bản PDF nhỏ hơn hoặc chụp lại giúp em.', 5500);
  }
  busy(true);
  var t;
  try { t = await huUpTep(f); }
  catch (e) { busy(false); return toast('Không tải tệp lên được: ' + ((e && e.message) || ''), 6500); }
  try {
    var r = await api('vagabond.ho_so_tt.dinh_tep', { name: hs.ma, tep: JSON.stringify([t]) });
    busy(false);
    toast((r && r.ghi_chu) || 'Đã đính tệp vào hồ sơ.', 5000);
    go(function () { scrHoSoTTView(hs.ma); }, true);
  } catch (e2) { busy(false); toast((e2 && e2.message) || 'Không đính được tệp', 6500); }
}

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
  if (k === 'suatk') {
    var t1 = await hoiNhap('Tên người thụ hưởng (đúng như trên tài khoản ngân hàng):', hs.ten_nhan || hs.ten_ncc || '');
    if (t1 === null) return;
    var t2 = await hoiNhap('Số tài khoản:', hs.stk_nhan || '');
    if (t2 === null) return;
    var t3 = await hoiNhap('Ngân hàng (viết tắt cũng được, ví dụ OCB, MB, VCB):', hs.ngan_hang_nhan || '');
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
    else baoTin('Trình duyệt chặn cửa sổ mới. Cho phép rồi bấm lại giúp em.');
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
    } catch (e) { busy(false); return baoTin((e && e.message) || 'Ghi nhận lỗi'); }
    return go(function () { scrHoSoTTView(hs.ma); }, true);
  }
  if (k === 'xemthu') {
    busy(true);
    var t;
    try { t = await api('vagabond.ho_so_tt.gui_email_ncc', { name: hs.ma, gui_that: 0 }); } catch (e) { busy(false); return baoTin((e && e.message) || 'Không dựng được thư'); }
    busy(false);
    var w = window.open('', '_blank');
    if (w) { w.document.write(t.html); w.document.close(); }
    else baoTin('Trình duyệt chặn cửa sổ mới. Cho phép rồi bấm lại giúp em.');
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



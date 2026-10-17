/* ===================================================================
   GIÁ VỐN TẠM TÍNH (Issue #482, anh Việt 16/10/2026)

   Cho kế toán giá thành (Khải) xem giá vốn nguyên liệu của từng bánh bán
   ra, cộng dồn qua từng lớp bán thành phẩm theo giá kho hôm nay, so với giá
   bán, và giá bán đề xuất theo HỆ SỐ mục tiêu của nhóm (giá bán gấp mấy lần
   giá vốn, anh Việt 16/10 tối: tiệm đọc theo "lãi số lần", phần trăm giá vốn
   chỉ hiện kèm). Bấm Chốt thì máy chủ lưu vào bảng giá riêng "Giá vốn tạm
   tính".

   Tab "Món thử (R&D)": phiếu tính giá thử cho món chưa bán. Nhập nguyên liệu
   tạm (mã có sẵn hoặc NVL mới kèm giá tay), máy chủ tính bằng đúng phép cộng
   dồn của món đang bán. Không tạo mã hàng, không tạo công thức.

   Màn chỉ ĐỌC, trừ các việc ghi đều qua máy chủ: lưu hệ số mục tiêu, chốt
   bảng giá, lưu và xoá phiếu thử. Không đụng công thức, tồn kho hay sổ sách.
   Mọi con số (giá vốn, trạng thái, giá đề xuất, quyền) do máy chủ tính; màn
   chỉ lọc và bày ra (vagabond/gia_von_tam.py).
   =================================================================== */

var GVT = { kq: null, nhom: '', tt: '', tim: '', moCct: false, tab: 'ban', thu: null, p: null, pk: null, hen: null,
  /* Codex #486: số lượt để bỏ kết quả về trễ (tính thử, tải danh sách). */
  lan: 0, lanDs: 0, thuQ: '', henQ: null,
  /* Codex #486 v7: ba hàng chip của danh sách phiếu thử (trạng thái, nhóm, khoảng ngày lập). */
  thuTt: '', thuNhom: '', thuKh: '',
  /* Codex #486 v3: câu lỗi của lần tính thử gần nhất (mẻ ra sai, máy chủ từ chối). */
  loiTinh: null };

var GVT_TT = {
  vuot_gia_ban: { nhan: 'Vượt giá bán', mau: '#b3261e', nen: '#fef2f2' },
  thieu_gia: { nhan: 'Thiếu giá NVL', mau: '#b45309', nen: '#fffbeb' },
  vong: { nhan: 'Công thức vòng', mau: '#b3261e', nen: '#fef2f2' },
  duoi_muc_tieu: { nhan: 'Dưới mục tiêu', mau: '#b45309', nen: '#fffbeb' }
};
/* Codex #483 vong 3: co ca 'vong' de loc rieng duoc mon cong thuc vong. Chip
   chi hien khi co mon o trang thai do (xem gvtVe). */
var GVT_CHIP_TT = ['vuot_gia_ban', 'vong', 'thieu_gia', 'duoi_muc_tieu'];
var GVT_TIEU_DE = 'Giá vốn tạm tính';
var GVT_TIEU_DE_THU = 'Phiếu tính giá thử';
/* Phiếu thử có nguyên liệu mà công thức trỏ vòng: giá tay không thay được
   (Codex #486 v10, v11), chỉ đường sửa công thức. MỘT câu cho thẻ và màn phiếu. */
var GVT_CAU_VONG = 'Công thức của một bán thành phẩm trong phiếu trỏ vòng vào chính nó nên chưa tính được. Sửa công thức đó trên Desk; giá tay không thay được.';

function gvtPhanTram(x) { return x == null ? '' : String(x).replace('.', ',') + '%'; }
function gvtHeSo(x) { return x == null ? '' : 'x' + String(x).replace('.', ','); }

function gvtNgay(s) {
  var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(s || ''));
  return m ? m[3] + '/' + m[2] : String(s || '');
}

/* Danh sách đang lọc. Thứ tự đã do máy chủ xếp (cần xử lên trước). */
function gvtLoc() {
  var kq = GVT.kq || {};
  return (kq.dong || []).filter(function (d) {
    if (GVT.nhom && d.nhom !== GVT.nhom) return false;
    if (GVT.tt && d.trang_thai !== GVT.tt) return false;
    return vgbKhop([d.ten, d.ma], GVT.tim);
  });
}

/* Chip trạng thái có chữ trên MỌI thẻ (Codex #483 vòng 2, AGENTS 2b điều 3):
   xanh đạt, vàng cần xem, đỏ cần xử, xám chưa đủ dữ liệu. */
var GVT_CHIP = {
  dat: ['Đạt mục tiêu', '#047857', '#ecfdf5'],
  duoi_muc_tieu: ['Dưới mục tiêu', '#b45309', '#fffbeb'],
  vuot_gia_ban: ['Vượt giá bán', '#b3261e', '#fef2f2'],
  thieu_gia: ['Thiếu giá NVL', '#b45309', '#fffbeb'],
  vong: ['Công thức vòng', '#b3261e', '#fef2f2'],
  chua_gia_ban: ['Chưa có giá bán', '#6b7280', '#f3f4f6'],
  chua_dat_muc_tieu: ['Chưa đặt mục tiêu', '#6b7280', '#f3f4f6'],
  chua_nguyen_lieu: ['Chưa có nguyên liệu', '#6b7280', '#f3f4f6']
};
function gvtChipTrangThai(d) {
  var c = GVT_CHIP[d.trang_thai] || [d.trang_thai, '#6b7280', '#f3f4f6'];
  return '<span class="gvt-c" data-gvttt="' + h(d.trang_thai) + '" style="color:' + c[1] + ';background:' + c[2] + '">' + h(c[0]) + '</span>';
}

/* Giao diện thẻ kiểu chip (anh Việt 17/10/2026: "nhìn kiểu chip ấy, hiện tại
   không đẹp như các phân hệ khác"). Một bộ lớp `gvt-*` dùng chung cho thẻ
   món đang bán, thẻ phiếu thử và ô kết quả, nạp MỘT lần. Trên điện thoại
   390px: tên và chip đứng cạnh ảnh, ba ô số trải hết bề ngang thẻ để số
   tiền bảy chữ số không bị cắt. */
function gvtCss() {
  if (typeof document === 'undefined' || !document.head || !document.createElement) return;
  if (document.getElementById && document.getElementById('gvtCss')) return;
  var st = document.createElement('style');
  st.id = 'gvtCss';
  st.textContent =
    '.gvt-the{padding:14px;border-bottom:1px solid #f0f2f6;background:#fff;cursor:pointer;-webkit-tap-highlight-color:transparent}' +
    '.gvt-the:last-child{border-bottom:0}' +
    '.gvt-the:active{background:#f8fafc}' +
    '.gvt-dau{display:flex;gap:12px;align-items:flex-start}' +
    '.gvt-dau .imm{flex:none}' +
    '.gvt-th{flex:1;min-width:0}' +
    '.gvt-ten{font-size:15.5px;font-weight:700;color:#101828;line-height:1.3;overflow:hidden;' +
    'display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}' +
    '.gvt-chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:7px}' +
    '.gvt-c{display:inline-flex;align-items:center;font-size:13px;font-weight:700;border-radius:999px;' +
    'padding:3px 10px;white-space:nowrap;line-height:1.4;color:#475467;background:#f2f4f7}' +
    '.gvt-c b{font-weight:800;margin-right:3px}' +
    '.gvt-so{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;margin-top:10px}' +
    '.gvt-o{background:#f8fafc;border-radius:10px;padding:7px 8px;min-width:0}' +
    '.gvt-o .l{font-size:13px;color:#667085;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}' +
    '.gvt-o .v{font-size:15px;font-weight:800;color:#101828;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:1px}' +
    '.gvt-o .v.nhat{font-size:13px;font-weight:600;color:#98a2b3;white-space:normal;line-height:1.3}' +
    '.gvt-o.dx{background:#ecfdf5}.gvt-o.dx .v{color:#047857}' +
    '.gvt-o.do{background:#fef2f2}.gvt-o.do .v{color:#b3261e}' +
    '.gvt-ghi{font-size:13px;line-height:1.5;margin-top:8px}' +
    '.gvt-nhom{display:flex;align-items:center;gap:8px;margin:14px 2px 8px}' +
    '.gvt-nhom .n{font-size:13px;font-weight:700;color:#8a8f9c;text-transform:uppercase;letter-spacing:.4px;flex:1;min-width:0}';
  document.head.appendChild(st);
}

/* Giá vốn đã đủ để tin chưa. Thiếu giá, vòng hay chưa có nguyên liệu thì máy
   chủ vẫn có thể trả he_so tính trên giá vốn THIẾU (Codex #486 v6): MỘT chỗ
   quyết cho thẻ món bán, thẻ phiếu thử và khối kết quả trong phiếu. */
function gvtTinhDuoc(d) {
  return d.trang_thai !== 'thieu_gia' && d.trang_thai !== 'vong' && d.trang_thai !== 'chua_nguyen_lieu';
}

/* Chip hệ số: "Hệ số x6,1 · vốn 16,5%". Màu theo trạng thái: xanh đạt, vàng
   dưới mục tiêu, đỏ vượt giá bán, xanh dương khi chưa có mục tiêu. Giá vốn
   chưa đủ thì không có chip, hệ số trên giá vốn thiếu là con số sai. */
function gvtChipHeSo(d) {
  if (d.he_so == null || !gvtTinhDuoc(d)) return '';
  var mau = { dat: ['#047857', '#ecfdf5'], duoi_muc_tieu: ['#b45309', '#fffbeb'], vuot_gia_ban: ['#b3261e', '#fef2f2'] }[d.trang_thai] ||
    ['#0b7c93', '#ecfeff'];
  return '<span class="gvt-c" data-gvths style="color:' + mau[0] + ';background:' + mau[1] + '"><b>' + gvtHeSo(d.he_so) + '</b>' +
    (d.ty_le != null ? '· vốn ' + gvtPhanTram(d.ty_le) : '') + '</span>';
}

/* Một ô số trong dải ba ô. `nhat`: chưa có số, chữ xám. */
function gvtO(nhan, giaTri, lop, nhat) {
  return '<div class="gvt-o' + (lop ? ' ' + lop : '') + '"><div class="l">' + h(nhan) + '</div>' +
    '<div class="v' + (nhat ? ' nhat' : '') + '">' + h(giaTri) + '</div></div>';
}

function gvtThe(d) {
  var tinhDuoc = gvtTinhDuoc(d);
  var oDx;
  if (!tinhDuoc) oDx = gvtO('Đề xuất', 'Chưa tính', '', 1);
  else if (d.gia_de_xuat) oDx = gvtO('Đề xuất ' + gvtHeSo(d.he_so_muc_tieu), money(d.gia_de_xuat) + 'đ', 'dx');
  else if (!d.gia_ban) oDx = gvtO('Đề xuất', 'Chưa có giá bán', '', 1);
  else oDx = gvtO('Đề xuất', 'Chưa đặt hệ số', '', 1);
  var co = '';
  if (d.trang_thai === 'thieu_gia') {
    var ten = (d.thieu_ten || []).slice(0, 2);
    var con = (d.thieu_so || 0) - ten.length;
    co = 'Thiếu giá ' + d.thieu_so + ' nguyên liệu: ' + ten.join(', ') + (con > 0 ? ' và ' + con + ' nữa' : '');
  } else if (d.trang_thai === 'vuot_gia_ban') {
    co = 'Giá vốn vượt giá bán. Xem lại đơn vị trong công thức.';
  } else if (d.trang_thai === 'vong') {
    co = 'Công thức trỏ vòng vào chính nó, chưa tính được.';
  }
  var tt = GVT_TT[d.trang_thai];
  var chot = d.lan_truoc ? '<span class="gvt-c" data-gvtchot>Chốt ' + gvtNgay(d.lan_truoc.ngay) + ': ' + money(d.lan_truoc.gia) + 'đ (' +
    (d.lan_truoc.chenh_pct > 0 ? '+' : '') + gvtPhanTram(d.lan_truoc.chenh_pct) + ')</span>' : '';
  return '<div class="gvt-the" data-gvtm="' + h(d.ma) + '">' +
    '<div class="gvt-dau">' + anhMon(d.anh) + '<div class="gvt-th">' +
      '<div class="gvt-ten">' + h(d.ten) + '</div>' +
      '<div class="gvt-chips">' + gvtChipTrangThai(d) + gvtChipHeSo(d) + chot + '</div>' +
    '</div></div>' +
    '<div class="gvt-so">' +
      gvtO('Giá vốn', money(d.gia_von) + 'đ', d.trang_thai === 'vuot_gia_ban' ? 'do' : '') +
      (d.gia_ban ? gvtO('Giá bán', money(d.gia_ban) + 'đ') : gvtO('Giá bán', 'Chưa có', '', 1)) +
      oDx +
    '</div>' +
    (co ? '<div class="gvt-ghi" data-gvtco style="color:' + (tt ? tt.mau : '#b45309') + '">' + h(co) + '</div>' : '') +
  '</div>';
}

/* Đầu mỗi nhóm: tên nhóm và chip hệ số mục tiêu của nhóm. */
function gvtDauNhom(ten, heSo) {
  return '<div class="gvt-nhom"><div class="n">' + h(ten) + '</div>' +
    (heSo ? '<span class="gvt-c" style="color:#0f766e;background:#ccfbf1">Mục tiêu <b style="margin:0 0 0 3px">' + gvtHeSo(heSo) + '</b></span>'
      : '<span class="gvt-c">Chưa đặt mục tiêu</span>') + '</div>';
}

function gvtVeDs() {
  var kq = GVT.kq || {};
  var ds = gvtLoc();
  var html = '';
  if (!ds.length) {
    html = '<div class="card"><div class="emp" style="padding:24px"><div class="e1">🍰</div>' +
      '<div>Không có bánh nào khớp. Bỏ bớt bộ lọc hoặc đổi từ khoá.</div>' +
      '<button class="btn gh" data-gvtbo style="margin-top:12px">Bỏ lọc</button></div></div>';
  } else {
    (kq.nhom || []).forEach(function (n) {
      var cua = ds.filter(function (d) { return d.nhom === n.ten; });
      if (!cua.length) return;
      html += gvtDauNhom(n.ten, n.he_so_muc_tieu) + '<div class="card">' + cua.map(gvtThe).join('') + '</div>';
    });
  }
  /* Codex #483 vong 3: mon co nhieu cong thuc dang chay ma chua chon ban mac
     dinh thi may chu KHONG doan, man noi ro ten va cach sua. */
  var nct = kq.nhieu_cong_thuc || {};
  if (nct.so) {
    html += '<div class="card" data-gvtnct style="padding:12px 14px">' +
      '<div style="font-size:13.5px;color:#b45309">' + nct.so + ' món có nhiều công thức nhưng chưa chọn công thức mặc định nên chưa tính. ' +
      'Mở công thức đúng trên Desk, tích Mặc định rồi tính lại.</div>' +
      '<div style="font-size:13px;color:#6b7280;margin-top:8px;line-height:1.6">' +
      (nct.ten || []).map(h).join(', ') + (nct.so > (nct.ten || []).length ? ' và ' + (nct.so - nct.ten.length) + ' nữa' : '') +
      '</div></div>';
  }
  var cct = kq.chua_cong_thuc || {};
  if (cct.so) {
    html += '<div class="card" data-gvtcct style="padding:12px 14px;cursor:pointer">' +
      '<div style="font-size:13.5px;color:#4b5563">' + cct.so + ' món chưa có công thức nên chưa tính được. ' +
      (GVT.moCct ? 'Bấm để thu gọn.' : 'Bấm để xem.') + ' Món mới đang thử thì dùng tab Món thử (R&D).</div>' +
      (GVT.moCct ? '<div data-gvtcctds style="font-size:13px;color:#6b7280;margin-top:8px;line-height:1.6">' +
        (cct.ten || []).map(h).join(', ') + (cct.so > (cct.ten || []).length ? ' và ' + (cct.so - cct.ten.length) + ' nữa' : '') +
        '</div>' : '') + '</div>';
  }
  return html;
}

/* Hai tab: Món đang bán, Món thử (R&D). */
function gvtTab() {
  return '<div style="display:flex;gap:7px;margin-bottom:10px">' +
    posChipNut('data-gvttab="ban"', 'Món đang bán', GVT.tab === 'ban') +
    posChipNut('data-gvttab="thu"', 'Món thử (R&D)', GVT.tab === 'thu') + '</div>';
}

function gvtVe() {
  gvtCss();
  if (GVT.tab === 'thu') return gvtVeThu();
  var kq = GVT.kq || {};
  var dong = kq.dong || [];
  var html = gvtTab() + '<div class="card" style="padding:12px 14px"><div style="font-size:13.5px;color:#4b5563;line-height:1.55">' +
    'Tiền nguyên liệu theo công thức đang dùng, tính dồn qua bán thành phẩm, theo giá kho hôm nay. ' +
    'x5 nghĩa là giá bán gấp 5 lần giá vốn; "vốn 20%" là giá vốn trên giá bán. ' +
    'Chưa gồm bao bì, công, hao hụt. Chỉ để định giá, không đổi sổ sách.</div>' +
    '<div style="font-size:13px;color:#9ca3af;margin-top:6px">Tính lúc ' + h(kq.cap_nhat_luc || '') + '</div>' +
    '<input class="tin" id="gvtQ" placeholder="Tìm tên hoặc mã bánh" value="' + h(GVT.tim) + '" style="margin:10px 0 0"></div>';

  var chipNhom = posChipNut('data-gvtn=""', 'Tất cả ' + dong.length, !GVT.nhom);
  (kq.nhom || []).forEach(function (n) {
    if (!n.so_mon) return;
    chipNhom += posChipNut('data-gvtn="' + h(n.ten) + '" title="' + h(n.ten) + '"', h(n.nhan) + ' ' + n.so_mon, GVT.nhom === n.ten);
  });
  var chipTt = '';
  GVT_CHIP_TT.forEach(function (t) {
    var so = dong.filter(function (d) { return d.trang_thai === t; }).length;
    if (!so && GVT.tt !== t) return;
    chipTt += posChipNut('data-gvtt="' + t + '"', GVT_TT[t].nhan + ' ' + so, GVT.tt === t, false, GVT_TT[t].mau);
  });
  html += '<div class="card" style="padding:10px 12px;overflow-x:auto"><div style="display:flex;gap:7px;padding:0 2px">' + chipNhom + '</div>' +
    (chipTt ? '<div style="display:flex;gap:7px;padding:8px 2px 0">' + chipTt + '</div>' : '') + '</div>';
  if (kq.sua_duoc) html += '<button class="btn gh" data-gvthso style="margin:0 0 10px">Hệ số mục tiêu</button>';
  html += '<div id="gvtDs">' + gvtVeDs() + '</div>';

  var b = frame(GVT_TIEU_DE, html, kq.sua_duoc ? { footer: '<button class="btn" id="gvtChot">Chốt vào bảng Giá vốn tạm tính</button>' } : {});
  var q = document.getElementById('gvtQ');
  if (q) q.oninput = function () {
    GVT.tim = q.value;
    var ds = document.getElementById('gvtDs');
    if (ds) ds.innerHTML = gvtVeDs();
  };
  b.onclick = function (e) {
    var t = e.target;
    var el;
    if ((el = t.closest('[data-gvttab]'))) return gvtDoiTab(el.getAttribute('data-gvttab'));
    if ((el = t.closest('[data-gvtn]'))) { GVT.nhom = el.getAttribute('data-gvtn') || ''; return gvtVe(); }
    if ((el = t.closest('[data-gvtt]'))) { var k = el.getAttribute('data-gvtt'); GVT.tt = GVT.tt === k ? '' : k; return gvtVe(); }
    if (t.closest('[data-gvtbo]')) { GVT.nhom = ''; GVT.tt = ''; GVT.tim = ''; return gvtVe(); }
    if (t.closest('[data-gvtcct]')) { GVT.moCct = !GVT.moCct; return gvtVe(); }
    if (t.closest('[data-gvthso]')) return gvtSuaHeSo();
    if ((el = t.closest('[data-gvtm]'))) return gvtChiTiet(el.getAttribute('data-gvtm'), null, []);
  };
  var c = document.getElementById('gvtChot');
  if (c) c.onclick = gvtChot;
  return b;
}

function gvtLoi(e) {
  var m = (e && e.message) || '';
  var cau = /quyền/i.test(m) ? m : 'Không tải được giá vốn. Kiểm mạng rồi bấm Thử lại.';
  var b = frame(GVT_TIEU_DE, '<div class="emp"><div class="e1">⚠️</div><div>' + h(cau) + '</div>' +
    '<button class="btn" data-gvtlai style="margin-top:12px">Thử lại</button></div>');
  b.onclick = function (ev) { if (ev.target.closest('[data-gvtlai]')) scrGiaVonTam(); };
}

async function scrGiaVonTam() {
  if (GVT.tab === 'thu') return gvtTaiThu();
  frame(GVT_TIEU_DE, '<div class="emp"><div class="e1">⏳</div><div>Đang tính giá vốn...</div></div>');
  try { GVT.kq = await api('vagabond.gia_von_tam.tinh', {}); }
  catch (e) { GVT.kq = null; return gvtLoi(e); }
  gvtVe();
}

/* Đổi tab chỉ tải phần chưa có, không tính lại tab kia. */
function gvtDoiTab(t) {
  GVT.tab = t === 'thu' ? 'thu' : 'ban';
  if (GVT.tab === 'thu') return GVT.thu ? gvtVeThu() : gvtTaiThu();
  return GVT.kq ? gvtVe() : scrGiaVonTam();
}

/* Sheet hệ số mục tiêu: mỗi nhóm một ô "x". Ô không lớn hơn 1 hoặc quá 20 bị
   chặn tại chỗ, không gửi lên máy chủ (máy chủ vẫn kiểm lại, chuan_he_so).
   Gõ tới đâu hiện phần trăm giá vốn tương ứng tới đó. */
function gvtQuyDoi(v) {
  var p = parseFloat(String(v || '').trim().replace(',', '.'));
  if (isNaN(p) || p <= 1 || p > 20) return '';
  return 'tức giá vốn ' + gvtPhanTram(Math.round(1000 / p) / 10) + ' giá bán';
}
function gvtSuaHeSo() {
  var kq = GVT.kq || {};
  /* Codex #486 v11: đủ mọi nhóm bán (kể cả nhóm chỉ có món thử, chưa có món
     bán tính được), để lưu không làm mất mục tiêu của nhóm bị ẩn. Máy chủ
     cũng chỉ ghi đè nhóm có gửi (gop_he_so). */
  var thongKe = {};
  (kq.nhom || []).forEach(function (n) { thongKe[n.ten] = n; });
  var nhom = (kq.nhom_ban || (kq.nhom || []).filter(function (n) { return n.so_mon; })).map(function (n) {
    var t = thongKe[n.ten] || {};
    return { ten: n.ten, so_mon: t.so_mon || 0, trung_vi: t.trung_vi == null ? null : t.trung_vi,
      he_so_muc_tieu: (kq.he_so || {})[n.ten] != null ? kq.he_so[n.ten] : (t.he_so_muc_tieu == null ? null : t.he_so_muc_tieu) };
  });
  var ov = document.createElement('div'); ov.className = 'sh';
  ov.innerHTML = '<div class="shb" style="padding:18px 16px calc(env(safe-area-inset-bottom,0px) + 16px)">' +
    '<div style="font-size:17.5px;font-weight:700;margin-bottom:6px">Hệ số giá bán mục tiêu</div>' +
    '<div style="font-size:13.5px;color:#5a6070;line-height:1.5;margin-bottom:12px">Giá bán đề xuất = giá vốn nhân hệ số này, làm tròn lên nghìn. ' +
    'Ví dụ x5 là giá bán gấp 5 lần giá vốn. Để trống thì không đề xuất giá cho nhóm đó.</div>' +
    '<div data-gvthsds style="flex:1;min-height:0;overflow-y:auto;margin:0 -4px 8px;padding:0 4px">' +
    nhom.map(function (n) {
      return '<div style="margin-bottom:12px"><div style="display:flex;align-items:center;gap:10px">' +
        '<div style="flex:1;font-size:14.5px;font-weight:600">' + h(n.ten) + '</div><span style="font-weight:700">x</span>' +
        '<input class="nt" data-gvthsn="' + h(n.ten) + '" inputmode="decimal" value="' + (n.he_so_muc_tieu == null ? '' : h(String(n.he_so_muc_tieu).replace('.', ','))) +
        '" style="width:84px;height:44px;text-align:right;padding:0 10px"></div>' +
        '<div style="font-size:13px;color:#9ca3af">' + (n.trung_vi != null ? 'Hiện trung vị ' + gvtHeSo(n.trung_vi) :
          n.so_mon ? 'Chưa đủ số để tính trung vị' : 'Chưa có món đang bán tính được') +
        ' <span data-gvtqd="' + h(n.ten) + '">' + h(gvtQuyDoi(n.he_so_muc_tieu)) + '</span></div>' +
        '<div data-gvtsai="' + h(n.ten) + '" style="font-size:13px;color:#b3261e"></div></div>';
    }).join('') + '</div>' +
    '<button class="btn" data-gvtluu>Lưu hệ số</button><button class="btn gh" data-gvthuy style="margin-top:9px">Huỷ</button></div>';
  document.body.appendChild(ov);
  ov.oninput = function (e) {
    var o = e.target.closest && e.target.closest('[data-gvthsn]');
    if (!o) return;
    var qd = ov.querySelector('[data-gvtqd="' + o.getAttribute('data-gvthsn') + '"]');
    if (qd) qd.innerHTML = h(gvtQuyDoi(o.value));
  };
  ov.onclick = async function (e) {
    if (e.target === ov || e.target.closest('[data-gvthuy]')) { ov.remove(); return; }
    if (!e.target.closest('[data-gvtluu]')) return;
    var hs = {}, sai = 0;
    nhom.forEach(function (n) {
      var o = ov.querySelector('[data-gvthsn="' + n.ten + '"]');
      var bao = ov.querySelector('[data-gvtsai="' + n.ten + '"]');
      var v = String((o && o.value) || '').trim().replace(',', '.');
      if (bao) bao.innerHTML = '';
      if (!v) { hs[n.ten] = ''; return; }
      var p = parseFloat(v);
      if (isNaN(p) || p <= 1 || p > 20) { sai++; if (bao) bao.innerHTML = 'Nhập số lớn hơn 1, tối đa 20.'; return; }
      hs[n.ten] = p;
    });
    if (sai) return;
    busy(true);
    try { await api('vagabond.gia_von_tam.luu_he_so', { he_so: JSON.stringify(hs) }); busy(false); }
    catch (er) { busy(false); return baoTin((er && er.message) || 'Lưu hệ số lỗi'); }
    ov.remove();
    toast('Đã lưu hệ số mục tiêu', 3000);
    GVT.thu = null;
    scrGiaVonTam();
  };
}

/* Sheet chi tiết: một tầng mỗi lần, chỉ gọi máy chủ khi bấm. Dòng bán thành
   phẩm có mũi tên mở xuống tầng con, tối đa 6 tầng. */
async function gvtChiTiet(ma, bom, duong) {
  var ct;
  busy(true);
  try { ct = await api('vagabond.gia_von_tam.chi_tiet', bom ? { ma: ma, bom: bom } : { ma: ma }); busy(false); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Không mở được chi tiết'); }
  var dong = ct.dong || [];
  var hien = dong.slice(0, 30);
  var ov = document.createElement('div'); ov.className = 'sh';
  ov.innerHTML = '<div class="shb"><div class="shh"><b>' + h(ct.ten) + '</b><div class="x" data-gvtdong>&times;</div></div>' +
    '<div style="padding:4px 14px 8px;font-size:13px;color:#6b7280">Một mẻ ra ' + (ct.so_ra || 1) + ' · giá vốn ' + money(ct.gia) + 'đ mỗi đơn vị' +
    (duong.length ? ' · <span data-gvtlui style="color:#0d9488;font-weight:700;cursor:pointer">‹ Quay lại</span>' : '') + '</div>' +
    '<div class="shl">' + hien.map(function (d) {
      var xuong = d.bom_con && duong.length < 5;
      return '<div class="shi"' + (xuong ? ' data-gvtcon="' + h(d.ma) + '" data-gvtbom="' + h(d.bom_con) + '"' : '') + ' style="align-items:flex-start">' +
        '<span style="flex:1;min-width:0">' + h(d.ten) +
        '<div style="color:#6b7280;font-size:12.5px;margin-top:2px">' + kl(d.sl, d.dvt) + ' · ' + money(d.don_gia) + 'đ/' + h(d.dvt) + ' (' + h(d.nguon) + ')' +
        (d.thieu ? ' · <span style="color:#b45309">thiếu giá</span>' : '') + '</div></span>' +
        '<span style="font-weight:700;white-space:nowrap">' + money(d.thanh_tien) + 'đ' + (xuong ? ' ›' : '') + '</span></div>';
    }).join('') +
    (dong.length > hien.length ? '<div style="padding:10px 14px;font-size:13px;color:#6b7280">và ' + (dong.length - hien.length) + ' nữa</div>' : '') +
    '</div></div>';
  document.body.appendChild(ov);
  ov.onclick = function (e) {
    if (e.target === ov || e.target.closest('[data-gvtdong]')) { ov.remove(); return; }
    if (e.target.closest('[data-gvtlui]')) { ov.remove(); var tr = duong[duong.length - 1]; return gvtChiTiet(tr.ma, tr.bom, duong.slice(0, -1)); }
    var con = e.target.closest('[data-gvtcon]');
    if (con) { ov.remove(); gvtChiTiet(con.getAttribute('data-gvtcon'), con.getAttribute('data-gvtbom'), duong.concat([{ ma: ma, bom: bom }])); }
  };
}

async function gvtChot() {
  var dong = (GVT.kq || {}).dong || [];
  var bo = { thieu_gia: 1, vong: 1 };
  var n = dong.filter(function (d) { return !bo[d.trang_thai] && d.gia_von > 0; }).length;
  var m = dong.length - n;
  var ngay = gvtNgay((GVT.kq || {}).ngay) + '/' + String((GVT.kq || {}).ngay || '').slice(0, 4);
  if (!await confirmSheet('Chốt giá vốn tạm',
    'Lưu giá vốn tạm của ' + n + ' món vào bảng giá Giá vốn tạm tính, ngày ' + ngay + '. ' +
    (m ? m + ' món chưa tính đủ giá (thiếu giá nguyên liệu) sẽ bỏ qua. ' : '') + 'Không đổi công thức, tồn kho hay sổ sách.', 'Chốt')) return;
  var kq;
  busy(true);
  try { kq = await api('vagabond.gia_von_tam.chot', {}); busy(false); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Chốt lỗi'); }
  var boQua = 0;
  Object.keys(kq.bo_qua || {}).forEach(function (k) { boQua += kq.bo_qua[k]; });
  toast('Đã lưu ' + kq.da_luu + ' món.' + (boQua ? ' Bỏ qua ' + boQua + ' món.' : ''), 5000);
  scrGiaVonTam();
}

/* =================================================================
   MÓN THỬ (R&D): danh sách phiếu và màn nhập
   ================================================================= */

/* Tham số gọi danh sách phiếu thử: MỘT chỗ ghép ô tìm và ba hàng chip, cho
   lần tải đầu, gõ tìm, bấm chip và mở lại bản nháp (Codex #486 v7). */
function gvtThamSoDs() {
  return { tu_khoa: GVT.thuQ, bat_dau: 0, trang_thai: GVT.thuTt, nhom: GVT.thuNhom, khoang: GVT.thuKh };
}

async function gvtTaiThu() {
  frame(GVT_TIEU_DE, gvtTab() + '<div class="emp"><div class="e1">⏳</div><div>Đang tính các phiếu thử...</div></div>');
  var lan = ++GVT.lanDs;
  var kq;
  try { kq = await api('vagabond.gia_von_tam.ds_thu', gvtThamSoDs()); }
  catch (e) { if (lan === GVT.lanDs) { GVT.thu = null; gvtLoi(e); } return; }
  if (lan !== GVT.lanDs) return;
  GVT.thu = kq;
  gvtVeThu();
}

/* Tải danh sách phiếu thử theo ô tìm (trang đầu) hoặc nối trang sau (Xem
   thêm). Máy chủ chia trang và tìm; kết quả của lượt cũ về sau bị bỏ, để
   gõ nhanh hai chữ không hiện nhầm danh sách của chữ trước (Codex #486). */
async function gvtTaiDs(noiTiep) {
  var t = GVT.thu || {};
  var lan = ++GVT.lanDs;
  var kq;
  try {
    /* Xem thêm đi đúng bộ lọc máy chủ đã dùng cho trang đang hiện. */
    kq = await api('vagabond.gia_von_tam.ds_thu', noiTiep ? { tu_khoa: t.tu_khoa || '', bat_dau: t.bat_dau_tiep || 0,
      trang_thai: t.trang_thai || '', nhom: t.nhom || '', khoang: t.khoang || '' } : gvtThamSoDs());
  } catch (e) { if (lan === GVT.lanDs) baoTin((e && e.message) || 'Không tải được danh sách phiếu thử'); return; }
  if (lan !== GVT.lanDs) return;
  if (noiTiep) kq.ds = (t.ds || []).concat(kq.ds || []);
  GVT.thu = kq;
  var vung = document.getElementById('gvtThuDs');
  if (vung) vung.innerHTML = gvtDsThu();
}

function gvtTenNhom(ten) {
  var n = ((GVT.thu || {}).nhom_ban || []).filter(function (x) { return x.ten === ten; })[0];
  return n ? n.nhan : ten;
}

/* Dòng giá đề xuất của một phiếu: nói rõ thiếu gì khi chưa đề xuất được. */
function gvtCauDeXuat(p) {
  if (p.gia_de_xuat) return 'Đề xuất ' + money(p.gia_de_xuat) + 'đ (mục tiêu ' + gvtHeSo(p.he_so_muc_tieu) + ')';
  if (p.trang_thai === 'chua_nguyen_lieu') return 'Thêm nguyên liệu để tính';
  if (p.trang_thai === 'thieu_gia' || p.trang_thai === 'vong') return '';
  if (!p.nhom) return 'Chọn nhóm bán để có giá đề xuất';
  return 'Nhóm ' + gvtTenNhom(p.nhom) + ' chưa đặt hệ số mục tiêu';
}

function gvtThePhieu(p) {
  var dvt = p.dvt_ra || 'Cái';
  var tinhDuoc = gvtTinhDuoc(p);
  var oDx;
  if (p.gia_de_xuat) oDx = gvtO('Đề xuất ' + gvtHeSo(p.he_so_muc_tieu), money(p.gia_de_xuat) + 'đ', 'dx');
  else oDx = gvtO('Đề xuất', !tinhDuoc ? 'Chưa tính' : (p.nhom ? 'Chưa đặt hệ số' : 'Chọn nhóm'), '', 1);
  /* Phiếu thử chưa có ảnh: ô 🍰 giữ hàng như thẻ món bán (AGENTS.md, Codex #486 v6). */
  return '<div class="gvt-the" data-gvtp="' + h(p.name) + '">' +
    '<div class="gvt-dau">' + anhMon('') + '<div class="gvt-th">' +
      '<div class="gvt-ten">' + h(p.ten_mon) + '</div>' +
      '<div class="gvt-chips">' + gvtChipTrangThai(p) + gvtChipHeSo(p) +
        (p.nhom ? '<span class="gvt-c">' + h(gvtTenNhom(p.nhom)) + '</span>' : '') +
        '<span class="gvt-c">Mẻ ra ' + String(p.so_ra).replace('.', ',') + ' ' + h(dvt) + '</span></div>' +
    '</div></div>' +
    '<div class="gvt-so">' +
      gvtO('Giá vốn/' + dvt, money(p.gia_von) + 'đ', p.trang_thai === 'vuot_gia_ban' ? 'do' : '') +
      (p.gia_ban_du_kien ? gvtO('Giá dự kiến', money(p.gia_ban_du_kien) + 'đ') : gvtO('Giá dự kiến', 'Chưa có', '', 1)) +
      oDx +
    '</div>' +
    (p.trang_thai === 'vong' ? '<div class="gvt-ghi" data-gvtvong style="color:#b3261e">' + GVT_CAU_VONG + '</div>' :
      p.thieu_so ? '<div class="gvt-ghi" style="color:#b45309">Thiếu giá ' + p.thieu_so + ' nguyên liệu. Mở phiếu để nhập giá tay.</div>' :
      (!p.gia_de_xuat && tinhDuoc && gvtCauDeXuat(p) ? '<div class="gvt-ghi" style="color:#667085">' + h(gvtCauDeXuat(p)) + '</div>' : '')) +
    gvtDauVet(p) +
  '</div>';
}

/* Ba hàng chip trên danh sách phiếu thử (AGENTS.md 2b điều 3, Codex #486 v7):
   trạng thái có đếm, nhóm bán có đếm, khoảng ngày lập. Số do máy chủ đếm
   trên cả tập đã tính, chip đang chọn tô đậm, mỗi hàng cuộn ngang. */
var GVT_TT_THU = ['vuot_gia_ban', 'vong', 'thieu_gia', 'duoi_muc_tieu', 'chua_dat_muc_tieu', 'chua_gia_ban', 'chua_nguyen_lieu', 'dat'];
var GVT_CHUA_NHOM = '__chua_nhom';
var GVT_KHOANG = [['', 'Mọi ngày lập'], ['hom_nay', 'Lập hôm nay'], ['7_ngay', 'Lập 7 ngày qua'], ['30_ngay', 'Lập 30 ngày qua']];
function gvtChipThu(t) {
  var dt = t.dem_tt || {}, dn = t.dem_nhom || {};
  var cong = function (o) { return Object.keys(o).reduce(function (s, k) { return s + (o[k] || 0); }, 0); };
  var hang = function (x, dau) { return '<div style="display:flex;gap:7px;overflow-x:auto;padding:' + (dau ? '0' : '8px') + ' 2px 2px">' + x + '</div>'; };
  var r1 = posChipNut('data-gvtft=""', 'Tất cả ' + cong(dt), !GVT.thuTt);
  GVT_TT_THU.forEach(function (k) {
    var so = dt[k] || 0;
    if (!so && GVT.thuTt !== k) return;
    r1 += posChipNut('data-gvtft="' + k + '"', GVT_CHIP[k][0] + ' ' + so, GVT.thuTt === k, false, GVT_CHIP[k][1]);
  });
  var r2 = posChipNut('data-gvtfn=""', 'Mọi nhóm ' + cong(dn), !GVT.thuNhom);
  (t.nhom_ban || []).forEach(function (n) {
    var so = dn[n.ten] || 0;
    if (!so && GVT.thuNhom !== n.ten) return;
    r2 += posChipNut('data-gvtfn="' + h(n.ten) + '" title="' + h(n.ten) + '"', h(n.nhan) + ' ' + so, GVT.thuNhom === n.ten);
  });
  var chua = dn[GVT_CHUA_NHOM] || 0;
  if (chua || GVT.thuNhom === GVT_CHUA_NHOM) r2 += posChipNut('data-gvtfn="' + GVT_CHUA_NHOM + '"', 'Chưa chọn nhóm ' + chua, GVT.thuNhom === GVT_CHUA_NHOM);
  var r3 = GVT_KHOANG.map(function (k) { return posChipNut('data-gvtfk="' + k[0] + '"', k[1], GVT.thuKh === k[0]); }).join('');
  return '<div class="card" data-gvtloc style="padding:10px 12px">' + hang(r1, 1) + hang(r2) + hang(r3) + '</div>';
}

/* Dấu vết của phiếu đã lưu (AGENTS.md 2b điều 11, Codex #486 v9): ai lập lúc
   nào, ai sửa gần nhất lúc nào, chip "Đã sửa N lần". Số do máy chủ đếm. */
function gvtLuc(s) {
  var m = /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})/.exec(String(s || ''));
  return m ? m[3] + '/' + m[2] + ' ' + m[4] + ':' + m[5] : '';
}
function gvtDauVet(p, kieu) {
  if (!p || !p.name) return '';
  var s = 'Lập: ' + h(p.ten_nguoi || p.nguoi || '') + ' ' + gvtLuc(p.lap_luc);
  if (p.so_lan_sua) s += ' · Sửa gần nhất: ' + h(p.ten_nguoi_sua || p.nguoi_sua || '') + ' ' + gvtLuc(p.cap_nhat);
  return '<div class="gvt-ghi" data-gvtvet style="color:#6b7280;' + (kieu || '') + '">' + s +
    (p.so_lan_sua ? ' <span class="gvt-c" data-gvtsua style="color:#92400e;background:#fef3c7">Đã sửa ' + p.so_lan_sua + ' lần</span>' : '') + '</div>';
}

/* Danh sách phiếu (phần dưới ô tìm): ba hàng chip, thẻ, câu rỗng, nút Xem thêm. */
function gvtDsThu() {
  var t = GVT.thu || {};
  var ds = t.ds || [];
  var dangLoc = !!(t.trang_thai || t.nhom || t.khoang);
  var chip = (t.tong || dangLoc) ? gvtChipThu(t) : '';
  /* Quá TOI_DA_THU phiếu khớp tên: máy chủ chỉ đếm, lọc trong phần mới sửa nhất.
     Câu này hiện cả khi lọc ra rỗng, để không bảo sai là không có (Codex #486 v8). */
  var vuot = t.vuot ? '<div data-gvtvuot style="font-size:13px;color:#b45309;margin:0 2px 8px">Chỉ đếm và lọc trong ' + (t.tong || 0) +
    ' phiếu sửa gần nhất. Phiếu cũ hơn có thể khớp: gõ tên món vào ô tìm để thu hẹp.</div>' : '';
  if (!ds.length) {
    var cau = dangLoc ? 'Không có phiếu nào khớp bộ lọc' + (t.tu_khoa ? ' và tên "' + h(t.tu_khoa) + '"' : '') + '.' :
      t.tu_khoa ? 'Không thấy phiếu nào có tên chứa "' + h(t.tu_khoa) + '".' :
      'Chưa có phiếu tính giá thử nào.' + (t.sua_duoc ? ' Bấm Phiếu tính giá thử mới để bắt đầu.' : '');
    return chip + vuot + '<div class="card"><div class="emp" style="padding:24px"><div class="e1">🧪</div><div>' + cau + '</div>' +
      (dangLoc ? '<button class="btn gh" data-gvtthubo style="margin-top:12px">Bỏ lọc</button>' : '') + '</div></div>';
  }
  return chip + vuot + '<div class="card">' + ds.map(gvtThePhieu).join('') + '</div>' +
    (t.con_nua ? '<button class="btn gh" data-gvtthemds style="margin:0 0 10px">Xem thêm phiếu cũ hơn</button>' : '');
}

function gvtVeThu() {
  gvtCss();
  var t = GVT.thu || {};
  var html = gvtTab() + '<div class="card" style="padding:12px 14px"><div style="font-size:13.5px;color:#4b5563;line-height:1.55">' +
    'Món đang thử chưa bán: nhập nguyên liệu tạm để có giá vốn và giá bán đề xuất theo hệ số mục tiêu của nhóm. ' +
    'Tính bằng giá kho hôm nay, bán thành phẩm lấy theo công thức đang có. Không tạo mã hàng, không tạo công thức, không đổi sổ sách.</div>' +
    '<input class="tin" id="gvtThuQ" placeholder="Tìm tên món thử" value="' + h(GVT.thuQ) + '" style="margin:10px 0 0"></div>' +
    '<div id="gvtThuDs">' + gvtDsThu() + '</div>';
  var b = frame(GVT_TIEU_DE, html, t.sua_duoc ? { footer: '<button class="btn" id="gvtThuMoi">Phiếu tính giá thử mới</button>' } : {});
  b.onclick = function (e) {
    var el;
    if ((el = e.target.closest('[data-gvttab]'))) return gvtDoiTab(el.getAttribute('data-gvttab'));
    if (e.target.closest('[data-gvtthemds]')) return gvtTaiDs(true);
    /* Bấm chip là lọc ở máy chủ từ trang đầu; bấm lại chip trạng thái đang chọn là bỏ. */
    if ((el = e.target.closest('[data-gvtft]'))) { var k = el.getAttribute('data-gvtft'); GVT.thuTt = k && GVT.thuTt !== k ? k : ''; return gvtTaiDs(false); }
    if ((el = e.target.closest('[data-gvtfn]'))) { GVT.thuNhom = el.getAttribute('data-gvtfn') || ''; return gvtTaiDs(false); }
    if ((el = e.target.closest('[data-gvtfk]'))) { GVT.thuKh = el.getAttribute('data-gvtfk') || ''; return gvtTaiDs(false); }
    if (e.target.closest('[data-gvtthubo]')) { GVT.thuTt = ''; GVT.thuNhom = ''; GVT.thuKh = ''; return gvtTaiDs(false); }
    if ((el = e.target.closest('[data-gvtp]'))) {
      var p = ((GVT.thu || {}).ds || []).filter(function (x) { return x.name === el.getAttribute('data-gvtp'); })[0];
      if (p) gvtMoPhieu(p);
    }
  };
  var q = document.getElementById('gvtThuQ');
  if (q) q.oninput = function () {
    GVT.thuQ = q.value;
    if (GVT.henQ) clearTimeout(GVT.henQ);
    GVT.henQ = setTimeout(function () { GVT.henQ = null; gvtTaiDs(false); }, 300);
  };
  var mo = document.getElementById('gvtThuMoi');
  if (mo) mo.onclick = function () {
    gvtMoPhieu({ name: null, ten_mon: '', nhom: '', so_ra: 1, dvt_ra: 'Cái', gia_ban_du_kien: 0, ghi_chu: '', dong: [] });
  };
  return b;
}

/* Mở màn nhập. Bản sao sâu, sửa không đụng danh sách cho tới khi Lưu. */
function gvtMoPhieu(p) {
  GVT.p = JSON.parse(JSON.stringify({
    name: p.name || null, ten_mon: p.ten_mon || '', nhom: p.nhom || '', so_ra: p.so_ra || 1, dvt_ra: p.dvt_ra || 'Cái',
    gia_ban_du_kien: p.gia_ban_du_kien || '', ghi_chu: p.ghi_chu || '',
    /* Bản của phiếu lúc mở (máy chủ trả), gửi kèm khi lưu để không đè bản người
       khác vừa sửa; bản nháp mang theo nên bản nháp cũ cũng bị chặn (v12). */
    phien_ban: p.phien_ban || '',
    /* Dấu vết giữ riêng trong phiếu đang sửa: kết quả tính thử thay GVT.pk mà
       không có ai lập, ai sửa (Codex #486 v10), và bản nháp lưu GVT.p nên mở
       lại từ bản nháp vẫn còn dấu vết (v11). Không gửi lên máy chủ. */
    vet: p.name ? { name: p.name, nguoi: p.nguoi, ten_nguoi: p.ten_nguoi, lap_luc: p.lap_luc, nguoi_sua: p.nguoi_sua,
      ten_nguoi_sua: p.ten_nguoi_sua, cap_nhat: p.cap_nhat, so_lan_sua: p.so_lan_sua } : null,
    dong: (p.dong || []).map(function (d) {
      return { item_code: d.item_code || null, ten: d.ten || '', dvt: d.dvt || '', so_luong: d.so_luong, don_gia_tay: d.don_gia_tay || '' };
    })
  }));
  GVT.pk = p.name ? JSON.parse(JSON.stringify(p)) : null;
  GVT.pkDong = p.name ? GVT.pk.dong : null;   /* phiếu đã lưu: mọi dòng đều hợp lệ, kết quả khớp từng dòng */
  GVT.lan++; GVT.loiTinh = null;
  vgbBoChuaLuu();
  go(gvtManPhieu);
}

/* Payload gửi máy chủ để TÍNH THỬ: chỉ dòng đã có số lượng > 0. `chiSo` giữ
   vị trí từng dòng gửi đi để ghép kết quả về đúng dòng trên màn. */
function gvtSoVn(v) { var p = parseFloat(String(v == null ? '' : v).trim().replace(',', '.')); return isNaN(p) ? null : p; }
function gvtGoiTinh() {
  var p = GVT.p, chiSo = [], dong = [];
  p.dong.forEach(function (d, i) {
    var sl = gvtSoVn(d.so_luong);
    if (sl == null || sl <= 0) return;
    chiSo.push(i);
    dong.push({ item_code: d.item_code, ten: d.ten, dvt: d.dvt, so_luong: sl, don_gia_tay: gvtSoVn(d.don_gia_tay) || 0 });
  });
  return { chiSo: chiSo, phieu: { ten_mon: p.ten_mon || 'Món thử', nhom: p.nhom, so_ra: gvtSoVn(p.so_ra),
    dvt_ra: p.dvt_ra, gia_ban_du_kien: gvtSoVn(p.gia_ban_du_kien) || 0, dong: dong } };
}

function gvtDanhDau() {
  S.chuaLuu = 'Phiếu tính giá thử đang sửa dở, chưa bấm Lưu phiếu. Rời màn này là mất.';
  S.chuaLuuNac = S.stack.length - 1;
}

async function gvtTinhLai() {
  var g = gvtGoiTinh();
  /* Codex #486: gõ tiếp khi lượt trước còn chạy thì lượt trước về sau phải
     bị bỏ, không đè số mới. Rời phiếu (lưu, bỏ, mở phiếu khác) cũng tăng lượt. */
  var lan = ++GVT.lan, p = GVT.p;
  /* Codex #486 v3: mẻ ra 0 hoặc trống thì không tự thay 1 rồi gửi, mà nói
     ngay cần sửa gì và bỏ số của lần trước. */
  var soRa = g.phieu.so_ra;
  if (soRa == null || soRa <= 0) return gvtBaoLoiTinh('Một mẻ phải ra hơn 0. Sửa ô Một mẻ ra để tính.');
  var kq;
  try { kq = await api('vagabond.gia_von_tam.tinh_thu', { phieu: JSON.stringify(g.phieu) }); }
  catch (e) {
    if (lan !== GVT.lan || p !== GVT.p) return;
    return gvtBaoLoiTinh((e && e.message) || 'Không tính được. Kiểm mạng rồi sửa lại một ô để tính lại.');
  }
  if (lan !== GVT.lan || p !== GVT.p) return;
  GVT.loiTinh = null;
  var dongKq = [];
  g.chiSo.forEach(function (i, j) { dongKq[i] = (kq.dong || [])[j]; });
  GVT.pk = kq;
  GVT.pkDong = dongKq;
  gvtVeKetQua();
}
function gvtBaoLoiTinh(cau) {
  GVT.pk = null; GVT.pkDong = []; GVT.loiTinh = cau;
  gvtVeKetQua();
}
function gvtHenTinh() {
  if (GVT.hen) clearTimeout(GVT.hen);
  GVT.hen = setTimeout(function () { GVT.hen = null; gvtTinhLai(); }, 400);
}

/* Khối kết quả trên đầu màn nhập. */
function gvtKhoiKetQua() {
  var k = GVT.pk;
  var p = GVT.p;
  if (GVT.loiTinh) return '<div style="font-size:14px;color:#b3261e;font-weight:700">' + h(GVT.loiTinh) + '</div>';
  if (!k) return '<div style="font-size:13.5px;color:#6b7280">Thêm nguyên liệu và số lượng để máy tính giá vốn.</div>';
  var de = gvtCauDeXuat(Object.assign({}, k, { nhom: p.nhom }));
  /* Cùng bộ chip với thẻ danh sách (17/10/2026). */
  return '<div style="font-size:17px;font-weight:800;color:#101828">Giá vốn ' + money(k.gia_von) + 'đ/' + h(p.dvt_ra || 'Cái') + '</div>' +
    '<div class="t2" style="margin-top:2px">Cả mẻ ' + money(k.tong_me) + 'đ, ra ' + String(p.so_ra || 1).replace('.', ',') + ' ' + h(p.dvt_ra || 'Cái') + '</div>' +
    '<div class="gvt-chips">' + gvtChipTrangThai(k) + gvtChipHeSo(k) +
      (de ? '<span class="gvt-c" style="color:' + (k.gia_de_xuat ? '#047857;background:#ecfdf5' : '#475467;background:#f2f4f7') + '">' + h(de) + '</span>' : '') +
    '</div>' +
    (k.he_so != null ? '<div class="t2" style="margin-top:6px">Giá bán dự kiến ' + money(gvtSoVn(p.gia_ban_du_kien)) + 'đ</div>' : '') +
    (k.trang_thai === 'vong' ? '<div class="gvt-ghi" data-gvtvong style="color:#b3261e">' + GVT_CAU_VONG + '</div>' :
      k.thieu_so ? '<div class="gvt-ghi" style="color:#b45309">Thiếu giá ' + k.thieu_so + ' nguyên liệu: nhập giá tay ở dòng đó.</div>' : '');
}
/* Dòng cần ô giá tay: NVL chưa có mã, mã máy chủ báo thiếu giá (kể cả nhiều
   công thức) hoặc máy chủ đang dùng giá tay của dòng đó. Mã đã có giá danh
   mục thì máy chủ bỏ qua giá tay (Codex #486 v9), nên không hiện ô giá tay.
   Chưa có kết quả thì theo giá tay đã gõ. MỘT chỗ quyết cho cả lúc vẽ dòng
   và lúc nhận kết quả (Codex #486 v4). */
function gvtCanGiaTay(d, r) {
  if (!d.item_code) return true;
  /* Công thức vòng: máy chủ không nhận giá tay (Codex #486 v10), ô giá tay
     chỉ làm người dùng gõ mãi không hết lỗi (v11). Phải sửa công thức. */
  if (r && r.vong) return false;
  return r ? !!(r.thieu || r.tay) : gvtSoVn(d.don_gia_tay) > 0;
}
function gvtVeKetQua() {
  var el = document.getElementById('gvtpKq');
  if (el) el.innerHTML = gvtKhoiKetQua();
  /* Kết quả mới làm một dòng cần ô giá tay mà dòng đó chưa có: vẽ lại danh
     sách dòng (ô đang gõ giữ chữ vì chữ nằm trong GVT.p). */
  var ds = document.getElementById('gvtpDs');
  var lech = (GVT.p.dong || []).some(function (d, i) {
    return gvtCanGiaTay(d, (GVT.pkDong || [])[i]) && !document.querySelector('[data-gvtpgia="' + i + '"]');
  });
  if (ds && lech) { ds.innerHTML = GVT.p.dong.map(gvtDongNhap).join(''); return; }
  (GVT.p.dong || []).forEach(function (d, i) {
    var o = document.querySelector('[data-gvtpgiadong="' + i + '"]');
    if (o) o.innerHTML = gvtGiaDong(d, (GVT.pkDong || [])[i]);
  });
}

/* Dòng giá của một nguyên liệu: nguồn giá và thành tiền theo kết quả máy chủ. */
function gvtGiaDong(d, r) {
  if (!r) return '<span style="color:#9ca3af">Nhập số lượng để tính</span>';
  return money(r.don_gia) + 'đ/' + h(r.dvt || d.dvt || '') + ' (' + h(r.nguon) + ')' +
    (r.vong ? ' · <span style="color:#b3261e">công thức vòng, sửa trên Desk</span>' : r.thieu ? ' · <span style="color:#b45309">thiếu giá</span>' : '') +
    ' · <b>' + money(r.thanh_tien) + 'đ</b>';
}

function gvtDongNhap(d, i) {
  var r = (GVT.pkDong || [])[i];
  var canGiaTay = gvtCanGiaTay(d, r);
  return '<div class="hub" data-gvtpd="' + i + '" style="align-items:flex-start;cursor:default">' +
    '<div class="hub-t" style="flex:1;min-width:0">' +
      '<div style="display:flex;gap:8px;align-items:center"><div class="t1" style="flex:1;min-width:0">' + h(d.ten || d.item_code) +
        (d.item_code ? '' : ' <span style="font-size:12px;color:#6b7280;font-weight:600">· chưa có mã</span>') + '</div>' +
        '<button class="ic" data-gvtpxoa="' + i + '" aria-label="Bỏ dòng" style="min-width:44px;min-height:44px;color:#b3261e">&times;</button></div>' +
      '<div style="display:flex;gap:8px;align-items:center;margin-top:6px">' +
        '<input class="nt" data-gvtpsl="' + i + '" inputmode="decimal" placeholder="Số lượng" value="' + h(d.so_luong == null ? '' : String(d.so_luong).replace('.', ',')) +
        '" style="width:110px;height:44px;text-align:right;padding:0 10px"><span style="font-size:14px">' + h(d.dvt || '') + '</span>' +
        (canGiaTay ? '<input class="nt" data-gvtpgia="' + i + '" inputmode="numeric" placeholder="Giá tay/' + h(d.dvt || 'đv') + '" value="' +
          h(gvtSoVn(d.don_gia_tay) > 0 ? String(d.don_gia_tay) : '') + '" style="flex:1;min-width:0;height:44px;text-align:right;padding:0 10px">' : '') +
      '</div>' +
      '<div class="t2" data-gvtpgiadong="' + i + '" style="margin-top:4px">' + gvtGiaDong(d, r) + '</div>' +
    '</div></div>';
}

function gvtManPhieu() {
  gvtCss();
  var p = GVT.p;
  /* Mở lại từ bản nháp trên trang chủ: chưa có danh sách nên chưa có nhóm
     bán và quyền. Tải trang đầu rồi vẽ lại nếu vẫn đang ở màn này. */
  if (!GVT.thu) {
    GVT.thu = { nhom_ban: [], sua_duoc: true, ds: [] };
    var man = S.stack[S.stack.length - 1];
    api('vagabond.gia_von_tam.ds_thu', gvtThamSoDs()).then(function (kq) {
      GVT.thu = kq;
      if (S.stack[S.stack.length - 1] === man && GVT.p === p) gvtManPhieu();
    }, function () { });
  }
  var t = GVT.thu || {};
  var sua = t.sua_duoc !== false;
  var html = '<div class="card" style="padding:12px 14px" id="gvtpKq">' + gvtKhoiKetQua() + '</div>' +
    '<div class="card" style="padding:12px 14px">' +
      (p.vet ? gvtDauVet(p.vet, 'margin:0 0 8px') : '') +
      '<div class="t2" style="margin-bottom:4px">Tên món thử</div>' +
      '<input class="tin" id="gvtpTen" placeholder="Ví dụ: Tart chanh dây size 16" value="' + h(p.ten_mon) + '" style="margin:0 0 10px">' +
      '<div class="t2" style="margin-bottom:6px">Nhóm bán dự kiến (để lấy hệ số mục tiêu)</div>' +
      gvtTheNhom(p.nhom, sua) +
      '<div style="display:flex;gap:8px;align-items:flex-end;margin-bottom:10px">' +
        '<div style="flex:1"><div class="t2" style="margin-bottom:4px">Một mẻ ra</div><input class="nt" id="gvtpRa" inputmode="decimal" value="' +
          h(String(p.so_ra).replace('.', ',')) + '" style="width:100%;height:44px;text-align:right;padding:0 10px"></div>' +
        '<div style="flex:1"><div class="t2" style="margin-bottom:4px">Đơn vị</div><input class="nt" id="gvtpDvt" value="' + h(p.dvt_ra) +
          '" style="width:100%;height:44px;padding:0 10px"></div></div>' +
      '<div class="t2" style="margin-bottom:4px">Giá bán dự kiến (không bắt buộc)</div>' +
      '<input class="nt" id="gvtpGb" inputmode="numeric" placeholder="Để trống nếu chưa có" value="' + h(gvtSoVn(p.gia_ban_du_kien) > 0 ? String(p.gia_ban_du_kien) : '') +
        '" style="width:100%;height:44px;text-align:right;padding:0 10px;margin-bottom:10px">' +
      '<div class="t2" style="margin-bottom:4px">Ghi chú</div>' +
      '<textarea class="tin" id="gvtpGc" rows="2" style="margin:0">' + h(p.ghi_chu) + '</textarea>' +
    '</div>' +
    '<div class="sec">Nguyên liệu, số lượng theo đơn vị kho</div>' +
    '<div class="card" id="gvtpDs">' + (p.dong.length ? p.dong.map(gvtDongNhap).join('') :
      '<div class="emp" style="padding:18px"><div>Chưa có nguyên liệu.</div></div>') + '</div>' +
    (sua ? '<button class="btn gh" data-gvtpthem style="margin:0 0 10px">Thêm nguyên liệu</button>' : '') +
    (sua && p.name ? '<button class="btn gh" data-gvtpbo style="margin:0 0 10px;color:#b3261e">Bỏ phiếu</button>' : '');
  var b = frame(GVT_TIEU_DE_THU, html, sua ? { footer: '<button class="btn" id="gvtpLuu">Lưu phiếu</button>' } : {});
  var gan = function (id, k) {
    var o = document.getElementById(id);
    if (o) o.oninput = function () { p[k] = o.value; gvtDanhDau(); if (k !== 'ten_mon' && k !== 'ghi_chu') gvtHenTinh(); };
  };
  gan('gvtpTen', 'ten_mon'); gan('gvtpRa', 'so_ra'); gan('gvtpDvt', 'dvt_ra'); gan('gvtpGb', 'gia_ban_du_kien'); gan('gvtpGc', 'ghi_chu');
  b.oninput = function (e) {
    var o = e.target, i;
    if (o.getAttribute && (i = o.getAttribute('data-gvtpsl')) != null) { p.dong[+i].so_luong = o.value; gvtDanhDau(); gvtHenTinh(); }
    else if (o.getAttribute && (i = o.getAttribute('data-gvtpgia')) != null) { p.dong[+i].don_gia_tay = o.value; gvtDanhDau(); gvtHenTinh(); }
  };
  b.onclick = function (e) {
    var el;
    if (sua && e.target.closest('[data-gvtpnhom]')) return gvtChonNhom();
    if ((el = e.target.closest('[data-gvtpxoa]'))) {
      p.dong.splice(+el.getAttribute('data-gvtpxoa'), 1); gvtDanhDau(); gvtManPhieu(); return gvtTinhLai();
    }
    if (e.target.closest('[data-gvtpthem]')) return gvtThemNl();
    if (e.target.closest('[data-gvtpbo]')) return gvtBoPhieu();
  };
  var l = document.getElementById('gvtpLuu');
  if (l) l.onclick = gvtLuuPhieu;
  if (!GVT.pkDong && p.dong.length) gvtTinhLai();
  return b;
}

/* Nhóm bán của phiếu thử: chín nhóm, hơn 8 lựa chọn nên KHÔNG dùng hàng chip
   mà dùng thẻ giá trị đang chọn (tên đậm, dòng phụ xám, mũi tên), chạm vào
   mở sheet có ô tìm (AGENTS.md 2b điều 2, Codex #486 v7). */
function gvtHeSoNhom(ten) { return (((GVT.thu || {}).he_so) || {})[ten]; }
function gvtTheNhom(ten, sua) {
  var hs = ten ? gvtHeSoNhom(ten) : null;
  var phu = !ten ? 'Chưa chọn. Chọn để có giá bán đề xuất.' : (hs ? 'Hệ số mục tiêu ' + gvtHeSo(hs) : 'Nhóm này chưa đặt hệ số mục tiêu');
  return '<div data-gvtpnhom style="display:flex;align-items:center;gap:10px;min-height:52px;padding:8px 12px;border:1.5px solid #d7dce5;' +
    'border-radius:12px;margin-bottom:10px;' + (sua ? 'cursor:pointer' : '') + '">' +
    '<div style="flex:1;min-width:0"><div style="font-size:15px;font-weight:700;color:' + (ten ? '#101828' : '#6b7280') + '">' +
      h(ten || 'Chọn nhóm bán') + '</div><div style="font-size:13px;color:#6b7280;margin-top:2px">' + h(phu) + '</div></div>' +
    (sua ? '<div style="font-size:20px;color:#9ca3af">›</div>' : '') + '</div>';
}
function gvtChonNhom() {
  var nhom = (GVT.thu || {}).nhom_ban || [];
  var dang = GVT.p.nhom || '';
  var ov = document.createElement('div'); ov.className = 'sh';
  ov.innerHTML = '<div class="shb"><div class="shh"><b>Nhóm bán dự kiến</b><div class="x" data-gvtpndong>&times;</div></div>' +
    '<div style="padding:4px 14px 8px"><input class="tin" data-gvtpntim placeholder="Gõ tên nhóm" style="margin:0"></div>' +
    '<div class="shl" data-gvtpnkq></div></div>';
  document.body.appendChild(ov);
  var vung = ov.querySelector('[data-gvtpnkq]');
  var ve = function (q) {
    var hop = nhom.filter(function (n) { return vgbKhop([n.ten, n.nhan], q); });
    vung.innerHTML = (q ? '' : '<div class="shi' + (!dang ? ' on' : '') + '" data-gvtpnchon=""><span style="flex:1;min-width:0">Chưa chọn nhóm' +
        '<div style="color:#6b7280;font-size:13px">Không có giá bán đề xuất</div></span></div>') +
      (hop.length ? hop.map(function (n) {
        var hs = gvtHeSoNhom(n.ten);
        return '<div class="shi' + (dang === n.ten ? ' on' : '') + '" data-gvtpnchon="' + h(n.ten) + '"><span style="flex:1;min-width:0">' + h(n.ten) +
          '<div style="color:#6b7280;font-size:13px">' + (hs ? 'Hệ số mục tiêu ' + gvtHeSo(hs) : 'Chưa đặt hệ số mục tiêu') + '</div></span>' +
          (dang === n.ten ? '<span>&#10003;</span>' : '') + '</div>';
      }).join('') : '<div style="padding:10px 14px;font-size:13px;color:#6b7280">Không có nhóm nào khớp.</div>');
  };
  ve('');
  var o = ov.querySelector('[data-gvtpntim]');
  o.oninput = function () { ve(o.value); };
  ov.onclick = function (e) {
    if (e.target === ov || e.target.closest('[data-gvtpndong]')) { ov.remove(); return; }
    var el = e.target.closest('[data-gvtpnchon]');
    if (!el) return;
    ov.remove();
    var n = el.getAttribute('data-gvtpnchon') || '';
    if (n === (GVT.p.nhom || '')) return;
    GVT.p.nhom = n; gvtDanhDau(); gvtManPhieu(); return gvtTinhLai();
  };
}

/* Sheet thêm nguyên liệu: gõ tìm mã có sẵn, hoặc ghi NVL chưa có mã. */
function gvtThemNl() {
  var ov = document.createElement('div'); ov.className = 'sh';
  var kq = [];
  ov.innerHTML = '<div class="shb"><div class="shh"><b>Thêm nguyên liệu</b><div class="x" data-gvtndong>&times;</div></div>' +
    '<div style="padding:4px 14px 8px"><input class="tin" data-gvtntim placeholder="Gõ tên hoặc mã nguyên liệu, bán thành phẩm" style="margin:0"></div>' +
    '<div class="shl" data-gvtnkq><div style="padding:10px 14px;font-size:13px;color:#6b7280">Gõ ít nhất 2 chữ để tìm.</div></div>' +
    '<div style="padding:10px 14px 14px;border-top:1px solid #eef0f4">' +
      '<div style="font-size:14px;font-weight:700;margin-bottom:6px">Nguyên liệu chưa có mã</div>' +
      '<div style="display:flex;gap:8px"><input class="nt" data-gvtnmoiten placeholder="Tên nguyên liệu" style="flex:2;min-width:0;height:44px;padding:0 10px">' +
      '<input class="nt" data-gvtnmoidvt placeholder="Đơn vị, ví dụ Gram" style="flex:1;min-width:0;height:44px;padding:0 10px"></div>' +
      '<div data-gvtnsai style="font-size:12.5px;color:#b3261e;margin-top:4px"></div>' +
      '<button class="btn gh" data-gvtnmoi style="margin-top:8px">Thêm nguyên liệu chưa có mã</button></div></div>';
  document.body.appendChild(ov);
  var hen = null;
  var o = ov.querySelector('[data-gvtntim]');
  var them = function (r) {
    GVT.p.dong.push(r); ov.remove(); gvtDanhDau(); gvtManPhieu();
    var sl = document.querySelector('[data-gvtpsl="' + (GVT.p.dong.length - 1) + '"]');
    if (sl && sl.focus) sl.focus();
  };
  o.oninput = function () {
    if (hen) clearTimeout(hen);
    var tu = o.value.trim();
    var vung = ov.querySelector('[data-gvtnkq]');
    if (tu.length < 2) { vung.innerHTML = '<div style="padding:10px 14px;font-size:13px;color:#6b7280">Gõ ít nhất 2 chữ để tìm.</div>'; return; }
    hen = setTimeout(async function () {
      /* Mất mạng hay máy chủ lỗi KHÔNG phải là không có nguyên liệu: báo lỗi
         kèm nút thử lại, không mời ghi dòng chưa có mã (Codex #486 v13). */
      kq = [];
      try { kq = await api('vagabond.gia_von_tam.tim_nl', { tu_khoa: tu }); }
      catch (e) {
        if (o.value.trim() !== tu) return;
        vung.innerHTML = '<div data-gvtnloi style="padding:10px 14px;font-size:13px;color:#b3261e">Chưa tìm được do mất mạng hoặc máy chủ lỗi. ' +
          'Nguyên liệu có thể vẫn có trong danh mục, đừng ghi thành dòng chưa có mã.' +
          '<button class="btn gh" data-gvtnlai style="margin-top:8px;width:100%">Tìm lại</button></div>';
        return;
      }
      if (o.value.trim() !== tu) return;
      vung.innerHTML = kq.length ? kq.map(function (x, i) {
        return '<div class="shi" data-gvtnchon="' + i + '"><span style="flex:1;min-width:0">' + h(x.ten) +
          '<div style="color:#6b7280;font-size:12.5px">' + h(x.ma) + ' · ' + h(x.dvt) + ' · ' + h(x.nhom) + '</div></span></div>';
      }).join('') : '<div style="padding:10px 14px;font-size:13px;color:#6b7280">Không thấy. Ghi vào ô Nguyên liệu chưa có mã bên dưới.</div>';
    }, 300);
  };
  ov.onclick = function (e) {
    if (e.target === ov || e.target.closest('[data-gvtndong]')) { ov.remove(); return; }
    if (e.target.closest('[data-gvtnlai]')) { ov.querySelector('[data-gvtnkq]').innerHTML = '<div style="padding:10px 14px;font-size:13px;color:#6b7280">Đang tìm...</div>'; o.oninput(); return; }
    var el = e.target.closest('[data-gvtnchon]');
    if (el) {
      var x = kq[+el.getAttribute('data-gvtnchon')];
      return them({ item_code: x.ma, ten: x.ten, dvt: x.dvt, so_luong: '', don_gia_tay: '' });
    }
    if (e.target.closest('[data-gvtnmoi]')) {
      var ten = ov.querySelector('[data-gvtnmoiten]').value.trim();
      var dvt = ov.querySelector('[data-gvtnmoidvt]').value.trim();
      if (!ten || !dvt) { ov.querySelector('[data-gvtnsai]').innerHTML = 'Ghi cả tên và đơn vị.'; return; }
      them({ item_code: null, ten: ten, dvt: dvt, so_luong: '', don_gia_tay: '' });
    }
  };
  if (o.focus) o.focus();
}

async function gvtLuuPhieu() {
  var p = GVT.p;
  /* Cùng luật với ô kết quả: mẻ ra trống hoặc 0 thì không gửi (máy chủ tự
     hiểu trống là 1, sẽ lưu sai điều người dùng thấy trên màn). */
  var soRa = gvtSoVn(p.so_ra);
  if (soRa == null || soRa <= 0) return baoTin('Một mẻ phải ra hơn 0. Sửa ô Một mẻ ra rồi bấm Lưu.');
  var gui = {
    name: p.name, phien_ban: p.phien_ban || '', ten_mon: p.ten_mon, nhom: p.nhom, so_ra: gvtSoVn(p.so_ra), dvt_ra: p.dvt_ra,
    gia_ban_du_kien: gvtSoVn(p.gia_ban_du_kien) || 0, ghi_chu: p.ghi_chu,
    dong: p.dong.map(function (d) {
      return { item_code: d.item_code, ten: d.ten, dvt: d.dvt, so_luong: gvtSoVn(d.so_luong), don_gia_tay: gvtSoVn(d.don_gia_tay) || 0 };
    })
  };
  var kq;
  busy(true);
  try { kq = await api('vagabond.gia_von_tam.luu_thu', { phieu: JSON.stringify(gui) }); busy(false); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Lưu phiếu lỗi'); }
  vgbBoChuaLuu();
  toast('Đã lưu phiếu ' + kq.name, 3000);
  GVT.thu = null; GVT.p = null; GVT.pk = null; GVT.pkDong = null; GVT.lan++;
  GVT.tab = 'thu';
  back();
}

/* Bỏ phiếu là bỏ MỀM (QT-20, Codex #486): phiếu ẩn khỏi danh sách, vẫn giữ
   trên hệ thống cùng người bỏ và lúc bỏ. */
async function gvtBoPhieu() {
  var p = GVT.p;
  if (!await confirmSheet('Bỏ phiếu', 'Bỏ phiếu tính giá thử "' + p.ten_mon + '"? Phiếu ẩn khỏi danh sách nhưng vẫn giữ trên hệ thống để tra lại. ' +
    'Không ảnh hưởng mã hàng, công thức hay sổ sách.', 'Bỏ phiếu', true)) return;
  busy(true);
  /* Gửi bản đang mở: bản nháp cũ hay tab để lâu không được bỏ âm thầm một
     bản người khác vừa sửa (Codex #486 v13). */
  try { await api('vagabond.gia_von_tam.bo_thu', { name: p.name, phien_ban: p.phien_ban || '' }); busy(false); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Bỏ phiếu lỗi'); }
  vgbBoChuaLuu();
  toast('Đã bỏ phiếu. Vẫn tra lại được trên Desk.', 3000);
  GVT.thu = null; GVT.p = null; GVT.pk = null; GVT.pkDong = null; GVT.lan++;
  GVT.tab = 'thu';
  back();
}

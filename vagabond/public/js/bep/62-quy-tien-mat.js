/* ---------------- Quỹ tiền mặt công ty (v628)

   Anh Việt 02/11/2026: "các bên nộp tiền về thì cộng vào + chị Dung có thể sửa (có
   ghi record) rồi khi nộp tiền mặt vào tài khoản thì hệ thống có chỗ cho chị ấy
   chuyển". Anh duyệt ảnh mẫu 4 màn cùng ngày; lệch quá 2 triệu thì anh duyệt.

   Mọi con số do máy chủ tính (vagabond/quy_tien_mat.py), màn chỉ vẽ. Không có ô
   nào gõ tay số dư quỹ: muốn sửa thì Kiểm quỹ, đếm theo mệnh giá, ghi lý do. */
var QTM = null;          /* dữ liệu màn chính lần đọc gần nhất */
var QTM_DEM = {};        /* bảng đếm đang gõ dở: {mệnh giá: số tờ} */
var QTM_LY_DO = '';
var QTM_NOP = { tk: '' };

function qtmLaiQuyen() { return !!(QTM && QTM.duoc_lam); }
function qtmTien(v) { return money(v) + ' đ'; }
function qtmDau(v) { v = Number(v) || 0; return (v > 0 ? '+' : v < 0 ? '-' : '') + money(Math.abs(v)); }
function qtmNgayGio(s) { s = String(s || ''); return s.length >= 16 ? s.slice(8, 10) + '/' + s.slice(5, 7) + ' ' + s.slice(11, 16) : tcNgay(s); }

async function scrQuyTm() {
  var td = 'Quỹ tiền mặt công ty';
  tcDoi(td, 'Đang tính tiền trong quỹ...');
  try { QTM = await api('vagabond.quy_tien_mat.man_quy', {}); } catch (e) { return tcLoi(td, e); }
  var q = QTM, html = '';
  html += '<div class="card" style="padding:14px"><div style="font-size:12.5px;color:#667085">Tiền đang có trong quỹ</div>';
  if (q.so_du === null || q.so_du === undefined) {
    /* v635 (anh Việt 03/11/2026): chị Dung thấy dòng này mà không có chỗ bấm, vì nút
       chốt nằm ở Cài đặt tài chính chỉ mở cho người Giám đốc chọn. Người làm quỹ chốt
       ngay ở đây bằng bảng đếm mệnh giá, một lần duy nhất. */
    html += '<div style="font-size:15px;font-weight:700;color:#b54708;margin-top:4px">Quỹ chưa chốt số dư đầu</div>' +
      '<div style="font-size:12.5px;color:#475467;margin-top:4px">' + (q.duoc_lam
        ? 'Đếm toàn bộ tiền trong quỹ theo mệnh giá rồi bấm chốt. Từ đó app tự cộng biên nhận nộp tiền, trừ khoản chi.'
        : 'Nhờ kế toán hoặc Giám đốc đếm quỹ và chốt số dư đầu trên màn này.') + '</div>' +
      (q.duoc_lam ? '<button class="btn" data-qtmchot="1" style="width:100%;margin:10px 0 0;min-height:48px">Chốt số dư đầu quỹ</button>' : '');
  } else {
    html += '<div data-qtmso="1" style="font-size:30px;font-weight:800;color:#0f7a6b;line-height:1.25">' + money(q.so_du) + '</div>';
    var l = q.lan_kiem;
    if (l) {
      var lc = Number(l.lech) || 0;
      html += tcChip(lc ? '#fffaeb' : '#ecfdf3', lc ? '#b54708' : '#067647',
        'Kiểm quỹ ' + qtmNgayGio(l.luc) + ' · ' + h(l.ten_nguoi || '') + ' · ' + (lc ? 'lệch ' + qtmDau(lc) : 'khớp') +
        (l.trang_thai === 'Chờ duyệt' ? ' · chờ duyệt' : ''));
    } else {
      html += tcChip('#f2f4f7', '#475467', 'Chưa kiểm quỹ lần nào');
    }
  }
  html += '</div>';
  if (q.duoc_lam && q.so_du !== null && q.so_du !== undefined) {
    html += '<div style="display:flex;gap:10px;margin-bottom:10px"><button class="btn" data-qtmkiem="1" style="flex:1;margin:0;min-height:48px">Kiểm quỹ</button>' +
      '<button class="btn" data-qtmnop="1" style="flex:1;margin:0;min-height:48px">Nộp vào ngân hàng</button></div>';
  }
  (q.cho_duyet || []).forEach(function (c) {
    var lc = Number(c.lech) || 0;
    html += '<div class="card" data-qtmcho="' + h(c.name) + '" style="padding:13px;border:1px solid #f3c3be">' +
      '<div style="font-size:12.5px;color:#667085">' + h(c.ten_nguoi || '') + ' kiểm quỹ ' + qtmNgayGio(c.luc) + '</div>' +
      '<div style="font-size:24px;font-weight:800;color:' + (lc < 0 ? '#b42318' : '#067647') + '">' + qtmDau(lc) + '</div>' +
      tcChip('#fef3f2', '#b42318', (lc < 0 ? 'Thiếu' : 'Thừa') + ' · quá mức ' + money(q.nguong)) +
      '<div style="display:flex;justify-content:space-between;font-size:13.5px;margin-top:8px"><span>Máy tính</span><span>' + money(c.so_may) + '</span></div>' +
      '<div style="display:flex;justify-content:space-between;font-size:13.5px"><span>Đếm được</span><span>' + money(c.so_dem) + '</span></div>' +
      '<div style="font-size:13px;margin-top:6px">Lý do: ' + h(c.ly_do_ten || '') + (c.ghi_chu ? '<div style="color:#667085">"' + h(c.ghi_chu) + '"</div>' : '') + '</div>' +
      ((c.anh || []).length ? '<div style="font-size:12.5px;margin-top:4px">' + c.anh.map(function (u, i) {
        return '<a href="' + h(u) + '" target="_blank" style="margin-right:10px">Ảnh ' + (i + 1) + '</a>'; }).join('') + '</div>' : '') +
      ((q.ba_lan || []).length ? '<div style="font-size:12px;color:#667085;margin-top:4px">Ba lần kiểm gần nhất: ' + q.ba_lan.map(function (x) {
        return tcNgay(x.ngay).slice(0, 5) + ' ' + (Number(x.lech) ? qtmDau(x.lech) : 'khớp'); }).join(' · ') + '</div>' : '') +
      (q.duoc_duyet && c.nguoi !== q.toi
        ? '<button class="btn" data-qtmduyet="' + h(c.name) + '" style="width:100%;margin:10px 0 0;min-height:46px">Duyệt, ghi nhận chênh lệch</button>' +
          '<button class="btn gh" data-qtmtra="' + h(c.name) + '" style="width:100%;margin:8px 0 0;min-height:46px">Trả lại, nhờ đếm lại</button>'
        : '<div style="font-size:12.5px;color:#b54708;margin-top:8px">Chờ Giám đốc duyệt. Quỹ vẫn hiện số cũ tới khi duyệt.</div>') +
      '</div>';
  });
  html += '<div class="sec">Gần đây</div><div class="card" style="padding:0">';
  if (!(q.lich_su || []).length) html += '<div style="padding:12px 13px;font-size:13px;color:#667085">Chưa có khoản nào sau mốc chốt.</div>';
  (q.lich_su || []).forEach(function (x) {
    var mau = x.cho ? '#b54708' : (Number(x.tien) >= 0 ? '#067647' : '#b42318');
    html += '<div style="display:flex;gap:10px;padding:10px 13px;border-top:1px solid #f1f5f9;min-height:44px">' +
      '<div style="flex:1;min-width:0"><b style="font-size:14px">' + qtmNgayGio(x.luc) + ' · ' + h(x.ten) + '</b>' +
      (x.phu ? '<div style="font-size:12.5px;color:#667085">' + h(x.phu) + '</div>' : '') +
      (x.chip ? '<div>' + tcChip(x.chip === 'Đã khớp SePay' ? '#ecfdf3' : '#fffaeb', x.chip === 'Đã khớp SePay' ? '#067647' : '#b54708', h(x.chip)) + '</div>' : '') +
      (qtmDuocHuy(x, q) ? '<button class="btn gh" data-qtmhuy="' + h(x.ma) + '" data-qtmhuyloai="' + h(x.huy) + '" style="width:auto;margin:6px 0 0;min-height:44px;padding:4px 12px;font-size:13px">Huỷ phiếu</button>' : '') +
      '</div><div style="flex:0 0 auto;font-weight:800;white-space:nowrap;color:' + mau + '">' + qtmDau(x.tien) + '</div></div>';
  });
  html += '</div>';
  if (q.duoc_lam) {
    html += '<details class="card" style="padding:11px 13px;font-size:13px"><summary style="font-weight:700;min-height:32px">Tài khoản hạch toán quỹ</summary>' +
      '<div style="color:#475467;margin:4px 0 6px">Chọn một lần. Để trống thì máy dùng tài khoản gợi ý.</div>' +
      [['tk_quy', 'Quỹ tiền mặt (111x)'], ['tk_thieu', 'Tiền thiếu chờ xử lý'], ['tk_thua', 'Tiền thừa chờ giải quyết']].map(function (k) {
        var t = (q.tk || {})[k[0]] || {};
        return '<div style="display:flex;gap:10px;align-items:center;padding:8px 0;border-top:1px solid #f1f5f9">' +
          '<div style="flex:1;min-width:0"><b>' + k[1] + '</b><div style="font-size:12.5px;color:#667085">' +
          (t.ma ? h(t.ten) : (t.goi_y ? 'Đang dùng gợi ý: ' + h(t.ten_goi_y) : '<span style="color:#b42318">Chưa có tài khoản</span>')) + '</div></div>' +
          '<button class="btn gh" data-qtmtk="' + k[0] + '" style="width:auto;margin:0;min-height:44px;padding:4px 12px">Chọn</button></div>';
      }).join('') + '</details>';
  }
  html += '<details class="card" style="padding:11px 13px;font-size:13px;color:#475467;line-height:1.6"><summary style="font-weight:700;color:#101828;min-height:32px">Cách tính</summary>' +
    '<div>Số dư đầu đã chốt (đếm trên màn này hoặc ở Cài đặt tài chính), cộng biên nhận nộp tiền mặt đã ký nhận, cộng trừ phiếu thu chi và bút toán tiền mặt trên sổ cái (trừ tiền đã tính ở két quầy).</div>' +
    '<div>Kiểm quỹ lệch thì máy lập bút toán chênh lệch, lệch quá ' + money(q.nguong) + ' đ chờ Giám đốc duyệt.</div>' +
    '<div>Nộp vào ngân hàng trừ quỹ ngay; tiền về tài khoản thì máy tự ghép giao dịch SePay cùng số tiền.</div></details>';
  var than = frame(td, html);
  var b = than.querySelector('[data-qtmchot]');
  if (b) b.onclick = function () { QTM_DEM = {}; go(scrQuyChotDau); };
  b = than.querySelector('[data-qtmkiem]');
  if (b) b.onclick = function () { QTM_DEM = {}; QTM_LY_DO = ''; tdkXoaHet(); go(scrQuyKiem); };
  b = than.querySelector('[data-qtmnop]');
  if (b) b.onclick = function () { QTM_NOP = { tk: ((q.tai_khoan_nh || [])[0] || {}).ma || '' }; tdkXoaHet(); go(scrQuyNop); };
  than.querySelectorAll('[data-qtmduyet]').forEach(function (n) {
    n.onclick = async function () {
      var ok = await hoiCo('Duyệt kiểm quỹ', 'Máy lập bút toán chênh lệch và quỹ đổi theo số đếm. Không hoàn tác bằng nút này.', 'Duyệt');
      if (!ok) return;
      try { await api('vagabond.quy_tien_mat.duyet_kiem_quy', { name: n.getAttribute('data-qtmduyet'), dong_y: 1 }); } catch (e) { toast(errMsg(e)); return; }
      toast('Đã duyệt, quỹ đã đổi theo số đếm');
      go(scrQuyTm, true);
    };
  });
  than.querySelectorAll('[data-qtmtra]').forEach(function (n) {
    n.onclick = async function () {
      var ly = await hoiChu('Trả lại phiếu kiểm quỹ', 'Ghi lý do để người kiểm biết cần đếm lại chỗ nào.', '', { bat_buoc: 1, nhieu_dong: 1 });
      if (!ly) return;
      try { await api('vagabond.quy_tien_mat.duyet_kiem_quy', { name: n.getAttribute('data-qtmtra'), dong_y: 0, ly_do: ly }); } catch (e) { toast(errMsg(e)); return; }
      toast('Đã trả lại, quỹ giữ số cũ');
      go(scrQuyTm, true);
    };
  });
  /* Codex #527 vòng 6: phiếu ghi nhầm (số tiền, tài khoản nhận) huỷ ngay từ lịch sử
     để máy hoàn bút toán, nhả giao dịch ngân hàng, rồi lập lại phiếu đúng. */
  than.querySelectorAll('[data-qtmhuy]').forEach(function (n) {
    n.onclick = async function () {
      var ma = n.getAttribute('data-qtmhuy'), nop = n.getAttribute('data-qtmhuyloai') === 'nop';
      var ly = await hoiChu('Huỷ phiếu ' + ma, 'Ghi lý do huỷ. Máy huỷ bút toán nên quỹ trở lại như trước phiếu này' +
        (nop ? '; giao dịch ngân hàng đã ghép được nhả ra. Sau đó lập lại phiếu nộp đúng.' : '.'), '', { bat_buoc: 1 });
      if (!ly) return;
      try { await api('vagabond.quy_tien_mat.huy_phieu', { name: ma, ly_do: ly }); } catch (e) { toast(errMsg(e)); return; }
      toast('Đã huỷ phiếu ' + ma + (nop ? '. Lập lại phiếu nộp đúng nếu cần.' : ''));
      go(scrQuyTm, true);
    };
  });
  than.querySelectorAll('[data-qtmtk]').forEach(function (n) {
    n.onclick = async function () {
      var k = n.getAttribute('data-qtmtk');
      var tu = await hoiChu('Tìm tài khoản', 'Gõ số hiệu hoặc tên, ví dụ ' + (k === 'tk_quy' ? '1111' : k === 'tk_thieu' ? '1381' : '3381') + '.', '', { bat_buoc: 1 });
      if (!tu) return;
      var ds;
      try { ds = await api('vagabond.quy_tien_mat.tim_tai_khoan', { tu_khoa: tu }); } catch (e) { toast(errMsg(e)); return; }
      if (!(ds || []).length) return toast('Không thấy tài khoản nào khớp "' + tu + '".');
      sheet('Chọn tài khoản', ds.map(function (x) { return { label: x.ten, value: x.ma }; }), '', async function (v) {
        var ts = {}; ts[k] = v;
        try { await api('vagabond.quy_tien_mat.luu_tai_khoan', ts); } catch (e) { toast(errMsg(e)); return; }
        toast('Đã lưu tài khoản');
        go(scrQuyTm, true);
      });
    };
  });
}

/* Dòng lịch sử có nút Huỷ phiếu không. THUẦN. Phiếu nộp: người làm quỹ; phiếu kiểm
   đã ghi: chỉ Giám đốc (máy chủ cũng chặn như vậy). */
function qtmDuocHuy(x, q) {
  if (!x || !x.huy) return false;
  return x.huy === 'nop' ? !!(q && q.duoc_lam) : x.huy === 'kiem' ? !!(q && q.duoc_duyet) : false;
}

/* Đã gõ ít nhất một ô (kể cả số 0) thì là đã đếm. THUẦN. */
function qtmDaDem(dem) {
  return Object.keys(dem || {}).some(function (mg) { return String(dem[mg] === undefined || dem[mg] === null ? '' : dem[mg]).trim() !== ''; });
}

/* Số đếm và lệch của bảng đang gõ. THUẦN để ca kiểm gọi được. */
function qtmTinhDem(dem, soMay) {
  var tong = 0;
  Object.keys(dem || {}).forEach(function (mg) { tong += (parseInt(mg, 10) || 0) * (parseInt(dem[mg], 10) || 0); });
  return { dem: tong, lech: tong - (Number(soMay) || 0) };
}

/* Màn lập phiếu mở thẳng (thẻ bản nháp trên trang chủ sau khi tải lại app) thì
   QTM còn null: hỏi lại máy chủ trước khi xét quyền, không thì rơi vào màn khoá
   (Codex #527 vòng 3). Trả về false khi lỗi đã hiện. */
async function qtmNap(td) {
  if (QTM) return true;
  tcDoi(td, 'Đang tính tiền trong quỹ...');
  try { QTM = await api('vagabond.quy_tien_mat.man_quy', {}); } catch (e) { tcLoi(td, e); return false; }
  return true;
}

/* Bảng gõ số tờ theo mệnh giá: dùng chung cho Kiểm quỹ và Chốt số dư đầu (v635). */
function qtmBangDem(menhGia) {
  return (menhGia || []).map(function (mg) {
    return '<div style="display:flex;align-items:center;gap:10px;padding:5px 0;border-top:1px solid #f1f5f9">' +
      '<span style="flex:1">' + money(mg) + '</span>' +
      '<input class="tin" data-qtmmg="' + mg + '" inputmode="numeric" placeholder="0" value="' + h(QTM_DEM[mg] || '') + '" style="width:80px;height:44px;margin:0;text-align:center">' +
      '<span data-qtmtt="' + mg + '" style="width:110px;text-align:right">' + money(mg * (parseInt(QTM_DEM[mg], 10) || 0)) + '</span></div>';
  }).join('');
}
function qtmNoiBangDem(than, veTong) {
  than.oninput = function (e) {
    var o = e.target.closest('[data-qtmmg]');
    if (!o) return;
    var mg = o.getAttribute('data-qtmmg');
    var v = String(o.value || '').replace(/[^0-9]/g, '');
    if (v !== o.value) o.value = v;
    QTM_DEM[mg] = v;
    var tt = than.querySelector('[data-qtmtt="' + mg + '"]');
    if (tt) tt.textContent = money((parseInt(mg, 10) || 0) * (parseInt(v, 10) || 0));
    veTong();
  };
}

/* Chốt số dư đầu quỹ (v635): chỉ khi quỹ chưa có mốc. Đếm theo mệnh giá như Kiểm quỹ,
   không có ô gõ tay số dư. Máy chủ quy số đếm về số cuối hôm qua (quy_tien_mat.so_du_cuoi_hom_qua) nên
   khoản ghi sau lúc chốt trong ngày vẫn cộng trừ tiếp (Codex #536 vòng 1). */
async function scrQuyChotDau() {
  var td = 'Chốt số dư đầu quỹ';
  if (!(await qtmNap(td))) return;
  if (!qtmLaiQuyen()) return tcKhoa(td);
  var q = QTM;
  if (q.so_du !== null && q.so_du !== undefined) {
    frame(td, '<div class="card" style="padding:14px;font-size:13.5px;line-height:1.5">Quỹ đã chốt số dư đầu. Muốn sửa số quỹ thì quay lại bấm Kiểm quỹ.</div>');
    return;
  }
  var html = '<div class="card" style="padding:12px 13px"><b>Đếm toàn bộ tiền trong quỹ</b>' +
    '<div style="font-size:12.5px;color:#667085;margin:2px 0 8px">Gõ số tờ từng loại. Quỹ trống thì gõ 0.</div>' +
    qtmBangDem(q.menh_gia) +
    '<div id="qtmTong" style="margin-top:10px"></div>' +
    '<input class="tin" id="qtmGhiChuChot" placeholder="Ghi thêm (nếu có), ví dụ: đếm cùng quản lý cửa hàng" style="width:100%;height:44px;box-sizing:border-box;margin-top:10px"></div>' +
    '<div class="card" style="padding:11px 13px;font-size:13px;color:#475467;line-height:1.6">' +
    '<div>Đếm lúc nào trong ngày cũng được. Khoản đã ký nhận hay đã chi trước lúc đếm nằm sẵn trong số đếm; khoản ghi sau lúc chốt app cộng trừ tiếp.</div>' +
    '<div>Chỉ chốt một lần. Sau đó muốn sửa số quỹ thì Kiểm quỹ.</div></div>' +
    '<button class="btn" data-qtmchotluu="1" style="width:100%;min-height:48px">Chốt số dư đầu</button>';
  var than = frame(td, html);
  function veTong() {
    var t = qtmTinhDem(QTM_DEM, 0);
    document.getElementById('qtmTong').innerHTML =
      '<div data-qtmdem="' + t.dem + '" style="display:flex;justify-content:space-between;font-size:15px;font-weight:800"><span>Đếm được</span><span>' + money(t.dem) + '</span></div>';
  }
  veTong();
  qtmNoiBangDem(than, veTong);
  var dangGui = false;
  than.querySelector('[data-qtmchotluu]').onclick = async function () {
    if (dangGui) return;
    if (!qtmDaDem(QTM_DEM)) return toast('Gõ số tờ đã đếm được. Quỹ trống thì gõ 0.');
    var t = qtmTinhDem(QTM_DEM, 0);
    dangGui = true;
    var ok = await hoiCo('Chốt quỹ ' + money(t.dem) + ' đ', 'Số này thành số dư đầu của quỹ, chỉ chốt một lần. Sau đó muốn sửa thì Kiểm quỹ.', 'Chốt số dư đầu');
    if (!ok) { dangGui = false; return; }
    var kq;
    try {
      kq = await api('vagabond.quy_tien_mat.chot_dau', { bang: JSON.stringify(QTM_DEM),
        ghi_chu: (document.getElementById('qtmGhiChuChot') || {}).value || '' });
    } catch (e) { dangGui = false; toast(errMsg(e)); return; }
    QTM_DEM = {};
    toast('Đã chốt quỹ ' + money(kq.so_du) + ' đ');
    back();
  };
}

async function scrQuyKiem() {
  var td = 'Kiểm quỹ';
  if (!(await qtmNap(td))) return;
  if (!qtmLaiQuyen()) return tcKhoa(td);
  var q = QTM;
  var html = '<div class="card" style="padding:12px 13px"><b>Đếm theo mệnh giá</b>' +
    '<div style="font-size:12.5px;color:#667085;margin:2px 0 8px">Gõ số tờ từng loại. Máy cộng và so với số quỹ máy đang tính.</div>' +
    qtmBangDem(q.menh_gia) +
    '<div id="qtmTong" style="margin-top:10px"></div></div>' +
    '<div class="card" id="qtmLyDoKhoi" style="padding:12px 13px;display:none"><b>Lý do lệch</b><div style="margin-top:6px">' +
    q.ly_do.map(function (x) {
      return '<button class="btn gh" data-qtmly="' + h(x.ma) + '" style="width:auto;margin:0 6px 6px 0;min-height:40px;padding:4px 12px' +
        (QTM_LY_DO === x.ma ? ';background:#dff3f1;border-color:#3d8b9a;color:#0f6b5e' : '') + '">' + h(x.ten) + '</button>';
    }).join('') + '</div>' +
    '<input class="tin" id="qtmGhiChu" placeholder="Ghi thêm, ví dụ: trả tiền ga 2 bình, phiếu chi giấy chưa nhập" style="width:100%;height:44px;box-sizing:border-box;margin-top:4px">' +
    tdkKhoi('qtmAnh', { nhan: '📎 Ảnh chứng từ (nếu có)', goi_y: 'Phiếu chi giấy, hoá đơn lẻ giải thích khoản lệch.' }) +
    '<div id="qtmCanhBao" style="display:none;margin-top:10px;background:#fffaeb;border:1px solid #fedf89;color:#93370d;border-radius:10px;padding:10px 12px;font-size:13px"></div></div>' +
    '<button class="btn" data-qtmluu="1" style="width:100%;min-height:48px">Lưu kiểm quỹ</button>';
  var than = frame(td, html);
  tdkNoi(than, 'qtmAnh', { nhan: '📎 Ảnh chứng từ (nếu có)', goi_y: 'Phiếu chi giấy, hoá đơn lẻ giải thích khoản lệch.' });
  function veTong() {
    var t = qtmTinhDem(QTM_DEM, q.so_du);
    var lc = t.lech;
    document.getElementById('qtmTong').innerHTML =
      '<div style="display:flex;justify-content:space-between;font-size:14px"><span>Máy tính quỹ đang có</span><span>' + money(q.so_du) + '</span></div>' +
      '<div style="display:flex;justify-content:space-between;font-size:14px"><span>Đếm được</span><span>' + money(t.dem) + '</span></div>' +
      '<div data-qtmlech="' + lc + '" style="display:flex;justify-content:space-between;font-size:15px;font-weight:800;color:' + (lc ? (lc < 0 ? '#b42318' : '#067647') : '#067647') + '">' +
      '<span>' + (lc ? (lc < 0 ? 'Thiếu' : 'Thừa') : 'Khớp') + '</span><span>' + (lc ? qtmDau(lc) : '0') + '</span></div>';
    document.getElementById('qtmLyDoKhoi').style.display = lc ? 'block' : 'none';
    var cb = document.getElementById('qtmCanhBao');
    if (Math.abs(lc) > q.nguong) {
      cb.style.display = 'block';
      cb.innerHTML = 'Lệch quá ' + money(q.nguong) + ' nên phiếu gửi Giám đốc duyệt. Quỹ vẫn hiện ' + money(q.so_du) + ' tới khi duyệt.';
    } else if (lc) {
      cb.style.display = 'block';
      cb.innerHTML = 'Lệch từ ' + money(q.nguong) + ' trở xuống: máy ghi ngay bút toán chênh lệch, Ban giám đốc thấy trong tin cuối ngày.';
    } else cb.style.display = 'none';
  }
  veTong();
  qtmNoiBangDem(than, veTong);
  than.querySelectorAll('[data-qtmly]').forEach(function (n) {
    n.onclick = function () {
      QTM_LY_DO = n.getAttribute('data-qtmly');
      than.querySelectorAll('[data-qtmly]').forEach(function (m) {
        var on = m.getAttribute('data-qtmly') === QTM_LY_DO;
        m.style.background = on ? '#dff3f1' : ''; m.style.borderColor = on ? '#3d8b9a' : ''; m.style.color = on ? '#0f6b5e' : '';
      });
    };
  });
  var dangGui = false;
  than.querySelector('[data-qtmluu]').onclick = async function () {
    if (dangGui) return;
    var t = qtmTinhDem(QTM_DEM, q.so_du);
    /* Codex #527 vòng 4: chưa gõ ô nào là chưa đếm; gõ 0 là đã đếm và quỹ rỗng. */
    if (!qtmDaDem(QTM_DEM)) return toast('Gõ số tờ đã đếm được. Két trống thì gõ 0.');
    if (t.lech && !QTM_LY_DO) return toast('Quỹ lệch: chọn lý do lệch.');
    if (!t.dem) {
      dangGui = true;
      var rong = await hoiCo('Quỹ đếm được 0 đồng', 'Máy ghi két đang trống, lệch ' + qtmDau(t.lech) + ' so với số quỹ máy tính.', 'Ghi quỹ rỗng');
      dangGui = false;
      if (!rong) return;
    }
    dangGui = true;
    var kq;
    try {
      kq = await api('vagabond.quy_tien_mat.kiem_quy', { bang: JSON.stringify(QTM_DEM), ly_do: QTM_LY_DO,
        ghi_chu: (document.getElementById('qtmGhiChu') || {}).value || '', anh: JSON.stringify(tdkDs('qtmAnh')) });
    } catch (e) { dangGui = false; toast(errMsg(e)); return; }
    tdkXoaHet();
    toast(kq.trang_thai === 'Khớp' ? 'Quỹ khớp, đã ghi lần kiểm' : kq.trang_thai === 'Chờ duyệt'
      ? 'Đã gửi Giám đốc duyệt khoản lệch ' + qtmDau(kq.lech) : 'Đã ghi chênh lệch ' + qtmDau(kq.lech));
    back();
  };
}

async function scrQuyNop() {
  var td = 'Nộp tiền mặt vào ngân hàng';
  if (!(await qtmNap(td))) return;
  if (!qtmLaiQuyen()) return tcKhoa(td);
  var q = QTM;
  var html = '<div class="card" style="padding:12px 13px">' +
    '<label style="font-size:13px;font-weight:700">Số tiền *</label>' +
    '<input class="tin" id="qtmSoTien" inputmode="numeric" placeholder="Ví dụ 20.000.000" value="' + h(QTM_NOP.so || '') + '" style="width:100%;height:46px;box-sizing:border-box;margin:4px 0">' +
    '<div style="font-size:12.5px;color:#667085">Quỹ đang có ' + qtmTien(q.so_du) + '</div>' +
    '<label style="font-size:13px;font-weight:700;display:block;margin-top:10px">Nộp vào tài khoản *</label><div style="margin-top:4px">' +
    (q.tai_khoan_nh || []).map(function (x) {
      return '<button class="btn gh" data-qtmnh="' + h(x.ma) + '" style="width:auto;margin:0 6px 6px 0;min-height:40px;padding:4px 12px' +
        (QTM_NOP.tk === x.ma ? ';background:#dff3f1;border-color:#3d8b9a;color:#0f6b5e' : '') + '">🏦 ' + h(x.ten) + '</button>';
    }).join('') + '</div>' +
    '<label style="font-size:13px;font-weight:700;display:block;margin-top:6px">Ngày nộp *</label>' +
    '<input class="tin" id="qtmNgay" type="date" max="' + h(q.hom_nay) + '" value="' + h(QTM_NOP.ngay || q.hom_nay) + '" style="width:100%;height:46px;box-sizing:border-box;margin:4px 0">' +
    tdkKhoi('qtmGiayNop', { tieu_de: 'ẢNH GIẤY NỘP TIỀN *', nhan: '📎 Chụp giấy nộp tiền của ngân hàng', goi_y: 'Bắt buộc. Kế toán đối chiếu khi tiền về.' }) +
    '<label style="font-size:13px;font-weight:700;display:block;margin-top:10px">Người mang đi nộp</label>' +
    '<input class="tin" id="qtmNguoiNop" placeholder="Để trống là tên bạn" style="width:100%;height:46px;box-sizing:border-box;margin:4px 0"></div>' +
    '<button class="btn" data-qtmnopluu="1" style="width:100%;min-height:48px">Lưu và trừ quỹ</button>' +
    '<div class="card" style="padding:11px 13px;font-size:13px;color:#475467;line-height:1.6;margin-top:10px">Lưu xong quỹ trừ ngay. Tiền về tài khoản thì máy tự ghép giao dịch SePay cùng số tiền (chip Đã khớp SePay); qua 2 ngày chưa thấy thì nhóm Zalo Kế toán nhận tin nhắc.</div>';
  var than = frame(td, html);
  tdkNoi(than, 'qtmGiayNop', { tieu_de: 'ẢNH GIẤY NỘP TIỀN *', nhan: '📎 Chụp giấy nộp tiền của ngân hàng', goi_y: 'Bắt buộc. Kế toán đối chiếu khi tiền về.' });
  than.querySelectorAll('[data-qtmnh]').forEach(function (n) {
    n.onclick = function () {
      QTM_NOP.tk = n.getAttribute('data-qtmnh');
      than.querySelectorAll('[data-qtmnh]').forEach(function (m) {
        var on = m.getAttribute('data-qtmnh') === QTM_NOP.tk;
        m.style.background = on ? '#dff3f1' : ''; m.style.borderColor = on ? '#3d8b9a' : ''; m.style.color = on ? '#0f6b5e' : '';
      });
    };
  });
  var dangGui = false;
  than.querySelector('[data-qtmnopluu]').onclick = async function () {
    if (dangGui) return;
    var so = (document.getElementById('qtmSoTien') || {}).value || '';
    if (!String(so).replace(/[^0-9]/g, '')) return toast('Gõ số tiền mang đi nộp.');
    if (!QTM_NOP.tk) return toast('Chọn tài khoản nhận tiền.');
    if (!tdkDs('qtmGiayNop').length) return toast('Chụp ảnh giấy nộp tiền của ngân hàng.');
    var ok = await hoiCo('Nộp ' + money(String(so).replace(/[^0-9]/g, '')) + ' đ vào ngân hàng',
      'Quỹ trừ ngay số này và máy lập bút toán Nợ ngân hàng, Có quỹ tiền mặt.', 'Lưu và trừ quỹ');
    if (!ok) return;
    dangGui = true;
    var kq;
    try {
      kq = await api('vagabond.quy_tien_mat.nop_ngan_hang', { so_tien: so, bank_account: QTM_NOP.tk,
        ngay: (document.getElementById('qtmNgay') || {}).value || '', anh: JSON.stringify(tdkDs('qtmGiayNop')),
        nguoi_nop: (document.getElementById('qtmNguoiNop') || {}).value || '' });
    } catch (e) { dangGui = false; toast(errMsg(e)); return; }
    tdkXoaHet();
    toast(kq.trang_thai === 'Đã khớp' ? 'Đã trừ quỹ, tiền đã về tài khoản (khớp SePay)' : 'Đã trừ quỹ, chờ tiền về tài khoản');
    back();
  };
}

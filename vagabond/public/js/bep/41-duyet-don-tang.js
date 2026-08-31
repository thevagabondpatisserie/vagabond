/* ---------------- Duyệt đơn hàng tặng, phân hệ Kế toán

   Anh Việt giao 31/08/2026:

     *"Anh đang muốn làm thêm 1 phương thức thanh toán nữa là 'Hàng tặng'.
     Máy sẽ cho ghi sổ mà không cần đối soát, xuất hoá đơn nguyên giá sản
     phẩm và ghi trên hoá đơn ở phần ghi chú khi xuất hoá đơn. Nhưng với
     những đơn chọn phương thức này thì em cho anh luồng gửi giám đốc duyệt
     đơn được không để tránh gian lận. Lập 1 màn duyệt đơn tặng bên phân hệ
     kế toán để anh vào duyệt thì đơn sẽ để đó chờ ghi sổ."*

   MÀN NÀY LÀ CỬA CHẶN, KHÔNG PHẢI MÀN THÔNG BÁO
   ---------------------------------------------
   Đơn trả bằng Hàng tặng KHÔNG ghi sổ được cho tới khi có người bấm Duyệt ở
   đây. Chặn thật nằm ở máy chủ (`hang_tang.truoc_khi_ghi_so`), màn này chỉ
   là chỗ bấm. Giấu nút đi không phải là chặn.

   DUYỆT THÌ PHẢI THẤY MÌNH ĐANG DUYỆT CÁI GÌ
   ------------------------------------------
   Bấm vào một đơn là mở ra từng dòng hàng, kèm con số "người lập này đã
   tặng bao nhiêu trong tháng". Không có hai thứ đó thì duyệt chỉ là bấm một
   cái nút, mà cả hàng rào này sinh ra để không phải bấm mù.

   Ô tìm và chip đếm chạy Ở MÁY CHỦ (QT-19).

   Tiền tố dtg = duyệt tặng. Đã kiểm và chạm tên trước khi đặt (QT-28). */

var dtgDiem = '';      // chip điểm bán đang chọn, rỗng là tất cả
var dtgTt = '';        // chip trạng thái duyệt
var dtgLoai = '';      // chip loại tặng
var dtgTim = '';       // ô tìm
var dtgMo = {};        // mã đơn nào đang mở rộng
var dtgChiTiet = {};   // chi tiết đã đọc về, khỏi hỏi lại máy chủ

function dtgMauTt(tt) {
  if (tt === 'Chờ duyệt') return ['#fffbeb', '#fcd34d', '#92400e'];
  if (tt === 'Đã duyệt') return ['#ecfdf3', '#a6f4c5', '#05603a'];
  if (tt === 'Từ chối') return ['#fef2f2', '#fecaca', '#b3261e'];
  return ['#f8fafc', '#e2e8f0', '#64748b'];
}

/* Một hàng chip, cùng khuôn với màn Danh sách phiếu hoàn tiền. Chip rỗng thì
   ẩn, riêng chip đang chọn luôn hiện dù đếm 0 - không thì bấm vào là nó biến
   mất và người ta không biết đường bấm lại. */
function dtgHangChip(thuoc, dsc, dem, chon, nhanTatCa) {
  var s = posChipNut(thuoc + '=""', (nhanTatCa || 'Tất cả') + ' · ' +
    (dem.tat_ca || 0), chon === '');
  (dsc || []).forEach(function (o) {
    var n = dem[o.k] || 0;
    if (!n && chon !== o.k) return;
    s += posChipNut(thuoc + '="' + h(o.k) + '"', o.ten + ' · ' + n, chon === o.k);
  });
  return '<div style="display:flex;gap:7px;flex-wrap:wrap;margin:7px 0">' + s + '</div>';
}

/* Nhãn nhỏ, mỗi nhãn không được gãy giữa chừng trên màn hình hẹp. Cùng bài
   học với `phNhanHang` ở màn phiếu hoàn (anh Việt bắt được 31/08/2026). */
function dtgNhan(cac) {
  var s = '<div class="h2" style="display:flex;flex-wrap:wrap;gap:5px;margin-top:6px">';
  (cac || []).forEach(function (o) {
    if (!o) return;
    s += '<span style="background:' + o[1] + ';border:1px solid ' + o[2] + ';color:' + o[3] +
      ';border-radius:20px;padding:2px 9px;font-size:11.5px;white-space:nowrap;' +
      'display:inline-block;line-height:1.5">' + h(o[0]) + '</span>';
  });
  return s + '</div>';
}

async function scrDuyetTang() {
  frame('Duyệt đơn hàng tặng', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc danh sách...</div></div>');
  var kq;
  try {
    kq = await api('vagabond.hang_tang.ds_don', {
      diem: dtgDiem, trang_thai: dtgTt, loai: dtgLoai, tim: dtgTim,
    });
  } catch (e) {
    frame('Duyệt đơn hàng tặng', '<div class="emp"><div class="e1">⚠️</div><div>' +
      h(errMsg(e)) + '</div></div>');
    return;
  }
  var dong = kq.dong || [];

  var html = '<div class="card" style="padding:12px 13px">' +
    '<div style="font-size:13px;color:#344054;line-height:1.6">' +
    'Đơn trả bằng <b>Hàng tặng</b> không thu tiền của khách. Hoá đơn vẫn xuất ' +
    '<b>nguyên giá và nguyên thuế</b> theo luật hàng biếu tặng, phần khách phải ' +
    'trả được gạt sang chi phí biếu tặng. Đơn chỉ ghi sổ được sau khi duyệt ở đây.' +
    '</div>' +
    '<div style="margin-top:9px;display:flex;gap:18px;flex-wrap:wrap">' +
    '<div><div style="font-size:12px;color:#8a8f9c">ĐANG CHỜ DUYỆT</div>' +
    '<b style="font-size:19px;color:#b54708">' + money(kq.tien_cho || 0) + ' đ</b></div>' +
    '<div><div style="font-size:12px;color:#8a8f9c">ĐÃ DUYỆT, CHỜ GHI SỔ</div>' +
    '<b style="font-size:19px;color:#05603a">' + money(kq.tien_duyet || 0) + ' đ</b></div>' +
    '</div>' +
    (kq.thieu_tai_khoan ? '<div style="margin-top:9px;padding:7px 9px;background:#fef2f2;' +
      'border:1px solid #fecaca;border-radius:8px;font-size:12.5px;color:#b3261e">' +
      '⚠️ <b>Chưa khai Tài khoản chi phí biếu tặng trong Cài đặt.</b> Duyệt được ' +
      'nhưng đơn vẫn chưa ghi sổ được, vì máy không biết hạch toán phần tặng vào ' +
      'đâu. Nhờ anh Việt và chị Dung chọn tài khoản trước.</div>' : '') +
    (kq.duyet_duoc ? '' : '<div style="margin-top:9px;padding:7px 9px;background:#f8fafc;' +
      'border:1px solid #e2e8f0;border-radius:8px;font-size:12.5px;color:#475467">' +
      'Bạn xem được danh sách nhưng không duyệt được. Chỉ Giám đốc mới duyệt, để ' +
      'người tặng và người duyệt không phải là một người.</div>') +
    '</div>';

  html += dtgHangChip('data-dtgd', kq.diem, kq.dem_diem || {}, dtgDiem, 'Mọi điểm bán');
  html += dtgHangChip('data-dtgt', (kq.trang_thai || []).map(function (k) {
    return { k: k, ten: k };
  }), kq.dem || {}, dtgTt, 'Mọi trạng thái');
  html += dtgHangChip('data-dtgl', kq.loai, kq.dem_loai || {}, dtgLoai, 'Mọi loại tặng');

  html += '<div class="card" style="padding:9px 11px"><input id="dtgTim" type="search" ' +
    'placeholder="Tìm theo mã đơn, tên khách, mã Pancake, lý do tặng" value="' + h(dtgTim) + '" ' +
    'style="width:100%;height:38px;border:1.5px solid #e4e7ec;border-radius:9px;' +
    'padding:0 10px;font-size:14px"></div>';

  html += '<div class="sec">' + dong.length + ' đơn' +
    (kq.con_nua ? ' trên tổng ' + kq.tong_dong : '') +
    ' · bấm để xem từng món</div><div class="card">';
  if (!dong.length) {
    html += '<div class="emp" style="padding:24px"><div class="e1">🎁</div>' +
      '<div>Không có đơn hàng tặng nào trong nhóm này.</div></div>';
  }
  var tenDiem = {};
  (kq.diem || []).forEach(function (o) { tenDiem[o.k] = o.ten; });
  dong.forEach(function (r) {
    var tt = r.vgb_tang_duyet || 'Chờ duyệt';
    var m = dtgMauTt(tt);
    var mo = !!dtgMo[r.name];
    html += '<div class="hub" data-dtgm="' + h(r.name) + '" style="align-items:flex-start' +
      (r.cho_lau ? ';background:#fffbfb;border-left:3px solid #b3261e' : '') + '">' +
      '<div class="hi">' + (r.da_ghi_so ? '✅' : (r.cho_lau ? '⚠️' : '🎁')) + '</div>' +
      '<div class="ht"><div class="h1">' +
      h(r.custom_pancake_display_id ? '#' + r.custom_pancake_display_id : r.name) +
      ' · ' + h(r.customer_name || 'Khách lẻ') + '</div>' +
      '<div class="h2">' + h(r.vgb_tang_ly_do || 'Chưa ghi lý do') + '</div>' +
      dtgNhan([
        [tt, m[0], m[1], m[2]],
        [r.nhan_loai, '#f8fafc', '#e2e8f0', '#475467'],
        [tenDiem[r.diem_ban] || 'Chưa rõ điểm bán', '#f8fafc', '#e2e8f0', '#475467'],
        r.da_ghi_so ? ['Đã ghi sổ', '#ecfdf3', '#a6f4c5', '#05603a'] : null,
        r.cho_lau ? ['Chờ ' + r.cho_ngay + ' ngày', '#fef2f2', '#fecaca', '#b3261e'] : null,
      ]) + (mo ? dtgThan(r, kq) : '') + '</div>' +
      '<div style="text-align:right;white-space:nowrap">' +
      '<b style="font-size:13.5px">' + money(r.grand_total) + '</b>' +
      '<div style="font-size:11px;color:#98a2b3">' + h(r.creation || '') + '</div></div></div>';
  });
  html += '</div>';

  frame('Duyệt đơn hàng tặng', html);
  var o = document.getElementById('dtgTim');
  if (o) {
    o.onchange = function () { dtgTim = o.value.trim(); go(scrDuyetTang, true); };
    o.onkeydown = function (e) { if (e.key === 'Enter') { dtgTim = o.value.trim(); go(scrDuyetTang, true); } };
  }
  /* Nghe trên `root` chứ không trên thân màn, xem bài học ở đầu 29-don-huy.js
     và ca kiểm `thu_chan_man.py`. */
  root.addEventListener('click', dtgBam);
}

/* Phần mở rộng của một đơn: từng món, và hai nút quyết. */
function dtgThan(r, kq) {
  var ct = dtgChiTiet[r.name];
  var s = '<div style="margin-top:9px;padding:9px 10px;background:#f9fafb;' +
    'border:1px solid #eef0f3;border-radius:9px">';
  var d = function (nhan, gt) {
    if (!gt) return '';
    return '<div style="display:flex;gap:8px;font-size:12px;margin-top:3px">' +
      '<span style="color:#98a2b3;min-width:112px">' + nhan + '</span>' +
      '<span style="color:#344054">' + h(String(gt)) + '</span></div>';
  };
  if (!ct) {
    s += '<div style="font-size:12.5px;color:#98a2b3">Đang đọc từng món...</div>';
    return s + '</div>';
  }
  s += '<div style="font-size:12.5px;font-weight:700;color:#475467;margin-bottom:5px">' +
    'Đang tặng những món này</div>';
  (ct.mon || []).forEach(function (x) {
    s += '<div style="display:flex;justify-content:space-between;gap:10px;' +
      'font-size:12.5px;padding:3px 0;border-bottom:1px solid #eef0f3">' +
      '<span style="color:#344054">' + h(x.item_name || x.item_code) +
      ' <span style="color:#98a2b3">x' + (x.qty || 0) + '</span></span>' +
      '<b style="white-space:nowrap">' + money(x.amount) + '</b></div>';
  });
  s += d('Mã đơn', r.name);
  s += d('Loại tặng', ct.nhan_loai);
  s += d('Lý do tặng', ct.vgb_tang_ly_do);
  s += d('Người lập', ct.owner);
  s += d('Người duyệt', r.vgb_tang_nguoi_duyet);
  s += d('Duyệt lúc', r.vgb_tang_luc_duyet);
  s += d('Ý kiến người duyệt', r.vgb_tang_y_kien);
  s += d('Bút toán gạt công nợ', r.vgb_but_toan_tang);
  /* Con số này là thứ giám đốc cần nhất trước khi bấm: một đơn 200 nghìn
     nhìn vô hại, nhưng là đơn thứ mười hai của cùng một người trong tháng
     thì câu chuyện khác hẳn. Cố ý KHÔNG chặn cứng theo hạn mức: đặt hạn
     mức bao nhiêu là quyết định của anh Việt, máy không đặt hộ. */
  if (ct.thang_nay) {
    s += '<div style="margin-top:8px;padding:6px 8px;background:#fffbeb;' +
      'border:1px solid #fcd34d;border-radius:8px;font-size:12px;color:#92400e">' +
      'Người lập này đã lập <b>' + (ct.thang_nay.so || 0) + ' đơn tặng</b> trong tháng, ' +
      'tổng <b>' + money(ct.thang_nay.tien || 0) + ' đ</b>.</div>';
  }
  if (kq.duyet_duoc && !r.da_ghi_so && (r.vgb_tang_duyet || 'Chờ duyệt') !== 'Đã duyệt') {
    s += '<div style="display:flex;gap:9px;margin-top:10px">' +
      '<button class="btn gh" data-dtgtc="' + h(r.name) + '" style="flex:1;margin:0">✖️ Từ chối</button>' +
      '<button class="btn" data-dtgok="' + h(r.name) + '" style="flex:2;margin:0">✅ Duyệt đơn</button></div>';
  } else if (kq.duyet_duoc && !r.da_ghi_so && r.vgb_tang_duyet === 'Đã duyệt') {
    s += '<div style="margin-top:10px"><button class="btn gh" data-dtgtc="' + h(r.name) +
      '" style="width:100%;margin:0">✖️ Rút lại, từ chối đơn này</button></div>';
  }
  return s + '</div>';
}

async function dtgBam(ev) {
  var t = ev.target.closest('[data-dtgd]');
  if (t) { dtgDiem = t.getAttribute('data-dtgd'); return go(scrDuyetTang, true); }
  t = ev.target.closest('[data-dtgt]');
  if (t) { dtgTt = t.getAttribute('data-dtgt'); return go(scrDuyetTang, true); }
  t = ev.target.closest('[data-dtgl]');
  if (t) { dtgLoai = t.getAttribute('data-dtgl'); return go(scrDuyetTang, true); }

  t = ev.target.closest('[data-dtgok]');
  if (t) {
    var ma = t.getAttribute('data-dtgok');
    var y = await hoiChu('Duyệt đơn hàng tặng',
      'Duyệt xong đơn này mới ghi sổ được. Ghi thêm ý kiến nếu cần, để trống cũng được.',
      '', { nhieu_dong: 1, goi_y: 'Ví dụ: đồng ý tặng, trừ vào ngân sách marketing tháng 8' });
    if (y === null) return;
    try {
      await api('vagabond.hang_tang.duyet', { name: ma, y_kien: y || '' });
    } catch (e) { return baoTin(errMsg(e), 'Không duyệt được'); }
    delete dtgChiTiet[ma];
    return go(scrDuyetTang, true);
  }

  t = ev.target.closest('[data-dtgtc]');
  if (t) {
    var maTc = t.getAttribute('data-dtgtc');
    var ly = await hoiChu('Từ chối đơn hàng tặng',
      'Ghi rõ vì sao từ chối, để người lập biết đường sửa.',
      '', { nhieu_dong: 1, bat_buoc: 1, goi_y: 'Ví dụ: đơn quá lớn, chưa ai đồng ý, tặng sai đối tượng' });
    if (ly === null) return;
    try {
      await api('vagabond.hang_tang.tu_choi', { name: maTc, ly_do: ly });
    } catch (e) { return baoTin(errMsg(e), 'Không từ chối được'); }
    delete dtgChiTiet[maTc];
    return go(scrDuyetTang, true);
  }

  t = ev.target.closest('[data-dtgm]');
  if (t) {
    var maM = t.getAttribute('data-dtgm');
    if (dtgMo[maM]) { delete dtgMo[maM]; return go(scrDuyetTang, true); }
    dtgMo[maM] = 1;
    if (!dtgChiTiet[maM]) {
      try {
        dtgChiTiet[maM] = await api('vagabond.hang_tang.chi_tiet', { name: maM });
      } catch (e) { return baoTin(errMsg(e), 'Không đọc được chi tiết đơn'); }
    }
    return go(scrDuyetTang, true);
  }
}

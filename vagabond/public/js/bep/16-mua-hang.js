/* ---------------- Don mua hang (PO) ---------------- */
async function scrDonMua() {
  frame('Đơn mua hàng', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc đơn mua hàng...</div></div>');
  var kq;
  try { kq = await api('vagabond.mua_hang.ds_po', { so_ngay: poNgay, tu_khoa: poTim, nhom: poNhom }); }
  catch (e) {
    frame('Đơn mua hàng', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  /* Loc theo chip lam o MAY CHU roi, o day chi ve ra. */
  var ds = kq.don || [];

  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">ĐƠN MUA HÀNG ' + (poNgay ? h(poNgay) + ' NGÀY GẦN ĐÂY' : 'TẤT CẢ') + '</div>' +
    '<div style="font-size:24px;font-weight:800">' + money(kq.tong_tien) + ' đ</div>' +
    '<div style="font-size:12.5px;color:#6b7280">' + money(kq.tong_dong) + ' đơn · đang xem ' + money(ds.length) + '</div>' +
    mkNhacCat(kq.bi_cat, 'đơn') + '</div>';

  html += '<div class="card" style="padding:10px 12px">' +
    mkChipNgay([[30, '30 ngày'], [60, '60 ngày'], [180, '6 tháng'], [0, 'Tất cả']], poNgay, 'data-pongay') + '</div>';
  html += '<div class="card" style="padding:10px 12px">' + mkChipNhom(kq.nhom, kq.dem, poNhom, 'data-ponhom') + '</div>';
  html += mkOTim('poTim', poTim, 'Tìm theo mã đơn hoặc tên nhà cung cấp...');

  if (!ds.length) {
    html += '<div class="card"><div class="emp" style="padding:26px"><div class="e1">🫙</div><div>Không có đơn nào ở nhóm này.</div></div></div>';
  } else {
    html += '<div class="lst">' + ds.map(function (d) {
      var mau = { tre_hen: '#b3261e', cho_hoa_don: '#b45309', nhap: '#6b7280', xong: '#0f766e' }[d.nhom] || '#374151';
      var ten = '';
      (kq.nhom || []).forEach(function (n) { if (n.k === d.nhom) ten = n.ic + ' ' + n.ten; });
      return '<div class="shi" data-po="' + h(d.name) + '" style="display:flex;gap:10px;align-items:flex-start;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
        '<div style="flex:1;min-width:0">' +
        '<b style="font-size:14.5px">' + h(d.supplier_name || d.supplier) + '</b>' +
        '<div style="font-size:12px;color:#98a2b3">' + h(d.name) + ' · đặt ' + ngayNgan(d.ngay) +
        (d.hen ? ' · hẹn ' + ngayNgan(d.hen) : '') + '</div>' +
        '<div style="font-size:12px;color:' + mau + ';font-weight:600;margin-top:3px">' + h(ten) +
        (d.tre_ngay ? ' ' + d.tre_ngay + ' ngày' : '') +
        (d.nhom === 'nhan_mot_phan' ? ' · đã nhận ' + Math.round(d.per_received) + '%' : '') + '</div></div>' +
        '<b style="white-space:nowrap">' + money(d.grand_total) + ' đ</b></div>';
    }).join('') + '</div>';
  }

  var b = frame('Đơn mua hàng', html);
  b.onclick = function (e) {
    var t = e.target.closest('[data-ponhom]');
    if (t) { poNhom = t.getAttribute('data-ponhom'); return go(scrDonMua, true); }
    t = e.target.closest('[data-pongay]');
    if (t) { poNgay = parseInt(t.getAttribute('data-pongay'), 10); return go(scrDonMua, true); }
    t = e.target.closest('[data-po]');
    if (t) { poXem = t.getAttribute('data-po'); return go(scrDonMuaXem, true); }
  };
  var o = document.getElementById('poTim');
  if (o) o.onchange = function () { poTim = o.value; go(scrDonMua, true); };
}

async function scrDonMuaXem() {
  frame('Đơn mua hàng', '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api('vagabond.mua_hang.xem_po', { name: poXem }); }
  catch (e) { frame('Đơn mua hàng', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không đọc được') + '</div></div>'); return; }

  var html = '<div class="card" style="padding:13px 14px;line-height:1.7">' +
    '<b style="font-size:15px">' + h(d.ten_ncc || d.ncc) + '</b>' +
    '<div style="font-size:12.5px;color:#6b7280">' + h(d.name) + ' · đặt ngày ' + ngayNgan(d.ngay) +
    (d.hen ? ' · hẹn giao ' + ngayNgan(d.hen) : '') + '</div>' +
    '<div style="font-size:13px;margin-top:6px">Đã nhận <b>' + Math.round(d.da_nhan) + '%</b> · đã lên hoá đơn <b>' + Math.round(d.da_hoa_don) + '%</b></div>' +
    '</div>';

  html += '<div class="sec">Mặt hàng</div><div class="card" style="padding:6px 14px">' +
    d.mon.map(function (m) {
      return '<div style="display:flex;justify-content:space-between;gap:10px;padding:8px 0;border-bottom:1px solid #f0f2f6">' +
        '<div style="flex:1;min-width:0">' + h(m.ten || m.ma) +
        '<div style="color:#a0a6b4;font-size:12px">đặt ' + money(m.sl) + ' ' + h(m.dvt || '') +
        ' · đã nhận ' + money(m.da_nhan) + ' · ' + money(m.gia) + ' đ</div></div>' +
        '<b style="white-space:nowrap">' + money(m.tien) + '</b></div>';
    }).join('') +
    '<div style="display:flex;justify-content:space-between;padding:9px 0;color:#5a6070"><span>Tiền hàng</span><span>' + money(d.tong_hang) + ' đ</span></div>' +
    (d.thue ? '<div style="display:flex;justify-content:space-between;padding:2px 0;color:#5a6070"><span>Thuế và phí</span><span>' + money(d.thue) + ' đ</span></div>' : '') +
    '<div style="display:flex;justify-content:space-between;padding:9px 0;font-size:16px"><b>Tổng cộng</b><b>' + money(d.tong) + ' đ</b></div></div>';

  html += '<div class="sec">Đã nối với</div><div class="card" style="padding:12px 14px;font-size:13.5px;line-height:1.8">' +
    '<div>Phiếu nhập kho: ' + (d.phieu_nhap.length ? '<b>' + d.phieu_nhap.map(h).join(', ') + '</b>' : '<span style="color:#b45309">chưa có phiếu nào</span>') + '</div>' +
    '<div>Hoá đơn mua: ' + (d.hoa_don.length ? '<b>' + d.hoa_don.map(h).join(', ') + '</b>' : '<span style="color:#b45309">chưa có hoá đơn nào</span>') + '</div>' +
    '</div>';

  frame('Đơn mua hàng', html);
}

/* ---------------- Cong no phai tra ---------------- */
var cntNcc = null;
async function scrNoPhaiTra() {
  frame('Công nợ phải trả', '<div class="emp"><div class="e1">⏳</div><div>Đang cộng sổ nợ nhà cung cấp...</div></div>');
  var kq;
  try { kq = await api('vagabond.mua_hang.cong_no_phai_tra', {}); }
  catch (e) {
    frame('Công nợ phải trả', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  var html = '<div class="card" style="padding:14px">' +
    '<div style="font-size:12px;color:#98a2b3">TỔNG CÒN PHẢI TRẢ</div>' +
    '<div style="font-size:28px;font-weight:800">' + money(kq.tong) + ' đ</div>' +
    '<div style="font-size:12.5px;color:#6b7280">' + money(kq.so_ncc) + ' nhà cung cấp</div>' +
    (kq.tong_qua_han
      ? '<div style="margin-top:9px;background:#fef2f2;border:1.5px solid #fecaca;border-radius:9px;padding:10px 12px;font-size:13px;color:#b3261e">' +
        'Trong đó <b>' + money(kq.tong_qua_han) + ' đ</b> đã quá hạn trả.</div>'
      : '<div style="margin-top:9px;font-size:13px;color:#0f766e">Chưa có khoản nào quá hạn.</div>') +
    '</div>';

  if (!(kq.ncc || []).length) {
    html += '<div class="card"><div class="emp" style="padding:26px"><div class="e1">🎉</div><div>Không nợ nhà cung cấp nào.</div></div></div>';
  } else {
    html += '<div class="sec">Nợ nhiều và quá hạn xếp lên đầu</div><div class="lst">' +
      kq.ncc.map(function (n) {
        return '<div class="shi" data-ncc="' + h(n.ncc) + '" style="display:flex;gap:10px;align-items:flex-start;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
          '<div style="flex:1;min-width:0"><b style="font-size:14.5px">' + h(n.ten) + '</b>' +
          '<div style="font-size:12px;color:#98a2b3">' + money(n.so_hd) + ' hoá đơn' +
          (n.han_gan_nhat ? ' · hạn gần nhất ' + ngayNgan(n.han_gan_nhat) : '') + '</div>' +
          (n.qua_han
            ? '<div style="font-size:12px;color:#b3261e;font-weight:600;margin-top:3px">Quá hạn ' + money(n.qua_han) + ' đ · ' + n.so_hd_qua_han + ' hoá đơn</div>'
            : '') + '</div>' +
          '<b style="white-space:nowrap">' + money(n.tien) + ' đ</b></div>';
      }).join('') + '</div>';
  }

  var b = frame('Công nợ phải trả', html);
  b.onclick = function (e) {
    var t = e.target.closest('[data-ncc]');
    if (!t) return;
    var ma = t.getAttribute('data-ncc');
    var n = (kq.ncc || []).filter(function (x) { return x.ncc === ma; })[0];
    if (n) mkSheetNoNcc(n);
  };
}

function mkSheetNoNcc(n) {
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>' + h(n.ten) + '</b><div class="x">&times;</div></div>' +
    '<div style="padding:4px 14px calc(env(safe-area-inset-bottom,0px) + 16px);max-height:78vh;overflow:auto">' +
    '<div style="font-size:13px;color:#374151;margin:8px 0 12px">Còn nợ <b>' + money(n.tien) + ' đ</b> trên ' + money(n.so_hd) + ' hoá đơn' +
    (n.qua_han ? ', trong đó <b style="color:#b3261e">' + money(n.qua_han) + ' đ quá hạn</b>' : '') + '.</div>' +
    n.hd.map(function (x) {
      return '<div style="border:1.5px solid ' + (x.tre_ngay ? '#fecaca' : '#e5e7eb') + ';background:' + (x.tre_ngay ? '#fef2f2' : '#fff') + ';border-radius:10px;padding:10px 12px;margin-bottom:8px">' +
        '<div style="display:flex;justify-content:space-between;gap:10px">' +
        '<b style="font-size:13.5px">' + h(x.name) + '</b><b>' + money(x.con_no) + ' đ</b></div>' +
        '<div style="font-size:12px;color:#6b7280;margin-top:3px">' +
        (x.so_hd_ncc ? 'Số hoá đơn NCC ' + h(x.so_hd_ncc) + ' · ' : '') +
        'ngày ' + ngayNgan(x.ngay) + (x.han ? ' · hạn trả ' + ngayNgan(x.han) : '') +
        (x.tre_ngay ? ' · <b style="color:#b3261e">trễ ' + x.tre_ngay + ' ngày</b>' : '') + '</div>' +
        (x.tong !== x.con_no ? '<div style="font-size:12px;color:#98a2b3">Tổng hoá đơn ' + money(x.tong) + ' đ, đã trả ' + money(x.tong - x.con_no) + ' đ</div>' : '') +
        '</div>';
    }).join('') + '</div>';
  ov.appendChild(box); document.body.appendChild(ov);
  ov.onclick = function (e) { if (e.target === ov) ov.remove(); };
  box.querySelector('.x').onclick = function () { ov.remove(); };
}

/* ---------------- Hoa don ban ra ---------------- */
async function scrHdBan() {
  frame('Hoá đơn bán ra', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc hoá đơn...</div></div>');
  var kq;
  try { kq = await api('vagabond.ke_toan.ds_hoa_don_ban', { so_ngay: ktBanNgay, quay: ktBanQuay, tu_khoa: ktBanTim, nhom: ktBanNhom }); }
  catch (e) {
    frame('Hoá đơn bán ra', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  var ds = kq.hd || [];

  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">HOÁ ĐƠN BÁN RA · ' + ngayNgan(kq.tu) + ' - ' + ngayNgan(kq.den) + '</div>' +
    '<div style="font-size:24px;font-weight:800">' + money(kq.tong) + ' đ</div>' +
    '<div style="font-size:12.5px;color:#6b7280">' + money(kq.tong_dong) + ' hoá đơn · đang xem ' + money(ds.length) +
    (kq.con_thu ? ' · còn phải thu ' + money(kq.con_thu) + ' đ' : '') + '</div>' +
    mkNhacCat(kq.bi_cat, 'hoá đơn') + '</div>';

  html += '<div class="card" style="padding:10px 12px">' +
    mkChipNgay([[7, '7 ngày'], [30, '30 ngày'], [90, '3 tháng'], [365, '1 năm']], ktBanNgay, 'data-ktbngay') + '</div>';
  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
    [['', 'Cả ba điểm'], ['SALES', 'Sales Online'], ['TCV', 'District 1'], ['NVHTN', 'NVHTN']]
      .map(function (q) { return posChipNut('data-ktbquay="' + q[0] + '"', q[1], ktBanQuay === q[0]); }).join('')) + '</div>';
  html += '<div class="card" style="padding:10px 12px">' + mkChipNhom(kq.nhom, kq.dem, ktBanNhom, 'data-ktbnhom') + '</div>';
  html += mkOTim('ktBanTim', ktBanTim, 'Tìm theo mã phiếu, tên khách, số hoá đơn điện tử...');

  html += mkBangHd(ds, 'ban');
  var b = frame('Hoá đơn bán ra', html);
  b.onclick = function (e) {
    var t = e.target.closest('[data-ktbnhom]');
    if (t) { ktBanNhom = t.getAttribute('data-ktbnhom'); return go(scrHdBan, true); }
    t = e.target.closest('[data-ktbngay]');
    if (t) { ktBanNgay = parseInt(t.getAttribute('data-ktbngay'), 10); return go(scrHdBan, true); }
    t = e.target.closest('[data-ktbquay]');
    if (t) { ktBanQuay = t.getAttribute('data-ktbquay'); return go(scrHdBan, true); }
    t = e.target.closest('[data-hdb]');
    if (t) return go(function () { scrDsView(t.getAttribute('data-hdb'), true); });
  };
  var o = document.getElementById('ktBanTim');
  if (o) o.onchange = function () { ktBanTim = o.value; go(scrHdBan, true); };
}

var TEN_DIEM_BAN = { SALES: 'Sales Online', TCV: 'District 1', NVHTN: 'NVHTN' };

function mkBangHd(ds, loai) {
  if (!ds.length) return '<div class="card"><div class="emp" style="padding:26px"><div class="e1">🫙</div><div>Không có hoá đơn nào ở nhóm này.</div></div></div>';
  return '<div class="lst">' + ds.map(function (d) {
    if (loai === 'ban') {
      return '<div class="shi" data-hdb="' + h(d.name) + '" style="display:flex;gap:10px;align-items:flex-start;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
        '<div style="flex:1;min-width:0"><b style="font-size:14px">' + h(d.khach || 'Khách lẻ') + '</b>' +
        '<div style="font-size:12px;color:#98a2b3">' + h(d.name) + ' · ' + ngayNgan(d.posting_date) +
        ' · ' + h(TEN_DIEM_BAN[d.diem] || d.diem) + '</div>' +
        '<div style="font-size:12px;color:#6b7280;margin-top:3px">' +
        (d.custom_hddt_so ? 'HĐ ' + h(d.custom_hddt_so) + ' · ' + h(d.custom_hddt_trang_thai || '') : '<span style="color:#b45309">chưa xuất hoá đơn điện tử</span>') +
        (d.vgb_pt_thanh_toan ? ' · ' + h(d.vgb_pt_thanh_toan) : '') +
        (d.docstatus === 0 && !d.vgb_huy ? ' · <b style="color:#b45309">còn nháp</b>' : '') +
        (d.docstatus === 2 || d.vgb_huy ? ' · <b style="color:#b3261e">🚫 đã huỷ</b>' : '') +
        (d.vgb_huy && d.vgb_huy_ly_do ? ' <span style="color:#b3261e">(' + h(d.vgb_huy_ly_do) + ')</span>' : '') +
        (d.da_sua ? ' · <b style="color:#92400e">✏️ đã sửa</b>' : '') + '</div></div>' +
        '<div style="text-align:right;white-space:nowrap"><b>' + money(d.grand_total) + '</b>' +
        (d.docstatus === 1 && d.outstanding_amount > 0 ? '<div style="font-size:11.5px;color:#b3261e">còn ' + money(d.outstanding_amount) + '</div>' : '') +
        '</div></div>';
    }
    return '<div class="shi" style="display:flex;gap:10px;align-items:flex-start;padding:12px 14px;border-bottom:1px solid #f2f4f7">' +
      '<div style="flex:1;min-width:0"><b style="font-size:14px">' + h(d.supplier_name || d.supplier) + '</b>' +
      '<div style="font-size:12px;color:#98a2b3">' + h(d.name) + ' · ' + ngayNgan(d.posting_date) +
      (d.bill_no ? ' · số ' + h(d.bill_no) : '') + '</div>' +
      '<div style="font-size:12px;color:#6b7280;margin-top:3px">' +
      (d.vgb_huy ? '<b style="color:#b3261e">🚫 đã huỷ' + (d.vgb_huy_ly_do ? ' (' + h(d.vgb_huy_ly_do) + ')' : '') + '</b>'
        : d.docstatus === 0 ? '<b style="color:#b45309">còn nháp</b>'
        : d.docstatus === 2 ? '<b style="color:#b3261e">đã huỷ</b>'
          : d.outstanding_amount > 0
            ? (d.tre_ngay ? '<b style="color:#b3261e">quá hạn ' + d.tre_ngay + ' ngày</b>' : 'hạn trả ' + ngayNgan(d.due_date || ''))
            : '<span style="color:#0f766e">đã trả xong</span>') +
      (d.da_sua ? ' · <b style="color:#92400e">✏️ đã sửa</b>' : '') + '</div></div>' +
      '<div style="text-align:right;white-space:nowrap"><b>' + money(d.grand_total) + '</b>' +
      (d.docstatus === 1 && d.outstanding_amount > 0 ? '<div style="font-size:11.5px;color:#b3261e">còn ' + money(d.outstanding_amount) + '</div>' : '') +
      '</div></div>';
  }).join('') + '</div>';
}

/* ---------------- Hoa don mua vao ---------------- */
async function scrHdMua() {
  frame('Hoá đơn mua vào', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc hoá đơn...</div></div>');
  var kq;
  try { kq = await api('vagabond.ke_toan.ds_hoa_don_mua', { so_ngay: ktMuaNgay, tu_khoa: ktMuaTim, nhom: ktMuaNhom }); }
  catch (e) {
    frame('Hoá đơn mua vào', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  var ds = kq.hd || [];

  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">HOÁ ĐƠN MUA VÀO · ' + ngayNgan(kq.tu) + ' - ' + ngayNgan(kq.den) + '</div>' +
    '<div style="font-size:24px;font-weight:800">' + money(kq.tong) + ' đ</div>' +
    '<div style="font-size:12.5px;color:#6b7280">' + money(kq.tong_dong) + ' hoá đơn · đang xem ' + money(ds.length) +
    (kq.con_no ? ' · còn nợ ' + money(kq.con_no) + ' đ' : '') + '</div>' +
    mkNhacCat(kq.bi_cat, 'hoá đơn') + '</div>';

  html += '<div class="card" style="padding:10px 12px">' +
    mkChipNgay([[30, '30 ngày'], [60, '60 ngày'], [180, '6 tháng'], [365, '1 năm']], ktMuaNgay, 'data-ktmngay') + '</div>';
  html += '<div class="card" style="padding:10px 12px">' + mkChipNhom(kq.nhom, kq.dem, ktMuaNhom, 'data-ktmnhom') + '</div>';
  html += mkOTim('ktMuaTim', ktMuaTim, 'Tìm theo mã phiếu, tên nhà cung cấp, số hoá đơn...');
  html += mkBangHd(ds, 'mua');

  var b = frame('Hoá đơn mua vào', html);
  b.onclick = function (e) {
    var t = e.target.closest('[data-ktmnhom]');
    if (t) { ktMuaNhom = t.getAttribute('data-ktmnhom'); return go(scrHdMua, true); }
    t = e.target.closest('[data-ktmngay]');
    if (t) { ktMuaNgay = parseInt(t.getAttribute('data-ktmngay'), 10); return go(scrHdMua, true); }
  };
  var o = document.getElementById('ktMuaTim');
  if (o) o.onchange = function () { ktMuaTim = o.value; go(scrHdMua, true); };
}



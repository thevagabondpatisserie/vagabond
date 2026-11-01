/* ---------------- Phân hệ Tài chính (v626)

   Anh Việt 31/10/2026: "tham khảo các phần mềm hàng đầu để làm phân hệ Tài
   chính: tổng tiền mặt hiện có, tổng tiền ngân hàng hiện có (qua SePay, anh
   đưa số dư ban đầu tại thời điểm chốt, em tự tính), tỉ lệ hao hụt...". Sau
   khi xem ảnh mẫu anh đồng ý đủ các nút: Tổng quan, Tiền hiện có, Dòng tiền,
   Dự báo 30 ngày, Lãi lỗ tháng, Tỉ lệ giá vốn và hao hụt, bốn ô công nợ và
   chờ chi (mở màn đã có), Cài đặt tài chính.

   Mọi con số do máy chủ tính (vagabond/tai_chinh.py), màn chỉ vẽ. Quyền chặn
   thật ở máy chủ; TC_VAI_LUON_XEM phải trùng tai_chinh.VAI_LUON_XEM, có ca
   kiểm chốt. Người khác Giám đốc chọn đích danh, cờ đi qua S.quyenNen. */
var TC_VAI_LUON_XEM = ['System Manager', 'Giám đốc'];
function coQuyenTaiChinh() {
  return TC_VAI_LUON_XEM.some(function (v) { return hasRole(v); }) ||
    !!(typeof S !== 'undefined' && S.quyenNen && S.quyenNen.tai_chinh);
}

var tcKyDong = 7;
var tcThang = '';
var tcMoChot = '';

/* Số gọn cho thẻ: 1,84 tỷ; 42,5 tr; 950.000. */
function tcGon(v) {
  if (v === null || v === undefined || isNaN(v)) return '...';
  var a = Math.abs(Number(v)), dau = Number(v) < 0 ? '-' : '';
  if (a >= 1e9) return dau + (Math.round(a / 1e7) / 100).toString().replace('.', ',') + ' tỷ';
  if (a >= 1e6) return dau + (Math.round(a / 1e5) / 10).toString().replace('.', ',') + ' tr';
  return dau + money(a);
}
function tcPt(v) { return v === null || v === undefined ? 'chưa có' : String(v).replace('.', ',') + '%'; }
function tcNgay(s) { s = String(s || ''); return s.length >= 10 ? s.slice(8, 10) + '/' + s.slice(5, 7) + '/' + s.slice(0, 4) : s; }
function tcThangVn(t) { t = String(t || ''); return t.length >= 7 ? 'tháng ' + t.slice(5, 7) + '/' + t.slice(0, 4) : t; }
function tcCongThang(t, n) {
  var y = +t.slice(0, 4), m = +t.slice(5, 7) + n;
  while (m < 1) { m += 12; y--; }
  while (m > 12) { m -= 12; y++; }
  return y + '-' + ('0' + m).slice(-2);
}
function tcChip(bg, fg, chu) {
  return '<span style="display:inline-block;background:' + bg + ';color:' + fg + ';font-size:11.5px;font-weight:700;' +
    'border-radius:999px;padding:2px 9px;margin:3px 5px 0 0;white-space:nowrap">' + chu + '</span>';
}
function tcKhoa(tieuDe) {
  frame(tieuDe, '<div class="emp"><div class="e1">🔒</div><div>Phân hệ Tài chính chỉ mở cho Giám đốc và người Giám đốc chọn cho xem.</div></div>');
}
function tcLoi(tieuDe, e) {
  frame(tieuDe, '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e)) + '</div></div>');
}
function tcDoi(tieuDe, chu) {
  frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>' + chu + '</div></div>');
}
function tcO(k, ic, ten, so, phu, mau) {
  return '<button class="btn gh" data-tcgo="' + k + '" style="display:flex;flex-direction:row;align-items:center;gap:12px;width:100%;' +
    'margin:0 0 8px;min-height:64px;padding:11px 12px;text-align:left;border-radius:12px">' +
    '<span style="font-size:22px;flex:0 0 auto">' + ic + '</span>' +
    '<span style="flex:1;min-width:0"><span style="display:block;font-weight:700;font-size:14.5px;color:#101828">' + h(ten) + '</span>' +
    (phu ? '<span style="display:block;font-size:12.5px;color:#667085;margin-top:1px">' + phu + '</span>' : '') + '</span>' +
    '<span style="flex:0 0 auto;font-weight:800;font-size:15px;white-space:nowrap;color:' + (mau || '#101828') + '">' + so + '</span></button>';
}

/* ================= Tổng quan */
async function scrTcTongQuan() {
  var td = 'Tổng quan tài chính';
  if (!coQuyenTaiChinh()) return tcKhoa(td);
  tcDoi(td, 'Đang đọc tiền, công nợ, lãi lỗ...');
  var kq;
  try { kq = await api('vagabond.tai_chinh.tong_quan', {}); } catch (e) { return tcLoi(td, e); }
  var p = function (x, f) { return x && x.ok ? f(x.v) : { so: '...', phu: 'Chưa đọc được', mau: '#b42318' }; };
  var tien = kq.tien && kq.tien.ok ? kq.tien.v : null;
  var html = '<div class="card" data-tctong="1" style="padding:14px 14px 12px">' +
    '<div style="font-size:12px;color:#98a2b3;letter-spacing:.3px">TỔNG TIỀN CÔNG TY ĐANG CÓ</div>' +
    (tien ? '<div style="font-size:26px;font-weight:800;line-height:1.3">' + money(tien.tong) + ' đ</div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px">' +
      '<div style="background:#f8fafc;border-radius:10px;padding:8px 10px"><div style="font-size:12px;color:#667085">Ngân hàng</div>' +
      '<div style="font-size:17px;font-weight:800">' + tcGon(tien.ngan_hang) + '</div>' +
      (tien.tam_ung ? '<div style="font-size:11.5px;color:#667085">gồm tạm ứng ' + tcGon(tien.tam_ung) + '</div>' : '') + '</div>' +
      '<div style="background:#f8fafc;border-radius:10px;padding:8px 10px"><div style="font-size:12px;color:#667085">Tiền mặt</div>' +
      '<div style="font-size:17px;font-weight:800">' + tcGon(tien.tien_mat) + '</div></div></div>' +
      (tien.loi ? '<div data-tcloi="1" style="margin-top:8px;font-size:12.5px;color:#b42318">Có ' + tien.loi +
        ' tài khoản, két chưa tính được lúc này nên tổng đang thiếu phần đó. Mở Tiền hiện có xem chỗ nào; vẫn vậy thì báo kỹ thuật.</div>' : '') +
      (tien.chua_chot ? '<div data-tcchuachot="1" style="margin-top:8px;font-size:12.5px;color:#b54708">Còn ' + tien.chua_chot +
        ' tài khoản, két chưa chốt số dư đầu nên chưa cộng vào tổng. Bấm Cài đặt tài chính để chốt.</div>' : '')
      : '<div style="color:#b42318;margin-top:6px">Chưa đọc được tiền hiện có.</div>') + '</div>';
  html += '<div class="sec">Tiền</div>';
  html += tcO('TCTIEN', '💵', 'Tiền hiện có', tien ? tcGon(tien.tong) : '...', 'Từng tài khoản, từng két, đối chiếu SePay');
  var d7 = p(kq.dong7, function (v) {
    if (v.thieu) return { so: (v.rong >= 0 ? '+' : '') + tcGon(v.rong), phu: 'Thiếu tiền mặt ' + v.thieu + ' lượt két chưa đọc được', mau: '#b54708' };
    return { so: (v.rong >= 0 ? '+' : '') + tcGon(v.rong), phu: '7 ngày: vào ' + tcGon(v.vao) + ', ra ' + tcGon(v.ra), mau: v.rong >= 0 ? '#067647' : '#b42318' };
  });
  html += tcO('TCDONG', '🔁', 'Dòng tiền', d7.so, d7.phu, d7.mau);
  html += tcO('TCDB', '🔮', 'Dự báo 30 ngày', '›', 'Số dư sau khi thu nợ, trả nhà cung cấp, chi đã duyệt');
  html += '<div class="sec">Lãi lỗ ' + h(tcThangVn(kq.thang)) + '</div>';
  var ll = p(kq.lai_lo, function (v) {
    return { so: tcGon(v.lai_rong), phu: 'Doanh thu thuần ' + tcGon(v.doanh_thu_thuan) + ' · lãi ròng ' + tcPt(v.ti_le_lai_rong), mau: v.lai_rong >= 0 ? '#067647' : '#b42318', fc: v.food_cost };
  });
  html += tcO('TCLL', '📈', 'Lãi lỗ tháng', ll.so, ll.phu, ll.mau);
  html += tcO('TCTL', '🥐', 'Tỉ lệ giá vốn và hao hụt', ll.fc !== undefined ? tcPt(ll.fc) : '...', 'Food cost theo sổ cái; prime cost; hao hụt kiểm kê, xuất huỷ');
  html += '<div class="sec">Công nợ và chờ chi</div>';
  var pt = p(kq.phai_thu, function (v) { return { so: tcGon(v), phu: 'Phải thu, khách nợ lâu lên đầu' }; });
  html += tcO('TCPT', '📥', 'Khách nợ mình', pt.so, pt.phu, pt.mau);
  var ptr = p(kq.phai_tra, function (v) {
    return { so: tcGon(v.tong), phu: v.qua_han ? 'Quá hạn ' + tcGon(v.qua_han) : 'Không có khoản quá hạn', mau: v.qua_han ? '#b42318' : '' };
  });
  html += tcO('TCPTR', '📤', 'Mình nợ nhà cung cấp', ptr.so, ptr.phu, ptr.mau);
  var cc = p(kq.cho_chi, function (v) {
    return { so: v.so + ' hồ sơ', phu: tcGon(v.tien) + ' đã duyệt chưa chuyển' + (v.so_cho_duyet ? ' · ' + v.so_cho_duyet + ' hồ sơ chờ duyệt' : '') };
  });
  html += tcO('TCCHO', '⏳', 'Chờ chi', cc.so, cc.phu, cc.mau);
  var tt = p(kq.tra_truoc, function (v) { return { so: tcGon(v.tong), phu: v.so_khach + ' khách còn tiền gửi trước. Tiền của khách, chưa phải của mình' }; });
  html += tcO('TCTT', '🎟️', 'Tiền khách gửi trước', tt.so, tt.phu, tt.mau);
  html += '<div class="sec">Cài đặt</div>' + tcO('TCCD', '⚙️', 'Cài đặt tài chính', '›', 'Chốt số dư đầu từng tài khoản, két; chọn người được xem');
  var than = frame(td, html);
  than.querySelectorAll('[data-tcgo]').forEach(function (b) {
    b.onclick = function () { vgbGo(b.getAttribute('data-tcgo')); };
  });
}

/* ================= Tiền hiện có */
function tcDongTien(d) {
  var dong2 = [];
  if (d.moc) dong2.push('Chốt ' + tcNgay(d.moc.ngay_chot) + ': ' + money(d.moc.so_du));
  if (d.moc && (d.vao || d.ra)) dong2.push('vào +' + money(d.vao) + ', ra -' + money(d.ra));
  var chip = '';
  var dc = d.doi_chieu;
  if (dc && dc.tt === 'khop') chip += tcChip('#ecfdf3', '#067647', '✓ Khớp SePay');
  else if (dc && dc.tt === 'lech') chip += tcChip('#fffaeb', '#b54708', 'Lệch SePay ' + money(dc.lech));
  (d.ghi || []).forEach(function (g) {
    if (d.loi) { chip += tcChip('#fef3f2', '#b42318', h(g)); return; }
    chip += tcChip(g.indexOf('SePay') >= 0 ? '#eff8ff' : '#f2f4f7', g.indexOf('SePay') >= 0 ? '#175cd3' : '#475467', h(g));
  });
  if (d.ca) dong2.push('Chốt ca ' + tcNgay(d.ca.luc) + ' ' + String(d.ca.luc || '').slice(11, 16) + ' đếm ' + money(d.ca.dem));
  var so = d.so_du === null || d.so_du === undefined
    ? (d.loi ? '<span data-tcdongloi="1" style="color:#b42318">Chưa tính được</span>' : '<span style="color:#b54708">Chưa chốt</span>')
    : money(d.so_du);
  return '<div data-tcnguon="' + h(d.nguon) + '" style="display:flex;gap:10px;align-items:flex-start;padding:10px 13px;border-top:1px solid #f1f5f9;min-height:44px">' +
    '<div style="flex:1;min-width:0"><b style="font-size:14px">' + h(d.ten) + '</b>' +
    (dong2.length ? '<div style="font-size:12.5px;color:#667085;margin-top:1px">' + h(dong2.join(' · ')) + '</div>' : '') +
    (chip ? '<div>' + chip + '</div>' : '') + '</div>' +
    '<div style="flex:0 0 auto;text-align:right;font-weight:800;white-space:nowrap">' + so + '</div></div>';
}
async function scrTcTien() {
  var td = 'Tiền hiện có';
  if (!coQuyenTaiChinh()) return tcKhoa(td);
  tcDoi(td, 'Đang tính tiền từng tài khoản, từng két...');
  var kq;
  try { kq = await api('vagabond.tai_chinh.tien_hien_co', {}); } catch (e) { return tcLoi(td, e); }
  var t = kq.tong || {};
  var nhCty = [], nhTu = [], tm = [];
  (kq.dong || []).forEach(function (d) {
    if (d.loai === 'Ngân hàng') (d.tam_ung ? nhTu : nhCty).push(d); else tm.push(d);
  });
  var cong = function (ds) { return ds.reduce(function (s, d) { return s + (d.so_du === null || d.so_du === undefined ? 0 : Number(d.so_du)); }, 0); };
  var nhom = function (ten, ds) {
    if (!ds.length) return '';
    return '<div class="card" style="padding:0"><div style="display:flex;justify-content:space-between;padding:11px 13px 6px">' +
      '<b>' + ten + '</b><b>' + money(cong(ds)) + '</b></div>' + ds.map(tcDongTien).join('') + '</div>';
  };
  var html = '<div class="card" style="padding:14px">' +
    '<div style="font-size:12px;color:#98a2b3;letter-spacing:.3px">TỔNG TIỀN CÔNG TY ĐANG CÓ · ' + h(String(kq.luc || '').slice(11, 16)) + '</div>' +
    '<div data-tctongtien="1" style="font-size:26px;font-weight:800;line-height:1.3">' + money(t.tong) + ' đ</div>' +
    '<div style="font-size:13px;color:#475467">Ngân hàng ' + money(t.ngan_hang) + ' · Tiền mặt ' + money(t.tien_mat) + '</div>' +
    (t.loi ? '<div data-tcloi="1" style="margin-top:6px;font-size:12.5px;color:#b42318">Có ' + t.loi + ' chỗ chưa tính được lúc này (dòng ghi đỏ bên dưới), tổng đang thiếu phần đó.</div>' : '') +
    (t.chua_chot ? '<div style="margin-top:6px;font-size:12.5px;color:#b54708">Còn ' + t.chua_chot + ' chỗ chưa chốt số dư đầu, chưa cộng vào tổng.</div>' : '') +
    (kq.sepay_doc_duoc ? '' : '<div style="margin-top:6px;font-size:12.5px;color:#b42318">Chưa đọc được số dư từ SePay lúc này, phần đối chiếu tạm bỏ trống.</div>') +
    '</div>';
  html += nhom('🏦 Ngân hàng công ty', nhCty) + nhom('🏦 Tài khoản tạm ứng', nhTu) + nhom('💵 Tiền mặt', tm);
  html += '<details class="card" style="padding:11px 13px;font-size:13px;color:#475467;line-height:1.6"><summary style="font-weight:700;color:#101828;min-height:32px">Cách tính</summary>' +
    '<div>Ngân hàng: số dư chốt cuối ngày, cộng tiền vào, trừ tiền ra theo giao dịch SePay từ hôm sau. SePay có báo số dư thì so hai số: khớp hiện chip xanh, lệch hiện số lệch.</div>' +
    '<div>Két: số dư chốt, cộng tiền mặt vào két (đúng phép màn Chốt ca: bill, tiền đặt bánh, tiền nạp số dư), trừ phiếu nộp quỹ đã giao.</div>' +
    '<div>Quỹ công ty: số dư chốt, cộng phiếu nộp quỹ đã ký nhận, cộng trừ bút toán tiền mặt trên sổ cái.</div>' +
    '<div>Chi tiền mặt không qua app thì app không thấy: đếm lại rồi chốt lại số dư ở Cài đặt tài chính.</div></details>';
  html += '<button class="btn" data-tcgo="TCCD" style="width:100%;min-height:46px;margin-top:4px">Chốt số dư ở Cài đặt tài chính</button>';
  var than = frame(td, html);
  than.querySelectorAll('[data-tcgo]').forEach(function (b) { b.onclick = function () { vgbGo(b.getAttribute('data-tcgo')); }; });
}

/* ================= Dòng tiền */
async function scrTcDong() {
  var td = 'Dòng tiền';
  if (!coQuyenTaiChinh()) return tcKhoa(td);
  tcDoi(td, 'Đang cộng tiền vào, tiền ra từng ngày...');
  var kq;
  try { kq = await api('vagabond.tai_chinh.dong_tien', { so_ngay: tcKyDong }); } catch (e) { return tcLoi(td, e); }
  var ngay = kq.ngay || [];
  var lon = Math.max.apply(null, [1].concat(ngay.map(function (x) { return Math.max(x.vao, x.ra); })));
  var html = '<div style="display:flex;gap:8px;margin:0 0 8px">' + [7, 30].map(function (n) {
    return '<button class="btn gh" data-tcky="' + n + '" style="flex:1;margin:0;min-height:44px;border-radius:999px;' +
      (tcKyDong === n ? 'border:2px solid #0f766e;color:#0f766e;font-weight:800' : '') + '">' + n + ' ngày</button>';
  }).join('') + '</div>';
  if ((kq.thieu || []).length) {
    html += '<div class="card" data-tcthieu="1" style="padding:12px 13px;color:#b54708;line-height:1.5">Chưa đọc được tiền mặt vào két: ' +
      h(kq.thieu.slice(0, 6).join(', ')) + (kq.thieu.length > 6 ? ' và ' + (kq.thieu.length - 6) + ' lượt khác' : '') +
      '. Tiền vào đang thiếu phần này. Mở lại sau ít phút; vẫn vậy thì báo kỹ thuật.</div>';
  }
  html += '<div class="card" style="padding:13px">' +
    '<div style="font-size:12px;color:#98a2b3">' + tcNgay(kq.tu) + ' tới ' + tcNgay(kq.den) + '</div>' +
    '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-top:6px">' +
    '<div><div style="font-size:12px;color:#667085">Tiền vào</div><b data-tcvao="1" style="color:#067647">+' + tcGon(kq.vao) + '</b></div>' +
    '<div><div style="font-size:12px;color:#667085">Tiền ra</div><b style="color:#b42318">-' + tcGon(kq.ra) + '</b></div>' +
    '<div><div style="font-size:12px;color:#667085">Còn lại</div><b style="color:' + (kq.rong >= 0 ? '#067647' : '#b42318') + '">' + (kq.rong >= 0 ? '+' : '') + tcGon(kq.rong) + '</b></div></div>' +
    '<div role="img" aria-label="Tiền vào và ra từng ngày" style="display:flex;align-items:flex-end;gap:2px;height:84px;margin-top:10px">' +
    ngay.map(function (x) {
      return '<div title="' + h(tcNgay(x.ngay)) + '" style="flex:1;min-width:2px;display:flex;flex-direction:column;justify-content:flex-end;height:84px">' +
        '<div style="background:#0d9488;border-radius:2px 2px 0 0;height:' + Math.round(x.vao / lon * 42) + 'px"></div>' +
        '<div style="background:#f97066;border-radius:0 0 2px 2px;height:' + Math.round(x.ra / lon * 42) + 'px"></div></div>';
    }).join('') + '</div>' +
    '<div style="font-size:12px;color:#667085;margin-top:6px">Xanh: tiền vào. Đỏ: tiền ra. Gồm ngân hàng, tiền mặt vào két, thu và chi tiền mặt của quỹ.</div>' +
    (kq.noi_bo && kq.noi_bo.so ? '<div style="font-size:12.5px;color:#475467;margin-top:4px">Đã bỏ ' + kq.noi_bo.so + ' lần chuyển giữa các tài khoản của mình (' + tcGon(kq.noi_bo.tien) + '), không tính là vào hay ra.</div>' : '') +
    '</div>';
  html += '<div class="card" style="padding:0"><div style="padding:11px 13px 4px;font-weight:700">Từng ngày</div>' +
    ngay.slice().reverse().map(function (x) {
      return '<div style="display:flex;justify-content:space-between;gap:8px;padding:8px 13px;border-top:1px solid #f1f5f9;font-size:13.5px">' +
        '<span>' + tcNgay(x.ngay) + '</span><span><b style="color:#067647">+' + money(x.vao) + '</b> · <b style="color:#b42318">-' + money(x.ra) + '</b></span></div>';
    }).join('') + '</div>';
  var ds = function (ten, arr, dau, mau) {
    if (!arr || !arr.length) return '';
    return '<div class="card" style="padding:0"><div style="padding:11px 13px 4px;font-weight:700">' + ten + '</div>' + arr.map(function (g) {
      return '<div style="display:flex;gap:8px;padding:8px 13px;border-top:1px solid #f1f5f9">' +
        '<div style="flex:1;min-width:0;font-size:12.5px;color:#475467">' + tcNgay(g.ngay) + ' · ' + h(g.tk || '') +
        '<div style="color:#101828;overflow-wrap:anywhere">' + h(g.mo_ta || '') + '</div></div>' +
        '<b style="white-space:nowrap;color:' + mau + '">' + dau + money(g.so) + '</b></div>';
    }).join('') + '</div>';
  };
  html += ds('Khoản vào lớn nhất', (kq.lon_nhat || {}).vao, '+', '#067647') + ds('Khoản ra lớn nhất', (kq.lon_nhat || {}).ra, '-', '#b42318');
  var than = frame(td, html);
  than.querySelectorAll('[data-tcky]').forEach(function (b) {
    b.onclick = function () { tcKyDong = +b.getAttribute('data-tcky'); go(scrTcDong, true); };
  });
}

/* ================= Dự báo 30 ngày */
async function scrTcDuBao() {
  var td = 'Dự báo 30 ngày';
  if (!coQuyenTaiChinh()) return tcKhoa(td);
  tcDoi(td, 'Đang cộng nợ phải thu, phải trả...');
  var kq;
  try { kq = await api('vagabond.tai_chinh.du_bao_30', {}); } catch (e) { return tcLoi(td, e); }
  var dong = function (ten, so, dau, mau, phu) {
    var chua = so === null || so === undefined;
    return '<div style="display:flex;justify-content:space-between;gap:8px;padding:9px 13px;border-top:1px solid #f1f5f9">' +
      '<span>' + ten + (phu ? '<div style="font-size:12px;color:#667085">' + phu + '</div>' : '') + '</span>' +
      (chua ? '<b data-tcchuadoc="1" style="white-space:nowrap;color:#b54708">Chưa đọc được</b>'
        : '<b style="white-space:nowrap;color:' + (mau || '#101828') + '">' + dau + money(so) + '</b>') + '</div>';
  };
  var hongNcc = kq.theo_tuan === null;
  var tuan = kq.theo_tuan || {};
  var ncc = function (k) { return hongNcc ? null : (tuan[k] || 0); };
  var html = '';
  if ((kq.thieu || []).length) {
    html += '<div class="card" data-tcthieu="1" style="padding:13px;color:#b54708;line-height:1.5">Chưa đọc được: ' + h(kq.thieu.join(', ')) +
      '. Vì thiếu phần này nên chưa kết luận số dư sau 30 ngày. Thử mở lại sau ít phút; vẫn vậy thì báo kỹ thuật.</div>';
  }
  if (kq.so_du === null || kq.so_du === undefined) {
    html += '<div class="card" style="padding:13px;color:#b54708">Chưa chốt số dư nào nên chưa dự báo được số dư. Vào Cài đặt tài chính để chốt.</div>';
  }
  html += '<div class="card" style="padding:0"><div style="padding:11px 13px 4px;font-weight:700">Từ hôm nay ' + tcNgay(kq.hom_nay) + ' tới 30 ngày sau</div>' +
    dong('Tiền đang có', kq.so_du || 0, '', '', kq.chua_chot ? 'còn ' + kq.chua_chot + ' chỗ chưa chốt' : '') +
    dong('Khách nợ mình (nếu thu hết)', kq.phai_thu, '+', '#067647') +
    dong('Nợ nhà cung cấp đã quá hạn', ncc('qua_han'), '-', '#b42318') +
    dong('Nợ nhà cung cấp đến hạn tuần 1', ncc('tuan_1'), '-', '#b42318') +
    dong('Tuần 2', ncc('tuan_2'), '-', '#b42318') +
    dong('Tuần 3', ncc('tuan_3'), '-', '#b42318') +
    dong('Tuần 4 tới hết ngày 30', ncc('tuan_4'), '-', '#b42318') +
    dong('Hồ sơ thanh toán đã duyệt, chờ chuyển', kq.cho_chi, '-', '#b42318') +
    dong('Hồ sơ thanh toán đang chờ duyệt', kq.cho_duyet, '-', '#b42318') + '</div>';
  if (kq.cuoi_ky !== null && kq.cuoi_ky !== undefined) {
    html += '<div class="card" style="padding:14px"><div style="font-size:12px;color:#98a2b3">SỐ DƯ DỰ KIẾN SAU 30 NGÀY</div>' +
      '<div data-tccuoiky="1" style="font-size:24px;font-weight:800;color:' + (kq.cuoi_ky >= 0 ? '#067647' : '#b42318') + '">' + money(kq.cuoi_ky) + ' đ</div>' +
      '<div style="font-size:13px;color:#475467">Nếu khách chưa trả nợ: ' + money(kq.cuoi_ky_khong_thu) + ' đ</div></div>';
  }
  html += '<div style="font-size:12.5px;color:#667085;margin:4px 4px 10px;line-height:1.6">Chưa tính tiền bán hàng mới và lương sẽ phát sinh. ' +
    'Nợ nhà cung cấp đã nằm trong hồ sơ thanh toán thì chỉ trừ một lần ở dòng hồ sơ. ' + (hongNcc ? '' : 'Đến hạn sau 30 ngày: ' + money(kq.sau_30) + ' đ, chưa trừ.') + '</div>';
  frame(td, html);
}

/* ================= Lãi lỗ tháng */
function tcThanhThang(t) {
  return '<div style="display:flex;gap:8px;align-items:center;margin-bottom:8px">' +
    '<button class="btn gh" data-tcthang="-1" aria-label="Tháng trước" style="flex:0 0 48px;width:48px;margin:0;min-height:44px">‹</button>' +
    '<div style="flex:1;text-align:center;font-weight:800">' + h(tcThangVn(t)) + '</div>' +
    '<button class="btn gh" data-tcthang="1" aria-label="Tháng sau" style="flex:0 0 48px;width:48px;margin:0;min-height:44px">›</button></div>';
}
function tcNoiThang(than, fn) {
  than.querySelectorAll('[data-tcthang]').forEach(function (b) {
    b.onclick = function () {
      var t = tcCongThang(tcThang || today().slice(0, 7), +b.getAttribute('data-tcthang'));
      if (t > today().slice(0, 7)) return;
      tcThang = t; go(fn, true);
    };
  });
}
async function scrTcLaiLo() {
  var td = 'Lãi lỗ tháng';
  if (!coQuyenTaiChinh()) return tcKhoa(td);
  tcDoi(td, 'Đang đọc sổ cái...');
  var kq;
  try { kq = await api('vagabond.tai_chinh.lai_lo_thang', { thang: tcThang }); } catch (e) { return tcLoi(td, e); }
  tcThang = kq.thang;
  var a = kq.ky || {}, b = kq.ky_truoc || {};
  var dong = function (ten, k, dam, am) {
    var v = Number(a[k] || 0), v2 = Number(b[k] || 0);
    return '<div style="display:flex;gap:8px;padding:8px 13px;border-top:1px solid #f1f5f9;' + (dam ? 'font-weight:800;' : '') + '">' +
      '<span style="flex:1;min-width:0">' + ten + '</span>' +
      '<span style="flex:0 0 auto;width:30%;text-align:right;white-space:nowrap">' + (am ? '-' : '') + tcGon(v) + '</span>' +
      '<span style="flex:0 0 auto;width:24%;text-align:right;white-space:nowrap;color:#98a2b3">' + (am ? '-' : '') + tcGon(v2) + '</span></div>';
  };
  var html = tcThanhThang(kq.thang);
  if (kq.dang_chay) html += '<div class="card" style="padding:10px 13px;font-size:12.5px;color:#b54708">Tháng đang chạy: hoá đơn, chi phí chưa ghi sổ thì chưa có trong số này.</div>';
  html += '<div class="card" style="padding:0" data-tcbanglailo="1">' +
    '<div style="display:flex;gap:8px;padding:10px 13px 4px;font-size:12px;color:#667085"><span style="flex:1"></span>' +
    '<span style="width:30%;text-align:right">' + h(tcThangVn(kq.thang)) + '</span><span style="width:24%;text-align:right">' + h(tcThangVn(kq.thang_truoc)) + '</span></div>' +
    dong('Doanh thu bán hàng', 'doanh_thu') + dong('Giảm trừ doanh thu', 'giam_tru', 0, 1) + dong('Doanh thu thuần', 'doanh_thu_thuan', 1) +
    dong('Giá vốn hàng bán', 'gia_von', 0, 1) + dong('Lãi gộp', 'lai_gop', 1) +
    dong('Chi phí bán hàng', 'cp_ban_hang', 0, 1) + dong('Chi phí quản lý', 'cp_quan_ly', 0, 1) +
    dong('Chi phí sản xuất chưa kết chuyển', 'cp_san_xuat', 0, 1) + dong('Tài chính (thu trừ chi)', 'tai_chinh') +
    dong('Khác (thu trừ chi)', 'khac') + dong('Lãi trước thuế', 'truoc_thue', 1) + dong('Thuế thu nhập doanh nghiệp', 'thue_tndn', 0, 1) +
    dong('Lãi ròng', 'lai_rong', 1) + '</div>';
  html += '<div class="card" style="padding:12px 13px;font-size:13.5px;line-height:1.7">Tỉ lệ lãi gộp <b>' + tcPt(a.ti_le_lai_gop) + '</b> · lãi ròng <b>' + tcPt(a.ti_le_lai_rong) +
    '</b><br>Food cost <b>' + tcPt(a.food_cost) + '</b> · prime cost <b>' + tcPt(a.prime_cost) + '</b></div>';
  html += '<div style="font-size:12.5px;color:#667085;margin:4px 4px 10px;line-height:1.6">Số lấy từ sổ cái (bút toán đã ghi sổ). Khoản nào kế toán chưa ghi sổ thì chưa có ở đây.</div>';
  var than = frame(td, html);
  tcNoiThang(than, scrTcLaiLo);
}

/* ================= Tỉ lệ giá vốn và hao hụt */
async function scrTcTiLe() {
  var td = 'Tỉ lệ giá vốn và hao hụt';
  if (!coQuyenTaiChinh()) return tcKhoa(td);
  tcDoi(td, 'Đang tính tỉ lệ...');
  var kq;
  try { kq = await api('vagabond.tai_chinh.ti_le_thang', { thang: tcThang }); } catch (e) { return tcLoi(td, e); }
  tcThang = kq.thang;
  var hh = kq.hao_hut || {};
  var o = function (ten, v, phu) {
    return '<div style="background:#fff;border:1px solid #eaecf0;border-radius:12px;padding:10px 12px">' +
      '<div style="font-size:12.5px;color:#667085">' + ten + '</div><div style="font-size:20px;font-weight:800">' + tcPt(v) + '</div>' +
      '<div style="font-size:12px;color:#667085">' + phu + '</div></div>';
  };
  var html = tcThanhThang(kq.thang);
  html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px">' +
    o('Food cost', kq.food_cost, 'Giá vốn ' + tcGon(kq.gia_von) + ' / doanh thu thuần') +
    o('Prime cost', kq.prime_cost, 'Thêm chi phí nhân viên ' + tcGon(kq.nhan_vien)) +
    o('Xuất huỷ', hh.ti_le_huy, 'Huỷ ' + tcGon(hh.huy) + ' / doanh thu thuần') +
    o('Hao hụt kiểm kê', hh.ti_le_kiem_ke, 'Thiếu ' + tcGon(hh.thieu) + ' / nguyên liệu dùng ' + tcGon(hh.da_dung)) + '</div>';
  html += '<div class="card" style="padding:0"><div style="padding:11px 13px 4px;font-weight:700">Theo kho</div>' +
    ((hh.dong || []).length ? (hh.dong || []).map(function (d) {
      var bt = !!d.bat_thuong;
      return '<div data-tckho="1" style="padding:9px 13px;border-top:1px solid #f1f5f9">' +
        '<div style="display:flex;justify-content:space-between;gap:8px"><b>' + h(d.kho) + '</b><b>' + tcPt(d.ti_le_kiem_ke) + '</b></div>' +
        '<div style="font-size:12.5px;color:#667085">Thiếu khi kiểm kê ' + money(d.thieu) + (d.thua ? ', thừa ' + money(d.thua) : '') +
        ' · dùng ' + money(d.da_dung) + (d.huy ? ' · huỷ ' + money(d.huy) : '') + '</div>' +
        (bt ? tcChip('#fef3f2', '#b42318', 'Bất thường: kiểm lại phiếu kiểm kê, có thể là lần đếm đầu') : '') + '</div>';
    }).join('') : '<div style="padding:12px 13px;color:#667085">Tháng này chưa có phiếu kiểm kê, xuất dùng hay xuất huỷ nào.</div>') + '</div>';
  html += '<div style="font-size:12.5px;color:#667085;margin:4px 4px 10px;line-height:1.6">Tạm tính. Hao hụt chỉ đúng khi bếp ghi đủ lệnh sản xuất, cân thật và kiểm kê đều. ' +
    'Xem màn Dữ liệu hao hụt để biết còn thiếu gì.</div>';
  html += '<button class="btn gh" data-tcgo="BCHH" style="width:100%;min-height:46px">Mở Dữ liệu hao hụt</button>';
  var than = frame(td, html);
  tcNoiThang(than, scrTcTiLe);
  than.querySelectorAll('[data-tcgo]').forEach(function (b) { b.onclick = function () { vgbGo(b.getAttribute('data-tcgo')); }; });
}

/* ================= Cài đặt tài chính */
async function scrTcCaiDat() {
  var td = 'Cài đặt tài chính';
  if (!coQuyenTaiChinh()) return tcKhoa(td);
  tcDoi(td, 'Đang đọc mốc chốt số dư...');
  var kq;
  try { kq = await api('vagabond.tai_chinh.cai_dat', {}); } catch (e) { return tcLoi(td, e); }
  var html = '<div class="card" style="padding:12px 13px;font-size:13px;color:#475467;line-height:1.6">' +
    'Mỗi tài khoản, mỗi két chốt <b>số dư cuối một ngày</b>. Từ hôm sau app tự cộng tiền vào, trừ tiền ra. ' +
    'Đếm lại thấy lệch thì bấm Chốt lại: app thêm mốc mới, mốc cũ vẫn giữ để đối chiếu.</div>';
  html += '<div class="card" style="padding:0">';
  (kq.nguon || []).forEach(function (n) {
    var m = (n.lich_su || [])[0];
    var mo = tcMoChot === n.nguon;
    html += '<div data-tccd="' + h(n.nguon) + '" style="padding:10px 13px;border-top:1px solid #f1f5f9">' +
      '<div style="display:flex;gap:10px;align-items:center"><div style="flex:1;min-width:0"><b>' + h(n.ten) + '</b>' +
      '<div style="font-size:12.5px;color:#667085">' + (m ? 'Đang dùng mốc ' + tcNgay(m.ngay_chot) + ': ' + money(m.so_du) + ' đ' :
        (n.loai === 'Ngân hàng' && !n.dong_bo && n.so_bao > 0 ? 'SePay báo số dư, không cần chốt' : 'Chưa chốt')) + '</div></div>' +
      '<button class="btn gh" data-tcmochot="' + h(n.nguon) + '" style="flex:0 0 auto;width:auto;margin:0;min-height:44px;padding:4px 12px">' + (m ? 'Chốt lại' : 'Chốt số dư') + '</button></div>';
    if (mo) {
      html += '<div data-tcform="1" style="margin-top:8px;background:#f8fafc;border-radius:10px;padding:10px">' +
        '<label style="font-size:12.5px;color:#475467">Số dư cuối ngày</label>' +
        '<input class="tin" id="tcNgayChot" type="date" max="' + h(kq.hom_nay) + '" value="' + h(kq.hom_nay) + '" style="width:100%;height:44px;box-sizing:border-box">' +
        '<label style="font-size:12.5px;color:#475467;display:block;margin-top:8px">Số dư (đồng)</label>' +
        '<input class="tin" id="tcSoDu" inputmode="numeric" placeholder="Ví dụ 1.628.400.000" style="width:100%;height:44px;box-sizing:border-box">' +
        '<label style="font-size:12.5px;color:#475467;display:block;margin-top:8px">Ghi chú (không bắt buộc)</label>' +
        '<input class="tin" id="tcGhiChu" placeholder="Ví dụ: theo sao kê MB cuối ngày" style="width:100%;height:44px;box-sizing:border-box">' +
        '<div style="display:flex;gap:8px;margin-top:10px"><button class="btn gh" data-tchuy="1" style="flex:1;margin:0;min-height:44px">Thôi</button>' +
        '<button class="btn" data-tcluu="' + h(n.nguon) + '" style="flex:2;margin:0;min-height:44px">Lưu mốc chốt</button></div></div>';
    }
    if ((n.lich_su || []).length > 1) {
      html += '<details style="margin-top:6px;font-size:12.5px;color:#475467"><summary style="min-height:28px">Các mốc trước</summary>' +
        n.lich_su.slice(1).map(function (x) { return '<div>' + tcNgay(x.ngay_chot) + ': ' + money(x.so_du) + ' đ · ' + h(x.nguoi) + (x.ghi_chu ? ' · ' + h(x.ghi_chu) : '') + '</div>'; }).join('') + '</details>';
    }
    html += '</div>';
  });
  html += '</div>';
  if (kq.la_giam_doc) {
    html += '<div class="sec">Ai được xem Tài chính</div><div class="card" style="padding:0">' +
      '<div style="padding:10px 13px;font-size:12.5px;color:#475467">Giám đốc luôn xem được. Tích thêm kế toán trưởng hoặc người anh tin cậy. Không tích ai là chỉ Giám đốc xem.</div>' +
      (kq.nguoi_dung || []).map(function (u) {
        return '<label data-tcnx="' + h(u.email) + '" style="display:flex;gap:10px;align-items:center;padding:8px 13px;border-top:1px solid #f1f5f9;min-height:44px">' +
          '<input type="checkbox" value="' + h(u.email) + '"' + (u.chon ? ' checked' : '') + ' style="width:22px;height:22px">' +
          '<span style="flex:1;min-width:0">' + h(u.ten) + '<div style="font-size:12px;color:#98a2b3">' + h(u.email) + '</div></span></label>';
      }).join('') +
      '<div style="padding:10px 13px"><button class="btn" data-tcluunx="1" style="width:100%;margin:0;min-height:46px">Lưu người được xem</button></div></div>';
  }
  var than = frame(td, html);
  than.querySelectorAll('[data-tcmochot]').forEach(function (b) {
    b.onclick = function () { tcMoChot = b.getAttribute('data-tcmochot'); go(scrTcCaiDat, true); };
  });
  than.querySelectorAll('[data-tchuy]').forEach(function (b) { b.onclick = function () { tcMoChot = ''; go(scrTcCaiDat, true); }; });
  than.querySelectorAll('[data-tcluu]').forEach(function (b) {
    b.onclick = async function () {
      var ngay = (document.getElementById('tcNgayChot') || {}).value || '';
      var so = (document.getElementById('tcSoDu') || {}).value || '';
      var ghi = (document.getElementById('tcGhiChu') || {}).value || '';
      if (!String(so).replace(/[^0-9]/g, '')) { toast('Gõ số dư bằng số, ví dụ 1.628.400.000'); return; }
      try {
        await api('vagabond.tai_chinh.luu_moc', { nguon: b.getAttribute('data-tcluu'), ngay_chot: ngay, so_du: so, ghi_chu: ghi });
      } catch (e) { toast(errMsg(e)); return; }
      toast('Đã lưu mốc chốt số dư');
      tcMoChot = '';
      go(scrTcCaiDat, true);
    };
  });
  var nx = than.querySelectorAll('[data-tcluunx]')[0];
  if (nx) nx.onclick = async function () {
    var ds = [];
    than.querySelectorAll('[data-tcnx]').forEach(function (l) {
      var c = l.querySelectorAll('input')[0];
      if (c && c.checked) ds.push(c.value || l.getAttribute('data-tcnx'));
    });
    try { await api('vagabond.tai_chinh.luu_nguoi_xem', { ds: JSON.stringify(ds) }); } catch (e) { toast(errMsg(e)); return; }
    toast('Đã lưu người được xem Tài chính');
    go(scrTcCaiDat, true);
  };
}

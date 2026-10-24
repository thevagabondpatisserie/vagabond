/* ---------------- Đối soát chuyển khoản (v610)

   Anh Việt 24/10/2026, theo báo của Dễ: bill TCVEHQHG ngày 23/10, khách xin
   số tài khoản công ty rồi chuyển thẳng vào MB 31561568. Tiền về SePay thật
   nhưng nút Dò tiền chỉ soi tài khoản ảo của điểm nên bill nằm mãi ở "Chưa
   đối soát được", không ghi sổ được.

   Màn này liệt kê mọi bill quầy trả chuyển khoản của một ngày, ba điểm bán
   chung một chỗ, bill chưa khớp tiền lên đầu. Bấm một bill là mở đúng bảng
   Dò tiền chuyển khoản (09-tinh-tien-quay.js), có chip tài khoản chính công
   ty. Chỉ Quản lý cửa hàng và Kế toán mở được (doi_soat_ck.QUYEN_GAN_NGOAI,
   chặn thật ở máy chủ). */
var QUYEN_DSCK = ['VGB - Quản lý cửa hàng', 'Accounts Manager', 'Accounts User', 'System Manager', 'Giám đốc', 'AP Giám đốc'];
function coQuyenDsck() {
  return QUYEN_DSCK.some(function (v) { return hasRole(v); });
}

var dsckNgay = '';
var dsckDiem = '';
var dsckTt = 'chua_xong';
var dsckTim = '';
/* Codex #497 v1 (4366436288): ô tìm theo mã bill, số hoá đơn, tên khách, kèm
   nút quét. Chuỗi quét từ mã QR có thể dài hơn mã bill nên khớp cả hai chiều:
   chữ gõ nằm trong dòng, hoặc mã bill nằm trong chữ quét. Đang tìm thì bỏ qua
   chip trạng thái và chip điểm, để gõ mã là thấy bill dù đang lọc gì. */
function dsckKhopTim(r, q) {
  var t = String(q || '').trim().toUpperCase();
  if (!t) return true;
  var dong = [r.ma, r.ma_tc, r.name, r.khach].join(' ').toUpperCase();
  if (dong.indexOf(t) >= 0) return true;
  return [r.ma, r.ma_tc, r.name].some(function (m) { m = String(m || '').toUpperCase(); return m.length >= 6 && t.indexOf(m) >= 0; });
}
var DSCK_TT = [
  { k: 'chua_xong', ten: 'Chưa khớp đủ tiền', ic: '⏳' },
  { k: 'du', ten: 'Đã khớp đủ', ic: '✅' },
];

function dsckChip(r) {
  var the = function (bg, fg, chu) {
    return '<span style="display:inline-block;background:' + bg + ';color:' + fg + ';font-size:11.5px;font-weight:700;' +
      'border-radius:999px;padding:2px 9px;margin:3px 5px 0 0;white-space:nowrap">' + chu + '</span>';
  };
  var c = '';
  if (r.tt === 'du') c += the('#dcfce7', '#166534', '✅ Đã khớp đủ tiền');
  else if (r.tt === 'thieu') c += the('#fef3c7', '#92400e', '⚠ Mới nhận ' + money(r.nhan) + ' đ');
  else c += the('#eef2ff', '#3730a3', '· Chưa khớp khoản nào');
  c += r.ghi_so ? the('#dcfce7', '#166534', 'Đã ghi sổ') : the('#e5e7eb', '#374151', 'Chưa ghi sổ');
  return c;
}

async function scrDoiSoatCk() {
  var tieuDe = 'Đối soát chuyển khoản';
  if (!dsckNgay) dsckNgay = today();
  frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc bill chuyển khoản...</div></div>');
  var kq;
  try { kq = await api('vagabond.doi_soat_ck.ds_bill_ck', { ngay: dsckNgay }); }
  catch (e) {
    frame(tieuDe, '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e)) + '</div></div>');
    return;
  }
  var tatCa = kq.rows || [];
  var dem = { tat_ca: tatCa.length, chua_xong: 0, du: 0 };
  var diemDs = [], demDiem = { tat_ca: tatCa.length };
  tatCa.forEach(function (r) {
    if (r.tt === 'du') dem.du++; else dem.chua_xong++;
    if (r.quay && diemDs.indexOf(r.quay) < 0) diemDs.push(r.quay);
    demDiem[r.quay] = (demDiem[r.quay] || 0) + 1;
  });
  var ds = tatCa.filter(function (r) {
    if (dsckTim) return dsckKhopTim(r, dsckTim);
    if (dsckDiem && r.quay !== dsckDiem) return false;
    if (dsckTt === 'du') return r.tt === 'du';
    if (dsckTt === 'chua_xong') return r.tt !== 'du';
    return true;
  });
  var cc = {
    ma: 'dsck',
    ho: [
      { k: 'tt', ds: DSCK_TT, dem: dem, chon: dsckTt, tatCa: 'Mọi bill', mau: '#0d9488' },
      { k: 'diem', ds: diemDs.map(function (m) { return { k: m, ten: m, ic: '🏪' }; }), dem: demDiem, chon: dsckDiem, tatCa: 'Mọi điểm bán', mau: '#4338ca' },
    ],
    tim: { gt: dsckTim, goiY: 'Tìm mã bill, số hoá đơn, tên khách', quet: true },
  };
  var html = '<div class="card" style="padding:12px 13px">' +
    '<div style="display:flex;gap:8px;align-items:center">' +
    '<button class="btn gh" data-dsckngay="-1" aria-label="Ngày trước" style="flex:0 0 48px;width:48px;margin:0;min-height:44px">‹</button>' +
    '<input class="tin" id="dsckChonNgay" type="date" value="' + h(dsckNgay) + '" style="flex:1;min-width:0;height:44px;text-align:center">' +
    '<button class="btn gh" data-dsckngay="1" aria-label="Ngày sau" style="flex:0 0 48px;width:48px;margin:0;min-height:44px">›</button></div>' +
    '<div style="font-size:12.5px;color:#475467;margin-top:8px;line-height:1.6">' +
    (dem.chua_xong ? '<b style="color:#b45309">' + dem.chua_xong + ' bill chưa khớp đủ tiền.</b> ' : '<b style="color:#15803d">Mọi bill chuyển khoản đã khớp đủ tiền.</b> ') +
    'Bấm một bill để dò tiền: có chip <b>Vào thẳng TK công ty</b> cho khoản khách chuyển tay vào tài khoản chính, không qua mã QR.</div></div>';
  html += dsCongCu(cc);
  html += '<div class="card">';
  if (!ds.length) {
    html += '<div class="emp" style="padding:24px"><div class="e1">🏦</div><div>' +
      (dsckTim ? 'Không có bill nào khớp "' + h(dsckTim) + '" trong ngày này. Kiểm lại mã hoặc đổi ngày.' :
        tatCa.length ? 'Không có bill nào trong nhóm này.' : 'Ngày này không có bill quầy nào trả bằng chuyển khoản.') + '</div></div>';
  }
  ds.forEach(function (r, i) {
    html += '<div class="row" data-dsckmo="' + i + '" style="cursor:pointer;display:flex;gap:10px;align-items:center;' +
      'padding:11px 13px;border-top:1px solid #f1f5f9;min-height:44px">' +
      '<div style="flex:1;min-width:0"><b>' + h(r.ma || r.name) + '</b>' +
      '<span style="color:#98a2b3;font-size:12px"> · ' + h(r.quay) + ' · ' + h(r.gio) + '</span>' +
      (r.khach ? '<div style="font-size:12.5px;color:#475467;margin-top:1px">👤 ' + h(r.khach) + '</div>' : '') +
      '<div>' + dsckChip(r) + '</div></div>' +
      '<div style="text-align:right"><b style="white-space:nowrap">' + money(r.tong) + '</b>' +
      (r.tt !== 'du' ? '<div style="font-size:12px;color:#0d9488;font-weight:700;margin-top:3px">Dò tiền &#8250;</div>' : '') +
      '</div></div>';
  });
  html += '</div>';
  var than = frame(tieuDe, html);
  dsCongCuNoi(than, cc, function (ho, k) {
    if (ho === 'tt') dsckTt = k;
    else if (ho === 'diem') dsckDiem = k;
    else if (ho === 'tim') dsckTim = k;
    go(scrDoiSoatCk, true);
  });
  than.querySelectorAll('[data-dsckngay]').forEach(function (b) {
    b.onclick = function () {
      dsckNgay = posDtCong(dsckNgay, +b.getAttribute('data-dsckngay'));
      go(scrDoiSoatCk, true);
    };
  });
  var o = document.getElementById('dsckChonNgay');
  if (o) o.onchange = function () { if (o.value) { dsckNgay = o.value; go(scrDoiSoatCk, true); } };
  than.querySelectorAll('[data-dsckmo]').forEach(function (d) {
    d.onclick = function () {
      var r = ds[+d.getAttribute('data-dsckmo')];
      if (!r) return;
      posSheetDoTien(r.tong, r.name, function () { go(scrDoiSoatCk, true); }, { quay: r.quay, ngay: dsckNgay });
    };
  });
}

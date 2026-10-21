/* ---------------- Số dư trả trước của khách (v607)

   Anh Việt 20/10/2026: khách trả trước 50 triệu vào tài khoản cá nhân Giám
   đốc rồi đặt bánh trừ dần, lâu nay các đơn đó bị ghi nhầm Hàng tặng. Anh
   duyệt bốn màn trong tra-truoc-cac-man-607.jpg:
     1. Danh sách khách trả trước
     2. Nạp tiền trả trước
     3. Sổ của một khách
     4. Chọn "Số dư trả trước" ở Bill quầy và Doanh thu Sales

   Số dư tính ở máy chủ từ chính các phiếu nạp và các đơn đã cấn, không ai
   gõ tay được. Xem vagabond/tra_truoc_khach.py. */
var SDT_CD = null;
var sdtTim = '';
var sdtKhachMo = '';
var sdtNap = null; /* {khach:{ma,ten}, so_tien, nguon, quay, anh[], ghi_chu, ma_gd, ma_lan} */

/* Ma lan gui cua MOT form nap (Codex #493 vong 3). Sinh mot lan khi mo form,
   giu ca trong ban nhap tu luu (48). Lan bam Luu dau da lap ma mat phan hoi,
   bam lai gui cung ma: may chu tra dung phieu cu, so du khong nhan doi. */
function sdtMaLan() {
  try { if (window.crypto && window.crypto.randomUUID) return window.crypto.randomUUID().toLowerCase(); } catch (e) { }
  var s = Date.now().toString(36) + '-';
  for (var i = 0; i < 24; i++) s += Math.floor(Math.random() * 36).toString(36);
  return s;
}

async function sdtCaiDat() {
  if (SDT_CD) return SDT_CD;
  SDT_CD = await api('vagabond.tra_truoc_khach.cai_dat', {});
  return SDT_CD;
}

/* Chip trạng thái số dư, cùng bảng màu chung: xanh ổn, vàng sắp hết, đỏ hết. */
function sdtChip(con) {
  if (con <= 0) return '<span style="background:#fef2f2;color:#b3261e;border-radius:999px;padding:2px 9px;font-size:11.5px;font-weight:700">Hết tiền</span>';
  if (con < 1000000) return '<span style="background:#fffbeb;color:#92400e;border-radius:999px;padding:2px 9px;font-size:11.5px;font-weight:700">Sắp hết</span>';
  return '';
}

/* ---- Màn 1: danh sách khách đang có tiền trả trước ----
   Dùng thanh công cụ chung (dsCongCu): một hàng chip trạng thái số dư và ô
   tìm, cùng nếp mọi màn danh sách khác. */
var sdtTt = '';
var SDT_TT = [
  { k: 'con', ten: 'Còn tiền', ic: '🟢' }, { k: 'sap_het', ten: 'Sắp hết', ic: '🟡' },
  { k: 'het', ten: 'Hết tiền', ic: '🔴' }, { k: 'cho', ten: 'Có phiếu chờ ghi sổ', ic: '⏳' },
];
function sdtTtCua(x) {
  var c = x.kha_dung_tam || 0;
  return c <= 0 ? 'het' : (c < 1000000 ? 'sap_het' : 'con');
}
async function scrSoDuTraTruoc() {
  frame('Số dư trả trước của khách', '<div class="emp"><div class="e1">⏳</div><div>Đang cộng số dư...</div></div>');
  var kq;
  try { kq = await api('vagabond.tra_truoc_khach.ds', { tim: sdtTim }); }
  catch (e) {
    frame('Số dư trả trước của khách', '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e)) + '</div></div>');
    return;
  }
  var tatCa = kq.khach || [];
  var dem = { tat_ca: tatCa.length };
  tatCa.forEach(function (x) {
    var t = sdtTtCua(x); dem[t] = (dem[t] || 0) + 1;
    if (x.cho_ghi_so) dem.cho = (dem.cho || 0) + 1;
  });
  var ds = tatCa.filter(function (x) {
    if (!sdtTt) return true;
    return sdtTt === 'cho' ? !!x.cho_ghi_so : sdtTtCua(x) === sdtTt;
  });
  var tong = 0, cho = 0;
  tatCa.forEach(function (x) { tong += x.kha_dung_tam || 0; cho += x.cho_ghi_so || 0; });
  var cc = {
    ma: 'sdt',
    ho: [{ k: 'tt', ds: SDT_TT, dem: dem, chon: sdtTt, tatCa: 'Mọi khách', mau: '#0d9488' }],
    tim: { gt: sdtTim, goiY: 'Tìm tên hoặc mã khách' },
  };
  var html = '<div class="card" style="padding:12px 13px">' +
    '<div style="font-size:12px;color:#8a8f9c">TIỀN KHÁCH ĐANG GỬI TIỆM</div>' +
    '<b style="font-size:24px;color:#0f766e">' + money(tong) + ' đ</b>' +
    '<div style="font-size:12.5px;color:#475467;margin-top:2px">' + tatCa.length + ' khách · trừ dần khi giao bánh' +
    (cho ? ' · ' + money(cho) + ' đ chờ kế toán ghi sổ' : '') + '</div>' +
    '<button class="btn" id="sdtNapMoi" style="margin:10px 0 0">＋ Nạp tiền trả trước</button></div>';
  html += dsCongCu(cc);
  html += '<div class="card">';
  if (!ds.length) {
    html += '<div class="emp" style="padding:24px"><div class="e1">💳</div><div>' +
      (tatCa.length ? 'Không có khách nào trong nhóm này.' :
        'Chưa có khách nào nạp tiền trả trước. Bấm Nạp tiền trả trước để ghi khoản khách đưa trước.') + '</div></div>';
  }
  ds.forEach(function (x) {
    html += '<div class="row" data-sdtk="' + h(x.khach) + '" style="cursor:pointer;display:flex;gap:10px;align-items:center;' +
      'padding:11px 13px;border-top:1px solid #f1f5f9;min-height:44px">' +
      '<div style="flex:1;min-width:0"><b>' + h(x.ten) + '</b> ' + sdtChip(x.kha_dung_tam || 0) +
      '<div style="font-size:12px;color:#7b8794;margin-top:2px">Nạp ' + money(x.da_nap + (x.cho_ghi_so || 0)) + ' · đã trừ ' +
      money(x.da_tru) + (x.giu_cho ? ' · đang giữ chỗ ' + money(x.giu_cho) : '') +
      (x.cho_ghi_so ? ' · chờ ghi sổ ' + money(x.cho_ghi_so) : '') + '</div></div>' +
      '<b style="white-space:nowrap;color:#0f766e">' + money(x.kha_dung_tam || 0) + '</b></div>';
  });
  html += '</div>';
  var than = frame('Số dư trả trước của khách', html);
  dsCongCuNoi(than, cc, function (ho, k) {
    if (ho === 'tt') sdtTt = k;
    else if (ho === 'tim') sdtTim = k;
    go(scrSoDuTraTruoc, true);
  });
  document.getElementById('sdtNapMoi').onclick = function () { sdtNap = null; go(scrSoDuNap); };
  document.querySelectorAll('[data-sdtk]').forEach(function (r) {
    r.onclick = function () { sdtKhachMo = r.getAttribute('data-sdtk'); go(scrSoDuKhach); };
  });
}

/* ---- Màn 3: sổ của một khách ---- */
async function scrSoDuKhach() {
  frame('Sổ trả trước', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc sổ...</div></div>');
  var kq;
  try { kq = await api('vagabond.tra_truoc_khach.so_khach', { khach: sdtKhachMo }); }
  catch (e) {
    frame('Sổ trả trước', '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e)) + '</div></div>');
    return;
  }
  var ten = kq.ten || kq.khach;
  var html = '<div class="card" style="padding:12px 13px">' +
    '<div style="font-size:12px;color:#8a8f9c">SỐ DƯ DÙNG ĐƯỢC · ' + h(ten) + '</div>' +
    '<b style="font-size:24px;color:#0f766e">' + money(kq.kha_dung_tam || 0) + ' đ</b> ' + sdtChip(kq.kha_dung_tam || 0) +
    (kq.giu_cho ? '<div style="font-size:12.5px;color:#475467;margin-top:2px">Đang giữ chỗ ' + money(kq.giu_cho) +
      ' đ cho đơn chưa ghi sổ.</div>' : '') +
    (kq.cho_ghi_so ? '<div style="margin-top:8px;padding:7px 9px;background:#fffbeb;border:1px solid #fde68a;border-radius:8px;' +
      'font-size:12.5px;color:#92400e">Có ' + money(kq.cho_ghi_so) + ' đ nạp đang chờ kế toán ghi sổ. Chọn trừ được ngay, ' +
      'nhưng đơn chỉ ghi sổ được khi phiếu nạp đã ghi sổ.</div>' : '') +
    '<button class="btn" id="sdtNapThem" style="margin:10px 0 0">＋ Nạp thêm</button></div>';
  html += '<div class="sec">Sổ chi tiết</div><div class="card">';
  if (!(kq.dong || []).length) html += '<div class="emp" style="padding:20px"><div>Chưa có dòng nào.</div></div>';
  (kq.dong || []).forEach(function (r) {
    var cong = r.loai === 'nap';
    html += '<div style="display:flex;gap:10px;align-items:center;padding:10px 13px;border-top:1px solid #f1f5f9">' +
      '<div style="flex:1;min-width:0"><div style="font-size:13.5px">' + h(posNgayVn(r.ngay)) + ' · ' +
      (cong ? 'Nạp, ' : '') + h(r.ghi_chu) + '</div>' +
      '<div style="font-size:12px;color:' + (r.cho ? '#b45309' : '#7b8794') + '">' + h(r.trang_thai) + ' · ' + h(r.chung_tu) + '</div>' +
      (cong && r.cho && kq.la_ke_toan
        ? '<button class="btn gh" data-sdtgs="' + h(r.chung_tu) + '" data-sdtdt="' + h(r.doctype) + '" ' +
          'style="margin:6px 0 0;width:auto;padding:6px 12px;min-height:36px;font-size:12.5px">✅ Ghi sổ phiếu nạp</button>' : '') +
      '</div><b style="white-space:nowrap;color:' + (cong ? '#05603a' : '#b3261e') + '">' +
      (cong ? '+' : '-') + money(r.so) + '</b></div>';
  });
  html += '</div>';
  frame('Sổ trả trước', html);
  document.getElementById('sdtNapThem').onclick = function () {
    sdtNap = { khach: { ma: kq.khach, ten: ten } };
    go(scrSoDuNap);
  };
  document.querySelectorAll('[data-sdtgs]').forEach(function (b) {
    b.onclick = async function () {
      if (!await xacNhan('Ghi sổ phiếu nạp ' + b.getAttribute('data-sdtgs') + '? Chỉ ghi sổ khi đã thấy tiền về.')) return;
      busy(true);
      try {
        await api('vagabond.tra_truoc_khach.ghi_so_phieu_nap', {
          doctype: b.getAttribute('data-sdtdt'), name: b.getAttribute('data-sdtgs') });
        busy(false); toast('Đã ghi sổ phiếu nạp.');
      } catch (e) { busy(false); return baoTin(errMsg(e), 'Chưa ghi sổ được'); }
      go(scrSoDuKhach, true);
    };
  });
}

/* ---- Màn 2: nạp tiền trả trước ---- */
async function scrSoDuNap() {
  var cd;
  try { cd = await sdtCaiDat(); }
  catch (e) { return baoTin(errMsg(e), 'Không mở được màn nạp'); }
  if (!sdtNap) sdtNap = {};
  var n = sdtNap;
  if (!n.anh) n.anh = [];
  if (!n.ma_lan) n.ma_lan = sdtMaLan();
  if (!n.quay && typeof posQuay !== 'undefined' && posQuay && posQuay.ma) n.quay = posQuay.ma;
  var ng = (cd.nguon || []).filter(function (x) { return x.ma === n.nguon; })[0];
  var html = '<div class="card" style="padding:12px 13px;display:grid;gap:10px">' +
    '<div><div style="font-size:13px;font-weight:700;margin-bottom:6px">Khách <b style="color:#b3261e">*</b></div>' +
    '<button class="btn gh" id="sdtChonKh" style="margin:0;text-align:left">' +
    (n.khach ? '👤 ' + h(n.khach.ten || n.khach.ma) + ' · ' + h(n.khach.ma) + ' (bấm để đổi)' : '🔍 Chọn khách nạp tiền') + '</button></div>' +
    '<div><div style="font-size:13px;font-weight:700;margin-bottom:6px">Số tiền <b style="color:#b3261e">*</b></div>' +
    '<input class="tin" id="sdtSoTien" inputmode="numeric" style="margin:0" placeholder="Ví dụ 50.000.000" value="' +
    (n.so_tien ? money(n.so_tien) : '') + '"></div>' +
    '<div><div style="font-size:13px;font-weight:700;margin-bottom:6px">Tiền về đâu <b style="color:#b3261e">*</b></div>' +
    '<div id="sdtNguon" style="display:grid;gap:6px">' +
    (cd.nguon || []).map(function (x) {
      var on = x.ma === n.nguon;
      return '<button type="button" data-sdtng="' + h(x.ma) + '" style="display:flex;gap:9px;align-items:center;text-align:left;' +
        'min-height:44px;padding:9px 10px;border-radius:10px;font-size:13.5px;cursor:pointer;border:1.5px solid ' +
        (on ? '#0d9488;background:#f0fdfa' : '#e4e7eb;background:#fff') + '">' +
        '<span style="width:18px;height:18px;border-radius:50%;flex:none;border:' + (on ? '6px solid #0d9488' : '2px solid #9aa5b1') + '"></span>' +
        '<span style="flex:1;min-width:0">' + h(x.nhan) + '<small style="display:block;color:#7b8794;font-size:11.5px">' +
        h(x.giai_thich) + '</small></span></button>';
    }).join('') + '</div>' +
    (n.nguon === 'gd_thu_ho' && cd.thieu_tk_gd
      ? '<div style="margin-top:6px;padding:7px 9px;background:#fef2f2;border:1px solid #fecaca;border-radius:8px;font-size:12.5px;' +
        'color:#b3261e">Chưa khai Tài khoản phải thu Giám đốc thu hộ trong Cài đặt. Nhờ kế toán khai trước rồi mới lập phiếu này.</div>' : '') +
    '</div>' +
    (ng && ng.can_quay
      ? '<div><div style="font-size:13px;font-weight:700;margin-bottom:6px">Quầy nhận tiền <b style="color:#b3261e">*</b></div>' +
        '<div style="display:flex;flex-wrap:wrap;gap:6px">' + (cd.quay || []).map(function (q) {
          var on = q.ma === n.quay;
          return '<button type="button" data-sdtq="' + h(q.ma) + '" style="min-height:40px;padding:7px 11px;border-radius:10px;' +
            'font-size:13px;cursor:pointer;border:1.5px solid ' + (on ? '#0d9488;background:#f0fdfa;color:#0f766e;font-weight:700' :
            '#e4e7eb;background:#fff;color:#344054') + '">' + h(q.ten) + '</button>';
        }).join('') + '</div><div style="font-size:12px;color:#7b8794;margin-top:4px">Màn Chốt ca của quầy này sẽ tính khoản tiền này vào két.</div></div>'
      : '') +
    '<div><div style="font-size:13px;font-weight:700;margin-bottom:6px">Ảnh chuyển khoản hoặc bill cà thẻ' +
    (ng && ng.can_anh ? ' <b style="color:#b3261e">*</b>' : '') + '</div>' +
    '<label class="tin" style="margin:0;display:flex;align-items:center;gap:9px;cursor:pointer">' +
    '<input type="file" accept="image/*" id="sdtAnh" multiple style="display:none"><span style="font-size:19px">📷</span>' +
    '<span style="font-size:13px;color:#475467">' + (n.anh.length ? 'Đã đính ' + n.anh.length + ' ảnh' : 'Đính ảnh') + '</span></label></div>' +
    '<div><div style="font-size:13px;font-weight:700;margin-bottom:6px">Mã giao dịch (nếu có)</div>' +
    '<input class="tin" id="sdtMaGd" style="margin:0" value="' + h(n.ma_gd || '') + '" placeholder="Mã giao dịch ngân hàng hoặc bill thẻ"></div>' +
    '<div><div style="font-size:13px;font-weight:700;margin-bottom:6px">Ghi chú</div>' +
    '<input class="tin" id="sdtGhiChu" style="margin:0" value="' + h(n.ghi_chu || '') + '" placeholder="Ví dụ: trả trước đặt bánh cả năm, trừ dần"></div>' +
    '<div style="font-size:12.5px;color:#475467;line-height:1.5;padding:8px 10px;background:#f8fafc;border-radius:9px">' +
    'Không xuất hoá đơn lúc nạp. Hoá đơn điện tử xuất từng đơn khi giao bánh, như đơn bình thường.</div>' +
    '<button class="btn" id="sdtLuuNap" style="margin:0">Lưu và gửi kế toán ghi sổ</button></div>';
  frame('Nạp tiền trả trước', html);
  function hut() {
    var o = document.getElementById('sdtSoTien');
    n.so_tien = Number(String((o && o.value) || '').replace(/[^0-9]/g, '')) || 0;
    n.ma_gd = (document.getElementById('sdtMaGd') || {}).value || '';
    n.ghi_chu = (document.getElementById('sdtGhiChu') || {}).value || '';
  }
  document.getElementById('sdtChonKh').onclick = function () {
    hut();
    sheetTimKhach('Chọn khách nạp tiền', function (x) {
      n.khach = { ma: x.name, ten: x.customer_name || x.name };
      go(scrSoDuNap, true);
    });
  };
  document.querySelectorAll('[data-sdtng]').forEach(function (b) {
    b.onclick = function () { hut(); n.nguon = b.getAttribute('data-sdtng'); go(scrSoDuNap, true); };
  });
  document.querySelectorAll('[data-sdtq]').forEach(function (b) {
    b.onclick = function () { hut(); n.quay = b.getAttribute('data-sdtq'); go(scrSoDuNap, true); };
  });
  var oa = document.getElementById('sdtAnh');
  oa.onchange = function () {
    hut();
    var cac = Array.prototype.slice.call(oa.files || []);
    if (!cac.length) return;
    n.anh = [];
    var con = cac.length;
    cac.forEach(function (f) {
      var fr = new FileReader();
      fr.onload = function () { n.anh.push({ ten: f.name, noi_dung: String(fr.result || '') }); if (!--con) go(scrSoDuNap, true); };
      fr.onerror = function () { if (!--con) go(scrSoDuNap, true); };
      fr.readAsDataURL(f);
    });
  };
  document.getElementById('sdtLuuNap').onclick = async function () {
    hut();
    if (!n.khach) return toast('Chọn khách nạp tiền.');
    if (!n.so_tien) return toast('Nhập số tiền khách nạp.');
    if (!n.nguon) return toast('Chọn tiền về đâu.');
    if (ng && ng.can_quay && !n.quay) return toast('Chọn quầy nhận tiền.');
    if (ng && ng.can_anh && !n.anh.length) return toast('Đính ảnh chuyển khoản hoặc bill cà thẻ.');
    if (!await xacNhan('Ghi khách ' + (n.khach.ten || n.khach.ma) + ' nạp ' + money(n.so_tien) + ' đ, ' +
      (ng ? ng.nhan.toLowerCase() : '') + '?')) return;
    busy(true);
    try {
      var kq = await api('vagabond.tra_truoc_khach.tao_phieu_nap', {
        khach: n.khach.ma, so_tien: n.so_tien, nguon: n.nguon, quay: n.quay || '',
        anh: n.anh.length ? JSON.stringify(n.anh) : '', ghi_chu: n.ghi_chu || '', ma_giao_dich: n.ma_gd || '',
        ma_lan: n.ma_lan,
      });
      busy(false);
      toast(kq && kq.trung ? 'Phiếu nạp này đã lập ở lần bấm trước, không lập thêm.'
        : 'Đã lập phiếu nạp, chờ kế toán ghi sổ.', 4000);
      sdtKhachMo = n.khach.ma;
      sdtNap = null;
      go(scrSoDuKhach, true);
    } catch (e) { busy(false); baoTin(errMsg(e), 'Chưa lập phiếu nạp'); }
  };
}

/* ---- Màn 4: khối Số dư trả trước trên đơn (Bill quầy, Doanh thu Sales) ----

   Chọn chip "Số dư trả trước" thì khối này mở: khách nào, còn bao nhiêu,
   trừ đơn này bao nhiêu. Thiếu thì chọn phương thức trả phần còn lại, máy
   tự chia. Lưu qua MỘT cửa máy chủ (tra_truoc_khach.ap_dung). */
var sdtDon = {};

async function sdtKhoiDon(px, d, dsPt, sauLuu) {
  var o = document.getElementById(px + 'SoDu');
  if (!o) return;
  var st = sdtDon[px + d.name];
  if (!st) {
    var c = String(d.customer || '');
    st = { khach: (c && c.indexOf('Khách lẻ') !== 0 && c !== 'Khách bán lẻ') ? { ma: c, ten: d.customer_name || c } : null,
      ptCon: '', mtc: '' };
    sdtDon[px + d.name] = st;
  }
  var s = null;
  if (st.khach) {
    o.innerHTML = '<div class="card" style="padding:12px 13px;font-size:12.5px;color:#98a2b3">Đang đọc số dư...</div>';
    try { s = await api('vagabond.tra_truoc_khach.so_du', { khach: st.khach.ma, si: d.name }); }
    catch (e) { o.innerHTML = '<div class="card" style="padding:12px 13px;color:#b3261e">' + h(errMsg(e)) + '</div>'; return; }
  }
  var tong = Number(d.grand_total || 0);
  var co = s ? Number(s.kha_dung_tam || 0) : 0;
  var tru = Math.min(tong, co), con = tong - tru;
  var khac = (dsPt || []).filter(function (p) { return ['Số dư trả trước', 'Hàng tặng', 'Công nợ'].indexOf(p) < 0; });
  var html = '<div class="card" style="padding:12px 13px;display:grid;gap:9px;margin-top:10px">' +
    '<div style="font-size:13px;font-weight:700">💳 Trừ vào số dư trả trước</div>' +
    '<button class="btn gh" data-sdtkh style="margin:0;text-align:left">' +
    (st.khach ? '👤 ' + h(st.khach.ten) + ' (bấm để đổi khách)' : '🔍 Chọn khách đã nạp tiền') + '</button>';
  if (st.khach && s) {
    html += '<div style="padding:9px 11px;background:#f0fdfa;border:1px solid #99f6e4;border-radius:9px;font-size:13px;line-height:1.6">' +
      'Số dư ' + h(st.khach.ten) + ': <b>' + money(co) + ' đ</b>' +
      (s.cho_ghi_so ? ' <span style="color:#92400e">(có ' + money(s.cho_ghi_so) + ' đ chờ kế toán ghi sổ)</span>' : '') +
      '<br>Trừ đơn này <b>' + money(tru) + ' đ</b>, còn lại ' + money(co - tru) + ' đ.</div>';
    if (co <= 0) {
      html += '<div style="font-size:12.5px;color:#b3261e">Khách này chưa còn số dư nào. Nạp tiền ở màn Số dư trả trước của khách, ' +
        'hoặc chọn phương thức khác.</div>';
    } else if (con > 0) {
      html += '<div style="font-size:13px;font-weight:700">Phần còn lại ' + money(con) + ' đ trả bằng <b style="color:#b3261e">*</b></div>' +
        '<div style="display:flex;flex-wrap:wrap;gap:6px">' + khac.map(function (p) {
          var on = p === st.ptCon;
          return '<button type="button" data-sdtpc="' + h(p) + '" style="min-height:40px;padding:7px 11px;border-radius:10px;' +
            'font-size:13px;cursor:pointer;border:1.5px solid ' + (on ? '#0d9488;background:#f0fdfa;color:#0f766e;font-weight:700' :
            '#e4e7eb;background:#fff;color:#344054') + '">' + h(p) + '</button>';
        }).join('') + '</div>' +
        '<input class="tin" id="' + px + 'SdtMtc" style="margin:0" placeholder="Mã tham chiếu của phần còn lại (nếu có)" value="' +
        h(st.mtc || '') + '">';
    }
    if (co > 0) {
      html += '<div style="font-size:12px;color:#7b8794;line-height:1.5">Trừ số dư thật khi đơn ghi sổ. Đơn huỷ thì tiền giữ chỗ trả lại số dư.</div>' +
        '<button class="btn" data-sdtluu style="margin:0">💳 Lưu: trừ số dư cho đơn này</button>';
    }
  }
  html += '</div>';
  o.innerHTML = html;
  o.onclick = async function (ev) {
    if (ev.target.closest('[data-sdtkh]')) {
      return sheetTimKhach('Chọn khách đã nạp tiền', function (x) {
        st.khach = { ma: x.name, ten: x.customer_name || x.name };
        sdtKhoiDon(px, d, dsPt, sauLuu);
      });
    }
    var t = ev.target.closest('[data-sdtpc]');
    if (t) {
      var om = document.getElementById(px + 'SdtMtc');
      st.mtc = om ? om.value : st.mtc;
      st.ptCon = t.getAttribute('data-sdtpc');
      return sdtKhoiDon(px, d, dsPt, sauLuu);
    }
    if (ev.target.closest('[data-sdtluu]')) {
      var om2 = document.getElementById(px + 'SdtMtc');
      st.mtc = om2 ? om2.value : st.mtc;
      if (con > 0 && !st.ptCon) return toast('Chọn phương thức trả phần còn lại ' + money(con) + ' đ.', 4000);
      busy(true);
      try {
        await api('vagabond.tra_truoc_khach.ap_dung', {
          si_name: d.name, khach: st.khach.ma, pt_con_lai: con > 0 ? st.ptCon : '', ma_tham_chieu: st.mtc || '',
        });
        busy(false);
        delete sdtDon[px + d.name];
        toast('Đã lưu: đơn trừ ' + money(tru) + ' đ vào số dư trả trước.', 4000);
        if (sauLuu) sauLuu();
      } catch (e) { busy(false); baoTin(errMsg(e), 'Chưa áp số dư trả trước'); }
    }
  };
}

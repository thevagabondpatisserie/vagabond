/* ---------------- Đơn đặt trước: bánh thiết kế riêng (v630)

   Anh Việt duyệt 02/11/2026 (bản 2 đề xuất Thiết kế riêng, sau góp ý Codex
   vòng 1): khách đặt và cọc 50% trên web, đơn đi luồng đặt bánh của app
   (dat_banh.py), không qua Pancake. Codex chỉ ra dat_banh chỉ là phần nền,
   chưa có màn nào để cửa hàng thu phần còn lại, giao bánh, xuất hoá đơn từ
   phiếu đặt và cấn tiền ứng trước. Màn này là phần đó.

   Mọi con số (tổng, đã thu, còn phải thu, trạng thái) do máy chủ tính
   (thiet_ke_rieng.tom_tat), màn chỉ hiện. Quyền chặn thật ở máy chủ
   (thiet_ke_rieng.QUYEN_TKR); danh sách dưới đây chỉ để ẩn ô và phải trùng
   tuyệt đối danh sách máy chủ (ca thu_thiet_ke_rieng_630 chốt). */
var QUYEN_TKR = ['Sales User', 'Sales Manager', 'System Manager', 'VGB - Quản lý cửa hàng',
  'Accounts User', 'Accounts Manager', 'Giám đốc'];
function coQuyenDdt() {
  return QUYEN_TKR.some(function (v) { return hasRole(v); });
}

var ddtTt = '';
var ddtTim = '';
/* Codex #531 vòng 3 (AGENTS 2b.3): hàng nhóm là điểm nhận, hàng ngày theo ngày
   nhận bánh. Mặc định "Mọi" để không giấu đơn nào khi mới mở màn. */
var ddtDiem = '';
var ddtNgay = '';
var ddtMo = '';
/* Màu chip trạng thái theo bảng chung: vàng chờ, xanh dương đang, xanh xong, xám huỷ. */
var DDT_MAU = {
  cho_coc: { ic: '⏳', nen: '#fef3c7', chu: '#92400e', mau: '#b45309' },
  da_coc: { ic: '💳', nen: '#e0f2fe', chu: '#075985', mau: '#0369a1' },
  du_tien: { ic: '✅', nen: '#dcfce7', chu: '#166534', mau: '#15803d' },
  da_giao: { ic: '🎂', nen: '#e5e7eb', chu: '#374151', mau: '#101828' },
  da_huy: { ic: '✕', nen: '#fee2e2', chu: '#991b1b', mau: '#98a2b3' },
};
var DDT_THU = ['Chủ Nhật', 'Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy'];

function ddtDdMm(s) {
  var p = String(s || '').slice(0, 10).split('-');
  return p.length === 3 ? p[2] + '/' + p[1] : String(s || '');
}
function ddtNhanNgay(ngay, homNay) {
  var p = String(ngay || '').split('-'), q = String(homNay || '').split('-');
  var d = new Date(+p[0], (+p[1] || 1) - 1, +p[2] || 1), n = new Date(+q[0], (+q[1] || 1) - 1, +q[2] || 1);
  var lech = Math.round((d - n) / 86400000);
  var dau = lech === 0 ? 'Hôm nay · ' : lech === 1 ? 'Ngày mai · ' : lech < 0 ? 'Đã qua · ' : '';
  return (dau + DDT_THU[d.getDay()] + ' ' + ddtDdMm(ngay)).toUpperCase();
}
function ddtChip(r) {
  var m = DDT_MAU[r.trang_thai] || DDT_MAU.cho_coc;
  return '<span style="background:' + m.nen + ';color:' + m.chu + ';border-radius:999px;padding:2px 9px;font-size:12px;font-weight:700;white-space:nowrap">' +
    m.ic + ' ' + h(r.nhan) + '</span>';
}
function ddtKhop(r, q) {
  var t = String(q || '').trim();
  if (!t) return true;
  var so = t.replace(/[^0-9]/g, '');
  if (so.length >= 3 && so.length === t.replace(/[\s.+-]/g, '').length) return String(r.sdt || '').replace(/[^0-9]/g, '').indexOf(so) >= 0;
  return vgbKhop([r.ma, r.khach, r.tac_pham, r.sdt], t);
}
function ddtThe(r) {
  var nhap = (r.phieu || []).filter(function (p) { return p.docstatus === 0; }).length;
  return '<div class="card" data-ddtthe="' + h(r.name) + '" role="button" tabindex="0" style="padding:12px 13px;cursor:pointer;min-height:44px">' +
    '<div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px">' +
    '<span style="font-size:15.5px;font-weight:800;color:#0b2a33">' + h(r.ma) + (r.gio ? ' · ' + h(r.gio) : '') + '</span>' + ddtChip(r) + '</div>' +
    /* Codex #531 vòng 7 (AGENTS 2b.4): ảnh tác phẩm từ danh mục, chưa có thì ô 🍰. */
    '<div style="display:flex;align-items:center;gap:10px;margin-top:4px">' + anhMon(r.anh) + '<div style="flex:1;min-width:0">' +
    '<div style="font-weight:700;font-size:15px">' + h(r.tac_pham) + (r.kich_co ? ' · size ' + h(r.kich_co) : '') + '</div>' +
    '<div style="font-size:13px;color:#475467;margin-top:2px">' + h(r.khach) + ' · ' + h(r.sdt) + (r.diem_nhan ? ' · ' + h(r.diem_nhan) : '') + '</div></div></div>' +
    '<div style="display:flex;justify-content:space-between;font-size:13.5px;margin-top:6px"><span>Tổng ' + money(r.tong) + 'đ</span>' +
    '<b style="color:' + (r.con_lai > 0 ? '#b45309' : '#15803d') + '">' + (r.con_lai > 0 ? 'Còn ' + money(r.con_lai) + 'đ' : 'Đã thu đủ') + '</b></div>' +
    (nhap ? '<div style="font-size:12.5px;color:#0369a1;margin-top:4px">' + nhap + ' phiếu chuyển khoản chờ kế toán ghi sổ</div>' : '') +
    '</div>';
}
function ddtTomTat(kq) {
  var dem = kq.dem || {}, rows = kq.rows || [];
  var con = rows.filter(function (r) { return r.trang_thai !== 'da_huy' && r.trang_thai !== 'da_giao'; });
  var tong = con.reduce(function (a, r) { return a + (r.con_lai || 0); }, 0);
  var o = (kq.trang_thai || []).filter(function (t) { return t.k !== 'da_huy'; }).map(function (t) {
    var m = DDT_MAU[t.k] || DDT_MAU.cho_coc, chon = ddtTt === t.k;
    return '<button class="btn gh" data-ddtso="' + h(t.k) + '" style="margin:0;min-height:44px;padding:8px 10px;text-align:left;display:block;width:100%;border-radius:11px;' +
      (chon ? 'border:2px solid ' + m.mau + ';' : '') + '"><div style="font-size:12.5px;color:#475467">' + m.ic + ' ' + h(t.ten) + '</div>' +
      '<div style="font-size:17px;font-weight:800;color:' + ((dem[t.k] || 0) ? m.mau : '#98a2b3') + '">' + (dem[t.k] || 0) + ' đơn</div></button>';
  }).join('');
  return '<div class="card" data-ddttom="1" style="padding:12px 13px">' +
    '<div style="font-size:11.5px;color:#98a2b3;letter-spacing:.4px">ĐƠN THIẾT KẾ RIÊNG ĐANG MỞ</div>' +
    '<div style="font-size:21px;font-weight:800;margin:2px 0 8px">' + con.length + ' đơn · còn phải thu ' + money(tong) + 'đ</div>' +
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:7px">' + o + '</div></div>';
}
function ddtVeDs(kq) {
  var tatCa = kq.rows || [];
  var ds = tatCa.filter(function (r) { return ddtTim ? ddtKhop(r, ddtTim) : (!ddtTt || r.trang_thai === ddtTt); });
  var html = '';
  if (ddtTim || ddtTt || ddtDiem || ddtNgay) {
    html += '<div data-ddtloc="1" style="display:flex;justify-content:space-between;gap:8px;margin:0 14px 4px;padding:8px 10px;border-radius:8px;background:#fffaeb;font-size:13px">' +
      '<span>Đang lọc' + (ddtTim ? ' "' + h(ddtTim) + '"' : '') + '</span><b>' + ds.length + ' đơn · còn ' +
      money(ds.reduce(function (a, r) { return a + (r.con_lai || 0); }, 0)) + 'đ</b></div>';
  }
  if (!ds.length) {
    return html + '<div class="card"><div class="emp" style="padding:24px"><div class="e1">🎂</div><div>' +
      (tatCa.length || kq.tong_goc ? 'Không có đơn nào khớp bộ lọc. Bấm Tất cả, Mọi điểm nhận hoặc Mọi ngày để xem hết.' :
        'Chưa có đơn bánh thiết kế riêng. Khách đặt ở tab Thiết kế riêng trên web, đơn hiện ở đây.') + '</div></div></div>';
  }
  var ngayCu = '';
  ds.forEach(function (r) {
    if (r.ngay !== ngayCu) {
      ngayCu = r.ngay;
      html += '<div style="font-size:12.5px;font-weight:700;color:#475467;margin:14px 16px 2px;letter-spacing:.3px">' + h(ddtNhanNgay(r.ngay, kq.hom_nay)) + '</div>';
    }
    html += ddtThe(r);
  });
  return html;
}

async function scrDonDatTruoc() {
  var tieuDe = 'Đơn đặt trước';
  if (!coQuyenDdt()) {
    frame(tieuDe, '<div class="emp"><div class="e1">🔒</div><div>Màn này mở cho Sales, quản lý cửa hàng, kế toán và giám đốc.</div></div>');
    return;
  }
  frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc đơn đặt trước...</div></div>');
  var kq;
  try { kq = await api('vagabond.thiet_ke_rieng.ds_don', {}); }
  catch (e) { frame(tieuDe, '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e)) + ' Kiểm tra mạng rồi mở lại màn.</div></div>'); return; }
  /* Lọc điểm nhận và ngày nhận áp cả thẻ tóm tắt lẫn danh sách; mỗi hàng chip
     đếm theo các hàng còn lại để số trên chip khớp số thẻ hiện ra. */
  var goc = kq.rows || [], homNay = kq.hom_nay;
  var theoNgay = goc.filter(function (r) { return dsTrongKhoangToi(r.ngay, ddtNgay, homNay); });
  var theoDiem = goc.filter(function (r) { return !ddtDiem || r.diem_nhan === ddtDiem; });
  var loc = theoNgay.filter(function (r) { return !ddtDiem || r.diem_nhan === ddtDiem; });
  var kqLoc = Object.assign({}, kq, { rows: loc, dem: dsDemTheo(loc, function (r) { return r.trang_thai; }), tong_goc: goc.length });
  var cacDiem = [];
  goc.forEach(function (r) { if (r.diem_nhan && cacDiem.indexOf(r.diem_nhan) < 0) cacDiem.push(r.diem_nhan); });
  var cc = {
    ma: 'ddt',
    ho: [{ k: 'tt', chon: ddtTt, mau: '#0d9488', tatCa: 'Tất cả', dem: kqLoc.dem,
      ds: (kq.trang_thai || []).map(function (t) { return { k: t.k, ten: t.ten, ic: (DDT_MAU[t.k] || {}).ic }; }) },
      { k: 'diem', chon: ddtDiem, tatCa: 'Mọi điểm nhận', dem: dsDemTheo(theoNgay, function (r) { return r.diem_nhan; }),
        ds: cacDiem.sort().map(function (d) { return { k: d, ten: dsNhanGon(d), ic: '📍' }; }) },
      { k: 'ngay', chon: ddtNgay, mau: '#b45309', tatCa: 'Mọi ngày', dem: dsDemKhoangToi(theoDiem, homNay), ds: dsKhoangToi() }],
    tim: { gt: ddtTim, goiY: '🔎 Tìm mã đơn, tên khách, số điện thoại' },
  };
  var html = dsCongCu(cc) + ddtTomTat(kqLoc) + '<div id="ddtDs">' + ddtVeDs(kqLoc) + '</div>' +
    '<div style="font-size:12px;color:#98a2b3;margin:10px 16px 18px;line-height:1.5">Khách đặt và cọc 50% trên web. Tiền cọc về thì máy lập phiếu thu chờ kế toán ghi sổ. Ngày nhận: thu phần còn lại, rồi giao bánh và xuất hoá đơn ở đây.</div>';
  var than = frame(tieuDe, html);
  dsCongCuNoi(than, cc, function (ho, k) {
    if (ho === 'tt') { ddtTt = k || ''; ddtTim = ''; }
    else if (ho === 'diem') ddtDiem = k || '';
    else if (ho === 'ngay') ddtNgay = k || '';
    else if (ho === 'tim') ddtTim = k;
    go(scrDonDatTruoc, true);
  });
  than.addEventListener('click', function (e) {
    var t = e.target.closest('[data-ddtso]');
    if (t) { var k = t.getAttribute('data-ddtso'); ddtTt = ddtTt === k ? '' : k; ddtTim = ''; go(scrDonDatTruoc, true); return; }
    t = e.target.closest('[data-ddtthe]');
    if (t) { ddtMo = t.getAttribute('data-ddtthe'); go(scrDonDatTruocCt); }
  });
  var o = document.getElementById('ddtDsTim');
  if (o) o.addEventListener('input', function () { ddtTim = o.value.trim(); var d = document.getElementById('ddtDs'); if (d) d.innerHTML = ddtVeDs(kqLoc); });
}

/* Quầy nhớ theo máy, lần chọn gần nhất (AGENTS 2b.9). */
function ddtQuayNho() { try { return localStorage.getItem('vgb_ddt_quay') || ''; } catch (e) { return ''; } }
function ddtNhoQuay(q) { try { localStorage.setItem('vgb_ddt_quay', q); } catch (e) { } }
function ddtChonQuay(ds, chon) {
  return kmHangChip((ds || []).map(function (q) { return posChipNut('data-ddtquay="' + h(q.ma) + '"', h(q.ten), q.ma === chon, false, '#0d9488'); }).join(''));
}
function ddtMoSheet(html) {
  var ov = document.createElement('div'); ov.className = 'sh';
  ov.innerHTML = '<div class="shb" style="padding:16px 16px calc(env(safe-area-inset-bottom,0px) + 18px)">' +
    '<div style="width:40px;height:4px;background:#d0d5dd;border-radius:2px;margin:0 auto 8px"></div>' + html + '</div>';
  document.body.appendChild(ov);
  ov.addEventListener('click', function (e) { if (e.target === ov) ov.remove(); });
  return ov;
}
async function ddtGoi(method, args, xong) {
  busy(true);
  try {
    var kq = await api(method, args);
    busy(false);
    toast(xong, 3600);
    go(scrDonDatTruocCt, true);
    return kq || true;
  } catch (e) {
    busy(false);
    toast(errMsg(e), 6000);
    return false;
  }
}
function ddtDocAnh(tep) {
  return new Promise(function (xong) {
    if (!tep) { xong(null); return; }
    var fr = new FileReader();
    fr.onload = function () { xong({ ten: tep.name, noi_dung: String(fr.result || '') }); };
    fr.onerror = function () { xong(null); };
    fr.readAsDataURL(tep);
  });
}

function ddtSheetThu(r, dsQuay) {
  var cach = 'tien_mat', quay = ddtQuayNho();
  if (!(dsQuay || []).some(function (q) { return q.ma === quay; })) quay = (dsQuay[0] || {}).ma || '';
  var ov = ddtMoSheet('<div style="font-size:18px;font-weight:700;margin:2px 0 6px">Thu phần còn lại</div>' +
    '<div style="font-size:14px;color:#475467">' + h(r.ma) + ' · ' + h(r.khach) + '</div>' +
    '<div style="font-size:24px;font-weight:800;color:#b45309;margin:6px 0 10px" data-ddtcon="1">' + money(r.con_lai) + 'đ</div>' +
    '<div style="font-size:13.5px;font-weight:700;color:#344054;margin:4px 0 6px">Khách trả bằng</div>' +
    '<div id="ddtCach"></div><div id="ddtThan" style="margin-top:12px"></div>');
  function veCach() {
    /* v637 (anh Việt 03/11/2026): thêm Thẻ OnePay, bỏ cà máy POS cho đơn đặt trước. */
    var cacCach = [['tien_mat', '💵 Tiền mặt'], ['qr', '🏦 Chuyển khoản qua QR']];
    if (r.onepay) cacCach.push(['the', '💳 Thẻ OnePay']);
    ov.querySelector('#ddtCach').innerHTML = kmHangChip(cacCach.map(function (c) {
      return posChipNut('data-ddtcach="' + c[0] + '"', c[1], cach === c[0], false, '#0d9488');
    }).join(''));
    var than = ov.querySelector('#ddtThan');
    if (cach === 'tien_mat') {
      than.innerHTML = '<div style="font-size:13.5px;font-weight:700;color:#344054;margin-bottom:6px">Quầy nhận tiền</div>' + ddtChonQuay(dsQuay, quay) +
        '<div style="font-size:12.5px;color:#475467;margin:8px 0 12px;line-height:1.5">Tiền mặt vào két quầy này, Chốt ca của quầy đếm khoản này.</div>' +
        '<button class="btn" data-ddtthutm="1" style="margin:0"' + (quay ? '' : ' disabled') + '>Đã thu tiền mặt ' + money(r.con_lai) + 'đ</button>';
    } else if (cach === 'the') {
      than.innerHTML = '<div data-ddtonepay="1" style="text-align:center;color:#475467;font-size:13.5px">Đang lấy mã thanh toán thẻ...</div>';
      ddtMoThe(r, ov);
    } else {
      var q = r.qr || {};
      than.innerHTML = (q.anh ? '<div style="text-align:center"><img alt="Mã QR chuyển khoản" src="' + h(q.anh) + '" style="width:220px;height:220px;background:#fff"></div>' :
        '<div style="color:#b3261e;font-size:13.5px">Không vẽ được mã QR. Đọc số tài khoản bên dưới cho khách chuyển tay.</div>') +
        '<div style="font-size:13.5px;line-height:1.7;margin:8px 0">' + h(q.ngan_hang || '') + ' · ' + h(q.stk || '') + '<br>Nội dung: <b>' + h(q.noi_dung || r.ma) + '</b></div>' +
        '<button class="btn" data-ddtkiem="1" style="margin:0">Khách đã chuyển, kiểm tiền về</button>' +
        '<div style="font-size:12.5px;color:#475467;margin-top:8px;line-height:1.5">Tiền về thì máy lập phiếu thu chờ kế toán đính giấy báo Có và ghi sổ. Ghi sổ xong mới giao bánh được.</div>';
    }
  }
  veCach();
  ov.addEventListener('click', async function (e) {
    var t = e.target.closest('[data-ddtcach]');
    if (t) { cach = t.getAttribute('data-ddtcach'); veCach(); return; }
    t = e.target.closest('[data-ddtquay]');
    if (t) { quay = t.getAttribute('data-ddtquay'); ddtNhoQuay(quay); veCach(); return; }
    t = e.target.closest('[data-ddtthutm]');
    if (t) {
      t.disabled = true;
      var ok = await ddtGoi('vagabond.thiet_ke_rieng.thu_tien_mat', { name: r.name, quay: quay }, 'Đã thu tiền mặt ' + money(r.con_lai) + 'đ của ' + r.ma);
      if (ok) ov.remove(); else t.disabled = false;
      return;
    }
    t = e.target.closest('[data-ddtkiem]');
    if (t) {
      t.disabled = true;
      busy(true);
      try {
        var kq = await api('vagabond.thiet_ke_rieng.kiem_tien_ve', { name: r.name });
        busy(false);
        if (kq && kq.lap) { toast('Đã thấy tiền về, máy lập phiếu thu chờ kế toán ghi sổ.', 4200); ov.remove(); go(scrDonDatTruocCt, true); }
        else { toast('Chưa thấy tiền về. Chờ một hai phút rồi bấm lại.', 4200); t.disabled = false; }
      } catch (er) { busy(false); toast(errMsg(er), 6000); t.disabled = false; }
    }
  });
}

/* v637: mã QR trang trả thẻ OnePay của đơn. Khách quét bằng điện thoại, nhập thẻ
   trên trang OnePay; màn hỏi lại số còn phải thu mỗi 4 giây, tiền về thì tự báo
   và đóng. Tiền thẻ ghi cho Sales (quầy không két), két quầy không cộng. */
var DDT_HOI_THE = 4000;
/* Giao dịch thẻ đã ghi nhận chưa có trong `daCo` (đối tượng mã -> 1). `daCo` null thì
   trả đối tượng các mã hiện có, làm mốc lúc mở. THUẦN. */
function ddtTheDaGhi(ds, daCo) {
  if (!daCo) { var m = {}; (ds || []).forEach(function (g) { if (g && g.ma) m[g.ma] = 1; }); return m; }
  return (ds || []).filter(function (g) { return g && g.ma && !daCo[g.ma]; });
}
function ddtConMo(ov, lan) { return !!ov.parentNode && ov._theLan === lan && cachDangLaThe(ov); }
function cachDangLaThe(ov) { return !!ov.querySelector('[data-ddtonepay]'); }
async function ddtMoThe(r, ov) {
  /* Mỗi lần mở cách Thẻ là một lượt; đổi cách, mở lại hay đóng sheet thì lượt cũ tự dừng hỏi. */
  var lan = (ov._theLan || 0) + 1;
  ov._theLan = lan;
  var o = ov.querySelector('[data-ddtonepay]');
  var kq;
  try { kq = await api('vagabond.onepay_dat.ma_the', { name: r.name }); }
  catch (e) { if (o && ddtConMo(ov, lan)) o.innerHTML = '<div style="color:#b3261e">' + h(errMsg(e)) + '</div>'; return; }
  if (!o || !ddtConMo(ov, lan)) return;
  /* Codex #538 vòng 2: số còn phải thu lấy từ máy chủ lúc mở, không từ màn đã nạp
     trước đó; đơn đã đủ thì không hiện QR. */
  var dau = Number(kq.con_lai) || 0;
  if (dau < 1) {
    o.innerHTML = '<div style="color:#067647;font-weight:700">Đơn ' + h(r.ma) + ' đã thu đủ, khách không cần trả thẻ.</div>';
    return;
  }
  o.innerHTML = '<img alt="Mã QR trả thẻ OnePay" data-ddttheqr="1" src="' + h(kq.anh) + '" style="width:220px;height:220px;background:#fff">' +
    '<div style="font-size:13.5px;line-height:1.6;margin:8px 0;color:#344054">Mời khách quét mã bằng camera điện thoại, bấm <b>Thanh toán bằng thẻ</b> rồi nhập thẻ trên trang OnePay.</div>' +
    '<div data-ddtthecho="1" style="font-size:13px;color:#b45309;font-weight:700">Đang chờ khách trả ' + money(dau) + 'đ...</div>' +
    '<div style="font-size:12.5px;color:#475467;margin-top:8px;line-height:1.5;text-align:left">Trả xong máy tự ghi phiếu thu cho Sales, két quầy không cộng khoản này. Thu ngân không cần cà máy POS.</div>';
  /* Chỉ báo "đã trả thẻ" khi máy chủ có giao dịch thẻ MỚI đã ghi nhận (so với lúc mở),
     không suy từ số còn phải thu: số đó còn giảm vì chuyển khoản, tiền mặt (Codex #538 vòng 2). */
  var daCo = ddtTheDaGhi(kq.the, null);
  async function hoi() {
    if (!ddtConMo(ov, lan)) return;
    var t;
    try { t = await api('vagabond.onepay_dat.con_lai', { name: r.name }); } catch (e) { t = null; }
    if (!ddtConMo(ov, lan)) return;
    var moi = t ? ddtTheDaGhi(t.the, daCo) : [];
    if (moi.length) {
      var so = moi.reduce(function (a, g) { return a + (Number(g.so_tien) || 0); }, 0);
      toast('Khách đã trả thẻ ' + money(so) + 'đ cho ' + r.ma, 4200);
      ov.remove();
      go(scrDonDatTruocCt, true);
      return;
    }
    if (t && (Number(t.con_lai) || 0) < 1) {
      toast('Đơn ' + r.ma + ' đã thu đủ qua cách khác, khách không cần trả thẻ.', 4200);
      ov.remove();
      go(scrDonDatTruocCt, true);
      return;
    }
    setTimeout(hoi, DDT_HOI_THE);
  }
  setTimeout(hoi, DDT_HOI_THE);
}

function ddtSheetGiao(r, dsQuay) {
  var quay = ddtQuayNho();
  if (!(dsQuay || []).some(function (q) { return q.ma === quay; })) quay = (dsQuay[0] || {}).ma || '';
  var ov = ddtMoSheet('<div style="font-size:18px;font-weight:700;margin:2px 0 6px">Giao bánh và xuất hoá đơn</div>' +
    '<div style="font-size:14px;color:#475467;line-height:1.6">' + h(r.ma) + ' · ' + h(r.tac_pham) + ' size ' + h(r.kich_co) + '<br>' + h(r.khach) + ' · tổng ' + money(r.tong) + 'đ, đã thu đủ</div>' +
    '<div style="font-size:13.5px;font-weight:700;color:#344054;margin:12px 0 6px">Quầy giao bánh</div><div id="ddtGq"></div>' +
    '<div style="font-size:12.5px;color:#475467;margin:10px 0 12px;line-height:1.5">Hoá đơn ngày hôm nay, phương thức Trả trước, cấn đúng các phiếu thu của đơn. Két quầy không cộng thêm khoản nào.</div>' +
    '<button class="btn" data-ddtgiaook="1" style="margin:0">Giao bánh và xuất hoá đơn</button>' +
    '<button class="btn gh" data-ddtdong="1" style="margin-top:9px">Để sau</button>');
  function ve() { ov.querySelector('#ddtGq').innerHTML = ddtChonQuay(dsQuay, quay); }
  ve();
  ov.addEventListener('click', async function (e) {
    var t = e.target.closest('[data-ddtquay]');
    if (t) { quay = t.getAttribute('data-ddtquay'); ddtNhoQuay(quay); ve(); return; }
    if (e.target.closest('[data-ddtdong]')) { ov.remove(); return; }
    t = e.target.closest('[data-ddtgiaook]');
    if (t) {
      if (!quay) { toast('Chọn quầy giao bánh.', 3000); return; }
      t.disabled = true;
      var ok = await ddtGoi('vagabond.thiet_ke_rieng.giao_banh', { name: r.name, quay: quay }, 'Đã giao bánh ' + r.ma + ' và xuất hoá đơn');
      if (ok) ov.remove(); else t.disabled = false;
    }
  });
}

function ddtSheetHuy(r) {
  var ov = ddtMoSheet('<div style="font-size:18px;font-weight:700;margin:2px 0 6px">Huỷ đơn ' + h(r.ma) + '</div>' +
    '<div style="font-size:13.5px;color:#475467;line-height:1.5">Chỉ huỷ được đơn chưa nhận đồng cọc nào. Đơn đã có tiền phải lập phiếu hoàn tiền.</div>' +
    '<div style="font-size:13.5px;font-weight:700;color:#344054;margin:12px 0 6px">Lý do (bắt buộc)</div>' +
    '<textarea class="nt" id="ddtLyDo" rows="2" maxlength="300" placeholder="Ví dụ: khách đổi ý, không chuyển cọc"></textarea>' +
    '<button class="btn" data-ddthuyok="1" style="margin:12px 0 0;background:#fff;border:2px solid #d92d20;color:#d92d20">Huỷ đơn</button>' +
    '<button class="btn gh" data-ddtdong="1" style="margin-top:9px">Không huỷ</button>');
  ov.addEventListener('click', async function (e) {
    if (e.target.closest('[data-ddtdong]')) { ov.remove(); return; }
    var t = e.target.closest('[data-ddthuyok]');
    if (!t) return;
    var lyDo = ov.querySelector('#ddtLyDo').value.replace(/\s+/g, ' ').trim();
    if (lyDo.length < 5) { toast('Ghi lý do huỷ.', 3000); return; }
    t.disabled = true;
    var ok = await ddtGoi('vagabond.thiet_ke_rieng.huy', { name: r.name, ly_do: lyDo }, 'Đã huỷ đơn ' + r.ma);
    if (ok) ov.remove(); else t.disabled = false;
  });
}

/* Nút chính của màn chi tiết, một nút to dính đáy theo trạng thái (2b.8). */
function ddtNutChinh(r) {
  if (r.trang_thai === 'da_giao' || r.trang_thai === 'da_huy') return '';
  var nhap = (r.phieu || []).some(function (p) { return p.docstatus === 0; });
  if (r.con_lai > 0) return '<button class="btn" id="ddtChinh" data-ddtthu="1" style="margin:0">Thu phần còn lại ' + money(r.con_lai) + 'đ</button>';
  if (nhap) return '<button class="btn" id="ddtChinh" disabled data-ddtcho="1" style="margin:0">Chờ kế toán ghi sổ phiếu chuyển khoản</button>';
  return '<button class="btn" id="ddtChinh" data-ddtgiao="1" style="margin:0">Giao bánh và xuất hoá đơn</button>';
}

async function scrDonDatTruocCt() {
  var tieuDe = 'Chi tiết đơn đặt trước';
  if (!coQuyenDdt() || !ddtMo) { go(scrDonDatTruoc, true); return; }
  frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc đơn...</div></div>');
  var r;
  try { r = await api('vagabond.thiet_ke_rieng.xem', { name: ddtMo }); }
  catch (e) { frame(tieuDe, '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e)) + ' Bấm quay lại rồi mở lại đơn.</div></div>'); return; }
  var dsQuay = r.quay || [], keToan = !!r.la_ke_toan;
  var html = '<div class="card" data-ddtct="' + h(r.name) + '" style="padding:12px 13px">' +
    '<div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px"><b style="font-size:18px">' + h(r.ma) + '</b>' + ddtChip(r) + '</div>' +
    '<div style="display:flex;align-items:center;gap:10px;margin-top:6px">' + anhMon(r.anh) +
    '<div style="font-size:15px;font-weight:700;flex:1;min-width:0">' + h(r.tac_pham) + (r.kich_co ? ' · size ' + h(r.kich_co) : '') + '</div></div>' +
    '<div style="font-size:13.5px;color:#475467;margin-top:2px">' + h(ddtNhanNgay(r.ngay, today())) + (r.gio ? ' lúc ' + h(r.gio) : '') + ' · ' + h(r.diem_nhan || '') + '</div>' +
    '<div style="font-size:13.5px;margin-top:2px">' + h(r.khach) + ' · <a href="tel:' + h(String(r.sdt || '').replace(/[^0-9+]/g, '')) + '">' + h(r.sdt) + '</a></div>' +
    '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-top:10px;font-size:12.5px;color:#475467">' +
    '<div>Tổng (gồm VAT)<br><b style="font-size:15px;color:#101828">' + money(r.tong) + 'đ</b></div>' +
    '<div>Cọc 50%<br><b style="font-size:15px;color:#101828">' + money(r.coc) + 'đ</b></div>' +
    '<div>Còn phải thu<br><b data-ddtconlai="1" style="font-size:15px;color:' + (r.con_lai > 0 ? '#b45309' : '#15803d') + '">' + money(r.con_lai) + 'đ</b></div></div></div>';
  html += '<div class="card" style="padding:12px 13px"><div style="font-size:13.5px;font-weight:700;margin-bottom:4px">Phiếu thu của đơn</div>' +
    ((r.phieu || []).length ? (r.phieu || []).map(function (p, i) {
      var cho = p.docstatus === 0;
      return '<div data-ddtpe="' + h(p.name) + '" style="display:flex;justify-content:space-between;align-items:center;gap:8px;padding:8px 0;border-top:1px solid #eef0f3;font-size:13.5px">' +
        '<span>' + h(p.pt || '') + ' · ' + h(ddtDdMm(p.ngay)) + '<br><span style="color:' + (cho ? '#0369a1' : '#15803d') + ';font-size:12.5px">' +
        (cho ? 'Chờ kế toán đính giấy báo Có và ghi sổ' : 'Đã ghi sổ') + ' · ' + h(p.name) + '</span></span>' +
        '<span style="text-align:right"><b>' + money(p.so_tien) + 'đ</b>' + (cho && keToan ? '<br><label class="btn gh" style="margin:4px 0 0;min-height:40px;padding:6px 10px;font-size:12.5px;display:inline-block">Đính và ghi sổ<input type="file" accept="image/*,application/pdf" data-ddtghiso="' + i + '" style="display:none"></label>' : '') + '</span></div>';
    }).join('') : '<div style="font-size:13px;color:#475467">Chưa có đồng nào. Khách chuyển cọc theo mã ' + h(r.ma) + ', máy tự nhận.</div>') + '</div>';
  /* Bảng kê dài (ghi chú khách gõ tới 500 ký tự) thu về đếm dòng, bấm mới mở (2b.17). */
  var bk = (r.bang_ke || []).filter(Boolean);
  html += '<details class="card" style="padding:12px 13px"><summary style="min-height:44px;display:flex;align-items:center;font-size:13.5px;font-weight:700;cursor:pointer">📝 Bảng kê ' + bk.length + ' dòng (in kèm hoá đơn)</summary>' +
    '<div style="font-size:13.5px;line-height:1.6;white-space:pre-line;color:#344054">' + bk.map(function (x) { return h(x); }).join('\n') + '</div></details>';
  if (r.hoa_don) html += '<div class="card" style="padding:12px 13px;font-size:13.5px">Hoá đơn ngày giao: <b>' + h(r.hoa_don) + '</b></div>';
  if (r.trang_thai === 'cho_coc') html += '<button class="btn gh" data-ddthuy="1" style="margin:4px 14px 18px;width:calc(100% - 28px);border:1.5px solid #f04438;color:#d92d20">Huỷ đơn chưa cọc</button>';
  var than = frame(tieuDe, html, { footer: ddtNutChinh(r) });
  var chinh = document.getElementById('ddtChinh');
  if (chinh) chinh.onclick = function () {
    if (chinh.hasAttribute('data-ddtthu')) ddtSheetThu(r, dsQuay);
    else if (chinh.hasAttribute('data-ddtgiao')) ddtSheetGiao(r, dsQuay);
  };
  than.addEventListener('click', function (e) {
    if (e.target.closest('[data-ddthuy]')) ddtSheetHuy(r);
  });
  than.querySelectorAll('[data-ddtghiso]').forEach(function (inp) {
    inp.addEventListener('change', async function () {
      var p = r.phieu[+inp.getAttribute('data-ddtghiso')];
      var anh = await ddtDocAnh(inp.files && inp.files[0]);
      if (!anh) { toast('Chưa đọc được tệp. Chọn lại ảnh hoặc PDF giấy báo Có.', 4000); return; }
      await ddtGoi('vagabond.thiet_ke_rieng.ghi_so_phieu', { name: r.name, phieu: p.name, anh: JSON.stringify([anh]) }, 'Đã ghi sổ phiếu ' + p.name);
    });
  });
}

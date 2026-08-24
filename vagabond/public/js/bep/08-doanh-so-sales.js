/* ---------- Doanh thu Sales: ra soat, chot le tung don, nhap tay ---------- */
var dsNgay = null;
var dsLoc = 'tat_ca', dsLocNg = '', dsLocHd = '';
function dsChip(txt, bg, fg) {
  return '<span style="display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:700;background:' + bg + ';color:' + fg + ';margin-right:5px;white-space:nowrap">' + txt + '</span>';
}
var DS_MAU_HD = {
  'Chờ duyệt': ['#fef3c7', '#92400e'], 'Chờ ký': ['#fef3c7', '#92400e'], 'Đang ký': ['#fef3c7', '#92400e'],
  'Đã ký': ['#dcfce7', '#166534'], 'Đã gửi CQT': ['#dcfce7', '#166534'], 'CQT chấp nhận': ['#bbf7d0', '#14532d'],
  'CQT báo lỗi': ['#fee2e2', '#991b1b'], 'Lỗi': ['#fee2e2', '#991b1b'], 'Đã hủy': ['#fee2e2', '#991b1b'],
  'HĐ điều chỉnh': ['#ede9fe', '#5b21b6'], 'HĐ thay thế': ['#ede9fe', '#5b21b6'],
  'Bị điều chỉnh': ['#ede9fe', '#5b21b6'], 'Bị thay thế': ['#ede9fe', '#5b21b6']
};
function dsChips(r) {
  var out = '';
  var tt = r.custom_hddt_trang_thai || '';
  if (r.custom_hddt_so || tt) {
    var mau = DS_MAU_HD[tt] || ['#e5e7eb', '#374151'];
    var nhan = (r.custom_hddt_so ? 'HĐ ' + h(r.custom_hddt_so) : 'HĐĐT') + (tt ? ' · ' + h(tt) : '');
    out += dsChip(nhan, mau[0], mau[1]);
  } else if (r.docstatus === 1) {
    out += dsChip('Chưa có HĐĐT', '#fee2e2', '#991b1b');
  }
  if (r.vgb_pt_thanh_toan) out += dsChip(h(r.vgb_pt_thanh_toan), '#e0f2fe', '#075985');
  else out += dsChip('Chưa chọn thanh toán', '#fee2e2', '#991b1b');
  /* SePay doc thang tu giao dich ngan hang, khong phu thuoc ai co go tay ma
     tham chieu hay khong. Truoc day chip nay bat theo o ma tham chieu nen
     don chuyen khoan da vao du tien van trong nhu chua nhan, con don ca the
     Payoo go so bill lai hien "SePay" - sai ca hai chieu. */
  if (r.sepay_du) out += dsChip('SePay ✓ đủ tiền', '#dcfce7', '#166534');
  else if (r.sepay_nhan) out += dsChip('SePay thiếu ' + money(Number(r.grand_total || 0) - Number(r.sepay_nhan || 0)) + ' đ', '#ffedd5', '#9a3412');
  if (r.vgb_ma_tham_chieu) out += dsChip('Mã ' + h(r.vgb_ma_tham_chieu), '#ede9fe', '#5b21b6');
  if (r.vgb_xhd_mst) out += dsChip('Xuất cho công ty / HKD', '#fef9c3', '#854d0e');
  /* Đơn có giảm giá cho khách thì phải nhìn ra ngay trên danh sách, khỏi mở
     từng đơn (anh Việt 24/08/2026). */
  if (r.giam_dong) out += dsChip('🏷️ Giảm ' + money(r.giam_dong) + ' đ', '#fef2f2', '#b3261e');
  if (r.trung) out += dsChip('⚠ Trùng phiếu', '#fee2e2', '#991b1b');
  return out;
}
async function scrDoanhSo() {
  if (!dsNgay) dsNgay = today();
  frame('Doanh thu Sales', '<div class="emp"><div class="e1">⏳</div><div>Đang tải doanh thu...</div></div>');
  var d;
  try { d = await api('vagabond.ban_hang.bang_doanh_so', { ngay: dsNgay }); }
  catch (e) { frame('Doanh thu Sales', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được, thử lại sau') + '</div></div>'); return; }
  var rows = d.rows || [];
  var nhap = rows.filter(function (r) { return r.docstatus === 0; });
  var html = '<div class="card" style="padding:12px 14px;display:flex;align-items:center;gap:12px">' +
    '<div style="font-weight:600;white-space:nowrap">Ngày bán</div>' +
    '<input type="date" class="hin" id="dsDate" value="' + dsNgay + '" max="' + today() + '" style="flex:1;margin:0">' +
    '</div>' + '<div class="card" style="padding:2px 14px 12px">' + chipNgay('data-dsbuoc') + '</div>';
  html += '<div class="card" style="padding:12px 14px">' +
    '<div style="display:flex;justify-content:space-between"><span>Chưa chốt</span><b>' + money(d.tong_nhap) + ' đ · ' + nhap.length + ' đơn</b></div>' +
    '<div style="display:flex;justify-content:space-between;margin-top:6px"><span>Đã chốt</span><b style="color:#0a8a4a">' + money(d.tong_chot) + ' đ · ' + (rows.length - nhap.length) + ' đơn</b></div>' +
    (d.dong_bo_luc ? '<div style="color:#a0a6b4;font-size:12px;margin-top:6px">Máy tự đồng bộ Pancake 30 phút một lần · lần cuối ' + h(d.dong_bo_luc) + '</div>' : '') +
    '<div id="dsChoGiao"></div></div>';
  if (d.so_don_trung) {
    html += '<div class="sec">Đơn bị trùng phiếu</div><div class="card" style="padding:12px 14px;border:1.5px solid #fecaca;background:#fff1f2;color:#991b1b;font-size:13px;line-height:1.6">' +
      '<b>' + d.so_don_trung + ' đơn đang có hai mã phiếu</b><br>' +
      'Một đơn Pancake mà thành hai phiếu thì ghi sổ xong doanh thu bị tính đôi. Bấm nút dưới, hệ thống giữ lại một phiếu và gỡ phiếu thừa (chỉ gỡ phiếu còn nháp, phiếu đã ghi sổ hay đã có hoá đơn điện tử thì hệ thống không đụng vào).' +
      '<div style="margin-top:10px"><button class="btn gh" data-ds="gotrung" style="width:100%">🧹 Rà và gỡ phiếu trùng</button></div></div>';
  }
  if ((d.loi || []).length) {
    html += '<div class="sec">Cần xử lý trước khi chốt</div><div class="card" style="padding:12px 14px;color:#b3261e;font-size:13px;line-height:1.6">' + d.loi.map(h).join('<br>') + '</div>';
  }
  /* Bo loc nhanh: sau muoi may dong ma soat bang mat thi de sot. */
  /* Bo loc hai tang: tinh trang x nguon/phuong thuc, giao nhau de soat
     duoc kieu "GrabFood ma chua ve tien" (anh Viet 10/08/2026). */
  var DSTT = [
    { k: 'tat_ca', nhan: 'Tất cả', loc: function () { return true; } },
    { k: 'chua_ghi', nhan: '📄 Chưa ghi sổ', loc: function (r) { return r.docstatus === 0; } },
    { k: 'da_ghi', nhan: '✅ Đã ghi sổ', loc: function (r) { return r.docstatus === 1; } },
    { k: 'chua_pt', nhan: '❓ Chưa chọn thanh toán', loc: function (r) { return r.docstatus === 0 && !r.vgb_pt_thanh_toan; } },
    /* Đơn đã giao xong mà Pancake không ghi nhận khoản nào. Máy CHỈ gắn cờ
       để sales rà lại, không bao giờ tự ghi là Công nợ - anh Việt chốt
       15/08/2026 sau khi đo thấy suy kiểu này ra 16 đơn trong khi sales chỉ
       đánh dấu 3 đơn là công nợ thật. */
    { k: 'nghi_no', nhan: '🧾 Nghi công nợ', loc: function (r) { return !!r.vgb_nghi_cong_no && !r.vgb_pt_thanh_toan; } },
    { k: 'chua_tien', nhan: '⏳ Chuyển khoản chưa về tiền', loc: function (r) { return r.vgb_pt_thanh_toan === 'Chuyển khoản' && !r.sepay_du; } },
    { k: 'du_tien', nhan: '💰 SePay đã đủ tiền', loc: function (r) { return !!r.sepay_du; } },
    { k: 'chua_hddt', nhan: '📌 Chưa có hoá đơn điện tử', loc: function (r) { return r.docstatus === 1 && !r.custom_hddt_so; } },
    { k: 'xhd_cty', nhan: '🏢 Xuất hoá đơn công ty', loc: function (r) { return !!(r.vgb_xhd_mst || r.can_hddt); } },
    { k: 'trung', nhan: '⚠ Trùng phiếu', loc: function (r) { return !!r.trung; } }
  ];
  var DSNG = locNguonPt(rows);
  var DSHD = locHddt();
  if (!locTim(DSTT, dsLoc) || locTim(DSTT, dsLoc).k !== dsLoc) dsLoc = 'tat_ca';
  var fTt = locTim(DSTT, dsLoc), fNg = locTim(DSNG, dsLocNg), fHd = locTim(DSHD, dsLocHd);
  dsLocNg = fNg.k; dsLocHd = fHd.k;
  html += '<div class="card" style="padding:10px 12px;display:flex;flex-direction:column;gap:7px">' +
    locHang(DSTT, dsLoc, 'data-loc', rows) +
    locHang(DSNG, dsLocNg, 'data-locng', rows.filter(fTt.loc)) +
    locHang(DSHD, dsLocHd, 'data-lochd', rows.filter(fTt.loc)) + '</div>';
  var loc = rows.filter(function (r) { return fTt.loc(r) && fNg.loc(r) && fHd.loc(r); });
  html += locKhoiTong(loc, [
    dsLoc === 'tat_ca' ? '' : fTt.nhan, fNg.k ? fNg.nhan : '', fHd.k ? fHd.nhan : ''
  ].filter(Boolean).join(' · '));
  html += '<div class="sec">Đơn trong ngày · bấm vào đơn để xem chi tiết</div><div class="card">';
  if (!rows.length) html += '<div class="emp" style="padding:24px"><div class="e1">🌤️</div><div>Chưa có đơn nào. Bấm Đồng bộ để kéo từ Pancake, hoặc dấu ➕ để nhập tay đơn Grab, Be.</div></div>';
  else if (!loc.length) html += '<div class="emp" style="padding:24px"><div class="e1">✅</div><div>Không có đơn nào thuộc nhóm <b>' + fTt.nhan + (fNg.k ? ' · ' + fNg.nhan : '') + '</b>.</div></div>';
  loc.forEach(function (r) {
    var kh = (r.remarks || '').split(' - ');
    var ng = (r.custom_nguon && r.custom_nguon !== 'Pancake') ? h(r.custom_nguon) + ' ' : '';
    var dong2 = h(r.name) + ' · ' + (r.docstatus === 1 ? 'Đã chốt' : 'Nháp');
    var chips = dsChips(r);
    html += '<div class="hub" data-si="' + h(r.name) + '" data-can="' + (r.can_hddt ? 1 : 0) + '"><div class="hi">' + (r.docstatus === 1 ? '✅' : '📝') + '</div>' +
      '<div class="ht"><div class="h1">' + ng + '#' + h(r.custom_pancake_display_id || '?') + ' · ' + h(kh[1] || 'Khách lẻ') + '</div>' +
      '<div class="h2">' + dong2 + '</div>' + (chips ? '<div class="h2" style="margin-top:4px;line-height:1.9">' + chips + '</div>' : '') + '</div>' +
      '<b style="white-space:nowrap;font-size:13px">' + money(r.grand_total) + '</b></div>';
  });
  html += '</div>';

  /* Cua vao man Don da huy cho hoan. Dat o day chu khong o trang chu vi
     anh Viet chon 21/08/2026: sales dang xem don thi nhay qua duoc ngay.
     Huy hieu dem nap sau, de man chinh khong phai cho them mot luot goi. */
  html += '<div class="card" style="margin-top:2px"><div class="hub" data-ds="donhuy">' +
    '<div class="hi">↩️</div><div class="ht">' +
    '<div class="h1">Đơn đã huỷ chờ hoàn tiền</div>' +
    '<div class="h2" id="dsDemHuy">Đơn khách huỷ mà tiền vẫn còn ở công ty</div>' +
    '</div><div style="color:#98a2b3;font-size:18px">›</div></div></div>';

  var foot = '<div style="display:flex;gap:10px"><button class="btn gh" data-ds="dongbo" style="flex:1">🔄 Đồng bộ Pancake</button>' +
    (nhap.length ? '<button class="btn" data-ds="chot" style="flex:2">Ghi sổ hoá đơn bán hàng (' + nhap.length + ' đơn)</button>' : '') + '</div>';
  var b = frame('Doanh thu Sales', html, { footer: foot, action: '➕', onAction: function () { go(scrDsNhapTay); } });
  var di = document.getElementById('dsDate');
  if (di) di.onchange = function () { if (di.value && di.value <= today()) { dsNgay = di.value; dsLoc = 'tat_ca'; dsLocNg = ''; go(scrDoanhSo, true); } };
  veODate('dsDate');
  /* Doanh thu chi ghi nhan don DA GIAO XONG. Sang som chua ai giao thi
     man nay 0 dong, sales tuong mat dong bo roi bam Dong bo hoai (anh Viet
     bao 11/08/2026). Nay dem luon so don CON CHO GIAO de biet la binh
     thuong, khong phai hong. */
  (async function () {
    try {
      var vd = await getList('Van Don', {
        fields: ['name', 'trang_thai'],
        filters: { ngay_giao: dsNgay },
        limit_page_length: 0
      });
      var cho = (vd || []).filter(function (x) { return x.trang_thai === 'Chờ giao' || x.trang_thai === 'Đang giao'; }).length;
      var o2 = document.getElementById('dsChoGiao');
      if (o2 && cho) {
        o2.innerHTML = '<div style="margin-top:8px;background:#ecfeff;border:1.5px solid #7fe5f6;border-radius:9px;padding:9px 11px;font-size:12.5px;color:#0b7c93;line-height:1.5">' +
          '🛵 Còn <b>' + cho + ' đơn chưa giao xong</b> trong ngày. Doanh thu chỉ ghi nhận khi đơn đã giao thành công, nên số ở trên còn thiếu là bình thường.</div>';
      }
    } catch (e2) { }
  })();
  timDonGan();
  /* Dem so don dang cho hoan, nap rieng va nuot loi: mot cai huy hieu hong
     khong duoc lam chet ca man doanh thu. */
  (async function () {
    try {
      var n = await api('vagabond.don_huy.dem_cho_hoan', {});
      var o3 = document.getElementById('dsDemHuy');
      if (o3 && n) {
        o3.innerHTML = '<b style="color:#b3261e">' + n + ' đơn</b> đang chờ hoàn tiền';
      }
    } catch (e3) { }
  })();
  b.addEventListener('click', function (e) {
    var t = e.target.closest('[data-dsbuoc]'); if (!t) return;
    var bu = +t.getAttribute('data-dsbuoc');
    var moi = bu ? ngayCong(dsNgay, bu) : today();
    if (moi > today()) return toast('Chưa tới ngày đó.');
    dsNgay = moi; dsLoc = 'tat_ca'; dsLocNg = '';
    go(scrDoanhSo, true);
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-loc]'), function (el) {
    el.onclick = function () { dsLoc = el.getAttribute('data-loc'); go(scrDoanhSo, true); };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-lochd]'), function (el) {
    el.onclick = function () { dsLocHd = el.getAttribute('data-lochd'); go(scrDoanhSo, true); };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-locng]'), function (el) {
    el.onclick = function () { dsLocNg = el.getAttribute('data-locng'); go(scrDoanhSo, true); };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-ds]'), function (el) {
    el.onclick = function () { dsHanh(el.getAttribute('data-ds')); };
  });
  b.addEventListener('click', function (e) {
    var r = e.target.closest('[data-si]'); if (!r) return;
    var nm = r.getAttribute('data-si'), can = r.getAttribute('data-can') === '1';
    go(function () { scrDsView(nm, can); });
  });
}
var dsDangDongBo = false;
async function dsHanh(k) {
  if (k === 'donhuy') return go(scrDonHuy);
  if (k === 'gotrung') {
    busy(true);
    var ke;
    try { ke = await api('vagabond.ban_hang.ds_don_trung', { ngay: dsNgay }); }
    catch (e) { busy(false); baoTin((e && e.message) || 'Không rà được'); return; }
    busy(false);
    var nhom = (ke && ke.nhom) || [];
    if (!nhom.length) { toast('Rà xong, không còn đơn nào bị trùng.'); go(scrDoanhSo, true); return; }
    var mo = nhom.map(function (n) {
      return '#' + n.don + ': giữ ' + n.giu + (n.go.length ? ', gỡ ' + n.go.join(', ') : '') + (n.ket.length ? '\n   ' + n.ket.join('\n   ') : '');
    }).join('\n');
    if (!await xacNhan('Hệ thống sẽ xử lý như sau: ' + mo + '\n\nĐồng ý gỡ chứ?')) return;
    busy(true);
    try { var kq3 = await api('vagabond.ban_hang.go_don_trung', { ngay: dsNgay }); busy(false); toast('Đã gỡ ' + (kq3.da_go || []).length + ' phiếu thừa' + ((kq3.ket || []).length ? ', ' + kq3.ket.length + ' phiếu phải xử lý tay' : ''), 3500); if ((kq3.ket || []).length) baoTin(kq3.ket.join('\n')); }
    catch (e) { busy(false); baoTin((e && e.message) || 'Gỡ lỗi'); }
    go(scrDoanhSo, true); return;
  }
  if (k === 'dongbo') {
    /* Bam hai lan trong vong vai giay la hai yeu cau chay song song, moi ben
       tao mot phieu cho cung mot don. May chu da co khoa, day chan them o
       ngay dau ngon tay cho khoi phai cho bao loi. */
    if (dsDangDongBo) { toast('Đang đồng bộ rồi, chờ chút nhé.'); return; }
    dsDangDongBo = true;
    busy(true);
    try { var kq = await api('vagabond.ban_hang.dong_bo_doanh_so', { ngay: dsNgay }); busy(false); toast('Kéo ' + (kq.so_don_pancake || 0) + ' đơn: ' + (kq.tao_moi || 0) + ' mới, ' + (kq.cap_nhat || 0) + ' cập nhật' + ((kq.loi || []).length ? ', ' + kq.loi.length + ' lỗi' : ''), 3500); }
    catch (e) { busy(false); baoTin((e && e.message) || 'Đồng bộ lỗi'); }
    dsDangDongBo = false;
    go(scrDoanhSo, true); return;
  }
  if (k === 'chot') {
    if (!await xacNhan('Chốt TOÀN BỘ đơn nháp của ngày ' + dsNgay.split('-').reverse().join('/') + '? Muốn chốt lẻ thì bấm vào từng đơn.')) return;
    busy(true);
    try {
      var kq2 = await api('vagabond.ban_hang.chot_doanh_so', { ngay: dsNgay }); busy(false);
      toast('Đã chốt ' + kq2.da_chot + ' đơn, xuất ' + (kq2.da_xuat_hddt || 0) + ' hoá đơn điện tử' + ((kq2.loi || []).length ? ', ' + kq2.loi.length + ' đơn cần xem lại' : ''), 4000);
      if ((kq2.loi || []).length) baoTin(kq2.loi.join('\n'));
    }
    catch (e) { busy(false); baoTin((e && e.message) || 'Chốt lỗi'); }
    go(scrDoanhSo, true); return;
  }
}
var CFGBH = null;
async function cfgBanHang() {
  if (!CFGBH) CFGBH = await api('vagabond.ban_hang.cau_hinh_ban_hang', {});
  return CFGBH;
}
function nguonBH(v) {
  var r = null;
  ((CFGBH || {}).nguon || []).forEach(function (n) { if (n.v === v) r = n; });
  return r;
}
function ptTheoNguon(v) {
  var c = CFGBH || { pt: [], nguon: [] };
  var n = nguonBH(v);
  var ds = n ? n.pt : (c.pt_pancake || []);
  return (c.pt || []).filter(function (p) { return ds.indexOf(p.v) >= 0; });
}
function quyPt(v) {
  var r = null;
  ((CFGBH || {}).pt || []).forEach(function (p) { if (p.v === v) r = p; });
  return r;
}
function chipPt(ds, chon) {
  return ds.map(function (p) {
    var on = p.v === chon;
    return '<button class="ptc" data-pt="' + p.v + '" style="display:inline-flex;align-items:center;gap:6px;padding:6px 10px;border-radius:8px;font-size:13px;border:1.5px solid ' +
      (on ? '#0d9488;background:#ccfbf1;color:#0f766e;font-weight:bold' : '#e5e7eb;background:#fff;color:#374151') + '">' +
      (p.lg ? '<img src="' + p.lg + '" style="height:18px;border-radius:3px">' : '🏦 ') + p.v + '</button>';
  }).join('');
}
function veChipPt(wrap, chon) {
  if (!wrap) return;
  wrap.querySelectorAll('.ptc').forEach(function (x) {
    var on = x.getAttribute('data-pt') === chon;
    x.style.border = '1.5px solid ' + (on ? '#0d9488' : '#e5e7eb');
    x.style.background = on ? '#ccfbf1' : '#fff';
    x.style.color = on ? '#0f766e' : '#374151';
    x.style.fontWeight = on ? 'bold' : 'normal';
  });
}
/* O ngay tren MAY TINH: tren dien thoai cham dau vao o cung mo lich,
   nhung tren laptop thi phai bam trung dung cai bieu tuong lich be xiu o
   goc phai - anh Viet 11/08/2026 bao khong chon duoc ngay. Nay bam bat cu
   dau trong o la lich bat ra (showPicker), khong con phai nham nhi. */
/* Cong tru mot ngay cho o ngay. Thu ngan doi ngay chu yeu la "hom qua"
   hay "hom nay", bam chip nhanh hon mo lich nhieu - va chac an tren MOI
   may, khong phu thuoc lich cua trinh duyet (anh Viet 11/08/2026). */
function ngayCong(iso, buoc) {
  var d = new Date(String(iso || today()) + 'T00:00:00');
  d.setDate(d.getDate() + buoc);
  var hs = function (n) { return (n < 10 ? '0' : '') + n; };
  return d.getFullYear() + '-' + hs(d.getMonth() + 1) + '-' + hs(d.getDate());
}
function chipNgay(attr) {
  return '<div style="display:flex;gap:7px;flex-wrap:wrap;margin-top:9px">' +
    posChipNut(attr + '="-1"', '\u25c0 Hôm trước', false) +
    posChipNut(attr + '="0"', 'Hôm nay', false) +
    posChipNut(attr + '="1"', 'Hôm sau \u25b6', false) +
    '</div>' + timDonO();
}

/* ---------- Ô tìm đơn, dùng chung mọi màn tính tiền ----------

   Anh Việt 18/08/2026: *"em viết script để có thêm ô Tìm kiếm... cho tất cả
   các màn tính tiền ở mọi điểm bán luôn. Nhập bất cứ thông tin gì thì cũng
   sẽ có thể tìm ra được đơn ấy nhanh, hiện tại anh đang phải dò bằng tay
   nếu muốn kiếm lại 1 đơn nào đó"*.

   Điểm cốt lõi: ô này tìm KHÔNG GIỚI HẠN NGÀY. Các màn tính tiền đều xem
   theo ngày, nên muốn tìm lại một đơn cũ mà không nhớ ngày thì phải lật
   từng ngày một, đúng là dò tay. Gõ mã đơn Pancake, mã đơn ERP, số điện
   thoại, tên khách hay địa chỉ đều ra.

   Gõ xong bấm Enter hoặc nút kính lúp chứ không tìm theo từng phím: mỗi
   phím là một lượt gọi máy chủ, mà đây là ô tra cứu chứ không phải ô lọc
   danh sách đang hiện. */
function timDonO() {
  return '<div style="display:flex;gap:7px;margin-top:9px">' +
    '<input id="tdO" placeholder="Nhập mã đơn Pancake, mã đơn ERP, SĐT, tên khách, địa chỉ..." ' +
    'style="flex:1;min-width:0;border:1.5px solid #e5e7eb;border-radius:9px;padding:9px 12px;font-size:13px">' +
    '<button id="tdNut" class="btn gh" style="margin:0;width:auto;padding:8px 14px;flex:0 0 auto">🔍</button>' +
    '</div>';
}

/* Gắn sự kiện cho ô tìm. Gọi sau mỗi lần vẽ lại màn. */
function timDonGan() {
  var o = document.getElementById('tdO');
  var n = document.getElementById('tdNut');
  if (!o || !n) return;
  var chay = function () { timDonChay(String(o.value || '')); };
  n.onclick = chay;
  o.onkeydown = function (e) { if (e.key === 'Enter') { e.preventDefault(); chay(); } };
}

async function timDonChay(tu) {
  tu = String(tu || '').trim();
  if (tu.length < 3) return toast('Vui lòng gõ ít nhất 3 ký tự rồi tìm.', 3500);
  busy(true);
  var kq;
  try { kq = await api('vagabond.ban_hang.tim_don', { tu_khoa: tu }); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Không tìm được', 'Lỗi tìm đơn'); }
  busy(false);
  var ds = (kq && kq.ds) || [];
  if (!ds.length) return baoTin((kq && kq.vi_sao) || 'Không thấy đơn nào khớp.', 'Không tìm thấy');

  var than = '<div style="font-size:12.5px;color:#6b7280;margin-bottom:9px">Tìm "' +
    h(kq.tu_khoa || tu) + '" · ' + ds.length + ' đơn, mới nhất lên trước. Bấm vào một dòng để mở.</div>' +
    ds.map(function (x) {
      var vn = String(x.ngay || '').split('-').reverse().join('/');
      var tt = x.vgb_huy ? 'đã huỷ' : (x.docstatus === 1 ? 'đã chốt' : 'chưa chốt');
      var mau = x.vgb_huy ? '#b3261e' : (x.docstatus === 1 ? '#0a8a4a' : '#b45309');
      return '<div data-td="' + h(x.name) + '" style="padding:11px 12px;border:1px solid #eef0f4;' +
        'border-radius:10px;margin-bottom:7px;cursor:pointer">' +
        '<div style="display:flex;gap:8px;align-items:center">' +
        '<div style="flex:1;min-width:0"><b style="font-size:13.5px">' +
        h(x.ten_tren_don || '(khách lẻ)') + '</b>' +
        '<div style="font-size:11.5px;color:#98a2b3">' + h(x.name) +
        (x.custom_pancake_display_id ? ' · Pancake #' + h(x.custom_pancake_display_id) : '') +
        '</div></div>' +
        '<div style="text-align:right"><b style="font-size:14px">' + money(x.grand_total) + ' đ</b>' +
        '<div style="font-size:11px;font-weight:700;color:' + mau + '">' + tt + '</div></div></div>' +
        '<div style="font-size:11.5px;color:#6b7280;margin-top:4px">' + vn +
        (x.sdt_tren_don ? ' · ' + h(x.sdt_tren_don) : '') +
        (x.custom_nguon ? ' · ' + h(x.custom_nguon) : '') +
        (x.vgb_pt_thanh_toan ? ' · ' + h(x.vgb_pt_thanh_toan) : '') +
        (x.custom_hddt_so ? ' · HĐĐT ' + h(x.custom_hddt_so) : '') + '</div></div>';
    }).join('');

  var hop = hopKhung('Kết quả tìm đơn', than,
    '<button class="btn gh" id="tdDong" style="margin:0;flex:1">Đóng</button>');
  hop.box.querySelector('.x').onclick = hop.dong;
  hop.box.querySelector('#tdDong').onclick = hop.dong;
  hop.box.querySelectorAll('[data-td]').forEach(function (el) {
    el.onclick = function () {
      var ten = el.getAttribute('data-td');
      hop.dong();
      /* Mo thang man chi tiet don, khong bat nguoi ta quay lai chon ngay. */
      go(function () { scrDsView(ten, 0); });
    };
  });
}

function veODate(id) {
  var o = document.getElementById(id);
  if (!o) return null;
  var mo = function (e) {
    if (typeof o.showPicker !== 'function') return;
    /* Bam trung bieu tuong lich thi de trinh duyet tu lo, goi them
       showPicker nua se bi bao loi da mo roi. */
    try { o.showPicker(); if (e) e.preventDefault(); } catch (er) { }
  };
  o.onmousedown = function (e) {
    if (e && e.button) return;
    mo(e);
  };
  o.onkeydown = function (e) {
    if (e && (e.key === 'Enter' || e.key === ' ')) mo(e);
  };
  return o;
}

function veOMtc(pt, idO, idNhan) {
  var q = quyPt(pt) || {};
  var o = document.getElementById(idO), nh = document.getElementById(idNhan);
  if (!o) return;
  var hien = !!(q.nhan || q.bat);
  o.parentElement.style.display = hien ? '' : 'none';
  var ten = q.nhan || 'Mã tham chiếu';
  o.placeholder = ten + (q.vd ? ' - vd ' + q.vd : '');
  o.style.borderColor = q.bat && !o.value.trim() ? '#f59e0b' : '#e5e7eb';
  /* TEN cua o phai nam NGOAI o. Truoc day ten chi nam trong placeholder,
     nhan vien go xong roi quay lai sua thi placeholder bi che mat, khong
     con biet o do la o gi (anh Viet 11/08/2026). */
  if (nh) {
    nh.innerHTML = '<b style="color:#374151;font-size:12.5px">' + h(ten) + '</b>' +
      (q.bat
        ? ' · <b style="color:#b45309">bắt buộc</b> để đối soát'
        : (pt === 'Chuyển khoản' ? ' · SePay tự khớp, để trống cũng được' : ' · không bắt buộc'));
  }
}
async function scrDsView(name, can) {
  frame('Chi tiết đơn', '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api('frappe.client.get', { doctype: 'Sales Invoice', name: name }); }
  catch (e) { frame('Chi tiết đơn', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không đọc được đơn') + '</div></div>'); return; }
  var kh = (d.remarks || '').split(' - ');
  var vn = String(d.posting_date || '').split('-');
  var html = '<div class="card" style="padding:12px 14px;line-height:1.7">' +
    '<div style="display:flex;justify-content:space-between"><b>#' + h(d.custom_pancake_display_id || '?') + ' · ' + h(d.custom_nguon || 'Pancake') + '</b>' +
    '<span>' + (d.docstatus === 1 ? '✅ Đã chốt' : '📝 Nháp') + '</span></div>' +
    '<div>' + h(kh[1] || 'Khách lẻ') + (kh[2] ? ' · ' + h(kh[2]) : '') + '</div>' +
    '<div style="color:#6b7280;font-size:13px">Mã phiếu: <b>' + h(d.name) + '</b> · Ngày ' + (vn.length === 3 ? vn[2] + '/' + vn[1] + '/' + vn[0] : h(d.posting_date)) + '</div>' +
    (d.custom_hddt_so ? '<div style="color:#0a8a4a;font-size:13px">HĐĐT số ' + h(d.custom_hddt_so) + (d.custom_hddt_trang_thai ? ' (' + h(d.custom_hddt_trang_thai) + ')' : '') + '</div>' : '') +
    '</div>';
  /* Don cua ngay cu ma con nhap: luat ke toan bat xuat hoa don dien tu ngay
     trong ngay ban, nen don hom qua co truc trac thi phai keo sang hom nay
     roi moi ghi so duoc (chi Dung 12/08/2026). Chi quan ly va ke toan thay
     nut nay, va phai co ma OTP. */
  var laCu = d.docstatus === 0 && !d.custom_hddt_so && String(d.posting_date || '') < today();
  if (laCu) {
    html += '<div class="card" style="padding:12px 14px;background:#fffbeb;border:1.5px solid #fcd34d">' +
      '<div style="font-size:13px;color:#92400e;line-height:1.6">Đơn này còn nháp và mang ngày <b>' +
      (vn.length === 3 ? vn[2] + '/' + vn[1] + '/' + vn[0] : h(d.posting_date)) + '</b>. ' +
      'Luật kế toán bắt xuất hoá đơn điện tử ngay trong ngày bán, nên đơn cũ ghi sổ xong vẫn không xuất được hoá đơn mang ngày cũ. ' +
      'Chuyển sang hôm nay rồi ghi sổ thì hoá đơn điện tử mang đúng ngày xuất.</div>' +
      '<button class="btn" id="dsvDoiNgay" style="margin-top:10px">📅 Chuyển đơn sang hôm nay (' + posNgayVn(today()) + ')</button></div>';
  }
  html += '<div class="sec">Món trong đơn</div><div class="card" style="padding:6px 14px">';
  /* Dòng nào có giảm giá thì phải NHÌN RA là có giảm giá.

     Anh Việt 24/08/2026: *"đồng bộ như vậy về phần giá của pancake thì nó
     thiếu bản chất, tức là mình không thấy được đơn này là đơn giảm giá cho
     khách"*. Trước đây màn này chỉ hiện một con giá đã trừ giảm, nhìn vào
     không biết hộp bánh 2.090.000 là hộp 2.200.000 giảm 5 phần trăm hay là
     một hộp khác vốn đã 2.090.000. */
  var tongGiamDong = 0;
  (d.items || []).forEach(function (r) {
    var goc = Number(r.price_list_rate || 0);
    var ban = Number(r.rate || 0);
    var giamDv = goc > ban ? goc - ban : 0;
    tongGiamDong += giamDv * Number(r.qty || 0);
    var pt = Number(r.discount_percentage || 0);
    html += '<div style="display:flex;justify-content:space-between;gap:10px;padding:8px 0;border-bottom:1px solid #f0f2f6">' +
      '<div style="flex:1;min-width:0">' + h(r.item_name) +
      '<div style="color:#a0a6b4;font-size:12px">' + money(r.qty) + ' x ' +
      (giamDv
        ? '<span style="text-decoration:line-through;color:#c3c8d4">' + money(goc) + '</span> <b style="color:#b3261e">' + money(ban) + '</b> đ'
        : money(ban) + ' đ') + '</div>' +
      (giamDv
        ? '<div style="margin-top:3px"><span style="display:inline-block;background:#fef2f2;border:1px solid #fecaca;color:#b3261e;border-radius:999px;padding:2px 9px;font-size:11.5px;font-weight:700">🏷️ Giảm ' +
          (pt ? num(pt) + '%' : money(giamDv) + ' đ') + ' mỗi ' + h(r.uom || 'món') +
          ' · tổng −' + money(giamDv * Number(r.qty || 0)) + ' đ</span></div>'
        : '') +
      '</div>' +
      '<b style="white-space:nowrap">' + money(r.amount) + '</b></div>';
  });
  if (tongGiamDong) html += '<div style="display:flex;justify-content:space-between;padding:8px 0;color:#b3261e"><span>Giảm giá trên dòng hàng</span><b>-' + money(tongGiamDong) + '</b></div>';
  if (d.discount_amount) html += '<div style="display:flex;justify-content:space-between;padding:8px 0;color:#b3261e"><span>Giảm giá cả đơn</span><b>-' + money(d.discount_amount) + '</b></div>';
  html += '<div style="display:flex;justify-content:space-between;padding:10px 0;font-size:16px"><b>Tổng tiền</b><b>' + money(d.grand_total) + ' đ</b></div></div>';
  await cfgBanHang();
  var PTDS = ptTheoNguon(d.custom_nguon || 'Pancake');
  html += '<div style="padding:8px 0 2px"><div style="font-size:12px;color:#6b7280;margin-bottom:6px">Phương thức thanh toán' + (d.vgb_pt_thanh_toan ? '' : ' - <b style="color:#b45309">chưa rõ, chọn giúp trước khi ghi sổ</b>') + '</div><div id="dsvPt" style="display:flex;gap:6px;flex-wrap:wrap">' + PTDS.map(function (p) { var on = p.v === d.vgb_pt_thanh_toan; return '<button class="ptc" data-pt="' + p.v + '" style="display:inline-flex;align-items:center;gap:6px;padding:6px 10px;border-radius:8px;font-size:13px;border:1.5px solid ' + (on ? '#0d9488;background:#ccfbf1;color:#0f766e;font-weight:bold' : '#e5e7eb;background:#fff;color:#374151') + '">' + (p.lg ? '<img src="' + p.lg + '" style="height:18px;border-radius:3px">' : '🏦 ') + p.v + '</button>'; }).join('') + '</div></div>';
  /* Khach chuyen khoan cho don ben Sales cung phai co ma QR nhu ben quay.
     Truoc day man nay chi co o go ma tham chieu, nen diem Sales chon nguon
     Tai cho hoac Mang ve roi chon Chuyen khoan la khong sinh duoc QR - thu
     ngan phai mo app ngan hang go tay (anh Viet 12/08/2026). */
  html += '<div id="dsvQr" style="margin-top:10px"></div>';
    html += '<div style="border:1.5px solid #e5e7eb;border-radius:10px;padding:10px;margin-top:10px">'
    + '<div id="dsvMtcNhan" style="font-size:12px;color:#6b7280;margin-bottom:6px"></div>'
    + '<input id="dsvMtc" placeholder="Mã tham chiếu" value="' + xesc(d.vgb_ma_tham_chieu) + '" style="width:100%;box-sizing:border-box;padding:9px 10px;border:1.5px solid #e5e7eb;border-radius:8px;font-size:14px;font-family:inherit">'
    + '<div style="font-size:12px;color:#6b7280;margin-top:8px">Đối soát thanh toán: '
    + (d.vgb_ghi_chu_doi_soat ? xesc(d.vgb_ghi_chu_doi_soat) : '<span style="color:#9ca3af">chưa có, chờ máy đối soát</span>')
    + '</div></div>';
  html += '<div id="dsvSepay" style="border:1.5px solid #e5e7eb;border-radius:10px;padding:10px;margin-top:10px;font-size:13px;color:#6b7280">Đang tìm giao dịch SePay của đơn này...</div>';
  /* Khach cong no: ban chiu thi phai biet no cua AI. O nay hien mo ma
     bat buoc khi chon phuong thuc Cong no (anh Viet 12/08/2026 - don
     91513 cua OSHIMA ghi cong no ma khong gan duoc khach nen man Cong no
     phai thu khong thay ten). */
  html += '<div id="dsvKhachBox" style="border:1.5px solid #e5e7eb;border-radius:10px;padding:10px;margin-top:10px"></div>';
  /* Bản tính của hệ thống lệch tổng đơn bên Pancake.

     Ngày 22/08/2026 Pancake gửi `discount_each_product = 5` kèm cờ
     `is_discount_percent`, ý là giảm 5 phần trăm; máy đọc thiếu cờ nên trừ
     5 đồng. Đơn 91853 thành 8.229.970 trong khi khách chuyển 7.820.000. Cả
     luồng chạy êm, không có màn nào báo. Dải băng này là chỗ báo. */
  if (Math.abs(Number(d.vgb_lech_pancake || 0)) >= 1) {
    var lechPk = Number(d.vgb_lech_pancake || 0);
    html += '<div style="border:1.5px solid #fca5a5;background:#fef2f2;border-radius:10px;'
      + 'padding:10px 12px;margin-top:10px;font-size:13px;color:#991b1b;line-height:1.55">'
      + '<b>⚠️ Tổng đơn lệch so với Pancake ' + Math.abs(lechPk).toLocaleString('vi-VN') + ' đ</b><br>'
      + 'Phiếu này đang tính ' + (lechPk > 0 ? 'CAO hơn' : 'THẤP hơn') + ' bên Pancake. '
      + 'Vui lòng báo bộ phận kỹ thuật trước khi ghi sổ và trước khi xuất hoá đơn điện tử.'
      + '</div>';
  }
  var XHD_MD = 'Bán cho người tiêu dùng';
  function xesc(t) { return String(t == null ? '' : t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
  var xhdCty = (d.vgb_xhd_ten && d.vgb_xhd_ten !== XHD_MD) ? d.vgb_xhd_ten : '';
  var xhdLoai = (d.vgb_xhd_mst || xhdCty) ? 'cong_ty' : 'ca_nhan';
  var xin = 'width:100%;box-sizing:border-box;padding:9px 10px;border:1.5px solid #e5e7eb;border-radius:8px;font-size:14px;font-family:inherit';
  html += '<div style="border:1.5px solid #e5e7eb;border-radius:10px;padding:10px;margin-top:10px">'
    + '<div style="font-size:12px;color:#6b7280;margin-bottom:8px"><b>Tên khách xuất hoá đơn</b></div>'
    + '<div id="xhdChon" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px">'
    + '<button class="xhdc" data-loai="ca_nhan" style="padding:6px 10px;border-radius:8px;font-size:13px">Bán cho người tiêu dùng</button>'
    + '<button class="xhdc" data-loai="cong_ty" style="padding:6px 10px;border-radius:8px;font-size:13px">Xuất cho công ty / HKD</button>'
    + '</div>'
    + '<div id="xhdForm" style="display:none;flex-direction:column;gap:6px">'
    + '<input id="xhdMst" placeholder="Mã số thuế: 10 số công ty, 12 số hộ kinh doanh, chi nhánh gõ cả dấu gạch vd 0311638525-027" value="' + xesc(d.vgb_xhd_mst) + '" style="' + xin + '">'
    + '<input id="xhdTen" placeholder="Tên pháp nhân trên hoá đơn" value="' + xesc(xhdCty) + '" style="' + xin + '">'
    + '<textarea id="xhdDc" rows="2" placeholder="Địa chỉ trên hoá đơn" style="' + xin + '">' + xesc(d.vgb_xhd_dia_chi) + '</textarea>'
    + '<input id="xhdEmail" placeholder="Email nhận hoá đơn" value="' + xesc(d.vgb_xhd_email) + '" style="' + xin + '">'
    + '<div id="xhdBao" style="font-size:12px;color:#6b7280"></div>'
    + '</div>'
    + (d.custom_hddt_so ? '<div style="font-size:12px;color:#0f766e">Đã xuất HĐĐT số ' + xesc(d.custom_hddt_so) + ' nên không sửa được nữa.</div>' : '<button class="btn" id="xhdLuu" style="margin-top:8px">Lưu thông tin đơn</button>')
    + '<div style="font-size:11px;color:#9ca3af;margin-top:8px">Luật kế toán hiện hành: mỗi đơn hàng là một hoá đơn VAT riêng, không được gộp đơn.</div>'
    + '</div>'
    /* Khoi Hoa don thay the. Chi ve khi don DA co so hoa don dien tu; noi
       dung nap sau bang dsvVeThayThe de man hinh hien ra ngay chu khong
       dung cho mang. */
    + (d.custom_hddt_so ? '<div id="dsvTT" style="margin-top:10px"></div>' : '');
  var foot = '';
  /* Nut Huy cho don CHUA GHI SO ben Sales. Truoc 15/08/2026 chi bill quay
     moi huy duoc tren app, don Sales bam nham la ket - phai nho ke toan
     vao ERP. Nay Sales nhap duoc ca don "Tại chỗ" va "Mang về" nen cang
     phai co duong huy (anh Viet). Van la HUY MEM: don nam nguyen trong
     danh sach, chi bi loc khoi doanh thu. */
  if (d.docstatus === 0 && !d.vgb_huy) {
    /* Ba nut cho don CHUA GHI SO (anh Viet 21/08/2026).

       "Huy don" cu chi dat dau huy. Dung khi khach chua tra dong nao: bam
       nham, trung don, khach hoi gia roi thoi.

       Nhung khach chot banh roi chuyen tien, hai ba tieng sau bao huy thi
       chi dat dau huy la con lai mot khoan tien vao khong chung tu. Nut
       "Huy don va hoan tien" lo ca hai: dat dau huy TRUOC roi lap phieu gui
       ke toan. Phai dat dau truoc vi chuoi cuoi ngay luc 23:00 tu ghi so
       nhung don nhap da nhan du tien roi xuat hoa don dien tu luon.

       Khong gop hai nut lam mot vi hai ca that su khac nhau, va ca "chua
       tra dong nao" la ca pho bien hon. */
    foot = '<div style="display:flex;gap:8px;flex-wrap:wrap">' +
      '<button class="btn gh" id="dsvHuy" style="margin:0;flex:1 1 44%;color:#b3261e;border-color:#fecaca">🚫 Huỷ đơn</button>' +
      '<button class="btn gh" id="dsvHuyHoan" style="margin:0;flex:1 1 44%;color:#b45309;border-color:#fde68a">↩️ Huỷ đơn và hoàn tiền</button>' +
      '<button class="btn" id="dsvChot" style="margin:0;flex:1 1 100%">Ghi sổ hoá đơn bán hàng</button></div>';
  } else if (d.docstatus === 0) {
    /* Da bam Huy don roi moi nho ra khach da chuyen tien. Van phai co duong
       tra tien, khong thi phai nho ke toan lap tay tren Desk. */
    foot = '<div style="text-align:center;color:#b3261e;font-weight:600;padding:6px 6px 10px">Đơn này đã huỷ' +
      (d.vgb_huy_ly_do ? ': ' + h(d.vgb_huy_ly_do) : '') + '</div>' +
      '<button class="btn gh" id="dsvHuyHoan" style="margin:0;color:#b45309;border-color:#fde68a">↩️ Khách đã chuyển tiền, hoàn lại cho khách</button>';
  } else if (d.docstatus === 1 && !d.vgb_huy) {
    /* Don DA GHI SO thi khong con huy duoc nua, va do la dung: to da vao so
       thi phai khu bang mot to nguoc chieu chu khong xoa di. Nen cho don da
       ghi so, cua ra la HOAN TIEN (anh Viet 16/08/2026 dat nut nay ngay canh
       cho nut Huy don van dung o man chua ghi so).

       Nut nay chi GUI YEU CAU, khong sinh chung tu va khong dong tien nao -
       xem ghi chu dau hoan_tien.tao. */
    /* Hai nut canh nhau, hai luong khac han (anh Viet 18/08/2026): *"anh
       nho em thiet ke luon 1 nut rieng ke ben nut Hoan tien do la nut
       Chuyen lai cho khach thanh toan du"*.

       Hoan tien la TRA HANG: khach tra banh ve, doanh thu khu di.
       Chuyen lai tien du la khach NOP THUA: hang giao du, gia dung, doanh
       thu giu nguyen, chi tra lai phan chuyen vuot. */
    foot = '<div style="display:flex;gap:8px;flex-wrap:wrap">' +
      '<button class="btn gh" id="dsvHoan" style="margin:0;flex:1 1 44%;color:#b45309;border-color:#fde68a">↩️ Hoàn tiền</button>' +
      '<button class="btn gh" id="dsvDu" style="margin:0;flex:1 1 44%;color:#0f766e;border-color:#99f6e4">💸 Chuyển lại tiền dư</button>' +
      (can && !d.custom_hddt_so
        ? '<button class="btn" id="dsvHddt" style="margin:0;flex:1 1 100%">Xuất HĐĐT (Chờ ký)</button>'
        : '<button class="btn gh" id="dsvXemHoan" style="margin:0;flex:1 1 100%">Xem danh sách hoàn tiền</button>') +
      '</div>';
  } else if (can && !d.custom_hddt_so) {
    foot = '<button class="btn" id="dsvHddt">Xuất HĐĐT (Chờ ký)</button>';
  }
  frame('Chi tiết đơn', html, foot ? { footer: foot } : {});
  var nHoan = document.getElementById('dsvHoan');
  if (nHoan) nHoan.onclick = function () { hoanMoForm(d); };
  var nHuyHoan = document.getElementById('dsvHuyHoan');
  if (nHuyHoan) nHuyHoan.onclick = function () { hoanMoFormHuy(d); };
  var nDu = document.getElementById('dsvDu');
  if (nDu) nDu.onclick = function () { hoanMoFormDu(d); };
  var nXemHoan = document.getElementById('dsvXemHoan');
  if (nXemHoan) nXemHoan.onclick = function () { go(scrHoanTien); };
  var nHuy = document.getElementById('dsvHuy');
  if (nHuy) nHuy.onclick = async function () {
    var ok = await confirmSheet('Huỷ đơn ' + (d.custom_pancake_display_id || d.name) + '?',
      'Đơn ' + money(d.grand_total) + ' đ sẽ được đánh dấu đã huỷ và không tính vào doanh thu nữa. ' +
      'Đơn vẫn nằm nguyên trong hệ thống để đối chiếu - không ai xoá được chứng từ.', 'Huỷ đơn', true);
    if (!ok) return;
    var ly_do = await promptSheet('Vì sao huỷ đơn này?', 'Khách đổi ý, nhập nhầm nguồn, trùng đơn...');
    if (ly_do === null) return;
    if (!ly_do) return toast('Phải ghi lý do thì sau này còn biết vì sao.', 4000);
    /* Huy chung tu luon phai qua ma OTP quan ly, giong het ben quay. Quan
       ly tu bam thi may chu tu cho qua, khong hoi ma. */
    var otp = await posXinPhep('Huỷ đơn ' + (d.custom_pancake_display_id || d.name));
    if (otp === null) return;
    busy(true);
    try {
      await api('vagabond.ban_hang.pos_xoa', { name: d.name, otp: otp, ly_do: ly_do });
      busy(false); toast('Đã huỷ đơn. Đơn vẫn còn trong danh sách.', 4000);
      go(function () { scrDsView(name, can); }, true);
    } catch (e) { busy(false); toast((e && e.message) || 'Huỷ lỗi', 5000); }
  };
  var DSV_PT = d.vgb_pt_thanh_toan || '';
  var ptWrap = document.getElementById('dsvPt');
  if (ptWrap) ptWrap.querySelectorAll('.ptc').forEach(function (b) {
    b.onclick = function () {
      DSV_PT = b.getAttribute('data-pt');
      ptWrap.querySelectorAll('.ptc').forEach(function (x) {
        var on = x.getAttribute('data-pt') === DSV_PT;
        x.style.border = '1.5px solid ' + (on ? '#0d9488' : '#e5e7eb');
        x.style.background = on ? '#ccfbf1' : '#fff';
        x.style.color = on ? '#0f766e' : '#374151';
        x.style.fontWeight = on ? 'bold' : 'normal';
      });
    };
  });
    if (ptWrap) ptWrap.addEventListener('click', function () { setTimeout(function () { veOMtc(DSV_PT, 'dsvMtc', 'dsvMtcNhan'); veKhachNo(); dsvVeQr(); }, 0); });
  veOMtc(DSV_PT, 'dsvMtc', 'dsvMtcNhan');

  /* Ma diem ban cua nguon don nay, de noi dung chuyen khoan mang ma diem -
     ke toan doc sao ke la biet ngay tien cua noi nao. */
  /* vgb_quay TRUOC: nguon "Tại chỗ" nay dung chung cho moi quay nen ban
     than ten nguon khong con noi duoc don cua diem nao, chi hoa don moi
     biet. Nguon rieng cua mot diem thi van suy nguoc duoc. */
  var dsvDiem = d.vgb_quay || (nguonBH(d.custom_nguon) || {}).diem || '';
  var dsvNoiDung = posNoiDungCk(d.name, dsvDiem, d.custom_nguon || '');
  function dsvVeQr() {
    var o = document.getElementById('dsvQr');
    if (!o) return;
    if (DSV_PT !== 'Chuyển khoản') { o.innerHTML = ''; return; }
    var tien = d.grand_total || 0;
    var url = posQrUrl(dsvNoiDung, tien, d.custom_nguon || '', dsvDiem);
    if (!url) {
      o.innerHTML = '<div style="border:1.5px solid #fecaca;background:#fef2f2;border-radius:10px;padding:12px;font-size:13px;color:#b3261e;line-height:1.6">' +
        'Chưa khai số tài khoản nhận chuyển khoản nên chưa sinh được mã QR. Vào Cài đặt · Tài khoản nhận tiền để khai.</div>';
      return;
    }
    var tk = posTaiKhoan(d.custom_nguon || '', dsvDiem);
    o.innerHTML = '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:12px;text-align:center;background:#fff">' +
      '<div style="font-size:12.5px;color:#6b7280">Khách quét mã này, máy tự điền số tiền và nội dung</div>' +
      '<img src="' + url + '" alt="Mã QR chuyển khoản" style="width:min(240px,62vw);aspect-ratio:1;margin:10px auto 6px;display:block;border-radius:10px;background:#fff">' +
      '<div style="font-size:18px;font-weight:800;color:#0f766e">' + money(tien) + ' đ</div>' +
      '<div style="font-size:13px;color:#374151;margin-top:2px">Nội dung: <b>' + h(dsvNoiDung) + '</b></div>' +
      '<div style="font-size:12px;color:#98a2b3;margin-top:2px">' + h(tk.ten || '') + ' · ' + h((tk.bank || '') + ' ' + (tk.stk || '')) +
      (tk.rieng ? ' · tài khoản riêng của nguồn này' : '') + '</div></div>';
  }
  dsvVeQr();

  /* --- khach cong no --- */
  var KHACH_LE_TEN = 'Khách lẻ';
  var dsvKhach = { ma: d.vgb_khach_no || '', ten: '' };
  if (!dsvKhach.ma && d.customer && String(d.customer).indexOf(KHACH_LE_TEN) !== 0) {
    dsvKhach = { ma: d.customer, ten: d.customer_name || d.customer };
  } else if (dsvKhach.ma) {
    dsvKhach.ten = d.vgb_khach_no;
  }
  /* Thẻ thành viên của khách đang gắn. Máy chủ trả về, app chỉ in ra:
     số điểm là tiền của khách nên không được để hai nơi tự tính (QT-19). */
  var dsvThe = null;

  async function dsvTaiThe() {
    dsvThe = null;
    if (!dsvKhach.ma) return;
    try {
      dsvThe = await api('vagabond.khach_hang.the_tren_don', {
        khach: dsvKhach.ma,
        tien: Number(d.grand_total) || 0,
        hoa_don: d.name || ''
      });
      if (dsvThe && !dsvThe.co) dsvThe = null;
    } catch (e) { dsvThe = null; }
    /* Trạng thái trừ điểm hỏi RIÊNG máy chủ chứ không suy ra từ dsvThe:
       máy chủ mới biết trần, khoá do nhập sai, và khách có số điện thoại
       trong hồ sơ hay chưa. Suy ở app là có ngày bày nút cho một đơn mà
       bấm vào thì báo lỗi. */
    dsvTru = null;
    if (!dsvKhach.ma) return;
    try {
      dsvTru = await api('vagabond.diem_otp.tinh_trang', { si_name: d.name });
    } catch (e) { dsvTru = null; }
  }

  /* Một ô số chỉ đọc. Dựng bằng khối chứ không dùng thẻ nhập, vì đây là
     số máy tính ra, gõ vào không có tác dụng gì mà chỉ làm người dùng
     tưởng sửa được. */
  function dsvOSo(nhan, so, mau, chu) {
    return '<div style="flex:1;min-width:0;border:1.5px solid #e5e7eb;border-radius:11px;padding:7px 10px;background:#fff">' +
      '<div style="font-size:10.5px;color:#8a8f9c;letter-spacing:.02em">' + h(nhan) + '</div>' +
      '<b style="font-size:16px;color:' + (mau || '#111') + '">' + money(so || 0) + '</b>' +
      (chu ? '<div style="font-size:10.5px;color:#9ca3af;margin-top:1px">' + h(chu) + '</div>' : '') +
      '</div>';
  }

  function veKhachNo() {
    var box = document.getElementById('dsvKhachBox');
    if (!box) return;
    var canNo = DSV_PT === 'Công nợ';
    box.style.borderColor = canNo && !dsvKhach.ma ? '#fcd34d' : '#e5e7eb';
    box.style.background = canNo && !dsvKhach.ma ? '#fffbeb' : '#fff';

    /* MỘT Ô, HAI VAI.
       Trường vgb_khach_no vừa là khách thân thiết của đơn bán lẻ, vừa là
       chủ nợ của đơn bán chịu. Nên nhãn đổi theo việc đang làm chứ không
       đóng cứng một chữ: gọi nó là "Khách hàng thân thiết" cho đúng bán
       lẻ, nhưng đơn bán chịu thì vẫn phải nói rõ là bắt buộc, không thì
       kế toán mất chủ nợ trên màn Công nợ phải thu. */
    box.innerHTML = '<div style="font-size:12px;color:#6b7280;margin-bottom:8px"><b>Khách hàng thân thiết</b>' +
      (canNo ? ' <span style="color:#b45309">- đơn bán chịu nên bắt buộc, khách này là chủ nợ</span>'
             : ' <span style="color:#9ca3af">- không bắt buộc</span>') + '</div>' +
      (dsvKhach.ma
        ? '<div style="display:flex;align-items:center;gap:9px">' +
          dsvTheAnh() +
          '<div style="flex:1;min-width:0"><b style="font-size:14px">' + h(dsvKhach.ten || dsvKhach.ma) + '</b>' +
          '<div style="font-size:11.5px;color:#6b7280">mã ' + h(dsvKhach.ma) +
          (dsvThe && dsvThe.ten_hang ? ' · hạng ' + h(dsvThe.ten_hang) : '') +
          (dsvThe && dsvThe.giam_gia ? ' · <b style="color:#b45309">ưu đãi giảm ' + dsvThe.giam_gia + '%</b>' : '') + '</div></div>' +
          '<button id="dsvKhachBo" style="border:0;background:transparent;color:#b3261e;font-size:17px;cursor:pointer">✕</button></div>' +
          dsvVeDiem() + dsvVeHt()
        : '<button class="btn gh" id="dsvKhachChon" style="margin:0">🎫 Chọn khách hàng thân thiết</button>') +
      (d.docstatus === 1
        ? '<div style="font-size:11px;color:#9ca3af;margin-top:8px">Đơn đã ghi sổ nên chỉ gắn được tên khách cho màn Công nợ phải thu, bút toán trên sổ cái giữ nguyên.</div>'
        : '');
    var nChon = document.getElementById('dsvKhachChon');
    if (nChon) nChon.onclick = function () {
      sheetTimKhach('Chọn khách hàng thân thiết', async function (x) {
        dsvKhach = { ma: x.name, ten: x.customer_name || x.name };
        veKhachNo();
        await dsvTaiThe();
        veKhachNo();
        if (d.docstatus === 1) {
          try { await api('vagabond.ban_hang.luu_khach_no', { si_name: d.name, khach: x.name }); toast('Đã gắn ' + dsvKhach.ten); }
          catch (e) { toast((e && e.message) || 'Không gắn được'); }
        }
      });
    };
    var nBo = document.getElementById('dsvKhachBo');
    if (nBo) nBo.onclick = function () { dsvKhach = { ma: '', ten: '' }; dsvThe = null; dsvTru = null; veKhachNo(); };
    dsvGanTruDiem();
    dsvGanHt();
  }

  /* Hình thẻ hạng thay cho emoji toà nhà.
     Khách chưa xếp hạng thì để một huy hiệu chữ chứ không để khung ảnh
     vỡ - khung vỡ trên màn của Loan Anh nhìn như lỗi hệ thống. */
  function dsvTheAnh() {
    if (dsvThe && dsvThe.anh_hang) {
      return '<img src="' + h(dsvThe.anh_hang) + '" alt="' + h(dsvThe.ten_hang || '') + '" ' +
        'style="width:38px;height:38px;object-fit:cover;border-radius:8px;flex:none;border:1px solid #e5e7eb">';
    }
    if (dsvThe && dsvThe.ten_hang) {
      return '<span style="flex:none;width:38px;height:38px;border-radius:8px;background:#f3edff;color:#7c3aed;' +
        'display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;text-align:center;line-height:1.1">' +
        h(String(dsvThe.ten_hang).slice(0, 4)) + '</span>';
    }
    return '<span style="flex:none;width:38px;height:38px;border-radius:8px;background:#f1f2f5;color:#9ca3af;' +
      'display:flex;align-items:center;justify-content:center;font-size:17px">🎫</span>';
  }

  function dsvVeDiem() {
    if (!dsvThe) return '';
    var nhan2 = dsvThe.da_tich ? 'Điểm đã tích cho đơn này' : 'Số điểm tích cho đơn này';
    /* Hai hạng cao nhất CỐ Ý không tích điểm mà đổi sang giảm giá thẳng
       trên bill: AMBASSADOR giảm 10%, FAMILY giảm 20%. Viết "chưa khai tỷ
       lệ" ở đây là nói sai nghiệp vụ, và Loan Anh đọc xong sẽ đi hỏi kỹ
       thuật một chuyện vốn không phải lỗi. */
    var chu2 = dsvThe.tich_diem_pt
      ? 'hạng ' + (dsvThe.ten_hang || '') + ' tích ' + dsvThe.tich_diem_pt + '%'
      : (dsvThe.giam_gia
          ? 'hạng này ưu đãi giảm ' + dsvThe.giam_gia + '% thay vì tích điểm'
          : 'hạng này chưa khai tỷ lệ tích điểm');
    return '<div style="display:flex;gap:8px;margin-top:9px">' +
      dsvOSo('Số điểm hiện tại', dsvThe.diem_hien_tai, '#111',
             dsvThe.da_tich ? 'trước khi chốt đơn này' : '') +
      dsvOSo(nhan2, dsvThe.diem_don_nay, dsvThe.diem_don_nay > 0 ? '#0a8a4a' : '#9ca3af', chu2) +
      '</div>' + dsvVeTruDiem();
  }

  /* ---------------------------------------------------------------- trừ điểm
     Hai pha. Pha 1 xin mã: máy chủ gửi ZNS tới số TRONG HỒ SƠ khách và ghi
     số điểm đã duyệt vào chính bản ghi OTP. Pha 2 chỉ gửi lên mã sáu số,
     KHÔNG gửi lại số điểm - gửi lại thì xin mã cho 100 điểm rồi xác nhận
     100.000 điểm là ăn, mà tin ZNS khách nhận vẫn ghi 100 điểm.

     Nên biến dsvPhien dưới đây cố ý CHỈ giữ thứ để hiển thị, và hàm xác
     nhận cố ý không đọc số điểm từ nó. */
  var dsvTru = null;
  var dsvPhien = null;
  var dsvDongHo = null;

  function dsvVeTruDiem() {
    if (!dsvTru) return '';
    if (dsvTru.da_tru > 0) {
      return '<div style="margin-top:9px;padding:9px 11px;border-radius:9px;background:#ecfdf5;' +
        'border:1.5px solid #a7f3d0;font-size:12.5px;color:#065f46">' +
        '<b>Đã dùng ' + money(dsvTru.da_tru) + ' điểm</b> cho đơn này, giảm ' +
        money(dsvTru.giam_diem) + ' đ. ' +
        '<button id="dsvGoDiem" style="border:1.5px solid #6ee7b7;background:#fff;color:#047857;' +
        'border-radius:7px;padding:3px 9px;font-size:12px;font-weight:700">Gỡ lượt trừ</button></div>';
    }
    if (!dsvTru.dung_duoc) {
      if (!dsvTru.vi_sao) return '';
      return '<div style="margin-top:8px;font-size:11.5px;color:#9ca3af">' + h(dsvTru.vi_sao) + '</div>';
    }
    /* Chưa xin mã thì bày ô nhập điểm; đã xin rồi thì bày ô nhập mã. Không
       bày cả hai cùng lúc: thu ngân đang đứng trước khách, mỗi lúc chỉ nên
       có đúng một việc để làm. */
    if (!dsvPhien) {
      return '<div style="margin-top:9px;padding:10px 11px;border-radius:9px;background:#f8fafc;' +
        'border:1.5px solid #e2e8f0">' +
        '<div style="font-size:12px;color:#475569;margin-bottom:7px">Khách trả bằng điểm? ' +
        'Đơn này dùng được tối đa <b>' + money(dsvTru.toi_da) + '</b> điểm.</div>' +
        '<div style="display:flex;gap:7px">' +
        '<input id="dsvDiemNhap" type="number" inputmode="numeric" min="1" max="' + dsvTru.toi_da + '" ' +
        'placeholder="Số điểm muốn dùng" style="flex:1;min-width:0;border:1.5px solid #cbd5e1;' +
        'border-radius:8px;padding:8px 10px;font-size:14px">' +
        '<button id="dsvXinMa" style="flex:none;border:0;background:#0f766e;color:#fff;border-radius:8px;' +
        'padding:8px 13px;font-size:13px;font-weight:700">Xác nhận trừ điểm</button></div>' +
        '<div id="dsvDiemQuy" style="font-size:11.5px;color:#64748b;margin-top:6px"></div></div>';
    }
    return '<div style="margin-top:9px;padding:10px 11px;border-radius:9px;background:#fffbeb;' +
      'border:1.5px solid #fde68a">' +
      '<div style="font-size:12px;color:#78350f;margin-bottom:7px">' +
      'Đã gửi mã tới số đuôi <b>' + h(dsvPhien.duoi_so) + '</b> của khách. Dùng <b>' +
      money(dsvPhien.so_diem) + '</b> điểm, giảm <b>' + money(dsvPhien.so_tien) + ' đ</b>.' +
      (dsvPhien.gia_lap ? ' <span style="color:#b45309">(chạy thử, chưa gửi Zalo thật)</span>' : '') +
      '</div>' +
      '<div style="display:flex;gap:7px;align-items:center">' +
      '<input id="dsvMaNhap" type="tel" inputmode="numeric" maxlength="6" placeholder="Mã 6 số" ' +
      'style="flex:1;min-width:0;border:1.5px solid #fcd34d;border-radius:8px;padding:8px 10px;' +
      'font-size:18px;letter-spacing:4px;text-align:center;font-weight:700">' +
      '<button id="dsvXacNhan" style="flex:none;border:0;background:#b45309;color:#fff;border-radius:8px;' +
      'padding:8px 13px;font-size:13px;font-weight:700">Xong</button></div>' +
      '<div style="display:flex;justify-content:space-between;align-items:center;margin-top:7px">' +
      '<span id="dsvDem" style="font-size:12px;color:#92400e;font-weight:700"></span>' +
      '<button id="dsvHuyMa" style="border:0;background:none;color:#92400e;font-size:11.5px;' +
      'text-decoration:underline">Huỷ</button></div></div>';
  }

  function dsvGanTruDiem() {
    var oNhap = document.getElementById('dsvDiemNhap');
    if (oNhap) {
      /* Quy ra tiền ngay khi gõ: thu ngân đọc cho khách nghe số tiền chứ
         không đọc số điểm, và tiền mới là cái khách quan tâm. */
      oNhap.oninput = function () {
        var o = document.getElementById('dsvDiemQuy');
        if (!o) return;
        var n = Number(oNhap.value) || 0;
        if (n <= 0) { o.textContent = ''; return; }
        if (n > dsvTru.toi_da) {
          o.innerHTML = '<span style="color:#b3261e">Vượt mức tối đa ' + money(dsvTru.toi_da) + ' điểm.</span>';
          return;
        }
        o.textContent = 'Giảm ' + money(Math.floor(n * (dsvTru.quy_doi || 1))) + ' đ cho đơn này.';
      };
      var nXin = document.getElementById('dsvXinMa');
      if (nXin) nXin.onclick = async function () {
        var n = Number(oNhap.value) || 0;
        if (n <= 0) { toast('Nhập số điểm muốn dùng đã.'); oNhap.focus(); return; }
        busy(true);
        try {
          var kq = await api('vagabond.diem_otp.xin_ma', { si_name: d.name, so_diem: n });
          busy(false);
          if (!kq || !kq.ok) { toast('Chưa gửi được mã cho khách. ' + ((kq && kq.chi_tiet) || ''), 4000); return; }
          dsvPhien = { duoi_so: kq.duoi_so, so_diem: kq.so_diem, so_tien: kq.so_tien,
                       gia_lap: kq.gia_lap, het_luc: Date.now() + kq.song_giay * 1000 };
          veKhachNo();
        } catch (e) { busy(false); }
      };
    }
    var oMa = document.getElementById('dsvMaNhap');
    if (oMa) {
      oMa.oninput = function () { oMa.value = oMa.value.replace(/\D/g, ''); };
      var nXn = document.getElementById('dsvXacNhan');
      if (nXn) nXn.onclick = async function () {
        var ma = (oMa.value || '').replace(/\D/g, '');
        if (ma.length !== 6) { toast('Mã gồm 6 chữ số.'); oMa.focus(); return; }
        busy(true);
        try {
          /* CHỈ gửi mã. Số điểm nằm ở bản ghi OTP trên máy chủ. */
          var kq = await api('vagabond.diem_otp.xac_nhan', { si_name: d.name, ma: ma });
          busy(false);
          dsvPhien = null;
          toast('Đã trừ ' + money(kq.so_diem) + ' điểm, giảm ' + money(kq.so_tien) + ' đ', 3000);
          /* Nạp lại CẢ tờ chứ không tự sửa số trên màn: tổng tiền do máy chủ
             tính lại, tin con số máy khách tự suy ra là có ngày lệch (QT-19). */
          await dsvNapLai();
        } catch (e) { busy(false); oMa.value = ''; oMa.focus(); }
      };
      var nHuy = document.getElementById('dsvHuyMa');
      if (nHuy) nHuy.onclick = function () { dsvPhien = null; veKhachNo(); };
      dsvChayDongHo();
    }
    var nGo = document.getElementById('dsvGoDiem');
    if (nGo) nGo.onclick = async function () {
      if (!confirm('Gỡ lượt trừ điểm của đơn này? Điểm sẽ được trả lại cho khách.')) return;
      busy(true);
      try {
        await api('vagabond.diem_otp.go_luot_tru', { si_name: d.name });
        busy(false); toast('Đã trả lại điểm cho khách'); await dsvNapLai();
      } catch (e) { busy(false); }
    };
  }

  function dsvChayDongHo() {
    if (dsvDongHo) clearInterval(dsvDongHo);
    dsvDongHo = setInterval(function () {
      var o = document.getElementById('dsvDem');
      /* Ô biến mất nghĩa là màn đã vẽ lại hoặc người dùng đã rời đi: dừng
         hẳn đồng hồ. Không dừng thì mỗi lần mở đơn lại thêm một bộ đếm chạy
         ngầm, và sau vài chục đơn là máy quầy ì. */
      if (!o || !dsvPhien) { clearInterval(dsvDongHo); dsvDongHo = null; return; }
      var con = Math.max(0, Math.round((dsvPhien.het_luc - Date.now()) / 1000));
      if (con <= 0) {
        clearInterval(dsvDongHo); dsvDongHo = null; dsvPhien = null;
        toast('Mã đã hết hạn, bấm lại để gửi mã mới', 3500);
        veKhachNo();
        return;
      }
      o.textContent = 'Mã còn ' + Math.floor(con / 60) + ':' + ('0' + (con % 60)).slice(-2);
    }, 250);
  }

  /* ---------------------------------------------------------- hoàn tiền
     Nút chỉ hiện với đơn ĐÃ GHI SỔ. Đơn còn nháp thì sửa hoặc huỷ thẳng
     là được, không cần đi đường trả hàng - và nói rõ điều đó thay vì bày
     một nút bấm vào thì báo lỗi. */
  var dsvHt = null;

  async function dsvTaiHt() {
    dsvHt = null;
    try { dsvHt = await api('vagabond.hoan_tien.tinh_trang', { si_name: d.name }); } catch (e) { dsvHt = null; }
  }

  // Chu tren khoi nay do anh Viet chot 19/08/2026.
  //
  // Cu ghi "Đã hoàn tiền" ngay khi mot phieu vua duoc TAO, trong khi tien
  // thi chi Dung moi chi. Sales doc dong do tuong khach da nhan tien roi.
  // Nen doi thanh "Đã tạo phiếu hoàn tiền". Va phieu bi anh Viet tu choi
  // thi goi thang la "Phiếu hoàn tiền đã bị từ chối", chu khong goi la
  // "đã huỷ" - hai chuyen khac nhau ve trach nhiem.
  var DSV_TT_HT = {
    'Cho chi': 'chờ chi',
    'Da chi': 'đã chi tiền',
    'Da doi soat': 'đã đối soát',
  };

  function dsvKhoiHt(t, mau) {
    var nen = mau === 'xam' ? '#f8fafc' : '#fef2f2';
    var vien = mau === 'xam' ? '#e2e8f0' : '#fecaca';
    var chu = mau === 'xam' ? '#475569' : '#991b1b';
    var dau = mau === 'xam'
      ? '<b>Phiếu hoàn tiền đã bị từ chối</b> ' + money(t.so_tien) + ' đ · phiếu ' + h(t.name)
      : '<b>Đã tạo phiếu hoàn tiền</b> ' + money(t.so_tien) + ' đ · phiếu ' + h(t.name) +
        ' · ' + h(DSV_TT_HT[t.trang_thai] || t.trang_thai);
    return '<div style="margin-top:10px;padding:10px 12px;border-radius:10px;background:' + nen + ';' +
      'border:1.5px solid ' + vien + ';font-size:12.5px;color:' + chu + '">' + dau + '</div>';
  }

  function dsvVeHt() {
    if (!dsvHt) return '';
    if (dsvHt.da_hoan) return dsvKhoiHt(dsvHt.da_hoan, 'do');
    // Phieu bi tu choi KHONG chan lap phieu moi nua (sua 19/08/2026), nen
    // ve ca dong xam bao da tung co phieu LAN nut hoan tien.
    var truoc = dsvHt.bi_tu_choi ? dsvKhoiHt(dsvHt.bi_tu_choi, 'xam') : '';
    if (!dsvHt.duoc) return truoc;
    return truoc + '<div style="margin-top:10px"><button id="dsvHoanTien" ' +
      'style="width:100%;border:1.5px solid #fecaca;background:#fff;color:#b91c1c;border-radius:10px;' +
      'padding:10px;font-size:13.5px;font-weight:700">↩︎ Hoàn tiền / Trả hàng</button></div>';
  }

  function dsvGanHt() {
    var n = document.getElementById('dsvHoanTien');
    if (!n) return;
    n.onclick = function () { dsvHoiHt(); };
  }

  function dsvHoiHt() {
    var ten = { 'Khach doi y': 'Khách đổi ý', 'Banh hong': 'Bánh hỏng', 'Di ung': 'Dị ứng',
                'Giao sai mon': 'Giao sai món', 'Giao tre': 'Giao trễ', 'Khac': 'Khác' };
    var ds = (dsvHt.ly_do_co_the || []).map(function (x) {
      return '<option value="' + h(x) + '">' + h(ten[x] || x) + '</option>';
    }).join('');
    var than = (dsvHt.canh_bao_hddt
        ? '<div style="padding:9px 11px;border-radius:9px;background:#fffbeb;border:1.5px solid #fde68a;' +
          'font-size:12.5px;color:#78350f;margin-bottom:10px">Đơn này đã xuất hoá đơn điện tử số <b>' +
          h(dsvHt.canh_bao_hddt) + '</b>. Máy KHÔNG tự động xử lý bên m-invoice, chị Dung phải làm tay.</div>'
        : '') +
      '<div style="font-size:12px;color:#6b7280;margin-bottom:3px">Lý do hoàn</div>' +
      '<select id="htLyDo" style="width:100%;box-sizing:border-box;border:1.5px solid #d1d5db;border-radius:8px;padding:8px 10px;font-size:13.5px;margin-bottom:9px">' + ds + '</select>' +
      '<textarea id="htDienGiai" placeholder="Diễn giải thêm (bắt buộc nếu chọn Khác)" ' +
      'style="width:100%;box-sizing:border-box;border:1.5px solid #d1d5db;border-radius:8px;padding:8px 10px;font-size:13px;min-height:52px;margin-bottom:11px"></textarea>' +
      '<div style="font-weight:700;font-size:12.5px;margin-bottom:6px">Tài khoản nhận tiền của khách</div>' +
      '<input id="htTenTk" placeholder="Tên chủ tài khoản" style="width:100%;box-sizing:border-box;border:1.5px solid #d1d5db;border-radius:8px;padding:8px 10px;font-size:13.5px;margin-bottom:7px">' +
      '<input id="htSoTk" inputmode="numeric" placeholder="Số tài khoản" style="width:100%;box-sizing:border-box;border:1.5px solid #d1d5db;border-radius:8px;padding:8px 10px;font-size:13.5px;margin-bottom:7px">' +
      '<input id="htNganHang" list="htDsNh" placeholder="Ngân hàng" style="width:100%;box-sizing:border-box;border:1.5px solid #d1d5db;border-radius:8px;padding:8px 10px;font-size:13.5px;margin-bottom:7px">' +
      '<datalist id="htDsNh"></datalist>' +
      '<input id="htSdt" inputmode="numeric" placeholder="Số điện thoại khách" style="width:100%;box-sizing:border-box;border:1.5px solid #d1d5db;border-radius:8px;padding:8px 10px;font-size:13.5px;margin-bottom:11px">' +
      '<div style="font-size:12px;color:#6b7280;margin-bottom:3px">Mã PIN quản lý</div>' +
      '<input id="htOtp" inputmode="numeric" maxlength="6" placeholder="6 số" style="width:100%;box-sizing:border-box;border:1.5px solid #fca5a5;border-radius:8px;padding:8px 10px;font-size:16px;letter-spacing:3px;text-align:center">';
    var hp = hopKhung('Hoàn tiền ' + money(dsvHt.so_tien) + ' đ', than,
      '<button class="btn gh" id="htThoi" style="flex:1;margin:0">Thôi</button>' +
      '<button class="btn" id="htOk" style="flex:1;margin:0;background:#b91c1c">Xác nhận hoàn tiền</button>');
    hp.box.querySelector('.x').onclick = hp.dong;
    hp.box.querySelector('#htThoi').onclick = hp.dong;
    hp.box.querySelector('#htOk').onclick = async function () {
        var goi = {
          si_name: d.name,
          ly_do: (document.getElementById('htLyDo') || {}).value,
          dien_giai: (document.getElementById('htDienGiai') || {}).value || '',
          ten_tk: (document.getElementById('htTenTk') || {}).value || '',
          so_tk: (document.getElementById('htSoTk') || {}).value || '',
          ngan_hang: (document.getElementById('htNganHang') || {}).value || '',
          sdt_khach: (document.getElementById('htSdt') || {}).value || '',
          otp: ((document.getElementById('htOtp') || {}).value || '').replace(/\D/g, '')
        };
        if (goi.otp.length !== 6) { toast('Cần mã PIN 6 số của quản lý.'); return; }
        busy(true);
        try {
          var kq = await api('vagabond.hoan_tien.tao', goi);
          busy(false); hp.dong();
          toast('Đã lập phiếu hoàn tiền ' + kq.ho_so, 3500);
          baoTin('Hàng đã vào ' + kq.kho_huy + ', KHÔNG về kho bán.\n\n' +
            'Phiếu chi ' + (kq.phieu_chi || '(chưa lập được)') + ' đang ở trạng thái nháp. ' +
            'Chị Dung chuyển khoản, đính kèm uỷ nhiệm chi rồi mới ghi sổ được.\n\n' +
            'Nội dung chuyển khoản phải gõ đúng: ' + kq.noi_dung_ck);
          await dsvNapLai();
        } catch (e) { busy(false); }
      };
    /* Danh sách ngân hàng tải sau khi hộp thoại đã mở, để hộp thoại hiện
       ra ngay chứ không đứng chờ mạng. */
    api('vagabond.hoan_tien.ds_ngan_hang', {}).then(function (r) {
      var dl = document.getElementById('htDsNh');
      if (dl) dl.innerHTML = (r || []).map(function (x) { return '<option value="' + h(x.name) + '">'; }).join('');
    }).catch(function () { });
  }

  async function dsvNapLai() {
    try { d = await api('frappe.client.get', { doctype: 'Sales Invoice', name: d.name }); } catch (e) { }
    await dsvTaiThe();
    await dsvTaiHt();
    veKhachNo();
  }

  veKhachNo();
  dsvTaiThe().then(veKhachNo);
  dsvTaiHt().then(veKhachNo);
  if (d.custom_hddt_so) dsvVeThayThe(d.name);
  function mtcGiaTri() { var o = document.getElementById('dsvMtc'); return o ? o.value : ''; }
  function xhdVe() {
    var ch = document.getElementById('xhdChon');
    if (!ch) return;
    ch.querySelectorAll('.xhdc').forEach(function (b) {
      var on = b.getAttribute('data-loai') === xhdLoai;
      b.style.border = '1.5px solid ' + (on ? '#0d9488' : '#e5e7eb');
      b.style.background = on ? '#ccfbf1' : '#fff';
      b.style.color = on ? '#0f766e' : '#374151';
      b.style.fontWeight = on ? 'bold' : 'normal';
    });
    var f = document.getElementById('xhdForm');
    if (f) f.style.display = xhdLoai === 'cong_ty' ? 'flex' : 'none';
  }
  var xhdCh = document.getElementById('xhdChon');
  if (xhdCh) {
    xhdCh.querySelectorAll('.xhdc').forEach(function (b) {
      b.onclick = function () { xhdLoai = b.getAttribute('data-loai'); xhdVe(); };
    });
    xhdVe();
  }
  var xmst = document.getElementById('xhdMst');
  if (xmst) xmst.onblur = async function () {
    var so = (xmst.value || '').replace(/[^0-9]/g, '');
    var bao = document.getElementById('xhdBao');
    /* 12 so la so dinh danh ca nhan cua chu ho kinh doanh, hop le tu
       01/07/2025 theo dieu 5 Thong tu 86/2024/TT-BTC. */
    if (so.length !== 10 && so.length !== 12 && so.length !== 13) {
      if (bao) bao.textContent = so ? 'Mã số thuế phải 10 số (công ty), 12 số (hộ kinh doanh) hoặc 13 số (chi nhánh).' : '';
      return;
    }
    if (bao) bao.textContent = 'Đang tra mã số thuế...';
    try {
      var kq = await api('vagabond.api.tra_mst', { mst: so });
      var t = document.getElementById('xhdTen'), dc = document.getElementById('xhdDc');
      if (kq && kq.ok) {
        if (t && !t.value.trim()) t.value = kq.ten || '';
        if (dc && !dc.value.trim()) dc.value = kq.dia_chi || '';
        /* Cong thong tin thue tra ve ten chi co loai hinh phap ly, khong co
           ten rieng. Da xay ra that ngay 22/08/2026 voi ma 0108903529: to
           hoa don 10901 mang ten "CÔNG TY CỔ PHẦN", khach khieu nai, ke toan
           phai lap bien ban va xuat to thay the. O ten van sua tay duoc,
           nen bao dong that to roi de nguoi doc quyet. */
        if (kq.nghi_thieu) {
          if (bao) {
            bao.innerHTML = '<span style="display:block;background:#fef3c7;border:1px solid #fcd34d;'
              + 'border-radius:8px;padding:8px 10px;color:#92400e;font-weight:700;line-height:1.5">⚠️ '
              + xesc(kq.canh_bao || 'Hệ thống nghi ngờ tên công ty bị thiếu. Vui lòng kiểm tra lại thông tin!')
              + '<br><span style="font-weight:400">Cổng tra cứu chỉ trả về "' + xesc(kq.ten || '')
              + '". Vui lòng xem giấy phép kinh doanh của khách rồi gõ đủ tên vào ô bên trên.</span></span>';
          }
          if (t) { t.style.borderColor = '#f59e0b'; t.focus(); }
          toast('Tên công ty tra về bị thiếu, vui lòng kiểm tra lại!', 6000);
        } else {
          if (t) t.style.borderColor = '#e5e7eb';
          if (bao) bao.textContent = 'Tra được: ' + (kq.ten || '');
        }
      } else if (bao) bao.textContent = 'Không tra được mã này, vui lòng điền tay.';
    } catch (e) { if (bao) bao.textContent = 'Không tra được mã này, vui lòng điền tay.'; }
  };
  async function luuXhd(ten_si) {
    if (d.custom_hddt_so) return;
    if (xhdLoai !== 'cong_ty') { await api('vagabond.ban_hang.luu_xhd', { si_name: ten_si, ten: XHD_MD }); return; }
    var mst = ((document.getElementById('xhdMst') || {}).value || '').replace(/[^0-9]/g, '');
    var ten = ((document.getElementById('xhdTen') || {}).value || '').trim();
    if (!mst || !ten) throw new Error('Xuất hoá đơn cho công ty hoặc hộ kinh doanh thì phải có mã số thuế và tên pháp nhân.');
    await api('vagabond.ban_hang.luu_xhd', { si_name: ten_si, ten: ten, mst: mst, dia_chi: ((document.getElementById('xhdDc') || {}).value || ''), email: ((document.getElementById('xhdEmail') || {}).value || '') });
  }
  var xlu = document.getElementById('xhdLuu');
  if (xlu) xlu.onclick = async function () {
    busy(true);
    try { await api('vagabond.ban_hang.luu_thanh_toan', { si_name: d.name, pt: DSV_PT, ma_tham_chieu: mtcGiaTri() }); await luuXhd(d.name); busy(false); toast('Đã lưu thông tin đơn'); }
    catch (e) { busy(false); baoTin((e && e.message) || 'Lưu lỗi'); }
  };
  (async function () {
    var o = document.getElementById('dsvSepay');
    if (!o) return;
    try {
      var kq = await api('vgb_gd_sepay', { phieu: d.name });
      var ds = (kq && kq.giao_dich) || [];
      var tieu = '<div style="font-size:12px;color:#6b7280;margin-bottom:6px"><b>Giao dịch SePay khớp theo mã đơn</b></div>';
      if (!ds.length) {
        o.innerHTML = tieu + '<div style="color:#9ca3af">Chưa nhận được chuyển khoản nào mang mã đơn này.</div>';
        return;
      }
      var dong = ds.map(function (g) {
        var vn = String(g.ngay || '').split('-');
        var ng = vn.length === 3 ? vn[2] + '/' + vn[1] : g.ngay;
        return '<div style="display:flex;justify-content:space-between;gap:8px;padding:5px 0;border-top:1px solid #f1f5f9">'
          + '<span style="color:#374151">' + ng + ' · ' + xesc(g.ma_tham_chieu || g.ma_gd) + '</span>'
          + '<b style="white-space:nowrap;color:#166534">' + Number(g.so_tien || 0).toLocaleString('vi-VN') + ' đ</b></div>';
      }).join('');
      var du = kq.du_tien ? '<span style="color:#166534;font-weight:700">Đủ tiền</span>'
        : '<span style="color:#b45309;font-weight:700">Thiếu ' + Number((kq.tien_phieu || 0) - (kq.tong_da_nhan || 0)).toLocaleString('vi-VN') + ' đ</span>';
      o.innerHTML = tieu + dong
        + '<div style="display:flex;justify-content:space-between;padding-top:6px;border-top:1.5px solid #e5e7eb;margin-top:4px">'
        + '<span>Đã nhận ' + Number(kq.tong_da_nhan || 0).toLocaleString('vi-VN') + ' đ / đơn ' + Number(kq.tien_phieu || 0).toLocaleString('vi-VN') + ' đ</span>' + du + '</div>';
    } catch (e) {
      o.innerHTML = '<div style="color:#9ca3af;font-size:12px">Chưa tra được giao dịch SePay.</div>';
    }
  })();
  var cDn = document.getElementById('dsvDoiNgay');
  if (cDn) cDn.onclick = async function () {
    var ok = await confirmSheet(
      'Chuyển đơn sang hôm nay',
      'Đơn #' + (d.custom_pancake_display_id || d.name) + ' đang mang ngày ' + d.posting_date +
      '.\nChuyển sang ' + today() + ' để hoá đơn điện tử xuất đúng ngày theo luật thuế.\n\n' +
      'Doanh thu của đơn sẽ tính vào ngày mới, không còn nằm ở ngày cũ.',
      'Chuyển sang hôm nay');
    if (!ok) return;
    var otp = await promptSheet('Đổi ngày hoá đơn cần mã OTP của quản lý', 'Nhập 6 số quản lý đọc cho');
    if (otp === null) return;
    busy(true);
    try {
      await api('vagabond.ban_hang.doi_ngay_hoa_don', { si_name: d.name, otp: (otp || '').replace(/\D/g, ''), ly_do: 'sửa đơn trục trặc' });
      busy(false);
      toast('Đã chuyển đơn sang ' + posNgayVn(today()));
      dsNgay = today();
      go(scrDoanhSo, true);
    } catch (e) { busy(false); baoTin((e && e.message) || 'Không đổi được ngày'); }
  };
  var c1 = document.getElementById('dsvChot');
  if (c1) c1.onclick = async function () {
    if (!DSV_PT && !await xacNhan('Chưa chọn phương thức thanh toán. Vẫn ghi sổ chứ?')) return;
    if (DSV_PT === 'Công nợ' && !dsvKhach.ma) {
      return baoTin('Đơn bán công nợ phải chọn khách công nợ, không thì cuối tháng không biết đòi ai.');
    }
    if (!await xacNhan('Ghi sổ hoá đơn cho đơn #' + (d.custom_pancake_display_id || '') + '? Số sẽ vào doanh thu chính thức.')) return;
    busy(true);
    try { await luuXhd(d.name); await api('vagabond.ban_hang.chot_mot_don', { si_name: d.name, pt: DSV_PT, ma_tham_chieu: mtcGiaTri(), khach: dsvKhach.ma || '' }); busy(false); toast('Đã ghi sổ ' + d.name); }
    catch (e) { busy(false); baoTin((e && e.message) || 'Chốt lỗi'); }
    go(scrDoanhSo, true);
  };
  var c2 = document.getElementById('dsvHddt');
  if (c2) c2.onclick = async function () {
    if (!await xacNhan('Xuất hoá đơn điện tử (Chờ ký) cho đơn này?')) return;
    busy(true);
    try { var kq = await api('vagabond.ban_hang.xuat_hoa_don_dien_tu', { si_name: d.name }); busy(false); toast('Đã tạo HĐĐT Chờ ký' + (kq && kq.inv_invoiceNumber ? ', số ' + kq.inv_invoiceNumber : '')); }
    catch (e) { busy(false); baoTin((e && e.message) || 'Xuất HĐĐT lỗi'); }
    go(scrDoanhSo, true);
  };
}
function dstSoThuan(v) {
  return String(v == null ? '' : v).replace(/[^0-9]/g, '');
}
function dstNganCach(v) {
  var t = dstSoThuan(v);
  return t ? t.replace(/\B(?=(\d{3})+(?!\d))/g, '.') : '';
}
function dstGanNganCach() {
  ['dstGiam', 'dstShip'].forEach(function (id) {
    var el = document.getElementById(id);
    if (!el || el.dataset.ngan) return;
    el.dataset.ngan = '1';
    el.addEventListener('input', function () { el.value = dstNganCach(el.value); });
  });
}
var dsTay = null, dsItemsCache = null;

/* Cac diem ban nhan mot nguon don.

   Tu 12/08/2026 "Tại chỗ" va "Mang về" dung chung cho moi quay (anh Viet:
   ban chat la mot, da quan ly tu buoc diem ban roi). Doi lai, ten nguon
   khong con noi duoc don cua diem nao nua, nen man Nhap don tay phai HOI
   chu khong duoc doan: hoa don khong mang ma quay thi ca he doc no thanh
   don Sales Online, doanh thu quay ve nham cho ma khong ai bao loi. */
function dstDiemDs(nguon) {
  var n = nguonBH(nguon) || {};
  var ds = n.diem_ds || (n.diem ? [n.diem] : []);
  /* Tra ten theo danh sach DIEM day du chu khong theo danh sach quay: tu
     15/08/2026 "Tại chỗ" va "Mang về" gan duoc cho ca Sales Online, ma
     Sales khong nam trong CFGBH.quay nen truoc day o chon chi hien tro
     ma "SALES" cut lun (anh Viet). Giu CFGBH.quay lam duong lui cho ban
     app cu chua co truong moi. */
  var dm = (CFGBH || {}).diem || [];
  var q = (CFGBH || {}).quay || [];
  return ds.map(function (ma) {
    var t = null, tq = null;
    dm.forEach(function (x) { if (x.ma === ma) t = x; });
    q.forEach(function (x) { if (x.ma === ma) tq = x; });
    if (t) return { ma: ma, ten: t.ten || ma, phu: t.phu || (t.co_quay ? '' : 'Đơn online, không thuộc quầy nào'), anh: t.anh || '', quay: !!t.co_quay };
    return { ma: ma, ten: tq ? tq.ten : ma, phu: tq ? (tq.phu || '') : 'Đơn online, không thuộc quầy nào', anh: tq ? (tq.anh || '') : '', quay: !!tq };
  });
}
function dsTayDoc() {
  if (!dsTay) return;
  var g = function (id) { var el = document.getElementById(id); return el ? el.value : ''; };
  dsTay.ma = g('dstMa'); dsTay.ten = g('dstTen'); dsTay.sdt = g('dstSdt'); dsTay.giam = dstSoThuan(g('dstGiam')); dsTay.ship = dstSoThuan(g('dstShip')); dsTay.mtc = g('dstMtc');
}
async function scrDsNhapTay() {
  await cfgBanHang();
  /* Ma bill sinh ngay luc mo man, giong hetben quay: co ma thi moi sinh
     duoc QR cho khach quet TRUOC khi luu don, va luu xong thi chinh ma nay
     di vao o ma tham chieu de SePay doi soat (anh Viet 12/08/2026). */
  if (!dsTay) dsTay = { nguon: 'GrabFood', bill: posMaBill(), ma: '', ten: '', sdt: '', giam: '', ship: '', pt: '', mtc: '', mon: [], quay: '' };
  if (!dsTay.bill) dsTay.bill = posMaBill();
  /* Diem ban KHONG hoi lai nua, may tu dien san.
     Anh Viet 15/08/2026: *"truoc khi vao man hinh tinh tien da phai chon
     diem ban roi ma, sao vao man tinh tien lai phai chon them diem ban khi
     bam bill"*. Dung: man Nhap don tay nam trong Doanh thu Sales, ma
     Doanh thu Sales chinh la diem nhan don online - nguoi dung da chon no
     o man "Chon diem ban" truoc do roi. Nen mac dinh lay dung diem do,
     dong Diem ban van hien de nhin ra don dang ghi cho noi nao va van bam
     doi duoc khi Sales nhap ho mot quay. */
  var dstDiem = dstDiemDs(dsTay.nguon);
  if (!dstDiem.some(function (x) { return x.ma === dsTay.quay; })) {
    var mac = null;
    dstDiem.forEach(function (x) { if (!mac && !x.quay) mac = x; });
    dsTay.quay = (mac || dstDiem[0] || {}).ma || '';
  }
  var dstPhaiChon = dstDiem.length > 1;
  var dstTenDiem = '';
  dstDiem.forEach(function (x) { if (x.ma === dsTay.quay) dstTenDiem = x.ten; });
  var dsPt = ptTheoNguon(dsTay.nguon);
  if (dsPt.length === 1) dsTay.pt = dsPt[0].v;
  if (dsTay.pt && !dsPt.some(function (p) { return p.v === dsTay.pt; })) dsTay.pt = dsPt.length === 1 ? dsPt[0].v : '';
  var tong = dsTay.mon.reduce(function (t, m) { return t + m.qty * m.rate; }, 0);
  var html = '<div class="card" style="padding:12px 14px;display:grid;gap:10px">' +
    '<div class="hub" data-t="nguon" style="padding:10px 0;border:none"><div class="ht"><div class="h2">Nguồn đơn</div><div class="h1">' + h(dsTay.nguon) + '</div></div><span style="color:#c3c8d4">&#8250;</span></div>' +
    (dstPhaiChon
      ? '<div class="hub" data-t="diem" style="padding:10px 0;border:none;border-top:1px solid #f0f2f6"><div class="ht"><div class="h2">Điểm bán · bấm để đổi</div><div class="h1"' +
        (dstTenDiem ? '' : ' style="color:#b3261e"') + '>' + h(dstTenDiem || 'Chưa chọn - bắt buộc') + '</div></div><span style="color:#c3c8d4">&#8250;</span></div>'
      : '<div style="border-top:1px solid #f0f2f6;padding-top:9px;font-size:12.5px;color:#8a8f9c">Điểm bán: <b style="color:#374151">' + h(dstTenDiem || '') + '</b></div>') +
    '<input class="tin" id="dstMa" placeholder="Mã đơn bên app (vd GF-123 hoặc số HĐ Fabi)" value="' + h(dsTay.ma) + '">' +
    '<input class="tin" id="dstTen" placeholder="Tên khách" value="' + h(dsTay.ten) + '">' +
    '<input class="tin" id="dstSdt" placeholder="Số điện thoại (không bắt buộc)" inputmode="tel" value="' + h(dsTay.sdt) + '">' +
    '</div>';
  html += '<div class="sec">Phương thức thanh toán</div><div class="card" style="padding:12px 14px;display:grid;gap:10px">' +
    (dsPt.length > 1
      ? '<div id="dstPt" style="display:flex;gap:6px;flex-wrap:wrap">' + chipPt(dsPt, dsTay.pt) + '</div>'
      : '<div style="font-size:13px;color:#6b7280">Đơn ' + h(dsTay.nguon) + ' chỉ có một phương thức: <b>' + h(dsPt.length ? dsPt[0].v : '') + '</b></div>') +
    '<div><div id="dstMtcNhan" style="font-size:12px;color:#6b7280;margin-bottom:6px"></div>' +
    '<input class="tin" id="dstMtc" placeholder="Mã tham chiếu" value="' + h(dsTay.mtc || '') + '"></div>' +
    '<div id="dstQr"></div>' +
    '</div>';
  html += '<div class="sec">Món trong đơn</div><div class="card" style="padding:6px 14px">';
  if (!dsTay.mon.length) html += '<div style="padding:14px 0;color:#a0a6b4">Chưa có món nào, bấm Thêm món.</div>';
  dsTay.mon.forEach(function (m, i) {
    /* Co anh mon thi nhin phat ra ngay, khong phai doc ten dai (anh Viet
       12/08/2026: "mon khi chon xong bi thieu hinh anh, kho nhan biet"). */
    html += '<div style="display:flex;flex-direction:row;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #f0f2f6">' +
      (m.anh
        ? '<img src="' + h(m.anh) + '" style="width:42px;height:42px;flex:none;border-radius:9px;object-fit:cover;background:#f2f4f7" onerror="this.style.visibility=\'hidden\'">'
        : '<div style="width:42px;height:42px;flex:none;border-radius:9px;background:#f2f4f7;display:flex;align-items:center;justify-content:center;font-size:19px">🎂</div>') +
      '<div style="flex:1;min-width:0">' + h(m.ten) + '<div style="color:#a0a6b4;font-size:12px">' + money(m.qty) + ' x ' + money(m.rate) + ' đ</div></div>' +
      '<b>' + money(m.qty * m.rate) + '</b><button class="ic" data-x="' + i + '" style="color:#b3261e">✕</button></div>';
  });
  html += '<div style="padding:10px 0"><button class="btn gh" id="dstThem" style="width:100%">➕ Thêm món</button></div></div>';
  html += '<div class="sec">Giảm giá và phí giao</div><div class="card" style="padding:12px 14px;display:grid;gap:10px">' +
    '<input class="tin" id="dstGiam" placeholder="Giảm giá cả đơn (đ), vd chiết khấu Grab" inputmode="numeric" value="' + h(dstNganCach(dsTay.giam)) + '">' +
    '<input class="tin" id="dstShip" placeholder="Phí giao thu của khách (đ), để trống nếu không" inputmode="numeric" value="' + h(dstNganCach(dsTay.ship)) + '">' +
    '</div>';
  html += '<div style="text-align:right;padding:6px 14px;color:#6b7280">Tạm tính: <b>' + money(tong) + ' đ</b> (chưa trừ giảm, chưa cộng ship)</div>';
  var b = frame('Nhập đơn tay', html, { footer: '<button class="btn" id="dstLuu">Lưu đơn nháp vào ngày ' + dsNgay.split('-').reverse().join('/') + '</button>' });
  dstGanNganCach();
  b.addEventListener('click', function (e) {
    if (e.target.closest('[data-t="nguon"]')) {
      dsTayDoc();
      return sheet('Nguồn đơn', ((CFGBH || {}).nguon || []).map(function (n) { return { value: n.v, label: n.v, icon: n.ic || '', img: n.lg || '' }; }), dsTay.nguon, function (o) { dsTay.nguon = o.value; dsTay.quay = ''; go(scrDsNhapTay, true); });
    }
    if (e.target.closest('[data-t="diem"]')) {
      dsTayDoc();
      return sheet('Điểm bán', dstDiem.map(function (x) { return { value: x.ma, label: x.ten, phu: x.phu, img: x.anh || '', icon: x.anh ? '' : '🏪' }; }), dsTay.quay, function (o) { dsTay.quay = o.value; go(scrDsNhapTay, true); });
    }
    var x = e.target.closest('[data-x]');
    if (x) { dsTayDoc(); dsTay.mon.splice(parseInt(x.getAttribute('data-x'), 10), 1); go(scrDsNhapTay, true); }
  });
  /* Ma QR cho don nhap tay. Noi dung mang ma diem ban cua nguon don, cong
     ma bill sinh san - de ke toan doc sao ke la biet tien cua noi nao, va
     SePay tu khop duoc vao dung don sau khi luu. */
  function dstVeQr() {
    var o = document.getElementById('dstQr');
    if (!o) return;
    if (dsTay.pt !== 'Chuyển khoản') { o.innerHTML = ''; return; }
    var giam = parseFloat(dsTay.giam || 0) || 0, ship = parseFloat(dsTay.ship || 0) || 0;
    var thu = dsTay.mon.reduce(function (t, m) { return t + m.qty * m.rate; }, 0) - giam + ship;
    var diem = dsTay.quay || (nguonBH(dsTay.nguon) || {}).diem || '';
    var nd = posNoiDungCk(dsTay.bill, diem, dsTay.nguon);
    var url = posQrUrl(nd, thu, dsTay.nguon, diem);
    if (!url) {
      o.innerHTML = '<div style="border:1.5px solid #fecaca;background:#fef2f2;border-radius:10px;padding:12px;font-size:13px;color:#b3261e;line-height:1.6">' +
        'Chưa khai số tài khoản nhận chuyển khoản nên chưa sinh được mã QR. Vào Cài đặt · Tài khoản nhận tiền để khai.</div>';
      return;
    }
    var tk = posTaiKhoan(dsTay.nguon, diem);
    o.innerHTML = '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:12px;text-align:center;background:#fff">' +
      '<div style="font-size:12.5px;color:#6b7280">Khách quét mã này, máy tự điền số tiền và nội dung</div>' +
      '<img src="' + url + '" alt="Mã QR chuyển khoản" style="width:min(230px,60vw);aspect-ratio:1;margin:10px auto 6px;display:block;border-radius:10px;background:#fff">' +
      '<div style="font-size:18px;font-weight:800;color:#0f766e">' + money(thu) + ' đ</div>' +
      '<div style="font-size:13px;color:#374151;margin-top:2px">Nội dung: <b>' + h(nd) + '</b></div>' +
      '<div style="font-size:12px;color:#98a2b3;margin-top:2px">' + h(tk.ten || '') + ' · ' + h((tk.bank || '') + ' ' + (tk.stk || '')) +
      (tk.rieng ? ' · tài khoản riêng của nguồn này' : '') + '</div>' +
      '<div style="font-size:11.5px;color:#98a2b3;margin-top:6px;line-height:1.5">Số tiền trên mã đã trừ giảm giá và cộng phí giao. Sửa món hay giảm giá thì mã tự vẽ lại.</div></div>';
  }

  function dstVeMtc() {
    var q = quyPt(dsTay.pt) || {};
    var oMtc = document.getElementById('dstMtc');
    var oMa = document.getElementById('dstMa');
    var boc = oMtc ? oMtc.parentElement : null;
    if (dsPt.length === 1) {
      // Don san: ma don ben app CHINH LA ma tham chieu, chi nhap mot lan.
      if (boc) boc.style.display = 'none';
      if (oMa) oMa.placeholder = (q.nhan || 'Mã đơn bên app') + (q.vd ? ' - vd ' + q.vd : '');
    } else {
      if (boc) boc.style.display = '';
      if (oMa) oMa.placeholder = 'Số phiếu nội bộ (không bắt buộc)';
      veOMtc(dsTay.pt, 'dstMtc', 'dstMtcNhan');
    }
  }
  var ptw = document.getElementById('dstPt');
  if (ptw) ptw.querySelectorAll('.ptc').forEach(function (b) {
    b.onclick = function () {
      dsTayDoc();
      dsTay.pt = b.getAttribute('data-pt');
      veChipPt(ptw, dsTay.pt);
      dstVeMtc();
      dstVeQr();
    };
  });
  dstVeMtc();
  dstVeQr();
  /* Sua so tien la mo QR phai doi theo, khong thi khach quet ra so cu. */
  ['dstGiam', 'dstShip'].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.addEventListener('input', function () { dsTayDoc(); dstVeQr(); });
  });
  document.getElementById('dstThem').onclick = dsTayThemMon;
  document.getElementById('dstLuu').onclick = dsTayLuu;
}
function themMonSheet(o, giaGoi) {
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  var g0 = parseFloat(giaGoi || 0) || 0;
  box.innerHTML = '<div class="shh"><b>Thêm món</b><div class="x">&times;</div></div>' +
    '<div style="padding:12px 14px calc(env(safe-area-inset-bottom,0px) + 14px);display:grid;gap:14px">' +
    '<div style="display:flex;gap:10px;align-items:center">' +
      (o.img ? '<img src="' + o.img + '" style="width:52px;height:52px;object-fit:cover;border-radius:10px;border:1px solid #e5e7eb">' : '<span style="font-size:34px">🎂</span>') +
      '<div style="flex:1;min-width:0"><b>' + h(o.label) + '</b><div style="color:#a0a6b4;font-size:12px">' + h(o.value) + '</div></div></div>' +
    '<div><div style="font-size:12px;color:#6b7280;margin-bottom:6px">Giá bán 1 đơn vị (đ)</div>' +
      '<input class="nt" id="tmGia" inputmode="numeric" value="' + (g0 ? money(g0) : '') + '" placeholder="0" style="height:48px;padding:0 12px;width:100%;box-sizing:border-box;text-align:right;font-size:18px;font-weight:bold"></div>' +
    '<div><div style="font-size:12px;color:#6b7280;margin-bottom:6px">Số lượng</div>' +
      '<div style="display:flex;gap:10px;align-items:center">' +
      '<button class="nt" id="tmTru" style="height:54px;width:58px;flex:none;font-size:26px;cursor:pointer">&minus;</button>' +
      '<input class="nt" id="tmSl" inputmode="decimal" value="1" style="height:54px;flex:1;text-align:center;font-size:22px;font-weight:bold;padding:0">' +
      '<button class="nt" id="tmCong" style="height:54px;width:58px;flex:none;font-size:26px;cursor:pointer">+</button></div></div>' +
    '<div style="display:flex;justify-content:space-between;align-items:center;font-size:16px"><span style="color:#5a6070">Tạm tính</span><b id="tmTong">0 đ</b></div>' +
    '<button class="btn" id="tmOk">Thêm vào đơn</button></div>';
  ov.appendChild(box); document.body.appendChild(ov);
  function dong() { ov.remove(); }
  ov.onclick = function (e) { if (e.target === ov) dong(); };
  box.querySelector('.x').onclick = dong;
  var oGia = box.querySelector('#tmGia'), oSl = box.querySelector('#tmSl'), oTong = box.querySelector('#tmTong');
  // Tien Viet dung dau cham lam phan cach nghin: o TIEN phai bo sach dau cham,
  // chi o SO LUONG moi cho phep dau thap phan.
  function soGia(el) { return parseFloat(String(el.value || '').replace(/[^0-9]/g, '')) || 0; }
  function soSl(el) { return parseFloat(String(el.value || '').replace(/,/g, '.').replace(/[^0-9.]/g, '')) || 0; }
  function ve() { oTong.textContent = money(soGia(oGia) * soSl(oSl)) + ' đ'; }
  oGia.oninput = ve; oSl.oninput = ve; ve();
  box.querySelector('#tmTru').onclick = function () { oSl.value = Math.max(1, soSl(oSl) - 1); ve(); };
  box.querySelector('#tmCong').onclick = function () { oSl.value = soSl(oSl) + 1; ve(); };
  oGia.onblur = function () { var g = soGia(oGia); oGia.value = g ? money(g) : ''; ve(); };
  box.querySelector('#tmOk').onclick = function () {
    var sl = soSl(oSl), gia = soGia(oGia);
    if (sl <= 0) return toast('Số lượng phải lớn hơn 0');
    dong();
    dsTay.mon.push({ item_code: o.value, ten: o.label, qty: sl, rate: gia, anh: o.img || '' });
    go(scrDsNhapTay, true);
  };
  setTimeout(function () { oSl.focus(); oSl.select(); }, 60);
}
async function dsTayThemMon() {
  dsTayDoc();
  if (!dsItemsCache) {
    busy(true);
    try { dsItemsCache = await getList('Item', { filters: { is_sales_item: 1, disabled: 0, item_group: ['not in', ['Nguyên vật liệu Thô', 'Bán thành phẩm Bánh', 'Bán thành phẩm Nước', 'Nhân bán thành phẩm', 'Công cụ Dụng cụ', 'Bao bì', 'Văn phòng phẩm', 'Tài sản Cố định']] }, fields: ['name', 'item_name', 'image', 'standard_rate'], limit_page_length: 0, order_by: 'item_name' });
      try {
        var dsBC = await getList('Item Barcode', { parent: 'Item', fields: ['parent', 'barcode'], limit_page_length: 0 });
        var dsBCM = {};
        (dsBC || []).forEach(function (b) { dsBCM[b.parent] = (dsBCM[b.parent] ? dsBCM[b.parent] + ' ' : '') + b.barcode; });
        dsItemsCache.forEach(function (x) { x.ma_vach = dsBCM[x.name] || ''; });
      } catch (e2) { /* khong co quyen doc barcode thi thoi, van tim duoc theo ma */ } }
    catch (e) { busy(false); return baoTin('Không tải được danh mục món'); }
    busy(false);
  }
  sheet('Chọn món', dsItemsCache.map(function (x) { return { value: x.name, label: x.item_name, icon: '🎂', img: x.image || '', gia: x.standard_rate || 0, phu: (x.standard_rate ? money(x.standard_rate) + ' đ' : 'chưa có giá') + ' · ' + x.name, tim: x.name + ' ' + (x.ma_vach || '') }; }), null, function (o) {
    return themMonSheet(o, o.gia);
    dsTay.mon.push({ item_code: o.value, ten: o.label, qty: sl, rate: gia });
    go(scrDsNhapTay, true);
  }, true);
}
async function dsTayLuu() {
  dsTayDoc();
  if (!dsTay.mon.length) return baoTin('Đơn chưa có món nào.');
  /* Nguon dung chung nhieu diem ma chua chon diem thi khong cho luu: don
     do se roi vao Sales Online, doanh thu quay hut mot to ma khong ai thay. */
  var dsDiem = dstDiemDs(dsTay.nguon);
  if (dsDiem.length > 1 && !dsTay.quay) return baoTin('Nguồn "' + dsTay.nguon + '" dùng chung cho nhiều điểm bán. Chọn điểm bán trước khi lưu.');
  var giam = parseFloat(dsTay.giam || 0) || 0, ship = parseFloat(dsTay.ship || 0) || 0;
  var tong = dsTay.mon.reduce(function (t, m) { return t + m.qty * m.rate; }, 0) - giam + ship;
  var tenDiem = '';
  dsDiem.forEach(function (x) { if (x.ma === dsTay.quay) tenDiem = x.ten; });
  if (!await xacNhan('Lưu đơn ' + h(dsTay.nguon) + (tenDiem ? ' tại ' + tenDiem : '') + (dsTay.ma ? ' #' + dsTay.ma : '') + ', tổng ' + money(tong) + ' đ vào doanh thu ngày ' + dsNgay.split('-').reverse().join('/') + '?')) return;
  busy(true);
  try {
    await api('vagabond.ban_hang.tao_don_tay', {
      ngay: dsNgay, nguon: dsTay.nguon, ma_don: dsTay.ma, ten_khach: dsTay.ten, dien_thoai: dsTay.sdt,
      /* Chuyen khoan ma thu ngan khong go gi thi lay chinh ma bill in tren
         QR lam ma tham chieu, de SePay doi soat dung to khach da chuyen. */
      pt: dsTay.pt || '',
      ma_tham_chieu: (dsTay.mtc || '').trim() || (dsTay.pt === 'Chuyển khoản' ? dsTay.bill : ''),
      items: JSON.stringify(dsTay.mon.map(function (m) { return { item_code: m.item_code, qty: m.qty, rate: m.rate }; })),
      giam_gia: giam, phi_ship: ship, quay: dsTay.quay || ''
    });
    busy(false); toast('Đã lưu đơn nháp'); dsTay = null;
  } catch (e) { busy(false); return baoTin((e && e.message) || 'Lưu lỗi'); }
  go(scrDoanhSo, true);
}

/* ============================ HOÁ ĐƠN THAY THẾ ============================

   Anh Việt 24/08/2026, sau sự cố hoá đơn 10901 của đơn 92409: tờ đã ký, đã
   gửi cơ quan thuế, mang tên người mua thiếu hẳn phần tên riêng. Kế toán
   lập biên bản rồi xuất tờ thay thế bên M-Invoice, nhưng trong ERP không có
   chỗ nào ghi lại việc đó: đơn hàng vẫn hiện "Đã xuất HĐĐT số 10901".

   Khối này là chỗ ghi. Ba việc:
     1. Bật cờ "Hoá đơn bị sai sót, cần thay thế" và ghi lý do.
     2. Gõ tay số hoá đơn thay thế. Hệ thống chưa đọc ngược được thay đổi
        làm thẳng trên cổng M-Invoice nên đoán bừa là sai.
     3. Đính biên bản thay thế, thumbnail có nút X đúng luật v289.

   Câu diễn giải bắt buộc theo Nghị định 123/2020 hiện sẵn để kế toán chép
   sang M-Invoice, khỏi gõ tay và khỏi nhớ đúng thứ tự các phần. */

var DSVTT = {};
/* Kế toán vừa tích ô nhưng chưa gõ lý do: cờ ở máy chủ chưa được bật, chỉ
   mở phần nhập ở màn hình. Cờ chỉ ghi thật khi bấm Ghi nhận hoặc khi đính
   biên bản, vì cả hai đường đó mới có đủ căn cứ để ghi. */
var DSVTT_MO = {};

async function dsvVeThayThe(siName) {
  var o = document.getElementById('dsvTT');
  if (!o) return;
  var r;
  try { r = await api('vagabond.ban_hang.bien_ban_thay_the', { si_name: siName }); }
  catch (e) { o.innerHTML = ''; return; }
  if (!r || !r.da_xuat) { o.innerHTML = ''; return; }
  DSVTT[siName] = r;
  var esc = function (t) { return String(t == null ? '' : t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); };
  var xin = 'width:100%;box-sizing:border-box;padding:9px 10px;border:1.5px solid #e5e7eb;border-radius:8px;font-size:14px;font-family:inherit';

  var mo = r.sai_sot || DSVTT_MO[siName];
  var h_ = '<div style="border:1.5px solid ' + (mo ? '#fcd34d' : '#e5e7eb') + ';border-radius:10px;padding:10px;'
    + (mo ? 'background:#fffbeb;' : '') + '">'
    + '<label style="display:flex;align-items:center;gap:9px;cursor:pointer;font-size:13.5px;font-weight:700;color:#92400e">'
    + '<input type="checkbox" id="ttCo" ' + (mo ? 'checked' : '') + (r.sua_duoc ? '' : ' disabled')
    + ' style="width:18px;height:18px;flex:none">Hoá đơn bị sai sót / cần thay thế</label>';

  if (!r.sai_sot && !DSVTT_MO[siName]) {
    h_ += '<div style="font-size:11.5px;color:#9ca3af;margin-top:7px;line-height:1.55">'
      + 'Tích ô này khi tờ hoá đơn số ' + esc(r.so_cu) + ' đã phát hành bị sai thông tin. '
      + 'Kế toán xuất tờ thay thế bên M-Invoice rồi quay lại đây ghi số tờ mới và đính biên bản.'
      + '</div></div>';
    o.innerHTML = h_;
    var c0 = document.getElementById('ttCo');
    if (c0) c0.onchange = function () {
      if (!c0.checked) return;
      DSVTT_MO[siName] = 1;
      dsvVeThayThe(siName);
    };
    return;
  }

  h_ += '<div style="font-size:11.5px;color:#92400e;background:#fef3c7;border-radius:8px;padding:8px 10px;margin-top:9px;line-height:1.6">'
    + '<b>Câu bắt buộc trên tờ thay thế</b> (Nghị định 123/2020), chép nguyên câu này sang M-Invoice:<br>'
    + '<span id="ttCau" style="display:block;margin-top:5px;font-weight:700;color:#78350f">' + esc(r.dien_giai || '') + '</span>'
    + '<button id="ttChep" style="margin-top:7px;border:1px solid #d97706;background:#fff;color:#92400e;'
    + 'border-radius:8px;padding:5px 11px;font-size:12px;font-weight:700;cursor:pointer">Chép câu này</button>'
    + '</div>';

  if (r.thay_the) {
    h_ += '<div style="font-size:13px;color:#065f46;background:#f0fdf4;border:1px solid #a7f3d0;border-radius:8px;'
      + 'padding:9px 11px;margin-top:9px;line-height:1.6">Đã ghi nhận tờ thay thế <b>' + esc(r.thay_the) + '</b>'
      + (r.thay_the_luc ? ' lúc ' + esc(r.thay_the_luc) : '') + '.'
      + (r.sua_duoc ? '<br><span id="ttGo" style="color:#b91c1c;text-decoration:underline;cursor:pointer">Ghi nhầm, gỡ số này</span>' : '')
      + '</div>';
  } else if (r.sua_duoc) {
    h_ += '<div style="display:flex;flex-direction:column;gap:6px;margin-top:9px">'
      + '<input id="ttSo" placeholder="Số HĐĐT thay thế, chép từ M-Invoice" style="' + xin + '">'
      + '<input id="ttKh" placeholder="Ký hiệu tờ mới, ví dụ 1C26MPV (để trống cũng được)" style="' + xin + '">'
      + '<textarea id="ttLy" rows="2" placeholder="Lý do phải thay thế, ví dụ: tên người mua bị thiếu" style="' + xin + '">' + esc(r.ly_do || '') + '</textarea>'
      + '<button class="btn" id="ttLuu">Ghi nhận hoá đơn thay thế</button></div>';
  } else {
    h_ += '<div style="font-size:12px;color:#6b7280;margin-top:9px">Chưa ghi số tờ thay thế. Vui lòng nhờ bộ phận kế toán ghi giúp.</div>';
  }

  /* Biên bản thay thế. Thumbnail đi qua ô dùng chung oTep nên luôn có nút X
     ở góc, đúng luật v289. Gỡ được chừng nào chưa ghi số tờ thay thế: ghi
     rồi là hồ sơ đã khép, tờ biên bản trong đó là căn cứ giải trình. */
  var goDuoc = r.sua_duoc && !r.thay_the;
  var oAnh = (r.tep || []).map(function (t) {
    return oTep({
      url: '', ten: t.ten, anh: t.anh, cho: 1, nhan: 1, lop: 'ttanh',
      mo: 'data-tep="' + esc(t.tep) + '" data-ten="' + esc(t.ten) + '" data-anh="' + (t.anh ? 1 : 0) + '" style="cursor:pointer"',
      go: goDuoc ? ('data-go="' + esc(t.tep) + '" data-ten="' + esc(t.ten) + '"') : ''
    });
  }).join('');
  h_ += '<div style="margin-top:10px"><div style="font-size:12px;color:#6b7280;margin-bottom:6px"><b>Biên bản thay thế</b></div>'
    + '<div id="ttAnh" style="display:flex;gap:10px;flex-wrap:wrap">' + (oAnh || '<span style="font-size:12px;color:#9ca3af">Chưa đính tờ nào.</span>') + '</div>';
  if (r.sua_duoc) {
    h_ += '<button class="btn" id="ttDinh" style="margin-top:8px;width:100%">📎 '
      + ((r.tep || []).length ? 'Đính thêm biên bản' : 'Đính biên bản thay thế') + '</button>'
      + '<input type="file" id="ttTep" accept="image/*,application/pdf" style="display:none">';
  }
  h_ += '</div></div>';
  o.innerHTML = h_;
  dsvTTGan(siName, r);
}

function dsvTTGan(siName, r) {
  var esc = function (t) { return String(t == null ? '' : t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); };
  var cCo = document.getElementById('ttCo');
  if (cCo) cCo.onchange = function () {
    if (cCo.checked) return;
    /* Chưa ghi gì lên máy chủ thì bỏ tích là đóng khối lại, không sao. Đã
       ghi số tờ thay thế hoặc đã đính biên bản rồi thì cờ này là một sự
       thật đã xảy ra, bỏ đi là xoá dấu vết (QT-20). */
    if (r.thay_the || (r.tep || []).length) {
      cCo.checked = true;
      return toast('Đơn này đã ghi nhận hồ sơ thay thế nên không bỏ cờ được. Ghi nhầm thì gỡ số tờ thay thế.', 5500);
    }
    DSVTT_MO[siName] = 0;
    dsvVeThayThe(siName);
  };
  var cChep = document.getElementById('ttChep');
  if (cChep) cChep.onclick = function () {
    var t = (document.getElementById('ttCau') || {}).textContent || '';
    try { navigator.clipboard.writeText(t); toast('Đã chép câu diễn giải.', 2500); }
    catch (e) { toast('Máy không chép được, anh chị bôi đen câu trên rồi chép tay giúp.', 4500); }
  };
  var cLuu = document.getElementById('ttLuu');
  if (cLuu) cLuu.onclick = async function () {
    var so = ((document.getElementById('ttSo') || {}).value || '').trim();
    var kh = ((document.getElementById('ttKh') || {}).value || '').trim();
    var ly = ((document.getElementById('ttLy') || {}).value || '').trim();
    if (!so) return toast('Chưa nhập số hoá đơn thay thế.', 4000);
    if (!ly) return toast('Chưa ghi lý do phải thay thế.', 4000);
    busy(true);
    try {
      var kq = await api('vagabond.ban_hang.ghi_hoa_don_thay_the', { si_name: siName, so: so, ky_hieu: kh, ly_do: ly });
      busy(false);
      toast((kq && kq.loi_nhan) || 'Đã ghi nhận.', 4500);
      dsvVeThayThe(siName);
    } catch (e) { busy(false); baoTin(errMsg(e) || 'Không ghi nhận được', 'Lỗi'); }
  };
  var cGo = document.getElementById('ttGo');
  if (cGo) cGo.onclick = async function () {
    var ly = await promptSheet('Gỡ số hoá đơn thay thế', 'Ghi rõ vì sao gỡ, nhật ký trên đơn vẫn giữ lại số cũ');
    if (ly === null) return;
    if (!String(ly || '').trim()) return toast('Phải ghi lý do gỡ.', 4000);
    busy(true);
    try {
      var kq = await api('vagabond.ban_hang.go_hoa_don_thay_the', { si_name: siName, ly_do: ly });
      busy(false);
      toast((kq && kq.loi_nhan) || 'Đã gỡ.', 4500);
      dsvVeThayThe(siName);
    } catch (e) { busy(false); baoTin(errMsg(e) || 'Không gỡ được', 'Lỗi'); }
  };
  var cDinh = document.getElementById('ttDinh'), cTep = document.getElementById('ttTep');
  if (cDinh && cTep) {
    cDinh.onclick = function () { cTep.value = ''; cTep.click(); };
    cTep.onchange = function () { dsvTTGui(siName, cTep.files && cTep.files[0]); };
  }
  var oAnh = document.getElementById('ttAnh');
  if (oAnh) {
    oAnh.querySelectorAll('.xo').forEach(function (b) {
      b.onclick = function (ev) {
        ev.stopPropagation();
        dsvTTGo(siName, b.getAttribute('data-go'), b.getAttribute('data-ten'));
      };
    });
    oAnh.querySelectorAll('.ttanh').forEach(function (n) {
      n.onclick = function () { dsvTTMo(siName, n.getAttribute('data-tep'), n.getAttribute('data-ten')); };
    });
  }
  dsvTTNapAnh(siName);
}

/* Nạp hình nhỏ sau khi màn đã vẽ. Mỗi tờ một yêu cầu riêng để tờ nào hỏng
   không kéo đổ tờ khác. Chỉ thay ruột ô CHỜ, không ghi đè cả ô: nút X là
   con của chính ô này. */
async function dsvTTNapAnh(siName) {
  var o = document.getElementById('ttAnh');
  if (!o) return;
  var ds = o.querySelectorAll('.ttanh');
  for (var i = 0; i < ds.length; i++) {
    var n = ds[i];
    var oCho = n.querySelector('.tt');
    if (!oCho) continue;
    if (n.getAttribute('data-anh') !== '1') { oCho.textContent = '📄'; continue; }
    try {
      var r = await api('vagabond.ban_hang.tai_bien_ban_thay_the', { si_name: siName, tep: n.getAttribute('data-tep'), co: 'nho' });
      var anh = document.createElement('img');
      anh.src = 'data:' + r.mime + ';base64,' + r.b64;
      anh.alt = '';
      anh.style.cssText = oCho.style.cssText.replace(/font-size:[^;]*;?/, '')
        + ';object-fit:cover;display:block;border-radius:10px;border:1.5px solid #fcd34d';
      oCho.replaceWith(anh);
    } catch (e) {
      oCho.textContent = '🚫';
    }
  }
}

async function dsvTTMo(siName, tep, ten) {
  toast('Đang tải biên bản...', 2000);
  var r;
  try { r = await api('vagabond.ban_hang.tai_bien_ban_thay_the', { si_name: siName, tep: tep, co: 'lon' }); }
  catch (e) { return toast(errMsg(e) || 'Không tải được tệp', 5000); }
  var url = 'data:' + r.mime + ';base64,' + r.b64;
  if (!String(r.mime || '').indexOf('image/')) {
    var ov = document.createElement('div');
    ov.style.cssText = 'position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,.92);display:flex;align-items:center;justify-content:center;padding:16px';
    ov.innerHTML = '<img src="' + url + '" style="max-width:100%;max-height:88%;border-radius:8px">'
      + '<div style="position:absolute;top:calc(env(safe-area-inset-top,0px) + 12px);right:18px;color:#fff;font-size:32px;line-height:1">&times;</div>';
    ov.onclick = function () { ov.remove(); };
    document.body.appendChild(ov);
    return;
  }
  var a = document.createElement('a');
  a.href = url; a.download = ten || r.ten || 'bien-ban-thay-the';
  document.body.appendChild(a); a.click(); a.remove();
}

async function dsvTTGo(siName, tep, ten) {
  if (!tep) return;
  var ok = await xacNhan(
    'Gỡ "' + (ten || tep) + '" khỏi đơn ' + siName + '?\n\n'
    + 'Tệp vẫn còn trên máy chủ, chỉ bỏ khỏi đơn này. Gỡ xong nhớ đính lại tờ đúng, '
    + 'không thì hồ sơ thay thế thiếu căn cứ.',
    'Gỡ biên bản thay thế', 'Gỡ');
  if (!ok) return;
  busy(true);
  try {
    await api('vagabond.ban_hang.go_bien_ban_thay_the', { si_name: siName, tep: tep });
    busy(false);
    toast('Đã gỡ ' + (ten || tep), 3000);
    dsvVeThayThe(siName);
  } catch (e) { busy(false); baoTin(errMsg(e) || 'Không gỡ được tệp', 'Lỗi'); }
}

function dsvTTGui(siName, file) {
  if (!file) return;
  /* Không nén, không đổi định dạng: biên bản thay thế là chứng từ gốc để
     giải trình thuế, chỉnh một pixel cũng là chỉnh chứng từ. */
  if (file.size > 12 * 1024 * 1024) {
    return toast('Tệp nặng quá 12 MB nên máy không nhận. Vui lòng xuất lại bản PDF nhỏ hơn.', 4500);
  }
  var fr = new FileReader();
  fr.onload = async function () {
    toast('Đang tải biên bản lên...', 2500);
    try {
      var kq = await api('vagabond.ban_hang.dinh_bien_ban_thay_the', {
        si_name: siName, ten: file.name || 'bien-ban-thay-the.pdf', noi_dung: String(fr.result || '')
      });
      toast((kq && kq.ghi_chu) || 'Đã đính biên bản.', 4500);
      dsvVeThayThe(siName);
    } catch (e) { baoTin(errMsg(e) || 'Không đính được biên bản', 'Lỗi'); }
  };
  fr.readAsDataURL(file);
}

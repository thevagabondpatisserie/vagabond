/* ---------- 52. Đối soát nhà cung cấp (v579, #420) ----------
 *
 * Anh Việt 06/10/2026 giao Claude làm trọn đối soát vendor: mười nguồn (Payoo,
 * OnePay, Shinhan POS, ShopeeFood, Xanh SM Ngon, GrabFood, Be, Grab for
 * Business, Xanh SM taxi, thẻ tín dụng Shinhan), tự nhận từ email và tải tay.
 * Bấm nhận thì CHỈ LƯU VÀ ĐỐI CHIẾU: không lập phiếu, không bút toán phí.
 *
 * Bố cục theo maquette anh duyệt 03/10/2026 (docs/doi-soat-vendor/maquette.html):
 * màn 03 trung tâm (việc cần làm, ba nhóm, tìm, ba hàng chip, danh sách, Tải
 * file), màn 04 nhận file (chọn file, xem trước, nhận dòng hợp lệ), màn 02 chi
 * tiết (ba lớp đủ nguồn / tiền về / chứng từ, từng dòng), màn 01 vùng Đối soát
 * trên Chi tiết đơn. Mọi con số do máy chủ đếm (QT-19); màn chỉ hiện.
 *
 * v641 (anh Việt duyệt 8 ảnh 06/11/2026): đối soát tự động qua hộp thư
 * doisoat@. Khối Hộp thư đầu màn, dải Tiến độ sáu bước (1 Nhận thư, 2 Xác thực,
 * 3 Đọc tệp, 4 Khớp tiền, 5 Nối chứng từ, 6 Kế toán xác nhận), chip Đường vào,
 * mỗi nguồn một thanh sáu bước; màn Thư bị chặn / Chưa về / Tải tay chờ duyệt;
 * tải tay phải ghi lý do và chờ giám đốc duyệt; nút Xác nhận chỉ mở khi năm
 * bước trước xanh. Máy chủ quyết mọi bước (doi_soat_thu.buoc_nguon).
 */
var DSVN = { nhom: 'Tiền bán', tt: '', vendor: '', tim: '', ky: '', tu: '', den: '', cur: '', loc: '', xt: null, tep: null,
  ct: '', ctNhan: null, ctNhanTen: {}, xtCt: '', duong: '', buoc: '', thuTab: 'chan', lyDo: '',
  trang: { nguon: { dau: '', so: 0 }, dong: { dau: '', so: 0 }, bill: { dau: '', so: 0 } } };

/* Codex #450: một nguồn đủ quyền có tới 20.000 dòng, danh sách có thể quá
   50 nguồn. Một chỗ giữ trang đang xem cho cả hai màn: bộ lọc đổi (dấu khác)
   thì về trang đầu, không nhớ trang cũ của bộ lọc khác. */
/* v651: dòng lỗi kèm chữ máy đọc được từ tệp, để kế toán so với PDF.
   Codex PR #554: lỗi ghép mảnh mang nhiều mảnh (tiền tố "GD-", dòng tiền, đuôi
   mã); hiện ĐỦ các mảnh máy giữ (tối đa 3), không chỉ mảnh đầu. */
function dsvDongLoi(d) {
  var tho = (d.tho || []).map(function (x) { return String(x || '').replace(/\s+/g, ' ').trim(); })
    .filter(Boolean).join(' | ');
  if (tho.length > 240) tho = tho.slice(0, 237) + '...';
  return 'Dòng ' + d.vi_tri + ': ' + d.ly_do + (tho ? ' Máy đọc được: "' + tho + '"' : '');
}

function dsvnTrang(loai, dau) {
  var t = DSVN.trang[loai];
  if (t.dau !== dau) { t.dau = dau; t.so = 0; }
  return t.so;
}
function dsvnPhanTrang(loai, so, con, coMoiTrang, donVi) {
  if (!so && !con) return '';
  var nut = function (buoc, chu) {
    return '<button class="btn gh" data-dsvntrang="' + loai + ':' + buoc + '" style="margin:0;min-height:44px;padding:0 14px">' + chu + '</button>';
  };
  return '<div style="display:flex;justify-content:center;align-items:center;gap:8px;margin:10px 0">' +
    (so > 0 ? nut(-1, '‹ Trang trước') : '') +
    '<span style="font-size:13px;color:#667085">' + donVi + ' ' + money(so * coMoiTrang + 1) + ' đến ' + money(so * coMoiTrang + coMoiTrang) + '</span>' +
    (con ? nut(1, 'Trang sau ›') : '') + '</div>';
}
function dsvnBamTrang(e, man) {
  var x = e.target.closest('[data-dsvntrang]');
  if (!x) return false;
  var p = x.getAttribute('data-dsvntrang').split(':');
  DSVN.trang[p[0]].so = Math.max(0, DSVN.trang[p[0]].so + Number(p[1]));
  go(man, true);
  return true;
}
var DSVN_NHOM = [['Tiền bán', '💰'], ['Chuyến đi', '🛵'], ['Thẻ tín dụng', '💳']];

function dsvnChip(tt) {
  var mau = {
    'Đã nhận': ['#ecfdf3', '#067647'], 'Cần xử lý': ['#fffaeb', '#b54708'], 'Lỗi tệp': ['#fef3f2', '#b42318'],
    'Đã thấy tiền về': ['#ecfdf3', '#067647'], 'Lệch tiền về': ['#fef3f2', '#b42318'],
    'Chưa thấy tiền về': ['#fffaeb', '#b54708'], 'Cần chọn tiền về': ['#fffaeb', '#b54708'], 'Không áp dụng': ['#f2f4f7', '#475467'],
    'Chưa đối chiếu': ['#f2f4f7', '#475467'], 'Đã nối': ['#ecfdf3', '#067647'],
    'Nối theo tiền': ['#eff8ff', '#175cd3'], 'Lệch tiền': ['#fef3f2', '#b42318'],
    'Nhiều chứng từ': ['#fffaeb', '#b54708'], 'Không thấy chứng từ': ['#fffaeb', '#b54708'],
    'Chưa nối': ['#f2f4f7', '#475467'], 'Đã thay': ['#f2f4f7', '#475467'],
    'Khớp': ['#ecfdf3', '#067647'], 'Sai mã': ['#fef3f2', '#b42318'], 'Không có trên báo cáo': ['#fef3f2', '#b42318'],
    'Chờ kế toán chọn': ['#fffaeb', '#b54708'], 'Chờ báo cáo': ['#f2f4f7', '#475467']
  }[tt] || ['#f2f4f7', '#475467'];
  return '<span style="display:inline-block;background:' + mau[0] + ';color:' + mau[1] +
    ';border-radius:999px;padding:3px 9px;font-size:12px;font-weight:600;white-space:nowrap">' + h(tt) + '</span>';
}

function dsvnKy(n) {
  var a = n.tu_ngay ? dmy(n.tu_ngay).slice(0, 5) : '', b = n.den_ngay ? dmy(n.den_ngay).slice(0, 5) : '';
  return a && b && a !== b ? a + ' - ' + b : (a || b || 'chưa rõ kỳ');
}

/* Loại dòng hiện bằng tiếng Việt, không lộ mã lưu (phi_ky, dieu_chinh...). */
var DSVN_LOAI = { ban: 'Bán', hoan: 'Hoàn tiền', dieu_chinh: 'Điều chỉnh', phi_ky: 'Phí trong kỳ', phi: 'Phí',
  lai: 'Lãi thẻ', phat_sinh: 'Chi tiêu thẻ', phi_quan_ly: 'Phí quản lý' };
function dsvnLoai(k) { return DSVN_LOAI[k] || 'Dòng khác'; }

function dsvnNhan(nhom) {
  return nhom === 'Tiền bán' ? 'thực nhận' : 'phải trả';
}

/* v641: sáu bước. Mã bước (x, v, d, n) chỉ là giá trị máy chủ gửi; người dùng
   chỉ thấy chấm màu và một dòng chữ. Xanh xong, vàng đang chờ, đỏ có sự cố,
   xám chưa tới. */
var DSVN_BUOC = ['Nhận thư', 'Xác thực', 'Đọc tệp', 'Khớp tiền', 'Nối chứng từ', 'Kế toán xác nhận'];
var DSVN_MAU_BUOC = { x: ['#12a150', '#fff'], v: ['#f5b40b', '#fff'], d: ['#d93a2b', '#fff'], n: ['#edf0f5', '#8994a4'] };
function dsvnThanhBuoc(tt, ghi) {
  tt = String(tt || '');
  var s = '<div style="display:flex;align-items:center;margin-top:7px" aria-label="Tiến độ: ' + h(ghi || '') + '">';
  for (var i = 0; i < 6; i++) {
    var c = tt.charAt(i) || 'n', m = DSVN_MAU_BUOC[c] || DSVN_MAU_BUOC.n;
    if (i) s += '<span style="flex:1;max-width:12px;height:2px;background:#d6dbe3"></span>';
    s += '<span title="' + h(DSVN_BUOC[i]) + '" style="flex:none;width:22px;height:22px;border-radius:50%;display:inline-grid;place-items:center;' +
      'font-size:11px;font-weight:700;background:' + m[0] + ';color:' + m[1] + '">' + (c === 'x' ? '✓' : c === 'd' ? '!' : (i + 1)) + '</span>';
  }
  return s + '<span style="margin-left:8px;font-size:12.5px;color:#475467;font-weight:600">' + h(ghi || '') + '</span></div>';
}
var DSVN_DUONG = [['thu', 'Từ thư ✓'], ['cho_duyet', 'Chờ duyệt'], ['da_duyet', 'Tải tay đã duyệt'], ['tu_choi', 'Bị từ chối'], ['cu', 'Trước khi có thư']];
function dsvnDuongChip(k) {
  var x = { thu: ['Từ thư ✓', '#ecfdf3', '#067647'], cho_duyet: ['Chờ giám đốc duyệt', '#fffaeb', '#b54708'],
    da_duyet: ['Tải tay, giám đốc đã duyệt', '#eff8ff', '#175cd3'], tu_choi: ['Giám đốc từ chối', '#fef3f2', '#b42318'],
    cu: ['Tải tay trước khi có thư', '#f2f4f7', '#475467'] }[k];
  if (!x) return '';
  return '<span style="display:inline-block;background:' + x[1] + ';color:' + x[2] +
    ';border-radius:999px;padding:3px 9px;font-size:12px;font-weight:600;white-space:nowrap">' + h(x[0]) + '</span>';
}

/* Khối Hộp thư đối soát đầu màn chính. */
function dsvnKhoiHop(ht) {
  if (!ht) return '';
  var trang = { chay: ['Đang chạy', '#ecfdf3', '#067647'], tat: ['Đang tắt', '#fffaeb', '#b54708'],
    loi: ['Lỗi đọc thư', '#fef3f2', '#b42318'], chua: ['Chưa đọc lần nào', '#f2f4f7', '#475467'] }[ht.trang] || ['', '#f2f4f7', '#475467'];
  var o = function (tab, nhan, so, mau) {
    return '<div data-dsvnthu="' + tab + '" style="background:#f9fafb;border-radius:12px;padding:10px 12px;cursor:pointer;min-height:44px">' +
      '<div style="font-size:12.5px;color:#667085">' + h(nhan) + '</div><div style="font-size:20px;font-weight:800;color:' + (so ? mau : '#101828') + '">' +
      money(so || 0) + '</div></div>';
  };
  var dong = ht.trang === 'tat' ? 'Máy chưa đọc hộp thư. Quản trị bật ở Cài đặt lõi, mục Hộp thư đối soát.' :
    ht.trang === 'loi' ? 'Không đọc được hộp thư: ' + (ht.loi || '') :
    (ht.doc_luc ? 'Đọc lần cuối ' + h(String(ht.doc_luc).slice(11, 16)) + ' ' + dmy(String(ht.doc_luc).slice(0, 10)).slice(0, 5) + ' · tự đọc mỗi 15 phút' :
      'Chưa đọc lần nào.');
  return '<div class="card" style="padding:13px 14px;border:1.5px solid #68d5e7">' +
    '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px"><b style="font-size:16px">Hộp thư ' +
    h(ht.dia_chi || 'doisoat@') + '</b><span style="background:' + trang[1] + ';color:' + trang[2] +
    ';border-radius:999px;padding:3px 9px;font-size:12px;font-weight:600;white-space:nowrap">' + h(trang[0]) + '</span></div>' +
    '<div style="font-size:13px;color:' + (ht.trang === 'loi' ? '#b42318' : '#667085') + ';margin-top:4px">' + h(dong) + '</div>' +
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px">' +
    o('ve', 'Thư về hôm nay', ht.ve_hom_nay, '#067647') + o('chua_ve', 'Thư chưa về', ht.chua_ve, '#b42318') +
    o('chan', 'Thư bị chặn (7 ngày)', ht.bi_chan, '#b42318') + o('tai_tay', 'Chờ giám đốc duyệt', ht.cho_duyet, '#b54708') + '</div>' +
    (ht.quan_tri ? '<button class="btn gh" id="dsvnThuKetNoi" style="margin:8px 0 0;min-height:44px">Thử kết nối hộp thư</button>' : '') + '</div>';
}

/* Dải Tiến độ: số nguồn đang kẹt ở từng bước. Bước 1, 2 mở màn Thư; bước
   3 tới 6 lọc danh sách (bấm lại để bỏ lọc). */
function dsvnDaiTienDo(ht, dem) {
  dem = dem || {};
  var so = [ht ? ht.chua_ve || 0 : 0, ht ? ht.cho_duyet || 0 : 0, dem[3] || 0, dem[4] || 0, dem[5] || 0, dem[6] || 0];
  var ten = ['Thư chưa về', 'Chờ duyệt', 'Tệp lỗi', 'Lệch tiền', 'Thiếu chứng từ', 'Chờ xác nhận'];
  return '<div class="card" style="padding:11px 12px"><div style="font-size:12px;color:#98a2b3">TIẾN ĐỘ · BẤM MỘT BƯỚC ĐỂ XEM</div>' +
    '<div style="display:flex;gap:6px;margin-top:8px">' + so.map(function (n, i) {
      var mau = !n ? DSVN_MAU_BUOC.x : (i < 4 ? DSVN_MAU_BUOC.d : DSVN_MAU_BUOC.v);
      var chon = String(DSVN.buoc) === String(i + 1);
      return '<div data-dsvnbuoc="' + (i + 1) + '" style="flex:1;min-width:0;background:' + (chon ? '#e1f8fc' : '#f5f7fa') +
        ';border-radius:10px;padding:7px 2px;text-align:center;cursor:pointer;min-height:44px;' + (chon ? 'outline:2px solid #08788e;' : '') + '">' +
        '<span style="display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;font-size:11px;font-weight:700;background:' +
        mau[0] + ';color:' + mau[1] + '">' + (n ? (i + 1) : '✓') + '</span>' +
        '<div style="font-size:17px;font-weight:800">' + money(n) + '</div><div style="font-size:10.5px;color:#647080;line-height:1.2">' + ten[i] + '</div></div>';
    }).join('') + '</div>' +
    (DSVN.buoc ? '<div style="font-size:12.5px;color:#08788e;margin-top:6px">Đang xem nguồn kẹt ở bước ' + h(DSVN.buoc) + ': ' +
      h(DSVN_BUOC[+DSVN.buoc - 1] || '') + '. Bấm lại ô đó để bỏ lọc.</div>' : '') + '</div>';
}

/* ---------- Màn 03: trung tâm Đối soát ---------- */
async function scrDsvn() {
  frame('Đối soát nhà cung cấp', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc nguồn đối soát...</div></div>');
  var kq, sk = [];
  try {
    var locDs = { nhom: DSVN.nhom, trang_thai: DSVN.tt, vendor: DSVN.vendor, tim: DSVN.tim, ky: DSVN.ky, tu: DSVN.tu, den: DSVN.den,
      duong: DSVN.duong, buoc: DSVN.buoc };
    locDs.trang = dsvnTrang('nguon', JSON.stringify(locDs));
    kq = await api('vagabond.doi_soat_vendor.ds', locDs);
    /* Codex #450 vòng 16: các pháp nhân được nhận tệp, màn Tải file dùng. */
    DSVN.ctNhan = kq.cong_ty_nhan || [];
    DSVN.ctNhanTen = kq.nhan_cong_ty || {};
    sk = await api('vagabond.doi_soat_vendor.suc_khoe', {});
  } catch (e) {
    frame('Đối soát nhà cung cấp', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được đối soát. Thử lại sau ít phút.') + '</div></div>');
    return;
  }
  /* v641: khối hộp thư đọc riêng; hỏng thì màn vẫn mở, chỉ thiếu khối này. */
  var ht = null;
  try { ht = await api('vagabond.doi_soat_vendor.hop_thu', {}); } catch (e) { ht = null; }
  DSVN.ht = ht;
  var dem = kq.dem || {};
  var html = dsvnKhoiHop(ht) + dsvnDaiTienDo(ht, kq.dem_buoc) + '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">VIỆC CẦN LÀM</div>' +
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px">' +
    dsvnO('Cần xử lý', dem['Cần xử lý'] || 0, 'nguồn', '#b42318') +
    /* Codex #450: số trên thẻ và bộ lọc khi bấm cùng một khoá gộp (máy chủ đếm
       và lọc đủ ba trạng thái chờ), không cộng ở máy khách rồi lọc một. */
    dsvnO('Chờ tiền về', dem['Chờ tiền về'] || 0, 'đợt', '#b54708') +
    dsvnO('Chưa nối đủ', dem['Chưa nối đủ'] || 0, 'nguồn', '#b54708') +
    dsvnO('', dem.tat_ca || 0, 'nguồn đã nhận', '#101828') +
    /* v647 (anh Việt 10/11/2026): chiều ngược, từng bill thu ngân chọn thẻ/sàn
       đối chiếu với báo cáo đối tác. Số nạp sau, hỏng thì màn vẫn mở. */
    '<div data-dsvnbill="1" style="grid-column:1 / -1;background:#fef3f2;border-radius:12px;padding:10px 12px;cursor:pointer;min-height:44px">' +
      '<div style="font-size:12.5px;color:#667085">Bill chưa khớp đối tác (14 ngày)</div>' +
      '<div style="font-size:20px;font-weight:800;color:#b42318"><span id="dsvnBillSo">…</span> <span style="font-size:13px;font-weight:500;color:#667085">bill</span></div></div>' +
    '</div>' +
    /* Codex #450: tổng thực nhận trong nhóm/nguồn đang chọn; đang lọc trạng
       thái thì thêm thanh "Tổng theo bộ lọc" (máy chủ tính cùng bộ lọc). */
    '<div style="display:flex;justify-content:space-between;gap:8px;margin-top:8px;font-size:13px;color:#475467">' +
      '<span>Tổng thực nhận</span><b style="color:#101828">' + money((kq.tong || {}).tat_ca || 0) + ' đ</b></div>' +
    ((kq.tong || {}).theo_loc != null ? '<div style="display:flex;justify-content:space-between;gap:8px;margin-top:4px;' +
      'padding:6px 8px;border-radius:8px;background:#fffaeb;font-size:13px"><span>Tổng theo bộ lọc</span><b>' +
      money(kq.tong.theo_loc) + ' đ</b></div>' : '') +
    dsvnSucKhoe(sk) + '</div>';
  html += '<div class="chips" style="padding:0 2px">' + DSVN_NHOM.map(function (n) {
    return '<div class="chip' + (DSVN.nhom === n[0] ? ' on' : '') + '" data-dsvnnhom="' + h(n[0]) + '">' + n[1] + ' ' + h(n[0]) +
      ' ' + (dem['nhom:' + n[0]] || 0) + '</div>';
  }).join('') + '</div>';
  /* Thanh công cụ danh sách dùng chung (v534): chip trạng thái, chip nguồn,
     chip ngày theo cuối kỳ báo cáo, ô tìm. */
  var cc = dsvnCongCu(kq);
  html += dsCongCu(cc);
  var hang = kq.hang || [];
  if (!hang.length) {
    html += '<div class="emp"><div class="e1">📭</div><div>Chưa có nguồn đối soát trong bộ lọc này. Nhận từ email hoặc bấm Tải file.</div></div>';
  } else {
    html += '<div class="card" style="padding:0">' + hang.map(function (n) {
      return '<div class="shi" data-dsvnct="' + h(n.name) + '" style="padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer;min-height:44px">' +
        '<div style="display:flex;justify-content:space-between;gap:8px;align-items:center"><b>' + h(n.vendor) +
        '</b><span>' + dsvnChip(n.trang_thai) + '</span></div>' +
        '<div style="font-size:13px;color:#667085;margin-top:3px">' + h(n.ten_mau || '') + ' · ' + dsvnKy(n) +
        ' · ' + money(n.so_dong) + ' dòng</div>' + dsvnThanhBuoc(n.buoc, n.buoc_ghi) +
        '<div style="display:flex;justify-content:space-between;gap:8px;align-items:center;margin-top:6px">' +
        '<span style="font-size:13px">' + money(n.thuc_nhan) + ' đ ' + dsvnNhan(n.nhom) + '</span>' +
        '<span style="display:flex;gap:4px;flex-wrap:wrap;justify-content:flex-end">' +
        (n.nhom === 'Tiền bán' ? dsvnChip(n.trang_thai_tien || 'Chưa đối chiếu') : '') +
        (n.so_chua_noi ? dsvnChip(n.so_chua_noi + ' chưa nối') : '') + '</span></div>' +
        '<div style="margin-top:6px">' + dsvnDuongChip(n.duong) + (n.xac_nhan_luc ? ' ' + dsvnChip('Đã khép') : '') + '</div></div>';
    }).join('') + '</div>';
  }
  html += dsvnPhanTrang('nguon', DSVN.trang.nguon.so, kq.con, 50, 'Nguồn');
  var foot = '<div style="display:flex;gap:8px"><button class="btn" id="dsvnDocThu" style="margin:0;flex:1">Đọc hộp thư ngay</button>' +
    '<button class="btn gh" id="dsvnTai" style="margin:0;flex:1">↑ Tải file (cần duyệt)</button></div>';
  var b = frame('Đối soát nhà cung cấp', html, { footer: foot });
  dsCongCuNoi(b, cc, function (ho, k) {
    if (ho === 'tt') DSVN.tt = k;
    else if (ho === 'ven') DSVN.vendor = k;
    else if (ho === 'ky') DSVN.ky = k;
    else if (ho === 'tim') DSVN.tim = k;
    else if (ho === 'tu') DSVN.tu = k;
    else if (ho === 'den') DSVN.den = k;
    else if (ho === 'duong') DSVN.duong = k;
    go(scrDsvn, true);
  });
  b.addEventListener('click', function (e) {
    if (dsvnBamTrang(e, scrDsvn)) return;
    var t = e.target.closest('[data-dsvnnhom]');
    if (t) { DSVN.nhom = t.getAttribute('data-dsvnnhom'); DSVN.vendor = ''; return go(scrDsvn, true); }
    t = e.target.closest('[data-dsvntt]');
    if (t) { DSVN.tt = t.getAttribute('data-dsvntt'); return go(scrDsvn, true); }
    t = e.target.closest('[data-dsvnct]');
    if (t) { DSVN.cur = t.getAttribute('data-dsvnct'); DSVN.loc = ''; return go(scrDsvnCt); }
    if (e.target.closest('[data-dsvnbill]')) { DSVN.bill = { tt: '', diem: '', kieu: '', ky: '', tu: '', den: '', tim: '' }; return go(scrDsvnBill); }
    t = e.target.closest('[data-dsvnthu]');
    if (t) {
      var tab = t.getAttribute('data-dsvnthu');
      /* Ô "Thư về hôm nay" lọc chip Đường vào = Từ thư; ba ô kia mở màn Thư. */
      if (tab === 've') { DSVN.duong = 'thu'; DSVN.buoc = ''; return go(scrDsvn, true); }
      DSVN.thuTab = tab; return go(scrDsvnThu);
    }
    t = e.target.closest('[data-dsvnbuoc]');
    if (t) {
      var k = t.getAttribute('data-dsvnbuoc');
      if (k === '1') { DSVN.thuTab = 'chua_ve'; return go(scrDsvnThu); }
      if (k === '2') { DSVN.thuTab = 'tai_tay'; return go(scrDsvnThu); }
      DSVN.buoc = DSVN.buoc === k ? '' : k;
      return go(scrDsvn, true);
    }
  });
  document.getElementById('dsvnTai').onclick = function () { DSVN.xt = null; DSVN.tep = null; DSVN.lyDo = ''; go(scrDsvnTai); };
  dsvnNapSoBill();
  document.getElementById('dsvnDocThu').onclick = async function () {
    busy(true);
    try {
      var r = await api('vagabond.doi_soat_vendor.doc_hop_thu_ngay', {});
      if (r.loi) baoTin('Chưa đọc được hộp thư: ' + r.loi);
      else toast(r.dang_chay ? 'Máy đang đọc hộp thư ở lượt khác, đợi ít phút rồi tải lại.' :
        (r.so_thu ? 'Đã đọc ' + r.so_thu + ' thư mới.' : 'Không có thư mới.'));
      go(scrDsvn, true);
    } catch (e) { baoTin((e && e.message) || 'Chưa đọc được hộp thư. Thử lại sau ít phút.'); }
    finally { busy(false); }
  };
  var tk = document.getElementById('dsvnThuKetNoi');
  if (tk) tk.onclick = async function () {
    busy(true);
    try {
      var r = await api('vagabond.doi_soat_vendor.thu_ket_noi', {});
      if (r.ok) toast('Kết nối được. Thư mục đang có ' + money(r.so_thu || 0) + ' thư.');
      else baoTin('Chưa kết nối được: ' + (r.loi || ''));
    } catch (e) { baoTin((e && e.message) || 'Chưa thử được kết nối.'); }
    finally { busy(false); }
  };
}

/* ---------- v647: bill thu ngân chọn thẻ/sàn -> báo cáo đối tác ---------- */
async function dsvnNapSoBill() {
  var o = document.getElementById('dsvnBillSo');
  if (!o) return;
  try {
    var r = await api('vagabond.doi_soat_vendor.bill_doi_tac', { chi_dem: 1 });
    o.textContent = money(r.can_xu_ly || 0);
  } catch (e) { o.textContent = '?'; }
}

var DSVN_BILL_TT = [
  ['', 'Cần xử lý', 'Ba loại dưới đây gộp lại: bill cần điểm bán hoặc kế toán sửa.'],
  ['Không có trên báo cáo', 'Không có trên báo cáo', 'Báo cáo đối tác của ngày đó đã về mà không có giao dịch nào của bill: thường là chọn nhầm phương thức hoặc nhập sai mã.'],
  ['Sai mã', 'Sai mã', 'Đối tác có giao dịch cùng tiền nhưng mã khác mã trên bill: sửa mã chuẩn chi trên bill cho đúng.'],
  ['Lệch tiền', 'Lệch tiền', 'Cùng mã nhưng số tiền bill khác số đối tác ghi: kiểm lại tiền thu.'],
  ['Chờ kế toán chọn', 'Chờ kế toán chọn', 'Báo cáo có giao dịch trùng mã hoặc trùng tiền, kế toán chọn bill đúng ở màn báo cáo.'],
  ['Chờ báo cáo', 'Chờ báo cáo', 'Báo cáo đối tác của ngày đó chưa về đủ, máy chưa kết luận.'],
  ['Khớp', 'Khớp', 'Bill đã có giao dịch đúng mã, đúng tiền trên báo cáo đối tác.']
];

function dsvnChipBill(ho, k, ten, so, chon) {
  return '<div class="chip' + (chon === k ? ' on' : '') + '" data-dsvnbchip="' + ho + '|' + h(k) + '" style="min-height:44px">' +
    h(ten) + (so != null ? ' ' + money(so) : '') + '</div>';
}

async function scrDsvnBill() {
  var L = DSVN.bill || (DSVN.bill = { tt: '', diem: '', kieu: '', ky: '', tu: '', den: '', tim: '' });
  frame('Bill chưa khớp đối tác', '<div class="emp"><div class="e1">⏳</div><div>Đang đối chiếu bill với báo cáo đối tác...</div></div>');
  var kq;
  /* Codex #550: chip ngày, ô tìm (mã bill hoặc mã chuẩn chi) và trang sau đều
     hỏi máy chủ; đổi bộ lọc thì về trang đầu. */
  var loc = { trang_thai: L.tt, diem: L.diem, kieu: L.kieu, ky: L.ky, tu: L.tu, den: L.den, tim: L.tim };
  loc.trang = dsvnTrang('bill', JSON.stringify(loc));
  try {
    kq = await api('vagabond.doi_soat_vendor.bill_doi_tac', loc);
  } catch (e) {
    frame('Bill chưa khớp đối tác', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được. Thử lại sau ít phút.') + '</div></div>');
    return;
  }
  var dem = kq.dem || {}, tenDiem = kq.ten_diem || {}, tenKieu = kq.ten_kieu || {};
  var chuThich = (DSVN_BILL_TT.filter(function (x) { return x[0] === L.tt; })[0] || DSVN_BILL_TT[0])[2];
  var html = '<div class="card" style="padding:12px 14px;font-size:13.5px;color:#475467">Từng bill thu ngân chọn Shinhan POS, Payoo, ' +
    'GrabFood, ShopeeFood, Xanh SM Ngon từ ' + h(dsvnNgay(kq.tu)) + ' đến ' + h(dsvnNgay(kq.den)) +
    ' được dò trong báo cáo đối tác gửi về cho đúng ngày đó, theo mã chuẩn chi hoặc mã đơn và số tiền.' +
    (L.ky ? '' : ' Mọi ngày là 14 ngày gần nhất, tới hôm qua.') +
    (kq.cat ? ' Khoảng chọn dài quá 92 ngày nên máy chỉ xét 92 ngày cuối.' : '') + '</div>';
  var cc = { ma: 'dsvnb', ho: [], ky: { chon: L.ky, tu: L.tu, den: L.den }, tim: { gt: L.tim, goiY: 'Tìm mã bill hoặc mã chuẩn chi...' } };
  html += dsCongCu(cc);
  html += '<div class="chips" style="padding:0 2px">' + DSVN_BILL_TT.map(function (x) {
    return dsvnChipBill('tt', x[0], x[1], x[0] ? (dem[x[0]] || 0) : kq.can_xu_ly, L.tt);
  }).join('') + '</div>';
  html += '<div style="font-size:12.5px;color:#667085;padding:0 4px 6px">' + h(chuThich) + '</div>';
  var diemDs = Object.keys(kq.dem_diem || {}).sort();
  if (diemDs.length > 1 || L.diem) {
    html += '<div class="chips" style="padding:0 2px">' + dsvnChipBill('diem', '', 'Mọi điểm bán', null, L.diem) + diemDs.map(function (d) {
      return dsvnChipBill('diem', d, tenDiem[d] || d || 'Chưa rõ điểm', kq.dem_diem[d], L.diem);
    }).join('') + '</div>';
  }
  var kieuDs = Object.keys(kq.dem_kieu || {}).sort();
  if (kieuDs.length > 1 || L.kieu) {
    html += '<div class="chips" style="padding:0 2px">' + dsvnChipBill('kieu', '', 'Mọi đối tác', null, L.kieu) + kieuDs.map(function (k) {
      return dsvnChipBill('kieu', k, tenKieu[k] || k, kq.dem_kieu[k], L.kieu);
    }).join('') + '</div>';
  }
  var hang = kq.hang || [];
  if (!hang.length) {
    html += '<div class="emp"><div class="e1">✅</div><div>Không có bill nào trong mục này.</div></div>';
  } else {
    var ngay = '';
    html += '<div class="card" style="padding:0">' + hang.map(function (x) {
      var dau = '';
      if (x.ngay !== ngay) {
        ngay = x.ngay;
        dau = '<div style="padding:8px 14px;background:#f9fafb;font-size:12.5px;color:#667085;font-weight:600">' + h(dsvnNgay(x.ngay)) + '</div>';
      }
      return dau + '<div class="shi" data-dsvnbill-si="' + h(x.name) + '" style="padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer;min-height:44px">' +
        '<div style="display:flex;justify-content:space-between;gap:8px;align-items:center"><b>' + h(x.name) + '</b>' +
        dsvnChip(x.trang_thai) + '</div>' +
        '<div style="font-size:13px;color:#667085;margin-top:3px">' + h(tenDiem[x.diem] || x.diem || 'Chưa rõ điểm') + ' · ' +
        h(tenKieu[x.kieu] || x.kieu) + ' · ' + money(x.tien) + ' đ' +
        ((x.ma || []).filter(Boolean).length ? ' · mã ' + h(x.ma.filter(Boolean).join(', ')) : '') + '</div>' +
        (x.ghi_chu ? '<div style="font-size:12.5px;color:#475467;margin-top:4px">' + h(x.ghi_chu) + '</div>' : '') + '</div>';
    }).join('') + '</div>';
  }
  html += dsvnPhanTrang('bill', DSVN.trang.bill.so, kq.con, kq.moi_trang || 200, 'Bill');
  var b = frame('Bill chưa khớp đối tác', html);
  dsCongCuNoi(b, cc, function (ho, k) {
    if (ho === 'ky') L.ky = k;
    else if (ho === 'tu') L.tu = k;
    else if (ho === 'den') L.den = k;
    else if (ho === 'tim') L.tim = k;
    go(scrDsvnBill, true);
  });
  b.addEventListener('click', function (e) {
    if (dsvnBamTrang(e, scrDsvnBill)) return;
    var t = e.target.closest('[data-dsvnbchip]');
    if (t) {
      var v = t.getAttribute('data-dsvnbchip'), i = v.indexOf('|');
      L[v.slice(0, i)] = v.slice(i + 1);
      return go(scrDsvnBill, true);
    }
    t = e.target.closest('[data-dsvnbill-si]');
    if (t) {
      var ten = t.getAttribute('data-dsvnbill-si');
      return go(function () { scrDsView(ten, 0); });
    }
  });
}

function dsvnNgay(d) {
  d = String(d || '');
  return d.length >= 10 ? d.slice(8, 10) + '/' + d.slice(5, 7) + '/' + d.slice(0, 4) : d;
}

function dsvnCongCu(kq) {
  var dem = kq.dem || {};
  return {
    ma: 'dsvn',
    ho: [
      { k: 'tt', tatCa: 'Mọi trạng thái', chon: DSVN.tt, dem: dem, mau: '#b42318',
        ds: [{ k: 'Cần xử lý', ten: 'Cần xử lý' }, { k: 'Chờ tiền về', ten: 'Chờ tiền về' }, { k: 'Chưa thấy tiền về', ten: 'Chưa thấy tiền' },
          { k: 'Lệch tiền về', ten: 'Lệch tiền về' }, { k: 'Cần chọn tiền về', ten: 'Trùng số tiền' }, { k: 'Chưa nối đủ', ten: 'Chưa nối đủ' },
          { k: 'Đã khép', ten: 'Đã khép' }] },
      /* v641: đường vào của nguồn (thư có chữ ký hay tải tay). */
      { k: 'duong', tatCa: 'Mọi đường vào', chon: DSVN.duong, dem: kq.dem_duong || {}, mau: '#175cd3',
        ds: DSVN_DUONG.map(function (d) { return { k: d[0], ten: d[1] }; }) },
      { k: 'ven', tatCa: 'Mọi nguồn', chon: DSVN.vendor, dem: kq.dem_vendor || {}, mau: '#0d9488',
        ds: (kq.vendor || []).map(function (v) { return { k: v, ten: v.length > 16 ? v.slice(0, 15) + '…' : v }; }) }
    ],
    ky: { chon: DSVN.ky, tu: DSVN.tu, den: DSVN.den },
    tim: { gt: DSVN.tim, goiY: 'Tìm nguồn, tên tệp, mã nguồn...' }
  };
}

function dsvnO(nhan, so, don_vi, mau) {
  var dat = nhan ? ' data-dsvntt="' + h(nhan) + '"' : ' data-dsvntt=""';
  return '<div' + dat + ' style="background:#f9fafb;border-radius:12px;padding:10px 12px;cursor:pointer;min-height:44px">' +
    '<div style="font-size:12.5px;color:#667085">' + h(nhan || 'Tất cả') + '</div>' +
    '<div style="font-size:20px;font-weight:800;color:' + mau + '">' + money(so) + ' <span style="font-size:13px;font-weight:500;color:#667085">' + h(don_vi) + '</span></div></div>';
}

/* Sức khoẻ nguồn: chỉ một dòng đếm; bấm mới mở danh sách (điều 17). */
function dsvnSucKhoe(sk) {
  var co = (sk || []).filter(function (x) { return x.so_nguon; }).length;
  var chua = (sk || []).filter(function (x) { return !x.so_nguon; });
  return '<details style="margin-top:10px"><summary style="font-size:13px;color:#475467;cursor:pointer;min-height:24px">' +
    '✓ ' + co + '/' + (sk || []).length + ' nguồn đã từng nhận' + (chua.length ? ' · ' + chua.length + ' nguồn chưa có tệp nào' : '') +
    '</summary><div style="margin-top:6px">' + (sk || []).map(function (x) {
      return '<div style="display:flex;justify-content:space-between;gap:8px;font-size:13px;padding:5px 0;border-bottom:1px solid #f2f4f7">' +
        '<span>' + h(x.vendor) + '</span><span style="color:#667085">' +
        (x.so_nguon ? 'kỳ mới nhất ' + (x.ky_moi ? dmy(x.ky_moi).slice(0, 5) : 'chưa rõ') +
          (x.can_xu_ly ? ' · ' + x.can_xu_ly + ' cần xử lý' : '') + (x.chua_tien ? ' · ' + x.chua_tien + ' chờ tiền' : '')
          : 'Chưa có') + '</span></div>';
    }).join('') + '</div></details>';
}

/* ---------- v641 màn 05: thư bị chặn, thư chưa về, chờ giám đốc duyệt ---------- */
var DSVN_THU_TAB = [['chan', 'Bị chặn', 'bi_chan'], ['chua_ve', 'Chưa về', 'chua_ve'], ['tai_tay', 'Chờ duyệt', 'cho_duyet']];
async function scrDsvnThu() {
  frame('Hộp thư đối soát', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc...</div></div>');
  var kq, ht = DSVN.ht || {};
  try {
    kq = await api('vagabond.doi_soat_vendor.ds_thu', { loai: DSVN.thuTab });
    try { ht = await api('vagabond.doi_soat_vendor.hop_thu', {}); DSVN.ht = ht; } catch (e) { ht = DSVN.ht || {}; }
  } catch (e) {
    frame('Hộp thư đối soát', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không mở được. Thử lại.') + '</div></div>');
    return;
  }
  var html = '<div style="display:flex;gap:6px;margin:0 0 10px">' + DSVN_THU_TAB.map(function (t) {
    var chon = DSVN.thuTab === t[0];
    return '<div data-dsvntab="' + t[0] + '" style="flex:1;text-align:center;border-radius:10px;padding:10px 6px;font-size:13px;font-weight:650;cursor:pointer;min-height:44px;' +
      (chon ? 'background:#05323c;color:#fff' : 'background:#fff') + '">' + t[1] + ' ' + money(ht[t[2]] || 0) + '</div>';
  }).join('') + '</div>';
  var ds = kq.ds || [];
  if (!ds.length) {
    html += '<div class="emp"><div class="e1">✓</div><div>' + ({ chan: 'Không có thư bị chặn trong 30 ngày.',
      chua_ve: 'Thư dự kiến đã về đủ.', tai_tay: 'Không có tệp nào chờ giám đốc duyệt.' }[DSVN.thuTab] || '') + '</div></div>';
  } else if (DSVN.thuTab === 'chan') {
    html += ds.map(function (x) {
      return '<div class="card" style="padding:12px 14px"><div style="display:flex;justify-content:space-between;gap:8px;align-items:center"><b>' +
        h(x.doi_tac ? 'Thư tự xưng ' + x.doi_tac : 'Thư từ ' + (x.ten_mien || 'người gửi lạ')) + '</b>' + dsvnChip(x.ket_qua || 'Bị chặn') + '</div>' +
        '<div style="font-size:13px;color:#667085;margin-top:3px">Người gửi ghi: ' + h(x.nguoi_gui || '') + ' · ' +
        h(String(x.nhan_luc || '').slice(11, 16)) + ' ' + dmy(String(x.nhan_luc || '').slice(0, 10)).slice(0, 5) + '</div>' +
        dsvnThanhBuoc('xd', x.ly_do) +
        '<div style="font-size:13px;margin-top:6px">' + h(x.tieu_de || '') + (x.so_tep ? ' · ' + money(x.so_tep) + ' tệp kèm' : '') + '</div>' +
        (x.ket_qua === 'Lỗi xử lý' ?
          '<div style="font-size:12.5px;color:#7a2e0e;background:#fffaeb;border-radius:10px;padding:8px 10px;margin-top:6px">Máy chưa đọc xong thư này nên chưa nhận số liệu. Bấm Đọc lại thư để thử lần nữa; máy vẫn kiểm chữ ký số như thư mới.</div>' +
          '<button class="btn" data-dsvndoclai="' + h(x.name) + '" style="margin:8px 0 0;min-height:44px">Đọc lại thư</button>' :
          '<div style="font-size:12.5px;color:#7a2e0e;background:#fffaeb;border-radius:10px;padding:8px 10px;margin-top:6px">Không nhận số liệu nào từ thư này. Không có nút Nhận. Đã thêm người gửi vào Cài đặt (đối tác tin cậy hay hộp thư nội bộ) thì bấm Kiểm lại thư: máy kiểm chữ ký số và người gửi lại từ đầu, thư giả vẫn bị chặn.</div>' +
          '<button class="btn gh" data-dsvndoclai="' + h(x.name) + '" style="margin:8px 0 0;min-height:44px">Kiểm lại thư</button>') +
        (x.bao_zalo ? '<div style="margin-top:6px">' + dsvnChip('Đã báo Zalo ' + String(x.bao_zalo).slice(11, 16)) + '</div>' : '') +
        '<button class="btn gh" data-dsvneml="' + h(x.name) + '" style="margin:8px 0 0;min-height:44px">Tải thư gốc (.eml) để xem →</button></div>';
    }).join('');
  } else if (DSVN.thuTab === 'chua_ve') {
    html += ds.map(function (x) {
      var ky = String(x.ngay || '').length > 7 ? 'ngày ' + dmy(x.ngay).slice(0, 5) : 'tháng ' + String(x.ngay || '').slice(5, 7) + '/' + String(x.ngay || '').slice(0, 4);
      return '<div class="card" style="padding:12px 14px"><div style="display:flex;justify-content:space-between;gap:8px;align-items:center"><b>' +
        h(x.vendor) + (x.tai_khoan ? ' · ' + h(x.tai_khoan) : '') + ' · ' + h(ky) + '</b>' + dsvnChip('Thiếu thư') + '</div>' +
        '<div style="font-size:13px;color:#667085;margin-top:3px">Thư dự kiến trước ' + h(x.han) + '</div>' +
        dsvnThanhBuoc('dnnnnn', 'Chưa nhận được thư') +
        '<div style="font-size:12.5px;color:#475467;margin-top:6px">Thư về muộn thì máy tự nhận. Đối tác không gửi thì tải tay tệp gốc (chờ giám đốc duyệt).</div></div>';
    }).join('');
  } else {
    html += '<div class="card" style="padding:0">' + ds.map(function (n) {
      return '<div class="shi" data-dsvnct="' + h(n.name) + '" style="padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer;min-height:44px">' +
        '<div style="display:flex;justify-content:space-between;gap:8px;align-items:center"><b>' + h(n.vendor) + ' · ' + dsvnKy(n) + '</b>' +
        dsvnDuongChip('cho_duyet') + '</div><div style="font-size:13px;color:#667085;margin-top:3px">' +
        (n.kenh_nhan === 'Hộp thư đối soát' ? 'Thư không có chữ ký số' : 'Tải tay') + ' · ' + money(n.so_dong) + ' dòng · ' + money(n.thuc_nhan) + ' đ</div>' +
        (n.ly_do_tai_tay ? '<div style="font-size:13px;margin-top:4px">Lý do: ' + h(n.ly_do_tai_tay) + '</div>' : '') + '</div>';
    }).join('') + '</div>';
  }
  html += '<div style="font-size:12.5px;color:#196578;background:#e7f8fc;border-radius:10px;padding:8px 10px;margin:10px 0">' +
    'Nguồn tải tay trước ngày bật hộp thư giữ nguyên, gắn nhãn "Trước khi có thư". Không xoá, không sửa.</div>';
  var b = frame('Hộp thư đối soát', html);
  b.onclick = async function (e) {
    var t = e.target.closest('[data-dsvntab]');
    if (t) { DSVN.thuTab = t.getAttribute('data-dsvntab'); return go(scrDsvnThu, true); }
    t = e.target.closest('[data-dsvnct]');
    if (t) { DSVN.cur = t.getAttribute('data-dsvnct'); DSVN.loc = ''; return go(scrDsvnCt); }
    t = e.target.closest('[data-dsvndoclai]');
    if (t) {
      busy(true);
      try {
        var r = await api('vagabond.doi_soat_vendor.doc_lai_thu', { name: t.getAttribute('data-dsvndoclai') });
        baoTin(r && r.ket_qua === 'Lỗi xử lý' ? 'Vẫn chưa đọc được thư.' : r && r.ket_qua === 'Bị chặn' ? 'Thư vẫn bị chặn: ' + (r.ly_do || '') :
          'Đã đọc lại thư: ' + ((r && r.ket_qua) || 'xong') + '.');
      } catch (er) { baoTin(errMsg(er)); }
      finally { busy(false); }
      return go(scrDsvnThu, true);
    }
    t = e.target.closest('[data-dsvneml]');
    if (t) {
      busy(true);
      try { var f = await api('vagabond.doi_soat_vendor.tai_thu_goc', { name: t.getAttribute('data-dsvneml') }); dsvnTaiXuong(f.ten, f.noi_dung); }
      catch (er) { baoTin(errMsg(er)); }
      finally { busy(false); }
    }
  };
}

/* ---------- Màn 04: nhận file ---------- */
async function scrDsvnTai() {
  /* Codex #450 vòng 16: tệp nhận vào pháp nhân nào phải rõ ràng. Một pháp
     nhân thì ghi ra cho biết; từ hai trở lên thì chọn trước, không tự lấy
     pháp nhân mặc định. Đổi pháp nhân khi đã có tệp thì xem trước lại. */
  var ctNhan = DSVN.ctNhan || [];
  if (ctNhan.length === 1) DSVN.ct = ctNhan[0];
  else if (ctNhan.indexOf(DSVN.ct) < 0) DSVN.ct = '';
  var canChon = ctNhan.length > 1;
  var html = canChon ? '<div class="card" style="padding:12px 14px"><b>Nhận vào pháp nhân</b>' +
    '<div style="font-size:13px;color:#667085;margin:2px 0 8px">Tệp được lưu và đối chiếu với hoá đơn, tiền về của pháp nhân này. Chọn trước khi chọn file.</div>' +
    /* Codex #450 vòng 17: chip mang nhãn ngắn máy chủ rút (tối đa 16 ký tự,
       không trùng), tên đầy đủ trong title và hiện dưới hàng chip khi đã chọn;
       giá trị gửi lên vẫn là tên đầy đủ. Hàng chip chừa lề hai bên. */
    '<div class="chips" style="padding:0 2px">' + ctNhan.map(function (c) {
      return '<div class="chip' + (DSVN.ct === c ? ' on' : '') + '" data-dsvnphap="' + h(c) + '" title="' + h(c) +
        '" style="min-height:44px">' + h(DSVN.ctNhanTen[c] || c) + '</div>';
    }).join('') + '</div>' +
    (DSVN.ct ? '<div style="font-size:12.5px;color:#475467;margin-top:6px">' + h(DSVN.ct) + '</div>' : '') + '</div>' :
    (ctNhan.length === 1 ? '<div style="font-size:13px;color:#667085;text-align:center;margin:4px 0 8px">Nhận vào pháp nhân <b>' + h(ctNhan[0]) + '</b></div>' : '');
  html += '<div class="card" style="padding:16px;text-align:center">' +
    '<div style="font-size:28px">↑</div><b>Thêm file vendor gửi</b>' +
    '<div style="font-size:13px;color:#667085;margin:4px 0 10px">Excel, CSV, PDF hoặc ZIP. Máy tự nhận ra nguồn và loại báo cáo, không cần chọn.</div>' +
    '<input type="file" id="dsvnFile" accept=".csv,.xlsx,.xlsm,.xls,.pdf,.zip" hidden>' +
    '<button class="btn gh" id="dsvnChon" style="margin:0">Chọn file từ thiết bị</button>' +
    (DSVN.tep ? '<div style="font-size:13px;margin-top:8px">' + h(DSVN.tep.ten) + '</div>' : '') + '</div>';
  var foot = '';
  if (DSVN.xt) {
    var tong_moi = 0;
    DSVN.xt.forEach(function (x) { if (!x.da_co && !x.phap_nhan_khac && x.mau) tong_moi += x.so.moi; });
    html += DSVN.xt.map(dsvnTheXemTruoc).join('');
    var co_nhan = DSVN.xt.some(function (x) { return !x.da_co && !x.phap_nhan_khac && (x.mau || x.loi.length); });
    if (co_nhan) {
      /* v641: tải tay "có duyệt". Người tải ghi lý do; nguồn chờ giám đốc
         duyệt mới tính là đã đối soát, người tải không tự duyệt được. */
      html += '<div class="card" style="padding:12px 14px"><b>Lý do tải tay</b>' +
        '<div style="font-size:13px;color:#667085;margin:2px 0 8px">Ưu tiên chờ thư đối tác về hộp doisoat@ (có chữ ký số). Tệp tải tay chờ giám đốc duyệt mới tính là đã đối soát.</div>' +
        '<textarea class="tin" id="dsvnLyDo" rows="2" placeholder="Ví dụ: ShopeeFood không gửi thư ngày 04/11" style="width:100%;min-height:44px">' +
        h(DSVN.lyDo || '') + '</textarea></div>';
      foot = '<button class="btn" id="dsvnNhan">' + (tong_moi ? 'Nhận ' + money(tong_moi) + ' dòng, gửi giám đốc duyệt' : 'Lưu nguồn để xử lý') + '</button>' +
        '<div style="text-align:center;font-size:12.5px;color:#667085;margin-top:6px">Chưa ghi sổ hoặc thanh toán. Dòng lỗi giữ lại để xem.</div>';
    }
  } else {
    html += '<div class="emp"><div class="e1">📄</div><div>Chọn file để xem trước: nguồn, kỳ, số dòng, tổng tiền và dòng lỗi. Chưa nhận gì cho tới khi bấm Nhận.</div></div>';
  }
  var b = frame('Nhận file đối soát', html, foot ? { footer: foot } : {});
  var inp = document.getElementById('dsvnFile');
  document.getElementById('dsvnChon').onclick = function () {
    if (canChon && !DSVN.ct) { baoTin('Chọn pháp nhân nhận tệp trước, rồi mới chọn file.'); return; }
    inp.click();
  };
  inp.onchange = function () { if (inp.files && inp.files[0]) dsvnTaiLen(inp.files[0]); };
  var nb = document.getElementById('dsvnNhan');
  if (nb) nb.onclick = dsvnNhanTep;
  var ld = document.getElementById('dsvnLyDo');
  if (ld) ld.oninput = function () { DSVN.lyDo = ld.value; };
  b.onclick = function (e) {
    var p = e.target.closest('[data-dsvnphap]');
    if (p) return dsvnDoiPhap(p.getAttribute('data-dsvnphap'));
    var t = e.target.closest('[data-dsvnct]');
    if (t) { DSVN.cur = t.getAttribute('data-dsvnct'); DSVN.loc = ''; return go(scrDsvnCt); }
  };
}

async function dsvnXem() {
  DSVN.xt = await api('vagabond.doi_soat_vendor.xem_truoc', { file_url: DSVN.tep.file_url, cong_ty: DSVN.ct });
  DSVN.xtCt = DSVN.ct;
}

async function dsvnDoiPhap(c) {
  if (c === DSVN.ct) return;
  DSVN.ct = c;
  if (!DSVN.tep) return go(scrDsvnTai, true);
  DSVN.xt = null;
  busy(true);
  try { await dsvnXem(); }
  catch (e) { baoTin((e && e.message) || 'Chưa đọc được tệp. Kiểm tra lại tệp vendor gửi.'); }
  finally { busy(false); }
  go(scrDsvnTai, true);
}

/* #457 mục 3: tệp chưa nhận ra mẫu thì cho xem ba dòng đầu máy đọc được, để
   người dùng biết máy không mù, và kỹ thuật biết lấy tệp nào làm mẫu. */
function dsvnDauTep(dau) {
  return '<div style="font-size:12.5px;color:#475467;margin-top:8px;line-height:1.5"><b>Ba dòng đầu máy đọc được</b><br>' +
    dau.slice(0, 3).map(function (d) { return '<code style="font-size:12px;word-break:break-all">' + h(d) + '</code>'; }).join('<br>') + '</div>';
}

function dsvnTheXemTruoc(x) {
  var s = '<div class="card" style="padding:12px 14px">' +
    '<div style="display:flex;justify-content:space-between;gap:8px;align-items:center"><b>' + h(x.ten_mau || 'Mẫu chưa nhận') + '</b>' +
    (x.tu_choi ? dsvnChip('Giám đốc từ chối') : x.da_co || x.phap_nhan_khac ? dsvnChip('Đã nhận trước') : dsvnChip(x.trang_thai)) + '</div>' +
    '<div style="font-size:13px;color:#667085;margin-top:2px">' + h(x.ten_tep || '') + '</div>' +
    (x.doc_lai ? '<div style="font-size:12.5px;color:#175cd3;margin-top:4px">Tệp này đã nhận trước nhưng còn lỗi. Bấm Nhận để đọc lại vào đúng nguồn cũ.</div>' : '');
  if (x.phap_nhan_khac) {
    return s + '<div style="font-size:13px;margin-top:8px">Tệp này đã nhận vào một pháp nhân khác. Mỗi tệp chỉ nhận vào một pháp nhân, nên không nhận lại ở đây.</div></div>';
  }
  if (x.da_co) {
    /* Codex #544 vòng 2: tệp giám đốc đã từ chối không nhận lại bằng tải tay. */
    s += '<div style="font-size:13px;margin-top:8px">' + (x.tu_choi ? 'Tệp này đã bị giám đốc từ chối, không nhận lại được. Đối tác gửi lại qua hộp thư đối soát (có chữ ký số) thì máy tự nhận.' :
      'Tệp này đã nhận rồi, không nhận lần hai.') + '</div>' +
      '<button class="btn gh" data-dsvnct="' + h(x.da_co) + '" style="margin:8px 0 0">Mở nguồn đã nhận →</button></div>';
    return s;
  }
  if (x.mau) {
    s += '<div style="font-size:13px;margin-top:8px;line-height:1.6">' +
      'Kỳ: <b>' + dsvnKy(x) + '</b>' + (x.ngay_tien_ve ? ' · tiền về ' + dmy(x.ngay_tien_ve).slice(0, 5) : '') + '<br>' +
      'Dòng mới hợp lệ: <b>' + money(x.so.moi) + '</b> · đã có từ trước: ' + money(x.so.trung) +
      (x.so.loi ? ' · <b style="color:#b42318">cần xem: ' + money(x.so.loi) + '</b>' : '') + '<br>' +
      'Tổng ' + (x.nhom === 'Tiền bán' ? 'thực nhận' : 'phải trả') + ': <b>' + money(x.tong.thuc_nhan) + ' đ</b>' +
      (x.tong_tep && x.tong_tep.thuc_nhan != null ? ' · in trên tệp ' + money(x.tong_tep.thuc_nhan) + ' đ' : '') + '</div>';
    if (x.ghi_chu_don_vi) s += '<div style="font-size:12.5px;color:#475467;margin-top:4px">' + h(x.ghi_chu_don_vi) + '</div>';
  }
  if (!x.mau && (x.dau_tep || []).length) s += dsvnDauTep(x.dau_tep);
  var nhac = (x.loi || []).concat((x.dong_loi || []).map(dsvDongLoi));
  if (nhac.length) {
    s += '<div style="background:#fffaeb;border-radius:10px;padding:8px 10px;margin-top:8px;font-size:13px;color:#7a2e0e">' +
      '<b>' + nhac.length + ' điều cần xem</b><br>' + nhac.slice(0, 2).map(h).join('<br>') +
      (nhac.length > 2 ? '<details><summary style="cursor:pointer">và ' + (nhac.length - 2) + ' nữa</summary>' +
        nhac.slice(2, 40).map(h).join('<br>') + '</details>' : '') + '</div>';
  }
  if ((x.canh_bao || []).length) {
    s += '<div style="font-size:12.5px;color:#475467;margin-top:6px">' + h(x.canh_bao[0]) + '</div>';
  }
  return s + '</div>';
}

function dsvnTaiLen(file) {
  var r = new FileReader();
  r.onload = async function () {
    busy(true);
    try {
      var up = await api('vagabond.doi_soat_vendor.tai_len', { ten: file.name, noi_dung: r.result });
      DSVN.tep = up;
      await dsvnXem();
      go(scrDsvnTai, true);
    } catch (e) { baoTin((e && e.message) || 'Chưa đọc được tệp. Kiểm tra lại tệp vendor gửi.'); }
    finally { busy(false); }
  };
  r.readAsDataURL(file);
}

async function dsvnNhanTep() {
  if (!DSVN.tep) return;
  var ld = document.getElementById('dsvnLyDo');
  var lyDo = String((ld ? ld.value : DSVN.lyDo) || '').trim();
  if (lyDo.length < 5) { baoTin('Ghi lý do tải tay (ví dụ: đối tác không gửi thư ngày 04/11) để giám đốc duyệt.'); return; }
  busy(true);
  try {
    /* Nhận đúng pháp nhân đã xem trước, không lấy chip đang chọn nếu khác. */
    var ra = await api('vagabond.doi_soat_vendor.nhan', { file_url: DSVN.tep.file_url, cong_ty: DSVN.xtCt, ly_do: lyDo });
    ra = ra.filter(function (r) { return r.name; });
    DSVN.lyDo = '';
    toast('Đã lưu ' + ra.length + ' nguồn, chờ giám đốc duyệt. Máy đang đối chiếu hoá đơn và tiền về.');
    DSVN.xt = null; DSVN.tep = null;
    if (ra.length === 1) { DSVN.cur = ra[0].name; DSVN.loc = ''; return go(scrDsvnCt, true); }
    go(scrDsvn, true);
  } catch (e) { baoTin((e && e.message) || 'Chưa nhận được tệp. Thử lại.'); }
  finally { busy(false); }
}

/* ---------- Màn 02: chi tiết một nguồn ---------- */
async function scrDsvnCt() {
  frame('Nguồn đối soát', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc nguồn...</div></div>');
  var kq;
  try { kq = await api('vagabond.doi_soat_vendor.chi_tiet', { name: DSVN.cur, loc: DSVN.loc, trang: dsvnTrang('dong', DSVN.cur + '|' + DSVN.loc) }); }
  catch (e) {
    frame('Nguồn đối soát', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không mở được nguồn. Quay lại danh sách.') + '</div></div>');
    return;
  }
  var n = kq.nguon, t = kq.them || {}, bc = kq.buoc || { tt: '', nhan: [], hien: 1 }, q = kq.quyen || {};
  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">' + h(n.ten_mau || n.vendor) + ' · ' + dsvnKy(n) + '</div>' +
    '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-top:4px">' +
    '<div style="font-size:24px;font-weight:800">' + money(n.thuc_nhan) + ' đ</div>' + dsvnChip(n.trang_thai) + '</div>' +
    '<div style="font-size:13px;color:#667085">' + dsvnNhan(n.nhom) + ' · ' + money(n.so_dong) + ' dòng</div>' +
    '<div style="margin-top:6px">' + dsvnDuongChip(kq.duong || dsvnDuongCua(n)) + '</div>' +
    (typeof veBuoc === 'function' ? veBuoc(DSVN_BUOC.map(function (ten, i) { return { ten: ten, loi: bc.tt.charAt(i) === 'd' }; }),
      bc.hien - 1, 'Tiến độ đối soát') : dsvnThanhBuoc(bc.tt, bc.ghi)) + '</div>';
  /* v641: sáu bước, mỗi bước một dòng kết quả do máy chủ viết. */
  var them = { 4: (t.tien_ve ? t.tien_ve : '') + (n.giao_dich_ngan_hang ? ' (' + n.giao_dich_ngan_hang.split('\n').join(', ') + ')' : ''),
    5: t.hoa_don_ky || '', 3: n.trang_thai !== 'Đã nhận' ? (n.ly_do || '') :
      (n.tong_tep != null && n.tong_tep !== 0 ? 'Tổng in trên tệp ' + money(n.tong_tep) + ' đ' : '') };
  html += '<div class="card" style="padding:12px 14px"><b>Tiến độ</b>' + DSVN_BUOC.map(function (ten, i) {
    return dsvnBuoc((i + 1) + ' · ' + ten, bc.tt.charAt(i) || 'n', (bc.nhan[i] || '') + (them[i + 1] ? '. ' + them[i + 1] : ''));
  }).join('') +
    '<div style="font-size:12.5px;color:#475467;margin-top:6px">Khớp tiền chưa có nghĩa đã hạch toán. Máy chỉ lưu và đối chiếu, không lập phiếu.</div></div>';
  html += dsvnKhoiDuyet(n, q) + dsvnCanCu(kq.can_cu, n);
  if (t.phi_vuot && t.phi_vuot.tong > 0) html += dsvnPhiVuot(t.phi_vuot);
  if (t.ky_the) html += dsvnTheTD(t.ky_the);
  if (t.doi_bien_ban) {
    var bb = t.doi_bien_ban;
    html += '<div class="card" style="padding:12px 14px"><b>So với các thông báo ngày đã nhận</b>' +
      '<div style="font-size:13px;margin-top:6px">' + (bb.khop ? '✓ Khớp đủ tiền, phí và thực nhận.' :
        'Lệch: tiền ' + money(bb.lech.tien_hang) + ' đ, phí ' + money(bb.lech.phi) + ' đ, thực nhận ' + money(bb.lech.thuc_nhan) +
        ' đ. Tải đủ thông báo tạm ứng ngày còn thiếu.') + '</div></div>';
  }
  if (n.trang_thai === 'Lỗi tệp' && (t.dau_tep || []).length) html += '<div class="card" style="padding:12px 14px">' + dsvnDauTep(t.dau_tep) + '</div>';
  var nhac = (t.loi || []).concat((t.dong_loi || []).map(dsvDongLoi));
  if (nhac.length) {
    html += '<details class="card" style="padding:12px 14px"><summary style="cursor:pointer;min-height:24px"><b>' + nhac.length +
      ' điều cần xem</b> · ' + h(String(nhac[0]).slice(0, 80)) + '</summary><div style="font-size:13px;margin-top:6px;line-height:1.5">' +
      nhac.slice(0, 60).map(h).join('<br>') + '</div></details>';
  }
  DSVN.banSua = t.ban_sua || [];
  if (DSVN.banSua.length) html += dsvnBanSua(DSVN.banSua);
  html += '<div class="chips" style="padding:0 2px">' + [['', 'Tất cả dòng'], ['chua_noi', 'Cần xem'], ['da_noi', 'Đã nối']].map(function (c) {
    return '<div class="chip' + (DSVN.loc === c[0] ? ' on' : '') + '" data-dsvnloc="' + c[0] + '">' + c[1] + '</div>';
  }).join('') + '</div>';
  var dong = kq.dong || [];
  if (!dong.length) {
    html += '<div class="emp"><div class="e1">✓</div><div>Không có dòng nào trong bộ lọc này.</div></div>';
  } else {
    html += '<div class="card" style="padding:0">' + dong.map(dsvnDong).join('') + '</div>';
  }
  html += dsvnPhanTrang('dong', DSVN.trang.dong.so, kq.con, 100, 'Dòng');
  var xn = bc.xac_nhan_duoc && q.xac_nhan;
  var foot = '<div style="display:flex;gap:8px"><button class="btn gh" id="dsvnLai" style="margin:0;flex:1">Đối chiếu lại</button>' +
    (n.xac_nhan_luc ? '' : '<button class="btn' + (xn ? '' : ' gh') + '" id="dsvnXacNhan" style="margin:0;flex:1"' + (xn ? '' : ' disabled') + '>' +
      (xn ? 'Xác nhận đã đối soát' : 'Xác nhận (chưa đủ bước)') + '</button>') + '</div>' +
    (!xn && !n.xac_nhan_luc ? '<div style="text-align:center;font-size:12.5px;color:#667085;margin-top:6px">' +
      h(q.xac_nhan ? 'Mở khi năm bước trước xanh: ' + (bc.ghi || '') : 'Chỉ kế toán xác nhận được.') + '</div>' : '');
  var b = frame('Nguồn đối soát', html, { footer: foot });
  b.onclick = async function (e) {
    if (dsvnBamTrang(e, scrDsvnCt)) return;
    var bs = e.target.closest('[data-dsvnbs]');
    if (bs) {
      var x = DSVN.banSua.filter(function (y) { return y.khoa === bs.getAttribute('data-dsvnbs'); })[0];
      if (!x) return;
      // Codex #450 vòng 15: thao tác đổi căn cứ tiền, phải hỏi lại và cho thấy hai bản.
      var ok = await confirmSheet('Dùng bản sửa của vendor?', 'Đơn ' + (x.ma || '') +
        '\nĐang tính: ' + dsvnBanTom(x.cu) + '\nBản sửa: ' + dsvnBanTom(x.moi) +
        '\n\nBản đang tính sẽ thôi tính (vẫn giữ để tra). Máy đối chiếu lại tổng và tiền về của cả hai báo cáo.',
        'Dùng bản sửa', true);
      if (!ok) return;
      busy(true);
      try {
        await api('vagabond.doi_soat_vendor.dung_ban_sua', { name: n.name, khoa: x.khoa, dau_cu: x.dau_cu || '' });
        toast('Đã dùng bản sửa. Máy đã đối chiếu lại hai báo cáo.'); go(scrDsvnCt, true);
      }
      catch (er) { toast(errMsg(er)); }
      finally { busy(false); }
      return;
    }
    var dy = e.target.closest('[data-dsvnduyet]');
    if (dy) {
      var co = dy.getAttribute('data-dsvnduyet') === '1';
      var lyTc = '';
      if (!co) {
        var o = document.getElementById('dsvnLyTc');
        lyTc = String(o ? o.value : '').trim();
        if (lyTc.length < 3) { baoTin('Ghi lý do từ chối để người tải biết.'); return; }
      }
      var dongY = await confirmSheet(co ? 'Duyệt tệp đối soát này?' : 'Từ chối tệp đối soát này?', co ?
        'Nguồn được tính là đã xác thực. Kế toán vẫn phải khớp tiền và nối chứng từ.' :
        'Các dòng của tệp thôi tính (vẫn giữ để tra). Khi thư thật của đối tác về, máy đọc lại từ thư.', co ? 'Duyệt' : 'Từ chối', !co);
      if (!dongY) return;
      busy(true);
      try {
        await api(co ? 'vagabond.doi_soat_vendor.duyet_nguon' : 'vagabond.doi_soat_vendor.tu_choi_nguon',
          co ? { name: n.name } : { name: n.name, ly_do: lyTc });
        toast(co ? 'Đã duyệt.' : 'Đã từ chối.'); go(scrDsvnCt, true);
      } catch (er) { baoTin(errMsg(er)); }
      finally { busy(false); }
      return;
    }
    var eml = e.target.closest('[data-dsvneml]');
    if (eml) {
      busy(true);
      try {
        var f = await api('vagabond.doi_soat_vendor.tai_thu_goc', { name: eml.getAttribute('data-dsvneml') });
        dsvnTaiXuong(f.ten, f.noi_dung);
      } catch (er) { baoTin(errMsg(er)); }
      finally { busy(false); }
      return;
    }
    var dl = e.target.closest('[data-dsvndoclaict]');
    if (dl) {
      busy(true);
      try {
        var r = await api('vagabond.doi_soat_vendor.doc_lai_thu', { name: dl.getAttribute('data-dsvndoclaict') });
        toast(r && r.ket_qua === 'Đã xác thực' ? 'Đã đọc lại thư gốc.' : 'Đọc lại: ' + ((r && r.ket_qua) || 'xong') + '.');
        go(scrDsvnCt, true);
      } catch (er) { baoTin(errMsg(er)); }
      finally { busy(false); }
      return;
    }
    var xn = e.target.closest('[data-dsvnxn]');
    if (xn) {
      busy(true);
      try { await api('vagabond.doi_soat_vendor.xac_nhan_noi', { name: xn.getAttribute('data-dsvnxn') }); toast('Đã xác nhận nối.'); go(scrDsvnCt, true); }
      catch (er) { toast(errMsg(er)); }
      finally { busy(false); }
      return;
    }
    var x = e.target.closest('[data-dsvnloc]');
    if (x) { DSVN.loc = x.getAttribute('data-dsvnloc'); return go(scrDsvnCt, true); }
    x = e.target.closest('[data-dsvnsi]');
    if (x && typeof scrDsView === 'function') return go(function () { return scrDsView(x.getAttribute('data-dsvnsi')); });
  };
  var nutXn = document.getElementById('dsvnXacNhan');
  if (nutXn && xn) nutXn.onclick = async function () {
    busy(true);
    try { await api('vagabond.doi_soat_vendor.xac_nhan_nguon', { name: n.name }); toast('Đã xác nhận nguồn đối soát.'); go(scrDsvnCt, true); }
    catch (er) { baoTin(errMsg(er)); }
    finally { busy(false); }
  };
  document.getElementById('dsvnLai').onclick = async function () {
    busy(true);
    try { await api('vagabond.doi_soat_vendor.doi_chieu_lai', { name: n.name }); toast('Đã đối chiếu lại.'); go(scrDsvnCt, true); }
    catch (e) { baoTin((e && e.message) || 'Chưa đối chiếu được. Thử lại.'); }
    finally { busy(false); }
  };
}

// Codex #450 vòng 14: vendor gửi lại sự kiện đã nhận với nội dung khác (ví dụ
// Grab đổi thẻ/ví thành tiền mặt). Kế toán so hai bản rồi bấm dùng bản sửa.
function dsvnBanTom(b) {
  return b ? (b.mo_ta || 'Không ghi') + ' · ' + money(b.thuc_nhan) + ' đ' : 'không còn bản đang tính';
}
function dsvnBanSua(ds) {
  return '<div class="card" style="padding:12px 14px"><b>' + ds.length + ' bản sửa của vendor chờ chọn</b>' +
    '<div style="font-size:12.5px;color:#475467;margin-top:4px">Báo cáo này ghi khác với lần nhận trước. ' +
    'Bấm "Dùng bản sửa" thì bản cũ thôi tính (vẫn giữ để tra) và máy đối chiếu lại tiền về của cả hai báo cáo.</div>' +
    ds.map(function (x) {
      var cu = h(dsvnBanTom(x.cu));
      return '<div style="border-top:1px solid #eaecf0;margin-top:8px;padding-top:8px;font-size:13px;line-height:1.5">' +
        '<b>' + h(x.ma || '') + '</b>' + (x.ngay ? ' · ' + h(x.ngay) : '') +
        '<div>Đang tính: ' + cu + '</div>' +
        '<div>Bản sửa: ' + h(dsvnBanTom(x.moi)) + '</div>' +
        '<button class="btn gh" style="margin:6px 0 0;min-height:44px" data-dsvnbs="' + h(x.khoa) + '">Dùng bản sửa</button></div>';
    }).join('') + '</div>';
}

function dsvnBuoc(ten, tt, mo_ta) {
  /* tt: x xong, v đang chờ, d có sự cố, n chưa tới (v641; true/false cũ vẫn hiểu). */
  if (tt === true) tt = 'x';
  if (tt === false) tt = 'v';
  var m = { x: ['#ecfdf3', '#067647', '✓'], v: ['#fffaeb', '#b54708', '…'], d: ['#fef3f2', '#b42318', '!'], n: ['#f2f4f7', '#8994a4', '·'] }[tt] ||
    ['#f2f4f7', '#8994a4', '·'];
  return '<div style="display:flex;gap:10px;align-items:flex-start;padding:8px 0;border-bottom:1px solid #f2f4f7">' +
    '<span style="flex:0 0 22px;height:22px;border-radius:50%;text-align:center;line-height:22px;font-size:13px;font-weight:700;' +
    'background:' + m[0] + ';color:' + m[1] + '">' + m[2] + '</span>' +
    '<div><b style="font-size:14px">' + h(ten) + '</b><div style="font-size:13px;color:#667085">' + h(mo_ta) + '</div></div></div>';
}

/* Khoá đường vào tính ở máy khách chỉ để hiện chip khi máy chủ chưa gửi
   (cùng luật doi_soat_thu.duong_vao). */
function dsvnDuongCua(n) {
  if (n.duong_vao === 'Chờ duyệt') return 'cho_duyet';
  if (n.duong_vao === 'Từ chối') return 'tu_choi';
  if (n.kenh_nhan === 'Hộp thư đối soát') return 'thu';
  if (n.duong_vao === 'Đã duyệt') return 'da_duyet';
  return 'cu';
}

/* Khối duyệt: tệp tải tay hay thư không chữ ký chờ giám đốc. */
function dsvnKhoiDuyet(n, q) {
  var cho = n.duong_vao === 'Chờ duyệt', cu = !n.duong_vao && n.kenh_nhan !== 'Hộp thư đối soát';
  if (n.duong_vao === 'Từ chối') {
    return '<div class="card" style="padding:12px 14px;border-left:4px solid #d93a2b"><b>Giám đốc đã từ chối</b>' +
      '<div style="font-size:13px;color:#475467;margin-top:4px">Lý do: ' + h(n.ly_do_duyet || '') + '. Các dòng đã thôi tính.</div></div>';
  }
  if (n.duong_vao === 'Đã duyệt') {
    return '<div class="card" style="padding:12px 14px"><b>Giám đốc đã duyệt</b><div style="font-size:13px;color:#475467;margin-top:4px">' +
      (n.ly_do_tai_tay ? 'Lý do tải tay: ' + h(n.ly_do_tai_tay) : 'Thư đối tác không có chữ ký số.') + '</div></div>';
  }
  if (!cho && !cu) return '';
  var s = '<div class="card" style="padding:12px 14px;border-left:4px solid #f5b40b"><b>' +
    (cho ? (n.kenh_nhan === 'Hộp thư đối soát' ? 'Thư không có chữ ký số, chờ giám đốc duyệt' : 'Tải tay, chờ giám đốc duyệt') :
      'Tải tay trước khi có hộp thư, chưa xác thực') + '</b>' +
    '<div style="font-size:13px;color:#475467;margin-top:4px">' +
    (n.ly_do_tai_tay ? 'Lý do tải tay: ' + h(n.ly_do_tai_tay) + '. ' : '') +
    'Chưa tính là đã đối soát cho tới khi giám đốc duyệt. Thư thật của đối tác về sau thì máy tự xác thực bằng thư.</div>';
  if (q.duyet) {
    s += '<textarea class="tin" id="dsvnLyTc" rows="2" placeholder="Lý do nếu từ chối" style="width:100%;margin-top:8px;min-height:44px"></textarea>' +
      '<div style="display:flex;gap:8px;margin-top:8px"><button class="btn gh" data-dsvnduyet="0" style="margin:0;flex:1;min-height:44px">Từ chối</button>' +
      '<button class="btn" data-dsvnduyet="1" style="margin:0;flex:1;min-height:44px">Duyệt</button></div>';
  } else if (q.cua_minh) {
    s += '<div style="font-size:12.5px;color:#b54708;margin-top:6px">Bạn là người tải tệp này nên không tự duyệt được. Giám đốc còn lại duyệt.</div>';
  }
  return s + '</div>';
}

/* Khối Căn cứ thư gốc. */
function dsvnCanCu(c, n) {
  if (!c) return '';
  var dong = function (a, b) { return '<div style="display:flex;justify-content:space-between;gap:10px;font-size:13.5px;padding:4px 0"><span style="color:#667085">' +
    a + '</span><b style="text-align:right;word-break:break-word">' + h(b) + '</b></div>'; };
  return '<div class="card" style="padding:12px 14px;border:1.5px solid #68d5e7"><b>Căn cứ thư gốc</b>' +
    dong('Người gửi', c.nguoi_gui || '') +
    dong('Chữ ký số', c.ky_boi ? '✓ ' + c.ky_boi + ', hợp lệ' : (c.ly_do || 'Không có chữ ký số')) +
    dong('Đường đi', 'Hộp thư công ty → doisoat@') +
    dong('Nhận lúc', c.nhan_luc ? String(c.nhan_luc).slice(11, 16) + ' ' + dmy(String(c.nhan_luc).slice(0, 10)).slice(0, 5) : '') +
    dong('Tệp đính kèm', n.ten_tep || '') + dong('Mã băm thư', c.sha256 || '') +
    '<div style="font-size:12.5px;color:#196578;background:#e7f8fc;border-radius:10px;padding:8px 10px;margin-top:6px">Thư gốc và tệp lưu chỉ đọc. ' +
    'Sửa tệp dù một ký tự là chữ ký hỏng, máy không nhận.</div>' +
    '<button class="btn gh" data-dsvneml="' + h(c.name) + '" style="margin:8px 0 0;min-height:44px">Tải thư gốc (.eml) để kiểm →</button>' +
    (n.trang_thai === 'Cần xử lý' || n.trang_thai === 'Lỗi tệp' ?
      '<div style="font-size:12.5px;color:#475467;margin-top:8px">Kỹ thuật đã sửa cách đọc mẫu này thì bấm Đọc lại thư gốc: máy kiểm lại chữ ký số rồi đọc lại tệp từ chính thư đó. Dòng đã đúng giữ nguyên.</div>' +
      '<button class="btn" data-dsvndoclaict="' + h(c.name) + '" style="margin:8px 0 0;min-height:44px">Đọc lại thư gốc</button>' : '') +
    '</div>';
}

function dsvnPhiVuot(p) {
  return '<div class="card" style="padding:12px 14px;border-left:4px solid #d93a2b"><b>Phí thu cao hơn biểu phí hợp đồng</b>' +
    (p.ct || []).map(function (x) {
      return '<div style="font-size:13px;margin-top:6px">Thẻ ' + h(x.the) + ' ' + h(x.vung === 'DOMESTIC' ? 'nội địa' : x.vung === 'INTERNATIONAL' ? 'quốc tế' : x.vung) +
        ': thu ' + h(String(x.mdr).replace('.', ',')) + '%, hợp đồng ' + h(String(x.bieu).replace('.', ',')) + '%, dư <b>' + money(x.du) + ' đ</b></div>';
    }).join('') + '<div style="font-size:12.5px;color:#475467;margin-top:6px">Tổng thu dư: ' + money(p.tong) + ' đ. Biểu phí khai ở Cài đặt lõi.</div></div>';
}

/* Tải một tệp máy chủ gửi dạng base64 xuống máy người dùng. */
function dsvnTaiXuong(ten, b64) {
  try {
    var bin = atob(b64), u = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
    var a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([u], { type: 'message/rfc822' }));
    a.download = ten || 'thu-goc.eml';
    document.body.appendChild(a); a.click(); a.remove();
  } catch (e) { baoTin('Trình duyệt này chưa tải được tệp. Mở trên máy tính.'); }
}

function dsvnTheTD(k) {
  if (!k.dau_ky && k.dau_ky !== 0) {
    return '<div class="card" style="padding:12px 14px"><b>Số dư thẻ</b><div style="font-size:13px;margin-top:6px">' + h(k.ghi_chu || '') +
      '<br>Dư nợ cuối kỳ theo sao kê: <b>' + money(k.cuoi_ky) + ' đ</b></div></div>';
  }
  return '<div class="card" style="padding:12px 14px"><b>Số dư thẻ</b>' +
    [['Dư nợ đầu kỳ', k.dau_ky], ['Chi tiêu trong kỳ', k.phat_sinh], ['Phí / lãi', k.phi], ['Đã trả trong kỳ', -k.da_tra], ['Dư nợ cuối kỳ theo sao kê', k.cuoi_ky]]
      .map(function (r) {
        return '<div style="display:flex;justify-content:space-between;font-size:13.5px;padding:4px 0"><span>' + r[0] + '</span><b>' + money(r[1]) + ' đ</b></div>';
      }).join('') +
    '<div style="font-size:12.5px;color:' + (k.du ? '#067647' : '#b42318') + ';margin-top:4px">' + (k.du ? '✓ Phương trình số dư khớp.' : h(k.ghi_chu)) + '</div>' +
    '<div style="font-size:12.5px;color:#475467;margin-top:4px">Trả nợ thẻ không phải chi phí lần nữa; chi phí nằm ở từng giao dịch mua.</div></div>';
}

function dsvnDong(d) {
  var ct = d.sales_invoice ? '<span data-dsvnsi="' + h(d.sales_invoice) + '" style="color:#175cd3;cursor:pointer">' + h(d.sales_invoice) + ' ›</span>' :
    (d.purchase_invoice ? 'HĐ mua ' + h(d.purchase_invoice) : (d.van_don ? 'Vận đơn ' + h(d.van_don) : ''));
  return '<div style="padding:10px 14px;border-bottom:1px solid #f2f4f7;min-height:44px">' +
    '<div style="display:flex;justify-content:space-between;gap:8px"><b style="font-size:14px">' + h(d.ma_don || d.mo_ta || dsvnLoai(d.loai)) +
    '</b><b style="font-size:14px">' + money(d.thuc_nhan) + ' đ</b></div>' +
    '<div style="font-size:12.5px;color:#667085">' + (d.ngay ? dmy(d.ngay).slice(0, 5) : '') + (d.gio ? ' ' + h(String(d.gio).slice(0, 5)) : '') +
    ' · ' + h(d.mo_ta || dsvnLoai(d.loai)) + (d.nguoi ? ' · ' + h(d.nguoi) : '') +
    (d.phi ? ' · phí ' + money(d.phi) + ' đ' : '') + '</div>' +
    '<div style="display:flex;justify-content:space-between;gap:8px;align-items:center;margin-top:4px">' +
    '<span style="font-size:12.5px">' + ct + '</span>' + dsvnChip(d.trang_thai_khop || 'Chưa nối') + '</div>' +
    (d.ghi_chu_khop ? '<div style="font-size:12px;color:#667085;margin-top:2px">' + h(d.ghi_chu_khop) + '</div>' : '') +
    /* Codex #450: nối theo tiền chỉ là gợi ý; kế toán xem hoá đơn rồi bấm xác
       nhận thì dòng mới tính là đã nối. */
    (d.trang_thai_khop === 'Nối theo tiền' && d.sales_invoice ? '<button class="btn gh" data-dsvnxn="' + h(d.name) +
      '" style="margin:6px 0 0;min-height:44px;width:100%">✓ Đúng hoá đơn ' + h(d.sales_invoice) + ', xác nhận nối</button>' : '') + '</div>';
}

/* ---------- Màn 01: vùng Đối soát trên Chi tiết đơn ---------- */
function dsvnKhoiHd() {
  return '<div id="dsvnKhoiHd"></div>';
}

async function dsvnNapKhoiHd(si) {
  var o = document.getElementById('dsvnKhoiHd');
  if (!o || typeof coQuyenKeToan !== 'function' || !coQuyenKeToan()) return;
  var ds;
  try { ds = await api('vagabond.doi_soat_vendor.cua_hoa_don', { si: si }); } catch (e) { return; }
  if (!ds || !ds.length) return;
  o.innerHTML = '<div class="card" style="padding:12px 14px"><b>ĐỐI SOÁT TIỀN BÁN</b>' + ds.map(function (d) {
    return '<div style="font-size:13.5px;margin-top:8px">' + h(d.vendor) + ' · ' + h(d.ma_don || '') + ' · ' + dsvnChip(d.trang_thai_khop) +
      [['Giá trị sau giảm giá', d.tien_hang], ['Phí theo báo cáo', -d.phi], ['Tiền nguồn trả cho đơn này', d.thuc_nhan]].map(function (r) {
        return '<div style="display:flex;justify-content:space-between;padding:3px 0"><span>' + r[0] + '</span><b>' + money(r[1]) + ' đ</b></div>';
      }).join('') + (d.ghi_chu_khop ? '<div style="font-size:12px;color:#667085">' + h(d.ghi_chu_khop) + '</div>' : '') +
      '<button class="btn gh" data-dsvnnguon="' + h(d.nguon) + '" style="margin:6px 0 0">Đối soát →</button></div>';
  }).join('') + '</div>';
  o.onclick = function (e) {
    var t = e.target.closest('[data-dsvnnguon]');
    if (t) { DSVN.cur = t.getAttribute('data-dsvnnguon'); DSVN.loc = ''; go(scrDsvnCt); }
  };
}

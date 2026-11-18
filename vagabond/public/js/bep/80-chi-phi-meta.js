/* v674 Chi phí quảng cáo Meta (anh Việt và chị Dung chốt 18/11/2026).
   Hai màn:
   1. Chi phí quảng cáo Meta (Marketing): số Meta ĐÃ TIÊU theo ngày cạnh doanh thu web.
      Số tham khảo, không phải số trừ thẻ; không gắn nhãn ROAS.
   2. Đối soát chi phí Meta (Kế toán): mỗi tháng ba con số tách riêng (Đã tiêu trên Meta,
      Đã trừ trên thẻ, Đã ghi sổ), giao dịch thẻ đã loại trùng, quyết định tay của kế toán,
      và MỘT bút toán nháp Nợ 6417 / Có 3411 (phí thẻ đi kèm vào 6427) chờ ghi sổ.
   Máy chủ chốt mọi con số (QT-19). */
var QCM_P = 'vagabond.quang_cao_meta.';
var DSM_P = 'vagabond.chi_phi_meta.';
var QCM = { khoang: '30', tk: '', tt: '', luot: 0 };
var DSM = { tt: '', bt: '', so: '6', luot: 0 };
var QCM_QUYEN = ['System Manager', 'Marketing', 'Giám đốc', 'AP Giám đốc', 'Accounts Manager', 'Accounts User', 'AP Kiểm soát (FIN)', 'Vagabond Bao cao'];
function coQuyenQcMeta() { return QCM_QUYEN.some(function (v) { return hasRole(v); }); }
var QCM_TT = { 'Đã chốt': ['#ecfdf3', '#067647'], 'Meta còn điều chỉnh': ['#fffaeb', '#b54708'], 'Chưa đọc': ['#fef3f2', '#b42318'], 'Không chi': ['#f2f4f7', '#475467'] };
var QCM_TT_NHAN = { 'Đã chốt': 'Đã chốt', 'Meta còn điều chỉnh': 'Còn điều chỉnh', 'Chưa đọc': 'Chưa đọc', 'Không chi': 'Không chi' };
var DSM_TT = { 'Khớp': ['#ecfdf3', '#067647'], 'Lệch': ['#fffaeb', '#b54708'], 'Chưa có sao kê': ['#f2f4f7', '#475467'], 'Chưa đủ chứng từ': ['#fef3f2', '#b42318'] };
var DSM_TT_NHAN = { 'Khớp': 'Khớp', 'Lệch': 'Lệch', 'Chưa có sao kê': 'Chưa có sao kê', 'Chưa đủ chứng từ': 'Thiếu chứng từ' };
var DSM_GD = { 'Vào bút toán': ['#e6f8fb', '#05323C'], 'Đã ghi sổ': ['#ecfdf3', '#067647'], 'Đã có chứng từ khác': ['#f2f4f7', '#475467'],
  'Chờ kế toán chọn': ['#fef3f2', '#b42318'], 'Kế toán bỏ': ['#f2f4f7', '#475467'], 'Không thuộc Meta': ['#f2f4f7', '#475467'] };
var DSM_BT = { 'Chưa lập': ['#f2f4f7', '#475467'], 'Nháp chờ ghi sổ': ['#fffaeb', '#b54708'], 'Nháp đã sửa tay': ['#fef3f2', '#b42318'], 'Đã ghi sổ': ['#ecfdf3', '#067647'], 'Đã bỏ nháp': ['#f2f4f7', '#475467'] };

function qcmChipMau(bang, tt, nhan) {
  var m = bang[tt] || ['#f2f4f7', '#475467'];
  return '<span style="flex:0 0 auto;display:inline-flex;align-items:center;min-height:28px;padding:0 10px;border-radius:14px;background:' + m[0] + ';color:' + m[1] +
    ';font-size:13px;font-weight:700;white-space:nowrap">' + h(nhan || tt) + '</span>';
}
function qcmTien(bangTien) {
  var k = Object.keys(bangTien || {}).filter(function (t) { return bangTien[t]; });
  if (!k.length) return '0 đ';
  return k.map(function (t) { return t === 'VND' || !t ? money(bangTien[t]) + ' đ' : Number(bangTien[t]).toLocaleString('vi-VN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' ' + h(t); }).join(' + ');
}
function qcmIso(d) { return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }
function qcmKhoang(k) {
  var hn = new Date(); var hq = new Date(hn.getTime() - 86400000);
  if (k === '7') return [qcmIso(new Date(hq.getTime() - 6 * 86400000)), qcmIso(hq)];
  if (k === 'thang') return [qcmIso(new Date(hn.getFullYear(), hn.getMonth(), 1)), qcmIso(hq)];
  if (k === 'thang_truoc') return [qcmIso(new Date(hn.getFullYear(), hn.getMonth() - 1, 1)), qcmIso(new Date(hn.getFullYear(), hn.getMonth(), 0))];
  return [qcmIso(new Date(hq.getTime() - 29 * 86400000)), qcmIso(hq)];
}

async function scrQcMeta() {
  var tieuDe = 'Chi phí quảng cáo Meta';
  frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc chi phí quảng cáo...</div></div>');
  var luot = QCM.luot = QCM.luot + 1, d;
  var kh = qcmKhoang(QCM.khoang);
  try { d = await api(QCM_P + 'tong_quan', { tu: kh[0], den: kh[1], tai_khoan: QCM.tk, trang_thai: QCM.tt }); }
  catch (e) {
    if (luot !== QCM.luot) return;
    frame(tieuDe, '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e) || 'Không đọc được.') + '</div><button class="btn gh" id="qcmLai" style="margin-top:12px;min-height:48px">Thử lại</button></div>');
    var l = document.getElementById('qcmLai'); if (l) l.onclick = function () { scrQcMeta(); };
    return;
  }
  if (luot !== QCM.luot) return;
  var ch = d.cau_hinh || {}, canh = [];
  if (!ch.bat) canh.push(['#f2f4f7', '#475467', 'Đọc chi phí Meta đang tắt. Quản trị hệ thống bật ở Cài đặt, mục Chi phí quảng cáo Meta.']);
  (ch.loi || []).forEach(function (x) { canh.push(['#fef3f2', '#b42318', x]); });
  (d.tai_khoan || []).forEach(function (t) { if (t.loi) canh.push(['#fef3f2', '#b42318', t.ten + ': ' + t.loi]); });
  if (ch.bat && !d.co_nhom_nhan) canh.push(['#fffaeb', '#b54708', 'Chưa có nhóm Zalo nhận tin "Đọc chi phí quảng cáo Meta bị dừng": lỗi chỉ hiện ở màn này.']);
  var dem = d.dem || {};
  var html = '<div class="card" style="padding:12px 14px"><div style="display:flex;gap:8px;text-align:center">' +
    '<div style="flex:1;min-width:0"><div style="font-size:13px;color:#667085">Meta đã tiêu</div><div style="font-size:16px;font-weight:800;word-break:break-word">' + qcmTien(d.tong_chi) + '</div></div>' +
    '<div style="flex:1;min-width:0"><div style="font-size:13px;color:#667085">Doanh thu web</div><div style="font-size:16px;font-weight:800">' + money(d.tong_doanh_thu_web) + ' đ</div></div></div>' +
    '<div style="font-size:13px;color:#667085;text-align:center;margin-top:6px">' + ngayNgan(d.tu) + ' tới ' + ngayNgan(d.den) + '. Số Meta báo đã tiêu là số tham khảo, chưa phải số trừ thẻ.</div></div>' +
    (canh.length ? canh.slice(0, 2).map(function (c) { return '<div style="background:' + c[0] + ';color:' + c[1] + ';border-radius:12px;padding:9px 12px;font-size:13.5px;margin:0 0 8px">' + h(c[2]) + '</div>'; }).join('') +
      (canh.length > 2 ? '<div style="font-size:13px;color:#667085;margin:-4px 2px 8px">và ' + (canh.length - 2) + ' nhắc nữa</div>' : '') : '') +
    cp2HangChip([['', 'Tất cả'], ['Đã chốt', 'Đã chốt'], ['Meta còn điều chỉnh', 'Còn điều chỉnh'], ['Chưa đọc', 'Chưa đọc'], ['Không chi', 'Không chi']].map(function (x) {
      return cp2Chip('data-qcmtt', x[0], x[1], QCM.tt === x[0], dem[x[0]] || 0);
    }).join('')) +
    cp2HangChip([['', 'Mọi tài khoản']].concat((d.tai_khoan || []).map(function (t) { return [t.ma, (t.ten || t.ma).slice(0, 14)]; })).map(function (x) {
      return cp2Chip('data-qcmtk', x[0], x[1], QCM.tk === x[0]);
    }).join('')) +
    cp2HangChip([['7', '7 ngày'], ['30', '30 ngày'], ['thang', 'Tháng này'], ['thang_truoc', 'Tháng trước']].map(function (x) {
      return cp2Chip('data-qcmkh', x[0], x[1], QCM.khoang === x[0]);
    }).join('')) +
    ((d.rows || []).length ? '<div class="card" style="padding:4px 12px">' + d.rows.map(function (r) {
      var tl = (r.chi && r.chi.VND && r.doanh_thu_web) ? ' · Chi trên doanh thu web ' + Math.round(r.chi.VND * 100 / r.doanh_thu_web) + '%' : '';
      return '<button type="button" data-qcmngay="' + h(r.ngay) + '" style="display:flex;gap:10px;align-items:center;width:100%;min-height:60px;border:0;border-bottom:1px solid #f2f4f7;background:none;font:inherit;text-align:left;padding:8px 0">' +
        '<span style="flex:0 0 54px;font-size:15px;font-weight:800">' + h(r.ngay.slice(8, 10) + '/' + r.ngay.slice(5, 7)) + '</span>' +
        '<span style="flex:1;min-width:0"><span style="display:block;font-size:14.5px;font-weight:700">Meta ' + qcmTien(r.chi) + '</span>' +
        '<span style="display:block;font-size:13px;color:#667085">Web ' + money(r.doanh_thu_web) + ' đ' + tl + '</span></span>' +
        qcmChipMau(QCM_TT, r.trang_thai, QCM_TT_NHAN[r.trang_thai]) + '</button>';
    }).join('') + '</div>'
      : (QCM.tt ? '<div class="emp"><div class="e1">🔎</div><div>Không có ngày nào khớp bộ lọc.</div><button class="btn gh" id="qcmBo" style="margin-top:12px;min-height:48px">Bỏ lọc</button></div>'
        : '<div class="emp"><div class="e1">📭</div><div>Chưa có số chi quảng cáo. Giám đốc dán mã truy cập Meta và bật đọc ở Cài đặt, mục Chi phí quảng cáo Meta; sáng hôm sau số sẽ hiện.</div></div>'));
  var b = frame(tieuDe, html, { footer: d.duoc_doc_lai && ch.bat ? '<button class="btn gh" id="qcmDoc" style="margin:0;min-height:48px">Đọc lại từ Meta</button>' : '' });
  var bo = document.getElementById('qcmBo'); if (bo) bo.onclick = function () { QCM.tt = ''; scrQcMeta(); };
  var dl = document.getElementById('qcmDoc');
  if (dl) dl.onclick = async function () { dl.disabled = true; try { var r = await api(QCM_P + 'doc_lai_ngay', {}); toast(r.loi_nhan); } catch (e) { toast(errMsg(e)); } dl.disabled = false; };
  b.onclick = function (e) {
    var n;
    if ((n = e.target.closest('[data-qcmtt]'))) { QCM.tt = n.getAttribute('data-qcmtt'); return scrQcMeta(); }
    if ((n = e.target.closest('[data-qcmtk]'))) { QCM.tk = n.getAttribute('data-qcmtk'); return scrQcMeta(); }
    if ((n = e.target.closest('[data-qcmkh]'))) { QCM.khoang = n.getAttribute('data-qcmkh'); return scrQcMeta(); }
    if ((n = e.target.closest('[data-qcmngay]'))) return qcmNgay(n.getAttribute('data-qcmngay'));
  };
}

async function qcmNgay(ngay) {
  var ds;
  try { ds = await api(QCM_P + 'chi_tiet_ngay', { ngay: ngay, tai_khoan: QCM.tk }); } catch (e) { return toast(errMsg(e)); }
  crmMoSheet('<div style="font-size:17px;font-weight:800">Ngày ' + ngayNgan(ngay) + '</div><div style="font-size:13.5px;color:#667085;margin-bottom:6px">' + ds.length + ' chiến dịch có chi</div>' +
    (ds.length ? ds.map(function (x) {
      var t = {}; t[x.tien_te || ''] = x.so_tien;
      return '<div style="display:flex;gap:8px;align-items:center;min-height:52px;border-top:1px solid #f2f4f7"><span style="flex:1;min-width:0;font-size:14.5px;font-weight:600">' + h(x.ten_chien_dich || x.chien_dich) +
        '<span style="display:block;font-size:13px;color:#667085;font-weight:500">' + h(x.ten_tai_khoan || x.tai_khoan) + '</span></span><b style="font-size:14.5px">' + qcmTien(t) + '</b></div>';
    }).join('') : '<div class="emp"><div class="e1">📭</div><div>Ngày này không có chiến dịch nào chi tiền.</div></div>'));
}

/* ------------------------------------------------------------ Đối soát (Kế toán) */

async function scrDsMeta() {
  var tieuDe = 'Đối soát chi phí Meta';
  frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đối chiếu sao kê thẻ...</div></div>');
  var luot = DSM.luot = DSM.luot + 1, d;
  try { d = await api(DSM_P + 'ds_thang', { so_thang: DSM.so }); }
  catch (e) {
    if (luot !== DSM.luot) return;
    frame(tieuDe, '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e) || 'Không đọc được.') + '</div><button class="btn gh" id="dsmLai" style="margin-top:12px;min-height:48px">Thử lại</button></div>');
    var l = document.getElementById('dsmLai'); if (l) l.onclick = function () { scrDsMeta(); };
    return;
  }
  if (luot !== DSM.luot) return;
  var rows = d.rows || [], demBt = { '': rows.length };
  rows.forEach(function (r) { demBt[r.but_toan] = (demBt[r.but_toan] || 0) + 1; });
  var hien = rows.filter(function (r) { return (!DSM.tt || r.trang_thai === DSM.tt) && (!DSM.bt || r.but_toan === DSM.bt); });
  var dem = d.dem || {};
  var html = (d.cho_duyet_sao_ke ? '<div style="background:#fffaeb;color:#b54708;border-radius:12px;padding:9px 12px;font-size:13.5px;margin-bottom:8px">' + d.cho_duyet_sao_ke +
      ' sao kê thẻ tải tay đang chờ giám đốc duyệt nên chưa tính vào đây.</div>' : '') +
    cp2HangChip([['', 'Tất cả'], ['Khớp', 'Khớp'], ['Lệch', 'Lệch'], ['Chưa đủ chứng từ', 'Thiếu chứng từ'], ['Chưa có sao kê', 'Chưa có sao kê']].map(function (x) {
      return cp2Chip('data-dsmtt', x[0], x[1], DSM.tt === x[0], dem[x[0]] || 0);
    }).join('')) +
    cp2HangChip([['', 'Mọi bút toán'], ['Chưa lập', 'Chưa lập'], ['Nháp chờ ghi sổ', 'Nháp chờ ghi'], ['Đã ghi sổ', 'Đã ghi sổ']].map(function (x) {
      return cp2Chip('data-dsmbt', x[0], x[1], DSM.bt === x[0], demBt[x[0]] || 0);
    }).join('')) +
    cp2HangChip([['6', '6 tháng'], ['12', '12 tháng']].map(function (x) { return cp2Chip('data-dsmso', x[0], x[1], DSM.so === x[0]); }).join('')) +
    (hien.length ? hien.map(function (r) {
      return '<button type="button" data-dsmky="' + h(r.ky) + '" class="card" style="display:block;width:100%;box-sizing:border-box;border:0;font:inherit;text-align:left;padding:12px 14px;min-height:64px">' +
        '<span style="display:flex;align-items:center;gap:8px"><b style="flex:1;font-size:16px">Tháng ' + h(r.ky.slice(5, 7) + '/' + r.ky.slice(0, 4)) + '</b>' + qcmChipMau(DSM_TT, r.trang_thai, DSM_TT_NHAN[r.trang_thai]) + '</span>' +
        '<span style="display:flex;gap:6px;margin-top:8px;text-align:center">' +
        [['Meta đã tiêu', qcmTien(r.da_tieu)], ['Đã trừ thẻ', money(r.da_tru) + ' đ'], ['Đã ghi sổ', money(r.da_ghi_so) + ' đ']].map(function (x) {
          return '<span style="flex:1;min-width:0;background:#f8fafc;border-radius:10px;padding:6px 2px"><span style="display:block;font-size:13px;color:#667085">' + x[0] + '</span><b style="font-size:14px;word-break:break-word">' + x[1] + '</b></span>';
        }).join('') + '</span>' +
        '<span style="display:block;font-size:13px;color:#667085;margin-top:6px">' + r.so_giao_dich + ' giao dịch · bút toán: ' + h(r.but_toan) + (r.so_cho ? ' · ' + r.so_cho + ' dòng chờ chọn' : '') +
        (r.thieu && r.thieu.length ? ' · thiếu sao kê' : '') + '</span></button>';
    }).join('') : '<div class="emp"><div class="e1">🔎</div><div>Không có tháng nào khớp bộ lọc.</div><button class="btn gh" id="dsmBo" style="margin-top:12px;min-height:48px">Bỏ lọc</button></div>');
  var b = frame(tieuDe, html);
  var bo = document.getElementById('dsmBo'); if (bo) bo.onclick = function () { DSM.tt = ''; DSM.bt = ''; scrDsMeta(); };
  b.onclick = function (e) {
    var n;
    if ((n = e.target.closest('[data-dsmtt]'))) { DSM.tt = n.getAttribute('data-dsmtt'); return scrDsMeta(); }
    if ((n = e.target.closest('[data-dsmbt]'))) { DSM.bt = n.getAttribute('data-dsmbt'); return scrDsMeta(); }
    if ((n = e.target.closest('[data-dsmso]'))) { DSM.so = n.getAttribute('data-dsmso'); return scrDsMeta(); }
    if ((n = e.target.closest('[data-dsmky]'))) { var ky = n.getAttribute('data-dsmky'); return go(function () { return scrDsMetaThang(ky); }); }
  };
}

async function scrDsMetaThang(ky) {
  var tieuDe = 'Chi phí Meta tháng ' + ky.slice(5, 7) + '/' + ky.slice(0, 4);
  frame(tieuDe, '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api(DSM_P + 'chi_tiet_thang', { ky: ky }); }
  catch (e) { return frame(tieuDe, '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e)) + '</div></div>'); }
  var bt = d.but_toan || {}, gd = d.giao_dich || [];
  var nut = '';
  if (d.duoc_lap && bt.trang_thai !== 'Nháp đã sửa tay' && d.trang_thai !== 'Chưa đủ chứng từ' && (bt.dong || []).length)
    nut += cp2NutChinh('dsmLap', bt.trang_thai === 'Nháp chờ ghi sổ' ? 'Cập nhật bản nháp' : 'Lập bút toán nháp', 'Hệ thống không tự ghi sổ. Kế toán kiểm rồi bấm Ghi sổ.');
  if (bt.trang_thai === 'Nháp đã sửa tay') nut += '<div style="font-size:13.5px;color:#b42318;margin-bottom:6px">Bút toán nháp ' + h(bt.journal_entry) + ' đã được sửa tay nên hệ thống không ghi đè.</div>';
  if (d.duoc_ghi && (bt.trang_thai === 'Nháp chờ ghi sổ' || bt.trang_thai === 'Nháp đã sửa tay')) nut += cp2NutPhu('dsmGhi', 'Ghi sổ bút toán ' + bt.journal_entry);
  if (d.duoc_lap && (bt.trang_thai === 'Nháp chờ ghi sổ' || bt.trang_thai === 'Nháp đã sửa tay')) nut += cp2NutPhu('dsmBoNhap', 'Bỏ bản nháp', 1);
  var html =
    '<div class="card" style="padding:12px 14px"><div style="display:flex;align-items:center;gap:8px"><b style="flex:1">Ba con số của tháng</b>' + qcmChipMau(DSM_TT, d.trang_thai, DSM_TT_NHAN[d.trang_thai]) + '</div>' +
    '<div style="display:flex;gap:6px;margin-top:8px;text-align:center">' + [['Meta đã tiêu', qcmTien(d.da_tieu)], ['Đã trừ thẻ', money(d.da_tru) + ' đ'], ['Đã ghi sổ', money(d.da_ghi_so) + ' đ']].map(function (x) {
      return '<div style="flex:1;min-width:0;background:#f8fafc;border-radius:10px;padding:6px 2px"><div style="font-size:13px;color:#667085">' + x[0] + '</div><b style="font-size:14.5px;word-break:break-word">' + x[1] + '</b></div>';
    }).join('') + '</div><div style="font-size:13px;color:#667085;margin-top:6px">Lệch giữa Meta đã tiêu và Đã trừ thẻ có thể do ngưỡng thanh toán, ngày trừ, hoàn tiền, tỷ giá; không tự là sai.</div></div>' +
    (d.thieu && d.thieu.length ? '<div style="background:#fef3f2;color:#b42318;border-radius:12px;padding:9px 12px;font-size:13.5px;margin-bottom:8px">Chưa đủ sao kê: chưa có sao kê ngân hàng cho ngày ' +
      d.thieu.slice(0, 2).map(function (x) { return ngayNgan(x[0]) + ' tới ' + ngayNgan(x[1]); }).join('; ') + (d.thieu.length > 2 ? ' và ' + (d.thieu.length - 2) + ' khoảng nữa' : '') + '. Chờ sao kê về rồi lập.</div>' : '') +
    (d.chung_tu_khac && d.chung_tu_khac.length ? '<div class="card" style="padding:10px 12px"><b style="font-size:14.5px">Chứng từ Meta có sẵn bằng đường khác</b>' +
      '<div style="font-size:13px;color:#667085">Hệ thống không sửa các chứng từ này. Xem từng tờ: nếu nó đã ghi chính các giao dịch dưới đây thì bỏ các giao dịch đó, nếu không thì xác nhận không trùng.</div>' +
      d.chung_tu_khac.map(function (c) {
        return '<div style="border-top:1px solid #f2f4f7;padding:8px 0;font-size:14px"><div style="display:flex;gap:8px;align-items:baseline"><b style="flex:1;min-width:0;word-break:break-all">' + h(c.name) + '</b><b>' + money(c.tien) + ' đ</b></div>' +
          '<div style="color:#667085;font-size:13px">' + ngayNgan(c.ngay) + ' · ' + h((c.mo || '').slice(0, 80)) + '</div>' +
          '<div style="margin-top:6px">' + (c.da_xem ? qcmChipMau(DSM_GD, 'Đã ghi sổ', 'Đã xem, không trùng') : (d.duoc_lap ? '<button type="button" class="btn gh" data-dsmct="' + h(c.doctype + ':' + c.name) + '" style="margin:0;min-height:44px">Không trùng</button>' : '')) + '</div></div>';
      }).join('') + '</div>' : '') +
    '<div style="font-size:15px;font-weight:800;margin:12px 2px 6px">Giao dịch thẻ của tháng (' + gd.length + ')</div>' +
    (gd.length ? '<div class="card" style="padding:4px 12px">' + gd.map(function (g) {
      var q = g.can_quyet;
      var nutQ = '';
      if (q && g.trang_thai === 'Chờ kế toán chọn' && d.duoc_lap) {
        if (q.loai === 'chon') nutQ = '<button type="button" class="btn gh" data-dsmq="' + h(q.khoa_quyet) + '" data-gt="vao" style="margin:0;min-height:44px;flex:1">Là phí Meta</button><button type="button" class="btn gh" data-dsmq="' + h(q.khoa_quyet) + '" data-gt="bo" style="margin:0;min-height:44px;flex:1">Không phải</button>';
        if (q.loai === 'trung') nutQ = '<button type="button" class="btn gh" data-dsmq="' + h(q.khoa_quyet) + '" data-gt="mot" data-lydo="1" style="margin:0;min-height:44px;flex:1">Một giao dịch</button><button type="button" class="btn gh" data-dsmq="' + h(q.khoa_quyet) + '" data-gt="hai" data-lydo="1" style="margin:0;min-height:44px;flex:1">Hai giao dịch</button>';
        if (q.loai === 'dem') { nutQ = ''; for (var i = q.it; i <= q.nhieu; i++) nutQ += '<button type="button" class="btn gh" data-dsmq="' + h(q.khoa_quyet) + '" data-gt="' + i + '" data-lydo="1" style="margin:0;min-height:44px;flex:1">' + i + ' giao dịch</button>'; }
      }
      return '<div style="border-bottom:1px solid #f2f4f7;padding:8px 0"><div style="display:flex;gap:8px;align-items:center;min-height:44px"><span style="flex:1;min-width:0">' +
        '<span style="display:block;font-size:14.5px;font-weight:700">' + h(g.dv) + '</span><span style="display:block;font-size:13px;color:#667085">Thẻ ' + h(g.the4) + ' · giao dịch ' + ngayNgan(g.ngay_gd) +
        ' · ngân hàng ghi ' + ngayNgan(g.ngay_bt) + (g.so_bang_chung > 1 ? ' · có ở ' + g.so_bang_chung + ' bản sao kê' : '') + '</span></span><b style="font-size:14.5px">' + money(g.tien) + ' đ</b></div>' +
        '<div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap">' + qcmChipMau(DSM_GD, g.trang_thai) + (g.purchase_invoice ? '<span style="font-size:13px;color:#667085">' + h(g.purchase_invoice) + '</span>' : '') + '</div>' +
        (q && g.trang_thai === 'Chờ kế toán chọn' ? '<div style="font-size:13px;color:#b42318;margin-top:4px">' + h(q.mo) + '</div><div style="display:flex;gap:6px;margin-top:6px">' + nutQ + '</div>' : '') + '</div>';
    }).join('') + '</div>' : '<div class="emp"><div class="e1">📭</div><div>Tháng này chưa có giao dịch Meta nào trên sao kê thẻ.</div></div>') +
    '<div class="card" style="padding:10px 12px;margin-top:10px"><div style="display:flex;align-items:center;gap:8px"><b style="flex:1;font-size:14.5px">Bút toán của tháng</b>' + qcmChipMau(DSM_BT, bt.trang_thai) + '</div>' +
    ((bt.dong || []).length ? bt.dong.map(function (x) {
      return '<div style="display:flex;gap:8px;min-height:36px;align-items:center;border-top:1px solid #f2f4f7;font-size:14px"><span style="flex:1;min-width:0">' + (x.debit ? 'Nợ ' : 'Có ') + h(cp2BoDuoi(x.account)) + '</span><b>' + money(x.debit || x.credit) + ' đ</b></div>';
    }).join('') : '<div style="font-size:13.5px;color:#667085;margin-top:6px">Không còn giao dịch nào chờ vào bút toán.</div>') +
    (bt.journal_entry ? '<div style="font-size:13px;color:#667085;margin-top:6px">Bút toán đang nối: ' + h(bt.journal_entry) + '</div>' : '') +
    '<div style="font-size:13px;color:#667085;margin-top:6px">Muốn tự hạch toán: lập ở màn Bút toán (Hạch toán tay), ghi rõ FACEBK hoặc Meta ở diễn giải; hệ thống thấy chứng từ đó và dừng lại cho kế toán xem, không ghi trùng.</div>' +
    (nut ? '<div style="margin-top:12px">' + nut + '</div>' : '') + '</div>';
  var b = frame(tieuDe, html);
  b.onclick = async function (e) {
    var n = e.target.closest('[data-dsmq]'), ct = e.target.closest('[data-dsmct]'), id = (e.target.closest('button') || {}).id;
    try {
      if (n) {
        var ly = '';
        if (n.getAttribute('data-lydo')) {
          ly = await hoiChu('Ghi lý do', 'Ghi căn cứ để người sau còn đối chiếu (ví dụ: đối chiếu ảnh sao kê ngân hàng).', '', { nhieu_dong: 1, bat_buoc: 1, nut: 'Xác nhận' });
          if (!ly || !String(ly).trim()) return;
        }
        n.disabled = true;
        await api(DSM_P + 'quyet', { ky: ky, khoa_quyet: n.getAttribute('data-dsmq'), gia_tri: n.getAttribute('data-gt'), ly_do: String(ly || '').trim() });
        toast('Đã ghi quyết định.'); return scrDsMetaThang(ky);
      }
      if (ct) {
        var ly2 = await hoiChu('Xác nhận không trùng', 'Chứng từ ' + ct.getAttribute('data-dsmct').split(':')[1] + ' không ghi các giao dịch thẻ của bảng này?', '', { nhieu_dong: 1, bat_buoc: 1, nut: 'Xác nhận' });
        if (!ly2 || !String(ly2).trim()) return;
        await api(DSM_P + 'quyet', { ky: ky, khoa_quyet: 'ct:' + ct.getAttribute('data-dsmct'), gia_tri: 'da_xem', ly_do: String(ly2).trim() });
        toast('Đã ghi xác nhận.'); return scrDsMetaThang(ky);
      }
      if (id === 'dsmLap') { var r = await api(DSM_P + 'lap', { ky: ky }); toast((r.cap_nhat ? 'Đã cập nhật ' : 'Đã lập nháp ') + r.journal_entry); return scrDsMetaThang(ky); }
      if (id === 'dsmGhi') {
        if (!await xacNhan('Ghi sổ bút toán chi phí Meta tháng ' + ky.slice(5, 7) + '/' + ky.slice(0, 4) + '?\n\nSổ cái ghi Nợ 6417 (và 6427 nếu có phí thẻ), Có 3411.', 'Ghi sổ', 'Ghi sổ')) return;
        await api(DSM_P + 'ghi_so', { ky: ky }); toast('Đã ghi sổ.'); return scrDsMetaThang(ky);
      }
      if (id === 'dsmBoNhap') {
        if (!await xacNhan('Bỏ bút toán nháp tháng này?\n\nBản nháp vẫn nằm trong hệ thống ở trạng thái đã bỏ.', 'Bỏ bản nháp', 'Bỏ')) return;
        await api(DSM_P + 'bo_nhap', { ky: ky }); toast('Đã bỏ bản nháp.'); return scrDsMetaThang(ky);
      }
    } catch (er) { if (n) n.disabled = false; toast(errMsg(er)); }
  };
}

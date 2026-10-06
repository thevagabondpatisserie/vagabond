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
 */
var DSVN = { nhom: 'Tiền bán', tt: '', vendor: '', tim: '', ky: '', tu: '', den: '', cur: '', loc: '', xt: null, tep: null };
var DSVN_NHOM = [['Tiền bán', '💰'], ['Chuyến đi', '🛵'], ['Thẻ tín dụng', '💳']];

function dsvnChip(tt) {
  var mau = {
    'Đã nhận': ['#ecfdf3', '#067647'], 'Cần xử lý': ['#fffaeb', '#b54708'], 'Lỗi tệp': ['#fef3f2', '#b42318'],
    'Đã thấy tiền về': ['#ecfdf3', '#067647'], 'Lệch tiền về': ['#fef3f2', '#b42318'],
    'Chưa thấy tiền về': ['#fffaeb', '#b54708'], 'Không áp dụng': ['#f2f4f7', '#475467'],
    'Chưa đối chiếu': ['#f2f4f7', '#475467'], 'Đã nối': ['#ecfdf3', '#067647'],
    'Nối theo tiền': ['#eff8ff', '#175cd3'], 'Lệch tiền': ['#fef3f2', '#b42318'],
    'Nhiều chứng từ': ['#fffaeb', '#b54708'], 'Không thấy chứng từ': ['#fffaeb', '#b54708'],
    'Chưa nối': ['#f2f4f7', '#475467']
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

/* ---------- Màn 03: trung tâm Đối soát ---------- */
async function scrDsvn() {
  frame('Đối soát nhà cung cấp', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc nguồn đối soát...</div></div>');
  var kq, sk = [];
  try {
    kq = await api('vagabond.doi_soat_vendor.ds', { nhom: DSVN.nhom, trang_thai: DSVN.tt, vendor: DSVN.vendor, tim: DSVN.tim, ky: DSVN.ky, tu: DSVN.tu, den: DSVN.den });
    sk = await api('vagabond.doi_soat_vendor.suc_khoe', {});
  } catch (e) {
    frame('Đối soát nhà cung cấp', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được đối soát. Thử lại sau ít phút.') + '</div></div>');
    return;
  }
  var dem = kq.dem || {};
  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">VIỆC CẦN LÀM</div>' +
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px">' +
    dsvnO('Cần xử lý', dem['Cần xử lý'] || 0, 'nguồn', '#b42318') +
    dsvnO('Chưa thấy tiền về', (dem['Chưa thấy tiền về'] || 0) + (dem['Lệch tiền về'] || 0), 'đợt', '#b54708') +
    dsvnO('Chưa nối đủ', dem['Chưa nối đủ'] || 0, 'nguồn', '#b54708') +
    dsvnO('', dem.tat_ca || 0, 'nguồn đã nhận', '#101828') + '</div>' +
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
        ' · ' + money(n.so_dong) + ' dòng' + (n.kenh_nhan === 'Email' ? ' · email' : '') + '</div>' +
        '<div style="display:flex;justify-content:space-between;gap:8px;align-items:center;margin-top:6px">' +
        '<span style="font-size:13px">' + money(n.thuc_nhan) + ' đ ' + dsvnNhan(n.nhom) + '</span>' +
        '<span style="display:flex;gap:4px;flex-wrap:wrap;justify-content:flex-end">' +
        (n.nhom === 'Tiền bán' ? dsvnChip(n.trang_thai_tien || 'Chưa đối chiếu') : '') +
        (n.so_chua_noi ? dsvnChip(n.so_chua_noi + ' chưa nối') : '') + '</span></div></div>';
    }).join('') + '</div>';
    if (kq.con) html += '<div style="text-align:center;color:#667085;font-size:13px;margin:8px">Đang hiện 50 nguồn mới nhất. Lọc hoặc tìm để thu hẹp.</div>';
  }
  var foot = '<div style="display:flex;gap:8px"><button class="btn gh" id="dsvnEmail" style="margin:0;flex:1">Nhận lại từ email</button>' +
    '<button class="btn" id="dsvnTai" style="margin:0;flex:1">↑ Tải file</button></div>';
  var b = frame('Đối soát nhà cung cấp', html, { footer: foot });
  dsCongCuNoi(b, cc, function (ho, k) {
    if (ho === 'tt') DSVN.tt = k;
    else if (ho === 'ven') DSVN.vendor = k;
    else if (ho === 'ky') DSVN.ky = k;
    else if (ho === 'tim') DSVN.tim = k;
    else if (ho === 'tu') DSVN.tu = k;
    else if (ho === 'den') DSVN.den = k;
    go(scrDsvn, true);
  });
  b.addEventListener('click', function (e) {
    var t = e.target.closest('[data-dsvnnhom]');
    if (t) { DSVN.nhom = t.getAttribute('data-dsvnnhom'); DSVN.vendor = ''; return go(scrDsvn, true); }
    t = e.target.closest('[data-dsvntt]');
    if (t) { DSVN.tt = t.getAttribute('data-dsvntt'); return go(scrDsvn, true); }
    t = e.target.closest('[data-dsvnct]');
    if (t) { DSVN.cur = t.getAttribute('data-dsvnct'); DSVN.loc = ''; return go(scrDsvnCt); }
  });
  document.getElementById('dsvnTai').onclick = function () { DSVN.xt = null; DSVN.tep = null; go(scrDsvnTai); };
  document.getElementById('dsvnEmail').onclick = async function () {
    busy(true);
    try {
      var r = await api('vagabond.doi_soat_vendor.quet_email', { so_ngay: 7 });
      toast(r.so_tep ? 'Đã đọc ' + r.so_tep + ' tệp từ email 7 ngày qua.' : 'Không có tệp mới từ email 7 ngày qua.');
      go(scrDsvn, true);
    } catch (e) { baoTin((e && e.message) || 'Chưa đọc được email. Tải file thay thế.'); }
    finally { busy(false); }
  };
}

function dsvnCongCu(kq) {
  var dem = kq.dem || {};
  return {
    ma: 'dsvn',
    ho: [
      { k: 'tt', tatCa: 'Mọi trạng thái', chon: DSVN.tt, dem: dem, mau: '#b42318',
        ds: [{ k: 'Cần xử lý', ten: 'Cần xử lý' }, { k: 'Chưa thấy tiền về', ten: 'Chờ tiền về' },
          { k: 'Lệch tiền về', ten: 'Lệch tiền về' }, { k: 'Chưa nối đủ', ten: 'Chưa nối đủ' }] },
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

/* ---------- Màn 04: nhận file ---------- */
async function scrDsvnTai() {
  var html = '<div class="card" style="padding:16px;text-align:center">' +
    '<div style="font-size:28px">↑</div><b>Thêm file vendor gửi</b>' +
    '<div style="font-size:13px;color:#667085;margin:4px 0 10px">Excel, CSV, PDF hoặc ZIP. Máy tự nhận ra nguồn và loại báo cáo, không cần chọn.</div>' +
    '<input type="file" id="dsvnFile" accept=".csv,.xlsx,.xlsm,.xls,.pdf,.zip" hidden>' +
    '<button class="btn gh" id="dsvnChon" style="margin:0">Chọn file từ thiết bị</button>' +
    (DSVN.tep ? '<div style="font-size:13px;margin-top:8px">' + h(DSVN.tep.ten) + '</div>' : '') + '</div>';
  var foot = '';
  if (DSVN.xt) {
    var tong_moi = 0;
    DSVN.xt.forEach(function (x) { if (!x.da_co && x.mau) tong_moi += x.so.moi; });
    html += DSVN.xt.map(dsvnTheXemTruoc).join('');
    var co_nhan = DSVN.xt.some(function (x) { return !x.da_co && (x.mau || x.loi.length); });
    if (co_nhan) {
      foot = '<button class="btn" id="dsvnNhan">' + (tong_moi ? 'Nhận ' + money(tong_moi) + ' dòng hợp lệ' : 'Lưu nguồn để xử lý') + '</button>' +
        '<div style="text-align:center;font-size:12.5px;color:#667085;margin-top:6px">Chưa ghi sổ hoặc thanh toán. Dòng lỗi giữ lại để xem.</div>';
    }
  } else {
    html += '<div class="emp"><div class="e1">📄</div><div>Chọn file để xem trước: nguồn, kỳ, số dòng, tổng tiền và dòng lỗi. Chưa nhận gì cho tới khi bấm Nhận.</div></div>';
  }
  var b = frame('Nhận file đối soát', html, foot ? { footer: foot } : {});
  var inp = document.getElementById('dsvnFile');
  document.getElementById('dsvnChon').onclick = function () { inp.click(); };
  inp.onchange = function () { if (inp.files && inp.files[0]) dsvnTaiLen(inp.files[0]); };
  var nb = document.getElementById('dsvnNhan');
  if (nb) nb.onclick = dsvnNhanTep;
  b.onclick = function (e) {
    var t = e.target.closest('[data-dsvnct]');
    if (t) { DSVN.cur = t.getAttribute('data-dsvnct'); DSVN.loc = ''; return go(scrDsvnCt); }
  };
}

function dsvnTheXemTruoc(x) {
  var s = '<div class="card" style="padding:12px 14px">' +
    '<div style="display:flex;justify-content:space-between;gap:8px;align-items:center"><b>' + h(x.ten_mau || 'Chưa nhận ra') + '</b>' +
    (x.da_co ? dsvnChip('Đã nhận trước') : dsvnChip(x.trang_thai)) + '</div>' +
    '<div style="font-size:13px;color:#667085;margin-top:2px">' + h(x.ten_tep || '') + '</div>' +
    (x.doc_lai ? '<div style="font-size:12.5px;color:#175cd3;margin-top:4px">Tệp này đã nhận trước nhưng còn lỗi. Bấm Nhận để đọc lại vào đúng nguồn cũ.</div>' : '');
  if (x.da_co) {
    s += '<div style="font-size:13px;margin-top:8px">Tệp này đã nhận rồi, không nhận lần hai.</div>' +
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
  var nhac = (x.loi || []).concat((x.dong_loi || []).map(function (d) { return 'Dòng ' + d.vi_tri + ': ' + d.ly_do; }));
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
      DSVN.xt = await api('vagabond.doi_soat_vendor.xem_truoc', { file_url: up.file_url });
      go(scrDsvnTai, true);
    } catch (e) { baoTin((e && e.message) || 'Chưa đọc được tệp. Kiểm tra lại tệp vendor gửi.'); }
    finally { busy(false); }
  };
  r.readAsDataURL(file);
}

async function dsvnNhanTep() {
  if (!DSVN.tep) return;
  busy(true);
  try {
    var ra = await api('vagabond.doi_soat_vendor.nhan', { file_url: DSVN.tep.file_url });
    toast('Đã lưu ' + ra.length + ' nguồn. Máy đang đối chiếu hoá đơn và tiền về.');
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
  try { kq = await api('vagabond.doi_soat_vendor.chi_tiet', { name: DSVN.cur, loc: DSVN.loc }); }
  catch (e) {
    frame('Nguồn đối soát', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không mở được nguồn. Quay lại danh sách.') + '</div></div>');
    return;
  }
  var n = kq.nguon, t = kq.them || {};
  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">' + h(n.ten_mau || n.vendor) + ' · ' + dsvnKy(n) + '</div>' +
    '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-top:4px">' +
    '<div style="font-size:24px;font-weight:800">' + money(n.thuc_nhan) + ' đ</div>' + dsvnChip(n.trang_thai) + '</div>' +
    '<div style="font-size:13px;color:#667085">' + dsvnNhan(n.nhom) + ' · ' + money(n.so_dong) + ' dòng · ' +
    (n.kenh_nhan === 'Email' ? 'nhận từ email' : 'tải tay') + '</div></div>';
  html += '<div class="card" style="padding:12px 14px"><b>Từng lớp đối soát</b>' +
    dsvnBuoc('1. Đủ nguồn', n.trang_thai === 'Đã nhận',
      n.trang_thai === 'Đã nhận' ? 'Đọc đủ dòng' + (n.tong_tep != null && n.tong_tep !== 0 ? ', khớp tổng in trên tệp ' + money(n.tong_tep) + ' đ' : '') :
        (n.ly_do || 'Còn dòng hoặc tổng cần xem.')) +
    (n.nhom === 'Tiền bán' ? dsvnBuoc('2. Tiền về ngân hàng', n.trang_thai_tien === 'Đã thấy tiền về' || n.trang_thai_tien === 'Không áp dụng',
      (n.trang_thai_tien || 'Chưa đối chiếu') + (t.tien_ve ? '. ' + t.tien_ve : '') + (n.giao_dich_ngan_hang ? ' (' + n.giao_dich_ngan_hang.split('\n').join(', ') + ')' : '')) : '') +
    dsvnBuoc((n.nhom === 'Tiền bán' ? '3' : '2') + '. Chứng từ', !n.so_chua_noi,
      money(n.so_da_noi) + ' dòng đã nối' + (n.so_chua_noi ? ', ' + money(n.so_chua_noi) + ' dòng chưa nối' : '') +
      (t.hoa_don_ky ? '. ' + t.hoa_don_ky : '')) +
    '<div style="font-size:12.5px;color:#475467;margin-top:6px">Khớp tiền chưa có nghĩa đã hạch toán. Máy chỉ lưu và đối chiếu, không lập phiếu.</div></div>';
  if (t.ky_the) html += dsvnTheTD(t.ky_the);
  if (t.doi_bien_ban) {
    var bb = t.doi_bien_ban;
    html += '<div class="card" style="padding:12px 14px"><b>So với các thông báo ngày đã nhận</b>' +
      '<div style="font-size:13px;margin-top:6px">' + (bb.khop ? '✓ Khớp đủ tiền, phí và thực nhận.' :
        'Lệch: tiền ' + money(bb.lech.tien_hang) + ' đ, phí ' + money(bb.lech.phi) + ' đ, thực nhận ' + money(bb.lech.thuc_nhan) +
        ' đ. Tải đủ thông báo tạm ứng ngày còn thiếu.') + '</div></div>';
  }
  var nhac = (t.loi || []).concat((t.dong_loi || []).map(function (d) { return 'Dòng ' + d.vi_tri + ': ' + d.ly_do; }));
  if (nhac.length) {
    html += '<details class="card" style="padding:12px 14px"><summary style="cursor:pointer;min-height:24px"><b>' + nhac.length +
      ' điều cần xem</b> · ' + h(String(nhac[0]).slice(0, 80)) + '</summary><div style="font-size:13px;margin-top:6px;line-height:1.5">' +
      nhac.slice(0, 60).map(h).join('<br>') + '</div></details>';
  }
  html += '<div class="chips" style="padding:0 2px">' + [['', 'Tất cả dòng'], ['chua_noi', 'Chưa nối'], ['da_noi', 'Đã nối']].map(function (c) {
    return '<div class="chip' + (DSVN.loc === c[0] ? ' on' : '') + '" data-dsvnloc="' + c[0] + '">' + c[1] + '</div>';
  }).join('') + '</div>';
  var dong = kq.dong || [];
  if (!dong.length) {
    html += '<div class="emp"><div class="e1">✓</div><div>Không có dòng nào trong bộ lọc này.</div></div>';
  } else {
    html += '<div class="card" style="padding:0">' + dong.map(dsvnDong).join('') + '</div>';
    if (kq.con) html += '<div style="text-align:center;color:#667085;font-size:13px;margin:8px">Đang hiện 100 dòng đầu. Lọc Chưa nối để xem dòng cần xử lý.</div>';
  }
  var foot = '<button class="btn gh" id="dsvnLai" style="margin:0">Đối chiếu lại hoá đơn và tiền về</button>';
  var b = frame('Nguồn đối soát', html, { footer: foot });
  b.onclick = function (e) {
    var x = e.target.closest('[data-dsvnloc]');
    if (x) { DSVN.loc = x.getAttribute('data-dsvnloc'); return go(scrDsvnCt, true); }
    x = e.target.closest('[data-dsvnsi]');
    if (x && typeof scrDsView === 'function') return go(function () { return scrDsView(x.getAttribute('data-dsvnsi')); });
  };
  document.getElementById('dsvnLai').onclick = async function () {
    busy(true);
    try { await api('vagabond.doi_soat_vendor.doi_chieu_lai', { name: n.name }); toast('Đã đối chiếu lại.'); go(scrDsvnCt, true); }
    catch (e) { baoTin((e && e.message) || 'Chưa đối chiếu được. Thử lại.'); }
    finally { busy(false); }
  };
}

function dsvnBuoc(ten, xong, mo_ta) {
  return '<div style="display:flex;gap:10px;align-items:flex-start;padding:8px 0;border-bottom:1px solid #f2f4f7">' +
    '<span style="flex:0 0 22px;height:22px;border-radius:50%;text-align:center;line-height:22px;font-size:13px;font-weight:700;' +
    (xong ? 'background:#ecfdf3;color:#067647">✓' : 'background:#fffaeb;color:#b54708">!') + '</span>' +
    '<div><b style="font-size:14px">' + h(ten) + '</b><div style="font-size:13px;color:#667085">' + h(mo_ta) + '</div></div></div>';
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
    (d.ghi_chu_khop ? '<div style="font-size:12px;color:#667085;margin-top:2px">' + h(d.ghi_chu_khop) + '</div>' : '') + '</div>';
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

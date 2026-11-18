/* v674 Bảng kê chi phí trả trước 242 (anh Việt 18/11/2026, Khải báo thiếu bảng kê 242).
   Kế toán xem mọi khoản đã vào 242 (hoá đơn mua đi thẳng 242, phiếu xuất công cụ dụng cụ
   phân bổ nhiều tháng, bút toán), khai cách phân bổ, và mỗi tháng lập MỘT bút toán nháp
   phân bổ rồi ghi sổ. Đường tay: phân bổ tay một khoản, gắn khoản cho dòng Có 242 lập tay.
   Máy chủ chốt mọi con số (QT-19): màn chỉ hiện. */
var CP2_P = 'vagabond.chi_phi_242.';
var CP2 = { tt: '', nguon: '', khoang: 'nam', tim: '', dl: null, dm: null, luot: 0 };
var CP2_TT = [
  ['', 'Tất cả'], ['Chờ khai số tháng', 'Chờ khai'], ['Đang phân bổ', 'Đang phân bổ'],
  ['Đã phân bổ xong', 'Đã xong'], ['Không phân bổ', 'Không phân bổ'], ['Chứng từ gốc đã huỷ', 'Gốc đã huỷ']
];
var CP2_NGUON = [['', 'Mọi nguồn'], ['Phiếu xuất CCDC', 'Phiếu xuất CCDC'], ['Hoá đơn mua', 'Hoá đơn mua'], ['Bút toán', 'Bút toán']];
var CP2_KHOANG = [['nam', 'Năm nay'], ['3thang', '3 tháng'], ['thang', 'Tháng này'], ['', 'Tất cả']];
/* Màu trạng thái theo AGENTS.md 2b.3: xanh xong, vàng chờ, đỏ cần xử, xám huỷ; màu luôn kèm chữ. */
var CP2_MAU = {
  'Chờ khai số tháng': ['#fef3f2', '#b42318', 'Chờ khai'],
  'Đang phân bổ': ['#fffaeb', '#b54708', 'Đang phân bổ'],
  'Đã phân bổ xong': ['#ecfdf3', '#067647', 'Đã xong'],
  'Không phân bổ': ['#f2f4f7', '#475467', 'Không phân bổ'],
  'Chứng từ gốc đã huỷ': ['#f2f4f7', '#475467', 'Gốc đã huỷ']
};
var CP2_IC = { 'Phiếu xuất CCDC': '📦', 'Hoá đơn mua': '🧾', 'Bút toán': '📒' };

function cp2Tien(n) { return money(n) + ' đ'; }
/* Bỏ đuôi viết tắt công ty (" - TV") khi hiện tên bộ phận, tài khoản: không hiện mã nội bộ (2b). */
function cp2BoDuoi(s) { return String(s || '').replace(/\s-\s[A-Z]{1,5}$/, ''); }
function cp2Thang(ky) { return ky ? ky.slice(5, 7) + '/' + ky.slice(0, 4) : ''; }
function cp2KyNay() { var d = new Date(); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0'); }
function cp2CongThang(ky, n) {
  var y = parseInt(ky.slice(0, 4), 10), m = parseInt(ky.slice(5, 7), 10) - 1 + n;
  y += Math.floor(m / 12); m = ((m % 12) + 12) % 12;
  return y + '-' + String(m + 1).padStart(2, '0');
}
function cp2Chip(attr, gt, chu, on, so) {
  return '<button type="button" ' + attr + '="' + h(gt) + '" aria-pressed="' + (on ? 'true' : 'false') + '" style="flex:0 0 auto;min-height:44px;padding:0 14px;border-radius:22px;' +
    'border:1px solid ' + (on ? '#0B7C93' : '#d0d5dd') + ';background:' + (on ? '#e6f8fb' : '#fff') + ';font:inherit;font-size:14px;font-weight:' + (on ? 800 : 600) +
    ';color:' + (on ? '#05323C' : '#344054') + '">' + h(chu) + (so !== undefined ? ' <b>' + so + '</b>' : '') + '</button>';
}
function cp2HangChip(html) { return '<div style="display:flex;gap:8px;overflow-x:auto;padding:2px 2px 8px">' + html + '</div>'; }
function cp2ChipTT(tt) {
  var m = CP2_MAU[tt] || ['#f2f4f7', '#475467', tt];
  return '<span style="flex:0 0 auto;display:inline-flex;align-items:center;min-height:28px;padding:0 10px;border-radius:14px;background:' + m[0] +
    ';color:' + m[1] + ';font-size:13px;font-weight:700;white-space:nowrap">' + h(m[2]) + '</span>';
}
function cp2NutChinh(id, chu, phu) {
  return '<button type="button" class="btn" id="' + id + '" style="margin:0;min-height:48px">' + h(chu) + '</button>' +
    (phu ? '<div style="font-size:13px;color:#667085;text-align:center;margin-top:6px">' + h(phu) + '</div>' : '');
}
function cp2NutPhu(id, chu, nguy) {
  return '<button type="button" class="btn gh" id="' + id + '" style="margin:8px 0 0;min-height:48px' + (nguy ? ';color:#b42318;border-color:#fda29b' : '') + '">' + h(chu) + '</button>';
}
function cp2Dong(nhan, gt) {
  return '<div style="display:flex;gap:10px;min-height:32px;align-items:baseline;border-top:1px solid #f2f4f7;padding:6px 0">' +
    '<span style="flex:0 0 42%;font-size:13.5px;color:#667085">' + h(nhan) + '</span><span style="flex:1;min-width:0;font-size:14.5px;font-weight:600">' + gt + '</span></div>';
}
async function cp2DanhMuc() { if (!CP2.dm) CP2.dm = await api(CP2_P + 'danh_muc'); return CP2.dm; }

async function scrCp242(moKhoan) {
  var tieuDe = 'Bảng kê chi phí trả trước';
  frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc bảng kê 242...</div></div>');
  /* Đổi chip, gõ tìm liên tiếp: lượt trả lời cũ đến muộn không vẽ đè lượt mới (H8 loại 8). */
  var luot = CP2.luot = CP2.luot + 1, dl;
  try { dl = await api(CP2_P + 'danh_sach', { trang_thai: CP2.tt, nguon: CP2.nguon, khoang: CP2.khoang, tu_khoa: CP2.tim }); }
  catch (e) {
    if (luot !== CP2.luot) return;
    frame(tieuDe, '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e) || 'Không đọc được bảng kê.') + '</div>' +
      '<button class="btn gh" id="cp2Lai" style="margin-top:12px;min-height:48px">Thử lại</button></div>');
    var lai = document.getElementById('cp2Lai');
    if (lai) lai.onclick = function () { scrCp242(); };
    return;
  }
  if (luot !== CP2.luot) return;
  CP2.dl = dl;
  var dem = dl.dem || { trang_thai: {}, nguon: {} }, t = dl.tong || {};
  var html =
    '<div class="card" style="padding:12px 14px"><div style="display:flex;gap:8px;text-align:center">' +
    [['Nguyên giá', t.nguyen_gia], ['Đã phân bổ', t.da_phan_bo], ['Còn lại', t.con_lai]].map(function (x) {
      return '<div style="flex:1;min-width:0"><div style="font-size:13px;color:#667085">' + x[0] + '</div><div style="font-size:15px;font-weight:800;white-space:nowrap">' + cp2Tien(x[1] || 0) + '</div></div>';
    }).join('') + '</div>' +
    ((CP2.tt || CP2.nguon || CP2.tim) ? '<div style="font-size:13px;color:#0B7C93;text-align:center;margin-top:6px">Tổng theo bộ lọc đang chọn</div>' : '') + '</div>' +
    cp2HangChip(CP2_TT.map(function (x) { return cp2Chip('data-cp2tt', x[0], x[1], CP2.tt === x[0], dem.trang_thai[x[0]] || 0); }).join('')) +
    cp2HangChip(CP2_NGUON.map(function (x) { return cp2Chip('data-cp2ng', x[0], x[1], CP2.nguon === x[0], dem.nguon[x[0]] || 0); }).join('')) +
    cp2HangChip(CP2_KHOANG.map(function (x) { return cp2Chip('data-cp2kh', x[0], x[1], CP2.khoang === x[0]); }).join('')) +
    '<input id="cp2Tim" type="search" value="' + h(CP2.tim) + '" placeholder="Tìm diễn giải, số chứng từ, bộ phận" style="width:100%;box-sizing:border-box;min-height:48px;border:1px solid #d0d5dd;border-radius:12px;padding:0 14px;font:inherit;font-size:16px;margin-bottom:8px">' +
    (dl.rows.length ? '<div class="card" style="padding:4px 12px">' + dl.rows.map(function (r) {
      return '<button type="button" data-cp2k="' + h(r.name) + '" style="display:flex;gap:10px;align-items:center;width:100%;min-height:64px;border:0;border-bottom:1px solid #f2f4f7;background:none;font:inherit;text-align:left;padding:8px 0">' +
        (r.nguon_loai === 'Bút toán' ? '<span style="flex:0 0 44px;width:44px;height:44px;border-radius:10px;background:#f2f4f7;display:flex;align-items:center;justify-content:center;font-size:20px">📒</span>' : anhMon(r.anh)) +
        '<span style="flex:1;min-width:0"><span style="display:block;font-size:15px;font-weight:700">' + h(r.dien_giai || r.nguon_so) + '</span>' +
        '<span style="display:block;font-size:13px;color:#667085">' + (CP2_IC[r.nguon_loai] || '📄') + ' ' + h(r.nguon_so) + ' · ' + ngayNgan(r.ngay) + '</span>' +
        '<span style="display:block;font-size:13px;color:#344054">Còn ' + cp2Tien(r.con_lai) + ' / ' + cp2Tien(r.nguyen_gia) + (r.so_ky ? ' · ' + r.so_ky + ' tháng' : '') + '</span></span>' +
        cp2ChipTT(r.trang_thai_hien) + '</button>';
    }).join('') + '</div>' : (CP2.tt || CP2.nguon || CP2.tim || CP2.khoang)
      ? '<div class="emp"><div class="e1">🔎</div><div>Không có khoản nào khớp bộ lọc.</div><button class="btn gh" id="cp2BoLoc" style="margin-top:12px;min-height:48px">Bỏ lọc, xem tất cả</button></div>'
      : '<div class="emp"><div class="e1">📭</div><div>Chưa có khoản nào vào 242. Khoản sẽ tự hiện khi hoá đơn mua đi 242 được ghi sổ hoặc kho ghi sổ phiếu xuất công cụ dụng cụ phân bổ nhiều tháng.</div></div>') +
    (dl.co_chua_gan && dl.co_chua_gan.length ? '<button type="button" id="cp2ChuaGan" style="display:block;width:100%;min-height:48px;margin-top:10px;border:1px solid #fecdca;border-radius:12px;background:#fef3f2;color:#b42318;font:inherit;font-size:14px;font-weight:700;text-align:left;padding:8px 12px">⚠️ ' +
      dl.co_chua_gan.length + ' dòng Có 242 trên bút toán đã ghi sổ chưa gắn khoản. Chạm để gắn.</button>' : '');
  var ky = cp2CongThang(cp2KyNay(), -1);
  var b = frame(tieuDe, html, { footer: dl.duoc_lap || dl.duoc_ghi ? '<button class="btn" id="cp2Thang" style="margin:0;min-height:48px">Phân bổ tháng ' + cp2Thang(ky) + '</button>' : '' });
  var o = document.getElementById('cp2Tim');
  if (o) o.onchange = function () { CP2.tim = o.value.trim(); scrCp242(); };
  var nt = document.getElementById('cp2Thang');
  if (nt) nt.onclick = function () { cp2SheetThang(ky); };
  var bl = document.getElementById('cp2BoLoc');
  if (bl) bl.onclick = function () { CP2.tt = ''; CP2.nguon = ''; CP2.tim = ''; CP2.khoang = ''; scrCp242(); };
  var cg = document.getElementById('cp2ChuaGan');
  if (cg) cg.onclick = function () { cp2SheetChuaGan(dl); };
  b.onclick = function (e) {
    var n;
    if ((n = e.target.closest('[data-cp2tt]'))) { CP2.tt = n.getAttribute('data-cp2tt'); return scrCp242(); }
    if ((n = e.target.closest('[data-cp2ng]'))) { CP2.nguon = n.getAttribute('data-cp2ng'); return scrCp242(); }
    if ((n = e.target.closest('[data-cp2kh]'))) { CP2.khoang = n.getAttribute('data-cp2kh'); return scrCp242(); }
    if ((n = e.target.closest('[data-cp2k]'))) return cp2ChiTiet(n.getAttribute('data-cp2k'));
  };
  if (moKhoan) cp2ChiTiet(moKhoan);
}

async function cp2ChiTiet(ten) {
  var d;
  try { d = await api(CP2_P + 'chi_tiet', { ten: ten }); } catch (e) { return toast(errMsg(e) || 'Không mở được khoản này.'); }
  var lich = d.lich || [], lan = d.lan_phan_bo || [];
  var ov = crmMoSheet(
    '<div style="display:flex;gap:10px;align-items:center">' + (d.mon && d.mon.length ? anhMon(d.mon[0].anh) : '<span style="font-size:24px">' + (CP2_IC[d.nguon_loai] || '📄') + '</span>') +
    '<b style="flex:1;min-width:0;font-size:17px">' + h(d.dien_giai || d.nguon_so) + '</b>' + cp2ChipTT(d.trang_thai_hien) + '</div>' +
    '<div style="display:flex;gap:8px;text-align:center;margin:12px 0 6px">' + [['Nguyên giá', d.nguyen_gia], ['Đã phân bổ', d.da_phan_bo], ['Còn lại', d.con_lai]].map(function (x) {
      return '<div style="flex:1;min-width:0;background:#f8fafc;border-radius:10px;padding:8px 4px"><div style="font-size:13px;color:#667085">' + x[0] + '</div><div style="font-size:15px;font-weight:800">' + cp2Tien(x[1]) + '</div></div>';
    }).join('') + '</div>' +
    cp2Dong('Chứng từ gốc', h(d.nguon_loai + ' ' + d.nguon_so)) + cp2Dong('Ngày ghi nhận', ngayNgan(d.ngay)) +
    cp2Dong('Bộ phận chịu', h(cp2BoDuoi(d.bo_phan) || 'Chưa chọn')) + cp2Dong('Tài khoản chi phí', h(cp2BoDuoi(d.tk_chi_phi) || 'Chưa chọn')) +
    cp2Dong('Phân bổ', d.so_ky ? h(d.so_ky + ' tháng, từ tháng ' + cp2Thang(d.ky_bat_dau)) : '<span style="color:#b42318">Chưa khai</span>') +
    (d.da_phan_bo_truoc ? cp2Dong('Đã phân bổ trước', cp2Tien(d.da_phan_bo_truoc)) : '') +
    (d.ghi_chu ? cp2Dong('Ghi chú', h(d.ghi_chu)) : '') +
    (d.mon && d.mon.length ? '<div style="font-size:14px;font-weight:800;margin:12px 0 4px">Hàng trong phiếu (' + d.mon.length + ' món)</div>' + d.mon.map(function (m) {
      return '<div style="display:flex;gap:10px;align-items:center;min-height:52px;border-top:1px solid #f2f4f7">' + anhMon(m.anh) +
        '<span style="flex:1;min-width:0;font-size:14.5px;font-weight:600">' + h(m.ten) + '<span style="display:block;font-size:13px;color:#667085;font-weight:500">' + money(m.sl) + ' ' + h(m.dvt || '') + ' · ' + cp2Tien(m.tien) + '</span></span></div>';
    }).join('') : '') +
    (lan.length ? '<div style="font-size:14px;font-weight:800;margin:12px 0 4px">Các lần phân bổ (' + lan.length + ')</div>' + lan.map(function (x) {
      var tt = x.huy ? ['Đã bỏ', '#475467', '#f2f4f7'] : x.docstatus === 1 ? ['Đã ghi sổ', '#067647', '#ecfdf3'] : ['Nháp', '#b54708', '#fffaeb'];
      return '<div style="display:flex;gap:8px;align-items:center;min-height:44px;border-top:1px solid #f2f4f7;font-size:14px"><span style="flex:1;min-width:0">' + h(x.je) + ' · ' + ngayNgan(x.ngay) +
        (x.may_lap ? '' : ' · tay') + '</span><b>' + cp2Tien(x.tien) + '</b><span style="padding:2px 8px;border-radius:12px;font-size:13px;font-weight:700;color:' + tt[1] + ';background:' + tt[2] + '">' + tt[0] + '</span></div>';
    }).join('') : '') +
    (lich.length ? '<button type="button" id="cp2XemLich" class="btn gh" style="margin:10px 0 0;min-height:44px">Xem lịch ' + lich.length + ' tháng</button><div id="cp2Lich"></div>' : '') +
    (d.duoc_lap && d.trang_thai_hien !== 'Chứng từ gốc đã huỷ' ? '<div style="margin-top:14px">' + cp2NutChinh('cp2Khai', d.so_ky ? 'Sửa cách phân bổ' : 'Khai cách phân bổ') +
      (d.con_lai > 0 && d.bo_phan && d.tk_chi_phi ? cp2NutPhu('cp2Tay', 'Phân bổ tay khoản này') : '') +
      (d.trang_thai_hien !== 'Không phân bổ' ? cp2NutPhu('cp2Ngung', 'Không phân bổ khoản này', 1) : '') + '</div>' : ''));
  var xl = ov.querySelector('#cp2XemLich');
  if (xl) xl.onclick = function () {
    ov.querySelector('#cp2Lich').innerHTML = lich.map(function (x) {
      return '<div style="display:flex;min-height:36px;align-items:center;border-top:1px solid #f2f4f7;font-size:14px"><span style="flex:1">Tháng ' + cp2Thang(x.ky) + '</span><b>' + cp2Tien(x.so_tien) + '</b></div>';
    }).join('');
    xl.remove();
  };
  var k = ov.querySelector('#cp2Khai');
  if (k) k.onclick = function () { ov.remove(); cp2SheetKhai(d); };
  var t = ov.querySelector('#cp2Tay');
  if (t) t.onclick = function () { ov.remove(); cp2SheetTay(d); };
  var n = ov.querySelector('#cp2Ngung');
  if (n) n.onclick = async function () {
    var ly = await hoiChu('Không phân bổ khoản này', 'Khoản sẽ không vào bút toán phân bổ tháng của hệ thống.', '',
      { nhieu_dong: 1, bat_buoc: 1, goi_y: 'Lý do, ví dụ: tiền thuê kế toán tự phân bổ', nut: 'Xác nhận' });
    if (!ly || !String(ly).trim()) return;
    ly = String(ly).trim();
    try { await api(CP2_P + 'ngung', { ten: d.name, ly_do: ly }); ov.remove(); toast('Đã chuyển khoản sang Không phân bổ.'); scrCp242(); }
    catch (e) { toast(errMsg(e)); }
  };
}

async function cp2SheetKhai(d) {
  var dm;
  try { dm = await cp2DanhMuc(); } catch (e) { return toast(errMsg(e)); }
  var st = { soKy: d.so_ky || null, kyBd: d.ky_bat_dau || (d.ngay || '').slice(0, 7), boPhan: d.bo_phan, tk: d.tk_chi_phi,
    daTruoc: d.da_phan_bo_truoc || 0, ghiChu: d.ghi_chu || '' };
  var chonSoKy = d.chon_so_ky || [2, 3, 6, 12, 18, 24, 36];
  var kyGhi = (d.ngay || '').slice(0, 7);
  function nhanCua(ds, v) { var x = (ds || []).filter(function (i) { return i.value === v; })[0]; return x ? x.label : v; }
  function ve() {
    var kyChip = [kyGhi, cp2CongThang(kyGhi, 1)].filter(function (x, i, a) { return x && a.indexOf(x) === i; });
    return '<div style="font-size:17px;font-weight:800">Cách phân bổ</div><div style="font-size:13.5px;color:#667085;margin-bottom:6px">' + h(d.dien_giai || d.nguon_so) + ' · ' + cp2Tien(d.nguyen_gia) + '</div>' +
      '<div style="font-size:14px;font-weight:700;margin-top:8px">Số tháng phân bổ</div>' +
      cp2HangChip(chonSoKy.map(function (n) { return cp2Chip('data-ksk', String(n), n + ' tháng', st.soKy === n); }).join('')) +
      '<label style="display:block;font-size:13.5px;color:#667085">Số khác (1 tới ' + (d.so_ky_toi_da || 36) + ' tháng)' +
      '<input id="kSkKhac" type="number" inputmode="numeric" min="1" max="' + (d.so_ky_toi_da || 36) + '" value="' + (st.soKy && chonSoKy.indexOf(st.soKy) < 0 ? st.soKy : '') + '" style="display:block;width:100%;box-sizing:border-box;min-height:48px;margin-top:4px;border:1px solid #d0d5dd;border-radius:12px;padding:0 12px;font:inherit;font-size:16px"></label>' +
      '<div style="font-size:14px;font-weight:700;margin-top:10px">Tháng bắt đầu</div>' +
      cp2HangChip(kyChip.map(function (k) { return cp2Chip('data-kky', k, 'Tháng ' + cp2Thang(k), st.kyBd === k); }).join('')) +
      '<label style="display:block;font-size:13.5px;color:#667085">Tháng khác<input id="kKyKhac" type="month" value="' + h(kyChip.indexOf(st.kyBd) < 0 ? st.kyBd : '') + '" style="display:block;width:100%;box-sizing:border-box;min-height:48px;margin-top:4px;border:1px solid #d0d5dd;border-radius:12px;padding:0 12px;font:inherit;font-size:16px"></label>' +
      '<div style="font-size:14px;font-weight:700;margin-top:10px">Bộ phận chịu chi phí</div>' +
      '<div style="margin-top:4px">' + crmNutChon('data-kbp="1"', '🏛️', st.boPhan ? h(nhanCua(dm.bo_phan, st.boPhan)) : 'Chọn bộ phận dùng công cụ này') + '</div>' +
      '<div style="font-size:14px;font-weight:700;margin-top:10px">Tài khoản chi phí</div>' +
      '<div style="margin-top:4px">' + crmNutChon('data-ktk="1"', '🧮', st.tk ? h(nhanCua(dm.tai_khoan, st.tk)) : 'Chọn tài khoản chi phí') + '</div>' +
      '<div style="font-size:13px;color:#667085;margin-top:4px">Bếp, sản xuất 6273; bán hàng 6413; quản lý 6423.</div>' +
      '<label style="display:block;margin-top:10px;font-size:14px;font-weight:700">Đã phân bổ trước khi lên bảng kê (đ)<span style="display:block;font-size:13px;font-weight:500;color:#667085">Phần đã chia vào chi phí ở sổ cũ, ngoài hệ thống. Không có thì để 0.</span>' +
      '<input id="kDaTruoc" type="number" inputmode="numeric" min="0" value="' + (st.daTruoc || 0) + '" style="display:block;width:100%;box-sizing:border-box;min-height:48px;margin-top:4px;border:1px solid #d0d5dd;border-radius:12px;padding:0 12px;font:inherit;font-size:16px"></label>' +
      '<label style="display:block;margin-top:10px;font-size:14px;font-weight:700">Ghi chú<input id="kGhiChu" value="' + h(st.ghiChu) + '" style="display:block;width:100%;box-sizing:border-box;min-height:48px;margin-top:4px;border:1px solid #d0d5dd;border-radius:12px;padding:0 12px;font:inherit;font-size:16px"></label>' +
      '<div style="margin-top:14px">' + cp2NutChinh('kLuu', 'Lưu cách phân bổ', 'Máy tính lịch từng tháng; bút toán tháng do Kế toán lập và ghi sổ.') + '</div>';
  }
  var ov = crmMoSheet('<div id="kBox">' + ve() + '</div>');
  function doc() {
    var sk = ov.querySelector('#kSkKhac').value.trim(); if (sk) st.soKy = parseInt(sk, 10) || null;
    var kk = ov.querySelector('#kKyKhac').value.trim(); if (kk) st.kyBd = kk;
    var dt = ov.querySelector('#kDaTruoc').value.trim(); st.daTruoc = dt === '' ? 0 : Number(dt);
    st.ghiChu = ov.querySelector('#kGhiChu').value;
  }
  function veLai() { ov.querySelector('#kBox').innerHTML = ve(); }
  ov.addEventListener('click', async function (e) {
    var n;
    if ((n = e.target.closest('[data-ksk]'))) { doc(); st.soKy = parseInt(n.getAttribute('data-ksk'), 10); ov.querySelector('#kSkKhac').value = ''; return veLai(); }
    if ((n = e.target.closest('[data-kky]'))) { doc(); st.kyBd = n.getAttribute('data-kky'); return veLai(); }
    if (e.target.closest('[data-kbp]')) { doc(); return xktSheetTim('Chọn bộ phận chịu chi phí', dm.bo_phan.map(function (x) { return { value: x.value, label: x.label, phu: x.phu, icon: '🏛️' }; }), st.boPhan, function (it) { st.boPhan = it.value; veLai(); }); }
    if (e.target.closest('[data-ktk]')) { doc(); return xktSheetTim('Chọn tài khoản chi phí', dm.tai_khoan.map(function (x) { return { value: x.value, label: x.label, phu: x.phu, icon: '🧮' }; }), st.tk, function (it) { st.tk = it.value; veLai(); }); }
    if (e.target.closest('#kLuu')) {
      doc();
      if (!st.soKy) return toast('Chưa chọn số tháng phân bổ.');
      if (!st.kyBd) return toast('Chưa chọn tháng bắt đầu.');
      if (!st.boPhan) return toast('Chưa chọn bộ phận chịu chi phí.');
      if (!st.tk) return toast('Chưa chọn tài khoản chi phí.');
      var nut = e.target.closest('#kLuu'); nut.disabled = true;
      try {
        await api(CP2_P + 'khai', { ten: d.name, so_ky: st.soKy, ky_bat_dau: st.kyBd, bo_phan: st.boPhan, tk_chi_phi: st.tk, da_phan_bo_truoc: st.daTruoc, ghi_chu: st.ghiChu });
        ov.remove(); toast('Đã lưu cách phân bổ.'); scrCp242(d.name);
      } catch (er) { nut.disabled = false; toast(errMsg(er)); }
    }
  });
}

async function cp2SheetTay(d) {
  var ky = cp2KyNay();
  var ov = crmMoSheet('<div style="font-size:17px;font-weight:800">Phân bổ tay</div><div style="font-size:13.5px;color:#667085">' + h(d.dien_giai || d.nguon_so) + ' · còn ' + cp2Tien(d.con_lai) + '</div>' +
    '<label style="display:block;margin-top:10px;font-size:14px;font-weight:700">Tháng hạch toán<input id="tKy" type="month" value="' + ky + '" style="display:block;width:100%;box-sizing:border-box;min-height:48px;margin-top:4px;border:1px solid #d0d5dd;border-radius:12px;padding:0 12px;font:inherit;font-size:16px"></label>' +
    '<label style="display:block;margin-top:10px;font-size:14px;font-weight:700">Số tiền phân bổ (đ)<input id="tTien" type="number" inputmode="numeric" min="1" value="' + (d.con_lai || '') + '" style="display:block;width:100%;box-sizing:border-box;min-height:48px;margin-top:4px;border:1px solid #d0d5dd;border-radius:12px;padding:0 12px;font:inherit;font-size:16px"></label>' +
    '<div style="font-size:13px;color:#667085;margin-top:6px">Nợ ' + h(cp2BoDuoi(d.tk_chi_phi)) + ' / Có 242, bộ phận ' + h(cp2BoDuoi(d.bo_phan)) + '. Bút toán riêng, không đụng bút toán tháng của máy.</div>' +
    '<div style="margin-top:14px">' + cp2NutChinh('tLap', 'Lập bút toán nháp') + (d.duoc_ghi ? cp2NutPhu('tGhi', 'Lập và ghi sổ ngay') : '') + '</div>');
  async function lam(ghi) {
    var k = ov.querySelector('#tKy').value, tien = Number(ov.querySelector('#tTien').value || 0);
    if (!k) return toast('Chưa chọn tháng.');
    if (!(tien > 0)) return toast('Số tiền phải lớn hơn 0.');
    try {
      var r = await api(CP2_P + 'phan_bo_tay', { ten: d.name, ky: k, so_tien: tien, ghi_so: ghi ? 1 : 0 });
      ov.remove(); toast((ghi ? 'Đã ghi sổ ' : 'Đã lập nháp ') + r.journal_entry); scrCp242(d.name);
    } catch (e) { toast(errMsg(e)); }
  }
  ov.querySelector('#tLap').onclick = function () { lam(false); };
  var g = ov.querySelector('#tGhi'); if (g) g.onclick = function () { lam(true); };
}

async function cp2SheetChuaGan(dl) {
  var khoan = (dl.rows || []).filter(function (r) { return r.trang_thai_hien !== 'Chứng từ gốc đã huỷ'; });
  var ov = crmMoSheet('<div style="font-size:17px;font-weight:800">Dòng Có 242 chưa gắn khoản</div>' +
    '<div style="font-size:13.5px;color:#667085;margin-bottom:6px">Bút toán lập tay ghi Có 242 mà chưa chọn khoản thì máy không biết khoản nào đã phân bổ, nên chưa lập bút toán tháng. Gắn đúng khoản cho từng dòng.</div>' +
    dl.co_chua_gan.map(function (x) {
      return '<div style="display:flex;gap:8px;align-items:center;min-height:56px;border-top:1px solid #f2f4f7"><span style="flex:1;min-width:0;font-size:14px"><b>' + h(x.je) + '</b> · ' + ngayNgan(x.ngay) +
        '<span style="display:block;color:#667085;font-size:13px">' + h((x.dien_giai || '').slice(0, 80)) + '</span></span><b style="font-size:14px">' + cp2Tien(x.tien) + '</b>' +
        (dl.duoc_lap ? '<button type="button" class="btn gh" data-gan="' + h(x.dong) + '" style="margin:0;min-height:44px;flex:0 0 auto;width:auto;padding:0 12px">Gắn khoản</button>' : '') + '</div>';
    }).join(''));
  ov.addEventListener('click', function (e) {
    var n = e.target.closest('[data-gan]');
    if (!n) return;
    var dong = n.getAttribute('data-gan');
    xktSheetTim('Chọn khoản 242', khoan.map(function (r) { return { value: r.name, label: r.dien_giai || r.nguon_so, phu: r.nguon_so + ' · còn ' + cp2Tien(r.con_lai), icon: CP2_IC[r.nguon_loai] || '📄' }; }), '', async function (it) {
      try { await api(CP2_P + 'gan_khoan', { dong: dong, ten: it.value }); ov.remove(); toast('Đã gắn khoản.'); scrCp242(); }
      catch (er) { toast(errMsg(er)); }
    });
  });
}

async function cp2SheetThang(ky) {
  var d;
  try { d = await api(CP2_P + 'xem_thang', { ky: ky }); } catch (e) { return toast(errMsg(e)); }
  var cac = d.dong || [], cho = d.cho_khai || [];
  var mauTT = { 'Chưa lập': ['#f2f4f7', '#475467'], 'Nháp chờ ghi sổ': ['#fffaeb', '#b54708'], 'Nháp đã sửa tay': ['#fef3f2', '#b42318'], 'Đã ghi sổ': ['#ecfdf3', '#067647'], 'Đã bỏ nháp': ['#f2f4f7', '#475467'] };
  var m = mauTT[d.trang_thai] || mauTT['Chưa lập'];
  var nut = '';
  if (d.trang_thai === 'Nháp đã sửa tay') {
    nut = '<div style="font-size:13.5px;color:#b42318;margin:6px 0">Bút toán nháp ' + h(d.journal_entry) + ' đã được sửa tay nên hệ thống không ghi đè. ' +
      (d.nhap_cu ? 'Bản nháp đã cũ so với số hiện tại: ' + h(d.nhap_cu) + '. Bỏ bản nháp rồi lập lại.' : 'Ghi sổ bản đã sửa, hoặc bỏ bản nháp rồi lập lại.') + '</div>' +
      (d.duoc_ghi && !d.nhap_cu ? cp2NutChinh('thGhi', 'Ghi sổ bản đã sửa') : '') + (d.duoc_lap ? cp2NutPhu('thBo', 'Bỏ bản nháp', 1) : '');
  } else {
    if (d.duoc_lap && cac.length && !d.tuong_lai) nut += cp2NutChinh('thLap', d.trang_thai === 'Nháp chờ ghi sổ' ? 'Cập nhật bản nháp' : 'Lập bút toán nháp', 'Hệ thống không tự ghi sổ.');
    if (d.nhap_cu && d.trang_thai === 'Nháp chờ ghi sổ') nut += '<div style="font-size:13.5px;color:#b42318;margin:6px 0">Bản nháp ' + h(d.journal_entry) + ' đã cũ so với số hiện tại: ' + h(d.nhap_cu) + '. Bấm Cập nhật bản nháp rồi mới ghi sổ.</div>';
    if (d.duoc_ghi && !d.nhap_cu && d.trang_thai === 'Nháp chờ ghi sổ') nut += cp2NutPhu('thGhi', 'Ghi sổ bút toán ' + d.journal_entry);
    if (d.duoc_lap && d.trang_thai === 'Nháp chờ ghi sổ') nut += cp2NutPhu('thBo', 'Bỏ bản nháp', 1);
  }
  var ov = crmMoSheet('<div style="display:flex;align-items:center;gap:8px"><b style="flex:1;font-size:17px">Phân bổ tháng ' + cp2Thang(ky) + '</b>' +
    '<span style="padding:4px 10px;border-radius:14px;font-size:13px;font-weight:700;background:' + m[0] + ';color:' + m[1] + '">' + h(d.trang_thai) + '</span></div>' +
    cp2HangChip([cp2CongThang(cp2KyNay(), -1), cp2KyNay()].map(function (k) { return cp2Chip('data-thky', k, 'Tháng ' + cp2Thang(k), k === ky); }).join('')) +
    '<div style="font-size:15px;margin:4px 0 6px">Cần phân bổ: <b>' + cp2Tien(d.tong) + '</b> · ' + cac.length + ' khoản' + (d.journal_entry ? ' · bút toán ' + h(d.journal_entry) : '') + '</div>' +
    cac.slice(0, 5).map(function (c) {
      return '<div style="display:flex;gap:8px;min-height:44px;align-items:center;border-top:1px solid #f2f4f7;font-size:14px"><span style="flex:1;min-width:0">' + h((c.dien_giai || c.nguon_so || '').slice(0, 70)) +
        '<span style="display:block;color:#667085;font-size:13px">' + h(cp2BoDuoi(c.tk_chi_phi)) + '</span></span><b>' + cp2Tien(c.so_tien) + '</b></div>';
    }).join('') + (cac.length > 5 ? '<div style="font-size:13px;color:#667085;padding:6px 0">và ' + (cac.length - 5) + ' khoản nữa</div>' : '') +
    (d.tuong_lai ? '<div style="font-size:13.5px;color:#b54708;margin-top:6px">Chưa tới tháng này nên chưa lập được.</div>' : '') +
    '<div style="margin-top:12px">' + nut + '</div>' +
    (cho.length ? '<div style="font-size:13.5px;color:#b42318;margin-top:10px">' + cho.length + ' khoản chờ khai số tháng chưa vào bút toán.</div>' : '') +
    (d.co_chua_gan && d.co_chua_gan.length ? '<div style="font-size:13.5px;color:#b42318;margin-top:6px">' + d.co_chua_gan.length + ' dòng Có 242 chưa gắn khoản: gắn xong mới lập được.</div>' : ''));
  ov.addEventListener('click', async function (e) {
    var n;
    if ((n = e.target.closest('[data-thky]'))) { ov.remove(); return cp2SheetThang(n.getAttribute('data-thky')); }
    var id = (e.target.closest('button') || {}).id;
    if (!id || ['thLap', 'thGhi', 'thBo'].indexOf(id) < 0) return;
    var nt = e.target.closest('button'); nt.disabled = true;
    try {
      if (id === 'thLap') { var r = await api(CP2_P + 'lap_thang', { ky: ky }); toast((r.cap_nhat ? 'Đã cập nhật ' : 'Đã lập nháp ') + r.journal_entry + ', ' + cp2Tien(r.tong)); }
      if (id === 'thGhi') {
        if (!await xacNhan('Ghi sổ bút toán phân bổ tháng ' + cp2Thang(ky) + '?\n\nSổ cái ghi Nợ chi phí, Có 242. Muốn sửa sau khi ghi sổ thì huỷ bút toán ở màn Bút toán.', 'Ghi sổ', 'Ghi sổ')) { nt.disabled = false; return; }
        await api(CP2_P + 'ghi_so_thang', { ky: ky }); toast('Đã ghi sổ phân bổ tháng ' + cp2Thang(ky));
      }
      if (id === 'thBo') {
        if (!await xacNhan('Bỏ bút toán nháp tháng ' + cp2Thang(ky) + '?\n\nBản nháp vẫn nằm trong hệ thống ở trạng thái đã bỏ.', 'Bỏ bản nháp', 'Bỏ')) { nt.disabled = false; return; }
        await api(CP2_P + 'bo_nhap_thang', { ky: ky }); toast('Đã bỏ bản nháp.');
      }
      ov.remove(); cp2SheetThang(ky);
    } catch (er) { nt.disabled = false; toast(errMsg(er)); }
  });
}

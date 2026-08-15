/* ================= DANH MUC NHA CUNG CAP =================
   Uyen hoi 14/08/2026: "co may mat hang chua gan NCC, em gan NCC o muc nao?"

   Do that truoc khi lam: 515 nha cung cap, 1.451 mat hang mua, ma chi 3 mon
   co gan nha cung cap. Nen cau hoi that khong phai "bam o dau" ma la "1.448
   mon kia lam sao gan cho xue". Chi duong bam roi de Uyen ngoi go tay 1.448
   lan thi do khong phai cau tra loi.

   Vi vay man nay xoay quanh mot y: may da biet san ai ban gi qua don mua va
   hoa don mua. Bay goi y ra, Uyen tick roi bam gan hang loat. */
var nccTim = '', nccNhom = null, nccChip = null, nccGanChon = {}, nccChiGoiY = 1;

async function scrNcc() {
  frame('Nhà cung cấp', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc danh mục...</div></div>');
  var kq;
  var ts = {};
  if (nccTim) ts.tu_khoa = nccTim;
  if (nccNhom) ts.nhom = nccNhom;
  if (nccChip) ts.chip = nccChip;
  try { kq = await api('vagabond.ncc.danh_sach', ts); }
  catch (e) { frame('Nhà cung cấp', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var rows = kq.rows || [], dem = kq.dem || {};

  var html = '<div class="card" style="padding:12px 14px"><input class="tin" id="nccQ" placeholder="Tìm theo tên, mã số thuế, số điện thoại" value="' + h(nccTim) + '" style="margin:0"></div>';

  var CHIP = [
    ['', '📚 Tất cả', kq.tat_ca],
    ['dang_mua', '🛒 Đang mua', dem.dang_mua],
    ['con_no', '💸 Còn nợ', dem.con_no],
    ['chua_gan_mon', '🔗 Chưa gán mặt hàng', dem.chua_gan_mon],
    ['thieu_ho_so', '⚠️ Thiếu MST hoặc email', dem.thieu_ho_so],
    ['da_tat', '🚫 Đã tắt', dem.da_tat]
  ];
  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(CHIP.map(function (x) {
    return posChipNut('data-nccc="' + x[0] + '"', x[1] + ' · ' + (x[2] || 0), (nccChip || '') === x[0]);
  }).join('')) + '</div>';

  if ((kq.nhom || []).length) {
    html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
      [['', '🏷 Mọi nhóm']].concat((kq.nhom || []).map(function (n) { return [n, n]; })).map(function (x) {
        return posChipNut('data-nccn="' + h(x[0]) + '"', h(x[1]), (nccNhom || '') === x[0]);
      }).join('')) + '</div>';
  }

  html += '<div class="card" style="padding:12px 14px;background:#f0fdfa;border:1.5px solid #99f6e4">' +
    '<div style="font-size:11.5px;color:#0f766e;font-weight:800">THEO BỘ LỌC</div>' +
    '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:5px">' +
    '<span style="font-size:13.5px;color:#374151">' + rows.length + ' nhà cung cấp</span>' +
    '<b style="font-size:19px;color:#0f766e">còn nợ ' + money(kq.tong_con_no) + ' đ</b></div></div>';

  html += '<div style="display:flex;gap:8px;margin-bottom:10px">' +
    '<button class="btn" id="nccGan" style="flex:2;margin:0">🔗 Gán NCC cho mặt hàng</button>' +
    '<button class="btn gh" id="nccXuat" style="flex:1;margin:0">📊 Excel</button></div>';

  html += '<div class="sec">Danh sách · bấm để xem hồ sơ</div><div class="card">';
  if (!rows.length) html += '<div class="emp" style="padding:24px"><div class="e1">🏭</div><div>Không có nhà cung cấp nào khớp bộ lọc.</div></div>';
  rows.slice(0, 200).forEach(function (r) {
    html += '<div class="hub" data-ncc="' + h(r.name) + '">' +
      '<div class="hub-i" style="background:' + (r.con_no > 0 ? '#fef2f2' : '#f0fdf4') + '">' + (r.disabled ? '🚫' : '🏭') + '</div>' +
      '<div class="hub-t"><div class="t1">' + h(r.supplier_name || r.name) + '</div>' +
      '<div class="t2">' + h(r.name) + (r.tax_id ? ' · MST ' + h(r.tax_id) : ' · chưa có MST') + (r.sdt ? ' · ' + h(r.sdt) : '') + '</div>' +
      '<div class="t2">' + r.so_mon + ' mặt hàng đã gán' + (r.mua_cuoi ? ' · mua gần nhất ' + hsNgayVn(r.mua_cuoi) : ' · chưa mua lần nào') + '</div>' +
      '</div>' + (r.con_no > 0 ? '<b style="white-space:nowrap;color:#b3261e">' + money(r.con_no) + ' đ</b>' : '') + '</div>';
  });
  if (rows.length > 200) html += '<div style="padding:10px 14px;font-size:12.5px;color:#6b7280">Còn ' + (rows.length - 200) + ' nhà nữa, gõ vào ô tìm để lọc bớt.</div>';
  html += '</div>';

  var b = frame('Nhà cung cấp', html, {});
  var q = document.getElementById('nccQ');
  if (q) q.onchange = function () { nccTim = q.value.trim(); go(scrNcc, true); };
  Array.prototype.forEach.call(document.querySelectorAll('[data-nccc]'), function (el) {
    el.onclick = function () { nccChip = el.getAttribute('data-nccc') || null; go(scrNcc, true); };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-nccn]'), function (el) {
    el.onclick = function () { nccNhom = el.getAttribute('data-nccn') || null; go(scrNcc, true); };
  });
  b.addEventListener('click', function (e) {
    var r = e.target.closest('[data-ncc]'); if (!r) return;
    var m = r.getAttribute('data-ncc');
    go(function () { scrNccXem(m); });
  });
  document.getElementById('nccGan').onclick = function () { nccGanChon = {}; go(scrNccGan); };
  document.getElementById('nccXuat').onclick = async function () {
    busy(true);
    try {
      var t = {}; if (nccTim) t.tu_khoa = nccTim; if (nccNhom) t.nhom = nccNhom; if (nccChip) t.chip = nccChip;
      var fl = await api('vagabond.ncc.xuat_excel', t);
      busy(false); bcTaiVe(fl.ten_file, fl.b64); toast('Đã tải ' + fl.ten_file);
    } catch (er) { busy(false); baoTin((er && er.message) || 'Xuất Excel lỗi'); }
  };
}

async function scrNccXem(ma) {
  frame('Nhà cung cấp', '<div class="emp"><div class="e1">⏳</div><div>Đang mở hồ sơ...</div></div>');
  var d;
  try { d = await api('vagabond.ncc.chi_tiet', { ncc: ma }); }
  catch (e) { frame('Nhà cung cấp', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>'); return; }
  var n = d.ncc;

  var o = function (nhan, gt) {
    return '<div style="display:flex;gap:10px;padding:5px 0;font-size:13px">' +
      '<span style="color:#6b7280;flex:0 0 42%">' + nhan + '</span>' +
      '<b style="flex:1;min-width:0;word-break:break-word">' + h(gt || '-') + '</b></div>';
  };
  var html = '<div class="card" style="padding:14px">' +
    '<div style="font-size:17px;font-weight:800;color:#0f766e">' + h(n.ten) + '</div>' +
    '<div style="font-size:12.5px;color:#6b7280;margin-top:3px">' + h(n.ma) + (n.tat ? ' · đã tắt' : '') + '</div></div>';

  html += '<div class="sec">Hồ sơ</div><div class="card" style="padding:10px 14px">' +
    o('Nhóm', n.nhom) + o('Mã số thuế', n.mst) + o('Điện thoại', n.sdt) +
    o('Email', n.email) + o('Địa chỉ', n.dia_chi) +
    o('Mã NCC nội bộ', n.ma_ncc) + o('Mã iPOS', n.ma_ipos) +
    o('Kênh đặt hàng', n.kenh) + o('Không chịu VAT', n.khong_vat ? 'Có' : 'Không') + '</div>';

  html += '<div class="sec">' + d.so_mon_gan + ' mặt hàng đã gán cho nhà này</div><div class="card">';
  if (!d.mon_gan.length) html += '<div class="emp" style="padding:20px"><div class="e1">🔗</div><div>Chưa gán mặt hàng nào. Xem mục dưới, máy đã dò ra những món từng mua của nhà này.</div></div>';
  d.mon_gan.forEach(function (x) {
    html += '<div class="hub" style="cursor:default"><div class="hub-i">📦</div>' +
      '<div class="hub-t"><div class="t1">' + h(x.ten) + '</div>' +
      '<div class="t2">' + h(x.ma) + (x.dvt ? ' · ' + h(x.dvt) : '') + (x.ma_ncc ? ' · mã bên NCC ' + h(x.ma_ncc) : '') + '</div></div>' +
      '<button class="btn gh" data-nccbo="' + h(x.ma) + '" style="margin:0;padding:5px 10px;font-size:12px">Gỡ</button></div>';
  });
  html += '</div>';

  if (d.tung_mua.length) {
    html += '<div class="sec">' + d.so_tung_mua + ' món đã từng mua của nhà này nhưng chưa gán</div>' +
      '<div class="card" style="padding:12px 14px;font-size:13px;line-height:1.6;color:#374151">' +
      'Máy dò từ hoá đơn mua đã ghi sổ. Bấm <b>Gán hết</b> để gắn cả ' + d.so_tung_mua + ' món này cho nhà cung cấp, sau này lập đơn mua sẽ tự gợi ý đúng nhà.' +
      '<button class="btn" id="nccGanHet" style="margin-top:10px">🔗 Gán hết ' + d.so_tung_mua + ' món</button></div>';
    html += '<div class="card">';
    d.tung_mua.slice(0, 60).forEach(function (x) {
      html += '<div class="hub" style="cursor:default"><div class="hub-i">🧾</div>' +
        '<div class="hub-t"><div class="t1">' + h(x.ten) + '</div>' +
        '<div class="t2">' + h(x.ma) + ' · mua ' + x.so_lan + ' lần · lần cuối ' + hsNgayVn(x.ngay) + '</div></div>' +
        '<b style="white-space:nowrap">' + money(x.gia) + ' đ</b></div>';
    });
    if (d.tung_mua.length > 60) html += '<div style="padding:10px 14px;font-size:12.5px;color:#6b7280">Còn ' + (d.tung_mua.length - 60) + ' món nữa.</div>';
    html += '</div>';
  }

  var b = frame(n.ten.slice(0, 28), html, {});
  b.addEventListener('click', async function (e) {
    var g = e.target.closest('[data-nccbo]');
    if (g) {
      var mon = g.getAttribute('data-nccbo');
      if (!await hoiCo('Gỡ gán', 'Gỡ nhà cung cấp này khỏi mặt hàng ' + mon + '?', 'Gỡ', true)) return;
      busy(true);
      try { await api('vagabond.ncc.bo_gan', { mon: mon, ncc: ma }); busy(false); toast('Đã gỡ'); }
      catch (er) { busy(false); return baoTin((er && er.message) || 'Gỡ lỗi'); }
      return go(function () { scrNccXem(ma); }, true);
    }
  });
  var gh = document.getElementById('nccGanHet');
  if (gh) gh.onclick = async function () {
    if (!await hoiCo('Gán hàng loạt', 'Gán ' + d.so_tung_mua + ' món này cho ' + n.ten + '?\n\nMáy dò từ hoá đơn mua đã ghi sổ nên gần như chắc đúng. Gán nhầm thì gỡ lại được.', 'Gán hết')) return;
    busy(true);
    try {
      var kq = await api('vagabond.ncc.gan_hang_loat', { cap: JSON.stringify(d.tung_mua.map(function (x) { return { mon: x.ma, ncc: ma }; })) });
      busy(false);
      toast('Đã gán ' + kq.da_gan + ' món' + (kq.so_loi ? ', ' + kq.so_loi + ' món lỗi' : ''), 4000);
      if (kq.so_loi) baoTin('Có ' + kq.so_loi + ' món không gán được:\n' + (kq.loi || []).join('\n'), 'Gán nhà cung cấp');
    } catch (er) { busy(false); return baoTin((er && er.message) || 'Gán lỗi'); }
    go(function () { scrNccXem(ma); }, true);
  };
}

/* Man tra loi thang cau hoi cua Uyen: mat hang nao chua gan, gan o day. */
async function scrNccGan() {
  frame('Gán nhà cung cấp', '<div class="emp"><div class="e1">⏳</div><div>Đang dò lịch sử mua...</div></div>');
  var d;
  try { d = await api('vagabond.ncc.mon_chua_gan', { chi_co_goi_y: nccChiGoiY ? 1 : 0, gioi_han: 300 }); }
  catch (e) { frame('Gán nhà cung cấp', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var rows = d.rows || [];
  var soChon = Object.keys(nccGanChon).length;

  var html = '<div class="card" style="padding:12px 14px;font-size:13px;line-height:1.6;color:#374151">' +
    'Còn <b>' + d.tong_chua_gan + '</b> mặt hàng chưa gán nhà cung cấp. Máy đã dò đơn mua và hoá đơn mua để đoán ai bán món nào: ' +
    '<b>' + d.co_goi_y + '</b> món có gợi ý, <b>' + d.khong_goi_y + '</b> món chưa từng mua nên phải gán tay.<br>' +
    'Bấm vào một dòng để chọn nhà cung cấp máy gợi ý, rồi bấm nút dưới cùng để gán cả loạt.</div>';

  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
    [[1, '💡 Chỉ món có gợi ý'], [0, '📋 Xem hết']].map(function (x) {
      return posChipNut('data-nccgy="' + x[0] + '"', x[1], (nccChiGoiY ? 1 : 0) === x[0]);
    }).join('')) + '</div>';

  html += '<div class="card" style="padding:12px 14px;background:#fffbeb;border:1.5px solid #fde68a">' +
    '<div style="font-size:11.5px;color:#92400e;font-weight:800">ĐANG CHỌN</div>' +
    '<div style="font-size:20px;font-weight:800;color:#92400e;margin-top:3px">' + soChon + ' mặt hàng</div></div>';

  html += '<div class="sec">Mặt hàng chưa gán · bấm để chọn nhà cung cấp</div><div class="card">';
  if (!rows.length) html += '<div class="emp" style="padding:24px"><div class="e1">🎉</div><div>Không còn mặt hàng nào trong nhóm này.</div></div>';
  rows.forEach(function (x) {
    var chon = nccGanChon[x.ma];
    html += '<div class="hub" data-nccm="' + h(x.ma) + '"' + (chon ? ' style="background:#dbeafe"' : '') + '>' +
      '<div class="hub-i">' + (chon ? '☑️' : (x.goi_y.length ? '💡' : '⬜')) + '</div>' +
      '<div class="hub-t"><div class="t1">' + h(x.ten) + '</div>' +
      '<div class="t2">' + h(x.ma) + (x.dvt ? ' · ' + h(x.dvt) : '') + '</div>' +
      (chon
        ? '<div class="t2" style="color:#1d4ed8;font-weight:700">→ ' + h(chon.ten_ncc) + '</div>'
        : (x.goi_y.length
          ? '<div class="t2" style="color:#0e7490">gợi ý: ' + h(x.goi_y[0].ten_ncc) + ' · mua ' + x.goi_y[0].so_lan + ' lần</div>'
          : '<div class="t2" style="color:#b45309">chưa từng mua, phải chọn tay</div>')) +
      '</div></div>';
  });
  if (d.da_cat_bot) html += '<div style="padding:10px 14px;font-size:12.5px;color:#6b7280">Còn ' + d.da_cat_bot + ' món nữa, gán bớt rồi mở lại màn này.</div>';
  html += '</div>';

  var foot = soChon
    ? '<div style="display:flex;gap:8px"><button class="btn" id="nccLuu" style="flex:2">🔗 Gán ' + soChon + ' mặt hàng</button>' +
      '<button class="btn gh" id="nccBo" style="flex:1">✖ Bỏ chọn</button></div>'
    : '';
  var b = frame('Gán nhà cung cấp', html, foot ? { footer: foot } : {});

  Array.prototype.forEach.call(document.querySelectorAll('[data-nccgy]'), function (el) {
    el.onclick = function () { nccChiGoiY = +el.getAttribute('data-nccgy'); go(scrNccGan, true); };
  });
  b.addEventListener('click', async function (e) {
    var r = e.target.closest('[data-nccm]'); if (!r) return;
    var ma = r.getAttribute('data-nccm');
    var mon = rows.filter(function (x) { return x.ma === ma; })[0];
    if (!mon) return;
    if (nccGanChon[ma]) { delete nccGanChon[ma]; return go(scrNccGan, true); }
    var lua = mon.goi_y.map(function (g) {
      return { k: g.ncc, icon: '🏭', nhan: g.ten_ncc,
        mo_ta: 'Đã mua ' + g.so_lan + ' lần, gần nhất ' + hsNgayVn(g.ngay) + ' giá ' + money(g.gia) + ' đ (theo ' + g.nguon + ')' };
    });
    lua.push({ k: '__tim', icon: '🔎', nhan: 'Chọn nhà cung cấp khác', mo_ta: 'Gõ tên để tìm trong danh mục' });
    var c = await hoiChon(mon.ten, 'Mặt hàng ' + mon.ma, lua);
    if (!c) return;
    if (c === '__tim') {
      var tu = await hoiChu('Tìm nhà cung cấp', 'Gõ một phần tên nhà cung cấp:', '', { bat_buoc: true });
      if (!tu) return;
      busy(true);
      var ds;
      try { ds = await api('vagabond.ncc.danh_sach', { tu_khoa: tu }); } catch (er) { busy(false); return baoTin((er && er.message) || 'Tìm lỗi'); }
      busy(false);
      var tim = (ds.rows || []).slice(0, 8);
      if (!tim.length) return baoTin('Không tìm thấy nhà cung cấp nào khớp "' + tu + '".', 'Tìm nhà cung cấp');
      var c2 = await hoiChon('Chọn nhà cung cấp', tim.length + ' nhà khớp', tim.map(function (t) {
        return { k: t.name, icon: '🏭', nhan: t.supplier_name || t.name, mo_ta: t.tax_id ? 'MST ' + t.tax_id : '' };
      }));
      if (!c2) return;
      var t2 = tim.filter(function (t) { return t.name === c2; })[0];
      nccGanChon[ma] = { ncc: c2, ten_ncc: (t2 && (t2.supplier_name || t2.name)) || c2 };
    } else {
      var g = mon.goi_y.filter(function (x) { return x.ncc === c; })[0];
      nccGanChon[ma] = { ncc: c, ten_ncc: (g && g.ten_ncc) || c };
    }
    go(scrNccGan, true);
  });
  var bo = document.getElementById('nccBo');
  if (bo) bo.onclick = function () { nccGanChon = {}; go(scrNccGan, true); };
  var luu = document.getElementById('nccLuu');
  if (luu) luu.onclick = async function () {
    var cap = Object.keys(nccGanChon).map(function (m) { return { mon: m, ncc: nccGanChon[m].ncc }; });
    if (!cap.length) return;
    if (!await hoiCo('Gán nhà cung cấp', 'Gán ' + cap.length + ' mặt hàng cho nhà cung cấp đã chọn?\n\nGán nhầm thì vào hồ sơ nhà cung cấp gỡ lại được.', 'Gán')) return;
    busy(true);
    try {
      var kq = await api('vagabond.ncc.gan_hang_loat', { cap: JSON.stringify(cap) });
      busy(false);
      nccGanChon = {};
      toast('Đã gán ' + kq.da_gan + ' mặt hàng' + (kq.so_loi ? ', ' + kq.so_loi + ' lỗi' : ''), 4000);
      if (kq.so_loi) baoTin('Có ' + kq.so_loi + ' món không gán được:\n' + (kq.loi || []).join('\n'), 'Gán nhà cung cấp');
    } catch (er) { busy(false); return baoTin((er && er.message) || 'Gán lỗi'); }
    go(scrNccGan, true);
  };
}



/* ================= QUAN LY NGUOI DUNG VA QUYEN =================
   Anh Viet 14/08/2026: "ma tran quyen cua em lam cung hoi roi, anh hy vong em
   co the lam no mot cach de thao tac nhat co the".

   Do that truoc khi lam: site co 40 vai tro dang bat, 34 tai khoan. Trong 40
   vai thi 25 la vai san cua ERPNext tiem khong dung toi. Bay ca 40 vai ra roi
   bao nguoi quan ly tu tick la dung cach lam cua ERPNext, khong phai cach lam
   cua nguoi dang ban hang.

   Nen man nay xoay quanh GOI CHUC VU: 11 goi da chon san dung theo cong viec
   that o tiem. Gan nguoi vao goi la xong. Ai can khac goi moi phai mo phan
   "Chinh tung quyen" ra - va do la truong hop hiem, nen no nam sau mot lop. */

var qndTim = '', qndChip = null, qndGoi = null;

async function scrNguoiDung() {
  frame('Quản lý người dùng', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc danh sách...</div></div>');
  var kq;
  var ts = {};
  if (qndTim) ts.tu_khoa = qndTim;
  if (qndChip) ts.chip = qndChip;
  if (qndGoi) ts.goi = qndGoi;
  try { kq = await api('vagabond.nguoi_dung.danh_sach', ts); }
  catch (e) { frame('Quản lý người dùng', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var rows = kq.rows || [], dem = kq.dem || {};

  var html = '<div class="card" style="padding:12px 14px"><input class="tin" id="qndQ" placeholder="Tìm theo tên, email, số điện thoại" value="' + h(qndTim) + '" style="margin:0"></div>';

  var CHIP = [
    ['', '👥 Tất cả', kq.tat_ca],
    ['dang_lam', '✅ Đang làm', dem.dang_lam],
    ['chua_dang_nhap', '📭 Chưa đăng nhập lần nào', dem.chua_dang_nhap],
    ['chua_gan', '❔ Chưa gán quyền', dem.chua_gan],
    ['tuy_chinh', '🔧 Quyền tuỳ chỉnh', dem.tuy_chinh],
    ['da_tat', '🚫 Đã tắt', dem.da_tat]
  ];
  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(CHIP.map(function (x) {
    return posChipNut('data-qndc="' + x[0] + '"', x[1] + ' · ' + (x[2] || 0), (qndChip || '') === x[0]);
  }).join('')) + '</div>';

  var dg = kq.dem_goi || {};
  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
    [['', '🏷 Mọi gói chức vụ']].concat((kq.goi || []).map(function (g) { return [g.k, g.icon + ' ' + g.ten]; })).map(function (x) {
      var so = x[0] ? (dg[x[0]] || 0) : null;
      return posChipNut('data-qndg="' + h(x[0]) + '"', h(x[1]) + (so === null ? '' : ' · ' + so), (qndGoi || '') === x[0]);
    }).join('')) + '</div>';

  html += '<div style="display:flex;gap:8px;margin-bottom:10px">' +
    '<button class="btn" id="qndMoi" style="flex:2;margin:0">✉️ Mời tài khoản mới</button>' +
    '<button class="btn gh" id="qndQuyen" style="flex:1;margin:0">🗝 Gói quyền</button></div>';

  html += '<div class="sec">' + rows.length + ' tài khoản · bấm để mở hồ sơ</div><div class="card">';
  if (!rows.length) html += '<div class="emp" style="padding:24px"><div class="e1">👥</div><div>Không có tài khoản nào khớp bộ lọc.</div></div>';
  rows.forEach(function (r) {
    html += '<div class="hub" data-qnd="' + h(r.email) + '">' +
      '<div class="hub-i" style="background:' + (r.bat ? '#f0fdf4' : '#f5f5f5') + '">' + (r.bat ? r.goi_icon : '🚫') + '</div>' +
      '<div class="hub-t"><div class="t1">' + h(r.ten) + '</div>' +
      '<div class="t2">' + h(r.email) + (r.sdt ? ' · ' + h(r.sdt) : '') + '</div>' +
      '<div class="t2">' + h(r.goi_ten) +
      (r.vai_thua && r.vai_thua.length ? ' <span style="color:#b45309">+' + r.vai_thua.length + ' quyền riêng</span>' : '') +
      (r.lan_cuoi ? ' · vào app ' + hsNgayVn(String(r.lan_cuoi).slice(0, 10)) : ' · <span style="color:#b45309">chưa đăng nhập lần nào</span>') +
      '</div></div>' +
      (r.bat ? '' : '<span class="vxtag c2">Đã tắt</span>') + '</div>';
  });
  html += '</div>';

  html += '<div style="font-size:12px;color:#98a2b3;padding:12px 4px 4px;line-height:1.6">' +
    'Gói chức vụ chỉ động vào những quyền nằm trong gói. Quyền nào ai đó đã gán riêng bên ngoài gói thì đổi gói cũng không mất.</div>';

  var b = frame('Quản lý người dùng', html, {});
  var q = document.getElementById('qndQ');
  if (q) q.onchange = function () { qndTim = q.value.trim(); go(scrNguoiDung, true); };
  Array.prototype.forEach.call(document.querySelectorAll('[data-qndc]'), function (el) {
    el.onclick = function () { qndChip = el.getAttribute('data-qndc') || null; go(scrNguoiDung, true); };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-qndg]'), function (el) {
    el.onclick = function () { qndGoi = el.getAttribute('data-qndg') || null; go(scrNguoiDung, true); };
  });
  b.addEventListener('click', function (e) {
    var r = e.target.closest('[data-qnd]'); if (!r) return;
    var m = r.getAttribute('data-qnd');
    go(function () { scrNguoiDungXem(m); });
  });
  document.getElementById('qndMoi').onclick = function () { qndMoi(); };
  document.getElementById('qndQuyen').onclick = function () { go(scrQuyen); };
}


/* Ho so mot nguoi: goi dang giu, viec lam duoc, va ba nut thao tac. */
async function scrNguoiDungXem(email) {
  frame('Người dùng', '<div class="emp"><div class="e1">⏳</div><div>Đang mở hồ sơ...</div></div>');
  var d;
  try { d = await api('vagabond.nguoi_dung.chi_tiet', { email: email }); }
  catch (e) { frame('Người dùng', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>'); return; }

  function o(nhan, giaTri) {
    if (!giaTri) return '';
    return '<div style="display:flex;justify-content:space-between;gap:12px;padding:9px 0;border-bottom:1px solid #f1f3f6">' +
      '<span style="font-size:13px;color:#6b7280">' + h(nhan) + '</span>' +
      '<b style="font-size:13.5px;text-align:right">' + h(String(giaTri)) + '</b></div>';
  }

  var html = '<div class="card" style="padding:14px">' +
    '<div style="font-size:19px;font-weight:800">' + h(d.ten) + '</div>' +
    '<div style="font-size:13px;color:#6b7280;margin-top:2px">' + h(d.email) + '</div>' +
    '<div style="margin-top:10px">' +
    '<span class="vxtag ' + (d.bat ? 'd' : 'c2') + '">' + (d.bat ? 'Đang làm' : 'Đã tắt') + '</span> ' +
    '<span class="vxtag c2">' + h(d.goi_ten) + '</span></div></div>';

  html += '<div class="card" style="padding:4px 14px 10px">' +
    o('Số điện thoại', d.sdt) +
    o('Vào app lần cuối', d.lan_cuoi ? hsNgayVn(String(d.lan_cuoi).slice(0, 10)) : 'Chưa đăng nhập lần nào') +
    o('Tạo tài khoản', d.tao_luc ? hsNgayVn(String(d.tao_luc).slice(0, 10)) : '') +
    '</div>';

  if ((d.lam_duoc || []).length) {
    html += '<div class="sec">Với gói này, làm được</div><div class="card" style="padding:12px 14px">' +
      (d.lam_duoc || []).map(function (x) {
        return '<div style="display:flex;gap:9px;align-items:flex-start;padding:5px 0">' +
          '<span style="color:#0f766e;font-weight:800">✓</span>' +
          '<span style="font-size:13.5px;line-height:1.6;color:#374151">' + h(x) + '</span></div>';
      }).join('') + '</div>';
  }

  if ((d.vai_thua || []).length) {
    html += '<div class="sec">Quyền riêng ngoài gói</div><div class="card" style="padding:12px 14px">' +
      '<div style="font-size:12.5px;color:#b45309;line-height:1.6;margin-bottom:8px">' +
      'Những quyền này ai đó đã gán thêm bằng tay. Đổi gói chức vụ sẽ không gỡ chúng.</div>' +
      (d.vai_thua || []).map(function (x) { return '<span class="vxtag c" style="margin:0 6px 6px 0">' + h(x) + '</span>'; }).join('') +
      '</div>';
  }

  html += '<div class="sec">Toàn bộ quyền đang có (' + (d.vai || []).length + ')</div>' +
    '<div class="card" style="padding:12px 14px">' +
    ((d.vai || []).length
      ? (d.vai || []).map(function (x) { return '<span class="vxtag c2" style="margin:0 6px 6px 0">' + h(x) + '</span>'; }).join('')
      : '<span style="font-size:13px;color:#98a2b3">Chưa có quyền nghiệp vụ nào, người này đăng nhập vào sẽ thấy màn hình trống.</span>') +
    '</div>';

  html += '<button class="btn" id="qndDoiGoi">🗝 Đổi gói chức vụ</button>' +
    '<button class="btn gh" id="qndThu">✉️ Gửi lại thư mời đặt mật khẩu</button>' +
    '<button class="btn gh" id="qndChiTiet">🔧 Chỉnh từng quyền một</button>' +
    (d.la_toi ? '' : '<button class="btn ' + (d.bat ? 'dg' : 'gh') + '" id="qndBatTat">' + (d.bat ? '🚫 Tắt tài khoản này' : '✅ Bật lại tài khoản') + '</button>');

  frame('Người dùng', html, { back: function () { go(scrNguoiDung); } });

  document.getElementById('qndDoiGoi').onclick = async function () {
    var ds;
    try { ds = await api('vagabond.nguoi_dung.danh_sach_goi'); } catch (er) { return baoTin((er && er.message) || 'Không đọc được gói'); }
    var chon = await hoiChon('Gói chức vụ cho ' + d.ten,
      'Chọn gói đúng với công việc của người này. Máy sẽ đặt lại toàn bộ quyền trong gói, quyền riêng ngoài gói giữ nguyên.',
      (ds.goi || []).map(function (g) { return { k: g.k, nhan: g.ten + ' · ' + g.so_nguoi + ' người', mo_ta: g.mo_ta, icon: g.icon }; }),
      d.goi || null);
    if (!chon) return;
    busy(true);
    try {
      var kq = await api('vagabond.nguoi_dung.dat_goi', { email: d.email, goi: chon });
      busy(false); toast(kq.loi_nhan, 4500);
    } catch (er) { busy(false); return baoTin((er && er.message) || 'Đổi gói lỗi'); }
    go(function () { scrNguoiDungXem(d.email); }, true);
  };

  document.getElementById('qndThu').onclick = async function () {
    if (!await hoiCo('Gửi thư mời', 'Gửi lại thư hướng dẫn đặt mật khẩu tới ' + d.email + '?', 'Gửi')) return;
    busy(true);
    try { var kq = await api('vagabond.nguoi_dung.gui_lai_thu', { email: d.email }); busy(false); toast(kq.loi_nhan, 4000); }
    catch (er) { busy(false); baoTin((er && er.message) || 'Gửi thư lỗi'); }
  };

  document.getElementById('qndChiTiet').onclick = function () { go(function () { qndSuaLe(d); }); };

  var bt = document.getElementById('qndBatTat');
  if (bt) bt.onclick = async function () {
    var tat = !!d.bat;
    if (!await hoiCo(tat ? 'Tắt tài khoản' : 'Bật tài khoản',
      tat ? h(d.ten) + ' sẽ không đăng nhập được nữa. Dữ liệu cũ của người này giữ nguyên, bật lại lúc nào cũng được.'
        : h(d.ten) + ' đăng nhập lại được ngay với quyền cũ.',
      tat ? 'Tắt' : 'Bật', tat)) return;
    busy(true);
    try { var kq = await api('vagabond.nguoi_dung.bat_tat', { email: d.email, bat: tat ? 0 : 1 }); busy(false); toast(kq.loi_nhan, 4000); }
    catch (er) { busy(false); return baoTin((er && er.message) || 'Không đổi được'); }
    go(function () { scrNguoiDungXem(d.email); }, true);
  };
}


/* Che do chi tiet. Co y de sau mot lop vi 99% truong hop khong can toi. */
function qndSuaLe(d) {
  var chon = {};
  (d.vai || []).forEach(function (v) { chon[v] = 1; });
  var html = '<div class="card" style="padding:12px 14px;background:#fffbeb;border:1.5px solid #fde68a">' +
    '<div style="font-size:13px;line-height:1.65;color:#92400e">Màn này gán thẳng từng quyền của hệ thống. ' +
    'Bình thường không cần vào đây - dùng gói chức vụ là đủ và ít sai hơn. ' +
    'Chỉ dùng khi một người phải làm việc mà không gói nào phủ hết.</div></div>';

  html += '<div class="sec">' + h(d.ten) + ' · tick quyền cần có</div><div class="card">';
  (d.vai_chon_duoc || []).forEach(function (v) {
    html += '<label class="hub" style="cursor:pointer" data-qvl="' + h(v) + '">' +
      '<input type="checkbox" ' + (chon[v] ? 'checked' : '') + ' style="width:20px;height:20px;flex:0 0 auto">' +
      '<div class="hub-t"><div class="t1" style="font-size:14.5px">' + h(v) + '</div></div></label>';
  });
  html += '</div><button class="btn" id="qvlLuu">💾 Lưu quyền</button>';

  frame('Chỉnh từng quyền', html, { back: function () { go(function () { scrNguoiDungXem(d.email); }); } });

  Array.prototype.forEach.call(document.querySelectorAll('[data-qvl]'), function (el) {
    var inp = el.querySelector('input');
    inp.onchange = function () { chon[el.getAttribute('data-qvl')] = inp.checked ? 1 : 0; };
  });
  document.getElementById('qvlLuu').onclick = async function () {
    var vai = Object.keys(chon).filter(function (k) { return chon[k]; });
    if (!await hoiCo('Lưu quyền', 'Đặt lại quyền cho ' + d.ten + ' thành ' + vai.length + ' quyền?', 'Lưu')) return;
    busy(true);
    try {
      var kq = await api('vagabond.nguoi_dung.sua_quyen_le', { email: d.email, vai: JSON.stringify(vai) });
      busy(false); toast(kq.loi_nhan, 4000);
    } catch (er) { busy(false); return baoTin((er && er.message) || 'Lưu lỗi'); }
    go(function () { scrNguoiDungXem(d.email); }, true);
  };
}


/* Moi tai khoan moi: ba o, chon goi bang chip, may gui thu dat mat khau. */
async function qndMoi() {
  var ten = await hoiChu('Mời tài khoản mới', 'Họ tên nhân viên, ghi như trên giấy tờ để sau này còn đối chiếu.', '', { bat_buoc: 1, goi_y: 'Nguyễn Văn A' });
  if (!ten) return;
  var email = await hoiChu('Mời tài khoản mới', 'Email của ' + h(ten) + '. Đây cũng là tên đăng nhập, và thư mời đặt mật khẩu sẽ gửi về hộp thư này.', '', { bat_buoc: 1, kieu: 'email', goi_y: 'ten@gmail.com' });
  if (!email) return;
  var sdt = await hoiChu('Mời tài khoản mới', 'Số điện thoại (bỏ trống cũng được).', '', { kieu: 'number', goi_y: '090...' });
  if (sdt === null) return;

  var ds;
  try { ds = await api('vagabond.nguoi_dung.danh_sach_goi'); } catch (er) { return baoTin((er && er.message) || 'Không đọc được gói'); }
  var goi = await hoiChon('Gói chức vụ', 'Chọn công việc của ' + h(ten) + '. Đổi lại lúc nào cũng được.',
    (ds.goi || []).map(function (g) { return { k: g.k, nhan: g.ten, mo_ta: g.mo_ta, icon: g.icon }; }), null);
  if (!goi) return;

  var g = (ds.goi || []).filter(function (x) { return x.k === goi; })[0] || {};
  if (!await hoiCo('Tạo tài khoản',
    ten + '\n' + email + (sdt ? '\n' + sdt : '') + '\n\nGói: ' + (g.ten || goi) +
    '\n\nMáy sẽ tạo tài khoản và gửi thư mời đặt mật khẩu ngay.', 'Tạo và gửi thư')) return;

  busy(true);
  try {
    var kq = await api('vagabond.nguoi_dung.moi', { email: email, ten: ten, goi: goi, sdt: sdt || '', gui_thu: 1 });
    busy(false); toast(kq.loi_nhan, 5000);
  } catch (er) { busy(false); return baoTin((er && er.message) || 'Tạo tài khoản lỗi'); }
  go(scrNguoiDung, true);
}


/* ---------- Man Quan ly quyen: doc goi nao lam duoc gi ---------- */
async function scrQuyen() {
  frame('Quản lý quyền', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc gói quyền...</div></div>');
  var d;
  try { d = await api('vagabond.nguoi_dung.danh_sach_goi'); }
  catch (e) { frame('Quản lý quyền', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }

  var html = '<div class="card" style="padding:12px 14px;background:#f0fdfa;border:1.5px solid #99f6e4">' +
    '<div style="font-size:13px;line-height:1.7;color:#0f766e">Mỗi gói là một cụm quyền chọn sẵn theo công việc thật ở tiệm. ' +
    'Gán người vào gói là xong, không phải nhớ tên quyền của hệ thống. ' +
    'Bấm vào gói để xem gói đó làm được gì và ai đang giữ.</div></div>';

  if (d.chua_xep) {
    html += '<div class="card" style="padding:12px 14px;background:#fffbeb;border:1.5px solid #fde68a">' +
      '<div style="font-size:13px;line-height:1.65;color:#92400e"><b>' + d.chua_xep + ' người chưa xếp gói.</b> ' +
      'Bộ quyền hiện tại của họ không khớp trọn vẹn gói nào. Họ vẫn dùng app bình thường, ' +
      'chỉ là muốn biết ai làm được gì thì phải xem từng người.' +
      ((d.nguoi_chua_xep || []).length ? '<br><br>' + h((d.nguoi_chua_xep || []).join(', ')) : '') +
      '</div></div>';
  }

  html += '<div class="sec">' + (d.goi || []).length + ' gói chức vụ</div><div class="card">';
  (d.goi || []).forEach(function (g) {
    html += '<div class="hub" data-qgo="' + h(g.k) + '">' +
      '<div class="hub-i" style="background:#f5f7fa">' + g.icon + '</div>' +
      '<div class="hub-t"><div class="t1">' + h(g.ten) + '</div>' +
      '<div class="t2">' + h(g.mo_ta) + '</div>' +
      '<div class="t2">' + g.vai.length + ' quyền hệ thống' +
      (g.vai_thieu.length ? ' · <span style="color:#b3261e">' + g.vai_thieu.length + ' quyền chưa tạo</span>' : '') + '</div>' +
      '</div><b style="white-space:nowrap;color:#0f766e">' + g.so_nguoi + ' người</b></div>';
  });
  html += '</div>';

  if ((d.vai_khac || []).length) {
    html += '<div class="sec">Quyền hệ thống không nằm trong gói nào (' + d.vai_khac.length + ')</div>' +
      '<div class="card" style="padding:12px 14px">' +
      '<div style="font-size:12.5px;color:#6b7280;line-height:1.6;margin-bottom:8px">' +
      'Đây là các quyền sẵn có của ERPNext mà tiệm chưa dùng tới. Muốn gán cho ai thì vào hồ sơ người đó, ' +
      'bấm Chỉnh từng quyền một.</div>' +
      (d.vai_khac || []).map(function (x) { return '<span class="vxtag c2" style="margin:0 6px 6px 0">' + h(x) + '</span>'; }).join('') +
      '</div>';
  }

  var b = frame('Quản lý quyền', html, { back: function () { go(scrNguoiDung); } });
  b.addEventListener('click', function (e) {
    var r = e.target.closest('[data-qgo]'); if (!r) return;
    var k = r.getAttribute('data-qgo');
    var g = (d.goi || []).filter(function (x) { return x.k === k; })[0];
    if (!g) return;
    go(function () { scrQuyenXem(g); });
  });
}

function scrQuyenXem(g) {
  var html = '<div class="card" style="padding:14px">' +
    '<div style="font-size:19px;font-weight:800">' + g.icon + ' ' + h(g.ten) + '</div>' +
    '<div style="font-size:13px;color:#6b7280;margin-top:4px;line-height:1.6">' + h(g.mo_ta) + '</div></div>';

  html += '<div class="sec">Làm được gì</div><div class="card" style="padding:12px 14px">' +
    (g.lam_duoc || []).map(function (x) {
      return '<div style="display:flex;gap:9px;align-items:flex-start;padding:5px 0">' +
        '<span style="color:#0f766e;font-weight:800">✓</span>' +
        '<span style="font-size:13.5px;line-height:1.6;color:#374151">' + h(x) + '</span></div>';
    }).join('') + '</div>';

  html += '<div class="sec">Ai đang giữ gói này (' + g.so_nguoi + ')</div><div class="card" style="padding:12px 14px">' +
    ((g.nguoi || []).length
      ? (g.nguoi || []).map(function (x) { return '<span class="vxtag d" style="margin:0 6px 6px 0">' + h(x) + '</span>'; }).join('') +
        (g.so_nguoi > (g.nguoi || []).length ? '<div style="font-size:12.5px;color:#98a2b3;margin-top:6px">và ' + (g.so_nguoi - g.nguoi.length) + ' người nữa</div>' : '')
      : '<span style="font-size:13px;color:#98a2b3">Chưa ai giữ gói này.</span>') +
    '</div>';

  html += '<div class="sec">Quy ra quyền của hệ thống</div><div class="card" style="padding:12px 14px">' +
    (g.vai || []).map(function (x) {
      var thieu = (g.vai_thieu || []).indexOf(x) >= 0;
      return '<span class="vxtag ' + (thieu ? 'x' : 'c2') + '" style="margin:0 6px 6px 0">' + h(x) + (thieu ? ' (chưa tạo)' : '') + '</span>';
    }).join('') +
    ((g.vai_thieu || []).length
      ? '<div style="font-size:12.5px;color:#b3261e;line-height:1.6;margin-top:8px">Quyền đánh dấu đỏ chưa được tạo trên hệ thống, gán gói này sẽ bỏ qua chúng. Báo em để em tạo.</div>'
      : '') +
    '</div>';

  frame('Gói chức vụ', html, { back: function () { go(scrQuyen); } });
}




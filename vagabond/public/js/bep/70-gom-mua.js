/* ---------- 70. Gom yêu cầu mua thành đơn mua (v646) ----------

   Anh Việt 09/11/2026: "Tổng hợp từ mấy cái đơn yêu cầu mua hàng của các bộ
   phận gửi lên ấy. Rồi staff thu mua vào chỉ việc sửa số rồi chốt."

   Máy chủ (vagabond/gom_mua.py) gom mọi dòng yêu cầu mua đã gửi mà chưa ai
   duyệt, chia theo nhà cung cấp mặc định, cộng theo món. Số mua điền sẵn bằng
   tổng số xin (số ĐẶT, điền sẵn được), thu mua sửa rồi bấm Chốt cho từng nhà
   cung cấp. Máy chủ đọc lại các dòng lúc chốt, ghi phần duyệt lên từng phiếu
   xin và lập đơn mua; màn này chỉ gửi mã món và số mua.

   Tiền tố gm = gom mua. */

var GM = { d: null, sua: {}, mo: {}, tim: '', loc: '' };
/* Bản nháp tự lưu (Codex 549): số thu mua đã sửa nằm ở GM.sua và được phần 48
   lưu trên máy. Mở lại từ bản nháp thì 48 đặt vào đây, màn ghép ngay sau khi
   đọc danh sách (phần sau 48 không móc sdGhep). */
var gmKhoiPhuc = null;

/* THUẦN: giữ số đã sửa của những món còn trên màn. Món vừa chốt, vừa có người
   duyệt hay ô gõ hỏng (null) thì bỏ. */
function gmGiuSua(sua, d) {
  var co = {}, ra = {};
  ((d && d.nhom) || []).forEach(function (g) { (g.mon || []).forEach(function (m) { co[m.ma] = 1; }); });
  Object.keys(sua || {}).forEach(function (k) { if (co[k] && sua[k] != null) ra[k] = sua[k]; });
  return ra;
}

/* THUẦN: sau lần chốt `a` (tham số gửi máy chủ) còn bao nhiêu món đã sửa ở
   nhóm khác. Còn thì bản nháp chưa xong, chốt một nhóm không được xoá nó. */
function gmConSuaKhac(a) {
  var chot = {};
  try { JSON.parse((a && a.dong) || '[]').forEach(function (x) { chot[x.ma] = 1; }); } catch (e) { }
  return Object.keys(gmGiuSua(GM.sua, GM.d)).filter(function (k) { return !chot[k]; }).length;
}

/* THUẦN: số mua đang hiện của một món (đã gõ thì theo số gõ, chưa thì số máy). */
function gmSoMua(m) {
  var k = m.ma;
  return GM.sua[k] != null ? GM.sua[k] : m.mua;
}

/* THUẦN: dòng gửi lên khi chốt một nhóm. */
function gmDongChot(nhom) {
  return (nhom.mon || []).map(function (m) { return { ma: m.ma, sl: gmSoMua(m) }; });
}

/* THUẦN: tiền tạm tính của nhóm theo số đang hiện (giá lần mua gần nhất). */
function gmTien(nhom) {
  return Math.round((nhom.mon || []).reduce(function (t, m) { return t + (Number(gmSoMua(m)) || 0) * (m.gia || 0); }, 0));
}

/* v650 (anh Việt 12/11/2026): màn cũ trơ trụi, tên nhà cung cấp dài đẩy nút
   Chốt tràn ngang, cả trang trượt sang phải. Nay mỗi món có dải chip trạng
   thái (cần ngày nào, Kho tổng còn bao nhiêu, đang chờ về, thuế, đã sửa số),
   đầu màn có dải tiến độ và chip lọc, nút Chốt nằm riêng một hàng. */

/* THUẦN: ngày cách hôm nay bao nhiêu (âm là đã qua). Chuỗi YYYY-MM-DD. */
function gmCachNgay(ngay, homNay) {
  if (!ngay || !homNay) return null;
  var a = Date.UTC(+ngay.slice(0, 4), +ngay.slice(5, 7) - 1, +ngay.slice(8, 10));
  var b = Date.UTC(+homNay.slice(0, 4), +homNay.slice(5, 7) - 1, +homNay.slice(8, 10));
  return Math.round((a - b) / 86400000);
}

/* THUẦN: món cần gấp (cần hôm nay, ngày mai, hay đã quá ngày cần). */
function gmGap(m, homNay) {
  var c = gmCachNgay(m.ngay_can, homNay);
  return c != null && c <= 1;
}

/* THUẦN: các chip của một món, theo thứ tự đọc. c là màu của lớp .st:
   r đỏ có việc gấp, w vàng cần để ý, g xanh ổn, b xanh dương thông tin, n xám. */
function gmChipMon(m, homNay, daSua) {
  var ra = [];
  var c = gmCachNgay(m.ngay_can, homNay);
  if (c != null) {
    ra.push(c < 0 ? { t: 'Quá ngày cần ' + dmy(m.ngay_can).slice(0, 5), c: 'r' }
      : c === 0 ? { t: 'Cần hôm nay', c: 'r' }
        : c === 1 ? { t: 'Cần ngày mai', c: 'w' }
          : { t: 'Cần ' + dmy(m.ngay_can).slice(0, 5), c: 'n' });
  }
  var ton = Number(m.ton) || 0, xin = Number(m.xin) || 0;
  ra.push(ton <= 0 ? { t: 'Kho tổng hết', c: 'n' }
    : ton + 0.0001 >= xin ? { t: 'Kho tổng đủ ' + kl(ton, m.dvt), c: 'g' }
      : { t: 'Kho tổng còn ' + kl(ton, m.dvt), c: 'w' });
  if ((Number(m.cho_ve) || 0) > 0) ra.push({ t: 'Đang chờ về ' + kl(m.cho_ve, m.dvt), c: 'w' });
  ra.push(m.thue == null ? { t: 'Món chưa khai VAT', c: 'w' } : { t: 'VAT ' + num(m.thue) + '%', c: 'b' });
  if (daSua) ra.push({ t: 'Đã sửa số mua', c: 'b' });
  return ra;
}

/* THUẦN: món có hợp chip lọc đang chọn không. */
function gmHopLoc(m, g, loc, homNay) {
  if (loc === 'gap') return gmGap(m, homNay);
  if (loc === 'kho') return (Number(m.ton) || 0) > 0;
  if (loc === 'ncc') return !g.ncc;
  if (loc === 'sua') return GM.sua[m.ma] != null && Math.abs((Number(GM.sua[m.ma]) || 0) - m.xin) > 0.0001;
  return true;
}

/* THUẦN: tiền thuế tạm tính của nhóm theo số đang hiện. */
function gmThue(nhom) {
  return Math.round((nhom.mon || []).reduce(function (t, m) {
    return t + (Number(gmSoMua(m)) || 0) * (m.gia || 0) * (Number(m.thue) || 0) / 100;
  }, 0));
}

function gmStChip(x) {
  return '<span class="st ' + x.c + '" style="font-size:11.5px;padding:3px 8px">' + h(x.t) + '</span>';
}

function gmMon(m, i) {
  var mo = !!GM.mo[m.ma];
  var lech = Math.abs((Number(gmSoMua(m)) || 0) - m.xin) > 0.0001;
  return '<div class="khsx-the" data-gmmon="' + h(m.ma) + '" data-gmchu="' + h((m.ten || '') + ' ' + m.ma) + '"><div class="li" style="align-items:flex-start">' + anhMon(m.anh) +
    '<div class="lt"><div class="l1" style="white-space:normal;word-break:break-word">' + h(m.ten) + '</div>' +
    '<div class="l2">Xin ' + kl(m.xin, m.dvt) + (m.gia ? ' · giá lần trước ' + money(m.gia) + ' đ' : ' · chưa có giá mua') + '</div>' +
    '<div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:6px">' + gmChipMon(m, today(), lech).map(gmStChip).join('') +
    '<button type="button" data-gmmo="' + h(m.ma) + '" class="st n" style="font-size:11.5px;padding:3px 8px;border:0;cursor:pointer;min-height:24px">' +
    m.phieu.length + ' phiếu xin ' + (mo ? '▴' : '▾') + '</button></div></div>' +
    '<input class="tin" data-gmsl="' + h(m.ma) + '" inputmode="decimal" value="' + h(gmSoMua(m)) + '" ' +
    'style="width:84px;margin:0;text-align:center;flex:none' + (lech ? ';border-color:#0B7C93;font-weight:700' : '') + '" aria-label="Số mua ' + h(m.ten) + '">' +
    '</div>' +
    (mo ? '<div style="padding:0 14px 10px 14px;font-size:12.5px;color:#5a6070;line-height:1.7">' +
      m.phieu.map(function (p) {
        return '• ' + h(p.phieu) + ' · ' + h(p.bo_phan || 'bộ phận chưa ghi') + ' · ' + kl(p.xin, m.dvt) + (p.ngay ? ' · cần ' + h(dmy(p.ngay)) : '');
      }).join('<br>') + '</div>' : '') +
    '</div>';
}

function gmNhom(g, i) {
  var tien = gmTien(g), thue = gmThue(g);
  var chuaThue = (g.mon || []).filter(function (m) { return m.thue == null; }).length;
  return '<div class="card" data-gmnhom="' + i + '" data-gmncc="' + h((g.ten_ncc || '') + ' ' + (g.ncc || '')) + '" style="padding:12px 12px 14px;margin-bottom:14px">' +
    '<div style="font-size:15.5px;font-weight:700;line-height:1.35;word-break:break-word">' + h(g.ten_ncc) + '</div>' +
    '<div style="display:flex;flex-wrap:wrap;gap:5px;margin:6px 0 10px">' +
    gmStChip({ t: g.so_mon + ' món · ' + g.so_phieu + ' phiếu', c: 'n' }) +
    (g.ncc ? gmStChip({ t: 'Chờ thu mua chốt', c: 'b' }) : gmStChip({ t: 'Chưa có nhà cung cấp', c: 'w' })) +
    (chuaThue ? gmStChip({ t: chuaThue + ' món chưa khai VAT', c: 'w' }) : '') + '</div>' +
    '<div class="lst">' + g.mon.map(gmMon).join('') + '</div>' +
    '<div style="font-size:13px;color:#374151;margin:10px 2px 8px;line-height:1.5">' +
    (g.ncc ? 'Tạm tính ' + money(tien) + ' đ' + (thue ? ' + VAT ' + money(thue) + ' đ = <b>' + money(tien + thue) + ' đ</b>' : '') +
      '<div style="font-size:12px;color:#6b7280">Giá lần mua trước, thuế theo mẫu VAT khai trên từng món.</div>'
      : 'Bấm Chốt để chọn nhà cung cấp cho nhóm này.') + '</div>' +
    '<button class="btn gr" data-gmchot="' + i + '" style="margin:0">✅ Chốt đơn ' + g.so_mon + ' món</button></div>';
}

/* Dải tiến độ một yêu cầu mua đi qua: thu mua đang ở bước 2. */
function gmTienDo() {
  var b = [['Bộ phận gửi yêu cầu', 'g'], ['Thu mua gom, chốt đơn', 'b'], ['Gửi đơn cho nhà cung cấp', 'n'], ['Kho nhận hàng', 'n']];
  return '<div style="display:flex;flex-wrap:wrap;gap:5px;margin:0 0 10px">' + b.map(function (x, i) {
    return '<span class="st ' + x[1] + '" style="font-size:11.5px;padding:4px 8px' + (i === 1 ? ';outline:2px solid #0B7C93' : '') + '">' +
      (i === 0 ? '✓ ' : (i + 1) + '. ') + h(x[0]) + (i === 1 ? ' (đang ở đây)' : '') + '</span>';
  }).join('') + '</div>';
}

/* Chip lọc đầu màn, bấm được. Đếm theo món. */
function gmChipLoc(nhom) {
  var hn = today(), dem = { '': 0, gap: 0, kho: 0, ncc: 0, sua: 0 };
  nhom.forEach(function (g) {
    (g.mon || []).forEach(function (m) {
      ['', 'gap', 'kho', 'ncc', 'sua'].forEach(function (k) { if (gmHopLoc(m, g, k, hn)) dem[k]++; });
    });
  });
  var ds = [['', 'Tất cả'], ['gap', '🔴 Cần gấp'], ['kho', '📦 Kho tổng còn hàng'], ['ncc', '⚠️ Chưa có nhà cung cấp'], ['sua', '✏️ Đã sửa số']];
  return '<div class="chips" style="flex-wrap:wrap;overflow:visible">' + ds.filter(function (x) { return !x[0] || dem[x[0]]; }).map(function (x) {
    return '<button type="button" class="chip' + (GM.loc === x[0] ? ' on' : '') + '" data-gmloc="' + x[0] + '">' + h(x[1]) + ' ' + dem[x[0]] + '</button>';
  }).join('') + '</div>';
}

/* Ô tìm nhanh (Codex 549, 4204048; AGENTS.md 2b.5): lọc theo tên món, mã món
   và tên nhà cung cấp, bỏ dấu. Chỉ ẩn hiện thẻ trên màn, số đã sửa giữ nguyên;
   nhóm không còn món nào khớp thì ẩn cả nhóm. Chữ đang tìm giữ qua lần vẽ lại. */
function gmLoc(b) {
  var q = vgbChuan(GM.tim || ''), thay = 0;
  Array.prototype.forEach.call(b.querySelectorAll('[data-gmnhom]'), function (g) {
    var ncc = g.getAttribute('data-gmncc') || '', con = 0;
    Array.prototype.forEach.call(g.querySelectorAll('[data-gmmon]'), function (m) {
      var gi = GM.d && GM.d.nhom ? GM.d.nhom[+g.getAttribute('data-gmnhom')] : null;
      var mon = gi ? (gi.mon || []).filter(function (x) { return x.ma === m.getAttribute('data-gmmon'); })[0] : null;
      var hop = (!q || vgbKhop((m.getAttribute('data-gmchu') || '') + ' ' + ncc, q)) &&
        (!GM.loc || !mon || gmHopLoc(mon, gi, GM.loc, today()));
      m.style.display = hop ? '' : 'none';
      if (hop) con++;
    });
    g.style.display = con ? '' : 'none';
    thay += con;
  });
  var tr = b.querySelector('#gmTimTrong');
  if (tr) tr.style.display = (q && !thay) ? '' : 'none';
}

async function scrGomMua(giu) {
  if (!coQuyenMua()) {
    frame('Gom yêu cầu mua', '<div class="emp"><div class="e1">🔒</div><div class="e2">Màn này chỉ mở cho Thu mua, Kế toán và Giám đốc.</div></div>');
    return;
  }
  if (!giu || !GM.d) {
    frame('Gom yêu cầu mua', '<div class="emp"><div class="e1">⏳</div></div>');
    /* Tải lại không xoá số đã sửa: chỉ bỏ số của món không còn trên màn. */
    try { GM.d = await api('vagabond.gom_mua.ds', {}); GM.sua = gmGiuSua(GM.sua, GM.d); }
    catch (e) {
      frame('Gom yêu cầu mua', '<div class="emp"><div class="e1">⚠️</div><div class="e2">' + h(errMsg(e)) + '</div></div>');
      return;
    }
  }
  if (gmKhoiPhuc) { GM.sua = gmGiuSua(gmKhoiPhuc, GM.d); gmKhoiPhuc = null; }
  var d = GM.d, nhom = d.nhom || [];
  var html = gmTienDo() + '<div class="card" style="padding:12px 14px;font-size:13.5px;line-height:1.55;color:#374151">' +
    '<b>' + d.so_phieu + ' phiếu</b> yêu cầu mua chưa duyệt, <b>' + nhom.length + ' nhà cung cấp</b>. ' +
    'Số mua điền sẵn bằng tổng số xin: sửa nếu cần (gõ 0 là chưa mua đợt này), rồi bấm Chốt đơn.</div>' +
    (nhom.length ? gmChipLoc(nhom) + vgbOTim('gmTim', nhom.reduce(function (t, g) { return t + (g.mon || []).length; }, 0),
      '🔎 Gõ tên món, mã món hoặc nhà cung cấp') + nhom.map(gmNhom).join('')
      : '<div class="emp"><div class="e1">🎉</div><div class="e2">Không còn yêu cầu mua nào chờ gom</div></div>');
  var b = frame('Gom yêu cầu mua', html, { action: '&#8635;', onAction: function () { GM.d = null; scrGomMua(); } });
  var oTim = b.querySelector('#gmTim');
  if (oTim) {
    oTim.value = GM.tim || '';
    oTim.oninput = function () { GM.tim = oTim.value; gmLoc(b); };
    gmLoc(b);
  }
  Array.prototype.forEach.call(b.querySelectorAll('[data-gmsl]'), function (o) {
    o.onclick = function (ev) { ev.stopPropagation(); };
    o.oninput = function () {
      var v = parseFloat(String(o.value).replace(',', '.'));
      GM.sua[o.dataset.gmsl] = isNaN(v) ? null : v;
    };
  });
  b.onclick = async function (e) {
    var lc = e.target.closest('[data-gmloc]');
    if (lc) { GM.loc = lc.getAttribute('data-gmloc') || ''; return scrGomMua(1); }
    var c = e.target.closest('[data-gmchot]');
    if (c) return gmChot(nhom[+c.dataset.gmchot]);
    var m = e.target.closest('[data-gmmo]');
    if (m) { GM.mo[m.dataset.gmmo] = GM.mo[m.dataset.gmmo] ? 0 : 1; return scrGomMua(1); }
  };
}

/* Nhóm chưa có nhà cung cấp: CHỌN từ danh mục có ô tìm nhanh (Codex 549,
   AGENTS.md QT-31), không bắt thu mua gõ đúng mã. Trả { ncc, ten } hoặc null. */
async function gmChonNcc() {
  var r;
  busy(1);
  try { r = await api('vagabond.gom_mua.tim_ncc', {}); }
  catch (e) { toast(errMsg(e), 6000); return null; }
  finally { busy(0); }
  var ds = (r && r.ds) || [];
  if (!ds.length) { toast('Danh mục chưa có nhà cung cấp nào đang dùng. Thêm ở màn Nhà cung cấp rồi chốt lại.', 6000); return null; }
  var k = await hoiChon('Chọn nhà cung cấp cho nhóm này',
    'Đơn mua lập cho nhà được chọn. Gõ vài chữ tên hoặc mã số thuế để tìm nhanh.',
    ds.map(function (x) { return { k: x.ncc, nhan: x.ten, mo_ta: x.mst ? 'MST ' + x.mst : '' }; }));
  if (!k) return null;
  var t = ds.filter(function (x) { return x.ncc === k; })[0];
  return { ncc: k, ten: (t && t.ten) || k };
}

async function gmChot(g) {
  if (!g) return;
  var dong = gmDongChot(g);
  var hong = dong.filter(function (x) { return x.sl == null || isNaN(Number(x.sl)) || Number(x.sl) < 0; });
  if (hong.length) return toast('Còn ô số mua để trống hoặc gõ sai, gõ 0 nếu chưa mua đợt này', 5000);
  var ncc = '', tenNcc = g.ten_ncc;
  if (!g.ncc) {
    var c = await gmChonNcc();
    if (!c) return;
    ncc = c.ncc; tenNcc = c.ten;
  }
  var so0 = dong.filter(function (x) { return Number(x.sl) === 0; }).length;
  if (!await confirmSheet('Chốt đơn ' + tenNcc + '?',
    'Máy duyệt ' + g.so_phieu + ' phiếu xin theo số đang hiện và lập đơn mua ' + (dong.length - so0) + ' món.' +
    (gmTien(g) ? '\nTạm tính ' + money(gmTien(g)) + ' đ' + (gmThue(g) ? ' + VAT ' + money(gmThue(g)) + ' đ = ' + money(gmTien(g) + gmThue(g)) + ' đ' : '') +
      '. VAT theo mẫu thuế khai trên từng món; sai thì sửa mẫu thuế của món trước khi chốt.' : '') +
    (so0 ? '\n\n' + so0 + ' món gõ 0: các dòng xin đó bị từ chối, ghi lý do "chưa mua đợt này".' : '') +
    '\n\nĐơn mua chưa gửi nhà cung cấp; gửi ở màn Đơn mua hàng.', 'Chốt đơn')) return;
  busy(1);
  try {
    var r = await api('vagabond.gom_mua.chot', { ncc: g.ncc, dong: JSON.stringify(dong), ncc_chon: ncc || null });
    /* Codex 549 (1eefda8): món vừa chốt bỏ khỏi số đã sửa. Phiếu xin mới của
       cùng món về sau phải hiện số máy mới, không mang số cũ (hay số 0) đi chốt lại. */
    dong.forEach(function (x) { delete GM.sua[x.ma]; });
    /* Ghi lại bản nháp ngay (phần 48), không để bản cũ còn số món vừa chốt. */
    if (typeof sdLuuNgay === 'function') { try { sdLuuNgay(); } catch (e2) { } }
    toast(r.ghi_chu, 8000);
    GM.d = null;
    if (r.don) { poXem = r.don; return go(scrDonMuaXem); }
    await scrGomMua();
  } catch (e) { toast(errMsg(e), 7000); } finally { busy(0); }
}

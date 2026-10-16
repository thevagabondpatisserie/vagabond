/* ===================================================================
   GIÁ VỐN TẠM TÍNH (Issue #482, anh Việt 16/10/2026)

   Cho kế toán giá thành (Khải) xem giá vốn nguyên liệu của từng bánh bán
   ra, cộng dồn qua từng lớp bán thành phẩm theo giá kho hôm nay, so với giá
   bán, và giá bán đề xuất theo tỷ lệ giá vốn mục tiêu của nhóm. Bấm Chốt thì
   máy chủ lưu vào bảng giá riêng "Giá vốn tạm tính".

   Màn này chỉ ĐỌC, trừ hai việc ghi đều qua máy chủ: lưu tỷ lệ mục tiêu và
   chốt bảng giá. Không đụng công thức, tồn kho hay sổ sách. Mọi con số
   (giá vốn, trạng thái, giá đề xuất, quyền) do máy chủ tính; màn chỉ lọc và
   bày ra (vagabond/gia_von_tam.py).
   =================================================================== */

var GVT = { kq: null, nhom: '', tt: '', tim: '', moCct: false };

var GVT_TT = {
  vuot_gia_ban: { nhan: 'Vượt giá bán', mau: '#b3261e', nen: '#fef2f2' },
  thieu_gia: { nhan: 'Thiếu giá NVL', mau: '#b45309', nen: '#fffbeb' },
  vong: { nhan: 'Công thức vòng', mau: '#b3261e', nen: '#fef2f2' },
  cao_hon_muc_tieu: { nhan: 'Cao hơn mục tiêu', mau: '#b45309', nen: '#fffbeb' }
};
/* Codex #483 vong 3: co ca 'vong' de loc rieng duoc mon cong thuc vong. Chip
   chi hien khi co mon o trang thai do (xem gvtVe). */
var GVT_CHIP_TT = ['vuot_gia_ban', 'vong', 'thieu_gia', 'cao_hon_muc_tieu'];
var GVT_TIEU_DE = 'Giá vốn tạm tính';

function gvtPhanTram(x) { return x == null ? '' : String(x).replace('.', ',') + '%'; }

function gvtNgay(s) {
  var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(s || ''));
  return m ? m[3] + '/' + m[2] : String(s || '');
}

/* Danh sách đang lọc. Thứ tự đã do máy chủ xếp (cần xử lên trước). */
function gvtLoc() {
  var kq = GVT.kq || {};
  return (kq.dong || []).filter(function (d) {
    if (GVT.nhom && d.nhom !== GVT.nhom) return false;
    if (GVT.tt && d.trang_thai !== GVT.tt) return false;
    return vgbKhop([d.ten, d.ma], GVT.tim);
  });
}

/* Chip trạng thái có chữ trên MỌI thẻ (Codex #483 vòng 2, AGENTS 2b điều 3):
   xanh đạt, vàng cần xem, đỏ cần xử, xám chưa đủ dữ liệu. */
var GVT_CHIP = {
  dat: ['Đạt mục tiêu', '#047857', '#ecfdf5'],
  cao_hon_muc_tieu: ['Cao hơn mục tiêu', '#b45309', '#fffbeb'],
  vuot_gia_ban: ['Vượt giá bán', '#b3261e', '#fef2f2'],
  thieu_gia: ['Thiếu giá NVL', '#b45309', '#fffbeb'],
  vong: ['Công thức vòng', '#b3261e', '#fef2f2'],
  chua_gia_ban: ['Chưa có giá bán', '#6b7280', '#f3f4f6'],
  chua_dat_ty_le: ['Chưa đặt mục tiêu', '#6b7280', '#f3f4f6']
};
function gvtChipTrangThai(d) {
  var c = GVT_CHIP[d.trang_thai] || [d.trang_thai, '#6b7280', '#f3f4f6'];
  return '<span data-gvttt="' + h(d.trang_thai) + '" style="flex:none;font-size:13px;font-weight:800;color:' + c[1] +
    ';background:' + c[2] + ';border-radius:999px;padding:4px 10px;white-space:nowrap">' + h(c[0]) + '</span>';
}

function gvtThe(d) {
  var dong3;
  if (d.trang_thai === 'thieu_gia' || d.trang_thai === 'vong') dong3 = '';
  else if (d.gia_de_xuat) dong3 = 'Đề xuất ' + money(d.gia_de_xuat) + 'đ (mục tiêu ' + gvtPhanTram(d.ty_le_muc_tieu) + ')';
  else if (!d.gia_ban) dong3 = 'Chưa có giá bán';
  else dong3 = 'Chưa đặt tỷ lệ mục tiêu';
  var co = '';
  if (d.trang_thai === 'thieu_gia') {
    var ten = (d.thieu_ten || []).slice(0, 2);
    var con = (d.thieu_so || 0) - ten.length;
    co = 'Thiếu giá ' + d.thieu_so + ' nguyên liệu: ' + ten.join(', ') + (con > 0 ? ' và ' + con + ' nữa' : '');
  } else if (d.trang_thai === 'vuot_gia_ban') {
    co = 'Giá vốn vượt giá bán. Xem lại đơn vị trong công thức.';
  } else if (d.trang_thai === 'vong') {
    co = 'Công thức trỏ vòng vào chính nó, chưa tính được.';
  }
  var tt = GVT_TT[d.trang_thai];
  return '<div class="hub" data-gvtm="' + h(d.ma) + '" style="align-items:flex-start">' + anhMon(d.anh) +
    '<div class="hub-t" style="flex:1;min-width:0">' +
      '<div style="display:flex;gap:8px;align-items:center"><div class="t1" style="flex:1;min-width:0">' + h(d.ten) + '</div>' + gvtChipTrangThai(d) + '</div>' +
      '<div class="t2">Giá vốn ' + money(d.gia_von) + 'đ · ' + (d.gia_ban ? 'Giá bán ' + money(d.gia_ban) + 'đ' : 'Chưa có giá bán') +
        (d.ty_le != null ? ' · <b>' + gvtPhanTram(d.ty_le) + '</b>' : '') + '</div>' +
      (dong3 ? '<div class="t2" style="color:#0f766e;font-weight:700">' + h(dong3) + '</div>' : '') +
      (d.lan_truoc ? '<div class="t2">Lần chốt ' + gvtNgay(d.lan_truoc.ngay) + ': ' + money(d.lan_truoc.gia) + 'đ (' +
        (d.lan_truoc.chenh_pct > 0 ? '+' : '') + gvtPhanTram(d.lan_truoc.chenh_pct) + ')</div>' : '') +
      (co ? '<div class="t2" data-gvtco style="color:' + (tt ? tt.mau : '#b45309') + '">' + h(co) + '</div>' : '') +
    '</div></div>';
}

function gvtVeDs() {
  var kq = GVT.kq || {};
  var ds = gvtLoc();
  var html = '';
  if (!ds.length) {
    html = '<div class="card"><div class="emp" style="padding:24px"><div class="e1">🍰</div>' +
      '<div>Không có bánh nào khớp. Bỏ bớt bộ lọc hoặc đổi từ khoá.</div>' +
      '<button class="btn gh" data-gvtbo style="margin-top:12px">Bỏ lọc</button></div></div>';
  } else {
    (kq.nhom || []).forEach(function (n) {
      var cua = ds.filter(function (d) { return d.nhom === n.ten; });
      if (!cua.length) return;
      html += '<div class="sec">' + h(n.ten) + ', ' +
        (n.ty_le_muc_tieu ? 'mục tiêu ' + gvtPhanTram(n.ty_le_muc_tieu) : 'chưa đặt mục tiêu') + '</div>' +
        '<div class="card">' + cua.map(gvtThe).join('') + '</div>';
    });
  }
  /* Codex #483 vong 3: mon co nhieu cong thuc dang chay ma chua chon ban mac
     dinh thi may chu KHONG doan, man noi ro ten va cach sua. */
  var nct = kq.nhieu_cong_thuc || {};
  if (nct.so) {
    html += '<div class="card" data-gvtnct style="padding:12px 14px">' +
      '<div style="font-size:13.5px;color:#b45309">' + nct.so + ' món có nhiều công thức nhưng chưa chọn công thức mặc định nên chưa tính. ' +
      'Mở công thức đúng trên Desk, tích Mặc định rồi tính lại.</div>' +
      '<div style="font-size:13px;color:#6b7280;margin-top:8px;line-height:1.6">' +
      (nct.ten || []).map(h).join(', ') + (nct.so > (nct.ten || []).length ? ' và ' + (nct.so - nct.ten.length) + ' nữa' : '') +
      '</div></div>';
  }
  var cct = kq.chua_cong_thuc || {};
  if (cct.so) {
    html += '<div class="card" data-gvtcct style="padding:12px 14px;cursor:pointer">' +
      '<div style="font-size:13.5px;color:#4b5563">' + cct.so + ' món chưa có công thức nên chưa tính được. ' +
      (GVT.moCct ? 'Bấm để thu gọn.' : 'Bấm để xem.') + '</div>' +
      (GVT.moCct ? '<div data-gvtcctds style="font-size:13px;color:#6b7280;margin-top:8px;line-height:1.6">' +
        (cct.ten || []).map(h).join(', ') + (cct.so > (cct.ten || []).length ? ' và ' + (cct.so - cct.ten.length) + ' nữa' : '') +
        '</div>' : '') + '</div>';
  }
  return html;
}

function gvtVe() {
  var kq = GVT.kq || {};
  var dong = kq.dong || [];
  var html = '<div class="card" style="padding:12px 14px"><div style="font-size:13.5px;color:#4b5563;line-height:1.55">' +
    'Tiền nguyên liệu theo công thức đang dùng, tính dồn qua bán thành phẩm, theo giá kho hôm nay. ' +
    'Chưa gồm bao bì, công, hao hụt. Chỉ để định giá, không đổi sổ sách.</div>' +
    '<div style="font-size:12.5px;color:#9ca3af;margin-top:6px">Tính lúc ' + h(kq.cap_nhat_luc || '') + '</div>' +
    '<input class="tin" id="gvtQ" placeholder="Tìm tên hoặc mã bánh" value="' + h(GVT.tim) + '" style="margin:10px 0 0"></div>';

  var chipNhom = posChipNut('data-gvtn=""', 'Tất cả ' + dong.length, !GVT.nhom);
  (kq.nhom || []).forEach(function (n) {
    if (!n.so_mon) return;
    chipNhom += posChipNut('data-gvtn="' + h(n.ten) + '" title="' + h(n.ten) + '"', h(n.nhan) + ' ' + n.so_mon, GVT.nhom === n.ten);
  });
  var chipTt = '';
  GVT_CHIP_TT.forEach(function (t) {
    var so = dong.filter(function (d) { return d.trang_thai === t; }).length;
    if (!so && GVT.tt !== t) return;
    chipTt += posChipNut('data-gvtt="' + t + '"', GVT_TT[t].nhan + ' ' + so, GVT.tt === t, false, GVT_TT[t].mau);
  });
  html += '<div class="card" style="padding:10px 12px;overflow-x:auto"><div style="display:flex;gap:7px;padding:0 2px">' + chipNhom + '</div>' +
    (chipTt ? '<div style="display:flex;gap:7px;padding:8px 2px 0">' + chipTt + '</div>' : '') + '</div>';
  if (kq.sua_duoc) html += '<button class="btn gh" data-gvttyle style="margin:0 0 10px">Tỷ lệ mục tiêu</button>';
  html += '<div id="gvtDs">' + gvtVeDs() + '</div>';

  var b = frame(GVT_TIEU_DE, html, kq.sua_duoc ? { footer: '<button class="btn" id="gvtChot">Chốt vào bảng Giá vốn tạm tính</button>' } : {});
  var q = document.getElementById('gvtQ');
  if (q) q.oninput = function () {
    GVT.tim = q.value;
    var ds = document.getElementById('gvtDs');
    if (ds) ds.innerHTML = gvtVeDs();
  };
  b.onclick = function (e) {
    var t = e.target;
    var el;
    if ((el = t.closest('[data-gvtn]'))) { GVT.nhom = el.getAttribute('data-gvtn') || ''; return gvtVe(); }
    if ((el = t.closest('[data-gvtt]'))) { var k = el.getAttribute('data-gvtt'); GVT.tt = GVT.tt === k ? '' : k; return gvtVe(); }
    if (t.closest('[data-gvtbo]')) { GVT.nhom = ''; GVT.tt = ''; GVT.tim = ''; return gvtVe(); }
    if (t.closest('[data-gvtcct]')) { GVT.moCct = !GVT.moCct; return gvtVe(); }
    if (t.closest('[data-gvttyle]')) return gvtSuaTyLe();
    if ((el = t.closest('[data-gvtm]'))) return gvtChiTiet(el.getAttribute('data-gvtm'), null, []);
  };
  var c = document.getElementById('gvtChot');
  if (c) c.onclick = gvtChot;
  return b;
}

function gvtLoi(e) {
  var m = (e && e.message) || '';
  var cau = /quyền/i.test(m) ? m : 'Không tải được giá vốn. Kiểm mạng rồi bấm Thử lại.';
  var b = frame(GVT_TIEU_DE, '<div class="emp"><div class="e1">⚠️</div><div>' + h(cau) + '</div>' +
    '<button class="btn" data-gvtlai style="margin-top:12px">Thử lại</button></div>');
  b.onclick = function (ev) { if (ev.target.closest('[data-gvtlai]')) scrGiaVonTam(); };
}

async function scrGiaVonTam() {
  frame(GVT_TIEU_DE, '<div class="emp"><div class="e1">⏳</div><div>Đang tính giá vốn...</div></div>');
  try { GVT.kq = await api('vagabond.gia_von_tam.tinh', {}); }
  catch (e) { GVT.kq = null; return gvtLoi(e); }
  gvtVe();
}

/* Sheet tỷ lệ mục tiêu: mỗi nhóm một ô %. Ô ngoài 1 tới 95 bị chặn tại chỗ,
   không gửi lên máy chủ (máy chủ vẫn kiểm lại, chuan_ty_le). */
function gvtSuaTyLe() {
  var kq = GVT.kq || {};
  var nhom = (kq.nhom || []).filter(function (n) { return n.so_mon; });
  var ov = document.createElement('div'); ov.className = 'sh';
  ov.innerHTML = '<div class="shb" style="padding:18px 16px calc(env(safe-area-inset-bottom,0px) + 16px)">' +
    '<div style="font-size:17.5px;font-weight:700;margin-bottom:6px">Tỷ lệ giá vốn mục tiêu</div>' +
    '<div style="font-size:13.5px;color:#5a6070;line-height:1.5;margin-bottom:12px">Giá bán đề xuất = giá vốn tạm chia tỷ lệ này, làm tròn lên nghìn. ' +
    'Để trống thì không đề xuất giá cho nhóm đó.</div>' +
    nhom.map(function (n) {
      return '<div style="margin-bottom:12px"><div style="display:flex;align-items:center;gap:10px">' +
        '<div style="flex:1;font-size:14.5px;font-weight:600">' + h(n.ten) + '</div>' +
        '<input class="nt" data-gvtpct="' + h(n.ten) + '" inputmode="decimal" value="' + (n.ty_le_muc_tieu == null ? '' : h(String(n.ty_le_muc_tieu).replace('.', ','))) +
        '" style="width:84px;height:44px;text-align:right;padding:0 10px"><span>%</span></div>' +
        '<div style="font-size:12.5px;color:#9ca3af">' + (n.trung_vi != null ? 'Hiện trung vị ' + gvtPhanTram(n.trung_vi) : 'Chưa đủ số để tính trung vị') + '</div>' +
        '<div data-gvtsai="' + h(n.ten) + '" style="font-size:12.5px;color:#b3261e"></div></div>';
    }).join('') +
    '<button class="btn" data-gvtluu>Lưu tỷ lệ</button><button class="btn gh" data-gvthuy style="margin-top:9px">Huỷ</button></div>';
  document.body.appendChild(ov);
  ov.onclick = async function (e) {
    if (e.target === ov || e.target.closest('[data-gvthuy]')) { ov.remove(); return; }
    if (!e.target.closest('[data-gvtluu]')) return;
    var ty = {}, sai = 0;
    nhom.forEach(function (n) {
      var o = ov.querySelector('[data-gvtpct="' + n.ten + '"]');
      var bao = ov.querySelector('[data-gvtsai="' + n.ten + '"]');
      var v = String((o && o.value) || '').trim().replace(',', '.');
      if (bao) bao.innerHTML = '';
      if (!v) { ty[n.ten] = ''; return; }
      var p = parseFloat(v);
      if (isNaN(p) || p < 1 || p > 95) { sai++; if (bao) bao.innerHTML = 'Nhập số từ 1 tới 95.'; return; }
      ty[n.ten] = p;
    });
    if (sai) return;
    busy(true);
    try { await api('vagabond.gia_von_tam.luu_ty_le', { ty_le: JSON.stringify(ty) }); busy(false); }
    catch (er) { busy(false); return baoTin((er && er.message) || 'Lưu tỷ lệ lỗi'); }
    ov.remove();
    toast('Đã lưu tỷ lệ mục tiêu', 3000);
    scrGiaVonTam();
  };
}

/* Sheet chi tiết: một tầng mỗi lần, chỉ gọi máy chủ khi bấm. Dòng bán thành
   phẩm có mũi tên mở xuống tầng con, tối đa 6 tầng. */
async function gvtChiTiet(ma, bom, duong) {
  var ct;
  busy(true);
  try { ct = await api('vagabond.gia_von_tam.chi_tiet', bom ? { ma: ma, bom: bom } : { ma: ma }); busy(false); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Không mở được chi tiết'); }
  var dong = ct.dong || [];
  var hien = dong.slice(0, 30);
  var ov = document.createElement('div'); ov.className = 'sh';
  ov.innerHTML = '<div class="shb"><div class="shh"><b>' + h(ct.ten) + '</b><div class="x" data-gvtdong>&times;</div></div>' +
    '<div style="padding:4px 14px 8px;font-size:13px;color:#6b7280">Một mẻ ra ' + (ct.so_ra || 1) + ' · giá vốn ' + money(ct.gia) + 'đ mỗi đơn vị' +
    (duong.length ? ' · <span data-gvtlui style="color:#0d9488;font-weight:700;cursor:pointer">‹ Quay lại</span>' : '') + '</div>' +
    '<div class="shl">' + hien.map(function (d) {
      var xuong = d.bom_con && duong.length < 5;
      return '<div class="shi"' + (xuong ? ' data-gvtcon="' + h(d.ma) + '" data-gvtbom="' + h(d.bom_con) + '"' : '') + ' style="align-items:flex-start">' +
        '<span style="flex:1;min-width:0">' + h(d.ten) +
        '<div style="color:#6b7280;font-size:12.5px;margin-top:2px">' + kl(d.sl, d.dvt) + ' · ' + money(d.don_gia) + 'đ/' + h(d.dvt) + ' (' + h(d.nguon) + ')' +
        (d.thieu ? ' · <span style="color:#b45309">thiếu giá</span>' : '') + '</div></span>' +
        '<span style="font-weight:700;white-space:nowrap">' + money(d.thanh_tien) + 'đ' + (xuong ? ' ›' : '') + '</span></div>';
    }).join('') +
    (dong.length > hien.length ? '<div style="padding:10px 14px;font-size:13px;color:#6b7280">và ' + (dong.length - hien.length) + ' nữa</div>' : '') +
    '</div></div>';
  document.body.appendChild(ov);
  ov.onclick = function (e) {
    if (e.target === ov || e.target.closest('[data-gvtdong]')) { ov.remove(); return; }
    if (e.target.closest('[data-gvtlui]')) { ov.remove(); var tr = duong[duong.length - 1]; return gvtChiTiet(tr.ma, tr.bom, duong.slice(0, -1)); }
    var con = e.target.closest('[data-gvtcon]');
    if (con) { ov.remove(); gvtChiTiet(con.getAttribute('data-gvtcon'), con.getAttribute('data-gvtbom'), duong.concat([{ ma: ma, bom: bom }])); }
  };
}

async function gvtChot() {
  var dong = (GVT.kq || {}).dong || [];
  var bo = { thieu_gia: 1, vong: 1 };
  var n = dong.filter(function (d) { return !bo[d.trang_thai] && d.gia_von > 0; }).length;
  var m = dong.length - n;
  var ngay = gvtNgay((GVT.kq || {}).ngay) + '/' + String((GVT.kq || {}).ngay || '').slice(0, 4);
  if (!await confirmSheet('Chốt giá vốn tạm',
    'Lưu giá vốn tạm của ' + n + ' món vào bảng giá Giá vốn tạm tính, ngày ' + ngay + '. ' +
    (m ? m + ' món chưa tính đủ giá (thiếu giá nguyên liệu) sẽ bỏ qua. ' : '') + 'Không đổi công thức, tồn kho hay sổ sách.', 'Chốt')) return;
  var kq;
  busy(true);
  try { kq = await api('vagabond.gia_von_tam.chot', {}); busy(false); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Chốt lỗi'); }
  var boQua = 0;
  Object.keys(kq.bo_qua || {}).forEach(function (k) { boQua += kq.bo_qua[k]; });
  toast('Đã lưu ' + kq.da_luu + ' món.' + (boQua ? ' Bỏ qua ' + boQua + ' món.' : ''), 5000);
  scrGiaVonTam();
}

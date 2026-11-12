/* ---------- 71. Dự chi công nợ: trả nhà cung cấp hai đợt 10 và 20 (v653) ----------

   Anh Việt 12/11/2026 (issue #555): thay bảng Excel "Dự chi công nợ" bằng một
   màn trên app. Máy (vagabond/du_chi.py) soạn sẵn đợt nháp ngày 7 và 17 từ dư
   nợ ERP; Uyên thương lượng từng nhà cung cấp, bấm Trả hết hoặc gõ số trả từng
   hoá đơn, máy tính phần gia hạn. Gửi duyệt: kế toán soát, giám đốc duyệt CẢ
   ĐỢT một lần, máy lập APP từng nhà cung cấp luôn.

   Màn chỉ gửi số trả, ghi chú, hẹn đợt; máy chủ đọc lại dư nợ và phần APP khác
   đang giữ dưới khoá rồi mới lưu (QT-19).

   Tiền tố dcn = dự chi nợ. */

var DCN = { ds: null, d: null, sua: {}, mo: {}, tim: '', loc: '' };
var dcnKhoiPhuc = null;

/* THUẦN: số trả đang hiện của một dòng (đã gõ thì theo số gõ). */
function dcnSoTra(r) {
  var s = DCN.sua[r.hoa_don];
  return s && s.so_tra != null ? s.so_tra : r.so_tra;
}

/* THUẦN: gia hạn của một dòng theo số trả đang hiện. Không âm. */
function dcnGiaHan(r) {
  return Math.max(0, Math.round((Number(r.co_the_tra) || 0) - (Number(dcnSoTra(r)) || 0)));
}

/* THUẦN: dòng có số trả gõ hỏng hay vượt phần còn đề nghị được. */
function dcnHong(r) {
  var v = Number(dcnSoTra(r));
  return isNaN(v) || v < 0 || v > (Number(r.co_the_tra) || 0) + 0.5;
}

/* THUẦN: giữ số đã sửa của những hoá đơn còn trên đợt. */
function dcnGiuSua(sua, d) {
  var co = {}, ra = {};
  ((d && d.dong) || []).forEach(function (r) { co[r.hoa_don] = 1; });
  Object.keys(sua || {}).forEach(function (k) { if (co[k]) ra[k] = sua[k]; });
  return ra;
}

/* THUẦN: nhóm dòng theo nhà cung cấp, giữ thứ tự. */
function dcnNhom(dong) {
  var thu = [], m = {};
  (dong || []).forEach(function (r) {
    if (!m[r.ncc]) { m[r.ncc] = { ncc: r.ncc, ten: r.ten_ncc, nhom: r.nhom, dong: [] }; thu.push(m[r.ncc]); }
    m[r.ncc].dong.push(r);
  });
  return thu;
}

/* THUẦN: ba tổng của đợt theo số đang hiện. */
function dcnTong(dong) {
  var t = { de_nghi: 0, tra: 0, gia_han: 0 };
  (dong || []).forEach(function (r) {
    t.de_nghi += Number(r.co_the_tra) || 0;
    t.tra += Number(dcnSoTra(r)) || 0;
    t.gia_han += dcnGiaHan(r);
  });
  return t;
}

/* THUẦN: dòng tới hạn (hạn dự tính trước hoặc đúng ngày đợt). */
function dcnToiHan(r, ngayDot) { return !!r.han && r.han <= ngayDot; }

/* THUẦN: dòng gửi máy chủ lúc lưu: chỉ những dòng đã sửa. */
function dcnDongLuu() {
  return Object.keys(DCN.sua).map(function (k) {
    var s = DCN.sua[k], x = { hoa_don: k };
    if (s.so_tra != null) x.so_tra = s.so_tra;
    if (s.ghi_chu != null) x.ghi_chu = s.ghi_chu;
    if (s.hen_dot != null) x.hen_dot = s.hen_dot;
    return x;
  });
}

/* THUẦN: các đợt sau ngày đợt này để hẹn trả (ba đợt kế). */
function dcnDotSau(ngayDot) {
  var y = +ngayDot.slice(0, 4), m = +ngayDot.slice(5, 7), d = +ngayDot.slice(8, 10), ra = [];
  for (var i = 0; i < 3; i++) {
    if (d < 20) d = 20; else { d = 10; m++; if (m > 12) { m = 1; y++; } }
    ra.push(y + '-' + ('0' + m).slice(-2) + '-' + ('0' + d).slice(-2));
  }
  return ra;
}

/* THUẦN: chip nguồn số ngày được nợ. */
function dcnChuNo(x) {
  if (!x) return 'Nợ 30 ngày (mặc định)';
  return 'Nợ ' + x.so + ' ngày' + (x.nguon === 'khai' ? '' : x.nguon === 'goi_y' ? ' (máy gợi ý)' : ' (mặc định)');
}

function dcnSua(hd, k, v) {
  DCN.sua[hd] = DCN.sua[hd] || {};
  DCN.sua[hd][k] = v;
}

function dcnSt(t, c) {
  return '<span class="st ' + c + '" style="font-size:13px;padding:4px 9px">' + h(t) + '</span>';
}

/* Dải tiến độ của đợt: bốn bước, bước đang ở có viền. */
function dcnTienDo(tt) {
  var b = [['Nhap', 'Uyên thương lượng'], ['Cho ke toan', 'Kế toán soát'], ['Cho giam doc', 'Giám đốc duyệt'], ['Da chot', 'Đã lập APP']];
  var vi = { 'Nhap': 0, 'Cho ke toan': 1, 'Cho giam doc': 2, 'Da duyet': 3, 'Da chot': 3 }[tt];
  if (vi == null) vi = -1;
  return '<div style="display:flex;flex-wrap:wrap;gap:5px;margin:0 0 10px">' + b.map(function (x, i) {
    var c = i < vi || tt === 'Da chot' ? 'g' : i === vi ? 'b' : 'n';
    return '<span class="st ' + c + '" style="font-size:13px;padding:4px 9px' + (i === vi && tt !== 'Da chot' ? ';outline:2px solid #0B7C93' : '') + '">' +
      (c === 'g' ? '✓ ' : (i + 1) + '. ') + h(x[1]) + '</span>';
  }).join('') + '</div>';
}

function dcnDong(r, sua, ngayDot) {
  var mo = !!DCN.mo[r.hoa_don];
  var hong = dcnHong(r);
  var s = DCN.sua[r.hoa_don] || {};
  var ghiChu = s.ghi_chu != null ? s.ghi_chu : r.ghi_chu;
  var hen = s.hen_dot != null ? s.hen_dot : r.hen_dot;
  var chip = [];
  if (r.han) chip.push(dcnToiHan(r, ngayDot) ? dcnSt('Tới hạn ' + dmy(r.han).slice(0, 5), 'r') : dcnSt('Hạn ' + dmy(r.han).slice(0, 5), 'n'));
  if (r.dang_giu > 0) chip.push(dcnSt('APP khác giữ ' + money(r.dang_giu) + ' đ', 'w'));
  if (dcnGiaHan(r) > 0) chip.push(dcnSt('Gia hạn ' + money(dcnGiaHan(r)) + ' đ', 'b'));
  if (r.app) chip.push(dcnSt('Đã lập ' + r.app, 'g'));
  if (r.ket_qua) chip.push(dcnSt('Chưa lập được APP', 'r'));
  if (ghiChu) chip.push(dcnSt('Có ghi chú', 'n'));
  return '<div class="khsx-the" data-dcndong="' + h(r.hoa_don) + '" data-dcnchu="' + h((r.ten_ncc || '') + ' ' + (r.so_hd || '') + ' ' + r.hoa_don) + '">' +
    '<div class="li" data-dcnmo="' + h(r.hoa_don) + '" style="align-items:flex-start;min-height:44px;cursor:pointer">' +
    '<div class="lt"><div class="l1" style="white-space:normal">HĐ ' + h(r.so_hd || r.hoa_don) + ' · ' + h(dmy(r.ngay_hd)) + '</div>' +
    '<div class="l2">Còn đề nghị được ' + money(r.co_the_tra) + ' đ' + (r.con_no !== r.co_the_tra ? ' (dư nợ ' + money(r.con_no) + ' đ)' : '') + '</div>' +
    '<div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:6px">' + chip.join('') + '</div></div>' +
    (sua ? '<input class="tin" data-dcntra="' + h(r.hoa_don) + '" inputmode="numeric" value="' + h(String(Math.round(Number(dcnSoTra(r)) || 0))) + '" ' +
      'style="width:118px;margin:0;text-align:right;flex:none;font-size:15px' + (hong ? ';border-color:#b3261e;color:#b3261e' : '') + '" aria-label="Trả đợt này hoá đơn ' + h(r.so_hd || r.hoa_don) + '">'
      : '<div style="flex:none;text-align:right;font-weight:700;font-size:15px">' + money(r.so_tra) + ' đ</div>') +
    '</div>' +
    (hong ? '<div style="padding:0 14px 8px;font-size:13px;color:#b3261e">Số trả phải từ 0 tới ' + money(r.co_the_tra) + ' đ.</div>' : '') +
    (r.ket_qua ? '<div style="padding:0 14px 8px;font-size:13px;color:#b3261e">' + h(r.ket_qua) + '</div>' : '') +
    (mo ? '<div style="padding:0 14px 12px">' +
      (sua ? '<textarea class="tin" rows="2" data-dcngc="' + h(r.hoa_don) + '" placeholder="Ghi chú thương lượng, ví dụ: chị Lan đồng ý dời phần còn lại sang đợt 10/12" style="margin:0 0 8px;font-size:14px">' + h(ghiChu || '') + '</textarea>' +
        '<div style="font-size:13px;color:#374151;margin-bottom:6px">Hẹn trả phần gia hạn vào đợt</div>' +
        '<div class="chips" style="flex-wrap:wrap;overflow:visible">' + [''].concat(dcnDotSau(ngayDot)).map(function (n) {
          return '<button type="button" class="chip' + ((hen || '') === n ? ' on' : '') + '" data-dcnhen="' + h(r.hoa_don) + '" data-ngay="' + n + '" style="min-height:44px">' + (n ? dmy(n).slice(0, 5) : 'Chưa hẹn') + '</button>';
        }).join('') + '</div>'
        : '<div style="font-size:13.5px;color:#374151;line-height:1.55">' + (ghiChu ? h(ghiChu) : 'Không có ghi chú') + (hen ? '<br>Hẹn trả đợt ' + h(dmy(hen)) : '') + '</div>') +
      '</div>' : '') +
    '</div>';
}

function dcnNcc(g, i, d, sua) {
  var t = dcnTong(g.dong), no = (d.so_ngay_no || {})[g.ncc];
  return '<div class="card" data-dcnnhom="' + i + '" data-dcnncc="' + h((g.ten || '') + ' ' + (g.ncc || '')) + '" style="padding:12px 12px 14px;margin-bottom:14px">' +
    '<div style="font-size:15.5px;font-weight:700;line-height:1.35;word-break:break-word">' + h(g.ten) + '</div>' +
    '<div style="display:flex;flex-wrap:wrap;gap:5px;margin:6px 0 10px">' +
    dcnSt(g.dong.length + ' hoá đơn · ' + money(t.de_nghi) + ' đ', 'n') +
    '<button type="button" class="st ' + (no && no.nguon === 'khai' ? 'b' : 'w') + '" data-dcnno="' + h(g.ncc) + '" style="font-size:13px;padding:4px 12px;border:0;min-height:44px;cursor:pointer">' + h(dcnChuNo(no)) + (sua ? ' ✎' : '') + '</button>' +
    (g.nhom ? dcnSt(g.nhom, 'n') : '') + '</div>' +
    '<div class="lst">' + g.dong.map(function (r) { return dcnDong(r, sua, d.ngay_dot); }).join('') + '</div>' +
    '<div style="font-size:13.5px;color:#374151;margin:10px 2px 8px;line-height:1.5">Trả đợt này <b>' + money(t.tra) + ' đ</b> · gia hạn <b>' + money(t.gia_han) + ' đ</b></div>' +
    (sua ? '<div style="display:flex;gap:8px"><button class="btn gr" data-dcnhet="' + i + '" style="margin:0;flex:1">Trả hết</button>' +
      '<button class="btn gh" data-dcnkhong="' + i + '" style="margin:0;flex:1">Không trả đợt này</button></div>' : '') +
    '</div>';
}

/* Ô tìm và chip lọc chỉ ẩn hiện thẻ, số đã sửa giữ nguyên. */
function dcnLoc(b) {
  var q = vgbChuan(DCN.tim || ''), thay = 0, nd = DCN.d ? DCN.d.ngay_dot : '';
  Array.prototype.forEach.call(b.querySelectorAll('[data-dcnnhom]'), function (g) {
    var ncc = g.getAttribute('data-dcnncc') || '', con = 0;
    Array.prototype.forEach.call(g.querySelectorAll('[data-dcndong]'), function (m) {
      var r = (DCN.d.dong || []).filter(function (x) { return x.hoa_don === m.getAttribute('data-dcndong'); })[0];
      var hop = (!q || vgbKhop((m.getAttribute('data-dcnchu') || '') + ' ' + ncc, q)) &&
        (!DCN.loc || !r || (DCN.loc === 'han' ? dcnToiHan(r, nd) : DCN.loc === 'giu' ? r.dang_giu > 0 : DCN.loc === 'tra' ? (Number(dcnSoTra(r)) || 0) > 0 : true));
      m.style.display = hop ? '' : 'none';
      if (hop) con++;
    });
    g.style.display = con ? '' : 'none';
    thay += con;
  });
  var tr = b.querySelector('#dcnTimTrong');
  if (tr) tr.style.display = (q && !thay) ? '' : 'none';
}

function dcnChipLoc(d) {
  var dem = { '': d.dong.length, han: 0, giu: 0, tra: 0 };
  d.dong.forEach(function (r) {
    if (dcnToiHan(r, d.ngay_dot)) dem.han++;
    if (r.dang_giu > 0) dem.giu++;
    if ((Number(dcnSoTra(r)) || 0) > 0) dem.tra++;
  });
  var ds = [['', 'Tất cả'], ['han', '🔴 Tới hạn'], ['tra', '💸 Có trả đợt này'], ['giu', '⏳ APP khác đang giữ']];
  return '<div class="chips" style="flex-wrap:wrap;overflow:visible">' + ds.filter(function (x) { return !x[0] || dem[x[0]]; }).map(function (x) {
    return '<button type="button" class="chip' + (DCN.loc === x[0] ? ' on' : '') + '" data-dcnloc="' + x[0] + '" style="min-height:44px">' + h(x[1]) + ' ' + dem[x[0]] + '</button>';
  }).join('') + '</div>';
}

async function scrDuChi() {
  frame('Dự chi công nợ', '<div class="emp"><div class="e1">⏳</div></div>');
  try { DCN.ds = await api('vagabond.du_chi.ds', {}); }
  catch (e) { return frame('Dự chi công nợ', '<div class="emp"><div class="e1">⚠️</div><div class="e2">' + h(errMsg(e)) + '</div></div>'); }
  var r = DCN.ds;
  var html = '<div class="card" style="padding:12px 14px;font-size:13.5px;line-height:1.55;color:#374151">' +
    'Trả nhà cung cấp hai đợt mỗi tháng, ngày <b>10</b> và <b>20</b>. Máy soạn sẵn đợt ngày 7 và 17 từ dư nợ ERP; Uyên thương lượng, kế toán soát, giám đốc duyệt một lần là máy lập APP.</div>' +
    (!r.da_co ? '<button class="btn" id="dcnSoan" style="margin:0 0 12px">💸 Soạn đợt ' + h(dmy(r.ke_tiep).slice(0, 5)) + ' ngay</button>' : '') +
    (r.dot.length ? '<div class="lst">' + r.dot.map(function (x) {
      var c = x.trang_thai === 'Da chot' ? 'g' : x.trang_thai === 'Huy' ? 'n' : x.trang_thai === 'Nhap' ? 'b' : 'w';
      return '<div class="li" data-dcnxem="' + h(x.name) + '" style="min-height:44px;cursor:pointer"><div class="lt">' +
        '<div class="l1">Đợt ' + h(dmy(x.ngay_dot)) + '</div>' +
        '<div class="l2">Trả ' + money(x.tong_tra) + ' đ · gia hạn ' + money(x.tong_gia_han) + ' đ</div></div>' +
        dcnSt(x.nhan, c) + '</div>';
    }).join('') + '</div>' : '<div class="emp"><div class="e1">💸</div><div class="e2">Chưa có đợt nào. Bấm Soạn đợt để máy dựng từ dư nợ hiện tại.</div></div>');
  var b = frame('Dự chi công nợ', html, { action: '&#8635;', onAction: scrDuChi });
  b.onclick = async function (e) {
    var x = e.target.closest('[data-dcnxem]');
    if (x) { DCN.d = null; DCN.sua = {}; DCN.mo = {}; DCN.ma = x.getAttribute('data-dcnxem'); return go(scrDuChiXem); }
    if (e.target.closest('#dcnSoan')) {
      busy(1);
      try { DCN.d = await api('vagabond.du_chi.soan_lai', { ngay_dot: r.ke_tiep }); DCN.ma = DCN.d.ma; DCN.sua = {}; DCN.mo = {}; }
      catch (er) { toast(errMsg(er), 7000); return; } finally { busy(0); }
      return go(function () { return scrDuChiXem(1); });
    }
  };
}

async function scrDuChiXem(giu) {
  if (!giu || !DCN.d || DCN.d.ma !== DCN.ma) {
    frame('Dự chi công nợ', '<div class="emp"><div class="e1">⏳</div></div>');
    try { DCN.d = await api('vagabond.du_chi.chi_tiet', { ma: DCN.ma }); DCN.sua = dcnGiuSua(DCN.sua, DCN.d); }
    catch (e) { return frame('Dự chi công nợ', '<div class="emp"><div class="e1">⚠️</div><div class="e2">' + h(errMsg(e)) + '</div></div>'); }
  }
  if (dcnKhoiPhuc && dcnKhoiPhuc.ma === DCN.d.ma) { DCN.sua = dcnGiuSua(dcnKhoiPhuc.sua, DCN.d); dcnKhoiPhuc = null; }
  var d = DCN.d, q = d.quyen || {};
  var sua = d.trang_thai === 'Nhap' && q.sua;
  var t = dcnTong(d.dong);
  var du = d.so_du != null ? d.so_du - t.tra : null;
  var nhom = dcnNhom(d.dong);
  var html = dcnTienDo(d.trang_thai) +
    '<div class="card" style="padding:12px 14px">' +
    '<div style="font-size:13px;color:#6b7280">Đợt ' + h(dmy(d.ngay_dot)) + ' · ' + h(d.nhan) + '</div>' +
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px">' +
    [['Trả đợt này', t.tra, '#0B7C93'], ['Gia hạn', t.gia_han, '#374151'], ['Còn đề nghị được', t.de_nghi, '#374151'],
      ['Số dư TK chi', d.so_du, d.so_du == null ? '#6b7280' : (du < 0 ? '#b3261e' : '#178a4c')]].map(function (x) {
        return '<div style="background:#f2f8fa;border-radius:10px;padding:8px 10px"><div style="font-size:13px;color:#6b7280">' + h(x[0]) + '</div>' +
          '<div style="font-size:17px;font-weight:800;color:' + x[2] + '">' + (x[1] == null ? 'Chưa đọc được' : money(x[1]) + ' đ') + '</div></div>';
      }).join('') + '</div>' +
    (du != null ? '<div style="font-size:13px;margin-top:8px;color:' + (du < 0 ? '#b3261e' : '#178a4c') + '">' + (du < 0 ? 'Thiếu ' + money(-du) + ' đ so với số dư lúc soạn.' : 'Còn dư ' + money(du) + ' đ sau đợt này.') + '</div>' : '') +
    (d.ly_do_tra_lai ? '<div style="font-size:13.5px;margin-top:8px;color:#b3261e">Trả lại: ' + h(d.ly_do_tra_lai) + '</div>' : '') +
    ((d.fin_boi || d.gd_boi) ? '<div style="font-size:13px;margin-top:8px;color:#6b7280">' + (d.fin_boi ? 'Kế toán soát: ' + h(d.fin_boi) + ' ' + h(dmy(d.fin_luc)) : '') + (d.gd_boi ? ' · Giám đốc: ' + h(d.gd_boi) + ' ' + h(dmy(d.gd_luc)) : '') + '</div>' : '') +
    '</div>' +
    (d.dong.length ? dcnChipLoc(d) + vgbOTim('dcnTim', d.dong.length, '🔎 Gõ tên nhà cung cấp hoặc số hoá đơn') +
      nhom.map(function (g, i) { return dcnNcc(g, i, d, sua); }).join('')
      : '<div class="emp"><div class="e1">🎉</div><div class="e2">Không còn hoá đơn mua nào cần trả.</div></div>');
  var foot = '';
  if (sua) foot = '<div style="display:flex;gap:8px"><button class="btn gh" id="dcnLuu" style="flex:1;margin:0">💾 Lưu</button>' +
    '<button class="btn" id="dcnGui" style="flex:2;margin:0">📤 Gửi duyệt ' + money(t.tra) + ' đ</button></div>';
  else if (d.trang_thai === 'Cho ke toan' && q.fin) foot = '<div style="display:flex;gap:8px"><button class="btn gh" id="dcnTraLai" style="flex:1;margin:0">Trả lại</button>' +
    '<button class="btn" id="dcnFin" style="flex:2;margin:0">✅ Kế toán đã soát</button></div>';
  else if (d.trang_thai === 'Cho giam doc' && q.gd) foot = '<div style="display:flex;gap:8px"><button class="btn gh" id="dcnTraLai" style="flex:1;margin:0">Trả lại</button>' +
    '<button class="btn" id="dcnGd" style="flex:2;margin:0">✅ Duyệt và lập APP</button></div>';
  else if (d.trang_thai === 'Da duyet' && (q.sua || q.gd)) foot = '<button class="btn" id="dcnChot" style="margin:0">🔁 Lập APP cho phần còn lỗi</button>';
  else if (d.trang_thai === 'Da chot') foot = '<button class="btn gh" id="dcnCk" style="margin:0">🏦 Danh sách chuyển khoản</button>';
  var b = frame('Dự chi ' + dmy(d.ngay_dot).slice(0, 5), html, sua ? { footer: foot, action: '&#8635;', onAction: dcnSoanLai } : (foot ? { footer: foot } : {}));
  var oTim = b.querySelector('#dcnTim');
  if (oTim) { oTim.value = DCN.tim || ''; oTim.oninput = function () { DCN.tim = oTim.value; dcnLoc(b); }; dcnLoc(b); }
  Array.prototype.forEach.call(b.querySelectorAll('[data-dcntra]'), function (o) {
    o.onclick = function (ev) { ev.stopPropagation(); };
    o.oninput = function () {
      var v = String(o.value).replace(/[^0-9]/g, '');
      dcnSua(o.dataset.dcntra, 'so_tra', v === '' ? null : Number(v));
    };
    o.onchange = function () { scrDuChiXem(1); };
  });
  Array.prototype.forEach.call(b.querySelectorAll('[data-dcngc]'), function (o) {
    o.oninput = function () { dcnSua(o.dataset.dcngc, 'ghi_chu', o.value); };
  });
  /* Nút ở thanh dưới nằm ngoài thân màn (frame dựng .vf riêng). */
  var tim = function (k) { return document.getElementById(k); };
  if (tim('dcnLuu')) tim('dcnLuu').onclick = function () { dcnLuu(false); };
  if (tim('dcnGui')) tim('dcnGui').onclick = function () { dcnLuu(true); };
  if (tim('dcnFin')) tim('dcnFin').onclick = function () { dcnDuyet('fin'); };
  if (tim('dcnGd')) tim('dcnGd').onclick = function () { dcnDuyet('gd'); };
  if (tim('dcnTraLai')) tim('dcnTraLai').onclick = function () { dcnDuyet('tra_lai'); };
  if (tim('dcnChot')) tim('dcnChot').onclick = dcnChot;
  if (tim('dcnCk')) tim('dcnCk').onclick = dcnChuyenKhoan;
  b.onclick = async function (e) {
    var lc = e.target.closest('[data-dcnloc]');
    if (lc) { DCN.loc = lc.getAttribute('data-dcnloc') || ''; return scrDuChiXem(1); }
    var het = e.target.closest('[data-dcnhet]'), khong = e.target.closest('[data-dcnkhong]');
    if (het || khong) {
      var g = nhom[+(het || khong).getAttribute(het ? 'data-dcnhet' : 'data-dcnkhong')];
      g.dong.forEach(function (r) { if (!r.app) dcnSua(r.hoa_don, 'so_tra', het ? Math.round(r.co_the_tra) : 0); });
      return scrDuChiXem(1);
    }
    var hen = e.target.closest('[data-dcnhen]');
    if (hen) { dcnSua(hen.getAttribute('data-dcnhen'), 'hen_dot', hen.getAttribute('data-ngay') || ''); return scrDuChiXem(1); }
    var no = e.target.closest('[data-dcnno]');
    if (no && sua) return dcnSoNgayNo(no.getAttribute('data-dcnno'));
    if (e.target.closest('input') || e.target.closest('textarea')) return;
    var m = e.target.closest('[data-dcnmo]');
    if (m) { DCN.mo[m.dataset.dcnmo] = DCN.mo[m.dataset.dcnmo] ? 0 : 1; return scrDuChiXem(1); }
  };
}

async function dcnSoanLai() {
  if (Object.keys(DCN.sua).length && !await confirmSheet('Soạn lại đợt?', 'Máy đọc lại dư nợ ERP. Số đã LƯU được giữ; số vừa gõ mà chưa bấm Lưu sẽ mất.', 'Soạn lại')) return;
  busy(1);
  try { DCN.d = await api('vagabond.du_chi.soan_lai', { ngay_dot: DCN.d.ngay_dot }); DCN.sua = {}; toast('Đã đọc lại dư nợ ERP', 4000); }
  catch (e) { toast(errMsg(e), 7000); } finally { busy(0); }
  scrDuChiXem(1);
}

async function dcnLuu(gui) {
  var d = DCN.d;
  var hong = d.dong.filter(dcnHong);
  if (hong.length) return toast('Còn ' + hong.length + ' hoá đơn có số trả sai (đỏ). Sửa rồi lưu lại.', 6000);
  if (gui) {
    var t = dcnTong(d.dong);
    if (!await confirmSheet('Gửi đợt ' + dmy(d.ngay_dot).slice(0, 5) + ' đi duyệt?',
      'Trả ' + money(t.tra) + ' đ, gia hạn ' + money(t.gia_han) + ' đ cho ' + dcnNhom(d.dong).filter(function (g) { return dcnTong(g.dong).tra > 0; }).length +
      ' nhà cung cấp.\n\nKế toán soát, giám đốc duyệt xong máy lập APP từng nhà cung cấp, sẵn chờ chuyển tiền.', 'Gửi duyệt')) return;
  }
  busy(1);
  try {
    if (Object.keys(DCN.sua).length) DCN.d = await api('vagabond.du_chi.luu', { ma: d.ma, dong: JSON.stringify(dcnDongLuu()) });
    DCN.sua = {};
    if (gui) { DCN.d = await api('vagabond.du_chi.gui', { ma: d.ma }); toast('Đã gửi duyệt', 4000); }
    else toast('Đã lưu', 3000);
  } catch (e) { toast(errMsg(e), 8000); } finally { busy(0); }
  scrDuChiXem(1);
}

async function dcnDuyet(buoc) {
  var d = DCN.d, ly = '';
  if (buoc === 'tra_lai') {
    ly = await hoiChu('Trả lại đợt cho Uyên', 'Ghi lý do để Uyên biết sửa gì.', '', { nhieu_dong: 1, bat_buoc: 1 });
    if (!ly) return;
  } else if (!await confirmSheet(buoc === 'gd' ? 'Duyệt đợt và lập APP?' : 'Kế toán đã soát đợt này?',
    buoc === 'gd' ? 'Máy lập APP cho từng nhà cung cấp đúng số trả, APP sẵn ở bước Đã duyệt chờ chuyển tiền.' : 'Đợt chuyển sang giám đốc duyệt.',
    buoc === 'gd' ? 'Duyệt và lập APP' : 'Đã soát')) return;
  busy(1);
  try {
    DCN.d = await api('vagabond.du_chi.duyet', { ma: d.ma, buoc: buoc, ly_do: ly });
    var loi = (DCN.d.dong || []).filter(function (r) { return r.ket_qua; }).length;
    toast(buoc === 'gd' ? (loi ? 'Đã duyệt. Còn ' + loi + ' hoá đơn chưa lập được APP, xem dòng đỏ rồi bấm Lập APP cho phần còn lỗi.' : 'Đã duyệt và lập đủ APP') : 'Đã ghi', loi ? 9000 : 4000);
  }
  catch (e) { toast(errMsg(e), 8000); } finally { busy(0); }
  scrDuChiXem(1);
}

async function dcnChot() {
  busy(1);
  try {
    var r = await api('vagabond.du_chi.chot', { ma: DCN.d.ma });
    toast(r.loi && r.loi.length ? 'Còn ' + r.loi.length + ' nhà cung cấp chưa lập được APP, xem dòng đỏ.' : 'Đã lập đủ APP', 7000);
  } catch (e) { toast(errMsg(e), 8000); } finally { busy(0); }
  DCN.d = null; scrDuChiXem();
}

async function dcnSoNgayNo(ncc) {
  var x = (DCN.d.so_ngay_no || {})[ncc];
  var v = await hoiChu('Số ngày được nợ', 'Nhà cung cấp cho nợ bao nhiêu ngày kể từ ngày hoá đơn. ' +
    (x && x.goi_y ? 'Lịch sử trả gợi ý ' + x.goi_y + ' ngày. ' : '') + 'Gõ 0 để máy tự dùng số gợi ý.', x && x.nguon === 'khai' ? String(x.so) : (x && x.goi_y ? String(x.goi_y) : ''), { kieu: 'number' });
  if (v == null) return;
  busy(1);
  try { await api('vagabond.du_chi.luu_so_ngay_no', { ncc: ncc, so_ngay: v }); toast('Đã ghi. Bấm ↻ để máy tính lại hạn.', 5000); DCN.d.so_ngay_no[ncc] = { so: +v || 30, nguon: +v ? 'khai' : 'goi_y', goi_y: x && x.goi_y }; }
  catch (e) { toast(errMsg(e), 7000); } finally { busy(0); }
  scrDuChiXem(1);
}

async function dcnChuyenKhoan() {
  var r;
  busy(1);
  try { r = await api('vagabond.du_chi.ds_chuyen_khoan', { ma: DCN.d.ma }); }
  catch (e) { toast(errMsg(e), 7000); return; } finally { busy(0); }
  var html = '<div class="lst">' + (r.dong || []).map(function (x) {
    return '<div class="li" data-dcnapp="' + h(x.name) + '" style="min-height:44px;align-items:flex-start;cursor:pointer"><div class="lt">' +
      '<div class="l1" style="white-space:normal">' + h(x.ten_nhan || x.ten_ncc) + '</div>' +
      '<div class="l2">' + h(x.stk_nhan || 'Chưa có số tài khoản') + ' · ' + h(x.ngan_hang_nhan || '') + '</div>' +
      '<div class="l2">' + h(x.name) + ' · ' + h(x.nhan) + '</div></div>' +
      '<div style="flex:none;font-weight:700">' + money(x.tong_tien) + ' đ</div></div>';
  }).join('') + '</div>';
  var b = frame('Chuyển khoản đợt ' + dmy(DCN.d.ngay_dot).slice(0, 5), html);
  b.onclick = function (e) {
    var a = e.target.closest('[data-dcnapp]');
    if (a) { var ma = a.getAttribute('data-dcnapp'); return go(function () { return scrHoSoTTView(ma); }); }
  };
}

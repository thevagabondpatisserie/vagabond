/* ---------- 71. Dự chi công nợ: trả nhà cung cấp hai đợt 10 và 20 (v653) ----------

   Anh Việt 12/11/2026 (issue #555): thay bảng Excel "Dự chi công nợ" bằng một
   màn trên app. Máy (vagabond/du_chi.py) soạn sẵn đợt nháp ngày 7 và 17 từ dư
   nợ ERP; Thu mua thương lượng từng nhà cung cấp, bấm Trả hết hoặc gõ số trả từng
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

/* THUẦN (v654, Thu mua 13/11): hoá đơn đang được CHỌN trả đợt này = số trả > 0.
   Ô chọn từng dòng và chọn hàng loạt chỉ đặt số trả: chọn là trả hết phần còn
   đề nghị được, bỏ chọn là 0. Một nguồn: số trả, không thêm cờ riêng. */
function dcnDaChon(r) { return (Number(dcnSoTra(r)) || 0) > 0; }

/* THUẦN: dòng có hợp lọc đang chọn (chip) và chữ đang tìm không. */
function dcnHopLoc(r, loc, nd, q, chu) {
  if (q && !vgbKhop(chu || '', q)) return false;
  if (!loc) return true;
  if (loc === 'han') return dcnToiHan(r, nd);
  if (loc === 'qua') return !!r.han && r.han < today();
  if (loc === 'giu') return r.dang_giu > 0;
  if (loc === 'tra') return dcnDaChon(r);
  if (loc === 'chua') return !dcnDaChon(r) && !r.app;
  return true;
}

/* THUẦN: chữ để tìm của một dòng (tên NCC, số hoá đơn, mã). */
function dcnChu(r) { return (r.ten_ncc || '') + ' ' + (r.so_hd || '') + ' ' + r.hoa_don + ' ' + (r.ncc || ''); }

/* THUẦN: các dòng đang hiện theo chip và ô tìm, chọn được (chưa lập APP). */
function dcnDangLoc(d) {
  var q = vgbChuan(DCN.tim || '');
  return (d.dong || []).filter(function (r) { return !r.app && dcnHopLoc(r, DCN.loc, d.ngay_dot, q, dcnChu(r)); });
}

/* THUẦN: số hoá đơn đã chọn và tổng tiền đợt thanh toán. */
function dcnDemChon(dong) {
  var n = 0, t = 0;
  (dong || []).forEach(function (r) { if (dcnDaChon(r)) { n++; t += Number(dcnSoTra(r)) || 0; } });
  return { n: n, tien: t };
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
  var b = [['Nhap', 'Thu mua thương lượng'], ['Cho ke toan', 'Kế toán soát'], ['Cho giam doc', 'Giám đốc duyệt'], ['Da chot', 'Đã lập APP']];
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
    (sua && !r.app ? '<button type="button" data-dcnchon="' + h(r.hoa_don) + '" role="checkbox" aria-checked="' + (dcnDaChon(r) ? 'true' : 'false') + '" ' +
      'aria-label="Chọn trả hoá đơn ' + h(r.so_hd || r.hoa_don) + '" style="flex:none;width:44px;min-height:44px;margin:0 6px 0 -6px;border:0;background:none;font-size:24px;line-height:1;cursor:pointer;color:' +
      (dcnDaChon(r) ? '#0B7C93' : '#98a2b3') + '">' + (dcnDaChon(r) ? '☑' : '☐') + '</button>' : '') +
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
      var hop = r ? dcnHopLoc(r, DCN.loc, nd, q, (m.getAttribute('data-dcnchu') || '') + ' ' + ncc) : true;
      m.style.display = hop ? '' : 'none';
      if (hop) con++;
    });
    g.style.display = con ? '' : 'none';
    thay += con;
  });
  var tr = b.querySelector('#dcnTimTrong');
  if (tr) tr.style.display = (q && !thay) ? '' : 'none';
  /* Số trên hai nút chọn hàng loạt theo đúng lọc đang hiện. */
  var n = DCN.d ? dcnDangLoc(DCN.d).length : 0;
  ['dcnChonHetSo', 'dcnBoHetSo'].forEach(function (k) { var o = b.querySelector('#' + k); if (o) o.innerHTML = n; });
}

/* Thanh chọn hàng loạt (v654): tổng đợt theo hoá đơn đã chọn, chọn hết hay bỏ
   chọn đúng các hoá đơn đang hiện theo chip lọc và ô tìm. */
function dcnThanhChon(d) {
  var c = dcnDemChon(d.dong), n = dcnDangLoc(d).length, tong = (d.dong || []).filter(function (r) { return !r.app; }).length;
  return '<div class="card" style="padding:10px 12px">' +
    '<div style="font-size:14px;color:#374151;line-height:1.5"><span>Đã chọn </span><b id="dcnSoChon">' + c.n + '/' + tong + '</b><span> hoá đơn · tổng đợt thanh toán </span>' +
    '<b id="dcnTongChon" style="color:#0B7C93">' + money(c.tien) + ' đ</b></div>' +
    '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">' +
    '<button type="button" class="btn gh" id="dcnChonHet" style="margin:0;flex:1;min-height:44px;font-size:14px">☑ Chọn hết <b id="dcnChonHetSo">' + n + '</b> đang lọc</button>' +
    '<button type="button" class="btn gh" id="dcnBoHet" style="margin:0;flex:1;min-height:44px;font-size:14px">☐ Bỏ chọn <b id="dcnBoHetSo">' + n + '</b> đang lọc</button></div>' +
    '<div style="font-size:13px;color:#667085;margin-top:6px">Chọn là trả hết phần còn đề nghị được; muốn trả một phần thì gõ số ở ô bên phải.</div></div>';
}

function dcnChipLoc(d) {
  var dem = { '': d.dong.length, han: 0, qua: 0, giu: 0, tra: 0, chua: 0 };
  d.dong.forEach(function (r) {
    ['han', 'qua', 'giu', 'tra', 'chua'].forEach(function (k) { if (dcnHopLoc(r, k, d.ngay_dot, '', '')) dem[k]++; });
  });
  var ds = [['', 'Tất cả'], ['qua', '⏰ Quá hạn'], ['han', '🔴 Tới hạn'], ['tra', '☑ Đã chọn trả'], ['chua', '☐ Chưa chọn'], ['giu', '⏳ APP khác đang giữ']];
  return '<div class="chips" style="flex-wrap:wrap;overflow:visible">' + ds.filter(function (x) { return !x[0] || dem[x[0]]; }).map(function (x) {
    return '<button type="button" class="chip' + (DCN.loc === x[0] ? ' on' : '') + '" data-dcnloc="' + x[0] + '" style="min-height:44px">' + h(x[1]) + ' ' + dem[x[0]] + '</button>';
  }).join('') + '</div>';
}

async function scrDuChi() {
  frame('Dự chi công nợ', '<div class="emp"><div class="e1">⏳</div></div>');
  try {
    var hai = await Promise.all([api('vagabond.du_chi.ds', {}),
      api('vagabond.lich_du_chi.lich', {}).catch(function (e) { return { loi: errMsg(e) }; })]);
    DCN.ds = hai[0]; LDC.l = hai[1];
  }
  catch (e) { return frame('Dự chi công nợ', '<div class="emp"><div class="e1">⚠️</div><div class="e2">' + h(errMsg(e)) + '</div></div>'); }
  var r = DCN.ds;
  var html = ldcKhoi(LDC.l) +
    '<div style="font-size:13px;font-weight:700;color:#475467;margin:14px 2px 6px">ĐỢT TRẢ NHÀ CUNG CẤP 10 VÀ 20</div>' +
    '<div class="card" style="padding:12px 14px;font-size:13.5px;line-height:1.55;color:#374151">' +
    'Trả nhà cung cấp hai đợt mỗi tháng, ngày <b>10</b> và <b>20</b>. Máy soạn sẵn đợt ngày 7 và 17 từ dư nợ ERP; Thu mua thương lượng, kế toán soát, giám đốc duyệt một lần là máy lập APP.</div>' +
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
    if (ldcBam(e)) return;
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
    [['Trả đợt này', t.tra, '#0B7C93'], ['Gia hạn', t.gia_han, '#374151'], ['Còn đề nghị được', t.de_nghi, '#374151']].concat(
      /* anh Việt 13/11: Thu mua không thấy số dư ngân hàng (máy chủ đã bỏ số). */
      d.an_so_du ? [] : [['Số dư ngân hàng', d.so_du, d.so_du == null ? '#6b7280' : (du < 0 ? '#b3261e' : '#178a4c')]]).map(function (x) {
        return '<div style="background:#f2f8fa;border-radius:10px;padding:8px 10px"><div style="font-size:13px;color:#6b7280">' + h(x[0]) + '</div>' +
          '<div style="font-size:17px;font-weight:800;color:' + x[2] + '">' + (x[1] == null ? 'Chưa đọc được' : money(x[1]) + ' đ') + '</div></div>';
      }).join('') + '</div>' +
    (du != null ? '<div style="font-size:13px;margin-top:8px;color:' + (du < 0 ? '#b3261e' : '#178a4c') + '">' + (du < 0 ? 'Thiếu ' + money(-du) + ' đ so với số dư lúc soạn.' : 'Còn dư ' + money(du) + ' đ sau đợt này.') + '</div>' : '') +
    (d.ly_do_tra_lai ? '<div style="font-size:13.5px;margin-top:8px;color:#b3261e">Trả lại: ' + h(d.ly_do_tra_lai) + '</div>' : '') +
    ((d.fin_boi || d.gd_boi) ? '<div style="font-size:13px;margin-top:8px;color:#6b7280">' + (d.fin_boi ? 'Kế toán soát: ' + h(d.fin_boi) + ' ' + h(dmy(d.fin_luc)) : '') + (d.gd_boi ? ' · Giám đốc: ' + h(d.gd_boi) + ' ' + h(dmy(d.gd_luc)) : '') + '</div>' : '') +
    '</div>' +
    (d.dong.length ? dcnChipLoc(d) + vgbOTim('dcnTim', d.dong.length, '🔎 Gõ tên nhà cung cấp hoặc số hoá đơn') + (sua ? dcnThanhChon(d) : '') +
      nhom.map(function (g, i) { return dcnNcc(g, i, d, sua); }).join('')
      : '<div class="emp"><div class="e1">🎉</div><div class="e2">Không còn hoá đơn mua nào cần trả.</div></div>');
  var foot = '';
  if (sua) foot = '<div style="display:flex;gap:8px"><button class="btn gh" id="dcnLuu" style="flex:1;margin:0">💾 Lưu</button>' +
    '<button class="btn" id="dcnGui" style="flex:2;margin:0">📤 Gửi duyệt ' + dcnDemChon(d.dong).n + ' HĐ · ' + money(t.tra) + ' đ</button></div>';
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
    var ch = e.target.closest('[data-dcnchon]');
    if (ch && sua) {
      var rc = d.dong.filter(function (x) { return x.hoa_don === ch.getAttribute('data-dcnchon'); })[0];
      if (rc && !rc.app) dcnSua(rc.hoa_don, 'so_tra', dcnDaChon(rc) ? 0 : Math.round(rc.co_the_tra));
      return scrDuChiXem(1);
    }
    var hl = e.target.closest('#dcnChonHet') ? 1 : e.target.closest('#dcnBoHet') ? 0 : -1;
    if (hl >= 0 && sua) {
      dcnDangLoc(d).forEach(function (r) { dcnSua(r.hoa_don, 'so_tra', hl ? Math.round(r.co_the_tra) : 0); });
      return scrDuChiXem(1);
    }
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
    ly = await hoiChu('Trả lại đợt cho Thu mua', 'Ghi lý do để Thu mua biết sửa gì.', '', { nhieu_dong: 1, bat_buoc: 1 });
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

/* ================= v654 Lịch dự chi (anh Việt 13/11/2026, ảnh đề xuất) =================

   Trên màn chính: Tiền khả dụng (nguồn, giờ đọc), nút ＋ Thêm dự chi, Lịch dự
   chi theo ngày (nhập tay, máy đề xuất theo hạn, theo lịch hằng tháng, đợt,
   hồ sơ APP đang duyệt), dòng cảnh báo ngày thiếu tiền và khoản cần thương
   lượng, Lịch chi hằng tháng. Máy chủ: vagabond/lich_du_chi.py (mỗi khoản đếm
   một lần). Máy chỉ tạo dự chi nháp; duyệt và chi theo hồ sơ APP như cũ.

   Tiền tố ldc = lịch dự chi. */

var LDC = { l: null, form: null, lichForm: null };
/* v654 Codex #561: bản nháp tự lưu (phần 48) của form Sửa dự chi đặt vào đây;
   màn ghép lại SAU khi đọc dự chi từ máy chủ (phần sau 48 không móc sdGhep). */
var ldcKhoiPhuc = null;
var LDC_MAU = { tay: ['#eef4ff', '#3538cd'], may: ['#fef6ee', '#b93815'], lich: ['#f4f3ff', '#5925dc'], dot: ['#ecfdf3', '#067647'], app: ['#f2f4f7', '#344054'] };

/* THUẦN: ngày dd/mm từ yyyy-mm-dd. */
function ldcNgay(s) { return s ? s.slice(8, 10) + '/' + s.slice(5, 7) : ''; }

/* THUẦN: ngày dd/mm của mã đợt DC-26-11-20. */
function ldcNgayDot(ma) { var p = String(ma || '').split('-'); return p.length === 4 ? p[3] + '/' + p[2] : String(ma || ''); }

/* THUẦN: chip nguồn của một khoản. */
function ldcChip(x) {
  var m = LDC_MAU[x.nguon] || LDC_MAU.app;
  return '<span style="display:inline-block;font-size:13px;padding:3px 9px;border-radius:999px;background:' + m[0] + ';color:' + m[1] + ';font-weight:600">' + h(x.nhan_nguon) + '</span>';
}

/* THUẦN: dòng ghi chú rủi ro của một khoản (quá hạn, trễ, đúng hạn ngoài đợt). */
function ldcGhiChu(x) {
  if (x.co === 'qua_han') return '⚠️ Quá hạn ' + ldcNgay(x.han) + ', máy xếp trả hôm nay.';
  if (x.tre) return '⚠️ Trả trễ ' + x.tre + ' ngày so với hạn ' + ldcNgay(x.han) + '.';
  if (x.nguon === 'may' && x.co === 'dung_han' && x.dot) return 'Hạn ' + ldcNgay(x.han) + ': máy đề xuất trả đúng hạn. Dời sang đợt ' + h(ldcNgayDot(x.dot)) + ' là trễ, cần nhà cung cấp đồng ý.';
  if (x.nguon === 'may' && x.co === 'dung_han' && x.han) return 'Hạn ' + ldcNgay(x.han) + ': trả đúng hạn.';
  if (x.nguon === 'may' && x.co === 'dot' && x.han) return 'Hạn ' + ldcNgay(x.han) + ', xếp vào đợt không sau hạn.';
  if (x.nguon === 'may' && x.co === 'hen') return 'Đã hẹn trả đợt này khi thương lượng.';
  if (x.qua_ngay) return '⚠️ Đã qua ngày cần chi, chưa thấy hồ sơ thanh toán.';
  if (x.nguon === 'tay' && x.da_tinh_noi_khac > 0) return 'Đã tính ' + money(x.da_tinh_noi_khac) + ' đ của khoản này trong đợt dự chi hoặc hồ sơ thanh toán của hoá đơn đã gắn, không đếm hai lần.';
  return '';
}

/* THUẦN: đầu khối Lịch dự chi. Người không được xem mục Tài chính (Thu mua)
   không thấy số dư, chỉ thấy máy đang dùng số đó để báo ngày không đủ tiền
   (anh Việt 13/11). Tiền dự kiến về lấy từ công nợ cần thu. */
function ldcDauTien(sd, dv) {
  if (sd.an) {
    return '<div style="font-size:13px;color:#6b7280">Tiền khả dụng</div>' +
      (sd.chua_ro ? '<div style="font-size:14px;color:#b45309;line-height:1.5;font-weight:600">Máy chưa xác định được số dư ngân hàng nên chưa báo được ngày nào không đủ tiền. Nhờ Kế toán kiểm mục Tài chính.</div>'
        : '<div style="font-size:14px;color:#475467;line-height:1.5">Chỉ Giám đốc và người được xem mục Tài chính thấy số này. Máy vẫn dùng số dư ngân hàng và tiền dự kiến về để báo ngày không đủ tiền chi.</div>');
  }
  return '<div style="font-size:13px;color:#6b7280">Tiền khả dụng</div>' +
    (sd.so_tien == null ? '<div style="font-size:16px;font-weight:800;color:#b45309">Chưa xác định được khả năng chi</div>'
      : '<div style="font-size:24px;font-weight:800;color:#0B7C93">' + money(sd.so_tien) + ' đ</div>') +
    '<div style="font-size:13px;color:#6b7280;line-height:1.45">' + h(sd.nguon || '') + (sd.luc ? ', đọc lúc ' + h(sd.luc.slice(11, 16)) + ' ' + h(ldcNgay(sd.luc.slice(0, 10))) : '') +
    (sd.chi_sau ? '. Đã trừ ' + money(sd.chi_sau) + ' đ vừa chi sau lúc đọc.' : '.') + '</div>' +
    '<div style="font-size:13px;color:#6b7280;margin-top:4px;line-height:1.45">' +
    (dv.loi ? 'Tiền dự kiến về: ' + h(dv.loi) + '.'
      : 'Tiền dự kiến về (công nợ cần thu): ' + money(dv.trong_khung || 0) + ' đ trong khung, cộng vào đúng ngày khách thường trả' +
        (dv.qua_han ? '. Khách quá hạn chưa trả ' + money(dv.qua_han) + ' đ, không tính vào ngày nào' : '') + '.') + '</div>';
}

/* Khối Lịch dự chi trên màn chính. */
function ldcKhoi(l) {
  if (!l) return '';
  if (l.loi) return '<div class="card" style="padding:12px 14px;font-size:13.5px;color:#b3261e">Chưa đọc được Lịch dự chi: ' + h(l.loi) + '</div>';
  var sd = l.so_du || {}, q = l.quyen || {};
  var html = '<div class="card" style="padding:12px 14px">' +
    '<div style="display:flex;align-items:flex-start;gap:10px">' +
    '<div style="flex:1;min-width:0">' + ldcDauTien(sd, l.du_kien_ve || {}) + '</div>' +
    (q.sua ? '<button class="btn" id="ldcThem" style="flex:none;margin:0;min-height:44px;padding:0 14px;font-size:14px;width:auto">＋ Thêm dự chi</button>' : '') +
    '</div></div>';
  if (l.thieu_dau) {
    html += '<div class="card" style="padding:12px 14px;background:#fef3f2;border:1px solid #fecdca">' +
      '<div style="font-size:15px;font-weight:800;color:#b42318">⚠️ Ngày ' + h(ldcNgay(l.thieu_dau.ngay)) +
      (l.thieu_dau.so_tien == null ? ' không đủ tiền chi' : ' còn thiếu ' + money(l.thieu_dau.so_tien) + ' đ') + '</div>' +
      ((l.can_thuong_luong || []).length ? '<div style="font-size:13px;color:#7a271a;margin-top:4px;line-height:1.5">Khoản có thể thương lượng dời: ' +
        l.can_thuong_luong.slice(0, 3).map(function (x) { return h(x.nguoi_nhan || x.noi_dung) + ' ' + money(x.so_tien) + ' đ (' + ldcNgay(x.ngay) + ')'; }).join('; ') + '.</div>' : '') +
      '</div>';
  }
  html += '<div style="font-size:13px;font-weight:700;color:#475467;margin:14px 2px 6px">LỊCH DỰ CHI ' + h(ldcNgay(l.hom_nay)) + ' TỚI ' + h(ldcNgay(l.den)) + '</div>';
  if (!(l.ngay || []).length) html += '<div class="card"><div class="emp" style="padding:20px"><div class="e1">🗓️</div><div class="e2">Chưa có khoản chi nào trong khung này.</div></div></div>';
  (l.ngay || []).forEach(function (g) {
    html += '<div class="card" style="padding:0;overflow:hidden">' +
      '<div style="display:flex;justify-content:space-between;gap:8px;padding:10px 14px;background:#f8fafc;border-bottom:1px solid #eaecf0;font-size:13px">' +
      '<b style="font-size:14px">' + h(ldcNgay(g.ngay)) + '</b><span style="color:#475467">chi ' + money(g.tong) + ' đ' +
      (g.ve ? ' · về ' + money(g.ve) + ' đ' : '') +
      (g.con_lai == null ? (g.khong_du ? ' · <b style="color:#b42318">không đủ tiền</b>' : '')
        : ' · <b style="color:' + (g.con_lai < 0 ? '#b42318' : '#067647') + '">' + (g.con_lai < 0 ? 'thiếu ' + money(-g.con_lai) : 'còn ' + money(g.con_lai)) + ' đ</b>') + '</span></div>' +
      g.muc.map(function (x) {
        var gc = ldcGhiChu(x), mo = x.nguon === 'tay' || x.nguon === 'app' || x.nguon === 'lich';
        return '<div ' + (mo ? 'data-ldcmo="' + h(x.nguon + '|' + x.ma) + '" ' : '') + 'style="display:flex;gap:10px;align-items:flex-start;padding:10px 14px;border-bottom:1px solid #f2f4f7;min-height:44px' + (mo ? ';cursor:pointer' : '') + '">' +
          '<div style="flex:1;min-width:0"><div style="font-size:14px;font-weight:600;white-space:normal">' + h(x.noi_dung) + '</div>' +
          (x.nguoi_nhan && x.nguoi_nhan !== x.noi_dung ? '<div style="font-size:13px;color:#6b7280">' + h(x.nguoi_nhan) + '</div>' : '') +
          '<div style="margin-top:4px">' + ldcChip(x) + '</div>' +
          (gc ? '<div style="font-size:13px;color:' + (gc.charAt(0) === '⚠' ? '#b42318' : '#475467') + ';margin-top:4px;line-height:1.45">' + gc + '</div>' : '') + '</div>' +
          '<div style="flex:none;font-weight:800;font-size:14px">' + money(x.so_tien) + ' đ</div></div>';
      }).join('') + '</div>';
  });
  html += '<div style="font-size:13px;font-weight:700;color:#475467;margin:14px 2px 6px">LỊCH CHI HẰNG THÁNG</div><div class="card" style="padding:0;overflow:hidden">' +
    ((l.lich_chi || []).length ? l.lich_chi.map(function (c) {
      var tat = c.bat === 0;
      return '<div data-ldclich="' + h(c.name) + '" style="display:flex;gap:10px;align-items:center;padding:10px 14px;border-bottom:1px solid #f2f4f7;min-height:44px;cursor:pointer' + (tat ? ';background:#f9fafb' : '') + '">' +
        '<div style="flex:1;min-width:0"><div style="font-size:14px;font-weight:600' + (tat ? ';color:#667085' : '') + '">' + h(c.noi_dung) + '</div>' +
        '<div style="font-size:13px;color:#6b7280">' + h(c.nguoi_nhan || '') + ' · ngày ' + c.ngay_trong_thang + ' hằng tháng' +
        (c.so_thang_thay ? ' · máy thấy ' + c.so_thang_thay + ' tháng' : '') + '</div>' +
        (tat ? '<div style="font-size:13px;color:#b45309;margin-top:2px">⏸ Đang tạm thôi tính, bấm để mở và dùng lại</div>' : '') + '</div>' +
        '<div style="flex:none;font-weight:700' + (tat ? ';color:#98a2b3' : '') + '">' + money(c.so_tien) + ' đ</div></div>';
    }).join('') : '<div style="padding:12px 14px;font-size:13.5px;color:#6b7280">Chưa có lịch chi hằng tháng nào.</div>') +
    '<div style="display:flex;gap:8px;flex-wrap:wrap;padding:10px 14px">' +
    (q.sua ? '<button class="btn gh" id="ldcThemLich" style="margin:0;min-height:44px;flex:1;font-size:14px">＋ Thêm lịch hằng tháng</button>' : '') +
    '<button class="btn gh" id="ldcGoiY" style="margin:0;min-height:44px;flex:1;font-size:14px">Máy gợi ý từ dữ liệu</button></div></div>';
  return html;
}

/* Bấm trong khối Lịch dự chi. Trả true khi đã xử lý. */
function ldcBam(e) {
  if (e.target.closest('#ldcThem')) { LDC.form = { ngay: '', noi_dung: '', so_tien: '', nguoi_nhan: '', ly_do: '', hoa_don: '', nha_cung_cap: '', ten_ncc: '' }; go(scrDuChiThem); return true; }
  if (e.target.closest('#ldcThemLich')) { LDC.lichForm = { noi_dung: '', nguoi_nhan: '', so_tien: '', ngay_trong_thang: 20, bat: 1, nha_cung_cap: '', ten_ncc: '' }; go(scrLichChi); return true; }
  if (e.target.closest('#ldcGoiY')) { go(scrLichGoiY); return true; }
  var c = e.target.closest('[data-ldclich]');
  if (c) {
    var x = ((LDC.l && LDC.l.lich_chi) || []).filter(function (y) { return y.name === c.getAttribute('data-ldclich'); })[0];
    if (x) { LDC.lichForm = ldcLichMo(x); go(scrLichChi); }
    return true;
  }
  var m = e.target.closest('[data-ldcmo]');
  if (m) {
    var p = m.getAttribute('data-ldcmo').split('|');
    if (p[0] === 'app') { var ma = p[1]; go(function () { return scrHoSoTTView(ma); }); return true; }
    if (p[0] === 'lich') {
      var y = ((LDC.l && LDC.l.lich_chi) || []).filter(function (z) { return z.name === p[1]; })[0];
      if (y) { LDC.lichForm = ldcLichMo(y); go(scrLichChi); }
      return true;
    }
    LDC.form = null;
    go(function () { return scrDuChiThem(p[1]); });
    return true;
  }
  return false;
}

function ldcO(nhan, giai, o) {
  return '<div style="margin:0 0 12px"><div style="font-size:14px;font-weight:700;color:#344054">' + nhan + '</div>' +
    (giai ? '<div style="font-size:13px;color:#667085;margin:2px 0 6px;line-height:1.45">' + giai + '</div>' : '<div style="height:6px"></div>') + o + '</div>';
}
var LDC_O = 'width:100%;box-sizing:border-box;min-height:44px;font-size:15px;padding:8px 12px;border:1px solid #d0d5dd;border-radius:10px;background:#fff';

/* THUẦN: form sửa một lịch hằng tháng mở từ danh sách. Giữ đúng cờ đang dùng
   (lịch tạm thôi mở ra vẫn là tạm thôi, bấm nút mới dùng lại). */
function ldcLichMo(x) {
  return Object.assign({}, x, { bat: x.bat === 0 ? 0 : 1, ten_ncc: x.nha_cung_cap ? (x.nguoi_nhan || x.nha_cung_cap) : '' });
}

/* THUẦN: ô chọn nhà cung cấp (AGENTS QT-31: chọn từ danh mục, không gõ tự do). */
function ldcONcc(id, f) {
  return '<button type="button" class="btn gh" id="' + id + '" style="margin:0;min-height:44px;font-size:14px;text-align:left;width:100%">' +
    (f.nha_cung_cap ? '🏭 ' + h(f.ten_ncc || f.nha_cung_cap) + ' <span style="color:#667085">· bấm để đổi</span>' : '🔎 Chọn nhà cung cấp trong danh mục') + '</button>';
}

/* Mở ô chọn nhà cung cấp: gõ một phần tên, mã hay MST, chọn trong danh mục.
   Trả {ncc, ten}, {ncc: ''} khi bỏ chọn, null khi đóng. */
async function ldcChonNcc(f) {
  var tu = await hoiChu('Chọn nhà cung cấp', 'Gõ một phần tên, mã hoặc mã số thuế:', '', { bat_buoc: true });
  if (!tu) return null;
  var ds;
  busy(1);
  try { ds = await api('vagabond.lich_du_chi.chon_ncc', { tu_khoa: tu }); }
  catch (e) { toast(errMsg(e), 6000); return null; } finally { busy(0); }
  var lua = (ds || []).map(function (x) { return { k: x.name, icon: '🏭', nhan: x.ten, mo_ta: (x.mst ? 'MST ' + x.mst + ' · ' : '') + 'mã ' + x.name }; });
  if (f && f.nha_cung_cap) lua.push({ k: '__bo', icon: '✖', nhan: 'Bỏ chọn nhà cung cấp', mo_ta: 'Khoản này trả cho người nhận khác, không phải nhà cung cấp' });
  if (!lua.length) { baoTin('Không có nhà cung cấp nào khớp "' + tu + '". Bên nhận chưa có trong danh mục thì ghi ở ô Người nhận khác.', 'Chọn nhà cung cấp'); return null; }
  var c = await hoiChon('Chọn nhà cung cấp', (ds || []).length + ' nhà khớp', lua);
  if (!c) return null;
  if (c === '__bo') return { ncc: '', ten: '' };
  var x = (ds || []).filter(function (y) { return y.name === c; })[0];
  return { ncc: c, ten: (x && x.ten) || c };
}

/* Form Thêm dự chi (ảnh đề xuất): ngày bất kỳ, nội dung, số tiền, người nhận, lý do, hoá đơn nếu có. */
async function scrDuChiThem(name) {
  if (name) {
    frame('Sửa dự chi', '<div class="emp"><div class="e1">⏳</div></div>');
    if (!(LDC.form && LDC.form.name === name && LDC.form.__dang_sua)) {
      try { LDC.form = await api('vagabond.lich_du_chi.chi_tiet_muc', { name: name }); }
      catch (e) { return frame('Sửa dự chi', '<div class="emp"><div class="e1">⚠️</div><div class="e2">' + h(errMsg(e)) + '</div></div>'); }
      LDC.form.__dang_sua = 1;
    }
    /* Bản nháp tự lưu của đúng dự chi này: ghép sau khi đọc máy chủ. */
    if (ldcKhoiPhuc && ldcKhoiPhuc.name === name) { LDC.form = Object.assign({}, LDC.form, ldcKhoiPhuc, { __dang_sua: 1 }); }
    ldcKhoiPhuc = null;
  }
  var f = LDC.form || {};
  var nhap = !f.trang_thai || f.trang_thai === 'Nhap';
  var html = '<div class="card" style="padding:14px">' +
    ldcO('Ngày cần chi', 'Chọn ngày bất kỳ, kể cả ngoài hai đợt 10 và 20.', '<input type="date" id="ldcNgay" value="' + h(f.ngay || '') + '" style="' + LDC_O + '">') +
    ldcO('Nội dung', '', '<input id="ldcND" value="' + h(f.noi_dung || '') + '" placeholder="Ví dụ: Chi gấp mua bơ" style="' + LDC_O + '">') +
    ldcO('Số tiền', '', '<input id="ldcTien" inputmode="numeric" value="' + h(f.so_tien ? money(f.so_tien) : '') + '" placeholder="10.000.000" style="' + LDC_O + '">') +
    ldcO('Nhà cung cấp', 'Chọn trong danh mục để máy nối đúng hoá đơn, hồ sơ thanh toán của nhà đó.', ldcONcc('ldcNcc', f)) +
    (f.nha_cung_cap ? '' : ldcO('Người nhận khác', 'Chỉ ghi khi bên nhận không có trong danh mục nhà cung cấp, ví dụ chi gấp ở chợ.',
      '<input id="ldcNhan" value="' + h(f.nguoi_nhan || '') + '" style="' + LDC_O + '">')) +
    ldcO('Lý do', '', '<textarea id="ldcLyDo" rows="3" style="' + LDC_O + '">' + h(f.ly_do || '') + '</textarea>') +
    ldcO('Hoá đơn công nợ (nếu có)', 'Có hoá đơn thì máy trừ phần này khỏi số đề xuất của hoá đơn đó, không đếm hai lần. Không có hoá đơn vẫn lưu được.',
      (f.hoa_don ? '<div style="display:flex;gap:8px;align-items:center;margin-bottom:8px"><div id="ldcHDDa" style="flex:1;min-width:0;font-size:14px;font-weight:600">🧾 ' + h(f.hoa_don) + '</div>' +
        '<button class="btn gh" id="ldcBoHD" style="margin:0;min-height:44px;width:auto;padding:0 14px;font-size:14px">Bỏ hoá đơn</button></div>' : '') +
      '<div style="display:flex;gap:8px"><input id="ldcHDTim" placeholder="Gõ tên nhà cung cấp, số hoặc mã hoá đơn" style="' + LDC_O + ';flex:1">' +
      '<button class="btn gh" id="ldcTimHD" style="margin:0;min-height:44px;width:auto;padding:0 14px;font-size:14px">Tìm</button></div><div id="ldcHDKq"></div>') +
    (f.ho_so_app ? '<div style="font-size:13.5px;color:#067647">Đã nối hồ sơ thanh toán ' + h(f.ho_so_app) + '. Lịch đếm theo hồ sơ này.</div>' : '') +
    '<div style="font-size:13px;color:#667085;line-height:1.5;margin-top:4px">Máy chỉ lưu dự chi nháp để tính tiền theo ngày. Chi thật vẫn lập hồ sơ thanh toán (APP) và duyệt như cũ, rồi nối hồ sơ vào đây.</div>' +
    '</div>';
  if (name && nhap) html += '<div class="card" style="padding:14px">' +
    ldcO('Nối hồ sơ thanh toán đã lập', 'Chọn hồ sơ thanh toán (APP) của khoản này. Từ lúc nối, lịch đếm theo hồ sơ đó.',
      '<button class="btn gh" id="ldcNoi" style="margin:0;min-height:44px;font-size:14px;text-align:left;width:100%">🔎 Chọn hồ sơ thanh toán để nối</button>') +
    '<button class="btn gh" id="ldcXoa" style="margin:4px 0 0;min-height:44px;color:#b42318">🗑 Xoá dự chi nháp</button></div>';
  var foot = nhap ? '<button class="btn" id="ldcLuu" style="margin:0;min-height:48px">💾 Lưu dự chi nháp</button>' : '';
  var b = frame(name ? 'Sửa dự chi' : 'Thêm dự chi', html, foot ? { footer: foot } : {});
  var v = function (k) { var o = document.getElementById(k); return o ? o.value : ''; };
  /* Chép ô đang gõ vào LDC.form trước khi vẽ lại (chọn nhà cung cấp, chọn hoá đơn). */
  var docO = function () {
    f.ngay = v('ldcNgay'); f.noi_dung = v('ldcND'); f.so_tien = String(v('ldcTien')).replace(/[^0-9]/g, '');
    if (!f.nha_cung_cap) f.nguoi_nhan = v('ldcNhan');
    f.ly_do = v('ldcLyDo');
  };
  var luu = document.getElementById('ldcLuu');
  if (luu) luu.onclick = async function () {
    busy(1);
    try {
      await api('vagabond.lich_du_chi.luu_muc', { name: name || '', ngay: v('ldcNgay'), noi_dung: v('ldcND'),
        so_tien: String(v('ldcTien')).replace(/[^0-9]/g, ''), nguoi_nhan: f.nha_cung_cap ? (f.ten_ncc || '') : v('ldcNhan'),
        nha_cung_cap: f.nha_cung_cap || '', ly_do: v('ldcLyDo'), hoa_don: f.hoa_don || '' });
      toast('Đã lưu dự chi nháp', 3500);
    } catch (e) { toast(errMsg(e), 7000); return; } finally { busy(0); }
    back();
  };
  b.onclick = async function (e) {
    if (e.target.closest('#ldcNcc')) {
      docO();
      var c = await ldcChonNcc(f);
      if (!c) return;
      f.nha_cung_cap = c.ncc; f.ten_ncc = c.ten; if (c.ncc) f.nguoi_nhan = c.ten;
      LDC.form = f;
      return go(function () { return scrDuChiThem(name); }, true);
    }
    if (e.target.closest('#ldcTimHD')) {
      var kq;
      try { kq = await api('vagabond.lich_du_chi.chon_hoa_don', { tu_khoa: v('ldcHDTim') }); } catch (er) { toast(errMsg(er), 6000); return; }
      document.getElementById('ldcHDKq').innerHTML = (kq || []).length ? kq.map(function (x) {
        return '<div data-ldchd="' + h(x.name) + '" data-ldchdncc="' + h(x.ncc || '') + '" data-ldchdten="' + h(x.ten || '') + '" style="padding:10px 4px;border-bottom:1px solid #f2f4f7;min-height:44px;cursor:pointer;font-size:13.5px"><b>' + h(x.name) + '</b> · ' + h(x.ten) +
          (x.so ? ' · số ' + h(x.so) : '') + ' · còn ' + money(x.con_no) + ' đ</div>';
      }).join('') : '<div style="font-size:13px;color:#667085;padding:8px 0">Không có hoá đơn còn nợ nào khớp.</div>';
      return;
    }
    var hd = e.target.closest('[data-ldchd]');
    if (hd) {
      docO();
      f.hoa_don = hd.getAttribute('data-ldchd');
      /* Hoá đơn của nhà nào thì khoản này trả cho đúng nhà đó. */
      if (hd.getAttribute('data-ldchdncc')) { f.nha_cung_cap = hd.getAttribute('data-ldchdncc'); f.ten_ncc = hd.getAttribute('data-ldchdten') || f.nha_cung_cap; f.nguoi_nhan = f.ten_ncc; }
      LDC.form = f;
      return go(function () { return scrDuChiThem(name); }, true);
    }
    if (e.target.closest('#ldcBoHD')) {
      docO(); f.hoa_don = ''; LDC.form = f;
      return go(function () { return scrDuChiThem(name); }, true);
    }
    if (e.target.closest('#ldcNoi')) {
      var tu = await hoiChu('Chọn hồ sơ thanh toán', 'Gõ mã APP, tên người nhận hoặc nhà cung cấp:', f.ten_ncc || f.nguoi_nhan || '', { bat_buoc: true });
      if (!tu) return;
      var ds;
      busy(1);
      try { ds = await api('vagabond.lich_du_chi.chon_app', { tu_khoa: tu }); } catch (er) { toast(errMsg(er), 6000); return; } finally { busy(0); }
      if (!(ds || []).length) return baoTin('Không có hồ sơ thanh toán nào khớp "' + tu + '".', 'Chọn hồ sơ thanh toán');
      var c = await hoiChon('Chọn hồ sơ thanh toán', ds.length + ' hồ sơ khớp', ds.map(function (x) {
        return { k: x.name, icon: '📄', nhan: x.name + ' · ' + money(x.so_tien) + ' đ', mo_ta: (x.ten ? x.ten + ' · ' : '') + x.trang_thai + (x.ngay ? ' · lập ' + ldcNgay(x.ngay) : '') };
      }));
      if (!c) return;
      busy(1);
      try { await api('vagabond.lich_du_chi.noi_app', { name: name, ho_so_app: c }); toast('Đã nối hồ sơ ' + c, 3500); }
      catch (er) { toast(errMsg(er), 7000); return; } finally { busy(0); }
      return back();
    }
    if (e.target.closest('#ldcXoa')) {
      if (!await confirmSheet('Xoá dự chi nháp này?', 'Khoản này bị xoá hẳn, không còn trên Lịch dự chi.', 'Xoá dự chi', true)) return;
      busy(1);
      try { await api('vagabond.lich_du_chi.xoa_muc', { name: name }); toast('Đã xoá dự chi nháp', 3000); }
      catch (er) { toast(errMsg(er), 7000); return; } finally { busy(0); }
      return back();
    }
  };
}

/* THUẦN: chữ của nút Đang dùng / Tạm thôi. */
function ldcChuBat(bat) { return bat === 0 ? '⏸ Đang tạm thôi tính (bấm để dùng lại)' : '✅ Đang dùng (bấm để tạm thôi)'; }

/* Form Lịch chi hằng tháng: tiền nhà, điện, nước... ngày cố định trong tháng. */
function scrLichChi() {
  var f = LDC.lichForm || {};
  var html = '<div class="card" style="padding:14px">' +
    ldcO('Nội dung', '', '<input id="lcND" value="' + h(f.noi_dung || '') + '" placeholder="Ví dụ: Tiền nhà" style="' + LDC_O + '">') +
    ldcO('Nhà cung cấp', 'Chọn trong danh mục để máy biết tháng nào đã có hoá đơn, hồ sơ thanh toán của nhà đó.', ldcONcc('lcNcc', f)) +
    (f.nha_cung_cap ? '' : ldcO('Người nhận khác', 'Chỉ ghi khi bên nhận không có trong danh mục nhà cung cấp.',
      '<input id="lcNhan" value="' + h(f.nguoi_nhan || '') + '" style="' + LDC_O + '">')) +
    ldcO('Số tiền mỗi tháng', '', '<input id="lcTien" inputmode="numeric" value="' + h(f.so_tien ? money(f.so_tien) : '') + '" style="' + LDC_O + '">') +
    ldcO('Ngày chi trong tháng', 'Tháng ngắn hơn thì máy lùi về ngày cuối tháng. Tháng đã có hồ sơ thanh toán hay hoá đơn mua của đúng người nhận thì máy không tính thêm.',
      '<input id="lcNgay" type="number" min="1" max="31" value="' + h(String(f.ngay_trong_thang || 20)) + '" style="' + LDC_O + '">') +
    '<button type="button" class="btn gh" id="lcBat" style="margin:0;min-height:44px;font-size:14px;text-align:left">' + ldcChuBat(f.bat) + '</button>' +
    '<div style="font-size:13px;color:#667085;margin-top:4px">Tạm thôi thì máy không tính lịch này trên Lịch dự chi, dữ liệu vẫn giữ.</div>' +
    (f.ngoai_le ? '<div style="font-size:13px;color:#b45309;margin-top:6px;white-space:pre-line">' + h(f.ngoai_le) + '</div>' : '') +
    '</div>';
  frame(f.name ? 'Sửa lịch hằng tháng' : 'Thêm lịch hằng tháng', html, { footer: '<button class="btn" id="lcLuu" style="margin:0;min-height:48px">💾 Lưu lịch</button>' });
  var v = function (k) { var o = document.getElementById(k); return o ? o.value : ''; };
  document.getElementById('lcNcc').onclick = async function () {
    f.noi_dung = v('lcND'); f.so_tien = String(v('lcTien')).replace(/[^0-9]/g, ''); f.ngay_trong_thang = v('lcNgay');
    if (!f.nha_cung_cap) f.nguoi_nhan = v('lcNhan');
    var c = await ldcChonNcc(f);
    if (!c) return;
    f.nha_cung_cap = c.ncc; f.ten_ncc = c.ten; if (c.ncc) f.nguoi_nhan = c.ten;
    LDC.lichForm = f;
    go(scrLichChi, true);
  };
  document.getElementById('lcBat').onclick = function () {
    f.bat = f.bat === 0 ? 1 : 0;
    document.getElementById('lcBat').innerHTML = ldcChuBat(f.bat);
  };
  document.getElementById('lcLuu').onclick = async function () {
    busy(1);
    try {
      await api('vagabond.lich_du_chi.luu_lich', { name: f.name || '', noi_dung: v('lcND'), nguoi_nhan: f.nha_cung_cap ? (f.ten_ncc || '') : v('lcNhan'),
        nha_cung_cap: f.nha_cung_cap || '',
        so_tien: String(v('lcTien')).replace(/[^0-9]/g, ''), ngay_trong_thang: v('lcNgay'), bat: f.bat === 0 ? 0 : 1,
        ngoai_le: f.name ? null : (f.ngoai_le || null), so_thang_thay: f.so_thang_thay || null });
      toast('Đã lưu lịch', 3500);
    } catch (e) { toast(errMsg(e), 7000); return; } finally { busy(0); }
    back();
  };
}

/* Gợi ý lịch hằng tháng máy học từ mọi tháng đọc được (APP đã trả, Payment Entry). */
async function scrLichGoiY() {
  frame('Máy gợi ý lịch chi', '<div class="emp"><div class="e1">⏳</div></div>');
  var r;
  try { r = await api('vagabond.lich_du_chi.goi_y_lich', {}); }
  catch (e) { return frame('Máy gợi ý lịch chi', '<div class="emp"><div class="e1">⚠️</div><div class="e2">' + h(errMsg(e)) + '</div></div>'); }
  var th = r.thang_doc_duoc || [];
  var html = '<div class="card" style="padding:12px 14px;font-size:13.5px;line-height:1.55;color:#374151">Máy đọc ' + th.length + ' tháng có dữ liệu' +
    (th.length ? ' (' + h(th[0].slice(5) + '/' + th[0].slice(0, 4)) + ' tới ' + h(th[th.length - 1].slice(5) + '/' + th[th.length - 1].slice(0, 4)) + ')' : '') +
    '. Chỉ gợi ý người nhận thấy từ ba tháng trở lên; hoàn ứng không tính. Hợp đồng hay hạn trên hoá đơn luôn đi trước gợi ý này.</div>';
  html += (r.goi_y || []).length ? (r.goi_y || []).map(function (x, i) {
    return '<div class="card" style="padding:12px 14px"><div style="display:flex;gap:10px;align-items:flex-start"><div style="flex:1;min-width:0">' +
      '<div style="font-size:14px;font-weight:700;white-space:normal">' + h(x.ten) + '</div>' +
      '<div style="font-size:13px;color:#475467">Thấy ' + x.so_thang + ' tháng: ' + x.thang.map(function (t) { return h(t.slice(5) + '/' + t.slice(2, 4)); }).join(', ') +
      ' · thường ngày ' + x.ngay_goi_y + ' · khoảng ' + money(x.so_tien_goi_y) + ' đ</div>' +
      (x.ngoai_le.length ? '<div style="font-size:13px;color:#b45309;margin-top:4px;line-height:1.45">' + x.ngoai_le.map(h).join('<br>') + '</div>' : '') + '</div>' +
      (x.da_tat ? '<button class="btn gh" data-lcmo="' + h(x.lich) + '" style="flex:none;margin:0;min-height:44px;width:auto;padding:0 12px;font-size:14px">Đang tạm thôi, mở lại</button>'
        : x.da_co ? '<span style="flex:none;font-size:13px;color:#067647">Đã có lịch</span>'
        : '<button class="btn gh" data-lcgy="' + i + '" style="flex:none;margin:0;min-height:44px;width:auto;padding:0 12px;font-size:14px">Thêm vào lịch</button>') +
      '</div></div>';
  }).join('') : '<div class="card"><div class="emp" style="padding:20px"><div class="e1">🗓️</div><div class="e2">Chưa thấy khoản nào lặp đủ ba tháng.</div></div></div>';
  var b = frame('Máy gợi ý lịch chi', html);
  b.onclick = function (e) {
    var mo = e.target.closest('[data-lcmo]');
    if (mo) {
      var y = ((LDC.l && LDC.l.lich_chi) || []).filter(function (z) { return z.name === mo.getAttribute('data-lcmo'); })[0];
      if (y) { LDC.lichForm = ldcLichMo(y); go(scrLichChi); }
      return;
    }
    var t = e.target.closest('[data-lcgy]');
    if (!t) return;
    var x = r.goi_y[+t.getAttribute('data-lcgy')];
    LDC.lichForm = { noi_dung: x.ten, nguoi_nhan: x.ten, so_tien: x.so_tien_goi_y, ngay_trong_thang: x.ngay_goi_y, bat: 1,
      nha_cung_cap: x.ncc || '', ten_ncc: x.ncc ? x.ten : '',
      ngoai_le: x.ngoai_le.join('\n'), so_thang_thay: x.so_thang };
    go(scrLichChi);
  };
}

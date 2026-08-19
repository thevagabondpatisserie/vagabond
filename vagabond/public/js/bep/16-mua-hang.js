/* ---------------- Don mua hang (PO) ---------------- */
async function scrDonMua() {
  frame('Đơn mua hàng', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc đơn mua hàng...</div></div>');
  var kq;
  try { kq = await api('vagabond.mua_hang.ds_po', { so_ngay: poNgay, tu_khoa: poTim, nhom: poNhom }); }
  catch (e) {
    frame('Đơn mua hàng', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  /* Loc theo chip lam o MAY CHU roi, o day chi ve ra. */
  var ds = kq.don || [];

  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">ĐƠN MUA HÀNG ' + (poNgay ? h(poNgay) + ' NGÀY GẦN ĐÂY' : 'TẤT CẢ') + '</div>' +
    '<div style="font-size:24px;font-weight:800">' + money(kq.tong_tien) + ' đ</div>' +
    '<div style="font-size:12.5px;color:#6b7280">' + money(kq.tong_dong) + ' đơn · đang xem ' + money(ds.length) + '</div>' +
    mkNhacCat(kq.bi_cat, 'đơn') + '</div>';

  html += '<div class="card" style="padding:10px 12px">' +
    mkChipNgay([[30, '30 ngày'], [60, '60 ngày'], [180, '6 tháng'], [0, 'Tất cả']], poNgay, 'data-pongay') + '</div>';
  html += '<div class="card" style="padding:10px 12px">' + mkChipNhom(kq.nhom, kq.dem, poNhom, 'data-ponhom') + '</div>';
  html += mkOTim('poTim', poTim, 'Tìm theo mã đơn hoặc tên nhà cung cấp...');

  if (!ds.length) {
    html += '<div class="card"><div class="emp" style="padding:26px"><div class="e1">🫙</div><div>Không có đơn nào ở nhóm này.</div></div></div>';
  } else {
    html += '<div class="lst">' + ds.map(function (d) {
      var mau = { tre_hen: '#b3261e', cho_hoa_don: '#b45309', nhap: '#6b7280', xong: '#0f766e' }[d.nhom] || '#374151';
      var ten = '';
      (kq.nhom || []).forEach(function (n) { if (n.k === d.nhom) ten = n.ic + ' ' + n.ten; });
      return '<div class="shi" data-po="' + h(d.name) + '" style="display:flex;gap:10px;align-items:flex-start;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
        '<div style="flex:1;min-width:0">' +
        '<b style="font-size:14.5px">' + h(d.supplier_name || d.supplier) + '</b>' +
        '<div style="font-size:12px;color:#98a2b3">' + h(d.name) + ' · đặt ' + ngayNgan(d.ngay) +
        (d.hen ? ' · hẹn ' + ngayNgan(d.hen) : '') + '</div>' +
        '<div style="font-size:12px;color:' + mau + ';font-weight:600;margin-top:3px">' + h(ten) +
        (d.tre_ngay ? ' ' + d.tre_ngay + ' ngày' : '') +
        (d.nhom === 'nhan_mot_phan' ? ' · đã nhận ' + Math.round(d.per_received) + '%' : '') +
        (d.con_nhan > 0.0001 ? ' · <span style="color:#b45309">còn ' + money(d.con_nhan) + ' của ' + d.so_mon_con + ' món</span>' : '') + '</div></div>' +
        '<b style="white-space:nowrap">' + money(d.grand_total) + ' đ</b></div>';
    }).join('') + '</div>';
  }

  var b = frame('Đơn mua hàng', html);
  b.onclick = function (e) {
    var t = e.target.closest('[data-ponhom]');
    if (t) { poNhom = t.getAttribute('data-ponhom'); return go(scrDonMua, true); }
    t = e.target.closest('[data-pongay]');
    if (t) { poNgay = parseInt(t.getAttribute('data-pongay'), 10); return go(scrDonMua, true); }
    t = e.target.closest('[data-po]');
    if (t) { poXem = t.getAttribute('data-po'); return go(scrDonMuaXem, true); }
  };
  var o = document.getElementById('poTim');
  if (o) o.onchange = function () { poTim = o.value; go(scrDonMua, true); };
}

async function scrDonMuaXem() {
  frame('Đơn mua hàng', '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api('vagabond.mua_hang.xem_po', { name: poXem }); }
  catch (e) { frame('Đơn mua hàng', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không đọc được') + '</div></div>'); return; }

  var html = '<div class="card" style="padding:13px 14px;line-height:1.7">' +
    '<b style="font-size:15px">' + h(d.ten_ncc || d.ncc) + '</b>' +
    '<div style="font-size:12.5px;color:#6b7280">' + h(d.name) + ' · đặt ngày ' + ngayNgan(d.ngay) +
    (d.hen ? ' · hẹn giao ' + ngayNgan(d.hen) : '') + '</div>' +
    '<div style="font-size:13px;margin-top:6px">Đã nhận <b>' + Math.round(d.da_nhan) + '%</b> · đã lên hoá đơn <b>' + Math.round(d.da_hoa_don) + '%</b></div>' +
    (d.con_nhan > 0.0001
      ? '<div style="margin-top:9px;background:#fff6e5;border:1.5px solid #fde3a7;border-radius:9px;padding:10px 12px;font-size:13px;color:#8a5b00">' +
        'Đơn này còn nợ <b>' + money(d.con_nhan) + '</b> đơn vị của <b>' + d.so_mon_con + ' món</b>. Kho vào màn Nhập kho, tab "Còn phải nhận" để nhận đợt tiếp theo.</div>'
      : '') +
    '</div>';

  html += '<div class="sec">Mặt hàng</div><div class="card" style="padding:6px 14px">' +
    d.mon.map(function (m) {
      return '<div style="display:flex;justify-content:space-between;gap:10px;padding:8px 0;border-bottom:1px solid #f0f2f6">' +
        '<div style="flex:1;min-width:0">' + h(m.ten || m.ma) +
        '<div style="color:#a0a6b4;font-size:12px">đặt ' + money(m.sl) + ' ' + h(m.dvt || '') +
        ' · đã nhận ' + money(m.da_nhan) +
        (m.con_lai > 0.0001 ? ' · <b style="color:#b45309">còn ' + money(m.con_lai) + '</b>' : '') +
        ' · ' + money(m.gia) + ' đ</div></div>' +
        '<b style="white-space:nowrap">' + money(m.tien) + '</b></div>';
    }).join('') +
    '<div style="display:flex;justify-content:space-between;padding:9px 0;color:#5a6070"><span>Tiền hàng</span><span>' + money(d.tong_hang) + ' đ</span></div>' +
    (d.thue ? '<div style="display:flex;justify-content:space-between;padding:2px 0;color:#5a6070"><span>Thuế và phí</span><span>' + money(d.thue) + ' đ</span></div>' : '') +
    '<div style="display:flex;justify-content:space-between;padding:9px 0;font-size:16px"><b>Tổng cộng</b><b>' + money(d.tong) + ' đ</b></div></div>';

  if ((d.lich_su_nhan || []).length) {
    html += '<div class="sec">Các đợt đã nhận hàng</div><div class="card" style="padding:6px 14px">' +
      d.lich_su_nhan.map(function (x) {
        return '<div style="display:flex;justify-content:space-between;gap:10px;padding:8px 0;border-bottom:1px solid #f0f2f6">' +
          '<div style="flex:1;min-width:0">Đợt ' + x.dot + ' · ' + ngayNgan(x.ngay) +
          '<div style="color:#a0a6b4;font-size:12px">Phiếu ' + h(x.name) + '</div></div>' +
          '<b style="white-space:nowrap">' + x.so_mon + ' món · ' + money(x.sl) + '</b></div>';
      }).join('') + '</div>';
  }

  html += '<div class="sec">Đã nối với</div><div class="card" style="padding:12px 14px;font-size:13.5px;line-height:1.8">' +
    '<div>Phiếu nhập kho: ' + (d.phieu_nhap.length ? '<b>' + d.phieu_nhap.map(h).join(', ') + '</b>' : '<span style="color:#b45309">chưa có phiếu nào</span>') + '</div>' +
    '<div>Hoá đơn mua: ' + (d.hoa_don.length ? '<b>' + d.hoa_don.map(h).join(', ') + '</b>' : '<span style="color:#b45309">chưa có hoá đơn nào</span>') + '</div>' +
    '</div>';

  frame('Đơn mua hàng', html);
}


/* ---------------- Duyet Phieu yeu cau mua hang (anh Viet duyet 15/08/2026)

   PA-3: giu nguyen so luong goc cua nhan vien, thu mua ghi so DUYET ben
   canh. Duyet 0 la tu choi, bat buoc ghi ly do.

   Phan dang gia nhat cua man nay khong phai nut tu choi ma la BANG CANH BAO
   tren tung dong: ton kho tong, so dang cho ve tu don da dat, va so cung
   mat hang dang cho duyet o phieu khac. Ba con so do tra loi thang cau hoi
   "co nen tu choi khong", con nut bam chi la buoc cuoi.

   Tien to dy = duyet yeu cau. Da kiem va cham ten truoc khi dat (QT-28). */

var dyDs = null, dyD = null;

function dySo(v) { return Math.round((Number(v) || 0) * 1000) / 1000; }

/* Bang canh bao mot dong. Mau theo muc do: 2 la gan nhu chac chan dat thua,
   1 la dang luu y, 0 thi khong ve gi ca. */
function dyCanhBao(x) {
  if (!x.canh_bao || !x.muc_canh_bao) return '';
  var m = x.muc_canh_bao === 2
    ? { nen: '#fff1f2', vien: '#fecaca', chu: '#b3261e', ic: '⚠️' }
    : { nen: '#fff6e5', vien: '#fde3a7', chu: '#8a5b00', ic: '💡' };
  return '<div style="margin:0 12px 8px;padding:10px 12px;border-radius:11px;background:' + m.nen +
    ';border:1.5px solid ' + m.vien + ';color:' + m.chu + ';font-size:12.5px;line-height:1.55">' +
    m.ic + ' ' + h(x.canh_bao) + '</div>';
}

/* Ba con so nen, bay ngang giong man nhan hang de nguoi dung quen mat. */
function dyBaSo(x) {
  function o(nhan, gt, mau, dam) {
    return '<div style="flex:1;min-width:0;text-align:center">' +
      '<div style="font-size:11px;color:#98a2b3;text-transform:uppercase;letter-spacing:.3px">' + nhan + '</div>' +
      '<div style="font-size:15px;font-weight:' + (dam ? '800' : '600') + ';color:' + mau + '">' + num(gt) + '</div></div>';
  }
  var conXanh = x.ton > 0.0001;
  var khacKho = (x.ton_tat_ca || 0) - (x.ton || 0);
  return '<div style="display:flex;gap:6px;padding:8px 12px;border-radius:11px;margin:0 12px 8px;background:' +
    (conXanh ? '#e7f8ef' : '#f7f8fa') + (conXanh ? ';border:1.5px solid #a7e3c0' : '') + '">' +
    o('Kho tổng', x.ton, conXanh ? '#0f7a44' : '#98a2b3', conXanh) +
    o('Kho bếp', khacKho, khacKho > 0.0001 ? '#0d9488' : '#98a2b3', 0) +
    o('Chờ về', x.cho_ve, x.cho_ve > 0 ? '#b45309' : '#98a2b3', 0) +
    o('Phiếu khác', x.cho_duyet, x.cho_duyet > 0 ? '#b45309' : '#98a2b3', 0) + '</div>';
}

async function scrDuyetYc() {
  frame('Duyệt yêu cầu mua', '<div class="emp"><div class="e1">⏳</div></div>');
  var kq;
  try { kq = await api('vagabond.duyet_ycmh.danh_sach', { so_ngay: 60 }); }
  catch (e) { frame('Duyệt yêu cầu mua', '<div class="emp"><div class="e1">🔒</div><div>' + h(errMsg(e)) + '</div></div>'); return; }
  dyDs = kq.phieu || [];
  var cho = dyDs.filter(function (x) { return x.con_cho > 0; });

  var html = '<div class="card" style="padding:12px 14px">' +
    '<div style="display:flex;justify-content:space-between"><span>Phiếu còn dòng chưa duyệt</span><b style="color:' + (cho.length ? '#b45309' : '#0f766e') + '">' + cho.length + '</b></div>' +
    '<div style="display:flex;justify-content:space-between;margin-top:6px"><span>Tổng phiếu đang mở</span><b>' + dyDs.length + '</b></div></div>';

  html += '<div class="sec">' + dyDs.length + ' phiếu</div><div class="card">';
  if (!dyDs.length) html += '<div class="emp" style="padding:24px"><div class="e1">✅</div><div>Không có phiếu yêu cầu mua nào đang mở.</div></div>';
  dyDs.forEach(function (x) {
    html += '<div class="hub" data-dy="' + h(x.name) + '"><div class="hi">' + (x.con_cho ? '📋' : '✅') + '</div>' +
      '<div class="ht"><div class="h1">' + h(x.bo_phan_yeu_cau || x.nguoi_yeu_cau || x.name) + '</div>' +
      '<div class="h2">' + h(x.name) + ' · ' + x.so_dong + ' dòng' +
      (x.can_ngay ? ' · cần ' + ngayNgan(x.can_ngay) : '') + '</div>' +
      '<div class="h2" style="color:' + (x.con_cho ? '#b45309' : '#0f766e') + ';font-weight:600">' +
      (x.con_cho ? x.con_cho + ' dòng chờ duyệt' : 'đã duyệt hết') +
      (x.da_tu_choi ? ' · ' + x.da_tu_choi + ' dòng từ chối' : '') + '</div></div>' +
      '<span class="fc" style="color:#c3c8d4;font-size:22px">&#8250;</span></div>';
  });
  html += '</div>';
  var b = frame('Duyệt yêu cầu mua', html);
  b.onclick = function (e) {
    var r = e.target.closest('[data-dy]'); if (!r) return;
    var nm = r.getAttribute('data-dy');
    go(function () { scrDuyetYcXem(nm); });
  };
}

async function scrDuyetYcXem(name) {
  frame('Duyệt yêu cầu mua', '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api('vagabond.duyet_ycmh.chi_tiet', { name: name }); }
  catch (e) { frame('Duyệt yêu cầu mua', '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e)) + '</div></div>'); return; }
  vgbCss();
  dyD = {
    name: name,
    lines: (d.mon || []).map(function (m) {
      return {
        dong: m.dong, ma: m.ma, ten: m.ten, dvt: m.dvt,
        xin: m.sl_yeu_cau,
        /* Chua ai duyet thi o de trong, KHONG dien san bang so xin: dien san
           thi khong phan biet duoc "da duyet du" voi "chua ai nhin". */
        duyet: m.sl_duyet,
        ly_do: m.ly_do_duyet || '',
        da_len_don: m.da_len_don,
        nguoi: m.nguoi_duyet_dong || '',
        ton: m.ton, ton_tat_ca: m.ton_tat_ca, cho_ve: m.cho_ve, cho_duyet: m.cho_duyet,
        canh_bao: m.canh_bao, muc_canh_bao: m.muc_canh_bao,
        moi: 0
      };
    })
  };
  var L = dyD.lines;

  function veLai() { go(function () { scrDuyetYcXem(name); }, true); }

  async function dyLuu() {
    var gui = L.filter(function (x) { return x.moi; });
    if (!gui.length) return toast('Chưa sửa dòng nào, không có gì để lưu.');
    var tc = gui.filter(function (x) { return (x.duyet || 0) <= 0.0001; });
    var thieuLy = tc.filter(function (x) { return !(x.ly_do || '').trim(); });
    if (thieuLy.length) return toast('Còn ' + thieuLy.length + ' dòng từ chối chưa ghi lý do. Bấm vào dòng để ghi.', 6000);
    var msg = 'Duyệt ' + gui.length + ' dòng.';
    if (tc.length) msg += ' Trong đó ' + tc.length + ' dòng bị từ chối.';
    msg += ' Số lượng nhân viên đã xin vẫn giữ nguyên, không sửa và không xoá dòng nào.';
    if (!await confirmSheet('Lưu quyết định duyệt?', msg, 'Lưu')) return;
    busy(1);
    try {
      var r = await api('vagabond.duyet_ycmh.duyet_dong', {
        name: name,
        dong: JSON.stringify(gui.map(function (x) {
          return { dong: x.dong, sl_duyet: x.duyet, ly_do_duyet: x.ly_do };
        }))
      });
      busy(0);
      toast('Đã lưu: ' + r.duyet_du + ' duyệt đủ, ' + r.cat_bot + ' cắt bớt, ' + r.tu_choi + ' từ chối.', 5000);
      return veLai();
    } catch (e) { busy(0); toast(errMsg(e), 7000); }
  }

  async function dyHoiLyDo(i) {
    var x = L[i];
    var v = await promptSheet('Vì sao từ chối "' + x.ten + '"?',
      'Nhân viên đặt hàng sẽ đọc được câu này, nên ghi rõ để lần sau không đặt lại. Ví dụ: kho tổng còn 12 kg, hoặc đã có đơn PO đặt ngày 10/08 chưa về.');
    if (v === null) return 0;
    if (!v) { toast('Phải ghi lý do thì mới từ chối được.', 4500); return 0; }
    x.ly_do = v;
    return 1;
  }

  var html = '<div class="card" style="padding:12px 14px;line-height:1.7">' +
    '<b style="font-size:15px">' + h(d.bo_phan || d.nguoi_yeu_cau || d.name) + '</b>' +
    '<div style="font-size:12.5px;color:#6b7280">' + h(d.name) + ' · lập ' + ngayNgan(d.ngay) +
    (d.can_ngay ? ' · cần ' + ngayNgan(d.can_ngay) : '') + '</div>' +
    '<div style="font-size:13px;margin-top:6px">Người yêu cầu <b>' + h(d.nguoi_yeu_cau) + '</b></div>' +
    '<div style="font-size:13px">' + (d.con_cho ? '<b style="color:#b45309">' + d.con_cho + ' dòng chờ duyệt</b>' : '<b style="color:#0f766e">Đã duyệt hết</b>') +
    (d.da_tu_choi ? ' · ' + d.da_tu_choi + ' dòng đã từ chối' : '') + '</div></div>';

  html += '<div class="rcvh">Số nhân viên xin nằm bên trái và <b>không sửa được</b>. Thu mua chỉ điền ô "Duyệt" bên phải. Duyệt 0 là từ chối và phải ghi lý do.</div>';

  html += '<div class="sec">' + L.length + ' mặt hàng</div>';
  html += L.map(function (x, i) {
    var chua = x.duyet === null || x.duyet === undefined;
    var tuChoi = !chua && x.duyet <= 0.0001;
    /* Kho tong con hang thi to ca dong xanh la: Uyen liec mot cai la biet
       dong nao dang can can nhac tu choi hoac giam so, khoi doc tung chu. */
    var conHang = x.ton > 0.0001;
    return '<div class="ic1' + (x.moi ? ' ok' : '') + '" data-dr="' + i + '"' +
      (conHang && chua ? ' style="background:#f2fbf6;border-left:5px solid #1f9254"' : '') + '>' +
      '<div class="ih"><div class="n">' + (i + 1) + '</div>' +
      '<div class="in">' + h(x.ten) +
      '<div class="ig">' + h(x.ma) + (x.da_len_don > 0.0001 ? ' · đã lên đơn ' + num(x.da_len_don) : '') + '</div>' +
      (conHang ? '<div style="margin-top:5px;display:inline-block;padding:2px 9px;border-radius:11px;font-size:12px;font-weight:700;color:#0f7a44;background:#d5f2e3">🟢 Kho tổng còn ' + num(x.ton) + ' ' + h(x.dvt) + '</div>' : '') +
      (chua ? '' : '<div style="margin-top:5px;display:inline-block;padding:2px 9px;border-radius:11px;font-size:12px;font-weight:600;color:#fff;background:' +
        (tuChoi ? '#c0392b' : (x.duyet < x.xin - 0.0001 ? '#c77700' : '#1f9254')) + '">' +
        (tuChoi ? 'Từ chối' : (x.duyet < x.xin - 0.0001 ? 'Duyệt ' + num(x.duyet) + '/' + num(x.xin) : 'Duyệt đủ')) +
        '</div>') +
      '</div></div>' +
      dyBaSo(x) + dyCanhBao(x) +
      '<div class="qw"><div style="flex:1;min-width:0">' +
      '<div class="lb">Nhân viên xin <b>' + num(x.xin) + ' ' + h(x.dvt) + '</b> · thu mua duyệt</div>' +
      '<div class="qr"><div class="stp"><button data-dm="' + i + '">&minus;</button>' +
      '<input type="number" inputmode="decimal" step="any" data-dq="' + i + '" placeholder="chưa duyệt" value="' + (chua ? '' : x.duyet) + '">' +
      '<button data-da2="' + i + '">+</button></div>' +
      '<div class="uml">' + h(x.dvt) + '</div></div></div></div>' +
      '<div style="display:flex;gap:6px;flex-wrap:wrap;padding:0 12px 10px">' +
      '<button data-ddu="' + i + '" class="btn gh" style="margin:0;flex:1;min-width:92px;padding:8px 6px;font-size:13px">Duyệt đủ</button>' +
      '<button data-dnua="' + i + '" class="btn gh" style="margin:0;flex:1;min-width:92px;padding:8px 6px;font-size:13px">Một nửa</button>' +
      '<button data-dtc="' + i + '" class="btn gh" style="margin:0;flex:1;min-width:92px;padding:8px 6px;font-size:13px;color:#b3261e;border-color:#fecaca">Từ chối</button>' +
      (chua ? '' : '<button data-dgo="' + i + '" class="btn gh" style="margin:0;flex:1;min-width:92px;padding:8px 6px;font-size:13px">Gỡ duyệt</button>') +
      '</div>' +
      (x.ly_do ? '<div style="padding:0 12px 10px;font-size:12.5px;color:#5a6070">Lý do: <b>' + h(x.ly_do) + '</b></div>' : '') +
      '</div>';
  }).join('');

  var conChua = L.filter(function (x) { return x.duyet === null || x.duyet === undefined; }).length;
  var b = frame('Duyệt ' + name, html, {
    footer:
      (conChua
        ? '<button class="btn gh" id="dyHet" style="margin:0 0 9px">✅ Duyệt tất cả ' + conChua + ' món còn lại</button>'
        : '') +
      '<button class="btn" id="dySub" style="margin:0">Lưu quyết định duyệt</button>'
  });

  b.onclick = async function (e) {
    var t, i;
    if ((t = e.target.closest('[data-ddu]'))) { i = +t.dataset.ddu; L[i].duyet = L[i].xin; L[i].ly_do = ''; L[i].moi = 1; return veLai(); }
    if ((t = e.target.closest('[data-dnua]'))) { i = +t.dataset.dnua; L[i].duyet = dySo(L[i].xin / 2); L[i].moi = 1; return veLai(); }
    if ((t = e.target.closest('[data-dtc]'))) {
      i = +t.dataset.dtc;
      if (!await dyHoiLyDo(i)) return;
      L[i].duyet = 0; L[i].moi = 1; return veLai();
    }
    if ((t = e.target.closest('[data-dm]'))) { i = +t.dataset.dm; L[i].duyet = Math.max(0, dySo((L[i].duyet || 0) - 1)); L[i].moi = 1; return veLai(); }
    if ((t = e.target.closest('[data-da2]'))) {
      i = +t.dataset.da2;
      var v = dySo((L[i].duyet || 0) + 1);
      if (v > L[i].xin + 0.0001) { v = L[i].xin; toast('Không duyệt quá số nhân viên đã xin. Cần mua thêm thì lập phiếu yêu cầu mới, để số gốc còn đối chiếu.', 6000); }
      L[i].duyet = v; L[i].moi = 1; return veLai();
    }
    if ((t = e.target.closest('[data-dgo]'))) {
      i = +t.dataset.dgo;
      var x = L[i];
      if (!x.moi) {
        if (!await confirmSheet('Gỡ duyệt "' + x.ten + '"?', 'Dòng này trở về trạng thái chưa ai duyệt. Không xoá gì, việc gỡ vẫn được ghi vết.', 'Gỡ duyệt')) return;
        busy(1);
        try { await api('vagabond.duyet_ycmh.bo_duyet', { name: name, dong_ten: x.dong }); busy(0); toast('Đã gỡ duyệt'); return veLai(); }
        catch (e2) { busy(0); return toast(errMsg(e2), 6000); }
      }
      x.duyet = null; x.ly_do = ''; x.moi = 0; return veLai();
    }
  };
  Array.prototype.forEach.call(b.querySelectorAll('[data-dq]'), function (el) {
    el.onchange = function () {
      var i = +el.dataset.dq;
      if (el.value === '') { L[i].duyet = null; L[i].moi = 0; return veLai(); }
      var v = Math.max(0, parseFloat(el.value) || 0);
      if (v > L[i].xin + 0.0001) { v = L[i].xin; toast('Không duyệt quá số nhân viên đã xin (' + num(L[i].xin) + ' ' + L[i].dvt + ').', 5500); }
      L[i].duyet = v; L[i].moi = 1; veLai();
    };
  });
  var sb = document.getElementById('dySub');
  if (sb) sb.onclick = dyLuu;

  var hb = document.getElementById('dyHet');
  if (hb) hb.onclick = async function () {
    /* Bam nut nay khi con thay doi chua luu thi de mat cong Uyen vua go:
       may chu chi nhin nhung dong CHUA co nguoi duyet, khong biet gi ve
       cac o dang sua tren man. Nen bat luu truoc. */
    if (L.filter(function (x) { return x.moi; }).length) {
      return toast('Còn thay đổi chưa lưu. Bấm "Lưu quyết định duyệt" trước rồi hãy duyệt phần còn lại.', 6500);
    }
    var conHang = L.filter(function (x) {
      return (x.duyet === null || x.duyet === undefined) && x.ton > 0.0001;
    }).length;
    var msg = 'Duyệt đủ ' + conChua + ' món chưa ai đụng tới, đúng bằng số nhân viên đã xin.\n\n' +
      'Món đã từ chối hoặc đã cắt bớt giữ nguyên, nút này không đụng tới.';
    if (conHang) {
      msg += '\n\nLưu ý: trong đó có ' + conHang + ' món kho tổng vẫn còn hàng (dòng tô xanh). ' +
        'Xem lại mấy dòng đó trước khi duyệt hết.';
    }
    if (!await confirmSheet('Duyệt tất cả các món còn lại?', msg, 'Duyệt hết')) return;
    busy(1);
    try {
      var r = await api('vagabond.duyet_ycmh.duyet_het', { name: name });
      busy(0);
      toast(r.da_duyet ? ('Đã duyệt đủ ' + r.da_duyet + ' món.') : 'Không còn món nào chưa duyệt.', 4500);
      return veLai();
    } catch (e) { busy(0); toast(errMsg(e), 7000); }
  };
}

/* ---------------- Cong no phai tra ---------------- */
var cntNcc = null;
async function scrNoPhaiTra() {
  frame('Công nợ phải trả', '<div class="emp"><div class="e1">⏳</div><div>Đang cộng sổ nợ nhà cung cấp...</div></div>');
  var kq;
  try { kq = await api('vagabond.mua_hang.cong_no_phai_tra', {}); }
  catch (e) {
    frame('Công nợ phải trả', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  var html = '<div class="card" style="padding:14px">' +
    '<div style="font-size:12px;color:#98a2b3">TỔNG CÒN PHẢI TRẢ</div>' +
    '<div style="font-size:28px;font-weight:800">' + money(kq.tong) + ' đ</div>' +
    '<div style="font-size:12.5px;color:#6b7280">' + money(kq.so_ncc) + ' nhà cung cấp</div>' +
    (kq.tong_qua_han
      ? '<div style="margin-top:9px;background:#fef2f2;border:1.5px solid #fecaca;border-radius:9px;padding:10px 12px;font-size:13px;color:#b3261e">' +
        'Trong đó <b>' + money(kq.tong_qua_han) + ' đ</b> đã quá hạn trả.</div>'
      : '<div style="margin-top:9px;font-size:13px;color:#0f766e">Chưa có khoản nào quá hạn.</div>') +
    '</div>';

  if (!(kq.ncc || []).length) {
    html += '<div class="card"><div class="emp" style="padding:26px"><div class="e1">🎉</div><div>Không nợ nhà cung cấp nào.</div></div></div>';
  } else {
    html += '<div class="sec">Nợ nhiều và quá hạn xếp lên đầu</div><div class="lst">' +
      kq.ncc.map(function (n) {
        return '<div class="shi" data-ncc="' + h(n.ncc) + '" style="display:flex;gap:10px;align-items:flex-start;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
          '<div style="flex:1;min-width:0"><b style="font-size:14.5px">' + h(n.ten) + '</b>' +
          '<div style="font-size:12px;color:#98a2b3">' + money(n.so_hd) + ' hoá đơn' +
          (n.han_gan_nhat ? ' · hạn gần nhất ' + ngayNgan(n.han_gan_nhat) : '') + '</div>' +
          (n.qua_han
            ? '<div style="font-size:12px;color:#b3261e;font-weight:600;margin-top:3px">Quá hạn ' + money(n.qua_han) + ' đ · ' + n.so_hd_qua_han + ' hoá đơn</div>'
            : '') + '</div>' +
          '<b style="white-space:nowrap">' + money(n.tien) + ' đ</b></div>';
      }).join('') + '</div>';
  }

  var b = frame('Công nợ phải trả', html);
  b.onclick = function (e) {
    var t = e.target.closest('[data-ncc]');
    if (!t) return;
    var ma = t.getAttribute('data-ncc');
    var n = (kq.ncc || []).filter(function (x) { return x.ncc === ma; })[0];
    if (n) mkSheetNoNcc(n);
  };
}

function mkSheetNoNcc(n) {
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>' + h(n.ten) + '</b><div class="x">&times;</div></div>' +
    '<div style="padding:4px 14px calc(env(safe-area-inset-bottom,0px) + 16px);max-height:78vh;overflow:auto">' +
    '<div style="font-size:13px;color:#374151;margin:8px 0 12px">Còn nợ <b>' + money(n.tien) + ' đ</b> trên ' + money(n.so_hd) + ' hoá đơn' +
    (n.qua_han ? ', trong đó <b style="color:#b3261e">' + money(n.qua_han) + ' đ quá hạn</b>' : '') + '.</div>' +
    n.hd.map(function (x) {
      return '<div style="border:1.5px solid ' + (x.tre_ngay ? '#fecaca' : '#e5e7eb') + ';background:' + (x.tre_ngay ? '#fef2f2' : '#fff') + ';border-radius:10px;padding:10px 12px;margin-bottom:8px">' +
        '<div style="display:flex;justify-content:space-between;gap:10px">' +
        '<b style="font-size:13.5px">' + h(x.name) + '</b><b>' + money(x.con_no) + ' đ</b></div>' +
        '<div style="font-size:12px;color:#6b7280;margin-top:3px">' +
        (x.so_hd_ncc ? 'Số hoá đơn NCC ' + h(x.so_hd_ncc) + ' · ' : '') +
        'ngày ' + ngayNgan(x.ngay) + (x.han ? ' · hạn trả ' + ngayNgan(x.han) : '') +
        (x.tre_ngay ? ' · <b style="color:#b3261e">trễ ' + x.tre_ngay + ' ngày</b>' : '') + '</div>' +
        (x.tong !== x.con_no ? '<div style="font-size:12px;color:#98a2b3">Tổng hoá đơn ' + money(x.tong) + ' đ, đã trả ' + money(x.tong - x.con_no) + ' đ</div>' : '') +
        '</div>';
    }).join('') + '</div>';
  ov.appendChild(box); document.body.appendChild(ov);
  ov.onclick = function (e) { if (e.target === ov) ov.remove(); };
  box.querySelector('.x').onclick = function () { ov.remove(); };
}

/* ---------------- Hoa don ban ra ---------------- */
async function scrHdBan() {
  frame('Hoá đơn bán ra', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc hoá đơn...</div></div>');
  var kq;
  try { kq = await api('vagabond.ke_toan.ds_hoa_don_ban', { so_ngay: ktBanNgay, quay: ktBanQuay, tu_khoa: ktBanTim, nhom: ktBanNhom }); }
  catch (e) {
    frame('Hoá đơn bán ra', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  var ds = kq.hd || [];

  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">HOÁ ĐƠN BÁN RA · ' + ngayNgan(kq.tu) + ' - ' + ngayNgan(kq.den) + '</div>' +
    '<div style="font-size:24px;font-weight:800">' + money(kq.tong) + ' đ</div>' +
    '<div style="font-size:12.5px;color:#6b7280">' + money(kq.tong_dong) + ' hoá đơn · đang xem ' + money(ds.length) +
    (kq.con_thu ? ' · còn phải thu ' + money(kq.con_thu) + ' đ' : '') + '</div>' +
    mkNhacCat(kq.bi_cat, 'hoá đơn') + '</div>';

  html += '<div class="card" style="padding:10px 12px">' +
    mkChipNgay([[7, '7 ngày'], [30, '30 ngày'], [90, '3 tháng'], [365, '1 năm']], ktBanNgay, 'data-ktbngay') + '</div>';
  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
    [['', 'Cả ba điểm'], ['SALES', 'Sales Online'], ['TCV', 'District 1'], ['NVHTN', 'NVHTN']]
      .map(function (q) { return posChipNut('data-ktbquay="' + q[0] + '"', q[1], ktBanQuay === q[0]); }).join('')) + '</div>';
  html += '<div class="card" style="padding:10px 12px">' + mkChipNhom(kq.nhom, kq.dem, ktBanNhom, 'data-ktbnhom') + '</div>';
  html += mkOTim('ktBanTim', ktBanTim, 'Tìm theo mã phiếu, tên khách, số hoá đơn điện tử...');

  html += mkBangHd(ds, 'ban');
  var b = frame('Hoá đơn bán ra', html);
  b.onclick = function (e) {
    var t = e.target.closest('[data-ktbnhom]');
    if (t) { ktBanNhom = t.getAttribute('data-ktbnhom'); return go(scrHdBan, true); }
    t = e.target.closest('[data-ktbngay]');
    if (t) { ktBanNgay = parseInt(t.getAttribute('data-ktbngay'), 10); return go(scrHdBan, true); }
    t = e.target.closest('[data-ktbquay]');
    if (t) { ktBanQuay = t.getAttribute('data-ktbquay'); return go(scrHdBan, true); }
    t = e.target.closest('[data-hdb]');
    if (t) return go(function () { scrDsView(t.getAttribute('data-hdb'), true); });
  };
  var o = document.getElementById('ktBanTim');
  if (o) o.onchange = function () { ktBanTim = o.value; go(scrHdBan, true); };
}

var TEN_DIEM_BAN = { SALES: 'Sales Online', TCV: 'District 1', NVHTN: 'NVHTN' };

function mkBangHd(ds, loai) {
  if (!ds.length) return '<div class="card"><div class="emp" style="padding:26px"><div class="e1">🫙</div><div>Không có hoá đơn nào ở nhóm này.</div></div></div>';
  return '<div class="lst">' + ds.map(function (d) {
    if (loai === 'ban') {
      return '<div class="shi" data-hdb="' + h(d.name) + '" style="display:flex;gap:10px;align-items:flex-start;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
        '<div style="flex:1;min-width:0"><b style="font-size:14px">' + h(d.khach || 'Khách lẻ') + '</b>' +
        '<div style="font-size:12px;color:#98a2b3">' + h(d.name) + ' · ' + ngayNgan(d.posting_date) +
        ' · ' + h(TEN_DIEM_BAN[d.diem] || d.diem) + '</div>' +
        '<div style="font-size:12px;color:#6b7280;margin-top:3px">' +
        (d.custom_hddt_so ? 'HĐ ' + h(d.custom_hddt_so) + ' · ' + h(d.custom_hddt_trang_thai || '') : '<span style="color:#b45309">chưa xuất hoá đơn điện tử</span>') +
        (d.vgb_pt_thanh_toan ? ' · ' + h(d.vgb_pt_thanh_toan) : '') +
        (d.docstatus === 0 && !d.vgb_huy ? ' · <b style="color:#b45309">còn nháp</b>' : '') +
        (d.docstatus === 2 || d.vgb_huy ? ' · <b style="color:#b3261e">🚫 đã huỷ</b>' : '') +
        (d.vgb_huy && d.vgb_huy_ly_do ? ' <span style="color:#b3261e">(' + h(d.vgb_huy_ly_do) + ')</span>' : '') +
        (d.da_sua ? ' · <b style="color:#92400e">✏️ đã sửa</b>' : '') + '</div></div>' +
        '<div style="text-align:right;white-space:nowrap"><b>' + money(d.grand_total) + '</b>' +
        (d.docstatus === 1 && d.outstanding_amount > 0 ? '<div style="font-size:11.5px;color:#b3261e">còn ' + money(d.outstanding_amount) + '</div>' : '') +
        '</div></div>';
    }
    return '<div class="shi" style="display:flex;gap:10px;align-items:flex-start;padding:12px 14px;border-bottom:1px solid #f2f4f7">' +
      '<div style="flex:1;min-width:0"><b style="font-size:14px">' + h(d.supplier_name || d.supplier) + '</b>' +
      '<div style="font-size:12px;color:#98a2b3">' + h(d.name) + ' · ' + ngayNgan(d.posting_date) +
      (d.bill_no ? ' · số ' + h(d.bill_no) : '') + '</div>' +
      '<div style="font-size:12px;color:#6b7280;margin-top:3px">' +
      (d.vgb_huy ? '<b style="color:#b3261e">🚫 đã huỷ' + (d.vgb_huy_ly_do ? ' (' + h(d.vgb_huy_ly_do) + ')' : '') + '</b>'
        : d.docstatus === 0 ? '<b style="color:#b45309">còn nháp</b>'
        : d.docstatus === 2 ? '<b style="color:#b3261e">đã huỷ</b>'
          : d.outstanding_amount > 0
            ? (d.tre_ngay ? '<b style="color:#b3261e">quá hạn ' + d.tre_ngay + ' ngày</b>' : 'hạn trả ' + ngayNgan(d.due_date || ''))
            : '<span style="color:#0f766e">đã trả xong</span>') +
      (d.da_sua ? ' · <b style="color:#92400e">✏️ đã sửa</b>' : '') + '</div></div>' +
      '<div style="text-align:right;white-space:nowrap"><b>' + money(d.grand_total) + '</b>' +
      (d.docstatus === 1 && d.outstanding_amount > 0 ? '<div style="font-size:11.5px;color:#b3261e">còn ' + money(d.outstanding_amount) + '</div>' : '') +
      '</div></div>';
  }).join('') + '</div>';
}

/* ---------------- Hoa don mua vao ---------------- */
async function scrHdMua() {
  frame('Hoá đơn mua vào', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc hoá đơn...</div></div>');
  var kq;
  try { kq = await api('vagabond.ke_toan.ds_hoa_don_mua', { so_ngay: ktMuaNgay, tu_khoa: ktMuaTim, nhom: ktMuaNhom }); }
  catch (e) {
    frame('Hoá đơn mua vào', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  var ds = kq.hd || [];

  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">HOÁ ĐƠN MUA VÀO · ' + ngayNgan(kq.tu) + ' - ' + ngayNgan(kq.den) + '</div>' +
    '<div style="font-size:24px;font-weight:800">' + money(kq.tong) + ' đ</div>' +
    '<div style="font-size:12.5px;color:#6b7280">' + money(kq.tong_dong) + ' hoá đơn · đang xem ' + money(ds.length) +
    (kq.con_no ? ' · còn nợ ' + money(kq.con_no) + ' đ' : '') + '</div>' +
    mkNhacCat(kq.bi_cat, 'hoá đơn') + '</div>';

  html += '<div class="card" style="padding:10px 12px">' +
    mkChipNgay([[30, '30 ngày'], [60, '60 ngày'], [180, '6 tháng'], [365, '1 năm']], ktMuaNgay, 'data-ktmngay') + '</div>';
  html += '<div class="card" style="padding:10px 12px">' + mkChipNhom(kq.nhom, kq.dem, ktMuaNhom, 'data-ktmnhom') + '</div>';
  html += mkOTim('ktMuaTim', ktMuaTim, 'Tìm theo mã phiếu, tên nhà cung cấp, số hoá đơn...');
  html += mkBangHd(ds, 'mua');

  var b = frame('Hoá đơn mua vào', html);
  b.onclick = function (e) {
    var t = e.target.closest('[data-ktmnhom]');
    if (t) { ktMuaNhom = t.getAttribute('data-ktmnhom'); return go(scrHdMua, true); }
    t = e.target.closest('[data-ktmngay]');
    if (t) { ktMuaNgay = parseInt(t.getAttribute('data-ktmngay'), 10); return go(scrHdMua, true); }
  };
  var o = document.getElementById('ktMuaTim');
  if (o) o.onchange = function () { ktMuaTim = o.value; go(scrHdMua, true); };
}




/* ================= Đề nghị chi nội bộ =================

Anh Việt 19/08/2026: nút này nằm trong phân hệ Đặt hàng và MỌI nhân viên
đều thấy, vì mua chai nước mắm hay bình gas là việc của bạn bếp bạn quầy
chứ không riêng thu mua. Lập xong thì Uyên và chuỗi duyệt xử tiếp.

Màn cố ý ngắn: sáu ô bắt buộc, phần còn lại chỉ hiện khi cần. Bạn đứng
trong bếp cầm điện thoại một tay thì mỗi ô thừa là một lần bỏ dở. */
var dncDm = null, dncForm = null, dncMoTu = {}, dncTamUng = null;

/* Một khoản chi rỗng. Mỗi khoản mang một `id` riêng chứ không dựa vào vị trí
   trong mảng: xoá khoản thứ hai giữa lúc đang gõ khoản thứ tư thì mọi chỉ số
   sau đó lùi một bậc, và ô đang gõ dở bị gán sang khoản khác. */
var dncIdSau = 1;
function dncKhoanMoi() {
  return {
    id: 'k' + (dncIdSau++), noi_dung: '', so_tien: '', phan_loai: '',
    loai_chung_tu: '', so_hoa_don: '', ngay_hoa_don: '', mst: '',
    ten_ban: '', dia_chi_ban: '', ghi_chu: ''
  };
}

function dncMoi() {
  return {
    loai_nghiep_vu: 'Chi phí', ngay_can_tt: '', dien_giai: '',
    hinh_thuc: 'Hoàn tiền cho nhân viên', nha_cung_cap: '', phuong_thuc: 'Chuyển khoản',
    ten_tk: '', so_tk: '', ngan_hang: '', thuoc_tam_ung: '',
    cac_khoan: [dncKhoanMoi()]
  };
}

/* Tra hai cờ của một loại chứng từ. Đọc từ DANH MỤC máy chủ gửi về, không so
   chuỗi với chữ "Hoá đơn VAT": đổi tên một dòng danh mục thì ba ô hoá đơn
   không được phép im lặng biến mất. */
function dncCoCT(ten) {
  return dncMoTu[(ten || '').trim()] || { la_hoa_don_vat: 0, bat_buoc_tep: 0 };
}

function dncTong(f) {
  return ((f && f.cac_khoan) || []).reduce(function (t, k) {
    return t + (Number(String(k.so_tien).replace(/[^0-9.-]/g, '')) || 0);
  }, 0);
}

async function scrDeNghiChi() {
  frame('Đề nghị chi', '<div class="emp"><div class="e1">⏳</div><div>Đang mở...</div></div>');
  if (!dncDm) {
    try { dncDm = await api('vagabond.de_nghi_chi.danh_muc', {}); }
    catch (e) {
      frame('Đề nghị chi', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
      return;
    }
    dncMoTu = {};
    ((dncDm && dncDm.loai_chung_tu) || []).forEach(function (x) { dncMoTu[x.ten] = x; });
  }
  if (!dncForm) dncForm = dncMoi();
  var ds = { ds: [] };
  try { ds = await api('vagabond.de_nghi_chi.danh_sach', { so_dong: 30 }); } catch (e2) { }
  dncVe(ds.ds || []);
}

/* Đọc mọi ô đang hiện trên màn về lại đối tượng. Gọi trước MỌI lần vẽ lại,
   nếu không thì chữ người ta vừa gõ bay mất khi bấm một cái chip. */
function dncDoc() {
  var f = dncForm;
  var g = function (id) { var o = document.getElementById(id); return o ? o.value : null; };
  ['ngay_can_tt', 'dien_giai', 'nha_cung_cap', 'ten_tk', 'so_tk'].forEach(function (k) {
    var v = g('dnc_' + k);
    if (v !== null) f[k] = v;
  });
  (f.cac_khoan || []).forEach(function (k) {
    ['noi_dung', 'so_tien', 'so_hoa_don', 'ngay_hoa_don', 'mst', 'ten_ban', 'dia_chi_ban', 'ghi_chu'].forEach(function (o) {
      var v = g('dnk_' + o + '_' + k.id);
      if (v !== null) k[o] = v;
    });
  });
  return f;
}

/* Cập nhật con số tổng NGAY trên màn, không vẽ lại cả trang.
   Vẽ lại cả trang mỗi lần gõ một chữ số thì ô đang gõ mất con trỏ. */
function dncNhayTong() {
  var f = dncDoc();
  var o = document.getElementById('dncTongSo');
  if (o) o.textContent = money(dncTong(f)) + ' đ';
  var c = document.getElementById('dncTongCanh');
  if (c) {
    var nguong = (dncDm && dncDm.nguong_giam_doc) || 2000000;
    c.innerHTML = dncTong(f) >= nguong
      ? 'Từ ' + money(nguong) + ' đ trở lên nên phiếu này cần <b>giám đốc duyệt thêm một cấp</b>.'
      : 'Dưới ' + money(nguong) + ' đ nên phiếu đi thẳng từ mua hàng sang kế toán.';
  }
}

/* Một khoản chi = một Thẻ. Cố ý KHÔNG dùng lưới: mười cột trên màn điện
   thoại thì chữ bị cắt hoặc phải cuộn ngang, mà bạn bếp cầm máy một tay. */
function dncTheKhoan(k, i, tong) {
  var ct = dncCoCT(k.loai_chung_tu);
  var o = function (id, nhan, gtri, kieu, gy) {
    return '<div style="flex:1;min-width:0">' +
      '<div style="font-size:11.5px;color:#6b7280;margin-bottom:3px">' + h(nhan) + '</div>' +
      '<input class="tin" id="dnk_' + id + '_' + k.id + '"' +
      (kieu ? ' type="' + kieu + '"' : '') +
      (kieu === 'number' ? ' inputmode="numeric"' : '') +
      (gy ? ' placeholder="' + h(gy) + '"' : '') +
      ' value="' + h(gtri || '') + '"></div>';
  };
  var html = '<div class="card" data-kid="' + h(k.id) + '" style="padding:12px 14px;margin-bottom:10px;border:1.5px solid #e5e7eb">' +
    '<div style="display:flex;align-items:center;gap:8px;margin-bottom:9px">' +
    '<span style="flex:none;background:#0f766e;color:#fff;border-radius:999px;width:24px;height:24px;' +
    'display:flex;align-items:center;justify-content:center;font-size:12.5px;font-weight:800">' + i + '</span>' +
    '<b style="flex:1;font-size:13.5px;color:#0f172a">Khoản chi ' + i + '</b>' +
    (tong > 1
      ? '<button class="dncXoa" data-kid="' + h(k.id) + '" style="flex:none;border:1.5px solid #fecaca;background:#fef2f2;' +
        'color:#b3261e;border-radius:8px;padding:5px 11px;font-size:12px;font-weight:700">Xoá</button>'
      : '') +
    '</div>';

  html += '<input class="tin" id="dnk_noi_dung_' + k.id + '" placeholder="Mua gì, chi cho việc gì" value="' +
    h(k.noi_dung || '') + '" style="margin-bottom:8px">';
  html += '<div style="display:flex;gap:8px;margin-bottom:9px">' + o('so_tien', 'Số tiền (đ)', k.so_tien, 'number') + '</div>';

  html += '<button class="dncPl" data-kid="' + h(k.id) + '" style="width:100%;text-align:left;border:1.5px solid ' +
    (k.phan_loai ? '#0f766e' : '#e5e7eb') + ';background:#fff;border-radius:11px;padding:11px 13px;font-size:14px;' +
    'color:' + (k.phan_loai ? '#0f172a' : '#9ca3af') + ';font-weight:' + (k.phan_loai ? '600' : '400') + ';margin-bottom:8px">' +
    (k.phan_loai ? h(k.phan_loai) : 'Chọn phân loại chi phí') + '</button>';

  html += '<button class="dncCt" data-kid="' + h(k.id) + '" style="width:100%;text-align:left;border:1.5px solid ' +
    (k.loai_chung_tu ? '#0f766e' : '#e5e7eb') + ';background:#fff;border-radius:11px;padding:11px 13px;font-size:14px;' +
    'color:' + (k.loai_chung_tu ? '#0f172a' : '#9ca3af') + ';font-weight:' + (k.loai_chung_tu ? '600' : '400') + '">' +
    (k.loai_chung_tu ? h(k.loai_chung_tu) : 'Chọn loại chứng từ đính kèm') + '</button>';

  /* Ba ô hoá đơn chỉ hiện khi loại chứng từ mang CỜ hoá đơn VAT. */
  if (ct.la_hoa_don_vat) {
    html += '<div style="margin-top:10px;padding-top:10px;border-top:1px dashed #e5e7eb">' +
      '<div style="font-size:11.5px;color:#0f766e;font-weight:800;margin-bottom:7px">THÔNG TIN HOÁ ĐƠN VAT</div>' +
      '<div style="display:flex;gap:8px;margin-bottom:8px">' +
      o('so_hoa_don', 'Số hoá đơn', k.so_hoa_don) +
      o('ngay_hoa_don', 'Ngày hoá đơn', k.ngay_hoa_don, 'date') + '</div>' +
      '<div style="font-size:11.5px;color:#6b7280;margin-bottom:3px">Mã số thuế người bán</div>' +
      '<input class="tin dncMst" id="dnk_mst_' + k.id + '" data-kid="' + h(k.id) + '" inputmode="numeric" ' +
      'placeholder="Gõ xong bấm ra ngoài, máy tự tra tên" value="' + h(k.mst || '') + '">' +
      '<div id="dncMstNhac_' + k.id + '" style="font-size:11.5px;color:#98a2b3;margin-top:5px;line-height:1.55">' +
      'Máy tra tên và địa chỉ công ty từ cổng thông tin. Tra không ra thì anh chị gõ tay, vẫn lưu được.</div>' +
      '<input class="tin" id="dnk_ten_ban_' + k.id + '" placeholder="Tên người bán" value="' +
      h(k.ten_ban || '') + '" style="margin-top:8px">' +
      '<input class="tin" id="dnk_dia_chi_ban_' + k.id + '" placeholder="Địa chỉ người bán" value="' +
      h(k.dia_chi_ban || '') + '" style="margin-top:8px">' +
      '</div>';
  }
  return html + '</div>';
}

function dncVe(lichSu) {
  var f = dncForm, dm = dncDm || {};
  var nguong = dm.nguong_giam_doc || 2000000;
  var chip = function (ten, ds, dang) {
    return '<div class="sec">' + ten + '</div><div class="card" style="padding:10px 12px">' +
      kmHangChip((ds || []).map(function (x) {
        return posChipNut('data-dnc="' + h(dang) + '|' + h(x) + '"', h(x), f[dang] === x);
      }).join('')) + '</div>';
  };
  var tong = dncTong(f);
  var khoan = f.cac_khoan || [];

  var html = '<div class="card" style="padding:12px 14px;font-size:13px;line-height:1.65;color:#374151">' +
    'Bạn ứng tiền túi mua đồ cho tiệm, hoặc cần công ty trả thẳng cho người bán thì lập phiếu ở đây. ' +
    'Một phiếu ghi được <b>nhiều khoản</b>, đi chợ một buổi về thì gộp hết vào một phiếu, ' +
    'không phải lập từng cái.</div>';

  html += chip('Loại nghiệp vụ', dm.loai_nghiep_vu, 'loai_nghiep_vu');

  /* Hoàn ứng thì phải nói rõ hoàn cho lần tạm ứng nào, nếu không thì bảng
     cấn trừ không bao giờ khớp. */
  if (f.loai_nghiep_vu === 'Hoàn ứng') {
    var tu = (dncTamUng || []).filter(function (x) { return x.ma === f.thuoc_tam_ung; })[0];
    html += '<div class="sec">Cấn trừ tạm ứng</div><div class="card" style="padding:12px 14px">' +
      '<button class="btn gh" id="dncTu" style="margin:0;width:100%;text-align:left">' +
      (f.thuoc_tam_ung ? '🔗 ' + h(f.thuoc_tam_ung) : '🔗 Chọn phiếu tạm ứng cần hoàn') + '</button>';
    if (tu) {
      html += '<div style="font-size:12.5px;color:#374151;background:#f0fdf4;border:1px solid #a7f3d0;' +
        'border-radius:9px;padding:9px 11px;margin-top:9px;line-height:1.6">' +
        'Đã ứng <b>' + money(tu.da_ung) + ' đ</b>, đã hoàn <b>' + money(tu.da_hoan_ung) + ' đ</b>. ' +
        h(tu.nhac || '') + '</div>';
    }
    html += '</div>';
  }

  /* ---- Bảng kê dạng Thẻ ---- */
  html += '<div class="sec">Bảng kê khoản chi · ' + khoan.length + ' khoản</div>' +
    khoan.map(function (k, i) { return dncTheKhoan(k, i + 1, khoan.length); }).join('') +
    '<button class="btn gh" id="dncThem" style="margin:0 0 10px;width:100%">+ Thêm khoản chi</button>';

  html += '<div class="card" style="padding:13px 14px;background:#f0fdfa;border:1.5px solid #99f6e4;margin-bottom:10px">' +
    '<div style="display:flex;align-items:baseline;gap:10px">' +
    '<div style="flex:1;font-size:13.5px;font-weight:700;color:#0f766e">Tổng tiền phiếu</div>' +
    '<div id="dncTongSo" style="font-size:20px;font-weight:800;color:#0f766e">' + money(tong) + ' đ</div></div>' +
    '<div id="dncTongCanh" style="font-size:11.5px;color:#0f766e;margin-top:5px;line-height:1.55">' +
    (tong >= nguong
      ? 'Từ ' + money(nguong) + ' đ trở lên nên phiếu này cần <b>giám đốc duyệt thêm một cấp</b>.'
      : 'Dưới ' + money(nguong) + ' đ nên phiếu đi thẳng từ mua hàng sang kế toán.') + '</div></div>';

  html += '<div class="sec">Thời hạn và diễn giải</div><div class="card" style="padding:12px 14px">' +
    '<div style="font-size:11.5px;color:#6b7280;margin-bottom:3px">Cần trả trước ngày</div>' +
    '<input class="tin" id="dnc_ngay_can_tt" type="date" value="' + h(f.ngay_can_tt) + '" style="margin-bottom:8px">' +
    '<input class="tin" id="dnc_dien_giai" placeholder="Diễn giải thêm (không bắt buộc)" value="' + h(f.dien_giai) + '"></div>';

  html += chip('Ai nhận tiền', dm.hinh_thuc, 'hinh_thuc');
  if (f.hinh_thuc === 'Thanh toán cho nhà cung cấp') {
    html += '<div class="card" style="padding:12px 14px">' +
      '<input class="tin" id="dnc_nha_cung_cap" placeholder="Mã nhà cung cấp" value="' + h(f.nha_cung_cap) + '">' +
      '<div style="font-size:11.5px;color:#98a2b3;margin-top:6px;line-height:1.6">' + h(dm.nhac_ncc || '') + '</div></div>';
  }

  html += chip('Phương thức thanh toán', dm.phuong_thuc, 'phuong_thuc');
  if (f.phuong_thuc === 'Chuyển khoản') {
    html += '<div class="card" style="padding:12px 14px">' +
      '<input class="tin" id="dnc_ten_tk" placeholder="Tên chủ tài khoản" value="' + h(f.ten_tk) + '" style="margin-bottom:8px">' +
      '<input class="tin" id="dnc_so_tk" placeholder="Số tài khoản" value="' + h(f.so_tk) + '" style="margin-bottom:8px">' +
      /* Ngân hàng là NÚT mở bảng chọn có ô tìm, không phải ô gõ tự do: danh
         mục NAPAS có 581 dòng và gõ tay thì sai chính tả là tệp chuyển tiền
         MB Biz không nhận. */
      '<button class="btn gh" id="dncNh" style="margin:0;width:100%;text-align:left;color:' +
      (f.ngan_hang ? '#0f172a' : '#9ca3af') + '">' +
      (f.ngan_hang ? '🏦 ' + h(f.ngan_hang) : '🏦 Chọn ngân hàng') + '</button></div>';
  }

  if ((lichSu || []).length) {
    html += '<div class="sec">Phiếu của tôi · ' + lichSu.length + '</div><div class="card">' +
      lichSu.slice(0, 12).map(function (x) {
        return '<div style="display:flex;gap:10px;padding:11px 14px;border-bottom:1px solid #f2f4f7">' +
          '<div style="flex:1;min-width:0"><b style="font-size:13.5px">' + h(x.tieu_de || x.ten_khoan_chi || x.name) + '</b>' +
          '<div style="font-size:11.5px;color:#98a2b3;margin-top:2px">' + h(x.name) +
          (x.so_khoan > 1 ? ' · ' + x.so_khoan + ' khoản' : '') + '</div></div>' +
          '<div style="text-align:right"><b style="font-size:13.5px">' + money(x.tien != null ? x.tien : x.so_tien) + ' đ</b>' +
          '<div style="font-size:11px;font-weight:700;color:#6b7280">' + h(x.nhan_trang_thai || '') + '</div></div></div>';
      }).join('') + '</div>';
  }

  var b = frame('Đề nghị chi', html, {
    footer: '<div style="display:flex;gap:8px">' +
      '<button class="btn" id="dncGui" style="margin:0;flex:2">📤 Lập và gửi duyệt</button>' +
      '<button class="btn gh" id="dncNhap" style="margin:0;flex:1">💾 Lưu nháp</button></div>'
  });

  /* Tổng nhảy theo thời gian thực khi gõ tiền. Chỉ đổi đúng con số, không
     vẽ lại trang, để ô đang gõ không mất con trỏ. */
  b.querySelectorAll('input[id^="dnk_so_tien_"]').forEach(function (n) {
    n.oninput = dncNhayTong;
  });

  /* Tra mã số thuế khi rời ô. Luôn cho sửa tay: tra không ra thì hai ô tên
     và địa chỉ vẫn gõ được như thường. */
  b.querySelectorAll('.dncMst').forEach(function (n) {
    n.onblur = function () { dncTraMst(n.getAttribute('data-kid'), n.value); };
  });

  b.addEventListener('click', function (e) {
    var t = e.target.closest('[data-dnc]');
    if (!t) return;
    var p = t.getAttribute('data-dnc').split('|');
    dncDoc();
    dncForm[p[0]] = p[1];
    if (p[0] === 'loai_nghiep_vu') {
      /* Đổi loại nghiệp vụ thì bảng phân loại đổi theo, nên phải xoá lựa
         chọn cũ ở mọi khoản - giữ lại là lưu xuống một phân loại không
         thuộc loại này. */
      (dncForm.cac_khoan || []).forEach(function (k) { k.phan_loai = ''; });
      if (p[1] !== 'Hoàn ứng') dncForm.thuoc_tam_ung = '';
    }
    dncVe(lichSu);
  });

  var nThem = document.getElementById('dncThem');
  if (nThem) nThem.onclick = function () {
    dncDoc();
    if ((dncForm.cac_khoan || []).length >= 200) {
      return baoTin('Một phiếu tối đa 200 khoản. Anh chị tách ra làm nhiều phiếu giúp em.');
    }
    dncForm.cac_khoan.push(dncKhoanMoi());
    dncVe(lichSu);
  };

  b.querySelectorAll('.dncXoa').forEach(function (n) {
    n.onclick = async function () {
      dncDoc();
      var kid = n.getAttribute('data-kid');
      var k = (dncForm.cac_khoan || []).filter(function (x) { return x.id === kid; })[0];
      if (k && ((k.noi_dung || '').trim() || Number(k.so_tien) > 0)) {
        if (!await hoiCo('Xoá khoản chi', 'Xoá "' + h(k.noi_dung || 'khoản này') + '" khỏi bảng kê?', 'Xoá', 1)) return;
      }
      dncForm.cac_khoan = (dncForm.cac_khoan || []).filter(function (x) { return x.id !== kid; });
      if (!dncForm.cac_khoan.length) dncForm.cac_khoan = [dncKhoanMoi()];
      dncVe(lichSu);
    };
  });

  b.querySelectorAll('.dncPl').forEach(function (n) {
    n.onclick = function () {
      dncDoc();
      var kid = n.getAttribute('data-kid');
      var k = (dncForm.cac_khoan || []).filter(function (x) { return x.id === kid; })[0];
      if (!k) return;
      var ds = dncForm.loai_nghiep_vu === 'Tạm ứng' ? (dm.phan_loai_tam_ung || []) : (dm.phan_loai || []);
      sheet('Phân loại chi phí', ds.map(function (x) { return { value: x, label: x }; }),
        k.phan_loai || '', function (it) { k.phan_loai = it.value; dncVe(lichSu); }, true);
    };
  });

  b.querySelectorAll('.dncCt').forEach(function (n) {
    n.onclick = function () {
      dncDoc();
      var kid = n.getAttribute('data-kid');
      var k = (dncForm.cac_khoan || []).filter(function (x) { return x.id === kid; })[0];
      if (!k) return;
      sheet('Loại chứng từ đính kèm',
        ((dm.loai_chung_tu) || []).map(function (x) {
          return {
            value: x.ten, label: x.ten,
            phu: (x.la_hoa_don_vat ? 'Có số hoá đơn và mã số thuế' : '') +
                 (x.bat_buoc_tep ? (x.la_hoa_don_vat ? ' · ' : '') + 'Bắt buộc đính tệp' : '')
          };
        }),
        k.loai_chung_tu || '', function (it) { k.loai_chung_tu = it.value; dncVe(lichSu); }, true);
    };
  });

  var nNh = document.getElementById('dncNh');
  if (nNh) nNh.onclick = function () {
    dncDoc();
    nhChon(dncForm.ngan_hang, function (v) { dncForm.ngan_hang = v; dncVe(lichSu); });
  };

  var nTu = document.getElementById('dncTu');
  if (nTu) nTu.onclick = async function () {
    dncDoc();
    busy(true);
    try { dncTamUng = (await api('vagabond.de_nghi_chi.tam_ung_cua_toi', {})).ds || []; }
    catch (e4) { busy(false); return baoTin((e4 && e4.message) || 'Không đọc được danh sách tạm ứng'); }
    busy(false);
    if (!dncTamUng.length) {
      return baoTin('Anh chị chưa có phiếu tạm ứng nào đã hoàn tất, nên chưa có gì để hoàn ứng. ' +
        'Nếu khoản này không phải hoàn ứng thì đổi Loại nghiệp vụ sang Chi phí giúp em.', 'Chưa có tạm ứng');
    }
    sheet('Chọn phiếu tạm ứng',
      dncTamUng.map(function (x) {
        return { value: x.ma, label: x.ma + ' · ' + money(x.da_ung) + ' đ', phu: (x.ten || '') + ' · ' + (x.nhac || '') };
      }),
      dncForm.thuoc_tam_ung || '',
      function (it) { dncForm.thuoc_tam_ung = it.value; dncVe(lichSu); }, true);
  };

  var luu = async function (gui) {
    var f2 = dncDoc();
    /* Nhắc CẢ danh sách còn thiếu trong một lần, không bắt sửa một cái rồi
       bấm lại mới biết còn thiếu cái nữa. Máy chủ vẫn kiểm lại lần nữa. */
    var thieu = [];
    (f2.cac_khoan || []).forEach(function (k, i) {
      var stt = 'Khoản ' + (i + 1);
      if (!(k.noi_dung || '').trim()) thieu.push(stt + ': chưa ghi nội dung');
      if (!(Number(k.so_tien) > 0)) thieu.push(stt + ': chưa nhập số tiền');
      if (!k.phan_loai) thieu.push(stt + ': chưa chọn phân loại');
      if (!k.loai_chung_tu) thieu.push(stt + ': chưa chọn loại chứng từ');
      if (dncCoCT(k.loai_chung_tu).la_hoa_don_vat) {
        if (!(k.so_hoa_don || '').trim()) thieu.push(stt + ': thiếu số hoá đơn');
        if (!k.ngay_hoa_don) thieu.push(stt + ': thiếu ngày hoá đơn');
        if (!(k.mst || '').trim()) thieu.push(stt + ': thiếu mã số thuế người bán');
      }
    });
    if (thieu.length) return baoTin(thieu.join('\n'), 'Còn thiếu');
    busy(true);
    try {
      var r = await api('vagabond.de_nghi_chi.tao', { du_lieu: JSON.stringify(f2), gui_luon: gui ? 1 : 0 });
      busy(false);
      dncForm = dncMoi();
      toast('Đã lập phiếu ' + r.ma + ' · ' + h(r.nhan_trang_thai), 4000);
      go(scrDeNghiChi, true);
    } catch (e3) { busy(false); baoTin((e3 && e3.message) || 'Không lập được phiếu'); }
  };
  document.getElementById('dncGui').onclick = function () { luu(1); };
  document.getElementById('dncNhap').onclick = function () { luu(0); };
}

/* Tra mã số thuế qua cổng thông tin, điền hộ tên và địa chỉ người bán.

   Ba điều cố ý:
   - KHÔNG ghi đè khi người ta đã tự gõ tên. Máy tra được một cái tên viết
     hoa toàn bộ mà đè lên cái tên người ta vừa gõ đúng là một lần mất công.
   - Tra không ra thì chỉ nhắc, không chặn. Hộ kinh doanh thường không có
     trong cơ sở dữ liệu đăng ký doanh nghiệp, mà hoá đơn của họ vẫn hợp lệ.
   - Chỉ vẽ lại đúng hai ô, không vẽ lại cả trang: người ta vừa rời ô mã số
     thuế và rất có thể đang gõ ô kế tiếp. */
async function dncTraMst(kid, mst) {
  var k = ((dncForm && dncForm.cac_khoan) || []).filter(function (x) { return x.id === kid; })[0];
  if (!k) return;
  k.mst = (mst || '').trim();
  var nhac = document.getElementById('dncMstNhac_' + kid);
  var so = k.mst.replace(/[^0-9]/g, '');
  if (so.length < 10) {
    if (nhac && so.length) nhac.innerHTML = 'Mã số thuế phải 10, 12 hoặc 13 số. Anh chị kiểm lại giúp em.';
    return;
  }
  if (nhac) nhac.innerHTML = 'Đang tra cổng thông tin...';
  var r = null;
  try { r = await api('vagabond.api.tra_mst', { mst: k.mst }); } catch (e) { r = null; }
  var oTen = document.getElementById('dnk_ten_ban_' + kid);
  var oDc = document.getElementById('dnk_dia_chi_ban_' + kid);
  if (r && r.ok) {
    if (oTen && !(oTen.value || '').trim()) { oTen.value = r.ten || ''; k.ten_ban = r.ten || ''; }
    if (oDc && !(oDc.value || '').trim()) { oDc.value = r.dia_chi || ''; k.dia_chi_ban = r.dia_chi || ''; }
    if (nhac) nhac.innerHTML = 'Đã tra được: <b>' + h(r.ten || '') + '</b>. Sai thì anh chị sửa tay bên dưới.';
    return;
  }
  if (nhac) {
    nhac.innerHTML = (r && r.ly_do === 'khong_tim_thay')
      ? 'Không tìm thấy mã số thuế này trên cổng thông tin. Hộ kinh doanh thường không có ở đó, ' +
        'anh chị gõ tay tên và địa chỉ bên dưới, phiếu vẫn lưu được bình thường.'
      : 'Chưa tra được (mạng hoặc cổng thông tin đang bận). Anh chị gõ tay giúp em, phiếu vẫn lưu được.';
  }
}

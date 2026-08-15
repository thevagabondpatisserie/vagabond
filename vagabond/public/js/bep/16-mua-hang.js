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
  return '<div style="display:flex;gap:6px;padding:8px 12px;background:#f7f8fa;border-radius:11px;margin:0 12px 8px">' +
    o('Tồn kho', x.ton, x.ton > 0 ? '#0d9488' : '#98a2b3', 0) +
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
        ton: m.ton, cho_ve: m.cho_ve, cho_duyet: m.cho_duyet,
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
    return '<div class="ic1' + (x.moi ? ' ok' : '') + '" data-dr="' + i + '">' +
      '<div class="ih"><div class="n">' + (i + 1) + '</div>' +
      '<div class="in">' + h(x.ten) +
      '<div class="ig">' + h(x.ma) + (x.da_len_don > 0.0001 ? ' · đã lên đơn ' + num(x.da_len_don) : '') + '</div>' +
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

  var b = frame('Duyệt ' + name, html, {
    footer: '<button class="btn" id="dySub">Lưu quyết định duyệt</button>'
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



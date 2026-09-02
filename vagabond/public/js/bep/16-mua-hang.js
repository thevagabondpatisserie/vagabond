/* ---------------- Don mua hang (PO) ---------------- */

/* Trang thai duong thu di.

   Uyen bam Gui, man bao thanh cong, bon muoi phut sau doi thanh "Gui loi",
   nha cung cap khong nhan duoc gi. Cai man bao thanh cong do la loi noi doi:
   luc bam Gui thi thu moi chui vao hang doi, chua ai gui gi ca.

   Nen o day KHONG bao gio tu suy ra "Da gui". Chu do chi hien khi may chu
   noi la hang doi da Sent. Con lai la "Dang cho gui", va hong thi noi ro
   hong vi sao chu khong go hai chu "Gui loi" roi de nguoi ta ngoi doan. */
var THU_MAU = {
  'Đã gửi': ['#dcfce7', '#166534', '✅'],
  'Đang chờ gửi': ['#fef3c7', '#92400e', '⏳'],
  'Gửi lỗi': ['#fee2e2', '#b3261e', '⚠️'],
  'Chưa gửi': ['#f2f4f7', '#6b7280', '✉️']
};

function thuChip(tt) {
  var m = THU_MAU[tt];
  if (!m) return '';
  return '<span style="display:inline-block;background:' + m[0] + ';color:' + m[1] +
    ';border-radius:999px;padding:1px 8px;font-size:11.5px;font-weight:700;white-space:nowrap">' +
    m[2] + ' ' + h(tt) + '</span>';
}

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
        (d.con_nhan > 0.0001 ? ' · <span style="color:#b45309">còn ' + money(d.con_nhan) + ' của ' + d.so_mon_con + ' món</span>' : '') + '</div>' +
        (d.trang_thai_gui_email ? '<div style="margin-top:5px">' + thuChip(d.trang_thai_gui_email) + '</div>' : '') +
        '</div>' +
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

  /* Thu gui nha cung cap. Dat TRUOC muc "Da noi voi" vi khi mot don khong
     toi tay nha cung cap thi day la thu dau tien nguoi ta can biet. */
  var gt = d.gui_thu || {};
  if (gt.trang_thai) {
    var loi = gt.trang_thai === 'Gửi lỗi';
    html += '<div class="sec">Thư gửi nhà cung cấp</div>' +
      '<div class="card" style="padding:12px 14px">' +
      '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">' +
      thuChip(gt.trang_thai) +
      (gt.so_thu > 1 ? '<span style="font-size:12px;color:#98a2b3">' + gt.so_thu + ' lá thư</span>' : '') +
      /* Cham hoi: bam vao la ra day du, khong bam thi khong chiem cho. */
      '<span data-thugiaithich style="cursor:pointer;font-size:12px;color:#0B7C93;font-weight:700" title="Bấm để xem giải thích">❔</span>' +
      '</div>' +
      '<div id="thuNhac" style="display:none;margin-top:9px;background:' +
      (loi ? '#fff1f0;border:1.5px solid #fecdca;color:#7a271a' : '#f2f7f8;border:1.5px solid #d6e6ea;color:#33505a') +
      ';border-radius:9px;padding:10px 12px;font-size:13px;line-height:1.65">' +
      h(gt.nhac || '') +
      (loi ? '<div style="margin-top:7px;font-size:12.5px">Báo bộ phận kỹ thuật kèm mã đơn <b>' + h(d.name) + '</b>.</div>' : '') +
      '</div></div>';
  }

  html += '<div class="sec">Đã nối với</div><div class="card" style="padding:12px 14px;font-size:13.5px;line-height:1.8">' +
    '<div>Phiếu nhập kho: ' + (d.phieu_nhap.length ? '<b>' + d.phieu_nhap.map(h).join(', ') + '</b>' : '<span style="color:#b45309">chưa có phiếu nào</span>') + '</div>' +
    '<div>Hoá đơn mua: ' + (d.hoa_don.length ? '<b>' + d.hoa_don.map(h).join(', ') + '</b>' : '<span style="color:#b45309">chưa có hoá đơn nào</span>') + '</div>' +
    '</div>';

  var bx = frame('Đơn mua hàng', html);
  bx.onclick = function (e) {
    if (!e.target.closest('[data-thugiaithich]')) return;
    var n = document.getElementById('thuNhac');
    if (n) n.style.display = n.style.display === 'none' ? 'block' : 'none';
  };
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

async function scrDuyetYcXem(name, giuMan) {
  /* giuMan = true nghia la VE LAI MAN VOI DU LIEU DANG CO, khong hoi lai
     may chu.

     VI SAO PHAI CO CO NAY (su co 21/08/2026, Uyen duyet YCMH-2026-00031):
     truoc day moi thao tac nho deu goi lai `chi_tiet` roi dung ban may chu
     ghi de len danh sach dong. Uyen go 5 vao o Duyet, roi ra khoi o: man ve
     lai, keo ban may chu ve, va so 5 bien mat khong mot loi bao. Bam Luu
     thi may noi "Chua sua dong nao" - dung theo cach may nhin, vi that su
     khong con dong nao mang dau da sua.

     Tu nay du lieu tren man la CUA NGUOI DANG GO. Chi hoi lai may chu o ba
     luc: mo phieu lan dau, sau khi luu xong, va sau khi go duyet o may chu. */
  var dungLai = !!(giuMan && dyD && dyD.name === name && dyD.head);
  var d;
  if (dungLai) {
    d = dyD.head;
  } else {
    frame('Duyệt yêu cầu mua', '<div class="emp"><div class="e1">⏳</div></div>');
    try { d = await api('vagabond.duyet_ycmh.chi_tiet', { name: name }); }
    catch (e) { frame('Duyệt yêu cầu mua', '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e)) + '</div></div>'); return; }
    dyD = {
      name: name,
      head: d,
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
  }
  vgbCss();
  var L = dyD.lines;

  function chuaDuyet(x) { return x.duyet === null || x.duyet === undefined; }
  function dangSua() { return L.filter(function (x) { return x.moi; }); }

  /* Ve lai man. Mac dinh GIU nguyen nhung gi dang go; truyen taiLai = 1 khi
     du lieu tren may chu vua doi that (luu xong, go duyet xong). */
  function veLai(taiLai) { go(function () { scrDuyetYcXem(name, !taiLai); }, true); }

  /* Dat so duyet cho mot dong. Moi duong sua so deu di qua day, de khong
     con cho nao quen dat co `moi` - chinh cai co do quyet dinh dong nao
     duoc gui len may chu. */
  function dyDat(i, so, ly) {
    var x = L[i];
    x.duyet = so;
    if (ly !== undefined) x.ly_do = ly;
    x.moi = 1;
  }
  function dyBoSua(i) {
    var x = L[i];
    x.duyet = null; x.ly_do = ''; x.moi = 0;
  }

  /* Dong nay dang duyet CAO HON so nhan vien xin.

     Anh Viet 24/08/2026: *"Cho phep nguoi co quyen duyet duoc phep chinh
     sua so luong duyet CAO HON so luong yeu cau (vi du: Quan ly yeu cau 5,
     Uyen co quyen sua thanh 6 de mua cho chan thung/don vi dong goi)."*

     Truoc do man nay chan cung tai cho go so. Bo chan roi thi phai to no
     ra cho de thay, khong thi mot cai go nham 55 thay vi 5 se lot qua ma
     khong ai biet: nhan doi mau tim, va hoi lai mot lan truoc khi luu. */
  function dyVuot(x) {
    return !chuaDuyet(x) && x.duyet > x.xin + 0.0001;
  }

  /* Nhan tren nut Luu phai noi ro dang giu bao nhieu dong chua luu. Uyen go
     xong nhin xuong day la biet may co nghe hay khong, khong phai doan. */
  function dyNhanLuu() {
    var n = dangSua().length;
    return n ? ('Lưu ' + n + ' dòng vừa duyệt' + (n === L.length ? '' : ' (còn lại giữ nguyên)')) : 'Lưu quyết định duyệt';
  }
  function dyCapNhatNutLuu() {
    var nut = document.getElementById('dySub');
    if (!nut) return;
    var n = dangSua().length;
    nut.textContent = dyNhanLuu();
    nut.className = n ? 'btn' : 'btn gh';
  }

  async function dyLuu() {
    var gui = dangSua();
    if (!gui.length) return toast('Chưa có dòng nào được điền số duyệt. Gõ số vào ô "Duyệt" hoặc bấm Duyệt đủ ở dòng cần duyệt rồi bấm lại nút này.', 6000);
    var tc = gui.filter(function (x) { return (x.duyet || 0) <= 0.0001; });
    var thieuLy = tc.filter(function (x) { return !(x.ly_do || '').trim(); });
    if (thieuLy.length) return toast('Còn ' + thieuLy.length + ' dòng từ chối chưa ghi lý do. Bấm nút Từ chối ở dòng đó để ghi lý do.', 6000);
    var vuot = gui.filter(dyVuot);
    var msg = 'Duyệt ' + gui.length + ' dòng.';
    if (tc.length) msg += ' Trong đó ' + tc.length + ' dòng bị từ chối.';
    var conLai = L.length - gui.length;
    if (conLai > 0) msg += ' ' + conLai + ' dòng chưa đụng tới vẫn nằm chờ, lưu lần này không đóng phiếu.';
    msg += ' Số lượng nhân viên đã xin vẫn giữ nguyên, không sửa và không xoá dòng nào.';
    /* Duyet vuot thi doi mot nhip xac nhan rieng, ke ro tung dong. Mot con
       so go nham (55 thay vi 5) chi lo ra o day, vi sau khi luu thi don mua
       se lay theo so duyet chu khong lay so nhan vien xin. */
    if (vuot.length) {
      msg += '\n\nDuyệt VƯỢT số nhân viên xin ở ' + vuot.length + ' dòng:\n' +
        vuot.map(function (x) {
          return '· ' + x.ten + ': xin ' + num(x.xin) + ', duyệt ' + num(x.duyet) +
            ' (+' + num(x.duyet - x.xin) + ' ' + x.dvt + ')';
        }).join('\n') +
        '\n\nPhần vượt sẽ được ghi vết kèm tên người duyệt.';
    }
    if (!await confirmSheet(vuot.length ? 'Lưu và duyệt vượt?' : 'Lưu quyết định duyệt?',
      msg, vuot.length ? 'Duyệt vượt và lưu' : 'Lưu')) return;
    busy(1);
    try {
      var r = await api('vagabond.duyet_ycmh.duyet_dong', {
        name: name,
        dong: JSON.stringify(gui.map(function (x) {
          return { dong: x.dong, sl_duyet: x.duyet, ly_do_duyet: x.ly_do };
        }))
      });
      busy(0);
      toast('Đã lưu: ' + r.duyet_du + ' duyệt đủ, ' + r.cat_bot + ' cắt bớt, ' + r.tu_choi + ' từ chối' +
        (r.duyet_them ? ', ' + r.duyet_them + ' duyệt vượt' : '') + '.', 5000);
      return veLai(1);
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

  /* Dem tren dau phieu doc tu DANH SACH DANG THAY, khong doc con so may chu
     tra ve luc mo phieu: hai con so lech nhau thi nguoi dung tin cai nao. */
  var conCho = L.filter(chuaDuyet).length;
  var daTuChoi = L.filter(function (x) { return !chuaDuyet(x) && x.duyet <= 0.0001; }).length;
  var soDangSua = dangSua().length;

  var html = '<div class="card" style="padding:12px 14px;line-height:1.7">' +
    '<b style="font-size:15px">' + h(d.bo_phan || d.nguoi_yeu_cau || d.name) + '</b>' +
    '<div style="font-size:12.5px;color:#6b7280">' + h(d.name) + ' · lập ' + ngayNgan(d.ngay) +
    (d.can_ngay ? ' · cần ' + ngayNgan(d.can_ngay) : '') + '</div>' +
    '<div style="font-size:13px;margin-top:6px">Người yêu cầu <b>' + h(d.nguoi_yeu_cau) + '</b></div>' +
    '<div style="font-size:13px">' + (conCho ? '<b style="color:#b45309">' + conCho + ' dòng chờ duyệt</b>' : '<b style="color:#0f766e">Đã duyệt hết</b>') +
    (daTuChoi ? ' · ' + daTuChoi + ' dòng từ chối' : '') + '</div></div>';

  if (soDangSua) {
    html += '<div style="margin:0 12px 10px;padding:10px 12px;border-radius:11px;background:#e7f8ef;' +
      'border:1.5px solid #a7e3c0;color:#0f7a44;font-size:12.5px;line-height:1.55">' +
      '✍️ Đang giữ <b>' + soDangSua + ' dòng</b> chưa lưu. Duyệt tiếp các dòng khác rồi bấm nút xanh dưới cùng một lần là xong.</div>';
  }

  html += '<div class="rcvh">Số nhân viên xin nằm bên trái và <b>không sửa được</b>. Thu mua chỉ điền ô "Duyệt" bên phải. Duyệt 0 là từ chối và phải ghi lý do. <b>Không cần duyệt hết cả phiếu</b>: duyệt được dòng nào lưu dòng đó, dòng còn lại vẫn nằm chờ.</div>';

  html += '<div class="sec">' + L.length + ' mặt hàng</div>';
  html += L.map(function (x, i) {
    var chua = chuaDuyet(x);
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
        (tuChoi ? '#c0392b' : dyVuot(x) ? '#6d28d9' : (x.duyet < x.xin - 0.0001 ? '#c77700' : '#1f9254')) + '">' +
        (tuChoi ? 'Từ chối'
          : dyVuot(x) ? 'Duyệt vượt ' + num(x.duyet) + '/' + num(x.xin)
          : (x.duyet < x.xin - 0.0001 ? 'Duyệt ' + num(x.duyet) + '/' + num(x.xin) : 'Duyệt đủ')) +
        (x.moi ? ' · chưa lưu' : '') +
        '</div>') +
      '</div></div>' +
      dyBaSo(x) + dyCanhBao(x) +
      '<div class="qw"><div style="flex:1;min-width:0">' +
      '<div class="lb">Nhân viên xin <b>' + num(x.xin) + ' ' + h(x.dvt) + '</b> · thu mua duyệt</div>' +
      '<div class="qr"><div class="stp"><button data-dm="' + i + '">&minus;</button>' +
      '<input type="number" inputmode="decimal" step="any" data-dq="' + i + '" placeholder="chưa duyệt" value="' + (chua ? '' : x.duyet) + '"' +
      (x.moi ? ' style="background:#eafaf1;font-weight:800"' : '') + '>' +
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
    footer:
      (conCho
        ? '<button class="btn gh" id="dyHet" style="margin:0 0 9px">✅ Duyệt đủ ' + conCho + ' món chưa ai đụng tới</button>'
        : '') +
      '<button class="' + (soDangSua ? 'btn' : 'btn gh') + '" id="dySub" style="margin:0">' + dyNhanLuu() + '</button>'
  });

  b.onclick = async function (e) {
    var t, i;
    if ((t = e.target.closest('[data-ddu]'))) { i = +t.dataset.ddu; dyDat(i, L[i].xin, ''); return veLai(); }
    if ((t = e.target.closest('[data-dnua]'))) { i = +t.dataset.dnua; dyDat(i, dySo(L[i].xin / 2)); return veLai(); }
    if ((t = e.target.closest('[data-dtc]'))) {
      i = +t.dataset.dtc;
      if (!await dyHoiLyDo(i)) return;
      dyDat(i, 0); return veLai();
    }
    if ((t = e.target.closest('[data-dm]'))) { i = +t.dataset.dm; dyDat(i, Math.max(0, dySo((L[i].duyet || 0) - 1))); return veLai(); }
    if ((t = e.target.closest('[data-da2]'))) {
      i = +t.dataset.da2;
      var v = dySo((L[i].duyet || 0) + 1);
      dyDat(i, v); return veLai();
    }
    if ((t = e.target.closest('[data-dgo]'))) {
      i = +t.dataset.dgo;
      var x = L[i];
      if (!x.moi) {
        if (!await confirmSheet('Gỡ duyệt "' + x.ten + '"?', 'Dòng này trở về trạng thái chưa ai duyệt. Không xoá gì, việc gỡ vẫn được ghi vết.', 'Gỡ duyệt')) return;
        busy(1);
        try { await api('vagabond.duyet_ycmh.bo_duyet', { name: name, dong_ten: x.dong }); busy(0); toast('Đã gỡ duyệt'); return veLai(1); }
        catch (e2) { busy(0); return toast(errMsg(e2), 6000); }
      }
      dyBoSua(i); return veLai();
    }
  };

  /* O nhap so: cap nhat NGAY khi go (oninput), va TUYET DOI khong ve lai
     man o buoc roi o (onchange).

     Vi sao khong ve lai: tren dien thoai, cham vao nut Luu lam o nhap mat
     tieu diem truoc, onchange chay truoc, DOM bi thay moi, va cu cham roi
     vao khoang khong - nut Luu coi nhu khong bam duoc. Uyen gap dung canh
     do ngay 21/08/2026. Nen o day chi sua so trong bo nho va to lai chinh
     o do cung nhan nut Luu, khong dung den phan con lai cua man. */
  Array.prototype.forEach.call(b.querySelectorAll('[data-dq]'), function (el) {
    function toO(co) {
      el.style.background = co ? '#eafaf1' : '';
      el.style.fontWeight = co ? '800' : '';
    }
    el.oninput = function () {
      var i = +el.dataset.dq;
      if (el.value === '') { dyBoSua(i); toO(0); return dyCapNhatNutLuu(); }
      var v = parseFloat(el.value);
      if (isNaN(v)) return;
      dyDat(i, Math.max(0, dySo(v)));
      toO(1); dyCapNhatNutLuu();
    };
    el.onchange = function () {
      var i = +el.dataset.dq;
      if (el.value === '') { dyBoSua(i); toO(0); return dyCapNhatNutLuu(); }
      var v = Math.max(0, dySo(parseFloat(el.value) || 0));
      /* Cho vuot, nhung nhac ngay tai cho. KHONG mo hop thoai o day: tren
         dien thoai, cham vao nut Luu lam o nhap mat tieu diem truoc,
         onchange chay truoc, va hop thoai cuop mat cu cham - dung canh
         Uyen gap ngay 21/08/2026. Hoi xac nhan de o buoc Luu. */
      if (v > L[i].xin + 0.0001) {
        toast('Đang duyệt vượt: nhân viên xin ' + num(L[i].xin) + ' ' + L[i].dvt +
          ', đang để ' + num(v) + '. Kiểm lại trước khi lưu.', 5500);
      }
      dyDat(i, v); toO(1); dyCapNhatNutLuu();
    };
  });

  var sb = document.getElementById('dySub');
  if (sb) sb.onclick = dyLuu;

  var hb = document.getElementById('dyHet');
  if (hb) hb.onclick = async function () {
    /* Con dong dang go dở thì lưu trước rồi mới duyệt phần còn lại: máy chủ
       chỉ nhìn những dòng CHƯA có người duyệt, không biết gì về các ô đang
       sửa trên màn. Trước đây chỗ này chỉ báo lỗi bắt người dùng tự bấm
       Lưu, nay làm hộ luôn cho đỡ một nhịp. */
    var sua = dangSua();
    if (sua.length) {
      var thieu = sua.filter(function (x) { return (x.duyet || 0) <= 0.0001 && !(x.ly_do || '').trim(); });
      if (thieu.length) return toast('Còn ' + thieu.length + ' dòng từ chối chưa ghi lý do. Vui lòng ghi lý do rồi bấm lại.', 6000);
      if (!await confirmSheet('Lưu ' + sua.length + ' dòng đang sửa trước?',
        'Máy sẽ lưu ' + sua.length + ' dòng anh chị vừa điền, rồi mới duyệt đủ các món chưa ai đụng tới.', 'Lưu rồi duyệt hết')) return;
      busy(1);
      try {
        await api('vagabond.duyet_ycmh.duyet_dong', {
          name: name,
          dong: JSON.stringify(sua.map(function (x) {
            return { dong: x.dong, sl_duyet: x.duyet, ly_do_duyet: x.ly_do };
          }))
        });
      } catch (e0) { busy(0); return toast(errMsg(e0), 7000); }
      busy(0);
    }
    var conHang = L.filter(function (x) {
      return chuaDuyet(x) && !x.moi && x.ton > 0.0001;
    }).length;
    var msg = 'Duyệt đủ các món chưa ai đụng tới, đúng bằng số nhân viên đã xin.\n\n' +
      'Món đã từ chối hoặc đã cắt bớt giữ nguyên, nút này không đụng tới.';
    if (conHang) {
      msg += '\n\nLưu ý: trong đó có ' + conHang + ' món kho tổng vẫn còn hàng (dòng tô xanh). ' +
        'Xem lại mấy dòng đó trước khi duyệt hết.';
    }
    if (!await confirmSheet('Duyệt tất cả các món còn lại?', msg, 'Duyệt hết')) return veLai(1);
    busy(1);
    try {
      var r = await api('vagabond.duyet_ycmh.duyet_het', { name: name });
      busy(0);
      toast(r.da_duyet ? ('Đã duyệt đủ ' + r.da_duyet + ' món.') : 'Không còn món nào chưa duyệt.', 4500);
      return veLai(1);
    } catch (e) { busy(0); toast(errMsg(e), 7000); }
  };
}

/* ---------------- Tao nha cung cap (anh Viet giao 21/08/2026)

   Uyen vap hai chuyen khi thu tao NCC tren app: khong co quyen Tao, va form
   chung cua khung danh muc chi co bon o. Bon o do du de sinh mot cai ten
   trong danh sach, nhung thieu dung nhung thu lam viec duoc: email de gui
   don mua hang, so tai khoan de lap ho so thanh toan, dia chi de len hoa
   don.

   Man nay xep theo dung thu tu tay nguoi lam: go MA SO THUE truoc, may tra
   cuu va dien ho ten voi dia chi, roi moi toi lien he va tai khoan. Tra
   cuu chi DIEN VAO O; nguoi dung van nhin thay va sua duoc truoc khi Luu.

   Tien to ncc = nha cung cap. Da kiem va cham ten truoc khi dat (QT-28). */

var nccF = null, nccDm = null;
/* Man tao nha cung cap duoc goi tu NHIEU cho: man Mua hang, va cac man lap
   ho so thanh toan khi go mai khong ra ten. `nccXongThi` la cho de man goi
   cai lai mot viec phai lam sau khi luu xong - thuong la quay ve dung man
   cu voi nha cung cap vua tao da duoc chon san.
   Anh Viet 21/08/2026: chi Dung lap phieu dong BHXH ma khong tim ra ben
   BHXH, vi ca tiem chua co ho so nha cung cap nao ten nhu vay va man do
   khong co duong tao moi. */
var nccXongThi = null;

function nccTaoNhanh(goiY, xong) {
  /* Mo man tao nha cung cap, dien san cai ten nguoi ta vua go tim.
     Go "bao hiem xa hoi" khong ra gi ma bam tao moi thi o Ten phai co san
     chu do, khong bat go lai lan nua. */
  nccF = nccOMoi();
  var g = String(goiY || '').trim();
  if (g) nccF.ten = g;
  nccXongThi = xong || null;
  go(scrNccTao);
}

function nccOMoi() {
  return {
    mst: '', ten: '', nhom: '', loai: 'Company', dia_chi: '', tinh: '',
    nguoi_lien_he: '', email: '', email_cc: '', email_cc2: '', email_cc3: '',
    dien_thoai: '', so_tk: '', ngan_hang: '', chu_tk: '', tra_xong: 0
  };
}

function nccDoc() {
  if (!nccF) return;
  [['nccMst', 'mst'], ['nccTen', 'ten'], ['nccNhom', 'nhom'], ['nccLoai', 'loai'],
   ['nccDiaChi', 'dia_chi'], ['nccNguoi', 'nguoi_lien_he'], ['nccEmail', 'email'],
   ['nccCc1', 'email_cc'], ['nccCc2', 'email_cc2'], ['nccCc3', 'email_cc3'],
   ['nccDt', 'dien_thoai'], ['nccStk', 'so_tk'], ['nccNh', 'ngan_hang'],
   ['nccChuTk', 'chu_tk']].forEach(function (c) {
    var o = document.getElementById(c[0]);
    if (o) nccF[c[1]] = o.value;
  });
}

async function scrNccTao() {
  if (!nccF) nccF = nccOMoi();
  if (!nccDm) {
    frame('Tạo nhà cung cấp', '<div class="emp"><div class="e1">⏳</div></div>');
    try { nccDm = await api('vagabond.nha_cung_cap.danh_muc', {}); }
    catch (e) {
      frame('Tạo nhà cung cấp', '<div class="emp"><div class="e1">🔒</div><div>' + h(errMsg(e)) + '</div></div>');
      return;
    }
  }
  vgbCss();
  var f = nccF;

  function o(id, nhan, gt, kieu, mo_ta, bat_buoc) {
    return '<div style="margin-bottom:11px">' +
      '<div style="font-size:12.5px;color:#6b7280;margin-bottom:5px">' + nhan +
      (bat_buoc ? ' <span style="color:#b3261e">*</span>' : '') + '</div>' +
      '<input class="tin" id="' + id + '" value="' + h(gt || '') + '"' +
      (kieu ? ' type="' + kieu + '"' : '') +
      (kieu === 'tel' ? ' inputmode="tel"' : '') +
      ' style="text-align:left;font-size:15px;font-weight:600;padding:0 13px">' +
      (mo_ta ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:4px;line-height:1.5">' + mo_ta + '</div>' : '') +
      '</div>';
  }

  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">BƯỚC 1 · ĐỊNH DANH</div>' +
    '<div style="font-size:12.5px;color:#374151;line-height:1.6;margin:4px 0 11px">' +
    'Gõ <b>mã số thuế</b> rồi chạm ra ngoài, máy tự tra cứu và điền hộ tên với địa chỉ. ' +
    'Nhà cung cấp là cá nhân, không có mã số thuế thì bỏ trống ô này và gõ tên tay.</div>' +
    o('nccMst', 'Mã số thuế', f.mst, '', 'Tra cứu qua cổng thông tin doanh nghiệp. Chi nhánh 13 số nhớ giữ nguyên dấu gạch.') +
    '<div id="nccMstKq" style="font-size:12.5px;margin:-4px 0 10px;line-height:1.55"></div>' +
    o('nccTen', 'Tên nhà cung cấp', f.ten, '', '', 1) +
    '<div style="margin-bottom:11px"><div style="font-size:12.5px;color:#6b7280;margin-bottom:5px">Nhóm nhà cung cấp <span style="color:#b3261e">*</span></div>' +
    '<select class="tin" id="nccNhom" style="text-align:left;font-size:15px;font-weight:600;padding:0 13px">' +
    '<option value="">- Chọn nhóm -</option>' +
    (nccDm.nhom || []).map(function (n) {
      return '<option value="' + h(n) + '"' + (f.nhom === n ? ' selected' : '') + '>' + h(n) + '</option>';
    }).join('') + '</select></div>' +
    '<div><div style="font-size:12.5px;color:#6b7280;margin-bottom:5px">Loại</div>' +
    '<select class="tin" id="nccLoai" style="text-align:left;font-size:15px;font-weight:600;padding:0 13px">' +
    '<option value="Company"' + (f.loai === 'Company' ? ' selected' : '') + '>Công ty</option>' +
    '<option value="Individual"' + (f.loai === 'Individual' ? ' selected' : '') + '>Cá nhân</option>' +
    '</select></div></div>';

  html += '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">BƯỚC 2 · LIÊN HỆ</div>' +
    '<div style="font-size:12.5px;color:#374151;line-height:1.6;margin:4px 0 11px">' +
    'Có email thì đơn mua hàng gửi thẳng vào đó. Nhà cung cấp chỉ đặt qua app hay sàn thương mại điện tử ' +
    'thì bỏ trống ô email cũng lưu được, lúc đó mình tự đặt hàng rồi vào đánh dấu đã gửi.</div>' +
    o('nccDiaChi', 'Địa chỉ', f.dia_chi, '', 'Địa chỉ ghi trên hoá đơn.') +
    o('nccNguoi', 'Người đại diện / liên hệ', f.nguoi_lien_he, '', 'Người mình gọi khi cần giục hàng hoặc đối chiếu công nợ.') +
    o('nccEmail', 'Email nhận đơn mua hàng', f.email, 'email', 'Bỏ trống nếu nhà cung cấp này không nhận đơn qua email.') +
    '<div style="border-top:1px dashed #e5e7eb;margin:2px 0 11px;padding-top:11px">' +
    '<div style="font-size:12.5px;color:#374151;font-weight:600;margin-bottom:4px">Các email phụ cần CC</div>' +
    '<div style="font-size:11.5px;color:#98a2b3;margin-bottom:9px;line-height:1.5">' +
    'Có nhà cung cấp muốn gửi cùng lúc cho kế toán và kho của họ. Điền vào đây thì mỗi lần gửi ' +
    'đơn mua hàng máy tự CC thêm, khỏi nhớ.</div>' +
    o('nccCc1', 'Email CC 1', f.email_cc, 'email') +
    o('nccCc2', 'Email CC 2', f.email_cc2, 'email') +
    o('nccCc3', 'Email CC 3', f.email_cc3, 'email') + '</div>' +
    o('nccDt', 'Số điện thoại', f.dien_thoai, 'tel') + '</div>';

  html += '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">BƯỚC 3 · THANH TOÁN</div>' +
    '<div style="font-size:12.5px;color:#374151;line-height:1.6;margin:4px 0 11px">' +
    'Điền sẵn thì lúc lập hồ sơ thanh toán máy tự đổ số tài khoản ra, kế toán khỏi gõ tay từng lần.</div>' +
    o('nccStk', 'Số tài khoản', f.so_tk, '') +
    '<div style="margin-bottom:11px"><div style="font-size:12.5px;color:#6b7280;margin-bottom:5px">Ngân hàng</div>' +
    '<input class="tin" id="nccNh" list="nccNhList" value="' + h(f.ngan_hang || '') + '" ' +
    'placeholder="Gõ vài chữ rồi chọn trong danh sách" ' +
    'style="text-align:left;font-size:15px;font-weight:600;padding:0 13px">' +
    '<datalist id="nccNhList">' +
    (nccDm.ngan_hang || []).map(function (n) { return '<option value="' + h(n) + '"></option>'; }).join('') +
    '</datalist>' +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:4px;line-height:1.5">Chọn đúng tên trong danh sách thì đối soát sao kê mới khớp được.</div></div>' +
    o('nccChuTk', 'Chủ tài khoản', f.chu_tk, '', 'Tên in trên thẻ hoặc trên sao kê, thường viết hoa không dấu.') + '</div>';

  var b = frame('Tạo nhà cung cấp', html, {
    footer: '<button class="btn" id="nccLuu" style="margin:0">Lưu hồ sơ nhà cung cấp</button>'
  });

  /* Khoa mem mot o nhap: khong sua duoc, nhung nhin ra ngay la may dien ho.
   Dung readOnly chu khong dung disabled - disabled thi trinh duyet khong
   gui gia tri o do di, ma ham nccDoc() ben duoi doc thang tu DOM. */
function nccKhoaO(cac) {
  (cac || []).forEach(function (o) {
    if (!o) return;
    o.readOnly = true;
    o.dataset.khoa = '1';
    o.style.background = '#f0fdf4';
    o.style.borderColor = '#86efac';
    o.style.color = '#166534';
  });
}

function nccMoO(cac) {
  (cac || []).forEach(function (o) {
    if (!o) return;
    o.readOnly = false;
    delete o.dataset.khoa;
    o.style.background = '';
    o.style.borderColor = '';
    o.style.color = '';
    o.focus();
  });
}

/* Tra cuu ma so thue khi roi o. Chi dien vao nhung o DANG TRONG: nguoi
     dung da go tay ten rieng cho de nho thi may khong duoc de len. */
  var mo = document.getElementById('nccMst');
  if (mo) mo.onblur = async function () {
    var so = (mo.value || '').trim();
    var kq = document.getElementById('nccMstKq');
    if (!so) { if (kq) kq.innerHTML = ''; return; }
    if (kq) kq.innerHTML = '<span style="color:#6b7280">Đang tra cứu ' + h(so) + '...</span>';
    var r;
    try { r = await api('vagabond.api.tra_mst', { mst: so }); }
    catch (e) { r = null; }
    nccDoc();
    if (!r || !r.ok) {
      if (kq) kq.innerHTML = '<span style="color:#b45309">Không tra ra mã số thuế này. ' +
        'Hộ kinh doanh và cá nhân thường không có trên cổng, anh chị vui lòng gõ tên tay.</span>';
      return;
    }
    var oTen = document.getElementById('nccTen');
    var oDc = document.getElementById('nccDiaChi');
    var da = [];
    if (oTen && !(oTen.value || '').trim()) { oTen.value = r.ten || ''; nccF.ten = oTen.value; da.push('tên'); }
    if (oDc && !(oDc.value || '').trim() && r.dia_chi) { oDc.value = r.dia_chi; nccF.dia_chi = r.dia_chi; da.push('địa chỉ'); }
    /* Anh Viet 21/08/2026: o nao may lay tu cong thue thi KHOA lai, kem dau
       tich xanh, de khoi ai sua bay thanh mot cai ten khong khop hoa don.

       Nhung khoa cung thi co ngay ket: cong thue tra ten viet tat hoac ten
       cu, ma nguoi dung khong sua duoc thi ho bo luon man nay. Nen khoa MEM:
       khoa san, va co nut "Sua tay" ngay canh de mo ra. */
    if (da.length) nccKhoaO([oTen, oDc]);
    if (kq) {
      kq.innerHTML = '<span style="color:#0f7a44;font-weight:700">✓ ' + h(r.ten || '') + '</span>' +
        (da.length
          ? '<span style="color:#6b7280"> · máy lấy từ cổng thuế và đã khoá ' + da.join(' và ') +
            '. <a href="#" id="nccMoKhoa" style="color:#0f766e;font-weight:700">Sửa tay</a></span>'
          : '<span style="color:#6b7280"> · giữ nguyên những ô anh chị đã gõ</span>');
    }
    var mk = document.getElementById('nccMoKhoa');
    if (mk) mk.onclick = function (ev) {
      ev.preventDefault();
      nccMoO([oTen, oDc]);
      var k2 = document.getElementById('nccMstKq');
      if (k2) k2.innerHTML = '<span style="color:#b45309">Đang sửa tay. ' +
        'Tên khác với cổng thuế thì hoá đơn điện tử có thể bị từ chối.</span>';
    };
  };

  var lb = document.getElementById('nccLuu');
  if (lb) lb.onclick = async function () {
    nccDoc();
    var f2 = nccF;
    if (!(f2.ten || '').trim()) return toast('Chưa có tên nhà cung cấp. Gõ mã số thuế để máy điền hộ, hoặc gõ tên tay.', 5000);
    if (!(f2.nhom || '').trim()) return toast('Chưa chọn nhóm nhà cung cấp.', 4500);
    if (!await confirmSheet('Lưu hồ sơ nhà cung cấp?',
      'Máy sẽ lập hồ sơ "' + f2.ten + '" kèm địa chỉ, người liên hệ và số tài khoản trong một lần.', 'Lưu')) return;
    busy(1);
    var r;
    try { r = await api('vagabond.nha_cung_cap.tao', f2); }
    catch (e) { busy(0); return toast(errMsg(e), 7000); }
    busy(0);
    toast((r && r.ghi_chu) || 'Đã lập hồ sơ nhà cung cấp.', 6000);
    nccF = null;
    /* Co man nao dang doi khong. Lay ra roi XOA NGAY: khong de lai cai bay
       cho lan sau ai do mo man tao tu man Mua hang lai bi nem di cho khac. */
    var cb = nccXongThi;
    nccXongThi = null;
    if (cb) return cb((r && r.ma) || '', (r && r.ten) || f2.ten);
    back();
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
        (d.da_sua ? ' · <b style="color:#92400e">✏️ đã sửa</b>' : '') + '</div>' +
        /* Nguoi ban ngay tren dong danh sach. Anh Viet chot 02/09/2026:
           moi man hoa don phai thay duoc ai ban to nay. May chu tra ve TEN
           chu khong tra dia chi thu, xem `vagabond/ten_nguoi.py`. */
        '<div style="font-size:12px;color:#0f766e;margin-top:2px">Người bán: <b>' +
        h(d.owner_ten || d.owner || 'chưa rõ') + '</b>' +
        (d.vgb_huy && d.vgb_huy_boi_ten
          ? ' · <span style="color:#b3261e">huỷ bởi ' + h(d.vgb_huy_boi_ten) + '</span>' : '') +
        '</div></div>' +
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
    ten_ban: '', dia_chi_ban: '', ghi_chu: '', tep: []
  };
}

/* Mã ô tải tệp của một khoản chi. Lấy theo id của khoản chứ không theo số
   thứ tự: xoá khoản giữa bảng thì số thứ tự nhảy, mà tệp thì không được
   nhảy theo. */
function dncOTep(k) { return 'dnc-' + k.id; }

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
  /* Đọc qua soTien: giá trị trong ô nay có dấu chấm ("2.000.000"), đọc
     thẳng bằng Number là ra NaN và phiếu lưu xuống số 0 mà không báo gì. */
  return ((f && f.cac_khoan) || []).reduce(function (t, k) {
    return t + soTien(k.so_tien);
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
    /* Tệp không nằm trong ô input nào nên không đọc bằng g(). Lấy thẳng từ
       kho của ô tải tệp, là nơi duy nhất biết tệp nào đã lên máy chủ. */
    k.tep = tdkDs(dncOTep(k));
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
    /* kieu 'tien' = ô tiền: KHÔNG dùng type="number" được, vì trình duyệt
       coi "2.000.000" là không hợp lệ và trả về chuỗi rỗng. Dùng text cộng
       inputmode numeric thì bàn phím số vẫn bật mà giá trị vẫn đọc được. */
    var laTien = kieu === 'tien';
    return '<div style="flex:1;min-width:0">' +
      '<div style="font-size:11.5px;color:#6b7280;margin-bottom:3px">' + h(nhan) + '</div>' +
      '<input class="tin' + (laTien ? ' tien' : '') + '" id="dnk_' + id + '_' + k.id + '"' +
      (laTien ? ' inputmode="numeric"' : (kieu ? ' type="' + kieu + '"' : '')) +
      (kieu === 'number' ? ' inputmode="numeric"' : '') +
      (gy ? ' placeholder="' + h(gy) + '"' : '') +
      ' value="' + h(laTien ? tienChuoi(gtri) : (gtri || '')) + '"></div>';
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
  html += '<div style="display:flex;gap:8px;margin-bottom:9px">' + o('so_tien', 'Số tiền (đ)', k.so_tien, 'tien') + '</div>';

  html += '<button class="dncPl" data-kid="' + h(k.id) + '" style="width:100%;text-align:left;border:1.5px solid ' +
    (k.phan_loai ? '#0f766e' : '#e5e7eb') + ';background:#fff;border-radius:11px;padding:11px 13px;font-size:14px;' +
    'color:' + (k.phan_loai ? '#0f172a' : '#9ca3af') + ';font-weight:' + (k.phan_loai ? '600' : '400') + ';margin-bottom:8px">' +
    (k.phan_loai ? h(k.phan_loai) : 'Chọn phân loại chi phí') + '</button>';

  html += '<button class="dncCt" data-kid="' + h(k.id) + '" style="width:100%;text-align:left;border:1.5px solid ' +
    (k.loai_chung_tu ? '#0f766e' : '#e5e7eb') + ';background:#fff;border-radius:11px;padding:11px 13px;font-size:14px;' +
    'color:' + (k.loai_chung_tu ? '#0f172a' : '#9ca3af') + ';font-weight:' + (k.loai_chung_tu ? '600' : '400') + '">' +
    (k.loai_chung_tu ? h(k.loai_chung_tu) : 'Chọn loại chứng từ đính kèm') + '</button>';

  /* Ô đính kèm của RIÊNG khoản này. Đặt ngay dưới nút chọn loại chứng từ vì
     đó là nơi người lập vừa nói mình có tờ gì trong tay - hỏi ảnh ngay lúc đó
     là đúng nhịp nghĩ. Loại chứng từ mang cờ "bắt buộc tệp" thì viền đổi đỏ
     khi chưa có tệp nào. */
  tdkNap(dncOTep(k), k.tep || []);
  var thieuTep = ct.bat_buoc_tep && !(k.tep || []).length;
  html += '<div style="margin-top:10px;padding-top:10px;border-top:1px dashed #e5e7eb' +
    (thieuTep ? ';border-left:3px solid #dc2626;padding-left:9px;margin-left:-9px' : '') + '">' +
    tdkKhoi(dncOTep(k), {
      style: 'margin:0',
      tieu_de: 'CHỨNG TỪ VÀ HÀNG HOÁ CỦA KHOẢN NÀY' + (ct.bat_buoc_tep ? ' · BẮT BUỘC' : ''),
      nhan: '📎 Chụp hoặc chọn tệp',
      goi_y: (ct.bat_buoc_tep
        ? 'Loại chứng từ này bắt buộc có tệp thì mới gửi duyệt được. '
        : '') +
        'Đính được nhiều tệp một lượt, cả ảnh lẫn PDF. Ảnh tự thu nhỏ ngay trên máy anh chị trước khi gửi.'
    }) + '</div>';

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

  /* Nối sự kiện cho từng ô tải tệp. Phải nối SAU khi khung đã vẽ xong, và
     nối cho từng khoản một vì mỗi khoản là một ô riêng. */
  (dncForm.cac_khoan || []).forEach(function (k) {
    var ct2 = dncCoCT(k.loai_chung_tu);
    tdkNoi(b, dncOTep(k), {
      style: 'margin:0',
      tieu_de: 'CHỨNG TỪ VÀ HÀNG HOÁ CỦA KHOẢN NÀY' + (ct2.bat_buoc_tep ? ' · BẮT BUỘC' : ''),
      nhan: '📎 Chụp hoặc chọn tệp',
      goi_y: (ct2.bat_buoc_tep
        ? 'Loại chứng từ này bắt buộc có tệp thì mới gửi duyệt được. '
        : '') +
        'Đính được nhiều tệp một lượt, cả ảnh lẫn PDF. Ảnh tự thu nhỏ ngay trên máy anh chị trước khi gửi.',
      khi_doi: function () { dncDoc(); }
    });
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
      return baoTin('Một phiếu tối đa 200 khoản. Anh chị vui lòng tách ra làm nhiều phiếu.');
    }
    dncForm.cac_khoan.push(dncKhoanMoi());
    dncVe(lichSu);
  };

  b.querySelectorAll('.dncXoa').forEach(function (n) {
    n.onclick = async function () {
      dncDoc();
      var kid = n.getAttribute('data-kid');
      var k = (dncForm.cac_khoan || []).filter(function (x) { return x.id === kid; })[0];
      if (k && ((k.noi_dung || '').trim() || soTien(k.so_tien) > 0)) {
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
        'Nếu khoản này không phải hoàn ứng thì đổi Loại nghiệp vụ sang Chi phí.', 'Chưa có tạm ứng');
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
      if (!(soTien(k.so_tien) > 0)) thieu.push(stt + ': chưa nhập số tiền');
      if (!k.phan_loai) thieu.push(stt + ': chưa chọn phân loại');
      if (!k.loai_chung_tu) thieu.push(stt + ': chưa chọn loại chứng từ');
      if (dncCoCT(k.loai_chung_tu).la_hoa_don_vat) {
        if (!(k.so_hoa_don || '').trim()) thieu.push(stt + ': thiếu số hoá đơn');
        if (!k.ngay_hoa_don) thieu.push(stt + ': thiếu ngày hoá đơn');
        if (!(k.mst || '').trim()) thieu.push(stt + ': thiếu mã số thuế người bán');
      }
      if (dncCoCT(k.loai_chung_tu).bat_buoc_tep && !(k.tep || []).length) {
        thieu.push(stt + ': loại chứng từ này bắt buộc đính kèm tệp');
      }
    });
    /* Gửi duyệt thì cả phiếu phải có ít nhất một tấm ảnh. Máy chủ cũng chặn
       câu này, nhưng nó chặn SAU khi phiếu đã lưu, nên bắt ở đây thì anh chị
       không bị đẻ ra một phiếu nháp thừa mỗi lần quên ảnh. */
    if (gui && !thieu.length) {
      var coAnh = (f2.cac_khoan || []).some(function (k) { return (k.tep || []).length; });
      if (!coAnh) {
        return baoTin('Phải đính kèm ít nhất một ảnh bill, hoá đơn hoặc ảnh hàng hoá ' +
          'thì kế toán mới duyệt được. Ô đính kèm nằm ngay trong từng khoản chi.',
          'Chưa có chứng từ');
      }
    }
    if (thieu.length) return baoTin(thieu.join('\n'), 'Còn thiếu');
    busy(true);
    try {
      /* Gửi lên máy chủ thì gửi SỐ, không gửi chuỗi có dấu chấm. Máy chủ
         vẫn cộng lại từ bảng kê (QT-19), nhưng gửi chuỗi lên thì flt() bên
         Python đọc "2.000.000" ra 2.0 - sai một triệu lần mà không báo. */
      var goi = JSON.parse(JSON.stringify(f2));
      (goi.cac_khoan || []).forEach(function (k) { k.so_tien = soTien(k.so_tien); });
      var r = await api('vagabond.de_nghi_chi.tao', { du_lieu: JSON.stringify(goi), gui_luon: gui ? 1 : 0 });
      busy(false);
      /* Dọn kho tệp của màn vừa lập. Giữ lại thì phiếu sau mở ra đã thấy sẵn
         ảnh của phiếu trước, mà tệp đó đã buộc vào phiếu trước rồi. */
      tdkXoaHet();
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
    if (nhac && so.length) nhac.innerHTML = 'Mã số thuế phải 10, 12 hoặc 13 số. Anh chị vui lòng kiểm lại.';
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
      : 'Chưa tra được (mạng hoặc cổng thông tin đang bận). Anh chị vui lòng gõ tay, phiếu vẫn lưu được.';
  }
}


/* ================= Danh sách phiếu thanh toán nội bộ (TTNB) =================

Anh Việt 20/08/2026: *"Bất kỳ phân hệ nào có nút Tạo phiếu thì bắt buộc phải
có màn hình Danh sách để xem lại."*

Chip trạng thái GOM chuỗi duyệt ba cấp lại cho dễ nhìn, chứ không đổi trạng
thái bên dưới: chuỗi mua hàng, giám đốc từ 2 triệu, kế toán là thứ anh Việt
chốt hôm 19/08 và đang chạy đúng. Đổi trạng thái là đổi cả chuỗi đó. */
var ttnbLoc = { chip: 'tat_ca', so_ngay: 30, tim: '' };

async function scrTTNB() {
  frame('Thanh toán nội bộ', '<div class="emp"><div class="e1">⏳</div><div>Đang mở...</div></div>');
  var kq;
  try { kq = await api('vagabond.de_nghi_chi.ds_man', ttnbLoc); }
  catch (e) {
    frame('Thanh toán nội bộ', '<div class="emp"><div class="e1">⚠️</div><div>' +
      h((e && e.message) || 'Không mở được danh sách') + '</div></div>');
    return;
  }
  ttnbVe(kq);
}

function ttnbMau(t) {
  return t === 'Da chi' ? '#065f46'
    : (t === 'Hoan tat' || t === 'Cho ke toan' ? '#0a8a4a'
      : (t === 'Bi tra lai' ? '#6b7280'
        : (t === 'Nhap' ? '#98a2b3' : '#b45309')));
}

function ttnbVe(kq) {
  var ds = kq.ds || [], dem = kq.dem || {};
  var html = '';

  html += '<div style="display:flex;gap:7px;margin-bottom:9px">' +
    '<input id="ttnbTim" value="' + h(ttnbLoc.tim) + '" placeholder="Tìm mã phiếu hoặc nội dung" ' +
    'style="flex:1;border:1.5px solid #e5e7eb;border-radius:9px;padding:9px 12px;font-size:13px">' +
    '<button id="ttnbTimNut" style="flex:none;border:1.5px solid #0f766e;background:#ccfbf1;color:#0f766e;' +
    'border-radius:9px;padding:0 14px;font-size:15px;font-weight:800">🔍</button>' +
    (ttnbLoc.tim ? '<button id="ttnbTimXoa" style="flex:none;border:1.5px solid #e5e7eb;background:#fff;' +
      'color:#6b7280;border-radius:9px;padding:0 13px;font-size:14px">✕</button>' : '') + '</div>';

  /* Chip trạng thái. Con số là số THẬT của cả sổ trong khoảng thời gian
     đang chọn, không phải số dòng đang hiện. */
  html += '<div style="display:flex;gap:7px;overflow-x:auto;padding:2px 0 8px">' +
    (kq.chip_trang_thai || []).map(function (c) {
      var on = ttnbLoc.chip === c.k;
      return '<button class="ttnbC" data-c="' + h(c.k) + '" style="flex:none;border:1.5px solid ' +
        (on ? '#0f766e' : '#e5e7eb') + ';background:' + (on ? '#ccfbf1' : '#fff') + ';color:' +
        (on ? '#0f766e' : '#374151') + ';border-radius:999px;padding:6px 13px;font-size:12.5px;font-weight:' +
        (on ? '800' : '600') + ';white-space:nowrap">' + h(c.ten) +
        (dem[c.k] !== undefined ? ' · ' + money(dem[c.k]) : '') + '</button>';
    }).join('') + '</div>';

  html += '<div style="display:flex;gap:7px;overflow-x:auto;padding:0 0 10px">' +
    (kq.chip_thoi_gian || []).map(function (c) {
      var on = String(ttnbLoc.so_ngay) === String(c.k);
      return '<button class="ttnbT" data-t="' + h(c.k) + '" style="flex:none;border:1px solid ' +
        (on ? '#0f766e' : '#e5e7eb') + ';background:' + (on ? '#f0fdfa' : '#fff') + ';color:' +
        (on ? '#0f766e' : '#6b7280') + ';border-radius:999px;padding:5px 12px;font-size:12px;font-weight:' +
        (on ? '800' : '600') + ';white-space:nowrap">' + h(c.ten) + '</button>';
    }).join('') + '</div>';

  if (!ds.length) {
    html += '<div class="emp"><div class="e1">🧾</div><div>' +
      (ttnbLoc.tim ? 'Không có phiếu nào khớp "' + h(ttnbLoc.tim) + '".' : 'Chưa có phiếu nào ở nhóm này.') +
      '</div><div style="font-size:12px;color:#9ca3af;margin-top:6px">' +
      'Bấm nút bên dưới để lập phiếu mới.</div></div>';
  } else {
    html += '<div class="card">' + ds.map(function (x) {
      return '<div class="ttnbMo" data-p="' + h(x.name) + '" style="padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
        '<div style="display:flex;align-items:center;gap:9px">' +
        '<div style="flex:1;min-width:0"><b style="font-size:14px">' + h(x.tieu_de || x.name) + '</b>' +
        '<div style="font-size:11.5px;color:#98a2b3;margin-top:2px">' + h(x.name) +
        (x.so_khoan > 1 ? ' · ' + x.so_khoan + ' khoản' : '') +
        ' · ' + h(String(x.creation || '').slice(0, 10)) + '</div></div>' +
        '<div style="text-align:right"><b style="font-size:15px">' + money(x.tien) + ' đ</b>' +
        '<div style="font-size:11px;font-weight:700;color:' + ttnbMau(x.trang_thai) + '">' +
        h(x.nhan_trang_thai || '') + '</div></div>' +
        '<div style="flex:none;color:#c9cfda;font-size:17px">›</div></div>' +
        (x.trang_thai === 'Da chi'
          ? '<div style="font-size:11.5px;color:#065f46;margin-top:5px">Tiền đã ra khỏi tài khoản' +
            (x.ngay_da_chi ? ' lúc ' + h(String(x.ngay_da_chi).slice(0, 16)) : '') +
            (x.ma_gd ? ' · ' + h(x.ma_gd) : '') + '</div>'
          : '') +
        '</div>';
    }).join('') + '</div>';
  }

  var chan = '<div style="display:flex;gap:8px">' +
    '<button class="btn" id="ttnbMoi" style="margin:0;flex:2">➕ Lập phiếu mới</button>' +
    (kq.duoc_duyet
      ? '<button class="btn gh" id="ttnbSoat" style="margin:0;flex:1">🔄 Đối soát</button>'
      : '') + '</div>';

  var b = frame('Thanh toán nội bộ', html, { footer: chan });

  var chay = function () { go(scrTTNB, true); };
  var oTim = document.getElementById('ttnbTim');
  var nTim = document.getElementById('ttnbTimNut');
  if (nTim) nTim.onclick = function () { ttnbLoc.tim = (oTim && oTim.value || '').trim(); chay(); };
  if (oTim) oTim.onkeydown = function (e) { if (e.key === 'Enter') nTim.onclick(); };
  var nXoa = document.getElementById('ttnbTimXoa');
  if (nXoa) nXoa.onclick = function () { ttnbLoc.tim = ''; chay(); };

  b.querySelectorAll('.ttnbC').forEach(function (n) {
    n.onclick = function () { ttnbLoc.chip = n.getAttribute('data-c'); chay(); };
  });
  b.querySelectorAll('.ttnbT').forEach(function (n) {
    n.onclick = function () { ttnbLoc.so_ngay = Number(n.getAttribute('data-t')); chay(); };
  });
  b.querySelectorAll('.ttnbMo').forEach(function (n) {
    n.onclick = function () { ttnbCt(n.getAttribute('data-p')); };
  });

  var nMoi = document.getElementById('ttnbMoi');
  if (nMoi) nMoi.onclick = function () { dncForm = null; go(scrDeNghiChi); };
  var nSoat = document.getElementById('ttnbSoat');
  if (nSoat) nSoat.onclick = async function () {
    busy(true);
    try {
      var r = await api('vagabond.de_nghi_chi.doi_soat', {});
      busy(false);
      var xx = r.xem_xet || [];
      var trung = xx.filter(function (y) { return y.trung_voi; });
      var lech = xx.filter(function (y) { return !y.trung_voi; });
      baoTin(r.ghi_chu ? r.ghi_chu :
        ('Đã khớp ' + money(r.da_khop || 0) + ' phiếu trên ' + money(r.so_phieu_quet || 0) + ' phiếu chờ chi.' +
         (lech.length ? '\n\nCó ' + lech.length + ' phiếu nội dung khớp nhưng SỐ TIỀN LỆCH, cần xem lại.' : '') +
         (trung.length ? '\n\nCó ' + trung.length + ' phiếu trỏ vào giao dịch đã gắn cho phiếu khác.' : '')));
      chay();
    } catch (e) { busy(false); baoTin((e && e.message) || 'Không đối soát được'); }
  };
}

/* Chi tiết một phiếu TTNB, kèm nút duyệt cho đúng người ở đúng bước. */
/* ---------- Khớp SePay cho phiếu thanh toán nội bộ (v294) ----------

Anh Việt 24/08/2026: mọi màn cần đối soát SePay đều phải có đối soát tự động
và nút thủ công ở kế bên.

Màn này là màn CẦN nút thủ công nhất trong cả hệ, mà trước v294 lại không có.
Đây là đường DUY NHẤT webhook SePay gọi thẳng: tiền về là phiếu tự nhảy sang
"Đã chi" mà không ai bấm nút nào. Nên khi kế toán gõ nội dung thiếu một chữ,
phiếu nằm mãi ở "Chờ kế toán" và không có đường nào để người nhìn sao kê rồi
chỉ đúng dòng.

Hai nút này gọi thẳng tầng chung `vagabond.doi_soat_sepay`, cùng một cửa với
màn Phiếu hoàn tiền. */
function ttnbKhopSepay(d) {
  if (!d.khop_duoc) {
    if (d.ma_gd) {
      return '<div style="font-size:12px;color:#065f46;background:#f0fdf4;border:1px solid #a7f3d0;' +
        'border-radius:9px;padding:9px 11px;margin-top:9px;line-height:1.6">' +
        'Lệnh chi đã khớp sao kê, giao dịch <b>' + h(d.ma_gd) + '</b>.</div>';
    }
    return '';
  }
  return '<button class="btn gh" id="ttnbKsAuto" style="margin:9px 0 0;width:100%">🔄 Khớp SePay</button>' +
    '<button class="btn gh" id="ttnbKsTay" style="margin:8px 0 0;width:100%">🔎 Khớp SePay thủ công</button>';
}

async function ttnbKhopAuto(d) {
  busy(true);
  var kq;
  try { kq = await api('vagabond.doi_soat_sepay.tu_dong', { loai: 'ttnb', ma_phieu: d.name, so_ngay: 45 }); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Chưa quét được sao kê.', 'Lỗi'); }
  busy(false);
  if (kq && kq.da_khop) {
    toast('Đã khớp lệnh chi, phiếu chuyển sang Đã chi.', 4500);
    return ttnbCt(d.name);
  }
  var xx = (kq && kq.xem_lai) || [];
  if (xx.length) {
    return baoTin(h(xx[0].vi_sao || '') + ' Anh chị xem lại rồi dùng nút Khớp SePay thủ công.',
      'Cần người xem');
  }
  baoTin('Chưa thấy dòng tiền ra nào mang mã "' + h(d.name) + '". Nếu tiền đã chuyển rồi ' +
    'thì bấm Khớp SePay thủ công để chọn đúng dòng.', 'Chưa khớp được');
}

async function ttnbFormGdRa(d) {
  frame('Khớp SePay thủ công', '<div class="emp"><div class="e1">⏳</div><div>Đang lọc sao kê...</div></div>');
  var kq;
  try { kq = await api('vagabond.doi_soat_sepay.ung_vien', { loai: 'ttnb', ma_phieu: d.name, so_ngay: 45 }); }
  catch (e) {
    frame('Khớp SePay thủ công', '<div class="emp"><div class="e1">⚠️</div><div>' +
      h((e && e.message) || 'Không lọc được sao kê') + '</div></div>');
    return;
  }
  var rows = (kq && kq.rows) || [];
  var html = '<div class="card" style="padding:12px 14px">' +
    '<div style="font-size:13px;font-weight:800">' + h(d.name) + ' · ' + money(d.tien) + ' đ</div>' +
    '<div style="font-size:12px;color:#6b7280;margin-top:4px;line-height:1.6">' +
    'Máy dò theo mã <b>' + h(kq.ma_do || d.name) + '</b> trong nội dung chuyển khoản.</div></div>';
  if (!rows.length) {
    html += '<div class="emp"><div class="e1">🔍</div><div class="e2">Không có dòng tiền ra ' +
      'nào còn trống trong 45 ngày qua.</div><div style="font-size:12px;color:#9ca3af;' +
      'margin-top:6px;line-height:1.6">Dòng đã được phiếu khác dùng thì không hiện ở đây, ' +
      'vì một lần tiền ra chỉ ứng với một phiếu.</div></div>';
  } else {
    html += '<div style="font-size:11.5px;color:#6b7280;padding:9px 14px 4px;line-height:1.55">' +
      'Xếp dòng khớp mã lên trước, rồi đến dòng đúng số tiền. Bấm để chọn.</div>';
    html += rows.map(function (r) {
      var vien = r.khop_ma ? '#a7f3d0' : (r.dung_tien ? '#bfdbfe' : '#e5e7eb');
      var nen = r.khop_ma ? '#f0fdf4' : (r.dung_tien ? '#eff6ff' : '#fff');
      return '<div class="ttnbgd" data-gd="' + h(r.name) + '" data-tien="' + h(String(r.tien)) + '" ' +
        'style="border:1.5px solid ' + vien + ';background:' + nen + ';border-radius:11px;' +
        'padding:10px 12px;margin:8px 12px;cursor:pointer">' +
        '<div style="display:flex;gap:8px;align-items:baseline">' +
        '<div style="flex:1;font-size:14px;font-weight:800">' + money(r.tien) + ' đ</div>' +
        '<div style="flex:none;font-size:12px;color:#6b7280">' + h(String(r.date || '').slice(0, 10)) + '</div></div>' +
        '<div style="font-size:12px;color:#374151;margin-top:3px;word-break:break-word">' +
        h(r.mo_ta || '(không có nội dung)') + '</div>' +
        '<div style="font-size:11px;color:#6b7280;margin-top:3px">' +
        (r.khop_ma ? '✅ khớp mã · ' : '') +
        (r.dung_tien ? 'đúng số tiền' : 'lệch ' + money(Math.abs(r.lech)) + ' đ') +
        '</div></div>';
    }).join('');
  }
  var b = frame('Khớp SePay thủ công', html);
  b.querySelectorAll('.ttnbgd').forEach(function (n) {
    n.onclick = function () { ttnbKhopTay(d, n.getAttribute('data-gd'), Number(n.getAttribute('data-tien') || 0)); };
  });
}

async function ttnbKhopTay(d, gd, tien) {
  var lech = Math.abs(Number(tien || 0) - Number(d.tien || 0));
  var cau = 'Gắn giao dịch ' + gd + ' (' + money(tien) + ' đ) vào phiếu ' + d.name + '.' +
    (lech > 1 ? ' Số tiền LỆCH ' + money(lech) + ' đ so với phiếu.' : '') +
    ' Máy sẽ chuyển phiếu sang Đã chi.';
  var ok = await confirmSheet('Khớp lệnh chi thủ công', cau, 'Đúng, khớp phiếu này', lech > 1);
  if (!ok) return;
  busy(true);
  try {
    var kq = await api('vagabond.de_nghi_chi.khop_tay', { phieu: d.name, gd: gd });
    busy(false);
    toast((kq && kq.nhac) || 'Đã khớp.', 5000);
    if (kq && kq.loi) baoTin(kq.loi, 'Bước sau chưa chạy xong');
  } catch (e) {
    busy(false);
    return baoTin((e && e.message) || 'Chưa khớp được.', 'Lỗi');
  }
  ttnbCt(d.name);
}

async function ttnbCt(ma) {
  frame('Phiếu thanh toán nội bộ', '<div class="emp"><div class="e1">⏳</div><div>Đang mở...</div></div>');
  var d;
  try { d = await api('vagabond.de_nghi_chi.chi_tiet', { ma_phieu: ma }); }
  catch (e) {
    frame('Phiếu thanh toán nội bộ', '<div class="emp"><div class="e1">⚠️</div><div>' +
      h((e && e.message) || 'Không mở được phiếu') + '</div></div>');
    return;
  }
  var dong = function (n, g, dam) {
    return '<div style="display:flex;gap:10px;padding:9px 0;border-bottom:1px solid #f2f4f7">' +
      '<div style="flex:0 0 40%;font-size:12px;color:#6b7280">' + h(n) + '</div>' +
      '<div style="flex:1;font-size:13.5px;' + (dam ? 'font-weight:800' : 'font-weight:600') +
      ';word-break:break-all">' + h(g === 0 || g ? String(g) : '(chưa có)') + '</div></div>';
  };
  var html = '<div class="card" style="padding:13px 14px;background:#f0fdfa;border:1.5px solid #99f6e4">' +
    '<div style="display:flex;align-items:baseline;gap:10px">' +
    '<div style="flex:1;font-size:13.5px;font-weight:700;color:#0f766e">' + h(d.name) + '</div>' +
    '<div style="font-size:20px;font-weight:800;color:#0f766e">' + money(d.tien) + ' đ</div></div>' +
    '<div style="font-size:12px;color:#0f766e;margin-top:4px">' + h(d.nhan_trang_thai || '') + '</div></div>';

  html += '<div class="sec">Bảng kê · ' + ((d.cac_khoan || []).length) + ' khoản</div><div class="card">' +
    (d.cac_khoan || []).map(function (k, i) {
      /* Chứng từ của khoản nào vẽ ngay dưới khoản đó. Dồn hết xuống chân
         phiếu thì kế toán soi một khoản phải tự đoán tấm nào của khoản nào,
         mà đoán sai là duyệt nhầm. */
      var luoi = (k.tep_hien || []).length
        ? '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:8px">' +
          k.tep_hien.map(function (t) {
            var trong = t.anh
              ? '<img src="' + h(t.url) + '" alt="' + h(t.ten) + '" loading="lazy" ' +
                'style="width:100%;height:100%;object-fit:cover;display:block">'
              : '<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;' +
                'background:#f1f5f9;color:#475569;font-size:12px;font-weight:800">' + h(t.duoi || 'TỆP') + '</div>';
            return '<div style="width:72px">' +
              '<a href="' + h(t.url) + '" target="_blank" rel="noopener" ' +
              'style="display:block;width:72px;height:72px;border-radius:9px;overflow:hidden;' +
              'border:1.5px solid #e5e7eb;background:#fff">' + trong + '</a>' +
              '<div style="font-size:10px;color:#98a2b3;margin-top:3px;line-height:1.3;' +
              'word-break:break-all;max-height:26px;overflow:hidden">' + h(t.ten || '') + '</div></div>';
          }).join('') + '</div>'
        : '';
      return '<div style="padding:11px 14px;border-bottom:1px solid #f2f4f7">' +
        '<div style="display:flex;gap:10px">' +
        '<div style="flex:1;min-width:0"><b style="font-size:13.5px">' + h(k.noi_dung || '') + '</b>' +
        '<div style="font-size:11.5px;color:#98a2b3;margin-top:2px">' + h(k.phan_loai || '') +
        (k.loai_chung_tu ? ' · ' + h(k.loai_chung_tu) : '') +
        (k.so_hoa_don ? ' · HĐ ' + h(k.so_hoa_don) : '') + '</div></div>' +
        '<div style="text-align:right;font-weight:800;font-size:13.5px">' + money(k.so_tien) + ' đ</div></div>' +
        luoi + '</div>';
    }).join('') + '</div>';

  html += '<div class="sec">Người nhận tiền</div><div class="card" style="padding:2px 14px 8px">' +
    dong('Hình thức', d.hinh_thuc || '') +
    dong('Phương thức', d.phuong_thuc || '') +
    (d.nha_cung_cap ? dong('Nhà cung cấp', d.nha_cung_cap) : '') +
    dong('Chủ tài khoản', d.ten_tk || '') +
    dong('Số tài khoản', d.so_tk || '', 1) +
    dong('Ngân hàng', d.ngan_hang || '') + '</div>';

  /* Nội dung chuyển khoản: chính chuỗi này là thứ duy nhất phép đối soát bám
     vào, nên phải bày ra thật rõ và chép được. */
  html += '<div class="sec">Đối soát ngân hàng</div><div class="card" style="padding:12px 14px">' +
    dong('Nội dung chuyển khoản', d.noi_dung_ck || '', 1) +
    (d.ma_gd ? dong('Mã giao dịch', d.ma_gd) : '') +
    (d.ngay_da_chi ? dong('Tiền ra lúc', String(d.ngay_da_chi).slice(0, 16)) : '') +
    '<button class="btn gh" id="ttnbChep" style="margin:9px 0 0;width:100%">📋 Chép nội dung chuyển khoản</button>' +
    '<div style="font-size:11.5px;color:#6b7280;margin-top:7px;line-height:1.6">' +
    'Chuyển tiền nên dán ĐÚNG nội dung này thì máy tự đổi phiếu sang ' +
    '<b>Đã chi</b> khi ngân hàng báo có. Gõ khác đi thì bấm hai nút dưới.</div>' +
    ttnbKhopSepay(d) + '</div>';

  if (d.can_tru) {
    var c = d.can_tru;
    html += '<div class="sec">Cấn trừ tạm ứng</div><div class="card" style="padding:12px 14px">' +
      dong('Đã ứng', money(c.da_ung) + ' đ') +
      dong('Đã hoàn ứng', money(c.da_hoan_ung) + ' đ') +
      '<div style="font-size:12.5px;color:#374151;background:#f8fafc;border:1px solid #e5e7eb;' +
      'border-radius:9px;padding:9px 11px;margin-top:8px;line-height:1.6">' + h(c.nhac || '') + '</div></div>';
  }

  var chan = '';
  if (d.duoc_duyet_buoc_nay) {
    chan += '<button class="btn" id="ttnbDuyet" style="margin:0;flex:2">✅ Duyệt thanh toán nội bộ</button>' +
      '<button class="btn" id="ttnbTra" style="margin:0;flex:1;background:#b3261e;border-color:#b3261e">Trả lại</button>';
  }
  var b = frame('Phiếu thanh toán nội bộ', html, chan ? { footer: '<div style="display:flex;gap:8px">' + chan + '</div>' } : undefined);

  var nKa = document.getElementById('ttnbKsAuto');
  if (nKa) nKa.onclick = function () { ttnbKhopAuto(d); };
  var nKt = document.getElementById('ttnbKsTay');
  if (nKt) nKt.onclick = function () { ttnbFormGdRa(d); };

  var nC = document.getElementById('ttnbChep');
  if (nC) nC.onclick = function () {
    var t = d.noi_dung_ck || '';
    try { navigator.clipboard.writeText(t); toast('Đã chép: ' + t, 4000); }
    catch (e) { baoTin(t, 'Vui lòng chép tay'); }
  };
  var nD = document.getElementById('ttnbDuyet');
  if (nD) nD.onclick = async function () {
    if (!await hoiCo('Duyệt thanh toán nội bộ',
      'Duyệt phiếu ' + h(d.name) + ' số tiền ' + money(d.tien) + ' đ?', 'Duyệt')) return;
    busy(true);
    try {
      var r = await api('vagabond.de_nghi_chi.duyet', { ma_phieu: d.name });
      busy(false);
      toast('Đã duyệt, phiếu chuyển sang ' + h(r.nhan_trang_thai || r.trang_thai || ''), 4500);
      ttnbCt(d.name);
    } catch (e) { busy(false); baoTin((e && e.message) || 'Không duyệt được'); }
  };
  var nT = document.getElementById('ttnbTra');
  if (nT) nT.onclick = async function () {
    var ly = await promptSheet('Trả lại phiếu', 'Ghi rõ lý do để người lập biết đường sửa');
    if (!ly) return;
    busy(true);
    try {
      await api('vagabond.de_nghi_chi.tra_lai', { ma_phieu: d.name, ly_do: ly });
      busy(false);
      toast('Đã trả phiếu về cho người lập.', 4000);
      ttnbCt(d.name);
    } catch (e) { busy(false); baoTin((e && e.message) || 'Không trả lại được'); }
  };
}

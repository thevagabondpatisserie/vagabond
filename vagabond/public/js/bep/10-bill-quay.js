/* ---------- Bill quay: in 80mm, tam tinh, danh sach bill cua quay ----------
   Anh Viet 09/08/2026: build de thay the han Fabi tinh tien. Moi quay tu
   quan bill cua minh - tu xem, tu sua, tu xoa, tu ghi so tai cho, khong di
   vong qua man Doanh thu Sales cua ai het. */
var posBillVua = null;

/* Mau in kho 80mm, in qua trinh duyet (AirPrint / may in nhiet co driver).
   Logo den tren nen trang de hop in nhiet; thieu anh thi tu an, van in chu. */
async function posInBill(d) {
  /* Quyet dinh duong in TRUOC khi goi mang de giu user gesture (khoi bi
     chan popup). In ngam thi khong mo cua so nao, khong thi mo ngay bay
     gio - xem hai nhip o 27-in-ngam.js.
     Bill that chua co link XHD thi tu xin: truoc day chi duong in lai tu
     chi tiet bill moi co QR, in ngay sau thu tien bi thieu (loi anh Viet
     bao 09/08) - gio moi duong in deu co. */
  var inW = inMoCuaSoNeuCan('hoa_don');
  if (inW === 'chan') return;
  if (!d.tam_tinh && !d.huy && d.name && !d.xhd_url) {
    try { var lk0 = await api('vagabond.ban_hang.pos_link_xhd', { name: d.name }); d.xhd_url = (lk0 && lk0.url) || ''; } catch (e0) { }
  }
  /* Diem thanh vien va ten thu ngan. Duong chot bill da co san trong d,
     duong IN LAI thi phai hoi may chu - va phai hoi that, vi ten thu ngan
     cua ban in lai la nguoi DA BAM BILL chu khong phai nguoi dang dung
     truoc may in (anh Viet 13/08/2026). */
  if (!d.tam_tinh && d.name && d.diem === undefined) {
    try {
      var th0 = await api('vagabond.ban_hang.pos_bill_them', { name: d.name });
      d.diem = (th0 && th0.diem) || null;
      if (th0 && th0.thu_ngan) d.thu_ngan = th0.thu_ngan;
    } catch (e1) { d.diem = null; }
  }
  var q = (CFGBH || {}).qr_quay || {};
  var mon = d.mon || [];
  var gio = new Date();
  var hs = function (n) { return (n < 10 ? '0' : '') + n; };
  var lucIn = hs(gio.getHours()) + ':' + hs(gio.getMinutes()) + ' ' + hs(gio.getDate()) + '/' + hs(gio.getMonth() + 1) + '/' + gio.getFullYear();
  var rows = mon.map(function (m) {
    return '<tr><td class="t">' + h(m.ten) + '</td></tr>' +
      /* Mon nao thuoc combo nao thi ghi ngay duoi ten mon: khach doc bill
         biet minh dang mua bo combo, nguoi di lay mon biet gom du bo (anh
         Viet 11/08/2026). Ma combo KHONG in, chi in ten. */
      (m.combo ? '<tr><td style="font-size:10px">&nbsp;&nbsp;&#9733; ' + h(m.combo) + '</td></tr>' : '') +
      ((m.tc || []).length ? '<tr><td style="font-size:10px">&nbsp;&nbsp;[' + h(m.tc.join(', ')) + ']</td></tr>' : '') +
      '<tr><td class="s">' + money(m.qty) + ' x ' + money(m.rate) + '<span class="r">' + money(m.qty * m.rate) + '</span></td></tr>';
  }).join('');
  var qrKhoi = '';
  if (d.tam_tinh) {
    /* Phieu tam tinh in kem QR THANH TOAN: khach xac nhan mon xong quet
       chuyen luon cung duoc, SePay khop theo ma bill. */
    var ndq = posNoiDungCk(d.bill, d.quay, d.nguon || '');
    var uq = posQrUrl(ndq, d.thu, d.nguon || '', d.quay);
    if (uq) qrKhoi = '<div class="qr"><img src="' + uq + '"><div>Quét để chuyển khoản ' + money(d.thu) + ' đ<br>Nội dung: <b>' + h(ndq) + '</b></div></div>';
  } else if (d.xhd_url) {
    /* Bill that in kem QR XUAT HOA DON: khach can hoa don cong ty thi quet,
       tu dien thong tin, ERP map vao don, cuoi ngay tu day m-invoice. */
    var ulink = location.origin + d.xhd_url;
    qrKhoi = '<div class="qr"><img src="https://api.qrserver.com/v1/create-qr-code/?size=190x190&data=' + encodeURIComponent(ulink) + '">' +
      '<div><b>Quý khách vui lòng quét mã QR (hiệu lực 2 tiếng)<br>để nhập thông tin xuất hoá đơn.</b><br>Hoá đơn điện tử gửi về email trong ngày.</div></div>';
  }
  /* MOT lenh in ra MOT lien (anh Viet 10/08/2026). Truoc day in lien
     nhau hai lien roi bat nhan vien cam keo cat giua - khong thong minh.
     Can lien thu hai thi bam In lai them mot lan, may tu ra to nua. */
  var lien2 = '';
  var inTieuDe = h(d.bill || d.name || 'Hoá đơn');
  var inToBill = ('<html><head><meta charset="utf-8"><title>' + inTieuDe + '</title><style>' +
    '@page{size:' + inKho('hoa_don').css + ';margin:0}' +
    '*{margin:0;padding:0;box-sizing:border-box}' +
    'body{width:' + inKho('hoa_don').rong + 'mm;margin:0 auto;font-family:Arial,sans-serif;font-size:11.5px;color:#000;padding:4mm 0 6mm}' +
    '.lg{display:block;width:44mm;margin:0 auto 2mm}' +
    'h1{font-size:13px;text-align:center;letter-spacing:.06em}' +
    '.ph{text-align:center;font-size:10px;line-height:1.45}' +
    '.tt{font-size:14px;font-weight:bold;text-align:center;margin:3mm 0 1mm;letter-spacing:.08em}' +
    'hr{border:0;border-top:1px dashed #000;margin:2mm 0}' +
    'table{width:100%;border-collapse:collapse}' +
    'td.t{font-weight:bold;padding-top:1.2mm}' +
    'td.s{font-size:11px;padding-bottom:.6mm}' +
    '.r{float:right;font-weight:bold}' +
    '.d{display:flex;justify-content:space-between;font-size:11.5px;padding:.4mm 0}' +
    '.d b.to{font-size:15px}' +
    '.gc{font-size:11px;border:1px solid #000;padding:1.5mm;margin-top:1.5mm}' +
    '.qr{text-align:center;margin-top:3mm;font-size:10px;line-height:1.5}' +
    '.qr img{width:34mm;height:34mm;display:block;margin:0 auto 1mm}' +
    '.ft{text-align:center;font-size:10px;margin-top:3mm;line-height:1.5}' +
    '</style></head><body>' +
    '<img class="lg" src="' + location.origin + '/files/logo-in.png" onerror="this.style.display=\'none\';document.getElementById(\'lgt\').style.display=\'block\'">' +
    '<h1 id="lgt" style="display:none">THE VAGABOND P&Acirc;TISSERIE</h1>' +
    '<div class="ph">' + h((posQuay && posQuay.ten) || '') + '<br>' + h((posQuay && posQuay.phu) || '') + '</div>' +
    '<div class="tt">' + (d.huy ? 'BILL ĐÃ HUỶ' : (d.tam_tinh ? 'PHIẾU TẠM TÍNH' : 'HOÁ ĐƠN BÁN HÀNG')) + '</div>' +
    /* Bill da huy in ra phai nhin la biet ngay: khong dong dau thi to giay
       giong het bill that, khach cam nham va thu ngan doi soat cung nham. */
    (d.huy
      ? '<div style="border:2px solid #000;text-align:center;font-weight:bold;font-size:13px;padding:2mm;margin:1.5mm 0;letter-spacing:.1em">' +
        'BILL NÀY ĐÃ HUỶ - KHÔNG CÓ GIÁ TRỊ THANH TOÁN' +
        (d.huy_ly_do ? '<div style="font-size:10px;font-weight:normal;letter-spacing:0;margin-top:1mm">Lý do: ' + h(d.huy_ly_do) + '</div>' : '') +
        '</div>'
      : '') +

    '<div class="d"><span>Mã bill: <b>' + h(d.bill || '') + '</b></span><span>' + h(d.name || '') + '</span></div>' +
    '<div class="d"><span>Thu ngân: ' + h(d.thu_ngan || S.me.full_name || String(S.user).split('@')[0]) + '</span><span>' + lucIn + '</span></div>' +
    (d.so_ban ? '<div class="d"><span style="font-size:14px;font-weight:bold">Bàn: ' + h(d.so_ban) + '</span></div>' : '') +
    (d.ten ? '<div class="d"><span>Khách: ' + h(d.ten) + '</span></div>' : '') +
    '<hr><table>' + rows + '</table><hr>' +
    '<div class="d"><span>Tạm tính</span><b>' + money(d.tong) + '</b></div>' +
    /* Tach tung chuong trinh mot dong: khach doc bill la biet duoc giam
       nhung gi, khoi ra quay hoi lai (anh Viet 11/08/2026). Ma combo
       KHONG in - chi in ten combo cho nguoi doc, con mon thi da nam
       thanh tung dong o tren roi. */
    ((d.kmAp || []).map(function (a) {
      return '<div class="d"><span>' + h(a.ten) + '</span><b>-' + money(a.giam) + '</b></div>';
    }).join('')) +
    (d.giamTay ? '<div class="d"><span>Giảm giá</span><b>-' + money(d.giamTay) + '</b></div>' : '') +
    '<div class="d"><span style="font-size:13px;font-weight:bold">' + (d.tam_tinh ? 'TẠM TÍNH' : 'PHẢI THU') + '</span><b class="to">' + money(d.thu) + ' đ</b></div>' +
    (d.pt && !d.tam_tinh ? '<div class="d"><span>Thanh toán</span><b>' + h(d.pt) + '</b></div>' : '') +
    /* Khoi diem thanh vien (anh Viet 13/08/2026): khach cam bill la biet
       ngay don nay duoc bao nhieu diem va tong con bao nhieu, khong phai
       ra quay hoi. Chi in tren bill THAT - phieu tam tinh chua thanh
       toan nen chua co diem, in vao la hua nham voi khach. */
    (d.diem && !d.tam_tinh && !d.huy
      ? '<hr><div class="d"><span style="font-weight:bold">THẺ THÀNH VIÊN</span><b>' + h(d.diem.hang || '') + '</b></div>' +
        '<div class="d"><span>' + h(d.diem.ten || '') + '</span></div>' +
        (d.diem.dung
          ? '<div class="d"><span>Điểm đã dùng cho đơn này</span><b>-' + money(d.diem.dung) + '</b></div>'
          : '') +
        (d.diem.tich
          ? '<div class="d"><span>Điểm tích đơn này (' + money(d.diem.ty_le) + '%)</span><b>+' + money(d.diem.tich) + '</b></div>'
          : '<div class="d"><span>Hạng này không tích điểm</span></div>') +
        '<div class="d"><span>Số dư điểm khả dụng</span><b>' + money(d.diem.du_sau) + '</b></div>'
      : '') +
    (d.ghi_chu ? '<div class="gc">Ghi chú: ' + h(d.ghi_chu) + '</div>' : '') +
    qrKhoi +
    '<div class="ft">' + (d.tam_tinh ? 'Phiếu giữ món, chưa phải hoá đơn thanh toán.' : 'Cảm ơn quý khách!') + '<br>thevagabondpatisserie.com</div>' +
    lien2 +
    '</body></html>');
  await inTo('hoa_don', inTieuDe, inToBill, inKho('hoa_don').rong, 1100, inW);
}

/* In phieu tam tinh: luu bill tam tinh vao so (giu mon, chua thanh toan)
   roi in ngay. Cashier sau nay vao Bill hom nay chot, thu tien, ghi so. */
async function posInTamTinh() {
  posDoc();
  if (!posDon.mon.length) return toast('Hoá đơn chưa có món nào.');
  var thieuGia = posDon.mon.filter(function (m) { return !m.rate; });
  if (thieuGia.length) return toast('Món ' + thieuGia[0].ten + ' chưa có giá trong danh mục.');
  /* Ve tru diem KHONG di theo phieu tam tinh: phieu tam tinh con duoc sua
     (them bot mon) truoc khi chot, ma diem thi tru mot lan la xong. De ve
     lai cho luc bam Thu tien, va noi ro cho thu ngan biet. */
  if (posDon.diemVe) {
    return toast('Đã xác nhận trừ ' + money(posDon.diemVe.so_diem) + ' điểm cho khách. Điểm chỉ trừ ' +
      'khi bấm Thu tiền, phiếu tạm tính chưa trừ. Bấm Bỏ ở khối điểm nếu muốn in tạm tính trước.', 6000);
  }
  var giamTay = posSoTien(posDon.giam);
  var tong = posDon.mon.reduce(function (t, m) { return t + m.qty * m.rate; }, 0);
  await posTinhKm();
  var giam = giamTay + ((posDon.kmKq && posDon.kmKq.tong_giam) || 0);
  var thu = Math.max(0, tong - giam);
  var ok = await confirmSheet('In phiếu tạm tính ' + money(thu) + ' đ',
    'Hoá đơn được lưu TẠM TÍNH - giữ món, chưa tính doanh thu.\nKhách thanh toán xong thì vào Hoá đơn hôm nay bấm Chốt.', 'Lưu và in phiếu');
  if (!ok) return;
  busy(true);
  var r;
  try {
    r = await api('vagabond.ban_hang.tao_don_tay', {
      ngay: today(), nguon: posNguonThuc(), ma_don: posDon.bill,
      ten_khach: posDon.ten || '', dien_thoai: posDon.sdt || '',
      items: JSON.stringify(posDon.mon.map(function (m) { return { item_code: m.item_code, qty: m.qty, rate: m.rate, tuy_chon: (m.tc || []).join(', '), ghi_chu: posGcGui(m, posMaAppHienTai()), combo: m.combo || '' }; })),
      giam_gia: giamTay, phi_ship: 0, quay: posQuay.ma || '', so_ban: posDon.so_ban || '',
      khach_no: (posDon.khach_no && posDon.khach_no.ma) || '',
      khach_ma: posDon.khach_ma || '',
      ctkm_ap: JSON.stringify(posDon.ctkm || []),
      combo_ap: JSON.stringify(posDon.combo || []),
      ma_voucher: posDon.maVc || '',
      ghi_chu: (posDon.km ? 'KM: ' + posDon.km.ten + (posDon.ghi_chu ? '. ' : '') : '') + (posDon.ghi_chu || ''), tam_tinh: 1
    });
  } catch (e) { busy(false); return toast((e && e.message) || 'Lưu lỗi, thử lại.', 4000); }
  busy(false);
  posBillVua = { name: (r && r.name) || '', bill: posDon.bill, mon: posDon.mon.slice(), tong: tong, giam: giam, giamTay: giamTay, kmAp: ((posDon.kmKq && posDon.kmKq.ap) || []).slice(), thu: thu, pt: '', quay: (posQuay && posQuay.ma) || '', nguon: posNguonThuc(), ghi_chu: posDon.ghi_chu || '', ten: posDon.ten || '', so_ban: posDon.so_ban || '', tam_tinh: 1 };
  posInBill(posBillVua);
  posDon = posMoi();
  posHomNayTxt = null;
  toast('Đã lưu hoá đơn tạm tính ' + ((r && r.name) || ''));
  go(scrPosDs, true);
}

/* ---------- Bill hom nay cua quay: xem - sua - xoa - chot - ghi so ---------- */
function posChipBill(r) {
  /* Chip pastel to ro nhu ben danh sach bill Doanh thu Sales
     (anh Viet 09/08: "lam chip the nay moi dep"). */
  var c = [];
  var the = function (bg, fg, chu) { return '<span style="display:inline-block;background:' + bg + ';color:' + fg + ';font-size:12px;font-weight:700;border-radius:999px;padding:3px 10px;margin:3px 5px 0 0;white-space:nowrap">' + chu + '</span>'; };
  if (r.vgb_huy) c.push(the('#fee2e2', '#991b1b', '🚫 Đã huỷ'));
  if (r.vgb_lan_sua) c.push(the('#fef3c7', '#92400e', '✏️ Đã sửa ' + r.vgb_lan_sua + ' lần'));
  if (r.docstatus === 1) c.push(the('#dcfce7', '#166534', '✅ Đã ghi sổ'));
  else if (r.vgb_tam_tinh) c.push(the('#fef3c7', '#92400e', '🕐 Tạm tính'));
  else c.push(the('#e5e7eb', '#374151', '📄 Chưa ghi sổ'));
  if (r.vgb_pt_thanh_toan) c.push(the('#e0f2fe', '#075985', h(r.vgb_pt_thanh_toan)));
  if ((r.vgb_pt_thanh_toan || '') === 'Chuyển khoản') {
    c.push(r.sepay_du ? the('#dcfce7', '#166534', 'SePay ✓ đủ tiền') : the('#fee2e2', '#991b1b', '⏳ Chờ tiền về'));
  }
  if (r.custom_hddt_so || (r.custom_hddt_trang_thai || '').trim()) {
    var mhd = DS_MAU_HD[r.custom_hddt_trang_thai] || ['#ede9fe', '#5b21b6'];
    c.push(the(mhd[0], mhd[1],
      (r.custom_hddt_so ? 'HĐ ' + h(r.custom_hddt_so) : 'HĐĐT') +
      (r.custom_hddt_trang_thai ? ' · ' + h(r.custom_hddt_trang_thai) : '')));
  }
  else if (r.vgb_xhd_mst) c.push(the('#fef9c3', '#854d0e', '🧾 Chờ xuất HĐ công ty'));
  if (r.discount_amount) c.push(the('#ffedd5', '#9a3412', '🎟 Giảm ' + money(r.discount_amount) + ' đ'));
  if (r.trung_ma) c.push(the('#fee2e2', '#991b1b', '⚠ Trùng mã trong ngày'));
  if (r.vgb_ghi_chu) c.push(the('#e0f7fa', '#0369a1', '📝 ' + h(String(r.vgb_ghi_chu).slice(0, 30))));
  return c.join('');
}
async function scrPosDs() {
  if (!posQuay) return go(scrPosChonQuay, true);
  if (!posDsNgay) posDsNgay = today();
  var laHomNay = posDsNgay === today();
  var tieuDe = (laHomNay ? 'Hoá đơn hôm nay' : 'Hoá đơn ' + posDsNgay.split('-').reverse().join('/')) + ' · ' + (posQuay.ma || '');
  frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang tải hoá đơn...</div></div>');
  var kq;
  try { kq = await api('vagabond.ban_hang.pos_ds_bill', { quay: posQuay.ma || '', ngay: posDsNgay }); }
  catch (e) { frame(tieuDe, '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var ds = (kq && kq.bill) || [];
  /* Bill da huy van nam trong danh sach de xem lai, nhung KHONG duoc cong
     vao tong: man Chot ca ben may chu da loc no ra roi, o day quen loc la
     hai con so lech nhau, thu ngan dem tien thay thieu ma khong hieu vi sao. */
  var dsTien = ds.filter(function (r) { return !r.vgb_huy; });
  var tong = dsTien.reduce(function (t, r) { return t + (r.grand_total || 0); }, 0);
  var soHuy = ds.length - dsTien.length;
  /* Tong theo phuong thuc de cashier doi soat nhanh ma khong can mo chot ca. */
  var ptTong = {};
  dsTien.forEach(function (r) {
    if (r.vgb_tam_tinh) return;
    var p = r.vgb_pt_thanh_toan || r.custom_nguon || 'Khác';
    ptTong[p] = (ptTong[p] || 0) + (r.grand_total || 0);
  });
  var ptTxt = Object.keys(ptTong).map(function (p) { return h(p) + ' ' + money(ptTong[p]) + ' đ'; }).join(' · ');
  /* Lich chon ngay: xem lai bill ngay qua khu (anh Viet 09/08). */
  var html = '<div class="card" style="padding:12px 14px;display:flex;align-items:center;gap:12px">' +
    '<div style="font-weight:600;white-space:nowrap">' + posNgayVn(posDsNgay) + '</div>' +
    '<input type="date" class="hin" id="posDsDate" value="' + posDsNgay + '" max="' + today() + '" style="flex:1;margin:0">' +
    chipNgay('data-pdbuoc') + '</div>';
  html += '<div class="card" style="padding:12px 14px;display:flex;align-items:center;gap:8px">' +
    '<div style="flex:1;min-width:0"><b>' + dsTien.length + ' hoá đơn · ' + money(tong) + ' đ</b>' +
    (soHuy ? '<span style="color:#991b1b;font-size:12.5px;font-weight:700;margin-left:8px">+ ' + soHuy + ' đã huỷ</span>' : '') +
    '<div style="font-size:12px;color:#5b6472">' + (ptTxt || 'Chưa có hoá đơn doanh thu') + '</div>' +
    '<div style="font-size:12px;color:#98a2b3">Hoá đơn của quầy ' + h(posQuay.ten) + ', mỗi quầy tự quản hoá đơn của mình.</div></div>' +
    (laHomNay ? '<button class="btn gh" id="posDsMoi" style="margin:0;padding:9px 11px;font-size:13px;flex:none">🧾 Hoá đơn mới</button>' : '') +
    '<button class="btn" id="posDsChotCa" style="margin:0;padding:9px 11px;font-size:13px;flex:none">🧮 Chốt ca</button></div>';
  /* Bo loc hai tang giong man Sales: tinh trang x nguon/phuong thuc.
     Quan ly ca soat cuoi ngay chi can bam vai chip la ra dung nhom can xem
     (anh Viet 10/08/2026). */
  var PTT = [
    { k: 'tat_ca', nhan: 'Tất cả', loc: function () { return true; } },
    { k: 'chua_ghi', nhan: '📄 Chưa ghi sổ', loc: function (r) { return r.docstatus === 0 && !r.vgb_tam_tinh && !r.vgb_huy; } },
    { k: 'da_ghi', nhan: '✅ Đã ghi sổ', loc: function (r) { return r.docstatus === 1; } },
    { k: 'tam_tinh', nhan: '🕐 Tạm tính', loc: function (r) { return !!r.vgb_tam_tinh && !r.vgb_huy; } },
    { k: 'da_huy', nhan: '🚫 Đã huỷ', loc: function (r) { return !!r.vgb_huy; } },
    { k: 'da_sua', nhan: '✏️ Đã sửa', loc: function (r) { return !!r.vgb_lan_sua; } },
    { k: 'cho_tien', nhan: '⏳ Chờ tiền về', loc: function (r) { return (r.vgb_pt_thanh_toan || '') === 'Chuyển khoản' && !r.sepay_du; } },
    { k: 'du_tien', nhan: '💰 SePay đã đủ tiền', loc: function (r) { return !!r.sepay_du; } },
    { k: 'xhd_cty', nhan: '🏢 Xuất hoá đơn công ty', loc: function (r) { return !!r.vgb_xhd_mst; } },
    { k: 'chua_hddt', nhan: '📌 Chưa có hoá đơn điện tử', loc: function (r) { return r.docstatus === 1 && !!r.vgb_xhd_mst && !r.custom_hddt_so; } },
    { k: 'giam', nhan: '🎟 Có giảm giá', loc: function (r) { return !!r.discount_amount; } },
    { k: 'ban', nhan: '🪑 Có số bàn', loc: function (r) { return !!r.vgb_so_ban; } },
    { k: 'ghi_chu', nhan: '📝 Có ghi chú', loc: function (r) { return !!r.vgb_ghi_chu; } },
    { k: 'trung', nhan: '⚠ Trùng mã trong ngày', loc: function (r) { return !!r.trung_ma; } }
  ];
  var PNG = locNguonPt(ds);
  var PHD = locHddt();
  var pTt = locTim(PTT, posLocTt), pNg = locTim(PNG, posLocNg), pHd = locTim(PHD, posLocHd);
  posLocTt = pTt.k; posLocNg = pNg.k; posLocHd = pHd.k;
  html += '<div class="card" style="padding:10px 12px;display:flex;flex-direction:column;gap:7px">' +
    locHang(PTT, posLocTt, 'data-ptt', ds) +
    locHang(PNG, posLocNg, 'data-png', ds.filter(pTt.loc)) +
    locHang(PHD, posLocHd, 'data-phd', ds.filter(pTt.loc)) + '</div>';
  var dsL = ds.filter(function (r) { return pTt.loc(r) && pNg.loc(r) && pHd.loc(r); });
  html += locKhoiTong(dsL, [
    posLocTt === 'tat_ca' ? '' : pTt.nhan, pNg.k ? pNg.nhan : '', pHd.k ? pHd.nhan : ''
  ].filter(Boolean).join(' · '));
  html += '<div class="card" style="margin-top:10px">';
  if (!ds.length) html += '<div class="emp" style="padding:24px"><div class="e1">🧾</div><div>' + (laHomNay ? 'Hôm nay chưa có hoá đơn nào.' : 'Ngày này không có hoá đơn nào.') + '</div></div>';
  else if (!dsL.length) html += '<div class="emp" style="padding:24px"><div class="e1">✅</div><div>Không có hoá đơn nào thuộc nhóm <b>' + pTt.nhan + (pNg.k ? ' · ' + pNg.nhan : '') + '</b>.</div></div>';
  dsL.forEach(function (r) {
    var gio = String(r.creation || '').slice(11, 16);
    var phu = [gio, h(r.custom_nguon || '')];
    if (r.total_qty) phu.push(money(r.total_qty) + ' món');
    /* "Ban cho nguoi tieu dung" la gia tri mac dinh, khong phai cong ty
       that - hien len moi dong chi gay nhieu. */
    if (r.vgb_xhd_ten && r.vgb_xhd_ten !== 'Bán cho người tiêu dùng') phu.push('🏢 ' + h(String(r.vgb_xhd_ten).slice(0, 26)));
    html += '<div class="hub" data-bill="' + h(r.name) + '"><div class="hi">🧾</div>' +
      '<div class="ht"><div class="h1">' + h(r.custom_pancake_display_id || r.name) + ' · ' + money(r.grand_total) + ' đ</div>' +
      '<div class="h2">' + phu.join(' · ') + '</div>' +
      '<div>' + posChipBill(r) + '</div></div>' +
      '<span class="fc" style="color:#c3c8d4;font-size:22px">&#8250;</span></div>';
  });
  html += '</div>';
  var b = frame(tieuDe, html);
  var oD = document.getElementById('posDsDate');
  if (oD) oD.onchange = function () { posDsNgay = oD.value || today(); posLocTt = 'tat_ca'; posLocNg = ''; go(scrPosDs, true); };
  veODate('posDsDate');
  /* O tim don dung chung, khong gioi han ngay (anh Viet 18/08/2026). Hai
     man tinh tien deu dung chung mot o va mot phep tim. */
  timDonGan();
  b.addEventListener('click', function (e) {
    var t = e.target.closest('[data-pdbuoc]'); if (!t) return;
    var bu = +t.getAttribute('data-pdbuoc');
    var moi = bu ? ngayCong(posDsNgay || today(), bu) : today();
    if (moi > today()) return toast('Chưa tới ngày đó.');
    posDsNgay = moi; posLocTt = 'tat_ca'; posLocNg = '';
    go(scrPosDs, true);
  });
  b.onclick = function (e) {
    var ct = e.target.closest('[data-ptt]');
    if (ct) { posLocTt = ct.getAttribute('data-ptt'); return go(scrPosDs, true); }
    ct = e.target.closest('[data-png]');
    if (ct) { posLocNg = ct.getAttribute('data-png'); return go(scrPosDs, true); }
    ct = e.target.closest('[data-phd]');
    if (ct) { posLocHd = ct.getAttribute('data-phd'); return go(scrPosDs, true); }
    if (e.target.id === 'posDsMoi') return go(scrPosQuay);
    if (e.target.id === 'posDsChotCa') return go(scrPosChotCa);
    var r = e.target.closest('[data-bill]');
    if (r) go(function () { scrPosBill(r.dataset.bill); });
  };
}
/* Chi tiet hoa don quay. Anh Viet 09/08/2026: hoa don la tien that da thu
   cua khach nen mac dinh KHOA HET - xem thi duoc, sua thi phai bam nut Sua
   hoa don va co ma OTP cua quan ly. Rieng hoa don con TAM TINH (khach chua
   tra tien) thi cashier van chot binh thuong, do la nghiep vu hang ngay. */
var posSua = null; /* {name, otp, mon[], giam, pt, mtc, ghi_chu, so_ban, xh} */
async function scrPosBill(name) {
  frame('Hoá đơn ' + name, '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api('frappe.client.get', { doctype: 'Sales Invoice', name: name }); }
  catch (e) { frame('Hoá đơn', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không đọc được hoá đơn') + '</div></div>'); return; }
  await cfgBanHang();
  var tamTinh = !!d.vgb_tam_tinh, nhap = d.docstatus === 0;
  var maBill = d.custom_pancake_display_id || '';
  var dsPt = ptTheoNguon(d.custom_nguon || '');
  var daKy = !!d.custom_hddt_so;
  if (posSua && posSua.name !== name) posSua = null;
  var suaMo = !!posSua;

  function monTuDoc() {
    return (d.items || []).map(function (m) {
      var tc = [];
      var mo = /\[([^\]]+)\]/.exec(String(m.description || ''));
      if (mo) tc = String(mo[1]).split(',').map(function (x) { return x.trim(); }).filter(Boolean);
      /* Dong bat dau bang dau ※ la GHI CHU RIENG cua mon do. */
      var gc = '';
      var mg = /\u203b\s*(.+)/.exec(String(m.description || ''));
      if (mg) gc = String(mg[1]).trim();
      /* Dong bat dau bang dau ◈ la TEN COMBO ma mon do thuoc ve - phai doc
         lai duoc thi in lai bill cu moi con thay combo (anh Viet 11/08). */
      var cb = '';
      var mc = /\u25c8\s*(.+)/.exec(String(m.description || ''));
      if (mc) cb = String(mc[1]).trim();
      return { item_code: m.item_code, ten: m.item_name || m.item_code, qty: m.qty, rate: m.rate, tc: tc, gc: gc, combo: cb };
    });
  }
  var mon = suaMo ? posSua.mon : monTuDoc();
  var giam = suaMo ? posSoTien(posSua.giam) : (d.discount_amount || 0);
  var tongMon = mon.reduce(function (t, m) { return t + m.qty * m.rate; }, 0);
  var phaiThu = suaMo ? Math.max(0, tongMon - giam) : d.grand_total;
  var soBan = suaMo ? posSua.so_ban : (d.vgb_so_ban || '');

  /* ----- the dau: ma, chip trang thai, so ban ----- */
  var html = '<div class="card" style="padding:12px 14px">' +
    '<div style="display:flex;justify-content:space-between"><b style="font-size:16px">' + h(maBill || d.name) + '</b><span style="color:#98a2b3;font-size:12px">' + h(d.name) + '</span></div>' +
    '<div style="font-size:12px;color:#6b7280">' + h(d.custom_nguon || '') + ' · ' + h(String(d.creation || '').slice(0, 16)) +
    (d.vgb_quay ? ' · quầy ' + h(d.vgb_quay) : '') + '</div>' +
    '<div style="margin-top:4px">' + posChipBill({
      docstatus: d.docstatus, vgb_tam_tinh: d.vgb_tam_tinh, vgb_pt_thanh_toan: d.vgb_pt_thanh_toan,
      sepay_du: 0, custom_hddt_so: d.custom_hddt_so, vgb_xhd_mst: d.vgb_xhd_mst,
      discount_amount: d.discount_amount, vgb_ghi_chu: '',
      vgb_huy: d.vgb_huy, vgb_lan_sua: d.vgb_lan_sua
    }) +
    (soBan ? '<span style="display:inline-block;background:#fef3c7;color:#92400e;font-size:12px;font-weight:700;border-radius:999px;padding:3px 10px;margin:3px 5px 0 0">🪑 Bàn ' + h(soBan) + '</span>' : '') +
    '</div></div>';

  /* Bill da huy: noi thang o ngay dau man, khong de thu ngan doc het bang
     mon roi moi phat hien minh dang xem mot to da bo. */
  if (d.vgb_huy) {
    html += '<div class="card" style="padding:12px 14px;margin-top:10px;background:#fef2f2;border:1px solid #fecaca">' +
      '<b style="font-size:14.5px;color:#991b1b">🚫 Bill này đã huỷ</b>' +
      '<div style="font-size:13px;color:#7f1d1d;line-height:1.6;margin-top:3px">' +
      'Lý do: ' + h(d.vgb_huy_ly_do || 'không ghi') +
      (d.vgb_huy_boi ? '<br>Người huỷ: ' + h(d.vgb_huy_boi) : '') +
      (d.vgb_huy_luc ? ' · ' + h(String(d.vgb_huy_luc).slice(0, 16)) : '') +
      '<br>Bill vẫn nằm nguyên trong hệ thống để đối chiếu, chỉ không tính vào doanh thu.' +
      '</div></div>';
  }

  /* ----- bang mon ----- */
  var suaMon = suaMo && nhap; /* hoa don da ghi so thi khong doi mon duoc */
  html += '<div class="card" style="padding:6px 14px;margin-top:10px">';
  if (!mon.length) html += '<div style="padding:14px 0;color:#a0a6b4">Hoá đơn không còn món nào.</div>';
  mon.forEach(function (m, i) {
    var NUT = 'height:34px;width:34px;flex:none;border:1px solid #e5e7eb;background:#fff;border-radius:9px;font-size:17px;line-height:1;padding:0;cursor:pointer';
    html += '<div style="display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid #f0f2f6">' +
      '<div style="flex:1;min-width:0"><div style="font-size:14px">' + h(m.ten) + '</div>' +
      ((m.tc || []).length ? '<div style="color:#0f766e;font-size:12px;margin-top:2px">⚙ ' + h(m.tc.join(', ')) + '</div>' : '') + '</div>' +
      (suaMon
        ? '<button data-sbot="' + i + '" style="' + NUT + '">&minus;</button>' +
          '<b style="min-width:20px;text-align:center">' + money(m.qty) + '</b>' +
          '<button data-scong="' + i + '" style="' + NUT + '">+</button>' +
          '<b style="min-width:66px;text-align:right">' + money(m.qty * m.rate) + '</b>' +
          '<button data-sxoa="' + i + '" style="' + NUT + ';color:#b3261e">✕</button>'
        : '<b style="white-space:nowrap">x' + money(m.qty) + '</b><b style="min-width:76px;text-align:right">' + money(m.qty * m.rate) + '</b>') +
      '</div>';
  });
  if (suaMon) html += '<div style="padding:9px 0"><button class="btn gh" id="pbThemMon" style="width:100%;margin:0">➕ Thêm món</button></div>';
  if (giam) html += '<div style="display:flex;justify-content:space-between;padding:7px 0;color:#b45309"><span>Giảm giá</span><b>-' + money(giam) + '</b></div>';
  html += '<div style="display:flex;justify-content:space-between;padding:9px 0;font-size:16px"><b>' + (tamTinh ? 'TẠM TÍNH' : 'PHẢI THU') + '</b><b>' + money(phaiThu) + ' đ</b></div></div>';

  /* ----- khoi thong tin xuat hoa don khach da dien ----- */
  var coXhd = d.vgb_xhd_mst && String(d.vgb_xhd_mst).trim();
  html += '<div class="sec">Thông tin xuất hoá đơn</div>';
  if (suaMo) {
    html += '<div class="card" style="padding:12px 14px;display:grid;gap:9px">' +
      '<input class="tin" id="pbXTen" placeholder="Tên công ty trên hoá đơn" value="' + h(posSua.xh.ten || '') + '">' +
      '<div style="display:flex;gap:8px"><input class="tin" id="pbXMst" inputmode="numeric" placeholder="Mã số thuế" value="' + h(posSua.xh.mst || '') + '" style="flex:1">' +
      '<button class="btn gh" id="pbXTra" style="margin:0;flex:0 0 34%">🔍 Tra MST</button></div>' +
      '<input class="tin" id="pbXDc" placeholder="Địa chỉ công ty" value="' + h(posSua.xh.dc || '') + '">' +
      '<input class="tin" id="pbXMail" placeholder="Email nhận hoá đơn điện tử" value="' + h(posSua.xh.email || '') + '"></div>';
  } else if (coXhd) {
    var dongX = function (nhan, gt) {
      return '<div style="display:flex;justify-content:space-between;gap:10px;padding:6px 0;border-bottom:1px solid #f0f2f6">' +
        '<span style="color:#6b7280;font-size:13px;flex:none">' + nhan + '</span>' +
        '<b style="font-size:13.5px;text-align:right;word-break:break-word">' + h(gt || '-') + '</b></div>';
    };
    html += '<div class="card" style="padding:6px 14px">' +
      dongX('Tên công ty', d.vgb_xhd_ten) + dongX('Mã số thuế', d.vgb_xhd_mst) +
      dongX('Địa chỉ', d.vgb_xhd_dia_chi) + dongX('Email nhận', d.vgb_xhd_email) +
      '<div style="padding:8px 0;font-size:12.5px;color:' + (daKy ? '#15803d' : '#b45309') + '">' +
      (daKy ? '✅ Đã phát hành hoá đơn điện tử số ' + h(d.custom_hddt_so) : '⏳ Chờ 23h30 máy đẩy sang m-invoice ký và gửi email cho khách') + '</div></div>';
  } else {
    html += '<div class="card" style="padding:12px 14px;font-size:13.5px;color:#6b7280;line-height:1.6">' +
      'Khách chưa gửi thông tin xuất hoá đơn. Khách quét mã QR cuối hoá đơn giấy để tự điền (mã có hiệu lực 2 tiếng), ' +
      'hoặc nhân viên bấm <b>Sửa hoá đơn</b> để điền hộ.</div>';
  }

  /* ----- thanh toan ----- */
  var choChon = suaMo || (nhap && tamTinh); /* tam tinh la nghiep vu chot binh thuong */
  var PB_PT = suaMo ? (posSua.pt || d.vgb_pt_thanh_toan || '') : (d.vgb_pt_thanh_toan || '');
  html += '<div class="sec">' + (tamTinh && nhap && !suaMo ? 'Khách thanh toán bằng gì?' : 'Thanh toán') + '</div>';
  if (choChon) {
    html += '<div class="card" style="padding:12px 14px;display:grid;gap:10px">' +
      '<div id="pbPt" style="display:grid;grid-template-columns:1fr 1fr;gap:8px">' + posNutPt(dsPt, PB_PT) + '</div>' +
      '<div id="pbQr"></div>' +
      '<input class="tin" id="pbMtc" placeholder="Mã tham chiếu (biên lai thẻ, mã giao dịch...)" value="' + h((suaMo ? posSua.mtc : d.vgb_ma_tham_chieu) || '') + '">' +
      (suaMo ? '<input class="tin" id="pbGiam" inputmode="numeric" placeholder="Giảm giá cả hoá đơn (đ)" value="' + (giam ? money(giam) : '') + '">' : '') +
      '<input class="tin" id="pbGhiChu" placeholder="Ghi chú hoá đơn" value="' + h((suaMo ? posSua.ghi_chu : d.vgb_ghi_chu) || '') + '">' +
      (suaMo && String(d.custom_nguon || '').indexOf('Tại chỗ') === 0
        ? '<input class="tin" id="pbBan" placeholder="Số bàn" value="' + h(soBan) + '">' : '') +
      '</div>';
  } else {
    /* KHOA: chi doc, muon doi phai bam Sua hoa don + ma OTP quan ly */
    html += '<div class="card" style="padding:12px 14px">' +
      '<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">' +
      '<span style="display:inline-block;background:#e0f2fe;color:#075985;font-size:13px;font-weight:700;border-radius:999px;padding:5px 13px">' + h(d.vgb_pt_thanh_toan || 'Chưa chọn') + '</span>' +
      (d.vgb_ma_tham_chieu ? '<span style="display:inline-block;background:#ede9fe;color:#5b21b6;font-size:13px;font-weight:700;border-radius:999px;padding:5px 13px">Mã ' + h(d.vgb_ma_tham_chieu) + '</span>' : '') +
      '</div>' +
      (d.vgb_ghi_chu ? '<div style="font-size:13.5px;margin-top:10px">📝 ' + h(d.vgb_ghi_chu) + '</div>' : '') +
      '<div style="font-size:12.5px;color:#6b7280;margin-top:10px;line-height:1.6">🔒 Hoá đơn đã thu tiền của khách nên khoá lại. ' +
      'Cần sửa thì bấm <b>Sửa hoá đơn</b> rồi nhập mã OTP xin của quản lý ca.</div></div>';
  }

  /* ----- nut duoi chan man ----- */
  var foot;
  if (d.vgb_huy) {
    foot = '<div style="display:flex;gap:8px">' +
      '<button class="btn gh" id="pbIn" style="flex:1;margin:0">🖨 In</button>' +
      (coQuyenHuy() ? '<button class="btn gh" id="pbGoHuy" style="flex:1;margin:0">↩️ Gỡ dấu huỷ</button>' : '') +
      '</div>';
  } else if (suaMo) {
    foot = '<div style="display:flex;gap:8px">' +
      '<button class="btn gh" id="pbHuySua" style="flex:0 0 34%;margin:0">✕ Thôi sửa</button>' +
      '<button class="btn" id="pbLuuSua" style="flex:1;margin:0">💾 Lưu thay đổi</button></div>';
  } else {
    foot = '<div style="display:flex;gap:8px">' +
      '<button class="btn gh" id="pbIn" style="flex:0 0 30%;margin:0">🖨 In</button>' +
      (nhap
        ? (tamTinh
          ? '<button class="btn" id="pbChot" style="flex:1;margin:0">✅ Chốt hoá đơn - khách đã trả</button>'
          : '<button class="btn" id="pbGhiSo" style="flex:1;margin:0">📒 Ghi sổ tại quầy</button>')
        : '<div style="flex:1;display:flex;align-items:center;justify-content:center;color:#15803d;font-weight:700">✅ Đã ghi sổ</div>') +
      '</div>' +
      /* Tem hien khi bill co bat ky mon nao; phieu lam mon chi hien khi co
         mon nuoc. Cung mot luat voi hai man bao thanh cong ben man tinh
         tien, xem ghi chu o posNutIn. */
      ((d.items || []).length
        ? '<div style="display:flex;gap:8px;margin-top:8px">' +
          (posCoNuoc(d.items || []) ? '<button class="btn gh" id="pbPhieuMon" style="flex:1;margin:0">🧾 In phiếu làm món</button>' : '') +
          '<button class="btn gh" id="pbTemLy" style="flex:1;margin:0">🏷 In tem món</button></div>'
        : '') +
      '<div style="display:flex;gap:8px;margin-top:8px">' +
      '<button class="btn gh" id="pbSua" style="flex:1;margin:0">✏️ Sửa hoá đơn</button>' +
      (nhap ? '<button class="btn gh" id="pbXoa" style="flex:1;margin:0;color:#b3261e;border-color:#fecaca">🚫 Huỷ bill</button>' : '') +
      '</div>';
  }
  var b = frame('Hoá đơn ' + (maBill || d.name), html, { footer: foot });

  function veQr() {
    var o = document.getElementById('pbQr');
    if (!o) return;
    o.innerHTML = PB_PT === 'Chuyển khoản' ? posKhoiQr(posNoiDungCk(maBill || d.name, d.vgb_quay, d.custom_nguon || ''), phaiThu, d.custom_nguon || '', d.vgb_quay) : '';
  }
  var ptw = document.getElementById('pbPt');
  if (ptw) ptw.querySelectorAll('.ptc').forEach(function (c) {
    c.onclick = function () {
      PB_PT = c.getAttribute('data-pt');
      if (posSua) posSua.pt = PB_PT;
      ptw.querySelectorAll('.ptc').forEach(function (x) {
        var on = x.getAttribute('data-pt') === PB_PT;
        x.style.border = '1.5px solid ' + (on ? '#0d9488' : '#e5e7eb');
        x.style.background = on ? '#ccfbf1' : '#fff';
        x.style.color = on ? '#0f766e' : '#374151';
      });
      var mo = document.getElementById('pbMtc');
      if (mo && PB_PT === 'Chuyển khoản' && !mo.value.trim()) mo.value = maBill || '';
      veQr();
    };
  });
  veQr();
  function docO(id) { var o = document.getElementById(id); return o ? o.value : ''; }
  function hutSua() {
    if (!posSua) return;
    posSua.pt = PB_PT;
    posSua.mtc = docO('pbMtc');
    posSua.ghi_chu = docO('pbGhiChu');
    posSua.giam = docO('pbGiam');
    var ob = document.getElementById('pbBan');
    if (ob) posSua.so_ban = ob.value;
    posSua.xh = {
      ten: docO('pbXTen'), mst: docO('pbXMst'), dc: docO('pbXDc'), email: docO('pbXMail')
    };
  }

  /* ----- chot / ghi so (nghiep vu binh thuong, khong can OTP) ----- */
  async function luuVe(chot) {
    if (!PB_PT) return toast('Chọn phương thức thanh toán trước.');
    busy(true);
    try {
      await api('vagabond.ban_hang.pos_chot', { name: d.name, pt: PB_PT, ma_tham_chieu: docO('pbMtc'), ghi_chu: docO('pbGhiChu') });
      if (chot) await api('vagabond.ban_hang.pos_ghi_so', { name: d.name });
      busy(false);
      toast(chot ? 'Đã ghi sổ ' + d.name : 'Đã chốt hoá đơn ' + d.name);
      posHomNayTxt = null;
      go(scrPosDs, true);
    } catch (e) { busy(false); toast((e && e.message) || 'Lỗi, thử lại.', 4500); }
  }
  var nc = document.getElementById('pbChot');
  if (nc) nc.onclick = async function () {
    var ok = await confirmSheet('Chốt hoá đơn ' + money(d.grand_total) + ' đ - ' + (PB_PT || 'chưa chọn'),
      'Khách đã thanh toán xong? Chốt xong hoá đơn thành doanh thu, ghi sổ được ngay.', 'Khách đã trả, chốt hoá đơn');
    if (ok) luuVe(false);
  };
  var ng = document.getElementById('pbGhiSo');
  if (ng) ng.onclick = async function () {
    var ok = await confirmSheet('Ghi sổ hoá đơn ' + money(d.grand_total) + ' đ',
      'Ghi sổ là chốt doanh thu chính thức tại quầy ' + (posQuay ? posQuay.ma : '') + '. Chuyển khoản thì máy tự kiểm SePay đủ tiền mới cho ghi.', 'Ghi sổ');
    if (ok) luuVe(true);
  };

  /* ----- go dau huy: danh dau nham thi lay lai duoc ----- */
  var ngh = document.getElementById('pbGoHuy');
  if (ngh) ngh.onclick = async function () {
    var ok = await confirmSheet('Gỡ dấu huỷ bill ' + (maBill || d.name) + '?',
      'Bill dùng lại bình thường và tính vào doanh thu trở lại.', 'Gỡ dấu huỷ');
    if (!ok) return;
    busy(true);
    try {
      await api('vagabond.chung_tu.bo_danh_dau_huy', { doctype: 'Sales Invoice', name: d.name });
      busy(false); toast('Đã gỡ dấu huỷ.'); posHomNayTxt = null;
      go(function () { scrPosBill(name); }, true);
    } catch (e) { busy(false); toast((e && e.message) || 'Không gỡ được', 5000); }
  };

  /* ----- huy bill: KHONG con xoa nua (anh Viet 11/08/2026) -----
     Hom 10/08 quan ly cua hang xoa 37 hoa don quay Tran Cao Van, so hoa
     don dien tu van nam ben co quan thue ma chung tu goc bien mat sach.
     Nay bill huy van nam nguyen trong danh sach, chi doi mau va bi loc ra
     khoi doanh thu - xem lai duoc bat cu luc nao. */
  var nx = document.getElementById('pbXoa');
  if (nx) nx.onclick = async function () {
    var ok = await confirmSheet('Huỷ bill ' + (maBill || d.name) + '?',
      'Bill ' + money(d.grand_total) + ' đ sẽ được đánh dấu đã huỷ và không tính vào doanh thu nữa. ' +
      'Bill vẫn nằm nguyên trong hệ thống để đối chiếu - không ai xoá được chứng từ. ' +
      'Thao tác này cần mã OTP của quản lý và ghi lại tên người huỷ.', 'Huỷ bill', true);
    if (!ok) return;
    var ly_do = await promptSheet('Vì sao huỷ bill ' + (maBill || d.name) + '?', 'Khách đổi ý, bấm nhầm món, trùng bill...');
    if (ly_do === null) return;
    if (!ly_do) return toast('Phải ghi lý do thì sau này còn biết vì sao.', 4000);
    var otp = await posXinPhep('Huỷ bill ' + (maBill || d.name));
    if (otp === null) return;
    busy(true);
    try {
      await api('vagabond.ban_hang.pos_xoa', { name: d.name, otp: otp, ly_do: ly_do });
      busy(false); toast('Đã huỷ bill ' + (maBill || d.name) + '. Bill vẫn còn trong danh sách.', 4000);
      posHomNayTxt = null; go(scrPosDs, true);
    }
    catch (e) { busy(false); toast((e && e.message) || 'Huỷ lỗi', 5000); }
  };

  /* ----- mo che do sua -----
     Muc quyen "duyet" thi xin OTP ngay tu dau nhu truoc gio. Hai muc con
     lai thi mo ra sua da, den luc Luu ma may chu doi ma moi hoi: luc bam
     Sua chua ai biet thu ngan sap THEM mon (duoc phep) hay BOT mon
     (khong duoc). Hoi truoc la bat ho go ma cho ca viec ho duoc lam. */
  var ns = document.getElementById('pbSua');
  if (ns) ns.onclick = async function () {
    var otp = '';
    if (posQuyenBoMon() === 'duyet') {
      otp = await posXinPhep('Sửa hoá đơn ' + (maBill || d.name));
      if (otp === null) return;
    }
    posSua = {
      name: d.name, otp: otp, mon: monTuDoc(),
      giam: String(d.discount_amount || ''), pt: d.vgb_pt_thanh_toan || '',
      mtc: d.vgb_ma_tham_chieu || '', ghi_chu: d.vgb_ghi_chu || '', so_ban: d.vgb_so_ban || '',
      xh: {
        ten: (d.vgb_xhd_ten && d.vgb_xhd_ten !== 'Bán cho người tiêu dùng') ? d.vgb_xhd_ten : '',
        mst: d.vgb_xhd_mst || '', dc: d.vgb_xhd_dia_chi || '', email: d.vgb_xhd_email || ''
      }
    };
    go(function () { scrPosBill(name); }, true);
  };
  var nhs = document.getElementById('pbHuySua');
  if (nhs) nhs.onclick = function () { posSua = null; go(function () { scrPosBill(name); }, true); };

  /* ----- sua so luong / xoa mon / them mon ----- */
  b.onclick = function (e) {
    if (!posSua) return;
    var t = e.target.closest('[data-scong]');
    if (t) { hutSua(); posSua.mon[+t.getAttribute('data-scong')].qty++; return go(function () { scrPosBill(name); }, true); }
    t = e.target.closest('[data-sbot]');
    if (t) {
      hutSua();
      var i = +t.getAttribute('data-sbot');
      if (posSua.mon[i].qty > 1) posSua.mon[i].qty--;
      return go(function () { scrPosBill(name); }, true);
    }
    t = e.target.closest('[data-sxoa]');
    if (t) { hutSua(); posSua.mon.splice(+t.getAttribute('data-sxoa'), 1); return go(function () { scrPosBill(name); }, true); }
  };
  var ntm = document.getElementById('pbThemMon');
  if (ntm) ntm.onclick = async function () {
    hutSua();
    if (!dsItemsCache) {
      busy(true);
      try {
        dsItemsCache = await getList('Item', { filters: { is_sales_item: 1, disabled: 0 }, fields: ['name', 'item_name', 'image', 'standard_rate', 'item_group'], limit_page_length: 0, order_by: 'item_name' });
      } catch (er) { busy(false); return toast('Không tải được danh mục món'); }
      busy(false);
    }
    posSheetMon(dsItemsCache.map(function (x) {
      return { value: x.name, label: x.item_name, icon: '🎂', img: x.image || '', gia: x.standard_rate || 0, nhom: x.item_group || '', phu: (x.standard_rate ? money(x.standard_rate) + ' đ' : 'chưa có giá') + ' · ' + x.name, tim: x.name + ' ' + (x.ma_vach || '') };
    }), function (o) {
      if (!o.gia) { toast('Món ' + o.label + ' chưa có giá bán trong danh mục.', 4000); return 0; }
      var vt = -1;
      posSua.mon.forEach(function (m, k) { if (m.item_code === o.value) vt = k; });
      if (vt >= 0) { posSua.mon[vt].qty += 1; return posSua.mon[vt].qty; }
      posSua.mon.push({ item_code: o.value, ten: o.label, qty: 1, rate: o.gia, nhom: o.nhom, tc: [], gc: '' });
      return 1;
    }, function () { go(function () { scrPosBill(name); }, true); }, function (ma) {
      var q = 0;
      (posSua ? posSua.mon : []).forEach(function (m) { if (m.item_code === ma) q = m.qty; });
      return q;
    });
  };

  /* ----- tra MST khi sua ----- */
  var nxt = document.getElementById('pbXTra');
  if (nxt) nxt.onclick = async function () {
    var mst = (docO('pbXMst') || '').replace(/\D/g, '');
    if (mst.length !== 10 && mst.length !== 12 && mst.length !== 13) return toast('Nhập đủ mã số thuế: 10 số công ty, 12 số hộ kinh doanh, 13 số chi nhánh.');
    busy(true);
    try {
      var kq = await api('vagabond.api.tra_mst', { mst: mst });
      busy(false);
      if (kq && kq.ok) {
        if (kq.ten) document.getElementById('pbXTen').value = kq.ten;
        if (kq.dia_chi) document.getElementById('pbXDc').value = kq.dia_chi;
        /* Xem ghi chú cùng đợt ở màn Doanh số: cổng tra cứu có lúc trả về
           tên chỉ có loại hình pháp lý, và máy chủ chặn lúc lưu. Báo ngay
           tại đây để người gõ sửa liền chứ không đợi tới lúc bấm Lưu. */
        if (kq.nghi_thieu) {
          var oT = document.getElementById('pbXTen');
          if (oT) { oT.style.borderColor = '#f59e0b'; oT.focus(); }
          baoTin((kq.canh_bao || 'Hệ thống nghi ngờ tên công ty bị thiếu. Vui lòng kiểm tra lại thông tin!')
            + '\n\nCổng tra cứu chỉ trả về "' + (kq.ten || '')
            + '". Vui lòng xem giấy phép kinh doanh của khách rồi gõ đủ tên.', 'Tên công ty bị thiếu');
        } else toast('Tra được: ' + (kq.ten || ''));
      } else toast('Không tra được mã này, vui lòng điền tay.', 4000);
    } catch (er) { busy(false); toast((er && er.message) || 'Không tra được mã số thuế', 4000); }
  };

  /* ----- luu thay doi ----- */
  var nls = document.getElementById('pbLuuSua');
  if (nls) nls.onclick = async function () {
    hutSua();
    if (nhap && !posSua.mon.length) return toast('Hoá đơn phải còn ít nhất một món.');
    var goi = {
      name: d.name, otp: posSua.otp,
      ghi_chu: posSua.ghi_chu || '', so_ban: posSua.so_ban || '',
      xhd_ten: posSua.xh.ten || '', xhd_mst: posSua.xh.mst || '',
      xhd_dia_chi: posSua.xh.dc || '', xhd_email: posSua.xh.email || ''
    };
    if (nhap) {
      goi.items = JSON.stringify(posSua.mon.map(function (m) {
        return { item_code: m.item_code, qty: m.qty, rate: m.rate, tuy_chon: (m.tc || []).join(', '), ghi_chu: m.gc || '' };
      }));
      goi.giam_gia = posSoTien(posSua.giam);
      if (posSua.pt) { goi.pt = posSua.pt; goi.ma_tham_chieu = posSua.mtc || ''; }
    }
    var ok = await confirmSheet('Lưu thay đổi hoá đơn ' + (maBill || d.name) + '?',
      (nhap ? 'Tổng mới: ' + money(Math.max(0, posSua.mon.reduce(function (t, m) { return t + m.qty * m.rate; }, 0) - posSoTien(posSua.giam))) + ' đ.\n' : '') +
      'Máy ghi lại tên người sửa vào lịch sử hoá đơn.', 'Lưu thay đổi');
    if (!ok) return;
    busy(true);
    try {
      await api('vagabond.ban_hang.pos_sua_don', goi);
    } catch (e) {
      busy(false);
      var loi = (e && e.message) || 'Lưu thay đổi lỗi';
      // May chu moi la noi quyet dinh co can OTP hay khong. App khong tu
      // doan: cu gui len, may chu doi ma thi luc do moi hoi quan ly.
      if (loi.indexOf('OTP') < 0) return toast(loi, 5000);
      var otp2 = await posSheetOtp('Sửa hoá đơn ' + (maBill || d.name) + ' - ' + loi);
      if (otp2 === null) return;
      goi.otp = otp2;
      busy(true);
      try { await api('vagabond.ban_hang.pos_sua_don', goi); }
      catch (e2) { busy(false); return toast((e2 && e2.message) || 'Lưu thay đổi lỗi', 5000); }
    }
    busy(false);
    posSua = null; posHomNayTxt = null;
    toast('Đã lưu thay đổi hoá đơn ' + (maBill || d.name));
    go(function () { scrPosBill(name); }, true);
  };

  /* ----- in ----- */
  function pbBillObj() {
    return {
      name: d.name, bill: maBill, tam_tinh: tamTinh ? 1 : 0, so_ban: soBan, quay: d.vgb_quay || '', nguon: d.custom_nguon || '',
      huy: d.vgb_huy ? 1 : 0, huy_ly_do: d.vgb_huy_ly_do || '',
      mon: monTuDoc(),
      tong: (d.items || []).reduce(function (t, m) { return t + (m.amount || 0); }, 0),
      giam: d.discount_amount || 0, thu: d.grand_total,
      pt: d.vgb_pt_thanh_toan || '', ghi_chu: d.vgb_ghi_chu || '', ten: ''
    };
  }
  var ni = document.getElementById('pbIn');
  if (ni) ni.onclick = function () {
    posInBill(pbBillObj());
    go(scrPosDs, true);
  };
  var nPm = document.getElementById('pbPhieuMon');
  if (nPm) nPm.onclick = function () { posInPhieuMon(pbBillObj()); };
  var nTem = document.getElementById('pbTemLy');
  if (nTem) nTem.onclick = function () { posInTemLy(pbBillObj()); };
}


/* ---------- Ma OTP quan ly (anh Viet 09/08/2026) ----------
   Hoa don quay la tien that da thu cua khach. Nhan vien muon sua hay xoa
   thi phai xin ma 6 so cua quan ly ca - vua chan gian lan, vua khong phai
   dua tai khoan sep cho nhan vien muon. Ma tu doi 10 phut mot lan. */
var otpDem = null;
async function scrOtp() {
  frame('Mã OTP quản lý', '<div class="emp"><div class="e1">⏳</div><div>Đang lấy mã...</div></div>');
  var k;
  try { k = await api('vagabond.ban_hang.otp_hien_tai'); }
  catch (e) {
    frame('Mã OTP quản lý', '<div class="card" style="padding:22px 18px;text-align:center">' +
      '<div style="font-size:40px">🔒</div>' +
      '<div style="font-size:15px;font-weight:700;margin-top:8px">Chỉ quản lý được cấp mã</div>' +
      '<div style="font-size:13.5px;color:#6b7280;margin-top:8px;line-height:1.6">' + h((e && e.message) || '') + '</div></div>');
    return;
  }
  var html = '<div class="card" style="padding:20px 18px;text-align:center">' +
    '<div style="font-size:12.5px;color:#6b7280;font-weight:600;letter-spacing:.06em">MÃ ĐANG CÓ HIỆU LỰC</div>' +
    '<div id="otpMa" style="font-size:46px;font-weight:800;letter-spacing:.16em;color:#0f766e;margin:8px 0 2px;font-variant-numeric:tabular-nums">' + h(k.ma) + '</div>' +
    '<div id="otpDem" style="font-size:13px;color:#b45309;font-weight:600"></div>' +
    '<div style="font-size:13px;color:#6b7280;margin-top:14px;line-height:1.7">Đọc mã này cho nhân viên khi họ cần sửa hoặc xoá hoá đơn. ' +
    'Mã tự đổi ' + (k.phut || 10) + ' phút một lần, mã cũ hết hiệu lực ngay.</div></div>';
  html += '<div class="card" style="padding:14px;font-size:13px;color:#5b6472;line-height:1.7">' +
    '<b>Trước khi đọc mã, hỏi nhân viên ba câu:</b><br>' +
    '1. Sửa hoá đơn nào, mã bao nhiêu?<br>' +
    '2. Sửa cái gì, vì sao phải sửa?<br>' +
    '3. Khách đã trả tiền chưa, tiền chênh xử lý thế nào?<br>' +
    '<span style="color:#98a2b3">Mỗi lần sửa hoặc xoá máy đều ghi lại tên người thao tác vào hoá đơn.</span></div>';
  frame('Mã OTP quản lý', html, { footer: '<button class="btn" id="otpMoi">🔄 Lấy mã mới nhất</button>' });
  document.getElementById('otpMoi').onclick = function () { go(scrOtp, true); };
  if (otpDem) clearInterval(otpDem);
  var con = k.con_lai || 0;
  var ve = function () {
    var o = document.getElementById('otpDem');
    if (!o) { clearInterval(otpDem); return; }
    if (con <= 0) { o.textContent = 'Mã đã đổi - bấm Lấy mã mới nhất'; o.style.color = '#b3261e'; clearInterval(otpDem); return; }
    o.textContent = 'Còn hiệu lực ' + Math.floor(con / 60) + ' phút ' + (con % 60) + ' giây';
    con--;
  };
  ve();
  otpDem = setInterval(ve, 1000);
}

/* Sheet nhap ma: tra ve chuoi ma, hoac null neu bo qua. */
function posSheetOtp(viec) {
  return new Promise(function (xong) {
    var ov = document.createElement('div'); ov.className = 'sh';
    ov.innerHTML = '<div class="shb" style="padding:20px 16px calc(env(safe-area-inset-bottom,0px) + 16px)">' +
      '<div style="font-size:18px;font-weight:800">🔐 Cần mã OTP quản lý</div>' +
      '<div style="font-size:13.5px;color:#6b7280;margin-top:6px;line-height:1.6">' + h(viec || 'Thao tác này') +
      ' phải được quản lý duyệt. Gọi quản lý ca xin mã 6 số rồi nhập vào đây.</div>' +
      '<input class="tin" id="otpNhap" inputmode="numeric" maxlength="6" placeholder="- - - - - -" ' +
      'style="margin-top:14px;text-align:center;font-size:30px;letter-spacing:.22em;height:60px;font-weight:800">' +
      '<div style="display:flex;gap:8px;margin-top:14px">' +
      '<button class="btn gh" data-huy style="flex:1;margin:0">Thôi</button>' +
      '<button class="btn" data-ok style="flex:1;margin:0">Xác nhận</button></div></div>';
    document.body.appendChild(ov);
    var o = ov.querySelector('#otpNhap');
    setTimeout(function () { try { o.focus(); } catch (e) { } }, 120);
    ov.onclick = function (e) {
      if (e.target.hasAttribute('data-ok')) {
        var ma = (o.value || '').replace(/\D/g, '');
        if (ma.length !== 6) return toast('Mã OTP gồm 6 số.');
        ov.remove(); return xong(ma);
      }
      if (e.target === ov || e.target.hasAttribute('data-huy')) { ov.remove(); xong(null); }
    };
  });
}

/* Sep thao tac thi may tu biet, khoi nhap ma. Nhan vien thi hien o nhap. */
/* Muc quyen bo mon cua thu ngan, khai o man Cai dat > Quyen tai quay.
   Mac dinh doc la "duyet" (chat nhat) khi chua tai duoc cau hinh - thieu
   mang thi phai nghieng ve phia chat, khong phai phia de. */
function posQuyenBoMon() { return ((CFGBH || {}).quyen_bo_mon) || 'duyet'; }

async function posXinPhep(viec) {
  try { await api('vagabond.ban_hang.otp_hien_tai'); return ''; }
  catch (e) { }
  return await posSheetOtp(viec);
}

/* ---------- Bao quay bar: phieu lam mon + tem ly (anh Viet 09/08/2026) ----------
   Mon nuoc nhan theo ma NU... (NUCF, NUTP, NUIC...) hoac nhom pha che.
   Phieu 80mm (xprinter quay bar) di theo ly thuy tinh ngoi tai quan;
   tem 4cm x 3cm (may in tem) dan ly mang di / giao hang. */
var POS_NHOM_NUOC = ['Trà', 'Cà phê', 'Matcha', 'Cacao', 'Ice Cream - Kem'];
/* Kho giay cua mot loai phieu, khai o Cai dat - May in (anh Viet 12/08/2026).

   Truoc day bon loai phieu deu go cung kho trong ma nguon. Doi mot may in
   khac kho la phai sua ma roi deploy, ma moi lan deploy la mot lan co the
   sai. Nay doc tu cau hinh; chua khai thi roi ve dung kho cu, khong doi
   hanh vi cua ai. */
function inKho(vaiTro) {
  var b = (CFGBH || {}).kho_in || {};
  var k = b[vaiTro];
  if (k && k.css) return k;
  return vaiTro === 'tem'
    ? { k: 'tem_40x30', css: '40mm 30mm', rong: 40, cao: 30, cuon: 0 }
    : { k: '80mm', css: '80mm auto', rong: 72, cuon: 1 };
}

function posLaNuoc(m) {
  if (String((m && m.item_code) || '').toUpperCase().indexOf('NU') === 0) return true;
  return POS_NHOM_NUOC.indexOf((m && m.nhom) || '') >= 0;
}
function posCoNuoc(mon) { return (mon || []).some(posLaNuoc); }
function posMonNuoc(mon) { return (mon || []).filter(posLaNuoc); }

async function posInPhieuMon(d) {
  var nuoc = posMonNuoc(d.mon || []);
  if (!nuoc.length) return toast('Hoá đơn không có món nước nào.');
  /* Phieu lam mon di dung vai CUA NO (v294).

     Ban cu goi thang 'hoa_don' voi ly do "no la giay cuon 80mm nhu bill".
     Ly do do noi ve KHO GIAY, ma kho giay von da doc rieng qua
     inKho('phieu_mon') o duoi. Hau qua: o "May in phieu quay bar" tren man
     Cai dat chua bao gio duoc dung toi, quay bar khong nhan duoc phieu nao.
     Tiem nao chua khai may rieng thi inManhCho tu ro ve may hoa don. */
  var inW = inMoCuaSoNeuCan('phieu_mon');
  if (inW === 'chan') return;
  var gio = new Date();
  var hs = function (n) { return (n < 10 ? '0' : '') + n; };
  var rows = nuoc.map(function (m) {
    return '<div class="m"><span class="q">' + money(m.qty) + 'x</span> <b>' + h(m.ten) + '</b>' +
      (m.combo ? '<div class="tc" style="font-weight:bold">&#9733; ' + h(m.combo) + '</div>' : '') +
      ((m.tc || []).length ? '<div class="tc">&#8594; ' + h(m.tc.join(', ')) + '</div>' : '<div class="tc">&#8594; 100% đường · 100% đá</div>') +
      /* Ghi chu rieng cua mon: quay pha che doc ngay tren phieu, khong
         phai hoi lai thu ngan (anh Viet 10/08/2026). */
      (m.gc ? '<div class="tc" style="font-weight:bold">&#9755; ' + h(m.gc) + '</div>' : '') +
      '</div>';
  }).join('');
  var inToPhieu = ('<html><head><meta charset="utf-8"><title>Phiếu làm món ' + h(d.bill || d.name || '') + '</title><style>' +
    '@page{size:' + inKho('phieu_mon').css + ';margin:0}*{margin:0;padding:0;box-sizing:border-box}' +
    'body{width:' + inKho('phieu_mon').rong + 'mm;margin:0 auto;font-family:Arial,sans-serif;color:#000;padding:3mm 0 6mm}' +
    'h1{font-size:15px;text-align:center;letter-spacing:.1em}' +
    '.ph{text-align:center;font-size:11px;margin:1mm 0 2mm}' +
    'hr{border:0;border-top:1px dashed #000;margin:1.5mm 0}' +
    '.m{font-size:14px;padding:1.5mm 0;border-bottom:1px dashed #999}' +
    '.m .q{font-size:15px;font-weight:bold}' +
    '.tc{font-size:12px;padding-left:6mm}' +
    '.gc{font-size:12px;border:1px solid #000;padding:1.5mm;margin-top:2mm}' +
    '</style></head><body>' +
    '<h1>PHIẾU LÀM MÓN</h1>' +
    '<div class="ph">' + h((posQuay && posQuay.ten) || '') + ' · hoá đơn <b>' + h(d.bill || d.name || '') + '</b> · ' + hs(gio.getHours()) + ':' + hs(gio.getMinutes()) + '</div>' +
    (d.so_ban ? '<div style="text-align:center;font-size:17px;font-weight:bold;margin:1mm 0">BÀN ' + h(d.so_ban) + '</div>' : '') +
    '<hr>' + rows +
    (d.ghi_chu ? '<div class="gc">Ghi chú: ' + h(d.ghi_chu) + '</div>' : '') +
    '</body></html>');
  await inTo('phieu_mon', 'Phiếu làm món', inToPhieu, inKho('phieu_mon').rong, 900, inW);
}

/* Ma don cua san food app doc ra tu mot hoa don da luu: uu tien ma tham
   chieu, khong co thi lay nguon don. In DAM tren dau tem de shipper
   GrabFood, ShopeeFood den doc phat la nhan dung tui (anh Viet 10/08/2026). */
function posMaAppCuaBill(d) {
  var dsApp = ((CFGBH || {}).nguon_app) || ['GrabFood', 'ShopeeFood', 'BeFood', 'GreenSM Food'];
  var ng = (d.nguon || d.pt || '').trim();
  if (dsApp.indexOf(ng) < 0) return '';
  var ma = (d.mtc || d.ma || '').trim();
  return ma ? (ng + ' · ' + ma) : ng;
}

/* Tem dan mon: MOI mon deu duoc in tem chu khong rieng mon nuoc (anh Viet
   10/08/2026) - hop entremet cung can tem de khach nhin la biet banh gi.
   Moi don vi mot tem: 3 ly tra ra 3 tem, 2 hop banh ra 2 tem. */
async function posInTemLy(d) {
  var mon = (d.mon || []).filter(function (m) { return (m.ten || '').trim(); });
  if (!mon.length) return toast('Hoá đơn không có món nào để in tem.');
  var ly = [];
  mon.forEach(function (m) {
    var n = Math.max(1, Math.round(m.qty || 1));
    for (var i = 0; i < n; i++) ly.push(m);
  });
  var inW = inMoCuaSoNeuCan('tem');
  if (inW === 'chan') return;
  var maApp = posMaAppCuaBill(d);
  var tem = ly.map(function (m, i) {
    /* Dong giua: tuy chon pha che voi mon nuoc, ghi chu rieng voi moi mon,
       VA ghi chu cua ca bill. Mon banh khong co tuy chon thi de trong chu
       khong in "100% da".

       Ghi chu bill duoc them 19/08/2026 theo De: *"khi in tem thi moi ghi
       chu phai duoc in theo"*. Truoc day o "Ghi chu bill" - goi qua, de
       lanh, giao lau 2 - chi song tren man hinh va tren phieu lam mon,
       khong co cho nao tren tem, nen ban dong goi khong bao gio thay. */
    var giua = [];
    if (m.combo) giua.push('★ ' + m.combo);
    if ((m.tc || []).length) giua.push(m.tc.join(', '));
    else if (posLaNuoc(m)) giua.push('100% đường · 100% đá');
    if (m.gc) giua.push(m.gc);
    if (d.ghi_chu) giua.push(d.ghi_chu);
    return '<div class="tem">' +
      (maApp
        ? '<div class="app">' + h(maApp) + '</div>'
        : '<div class="h">THE VAGABOND P&Acirc;TISSERIE</div>') +
      '<div class="t">' + h(m.ten) + '</div>' +
      '<div class="c">' + h(giua.join(' · ')) + '</div>' +
      '<div class="f"><span>' + h(d.bill || d.name || '') + (d.so_ban ? ' · Bàn ' + h(d.so_ban) : '') + '</span><span>' + (i + 1) + '/' + ly.length + '</span></div>' +
      '</div>';
  }).join('');
  /* Tem di ra may in TEM, khong duoc lan sang may in bill. Moi tem la mot
     trang rieng nen day ca cuon xuong QZ mot lan, QZ cat trang theo
     page-break-after cua tung the .tem. */
  await inTo('tem', 'Tem món ' + (d.bill || d.name || ''),
    temKhung('Tem món ' + (d.bill || d.name || ''), tem),
    inKho('tem').rong, 900, inW);
}


/* Khung trang in cua tem, dung chung cho ban in that va ban in thu can tem.

   Hai ban PHAI dung chung mot khung. Neu ban in thu ve mot khung rieng thi
   no chi chung minh duoc rang ban in thu can dung, con ban that thi khong. */
function temKhung(tieuDe, than, vien) {
  var k = inKho('tem');
  var rong = k.rong || 40, cao = k.cao || 30;
  var ngang = Number(k.ngang) || 0, doc = Number(k.doc) || 0;
  var xoay = Number(k.xoay) === 90;
  /* Xoay 90 do thi kho trang doi chieu, con o tem van ve theo chieu cu roi
     quay lai - de mat chu tren tem khong doi. */
  var trang = xoay ? (cao + 'mm ' + rong + 'mm') : (rong + 'mm ' + cao + 'mm');
  return '<html><head><meta charset="utf-8"><title>' + h(tieuDe) + '</title><style>' +
    '@page{size:' + trang + ';margin:0}*{margin:0;padding:0;box-sizing:border-box}' +
    'body{font-family:Arial,sans-serif;color:#000}' +
    /* Dich ngang va dich doc: chinh mot lan tren man Cai dat cho vua giay
       that, khong sua ma nguon. Dung padding chu khong dung transform vi
       transform hay bi driver may in bo qua luc in. */
    '.tem{width:' + rong + 'mm;height:' + cao + 'mm;' +
    'padding:' + (1.5 + doc) + 'mm ' + (2 - ngang) + 'mm ' + (1.5 - doc) + 'mm ' + (2 + ngang) + 'mm;' +
    'page-break-after:always;overflow:hidden;display:flex;flex-direction:column' +
    (vien ? ';outline:.2mm solid #000;outline-offset:-.2mm' : '') +
    (xoay ? ';transform:rotate(90deg);transform-origin:' + (cao / 2) + 'mm ' + (cao / 2) + 'mm' : '') + '}' +
    '.h{font-size:6.5px;text-align:center;letter-spacing:.06em}' +
    '.app{font-size:10px;font-weight:bold;text-align:center;background:#000;color:#fff;padding:.6mm 0;line-height:1.1}' +
    '.t{font-size:11px;font-weight:bold;text-align:center;line-height:1.15;margin-top:.5mm;flex:1;display:flex;align-items:center;justify-content:center}' +
    '.c{font-size:8px;text-align:center;line-height:1.2}' +
    '.f{display:flex;justify-content:space-between;font-size:7.5px;margin-top:.5mm;font-weight:bold}' +
    '</style></head><body>' + than +
    '</body></html>';
}


/* In thu can tem: hai tem co vien bao quanh dung mep giay.

   Nhin mot cai la biet lech bao nhieu: vien in ra khong trung mep giay thi
   do dung khoang ho roi go vao hai o dich ngang va dich doc. Khong phai
   doan, khong phai deploy lai. */
async function posInTemThu() {
  var k = inKho('tem');
  var inW = inMoCuaSoNeuCan('tem');
  if (inW === 'chan') return;
  var mot = '<div class="tem">' +
    '<div class="h">CĂN TEM &middot; ' + (k.rong || 40) + ' x ' + (k.cao || 30) + 'mm</div>' +
    '<div class="t">VIỀN PHẢI TRÙNG MÉP GIẤY</div>' +
    '<div class="c">lệch bao nhiêu mm thì gõ vào ô dịch ngang / dịch dọc</div>' +
    '<div class="f"><span>ngang ' + (Number(k.ngang) || 0) + '</span><span>dọc ' + (Number(k.doc) || 0) + '</span></div>' +
    '</div>';
  await inTo('tem', 'In thử căn tem', temKhung('In thử căn tem', mot + mot, 1),
    inKho('tem').rong, 900, inW);
}



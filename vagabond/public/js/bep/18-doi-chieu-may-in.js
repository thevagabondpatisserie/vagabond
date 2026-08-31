/* ---------- Doi chieu hoa don mua (Uyen 12/08/2026) ----------

   Uyen noi phieu xong bam Luu ma trang thai khong doi, vi con thieu nut
   Gui nam o cho khac tren man Desk. Man nay gop hai buoc thanh mot nut. */
var dcmNgay = 60, dcmNhom = '', dcmTim = '', dcmPhieu = [], dcmSs = null;

async function scrDoiChieuMua() {
  frame('Đối chiếu hoá đơn mua', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc hoá đơn...</div></div>');
  var kq;
  try { kq = await api('vagabond.doi_chieu_mua.danh_sach', { so_ngay: dcmNgay, nhom: dcmNhom, tu_khoa: dcmTim }); }
  catch (e) {
    frame('Đối chiếu hoá đơn mua', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  var ds = kq.hd || [];

  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">ĐỐI CHIẾU HOÁ ĐƠN MUA · ' + ngayNgan(kq.tu) + ' - ' + ngayNgan(kq.den) + '</div>' +
    '<div style="font-size:13.5px;color:#374151;line-height:1.6;margin-top:4px">' +
    'Chọn một hoá đơn nhà cung cấp còn nháp, máy tìm phiếu nhập kho khớp và chỉ ra chỗ lệch. ' +
    'Một nút <b>Khớp và ghi sổ</b> làm cả hai việc: nối phiếu rồi ghi sổ.</div>' +
    mkNhacCat(kq.bi_cat, 'hoá đơn') + '</div>';

  html += '<div class="card" style="padding:10px 12px">' +
    mkChipNgay([[30, '30 ngày'], [60, '60 ngày'], [90, '3 tháng'], [365, '1 năm']], dcmNgay, 'data-dcmngay') + '</div>';
  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
    (kq.nhom || []).map(function (n) {
      var so = (kq.dem || {})[n.k] || 0;
      if (!so && n.k) return '';
      return posChipNut('data-dcmnhom="' + h(n.k) + '"', n.ic + ' ' + n.ten + ' ' + so, dcmNhom === n.k);
    }).join('')) + '</div>';
  html += mkOTim('dcmTim', dcmTim, 'Tìm theo mã phiếu, tên nhà cung cấp, số hoá đơn NCC...');

  if (!ds.length) {
    html += '<div class="card"><div class="emp" style="padding:26px"><div class="e1">🫙</div><div>Không có hoá đơn nào ở nhóm này.</div></div></div>';
  } else {
    html += '<div class="lst">' + ds.map(function (d) {
      return '<div class="shi" data-dcm="' + h(d.name) + '" style="display:flex;gap:10px;align-items:flex-start;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
        '<div style="flex:1;min-width:0"><b style="font-size:14px">' + h(d.supplier_name || d.supplier) + '</b>' +
        '<div style="font-size:12px;color:#98a2b3">' + h(d.name) + ' · ' + ngayNgan(d.posting_date) +
        (d.bill_no ? ' · HĐ NCC ' + h(d.bill_no) : '') + '</div>' +
        '<div style="margin-top:4px">' + dcmChip(d) + '</div></div>' +
        '<div style="text-align:right;white-space:nowrap"><b>' + money(d.grand_total) + '</b></div></div>';
    }).join('') + '</div>';
  }

  var b = frame('Đối chiếu hoá đơn mua', html);
  b.onclick = function (e) {
    var t = e.target.closest('[data-dcmngay]');
    if (t) { dcmNgay = parseInt(t.getAttribute('data-dcmngay'), 10); return go(scrDoiChieuMua, true); }
    t = e.target.closest('[data-dcmnhom]');
    if (t) { dcmNhom = t.getAttribute('data-dcmnhom'); return go(scrDoiChieuMua, true); }
    t = e.target.closest('[data-dcm]');
    if (t) { var nm = t.getAttribute('data-dcm'); dcmPhieu = []; dcmSs = null; return go(function () { scrDcmXem(nm); }); }
  };
  var o = document.getElementById('dcmTim');
  if (o) o.onchange = function () { dcmTim = o.value; go(scrDoiChieuMua, true); };
}

function dcmChip(d) {
  var the = function (bg, fg, chu) {
    return '<span style="display:inline-block;background:' + bg + ';color:' + fg + ';font-size:12px;font-weight:700;border-radius:999px;padding:3px 10px;margin:2px 5px 0 0;white-space:nowrap">' + chu + '</span>';
  };
  if (d.nhom === 'xong') return the('#dcfce7', '#166534', '✅ Đã ghi sổ');
  if (d.nhom === 'huy') return the('#fee2e2', '#991b1b', '🚫 Đã huỷ');
  if (d.nhom === 'cho_ghi_so') return the('#dbeafe', '#1e40af', '📒 Đã nối phiếu, chờ ghi sổ');
  if (d.nhom === 'khong_thay') return the('#f3f4f6', '#4b5563', '❓ Không thấy phiếu nhập nào');
  if (d.nhom === 'lech') {
    return the('#fee2e2', '#991b1b', '⚠️ Lệch ' + money(Math.abs(d.lech || 0)) + ' đ') +
      the('#f3f4f6', '#4b5563', d.so_phieu_goi_y + ' phiếu gợi ý');
  }
  return the('#fef3c7', '#92400e', '🔍 Chờ đối chiếu') + the('#f3f4f6', '#4b5563', (d.so_phieu_goi_y || 0) + ' phiếu gợi ý');
}

async function scrDcmXem(name) {
  frame('Đối chiếu ' + name, '<div class="emp"><div class="e1">⏳</div></div>');
  var kq;
  try { kq = await api('vagabond.doi_chieu_mua.xem', { name: name }); }
  catch (e) { frame('Đối chiếu', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không đọc được') + '</div></div>'); return; }
  var d = kq.hd || {};
  var gy = kq.goi_y || [];

  /* Lan dau mo: tick san. Hoa don da noi phieu tu truoc thi tick DUNG may
     phieu do, chua noi gi thi tick phieu may chấm điểm cao nhất. Người
     dùng vẫn bỏ tick hoặc chọn thêm phiếu khác được. */
  if (!dcmPhieu.length) {
    if ((kq.phieu_da_noi || []).length) dcmPhieu = kq.phieu_da_noi.slice();
    else if (gy.length) dcmPhieu = [gy[0].name];
  }

  async function veSoSanh() {
    var o = document.getElementById('dcmSs');
    if (!o) return;
    if (!dcmPhieu.length) { o.innerHTML = '<div class="card" style="padding:14px;font-size:13px;color:#6b7280">Chọn ít nhất một phiếu nhập để đối chiếu.</div>'; return; }
    o.innerHTML = '<div class="card" style="padding:14px;font-size:13px;color:#6b7280">Đang đối chiếu...</div>';
    try { dcmSs = await api('vagabond.doi_chieu_mua.so_sanh', { name: name, phieu: JSON.stringify(dcmPhieu) }); }
    catch (e) { o.innerHTML = '<div class="card" style="padding:14px;font-size:13px;color:#b3261e">' + h((e && e.message) || 'Không đối chiếu được') + '</div>'; return; }
    var s = dcmSs;
    var html = '<div class="card" style="padding:13px 14px;background:' + (s.khop ? '#f0fdf4' : '#fffbeb') + ';border:1.5px solid ' + (s.khop ? '#86efac' : '#fcd34d') + '">' +
      '<div style="display:flex;justify-content:space-between"><span style="font-size:13px;color:#374151">Tiền hàng trên hoá đơn</span><b>' + money(s.tien_hd) + ' đ</b></div>' +
      '<div style="display:flex;justify-content:space-between;margin-top:4px"><span style="font-size:13px;color:#374151">Tiền hàng trên phiếu nhập</span><b>' + money(s.tien_pnk) + ' đ</b></div>' +
      '<div style="display:flex;justify-content:space-between;margin-top:6px;padding-top:6px;border-top:1px solid rgba(0,0,0,.08)">' +
      '<b style="font-size:13.5px;color:' + (s.khop ? '#15803d' : '#92400e') + '">' + (s.khop ? '✅ Khớp' : '⚠️ Lệch') + '</b>' +
      '<b style="color:' + (s.khop ? '#15803d' : '#92400e') + '">' + (s.lech_tien ? money(s.lech_tien) + ' đ' : '0 đ') + '</b></div>' +
      (s.khop ? '' : '<div style="font-size:12px;color:#92400e;margin-top:6px;line-height:1.5">Lệch dưới ' + money(s.nguong_lech) + ' đ thì máy vẫn coi là khớp, vì đó thường là làm tròn thuế.</div>') +
      '</div>';

    html += '<div class="sec">Từng món</div><div class="card">';
    /* Tu v315 moi con so deu kem DON VI, va lech don vi duoc noi rieng ra.
       Truoc do man nay in "Hoa don 4 x 280.000" canh "Phieu nhap 4 x 161.000"
       roi ket luan chi lech gia, trong khi mot ben la 4 gram con ben kia la
       4 tui tuc 4.000 gram. Cai sai nguy hiem nhat lai la cai khong ai thay. */
    (s.dong || []).forEach(function (r) {
      var lechDvt = !!r.lech_dvt;
      /* Cung so luong ma khac cai ten don vi thi KHONG phai loi: luc noi may
         tu doi ten dong hoa don theo phieu nhap. Van noi cho nguoi ta biet,
         vi nhin hai cot thay "Goi" canh "Kg" la de tuong minh go nham. */
      var khacTen = !!r.khac_ten_dvt;
      var lech = lechDvt || Math.abs(r.lech_sl) > 0.0001 || Math.abs(r.lech_gia) > 0.005 || !r.co_phieu;
      html += '<div style="padding:10px 14px;border-bottom:1px solid #f2f4f7;background:' + (lech ? '#fef2f2' : '#fff') + '">' +
        '<div style="font-size:13.5px;font-weight:600">' + h(r.item_name || r.item_code) + '</div>' +
        '<div style="display:flex;justify-content:space-between;gap:10px;font-size:12px;color:#6b7280;margin-top:3px">' +
        '<span>Hoá đơn ' + num(r.sl_hd) + ' ' + h(r.dvt_hd || '') + ' × ' + money(r.gia_hd) + '</span>' +
        '<span>' + (r.co_phieu ? 'Phiếu nhập ' + num(r.sl_pnk) + ' ' + h(r.dvt_pnk || '') + ' × ' + money(r.gia_pnk) : '<b style="color:#b3261e">không có trong phiếu</b>') + '</span></div>' +
        (lechDvt
          ? '<div style="font-size:12px;color:#b3261e;margin-top:3px;line-height:1.55"><b>Hai bên khác đơn vị.</b> Quy về ' + h(r.dvt_kho || '') +
            ' thì hoá đơn là ' + num(r.ton_hd) + ' còn phiếu nhập là ' + num(r.ton_pnk) + '.' +
            (r.dvt_ncc ? ' Nhà cung cấp ghi đơn vị "' + h(r.dvt_ncc) + '" trên hoá đơn điện tử, hệ chưa biết đó là đơn vị nào của mình.' : '') +
            '</div>' +
            (kq.lam_duoc && r.dvt_pnk && !r.da_noi
              ? '<button class="btn gh" data-dcmdvt="' + h(String(r.idx)) + '" data-dvt="' + h(r.dvt_pnk) +
                '" style="margin:7px 0 2px;padding:7px 12px;font-size:12.5px">Đổi đơn vị dòng này thành ' + h(r.dvt_pnk) + '</button>'
              : '') +
            /* KHAI HAN DON VI CUA NHA CUNG CAP VAO MON. Nut tren chi chua
               DONG NAY; thang sau nha cung cap gui to khac la lech y nguyen.
               Nut duoi day chua CAI GOC: khai mot lan cho mon, tu do ve sau
               may doc dung don vi do. Anh Viet 31/08/2026: "anh chang hieu
               anh phai lam gi de no khong lech". Day la cai phai lam. */
            /* CHUA GAN MA HANG. Day la ca chiem gan het so dong dang hong
               (9.985 tren 11.351 dong, ngay 31/08/2026). Truoc ban nay man
               hinh bao "hang chua duoc nhap kho" - sai, va sai theo huong
               day nguoi ta di lap them phieu nhap cho lo hang da nhap roi. */
            (!r.item_code
              ? '<div style="font-size:12px;color:#b3261e;margin-top:3px;line-height:1.55">' +
                '<b>Dòng này chưa gắn mã hàng.</b> Máy chưa biết "' + h(r.item_name || '') +
                '" là món nào bên mình nên không đối chiếu với kho được.</div>' +
                (kq.lam_duoc && !r.da_noi
                  ? '<button class="btn gh" data-dcmgan="' + h(String(r.idx)) +
                    '" style="margin:7px 0 2px;padding:7px 12px;font-size:12.5px">Gắn mã hàng cho dòng này</button>'
                  : '')
              : '') +
            (kq.lam_duoc && r.dvt_ncc && r.item_code && !r.da_noi
              ? '<button class="btn gh" data-dcmkhai="' + h(r.item_code) + '" data-dvt="' + h(r.dvt_ncc) +
                '" data-slhd="' + h(String(r.sl_hd)) + '" data-slpnk="' + h(String(r.co_phieu ? r.sl_pnk : 0)) +
                '" data-hspnk="' + h(String(r.hs_pnk || 0)) + '" data-kho="' + h(r.dvt_kho || '') +
                '" style="margin:7px 0 2px 8px;padding:7px 12px;font-size:12.5px">Khai đơn vị "' + h(r.dvt_ncc) + '" cho món này</button>'
              : '')
          : (khacTen ? '<div style="font-size:12px;color:#166534;margin-top:3px;line-height:1.55">Hoá đơn ghi <b>' + h(r.dvt_hd || '') + '</b>, phiếu nhập ghi <b>' + h(r.dvt_pnk || '') + '</b>, hai bên cùng ' + num(r.ton_hd) + ' ' + h(r.dvt_kho || '') + ' nên không sao. Lúc nối máy tự đổi tên đơn vị dòng hoá đơn cho khớp phiếu nhập.</div>' : '') +
            (Math.abs(r.lech_sl) > 0.0001 ? '<div style="font-size:12px;color:#b3261e;margin-top:2px">Lệch số lượng ' + num(r.lech_sl) + ' ' + h(r.dvt_kho || '') + '</div>' : '') +
            (r.co_phieu && Math.abs(r.lech_gia) > 0.005 ? '<div style="font-size:12px;color:#b3261e;margin-top:2px">Lệch đơn giá ' + money(r.lech_gia) + ' đ mỗi ' + h(r.dvt_kho || '') + '</div>' : '')) +
        '</div>';
    });
    html += '</div>';

    /* Lech gia ma nguoi dang dung khong co quyen vuot: noi truoc o day chu
       dung de ho bam Ghi so roi moi an mot cau chan. Anh Viet 26/08/2026. */
    var lechGia = (s.dong || []).filter(function (r) { return r.co_phieu && !r.lech_dvt && Math.abs(r.lech_gia) > 0.005; }).length;
    if (lechGia && !s.vuot_lech_gia_duoc) {
      html += '<div class="card" style="padding:12px 14px;background:#fffbeb;border:1.5px solid #fcd34d">' +
        '<b style="font-size:13.5px;color:#92400e">Giá trên hoá đơn khác giá phiếu nhập</b>' +
        '<div style="font-size:12.5px;color:#7c2d12;line-height:1.65;margin-top:3px">' +
        'Hay gặp khi đặt hàng lúc còn khuyến mãi mà nhà cung cấp xuất hoá đơn sau khi hết chương trình. ' +
        'Hàng đã về kho nên tờ này vẫn ghi sổ được, nhưng phải là kế toán ghi. ' +
        'Nhờ kế toán mở màn này ghi sổ giúp, hoặc đề nghị nhà cung cấp phát hành lại hoá đơn theo giá đã đặt.' +
        '</div></div>';
    }

    if (s.so_lech_dvt) {
      html += '<div class="card" style="padding:12px 14px;background:#fef2f2;border:1.5px solid #fecaca">' +
        '<b style="font-size:13.5px;color:#b3261e">Chưa nối được vì lệch đơn vị</b>' +
        '<div style="font-size:12.5px;color:#7f1d1d;line-height:1.65;margin-top:3px">' +
        'Hoá đơn điện tử của nhà cung cấp ghi đơn vị mà hệ chưa biết, nên máy hạ về đơn vị kho. ' +
        'Tiền vẫn đúng nhưng số lượng sai, nối vào là hỏng giá vốn và tồn kho. ' +
        'Khai đơn vị đó vào bảng quy đổi của món rồi tải lại hoá đơn, hoặc sửa đơn vị dòng hoá đơn cho đúng.' +
        '</div></div>';
    }

    if ((s.thua || []).length) {
      html += '<div class="sec">Có trong phiếu nhập mà hoá đơn không nhắc tới</div>' +
        '<div class="card" style="padding:12px 14px;font-size:13px;color:#92400e;line-height:1.7">' +
        'Hàng đã về kho mà tờ hoá đơn này không tính tiền. Có thể nhà cung cấp xuất hoá đơn làm nhiều lần, cũng có thể chọn nhầm phiếu.<br>' +
        (s.thua || []).map(function (x) { return '· ' + h(x.item_name || x.item_code) + ' · ' + num(x.sl_pnk) + ' · ' + money(x.tien_pnk) + ' đ'; }).join('<br>') +
        '</div>';
    }
    o.innerHTML = html;
  }

  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">HOÁ ĐƠN NHÀ CUNG CẤP</div>' +
    '<b style="font-size:17px">' + h(d.supplier_name || d.supplier) + '</b>' +
    '<div style="font-size:12.5px;color:#6b7280;margin-top:3px">' + h(d.name) + ' · ' + ngayNgan(d.posting_date) +
    (d.bill_no ? ' · số ' + h(d.bill_no) : '') + '</div>' +
    '<div style="display:flex;justify-content:space-between;margin-top:8px"><span style="font-size:13px;color:#374151">Tổng hoá đơn</span><b style="font-size:16px">' + money(d.grand_total) + ' đ</b></div>' +
    '<div style="margin-top:6px">' + dcmChip({ nhom: kq.nhom, so_phieu_goi_y: gy.length }) + '</div></div>';

  /* To sinh tu hoa don dien tu ma tong tien lech ban goc: noi ngay o day,
     truoc khi nguoi ta ngoi doi chieu tung mon. Anh Viet 26/08/2026. */
  if (kq.hddt && kq.hddt.viec !== 'khop') {
    html += '<div class="card" style="padding:13px 14px;background:#fef2f2;border:1.5px solid #fecaca">' +
      '<b style="font-size:13.5px;color:#b3261e">Lệch so với hoá đơn điện tử của nhà cung cấp</b>' +
      '<div style="display:flex;justify-content:space-between;margin-top:6px;font-size:13px;color:#374151">' +
      '<span>Tổng trên hoá đơn điện tử ' + h(kq.hddt.so) + '</span><b>' + money(kq.hddt.tong) + ' đ</b></div>' +
      '<div style="display:flex;justify-content:space-between;margin-top:3px;font-size:13px;color:#374151">' +
      '<span>Tổng trên phiếu này</span><b>' + money(d.grand_total) + ' đ</b></div>' +
      '<div style="display:flex;justify-content:space-between;margin-top:6px;padding-top:6px;border-top:1px solid rgba(0,0,0,.08)">' +
      '<b style="color:#b3261e">Phiếu đang ' + (kq.hddt.viec === 'thieu' ? 'thiếu' : 'thừa') + '</b>' +
      '<b style="color:#b3261e">' + money(kq.hddt.lech) + ' đ</b></div>' +
      '<div style="font-size:12.5px;color:#7f1d1d;line-height:1.65;margin-top:7px">' +
      'Số trên hoá đơn điện tử là số nhà cung cấp đã gửi cơ quan thuế, còn lệch thì không ghi sổ được. ' +
      'Nguyên nhân hay gặp: có người bấm nút <b>Nối phiếu nhập kho</b> bên màn quản trị, nút đó chép đè ' +
      'giá của phiếu nhập lên hoá đơn. Màn này thì không đụng tới giá.</div>' +
      (kq.hddt.dung_lai_duoc && kq.lam_duoc
        ? '<button class="btn" id="dcmDungLai" style="margin:9px 0 0;width:100%">Dựng lại theo hoá đơn điện tử</button>'
        : '') +
      '</div>';
  }

  if (d.docstatus === 1) {
    html += '<div class="card" style="padding:14px;background:#f0fdf4;border:1.5px solid #86efac;font-size:13.5px;color:#15803d;line-height:1.6">' +
      '✅ Hoá đơn này đã ghi sổ xong. Công nợ còn ' + money(d.outstanding_amount) + ' đ.</div>';
    frame('Đối chiếu ' + name, html);
    dcmGanDungLai(name);
    return;
  }

  if (cint0(d.update_stock)) {
    html += '<div class="card" style="padding:14px;background:#fef2f2;border:1.5px solid #fecaca;font-size:13.5px;color:#991b1b;line-height:1.6">' +
      'Hoá đơn này đang bật <b>Cập nhật tồn kho</b>. Nối thêm vào phiếu nhập nữa là hàng vào kho hai lần, nên hệ thống chưa nối được. Nhờ anh chị tắt ô đó bên Desk rồi quay lại.</div>';
    frame('Đối chiếu ' + name, html);
    dcmGanDungLai(name);
    return;
  }

  html += '<div class="sec">Phiếu nhập kho của nhà cung cấp này</div>';
  if (!gy.length) {
    html += '<div class="card" style="padding:14px;font-size:13.5px;color:#6b7280;line-height:1.7">' +
      'Không thấy phiếu nhập kho nào còn chưa được hoá đơn nào lấy, mà lại trùng món với hoá đơn này.<br>' +
      'Thường là do hàng chưa được nhập kho, hoặc phiếu nhập còn đang nháp chưa ghi sổ.</div>';
  } else {
    html += '<div class="card">' + gy.map(function (p) {
      var on = dcmPhieu.indexOf(p.name) >= 0;
      return '<div data-dcmp="' + h(p.name) + '" style="display:flex;align-items:center;gap:10px;padding:11px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer;background:' + (on ? '#f0fdfa' : '#fff') + '">' +
        '<span style="font-size:18px">' + (on ? '✅' : '⬜') + '</span>' +
        '<div style="flex:1;min-width:0"><b style="font-size:13.5px">' + h(p.name) + '</b>' +
        '<div style="font-size:11.5px;color:#98a2b3">' + ngayNgan(p.ngay) + ' · ' + p.so_mon + ' món, trùng ' + p.so_mon_trung +
        (p.da_hoa_don ? ' · đã hoá đơn ' + num(Math.round(p.da_hoa_don)) + '%' : '') + '</div></div>' +
        '<b style="white-space:nowrap;font-size:13px">' + money(p.tien) + '</b></div>';
    }).join('') + '</div>';
  }

  html += '<div id="dcmSs"></div>';

  var foot = '';

  /* KHONG CON DOI PHAI CO PHIEU GOI Y MOI VE NUT.

     Chi Dung bao 31/08/2026 "bong bi mat nut ghi so". Khong bong nhien: cau
     `if (kq.lam_duoc && gy.length)` chi ve khoi nut khi tim ra it nhat mot
     phieu nhap goi y. To nao khong co phieu nao thi ca cum nut bien mat, ke
     ca nut ghi so - trong khi chinh man hinh bao "nho ke toan ghi so thang
     to nay". Bao mot duong, khong co nut de lam duong do.

     Ngay do nhom "Khong thay phieu nhap nao" co 618 to, phan lon la xang
     dau, Grab, phi dich vu - nhung thu KHONG BAO GIO co phieu nhap. */
  if (kq.lam_duoc && !gy.length) {
    foot = kq.ghi_so_duoc
      ? '<button class="btn" id="dcmThang" style="margin:0;width:100%">✅ Ghi sổ thẳng, không nối phiếu</button>' +
        '<div style="font-size:11.5px;color:#98a2b3;margin:6px 0 10px;line-height:1.6">' +
        'Tờ này không tìm được phiếu nhập nào. Hàng không qua kho (xăng dầu, ' +
        'dịch vụ, phí ship) thì ghi sổ thẳng là đúng. Còn dòng hàng qua kho ' +
        'chưa nối phiếu thì hệ vẫn chặn.</div>'
      : '<div style="font-size:11.5px;color:#98a2b3;margin:0 0 10px;line-height:1.6">' +
        'Tờ này không tìm được phiếu nhập nào. Nếu là hàng không qua kho ' +
        '(xăng dầu, dịch vụ, phí ship) thì nhờ kế toán ghi sổ thẳng.</div>';
  } else if (kq.lam_duoc && gy.length) {
    foot = '<div style="display:flex;gap:8px">' +
      /* Ghi so la viec cua ke toan. Thu mua chi thay nut noi phieu, kem
         mot cau noi ro to hoa don di dau tiep - khong thi Uyen tuong minh
         lam thieu buoc. Chi Dung 28/08/2026 bao may tu ghi so luon khi
         Uyen noi phieu, anh Viet chot tach hai buoc. */
      (kq.ghi_so_duoc
        ? '<button class="btn gh" id="dcmNoi" style="margin:0;flex:0 0 38%">🔗 Chỉ nối phiếu</button>' +
          '<button class="btn" id="dcmXong" style="margin:0;flex:1">✅ Khớp và ghi sổ</button>'
        : '<button class="btn" id="dcmNoi" style="margin:0;flex:1">🔗 Nối phiếu, chuyển kế toán ghi sổ</button>') +
      '</div>' +
      (kq.ghi_so_duoc ? '' :
        '<div style="font-size:11.5px;color:#98a2b3;margin:-4px 0 10px;line-height:1.6">' +
        'Nối xong, tờ hoá đơn nằm ở dạng nháp trong nhóm <b>Chờ ghi sổ</b> để kế toán ghi vào sổ cái.</div>');
  }
  var b = frame('Đối chiếu ' + name, html, foot ? { footer: foot } : {});
  b.onclick = function (e) {
    /* Nut doi don vi: sua o `uom` cua dong hoa don con nhap, GIU NGUYEN so
       luong va don gia nen thanh tien khong doi mot dong. Chi so luong quy
       ve don vi kho la duoc nan lai. Anh Viet 26/08/2026. */
    var u = e.target.closest('[data-dcmdvt]');
    if (u) return dcmDoiDonVi(name, u.getAttribute('data-dcmdvt'), u.getAttribute('data-dvt'));
    var g = e.target.closest('[data-dcmgan]');
    if (g) return dcmGanMaHang(name, g.getAttribute('data-dcmgan'));
    var k = e.target.closest('[data-dcmkhai]');
    if (k) return dcmKhaiDonVi(name, k.getAttribute('data-dcmkhai'), k.getAttribute('data-dvt'),
      k.getAttribute('data-slhd'), k.getAttribute('data-slpnk'), k.getAttribute('data-hspnk'),
      k.getAttribute('data-kho'));
    var t = e.target.closest('[data-dcmp]');
    if (!t) return;
    var ma = t.getAttribute('data-dcmp');
    var i = dcmPhieu.indexOf(ma);
    if (i >= 0) dcmPhieu.splice(i, 1); else dcmPhieu.push(ma);
    go(function () { scrDcmXem(name); }, true);
  };
  dcmGanDungLai(name);
  veSoSanh();

  async function chay(ghiSo) {
    if (!dcmPhieu.length) return toast('Chọn phiếu nhập trước đã.');
    if (ghiSo && dcmSs && !dcmSs.khop) {
      var ok = await confirmSheet('Hoá đơn và phiếu nhập đang lệch',
        'Chênh ' + money(dcmSs.lech_tien) + ' đ.\nGhi sổ bây giờ là ghi công nợ và giá vốn theo con số của hoá đơn.\n\nChắc chắn thì bấm tiếp.',
        'Vẫn ghi sổ', true);
      if (!ok) return;
    }
    busy(true);
    var r;
    try { r = await api('vagabond.doi_chieu_mua.noi_phieu', { name: name, phieu: JSON.stringify(dcmPhieu), ghi_so: ghiSo ? 1 : 0 }); }
    catch (e) { busy(false); baoTin((e && e.message) || 'Không nối được'); return; }
    busy(false);
    /* Tu v362 phep noi khong con la duoc-het-hoac-khong-gi. No noi duoc dong
       nao thi noi dong do va tra ve mot cau ke ro: da noi may dong, may dong
       khong qua kho nen khong can phieu, con may dong hang chua co phieu.
       Nen hien dung cau do thay vi mot cau chung chung. */
    var cau = r.loi_nhan || '';
    if (r.da_ghi_so) {
      toast('Đã nối phiếu và ghi sổ ' + name + (cau ? '. ' + cau : ''), 5000);
    } else if ((r.con_lai || []).length) {
      /* Con dong hang chua noi: phai noi ro chu khong toast roi troi qua. */
      baoTin(cau + '\n\nMấy dòng còn lại:\n\n' + (r.con_lai || []).join('\n'));
    } else {
      toast((cau || 'Đã nối phiếu ' + name + '.') +
        (kq.ghi_so_duoc ? ' Bấm "Khớp và ghi sổ" khi muốn ghi sổ.'
                        : ' Tờ này đang chờ kế toán ghi sổ.'), 5000);
    }
    if (r.da_ghi_so) { dcmPhieu = []; dcmSs = null; return go(scrDoiChieuMua, true); }
    go(function () { scrDcmXem(name); }, true);
  }
  var n1 = document.getElementById('dcmNoi');
  if (n1) n1.onclick = function () { chay(0); };
  var n3 = document.getElementById('dcmThang');
  if (n3) n3.onclick = async function () {
    var ok = await confirmSheet('Ghi sổ thẳng tờ ' + name,
      'Tờ này không nối vào phiếu nhập kho nào.\n\n' +
      'Đúng khi hàng không qua kho: xăng dầu, dịch vụ, phí ship, văn phòng phẩm.\n\n' +
      'Nếu có dòng hàng thật đáng lẽ phải qua kho thì hệ sẽ chặn và nói rõ dòng nào.',
      'Ghi sổ', false);
    if (!ok) return;
    busy(true);
    try {
      var r = await api('vagabond.doi_chieu_mua.ghi_so_thang', { name: name });
      busy(false);
      toast((r && r.loi_nhan) || ('Đã ghi sổ ' + name), 5000);
      dcmPhieu = []; dcmSs = null;
      go(scrDoiChieuMua, true);
    } catch (e) { busy(false); baoTin((e && e.message) || 'Không ghi sổ được'); }
  };
  var n2 = document.getElementById('dcmXong');
  if (n2) n2.onclick = function () { chay(1); };
}

function cint0(v) { var n = parseInt(v, 10); return isNaN(n) ? 0 : n; }


/* ---------- Cai dat - May in (anh Viet 12/08/2026) ----------

   Man nay lam HAI viec, va phai noi ro cai thu ba no KHONG lam duoc:

   1. So thiet bi: ba may in iPOS o 9 Tran Cao Van, moi may mot so seri.
      De con biet may nao hong thi goi bao hanh cai nao.
   2. Kho giay theo loai phieu: app doc so nay khi in that, thay vi go
      cung 80mm trong ma nguon nhu truoc.
   3. KHONG chon duoc may in cho tung phieu. Trinh duyet khong cho ma
      nguon chi dinh may in - do la rao can bao mat cua trinh duyet chu
      khong phai thieu sot cua minh. Muon phieu chay dung may thi dat may
      in mac dinh tren tung may tinh o quay. Man hinh phai noi that cho
      nguoi dung, khong duoc de ho tuong da cau hinh xong. */
var miData = null, miDs = [], miMo = null, miMoi = 0, miSuaDuoc = 0;

async function scrMayIn() {
  frame('Máy in', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc cấu hình...</div></div>');
  try { miData = await api('vagabond.may_in.danh_sach', {}); }
  catch (e) {
    frame('Máy in', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  /* Vua doc lai tu may chu nen khong con gi chua luu. */
  S.chuaLuu = '';
  miDs = miData.may || []; miSuaDuoc = miData.sua_duoc ? 1 : 0;
  miVe();
  miVeQz();
}

/* Do QZ Tray roi thay ruot khoi tinh trang. Tach ra khoi miVe vi miVe
   duoc goi lai moi lan sua mot o, con do QZ thi cham va khong can lam
   lai theo tung nhip go. */
async function miVeQz() {
  var o = document.getElementById('qzKhoi');
  if (!o) return;
  var t;
  try { t = await inNgamTinhTrang(); }
  catch (e) { t = { co: 0, loi: (e && e.message) || 'không dò được' }; }
  if (!document.getElementById('qzKhoi')) return;
  if (t.co) {
    /* Bay ca BON loai phieu. Truoc day chi hien hoa don va tem, nen "phieu
       mon" va "chot ca" di dau thi khong ai biet, va khong ai sua duoc. */
    var dong = (miData.vai_tro || []).map(function (v) {
      var x = (t.theo_vai || {})[v.k] || {};
      return '<div style="display:flex;gap:8px;align-items:baseline;margin-top:3px">' +
        '<span style="flex:0 0 auto">' + (v.ic || '🖨') + '</span>' +
        '<span style="flex:1">' + h(v.ten) + '</span>' +
        (x.may
          ? '<b style="flex:1;text-align:right">' + h(x.may) + '</b>'
          : '<span style="flex:1;text-align:right;color:#b45309">chưa khớp máy nào</span>') +
        '</div>';
    }).join('');
    o.setAttribute('style', 'padding:12px 14px;background:#ecfdf3;border:1.5px solid #6ce9a6');
    o.innerHTML = '<b style="font-size:14px;color:#05603a">✅ Máy này đang in ngầm qua QZ Tray</b>' +
      '<div style="font-size:12.5px;color:#05603a;margin-top:4px;line-height:1.6">' +
      'Bấm In là giấy ra ngay, không hiện hộp thoại in của trình duyệt.</div>' +
      '<div style="font-size:12.5px;color:#05603a;margin-top:8px">' + dong + '</div>' +
      '<div style="font-size:11.5px;color:#3b7c60;margin-top:8px;line-height:1.55">' +
      'Máy in QZ thấy được: ' + h((t.may || []).join(', ') || 'không có') + '<br>' +
      'Dòng nào nói chưa khớp thì mở máy in đó ở danh sách dưới và chạm chọn tên.</div>';
    return;
  }
  o.setAttribute('style', 'padding:12px 14px;background:#fffbeb;border:1.5px solid #fcd34d');
  o.innerHTML = '<b style="font-size:14px;color:#92400e">Máy này đang in qua hộp thoại trình duyệt</b>' +
    '<div style="font-size:12.5px;color:#7c4a03;margin-top:4px;line-height:1.6">' +
    'Lý do: ' + h(t.loi || 'không rõ') + '.<br>' +
    'In vẫn chạy bình thường, chỉ là thu ngân phải bấm thêm một nhịp và phải đặt sẵn ' +
    'máy in mặc định trên máy tính.</div>' +
    '<div style="font-size:12.5px;color:#7c4a03;margin-top:8px;line-height:1.6">' +
    miGoY(t) + '</div>' +
    '<button class="btn gh" id="miDoQz" style="margin-top:10px">🔎 Kiểm tra QZ trên máy này</button>' +
    '<div id="miDoKq" style="font-size:12px;color:#7c4a03;margin-top:8px;line-height:1.6"></div>';
  var nut = document.getElementById('miDoQz');
  if (nut) nut.onclick = function () { miDoQzChay(); };
}

/* ---------- Chi dung viec phai lam, theo dung LOI dang gap ----------

Anh Viet 22/08/2026: da dan chung thu roi ma hop vang van bao y het, vi
dong huong dan cu chi biet noi mot cau "cai QZ Tray va dan chung thu".

Hai loi nay khac han nhau va cach chua cung khac han:

  - "Chua dan chung thu": may chu chua co chung thu. Viec o Vagabond
    Settings, lam mot lan cho ca tiem.
  - "Unable to establish connection with QZ": trinh duyet KHONG mo noi
    duong toi QZ Tray tren chinh may thu ngan. Chung thu khong lien quan gi
    o day - chung thu chi de QZ khoi hoi "Untrusted website" SAU KHI da noi
    duoc. Dan chung thu ma QZ khong chay thi van y nguyen loi nay.

Viec dua nguoi ta di sai duong o day dat lam: moi may quay la mot lan De
phai chay toi tan noi. */
function miGoY(t) {
  var loi = String((t && t.loi) || '');
  var noi_duoc = /connection|connect|websocket|refus|timeout|unable/i.test(loi);
  if (!noi_duoc && /chứng thư|chung thu/i.test(loi)) {
    return '<b>Việc cần làm:</b> dán chứng thư QZ Tray vào Vagabond Settings. ' +
      'Làm một lần cho cả tiệm, xem hướng dẫn ở project doc v256.';
  }
  if (!noi_duoc) return 'Xem hướng dẫn ở project doc v256.';
  return '<b>Đây KHÔNG phải lỗi chứng thư.</b> Chứng thư chỉ để QZ khỏi hỏi ' +
    '"Untrusted website" sau khi đã nối được. Lỗi này là trình duyệt không mở ' +
    'nổi đường tới QZ Tray trên chính máy tính này. Làm theo thứ tự:<br>' +
    '<b>1.</b> Nhìn khay đồng hồ góc phải màn hình, có biểu tượng QZ Tray không. ' +
    'Không có thì mở QZ Tray lên. Máy vừa khởi động lại thì hay quên bật.<br>' +
    '<b>2.</b> Mở tab mới, gõ <b>https://localhost:8181</b>. Báo "không kết nối được" ' +
    'tức là QZ chưa chạy, quay lại bước 1. Báo cảnh báo bảo mật thì bấm Nâng cao, ' +
    'Tiếp tục truy cập, rồi quay lại đây bấm kiểm tra.<br>' +
    '<b>3.</b> Vẫn hỏng thì bấm nút kiểm tra bên dưới rồi chụp màn gửi bộ phận kỹ thuật.';
}

/* ---------- Do thang tung cua, chi dich danh cua nao hong ----------

Thu vien QZ thu lan luot localhost roi localhost.qz.io. Hong ca hai thi no
chi tra ve dung mot cau "Unable to establish connection with QZ", khong noi
hong o dau. Ham nay thu RIENG tung cua va bao ket qua tung cai, vi hai ket
qua khac nhau chi ra hai benh khac han:

  - Ca hai deu khong noi duoc  -> QZ Tray khong chay, hoac bi tuong lua chan.
  - localhost.qz.io noi duoc, localhost thi khong -> QZ co chay, chi la
    trinh duyet chua chiu chung thu localhost. Vao https://localhost:8181
    bam chap nhan mot lan la xong.

Dung WebSocket tho chu khong qua thu vien QZ, vi thu vien nuot mat ket qua
tung cua. */
function miDoMotCua(url) {
  return new Promise(function (xong) {
    var s, kip = 0;
    var het = setTimeout(function () {
      if (kip) return;
      kip = 1;
      try { s.close(); } catch (e) { }
      xong(0);
    }, 3500);
    try { s = new WebSocket(url); } catch (e) { clearTimeout(het); return xong(0); }
    s.onopen = function () {
      if (kip) return;
      kip = 1; clearTimeout(het);
      try { s.close(); } catch (e) { }
      xong(1);
    };
    s.onerror = function () {
      if (kip) return;
      kip = 1; clearTimeout(het);
      xong(0);
    };
  });
}

async function miDoQzChay() {
  var o = document.getElementById('miDoKq');
  if (o) o.innerHTML = 'Đang thử...';
  var a = await miDoMotCua('wss://localhost:8181');
  var b = await miDoMotCua('wss://localhost.qz.io:8181');
  var ket;
  if (a || b) {
    if (a && b) {
      ket = '<b>QZ Tray đang chạy và nối được cả hai cửa.</b> Lỗi nằm ở bước sau, ' +
        'nhiều khả năng là chứng thư hoặc chữ ký. Chụp màn này gửi bộ phận kỹ thuật.';
    } else if (b) {
      ket = '<b>QZ Tray đang chạy.</b> Trình duyệt chưa chịu chứng thư của cửa ' +
        'localhost. Mở tab mới vào <b>https://localhost:8181</b>, bấm Nâng cao rồi ' +
        'Tiếp tục truy cập, xong quay lại đây tải lại trang.';
    } else {
      ket = '<b>QZ Tray đang chạy.</b> Cửa localhost.qz.io không vào được, thường ' +
        'là mạng tiệm chặn. Không sao, cửa localhost đủ dùng. Tải lại trang thử in.';
    }
  } else {
    ket = '<b>Không cửa nào trả lời, nên QZ Tray đang KHÔNG chạy trên máy này.</b> ' +
      'Mở QZ Tray lên (tìm trong Start menu), chờ biểu tượng hiện ở khay đồng hồ ' +
      'góc phải, rồi tải lại trang này. Nếu máy chưa cài thì cài QZ Tray trước, ' +
      'hướng dẫn ở project doc v256.';
  }
  if (o) {
    o.innerHTML = 'wss://localhost:8181 &rarr; ' + (a ? 'nối được' : 'không nối được') + '<br>' +
      'wss://localhost.qz.io:8181 &rarr; ' + (b ? 'nối được' : 'không nối được') + '<br><br>' + ket;
  }
}

/* Doc bon o so tren man ve mot cuc. Ve lai man thi giu nguyen so dang go,
   khong bat go lai tu dau. */
function miCtDoc() {
  var g = function (id) { var o = document.getElementById(id); return o ? Number(o.value) || 0 : 0; };
  var cu = (miData && miData.can_tem) || {};
  var o = document.getElementById('ctNgang');
  if (!o) return { ngang: Number(cu.ngang) || 0, doc: Number(cu.doc) || 0,
                   rong: Number(cu.rong) || 0, cao: Number(cu.cao) || 0, xoay: Number(cu.xoay) || 0 };
  return { ngang: g('ctNgang'), doc: g('ctDoc'), rong: g('ctRong'), cao: g('ctCao'),
           xoay: Number(cu.xoay) || 0 };
}

/* Ve lai man ma KHONG goi lai may chu: giu nguyen so dang go do. */
function scrMayIn0() { miVe(); }

function miTenVaiTro(k) {
  var ds = (miData && miData.vai_tro) || [];
  for (var i = 0; i < ds.length; i++) if (ds[i].k === k) return ds[i].ten;
  return k;
}
function miIconVaiTro(k) {
  var ds = (miData && miData.vai_tro) || [];
  for (var i = 0; i < ds.length; i++) if (ds[i].k === k) return ds[i].ic || '🖨';
  return '🖨';
}
function miTenKho(k) {
  var ds = (miData && miData.kho_giay) || [];
  for (var i = 0; i < ds.length; i++) if (ds[i].k === k) return ds[i].ten;
  return k;
}
function miTenDiem(ma) {
  var ds = (miData && miData.diem) || [];
  for (var i = 0; i < ds.length; i++) if (ds[i].ma === ma) return ds[i].ten;
  return ma || 'chưa gán điểm';
}

function miVe() {
  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">MÁY IN</div>' +
    '<div style="font-size:14px;color:#374151;line-height:1.6;margin-top:4px">' +
    'Khai từng máy in đang có ở các điểm bán, kèm số sê-ri để sau này còn biết máy nào hỏng thì gọi bảo hành cái nào. ' +
    'Khổ giấy khai ở đây được app dùng thật khi in.</div></div>';

  /* Khoi in ngam. Do THAT tren chinh may nay chu khong doc cau hinh: khai
     dung het ma QZ Tray tren may quay bi tat thi van khong in ngam duoc,
     va nguoi dung can biet dieu do o day chu khong phai luc dang tinh
     tien cho khach. scrMayIn thay ruot khoi nay sau khi do xong. */
  html += '<div class="card" id="qzKhoi" style="padding:12px 14px;background:#f8fafc;border:1.5px solid #e4e7ec">' +
    '<b style="font-size:14px;color:#344054">⏳ Đang dò QZ Tray trên máy này...</b></div>';

  html += '<div class="sec">Khổ giấy từng loại phiếu</div><div class="card">' +
    ((miData.vai_tro || []).map(function (v) {
      var may = miDs.filter(function (m) { return m.bat && (m.vai_tro || []).indexOf(v.k) >= 0; });
      return '<div style="display:flex;align-items:center;gap:11px;padding:11px 14px;border-bottom:1px solid #f2f4f7">' +
        '<div style="width:32px;flex:none;text-align:center;font-size:19px">' + (v.ic || '🖨') + '</div>' +
        '<div style="flex:1;min-width:0"><b style="font-size:14px">' + h(v.ten) + '</b>' +
        '<div style="font-size:11.5px;color:#98a2b3;margin-top:2px">' +
        (may.length ? h(may.map(function (m) { return m.ten + ' · ' + miTenKho(m.kho); }).join(' | '))
                    : '<span style="color:#b45309">chưa có máy nào nhận, in ra khổ mặc định</span>') +
        '</div></div></div>';
    }).join('')) + '</div>';

  /* Can tem: hai o so va mot nut in thu.

     De bao 19/08/2026 tem in ra bi lech khoi giay. Kho khai trong ma nguon
     la 40 x 30mm va dung dung; cai lech den tu hai lop nam giua CSS va
     giay that, la le mac dinh cua trinh duyet va phep co gian cua driver
     may in. Hai lop do khac nhau tren tung may, nen sua cung so trong ma
     nguon roi deploy la mot vong lap khong loi ra. Cho chinh tai cho, va
     cho mot ban in co vien de nhin ra lech bao nhieu. */
  var ct = (miData && miData.can_tem) || { ngang: 0, doc: 0, rong: 0, cao: 0, xoay: 0 };
  html += '<div class="sec">Căn tem</div><div class="card" style="padding:12px 14px">' +
    '<div style="font-size:12.5px;color:#374151;line-height:1.65;margin-bottom:10px">' +
    'Bấm <b>In thử căn tem</b>, máy in ra hai tem có viền bao quanh. Viền trùng mép giấy là vừa. ' +
    'Lệch sang phải thì gõ số âm vào ô dịch ngang, lệch xuống thì gõ số âm vào ô dịch dọc, ' +
    'tính bằng mi li mét. Chỉnh một lần dùng mãi.</div>' +
    '<div style="display:flex;gap:8px;margin-bottom:8px">' +
    '<div style="flex:1"><div style="font-size:11.5px;color:#6b7280;margin-bottom:3px">Dịch ngang (mm)</div>' +
    '<input class="tin" id="ctNgang" type="number" step="0.5" value="' + (Number(ct.ngang) || 0) + '"></div>' +
    '<div style="flex:1"><div style="font-size:11.5px;color:#6b7280;margin-bottom:3px">Dịch dọc (mm)</div>' +
    '<input class="tin" id="ctDoc" type="number" step="0.5" value="' + (Number(ct.doc) || 0) + '"></div></div>' +
    '<div style="display:flex;gap:8px;margin-bottom:8px">' +
    '<div style="flex:1"><div style="font-size:11.5px;color:#6b7280;margin-bottom:3px">Rộng tem (mm), 0 là theo khổ đã chọn</div>' +
    '<input class="tin" id="ctRong" type="number" step="0.5" value="' + (Number(ct.rong) || 0) + '"></div>' +
    '<div style="flex:1"><div style="font-size:11.5px;color:#6b7280;margin-bottom:3px">Cao tem (mm)</div>' +
    '<input class="tin" id="ctCao" type="number" step="0.5" value="' + (Number(ct.cao) || 0) + '"></div></div>' +
    kmHangChip(posChipNut('data-ctxoay="0"', 'Chữ nằm ngang', Number(ct.xoay) !== 90) +
               posChipNut('data-ctxoay="90"', 'Xoay 90 độ', Number(ct.xoay) === 90)) +
    '<button class="btn gh" id="ctThu" style="margin:10px 0 0;width:100%">🏷 In thử căn tem</button>' +
    (miSuaDuoc ? '<button class="btn" id="ctLuu" style="margin:8px 0 0;width:100%">💾 Lưu căn tem</button>' : '') +
    '</div>';

  /* Danh sách NHÓM THEO ĐIỂM BÁN (anh Việt 24/08/2026): mỗi điểm bán có bộ
     máy in riêng của nó, nên nhìn vào phải thấy ngay điểm nào đủ máy, điểm
     nào còn thiếu loại phiếu gì. Trước đây là một danh sách phẳng, tên điểm
     nằm lẫn trong dòng chữ nhỏ. */
  html += '<div class="sec">Máy in theo điểm bán</div>';
  if (!miDs.length) {
    html += '<div class="card" style="padding:14px;font-size:13.5px;color:#6b7280">Chưa khai máy in nào.</div>';
  } else {
    var nhom = [];
    (miData.diem || []).forEach(function (x) { nhom.push({ ma: x.ma, ten: x.ten, may: [] }); });
    nhom.push({ ma: '', ten: 'Chưa gán điểm bán', chung: 1, may: [] });
    miDs.forEach(function (d, i) {
      var t = null;
      for (var j = 0; j < nhom.length; j++) if (nhom[j].ma === (d.diem || '')) { t = nhom[j]; break; }
      if (!t) { t = { ma: d.diem || '', ten: miTenDiem(d.diem), may: [] }; nhom.push(t); }
      t.may.push({ d: d, i: i });
    });
    nhom.forEach(function (g) {
      if (!g.may.length && !g.chung) {
        html += '<div class="card" style="padding:12px 14px;margin-bottom:10px">' +
          '<b style="font-size:14.5px">' + h(g.ten) + '</b>' +
          '<div style="font-size:12px;color:#b45309;margin-top:4px">Chưa có máy in nào cho điểm này. ' +
          'Máy chưa gán điểm bán vẫn dùng được cho mọi điểm.</div></div>';
        return;
      }
      if (!g.may.length) return;
      var thieu = [];
      ((miData && miData.vai_tro) || []).forEach(function (v) {
        var co = g.may.some(function (x) { return x.d.bat && (x.d.vai_tro || []).indexOf(v.k) >= 0 && (x.d.qz || '').trim(); });
        if (!co) thieu.push(miTenVaiTro(v.k));
      });
      html += '<div style="display:flex;align-items:baseline;justify-content:space-between;padding:2px 4px 6px">' +
        '<b style="font-size:14px;color:#0b7c93">' + h(g.ten) + '</b>' +
        '<span style="font-size:11.5px;color:' + (thieu.length ? '#b45309' : '#0f766e') + '">' +
        (thieu.length ? 'chưa có máy cho: ' + h(thieu.join(', ')) : 'đủ cả bốn loại phiếu') + '</span></div>';
      html += '<div class="card" style="margin-bottom:12px">' + g.may.map(function (x) {
        var d = x.d;
        var vt = (d.vai_tro || []).map(function (k) { return miIconVaiTro(k) + ' ' + miTenVaiTro(k); }).join(' · ');
        return '<div data-mimo="' + x.i + '" style="display:flex;align-items:center;gap:11px;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
          '<div style="width:34px;height:34px;flex:none;border-radius:10px;background:#eef2ff;display:flex;align-items:center;justify-content:center;font-size:17px">🖨</div>' +
          '<div style="flex:1;min-width:0"><b style="font-size:14.5px">' + h(d.ten) + '</b>' +
          '<div style="font-size:11.5px;color:#6b7280;margin-top:2px">' + h((d.hang ? d.hang + ' ' : '') + (d.model || '')) + ' · ' + h(miTenKho(d.kho)) +
          ((d.qz || '').trim() ? '' : ' · <span style="color:#b45309">chưa gán tên máy QZ</span>') + '</div>' +
          '<div style="font-size:11.5px;color:#98a2b3;margin-top:2px">' + (vt ? h(vt) : '<span style="color:#b45309">chưa chọn loại phiếu</span>') + '</div></div>' +
          '<span style="font-size:12px;font-weight:700;color:' + (d.bat ? '#0f766e' : '#a0a6b4') + '">' + (d.bat ? 'ĐANG DÙNG' : 'ĐÃ TẮT') + '</span>' +
          '<span style="color:#c8ccd4">›</span></div>';
      }).join('') + '</div>';
    });
  }

  var b = frame('Máy in', html, miSuaDuoc ? {
    footer: '<div style="display:flex;gap:8px">' +
      '<button class="btn gh" id="miThem" style="margin:0;flex:0 0 44%">➕ Thêm máy in</button>' +
      '<button class="btn" id="miLuu" style="margin:0;flex:1">💾 Lưu</button></div>'
  } : null);

  b.onclick = function (e) {
    var x = e.target.closest('[data-ctxoay]');
    if (x) {
      miData.can_tem = miCtDoc();
      miData.can_tem.xoay = +x.getAttribute('data-ctxoay');
      return go(scrMayIn0, true);
    }
    var t = e.target.closest('[data-mimo]');
    if (t) { miMo = +t.getAttribute('data-mimo'); miMoi = 0; go(scrMayInSua); }
  };
  /* Noi thang ngay o man danh sach, dung de nguoi dung mo tung may ra roi
     moi phat hien khong luu duoc. */
  if (!miSuaDuoc) {
    var nB = document.createElement('div');
    nB.style.cssText = 'font-size:12px;color:#92400e;background:#fffbeb;border:1px solid #fde68a;' +
      'border-radius:9px;padding:10px 12px;margin:10px 12px;line-height:1.6';
    nB.innerHTML = 'Tài khoản của anh chị <b>chỉ xem</b> được cấu hình máy in. ' +
      'Nhờ quản lý, kế toán hoặc anh Việt gán giúp một lần, gán xong thì cả tiệm dùng chung.';
    b.insertBefore(nB, b.firstChild);
  }
  var nThu = document.getElementById('ctThu');
  /* In thu bang DUNG thong so dang go tren man, chua luu cung in thu duoc.
     Bat luu truoc moi duoc thu la bat nguoi dung luu mot con so ho chua
     biet co dung khong. */
  if (nThu) nThu.onclick = function () {
    var c = miCtDoc();
    CFGBH = CFGBH || {};
    CFGBH.kho_in = CFGBH.kho_in || {};
    var t = CFGBH.kho_in.tem || { rong: 40, cao: 30 };
    CFGBH.kho_in.tem = {
      k: t.k || 'tem_40x30',
      rong: c.rong > 0 ? c.rong : (t.rong || 40),
      cao: c.cao > 0 ? c.cao : (t.cao || 30),
      ngang: c.ngang, doc: c.doc, xoay: c.xoay,
      css: '', cuon: 0
    };
    CFGBH.kho_in.tem.css = CFGBH.kho_in.tem.rong + 'mm ' + CFGBH.kho_in.tem.cao + 'mm';
    posInTemThu();
  };
  var nCtLuu = document.getElementById('ctLuu');
  if (nCtLuu) nCtLuu.onclick = async function () {
    var c = miCtDoc();
    busy(true);
    try {
      miData = await api('vagabond.may_in.luu_can_tem', c);
      miDs = miData.may || [];
      busy(false);
      toast('Đã lưu căn tem. Tải lại app ở quầy để máy in nhận số mới.', 4500);
      go(scrMayIn0, true);
    } catch (e2) { busy(false); baoTin((e2 && e2.message) || 'Không lưu được căn tem'); }
  };
  var nt = document.getElementById('miThem');
  if (nt) nt.onclick = function () {
    miDs.push({ ma: 'MI' + (miDs.length + 1), ten: '', hang: 'iPOS.VN', model: '', loai: '', so_seri: '',
      giao_tiep: '', nguon_dien: '', xuat_xu: '', diem: '', vai_tro: [], kho: '80mm', ghi_chu: '', bat: 1 });
    miMo = miDs.length - 1; miMoi = 1;
    go(scrMayInSua);
  };
  var nl = document.getElementById('miLuu');
  if (nl) nl.onclick = function () { miLuu(); };
}

/* ---------- Gan ten may in that cho tung may trong so ----------

   De khong dung ban Desk (anh Viet 22/08/2026), viec gan ten may in phai
   lam duoc ngay tren may quay. Hai ham nay lo phan kho nhat: nguoi dung
   khong phai go dung tung ky tu cai ten dai loong ngoong ma Windows dat cho
   may in, chi cham vao ten QZ doc duoc la xong. */

/* Vai manh ten NGAN hon de goi y. Ten day du chua so cong USB hoac duoi
   "(Copy 1)", doi day cam la lech; manh ngan thi song sot. */
function miQzGoiY(ten) {
  var day = String(ten || '').trim();
  var t = day.replace(/\s*\(.*?\)\s*$/, '').trim();
  var ra = [];
  if (t && t !== day) ra.push(t);
  var tu = t.split(/\s+/).filter(Boolean);
  if (tu.length > 1) ra.push(tu.slice(0, 2).join(' '));
  if (tu.length && tu[0].length >= 3) ra.push(tu[0]);
  return ra.filter(function (x, i) { return x && ra.indexOf(x) === i && x !== day; });
}

/* May in nao tren may tinh NAY dang khop voi manh dang go. */
function miQzKhop(manh) {
  var m = String(manh || '').toLowerCase().trim();
  if (!m) return [];
  var ds = (typeof IN_QZ !== 'undefined' && IN_QZ.may) ? IN_QZ.may : [];
  return ds.filter(function (t) { return String(t).toLowerCase().indexOf(m) >= 0; });
}

function scrMayInSua() {
  var d = (miDs || [])[miMo];
  if (!d) return go(scrMayIn, true);
  var o = function (nhan, id, gt, mo) {
    return '<div style="padding:11px 14px;border-bottom:1px solid #f2f4f7">' +
      '<div style="font-size:12px;color:#6b7280;margin-bottom:4px">' + nhan + '</div>' +
      '<input class="tin" id="' + id + '" value="' + h(gt == null ? '' : gt) + '" style="width:100%;margin:0">' +
      (mo ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:4px;line-height:1.5">' + mo + '</div>' : '') + '</div>';
  };

  var html = '<div class="card">' +
    o('Tên gọi trong nhà', 'miTen', d.ten, 'Gọi sao cho nhân viên nhận ra, ví dụ Máy in hoá đơn quầy.') +
    o('Mã máy', 'miMa', d.ma, 'Chữ in hoa không dấu và số. Mã này đi vào nhật ký nên đặt xong đừng đổi.') +
    '</div>';

  html += '<div class="sec">Điểm bán</div><div class="card" style="padding:11px 12px">' +
    kmHangChip((miData.diem || []).map(function (x) {
      return posChipNut('data-midiem="' + h(x.ma) + '"', h(x.ten), d.diem === x.ma);
    }).join('')) + '</div>';

  html += '<div class="sec">Máy này in loại phiếu nào</div><div class="card" style="padding:11px 12px">' +
    kmHangChip((miData.vai_tro || []).map(function (v) {
      return posChipNut('data-mivt="' + h(v.k) + '"', (v.ic || '🖨') + ' ' + h(v.ten), (d.vai_tro || []).indexOf(v.k) >= 0);
    }).join('')) +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:8px;line-height:1.6">' +
    'Chọn được nhiều loại. Đây là ghi nhớ cho người dùng và là chỗ app lấy khổ giấy, ' +
    'không phải lệnh điều khiển máy in.</div></div>';

  html += '<div class="sec">Khổ giấy</div><div class="card" style="padding:11px 12px">' +
    kmHangChip((miData.kho_giay || []).map(function (k) {
      return posChipNut('data-mikho="' + h(k.k) + '"', h(k.ten), d.kho === k.k);
    }).join('')) +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:8px;line-height:1.6">' +
    'Số này app dùng thật khi in. Đổi ở đây là bản in đổi theo, không phải sửa phần mềm.</div></div>';

  /* Khoi gan ten may in that. Dat NGAY SAU kho giay vi hai thu nay di voi
     nhau: kho giay quyet dinh ban in trong the nao, ten may quyet dinh no
     ra cai may nao. */
  var qzCo = (typeof IN_QZ !== 'undefined' && IN_QZ.co) ? 1 : 0;
  var qzDs = (typeof IN_QZ !== 'undefined' && IN_QZ.may) ? IN_QZ.may : [];
  var khop = miQzKhop(d.qz);
  html += '<div class="sec">Tên máy in trên máy tính ở quầy</div>' +
    '<div class="card" style="padding:11px 12px">' +
    '<input class="tin" id="miQz" value="' + h(d.qz || '') + '" placeholder="Ví dụ XP-350 hoặc TM-T82" style="width:100%;margin:0">' +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:6px;line-height:1.6">' +
    'Chỉ cần một <b>mảnh ngắn</b> của tên, không cần gõ đủ. Tên máy in trên Windows đổi ' +
    'theo cổng USB, mảnh ngắn thì sống sót qua mỗi lần cắm lại.</div>';

  if (!qzCo) {
    html += '<div style="margin-top:9px;padding:9px 11px;border-radius:9px;background:#fffbeb;' +
      'border:1px solid #fcd34d;font-size:12.5px;color:#7c4a03;line-height:1.6">' +
      'Máy tính này chưa nối được QZ Tray nên chưa dò được tên máy in. ' +
      'Gõ tay cũng được, nhưng ra đúng quầy rồi chạm chọn thì chắc hơn.</div>';
  } else if (!qzDs.length) {
    html += '<div style="margin-top:9px;font-size:12.5px;color:#b45309">QZ Tray không thấy máy in nào trên máy tính này.</div>';
  } else {
    html += '<div style="font-size:11.5px;color:#6b7280;margin:10px 0 6px">CHẠM MỘT TÊN QZ ĐANG THẤY</div>' +
      kmHangChip(qzDs.map(function (t) {
        return posChipNut('data-miqz="' + h(t) + '"', h(t), String(d.qz || '') === t);
      }).join(''));
    var gy = [];
    qzDs.forEach(function (t) { gy = gy.concat(miQzGoiY(t)); });
    gy = gy.filter(function (x, i) { return gy.indexOf(x) === i; });
    if (gy.length) {
      html += '<div style="font-size:11.5px;color:#6b7280;margin:10px 0 6px">HOẶC LẤY MẢNH NGẮN HƠN</div>' +
        kmHangChip(gy.map(function (t) {
          return posChipNut('data-miqz="' + h(t) + '"', h(t), String(d.qz || '') === t);
        }).join(''));
    }
  }

  if (d.qz) {
    html += '<div style="margin-top:10px;padding:9px 11px;border-radius:9px;font-size:12.5px;line-height:1.6;' +
      (khop.length === 1
        ? 'background:#ecfdf3;border:1px solid #6ce9a6;color:#05603a">✅ Trên máy tính này đang khớp đúng một máy: <b>' + h(khop[0]) + '</b>'
        : khop.length > 1
          ? 'background:#fffbeb;border:1px solid #fcd34d;color:#7c4a03">⚠️ Mảnh này khớp ' + khop.length + ' máy: <b>' + h(khop.join(', ')) + '</b>. Máy sẽ lấy cái đầu tiên. Gõ dài thêm cho khỏi nhầm.'
        : 'background:#fef2f2;border:1px solid #fecaca;color:#b3261e">Chưa khớp máy in nào trên máy tính này. Nếu đang ngồi ở quầy khác thì bình thường, còn ngồi ngay quầy đó thì kiểm lại tên.') +
      '</div>';
  }
  html += '</div>';

  html += '<div class="sec">Thông số thiết bị</div><div class="card">' +
    o('Hãng', 'miHang', d.hang, '') +
    o('Model', 'miModel', d.model, '') +
    o('Loại máy', 'miLoai', d.loai, 'Ví dụ Thermal Receipt Printer hay Thermal Barcode Printer.') +
    o('Số sê-ri', 'miSeri', d.so_seri, 'Đọc trên tem dán dưới đáy máy. Cần khi gọi bảo hành.') +
    o('Giao tiếp', 'miGiaoTiep', d.giao_tiep, 'Ví dụ USB, Serial, Ethernet.') +
    o('Nguồn điện', 'miNguon', d.nguon_dien, '') +
    o('Xuất xứ', 'miXuatXu', d.xuat_xu, '') +
    o('Ghi chú', 'miGhiChu', d.ghi_chu, '') +
    '</div>';

  html += '<div class="card" style="padding:11px 12px">' +
    kmHangChip(posChipNut('data-mibat="1"', d.bat ? '● Đang dùng' : '○ Đã tắt', !!d.bat)) +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px;line-height:1.6">' +
    'Tắt thì máy này không còn nhận loại phiếu nào nữa, nhưng thông số vẫn giữ lại để tra sau.</div></div>';

  var b = frame(d.ten || 'Máy in mới', html, miSuaDuoc ? {
    footer: '<div style="display:flex;gap:8px">' +
      '<button class="btn gh" id="miBo" style="margin:0;flex:0 0 34%;color:#b3261e;border-color:#fecaca">Bỏ máy này</button>' +
      '<button class="btn" id="miLuu2" style="margin:0;flex:1">💾 Lưu</button></div>'
  } : null);

  b.onclick = function (e) {
    /* KHOA HAN phan cham chon khi khong du vai (v294, anh Viet 24/08/2026).

       Bay giao dien cua ban cu: doan gan su kien nay nam TRUOC dong
       `if (!miSuaDuoc) return;` o duoi, nen nguoi khong du vai van cham chon
       duoc moi chip, man van doi mau y nhu da cau hinh xong, ma chan man
       khong co bat ky nut Luu nao. Cham xong roi roi man la mat sach,
       khong mot loi canh bao.

       Ban De o quay dinh dung ca nay ngay 24/08: bao "khong co nut gi de
       luu setting ca". Nay cham vao la duoc noi thang ai gan giup duoc. */
    if (!miSuaDuoc) {
      return baoTin('Tài khoản của anh chị chỉ xem được cấu hình máy in, ' +
        'chưa sửa được. Nhờ quản lý, kế toán hoặc anh Việt mở màn này gán ' +
        'giúp một lần, gán xong thì cả tiệm dùng chung.', 'Chưa sửa được');
    }
    /* Cham mot chip la co thay doi chi nam trong bo nho, chua xuong may
       chu. Dat cau hoi de nut lui phai hoi truoc khi bo di. */
    S.chuaLuu = 'Cấu hình máy in đang sửa dở, chưa bấm Lưu. Rời màn này là mất.';
    var t = e.target.closest('[data-midiem]');
    if (t) { miDoc(); d.diem = t.getAttribute('data-midiem'); return go(scrMayInSua, true); }
    t = e.target.closest('[data-mivt]');
    if (t) {
      miDoc();
      var k = t.getAttribute('data-mivt');
      d.vai_tro = d.vai_tro || [];
      var i = d.vai_tro.indexOf(k);
      if (i >= 0) d.vai_tro.splice(i, 1); else d.vai_tro.push(k);
      /* Chon in tem thi tu nhay sang kho tem, va nguoc lai: khoi de nguoi
         dung luu xong moi an loi tu may chu. */
      var laTem = d.vai_tro.indexOf('tem') >= 0;
      var kho = (miData.kho_giay || []).filter(function (x) { return x.k === d.kho; })[0] || {};
      if (laTem && kho.cuon) d.kho = 'tem_40x30';
      if (!laTem && d.vai_tro.length && !kho.cuon) d.kho = '80mm';
      return go(scrMayInSua, true);
    }
    t = e.target.closest('[data-mikho]');
    if (t) { miDoc(); d.kho = t.getAttribute('data-mikho'); return go(scrMayInSua, true); }
    t = e.target.closest('[data-miqz]');
    if (t) { miDoc(); d.qz = t.getAttribute('data-miqz'); return go(scrMayInSua, true); }
    if (e.target.closest('[data-mibat]')) { miDoc(); d.bat = d.bat ? 0 : 1; return go(scrMayInSua, true); }
  };
  /* Chua do QZ lan nao (vao thang man nay chu khong qua man danh sach) thi
     do roi ve lai, de danh sach ten may in hien ra cho ma cham. */
  if (typeof inNgamDo === 'function' && typeof IN_QZ !== 'undefined' && !IN_QZ.do_roi) {
    inNgamDo().then(function () {
      if (miMo === (miDs || []).indexOf(d)) go(scrMayInSua, true);
    }).catch(function () { });
  }

  if (!miSuaDuoc) return;
  document.getElementById('miLuu2').onclick = function () { miDoc(); miLuu(); };
  document.getElementById('miBo').onclick = async function () {
    var ok = await confirmSheet('Bỏ máy in ' + (d.ten || 'mới') + '?',
      'Thông số máy này sẽ mất khỏi danh sách. Muốn giữ lại để tra sau thì tắt nó đi thay vì bỏ.', 'Bỏ máy này', true);
    if (!ok) return;
    /* Đánh dấu XOÁ thay vì cắt khỏi mảng: máy chủ nay trộn theo mã máy nên
       một máy chỉ biến mất khi có cờ này, còn máy không gửi lên thì được giữ
       nguyên. Nhờ vậy hai người cùng sửa hai máy khác nhau không xoá của
       nhau (anh Việt 24/08/2026). */
    miDs[miMo].xoa = 1;
    miLuu(1);
  };
}

function miDoc() {
  var d = (miDs || [])[miMo];
  if (!d) return;
  var v = function (id) { var e = document.getElementById(id); return e ? String(e.value).trim() : null; };
  var g;
  if ((g = v('miTen')) !== null) d.ten = g;
  if ((g = v('miMa')) !== null) d.ma = g.toUpperCase();
  if ((g = v('miHang')) !== null) d.hang = g;
  if ((g = v('miModel')) !== null) d.model = g;
  if ((g = v('miLoai')) !== null) d.loai = g;
  if ((g = v('miSeri')) !== null) d.so_seri = g;
  if ((g = v('miGiaoTiep')) !== null) d.giao_tiep = g;
  if ((g = v('miNguon')) !== null) d.nguon_dien = g;
  if ((g = v('miXuatXu')) !== null) d.xuat_xu = g;
  if ((g = v('miGhiChu')) !== null) d.ghi_chu = g;
  if ((g = v('miQz')) !== null) d.qz = g;
}

async function miLuu(veDanhSach) {
  busy(true);
  try {
    miData = await api('vagabond.may_in.luu', { may: JSON.stringify(miDs) });
    miDs = miData.may || []; miSuaDuoc = miData.sua_duoc ? 1 : 0;
    S.chuaLuu = '';
    /* Doi kho giay xong thi cau hinh ban hang cu van con trong bo nho, ban
       in tiep theo se ra kho cu. Xoa di de lan in sau doc lai. */
    CFGBH = null;
    busy(false);
    toast('Đã lưu máy in');
    miMoi = 0;
    go(scrMayIn, veDanhSach ? true : true);
  } catch (e) {
    busy(false);
    baoTin((e && e.message) || 'Không lưu được');
  }
}


/* ---------- Ho so mot khach hang (anh Viet 12/08/2026) ----------

   Truoc day bam vao mot khach chi hien mot bang gan hang, khong co thong
   tin gi de cham soc ho. Nay la mot man day du: lien he sua duoc ngay tai
   cho, lich su mua ca ben he nay lan ben Fabi, tinh trang the thanh vien
   va con bao nhieu tien nua thi len hang.

   Cac o mang tu Fabi sang de CHI DOC: sua chung khong lam khach duoc cham
   soc tot hon, ma lai mat dau vet so lieu cu. */
var khMa = '', khHs = null, khSua = null, khDsHang = [];

async function scrKhachChiTiet() {
  if (!khMa) return go(scrKhachHang, true);
  frame('Khách hàng', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc hồ sơ khách...</div></div>');
  try {
    khHs = await api('vagabond.khach_hang.ho_so', { khach: khMa });
    khDsHang = (await api('vagabond.khach_hang.ds_hang', {})).hang || [];
  } catch (e) {
    frame('Khách hàng', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không đọc được') + '</div></div>');
    return;
  }
  khSua = null;
  khCtVe();
}

function khO(nhan, gt, phu) {
  return '<div style="display:flex;justify-content:space-between;gap:12px;padding:9px 0;border-bottom:1px solid #f4f5f8">' +
    '<span style="color:#6b7280;font-size:13px;flex:0 0 42%">' + nhan + '</span>' +
    '<span style="flex:1;min-width:0;text-align:right;font-size:13.5px' + (gt ? ';font-weight:600' : ';color:#c3c8d4') + '">' +
    (gt ? h(gt) : 'chưa có') + (phu ? '<div style="font-size:11.5px;color:#98a2b3;font-weight:400;margin-top:2px">' + h(phu) + '</div>' : '') +
    '</span></div>';
}

function khNgay(s) { return s ? posNgayVn(String(s).slice(0, 10)) : ''; }

function khCtVe() {
  var d = khHs.khach || {}, lh = khHs.lien_he || {}, the = khHs.the || {};
  var hg = khHs.hang || {}, mn = khHs.mua_next || {}, mf = khHs.mua_fabi || {};

  /* The thanh vien in NGUYEN TAM, khong cat. Ban cu dat max-height 132px
     kem object-fit cover nen anh 1012x638 bi xen mat dai duoi - dung cho
     co ten hang tren the (anh Viet 13/08/2026). Nay de the o giua mot
     khung co dem, giu dung ti le 1.586:1, ten hang doc o dong chu ben
     duoi the. */
  var html = '<div class="card" style="padding:0;overflow:hidden">' +
    (hg.anh
      ? '<div style="padding:14px 14px 0;background:#fafbfc"><img src="' + h(hg.anh) + '" alt="' + h(hg.ten_hang || '') +
        '" style="width:100%;max-width:330px;aspect-ratio:1.586;object-fit:contain;display:block;margin:0 auto;border-radius:9px"></div>'
      : '') +
    '<div style="padding:13px 14px">' +
    '<div style="font-size:18px;font-weight:800">' + h(d.customer_name || khMa) + '</div>' +
    '<div style="font-size:12.5px;color:#6b7280;margin-top:3px">' +
    '<span style="font-family:ui-monospace,monospace">' + h(khMa) + '</span>' +
    (lh.sdt ? ' · ' + h(lh.sdt) : '') + ' · ' + h(d.customer_group || 'chưa gắn nhóm') + '</div>' +
    (hg.name
      ? '<div style="font-size:12.5px;color:#0f766e;font-weight:700;margin-top:5px">' + h(hg.ten_hang || hg.name) +
        (hg.giam_gia ? ' · giảm ' + money(hg.giam_gia) + '%' : '') +
        (hg.tich_diem ? ' · tích ' + money(hg.tich_diem) + '%' : '') + '</div>'
      : '<div style="font-size:12.5px;color:#b45309;font-weight:700;margin-top:5px">Chưa xếp hạng</div>') +
    '</div></div>';

  if (khHs.la_gop) {
    html += '<div class="card" style="padding:12px 14px;background:#fffbeb;border:1.5px solid #fcd34d;font-size:13px;color:#92400e;line-height:1.6">' +
      'Đây là giỏ dùng chung cho khách vãng lai, không phải một người thật. Không gắn hạng và không tích điểm cho bản ghi này.</div>';
  }

  /* --- The thanh vien --- */
  html += '<div class="sec">Thẻ thành viên</div><div class="card" style="padding:4px 14px 10px">' +
    khO('Điểm hiện có', money(the.diem || 0) + ' điểm') +
    khO('Chi tiêu trong kỳ xét', money(the.tien_ky || 0) + ' đ', (the.so_thang || 12) + ' tháng gần nhất, đã cộng phần tiêu bên Fabi') +
    khO('Hạng đủ điều kiện', the.hang_du_dieu_kien || '', the.hang_du_dieu_kien && hg.name && the.hang_du_dieu_kien !== hg.name ? 'khác hạng đang gắn' : '') +
    (the.hang_tiep
      ? khO('Còn thiếu để lên ' + the.hang_tiep, money(the.con_thieu) + ' đ')
      : khO('Hạng tiếp theo', '', 'đang ở hạng cao nhất theo chi tiêu')) +
    khO('Hạng tính từ ngày', khNgay(d.vgb_hang_tu)) +
    '</div>';

  /* --- Gan hang --- */
  if (!khHs.la_gop) {
    html += '<div class="card" style="padding:11px 12px">' +
      '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin-bottom:8px">GẮN HẠNG</div>' +
      kmHangChip(khDsHang.map(function (x) {
        return posChipNut('data-khsh="' + h(x.name) + '"',
          hangChipAnh(x, 16) + h(x.ten_hang) + (x.giam_gia ? ' −' + money(x.giam_gia) + '%' : ''), (d.vgb_hang || '') === x.name);
      }).join('') + ((d.vgb_hang || '') ? posChipNut('data-khsh=""', '✕ Bỏ hạng', false, 1) : '')) + '</div>';
  }

  /* --- Lien he: sua duoc ngay tai cho --- */
  html += '<div class="sec">Liên hệ</div><div class="card" style="padding:4px 14px 10px">' +
    khO('Số điện thoại', lh.sdt) +
    khO('Email', lh.email) +
    khO('Sinh nhật', khNgay(d.vgb_sinh_nhat)) +
    khO('Giới tính', d.gender === 'Male' ? 'Nam' : (d.gender === 'Female' ? 'Nữ' : '')) +
    khO('Địa chỉ', d.vgb_dia_chi_cu) +
    khO('Zalo user id', d.vgb_zalo_id) +
    khO('Nhãn', d.vgb_tags) +
    '<div style="padding-top:10px"><button class="btn gh" id="khSuaTt" style="margin:0;width:100%">✏️ Sửa thông tin liên hệ</button></div>' +
    '</div>';

  /* --- Mua hang ben he nay --- */
  html += '<div class="sec">Mua hàng trên hệ này</div><div class="card" style="padding:4px 14px 10px">' +
    khO('Số hoá đơn', money(mn.so_don || 0) + ' hoá đơn') +
    khO('Tổng đã chi', money(mn.tien || 0) + ' đ') +
    khO('Trung bình mỗi hoá đơn', mn.so_don ? money(Math.round(mn.trung_binh)) + ' đ' : '') +
    khO('Mua lần đầu', khNgay(mn.lan_dau)) +
    khO('Mua lần cuối', khNgay(mn.lan_cuoi)) +
    '</div>';

  /* --- Mua hang ben Fabi --- */
  if (mf.tien || mf.so_don || mf.lan_cuoi) {
    html += '<div class="sec">Lịch sử bên Fabi</div><div class="card" style="padding:4px 14px 10px">' +
      khO('Số hoá đơn', money(mf.so_don || 0) + ' hoá đơn') +
      khO('Tổng đã chi', money(mf.tien || 0) + ' đ', 'số này được cộng vào khi xét hạng') +
      khO('Trung bình mỗi hoá đơn', mf.so_don ? money(Math.round(mf.trung_binh)) + ' đ' : '') +
      khO('Mua lần đầu', khNgay(mf.lan_dau)) +
      khO('Mua lần cuối', khNgay(mf.lan_cuoi)) +
      khO('Cửa hàng hay mua', mf.cua_hang) +
      khO('Đăng ký thành viên', khNgay(d.vgb_ngay_dang_ky), d.vgb_kenh_dang_ky ? 'qua ' + d.vgb_kenh_dang_ky : '') +
      '</div>';
  }

  /* --- Hoa don gan day --- */
  var don = khHs.don_gan_day || [];
  html += '<div class="sec">Hoá đơn gần đây</div><div class="card" style="padding:6px 14px">';
  if (!don.length) {
    html += '<div style="padding:16px 0;color:#a0a6b4;text-align:center">Chưa có hoá đơn nào trên hệ này.</div>';
  } else {
    html += don.map(function (o) {
      return '<div style="display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid #f4f5f8">' +
        '<div style="flex:1;min-width:0"><div style="font-size:13.5px;font-weight:600">' + h(o.name) + '</div>' +
        '<div style="font-size:11.5px;color:#98a2b3">' + posNgayVn(String(o.posting_date).slice(0, 10)) +
        (o.custom_nguon ? ' · ' + h(o.custom_nguon) : '') + (o.vgb_quay ? ' · ' + h(o.vgb_quay) : '') + '</div></div>' +
        '<b style="white-space:nowrap">' + money(o.grand_total) + ' đ</b></div>';
    }).join('');
  }
  html += '</div>';

  /* --- So diem --- */
  html += '<div class="card" style="padding:11px 12px">' +
    '<button class="btn gh" id="khSoDiem" style="margin:0;width:100%">🧾 Xem sổ điểm</button></div>';

  var b = frame(d.customer_name || 'Khách hàng', html, null);
  b.onclick = async function (e) {
    var t = e.target.closest('[data-khsh]');
    if (!t) return;
    var hgm = t.getAttribute('data-khsh');
    busy(true);
    try {
      await api('vagabond.khach_hang.dat_hang', { khach: khMa, hang: hgm });
      khHs = await api('vagabond.khach_hang.ho_so', { khach: khMa });
      busy(false);
      toast(hgm ? 'Đã xếp vào hạng ' + hgm : 'Đã bỏ hạng');
      khCtVe();
    } catch (er) { busy(false); toast((er && er.message) || 'Không đặt được hạng', 4000); }
  };
  var ns = document.getElementById('khSuaTt');
  if (ns) ns.onclick = function () { khSheetSua(); };
  var nd = document.getElementById('khSoDiem');
  if (nd) nd.onclick = function () { khSheetSoDiem(); };
}

/* Sua thong tin lien he. So dien thoai va email di vao LIEN HE chu khong
   ghi thang vao Customer - truong mobile_no cua Customer la chi doc, ghi
   thang vao do thi lan sau ai bam Luu la so bien mat. */
function khSheetSua() {
  var d = khHs.khach || {}, lh = khHs.lien_he || {};
  var f = {
    ten: d.customer_name || '', sdt: lh.sdt || '', email: lh.email || '',
    sinh_nhat: String(d.vgb_sinh_nhat || '').slice(0, 10),
    gioi_tinh: d.gender || '', dia_chi: d.vgb_dia_chi_cu || '',
    zalo: d.vgb_zalo_id || '', tags: d.vgb_tags || ''
  };
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  var o = function (nhan, id, gt, kieu, mo) {
    return '<div style="padding:10px 0;border-bottom:1px solid #f2f4f7">' +
      '<div style="font-size:12px;color:#6b7280;margin-bottom:4px">' + nhan + '</div>' +
      '<input class="tin" id="' + id + '" type="' + (kieu || 'text') + '" value="' + h(gt) + '" style="width:100%;margin:0">' +
      (mo ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:4px;line-height:1.5">' + mo + '</div>' : '') + '</div>';
  };
  box.innerHTML = '<div class="shh"><b>Sửa thông tin khách</b><div class="x">&times;</div></div>' +
    '<div style="padding:4px 14px calc(env(safe-area-inset-bottom,0px) + 14px)">' +
    o('Tên khách', 'khfTen', f.ten) +
    o('Số điện thoại', 'khfSdt', f.sdt, 'tel', 'Gõ kiểu nào cũng được, máy tự đưa về dạng 0 ở đầu.') +
    o('Email', 'khfEmail', f.email, 'email') +
    o('Sinh nhật', 'khfSn', f.sinh_nhat, 'date', 'Để trống nếu chưa biết. Đừng điền bừa, máy dùng ngày này để chúc mừng.') +
    '<div style="padding:10px 0;border-bottom:1px solid #f2f4f7">' +
    '<div style="font-size:12px;color:#6b7280;margin-bottom:6px">Giới tính</div>' +
    kmHangChip(
      posChipNut('data-khgt="Male"', 'Nam', f.gioi_tinh === 'Male') +
      posChipNut('data-khgt="Female"', 'Nữ', f.gioi_tinh === 'Female') +
      posChipNut('data-khgt=""', 'Chưa rõ', !f.gioi_tinh)) + '</div>' +
    o('Địa chỉ', 'khfDc', f.dia_chi) +
    o('Zalo user id', 'khfZalo', f.zalo) +
    o('Nhãn', 'khfTags', f.tags, 'text', 'Mỗi nhãn cách nhau bằng dấu phẩy.') +
    '<button class="btn" id="khfLuu" style="width:100%;margin-top:14px">💾 Lưu</button></div>';
  ov.appendChild(box); document.body.appendChild(ov);
  function dong() { ov.remove(); }
  ov.onclick = function (e) { if (e.target === ov) dong(); };
  box.querySelector('.x').onclick = dong;
  box.addEventListener('click', function (e) {
    var t = e.target.closest('[data-khgt]');
    if (!t) return;
    f.gioi_tinh = t.getAttribute('data-khgt');
    box.querySelectorAll('[data-khgt]').forEach(function (n) {
      var on = n.getAttribute('data-khgt') === f.gioi_tinh;
      n.style.background = on ? '#0d9488' : '#fff';
      n.style.color = on ? '#fff' : '#374151';
      n.style.borderColor = on ? '#0d9488' : '#d7dce5';
      n.style.fontWeight = on ? '800' : '600';
    });
  });
  document.getElementById('khfLuu').onclick = async function () {
    var v = function (id) { var n = document.getElementById(id); return n ? String(n.value).trim() : ''; };
    busy(true);
    try {
      khHs = await api('vagabond.khach_hang.luu_ho_so', {
        khach: khMa,
        dat: JSON.stringify({
          ten: v('khfTen'), sdt: v('khfSdt'), email: v('khfEmail'),
          sinh_nhat: v('khfSn'), gioi_tinh: f.gioi_tinh, dia_chi: v('khfDc'),
          zalo: v('khfZalo'), tags: v('khfTags')
        })
      });
      busy(false); dong(); toast('Đã lưu'); khCtVe();
    } catch (er) { busy(false); baoTin((er && er.message) || 'Không lưu được'); }
  };
}

async function khSheetSoDiem() {
  busy(true);
  var k;
  try { k = await api('vagabond.khach_hang.so_diem', { khach: khMa, so_dong: 50 }); }
  catch (e) { busy(false); return toast((e && e.message) || 'Không đọc được sổ điểm'); }
  busy(false);
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  var but = k.but || [];
  box.innerHTML = '<div class="shh"><b>Sổ điểm</b><div class="x">&times;</div></div>' +
    '<div style="padding:4px 14px calc(env(safe-area-inset-bottom,0px) + 14px)">' +
    '<div style="font-size:12.5px;color:#6b7280;margin-bottom:10px">Số dư <b>' + money(k.so_du || 0) + ' điểm</b>. 1 điểm bằng 1 đồng.</div>' +
    (but.length
      ? but.map(function (x) {
          return '<div style="display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid #f4f5f8">' +
            '<div style="flex:1;min-width:0"><div style="font-size:13.5px">' + h(x.loai || '') + '</div>' +
            '<div style="font-size:11.5px;color:#98a2b3">' + h(String(x.ngay || '').slice(0, 16)) +
            (x.hoa_don ? ' · ' + h(x.hoa_don) : '') + (x.ghi_chu ? '<br>' + h(x.ghi_chu) : '') + '</div></div>' +
            '<b style="white-space:nowrap;color:' + ((x.diem || 0) < 0 ? '#b3261e' : '#0f766e') + '">' +
            ((x.diem || 0) > 0 ? '+' : '') + money(x.diem || 0) + '</b></div>';
        }).join('')
      : '<div style="padding:20px 0;color:#a0a6b4;text-align:center">Chưa có bút nào.</div>') +
    '</div>';
  ov.appendChild(box); document.body.appendChild(ov);
  function dong() { ov.remove(); }
  ov.onclick = function (e) { if (e.target === ov) dong(); };
  box.querySelector('.x').onclick = dong;
}


/* ---------- Don con treo: hoa don sales chua ghi so duoc, va vi sao ----------
   Anh Viet 13/08/2026 hoi vi sao ba don o nguon sales khong tu ghi so va tu
   xuat hoa don. Chuoi cuoi ngay VAN chan dung - don chua chon phuong thuc,
   don chuyen khoan chua ve tien thi khong duoc ghi so. Cai sai la chan xong
   roi im lang: loi chi vao Error Log, khong ai mo, nen 149 don tu 01-04/08
   nam nhap nua thang (114 trieu) khong ai hay.

   Man nay bay het ra: tung don, ly do, so tien SePay da nhan, va nut xu. */
var dtNgay = 14, dtLoc = '';
var DT_MAU = {
  chua_pt: ['#fff7ed', '#fed7aa', '#9a3412', '❓'],
  pt_sai_nguon: ['#fef2f2', '#fecaca', '#991b1b', '⚠'],
  chua_ve_tien: ['#fefce8', '#fde68a', '#854d0e', '⏳'],
  san_sang: ['#f0fdf4', '#bbf7d0', '#166534', '✅']
};

async function scrDonTreo() {
  frame('Đơn còn treo', '<div class="emp"><div class="e1">⏳</div><div>Đang soát đơn chưa ghi sổ...</div></div>');
  var d;
  try { d = await api('vagabond.ban_hang.don_treo', { so_ngay: dtNgay }); }
  catch (e) { frame('Đơn còn treo', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var rows = d.rows || [];
  var LD = d.ly_do || {};

  var html = '<div class="card" style="padding:12px 14px;font-size:13px;line-height:1.6;color:#374151">' +
    'Đơn nào <b>chưa ghi sổ được</b> thì nằm ở đây kèm lý do. Máy chạy chuỗi cuối ngày lúc 23h rồi vét lại 5 phút một lần cho tới nửa đêm; đơn nào tới lúc đó vẫn thiếu điều kiện thì mới treo lại. ' +
    'Đúng 23h55 máy gửi thư báo cho kế toán và quản lý.</div>';

  /* Bootstrap cua Frappe dat .card{display:flex;flex-direction:column} nen chip
     nhet thang vao .card se xep DOC va gian het be ngang. Luon boc mot lop
     div rieng - xem kmHangChip. */
  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
    [7, 14, 30, 90].map(function (n) {
      return posChipNut('data-dtng="' + n + '"', n + ' ngày', dtNgay === n);
    }).join('')) + '</div>';

  var DTL = [{ k: '', nhan: 'Tất cả', loc: function () { return true; } }];
  ['san_sang', 'chua_ve_tien', 'chua_pt', 'pt_sai_nguon'].forEach(function (k) {
    if (!LD[k]) return;
    var m = DT_MAU[k] || ['', '', '', ''];
    DTL.push({ k: k, nhan: m[3] + ' ' + h(LD[k]), loc: function (r) { return r.ly_do === k; } });
  });
  if (!locTim(DTL, dtLoc) || locTim(DTL, dtLoc).k !== dtLoc) dtLoc = '';
  var f = locTim(DTL, dtLoc);
  html += '<div class="card" style="padding:10px 12px">' + locHang(DTL, dtLoc, 'data-dtloc', rows) + '</div>';

  var loc = rows.filter(f.loc);
  html += locKhoiTong(loc, dtLoc ? f.nhan : '');

  /* Nut xu ca loat chi hien khi CO don da du dieu kien cua ngay cu. Don
     hom nay khong dua vao: chuoi cuoi ngay toi 23h se lo, khong can keo
     ngay cua chinh no. */
  var sanSangCu = rows.filter(function (r) { return r.ly_do === 'san_sang' && !r.hom_nay; });
  if (sanSangCu.length) {
    var tienCu = sanSangCu.reduce(function (a, r) { return a + Number(r.grand_total || 0); }, 0);
    html += '<div class="sec">Xử cả loạt</div><div class="card" style="padding:12px 14px;font-size:13px;line-height:1.6;color:#374151">' +
      '<b>' + sanSangCu.length + ' đơn của ngày cũ đã đủ điều kiện</b>, tổng ' + money(tienCu) + ' đ.<br>' +
      'Luật bắt xuất hoá đơn điện tử <b>trong ngày bán</b>, nên đơn cũ phải kéo sang hôm nay rồi mới ghi sổ được. ' +
      'Ngày bán thật vẫn giữ trong ô ghi chú của từng đơn.' +
      '<div style="margin-top:10px"><button class="btn gh" data-dt="keo" style="width:100%">📥 Kéo ' + sanSangCu.length + ' đơn sang hôm nay và ghi sổ</button></div></div>';
  }

  /* Huy ghi so hang loat: nut nay chi hien khi ngay dang xem CO to da ghi
     so bi keo tu ngay cu sang. Khong bay ra thuong truc - huy hang loat la
     viec hiem, de san mot nut do giua man chi to bam nham. */
  html += '<div class="sec">Công cụ kế toán</div><div class="card" style="padding:12px 14px;font-size:13px;line-height:1.6;color:#374151">' +
    'Hoá đơn đã ghi sổ nhầm thì huỷ ghi sổ ở đây. Máy đảo ngược bút toán, rút lại điểm đã tích, xoá số hoá đơn điện tử bên mình và ẩn tờ đó khỏi danh sách bill của Sales.' +
    '<br><b style="color:#991b1b">Tờ đã ký hoặc cơ quan thuế đã nhận thì máy chặn</b>, những tờ đó phải làm hoá đơn thay thế.' +
    '<div style="margin-top:10px"><button class="btn gh" data-dt="huyloat" style="width:100%">🗑 Huỷ ghi sổ hàng loạt</button></div></div>';

  html += '<div class="sec">Danh sách đơn · bấm để mở đơn</div><div class="card">';
  if (!rows.length) html += '<div class="emp" style="padding:24px"><div class="e1">🎉</div><div>Không còn đơn nào treo trong ' + dtNgay + ' ngày qua.</div></div>';
  else if (!loc.length) html += '<div class="emp" style="padding:24px"><div class="e1">✅</div><div>Không có đơn nào thuộc nhóm <b>' + f.nhan + '</b>.</div></div>';
  loc.forEach(function (r) {
    var m = DT_MAU[r.ly_do] || ['#f3f4f6', '#e5e7eb', '#374151', ''];
    var kh = (r.remarks || '').split(' - ');
    html += '<div class="hub" data-dtsi="' + h(r.name) + '">' +
      '<div class="hub-i" style="background:' + m[0] + '">' + m[3] + '</div>' +
      '<div class="hub-t"><div class="t1">' +
      (r.custom_nguon && r.custom_nguon !== 'Pancake' ? h(r.custom_nguon) + ' ' : '') +
      '#' + h(r.custom_pancake_display_id || r.name) + (kh[1] ? ' · ' + h(kh[1]) : '') + '</div>' +
      '<div class="t2">' + dtNgayVn(r.posting_date) + ' · ' + h(r.name) +
      (r.vgb_pt_thanh_toan ? ' · ' + h(r.vgb_pt_thanh_toan) : '') + '</div>' +
      '<div style="margin-top:4px"><span style="display:inline-block;background:' + m[0] +
      ';border:1px solid ' + m[1] + ';color:' + m[2] + ';border-radius:999px;padding:2px 9px;font-size:11.5px;font-weight:700">' +
      h((LD[r.ly_do] || r.ly_do)) + '</span>' +
      (r.ly_do === 'chua_ve_tien' ? '<span style="margin-left:7px;font-size:11.5px;color:#854d0e">ngân hàng mới nhận ' + money(r.sepay_nhan) + ' đ</span>' : '') +
      '</div></div>' +
      '<b style="white-space:nowrap">' + money(r.grand_total) + ' đ</b></div>';
  });
  html += '</div>';

  frame('Đơn còn treo', html);
  Array.prototype.forEach.call(document.querySelectorAll('[data-dtng]'), function (el) {
    el.onclick = function () { dtNgay = +el.getAttribute('data-dtng'); go(scrDonTreo, true); };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-dtloc]'), function (el) {
    el.onclick = function () { dtLoc = el.getAttribute('data-dtloc'); go(scrDonTreo, true); };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-dtsi]'), function (el) {
    el.onclick = function () { var nm = el.getAttribute('data-dtsi'); go(function () { scrDsView(nm, false); }); };
  });
  var nk = document.querySelector('[data-dt="keo"]');
  if (nk) nk.onclick = async function () { await dtKeo(); };
  var nh = document.querySelector('[data-dt="huyloat"]');
  if (nh) nh.onclick = async function () { await dtHuyLoat(); };
}

function dtNgayVn(s) {
  var p = String(s || '').split('-');
  return p.length === 3 ? p[2] + '/' + p[1] : String(s || '');
}

/* Huy ghi so hang loat. Ba lop chan truoc khi chay that: xem truoc bat
   buoc, bat go ly do, va hoi lai kem con so. */
async function dtHuyLoat() {
  var ngay = await hoiNhap('Huỷ ghi sổ các hoá đơn ĐÃ GHI SỔ của ngày nào? (YYYY-MM-DD)', today());
  if (!ngay) return;
  var truoc = await hoiNhap(
    'Chỉ lấy tờ được LẬP TRƯỚC ngày nào? Để trống thì lấy hết tờ của ngày trên.\n\n' +
    'Ví dụ gõ 2026-08-05 thì chỉ dính những tờ bị kéo từ ngày cũ sang, không dính tờ sinh trong ngày.',
    '');
  var ts = { ngay: ngay };
  if (truoc && truoc.trim()) ts.tao_truoc = truoc.trim();
  busy(true);
  var xem;
  try { xem = await api('vagabond.chung_tu.xem_truoc_huy_ghi_so', ts); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Không xem trước được'); }
  busy(false);
  if (!xem || !xem.so_don) return toast('Không có hoá đơn đã ghi sổ nào khớp tiêu chí đó.');
  var mo = (xem.vi_du || []).slice(0, 10).map(function (x) {
    return '#' + (x.ma || x.don) + ' · ' + money(x.tien) + ' đ' + (x.hddt ? ' · HĐĐT ' + x.hddt + ' (' + x.hddt_tt + ')' : '');
  }).join('\n');
  if (!await xacNhan(
    'Sẽ huỷ ghi sổ ' + xem.so_don + ' hoá đơn, tổng ' + money(xem.tong_tien) + ' đ.\n' +
    xem.co_hddt + ' tờ có số hoá đơn điện tử' + (xem.da_ky ? ', trong đó ' + xem.da_ky + ' tờ ĐÃ KÝ hoặc CQT đã nhận nên máy sẽ BỎ QUA' : '') + '.\n\n' +
    mo + (xem.so_don > 10 ? '\n... và ' + (xem.so_don - 10) + ' tờ nữa' : '') +
    '\n\nViệc này KHÔNG LUI LẠI ĐƯỢC. Tiếp tục?')) return;
  var ly = await hoiNhap('Lý do huỷ? (bắt buộc, sau này còn biết vì sao)', '');
  if (!ly || !ly.trim()) return toast('Chưa ghi lý do nên hệ thống chưa huỷ.');
  ts.ly_do = ly.trim();
  busy(true);
  var kq;
  try { kq = await api('vagabond.chung_tu.huy_ghi_so_hang_loat', ts); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Huỷ lỗi'); }
  busy(false);
  baoTin('Xong: huỷ ' + kq.huy + ' tờ, tổng ' + money(kq.tong_tien) + ' đ.' +
    (kq.bo_qua_da_ky ? '\nBỏ qua ' + kq.bo_qua_da_ky + ' tờ đã ký hoặc CQT đã nhận.' : '') +
    ((kq.loi || []).length ? '\n\n' + kq.loi.slice(0, 8).join('\n') : ''));
  go(scrDonTreo, true);
}

/* Keo don cu sang hom nay roi ghi so. Xem truoc TRUOC, hoi lai, roi moi
   chay that - day la doanh thu vao so, khong lui lai duoc. */
async function dtKeo() {
  var xem;
  busy(true);
  try { xem = await api('vagabond.ban_hang.keo_va_ghi_so', { so_ngay: dtNgay, chay_thu: 1 }); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Không xem trước được'); }
  busy(false);
  if (!xem || !xem.chon) return toast('Không có đơn nào đủ điều kiện để kéo.');
  var mo = (xem.vi_du || []).slice(0, 8).map(function (x) {
    return '#' + x.ma + ' ngày ' + dtNgayVn(x.ngay_cu) + ' · ' + money(x.tien) + ' đ';
  }).join('\n');
  if (!await xacNhan('Kéo ' + xem.chon + ' đơn sang hôm nay rồi ghi sổ và xuất hoá đơn?\n' +
    'Tổng ' + money(xem.tien) + ' đ.\n\n' + mo + (xem.chon > 8 ? '\n... và ' + (xem.chon - 8) + ' đơn nữa' : '') +
    '\n\nDoanh thu sẽ vào sổ ngày hôm nay. Việc này không lui lại được.')) return;
  busy(true);
  var kq;
  try { kq = await api('vagabond.ban_hang.keo_va_ghi_so', { so_ngay: dtNgay, chay_thu: 0 }); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Chạy lỗi'); }
  busy(false);
  baoTin('Xong: kéo ' + kq.keo + ' đơn, ghi sổ ' + kq.ghi_so + ' đơn, xuất hoá đơn ' + kq.xuat_hddt + '.' +
    ((kq.loi || []).length ? '\n\nCòn lại:\n' + kq.loi.slice(0, 10).join('\n') : ''));
  go(scrDonTreo, true);
}



/* Doi don vi mot dong hoa don mua con nhap.
   Chi doi don vi, khong dong den so luong hay don gia, nen tien tren to
   hoa don khong xe dich. Cai duoc nan lai la so luong quy ve don vi kho. */
async function dcmDoiDonVi(name, idx, dvt) {
  if (!dvt) return;
  var ok = await confirmSheet('Đổi đơn vị dòng ' + idx + ' thành ' + dvt,
    'Số lượng và đơn giá giữ nguyên nên thành tiền của hoá đơn không đổi.\n\n' +
    'Cái được sửa là số lượng quy về đơn vị kho, để khớp với phiếu nhập.',
    'Đổi đơn vị', false);
  if (!ok) return;
  busy(true);
  try {
    await api('vagabond.doi_chieu_mua.sua_don_vi', { name: name, dong: JSON.stringify([String(idx)]), dvt: dvt });
    busy(false);
    toast('Đã đổi đơn vị dòng ' + idx + ' thành ' + dvt + '.', 3200);
    go(function () { scrDcmXem(name); }, true);
  } catch (e) { busy(false); baoTin((e && e.message) || 'Không đổi được đơn vị'); }
}

/* Khai han don vi cua nha cung cap vao bang quy doi cua mon.

   Doi don vi mot dong hoa don la va cai ngon. Khai don vi cho mon la chua
   cai goc: lan sau nha cung cap van ghi "BAG" thi he doc ra ngay, khong ha
   ngam ve don vi kho he so 1 nua.

   HE SO PHAI DO NGUOI GO. May co de xuat mot con so khi hoa don va phieu
   nhap cung so luong - luc do cai thung cua ho va cai tui cua minh la mot -
   nhung van bat nguoi nhin va xac nhan. Doan sai he so o day la sai so
   luong ton kho gap hang nghin lan, dung cai loi ngay 27/08 da mac. */
async function dcmKhaiDonVi(name, itemCode, dvt, slHd, slPnk, hsPnk, dvtKho) {
  if (!itemCode || !dvt) return;

  /* De xuat he so: hai ben cung so luong thi don vi cua ho bang don vi cua
     minh, nen he so chinh la he so cua dong phieu nhap. Khac so luong thi
     de trong, khong doan. */
  var a = parseFloat(slHd || 0), b = parseFloat(slPnk || 0), hs = parseFloat(hsPnk || 0);
  var deXuat = (a > 0 && b > 0 && Math.abs(a - b) < 0.0001 && hs > 0) ? String(hs) : '';

  var nhan = 'Nhà cung cấp ghi "' + dvt + '", hệ chưa biết đó là bao nhiêu ' +
    (dvtKho || 'đơn vị kho') + '. Gõ vào: 1 ' + dvt + ' bằng bao nhiêu ' + (dvtKho || 'đơn vị kho') + '?' +
    (deXuat ? ' Máy đề xuất ' + deXuat + ' vì hoá đơn và phiếu nhập cùng ghi ' + a + ', vẫn nên nhìn lại.' : '');
  var d = await qtySheet('Khai đơn vị "' + dvt + '" cho món này', nhan,
    deXuat ? parseFloat(deXuat) : 0, dvtKho || '');
  if (!(parseFloat(d) > 0)) return;

  busy(true);
  try {
    var kq = await api('vagabond.doi_chieu_mua.khai_don_vi',
      { item_code: itemCode, dvt: dvt, he_so: parseFloat(d) });
    busy(false);
    baoTin((kq && kq.loi_nhan) || 'Đã khai đơn vị.');
    go(function () { scrDcmXem(name); }, true);
  } catch (e) { busy(false); baoTin((e && e.message) || 'Không khai được đơn vị'); }
}

/* Gan mot Mon vao dong hoa don chua co ma hang.

   Ten hang cua nha cung cap va ten Mon cua minh gan nhu khong bao gio giong
   nhau: "CHERRY CALADA S10_5K/T" ben ho la "Trai cherry tuoi, Thung 5 kg"
   ben minh. May so chuoi kieu gi cung khong ra, nen phai co nguoi chon.

   Nhung khong bat nguoi go tim trong ba nghin Mon. May xep san nhung Mon
   nam tren phieu nhap chua thanh toan cua chinh nha cung cap do - hang da
   ve kho roi thi gan nhu chac chan la lo hang cua to hoa don nay.

   Bam mot lan la NHO LUON: lan sau nha cung cap gui dung ten hang do, may
   tu nhan. Do moi la cho chua goc, chu sua tay tung dong thi 9.985 dong lam
   den bao gio moi het. */
async function dcmGanMaHang(name, idx) {
  busy(true);
  var gy;
  try { gy = await api('vagabond.doi_chieu_mua.goi_y_mon', { name: name, dong: idx }); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Không lấy được gợi ý'); }
  busy(false);

  /* `sheet` doi dung ba khoa: label, value, phu. Va no tra ve CA MUC chu
     khong tra ve rieng value. */
  var ds = (gy.goi_y || []).map(function (x) {
    return { value: x.item_code, label: x.item_name, phu: x.vi_sao, tim: x.item_code };
  });
  ds.push({ value: '__TIM__', label: 'Tìm món khác...', phu: 'Gõ tên hoặc mã để tìm trong toàn bộ danh mục' });

  sheet('Hàng "' + (gy.ten_ncc || '') + '" là món nào?', ds, null, function (muc) {
    if (!muc || !muc.value) return;
    if (muc.value === '__TIM__') {
      /* mfgPickItem tra ve thang chuoi ma hang. */
      return mfgPickItem('Tìm món cho "' + (gy.ten_ncc || '') + '"', null, function (ma) {
        dcmGanXong(name, idx, ma);
      });
    }
    dcmGanXong(name, idx, muc.value);
  }, true);
}

async function dcmGanXong(name, idx, itemCode) {
  if (!itemCode) return;
  busy(true);
  try {
    var kq = await api('vagabond.doi_chieu_mua.gan_ma_hang',
      { name: name, dong: idx, item_code: itemCode, nho: 1 });
    busy(false);
    baoTin((kq && kq.loi_nhan) || 'Đã gắn mã hàng.');
    go(function () { scrDcmXem(name); }, true);
  } catch (e) { busy(false); baoTin((e && e.message) || 'Không gắn được mã hàng'); }
}

/* Dung lai dong hang cua mot hoa don NHAP theo ban hoa don dien tu goc.
   Chi dung lai bang dong hang; nha cung cap, ngay, so hoa don, dong thue
   deu giu nguyen vi chung von lay tu hoa don dien tu ma ra. */
function dcmGanDungLai(name) {
  var n = document.getElementById('dcmDungLai');
  if (!n) return;
  n.onclick = async function () {
    var ok = await confirmSheet('Dựng lại theo hoá đơn điện tử',
      'Toàn bộ dòng hàng của phiếu này sẽ được dựng lại đúng như bản hoá đơn ' +
      'nhà cung cấp đã gửi cơ quan thuế.\n\nNhững gì đã sửa tay trên dòng hàng sẽ mất.',
      'Dựng lại', true);
    if (!ok) return;
    busy(true);
    try {
      var kq = await api('vagabond.dung_lai_hddt.dung_lai', { name: name });
      busy(false);
      toast((kq && kq.loi_nhan) || 'Đã dựng lại.', 4500);
      go(function () { scrDcmXem(name); }, true);
    } catch (e) { busy(false); baoTin((e && e.message) || 'Không dựng lại được'); }
  };
}

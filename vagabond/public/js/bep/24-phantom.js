
/* ---------------- Chuyen BTP cap 1 thanh Phantom (anh Viet giao 21/08/2026)

   139 ma ban thanh phan dang ghi so kho trong khi chua ai lam lenh san
   xuat nao cho chung. Man nay lam hai viec, dung thu tu:

     1. Don chung tu thu   - dong not cac lenh san xuat con treo
     2. Chuyen Phantom     - chay thu truoc, doc ky, roi moi ghi that

   Nut ghi that co CHU DO va hoi lai mot lan nua, vi khong co nut hoan tac.
   Tien to pt = phantom. Da kiem va cham ten truoc khi dat (QT-28). */

var ptKe = null;

function ptSo(n) { return (n || 0).toLocaleString('vi-VN'); }

function ptO(nhan, gt, mau) {
  return '<div style="display:flex;justify-content:space-between;gap:10px;padding:7px 0;' +
    'border-bottom:1px solid #f3f4f6"><div style="font-size:13px;color:#6b7280">' + nhan +
    '</div><div style="font-size:14px;font-weight:700;color:' + (mau || '#111827') + '">' +
    gt + '</div></div>';
}

/* ---------------- Man 1: don chung tu thu ---------------- */

async function scrDonChungTuThu() {
  frame('Dọn chứng từ thử', '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api('vagabond.phantom.chung_tu_thu', {}); }
  catch (e) {
    frame('Dọn chứng từ thử',
      '<div class="emp"><div class="e1">🔒</div><div>' + h(errMsg(e)) + '</div></div>');
    return;
  }

  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12.5px;color:#374151;line-height:1.6">' +
    'Trước khi bỏ theo dõi tồn kho của ' + ptSo(d.so_btp) + ' mã bán thành phẩm, ' +
    'phải dọn hết chứng từ còn treo trên chúng. Còn một lệnh treo mà đã bỏ tồn kho ' +
    'thì lệnh đó đòi một mã không còn kho để lấy, và bếp đứng.</div></div>';

  var lenh = d.lenh_treo || [];
  html += '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">LỆNH SẢN XUẤT CÒN TREO · ' +
    ptSo(lenh.length) + '</div>';
  if (!lenh.length) {
    html += '<div style="font-size:13px;color:#0f7a44;margin-top:8px">' +
      '✓ Không còn lệnh nào treo.</div>';
  } else {
    lenh.forEach(function (x, i) {
      html += '<div style="border-top:1px solid #f3f4f6;padding:10px 0">' +
        '<div style="font-size:14px;font-weight:700">' + h(x.production_item) +
        ' <span style="font-weight:500;color:#6b7280">' + h(x.item_name || '') + '</span></div>' +
        '<div style="font-size:12px;color:#6b7280;margin:3px 0 8px">' + h(x.name) +
        ' · ' + h(x.status) + ' · đã làm ' + ptSo(x.produced_qty) + '/' + ptSo(x.qty) + '</div>' +
        '<button class="btn2 ptDong" data-ma="' + h(x.name) + '" data-i="' + i +
        '" style="margin:0;height:36px;font-size:13px">Đóng lệnh này</button></div>';
    });
    html += '<div style="font-size:11.5px;color:#98a2b3;margin-top:8px;line-height:1.5">' +
      'Đóng chứ không xoá. Lệnh vẫn tra lại được, chỉ thôi đòi nguyên liệu.</div>';
  }
  html += '</div>';

  var ton = d.ton_con_lai || [];
  html += '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">MÃ CÒN TỒN KHO · ' + ptSo(ton.length) + '</div>';
  if (!ton.length) {
    html += '<div style="font-size:13px;color:#0f7a44;margin-top:8px">' +
      '✓ Không mã nào còn tồn.</div>';
  } else {
    ton.forEach(function (x) {
      html += ptO(h(x.item_code) + '<div style="font-size:11.5px;color:#98a2b3">' +
        h(x.warehouse) + '</div>', ptSo(x.actual_qty) + ' ' + h(x.stock_uom || ''), '#b45309');
    });
    html += '<div style="font-size:11.5px;color:#98a2b3;margin-top:8px;line-height:1.5">' +
      'Số này phải xuất hết hoặc kiểm kê về 0 trước. Bỏ tồn kho khi còn số dư thì ' +
      'số đó nằm lại trong kho mà không màn nào đọc ra nữa.</div>';
  }
  html += '</div>';

  var nhap = d.phieu_nhap || [];
  if (nhap.length) {
    html += '<div class="card" style="padding:13px 14px">' +
      '<div style="font-size:12px;color:#98a2b3">PHIẾU KHO CÒN NHÁP · ' + ptSo(nhap.length) + '</div>' +
      '<div style="font-size:12.5px;color:#374151;margin:4px 0 8px;line-height:1.6">' +
      'Nháp thì chưa ghi sổ nên không chặn, nhưng ghi sổ sau khi chuyển Phantom là hỏng. ' +
      'Anh chị vào Desk xoá hoặc để nguyên rồi bỏ hẳn.</div>';
    nhap.forEach(function (x) {
      html += ptO(h(x.name) + '<div style="font-size:11.5px;color:#98a2b3">' +
        h((x.cac_ma || []).join(', ')) + '</div>', h(x.stock_entry_type || x.purpose || ''));
    });
    html += '</div>';
  }

  var xong = !(d.chan);
  var b = frame('Dọn chứng từ thử', html, {
    footer: '<button class="btn" id="ptSang" style="margin:0' +
      (xong ? '' : ';opacity:.5') + '">' +
      (xong ? 'Xong, sang bước chuyển Phantom' : 'Còn vướng, xem lại ở trên') + '</button>'
  });

  Array.prototype.forEach.call(document.querySelectorAll('.ptDong'), function (o) {
    o.onclick = async function () {
      var ma = o.getAttribute('data-ma');
      if (!await confirmSheet('Đóng lệnh ' + ma + '?',
        'Lệnh vẫn nằm nguyên trên hệ và tra lại được, chỉ thôi đòi nguyên liệu ' +
        'và thôi chặn việc chuyển Phantom.', 'Đóng lệnh')) return;
      busy(1);
      try { var r = await api('vagabond.phantom.dong_lenh', { ma: ma, ly_do: 'Dọn chứng từ thử trước khi chuyển Phantom' }); busy(0); toast((r && r.ghi_chu) || 'Đã đóng lệnh.', 5000); }
      catch (e) { busy(0); return toast(errMsg(e), 7000); }
      go(scrDonChungTuThu, true);
    };
  });

  var sang = document.getElementById('ptSang');
  if (sang) sang.onclick = function () {
    if (!xong) return toast('Còn chứng từ treo hoặc còn tồn kho, dọn nốt rồi hãy sang.', 5500);
    ptKe = null;
    go(scrChuyenPhantom);
  };
}

/* ---------------- Man 2: chuyen Phantom ---------------- */

async function scrChuyenPhantom() {
  frame('Chuyển Phantom', '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api('vagabond.phantom.xem_truoc', {}); }
  catch (e) {
    frame('Chuyển Phantom',
      '<div class="emp"><div class="e1">🔒</div><div>' + h(errMsg(e)) + '</div></div>');
    return;
  }
  ptKe = d;

  var noRa = (d.doi_dong || []).filter(function (x) { return x.viec === 'bat_no'; });
  var chan = (d.doi_dong || []).filter(function (x) { return x.viec === 'chan_no'; });

  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">BẢN CHẠY THỬ · CHƯA GHI GÌ</div>' +
    '<div style="font-size:12.5px;color:#374151;line-height:1.6;margin:5px 0 10px">' +
    'Đây là danh sách máy SẼ đổi nếu anh bấm chạy thật. Đọc kỹ ba con số dưới đây.</div>' +
    ptO('Mã bán thành phẩm bỏ theo dõi tồn kho', ptSo((d.doi_ma || []).length)) +
    ptO('Dòng công thức mở nổ xuống nguyên liệu', ptSo(noRa.length)) +
    ptO('Dòng công thức chặn nổ ở cấp giữ tồn (C1, C2)', ptSo(chan.length)) +
    ptO('Công thức cha phải dựng lại bảng nổ', ptSo((d.bom_dung_lai || []).length)) +
    '</div>';

  if (d.hang_rao && d.hang_rao.chan) {
    html += '<div class="card" style="padding:13px 14px;border:1px solid #f5c2c0;background:#fff5f5">' +
      '<div style="font-size:12px;color:#b3261e">CHƯA CHẠY THẬT ĐƯỢC</div>' +
      '<div style="font-size:12.5px;color:#374151;line-height:1.6;margin-top:5px">' +
      h(d.hang_rao.vi_sao) + '</div>' +
      '<button class="btn2" id="ptVeDon" style="margin:10px 0 0;height:38px">Sang màn Dọn chứng từ thử</button></div>';
  }

  if ((d.vuong_dong || []).length) {
    html += '<div class="card" style="padding:13px 14px">' +
      '<div style="font-size:12px;color:#b45309">DÒNG CHƯA XỬ ĐƯỢC · ' +
      ptSo(d.vuong_dong.length) + '</div>' +
      '<div style="font-size:12.5px;color:#374151;margin:4px 0 8px;line-height:1.6">' +
      'Những dòng này máy để nguyên, không đụng vào. Xử xong thì chạy lại.</div>';
    d.vuong_dong.slice(0, 30).forEach(function (x) {
      html += ptO(h(x.ma) + '<div style="font-size:11.5px;color:#98a2b3">' +
        h(x.bom_cha) + '</div>', '<span style="font-size:12px;font-weight:500;color:#b45309">' +
        h(x.vi_sao) + '</span>');
    });
    html += '</div>';
  }

  if ((d.doi_ma || []).length) {
    html += '<div class="card" style="padding:13px 14px">' +
      '<div style="font-size:12px;color:#98a2b3">MÃ SẼ THÀNH PHANTOM · ' +
      ptSo(d.doi_ma.length) + '</div>';
    d.doi_ma.slice(0, 200).forEach(function (x) {
      html += ptO(h(x.ma), '<span style="font-size:12.5px;font-weight:500;color:' +
        (x.vuong ? '#b45309' : '#6b7280') + '">' + h(x.vuong || x.ten || '') + '</span>');
    });
    if (d.doi_ma.length > 200) {
      html += '<div style="font-size:12px;color:#98a2b3;margin-top:8px">' +
        'và ' + ptSo(d.doi_ma.length - 200) + ' mã nữa.</div>';
    }
    html += '</div>';
  }

  var chayDuoc = !(d.hang_rao && d.hang_rao.chan) && (d.doi_ma || []).length;
  frame('Chuyển Phantom', html, {
    footer: '<button class="btn" id="ptChay" style="margin:0;background:#b3261e' +
      (chayDuoc ? '' : ';opacity:.45') + '">Chạy thật, ghi xuống hệ</button>'
  });

  var ve = document.getElementById('ptVeDon');
  if (ve) ve.onclick = function () { go(scrDonChungTuThu); };

  var nut = document.getElementById('ptChay');
  if (nut) nut.onclick = async function () {
    if (!chayDuoc) return toast('Chưa chạy thật được, đọc phần màu đỏ ở trên.', 5000);
    if (!await confirmSheet('Ghi thật xuống hệ?',
      'Máy sẽ bỏ theo dõi tồn kho của ' + ptSo(d.doi_ma.length) + ' mã và sửa ' +
      ptSo((d.doi_dong || []).length) + ' dòng công thức. KHÔNG có nút hoàn tác. ' +
      'Nên chạy ngoài giờ bếp đang làm.', 'Ghi thật')) return;
    busy(1);
    var r;
    try { r = await api('vagabond.phantom.chuyen', { chay_that: 1 }); }
    catch (e) { busy(0); return toast(errMsg(e), 9000); }
    busy(0);
    toast((r && r.ghi_chu) || 'Đã chuyển xong.', 9000);
    ptKe = null;
    go(scrChuyenPhantom, true);
  };
}

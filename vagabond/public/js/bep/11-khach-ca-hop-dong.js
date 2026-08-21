/* ---------- Cong no phai thu (anh Viet 11/08/2026) ----------

Khach si nhu Ravie va khach VIP gom nhieu hoa don tra mot lan. Man nay lam
hai viec: xem ai dang no bao nhieu va bao lau, va gom hoa don thanh mot
PHIEU DOI NO co ma QR rieng de khach chuyen mot phat.

Co y de hai tab tach han: "Khach đang nợ" la viec di doi, "Phiếu đã gửi"
la viec doi soat. Tron chung vao mot danh sach la ke toan roi ngay. */
var cnTab = 'no', cnChon = {}, cnKhachMo = '';

async function scrCongNo() {
  frame('Công nợ phải thu', '<div class="emp"><div class="e1">⏳</div><div>Đang cộng sổ công nợ...</div></div>');
  var kq, kp;
  try {
    kq = await api('vagabond.cong_no.ds_khach_no', {});
    kp = await api('vagabond.cong_no.ds_phieu', {});
  } catch (e) {
    frame('Công nợ phải thu', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>');
    return;
  }
  var khach = (kq && kq.khach) || [], phieu = (kp && kp.phieu) || [];
  var choThu = phieu.filter(function (p) { return p.trang_thai === 'Cho thu' || p.trang_thai === 'Thu thieu'; });
  var tienChoThu = choThu.reduce(function (t, p) { return t + (p.con_thieu || 0); }, 0);

  var html = '<div class="card" style="padding:12px 14px;display:flex;gap:10px">' +
    '<div style="flex:1"><div style="font-size:12px;color:#98a2b3">CHƯA GOM PHIẾU</div>' +
    '<div style="font-size:19px;font-weight:800;color:#b45309">' + money(kq.tong || 0) + ' đ</div>' +
    '<div style="font-size:12px;color:#98a2b3">' + khach.length + ' khách</div></div>' +
    '<div style="flex:1;border-left:1px solid #eef0f4;padding-left:10px"><div style="font-size:12px;color:#98a2b3">ĐÃ GỬI, CHỜ TIỀN</div>' +
    '<div style="font-size:19px;font-weight:800;color:#0b7c93">' + money(tienChoThu) + ' đ</div>' +
    '<div style="font-size:12px;color:#98a2b3">' + choThu.length + ' phiếu</div></div></div>';

  html += '<div class="card" style="padding:10px 12px;display:flex;gap:8px">' +
    posChipNut('data-cntab="no"', '📒 Khách đang nợ ' + khach.length, cnTab === 'no') +
    posChipNut('data-cntab="phieu"', '📤 Phiếu đã gửi ' + phieu.length, cnTab === 'phieu') + '</div>';

  if (cnTab === 'no') {
    if (!khach.length) {
      html += '<div class="card"><div class="emp" style="padding:26px"><div class="e1">🎉</div><div>Không còn khoản công nợ nào chưa gom. Sạch sổ.</div></div></div>';
    }
    khach.forEach(function (k) {
      var mo = cnKhachMo === k.khach;
      var chon = cnChon[k.khach] || {};
      var soChon = Object.keys(chon).filter(function (x) { return chon[x]; }).length;
      var tienChon = (k.hd || []).filter(function (d) { return chon[d.name]; }).reduce(function (t, d) { return t + d.tien; }, 0);
      /* Mau canh bao theo tuoi no: qua 30 ngay la do, 15 ngay la cam. */
      var mau = k.so_ngay >= 30 ? '#b91c1c' : (k.so_ngay >= 15 ? '#c2410c' : '#0f766e');
      html += '<div class="card" style="margin-bottom:10px;padding:0;overflow:hidden">' +
        '<div data-cnmo="' + h(k.khach) + '" style="padding:13px 14px;cursor:pointer;display:flex;align-items:center;gap:10px">' +
        '<div style="flex:1;min-width:0"><b style="font-size:15.5px">' + h(k.ten) + '</b>' +
        '<div style="font-size:12.5px;color:' + mau + ';font-weight:700;margin-top:2px">' +
        k.so_hd + ' hoá đơn · nợ lâu nhất ' + k.so_ngay + ' ngày</div></div>' +
        '<b style="font-size:16px;white-space:nowrap">' + money(k.tien) + ' đ</b>' +
        '<span style="color:#c3c8d4;font-size:20px">' + (mo ? '▾' : '▸') + '</span></div>';
      if (mo) {
        html += '<div style="border-top:1px solid #f0f2f6;padding:4px 14px 12px">';
        (k.hd || []).forEach(function (d) {
          var on = !!chon[d.name];
          html += '<div data-cnhd="' + h(k.khach) + '|' + h(d.name) + '" style="display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid #f6f7f9;cursor:pointer">' +
            '<span style="width:22px;height:22px;flex:none;border-radius:6px;border:2px solid ' + (on ? '#0d9488;background:#0d9488' : '#d7dce5') + ';color:#fff;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:900">' + (on ? '✓' : '') + '</span>' +
            '<div style="flex:1;min-width:0"><div style="font-size:13.5px">' + h(d.name) + '</div>' +
            '<div style="font-size:12px;color:#98a2b3">' + posNgayVn(d.ngay) + (d.nguon ? ' · ' + h(d.nguon) : '') + (d.quay ? ' · ' + h(d.quay) : '') + '</div></div>' +
            '<b style="white-space:nowrap">' + money(d.tien) + ' đ</b></div>';
        });
        html += '<div style="display:flex;gap:7px;flex-wrap:wrap;margin-top:10px">' +
          posChipNut('data-cnall="' + h(k.khach) + '"', 'Chọn hết', false) +
          posChipNut('data-cnnone="' + h(k.khach) + '"', 'Bỏ chọn', false, 1) + '</div>';
        html += '<button class="btn" data-cngom="' + h(k.khach) + '" style="margin-top:12px"' + (soChon ? '' : ' disabled') + '>' +
          (soChon ? '📤 Gom ' + soChon + ' hoá đơn · ' + money(tienChon) + ' đ thành phiếu đề nghị thanh toán' : 'Tick hoá đơn cần thu ở trên') + '</button>';
        html += '</div>';
      }
      html += '</div>';
    });
  } else {
    var CPL = [
      { k: '', nhan: 'Tất cả', loc: function () { return true; } },
      { k: 'Cho thu', nhan: '⏳ Chờ tiền', loc: function (p) { return p.trang_thai === 'Cho thu'; } },
      { k: 'Thu thieu', nhan: '⚠ Thu thiếu', loc: function (p) { return p.trang_thai === 'Thu thieu'; } },
      { k: 'Da thu du', nhan: '✅ Đã thu đủ', loc: function (p) { return p.trang_thai === 'Da thu du'; } },
      { k: 'het_han', nhan: '⌛ QR hết hạn', loc: function (p) { return p.het_han && p.trang_thai !== 'Da thu du'; } },
      { k: 'Huy', nhan: '🚫 Đã huỷ', loc: function (p) { return p.trang_thai === 'Huy'; } }
    ];
    var fp = locTim(CPL, cnLocPhieu); cnLocPhieu = fp.k;
    html += '<div class="card" style="padding:10px 12px">' + locHang(CPL, cnLocPhieu, 'data-cnlp', phieu) + '</div>';
    var dsP = phieu.filter(fp.loc);
    if (!dsP.length) html += '<div class="card"><div class="emp" style="padding:26px"><div class="e1">📭</div><div>Chưa có phiếu nào thuộc nhóm này.</div></div></div>';
    dsP.forEach(function (p) {
      var mau = p.trang_thai === 'Da thu du' ? '#15803d' : (p.trang_thai === 'Huy' ? '#98a2b3' : (p.het_han ? '#b91c1c' : '#b45309'));
      var nhan = p.trang_thai === 'Da thu du' ? '✅ Đã thu đủ' : (p.trang_thai === 'Huy' ? '🚫 Đã huỷ' : (p.trang_thai === 'Thu thieu' ? '⚠ Thu thiếu' : '⏳ Chờ tiền'));
      html += '<div class="card" data-cnxem="' + h(p.name) + '" style="margin-bottom:10px;padding:13px 14px;cursor:pointer">' +
        '<div style="display:flex;align-items:center;gap:10px;pointer-events:none">' +
        '<div style="flex:1;min-width:0"><b style="font-size:15px">' + h(p.ten_khach || p.khach) + '</b>' +
        '<div style="font-size:12.5px;color:#98a2b3;margin-top:2px">' + h(p.ma_phieu) + ' · ' + p.so_hd + ' hoá đơn · tạo ' + posNgayVn(p.ngay_tao) + '</div>' +
        '<div style="font-size:12.5px;color:' + mau + ';font-weight:700;margin-top:3px">' + nhan +
        (p.het_han && p.trang_thai !== 'Da thu du' ? ' · QR hết hạn ' + posNgayVn(p.han_qr) : '') +
        (p.sepay ? ' · SePay đã nhận ' + money(p.sepay) + ' đ' : '') + '</div></div>' +
        '<div style="text-align:right"><b style="font-size:16px">' + money(p.tong_tien) + ' đ</b>' +
        (p.con_thieu && p.trang_thai !== 'Huy' ? '<div style="font-size:12px;color:#b91c1c">còn ' + money(p.con_thieu) + ' đ</div>' : '') + '</div>' +
        '<span style="color:#c3c8d4;font-size:20px">›</span></div></div>';
    });
  }

  var b = frame('Công nợ phải thu', html);
  b.onclick = async function (e) {
    var t = e.target.closest('[data-cntab]');
    if (t) { cnTab = t.getAttribute('data-cntab'); return go(scrCongNo, true); }
    t = e.target.closest('[data-cnlp]');
    if (t) { cnLocPhieu = t.getAttribute('data-cnlp'); return go(scrCongNo, true); }
    t = e.target.closest('[data-cnmo]');
    if (t) { var m = t.getAttribute('data-cnmo'); cnKhachMo = cnKhachMo === m ? '' : m; return go(scrCongNo, true); }
    t = e.target.closest('[data-cnhd]');
    if (t) {
      var v = t.getAttribute('data-cnhd').split('|');
      cnChon[v[0]] = cnChon[v[0]] || {};
      cnChon[v[0]][v[1]] = !cnChon[v[0]][v[1]];
      return go(scrCongNo, true);
    }
    t = e.target.closest('[data-cnall]');
    if (t) {
      var ka = t.getAttribute('data-cnall');
      var kk = khach.filter(function (x) { return x.khach === ka; })[0] || { hd: [] };
      cnChon[ka] = {};
      (kk.hd || []).forEach(function (d) { cnChon[ka][d.name] = true; });
      return go(scrCongNo, true);
    }
    t = e.target.closest('[data-cnnone]');
    if (t) { cnChon[t.getAttribute('data-cnnone')] = {}; return go(scrCongNo, true); }
    t = e.target.closest('[data-cnxem]');
    if (t) return go(function () { scrCnPhieu(t.getAttribute('data-cnxem')); });
    t = e.target.closest('[data-cngom]');
    if (t) {
      var kg = t.getAttribute('data-cngom');
      var ds = Object.keys(cnChon[kg] || {}).filter(function (x) { return cnChon[kg][x]; });
      if (!ds.length) return;
      var kx = khach.filter(function (x) { return x.khach === kg; })[0] || {};
      var tien = (kx.hd || []).filter(function (d) { return ds.indexOf(d.name) >= 0; }).reduce(function (s2, d) { return s2 + d.tien; }, 0);
      var ok = await confirmSheet('Gom ' + ds.length + ' hoá đơn · ' + money(tien) + ' đ',
        (kx.ten || kg) + '\nMáy sinh một phiếu đề nghị thanh toán công nợ kèm mã QR MB Bank sống 7 ngày. Khách chuyển một lần, SePay tự khớp và tự xoá nợ.',
        'Tạo phiếu yêu cầu thanh toán công nợ');
      if (!ok) return;
      busy(true);
      try {
        var r = await api('vagabond.cong_no.tao_phieu', { khach: kg, hoa_don: JSON.stringify(ds) });
        busy(false);
        cnChon[kg] = {};
        toast('Đã tạo phiếu ' + r.ma_phieu);
        return go(function () { scrCnPhieu(r.name); });
      } catch (er) { busy(false); toast((er && er.message) || 'Không tạo được phiếu', 5000); }
    }
  };
}
var cnLocPhieu = '';

/* Chi tiet mot phieu doi no: ma QR de gui khach, danh sach hoa don trong
   phieu, va nut doi chieu SePay. */
async function scrCnPhieu(name) {
  frame('Phiếu đề nghị thanh toán', '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api('vagabond.cong_no.xem_phieu', { name: name }); }
  catch (e) { frame('Phiếu đề nghị thanh toán', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không đọc được') + '</div></div>'); return; }
  var du = d.sepay >= d.tong_tien - 1;
  var qr = d.qr || {};
  var url = qr.stk
    ? 'https://img.vietqr.io/image/' + (qr.bank || 'MB') + '-' + qr.stk + '-qr_only.png?amount=' + Math.round(d.tong_tien) +
      '&addInfo=' + encodeURIComponent(d.ma_phieu) + '&accountName=' + encodeURIComponent(qr.ten || '')
    : '';

  var html = '<div class="card" style="padding:14px">' +
    '<div style="display:flex;align-items:center;gap:10px">' +
    '<div style="flex:1"><div style="font-size:12px;color:#98a2b3">PHIẾU ĐỀ NGHỊ THANH TOÁN</div>' +
    '<b style="font-size:18px">' + h(d.ma_phieu) + '</b>' +
    '<div style="font-size:13.5px;color:#374151;margin-top:2px">' + h(d.ten_khach || d.khach) + '</div></div>' +
    '<div style="text-align:right"><b style="font-size:19px">' + money(d.tong_tien) + ' đ</b>' +
    '<div style="font-size:12px;color:#98a2b3">' + (d.dong || []).length + ' hoá đơn</div></div></div></div>';

  if (du) {
    html += '<div class="card" style="padding:18px;text-align:center;border:2px solid #16a34a;background:#f0fdf4">' +
      '<div style="font-size:34px">✅</div><div style="font-size:18px;font-weight:800;color:#15803d">ĐÃ NHẬN ĐỦ ' + money(d.sepay) + ' đ</div>' +
      '<div style="font-size:13px;color:#15803d;margin-top:4px">Công nợ của khách này đã sạch.</div></div>';
  } else {
    html += '<div class="card" style="padding:14px;text-align:center">' +
      (d.het_han
        ? '<div style="background:#fef2f2;border:1.5px solid #fecaca;color:#b91c1c;border-radius:9px;padding:9px;font-size:13px;font-weight:700;margin-bottom:10px">Mã QR đã quá hạn ' + posNgayVn(d.han_qr) + '. Huỷ phiếu này rồi gom lại phiếu mới.</div>'
        : '<div style="font-size:12.5px;color:#6b7280;margin-bottom:8px">Mã QR sống tới hết ngày <b>' + posNgayVn(d.han_qr) + '</b></div>') +
      (url ? '<img src="' + url + '" style="width:230px;height:230px;display:block;margin:0 auto;border:1px solid #eef0f4;border-radius:10px">' : '<div style="color:#b3261e;font-size:13px">Chưa khai số tài khoản nhận nên chưa sinh được QR.</div>') +
      (d.sepay ? '<div style="margin-top:8px;color:#b45309;font-weight:700">SePay đã nhận ' + money(d.sepay) + ' đ, còn thiếu ' + money(d.con_thieu) + ' đ</div>' : '') +
      '</div>';

    /* Khoi chu cho khach khong quet duoc QR (anh Viet 14/08/2026). Ke toan
       ben khach si chuyen tu app ngan hang cua cong ty ho, ben do khong co
       cho quet ma phai go tay bon dong nay. Bay ro, bam mot cai la chep. */
    var ckTien = d.sepay ? d.con_thieu : d.tong_tien;
    var DONG_CK = [
      ['Ngân hàng', qr.bank || '', 0],
      ['Số tài khoản', qr.stk || '', 1],
      ['Tên tài khoản', qr.ten || '', 0],
      ['Số tiền', money(ckTien) + ' đ', 1],
      ['Nội dung chuyển khoản', d.ma_phieu || '', 1]
    ];
    html += '<div class="card" style="padding:12px 14px">' +
      '<div style="font-size:11.5px;font-weight:800;color:#0f766e;letter-spacing:.4px">CHUYỂN KHOẢN THỦ CÔNG</div>' +
      '<div style="font-size:12px;color:#6b7280;margin-top:3px;line-height:1.5">Dành cho khách không quét được mã QR. Bấm vào dòng để chép.</div>' +
      DONG_CK.map(function (x, i) {
        return '<div data-cnck="' + i + '" data-cnv="' + h(x[1]) + '" style="display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid #f1f3f6;cursor:pointer">' +
          '<span style="flex:0 0 42%;font-size:12.5px;color:#6b7280">' + h(x[0]) + '</span>' +
          '<b style="flex:1;min-width:0;font-size:' + (x[2] ? '15px' : '13.5px') + ';word-break:break-all">' + (x[1] ? h(x[1]) : '<span style="color:#b3261e;font-weight:400">chưa khai</span>') + '</b>' +
          (x[1] ? '<span style="font-size:15px;color:#98a2b3">📋</span>' : '') + '</div>';
      }).join('') +
      '</div>';
  }

  html += '<div class="sec">Hoá đơn trong phiếu</div><div class="card" style="padding:6px 14px">';
  (d.dong || []).forEach(function (x) {
    html += '<div style="display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid #f6f7f9">' +
      '<div style="flex:1;min-width:0"><div style="font-size:13.5px">' + h(x.hoa_don) + '</div>' +
      '<div style="font-size:12px;color:#98a2b3">' + posNgayVn(x.ngay) + (x.nguon ? ' · ' + h(x.nguon) : '') + '</div></div>' +
      '<b style="white-space:nowrap">' + money(x.so_tien) + ' đ</b></div>';
  });
  html += '</div>';
  if (d.ghi_chu) html += '<div class="card" style="padding:12px 14px;font-size:13px;white-space:pre-wrap">' + h(d.ghi_chu) + '</div>';

  var foot = '<div style="display:flex;gap:8px;flex-wrap:wrap">' +
    '<button class="btn" id="cnXuat" style="flex:1;margin:0">📄 Xuất phiếu</button>' +
    '<button class="btn gh" id="cnKiem" style="flex:1;margin:0">🔄 Đối chiếu SePay</button>' +
    (du ? '<button class="btn gh" id="cnThu" style="flex:1;margin:0">✉️ Thư báo</button>'
        : '<button class="btn gh" id="cnKhop" style="flex:1;margin:0">🔎 Khớp tay</button>') +
    (du || d.trang_thai === 'Huy' ? '' : '<button class="btn gh" id="cnHuy" style="flex:0 0 34%;margin:0;color:#b3261e">Huỷ phiếu</button>') +
    '</div>';
  var b = frame('Phiếu ' + h(d.ma_phieu), html, { footer: foot });
  Array.prototype.forEach.call(document.querySelectorAll('[data-cnck]'), function (el) {
    el.onclick = function () {
      var v = el.getAttribute('data-cnv') || '';
      if (v) hsCopy(v);
    };
  });
  var nkhop = document.getElementById('cnKhop');
  if (nkhop) nkhop.onclick = function () { cnKhopTay(d); };
  var nthu = document.getElementById('cnThu');
  if (nthu) nthu.onclick = async function () {
    var xt;
    try { xt = await api('vagabond.cong_no.xem_truoc_thu', { name: name }); } catch (e) { return baoTin((e && e.message) || 'Không xem trước được'); }
    if (!xt.email) return baoTin('Khách này chưa có email trên hệ nên chưa gửi thư báo được. Vào Danh sách khách hàng điền email rồi quay lại.');
    if (!await hoiCo('Gửi thư báo nhận tiền', 'Gửi thư xác nhận đã nhận ' + money(d.sepay || d.tong_tien) + ' đ tới ' + xt.email + '?', 'Gửi')) return;
    busy(true);
    try { var kq = await api('vagabond.cong_no.gui_thu_da_nhan', { name: name }); busy(false); toast(kq.loi_nhan, 4500); }
    catch (e) { busy(false); baoTin((e && e.message) || 'Gửi thư lỗi'); }
  };
  document.getElementById('cnXuat').onclick = async function () {
    busy(true);
    try {
      var fl = await api('vagabond.cong_no.xuat_phieu', { name: name });
      busy(false); bcTaiVe(fl.ten_file, fl.b64, fl.kieu); toast('Đã tải ' + fl.ten_file, 4000);
    } catch (e) { busy(false); baoTin((e && e.message) || 'Xuất phiếu lỗi'); }
  };
  document.getElementById('cnKiem').onclick = async function () {
    busy(true);
    try { var r = await api('vagabond.cong_no.kiem_sepay', { name: name }); busy(false); toast(r.sepay >= r.tong_tien - 1 ? 'Tiền đã về đủ, đã xoá nợ.' : 'SePay mới nhận ' + money(r.sepay) + ' đ.', 4000); go(function () { scrCnPhieu(name); }, true); }
    catch (e) { busy(false); toast((e && e.message) || 'Không đối chiếu được', 4000); }
  };
  var nh = document.getElementById('cnHuy');
  if (nh) nh.onclick = async function () {
    var ok = await confirmSheet('Huỷ phiếu ' + d.ma_phieu, 'Các hoá đơn trong phiếu sẽ quay lại danh sách chờ gom. Mã QR này sẽ không dùng nữa.', 'Huỷ phiếu');
    if (!ok) return;
    busy(true);
    try { await api('vagabond.cong_no.huy_phieu', { name: name, ly_do: S.me.full_name || S.user }); busy(false); toast('Đã huỷ phiếu.'); go(scrCongNo); }
    catch (e) { busy(false); toast((e && e.message) || 'Không huỷ được', 4000); }
  };
}


/* ---------- Danh sach khach hang (anh Viet 11/08/2026) ----------

Tra cuu khach: ai la khach si ai la khach le, ai dang o hang nao, da chi
bao nhieu trong nam. Chi tieu tinh tren hoa don DA GHI SO trong 12 thang -
don con o ban nhap chua phai tien that.

Hang do doctype "Vagabond Hang Khach" giu, khong nhet trong ma, nen anh
Viet chot muc chi tieu luc nao thi sua o do la xong. */
var khDang = '', khHang = '', khTim = '', khData = null;

async function scrKhachHang() {
  frame('Danh sách khách hàng', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc danh mục khách...</div></div>');
  var kq, kh;
  try {
    kq = await api('vagabond.khach_hang.ds_khach', { tu_khoa: khTim, dang: khDang, hang: khHang });
    kh = await api('vagabond.khach_hang.ds_hang', {});
  } catch (e) {
    frame('Danh sách khách hàng', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>');
    return;
  }
  khData = kq;
  var all = (kq && kq.khach) || [], hangs = (kh && kh.hang) || [];

  var DANG = [
    { k: '', nhan: 'Tất cả', loc: function () { return true; } },
    { k: 'si', nhan: '🏢 Khách sỉ', loc: function (x) { return !!x.si; } },
    { k: 'le', nhan: '🧍 Khách lẻ', loc: function (x) { return !x.si; } }
  ];
  var HANG = [{ k: '', nhan: 'Mọi hạng', loc: function () { return true; } }];
  hangs.forEach(function (hg) {
    HANG.push({
      k: hg.name,
      /* Anh the hang ngay tren chip loc: nhin mau nen la biet hang nao,
         khong phai doc ten (anh Viet 12/08/2026). */
      nhan: hangChipAnh(hg, 14) + h(hg.ten_hang) + (hg.giam_gia ? ' −' + money(hg.giam_gia) + '%' : ''),
      loc: function (x) { return x.hang === hg.name; }
    });
  });
  HANG.push({ k: '_chua', nhan: '· Chưa xếp hạng', loc: function (x) { return !x.hang; } });

  var fD = locTim(DANG, khDang); khDang = fD.k;
  var fH = locTim(HANG, khHang); khHang = fH.k;
  /* May chu da loc san theo dang va hang roi (khong the loc o day duoc vi
     danh muc hon 1500 khach, chi tai ve mot phan). */
  var ds = all;
  var tong = ds.reduce(function (t, x) { return t + x.tien; }, 0);

  var html = '<div class="card" style="padding:12px 14px;display:flex;gap:10px">' +
    '<div style="flex:1"><div style="font-size:12px;color:#98a2b3">ĐANG XEM</div>' +
    '<div style="font-size:19px;font-weight:800">' + (kq.tong_so || ds.length) + ' khách</div>' +
    '<div style="font-size:12px;color:#98a2b3">' + kq.so_si + ' sỉ · ' + kq.so_le + ' lẻ</div></div>' +
    '<div style="flex:1;border-left:1px solid #eef0f4;padding-left:10px"><div style="font-size:12px;color:#98a2b3">CHI TIÊU 12 THÁNG</div>' +
    '<div style="font-size:19px;font-weight:800;color:#0f766e">' + money(tong) + ' đ</div></div></div>';

  html += '<div class="card" style="padding:10px 12px">' +
    '<input class="tin" id="khO" placeholder="Tìm theo tên, mã, mã số thuế, số điện thoại..." value="' + h(khTim) + '" style="margin-bottom:8px"></div>';
  var chipHang = function (ds2, chon, attr) {
    return '<div style="flex:0 0 auto;display:flex;gap:7px;padding:2px 0;overflow-x:auto;-webkit-overflow-scrolling:touch">' +
      ds2.map(function (c) { return posChipNut(attr + '="' + h(c.k) + '"', c.nhan, c.k === chon); }).join('') + '</div>';
  };
  html += '<div class="card" style="padding:10px 12px;display:flex;flex-direction:column;gap:7px">' +
    chipHang(DANG, khDang, 'data-khd') +
    chipHang(HANG, khHang, 'data-khh') + '</div>';

  if (!hangs.length) {
    html += '<div class="card" style="padding:12px 14px;background:#fffbeb;border:1.5px solid #fcd34d;font-size:13px;color:#92400e">' +
      'Chưa cấu hình hạng khách nào. Vào Desk mở danh mục <b>Vagabond Hang Khach</b> để điền mức chi tiêu và phần trăm giảm cho từng hạng.</div>';
  }

  html += '<div class="sec">Khách · chi nhiều nhất lên đầu</div><div class="card" style="padding:6px 14px">';
  if (!ds.length) html += '<div class="emp" style="padding:24px"><div class="e1">🔍</div><div>Không có khách nào thuộc nhóm này.</div></div>';
  ds.slice(0, 200).forEach(function (x) {
    var hg = hangs.filter(function (y) { return y.name === x.hang; })[0];
    html += '<div data-khx="' + h(x.ma) + '" style="display:flex;align-items:center;gap:10px;padding:11px 0;border-bottom:1px solid #f6f7f9;cursor:pointer">' +
      /* Anh the to han va dung ti le the (1.586:1), ten hang nam DUOI the
         chu khong nhet chung mot chip (anh Viet 13/08/2026). Chip cu chi
         hien duoc mot lat cat 14px cua the nen nhin nhu bi lech. */
      (hg && hg.anh
        /* 68px chu khong phai 62: ten hang dai nhat la VAGABONDER, o 62px
           thi bi cat thanh "VAGABOND..." (thay khi chay that 13/08/2026). */
        ? '<div style="width:68px;flex:none;text-align:center">' +
          '<img src="' + h(hg.anh) + '" alt="" loading="lazy" style="width:68px;aspect-ratio:1.586;object-fit:cover;border-radius:5px;border:1px solid #e5e7eb;display:block;background:#f2f4f7">' +
          '<div style="font-size:8px;font-weight:800;color:#92400e;margin-top:3px;line-height:1.2;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + h(hg.ten_hang) + '</div></div>'
        : '<span style="width:38px;height:38px;flex:none;border-radius:10px;background:' + (x.si ? '#eef2ff' : '#f0fdfa') + ';display:flex;align-items:center;justify-content:center;font-size:18px">' + (x.si ? '🏢' : '🧍') + '</span>') +
      '<div style="flex:1;min-width:0"><div style="font-size:14.5px;font-weight:600">' + h(x.ten) + '</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:4px">' +
      (hg
        ? (hg.anh
          /* The da hien ten hang roi, o day chi con nhac quyen loi giam
             gia - lap lai ten hang lan nua la thua cho tren dong hep. */
          ? (hg.giam_gia
            ? '<span style="background:#fef3c7;color:#92400e;border:1.5px solid #fcd34d;border-radius:999px;padding:2px 9px;font-size:11.5px;font-weight:800">giảm ' + money(hg.giam_gia) + '%</span>'
            : '')
          : '<span style="display:inline-flex;align-items:center;background:#fef3c7;color:#92400e;border:1.5px solid #fcd34d;border-radius:999px;padding:2px 9px;font-size:11.5px;font-weight:800">' + h(hg.ten_hang) + (hg.giam_gia ? ' · −' + money(hg.giam_gia) + '%' : '') + '</span>')
        : '<span style="background:#f6f7f9;color:#98a2b3;border:1.5px dashed #d7dce5;border-radius:999px;padding:2px 9px;font-size:11.5px">chưa xếp hạng</span>') +
      /* Ma khach hien ngay tren dong (anh Viet 11/08/2026): tra cuu, doi
         chieu voi phieu giay va goi dien cho nhau deu can doc ma. */
      '<span style="background:#f1f5f9;color:#475569;border:1.5px solid #e2e8f0;border-radius:999px;padding:2px 9px;font-size:11.5px;font-family:ui-monospace,monospace">' + h(x.ma) + '</span>' +
      (x.mst ? '<span style="background:#eef2ff;color:#3730a3;border-radius:999px;padding:2px 9px;font-size:11.5px">MST ' + h(x.mst) + '</span>' : '') +
      (x.dt ? '<span style="background:#f0fdfa;color:#0f766e;border-radius:999px;padding:2px 9px;font-size:11.5px">' + h(x.dt) + '</span>' : '') +
      '</div></div>' +
      '<div style="text-align:right;flex:none"><b style="font-size:14.5px">' + money(x.tien) + ' đ</b>' +
      '<div style="font-size:11.5px;color:#98a2b3">' + x.so_don + ' hoá đơn</div></div>' +
      '<span style="color:#c3c8d4;font-size:18px">›</span></div>';
  });
  var conLai = Math.max(0, (kq.tong_so || ds.length) - Math.min(ds.length, 200));
  if (conLai) html += '<div style="padding:10px 0;text-align:center;font-size:12.5px;color:#98a2b3">Nhóm này có <b>' + (kq.tong_so || ds.length) + ' khách</b>, đang hiện ' + Math.min(ds.length, 200) + '. Gõ tìm để ra đúng khách cần.</div>';
  html += '</div>';

  var b = frame('Danh sách khách hàng', html);
  var o = document.getElementById('khO');
  if (o) {
    var tre = null;
    o.oninput = function () {
      if (tre) clearTimeout(tre);
      tre = setTimeout(function () { khTim = o.value; go(scrKhachHang, true); }, 320);
    };
  }
  b.onclick = function (e) {
    var t = e.target.closest('[data-khd]');
    if (t) { khDang = t.getAttribute('data-khd'); return go(scrKhachHang, true); }
    t = e.target.closest('[data-khh]');
    if (t) { khHang = t.getAttribute('data-khh'); return go(scrKhachHang, true); }
    t = e.target.closest('[data-khx]');
    if (t) { khMa = t.getAttribute('data-khx'); return go(scrKhachChiTiet); }
  };
}

/* Bang gan hang cho mot khach. Co hien ca hang MAY GOI Y theo chi tieu de
   quan ly doi chieu, nhung KHONG tu doi - len hang la quyet dinh cua
   nguoi, khong phai cua may. */
async function khSheetHang(ma, hangs, all) {
  var x = all.filter(function (y) { return y.ma === ma; })[0] || {};
  var gy = {};
  try { gy = await api('vagabond.khach_hang.goi_y_hang', { khach: ma }); } catch (e) { }
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  var html = '<div class="shh"><b>' + h(x.ten || ma) + '</b><div class="x">&times;</div></div>' +
    '<div style="padding:4px 14px calc(env(safe-area-inset-bottom,0px) + 14px)">' +
    '<div style="font-size:12.5px;color:#6b7280;margin-bottom:10px">' +
    h(x.nhom || 'chưa gắn nhóm') + ' · đã chi <b>' + money(x.tien) + ' đ</b> qua ' + x.so_don + ' hoá đơn' +
    (x.gan_nhat ? ' · gần nhất ' + posNgayVn(x.gan_nhat) : '') + '</div>';
  if (gy && gy.hang) {
    html += '<div style="background:#ecfeff;border:1.5px solid #7fe5f6;border-radius:9px;padding:9px 11px;font-size:12.5px;color:#0b7c93;margin-bottom:10px">' +
      'Theo chi tiêu ' + money(gy.tien) + ' đ trong ' + (gy.so_thang || 12) + ' tháng, khách này <b>đủ điều kiện hạng ' + h(gy.hang) + '</b>.</div>';
  }
  html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin-bottom:7px">GẮN HẠNG</div>' +
    '<div style="display:flex;flex-wrap:wrap;gap:7px">' +
    hangs.map(function (hg) {
      return posChipNut('data-sethang="' + h(hg.name) + '"',
        hangChipAnh(hg, 16) + h(hg.ten_hang) + (hg.giam_gia ? ' −' + money(hg.giam_gia) + '%' : ''), x.hang === hg.name);
    }).join('') +
    (x.hang ? posChipNut('data-sethang=""', '✕ Bỏ hạng', false, 1) : '') +
    '</div>';
  var mt = hangs.filter(function (hg) { return (hg.mo_ta || '').trim(); });
  if (mt.length) {
    html += '<div style="margin-top:14px;font-size:12px;color:#98a2b3;line-height:1.6">' +
      mt.map(function (hg) { return '<b>' + h(hg.ten_hang) + ':</b> ' + h(hg.mo_ta); }).join('<br>') + '</div>';
  }
  html += '</div>';
  box.innerHTML = html;
  ov.appendChild(box); document.body.appendChild(ov);
  function dong() { ov.remove(); }
  ov.onclick = function (e) { if (e.target === ov) dong(); };
  box.querySelector('.x').onclick = dong;
  box.addEventListener('click', async function (e) {
    var t = e.target.closest('[data-sethang]'); if (!t) return;
    var hg = t.getAttribute('data-sethang');
    busy(true);
    try {
      await api('vagabond.khach_hang.dat_hang', { khach: ma, hang: hg });
      busy(false); dong();
      toast(hg ? 'Đã xếp ' + (x.ten || ma) + ' vào hạng ' + hg : 'Đã bỏ hạng của ' + (x.ten || ma));
      go(scrKhachHang, true);
    } catch (er) { busy(false); toast((er && er.message) || 'Không đặt được hạng', 4000); }
  });
}

/* ---------- Chot ca: cong so cuoi ca cua MOT quay (anh Viet 09/08/2026) ----------
   Tien mat phai co trong ket, CK doi voi SePay da ve, tam tinh con treo,
   bill chua ghi so - lech la thay ngay truoc khi giao ca. */
async function scrPosChotCa() {
  if (!posQuay) return go(scrPosChonQuay, true);
  frame('Chốt ca · ' + (posQuay.ma || ''), '<div class="emp"><div class="e1">⏳</div><div>Đang cộng sổ ca hôm nay...</div></div>');
  var k;
  try { k = await api('vagabond.ban_hang.pos_chot_ca', { quay: posQuay.ma || '', ngay: posDsNgay || today() }); }
  catch (e) { frame('Chốt ca · ' + (posQuay.ma || ''), '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var dRow = function (nhan, tien, phu, mau) {
    return '<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #f0f2f6">' +
      '<span style="flex:1;min-width:0">' + nhan + (phu ? '<div style="font-size:12px;color:#98a2b3">' + phu + '</div>' : '') + '</span>' +
      '<b style="white-space:nowrap;margin-left:8px' + (mau ? ';color:' + mau : '') + '">' + money(tien) + ' đ</b></div>';
  };
  var html = '<div class="card" style="padding:12px 14px"><b>Ca ngày ' + h(k.ngay || today()) + ' · quầy ' + h(k.quay || '') + '</b>' +
    '<div style="font-size:12px;color:#98a2b3">' + (k.tong_bill || 0) + ' hoá đơn doanh thu · tổng ' + money(k.tong_tien || 0) + ' đ</div></div>';
  html += '<div class="sec">Tiền theo phương thức</div><div class="card" style="padding:6px 14px">';
  (k.pt || []).forEach(function (p) {
    var laTm = p.pt === 'Tiền mặt';
    html += dRow((laTm ? '💵 ' : '') + h(p.pt) + ' · ' + p.so + ' hoá đơn', p.tien,
      laTm ? 'PHẢI CÓ ĐỦ TRONG KÉT khi giao ca' : '', laTm ? '#b45309' : '');
  });
  if (!(k.pt || []).length) html += '<div style="padding:16px 0;color:#98a2b3;text-align:center">Chưa có hoá đơn doanh thu nào.</div>';
  html += '</div>';
  /* Tien CHUA nam trong ket luc giao ca: Grab Dine-Out Grab giu den T+1,
     Cong no khach si con thieu. Tach hin ra de thu ngan dem tien mat khong
     bi lech va quan ly biet con bao nhieu phai di doi (anh Viet 10/08/2026). */
  var cv = k.chua_ve || { so: 0, tien: 0, dong: [] };
  if (cv.so) {
    html += '<div class="sec">Tiền chưa về két</div><div class="card" style="padding:6px 14px;border:1.5px solid #fcd34d;background:#fffbeb">';
    (cv.dong || []).forEach(function (p) {
      html += dRow('⏳ ' + h(p.pt) + ' · ' + p.so + ' hoá đơn', p.tien,
        p.pt === 'Công nợ' ? 'khách sỉ gom hoá đơn, theo dõi ở Công nợ phải thu' : 'Grab giữ tiền, chuyển về tiệm ngày T+1', '#b45309');
    });
    html += dRow('<b>Cộng chưa về</b>', cv.tien, 'KHÔNG đếm số này trong két tiền mặt', '#b45309');
    html += '</div>';
  }
  html += '<div class="sec">Đối soát chuyển khoản (SePay)</div><div class="card" style="padding:6px 14px">' +
    dRow('✅ SePay đã nhận', k.ck_ve || 0, 'khớp theo mã hoá đơn VGB trong nội dung CK', '#0f766e');
  (k.ck_thieu || []).forEach(function (c) {
    html += dRow('⚠ ' + h(c.bill) + ' còn thiếu', c.thieu, 'kiểm với khách / SePay trước khi ghi sổ', '#b91c1c');
  });
  if (!(k.ck_thieu || []).length) html += '<div style="padding:8px 0;color:#15803d;font-size:13px">Không hoá đơn chuyển khoản nào thiếu tiền 👍</div>';
  html += '</div>';
  var tt = k.tam_tinh || { so: 0, tien: 0 };
  var tRow = function (nhan, gia, mau, phu) {
    return '<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #f0f2f6">' +
      '<span style="flex:1;min-width:0">' + nhan + (phu ? '<div style="font-size:12px;color:#98a2b3">' + phu + '</div>' : '') + '</span>' +
      '<b style="white-space:nowrap;margin-left:8px' + (mau ? ';color:' + mau : '') + '">' + gia + '</b></div>';
  };
  html += '<div class="sec">Sổ sách trước khi giao ca</div><div class="card" style="padding:6px 14px">' +
    tRow('📒 Đã ghi sổ', (k.da_ghi || 0) + ' hoá đơn', '') +
    tRow('📄 Chưa ghi sổ', (k.chua_ghi || 0) + ' hoá đơn', k.chua_ghi ? '#b91c1c' : '#15803d', k.chua_ghi ? 'vào Hoá đơn hôm nay ghi sổ hết rồi hãy chốt ca' : '') +
    tRow('🕐 Tạm tính còn treo', tt.so + ' hoá đơn · ' + money(tt.tien) + ' đ', tt.so ? '#c2410c' : '#15803d') + '</div>';
  frame('Chốt ca · ' + (posQuay.ma || ''), html, { footer: '<button class="btn" id="ccIn">🖨 In bảng chốt ca</button>' });
  document.getElementById('ccIn').onclick = function () { posInChotCa(k); };
}

function posInChotCa(k) {
  var w = window.open('', '_blank');
  if (!w) return toast('Trình duyệt chặn cửa sổ in. Cho phép popup rồi bấm lại.', 4000);
  var gio = new Date();
  var hs = function (n) { return (n < 10 ? '0' : '') + n; };
  var lucIn = hs(gio.getHours()) + ':' + hs(gio.getMinutes()) + ' ' + hs(gio.getDate()) + '/' + hs(gio.getMonth() + 1) + '/' + gio.getFullYear();
  var dd = function (a, b) { return '<div class="d"><span>' + a + '</span><b>' + b + '</b></div>'; };
  var tt = k.tam_tinh || { so: 0, tien: 0 };
  var thanPt = (k.pt || []).map(function (p) { return dd(h(p.pt) + ' (' + p.so + ' hoá đơn)', money(p.tien) + ' đ'); }).join('');
  var thanThieu = (k.ck_thieu || []).map(function (c) { return dd('Thiếu ' + h(c.bill), money(c.thieu) + ' đ'); }).join('');
  w.document.write('<html><head><meta charset="utf-8"><title>Chốt ca ' + h(k.quay || '') + '</title><style>' +
    '@page{size:' + inKho('chot_ca').css + ';margin:0}*{margin:0;padding:0;box-sizing:border-box}' +
    'body{width:' + inKho('chot_ca').rong + 'mm;margin:0 auto;font-family:Arial,sans-serif;font-size:11.5px;color:#000;padding:4mm 0 6mm}' +
    'h1{font-size:14px;text-align:center;letter-spacing:.08em}' +
    '.ph{text-align:center;font-size:10.5px;margin-bottom:2mm;line-height:1.5}' +
    'hr{border:0;border-top:1px dashed #000;margin:2mm 0}' +
    '.d{display:flex;justify-content:space-between;padding:.6mm 0}' +
    '.s{font-weight:bold;margin-top:1.5mm}' +
    '</style></head><body>' +
    '<h1>BẢNG CHỐT CA</h1>' +
    '<div class="ph">' + h((posQuay && posQuay.ten) || k.quay || '') + '<br>Ngày ' + h(k.ngay || '') + ' · in lúc ' + lucIn + '<br>Người chốt: ' + h(S.me.full_name || String(S.user).split('@')[0]) + '</div>' +
    '<hr><div class="s">TIỀN THEO PHƯƠNG THỨC</div>' + (thanPt || dd('Chưa có hoá đơn', '')) +
    '<hr><div class="s">ĐỐI SOÁT CHUYỂN KHOẢN</div>' +
    dd('SePay đã nhận', money(k.ck_ve || 0) + ' đ') + (thanThieu || dd('Không hoá đơn nào thiếu', '&#10003;')) +
    '<hr><div class="s">SỔ SÁCH</div>' +
    dd('Đã ghi sổ', (k.da_ghi || 0) + ' hoá đơn') + dd('Chưa ghi sổ', (k.chua_ghi || 0) + ' hoá đơn') +
    dd('Tạm tính còn treo', tt.so + ' hoá đơn · ' + money(tt.tien) + ' đ') +
    '<hr>' + dd('TỔNG DOANH THU', money(k.tong_tien || 0) + ' đ') +
    '<div style="margin-top:6mm;display:flex;justify-content:space-between;font-size:10.5px;text-align:center"><span>Người giao ca<br><br><br>____________</span><span>Người nhận ca<br><br><br>____________</span></div>' +
    '<script>window.onload=function(){setTimeout(function(){window.print()},900)}<' + '/script>' +
    '</body></html>');
  w.document.close();
}

/* ---------- Hop dong Event: catering, teabreak, banh thiet ke ---------- */
var hdLoc = null;
async function scrHopDong() {
  frame('Hợp đồng Event', '<div class="emp"><div class="e1">⏳</div><div>Đang tải hợp đồng...</div></div>');
  var ds;
  try { ds = await api('vagabond.hop_dong.danh_sach', hdLoc ? { trang_thai: hdLoc } : {}); }
  catch (e) { frame('Hợp đồng Event', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var html = '<div class="card" style="padding:12px 14px;display:flex;align-items:center;gap:12px">' +
    '<div style="font-weight:600">Trạng thái</div>' +
    '<button class="btn gh" id="hdLoc" style="flex:1;margin:0">' + h(hdLoc || 'Tất cả') + ' ▾</button></div>';
  html += '<div class="sec">' + ds.length + ' hợp đồng · bấm vào để xem chi tiết</div><div class="card">';
  if (!ds.length) html += '<div class="emp" style="padding:24px"><div class="e1">📑</div><div>Chưa có hợp đồng nào. Bấm dấu ➕ để tạo.</div></div>';
  var HDICON = { 'Nháp': '📝', 'Đang thực hiện': '🚚', 'Hoàn tất': '✅', 'Đã thanh lý': '🧾', 'Huỷ': '⛔' };
  ds.forEach(function (r) {
    html += '<div class="hub" data-hd="' + h(r.name) + '"><div class="hi">' + (HDICON[r.trang_thai] || '📑') + '</div>' +
      '<div class="ht"><div class="h1">' + h(r.ten) + '</div>' +
      '<div class="h2">' + h(r.so_hop_dong || r.name) + (r.khach_hang ? ' · ' + h(r.khach_hang) : '') + ' · ' + h(r.trang_thai) + '</div>' +
      '<div class="h2">Giá trị ' + money(r.gia_tri) + ' · đã xuất ' + money(r.da_xuat) + ' · đã thu ' + money(r.da_thu) + '</div></div></div>';
  });
  html += '</div>';
  var b = frame('Hợp đồng Event', html, { action: '➕', onAction: function () { go(scrHdTao); } });
  document.getElementById('hdLoc').onclick = function () {
    sheet('Lọc trạng thái', [
      { value: '', label: 'Tất cả', icon: '📚' },
      { value: 'Nháp', label: 'Nháp', icon: '📝' },
      { value: 'Đã gửi khách', label: 'Đã gửi khách', icon: '📧' },
      { value: 'Đang thương thảo', label: 'Đang thương thảo', icon: '✏️' },
      { value: 'Đang thực hiện', label: 'Đang thực hiện', icon: '🚚' },
      { value: 'Hoàn tất', label: 'Hoàn tất', icon: '✅' },
      { value: 'Đã thanh lý', label: 'Đã thanh lý', icon: '🧾' },
      { value: 'Huỷ', label: 'Huỷ', icon: '⛔' }
    ], hdLoc || '', function (o) { hdLoc = o.value || null; go(scrHopDong, true); });
  };
  b.addEventListener('click', function (e) {
    var r = e.target.closest('[data-hd]'); if (!r) return;
    var nm = r.getAttribute('data-hd');
    go(function () { scrHdView(nm); });
  });
}

async function scrHdView(name) {
  frame('Chi tiết hợp đồng', '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api('vagabond.hop_dong.chi_tiet', { name: name }); }
  catch (e) { frame('Chi tiết hợp đồng', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không đọc được') + '</div></div>'); return; }
  var hd = d.hop_dong;
  var vn = function (s) { var p = String(s || '').split('-'); return p.length === 3 ? p[2] + '/' + p[1] + '/' + p[0] : (s || ''); };
  var html = '<div class="card" style="padding:12px 14px;line-height:1.7">' +
    '<div style="display:flex;justify-content:space-between;gap:8px;align-items:center"><b style="flex:1">' + h(hd.ten) + '</b><button class="btn gh" id="hdTt" style="margin:0;padding:4px 10px;font-size:13px;width:auto;flex:none;white-space:nowrap">' + h(hd.trang_thai) + ' ▾</button></div>' +
    '<div style="color:#6b7280;font-size:13px">' + h(hd.name) + (hd.so_hop_dong ? ' · Số HĐ: <b>' + h(hd.so_hop_dong) + '</b>' : '') + '</div>' +
    '<div style="font-size:13px">' + h(hd.loai || '') + (hd.khach_hang ? ' · ' + h(hd.khach_hang) : '') + '</div>' +
    ((hd.ngay_ky || hd.ngay_su_kien) ? '<div style="font-size:13px">' + (hd.ngay_ky ? 'Ký ' + vn(hd.ngay_ky) : '') + (hd.ngay_su_kien ? ' · Sự kiện ' + vn(hd.ngay_su_kien) : '') + '</div>' : '') +
    (hd.mo_ta ? '<div style="font-size:13px;color:#6b7280;white-space:pre-wrap;margin-top:4px">' + h(hd.mo_ta) + '</div>' : '') +
    '</div>';
  html += '<div class="card" style="padding:12px 14px">' +
    '<div style="display:flex;justify-content:space-between"><span>Giá trị hợp đồng</span><b>' + money(hd.gia_tri) + ' đ</b></div>' +
    '<div style="display:flex;justify-content:space-between;margin-top:6px"><span>Đã xuất hoá đơn</span><b>' + money(d.da_xuat) + ' đ · ' + d.so_hd_chot + ' chốt' + (d.so_hd_nhap ? ' + ' + d.so_hd_nhap + ' nháp' : '') + '</b></div>' +
    '<div style="display:flex;justify-content:space-between;margin-top:6px"><span>Đã thu</span><b style="color:#0a8a4a">' + money(d.da_thu) + ' đ</b></div>' +
    '<div style="display:flex;justify-content:space-between;margin-top:6px"><span>Còn phải thu</span><b style="color:#b3261e">' + money(d.con_no) + ' đ</b></div></div>';
  html += hdKhoiThuongThao(hd, d);
  html += '<div class="sec">Hoá đơn thuộc hợp đồng · bấm vào để xem hoặc gỡ</div><div class="card">';
  if (!d.hoa_don.length) html += '<div class="emp" style="padding:20px"><div class="e1">🧾</div><div>Chưa gắn hoá đơn nào.</div></div>';
  d.hoa_don.forEach(function (r) {
    html += '<div class="hub" data-si="' + h(r.name) + '"><div class="hi">' + (r.docstatus === 1 ? '✅' : '📝') + '</div>' +
      '<div class="ht"><div class="h1">' + h(r.name) + '</div><div class="h2">' + vn(r.posting_date) + ' · ' + h(r.customer_name || '') + '</div></div>' +
      '<b style="white-space:nowrap;font-size:13px">' + money(r.grand_total) + '</b></div>';
  });
  html += '</div>';
  /* ---- Khoi hop dong phap ly (anh Viet 18/08/2026) ----
     Chi hien khi hop dong co goc la mot to bao gia da chot: to phap ly lay
     tung dong hang tu do ra, va bao gia cung chinh la Phu luc 01. Hop dong
     go tay khong co goc thi khong bay nut ra roi bam vao chi de nhan cau
     bao loi. */
  if (hd.bao_gia) {
    html += '<div class="sec">Hợp đồng pháp lý</div><div class="card" style="padding:12px 14px;line-height:1.7">' +
      '<div style="font-size:13px">Lập từ báo giá <b>' + h(hd.bao_gia) + '</b>, tờ này được đính kèm làm <b>Phụ lục 01</b> trong cùng tệp PDF.</div>' +
      (hd.ten_khach ? '<div style="font-size:13px;margin-top:4px">Bên A: <b>' + h(hd.ten_khach) + '</b>' + (hd.ma_so_thue ? ' · MST ' + h(hd.ma_so_thue) : '') + '</div>' : '') +
      (hd.dai_dien ? '<div style="font-size:13px">Đại diện: ' + h(hd.dai_dien) + (hd.chuc_vu ? ' - ' + h(hd.chuc_vu) : '') + '</div>' : '') +
      (hd.email ? '<div style="font-size:13px">Email nhận hợp đồng: ' + h(hd.email) + '</div>' : '<div style="font-size:12.5px;color:#b3261e">Chưa có email bên A, chưa gửi thư được.</div>') +
      (hd.dat_coc_pt ? '<div style="font-size:13px">Điều 2 chia hai đợt: đợt 1 ' + hd.dat_coc_pt + '% (' + money(hd.dat_coc_tien) + ' đ), đợt 2 phần còn lại.</div>'
                     : '<div style="font-size:13px">Điều 2: thanh toán một lần 100% trước khi giao.</div>') +
      /* Hai dong duoi day la hai cho anh Viet bat loi hom 18/08/2026: khoi
         chu ky in ra ten Sales, va phu luc dinh kem la ban may dung chu
         khong phai ban khach da ky. Bay thang len man chi tiet de nhin mot
         cai la biet to nay da du dieu kien gui khach chua. */
      '<div style="font-size:13px;margin-top:6px">Người ký: ' +
        (hd.nguoi_ky_a ? '<b>' + h(hd.nguoi_ky_a) + '</b>' + (hd.chuc_vu_ky_a ? ' (' + h(hd.chuc_vu_ky_a) + ')' : '') : '<span style="color:#b3261e">bên A còn trống</span>') +
        ' · ' +
        (hd.nguoi_ky_b ? '<b>' + h(hd.nguoi_ky_b) + '</b>' + (hd.chuc_vu_ky_b ? ' (' + h(hd.chuc_vu_ky_b) + ')' : '') : '<span style="color:#b3261e">bên B còn trống</span>') +
      '</div>' +
      (hd.phu_luc_scan
        ? '<div style="font-size:13px;color:#0a6b3a">Phụ lục 01: đã đính kèm bản khách ký, bấm để xem <a href="' + h(hd.phu_luc_scan) + '" target="_blank">tệp</a>.</div>'
        : '<div style="font-size:13px;color:#b3261e">Phụ lục 01: chưa có bản khách ký, đang ghép bản báo giá do máy dựng.</div>') +
      '<div style="display:flex;gap:8px;margin-top:10px">' +
      '<button class="btn gh" id="hdSuaKy" style="margin:0;flex:1;padding:8px 10px;font-size:13px">✍️ Người ký</button>' +
      '<button class="btn gh" id="hdScan" style="margin:0;flex:1.4;padding:8px 10px;font-size:13px">📎 ' + (hd.phu_luc_scan ? 'Đổi bản scan' : 'Đính kèm bản scan') + '</button>' +
      (hd.phu_luc_scan ? '<button class="btn gh" id="hdScanGo" style="margin:0;flex:0.7;padding:8px 10px;font-size:13px">Gỡ</button>' : '') +
      '</div>' +
      '<div style="display:flex;gap:8px;margin-top:8px">' +
      (hd.tep_hop_dong_chot
        /* Đã có bản hai bên chốt: nút Xuất PDF tự sinh TẮT hẳn, không phải
           chỉ mờ đi. Máy chủ cũng chặn đường đó, nên có mở công cụ nhà phát
           triển gọi tay cũng không ra tờ máy tự sinh. */
        ? '<button class="btn gh" id="hdXem" style="margin:0;flex:1;padding:8px 10px;font-size:13px">👁 Xem bản máy dựng</button>' +
          '<button class="btn gh" id="hdTaiChot" style="margin:0;flex:1.3;padding:8px 10px;font-size:13px">📄 Tải bản đã chốt</button>' +
          '<button class="btn" id="hdMail" style="margin:0;flex:1.2;padding:8px 10px;font-size:13px">📧 Gửi Email</button>'
        : '<button class="btn gh" id="hdXem" style="margin:0;flex:1;padding:8px 10px;font-size:13px">👁 Xem trước</button>' +
          '<button class="btn gh" id="hdPdf" style="margin:0;flex:1;padding:8px 10px;font-size:13px">📄 Xuất PDF</button>' +
          '<button class="btn" id="hdMail" style="margin:0;flex:1.2;padding:8px 10px;font-size:13px">📧 Gửi Email</button>') +
      '</div>' +
      hdKhoiBanChot(hd) +
      '<input type="file" id="hdScanTep" accept="image/*,application/pdf" style="display:none">' +
      '<input type="file" id="hdChotTep" accept="application/pdf" style="display:none">' +
      '</div>';
  }
  html += hdKhoiLichSu(d);
  var b = frame('Chi tiết hợp đồng', html, { footer: '<button class="btn" id="hdGan">🔗 Gắn hoá đơn vào hợp đồng</button>' });
  var nXem = document.getElementById('hdXem');
  if (nXem) nXem.onclick = async function () {
    busy(true);
    try {
      var ht = await api('vagabond.hop_dong_pdf.xem_truoc', { name: name });
      busy(false);
      var hop = hopKhung('Hợp đồng ' + (hd.so_hop_dong || name),
        '<div style="background:#fff;padding:4px">' + ht + '</div>',
        '<button class="btn" id="hdXemDong" style="margin:0;flex:1">Đóng</button>');
      hop.box.querySelector('.x').onclick = hop.dong;
      hop.box.querySelector('#hdXemDong').onclick = hop.dong;
    } catch (e) { busy(false); baoTin((e && e.message) || 'Không dựng được tờ hợp đồng'); }
  };
  var nPdf = document.getElementById('hdPdf');
  if (nPdf) nPdf.onclick = async function () {
    busy(true);
    try {
      var fl = await api('vagabond.hop_dong_pdf.xuat_pdf', { name: name });
      busy(false); bcTaiVe(fl.ten_file, fl.b64, fl.kieu);
      toast('Đã tải ' + fl.ten_file + ' (đã gồm Phụ lục 01)', 4500);
    } catch (e) { busy(false); baoTin((e && e.message) || 'Xuất PDF lỗi'); }
  };
  var nMail = document.getElementById('hdMail');
  if (nMail) nMail.onclick = function () { hdGuiMail(hd); };
  hdGanNutDieuChinh(hd, d, name);
  var nSuaKy = document.getElementById('hdSuaKy');
  if (nSuaKy) nSuaKy.onclick = async function () {
    if (!await hdFormNguoiKy(hd)) return;
    go(function () { scrHdView(name); }, true);
  };
  var nScan = document.getElementById('hdScan');
  var oScan = document.getElementById('hdScanTep');
  if (nScan) nScan.onclick = function () { oScan.click(); };
  if (oScan) oScan.onchange = async function () {
    var t = oScan.files && oScan.files[0];
    if (!t) return;
    if (t.size > 12 * 1024 * 1024) {
      oScan.value = '';
      return baoTin('Tệp nặng ' + Math.round(t.size / 1048576) + ' MB, quá 12 MB nên máy không nhận. Chụp lại ở chế độ thường hoặc nén bớt rồi chọn lại giúp em.', 'Tệp quá nặng');
    }
    busy(true);
    try { await bgTaiPhuLuc(name, t); }
    catch (e) { busy(false); return baoTin((e && e.message) || 'Không tải được bản scan lên. Anh chị thử lại, hoặc chụp lại ảnh nhẹ hơn.'); }
    busy(false); toast('Đã đính kèm bản scan làm Phụ lục 01', 3500);
    go(function () { scrHdView(name); }, true);
  };
  var nScanGo = document.getElementById('hdScanGo');
  if (nScanGo) nScanGo.onclick = async function () {
    if (!await hoiCo('Gỡ bản scan phụ lục',
      'Gỡ ra thì PDF hợp đồng quay lại ghép bản báo giá do máy dựng, bản đó chưa có chữ ký hai bên. Tệp vẫn nằm trong kho tệp chứ không bị xoá.',
      'Gỡ ra', true)) return;
    busy(true);
    try { await api('vagabond.hop_dong.go_phu_luc_scan', { name: name }); }
    catch (e) { busy(false); return baoTin((e && e.message) || 'Không gỡ được'); }
    busy(false); go(function () { scrHdView(name); }, true);
  };
  document.getElementById('hdTt').onclick = function () {
    /* CỐ Ý không bày "Đang thương thảo" ở đây: vào thương thảo phải qua nút
       Điều chỉnh (đường đó bắt ghi lý do và chụp lại bản gốc), ra thì phải
       qua Chốt điều chỉnh hoặc Đóng thương thảo (hai đường đó sinh phiên
       bản và trả về đúng trạng thái cũ). Máy chủ cũng chặn, đây chỉ là để
       màn hình không mời người ta đi đường vòng. */
    if (hd.trang_thai === 'Đang thương thảo') {
      return baoTin('Hợp đồng đang thương thảo nên không đổi trạng thái tay được. ' +
        'Bấm Chốt điều chỉnh để ghi lại bản mới, hoặc Đóng thương thảo nếu khách ' +
        'thôi không sửa nữa.', 'Đang thương thảo');
    }
    sheet('Đổi trạng thái', ['Nháp', 'Đã gửi khách', 'Đang thực hiện', 'Hoàn tất', 'Đã thanh lý', 'Huỷ'].map(function (t) { return { value: t, label: t, icon: '📌' }; }), hd.trang_thai, async function (o) {
      busy(true);
      try { await api('vagabond.hop_dong.doi_trang_thai', { name: name, trang_thai: o.value }); busy(false); }
      catch (e) { busy(false); baoTin((e && e.message) || 'Lỗi'); }
      go(function () { scrHdView(name); }, true);
    });
  };
  document.getElementById('hdGan').onclick = async function () {
    busy(true);
    var cg;
    try { cg = await api('vagabond.hop_dong.hoa_don_chua_gan', hd.khach_hang ? { khach_hang: hd.khach_hang } : {}); }
    catch (e) { busy(false); return baoTin((e && e.message) || 'Lỗi'); }
    busy(false);
    if (!cg.length) return baoTin('Không có hoá đơn nào chưa gắn trong 90 ngày gần nhất' + (hd.khach_hang ? ' của khách ' + hd.khach_hang : '') + '.');
    sheet('Chọn hoá đơn để gắn', cg.map(function (x) { return { value: x.name, label: x.name + ' · ' + (x.customer_name || '') + ' · ' + money(x.grand_total) + ' đ', icon: x.docstatus === 1 ? '✅' : '📝' }; }), null, async function (o) {
      busy(true);
      try { await api('vagabond.hop_dong.gan_hoa_don', { hop_dong: name, si_name: o.value }); busy(false); toast('Đã gắn ' + o.value); }
      catch (e) { busy(false); baoTin((e && e.message) || 'Lỗi'); }
      go(function () { scrHdView(name); }, true);
    }, true);
  };
  b.addEventListener('click', function (e) {
    var r = e.target.closest('[data-si]'); if (!r) return;
    var nm = r.getAttribute('data-si');
    sheet('Hoá đơn ' + nm, [
      { value: 'xem', label: 'Xem chi tiết hoá đơn', icon: '👁️' },
      { value: 'go', label: 'Gỡ khỏi hợp đồng', icon: '✂️' }
    ], null, async function (o) {
      if (o.value === 'xem') return go(function () { scrDsView(nm, false); });
      busy(true);
      try { await api('vagabond.hop_dong.gan_hoa_don', { hop_dong: name, si_name: nm, go: 1 }); busy(false); toast('Đã gỡ ' + nm); }
      catch (e) { busy(false); baoTin((e && e.message) || 'Lỗi'); }
      go(function () { scrHdView(name); }, true);
    });
  });
}

var hdTay = null;
function hdTaoDoc() {
  if (!hdTay) return;
  var g = function (id) { var el = document.getElementById(id); return el ? el.value : ''; };
  hdTay.ten = g('hdtTen'); hdTay.so = g('hdtSo'); hdTay.giatri = g('hdtGiaTri'); hdTay.ngayky = g('hdtNgayKy'); hdTay.ngaysk = g('hdtNgaySk'); hdTay.mota = g('hdtMoTa');
}
async function scrHdTao() {
  if (!hdTay) hdTay = { ten: '', so: '', loai: 'Event - Catering', khach: '', giatri: '', ngayky: today(), ngaysk: '', mota: '' };
  var html = '<div class="card" style="padding:12px 14px;display:grid;gap:10px">' +
    '<input class="tin" id="hdtTen" placeholder="Tên hợp đồng / sự kiện (bắt buộc)" value="' + h(hdTay.ten) + '">' +
    '<input class="tin" id="hdtSo" placeholder="Số hợp đồng (vd 026-022/PYR-VAGABOND)" value="' + h(hdTay.so) + '">' +
    '<div class="hub" data-t="loai" style="padding:10px 0;border:none"><div class="ht"><div class="h2">Loại</div><div class="h1">' + h(hdTay.loai) + '</div></div><span style="color:#c3c8d4">&#8250;</span></div>' +
    '<div class="hub" data-t="khach" style="padding:10px 0;border:none"><div class="ht"><div class="h2">Khách hàng</div><div class="h1">' + h(hdTay.khach || 'Chọn khách...') + '</div></div><span style="color:#c3c8d4">&#8250;</span></div>' +
    '<input class="tin" id="hdtGiaTri" placeholder="Giá trị hợp đồng (đ)" inputmode="numeric" value="' + h(hdTay.giatri) + '">' +
    '</div>';
  html += '<div class="sec">Ngày</div><div class="card" style="padding:12px 14px;display:grid;gap:10px">' +
    '<div style="display:flex;flex-direction:row;align-items:center;gap:10px"><span style="width:90px">Ngày ký</span><input type="date" class="hin" id="hdtNgayKy" value="' + h(hdTay.ngayky) + '" style="flex:1;margin:0"></div>' +
    '<div style="display:flex;flex-direction:row;align-items:center;gap:10px"><span style="width:90px">Sự kiện</span><input type="date" class="hin" id="hdtNgaySk" value="' + h(hdTay.ngaysk) + '" style="flex:1;margin:0"></div></div>';
  html += '<div class="sec">Nội dung (đúng câu chữ hợp đồng, dùng cho hoá đơn)</div><div class="card" style="padding:12px 14px">' +
    '<textarea class="tin" id="hdtMoTa" rows="3" placeholder="Vd: Cung cấp gói tea break 120 khách theo hợp đồng số...">' + h(hdTay.mota) + '</textarea></div>';
  var b = frame('Tạo hợp đồng', html, { footer: '<button class="btn" id="hdtLuu">Lưu hợp đồng</button>' });
  b.addEventListener('click', async function (e) {
    if (e.target.closest('[data-t="loai"]')) {
      hdTaoDoc();
      return sheet('Loại hợp đồng', ['Event - Catering', 'Teabreak', 'Bánh thiết kế', 'B2B sỉ', 'Khác'].map(function (t) { return { value: t, label: t, icon: '📑' }; }), hdTay.loai, function (o) { hdTay.loai = o.value; go(scrHdTao, true); });
    }
    if (e.target.closest('[data-t="khach"]')) {
      hdTaoDoc(); busy(true);
      var kh;
      try { kh = await getList('Customer', { fields: ['name', 'customer_name'], filters: { disabled: 0 }, limit_page_length: 0, order_by: 'customer_name' }); }
      catch (er) { busy(false); return baoTin('Không tải được danh sách khách'); }
      busy(false);
      return sheet('Chọn khách hàng', kh.map(function (x) { return { value: x.name, label: x.customer_name || x.name, icon: '👤' }; }), hdTay.khach, function (o) { hdTay.khach = o.value; go(scrHdTao, true); }, true);
    }
  });
  document.getElementById('hdtLuu').onclick = async function () {
    hdTaoDoc();
    if (!hdTay.ten.trim()) return baoTin('Nhập tên hợp đồng đã nhé.');
    busy(true);
    try {
      var nm = await api('vagabond.hop_dong.tao', { ten: hdTay.ten.trim(), so_hop_dong: hdTay.so.trim(), loai: hdTay.loai, khach_hang: hdTay.khach || '', ngay_ky: hdTay.ngayky || '', ngay_su_kien: hdTay.ngaysk || '', gia_tri: parseFloat(hdTay.giatri || 0) || 0, mo_ta: hdTay.mota });
      busy(false); toast('Đã tạo hợp đồng'); hdTay = null;
      go(function () { scrHdView(nm); }, true);
    } catch (e) { busy(false); baoTin((e && e.message) || 'Lưu lỗi'); }
  };
}



/* ---------------- Màn Hoàn tiền / Trả hàng (anh Việt 16/08/2026) ----------
   Đặt trong phân hệ Bán hàng, ngay dưới Công nợ phải thu: hai màn cùng một
   mạch nghiệp vụ tiền nong với khách.

   Màn này CHỈ ĐỌC. Phiếu hoàn tiền sinh ra từ nút Hoàn tiền trên màn Chi
   tiết đơn; đẻ thêm một cửa tạo phiếu ở đây là mở một đường vòng. */
var htDsData = null, htDsLoc = 'tat_ca', htDsTim = '', htCtData = null;

/* ---------- Form gửi yêu cầu hoàn tiền, mở từ màn Chi tiết đơn ----------

Anh Việt chốt 16/08/2026: bỏ hẳn mã PIN quản lý ở bước này.

Lý do đáng ghi lại: PIN ở quầy chặn được một người bấm nhầm, nhưng không
chặn được một khoản chi sai, vì lúc gõ PIN thì tiền vẫn chưa đi đâu cả.
Cửa duyệt thật nằm ở kế toán, là người cầm tay chuyển khoản. Nên cái bắt
buộc ở đây không phải mã PIN mà là BẰNG CHỨNG: ảnh khách phản ánh, ảnh
bánh hỏng. Không có ảnh thì nút Gửi duyệt không đi qua được.

Form này chỉ GỬI YÊU CẦU. Không sinh một chứng từ nào, không động một
đồng nào. Chứng từ đợi tới lúc SePay báo tiền đã ra thật mới sinh. */
var htF = null, htFHop = null;

function hoanMoForm(don) {
  var tong = Number(don.grand_total || 0);
  htF = {
    don: don.name, tong: tong, tien: tong, muc: 100,
    ly_do: '', dien_giai: '', ten_tk: '', so_tk: '', ngan_hang: '', sdt: '',
    ten_khach: '', nguon_khach: '',
    anh: [], goi_y: null, hddt: (don.custom_hddt_so || '')
  };
  hoanVeForm();
  /* Đọc gợi ý tài khoản của chính khách này ở lần hoàn trước, tên và số
     điện thoại khách trên đơn, và đọc lại tổng đơn từ máy chủ. Chạy SAU khi
     vẽ xong form để form hiện ngay; hỏng thì để nguyên form chứ không chặn
     Sales lại. */
  api('vagabond.hoan_tien.tinh_trang', { si_name: don.name }).then(function (t) {
    if (!htF || htF.don !== don.name) return;
    if (!t || !t.duoc) {
      htFDong();
      return baoTin((t && t.vi_sao) || 'Đơn này không hoàn tiền được.', 'Không gửi được yêu cầu');
    }
    if (t.so_tien) { htF.tong = Number(t.so_tien); if (htF.muc) htF.tien = Math.round(htF.tong * htF.muc / 100); }
    htDoSanKhach(t);
    hoanVeForm();
  }).catch(function () { });
}

/* Đổ sẵn tên khách, số điện thoại và tài khoản khách dùng lần trước.

   Tách ra thành hàm riêng vì luồng chuyển lại tiền dư dùng chung y hệt:
   khách vẫn là khách đó, tài khoản nhận vẫn là tài khoản đó. */
function htDoSanKhach(t) {
  if (!htF || !t) return;
  /* Tự điền tên và số điện thoại khách từ chính đơn hàng (anh Việt
     17/08/2026). Nhân viên vừa đọc số của khách xong cách đó ba phút, bắt
     gõ lại là vừa mất thời gian vừa thêm một chỗ gõ sai. */
  if (t.khach) {
    if (t.khach.ten && !htF.ten_khach) htF.ten_khach = t.khach.ten;
    if (t.khach.sdt && !htF.sdt) htF.sdt = t.khach.sdt;
    htF.nguon_khach = t.khach.nguon || '';
    /* Tên chủ tài khoản mặc định là tên khách, vì phần lớn khách nhận về
       chính tài khoản của mình. Sales sửa lại được khi khách nhờ chuyển hộ
       người khác. */
    if (htF.ten_khach && !htF.ten_tk) htF.ten_tk = htF.ten_khach;
  }
  if (t.goi_y_tk && t.goi_y_tk.so_tk && !htF.so_tk) {
    htF.goi_y = t.goi_y_tk;
    if (t.goi_y_tk.ten_tk) htF.ten_tk = t.goi_y_tk.ten_tk;
    htF.so_tk = t.goi_y_tk.so_tk || '';
    htF.ngan_hang = t.goi_y_tk.ngan_hang || '';
  }
}

/* Luồng tiền dư cũng cần tên khách và tài khoản, đọc từ chính đường của
   luồng hoàn tiền. Hỏng thì để trống chứ không chặn Sales lại. */
function htNapGoiY(don) {
  api('vagabond.hoan_tien.tinh_trang', { si_name: don.name }).then(function (t) {
    if (!htF || htF.don !== don.name || !t) return;
    htDoSanKhach(t);
    hoanVeForm();
  }).catch(function () { });
}

/* ---------- Ô chọn ngân hàng, dùng chung cả app ----------

Anh Việt 17/08/2026: gõ tay "MB" thì máy ném lỗi "Không tìm thấy Ngân hàng:
MB", vì tên đầy đủ trong danh mục là "MB - Ngân hàng TMCP Quân đội".

Nên bỏ hẳn việc gõ tay. Danh mục 581 ngân hàng lấy từ chính tệp chuyển tiền
lô của MB Biz, nằm dưới backend, và MỌI chỗ trong app cần tên ngân hàng đều
gọi hàm này - không chỗ nào tự dựng danh sách riêng.

Danh sách tải một lần rồi giữ lại: 581 dòng mà mỗi lần mở ô lại tải là bắt
nhân viên quầy ngồi chờ mạng 4G. */
var NH_DS = null;

async function nhChon(dangChon, xong) {
  if (!NH_DS) {
    busy(true);
    try {
      var kq = await api('vagabond.ngan_hang.tim', {});
      NH_DS = (kq && kq.ds) || [];
    } catch (e) {
      busy(false);
      return baoTin((e && e.message) || 'Chưa đọc được danh mục ngân hàng', 'Lỗi');
    }
    busy(false);
  }
  if (!NH_DS.length) return baoTin('Danh mục ngân hàng đang trống. Báo em để nạp lại.', 'Chưa có dữ liệu');
  sheet('Chọn ngân hàng · ' + NH_DS.length + ' ngân hàng',
    NH_DS.map(function (x) {
      return { value: x.k, label: x.ten, phu: x.hinh_thuc || '', tim: x.tim || '' };
    }),
    dangChon || '',
    function (it) { xong(it.value); },
    true);
}

function htFDong() { if (htFHop) { htFHop.dong(); htFHop = null; } htF = null; }

function htLyDoTen(k) {
  return {
    'Khach doi y': 'Khách đổi ý', 'Banh hong': 'Bánh hỏng', 'Di ung': 'Dị ứng',
    'Giao sai mon': 'Giao sai món', 'Giao tre': 'Giao trễ', 'Khac': 'Khác',
    'Doi size nho hon': 'Đổi size nhỏ hơn',
    'Khach tu den lay, khong giao': 'Khách tự đến lấy, không giao',
    'Bo bot mon': 'Bỏ bớt món', 'Chuyen du tien': 'Chuyển dư tiền'
  }[k] || k;
}

/* ---------- Chuyển lại tiền khách nộp thừa (anh Việt 18/08/2026) ----------

   *"anh nhờ em thiết kế luôn 1 nút riêng kế bên nút Hoàn tiền đó là nút
   Chuyển lại cho khách thanh toán dư... ví dụ khách chuyển bao gồm cả tiền
   ship nhưng mà sau đó đổi ý muốn đến tiệm pickup, cần chuyển lại cho khách
   phần tiền ship bị dư ra"*.

   Dùng lại đúng form của hoàn tiền vì hai luồng giống nhau tới 90%: cùng
   một cửa duyệt của chị Dung, cùng ra tiền từ tài khoản MB công ty, cùng
   đối soát SePay. Chỉ khác bốn chỗ, và bốn chỗ đó đều rẽ theo cờ f.du:

     - Trần: tối đa là phần khách chuyển VƯỢT tổng đơn, không phải cả đơn.
     - Bộ lý do khác hẳn.
     - Ảnh không bắt buộc: bằng chứng nằm ngay trong sổ, là chênh lệch giữa
       số SePay đã nhận và tổng đơn, máy tự tính chứ không ai khai.
     - Gọi endpoint khác, và endpoint đó KHÔNG lập hoá đơn trả hàng. */
function hoanMoFormDu(don) {
  busy(true);
  api('vagabond.hoan_tien.xem_tien_du', { si_name: don.name }).then(function (t) {
    busy(false);
    if (!t || !t.duoc) {
      return baoTin((t && t.vi_sao) || 'Đơn này không có phần dư để chuyển lại.',
        'Không lập được phiếu');
    }
    htF = {
      don: don.name, du: 1, tong: Number(t.tong_don || 0), tran: Number(t.tran || 0),
      da_nhan: Number(t.da_nhan || 0), tien: Number(t.tran || 0), muc: 100,
      ly_do: '', dien_giai: '', ten_tk: '', so_tk: '', ngan_hang: '', sdt: '',
      ten_khach: '', nguon_khach: '', anh: [], goi_y: null,
      hddt: (don.custom_hddt_so || t.canh_bao_hddt || '')
    };
    hoanVeForm();
    htNapGoiY(don);
  }).catch(function (e) {
    busy(false); baoTin((e && e.message) || 'Không đọc được phần dư của đơn này.');
  });
}

/* Huỷ đơn CHƯA GHI SỔ và trả lại tiền khách đã chuyển (anh Việt 21/08/2026).

   Khách chốt bánh, chuyển tiền, hai ba tiếng sau báo huỷ. Hoá đơn mới ở dạng
   nháp nên nút Hoàn tiền không nhận: luồng đó neo vào hoá đơn đã ghi sổ.

   Cái bẫy không nằm ở kế toán mà nằm ở đồng hồ. Chuỗi cuối ngày lúc 23:00 tự
   ghi sổ những đơn nháp đã đủ điều kiện rồi phát hành hoá đơn điện tử, mà
   "đủ điều kiện" chính là chuyển khoản đã về đủ tiền. Nên bấm nút này là máy
   đánh dấu huỷ đơn TRƯỚC, lập phiếu sau. */
function hoanMoFormHuy(don) {
  busy(true);
  api('vagabond.hoan_tien.xem_huy_nhap', { si_name: don.name }).then(function (t) {
    busy(false);
    if (!t || !t.duoc) {
      return baoTin((t && t.vi_sao) || 'Đơn này chưa lập được phiếu huỷ và hoàn tiền.',
        'Không lập được phiếu');
    }
    htF = {
      don: don.name, huy: 1, tong: Number(t.tong_don || 0), tran: Number(t.tran || 0),
      da_nhan: Number(t.da_nhan || 0), tien: Number(t.tran || 0), muc: 100,
      da_huy: Number(t.da_huy || 0),
      ly_do: '', dien_giai: '', ten_tk: '', so_tk: '', ngan_hang: '', sdt: '',
      ten_khach: '', nguon_khach: '', anh: [], goi_y: null, hddt: ''
    };
    hoanVeForm();
    htNapGoiY(don);
  }).catch(function (e) {
    busy(false); baoTin((e && e.message) || 'Không đọc được tình trạng của đơn này.');
  });
}

function hoanVeForm() {
  var f = htF; if (!f) return;
  if (htFHop) { htFHop.dong(); htFHop = null; }
  var du = !!f.du;
  var huy = !!f.huy;
  /* Trần của phiếu huỷ là SỐ ĐÃ NHẬN chứ không phải tổng đơn: khách đặt cọc
     một phần rồi huỷ thì chỉ trả lại đúng phần đã nhận. */
  var tranF = (du || huy) ? Number(f.tran || 0) : Number(f.tong || 0);
  var mucs = du
    ? [[100, 'Trả hết phần dư'], [0, 'Nhập số khác']]
    : (huy
      ? [[100, 'Trả hết số đã nhận'], [0, 'Nhập số khác']]
      : [[100, 'Hoàn 100%'], [50, 'Hoàn 50%'], [0, 'Nhập số khác']]);
  var than =
    (huy
      ? '<div style="font-size:12.5px;color:#6b7280;margin-bottom:10px;line-height:1.6">' +
        'Đơn <b>' + h(f.don) + '</b> · giá trị <b>' + money(f.tong) + ' đ</b><br>' +
        'Máy thấy khách đã chuyển <b style="color:#b45309">' + money(f.da_nhan) + ' đ</b>.<br>' +
        'Yêu cầu này gửi kế toán duyệt. Tiền chỉ ra sau khi kế toán chuyển khoản thật.</div>' +
        /* Hai câu này là thứ chị Dung cần đọc trước khi duyệt, và cũng là
           thứ giữ cho không ai nghĩ tới việc ghi sổ đơn để "có cái mà đính". */
        '<div style="font-size:12px;color:#065f46;background:#ecfdf5;border:1px solid #a7f3d0;border-radius:9px;padding:9px 11px;margin-bottom:12px;line-height:1.6">' +
        'Đơn này <b>chưa từng ghi sổ</b> nên không có doanh thu để khử. Máy sẽ ' +
        '<b>không lập hoá đơn trả hàng</b> và <b>không có hoá đơn điện tử nào</b> ' +
        'phải xử lý. Khoản tiền này là tiền khách chuyển trước, mình giữ hộ và nay trả lại.</div>' +
        '<div style="font-size:12px;color:#7c2d12;background:#fff7ed;border:1px solid #fed7aa;border-radius:9px;padding:9px 11px;margin-bottom:12px;line-height:1.6">' +
        (f.da_huy
          ? 'Đơn đã mang dấu huỷ từ trước, phiếu này chỉ lo phần trả tiền.'
          : 'Bấm gửi là máy <b>đánh dấu huỷ đơn ngay</b>, trước khi lập phiếu. ' +
            'Phải làm vậy vì chuỗi cuối ngày lúc 23:00 sẽ tự ghi sổ những đơn nháp ' +
            'đã nhận đủ tiền rồi xuất hoá đơn điện tử luôn.') + '</div>'
      : du
      ? '<div style="font-size:12.5px;color:#6b7280;margin-bottom:10px;line-height:1.6">' +
        'Đơn <b>' + h(f.don) + '</b><br>' +
        'Đã nhận <b>' + money(f.da_nhan) + ' đ</b>, giá trị đơn <b>' + money(f.tong) + ' đ</b>, ' +
        'khách nộp thừa <b style="color:#b45309">' + money(f.tran) + ' đ</b>.<br>' +
        'Yêu cầu này gửi kế toán duyệt. Tiền chỉ ra sau khi kế toán chuyển khoản thật.</div>' +
        /* Câu này là điểm khác biệt quan trọng nhất giữa hai luồng, và là
           thứ chị Dung cần đọc trước khi duyệt. */
        '<div style="font-size:12px;color:#065f46;background:#ecfdf5;border:1px solid #a7f3d0;border-radius:9px;padding:9px 11px;margin-bottom:12px;line-height:1.6">' +
        'Đây <b>không phải trả hàng</b>. Khách nhận đủ hàng, giá đúng. Máy sẽ ' +
        '<b>không lập hoá đơn trả hàng</b>, doanh thu của đơn giữ nguyên ' +
        money(f.tong) + ' đ và hoá đơn điện tử không phải điều chỉnh.</div>'
      : '<div style="font-size:12.5px;color:#6b7280;margin-bottom:10px;line-height:1.6">' +
        'Đơn <b>' + h(f.don) + '</b> · tổng <b>' + money(f.tong) + ' đ</b><br>' +
        'Yêu cầu này gửi kế toán duyệt. Tiền chỉ ra sau khi kế toán chuyển khoản thật.</div>') +
    (f.hddt && !du ? '<div style="font-size:12px;color:#92400e;background:#fffbeb;border:1px solid #fde68a;border-radius:9px;padding:9px 11px;margin-bottom:12px;line-height:1.6">' +
      'Đơn này <b>đã xuất hoá đơn điện tử số ' + h(f.hddt) + '</b>. Hoàn tiền xong thì tờ đó phải xử lý riêng bên m-invoice, máy không tự làm.</div>' : '') +

    rndLbl(du ? 'Số tiền chuyển lại' : huy ? 'Số tiền trả lại khách' : 'Mức hoàn tiền') +
    '<div style="display:flex;gap:7px;margin-bottom:9px">' +
    mucs.map(function (m) {
      var on = f.muc === m[0];
      return '<button data-htm="' + m[0] + '" style="flex:1;border:1.5px solid ' + (on ? '#0f766e' : '#e5e7eb') +
        ';background:' + (on ? '#ccfbf1' : '#fff') + ';color:' + (on ? '#0f766e' : '#374151') +
        ';border-radius:9px;padding:9px 6px;font-size:12.5px;font-weight:' + (on ? '800' : '600') + '">' + h(m[1]) + '</button>';
    }).join('') + '</div>' +
    '<input class="nt" id="htFTien" inputmode="numeric" placeholder="Số tiền hoàn" value="' + h(money(f.tien)) + '"' +
    (f.muc ? ' readonly style="background:#f7f8fa;color:#374151"' : '') + '>' +
    '<div id="htFTienNhac" style="font-size:11.5px;color:#9ca3af;margin:5px 0 12px">' +
    (du ? 'Tối đa ' + money(tranF) + ' đ, đúng bằng phần khách nộp thừa.'
        : huy ? 'Tối đa ' + money(tranF) + ' đ, đúng bằng số máy thấy đã nhận.'
        : 'Tối đa ' + money(tranF) + ' đ, đúng bằng tổng đơn.') + '</div>' +

    rndLbl(du ? 'Lý do dư tiền' : huy ? 'Lý do huỷ đơn' : 'Lý do hoàn') +
    '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:9px">' +
    (du ? ['Doi size nho hon', 'Khach tu den lay, khong giao', 'Bo bot mon', 'Chuyen du tien', 'Khac']
        : huy ? ['Khach doi y', 'Khach dat nham ngay', 'Bep khong kip lam', 'Het nguyen lieu', 'Trung don', 'Khac']
        : ['Khach doi y', 'Banh hong', 'Di ung', 'Giao sai mon', 'Giao tre', 'Khac']).map(function (k) {
      var on = f.ly_do === k;
      return '<button data-htl="' + h(k) + '" style="border:1.5px solid ' + (on ? '#0f766e' : '#e5e7eb') +
        ';background:' + (on ? '#ccfbf1' : '#fff') + ';color:' + (on ? '#0f766e' : '#374151') +
        ';border-radius:999px;padding:6px 12px;font-size:12px;font-weight:' + (on ? '800' : '600') + '">' +
        h(htLyDoTen(k)) + '</button>';
    }).join('') + '</div>' +
    '<textarea class="nt" id="htFGhi" rows="2" placeholder="' +
    (f.ly_do === 'Khac' ? 'Bắt buộc: ghi rõ vì sao ' + (du ? 'dư' : huy ? 'huỷ' : 'hoàn') : 'Diễn giải thêm (không bắt buộc)') +
    '">' + h(f.dien_giai) + '</textarea>' +

    '<div style="height:14px"></div>' + rndLbl('Khách hàng') +
    (f.nguon_khach ? '<div style="font-size:11.5px;color:#0f766e;margin-bottom:6px">Đã điền sẵn từ ' + h(f.nguon_khach) + ', kiểm lại giúp em.</div>' : '') +
    '<input class="nt" id="htFKhach" placeholder="Tên khách" value="' + h(f.ten_khach) + '">' +
    '<div style="height:7px"></div>' +
    '<input class="nt" id="htFSdt" inputmode="tel" placeholder="Số điện thoại khách (không bắt buộc)" value="' + h(f.sdt) + '">' +

    '<div style="height:14px"></div>' + rndLbl('Tài khoản nhận tiền của khách') +
    (f.goi_y && f.goi_y.so_tk ? '<div style="font-size:11.5px;color:#0f766e;margin-bottom:6px">Đã điền sẵn tài khoản khách dùng lần trước, kiểm lại giúp em.</div>' : '') +
    /* Ô ngân hàng là NÚT CHỌN chứ không gõ tay: gõ "MB" thì máy không tìm
       ra "MB - Ngân hàng TMCP Quân đội", và một cái tên sai ở đây là tiền
       đi vào một ngân hàng không tồn tại. */
    '<button id="htFNh" style="width:100%;text-align:left;border:1.5px solid ' +
    (f.ngan_hang ? '#0f766e' : '#e5e7eb') + ';background:#fff;border-radius:11px;padding:13px 14px;' +
    'font-size:15px;color:' + (f.ngan_hang ? '#0f172a' : '#9ca3af') + ';font-weight:' +
    (f.ngan_hang ? '600' : '400') + ';line-height:1.4">' +
    (f.ngan_hang ? h(f.ngan_hang) : 'Chọn ngân hàng của khách') +
    '<span style="float:right;color:#9ca3af;font-weight:400">▾</span></button>' +
    '<div style="height:7px"></div>' +
    '<input class="nt" id="htFStk" inputmode="numeric" placeholder="Số tài khoản" value="' + h(f.so_tk) + '">' +
    '<div style="height:7px"></div>' +
    '<input class="nt" id="htFTen" placeholder="Tên chủ tài khoản" value="' + h(f.ten_tk) + '">' +

    '<div style="height:14px"></div>' + rndLbl(du ? 'Ảnh kèm theo · không bắt buộc' : 'Bằng chứng · bắt buộc') +
    '<div style="font-size:11.5px;color:#9ca3af;margin-bottom:7px;line-height:1.6">' +
    (du
      /* Với tiền dư thì bằng chứng nằm ngay trong sổ: chênh lệch giữa số
         SePay đã nhận và tổng đơn, máy tự tính chứ không ai khai. Bắt ảnh ở
         đây là bắt một thứ không nói thêm điều gì. */
      ? 'Chênh lệch giữa số đã nhận và tổng đơn là căn cứ đủ rồi, máy tự tính. Có ảnh tin nhắn khách xin đổi thì đính kèm cho rõ, không có cũng gửi được.'
      : huy
      /* Với phiếu huỷ thì ngược lại: việc khách xin huỷ KHÔNG nằm trong sổ
         sách chỗ nào cả. Sổ chỉ thấy một đơn nháp và một khoản tiền vào.
         Ảnh tin nhắn là căn cứ duy nhất, và cái mốc giờ trên đó là thứ sau
         này quyết được có giữ lại phí nguyên liệu hay không. */
      ? 'Ảnh tin nhắn khách xin huỷ, nhìn rõ mốc giờ. Việc khách xin huỷ không nằm trong sổ sách chỗ nào, đây là căn cứ duy nhất kế toán có để duyệt.'
      : 'Ảnh khách phản ánh, hoặc ảnh bánh hỏng. Kế toán ngồi xa quầy, đây là căn cứ duy nhất để duyệt.') + '</div>' +
    '<div class="att" id="htFAnh">' +
    f.anh.map(function (a, i) {
      return '<div class="ph" style="background-image:url(' + a.url + ');background-size:cover;background-position:center;position:relative">' +
        '<span data-htrm="' + i + '" style="position:absolute;top:2px;right:4px;background:rgba(0,0,0,.55);color:#fff;border-radius:999px;width:20px;height:20px;line-height:20px;text-align:center;font-size:13px">&times;</span></div>';
    }).join('') +
    '<div class="ph" id="htFCam"><div style="font-size:22px">📷</div>Thêm ảnh</div></div>' +
    '<input type="file" accept="image/*" id="htFFile" style="display:none">';

  htFHop = hopKhung(
    du ? 'Chuyển lại tiền khách nộp thừa'
      : huy ? 'Huỷ đơn và hoàn tiền cho khách'
      : 'Yêu cầu hoàn tiền', than,
    '<button class="btn gh" id="htFThoi" style="margin:0;flex:0 0 34%">Thôi</button>' +
    '<button class="btn" id="htFGui" style="margin:0;flex:1">Gửi duyệt</button>');
  var box = htFHop.box;
  box.querySelector('.x').onclick = htFDong;
  box.querySelector('#htFThoi').onclick = htFDong;

  box.querySelectorAll('[data-htm]').forEach(function (n) {
    n.onclick = function () {
      htFDoc(box);
      f.muc = Number(n.getAttribute('data-htm'));
      /* Voi tien du thi 100% nghia la tra het PHAN DU, khong phai ca don. */
      if (f.muc) f.tien = Math.round(tranF * f.muc / 100);
      hoanVeForm();
    };
  });
  box.querySelectorAll('[data-htl]').forEach(function (n) {
    n.onclick = function () { htFDoc(box); f.ly_do = n.getAttribute('data-htl'); hoanVeForm(); };
  });
  box.querySelectorAll('[data-htrm]').forEach(function (n) {
    n.onclick = function () { htFDoc(box); f.anh.splice(+n.getAttribute('data-htrm'), 1); hoanVeForm(); };
  });
  box.querySelector('#htFNh').onclick = function () {
    htFDoc(box);
    nhChon(f.ngan_hang, function (v) { f.ngan_hang = v; hoanVeForm(); });
  };
  var fi = box.querySelector('#htFFile');
  box.querySelector('#htFCam').onclick = function () { fi.click(); };
  fi.onchange = function () { if (fi.files[0]) { htFDoc(box); htFThemAnh(fi.files[0]); } };

  /* Ô tiền: chỉ gõ được khi đang ở mức "Nhập số khác", và chặn ngay trên
     màn nếu vượt tổng đơn. Máy chủ vẫn tính lại (QT-19), đây chỉ để Sales
     biết liền chứ không đợi tới lúc bấm Gửi mới báo. */
  var oT = box.querySelector('#htFTien');
  if (oT && !f.muc) oT.oninput = function () {
    var v = Number(String(oT.value).replace(/[^0-9]/g, '')) || 0;
    var nhac = box.querySelector('#htFTienNhac');
    var chu = du ? 'phần khách nộp thừa' : huy ? 'số máy thấy đã nhận' : 'tổng đơn';
    if (v > tranF) { nhac.textContent = 'Vượt ' + chu + ' ' + money(tranF) + ' đ. Nhập lại số nhỏ hơn.'; nhac.style.color = '#b3261e'; }
    else { nhac.textContent = 'Tối đa ' + money(tranF) + ' đ, đúng bằng ' + chu + '.'; nhac.style.color = '#9ca3af'; }
  };

  box.querySelector('#htFGui').onclick = function () { htFDoc(box); htFGui(); };
}

/* Đọc lại mọi ô TRƯỚC mỗi lần vẽ lại form. Không có bước này thì bấm đổi
   mức hoàn là mất sạch tài khoản vừa gõ - đúng loại lỗi người dùng không
   bao giờ báo lại lần hai, chỉ lặng lẽ bỏ dùng. */
function htFDoc(box) {
  var f = htF; if (!f || !box) return;
  var g = function (id) { var n = box.querySelector(id); return n ? n.value : ''; };
  if (!f.muc) f.tien = Number(String(g('#htFTien')).replace(/[^0-9]/g, '')) || 0;
  f.dien_giai = g('#htFGhi');
  /* Ngân hàng KHÔNG đọc ở đây: nó là nút chọn, giá trị đã nằm sẵn trong
     f.ngan_hang. Đọc lại từ nút là đọc phải chữ hiển thị. */
  f.so_tk = g('#htFStk'); f.ten_tk = g('#htFTen'); f.sdt = g('#htFSdt');
  f.ten_khach = g('#htFKhach');
}

function htFThemAnh(file) {
  var fr = new FileReader();
  fr.onload = function () {
    var img = new Image();
    img.onload = function () {
      /* Nén lại trước khi gửi: ảnh điện thoại 4 MB gửi qua mạng quán là
         Sales ngồi chờ, còn ảnh 1280 px thì kế toán vẫn nhìn rõ vết nứt. */
      var mx = 1280, w = img.width, ht = img.height;
      if (w > mx || ht > mx) { var s = mx / Math.max(w, ht); w = Math.round(w * s); ht = Math.round(ht * s); }
      var cv = document.createElement('canvas'); cv.width = w; cv.height = ht;
      cv.getContext('2d').drawImage(img, 0, 0, w, ht);
      var url = cv.toDataURL('image/jpeg', 0.72);
      htF.anh.push({ url: url, b64: url.split(',')[1], ten: 'bang-chung-' + (htF.anh.length + 1) + '.jpg' });
      hoanVeForm();
    };
    img.src = fr.result;
  };
  fr.readAsDataURL(file);
}

async function htFGui() {
  var f = htF; if (!f) return;
  var du = !!f.du;
  var huy = !!f.huy;
  var tranF = (du || huy) ? Number(f.tran || 0) : Number(f.tong || 0);
  if (!f.ly_do) return toast(du ? 'Chọn lý do dư tiền giúp em.'
    : huy ? 'Chọn lý do huỷ đơn giúp em.' : 'Chọn lý do hoàn giúp em.', 3500);
  if (f.ly_do === 'Khac' && !(f.dien_giai || '').trim())
    return toast('Lý do "Khác" thì phải ghi rõ vì sao ' + (du ? 'dư' : huy ? 'huỷ' : 'hoàn') + '.', 4000);
  if (!f.tien || f.tien <= 0) return toast('Nhập số tiền lớn hơn 0.', 3500);
  if (f.tien > tranF)
    return toast(du
      ? 'Số tiền chuyển lại không được lớn hơn phần khách nộp thừa ' + money(tranF) + ' đ.'
      : huy
      ? 'Số tiền trả lại không được lớn hơn số máy thấy đã nhận ' + money(tranF) + ' đ.'
      : 'Số tiền hoàn không được lớn hơn tổng đơn ' + money(tranF) + ' đ.', 4500);
  if (!(f.ngan_hang || '').trim()) return toast('Bấm ô ngân hàng để chọn ngân hàng của khách.', 4000);
  if (!(f.so_tk || '').trim() || !(f.ten_tk || '').trim())
    return toast('Điền đủ số tài khoản và tên chủ tài khoản của khách.', 4500);
  /* Anh bat buoc voi TRA HANG thoi. Voi tien du thi bang chung la chenh
     lech giua so da nhan va tong don, may tu tinh. */
  if (!du && !f.anh.length) return toast('Phải đính kèm ít nhất một ảnh làm căn cứ.', 4000);

  var ok = await confirmSheet(
    du ? 'Chuyển lại ' + money(f.tien) + ' đ cho khách?'
      : huy ? 'Huỷ đơn và trả lại ' + money(f.tien) + ' đ?'
      : 'Gửi yêu cầu hoàn ' + money(f.tien) + ' đ?',
    du
      ? 'Kế toán nhận thư báo ngay. Máy KHÔNG lập hoá đơn trả hàng, doanh thu của đơn ' +
        'giữ nguyên ' + money(f.tong) + ' đ. Tiền chỉ ra khi kế toán chuyển khoản thật.'
      : huy
      ? 'Máy đánh dấu huỷ đơn ngay, rồi gửi phiếu cho kế toán. Đơn chưa từng ghi sổ nên ' +
        'KHÔNG có doanh thu, KHÔNG hoá đơn trả hàng, KHÔNG hoá đơn điện tử. ' +
        'Tiền chỉ ra khi kế toán chuyển khoản thật.'
      : 'Kế toán nhận thư báo ngay. Tiền chỉ ra khi kế toán chuyển khoản thật, và máy ' +
        'chỉ sinh chứng từ sau khi ngân hàng báo tiền đã đi.',
    'Gửi duyệt');
  if (!ok) return;

  /* Đặt cờ huỷ là thao tác đã có sẵn một chốt kiểm soát là mã OTP quản lý.
     Cửa mới dùng lại đúng chốt đó chứ không tự mở một đường vòng. */
  var otpHuy = null;
  if (huy && !f.da_huy) {
    otpHuy = await posXinPhep('Huỷ đơn ' + f.don + ' và hoàn ' + money(f.tien) + ' đ');
    if (otpHuy === null) return;
  }

  busy(true);
  try {
    var goiF = {
      si_name: f.don, ly_do: f.ly_do, dien_giai: f.dien_giai, so_tien: f.tien,
      ten_tk: f.ten_tk, so_tk: f.so_tk, ngan_hang: f.ngan_hang, sdt_khach: f.sdt,
      tep: JSON.stringify(f.anh.map(function (a) { return { ten: a.ten, noi_dung: a.b64 }; }))
    };
    if (huy) goiF.otp = otpHuy || '';
    var kq = await api(
      du ? 'vagabond.hoan_tien.tao_tien_du'
        : huy ? 'vagabond.hoan_tien.tao_huy_nhap'
        : 'vagabond.hoan_tien.tao',
      goiF);
    busy(false);
    htFDong();
    baoTin(
      'Đã gửi yêu cầu ' + kq.ho_so + ', số tiền ' + money(kq.so_tien) + ' đ.\n\n' +
      (du ? 'Đây là phiếu TIỀN NỘP THỪA: máy không lập hoá đơn trả hàng, doanh thu của đơn giữ nguyên.\n\n' : '') +
      (huy ? 'Đã đánh dấu huỷ đơn nên chuỗi ghi sổ cuối ngày sẽ không đụng tới nó nữa.\n' +
             'Đơn chưa từng ghi sổ nên không có doanh thu, không hoá đơn trả hàng, không hoá đơn điện tử.\n\n' : '') +
      (kq.da_bao_ke_toan ? 'Đã báo kế toán qua email.' : 'Chưa gửi được email báo kế toán, nhưng phiếu đã nằm trên màn Hoàn tiền.') +
      '\n\nNội dung chuyển khoản kế toán sẽ dùng:\n' + kq.noi_dung_ck +
      (kq.mot_phan ? '\n\nHoàn một phần nên khách giữ lại hàng, máy không lập phiếu chuyển Kho Hàng Hủy.' : '') +
      (kq.canh_bao_hddt ? '\n\nĐơn đã xuất hoá đơn điện tử số ' + kq.canh_bao_hddt + ', phải xử lý riêng bên m-invoice.' : ''),
      'Đã gửi duyệt');
    go(scrHoanTien);
  } catch (e) { busy(false); baoTin((e && e.message) || 'Gửi yêu cầu lỗi', 'Không gửi được'); }
}

/* ---------- Gửi hợp đồng qua email ----------

Đi đúng nếp gửi báo giá: máy chủ tính lại danh sách người nhận bằng ĐÚNG
phép lọc của hàm gửi (QT-19), bày ra hết, rồi mới cho bấm. Gửi nhầm một tờ
hợp đồng sang địa chỉ khác là loại lỗi không rút lại được, và ở đây còn
nặng hơn báo giá vì tờ này có mã số thuế và người đại diện hai bên. */
/* Sua bon o cua khoi chu ky tren mot hop dong da tao.

   Anh Viet 18/08/2026: *"Khoi chu ky cuoi hop dong tuyet doi khong duoc ghi
   Ms./Mr. va khong duoc lay mac dinh ten cua ban Sales"*. Man tao hop dong
   da hoi bon o nay roi, day la duong sua lai khi go nham.

   Tra ve true neu co luu, false neu bam Thoi. */
function hdFormNguoiKy(hd) {
  return new Promise(function (xong) {
    function o(id, gtri, goiY) {
      return '<input class="tin" id="' + id + '" value="' + h(gtri || '') + '" placeholder="' + h(goiY || '') +
        '" style="height:auto;font-size:15px;font-weight:500;text-align:left;padding:10px 12px;margin:0">';
    }
    var than =
      rndLbl('Người ký Bên A (khách hàng)') +
      o('hkKyA', hd.nguoi_ky_a, 'Họ và tên người đặt bút ký') +
      '<div style="height:7px"></div>' + o('hkCvA', hd.chuc_vu_ky_a, 'Chức vụ, vd Giám đốc') +
      '<div style="height:7px"></div>' + o('hkDtA', hd.dt_ky_a, 'SĐT người ký') +
      '<div style="height:7px"></div>' + o('hkEmA', hd.email_ky_a, 'Email người ký') +
      '<div style="height:12px"></div>' +
      rndLbl('Người ký Bên B (Vagabond)') +
      o('hkKyB', hd.nguoi_ky_b, 'Họ và tên người đặt bút ký') +
      '<div style="height:7px"></div>' + o('hkCvB', hd.chuc_vu_ky_b, 'Chức vụ, vd Giám đốc') +
      '<div style="height:7px"></div>' + o('hkDtB', hd.dt_ky_b, 'SĐT người ký') +
      '<div style="height:7px"></div>' + o('hkEmB', hd.email_ky_b, 'Email người ký') +
      /* Anh Viet 18/08/2026: *"hien em dang lay thong tin email va so dien
         thoai cua Loan Anh gan cho anh la sao"*. Nen sdt va email phai hoi
         rieng cho NGUOI KY, khong lay o lien he cua to bao gia. */
      '<div style="font-size:12.5px;color:#8a8f9c;line-height:1.35;margin-top:8px">Các ô này in thẳng xuống khối thông tin hai bên và khối chữ ký cuối hợp đồng. Ghi đúng họ tên, không ghi Ms./Mr., và thường là Giám đốc chứ không phải bạn làm báo giá. SĐT và email phải là của chính người ký.</div>' +
      '<div style="font-size:12.5px;color:#8a8f9c;line-height:1.35;margin-top:6px">Bên B khai một lần trong Cài đặt câu chữ khung tờ báo giá thì mọi hợp đồng sau tự điền sẵn.</div>';
    var k = hopKhung('Người ký hợp đồng', than,
      '<button class="btn gh" data-hkx style="flex:1;margin:0">Thôi</button>' +
      '<button class="btn" data-hkluu style="flex:2;margin:0">Lưu</button>');
    var tra = function (v) { k.dong(); xong(v); };
    k.ov.onclick = function (e) { if (e.target === k.ov) tra(false); };
    k.box.onclick = async function (e) {
      if (e.target.closest('.x') || e.target.closest('[data-hkx]')) return tra(false);
      if (!e.target.closest('[data-hkluu]')) return;
      var v = {
        name: hd.name,
        nguoi_ky_a: String(k.box.querySelector('#hkKyA').value || '').trim(),
        chuc_vu_ky_a: String(k.box.querySelector('#hkCvA').value || '').trim(),
        dt_ky_a: String(k.box.querySelector('#hkDtA').value || '').trim(),
        email_ky_a: String(k.box.querySelector('#hkEmA').value || '').trim(),
        nguoi_ky_b: String(k.box.querySelector('#hkKyB').value || '').trim(),
        chuc_vu_ky_b: String(k.box.querySelector('#hkCvB').value || '').trim(),
        dt_ky_b: String(k.box.querySelector('#hkDtB').value || '').trim(),
        email_ky_b: String(k.box.querySelector('#hkEmB').value || '').trim()
      };
      busy(true);
      try { await api('vagabond.hop_dong.sua_nguoi_ky', v); }
      catch (er) { busy(false); return baoTin((er && er.message) || 'Không lưu được người ký'); }
      busy(false); toast('Đã lưu người ký', 3000);
      tra(true);
    };
  });
}

async function hdGuiMail(hd) {
  var em = await hoiChu('Gửi hợp đồng qua email',
    'Tệp PDF hợp đồng <b>' + h(hd.so_hop_dong || hd.name) + '</b> sẽ được đính kèm, đã gồm báo giá ' +
    h(hd.bao_gia || '') + ' làm Phụ lục 01. <b>Nhiều email thì ngăn nhau bằng dấu phẩy.</b>',
    hd.email || '', { goi_y: 'ten@congty.com, ketoan@congty.com', bat_buoc: true });
  if (em === null) return;

  busy(true);
  var ng;
  try { ng = await api('vagabond.hop_dong_pdf.xem_nguoi_nhan', { name: hd.name, email: em }); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Không kiểm được danh sách người nhận'); }
  busy(false);
  if (ng.sai && ng.sai.length) return baoTin('Địa chỉ này chưa đúng dạng email: ' + ng.sai.join(', ') + '. Anh chị sửa lại giúp em.');
  if (!ng.nhan.length) return baoTin('Chưa có địa chỉ nào hợp lệ để gửi.');

  var mo = 'Hợp đồng ' + (hd.so_hop_dong || hd.name) + ' · ' + money(hd.gia_tri) + ' đ\n\n' +
    'Gửi tới:\n' + ng.nhan.map(function (x) { return '  • ' + x; }).join('\n');
  if (ng.cc && ng.cc.length) mo += '\n\nCC nội bộ:\n' + ng.cc.map(function (x) { return '  • ' + x; }).join('\n');
  mo += '\n\nNgười gửi: ' + (ng.tu || 'hộp thư mặc định của hệ thống');
  if (!ng.tu_co_that && ng.tu_khai) mo += '\n(Hộp thư ' + ng.tu_khai + ' chưa được bật gửi đi)';
  if (!await hoiCo('Xác nhận gửi hợp đồng', mo, 'Gửi thư')) return;

  /* Chip cau co san thay vi bat sales go tay (anh Viet 18/08/2026): *"em
     tao ra khoang 5 chip nhung loi nhan than thu thuong hay su dung nhat de
     sales chi viec lua chon chu khong phai go"*.

     Dung lai dung hop thoai cua to bao gia, chi doi bo cau. Doc cau tu Cai
     dat nen anh sua duoc ma khong can deploy; may chu hong thi lui ve bo
     cai san trong app chu khong bay ra hop thoai rong. */
  var cauHd = [];
  try {
    var cdHd = await api('vagabond.bao_gia.cd_doc', {});
    cauHd = (cdHd && cdHd.loi_nhan_hd_mau) || [];
  } catch (e) { cauHd = []; }
  if (!cauHd.length) cauHd = [
    'Anh chị xem giúp em phần Điều 2 rồi phản hồi trước thứ Sáu ạ.',
    'Anh chị ký đóng dấu rồi gửi lại bên em một bản scan giúp em ạ.',
    'Bên em đã đính kèm báo giá đã chốt làm Phụ lục 01 của Hợp đồng ạ.',
    'Sau khi nhận cọc đợt 1 bên em sẽ lên lịch sản xuất ngay ạ.',
    'Anh chị cần điều chỉnh chỗ nào thì báo em, bên em gửi lại bản mới ạ.'
  ];
  var loi = await bgHoiLoiNhan(cauHd, hd.ngay_su_kien || hd.ngay_ky);
  if (loi === null) return;

  busy(true);
  try {
    var r = await api('vagabond.hop_dong_pdf.gui_email', { name: hd.name, email: em, loi_nhan: loi || '' });
    busy(false);
    toast('Đã gửi ' + r.ten_file + ' tới ' + (r.nhan || []).length + ' địa chỉ' +
      ((r.cc || []).length ? ' và CC ' + r.cc.length + ' nội bộ' : ''), 5000);
    go(function () { scrHdView(hd.name); }, true);
  } catch (e) { busy(false); baoTin((e && e.message) || 'Gửi thư lỗi'); }
}


async function scrHoanTien() {
  frame('Phiếu hoàn tiền (Cash-back)', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc phiếu hoàn tiền...</div></div>');
  try { htDsData = await api('vagabond.hoan_tien.ds', { trang_thai: htDsLoc, tim: htDsTim }); }
  catch (e) {
    frame('Phiếu hoàn tiền (Cash-back)', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  htDsVe();
}

function htDsTen(t) {
  return { 'Cho chi': 'Chờ chi', 'Da chi': 'Đã chi', 'Da doi soat': 'Đã đối soát',
           'Hoan thanh': 'Hoàn thành', 'Da huy': 'Đã huỷ / Từ chối' }[t] || t;
}

/* ---------- Danh sách phiếu hoàn tiền ----------

Anh Việt 18/08/2026 giao ba việc cho màn này: chuyển hẳn sang khối Kế toán,
làm mỗi dòng bấm được để xem chi tiết, và thêm chip trạng thái với thanh
tìm kiếm.

Ô tìm và chip đều gửi thẳng lên MÁY CHỦ chứ không lọc mảng đã tải về. Hai
lý do, và lý do thứ hai mới là lý do thật: một, danh sách có thể dài hàng
trăm dòng; hai, nếu lọc ở máy khách thì con số trên chip chỉ đếm được phần
đã kéo về, và kế toán sẽ tin vào một con số sai.

Ô tìm gõ xong phải bấm Enter hoặc nút kính lúp. Cố tình không tự tìm theo
từng phím: mỗi phím là một lượt gọi máy chủ, mà đây là màn kế toán ngồi
đọc chứ không phải ô tìm tức thời. */
function htDsVe() {
  var d = htDsData, ds = d.ds || [], dem = d.dem || {};
  var loc = [['tat_ca', 'Tất cả'], ['Cho chi', 'Chờ chi'], ['Da chi', 'Đã chi'],
             ['Da doi soat', 'Đã đối soát'], ['Hoan thanh', 'Hoàn thành'],
             ['Da huy', 'Đã huỷ / Từ chối']];
  var html = '<div style="display:flex;gap:7px;margin-bottom:9px">' +
    '<input id="htTim" value="' + h(htDsTim) + '" placeholder="Tìm tên khách, mã phiếu, mã hoá đơn" ' +
    'style="flex:1;border:1.5px solid #e5e7eb;border-radius:9px;padding:9px 12px;font-size:13px">' +
    '<button id="htTimNut" style="flex:none;border:1.5px solid #0f766e;background:#ccfbf1;color:#0f766e;' +
    'border-radius:9px;padding:0 14px;font-size:15px;font-weight:800">🔍</button>' +
    (htDsTim ? '<button id="htTimXoa" style="flex:none;border:1.5px solid #e5e7eb;background:#fff;color:#6b7280;' +
      'border-radius:9px;padding:0 13px;font-size:14px">✕</button>' : '') +
    '</div>';

  html += '<div style="display:flex;gap:7px;overflow-x:auto;padding:2px 0 10px">' +
    loc.map(function (x) {
      var on = htDsLoc === x[0];
      return '<button class="htf" data-htf="' + x[0] + '" style="flex:none;border:1.5px solid ' +
        (on ? '#0f766e' : '#e5e7eb') + ';background:' + (on ? '#ccfbf1' : '#fff') + ';color:' +
        (on ? '#0f766e' : '#374151') + ';border-radius:999px;padding:6px 13px;font-size:12.5px;font-weight:' +
        (on ? '800' : '600') + ';white-space:nowrap">' + h(x[1]) +
        (dem[x[0]] !== undefined ? ' · ' + money(dem[x[0]]) : '') + '</button>';
    }).join('') + '</div>';

  if (d.kho_huy) {
    html += '<div style="font-size:11.5px;color:#98a2b3;padding:0 2px 10px;line-height:1.6">' +
      'Hàng khách trả về <b>' + h(d.kho_huy) + '</b> chờ tiêu huỷ, không quay lại kho bán. ' +
      'Tiền chi từ <b>' + h(d.tk_chi || '(chưa khai)') + '</b>.</div>';
  }

  if (!ds.length) {
    html += '<div class="emp"><div class="e1">🧾</div><div>' +
      (htDsTim ? 'Không có phiếu nào khớp "' + h(htDsTim) + '".' : 'Chưa có phiếu hoàn tiền nào.') + '</div>' +
      '<div style="font-size:12px;color:#9ca3af;margin-top:6px">' +
      (htDsTim ? 'Anh chị xoá ô tìm hoặc đổi chip trạng thái để xem lại.'
               : 'Phiếu được lập từ nút Hoàn tiền trên màn Chi tiết đơn.') + '</div></div>';
  } else {
    html += '<div class="card">' + ds.map(function (x) {
      var mau = x.trang_thai === 'Hoan thanh' ? '#065f46'
        : (x.trang_thai === 'Da doi soat' ? '#0a8a4a'
          : (x.trang_thai === 'Da chi' ? '#b45309'
            : (x.trang_thai === 'Da huy' ? '#6b7280' : '#b3261e')));
      /* Ca dong la mot vung bam duoc (htmo), tru cac nut ben trong. Truoc
         18/08/2026 dong nay khong bam duoc o dau ca, nen ke toan khong co
         duong nao xem anh to hay so tai khoan khach. */
      return '<div class="htmo" data-ht="' + h(x.name) + '" style="padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
        '<div style="display:flex;align-items:center;gap:9px">' +
        '<div style="flex:1;min-width:0"><b style="font-size:14px">' + h(x.ten_khach || '(khách lẻ)') + '</b>' +
        /* Ke toan phai nhin ra NGAY day la phieu tra hang hay phieu tien
           nop thua, vi hai loai sinh chung tu khac han nhau: mot ben khu
           doanh thu, mot ben khong dung toi doanh thu. */
        (x.loai_hoan === 'Tien nop thua'
          ? '<span style="display:inline-block;background:#ecfdf5;color:#065f46;border:1px solid #a7f3d0;border-radius:999px;padding:1px 8px;font-size:10.5px;font-weight:800;margin-left:6px">TIỀN DƯ</span>'
          : '') +
        '<div style="font-size:11.5px;color:#98a2b3">' + h(x.name) + ' · ' + h(x.hoa_don) + '</div></div>' +
        '<div style="text-align:right"><b style="font-size:15px">' + money(x.so_tien) + ' đ</b>' +
        '<div style="font-size:11px;font-weight:700;color:' + mau + '">' + h(htDsTen(x.trang_thai)) + '</div></div>' +
        '<div style="flex:none;color:#c9cfda;font-size:17px">›</div></div>' +
        '<div style="font-size:11.5px;color:#6b7280;margin-top:5px">' + h(htLyDoTen(x.ly_do || '')) +
        (x.phieu_chi
          ? ' · phiếu chi ' + h(x.phieu_chi) + (x.phieu_chi_da_ghi ? ' (đã ghi sổ)' : ' <b style="color:#b3261e">(chưa ghi sổ)</b>') +
            /* Chi Dung can nhin luot ca danh sach la biet phieu nao dang
               cho minh dinh giay to, khong phai mo tung phieu ra xem. */
            (x.co_unc ? ' · <b style="color:#065f46">có UNC</b>' : ' · <b style="color:#b45309">chưa có UNC</b>')
          : (x.trang_thai === 'Da huy' ? ' · <b style="color:#6b7280">đã từ chối, không chi</b>'
            : (x.da_doi_soat ? ' · <b style="color:#b3261e">chưa có phiếu chi</b>' : ' · chứng từ sinh sau khi tiền ra'))) +
        '</div>' +
        /* Tien da ra, da khop sao ke, nhung chung tu chua sinh duoc. Truoc
           19/08/2026 chuyen nay im lang tuyet doi: phieu nam mai o "Cho
           chi" trong khi tien da di, va nhip doi soat cu 35 phut moi gio
           lai hong lai lang. Bay len dong dau cho ke toan nhin thay. */
        (x.loi_sinh_ct
          ? '<div style="font-size:11.5px;color:#b3261e;background:#fef2f2;border:1px solid #fecaca;' +
            'border-radius:8px;padding:7px 9px;margin-top:7px;line-height:1.55">⚠️ ' + h(x.loi_sinh_ct) + '</div>'
          : '') +
        /* Anh bang chung: ke toan ngoi xa quay, day la can cu duy nhat de
           quyet. Bay anh nho ra ngay tren dong chu khong bat bam vao xem -
           mot cai bam nua la mot co hoi de duyet cho xong. */
        ((x.anh || []).length
          ? '<div style="display:flex;gap:6px;margin-top:7px;flex-wrap:wrap">' +
            x.anh.map(function (a) {
              return '<div class="htanh" data-url="' + h(a.url) + '" style="width:54px;height:54px;border-radius:8px;' +
                'background-image:url(' + a.url + ');background-size:cover;background-position:center;border:1px solid #e3e6ec"></div>';
            }).join('') + '</div>'
          : '<div style="font-size:11px;color:#b3261e;margin-top:6px">Chưa có ảnh bằng chứng</div>') +
        (x.trang_thai === 'Da huy' ? '' :
        '<div style="display:flex;gap:7px;margin-top:8px">' +
        '<button class="htmb" data-ht="' + h(x.name) + '" style="flex:2;border:1.5px solid #0f766e;background:#ccfbf1;' +
        'color:#0f766e;border-radius:8px;padding:7px 10px;font-size:12px;font-weight:800">🏦 Xuất thông tin chuyển khoản MB Biz</button>' +
        '</div>') + '</div>';
    }).join('') + '</div>';
  }

  var b = frame('Phiếu hoàn tiền (Cash-back)', html, {
    footer: '<div style="display:flex;gap:8px">' +
      '<button class="btn gh" id="htDsSoat" style="margin:0;flex:2">🔄 Đối soát lệnh chi</button>' +
      '<button class="btn gh" id="htDsXls" style="margin:0;flex:1">📊 Xuất Excel</button></div>'
  });
  var oTim = document.getElementById('htTim');
  var chay = function () {
    htDsTim = (oTim && oTim.value || '').trim();
    go(scrHoanTien, true);
  };
  if (oTim) oTim.onkeydown = function (e) { if (e.key === 'Enter') chay(); };
  var nTim = document.getElementById('htTimNut');
  if (nTim) nTim.onclick = chay;
  var nXoa = document.getElementById('htTimXoa');
  if (nXoa) nXoa.onclick = function () { htDsTim = ''; go(scrHoanTien, true); };

  var nXls = document.getElementById('htDsXls');
  /* Xuat DUNG cai dang hien tren man: cung chip trang thai, cung o tim.
     Tep khac man hinh la mot ngay nao do hai ben cai nhau ve mot con so. */
  if (nXls) nXls.onclick = async function () {
    busy(true);
    try {
      var fl = await api('vagabond.hoan_tien.xuat_excel', {
        trang_thai: htDsLoc === 'tat_ca' ? '' : htDsLoc, tim: htDsTim, so_dong: 500
      });
      busy(false);
      bcTaiVe(fl.ten_file, fl.b64, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
      toast('Đã tải ' + fl.ten_file + ' · ' + fl.so_dong + ' phiếu', 4000);
    } catch (e) { busy(false); toast((e && e.message) || 'Không xuất được Excel', 5000); }
  };

  b.querySelectorAll('.htf').forEach(function (n) {
    n.onclick = function () { htDsLoc = n.getAttribute('data-htf'); go(scrHoanTien, true); };
  });
  b.querySelectorAll('.htanh').forEach(function (n) {
    n.onclick = function (e) { e.stopPropagation(); rndXemAnh(n.getAttribute('data-url')); };
  });
  b.querySelectorAll('.htmb').forEach(function (n) {
    n.onclick = function (e) { e.stopPropagation(); htMbBiz(n.getAttribute('data-ht')); };
  });
  b.querySelectorAll('.htmo').forEach(function (n) {
    n.onclick = function () { htChiTiet(n.getAttribute('data-ht')); };
  });
  var s = document.getElementById('htDsSoat');
  if (s) s.onclick = async function () {
    busy(true);
    try {
      var kq = await api('vagabond.hoan_tien.doi_soat', {});
      busy(false);
      /* Tách hai loại "cần xem lại" ra: số tiền lệch là kế toán chuyển
         thiếu hoặc thừa, còn trùng giao dịch là hai phiếu cùng trỏ vào một
         lần tiền ra. Gộp làm một dòng thì người đọc không biết phải làm gì
         tiếp, mà hai việc đó xử lý khác hẳn nhau. */
      var xx = kq.xem_xet || [];
      var trung = xx.filter(function (x) { return x.trung_voi; });
      var lech = xx.filter(function (x) { return !x.trung_voi; });
      baoTin(kq.ghi_chu ? kq.ghi_chu :
        ('Đã khớp ' + money(kq.da_khop || 0) + ' phiếu trên ' + money(kq.so_phieu_quet || 0) + ' phiếu chờ.' +
         (lech.length ? '\n\nCó ' + lech.length + ' phiếu nội dung khớp nhưng SỐ TIỀN LỆCH, cần xem lại.' : '') +
         (trung.length ? '\n\nCó ' + trung.length + ' phiếu trỏ vào giao dịch đã gắn cho phiếu khác ' +
          '(' + trung.map(function (x) { return x.ho_so + ' trùng ' + x.trung_voi; }).join(', ') + '). ' +
          'Một lần tiền ra chỉ khớp cho một phiếu. Nếu đây thật sự là hai lần hoàn khác nhau ' +
          'thì sao kê còn thiếu một dòng, báo anh Việt nạp bù giúp.' : '')));
      go(scrHoanTien, true);
    } catch (e) { busy(false); }
  };
}


/* ---------- Chi tiết một phiếu hoàn tiền ----------

Màn này là chỗ chị Dung quyết chi hay từ chối, nên nó phải bày đủ ba thứ mà
màn danh sách không bày nổi: ảnh bằng chứng xem được to, số tài khoản khách
đọc được từng chữ số, và đơn gốc gồm những món gì.

Nút Từ chối chỉ hiện khi máy chủ nói còn từ chối được. Không tự đoán ở đây:
điều kiện thật là tiền chưa ra, và chỉ máy chủ biết chắc điều đó. */
async function htChiTiet(ma) {
  frame('Phiếu hoàn tiền', '<div class="emp"><div class="e1">⏳</div><div>Đang mở phiếu...</div></div>');
  var d;
  try { d = await api('vagabond.hoan_tien.chi_tiet', { ho_so: ma }); }
  catch (e) {
    frame('Phiếu hoàn tiền', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không mở được phiếu') + '</div></div>');
    return;
  }
  htCtData = d;
  htCtVe();
}

function htCtDong(nhan, gtri, dam) {
  return '<div style="display:flex;gap:10px;padding:9px 0;border-bottom:1px solid #f2f4f7">' +
    '<div style="flex:0 0 40%;font-size:12px;color:#6b7280">' + h(nhan) + '</div>' +
    '<div style="flex:1;font-size:13.5px;' + (dam ? 'font-weight:800' : 'font-weight:600') +
    ';word-break:break-all">' + h(gtri === 0 || gtri ? String(gtri) : '(chưa có)') + '</div></div>';
}

function htCtVe() {
  var d = htCtData;
  var mau = d.trang_thai === 'Hoan thanh' ? '#065f46'
    : (d.trang_thai === 'Da doi soat' ? '#0a8a4a'
      : (d.trang_thai === 'Da chi' ? '#b45309' : (d.trang_thai === 'Da huy' ? '#6b7280' : '#b3261e')));

  var html = '<div class="card" style="padding:14px">' +
    '<div style="display:flex;align-items:flex-start;gap:10px">' +
    '<div style="flex:1;min-width:0"><b style="font-size:16px">' + h(d.ten_khach || '(khách lẻ)') + '</b>' +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:2px">' + h(d.name) + '</div></div>' +
    '<div style="text-align:right"><b style="font-size:18px">' + money(d.so_tien) + ' đ</b>' +
    '<div style="font-size:11.5px;font-weight:800;color:' + mau + '">' + h(htDsTen(d.trang_thai)) + '</div></div>' +
    '</div></div>';

  if (d.trang_thai === 'Da huy') {
    html += '<div style="background:#f3f4f6;border:1px solid #e5e7eb;border-radius:10px;padding:11px 13px;' +
      'margin-top:11px;font-size:12.5px;line-height:1.65;color:#374151">' +
      '<b>Phiếu đã bị từ chối, không chi tiền.</b><br>Lý do: ' + h(d.ly_do_tu_choi || '(không ghi)') +
      (d.nguoi_tu_choi ? '<br>Người từ chối: ' + h(d.nguoi_tu_choi) : '') +
      (d.ngay_tu_choi ? '<br>Lúc: ' + h(String(d.ngay_tu_choi).slice(0, 16)) : '') + '</div>';
  }

  html += '<div class="sec">Lý do và diễn giải</div><div class="card" style="padding:2px 14px 8px">' +
    htCtDong('Loại phiếu',
      d.loai_hoan === 'Tien nop thua'
        ? 'Tiền nộp thừa · KHÔNG lập hoá đơn trả hàng, doanh thu giữ nguyên'
        : 'Trả hàng · lập hoá đơn trả hàng để khử doanh thu', 1) +
    htCtDong('Lý do hoàn', htLyDoTen(d.ly_do || ''), 1) +
    htCtDong('Diễn giải', d.dien_giai || '') +
    htCtDong('Người lập', d.nguoi_duyet || '') +
    htCtDong('Lập lúc', String(d.creation || '').slice(0, 16)) +
    '</div>';

  html += '<div class="sec">Tài khoản nhận tiền của khách</div><div class="card" style="padding:2px 14px 8px">' +
    htCtDong('Chủ tài khoản', d.ten_tk || '', 1) +
    htCtDong('Số tài khoản', d.so_tk || '', 1) +
    htCtDong('Ngân hàng', d.ngan_hang || '') +
    htCtDong('Điện thoại', d.sdt || '') +
    htCtDong('Nội dung chuyển khoản', d.noi_dung_ck || '', 1) +
    '</div>';

  html += '<div class="sec">Ảnh bằng chứng</div>';
  if ((d.anh || []).length) {
    html += '<div style="display:flex;gap:8px;flex-wrap:wrap;padding:2px">' +
      d.anh.map(function (a) {
        return '<div class="htcanh" data-url="' + h(a.url) + '" style="width:92px;height:92px;border-radius:10px;' +
          'background-image:url(' + a.url + ');background-size:cover;background-position:center;' +
          'border:1px solid #e3e6ec;cursor:pointer"></div>';
      }).join('') + '</div>' +
      '<div style="font-size:11px;color:#9ca3af;padding:7px 2px 0">Bấm vào ảnh để xem to.</div>';
  } else {
    html += '<div style="font-size:12.5px;color:#b3261e;background:#fef2f2;border:1px solid #fecaca;' +
      'border-radius:10px;padding:10px 12px;line-height:1.6">Phiếu này chưa có ảnh bằng chứng. ' +
      'Anh chị bảo bạn Sales chụp lại bánh hỏng hoặc màn hình khách yêu cầu rồi đính vào, ' +
      'trước khi quyết chi.</div>';
  }

  if (d.don) {
    html += '<div class="sec">Đơn gốc ' + h(d.don.name) + '</div><div class="card" style="padding:2px 14px 10px">' +
      htCtDong('Ngày đơn', d.don.ngay) +
      /* Ma don Pancake la thu DUY NHAT phep doi soat tu dong dem tim trong
         noi dung chuyen khoan. De trong thi dong "SePay da nhan" chac chan
         ra 0, va nguoi doc phai biet ngay do la vi sao. */
      htCtDong('Mã đơn Pancake', d.don.ma_pancake || '') +
      htCtDong('Tổng đơn', money(d.don.tong) + ' đ', 1) +
      /* Truoc 19/08/2026 dong nay chi hien cho phieu tien nop thua. Nhung
         truoc khi chuyen tien ra, phieu tra hang cung can dung mot cau hoi:
         tien khach da that su vao chua. Ca Ms.Giang hom 19/08 la vi khong
         co dong nay ma khong ai tra loi duoc. */
      htCtDong('SePay đã nhận', money(d.don.da_nhan_sepay) + ' đ', 1) +
      (d.loai_hoan === 'Tien nop thua'
        ? htCtDong('Khách nộp thừa',
            money(Math.max(0, Number(d.don.da_nhan_sepay || 0) - Number(d.don.tong || 0))) + ' đ', 1)
        : '') +
      (Number(d.don.da_nhan_sepay || 0) <= 0 ? htCtSepayTrong(d) : '') +
      htCtDong('Đã thu', money(d.don.da_thu) + ' đ') +
      (d.don.diem_ban ? htCtDong('Điểm bán', d.don.diem_ban) : '') +
      '<div style="padding:9px 0 0">' + (d.don.mon || []).map(function (m) {
        return '<div style="display:flex;gap:8px;font-size:12.5px;padding:3px 0;color:#374151">' +
          '<div style="flex:1;min-width:0">' + h(m.ten) + '</div>' +
          '<div style="flex:none;color:#6b7280">x' + money(m.sl) + '</div>' +
          '<div style="flex:none;font-weight:700">' + money(m.tien) + '</div></div>';
      }).join('') + '</div></div>';
  }

  /* Tien da ra ma chung tu chua sinh duoc: noi ngay dau man, truoc ca khoi
     chung tu, vi day la viec phai lam chu khong phai mot dong ghi chu. */
  if (d.loi_sinh_ct) {
    html += '<div class="card" style="padding:12px 14px;background:#fef2f2;border:1.5px solid #fecaca">' +
      '<b style="font-size:13.5px;color:#b3261e">Tiền đã ra nhưng chứng từ chưa sinh được</b>' +
      '<div style="font-size:12.5px;color:#7f1d1d;line-height:1.6;margin-top:4px">' + h(d.loi_sinh_ct) + '</div></div>';
  }

  html += '<div class="sec">Chứng từ hệ sinh ra</div><div class="card" style="padding:2px 14px 8px">' +
    htCtDong('Hoá đơn trả hàng', d.hoa_don_tra || '') +
    htCtDong('Phiếu chi', d.phieu_chi ? (d.phieu_chi + (d.phieu_chi_trang_thai ? ' · ' + d.phieu_chi_trang_thai : '')) : '') +
    htCtDong('Đã đối soát SePay', d.da_doi_soat ? 'Rồi' : 'Chưa') +
    htCtDong('Mã giao dịch ngân hàng', d.ma_gd || '') +
    htCtDong('Kho nhận hàng trả', d.kho_huy || '') +
    '</div>';

  /* Doi chieu TAY khoan tien vao. Chi hien cho nguoi duoc quyen, va noi ro
     day la mot chu ky cua nguoi chu khong phai mot phep may tu chay. */
  html += '<div class="sec">Giao dịch tiền vào đã đối chiếu</div><div class="card" style="padding:2px 14px 12px">';
  if (d.gd_vao_ct) {
    html += htCtDong('Giao dịch', d.gd_vao_ct.name) +
      htCtDong('Ngày về', String(d.gd_vao_ct.date || '')) +
      htCtDong('Số tiền vào', money(d.gd_vao_ct.deposit) + ' đ', 1) +
      htCtDong('Nội dung', d.gd_vao_ct.description || '') +
      htCtDong('Người đối chiếu', d.nguoi_gan_gd_vao || '');
  } else {
    html += '<div style="font-size:12.5px;color:#6b7280;padding:10px 0 4px;line-height:1.6">' +
      'Chưa ai gắn khoản tiền vào nào cho phiếu này. Khi khách tự gõ nội dung ' +
      'chuyển khoản thì máy không tự khớp được, phải có người nhìn sao kê và chọn.</div>';
  }
  if (d.duoc_doi_chieu && d.trang_thai !== 'Da huy') {
    html += '<button class="btn gh" id="htCtGd" style="margin:8px 0 0;width:100%">🔎 ' +
      (d.gd_vao_ct ? 'Chọn lại giao dịch tiền vào' : 'Đối chiếu tay khoản tiền vào') + '</button>';
  }
  html += '</div>';

  html += htCtHddt(d);
  html += htCtUnc(d);

  var chan = '';
  if (d.trang_thai !== 'Da huy') {
    chan += '<button class="btn gh" id="htCtMb" style="margin:0;flex:1">🏦 Chuyển khoản</button>';
  }
  if (d.con_tu_choi_duoc && d.duoc_tu_choi) {
    chan += '<button class="btn" id="htCtTc" style="margin:0;flex:1;background:#b3261e;border-color:#b3261e">Từ chối hoàn tiền</button>';
  }
  var b = frame('Phiếu hoàn tiền', html, chan ? { footer: chan } : undefined);

  b.querySelectorAll('.htcanh').forEach(function (n) {
    n.onclick = function () { rndXemAnh(n.getAttribute('data-url')); };
  });
  var nMb = document.getElementById('htCtMb');
  if (nMb) nMb.onclick = function () { htMbBiz(d.name); };
  var nTc = document.getElementById('htCtTc');
  if (nTc) nTc.onclick = function () { htFormTuChoi(d.name); };
  var nGd = document.getElementById('htCtGd');
  if (nGd) nGd.onclick = function () { htFormGdVao(d); };

  var nUncN = document.getElementById('htUncNut');
  var nUncT = document.getElementById('htUncTep');
  if (nUncN && nUncT) {
    nUncN.onclick = function () { nUncT.value = ''; nUncT.click(); };
    nUncT.onchange = function () { htUncGui(d, nUncT.files && nUncT.files[0]); };
  }
  b.querySelectorAll('.htuncanh').forEach(function (n) {
    n.onclick = function () { htUncPhongTo(d.name, n.getAttribute('data-tep'), n.getAttribute('data-ten')); };
  });
  b.querySelectorAll('.htunctep').forEach(function (n) {
    n.onclick = function () { htUncTaiTep(d.name, n.getAttribute('data-tep'), n.getAttribute('data-ten')); };
  });
  htUncNapAnh(b, d.name);
  var nKt = document.getElementById('htUncXong');
  if (nKt) nKt.onclick = function () { htUncKetThuc(d); };

  var nHd = document.getElementById('htHddtMo');
  if (nHd) nHd.onclick = function () { htHddtMo(d); };
  var nHdC = document.getElementById('htHddtChep');
  if (nHdC) nHdC.onclick = function () { htHddtChep(d); };

  var nTtL = document.getElementById('htTtLuu');
  if (nTtL) nTtL.onclick = function () { htTtLuu(d); };
  var nTtG = document.getElementById('htTtGo');
  if (nTtG) nTtG.onclick = function () { htTtGo(d); };
}


/* ---------- Hoá đơn điện tử của đơn gốc ----------

Anh Việt 20/08/2026: chị Dung cần xuất hoá đơn thay thế cho đơn đã hoàn tiền,
nên phải thấy ngay mã hoá đơn đã xuất và bấm một phát sang được M-Invoice.

Khối này CHỈ ĐỌC và CHỈ mở liên kết. Không phát hành, không ký, không huỷ,
không sửa tờ nào - anh Việt đã dặn sau lần phải đi xoá tay hoá đơn bên
M-Invoice ngày 13/08. */
function htCtHddt(d) {
  var v = d.hddt;
  var h_ = '<div class="sec">Hoá đơn điện tử của đơn gốc</div>' +
    '<div class="card" style="padding:12px 14px">';
  if (!v) {
    return h_ + '<div style="font-size:12.5px;color:#6b7280;line-height:1.6">' +
      'Đơn gốc chưa xuất hoá đơn điện tử, hoặc đơn này không xuất hoá đơn. ' +
      'Không có gì để lập hoá đơn thay thế.</div></div>';
  }
  h_ += htCtDong('Mã hoá đơn', v.ma || '', 1) +
    (v.trang_thai ? htCtDong('Trạng thái bên M-Invoice', v.trang_thai) : '') +
    (v.so_bao_mat ? htCtDong('Mã tra cứu', v.so_bao_mat) : '');
  h_ += '<button class="btn gh" id="htHddtMo" style="margin:9px 0 0;width:100%">' +
    '🔗 Xem hoá đơn bên M-Invoice</button>';
  if (!v.da_khai_mau) {
    h_ += '<button class="btn gh" id="htHddtChep" style="margin:8px 0 0;width:100%">' +
      '📋 Chép mã tra cứu</button>' +
      '<div style="font-size:11.5px;color:#92400e;background:#fffbeb;border:1px solid #fde68a;' +
      'border-radius:9px;padding:9px 11px;margin-top:8px;line-height:1.6">' +
      'Nút trên đang mở trang chủ M-Invoice chứ chưa nhảy thẳng tới tờ hoá đơn, ' +
      'vì em chưa biết đường dẫn sâu của họ. Chị Dung mở một tờ bất kỳ bên đó, ' +
      'chép đường dẫn trên thanh địa chỉ gửi anh Việt, em khai vào Cài đặt một ' +
      'lần là từ đó bấm một phát ra đúng tờ.</div>';
  }
  h_ += htCtThayThe(d, v);
  return h_ + '</div>';
}

/* ---------- Nối mã hoá đơn THAY THẾ ----------

Chị Dung 20/08/2026: *"không cần nút click vào M-Invoice vì mỗi hoá đơn bên
M-Invoice không có link riêng. Chị ấy sẽ tự tìm hoá đơn rồi tự thay thế."*
Anh Việt: *"ví dụ hoá đơn đã thay thế rồi thì em viết luồng automation để nối
mã hoá đơn đã thay thế đó vào đơn hàng trước đó và vào phiếu hoàn tiền luôn
được không?"*

Nên khối này KHÔNG thay thế hoá đơn. Việc thay thế chị Dung làm tay bên
M-Invoice, ở đây chỉ ghi lại số tờ mới rồi máy tự nối vào cả đơn hàng gốc lẫn
phiếu hoàn tiền, kèm một dòng nhật ký trên đơn. Đó là phần máy làm được mà
không đụng tới hoá đơn đã gửi cơ quan thuế. */
function htCtThayThe(d, v) {
  var tt = (v && v.thay_the) || '';
  if (tt) {
    return '<div style="margin-top:10px;border:1.5px solid #a7f3d0;background:#ecfdf5;' +
      'border-radius:10px;padding:10px 12px">' +
      '<div style="font-size:11.5px;color:#047857;font-weight:700">ĐÃ THAY THẾ BẰNG</div>' +
      '<div style="font-size:15px;font-weight:800;color:#065f46;margin-top:2px;word-break:break-all">' +
      h(tt) + '</div>' +
      (v.thay_the_luc ? '<div style="font-size:11.5px;color:#4b7a63;margin-top:2px">Ghi nhận lúc ' +
        h(String(v.thay_the_luc).slice(0, 16)) + '</div>' : '') +
      '<button class="btn gh" id="htTtGo" style="margin:8px 0 0;width:100%;font-size:14px">' +
      'Ghi nhầm, gỡ ra</button></div>';
  }
  return '<div style="margin-top:10px;border:1.5px dashed #d1d5db;border-radius:10px;padding:10px 12px">' +
    '<div style="font-size:12.5px;color:#374151;line-height:1.6">' +
    'Thay thế xong bên M-Invoice thì dán số tờ mới vào đây. Máy nối luôn vào ' +
    'đơn hàng gốc và phiếu này, không phải mở lại ba nơi.</div>' +
    '<div style="display:flex;gap:8px;margin-top:8px">' +
    '<input id="htTtKh" class="lgi" style="flex:0 0 40%;margin:0" placeholder="Ký hiệu, ví dụ C26TVP">' +
    '<input id="htTtSo" class="lgi" style="flex:1;margin:0" placeholder="Số hoá đơn mới" inputmode="numeric">' +
    '</div>' +
    '<button class="btn" id="htTtLuu" style="margin:8px 0 0;width:100%;font-size:15px">' +
    'Nối mã hoá đơn thay thế</button>' +
    '<div style="font-size:11px;color:#9ca3af;margin-top:7px;line-height:1.55">' +
    'Ô này chỉ GHI LẠI con số. Máy không phát hành, không huỷ, không thay thế ' +
    'tờ nào bên cơ quan thuế.</div></div>';
}

async function htTtLuu(d) {
  var so = (document.getElementById('htTtSo') || {}).value || '';
  var kh = (document.getElementById('htTtKh') || {}).value || '';
  if (!String(so).trim()) {
    return baoTin('Chưa nhập số hoá đơn mới. Mở tờ thay thế bên M-Invoice rồi chép số vào ô này.', 'Thiếu số hoá đơn');
  }
  busy(true);
  try {
    var r = await api('vagabond.hoan_tien.ghi_hddt_thay_the', { ma_phieu: d.name, so: so, ky_hieu: kh });
    busy(false);
    toast((r && r.loi_nhan) || 'Đã nối mã hoá đơn thay thế.', 5000);
    htChiTiet(d.name);
  } catch (e) {
    busy(false);
    baoTin((e && e.message) || 'Chưa nối được mã.', 'Lỗi');
  }
}

async function htTtGo(d) {
  var ly_do = await hoiChu('Gỡ mã hoá đơn thay thế', 'Vì sao gỡ? Câu này nằm lại trong nhật ký của đơn hàng.', '');
  if (ly_do === null) return;
  if (!String(ly_do || '').trim()) {
    return baoTin('Phải ghi lý do thì mới gỡ được. Ô này trống lại mà không ai biết vì sao là chỗ sinh ra hiểu nhầm.', 'Thiếu lý do');
  }
  busy(true);
  try {
    var r = await api('vagabond.hoan_tien.go_hddt_thay_the', { ma_phieu: d.name, ly_do: ly_do });
    busy(false);
    toast((r && r.loi_nhan) || 'Đã gỡ.', 4000);
    htChiTiet(d.name);
  } catch (e) {
    busy(false);
    baoTin((e && e.message) || 'Chưa gỡ được.', 'Lỗi');
  }
}

function htHddtMo(d) {
  var v = d.hddt || {};
  var u = v.lien_ket || v.host;
  if (!u) {
    return baoTin('Chưa khai host M-Invoice trong Cài đặt nên em chưa biết mở đi đâu.', 'Thiếu cấu hình');
  }
  window.open(u, '_blank', 'noopener');
}

function htHddtChep(d) {
  var v = d.hddt || {};
  var t = v.so_bao_mat || v.so || '';
  if (!t) return toast('Đơn này không có mã tra cứu.', 3000);
  try {
    navigator.clipboard.writeText(t);
    toast('Đã chép mã tra cứu ' + t + '. Dán vào ô tra cứu bên M-Invoice.', 5000);
  } catch (e) {
    baoTin('Mã tra cứu: ' + t, 'Chép tay giúp em');
  }
}


/* ---------- Uỷ nhiệm chi và kết thúc phiếu ----------

Anh Việt 19/08/2026: đính uỷ nhiệm chi -> sales lấy gửi khách -> hoàn thành
-> máy tự ghi sổ. Trước đó phiếu đi tới "Đã đối soát" rồi đứng lại vĩnh
viễn, vì bước ghi sổ nằm trên Desk chứ không nằm trên màn này.

Vì sao vẫn để HAI nhịp chứ không ghi sổ ngay lúc đính tệp: chị Dung chốt
16/08 rằng nút ghi sổ phải nằm trong tay kế toán. Và giữa hai nhịp đó chính
là khoảng Sales tải tệp về gửi khách. Gộp làm một thì mất đúng khoảng ấy. */
function htCtUnc(d) {
  var tep = d.unc || [];
  /* Cờ "đã có UNC hay chưa" đọc thẳng từ máy chủ chứ không đếm lại mảng ở
     đây. Máy chủ đếm tệp thật trên phiếu chi ngay lúc hỏi; đếm lại ở màn
     là mở đường cho hai bên nói hai con số khác nhau (QT-19). */
  var coUnc = !!d.co_unc;
  var h_ = '<div class="sec">Uỷ nhiệm chi và kết thúc phiếu</div>' +
    '<div class="card" style="padding:12px 14px">';

  if (coUnc && tep.length) {
    /* Anh UNC ve thanh HINH NHO chu khong con la mot dong ten tep
       IMG_xxx.jpg (anh Viet 20/08/2026: "Dung the img de render anh duoi
       dang Thumbnail nho, click vao thi phong to"). Ruot anh di qua duong
       tai_unc cua may chu chu khong qua /private/files: tep dinh vao
       Payment Entry ma Sales khong co quyen doc doctype do, dua duong dan
       tho la Sales bam vao chi nhan 403. */
    var anhUnc = tep.filter(function (t) { return t.la_anh && t.tep; });
    var tepKhac = tep.filter(function (t) { return !(t.la_anh && t.tep); });
    if (anhUnc.length) {
      h_ += '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:7px">' +
        anhUnc.map(function (t) {
          return '<div class="htuncanh" data-tep="' + h(t.tep) + '" data-ten="' + h(t.ten) + '" ' +
            'style="width:86px;height:86px;border-radius:10px;border:1.5px solid #d1fae5;' +
            'background:#f0fdf4;display:flex;align-items:center;justify-content:center;' +
            'overflow:hidden;font-size:20px;color:#a7c4b5">⏳</div>';
        }).join('') + '</div>' +
        '<div style="font-size:11.5px;color:#4b7a63;margin-bottom:7px">Bấm vào ảnh để ' +
        'phóng to, trong ảnh phóng to có nút tải về gửi khách.</div>';
    }
    h_ += tepKhac.map(function (t) {
      return '<div class="htunctep" data-tep="' + h(t.tep || '') + '" data-ten="' + h(t.ten) + '" ' +
        'style="display:flex;gap:9px;align-items:center;cursor:pointer;' +
        'border:1.5px solid #d1fae5;background:#f0fdf4;border-radius:10px;' +
        'padding:9px 11px;margin-bottom:7px">' +
        '<div style="flex:none;font-size:17px">📄</div>' +
        '<div style="flex:1;min-width:0">' +
        '<div style="font-size:13px;font-weight:700;color:#065f46;word-break:break-all">' +
        h(t.ten) + '</div>' +
        '<div style="font-size:11.5px;color:#4b7a63">Đính lúc ' +
        h(String(t.luc || '').slice(0, 16)) + ' · bấm để tải về gửi khách</div></div></div>';
    }).join('');
  } else {
    h_ += '<div style="font-size:12.5px;color:#6b7280;line-height:1.6;padding-bottom:4px">' +
      'Chưa có uỷ nhiệm chi nào. Dòng sao kê SePay <b>không</b> thay được UNC khi ' +
      'giải trình với cơ quan thuế, nên phiếu chỉ khép lại được sau khi có tệp này.</div>';
  }

  if (d.dinh_duoc_unc) {
    h_ += '<button class="btn gh" id="htUncNut" style="margin:6px 0 0;width:100%">📎 ' +
      (coUnc ? 'Đính thêm uỷ nhiệm chi' : 'Đính uỷ nhiệm chi') + '</button>' +
      '<input type="file" id="htUncTep" accept="image/*,application/pdf" style="display:none">';
  }
  if (d.ket_thuc_duoc) {
    h_ += '<button class="btn" id="htUncXong" style="margin:8px 0 0;width:100%">✅ Hoàn thành và ghi sổ</button>' +
      '<div style="font-size:11.5px;color:#6b7280;margin-top:6px;line-height:1.55">' +
      'Bấm nút này là máy ghi sổ phiếu chi ' + h(d.phieu_chi || '') + ' và đóng phiếu ' +
      'hoàn tiền. Trước khi bấm, anh chị nhớ gửi tệp trên cho khách.</div>';
  } else if (d.trang_thai === 'Hoan thanh') {
    h_ += '<div style="font-size:12.5px;color:#065f46;background:#f0fdf4;border:1px solid #a7f3d0;' +
      'border-radius:9px;padding:9px 11px;margin-top:8px;line-height:1.6">Phiếu đã kết thúc' +
      (d.nguoi_hoan_thanh ? ' bởi <b>' + h(d.nguoi_hoan_thanh) + '</b>' : '') +
      (d.ngay_hoan_thanh ? ' lúc ' + h(String(d.ngay_hoan_thanh).slice(0, 16)) : '') + '.</div>';
  }
  return h_ + '</div>';
}

/* Nap hinh nho cua tung anh UNC sau khi man da ve. Goi mot luot, moi anh
   mot yeu cau rieng de anh nao hong khong keo do anh khac. */
async function htUncNapAnh(b, hoSo) {
  var o = b.querySelectorAll('.htuncanh');
  for (var i = 0; i < o.length; i++) {
    var n = o[i];
    try {
      var r = await api('vagabond.hoan_tien.tai_unc', {
        ho_so: hoSo, tep: n.getAttribute('data-tep'), co: 'nho'
      });
      n.innerHTML = '<img src="data:' + r.mime + ';base64,' + r.b64 + '" alt="" ' +
        'style="width:100%;height:100%;object-fit:cover;display:block">';
    } catch (e) { n.textContent = '🚫'; n.title = (e && e.message) || ''; }
  }
}

/* Phong to mot anh UNC: keo ban day du roi mo overlay co nut tai ve. */
async function htUncPhongTo(hoSo, tep, ten) {
  toast('Đang tải ảnh gốc...', 2000);
  var r;
  try { r = await api('vagabond.hoan_tien.tai_unc', { ho_so: hoSo, tep: tep, co: 'lon' }); }
  catch (e) { return toast((e && e.message) || 'Không tải được ảnh', 5000); }
  var url = 'data:' + r.mime + ';base64,' + r.b64;
  var ov = document.createElement('div');
  ov.style.cssText = 'position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,.92);' +
    'display:flex;align-items:center;justify-content:center;padding:16px';
  ov.innerHTML = '<img src="' + url + '" style="max-width:100%;max-height:88%;border-radius:8px">' +
    '<div style="position:absolute;top:calc(env(safe-area-inset-top,0px) + 12px);right:18px;' +
    'color:#fff;font-size:32px;line-height:1">&times;</div>' +
    '<a download="' + h(ten || r.ten || 'uy-nhiem-chi') + '" href="' + url + '" ' +
    'style="position:absolute;bottom:calc(env(safe-area-inset-bottom,0px) + 18px);' +
    'left:50%;transform:translateX(-50%);background:#16a34a;color:#fff;text-decoration:none;' +
    'font-weight:800;font-size:14px;border-radius:12px;padding:11px 22px">⬇️ Tải về gửi khách</a>';
  ov.onclick = function (e) { if (e.target.tagName !== 'A' && e.target.tagName !== 'IMG') ov.remove(); };
  document.body.appendChild(ov);
}

/* Tai mot tep UNC khong phai anh (PDF...) ve may qua duong tai_unc. */
async function htUncTaiTep(hoSo, tep, ten) {
  toast('Đang tải tệp...', 2000);
  var r;
  try { r = await api('vagabond.hoan_tien.tai_unc', { ho_so: hoSo, tep: tep, co: 'lon' }); }
  catch (e) { return toast((e && e.message) || 'Không tải được tệp', 5000); }
  var a = document.createElement('a');
  a.href = 'data:' + r.mime + ';base64,' + r.b64;
  a.download = ten || r.ten || 'uy-nhiem-chi';
  document.body.appendChild(a);
  a.click();
  a.remove();
}

function htUncGui(d, file) {
  if (!file) return;
  /* Không nén, không đổi định dạng: uỷ nhiệm chi là chứng từ gốc để giải
     trình thuế, chỉnh một pixel cũng là chỉnh chứng từ. Chỉ chặn tệp quá
     nặng ngay tại đây để người bấm biết liền, máy chủ vẫn chặn lần nữa. */
  if (file.size > 12 * 1024 * 1024) {
    return toast('Tệp nặng quá 12 MB nên máy không nhận. Xuất lại bản PDF nhỏ hơn giúp em.', 4500);
  }
  var fr = new FileReader();
  fr.onload = async function () {
    var url = String(fr.result || '');
    toast('Đang tải uỷ nhiệm chi lên...', 2500);
    try {
      var kq = await api('vagabond.hoan_tien.dinh_unc', {
        ho_so: d.name, ten: file.name || 'uy-nhiem-chi.pdf', noi_dung: url
      });
      toast((kq && kq.ghi_chu) || 'Đã đính uỷ nhiệm chi.', 5000);
      htChiTiet(d.name);
    } catch (e) {
      toast(h((e && e.message) || 'Không đính được uỷ nhiệm chi'), 6000);
    }
  };
  fr.readAsDataURL(file);
}

async function htUncKetThuc(d) {
  var ok = await hoiCo('Hoàn thành phiếu hoàn tiền',
    'Máy sẽ ghi sổ phiếu chi ' + h(d.phieu_chi || '') + ' và đóng phiếu ' + h(d.name) +
    '. Ghi sổ rồi thì không sửa lại được, chỉ huỷ bút toán mới đổi được. ' +
    'Anh chị đã gửi uỷ nhiệm chi cho khách chưa?', 'Ghi sổ');
  if (!ok) return;
  toast('Đang ghi sổ...', 2500);
  try {
    var kq = await api('vagabond.hoan_tien.hoan_thanh', { ho_so: d.name });
    toast((kq && kq.ghi_chu) || 'Đã kết thúc phiếu.', 5500);
    htChiTiet(d.name);
  } catch (e) {
    toast(h((e && e.message) || 'Không kết thúc được phiếu'), 6500);
  }
}


/* Vi sao dong "SePay da nhan" ra 0 - noi thang thay vi de nguoi doc doan.

   Hai nguyen nhan, va cach xu ly khac han nhau. Thieu ma don Pancake thi
   phep doi soat khong co gi de tim, sua o hoa don. Co ma don ma van 0 thi
   khach da tu go noi dung chuyen khoan, phai doi chieu tay. */
function htCtSepayTrong(d) {
  var vi_sao = d.don.ma_pancake
    ? 'Đơn có mã Pancake <b>' + h(d.don.ma_pancake) + '</b> nhưng không giao dịch nào ' +
      'mang mã này trong nội dung. Thường là khách tự gõ nội dung chuyển khoản thay vì ' +
      'quét mã QR, nên máy không có gì để bám. Dùng nút đối chiếu tay ở dưới.'
    : 'Hoá đơn này chưa có mã đơn Pancake, mà đó là thứ duy nhất phép đối soát dựa vào. ' +
      'Nên con số 0 ở đây <b>không</b> có nghĩa là khách chưa chuyển tiền.';
  return '<div style="font-size:12px;color:#92400e;background:#fffbeb;border:1px solid #fde68a;' +
    'border-radius:9px;padding:9px 11px;margin:8px 0 2px;line-height:1.6">' + vi_sao + '</div>';
}


/* ---------- Đối chiếu tay khoản tiền vào ----------

Máy chỉ lọc ra ứng viên gần đúng số tiền và gần đúng ngày. Chọn dòng nào là
việc của người, và tên người đó được ghi lại ngay cạnh giao dịch. Không để
máy tự chọn: một khoản 650.000 đ ngày 13/08 có thể là của bất kỳ đơn nào
cùng số tiền. */
async function htFormGdVao(d) {
  var soTien = Number((d.don && d.don.tong) || d.so_tien || 0);
  var ngay = (d.don && d.don.ngay) || '';
  frame('Đối chiếu tiền vào', '<div class="emp"><div class="e1">⏳</div><div>Đang lọc sao kê...</div></div>');
  var kq;
  try {
    kq = await api('vagabond.sepay.tim_gd_vao', { so_tien: soTien, ngay: ngay, so_ngay: 30 });
  } catch (e) {
    frame('Đối chiếu tiền vào', '<div class="emp"><div class="e1">⚠️</div><div>' +
      h((e && e.message) || 'Không lọc được sao kê') + '</div></div>');
    return;
  }
  var rows = (kq && kq.rows) || [];
  var than =
    '<div style="font-size:12.5px;color:#374151;background:#f8fafc;border:1px solid #e5e7eb;' +
    'border-radius:9px;padding:10px 12px;margin-bottom:11px;line-height:1.6">' +
    'Đang tìm khoản tiền vào quanh <b>' + money(soTien) + ' đ</b>' +
    (ngay ? ' và quanh ngày <b>' + h(ngay) + '</b>' : '') + '. ' +
    'Chọn đúng dòng khách đã chuyển. Tên anh chị được ghi lại cạnh giao dịch này.</div>';
  if (!rows.length) {
    than += '<div style="font-size:12.5px;color:#b3261e;background:#fef2f2;border:1px solid #fecaca;' +
      'border-radius:9px;padding:10px 12px;line-height:1.6">Không có giao dịch tiền vào nào ' +
      'gần số tiền và ngày này trong sao kê đang có. Nếu tiền chắc chắn đã về thì sao kê ' +
      'còn thiếu, báo anh Việt nạp bù giúp.</div>';
  } else {
    than += rows.map(function (r) {
      return '<button class="htgdv" data-gd="' + h(r.name) + '" style="display:block;width:100%;text-align:left;' +
        'border:1.5px solid #e5e7eb;background:#fff;border-radius:11px;padding:10px 12px;margin-bottom:8px">' +
        '<div style="display:flex;gap:8px;align-items:baseline">' +
        '<div style="flex:1;font-weight:800;font-size:14px;color:#0a8a4a">+' + money(r.deposit) + ' đ</div>' +
        '<div style="flex:none;font-size:12px;color:#6b7280">' + h(String(r.date || '')) + '</div></div>' +
        '<div style="font-size:11.5px;color:#6b7280;margin-top:3px;word-break:break-all">' +
        h(String(r.description || '').slice(0, 140)) + '</div></button>';
    }).join('');
  }
  if (d.gd_vao_ct) {
    than += '<button class="btn gh" id="htGdBo" style="margin:6px 0 0;width:100%">Bỏ gắn giao dịch hiện tại</button>';
  }
  var b = frame('Đối chiếu tiền vào', than);
  b.querySelectorAll('.htgdv').forEach(function (n) {
    n.onclick = function () { htGdGan(d.name, n.getAttribute('data-gd')); };
  });
  var nBo = document.getElementById('htGdBo');
  if (nBo) nBo.onclick = function () { htGdGan(d.name, ''); };
}


async function htGdGan(ma, gd) {
  try {
    await api('vagabond.hoan_tien.gan_gd_vao', { ho_so: ma, gd: gd });
    toast(gd ? 'Đã gắn giao dịch ' + gd : 'Đã bỏ gắn giao dịch', 3500);
  } catch (e) {
    toast((e && e.message) || 'Không gắn được giao dịch', 5000);
    return;
  }
  htChiTiet(ma);
}


/* ---------- Form từ chối hoàn tiền ----------

Lý do bắt buộc, và kiểm ở CẢ hai nơi. Ở đây kiểm để người bấm biết ngay mà
sửa; ở máy chủ kiểm vì đó mới là chỗ chặn thật (QT-19). Câu chữ này về sau
là thứ duy nhất giải thích được vì sao khách không nhận được tiền. */
function htFormTuChoi(ma) {
  var goi = [
    'Khách đổi ý, không yêu cầu hoàn nữa',
    'Ảnh bằng chứng không hợp lệ',
    'Đơn đã được xử lý bằng cách khác',
    'Sai số tiền, lập lại phiếu mới'
  ];
  var than =
    '<div style="font-size:12.5px;color:#b3261e;background:#fef2f2;border:1px solid #fecaca;' +
    'border-radius:9px;padding:10px 12px;margin-bottom:12px;line-height:1.6">' +
    'Từ chối là chặn hẳn một khoản tiền sắp ra. Phiếu chuyển sang <b>Đã huỷ</b>, ' +
    'không bị xoá, và máy sẽ không tự đối soát phiếu này nữa.</div>' +
    '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:9px">' +
    goi.map(function (g, i) {
      return '<button class="httcg" data-g="' + h(g) + '" style="border:1.5px solid #e5e7eb;background:#fff;' +
        'color:#374151;border-radius:999px;padding:6px 12px;font-size:12px;font-weight:600">' + h(g) + '</button>';
    }).join('') + '</div>' +
    '<textarea id="htTcLd" rows="4" placeholder="Lý do từ chối (bắt buộc, ít nhất 5 ký tự)" ' +
    'style="width:100%;border:1.5px solid #e5e7eb;border-radius:10px;padding:11px 12px;font-size:13.5px;' +
    'font-family:inherit;box-sizing:border-box"></textarea>';

  var hop = hopKhung('Từ chối hoàn tiền', than,
    '<button class="btn gh" id="htTcHuy" style="margin:0;flex:1">Thôi</button>' +
    '<button class="btn" id="htTcOk" style="margin:0;flex:1;background:#b3261e;border-color:#b3261e">Xác nhận từ chối</button>');
  hop.box.querySelector('.x').onclick = hop.dong;
  hop.box.querySelector('#htTcHuy').onclick = hop.dong;
  var o = hop.box.querySelector('#htTcLd');
  hop.box.querySelectorAll('.httcg').forEach(function (n) {
    n.onclick = function () {
      var g = n.getAttribute('data-g');
      o.value = o.value.trim() ? (o.value.trim() + '. ' + g) : g;
      o.focus();
    };
  });
  hop.box.querySelector('#htTcOk').onclick = async function () {
    var ld = (o.value || '').trim();
    if (ld.length < 5) {
      return baoTin('Phải ghi rõ lý do từ chối, ít nhất 5 ký tự. Câu này sẽ nằm lại trong ' +
        'hồ sơ và là thứ duy nhất giải thích được vì sao khách không nhận được tiền.', 'Chưa gửi được');
    }
    busy(true);
    try {
      var kq = await api('vagabond.hoan_tien.tu_choi', { ho_so: ma, ly_do: ld });
      busy(false);
      hop.dong();
      toast(kq.ghi_chu || 'Đã từ chối phiếu', 3500);
      htDsData = null;
      go(scrHoanTien, true);
    } catch (e) { busy(false); }
  };
}


/* ---------- Xuất thông tin chuyển khoản cho MB Biz ----------

Đi đúng nếp hồ sơ thanh toán APP đang chạy: ba dạng của cùng một thông
tin, vì ba dạng phục vụ ba việc khác nhau.

  đọc bằng mắt   - kiểm trước khi bấm, tránh chuyển nhầm người
  dán vào tệp lô - mỗi cột một ô Excel, khỏi tách tay
  riêng nội dung - dán vào ô Nội dung trên MB Biz

Nội dung chuyển khoản là chỗ quan trọng nhất của cả màn này: nó chính là
sợi dây để SePay tìm đường về đúng phiếu. Gõ tay hoặc sửa một chữ là dòng
tiền ra đó thành mồ côi, và kế toán phải khớp tay. */
async function htMbBiz(ma) {
  busy(true);
  var kq;
  try { kq = await api('vagabond.hoan_tien.thong_tin_chuyen_khoan', { ho_so: ma }); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Không dựng được thông tin', 'Lỗi'); }
  busy(false);

  var o = function (nhan, gtri, dam) {
    return '<div style="display:flex;gap:10px;padding:9px 0;border-bottom:1px solid #f2f4f7">' +
      '<div style="flex:0 0 38%;font-size:12px;color:#6b7280">' + h(nhan) + '</div>' +
      '<div style="flex:1;font-size:13.5px;' + (dam ? 'font-weight:800' : 'font-weight:600') +
      ';word-break:break-all">' + h(gtri || '(chưa khai)') + '</div></div>';
  };
  var than =
    (kq.nhac ? '<div style="font-size:12.5px;color:#b3261e;background:#fef2f2;border:1px solid #fecaca;border-radius:9px;padding:9px 11px;margin-bottom:11px;line-height:1.6">' + h(kq.nhac) + '</div>' : '') +
    '<div class="card" style="padding:2px 14px 8px;margin-bottom:12px">' +
    o('Số tài khoản', kq.so_tk, 1) +
    o('Tên người thụ hưởng', kq.ten_ck, 1) +
    o('Ngân hàng', kq.ngan_hang) +
    o('Số tiền', money(kq.so_tien) + ' đ', 1) +
    o('Nội dung', kq.noi_dung_ck, 1) +
    '</div>' +
    '<div style="font-size:11.5px;color:#9ca3af;line-height:1.6;margin-bottom:4px">' +
    'Nội dung chuyển khoản phải giữ <b>nguyên si</b>: SePay dò đúng chuỗi này để tự khớp ' +
    'về phiếu ' + h(kq.ma) + '. Sửa một chữ là dòng tiền ra thành mồ côi, phải khớp tay.' +
    '</div>' +
    (kq.da_doi_soat
      ? '<div style="font-size:12px;color:#0a8a4a;font-weight:700;margin-top:8px">Phiếu này ngân hàng đã báo tiền ra, không cần chuyển lại.</div>'
      : '');

  var hop = hopKhung('Chuyển khoản MB Biz', than,
    '<button class="btn gh" id="htMbCk" style="margin:0;flex:1">Chép nội dung</button>' +
    '<button class="btn" id="htMbAll" style="margin:0;flex:1">Chép dòng cho tệp lô</button>');
  hop.box.querySelector('.x').onclick = hop.dong;
  hop.box.querySelector('#htMbCk').onclick = async function () {
    try { await navigator.clipboard.writeText(kq.noi_dung_ck); toast('Đã chép nội dung chuyển khoản', 2500); }
    catch (e) { baoTin(kq.noi_dung_ck, 'Nội dung chuyển khoản'); }
  };
  hop.box.querySelector('#htMbAll').onclick = async function () {
    /* Dòng ngăn bằng Tab do backend dựng, đúng sáu cột của tệp lô MB. Dán
       vào Excel là mỗi cột một ô. Cấu trúc cột nằm ở ngan_hang.tep_lo, KHÔNG
       dựng ở đây - anh Việt chốt 17/08/2026. */
    var chu = kq.tsv || kq.dong_tab;
    try { await navigator.clipboard.writeText(chu); toast('Đã chép, dán thẳng vào tệp lô MB Biz', 3000); }
    catch (e) { baoTin(chu, 'Dòng cho tệp lô MB Biz'); }
    if ((kq.nhac_lo || []).length) baoTin(kq.nhac_lo.join('\n'), 'Có chỗ cần xem lại');
  };
}


/* ================= Kiểm bánh theo MÙA (anh Việt 17/08/2026) =================

Vì sao tách hẳn khỏi bảng kiểm bánh theo ngày
---------------------------------------------
Bảng theo ngày trả lời "hôm nay còn bao nhiêu cái để bán", mỗi sáng đếm lại
từ đầu vì bếp làm mới mỗi ngày.

Bảng mùa trả lời một câu khác: "cả mùa này còn bao nhiêu cái". Hộp MOONLAPIS
in 100 hộp là 100, không có chuyện mai làm thêm. Khách đặt giao ngày 25/09 và
khách đặt giao ngày 02/10 đều ăn vào cùng con số 100 đó.

Nên nguồn hàng ở đây không phải tồn đầu cộng bếp làm, mà là một HẠN MỨC gõ
tay - nhà in giao thêm thì sửa lên, hộp hỏng thì sửa xuống. Kế thừa nguyên si
phần còn lại từ bảng ngày: kéo đơn Pancake, chia Đã đặt / Chờ chốt, đơn kênh
khác đếm từ hoá đơn, trạng thái huỷ và xoá không đếm. */

var MV = { ds: null, mua: null, data: null, xem: 'sp', loc: 'all', tim: '' };

async function scrMuaVuDs() {
  frame('Kiểm bánh theo mùa', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc các mùa vụ...</div></div>');
  try { MV.ds = await api('vagabond.mua_vu.danh_sach', {}); }
  catch (e) {
    return frame('Kiểm bánh theo mùa',
      '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
  }
  var ds = (MV.ds && MV.ds.ds) || [];
  var html = '<div style="font-size:11.5px;color:#98a2b3;padding:2px 2px 10px;line-height:1.6">' +
    'Dành cho hàng sản xuất một lô có số lượng giới hạn: bánh trung thu, bánh Tết, ' +
    'panettone. Số lượng sản xuất do mình gõ tay, phần còn lại máy đếm từ đơn Pancake.</div>';

  if (!ds.length) {
    html += '<div class="emp"><div class="e1">🌕</div><div>Chưa có mùa vụ nào.</div>' +
      '<div style="font-size:12px;color:#9ca3af;margin-top:6px">Bấm nút bên dưới để lập mùa đầu tiên.</div></div>';
  } else {
    html += '<div class="card">' + ds.map(function (x) {
      var mau = x.dang_chay ? '#0a8a4a' : (x.tinh_trang === 'Da dong' ? '#98a2b3' : '#b45309');
      return '<div class="hub" data-mv="' + h(x.name) + '">' +
        '<div class="hub-i">' + (x.dang_chay ? '🌕' : '🌑') + '</div>' +
        '<div class="hub-t"><div class="t1">' + h(x.ten_mua) + '</div>' +
        '<div class="t2">' + mvNgay(x.tu_ngay) + ' đến ' + mvNgay(x.den_ngay) +
        ' · ' + money(x.so_sp) + ' sản phẩm</div></div>' +
        '<b style="font-size:11.5px;color:' + mau + ';white-space:nowrap">' +
        (x.dang_chay ? 'Đang chạy' : (x.tinh_trang === 'Da dong' ? 'Đã đóng' : 'Chưa tới')) + '</b></div>';
    }).join('') + '</div>';
  }

  var b = frame('Kiểm bánh theo mùa', html, { footer: '<button class="btn" id="mvMoi" style="margin:0">➕ Lập mùa vụ mới</button>' });
  b.querySelectorAll('[data-mv]').forEach(function (n) {
    n.onclick = function () { MV.mua = n.getAttribute('data-mv'); go(scrMuaVu); };
  });
  document.getElementById('mvMoi').onclick = mvLapMua;
}

function mvNgay(s) {
  if (!s) return '';
  var p = String(s).split('-');
  return p.length === 3 ? (p[2] + '/' + p[1]) : String(s);
}

async function mvLapMua() {
  var ten = await hoiNhap('Tên mùa vụ, ví dụ "Trung thu 2026"', '');
  if (ten === null) return;
  if (!(ten || '').trim()) return toast('Đặt tên cho mùa vụ giúp em.', 3500);
  var t1 = await hoiNhap('Bán từ ngày (YYYY-MM-DD)', String(new Date().toISOString().slice(0, 10)));
  if (t1 === null) return;
  var t2 = await hoiNhap('Bán đến ngày (YYYY-MM-DD)', '');
  if (t2 === null) return;
  busy(true);
  try {
    var kq = await api('vagabond.mua_vu.tao_mua', { ten_mua: ten, tu_ngay: t1, den_ngay: t2 });
    busy(false);
    MV.mua = kq.mua;
    toast('Đã lập mùa ' + kq.mua, 3000);
    go(scrMuaVu);
  } catch (e) { busy(false); baoTin((e && e.message) || 'Lập mùa lỗi', 'Không lập được'); }
}

/* ---------- Mở màn và nhịp tự làm mới (anh Việt báo 18/08/2026) ----------

Trước 18/08 màn này ĐỢI cả lượt kéo Pancake mới vẽ ra được. Anh bấm Đồng bộ
Pancake thì màn đứng im ở khung chờ, mãi mãi. Đọc bản ghi thì thấy máy chủ
chạy xong cả ba lần anh bấm, mà màn vẫn nằm ở khung chờ: lượt kéo đi ra
Internet, một lần mạng chập giữa chừng là lời hứa treo và màn kẹt theo.

Nay tách hẳn hai việc. Mở màn thì VẼ NGAY bằng số trong cơ sở dữ liệu, nhanh
và không bao giờ treo được. Việc kéo Pancake giao cho hậu trường, xong thì
nhịp dưới đây tự nạp lại. Máy chủ cũng tự kéo mỗi phút, nên số vẫn mới kể cả
lúc không ai mở màn. */
var MV_NHIP = null;
var MV_GIAY = 30;   /* anh Việt chốt: xin đồng bộ 30 giây một lần khi đang mở màn */
var MV_DAU = '';    /* dấu của lần vẽ trước, để không vẽ lại khi số không đổi */

async function scrMuaVu() {
  frame('Kiểm bánh theo mùa', '<div class="emp"><div class="e1">⏳</div><div>Đang mở bảng...</div></div>');
  try { MV.data = await api('vagabond.mua_vu.bang', { mua: MV.mua }); }
  catch (e) {
    return frame('Kiểm bánh theo mùa',
      '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không đọc được') + '</div></div>');
  }
  MV_DAU = mvDau(MV.data);
  mvVe();
  mvXin();
  mvBatNhip();
}

function mvDau(d) {
  try { return JSON.stringify([(d || {}).dong, (d || {}).lich, (d || {}).dot, (d || {}).dinh_muc]); }
  catch (e) { return String(Math.random()); }
}

/* Còn đứng ở màn mùa vụ không. Nhịp phải tự tắt khi người ta đi chỗ khác,
   nếu không nó chạy ngầm cả buổi và tốn pin điện thoại của các bạn. */
function mvConODay() { return S.stack[S.stack.length - 1] === scrMuaVu; }

function mvTatNhip() { if (MV_NHIP) { clearInterval(MV_NHIP); MV_NHIP = null; } }

function mvBatNhip() {
  mvTatNhip();
  MV_NHIP = setInterval(function () {
    if (!mvConODay()) return mvTatNhip();
    mvXin();
    setTimeout(mvNapLai, 7000);
  }, MV_GIAY * 1000);
}

/* Xin máy chủ kéo Pancake. Trả về ngay, không đợi kéo xong. */
async function mvXin() {
  try { await api('vagabond.mua_vu.xin_dong_bo', { mua: MV.mua }); } catch (e) { }
}

async function mvNapLai() {
  if (!mvConODay()) return mvTatNhip();
  /* Đang mở hộp thoại thì để yên: vẽ lại giữa lúc người ta đang gõ số sản
     xuất là cướp mất ô nhập của họ. Ô tìm nhanh cũng vậy. */
  if (document.querySelector('.sh')) return;
  if (document.activeElement && document.activeElement.id === 'mvTim') return;
  var d;
  try { d = await api('vagabond.mua_vu.bang', { mua: MV.mua }); } catch (e) { return; }
  if (!mvConODay() || document.querySelector('.sh')) return;
  var dau = mvDau(d);
  MV.data = d;
  /* Số không đổi thì không vẽ lại. Vẽ lại mỗi 30 giây mà không có gì mới
     chỉ làm màn giật và làm mất chỗ người ta đang đọc. */
  if (dau === MV_DAU) {
    /* Số không đổi thì không vẽ lại cả màn, nhưng vẫn phải nhích giờ đồng
       bộ, để nhìn là biết hệ đang chạy chứ không phải đang chết. */
    var nMoc = document.getElementById('mvMoc');
    if (nMoc) nMoc.innerHTML = mvChuMoc(d);
    return;
  }
  MV_DAU = dau;
  mvVe();
}

/* Nút Đồng bộ Pancake: xin kéo rồi nạp lại hai nhịp. Không đợi, không treo. */
async function mvSoatTay() {
  toast('Đang kéo đơn Pancake về, số tự cập nhật trong ít giây.', 4000);
  await mvXin();
  setTimeout(mvNapLai, 7000);
  setTimeout(mvNapLai, 16000);
}

function mvVe() {
  var d = MV.data;
  if (!d || !d.co_so) return frame('Kiểm bánh theo mùa', '<div class="emp"><div class="e1">🌑</div><div>Mùa vụ này không còn.</div></div>');
  var ds = d.dong || [];

  var tongSx = 0, tongDat = 0, tongCon = 0;
  ds.forEach(function (x) {
    tongSx += x.san_xuat || 0;
    tongDat += (x.da_dat || 0) + (x.cho_chot || 0) + (x.don_khac || 0);
    tongCon += x.co_the_ban || 0;
  });

  var html =
    '<div style="display:flex;gap:7px;margin-bottom:10px">' +
    mvO('Sản xuất', tongSx, '#374151') + mvO('Đã nhận', tongDat, '#b45309') +
    mvO('Còn bán', tongCon, tongCon < 0 ? '#b3261e' : '#0a8a4a') +
    '</div>' +
    '<div id="mvMoc" style="font-size:11.5px;color:#98a2b3;padding:0 2px 10px;line-height:1.6">' +
    mvChuMoc(d) + '</div>' +
    '<div style="display:flex;gap:7px;margin-bottom:10px">' +
    [['sp', 'Sản phẩm'], ['lich', 'Lịch tháng'], ['dot', 'Đợt hàng'], ['dm', 'Định mức']].map(function (x) {
      var on = MV.xem === x[0];
      return '<button data-mvx="' + x[0] + '" style="flex:1;border:1.5px solid ' + (on ? '#0f766e' : '#e5e7eb') +
        ';background:' + (on ? '#ccfbf1' : '#fff') + ';color:' + (on ? '#0f766e' : '#374151') +
        ';border-radius:9px;padding:8px 4px;font-size:12px;font-weight:' + (on ? '800' : '600') + '">' +
        h(x[1]) + '</button>';
    }).join('') + '</div>';

  html += MV.xem === 'sp' ? mvVeSanPham(ds)
    : MV.xem === 'lich' ? mvVeLuoi(d, ds)
    : MV.xem === 'dot' ? mvVeDot(d)
    : mvVeDinhMuc(d);

  var nutChinh = MV.xem === 'dot'
    ? '<button class="btn gh" id="mvThemDot" style="margin:0;flex:0 0 46%">➕ Khai đợt hàng</button>'
    : MV.xem === 'dm'
      ? '<button class="btn gh" id="mvThemDm" style="margin:0;flex:0 0 46%">➕ Khai định mức</button>'
      : '<button class="btn gh" id="mvThem" style="margin:0;flex:0 0 46%">➕ Thêm sản phẩm</button>';
  var b = frame('Kiểm bánh theo mùa', html, {
    footer: '<div style="display:flex;gap:8px">' + nutChinh +
      '<button class="btn" id="mvSoat" style="margin:0;flex:1">🔄 Đồng bộ Pancake</button></div>'
  });

  b.querySelectorAll('[data-mvx]').forEach(function (n) {
    n.onclick = function () { MV.xem = n.getAttribute('data-mvx'); mvVe(); };
  });
  mvGanNutSx(b);
  b.querySelectorAll('[data-mvloc]').forEach(function (n) {
    n.onclick = function () { MV.loc = n.getAttribute('data-mvloc'); mvVe(); };
  });
  /* Gõ tìm chỉ vẽ lại ĐÚNG khối danh sách, không vẽ lại cả màn: vẽ lại cả
     màn thì ô nhập bị dựng mới và con trỏ nhảy ra ngoài sau mỗi ký tự. */
  var oT = document.getElementById('mvTim');
  if (oT) {
    oT.oninput = function () {
      MV.tim = oT.value || '';
      var kh = document.getElementById('mvDsSp');
      if (!kh) return;
      kh.innerHTML = mvDsSpHtml(ds);
      mvGanNutSx(kh);
    };
  }
  b.querySelectorAll('[data-mvng]').forEach(function (n) {
    n.onclick = function () { mvXemNgay(n.getAttribute('data-mvng')); };
  });
  var nT = document.getElementById('mvThem');
  if (nT) nT.onclick = mvThemSp;
  var nD = document.getElementById('mvThemDot');
  if (nD) nD.onclick = mvKhaiDot;
  var nM = document.getElementById('mvThemDm');
  if (nM) nM.onclick = mvKhaiDinhMuc;
  b.querySelectorAll('[data-mvdotve]').forEach(function (n) {
    n.onclick = function () { mvDotVe(+n.getAttribute('data-mvdotve'), n.getAttribute('data-ve') === '1' ? 0 : 1); };
  });
  b.querySelectorAll('[data-mvdotxoa]').forEach(function (n) {
    n.onclick = function () { mvXoaDot(+n.getAttribute('data-mvdotxoa')); };
  });
  b.querySelectorAll('[data-mvdmxoa]').forEach(function (n) {
    n.onclick = function () { mvXoaDm(n.getAttribute('data-hop'), n.getAttribute('data-banh')); };
  });
  document.getElementById('mvSoat').onclick = mvSoatTay;
}

/* Dòng mốc tách riêng ra hàm vì hai nơi dùng: lần vẽ đầu, và nhịp tự làm
   mới khi số không đổi. Nhịp mà không đụng vào dòng này thì giờ đồng bộ
   đứng yên hàng chục phút, và người nhìn sẽ tưởng hệ chết. */
function mvChuMoc(d) {
  return h(d.ten_mua) + ' · ' + mvNgay(d.tu_ngay) + ' đến ' + mvNgay(d.den_ngay) +
    (d.dong_bo_luc ? ' · đồng bộ ' + h(String(d.dong_bo_luc).slice(11, 16)) : '');
}

function mvGanNutSx(root) {
  root.querySelectorAll('[data-mvsx]').forEach(function (n) {
    n.onclick = function () { mvSuaSx(n.getAttribute('data-mvsx')); };
  });
}

function mvO(nhan, so, mau) {
  return '<div style="flex:1;background:#fff;border:1px solid #e5e7eb;border-radius:11px;padding:9px 10px;text-align:center">' +
    '<div style="font-size:11px;color:#9ca3af">' + h(nhan) + '</div>' +
    '<b style="font-size:17px;color:' + mau + '">' + money(so) + '</b></div>';
}

/* ---------- Chip lọc và ô tìm nhanh (anh Việt 18/08/2026) ----------

Mùa trung thu này bảng đã 19 dòng và còn dài thêm mỗi lần thêm món. Cuộn hết
bảng để tìm một mã, giữa lúc đang có khách trên điện thoại, là chậm.

Bốn chip em chọn đúng bốn câu sales hỏi bảng này, xếp theo mức gấp:
  BÁN LỐ trước nhất  - đã có đơn không giao được, phải gọi khách NGAY
  SẮP HẾT            - còn dưới 10 phần trăm, cần chốt đợt hàng mới
  CÒN BÁN            - danh sách để chào khách
  THEO HỘP           - bánh chỉ làm theo hộp, xem để bếp biết phải làm bao nhiêu

Chip nào không có mã nào thì ẩn hẳn, để hàng chip không bao giờ dài quá màn. */
var MV_NGUONG_SAP_HET = 10;   /* phần trăm, khớp NGUONG_CANH_BAO bên mua_vu.py */

function mvNhomCua(x) {
  if (x.khong_tran) return 'hop';
  var con = x.co_the_ban || 0;
  if (con < 0) return 'lo';
  var sx = x.san_xuat || 0;
  if (sx > 0 && (con * 100 / sx) < MV_NGUONG_SAP_HET) return 'het';
  if (sx <= 0 && con <= 0) return 'het';
  return 'con';
}

/* Bán lố lên đầu, rồi sắp hết, rồi còn bán, cuối cùng là bánh theo hộp.
   Trong cùng nhóm thì mã ít còn lại nhất lên trước. Trước 18/08 bảng xếp
   theo thứ tự dòng trong cơ sở dữ liệu, tức là không theo thứ tự nào cả. */
var MV_THU_TU = { lo: 0, het: 1, con: 2, hop: 3 };

function mvSapXep(ds) {
  return (ds || []).slice().sort(function (a, b) {
    var ta = MV_THU_TU[mvNhomCua(a)], tb = MV_THU_TU[mvNhomCua(b)];
    if (ta !== tb) return ta - tb;
    return (a.co_the_ban || 0) - (b.co_the_ban || 0);
  });
}

/* Bỏ dấu tiếng Việt trước khi so khớp. Trên điện thoại, giữa lúc đang nói
   chuyện với khách, gần như không ai gõ đủ dấu: gõ "dua" phải ra "Dứa Bưởi"
   và "Dừa Sáp". Bắt được lúc nghiệm thu v211, khi gõ "dua" thì màn trả về
   không có mã nào khớp trong khi mùa có hai món dứa dừa. */
function mvKhongDau(s) {
  s = String(s || '').toLowerCase();
  try { s = s.normalize('NFD').replace(/[\u0300-\u036f]/g, ''); } catch (e) { }
  return s.replace(/đ/g, 'd');
}

function mvKhop(x, q) {
  if (!q) return true;
  q = mvKhongDau(q).trim();
  if (!q) return true;
  return mvKhongDau((x.ten_banh || '') + ' ' + (x.ma_hang || '') + ' ' + (x.nhan_ngan || ''))
    .indexOf(q) >= 0;
}

function mvLocDs(ds) {
  var r = mvSapXep(ds).filter(function (x) { return mvKhop(x, MV.tim); });
  if (MV.loc !== 'all') r = r.filter(function (x) { return mvNhomCua(x) === MV.loc; });
  return r;
}

function mvVeSanPham(ds) {
  if (!ds.length) {
    return '<div class="emp"><div class="e1">📦</div><div>Chưa có sản phẩm nào trong mùa.</div>' +
      '<div style="font-size:12px;color:#9ca3af;margin-top:6px">Bấm Thêm sản phẩm để đặt số lượng sản xuất, ' +
      'hoặc bấm Đồng bộ để máy tự kéo về từ đơn Pancake.</div></div>';
  }
  var dem = { all: ds.length, lo: 0, het: 0, con: 0, hop: 0 };
  ds.forEach(function (x) { dem[mvNhomCua(x)]++; });
  var CHIP = [
    ['all', 'Tất cả', '#101828'],
    ['lo', 'Bán lố', '#b3261e'],
    ['het', 'Sắp hết', '#b45309'],
    ['con', 'Còn bán', '#0a8a4a'],
    ['hop', 'Theo hộp', '#7c3aed']
  ];
  return '<div style="display:flex;gap:6px;overflow-x:auto;padding:0 2px 9px">' +
    CHIP.map(function (c) {
      if (!dem[c[0]] && c[0] !== 'all') return '';
      var on = MV.loc === c[0];
      return '<button data-mvloc="' + c[0] + '" style="flex:0 0 auto;border:1.5px solid ' +
        (on ? c[2] : '#e5e7eb') + ';background:' + (on ? c[2] : '#fff') + ';color:' +
        (on ? '#fff' : c[2]) + ';border-radius:999px;padding:6px 13px;font-size:12px;font-weight:800">' +
        h(c[1]) + ' ' + dem[c[0]] + '</button>';
    }).join('') + '</div>' +
    '<div style="padding:0 2px 10px">' +
    '<input id="mvTim" placeholder="Tìm theo tên bánh, mã hàng hoặc nhãn" value="' + h(MV.tim) +
    '" style="width:100%;box-sizing:border-box;border:1px solid #d0d5dd;border-radius:10px;' +
    'padding:11px 12px;font-size:15px;background:#fff;color:#101828"></div>' +
    '<div id="mvDsSp">' + mvDsSpHtml(ds) + '</div>';
}

function mvDsSpHtml(ds) {
  var loc = mvLocDs(ds);
  if (!loc.length) {
    return '<div class="emp"><div class="e1">🔍</div><div>Không có mã nào khớp.</div>' +
      '<div style="font-size:12px;color:#9ca3af;margin-top:6px">Bỏ bớt điều kiện lọc hoặc xoá ô tìm.</div></div>';
  }
  return '<div class="card">' + loc.map(function (x) {
    var con = x.co_the_ban || 0;
    /* Bánh chỉ làm theo hộp thì không có trần riêng, nên không có chuyện
       "bán lố": trần thật của nó nằm ở dòng cái hộp. */
    var theoHop = !!x.khong_tran;
    var mau = theoHop ? '#7c3aed' : (con < 0 ? '#b3261e' : (con === 0 ? '#b45309' : '#0a8a4a'));
    /* Hết hàng và bán lố là hai chuyện khác nhau, phải nhìn ra ngay: bán lố
       nghĩa là đã có đơn không giao được, sales phải gọi khách ngay hôm nay. */
    var nhan = theoHop ? 'theo hộp'
      : (con < 0 ? 'BÁN LỐ ' + money(-con) : (con === 0 ? 'HẾT' : 'còn ' + money(con)));
    /* Hai chip anh Việt chốt 18/08/2026: bán lẻ bao nhiêu, theo hộp bao
       nhiêu. Cùng một mã bánh đi ra bằng hai đường và hai đường đó phải
       tách bạch, vì bếp làm theo tổng còn sales bán theo từng đường. */
    var banLe = (x.da_dat || 0) + (x.cho_chot || 0) + (x.don_khac || 0);
    return '<div style="padding:12px 14px;border-bottom:1px solid #f2f4f7">' +
      '<div style="display:flex;gap:10px;align-items:center">' +
      (x.hinh ? '<div style="width:44px;height:44px;flex:none;border-radius:9px;background-image:url(' + x.hinh +
        ');background-size:cover;background-position:center;border:1px solid #e3e6ec"></div>' : '') +
      '<div style="flex:1;min-width:0">' +
      '<b style="font-size:13.5px">' + h(x.ten_banh || x.ma_hang) + '</b>' +
      '<div style="font-size:11px;color:#98a2b3">' + h(x.ma_hang) +
      (x.nhan_ngan ? ' · lịch ghi <b>' + h(x.nhan_ngan) + '</b>' : '') +
      (x.tran_ngay ? ' · trần ' + money(x.tran_ngay) + '/ngày' : '') + '</div></div>' +
      '<div style="text-align:right"><b style="font-size:15px;color:' + mau + '">' + h(nhan) + '</b>' +
      '<div style="font-size:11px;color:#9ca3af">' +
      (theoHop ? 'không đặt trần' : 'trên ' + money(x.san_xuat)) + '</div></div></div>' +
      '<div style="display:flex;gap:6px;margin-top:8px;font-size:11.5px;flex-wrap:wrap;align-items:center">' +
      mvChip('Bán lẻ', banLe, '#0f766e') +
      /* Banh le bi hop an di. Chip nay quan trong hon ve ngoai cua no: truoc
         18/08 hai thu dem doc lap, nen ban 2000 hop van thay banh le "con
         192" trong khi lo banh do da vao het trong hop. */
      mvChip('Theo hộp', x.trong_hop, '#7c3aed') +
      (banLe || x.trong_hop
        ? '<span style="color:#aeb4bf;font-size:11px">tổng ' + money(banLe + (x.trong_hop || 0)) + '</span>'
        : '<span style="color:#aeb4bf;font-size:11px">chưa có đơn nào</span>') +
      '<button data-mvsx="' + h(x.ma_hang) + '" style="margin-left:auto;border:1.5px solid #0f766e;' +
      'background:#fff;color:#0f766e;border-radius:8px;padding:5px 11px;font-size:11.5px;font-weight:800">' +
      '✏️ Sản xuất ' + money(x.san_xuat) + '</button></div>' +
      (banLe ? '<div style="font-size:11px;color:#98a2b3;margin-top:6px">Bán lẻ gồm: đã đặt ' +
        money(x.da_dat) + ' · chờ chốt ' + money(x.cho_chot) + ' · kênh khác ' + money(x.don_khac) +
        '</div>' : '') +
      (x.ten_khach_cho ? '<div style="font-size:11px;color:#b45309;margin-top:6px">Đang chờ chốt: ' +
        h(String(x.ten_khach_cho).slice(0, 120)) + '</div>' : '') +
      '</div>';
  }).join('') + '</div>';
}

function mvChip(nhan, so, mau) {
  if (!so) return '';
  return '<span style="background:#f5f6f8;border-radius:999px;padding:4px 9px;color:' + mau + ';font-weight:700">' +
    h(nhan) + ' ' + money(so) + '</span>';
}

/* Lịch theo ngày: anh Việt yêu cầu "tạo bảng các ngày trong tháng thể hiện
   những ngày nào có khách đã đặt bao nhiêu hộp". Chỉ hiện ngày CÓ đơn - một
   mùa dài ba tháng mà kê đủ 90 dòng thì cuộn mãi không thấy ngày cao điểm. */
function mvVeLich(d, ds) {
  var lich = d.lich || { ngay: [], o: {} };
  if (!lich.ngay.length) {
    return '<div class="emp"><div class="e1">📅</div><div>Chưa có đơn nào trong mùa.</div>' +
      '<div style="font-size:12px;color:#9ca3af;margin-top:6px">Bấm Đồng bộ Pancake để kéo đơn về.</div></div>';
  }
  var ten = {};
  ds.forEach(function (x) { ten[x.ma_hang] = x.ten_banh || x.ma_hang; });

  return '<div class="card">' + lich.ngay.map(function (ng) {
    var o = lich.o[ng] || {};
    var tong = 0;
    Object.keys(o).forEach(function (m) { tong += (o[m].chot || 0) + (o[m].cho || 0); });
    var dong = Object.keys(o).sort().map(function (m) {
      var v = o[m];
      return '<div style="display:flex;gap:8px;font-size:11.5px;padding:3px 0">' +
        '<div style="flex:1;min-width:0;color:#374151">' + h(String(ten[m] || m).slice(0, 42)) + '</div>' +
        '<b style="color:#0f766e">' + money(v.chot || 0) + '</b>' +
        (v.cho ? '<span style="color:#b45309">+' + money(v.cho) + ' chờ</span>' : '') + '</div>';
    }).join('');
    return '<div style="padding:11px 14px;border-bottom:1px solid #f2f4f7">' +
      '<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">' +
      '<b style="font-size:13px">' + h(mvNgayDay(ng)) + '</b>' +
      '<b style="margin-left:auto;font-size:14px;color:#0f172a">' + money(tong) + '</b></div>' +
      dong + '</div>';
  }).join('') + '</div>';
}

function mvNgayDay(s) {
  var p = String(s).split('-');
  if (p.length !== 3) return String(s);
  var thu = ['Chủ nhật', 'Thứ hai', 'Thứ ba', 'Thứ tư', 'Thứ năm', 'Thứ sáu', 'Thứ bảy'];
  var dt = new Date(s + 'T00:00:00');
  return thu[dt.getDay()] + ' ' + p[2] + '/' + p[1];
}

async function mvLuuO(ma, truong, gia_tri) {
  busy(true);
  try {
    await api('vagabond.mua_vu.luu_o', { mua: MV.mua, ma_hang: ma, truong: truong, gia_tri: gia_tri });
    MV.data = await api('vagabond.mua_vu.bang', { mua: MV.mua });
    busy(false); mvVe();
  } catch (e) { busy(false); baoTin((e && e.message) || 'Lưu lỗi', 'Không lưu được'); }
}

/* Ba ô cùng nói về một dòng nên gom vào một bảng chọn, thay vì rải ba nút
   trên một hàng đã chật. Ô Sản xuất vẫn là ô hay dùng nhất nên đứng đầu. */
async function mvSuaSx(ma) {
  var x = null;
  (MV.data.dong || []).forEach(function (r) { if (r.ma_hang === ma) x = r; });
  if (!x) return;
  var ten = String(x.ten_banh || ma).slice(0, 40);
  sheet('Cài đặt cho "' + ten + '"', [
    { value: 'san_xuat', label: 'Số lượng sản xuất cả mùa', phu: 'đang là ' + money(x.san_xuat || 0) },
    { value: 'tran_ngay', label: 'Trần mỗi ngày', phu: x.tran_ngay ? 'đang là ' + money(x.tran_ngay) + '/ngày' : 'chưa đặt, lịch tháng không cảnh báo' },
    { value: 'nhan_ngan', label: 'Nhãn ngắn hiện trong ô lịch', phu: x.nhan_ngan ? 'đang là ' + x.nhan_ngan : 'máy tự đặt' },
    {
      value: 'khong_tran', label: x.khong_tran ? 'Bỏ đánh dấu "chỉ làm theo hộp"' : 'Đánh dấu "chỉ làm theo hộp"',
      phu: x.khong_tran ? 'bật lại chốt chặn bán lố cho mã này' : 'không đặt trần riêng, không chặn bán lố, không lên chip cảnh báo'
    }
  ], '', async function (it) {
    if (it.value === 'khong_tran') return mvLuuO(ma, 'khong_tran', x.khong_tran ? 0 : 1);
    if (it.value === 'nhan_ngan') {
      var n = await hoiNhap('Nhãn ngắn hiện trong ô lịch tháng (tối đa 6 chữ)', String(x.nhan_ngan || ''));
      if (n === null) return;
      return mvLuuO(ma, 'nhan_ngan', String(n).trim());
    }
    var nhan = it.value === 'san_xuat'
      ? 'Số lượng sản xuất cả mùa cho "' + ten + '"'
      : 'Bếp làm được tối đa bao nhiêu "' + ten + '" trong MỘT ngày (0 là không theo dõi)';
    var v = await hoiNhap(nhan, String(it.value === 'san_xuat' ? (x.san_xuat || 0) : (x.tran_ngay || 0)));
    if (v === null) return;
    var so = Number(String(v).replace(/[^0-9]/g, ''));
    if (isNaN(so)) return toast('Nhập một con số giúp em.', 3500);
    mvLuuO(ma, it.value, so);
  });
}

async function mvThemSp() {
  busy(true);
  var kq;
  try { kq = await api('vagabond.mua_vu.tim_san_pham', { mua: MV.mua }); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Không đọc được danh mục', 'Lỗi'); }
  busy(false);
  var ds = (kq && kq.ds) || [];
  if (!ds.length) return baoTin('Chưa có sản phẩm mùa vụ nào trong danh mục.', 'Chưa có dữ liệu');
  sheet('Thêm sản phẩm vào mùa',
    ds.map(function (x) {
      return { value: x.ma, label: x.ten, phu: x.ma + (x.da_co ? ' · đã có trong mùa' : ''), tim: x.ma };
    }), '', async function (it) {
      busy(true);
      try {
        MV.data = await api('vagabond.mua_vu.them_dong', { mua: MV.mua, ma_hang: it.value });
        busy(false); mvVe();
        toast('Đã thêm. Bấm nút Sản xuất để đặt số lượng.', 4000);
      } catch (e) { busy(false); baoTin((e && e.message) || 'Thêm lỗi', 'Không thêm được'); }
    }, true);
}


/* ---------- Lịch dạng lưới tháng (anh Việt chốt 18/08/2026) ----------

Vì sao đổi từ danh sách sang lưới: anh nói "Sales sẽ biết được ngày nào ít
đơn để mà dồn khách vào nhận ngày đó". Danh sách cho biết ngày nào có bao
nhiêu, nhưng không cho thấy CHỖ TRỐNG - mà chỗ trống mới là thứ sales cần
tìm khi đang nói chuyện với khách.

Nền ô đậm dần theo số lượng, nên ngày cao điểm nổi lên còn ngày trống nhạt
hẳn ra. Ngày quá khứ làm mờ: dồn khách vào một ngày đã qua thì vô nghĩa. */
function mvVeLuoi(d, ds) {
  var L = d.lich || { ngay: [], o: {}, muc: {}, tai: {}, tran: {} };
  var tong = {}, mon = {};
  /* Anh Việt 18/08/2026: "Lịch tháng thì hiện phải click vào mới ra chi tiết.
     Em cho hiện sản phẩm + số lượng của ngày đó luôn trong ô". Ô lịch trên
     điện thoại rộng chừng 48 điểm ảnh nên phải dùng nhãn ngắn, và bảng chú
     giải nằm ngay dưới lưới để không ai phải đoán. */
  var nhanCua = {}, tenCua = {};
  (ds || []).forEach(function (x) {
    nhanCua[x.ma_hang] = x.nhan_ngan || String(x.ma_hang || '').slice(-3);
    tenCua[x.ma_hang] = x.ten_banh || x.ma_hang;
  });
  L.ngay.forEach(function (ng) {
    var o = L.o[ng] || {}, t = 0, ms = [];
    Object.keys(o).forEach(function (m) {
      var s = (o[m].chot || 0) + (o[m].cho || 0);
      t += s;
      if (s > 0) ms.push([m, s]);
    });
    ms.sort(function (p, q) { return q[1] - p[1]; });
    tong[ng] = t; mon[ng] = ms;
  });
  var max = 0;
  Object.keys(tong).forEach(function (k) { if (tong[k] > max) max = tong[k]; });

  var a = d.tu_ngay, b = d.den_ngay;
  if (!a || !b) return '<div class="emp"><div class="e2">Mùa chưa khai ngày.</div></div>';
  var thang = [], cur = a.slice(0, 7);
  var stop = b.slice(0, 7), dem = 0;
  while (dem++ < 24) {
    thang.push(cur);
    if (cur === stop) break;
    var y = +cur.slice(0, 4), m = +cur.slice(5, 7) + 1;
    if (m > 12) { m = 1; y++; }
    cur = y + '-' + (m < 10 ? '0' : '') + m;
  }
  var homNay = new Date().toISOString().slice(0, 10);

  /* Ngày gần đầy phải nói thành lời chứ không chỉ tô màu: "để biết đường
     dồn khách sang ngày khác để không bị quá tải" (anh Việt 18/08/2026). */
  var tranTen = Object.keys(L.tran || {}).map(function (m) {
    return (tenCua[m] || m) + ' ' + money(L.tran[m]) + '/ngày';
  }).join(', ');
  var ngayDo = [], ngayVang = [];
  Object.keys(L.muc || {}).sort().forEach(function (ng) {
    if (L.muc[ng] === 2) ngayDo.push(ng); else if (L.muc[ng] === 1) ngayVang.push(ng);
  });
  var canhBao = '';
  if (ngayDo.length || ngayVang.length) {
    canhBao = '<div style="background:' + (ngayDo.length ? '#fef2f2' : '#fffbeb') +
      ';border:1px solid ' + (ngayDo.length ? '#fecaca' : '#fde68a') +
      ';border-radius:11px;padding:10px 12px;margin-bottom:9px;font-size:12px;line-height:1.65;color:#374151">' +
      (ngayDo.length ? '<b style="color:#b3261e">Đã đầy hoặc quá tải: ' +
        ngayDo.map(function (x) { return mvNgay(x); }).join(', ') + '</b><br>' : '') +
      (ngayVang.length ? '<b style="color:#b45309">Gần đầy: ' +
        ngayVang.map(function (x) { return mvNgay(x); }).join(', ') + '</b><br>' : '') +
      'Dồn khách sang ngày nhạt màu để bếp không quá tải.</div>';
  }

  var html = canhBao + '<div style="font-size:11.5px;color:#98a2b3;padding:0 2px 8px;line-height:1.6">' +
    'Trong ô là <b>nhãn sản phẩm và số lượng</b> của ngày đó. Bấm vào ô để xem tên khách. ' +
    'Ngày nhạt là ngày còn trống, dồn khách vào đó được.' +
    (tranTen ? '<br>Trần mỗi ngày: <b>' + h(tranTen) + '</b>. Ô vàng là đã tới ' +
      Math.round((L.ty_le_vang || 0.75) * 100) + ' phần trăm trần, ô đỏ là đã chạm trần.' : '') +
    '</div>';

  thang.forEach(function (th) {
    var y = +th.slice(0, 4), mo = +th.slice(5, 7);
    var dauThang = new Date(y, mo - 1, 1);
    var soNgay = new Date(y, mo, 0).getDate();
    /* Tuần bắt đầu từ thứ hai, đúng cách người Việt đọc lịch. */
    var lech = (dauThang.getDay() + 6) % 7;
    var o = '';
    for (var i = 0; i < lech; i++) o += '<div></div>';
    for (var dd = 1; dd <= soNgay; dd++) {
      var iso = y + '-' + (mo < 10 ? '0' : '') + mo + '-' + (dd < 10 ? '0' : '') + dd;
      var t = tong[iso] || 0;
      var qua = iso < homNay;
      var muc = (L.muc || {})[iso] || 0;
      var dam = max > 0 ? Math.min(1, t / max) : 0;
      /* Ba thang màu, không trộn vào nhau: đỏ là chạm trần bếp, vàng là gần
         chạm, xanh là mật độ đơn thường. Trần bếp quan trọng hơn mật độ nên
         nó đè lên. */
      var nen = muc === 2 ? '#fde3e1' : muc === 1 ? '#fdf0d5'
        : (t > 0 ? 'rgba(15,118,110,' + (0.10 + dam * 0.62).toFixed(2) + ')' : '#fafbfc');
      var vien = muc === 2 ? '#f0a9a3' : muc === 1 ? '#efd08a' : (t > 0 ? 'transparent' : '#eef0f3');
      var chu = muc === 2 ? '#8f1d16' : muc === 1 ? '#8a5a09'
        : (t > 0 && dam > 0.62 ? '#fff' : (t > 0 ? '#0f766e' : '#c9ced8'));
      var ngoai = (iso >= (d.tu_ngay || '') && iso <= (d.den_ngay || ''));
      var ms = mon[iso] || [];
      var dongMon = ms.slice(0, 3).map(function (p) {
        return '<div style="font-size:8.5px;line-height:1.35;white-space:nowrap;overflow:hidden;' +
          'text-overflow:ellipsis;max-width:100%">' + h(nhanCua[p[0]] || p[0]) +
          ' <b>' + p[1] + '</b></div>';
      }).join('') + (ms.length > 3 ? '<div style="font-size:8px;opacity:.7">+' + (ms.length - 3) + ' món</div>' : '');
      o += '<div ' + (t ? 'data-mvng="' + iso + '"' : '') + ' style="min-height:58px;border-radius:8px;' +
        'padding:3px 2px;background:' + (ngoai ? nen : '#f4f5f7') + ';border:1px solid ' + vien +
        ';display:flex;flex-direction:column;align-items:center;justify-content:flex-start;overflow:hidden;' +
        'color:' + chu + ';' + (qua ? 'opacity:.42;' : '') + (t ? 'cursor:pointer;' : '') + '">' +
        '<div style="font-size:10px;line-height:1.1;font-weight:' + (t ? '800' : '500') + '">' + dd +
        (t ? ' · ' + t : '') + '</div>' + dongMon +
        '</div>';
    }
    html += '<div class="sec">' + mvTenThang(mo) + ' ' + y + '</div>' +
      '<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:4px;margin-bottom:4px">' +
      ['H', 'B', 'T', 'N', 'S', 'B', 'C'].map(function (x) {
        return '<div style="text-align:center;font-size:10px;color:#aeb4bf;font-weight:700">' + x + '</div>';
      }).join('') + '</div>' +
      '<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:4px">' + o + '</div>';
  });

  /* Chú giải chỉ liệt kê nhãn THẬT SỰ xuất hiện trong lưới. Kê đủ cả mùa
     thì dài hơn cái lưới nó chú giải. */
  var daHien = {};
  L.ngay.forEach(function (ng) {
    (mon[ng] || []).slice(0, 3).forEach(function (p) { daHien[p[0]] = 1; });
  });
  var cg = Object.keys(daHien).map(function (m) {
    return '<span style="background:#f5f6f8;border-radius:999px;padding:3px 9px;color:#475467">' +
      '<b>' + h(nhanCua[m] || m) + '</b> ' + h(tenCua[m] || m) + '</span>';
  }).join('');
  if (cg) {
    html += '<div class="sec">Nhãn trong ô</div>' +
      '<div style="display:flex;gap:5px;flex-wrap:wrap;font-size:10.5px;line-height:1.7;padding:0 2px">' +
      cg + '</div>';
  }
  return html;
}

function mvTenThang(m) {
  return ['Tháng một', 'Tháng hai', 'Tháng ba', 'Tháng tư', 'Tháng năm', 'Tháng sáu',
    'Tháng bảy', 'Tháng tám', 'Tháng chín', 'Tháng mười', 'Tháng mười một', 'Tháng mười hai'][m - 1] || ('Tháng ' + m);
}

function mvXemNgay(iso) {
  var d = MV.data, L = d.lich || { o: {} }, o = L.o[iso] || {};
  var ten = {};
  (d.dong || []).forEach(function (x) { ten[x.ma_hang] = x.ten_banh || x.ma_hang; });
  var dong = Object.keys(o).sort().map(function (m) {
    var v = o[m];
    return '<div style="display:flex;gap:8px;padding:7px 0;border-bottom:1px solid #f2f4f7;font-size:13px">' +
      '<div style="flex:1;min-width:0">' + h(String(ten[m] || m)) + '</div>' +
      '<b style="color:#0f766e">' + money(v.chot || 0) + '</b>' +
      (v.cho ? '<span style="color:#b45309">+' + money(v.cho) + ' chờ</span>' : '') + '</div>';
  }).join('');
  var khach = Object.keys(o).map(function (m) { return o[m].khach || ''; }).filter(Boolean).join(', ');
  var hop = hopKhung(mvNgayDay(iso), dong +
    (khach ? '<div style="font-size:11.5px;color:#6b7280;margin-top:10px;line-height:1.6">Khách: ' +
      h(khach.slice(0, 260)) + '</div>' : ''));
  hop.box.querySelector('.x').onclick = hop.dong;
}

/* ---------- Đợt hàng nhà in (anh Việt chốt 18/08/2026) ----------

Hạn mức thật là TỔNG CÁC ĐỢT ĐÃ VỀ, không phải một con số gõ tay. Đợt hẹn
ngày mai thì số hộp đó chưa có trong tay: cộng trước là bán trên một con số
chưa tồn tại, và tới ngày nhà in giao thiếu thì hộp đã vào tay khách hết. */
function mvVeDot(d) {
  var ds = d.dot || [];
  var html = '<div style="font-size:11.5px;color:#98a2b3;padding:0 2px 10px;line-height:1.6">' +
    'Hạn mức bán được tính bằng <b>tổng các đợt đã về</b>. Đợt chưa về không cộng vào, ' +
    'nên hàng chưa tới kho thì chưa bán ra được.</div>';
  if (!ds.length) {
    return html + '<div class="emp"><div class="e1">🚚</div><div>Chưa khai đợt nào.</div>' +
      '<div style="font-size:12px;color:#9ca3af;margin-top:6px">Chưa khai đợt thì máy dùng số ở ô ' +
      'Sản xuất như cũ. Khai đợt đầu tiên là máy chuyển sang tính theo đợt.</div></div>';
  }
  var gop = {};
  ds.forEach(function (x, i) { (gop[x.ma_hang] = gop[x.ma_hang] || []).push([x, i]); });
  html += Object.keys(gop).map(function (ma) {
    var cac = gop[ma], ve = 0, cho = 0;
    cac.forEach(function (p) { if (p[0].da_ve) ve += p[0].so_luong || 0; else cho += p[0].so_luong || 0; });
    return '<div class="sec">' + h(String(cac[0][0].ten_banh || ma)) + '</div><div class="card">' +
      '<div style="padding:9px 14px;background:#f8fafb;font-size:12px;color:#374151">' +
      'Đã về <b style="color:#0a8a4a">' + money(ve) + '</b>' +
      (cho ? ' · đang chờ <b style="color:#b45309">' + money(cho) + '</b>' : '') +
      ' · hạn mức bán được là <b>' + money(ve) + '</b></div>' +
      cac.map(function (p) {
        var x = p[0], i = p[1];
        return '<div style="padding:11px 14px;border-top:1px solid #f2f4f7;display:flex;align-items:center;gap:9px">' +
          '<div style="flex:1;min-width:0">' +
          '<b style="font-size:14px">' + money(x.so_luong) + ' cái</b>' +
          '<div style="font-size:11.5px;color:#98a2b3">' +
          (x.da_ve ? 'đã về' + (x.ngay_ve_that ? ' ' + mvNgay(x.ngay_ve_that) : '')
            : 'hẹn ' + (x.ngay_du_kien ? mvNgay(x.ngay_du_kien) : 'chưa rõ ngày')) +
          (x.ghi_chu ? ' · ' + h(x.ghi_chu) : '') + '</div></div>' +
          '<button data-mvdotve="' + i + '" data-ve="' + (x.da_ve ? '1' : '0') + '" ' +
          'style="border:1.5px solid ' + (x.da_ve ? '#0a8a4a' : '#d1d5db') + ';background:' +
          (x.da_ve ? '#dcfce7' : '#fff') + ';color:' + (x.da_ve ? '#0a8a4a' : '#374151') +
          ';border-radius:8px;padding:6px 11px;font-size:11.5px;font-weight:800">' +
          (x.da_ve ? '✓ Đã về' : 'Đánh dấu về') + '</button>' +
          (x.da_ve ? '' : '<span data-mvdotxoa="' + i + '" style="color:#b3261e;font-size:17px;cursor:pointer;padding:0 3px">&times;</span>') +
          '</div>';
      }).join('') + '</div>';
  }).join('');
  return html;
}

async function mvKhaiDot() {
  var ds = (MV.data.dong || []);
  if (!ds.length) return baoTin('Chưa có sản phẩm nào trong mùa. Bấm Thêm sản phẩm trước.', 'Chưa có gì để khai');
  sheet('Khai đợt cho sản phẩm nào',
    ds.map(function (x) { return { value: x.ma_hang, label: x.ten_banh || x.ma_hang, phu: x.ma_hang, tim: x.ma_hang }; }),
    '', async function (it) {
      var sl = await hoiNhap('Số lượng đợt này của "' + String(it.label).slice(0, 34) + '"', '');
      if (sl === null) return;
      var so = Number(String(sl).replace(/[^0-9]/g, ''));
      if (!so) return toast('Nhập số lượng lớn hơn 0 giúp em.', 3500);
      var ng = await hoiNhap('Ngày dự kiến hàng về (YYYY-MM-DD), để trống nếu chưa rõ', '');
      if (ng === null) return;
      var gc = await hoiNhap('Ghi chú (không bắt buộc)', '');
      if (gc === null) return;
      busy(true);
      try {
        MV.data = await api('vagabond.mua_vu.them_dot',
          { mua: MV.mua, ma_hang: it.value, so_luong: so, ngay_du_kien: ng, ghi_chu: gc });
        busy(false); MV.xem = 'dot'; mvVe();
        toast('Đã khai đợt. Bấm Đánh dấu về khi hàng tới kho thì hạn mức mới nhích lên.', 5000);
      } catch (e) { busy(false); baoTin((e && e.message) || 'Khai đợt lỗi', 'Không khai được'); }
    }, true);
}

async function mvDotVe(i, ve) {
  if (ve) {
    var ok = await confirmSheet('Đánh dấu hàng đã về?',
      'Hạn mức bán được sẽ tăng thêm đúng số của đợt này, và sales bán tiếp được ngay.', 'Hàng đã về');
    if (!ok) return;
  }
  busy(true);
  try {
    MV.data = await api('vagabond.mua_vu.danh_dau_dot_ve', { mua: MV.mua, chi_so: i, da_ve: ve });
    busy(false); mvVe();
  } catch (e) { busy(false); baoTin((e && e.message) || 'Lưu lỗi', 'Không lưu được'); }
}

async function mvXoaDot(i) {
  var ok = await confirmSheet('Bỏ đợt này?', 'Đợt chưa về nên bỏ đi không ảnh hưởng số đang bán.', 'Bỏ đợt', true);
  if (!ok) return;
  busy(true);
  try {
    MV.data = await api('vagabond.mua_vu.xoa_dot', { mua: MV.mua, chi_so: i });
    busy(false); mvVe();
  } catch (e) { busy(false); baoTin((e && e.message) || 'Xoá lỗi', 'Không xoá được'); }
}

/* ---------- Định mức hộp và bánh lẻ (anh Việt chốt 18/08/2026) ----------

Bán một hộp MOONGARDEN là lấy đi mấy cái bánh 110g bên trong. Trước 18/08
hai thứ đếm độc lập, nên bán 2000 hộp mà bảng vẫn báo bánh lẻ "còn 192"
trong khi lò bánh đó đã vào hết trong hộp. */
function mvVeDinhMuc(d) {
  var ds = d.dinh_muc || [];
  var html = '<div style="font-size:11.5px;color:#98a2b3;padding:0 2px 10px;line-height:1.6">' +
    'Khai một hộp gồm những bánh lẻ nào. Bán một hộp là máy trừ luôn số bánh lẻ bên trong ' +
    'khỏi hạn mức của bánh đó, nên không bán trùng một lò bánh cho hai chỗ.</div>';
  if (!ds.length) {
    return html + '<div class="emp"><div class="e1">🎁</div><div>Chưa khai định mức nào.</div>' +
      '<div style="font-size:12px;color:#9ca3af;margin-top:6px">Chưa khai thì hộp và bánh lẻ ' +
      'đếm độc lập, và một lò bánh có thể bị bán hai lần.</div></div>';
  }
  var gop = {};
  ds.forEach(function (m) { (gop[m.ma_hop] = gop[m.ma_hop] || []).push(m); });
  html += Object.keys(gop).map(function (hop) {
    var cac = gop[hop];
    var tong = 0;
    cac.forEach(function (m) { tong += m.so_luong || 0; });
    return '<div class="sec">' + h(String(cac[0].ten_hop || hop)) + ' · ' + money(tong) + ' bánh mỗi hộp</div>' +
      '<div class="card">' + cac.map(function (m) {
        return '<div style="padding:11px 14px;border-bottom:1px solid #f2f4f7;display:flex;align-items:center;gap:9px">' +
          '<div style="flex:1;min-width:0"><b style="font-size:13.5px">' + h(String(m.ten_banh || m.ma_banh)) + '</b>' +
          '<div style="font-size:11px;color:#98a2b3">' + h(m.ma_banh) + '</div></div>' +
          '<b style="font-size:15px;color:#7c3aed">' + money(m.so_luong) + '</b>' +
          '<span data-mvdmxoa="1" data-hop="' + h(m.ma_hop) + '" data-banh="' + h(m.ma_banh) + '" ' +
          'style="color:#b3261e;font-size:17px;cursor:pointer;padding:0 3px">&times;</span></div>';
      }).join('') + '</div>';
  }).join('');
  return html;
}

async function mvKhaiDinhMuc() {
  var ds = (MV.data.dong || []);
  if (ds.length < 2) return baoTin('Cần có cả hộp và bánh lẻ trong mùa mới khai được định mức.', 'Chưa đủ sản phẩm');
  var mon = function (x) { return { value: x.ma_hang, label: x.ten_banh || x.ma_hang, phu: x.ma_hang, tim: x.ma_hang }; };
  sheet('Chọn HỘP', ds.map(mon), '', function (hop) {
    sheet('Trong hộp đó có bánh lẻ nào', ds.filter(function (x) { return x.ma_hang !== hop.value; }).map(mon), '',
      async function (banh) {
        var sl = await hoiNhap('Một hộp "' + String(hop.label).slice(0, 26) + '" có mấy cái "' +
          String(banh.label).slice(0, 26) + '"', '');
        if (sl === null) return;
        var so = Number(String(sl).replace(/[^0-9]/g, ''));
        if (!so) return toast('Nhập số lớn hơn 0 giúp em.', 3500);
        busy(true);
        try {
          MV.data = await api('vagabond.mua_vu.them_dinh_muc',
            { mua: MV.mua, ma_hop: hop.value, ma_banh: banh.value, so_luong: so });
          busy(false); MV.xem = 'dm'; mvVe();
        } catch (e) { busy(false); baoTin((e && e.message) || 'Khai lỗi', 'Không khai được'); }
      }, true);
  }, true);
}

async function mvXoaDm(hop, banh) {
  busy(true);
  try {
    MV.data = await api('vagabond.mua_vu.xoa_dinh_muc', { mua: MV.mua, ma_hop: hop, ma_banh: banh });
    busy(false); mvVe();
  } catch (e) { busy(false); baoTin((e && e.message) || 'Xoá lỗi', 'Không xoá được'); }
}


/* ==================== THƯƠNG THẢO VÀ ĐIỀU CHỈNH HỢP ĐỒNG ====================

Loan Anh bên Sales đặt bài, anh Việt chuyển sang 21/08/2026: *"Khách hàng yêu
cầu chỉnh sửa điều khoản hợp đồng sau khi nhận được bản hệ thống sinh ra."*

NGUYÊN TẮC SỐ MỘT, nhắc lại ở đây vì đây là nơi người dùng chạm vào:

    Máy KHÔNG đọc tệp của khách để điền số hộ Sales.

Có đúng hai đường, và chúng không gặp nhau. Đường SỐ LIỆU là form dưới đây,
Sales gõ tay từng ô. Đường TỆP chỉ nhận một bản PDF rồi cất đi, không mở ra,
không rút một con số nào. Một con số rút sai từ PDF không dừng ở tờ hợp đồng:
nó chảy thẳng vào hoá đơn, vào sổ kế toán và vào lệnh xuất kho. */

var hdSua = null;   /* {name, gt:{}} khi đang soạn bản điều chỉnh */

/* Ô Sales sửa được lúc thương thảo. Khai đúng bằng danh sách SUA_DUOC bên
   Python; máy chủ vẫn lọc lại một lần nữa nên đây chỉ là để dựng màn. */
var HD_O_SUA = [
  { k: 'gia_tri', nhan: 'Giá trị hợp đồng', kieu: 'tien' },
  { k: 'dat_coc_pt', nhan: 'Đợt 1 (%)', kieu: 'so' },
  { k: 'dat_coc_tien', nhan: 'Tiền đợt 1', kieu: 'tien' },
  { k: 'ngay_dot1', nhan: 'Số ngày trả đợt 1 sau khi ký', kieu: 'so' },
  { k: 'ngay_dot2', nhan: 'Số ngày trả đợt 2 trước khi giao', kieu: 'so' },
  { k: 'ngay_ky', nhan: 'Ngày ký', kieu: 'ngay' },
  { k: 'ngay_su_kien', nhan: 'Ngày sự kiện / giao', kieu: 'ngay' },
  { k: 'dia_diem_giao', nhan: 'Địa điểm bàn giao', kieu: 'chu' },
  { k: 'thoi_gian_giao', nhan: 'Thời gian bàn giao', kieu: 'chu' },
  { k: 'ten', nhan: 'Tên hợp đồng', kieu: 'chu' },
  { k: 'so_hop_dong', nhan: 'Số hợp đồng', kieu: 'chu' },
  { k: 'mo_ta', nhan: 'Mô tả nội dung', kieu: 'dai' },
  { k: 'ten_khach', nhan: 'Tên công ty bên A', kieu: 'chu' },
  { k: 'ma_so_thue', nhan: 'Mã số thuế bên A', kieu: 'chu' },
  { k: 'dia_chi', nhan: 'Địa chỉ bên A', kieu: 'dai' },
  { k: 'dai_dien', nhan: 'Người đại diện bên A', kieu: 'chu' },
  { k: 'chuc_vu', nhan: 'Chức vụ đại diện', kieu: 'chu' },
  { k: 'dien_thoai', nhan: 'Điện thoại bên A', kieu: 'chu' },
  { k: 'email', nhan: 'Email nhận hợp đồng', kieu: 'chu' }
];

var HD_MO_DUOC = ['Nháp', 'Đã gửi khách', 'Đang thực hiện'];

function hdKhoiThuongThao(hd, d) {
  var dang = hd.trang_thai === 'Đang thương thảo';
  var pb = d.so_phien_ban || 0;
  if (dang) {
    return '<div class="card" style="padding:13px 15px;border:1.5px solid #f59e0b;background:#fffbeb">' +
      '<div style="font-size:13px;font-weight:800;color:#92400e">ĐANG THƯƠNG THẢO</div>' +
      (hd.ly_do_thuong_thao
        ? '<div style="font-size:12.5px;color:#78350f;margin-top:4px;line-height:1.6">Lý do: ' +
          h(hd.ly_do_thuong_thao) + '</div>' : '') +
      (hd.nguoi_mo_thuong_thao
        ? '<div style="font-size:11.5px;color:#a16207;margin-top:2px">' + h(hd.nguoi_mo_thuong_thao) +
          ' mở lúc ' + h(String(hd.ngay_mo_thuong_thao || '').slice(0, 16)) + '</div>' : '') +
      '<div style="font-size:12px;color:#78350f;margin-top:8px;line-height:1.6">' +
      'Sửa số liệu xong thì bấm Chốt điều chỉnh, máy sinh bản mới và trả hợp đồng ' +
      'về trạng thái cũ. Khách thôi không sửa nữa thì bấm Đóng thương thảo.</div>' +
      '<div style="display:flex;gap:8px;margin-top:10px">' +
      '<button class="btn gh" id="hdTtDong" style="margin:0;flex:1;padding:9px 10px;font-size:13px">Đóng thương thảo</button>' +
      '<button class="btn gh" id="hdTtSua" style="margin:0;flex:1.2;padding:9px 10px;font-size:13px">✏️ Sửa số liệu</button>' +
      '<button class="btn" id="hdTtChot" style="margin:0;flex:1.2;padding:9px 10px;font-size:13px">Chốt điều chỉnh</button>' +
      '</div></div>';
  }
  if (HD_MO_DUOC.indexOf(hd.trang_thai) < 0) return '';
  return '<div class="card" style="padding:12px 15px">' +
    '<div style="display:flex;gap:10px;align-items:center">' +
    '<div style="flex:1;min-width:0"><div style="font-size:13.5px;font-weight:700">Khách đòi sửa hợp đồng?</div>' +
    '<div style="font-size:12px;color:#8a90a0;margin-top:2px;line-height:1.55">' +
    'Mở thương thảo để sửa lại số liệu, hoặc tải lên bản hai bên đã chốt.' +
    (pb ? ' Đang ở <b>' + h('Hợp đồng v' + pb) + '</b>.' : '') + '</div></div>' +
    '<button class="btn gh" id="hdTtMo" style="margin:0;flex:none;width:auto;padding:9px 14px;font-size:13px;white-space:nowrap">✏️ Điều chỉnh</button>' +
    '</div></div>';
}

function hdKhoiBanChot(hd) {
  if (hd.tep_hop_dong_chot) {
    return '<div style="margin-top:10px;border:1.5px solid #a7f3d0;background:#ecfdf5;border-radius:10px;padding:11px 12px">' +
      '<div style="font-size:11.5px;font-weight:800;color:#047857">BẢN HỢP ĐỒNG ĐÃ CHỐT ĐANG DÙNG</div>' +
      '<div style="font-size:13.5px;font-weight:700;color:#065f46;margin-top:3px;word-break:break-all">' +
      h(hd.tep_chot_ten || 'hop-dong-da-chot.pdf') + '</div>' +
      '<div style="font-size:11.5px;color:#4b7a63;margin-top:2px">' +
      h(hd.tep_chot_nguoi || '') + ' tải lên lúc ' + h(String(hd.tep_chot_luc || '').slice(0, 16)) + '</div>' +
      (hd.tep_chot_ghi_chu ? '<div style="font-size:12px;color:#065f46;margin-top:4px;line-height:1.55">' + h(hd.tep_chot_ghi_chu) + '</div>' : '') +
      '<div style="font-size:12px;color:#065f46;margin-top:6px;line-height:1.6">' +
      'Tờ gửi khách và tờ đem đi ký là bản này. Nút Xuất PDF tự sinh đã tắt.</div>' +
      '<div style="display:flex;gap:8px;margin-top:9px">' +
      '<button class="btn gh" id="hdChotDoi" style="margin:0;flex:1;padding:8px 10px;font-size:13px">Đổi tệp khác</button>' +
      '<button class="btn gh" id="hdChotGo" style="margin:0;flex:1;padding:8px 10px;font-size:13px">Gỡ, dùng lại bản máy</button>' +
      '</div></div>';
  }
  return '<div style="margin-top:10px;border:1.5px dashed #d1d5db;border-radius:10px;padding:11px 12px">' +
    '<div style="font-size:13px;font-weight:700;color:#374151">Hai bên đã redline và chốt bản riêng?</div>' +
    '<div style="font-size:12px;color:#6b7280;margin-top:3px;line-height:1.6">' +
    'Tải bản PDF đã chốt lên đây. Từ lúc đó tờ gửi khách là bản của anh chị, ' +
    'không phải bản máy tự sinh.</div>' +
    '<button class="btn gh" id="hdChotTai" style="margin:8px 0 0;width:100%;font-size:13.5px">' +
    '📎 Upload bản Hợp đồng đã chốt</button>' +
    '<div style="font-size:11px;color:#9ca3af;margin-top:7px;line-height:1.55">' +
    'Máy chỉ cất tệp, KHÔNG đọc nội dung bên trong. Số liệu đổi thì anh chị vẫn ' +
    'phải gõ tay qua nút Điều chỉnh, để kế toán và kho không lệch nhau.</div></div>';
}

function hdKhoiLichSu(d) {
  var pb = d.so_phien_ban || 0;
  if (!pb) return '';
  return '<div class="sec">Lịch sử phiên bản · ' + pb + ' bản</div>' +
    '<div class="card" style="padding:12px 14px">' +
    '<div style="font-size:12.5px;color:#6b7280;line-height:1.6">' +
    'Mỗi lần chốt một lần điều chỉnh, máy ghi lại một bản kèm đúng những ô đã đổi.</div>' +
    '<button class="btn gh" id="hdLichSu" style="margin:9px 0 0;width:100%;font-size:13.5px">' +
    '🕘 Xem nhật ký thay đổi</button></div>';
}

function hdGanNutDieuChinh(hd, d, name) {
  var lai = function () { go(function () { scrHdView(name); }, true); };

  var nMo = document.getElementById('hdTtMo');
  if (nMo) nMo.onclick = async function () {
    var ly = await hoiChu('Mở thương thảo',
      'Khách yêu cầu sửa cái gì? Câu này nằm lại trong nhật ký và là thứ ' +
      'Giám đốc đọc đầu tiên.', '', { nhieu_dong: 1, goi_y: 'Ví dụ: khách xin dời ngày giao và giảm cọc còn 30%' });
    if (ly === null) return;
    busy(true);
    try {
      var r = await api('vagabond.hop_dong_dieu_chinh.mo_thuong_thao', { name: name, ly_do: ly });
      busy(false);
      if (r && r.nhac) baoTin(h(r.nhac), 'Hợp đồng đã có hoá đơn');
      else toast('Đã mở thương thảo. Bấm Sửa số liệu để cập nhật.', 4000);
      lai();
    } catch (e) { busy(false); baoTin((e && e.message) || 'Không mở được', 'Lỗi'); }
  };

  var nSua = document.getElementById('hdTtSua');
  if (nSua) nSua.onclick = function () {
    hdSua = { name: name, gt: {} };
    HD_O_SUA.forEach(function (o) { hdSua.gt[o.k] = hd[o.k]; });
    go(scrHdSuaSoLieu);
  };

  var nChot = document.getElementById('hdTtChot');
  if (nChot) nChot.onclick = async function () {
    var gc = await hoiChu('Chốt điều chỉnh',
      'Ghi thêm gì cho bản này không? Để trống cũng được, máy vẫn giữ lý do đã ghi lúc mở.',
      '', { nhieu_dong: 1 });
    if (gc === null) return;
    busy(true);
    try {
      var r = await api('vagabond.hop_dong_dieu_chinh.chot_dieu_chinh', { name: name, ghi_chu: gc });
      busy(false);
      hdKhacBietHop(r.nhan, r.khac_biet || [], r.loi_nhan);
      lai();
    } catch (e) { busy(false); baoTin((e && e.message) || 'Không chốt được', 'Lỗi'); }
  };

  var nDong = document.getElementById('hdTtDong');
  if (nDong) nDong.onclick = async function () {
    if (!await hoiCo('Đóng thương thảo',
      'Hợp đồng quay lại trạng thái cũ và KHÔNG sinh phiên bản mới. Những ô ' +
      'anh chị đã sửa thì vẫn giữ nguyên như đang sửa, chỉ là không có bản ghi ' +
      'nào đánh dấu lần này.', 'Đóng lại')) return;
    busy(true);
    try { await api('vagabond.hop_dong_dieu_chinh.huy_thuong_thao', { name: name }); busy(false); lai(); }
    catch (e) { busy(false); baoTin((e && e.message) || 'Lỗi', 'Lỗi'); }
  };

  /* ---- Đường TỆP. Chỉ cất tệp, không đọc. ---- */
  var oChot = document.getElementById('hdChotTep');
  var moTep = function () { if (oChot) { oChot.value = ''; oChot.click(); } };
  var nTai = document.getElementById('hdChotTai');
  var nDoi = document.getElementById('hdChotDoi');
  if (nTai) nTai.onclick = function () { hdCanhBaoGhiDe(hd, moTep); };
  if (nDoi) nDoi.onclick = function () { hdCanhBaoGhiDe(hd, moTep); };
  if (oChot) oChot.onchange = function () { hdTaiBanChot(name, oChot.files && oChot.files[0]); };

  var nGo = document.getElementById('hdChotGo');
  if (nGo) nGo.onclick = async function () {
    var ly = await hoiChu('Gỡ bản đã chốt',
      'Vì sao quay lại dùng bản máy tự sinh? Câu này nằm lại trong nhật ký của hợp đồng.', '');
    if (ly === null) return;
    if (!String(ly || '').trim()) return baoTin('Phải ghi lý do thì mới gỡ được.', 'Thiếu lý do');
    busy(true);
    try {
      var r = await api('vagabond.hop_dong_dieu_chinh.go_ban_chot', { name: name, ly_do: ly });
      busy(false); toast((r && r.loi_nhan) || 'Đã gỡ.', 4500); lai();
    } catch (e) { busy(false); baoTin((e && e.message) || 'Không gỡ được', 'Lỗi'); }
  };

  var nTaiChot = document.getElementById('hdTaiChot');
  if (nTaiChot) nTaiChot.onclick = async function () {
    busy(true);
    try {
      var f = await api('vagabond.hop_dong_dieu_chinh.tai_ve_ban_chot', { name: name });
      busy(false); bcTaiVe(f.ten_file, f.b64, f.kieu);
      toast('Đã tải ' + f.ten_file, 4000);
    } catch (e) { busy(false); baoTin((e && e.message) || 'Không tải được', 'Lỗi'); }
  };

  var nLs = document.getElementById('hdLichSu');
  if (nLs) nLs.onclick = function () { hdXemLichSu(name); };
}

/* Cảnh báo trước khi tải lên. Anh Việt dặn phải nói rõ: *"Bản upload này sẽ
   ghi đè và thay thế bản hợp đồng tự sinh của hệ thống."* */
async function hdCanhBaoGhiDe(hd, tiep) {
  var ok = await hoiCo('Upload bản Hợp đồng đã chốt',
    '<b>Bản upload này sẽ ghi đè và thay thế bản hợp đồng tự sinh của hệ thống.</b>' +
    '<br><br>Từ lúc tải lên, nút Xuất PDF tự sinh tắt hẳn, và thư gửi khách sẽ đính ' +
    'đúng tệp anh chị vừa chọn.' +
    '<br><br>Máy <b>không đọc</b> nội dung tệp. Nếu bản chốt có đổi giá hay số lượng ' +
    'thì anh chị vẫn phải gõ tay qua nút Điều chỉnh, không thì kế toán và kho vẫn ' +
    'chạy theo con số cũ.',
    'Đã hiểu, chọn tệp');
  if (ok) tiep();
}

function hdTaiBanChot(name, file) {
  if (!file) return;
  if (!/\.pdf$/i.test(file.name || '')) {
    return baoTin('Chỉ nhận tệp PDF. Bản Word thì bấm Lưu thành PDF rồi chọn lại, ' +
      'vì bản gửi khách phải là bản không sửa được nữa.', 'Sai định dạng');
  }
  if (file.size > 20 * 1024 * 1024) {
    return baoTin('Tệp nặng ' + Math.round(file.size / 1048576) + ' MB, quá 20 MB. ' +
      'Xuất lại bản PDF nhẹ hơn giúp em.', 'Tệp quá nặng');
  }
  var fr = new FileReader();
  fr.onload = async function () {
    var gc = await hoiChu('Ghi chú cho bản này',
      'Ví dụ: bản chốt sau buổi họp 21/08, khách bỏ điều 5 và thêm điều khoản bảo mật.',
      '', { nhieu_dong: 1 });
    if (gc === null) gc = '';
    busy(true);
    try {
      var r = await api('vagabond.hop_dong_dieu_chinh.tai_ban_chot', {
        name: name, ten: file.name || 'hop-dong-da-chot.pdf',
        noi_dung: String(fr.result || ''), ghi_chu: gc
      });
      busy(false);
      toast((r && r.loi_nhan) || 'Đã tải lên.', 5500);
      go(function () { scrHdView(name); }, true);
    } catch (e) {
      busy(false); baoTin((e && e.message) || 'Không tải lên được', 'Lỗi');
    }
  };
  fr.readAsDataURL(file);
}

/* ---- Form sửa số liệu. Sales gõ TAY từng ô. ---- */
function scrHdSuaSoLieu() {
  var f = hdSua;
  if (!f) return go(scrHopDong, true);
  var o = function (c) {
    var v = f.gt[c.k];
    var id = 'hds_' + c.k;
    if (c.kieu === 'dai') {
      return '<div class="vxl">' + h(c.nhan) + '</div>' +
        '<textarea class="vxi" id="' + id + '" data-hds="' + h(c.k) + '" rows="3" style="font-family:inherit">' +
        h(v == null ? '' : v) + '</textarea>';
    }
    return '<div class="vxl">' + h(c.nhan) + '</div>' +
      '<input class="vxi' + (c.kieu === 'tien' ? ' tien' : '') + '" id="' + id + '" data-hds="' + h(c.k) + '"' +
      (c.kieu === 'ngay' ? ' type="date"' : '') +
      (c.kieu === 'so' || c.kieu === 'tien' ? ' inputmode="decimal"' : '') +
      ' value="' + h(v == null ? '' : (c.kieu === 'tien' ? tienChuoi(v) : v)) + '">';
  };
  var html = '<div class="vxf">' +
    '<div style="font-size:12.5px;color:#92400e;background:#fffbeb;border:1px solid #fde68a;' +
    'border-radius:10px;padding:11px 12px;line-height:1.65">' +
    '<b>Anh chị gõ tay từng ô.</b> Máy cố ý không đọc tệp của khách để điền hộ: ' +
    'một con số rút sai từ PDF sẽ chạy thẳng vào hoá đơn, sổ kế toán và lệnh xuất kho, ' +
    'mà vẫn trông rất hợp lý.</div>' +
    '<div style="font-size:12px;color:#6b7280;margin-top:10px;line-height:1.6">' +
    'Đổi <b>dòng hàng</b> (thêm bớt món, đổi số lượng từng món) thì phải sửa ở tờ ' +
    'báo giá nguồn rồi lập lại hợp đồng, vì Phụ lục 01 lấy từng dòng từ đó ra. ' +
    'Ô dưới đây là các điều khoản của chính tờ hợp đồng.</div>' +
    HD_O_SUA.map(o).join('') +
    '</div>';
  var b = frame('Sửa số liệu hợp đồng', html, {
    footer: '<button class="btn" id="hdsLuu" style="margin:0">Lưu số liệu mới</button>'
  });
  b.querySelectorAll('[data-hds]').forEach(function (n) {
    var k = n.getAttribute('data-hds');
    var doc = function () { f.gt[k] = n.classList.contains('tien') ? soTien(n.value) : n.value; };
    n.oninput = doc; n.onchange = doc;
  });
  document.getElementById('hdsLuu').onclick = async function () {
    busy(true);
    try {
      var r = await api('vagabond.hop_dong_dieu_chinh.cap_nhat_so_lieu', {
        name: f.name, gt: JSON.stringify(f.gt)
      });
      busy(false);
      toast('Đã lưu ' + ((r && r.da_sua) || []).length + ' ô. Bấm Chốt điều chỉnh để ghi thành bản mới.', 5000);
      var nm = f.name; hdSua = null;
      go(function () { scrHdView(nm); }, true);
    } catch (e) { busy(false); baoTin((e && e.message) || 'Không lưu được', 'Lỗi'); }
  };
}

/* ---- Nhật ký phiên bản ---- */
function hdDongKhac(k) {
  var ve = function (v) {
    if (k.kieu === 'tien') return money(v) + ' đ';
    if (v === '' || v === null || v === undefined) return '(trống)';
    return String(v);
  };
  return '<div style="border-top:1px solid #f2f4f7;padding:7px 0;font-size:12.5px;line-height:1.55">' +
    '<div style="font-weight:700;color:#374151">' + h(k.nhan) + '</div>' +
    '<div style="color:#b3261e;text-decoration:line-through">' + h(ve(k.tu)) + '</div>' +
    '<div style="color:#047857;font-weight:700">' + h(ve(k.den)) + '</div></div>';
}

function hdKhacBietHop(nhan, khac, loi) {
  var than = '<div style="font-size:13px;color:#374151;line-height:1.6">' + h(loi || '') + '</div>';
  if (khac && khac.length) {
    than += '<div style="margin-top:10px">' + khac.map(hdDongKhac).join('') + '</div>';
  }
  var k = hopKhung(nhan || 'Đã chốt', than,
    '<button class="btn" data-hbok style="flex:1;margin:0">Đã hiểu</button>');
  k.box.querySelector('.x').onclick = k.dong;
  k.box.querySelector('[data-hbok]').onclick = k.dong;
}

async function hdXemLichSu(name) {
  busy(true);
  var r;
  try { r = await api('vagabond.hop_dong_dieu_chinh.lich_su', { name: name }); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Không đọc được nhật ký', 'Lỗi'); }
  busy(false);
  var ds = (r && r.ds) || [];
  if (!ds.length) return baoTin('Hợp đồng này chưa có bản điều chỉnh nào.', 'Nhật ký trống');
  var than = ds.map(function (x) {
    return '<div style="border:1px solid #e5e7eb;border-radius:10px;padding:10px 12px;margin-bottom:9px">' +
      '<div style="display:flex;justify-content:space-between;gap:8px;align-items:baseline">' +
      '<b style="font-size:14px">' + h(x.nhan || ('Hợp đồng v' + x.phien_ban)) + '</b>' +
      '<span style="font-size:12.5px;font-weight:700">' + money(x.gia_tri) + ' đ</span></div>' +
      '<div style="font-size:11.5px;color:#8a90a0;margin-top:2px">' +
      h(x.nguoi || '') + ' · ' + h(String(x.luc || '').slice(0, 16)) +
      (x.trang_thai_luc_chot ? ' · ' + h(x.trang_thai_luc_chot) : '') + '</div>' +
      (x.ly_do ? '<div style="font-size:12.5px;color:#4b5563;margin-top:5px;line-height:1.55">' + h(x.ly_do) + '</div>' : '') +
      (x.tep_chot ? '<div style="font-size:12px;margin-top:4px">📄 Bản chốt đính kèm</div>' : '') +
      ((x.khac_biet && x.khac_biet.length)
        ? '<div style="margin-top:6px">' + x.khac_biet.map(hdDongKhac).join('') + '</div>'
        : '<div style="font-size:12px;color:#9ca3af;margin-top:5px">Bản gốc, không có gì để so.</div>') +
      '</div>';
  }).join('');
  var k = hopKhung('Nhật ký thay đổi · ' + ds.length + ' bản', than,
    '<button class="btn" data-hlok style="flex:1;margin:0">Đóng</button>');
  k.box.querySelector('.x').onclick = k.dong;
  k.box.querySelector('[data-hlok]').onclick = k.dong;
}

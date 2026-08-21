/* ---------------- Đơn Pancake đã huỷ, tiền khách còn ở công ty

   Anh Việt giao 21/08/2026 kèm ảnh ba đơn: 92252 (705.000 đ), 92245
   (920.000 đ), 92156 (750.000 đ). Cả ba đều "Đã huỷ" trên Pancake và khách
   đã chuyển tiền.

   VÌ SAO KHÔNG NẰM CHUNG DANH SÁCH ĐƠN
   ------------------------------------
   Những đơn này KHÔNG BAO GIỜ sang ERPNext thành hoá đơn, kể cả hoá đơn
   nháp. Hai tầng lọc của luồng đồng bộ chặn chúng lại: chỉ trạng thái 3 và
   16 mới thành hoá đơn, và khung quét là ngày giao chứ không phải ngày đặt.
   Lý do đầy đủ ở đầu vagabond/don_huy.py.

   Nên màn này đọc từ BẢNG ĐỆM riêng, không đọc Sales Invoice. Chip trạng
   thái cũng là trạng thái hoàn tiền chứ không phải trạng thái hoá đơn.

   Tiền tố dh = đơn huỷ. Đã kiểm và chạm tên trước khi đặt (QT-28). */

var dhLoc = '';        // chip đang chọn, rỗng là tất cả
var dhTim = '';        // ô tìm
var dhKq = null;       // kết quả lần tải gần nhất

function dhMau(tt) {
  if (tt === 'Cho hoan') return ['#fef2f2', '#fecaca', '#b3261e'];
  if (tt === 'Dang hoan') return ['#fffbeb', '#fcd34d', '#92400e'];
  if (tt === 'Da hoan') return ['#ecfdf3', '#a6f4c5', '#05603a'];
  if (tt === 'Bo qua') return ['#f8fafc', '#e2e8f0', '#64748b'];
  return ['#f0f9ff', '#bae6fd', '#0369a1'];
}

/* Chip lọc có ĐẾM SỐ ngay trên chip. Số đếm tính trên toàn bảng chứ không
   phải trên trang đang xem, để "Chờ hoàn 3" nói đúng số việc còn tồn. */
function dhChips(dem, nhan) {
  var thu_tu = ['Cho hoan', 'Dang hoan', 'Da hoan', 'Khong phai hoan', 'Bo qua'];
  var s = posChipNut('data-dhl=""', 'Tất cả · ' + (dem.tat_ca || 0), dhLoc === '');
  thu_tu.forEach(function (k) {
    var n = dem[k] || 0;
    if (!n && k !== 'Cho hoan') return;   // chip rỗng thì ẩn, trừ chip chính
    s += posChipNut('data-dhl="' + k + '"', (nhan[k] || k) + ' · ' + n, dhLoc === k);
  });
  return '<div style="display:flex;gap:7px;flex-wrap:wrap;margin:9px 0">' + s + '</div>';
}

async function scrDonHuy() {
  frame('Đơn đã huỷ chờ hoàn', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc danh sách...</div></div>');
  var kq;
  try { kq = await api('vagabond.don_huy.ds', { trang_thai: dhLoc, tim: dhTim }); }
  catch (e) {
    frame('Đơn đã huỷ chờ hoàn', '<div class="emp"><div class="e1">⚠️</div><div>' +
      h(errMsg(e)) + '</div></div>');
    return;
  }
  dhKq = kq;
  var dong = kq.dong || [], dem = kq.dem || {}, nhan = kq.nhan || {};

  var html = '<div class="card" style="padding:12px 13px">' +
    '<div style="font-size:13px;color:#344054;line-height:1.6">' +
    'Đơn Pancake <b>đã huỷ</b> mà tiền khách vẫn nằm ở công ty. Những đơn này ' +
    'không bao giờ có hoá đơn trong ERPNext nên không tìm được ở màn Doanh thu.' +
    '</div>' +
    '<div style="margin-top:9px;display:flex;align-items:baseline;gap:8px">' +
    '<span style="font-size:12px;color:#8a8f9c">ĐANG GIỮ HỘ KHÁCH</span>' +
    '<b style="font-size:19px;color:#b3261e">' + money(kq.tien_cho_hoan || 0) + ' đ</b></div>' +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:4px">Danh sách giữ ' +
    (kq.ngay_giu || 30) + ' ngày. Đơn quá hạn mà không phải hoàn thì tự dọn, ' +
    'đơn đã lập phiếu thì giữ lại.</div></div>';

  html += dhChips(dem, nhan);
  html += '<div class="card" style="padding:9px 11px"><input id="dhTim" type="search" ' +
    'placeholder="Tìm theo mã đơn, tên khách, số điện thoại" value="' + h(dhTim) + '" ' +
    'style="width:100%;height:38px;border:1.5px solid #e4e7ec;border-radius:9px;' +
    'padding:0 10px;font-size:14px"></div>';

  html += '<div class="sec">' + dong.length + ' đơn · bấm vào đơn để hoàn tiền</div><div class="card">';
  if (!dong.length) {
    html += '<div class="emp" style="padding:24px"><div class="e1">✅</div>' +
      '<div>Không có đơn nào trong nhóm này. Bấm Đồng bộ để kéo lại từ Pancake.</div></div>';
  }
  dong.forEach(function (r) {
    var m = dhMau(r.trang_thai);
    html += '<div class="hub" data-dh="' + h(r.ma_don) + '">' +
      '<div class="hi">' + (r.trang_thai === 'Da hoan' ? '✅' : '↩️') + '</div>' +
      '<div class="ht"><div class="h1">#' + h(r.ma_hien_thi || r.ma_don) + ' · ' +
      h(r.ten_khach || 'Khách lẻ') + '</div>' +
      '<div class="h2">' + h(r.sdt || '') + (r.huy_luc ? ' · huỷ ' + h(String(r.huy_luc).slice(0, 16)) : '') + '</div>' +
      '<div class="h2" style="margin-top:4px">' +
      '<span style="background:' + m[0] + ';border:1px solid ' + m[1] + ';color:' + m[2] +
      ';border-radius:20px;padding:1px 9px;font-size:11.5px">' + h(r.nhan_trang_thai) + '</span>' +
      (r.ho_so_hoan ? ' <span style="font-size:11.5px;color:#98a2b3">' + h(r.ho_so_hoan) + '</span>' : '') +
      '</div></div>' +
      '<div style="text-align:right;white-space:nowrap">' +
      '<b style="font-size:13.5px">' + money(r.da_nhan) + '</b>' +
      '<div style="font-size:11px;color:#98a2b3">đơn ' + money(r.tong_don) + '</div></div></div>';
  });
  html += '</div>';

  var foot = '<div style="display:flex;gap:9px">' +
    '<button class="btn gh" data-dhb="dongbo" style="flex:1">🔄 Đồng bộ Pancake</button>' +
    '<button class="btn gh" data-dhb="excel" style="flex:1">📄 Xuất Excel</button></div>';

  var b = frame('Đơn đã huỷ chờ hoàn', html, { footer: foot });
  var o = document.getElementById('dhTim');
  if (o) {
    o.onchange = function () { dhTim = o.value.trim(); go(scrDonHuy, true); };
    o.onkeydown = function (e) { if (e.key === 'Enter') { dhTim = o.value.trim(); go(scrDonHuy, true); } };
  }
  b.addEventListener('click', dhBam);
}

async function dhBam(ev) {
  var el;
  if ((el = ev.target.closest('[data-dhl]'))) {
    dhLoc = el.getAttribute('data-dhl');
    return go(scrDonHuy, true);
  }
  if ((el = ev.target.closest('[data-dhb]'))) {
    var v = el.getAttribute('data-dhb');
    if (v === 'dongbo') return dhDongBo();
    if (v === 'excel') return dhExcel();
  }
  if ((el = ev.target.closest('[data-dh]'))) return dhMo(el.getAttribute('data-dh'));
}

async function dhDongBo() {
  busy(1);
  var kq;
  try { kq = await api('vagabond.don_huy.dong_bo', {}); }
  catch (e) { busy(0); return toast(errMsg(e), 6000); }
  busy(0);
  toast('Quét ' + kq.quet + ' đơn huỷ · thêm mới ' + kq.moi + ' · cập nhật ' +
    kq.cap_nhat + (kq.don_dep ? ' · dọn ' + kq.don_dep + ' đơn quá hạn' : ''), 6000);
  return go(scrDonHuy, true);
}

async function dhExcel() {
  busy(1);
  var kq;
  try { kq = await api('vagabond.don_huy.xuat_excel', { trang_thai: dhLoc, tim: dhTim }); }
  catch (e) { busy(0); return toast(errMsg(e), 6000); }
  busy(0);
  if (!kq.tong_dong) return toast('Không có dòng nào để xuất.', 4000);
  /* Dựng CSV ngay trên máy chứ không nhờ máy chủ sinh tệp: danh sách này
     nhiều nhất vài trăm dòng, và làm vậy thì kế toán bấm là có ngay, không
     phải chờ một vòng tải tệp. Có BOM để Excel đọc đúng tiếng Việt. */
  var esc = function (v) {
    var s = (v === null || v === undefined) ? '' : String(v);
    return '"' + s.replace(/"/g, '""') + '"';
  };
  var csv = kq.cot.map(esc).join(',') + '\n' +
    kq.hang.map(function (h2) { return h2.map(esc).join(','); }).join('\n');
  var blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = kq.ten_tep;
  document.body.appendChild(a);
  a.click();
  setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  toast('Đã xuất ' + kq.tong_dong + ' dòng.', 4000);
}

/* ---------------- Form hoàn tiền cho một đơn đã huỷ

   Form riêng chứ không dùng lại `hoanVeForm` của màn Chi tiết đơn: form kia
   neo vào một Sales Invoice từ đầu tới cuối, mà đơn ở đây thì không có hoá
   đơn nào. Nhét thêm một nhánh vào form đó là làm nó gánh hai việc khác
   nhau, và tệp 11 đang có phiên khác đụng tới. */

var dhF = null;   // trạng thái form đang mở
var dhOv = null;  // thẻ phủ

function dhDong() { if (dhOv) { dhOv.remove(); dhOv = null; } dhF = null; }

async function dhMo(ma) {
  busy(1);
  var t;
  try { t = await api('vagabond.don_huy.xem_hoan', { ma_don: ma }); }
  catch (e) { busy(0); return toast(errMsg(e), 6000); }
  busy(0);
  if (!t.duoc) return toast(t.vi_sao || 'Đơn này chưa hoàn được.', 7000);

  dhF = {
    ma: t.ma_don, hien: t.ma_hien_thi, ten: t.ten_khach, sdt: t.sdt,
    tong: t.tong_don, da_nhan: t.da_nhan, tien: t.muc_hoan,
    ly_do: '', dien_giai: '', ten_tk: t.ten_khach || '', so_tk: '',
    ngan_hang: '', otp: '', noi_dung_ck: t.noi_dung_ck
  };
  dhOv = document.createElement('div');
  dhOv.className = 'sh';
  dhOv.innerHTML = '<div class="shb" style="padding:16px 15px calc(env(safe-area-inset-bottom,0px) + 14px);max-height:90vh;overflow:auto"></div>';
  document.body.appendChild(dhOv);
  dhOv.addEventListener('click', dhFBam);
  dhVeForm();
}

function dhVeForm() {
  var f = dhF; if (!f || !dhOv) return;
  var s = '<div style="font-size:17.5px;font-weight:700">Hoàn tiền đơn đã huỷ</div>' +
    '<div style="font-size:13px;color:#344054;margin-top:2px">#' + h(f.hien || f.ma) +
    ' · ' + h(f.ten || 'Khách lẻ') + '</div>' +
    '<div style="font-size:12px;color:#98a2b3;margin-bottom:12px">Khách đã chuyển ' +
    money(f.da_nhan) + ' đ · giá trị đơn ' + money(f.tong) + ' đ</div>';

  /* Ba câu này là thứ chị Dung đọc trước khi duyệt, và cũng là thứ giữ cho
     không ai nghĩ tới việc ghi sổ một đơn chưa từng có để "có cái mà đính". */
  s += '<div style="font-size:12px;color:#065f46;background:#ecfdf5;border:1px solid #a7f3d0;' +
    'border-radius:9px;padding:9px 11px;margin-bottom:10px;line-height:1.6">' +
    'Đơn này <b>chưa bao giờ có hoá đơn</b> trong hệ, nên không có doanh thu để khử. ' +
    'Máy <b>không lập hoá đơn trả hàng</b> và <b>không đụng hoá đơn điện tử</b>. ' +
    'Khoản này là tiền khách chuyển trước, công ty giữ hộ và nay trả lại.</div>';
  s += '<div style="font-size:12px;color:#1e40af;background:#eff6ff;border:1px solid #bfdbfe;' +
    'border-radius:9px;padding:9px 11px;margin-bottom:10px;line-height:1.6">' +
    'Máy sinh sẵn <b>hai phiếu ở dạng nháp</b>: phiếu thu cho khoản khách đã chuyển ' +
    'và phiếu chi cho khoản trả lại. Kế toán đính giấy báo Có và uỷ nhiệm chi tải từ ' +
    'e-banking rồi mới ghi sổ.</div>';
  s += '<div style="font-size:12px;color:#7c2d12;background:#fff7ed;border:1px solid #fed7aa;' +
    'border-radius:9px;padding:9px 11px;margin-bottom:12px;line-height:1.6">' +
    'Chuyển lại <b>đúng số tài khoản khách đã chuyển đến</b>. Khách nhắn xin đổi tài ' +
    'khoản thì gọi điện xác minh trước, đây là kịch bản lừa đảo phổ biến.</div>';

  s += rndLbl('Số tiền trả lại khách') +
    '<input class="nt" id="dhTien" inputmode="numeric" value="' + h(money(f.tien)) + '">' +
    '<div style="font-size:11.5px;color:#9ca3af;margin:5px 0 12px">Tối đa ' +
    money(f.da_nhan) + ' đ, đúng bằng số máy thấy đã nhận. Sửa xuống được nếu có ' +
    'thoả thuận trừ tiền nguyên liệu, nhưng phần giữ lại là doanh thu và phải ' +
    'xuất hoá đơn riêng.</div>';

  s += rndLbl('Lý do huỷ') + '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px">';
  ['Khach doi y', 'Khach dat nham ngay', 'Bep khong kip lam', 'Het nguyen lieu', 'Trung don', 'Khac']
    .forEach(function (k) {
      var on = f.ly_do === k;
      s += '<button data-dhly="' + h(k) + '" style="border:1.5px solid ' +
        (on ? '#0f766e' : '#e5e7eb') + ';background:' + (on ? '#ccfbf1' : '#fff') +
        ';color:' + (on ? '#0f766e' : '#374151') + ';border-radius:20px;padding:6px 12px;' +
        'font-size:12.5px;font-weight:' + (on ? '700' : '500') + '">' + h(k) + '</button>';
    });
  s += '</div>';

  s += rndLbl('Tài khoản nhận tiền của khách') +
    '<input class="nt" id="dhNH" placeholder="Ngân hàng, ví dụ MB, VCB" value="' + h(f.ngan_hang) + '">' +
    '<div style="height:8px"></div>' +
    '<input class="nt" id="dhSTK" inputmode="numeric" placeholder="Số tài khoản" value="' + h(f.so_tk) + '">' +
    '<div style="height:8px"></div>' +
    '<input class="nt" id="dhTenTK" placeholder="Tên chủ tài khoản" value="' + h(f.ten_tk) + '">' +
    '<div style="height:12px"></div>';

  s += rndLbl('Ghi chú thêm') +
    '<input class="nt" id="dhGhi" placeholder="Không bắt buộc" value="' + h(f.dien_giai) + '">' +
    '<div style="height:12px"></div>';

  s += rndLbl('Mã OTP của quản lý') +
    '<input class="nt" id="dhOtp" inputmode="numeric" placeholder="Quản lý tự bấm thì để trống" value="' + h(f.otp) + '">' +
    '<div style="font-size:11.5px;color:#9ca3af;margin:5px 0 12px">Nội dung chuyển khoản sẽ là <b>' +
    h(f.noi_dung_ck) + '</b></div>';

  s += '<button class="btn" data-dhok style="margin-top:4px">Gửi kế toán duyệt</button>' +
    '<button class="btn gh" data-dhhuy style="margin-top:9px">Đóng</button>';
  dhOv.querySelector('.shb').innerHTML = s;
}

function dhDocO() {
  var f = dhF; if (!f || !dhOv) return;
  var lay = function (id) { var e = dhOv.querySelector('#' + id); return e ? e.value : ''; };
  f.tien = Number(String(lay('dhTien')).replace(/[^0-9]/g, '')) || 0;
  f.ngan_hang = lay('dhNH').trim();
  f.so_tk = lay('dhSTK').replace(/[^0-9]/g, '');
  f.ten_tk = lay('dhTenTK').trim();
  f.dien_giai = lay('dhGhi').trim();
  f.otp = lay('dhOtp').replace(/[^0-9]/g, '');
}

async function dhFBam(ev) {
  var el;
  if (ev.target === dhOv) return dhDong();
  if (ev.target.closest('[data-dhhuy]')) return dhDong();
  if ((el = ev.target.closest('[data-dhly]'))) {
    dhDocO(); dhF.ly_do = el.getAttribute('data-dhly'); return dhVeForm();
  }
  if (ev.target.closest('[data-dhok]')) return dhGui();
}

async function dhGui() {
  dhDocO();
  var f = dhF;
  if (!f.tien) return toast('Điền số tiền trả lại khách.', 4000);
  if (f.tien > f.da_nhan) return toast('Không hoàn quá số khách đã chuyển (' + money(f.da_nhan) + ' đ).', 5000);
  if (!f.ly_do) return toast('Chọn lý do huỷ.', 4000);
  if (!(f.ngan_hang && f.so_tk && f.ten_tk)) return toast('Điền đủ ngân hàng, số tài khoản và tên chủ tài khoản.', 5000);
  busy(1);
  var kq;
  try {
    kq = await api('vagabond.don_huy.tao_hoan', {
      ma_don: f.ma, so_tien: f.tien, ly_do: f.ly_do, dien_giai: f.dien_giai,
      ten_tk: f.ten_tk, so_tk: f.so_tk, ngan_hang: f.ngan_hang,
      sdt_khach: f.sdt, otp: f.otp
    });
  } catch (e) { busy(0); return toast(errMsg(e), 7000); }
  busy(0);
  dhDong();
  toast('Đã lập hồ sơ ' + kq.ho_so + ' · phiếu thu ' + (kq.phieu_thu || '?') +
    ' · phiếu chi ' + (kq.phieu_chi || '?') + '. Hai phiếu đang ở dạng nháp.', 8000);
  return go(scrDonHuy, true);
}

/* ---------------- Phiếu hoàn của đơn Pancake đã huỷ, cửa sổ phía Sales

   Anh Việt giao 31/08/2026: *"thêm dùm anh nút để xem lại danh sách các
   phiếu hoàn cho đơn đã huỷ của pancake để sales theo dõi, nối các trạng
   thái, hồ sơ, uỷ nhiệm chi,... bên chỗ kế toán làm lên để tự động cập nhật
   sang cho bên sales theo dõi, tải UNC gửi khách"*.

   VÌ SAO PHẢI CÓ MÀN NÀY
   ----------------------
   Sales lập phiếu hoàn xong là mất dấu. Phần còn lại của việc - kế toán
   chuyển tiền, đính uỷ nhiệm chi, ghi sổ phiếu chi, khớp sao kê - đều nằm
   trong phân hệ Kế toán, mà v355 đã khoá phân hệ đó lại không cho nhân viên
   vào. Nên khách nhắn "tiền của em tới đâu rồi" là Sales không có chỗ nào
   để nhìn, phải đi hỏi.

   Màn này là cửa sổ CHỈ ĐỌC mở về phía Sales. Không có nhịp đồng bộ nào và
   cũng không có bảng thứ hai: nó đọc thẳng hồ sơ hoàn tiền và phiếu chi mà
   kế toán đang làm, nên kế toán bấm xong là Sales mở màn ra thấy ngay.

   Uỷ nhiệm chi trả về ĐƯỜNG DẪN TỆP chứ không phải chỉ một cái dấu tích:
   thứ Sales cần là tải nó xuống gửi cho khách, đó là cả lý do có màn.

   Ô tìm và chip đếm chạy Ở MÁY CHỦ (QT-19). Xem `don_huy.dieu_kien_tim`.

   Tiền tố ph = phiếu hoàn. Đã kiểm và chạm tên trước khi đặt (QT-28). */

var phLoc = '';        // chip trạng thái đang chọn, rỗng là tất cả
var phTim = '';        // ô tìm
var phMoRong = {};     // mã phiếu nào đang mở rộng xem chi tiết

function phMau(tt) {
  if (tt === 'Cho chi') return ['#fffbeb', '#fcd34d', '#92400e'];
  if (tt === 'Da chi') return ['#eff8ff', '#b2ddff', '#175cd3'];
  if (tt === 'Da doi soat') return ['#f0f9ff', '#bae6fd', '#0369a1'];
  if (tt === 'Hoan thanh') return ['#ecfdf3', '#a6f4c5', '#05603a'];
  if (tt === 'Da huy') return ['#f8fafc', '#e2e8f0', '#64748b'];
  return ['#f8fafc', '#e2e8f0', '#64748b'];
}

function phChips(dem, nhan) {
  var thu_tu = ['Cho chi', 'Da chi', 'Da doi soat', 'Hoan thanh', 'Da huy'];
  var s = posChipNut('data-phl=""', 'Tất cả · ' + (dem.tat_ca || 0), phLoc === '');
  thu_tu.forEach(function (k) {
    var n = dem[k] || 0;
    if (!n && k !== 'Cho chi') return;   // chip rỗng thì ẩn, trừ chip chính
    s += posChipNut('data-phl="' + k + '"', (nhan[k] || k) + ' · ' + n, phLoc === k);
  });
  return '<div style="display:flex;gap:7px;flex-wrap:wrap;margin:9px 0">' + s + '</div>';
}

/* Dây chuyền bốn bước, vẽ thành bốn chấm nối nhau. Cách nói này trả lời
   đúng câu khách hỏi Sales, mà một dòng trạng thái đơn lẻ thì không: trạng
   thái nhảy sang "Đã chi" ngay lúc kế toán ghi sổ, nhưng thứ khách muốn là
   cái uỷ nhiệm chi. */
function phDay(r, buoc) {
  var s = '<div style="display:flex;align-items:center;gap:0;margin-top:7px">';
  (buoc || []).forEach(function (b, i) {
    var xong = (r.buoc_xong || 0) > i;
    var dang = (r.buoc_cho === b.k);
    var nen = xong ? '#12b76a' : (dang ? '#f79009' : '#e4e7ec');
    var chu = xong ? '✓' : String(i + 1);
    if (i) {
      s += '<div style="flex:1;height:3px;background:' +
        (xong ? '#12b76a' : '#e4e7ec') + '"></div>';
    }
    s += '<div title="' + h(b.ten) + '" style="width:19px;height:19px;flex:0 0 19px;' +
      'border-radius:50%;background:' + nen + ';color:#fff;font-size:11px;' +
      'line-height:19px;text-align:center;font-weight:700">' + chu + '</div>';
  });
  return s + '</div>';
}

async function scrPhieuHoanHuy() {
  frame('Phiếu hoàn đơn huỷ', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc danh sách...</div></div>');
  var kq;
  try { kq = await api('vagabond.don_huy.ds_phieu', { trang_thai: phLoc, tim: phTim }); }
  catch (e) {
    frame('Phiếu hoàn đơn huỷ', '<div class="emp"><div class="e1">⚠️</div><div>' +
      h(errMsg(e)) + '</div></div>');
    return;
  }
  var dong = kq.dong || [], dem = kq.dem || {}, nhan = kq.nhan || {}, buoc = kq.buoc || [];

  var html = '<div class="card" style="padding:12px 13px">' +
    '<div style="font-size:13px;color:#344054;line-height:1.6">' +
    'Phiếu hoàn tiền của những đơn Pancake <b>đã huỷ</b>. Kế toán làm tới đâu ' +
    'màn này hiện tới đó, không phải đi hỏi. Có uỷ nhiệm chi rồi thì tải về ' +
    'gửi cho khách ngay tại đây.</div>' +
    '<div style="margin-top:9px;display:flex;align-items:baseline;gap:8px">' +
    '<span style="font-size:12px;color:#8a8f9c">TIỀN ĐANG CHẠY</span>' +
    '<b style="font-size:19px;color:#b54708">' + money(kq.tien_dang_chay || 0) + ' đ</b></div>' +
    (kq.cho_unc ? '<div style="font-size:11.5px;color:#b3261e;margin-top:4px">' +
      kq.cho_unc + ' phiếu đang chờ kế toán chuyển tiền và đính uỷ nhiệm chi.</div>' : '') +
    '</div>';

  html += phChips(dem, nhan);
  html += '<div class="card" style="padding:9px 11px"><input id="phTim" type="search" ' +
    'placeholder="Tìm theo mã đơn, tên khách, số tài khoản, mã phiếu" value="' + h(phTim) + '" ' +
    'style="width:100%;height:38px;border:1.5px solid #e4e7ec;border-radius:9px;' +
    'padding:0 10px;font-size:14px"></div>';

  html += '<div class="sec">' + dong.length + ' phiếu · bấm để xem chi tiết</div><div class="card">';
  if (!dong.length) {
    html += '<div class="emp" style="padding:24px"><div class="e1">📄</div>' +
      '<div>Chưa có phiếu hoàn nào trong nhóm này.</div></div>';
  }
  dong.forEach(function (r) {
    var m = phMau(r.trang_thai);
    var mo = !!phMoRong[r.name];
    html += '<div class="hub" data-phm="' + h(r.name) + '" style="align-items:flex-start">' +
      '<div class="hi">' + ((r.buoc_xong || 0) >= 4 ? '✅' : '💸') + '</div>' +
      '<div class="ht"><div class="h1">#' + h(r.ma_hien_thi || r.ma_don_pancake) +
      ' · ' + h(r.ten_khach || 'Khách lẻ') + '</div>' +
      '<div class="h2">' + h(r.cau_tinh_hinh || '') + '</div>' +
      phDay(r, buoc) +
      '<div class="h2" style="margin-top:6px">' +
      '<span style="background:' + m[0] + ';border:1px solid ' + m[1] + ';color:' + m[2] +
      ';border-radius:20px;padding:1px 9px;font-size:11.5px">' + h(r.nhan_trang_thai) + '</span>' +
      (r.co_unc ? ' <span style="background:#ecfdf3;border:1px solid #a6f4c5;color:#05603a;' +
        'border-radius:20px;padding:1px 9px;font-size:11.5px">Có uỷ nhiệm chi</span>' : '') +
      '</div>' + (mo ? phChiTiet(r) : '') + '</div>' +
      '<div style="text-align:right;white-space:nowrap">' +
      '<b style="font-size:13.5px">' + money(r.so_tien) + '</b>' +
      '<div style="font-size:11px;color:#98a2b3">' + h(r.creation || '') + '</div></div></div>';
  });
  html += '</div>';

  var foot = '<div style="display:flex;gap:9px">' +
    '<button class="btn gh" data-phb="don" style="flex:1">↩️ Đơn đã huỷ</button>' +
    '<button class="btn gh" data-phb="excel" style="flex:1">📄 Xuất Excel</button></div>';

  frame('Phiếu hoàn đơn huỷ', html, { footer: foot });
  var o = document.getElementById('phTim');
  if (o) {
    o.onchange = function () { phTim = o.value.trim(); go(scrPhieuHoanHuy, true); };
    o.onkeydown = function (e) { if (e.key === 'Enter') { phTim = o.value.trim(); go(scrPhieuHoanHuy, true); } };
  }
  /* Nghe trên `root` chứ không trên thân màn: chân màn `.vf` là ANH EM của
     ô thân, không nằm trong nó. Xem bài học ở đầu 29-don-huy.js và ca kiểm
     `thu_chan_man.py`. */
  root.addEventListener('click', phBam);
}

/* Phần mở rộng: những gì bên kế toán đã làm, kèm nút tải uỷ nhiệm chi. */
function phChiTiet(r) {
  var d = function (nhan, gt) {
    if (!gt) return '';
    return '<div style="display:flex;gap:8px;font-size:12px;margin-top:3px">' +
      '<span style="color:#98a2b3;min-width:112px">' + nhan + '</span>' +
      '<span style="color:#344054">' + h(String(gt)) + '</span></div>';
  };
  var s = '<div style="margin-top:9px;padding:9px 10px;background:#f9fafb;' +
    'border:1px solid #eef0f3;border-radius:9px">';
  s += d('Mã phiếu hoàn', r.name);
  s += d('Lý do huỷ đơn', r.nhan_ly_do);
  s += d('Chuyển vào', (r.ten_tk || '') + (r.so_tk ? ' · ' + r.so_tk : '') +
    (r.ngan_hang ? ' · ' + r.ngan_hang : ''));
  s += d('Nội dung chuyển', r.noi_dung_ck);
  s += d('Phiếu chi', (r.phieu_chi || '(chưa có)') +
    (r.phieu_chi_da_ghi ? ' · đã ghi sổ' : (r.phieu_chi ? ' · còn nháp' : '')));
  s += d('Mã giao dịch', r.ma_gd);
  s += d('Đối soát lúc', r.ngay_doi_soat);
  s += d('Người lập', r.nguoi_duyet);
  if (r.ly_do_tu_choi) s += d('Từ chối vì', r.ly_do_tu_choi);
  if ((r.unc || []).length) {
    s += '<div style="margin-top:8px;display:flex;gap:7px;flex-wrap:wrap">';
    (r.unc || []).forEach(function (t) {
      s += '<a href="' + h(t.url) + '" target="_blank" rel="noopener" download ' +
        'style="display:inline-block;background:#fff;border:1.5px solid #12b76a;' +
        'color:#05603a;border-radius:9px;padding:6px 11px;font-size:12.5px;' +
        'text-decoration:none;font-weight:600">⬇️ Tải uỷ nhiệm chi</a>';
    });
    s += '</div>';
  } else {
    s += '<div style="margin-top:8px;font-size:12px;color:#b54708">Chưa có uỷ ' +
      'nhiệm chi. Kế toán tải từ e-banking về và đính vào phiếu chi thì nút ' +
      'tải sẽ hiện ở đây.</div>';
  }
  return s + '</div>';
}

async function phBam(ev) {
  var el;
  if ((el = ev.target.closest('a[href]'))) return;   // để nút tải tệp đi đường của nó
  if ((el = ev.target.closest('[data-phl]'))) {
    phLoc = el.getAttribute('data-phl');
    return go(scrPhieuHoanHuy, true);
  }
  if ((el = ev.target.closest('[data-phb]'))) {
    var v = el.getAttribute('data-phb');
    if (v === 'don') return go(scrDonHuy);
    if (v === 'excel') return phExcel();
  }
  if ((el = ev.target.closest('[data-phm]'))) {
    var k = el.getAttribute('data-phm');
    phMoRong[k] = !phMoRong[k];
    return go(scrPhieuHoanHuy, true);
  }
}

async function phExcel() {
  busy(1);
  var kq;
  try { kq = await api('vagabond.don_huy.xuat_excel_phieu', { trang_thai: phLoc, tim: phTim }); }
  catch (e) { busy(0); return toast(errMsg(e), 6000); }
  busy(0);
  if (!kq.tong_dong) return toast('Không có dòng nào để xuất.', 4000);
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

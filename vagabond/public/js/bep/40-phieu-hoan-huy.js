/* ---------------- Danh sách phiếu hoàn tiền, cửa sổ phía các điểm bán

   Anh Việt giao 31/08/2026, hai đợt.

   Đợt một: *"thêm nút để xem lại danh sách các phiếu hoàn cho đơn đã huỷ
   của pancake để sales theo dõi, nối các trạng thái, hồ sơ, uỷ nhiệm
   chi... tải UNC gửi khách"*.

   Đợt hai: *"màn danh mục phiếu hoàn tiền cash back lại chỉ có bên phân hệ
   kế toán mà không có ở bên phân hệ Bán hàng. Em làm thêm danh sách đó rồi
   gộp luôn vào... cho anh những chip lọc điểm bán... vì tương lai cả bên
   các điểm bán khác không chỉ bên Sales cũng cần làm những phiếu hoàn tiền
   này, họ cũng cần theo dõi."*

   VÌ SAO PHẢI CÓ MÀN NÀY
   ----------------------
   Người lập phiếu xong là mất dấu. Phần còn lại của việc - kế toán chuyển
   tiền, đính uỷ nhiệm chi, ghi sổ phiếu chi, khớp sao kê - đều nằm trong
   phân hệ Kế toán, mà v355 đã khoá phân hệ đó lại không cho nhân viên vào.
   Nên khách nhắn "tiền của em tới đâu rồi" là không ai có chỗ nhìn.

   Màn này là cửa sổ CHỈ ĐỌC mở về phía các điểm bán. Không có nhịp đồng bộ
   nào và cũng không có bảng thứ hai: nó đọc thẳng hồ sơ hoàn tiền và phiếu
   chi mà kế toán đang làm, nên kế toán bấm xong là mở màn ra thấy ngay.

   Uỷ nhiệm chi trả về ĐƯỜNG DẪN TỆP chứ không phải chỉ một cái dấu tích:
   thứ người bán cần là tải nó xuống gửi cho khách, đó là cả lý do có màn.

   BA HỌ CHIP: điểm bán, loại phiếu, trạng thái. Mỗi họ đếm trên tập đã lọc
   bởi hai họ kia, để bấm một chip xong thì số trên các chip còn lại vẫn nói
   đúng "bấm thêm cái này thì còn bao nhiêu".

   Ô tìm và chip đếm chạy Ở MÁY CHỦ (QT-19). Xem `don_huy.dieu_kien_tim`.

   Tiền tố ph = phiếu hoàn. Đã kiểm và chạm tên trước khi đặt (QT-28). */

var phDiem = '';       // chip điểm bán đang chọn, rỗng là tất cả
var phLoai = '';       // chip loại phiếu
var phLoc = '';        // chip trạng thái
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

/* Một hàng chip. `dsc` là danh sách {k, ten} máy chủ gửi xuống, `dem` là số
   đếm, `chon` là chip đang bật, `thuoc` là tên thuộc tính data-.
   Chip rỗng thì ẩn, để hàng chip không dài ra vì những nhóm chưa có phiếu
   nào. Riêng chip đang chọn thì luôn hiện dù đếm 0, nếu không bấm vào là nó
   biến mất và người ta không biết đường bấm lại. */
/* Mau cua tung HO chip. Anh Viet 31/08/2026: ba hang chip xep chong nhau ma
   hang nao cung xanh y het nhau thi nhin rat roi, khong biet minh dang loc
   theo cai gi.

   Chon mau theo NGHIA chu khong theo thu tu: diem ban la noi chon (chi lam),
   loai phieu la ban chat viec (tim), trang thai la buoc chay (xanh mong ket
   nhu moi man khac cua app). */
var PH_MAU_CHIP = { diem: '#4338ca', loai: '#b45309', tt: '#0d9488' };

function phHangChip(thuoc, dsc, dem, chon, nhan_tat_ca, mau) {
  var s = posChipNut(thuoc + '=""', (nhan_tat_ca || 'Tất cả') + ' · ' +
    (dem.tat_ca || 0), chon === '', 0, mau);
  (dsc || []).forEach(function (o) {
    var n = dem[o.k] || 0;
    if (!n && chon !== o.k) return;
    s += posChipNut(thuoc + '="' + h(o.k) + '"', o.ten + ' · ' + n, chon === o.k, 0, mau);
  });
  return '<div style="display:flex;gap:7px;flex-wrap:wrap;margin:7px 0">' + s + '</div>';
}

/* Một hàng nhãn nhỏ. Mỗi nhãn KHÔNG được gãy giữa chừng.

   Lỗi anh Việt bắt được 31/08/2026 trên điện thoại: nhãn "Có uỷ nhiệm chi"
   bị bẻ làm hai dòng, chữ "chi" rơi xuống dòng dưới nằm một mình. Gốc là
   các nhãn nằm trong một khối chữ thường, nên trình duyệt ngắt dòng theo
   TỪ chứ không theo nhãn.

   Hai thứ phải có: khối bọc là flex có `flex-wrap` để nhãn xuống dòng
   nguyên khối, và mỗi nhãn `white-space:nowrap` để không bao giờ gãy ruột.
   Màn hình điện thoại hẹp nên đây không phải ca hiếm, gần như dòng nào
   cũng dính. */
function phNhanHang(cac) {
  var s = '<div class="h2" style="display:flex;flex-wrap:wrap;gap:5px;margin-top:6px">';
  (cac || []).forEach(function (o) {
    if (!o) return;
    s += '<span style="background:' + o[1] + ';border:1px solid ' + o[2] + ';color:' + o[3] +
      ';border-radius:20px;padding:2px 9px;font-size:11.5px;white-space:nowrap;' +
      'display:inline-block;line-height:1.5">' + h(o[0]) + '</span>';
  });
  return s + '</div>';
}

/* Dây chuyền bốn bước, vẽ thành bốn chấm nối nhau. Cách nói này trả lời
   đúng câu khách hỏi, mà một dòng trạng thái đơn lẻ thì không: trạng thái
   nhảy sang "Đã chi" ngay lúc kế toán ghi sổ, nhưng thứ khách muốn là cái
   uỷ nhiệm chi. */
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
  frame('Danh sách phiếu hoàn tiền', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc danh sách...</div></div>');
  var kq;
  try {
    kq = await api('vagabond.don_huy.ds_phieu', {
      diem: phDiem, loai: phLoai, trang_thai: phLoc, tim: phTim,
    });
  } catch (e) {
    frame('Danh sách phiếu hoàn tiền', '<div class="emp"><div class="e1">⚠️</div><div>' +
      h(errMsg(e)) + '</div></div>');
    return;
  }
  var dong = kq.dong || [], buoc = kq.buoc || [];

  var html = '<div class="card" style="padding:12px 13px">' +
    '<div style="font-size:13px;color:#344054;line-height:1.6">' +
    'Phiếu hoàn tiền cho khách: đơn Pancake <b>đã huỷ</b>, đơn <b>đã ghi sổ</b> ' +
    'trả hàng, tiền khách <b>nộp thừa</b>. Kế toán làm tới đâu màn này hiện tới ' +
    'đó, không phải đi hỏi. Bấm vào một phiếu là thấy đủ chứng từ kế toán đã ' +
    'đính và ảnh bằng chứng, bấm vào hình là mở ra gửi khách được.</div>' +
    '<div style="margin-top:9px;display:flex;align-items:baseline;gap:8px">' +
    '<span style="font-size:12px;color:#8a8f9c">TIỀN ĐANG CHẠY</span>' +
    '<b style="font-size:19px;color:#b54708">' + money(kq.tien_dang_chay || 0) + ' đ</b></div>' +
    (kq.cho_unc ? '<div style="font-size:11.5px;color:#b3261e;margin-top:4px">' +
      kq.cho_unc + ' phiếu đang chờ kế toán chuyển tiền và đính uỷ nhiệm chi.</div>' : '') +
    (kq.treo_lau ? '<div style="margin-top:8px;padding:7px 9px;background:#fef2f2;' +
      'border:1px solid #fecaca;border-radius:8px;font-size:12.5px;color:#b3261e">' +
      '⚠️ <b>' + kq.treo_lau + ' phiếu treo quá ' + (kq.treo_ngay || 3) + ' ngày.</b> ' +
      'Tiền của khách vẫn đang nằm ở tiệm. Những phiếu này đã được đưa lên đầu ' +
      'danh sách.</div>' : '') +
    '</div>';

  html += phHangChip('data-phd', kq.diem, kq.dem_diem || {}, phDiem,
    'Mọi điểm bán', PH_MAU_CHIP.diem);
  html += phHangChip('data-phlo', kq.loai, kq.dem_loai || {}, phLoai,
    'Mọi loại phiếu', PH_MAU_CHIP.loai);
  html += phHangChip('data-phl', phDsTt(kq), kq.dem || {}, phLoc,
    'Mọi trạng thái', PH_MAU_CHIP.tt);

  html += '<div class="card" style="padding:9px 11px"><input id="phTim" type="search" ' +
    'placeholder="Tìm theo mã đơn, hoá đơn, tên khách, số tài khoản, mã phiếu" value="' + h(phTim) + '" ' +
    'style="width:100%;height:38px;border:1.5px solid #e4e7ec;border-radius:9px;' +
    'padding:0 10px;font-size:14px"></div>';

  html += '<div class="sec">' + dong.length + ' phiếu' +
    (kq.con_nua ? ' trên tổng ' + kq.tong_dong : '') +
    ' · bấm để xem chi tiết</div><div class="card">';
  if (!dong.length) {
    html += '<div class="emp" style="padding:24px"><div class="e1">📄</div>' +
      '<div>Chưa có phiếu hoàn nào trong nhóm này.</div></div>';
  }
  var ten_diem = {};
  (kq.diem || []).forEach(function (o) { ten_diem[o.k] = o.ten; });
  dong.forEach(function (r) {
    var m = phMau(r.trang_thai);
    var mo = !!phMoRong[r.name];
    html += '<div class="hub" data-phm="' + h(r.name) + '" style="align-items:flex-start' +
      (r.treo_lau ? ';background:#fffbfb;border-left:3px solid #b3261e' : '') + '">' +
      '<div class="hi">' + (r.treo_lau ? '⚠️' : ((r.buoc_xong || 0) >= 4 ? '✅' : '💸')) + '</div>' +
      '<div class="ht"><div class="h1">#' + h(r.ma_hien_thi || r.name) +
      ' · ' + h(r.ten_khach || 'Khách lẻ') + '</div>' +
      '<div class="h2">' + h(r.cau_tinh_hinh || '') +
      (r.treo_lau ? ' <b style="color:#b3261e">Treo ' + r.treo_ngay + ' ngày rồi.</b>' : '') +
      '</div>' +
      phDay(r, buoc) +
      phNhanHang([
        [r.nhan_trang_thai, m[0], m[1], m[2]],
        [r.nhan_loai, '#f8fafc', '#e2e8f0', '#475467'],
        [ten_diem[r.diem_ban] || 'Chưa rõ điểm bán', '#f8fafc', '#e2e8f0', '#475467'],
        /* Nhan noi dung so tep, khong tu xung la uy nhiem chi: may chu
           khong biet tep nao la uy nhiem chi (anh Viet 31/08/2026). */
        r.co_unc ? [(r.unc || []).length + ' chứng từ chi', '#ecfdf3', '#a6f4c5', '#05603a'] : null,
        (r.bang_chung || []).length ? [(r.bang_chung || []).length + ' ảnh bằng chứng',
          '#eff8ff', '#b2ddff', '#175cd3'] : null,
      ]) + (mo ? phChiTiet(r) : '') + '</div>' +
      '<div style="text-align:right;white-space:nowrap">' +
      '<b style="font-size:13.5px">' + money(r.so_tien) + '</b>' +
      '<div style="font-size:11px;color:#98a2b3">' + h(r.creation || '') + '</div></div></div>';
  });
  html += '</div>';

  var foot = '<button class="btn" data-phb="lap" style="width:100%;margin-bottom:8px">' +
    '➕ Lập phiếu hoàn tiền</button>' +
    '<div style="display:flex;gap:9px">' +
    '<button class="btn gh" data-phb="don" style="flex:1">↩️ Đơn đã huỷ</button>' +
    '<button class="btn gh" data-phb="excel" style="flex:1">📄 Xuất Excel</button></div>';

  frame('Danh sách phiếu hoàn tiền', html, { footer: foot });
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

/* Danh sách chip trạng thái. Nhãn do MÁY CHỦ gửi xuống, màn không tự chế
   bảng thứ hai: ngày 22/08/2026 sáu con chip đã hiện nguyên khoá không dấu
   ra cho người dùng đọc, đúng vì màn tự dựng danh sách bằng chuỗi khoá. */
function phDsTt(kq) {
  var thu_tu = ['Cho chi', 'Da chi', 'Da doi soat', 'Hoan thanh', 'Da huy'];
  var nhan = kq.nhan || {};
  return thu_tu.map(function (k) { return { k: k, ten: nhan[k] || k }; });
}

/* Phần mở rộng: những gì bên kế toán đã làm, kèm các tệp đã đính.

   BỐ CỤC DÒNG (anh Việt 31/08/2026, kèm CSS anh gửi)
   --------------------------------------------------
   Mỗi dòng là một hàng flex: cột nhãn khoá cứng 118px, cột giá trị ăn hết
   phần còn lại và tự ngắt dòng thông minh. Giữa hai dòng có một nét đứt mờ
   để mắt dóng ngang được. Bản cũ để hai cột trôi tự do nên mã dài đẩy nhãn
   lệch đi, nhìn như thụt lề bậy.

   Khoá 118px chứ không phải 130px như CSS anh gửi: màn hình điện thoại hẹp
   nhất mà nhân viên đang dùng rộng 320px, trừ đệm hai bên còn 276px, để
   130px thì cột giá trị chỉ còn 134px và mã hoá đơn nào cũng gãy làm ba
   dòng. Đã đo trên đúng khổ đó rồi mới chốt con số.

   TỆP ĐÍNH KÈM (anh Việt 31/08/2026)
   ----------------------------------
   *"Các nút tải thì cả 3 nút đều ghi là tải uỷ nhiệm chi nhưng nhấn vào lại
   ra ảnh bằng chứng, ảnh đơn hàng... mọi tệp đính kèm phải trình bày dạng
   thumbnail, không để nút tải như thế."*

   Nay ảnh vẽ thành hình thu nhỏ bấm được, tệp khác vẽ thành một ô vuông
   mang đúng ĐUÔI TỆP và tên thật ở dưới. Không con nút nào tự xưng là uỷ
   nhiệm chi nữa: máy chủ không biết tệp nào là uỷ nhiệm chi, và đoán sai
   thì người đọc tin nhầm. */
function phDong(nhan, gt) {
  if (!gt) return '';
  return '<div style="display:flex;align-items:flex-start;padding-bottom:8px;' +
    'margin-bottom:8px;border-bottom:1px dashed #e6e8ec">' +
    '<span style="flex:0 0 118px;color:#98a2b3;font-size:12px;line-height:1.5;' +
    'padding-right:10px">' + h(nhan) + '</span>' +
    '<span style="flex:1;color:#344054;font-size:12.5px;font-weight:500;' +
    'line-height:1.5;word-break:break-word;overflow-wrap:break-word">' +
    h(String(gt)) + '</span></div>';
}

/* Một ô tệp: ảnh thì hiện hình, tệp khác thì hiện đuôi. Cả hai đều mở được
   trong thẻ mới, và đều mang tên thật ở dưới để biết mình sắp mở cái gì. */
function phOTep(t) {
  var ten = String(t.ten || 'tệp');
  var o = '<a href="' + h(t.url) + '" target="_blank" rel="noopener" ' +
    'title="' + h(ten) + '" style="display:block;width:88px;text-decoration:none">';
  if (t.anh) {
    o += '<img src="' + h(t.url) + '" alt="' + h(ten) + '" loading="lazy" ' +
      'style="width:88px;height:88px;object-fit:cover;border-radius:9px;' +
      'border:1px solid #e4e7ec;background:#f8fafc;display:block">';
  } else {
    o += '<div style="width:88px;height:88px;border-radius:9px;border:1px solid #e4e7ec;' +
      'background:#f8fafc;display:flex;align-items:center;justify-content:center;' +
      'color:#475467;font-size:13px;font-weight:800;letter-spacing:.5px">' +
      h(t.duoi || 'TỆP') + '</div>';
  }
  o += '<div style="font-size:10.5px;color:#667085;margin-top:4px;line-height:1.35;' +
    'word-break:break-word">' + h(ten.length > 34 ? ten.slice(0, 32) + '…' : ten) +
    '</div></a>';
  return o;
}

function phLuoiTep(tieu_de, cac, khi_trong) {
  if (!(cac || []).length) {
    return khi_trong ? '<div style="margin-top:8px;font-size:12px;color:#b54708">' +
      h(khi_trong) + '</div>' : '';
  }
  return '<div style="margin-top:10px">' +
    '<div style="font-size:11.5px;font-weight:700;color:#667085;margin-bottom:6px;' +
    'text-transform:uppercase;letter-spacing:.3px">' + h(tieu_de) + '</div>' +
    '<div style="display:flex;gap:9px;flex-wrap:wrap">' +
    cac.map(phOTep).join('') + '</div></div>';
}

function phChiTiet(r) {
  var s = '<div style="margin-top:9px;padding:11px 12px;background:#f9fafb;' +
    'border:1px solid #eef0f3;border-radius:9px">';
  s += phDong('Mã phiếu hoàn', r.name);
  s += phDong('Loại phiếu', r.nhan_loai);
  s += phDong('Hoá đơn gốc', r.hoa_don);
  s += phDong('Số hoá đơn điện tử', r.so_hddt);
  s += phDong('Mã đơn Pancake', r.ma_don_pancake);
  s += phDong('Lý do', r.nhan_ly_do);
  s += phDong('Diễn giải', r.dien_giai);
  s += phDong('Chuyển vào', (r.ten_tk || '') + (r.so_tk ? ' · ' + r.so_tk : '') +
    (r.ngan_hang ? ' · ' + r.ngan_hang : ''));
  s += phDong('Nội dung chuyển', r.noi_dung_ck);
  s += phDong('Phiếu thu', r.phieu_thu);
  s += phDong('Phiếu chi', (r.phieu_chi || '(chưa có)') +
    (r.phieu_chi_da_ghi ? ' · đã ghi sổ' : (r.phieu_chi ? ' · còn nháp' : '')));
  s += phDong('Mã giao dịch', r.ma_gd);
  s += phDong('Đối soát lúc', r.ngay_doi_soat);
  s += phDong('Người lập', r.nguoi_duyet);
  if (r.ly_do_tu_choi) s += phDong('Từ chối vì', r.ly_do_tu_choi);
  s += phLuoiTep('Chứng từ kế toán đính trên phiếu chi', r.unc,
    'Kế toán chưa đính chứng từ chi nào. Có uỷ nhiệm chi rồi thì nó hiện ở đây, ' +
    'bấm vào là mở ra gửi khách được.');
  s += phLuoiTep('Ảnh bằng chứng người lập đính', r.bang_chung, '');
  return s + '</div>';
}

async function phBam(ev) {
  var el;
  if (ev.target.closest('a[href]')) return;   // để nút tải tệp đi đường của nó
  if ((el = ev.target.closest('[data-phd]'))) {
    phDiem = el.getAttribute('data-phd');
    return go(scrPhieuHoanHuy, true);
  }
  if ((el = ev.target.closest('[data-phlo]'))) {
    phLoai = el.getAttribute('data-phlo');
    return go(scrPhieuHoanHuy, true);
  }
  if ((el = ev.target.closest('[data-phl]'))) {
    phLoc = el.getAttribute('data-phl');
    return go(scrPhieuHoanHuy, true);
  }
  if ((el = ev.target.closest('[data-phb]'))) {
    var v = el.getAttribute('data-phb');
    if (v === 'don') return go(scrDonHuy);
    if (v === 'lap') return go(scrPhLap);
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
  try {
    kq = await api('vagabond.don_huy.xuat_excel_phieu', {
      diem: phDiem, loai: phLoai, trang_thai: phLoc, tim: phTim,
    });
  } catch (e) { busy(0); return toast(errMsg(e), 6000); }
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

/* ---------------- Lập phiếu hoàn tiền, chọn đường rồi chọn đơn

   Anh Việt duyệt 31/08/2026: các điểm bán phải TỰ LẬP được phiếu hoàn chứ
   không chỉ ngồi xem. Trước đây muốn lập thì phải đi qua màn hoá đơn hoặc
   nhờ kế toán, mà phân hệ Kế toán thì nhân viên không vào được.

   MÀN NÀY KHÔNG LẬP PHIẾU. Nó chỉ dẫn người ta tới đúng cửa cũ. Bốn luồng
   hoàn tiền đã có đủ hàng rào ở máy chủ: trần số tiền, bắt buộc ảnh bằng
   chứng, chặn hoàn quá số khách đã chuyển, chặn lập trùng. Mở thêm một cửa
   thứ hai cho tiền ra là mở thêm một chỗ để sai. */

var phlDiem = '';      // điểm bán đang chọn
var phlKieu = '';      // đường đang chọn
var phlTim = '';

var PHL_KIEU = [
  ['tra', '↩️', 'Khách trả hàng', 'Đơn ĐÃ ghi sổ, khách trả lại bánh. Máy lập hoá đơn trả hàng để khử doanh thu.'],
  ['huy', '🚫', 'Khách huỷ đơn chưa ghi sổ', 'Khách đã chuyển tiền rồi báo huỷ, đơn còn nháp. Không đụng doanh thu.'],
  ['du', '💰', 'Khách nộp thừa', 'Khách chuyển dư so với tổng đơn. Chỉ trả lại phần dư.'],
  ['pancake', '📦', 'Đơn Pancake đã huỷ', 'Đơn huỷ bên Pancake, chưa bao giờ về hệ. Đi qua màn Đơn đã huỷ.'],
];

async function scrPhLap() {
  var html = '<div class="card" style="padding:12px 13px">' +
    '<div style="font-size:13px;color:#344054;line-height:1.6">' +
    'Chọn đúng loại việc trước, rồi chọn đơn. Máy sẽ tự kiểm xem đơn đó có ' +
    'hoàn được không và hoàn được tối đa bao nhiêu.</div></div>';

  html += '<div class="sec">Điểm bán</div>';
  /* Doc thang danh muc diem ban, KHONG goi lai man danh sach phieu chi de
     lay ten chip: man do doc het so phieu, ma o day chi can ba cai ten. */
  var dsd = [];
  try {
    var kq = await api('vagabond.diem_ban.danh_sach', {});
    dsd = (kq.diem || []).filter(function (o) { return o.bat; })
      .map(function (o) { return { k: o.ma, ten: o.ten_ngan || o.ten }; });
  } catch (e) { dsd = []; }
  var sc = posChipNut('data-phld=""', 'Mọi điểm bán', phlDiem === '');
  dsd.forEach(function (o) {
    sc += posChipNut('data-phld="' + h(o.k) + '"', o.ten, phlDiem === o.k);
  });
  html += '<div style="display:flex;gap:7px;flex-wrap:wrap;margin:7px 0">' + sc + '</div>';

  html += '<div class="sec">Loại việc</div><div class="card">';
  PHL_KIEU.forEach(function (k) {
    html += '<div class="hub" data-phlk="' + k[0] + '" style="align-items:flex-start">' +
      '<div class="hi">' + k[1] + '</div>' +
      '<div class="ht"><div class="h1">' + k[2] +
      (phlKieu === k[0] ? ' <span style="color:#12b76a">✓</span>' : '') + '</div>' +
      '<div class="h2" style="line-height:1.5">' + k[3] + '</div></div></div>';
  });
  html += '</div>';

  if (phlKieu && phlKieu !== 'pancake') {
    html += '<div class="card" style="padding:9px 11px"><input id="phlTim" type="search" ' +
      'placeholder="Tìm hoá đơn theo mã, tên khách, số hoá đơn điện tử" value="' + h(phlTim) + '" ' +
      'style="width:100%;height:38px;border:1.5px solid #e4e7ec;border-radius:9px;' +
      'padding:0 10px;font-size:14px"></div>';
    var d = { dong: [] };
    try { d = await api('vagabond.don_huy.tim_don_de_hoan', { diem: phlDiem, tim: phlTim }); }
    catch (e) { d = { dong: [] }; }
    html += '<div class="sec">' + (d.dong || []).length + ' đơn · bấm để lập phiếu</div><div class="card">';
    if (!(d.dong || []).length) {
      html += '<div class="emp" style="padding:20px"><div class="e1">🔍</div>' +
        '<div>Không thấy đơn nào. Gõ mã đơn hoặc tên khách vào ô tìm.</div></div>';
    }
    (d.dong || []).forEach(function (r) {
      html += '<div class="hub" data-phlo="' + h(r.name) + '">' +
        '<div class="hi">🧾</div>' +
        '<div class="ht"><div class="h1">' + h(r.name) + ' · ' + h(r.customer_name || 'Khách lẻ') + '</div>' +
        '<div class="h2">' + h(r.posting_date || '') +
        (r.da_ghi_so ? ' · đã ghi sổ' : ' · còn nháp') +
        (r.custom_hddt_so ? ' · hoá đơn ' + h(r.custom_hddt_so) : '') + '</div>' +
        (r.da_co_phieu ? '<div class="h2" style="color:#b54708;margin-top:3px">' +
          'Đơn này đã có phiếu hoàn rồi.</div>' : '') +
        '</div>' +
        '<div style="text-align:right;white-space:nowrap"><b style="font-size:13.5px">' +
        money(r.grand_total) + '</b></div></div>';
    });
    html += '</div>';
  }

  var foot = '<button class="btn gh" data-phlb="ve" style="width:100%">' +
    '← Về danh sách phiếu hoàn</button>';
  frame('Lập phiếu hoàn tiền', html, { footer: foot });
  var o = document.getElementById('phlTim');
  if (o) {
    o.onchange = function () { phlTim = o.value.trim(); go(scrPhLap, true); };
    o.onkeydown = function (e) { if (e.key === 'Enter') { phlTim = o.value.trim(); go(scrPhLap, true); } };
  }
  root.addEventListener('click', phlBam);
}

async function phlBam(ev) {
  var el;
  if ((el = ev.target.closest('[data-phld]'))) {
    phlDiem = el.getAttribute('data-phld');
    return go(scrPhLap, true);
  }
  if ((el = ev.target.closest('[data-phlk]'))) {
    var k = el.getAttribute('data-phlk');
    if (k === 'pancake') return go(scrDonHuy);
    phlKieu = k;
    return go(scrPhLap, true);
  }
  if ((el = ev.target.closest('[data-phlo]'))) {
    return phlMoForm(el.getAttribute('data-phlo'));
  }
  if ((el = ev.target.closest('[data-phlb]'))) return go(scrPhieuHoanHuy);
}

/* Mở đúng form cũ của luồng hoàn tiền. Ba form này đều tự hỏi máy chủ xem
   đơn có hoàn được không rồi mới cho gõ, nên ở đây chỉ cần đưa mã đơn. */
function phlMoForm(ma) {
  var don = { name: ma, grand_total: 0, custom_hddt_so: '' };
  if (phlKieu === 'tra') return hoanMoForm(don);
  if (phlKieu === 'huy') return hoanMoFormHuy(don);
  if (phlKieu === 'du') return hoanMoFormDu(don);
  return toast('Chọn loại việc trước đã.', 4000);
}

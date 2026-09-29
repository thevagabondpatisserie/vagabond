/* ---------------- Duyệt đơn hàng tặng, phân hệ Kế toán

   Anh Việt giao 31/08/2026:

     *"Anh đang muốn làm thêm 1 phương thức thanh toán nữa là 'Hàng tặng'.
     Máy sẽ cho ghi sổ mà không cần đối soát, xuất hoá đơn nguyên giá sản
     phẩm và ghi trên hoá đơn ở phần ghi chú khi xuất hoá đơn. Nhưng với
     những đơn chọn phương thức này thì em cho anh luồng gửi giám đốc duyệt
     đơn được không để tránh gian lận. Lập 1 màn duyệt đơn tặng bên phân hệ
     kế toán để anh vào duyệt thì đơn sẽ để đó chờ ghi sổ."*

   MÀN NÀY LÀ CỬA CHẶN, KHÔNG PHẢI MÀN THÔNG BÁO
   ---------------------------------------------
   Đơn trả bằng Hàng tặng KHÔNG ghi sổ được cho tới khi có người bấm Duyệt ở
   đây. Chặn thật nằm ở máy chủ (`hang_tang.truoc_khi_ghi_so`), màn này chỉ
   là chỗ bấm. Giấu nút đi không phải là chặn.

   DUYỆT THÌ PHẢI THẤY MÌNH ĐANG DUYỆT CÁI GÌ
   ------------------------------------------
   Bấm vào một đơn là mở ra từng dòng hàng, kèm con số "người lập này đã
   tặng bao nhiêu trong tháng". Không có hai thứ đó thì duyệt chỉ là bấm một
   cái nút, mà cả hàng rào này sinh ra để không phải bấm mù.

   Ô tìm và chip đếm chạy Ở MÁY CHỦ (QT-19).

   Tiền tố dtg = duyệt tặng. Đã kiểm và chạm tên trước khi đặt (QT-28). */

var dtgDiem = '';      // chip điểm bán đang chọn, rỗng là tất cả
var dtgChang = '';     // chip chặng (v534): cho_duyet, cho_ghi_so, hoan_tat, tu_choi
var dtgKy = '';        // chip ngày (v534), khoá theo DS_KY ở 15-khuon-danh-sach.js
var dtgTu = '';        // hai ô ngày khi chọn Tuỳ chọn
var dtgDen = '';
var dtgLoai = '';      // chip loại tặng
var dtgTim = '';       // ô tìm
var dtgMo = {};        // mã đơn nào đang mở rộng
var dtgChiTiet = {};   // chi tiết đã đọc về, khỏi hỏi lại máy chủ

function dtgMauTt(tt) {
  if (tt === 'Chờ duyệt') return ['#fffbeb', '#fcd34d', '#92400e'];
  if (tt === 'Đã duyệt') return ['#ecfdf3', '#a6f4c5', '#05603a'];
  if (tt === 'Từ chối') return ['#fef2f2', '#fecaca', '#b3261e'];
  return ['#f8fafc', '#e2e8f0', '#64748b'];
}

/* v534: bốn họ chip (chặng, điểm bán, loại tặng, ngày), ô tìm và nút Excel
   vẽ bằng thanh công cụ dùng chung `dsCongCu` (15-khuon-danh-sach.js). Hàm
   vẽ chip riêng của màn này bỏ đi, để màn tặng không lệch khỏi mọi màn khác. */
function dtgLoc() {
  return { diem: dtgDiem, chang: dtgChang, loai: dtgLoai, tim: dtgTim, ky: dtgKy, tu: dtgTu, den: dtgDen };
}

/* Nhãn nhỏ, mỗi nhãn không được gãy giữa chừng trên màn hình hẹp. Cùng bài
   học với `phNhanHang` ở màn phiếu hoàn (anh Việt bắt được 31/08/2026). */
function dtgNhan(cac) {
  var s = '<div class="h2" style="display:flex;flex-wrap:wrap;gap:5px;margin-top:6px">';
  (cac || []).forEach(function (o) {
    if (!o) return;
    s += '<span style="background:' + o[1] + ';border:1px solid ' + o[2] + ';color:' + o[3] +
      ';border-radius:20px;padding:2px 9px;font-size:11.5px;white-space:nowrap;' +
      'display:inline-block;line-height:1.5">' + h(o[0]) + '</span>';
  });
  return s + '</div>';
}

var DTG_TEN = 'Hàng tặng: duyệt và sổ đơn';

/* Cấu hình thanh công cụ cho màn này: đọc thẳng số đếm máy chủ trả về. */
function dtgCongCu(kq) {
  var tong = (kq.dem_chang || {}).tat_ca || 0;
  return {
    ma: 'dtg',
    chang: { ds: kq.cac_chang || [], dem: kq.dem_chang || {}, chon: dtgChang, tatCa: 'Mọi chặng' },
    ho: [
      { k: 'diem', ds: kq.diem || [], dem: kq.dem_diem || {}, chon: dtgDiem, tatCa: 'Mọi điểm bán', mau: '#4338ca' },
      { k: 'loai', ds: kq.loai || [], dem: kq.dem_loai || {}, chon: dtgLoai, tatCa: 'Mọi loại tặng', mau: '#b45309' },
    ],
    ky: { chon: dtgKy, tu: dtgTu, den: dtgDen },
    tim: { gt: dtgTim, goiY: 'Tìm mã đơn, tên khách, lý do' },
    xuat: { man: 'hang_tang', so: kq.tong_dong != null ? kq.tong_dong : tong, loc: dtgLoc },
  };
}

async function scrDuyetTang() {
  frame(DTG_TEN, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc danh sách...</div></div>');
  var kq;
  try {
    kq = await api('vagabond.hang_tang.ds_don', dtgLoc());
  } catch (e) {
    frame(DTG_TEN, '<div class="emp"><div class="e1">⚠️</div><div>' +
      h(errMsg(e)) + '</div></div>');
    return;
  }
  var dong = kq.dong || [];

  var html = '<div class="card" style="padding:12px 13px">' +
    '<div style="font-size:13px;color:#344054;line-height:1.6">' +
    /* v534: lời giải thích thu về hai dòng (AGENTS mục 2b điều 17), khối
       chỉ để đọc không được đẩy thanh công cụ xuống khỏi màn đầu. */
    'Đơn tặng không thu tiền, hoá đơn xuất <b>nguyên giá</b>. ' +
    'Chỉ ghi sổ sau khi giám đốc duyệt.' +
    '</div>' +
    '<div style="margin-top:9px;display:flex;gap:18px;flex-wrap:wrap">' +
    '<div><div style="font-size:12px;color:#8a8f9c">ĐANG CHỜ DUYỆT</div>' +
    '<b style="font-size:19px;color:#b54708">' + money(kq.tien_cho || 0) + ' đ</b></div>' +
    '<div><div style="font-size:12px;color:#8a8f9c">ĐÃ DUYỆT, CHỜ GHI SỔ</div>' +
    '<b style="font-size:19px;color:#05603a">' + money(kq.tien_duyet || 0) + ' đ</b></div>' +
    '</div>' +
    (kq.thieu_tai_khoan ? '<div style="margin-top:9px;padding:7px 9px;background:#fef2f2;' +
      'border:1px solid #fecaca;border-radius:8px;font-size:12.5px;color:#b3261e">' +
      '⚠️ <b>Chưa khai Tài khoản chi phí biếu tặng trong Cài đặt.</b> Duyệt được ' +
      'nhưng đơn vẫn chưa ghi sổ được, vì máy không biết hạch toán phần tặng vào ' +
      'đâu. Nhờ anh Việt và chị Dung chọn tài khoản trước.</div>' : '') +
    (kq.duyet_duoc ? '' : '<div style="margin-top:9px;padding:7px 9px;background:#f8fafc;' +
      'border:1px solid #e2e8f0;border-radius:8px;font-size:12.5px;color:#475467">' +
      'Bạn xem được danh sách nhưng không duyệt được. Chỉ Giám đốc mới duyệt, để ' +
      'người tặng và người duyệt không phải là một người.</div>') +
    '</div>';

  /* Ba họ chip ba màu, cùng bảng màu với màn Danh sách phiếu hoàn tiền:
     ba hàng xếp chồng mà cùng một màu thì không biết mình đang lọc theo
     cái gì. Anh Việt nhắc 31/08/2026. */
  var cc = dtgCongCu(kq);
  html += dsCongCu(cc);

  html += '<div class="sec">' + dong.length + ' đơn' +
    (kq.con_nua ? ' trên tổng ' + kq.tong_dong : '') +
    ' · bấm để xem từng món</div><div class="card">';
  if (!dong.length) {
    html += '<div class="emp" style="padding:24px"><div class="e1">🎁</div>' +
      '<div>Không có đơn hàng tặng nào trong nhóm này.</div></div>';
  }
  var tenDiem = {};
  (kq.diem || []).forEach(function (o) { tenDiem[o.k] = o.ten; });
  dong.forEach(function (r) {
    var tt = r.vgb_tang_duyet || 'Chờ duyệt';
    var m = dtgMauTt(tt);
    var mo = !!dtgMo[r.name];
    html += '<div class="hub" data-dtgm="' + h(r.name) + '" style="align-items:flex-start' +
      (r.cho_lau ? ';background:#fffbfb;border-left:3px solid #b3261e' : '') + '">' +
      '<div class="hi">' + (r.da_ghi_so ? '✅' : (r.cho_lau ? '⚠️' : '🎁')) + '</div>' +
      '<div class="ht"><div class="h1">' +
      h(r.custom_pancake_display_id ? '#' + r.custom_pancake_display_id : r.name) +
      ' · ' + h(r.customer_name || 'Khách lẻ') + '</div>' +
      '<div class="h2">' + h(r.vgb_tang_ly_do || 'Chưa ghi lý do') + '</div>' +
      dtgNhan([
        [tt, m[0], m[1], m[2]],
        [r.nhan_loai, '#f8fafc', '#e2e8f0', '#475467'],
        [tenDiem[r.diem_ban] || 'Chưa rõ điểm bán', '#f8fafc', '#e2e8f0', '#475467'],
        r.da_ghi_so ? ['Đã ghi sổ', '#ecfdf3', '#a6f4c5', '#05603a'] : null,
        r.cho_lau ? ['Chờ ' + r.cho_ngay + ' ngày', '#fef2f2', '#fecaca', '#b3261e'] : null,
      ]) + '</div>' +
      '<div style="text-align:right;white-space:nowrap">' +
      '<b style="font-size:13.5px">' + money(r.grand_total) + '</b>' +
      '<div style="font-size:11px;color:#98a2b3">' + h(r.creation || '') + '</div></div></div>' +
      /* Khoi chi tiet nam NGOAI hang bam, chiem ca chieu ngang man hinh.
         Truoc 02/09/2026 no nam trong cot chu cua hang, tuc la bi ep giua
         cai bieu tuong ben trai va cot tien ben phai; tren dien thoai cot
         do con chung ba muoi ky tu nen chu xuong dong tung chu mot. Anh
         Viet gui anh chup: "no dang bi ep dong".
         Nam ngoai con duoc mot cai loi thu hai: bam vao trong phan chi
         tiet khong con lam dong sap hang lai. */
      (mo ? dtgThan(r, kq) : '');
  });
  html += '</div>';

  var than = frame(DTG_TEN, html, {
    footer: '<button class="btn gh" data-dtgbc="1" style="width:100%;margin:0">' +
      '📊 Báo cáo hàng tặng</button>',
  });
  dsCongCuNoi(than, cc, function (ho, k) {
    if (ho === 'chang') dtgChang = k;
    else if (ho === 'diem') dtgDiem = k;
    else if (ho === 'loai') dtgLoai = k;
    else if (ho === 'ky') { dtgKy = k; if (k !== 'tuy_chon') { dtgTu = ''; dtgDen = ''; } }
    else if (ho === 'tu') dtgTu = k;
    else if (ho === 'den') dtgDen = k;
    else if (ho === 'tim') dtgTim = k;
    go(scrDuyetTang, true);
  });
  /* Nghe trên `root` chứ không trên thân màn, xem bài học ở đầu 29-don-huy.js
     và ca kiểm `thu_chan_man.py`. */
  root.addEventListener('click', dtgBam);
}

/* Phần mở rộng của một đơn: từng món, và hai nút quyết. */
function dtgThan(r, kq) {
  var ct = dtgChiTiet[r.name];
  var s = '<div style="margin-top:9px;padding:9px 10px;background:#f9fafb;' +
    'border:1px solid #eef0f3;border-radius:9px">';
  /* `flex-shrink:0` cho o nhan va `min-width:0` cho o gia tri la hai nua
     cua cung mot viec: khong co chung thi trinh duyet co the bop o gia tri
     xuong con vai ky tu roi be chu xuong dong tung chu mot. */
  var d = function (nhan, gt, dam) {
    if (!gt && gt !== 0) return '';
    return '<div style="display:flex;gap:8px;font-size:12px;margin-top:3px;' +
      'align-items:baseline">' +
      '<span style="color:#98a2b3;flex:0 0 auto;min-width:112px">' + nhan + '</span>' +
      '<span style="color:' + (dam ? '#0f766e;font-weight:700' : '#344054') +
      ';flex:1;min-width:0;word-break:break-word">' + h(String(gt)) +
      '</span></div>';
  };
  if (!ct) {
    s += '<div style="font-size:12.5px;color:#98a2b3">Đang đọc từng món...</div>';
    return s + '</div>';
  }
  s += '<div style="font-size:12.5px;font-weight:700;color:#475467;margin-bottom:5px">' +
    'Đang tặng những món này</div>';
  (ct.mon || []).forEach(function (x) {
    s += '<div style="display:flex;justify-content:space-between;gap:10px;' +
      'font-size:12.5px;padding:3px 0;border-bottom:1px solid #eef0f3">' +
      '<span style="color:#344054">' + h(x.item_name || x.item_code) +
      ' <span style="color:#98a2b3">x' + (x.qty || 0) + '</span></span>' +
      '<b style="white-space:nowrap">' + money(x.amount) + '</b></div>';
  });
  /* Anh chung minh, ve thanh hinh thu nho. Duyet mot don den bu ma khong
     thay cai banh hong thi chi la bam mot cai nut. */
  if ((ct.anh || []).length) {
    s += '<div style="margin-top:9px;display:flex;gap:8px;flex-wrap:wrap">' +
      (ct.anh || []).map(function (a) {
        return '<a href="' + h(a.url) + '" target="_blank" rel="noopener" ' +
          'title="' + h(a.ten || '') + '" style="display:block">' +
          '<img src="' + h(a.url) + '" alt="' + h(a.ten || 'ảnh') + '" loading="lazy" ' +
          'style="width:82px;height:82px;object-fit:cover;border-radius:9px;' +
          'border:1px solid #e4e7ec;background:#f8fafc;display:block"></a>';
      }).join('') + '</div>';
  } else if (ct.can_anh) {
    s += '<div style="margin-top:9px;padding:7px 9px;background:#fef2f2;' +
      'border:1px solid #fecaca;border-radius:8px;font-size:12px;color:#b3261e">' +
      'Đơn <b>Đền bù sự cố</b> chưa có ảnh chứng minh nên chưa duyệt được. ' +
      'Nhờ người lập đính ảnh vào đơn rồi bấm lưu lại.</div>';
  }
  s += d('Mã đơn', r.name);
  /* So hoa don dien tu da xuat cho chinh don nay. Anh Viet 02/09/2026:
     duyet xong van phai doi chieu voi to hoa don that, de o day thi khong
     phai mo them man khac de tra. Chua xuat thi noi thang la chua xuat,
     dung de o trong cho nguoi ta doan. */
  s += d('Số hoá đơn đã xuất',
    ct.custom_hddt_so
      ? (ct.custom_hddt_so + (ct.custom_hddt_trang_thai ? ' · ' + ct.custom_hddt_trang_thai : ''))
      : 'Chưa xuất hoá đơn điện tử',
    !!ct.custom_hddt_so);
  s += d('Loại tặng', ct.nhan_loai);
  s += d('Lý do tặng', ct.vgb_tang_ly_do);
  s += d('Người lập', ct.owner_ten || ct.owner);
  s += d('Người duyệt', ct.vgb_tang_nguoi_duyet_ten || r.vgb_tang_nguoi_duyet);
  s += d('Duyệt lúc', r.vgb_tang_luc_duyet);
  s += d('Ý kiến người duyệt', r.vgb_tang_y_kien);
  s += d('Bút toán gạt công nợ', r.vgb_but_toan_tang);
  /* Con số này là thứ giám đốc cần nhất trước khi bấm: một đơn 200 nghìn
     nhìn vô hại, nhưng là đơn thứ mười hai của cùng một người trong tháng
     thì câu chuyện khác hẳn. Cố ý KHÔNG chặn cứng theo hạn mức: đặt hạn
     mức bao nhiêu là quyết định của anh Việt, máy không đặt hộ. */
  if (ct.thang_nay) {
    s += '<div style="margin-top:8px;padding:6px 8px;background:#fffbeb;' +
      'border:1px solid #fcd34d;border-radius:8px;font-size:12px;color:#92400e">' +
      'Người lập này đã lập <b>' + (ct.thang_nay.so || 0) + ' đơn tặng</b> trong tháng, ' +
      'tổng <b>' + money(ct.thang_nay.tien || 0) + ' đ</b>.</div>';
  }
  s += '<div style="margin-top:10px"><button class="btn gh" data-dtgbill="' + h(r.name) +
    '" style="width:100%;margin:0;min-height:44px">🧾 Xem lại bill</button></div>';
  if (kq.duyet_duoc && !r.da_ghi_so && (r.vgb_tang_duyet || 'Chờ duyệt') !== 'Đã duyệt') {
    s += '<div style="display:flex;gap:9px;margin-top:10px">' +
      '<button class="btn gh" data-dtgtc="' + h(r.name) + '" style="flex:1;margin:0">✖️ Từ chối</button>' +
      '<button class="btn" data-dtgok="' + h(r.name) + '" style="flex:2;margin:0">✅ Duyệt đơn</button></div>';
  } else if (kq.duyet_duoc && !r.da_ghi_so && r.vgb_tang_duyet === 'Đã duyệt') {
    s += '<div style="margin-top:10px"><button class="btn gh" data-dtgtc="' + h(r.name) +
      '" style="width:100%;margin:0">✖️ Rút lại, từ chối đơn này</button></div>';
  }
  return s + '</div>';
}

async function dtgBam(ev) {
  var t;
  if (ev.target.closest('[data-dtgbc]')) return go(scrTangBaoCao);

  /* Sales Manager 28/09/2026: đơn tặng xong rồi vẫn phải mở lại được đúng
     tờ bill để tra, không phải đi tìm ở màn khác. */
  t = ev.target.closest('[data-dtgbill]');
  if (t) { var maB = t.getAttribute('data-dtgbill'); return go(function () { return scrPosBill(maB); }); }

  t = ev.target.closest('[data-dtgok]');
  if (t) {
    var ma = t.getAttribute('data-dtgok');
    var y = await hoiChu('Duyệt đơn hàng tặng',
      'Duyệt sẽ đổi đơn nháp sang hôm nay, ghi sổ và gửi phát hành theo cấu hình. Nếu kẹt, máy giữ quyết định duyệt và báo rõ lý do. Ghi thêm ý kiến nếu cần.',
      '', { nhieu_dong: 1, goi_y: 'Ví dụ: đồng ý tặng, trừ vào ngân sách marketing tháng 8' });
    if (y === null) return;
    try {
      var kq = await api('vagabond.hang_tang.duyet', { name: ma, y_kien: y || '' });
      if (kq.loi) await baoTin(kq.loi, 'Kết quả duyệt hàng tặng');
      else if (kq.thong_bao) await baoTin(kq.thong_bao, 'Đã ghi sổ, chờ phát hành');
      else toast(kq.xuat_hddt ? 'Đã duyệt, ghi sổ và gửi phát hành HĐĐT.' : 'Đã duyệt.');
    } catch (e) { return baoTin(errMsg(e), 'Không duyệt được'); }
    delete dtgChiTiet[ma];
    return go(scrDuyetTang, true);
  }

  t = ev.target.closest('[data-dtgtc]');
  if (t) {
    var maTc = t.getAttribute('data-dtgtc');
    var ly = await hoiChu('Từ chối đơn hàng tặng',
      'Ghi rõ vì sao từ chối, để người lập biết đường sửa.',
      '', { nhieu_dong: 1, bat_buoc: 1, goi_y: 'Ví dụ: đơn quá lớn, chưa ai đồng ý, tặng sai đối tượng' });
    if (ly === null) return;
    try {
      await api('vagabond.hang_tang.tu_choi', { name: maTc, ly_do: ly });
    } catch (e) { return baoTin(errMsg(e), 'Không từ chối được'); }
    delete dtgChiTiet[maTc];
    return go(scrDuyetTang, true);
  }

  t = ev.target.closest('[data-dtgm]');
  if (t) {
    var maM = t.getAttribute('data-dtgm');
    if (dtgMo[maM]) { delete dtgMo[maM]; return go(scrDuyetTang, true); }
    dtgMo[maM] = 1;
    if (!dtgChiTiet[maM]) {
      try {
        dtgChiTiet[maM] = await api('vagabond.hang_tang.chi_tiet', { name: maM });
      } catch (e) { return baoTin(errMsg(e), 'Không đọc được chi tiết đơn'); }
    }
    return go(scrDuyetTang, true);
  }
}


/* ---------------- Báo cáo hàng tặng

   Anh Việt duyệt 31/08/2026: *"Báo cáo hàng tặng theo tháng, theo điểm bán,
   theo loại tặng, để cuối năm biết tiệm đã cho đi bao nhiêu cho việc gì."*

   CHỈ CỘNG ĐƠN ĐÃ GHI SỔ. Đơn còn chờ duyệt chưa phải chi phí của tiệm, gộp
   vào là báo cáo phồng lên bằng những thứ có thể bị từ chối. Số đang chờ để
   riêng một dòng, không lẫn vào. */
var tbcTu = '';
var tbcDen = '';

function tbcBang(tieu_de, cac, tong) {
  if (!(cac || []).length) return '';
  var s = '<div class="sec">' + h(tieu_de) + '</div><div class="card">';
  cac.forEach(function (o) {
    var pt = tong > 0 ? Math.round(o.tien * 100 / tong) : 0;
    s += '<div style="padding:9px 12px;border-bottom:1px solid #f2f4f7">' +
      '<div style="display:flex;justify-content:space-between;gap:10px;font-size:13.5px">' +
      '<span style="color:#344054">' + h(o.ten || o.k) +
      ' <span style="color:#98a2b3">· ' + o.so + ' đơn</span></span>' +
      '<b style="white-space:nowrap">' + money(o.tien) + ' đ</b></div>' +
      /* Thanh ty le ve bang chieu rong, khong ve bang mau: mot thanh dai
         ngan noi ro hon mot con so phan tram nam le loi. */
      '<div style="margin-top:5px;height:6px;background:#f2f4f7;border-radius:99px">' +
      '<div style="width:' + pt + '%;height:6px;background:#7c3aed;border-radius:99px"></div>' +
      '</div></div>';
  });
  return s + '</div>';
}

async function scrTangBaoCao() {
  frame('Báo cáo hàng tặng', '<div class="emp"><div class="e1">⏳</div><div>Đang cộng sổ...</div></div>');
  var kq;
  try {
    kq = await api('vagabond.hang_tang.bao_cao', { tu_ngay: tbcTu, den_ngay: tbcDen });
  } catch (e) {
    frame('Báo cáo hàng tặng', '<div class="emp"><div class="e1">⚠️</div><div>' +
      h(errMsg(e)) + '</div></div>');
    return;
  }
  tbcTu = kq.tu_ngay || ''; tbcDen = kq.den_ngay || '';

  var html = '<div class="card" style="padding:12px 13px">' +
    '<div style="font-size:12px;color:#8a8f9c">TIỆM ĐÃ TẶNG (đã ghi sổ)</div>' +
    '<b style="font-size:24px;color:#5b21b6">' + money(kq.tien || 0) + ' đ</b>' +
    '<div style="font-size:12.5px;color:#475467;margin-top:2px">' +
    (kq.so || 0) + ' đơn, từ ' + h(kq.tu_ngay || '') + ' đến ' + h(kq.den_ngay || '') + '</div>' +
    (kq.cho_so ? '<div style="margin-top:8px;padding:7px 9px;background:#fffbeb;' +
      'border:1px solid #fde68a;border-radius:8px;font-size:12.5px;color:#92400e">' +
      'Còn <b>' + kq.cho_so + ' đơn</b> chưa ghi sổ, tổng ' + money(kq.cho_tien || 0) +
      ' đ. Chưa cộng vào con số trên, vì đơn chưa duyệt thì chưa phải chi phí.</div>' : '') +
    '<div style="display:flex;gap:8px;margin-top:10px">' +
    '<input class="tin" type="date" id="tbcTu" value="' + h(tbcTu) + '" style="margin:0;flex:1">' +
    '<input class="tin" type="date" id="tbcDen" value="' + h(tbcDen) + '" style="margin:0;flex:1">' +
    '</div></div>';

  html += tbcBang('Theo loại tặng', kq.loai, kq.tien);
  html += tbcBang('Theo điểm bán', kq.diem, kq.tien);
  html += tbcBang('Theo tháng', (kq.thang || []).map(function (o) {
    return { k: o.k, ten: o.k, so: o.so, tien: o.tien };
  }), kq.tien);
  if (!(kq.so || 0)) {
    html += '<div class="card"><div class="emp" style="padding:24px">' +
      '<div class="e1">🎁</div><div>Chưa có đơn hàng tặng nào đã ghi sổ trong kỳ này.</div>' +
      '</div></div>';
  }

  frame('Báo cáo hàng tặng', html);
  ['tbcTu', 'tbcDen'].forEach(function (id) {
    var o = document.getElementById(id);
    if (!o) return;
    o.onchange = function () {
      tbcTu = document.getElementById('tbcTu').value || '';
      tbcDen = document.getElementById('tbcDen').value || '';
      go(scrTangBaoCao, true);
    };
  });
}

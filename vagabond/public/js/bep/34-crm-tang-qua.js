/* ---------- 34. CRM: Tang qua khach VIP ----------

Anh Viet dat bai 25/08/2026: thay bang tinh cua chi Loan Anh, nam sheet,
347 dong, bon mua qua.

Ba diem cua man nay khac han mot man danh sach thong thuong, va ca ba deu
doc ra tu du lieu that chu khong tu de bai:

1. HAI NHAN TRANG THAI TREN MOI DONG DEU BAM DUOC NGAY TAI CHO. Nguoi truc
   dien thoai goi xong sau muoi cuoc thi bam sau muoi lan. Bat mo va dong
   sau muoi cai form la ly do nguoi ta quay lai dung Excel.

2. KHUNG XANH DUOI O SO DIEN THOAI. Go toi dau boc toi do. Nguoi nhap THAY
   NGAY may doc ra so gi va ai nghe may, chu khong phai luu xong roi moi
   biet may hieu sai. Xem vagabond/sdt_boc.py.

3. HAI O SO DIEN THOAI CHU KHONG MOT. O tren la so cua CHINH khach, dung de
   dinh danh va la so duy nhat duoc gui tin Zalo. O duoi la so nguoi nhan
   thuc te cho shipper goi, duoc phep la so tro ly hay quan gia.

Moi con so tien va so luong deu do may chu chot lai (QT-19). Man nay chi ve.
*/

var tq = {
  dot: '', ten_dot: '', loc: 'tat_ca', nhom: '', tim: '',
  dm: null, form: null, boc: null
};

function tqCss() {
  if (document.getElementById('tqCss')) return;
  var st = document.createElement('style');
  st.id = 'tqCss';
  st.textContent =
    '.tqd{background:#fff;border-radius:14px;padding:14px;margin:0 12px 10px;' +
    'box-shadow:0 1px 3px rgba(16,24,40,.08);cursor:pointer}' +
    '.tqd:active{transform:scale(.99)}' +
    '.tqd .t1{font-size:16.5px;font-weight:700;color:#101828}' +
    '.tqd .t2{font-size:12.5px;color:#98a2b3;margin-top:3px}' +
    '.tqd .t3{display:flex;gap:14px;margin-top:10px}' +
    '.tqd .t3 div{font-size:12px;color:#667085}' +
    '.tqd .t3 b{display:block;font-size:17px;color:#101828}' +
    '.tqr{background:#fff;border-radius:12px;padding:11px 12px;margin:0 12px 8px;' +
    'box-shadow:0 1px 2px rgba(16,24,40,.06)}' +
    '.tqr.loi{border:1px solid #fda29b}' +
    '.tqr .r1{display:flex;align-items:flex-start;gap:8px}' +
    '.tqr .r1 b{flex:1;min-width:0;font-size:15.5px;color:#101828;font-weight:600}' +
    '.tqr .r2{font-size:12.5px;color:#667085;margin-top:3px}' +
    '.tqr .r3{font-size:12px;color:#98a2b3;margin-top:2px}' +
    '.tqr .r4{display:flex;gap:7px;margin-top:9px;flex-wrap:wrap}' +
    '.tqr .rw{font-size:12px;color:#b42318;background:#fef3f2;border-radius:8px;' +
    'padding:6px 8px;margin-top:8px;line-height:1.45}' +
    '.tqn{font-size:11.5px;font-weight:600;border-radius:999px;padding:2px 9px;' +
    'background:#eceff2;color:#5c6670;white-space:nowrap}' +
    '.tqb{font-size:12.5px;font-weight:700;border:1px solid transparent;' +
    'border-radius:999px;padding:6px 12px;cursor:pointer;-webkit-tap-highlight-color:transparent}' +
    '.tqb:active{transform:scale(.96)}' +
    '.tqb.cho{background:#fef0c7;color:#b54708}' +
    '.tqb.xong{background:#d1fadf;color:#027a48}' +
    '.tqb.di{background:#e0eaff;color:#3538cd}' +
    '.tqok{background:#ecfdf3;border:1px solid #abefc6;color:#067647;font-size:12.5px;' +
    'border-radius:10px;padding:9px 11px;margin-top:7px;line-height:1.5}' +
    '.tqwarn{background:#fffaeb;border:1px solid #fedf89;color:#b54708;font-size:12.5px;' +
    'border-radius:10px;padding:9px 11px;margin-top:7px;line-height:1.5}' +
    '.tqlc{background:#f7f8fa;border:1px solid #e4e7ec;border-radius:10px;padding:11px;' +
    'font-size:13.5px;color:#344054;white-space:pre-wrap;line-height:1.6;margin-top:6px}' +
    '.tqmon{display:flex;align-items:center;gap:8px;background:#fff;border-radius:10px;' +
    'padding:9px 10px;margin-bottom:7px;box-shadow:0 1px 2px rgba(16,24,40,.06)}' +
    '.tqmon .m1{flex:1;min-width:0;font-size:14.5px;color:#101828;overflow:hidden;' +
    'text-overflow:ellipsis;white-space:nowrap}';
  document.head.appendChild(st);
}

/* ---------- Man 1: danh sach dot ---------- */

async function scrTqDot() {
  tqCss();
  frame('Tặng quà khách VIP', '<div class="emp"><div class="e1">⏳</div></div>');
  var kq;
  try { kq = await api('vagabond.tang_qua.ds_dot'); }
  catch (e) {
    return frame('Tặng quà khách VIP',
      '<div class="emp"><div class="e1">⚠️</div><div class="e2">' + h(errMsg(e)) + '</div></div>');
  }
  var ds = kq.ds || [];
  var than = ds.length ? ds.map(function (d) {
    return '<div class="tqd" data-dot="' + h(d.name) + '" data-ten="' + h(d.ten_dot) + '">' +
      '<div class="t1">' + h(d.ten_dot) + '</div>' +
      '<div class="t2">' + h(d.dip || '') + (d.nam ? ' ' + d.nam : '') +
      ' · ' + h(d.trang_thai_dot || '') + '</div>' +
      '<div class="t3">' +
      '<div><b>' + (d.tong || 0) + '</b>khách</div>' +
      '<div><b>' + (d.da_lh || 0) + '</b>đã liên hệ</div>' +
      '<div><b>' + (d.da_tang || 0) + '</b>đã tặng</div>' +
      '</div>' +
      /* Nut nhan ban nam TRONG the nhung tach data rieng. Bam vao the la mo
         dot, bam dung nut la nhan ban - nen o tren phai soi data-nb TRUOC
         data-dot, khong thi bam nut cung chi mo dot. */
      '<div style="display:flex;gap:8px;margin-top:8px">' +
      '<button class="btn gh" data-sd="' + h(d.name) + '" ' +
      'style="flex:1;margin:0;padding:7px 10px;font-size:13px">✏️ Sửa đợt</button>' +
      '<button class="btn gh" data-nb="' + h(d.name) + '" data-nbten="' + h(d.ten_dot) + '" ' +
      'style="flex:1;margin:0;padding:7px 10px;font-size:13px">🗓️ Nhân bản</button>' +
      '</div></div>';
  }).join('') : '<div class="emp"><div class="e1">🎁</div>' +
    '<div class="e2">Chưa có đợt tặng quà nào</div>' +
    '<div class="e3">Bấm nút cộng ở góc dưới bên phải để mở đợt đầu tiên, ví dụ Trung thu 2026</div></div>';

  var b = frame('Tặng quà khách VIP', than, {
    fab: 1,
    onFab: function () { tqd.form = null; go(scrTqLapDot); }
  });
  b.onclick = function (e) {
    var nb = e.target.closest('[data-nb]');
    if (nb) return tqNhanBan(nb.dataset.nb, nb.dataset.nbten);
    var sd = e.target.closest('[data-sd]');
    if (sd) return tqSuaDot(sd.dataset.sd);
    var t = e.target.closest('[data-dot]');
    if (!t) return;
    tq.dot = t.dataset.dot;
    tq.ten_dot = t.dataset.ten;
    tq.loc = 'tat_ca'; tq.nhom = ''; tq.tim = '';
    go(scrTqDs);
  };
}

/* ---------- Man 2: danh sach khach trong mot dot ---------- */

var TQ_CHIP = [
  ['tat_ca', 'Tất cả'], ['chua_lien_he', 'Chưa liên hệ'],
  ['chua_tang', 'Chưa tặng'], ['da_tang', 'Đã tặng'],
  ['sdt_loi', 'Số điện thoại lỗi'], ['da_huy', 'Đã huỷ']
];

async function scrTqDs() {
  tqCss();
  if (!tq.dot) return go(scrTqDot);
  frame(tq.ten_dot || 'Danh sách tặng quà', '<div class="emp"><div class="e1">⏳</div></div>');
  var kq;
  try {
    kq = await api('vagabond.tang_qua.danh_sach',
      { dot: tq.dot, loc: tq.loc, nhom: tq.nhom, tim: tq.tim });
  } catch (e) {
    return frame(tq.ten_dot || 'Danh sách tặng quà',
      '<div class="emp"><div class="e1">⚠️</div><div class="e2">' + h(errMsg(e)) + '</div></div>');
  }
  tqVeDs(kq);
}

function tqVeDs(kq) {
  var dem = kq.dem || {};
  var chip = '<div class="vtb">' + TQ_CHIP.map(function (c) {
    var so = dem[c[0]] || 0;
    if (c[0] === 'da_huy' && !so) return '';
    return '<span class="vt' + (kq.loc === c[0] ? ' on' : '') + '" data-loc="' + c[0] + '">' +
      h(c[1]) + '<b>' + so + '</b></span>';
  }).join('') + '</div>';

  var chipNhom = (kq.chip_nhom || []).length
    ? '<div class="vtb">' +
      '<span class="vt' + (kq.nhom ? '' : ' on') + '" data-nhom="">Mọi nhóm</span>' +
      kq.chip_nhom.map(function (n) {
        return '<span class="vt' + (kq.nhom === n.k ? ' on' : '') + '" data-nhom="' + h(n.k) + '">' +
          h(n.k) + '<b>' + n.so + '</b></span>';
      }).join('') + '</div>'
    : '';

  var otim = '<div style="padding:8px 12px 4px">' +
    '<input class="vxi" id="tqTim" placeholder="Tìm theo tên khách, đơn vị hoặc số điện thoại" value="' +
    h(kq.tim || '') + '"></div>';

  var ds = kq.ds || [];
  var than = ds.length ? ds.map(tqDong).join('')
    : '<div class="emp"><div class="e1">🔍</div><div class="e2">Không có dòng nào khớp</div>' +
      '<div class="e3">Thử bỏ bớt bộ lọc, hoặc bấm chip Tất cả</div></div>';

  var b = frame(tq.ten_dot || 'Danh sách tặng quà',
    chip + chipNhom + otim + '<div style="padding-top:4px">' + than + '</div>',
    {
      fab: 1, onFab: function () { tq.form = null; go(scrTqSua); },
      /* Nut cong o goc phai mo tung phieu mot, nut nay them ca chuc nguoi
         mot luc. Hai viec khac han nhau nen hai nut khac nhau. */
      /* MOT nut hanh dong, mo mot bang chon hai duong them khach. Hai
         nut tren thanh tieu de thi khong con cho cho nut Ve. */
      action: '👥',
      onAction: tqThemKhachKieuGi
    });

  var o = document.getElementById('tqTim');
  if (o) {
    var hen = null;
    o.oninput = function () {
      clearTimeout(hen);
      var v = o.value;
      /* Doi 400ms roi moi hoi may chu: go mot ten dai la muoi lan goi. */
      hen = setTimeout(function () { tq.tim = v; scrTqDs(); }, 400);
    };
  }

  b.onclick = function (e) {
    var c = e.target.closest('[data-loc]');
    if (c) { tq.loc = c.dataset.loc; return scrTqDs(); }
    var n = e.target.closest('[data-nhom]');
    if (n) { tq.nhom = n.dataset.nhom; return scrTqDs(); }
    var nut = e.target.closest('[data-truc]');
    if (nut) return tqBamTrangThai(nut);
    var d = e.target.closest('[data-ma]');
    if (d) { tq.form = { ma: d.dataset.ma }; return go(scrTqSua); }
  };
}

function tqDong(x) {
  var lh = x.tt_lien_he === 'Da lien he';
  var tang = x.tt_tang === 'Da tang';
  var dangXl = x.tt_tang === 'Dang xu ly';
  var phu = [x.don_vi, x.khach_cua, x.bo_phan_lam].filter(Boolean).join(' · ');
  /* So hien ra la so NGUOI NHAN neu co, vi do la so shipper goi. Kem ten
     nguoi nghe may de nguoi truc biet minh sap goi cho ai. */
  var so = x.sdt_nhan || x.sdt_khach || '';
  var nghe = x.nguoi_nghe_may ? ' (' + x.nguoi_nghe_may + ')' : '';

  return '<div class="tqr' + (x.canh_bao_sdt ? ' loi' : '') + '">' +
    '<div class="r1"><b data-ma="' + h(x.name) + '">' + h(x.ten_khach || '(chưa có tên)') + '</b>' +
    (x.phan_loai ? '<span class="tqn">' + h(x.phan_loai) + '</span>' : '') + '</div>' +
    (x.tom_mon ? '<div class="r2">' + h(x.tom_mon) + '</div>' : '') +
    (phu ? '<div class="r3">' + h(phu) + '</div>' : '') +
    (so ? '<div class="r3">' + h(so + nghe) + '</div>' : '') +
    '<div class="r4">' +
    '<span class="tqb ' + (lh ? 'xong' : 'cho') + '" data-truc="lien_he" ' +
    'data-ma="' + h(x.name) + '" data-moi="' + (lh ? 'Chua lien he' : 'Da lien he') + '">' +
    (lh ? 'Đã liên hệ' : 'Chưa liên hệ') + '</span>' +
    '<span class="tqb ' + (tang ? 'xong' : dangXl ? 'di' : 'cho') + '" data-truc="tang" ' +
    'data-ma="' + h(x.name) + '" data-moi="' + h(tang ? 'Chua tang' : dangXl ? 'Da tang' : 'Dang xu ly') + '">' +
    (tang ? 'Đã tặng' : dangXl ? 'Đang xử lý' : 'Chưa tặng') + '</span>' +
    '</div>' +
    (x.canh_bao_sdt ? '<div class="rw">' + h(x.canh_bao_sdt) + '</div>' : '') +
    '</div>';
}

async function tqBamTrangThai(nut) {
  /* Bam thang tren dong, khong mo form. Day la cho tiet kiem thoi gian
     lon nhat cua ca man: sau muoi cuoc goi la sau muoi lan bam. */
  busy(1);
  try {
    await api('vagabond.tang_qua.doi_trang_thai',
      { ma: nut.dataset.ma, truc: nut.dataset.truc, gia_tri: nut.dataset.moi });
  } catch (e) { busy(0); return toast(errMsg(e), 4600); }
  busy(0);
  scrTqDs();
}

/* ---------- Man 3: form mot phieu ---------- */

async function tqNapDanhMuc() {
  if (tq.dm) return tq.dm;
  tq.dm = await api('vagabond.tang_qua.danh_muc');
  return tq.dm;
}

async function scrTqSua() {
  tqCss();
  frame('Phiếu tặng quà', '<div class="emp"><div class="e1">⏳</div></div>');
  var dm;
  try { dm = await tqNapDanhMuc(); }
  catch (e) { return frame('Phiếu tặng quà',
    '<div class="emp"><div class="e1">⚠️</div><div class="e2">' + h(errMsg(e)) + '</div></div>'); }

  var p = tq.form || {};
  if (p.ma && !p.da_nap) {
    try { p = await api('vagabond.tang_qua.chi_tiet', { ma: p.ma }); p.da_nap = 1; tq.form = p; }
    catch (e) { return frame('Phiếu tặng quà',
      '<div class="emp"><div class="e1">⚠️</div><div class="e2">' + h(errMsg(e)) + '</div></div>'); }
  }
  if (!p.mon) p.mon = [];
  if (!p.bo_phan_lam) p.bo_phan_lam = 'Sales';
  if (!p.tt_tang) p.tt_tang = 'Chua tang';
  if (!p.tt_lien_he) p.tt_lien_he = 'Chua lien he';
  tq.form = p;
  tqVeForm(dm, p);
}

function tqO(nhan, id, gt, chu) {
  return '<div class="vxl">' + h(nhan) + '</div>' +
    '<input class="vxi" id="' + id + '" value="' + h(gt || '') + '"' +
    (chu ? ' placeholder="' + h(chu) + '"' : '') + '>';
}

function tqChon(nhan, id, gt, chu) {
  /* O CHON, khong o go (QT-31). Bam mo bang chon, khong go tu do. */
  return '<div class="vxl">' + h(nhan) + '</div>' +
    '<div class="vxi" id="' + id + '" data-chon="' + id + '" ' +
    'style="display:flex;align-items:center;gap:8px;cursor:pointer">' +
    '<span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap' +
    (gt ? '' : ';color:#98a2b3') + '">' + h(gt || chu || 'Chạm để chọn') + '</span>' +
    '<span style="color:#c3c8d4">&#8250;</span></div>';
}

function tqVeForm(dm, p) {
  var moi = !p.name;

  var khoiSdt =
    '<div class="vxl">SĐT khách VIP</div>' +
    '<input class="vxi" id="tqSdtKhach" value="' + h(p.sdt_khach_tho || '') + '" ' +
    'placeholder="Số riêng của chính khách">' +
    '<div id="tqBocKhach"></div>' +
    '<div class="vxl">SĐT người nhận thực tế</div>' +
    '<input class="vxi" id="tqSdtNhan" value="' + h(p.sdt_nhan_tho || '') + '" ' +
    'placeholder="Trợ lý, quản gia, bảo vệ... shipper gọi số này">' +
    '<div id="tqBocNhan"></div>';

  var mon = (p.mon || []).map(function (m, i) {
    return '<div class="tqmon"><span class="m1">' + h(m.ten_mon || m.mon || '') + '</span>' +
      '<input class="vxq" data-sl="' + i + '" type="number" min="1" value="' + (m.so_luong || 1) + '">' +
      '<button class="vxx" data-xoamon="' + i + '">&times;</button></div>';
  }).join('');

  var lc = p.loi_chuc_in || p.loi_chuc || '';

  var than = '<div class="vxf">' +
    '<div class="vxl" style="margin-top:2px">1. KHÁCH</div>' +
    tqChon('Khách trong hệ (bỏ qua được)', 'tqKhach', p.khach, 'Chưa liên kết khách nào') +
    tqO('Tên khách', 'tqTen', p.ten_khach, 'Tên in lên thiệp') +
    tqChon('Phân loại', 'tqNhom', p.phan_loai) +
    tqO('Title riêng', 'tqTitle', p.title_rieng, 'Đạo diễn, Nhà Thiết Kế, Doanh nhân...') +
    tqO('Đơn vị', 'tqDonVi', p.don_vi, 'ELLE Tạp Chí, Manki Coffee...') +

    '<div class="vxl" style="margin-top:18px">2. AI LO</div>' +
    tqChon('Khách của ai', 'tqKhachCua', p.khach_cua, 'Người giữ quan hệ') +
    tqChon('Bộ phận làm', 'tqBoPhan', p.bo_phan_lam) +
    tqChon('Người làm', 'tqNguoiLam', p.nguoi_lam, 'Để trống thì giao cả nhóm') +

    '<div class="vxl" style="margin-top:18px">3. LIÊN HỆ</div>' + khoiSdt +
    tqO('Địa chỉ', 'tqDiaChi', p.dia_chi) +
    tqO('Giờ giao', 'tqGioGiao', p.gio_giao, 'T4 13/12 trước 16g') +
    tqO('Ghi chú vận chuyển', 'tqGcVc', p.ghi_chu_van_chuyen,
      'Đã chuyển D1 cho khách ghé lấy, nhờ anh Jin cầm theo...') +

    '<div class="vxl" style="margin-top:18px">4. QUÀ</div>' +
    '<div id="tqDsMon">' + (mon || '<div class="vxl" style="margin:0 0 6px">Chưa chọn món nào</div>') + '</div>' +
    '<button class="vxb o" id="tqThemMon" style="margin-top:0">+ Thêm món</button>' +

    '<div class="vxl" style="margin-top:18px">5. LỜI CHÚC</div>' +
    tqChon('Mẫu lời chúc', 'tqMau', p.mau_loi_chuc, 'Lấy mẫu mặc định của đợt') +
    '<div class="tqlc" id="tqXemLc">' + (lc ? h(lc) : 'Chọn mẫu rồi lời chúc sẽ hiện ở đây') + '</div>' +
    '<div class="vxl" style="margin-top:12px">' +
    '<label><input type="checkbox" id="tqSuaTay"' + (p.sua_tay ? ' checked' : '') + '> ' +
    'Sửa tay lời chúc này</label></div>' +
    '<textarea class="vxi" id="tqLcTay" rows="5"' + (p.sua_tay ? '' : ' style="display:none"') + '>' +
    h(p.loi_chuc_sua_tay || '') + '</textarea>' +

    '<div class="vxl" style="margin-top:18px">6. TRẠNG THÁI</div>' +
    tqChon('Trạng thái tặng', 'tqTtTang', p.tt_tang) +
    tqChon('Trạng thái liên hệ', 'tqTtLh', p.tt_lien_he) +
    tqO('Ghi chú', 'tqGhiChu', p.ghi_chu) +

    /* Khoi hoa don CHI hien khi phieu da luu va da gan khach trong he.
       Chua luu thi chua co ma phieu de may soi, con chua gan khach thi
       khong biet xuat hoa don cho ai - hai truong hop deu khong nen bay ra
       mot cai nut bam vao la bao loi. */
    (moi || !p.khach ? '' :
      '<div class="vxl" style="margin-top:18px">7. HOÁ ĐƠN HÀNG BIẾU TẶNG</div>' +
      (p.hoa_don
        ? '<div class="tqok">Đã xuất hoá đơn ' + h(p.hoa_don) + '.</div>'
        : '<div class="tqwarn">Hoá đơn quà ghi ĐỦ giá bán và thuế theo luật hàng ' +
          'biếu tặng. Khách trả 0 đồng, phần công nợ được gạt sang chi phí biếu tặng. ' +
          'Tờ lập ra ở dạng nháp.</div>' +
          '<button class="vxb o" id="tqHoaDon" style="margin-top:8px">🧾 Xuất hoá đơn quà tặng</button>')) +
    '</div>';

  var nut = '<button class="btn" id="tqLuu">Lưu</button>' +
    (moi ? '<button class="btn gh" id="tqLuuTiep" style="margin-top:9px">Lưu và thêm khách tiếp theo</button>' : '');

  var b = frame(moi ? 'Thêm khách nhận quà' : 'Phiếu tặng quà', than, { footer: nut });
  tqGanSuKien(b, dm, p);
  var bhd = document.getElementById('tqHoaDon');
  if (bhd) bhd.onclick = async function () {
    var ma = await tqXuatHoaDon(p.name, p.ten_khach);
    if (ma) { p.hoa_don = ma; tqVeForm(dm, p); }
  };
  tqBocLai();
}

/* Khung xanh duoi o so dien thoai. Go toi dau boc toi do.

   Day la diem mau chot cua ca man: nguoi nhap THAY NGAY may doc ra so gi
   va ai nghe may, chu khong phai luu xong roi moi biet may hieu sai. */
function tqKhungBoc(r, la_khach) {
  if (!r || (!r.sdt && !r.canh_bao)) return '';
  var d = [];
  if (r.sdt) {
    d.push('Đã đọc ra <b>' + h(r.sdt) + '</b>' +
      (r.loai === 'co_dinh' ? ', số bàn' : ', di động') + '.');
  }
  if (r.nguoi_nghe) d.push('Người nghe máy: <b>' + h(r.nguoi_nghe) + '</b>.');
  if (la_khach && r.sdt && !r.chinh_chu) {
    d.push('Đây <b>không phải</b> số chính chủ, tin nhắn tự động đã khoá.');
  }
  if (r.canh_bao) d.push(h(r.canh_bao));
  var xau = r.canh_bao || (la_khach && r.sdt && !r.chinh_chu);
  return '<div class="' + (xau ? 'tqwarn' : 'tqok') + '">' + d.join('<br>') + '</div>';
}

var tqHenBoc = null;
function tqBocLai() {
  clearTimeout(tqHenBoc);
  tqHenBoc = setTimeout(async function () {
    var a = document.getElementById('tqSdtKhach');
    var b = document.getElementById('tqSdtNhan');
    var oa = document.getElementById('tqBocKhach');
    var ob = document.getElementById('tqBocNhan');
    if (!a || !oa) return;
    try {
      var ra = await api('vagabond.tang_qua.thu_boc_sdt', { tho: a.value });
      oa.innerHTML = tqKhungBoc(ra, 1);
    } catch (e) { oa.innerHTML = ''; }
    if (!b || !ob) return;
    try {
      var rb = await api('vagabond.tang_qua.thu_boc_sdt', { tho: b.value });
      ob.innerHTML = tqKhungBoc(rb, 0);
    } catch (e) { ob.innerHTML = ''; }
  }, 350);
}

var tqHenLc = null;
function tqXemLoiChuc() {
  clearTimeout(tqHenLc);
  tqHenLc = setTimeout(async function () {
    var o = document.getElementById('tqXemLc');
    if (!o) return;
    var p = tq.form || {};
    if (!p.mau_loi_chuc) {
      o.textContent = 'Chọn mẫu rồi lời chúc sẽ hiện ở đây';
      return;
    }
    try {
      var r = await api('vagabond.tang_qua.xem_truoc_loi_chuc', {
        mau: p.mau_loi_chuc, phan_loai: p.phan_loai, title_rieng: p.title_rieng,
        ten_khach: p.ten_khach, don_vi: p.don_vi
      });
      o.textContent = r.loi_chuc || '(mẫu này chưa ráp ra câu nào)';
    } catch (e) { o.textContent = errMsg(e); }
  }, 300);
}

function tqGanSuKien(b, dm, p) {
  function goO(id, truong) {
    var o = document.getElementById(id);
    if (o) o.oninput = function () {
      p[truong] = o.value;
      if (truong === 'ten_khach' || truong === 'don_vi' || truong === 'title_rieng') tqXemLoiChuc();
    };
  }
  goO('tqTen', 'ten_khach'); goO('tqTitle', 'title_rieng');
  goO('tqDonVi', 'don_vi'); goO('tqDiaChi', 'dia_chi');
  goO('tqGioGiao', 'gio_giao'); goO('tqGcVc', 'ghi_chu_van_chuyen');
  goO('tqGhiChu', 'ghi_chu'); goO('tqLcTay', 'loi_chuc_sua_tay');

  ['tqSdtKhach', 'tqSdtNhan'].forEach(function (id) {
    var o = document.getElementById(id);
    if (!o) return;
    o.oninput = function () {
      p[id === 'tqSdtKhach' ? 'sdt_khach_tho' : 'sdt_nhan_tho'] = o.value;
      tqBocLai();
    };
  });

  var st = document.getElementById('tqSuaTay');
  if (st) st.onchange = function () {
    p.sua_tay = st.checked ? 1 : 0;
    var t = document.getElementById('tqLcTay');
    if (t) t.style.display = st.checked ? '' : 'none';
  };

  b.onclick = function (e) {
    var c = e.target.closest('[data-chon]');
    if (c) return tqMoChon(c.dataset.chon, dm, p);
    var x = e.target.closest('[data-xoamon]');
    if (x) { p.mon.splice(parseInt(x.dataset.xoamon, 10), 1); return tqVeForm(dm, p); }
    if (e.target.id === 'tqThemMon') return tqChonMonQua(dm, p);
    if (e.target.id === 'tqLuu') return tqLuu(p, 0);
    if (e.target.id === 'tqLuuTiep') return tqLuu(p, 1);
  };
  b.addEventListener('input', function (e) {
    var s = e.target.closest('[data-sl]');
    if (s) p.mon[parseInt(s.dataset.sl, 10)].so_luong = parseInt(s.value, 10) || 1;
  });
}

/* Moi o chon deu tro thang vao danh muc that (QT-31). Khong o go tu do. */
async function tqMoChon(id, dm, p) {
  if (id === 'tqNhom') {
    return sheet('Phân loại khách', (dm.nhom || []).map(function (x) {
      return { value: x.name, label: x.name, phu: 'xưng hô: ' + (x.xung_ho || ''), icon: '⭐' };
    }), p.phan_loai, function (x) { p.phan_loai = x.value; tqVeForm(dm, p); tqXemLoiChuc(); }, true);
  }
  if (id === 'tqMau') {
    return sheet('Mẫu lời chúc', (dm.mau || []).map(function (x) {
      return { value: x.name, label: x.ten_mau || x.name, phu: x.dip || '', icon: '💌' };
    }), p.mau_loi_chuc, function (x) { p.mau_loi_chuc = x.value; tqVeForm(dm, p); tqXemLoiChuc(); }, true);
  }
  if (id === 'tqBoPhan') {
    return sheet('Bộ phận làm', (dm.bo_phan || []).map(function (x) {
      return { value: x, label: x, icon: x === 'Marketing' ? '📣' : '🧾' };
    }), p.bo_phan_lam, function (x) { p.bo_phan_lam = x.value; tqVeForm(dm, p); });
  }
  if (id === 'tqTtTang') {
    return sheet('Trạng thái tặng', [
      { value: 'Chua tang', label: 'Chưa tặng', icon: '⏳' },
      { value: 'Dang xu ly', label: 'Đang xử lý, vận chuyển', icon: '🚚',
        phu: 'Gồm cả trường hợp đã chuyển chi nhánh chờ khách ghé lấy' },
      { value: 'Da tang', label: 'Đã tặng', icon: '✅' }
    ], p.tt_tang, function (x) { p.tt_tang = x.value; tqVeForm(dm, p); });
  }
  if (id === 'tqTtLh') {
    return sheet('Trạng thái liên hệ', [
      { value: 'Chua lien he', label: 'Chưa liên hệ', icon: '⏳' },
      { value: 'Da lien he', label: 'Đã liên hệ', icon: '✅' }
    ], p.tt_lien_he, function (x) { p.tt_lien_he = x.value; tqVeForm(dm, p); });
  }
  if (id === 'tqKhach') return tqChonKhach(dm, p);
  if (id === 'tqKhachCua' || id === 'tqNguoiLam') return tqChonNguoi(id, dm, p);
}

async function tqChonKhach(dm, p) {
  busy(1);
  var ds;
  try {
    ds = await getList('Customer', {
      fields: ['name', 'customer_name', 'mobile_no', 'account_manager'],
      filters: { disabled: 0 }, limit_page_length: 300, order_by: 'modified desc'
    });
  } catch (e) { busy(0); return toast('Không tải được danh sách khách'); }
  busy(0);
  var muc = [{ value: '', label: 'Không liên kết khách nào', icon: '➖' }].concat(
    ds.map(function (x) {
      return { value: x.name, label: x.customer_name || x.name,
        phu: (x.mobile_no || '') + ' · ' + x.name, icon: '👤', tim: x.name };
    }));
  sheet('Khách trong hệ', muc, p.khach, function (x) {
    p.khach = x.value;
    /* Keo san nguoi giu quan he va so cua khach ve, khoi go lai. May chu
       van boc lai luc luu, o day chi de do tay cho nguoi nhap. */
    var k = ds.filter(function (c) { return c.name === x.value; })[0];
    if (k) {
      if (!p.ten_khach) p.ten_khach = k.customer_name || '';
      if (!p.khach_cua && k.account_manager) p.khach_cua = k.account_manager;
      if (!p.sdt_khach_tho && k.mobile_no) p.sdt_khach_tho = k.mobile_no;
    }
    tqVeForm(dm, p);
    tqBocLai();
    tqXemLoiChuc();
  }, true);
}

async function tqChonNguoi(id, dm, p) {
  busy(1);
  var ds;
  try {
    ds = await getList('User', {
      fields: ['name', 'full_name'], filters: { enabled: 1, user_type: 'System User' },
      limit_page_length: 300, order_by: 'full_name'
    });
  } catch (e) { busy(0); return toast('Không tải được danh sách người dùng'); }
  busy(0);
  var truong = id === 'tqKhachCua' ? 'khach_cua' : 'nguoi_lam';
  var muc = [{ value: '', label: 'Để trống', icon: '➖' }].concat(
    ds.map(function (x) {
      return { value: x.name, label: x.full_name || x.name, phu: x.name, icon: '🧑' };
    }));
  sheet(id === 'tqKhachCua' ? 'Khách của ai' : 'Người làm', muc, p[truong],
    function (x) { p[truong] = x.value; tqVeForm(dm, p); }, true);
}

async function tqChonMonQua(dm, p) {
  busy(1);
  var ds;
  try {
    ds = await getList('Item', {
      fields: ['name', 'item_name', 'image', 'stock_uom'],
      filters: { is_sales_item: 1, disabled: 0 },
      limit_page_length: 0, order_by: 'item_name'
    });
  } catch (e) { busy(0); return toast('Không tải được danh mục món'); }
  busy(0);
  sheet('Chọn món quà', ds.map(function (x) {
    return { value: x.name, label: x.item_name || x.name, phu: x.name,
      img: x.image || '', icon: '🎁', tim: x.name };
  }), '', function (x) {
    p.mon.push({ mon: x.value, ten_mon: x.label, so_luong: 1 });
    tqVeForm(dm, p);
  }, true);
}

async function tqLuu(p, themTiep) {
  if (!(p.ten_khach || '').trim()) return toast('Chưa có tên khách. Nhờ anh chị điền ô Tên khách.', 4200);
  if (!p.phan_loai) return toast('Chưa chọn phân loại khách. Nhờ anh chị chạm ô Phân loại.', 4200);
  if (!(p.mon || []).length) return toast('Chưa chọn món quà nào. Nhờ anh chị bấm Thêm món.', 4200);

  var goi = {
    dot: tq.dot,
    khach: p.khach || '', ten_khach: p.ten_khach, phan_loai: p.phan_loai,
    title_rieng: p.title_rieng || '', don_vi: p.don_vi || '',
    khach_cua: p.khach_cua || '', bo_phan_lam: p.bo_phan_lam || 'Sales',
    nguoi_lam: p.nguoi_lam || '',
    sdt_khach_tho: p.sdt_khach_tho || '', sdt_nhan_tho: p.sdt_nhan_tho || '',
    dia_chi: p.dia_chi || '', gio_giao: p.gio_giao || '',
    ghi_chu_van_chuyen: p.ghi_chu_van_chuyen || '',
    mau_loi_chuc: p.mau_loi_chuc || '', sua_tay: p.sua_tay ? 1 : 0,
    loi_chuc_sua_tay: p.loi_chuc_sua_tay || '',
    tt_tang: p.tt_tang, tt_lien_he: p.tt_lien_he, ghi_chu: p.ghi_chu || '',
    mon: (p.mon || []).map(function (m) {
      return { mon: m.mon, so_luong: m.so_luong || 1, ghi_chu_mon: m.ghi_chu_mon || '' };
    })
  };
  busy(1);
  try {
    /* May chu giu duong luu (QT-19), khong dung frappe.client.insert
       chung: boc lai so dien thoai, rap lai loi chuc va chan quyen deu
       phai chay o may chu, con man nay chi gui thu nguoi ta go. */
    await api('vagabond.tang_qua.luu', { ma: p.name || '', du_lieu: JSON.stringify(goi) });
  } catch (e) { busy(0); return toast(errMsg(e), 5200); }
  busy(0);
  toast('Đã lưu');
  if (themTiep) {
    /* Giu lai dot, phan loai, bo phan va mau: mot dot qua thuong nhap lien
       vai chuc khach cung nhom, chon lai tung o moi dong la vo ich. */
    tq.form = {
      phan_loai: p.phan_loai, bo_phan_lam: p.bo_phan_lam,
      khach_cua: p.khach_cua, mau_loi_chuc: p.mau_loi_chuc, mon: []
    };
    return scrTqSua();
  }
  back();
}

/* =====================================================================
   Nhan ban dot, them khach hang loat, va xuat hoa don qua tang
   (anh Viet dat bai 26/08/2026)

   Ba man nay khong dung chung nut voi ba man tren, co chu y:

   - Nhan ban dot va Them khach hang loat la viec cua QUAN LY, lam mot lan
     dau mua. Trong khi ba man tren la viec cua nguoi truc, lam ca ngay.
     Tron nut vao nhau la nguoi truc bam nham mot cai la sinh ra ca mot dot
     moi.

   - Nut Xuat hoa don qua nam trong man chi tiet phieu chu khong nam ngoai
     danh sach: no cham so cai va co the ban sang hoa don dien tu, nen phai
     mo dung mot phieu ra doc roi moi bam duoc.
   ===================================================================== */

var tqb = { dot: '', chon: {}, tim: '', hang: '', mon: [] };

/* ---------- Nhan ban mot dot sang mua sau ---------- */

async function tqNhanBan(maDot, tenDot) {
  var nam = await hoiChu('Nhân bản đợt tặng quà',
    'Năm của đợt mới', String((new Date()).getFullYear() + 1));
  if (nam === null) return;
  nam = String(nam || '').trim();
  if (!/^\d{4}$/.test(nam)) return toast('Năm phải là bốn chữ số, ví dụ 2027.', 4200);

  var chepQua = await hoiCo('Món quà',
    'Chép luôn cả món quà của từng khách sang đợt mới?\n\n' +
    'Thường thì KHÔNG: quà Trung thu khác quà Tết, chép sang lại phải xoá từng dòng.',
    'Có, chép cả món');

  busy(1);
  var kq;
  try {
    kq = await api('vagabond.tang_qua.nhan_ban_dot',
      { ma_dot: maDot, nam_moi: nam, chep_qua: chepQua ? 1 : 0 });
  } catch (e) { busy(0); return toast(errMsg(e), 6000); }
  busy(0);
  toast(kq.loi_nhan || 'Đã nhân bản', 6000);
  tq.dot = kq.ma; tq.ten_dot = tenDot || kq.ma;
  tq.loc = 'tat_ca'; tq.nhom = ''; tq.tim = '';
  go(scrTqDs);
}

/* ---------- Man: tick hang loat khach co hang thanh vien ---------- */

async function scrTqThemLoat() {
  tqCss();
  if (!tq.dot) return go(scrTqDot);
  tqb.dot = tq.dot;
  frame('Thêm khách vào đợt', '<div class="emp"><div class="e1">⏳</div></div>');
  var kq;
  try {
    kq = await api('vagabond.tang_qua.khach_co_hang',
      { dot: tqb.dot, tim: tqb.tim, tu_khoa: tqb.tim, hang: tqb.hang });
  } catch (e) {
    return frame('Thêm khách vào đợt',
      '<div class="emp"><div class="e1">⚠️</div><div class="e2">' + h(errMsg(e)) + '</div></div>');
  }
  tqVeThemLoat(kq);
}

function tqVeThemLoat(kq) {
  var ds = kq.ds || [];
  var soChon = Object.keys(tqb.chon).length;

  var chipHang = '<div class="vtb">' +
    '<span class="vt' + (tqb.hang ? '' : ' on') + '" data-hg="">Mọi hạng</span>' +
    (kq.hang || []).map(function (x) {
      return '<span class="vt' + (tqb.hang === x ? ' on' : '') + '" data-hg="' + h(x) + '">' +
        h(x) + '</span>';
    }).join('') + '</div>';

  var otim = '<div style="padding:8px 12px 4px">' +
    '<input class="vxi" id="tqbTim" placeholder="Tìm theo tên hoặc mã khách" value="' +
    h(tqb.tim || '') + '"></div>';

  var than = ds.length ? ds.map(function (x) {
    var da = !!x.da_co;
    var tick = !!tqb.chon[x.ma];
    return '<div class="tqmon" style="' + (da ? 'opacity:.55' : '') + '" ' +
      (da ? '' : 'data-tick="' + h(x.ma) + '" data-ten="' + h(x.ten) + '"') + '>' +
      '<span style="width:22px;text-align:center">' +
      (da ? '✓' : (tick ? '☑️' : '⬜')) + '</span>' +
      '<span class="m1">' + h(x.ten) +
      '<div style="font-size:12px;color:#667085">' + h(x.hang || '') +
      (x.nhom ? ' · ' + h(x.nhom) : '') + (da ? ' · đã có trong đợt' : '') + '</div></span>' +
      '</div>';
  }).join('') : '<div class="emp"><div class="e1">🔍</div>' +
    '<div class="e2">Không có khách nào khớp</div>' +
    '<div class="e3">Chỉ hiện khách ĐÃ được xếp hạng thành viên. Khách chưa có hạng thì xếp hạng ở màn Danh mục khách hàng trước.</div></div>';

  var chanTrang =
    '<button class="btn gh" id="tqbMon" style="margin-bottom:6px">🎁 Món quà chung: ' +
    (tqb.mon.length ? h(tqb.mon.map(function (m) { return m.ten_mon + ' x' + m.so_luong; }).join(', '))
      : 'chưa chọn') + '</button>' +
    '<button class="btn" id="tqbThem"' + (soChon ? '' : ' disabled') + '>' +
    'Thêm ' + soChon + ' khách vào đợt</button>';

  var b = frame('Thêm khách vào đợt', chipHang + otim +
    '<div style="padding:4px 12px 12px">' + than + '</div>',
    { footer: chanTrang });

  var o = document.getElementById('tqbTim');
  if (o) {
    var hen = null;
    o.oninput = function () {
      clearTimeout(hen);
      var v = o.value;
      hen = setTimeout(function () { tqb.tim = v; scrTqThemLoat(); }, 400);
    };
  }

  var bm = document.getElementById('tqbMon');
  if (bm) bm.onclick = tqbChonMon;
  var bt = document.getElementById('tqbThem');
  if (bt) bt.onclick = tqbGui;

  b.onclick = function (e) {
    var hg = e.target.closest('[data-hg]');
    if (hg) { tqb.hang = hg.dataset.hg; return scrTqThemLoat(); }
    var t = e.target.closest('[data-tick]');
    if (!t) return;
    var ma = t.dataset.tick;
    if (tqb.chon[ma]) delete tqb.chon[ma];
    else tqb.chon[ma] = t.dataset.ten || ma;
    tqVeThemLoat(kq);
  };
}

async function tqbChonMon() {
  busy(1);
  var ds;
  try {
    ds = await getList('Item', {
      fields: ['name', 'item_name', 'image'],
      filters: { disabled: 0, is_sales_item: 1 },
      limit_page_length: 400, order_by: 'item_name'
    });
  } catch (e) { busy(0); return toast('Không tải được danh mục món'); }
  busy(0);
  sheet('Món quà chung cho mọi khách được tick', ds.map(function (x) {
    return { value: x.name, label: x.item_name || x.name, phu: x.name,
      img: x.image || '', icon: '🎁', tim: x.name };
  }), '', async function (x) {
    var sl = await hoiSo('Số lượng', x.label, '1');
    if (sl === null) return;
    tqb.mon.push({ mon: x.value, ten_mon: x.label, so_luong: Math.max(1, parseInt(sl, 10) || 1) });
    scrTqThemLoat();
  }, true);
}

async function tqbGui() {
  var ma = Object.keys(tqb.chon);
  if (!ma.length) return toast('Chưa tick khách nào.');
  var ok = await hoiCo('Xác nhận',
    'Thêm ' + ma.length + ' khách vào đợt ' + (tq.ten_dot || tqb.dot) + '?' +
    (tqb.mon.length ? '' : '\n\nChưa chọn món quà chung, các phiếu sẽ để trống món.'),
    'Thêm vào đợt');
  if (!ok) return;
  busy(1);
  var kq;
  try {
    kq = await api('vagabond.tang_qua.them_hang_loat', {
      dot: tqb.dot, khach: JSON.stringify(ma),
      mon: JSON.stringify(tqb.mon.map(function (m) {
        return { mon: m.mon, so_luong: m.so_luong };
      }))
    });
  } catch (e) { busy(0); return toast(errMsg(e), 6000); }
  busy(0);
  toast(kq.loi_nhan || 'Đã thêm', 6000);
  tqb.chon = {};
  back();
}

/* ---------- Xuat hoa don hang bieu tang tu mot phieu ---------- */

async function tqXuatHoaDon(maPhieu, tenKhach) {
  busy(1);
  var soi;
  try { soi = await api('vagabond.qua_tang_hoa_don.kiem_phieu', { ma_phieu: maPhieu }); }
  catch (e) { busy(0); return toast(errMsg(e), 6000); }
  busy(0);

  if (!soi.duoc) {
    return toast('Chưa xuất được: ' + (soi.loi || []).join(' '), 7000);
  }

  var tomMon = (soi.mon || []).map(function (m) {
    return m.ma + ' x' + m.so_luong;
  }).join(', ');

  /* Hai buoc, khong gop. Buoc mot lap ban nhap, buoc hai moi ghi so. Ghi so
     la luc cham so cai va co the ban sang hoa don dien tu, ma hoa don dien
     tu da gui co quan thue thi rat kho go lai (anh Viet dan 13/08/2026). */
  var ok = await hoiCo('Hoá đơn quà tặng',
    'Lập hoá đơn hàng biếu tặng cho ' + (tenKhach || maPhieu) + '?\n\n' +
    'Món: ' + (tomMon || '(chưa có món)') + '\n\n' +
    'Hoá đơn ghi ĐỦ giá bán và thuế theo luật hàng biếu tặng. Khách trả 0 đồng, ' +
    'phần công nợ được gạt sang chi phí biếu tặng bằng một bút toán riêng.\n\n' +
    'Tờ này lập ra ở dạng NHÁP, soát xong mới bấm Ghi sổ.',
    'Lập hoá đơn nháp');
  if (!ok) return;

  busy(1);
  var kq;
  try { kq = await api('vagabond.qua_tang_hoa_don.xuat_hoa_don', { ma_phieu: maPhieu }); }
  catch (e) { busy(0); return toast(errMsg(e), 7000); }
  busy(0);
  toast(kq.loi_nhan || 'Đã lập hoá đơn', 7000);
  return kq.ma;
}

/* =====================================================================
   Tu lap dot va dan danh sach NGAY TREN APP (anh Viet 26/08/2026)

   Truoc ban nay man Dot tang qua rong thi chi co mot cau "Mo Desk tao mot
   dot". Desk la man quan tri, Sales va Marketing khong vao, ma cung khong
   nen vao. Nen mua qua nao cung phai nho nguoi khac mo ho mot ban ghi roi
   moi lam duoc viec cua minh.
   ===================================================================== */

var tqd = { form: null, dm: null, dan: '', mon: [] };

/* ---------- Man: lap hoac sua mot dot ---------- */

async function scrTqLapDot() {
  tqCss();
  var p = tqd.form || {};
  frame(p.name ? 'Sửa đợt tặng quà' : 'Đợt tặng quà mới',
    '<div class="emp"><div class="e1">⏳</div></div>');
  if (!tqd.dm) {
    try { tqd.dm = await api('vagabond.tang_qua.danh_muc_dot'); }
    catch (e) {
      return frame('Đợt tặng quà mới',
        '<div class="emp"><div class="e1">⚠️</div><div class="e2">' + h(errMsg(e)) + '</div></div>');
    }
  }
  if (!p.nam) p.nam = tqd.dm.nam;
  if (!p.trang_thai_dot) p.trang_thai_dot = 'Nhap';
  tqd.form = p;
  tqVeLapDot(p);
}

function tqVeLapDot(p) {
  var dm = tqd.dm || {};
  var tenDip = function (k) {
    var x = (dm.dip || []).filter(function (d) { return d.k === k; })[0];
    return x ? x.ten : '';
  };
  var tenTt = function (k) {
    var x = (dm.trang_thai || []).filter(function (d) { return d.k === k; })[0];
    return x ? x.ten : '';
  };

  var than = '<div class="vxf">' +
    tqChon('Dịp', 'tqdDip', tenDip(p.dip), 'Tết, Trung thu, Giáng sinh...') +
    tqO('Năm', 'tqdNam', p.nam, '2026') +
    tqO('Tên đợt', 'tqdTen', p.ten_dot, 'Để trống thì máy tự đặt theo dịp và năm') +

    '<div class="vxl" style="margin-top:18px">KHUNG THỜI GIAN</div>' +
    tqO('Từ ngày', 'tqdTu', p.tu_ngay, 'dạng 2026-09-01') +
    tqO('Đến ngày', 'tqdDen', p.den_ngay, 'dạng 2026-09-25') +
    '<div class="tqwarn">Đến ngày là mốc để hệ nhắc người phụ trách trước ba ngày. ' +
    'Để trống thì không nhắc ai cả.</div>' +

    '<div class="vxl" style="margin-top:18px">MẶC ĐỊNH CỦA ĐỢT</div>' +
    tqChon('Mẫu lời chúc', 'tqdMau', p.mau_loi_chuc_md, 'Áp cho mọi phiếu trong đợt') +
    tqChon('Trạng thái', 'tqdTt', tenTt(p.trang_thai_dot)) +
    '<div class="tqwarn">Chỉ đợt <b>Đang chạy</b> mới được xuất hoá đơn quà. ' +
    'Đợt vừa lập nên để Nháp cho tới khi soát xong danh sách.</div>' +
    tqO('Ghi chú', 'tqdGc', p.ghi_chu) +
    '</div>';

  var nut = '<button class="btn" id="tqdLuu">Lưu đợt</button>';
  var b = frame(p.name ? 'Sửa đợt tặng quà' : 'Đợt tặng quà mới', than, { footer: nut });

  function goO(id, truong) {
    var o = document.getElementById(id);
    if (o) o.oninput = function () { p[truong] = o.value; };
  }
  goO('tqdNam', 'nam'); goO('tqdTen', 'ten_dot');
  goO('tqdTu', 'tu_ngay'); goO('tqdDen', 'den_ngay'); goO('tqdGc', 'ghi_chu');

  var cDip = document.getElementById('tqdDip');
  if (cDip) cDip.onclick = function () {
    sheet('Dịp tặng quà', (dm.dip || []).map(function (x) {
      return { value: x.k, label: x.ten, icon: '🎁' };
    }), p.dip, function (x) { p.dip = x.value; tqVeLapDot(p); });
  };
  var cMau = document.getElementById('tqdMau');
  if (cMau) cMau.onclick = function () {
    sheet('Mẫu lời chúc', (dm.mau || []).map(function (x) {
      return { value: x.name, label: x.ten_mau || x.name, phu: x.dip || '', icon: '💌' };
    }), p.mau_loi_chuc_md, function (x) { p.mau_loi_chuc_md = x.value; tqVeLapDot(p); });
  };
  var cTt = document.getElementById('tqdTt');
  if (cTt) cTt.onclick = function () {
    sheet('Trạng thái đợt', (dm.trang_thai || []).map(function (x) {
      return { value: x.k, label: x.ten, icon: x.k === 'Dang chay' ? '🟢' : (x.k === 'Da dong' ? '⚪' : '📝') };
    }), p.trang_thai_dot, function (x) { p.trang_thai_dot = x.value; tqVeLapDot(p); });
  };

  var bl = document.getElementById('tqdLuu');
  if (bl) bl.onclick = function () { tqdLuu(p); };
}

async function tqdLuu(p) {
  if (!p.dip) return toast('Chưa chọn dịp. Mã đợt sinh ra từ dịp và năm.', 4200);
  if (!String(p.nam || '').match(/^\d{4}$/)) return toast('Năm phải là bốn chữ số.', 4200);
  busy(1);
  var kq;
  try {
    kq = await api('vagabond.tang_qua.luu_dot', {
      ma: p.name || '',
      du_lieu: JSON.stringify({
        dip: p.dip, nam: p.nam, ten_dot: p.ten_dot || '',
        tu_ngay: p.tu_ngay || '', den_ngay: p.den_ngay || '',
        mau_loi_chuc_md: p.mau_loi_chuc_md || '',
        trang_thai_dot: p.trang_thai_dot || 'Nhap',
        ghi_chu: p.ghi_chu || ''
      })
    });
  } catch (e) { busy(0); return toast(errMsg(e), 6000); }
  busy(0);
  toast('Đã lưu đợt ' + kq.ma);
  tq.dot = kq.ma; tq.ten_dot = kq.ten_dot;
  tq.loc = 'tat_ca'; tq.nhom = ''; tq.tim = '';
  tqd.form = null;
  reset(scrTqDot);
  go(scrTqDs);
}

/* ---------- Man: dan danh sach tu bang tinh ---------- */

async function scrTqDan() {
  tqCss();
  if (!tq.dot) return go(scrTqDot);
  tqVeDan(null);
}

function tqVeDan(xem) {
  var dm = tq.dm || {};
  var cot = (xem && xem.cot) || ['Tên khách', 'Số lượng', 'Địa chỉ',
    'SĐT hoặc người nhận', 'Ghi chú giao hàng', 'Ghi chú'];

  var bang = '';
  if (xem) {
    if (!xem.so_dong) {
      bang = '<div class="tqwarn">Chưa đọc ra dòng nào. Nhớ quét cả vùng trong ' +
        'bảng tính rồi Copy, đừng gõ tay từng dòng.</div>';
    } else {
      bang = '<div class="tqok">Đọc ra <b>' + xem.so_dong + '</b> dòng, tổng <b>' +
        xem.tong_qua + '</b> phần quà.' +
        (xem.thieu_ten && xem.thieu_ten.length
          ? ' Dòng thiếu tên khách sẽ bị bỏ qua: ' + xem.thieu_ten.join(', ') + '.'
          : '') + '</div>' +
        (xem.ds || []).slice(0, 12).map(function (d) {
          return '<div class="tqmon"><span class="m1">' + h(d.ten_khach || '(thiếu tên)') +
            '<div style="font-size:12px;color:#667085">' +
            h([d.so_luong + ' phần', d.sdt_nhan_tho, d.dia_chi].filter(Boolean).join(' · ').slice(0, 90)) +
            '</div></span></div>';
        }).join('') +
        (xem.so_dong > 12 ? '<div class="vxl">... và ' + (xem.so_dong - 12) + ' dòng nữa</div>' : '');
    }
  }

  var than = '<div class="vxf">' +
    '<div class="tqwarn">Trong bảng tính, quét đúng sáu cột theo thứ tự này rồi Copy:<br>' +
    '<b>' + cot.map(h).join(' &rarr; ') + '</b><br>' +
    'Ngăn cột bằng TAB, tức là copy thẳng từ Google Sheet hay Excel là đúng rồi. ' +
    'Thiếu cột cuối cũng không sao.</div>' +
    '<textarea class="vxi" id="tqDanO" rows="8" placeholder="Dán vào đây">' +
    h(tqd.dan || '') + '</textarea>' +
    '<button class="vxb o" id="tqDanXem" style="margin-top:8px">👀 Xem thử đọc ra gì</button>' +
    '<div style="margin-top:10px">' + bang + '</div>' +
    '<div class="vxl" style="margin-top:18px">ÁP CHUNG CHO CẢ LOẠT</div>' +
    '<button class="vxb o" id="tqDanMon">🎁 Món quà: ' +
    (tqd.mon.length ? h(tqd.mon.map(function (m) { return m.ten_mon; }).join(', ')) : 'chưa chọn') +
    '</button>' +
    '<div class="tqwarn">Số lượng lấy theo cột Số lượng của từng dòng, ' +
    'món thì cả loạt dùng chung.</div>' +
    '</div>';

  var nut = '<button class="btn" id="tqDanNap"' +
    (xem && xem.so_dong ? '' : ' disabled') + '>Nạp ' +
    ((xem && xem.so_dong) || 0) + ' dòng vào đợt</button>';

  var b = frame('Dán danh sách vào đợt', than, { footer: nut });

  var o = document.getElementById('tqDanO');
  if (o) o.oninput = function () { tqd.dan = o.value; };
  var bx = document.getElementById('tqDanXem');
  if (bx) bx.onclick = tqDanXem;
  var bm = document.getElementById('tqDanMon');
  if (bm) bm.onclick = tqDanChonMon;
  var bn = document.getElementById('tqDanNap');
  if (bn) bn.onclick = function () { tqDanNap(xem); };
}

async function tqDanXem() {
  var o = document.getElementById('tqDanO');
  if (o) tqd.dan = o.value;
  if (!(tqd.dan || '').trim()) return toast('Chưa dán gì vào ô.');
  busy(1);
  var xem;
  try { xem = await api('vagabond.tang_qua.xem_truoc_dan', { van_ban: tqd.dan }); }
  catch (e) { busy(0); return toast(errMsg(e), 6000); }
  busy(0);
  tqVeDan(xem);
}

async function tqDanChonMon() {
  busy(1);
  var ds;
  try {
    ds = await getList('Item', {
      fields: ['name', 'item_name', 'image'],
      filters: { disabled: 0, is_sales_item: 1 },
      limit_page_length: 400, order_by: 'item_name'
    });
  } catch (e) { busy(0); return toast('Không tải được danh mục món'); }
  busy(0);
  sheet('Món quà chung cho cả loạt', ds.map(function (x) {
    return { value: x.name, label: x.item_name || x.name, phu: x.name,
      img: x.image || '', icon: '🎁', tim: x.name };
  }), '', function (x) {
    tqd.mon = [{ mon: x.value, ten_mon: x.label, so_luong: 1 }];
    tqDanXem();
  }, true);
}

async function tqDanNap(xem) {
  if (!xem || !xem.so_dong) return toast('Bấm Xem thử trước đã.');
  if (!tqd.mon.length) return toast('Chưa chọn món quà chung.', 4200);
  var ok = await hoiCo('Nạp danh sách',
    'Thêm ' + xem.so_dong + ' khách vào đợt ' + (tq.ten_dot || tq.dot) + '?\n\n' +
    'Món: ' + tqd.mon.map(function (m) { return m.ten_mon; }).join(', ') + '\n' +
    'Số lượng lấy theo từng dòng, tổng ' + xem.tong_qua + ' phần.',
    'Nạp vào đợt');
  if (!ok) return;
  busy(1);
  var kq;
  try {
    kq = await api('vagabond.tang_qua.nap_dan', {
      dot: tq.dot, van_ban: tqd.dan,
      mon: JSON.stringify(tqd.mon.map(function (m) { return { mon: m.mon }; }))
    });
  } catch (e) { busy(0); return toast(errMsg(e), 7000); }
  busy(0);
  toast(kq.loi_nhan || 'Đã nạp', 7000);
  tqd.dan = '';
  back();
}


/* Hai duong them khach vao mot dot. Hoi truoc roi moi mo man, vi hai duong
   nay danh cho hai tinh huong khac han: mot ben la danh sach da co san
   trong bang tinh, mot ben la chon tay tu danh muc khach da xep hang. */
function tqThemKhachKieuGi() {
  sheet('Thêm khách vào đợt', [
    { value: 'dan', label: 'Dán danh sách từ bảng tính',
      phu: 'Copy nguyên vùng từ Google Sheet hay Excel', icon: '📋' },
    { value: 'tick', label: 'Tick chọn khách đã có hạng',
      phu: 'Lọc theo hạng thành viên trong hệ', icon: '👥' }
  ], '', function (x) {
    if (x.value === 'dan') { tqd.dan = ''; tqd.mon = []; return go(scrTqDan); }
    tqb.chon = {}; tqb.tim = ''; tqb.hang = '';
    go(scrTqThemLoat);
  });
}


/* Mo mot dot da co ra sua. Doc lai tu may chu chu khong dung con so dang
   hien tren the: the chi mang vai o de ve, con form thi can du. */
async function tqSuaDot(maDot) {
  busy(1);
  var d;
  try {
    /* Doc bang get_list loc theo ten chu khong dung frappe.client.get:
       ca he dang di duong get_list, va o day chi can vai o. */
    var r = await getList('Vagabond Dot Tang Qua', {
      filters: { name: maDot },
      fields: ['name', 'dip', 'nam', 'ten_dot', 'tu_ngay', 'den_ngay',
        'mau_loi_chuc_md', 'trang_thai_dot', 'ghi_chu'],
      limit_page_length: 1
    });
    d = (r || [])[0];
    if (!d) { busy(0); return toast('Không tìm thấy đợt ' + maDot); }
  } catch (e) { busy(0); return toast(errMsg(e), 6000); }
  busy(0);
  tqd.form = {
    name: maDot, dip: d.dip, nam: d.nam, ten_dot: d.ten_dot,
    tu_ngay: d.tu_ngay || '', den_ngay: d.den_ngay || '',
    mau_loi_chuc_md: d.mau_loi_chuc_md || '',
    trang_thai_dot: d.trang_thai_dot || 'Nhap', ghi_chu: d.ghi_chu || ''
  };
  go(scrTqLapDot);
}

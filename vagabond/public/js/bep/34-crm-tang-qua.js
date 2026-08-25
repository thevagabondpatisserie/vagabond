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
      '</div></div>';
  }).join('') : '<div class="emp"><div class="e1">🎁</div>' +
    '<div class="e2">Chưa có đợt tặng quà nào</div>' +
    '<div class="e3">Mở Desk tạo một đợt, ví dụ Tết Bính Ngọ 2026, rồi quay lại đây</div></div>';

  var b = frame('Tặng quà khách VIP', than);
  b.onclick = function (e) {
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
    { fab: 1, onFab: function () { tq.form = null; go(scrTqSua); } });

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
    '</div>';

  var nut = '<button class="btn" id="tqLuu">Lưu</button>' +
    (moi ? '<button class="btn gh" id="tqLuuTiep" style="margin-top:9px">Lưu và thêm khách tiếp theo</button>' : '');

  var b = frame(moi ? 'Thêm khách nhận quà' : 'Phiếu tặng quà', than, { footer: nut });
  tqGanSuKien(b, dm, p);
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

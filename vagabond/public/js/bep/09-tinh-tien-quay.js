/* ---------- Tinh tien quay: D1 (TCV) va NVHTN (08/08/2026) ----------
   Buoc 1 chon quay, buoc 2 chon NGUON DON cho tung bill: Tai cho, Mang ve,
   hoac app (Grab, Be, GreenSM, Shopee) - dung nguyen tac "vao nguon nao ra
   nguon do" cua SOP. Bill luu bang tao_don_tay thanh Sales Invoice NHAP,
   ra soat va ghi so cuoi ngay tren man Doanh thu Sales. Chuyen khoan thi
   hien VietQR dien san so tien + so phieu. Chua tru kho, chua in bill. */
var posDon = null, posHomNayTxt = null, posQuay = null;
var posDsNgay = null; /* ngay dang xem o danh sach hoá đơn; null = hom nay */
var posLocTt = 'tat_ca', posLocNg = '', posLocHd = ''; /* chip loc: tinh trang x nguon-pt x trang thai HDDT */
function posNgayVn(iso) {
  var d = new Date(iso + 'T00:00:00');
  var thu = ['Chủ nhật', 'Thứ hai', 'Thứ ba', 'Thứ tư', 'Thứ năm', 'Thứ sáu', 'Thứ bảy'][d.getDay()];
  var p = iso.split('-');
  return thu + ', ' + p[2] + '/' + p[1] + '/' + p[0];
}
/* Ma bill sinh ngay luc mo bill, dung lam NOI DUNG CHUYEN KHOAN in trong
   ma QR. Sinh truoc thi khach quet duoc ngay, khoi doi luu bill xong;
   luu bill thi chinh ma nay di vao o ma tham chieu de ke toan doi soat
   dung cai khach da chuyen (giong ma HD tren bill Fabi). */
/* TIEN TO THEO DIEM BAN, anh Viet 31/08/2026:

     "Don o Tran Cao Van se mang ma TCV thay vi VGB, NVHTN thi la NVH, con o
      307/1 Nguyen Van Troi Sales Online thi tien to la SOL."

   Loi ich that: ke toan nhin sao ke ngan hang la biet ngay giao dich thuoc
   diem nao, khong phai mo tung don ra tra. Va noi dung chuyen khoan gon lai
   con dung mot chuoi tam ky tu, khong con khoang trang de app ngan hang nao
   cat bot lam mat phan duoi.

   Bang tien to lay tu MAY CHU (`ma_bill.py` qua CFGBH), khong chep lai o
   day: chep lai la den luc them diem ban thu ba, may chu doc duoc tien to
   moi ma man hinh van sinh VGB.

   Bill cu mang VGB thi giu nguyen mai mai, chi khong sinh moi nua. */
/* Bang tien to da tu may chu ve chua. Chua ve thi khong duoc sinh lai ma,
   khong thi ma dang dung lai bi doi thanh VGB. */
/* Nhan ngan cho dong giam gia tren man hinh khach. Rong la de nguyen chu
   "Giam gia" nhu cu. THUAN theo nghia khong cham DOM. */
function posLyDoGiam() {
  if (!posDon) return '';
  /* Tru diem, hoac chuong trinh khuyen mai gan voi ho so khach: ca hai deu
     la uu dai cua thanh vien. Voucher go tay thi khong phai. */
  var coDiem = !!(posDon.diemVe && posDon.diemVe.so_tien);
  var coTv = !!(posDon.khach_ma && posDon.kmKq && (posDon.kmKq.ap || []).length);
  if (coDiem || coTv) return 'thành viên';
  if (posDon.maVc || posDon.km) return 'ưu đãi';
  return '';
}
function posCoBangTienTo() {
  var b = (CFGBH || {}).ma_tien_to;
  if (!b) return false;
  for (var k in b) { if (b.hasOwnProperty(k)) return true; }
  return false;
}
function posTienTo(maDiem) {
  var c = CFGBH || {};
  var b = c.ma_tien_to || {};
  var d = posDiemCua(maDiem);
  return b[d] || c.ma_tien_to_cu || 'VGB';
}
function posMaBill(maDiem) {
  var c = CFGBH || {};
  /* Bang chu co tinh thieu B I O Z 0 1 2: khach hay doc nham chung thanh
     8 1 0 2 khi phai go tay noi dung chuyen khoan. */
  var chu = c.ma_chu_sinh || 'ACDEFGHJKLMNPQRSTUVWXY3456789';
  var n = parseInt(c.ma_dai_duoi, 10) || 5;
  var s = '';
  for (var i = 0; i < n; i++) s += chu.charAt(Math.floor(Math.random() * chu.length));
  return posTienTo(maDiem) + s;
}
function posMoi() {
  posSepayNhan = 0; posSepayGoiY = 0;
  /* Chế độ mặc định phải là chế độ CÓ THẬT của điểm bán này. Điểm Sales
     Online không bán tại chỗ, để nguyên 'Tại chỗ' là máy chủ từ chối đơn với
     câu "Nguồn đơn (trống) không có trong danh mục". */
  var ds0 = posDsCheDo();
  var mac = (ds0[0] && ds0[0].v) || 'Tại chỗ';
  return { che_do: mac, ma: '', bill: posMaBill(), pt: 'Tiền mặt', mtc: '', ten: '', sdt: '', giam: '', ship: '', dua: '', ghi_chu: '', km: null, so_ban: '', khach_no: null, xhd_mo: false, xh: { mst: '', ten: '', dc: '', email: '' }, mon: [], ctkm: [], combo: [], maVc: '', otpKm: '', kmKq: null, khach_ma: '', khach_hang: '', diemThe: null, diemTt: null, diemNhap: '', diemPhien: null, diemHan: 0, diemVe: null };
}
function posKmGiam(km, tong) {
  if (!km) return 0;
  if (km.loai === 'Phần trăm') return Math.round(tong * flt0(km.gia_tri) / 100);
  return Math.round(flt0(km.gia_tri));
}
/* Tien SePay da nhan cho ma bill dang mo - poll 5 giay mot lan khi dang
   chia QR chuyen khoan, de khach chuyen den noi la cashier thay ngay. */
var posSepayNhan = 0, posPollId = null;
/* So khoan tien DUNG BANG so phai thu vua ve ma chua bill nao nhan.

   Anh Viet 01/09/2026 bo hoan toan phep tu gach theo khung gio: khach A tra
   85.000 luc 14h00 khong ai gach, khach B goi 85.000 luc 14h20 la may xanh
   nham ngay, thu ngan tra banh ma tien chua ve. Nen o day chi DEM, roi moi
   thu ngan bam nut "Do tien chuyen khoan" de tu nhin va tu chon. */
var posSepayGoiY = 0;
function posPollTat() { if (posPollId) { clearInterval(posPollId); posPollId = null; } }
function posPollBat(ma, tien) {
  posPollTat();
  posPollId = setInterval(async function () {
    /* Roi man tinh tien thi tu tat, khoi goi may chu vo ich. */
    if (!document.getElementById('posNd')) return posPollTat();
    try {
      var kq = await api('vagabond.ban_hang.pos_kiem_sepay', { noi_dung: ma, tien: tien });
      var doi = false;
      if (kq && flt0(kq.nhan) > posSepayNhan) { posSepayNhan = flt0(kq.nhan); doi = true; }
      var gy = kq ? (parseInt(kq.goi_y, 10) || 0) : 0;
      if (gy !== posSepayGoiY) { posSepayGoiY = gy; doi = true; }
      if (doi && document.getElementById('posNd')) go(scrPosQuay, true);
      if (kq && kq.du) posPollTat();
    } catch (e) { }
  }, 5000);
}
function flt0(v) { return parseFloat(v) || 0; }
function posSoTien(v) { return parseFloat(String(v == null ? '' : v).replace(/[^0-9]/g, '')) || 0; }
/* Các chế độ bán của ĐÚNG điểm bán đang đứng.

   Anh Việt 24/08/2026: *"cơ bản chỉ là khác điểm bán thôi chứ còn các nghiệp
   vụ bên trong đều phải đầy đủ hết"*. Điểm có quầy tiền mặt thì bán Tại chỗ
   và Mang về; điểm Sales Online thì không có quầy nên chế độ của nó chính là
   các nguồn đơn nó nhận (GrabFood, ShopeeFood, BeFood, GreenSM).

   Pancake bị loại ở cả hai: đơn Pancake tự đồng bộ về màn Doanh số, gõ tay
   lại là tạo đơn trùng. */
function posDsCheDo() {
  var ic = {};
  (((CFGBH || {}).nguon) || []).forEach(function (n) { ic[n.v] = n; });
  function bay(v) { var n = ic[v] || {}; return { v: v, ic: n.ic || '', lg: n.lg || '' }; }
  var d = posQuay || {};
  var nguon = (d.nguon || []).filter(function (v) { return v !== 'Pancake'; });
  /* NGHE THEO CÀI ĐẶT ĐIỂM BÁN, không nối cứng.

     Trước 01/09/2026 điểm có quầy thì màn này bỏ qua cấu hình của điểm và
     tự nối thêm TOÀN BỘ nguồn sàn của cả hệ vào. Nghĩa là màn Cài đặt Điểm
     bán nói một đằng còn màn tính tiền làm một nẻo, đúng cái mà quy tắc
     một nguồn duy nhất hứa sẽ không xảy ra. Nay đọc thẳng danh sách nguồn
     của điểm.

     Điểm có quầy vẫn luôn có Tại chỗ và Mang về đứng đầu, vì đó là hai chế
     độ bán của một cái quầy vật lý, không phải nguồn đơn. Thiếu chúng thì
     không bán tại quầy được. */
  if (posCoQuay()) {
    var dau = ['Tại chỗ', 'Mang về'];
    var them = nguon.filter(function (v) { return dau.indexOf(v) < 0; });
    return [{ v: 'Tại chỗ', ic: '🏬' }, { v: 'Mang về', ic: '🥡' }].concat(them.map(bay));
  }
  /* Điểm không có quầy: chế độ chính là nguồn đơn của nó. */
  return nguon.map(bay);
}
/* Điểm bán đang đứng có quầy tiền mặt không. Không có quầy thì không có ca
   làm việc, không có tiền thối, và bill của nó nằm ở nhóm đơn online. */
function posCoQuay() {
  return !!(posQuay && posQuay.quay);
}
/* Hai nut in tren man bao thanh cong, dung chung cho ca luong tien mat lan
   luong chuyen khoan.

   Vi sao tach ra thanh mot ham: truoc 19/08/2026 hai man tu ve hai lan, va
   ca hai deu khoa NUT IN TEM sau dieu kien "bill co mon nuoc". Trong khi
   chinh ham in tem da doi tu 10/08 theo anh Viet - *"moi mon deu duoc in
   tem chu khong rieng mon nuoc, hop entremet cung can tem"* - ma cai khoa
   thi khong ai doi theo. Ket qua: don GrabFood ban mot hu banh Almond
   Tuile thi khong co nut in tem nao ca (De bao 19/08/2026).

   Nay TEM hien khi bill co bat ky mon nao, con PHIEU LAM MON van chi hien
   khi co mon nuoc - phieu do la phieu cho quay pha che, bill toan banh thi
   in ra khong ai dung. */
function posNutIn(d) {
  var mon = (d && d.mon) || [];
  if (!mon.length) return '';
  var coNuoc = posCoNuoc(mon);
  return '<div style="display:flex;gap:8px;margin-top:8px">' +
    (coNuoc ? '<button class="btn gh" data-pm style="flex:1;margin:0">🧾 In phiếu làm món</button>' : '') +
    '<button class="btn gh" data-tem style="flex:1;margin:0">🏷 In tem món</button></div>';
}

function posNguonThuc() {
  if (!posQuay || !posDon) return '';
  /* Điểm không có quầy: chế độ đã CHÍNH LÀ nguồn đơn, không phải ánh xạ qua
     hai nhãn Tại chỗ / Mang về. */
  if (!posCoQuay()) return posDon.che_do;
  if (posDon.che_do === 'Tại chỗ') return posQuay.tai_cho;
  if (posDon.che_do === 'Mang về') return posQuay.mang_ve;
  return posDon.che_do;
}
function posDoc() {
  if (!posDon) return;
  var g = function (id) { var o = document.getElementById(id); return o ? o.value : null; };
  var v;
  v = g('posMa'); if (v !== null) posDon.ma = v;
  v = g('posTen'); if (v !== null) posDon.ten = v;
  v = g('posSdt'); if (v !== null) posDon.sdt = v;
  v = g('posMtc'); if (v !== null) posDon.mtc = v;
  if (!posDon.bill) posDon.bill = posMaBill();
  v = g('posGiam'); if (v !== null) posDon.giam = posSoTien(v) ? String(posSoTien(v)) : '';
  v = g('posShip'); if (v !== null) posDon.ship = posSoTien(v) ? String(posSoTien(v)) : '';
  v = g('posDua'); if (v !== null) posDon.dua = posSoTien(v) ? String(posSoTien(v)) : '';
  v = g('posGhiChu'); if (v !== null) posDon.ghi_chu = v;
  v = g('posXhMst'); if (v !== null) posDon.xh.mst = v;
  v = g('posXhTen'); if (v !== null) posDon.xh.ten = v;
  v = g('posXhDc'); if (v !== null) posDon.xh.dc = v;
  v = g('posXhEmail'); if (v !== null) posDon.xh.email = v;
  v = g('posDiemNhap'); if (v !== null) posDon.diemNhap = v;
}
/* Buoc chon quay: vao card la hoi, khong nho lua chon cu (anh Viet 08/08). */
async function scrPosChonQuay() {
  await cfgBanHang();
  /* Thumbnail la anh cua hang that (anh Viet gui 09/08), nhin phat biet
     ngay minh dang chon quay nao. Anh nam trong repo, thieu thi lui ve
     bieu tuong cu. */
  /* MỘT NGUỒN DUY NHẤT cho danh sách điểm bán (anh Việt 24/08/2026).

     Trước đây danh sách này là hai quầy đọc từ cấu hình, cộng thêm một thẻ
     Sales Online GÕ CỨNG ngay trong màn hình. Thẻ gõ cứng đó bấm vào thì
     nhảy thẳng sang màn Doanh số, nên điểm Sales chưa bao giờ có màn tính
     tiền: không mã voucher, không chương trình khuyến mãi, không combo,
     không tích điểm. Trong khi nghiệp vụ bên trong của ba điểm là như nhau,
     chỉ khác chỗ đứng.

     Nay cả ba đọc chung từ `diem`, tức từ đúng bảng Điểm bán mà màn Cài đặt
     sửa. Mở điểm thứ tư là khai trong Cài đặt, không phải sửa mã rồi deploy. */
  var dsAll = ((CFGBH || {}).diem) || ((CFGBH || {}).quay) || [];
  var suaAnh = typeof isSales === 'function' ? isSales() : false;
  var html = '<div class="sec">Chọn điểm bán</div>';
  dsAll.forEach(function (q, i) {
    html += '<div class="card" style="margin-bottom:12px;overflow:hidden;padding:0;position:relative">' +
      '<div data-q="' + i + '" style="cursor:pointer">' +
      (q.anh
        ? '<img src="' + h(q.anh) + '" alt="" style="width:100%;height:150px;object-fit:cover;display:block" onerror="this.style.display=\'none\'">'
        : '<div style="height:96px;display:flex;align-items:center;justify-content:center;background:#f6f7f9;color:#c3c8d4;font-size:34px">🏬</div>') +
      '<div style="display:flex;align-items:center;gap:10px;padding:13px 14px">' +
      '<div style="flex:1"><div class="h1" style="font-size:17px;font-weight:700">' + h(q.ten) + '</div>' +
      '<div class="h2" style="color:#98a2b3;font-size:13px">' + h(q.phu || '') + '</div></div>' +
      '<span style="color:#c3c8d4;font-size:22px">&#8250;</span></div></div>' +
      (suaAnh
        ? '<button data-anh="' + h(q.ma) + '" style="position:absolute;top:9px;right:9px;border:0;background:rgba(16,24,40,.62);color:#fff;border-radius:999px;padding:6px 12px;font-size:12px;font-weight:700;cursor:pointer;font-family:inherit">✎ Ảnh</button>'
        : '') +
      '</div>';
  });
  html += '<div style="text-align:center;color:#a0a6b4;font-size:12px;padding:4px 10px 10px">Chọn đúng điểm bán mình đang đứng - doanh thu và đối soát tách riêng từng điểm, không gộp chung</div>';
  var b = frame('Tính tiền - hoá đơn bán hàng', html);
  b.onclick = function (e) {
    var a = e.target.closest('[data-anh]');
    if (a) return posDoiAnhQuay(a.getAttribute('data-anh'));
    var r = e.target.closest('[data-q]');
    if (!r) return;
    var q = dsAll[+r.getAttribute('data-q')];
    if (!q) return;
    /* Đổi điểm là đổi bộ máy in và đổi khổ giấy, nên bỏ luôn đơn đang gõ dở
       để không mang giá và nguồn của điểm cũ sang điểm mới. */
    if (posQuay && posQuay.ma !== q.ma) posDon = null;
    posQuay = q;
    posHomNayTxt = null;
    go(scrPosQuay);
  };
}

/* Doi anh thumbnail diem ban ngay trong app: quan ly chup anh cua hang
   bang dien thoai roi tai len, khong phai nho ky thuat (anh Viet
   10/08/2026). Anh luu thanh File cua Frappe, duong dan cat vao default. */
async function posDoiAnhQuay(ma) {
  var inp = document.createElement('input');
  inp.type = 'file';
  inp.accept = 'image/*';
  inp.onchange = async function () {
    var f = inp.files && inp.files[0];
    if (!f) return;
    if (f.size > 8 * 1024 * 1024) return toast('Ảnh nặng quá 8MB, vui lòng chụp lại hoặc giảm kích thước.', 4000);
    busy(true);
    try {
      var fd = new FormData();
      fd.append('file', f, f.name);
      fd.append('is_private', '0');
      fd.append('folder', 'Home');
      var rs = await fetch('/api/method/upload_file', {
        method: 'POST',
        headers: { 'X-Frappe-CSRF-Token': (window.frappe && frappe.csrf_token) || '' },
        body: fd,
        credentials: 'same-origin'
      });
      var kq = await rs.json();
      var url = ((kq || {}).message || {}).file_url || '';
      if (!url) throw new Error('Tải ảnh lên không thành công');
      await api('vagabond.ban_hang.pos_anh_quay_luu', { ma: ma, url: url });
      CFGBH = null;
      busy(false);
      toast('Đã đổi ảnh điểm bán.');
      go(scrPosChonQuay, true);
    } catch (e) {
      busy(false);
      toast((e && e.message) || 'Không tải được ảnh lên.', 4000);
    }
  };
  inp.click();
}
/* Logo GrabFood, GreenSM, ShopeeFood... moi cai mot ti le khac nhau (co cai
   rong gap 3 lan chieu cao), de chung mot dong voi chu thi chu bi day tran
   ra ngoai nut (anh Viet 09/08). Nay moi logo deu duoc gioi han CUNG MOT
   CHIEU CAO va khong bao gio rong qua nut - nhin ngang hang, chu xuong
   dong ben duoi nen nut nao cung vuong van bang nhau. */
function posONhan(n, cao) {
  cao = cao || 22;
  var k = 'height:' + cao + 'px;max-width:100%;flex:none;display:flex;align-items:center;justify-content:center';
  if (n.lg) return '<span style="' + k + '"><img src="' + n.lg + '" style="max-width:100%;max-height:100%;width:auto;height:auto;object-fit:contain;display:block"></span>';
  if (n.ic) return '<span style="' + k + ';width:' + cao + 'px;font-size:' + Math.round(cao * 0.86) + 'px">' + n.ic + '</span>';
  return '';
}
function posNutNguon(ds, chon) {
  return ds.map(function (n) {
    var on = n.v === chon;
    return '<button class="pnc" data-nd="' + h(n.v) + '" style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;min-height:66px;padding:6px 4px;border-radius:10px;overflow:hidden;border:1.5px solid ' + (on ? '#0d9488;background:#ccfbf1;color:#0f766e' : '#e5e7eb;background:#fff;color:#374151') + '">' +
      posONhan(n) +
      '<span style="font-size:12.5px;line-height:1.15;text-align:center;font-weight:' + (on ? '700' : '500') + '">' + h(n.v) + '</span></button>';
  }).join('');
}
function posNutPt(ds, chon) {
  return ds.map(function (p) {
    var on = p.v === chon;
    return '<button class="ptc" data-pt="' + h(p.v) + '" style="display:flex;align-items:center;justify-content:center;gap:8px;min-height:56px;padding:8px 10px;border-radius:10px;overflow:hidden;border:1.5px solid ' + (on ? '#0d9488;background:#ccfbf1;color:#0f766e' : '#e5e7eb;background:#fff;color:#374151') + '">' +
      posONhan({ lg: p.lg, ic: p.lg ? '' : (p.ic || '🏦') }, 24) +
      /* min-width:0 để nhãn dài như "Chuyển khoản ngân hàng" xuống dòng
         gọn thay vì bị cắt cụt bởi overflow:hidden của nút. */
      '<span style="flex:0 1 auto;min-width:0;font-size:14px;line-height:1.3;font-weight:' + (on ? '700' : '500') + '">' + h(p.v) + '</span></button>';
  }).join('');
}
/* ---------------- Ca lam viec tai quay ----------------
   Mo ca khai tien le dau ca. Chot ca DEM MU: thu ngan chi thay o trong de
   go so minh dem, khong thay so may - thay truoc thi go lai dung so do va
   phep doi soat vo nghia. Luat nam o vagabond/ca_quay.py. */
var caPos = null;

async function posCaVe() {
  var tt = document.getElementById('posCaTt'), nut = document.getElementById('posCaNut');
  if (!tt || !nut) return;
  try { caPos = await api('vagabond.ca_quay.tinh_trang', { quay: posQuay.ma }); }
  catch (e) { tt.textContent = 'Không đọc được ca: ' + ((e && e.message) || ''); return; }
  if (caPos.dang_mo) {
    tt.innerHTML = 'Ca <b>' + h(caPos.ma) + '</b> mở lúc ' + h(String(caPos.mo_luc).slice(11, 16)) +
      ' · tiền lẻ đầu ca <b>' + money(caPos.tien_le_dau_ca) + ' đ</b>';
    nut.textContent = 'Chốt ca';
    nut.style.display = '';
    nut.onclick = function () { go(scrChotCa); };
  } else {
    tt.textContent = 'Chưa mở ca. Mở ca để tiền mặt cuối ngày đối soát được.';
    nut.textContent = 'Mở ca';
    nut.style.display = '';
    nut.onclick = posMoCa;
  }
}

async function posMoCa() {
  var tien = await hoiSo('Mở ca ' + posQuay.ten, 'Tiền lẻ đầu ca đếm được trong két (đ)', '');
  if (tien === null) return;
  busy(true);
  try {
    var k = await api('vagabond.ca_quay.mo_ca', { quay: posQuay.ma, tien_le_dau_ca: tien });
    busy(false);
    toast('Đã mở ca ' + k.ma + ' · tiền lẻ ' + money(tien) + ' đ', 4000);
    posCaVe();
  } catch (e) { busy(false); baoTin((e && e.message) || 'Không mở được ca', 'Mở ca'); }
}

/* Man chot ca: moi phuong thuc mot o, go xong bam chot. Co lech thi may
   tra bang doi soat ve va doi ly do roi moi chot that. */
async function scrChotCa() {
  if (!posQuay || !caPos || !caPos.dang_mo) return go(scrPosQuay, true);
  var dsPt = caPos.phuong_thuc || ['Tiền mặt'];
  var html = '<div class="card" style="padding:13px 14px">' +
    '<b style="font-size:15px">Chốt ca ' + h(caPos.ma) + ' · ' + h(posQuay.ten) + '</b>' +
    '<div style="font-size:12.5px;color:#6b7280;margin-top:3px">Mở lúc ' + h(String(caPos.mo_luc).slice(11, 16)) +
    ' · tiền lẻ đầu ca ' + money(caPos.tien_le_dau_ca) + ' đ</div>' +
    '<div style="margin-top:9px;background:#fff6e5;border:1.5px solid #fde3a7;border-radius:9px;padding:9px 12px;font-size:12.5px;color:#8a5b00">' +
    'Đếm tiền TRƯỚC rồi mới gõ. Máy cố ý không hiện số hệ thống ở bước này - gõ đúng số mình đếm được, kể cả bằng 0.</div></div>';
  html += '<div class="sec">Số đếm được theo từng phương thức</div><div class="card" style="padding:12px 14px">' +
    dsPt.map(function (t, i) {
      return '<div style="display:flex;align-items:center;gap:10px;padding:7px 0' +
        (i ? ';border-top:1px solid #f2f4f7' : '') + '">' +
        '<div style="flex:1;font-size:14px;font-weight:600">' + h(t) + '</div>' +
        '<input class="tin caDem" data-pt="' + h(t) + '" inputmode="numeric" placeholder="0" style="width:150px;text-align:right;margin:0">' +
        '</div>';
    }).join('') + '</div>';
  html += '<div class="card" style="padding:12px 14px">' +
    '<div class="h2" style="margin-bottom:6px">Ghi chú ca (không bắt buộc)</div>' +
    '<input class="tin" id="caGhiChu" style="margin:0" placeholder="Bàn giao cho ai, sự cố trong ca...">' +
    '</div>';
  html += '<button class="btn" id="caChotNut" style="width:100%">Chốt ca và xem đối soát</button>';
  var b = frame('Chốt ca', html);
  b.querySelectorAll('.caDem').forEach(function (o) {
    o.oninput = function () { o.value = o.value.replace(/[^0-9]/g, ''); };
  });
  document.getElementById('caChotNut').onclick = async function () {
    var dem = {};
    b.querySelectorAll('.caDem').forEach(function (o) {
      if (o.value !== '') dem[o.getAttribute('data-pt')] = Number(o.value) || 0;
    });
    if (!Object.keys(dem).length) return toast('Chưa gõ số đếm nào. Ô nào không có tiền thì gõ 0.', 4500);
    var ghiChu = (document.getElementById('caGhiChu') || {}).value || '';
    busy(true);
    var k;
    try { k = await api('vagabond.ca_quay.chot_ca', { quay: posQuay.ma, dem: JSON.stringify(dem), ghi_chu: ghiChu }); }
    catch (e) { busy(false); return baoTin((e && e.message) || 'Không chốt được ca', 'Chốt ca'); }
    busy(false);
    if (k.can_ly_do) {
      var lyDo = await hoiChu('Ca đang lệch', caLechChu(k.bang) + '\n' + (k.nhac || 'Gõ lý do lệch:'), '', { nhieu_dong: 1 });
      if (lyDo === null || !String(lyDo).trim()) return toast('Chưa chốt: ca lệch thì phải có lý do.', 5000);
      busy(true);
      try { k = await api('vagabond.ca_quay.chot_ca', { quay: posQuay.ma, dem: JSON.stringify(dem), ghi_chu: ghiChu, ly_do_lech: lyDo }); }
      catch (e2) { busy(false); return baoTin((e2 && e2.message) || 'Không chốt được ca', 'Chốt ca'); }
      busy(false);
    }
    caPos = null;
    scrDoiSoatCa(k);
  };
}

function caLechChu(bang) {
  return (bang || []).filter(function (d) { return Math.abs(d.lech) >= 1; })
    .map(function (d) { return d.phuong_thuc + ': ' + (d.lech > 0 ? 'thừa ' : 'thiếu ') + money(Math.abs(d.lech)) + ' đ'; })
    .join('; ');
}

/* Bang doi soat sau khi chot: xanh la khop, do la lech, kem cot phai co
   (may cong tien le dau ca cho dong Tien mat). */
function scrDoiSoatCa(k) {
  var html = '<div class="card" style="padding:13px 14px">' +
    '<b style="font-size:15px">Đối soát ca ' + h(k.ma || '') + '</b>' +
    '<div style="font-size:13px;margin-top:4px;color:' + (k.tong_lech >= 1 ? '#b3261e' : '#0f766e') + ';font-weight:700">' +
    (k.tong_lech >= 1 ? 'Tổng lệch ' + money(k.tong_lech) + ' đ' : 'Khớp toàn bộ ✓') + '</div></div>';
  html += '<div class="card" style="padding:6px 14px">' +
    '<table style="width:100%;border-collapse:collapse;font-size:13px">' +
    '<tr style="color:#98a2b3;font-size:11.5px"><td style="padding:7px 0">PHƯƠNG THỨC</td>' +
    '<td style="text-align:right">PHẢI CÓ</td><td style="text-align:right">ĐÃ ĐẾM</td><td style="text-align:right">LỆCH</td></tr>' +
    (k.bang || []).map(function (d) {
      var lech = Math.round(d.lech);
      return '<tr style="border-top:1px solid #f2f4f7">' +
        '<td style="padding:8px 0">' + h(d.phuong_thuc) + (d.so_bill ? ' <span style="color:#98a2b3;font-size:11px">(' + d.so_bill + ' bill)</span>' : '') + '</td>' +
        '<td style="text-align:right">' + money(d.phai_co) + '</td>' +
        '<td style="text-align:right">' + money(d.dem) + '</td>' +
        '<td style="text-align:right;font-weight:700;color:' + (Math.abs(lech) >= 1 ? '#b3261e' : '#0f766e') + '">' +
        (lech > 0 ? '+' : '') + money(lech) + '</td></tr>';
    }).join('') + '</table></div>';
  html += '<div class="card" style="padding:11px 14px;font-size:12.5px;color:#6b7280;line-height:1.6">' +
    'Tiền mặt đếm được <b>' + money(k.tien_mat_dem || 0) + ' đ</b> của ca này sẽ thành tiền kỳ vọng ' +
    'khi lập Phiếu nộp quỹ (màn Kế toán · Nộp quỹ tiền mặt).</div>';
  html += '<button class="btn" id="caVeQuay" style="width:100%">Về màn quầy</button>';
  var b = frame('Đối soát ca', html);
  document.getElementById('caVeQuay').onclick = function () { go(scrPosQuay, true); };
}

async function scrPosQuay() {
  await cfgBanHang();
  posPollTat();
  /* Do QZ Tray NGAY luc mo man quay, khong doi toi luc bam In. Do luc bam
     la mat nhip user gesture va bi chan popup - xem ghi chu hai nhip o
     27-in-ngam.js. Khong await: do xong hay chua thi man van ve. */
  if (!posQuay) return go(scrPosChonQuay, true);
  /* Dò máy in SAU khi đã biết đứng ở điểm bán nào, và dò lại khi đổi điểm.
     Trước đây dò ngay dòng đầu, tức là trước cả bước chọn quầy, nên mọi máy
     đều nhận về hộp chung mảnh tên máy in của cả ba điểm. */
  inNgamDo(0, posQuay.ma);
  if (!posDon) posDon = posMoi();
  /* TU CHUA MA BILL KHI TIEN TO LECH (anh Viet 01/09/2026).

     Ma bill sinh mot lan luc mo bill. Neu luc do bang tien to chua ve tu
     may chu, hay may quay dang mo tu truoc lan deploy, thi ma sinh ra van
     mang tien to cu VGB du dang dung o Tran Cao Van - dung cai anh Viet
     nhin thay sang 01/09: *"ma chuyen khoan thi lai co chu TCV VGB... ma
     trong don thi lai khong co chu TCV"*.

     Nen moi lan ve man, neu bang tien to DA ve va gio hang con TRONG thi
     sinh lai ma cho dung diem. Chi lam khi gio hang trong: co mon roi la
     khach co the da quet ma QR, doi ma luc do la doi noi dung khach vua
     chuyen. */
  if (posCoBangTienTo() && !posDon.mon.length
      && posTienTo('') !== String(posDon.bill || '').slice(0, 3)) {
    posDon.bill = posMaBill();
  }
  var laApp = posDon.che_do !== 'Tại chỗ' && posDon.che_do !== 'Mang về';
  var nguonThuc = posNguonThuc();
  var dsPt = ptTheoNguon(nguonThuc);
  /* Nguon cua san giu lai lua chon cua thu ngan neu no van hop le. Truoc
     day dong nay dat lai o phuong thuc moi lan ve man, nen nguon nao di
     duoc hai phuong thuc thi bam chon xong ve man la mat lua chon. */
  if (laApp) {
    if (dsPt.length === 1) posDon.pt = dsPt[0].v;
    else if (!dsPt.some(function (p) { return p.v === posDon.pt; })) posDon.pt = '';
  }
  /* Don tai quay roi ve Tien mat, NHUNG chi khi Tien mat con bat. Truoc day
     go cung chuoi 'Tiền mặt' o day, nen ai tat phuong thuc do trong Cai dat
     la man tinh tien khong nut nao sang, bam Thu tien thi may chu nem loi.
     Lay dung phan tu dau danh sach lam duong lui. */
  else if (!posDon.pt || !dsPt.some(function (p) { return p.v === posDon.pt; })) {
    posDon.pt = dsPt.some(function (p) { return p.v === 'Tiền mặt'; })
      ? 'Tiền mặt'
      : ((dsPt[0] && dsPt[0].v) || '');
  }
  var tong = posDon.mon.reduce(function (t, m) { return t + m.qty * m.rate; }, 0);
  /* Voucher phan tram bam theo tong bill: them bot mon la so giam tu tinh lai. */
  if (posDon.km) posDon.giam = String(posKmGiam(posDon.km, tong) || '');
  /* Khuyen mai moi: so tien giam do MAY CHU tinh, may khach chi hien lai.
     Gio hang doi mot chut la tinh lai ngay, khong de so cu tren man hinh
     roi luc chot ra so khac (anh Viet 11/08/2026). */
  await posTinhKm();
  var giamTay = posSoTien(posDon.giam), dua = posSoTien(posDon.dua);
  /* PHÍ GIAO thu của khách. Màn nhập đơn tay bên Sales thu được từ lâu, màn
     quầy thì gửi cứng số 0, nên đơn tại quầy có ship là hoá đơn thiếu đúng
     khoản đó (anh Việt 01/09/2026: mọi tính năng phải có ở mọi màn). */
  var ship = posSoTien(posDon.ship);
  var giamKm = (posDon.kmKq && posDon.kmKq.tong_giam) || 0;
  var giam = giamTay + giamKm;
  /* The hang va tran diem phai tinh tren so tien TRUOC khi tru diem, dung
     nhu may chu lam - xem diem_otp.tran_dung_duoc.
     Phi giao KHONG tinh vao day: no la tien cong van chuyen, khong phai
     gia tri hang, nen khong duoc dung de day khach len hang cao hon. */
  await posTaiThe(tong - giam);
  var giamDiem = (posDon.diemVe && posDon.diemVe.so_tien) || 0;
  var phaiThu = Math.max(0, tong - giam - giamDiem) + ship;
  var qApp = laApp ? (quyPt(posDon.pt) || {}) : {};
  var html = '<div class="card" style="padding:8px 14px">' +
    '<div class="hub" data-t="posDoiQuay" style="padding:6px 0;border:none"><div class="ht"><div class="h2">Quầy đang bán · bấm để đổi</div><div class="h1">' + h(posQuay.ten) + '</div></div>' +
    '<div style="text-align:right;flex:none"><div class="h2" style="color:#6b7280">Ngày bán</div><div style="font-weight:700;font-size:14px">' + posNgayVn(today()) + '</div></div>' +
    '<span style="color:#c3c8d4;margin-left:4px">&#8250;</span></div></div>';
  /* O TO mo danh sach hoa don trong ngay (anh Viet 09/08) - cashier va
     quan ly bam phat vao ngay, khoi phai mo dong chu nho. */
  html += '<div class="card" data-t="posDsBill" style="padding:13px 14px;cursor:pointer;border:1.5px solid #7fe5f6;background:#f4feff">' +
    '<div style="display:flex;align-items:center;gap:10px;pointer-events:none">' +
    '<span style="font-size:24px">📋</span>' +
    '<div style="flex:1;min-width:0"><div style="font-weight:800;font-size:15.5px;color:#0b7c93">Danh sách hoá đơn bán hàng trong ngày</div>' +
    '<div id="posHomNay" style="font-size:12.5px;color:#0b7c93;margin-top:2px">' + h(posHomNayTxt || 'Đang đếm hoá đơn hôm nay...') + '</div></div>' +
    '<span style="color:#0b7c93;font-size:22px">&#8250;</span></div></div>';
  /* Ca lam viec: mo ca khai tien le, chot ca dem mu. Trang thai doc SAU
     khi man da ve (posCaVe) de khong bat khach cho mot vong API nua.

     MỌI ĐIỂM BÁN ĐỀU CÓ CA, kể cả điểm không có quầy. Anh Việt 01/09/2026:
     *"Bên chỗ màn Sales online em dựng luôn cái mở ca đóng ca đi để đếm
     tiền. Tiền mặt kênh này có tiền shipper thu về, khách vãng lai cũng có
     thể ghé mua chỗ sales online mua mang đi rồi trả tiền mặt."*

     Trước đó khối này chỉ vẽ cho điểm có quầy, vì máy chủ đọc doanh thu ca
     bằng ô quầy trên hoá đơn, mà hoá đơn Sales Online để trống ô đó, nên
     bảng đối soát sẽ báo toàn bộ doanh thu là tiền thừa. Nay máy chủ đọc
     theo ĐIỂM BÁN nên hàng rào này không còn lý do tồn tại. */
  html += '<div class="card" id="posCaKhoi" style="padding:11px 14px">' +
    '<div style="display:flex;align-items:center;gap:10px">' +
    '<span style="font-size:20px">🕐</span>' +
    '<div style="flex:1;min-width:0"><div style="font-weight:800;font-size:14px">Ca làm việc</div>' +
    '<div id="posCaTt" style="font-size:12.5px;color:#98a2b3">Đang xem ca của điểm bán...</div></div>' +
    /* flex:none BAT BUOC. Lop .btn mang width:100%, de nguyen trong mot hang
       flex thi nut nuot tron be ngang va cot chu ben trai bi bop con mot ky
       tu moi dong. Thay tan mat tren site that ngay 21/08/2026. */
    '<button class="btn gh" id="posCaNut" style="margin:0;padding:8px 14px;flex:none;width:auto;display:none"></button>' +
    '</div></div>';
  /* Man hinh phu quay ra phia khach. HTML nam trong 25-man-hinh-khach.js
     de phan nay chi co mot dong, do dung do cua phien khac. */
  html += cfdKhoi();
  html += '<div class="sec">Nguồn đơn</div><div class="card" style="padding:12px 14px">' +
    '<div id="posNd" style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px">' + posNutNguon(posDsCheDo(), posDon.che_do) + '</div>' +
    (laApp ? '<input class="tin" id="posMa" style="margin-top:10px" placeholder="' + h((qApp.nhan || 'Mã đơn bên app') + (qApp.vd ? ' - vd ' + qApp.vd : '')) + '" value="' + h(posDon.ma || '') + '">' : '') +
    '</div>';
  /* So ban: don ngoi tai quan thi waiter nhin so ban tren phieu ma bung
     mon cho dung khach (anh Viet 09/08/2026). Chon xong in len hoa don. */
  if (posDon.che_do === 'Tại chỗ') {
    var dsBan = [];
    for (var sb = 1; sb <= 20; sb++) dsBan.push(String(sb));
    html += '<div class="sec">Số bàn</div><div class="card" style="padding:10px 14px">' +
      '<div id="posBan" style="display:flex;flex-wrap:wrap;gap:8px">' +
      dsBan.map(function (b) {
        var on = posDon.so_ban === b;
        return posChipNut('data-ban="' + b + '"', 'Bàn ' + b, on);
      }).join('') +
      posChipNut('data-ban="Mang đi"', '🥡 Mang đi', posDon.so_ban === 'Mang đi') +
      (posDon.so_ban ? posChipNut('data-ban=""', '✕ Bỏ chọn', false, 1) : '') +
      '</div></div>';
  }
  html += '<div class="sec">Món trong hoá đơn</div><div class="card" style="padding:6px 14px">';
  if (!posDon.mon.length) html += '<div style="padding:14px 0;color:#a0a6b4">Chưa có món nào. Bấm Thêm món: tìm theo tên, mã hoặc quét mã vạch.</div>';
  /* Anh mon de nhin mat banh la biet dung mon chua; gia don vi nam ngay
     duoi ten, KHONG con duong bam sua gia (gia o quay khong duoc sua tay -
     anh Viet 09/08). Ba nut tru, cong, xoa cung mot kieu vuong 38px. */
  var NUT = 'height:38px;width:38px;flex:none;display:flex;align-items:center;justify-content:center;' +
    'border:1px solid #e5e7eb;background:#fff;border-radius:9px;font-size:19px;line-height:1;padding:0;cursor:pointer';
  posDon.mon.forEach(function (m, i) {
    html += '<div style="display:flex;align-items:center;gap:8px;padding:9px 0;border-bottom:1px solid #f0f2f6">' +
      (m.anh
        ? '<img src="' + h(m.anh) + '" loading="lazy" style="width:44px;height:44px;flex:none;object-fit:cover;border-radius:9px;border:1px solid #eef0f4" onerror="this.style.display=\'none\'">'
        : '<span style="width:44px;height:44px;flex:none;display:flex;align-items:center;justify-content:center;border-radius:9px;background:#f6f7f9;font-size:22px">🎂</span>') +
      '<div style="flex:1;min-width:0"><div data-tc-mo="' + i + '" style="font-size:14.5px;line-height:1.25;cursor:pointer">' + h(m.ten) + '</div>' +
      '<div style="color:#a0a6b4;font-size:12px;margin-top:1px">' + money(m.rate) + ' đ/cái</div>' +
      /* Tuy chon pha che la CHIP cho to ro (anh Viet 09/08): da chon thi
         chip xanh liet ke, chua chon mon nuoc thi chip nhac bam vao. */
      ((m.tc || []).length
        ? '<div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:5px">' +
          m.tc.map(function (x) {
            return '<span data-tc-mo="' + i + '" style="display:inline-block;background:#ccfbf1;color:#0f766e;border:1.5px solid #5eead4;border-radius:999px;padding:3px 11px;font-size:12.5px;font-weight:700;cursor:pointer">' + h(x) + '</span>';
          }).join('') +
          '<span data-tc-mo="' + i + '" style="display:inline-block;background:#fff;color:#6b7280;border:1.5px dashed #cbd5e1;border-radius:999px;padding:3px 10px;font-size:12.5px;cursor:pointer">✎ sửa</span></div>'
        : (m.nhom && ['Trà', 'Cà phê', 'Matcha', 'Cacao', 'Ice Cream - Kem'].indexOf(m.nhom) >= 0
          ? '<div style="margin-top:5px"><span data-tc-mo="' + i + '" style="display:inline-block;background:#ecfeff;color:#0b7c93;border:1.5px solid #7fe5f6;border-radius:999px;padding:4px 12px;font-size:12.5px;font-weight:700;cursor:pointer">🧊 Chọn đá / đường</span></div>'
          : '')) +
      /* Ghi chu RIENG cua tung mon (anh Viet 10/08/2026): o ghi chu chung
         ca hoa don khong du - bep khong biet loi dan la cho mon nao. */
      /* Moi ghi chu MOT chip rieng cho de nhin, khong don het vao mot
         chip dai (anh Viet 11/08/2026). */
      '<div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:5px">' +
      /* Chip TEN COMBO: mon ra tu combo nao thi mang chip cua combo do, de
         nguoi di lay mon biet gom du bo, va de cuoi ngay dem duoc ban bao
         nhieu bo combo (anh Viet 11/08/2026). */
      (m.combo
        ? '<span style="display:inline-block;background:#ede9fe;color:#5b21b6;border:1.5px solid #c4b5fd;border-radius:999px;padding:4px 12px;font-size:12.5px;font-weight:700">🧺 ' + h(m.combo) + '</span>'
        : '') +
      /* Chip MA DON cua san food app: dong bo tu ma don nhap ben tren, de
         in bill va in tem ra la biet mon nay cua don nao (anh Viet
         11/08/2026). Chip nay may tu dien, khong bam sua duoc. */
      (posMaAppHienTai()
        ? '<span style="display:inline-block;background:#111827;color:#fff;border-radius:999px;padding:4px 12px;font-size:12.5px;font-weight:700">🛵 ' + h(posMaAppHienTai()) + '</span>'
        : '') +
      (m.gc
        ? String(m.gc).split(',').map(function (x) { return x.trim(); }).filter(Boolean).map(function (x) {
          return '<span data-gc-mo="' + i + '" style="display:inline-block;background:#fef3c7;color:#92400e;border:1.5px solid #fcd34d;border-radius:999px;padding:4px 12px;font-size:12.5px;font-weight:700;cursor:pointer">📝 ' + h(x) + '</span>';
        }).join('') +
        '<span data-gc-mo="' + i + '" style="display:inline-block;background:#fff;color:#6b7280;border:1.5px dashed #cbd5e1;border-radius:999px;padding:4px 10px;font-size:12.5px;cursor:pointer">✎ sửa</span>'
        : '<span data-gc-mo="' + i + '" style="display:inline-block;background:#fff;color:#98a2b3;border:1.5px dashed #d7dce5;border-radius:999px;padding:4px 12px;font-size:12.5px;cursor:pointer">📝 Ghi chú món</span>') +
      '</div></div>' +
      '<button data-bot="' + i + '" style="' + NUT + '">&minus;</button>' +
      '<b style="min-width:22px;text-align:center;font-size:15px">' + money(m.qty) + '</b>' +
      '<button data-cong="' + i + '" style="' + NUT + '">+</button>' +
      '<b style="min-width:70px;text-align:right;font-size:15px">' + money(m.qty * m.rate) + '</b>' +
      '<button data-x="' + i + '" style="' + NUT + ';color:#b3261e;font-size:16px">✕</button></div>';
  });
  html += '<div style="padding:10px 0"><button class="btn gh" id="posThem" style="width:100%">➕ Thêm món</button></div></div>';
  html += '<div class="sec">Thanh toán</div><div class="card" style="padding:12px 14px;display:grid;gap:10px">' +
    (posDon.pt === 'Công nợ' && !laApp ? posKhoiKhachNo() : '') +
    /* BEN DE 01/09/2026: *"cac food app no khong co nut chon phuong thuc,
       khi luu hoa don no de la thanh toan chuyen khoan, cho tien ve"*.

       Truoc day nguon cua san chi hien MOT DONG CHU, khong co nut nao, nen
       khi o phuong thuc bi lech thi khong ai nhin ra va cung khong ai sua
       duoc tai cho. Nay van hien nut y het cac nguon khac. Nguon chi di mot
       phuong thuc thi ra dung mot nut, bam vao khong doi duoc gi - nhung
       cai thu ngan NHIN THAY chinh la cai se ghi so, do moi la diem quan
       trong. May chu van la noi chot (`_kiem_pt`), man hinh khong tu quyet. */
    '<div id="posPt" style="display:grid;grid-template-columns:1fr 1fr;gap:8px">' + posNutPt(dsPt, posDon.pt) + '</div>' +
    (laApp
      ? (dsPt.length > 1
          ? '<div style="font-size:12px;color:#6b7280">Đơn ' + h(posDon.che_do) + ' đi được ' + dsPt.length + ' phương thức, chọn đúng cách khách đã trả.</div>'
          : '<div style="font-size:12px;color:#6b7280">Đơn ' + h(posDon.che_do) + ' chỉ đi một phương thức này.</div>')
      : (posDon.pt === 'Chuyển khoản'
          ? posKhoiQr(posNoiDungCk(posDon.bill, '', posNguonThuc()), phaiThu, posNguonThuc())
          : '<div><div id="posMtcNhan" style="font-size:12px;color:#6b7280;margin-bottom:6px"></div>' +
            '<input class="tin" id="posMtc" placeholder="Mã tham chiếu" value="' + h(posDon.mtc || '') + '"></div>')) +
    posKhoiKm() +
    '<div><div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">' +
    '<span style="font-size:12.5px;color:#6b7280;font-weight:600">GIẢM GIÁ TAY THÊM (đ)</span></div>' +
    '<input class="tin" id="posGiam" placeholder="0" inputmode="numeric" value="' + (giamTay ? money(giamTay) : '') + '"></div>' +
    '<div><div style="font-size:12.5px;color:#6b7280;font-weight:600;margin-bottom:6px">PHÍ GIAO THU CỦA KHÁCH (đ)</div>' +
    '<input class="tin" id="posShip" placeholder="0" inputmode="numeric" value="' + (ship ? money(ship) : '') + '"></div>' +
    /* HÀNG TẶNG LÀ NGÕ CỤT NẾU KHÔNG NÓI TRƯỚC.

       Nút Hàng tặng vẫn hiện ở đây vì nó là một phương thức thanh toán
       thật, nhưng chỗ khai loại tặng và lý do lại nằm ở màn bill. Lưu xong
       mà không khai thì bill treo Chờ duyệt và không ghi sổ được, thu ngân
       không hiểu vì sao (anh Việt 01/09/2026).

       Nói trước ngay tại đây, và sau khi lưu thì đưa thẳng sang màn bill
       chứ không bắt tự mò. Không chép khối khai sang đây: đơn tặng phải
       qua giám đốc duyệt, để hai cửa khai là hai bản khai lệch nhau. */
    (posDon.pt === 'Hàng tặng'
      ? '<div style="padding:9px 11px;background:#fffbeb;border:1px solid #fde68a;' +
        'border-radius:9px;font-size:12.5px;color:#92400e;line-height:1.55">' +
        'Đơn <b>hàng tặng</b> cần khai loại tặng và lý do thì giám đốc mới duyệt ' +
        'được. Bấm Thu tiền xong máy đưa thẳng sang màn khai, khai luôn rồi mới ' +
        'ghi sổ được.</div>'
      : '') +
    (!laApp && posDon.pt === 'Tiền mặt'
      ? '<div><div style="font-size:12.5px;color:#6b7280;font-weight:600;margin-bottom:6px">KHÁCH ĐƯA (đ) - máy tính tiền thối</div>' +
        '<input class="tin" id="posDua" placeholder="0" inputmode="numeric" value="' + (dua ? money(dua) : '') + '"></div>'
      : '') +
    '</div>';
  html += '<div class="sec">Khách (không bắt buộc)</div><div class="card" style="padding:12px 14px;display:grid;gap:10px">' +
    /* O ten khach co GOI Y: go ten, ma, ma so thue hay so dien thoai la
       xo ra danh sach de bam chon (anh Viet 11/08/2026). Chon xong may
       dien luon so dien thoai va gan ho so khach vao hoa don, nho vay
       chuong trinh khuyen mai theo hang khach moi ap duoc. */
    '<div style="position:relative">' +
    (posDon.khach_ma
      ? '<div style="display:flex;align-items:center;gap:8px;background:#f0fdfa;border:1.5px solid #7fe5f6;border-radius:10px;padding:9px 11px;margin-bottom:8px">' +
        '<span style="font-size:17px">👤</span>' +
        '<div style="flex:1;min-width:0"><b style="font-size:14px">' + h(posDon.ten || posDon.khach_ma) + '</b>' +
        '<div style="font-size:11.5px;color:#0b7c93">mã ' + h(posDon.khach_ma) + (posDon.khach_hang ? ' · hạng ' + h(posDon.khach_hang) : '') + '</div></div>' +
        '<button id="posBoKhach" style="border:0;background:transparent;color:#b3261e;font-size:17px;cursor:pointer">✕</button></div>'
      : '') +
    '<input class="tin" id="posTen" placeholder="Tên khách, mã khách, MST hoặc số điện thoại" autocomplete="off" value="' + h(posDon.ten || '') + '">' +
    '<div id="posTenGoi"></div></div>' +
    /* Ba ô này trước đây dính sát nhau không có một khoảng nào, ngón tay to
       là bấm nhầm ô. Đặt khoảng ngay tại đây chứ KHÔNG sửa .tin toàn hệ:
       lớp .tin đang dùng ở 109 chỗ khắp các màn, đổi nó là đổi cả những màn
       không ai yêu cầu và không ai kiểm lại. */
    '<input class="tin" id="posSdt" placeholder="Số điện thoại" inputmode="tel" style="margin-top:12px" value="' + h(posDon.sdt || '') + '">' +
    '<input class="tin" id="posGhiChu" placeholder="Ghi chú bill: gói quà, để lạnh, giao lầu 2..." style="margin-top:12px" value="' + h(posDon.ghi_chu || '') + '">' +
    '</div>';
  /* Hang, so diem hien co, so diem se tich, va o tru tien bang diem.
     Toan bo khoi nay dung o 13-khuyen-mai.js (anh Viet 19/08/2026). */
  html += posVeThe();
  /* Khach can hoa don cong ty thi dien ngay tai quay - nhap MST la may tu
     tra ten va dia chi (giong man Doanh thu Sales). Khong dien o day thi
     khach van quet duoc QR cuoi bill giay de tu dien sau. */
  var xin2 = 'width:100%;box-sizing:border-box;padding:10px 11px;border:1.5px solid #e5e7eb;border-radius:9px;font-size:14px;font-family:inherit';
  html += '<div class="card" style="padding:12px 14px;margin-top:10px">' +
    '<div id="posXhMo" style="display:flex;align-items:center;gap:8px;cursor:pointer"><span style="font-size:17px">🧾</span>' +
    '<div style="flex:1"><b style="font-size:14px">Khách cần hoá đơn công ty?</b><div style="font-size:12px;color:#98a2b3">Không điền cũng được - khách quét QR cuối hoá đơn tự điền sau</div></div>' +
    '<span style="color:#c3c8d4;font-size:18px">' + (posDon.xhd_mo ? '▾' : '▸') + '</span></div>' +
    (posDon.xhd_mo
      ? '<div style="display:grid;gap:8px;margin-top:10px">' +
        '<input id="posXhMst" placeholder="Mã số thuế: 10 số công ty, 12 số hộ kinh doanh, chi nhánh gõ cả dấu gạch" value="' + h(posDon.xh.mst) + '" style="' + xin2 + '">' +
        '<input id="posXhTen" placeholder="Tên pháp nhân trên hoá đơn" value="' + h(posDon.xh.ten) + '" style="' + xin2 + '">' +
        '<textarea id="posXhDc" rows="2" placeholder="Địa chỉ trên hoá đơn" style="' + xin2 + '">' + h(posDon.xh.dc) + '</textarea>' +
        '<input id="posXhEmail" placeholder="Email nhận hoá đơn" value="' + h(posDon.xh.email) + '" style="' + xin2 + '">' +
        '<div id="posXhBao" style="font-size:12px;color:#6b7280"></div></div>'
      : '') +
    '</div>';
  html += '<div class="card" style="padding:12px 14px;display:grid;gap:6px;margin-top:10px">' +
    '<div style="display:flex;justify-content:space-between;color:#5a6070"><span>Tạm tính</span><span>' + money(tong) + ' đ</span></div>' +
    (((posDon.kmKq && posDon.kmKq.ap) || []).map(function (a) {
      return '<div style="display:flex;justify-content:space-between;color:#0f766e"><span>' + h(a.ten) + '</span><span>&minus;' + money(a.giam) + ' đ</span></div>';
    }).join('')) +
    (giamTay ? '<div style="display:flex;justify-content:space-between;color:#b45309"><span>Giảm giá tay</span><span>&minus;' + money(giamTay) + ' đ</span></div>' : '') +
    (giamDiem ? '<div style="display:flex;justify-content:space-between;color:#0369a1"><span>Trừ ' + money(posDon.diemVe.so_diem) + ' điểm thành viên</span><span>&minus;' + money(giamDiem) + ' đ</span></div>' : '') +
    (ship ? '<div style="display:flex;justify-content:space-between;color:#5a6070"><span>Phí giao</span><span>+' + money(ship) + ' đ</span></div>' : '') +
    '<div style="display:flex;justify-content:space-between;font-size:19px"><b>PHẢI THU</b><b>' + money(phaiThu) + ' đ</b></div>' +
    (!laApp && posDon.pt === 'Tiền mặt' && dua ? '<div style="display:flex;justify-content:space-between;color:' + (dua >= phaiThu ? '#0f766e' : '#b3261e') + '"><span>Khách đưa ' + money(dua) + ' đ</span><b>' + (dua >= phaiThu ? 'Thối ' + money(dua - phaiThu) : 'Còn thiếu ' + money(phaiThu - dua)) + ' đ</b></div>' : '') +
    '</div>';
  /* In bill tam tinh (y Felix): khach dat qua sale hoac ban thanh toan
     chung cuoi buoi - in phieu giu mon kem QR, cashier chot sau. Don app
     thi khong co khai niem tam tinh. */
  var footer = (laApp ? '' : '<button class="btn gh" id="posTam" style="flex:0 0 34%;margin:0">🖨 Tạm tính</button>') +
    /* Don food app: khach da tra tien cho app roi, app dang giu, quay
       khong thu dong nao ca. Dung chu "Thu tien" o day la de nhan vien
       hieu nham va de khach dung tai quay hieu nham (Felix 19/08/2026). */
    '<button class="btn" id="posLuu" style="flex:1;margin:0">' +
    (laApp ? '🧾 Lưu hoá đơn ' : '💰 Thu tiền ') + money(phaiThu) + ' đ</button>';
  var b = frame('Tính tiền · ' + (posQuay.ma || ''), html, { footer: '<div style="display:flex;gap:8px">' + footer + '</div>' });
  if (!laApp && posDon.pt !== 'Chuyển khoản') veOMtc(posDon.pt, 'posMtc', 'posMtcNhan');
  posDemHomNay();
  posCaVe();
  cfdGan();
  /* Noi cac nut cua khoi diem. Truyen ham ve lai man de moi nhanh khoi
     phai tu goi go(scrPosQuay, true) - de quen mot cho la man hinh dung im
     sau khi bam. */
  posGanTruDiem(function () { posDoc(); go(scrPosQuay, true); });
  b.addEventListener('click', function (e) {
    if (e.target.closest('[data-t="posDoiQuay"]')) { posDoc(); posQuay = null; posHomNayTxt = null; return go(scrPosChonQuay, true); }
    if (e.target.closest('[data-t="posDsBill"]')) { posDoc(); posDsNgay = null; return go(scrPosDs); }
    var t;
    t = e.target.closest('[data-nd]');
    if (t) { posDoc(); posDon.che_do = t.getAttribute('data-nd'); return go(scrPosQuay, true); }
    t = e.target.closest('[data-cong]');
    if (t) { posDoc(); posDon.mon[+t.getAttribute('data-cong')].qty += 1; return go(scrPosQuay, true); }
    t = e.target.closest('[data-bot]');
    if (t) {
      posDoc();
      var i = +t.getAttribute('data-bot');
      posDon.mon[i].qty -= 1;
      if (posDon.mon[i].qty <= 0) posDon.mon.splice(i, 1);
      return go(scrPosQuay, true);
    }
    t = e.target.closest('[data-x]');
    if (t) { posDoc(); posDon.mon.splice(+t.getAttribute('data-x'), 1); return go(scrPosQuay, true); }
    t = e.target.closest('[data-ban]');
    if (t) { posDoc(); posDon.so_ban = t.getAttribute('data-ban') || ''; return go(scrPosQuay, true); }
    t = e.target.closest('[data-tc-mo]');
    if (t) { posDoc(); return posMoTuyChon(+t.getAttribute('data-tc-mo')); }
    t = e.target.closest('[data-gc-mo]');
    if (t) { posDoc(); return posMoGhiChuMon(+t.getAttribute('data-gc-mo')); }
  });
  var nDo = document.querySelector('[data-dotien]');
  if (nDo) nDo.onclick = function () { posDoc(); posSheetDoTien(phaiThu, ''); };
  var ptw = document.getElementById('posPt');
  if (ptw) ptw.querySelectorAll('.ptc').forEach(function (c) {
    c.onclick = function () { posDoc(); posDon.pt = c.getAttribute('data-pt'); go(scrPosQuay, true); };
  });
  ['posGiam', 'posDua'].forEach(function (id) {
    var o = document.getElementById(id);
    if (o) o.onblur = function () { posDoc(); go(scrPosQuay, true); };
  });
  document.getElementById('posThem').onclick = posThemMon;
  document.getElementById('posLuu').onclick = posLuuDon;
  var nTam = document.getElementById('posTam');
  if (nTam) nTam.onclick = posInTamTinh;
  var nCn = document.getElementById('posChonKhachNo');
  if (nCn) nCn.onclick = posSheetKhachNo;
  var nCnBo = document.getElementById('posBoKhachNo');
  if (nCnBo) nCnBo.onclick = function () { posDoc(); posDon.khach_no = null; go(scrPosQuay, true); };
  posNoiKm();
  posNoiTimKhach();
  /* Go xong ma don san food app thi ve lai man de chip ma don hien ngay
     tren tung mon (anh Viet 11/08/2026). */
  var nMa = document.getElementById('posMa');
  if (nMa) nMa.onchange = function () { posDoc(); go(scrPosQuay, true); };
  var xhMo = document.getElementById('posXhMo');
  if (xhMo) xhMo.onclick = function () { posDoc(); posDon.xhd_mo = !posDon.xhd_mo; go(scrPosQuay, true); };
  var xhMst = document.getElementById('posXhMst');
  if (xhMst) xhMst.onblur = async function () {
    var so = (xhMst.value || '').replace(/[^0-9]/g, '');
    var bao = document.getElementById('posXhBao');
    /* 12 so la so dinh danh ca nhan cua chu ho kinh doanh, hop le tu
       01/07/2025 theo dieu 5 Thong tu 86/2024/TT-BTC. */
    if (so.length !== 10 && so.length !== 12 && so.length !== 13) {
      if (bao) bao.textContent = so ? 'Mã số thuế phải 10 số (công ty), 12 số (hộ kinh doanh) hoặc 13 số (chi nhánh).' : '';
      return;
    }
    if (bao) bao.textContent = 'Đang tra mã số thuế...';
    try {
      var kq = await api('vagabond.api.tra_mst', { mst: so });
      var t = document.getElementById('posXhTen'), dc = document.getElementById('posXhDc');
      if (kq && kq.ok) {
        if (t && !t.value.trim()) t.value = kq.ten || '';
        if (dc && !dc.value.trim()) dc.value = kq.dia_chi || '';
        /* Cổng tra cứu trả về tên chỉ có loại hình pháp lý. Đã xảy ra thật
           ngày 22/08/2026, tờ hoá đơn 10901 mang tên "CÔNG TY CỔ PHẦN". */
        if (kq.nghi_thieu) {
          if (bao) { bao.textContent = '⚠️ ' + (kq.canh_bao || 'Hệ thống nghi ngờ tên công ty bị thiếu. Vui lòng kiểm tra lại thông tin!'); bao.style.color = '#b45309'; bao.style.fontWeight = '700'; }
          if (t) { t.style.borderColor = '#f59e0b'; t.focus(); }
          toast('Tên công ty tra về bị thiếu, vui lòng kiểm tra lại!', 6000);
        } else {
          if (t) t.style.borderColor = '';
          if (bao) { bao.textContent = 'Tra được: ' + (kq.ten || ''); bao.style.color = ''; bao.style.fontWeight = ''; }
        }
      } else if (bao) bao.textContent = 'Không tra được mã này, vui lòng điền tay.';
    } catch (e) { if (bao) bao.textContent = 'Không tra được mã này, vui lòng điền tay.'; }
  };
  ['posGhiChu'].forEach(function (id) {
    var o = document.getElementById(id);
    if (o) o.onblur = function () { posDoc(); };
  });
  /* Chuyen khoan dang cho tien: poll SePay de bao ngay khi tien ve. */
  if (!laApp && posDon.pt === 'Chuyển khoản' && phaiThu > 0 && posSepayNhan < phaiThu - 1) posPollBat(posDon.bill, phaiThu);
  /* Man hinh khach bam theo man nay: moi lan ve lai la mot lan day. */
  /* LY DO GIAM GIA, tinh O DAY chu khong ben man hinh khach.

     Anh Viet 01/09/2026 chon: man hinh khach KHONG bay ten, so dien thoai,
     hang the hay so diem cua khach, vi no quay thang ra hang nguoi dang xep
     hang. Thay vao do chi noi cho khach biet phan giam nay den TU DAU.

     Vi sao tinh o day: tep 25-man-hinh-khach.js bi ca kiem soi tung chu,
     no khong duoc phep nhac den mot o rieng tu nao cua don. Nen ben nay doc
     cac o do roi chi chuyen sang mot NHAN NGAN, khong chuyen du lieu goc.
     Nhan cung khong duoc mang ten hang the: noi "thanh vien" thi khong ai
     doan duoc khach nay hang gi. */
  cfdDay(posDon, posQuay, phaiThu, nguonThuc, laApp, posLyDoGiam());
}
async function posDemHomNay() {
  if (!posQuay) return;
  try {
    var kq = await api('vagabond.ban_hang.pos_ds_bill', { quay: posQuay.ma || '' });
    /* Bill da huy khong phai tien: dong nay la cho thu ngan nhin nhieu nhat
       trong ngay, lech voi Chot ca la sinh chuyen cai nhau luc giao ca. */
    var ds = ((kq && kq.bill) || []).filter(function (r) { return !r.vgb_huy; });
    var tong = 0, tam = 0, chua = 0, xong = 0;
    ds.forEach(function (r) {
      tong += r.grand_total || 0;
      if (r.docstatus === 1) xong++;
      else if (r.vgb_tam_tinh) tam++;
      else chua++;
    });
    posHomNayTxt = 'Hôm nay ' + ds.length + ' hoá đơn · ' + money(tong) + ' đ · ' +
      (tam ? '🕐 ' + tam + ' tạm tính · ' : '') +
      (chua ? '📄 ' + chua + ' chưa ghi sổ · ' : '') +
      '✅ ' + xong + ' đã ghi sổ.';
  } catch (e) { posHomNayTxt = ''; }
  var o = document.getElementById('posHomNay');
  if (o) o.textContent = posHomNayTxt;
}
async function posThemMon() {
  posDoc();
  if (!dsItemsCache) {
    busy(true);
    try {
      dsItemsCache = await getList('Item', { filters: { is_sales_item: 1, disabled: 0, item_group: ['not in', ['Nguyên vật liệu Thô', 'Bán thành phẩm Bánh', 'Bán thành phẩm Nước', 'Nhân bán thành phẩm', 'Công cụ Dụng cụ', 'Bao bì', 'Văn phòng phẩm', 'Tài sản Cố định']] }, fields: ['name', 'item_name', 'image', 'standard_rate', 'item_group'], limit_page_length: 0, order_by: 'item_name' });
      try {
        var bc = await getList('Item Barcode', { parent: 'Item', fields: ['parent', 'barcode'], limit_page_length: 0 });
        var bcm = {};
        (bc || []).forEach(function (r) { bcm[r.parent] = (bcm[r.parent] ? bcm[r.parent] + ' ' : '') + r.barcode; });
        dsItemsCache.forEach(function (x) { x.ma_vach = bcm[x.name] || ''; });
      } catch (e2) { /* khong doc duoc barcode thi van tim theo ma */ }
    } catch (e) { busy(false); return toast('Không tải được danh mục món'); }
    busy(false);
  }
  /* Combo nam ngay trong bang chon mon, nhom "Combo" xep dau tien (anh
     Viet 11/08/2026). Bam mot combo la may RA no thanh cac mon thanh phan
     do vao gio, moi mon mang chip ten combo de nguoi di lay mon biet no
     thuoc combo nao. */
  var dsCombo = [];
  try {
    var kqCb = await api('vagabond.khuyen_mai.ds_combo', { quay: (posQuay && posQuay.ma) || '', nguon: posNguonThuc() });
    dsCombo = ((kqCb && kqCb.combo) || []).filter(function (x) { return x.dung_duoc; });
  } catch (e3) { dsCombo = []; }
  var oCombo = dsCombo.map(function (c) {
    return {
      value: '@CB@' + c.name, label: '🧺 ' + c.ten, icon: '🧺', img: c.anh || '',
      gia: c.gia_combo, nhom: NHOM_COMBO, combo: c,
      phu: comboMoTa(c) + ' · ' + money(c.gia_combo) + ' đ, tiết kiệm ' + (c.co_nhom ? 'từ ' : '') + money(c.tiet_kiem) + ' đ',
      tim: c.name + ' combo'
    };
  });
  posSheetMon(oCombo.concat(dsItemsCache.map(function (x) {
    return { value: x.name, label: x.item_name, icon: '🎂', img: x.image || '', gia: x.standard_rate || 0, nhom: x.item_group || '', phu: (x.standard_rate ? money(x.standard_rate) + ' đ' : 'chưa có giá') + ' · ' + x.name, tim: x.name + ' ' + (x.ma_vach || '') };
  })), function (o) {
    if (o.combo) { return posBamCombo(o.combo); }
    var i = -1;
    posDon.mon.forEach(function (m, k) { if (m.item_code === o.value && !m.combo) i = k; });
    if (i >= 0) { posDon.mon[i].qty += 1; return posDon.mon[i].qty; }
    /* Gia o quay khong duoc sua tay: mon chua co gia ban thi bao Sales dat
       gia trong danh muc, chu khong go tay tai quay (anh Viet 09/08). */
    if (!o.gia) { toast('Món ' + o.label + ' chưa có giá bán trong danh mục. Nhờ Sales đặt giá rồi bấm lại.', 4500); return 0; }
    posDon.mon.push({ item_code: o.value, ten: o.label, qty: 1, rate: o.gia, anh: o.img || '', nhom: o.nhom, tc: [], gc: '' });
    return 1;
  }, function () { go(scrPosQuay, true); }, function (ma) {
    var q = 0;
    if (String(ma).indexOf('@CB@') === 0) {
      var mc = String(ma).slice(4);
      (posDon.combo || []).forEach(function (c) { if (c.ma === mc) q = c.so_bo; });
      return q;
    }
    posDon.mon.forEach(function (m) { if (m.item_code === ma) q += m.qty; });
    return q;
  });
}

var NHOM_COMBO = 'Combo';

/* Mot dong chu ta noi dung combo: mon co san cong voi cac nhom cho chon. */
function comboMoTa(c) {
  var ph = (c.bat_buoc || c.dong || []).map(function (d) { return num(d.so_luong) + '× ' + h(d.ten_mon || d.item_code); });
  (c.nhom_ds || []).forEach(function (g) {
    var tt = parseInt(g.toi_thieu, 10); if (isNaN(tt)) tt = g.chon || 1;
    var td = parseInt(g.toi_da, 10); if (isNaN(td) || td < 1) td = g.chon || 1;
    ph.push((tt === td ? 'chọn ' + td : 'chọn ' + tt + ' đến ' + td) + ' trong ' + (g.mon || []).length + ' ' + h(g.ten));
  });
  return ph.join(' + ');
}

/* Them mot bo combo vao gio: ra thanh tung mon thanh phan, moi mon mang
   ten combo de bep va nguoi di lay mon biet mon do thuoc combo nao, va de
   cuoi ngay dem duoc ban bao nhieu bo (anh Viet 11/08/2026). */
function posThemCombo(c, chon) {
  chon = chon || [];
  /* Mon vao bill = mon bat buoc + mon khach vua chon trong tung nhom.
     Combo cu khong co nhom nao thi bat_buoc chinh la ca danh sach dong. */
  var dong = (c.bat_buoc || c.dong || []).slice();
  chon.forEach(function (x) {
    (c.nhom_ds || []).forEach(function (g) {
      if (g.ten !== x.nhom) return;
      (g.mon || []).forEach(function (m) { if (m.item_code === x.item_code) dong.push(m); });
    });
  });
  dong.forEach(function (d) {
    var i = -1;
    posDon.mon.forEach(function (m, k) {
      if (m.item_code === d.item_code && m.combo === c.ten) i = k;
    });
    if (i >= 0) posDon.mon[i].qty += flt0(d.so_luong);
    else posDon.mon.push({
      item_code: d.item_code, ten: d.ten_mon || d.item_code,
      qty: flt0(d.so_luong), rate: flt0(d.gia_goc),
      anh: '', nhom: '', tc: [], gc: '', combo: c.ten, combo_ma: c.name
    });
  });
  posDon.combo = posDon.combo || [];
  /* Cung mot combo ma khach chon hai bo mon khac nhau thi phai la HAI dong
     rieng: gop chung lai la may chu khong biet bo thu hai gom nhung mon gi,
     tinh sai tien giam. */
  var khoa = comboKhoa(c.name, chon);
  var cu = null;
  posDon.combo.forEach(function (x) { if (comboKhoa(x.ma, x.chon) === khoa) cu = x; });
  if (cu) cu.so_bo += 1;
  else posDon.combo.push({ ma: c.name, so_bo: 1, ten: c.ten, chon: chon });
  posDon.kmKq = null;
  toast('Đã thêm combo ' + c.ten);
}

/* Bam combo o bang chon mon: co nhom thi hoi truoc, khong co thi do luon. */
function posBamCombo(c) {
  if (c.co_nhom) {
    posSheetChonCombo(c, function (chon) {
      posThemCombo(c, chon);
      /* Bang chon mon van dang mo o duoi, dong no lai roi hay ve man tinh
         tien - khong thi thu ngan bam OK xong van thay bang chon mon. */
      Array.prototype.forEach.call(document.querySelectorAll('.sh'), function (o) { o.remove(); });
      go(scrPosQuay, true);
    });
    return 0;
  }
  posThemCombo(c);
  return 1;
}

/* Hang chip LOC dung chung cho ba man danh sach hoa don (anh Viet
   10/08/2026). Moi chip kem so dem; chip khong co hoa don nao thi an di
   cho do roi mat, rieng chip "Tat ca" luon hien. */
/* Nhom trang thai hoa don dien tu, dung chung cho ca ba man danh sach hoa
   don: Doanh thu Sales, hoa don quay D1 va quay NVHTN (anh Viet 12/08/2026).
   Ke toan can loc nhanh "don nao chua ky", "don nao bi thay the" ma khong
   phai mo tung don ra xem. */
var HD_NHOM = {
  cho_ky: ['Chờ ký', 'Chờ duyệt', 'Đang ký'],
  da_ky: ['Đã ký', 'Đã gửi CQT', 'CQT chấp nhận'],
  loi: ['CQT báo lỗi', 'Lỗi'],
  huy: ['Đã hủy', 'Đã huỷ'],
  thay_the: ['HĐ thay thế', 'Bị thay thế'],
  dieu_chinh: ['HĐ điều chỉnh', 'Bị điều chỉnh']
};
function hdThuoc(r, nhom) {
  var tt = (r.custom_hddt_trang_thai || '').trim();
  return tt ? (HD_NHOM[nhom] || []).indexOf(tt) >= 0 : false;
}
function locHddt() {
  return [
    { k: '', nhan: 'Mọi trạng thái HĐ', loc: function () { return true; } },
    { k: 'chua', nhan: '📌 Chưa xuất HĐĐT', loc: function (r) { return r.docstatus === 1 && !r.custom_hddt_so && !(r.custom_hddt_trang_thai || '').trim(); } },
    { k: 'cho_ky', nhan: '✍️ Chờ ký', loc: function (r) { return hdThuoc(r, 'cho_ky'); } },
    { k: 'da_ky', nhan: '✅ Đã ký', loc: function (r) { return hdThuoc(r, 'da_ky'); } },
    { k: 'thay_the', nhan: '🔁 Thay thế', loc: function (r) { return hdThuoc(r, 'thay_the'); } },
    { k: 'dieu_chinh', nhan: '✏️ Điều chỉnh', loc: function (r) { return hdThuoc(r, 'dieu_chinh'); } },
    { k: 'huy', nhan: '🚫 Đã huỷ', loc: function (r) { return hdThuoc(r, 'huy'); } },
    { k: 'loi', nhan: '⚠ Cơ quan thuế báo lỗi', loc: function (r) { return hdThuoc(r, 'loi'); } }
  ];
}

/* Loc cai gi thi phai biet loc ra BAO NHIEU TIEN. Cuoi ngay bam chip
   GrabFood la de doi soat voi Grab: khong co dong tong thi phai lay may
   tinh cong tay tung dong tren man (anh Viet 12/08/2026).

   Tinh tren TOAN BO tap da loc, khong tinh tren phan dang hien: man nao
   cat bot dong de ve nhanh thi con so o day van la con so that. */
function locKhoiTong(rows, nhan) {
  var so = 0, tien = 0, chot = 0, tienChot = 0, nhap = 0, tienNhap = 0, huy = 0, tienHuy = 0;
  (rows || []).forEach(function (r) {
    var v = Number(r.grand_total || 0);
    if (r.vgb_huy) { huy++; tienHuy += v; return; }
    so++; tien += v;
    if (r.docstatus === 1) { chot++; tienChot += v; }
    else { nhap++; tienNhap += v; }
  });
  var dong = function (chu, n, t, mau) {
    return '<div style="display:flex;justify-content:space-between;font-size:12.5px;color:' + (mau || '#6b7280') + ';margin-top:3px">' +
      '<span>' + chu + ' ' + n + ' đơn</span><b>' + money(t) + ' đ</b></div>';
  };
  return '<div class="card" style="padding:12px 14px;background:#f0fdfa;border:1.5px solid #99f6e4">' +
    '<div style="font-size:11.5px;color:#0f766e;font-weight:800;letter-spacing:.3px">TỔNG THEO BỘ LỌC' +
    (nhan ? ' · ' + h(nhan) : '') + '</div>' +
    '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:5px">' +
    '<span style="font-size:13.5px;color:#374151">' + so + ' hoá đơn</span>' +
    '<b style="font-size:20px;color:#0f766e">' + money(tien) + ' đ</b></div>' +
    (chot && nhap ? dong('Đã ghi sổ', chot, tienChot) + dong('Chưa ghi sổ', nhap, tienNhap) : '') +
    (huy ? dong('Đã huỷ, không tính vào tổng', huy, tienHuy, '#991b1b') : '') +
    '</div>';
}

function locHang(ds, dangChon, attr, rows) {
  var ra = ds.map(function (c) {
    var n = rows.filter(c.loc).length;
    if (!n && c.k !== '') return '';
    var on = c.k === dangChon;
    return '<button ' + attr + '="' + h(c.k) + '" style="flex:0 0 auto;border:1.5px solid ' +
      (on ? '#0d9488' : '#d7dce5') + ';background:' + (on ? '#0d9488' : '#fff') +
      ';color:' + (on ? '#fff' : '#374151') + ';border-radius:999px;padding:7px 13px;font-size:12.5px;' +
      'font-weight:' + (on ? '800' : '600') + ';cursor:pointer;white-space:nowrap;font-family:inherit">' +
      c.nhan + ' <span style="opacity:.75">' + n + '</span></button>';
  }).join('');
  return '<div style="flex:0 0 auto;display:flex;gap:7px;padding:2px 0;overflow-x:auto;-webkit-overflow-scrolling:touch">' + ra + '</div>';
}

/* Chip nguon don + phuong thuc thanh toan sinh theo du lieu that cua ngay,
   khong bay ra chip rong. */
function locNguonPt(rows) {
  var ds = [{ k: '', nhan: 'Mọi nguồn', loc: function () { return true; } }];
  var ng = [], pt = [];
  rows.forEach(function (r) {
    var a = r.custom_nguon || '';
    if (a && ng.indexOf(a) < 0) ng.push(a);
    var b = r.vgb_pt_thanh_toan || '';
    if (b && pt.indexOf(b) < 0) pt.push(b);
  });
  ng.sort(function (a, b) { return a.localeCompare(b, 'vi'); });
  pt.sort(function (a, b) { return a.localeCompare(b, 'vi'); });
  ng.forEach(function (a) {
    ds.push({ k: 'ng:' + a, nhan: h(a), loc: function (r) { return (r.custom_nguon || '') === a; } });
  });
  pt.forEach(function (b) {
    /* Don san co phuong thuc trung ten nguon (GrabFood tra qua GrabFood):
       bay hai chip giong het nhau chi lam roi mat, bo bot mot. */
    if (ng.indexOf(b) >= 0) return;
    ds.push({ k: 'pt:' + b, nhan: 'Trả: ' + h(b), loc: function (r) { return (r.vgb_pt_thanh_toan || '') === b; } });
  });
  return ds;
}
function locTim(ds, k) {
  for (var i = 0; i < ds.length; i++) if (ds[i].k === k) return ds[i];
  return ds[0];
}

/* Chip chung cho moi nut chon nhanh cua app (anh Viet 09/08/2026: nut
   bam thi lam dang CHIP cho de nhin, de phan biet). */
/* Mot con chip loc.

   `mau` la mau cua trang thai DANG CHON, mac dinh xanh mong két. Them
   31/08/2026 vi anh Viet bao man Danh sach phieu hoan tien co ba hang chip
   xep chong nhau ma hang nao cung xanh y het nhau, nhin khong biet minh
   dang o hang nao. Moi HO chip mot mau thi liec mot cai la ro. */
function posChipNut(attr, chu, dangChon, laXoa, mau) {
  var m = mau || '#0d9488';
  var vien = dangChon ? m : (laXoa ? '#fecaca' : '#d7dce5');
  var nen = dangChon ? m : '#fff';
  var chuMau = dangChon ? '#fff' : (laXoa ? '#b3261e' : '#374151');
  return '<button ' + attr + ' style="border:1.5px solid ' + vien + ';background:' + nen +
    ';color:' + chuMau + ';border-radius:999px;padding:9px 15px;font-size:14px;font-weight:' +
    (dangChon ? '800' : '600') + ';cursor:pointer;white-space:nowrap;line-height:1.2">' + chu + '</button>';
}

/* Sheet chon mon rieng cho quay: co hang chip NHOM MON nhu cot trai Fabi
   (anh Viet 09/08/2026) - bam nhom la loc, do phai go tim tung mon. */
var posNhomChon = '';
/* Thu tu nhom mon o hang chip: xep theo tan suat ban that tai quay chu
   khong theo bang chu cai (anh Viet 10/08/2026). Danh sach thu tu do
   backend giu, nhom la de cuoi. */
function posXepNhom(nhoms) {
  var uu = ((CFGBH || {}).thu_tu_nhom) || [];
  return nhoms.slice().sort(function (a, b) {
    /* Combo luon dau hang chip: cashier bam vao la thay ngay, khong phai
       cuon di tim (anh Viet 11/08/2026). */
    if (a === NHOM_COMBO) return -1;
    if (b === NHOM_COMBO) return 1;
    var ia = uu.indexOf(a), ib = uu.indexOf(b);
    if (ia < 0) ia = 9999;
    if (ib < 0) ib = 9999;
    if (ia !== ib) return ia - ib;
    return a.localeCompare(b, 'vi');
  });
}
function posSheetMon(items, onPick, onDong, demSo) {
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  var nhoms = [];
  items.forEach(function (it) { if (it.nhom && nhoms.indexOf(it.nhom) < 0) nhoms.push(it.nhom); });
  nhoms = posXepNhom(nhoms);
  var hd = '<div class="shh"><b>Chọn món</b><div class="x">&times;</div></div>' +
    '<div style="flex:0 0 auto;padding:10px 14px 4px;display:flex;gap:8px"><input class="nt" placeholder="Tìm nhanh..." style="height:46px;padding:0 12px;flex:1"><button class="nt" id="shQuet" title="Quét mã vạch" style="height:46px;width:54px;flex:none;font-size:20px;cursor:pointer">&#128247;</button></div>' +
    /* flex:0 0 auto: .shb la flex column nen hang chip tung bi danh sach mon
       dai nen bep con 12px, mat chu (loi anh Viet bao 09/08). */
    '<div id="shNhom" style="flex:0 0 auto;min-height:40px;display:flex;gap:6px;padding:8px 14px 6px;overflow-x:auto;-webkit-overflow-scrolling:touch"></div>';
  /* Thanh duoi: dem so mon da chon va nut Xong. Truoc day bam mot mon la
     sheet dong luon, muon them mon thu hai phai mo lai tu dau - Dễ bao
     10/08/2026. Nay bam bao nhieu mon cung duoc, xong moi dong. */
  box.innerHTML = hd + '<div class="shl"></div>' +
    '<div id="shDay" style="flex:0 0 auto;display:flex;align-items:center;gap:10px;' +
    'padding:10px 14px calc(env(safe-area-inset-bottom,0px) + 10px);border-top:1px solid #eef0f4;background:#fff">' +
    '<div id="shDem" style="flex:1;min-width:0;font-size:13px;color:#6b7280"></div>' +
    '<button id="shXong" style="flex:none;border:0;background:#0d9488;color:#fff;border-radius:999px;' +
    'padding:11px 22px;font-size:15px;font-weight:800;cursor:pointer;font-family:inherit">Xong</button></div>';
  var lst = box.querySelector('.shl'), oNhom = box.querySelector('#shNhom');
  var soLanChon = 0;
  function veDem() {
    var o = box.querySelector('#shDem');
    if (!o) return;
    o.innerHTML = soLanChon
      ? '<b style="color:#0f766e">Đã thêm ' + soLanChon + ' lượt món</b> · bấm tiếp để thêm nữa'
      : 'Bấm liên tiếp để thêm nhiều món, xong thì bấm Xong';
  }
  function veNhom() {
    var ds = ['Tất cả'].concat(nhoms);
    oNhom.innerHTML = ds.map(function (n) {
      var v = n === 'Tất cả' ? '' : n;
      var on = v === posNhomChon;
      return '<button data-nh="' + h(v) + '" style="flex:0 0 auto;padding:7px 13px;border-radius:18px;font-size:13px;white-space:nowrap;cursor:pointer;border:1.5px solid ' + (on ? '#0d9488;background:#0d9488;color:#fff;font-weight:700' : '#e5e7eb;background:#fff;color:#374151') + '">' + h(n) + '</button>';
    }).join('');
  }
  function draw(q) {
    q = (q || '').toLowerCase();
    var f = items.filter(function (it) {
      if (posNhomChon && it.nhom !== posNhomChon) return false;
      return !q || ((it.label || '') + ' ' + (it.tim || '') + ' ' + (it.value || '')).toLowerCase().indexOf(q) >= 0;
    });
    lst.innerHTML = f.length ? f.map(function (it) {
      var dc = demSo ? (demSo(it.value) || 0) : 0;
      return '<div class="shi" data-i="' + items.indexOf(it) + '"' + (dc ? ' style="background:#f0fdfa"' : '') + '>' +
        (it.img ? '<img src="' + it.img + '" style="width:36px;height:36px;object-fit:cover;border-radius:8px;flex:none;border:1px solid #e5e7eb" loading="lazy">' : '<span>' + (it.icon || '🎂') + '</span>') +
        '<span style="flex:1;min-width:0">' + h(it.label) + (it.phu ? '<div style="color:#a0a6b4;font-size:12px;margin-top:2px">' + h(it.phu) + '</div>' : '') + '</span>' +
        (dc ? '<b style="flex:none;background:#0d9488;color:#fff;border-radius:999px;min-width:26px;height:26px;' +
          'display:flex;align-items:center;justify-content:center;font-size:13px;padding:0 8px">' + money(dc) + '</b>' : '') +
        '</div>';
    }).join('') : '<div class="emp"><div class="e2">Không tìm thấy trong nhóm này</div></div>';
  }
  veNhom(); draw(''); 
  ov.appendChild(box); document.body.appendChild(ov);
  var inp = box.querySelector('input');
  inp.oninput = function () { draw(inp.value); };
  oNhom.onclick = function (e) {
    var t = e.target.closest('[data-nh]'); if (!t) return;
    posNhomChon = t.getAttribute('data-nh');
    veNhom(); draw(inp.value);
  };
  var shQ = box.querySelector('#shQuet');
  if (shQ) shQ.onclick = async function () {
    var code = null;
    try { code = await scanBarcode(); } catch (e) { code = null; }
    if (code) { inp.value = code; draw(code); }
  };
  function close() { ov.remove(); if (onDong) onDong(); }
  ov.onclick = function (e) { if (e.target === ov) close(); };
  box.querySelector('.x').onclick = close;
  box.querySelector('#shXong').onclick = close;
  lst.onclick = function (e) {
    var r = e.target.closest('.shi'); if (!r) return;
    var kq = onPick(items[+r.dataset.i]);
    /* Ham chon tra ve so luong moi cua mon do (0 = khong them duoc, vi du
       mon chua co gia). Sheet van mo, chi ve lai dong cho thay so. */
    if (kq) {
      soLanChon += 1;
      r.style.background = '#ccfbf1';
      setTimeout(function () { draw(inp.value); }, 130);
    }
    veDem();
  };
  veDem();
}

/* Ban cho khach cong no thi PHAI biet la no cua ai, khong thi cuoi
   thang khong doi duoc (anh Viet 11/08/2026). Chon khach xong, thong tin
   xuat hoa don da luu cua khach do tu dien luon xuong duoi. */
function posKhoiKhachNo() {
  var k = posDon.khach_no;
  if (k) {
    return '<div style="border:1.5px solid #fcd34d;background:#fffbeb;border-radius:10px;padding:11px 12px">' +
      '<div style="display:flex;align-items:center;gap:8px">' +
      '<span style="font-size:18px">📒</span>' +
      '<div style="flex:1;min-width:0"><b style="font-size:14.5px">' + h(k.ten) + '</b>' +
      '<div style="font-size:12px;color:#92400e">Ghi nợ cho khách này · mã ' + h(k.ma) + (k.mst ? ' · MST ' + h(k.mst) : '') + '</div></div>' +
      '<button id="posBoKhachNo" style="border:0;background:transparent;color:#b3261e;font-size:18px;cursor:pointer">✕</button></div></div>';
  }
  return '<button id="posChonKhachNo" class="btn gh" style="margin:0;border-color:#fcd34d;color:#92400e">📒 Chọn khách công nợ (bắt buộc)</button>';
}

/* Sheet tim khach hang: go ten hay ma deu ra, giong bang tim mon. */
/* Sheet chon khach dung chung cho ca man tinh tien quay va man Chi tiet
   don ben Doanh thu Sales. Go la hoi thang MAY CHU chu khong loc tren
   danh sach da tai ve - danh muc hang nghin khach, loc tai cho thi go
   "Oshima" khong bao gio ra (anh Viet 12/08/2026). */
async function sheetTimKhach(tieuDe, onChon) {
  busy(true);
  var kq;
  try { kq = await api('vagabond.cong_no.tim_khach', { tu_khoa: '' }); }
  catch (e) { busy(false); return toast((e && e.message) || 'Không tải được danh sách khách'); }
  busy(false);
  var ds = (kq && kq.khach) || [];
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>' + h(tieuDe) + '</b><div class="x">&times;</div></div>' +
    '<div style="flex:0 0 auto;padding:10px 14px 4px"><input class="nt" id="tkTim" placeholder="Gõ tên, mã khách, MST hoặc số điện thoại..." style="height:46px;padding:0 12px;width:100%;box-sizing:border-box"></div>' +
    '<div class="shl"></div>';
  var lst = box.querySelector('.shl');
  function ve() {
    lst.innerHTML = ds.length ? ds.map(function (x) {
      return '<div class="shi" data-kh="' + h(x.name) + '"><span>🏢</span>' +
        '<span style="flex:1;min-width:0">' + h(x.customer_name || x.name) +
        '<div style="color:#a0a6b4;font-size:12px;margin-top:2px">' + h(x.name) +
        (x.tax_id ? ' · MST ' + h(x.tax_id) : '') +
        (x.mobile_no ? ' · ' + h(x.mobile_no) : '') +
        (x.customer_group ? ' · ' + h(x.customer_group) : '') + '</div></span></div>';
    }).join('') : '<div class="emp"><div class="e2">Không tìm thấy khách nào. Kế toán tạo khách bên Next trước nhé.</div></div>';
  }
  ve();
  ov.appendChild(box); document.body.appendChild(ov);
  var inp = box.querySelector('#tkTim');
  var tre = null;
  inp.oninput = function () {
    if (tre) clearTimeout(tre);
    tre = setTimeout(async function () {
      try {
        var k2 = await api('vagabond.cong_no.tim_khach', { tu_khoa: inp.value });
        ds = (k2 && k2.khach) || [];
        ve();
      } catch (e) { }
    }, 260);
  };
  function dong() { ov.remove(); }
  ov.onclick = function (e) { if (e.target === ov) dong(); };
  box.querySelector('.x').onclick = dong;
  lst.onclick = function (e) {
    var r = e.target.closest('[data-kh]'); if (!r) return;
    var ma = r.getAttribute('data-kh');
    var x = ds.filter(function (y) { return y.name === ma; })[0] || {};
    dong();
    onChon(x.name ? x : { name: ma, customer_name: ma });
  };
  setTimeout(function () { try { inp.focus(); } catch (e) { } }, 120);
}

async function posSheetKhachNo() {
  busy(true);
  var kq;
  try { kq = await api('vagabond.cong_no.tim_khach', { tu_khoa: '' }); }
  catch (e) { busy(false); return toast((e && e.message) || 'Không tải được danh sách khách'); }
  busy(false);
  var ds = (kq && kq.khach) || [];
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>Chọn khách công nợ</b><div class="x">&times;</div></div>' +
    '<div style="flex:0 0 auto;padding:10px 14px 4px"><input class="nt" id="cnTim" placeholder="Gõ tên hoặc mã khách..." style="height:46px;padding:0 12px;width:100%;box-sizing:border-box"></div>' +
    '<div class="shl"></div>';
  var lst = box.querySelector('.shl');
  function ve(q) {
    q = (q || '').toLowerCase();
    var f = ds.filter(function (x) {
      return !q || ((x.customer_name || '') + ' ' + (x.name || '') + ' ' + (x.tax_id || '')).toLowerCase().indexOf(q) >= 0;
    });
    lst.innerHTML = f.length ? f.map(function (x) {
      return '<div class="shi" data-kh="' + h(x.name) + '"><span>🏢</span>' +
        '<span style="flex:1;min-width:0">' + h(x.customer_name || x.name) +
        '<div style="color:#a0a6b4;font-size:12px;margin-top:2px">' + h(x.name) +
        (x.tax_id ? ' · MST ' + h(x.tax_id) : '') + (x.customer_group ? ' · ' + h(x.customer_group) : '') + '</div></span></div>';
    }).join('') : '<div class="emp"><div class="e2">Không tìm thấy khách nào. Kế toán tạo khách bên Next trước nhé.</div></div>';
  }
  ve('');
  ov.appendChild(box); document.body.appendChild(ov);
  var inp = box.querySelector('#cnTim');
  /* Danh sach khach hang dai (hang tram khach si va khach cong ty) nen
     lan dau chi lay 60 cai dau. Go tim thi phai hoi lai MAY CHU chu khong
     duoc loc tren 60 cai da tai ve - go "ravie" ma khong ra vi Ravie
     khong nam trong 60 khach dau bang chu cai (bat duoc 11/08/2026). */
  var tre = null;
  inp.oninput = function () {
    var q = inp.value;
    ve(q);
    if (tre) clearTimeout(tre);
    tre = setTimeout(async function () {
      try {
        var k2 = await api('vagabond.cong_no.tim_khach', { tu_khoa: q });
        ds = (k2 && k2.khach) || [];
        ve(inp.value);
      } catch (e) { }
    }, 280);
  };
  function dong() { ov.remove(); }
  ov.onclick = function (e) { if (e.target === ov) dong(); };
  box.querySelector('.x').onclick = dong;
  lst.onclick = async function (e) {
    var r = e.target.closest('[data-kh]'); if (!r) return;
    var ma = r.getAttribute('data-kh');
    var x = ds.filter(function (y) { return y.name === ma; })[0] || {};
    dong();
    posDoc();
    posDon.khach_no = { ma: ma, ten: x.customer_name || ma, mst: x.tax_id || '' };
    if (!posDon.ten) posDon.ten = x.customer_name || '';
    if (!posDon.sdt) posDon.sdt = x.mobile_no || '';
    /* Khach si nao da luu thong tin xuat hoa don thi dien san luon, thu
       ngan khoi go lai tung chu. */
    try {
      var tt = await api('vagabond.cong_no.thong_tin_xhd', { khach: ma });
      if (tt && (tt.mst || tt.ten)) {
        posDon.xhd_mo = true;
        posDon.xh = {
          mst: tt.mst || '', ten: tt.ten || '',
          dc: tt.dia_chi || '', email: tt.email || ''
        };
        toast('Đã điền sẵn thông tin xuất hoá đơn của ' + (tt.ten || ma));
      }
    } catch (e2) { }
    go(scrPosQuay, true);
  };
}

/* Ghi chu cho MOT mon: bep va quay pha che doc tren phieu lam mon va
   tem dan, nen phai go duoc loi dan rieng tung mon chu khong dung chung
   mot o ghi chu ca hoa don (anh Viet 10/08/2026). */
var POS_GC_NHANH = [
  'Không đá', 'Ít đá', 'Đá riêng', 'Ít ngọt', 'Không đường',
  'Nóng', 'Mang đi', 'Gói riêng', 'Để lạnh', 'Không hộp',
  'Cắt sẵn', 'Không nến', 'Viết lời chúc'
];
function posMoGhiChuMon(i) {
  var m = posDon.mon[i];
  if (!m) return;
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>Ghi chú · ' + h(m.ten) + '</b><div class="x">&times;</div></div>' +
    '<div style="padding:6px 14px calc(env(safe-area-inset-bottom,0px) + 14px)">' +
    '<div style="font-size:12px;color:#98a2b3;margin-bottom:8px">Ghi chú này in lên phiếu làm món và tem dán món, chỉ áp cho món này.</div>' +
    '<textarea id="gcO" rows="2" placeholder="Ví dụ: ít ngọt, gói riêng, viết chữ Happy Birthday..." style="width:100%;box-sizing:border-box;padding:11px 12px;border:1.5px solid #d7dce5;border-radius:10px;font-size:15px;font-family:inherit">' + h(m.gc || '') + '</textarea>' +
    '<div style="display:flex;flex-wrap:wrap;gap:7px;margin-top:10px">' +
    POS_GC_NHANH.map(function (x) {
      return '<button data-gcn="' + h(x) + '" style="border:1.5px solid #d7dce5;background:#fff;color:#374151;border-radius:999px;padding:8px 13px;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit">' + h(x) + '</button>';
    }).join('') + '</div>' +
    '<button class="btn" id="gcXong" style="margin-top:16px">Xong</button>' +
    (m.gc ? '<button class="btn gh" id="gcXoa" style="margin-top:8px;color:#b3261e">Xoá ghi chú món này</button>' : '') +
    '</div>';
  ov.appendChild(box); document.body.appendChild(ov);
  var o = box.querySelector('#gcO');
  function dong(luu) {
    if (luu) m.gc = (o.value || '').trim().slice(0, 200);
    ov.remove();
    go(scrPosQuay, true);
  }
  ov.onclick = function (e) { if (e.target === ov) dong(1); };
  box.querySelector('.x').onclick = function () { dong(1); };
  box.querySelector('#gcXong').onclick = function () { dong(1); };
  var nx = box.querySelector('#gcXoa');
  if (nx) nx.onclick = function () { o.value = ''; dong(1); };
  box.addEventListener('click', function (e) {
    var t = e.target.closest('[data-gcn]'); if (!t) return;
    var v = t.getAttribute('data-gcn');
    var cu = (o.value || '').trim();
    o.value = cu ? (cu.indexOf(v) >= 0 ? cu : cu + ', ' + v) : v;
  });
  setTimeout(function () { try { o.focus(); } catch (e) { } }, 60);
}

/* Ma don cua san food app, de mapping vao ghi chu tung mon va in dam len
   tem: shipper GrabFood den doc dung ma la nhan dung tui (anh Viet
   10/08/2026). Don tai cho / mang ve thi khong co ma nay. */
function posMaAppHienTai() {
  if (!posDon) return '';
  var laApp = posDon.che_do !== 'Tại chỗ' && posDon.che_do !== 'Mang về';
  if (!laApp) return '';
  var ma = (posDon.ma || '').trim();
  return ma ? (posDon.che_do + ' ' + ma) : '';
}
function posGcGui(m, maApp) {
  var v = [];
  if (maApp) v.push(maApp);
  if (m.gc) v.push(m.gc);
  return v.join(' · ');
}

/* Tuy chon pha che kieu customization Fabi: it duong, it da, da rieng...
   Khong chon gi = mac dinh 100% duong 100% da, khong ghi gi len bill.
   Cac lua chon deu 0 dong - chi la loi dan cho quay pha che. */
var POS_TC = null;
async function posMoTuyChon(i) {
  var m = posDon.mon[i];
  if (!m) return;
  if (POS_TC === null) {
    try { var kq = await api('vagabond.ban_hang.pos_ds_tuy_chon', {}); POS_TC = (kq && kq.tc) || []; }
    catch (e) { POS_TC = []; }
  }
  var ds = POS_TC.filter(function (n) { return !n.nhom_mon.length || n.nhom_mon.indexOf(m.nhom || '') >= 0; });
  if (!ds.length) return;
  m.tc = m.tc || [];
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  var html = '<div class="shh"><b>' + h(m.ten) + '</b><div class="x">&times;</div></div>' +
    '<div style="padding:4px 14px calc(env(safe-area-inset-bottom,0px) + 14px)">' +
    '<div style="font-size:12px;color:#98a2b3;margin-bottom:6px">Không chọn gì = 100% đường, 100% đá như bình thường.</div>';
  ds.forEach(function (n) {
    html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:10px 0 6px;text-transform:uppercase">' + h(n.nhom) + '</div>' +
      '<div style="display:flex;gap:7px;flex-wrap:wrap">' +
      n.lua_chon.map(function (lc) {
        var on = m.tc.indexOf(lc) >= 0;
        return '<button data-tc="' + h(lc) + '" style="padding:9px 13px;border-radius:10px;font-size:14px;cursor:pointer;border:1.5px solid ' + (on ? '#0d9488;background:#ccfbf1;color:#0f766e;font-weight:700' : '#e5e7eb;background:#fff;color:#374151') + '">' + h(lc) + '</button>';
      }).join('') + '</div>';
  });
  html += '<button class="btn" id="tcXong" style="margin-top:16px">Xong</button></div>';
  box.innerHTML = html;
  ov.appendChild(box); document.body.appendChild(ov);
  function dong() { ov.remove(); go(scrPosQuay, true); }
  ov.onclick = function (e) { if (e.target === ov) dong(); };
  box.querySelector('.x').onclick = dong;
  box.querySelector('#tcXong').onclick = dong;
  box.addEventListener('click', function (e) {
    var t = e.target.closest('[data-tc]'); if (!t) return;
    var lc = t.getAttribute('data-tc');
    var k = m.tc.indexOf(lc);
    if (k >= 0) m.tc.splice(k, 1); else m.tc.push(lc);
    var on = m.tc.indexOf(lc) >= 0;
    t.style.border = '1.5px solid ' + (on ? '#0d9488' : '#e5e7eb');
    t.style.background = on ? '#ccfbf1' : '#fff';
    t.style.color = on ? '#0f766e' : '#374151';
    t.style.fontWeight = on ? '700' : 'normal';
  });
}
/* Ma QR dong kieu bill Fabi: khach quet bang app ngan hang la so tien va
   noi dung chuyen khoan dien san, khoi go tay, khoi go nham (anh Viet
   09/08/2026). Dung anh VietQR nen may nao co mang la hien duoc. */
/* Noi dung chuyen khoan mang MA DIEM BAN o dau: "TCV VGBAB123".

   Ke toan nhin sao ke ngan hang la biet ngay giao dich thuoc diem nao ma
   khong phai mo tung don ra tra. Ma bill van nam nguyen trong chuoi nen bo
   do SePay khong he doi: no tim VGBxxxxx BEN TRONG noi dung chu khong so
   ca cum.

   Day chi la lop mem - khach sua duoc noi dung, app ngan hang co loai cat
   bot ky tu. Lop cung la moi diem mot tai khoan nhan rieng; luc nao mo
   duoc tai khoan ao rieng thi khai o man Diem ban. */
/* Noi dung chuyen khoan in trong ma QR.

   Nguon da co tai khoan ao rieng thi chi ghi ma bill: sao ke ngan hang da
   tach san theo tai khoan roi, gan them ma diem ban vao nua vua thua vua
   xau (anh Viet 12/08/2026).

   Nguon CHUA khai tai khoan ao thi van giu ma diem ban o dau, khong thi
   tien ba noi do chung mot tai khoan ma noi dung khong con dau vet nao de
   ke toan lan ra. Khai du tai khoan ao la moi noi tu dong gon lai. */
function posNoiDungCk(maBill, maDiem, nguon) {
  var b = String(maBill || '').trim();
  var d = posDiemCua(maDiem);
  var tk = posTaiKhoan(nguon, d);
  if (tk && tk.rieng) return b;
  /* Tu 31/08/2026 chinh MA BILL da mang tien to cua diem (TCVQ4PFX), nen
     dan them ma diem o dau nua la thua va con lam noi dung dai ra. Chi bill
     cu mang tien to chung VGB moi con can ma diem di kem. */
  if (b && posMaCoTienTo(b)) return b;
  return d ? (d + ' ' + b) : b;
}
/* Ma bill nay da tu mang tien to cua mot diem ban chua. */
function posMaCoTienTo(ma) {
  var b = (CFGBH || {}).ma_tien_to || {};
  var m = String(ma || '').trim().toUpperCase();
  for (var k in b) { if (b.hasOwnProperty(k) && m.indexOf(b[k]) === 0) return true; }
  return false;
}

/* Ma diem ban dang lam viec. Man tinh tien quay thi tu biet, cac man khac
   phai truyen vao (hoa don co vgb_quay, man Nhap don tay co o chon). */
function posDiemCua(maDiem) {
  var d = String(maDiem || '').trim();
  if (d) return d.toUpperCase();
  if (typeof posQuay !== 'undefined' && posQuay && posQuay.ma) return String(posQuay.ma).toUpperCase();
  return '';
}

/* Tai khoan nhan tien cua mot don. Anh Viet da xin duoc MB Bank cap tai
   khoan ao rieng cho tung diem ban de ke toan doc sao ke la biet ngay tien
   cua noi nao.

   Tu 12/08/2026 hai quay dung chung nguon "Tại chỗ" va "Mang về" nen ten
   nguon khong con noi duoc don cua diem nao: phai tra khoa co ma diem
   truoc ("TCV|Tại chỗ"), roi moi den khoa chi co nguon, roi tai khoan cua
   rieng diem do, cuoi cung la tai khoan mac dinh. */
function posTaiKhoan(nguon, maDiem) {
  var c = CFGBH || {};
  var n = String(nguon || '').trim();
  var d = posDiemCua(maDiem);
  var b = c.qr_nguon || {};
  var thu = [];
  if (n && d) thu.push(d + '|' + n);
  if (n) thu.push(n);
  if (d) thu.push(d + '|');
  for (var i = 0; i < thu.length; i++) {
    var t = b[thu[i]];
    if (t && t.stk && t.rieng) return t;
  }
  for (var j = 0; j < thu.length; j++) {
    var u = b[thu[j]];
    if (u && u.stk) return u;
  }
  return c.qr_quay || {};
}
function posQrUrl(noiDung, tien, nguon, maDiem) {
  var q = posTaiKhoan(nguon, maDiem);
  if (!q.stk) return '';
  return 'https://img.vietqr.io/image/' + (q.bank || 'MB') + '-' + q.stk + '-qr_only.png' +
    '?amount=' + Math.round(tien || 0) +
    '&addInfo=' + encodeURIComponent(noiDung || '') +
    '&accountName=' + encodeURIComponent(q.ten || '');
}
function posKhoiQr(noiDung, tien, nguon, maDiem) {
  var q = posTaiKhoan(nguon, maDiem);
  var url = posQrUrl(noiDung, tien, nguon, maDiem);
  if (!url) return '<div style="font-size:13px;color:#b3261e">Chưa khai số tài khoản nhận chuyển khoản nên chưa sinh được mã QR.</div>';
  if (!tien) return '<div style="font-size:13px;color:#6b7280">Thêm món vào hoá đơn rồi mã QR chuyển khoản sẽ hiện ra đây.</div>';
  /* Tien ve du la khoi nay tu doi mau xanh - poll SePay 5 giay mot lan. */
  if (posSepayNhan >= tien - 1) {
    return '<div style="border:2px solid #16a34a;border-radius:12px;padding:16px;text-align:center;background:#f0fdf4">' +
      '<div style="font-size:34px">✅</div>' +
      '<div style="font-size:18px;font-weight:800;color:#15803d">ĐÃ NHẬN ĐỦ ' + money(posSepayNhan) + ' đ</div>' +
      '<div style="font-size:13px;color:#374151;margin-top:4px">SePay khớp nội dung <b>' + h(noiDung) + '</b>. Bấm nút cuối màn để lưu hoá đơn rồi ghi sổ.</div>' +
      '</div>';
  }
  return '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:12px;text-align:center;background:#fff">' +
    '<div style="font-size:12.5px;color:#6b7280">Khách quét mã này, máy tự điền số tiền và nội dung</div>' +
    '<img src="' + url + '" alt="Mã QR chuyển khoản" style="width:min(240px,62vw);aspect-ratio:1;margin:10px auto 6px;display:block;border-radius:10px;background:#fff">' +
    '<div style="font-size:18px;font-weight:800;color:#0f766e">' + money(tien) + ' đ</div>' +
    '<div style="font-size:13px;color:#374151;margin-top:2px">Nội dung: <b>' + h(noiDung) + '</b></div>' +
    '<div style="font-size:12px;color:#98a2b3;margin-top:2px">' + h(q.ten || '') + ' · ' + h((q.bank || '') + ' ' + (q.stk || '')) + '</div>' +
    '<div id="posChoTien" style="font-size:12px;color:#b45309;margin-top:8px">' +
    (posSepayGoiY
      ? '💡 Có ' + posSepayGoiY + ' khoản đúng ' + money(tien) + ' đ vừa về mà chưa hoá đơn nào nhận. Bấm nút bên dưới để xem.'
      : '⏳ Đang chờ tiền về... màn hình tự báo khi ngân hàng nhận đủ.') + '</div>' +
    /* NUT DO TAY, anh Viet 01/09/2026: may de xuat, nguoi quyet dinh. */
    '<button class="btn gh" data-dotien style="width:100%;margin:10px 0 0">🔎 Dò tiền chuyển khoản</button>' +
    '</div>';
}
/* ---------------- Do tien chuyen khoan tay (anh Viet 01/09/2026) ----------

   *"Em cho them giup anh nut 'Do tien chuyen khoan' o man bam bill de thu
    ngan co the nhan roi do thu cong."*

   Ban thay cho phep tu doan theo khung gio da bo. Khac nhau o dung mot
   chuyen: MAY DE XUAT, NGUOI QUYET DINH.

   May liet ke moi khoan tien DUNG BANG so phai thu trong ngay ma chua hoa
   don nao nhan. Khong loc theo gio: nguoi dang dung day biet ro khach vua
   tra luc nao, chinh xac hon moi khung gio may tu dat.

   `siName` rong nghia la bill CHUA LUU: luc do chi xem cho biet tien da ve
   chua, khong gan duoc vao dau. Luu bill xong bam lai o man danh sach thi
   moi gan. */
async function posSheetDoTien(tien, siName, sauKhiGan) {
  busy(true);
  var kq;
  try {
    kq = await api('vagabond.ban_hang.pos_do_tien', {
      tien: tien || 0, name: siName || '', quay: (posQuay && posQuay.ma) || ''
    });
  }
  catch (e) { busy(false); return toast((e && e.message) || 'Không đọc được sao kê.'); }
  busy(false);
  var gd = (kq && kq.gd) || [];
  var ov = document.createElement('div'); ov.className = 'sh';

  var dong = function (g, i) {
    var vien = g.khop ? '#0d9488' : (g.cua_bill ? '#e5e7eb' : '#cbd5e1');
    var nen = g.khop ? '#f0fdfa' : '#fff';
    var mo = g.cua_bill ? 'opacity:.62;' : '';
    return '<div data-gan="' + i + '" style="' + mo + 'display:flex;align-items:center;gap:10px;padding:11px 12px;' +
      'border:1.5px solid ' + vien + ';border-radius:10px;margin-bottom:8px;background:' + nen + ';text-align:left">' +
      '<div style="flex:1;min-width:0">' +
      '<div style="font-size:15px;font-weight:800;color:' + (g.khop ? '#0f766e' : '#374151') + '">' +
      money(g.tien) + ' đ<span style="font-weight:600;color:#6b7280"> · ' + h(g.gio || '') + '</span>' +
      (g.khop ? '<span style="margin-left:8px;font-size:11.5px;background:#ccfbf1;color:#0f766e;border-radius:999px;padding:2px 8px">đúng số tiền</span>' : '') +
      '</div>' +
      '<div style="font-size:11.5px;color:#98a2b3;margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' +
      (g.cua_bill ? '⛔ Đã gắn cho ' + h(g.cua_bill) : h(g.mo_ta || '')) + '</div></div>' +
      (siName && !g.cua_bill ? '<span style="flex:none;font-size:12.5px;font-weight:700;color:#0d9488">Chọn &#8250;</span>' : '') +
      '</div>';
  };

  var than = '';
  if (!gd.length) {
    than = '<div style="padding:20px 4px;text-align:center;color:#6b7280;font-size:13.5px;line-height:1.7">' +
      'Hôm nay chưa có khoản chuyển khoản nào về tài khoản của điểm bán này.<br>' +
      'Khách vừa chuyển thì chờ vài giây rồi dò lại.</div>';
  } else {
    than = gd.map(dong).join('');
  }

  /* Noi ro dang soi tai khoan nao. Diem chua khai tai khoan rieng thi danh
     sach nay la sao ke CHUNG cua ca ba diem, phai bao ra chu khong de nguoi
     ta tuong day la tien cua riêng quay minh. */
  var dauMuc = kq && kq.tk_rieng
    ? 'Tiền về tài khoản <b>' + h(kq.tk_stk || '') + '</b> của điểm này, hôm nay.'
    : '<span style="color:#b45309">⚠ Điểm này chưa khai tài khoản riêng nên đây là sao kê chung của cả ba điểm. Vào Cài đặt · Tài khoản nhận tiền để khai.</span>';

  ov.innerHTML = '<div class="shb" style="padding:18px 16px calc(env(safe-area-inset-bottom,0px) + 16px);text-align:center">' +
    '<div style="font-size:19px;font-weight:800">Dò tiền chuyển khoản</div>' +
    '<div style="font-size:12.5px;color:#6b7280;margin:2px 0 4px">Cần thu ' + money(tien) + ' đ' +
    (kq && kq.so_khop ? ' · máy thấy ' + kq.so_khop + ' khoản đúng số tiền' : '') + '</div>' +
    '<div style="font-size:12px;color:#6b7280;margin-bottom:12px;line-height:1.6">' + dauMuc + '</div>' +
    '<div style="max-height:52vh;overflow:auto;text-align:left">' + than + '</div>' +
    (siName
      ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:8px;line-height:1.6;text-align:left">Đối chiếu giờ với điện thoại khách rồi chọn đúng khoản. Máy ghi số tham chiếu ngân hàng vào hoá đơn, không tự chọn hộ.</div>'
      : '<div style="font-size:11.5px;color:#98a2b3;margin-top:8px;line-height:1.6;text-align:left">Hoá đơn chưa lưu nên chỉ xem cho biết tiền đã về chưa. Lưu xong vào danh sách hoá đơn bấm dò lại thì mới gắn được.</div>') +
    '<button class="btn gh" data-dong style="width:100%;margin:12px 0 0">Đóng</button></div>';
  document.body.appendChild(ov);

  ov.onclick = async function (e) {
    if (e.target === ov || e.target.hasAttribute('data-dong')) return ov.remove();
    var t = e.target.closest('[data-gan]');
    if (!t || !siName) return;
    var g = gd[+t.getAttribute('data-gan')];
    if (!g) return;
    if (g.cua_bill) return toast('Khoản này đã gắn cho hoá đơn ' + g.cua_bill + '.', 4000);
    var lech = Math.round(g.tien - (tien || 0));
    var dong_y = await confirmSheet(
      'Gắn khoản này vào hoá đơn?',
      money(g.tien) + ' đ về lúc ' + (g.gio || '') + '.\nHoá đơn ' + siName + ', cần thu ' + money(tien || 0) + ' đ.' +
      (Math.abs(lech) > 1 ? '\n\n⚠ LỆCH ' + money(Math.abs(lech)) + ' đ ' + (lech > 0 ? 'THỪA' : 'THIẾU') + '. Máy vẫn gắn và ghi rõ số lệch vào ghi chú đối soát.' : '') +
      '\n\nMáy ghi số tham chiếu ngân hàng vào hoá đơn.',
      'Gắn vào hoá đơn', Math.abs(lech) > 1);
    if (!dong_y) return;
    busy(true);
    try {
      await api('vagabond.ban_hang.pos_gan_tien', { name: siName, gd: g.ten });
      busy(false); ov.remove();
      toast('Đã gắn khoản ' + money(g.tien) + ' đ vào ' + siName + '.');
      if (sauKhiGan) sauKhiGan();
    } catch (err) { busy(false); toast((err && err.message) || 'Không gắn được.'); }
  };
}

function posQrSheet(soPhieu, tien, siName, nguon, maDiem) {
  var q = posTaiKhoan(nguon, maDiem);
  var url = posQrUrl(soPhieu, tien, nguon, maDiem);
  var ov = document.createElement('div'); ov.className = 'sh';
  ov.innerHTML = '<div class="shb" style="padding:20px 16px calc(env(safe-area-inset-bottom,0px) + 16px);text-align:center">' +
    '<div style="font-size:21px;font-weight:800">Chuyển khoản ' + money(tien) + ' đ</div>' +
    '<div style="font-size:12.5px;color:#6b7280;margin-top:2px">' + h(q.ten || '') + ' · ' + h((q.bank || '') + ' ' + (q.stk || '')) + '</div>' +
    '<img src="' + url + '" alt="VietQR" style="width:min(300px,72vw);aspect-ratio:1;margin:12px auto 4px;display:block;border:1px solid #e5e7eb;border-radius:14px;background:#fff">' +
    '<div style="font-size:13px;color:#374151">Nội dung chuyển khoản: <b>' + h(soPhieu) + '</b></div>' +
    '<div id="qrsBao" style="font-size:12.5px;color:#b45309;margin-top:8px">⏳ Đang chờ tiền về... màn hình tự báo khi SePay nhận đủ.</div>' +
    '<div style="display:flex;gap:8px;margin-top:14px">' +
    (posBillVua ? '<button class="btn gh" data-in style="flex:0 0 34%;margin:0">🖨 In hoá đơn</button>' : '') +
    '<button class="btn" data-y style="flex:1;margin:0">Hoá đơn mới</button></div>' +
    (posBillVua ? posNutIn(posBillVua) : '') +
    '</div>';
  document.body.appendChild(ov);
  /* Tien ve la doi ngay thanh nut ghi so - cashier chot bill tai cho. */
  var pid = setInterval(async function () {
    if (!document.body.contains(ov)) return clearInterval(pid);
    try {
      var kq = await api('vagabond.ban_hang.pos_kiem_sepay', { noi_dung: soPhieu, tien: tien });
      if (kq && kq.du) {
        clearInterval(pid);
        var bao = ov.querySelector('#qrsBao');
        if (bao) { bao.style.color = '#15803d'; bao.innerHTML = '✅ <b>ĐÃ NHẬN ĐỦ ' + money(kq.nhan) + ' đ</b> - SePay khớp nội dung ' + h(soPhieu) + '.'; }
        var ny = ov.querySelector('[data-y]');
        if (ny && siName) { ny.textContent = '📒 Ghi sổ luôn - Hoá đơn mới'; ny.setAttribute('data-gs', '1'); }
      }
    } catch (e) { }
  }, 5000);
  ov.onclick = async function (e) {
    /* In bill / ghi so xong la ve DANH SACH BILL de quan ly thay chip
       trang thai ca (anh Viet 09/08); Bill moi thi ve man bam bill. */
    if (e.target.hasAttribute('data-in')) {
      if (posBillVua) posInBill(posBillVua);
      clearInterval(pid); ov.remove(); posHomNayTxt = null; go(scrPosDs, true);
      return;
    }
    if (e.target.hasAttribute('data-pm')) { if (posBillVua) posInPhieuMon(posBillVua); return; }
    if (e.target.hasAttribute('data-tem')) { if (posBillVua) posInTemLy(posBillVua); return; }
    if (!e.target.hasAttribute('data-y')) return;
    var ghiSo = !!(e.target.hasAttribute('data-gs') && siName);
    if (ghiSo) {
      busy(true);
      try { await api('vagabond.ban_hang.pos_ghi_so', { name: siName }); busy(false); toast('Đã ghi sổ ' + siName); }
      catch (er) { busy(false); toast((er && er.message) || 'Ghi sổ lỗi', 4000); }
    }
    clearInterval(pid); ov.remove(); posHomNayTxt = null; go(ghiSo ? scrPosDs : scrPosQuay, true);
  };
}
var posDangLuu = false;
async function posLuuDon() {
  /* Bam hai lan lien la ra hai bill cung so tien - khoa lai cho chac. */
  if (posDangLuu) return;
  posDoc();
  if (!posDon.mon.length) return toast('Hoá đơn chưa có món nào.');
  var thieuGia = posDon.mon.filter(function (m) { return !m.rate; });
  if (thieuGia.length) return toast('Món ' + thieuGia[0].ten + ' chưa có giá, bấm vào tên món để nhập.');
  var laApp = posDon.che_do !== 'Tại chỗ' && posDon.che_do !== 'Mang về';
  var nguon = posNguonThuc();
  var giamTay = posSoTien(posDon.giam), dua = posSoTien(posDon.dua);
  var tong = posDon.mon.reduce(function (t, m) { return t + m.qty * m.rate; }, 0);
  /* Tinh lai khuyen mai ngay truoc khi chot: gio hang co the vua doi ma
     man hinh chua kip ve lai. */
  await posTinhKm();
  var giamKm = (posDon.kmKq && posDon.kmKq.tong_giam) || 0;
  var giam = giamTay + giamKm;
  var giamDiem = (posDon.diemVe && posDon.diemVe.so_tien) || 0;
  var ship = posSoTien(posDon.ship);
  var phaiThu = Math.max(0, tong - giam - giamDiem) + ship;
  if (laApp && !(posDon.ma || '').trim()) return toast('Đơn ' + posDon.che_do + ' phải nhập mã đơn bên app để đối soát.');
  if (!laApp) {
    /* Cong no ma khong biet no cua ai thi cuoi thang khong doi duoc. */
    if (posDon.pt === 'Công nợ' && !(posDon.khach_no && posDon.khach_no.ma)) {
      return toast('Bán công nợ phải chọn khách hàng để còn theo dõi và thu sau.', 4000);
    }
    var qp = quyPt(posDon.pt) || {};
    if (qp.bat && !(posDon.mtc || '').trim()) return toast('Phương thức ' + posDon.pt + ' bắt buộc nhập ' + (qp.nhan || 'mã tham chiếu') + '.');
    /* Chuyen khoan: noi dung khach chuyen chinh la ma bill in trong QR. */
    if (posDon.pt === 'Chuyển khoản' && !(posDon.mtc || '').trim()) posDon.mtc = posDon.bill || '';
  }
  var canhBao = (!laApp && posDon.pt === 'Tiền mặt' && dua && dua < phaiThu) ? '\n⚠ Khách mới đưa ' + money(dua) + ' đ, còn thiếu ' + money(phaiThu - dua) + ' đ.' : '';
  /* Hai bill giong het nhau trong vong hai phut thuong la bam trung. */
  try {
    var kqT = await api('vagabond.ban_hang.pos_ds_bill', { quay: posQuay.ma || '' });
    var gio = Date.now();
    var trung = ((kqT && kqT.bill) || []).filter(function (r) {
      var t = new Date(String(r.creation || '').replace(' ', 'T')).getTime();
      return Math.abs((r.grand_total || 0) - phaiThu) < 1 && (gio - t) < 2 * 60 * 1000;
    });
    if (trung.length) canhBao += '\n⚠ CÓ ' + trung.length + ' HOÁ ĐƠN CÙNG SỐ TIỀN ' + money(phaiThu) + ' đ vừa lưu chưa đầy 2 phút. Có phải bấm trùng không? Kiểm trong danh sách hoá đơn trước khi thu tiếp.';
  } catch (e) { }
  var ok = await confirmSheet(
    (laApp ? 'Lưu hoá đơn ' : 'Thu ') + money(phaiThu) + ' đ - ' + (laApp ? posDon.che_do : posDon.pt),
    posQuay.ten + ' · ' + posDon.che_do + '\n' + posDon.mon.map(function (m) { return m.ten + ' x' + money(m.qty); }).join(', ') +
    (giamKm ? '\n' + ((posDon.kmKq.ap || []).map(function (a) { return a.ten + ' −' + money(a.giam) + ' đ'; }).join('\n')) : '') +
    (giamTay ? '\nGiảm tay ' + money(giamTay) + ' đ' : '') +
    (ship ? '\nPhí giao ' + money(ship) + ' đ' : '') +
    (giamDiem ? '\nTrừ ' + money(posDon.diemVe.so_diem) + ' điểm thành viên −' + money(giamDiem) + ' đ' : '') + canhBao,
    laApp ? 'Lưu hoá đơn' : 'Thu tiền, lưu hoá đơn');
  if (!ok) return;
  var otpKm = await posXinOtpKm();
  if (posDon.kmKq && posDon.kmKq.can_otp && !otpKm) return toast('Chưa có mã OTP nên chưa lưu được hoá đơn.', 4000);
  if (posDangLuu) return;
  posDangLuu = true;
  busy(true);
  var r;
  try {
    r = await api('vagabond.ban_hang.tao_don_tay', {
      ngay: today(), nguon: nguon, ma_don: laApp ? (posDon.ma || '') : posDon.bill, ten_khach: posDon.ten || '', dien_thoai: posDon.sdt || '',
      /* Gui ca phuong thuc cua don cua san. May chu van la noi chot: nguon
         chi di mot phuong thuc thi `_kiem_pt` nan ve dung phuong thuc do,
         gui sai cung khong vao duoc. Nhung nguon di duoc hai phuong thuc
         thi phai gui, khong thi lua chon cua thu ngan roi mat. */
      pt: posDon.pt || '', ma_tham_chieu: laApp ? (posDon.ma || '') : (posDon.mtc || ''),
      items: JSON.stringify(posDon.mon.map(function (m) { return { item_code: m.item_code, qty: m.qty, rate: m.rate, tuy_chon: (m.tc || []).join(', '), ghi_chu: posGcGui(m, posMaAppHienTai()), combo: m.combo || '' }; })),
      giam_gia: giamTay, phi_ship: ship, quay: posQuay.ma || '', so_ban: posDon.so_ban || '',
      khach_no: (posDon.khach_no && posDon.khach_no.ma) || '',
      khach_ma: posDon.khach_ma || '',
      /* CHI gui ma chuong trinh, KHONG gui so tien giam - may chu tu tinh
         lai tu gio hang (anh Viet 11/08/2026). */
      ctkm_ap: JSON.stringify(posDon.ctkm || []),
      combo_ap: JSON.stringify(posDon.combo || []),
      ma_voucher: posDon.maVc || '',
      otp_km: otpKm || '',
      /* Ve tru diem: may chu kiem lai tran tren grand_total THAT roi moi
         tru. May khach khong gui so tien giam. */
      ve_diem: (posDon.diemVe && posDon.diemVe.ve) || '',
      ghi_chu: (posDon.km ? 'KM: ' + posDon.km.ten + (posDon.ghi_chu ? '. ' : '') : '') + (posDon.ghi_chu || ''),
      xhd_mst: posDon.xhd_mo ? (posDon.xh.mst || '') : '',
      xhd_ten: posDon.xhd_mo ? (posDon.xh.ten || '') : '',
      xhd_dia_chi: posDon.xhd_mo ? (posDon.xh.dc || '') : '',
      xhd_email: posDon.xhd_mo ? (posDon.xh.email || '') : ''
    });
  } catch (e) { posDangLuu = false; busy(false); return toast((e && e.message) || 'Lưu hoá đơn lỗi, thử lại.', 4000); }
  posDangLuu = false;
  busy(false);
  var thu = (r && r.grand_total) || phaiThu;
  /* So diem VUA CONG cua chinh hoa don nay. Khong bay so du con lai: so du
     la thu chi chu the moi can biet, con so vua cong thi ai nhin cung chi
     suy ra duoc tu tong tien tren man, khong lo them gi. */
  cfdCamOn(thu, (r && r.diem && r.diem.tich) || 0);
  var laCK = !laApp && posDon.pt === 'Chuyển khoản';
  var thoi = !laApp && posDon.pt === 'Tiền mặt' && dua >= thu ? dua - thu : 0;
  var maCk = posDon.mtc || posDon.bill || '';
  /* Nguon phai doc TRUOC khi mo bill moi: posMoi() dat lai che_do ve
     "Tai cho", doc sau la don Mang ve lai ra ma QR cua nguon Tai cho. */
  var nguonCk = posNguonThuc();
  /* Giu ban sao de in bill ngay, truoc khi mo bill moi. */
  posBillVua = {
    name: (r && r.name) || '', bill: posDon.bill, mon: posDon.mon.slice(),
    tong: tong, giam: giam + ((r && r.tru_diem && r.tru_diem.so_tien) || 0), giamTay: giamTay,
    truDiem: (r && r.tru_diem) || null,
    kmAp: ((posDon.kmKq && posDon.kmKq.ap) || []).slice(),
    thu: thu, pt: laApp ? posDon.che_do : posDon.pt,
    /* mtc PHAI co mat. Tem in ra ghep "GrabFood 678" tu nguon cong ma tham
       chieu; thieu o nay thi ham in tem khong tim thay ma nao, va con so
       De go vao chip 678 chi song tren man hinh chu khong bao gio di toi
       may in (De bao 19/08/2026). Voi don san thi ma nam o posDon.ma, voi
       don thuong thi nam o posDon.mtc - dung dung cach may chu nhan. */
    mtc: laApp ? (posDon.ma || '') : (posDon.mtc || ''),
    quay: (posQuay && posQuay.ma) || '', nguon: nguonCk,
    ghi_chu: posDon.ghi_chu || '', ten: posDon.ten || '', so_ban: posDon.so_ban || '', tam_tinh: 0,
    diem: (r && r.diem) || null
  };
  posDon = posMoi();
  posHomNayTxt = null;
  /* Van la ma QR khach da quet luc nay, khong doi sang so phieu - de neu
     khach chua chuyen kip thi quet lai van ra dung noi dung. */
  if (laCK) return posQrSheet(maCk, thu, (r && r.name) || '', nguonCk);
  /* Đơn hàng tặng: đưa thẳng sang màn bill để khai loại tặng và lý do. Bỏ
     qua bảng "đã thu" vì đơn tặng không thu đồng nào, và việc còn dở là
     khai chứ không phải in. */
  if (posBillVua.pt === 'Hàng tặng' && posBillVua.name) {
    toast('Đơn hàng tặng: khai loại tặng và lý do để giám đốc duyệt.', 4500);
    var tenTang = posBillVua.name;
    return go(function () { scrPosBill(tenTang); }, true);
  }
  var ov = document.createElement('div'); ov.className = 'sh';
  ov.innerHTML = '<div class="shb" style="padding:22px 16px calc(env(safe-area-inset-bottom,0px) + 16px);text-align:center">' +
    '<div style="font-size:44px">✅</div>' +
    '<div style="font-size:19px;font-weight:700;margin:6px 0 2px">Đã thu ' + money(thu) + ' đ</div>' +
    (thoi ? '<div style="font-size:17px;color:#0f766e;font-weight:700">Thối khách ' + money(thoi) + ' đ</div>' : '') +
    '<div style="font-size:12.5px;color:#a0a6b4;margin-top:6px">' + h((r && r.name) || '') + ' · ghi sổ ngay tại quầy trong Hoá đơn hôm nay</div>' +
    '<div style="display:flex;gap:8px;margin-top:16px">' +
    '<button class="btn gh" data-in style="flex:1;margin:0">🖨 In hoá đơn</button>' +
    '<button class="btn" data-y style="flex:1;margin:0">🧾 Hoá đơn mới</button></div>' +
    posNutIn(posBillVua) +
    '<button class="btn gh" data-ds style="margin-top:8px">📋 Về danh sách hoá đơn</button></div>';
  document.body.appendChild(ov);
  ov.onclick = function (e) {
    if (e.target.hasAttribute('data-in')) { posInBill(posBillVua); ov.remove(); go(scrPosDs, true); return; }
    if (e.target.hasAttribute('data-pm')) { posInPhieuMon(posBillVua); return; }
    if (e.target.hasAttribute('data-tem')) { posInTemLy(posBillVua); return; }
    if (e.target.hasAttribute('data-ds')) { ov.remove(); go(scrPosDs, true); return; }
    if (e.target === ov || e.target.hasAttribute('data-y')) { ov.remove(); go(scrPosQuay, true); }
  };
}



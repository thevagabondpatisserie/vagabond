/* ---------- Man hinh phu cho khach (CFD) - phan PHAT (anh Viet 20/08/2026)

   Quay TCV co mot man hinh nho quay ra phia khach. Truoc nay no khong hien
   gi ca, nen khach chuyen khoan phai chom nguoi qua nhin man hinh cua thu
   ngan de quet ma QR. Vua bat tien vua khong dep, va thu ngan phai xoay
   may tinh moi lan.

   Ba dieu da chot truoc khi viet dong nay
   ---------------------------------------
   1. TRANG /man-hinh-khach KHONG GOI MOT API NAO. Toan bo du lieu di qua
      BroadcastChannel tu tab tinh tien sang. Ly do: neu trang do goi API ma
      phien dang nhap het han thi Frappe da ra form dang nhap, va cai form
      do se nam chan giua man hinh ngay truoc mat khach. Man hinh khach chi
      la cai ti vi, khong phai mot phien lam viec.

   2. RANH GIOI RIENG TU. Man hinh nay quay ra cho dong nguoi qua lai. Chi
      duoc bay: ten mon, so luong, so tien, ma QR, va tinh trang da nhan
      tien. TUYET DOI khong bay so dien thoai, ma khach, hang the, diem tich
      luy, cong no hay ma so thue. Ca kiem thu nhom 50 chot lai dieu nay:
      them mot o cam vao goi tin la cong kiem do ngay.

   3. TRANG THAI PHAI NHIN THAY DUOC. Khoi tren man tinh tien noi that ra
      la man hinh khach dang bat hay chua, dua tren tin bao "song" ma trang
      do gui nguoc lai. Khong bao "da gui" roi thoi. Bai hoc email ba ngay
      16/08: khong bao giao thanh cong khi chua co ai xac nhan.

   Vi sao co bat tay va nhip tim
   -----------------------------
   BroadcastChannel khong luu lai tin cu. Mo man hinh khach sau khi thu ngan
   da bam vai mon thi no khong nhan duoc gi het, man hinh trang tron. Nen no
   phat mot tin "xin", va tab tinh tien gui lai ngay goi cuoi cung.
   Nhip tim ba giay thi de chieu nguoc lai: tab tinh tien tat may, dong tab,
   hay mat dien, man hinh khach khong nhan nhip nua thi tu ve man chao chu
   khong dung im voi so tien cua khach truoc. */

var CFD_KENH = 'vagabond-cfd';
var CFD_GT = 1;               /* so hieu giao thuc, doi la doi ca hai ben */
var CFD_NHIP = 3000;          /* phat lai trang thai moi ba giay */
var CFD_SONG_HAN = 9000;      /* qua ngan nay khong nghe tin song la coi nhu tat */
var CFD_TRANG = '/man-hinh-khach';

var cfdBang = null;      /* BroadcastChannel; null la trinh duyet nay khong co */
var cfdTab = '';         /* ma rieng cua tab tinh tien nay */
var cfdHen = null;       /* id nhip tim */
var cfdGoiCuoi = null;   /* goi tin gui gan nhat, de tra loi khi co ai xin */
var cfdSongLuc = 0;      /* luc cuoi cung man hinh khach bao no con song */

function cfdCo() {
  try { return typeof BroadcastChannel === 'function'; } catch (e) { return false; }
}

/* Ma tab sinh mot lan khi nap app. Hai tab tinh tien cung mo thi man hinh
   khach bam theo mot tab thoi, khong nhay qua nhay lai. */
function cfdMaTab() {
  if (cfdTab) return cfdTab;
  var chu = 'ACDEFGHJKLMNPQRSTUVWXY3456789';
  var s = '';
  for (var i = 0; i < 6; i++) s += chu.charAt(Math.floor(Math.random() * chu.length));
  cfdTab = s;
  return cfdTab;
}

function cfdKenh() {
  if (!cfdCo()) return null;
  if (cfdBang) return cfdBang;
  try { cfdBang = new BroadcastChannel(CFD_KENH); } catch (e) { cfdBang = null; return null; }
  cfdMaTab();
  cfdBang.onmessage = function (e) {
    var m = e && e.data;
    if (!m || m.gt !== CFD_GT) return;
    /* Man hinh khach vua mo, chua co gi de ve: gui lai ngay goi cuoi cung. */
    if (m.loai === 'xin') { if (cfdGoiCuoi) cfdPhat(cfdGoiCuoi); return; }
    /* No bao con song: khoi tren man tinh tien doi chu ngay. */
    if (m.loai === 'song') { cfdSongLuc = Date.now(); cfdVeChip(); return; }
  };
  return cfdBang;
}

function cfdPhat(goi) {
  var k = cfdKenh();
  if (!k || !goi) return false;
  try { k.postMessage(goi); return true; } catch (e) { return false; }
}

/* ---------------------------------------------------------- phan thuan */

/* Dung goi tin trang thai. Ham THUAN: vao la vat the, ra la vat the, khong
   dung DOM, khong dung mang, nen ca kiem thu chay duoc bang node.

   DANH SACH O DUOC PHEP nam gon trong ham nay. Ai muon them o thi phai sua
   dung day, va ca kiem thu nhom 50 se soi lai. */
function cfdDungGoi(don, quay, phaiThu, qr, tab, luc) {
  don = don || {};
  quay = quay || {};
  var mon = (don.mon || []).map(function (m) {
    return {
      ten: String(m.ten || ''),
      sl: Number(m.qty) || 0,
      tien: (Number(m.qty) || 0) * (Number(m.rate) || 0)
    };
  });
  var tong = mon.reduce(function (t, m) { return t + m.tien; }, 0);
  var tra = Number(phaiThu) || 0;
  var g = {
    gt: CFD_GT,
    loai: 'trang_thai',
    tab: String(tab || ''),
    luc: Number(luc) || 0,
    man: mon.length ? 'don' : 'chao',
    quay: String(quay.ten || quay.ma || ''),
    mon: mon,
    tong: tong,
    giam: Math.max(0, tong - tra),
    tra: tra,
    pt: String(don.pt || ''),
    qr: null
  };
  if (qr && qr.url) {
    g.qr = {
      url: String(qr.url),
      nd: String(qr.nd || ''),
      ten: String(qr.ten || ''),
      bank: String(qr.bank || ''),
      stk: String(qr.stk || ''),
      nhan: Number(qr.nhan) || 0,
      du: !!qr.du
    };
  }
  return g;
}

/* Goi tin cam on sau khi luu hoa don xong. Khong mang theo mon nao, khong
   mang theo QR: viec cua no la doi man hinh sang loi cam on roi ve man
   chao, khong de so tien cua khach truoc nam lai tren man. */
function cfdGoiCamOn(quay, thu, tab, luc) {
  quay = quay || {};
  return {
    gt: CFD_GT,
    loai: 'trang_thai',
    tab: String(tab || ''),
    luc: Number(luc) || 0,
    man: 'cam_on',
    quay: String(quay.ten || quay.ma || ''),
    mon: [],
    tong: Number(thu) || 0,
    giam: 0,
    tra: Number(thu) || 0,
    pt: '',
    qr: null
  };
}

/* ------------------------------------------------------ phan cham DOM */

function cfdNhipTat() { if (cfdHen) { clearInterval(cfdHen); cfdHen = null; } }

function cfdNhipBat() {
  cfdNhipTat();
  cfdHen = setInterval(function () {
    /* Roi man tinh tien thi thoi phat, khoi ban tin vo ich. Man hinh khach
       het chin muoi giay khong nghe gi se tu ve man chao. */
    if (!document.getElementById('posNd')) return cfdNhipTat();
    if (!cfdGoiCuoi) return;
    cfdGoiCuoi.luc = Date.now();
    cfdPhat(cfdGoiCuoi);
  }, CFD_NHIP);
}

/* Day trang thai gio hang sang man hinh khach. Goi o cuoi scrPosQuay nen
   moi lan them mon, doi phuong thuc, hay SePay bao tien ve deu tu day. */
function cfdDay(don, quay, phaiThu, nguon, laApp) {
  if (!cfdCo()) return;
  var qr = null;
  if (!laApp && don && don.pt === 'Chuyển khoản' && phaiThu > 0) {
    var nd = posNoiDungCk(don.bill, '', nguon);
    var tk = posTaiKhoan(nguon, '') || {};
    var url = posQrUrl(nd, phaiThu, nguon, '');
    if (url) {
      qr = {
        url: url, nd: nd, ten: tk.ten || '', bank: tk.bank || '', stk: tk.stk || '',
        nhan: posSepayNhan || 0, du: (posSepayNhan || 0) >= phaiThu - 1
      };
    }
  }
  cfdGoiCuoi = cfdDungGoi(don, quay, phaiThu, qr, cfdMaTab(), Date.now());
  cfdPhat(cfdGoiCuoi);
  cfdNhipBat();
}

function cfdCamOn(thu) {
  if (!cfdCo()) return;
  cfdGoiCuoi = cfdGoiCamOn(posQuay, thu, cfdMaTab(), Date.now());
  cfdPhat(cfdGoiCuoi);
}

/* Khoi nho tren man tinh tien. Noi that ra man hinh khach dang bat hay
   chua, khong bao bua. */
function cfdKhoi() {
  if (!cfdCo()) {
    return '<div class="card" style="padding:11px 14px;font-size:12.5px;color:#98a2b3">' +
      '🖥 Trình duyệt này không có BroadcastChannel nên chưa bật được màn hình khách. ' +
      'Dùng Chrome hoặc Safari bản mới trên máy quầy.</div>';
  }
  return '<div class="card" id="cfdKhoiO" style="padding:11px 14px">' +
    '<div style="display:flex;align-items:center;gap:10px">' +
    '<span style="font-size:20px">🖥</span>' +
    '<div style="flex:1;min-width:0"><div style="font-weight:800;font-size:14px">Màn hình khách</div>' +
    '<div id="cfdChip" style="font-size:12.5px;color:#98a2b3">Chưa mở màn hình khách.</div></div>' +
    '<button class="btn gh" id="cfdMoNut" style="margin:0;padding:8px 14px">Mở</button>' +
    '</div></div>';
}

function cfdVeChip() {
  var o = document.getElementById('cfdChip');
  if (!o) return;
  var song = cfdSongLuc && (Date.now() - cfdSongLuc) < CFD_SONG_HAN;
  o.textContent = song
    ? 'Đang bật, khách nhìn thấy giỏ hàng và mã QR.'
    : 'Chưa mở màn hình khách.';
  o.style.color = song ? '#0f766e' : '#98a2b3';
}

function cfdGan() {
  if (!cfdCo()) return;
  cfdKenh();
  cfdVeChip();
  var n = document.getElementById('cfdMoNut');
  if (n) {
    n.onclick = function () {
      /* Dat ten cua so co dinh: bam Mo lan hai thi dua cua so cu len chu
         khong de ba cai man hinh khach chong len nhau. */
      try { window.open(CFD_TRANG, 'vgbManKhach'); }
      catch (e) { toast('Trình duyệt chặn mở cửa sổ. Mở tay địa chỉ ' + CFD_TRANG + ' rồi kéo sang màn hình phụ.', 6000); }
    };
  }
}

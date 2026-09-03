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
function cfdDungGoi(don, quay, phaiThu, qr, tab, luc, giamVi) {
  don = don || {};
  quay = quay || {};
  var mon = (don.mon || []).map(function (m) {
    return {
      ten: String(m.ten || ''),
      sl: Number(m.qty) || 0,
      tien: (Number(m.qty) || 0) * (Number(m.rate) || 0),
      /* ANH MON, them 01/09/2026 theo y anh Viet: *"hien thi ten mon anh
         mon, roi hien thi ma QR tren nen xanh robin egg cua branding"*.

         Anh mon KHONG phai du lieu rieng tu: no la anh san pham ai vao
         tiem cung nhin thay tren menu. Ranh gioi rieng tu cua man nay van
         nguyen: khong so dien thoai, khong ma khach, khong hang the,
         khong diem tich luy, khong cong no, khong ma so thue. */
      anh: String(m.anh || '')
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
    /* LY DO GIAM, do man tinh tien tinh san roi chuyen sang (xem
       posLyDoGiam ben 09-tinh-tien-quay.js). O day CHI chep lai mot nhan
       ngan, khong doc mot o rieng tu nao cua don - do la ly do phep tinh
       nam ben kia chu khong nam day. Nhan la "thanh vien" hay "uu dai",
       khong bao gio mang ten hang the. */
    giam_vi: String(giamVi || '').slice(0, 24),
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
function cfdGoiCamOn(quay, thu, tab, luc, diem) {
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
    giam_vi: '',
    tra: Number(thu) || 0,
    pt: '',
    qr: null,
    /* So diem VUA CONG cua hoa don nay. Khong phai so du: so du la thu chi
       chu the moi can biet. Khong co diem thi de 0 va man hinh bo qua. */
    diem: Math.max(0, Math.round(Number(diem) || 0))
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
function cfdDay(don, quay, phaiThu, nguon, laApp, giamVi) {
  if (!cfdCo()) return;
  var qr = null;
  if (!laApp && don && don.pt === 'Chuyển khoản' && phaiThu > 0) {
    /* Truyen ma diem vao ca ba cho. De rong la ba ham roi ve tai khoan
       mac dinh, nen man hinh khach bay ma QR vao TAI KHOAN CHUNG trong khi
       man thu ngan bay ma QR vao tai khoan rieng cua diem - hai man mot
       ben mot neo, khach quet cai nao cung duoc va tien ve sai cho. */
    var maDiem = (quay && quay.ma) || '';
    var nd = posNoiDungCk(don.bill, maDiem, nguon);
    var tk = posTaiKhoan(nguon, maDiem) || {};
    var url = posQrUrl(nd, phaiThu, nguon, maDiem);
    if (url) {
      qr = {
        url: url, nd: nd, ten: tk.ten || '', bank: tk.bank || '', stk: tk.stk || '',
        nhan: posSepayNhan || 0, du: (posSepayNhan || 0) >= phaiThu - 1
      };
    }
  }
  cfdGoiCuoi = cfdDungGoi(don, quay, phaiThu, qr, cfdMaTab(), Date.now(), giamVi);
  cfdPhat(cfdGoiCuoi);
  cfdNhipBat();
}

function cfdCamOn(thu, diem) {
  if (!cfdCo()) return;
  cfdGoiCuoi = cfdGoiCamOn(posQuay, thu, cfdMaTab(), Date.now(), diem);
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
    /* flex:none BAT BUOC, xem chu thich cung kieu o khoi Ca lam viec. */
    '<button class="btn gh" id="cfdMoNut" style="margin:0;padding:8px 14px;flex:none;width:auto">Mở</button>' +
    '</div></div>';
}

function cfdVeChip() {
  var o = document.getElementById('cfdChip');
  if (!o) return;
  var song = cfdSongLuc && (Date.now() - cfdSongLuc) < CFD_SONG_HAN;
  /* Chua mo thi noi luon PHAI LAM GI. Man hinh phu o quay Tran Cao Van
     dang duoc dat che do Duplicate nen no chi soi lai man cua thu ngan;
     ba cau nay la ba viec can lam de no thanh man hinh rieng. */
  o.textContent = song
    ? 'Đang bật, khách nhìn thấy giỏ hàng và mã QR.'
    : 'Chưa mở. Bấm Mở, máy tự đặt sang màn hình phụ; chạm vào màn đó một lần để phóng to. '
    + 'Windows phải để màn hình phụ ở chế độ Extend (Win+P), không phải Duplicate.';
  o.style.color = song ? '#0f766e' : '#98a2b3';
}

/* ---------------------------------------------- mo dung man hinh phu

   HAI TRIEU CHUNG anh Viet bao 03/09/2026, va vi sao cung mot goc:

   1. "Mat cam ung man hinh chinh cua thu ngan." Cua so man hinh khach mo
      bang window.open thi Windows dat no LEN TREN cua so dang co, tren
      CUNG man hinh voi thu ngan. Bam Toan man hinh o do la no phu kin man
      thu ngan. Thu ngan cham vao dau cung la cham vao man hinh khach, nen
      tuong may hong cam ung. Man phu de Duplicate thi con te hon: hai man
      la mot, keo di dau cung the.

   2. "Man hinh khach toi den." Man phu khong ai cham vao, Windows tat no
      di de tiet kiem dien sau muoi lam phut. Phan nay sua ben trang
      man-hinh-khach.html bang Wake Lock, khong o day.

   Cach sua o day: khong bat thu ngan keo cua so nua. Hoi trinh duyet may
   nay co bao nhieu man hinh (Window Management API, Chrome tu ban 100),
   co man phu thi DAT THANG cua so len man phu voi dung kich thuoc man do.
   Chi thay MOT man hinh thi noi thang la dang Duplicate va KHONG mo, vi
   mo ra chi de no de len man thu ngan.

   Trinh duyet cu khong co API nay thi ve duong cu va noi ro phai keo tay.

   THUAN: hai ham dau khong cham DOM, ca kiem chay bang node duoc. */

/* Chon man hinh phu trong danh sach trinh duyet tra ve. Uu tien man KHONG
   phai man chinh; khong co thi lay man thu hai; chi co mot man thi null. */
function cfdChonManPhu(cacMan) {
  cacMan = cacMan || [];
  for (var i = 0; i < cacMan.length; i++) {
    if (cacMan[i] && cacMan[i].isPrimary === false) return cacMan[i];
  }
  return cacMan.length > 1 ? cacMan[1] : null;
}

/* Chuoi dac tinh cua window.open de cua so nam TRON trong man phu do.
   Dung avail* chu khong dung width/height: avail da tru thanh tac vu. */
function cfdDacTinhCuaSo(man) {
  if (!man) return '';
  return 'popup=1,left=' + Math.round(Number(man.availLeft) || 0) +
    ',top=' + Math.round(Number(man.availTop) || 0) +
    ',width=' + Math.round(Number(man.availWidth) || 1280) +
    ',height=' + Math.round(Number(man.availHeight) || 720);
}

async function cfdMo() {
  var w = null;
  /* screen.isExtended khong can xin quyen: false chac chan la may chi co
     mot man hinh (hoac Duplicate). Noi ngay, dung mo. */
  try {
    if (window.screen && window.screen.isExtended === false) {
      toast('Máy chỉ thấy MỘT màn hình. Windows đang để Duplicate: bấm Win+P chọn Extend, rồi bấm Mở lại.', 9000);
      return;
    }
  } catch (e0) { }
  if (typeof window.getScreenDetails === 'function') {
    try {
      /* Lan dau Chrome hoi quyen "quan ly cua so tren cac man hinh". Bam
         Cho phep mot lan la nho. Tu choi thi roi xuong duong cu ben duoi. */
      var sd = await window.getScreenDetails();
      var phu = cfdChonManPhu(sd && sd.screens);
      if (!phu) {
        toast('Máy chỉ thấy MỘT màn hình. Windows đang để Duplicate: bấm Win+P chọn Extend, rồi bấm Mở lại.', 9000);
        return;
      }
      w = window.open(CFD_TRANG + '?phu=1', 'vgbManKhach', cfdDacTinhCuaSo(phu));
    } catch (e1) { w = null; }
  }
  if (!w) {
    /* Duong cu: trinh duyet cu, hoac bi tu choi quyen. */
    try { w = window.open(CFD_TRANG, 'vgbManKhach'); } catch (e2) { w = null; }
    if (w) toast('Đã mở. Kéo cửa sổ đó sang màn hình phụ rồi chạm vào nó một lần để phóng toàn màn hình.', 7000);
  }
  if (!w) {
    toast('Trình duyệt chặn mở cửa sổ. Mở tay địa chỉ ' + CFD_TRANG + ' rồi kéo sang màn hình phụ.', 6000);
    return;
  }
  /* Tra tieu diem ve man thu ngan: cua so vua mo cuop tieu diem, va cai
     cham dau tien cua thu ngan sau do chi de lay lai tieu diem chu khong
     bam duoc nut nao. */
  try { window.focus(); } catch (e3) { }
}

function cfdGan() {
  if (!cfdCo()) return;
  cfdKenh();
  cfdVeChip();
  var n = document.getElementById('cfdMoNut');
  if (n) n.onclick = function () { cfdMo(); };
}

/* ---------------- In ngam qua QZ Tray (anh Viet giao 21/08/2026)

   Thu ngan bam In bill thi giay ra ngay, khong hop thoai trinh duyet,
   khong canh bao "Untrusted website" cua QZ Tray. Ba tang:

     1. Ky chu ky so - may chu giu khoa rieng, xem vagabond/in_ngam.py.
     2. Render anh raster 203 DPI roi day xuong QZ, thay vi day HTML tho.
        May in nhiet dung font cua may, gap chu Viet co dau la rot dau
        hoac lech le; anh bitmap thi in ra dung y nhu tren man.
     3. Luoi an toan: QZ tat, may in rut day, chua dan chung thu - deu roi
        ve window.print() cu, kem mot toast mo. KHONG bao gio de thu ngan
        dung hinh vi mot cai may in.

   NHIP LA THU QUAN TRONG NHAT O DAY
   ---------------------------------
   window.open() phai goi NGAY trong cu cham cua nguoi dung, cham tre mot
   nhip la trinh duyet chan popup. Nen tuyet doi khong duoc "thu QZ truoc,
   hong thi mo cua so": luc biet hong thi cu cham da nguoi, popup bi chan,
   va thu ngan mat ca hai duong in.

   Vi vay trang thai QZ duoc do TRUOC va nho lai (inNgamDo), con luc bam
   in thi quyet dinh bang trang thai da biet, khong cho doi gi ca. Chua do
   xong thi mac dinh di duong trinh duyet.

   Tien to in = in an. Da kiem va cham ten truoc khi dat (QT-28). */

var IN_QZ = {
  do_roi: 0,        // da do xong chua
  co: 0,            // QZ Tray dang chay va da noi duoc
  may: [],          // ten cac may in tim thay
  tuyen: null,      // manh ten may in hoa don / tem, lay tu may chu
  loi: '',          // ly do khong dung duoc, de hien khi can
  dang_do: null     // Promise cua lan do dang chay, tranh do hai lan
};

var IN_VENDOR = {
  qz: '/assets/vagabond/js/vendor/qz-tray.js',
  h2c: '/assets/vagabond/js/vendor/html2canvas.min.js'
};

/* Nap mot thu vien ngoai mot lan duy nhat. Nap tu chinh site chu khong tu
   CDN: trang /bep la mot ban ghi Web Page nam trong co so du lieu, them
   the script vao do la sua du lieu ngoai git. Xem vendor/DOC-DAU-TIEN.md. */
var inDaNap = {};
function inNapJs(duong) {
  if (inDaNap[duong]) return inDaNap[duong];
  inDaNap[duong] = new Promise(function (ok, hong) {
    var s = document.createElement('script');
    s.src = duong;
    s.onload = function () { ok(1); };
    s.onerror = function () { inDaNap[duong] = null; hong(new Error('Không nạp được ' + duong)); };
    document.head.appendChild(s);
  });
  return inDaNap[duong];
}

/* ---------- Tang 1: noi va ky ---------- */

async function inNoiQz() {
  await inNapJs(IN_VENDOR.qz);
  if (typeof qz === 'undefined') throw new Error('Thư viện QZ Tray không nạp được');
  if (qz.websocket.isActive()) return 1;

  /* Ba cua nay phai khai TRUOC khi noi. QZ hoi chung thu va chu ky ngay
     trong luc bat tay, khai sau la muon. */
  qz.security.setCertificatePromise(function (ok, hong) {
    api('vagabond.in_ngam.chung_thu', {})
      .then(function (r) {
        if (r && r.chung_thu) ok(r.chung_thu);
        else hong(new Error('Chưa dán chứng thư QZ Tray trong Vagabond Settings'));
      })
      .catch(hong);
  });
  qz.security.setSignatureAlgorithm('SHA512');
  qz.security.setSignaturePromise(function (chuoi) {
    return function (ok, hong) {
      api('vagabond.in_ngam.ky', { chuoi: chuoi, thuat_toan: 'SHA512' })
        .then(function (r) { ok((r && r.chu_ky) || ''); })
        .catch(hong);
    };
  });

  await qz.websocket.connect({ retries: 1, delay: 1 });
  return 1;
}

/* Do mot lan luc vao man quay hoac man bep. Goi lai nhieu lan cung chi do
   mot lan, tru khi ep do lai. */
function inNgamDo(ep) {
  if (IN_QZ.dang_do) return IN_QZ.dang_do;
  if (IN_QZ.do_roi && !ep) return Promise.resolve(IN_QZ.co);
  IN_QZ.dang_do = (async function () {
    try {
      var t = await api('vagabond.in_ngam.dinh_tuyen', {});
      IN_QZ.tuyen = t;
      if (!t || !t.da_bat) {
        IN_QZ.co = 0; IN_QZ.loi = 'Chưa bật in ngầm (chưa dán chứng thư QZ Tray)';
        return 0;
      }
      await inNoiQz();
      IN_QZ.may = (await qz.printers.find()) || [];
      if (!IN_QZ.may.length) { IN_QZ.co = 0; IN_QZ.loi = 'QZ Tray không thấy máy in nào'; return 0; }
      IN_QZ.co = 1; IN_QZ.loi = '';
      return 1;
    } catch (e) {
      IN_QZ.co = 0;
      IN_QZ.loi = (e && e.message) || 'Không nối được QZ Tray';
      return 0;
    } finally {
      IN_QZ.do_roi = 1;
      IN_QZ.dang_do = null;
    }
  })();
  return IN_QZ.dang_do;
}

/* Chon may in theo vai tro. Khong tim thay manh ten thi tra null de roi
   ve trinh duyet, chu KHONG in bua vao may dau tien: in tem ly ra may in
   hoa don la hong ca cuon giay. */
function inChonMay(vaiTro) {
  var manh = (vaiTro === 'tem'
    ? (IN_QZ.tuyen && IN_QZ.tuyen.tem)
    : (IN_QZ.tuyen && IN_QZ.tuyen.hoa_don)) || '';
  if (!manh) return null;
  var m = manh.toLowerCase();
  var hop = (IN_QZ.may || []).filter(function (t) {
    return String(t).toLowerCase().indexOf(m) >= 0;
  });
  return hop.length ? hop[0] : null;
}

/* ---------- Tang 2: bien HTML thanh anh raster ---------- */

/* 1 mm = 203/25.4 diem o may in 203 DPI. Tra ve so diem anh can rong. */
function inSoDiem(rongMm, dpi) {
  return Math.round((rongMm || 72) * ((dpi || 203) / 25.4));
}

/* Chup ca to HTML thanh anh, bang mot IFRAME an chu khong bang mot the div.

   Vi sao phai la iframe: to bill mang theo CSS cua no, trong do co nhung
   luat quet ca trang nhu `*{margin:0}` va `body{width:72mm}`. Nhet the
   <style> do vao mot the div giua app la CSS do de len CA app - menu xo
   lech, chu bay mat - vi the <style> khong biet gioi han theo the cha.
   Trong iframe thi CSS dong khung o do, va quan trong hon: anh chup ra
   giong HET to ma trinh duyet se in, vi hai duong dung chung mot to.

   Ve do phan giai: don vi mm trong CSS la co dinh, 1mm bang 96/25.4 diem
   CSS. Bill 72mm rong 272 diem CSS. May in 203 DPI can 575 diem. Nen giu
   iframe dung be ngang that roi chup o scale 203/96: chu nho ra sac net
   dung nhu may in ve duoc, khong phong to mot anh mo. */
async function inChupRaster(tepHtml, rongMm, dpi, duongDan) {
  await inNapJs(IN_VENDOR.h2c);
  if (typeof html2canvas === 'undefined') throw new Error('html2canvas không nạp được');
  var rongCss = Math.ceil((rongMm || 72) * (96 / 25.4));
  var khung = document.createElement('iframe');
  khung.setAttribute('aria-hidden', 'true');
  khung.setAttribute('style',
    'position:fixed;left:-10000px;top:0;border:0;background:#fff;' +
    'width:' + rongCss + 'px;height:2400px;z-index:-1');
  document.body.appendChild(khung);
  try {
    await new Promise(function (ok, hong) {
      var xong = 0;
      khung.onload = function () { if (!xong) { xong = 1; ok(1); } };
      /* srcdoc giu nguyen goc same-origin nen html2canvas doc duoc ben
         trong. Ban do may chu dung thi tro thang iframe sang dia chi,
         cung same-origin nen doc duoc y het. Kem mot han 6 giay: to bill
         co ma QR tai tu mang, ket mang thi cho mai khong xong ma thu ngan
         thi dang doi giay. */
      if (duongDan) khung.src = duongDan; else khung.srcdoc = tepHtml;
      setTimeout(function () { if (!xong) { xong = 1; ok(0); } }, 6000);
    });
    var tl = khung.contentDocument;
    if (!tl || !tl.body) throw new Error('Không dựng được khung in');
    /* Cho font va anh trong khung ve xong roi hay chup. Thieu nhip nay
       thi bill ra thieu logo hoac thieu ma QR. */
    if (tl.fonts && tl.fonts.ready) { try { await tl.fonts.ready; } catch (e) { /* bo qua */ } }
    await new Promise(function (ok) { setTimeout(ok, 120); });
    var canvas = await html2canvas(tl.body, {
      backgroundColor: '#ffffff',
      scale: (dpi || 203) / 96,
      width: rongCss,
      windowWidth: rongCss,
      height: Math.max(tl.body.scrollHeight, 1),
      logging: false,
      useCORS: true
    });
    return canvas.toDataURL('image/png').split(',')[1];
  } finally {
    document.body.removeChild(khung);
  }
}

/* ---------- Tang 3: cua chinh, va luoi an toan ---------- */

/* Chen the script tu in vao to HTML, dung nhu cac man van lam tu truoc.
   Chi duong TRINH DUYET dung the nay; to dem di chup raster thi khong,
   neu khong may quay se mo them mot hop thoai in giua luc in ngam. */
function inThemLenhIn(tepHtml, chamMs) {
  var s = '<' + 'script>window.onload=function(){setTimeout(function(){window.print()},' +
    (chamMs || 900) + ')}<' + '/script>';
  var i = tepHtml.lastIndexOf('</body>');
  return i < 0 ? (tepHtml + s) : (tepHtml.slice(0, i) + s + tepHtml.slice(i));
}

/* Mo cua so in cua trinh duyet nhu tu truoc toi nay. Tach ra thanh ham
   rieng de duong roi ve chi con mot cho, va de goi duoc NGAY trong cu
   cham (xem ghi chu ve nhip o dau tep). */
function inQuaTrinhDuyet(tieuDe, tepHtml, chamMs) {
  var w = window.open('', '_blank');
  if (!w) { toast('Trình duyệt chặn cửa sổ in. Cho phép popup rồi bấm lại.', 4000); return null; }
  w.document.write(inThemLenhIn(tepHtml, chamMs));
  w.document.close();
  return w;
}

/* HAI NHIP CHO MAN GOI VAO - dung nhip nay chu dung tu mo cua so.

   Nhip 1, goi NGAY dau ham in, truoc moi await: `inMoCuaSoNeuCan`. Neu
   in ngam dung duoc thi tra null va khong mo gi ca; neu khong thi mo cua
   so trinh duyet ngay trong cu cham, luc popup con duoc phep.

   Nhip 2, goi cuoi ham sau khi da dung xong to HTML: `inTo`, truyen lai
   cai cua so vua mo o nhip 1.

   Tach hai nhip vi cac man in deu co await o giua (hoi ma QR, hoi ten
   thu ngan). Doi xong moi mo cua so la trinh duyet chan popup - loi nay
   da co that tu truoc, xem ghi chu goc trong posInBill. */
function inSanSang(vaiTro) {
  return (IN_QZ.do_roi && IN_QZ.co && inChonMay(vaiTro)) ? 1 : 0;
}

function inMoCuaSoNeuCan(vaiTro) {
  if (inSanSang(vaiTro)) return null;
  var w = window.open('', '_blank');
  if (!w) toast('Trình duyệt chặn cửa sổ in. Cho phép popup rồi bấm lại.', 4000);
  /* Chua do QZ lan nao thi do ngay bay gio, de lan in sau di duong ngam. */
  if (!IN_QZ.do_roi) inNgamDo();
  return w || 'chan';
}

async function inTo(vaiTro, tieuDe, tepHtml, rongMm, chamMs, w) {
  if (w === 'chan') return 'chan';
  if (w) {
    w.document.write(inThemLenhIn(tepHtml, chamMs));
    w.document.close();
    return 'trinh-duyet';
  }
  return await inGiay(vaiTro, tieuDe, tepHtml, rongMm, chamMs);
}

/* IN: duong duy nhat moi man goi vao.

     vaiTro   'hoa_don' hoac 'tem' - quyet dinh day sang may in nao
     tieuDe   ten cua so in, chi thay khi in bang trinh duyet
     tepHtml  ca to HTML, KHONG kem the script tu in (ham nay tu chen khi
              di duong trinh duyet)
     rongMm   be ngang giay
     chamMs   cham bao lau roi hay goi window.print, giu dung so cu cua
              tung man vi moi to co luong anh khac nhau

   Tra ve 'qz' neu in ngam duoc, 'trinh-duyet' neu roi ve duong cu.

   Ca hai duong dung CHUNG mot to HTML: in ngam la chup chinh to do thanh
   anh. Nen sua mot dong trong mau bill la ca hai duong doi theo, khong
   bao gio lech nhau. */
async function inGiay(vaiTro, tieuDe, tepHtml, rongMm, chamMs) {
  /* Chua do xong QZ thi KHONG cho doi: mo cua so trinh duyet ngay trong
     cu cham nay, roi do QZ trong nen cho lan in sau. */
  if (!IN_QZ.do_roi || !IN_QZ.co) {
    inQuaTrinhDuyet(tieuDe, tepHtml, chamMs);
    if (!IN_QZ.do_roi) inNgamDo();
    return 'trinh-duyet';
  }
  var may = inChonMay(vaiTro);
  if (!may) {
    inQuaTrinhDuyet(tieuDe, tepHtml, chamMs);
    toast('Không tìm thấy máy in ' +
      (vaiTro === 'tem' ? 'tem' : 'hoá đơn') + ', in bằng trình duyệt.', 3500);
    return 'trinh-duyet';
  }
  try {
    var dpi = (IN_QZ.tuyen && IN_QZ.tuyen.dpi) || 203;
    var anh = await inChupRaster(tepHtml, rongMm, dpi);
    var cfg = qz.configs.create(may, {
      colorType: 'blackwhite',
      density: dpi,
      units: 'mm',
      margins: 0,
      size: { width: rongMm, height: null },
      scaleContent: false,
      rasterize: true
    });
    await qz.print(cfg, [{
      type: 'pixel', format: 'image', flavor: 'base64', data: anh
    }]);
    return 'qz';
  } catch (e) {
    /* Hong giua chung: may in rut day, QZ vua tat, chung thu het han.
       Danh dau phai do lai roi in bang trinh duyet ngay lap tuc. */
    IN_QZ.do_roi = 0;
    IN_QZ.co = 0;
    IN_QZ.loi = (e && e.message) || String(e);
    inQuaTrinhDuyet(tieuDe, tepHtml, chamMs);
    toast('Không tìm thấy QZ Tray, in bằng trình duyệt', 3500);
    return 'trinh-duyet';
  }
}

/* Ban in do MAY CHU dung (printview cua ERPNext), vi du tem HACCP theo lo.

   Khac hai ham tren o cho: to giay khong nam trong tay app, no la mot dia
   chi. Cung same-origin nen van do vao iframe roi chup duoc. Duong roi ve
   la dieu huong chinh cua so da mo sang dia chi do, y het cach cu.

   `w` la cua so da mo o nhip 1, hoac null neu in ngam dung duoc. */
async function inToTuDuongDan(vaiTro, tieuDe, duongDan, rongMm, w) {
  if (w === 'chan') return 'chan';
  if (w) { w.location.href = duongDan; return 'trinh-duyet'; }
  var may = inChonMay(vaiTro);
  if (!may) { window.open(duongDan, '_blank'); return 'trinh-duyet'; }
  try {
    var dpi = (IN_QZ.tuyen && IN_QZ.tuyen.dpi) || 203;
    /* Bo trigger_print di: to nay chi de chup, khong duoc tu bung hop
       thoai in cua trinh duyet ngay giua luc in ngam. */
    var u = duongDan.replace(/[?&]trigger_print=1/, '');
    var anh = await inChupRaster(null, rongMm, dpi, u);
    var cfg = qz.configs.create(may, {
      colorType: 'blackwhite', density: dpi, units: 'mm', margins: 0,
      size: { width: rongMm, height: null }, scaleContent: false, rasterize: true
    });
    await qz.print(cfg, [{ type: 'pixel', format: 'image', flavor: 'base64', data: anh }]);
    return 'qz';
  } catch (e) {
    IN_QZ.do_roi = 0; IN_QZ.co = 0;
    IN_QZ.loi = (e && e.message) || String(e);
    window.open(duongDan, '_blank');
    toast('Không tìm thấy QZ Tray, in bằng trình duyệt', 3500);
    return 'trinh-duyet';
  }
}

/* Man Cai dat co nut nay: bao ro dang in bang duong nao va thay may in
   nao, de khoi phai doan khi quay keu "may khong ra giay". */
async function inNgamTinhTrang() {
  await inNgamDo(1);
  return {
    co: IN_QZ.co,
    loi: IN_QZ.loi,
    may: IN_QZ.may,
    may_hoa_don: inChonMay('hoa_don'),
    may_tem: inChonMay('tem'),
    tuyen: IN_QZ.tuyen
  };
}

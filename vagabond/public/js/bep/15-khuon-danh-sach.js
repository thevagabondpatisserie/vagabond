/* ========== DON MUA HANG, CONG NO PHAI TRA, HAI MAN HOA DON ==========
   (anh Viet 12/08/2026)

Bon man dung chung mot khuon: mot hang chip trang thai co dem so, mot o
tim, roi danh sach. Chip nao dang chon thi to mau; bam lai chip "Tất cả"
de bo loc.

Man nao cung doc so lieu song tu may chu, khong nho cache - ke toan mo ra
la thay dung tinh hinh luc do. */

/* Ngay dang ngan gon "11/08/2026", rong thi tra ve dau gach - posNgayVn
   co san tra ve ca thu trong tuan, dai qua cho danh sach, va no vo khi
   chuoi ngay rong. */
function ngayNgan(iso) {
  var p = String(iso || '').split('-');
  return p.length === 3 ? p[2] + '/' + p[1] + '/' + p[0] : '-';
}

/* Danh sach dai qua thi may chu chi tra ve 300 dong dau. KHONG duoc im
   lang cat bot: nguoi doc se tuong da xem het. Con so dem tren chip va so
   tong van tinh tren toan bo, chi rieng danh sach bi cat. */
function mkNhacCat(soCat, donVi) {
  if (!soCat) return '';
  return '<div style="margin-top:9px;background:#fff7ed;border:1.5px solid #fed7aa;border-radius:9px;padding:9px 11px;font-size:12.5px;color:#9a3412">' +
    'Danh sách bên dưới chỉ hiện 300 ' + donVi + ' mới nhất, còn <b>' + money(soCat) + '</b> ' + donVi +
    ' nữa chưa hiện. Thu hẹp khoảng ngày hoặc bấm một chip trạng thái để xem cho đủ. Các con số tổng ở trên vẫn tính đủ.</div>';
}

var poNhom = '', poNgay = 60, poTim = '', poXem = null;
var ktBanNhom = '', ktBanNgay = 30, ktBanQuay = '', ktBanTim = '';
var ktMuaNhom = '', ktMuaNgay = 60, ktMuaTim = '';

/* Hang chip co dem so, dung chung cho ca bon man. */
function mkChipNhom(ds, dem, dangChon, thuoc) {
  return kmHangChip(ds.map(function (n) {
    var so = (dem || {})[n.k];
    return posChipNut(thuoc + '="' + h(n.k) + '"',
      n.ic + ' ' + h(n.ten) + (so ? ' <b>' + so + '</b>' : ''), dangChon === n.k);
  }).join(''));
}

function mkChipNgay(ds, dangChon, thuoc) {
  return kmHangChip(ds.map(function (n) {
    return posChipNut(thuoc + '="' + n[0] + '"', h(n[1]), String(dangChon) === String(n[0]));
  }).join(''));
}

function mkOTim(id, gt, moTa) {
  return '<div class="card" style="padding:10px 12px">' +
    '<input class="tin" id="' + id + '" placeholder="' + h(moTa) + '" value="' + h(gt || '') + '"></div>';
}


/* ==========================================================================
   B3 - KHUON MAN DANH SACH DUNG CHUNG (anh Viet duyet 15/08/2026)

   Man hinh o day khong biet Don mua hang la gi, khong biet Hoa don la gi.
   No chi biet doc HOP DONG DU LIEU ma tang khung A2 tra ve:

       cot      moi cot co k, nhan, kieu (chu/tien/so/phan_tram/ngay/chip)
       dong     cac dong DA duoc may chu loc, xep va cat
       cong     dong TONG cuoi bang, cong dung nhung dong dang hien
       tom_tat  the so lon tren dau man, la TIEN THAT da loai don huy
       chip     ds cac chip, chip dang chon, va so dem tung chip
       loc      khai bao bo loc kem gia tri dang ap
       tong_dong / bi_cat / gioi_han

   Nghia la: them mot man danh sach moi tu nay ve sau KHONG phai viet mot
   dong JavaScript nao. Chi khai bao cot va bo loc ben Python. Dung nhu
   phan he Bao cao da chung minh hom 14/08: them BC13 den BC16 chi mat
   phan may chu, giao dien tu hien.

   Chay SONG SONG voi cac man cu, khong thay the man nao.
   ========================================================================== */

/* Tien to kg (khung), KHONG dung kh: man Khach hang o duoi da co khO() va
   khMa roi. Lan dau dat tien to kh thi ham khO cua man khach hang khai sau
   de len ham cua khuon, the so lon in ra [object Object] va so tien khong
   duoc dinh dang - bat duoc luc chay thu tren may that 15/08/2026.
   Day dung la benh cua mot file 20.000 dong voi 124 bien toan cuc, tuc ly
   do phai lam B1 tach file. */
var kgMa = '', kgXem = {}, kgTS = {};

function kgMo(ma) { kgMa = ma; go(scrKhungDs); }

function kgTs(ma) {
  if (!kgTS[ma]) kgTS[ma] = { so_ngay: 60, chip: '' };
  return kgTS[ma];
}

/* Mot o trong bang. Giong bcO cua bao cao, them kieu chip. */
function kgO(c, v, kq) {
  if (c.kieu === 'tien') return money(Math.round(flt0(v))) + ' đ';
  if (c.kieu === 'so') return money(Math.round(flt0(v) * 100) / 100);
  if (c.kieu === 'phan_tram') return (Math.round(flt0(v) * 10) / 10) + '%';
  if (c.kieu === 'ngay') { var s = String(v == null ? '' : v).slice(0, 10); return s ? ngayNgan(s) : ''; }
  if (c.kieu === 'chip') return kgTenChip(kq, v);
  return h(String(v == null ? '' : v));
}

function kgChipInfo(kq, k) {
  var ra = null;
  ((kq.chip && kq.chip.ds) || []).forEach(function (x) { if (x.k === k) ra = x; });
  return ra;
}

function kgTenChip(kq, k) {
  var c = kgChipInfo(kq, k);
  if (!c) return h(String(k == null ? '' : k));
  var mau = KG_MAU[k] || '#374151';
  return '<span style="color:' + mau + ';font-weight:700;white-space:nowrap">' + c.ic + ' ' + h(c.ten) + '</span>';
}

/* Mau theo viec con phai lam, khong theo ma ky thuat: do la viec gap,
   cam la cho xu ly, xam la khong con phai lam gi. */
var KG_MAU = {
  tre_hen: '#b3261e', qua_han: '#b3261e', cho_hoa_don: '#b45309',
  con_no: '#b45309', nhap: '#6b7280', huy: '#9ca3af',
  xong: '#0f766e', da_tra: '#0f766e', dong: '#6b7280', da_sua: '#7c3aed'
};

/* ---- the so lon tren dau man: TIEN THAT ---- */
function kgTheTomTat(kq) {
  var ds = kq.tom_tat || [];
  if (!ds.length) return '';
  var chinh = ds[1] || ds[0];
  var phu = ds.filter(function (x) { return x !== chinh; });
  return '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3;letter-spacing:.3px">' +
      h((chinh.nhan || '').toUpperCase()) + ' · TIỀN THẬT' + '</div>' +
    '<div style="font-size:26px;font-weight:800;line-height:1.25">' + kgO(chinh, chinh.gt, kq) + '</div>' +
    '<div style="font-size:12.5px;color:#6b7280;margin-top:2px">' +
      phu.map(function (x) { return h(x.nhan) + ' ' + kgO(x, x.gt, kq); }).join(' · ') + '</div>' +
    /* Anh Viet dan 15/08/2026: ke toan phai hieu ngay vi sao con so tren
       dau man khac dong TONG cuoi bang. Noi thang bang chu, khong dua vao
       tooltip - dien thoai khong co chuot de ro chuot len. */
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px;line-height:1.6;' +
      'border-top:1px dashed #e5e7eb;padding-top:7px">' +
      'Con số này tính trên <b>toàn bộ ' + money(kq.chip && kq.chip.dem ? kq.chip.dem[''] : kq.tong_dong) +
      '</b> dòng của khoảng đang lọc, đã loại đơn huỷ và đơn chưa ghi sổ, và <b>không đổi</b> khi bấm chip. ' +
      'Dòng TỔNG cuối bảng là phép cộng của đúng những dòng đang hiện.</div>' +
    '</div>';
}

/* ---- thanh bo loc: doc tu khai bao, khong viet tay cho tung man ---- */
function kgThanhLoc(kq) {
  var ts = kgTs(kq.ma), ra = '';
  (kq.loc || []).forEach(function (f) {
    if (f.kieu === 'ngay') {
      ra += '<div class="card" style="padding:10px 12px">' +
        kmHangChip([[30, '30 ngày'], [60, '60 ngày'], [180, '6 tháng'], [0, 'Tất cả']].map(function (n) {
          var dc = !ts.tu && !ts.den && String(ts.so_ngay) === String(n[0]);
          return posChipNut('data-kgngay="' + n[0] + '"', n[1], dc);
        }).join('')) +
        '<div style="display:flex;gap:8px;margin-top:8px;align-items:center">' +
        '<input class="tin" id="kgTu" type="date" value="' + h(ts.tu || '') + '" style="flex:1">' +
        '<input class="tin" id="kgDen" type="date" value="' + h(ts.den || '') + '" style="flex:1">' +
        (ts.tu || ts.den ? posChipNut('data-kgxoangay="1"', '✕', false, true) : '') +
        '</div></div>';
    } else if (f.kieu === 'tim_chu' || f.kieu === 'chon_mot') {
      /* chon_mot chua khai nguon danh sach thi tam thoi go tay dung MA.
         Ghi ro "mã" trong o de khoi go ten roi tuong may hong. Khi nao lam
         A4 co danh muc dung chung thi doi o nay thanh o chon. */
      var moTa = f.kieu === 'chon_mot' ? f.nhan + ' (gõ đúng mã)' : 'Tìm ' + f.nhan.toLowerCase();
      ra += '<div class="card" style="padding:10px 12px">' +
        '<input class="tin" data-kgtxt="' + h(f.k) + '" placeholder="' + h(moTa) + '" value="' +
        h(ts[f.k] || '') + '"></div>';
    } else if (f.kieu === 'khoang_so') {
      ra += '<div class="card" style="padding:10px 12px;display:flex;gap:8px">' +
        '<input class="tin" data-kgtxt="' + h(f.k) + '_tu" type="number" placeholder="' + h(f.nhan) + ' từ" value="' + h(ts[f.k + '_tu'] || '') + '" style="flex:1">' +
        '<input class="tin" data-kgtxt="' + h(f.k) + '_den" type="number" placeholder="đến" value="' + h(ts[f.k + '_den'] || '') + '" style="flex:1"></div>';
    } else if (f.kieu === 'co') {
      ra += '<div class="card" style="padding:10px 12px">' +
        kmHangChip(posChipNut('data-kgco="' + h(f.k) + '"', h(f.nhan), !!ts[f.k])) + '</div>';
    }
  });
  return ra;
}

/* ---- hang chip trang thai kem so dem ---- */
function kgHangChip(kq) {
  var c = kq.chip || {}, dem = c.dem || {};
  if (!(c.ds || []).length) return '';
  return '<div class="card" style="padding:10px 12px">' + kmHangChip((c.ds || []).map(function (x) {
    var n = dem[x.k] || 0;
    return posChipNut('data-kgchip="' + h(x.k) + '"', x.ic + ' ' + h(x.ten) + ' <b>' + money(n) + '</b>',
      String(c.chon || '') === String(x.k));
  }).join('')) + '</div>';
}

/* ---- bang cat dong: im lang o cho nay la nguy hiem nhat ---- */
function kgNhacCat(kq) {
  if (!kq.bi_cat) return '';
  return '<div class="card" style="padding:11px 13px;border:1.5px solid #fcd34d;background:#fffbeb">' +
    '<div style="font-size:12.5px;color:#92400e;line-height:1.65">' +
    'Khoảng này có <b>' + money(kq.tong_dong) + '</b> dòng, màn hình đang hiện <b>' + money(kq.gioi_han) +
    '</b> dòng đầu, còn <b>' + money(kq.bi_cat) + '</b> dòng chưa hiện. ' +
    'Thu hẹp khoảng ngày, gõ tìm, hoặc bấm một chip trạng thái để xem cho đủ. ' +
    'Thẻ số ở trên vẫn tính đủ cả ' + money(kq.tong_dong) + ' dòng.</div></div>';
}

/* ---- dang bang: cho may tinh va cho luc doi chieu so ---- */
function kgVeBang(kq) {
  if (!(kq.dong || []).length) return kgRong();
  var phai = { tien: 1, so: 1, phan_tram: 1 };
  var html = '<div class="card" style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:13px">' +
    '<thead><tr>' + kq.cot.map(function (c) {
      return '<th style="text-align:' + (phai[c.kieu] ? 'right' : 'left') + ';padding:10px 12px;background:#f8fafc;color:#6b7280;font-size:11.5px;font-weight:700;white-space:nowrap;position:sticky;top:0">' + h(c.nhan) + '</th>';
    }).join('') + '</tr></thead><tbody>';
  kq.dong.forEach(function (r, i) {
    html += '<tr data-kgdong="' + h(r[kq.cot[0].k]) + '" style="border-top:1px solid #f2f4f7' + (i % 2 ? ';background:#fcfdfe' : '') + '">' +
      kq.cot.map(function (c, j) {
        return '<td style="text-align:' + (phai[c.kieu] ? 'right' : 'left') + ';padding:9px 12px;white-space:nowrap' + (j === 0 ? ';font-weight:600' : '') + '">' + kgO(c, r[c.k], kq) + '</td>';
      }).join('') + '</tr>';
  });
  if (kq.cong && Object.keys(kq.cong).length) {
    /* Dong TONG de mau XAM, khac han the TIEN THAT mau xanh o tren, va ghi
       ro dang cong bao nhieu dong. Hai con so khac nhau va deu dung; cai
       nguy hiem la de ke toan tuong chung la mot. */
    html += '<tr style="border-top:2px solid #e5e7eb;background:#f3f4f6;font-weight:800">' +
      kq.cot.map(function (c, j) {
        if (j === 0) return '<td style="padding:10px 12px;white-space:nowrap;color:#4b5563">TỔNG ' + money(kq.dong.length) + ' dòng đang hiện</td>';
        var v = kq.cong[c.k] == null ? '' : kgO(c, kq.cong[c.k], kq);
        return '<td style="text-align:' + (phai[c.kieu] ? 'right' : 'left') + ';padding:10px 12px;white-space:nowrap;color:#4b5563">' + v + '</td>';
      }).join('') + '</tr>';
  }
  return html + '</tbody></table></div>';
}

/* ---- dang the: cho dien thoai, dung kieu cu nhan vien da quen ---- */
function kgVeThe(kq) {
  if (!(kq.dong || []).length) return kgRong();
  var cot = kq.cot, dau = cot[0];
  var cTien = null, cChip = null;
  cot.forEach(function (c) {
    if (!cTien && c.kieu === 'tien') cTien = c;
    if (!cChip && c.kieu === 'chip') cChip = c;
  });
  var con = cot.filter(function (c) { return c !== dau && c !== cTien && c !== cChip; });
  return '<div class="lst">' + kq.dong.map(function (r) {
    return '<div class="shi" data-kgdong="' + h(r[dau.k]) + '" style="display:flex;gap:10px;align-items:flex-start;padding:12px 14px;border-bottom:1px solid #f2f4f7">' +
      '<div style="flex:1;min-width:0">' +
      '<b style="font-size:14.5px">' + kgO(dau, r[dau.k], kq) + '</b>' +
      /* Bo o rong va o bang 0: dang the la de liec nhanh tren dien thoai,
         bay "Tre (ngay) 0" tren tung dong chi lam roi mat. Dang bang van
         hien du moi o de doi chieu. */
      '<div style="font-size:12px;color:#98a2b3;margin-top:2px">' +
        con.filter(function (c) {
          var v = r[c.k];
          if (v == null || v === '') return false;
          if (c.kieu === 'so' || c.kieu === 'tien' || c.kieu === 'phan_tram') return flt0(v) !== 0;
          return true;
        }).map(function (c) { return h(c.nhan) + ' ' + kgO(c, r[c.k], kq); }).join(' · ') + '</div>' +
      (cChip ? '<div style="font-size:12px;margin-top:3px">' + kgO(cChip, r[cChip.k], kq) + '</div>' : '') +
      '</div>' +
      (cTien ? '<b style="white-space:nowrap">' + kgO(cTien, r[cTien.k], kq) + '</b>' : '') +
      '</div>';
  }).join('') + '</div>';
}

function kgRong() {
  return '<div class="card"><div class="emp" style="padding:26px"><div class="e1">🫙</div><div>Không có dòng nào khớp bộ lọc này.</div></div></div>';
}

/* ---- man hinh ---- */
async function scrKhungDs() {
  var ma = kgMa, ts = kgTs(ma);
  frame('Danh sách', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc dữ liệu...</div></div>');
  var goi = { ma: ma };
  Object.keys(ts).forEach(function (k) {
    if (ts[k] !== '' && ts[k] != null) goi[k] = ts[k];
  });
  var kq;
  try { kq = await api('vagabond.khung.ds.chay', goi); }
  catch (e) {
    frame('Danh sách', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }

  var xem = kgXem[ma] || 'the';
  var html = kgTheTomTat(kq) +
    kgThanhLoc(kq) +
    kgHangChip(kq) +
    '<div class="card" style="padding:10px 12px">' + kmHangChip(
      posChipNut('data-kgxem="the"', '🗂️ Thẻ', xem === 'the') +
      posChipNut('data-kgxem="bang"', '📋 Bảng', xem === 'bang')
    ) + '</div>' +
    kgNhacCat(kq) +
    (xem === 'bang' ? kgVeBang(kq) : kgVeThe(kq)) +
    '<div style="text-align:center;color:#a0a6b4;font-size:11.5px;padding:9px 14px 60px;line-height:1.6">' +
      h(kq.ten) + ' · ' + (kq.tu ? h(kq.tu) + ' đến ' + h(kq.den) : 'tất cả các kỳ') +
      ' · màn này dựng từ khuôn dùng chung, số liệu do máy chủ cộng.</div>';

  /* Nút + góc phải, dùng đúng cơ chế fab có sẵn của khung app chứ không tự
     nhét một nút vào thân màn: nút trong thân màn sẽ cuộn theo nội dung,
     và mất hút ngay khi danh sách dài hơn một trang.

     Chỉ có nút khi máy chủ trả về khối `tao`, tức là tài khoản này thật sự
     được tạo mới ở danh mục đó. */
  var b = frame(kq.ten, html, kq.tao ? { fab: 1 } : undefined);
  var nTao = document.getElementById('vgbFab');
  if (nTao) {
    nTao.title = kq.tao.nhan;
    nTao.onclick = function () { kgMoTao(kq); };
  }
  b.onclick = function (e) {
    var t = e.target.closest('[data-kgchip]');
    if (t) { ts.chip = t.getAttribute('data-kgchip'); return go(scrKhungDs, true); }
    t = e.target.closest('[data-kgngay]');
    if (t) { ts.so_ngay = parseInt(t.getAttribute('data-kgngay'), 10); ts.tu = ''; ts.den = ''; return go(scrKhungDs, true); }
    t = e.target.closest('[data-kgxoangay]');
    if (t) { ts.tu = ''; ts.den = ''; return go(scrKhungDs, true); }
    t = e.target.closest('[data-kgxem]');
    if (t) { kgXem[ma] = t.getAttribute('data-kgxem'); return go(scrKhungDs, true); }
    t = e.target.closest('[data-kgco]');
    if (t) { var k = t.getAttribute('data-kgco'); ts[k] = ts[k] ? 0 : 1; return go(scrKhungDs, true); }
  };
  ['kgTu', 'kgDen'].forEach(function (id) {
    var o = document.getElementById(id);
    if (o) o.onchange = function () {
      ts.tu = (document.getElementById('kgTu') || {}).value || '';
      ts.den = (document.getElementById('kgDen') || {}).value || '';
      if (ts.tu && ts.den) go(scrKhungDs, true);
    };
  });
  Array.prototype.forEach.call(b.querySelectorAll('[data-kgtxt]'), function (o) {
    o.onchange = function () { ts[o.getAttribute('data-kgtxt')] = o.value; go(scrKhungDs, true); };
  });
}



/* ========== NÚT TẠO MỚI VÀ FORM NHẬP LIỆU DÙNG CHUNG ==========

Anh Việt 21/08/2026: *"Hiện tại App mới chỉ cho phép xem và tra cứu. Em hãy
thiết kế thêm nút Tạo mới (nổi bật, thường là nút + hoặc nút hành động ở góc
phải màn hình) trong tất cả các màn hình danh sách của phân hệ này... Xây
dựng Form nhập liệu (Form View) tương ứng... tối ưu với giao diện Mobile App."*

MỘT form cho cả mười ba danh mục, không phải mười ba màn chép tay. Máy chủ
khai ô nào thì màn dựng ô đó; thêm một danh mục về sau chỉ là thêm khai báo
bên Python, không đụng một dòng JavaScript nào.

Nút chỉ hiện khi MÁY CHỦ trả về khối `tao` - và máy chủ chỉ trả khi tài
khoản này thật sự được tạo. Bày ra một cái nút bấm vào báo lỗi quyền là một
cách nói dối nhẹ. */

var kgForm = null;   /* {ma, nhan, ghi_chu, o:[...], gt:{}} */

function kgMoTao(kq) {
  var t = kq.tao;
  if (!t) return;
  /* Danh mục có màn tạo riêng tốt hơn form chung thì dẫn sang màn đó. */
  if (t.di_toi) return vgbGo(t.di_toi);
  kgForm = { ma: kq.ma, nhan: t.nhan, ghi_chu: t.ghi_chu, o: t.o || [], gt: {} };
  (kgForm.o || []).forEach(function (c) {
    if (c.mac_dinh !== undefined && c.mac_dinh !== null) kgForm.gt[c.k] = c.mac_dinh;
  });
  go(scrKgTao);
}

function kgOVe(c, gt) {
  var v = gt[c.k];
  var id = 'kgo_' + c.k;
  var nhan = '<div class="vxl">' + h(c.nhan) + (c.bat_buoc ? ' <span style="color:#d92d20">*</span>' : '') + '</div>';
  var o = '';
  if (c.kieu === 'co') {
    return '<label style="display:flex;align-items:center;gap:11px;background:#fff;border-radius:12px;' +
      'padding:13px 14px;margin-top:12px"><input type="checkbox" id="' + id + '" data-kgo="' + h(c.k) + '"' +
      (v ? ' checked' : '') + ' style="width:22px;height:22px;flex:none">' +
      '<div style="flex:1;min-width:0"><div style="font-size:14.5px;font-weight:600;color:#101828">' +
      h(c.nhan) + '</div>' +
      (c.mo_ta ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:2px;line-height:1.5">' + h(c.mo_ta) + '</div>' : '') +
      '</div></label>';
  }
  if (c.kieu === 'chon') {
    o = '<select class="vxs" id="' + id + '" data-kgo="' + h(c.k) + '">' +
      (c.bat_buoc ? '' : '<option value="">- chưa chọn -</option>') +
      (c.chon || []).map(function (x) {
        return '<option value="' + h(x[0]) + '"' + (String(v) === String(x[0]) ? ' selected' : '') + '>' +
          h(x[1]) + '</option>';
      }).join('') + '</select>';
  } else if (c.kieu === 'lien_ket') {
    /* Ô liên kết: gõ chữ, máy chủ tra, chọn một dòng. Danh sách KHÔNG kéo
       hết về: doctype Customer của tiệm có 43.220 dòng. */
    o = '<input class="vxi" id="' + id + '" data-kglk="' + h(c.k) + '" autocomplete="off" ' +
      'placeholder="' + h(c.goi_y || 'Gõ vài chữ để tìm') + '" value="' + h(v == null ? '' : v) + '">' +
      '<div id="' + id + '_ds" style="display:none;background:#fff;border:1px solid #e4e7ec;border-radius:10px;' +
      'margin-top:4px;max-height:190px;overflow-y:auto"></div>';
  } else if (c.kieu === 'chu_dai') {
    o = '<textarea class="vxi" id="' + id + '" data-kgo="' + h(c.k) + '" rows="3" ' +
      'placeholder="' + h(c.goi_y || '') + '" style="font-family:inherit">' + h(v == null ? '' : v) + '</textarea>';
  } else {
    var so = (c.kieu === 'so' || c.kieu === 'tien');
    o = '<input class="vxi' + (c.kieu === 'tien' ? ' tien' : '') + '" id="' + id + '" data-kgo="' + h(c.k) + '"' +
      (c.kieu === 'ngay' ? ' type="date"' : '') +
      (so ? ' inputmode="decimal"' : '') +
      ' placeholder="' + h(c.goi_y || '') + '" value="' +
      h(v == null ? '' : (c.kieu === 'tien' ? tienChuoi(v) : v)) + '">';
  }
  return nhan + o +
    (c.mo_ta ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:5px;line-height:1.5">' + h(c.mo_ta) + '</div>' : '');
}

function scrKgTao() {
  var f = kgForm;
  if (!f) return go(scrKhungDs, true);
  var html = '<div class="vxf">' +
    (f.ghi_chu
      ? '<div style="font-size:12.5px;color:#92400e;background:#fffbeb;border:1px solid #fde68a;' +
        'border-radius:10px;padding:10px 12px;line-height:1.6">' + h(f.ghi_chu) + '</div>'
      : '') +
    f.o.map(function (c) { return kgOVe(c, f.gt); }).join('') +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:16px;line-height:1.6">' +
    'Ô có dấu <span style="color:#d92d20">*</span> là bắt buộc. Máy chủ kiểm lại ' +
    'một lần nữa trước khi ghi, nên điền thiếu thì nó nói rõ thiếu ô nào.</div>' +
    '</div>';

  var b = frame(f.nhan, html, {
    footer: '<button class="btn" id="kgLuu" style="margin:0">Lưu lại</button>'
  });

  b.querySelectorAll('[data-kgo]').forEach(function (n) {
    var k = n.getAttribute('data-kgo');
    var doc = function () {
      f.gt[k] = (n.type === 'checkbox') ? (n.checked ? 1 : 0)
        : (n.classList.contains('tien') ? soTien(n.value) : n.value);
    };
    n.onchange = doc;
    n.oninput = doc;
  });
  b.querySelectorAll('[data-kglk]').forEach(function (n) { kgGanLienKet(f, n); });

  document.getElementById('kgLuu').onclick = function () { kgGhi(f); };
}

/* Ô liên kết: gõ -> đợi 250ms -> hỏi máy chủ -> hiện danh sách -> bấm chọn.

   Đợi 250ms chứ không hỏi mỗi phím: gõ "Vinamilk" là tám lần hỏi, và tám
   câu trả lời về không đúng thứ tự thì ô hiện kết quả của chữ "Vinami". */
function kgGanLienKet(f, n) {
  var k = n.getAttribute('data-kglk');
  var oDs = document.getElementById('kgo_' + k + '_ds');
  var hen = null;
  function dong() { if (oDs) { oDs.style.display = 'none'; oDs.innerHTML = ''; } }
  n.oninput = function () {
    f.gt[k] = n.value;
    if (hen) clearTimeout(hen);
    hen = setTimeout(async function () {
      var r;
      try { r = await api('vagabond.khung.ds.tim_lien_ket', { ma: f.ma, o: k, tu_khoa: n.value }); }
      catch (e) { return dong(); }
      var ds = (r && r.ds) || [];
      if (!ds.length) {
        oDs.innerHTML = '<div style="padding:11px 13px;font-size:12.5px;color:#98a2b3">' +
          'Không có dòng nào khớp. Gõ ít chữ hơn thử xem.</div>';
        oDs.style.display = 'block';
        return;
      }
      oDs.innerHTML = ds.map(function (x) {
        return '<div data-kgpick="' + h(x.ma) + '" style="padding:11px 13px;font-size:13.5px;' +
          'border-bottom:1px solid #f2f4f7;cursor:pointer">' + h(x.ten) + '</div>';
      }).join('');
      oDs.style.display = 'block';
      oDs.querySelectorAll('[data-kgpick]').forEach(function (d) {
        d.onclick = function () {
          n.value = d.getAttribute('data-kgpick');
          f.gt[k] = n.value;
          dong();
        };
      });
    }, 250);
  };
  n.onblur = function () { setTimeout(dong, 220); };
}

async function kgGhi(f) {
  var thieu = f.o.filter(function (c) {
    return c.bat_buoc && !String(f.gt[c.k] == null ? '' : f.gt[c.k]).trim();
  });
  if (thieu.length) {
    return baoTin('Chưa điền: ' + thieu.map(function (c) { return c.nhan; }).join(', ') +
      '. Vui lòng điền đủ rồi bấm Lưu lại.', 'Thiếu thông tin');
  }
  busy(true);
  try {
    var r = await api('vagabond.khung.ds.tao_moi', { ma: f.ma, gt: JSON.stringify(f.gt) });
    busy(false);
    toast((r && r.loi_nhan) || 'Đã tạo xong.', 5000);
    kgForm = null;
    go(scrKhungDs, true);
  } catch (e) {
    busy(false);
    baoTin((e && e.message) || 'Chưa tạo được. Kiểm lại các ô rồi thử lần nữa.', 'Chưa lưu được');
  }
}

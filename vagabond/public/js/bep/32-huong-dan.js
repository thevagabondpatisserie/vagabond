/* ---------------- Huong dan che bien (anh Viet giao 25/08/2026)

   *"Em lam thanh 1 nut nho mang ten 'huong dan che bien' o ke ben moi BOM
   cua cac mon... cho cac ban bep truong nhap tren dien thoai de san xuat
   cho dung."*

   Doctype va ban in A4 da dung o v301. Phan con thieu la MAN HINH, va do
   la tep nay.

   BA QUYET DINH VE CACH DUNG MAN
   ------------------------------
   1. Vao tu THE CONG THUC chu khong phai tu mot muc rieng tren trang chu.
      Bep truong khong nghi "toi di soan huong dan", ho nghi "mon nay lam
      the nao". Nen nut nam ngay canh mon, dung cho anh Viet ve o vuong do.
      Man co dia chi rieng (`huong-dan-che-bien`) de luu dau trang duoc,
      nhung duong vao chinh van la the cong thuc.

   2. SOAN TRUC TIEP, khong sheet long nhau. Bep truong go tren dien thoai
      mot tay, moi lan mo them mot lop la mot lan mat cho dang go. Nen moi
      thu nam tren MOT trang cuon, dong con thi la the co nut xoa.

   3. VE LAI CANG IT CANG TOT. O go ghi thang vao `hdE`, khong ve lai sau
      moi phim. Chi ve lai khi them hay bot dong, tuc luc cau truc doi.
      Ve lai giua chung la mat con tro va mat ca dong dang go do.

   Tien to hd = huong dan. Da kiem va cham ten truoc khi dat (QT-28). */

var hdE = null;      /* ban dang soan */
var hdMa = '';       /* ma mon dang soan */
var hdTen = '';      /* ten mon, chi de hien tieu de */

var HD_TT = ['Nháp', 'Đang dùng', 'Ngừng dùng'];
var HD_MAU_TT = { 'Nháp': 'w', 'Đang dùng': 'g', 'Ngừng dùng': 'n' };
var HD_TOI_HAN = [['', 'Bước thường'], ['OPRP', 'OPRP'], ['CCP', 'CCP']];

function hdSuaDuoc() {
  return hasRole('Manufacturing Manager') || hasRole('System Manager') ||
    hasRole('Giám đốc') || hasRole('AP Giám đốc') || hasRole('Bếp phó');
}

/* Chuoi rong an toan cho thuoc tinh value cua the input. */
function hdV(x) { return h(x == null ? '' : x); }

/* Mot o nhap co nhan, ghi thang vao doi tuong khi go. */
function hdO(nhan, khoa, gt, kieu, goiY) {
  return '<label class="hd-o"><span>' + h(nhan) + '</span>' +
    '<input class="tin hd-in" data-k="' + h(khoa) + '" type="' + (kieu || 'text') +
    '" value="' + hdV(gt) + '" placeholder="' + h(goiY || '') + '"></label>';
}

function hdODai(nhan, khoa, gt, goiY, dong) {
  return '<label class="hd-o"><span>' + h(nhan) + '</span>' +
    '<textarea class="nt hd-in" data-k="' + h(khoa) + '" rows="' + (dong || 3) +
    '" placeholder="' + h(goiY || '') + '">' + hdV(gt) + '</textarea></label>';
}

/* ------------------------------------------------------ danh sach */

async function scrHuongDan() {
  frame('Hướng dẫn chế biến', '<div class="emp"><div class="e1">⏳</div></div>');
  var r;
  try { r = await api('vagabond.huong_dan_che_bien.danh_sach', { gioi_han: 200 }); }
  catch (e) {
    frame('Hướng dẫn chế biến',
      '<div class="emp"><div class="e1">🔒</div><div>' + h(errMsg(e)) + '</div></div>');
    return;
  }
  var ds = (r && r.danh_sach) || [];
  var chuaCo = (r && r.so_mon_chua_co) || 0;

  var body = '';
  if (chuaCo) {
    body += '<div class="card" style="padding:12px 14px;font-size:13.5px;line-height:1.5">' +
      '📋 Còn <b>' + chuaCo + '</b> món có công thức mà chưa có hướng dẫn. ' +
      'Mở Danh mục công thức, bấm nút 📖 trên thẻ của món để soạn.</div>';
  }
  body += ds.length
    ? '<div class="sec">Đã soạn</div><div class="lst">' + ds.map(function (x) {
      return '<div class="li" data-m="' + h(x.ma_mon) + '"><div class="lt">' +
        '<div class="l1">' + h(x.ten_mon || x.ma_mon) + '</div>' +
        '<div class="l2">' + h(x.ma_mon) + ' · ' + (x.so_buoc || 0) + ' bước' +
        (x.cong_thuc_da_doi ? ' · ⚠️ công thức đã đổi' : '') + '</div></div>' +
        '<div style="text-align:right"><div class="st ' + (HD_MAU_TT[x.trang_thai] || 'n') + '">' +
        h(x.trang_thai || '') + '</div></div></div>';
    }).join('') + '</div>'
    : '<div class="emp"><div class="e1">📖</div><div class="e2">Chưa có hướng dẫn nào</div></div>';

  var b = frame('Hướng dẫn chế biến', body);
  b.onclick = function (e) {
    var t = e.target.closest('[data-m]');
    if (t) { var m = t.dataset.m; return go(function () { scrHuongDanSoan(m, ''); }); }
  };
}

/* ------------------------------------------------------ trinh soan */

async function scrHuongDanSoan(maMon, tenMon) {
  hdMa = maMon;
  hdTen = tenMon || maMon;
  frame('Hướng dẫn chế biến', '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api('vagabond.huong_dan_che_bien.chi_tiet', { ma_mon: maMon }); }
  catch (e) {
    frame('Hướng dẫn chế biến',
      '<div class="emp"><div class="e1">🔒</div><div>' + h(errMsg(e)) + '</div></div>');
    return;
  }
  if (d && d.chua_co) {
    hdE = {
      name: '', ma_mon: maMon, trang_thai: 'Nháp',
      me_chuan: '', dvt_me: '', nang_suat: '', hao_hut_cho_phep: '',
      tg_chuan_bi: '', tg_lam: '', tg_nghi: '', dung_cu: '',
      dinh_luong: [], buoc: [], tieu_chi: [],
      di_ung: '', han_su_dung: '', bao_quan: '', ghi_chu: '',
      anh_dat_chinh: '', bom_soan_theo: '', moi: 1
    };
  } else {
    hdE = d;
    hdE.moi = 0;
    hdTen = d.ten_mon || hdTen;
    ['dinh_luong', 'buoc', 'tieu_chi'].forEach(function (k) {
      if (!hdE[k]) hdE[k] = [];
    });
  }
  hdVe();
}

function hdVe() {
  var d = hdE;
  var sua = hdSuaDuoc();
  var html = '';

  /* --- dau bai --- */
  html += '<div class="card"><div class="kpg">' +
    '<div style="font-size:18px;font-weight:700;line-height:1.3">' + h(hdTen) + '</div>' +
    '<div style="font-size:12.5px;color:#8a8f9c;margin-top:5px">' + h(d.ma_mon) +
    (d.name ? ' · bản ' + (d.phien_ban || 1) : ' · chưa soạn') + '</div></div>';
  if (d.cong_thuc_da_doi) {
    html += '<div style="margin:0 14px 12px;padding:10px 12px;border-radius:9px;' +
      'background:#fff4e5;color:#7a4a00;font-size:13px;line-height:1.5">' +
      '⚠️ Công thức của món này đã đổi sau khi soạn hướng dẫn. Soát lại định lượng ' +
      'rồi lưu để gỡ cảnh báo.</div>';
  }
  html += '<div class="chips" style="padding:0 12px 12px">' + HD_TT.map(function (t) {
    return '<div class="chip' + (d.trang_thai === t ? ' on' : '') + '" data-tt="' + h(t) + '">' + h(t) + '</div>';
  }).join('') + '</div></div>';

  /* --- me va thoi gian --- */
  html += '<div class="sec">Mẻ chuẩn và thời gian</div><div class="card hd-form">' +
    '<div class="row2">' + hdO('Mẻ chuẩn', 'me_chuan', d.me_chuan, 'number') +
    hdO('Đơn vị mẻ', 'dvt_me', d.dvt_me, 'text', 'Gram') + '</div>' +
    hdO('Ra bao nhiêu thành phẩm', 'nang_suat', d.nang_suat, 'text', 'vd: 2 khuôn 18cm') +
    '<div class="row2">' + hdO('Chuẩn bị (phút)', 'tg_chuan_bi', d.tg_chuan_bi, 'number') +
    hdO('Làm (phút)', 'tg_lam', d.tg_lam, 'number') + '</div>' +
    '<div class="row2">' + hdO('Nghỉ, ủ, đông (phút)', 'tg_nghi', d.tg_nghi, 'number') +
    hdO('Hao hụt cho phép (%)', 'hao_hut_cho_phep', d.hao_hut_cho_phep, 'number') + '</div>' +
    hdODai('Dụng cụ và thiết bị cần', 'dung_cu', d.dung_cu, 'vd: máy đánh trứng, khuôn 18cm, lò 170 độ', 2) +
    '</div>';

  /* --- dinh luong --- */
  html += '<div class="sec">Định lượng</div>';
  html += '<div class="card" style="padding:10px 12px">' +
    '<button class="btn gh" id="hdNapBom" style="font-size:13.5px">⬇️ Nạp từ công thức đang dùng</button>' +
    '<div style="font-size:12px;color:#98a2b3;margin-top:7px;line-height:1.5">' +
    'Kéo nguyên liệu, số lượng và cột Note từ công thức sang. Nạp lại sẽ thay ' +
    'toàn bộ danh sách bên dưới.</div></div>';
  html += '<div class="lst hd-bang">' + (d.dinh_luong || []).map(function (x, i) {
    return '<div class="card hd-dong hd-form" data-b="dinh_luong" data-i="' + i + '">' +
      '<div class="hd-so">Nguyên liệu ' + (i + 1) +
      '<button class="hd-xoa" data-xoa>✕</button></div>' +
      '<div class="row2">' + hdO('Tên nguyên liệu', 'ten', x.ten) +
      hdO('Mã hàng', 'ma_hang', x.ma_hang, 'text', 'không bắt buộc') + '</div>' +
      '<div class="row2">' + hdO('Số lượng', 'so_luong', x.so_luong, 'number') +
      hdO('Đơn vị', 'dvt', x.dvt) + '</div>' +
      '<div class="row2">' + hdO('Tách từ', 'tach_tu', x.tach_tu, 'text', 'vd: từ 3 quả trứng') +
      hdO('Ghi chú', 'ghi_chu', x.ghi_chu, 'text', 'vd: nguyên quả') + '</div></div>';
  }).join('') + '</div>' +
    '<button class="btn gh" data-them="dinh_luong" style="margin:0 0 4px">➕ Thêm nguyên liệu</button>';

  /* --- cac buoc --- */
  html += '<div class="sec">Các bước làm</div>';
  html += '<div class="lst hd-bang">' + (d.buoc || []).map(function (x, i) {
    return '<div class="card hd-dong hd-form" data-b="buoc" data-i="' + i + '">' +
      '<div class="hd-so">Bước ' + (i + 1) +
      '<button class="hd-xoa" data-xoa>✕</button></div>' +
      hdO('Công đoạn', 'cong_doan', x.cong_doan, 'text', 'vd: Đánh bông lòng trắng') +
      hdODai('Cách làm', 'mo_ta', x.mo_ta, 'Viết như đang cầm tay chỉ việc', 3) +
      '<div class="row2">' + hdO('Thời gian (phút)', 'thoi_gian_phut', x.thoi_gian_phut, 'number') +
      hdO('Nhiệt độ', 'nhiet_do', x.nhiet_do, 'text', 'vd: 170 độ C') + '</div>' +
      hdO('Thông số', 'thong_so', x.thong_so, 'text', 'vd: tốc độ 6, chóp mềm') +
      '<div class="hd-o"><span>Điểm tới hạn</span><div class="chips">' +
      HD_TOI_HAN.map(function (c) {
        return '<div class="chip' + ((x.diem_toi_han || '') === c[0] ? ' on' : '') +
          '" data-th="' + h(c[0]) + '" data-thi="' + i + '">' + h(c[1]) + '</div>';
      }).join('') + '</div></div>' +
      ((x.diem_toi_han || '') ? hdO('Biểu mẫu phải ghi', 'bieu_mau', x.bieu_mau, 'text', 'vd: Sổ theo dõi nhiệt lò') : '') +
      '</div>';
  }).join('') + '</div>' +
    '<button class="btn gh" data-them="buoc" style="margin:0 0 4px">➕ Thêm bước</button>';

  /* --- tieu chi QC --- */
  html += '<div class="sec">Tiêu chí QC</div>';
  html += '<div class="card" style="padding:10px 12px">' +
    (d.anh_dat_chinh
      ? '<img src="' + h(d.anh_dat_chinh) + '" style="width:100%;border-radius:9px;display:block">'
      : '<div style="text-align:center;color:#98a2b3;font-size:13px;padding:14px 0">Chưa có ảnh món đạt</div>') +
    '<button class="btn gh" id="hdAnh" style="margin-top:9px;font-size:13.5px">📷 ' +
    (d.anh_dat_chinh ? 'Chụp lại ảnh món đạt' : 'Chụp ảnh món đạt') + '</button></div>';
  html += '<div class="lst hd-bang">' + (d.tieu_chi || []).map(function (x, i) {
    return '<div class="card hd-dong hd-form" data-b="tieu_chi" data-i="' + i + '">' +
      '<div class="hd-so">Tiêu chí ' + (i + 1) +
      '<button class="hd-xoa" data-xoa>✕</button></div>' +
      hdO('Tiêu chí', 'tieu_chi', x.tieu_chi, 'text', 'vd: Màu ruột bánh') +
      hdODai('Đạt khi', 'dat_khi', x.dat_khi, '', 2) +
      hdODai('Không đạt khi', 'khong_dat_khi', x.khong_dat_khi, '', 2) +
      hdODai('Không đạt thì làm gì', 'xu_ly', x.xu_ly, '', 2) + '</div>';
  }).join('') + '</div>' +
    '<button class="btn gh" data-them="tieu_chi" style="margin:0 0 4px">➕ Thêm tiêu chí</button>';

  /* --- an toan --- */
  html += '<div class="sec">Dị ứng và bảo quản</div><div class="card hd-form">' +
    '<div class="chips" style="margin-bottom:8px">' +
    ((d.goi_y_di_ung || []).map(function (g) {
      return '<div class="chip" data-du="' + h(g) + '">+ ' + h(g) + '</div>';
    }).join('')) + '</div>' +
    hdODai('Cảnh báo dị ứng', 'di_ung', d.di_ung, 'Nhóm nguyên liệu gây dị ứng có trong món', 2) +
    hdO('Hạn sử dụng', 'han_su_dung', d.han_su_dung, 'text', 'vd: 3 ngày kể từ ngày làm') +
    hdODai('Điều kiện bảo quản', 'bao_quan', d.bao_quan, 'vd: mát 4 độ, đậy kín', 2) +
    hdODai('Ghi chú', 'ghi_chu', d.ghi_chu, '', 2) + '</div>';

  var nut = '';
  if (sua) {
    nut = '<div class="row2"><button class="btn gh" id="hdIn">🖨️ In A4</button>' +
      '<button class="btn" id="hdLuu">💾 Lưu</button></div>';
  } else if (d.name) {
    nut = '<button class="btn gh" id="hdIn">🖨️ In A4</button>';
  }

  var b = frame('Hướng dẫn chế biến', html, nut ? { footer: nut } : {});
  hdGan(b);
}

/* ------------------------------------------------------ gan su kien */

function hdGan(b) {
  /* O go: ghi thang vao hdE, KHONG ve lai. Ve lai la mat con tro. */
  var os = b.querySelectorAll('.hd-in');
  for (var i = 0; i < os.length; i++) {
    (function (o) {
      o.oninput = function () {
        var khoa = o.dataset.k;
        var dong = o.closest('[data-b]');
        if (dong) {
          var bang = dong.dataset.b, vt = parseInt(dong.dataset.i, 10);
          if (hdE[bang] && hdE[bang][vt]) hdE[bang][vt][khoa] = o.value;
        } else {
          hdE[khoa] = o.value;
        }
      };
    })(os[i]);
  }

  b.onclick = function (e) {
    var tt = e.target.closest('[data-tt]');
    if (tt) { hdE.trang_thai = tt.dataset.tt; return hdVe(); }

    var th = e.target.closest('[data-th]');
    if (th) {
      var vt = parseInt(th.dataset.thi, 10);
      if (hdE.buoc && hdE.buoc[vt]) hdE.buoc[vt].diem_toi_han = th.dataset.th;
      return hdVe();
    }

    var du = e.target.closest('[data-du]');
    if (du) {
      var cu = String(hdE.di_ung || '').trim();
      var them = du.dataset.du;
      if (cu.indexOf(them) < 0) hdE.di_ung = cu ? cu + ', ' + them : them;
      return hdVe();
    }

    var xoa = e.target.closest('[data-xoa]');
    if (xoa) {
      var d2 = xoa.closest('[data-b]');
      if (d2) hdE[d2.dataset.b].splice(parseInt(d2.dataset.i, 10), 1);
      return hdVe();
    }

    var them2 = e.target.closest('[data-them]');
    if (them2) {
      var bang = them2.dataset.them;
      if (!hdE[bang]) hdE[bang] = [];
      hdE[bang].push({});
      return hdVe();
    }
  };

  var np = document.getElementById('hdNapBom');
  if (np) np.onclick = hdNapTuBom;
  var lu = document.getElementById('hdLuu');
  if (lu) lu.onclick = hdLuu;
  var inn = document.getElementById('hdIn');
  if (inn) inn.onclick = hdIn;
  var an = document.getElementById('hdAnh');
  if (an) an.onclick = hdChupAnhDat;
}

/* ------------------------------------------------------ hanh dong */

async function hdNapTuBom() {
  busy(1);
  var ds;
  try {
    ds = await api('vagabond.cong_thuc.danh_sach',
      { tim: hdE.ma_mon, trang_thai: 'dang_dung' });
  } catch (e) { busy(0); return toast(errMsg(e), 6000); }
  var khop = ((ds && ds.ds) || []).filter(function (x) { return x.ma === hdE.ma_mon; });
  if (!khop.length) {
    busy(0);
    return toast('Món này chưa có công thức nào đang dùng để nạp.', 6000);
  }
  var ct;
  try { ct = await api('vagabond.cong_thuc.chi_tiet', { name: khop[0].bom }); }
  catch (e) { busy(0); return toast(errMsg(e), 6000); }
  busy(0);
  if (!await confirmSheet('Nạp từ công thức ' + khop[0].bom + '?',
    'Sẽ thay toàn bộ phần Định lượng bằng ' + ct.dong.length + ' dòng của công thức này. ' +
    'Phần các bước và tiêu chí QC không bị đụng tới.', 'Nạp')) return;
  hdE.dinh_luong = ct.dong.map(function (m) {
    return {
      ma_hang: m.ma, ten: m.ten || m.ma, so_luong: m.sl,
      dvt: m.dvt || '', tach_tu: '', ghi_chu: m.note || ''
    };
  });
  hdE.bom_soan_theo = ct.bom;
  if (!hdE.me_chuan) { hdE.me_chuan = ct.so_luong; hdE.dvt_me = ct.dvt || ''; }
  hdVe();
  toast('Đã nạp ' + hdE.dinh_luong.length + ' dòng định lượng.', 4000);
}

async function hdLuu() {
  busy(1);
  var r;
  try {
    r = await api('vagabond.huong_dan_che_bien.luu', { du_lieu: JSON.stringify(hdE) });
  } catch (e) { busy(0); return toast(errMsg(e), 8000); }
  busy(0);
  hdE.name = r.name;
  hdE.phien_ban = r.phien_ban;
  hdE.moi = 0;
  hdE.cong_thuc_da_doi = 0;
  toast('Đã lưu bản ' + r.phien_ban + '.', 4000);
  hdVe();
}

function hdIn() {
  if (!hdE.name) return toast('Lưu lại một lần rồi mới in được.', 5000);
  var u = '/printview?doctype=' + encodeURIComponent('Vagabond Huong Dan Che Bien') +
    '&name=' + encodeURIComponent(hdE.name) +
    '&format=' + encodeURIComponent('Vagabond - Hướng dẫn chế biến') +
    '&no_letterhead=0&trigger_print=1';
  window.open(u, '_blank');
}

function hdChupAnhDat() {
  if (!hdE.name) return toast('Lưu lại một lần rồi mới đính ảnh được.', 5000);
  vdChupAnh(function (blob) {
    vdUpload(blob, 'Vagabond Huong Dan Che Bien', hdE.name, 'anh_dat_chinh')
      .then(function (url) {
        busy(0);
        hdE.anh_dat_chinh = url;
        hdVe();
        toast('Đã lưu ảnh món đạt.', 4000);
      })
      .catch(function (e) { busy(0); toast(errMsg(e), 6000); });
  });
}

/* ---------------- Don tiec / B2B (anh Viet duyet 25/08/2026)

   Lam theo don, KHONG dinh muc. Goi tiec khong co ma thanh pham co dinh
   va khong co BOM tinh, nen luong nay KHONG di qua Lenh san xuat.

   Doanh thu di truoc, gia von di sau, hai duong doc lap. Cai duy nhat
   noi hai duong lai la mot du an chung, va do la thu man nay dung nen.
   Doc ban thiet ke o project doc thiet-ke-b2b-tiec-lam-theo-don.md.

   BA CHO CAN CAN THAN TREN MAN NAY
   --------------------------------
   1. Nut "Ghi so phieu xuat" GHI THANG vao so kho VA so cai. Khong co
      nut hoan tac. Nen no phai hoi lai, va phai noi ro se ghi bao nhieu
      dong vao kho nao.

   2. DON VI la don vi KHO cua mat hang, hien to canh o nhap. Bep can
      bang gam; mat hang nao khai don vi kho la Kg ma bep go 12000 thi
      thanh 12 tan. Man phai hien don vi ro rang de bep tu thay.

   3. O tim dung lai `xuat_kho.tim_hang` chu khong viet cua tim thu hai.
      Ham do CHI liet ke ma con ton that trong kho do va tra kem gia von.
      Viet cua tim rieng chi de hai cho lech nhau.

   Tien to tc = tiec. Da kiem va cham ten truoc khi dat (QT-28). */

var tcD = { ds: null, tong: 0, loc: 'sap_toi' };
var tcX = null;   /* phieu xuat dang soan */

var TC_LOC = [
  ['sap_toi', 'Sắp tới'],
  ['tuan_nay', 'Tuần này'],
  ['tat_ca', 'Tất cả']
];

var TC_ICON = {
  'Event - Catering': '🎂', 'Teabreak': '🥐',
  'Bánh thiết kế': '🎨', 'B2B sỉ': '📦'
};

/* KHONG co ham tcXuatDuoc() o day, va do la co y.

   Chep danh sach vai vao day la dung mot ban sao thu hai cua
   `xuat_kho.VAI_XUAT`. Hom nao ben Python them hay bot mot vai thi ban
   sao nay lech, va man hinh se hien nut cho nguoi khong bam duoc, hoac
   giau nut khoi nguoi bam duoc. May chu tra thang co `duoc_xuat` trong
   `chi_tiet_tiec`, man hinh chi viec nghe theo. */

function tcNgayISO(d) {
  return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) +
    '-' + ('0' + d.getDate()).slice(-2);
}

/* Khoang ngay cua tung chip loc. Tra ve null nghia la khong gioi han. */
function tcKhoang() {
  if (tcD.loc === 'tat_ca') return { tu: null, den: null };
  if (tcD.loc === 'tuan_nay') {
    var n = new Date();
    /* Tuan bat dau tu THU HAI. getDay() tra 0 cho Chu nhat, nen Chu nhat
       phai lui 6 ngay chu khong phai lui 0. */
    var thu = n.getDay() === 0 ? 7 : n.getDay();
    var dau = new Date(n); dau.setDate(n.getDate() - (thu - 1));
    var cuoi = new Date(dau); cuoi.setDate(dau.getDate() + 6);
    return { tu: tcNgayISO(dau), den: tcNgayISO(cuoi) };
  }
  return { tu: null, den: null };   /* sap toi: may chu tu lay tu hom nay */
}

/* ------------------------------------------------------ danh sach */

async function tcTai() {
  var k = tcKhoang();
  var r = await api('vagabond.tiec.don_tiec',
    { tu_ngay: k.tu, den_ngay: k.den, trang_thai: tcD.loc === 'tat_ca' ? '' : null });
  tcD.ds = (r && r.ds) || [];
  tcD.tong = (r && r.tong) || 0;
}

async function scrDonTiec() {
  /* Danh muc kho phai co truoc: man xuat kho ben duoi doc thang tu S.wh,
     ma S.wh chi duoc nap mot lan trong ca phien. Thieu buoc nay thi vao
     thang bang dia chi /don-tiec se ra o chon kho rong tron. */
  await loadMasters();
  if (tcD.ds === null) {
    frame('Đơn tiệc / B2B', '<div class="emp"><div class="e1">⏳</div></div>');
    try { await tcTai(); }
    catch (e) {
      frame('Đơn tiệc / B2B',
        '<div class="emp"><div class="e1">🔒</div><div>' + h(errMsg(e)) + '</div></div>');
      return;
    }
  }
  var chips = TC_LOC.map(function (c) {
    return '<div class="chip' + (tcD.loc === c[0] ? ' on' : '') +
      '" data-l="' + c[0] + '">' + c[1] + '</div>';
  }).join('');

  var body = '<div class="chips">' + chips + '</div>' +
    (tcD.ds.length ? '<div class="lst">' + tcD.ds.map(function (x) {
      var icon = TC_ICON[x.loai] || '🍽️';
      return '<div class="li" data-t="' + h(x.hop_dong) + '"><div class="lt">' +
        '<div class="l1">' + icon + ' ' + h(x.ten) + '</div>' +
        '<div class="l2">' + h(x.loai || '') +
        (x.khach ? ' · ' + h(x.khach) : '') + '</div>' +
        '<div class="l2">' +
        (x.gio_giao ? 'Giao ' + h(x.gio_giao) + ' · ' : '') +
        h(x.dia_diem || '') + '</div>' +
        '<div class="l2" style="margin-top:3px">' +
        (x.so_lan_xuat
          ? '<b style="color:#0b6bcb">đã xuất NVL ' + x.so_lan_xuat + ' lần</b>'
          : '<b style="color:#8a5a00">chưa xuất NVL</b>') + '</div></div>' +
        '<div style="text-align:right"><div class="amt">' + money(x.gia_tri) + '</div>' +
        '<div class="l2" style="margin-top:4px">' + h(dmy(x.ngay_su_kien)) + '</div></div></div>';
    }).join('') + '</div>'
      : '<div class="emp"><div class="e1">🍽️</div><div class="e2">' +
        'Không có đơn tiệc nào đang thực hiện trong khoảng này</div></div>');

  var b = frame('Đơn tiệc / B2B', body);
  b.onclick = function (e) {
    var l = e.target.closest('[data-l]');
    if (l) { tcD.loc = l.dataset.l; tcD.ds = null; return scrDonTiec(); }
    var t = e.target.closest('[data-t]');
    if (t) { var hd = t.dataset.t; return go(function () { scrTiecXem(hd); }); }
  };
}

/* ------------------------------------------------------ chi tiet */

async function scrTiecXem(hopDong) {
  frame('Đơn tiệc', '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api('vagabond.tiec.chi_tiet_tiec', { hop_dong: hopDong }); }
  catch (e) {
    frame('Đơn tiệc',
      '<div class="emp"><div class="e1">🔒</div><div>' + h(errMsg(e)) + '</div></div>');
    return;
  }

  var html = '<div class="card"><div class="kpg">' +
    '<div style="font-size:18px;font-weight:700;line-height:1.3">' + h(d.ten) + '</div>' +
    '<div style="font-size:12.5px;color:#8a8f9c;margin-top:5px">' +
    h(d.loai || '') + (d.so_hop_dong ? ' · ' + h(d.so_hop_dong) : '') +
    ' · ' + h(d.hop_dong) + '</div></div>' +
    '<div class="stk">' +
    '<div><div class="s1">Ngày sự kiện</div><div class="s2">' + h(dmy(d.ngay_su_kien)) + '</div></div>' +
    '<div><div class="s1">Giao lúc</div><div class="s2">' + h(d.gio_giao || '-') + '</div></div>' +
    '<div><div class="s1">Giá trị</div><div class="s2">' + money(d.gia_tri) + '</div></div></div>';
  if (d.khach || d.dia_diem) {
    html += '<div style="padding:0 14px 12px;font-size:13px;color:#5a6070;line-height:1.6">' +
      (d.khach ? '👤 ' + h(d.khach) + '<br>' : '') +
      (d.dia_diem ? '📍 ' + h(d.dia_diem) : '') + '</div>';
  }
  html += '</div>';

  if (d.mo_ta) {
    html += '<div class="sec">Thực đơn</div>' +
      '<div class="card" style="padding:12px 14px;font-size:14px;line-height:1.8;white-space:pre-line">' +
      h(d.mo_ta) + '</div>';
  }

  html += '<div class="sec">Đã xuất nguyên liệu' +
    (d.tong_da_xuat ? ' · tổng ' + money(d.tong_da_xuat) : '') + '</div>';
  html += d.phieu.length
    ? d.phieu.map(function (p) {
      return '<div class="card" style="padding:12px 14px;margin-bottom:9px">' +
        '<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px">' +
        '<div><div style="font-weight:600;font-size:13.5px">' + h(p.phieu) + '</div>' +
        '<div class="l2">' + h(dmy(p.ngay)) + (p.gio ? ' · ' + h(p.gio) : '') +
        (p.da_ghi_so ? '' : ' · <b style="color:#b3261e">đã huỷ</b>') + '</div></div>' +
        '<div style="text-align:right;white-space:nowrap">' +
        '<div class="amt">' + money(p.gia_tri) + '</div>' +
        (p.da_ghi_so && d.duoc_xuat
          ? '<button class="tc-huy" data-huy="' + h(p.phieu) + '">✕ Huỷ</button>'
          : '') + '</div></div>' +
        '<div style="margin-top:8px;font-size:13px;line-height:1.7;color:#5a6070">' +
        p.dong.map(function (m) {
          return h(m.ten) + ' &middot; <b>' + num(m.sl) + ' ' + h(m.dvt) + '</b>' +
            (m.ghi_chu ? ' <i style="color:#8a8f9c">(' + h(m.ghi_chu) + ')</i>' : '');
        }).join('<br>') + '</div></div>';
    }).join('')
    : '<div class="card" style="padding:16px 14px;text-align:center;color:#98a2b3;font-size:13.5px">' +
      'Chưa xuất nguyên liệu lần nào cho tiệc này</div>';

  var nut = d.duoc_xuat
    ? '<button class="btn" id="tcXuat">➕ Xuất kho nguyên liệu</button>'
    : '';
  var b = frame('Đơn tiệc', html, nut ? { footer: nut } : {});

  b.onclick = function (e) {
    var hy = e.target.closest('[data-huy]');
    if (hy) return tcHuyPhieu(hy.dataset.huy, d.hop_dong);
  };
  var x = document.getElementById('tcXuat');
  if (x) x.onclick = function () { tcMoXuat(d); };
}

async function tcHuyPhieu(phieu, hopDong) {
  /* Phieu nay da vao so kho va so cai. Huy la dao nguoc but toan, nen
     bat go LY DO chu khong chi hoi co hay khong. */
  var ly = await promptSheet('Huỷ phiếu ' + phieu + '?',
    'Gõ lý do huỷ. Phiếu đã ghi vào sổ kho và sổ cái, huỷ sẽ đảo ngược bút toán.');
  if (ly === null) return;
  if (!ly) return toast('Phải ghi lý do huỷ.', 5000);
  busy(1);
  try {
    var r = await api('vagabond.tiec.huy_xuat_nvl', { phieu: phieu, ly_do: ly });
    busy(0);
    toast(r.ghi_chu, 6000);
  } catch (e) { busy(0); return toast(errMsg(e), 8000); }
  tcD.ds = null;
  go(function () { scrTiecXem(hopDong); }, true);
}

/* ------------------------------------------------------ form xuat kho */

function tcMoXuat(d) {
  tcX = { hop_dong: d.hop_dong, ten: d.ten, kho: '', dong: [], tim: '', ket: [] };
  try { tcX.kho = localStorage.getItem('vgb_tiec_kho') || ''; } catch (e) { }
  if (S.wh.indexOf(tcX.kho) < 0) tcX.kho = '';
  go(scrTiecXuat);
}

function scrTiecXuat() {
  var d = tcX;

  function draw() {
    var html = '<div class="card" style="padding:12px 14px">' +
      '<div class="l2" style="margin-bottom:6px">Xuất cho tiệc</div>' +
      '<div style="font-weight:700;font-size:15px;margin-bottom:10px">' + h(d.ten) + '</div>' +
      '<div class="hd-o"><span>Kho xuất</span>' +
      '<select class="tin" id="tcKho" style="width:100%;text-align:left;font-size:15px;padding:0 12px">' +
      '<option value="">Chọn kho</option>' +
      S.wh.map(function (w) {
        return '<option value="' + h(w) + '"' + (d.kho === w ? ' selected' : '') + '>' + h(w) + '</option>';
      }).join('') + '</select></div></div>';

    if (!d.kho) {
      html += '<div class="emp"><div class="e1">🏬</div>' +
        '<div class="e2">Chọn kho xuất trước, rồi mới tìm được nguyên liệu</div></div>';
    } else {
      html += '<div class="card" style="padding:12px 14px">' +
        '<input class="tin" id="tcTim" placeholder="Tìm tên hoặc mã nguyên liệu" ' +
        'value="' + h(d.tim) + '" style="text-align:left;font-size:14.5px;padding:0 13px;width:100%">' +
        '<div style="font-size:12px;color:#98a2b3;margin-top:7px;line-height:1.5">' +
        'Chỉ hiện mã còn tồn thật trong kho này.</div></div>';
      if (d.ket.length) {
        html += '<div class="lst">' + d.ket.map(function (k) {
          return '<div class="li" data-add="' + h(k.ma) + '"><div class="lt">' +
            '<div class="l1">' + h(k.ten || k.ma) + '</div>' +
            '<div class="l2">' + h(k.ma) + ' · tồn ' + num(k.ton) + ' ' + h(k.dvt) + '</div></div>' +
            '<div style="text-align:right"><div class="ct-hd">➕ Thêm</div></div></div>';
        }).join('') + '</div>';
      }
    }

    html += '<div class="sec">Dòng sẽ xuất</div>';
    html += d.dong.length
      ? '<div class="lst hd-bang">' + d.dong.map(function (m, i) {
        return '<div class="card hd-dong hd-form" data-i="' + i + '">' +
          '<div class="hd-so">' + h(m.ten || m.ma) +
          '<button class="hd-xoa" data-xoa>✕</button></div>' +
          '<div class="l2" style="margin-bottom:8px">' + h(m.ma) +
          ' · tồn ' + num(m.ton) + ' ' + h(m.dvt) + '</div>' +
          '<div class="row2">' +
          '<label class="hd-o"><span>Số lượng (' + h(m.dvt) + ')</span>' +
          '<input class="tin tc-sl" type="number" inputmode="decimal" ' +
          'value="' + (m.sl === '' ? '' : h(m.sl)) + '"></label>' +
          '<label class="hd-o"><span>Ghi chú</span>' +
          '<input class="tin tc-gc" value="' + h(m.ghi_chu || '') + '" ' +
          'placeholder="vd: đợt 1"></label></div>' +
          (m.sl > m.ton
            ? '<div style="color:#b3261e;font-size:12.5px;line-height:1.5">' +
              '⚠️ Gõ nhiều hơn tồn kho. Kiểm lại đơn vị: mặt hàng này tính bằng ' +
              h(m.dvt) + '.</div>'
            : '') + '</div>';
      }).join('') + '</div>'
      : '<div class="card" style="padding:16px 14px;text-align:center;color:#98a2b3;font-size:13.5px">' +
        'Chưa thêm nguyên liệu nào</div>';

    var nut = '<button class="btn" id="tcGhi">✅ Ghi sổ phiếu xuất</button>';
    var b = frame('Xuất NVL cho tiệc', html, { footer: nut });
    gan(b);
  }

  function gan(b) {
    var kho = document.getElementById('tcKho');
    if (kho) kho.onchange = function () {
      d.kho = kho.value;
      try { localStorage.setItem('vgb_tiec_kho', d.kho); } catch (e) { }
      /* Doi kho thi ton cua cac dong da them khong con dung nua. Bo het
         di con an toan hon la de lai con so cu ma bep tuong la that. */
      d.dong = []; d.ket = []; d.tim = '';
      draw();
    };

    /* O go so luong va ghi chu: ghi THANG vao tcX, khong ve lai. Ve lai
       giua chung la mat con tro va mat ca dong dang go do. */
    var sls = b.querySelectorAll('.tc-sl');
    for (var i = 0; i < sls.length; i++) {
      (function (o) {
        o.oninput = function () {
          var r = o.closest('[data-i]');
          if (r) d.dong[parseInt(r.dataset.i, 10)].sl = o.value === '' ? '' : parseFloat(o.value);
        };
      })(sls[i]);
    }
    var gcs = b.querySelectorAll('.tc-gc');
    for (var j = 0; j < gcs.length; j++) {
      (function (o) {
        o.oninput = function () {
          var r = o.closest('[data-i]');
          if (r) d.dong[parseInt(r.dataset.i, 10)].ghi_chu = o.value;
        };
      })(gcs[j]);
    }

    b.onclick = function (e) {
      var ad = e.target.closest('[data-add]');
      if (ad) {
        var ma = ad.dataset.add;
        var k = d.ket.filter(function (x) { return x.ma === ma; })[0];
        if (!k) return;
        /* Them cung mot ma hai lan la chuyen thuong (bo dot 1, dot 2).
           Cu them dong moi; may chu se cong don lai khi dung phieu. */
        d.dong.push({ ma: k.ma, ten: k.ten, dvt: k.dvt, ton: k.ton, sl: '', ghi_chu: '' });
        return draw();
      }
      var xo = e.target.closest('[data-xoa]');
      if (xo) {
        var r = xo.closest('[data-i]');
        if (r) d.dong.splice(parseInt(r.dataset.i, 10), 1);
        return draw();
      }
    };

    var ti = document.getElementById('tcTim');
    if (ti) {
      var cho = null;
      ti.oninput = function () {
        d.tim = ti.value;
        if (cho) clearTimeout(cho);
        cho = setTimeout(async function () {
          try {
            d.ket = await api('vagabond.xuat_kho.tim_hang',
              { kho: d.kho, tu_khoa: d.tim, gioi_han: 30 }) || [];
          } catch (e) { d.ket = []; }
          var giu = document.activeElement === ti;
          var vt = ti.selectionStart;
          draw();
          if (giu) {
            var t2 = document.getElementById('tcTim');
            if (t2) { t2.focus(); try { t2.setSelectionRange(vt, vt); } catch (e) { } }
          }
        }, 420);
      };
    }

    var gh = document.getElementById('tcGhi');
    if (gh) gh.onclick = tcGhiSo;
  }

  draw();
}

async function tcGhiSo() {
  var d = tcX;
  var sach = d.dong.filter(function (m) { return (parseFloat(m.sl) || 0) > 0; });
  if (!d.kho) return toast('Chưa chọn kho xuất.', 5000);
  if (!sach.length) return toast('Chưa có dòng nào có số lượng lớn hơn 0.', 5000);

  var qua = sach.filter(function (m) { return m.sl > m.ton; });
  if (qua.length) {
    var ok = await confirmSheet('Có dòng gõ nhiều hơn tồn kho',
      qua.map(function (m) {
        return m.ten + ': gõ ' + num(m.sl) + ' ' + m.dvt + ', tồn ' + num(m.ton) + ' ' + m.dvt;
      }).join('\n') +
      '\n\nKiểm lại đơn vị trước khi ghi sổ. Bếp cân bằng gam mà mặt hàng khai ' +
      'đơn vị kho là Kg thì con số lệch một nghìn lần.', 'Vẫn ghi sổ', true);
    if (!ok) return;
  }

  if (!await confirmSheet('Ghi sổ phiếu xuất?',
    'Sẽ xuất ' + sach.length + ' dòng nguyên liệu khỏi kho ' + d.kho +
    ' cho tiệc ' + d.ten + '.\n\nPhiếu ghi thẳng vào sổ kho và sổ cái. ' +
    'Ghi nhầm thì phải huỷ phiếu chứ không sửa được.', 'Ghi sổ')) return;

  busy(1);
  var r;
  try {
    r = await api('vagabond.tiec.xuat_nvl', {
      hop_dong: d.hop_dong, kho: d.kho,
      dong: JSON.stringify(sach.map(function (m) {
        return { ma: m.ma, sl: m.sl, ghi_chu: m.ghi_chu || '' };
      }))
    });
  } catch (e) { busy(0); return toast(errMsg(e), 9000); }
  busy(0);
  toast(r.ghi_chu, 7000);
  tcD.ds = null;
  var hd = d.hop_dong;
  tcX = null;
  go(function () { scrTiecXem(hd); }, true);
}

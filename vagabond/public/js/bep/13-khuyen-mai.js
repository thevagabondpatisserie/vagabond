/* ---------- Khuyen mai tren man tinh tien (anh Viet 11/08/2026) ----------

Cashier chon chuong trinh, bam combo, hoac go ma voucher. So tien giam
KHONG do may khach tu tinh: moi lan gio hang doi la goi may chu tinh lai.
Lam vay vi hai le:
  - so tren man hinh va so tren bill khong bao gio lech nhau
  - khong ai mo Devtools tu ha bill cua minh xuong duoc

Combo bam vao thi RA NGAY thanh tung mon thanh phan do vao gio (anh Viet
chot). Bill in ra chi thay ten mon that, khong in ma combo. */

function posKmChuKy() {
  return (posDon.mon || []).map(function (m) { return m.item_code + ':' + m.qty + ':' + m.rate; }).join('|') +
    '#' + (posDon.ctkm || []).join(',') +
    '#' + (posDon.combo || []).map(function (c) { return c.ma + 'x' + c.so_bo; }).join(',') +
    '#' + (posDon.maVc || '') +
    '#' + ((posDon.khach_no && posDon.khach_no.ma) || posDon.khach_ma || '') + '#' + (posDon.sdt || '');
}

async function posTinhKm() {
  var coGi = (posDon.ctkm && posDon.ctkm.length) || (posDon.combo && posDon.combo.length) || posDon.maVc;
  if (!coGi || !(posDon.mon || []).length) { posDon.kmKq = null; return; }
  var ck = posKmChuKy();
  if (posDon.kmKq && posDon.kmKq.ck === ck) return;
  try {
    var kq = await api('vagabond.khuyen_mai.xem_truoc', {
      items: JSON.stringify(posDon.mon.map(function (m) { return { item_code: m.item_code, qty: m.qty, rate: m.rate }; })),
      ctkm: JSON.stringify(posDon.ctkm || []),
      combo: JSON.stringify(posDon.combo || []),
      ma: posDon.maVc || '',
      quay: (posQuay && posQuay.ma) || '',
      nguon: posNguonThuc(),
      khach: (posDon.khach_no && posDon.khach_no.ma) || posDon.khach_ma || '',
      sdt: posDon.sdt || ''
    });
    kq.ck = ck;
    posDon.kmKq = kq;
  } catch (e) {
    /* Ma voucher hong thi go han ra khoi bill, khong de ket man hinh. */
    posDon.kmKq = null;
    posDon.maVc = '';
    toast((e && e.message) || 'Không tính được khuyến mãi', 4200);
  }
}

function posKhoiKm() {
  var kq = posDon.kmKq;
  var html = '<div><div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:7px">' +
    '<span style="font-size:12.5px;color:#6b7280;font-weight:600">KHUYẾN MÃI</span></div>' +
    '<div style="display:flex;flex-wrap:wrap;gap:7px;margin-bottom:8px">' +
    posChipNut('id="posKmChon"', '🎫 Chương trình', false) +
    /* KHONG co chip Combo o day nua (anh Viet 11/08/2026): combo la thu
       cashier chon LUC KHACH ORDER, nen no phai nam trong o "Them mon"
       cung cho voi mon binh thuong, khong phai o duoi khoi thanh toan. */
    posChipNut('id="posKmMa"', posDon.maVc ? '🎟 ' + h(posDon.maVc) : '🎟 Nhập mã', !!posDon.maVc) +
    '</div>';

  if (kq && (kq.ap || []).length) {
    html += '<div style="background:#f0fdfa;border:1.5px solid #7fe5f6;border-radius:9px;padding:9px 11px;margin-bottom:7px">';
    (kq.ap || []).forEach(function (a) {
      html += '<div style="display:flex;align-items:flex-start;gap:6px;padding:3px 0;font-size:13px">' +
        '<span style="flex:1;min-width:0">' + (a.loai === 'combo' ? '🧺 ' : '🎫 ') + '<b>' + h(a.ten) + '</b>' +
        (a.dien_giai ? '<div style="font-size:11.5px;color:#0b7c93;margin-top:1px">' + h(a.dien_giai) + '</div>' : '') + '</span>' +
        '<b style="flex:none;color:#0f766e">−' + money(a.giam) + ' đ</b>' +
        '<button data-kmbo="' + h(a.ma) + '" data-l="' + h(a.loai) + '" style="flex:none;border:0;background:transparent;color:#b3261e;font-size:15px;cursor:pointer;padding:0 2px">✕</button></div>';
    });
    html += '</div>';
  }
  if (kq && (kq.bo || []).length) {
    html += '<div style="background:#fff7ed;border:1.5px solid #fed7aa;border-radius:9px;padding:9px 11px;margin-bottom:7px;font-size:12px;color:#9a3412;line-height:1.6">' +
      (kq.bo || []).map(function (b) { return '<b>' + h(b.ten) + '</b>: ' + h(b.ly_do); }).join('<br>') + '</div>';
  }
  if (kq && (kq.them_mon || []).length) {
    html += '<div style="background:#fef3c7;border:1.5px solid #fcd34d;border-radius:9px;padding:9px 11px;margin-bottom:7px;font-size:12.5px;color:#92400e;line-height:1.6">' +
      'Khách được tặng ' + (kq.them_mon || []).map(function (t) { return '<b>' + num(t.qty) + '× ' + h(t.item_code) + '</b>'; }).join(', ') +
      ' nhưng chưa có trong đơn.<br>' +
      posChipNut('id="posKmThemTang"', '+ Thêm món tặng vào đơn', false) + '</div>';
  }
  if (kq && kq.can_otp) {
    html += '<div style="background:#fef2f2;border:1.5px solid #fecaca;border-radius:9px;padding:9px 11px;margin-bottom:7px;font-size:12.5px;color:#b3261e;line-height:1.6">' +
      '🔐 Chương trình này cần mã OTP của quản lý. Lúc bấm Thu tiền máy sẽ hỏi mã.</div>';
  }
  html += '</div>';
  return html;
}

function posNoiKm() {
  var n = document.getElementById('posKmChon');
  if (n) n.onclick = function () { posDoc(); posSheetChonKm(); };
  n = document.getElementById('posKmMa');
  if (n) n.onclick = function () { posDoc(); posSheetMaVc(); };
  n = document.getElementById('posKmThemTang');
  if (n) n.onclick = function () {
    posDoc();
    ((posDon.kmKq && posDon.kmKq.them_mon) || []).forEach(function (t) {
      var i = -1;
      posDon.mon.forEach(function (m, k) { if (m.item_code === t.item_code) i = k; });
      if (i >= 0) posDon.mon[i].qty += t.qty;
      else posDon.mon.push({ item_code: t.item_code, ten: t.item_code, qty: t.qty, rate: t.rate, anh: '', nhom: '', tc: [], gc: '' });
    });
    posDon.kmKq = null;
    go(scrPosQuay, true);
  };
  var b = document.getElementById('vgbBody');
  if (b) b.addEventListener('click', function (e) {
    var t = e.target.closest('[data-kmbo]');
    if (!t) return;
    posDoc();
    var ma = t.getAttribute('data-kmbo');
    if (t.getAttribute('data-l') === 'combo') {
      posDon.combo = (posDon.combo || []).filter(function (c) { return c.ma !== ma; });
    } else {
      posDon.ctkm = (posDon.ctkm || []).filter(function (c) { return c !== ma; });
      /* Chuong trinh nay den tu ma voucher thi go luon ma. */
      if (posDon.kmKq) {
        (posDon.kmKq.ap || []).forEach(function (a) { if (a.ma === ma && a.voucher) posDon.maVc = ''; });
      }
    }
    posDon.kmKq = null;
    go(scrPosQuay, true);
  });
}

async function posSheetChonKm() {
  busy(true);
  var kq;
  try {
    kq = await api('vagabond.khuyen_mai.ds_ctkm', {
      quay: (posQuay && posQuay.ma) || '', nguon: posNguonThuc(),
      khach: (posDon.khach_no && posDon.khach_no.ma) || posDon.khach_ma || '', sdt: posDon.sdt || ''
    });
  } catch (e) { busy(false); return toast((e && e.message) || 'Không tải được chương trình'); }
  busy(false);
  /* Chuong trinh phat ma dung mot lan thi phai go ma, khong bam chon
     thang duoc - khong thi ma xuat cho doi tac thanh vo nghia. */
  var ds = ((kq && kq.km) || []).filter(function (x) { return x.cach_ma !== 'Ma dung mot lan'; });
  if (!ds.length) return toast('Chưa có chương trình khuyến mãi nào đang bật cho quầy này.', 4500);

  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  function ve() {
    var html = '<div class="shh"><b>Chương trình khuyến mãi</b><div class="x">&times;</div></div>' +
      '<div style="padding:4px 14px calc(env(safe-area-inset-bottom,0px) + 14px);max-height:74vh;overflow:auto">';
    ds.forEach(function (x) {
      var chon = (posDon.ctkm || []).indexOf(x.name) >= 0;
      html += '<div data-kmc="' + h(x.name) + '" style="display:flex;align-items:center;gap:10px;padding:11px 0;border-bottom:1px solid #f6f7f9;cursor:' + (x.dung_duoc ? 'pointer' : 'default') + ';opacity:' + (x.dung_duoc ? '1' : '.55') + '">' +
        '<span style="width:34px;height:34px;flex:none;border-radius:9px;background:' + (chon ? '#0d9488' : '#f0fdfa') + ';color:' + (chon ? '#fff' : '#0f766e') + ';display:flex;align-items:center;justify-content:center;font-size:17px">' + (chon ? '✓' : '🎫') + '</span>' +
        '<div style="flex:1;min-width:0"><div style="font-size:14.5px;font-weight:600">' + h(x.ten) + '</div>' +
        '<div style="font-size:12px;color:#98a2b3;margin-top:2px">' + h(x.nhan_cach || '') + ' · ' + kmMucGiam(x) +
        (x.can_otp ? ' · 🔐 cần OTP' : '') + '</div>' +
        (x.dung_duoc ? '' : '<div style="font-size:11.5px;color:#9a3412;margin-top:3px">Không áp được lúc này: ' + h(x.ly_do) + '</div>') +
        '</div></div>';
    });
    html += '<button class="btn" id="kmXong" style="width:100%;margin-top:12px">Xong</button></div>';
    box.innerHTML = html;
    box.querySelector('.x').onclick = dong;
    box.querySelector('#kmXong').onclick = dong;
    box.querySelectorAll('[data-kmc]').forEach(function (o) {
      o.onclick = function () {
        var ma = o.getAttribute('data-kmc');
        var x = ds.filter(function (y) { return y.name === ma; })[0] || {};
        if (!x.dung_duoc) return toast(x.ly_do || 'Chương trình không áp được lúc này', 3800);
        posDon.ctkm = posDon.ctkm || [];
        var i = posDon.ctkm.indexOf(ma);
        if (i >= 0) posDon.ctkm.splice(i, 1); else posDon.ctkm.push(ma);
        posDon.kmKq = null;
        ve();
      };
    });
  }
  function dong() { ov.remove(); go(scrPosQuay, true); }
  ve();
  ov.appendChild(box);
  ov.onclick = function (e) { if (e.target === ov) dong(); };
  document.body.appendChild(ov);
}

async function posSheetCombo() {
  busy(true);
  var kq;
  try { kq = await api('vagabond.khuyen_mai.ds_combo', { quay: (posQuay && posQuay.ma) || '', nguon: posNguonThuc() }); }
  catch (e) { busy(false); return toast((e && e.message) || 'Không tải được combo'); }
  busy(false);
  var ds = (kq && kq.combo) || [];
  if (!ds.length) return toast('Chưa có combo nào đang bật cho quầy này.', 4500);

  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  var html = '<div class="shh"><b>Combo</b><div class="x">&times;</div></div>' +
    '<div style="padding:4px 14px calc(env(safe-area-inset-bottom,0px) + 14px);max-height:74vh;overflow:auto">' +
    '<div style="font-size:12px;color:#6b7280;margin-bottom:10px;line-height:1.6">Bấm một combo là máy tự đổ các món thành phần vào hoá đơn rồi trừ tiền bên dưới. Bill in ra chỉ thấy tên món thật.</div>';
  ds.forEach(function (x) {
    var mon = comboMoTa(x);
    html += '<div data-cbc="' + h(x.name) + '" style="display:flex;align-items:center;gap:10px;padding:11px 0;border-bottom:1px solid #f6f7f9;cursor:pointer;opacity:' + (x.dung_duoc ? '1' : '.55') + '">' +
      '<span style="width:34px;height:34px;flex:none;border-radius:9px;background:#f0fdfa;display:flex;align-items:center;justify-content:center;font-size:17px">🧺</span>' +
      '<div style="flex:1;min-width:0"><div style="font-size:14.5px;font-weight:600">' + h(x.ten) + '</div>' +
      '<div style="font-size:12px;color:#98a2b3;margin-top:2px">' + mon + '</div>' +
      '<div style="font-size:12px;color:#0f766e;margin-top:2px"><s style="color:#c3c8d4">' + money(x.gia_goc) + 'đ</s> → <b>' + money(x.gia_combo) + 'đ</b> · tiết kiệm ' + (x.co_nhom ? 'từ ' : '') + money(x.tiet_kiem) + 'đ</div>' +
      (x.dung_duoc ? '' : '<div style="font-size:11.5px;color:#9a3412;margin-top:3px">' + h(x.ly_do) + '</div>') +
      '</div><span style="color:#c3c8d4;font-size:18px">›</span></div>';
  });
  html += '</div>';
  box.innerHTML = html;
  box.querySelector('.x').onclick = function () { ov.remove(); };
  box.querySelectorAll('[data-cbc]').forEach(function (o) {
    o.onclick = async function () {
      var ma = o.getAttribute('data-cbc');
      var x = ds.filter(function (y) { return y.name === ma; })[0] || {};
      if (!x.dung_duoc) return toast(x.ly_do || 'Combo không bán được lúc này', 3800);
      ov.remove();
      if (x.co_nhom) {
        posSheetChonCombo(x, function (chon) { posThemCombo(x, chon); go(scrPosQuay, true); });
        return;
      }
      posThemCombo(x);
      go(scrPosQuay, true);
    };
  });
  ov.appendChild(box);
  ov.onclick = function (e) { if (e.target === ov) ov.remove(); };
  document.body.appendChild(ov);
}

function posSheetMaVc() {
  var ov = document.createElement('div'); ov.className = 'sh';
  ov.innerHTML = '<div class="shb" style="padding:18px 16px calc(env(safe-area-inset-bottom,0px) + 16px)">' +
    '<div style="font-size:17.5px;font-weight:700;margin-bottom:4px">Mã ưu đãi của khách</div>' +
    '<div style="font-size:12.5px;color:#6b7280;margin-bottom:12px;line-height:1.6">Khách đọc mã, thu ngân gõ vào đây. Máy tự kiểm mã còn hạn không, đã ai dùng chưa.</div>' +
    '<input class="nt" id="vcO" placeholder="Ví dụ K7M2QP" autocapitalize="characters" style="text-transform:uppercase;letter-spacing:2px;font-size:18px;text-align:center" value="' + h(posDon.maVc || '') + '">' +
    '<div id="vcBao" style="font-size:12.5px;color:#b3261e;margin-top:8px;min-height:18px"></div>' +
    '<button class="btn" data-y style="margin-top:6px">Áp mã</button>' +
    (posDon.maVc ? '<button class="btn gh" data-x style="margin-top:9px">Bỏ mã đang dùng</button>' : '') +
    '<button class="btn gh" data-n style="margin-top:9px">Đóng</button></div>';
  document.body.appendChild(ov);
  var o = ov.querySelector('#vcO');
  setTimeout(function () { o.focus(); }, 120);
  async function ap() {
    var ma = (o.value || '').trim().toUpperCase();
    var bao = ov.querySelector('#vcBao');
    if (!ma) { bao.textContent = 'Chưa nhập mã.'; return; }
    bao.style.color = '#6b7280'; bao.textContent = 'Đang kiểm mã...';
    try {
      var kq = await api('vagabond.khuyen_mai.tra_ma', {
        ma: ma, quay: (posQuay && posQuay.ma) || '', nguon: posNguonThuc()
      });
      if (!kq.dung_duoc) { bao.style.color = '#b3261e'; bao.textContent = kq.ly_do || 'Mã không dùng được lúc này.'; return; }
      posDon.maVc = ma;
      posDon.kmKq = null;
      ov.remove();
      toast('Đã áp mã ' + ma + ' · ' + kq.ten);
      go(scrPosQuay, true);
    } catch (e) {
      bao.style.color = '#b3261e';
      bao.textContent = (e && e.message) || 'Mã không dùng được.';
    }
  }
  o.onkeydown = function (e) { if (e.key === 'Enter') ap(); };
  ov.onclick = function (e) {
    if (e.target === ov || e.target.hasAttribute('data-n')) return ov.remove();
    if (e.target.hasAttribute('data-x')) { posDon.maVc = ''; posDon.kmKq = null; ov.remove(); return go(scrPosQuay, true); }
    if (e.target.hasAttribute('data-y')) ap();
  };
}

/* O tim khach tren man tinh tien: go la xo danh sach, bam mot dong la gan
   ho so khach vao hoa don. Gan ho so khach KHONG phai chuyen sang ban cong
   no - no chi de biet khach nay la ai, hang gi, de ap dung chuong trinh
   khuyen mai theo hang va de cham soc sau nay (anh Viet 11/08/2026). */
var posTreTim = null;
function posNoiTimKhach() {
  var o = document.getElementById('posTen');
  var hop = document.getElementById('posTenGoi');
  if (!o || !hop) return;
  var nBo = document.getElementById('posBoKhach');
  if (nBo) nBo.onclick = async function () {
    posDoc();
    /* Bo khach thi phai bo luon ve tru diem: ve gan voi MOT khach cu the,
       de lai thi may chu se tu choi luc chot bill va thu ngan khong hieu
       vi sao. */
    if (posDon.diemVe || posDon.diemPhien) {
      var ve = (posDon.diemVe && posDon.diemVe.ve) || (posDon.diemPhien && posDon.diemPhien.phien);
      try { await api('vagabond.diem_otp.bo_ve', { phien: ve }); } catch (e) { }
    }
    posDiemDat();
    posDon.khach_ma = ''; posDon.khach_hang = '';
    posDon.kmKq = null;
    go(scrPosQuay, true);
  };
  function dong() { hop.innerHTML = ''; }
  /* Hop goi y phai NOI TREN mat kinh chu khong nam trong the .card: CSS cua
     app dat .card{overflow:hidden} nen danh sach dai bi cat cut, tren dien
     thoai gan nhu khong thay gi (anh Viet 12/08/2026 - "vẫn chưa xổ ra danh
     sách"). Dung position:fixed va tu tinh toa do theo o nhap. */
  function neo(el) {
    var r = o.getBoundingClientRect();
    var duoi = window.innerHeight - r.bottom;
    el.style.position = 'fixed';
    el.style.left = r.left + 'px';
    el.style.width = r.width + 'px';
    el.style.zIndex = '2147483000';
    if (duoi < 190 && r.top > duoi) {
      el.style.bottom = (window.innerHeight - r.top + 4) + 'px';
      el.style.maxHeight = Math.max(140, r.top - 60) + 'px';
    } else {
      el.style.top = (r.bottom + 4) + 'px';
      el.style.maxHeight = Math.max(140, duoi - 16) + 'px';
    }
  }
  function ve(ds) {
    if (!ds.length) {
      hop.innerHTML = '<div style="background:#fff;border:1.5px solid #e5e7eb;border-radius:10px;padding:11px 13px;font-size:13px;color:#98a2b3;box-shadow:0 6px 18px rgba(16,24,40,.12)">Không có khách nào khớp. Cứ gõ tên tự do cũng được.</div>';
      neo(hop.firstElementChild);
      return;
    }
    hop.innerHTML = '<div style="overflow:auto;background:#fff;border:1.5px solid #7fe5f6;border-radius:10px;box-shadow:0 6px 18px rgba(16,24,40,.12)">' +
      ds.slice(0, 25).map(function (k) {
        return '<div data-kchon="' + h(k.name) + '" style="padding:10px 12px;border-bottom:1px solid #f6f7f9;cursor:pointer">' +
          '<div style="font-size:14px;font-weight:600">' + h(k.customer_name || k.name) + '</div>' +
          '<div style="font-size:11.5px;color:#98a2b3">' + h(k.name) +
          (k.mobile_no ? ' · ' + h(k.mobile_no) : '') +
          (k.tax_id ? ' · MST ' + h(k.tax_id) : '') +
          (k.customer_group ? ' · ' + h(k.customer_group) : '') + '</div></div>';
      }).join('') + '</div>';
    neo(hop.firstElementChild);
    hop.querySelectorAll('[data-kchon]').forEach(function (el) {
      el.onclick = async function () {
        var ma = el.getAttribute('data-kchon');
        var k = ds.filter(function (x) { return x.name === ma; })[0] || {};
        posDoc();
        posDiemDat();
        posDon.khach_ma = ma;
        posDon.ten = k.customer_name || ma;
        if (k.mobile_no && !posDon.sdt) posDon.sdt = k.mobile_no;
        posDon.kmKq = null;
        dong();
        try {
          var tt = await api('vagabond.cong_no.thong_tin_xhd', { khach: ma });
          if (tt && tt.mst) {
            posDon.xhd_mo = true;
            posDon.xh = { mst: tt.mst || '', ten: tt.ten || '', dc: tt.dia_chi || '', email: tt.email || '' };
          }
        } catch (e) { }
        go(scrPosQuay, true);
      };
    });
  }
  async function tim(q) {
    try {
      var kq = await api('vagabond.cong_no.tim_khach', { tu_khoa: q });
      ve((kq && kq.khach) || []);
    } catch (e) { dong(); }
  }
  o.oninput = function () {
    if (posTreTim) clearTimeout(posTreTim);
    var q = o.value.trim();
    /* Mot ky tu cung tim: khach hay dat ten goi nho rat ngan ("Ry", "An"),
       bat tu hai ky tu la go mai khong thay gi. */
    if (!q) { return tim(''); }
    posTreTim = setTimeout(function () { tim(q); }, 260);
  };
  /* Bam vao o la xo luon danh sach khach gan day, khoi phai nho ten. */
  o.onfocus = function () { tim(o.value.trim()); };
  o.onblur = function () { setTimeout(dong, 220); };
}

/* Chuong trinh nao bat buoc OTP quan ly thi hoi ma ngay truoc khi luu.
   Sep tu thao tac thi may chu cho qua, khoi nhap. */
async function posXinOtpKm() {
  if (!(posDon.kmKq && posDon.kmKq.can_otp)) return '';
  var ma = await promptSheet('Khuyến mãi này cần mã OTP của quản lý', 'Nhập 6 số quản lý đọc cho');
  return (ma || '').replace(/\D/g, '');
}

/* ---------- Chuong trinh khuyen mai va combo (anh Viet 11/08/2026) ----------

Bay cach thuc anh Viet liet ke deu cau hinh duoc ngay tren app, khong phai
mo Desk. Man nay chia bon the:
  - Chuong trinh: bay cach thuc, thoi gian, doi tuong, kenh ban, han muc
  - Combo: phoi mon thanh goi; luc tinh tien may RA thanh mon thanh phan
  - Ma voucher: hai cach phat ma (co dinh cho cashier chon, hoac xuat lo
    ma 6 ky tu gui qua email cho doi tac)
  - Bao cao: tien da giam, xep hang thu ngan - de SOI ai giam bat thuong

MOI NUT DEU LA CHIP theo y anh Viet 09/08/2026. */

var kmThe = 'ct', kmLocCt = '', kmData = null, kmSua = null, kmDm = null;

/* Chip nhieu lua chon tren mot truong dang "moi dong mot gia tri". Tra ve
   HTML hang chip; nguoi dung bam chip nao thi them hoac bo dong do. */
function kmChipNhieu(thuoc, ds, giaTri) {
  var da = String(giaTri || '').split('\n').map(function (s) { return s.trim(); }).filter(Boolean);
  if (!ds || !ds.length) return '<div style="font-size:11.5px;color:#98a2b3;margin-bottom:10px">Danh mục đang trống.</div>';
  return '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px">' +
    ds.map(function (x) {
      var ma = typeof x === 'string' ? x : x.ma;
      var ten = typeof x === 'string' ? x : x.ten;
      return posChipNut(thuoc + '="' + h(ma) + '"', h(ten), da.indexOf(ma) >= 0);
    }).join('') + '</div>';
}

/* Bam mot chip nhieu lua chon: co roi thi bo ra, chua co thi them vao. */
function kmDoiDong(giaTri, ma) {
  var da = String(giaTri || '').split('\n').map(function (s) { return s.trim(); }).filter(Boolean);
  var i = da.indexOf(ma);
  if (i >= 0) da.splice(i, 1); else da.push(ma);
  return da.join('\n');
}

/* Ba diem ban. Don Sales online khong mang ma quay nen quy uoc la SALES,
   may chu cung hieu quy uoc nay (khuyen_mai._hop_kenh). */
var KM_QUAY = [
  { ma: 'SALES', ten: 'Sales Online' },
  { ma: 'TCV', ten: 'District 1' },
  { ma: 'NVHTN', ten: 'NVHTN' }
];

var KM_CACH = [
  { k: 'Giam tong hoa don', nhan: 'Giảm tổng hoá đơn', ic: '🧾', mo: 'Giảm % hoặc số tiền trên cả hoá đơn' },
  { k: 'Giam gia mon', nhan: 'Giảm giá món', ic: '🍰', mo: 'Chỉ giảm trên món hoặc nhóm món chỉ định' },
  { k: 'Mua A giam B', nhan: 'Mua A giảm B', ic: '🔁', mo: 'Mua đủ món điều kiện thì món ưu đãi được giảm' },
  { k: 'Mua X tang Y', nhan: 'Mua X tặng Y', ic: '🎁', mo: 'Mua 2 tặng 1, mua 3 tặng 1...' },
  { k: 'Tang mon', nhan: 'Tặng món', ic: '🍬', mo: 'Đạt điều kiện thì tặng hẳn một món' },
  { k: 'Dong gia', nhan: 'Đồng giá', ic: '🏷️', mo: 'Kéo món về một mức giá cố định' },
  { k: 'Giam luy ke', nhan: 'Giảm luỹ kế', ic: '📈', mo: 'Bậc thang: hoá đơn càng lớn giảm càng sâu' }
];
function kmNhanCach(k) {
  for (var i = 0; i < KM_CACH.length; i++) if (KM_CACH[i].k === k) return KM_CACH[i];
  return { k: k, nhan: k, ic: '🎫', mo: '' };
}

/* Bootstrap cua Frappe dat .card{display:flex;flex-direction:column} nen chip
   nhet thang vao .card se xep DOC va gian het be ngang (bat duoc khi nghiem
   thu v107). Luon boc chip trong mot lop div rieng. */
function kmHangChip(noiDung) {
  return '<div style="display:flex;flex-direction:row;flex-wrap:wrap;gap:7px">' + noiDung + '</div>';
}

function kmTheChip(t, nhan) { return posChipNut('data-kmthe="' + t + '"', nhan, kmThe === t); }

async function scrKhuyenMai() {
  frame('Khuyến mãi - combo', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc chương trình...</div></div>');
  var ct, cb;
  try {
    ct = await api('vagabond.khuyen_mai.ds_ctkm', { tat_ca: 1 });
    cb = await api('vagabond.khuyen_mai.ds_combo', { tat_ca: 1 });
    /* Hang khach, nhom khach, nhom mon va quay lay tu may de bay ra thanh
       chip cho bam, khoi go tay (anh Viet 12/08/2026). */
    if (!kmDm) { try { kmDm = await api('vagabond.khuyen_mai.danh_muc', {}); } catch (e2) { kmDm = null; } }
  } catch (e) {
    frame('Khuyến mãi - combo', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>');
    return;
  }
  kmData = { ct: (ct && ct.km) || [], cb: (cb && cb.combo) || [] };
  var dsCt = kmData.ct, dsCb = kmData.cb;
  var dangBat = dsCt.filter(function (x) { return x.bat; }).length;
  var cbBat = dsCb.filter(function (x) { return x.bat; }).length;

  var html = '<div class="card" style="padding:12px 14px;display:flex;flex-direction:row;gap:10px">' +
    '<div style="flex:1"><div style="font-size:12px;color:#98a2b3">CHƯƠNG TRÌNH</div>' +
    '<div style="font-size:19px;font-weight:800">' + dangBat + ' đang chạy</div>' +
    '<div style="font-size:12px;color:#98a2b3">' + dsCt.length + ' chương trình đã cấu hình</div></div>' +
    '<div style="flex:1;border-left:1px solid #eef0f4;padding-left:10px"><div style="font-size:12px;color:#98a2b3">COMBO</div>' +
    '<div style="font-size:19px;font-weight:800;color:#0f766e">' + cbBat + ' đang bán</div>' +
    '<div style="font-size:12px;color:#98a2b3">' + dsCb.length + ' combo đã phối</div></div></div>';

  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
    kmTheChip('ct', '🎫 Tạo voucher') + kmTheChip('cb', '🧺 Combo') +
    kmTheChip('lo', '📮 Xuất danh sách mã voucher') + kmTheChip('bc', '📊 Báo cáo')) + '</div>';

  if (kmThe === 'ct') html += kmHtmlCt(dsCt);
  else if (kmThe === 'cb') html += kmHtmlCb(dsCb);
  else if (kmThe === 'lo') html += '<div class="card" id="kmLoBox" style="padding:6px 14px"><div class="emp" style="padding:22px"><div class="e1">⏳</div><div>Đang đọc lô mã...</div></div></div>';
  else html += '<div class="card" id="kmBcBox" style="padding:6px 14px"><div class="emp" style="padding:22px"><div class="e1">⏳</div><div>Đang cộng sổ...</div></div></div>';

  var b = frame('Khuyến mãi - combo', html, {
    fab: (kmThe === 'ct' || kmThe === 'cb'),
    onFab: function () { kmThe === 'cb' ? kmSheetCombo(null) : kmSheetCtkm(null); }
  });

  if (kmThe === 'lo') kmVeLo();
  if (kmThe === 'bc') kmVeBaoCao();

  b.onclick = function (e) {
    var t = e.target.closest('[data-kmthe]');
    if (t) { kmThe = t.getAttribute('data-kmthe'); return go(scrKhuyenMai, true); }
    t = e.target.closest('[data-kmloc]');
    if (t) { kmLocCt = t.getAttribute('data-kmloc'); return go(scrKhuyenMai, true); }
    t = e.target.closest('[data-kmbat]');
    if (t) return kmBatTat(t.getAttribute('data-kmbat'), t.getAttribute('data-loai'));
    t = e.target.closest('[data-kmx]');
    if (t) return kmSheetCtkm(t.getAttribute('data-kmx'));
    t = e.target.closest('[data-kmcb]');
    if (t) return kmSheetCombo(t.getAttribute('data-kmcb'));
    t = e.target.closest('[data-kmxlo]');
    if (t) return kmSheetXuatLo(t.getAttribute('data-kmxlo'));
    t = e.target.closest('[data-kmlo]');
    if (t) return kmSheetLo(t.getAttribute('data-kmlo'));
    t = e.target.closest('[data-kmgui]');
    if (t) return kmGuiLai(t.getAttribute('data-kmgui'));
  };
}

/* --- the Chuong trinh --- */
function kmHtmlCt(ds) {
  var LOC = [{ k: '', nhan: 'Tất cả' }, { k: 'bat', nhan: '● Đang chạy' }, { k: 'tat', nhan: '○ Đang tắt' }];
  KM_CACH.forEach(function (c) { LOC.push({ k: c.k, nhan: c.ic + ' ' + c.nhan }); });
  var loc = kmLocCt;
  var d2 = ds.filter(function (x) {
    if (!loc) return true;
    if (loc === 'bat') return !!x.bat;
    if (loc === 'tat') return !x.bat;
    return x.cach_thuc === loc;
  });
  var html = '<div class="card" style="padding:10px 12px">' + kmHangChip(
    LOC.map(function (c) { return posChipNut('data-kmloc="' + h(c.k) + '"', c.nhan, c.k === loc); }).join('')) + '</div>';
  html += '<div class="sec">Chương trình</div><div class="card" style="padding:6px 14px">';
  if (!d2.length) html += '<div class="emp" style="padding:24px"><div class="e1">🎫</div><div>Chưa có chương trình nào ở nhóm này.<br>Bấm nút <b>+</b> góc dưới để tạo.</div></div>';
  d2.forEach(function (x) {
    var c = kmNhanCach(x.cach_thuc);
    html += '<div style="display:flex;align-items:center;gap:10px;padding:11px 0;border-bottom:1px solid #f6f7f9">' +
      '<span style="width:38px;height:38px;flex:none;border-radius:10px;background:' + (x.bat ? '#f0fdfa' : '#f6f7f9') + ';display:flex;align-items:center;justify-content:center;font-size:18px">' + c.ic + '</span>' +
      '<div data-kmx="' + h(x.name) + '" style="flex:1;min-width:0;cursor:pointer">' +
      '<div style="font-size:14.5px;font-weight:600">' + h(x.ten) + '</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:4px">' +
      kmChipNho(c.nhan, '#eef2ff', '#3730a3') +
      kmChipNho(kmMucGiam(x), '#fef3c7', '#92400e') +
      (x.cach_ma === 'Ma co dinh' ? kmChipNho('mã ' + h(x.ma_co_dinh), '#f0fdfa', '#0f766e') : '') +
      (x.cach_ma === 'Ma dung mot lan' ? kmChipNho('mã dùng 1 lần', '#f0fdfa', '#0f766e') : '') +
      (x.can_otp ? kmChipNho('🔐 cần OTP', '#fef2f2', '#b3261e') : '') +
      (x.bat && !x.dung_duoc ? kmChipNho(h(x.ly_do), '#fff7ed', '#9a3412') : '') +
      (x.da_dung ? kmChipNho('đã dùng ' + x.da_dung, '#f6f7f9', '#6b7280') : '') +
      '</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:4px">' + kmChipPhamVi(x) + '</div>' +
      '</div>' +
      posChipNut('data-kmbat="' + h(x.name) + '" data-loai="ct"', x.bat ? '● Bật' : '○ Tắt', !!x.bat) +
      '</div>';
  });
  html += '</div>';
  return html;
}

/* Chip pham vi: nguon don va diem ban cua mot chuong trinh.

   Truoc day man nay bao "khong ap dung cho nguon don (trong)" cho moi
   chuong trinh, vi no hoi may chu "chuong trinh nay dung duoc khong" ma
   khong kem don hang nao - khong co don thi kenh nao cung khong khop.
   Nay man cau hinh chi noi PHAM VI da khai, khong phan xet dung sai
   (De bao 12/08/2026). */
function kmChipPhamVi(x) {
  var out = '';
  var kenh = x.kenh_ds || [];
  if (kenh.length) {
    kenh.forEach(function (n) { out += kmChipNho(h(n), '#ecfeff', '#0b7c93'); });
  } else {
    out += kmChipNho('mọi nguồn đơn', '#f6f7f9', '#6b7280');
  }
  var quay = x.quay_ds || [];
  if (quay.length) {
    quay.forEach(function (q) {
      var ten = q;
      for (var i = 0; i < KM_QUAY.length; i++) if (KM_QUAY[i].ma === q) ten = KM_QUAY[i].ten;
      out += kmChipNho('🏪 ' + h(ten), '#f5f3ff', '#5b21b6');
    });
  } else {
    out += kmChipNho('🏪 cả ba điểm', '#f6f7f9', '#6b7280');
  }
  return out;
}

function kmChipNho(chu, nen, mau) {
  return '<span style="background:' + nen + ';color:' + mau + ';border-radius:999px;padding:2px 9px;font-size:11.5px;font-weight:600">' + chu + '</span>';
}

function kmMucGiam(x) {
  if (x.cach_thuc === 'Dong gia') return 'đồng giá ' + money(x.gia_dong) + 'đ';
  if (x.cach_thuc === 'Giam luy ke') return 'theo bậc';
  if (x.cach_thuc === 'Mua X tang Y' || x.cach_thuc === 'Tang mon') return 'tặng món';
  return x.kieu_giam === 'So tien' ? 'giảm ' + money(x.gia_tri) + 'đ' : 'giảm ' + num(x.gia_tri) + '%';
}

/* --- the Combo --- */
function kmHtmlCb(ds) {
  var html = '<div class="sec">Combo</div><div class="card" style="padding:6px 14px">';
  if (!ds.length) html += '<div class="emp" style="padding:24px"><div class="e1">🧺</div><div>Chưa phối combo nào.<br>Bấm nút <b>+</b> góc dưới để tạo.</div></div>';
  ds.forEach(function (x) {
    var mon = comboMoTa(x);
    html += '<div style="display:flex;align-items:center;gap:10px;padding:11px 0;border-bottom:1px solid #f6f7f9">' +
      '<span style="width:38px;height:38px;flex:none;border-radius:10px;background:' + (x.bat ? '#f0fdfa' : '#f6f7f9') + ';display:flex;align-items:center;justify-content:center;font-size:18px">🧺</span>' +
      '<div data-kmcb="' + h(x.name) + '" style="flex:1;min-width:0;cursor:pointer">' +
      '<div style="font-size:14.5px;font-weight:600">' + h(x.ten) + '</div>' +
      '<div style="font-size:12px;color:#98a2b3;margin-top:2px">' + mon + '</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:4px">' +
      kmChipNho('<s>' + money(x.gia_goc) + 'đ</s> → <b>' + money(x.gia_combo) + 'đ</b>', '#eef2ff', '#3730a3') +
      kmChipNho('khách tiết kiệm ' + (x.co_nhom ? 'từ ' : '') + money(x.tiet_kiem) + 'đ', '#fef3c7', '#92400e') +
      (x.can_otp ? kmChipNho('🔐 cần OTP', '#fef2f2', '#b3261e') : '') +
      (x.bat && !x.dung_duoc ? kmChipNho(h(x.ly_do), '#fff7ed', '#9a3412') : '') +
      '</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:4px">' + kmChipPhamVi(x) + '</div>' +
      '</div>' +
      posChipNut('data-kmbat="' + h(x.name) + '" data-loai="cb"', x.bat ? '● Bật' : '○ Tắt', !!x.bat) +
      '</div>';
  });
  html += '</div>';
  return html;
}

async function kmBatTat(ma, loai) {
  var ds = loai === 'cb' ? kmData.cb : kmData.ct;
  var x = ds.filter(function (y) { return y.name === ma; })[0] || {};
  try {
    await api(loai === 'cb' ? 'vagabond.khuyen_mai.bat_tat_combo' : 'vagabond.khuyen_mai.bat_tat_ctkm',
      { ma: ma, bat: x.bat ? 0 : 1 });
    toast(x.bat ? 'Đã tắt "' + (x.ten || ma) + '"' : 'Đã bật "' + (x.ten || ma) + '"');
    go(scrKhuyenMai, true);
  } catch (e) { toast((e && e.message) || 'Không đổi được'); }
}

/* --- the Lo ma voucher --- */
async function kmVeLo() {
  var box = document.getElementById('kmLoBox'); if (!box) return;
  var kq;
  try { kq = await api('vagabond.khuyen_mai.ds_lo', {}); }
  catch (e) { box.innerHTML = '<div class="emp" style="padding:22px"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'; return; }
  var ds = (kq && kq.lo) || [];
  var maLan = kmData.ct.filter(function (x) { return x.cach_ma === 'Ma dung mot lan'; });
  var html = '';
  if (!maLan.length) {
    html += '<div style="padding:12px 0;font-size:13px;color:#92400e;background:#fffbeb;border:1.5px solid #fcd34d;border-radius:9px;padding:11px 13px;margin:8px 0">' +
      'Chưa có chương trình nào để cách phát mã là <b>Mã dùng một lần</b>. Mở một chương trình rồi đổi cách phát mã, sau đó mới xuất lô được.</div>';
  } else {
    html += '<div style="padding:10px 0;font-size:12.5px;color:#6b7280;font-weight:700">XUẤT LÔ MÃ MỚI CHO CHƯƠNG TRÌNH</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:7px;padding-bottom:12px">' +
      maLan.map(function (x) { return posChipNut('data-kmxlo="' + h(x.name) + '"', '📮 ' + h(x.ten), false); }).join('') + '</div>';
  }
  if (!ds.length) html += '<div class="emp" style="padding:24px"><div class="e1">📮</div><div>Chưa xuất lô mã nào.</div></div>';
  ds.forEach(function (x) {
    var mau = x.trang_thai === 'Da gui' ? ['#f0fdfa', '#0f766e'] : (x.trang_thai === 'Loi gui' ? ['#fef2f2', '#b3261e'] : ['#fffbeb', '#92400e']);
    html += '<div style="padding:11px 0;border-bottom:1px solid #f6f7f9">' +
      '<div style="display:flex;align-items:center;gap:10px">' +
      '<div data-kmlo="' + h(x.name) + '" style="flex:1;min-width:0;cursor:pointer">' +
      '<div style="font-size:14.5px;font-weight:600">' + h(x.ten_ctkm || x.ctkm) + '</div>' +
      '<div style="font-size:12px;color:#98a2b3;margin-top:2px">' + h(x.name) + ' · ' + x.so_luong + ' mã · gửi ' + h(x.email_nhan) +
      (x.gui_cho ? ' · cho ' + h(x.gui_cho) : '') + '</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:4px">' +
      kmChipNho(x.trang_thai === 'Da gui' ? '✓ đã gửi mail' : (x.trang_thai === 'Loi gui' ? '⚠️ lỗi gửi mail' : '⏳ chờ gửi'), mau[0], mau[1]) +
      kmChipNho('đã dùng ' + (x.da_dung || 0) + '/' + x.so_luong, '#eef2ff', '#3730a3') +
      (x.han_dung ? kmChipNho('hạn ' + posNgayVn(x.han_dung), '#f6f7f9', '#6b7280') : '') +
      '</div></div>' +
      (x.trang_thai === 'Da gui' ? '' : posChipNut('data-kmgui="' + h(x.name) + '"', '📨 Gửi lại', false)) +
      '</div>' +
      (x.loi_gui ? '<div style="font-size:11.5px;color:#b3261e;margin-top:5px">' + h(x.loi_gui) + '</div>' : '') +
      '</div>';
  });
  box.innerHTML = html;
}

async function kmGuiLai(lo) {
  toast('Đang gửi lại...');
  try {
    var kq = await api('vagabond.khuyen_mai.gui_lai_lo', { lo: lo });
    toast(kq.da_gui ? 'Đã gửi lại ' + kq.so_luong + ' mã' : ('Vẫn lỗi: ' + (kq.loi || '')));
    go(scrKhuyenMai, true);
  } catch (e) { toast((e && e.message) || 'Không gửi được'); }
}

/* --- the Bao cao --- */
async function kmVeBaoCao() {
  var box = document.getElementById('kmBcBox'); if (!box) return;
  var kq;
  try { kq = await api('vagabond.khuyen_mai.bao_cao', {}); }
  catch (e) { box.innerHTML = '<div class="emp" style="padding:22px"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'; return; }
  var html = '<div style="display:flex;gap:10px;padding:12px 0;border-bottom:1px solid #f6f7f9">' +
    '<div style="flex:1"><div style="font-size:12px;color:#98a2b3">ĐÃ GIẢM ' + posNgayVn(kq.tu) + ' → ' + posNgayVn(kq.den) + '</div>' +
    '<div style="font-size:20px;font-weight:800;color:#b3261e">' + money(kq.tong_giam) + ' đ</div></div>' +
    '<div style="flex:1;border-left:1px solid #eef0f4;padding-left:10px"><div style="font-size:12px;color:#98a2b3">SỐ LƯỢT</div>' +
    '<div style="font-size:20px;font-weight:800">' + kq.so_luot + '</div></div></div>';

  html += '<div style="padding:12px 0 6px;font-size:12.5px;color:#6b7280;font-weight:700">THU NGÂN ĐÃ GIẢM NHIỀU NHẤT</div>';
  if (!kq.theo_nguoi.length) html += '<div style="padding:14px 0;color:#98a2b3;font-size:13px">Chưa có lượt khuyến mãi nào trong kỳ.</div>';
  kq.theo_nguoi.forEach(function (r, i) {
    html += '<div style="display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid #f6f7f9">' +
      '<span style="width:26px;text-align:center;font-weight:800;color:' + (i === 0 ? '#b3261e' : '#98a2b3') + '">' + (i + 1) + '</span>' +
      '<div style="flex:1;min-width:0;font-size:14px">' + h(r.nguoi) + '</div>' +
      '<div style="text-align:right"><b>' + money(r.tien) + ' đ</b>' +
      '<div style="font-size:11.5px;color:#98a2b3">' + r.so + ' lượt</div></div></div>';
  });

  html += '<div style="padding:14px 0 6px;font-size:12.5px;color:#6b7280;font-weight:700">CHƯƠNG TRÌNH TỐN NHẤT</div>';
  kq.theo_ct.forEach(function (r) {
    html += '<div style="display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid #f6f7f9">' +
      '<div style="flex:1;min-width:0;font-size:14px">' + h(r.ten) + ' ' + kmChipNho(r.loai === 'Combo' ? 'combo' : 'CTKM', '#eef2ff', '#3730a3') + '</div>' +
      '<div style="text-align:right"><b>' + money(r.tien) + ' đ</b>' +
      '<div style="font-size:11.5px;color:#98a2b3">' + r.so + ' lượt</div></div></div>';
  });
  html += '<div style="padding:12px 0;font-size:12px;color:#98a2b3;line-height:1.6">Bảng này để soi: một thu ngân bỗng nhiên giảm gấp nhiều lần người khác là có chuyện. Mọi lượt áp khuyến mãi đều ghi lại ai bấm, bill nào, lúc mấy giờ.</div>';
  box.innerHTML = html;
}

/* ---------- Sheet cau hinh mot chuong trinh ---------- */
function kmO(nhan, id, val, ph, kieu, mo) {
  return '<div style="margin-bottom:11px"><div style="font-size:12.5px;color:#6b7280;font-weight:700;margin-bottom:5px">' + nhan + '</div>' +
    '<input class="tin" id="' + id + '" type="' + (kieu || 'text') + '" value="' + h(val == null ? '' : val) + '" placeholder="' + h(ph || '') + '">' +
    (mo ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:4px;line-height:1.5">' + mo + '</div>' : '') + '</div>';
}
function kmOta(nhan, id, val, ph, mo) {
  return '<div style="margin-bottom:11px"><div style="font-size:12.5px;color:#6b7280;font-weight:700;margin-bottom:5px">' + nhan + '</div>' +
    '<textarea class="tin" id="' + id + '" rows="3" placeholder="' + h(ph || '') + '" style="resize:vertical">' + h(val || '') + '</textarea>' +
    (mo ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:4px;line-height:1.5">' + mo + '</div>' : '') + '</div>';
}
function kmV(id) { var o = document.getElementById(id); return o ? o.value.trim() : ''; }
function kmN(id) { var o = document.getElementById(id); return o ? (parseFloat(o.value) || 0) : 0; }

async function kmSheetCtkm(ma) {
  var km = null;
  if (ma) {
    try { var r = await api('vagabond.khuyen_mai.xem_ctkm', { ma: ma }); km = r.km; }
    catch (e) { toast((e && e.message) || 'Không mở được'); return; }
  }
  km = km || {
    cach_thuc: 'Giam tong hoa don', kieu_giam: 'Phan tram', pham_vi: 'Ca hoa don',
    doi_tuong: 'Moi khach', cach_ma: 'Khong can ma', cong_don: 1, uu_tien: 10, bat: 0,
    dong_mon: [], dong_bac: []
  };
  kmSua = JSON.parse(JSON.stringify(km));

  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  function ve() {
    var k = kmSua;
    var c = kmNhanCach(k.cach_thuc);
    /* Bam mot chip la ve lai ca to giay, ma to giay moi bat dau tu dong
       dau nen man hinh nhay vot len tren - anh Viet bao "bam chip nao man
       hinh cung bi cuon len" (12/08/2026). Nho cho dang doc truoc khi ve,
       ve xong dat lai. */
    var cuonCu = 0;
    var oCuonCu = box.querySelector('#kmCuon');
    if (oCuonCu) cuonCu = oCuonCu.scrollTop;
    var html = '<div class="shh"><b>' + (ma ? 'Sửa chương trình' : 'Chương trình mới') + '</b><div class="x">&times;</div></div>' +
      '<div id="kmCuon" style="padding:4px 14px calc(env(safe-area-inset-bottom,0px) + 90px);max-height:78vh;overflow:auto">';

    if (ma) html += '<div style="font-size:12px;color:#98a2b3;margin-bottom:10px">Mã ' + h(k.name) + (k.da_dung ? ' · đã dùng ' + k.da_dung + ' lượt' : '') + '</div>';

    html += kmO('TÊN CHƯƠNG TRÌNH', 'kmTen', k.ten, 'Ví dụ: Giảm 15% cho khách VAGABONDER');

    html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:14px 0 6px">CÁCH THỨC</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:7px;margin-bottom:6px">' +
      KM_CACH.map(function (x) { return posChipNut('data-kmc="' + x.k + '"', x.ic + ' ' + x.nhan, k.cach_thuc === x.k); }).join('') + '</div>' +
      '<div style="font-size:11.5px;color:#98a2b3;margin-bottom:12px;line-height:1.5">' + c.mo + '</div>';

    /* --- muc uu dai theo tung cach thuc --- */
    if (k.cach_thuc === 'Dong gia') {
      html += kmO('GIÁ ĐỒNG (đ)', 'kmGiaDong', k.gia_dong, '39000', 'number', 'Mọi món trong phạm vi kéo về mức giá này');
    } else if (k.cach_thuc === 'Giam luy ke') {
      html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:6px 0">CÁC BẬC</div>';
      (k.dong_bac || []).forEach(function (b, i) {
        html += '<div style="display:flex;gap:6px;align-items:center;margin-bottom:7px">' +
          '<input class="tin" data-bac="' + i + '" data-f="tu_tien" type="number" value="' + (b.tu_tien || '') + '" placeholder="từ (đ)" style="flex:2">' +
          '<input class="tin" data-bac="' + i + '" data-f="gia_tri" type="number" value="' + (b.gia_tri || '') + '" placeholder="giảm" style="flex:1">' +
          posChipNut('data-backi="' + i + '"', b.kieu_giam === 'So tien' ? 'đ' : '%', false) +
          posChipNut('data-bacxoa="' + i + '"', '×', false, true) + '</div>';
      });
      html += '<div style="margin-bottom:12px">' + posChipNut('data-bacthem="1"', '+ Thêm bậc', false) + '</div>';
    } else if (k.cach_thuc !== 'Mua X tang Y' && k.cach_thuc !== 'Tang mon') {
      html += '<div style="display:flex;gap:7px;margin-bottom:8px">' +
        posChipNut('data-kmkieu="Phan tram"', 'Giảm %', k.kieu_giam !== 'So tien') +
        posChipNut('data-kmkieu="So tien"', 'Giảm số tiền', k.kieu_giam === 'So tien') + '</div>' +
        kmO(k.kieu_giam === 'So tien' ? 'GIẢM (đ)' : 'GIẢM (%)', 'kmGiaTri', k.gia_tri, k.kieu_giam === 'So tien' ? '20000' : '10', 'number');
    }

    /* --- pham vi mon --- */
    if (k.cach_thuc === 'Giam tong hoa don' || k.cach_thuc === 'Giam gia mon' || k.cach_thuc === 'Dong gia') {
      html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:8px 0 6px">PHẠM VI MÓN</div>' +
        '<div style="display:flex;flex-wrap:wrap;gap:7px;margin-bottom:8px">' +
        posChipNut('data-kmpv="Ca hoa don"', 'Cả hoá đơn', k.pham_vi === 'Ca hoa don') +
        posChipNut('data-kmpv="Nhom mon chi dinh"', 'Nhóm món', k.pham_vi === 'Nhom mon chi dinh') +
        posChipNut('data-kmpv="Mon chi dinh"', 'Món chỉ định', k.pham_vi === 'Mon chi dinh') + '</div>';
      if (k.pham_vi === 'Nhom mon chi dinh') {
        html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:8px 0 6px">NHÓM MÓN ÁP DỤNG</div>' +
          kmChipNhieu('data-kmnmon', (kmDm && kmDm.nhom_mon) || [], k.nhom_mon);
      }
    }

    /* --- danh sach mon --- */
    if (k.cach_thuc !== 'Giam tong hoa don' && k.cach_thuc !== 'Giam luy ke') {
      html += kmHtmlDongMon(k);
    } else if (k.pham_vi === 'Mon chi dinh') {
      html += kmHtmlDongMon(k);
    }

    /* --- dieu kien --- */
    html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:14px 0 6px">ĐIỀU KIỆN</div>' +
      kmO('HOÁ ĐƠN TỪ (đ, để trống là không cần)', 'kmHdTt', k.hd_toi_thieu, '0', 'number') +
      kmO('SỐ MÓN TỐI THIỂU', 'kmSlTt', k.sl_toi_thieu, '0', 'number');

    /* --- thoi gian --- */
    html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:14px 0 6px">THỜI GIAN</div>' +
      '<div style="display:flex;gap:8px">' +
      '<div style="flex:1">' + kmO('TỪ NGÀY', 'kmTuNgay', k.tu_ngay, '', 'date') + '</div>' +
      '<div style="flex:1">' + kmO('ĐẾN NGÀY', 'kmDenNgay', k.den_ngay, '', 'date') + '</div></div>' +
      '<div style="display:flex;gap:8px">' +
      '<div style="flex:1">' + kmO('GIỜ TỪ', 'kmGioTu', (k.gio_tu || '').toString().slice(0, 5), '', 'time') + '</div>' +
      '<div style="flex:1">' + kmO('GIỜ ĐẾN', 'kmGioDen', (k.gio_den || '').toString().slice(0, 5), '', 'time') + '</div></div>' +
      '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:4px 0 6px">THỨ TRONG TUẦN <span style="font-weight:400;color:#98a2b3">(không chọn = mọi ngày)</span></div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px">' +
      [['thu_2', 'T2'], ['thu_3', 'T3'], ['thu_4', 'T4'], ['thu_5', 'T5'], ['thu_6', 'T6'], ['thu_7', 'T7'], ['thu_cn', 'CN']]
        .map(function (t) { return posChipNut('data-kmthu="' + t[0] + '"', t[1], !!k[t[0]]); }).join('') + '</div>';

    /* --- kenh va quay --- */
    html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:8px 0 6px">KÊNH BÁN</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px">' +
      (function () {
        /* Kenh dang tich ma khong con trong danh muc (nguon vua doi ten)
           van phai hien ra, khong thi no am tham co hieu luc ma khong ai
           bo tich duoc. */
        var dang = (k.kenh || '').split('\n').map(function (s) { return s.trim(); }).filter(Boolean);
        var co = kmDsKenh().slice();
        dang.forEach(function (n) { if (co.indexOf(n) < 0) co.push(n); });
        return co;
      })().map(function (n) {
        return posChipNut('data-kmkenh="' + h(n) + '"', h(n), (k.kenh || '').split('\n').indexOf(n) >= 0);
      }).join('') + '</div>' +
      '<div style="font-size:11.5px;color:#98a2b3;margin-bottom:10px">Không chọn kênh nào = áp dụng mọi kênh.</div>' +
      '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:8px 0 6px">QUẦY</div>' +
      kmChipNhieu('data-kmquay', (kmDm && kmDm.quay) || KM_QUAY, k.quay) +
      '<div style="font-size:11.5px;color:#98a2b3;margin:-6px 0 10px">Không chọn quầy nào = áp dụng cả ba điểm bán.</div>';

    /* --- doi tuong --- */
    html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:8px 0 6px">ĐỐI TƯỢNG KHÁCH</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:7px;margin-bottom:8px">' +
      [['Moi khach', 'Mọi khách'], ['Theo hang khach', 'Theo hạng khách'], ['Theo nhom khach', 'Theo nhóm khách'],
       ['Khach chi dinh', 'Khách chỉ định'], ['Nhan vien', 'Nhân viên']]
        .map(function (d) { return posChipNut('data-kmdt="' + d[0] + '"', d[1], k.doi_tuong === d[0]); }).join('') + '</div>';
    if (k.doi_tuong === 'Theo hang khach') {
      html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:8px 0 6px">HẠNG ÁP DỤNG</div>' +
        kmChipNhieu('data-kmhang', (kmDm && kmDm.hang) || [], k.hang_khach);
    }
    if (k.doi_tuong === 'Theo nhom khach') {
      html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:8px 0 6px">NHÓM KHÁCH ÁP DỤNG</div>' +
        kmChipNhieu('data-kmnkh', (kmDm && kmDm.nhom_khach) || [], k.nhom_khach);
    }
    if (k.doi_tuong === 'Nhan vien') html += '<div style="font-size:11.5px;color:#98a2b3;margin-bottom:10px;line-height:1.5">Máy nhận diện qua số điện thoại trên hồ sơ nhân sự, không phải nhân viên tự khai.</div>';

    /* --- ma voucher --- */
    html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:14px 0 6px">CÁCH PHÁT MÃ</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:7px;margin-bottom:8px">' +
      [['Khong can ma', 'Không cần mã'], ['Ma co dinh', 'Mã cố định'], ['Ma dung mot lan', 'Mã dùng một lần']]
        .map(function (d) { return posChipNut('data-kmcm="' + d[0] + '"', d[1], k.cach_ma === d[0]); }).join('') + '</div>';
    if (k.cach_ma === 'Ma co dinh') html += kmO('MÃ CỐ ĐỊNH', 'kmMaCd', k.ma_co_dinh, 'VAGABOND10', 'text', 'Cashier gõ mã này khi tính tiền. Dùng bao nhiêu lần cũng được, chỉ bị chặn bởi hạn mức bên dưới.');
    if (k.cach_ma === 'Ma dung mot lan') html += kmO('HẠN DÙNG MẶC ĐỊNH CỦA MÃ', 'kmHanMa', k.han_ma, '', 'date', 'Lưu chương trình xong, qua thẻ <b>Lô mã</b> để xuất mã và gửi qua email.');

    /* --- chong gian lan --- */
    html += '<div style="font-size:12.5px;color:#b3261e;font-weight:700;margin:14px 0 6px">CHỐNG GIAN LẬN</div>' +
      '<div style="background:#fff7ed;border:1.5px solid #fed7aa;border-radius:9px;padding:11px 13px;margin-bottom:10px;font-size:12px;color:#9a3412;line-height:1.6">' +
      'Để 0 là không giới hạn. Nên đặt ít nhất trần giảm hoặc bắt buộc OTP với chương trình giảm sâu - nếu không, một thu ngân có thể bấm cả trăm lần trong ca cho người quen.</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:7px;margin-bottom:10px">' +
      posChipNut('data-kmotp="1"', '🔐 Bắt buộc OTP quản lý', !!k.can_otp) +
      posChipNut('data-kmcd="1"', '➕ Cho cộng dồn chương trình khác', !!k.cong_don) + '</div>' +
      kmO('TRẦN GIẢM MỖI HOÁ ĐƠN (đ)', 'kmTran', k.giam_toi_da, '0', 'number') +
      kmO('TỐI ĐA MỖI NGÀY (toàn hệ thống)', 'kmLanNgay', k.lan_moi_ngay, '0', 'number') +
      kmO('TỐI ĐA MỖI THU NGÂN MỖI NGÀY', 'kmLanCa', k.lan_moi_ca, '0', 'number') +
      kmO('TỐI ĐA MỖI SỐ ĐIỆN THOẠI KHÁCH', 'kmLanKhach', k.lan_moi_khach, '0', 'number') +
      kmO('TỔNG SỐ LƯỢT CẢ CHƯƠNG TRÌNH', 'kmTongLan', k.so_lan_toi_da, '0', 'number') +
      kmOta('GHI CHÚ', 'kmGhiChu', k.ghi_chu, '');

    html += '<div style="display:flex;gap:7px;margin:8px 0 4px">' +
      posChipNut('data-kmbatct="1"', k.bat ? '● Chương trình đang bật' : '○ Chương trình đang tắt', !!k.bat) + '</div>';

    html += '</div><div style="position:sticky;bottom:0;background:#fff;border-top:1px solid #eef0f4;padding:11px 14px calc(env(safe-area-inset-bottom,0px) + 11px);display:flex;gap:8px">' +
      '<button class="btn" id="kmLuu" style="flex:1">Lưu chương trình</button></div>';
    box.innerHTML = html;
    var oCuonMoi = box.querySelector('#kmCuon');
    if (oCuonMoi && cuonCu) oCuonMoi.scrollTop = cuonCu;
    noiSuKien();
  }

  function thu(f) {
    var k = kmSua;
    k.ten = kmV('kmTen') || k.ten;
    if (document.getElementById('kmGiaTri')) k.gia_tri = kmN('kmGiaTri');
    if (document.getElementById('kmGiaDong')) k.gia_dong = kmN('kmGiaDong');
    if (document.getElementById('kmNhomMon')) k.nhom_mon = kmV('kmNhomMon');
    if (document.getElementById('kmHdTt')) k.hd_toi_thieu = kmN('kmHdTt');
    if (document.getElementById('kmSlTt')) k.sl_toi_thieu = kmN('kmSlTt');
    if (document.getElementById('kmTuNgay')) k.tu_ngay = kmV('kmTuNgay');
    if (document.getElementById('kmDenNgay')) k.den_ngay = kmV('kmDenNgay');
    if (document.getElementById('kmGioTu')) k.gio_tu = kmV('kmGioTu');
    if (document.getElementById('kmGioDen')) k.gio_den = kmV('kmGioDen');
    if (document.getElementById('kmHang')) k.hang_khach = kmV('kmHang');
    if (document.getElementById('kmNhomKh')) k.nhom_khach = kmV('kmNhomKh');
    if (document.getElementById('kmMaCd')) k.ma_co_dinh = kmV('kmMaCd');
    if (document.getElementById('kmHanMa')) k.han_ma = kmV('kmHanMa');
    if (document.getElementById('kmTran')) k.giam_toi_da = kmN('kmTran');
    if (document.getElementById('kmLanNgay')) k.lan_moi_ngay = kmN('kmLanNgay');
    if (document.getElementById('kmLanCa')) k.lan_moi_ca = kmN('kmLanCa');
    if (document.getElementById('kmLanKhach')) k.lan_moi_khach = kmN('kmLanKhach');
    if (document.getElementById('kmTongLan')) k.so_lan_toi_da = kmN('kmTongLan');
    if (document.getElementById('kmGhiChu')) k.ghi_chu = kmV('kmGhiChu');
    box.querySelectorAll('[data-bac]').forEach(function (o) {
      var i = parseInt(o.getAttribute('data-bac'), 10);
      if (kmSua.dong_bac[i]) kmSua.dong_bac[i][o.getAttribute('data-f')] = parseFloat(o.value) || 0;
    });
  }

  function bat(sel, fn) {
    box.querySelectorAll(sel).forEach(function (o) {
      o.onclick = function () { thu(); fn(o); ve(); };
    });
  }

  function noiSuKien() {
    box.querySelector('.x').onclick = function () { ov.remove(); };
    bat('[data-kmc]', function (o) { kmSua.cach_thuc = o.getAttribute('data-kmc'); });
    bat('[data-kmkieu]', function (o) { kmSua.kieu_giam = o.getAttribute('data-kmkieu'); });
    bat('[data-kmpv]', function (o) { kmSua.pham_vi = o.getAttribute('data-kmpv'); });
    bat('[data-kmdt]', function (o) { kmSua.doi_tuong = o.getAttribute('data-kmdt'); });
    bat('[data-kmcm]', function (o) { kmSua.cach_ma = o.getAttribute('data-kmcm'); });
    bat('[data-kmthu]', function (o) { var t = o.getAttribute('data-kmthu'); kmSua[t] = kmSua[t] ? 0 : 1; });
    bat('[data-kmotp]', function () { kmSua.can_otp = kmSua.can_otp ? 0 : 1; });
    bat('[data-kmcd]', function () { kmSua.cong_don = kmSua.cong_don ? 0 : 1; });
    bat('[data-kmbatct]', function () { kmSua.bat = kmSua.bat ? 0 : 1; });
    bat('[data-kmkenh]', function (o) {
      var n = o.getAttribute('data-kmkenh');
      var ds = (kmSua.kenh || '').split('\n').filter(function (x) { return x.trim(); });
      var i = ds.indexOf(n); if (i >= 0) ds.splice(i, 1); else ds.push(n);
      kmSua.kenh = ds.join('\n');
    });
    bat('[data-kmquay]', function (o) { kmSua.quay = kmDoiDong(kmSua.quay, o.getAttribute('data-kmquay')); });
    bat('[data-kmhang]', function (o) { kmSua.hang_khach = kmDoiDong(kmSua.hang_khach, o.getAttribute('data-kmhang')); });
    bat('[data-kmnkh]', function (o) { kmSua.nhom_khach = kmDoiDong(kmSua.nhom_khach, o.getAttribute('data-kmnkh')); });
    bat('[data-kmnmon]', function (o) { kmSua.nhom_mon = kmDoiDong(kmSua.nhom_mon, o.getAttribute('data-kmnmon')); });
    bat('[data-bacthem]', function () { kmSua.dong_bac.push({ tu_tien: 0, kieu_giam: 'Phan tram', gia_tri: 0 }); });
    bat('[data-bacxoa]', function (o) { kmSua.dong_bac.splice(parseInt(o.getAttribute('data-bacxoa'), 10), 1); });
    bat('[data-backi]', function (o) {
      var i = parseInt(o.getAttribute('data-backi'), 10);
      kmSua.dong_bac[i].kieu_giam = kmSua.dong_bac[i].kieu_giam === 'So tien' ? 'Phan tram' : 'So tien';
    });
    bat('[data-monxoa]', function (o) { kmSua.dong_mon.splice(parseInt(o.getAttribute('data-monxoa'), 10), 1); });
    bat('[data-monvt]', function (o) {
      var i = parseInt(o.getAttribute('data-monvt'), 10);
      kmSua.dong_mon[i].vai_tro = kmSua.dong_mon[i].vai_tro === 'Dieu kien' ? 'Uu dai' : 'Dieu kien';
    });
    box.querySelectorAll('[data-monsl]').forEach(function (o) {
      o.onchange = function () {
        var i = parseInt(o.getAttribute('data-monsl'), 10);
        if (kmSua.dong_mon[i]) kmSua.dong_mon[i].so_luong = parseFloat(o.value) || 1;
      };
    });
    var tm = box.querySelector('[data-monthem]');
    if (tm) tm.onclick = function () {
      thu();
      kmChonMon(function (it) {
        var canDk = (kmSua.cach_thuc === 'Mua A giam B' || kmSua.cach_thuc === 'Mua X tang Y');
        var daCoDk = (kmSua.dong_mon || []).some(function (m) { return m.vai_tro === 'Dieu kien'; });
        kmSua.dong_mon.push({
          vai_tro: (canDk && !daCoDk) ? 'Dieu kien' : 'Uu dai',
          item_code: it.value, ten_mon: it.label, so_luong: 1,
          kieu_giam: (kmSua.cach_thuc === 'Mua X tang Y' || kmSua.cach_thuc === 'Tang mon') ? 'Tang mien phi' : '',
          gia_tri: 0
        });
        return 1;
      }, function () { ve(); });
    };
    box.querySelector('#kmLuu').onclick = async function () {
      thu();
      if (!kmSua.ten) { toast('Chương trình chưa có tên.'); return; }
      var nut = box.querySelector('#kmLuu'); nut.disabled = true; nut.textContent = 'Đang lưu...';
      try {
        await api('vagabond.khuyen_mai.luu_ctkm', { du_lieu: JSON.stringify(kmSua), ma: ma || '' });
        ov.remove();
        toast('Đã lưu chương trình');
        go(scrKhuyenMai, true);
      } catch (e) {
        nut.disabled = false; nut.textContent = 'Lưu chương trình';
        toast((e && e.message) || 'Không lưu được');
      }
    };
  }

  ve();
  ov.appendChild(box);
  ov.onclick = function (e) { if (e.target === ov) ov.remove(); };
  document.body.appendChild(ov);
}

function kmHtmlDongMon(k) {
  var canDk = (k.cach_thuc === 'Mua A giam B' || k.cach_thuc === 'Mua X tang Y');
  var html = '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:14px 0 6px">MÓN' +
    (canDk ? ' <span style="font-weight:400;color:#98a2b3">(bấm chip vai trò để đổi Điều kiện ↔ Ưu đãi)</span>' : '') + '</div>';
  if (!(k.dong_mon || []).length) {
    html += '<div style="font-size:12.5px;color:#98a2b3;padding:8px 0">' +
      (canDk ? 'Chưa khai món nào. Cần ít nhất một món <b>Điều kiện</b> (khách phải mua) và một món <b>Ưu đãi</b>.'
             : 'Chưa khai món nào.') + '</div>';
  }
  (k.dong_mon || []).forEach(function (m, i) {
    html += '<div style="display:flex;gap:6px;align-items:center;margin-bottom:7px">' +
      (canDk || k.cach_thuc === 'Tang mon'
        ? posChipNut('data-monvt="' + i + '"', m.vai_tro === 'Dieu kien' ? 'Điều kiện' : 'Ưu đãi', m.vai_tro === 'Dieu kien') : '') +
      '<div style="flex:1;min-width:0;font-size:13.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + h(m.ten_mon || m.item_code) + '</div>' +
      '<input class="tin" data-monsl="' + i + '" type="number" value="' + (m.so_luong || 1) + '" style="width:64px;flex:none;text-align:center">' +
      posChipNut('data-monxoa="' + i + '"', '×', false, true) + '</div>';
  });
  html += '<div style="margin-bottom:8px">' + posChipNut('data-monthem="1"', '+ Thêm món', false) + '</div>';
  return html;
}

/* Mo bang chon mon dung chung cua quay. Dung lai dsItemsCache de khong
   phai tai lai danh muc mon lan nua. */
async function kmChonMon(onPick, onDong) {
  if (!dsItemsCache) {
    busy(true);
    try {
      dsItemsCache = await getList('Item', {
        filters: { is_sales_item: 1, disabled: 0, item_group: ['not in', ['Nguyên vật liệu Thô', 'Bán thành phẩm Bánh', 'Bán thành phẩm Nước', 'Nhân bán thành phẩm', 'Công cụ Dụng cụ', 'Bao bì', 'Văn phòng phẩm', 'Tài sản Cố định']] },
        fields: ['name', 'item_name', 'image', 'standard_rate', 'item_group'],
        limit_page_length: 0, order_by: 'item_name'
      });
    } catch (e) { busy(false); return toast('Không tải được danh mục món'); }
    busy(false);
  }
  posSheetMon(dsItemsCache.map(function (x) {
    return {
      value: x.name, label: x.item_name, icon: '🎂', img: x.image || '',
      gia: x.standard_rate || 0, nhom: x.item_group || '',
      phu: (x.standard_rate ? money(x.standard_rate) + ' đ' : 'chưa có giá') + ' · ' + x.name,
      tim: x.name
    };
  }), onPick, onDong);
}

/* Danh sach kenh ban de tich khi tao chuong trinh khuyen mai.

   Truoc day la mot danh sach cung o day, go tay theo tri nho. Sua danh
   sach nguon don ben man Diem ban ma quen sua o day la mo mot chuong
   trinh cu ra: chip cua nguon da doi ten khong con nut nao de bo tich,
   ma van dang co hieu luc. Nay lay thang tu cau hinh ban hang. */
function kmDsKenh() {
  var ds = ((CFGBH || {}).nguon || []).map(function (n) { return n.v; });
  if (ds.indexOf('Pancake') < 0) ds.unshift('Pancake');
  return ds;
}

/* ---------- Sheet cau hinh combo ---------- */
async function kmSheetCombo(ma) {
  var cb = null;
  if (ma) {
    cb = (kmData.cb || []).filter(function (x) { return x.name === ma; })[0];
    if (cb) cb = JSON.parse(JSON.stringify(cb));
  }
  cb = cb || { kieu: 'Gia tron goi', bat: 0, uu_tien: 10, dong: [], nhom: [], gioi_han_bill: 0 };
  cb.nhom = cb.nhom || [];
  cb.dong = cb.dong || [];
  var s = cb;

  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';

  /* Nhom mon cho khach chon. Moi nhom la mot dong trong bang s.nhom, co
     ten, chon toi thieu va toi da. Dong mon gan vao nhom bang TEN nhom;
     dong khong ghi ten nhom la mon bat buoc, luon vao bill. */
  function cbMonCuaNhom(ten) {
    return (s.dong || []).filter(function (d) { return String(d.nhom || '').trim() === ten; });
  }
  function cbNhom() {
    var ra = {};
    (s.nhom || []).forEach(function (g) {
      var ten = String(g.ten || '').trim();
      if (!ten) return;
      var ds = cbMonCuaNhom(ten);
      var toiDa = parseInt(g.chon_toi_da, 10) || 1;
      var toiThieu = parseInt(g.chon_toi_thieu, 10);
      if (isNaN(toiThieu) || toiThieu < 0) toiThieu = 0;
      ra[ten] = { toi_thieu: Math.min(toiThieu, toiDa), toi_da: toiDa, dong: ds, g: g };
    });
    return ra;
  }
  /* Tong gia le cua mot bo. datNhat = khach lay het suat toi da va toan mon
     dat nhat; nguoc lai la chi lay dung so toi thieu va toan mon re nhat.
     Phai khop y het cach may chu tinh. */
  function tongGoc(datNhat) {
    var t = 0;
    (s.dong || []).forEach(function (d) {
      if (!String(d.nhom || '').trim()) t += (d.gia_goc || 0) * (d.so_luong || 0);
    });
    var nh = cbNhom();
    Object.keys(nh).forEach(function (k) {
      var gia = nh[k].dong.map(function (d) { return (d.gia_goc || 0) * (d.so_luong || 0); });
      gia.sort(function (a, b) { return datNhat ? b - a : a - b; });
      var so = datNhat ? nh[k].toi_da : nh[k].toi_thieu;
      gia.slice(0, so).forEach(function (v) { t += v; });
    });
    return t;
  }
  function tinhTietKiem() {
    /* Tinh tren phuong an RE NHAT: bang gia dan cho khach ghi "tiet kiem X"
       thi X phai la con so khach luon duoc, chon kieu gi cung khong tut. */
    var g = tongGoc(false);
    if (s.kieu === 'Gia tron goi') return Math.max(0, g - (s.gia_combo || 0));
    if (s.kieu === 'Giam phan tram') return g * (s.gia_tri || 0) / 100;
    return Math.min(g, s.gia_tri || 0);
  }

  /* Mot dong mon trong bang cau hinh. Dung chung cho mon co san va mon
     nam trong nhom, chi khac cho co nut go khoi nhom hay khong. */
  function cbDongMon(i, tenNhom) {
    var d = (s.dong || [])[i];
    if (!d) return '';
    return '<div style="display:flex;gap:6px;align-items:center;margin-bottom:7px">' +
      '<div style="flex:1;min-width:0"><div style="font-size:13.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + h(d.ten_mon || d.item_code) + '</div>' +
      '<div style="font-size:11.5px;color:#98a2b3">' + money(d.gia_goc) + 'đ/phần</div></div>' +
      '<input class="tin" data-cbsl="' + i + '" type="number" value="' + (d.so_luong || 1) + '" style="width:58px;flex:none;text-align:center;margin:0">' +
      '<input class="tin" data-cbg="' + i + '" type="number" value="' + (d.gia_goc || 0) + '" style="width:88px;flex:none;text-align:right;margin:0">' +
      posChipNut('data-cbxoa="' + i + '"', '×', false, true) + '</div>';
  }

  function ve() {
    var g = tongGoc(true), gMin = tongGoc(false), tk = tinhTietKiem();
    var cuonCu = 0;
    var oCuonCu = box.querySelector('#cbCuon');
    if (oCuonCu) cuonCu = oCuonCu.scrollTop;
    var html = '<div class="shh"><b>' + (ma ? 'Sửa combo' : 'Combo mới') + '</b><div class="x">&times;</div></div>' +
      '<div id="cbCuon" style="padding:4px 14px calc(env(safe-area-inset-bottom,0px) + 90px);max-height:78vh;overflow:auto">' +
      '<div style="background:#f0fdfa;border:1.5px solid #7fe5f6;border-radius:9px;padding:11px 13px;margin-bottom:12px;font-size:12px;color:#0b7c93;line-height:1.6">' +
      'Khi tính tiền, cashier bấm combo thì máy <b>rã ra thành từng món thành phần</b> rồi đặt một dòng giảm giá bên dưới. Bill in ra chỉ thấy tên món thật, không in mã combo.</div>' +
      kmO('TÊN COMBO', 'cbTen', s.ten, 'Ví dụ: Combo sáng cà phê + bánh mì');

    /* ----- Mon co san: luon vao bill ----- */
    var monBB = [];
    (s.dong || []).forEach(function (d, i) { if (!String(d.nhom || '').trim()) monBB.push(i); });
    html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:8px 0 6px">MÓN CÓ SẴN TRONG COMBO' +
      ' <span style="font-weight:400;color:#98a2b3">(luôn vào bill)</span></div>';
    if (!monBB.length) html += '<div style="font-size:12.5px;color:#98a2b3;padding:6px 0">Chưa có món nào. Combo có thể chỉ gồm các nhóm cho khách chọn.</div>';
    monBB.forEach(function (i) { html += cbDongMon(i, ''); });
    html += '<div style="margin-bottom:14px">' + posChipNut('data-cbthem="1"', '+ Thêm món có sẵn', false) + '</div>';

    /* ----- Nhom mon cho khach chon ----- */
    var nhBang = cbNhom();
    var tenNh = Object.keys(nhBang);
    html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:8px 0 6px">NHÓM MÓN CHO KHÁCH CHỌN</div>';
    if (!tenNh.length) {
      html += '<div style="background:#f0fdfa;border:1.5px solid #7fe5f6;border-radius:9px;padding:10px 12px;margin-bottom:10px;font-size:12px;color:#0b7c93;line-height:1.6">' +
        'Bấm <b>Tạo nhóm món</b> để cho khách chọn, ví dụ một nhóm "Món nước" chọn 1 trong 2, một nhóm "Bánh" chọn 1 trong 4. ' +
        'Combo có nhóm thì thu ngân bấm combo sẽ hiện hộp chọn món trước khi vào bill.</div>';
    }
    (s.nhom || []).forEach(function (g, gi) {
      var ten = String(g.ten || '').trim();
      var ds = ten ? cbMonCuaNhom(ten) : [];
      var toiDa = parseInt(g.chon_toi_da, 10) || 1;
      var toiThieu = parseInt(g.chon_toi_thieu, 10); if (isNaN(toiThieu)) toiThieu = 0;
      html += '<div style="border:1.5px solid #7fe5f6;background:#f7feff;border-radius:12px;padding:10px 11px;margin-bottom:10px">' +
        '<div style="display:flex;gap:6px;align-items:center;margin-bottom:8px">' +
        '<input class="tin" data-cbnten="' + gi + '" value="' + h(ten) + '" placeholder="Tên nhóm, ví dụ Món nước" style="flex:1;margin:0;font-weight:700">' +
        posChipNut('data-cbnxoa="' + gi + '"', '×', false, true) + '</div>' +
        '<div style="display:flex;gap:8px;margin-bottom:8px">' +
        '<div style="flex:1"><div style="font-size:11.5px;color:#6b7280;margin-bottom:3px">Chọn tối thiểu</div>' +
        '<input class="tin" data-cbntt="' + gi + '" type="number" min="0" value="' + toiThieu + '" style="width:100%;margin:0;text-align:center"></div>' +
        '<div style="flex:1"><div style="font-size:11.5px;color:#6b7280;margin-bottom:3px">Tối đa</div>' +
        '<input class="tin" data-cbntd="' + gi + '" type="number" min="1" value="' + toiDa + '" style="width:100%;margin:0;text-align:center"></div>' +
        '</div>' +
        '<div style="font-size:11.5px;color:#0b7c93;margin-bottom:8px;line-height:1.5">' +
        (ten
          ? (toiThieu === toiDa
            ? 'Khách chọn đúng <b>' + toiDa + '</b> món trong ' + ds.length + ' món dưới đây.'
            : 'Khách chọn từ <b>' + toiThieu + '</b> đến <b>' + toiDa + '</b> món trong ' + ds.length + ' món dưới đây.')
          : '<span style="color:#b45309">Đặt tên nhóm trước rồi mới thêm món vào được.</span>') +
        '</div>';
      ds.forEach(function (d) { html += cbDongMon(s.dong.indexOf(d), ten); });
      if (ten && !ds.length) html += '<div style="font-size:12.5px;color:#b45309;padding:4px 0 8px">Nhóm chưa có món nào.</div>';
      html += '<div>' + posChipNut('data-cbnthem="' + gi + '"', '+ Thêm món vào nhóm', false) + '</div>' +
        '</div>';
    });
    html += '<div style="margin-bottom:14px">' + posChipNut('data-cbntao="1"', '➕ Tạo nhóm món', false) + '</div>';

    /* Mon dang ghi ten nhom ma khong con nhom nao ten do: bao ngay o day,
       khong de may chu chan luc bam Luu. */
    var moCoi = [];
    (s.dong || []).forEach(function (d, i) {
      var n = String(d.nhom || '').trim();
      if (n && !nhBang[n]) moCoi.push(i);
    });
    if (moCoi.length) {
      html += '<div style="background:#fef2f2;border:1.5px solid #fecaca;border-radius:9px;padding:10px 12px;margin-bottom:12px;font-size:12.5px;color:#991b1b;line-height:1.6">' +
        moCoi.length + ' món đang ghi nhóm không còn tồn tại nên sẽ không bao giờ được chọn:<br>' +
        moCoi.map(function (i) { return '· ' + h(s.dong[i].ten_mon || s.dong[i].item_code) + ' (nhóm "' + h(s.dong[i].nhom) + '")'; }).join('<br>') +
        '<div style="margin-top:8px">' + posChipNut('data-cbmocoi="1"', 'Gỡ tên nhóm, cho thành món có sẵn', false) + '</div></div>';
      moCoi.forEach(function (i) { html += cbDongMon(i, ''); });
    }

    html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:8px 0 6px">GIÁ COMBO</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:7px;margin-bottom:8px">' +
      [['Gia tron goi', 'Giá trọn gói'], ['Giam phan tram', 'Giảm %'], ['Giam so tien', 'Giảm số tiền']]
        .map(function (d) { return posChipNut('data-cbkieu="' + d[0] + '"', d[1], s.kieu === d[0]); }).join('') + '</div>' +
      (s.kieu === 'Gia tron goi'
        ? kmO('GIÁ BÁN CỦA COMBO (đ)', 'cbGia', s.gia_combo, '', 'number')
        : kmO(s.kieu === 'Giam phan tram' ? 'GIẢM (%)' : 'GIẢM (đ)', 'cbGiaTri', s.gia_tri, '', 'number'));

    html += '<div style="background:#fef3c7;border:1.5px solid #fcd34d;border-radius:9px;padding:11px 13px;margin-bottom:12px;font-size:13px;color:#92400e">' +
      (gMin === g
        ? 'Tổng giá lẻ <b>' + money(g) + 'đ</b> → khách trả <b>' + money(g - tk) + 'đ</b>, tiết kiệm <b>' + money(tk) + 'đ</b>' +
          (g > 0 ? ' (' + num(Math.round(tk / g * 1000) / 10) + '%)' : '')
        : 'Khách chọn rẻ nhất: giá lẻ <b>' + money(gMin) + 'đ</b>, tiết kiệm <b>' + money(tk) + 'đ</b>.<br>' +
          'Khách chọn đắt nhất: giá lẻ <b>' + money(g) + 'đ</b>. Máy tính tiền giảm theo đúng món khách chọn.') +
      '</div>';

    html += '<div style="display:flex;gap:8px">' +
      '<div style="flex:1">' + kmO('TỪ NGÀY', 'cbTuNgay', s.tu_ngay, '', 'date') + '</div>' +
      '<div style="flex:1">' + kmO('ĐẾN NGÀY', 'cbDenNgay', s.den_ngay, '', 'date') + '</div></div>';

    html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:8px 0 6px">QUẦY</div>' +
      kmChipNhieu('data-cbquay', (kmDm && kmDm.quay) || KM_QUAY, s.quay) +
      '<div style="font-size:11.5px;color:#98a2b3;margin:-6px 0 10px">Không chọn quầy nào = bán ở cả ba điểm.</div>';

    html += '<div style="font-size:12.5px;color:#b3261e;font-weight:700;margin:8px 0 6px">CHỐNG GIAN LẬN</div>' +
      '<div style="display:flex;gap:7px;margin-bottom:10px">' +
      posChipNut('data-cbotp="1"', '🔐 Bắt buộc OTP quản lý', !!s.can_otp) + '</div>' +
      kmO('TỐI ĐA MỖI HOÁ ĐƠN (0 = không giới hạn)', 'cbGhBill', s.gioi_han_bill, '0', 'number') +
      kmO('TỐI ĐA MỖI NGÀY', 'cbLanNgay', s.lan_moi_ngay, '0', 'number') +
      kmOta('MÔ TẢ', 'cbMoTa', s.mo_ta, '');

    html += '<div style="display:flex;gap:7px;margin:8px 0 4px">' +
      posChipNut('data-cbbat="1"', s.bat ? '● Combo đang bật' : '○ Combo đang tắt', !!s.bat) + '</div>';

    html += '</div><div style="position:sticky;bottom:0;background:#fff;border-top:1px solid #eef0f4;padding:11px 14px calc(env(safe-area-inset-bottom,0px) + 11px)">' +
      '<button class="btn" id="cbLuu" style="width:100%">Lưu combo</button></div>';
    box.innerHTML = html;
    var oCuonMoi = box.querySelector('#cbCuon');
    if (oCuonMoi && cuonCu) oCuonMoi.scrollTop = cuonCu;
    noi();
  }

  function thu() {
    s.ten = kmV('cbTen') || s.ten;
    if (document.getElementById('cbGia')) s.gia_combo = kmN('cbGia');
    if (document.getElementById('cbGiaTri')) s.gia_tri = kmN('cbGiaTri');
    if (document.getElementById('cbTuNgay')) s.tu_ngay = kmV('cbTuNgay');
    if (document.getElementById('cbDenNgay')) s.den_ngay = kmV('cbDenNgay');
    if (document.getElementById('cbGhBill')) s.gioi_han_bill = kmN('cbGhBill');
    if (document.getElementById('cbLanNgay')) s.lan_moi_ngay = kmN('cbLanNgay');
    if (document.getElementById('cbMoTa')) s.mo_ta = kmV('cbMoTa');
    box.querySelectorAll('[data-cbsl]').forEach(function (o) {
      var i = parseInt(o.getAttribute('data-cbsl'), 10);
      if (s.dong[i]) s.dong[i].so_luong = parseFloat(o.value) || 1;
    });
    box.querySelectorAll('[data-cbg]').forEach(function (o) {
      var i = parseInt(o.getAttribute('data-cbg'), 10);
      if (s.dong[i]) s.dong[i].gia_goc = parseFloat(o.value) || 0;
    });
    /* Doi ten nhom thi phai keo theo cac dong mon dang tro toi ten cu,
       khong thi mon bi mo coi ngay khi go xong chu cai dau tien. */
    box.querySelectorAll('[data-cbnten]').forEach(function (o) {
      var gi = parseInt(o.getAttribute('data-cbnten'), 10);
      var g = (s.nhom || [])[gi];
      if (!g) return;
      var cu = String(g.ten || '').trim();
      var moi = String(o.value || '').trim();
      if (moi === cu) return;
      g.ten = moi;
      (s.dong || []).forEach(function (d) { if (String(d.nhom || '').trim() === cu) d.nhom = moi; });
    });
    box.querySelectorAll('[data-cbntt]').forEach(function (o) {
      var gi = parseInt(o.getAttribute('data-cbntt'), 10);
      if (s.nhom[gi]) s.nhom[gi].chon_toi_thieu = Math.max(0, parseInt(o.value, 10) || 0);
    });
    box.querySelectorAll('[data-cbntd]').forEach(function (o) {
      var gi = parseInt(o.getAttribute('data-cbntd'), 10);
      if (s.nhom[gi]) s.nhom[gi].chon_toi_da = Math.max(1, parseInt(o.value, 10) || 1);
    });
  }

  function noi() {
    box.querySelector('.x').onclick = function () { ov.remove(); };
    function bat2(sel, fn) {
      box.querySelectorAll(sel).forEach(function (o) { o.onclick = function () { thu(); fn(o); ve(); }; });
    }
    bat2('[data-cbkieu]', function (o) { s.kieu = o.getAttribute('data-cbkieu'); });
    bat2('[data-cbxoa]', function (o) { s.dong.splice(parseInt(o.getAttribute('data-cbxoa'), 10), 1); });
    bat2('[data-cbotp]', function () { s.can_otp = s.can_otp ? 0 : 1; });
    bat2('[data-cbbat]', function () { s.bat = s.bat ? 0 : 1; });
    bat2('[data-cbquay]', function (o) { s.quay = kmDoiDong(s.quay, o.getAttribute('data-cbquay')); });
    box.querySelectorAll('[data-cbsl],[data-cbg],[data-cbnten],[data-cbntt],[data-cbntd]').forEach(function (o) { o.onchange = function () { thu(); ve(); }; });
    function themMonVao(tenNhom) {
      thu();
      kmChonMon(function (it) {
        s.dong.push({
          item_code: it.value, ten_mon: it.label, so_luong: 1, gia_goc: it.gia || 0,
          nhom: tenNhom || '', chon_trong_nhom: 0
        });
        return 1;
      }, function () { ve(); });
    }
    var tm = box.querySelector('[data-cbthem]');
    if (tm) tm.onclick = function () { themMonVao(''); };
    box.querySelectorAll('[data-cbnthem]').forEach(function (o) {
      o.onclick = function () {
        thu();
        var g = (s.nhom || [])[parseInt(o.getAttribute('data-cbnthem'), 10)];
        if (!g || !String(g.ten || '').trim()) { toast('Đặt tên nhóm trước đã.'); return ve(); }
        themMonVao(String(g.ten).trim());
      };
    });
    var nt = box.querySelector('[data-cbntao]');
    if (nt) nt.onclick = function () {
      thu();
      /* Ten mac dinh khac nhau de hai nhom moi khong dam ten nhau. */
      var i = (s.nhom || []).length + 1;
      var ten = 'Nhóm ' + i;
      while ((s.nhom || []).some(function (g) { return String(g.ten || '').trim() === ten; })) {
        i++; ten = 'Nhóm ' + i;
      }
      s.nhom.push({ ten: ten, chon_toi_thieu: 1, chon_toi_da: 1, mo_ta: '' });
      ve();
    };
    box.querySelectorAll('[data-cbnxoa]').forEach(function (o) {
      o.onclick = async function () {
        thu();
        var gi = parseInt(o.getAttribute('data-cbnxoa'), 10);
        var g = (s.nhom || [])[gi];
        if (!g) return;
        var ten = String(g.ten || '').trim();
        var ds = ten ? cbMonCuaNhom(ten) : [];
        if (ds.length) {
          var ok = await confirmSheet('Bỏ nhóm ' + (ten || 'mới') + '?',
            ds.length + ' món trong nhóm này sẽ thành món có sẵn, tức là luôn vào bill.',
            'Bỏ nhóm', true);
          if (!ok) return;
          ds.forEach(function (d) { d.nhom = ''; d.chon_trong_nhom = 0; });
        }
        s.nhom.splice(gi, 1);
        ve();
      };
    });
    var mc = box.querySelector('[data-cbmocoi]');
    if (mc) mc.onclick = function () {
      thu();
      var ten = {};
      (s.nhom || []).forEach(function (g) { ten[String(g.ten || '').trim()] = 1; });
      (s.dong || []).forEach(function (d) {
        var n = String(d.nhom || '').trim();
        if (n && !ten[n]) { d.nhom = ''; d.chon_trong_nhom = 0; }
      });
      ve();
    };
    box.querySelector('#cbLuu').onclick = async function () {
      thu();
      if (!s.ten) { toast('Combo chưa có tên.'); return; }
      if (!(s.dong || []).length) { toast('Combo phải có ít nhất một món.'); return; }
      var loiNh = '';
      var daTen = {};
      (s.nhom || []).forEach(function (g) {
        if (loiNh) return;
        var ten = String(g.ten || '').trim();
        if (!ten) { loiNh = 'Có nhóm món chưa đặt tên.'; return; }
        if (daTen[ten]) { loiNh = 'Nhóm "' + ten + '" bị khai hai lần.'; return; }
        daTen[ten] = 1;
        var ds = cbMonCuaNhom(ten);
        var toiDa = parseInt(g.chon_toi_da, 10) || 1;
        var toiThieu = parseInt(g.chon_toi_thieu, 10) || 0;
        if (!ds.length) { loiNh = 'Nhóm "' + ten + '" chưa có món nào.'; return; }
        if (toiThieu > toiDa) { loiNh = 'Nhóm "' + ten + '" bắt chọn tối thiểu ' + toiThieu + ' mà tối đa chỉ ' + toiDa + '.'; return; }
        if (toiDa > ds.length) { loiNh = 'Nhóm "' + ten + '" cho chọn tối đa ' + toiDa + ' món mà mới có ' + ds.length + ' món.'; return; }
        if (toiThieu === toiDa && toiDa === ds.length) {
          loiNh = 'Nhóm "' + ten + '" bắt khách lấy hết cả ' + ds.length + ' món thì không còn gì để chọn.';
        }
      });
      if (!loiNh) {
        (s.dong || []).forEach(function (d) {
          if (loiNh) return;
          var n = String(d.nhom || '').trim();
          if (n && !daTen[n]) loiNh = 'Món ' + (d.ten_mon || d.item_code) + ' đang ghi nhóm "' + n + '" mà không có nhóm nào tên đó.';
        });
      }
      if (loiNh) { toast(loiNh, 5000); return; }
      var nut = box.querySelector('#cbLuu'); nut.disabled = true; nut.textContent = 'Đang lưu...';
      try {
        await api('vagabond.khuyen_mai.luu_combo', { du_lieu: JSON.stringify(s), ma: ma || '' });
        ov.remove();
        toast('Đã lưu combo');
        go(scrKhuyenMai, true);
      } catch (e) {
        nut.disabled = false; nut.textContent = 'Lưu combo';
        toast((e && e.message) || 'Không lưu được');
      }
    };
  }

  ve();
  ov.appendChild(box);
  ov.onclick = function (e) { if (e.target === ov) ov.remove(); };
  document.body.appendChild(ov);
}

/* ---------- Xuat lo ma voucher qua email ---------- */
function kmSheetXuatLo(ctkm) {
  var x = (kmData.ct || []).filter(function (y) { return y.name === ctkm; })[0] || {};
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>Xuất lô mã ưu đãi</b><div class="x">&times;</div></div>' +
    '<div style="padding:4px 14px calc(env(safe-area-inset-bottom,0px) + 14px)">' +
    '<div style="font-size:13px;color:#374151;margin-bottom:12px">Chương trình <b>' + h(x.ten || ctkm) + '</b></div>' +
    '<div style="background:#f0fdfa;border:1.5px solid #7fe5f6;border-radius:9px;padding:11px 13px;margin-bottom:12px;font-size:12px;color:#0b7c93;line-height:1.6">' +
    'Máy sinh đủ số mã <b>6 ký tự ngẫu nhiên khác nhau</b>, mỗi mã dùng được một lần, rồi gửi file CSV về email điền bên dưới. Danh sách này để gửi cho đối tác, brand collab hoặc khách.</div>' +
    kmO('SỐ LƯỢNG MÃ', 'loSl', 100, '100', 'number', 'Tối đa 5.000 mã một lô') +
    kmO('EMAIL NHẬN DANH SÁCH MÃ', 'loEmail', '', 'ten@congty.com', 'email', 'Ai thao tác thì điền email của mình, hoặc điền thẳng email đối tác') +
    kmO('GỬI CHO (đối tác, brand, khách)', 'loCho', '', 'Ví dụ: Brand ABC - collab tháng 9') +
    kmO('HẠN DÙNG CỦA LÔ', 'loHan', x.han_ma || '', '', 'date') +
    kmOta('GHI CHÚ', 'loGc', '', '') +
    '<button class="btn" id="loXuat" style="width:100%;margin-top:6px">Sinh mã và gửi email</button></div>';
  box.querySelector('.x').onclick = function () { ov.remove(); };
  box.querySelector('#loXuat').onclick = async function () {
    var sl = kmN('loSl'), em = kmV('loEmail');
    if (sl <= 0) { toast('Số lượng mã phải lớn hơn 0.'); return; }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(em)) { toast('Email chưa đúng định dạng.'); return; }
    var nut = box.querySelector('#loXuat'); nut.disabled = true; nut.textContent = 'Đang sinh ' + sl + ' mã...';
    try {
      var kq = await api('vagabond.khuyen_mai.xuat_lo', {
        ctkm: ctkm, so_luong: sl, email: em, gui_cho: kmV('loCho'),
        han_dung: kmV('loHan'), ghi_chu: kmV('loGc')
      });
      ov.remove();
      toast(kq.da_gui ? ('Đã sinh ' + kq.so_luong + ' mã và gửi về ' + kq.email) : ('Đã sinh mã nhưng gửi mail lỗi: ' + (kq.loi || '')));
      kmThe = 'lo';
      go(scrKhuyenMai, true);
    } catch (e) {
      nut.disabled = false; nut.textContent = 'Sinh mã và gửi email';
      toast((e && e.message) || 'Không xuất được');
    }
  };
  ov.appendChild(box);
  ov.onclick = function (e) { if (e.target === ov) ov.remove(); };
  document.body.appendChild(ov);
}

async function kmSheetLo(lo) {
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>' + h(lo) + '</b><div class="x">&times;</div></div>' +
    '<div style="padding:14px"><div class="emp"><div class="e1">⏳</div><div>Đang đọc mã...</div></div></div>';
  box.querySelector('.x').onclick = function () { ov.remove(); };
  ov.appendChild(box);
  ov.onclick = function (e) { if (e.target === ov) ov.remove(); };
  document.body.appendChild(ov);
  var kq;
  try { kq = await api('vagabond.khuyen_mai.ds_ma_cua_lo', { lo: lo }); }
  catch (e) { box.innerHTML = '<div class="shh"><b>' + h(lo) + '</b><div class="x">&times;</div></div><div style="padding:20px;color:#b3261e">' + h((e && e.message) || 'Lỗi') + '</div>'; return; }
  var ds = (kq && kq.ma) || [];
  var chuaDung = ds.filter(function (x) { return x.trang_thai === 'Chua dung'; }).length;
  var html = '<div class="shh"><b>' + h(lo) + '</b><div class="x">&times;</div></div>' +
    '<div style="padding:4px 14px calc(env(safe-area-inset-bottom,0px) + 14px);max-height:76vh;overflow:auto">' +
    '<div style="font-size:13px;color:#374151;margin-bottom:10px">' + kq.tong_so + ' mã · <b>' + chuaDung + '</b> chưa dùng · ' + (ds.length - chuaDung) + ' đã dùng hoặc huỷ</div>' +
    '<div style="display:flex;flex-wrap:wrap;gap:6px">';
  ds.forEach(function (x) {
    var dung = x.trang_thai === 'Da dung', huy = x.trang_thai === 'Da huy';
    html += '<span title="' + (dung ? h(x.hoa_don || '') : '') + '" style="font-family:ui-monospace,monospace;font-size:13px;letter-spacing:.5px;border-radius:7px;padding:5px 9px;' +
      (dung ? 'background:#f6f7f9;color:#c3c8d4;text-decoration:line-through' : (huy ? 'background:#fef2f2;color:#fca5a5;text-decoration:line-through' : 'background:#f0fdfa;color:#0f766e;font-weight:700')) + '">' + h(x.name) + '</span>';
  });
  html += '</div>';
  if (kq.tong_so > ds.length) html += '<div style="font-size:12px;color:#98a2b3;margin-top:10px">Lô có ' + kq.tong_so + ' mã, đang hiện ' + ds.length + '. File CSV đầy đủ đã gửi qua email.</div>';
  html += '</div>';
  box.innerHTML = html;
  box.querySelector('.x').onclick = function () { ov.remove(); };
}


/* ==================================================================
   Khach hang than thiet ngay tren man TINH TIEN (anh Viet 19/08/2026)

   Truoc hom nay toan bo phan hang va diem chi song o man Doanh thu Sales.
   Thu ngan bam bill tay tai quay thi chon khach xong khong thay gi ca:
   khong hang, khong so diem, khong biet khach duoc tich bao nhieu. Chip
   "hang" trong 09-tinh-tien-quay.js doc posDon.khach_hang, ma o do chua
   bao gio duoc gan gia tri - tuc la ma chet.

   Hai khoi duoi day bu cho phan do, va them o TRU TIEN BANG DIEM.

   Luong tru diem tai quay khac luong tren hoa don o mot cho: hoa don chua
   ton tai luc thu ngan nhap diem. Nen pha xac nhan ma CHUA tru diem, no
   chi cap mot VE. Diem chi that su bi tru luc bam Thu tien, khi may chu da
   co to hoa don that de kiem lai tran. Xem chu thich dai o dau phan quay
   trong vagabond/diem_otp.py.
   ================================================================== */

var posDemNguoc = null;

function posDiemDat() {
  /* Dat lai toan bo trang thai diem. Goi khi doi khach hoac chot xong bill. */
  posDon.diemThe = null;
  posDon.diemTt = null;
  posDon.diemNhap = '';
  posDon.diemPhien = null;
  posDon.diemHan = 0;
  posDon.diemVe = null;
}

function posDiemTat() {
  if (posDemNguoc) { clearInterval(posDemNguoc); posDemNguoc = null; }
}

async function posTaiThe(tongTruocDiem) {
  /* Nap the hang va tran diem cho khach dang chon. Loi thi bo qua im lang:
     khong ai duoc phep ket bill chi vi khoi the khong tai duoc. */
  if (!posDon.khach_ma) { posDon.diemThe = null; posDon.diemTt = null; return; }
  try {
    posDon.diemThe = await api('vagabond.khach_hang.the_tren_don', {
      khach: posDon.khach_ma, tien: Math.max(0, tongTruocDiem || 0)
    });
  } catch (e) { posDon.diemThe = null; }
  try {
    posDon.diemTt = await api('vagabond.diem_otp.tinh_trang_quay', {
      khach: posDon.khach_ma, tong: Math.max(0, tongTruocDiem || 0)
    });
  } catch (e) { posDon.diemTt = null; }
}

function posVeThe() {
  /* Khoi hang the va so diem. Chi hien khi da chon khach. */
  var t = posDon.diemThe;
  if (!t || !t.co) return '';
  var anh = t.anh_hang
    ? '<img src="' + h(t.anh_hang) + '" alt="" style="width:44px;height:44px;border-radius:9px;object-fit:cover;flex:none">'
    : '<span style="font-size:26px">🎫</span>';
  var uu = t.giam_gia
    ? '<span style="background:#ecfdf5;color:#047857;border-radius:999px;padding:2px 8px;font-size:11.5px;font-weight:700">giảm ' + money(t.giam_gia) + '%</span>'
    : '';
  return '<div class="card" style="padding:12px 14px;margin-top:10px;border:1.5px solid #bae6fd;background:#f0f9ff">' +
    '<div style="display:flex;align-items:center;gap:10px">' + anh +
    '<div style="flex:1;min-width:0"><b style="font-size:14.5px">' + h(t.ten || t.khach) + '</b>' +
    '<div style="font-size:12px;color:#0369a1;margin-top:2px">hạng ' + h(t.ten_hang || 'chưa xếp') + ' ' + uu + '</div></div></div>' +
    '<div style="display:flex;gap:8px;margin-top:10px">' +
    '<div style="flex:1;background:#fff;border:1.5px solid #e0f2fe;border-radius:9px;padding:8px 10px">' +
    '<div style="font-size:11.5px;color:#6b7280">Số điểm hiện có</div>' +
    '<div style="font-size:18px;font-weight:800;color:#0f172a">' + money(t.diem_hien_tai) + '</div></div>' +
    '<div style="flex:1;background:#fff;border:1.5px solid #dcfce7;border-radius:9px;padding:8px 10px">' +
    '<div style="font-size:11.5px;color:#6b7280">Điểm tích cho bill này</div>' +
    '<div style="font-size:18px;font-weight:800;color:#15803d">' + money(t.diem_don_nay) + '</div>' +
    '<div style="font-size:11px;color:#94a3b8">hạng ' + h(t.ten_hang || '') + ' tích ' + money(t.tich_diem_pt) + '%</div></div>' +
    '</div>' + posVeTruDiem() + '</div>';
}

function posVeTruDiem() {
  /* Ba trang thai: chua xin ma, dang cho khach doc ma, da xac nhan xong. */
  var tt = posDon.diemTt || {};
  if (posDon.diemVe) {
    return '<div style="margin-top:10px;background:#ecfdf5;border:1.5px solid #a7f3d0;border-radius:10px;padding:10px 12px">' +
      '<div style="display:flex;align-items:center;gap:8px">' +
      '<div style="flex:1;font-size:13px;color:#065f46"><b>Đã xác nhận trừ ' + money(posDon.diemVe.so_diem) + ' điểm</b>' +
      '<div style="font-size:12px;margin-top:2px">giảm ' + money(posDon.diemVe.so_tien) + ' đ · điểm chỉ thật sự trừ khi bấm Thu tiền</div></div>' +
      '<button id="posDiemBo" style="border:1.5px solid #fecaca;background:#fff;color:#b91c1c;border-radius:8px;padding:7px 11px;font-size:12.5px;font-weight:700">Bỏ</button>' +
      '</div></div>';
  }
  if (posDon.diemPhien) {
    return '<div style="margin-top:10px;background:#fffbeb;border:1.5px solid #fde68a;border-radius:10px;padding:10px 12px">' +
      '<div style="font-size:13px;color:#92400e"><b>Đã gửi mã tới số ****' + h(posDon.diemPhien.duoi_so || '') + '</b>' +
      (posDon.diemPhien.gia_lap ? ' <span style="color:#b45309">(chế độ giả lập, mã nằm trong Error Log)</span>' : '') +
      '<div style="font-size:12px;margin-top:2px">Trừ ' + money(posDon.diemPhien.so_diem) + ' điểm, giảm ' +
      money(posDon.diemPhien.so_tien) + ' đ. Nhờ khách đọc mã 6 số. <span id="posDiemDem"></span></div></div>' +
      '<div style="display:flex;gap:8px;margin-top:8px">' +
      '<input class="tin" id="posDiemMa" placeholder="Mã 6 số khách đọc" inputmode="numeric" maxlength="6" style="flex:1;margin:0">' +
      '<button id="posDiemXn" style="border:0;background:#0b7c93;color:#fff;border-radius:9px;padding:9px 14px;font-size:13.5px;font-weight:700">Xác nhận</button>' +
      '</div>' +
      '<div style="margin-top:6px"><button id="posDiemHuy" style="border:0;background:transparent;color:#6b7280;font-size:12.5px;text-decoration:underline;padding:0">Huỷ lượt trừ điểm này</button></div>' +
      '</div>';
  }
  if (!tt.dung_duoc) {
    return tt.vi_sao
      ? '<div style="margin-top:10px;font-size:12px;color:#94a3b8">Trừ tiền bằng điểm: ' + h(tt.vi_sao) + '</div>'
      : '';
  }
  return '<div style="margin-top:10px;background:#fff;border:1.5px dashed #7dd3fc;border-radius:10px;padding:10px 12px">' +
    '<div style="font-size:12.5px;color:#0369a1;font-weight:700;margin-bottom:6px">TRỪ TIỀN BẰNG ĐIỂM</div>' +
    '<div style="font-size:11.5px;color:#6b7280;margin-bottom:7px">Bill này dùng được tối đa <b>' + money(tt.toi_da) +
    '</b> điểm (bằng ' + money(tt.tran_pt) + '% giá trị bill). 1 điểm = ' + money(tt.quy_doi) + ' đ.</div>' +
    '<div style="display:flex;gap:8px">' +
    '<input class="tin" id="posDiemNhap" placeholder="Số điểm khách muốn dùng" inputmode="numeric" value="' +
    h(posDon.diemNhap || '') + '" style="flex:1;margin:0">' +
    '<button id="posDiemXin" style="border:0;background:#0b7c93;color:#fff;border-radius:9px;padding:9px 14px;font-size:13.5px;font-weight:700">Gửi mã</button>' +
    '</div>' +
    '<div style="margin-top:6px"><button id="posDiemToiDa" style="border:0;background:transparent;color:#0b7c93;font-size:12.5px;text-decoration:underline;padding:0">Dùng tối đa ' + money(tt.toi_da) + ' điểm</button></div>' +
    '</div>';
}

function posGanTruDiem(goiLai) {
  /* Noi cac nut cua khoi diem. goiLai la ham ve lai man hinh. */
  posDiemTat();
  var nNhap = document.getElementById('posDiemNhap');
  if (nNhap) nNhap.oninput = function () { posDon.diemNhap = nNhap.value; };

  var nToiDa = document.getElementById('posDiemToiDa');
  if (nToiDa) nToiDa.onclick = function () {
    posDon.diemNhap = String((posDon.diemTt || {}).toi_da || 0);
    goiLai();
  };

  var nXin = document.getElementById('posDiemXin');
  if (nXin) nXin.onclick = async function () {
    var so = parseInt(String(posDon.diemNhap || '').replace(/[^0-9]/g, ''), 10) || 0;
    if (so <= 0) return toast('Nhập số điểm khách muốn dùng trước đã.');
    busy(true);
    try {
      /* Gui ca gio hang len: may chu tinh lai tong bill roi moi duyet so
         diem. Khong gui tong tien - QT-19. */
      var kq = await api('vagabond.diem_otp.xin_ma_quay', {
        khach: posDon.khach_ma,
        so_diem: so,
        items: JSON.stringify(posDon.mon.map(function (m) {
          return { item_code: m.item_code, qty: m.qty, rate: m.rate };
        })),
        giam_gia: posSoTien(posDon.giam),
        phi_ship: 0,
        ctkm_ap: JSON.stringify(posDon.ctkm || []),
        combo_ap: JSON.stringify(posDon.combo || []),
        ma_voucher: posDon.maVc || '',
        quay: (posQuay && posQuay.ma) || '',
        nguon: posNguonThuc(),
        sdt: posDon.sdt || '',
        ngay: today()
      });
      busy(false);
      if (!kq || !kq.ok) return toast('Không gửi được mã cho khách: ' + ((kq && kq.chi_tiet) || 'thử lại giúp em'), 5000);
      posDon.diemPhien = kq;
      posDon.diemHan = Date.now() + (kq.song_giay || 180) * 1000;
      goiLai();
    } catch (e) { busy(false); toast((e && e.message) || 'Xin mã lỗi, thử lại.', 5000); }
  };

  var nXn = document.getElementById('posDiemXn');
  var nMa = document.getElementById('posDiemMa');
  if (nXn) nXn.onclick = async function () {
    var ma = String((nMa && nMa.value) || '').replace(/[^0-9]/g, '');
    if (ma.length !== 6) return toast('Mã xác nhận gồm 6 chữ số.');
    busy(true);
    try {
      var kq = await api('vagabond.diem_otp.xac_nhan_quay', {
        phien: posDon.diemPhien.phien, ma: ma
      });
      busy(false);
      posDon.diemVe = kq;
      posDon.diemPhien = null;
      toast('Đã xác nhận. Điểm sẽ trừ khi bấm Thu tiền.', 3500);
      goiLai();
    } catch (e) { busy(false); toast((e && e.message) || 'Mã không đúng.', 5000); }
  };

  var nHuy = document.getElementById('posDiemHuy');
  if (nHuy) nHuy.onclick = async function () {
    try { await api('vagabond.diem_otp.bo_ve', { phien: posDon.diemPhien.phien }); } catch (e) { }
    posDon.diemPhien = null;
    goiLai();
  };

  var nBo = document.getElementById('posDiemBo');
  if (nBo) nBo.onclick = async function () {
    try { await api('vagabond.diem_otp.bo_ve', { phien: posDon.diemVe.ve }); } catch (e) { }
    posDon.diemVe = null;
    posDon.diemNhap = '';
    goiLai();
  };

  /* Dong ho dem nguoc cho ma OTP. Chi ve lai mot the span, khong ve lai ca
     man hinh moi giay - ve lai ca man thi o nhap ma mat con tro. */
  var nDem = document.getElementById('posDiemDem');
  if (nDem && posDon.diemHan) {
    posDemNguoc = setInterval(function () {
      var n = document.getElementById('posDiemDem');
      if (!n) return posDiemTat();
      var con = Math.max(0, Math.round((posDon.diemHan - Date.now()) / 1000));
      n.innerHTML = con > 0
        ? 'Mã còn <b>' + con + '</b> giây.'
        : '<b style="color:#b3261e">Mã đã hết hạn, bấm Huỷ rồi gửi lại.</b>';
      if (con <= 0) posDiemTat();
    }, 1000);
  }
}

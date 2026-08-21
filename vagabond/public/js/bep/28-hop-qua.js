/* ---------------- Tuy bien ruot hop qua (Sales, 21/08/2026)

   Viec that: khach dat 25 hop Moongarden nhung khong an duoc sau rieng,
   xin doi sang hat de long nhan va chiu phu thu. Anh Viet chot "Duoc em,
   code thi chinh duoc".

   Cach lam, va vi sao lam vay
   ---------------------------
   Mot dong bao gia van la MOT dong, khong bung thanh nhieu dong hang. Don
   25 hop cho khach doanh nghiep phai xuat hoa don dung mot dong "Hop
   Moongarden x25"; bung ra tung cai banh la doi ca to hoa don dien tu, ma
   hoa don da gui co quan thue thi khong sua lai duoc (luat anh Viet chot
   13/08/2026).

   Nen ruot hop nam trong chinh dong do, cat o dang JSON trong o `ruot_hop`.
   Sales doi mon, bot mon, them mon, go phu thu - tat ca nam trong ban chep
   nay. Ma hop goc trong danh muc KHONG bao gio bi don hang sua vao.

   Tien to hq = hop qua. Da kiem va cham ten truoc khi dat (QT-28). */

var hqE = null;   // { i, ten, ma_mon, ten_mon, goc, ruot, phu_thu, don_gia_goc }
var hqOv = null;  // the phu man hinh dang mo

function hqDocRuot(x) {
  if (!x) return [];
  if (Array.isArray(x)) return x;
  try { var v = JSON.parse(x); return Array.isArray(v) ? v : []; }
  catch (e) { return []; }
}

/* Dong nay co phai hop qua khong. Hai dau hieu: da co ruot roi, hoac ma mon
   mang tien to mua vu. Khong doan theo TEN, vi ten do Sales go tay. */
function hqLaHop(x) {
  if (!x) return 0;
  if (hqDocRuot(x.ruot_hop).length) return 1;
  return String(x.ma_mon || '').toUpperCase().indexOf('BASS') === 0 ? 1 : 0;
}

function hqSoMon(ruot) {
  return (ruot || []).reduce(function (t, m) { return t + (Number(m.sl) || 0); }, 0);
}

/* Nhan gon hien ngay tren dong bao gia, de Sales nhin la biet dong nao da
   tuy bien ma khong phai mo ra xem. */
function hqNhan(x) {
  var r = hqDocRuot(x && x.ruot_hop);
  if (!r.length) return '';
  var t = hqSoMon(r) + ' món';
  if (x.phu_thu_hop) t += ' · phụ thu ' + money(x.phu_thu_hop);
  else t += ' · đổi ngang';
  return t;
}

/* DOI NGANG THI KHONG BU TIEN.

   Anh Viet chot 21/08/2026: "neu doi banh thi doi ngang thoi chu khong bu
   them tien, banh van deu la loai 80 grams het ma". Nen o phu thu chi co
   nghia khi SO MON doi. Cho nay chi NHAC chu khong chan, va so cuoi cung
   van do may chu chot (QT-19), day chi la dong chu cho Sales nhin. */
function hqNhacSoMon(soGoc, soMon, phuThu) {
  var vang = 'margin-top:11px;padding:10px 12px;background:#fffbeb;' +
    'border:1.5px solid #fcd34d;border-radius:11px;font-size:12.5px;color:#92400e';
  var xanh = 'margin-top:11px;padding:10px 12px;background:#ecfdf3;' +
    'border:1.5px solid #a6f4c5;border-radius:11px;font-size:12.5px;color:#05603a';
  var t;
  if (soGoc === soMon) {
    if (phuThu) {
      t = 'Đổi ngang <b>' + soMon + '</b> món mà vẫn đang ghi phụ thu ' +
        money(phuThu) + ' đ. Bánh đều loại 80 gram nên đổi ngang thì để <b>0</b>, kiểm lại giúp.';
      return '<div id="hq_nhac" style="' + vang + '">' + t + '</div>';
    }
    t = 'Đổi ngang <b>' + soMon + '</b> món, không cộng thêm tiền. Đúng ý rồi.';
    return '<div id="hq_nhac" style="' + xanh + '">' + t + '</div>';
  }
  t = 'Hộp chuẩn có <b>' + soGoc + '</b> món, hộp này đang <b>' + soMon + '</b> món. ' +
    (soMon > soGoc
      ? 'Khách thêm bánh thì ghi phụ thu <b>dương</b> cho đúng.'
      : 'Khách bớt bánh thì ghi phụ thu <b>âm</b> để trừ tiền.');
  return '<div id="hq_nhac" style="' + vang + '">' + t + '</div>';
}

/* ---------- Hop thoai tuy bien ---------- */

async function hqMo(i, tenBaoGia) {
  bgDoc();
  var x = (bgTay && bgTay.dong || [])[i];
  if (!x) return;
  if (!x.ma_mon) {
    return toast('Dòng này chưa chọn mã món trong danh mục nên máy chưa biết ' +
      'hộp gồm những gì. Chọn mã món trước rồi tuỳ biến.', 6000);
  }
  busy(1);
  var kq;
  try {
    kq = await api('vagabond.hop_qua.xem_tuy_bien', {
      ma_mon: x.ma_mon,
      ruot: JSON.stringify(hqDocRuot(x.ruot_hop)),
      don_gia_goc: x.don_gia || 0,
      phu_thu: x.phu_thu_hop || 0
    });
  } catch (e) { busy(0); return toast(errMsg(e), 6000); }
  busy(0);

  hqE = {
    i: i, ten: tenBaoGia, ma_mon: x.ma_mon, ten_mon: x.ten_mon || x.ma_mon,
    goc: kq.ruot_goc || [], co_khai_goc: kq.co_khai_goc, nhac: kq.nhac || '',
    /* Chua tuy bien lan nao thi lay nguyen ruot goc lam diem xuat phat. */
    ruot: (hqDocRuot(x.ruot_hop).length ? (kq.ruot || []) : (kq.ruot_goc || []).slice()),
    don_gia_goc: x.don_gia || 0,
    phu_thu: x.phu_thu_hop || 0
  };

  hqOv = document.createElement('div');
  hqOv.className = 'sh';
  hqOv.innerHTML = '<div class="shb" style="padding:16px 15px calc(env(safe-area-inset-bottom,0px) + 14px);max-height:88vh;overflow:auto"></div>';
  document.body.appendChild(hqOv);
  hqOv.addEventListener('click', hqBam);
  hqVe();
}

function hqDong() {
  if (hqOv) { hqOv.remove(); hqOv = null; }
  hqE = null;
}

function hqVe() {
  if (!hqE || !hqOv) return;
  var e = hqE;
  var soMon = hqSoMon(e.ruot), soGoc = hqSoMon(e.goc);

  var s = '<div style="font-size:17.5px;font-weight:700">Tuỳ biến hộp</div>' +
    '<div style="font-size:13.5px;color:#344054;margin-top:2px">' + h(e.ten_mon) + '</div>' +
    '<div style="font-size:12px;color:#98a2b3;margin-bottom:12px">' + h(e.ma_mon) + '</div>';

  if (!e.co_khai_goc) {
    s += '<div style="padding:11px 13px;background:#fffbeb;border:1.5px solid #fcd34d;' +
      'border-radius:11px;margin-bottom:11px">' +
      '<b style="font-size:13px;color:#92400e">Hộp này chưa khai ruột trong danh mục</b>' +
      '<div style="font-size:12.5px;color:#7c4a03;margin-top:4px;line-height:1.55">' +
      h(e.nhac || '') + ' Vẫn tuỳ biến được cho riêng đơn này: bấm Thêm món để liệt kê bánh.</div></div>';
  }

  s += '<div style="font-size:12px;color:#8a8f9c;margin-bottom:6px">BÁNH TRONG HỘP</div>';
  if (!e.ruot.length) {
    s += '<div style="padding:16px;text-align:center;color:#98a2b3;font-size:13px;' +
      'border:1.5px dashed #e4e7ec;border-radius:11px">Chưa có món nào.</div>';
  }
  e.ruot.forEach(function (m, j) {
    var laMoi = !(e.goc || []).some(function (g) { return g.ma === m.ma; });
    s += '<div style="display:flex;align-items:center;gap:8px;padding:8px 0;' +
      'border-bottom:1px solid #f2f4f7">' +
      '<div style="flex:1;min-width:0">' +
      '<div style="font-size:14px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' +
      h(m.ten || m.ma) +
      (laMoi && e.co_khai_goc ? ' <span style="font-size:11px;color:#05603a;background:#ecfdf3;' +
        'border-radius:20px;padding:1px 7px">mới thay</span>' : '') + '</div>' +
      '<div style="font-size:11.5px;color:#98a2b3">' + h(m.ma || '') + '</div></div>' +
      '<input id="hq_sl_' + j + '" type="number" inputmode="decimal" value="' + (m.sl || 1) +
      '" style="width:58px;height:36px;border:1.5px solid #e4e7ec;border-radius:9px;' +
      'text-align:center;font-size:14px;padding:0 4px">' +
      '<button data-hqdoi="' + j + '" style="flex:none;height:36px;padding:0 11px;border-radius:9px;' +
      'border:1.5px solid #bae6fd;background:#fff;color:#0369a1;font-size:12.5px;cursor:pointer">Đổi</button>' +
      '<button data-hqbo="' + j + '" style="flex:none;width:36px;height:36px;border-radius:9px;' +
      'border:1.5px solid #fecaca;background:#fff;color:#b3261e;font-size:15px;cursor:pointer">&#128465;</button>' +
      '</div>';
  });
  s += '<button data-hqthem="1" style="width:100%;height:40px;margin-top:10px;border-radius:10px;' +
    'border:1.5px dashed #bae6fd;background:#f0f9ff;color:#0369a1;font-size:13.5px;' +
    'font-weight:600;cursor:pointer">&#10133; Thêm món vào hộp</button>';

  /* Doi chieu so mon. Noi ra chu KHONG chan: co khach xin them mot banh va
     chiu tien, do la viec that chu khong phai loi. */
  if (e.co_khai_goc) s += hqNhacSoMon(soGoc, soMon, e.phu_thu);

  s += '<div style="font-size:12px;color:#8a8f9c;margin:14px 0 6px">PHỤ THU VÀ ĐƠN GIÁ</div>' +
    '<div style="display:flex;align-items:center;gap:10px;padding:5px 0">' +
    '<span style="width:118px;font-size:13.5px;color:#344054">Đơn giá gốc</span>' +
    '<b style="font-size:14.5px">' + money(e.don_gia_goc) + ' đ</b></div>' +
    '<div style="display:flex;align-items:center;gap:10px;padding:5px 0">' +
    '<span style="width:118px;font-size:13.5px;color:#344054">Phụ thu một hộp</span>' +
    '<input id="hq_phu_thu" type="text" inputmode="numeric" value="' + money(e.phu_thu) +
    '" style="width:130px;height:38px;border:1.5px solid #e4e7ec;border-radius:9px;' +
    'text-align:right;font-size:14px;padding:0 9px"></div>' +
    '<div style="font-size:12px;color:#98a2b3;line-height:1.55;margin:4px 0 9px">' +
    '<b>Đổi bánh này lấy bánh kia thì để 0</b>, bánh trong hộp đều loại 80 gram nên đổi ngang ' +
    'không bù thêm tiền. Chỉ gõ số khi khách <b>thêm</b> bánh (số dương) hoặc <b>bớt</b> bánh ' +
    '(số âm, trừ tiền). Phụ thu cộng thẳng vào đơn giá của dòng, hoá đơn vẫn in một dòng hộp.</div>' +
    '<div style="display:flex;align-items:center;gap:10px;border-top:1px solid #f2f4f7;padding-top:10px">' +
    '<span style="width:118px;font-size:13.5px;font-weight:600">Đơn giá mới</span>' +
    '<b id="hq_gia_moi" style="font-size:16.5px;color:#05603a">' +
    money(Math.max(0, (e.don_gia_goc || 0) + (e.phu_thu || 0))) + ' đ</b></div>';

  s += '<button class="btn" data-hqok style="margin-top:14px">&#9989; Áp dụng vào dòng</button>' +
    '<button class="btn gh" data-hqhuy style="margin-top:9px">Đóng</button>';

  hqOv.querySelector('.shb').innerHTML = s;
  var p = hqOv.querySelector('#hq_phu_thu');
  if (p) {
    p.oninput = function () {
      hqDocO();
      var g = hqOv.querySelector('#hq_gia_moi');
      if (g) g.textContent = money(Math.max(0, (hqE.don_gia_goc || 0) + (hqE.phu_thu || 0))) + ' đ';
      var n = hqOv.querySelector('#hq_nhac');
      if (n && hqE.co_khai_goc) {
        n.outerHTML = hqNhacSoMon(hqSoMon(hqE.goc), hqSoMon(hqE.ruot), hqE.phu_thu);
      }
    };
  }
}

/* Doc cac o dang go tren hop thoai ve hqE. Goi truoc moi lan ve lai, neu
   khong thi so Sales vua go bay mat khi bam mot nut khac. */
function hqDocO() {
  if (!hqE || !hqOv) return;
  hqE.ruot.forEach(function (m, j) {
    var el = hqOv.querySelector('#hq_sl_' + j);
    if (el) { var v = Number(el.value) || 0; m.sl = v > 0 ? v : 1; }
  });
  var p = hqOv.querySelector('#hq_phu_thu');
  if (p) {
    /* Giu dau tru: phu thu am la khach bot mon, tru tien. */
    var am = String(p.value).trim().indexOf('-') === 0;
    var so = Number(String(p.value).replace(/[^0-9]/g, '')) || 0;
    hqE.phu_thu = am ? -so : so;
  }
}

async function hqBam(ev) {
  var el;
  if (ev.target === hqOv) return hqDong();
  if ((el = ev.target.closest('[data-hqhuy]'))) return hqDong();
  if ((el = ev.target.closest('[data-hqbo]'))) {
    hqDocO(); hqE.ruot.splice(+el.getAttribute('data-hqbo'), 1); return hqVe();
  }
  if ((el = ev.target.closest('[data-hqdoi]'))) {
    return hqChonMon(+el.getAttribute('data-hqdoi'));
  }
  if (ev.target.closest('[data-hqthem]')) return hqChonMon(null);
  if (ev.target.closest('[data-hqok]')) return hqApDung();
}

async function hqApDung() {
  hqDocO();
  var e = hqE, x = bgTay.dong[e.i];
  var kq;
  busy(1);
  try {
    kq = await api('vagabond.hop_qua.xem_tuy_bien', {
      ma_mon: e.ma_mon, ruot: JSON.stringify(e.ruot),
      don_gia_goc: e.don_gia_goc, phu_thu: e.phu_thu
    });
  } catch (er) { busy(0); return toast(errMsg(er), 6000); }
  busy(0);
  x.ruot_hop = JSON.stringify(kq.ruot || []);
  x.phu_thu_hop = e.phu_thu;
  /* Don gia chot o MAY CHU chu khong tinh tren dien thoai (QT-19). */
  x.don_gia = kq.don_gia_moi;
  /* Ghi cau mo ta vao o Mo ta cua dong de no in len bao gia gui khach va
     bep doc duoc. Cat cau tuy bien cu ra truoc roi ghi lai, de bam nut hai
     lan khong de ra hai cau chong nhau. */
  var cu = String(x.mo_ta || '').replace(/\s*\(Tuỳ biến:[^)]*\)\s*$/, '').trim();
  x.mo_ta = kq.mo_ta ? ((cu ? cu + ' ' : '') + '(Tuỳ biến: ' + kq.mo_ta + ')') : cu;
  var ten = e.ten;
  hqDong();
  toast((kq.mo_ta ? ('Đã ghi: ' + kq.mo_ta) : 'Đã lưu ruột hộp vào dòng.') +
    (kq.nhac_phu_thu ? ' - ' + kq.nhac_phu_thu : ''), 5000);
  return go(function () { scrBgSua(ten); }, true);
}

/* Doi mot mon trong hop sang mon khac, hoac them mon moi.
   j === null nghia la them moi. */
async function hqChonMon(j) {
  hqDocO();
  var kq;
  busy(1);
  try { kq = await api('vagabond.hop_qua.mon_thay_the', { tim: '', gioi_han: 300 }); }
  catch (e) { busy(0); return toast(errMsg(e), 6000); }
  busy(0);
  var ds = (kq && kq.ds) || [];
  if (!ds.length) return toast('Danh mục chưa có món nào để chọn.', 5000);
  sheet(j === null ? 'Thêm món vào hộp' : 'Đổi sang món nào', ds.map(function (m) {
    return { value: m.ma, label: m.ten, phu: m.ma + ' · ' + (m.nhom || ''), tim: m.ma };
  }), null, function (it) {
    if (!it) return;
    var m = ds.filter(function (y) { return y.ma === it.value; })[0];
    if (!m) return;
    if (j === null) hqE.ruot.push({ ma: m.ma, ten: m.ten, sl: 1, ghi_chu: '' });
    else hqE.ruot[j] = { ma: m.ma, ten: m.ten, sl: hqE.ruot[j].sl || 1, ghi_chu: '' };
    hqVe();
  }, true);
}

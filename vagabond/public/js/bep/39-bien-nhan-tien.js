
/* ================= BIEN NHAN NOP TIEN MAT =================
   Anh Viet dat 30/08/2026, theo mau phieu duyet ben Lark.

   Vi sao co man nay trong khi da co man Nop quy: man Nop quy bat phai MO CA
   va CHOT CA truoc, ma kiem tren site that ngay 30/08/2026 thi bang ca
   RONG - ba diem ban chua ai mo ca. Nen ca man do chua ai dung duoc.

   Man nay di duong khac: chon diem ban, chon mot ngay hoac mot khoang
   ngay, may doc doanh thu TIEN MAT cua diem do lam so ky vong. Thu ngan
   dem so to theo menh gia, ky tay, nguoi nhan ky tay. Luat o
   vagabond/nop_quy.py.

   Hai duong do vao MOT phieu, mot bang ke, mot cap chu ky, mot bien ban.

   O ben Ban hang chi bay phieu cua CHINH MINH, o ben Ke toan bay tat ca.
   Do chi la cho gon man, hang rao that nam o may chu. */
var BNT_TOI = 0;
var bntDiem = '', bntLoc = '', bntNgay = 30, bntTim = '';
var BNT_MENH_GIA = [500000, 200000, 100000, 50000, 20000, 10000, 5000, 2000, 1000];

function bntTuNgay() {
  if (!bntNgay) return null;
  var d = new Date(); d.setDate(d.getDate() - bntNgay);
  return d.toISOString().slice(0, 10);
}

function bntTuaDe() {
  return BNT_TOI ? 'Biên nhận nộp tiền mặt' : 'Biên nhận nộp tiền (kế toán)';
}

/* Doc mot o so, bo moi ky tu khong phai chu so. Tra ve 0 khi trong. */
function bntSo(o) {
  if (!o) return 0;
  return Number(String(o.value || '').replace(/[^0-9]/g, '')) || 0;
}

/* ---- Danh sach phieu ---- */
async function scrBntDs() {
  var tua = bntTuaDe();
  frame(tua, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc phiếu...</div></div>');
  var kq, dsDiem = [];
  try {
    kq = await api('vagabond.nop_quy.danh_sach', {
      trang_thai: bntLoc, tu_ngay: bntTuNgay(), den_ngay: bntNgay ? today() : null,
      tim: bntTim, diem: bntDiem, chi_toi: BNT_TOI
    });
  } catch (e) {
    frame(tua, '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  /* Danh sach diem ban lay tu chinh cua doanh thu, khong go tay ba diem
     vao day: them diem thu tu ma man nay khong biet la bat dau lech. */
  try { dsDiem = (await api('vagabond.nop_quy.doanh_thu_diem', {})).diem || []; } catch (e) { }
  var ds = kq.ds || [], dem = kq.dem || {};

  var html = '';
  if (dsDiem.length) {
    html += '<div class="card" style="padding:10px 12px">' +
      mkChipNgay([['', 'Mọi điểm']].concat(dsDiem.map(function (d) { return [d.ma, d.ten_ngan]; })),
        bntDiem, 'data-bntdiem') + '</div>';
  }
  html += '<div class="card" style="padding:10px 12px">' +
    mkChipNgay([[7, '7 ngày'], [30, '30 ngày'], [90, '3 tháng'], [0, 'Tất cả']], bntNgay, 'data-bntngay') + '</div>';
  html += '<div class="card" style="padding:10px 12px"><div style="display:flex;flex-wrap:wrap;gap:8px">' +
    [['', 'Tất cả'], ['Nháp', 'Nháp'], ['Chờ ký nhận', 'Chờ ký nhận'], ['Đã nộp quỹ', 'Đã nộp quỹ']].map(function (c) {
      var on = bntLoc === c[0];
      var so = dem[c[0]] !== undefined ? dem[c[0]] : 0;
      return '<button class="chip' + (on ? ' on' : '') + '" data-bntloc="' + h(c[0]) + '" style="font-family:inherit">' + h(c[1]) + ' · ' + so + '</button>';
    }).join('') + '</div></div>';
  /* O tim: may chu da loc san tu lau ma man cu chua bao gio ve o nhap nao,
     nen bien tim luon rong. */
  html += '<div class="card" style="padding:10px 12px">' +
    '<input class="tin" id="bntTim" type="search" autocomplete="off" placeholder="🔎 Tìm mã phiếu hoặc tên người nộp" value="' + h(bntTim) + '" style="margin:0"></div>';

  var tongNhan = ds.reduce(function (a, d) { return a + (d.tong_thuc_nhan || 0); }, 0);
  html += '<div class="card" style="padding:12px 14px;display:flex;gap:14px">' +
    '<div style="flex:1"><div style="font-size:11.5px;color:#98a2b3;font-weight:700">SỐ PHIẾU</div>' +
    '<b style="font-size:19px">' + ds.length + '</b></div>' +
    '<div style="flex:2"><div style="font-size:11.5px;color:#98a2b3;font-weight:700">TỔNG THỰC NỘP</div>' +
    '<b style="font-size:19px">' + money(tongNhan) + ' đ</b></div></div>';

  html += '<div style="display:flex;gap:9px;margin:2px 0 6px">' +
    '<button class="btn" id="bntTao" style="flex:2;margin:0">＋ Lập biên nhận nộp tiền</button>' +
    '<button class="btn gh" id="bntXls" style="flex:1;margin:0">⬇ Tải Excel</button></div>';

  if (!ds.length) {
    html += '<div class="card"><div class="emp" style="padding:26px"><div class="e1">🫙</div>' +
      '<div>Không có phiếu nào ở nhóm này.</div></div></div>';
  } else {
    html += '<div class="lst">' + ds.map(function (d) {
      var ky = d.tu_ngay ? (d.tu_ngay === d.den_ngay ? d.tu_ngay
        : d.tu_ngay + ' → ' + d.den_ngay + ' (' + d.so_ngay + ' ngày)') : d.ngay;
      return '<div class="shi" data-bnt="' + h(d.name) + '" style="display:flex;gap:10px;align-items:flex-start;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
        '<div style="flex:1;min-width:0">' +
        '<b style="font-size:14.5px">' + h(d.name) + '</b> ' + nqChipTt(d.trang_thai) +
        '<div style="font-size:12px;color:#98a2b3;margin-top:3px">' +
        (d.ten_diem_ban ? h(d.ten_diem_ban) + ' · ' : (d.so_ca ? d.so_ca + ' ca · ' : '')) + h(ky) + '</div>' +
        '<div style="font-size:12px;color:#98a2b3">giao: ' + h(d.nguoi_giao) +
        (d.nguoi_nhan ? ' · nhận: ' + h(d.nguoi_nhan) : '') + '</div>' +
        (Math.abs(d.lech) >= 1 ? '<div style="font-size:12px;color:#b3261e;font-weight:700;margin-top:2px">Lệch ' + (d.lech > 0 ? '+' : '') + money(d.lech) + ' đ</div>' : '') +
        '</div>' +
        '<b style="white-space:nowrap">' + money(d.tong_thuc_nhan) + ' đ</b></div>';
    }).join('') + '</div>';
  }

  var b = frame(tua, html);
  b.onclick = function (e) {
    var t = e.target.closest('[data-bntdiem]');
    if (t) { bntDiem = t.getAttribute('data-bntdiem'); return go(scrBntDs, true); }
    t = e.target.closest('[data-bntngay]');
    if (t) { bntNgay = parseInt(t.getAttribute('data-bntngay'), 10); return go(scrBntDs, true); }
    t = e.target.closest('[data-bntloc]');
    if (t) { bntLoc = t.getAttribute('data-bntloc'); return go(scrBntDs, true); }
    t = e.target.closest('[data-bnt]');
    if (t) { nqXem = t.getAttribute('data-bnt'); return go(scrNopQuyXem, true); }
  };
  var oTim = document.getElementById('bntTim');
  var hen = null;
  oTim.oninput = function () {
    var v = this.value;
    clearTimeout(hen);
    /* Cho go xong hay hoi may chu: go tung chu ma ban di mot cau la man
       nhay lien tuc va ban phim rot mat. */
    hen = setTimeout(function () { bntTim = v; go(scrBntDs, true); }, 450);
  };
  document.getElementById('bntTao').onclick = function () { go(scrBntTao); };
  document.getElementById('bntXls').onclick = async function () {
    busy(true);
    try {
      var fl = await api('vagabond.nop_quy.xuat_excel', {
        trang_thai: bntLoc, tu_ngay: bntTuNgay(), den_ngay: bntNgay ? today() : null,
        tim: bntTim, diem: bntDiem, chi_toi: BNT_TOI, so_dong: 500
      });
      busy(false);
      bcTaiVe(fl.ten_file, fl.b64);
      toast('Đã tải ' + fl.ten_file + ' · ' + fl.so_dong + ' phiếu', 4000);
    } catch (e) { busy(false); toast((e && e.message) || 'Không xuất được Excel', 5000); }
  };
}

/* ---- Lap bien nhan theo diem ban va ngay ---- */
async function scrBntTao() {
  frame('Lập biên nhận nộp tiền', '<div class="emp"><div class="e1">⏳</div></div>');
  var dau;
  try { dau = await api('vagabond.nop_quy.doanh_thu_diem', {}); }
  catch (e) {
    frame('Lập biên nhận nộp tiền', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || '') + '</div></div>');
    return;
  }
  var dsDiem = dau.diem || [];
  if (!dsDiem.length) {
    frame('Lập biên nhận nộp tiền', '<div class="card"><div class="emp" style="padding:26px">' +
      '<div class="e1">🏪</div><div>Chưa khai điểm bán nào đang bật.</div></div></div>');
    return;
  }
  /* Mac dinh nop doanh thu HOM QUA: cuoi ngay moi nop, ma luc nop thi ngay
     hom nay chua ban xong. */
  var hqua = new Date(); hqua.setDate(hqua.getDate() - 1);
  var NG_MAC_DINH = hqua.toISOString().slice(0, 10);

  var BNT = { diem: bntDiem || dsDiem[0].ma, pham_vi: 'Một ngày',
    tu: NG_MAC_DINH, den: NG_MAC_DINH, kyVong: 0, anh: '', nhan: '', nhanTen: '' };

  var html = '<div class="vf"><div class="vfh"><span class="ic">🏪</span><b>Nộp cho điểm bán nào, doanh thu ngày nào</b></div>' +
    '<div class="vxl">Điểm bán</div>' +
    '<select class="vfs" id="bntDiemO">' + dsDiem.map(function (d) {
      return '<option value="' + h(d.ma) + '"' + (d.ma === BNT.diem ? ' selected' : '') + '>' + h(d.ten) + '</option>';
    }).join('') + '</select>' +
    '<div class="vxl">Phạm vi</div>' +
    '<select class="vfs" id="bntPv"><option value="Một ngày">Một ngày</option>' +
    '<option value="Khoảng ngày">Khoảng ngày (nộp gộp nhiều ngày)</option></select>' +
    '<div class="vxl" id="bntLbTu">Doanh thu của ngày</div>' +
    '<input class="vfi" type="date" id="bntTu" value="' + NG_MAC_DINH + '">' +
    '<div id="bntKhoiDen" style="display:none"><div class="vxl">Đến ngày</div>' +
    '<input class="vfi" type="date" id="bntDen" value="' + NG_MAC_DINH + '"></div>' +
    '</div>';

  html += '<div class="vf"><div class="vfh"><span class="ic">💰</span><b>Doanh thu tiền mặt hệ thống ghi nhận</b></div>' +
    '<div id="bntDt"><div class="vfm">Đang đọc...</div></div></div>';

  html += '<div class="vf"><div class="vfh"><span class="ic">🧾</span><b>Đếm số tờ tiền mặt thực nộp</b></div>' +
    '<div class="vfm">Đếm từng mệnh giá. Mệnh giá nào không có thì để trống.</div>' +
    BNT_MENH_GIA.map(function (mg, i) {
      return '<div style="display:flex;align-items:center;gap:10px;padding:6px 0' + (i ? ';border-top:1px solid #f2f4f7' : '') + '">' +
        '<div style="width:88px;text-align:right;font-weight:700">' + money(mg) + '</div>' +
        '<div style="color:#98a2b3;font-size:12px">đ ×</div>' +
        '<input class="tin bntTo" data-mg="' + mg + '" inputmode="numeric" placeholder="0" style="width:82px;text-align:right;margin:0">' +
        '<div style="flex:1;text-align:right;font-size:13px" id="bntTt' + mg + '">0 đ</div></div>';
    }).join('') +
    '<div style="display:flex;justify-content:space-between;padding:10px 0;border-top:2px solid #101828;font-size:15px">' +
    '<b>Tổng tiền mặt thực nhận</b><b id="bntTong">0 đ</b></div>' +
    '<div style="display:flex;justify-content:space-between;padding:2px 0;color:#5a6070;font-size:13px">' +
    '<span>Doanh thu tiền mặt trong kỳ</span><span id="bntKv">0 đ</span></div>' +
    '<div style="display:flex;justify-content:space-between;padding:2px 0 8px;font-size:13px;font-weight:700">' +
    '<span>Lệch</span><span id="bntLech">0 đ</span></div></div>';

  /* Anh coc tien BAT BUOC (anh Viet 31/08/2026). Chan that nam o may chu
     (`nop_quy.tao_theo_ngay`), o day chi noi truoc cho nguoi ta biet - noi
     "bat buoc" ma van lap duoc phieu trang anh thi cau do la noi doi. */
  html += '<div class="vf"><div class="vfh"><span class="ic">📷</span>' +
    '<b>Ảnh minh chứng giao nhận tiền</b>' +
    '<span style="margin-left:7px;background:#fef2f2;border:1px solid #fecaca;' +
    'color:#b3261e;border-radius:20px;padding:1px 8px;font-size:11px;' +
    'font-weight:700;white-space:nowrap">bắt buộc</span></div>' +
    '<label class="vfa" id="bntAnhO"><input type="file" accept="image/*" id="bntAnh">' +
    '<div class="i">📷</div><div class="t" id="bntAnhT">Chụp hoặc chọn ảnh cọc tiền</div>' +
    '<div class="p">Bắt buộc. Đây là chứng từ gốc của lần bàn giao tiền mặt này, ' +
    'không có ảnh thì sau này hai bên nhớ khác nhau là hết đường đối chiếu.</div></label>' +
    '<div id="bntAnhOk"></div></div>';

  /* Ba sua theo ghi chu anh Viet 31/08/2026:
       - Noi dung: may tu goi y cau day du kem khoang ngay, nguoi lap chi
         sua khi can. Cau do may chu dung, xem `nop_quy.noi_dung_mac_dinh`.
       - Noi giao nhan: DROPDOWN cac diem ban, dung bat go. Go tay thi mot
         cho ra nam cach viet, va bao cao gom theo noi giao nhan la vo dung.
       - Them o "Nop cho ai": go vai chu roi chon trong danh sach nguoi CO
         QUYEN ky nhan. Khong cho go tu do mot cai ten bat ky. */
  html += '<div class="vf"><div class="vfh"><span class="ic">📝</span><b>Nội dung và nơi giao nhận</b></div>' +
    '<div class="vxl">Nội dung nộp tiền</div>' +
    '<input class="vfi" id="bntNd" placeholder="Máy tự điền, sửa được">' +
    '<div class="vxl">Nơi giao nhận tiền</div>' +
    '<select class="vfs" id="bntNoi">' +
    dsDiem.map(function (d) {
      return '<option value="' + h(d.ten) + '">' + h(d.ten) + '</option>';
    }).join('') + '</select>' +
    '<div class="vxl">Nộp cho ai</div>' +
    '<input class="vfi" id="bntNhan" placeholder="Gõ vài chữ tên người nhận, ví dụ Dung" ' +
    'autocomplete="off">' +
    '<div id="bntNhanDs" style="margin-top:4px"></div>' +
    '<div class="vxl">Ghi chú</div>' +
    '<input class="vfi" id="bntGc" placeholder="Không bắt buộc"></div>';

  html += '<button class="btn" id="bntLap" style="width:100%">Ký bên giao và lập biên nhận</button>';
  var b = frame('Lập biên nhận nộp tiền', html);

  function tinhTien() {
    var tong = 0;
    b.querySelectorAll('.bntTo').forEach(function (o) {
      var mg = Number(o.getAttribute('data-mg')), so = bntSo(o);
      var tt = mg * so; tong += tt;
      var oTt = document.getElementById('bntTt' + mg);
      if (oTt) oTt.textContent = money(tt) + ' đ';
    });
    var lech = tong - BNT.kyVong;
    document.getElementById('bntTong').textContent = money(tong) + ' đ';
    document.getElementById('bntKv').textContent = money(BNT.kyVong) + ' đ';
    var oL = document.getElementById('bntLech');
    oL.textContent = (lech > 0 ? '+' : '') + money(lech) + ' đ';
    oL.style.color = Math.abs(lech) >= 1000 ? '#b3261e' : '#0f766e';
  }

  async function napDoanhThu() {
    var o = document.getElementById('bntDt');
    o.innerHTML = '<div class="vfm">Đang đọc doanh thu...</div>';
    var k;
    try {
      k = await api('vagabond.nop_quy.doanh_thu_diem', {
        diem: BNT.diem, pham_vi: BNT.pham_vi, tu_ngay: BNT.tu, den_ngay: BNT.den
      });
    } catch (e) {
      BNT.kyVong = 0; tinhTien();
      o.innerHTML = '<div class="vfm" style="color:#b3261e">' + h((e && e.message) || 'Không đọc được doanh thu') + '</div>';
      return;
    }
    BNT.kyVong = k.tong_tien_mat || 0;
    var ds = k.theo_ngay || [];
    var t = '';
    if (k.phieu_trum && k.phieu_trum.length) {
      t += '<div style="background:#fef3f2;border:1px solid #fda29b;border-radius:9px;padding:9px 11px;margin-bottom:9px;font-size:12.5px;color:#b42318">' +
        'Điểm này đã có phiếu <b>' + h(k.phieu_trum[0].ma) + '</b> trùm lên khoảng ngày đang chọn (' +
        h(k.phieu_trum[0].tu_ngay) + ' → ' + h(k.phieu_trum[0].den_ngay) +
        '). Nộp hai lần cùng một ngày là tiền trong sổ nhiều gấp đôi tiền có thật.</div>';
    }
    if (!ds.length) {
      t += '<div class="vfm">Không có hoá đơn tiền mặt nào trong kỳ này.</div>';
    } else {
      t += ds.map(function (r, i) {
        return '<div style="display:flex;justify-content:space-between;padding:6px 0' + (i ? ';border-top:1px solid #f2f4f7' : '') + ';font-size:13.5px">' +
          '<span>' + h(r.ngay) + ' <span style="color:#98a2b3">· ' + r.so_bill + ' bill</span></span>' +
          '<b>' + money(r.tien) + ' đ</b></div>';
      }).join('');
    }
    t += '<div style="display:flex;justify-content:space-between;padding:9px 0 2px;border-top:2px solid #101828;font-size:15px">' +
      '<b>Tổng tiền mặt</b><b>' + money(BNT.kyVong) + ' đ</b></div>';
    o.innerHTML = t;
    var oNd = document.getElementById('bntNd'), oNoi = document.getElementById('bntNoi');
    /* Cau goi y do MAY CHU dung, man hinh khong tu ghep chuoi: ghep o hai
       noi thi som muon hai noi viet khac nhau, ma cau nay di thang len to
       bien ban va len so quy. Nguoi lap sua tay roi thi khong de len nua. */
    if (!oNd.value || oNd.getAttribute('data-tu-may') === '1') {
      oNd.value = k.noi_dung || ''; oNd.setAttribute('data-tu-may', '1');
    }
    if (oNoi && k.noi_giao_nhan) oNoi.value = k.noi_giao_nhan;
    tinhTien();
  }

  /* O tim nguoi nhan. Go vai chu, may chu tra ve nhung nguoi CO QUYEN ky
     nhan, bam mot cai la chon. Khong cho go tu do mot cai ten bat ky: to
     bien ban la chung tu goc, ghi ten mot nguoi khong co quyen nhan tien
     thi to do sai ngay tu luc in ra. */
  var oNhan = document.getElementById('bntNhan'), oNhanDs = document.getElementById('bntNhanDs');
  var bntTimHen = null;
  function veNhanDs(ds) {
    if (!oNhanDs) return;
    if (!ds || !ds.length) { oNhanDs.innerHTML = ''; return; }
    oNhanDs.innerHTML = '<div style="display:flex;gap:6px;flex-wrap:wrap">' +
      ds.map(function (u) {
        return '<button type="button" data-bntn="' + h(u.ma) + '" data-bntt="' + h(u.ten) + '" ' +
          'style="border:1.5px solid #d7dce5;background:#fff;color:#374151;' +
          'border-radius:999px;padding:6px 12px;font-size:13px;cursor:pointer">' +
          h(u.ten) + '</button>';
      }).join('') + '</div>';
  }
  async function timNhan() {
    var q = String(oNhan.value || '').trim();
    if (BNT.nhan && BNT.nhanTen !== q) { BNT.nhan = ''; BNT.nhanTen = ''; }
    try {
      var k = await api('vagabond.nop_quy.tim_nguoi_nhan', { tu_khoa: q });
      veNhanDs((k || {}).ds || []);
    } catch (e) { veNhanDs([]); }
  }
  if (oNhan) {
    oNhan.oninput = function () {
      if (bntTimHen) clearTimeout(bntTimHen);
      bntTimHen = setTimeout(timNhan, 260);
    };
    oNhan.onfocus = function () { if (!oNhanDs.innerHTML) timNhan(); };
  }
  if (oNhanDs) {
    oNhanDs.onclick = function (ev) {
      var t = ev.target.closest('[data-bntn]');
      if (!t) return;
      BNT.nhan = t.getAttribute('data-bntn');
      BNT.nhanTen = t.getAttribute('data-bntt');
      oNhan.value = BNT.nhanTen;
      oNhanDs.innerHTML = '<div style="font-size:12px;color:#05603a">✓ Sẽ nộp cho ' +
        h(BNT.nhanTen) + '</div>';
    };
  }

  document.getElementById('bntDiemO').onchange = function () { BNT.diem = this.value; napDoanhThu(); };
  document.getElementById('bntPv').onchange = function () {
    BNT.pham_vi = this.value;
    var mot = BNT.pham_vi === 'Một ngày';
    document.getElementById('bntKhoiDen').style.display = mot ? 'none' : '';
    document.getElementById('bntLbTu').textContent = mot ? 'Doanh thu của ngày' : 'Doanh thu từ ngày';
    napDoanhThu();
  };
  document.getElementById('bntTu').onchange = function () {
    BNT.tu = this.value;
    /* Doi tu ngay ma den ngay dang som hon thi keo theo, khong de nguoi
       dung phai sua hai o. */
    var oDen = document.getElementById('bntDen');
    if (oDen.value < BNT.tu) { oDen.value = BNT.tu; BNT.den = BNT.tu; }
    napDoanhThu();
  };
  document.getElementById('bntDen').onchange = function () { BNT.den = this.value; napDoanhThu(); };
  b.querySelectorAll('.bntTo').forEach(function (o) {
    o.oninput = function () { this.value = this.value.replace(/[^0-9]/g, ''); tinhTien(); };
  });
  ['bntNd', 'bntNoi'].forEach(function (id) {
    document.getElementById(id).oninput = function () { this.setAttribute('data-tu-may', '0'); };
  });
  document.getElementById('bntAnh').onchange = async function () {
    var f = this.files && this.files[0];
    if (!f) return;
    var o = document.getElementById('bntAnhO'), t = document.getElementById('bntAnhT');
    o.classList.remove('thieu'); t.textContent = 'Đang tải ảnh lên...';
    busy(true);
    try {
      BNT.anh = await vxUpAnh(f);
      o.classList.add('xong'); t.textContent = 'Đã có ảnh minh chứng';
      document.getElementById('bntAnhOk').innerHTML = '<img class="vfanh" alt="Ảnh minh chứng" src="' + h(BNT.anh) + '">';
    } catch (e) {
      o.classList.add('thieu'); t.textContent = 'Chưa tải được ảnh, chạm để thử lại';
      toast((e && e.message) || 'Không tải được ảnh', 4500);
    }
    busy(false);
  };

  await napDoanhThu();

  document.getElementById('bntLap').onclick = async function () {
    var bangKe = {};
    b.querySelectorAll('.bntTo').forEach(function (o) {
      var so = bntSo(o);
      if (so > 0) bangKe[o.getAttribute('data-mg')] = so;
    });
    if (!Object.keys(bangKe).length) return toast('Chưa đếm tờ nào.', 3500);
    var thamSo = {
      diem: BNT.diem, pham_vi: BNT.pham_vi, tu_ngay: BNT.tu,
      den_ngay: BNT.pham_vi === 'Một ngày' ? BNT.tu : BNT.den,
      bang_ke: JSON.stringify(bangKe),
      anh_minh_chung: BNT.anh || '',
      noi_dung: document.getElementById('bntNd').value || '',
      noi_giao_nhan: document.getElementById('bntNoi').value || '',
      nguoi_nhan_du_kien: BNT.nhan || '',
      ghi_chu: document.getElementById('bntGc').value || ''
    };
    /* Noi truoc khi goi may chu, de nguoi ta khong mat cong doi mot vong
       chi de nghe cau tu choi. May chu van chan lai, day chi la loi nhac. */
    if (!BNT.anh) return toast('Chụp ảnh cọc tiền trước đã, ảnh này bắt buộc.', 4500);
    busy(true);
    var k;
    try { k = await api('vagabond.nop_quy.tao_theo_ngay', thamSo); }
    catch (e) { busy(false); return baoTin((e && e.message) || 'Không lập được phiếu', 'Lập biên nhận'); }
    busy(false);
    if (k.can_ly_do) {
      var lyDo = await hoiChu('Lệch so với doanh thu', (k.nhac || '') + '\nGõ lý do:', '', { nhieu_dong: 1 });
      if (lyDo === null || !String(lyDo).trim()) return toast('Chưa lập: lệch thì phải có lý do.', 5000);
      thamSo.ly_do_lech = lyDo;
      busy(true);
      try { k = await api('vagabond.nop_quy.tao_theo_ngay', thamSo); }
      catch (e2) { busy(false); return baoTin((e2 && e2.message) || 'Không lập được phiếu', 'Lập biên nhận'); }
      busy(false);
    }
    var anh = await nqKyTay('Bên giao ký tên · ' + k.ma);
    if (anh) {
      busy(true);
      try { await api('vagabond.nop_quy.ky_giao', { ma: k.ma, chu_ky: anh }); busy(false); toast('Đã lập và ký ' + k.ma, 4000); }
      catch (e3) { busy(false); baoTin((e3 && e3.message) || 'Phiếu đã lập nhưng chưa ký được', 'Ký bên giao'); }
    } else {
      toast('Đã lập ' + k.ma + ' (Nháp, chưa ký bên giao)', 4500);
    }
    nqXem = k.ma;
    go(scrNopQuyXem, true);
  };
}

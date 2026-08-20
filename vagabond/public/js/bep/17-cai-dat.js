/* ===== Cai dat: chuoi cuoi ngay theo tung diem ban (anh Viet 12/08/2026) =====

Truoc day muon doi gio chay hay bat tat mot chi nhanh la phai sua code roi
deploy. Nay bay het len app: bat tat tung diem ban, chon gio, va co nut chay
tay khi can.

Ba buoc chay LIEN NHAU trong mot lan: ghi so, phat hanh hoa don dien tu, roi
ky. Mac dinh 23:00 de xong truoc 23h30 - chi Dung so xuat sat 24h, lo nghen
mang la to hoa don lot sang ngay hom sau, sai luat ke toan. */

var cdData = null, cdGhiSo = [], cdHddt = [], cdBat = 1, cdGio = '23:00';

async function scrCaiDatCuoiNgay() {
  frame('Cuối ngày', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc cấu hình...</div></div>');
  try { cdData = await api('vagabond.ban_hang.cai_dat_cuoi_ngay', {}); }
  catch (e) {
    frame('Cuối ngày', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  cdBat = cdData.bat ? 1 : 0;
  cdGio = cdData.gio || '23:00';
  cdGhiSo = (cdData.diem || []).filter(function (d) { return d.ghi_so; }).map(function (d) { return d.ma; });
  cdHddt = (cdData.diem || []).filter(function (d) { return d.hddt; }).map(function (d) { return d.ma; });
  cdVe();
}

function cdVe() {
  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">CHUỖI CUỐI NGÀY</div>' +
    '<div style="font-size:14px;color:#374151;line-height:1.6;margin-top:4px">' +
    'Mỗi ngày một lần, máy chạy liền ba bước: <b>ghi sổ</b> hoá đơn còn nháp, <b>phát hành</b> hoá đơn điện tử, rồi <b>ký</b>. ' +
    'Đặt 23:00 thì cả ba xong trước 23h30, không lo nghẽn mạng làm hoá đơn lọt sang ngày hôm sau.</div></div>';

  html += '<div class="card" style="padding:11px 12px">' + kmHangChip(
    posChipNut('data-cdbat="1"', cdBat ? '● Đang bật' : '○ Đang tắt', !!cdBat)) +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px">Tắt thì không có gì tự chạy, kế toán ghi sổ và xuất hoá đơn bằng tay như cũ.</div></div>';

  html += '<div class="sec">Giờ chạy</div><div class="card" style="padding:11px 12px">' +
    kmHangChip(['22:00', '22:30', '23:00', '23:15'].map(function (g) {
      return posChipNut('data-cdgio="' + g + '"', g, cdGio === g);
    }).join('')) +
    '<div style="display:flex;gap:8px;align-items:center;margin-top:9px">' +
    '<span style="font-size:12.5px;color:#6b7280">Giờ khác:</span>' +
    '<input class="tin" id="cdGioTay" type="time" value="' + h(cdGio) + '" style="flex:1;max-width:170px"></div></div>';

  html += '<div class="sec">Tự ghi sổ hoá đơn còn nháp</div><div class="card">' +
    (cdData.diem || []).map(function (d) {
      var on = cdGhiSo.indexOf(d.ma) >= 0;
      return cdDong('cdgs', d, on, d.ma === 'SALES'
        ? 'Đơn online Pancake và các sàn'
        : 'Bill bán tại quầy');
    }).join('') + '</div>';

  html += '<div class="sec">Tự xuất hoá đơn điện tử</div><div class="card">' +
    (cdData.diem || []).map(function (d) {
      var on = cdHddt.indexOf(d.ma) >= 0;
      return cdDong('cdhd', d, on, 'Nguồn đơn: ' + h((d.nguon || []).join(', ')));
    }).join('') + '</div>' +
    '<div style="font-size:11.5px;color:#98a2b3;padding:2px 14px 8px;line-height:1.6">' +
    'Chỉ hoá đơn <b>đã ghi sổ</b> mới được phát hành. Điểm bán nào chưa bật thì hoá đơn nằm yên trong hệ thống, không sang cơ quan thuế.</div>';

  // Cong tac goc nam ben m-invoice. Hai noi bat tat khac nhau chinh la cai
  // da gay ra vu 37 hoa don hom 10/08, nen o day phai noi thang trang thai
  // cua no chu khong de nguoi dung doan.
  if (!cdData.bat_hddt_chung || !cdData.bat_ky_chung) {
    html += '<div class="card" style="padding:12px 14px;background:#fff7ed;border:1px solid #fed7aa">' +
      '<b style="font-size:13.5px;color:#9a3412">Khoá gốc bên m-invoice đang chặn</b>' +
      '<div style="font-size:12.5px;color:#7c2d12;line-height:1.6;margin-top:3px">' +
      (!cdData.bat_hddt_chung
        ? 'Cấu hình m-invoice đang tắt phát hành, nên dù bật ở đây máy vẫn không đẩy hoá đơn nào sang cơ quan thuế.'
        : 'Cấu hình m-invoice đang tắt ký hàng loạt, nên hoá đơn sẽ phát hành rồi nằm ở trạng thái Chờ ký.') +
      ' Báo kế toán mở lại trong phần cài đặt m-invoice nếu muốn chạy đủ chuỗi.</div></div>';
  }

  if (cdData.nhat_ky) {
    html += '<div class="sec">Lần chạy gần nhất</div><div class="card" style="padding:12px 14px;font-size:13px;color:#374151;line-height:1.6">' +
      h(cdData.nhat_ky) + '</div>';
  }

  var b = frame('Cuối ngày', html, {
    footer: '<div style="display:flex;gap:8px">' +
      '<button class="btn gh" id="cdChay" style="margin:0;flex:1">▶️ Chạy ngay</button>' +
      '<button class="btn" id="cdLuu" style="margin:0;flex:1">Lưu cấu hình</button></div>'
  });

  b.onclick = function (e) {
    var t = e.target.closest('[data-cdbat]');
    if (t) { cdBat = cdBat ? 0 : 1; return cdVe(); }
    t = e.target.closest('[data-cdgio]');
    if (t) { cdGio = t.getAttribute('data-cdgio'); return cdVe(); }
    t = e.target.closest('[data-cdgs]');
    if (t) { cdBoThem(cdGhiSo, t.getAttribute('data-cdgs')); return cdVe(); }
    t = e.target.closest('[data-cdhd]');
    if (t) { cdBoThem(cdHddt, t.getAttribute('data-cdhd')); return cdVe(); }
  };
  var og = document.getElementById('cdGioTay');
  if (og) og.onchange = function () { cdGio = og.value || cdGio; cdVe(); };

  document.getElementById('cdLuu').onclick = cdLuu;
  document.getElementById('cdChay').onclick = cdChay;
}

function cdDong(thuoc, d, on, mo) {
  return '<div ' + thuoc + '="' + h(d.ma) + '" style="display:flex;align-items:center;gap:11px;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
    '<div style="width:44px;height:26px;border-radius:99px;background:' + (on ? '#0d9488' : '#d5d9e0') + ';position:relative;flex:none;transition:background .15s">' +
    '<div style="position:absolute;top:3px;left:' + (on ? '21px' : '3px') + ';width:20px;height:20px;border-radius:50%;background:#fff;transition:left .15s"></div></div>' +
    '<div style="flex:1;min-width:0"><b style="font-size:14.5px">' + h(d.ten) + '</b>' +
    '<div style="font-size:11.5px;color:#98a2b3;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + mo + '</div></div>' +
    '<span style="font-size:12.5px;font-weight:700;color:' + (on ? '#0f766e' : '#a0a6b4') + '">' + (on ? 'BẬT' : 'TẮT') + '</span></div>';
}

function cdBoThem(ds, ma) {
  var i = ds.indexOf(ma);
  if (i >= 0) ds.splice(i, 1); else ds.push(ma);
}

async function cdLuu() {
  busy(true);
  try {
    cdData = await api('vagabond.ban_hang.luu_cai_dat_cuoi_ngay', {
      bat: cdBat, gio: cdGio, ghi_so: JSON.stringify(cdGhiSo), hddt: JSON.stringify(cdHddt)
    });
    busy(false);
    toast('Đã lưu. Cuối ngày chạy lúc ' + (cdData.gio || cdGio) + '.', 3500);
    go(scrCaiDatCuoiNgay, true);
  } catch (e) { busy(false); baoTin((e && e.message) || 'Không lưu được'); }
}

async function cdChay() {
  if (!await xacNhan('Chạy ngay chuỗi cuối ngày cho hôm nay?\n\nMáy sẽ ghi sổ hoá đơn còn nháp, phát hành hoá đơn điện tử rồi ký. Việc này không lùi lại được.')) return;
  busy(true);
  try {
    cdData = await api('vagabond.ban_hang.chay_cuoi_ngay_ngay_bay_gio', {});
    busy(false);
    baoTin(cdData.nhat_ky || 'Đã chạy xong.');
    go(scrCaiDatCuoiNgay, true);
  } catch (e) { busy(false); baoTin((e && e.message) || 'Chạy lỗi'); }
}


/* ===== Cai dat: danh sach diem ban (anh Viet 12/08/2026) =====

Truoc day ba diem ban duoc khai o BA CHO trong ma nguon, con dat ten khac
nhau cho cung mot diem. Mo chi nhanh thu tu la sua code roi deploy. Nay
khai o day, ca he doc chung mot noi. */

var dbDs = null, dbSuaDuoc = 0, dbMo = null, dbMoi = 0, dbNguonCoSan = [];

async function scrDiemBan() {
  frame('Điểm bán', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc cấu hình...</div></div>');
  try {
    var kq = await api('vagabond.diem_ban.danh_sach', {});
    dbDs = kq.diem || []; dbSuaDuoc = kq.sua_duoc ? 1 : 0; dbNguonCoSan = kq.nguon_co_san || dbNguonCoSan;
  } catch (e) {
    frame('Điểm bán', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  dbVe();
}

function dbVe() {
  /* Them mot dong roi bam Back thi dong rong con nam lai trong bo nho, man
     danh sach ve mot the trong nhin rat kho hieu. Don o day. */
  if (dbMoi) { dbDs = (dbDs || []).filter(function (x) { return !!x.ma; }); dbMoi = 0; }
  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">ĐIỂM BÁN</div>' +
    '<div style="font-size:14px;color:#374151;line-height:1.6;margin-top:4px">' +
    'Khai ở đây một lần, cả hệ dùng chung: màn tính tiền, chuỗi cuối ngày, khuyến mãi và báo cáo. ' +
    'Mở chi nhánh mới chỉ cần thêm một dòng, không phải sửa phần mềm.</div></div>';

  html += '<div class="card">' + (dbDs || []).map(function (d, i) {
    var phu = [];
    if (d.quay) phu.push('quầy ' + h(d.quay)); else phu.push('đơn online');
    if (d.dia_chi) phu.push(h(d.dia_chi));
    return '<div data-dbmo="' + i + '" style="display:flex;align-items:center;gap:11px;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
      '<div style="width:42px;height:42px;border-radius:11px;flex:none;background:' + (d.bat ? '#ecfdf5' : '#f3f4f6') +
      ';display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;color:' + (d.bat ? '#047857' : '#9ca3af') + '">' + h(d.ma) + '</div>' +
      '<div style="flex:1;min-width:0"><b style="font-size:14.5px">' + h(d.ten) + '</b>' +
      '<div style="font-size:11.5px;color:#98a2b3;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + phu.join(' · ') + '</div>' +
      '<div style="font-size:11.5px;color:#6b7280;margin-top:2px">' + (d.nguon || []).length + ' nguồn đơn</div></div>' +
      '<span style="font-size:12px;font-weight:700;color:' + (d.bat ? '#0f766e' : '#a0a6b4') + '">' + (d.bat ? 'ĐANG DÙNG' : 'ĐÃ TẮT') + '</span>' +
      '<span style="color:#c8ccd4">›</span></div>';
  }).join('') + '</div>';

  html += '<div style="font-size:11.5px;color:#98a2b3;padding:8px 14px;line-height:1.6">' +
    'Điểm bán đã có hoá đơn thì không xoá được, chỉ tắt. Số liệu cũ vẫn xem lại được trong báo cáo.</div>';

  var b = frame('Điểm bán', html, dbSuaDuoc ? {
    footer: '<button class="btn gh" id="dbThem" style="margin:0">➕ Thêm điểm bán</button>'
  } : null);

  b.onclick = function (e) {
    var t = e.target.closest('[data-dbmo]');
    if (t) { dbMo = +t.getAttribute('data-dbmo'); go(scrDiemBanSua); }
  };
  var n = document.getElementById('dbThem');
  if (n) n.onclick = function () {
    dbDs.push({ ma: '', ten: '', ten_ngan: '', quay: '', dia_chi: '', mst: '', ky_hieu: '', nguon: [], bat: 1, thu_tu: dbDs.length + 1 });
    dbMo = dbDs.length - 1;
    dbMoi = 1;
    go(scrDiemBanSua);
  };
}

function scrDiemBanSua() {
  var d = (dbDs || [])[dbMo];
  if (!d) return go(scrDiemBan, true);
  var moi = !d.ma;
  var o = function (nhan, id, gt, mo, kieu) {
    return '<div style="padding:11px 14px;border-bottom:1px solid #f2f4f7">' +
      '<div style="font-size:12px;color:#6b7280;margin-bottom:4px">' + nhan + '</div>' +
      '<input class="tin" id="' + id + '" type="' + (kieu || 'text') + '" value="' + h(gt || '') + '" style="width:100%;margin:0">' +
      (mo ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:4px;line-height:1.5">' + mo + '</div>' : '') + '</div>';
  };

  var html = '<div class="card">' +
    o('Mã điểm bán', 'dbMa', d.ma, 'Chữ không dấu và số, ví dụ SALES, TCV, NVHTN. Mã đi vào báo cáo nên đặt xong thì đừng đổi.') +
    o('Tên đầy đủ', 'dbTen', d.ten, 'Hiện trên màn Cài đặt và chuỗi cuối ngày.') +
    o('Tên ngắn', 'dbTenNgan', d.ten_ngan, 'Hiện trên chip và cột báo cáo cho gọn.') +
    o('Địa chỉ', 'dbDiaChi', d.dia_chi) +
    o('Mã số thuế chi nhánh', 'dbMst', d.mst, 'Để trống thì dùng mã số thuế công ty.') +
    o('Ký hiệu hoá đơn điện tử', 'dbKyHieu', d.ky_hieu, 'Để trống thì dùng ký hiệu chung.') +
    '</div>';

  /* Khong cho nhap ma quay rieng: ca he quy hoa don ve diem ban bang cach
     doc vgb_quay roi tra theo MA DIEM. De hai thu lech nhau la bao cao ra
     dong 0 dong con doanh thu that gom vao mot khoa khong ten. */
  html += '<div class="sec">Loại điểm bán</div><div class="card" style="padding:11px 12px">' +
    kmHangChip(
      posChipNut('data-dbloai="1"', '🏬 Bán tại quầy', !!d.co_quay) +
      posChipNut('data-dbloai="0"', '🛵 Nhận đơn online', !d.co_quay)) +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px;line-height:1.6">' +
    (d.co_quay
      ? 'Mã quầy dùng đúng mã điểm bán là <b>' + h(d.ma || '(chưa đặt mã)') + '</b>.'
      : 'Đơn online không mang mã quầy. Cả hệ chỉ có <b>một</b> điểm nhận đơn online.') +
    '</div></div>';

  html += '<div class="sec">Nguồn đơn thuộc điểm bán này</div><div class="card" style="padding:12px">' +
    dbChipNguon(d) +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:10px;line-height:1.6">' +
    'Một nguồn gán được cho nhiều điểm bán, kể cả điểm nhận đơn online. ' +
    'Hoá đơn quy về điểm nào là đọc theo mã quầy chứ không theo tên nguồn, nên dùng chung không làm lệch số liệu. ' +
    'Nguồn dùng chung thì màn Nhập đơn tay sẽ hỏi chọn điểm bán trước khi lưu.</div></div>';

  html += '<div class="card" style="padding:11px 12px">' + kmHangChip(
    posChipNut('data-dbbat="1"', d.bat ? '● Đang dùng' : '○ Đã tắt', !!d.bat)) +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px">Tắt thì điểm bán không hiện ở màn tính tiền và chuỗi cuối ngày nữa, nhưng số liệu cũ vẫn còn nguyên trong báo cáo.</div></div>';

  var b = frame(moi ? 'Điểm bán mới' : ('Điểm bán ' + d.ma), html, {
    footer: '<div style="display:flex;gap:8px">' +
      '<button class="btn gh" id="dbBo" style="margin:0;flex:0 0 34%;color:#b3261e;border-color:#fecaca">Bỏ dòng này</button>' +
      '<button class="btn" id="dbLuu" style="margin:0;flex:1">💾 Lưu</button></div>'
  });

  b.onclick = async function (e) {
    if (e.target.closest('[data-dbbat]')) { dbDoc(); d.bat = d.bat ? 0 : 1; return go(scrDiemBanSua, true); }
    var t = e.target.closest('[data-dbloai]');
    if (t) { dbDoc(); d.co_quay = t.getAttribute('data-dbloai') === '1' ? 1 : 0; return go(scrDiemBanSua, true); }
    t = e.target.closest('[data-dbng]');
    if (t) {
      dbDoc();
      if (dbBamNguon(t.getAttribute('data-dbng'), d)) go(scrDiemBanSua, true);
      return;
    }
    if (e.target.closest('[data-dbngmoi]')) {
      dbDoc();
      var v = await promptSheet('Tên nguồn đơn mới',
        'Gõ đúng từng chữ như nguồn đơn ghi trên hoá đơn, ví dụ Tiệc đặt hay Bán buôn. Tại chỗ và Mang về đã có sẵn, dùng chung cho mọi điểm bán.');
      if (v === null) return;
      v = v.trim();
      if (!v) return;
      if ((d.nguon || []).indexOf(v) >= 0) return toast('Nguồn này đã có sẵn rồi.');
      if (dbBamNguon(v, d)) go(scrDiemBanSua, true);
      return;
    }
  };
  /* Phai boc lai: gan thang dbLuu thi onclick truyen su kien vao tham so
     daBo, luon truthy, dbDoc() khong bao gio chay - bam Luu la mat sach
     thay doi ma man hinh van bao "Da luu". */
  document.getElementById('dbLuu').onclick = function () { dbLuu(); };
  document.getElementById('dbBo').onclick = async function () {
    var ok = await confirmSheet('Bỏ điểm bán ' + (d.ma || 'mới') + '?',
      'Nếu điểm này đã có hoá đơn thì máy chủ sẽ chặn - lúc đó anh chị tắt nó đi thay vì bỏ.', 'Bỏ dòng này', true);
    if (!ok) return;
    dbDs.splice(dbMo, 1);
    dbLuu(1);
  };
}

function dbDoc() {
  var d = (dbDs || [])[dbMo];
  if (!d) return;
  var v = function (id) { var e = document.getElementById(id); return e ? e.value.trim() : ''; };
  d.ma = v('dbMa').toUpperCase();
  d.ten = v('dbTen');
  d.ten_ngan = v('dbTenNgan');
  d.quay = d.co_quay ? d.ma : '';
  d.dia_chi = v('dbDiaChi');
  d.mst = v('dbMst');
  d.ky_hieu = v('dbKyHieu');
  /* Nguon don gio la chip bam chon, khong con o go tay - dbDoc chi hut
     may o input, khong duoc dung vao d.nguon. */
  d.nguon = d.nguon || [];
}

async function dbLuu(daBo) {
  if (!daBo) dbDoc();
  busy(true);
  try {
    var kq = await api('vagabond.diem_ban.luu', { diem: JSON.stringify(dbDs) });
    dbDs = kq.diem || []; dbSuaDuoc = kq.sua_duoc ? 1 : 0; dbNguonCoSan = kq.nguon_co_san || dbNguonCoSan;
    busy(false);
    toast('Đã lưu danh sách điểm bán.', 3000);
    dbMoi = 0;
    back();
  } catch (e) {
    busy(false);
    /* May chu chan thi phai doc lai danh sach that, khong de man hinh giu
       ban sai trong bo nho roi lan sau luu de len. */
    baoTin((e && e.message) || 'Không lưu được');
    /* May chu chan thi doc lai danh sach that. Khong quay ve ngay: nguoi
       dung con dang sua do, phai o lai de sua tiep cho dung. */
    try {
      var lai = await api('vagabond.diem_ban.danh_sach', {});
      dbDs = lai.diem || []; dbSuaDuoc = lai.sua_duoc ? 1 : 0; dbNguonCoSan = lai.nguon_co_san || dbNguonCoSan;
      if (dbMo >= dbDs.length) dbMo = Math.max(0, dbDs.length - 1);
    } catch (e2) { }
    go(scrDiemBanSua, true);
  }
}


/* ===== Cai dat: khoa so theo ngay (anh Viet 12/08/2026) =====

Hoc tu Fabi muc 3.7. Truoc day hoa don da ghi so van sua duoc vo thoi han
mien co ma OTP - nghia la so lieu thang truoc, da nop thue, da doi soat
voi ngan hang, van doi duoc ma khong ai hay. */

var ksData = null, ksNgay = 0, ksDen = '';

async function scrKhoaSo() {
  frame('Khoá sổ', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc cấu hình...</div></div>');
  try { ksData = await api('vagabond.chung_tu.cai_dat_khoa_so', {}); }
  catch (e) {
    frame('Khoá sổ', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  ksNgay = ksData.so_ngay || 0;
  ksDen = ksData.den || '';
  ksVe();
}

function ksVe() {
  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">KHOÁ SỔ</div>' +
    '<div style="font-size:14px;color:#374151;line-height:1.6;margin-top:4px">' +
    'Chứng từ của ngày đã khoá thì không ghi sổ, không huỷ, không sửa được nữa - ' +
    'trên app hay trên máy tính đều vậy. Cần sửa một tờ cũ thì kế toán mở khoá riêng tờ đó, ' +
    'máy ghi lại lý do và tên người mở.</div></div>';

  if (ksData.ngay_khoa) {
    html += '<div class="card" style="padding:12px 14px;background:#ecfdf5;border:1px solid #a7f3d0">' +
      '<b style="font-size:14.5px;color:#047857">🔒 Đang khoá đến hết ' + ngayNgan(ksData.ngay_khoa) + '</b>' +
      '<div style="font-size:12.5px;color:#065f46;margin-top:3px;line-height:1.6">' +
      'Mọi chứng từ từ ngày đó trở về trước đều đã chốt.</div></div>';
  } else {
    html += '<div class="card" style="padding:12px 14px;background:#fff7ed;border:1px solid #fed7aa">' +
      '<b style="font-size:14.5px;color:#9a3412">⚠️ Chưa khoá gì</b>' +
      '<div style="font-size:12.5px;color:#7c2d12;margin-top:3px;line-height:1.6">' +
      'Hoá đơn của tháng trước vẫn sửa và huỷ được như thường.</div></div>';
  }

  html += '<div class="sec">Tự khoá sau bao nhiêu ngày</div><div class="card" style="padding:11px 12px">' +
    kmHangChip([
      { v: 0, t: 'Không khoá' }, { v: 3, t: '3 ngày' }, { v: 7, t: '7 ngày' },
      { v: 15, t: '15 ngày' }, { v: 31, t: '31 ngày' }
    ].map(function (x) {
      return posChipNut('data-ksn="' + x.v + '"', x.t, ksNgay === x.v);
    }).join('')) +
    '<div style="display:flex;gap:8px;align-items:center;margin-top:9px">' +
    '<span style="font-size:12.5px;color:#6b7280">Số ngày khác:</span>' +
    '<input class="tin" id="ksNgayTay" type="number" min="0" max="3650" value="' + ksNgay + '" style="flex:1;max-width:120px">' +
    '</div>' +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px;line-height:1.6">' +
    'Đặt 3 ngày nghĩa là hôm nay không đụng được vào chứng từ của 3 ngày trước trở về trước. ' +
    'Đủ để kế toán xử lý sai sót trong tuần mà vẫn chặn việc sửa số của kỳ đã chốt.</div></div>';

  html += '<div class="sec">Mốc khoá cứng</div><div class="card" style="padding:11px 12px">' +
    '<input class="tin" id="ksDenTay" type="date" value="' + h(ksDen) + '" max="' + ksHomQua() + '" style="width:100%;margin:0">' +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px;line-height:1.6">' +
    'Dùng sau khi chốt sổ một kỳ: đặt ngày cuối kỳ vào đây thì kỳ đó khoá vĩnh viễn, ' +
    'không trôi theo ngày như ô trên. Để trống nếu chưa cần.</div></div>';

  if (ksData.so_to_dang_mo) {
    html += '<div class="card" style="padding:12px 14px;background:#fef2f2;border:1px solid #fecaca">' +
      '<b style="font-size:14px;color:#991b1b">Đang có ' + ksData.so_to_dang_mo + ' hoá đơn được mở khoá</b>' +
      '<div style="font-size:12.5px;color:#7f1d1d;margin-top:3px;line-height:1.6">' +
      'Sửa xong nhớ đóng lại, không thì mấy tờ đó vẫn sửa được mãi.</div></div>';
  }

  html += '<div style="font-size:11.5px;color:#98a2b3;padding:8px 14px;line-height:1.6">' +
    'Áp dụng cho: ' + h((ksData.loai || []).join(', ')) + '.</div>';

  var b = frame('Khoá sổ', html, ksData.sua_duoc ? {
    footer: '<button class="btn" id="ksLuu" style="margin:0">💾 Lưu cấu hình khoá sổ</button>'
  } : null);

  b.onclick = function (e) {
    var t = e.target.closest('[data-ksn]');
    if (t) { ksDoc(); ksNgay = +t.getAttribute('data-ksn'); ksVe(); }
  };
  var n = document.getElementById('ksLuu');
  if (n) n.onclick = function () { ksLuu(); };
}

function ksHomQua() {
  /* Moc cung khong duoc dat vao hom nay: dat vao la khoa luon so cua hom
     nay, quay khong chot duoc bill nao. */
  var d = new Date(); d.setDate(d.getDate() - 1);
  var s2 = function (n) { return (n < 10 ? '0' : '') + n; };
  return d.getFullYear() + '-' + s2(d.getMonth() + 1) + '-' + s2(d.getDate());
}

function ksDoc() {
  var a = document.getElementById('ksNgayTay');
  var c = document.getElementById('ksDenTay');
  if (a && a.value !== '') ksNgay = Math.max(0, Math.min(3650, +a.value || 0));
  if (c) ksDen = c.value || '';
}

async function ksLuu() {
  ksDoc();
  var nhac = ksNgay === 0 && !ksDen
    ? 'Bỏ khoá hoàn toàn? Hoá đơn của mọi ngày sẽ sửa và huỷ được lại như cũ.'
    : 'Khoá sổ' + (ksNgay ? ' sau ' + ksNgay + ' ngày' : '') + (ksDen ? ', mốc cứng ' + ngayNgan(ksDen) : '') + '?';
  var ok = await confirmSheet('Lưu cấu hình khoá sổ', nhac + '\nÁp dụng ngay cho cả app lẫn máy tính.', 'Lưu', ksNgay === 0 && !ksDen);
  if (!ok) return;
  busy(true);
  try {
    ksData = await api('vagabond.chung_tu.luu_khoa_so', { so_ngay: ksNgay, den: ksDen });
    ksNgay = ksData.so_ngay || 0; ksDen = ksData.den || '';
    busy(false);
    toast(ksData.ngay_khoa ? ('Đã khoá đến hết ' + ngayNgan(ksData.ngay_khoa)) : 'Đã bỏ khoá sổ.', 3500);
    ksVe();
  } catch (e) { busy(false); baoTin((e && e.message) || 'Không lưu được'); }
}


/* ===== Cai dat: phuong thuc thanh toan (anh Viet 12/08/2026) =====

Truoc day mot phuong thuc phai khai o SAU cho trong ma nguon: bang tham
chieu, danh sach cho quay, danh sach cho don online, hai danh sach tien
chua ve, va bang ma gui co quan thue. Them mot may ca the moi la sua sau
cho roi deploy - quen mot cho thi lech so ma khong ai bao loi ngay. */

var ptDs = null, ptSuaDuoc = 0, ptTienVe = [], ptMo = null, ptMoi = 0;

async function scrPtThanhToan() {
  frame('Phương thức thanh toán', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc cấu hình...</div></div>');
  try {
    var kq = await api('vagabond.pt_thanh_toan.danh_sach', {});
    ptDs = kq.pt || []; ptSuaDuoc = kq.sua_duoc ? 1 : 0; ptTienVe = kq.tien_ve || [];
  } catch (e) {
    frame('Phương thức thanh toán', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  ptVe();
}

function ptNhanTienVe(k) {
  for (var i = 0; i < ptTienVe.length; i++) if (ptTienVe[i].k === k) return ptTienVe[i].ten;
  return k;
}

function ptVe() {
  if (ptMoi) { ptDs = (ptDs || []).filter(function (x) { return !!x.ten; }); ptMoi = 0; }
  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">PHƯƠNG THỨC THANH TOÁN</div>' +
    '<div style="font-size:14px;color:#374151;line-height:1.6;margin-top:4px">' +
    'Khai ở đây một lần, cả hệ dùng chung: màn tính tiền tại quầy, đơn online, màn chốt ca ' +
    'và mã hình thức thanh toán gửi sang cơ quan thuế.</div></div>';

  html += '<div class="card">' + (ptDs || []).map(function (d, i) {
    var noi = [];
    if (d.quay) noi.push('quầy');
    if (d.online) noi.push('đơn online');
    if (!noi.length) noi.push('theo nguồn đơn của sàn');
    return '<div data-ptmo="' + i + '" style="display:flex;align-items:center;gap:11px;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
      (d.lg
        ? '<img src="' + h(d.lg) + '" style="width:38px;height:38px;object-fit:contain;flex:none" onerror="this.style.visibility=\'hidden\'">'
        : '<div style="width:38px;height:38px;flex:none;display:flex;align-items:center;justify-content:center;font-size:22px">' + (d.ic || '💳') + '</div>') +
      '<div style="flex:1;min-width:0"><b style="font-size:14.5px">' + h(d.ten) + '</b>' +
      '<div style="font-size:11.5px;color:#98a2b3">' + noi.join(' · ') +
      (d.bat ? ' · bắt buộc nhập mã' : '') + '</div>' +
      '<div style="font-size:11.5px;color:#6b7280;margin-top:2px">' + h(ptNhanTienVe(d.tien_ve)) +
      (d.minvoice ? ' · thuế ' + h(d.minvoice) : '') + '</div></div>' +
      '<span style="font-size:12px;font-weight:700;color:' + (d.dung ? '#0f766e' : '#a0a6b4') + '">' + (d.dung ? 'ĐANG DÙNG' : 'ĐÃ TẮT') + '</span>' +
      '<span style="color:#c8ccd4">›</span></div>';
  }).join('') + '</div>';

  html += '<div style="font-size:11.5px;color:#98a2b3;padding:8px 14px;line-height:1.6">' +
    'Phương thức đã có hoá đơn thì không bỏ khỏi danh sách được, chỉ tắt. Hoá đơn cũ vẫn đọc được.</div>';

  var b = frame('Phương thức thanh toán', html, ptSuaDuoc ? {
    footer: '<button class="btn gh" id="ptThem" style="margin:0">➕ Thêm phương thức</button>'
  } : null);

  b.onclick = function (e) {
    var t = e.target.closest('[data-ptmo]');
    if (t) { ptMo = +t.getAttribute('data-ptmo'); go(scrPtSua); }
  };
  var n = document.getElementById('ptThem');
  if (n) n.onclick = function () {
    ptDs.push({ ten: '', lg: '', ic: '💳', quay: 1, online: 0, bat: 0, nhan: '', vd: '', mau: '', loi: '', tien_ve: 'ngay', minvoice: 'CK', dung: 1, thu_tu: ptDs.length + 1 });
    ptMo = ptDs.length - 1; ptMoi = 1;
    go(scrPtSua);
  };
}

function scrPtSua() {
  var d = (ptDs || [])[ptMo];
  if (!d) return go(scrPtThanhToan, true);
  var o = function (nhan, id, gt, mo) {
    return '<div style="padding:11px 14px;border-bottom:1px solid #f2f4f7">' +
      '<div style="font-size:12px;color:#6b7280;margin-bottom:4px">' + nhan + '</div>' +
      '<input class="tin" id="' + id + '" value="' + h(gt || '') + '" style="width:100%;margin:0">' +
      (mo ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:4px;line-height:1.5">' + mo + '</div>' : '') + '</div>';
  };

  var html = '<div class="card">' +
    o('Tên phương thức', 'ptTen', d.ten, 'Tên này ghi thẳng vào từng hoá đơn, đặt xong thì đừng đổi.') +
    o('Đường dẫn logo', 'ptLg', d.lg, 'Để trống thì dùng biểu tượng bên dưới.') +
    o('Biểu tượng', 'ptIc', d.ic, 'Dùng khi không có logo.') +
    '</div>';

  html += '<div class="sec">Hiện ở đâu</div><div class="card" style="padding:11px 12px">' +
    kmHangChip(
      posChipNut('data-ptq="1"', '🏬 Màn tính tiền tại quầy', !!d.quay) +
      posChipNut('data-pto="1"', '🛵 Đơn online', !!d.online)) +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px;line-height:1.6">' +
    'Tắt cả hai nghĩa là phương thức này đi theo nguồn đơn của sàn, không hiện ra cho ai chọn tay.</div></div>';

  html += '<div class="sec">Tiền về lúc nào</div><div class="card" style="padding:11px 12px">' +
    kmHangChip(ptTienVe.map(function (x) {
      return posChipNut('data-pttv="' + h(x.k) + '"', x.ten, d.tien_ve === x.k);
    }).join('')) +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px;line-height:1.6">' +
    'Màn Chốt ca tách riêng hai loại sau để thu ngân đếm tiền mặt không bị lệch.</div></div>';

  html += '<div class="sec">Mã tham chiếu đối soát</div><div class="card">' +
    '<div style="padding:11px 12px;border-bottom:1px solid #f2f4f7">' +
    kmHangChip(posChipNut('data-ptbat="1"', d.bat ? '● Bắt buộc nhập' : '○ Không bắt buộc', !!d.bat)) + '</div>' +
    o('Nhãn ô nhập', 'ptNhan', d.nhan, 'Câu hiện trên màn cho thu ngân biết phải gõ gì.') +
    o('Ví dụ', 'ptVd', d.vd) +
    o('Mẫu kiểm định dạng', 'ptMau', d.mau, 'Để trống thì không kiểm. Gõ sai mẫu thì máy chặn ngay lúc lưu cấu hình.') +
    o('Câu báo khi sai dạng', 'ptLoi', d.loi) +
    '</div>';

  html += '<div class="sec">Gửi sang cơ quan thuế</div><div class="card" style="padding:11px 12px">' +
    kmHangChip(['TM', 'CK', 'TM/CK', ''].map(function (m) {
      return posChipNut('data-ptmi="' + m + '"', m || 'Không gửi', (d.minvoice || '') === m);
    }).join('')) +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px;line-height:1.6">' +
    'TM là tiền mặt, CK là chuyển khoản. Ghi sai thì tờ hoá đơn điện tử sai hình thức thanh toán.</div></div>';

  html += '<div class="card" style="padding:11px 12px">' +
    kmHangChip(posChipNut('data-ptdung="1"', d.dung ? '● Đang dùng' : '○ Đã tắt', !!d.dung)) + '</div>';

  var b = frame(d.ten ? ('Sửa ' + d.ten) : 'Phương thức mới', html, {
    footer: '<div style="display:flex;gap:8px">' +
      '<button class="btn gh" id="ptBo" style="margin:0;flex:0 0 34%;color:#b3261e;border-color:#fecaca">Bỏ dòng này</button>' +
      '<button class="btn" id="ptLuu" style="margin:0;flex:1">💾 Lưu</button></div>'
  });

  b.onclick = function (e) {
    var t;
    if (e.target.closest('[data-ptq]')) { ptDoc(); d.quay = d.quay ? 0 : 1; return go(scrPtSua, true); }
    if (e.target.closest('[data-pto]')) { ptDoc(); d.online = d.online ? 0 : 1; return go(scrPtSua, true); }
    if (e.target.closest('[data-ptbat]')) { ptDoc(); d.bat = d.bat ? 0 : 1; return go(scrPtSua, true); }
    if (e.target.closest('[data-ptdung]')) { ptDoc(); d.dung = d.dung ? 0 : 1; return go(scrPtSua, true); }
    t = e.target.closest('[data-pttv]');
    if (t) { ptDoc(); d.tien_ve = t.getAttribute('data-pttv'); return go(scrPtSua, true); }
    t = e.target.closest('[data-ptmi]');
    if (t) { ptDoc(); d.minvoice = t.getAttribute('data-ptmi'); return go(scrPtSua, true); }
  };
  document.getElementById('ptLuu').onclick = function () { ptLuu(); };
  document.getElementById('ptBo').onclick = async function () {
    var ok = await confirmSheet('Bỏ phương thức ' + (d.ten || 'mới') + '?',
      'Nếu phương thức này đã có hoá đơn thì máy chủ sẽ chặn - lúc đó anh chị tắt nó đi thay vì bỏ.', 'Bỏ dòng này', true);
    if (!ok) return;
    ptDs.splice(ptMo, 1);
    ptLuu(1);
  };
}

function ptDoc() {
  var d = (ptDs || [])[ptMo];
  if (!d) return;
  var v = function (id) { var e = document.getElementById(id); return e ? e.value.trim() : null; };
  var g;
  if ((g = v('ptTen')) !== null) d.ten = g;
  if ((g = v('ptLg')) !== null) d.lg = g;
  if ((g = v('ptIc')) !== null) d.ic = g;
  if ((g = v('ptNhan')) !== null) d.nhan = g;
  if ((g = v('ptVd')) !== null) d.vd = g;
  if ((g = v('ptMau')) !== null) d.mau = g;
  if ((g = v('ptLoi')) !== null) d.loi = g;
}

async function ptLuu(daBo) {
  if (!daBo) ptDoc();
  busy(true);
  try {
    var kq = await api('vagabond.pt_thanh_toan.luu', { pt: JSON.stringify(ptDs) });
    ptDs = kq.pt || []; ptSuaDuoc = kq.sua_duoc ? 1 : 0;
    busy(false);
    toast('Đã lưu phương thức thanh toán.', 3000);
    ptMoi = 0;
    back();
  } catch (e) {
    busy(false);
    baoTin((e && e.message) || 'Không lưu được');
    try {
      var lai = await api('vagabond.pt_thanh_toan.danh_sach', {});
      ptDs = lai.pt || []; ptSuaDuoc = lai.sua_duoc ? 1 : 0;
      if (ptMo >= ptDs.length) ptMo = Math.max(0, ptDs.length - 1);
    } catch (e2) { }
    go(scrPtSua, true);
  }
}

/* ---------- Cai dat: Quyen tai quay (anh Viet 12/08/2026) ----------
   Hoc theo ba muc quyen bo mon cua Fabi. Man nay chi doi mot cai cong
   tac, nhung doi no la doi cach ca quay lam viec nen phai noi that ro
   moi muc nghia la gi, va noi luon dieu gi KHONG doi. */
var qqData = null, qqChon = '';

async function scrQuyenQuay() {
  frame('Quyền tại quầy', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc cấu hình...</div></div>');
  try { qqData = await api('vagabond.quyen_quay.cai_dat', {}); }
  catch (e) {
    frame('Quyền tại quầy', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  qqChon = qqData.muc || 'duyet';
  qqVe();
}

function qqVe() {
  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">QUYỀN BỎ MÓN CỦA THU NGÂN</div>' +
    '<div style="font-size:14px;color:#374151;line-height:1.6;margin-top:4px">' +
    'Mốc để tính là lúc bấm <b>In tạm tính</b>: từ đó trở đi tờ phiếu đã nằm trong tay ' +
    'khách, món biến mất khỏi bill là lệch với tờ khách đang cầm.</div></div>';

  html += '<div class="card">' + (qqData.ds || []).map(function (x) {
    var on = qqChon === x.k;
    return '<div data-qqm="' + h(x.k) + '" style="display:flex;gap:11px;padding:13px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer;background:' + (on ? '#f0fdfa' : '#fff') + '">' +
      '<div style="flex:none;font-size:19px;line-height:1.2;color:' + (on ? '#0f766e' : '#c8ccd4') + '">' + (on ? '◉' : '○') + '</div>' +
      '<div style="flex:1;min-width:0">' +
      '<b style="font-size:14.5px;color:' + (on ? '#0f766e' : '#101828') + '">' + h(x.ten) + '</b>' +
      '<div style="font-size:12.5px;color:#6b7280;margin-top:3px;line-height:1.6">' + h(x.mo) + '</div>' +
      '</div></div>';
  }).join('') + '</div>';

  html += '<div class="card" style="padding:12px 14px;background:#f8fafc">' +
    '<div style="font-size:12px;color:#98a2b3">MỨC NÀO CŨNG KHÔNG ĐỔI</div>' +
    '<div style="font-size:12.5px;color:#475467;line-height:1.7;margin-top:4px">' +
    '· Huỷ nguyên một bill vẫn luôn cần mã OTP của quản lý ca.<br>' +
    '· Hoá đơn đã ghi sổ thì không sửa được món ở quầy, mức nào cũng vậy.<br>' +
    '· Mọi lần sửa đều ghi lại tên người sửa vào lịch sử hoá đơn.<br>' +
    '· Quản lý tự thao tác thì không phải gõ mã.</div></div>';

  var b = frame('Quyền tại quầy', html, qqData.sua_duoc ? {
    footer: '<button class="btn" id="qqLuu" style="margin:0">💾 Lưu mức quyền</button>'
  } : null);

  if (!qqData.sua_duoc) return;
  b.onclick = function (e) {
    var t = e.target.closest('[data-qqm]');
    if (t) { qqChon = t.getAttribute('data-qqm'); return qqVe(); }
  };
  document.getElementById('qqLuu').onclick = function () { qqLuu(); };
}

async function qqLuu() {
  busy(true);
  try {
    qqData = await api('vagabond.quyen_quay.luu', { muc_moi: qqChon });
    qqChon = qqData.muc || 'duyet';
    CFGBH = null; /* man tinh tien phai doc lai muc quyen moi */
    busy(false);
    toast('Đã lưu mức quyền tại quầy.', 3000);
    qqVe();
  } catch (e) {
    busy(false);
    baoTin((e && e.message) || 'Không lưu được');
  }
}

/* ---------- Chip chon nguon don cho man Diem ban (anh Viet 12/08/2026) ----------
   Truoc day la o go tay tung dong. Go thieu mot dau la nguon do khong khop
   voi hoa don nao ca, ma khong ai bao loi - hoa don cu the nam ngoai moi
   diem ban, cuoi ngay khong ai ghi so cho no. */
/* Nguon nay dang thuoc diem nao. Tinh tren danh sach dang sua trong bo nho
   chu khong tinh tren ban may chu doc luc mo man: go mot nguon khoi diem A
   roi gan sang diem B la viec rat thuong, ban cu se chan nham. */
/* Cac diem KHAC dang giu nguon nay. Tra ve mang ma diem.
   Tu 15/08/2026 khong con diem nao bi CHAN gan nguon: moi nguon deu dung
   chung duoc cho moi diem, ke ca diem nhan don online (anh Viet). Ca he
   quy hoa don ve diem ban bang ma quay chu khong bang ten nguon, va khoa
   xuat hoa don dien tu cung dem theo ma quay, nen dung chung khong con lam
   lech so lieu. */
function dbChuNguon(v, d) {
  var ds = dbDs || [], ra = [];
  for (var i = 0; i < ds.length; i++) {
    if (ds[i] === d) continue;
    if ((ds[i].nguon || []).indexOf(v) >= 0) ra.push(ds[i].ma || '(chưa đặt mã)');
  }
  return ra;
}

function dbChipNguon(d) {
  var dang = (d.nguon || []).slice();
  var co = (dbNguonCoSan || []).slice();

  /* Truoc 12/08/2026 cho nay goi y "Tại chỗ - <tên điểm>" va "Mang về -
     <tên điểm>". Nay hai nguon do gom lai thanh "Tại chỗ" va "Mang về"
     dung chung cho moi quay, da nam san trong bang mau nen khong sinh
     theo ten diem nua. */
  /* Nguon dang gan cho diem nay ma bang tra chua co (vua go tay xong) */
  dang.forEach(function (n) {
    if (!co.some(function (x) { return x.v === n; })) co.push({ v: n, lg: '', ic: '🧾' });
  });

  /* Chip chi hien DUNG TEN NGUON, khong dinh them ma diem vao duoi.
     Anh Viet 15/08/2026: *"Ten diem ban trong phan cai dat cung sua lai
     thay vi 'Tai cho - TCV' va 'Mang ve - TCV' thi thanh 'Tai cho' va
     'Mang ve'"*. Nguon nao dang dung chung thi ghi thanh mot dong chu o
     duoi khoi chip, de nguoi doc van biet ma chip khong bi dai ra. */
  var html = co.map(function (x) {
    var on = dang.indexOf(x.v) >= 0;
    var anh = x.lg
      ? '<img src="' + h(x.lg) + '" style="height:17px;border-radius:3px;background:#fff;padding:1px 2px" onerror="this.style.display=\'none\'">'
      : '<span style="font-size:15px">' + (x.ic || '🧾') + '</span>';
    return '<button data-dbng="' + h(x.v) + '" style="display:inline-flex;align-items:center;gap:7px;' +
      'border:1.5px solid ' + (on ? '#0d9488' : '#d7dce5') + ';background:' + (on ? '#0d9488' : '#fff') +
      ';color:' + (on ? '#fff' : '#374151') +
      ';border-radius:999px;padding:8px 14px;font-size:13.5px;font-weight:' + (on ? '800' : '600') +
      ';cursor:pointer;white-space:nowrap;line-height:1.2">' + anh + h(x.v) + '</button>';
  }).join('');

  html += '<button data-dbngmoi="1" style="display:inline-flex;align-items:center;gap:6px;border:1.5px dashed #b9c0cc;' +
    'background:#fff;color:#475467;border-radius:999px;padding:8px 14px;font-size:13.5px;font-weight:600;' +
    'cursor:pointer;white-space:nowrap;line-height:1.2">➕ Nguồn khác</button>';

  var chung = [];
  dang.forEach(function (v) {
    var k = dbChuNguon(v, d);
    if (k.length) chung.push(v + ' dùng chung với ' + k.join(', '));
  });
  return kmHangChip(html) +
    (chung.length
      ? '<div style="font-size:11.5px;color:#6b7280;margin-top:9px;line-height:1.6">' + h(chung.join(' · ')) + '</div>'
      : '') +
    (dang.length
      ? ''
      : '<div style="font-size:12px;color:#b45309;margin-top:9px;font-weight:600">Chưa chọn nguồn nào. Điểm bán không có nguồn thì không nhận được hoá đơn nào.</div>');
}

/* Bam mot chip nguon: gan vao diem dang sua, hoac go ra. */
function dbBamNguon(v, d) {
  var i = (d.nguon || []).indexOf(v);
  if (i >= 0) { d.nguon.splice(i, 1); return 1; }
  d.nguon = (d.nguon || []).concat([v]);
  var k = dbChuNguon(v, d);
  if (k.length) {
    toast('Nguồn "' + v + '" giờ dùng chung với điểm ' + k.join(', ') +
      '. Đơn nhập tay nguồn này sẽ hỏi chọn điểm bán trước khi lưu.', 5000);
  }
  return 1;
}

/* ---------- Cai dat: Hang thanh vien (anh Viet 12/08/2026) ----------
   Ba hang chay tu dong theo chi tieu (EXPLORER, VOYAGER, VAGABONDER) va
   cac hang gan tay (AMBASSADOR, FAMILY). Moi hang co muc giam gia va ty le
   tich diem rieng; 1 diem = 1 dong, giu dung quy uoc cu ben Fabi de khach
   khong phai doi thoi quen. */
var htData = null, htDs = [], htMo = null, htMoi = 0, htSuaDuoc = 0;

async function scrHangKhach() {
  frame('Hạng thành viên', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc bảng hạng...</div></div>');
  try {
    htData = await api('vagabond.khach_hang.cai_dat_hang', {});
    htDs = htData.hang || []; htSuaDuoc = htData.sua_duoc ? 1 : 0;
  } catch (e) {
    frame('Hạng thành viên', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  try { cdDiem = await api('vagabond.diem_han.cai_dat', {}); } catch (e) { cdDiem = null; }
  htVe();
}

/* ---------- Cài đặt điểm: quy đổi, trần, OTP, hạn điểm ----------
   Anh Việt hỏi 16/08/2026 "phần này vào nút cài đặt nào", và câu trả lời
   thật lúc đó là "chưa vào nút nào cả" - các ô này mới chỉ sửa được trong
   bản quản trị Frappe. Một cài đặt mà chủ tiệm không tự mở được thì coi
   như không có, nên đưa lên đây, ngay trên bảng hạng.

   Hạn điểm để mặc định TẮT và không tự bật: xoá điểm của 43.000 khách là
   việc phải có người bấm. */
var cdDiem = null;

function cdDiemVe() {
  if (!cdDiem) return '';
  var d = cdDiem;
  function o(nhan, id, gt, chu, kieu) {
    return '<div style="flex:1;min-width:150px"><div style="font-size:11px;color:#6b7280;margin-bottom:3px">' +
      h(nhan) + '</div><input id="' + id + '" type="' + (kieu || 'number') + '" value="' + h(String(gt)) +
      '" style="width:100%;box-sizing:border-box;border:1.5px solid #d1d5db;border-radius:8px;padding:7px 9px;font-size:13.5px">' +
      (chu ? '<div style="font-size:10.5px;color:#9ca3af;margin-top:2px">' + h(chu) + '</div>' : '') + '</div>';
  }
  var chon = d.cach_co_the.map(function (c) {
    var ten = { 'Tat': 'Tắt - điểm không bao giờ hết hạn', 'Cuon chieu': 'Cuộn chiếu - mỗi bút sống N tháng',
                'Cuoi nam': 'Cuối năm - xoá sạch vào ngày chốt', 'Ngay ky niem': 'Ngày kỷ niệm của từng khách' }[c] || c;
    return '<option value="' + h(c) + '"' + (d.chu_ky === c ? ' selected' : '') + '>' + h(ten) + '</option>';
  }).join('');
  return '<div style="border:1.5px solid #e5e7eb;border-radius:13px;padding:12px 13px;margin-bottom:13px;background:#fff">' +
    '<div style="font-weight:800;font-size:14px;margin-bottom:9px">Điểm thành viên</div>' +
    '<div style="display:flex;gap:9px;flex-wrap:wrap">' +
      o('1 điểm bằng bao nhiêu đồng', 'cdQuyDoi', d.quy_doi) +
      o('Tối đa % bill trả bằng điểm', 'cdTran', d.tran_pt) +
      o('Bill sau khi trừ không dưới (đ)', 'cdToiThieu', d.bill_toi_thieu) +
      o('Mã OTP sống (giây)', 'cdGiay', d.otp_giay, 'nên để 180') +
    '</div>' +
    (d.gia_lap ? '<div style="margin-top:9px;padding:8px 10px;border-radius:8px;background:#fffbeb;' +
      'border:1.5px solid #fde68a;font-size:12px;color:#78350f">Chế độ chạy thử đang bật: mã KHÔNG gửi tới ' +
      'điện thoại khách, nên trừ điểm ở quầy chưa hoàn tất được. ' +
      (d.co_mau_zns ? 'Tắt chế độ chạy thử trong bản quản trị để chạy thật.' : 'Chưa khai mã mẫu ZNS.') + '</div>' : '') +
    '<div style="height:1px;background:#eef0f3;margin:12px 0"></div>' +
    '<div style="font-weight:800;font-size:14px;margin-bottom:9px">Hạn điểm và hạ hạng</div>' +
    '<div style="display:flex;gap:9px;flex-wrap:wrap;align-items:flex-end">' +
      '<div style="flex:2;min-width:210px"><div style="font-size:11px;color:#6b7280;margin-bottom:3px">Cách tính hạn điểm</div>' +
      '<select id="cdChuKy" style="width:100%;box-sizing:border-box;border:1.5px solid #d1d5db;border-radius:8px;padding:7px 9px;font-size:13.5px">' +
      chon + '</select></div>' +
      o('Điểm sống bao nhiêu tháng', 'cdHanThang', d.han_thang) +
      o('Ngày chốt hằng năm', 'cdNgayChot', d.ngay_chot, 'dạng 31-12', 'text') +
    '</div>' +
    '<label style="display:flex;align-items:center;gap:8px;margin-top:10px;font-size:12.5px;cursor:pointer">' +
      '<input type="checkbox" id="cdTungBac"' + (d.ha_hang_tung_bac ? ' checked' : '') + '>' +
      '<span>Hạ hạng mỗi kỳ chỉ một bậc <span style="color:#9ca3af">- khách tụt chi tiêu nhiều vẫn chỉ xuống một hạng. Lên hạng thì vẫn lên thẳng.</span></span></label>' +
    '<div style="display:flex;gap:8px;margin-top:11px;align-items:center">' +
      '<button id="cdLuuDiem" style="border:0;background:#0f766e;color:#fff;border-radius:9px;padding:8px 15px;font-size:13px;font-weight:700">Lưu cài đặt điểm</button>' +
      '<button id="cdThuHan" style="border:1.5px solid #d1d5db;background:#fff;color:#374151;border-radius:9px;padding:8px 13px;font-size:13px">Chạy thử hạn điểm</button>' +
    '</div></div>';
}

function cdDiemGan() {
  var n = document.getElementById('cdLuuDiem');
  if (n) n.onclick = async function () {
    busy(true);
    try {
      cdDiem = await api('vagabond.diem_han.luu_cai_dat', {
        quy_doi: (document.getElementById('cdQuyDoi') || {}).value,
        tran_pt: (document.getElementById('cdTran') || {}).value,
        bill_toi_thieu: (document.getElementById('cdToiThieu') || {}).value,
        otp_giay: (document.getElementById('cdGiay') || {}).value,
        chu_ky: (document.getElementById('cdChuKy') || {}).value,
        han_thang: (document.getElementById('cdHanThang') || {}).value,
        ngay_chot: (document.getElementById('cdNgayChot') || {}).value,
        ha_hang_tung_bac: (document.getElementById('cdTungBac') || {}).checked ? 1 : 0
      });
      busy(false); toast('Đã lưu cài đặt điểm'); htVe();
    } catch (e) { busy(false); }
  };
  var t = document.getElementById('cdThuHan');
  /* Chạy thử KHÔNG ghi gì. Nút này để anh xem trước đêm nay máy sẽ đốt
     điểm của bao nhiêu khách, trước khi bật hạn điểm. */
  if (t) t.onclick = async function () {
    busy(true);
    try {
      var kq = await api('vagabond.diem_han.het_han', {});
      busy(false);
      baoTin(kq.ghi_chu ? kq.ghi_chu :
        ('Cách ' + kq.cach + ': hôm nay sẽ đốt điểm của ' + money(kq.so_khach || 0) +
         ' khách, tổng ' + money(kq.tong_diem || 0) + ' điểm. Đây là bản chạy thử, chưa ghi gì.'));
    } catch (e) { busy(false); }
  };
}

function htTien(n) { return money(n) + ' đ'; }

/* Anh the thanh vien cua mot hang (anh Viet 12/08/2026).

   Truoc day moi hang deo mot bieu tuong chung chung, nhin ba hang theo chi
   tieu deu ra mot cai 📈 giong nhau. Nay dung dung file the ma ben thiet ke
   da lam: mau nen cua the la thu de phan biet nhanh nhat, ke ca khi thu
   nho con hai ba chuc diem anh.

   Chua khai anh thi roi ve bieu tuong cu chu khong de o trong: hang moi
   them tren app chua kip lam the van phai nhin ra duoc. */
function hangThe(hg, rong) {
  var r = rong || 46;
  var c = Math.round(r / 1.586);
  var tay = ((hg && hg.loai) || 'Theo chi tieu') === 'Gan tay';
  var khung = 'width:' + r + 'px;height:' + c + 'px;flex:none;border-radius:6px;';
  if (hg && hg.anh) {
    return '<img src="' + h(hg.anh) + '" alt="' + h(hg.ten_hang || '') + '" style="' + khung +
      'object-fit:cover;border:1px solid #e5e7eb;background:#f2f4f7" loading="lazy">';
  }
  return '<div style="' + khung + 'display:flex;align-items:center;justify-content:center;' +
    'background:' + (tay ? '#fef3c7' : '#ccfbf1') + ';font-size:' + Math.round(c * 0.5) + 'px">' +
    (tay ? '✋' : '📈') + '</div>';
}

/* Chip hang co anh the o dau. Dung o man Danh muc khach hang va bang gan
   hang, nhung noi chi co cho cho mot chip ngan. */
function hangChipAnh(hg, cao) {
  var c = cao || 15;
  var r = Math.round(c * 1.586);
  if (!hg || !hg.anh) return '';
  return '<img src="' + h(hg.anh) + '" alt="" style="width:' + r + 'px;height:' + c +
    'px;flex:none;border-radius:3px;object-fit:cover;background:#fff;margin-right:5px;vertical-align:-2px" loading="lazy">';
}

function htVe() {
  var theoCt = htDs.filter(function (x) { return (x.loai || 'Theo chi tieu') === 'Theo chi tieu'; });
  var moc = {}, trung = '';
  theoCt.forEach(function (x) {
    var k = String(x.chi_tieu_tu || 0);
    if (moc[k]) trung = moc[k] + ' và ' + x.ten_hang;
    moc[k] = x.ten_hang;
  });

  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">HẠNG THÀNH VIÊN</div>' +
    '<div style="font-size:14px;color:#374151;line-height:1.6;margin-top:4px">' +
    'Hạng <b>theo chi tiêu</b> máy tự xét lại mỗi đêm theo tiền khách đã mua trong kỳ. ' +
    'Hạng <b>gán tay</b> thì máy không bao giờ đụng vào: nhân viên, đại sứ, người nhà.</div></div>';

  if (trung) {
    html += '<div class="card" style="padding:12px 14px;background:#fef2f2;border:1px solid #fecaca">' +
      '<b style="font-size:14.5px;color:#b42318">⚠️ Chưa chạy xét lại được</b>' +
      '<div style="font-size:12.5px;color:#7f1d1d;margin-top:3px;line-height:1.6">' +
      'Hạng ' + h(trung) + ' đang cùng một mức chi tiêu nên máy không biết xếp khách vào đâu. ' +
      'Đặt mốc khác nhau cho từng hạng rồi lưu lại.</div></div>';
  }

  html += cdDiemVe();

  html += '<div class="card">' + htDs.map(function (d, i) {
    var tay = (d.loai || 'Theo chi tieu') === 'Gan tay';
    var phu = [];
    if (tay) phu.push('gán tay');
    else phu.push('từ ' + htTien(d.chi_tieu_tu || 0));
    if (d.giam_gia) phu.push('giảm ' + d.giam_gia + '%');
    phu.push(d.tich_diem ? ('tích ' + d.tich_diem + '%') : 'không tích điểm');
    return '<div data-htmo="' + i + '" style="display:flex;align-items:center;gap:11px;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
      hangThe(d, 58) +
      '<div style="flex:1;min-width:0"><b style="font-size:14.5px">' + h(d.ten_hang) + '</b>' +
      '<div style="font-size:11.5px;color:#98a2b3">' + h(phu.join(' · ')) + '</div>' +
      '<div style="font-size:11.5px;color:#6b7280;margin-top:2px">' + money(d.so_khach || 0) + ' khách</div></div>' +
      '<span style="font-size:12px;font-weight:700;color:' + (d.bat ? '#0f766e' : '#a0a6b4') + '">' + (d.bat ? 'ĐANG DÙNG' : 'ĐÃ TẮT') + '</span>' +
      '<span style="color:#c8ccd4">›</span></div>';
  }).join('') + '</div>';

  html += '<div style="font-size:11.5px;color:#98a2b3;padding:8px 14px;line-height:1.6">' +
    money(htData.chua_xep || 0) + ' khách chưa xếp hạng. Tích điểm tính trên giá trị hoá đơn, 1 điểm bằng 1 đồng.</div>';

  html += '<div class="card" style="padding:12px 14px">' +
    '<button class="btn gh" id="htXet" style="margin:0">🔁 Xét lại hạng hàng loạt</button>' +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:8px;line-height:1.6">' +
    'Xem trước ai lên ai xuống rồi mới áp. Máy không đụng vào khách đang đeo hạng gán tay.</div></div>';

  var b = frame('Hạng thành viên', html, htSuaDuoc ? {
    footer: '<button class="btn gh" id="htThem" style="margin:0">➕ Thêm hạng</button>'
  } : null);

  b.onclick = function (e) {
    var t = e.target.closest('[data-htmo]');
    if (t) { htMo = +t.getAttribute('data-htmo'); go(scrHangSua); }
  };
  document.getElementById('htXet').onclick = function () { go(scrXetLaiHang); };
  var n = document.getElementById('htThem');
  if (n) n.onclick = function () {
    htDs.push({ ten_hang: '', thu_tu: htDs.length + 1, loai: 'Theo chi tieu', giam_gia: 0, tich_diem: 0, chi_tieu_tu: 0, so_thang_xet: 12, bat: 1, mo_ta: '', anh: '', so_khach: 0 });
    htMo = htDs.length - 1; htMoi = 1;
    go(scrHangSua);
  };
  cdDiemGan();
}

function scrHangSua() {
  var d = (htDs || [])[htMo];
  if (!d) return go(scrHangKhach, true);
  var tay = (d.loai || 'Theo chi tieu') === 'Gan tay';
  var o = function (nhan, id, gt, mo, kieu) {
    return '<div style="padding:11px 14px;border-bottom:1px solid #f2f4f7">' +
      '<div style="font-size:12px;color:#6b7280;margin-bottom:4px">' + nhan + '</div>' +
      '<input class="tin" id="' + id + '" type="' + (kieu || 'text') + '" value="' + h(gt == null ? '' : gt) + '" style="width:100%;margin:0">' +
      (mo ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:4px;line-height:1.5">' + mo + '</div>' : '') + '</div>';
  };

  var html = '<div class="card">' +
    o('Tên hạng', 'htTen', d.ten_hang, 'Tên này in lên bill và hiện cho khách. Đặt xong thì đừng đổi.') +
    o('Thứ tự', 'htThuTu', d.thu_tu, 'Nhỏ là hạng thấp.', 'number') +
    '</div>';

  html += '<div class="sec">Cách lên hạng</div><div class="card" style="padding:11px 12px">' +
    kmHangChip(
      posChipNut('data-htloai="Theo chi tieu"', '📈 Theo chi tiêu', !tay) +
      posChipNut('data-htloai="Gan tay"', '✋ Gán tay', tay)) +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px;line-height:1.6">' +
    (tay
      ? 'Máy không bao giờ tự gán hay tự gỡ hạng này. Dùng cho nhân viên, đại sứ, người nhà.'
      : 'Mỗi đêm máy tính lại tiền khách đã mua trong kỳ rồi xếp hạng theo mốc bên dưới.') +
    '</div></div>';

  if (!tay) {
    html += '<div class="card">' +
      o('Chi tiêu từ (đ)', 'htChiTieu', d.chi_tieu_tu, 'Khách mua đủ mức này trong kỳ thì lên hạng. Hạng thấp nhất để 0.', 'number') +
      o('Kỳ xét (tháng)', 'htThang', d.so_thang_xet, 'Anh Việt chốt 12 tháng: hạng xét lại theo chu kỳ chứ không giữ vĩnh viễn.', 'number') +
      '</div>';
  }

  /* Anh the thanh vien (anh Viet 12/08/2026). De cong khai chu khong rieng
     tu: the con phai hien duoc tren trang thanh vien va trong tin nhan gui
     cho khach, khong chi trong app noi bo. */
  html += '<div class="sec">Thẻ thành viên</div><div class="card" style="padding:12px 14px">' +
    '<div id="htAnhXem" style="display:flex;align-items:center;gap:12px">' +
    hangThe(d, 132) +
    '<div style="flex:1;min-width:0;font-size:12px;color:#98a2b3;line-height:1.6">' +
    (d.anh ? 'Ảnh thẻ đang dùng cho hạng này.' : 'Chưa có ảnh thẻ, app đang hiện biểu tượng chung.') +
    '</div></div>' +
    '<div style="display:flex;gap:8px;margin-top:11px">' +
    '<button class="btn gh" id="htAnhChon" style="margin:0;flex:1">🖼 Chọn ảnh thẻ</button>' +
    (d.anh ? '<button class="btn gh" id="htAnhBo" style="margin:0;flex:0 0 34%;color:#b3261e;border-color:#fecaca">Bỏ ảnh</button>' : '') +
    '</div>' +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:8px;line-height:1.6">' +
    'Ảnh ngang theo tỉ lệ thẻ, khoảng 1012 x 638 điểm ảnh.</div></div>';

  html += '<div class="sec">Quyền lợi</div><div class="card">' +
    o('Giảm giá (%)', 'htGiam', d.giam_gia, 'Áp cho mọi hoá đơn của khách hạng này.', 'number') +
    o('Tích điểm (%)', 'htDiem', d.tich_diem, htGoiYDiem(d), 'number') +
    o('Mô tả quyền lợi', 'htMoTa', d.mo_ta, 'Câu này hiện cho khách xem trên trang thành viên.') +
    '</div>';

  html += '<div class="card" style="padding:11px 12px">' +
    kmHangChip(posChipNut('data-htbat="1"', d.bat ? '● Đang dùng' : '○ Đã tắt', !!d.bat)) +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px">Tắt thì hạng này không nhận khách mới nữa, khách cũ vẫn giữ nguyên hạng.</div></div>';

  var b = frame(d.ten_hang ? ('Hạng ' + d.ten_hang) : 'Hạng mới', html, htSuaDuoc ? {
    footer: '<div style="display:flex;gap:8px">' +
      '<button class="btn gh" id="htBo" style="margin:0;flex:0 0 34%;color:#b3261e;border-color:#fecaca">Bỏ hạng này</button>' +
      '<button class="btn" id="htLuu" style="margin:0;flex:1">💾 Lưu</button></div>'
  } : null);

  b.onclick = function (e) {
    var t = e.target.closest('[data-htloai]');
    if (t) { htDoc(); d.loai = t.getAttribute('data-htloai'); return go(scrHangSua, true); }
    if (e.target.closest('[data-htbat]')) { htDoc(); d.bat = d.bat ? 0 : 1; return go(scrHangSua, true); }
  };
  if (!htSuaDuoc) return;
  var nAnh = document.getElementById('htAnhChon');
  if (nAnh) nAnh.onclick = function () { htChonAnh(); };
  var nBo = document.getElementById('htAnhBo');
  if (nBo) nBo.onclick = function () { htDoc(); d.anh = ''; go(scrHangSua, true); };
  document.getElementById('htLuu').onclick = function () { htLuu(); };
  document.getElementById('htBo').onclick = async function () {
    var ok = await confirmSheet('Bỏ hạng ' + (d.ten_hang || 'mới') + '?',
      'Hạng đang có khách thì máy chủ sẽ chặn - lúc đó anh chị tắt nó đi thay vì bỏ.', 'Bỏ hạng này', true);
    if (!ok) return;
    htDs.splice(htMo, 1);
    htLuu(1);
  };
}

/* Chon anh the cho mot hang. De CONG KHAI vi the con phai hien tren trang
   thanh vien va trong tin nhan gui khach, khong chi trong app noi bo. Chua
   luu hang thi da tai anh len roi: bam Luu moi gan vao, bo giua chung thi
   anh nam lai trong kho tep chu khong hong gi. */
async function htChonAnh() {
  var d = (htDs || [])[htMo];
  if (!d) return;
  htDoc();
  var inp = document.createElement('input');
  inp.type = 'file';
  inp.accept = 'image/*';
  inp.onchange = async function () {
    var f = inp.files && inp.files[0];
    inp.remove();
    if (!f) return;
    busy(true);
    try {
      var fd = new FormData();
      fd.append('file', f, f.name);
      fd.append('is_private', '0');
      fd.append('folder', 'Home');
      var hd = {};
      hd['X-Frappe-' + 'CSRF-' + 'Token'] = frappe.csrf_token;
      var r = await fetch('/api/method/upload_file', { method: 'POST', headers: hd, body: fd });
      var j = await r.json();
      if (!r.ok || !j.message || !j.message.file_url) throw new Error('Không tải được ảnh lên');
      d.anh = j.message.file_url;
      busy(false);
      go(scrHangSua, true);
      toast('Đã chọn ảnh thẻ, bấm Lưu để áp dụng');
    } catch (e) {
      busy(false);
      baoTin((e && e.message) || 'Không tải được ảnh lên');
    }
  };
  inp.style.display = 'none';
  document.body.appendChild(inp);
  inp.click();
}

/* Dong goi y ngay duoi o Tich diem, giong Fabi: go % xong thay ngay mot hoa
   don 500.000 d thi khach duoc bao nhieu diem. */
function htGoiYDiem(d) {
  var p = htSo(d.tich_diem);
  if (!p) return '1 điểm bằng 1 đồng. Để 0 là hạng này không tích điểm.';
  return 'Hoá đơn 500.000 đ được <b>' + money(Math.round(500000 * p / 100)) + ' điểm</b>. 1 điểm bằng 1 đồng.';
}
/* Rieng cho man Hang thanh vien: nhan ca dau phay thap phan vi o nhap la
   type=number nhung ban phim dien thoai VN hay ra dau phay. KHONG dat ten
   flt0 - ten do da co san hai cho trong file, dinh nghia them mot cai nua
   la de len ca hai, doi hanh vi cua nhung cho khong lien quan. */
function htSo(v) { var n = parseFloat(String(v == null ? '' : v).replace(',', '.')); return isNaN(n) ? 0 : n; }

function htDoc() {
  var d = (htDs || [])[htMo];
  if (!d) return;
  var v = function (id) { var e = document.getElementById(id); return e ? e.value.trim() : null; };
  var g;
  if ((g = v('htTen')) !== null) d.ten_hang = g;
  if ((g = v('htThuTu')) !== null) d.thu_tu = parseInt(g, 10) || 0;
  if ((g = v('htChiTieu')) !== null) d.chi_tieu_tu = htSo(g);
  if ((g = v('htThang')) !== null) d.so_thang_xet = parseInt(g, 10) || 12;
  if ((g = v('htGiam')) !== null) d.giam_gia = htSo(g);
  if ((g = v('htDiem')) !== null) d.tich_diem = htSo(g);
  if ((g = v('htMoTa')) !== null) d.mo_ta = g;
}

async function htLuu(daBo) {
  if (!daBo) htDoc();
  busy(true);
  try {
    htData = await api('vagabond.khach_hang.luu_hang', { hang: JSON.stringify(htDs) });
    htDs = htData.hang || []; htSuaDuoc = htData.sua_duoc ? 1 : 0;
    busy(false);
    toast('Đã lưu bảng hạng thành viên.', 3000);
    htMoi = 0;
    back();
  } catch (e) {
    busy(false);
    baoTin((e && e.message) || 'Không lưu được');
    try {
      var lai = await api('vagabond.khach_hang.cai_dat_hang', {});
      htData = lai; htDs = lai.hang || []; htSuaDuoc = lai.sua_duoc ? 1 : 0;
      if (htMo >= htDs.length) htMo = Math.max(0, htDs.length - 1);
    } catch (e2) { }
    go(scrHangSua, true);
  }
}

/* ---------- Xet lai hang hang loat ---------- */
var xlData = null;

async function scrXetLaiHang() {
  frame('Xét lại hạng', '<div class="emp"><div class="e1">⏳</div><div>Đang tính chi tiêu của cả tiệm...</div></div>');
  try { xlData = await api('vagabond.khach_hang.xet_lai', { ap: 0, so_khach: 400 }); }
  catch (e) {
    frame('Xét lại hạng', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không chạy được') + '</div></div>');
    return;
  }
  xlVe();
}

function xlVe() {
  var doi = xlData.doi || [];
  var html = '';
  if (xlData.loi_nhac) {
    html += '<div class="card" style="padding:12px 14px;background:#fef2f2;border:1px solid #fecaca">' +
      '<b style="font-size:14.5px;color:#b42318">⚠️ Chưa chạy được</b>' +
      '<div style="font-size:12.5px;color:#7f1d1d;margin-top:3px;line-height:1.6">' + h(xlData.loi_nhac) + '</div></div>';
    frame('Xét lại hạng', html);
    return;
  }

  /* Lay so dem tu may chu: may chu dem tren toan bo tap, con "doi" o day
     chi la phan dau da bi cat de man hinh khong treo. */
  var len = xlData.so_len == null ? doi.filter(function (x) { return x.len; }).length : xlData.so_len;
  var xuong = xlData.so_xuong == null ? Math.max(0, (xlData.tong || 0) - len) : xlData.so_xuong;
  html += '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">KẾT QUẢ XÉT LẠI</div>' +
    '<div style="font-size:14px;color:#374151;line-height:1.6;margin-top:4px">' +
    'Tính theo tiền khách đã mua trong <b>' + (xlData.so_thang || 12) + ' tháng</b> gần nhất. ' +
    'Có <b>' + money(xlData.tong || 0) + ' khách</b> lệch hạng: ' + money(len) + ' lên, ' +
    money(xuong) + ' xuống. Khách đeo hạng gán tay không bị đụng tới.</div></div>';

  if (!doi.length) {
    html += '<div class="emp"><div class="e1">✅</div><div>Không ai lệch hạng. Bảng hạng đang khớp với chi tiêu thật.</div></div>';
    frame('Xét lại hạng', html);
    return;
  }

  html += '<div class="card">' + doi.map(function (x) {
    return '<div style="display:flex;align-items:center;gap:10px;padding:11px 14px;border-bottom:1px solid #f2f4f7">' +
      '<div style="flex:none;font-size:17px">' + (x.len ? '⬆️' : '⬇️') + '</div>' +
      '<div style="flex:1;min-width:0"><b style="font-size:14px">' + h(x.ten) + '</b>' +
      '<div style="font-size:11.5px;color:#98a2b3">' + htTien(x.tien) + ' trong kỳ</div></div>' +
      '<div style="text-align:right;font-size:12px">' +
      '<span style="color:#98a2b3">' + h(x.tu || 'chưa xếp') + '</span><br>' +
      '<b style="color:' + (x.len ? '#0f766e' : '#b45309') + '">' + h(x.sang) + '</b></div></div>';
  }).join('') + '</div>';

  if ((xlData.tong || 0) > doi.length) {
    html += '<div style="font-size:11.5px;color:#b45309;padding:8px 14px;font-weight:600">' +
      'Màn hình chỉ hiện ' + money(doi.length) + ' khách đầu, nhưng bấm áp là đổi đủ cả ' + money(xlData.tong) + ' khách.</div>';
  }

  var b = frame('Xét lại hạng', html, htSuaDuoc ? {
    footer: '<button class="btn" id="xlAp" style="margin:0">Áp cho ' + money(xlData.tong || 0) + ' khách</button>'
  } : null);
  var n = document.getElementById('xlAp');
  if (n) n.onclick = async function () {
    var ok = await confirmSheet('Đổi hạng cho ' + money(xlData.tong || 0) + ' khách?',
      'Hạng cũ không lưu lại ở đâu để quay về. Xem kỹ danh sách trên rồi hãy bấm.', 'Áp hạng mới', true);
    if (!ok) return;
    busy(true);
    try {
      var kq = await api('vagabond.khach_hang.xet_lai', { ap: 1, so_khach: 1 });
      busy(false);
      toast('Đã đổi hạng cho ' + money(kq.da_ap || 0) + ' khách.', 4000);
      back();
    } catch (e) { busy(false); baoTin((e && e.message) || 'Không áp được'); }
  };
}


/* ---------- Cai dat: Tai khoan nhan chuyen khoan (anh Viet 12/08/2026) ----------

   Truoc day so tai khoan nam trong ma nguon: mot tai khoan ao MBBank cho
   ca ba diem ban va moi nguon don. Ke toan doc sao ke thi moi giao dich do
   ve mot cho, muon biet tien cua quay nao phai lan theo noi dung chuyen
   khoan - ma noi dung la thu thu ngan go tay, go thieu la mat dau.

   Nay khai duoc tai khoan RIENG cho tung nguon don. Nguon nao chua khai
   thi dung tai khoan mac dinh, tuc chay y nhu cu. */
var tkData = null, tkMo = -1, tkMoi = 0;

async function scrTaiKhoan() {
  frame('Tài khoản nhận tiền', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc cấu hình...</div></div>');
  try { tkData = await api('vagabond.tai_khoan.danh_sach', {}); }
  catch (e) {
    frame('Tài khoản nhận tiền', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  tkVe();
}

/* Muc dich dac biet nhu phieu doi no khai chung bang voi nguon don, nhung
   phai hien ra bang chu nguoi doc hieu chu khong phai ma noi bo. */
function tkNhan(v) {
  var ds = (tkData && tkData.nguon) || [];
  for (var i = 0; i < ds.length; i++) if (ds[i].v === v) return ds[i].nhan || v;
  return v;
}
function tkIcon(v) {
  var ds = (tkData && tkData.nguon) || [];
  for (var i = 0; i < ds.length; i++) if (ds[i].v === v) return ds[i].ic || '🏦';
  return '🏦';
}
function tkMoTa(v) {
  var ds = (tkData && tkData.nguon) || [];
  for (var i = 0; i < ds.length; i++) if (ds[i].v === v) return ds[i].mo || '';
  return '';
}

function tkTenNh(ma) {
  var ds = (tkData && tkData.ngan_hang) || [];
  for (var i = 0; i < ds.length; i++) if (ds[i].bin === ma || ds[i].ma === ma) return ds[i].ten;
  return ma || '';
}

function tkOSelect(id, chon) {
  var ds = (tkData && tkData.ngan_hang) || [];
  var op = '<option value="">- Chọn ngân hàng -</option>';
  for (var i = 0; i < ds.length; i++) {
    var v = ds[i].bin;
    var on = (chon === ds[i].bin || chon === ds[i].ma) ? ' selected' : '';
    op += '<option value="' + h(v) + '"' + on + '>' + h(ds[i].ten) + '</option>';
  }
  return '<select class="tin" id="' + id + '" style="width:100%;margin:0">' + op + '</select>';
}

function tkONhap(nhan, id, gt, mo) {
  return '<div style="padding:11px 14px;border-bottom:1px solid #f2f4f7">' +
    '<div style="font-size:12px;color:#6b7280;margin-bottom:4px">' + nhan + '</div>' +
    '<input class="tin" id="' + id + '" value="' + h(gt || '') + '" style="width:100%;margin:0">' +
    (mo ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:4px;line-height:1.5">' + mo + '</div>' : '') + '</div>';
}

function tkVe() {
  var md = (tkData && tkData.mac_dinh) || {};
  var ds = (tkData && tkData.theo_nguon) || [];
  var sua = tkData && tkData.sua_duoc;

  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">TÀI KHOẢN NHẬN CHUYỂN KHOẢN</div>' +
    '<div style="font-size:14px;color:#374151;line-height:1.6;margin-top:4px">' +
    'Mọi mã QR chuyển khoản của hệ sinh từ đây: màn tính tiền tại quầy, màn nhập đơn tay, ' +
    'chi tiết đơn Sales, phiếu tạm tính in cho khách và phiếu đòi công nợ.<br>' +
    'Khai tài khoản ảo riêng cho từng điểm bán thì sao kê ngân hàng tự tách sẵn, ' +
    'kế toán không phải lần theo nội dung chuyển khoản nữa. Tiền vẫn về tài khoản chính.</div></div>';

  html += '<div class="sec">Tài khoản mặc định</div><div class="card">' +
    '<div style="padding:11px 14px;border-bottom:1px solid #f2f4f7">' +
    '<div style="font-size:12px;color:#6b7280;margin-bottom:4px">Ngân hàng</div>' +
    tkOSelect('tkMdBank', md.bank || '') + '</div>' +
    tkONhap('Số tài khoản', 'tkMdStk', md.stk, 'Tài khoản ảo MB Bank cũng điền vào đây.') +
    tkONhap('Tên chủ tài khoản', 'tkMdTen', md.ten, 'Viết không dấu, đúng như ngân hàng đang ghi.') +
    '</div>' +
    '<div style="font-size:11.5px;color:#98a2b3;padding:8px 14px;line-height:1.6">' +
    'Nguồn đơn nào chưa khai riêng thì tiền về tài khoản này.</div>';

  html += '<div class="sec">Tài khoản riêng theo điểm bán và nguồn đơn</div>';
  if (!ds.length) {
    html += '<div class="card" style="padding:14px;font-size:13.5px;color:#6b7280;line-height:1.6">' +
      'Chưa khai dòng nào. Cả hệ đang dùng chung tài khoản mặc định.</div>';
  } else {
    html += '<div class="card">' + ds.map(function (t, i) {
      return '<div data-tkmo="' + i + '" style="display:flex;align-items:center;gap:11px;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
        '<div style="width:34px;flex:none;text-align:center;font-size:20px">' + h(tkIcon(t.nguon)) + '</div>' +
        '<div style="flex:1;min-width:0"><b style="font-size:14.5px">' + h(tkNhan(t.nguon)) + '</b>' +
        '<div style="font-size:11.5px;color:#6b7280;margin-top:2px">' + h(tkTenNh(t.bank)) + ' · ' + h(t.stk || 'chưa có số') + '</div></div>' +
        '<span style="font-size:12px;font-weight:700;color:' + (t.dung ? '#0f766e' : '#a0a6b4') + '">' + (t.dung ? 'ĐANG DÙNG' : 'ĐÃ TẮT') + '</span>' +
        '<span style="color:#c8ccd4">›</span></div>';
    }).join('') + '</div>';
  }

  var b = frame('Tài khoản nhận tiền', html, sua ? {
    footer: '<div style="display:flex;gap:8px">' +
      '<button class="btn gh" id="tkThem" style="margin:0;flex:0 0 44%">➕ Thêm nguồn</button>' +
      '<button class="btn" id="tkLuuMd" style="margin:0;flex:1">💾 Lưu</button></div>'
  } : null);

  b.onclick = function (e) {
    var t = e.target.closest('[data-tkmo]');
    if (t) { tkDocMd(); tkMo = +t.getAttribute('data-tkmo'); go(scrTaiKhoanSua); }
  };
  var nt = document.getElementById('tkThem');
  if (nt) nt.onclick = function () {
    tkDocMd();
    tkData.theo_nguon.push({ nguon: '', bank: md.bank || '', stk: '', ten: md.ten || '', dung: 1 });
    tkMo = tkData.theo_nguon.length - 1; tkMoi = 1;
    go(scrTaiKhoanSua);
  };
  var nl = document.getElementById('tkLuuMd');
  if (nl) nl.onclick = function () { tkDocMd(); tkLuu(); };
}

function tkDocMd() {
  if (!tkData) return;
  var v = function (id) { var o = document.getElementById(id); return o ? String(o.value).trim() : null; };
  var g;
  if ((g = v('tkMdBank')) !== null) tkData.mac_dinh.bank = g;
  if ((g = v('tkMdStk')) !== null) tkData.mac_dinh.stk = g;
  if ((g = v('tkMdTen')) !== null) tkData.mac_dinh.ten = g;
}

function scrTaiKhoanSua() {
  var t = ((tkData || {}).theo_nguon || [])[tkMo];
  if (!t) return go(scrTaiKhoan, true);
  var nguon = (tkData.nguon || []);

  var html = '<div class="sec">Khai cho điểm bán hay nguồn đơn</div><div class="card" style="padding:11px 12px">' +
    kmHangChip(nguon.map(function (n) {
      /* Nguon da khai o dong KHAC thi khong cho chon lai o day: hai dong
         cung mot nguon la khong ai biet dong nao dang co hieu luc. */
      var ban = 0;
      (tkData.theo_nguon || []).forEach(function (x, i) { if (i !== tkMo && x.nguon === n.v) ban = 1; });
      if (ban) return '';
      return posChipNut('data-tkng="' + h(n.v) + '"', (n.lg ? '' : (n.ic || '🧾') + ' ') + h(n.nhan || n.v), t.nguon === n.v);
    }).join('')) +
    (t.nguon
      ? (tkMoTa(t.nguon) ? '<div style="font-size:12px;color:#0b7c93;margin-top:8px;line-height:1.5">' + h(tkMoTa(t.nguon)) + '</div>' : '')
      : '<div style="font-size:12px;color:#b45309;margin-top:8px">Chọn điểm bán hoặc nguồn đơn trước đã.</div>') +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:8px;line-height:1.6">' +
    'Khai theo điểm bán thì mọi nguồn đơn của điểm đó về chung một tài khoản. ' +
    'Khai theo nguồn đơn thì riêng nguồn ấy tách ra, kể cả khi điểm bán đã có tài khoản riêng.</div>' +
    '</div>';

  html += '<div class="sec">Tài khoản nhận tiền</div><div class="card">' +
    '<div style="padding:11px 14px;border-bottom:1px solid #f2f4f7">' +
    '<div style="font-size:12px;color:#6b7280;margin-bottom:4px">Ngân hàng</div>' +
    tkOSelect('tkBank', t.bank || '') + '</div>' +
    tkONhap('Số tài khoản', 'tkStk', t.stk, 'Dán đúng số tài khoản ảo MB Bank cấp cho dòng này.') +
    tkONhap('Tên chủ tài khoản', 'tkTen', t.ten, 'Để trống thì lấy tên của tài khoản mặc định.') +
    '</div>';

  html += '<div class="card" style="padding:11px 12px">' +
    kmHangChip(posChipNut('data-tkdung="1"', t.dung ? '● Đang dùng' : '○ Đã tắt', !!t.dung)) +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px;line-height:1.6">' +
    'Tắt dòng này thì nguồn đó quay về dùng tài khoản mặc định.</div></div>';

  var b = frame(t.nguon ? ('Tài khoản cho ' + tkNhan(t.nguon)) : 'Nguồn mới', html, {
    footer: '<div style="display:flex;gap:8px">' +
      '<button class="btn gh" id="tkBo" style="margin:0;flex:0 0 34%;color:#b3261e;border-color:#fecaca">Bỏ dòng này</button>' +
      '<button class="btn" id="tkLuu" style="margin:0;flex:1">💾 Lưu</button></div>'
  });

  b.onclick = function (e) {
    var x = e.target.closest('[data-tkng]');
    if (x) { tkDocDong(); t.nguon = x.getAttribute('data-tkng'); return go(scrTaiKhoanSua, true); }
    if (e.target.closest('[data-tkdung]')) { tkDocDong(); t.dung = t.dung ? 0 : 1; return go(scrTaiKhoanSua, true); }
  };
  document.getElementById('tkLuu').onclick = function () {
    tkDocDong();
    if (!t.nguon) return toast('Chọn nguồn đơn trước đã.');
    tkLuu();
  };
  document.getElementById('tkBo').onclick = async function () {
    var ok = await confirmSheet('Bỏ tài khoản riêng của ' + (t.nguon ? tkNhan(t.nguon) : 'nguồn mới') + '?',
      'Nguồn này sẽ quay về dùng tài khoản mặc định. Giao dịch cũ trong sao kê giữ nguyên.', 'Bỏ dòng này', true);
    if (!ok) return;
    tkData.theo_nguon.splice(tkMo, 1);
    tkLuu(1);
  };
}

function tkDocDong() {
  var t = ((tkData || {}).theo_nguon || [])[tkMo];
  if (!t) return;
  var v = function (id) { var o = document.getElementById(id); return o ? String(o.value).trim() : null; };
  var g;
  if ((g = v('tkBank')) !== null) t.bank = g;
  if ((g = v('tkStk')) !== null) t.stk = g;
  if ((g = v('tkTen')) !== null) t.ten = g;
}

async function tkLuu(daBo) {
  busy(true);
  try {
    var kq = await api('vagabond.tai_khoan.luu', {
      mac_dinh: JSON.stringify(tkData.mac_dinh || {}),
      theo_nguon: JSON.stringify(tkData.theo_nguon || [])
    });
    tkData = kq;
    tkMoi = 0;
    busy(false);
    toast('Đã lưu tài khoản nhận tiền.', 3000);
    /* Cau hinh ban hang dang nam trong bo nho cua app, khong nap lai thi
       man tinh tien van sinh QR vao tai khoan cu cho den luc tai lai trang. */
    CFGBH = null;
    try { await cfgBanHang(); } catch (e2) { }
    if (daBo || tkMo >= 0) { tkMo = -1; return back(); }
    tkVe();
  } catch (e) {
    busy(false);
    baoTin((e && e.message) || 'Không lưu được');
  }
}


/* ---------- Combo co nhom mon cho khach chon (De feedback 12/08/2026) ----------

   Fabi cho tao "nhom" trong combo: 1 mon nuoc trong 2 mon nuoc da cai, 1
   banh trong 4 banh. Thu ngan bam combo thi phai hien hop chon mon truoc,
   chon xong bam OK moi do vao bill - chu khong duoc do thang ca sau mon
   vao hoa don.

   Dong nao khong ghi ten nhom van la mon BAT BUOC, luon vao bill. Combo
   cu khai truoc day khong co nhom nao nen chay y nhu truoc, khong hien
   hop chon. */

function comboKhoa(ma, chon) {
  return ma + '|' + (chon || []).map(function (x) { return x.nhom + '>' + x.item_code; }).sort().join(',');
}

/* Hop chon mon cua combo. xong(chon) duoc goi khi nguoi dung bam OK. */
function posSheetChonCombo(c, xong) {
  var nhom = c.nhom_ds || [];
  if (!nhom.length) { xong([]); return; }
  var da = {};
  nhom.forEach(function (g) { da[g.ten] = []; });

  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';

  function gTT(g) { var v = parseInt(g.toi_thieu, 10); return isNaN(v) ? (g.chon || 1) : v; }
  function gTD(g) { var v = parseInt(g.toi_da, 10); return isNaN(v) || v < 1 ? (g.chon || 1) : v; }
  function duSo() {
    for (var i = 0; i < nhom.length; i++) {
      var n = (da[nhom[i].ten] || []).length;
      if (n < gTT(nhom[i]) || n > gTD(nhom[i])) return 0;
    }
    return 1;
  }

  function ve() {
    var html = '<div class="shh"><b>' + h(c.ten) + '</b><div class="x">&times;</div></div>' +
      '<div style="padding:4px 14px calc(env(safe-area-inset-bottom,0px) + 90px);max-height:76vh;overflow:auto">' +
      '<div style="font-size:12.5px;color:#6b7280;line-height:1.6;margin-bottom:10px">Khách chọn món trong từng nhóm, bấm OK thì máy mới đổ vào hoá đơn.</div>';

    if ((c.bat_buoc || []).length) {
      html += '<div style="font-size:12px;color:#6b7280;font-weight:700;margin:6px 0 6px">CÓ SẴN TRONG COMBO</div>' +
        '<div style="font-size:13.5px;color:#374151;line-height:1.8;margin-bottom:12px">' +
        (c.bat_buoc || []).map(function (m) { return num(m.so_luong) + '× ' + h(m.ten_mon || m.item_code); }).join('<br>') +
        '</div>';
    }

    nhom.forEach(function (g, gi) {
      var chon = da[g.ten] || [];
      var tt = gTT(g), td = gTD(g);
      var xong2 = chon.length >= tt && chon.length <= td;
      html += '<div style="font-size:12px;font-weight:700;margin:12px 0 7px;color:' + (xong2 ? '#0f766e' : '#b45309') + '">' +
        h(g.ten).toUpperCase() + ' · ' + (tt === td ? 'chọn ' + td + ' món' : 'chọn từ ' + tt + ' đến ' + td + ' món') +
        ' <span style="font-weight:600">(' + chon.length + '/' + td + ')</span></div>' +
        (g.mo_ta ? '<div style="font-size:12px;color:#6b7280;margin:-3px 0 7px">' + h(g.mo_ta) + '</div>' : '') +
        '<div style="display:flex;flex-direction:column;gap:7px">';
      (g.mon || []).forEach(function (m, mi) {
        var on = chon.indexOf(m.item_code) >= 0;
        html += '<div data-cbg="' + gi + '" data-cbm="' + mi + '" style="display:flex;align-items:center;gap:10px;border:1.5px solid ' +
          (on ? '#0d9488' : '#e5e7eb') + ';background:' + (on ? '#ccfbf1' : '#fff') +
          ';border-radius:10px;padding:10px 12px;cursor:pointer">' +
          '<span style="font-size:17px">' + (on ? '✅' : '⬜') + '</span>' +
          '<div style="flex:1;min-width:0"><div style="font-size:14px;font-weight:' + (on ? '700' : '600') + '">' + h(m.ten_mon || m.item_code) + '</div>' +
          '<div style="font-size:11.5px;color:#98a2b3">' + num(m.so_luong) + ' phần · giá lẻ ' + money(m.gia_goc) + ' đ</div></div></div>';
      });
      html += '</div>';
    });

    html += '</div><div style="position:sticky;bottom:0;background:#fff;border-top:1px solid #eef0f4;padding:11px 14px calc(env(safe-area-inset-bottom,0px) + 11px)">' +
      '<button class="btn" id="cbcOk" style="width:100%"' + (duSo() ? '' : ' disabled') + '>' +
      (duSo() ? 'OK, thêm vào hoá đơn' : 'Chọn đủ món rồi mới bấm được') + '</button></div>';
    box.innerHTML = html;
    noi();
  }

  function noi() {
    box.querySelector('.x').onclick = function () { ov.remove(); };
    box.querySelectorAll('[data-cbg]').forEach(function (o) {
      o.onclick = function () {
        var g = nhom[+o.getAttribute('data-cbg')];
        var m = (g.mon || [])[+o.getAttribute('data-cbm')];
        if (!g || !m) return;
        var ds = da[g.ten] || [];
        var td = gTD(g);
        var i = ds.indexOf(m.item_code);
        if (i >= 0) ds.splice(i, 1);
        else if (ds.length >= td) {
          if (td === 1) {
            /* Nhom chi cho mot mon: bam mon khac la doi luon, khoi bat thu
               ngan bo tick roi tick lai. */
            ds.length = 0; ds.push(m.item_code);
          } else {
            toast('Nhóm ' + g.ten + ' chỉ được chọn tối đa ' + td + ' món. Bỏ bớt một món rồi chọn lại.', 3200);
            return;
          }
        } else ds.push(m.item_code);
        da[g.ten] = ds;
        ve();
      };
    });
    var ok = box.querySelector('#cbcOk');
    if (ok) ok.onclick = function () {
      if (!duSo()) return;
      var chon = [];
      nhom.forEach(function (g) {
        (da[g.ten] || []).forEach(function (ma) { chon.push({ nhom: g.ten, item_code: ma }); });
      });
      ov.remove();
      xong(chon);
    };
  }

  ve();
  ov.appendChild(box);
  ov.onclick = function (e) { if (e.target === ov) ov.remove(); };
  document.body.appendChild(ov);
}


/* ---------- Cai dat: Danh muc san pham (anh Viet 12/08/2026) ----------

   Man Item goc cua ERPNext hon 80 truong, mo ra khong biet bat dau tu dau.
   Ket qua thay trong du lieu that: 1.428 ma hang, 33 tien to, 27 ma khong
   theo khuon nao, va ca ma ERPNext tu sinh kieu "9ZKKL9YXG7BU".

   Man nay chi hoi BAY thu. Ma hang, ba co mua/ban/ton kho va don vi tinh
   thi may tu dat theo LOAI HANG. */
var dmCai = null, dmVe = null, dmTre = null, dmVuaTao = null, dmNangCao = 0;

async function scrDanhMuc() {
  frame('Danh mục sản phẩm', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc danh mục...</div></div>');
  if (!dmCai) {
    try { dmCai = await api('vagabond.danh_muc.cai_dat', {}); }
    catch (e) {
      dmCai = null;
      frame('Danh mục sản phẩm', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
      return;
    }
  }
  if (!dmVe) dmVe = { nhom: '', loai: 'thanh_pham', ten: '', quy_cach: '', gia: '', bep: '', mo_ta: '', dvt: '', tien_to: '' };
  dmDraw();
}

function dmLoai(k) {
  var ds = (dmCai && dmCai.loai) || [];
  for (var i = 0; i < ds.length; i++) if (ds[i].k === k) return ds[i];
  return ds[0] || { ten: '', mua: 0, ban: 1, ton: 1 };
}

function dmDraw(giuCuon) {
  var s = dmVe, l = dmLoai(s.loai);
  var xin = 'width:100%;box-sizing:border-box;padding:10px 11px;border:1.5px solid #e5e7eb;border-radius:9px;font-size:15px;font-family:inherit';
  var nhan = function (t, phu) {
    return '<div style="font-size:12px;color:#6b7280;margin:12px 0 5px;font-weight:700">' + t +
      (phu ? ' <span style="font-weight:400;color:#98a2b3">' + phu + '</span>' : '') + '</div>';
  };

  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">MỞ MÃ HÀNG MỚI</div>' +
    '<div style="font-size:13.5px;color:#374151;line-height:1.6;margin-top:4px">' +
    'Chỉ điền bảy ô. Mã hàng, đơn vị tính và ba cờ mua - bán - tồn kho thì máy tự đặt theo loại hàng.</div></div>';

  html += '<div class="card" style="padding:4px 14px 14px">';

  html += nhan('1. NHÓM MÓN');
  html += '<select id="dmNhom" style="' + xin + '"><option value="">- Chọn nhóm -</option>' +
    ((dmCai && dmCai.nhom) || []).map(function (n) {
      return '<option value="' + h(n.ten) + '"' + (s.nhom === n.ten ? ' selected' : '') + '>' + h(n.ten) + '</option>';
    }).join('') + '</select>';

  html += nhan('2. LOẠI HÀNG');
  html += kmHangChip(((dmCai && dmCai.loai) || []).map(function (x) {
    return posChipNut('data-dmloai="' + h(x.k) + '"', x.ten, s.loai === x.k);
  }).join(''));
  html += '<div style="font-size:11.5px;color:#98a2b3;margin-top:6px;line-height:1.5">' + h(l.mo || '') + '</div>';
  html += '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:7px">' +
    dmCo('Cho mua', l.mua) + dmCo('Cho bán', l.ban) + dmCo('Quản lý tồn kho', l.ton) + '</div>';

  html += nhan('3. TÊN MẶT HÀNG');
  html += '<input id="dmTen" value="' + h(s.ten) + '" placeholder="Ví dụ: Bánh mì bơ tỏi" style="' + xin + '">';

  html += nhan('4. QUY CÁCH HOẶC SIZE', l.ban ? '(gắn vào tên món)' : '(ghi xuống mô tả)');
  html += '<input id="dmQc" value="' + h(s.quy_cach) + '" placeholder="Ví dụ: 110 gram, size 16cm, hộp 8 cái" style="' + xin + '">';

  html += nhan('5. GIÁ BÁN (đ)', l.ban ? '' : '(loại này không bán, để trống)');
  html += '<input id="dmGia" inputmode="numeric" value="' + h(s.gia) + '" placeholder="0" style="' + xin + '">';

  if (dmCai && dmCai.co_bep) {
    html += nhan('6. BẾP HOẶC VỊ TRÍ', '(nếu khác mặc định của nhóm)');
    html += '<input id="dmBep" value="' + h(s.bep) + '" placeholder="Để trống là theo nhóm món" style="' + xin + '">';
  }

  html += nhan((dmCai && dmCai.co_bep ? '7' : '6') + '. MÔ TẢ NGẮN', '(nếu đã có)');
  html += '<textarea id="dmMoTa" rows="2" placeholder="Để trống thì máy lấy tên món" style="' + xin + '">' + h(s.mo_ta) + '</textarea>';

  html += '<div style="margin-top:12px">' +
    posChipNut('data-dmnc="1"', dmNangCao ? '▾ Ẩn phần nâng cao' : '▸ Phần nâng cao', false) + '</div>';
  if (dmNangCao) {
    html += nhan('ĐƠN VỊ TÍNH GỐC', '(để trống là theo nhóm)');
    html += '<input id="dmDvt" value="' + h(s.dvt) + '" placeholder="' + h((dmKq && dmKq.dvt_goi_y) || 'Cái') + '" style="' + xin + '">';
    html += nhan('TIỀN TỐ MÃ', '(để trống là theo nhóm)');
    html += '<input id="dmTt" value="' + h(s.tien_to) + '" placeholder="' + h((dmKq && dmKq.tien_to) || 'VD BAWS') + '" style="text-transform:uppercase;' + xin + '">';
  }
  html += '</div>';

  html += '<div id="dmXem"></div>';

  var b = frame('Danh mục sản phẩm', html, (dmCai && dmCai.tao_duoc) ? {
    footer: '<button class="btn" id="dmTao" style="margin:0">➕ Tạo mã hàng</button>'
  } : null);

  b.onclick = function (e) {
    var t = e.target.closest('[data-dmloai]');
    if (t) { dmDoc(); dmVe.loai = t.getAttribute('data-dmloai'); return dmDraw(); }
    if (e.target.closest('[data-dmnc]')) { dmDoc(); dmNangCao = dmNangCao ? 0 : 1; return dmDraw(); }
  };
  ['dmTen', 'dmQc'].forEach(function (id) {
    var o = document.getElementById(id);
    if (o) o.oninput = function () { dmDoc(); dmHoiXem(); };
  });
  var on = document.getElementById('dmNhom');
  if (on) on.onchange = function () { dmDoc(); dmHoiXem(); dmDraw(); };
  var nt = document.getElementById('dmTao');
  if (nt) nt.onclick = function () { dmTao(0); };
  dmVeXem();
  dmHoiXem();
}

function dmCo(ten, on) {
  return '<span style="display:inline-block;background:' + (on ? '#ccfbf1' : '#f3f4f6') + ';color:' + (on ? '#0f766e' : '#9ca3af') +
    ';border-radius:999px;padding:3px 11px;font-size:12px;font-weight:700">' + (on ? '✓ ' : '✕ ') + ten + '</span>';
}

function dmDoc() {
  var v = function (id) { var o = document.getElementById(id); return o ? o.value : null; };
  var g;
  if ((g = v('dmNhom')) !== null) dmVe.nhom = g;
  if ((g = v('dmTen')) !== null) dmVe.ten = g;
  if ((g = v('dmQc')) !== null) dmVe.quy_cach = g;
  if ((g = v('dmGia')) !== null) dmVe.gia = g;
  if ((g = v('dmBep')) !== null) dmVe.bep = g;
  if ((g = v('dmMoTa')) !== null) dmVe.mo_ta = g;
  if ((g = v('dmDvt')) !== null) dmVe.dvt = g;
  if ((g = v('dmTt')) !== null) dmVe.tien_to = String(g || '').toUpperCase();
}

var dmKq = null;
function dmHoiXem() {
  if (dmTre) clearTimeout(dmTre);
  dmTre = setTimeout(async function () {
    var s = dmVe;
    if (!s.nhom && String(s.ten || '').trim().length < 3) { dmKq = null; return dmVeXem(); }
    try {
      dmKq = await api('vagabond.danh_muc.xem_truoc', {
        nhom: s.nhom, loai: s.loai, ten: s.ten, quy_cach: s.quy_cach
      });
    } catch (e) { dmKq = null; }
    dmVeXem();
  }, 320);
}

function dmVeXem() {
  var o = document.getElementById('dmXem');
  if (!o) return;
  var html = '';

  if (dmVuaTao) {
    html += '<div class="card" style="padding:14px;background:#f0fdf4;border:1.5px solid #86efac">' +
      '<div style="font-size:12px;color:#15803d;font-weight:800">VỪA MỞ XONG</div>' +
      '<div style="font-size:18px;font-weight:800;margin-top:3px">' + h(dmVuaTao.ma) + '</div>' +
      '<div style="font-size:13.5px;color:#374151;margin-top:2px">' + h(dmVuaTao.ten) + '</div>' +
      '<div style="font-size:12px;color:#6b7280;margin-top:3px">' + h(dmVuaTao.nhom) + ' · ' + h(dmVuaTao.dvt) +
      (dmVuaTao.gia_ban ? ' · ' + money(dmVuaTao.gia_ban) + ' đ' : ' · chưa có giá bán') + '</div>' +
      '<button class="btn gh" id="dmPan" style="margin-top:10px">🔄 Đồng bộ mã này sang Pancake</button>' +
      '<div id="dmPanBao" style="font-size:12.5px;color:#374151;margin-top:7px;line-height:1.5"></div></div>';
  }

  var k = dmKq;
  if (k) {
    html += '<div class="card" style="padding:13px 14px">' +
      '<div style="font-size:12px;color:#98a2b3;font-weight:700">MÁY SẼ ĐẶT</div>' +
      '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:5px">' +
      '<span style="font-size:13px;color:#6b7280">Mã hàng</span>' +
      '<b style="font-size:16px">' + h(k.ma_du_kien || 'chưa đoán được') + '</b></div>' +
      '<div style="display:flex;justify-content:space-between;gap:12px;margin-top:5px">' +
      '<span style="font-size:13px;color:#6b7280;flex:none">Tên món</span>' +
      '<b style="font-size:13.5px;text-align:right">' + h(k.ten_day_du || '') + '</b></div>' +
      (k.dvt_goi_y ? '<div style="display:flex;justify-content:space-between;margin-top:5px">' +
        '<span style="font-size:13px;color:#6b7280">Đơn vị tính</span><b style="font-size:13.5px">' + h(k.dvt_goi_y) + '</b></div>' : '') +
      '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px">Số cuối chỉ là dự kiến. Máy cấp số thật lúc bấm Tạo.</div></div>';

    (k.canh_bao || []).forEach(function (c) {
      html += '<div class="card" style="padding:12px 14px;background:#fffbeb;border:1.5px solid #fcd34d;font-size:13px;color:#92400e;line-height:1.6">⚠️ ' + h(c) + '</div>';
    });

    if ((k.trung || []).length) {
      var nang = (k.trung || []).filter(function (x) { return x.muc >= 3; }).length;
      html += '<div class="card" style="padding:12px 14px;border:1.5px solid ' + (nang ? '#fecaca' : '#e5e7eb') + ';background:' + (nang ? '#fef2f2' : '#fff') + '">' +
        '<div style="font-size:12px;font-weight:800;color:' + (nang ? '#991b1b' : '#6b7280') + '">' +
        (nang ? '⚠️ ĐÃ CÓ MÓN TRÙNG TÊN' : 'MÓN GẦN GIỐNG ĐÃ CÓ') + '</div>' +
        '<div style="font-size:12px;color:#6b7280;margin:4px 0 8px;line-height:1.6">' +
        'Mở thêm mã cho món đã có là tồn kho bị tách vụn, báo cáo bán chạy bị chia nhỏ, ' +
        'và về sau gộp lại phải kéo theo mọi hoá đơn đã trỏ tới.</div>' +
        (k.trung || []).map(function (x) {
          return '<div style="display:flex;gap:9px;align-items:baseline;padding:6px 0;border-top:1px solid #f2f4f7">' +
            '<b style="font-size:12.5px;flex:none">' + h(x.ma) + '</b>' +
            '<div style="flex:1;min-width:0"><div style="font-size:13px">' + h(x.ten) + '</div>' +
            '<div style="font-size:11.5px;color:#98a2b3">' + h(x.nhom) + ' · ' + h(x.vi_sao) + (x.tat ? ' · đã khoá' : '') + '</div></div></div>';
        }).join('') + '</div>';
    }
  }
  o.innerHTML = html;

  var np = document.getElementById('dmPan');
  if (np) np.onclick = async function () {
    var bao = document.getElementById('dmPanBao');
    np.disabled = true; np.textContent = 'Đang đẩy sang Pancake...';
    try {
      var r = await api('vagabond.danh_muc.day_sang_pancake', { item_code: dmVuaTao.ma });
      if (bao) bao.textContent = (r && r.thong_bao) || 'Xong.';
    } catch (e) {
      if (bao) bao.textContent = (e && e.message) || 'Không đẩy được sang Pancake.';
    }
    np.disabled = false; np.textContent = '🔄 Đồng bộ mã này sang Pancake';
  };
}

async function dmTao(boQuaTrung) {
  dmDoc();
  var s = dmVe;
  if (!s.nhom) return toast('Chọn nhóm món trước đã.');
  if (String(s.ten || '').trim().length < 3) return toast('Gõ tên mặt hàng giúp em.');
  busy(true);
  var r;
  try {
    r = await api('vagabond.danh_muc.tao', {
      nhom: s.nhom, loai: s.loai, ten: s.ten, quy_cach: s.quy_cach,
      gia_ban: String(s.gia || '').replace(/[^0-9]/g, ''),
      bep: s.bep, mo_ta: s.mo_ta, dvt: s.dvt, tien_to: s.tien_to,
      bo_qua_trung: boQuaTrung ? 1 : 0
    });
  } catch (e) {
    busy(false);
    var msg = (e && e.message) || 'Không tạo được';
    if (!boQuaTrung && msg.indexOf('Đã có mã') === 0) {
      var ok = await confirmSheet('Món này đã có mã rồi', msg, 'Vẫn tạo mã mới', true);
      if (ok) return dmTao(1);
      return;
    }
    baoTin(msg);
    return;
  }
  busy(false);
  dmVuaTao = r;
  /* Xoa o nhap de go tiep mon sau, giu lai nhom va loai hang: nguoi ta hay
     mo mot loat ma cung nhom trong mot luot. */
  dmVe.ten = ''; dmVe.quy_cach = ''; dmVe.gia = ''; dmVe.mo_ta = '';
  dmKq = null;
  toast('Đã mở mã ' + r.ma);
  dmDraw();
}



/* ================= SePay: nhận giao dịch ngân hàng =================

Ngày 19/08/2026 Uyên báo sao kê OCB kéo về thiếu giao dịch. Đọc lại mới ra
là hệ thống không hề NHẬN webhook, nó KÉO mỗi giờ một lần bằng một Server
Script, và con trỏ since_id của kịch bản đó đã vượt qua toàn bộ giao dịch
OCB cũ hơn ngày tài khoản này được khai vào bản đồ.

Màn này bày ra ba thứ mà trước đó không ai nhìn thấy được: đường dẫn thật
để dán sang SePay, con trỏ và kết quả lần kéo gần nhất, và số tài khoản nào
đang bị bỏ qua vì chưa khai. */

var seData = null;

async function scrSePay() {
  frame('SePay', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc cấu hình...</div></div>');
  try { seData = await api('vagabond.sepay.tinh_trang', {}); }
  catch (e) {
    frame('SePay', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  seVe();
}

/* Duong dan day du de dan sang SePay.

   Khong dung thang chuoi may chu tra ve: frappe.utils.get_url() cho ra ten
   mien noi bo cua Frappe Cloud (vagabond.s.frappe.cloud). Ca hai ten mien
   deu vao dung mot site, nhung cai dan cho ben thu ba phai la ten mien
   that cua cong ty - tuc chinh cai anh chi dang mo. */
function seUrl(d) {
  if (d && d.duong_dan_path) return location.origin + d.duong_dan_path;
  return (d && d.duong_dan) || '';
}

function seVe() {
  var d = seData || {};
  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">HAI ĐƯỜNG VÀO SỔ</div>' +
    '<div style="font-size:13.5px;color:#374151;line-height:1.65;margin-top:4px">' +
    '<b>Webhook</b> là SePay gọi sang ngay khi tiền về, tính bằng giây. ' +
    '<b>Nhịp kéo</b> là máy tự hỏi SePay mỗi giờ một lần, chậm nhưng là lưới an toàn ' +
    'khi webhook lỡ một gói. Cả hai cùng ghi một khoá <code>SEPAY-&lt;mã&gt;</code> nên ' +
    'không bao giờ sinh hai dòng cho một giao dịch.</div></div>';

  html += '<div class="sec">Webhook</div><div class="card" style="padding:12px 14px">' +
    '<div style="font-size:12px;color:#6b7280">Đường dẫn dán vào ô "URL nhận webhook" bên SePay</div>' +
    '<div id="seUrl" style="font-size:12.5px;font-weight:700;color:#0a58ca;word-break:break-all;' +
    'background:#f8fafc;border:1px solid #e5e7eb;border-radius:9px;padding:9px 11px;margin:6px 0 10px">' +
    h(seUrl(d)) + '</div>' +
    '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:9px">' +
    posChipNut('data-sebat="1"', d.bat ? '● Đang nhận' : '○ Đang tắt', !!d.bat) +
    posChipNut('data-sehm="1"', d.co_hmac ? '🛡 Đã có khoá HMAC' : '⚠️ Chưa có khoá HMAC', !!d.co_hmac) +
    posChipNut('data-sekhoa="1"', d.co_khoa ? '🔑 Có khoá dự phòng' : '○ Không khoá dự phòng', !!d.co_khoa) +
    posChipNut('data-sehm2="1"', d.co_hmac_2 ? '🛡 Có khoá HMAC 2 (ACB)' : '○ Chưa có khoá ACB', !!d.co_hmac_2) +
    '</div>' +
    /* HMAC la duong chinh, khong phai lua chon thu hai.
       Mot, no ky ca goi tin nen doi mot dong trong do la chu ky hong.
       Hai, chu ky di o header X-SePay-Signature ma Frappe khong dung toi,
       trong khi duong API Key cua SePay bat buoc gui o header
       Authorization va Frappe tra 401 cho header do truoc khi goi tin vao
       toi diem nhan (nghiem thu tren site 19/08/2026). */
    '<div style="font-size:12.5px;color:#374151;line-height:1.65;margin-bottom:8px">' +
    'Bên SePay chọn <b>HMAC-SHA256</b>, bấm nút sinh Secret Key rồi copy chuỗi ' +
    '<code>whsec_...</code> dán vào ô dưới đây. Đừng chọn API Key: cách đó bắt gửi ở header ' +
    '<code>Authorization</code>, mà Frappe chặn header đó trước khi gói tin vào tới đây.</div>' +
    (d.sua_duoc
      ? '<input class="tin" id="seHm" type="password" placeholder="Dán Secret Key whsec_... của SePay" style="margin-bottom:8px">' +
        '<button class="btn" id="seLuuHm" style="margin:0;width:100%">🛡 Lưu khoá HMAC và bật nhận</button>' +
        /* Webhook THU HAI (ACB) chay song song: SePay sinh cho moi webhook
           mot Secret Key rieng, nguoi dung khong chon duoc, nen phai co o
           thu hai. Ca hai webhook dan CUNG mot duong dan o tren. */
        '<div style="font-size:12.5px;color:#374151;line-height:1.6;margin:12px 0 6px">Chạy thêm ' +
        'tài khoản <b>ACB</b>: bên SePay tạo webhook <b>thứ hai</b> cho tài khoản ACB, trỏ về ' +
        'cùng đường dẫn trên, chọn HMAC-SHA256 rồi dán Secret Key của webhook đó vào đây.</div>' +
        '<input class="tin" id="seHm2" type="password" placeholder="Dán Secret Key whsec_... của webhook ACB" style="margin-bottom:8px">' +
        '<button class="btn" id="seLuuHm2" style="margin:0;width:100%">🛡 Lưu khoá HMAC thứ hai (ACB)</button>' +
        '<button class="btn gh" id="seSinh" style="margin:8px 0 0;width:100%">🔑 Sinh khoá dự phòng (header X-Api-Key)</button>'
      : '') +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:8px;line-height:1.6">' +
    'Khoá dự phòng chỉ dùng khi cần thử tay, gửi ở header <b>X-Api-Key</b>. Không có khoá ' +
    'nào thì ai biết đường dẫn cũng bắn được giao dịch giả vào sổ.</div></div>';

  var k = d.keo || {};
  html += '<div class="sec">Nhịp kéo hàng giờ</div><div class="card" style="padding:2px 14px 10px">' +
    htCtDong('Trạng thái', k.bat ? 'Đang chạy' : 'Đang tắt') +
    htCtDong('Lần kéo gần nhất', k.lan_cuoi || '') +
    htCtDong('Kết quả', k.ket_qua || '') +
    htCtDong('Con trỏ since_id', k.con_tro || '') +
    '<div style="font-size:11.5px;color:#98a2b3;padding:8px 0 0;line-height:1.6">' +
    'Con trỏ chỉ tiến, không lùi. Giao dịch nào có mã nhỏ hơn con trỏ mà lúc đó tài khoản ' +
    'chưa khai thì bị bỏ qua <b>vĩnh viễn</b> - phải nạp bù mới lấy lại được.</div></div>';

  html += '<div class="sec">Bản đồ tài khoản</div><div class="card" style="padding:2px 14px 10px">' +
    Object.keys(d.ban_do || {}).map(function (so) {
      return htCtDong(so, (d.ban_do || {})[so]);
    }).join('') +
    ((d.chua_map || []).length
      ? '<div style="font-size:12.5px;color:#b3261e;background:#fef2f2;border:1px solid #fecaca;' +
        'border-radius:9px;padding:10px 12px;margin-top:9px;line-height:1.6">Đang có giao dịch của ' +
        '<b>' + h((d.chua_map || []).join(', ')) + '</b> bị bỏ qua vì chưa khai trong bản đồ. ' +
        'Khai ngay ở ô dưới rồi nạp bù, nếu không thì tiền đã về mà sổ không có.</div>'
      : '') +
    (d.sua_duoc
      ? '<div style="font-size:12px;color:#6b7280;margin-top:10px">Khai thêm tài khoản (ví dụ ACB)</div>' +
        '<input class="tin" id="seMapSo" inputmode="numeric" placeholder="Số tài khoản như SePay hiển thị"' +
        ' value="' + h((d.chua_map || [])[0] || '') + '" style="margin:6px 0 8px">' +
        '<select class="tin" id="seMapTk" style="margin-bottom:8px">' +
        '<option value="">- Chọn tài khoản ngân hàng trong ERPNext -</option>' +
        (d.ds_tai_khoan || []).map(function (t) { return '<option value="' + h(t) + '">' + h(t) + '</option>'; }).join('') +
        '</select>' +
        '<button class="btn" id="seMapThem" style="margin:0;width:100%">➕ Thêm vào bản đồ</button>' +
        '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px;line-height:1.6">Nếu ACB chưa có ' +
        'trong danh sách chọn thì tạo Bank Account trên Desk trước. Khai xong nhớ chạy <b>nạp bù</b> ' +
        'bên dưới để lấy lại các giao dịch đã bị bỏ qua.</div>'
      : '') + '</div>';

  html += '<div class="sec">Số dòng đang có trong sổ</div><div class="card" style="padding:2px 14px 10px">' +
    (d.tai_khoan || []).map(function (t) {
      return htCtDong(t.bank_account || '', t.so + ' dòng, từ ' + (t.dau || '') + ' đến ' + (t.cuoi || ''));
    }).join('') + '</div>';

  if (d.sua_duoc) {
    html += '<div class="sec">Nạp bù sao kê cũ</div><div class="card" style="padding:12px 14px">' +
      '<div style="font-size:12.5px;color:#374151;line-height:1.65;margin-bottom:10px">' +
      'Đi lấy lại những giao dịch con trỏ đã bỏ qua. Thao tác này <b>chỉ thêm</b> dòng mới, ' +
      'không sửa và không xoá dòng nào, chạy lại bao nhiêu lần cũng ra kết quả như lần đầu.</div>' +
      '<input class="tin" id="seTk" placeholder="Số tài khoản (để trống là tất cả)" style="margin-bottom:8px">' +
      '<div style="display:flex;gap:8px">' +
      '<input class="tin" id="seTu" type="date" style="flex:1">' +
      '<input class="tin" id="seDen" type="date" style="flex:1"></div>' +
      '<button class="btn gh" id="seThu" style="margin:10px 0 0;width:100%">🔍 Chạy thử, chỉ đếm</button>' +
      '<button class="btn" id="seThat" style="margin:8px 0 0;width:100%">⬇️ Nạp bù thật</button>' +
      '<div id="seKq" style="margin-top:10px"></div></div>';
  }

  var b = frame('SePay', html);
  var nSinh = document.getElementById('seSinh');
  if (nSinh) nSinh.onclick = seSinhKhoa;
  var nHm = document.getElementById('seLuuHm');
  if (nHm) nHm.onclick = function () { seLuuHmac(1); };
  var nHm2 = document.getElementById('seLuuHm2');
  if (nHm2) nHm2.onclick = function () { seLuuHmac(2); };
  var nMap = document.getElementById('seMapThem');
  if (nMap) nMap.onclick = seThemTaiKhoan;
  var nThu = document.getElementById('seThu');
  if (nThu) nThu.onclick = function () { seNapBu(0); };
  var nThat = document.getElementById('seThat');
  if (nThat) nThat.onclick = function () { seNapBu(1); };
  return b;
}

async function seLuuHmac(khe) {
  var o = document.getElementById(khe === 2 ? 'seHm2' : 'seHm');
  var k = (o && o.value || '').trim();
  if (!k) return toast('Chưa dán Secret Key.', 4000);
  try { await api('vagabond.sepay.dat_hmac', { khoa: k, khe: khe === 2 ? 2 : 1 }); }
  catch (e) { return toast((e && e.message) || 'Không lưu được khoá', 5000); }
  if (o) o.value = '';
  toast(khe === 2 ? 'Đã lưu khoá HMAC thứ hai (ACB).' : 'Đã lưu khoá HMAC và bật nhận webhook.', 4000);
  scrSePay();
}

async function seThemTaiKhoan() {
  var so = (document.getElementById('seMapSo') || {}).value || '';
  var tk = (document.getElementById('seMapTk') || {}).value || '';
  if (!so.trim()) return toast('Chưa gõ số tài khoản.', 4000);
  if (!tk) return toast('Chưa chọn tài khoản ngân hàng trong ERPNext.', 4000);
  try { await api('vagabond.sepay.them_tai_khoan', { so_tk: so.trim(), tai_khoan: tk }); }
  catch (e) { return toast((e && e.message) || 'Không thêm được', 6000); }
  toast('Đã khai ' + so.trim() + ' vào bản đồ. Nhớ chạy nạp bù để lấy giao dịch cũ.', 5000);
  scrSePay();
}

async function seSinhKhoa() {
  var r;
  try { r = await api('vagabond.sepay.dat_khoa', {}); }
  catch (e) { toast((e && e.message) || 'Không sinh được khoá', 5000); return; }
  /* Hiện nguyên văn đúng một lần. Cất xong thì chính máy chủ cũng chỉ đọc
     lại được để so sánh, không bày ra màn nào nữa. */
  frame('Khoá webhook SePay',
    '<div style="font-size:13px;color:#374151;line-height:1.65;margin-bottom:11px">' +
    /* Nghiem thu 19/08/2026: header Authorization bi chinh Frappe tra 401
       truoc khi vao toi diem nhan, vi Frappe doc header do de tim khoa API
       cua no. Phai dung X-Api-Key. Ghi ro o day de khong ai huong dan lai
       theo cach cu. */
    'Dán hai dòng này sang SePay: đường dẫn vào ô <b>URL nhận webhook</b>, khoá vào tab ' +
    '<b>Bảo mật</b> với tên header <code>X-Api-Key</code> và giá trị là đúng chuỗi khoá. ' +
    '<b>Không dùng header <code>Authorization</code></b> - Frappe chặn header đó trước khi ' +
    'vào tới đây. Khoá này <b>không hiện lại</b> lần nữa.</div>' +
    '<div style="font-size:12px;color:#6b7280">Đường dẫn</div>' +
    '<div style="font-size:12.5px;font-weight:700;word-break:break-all;background:#f8fafc;' +
    'border:1px solid #e5e7eb;border-radius:9px;padding:9px 11px;margin:4px 0 11px">' + h(seUrl(r)) + '</div>' +
    '<div style="font-size:12px;color:#6b7280">Khoá</div>' +
    '<div style="font-size:13px;font-weight:800;word-break:break-all;background:#fffbeb;' +
    'border:1px solid #fde68a;border-radius:9px;padding:10px 11px;margin-top:4px">' + h(r.khoa) + '</div>');
}

async function seNapBu(that) {
  var tk = (document.getElementById('seTk') || {}).value || '';
  var tu = (document.getElementById('seTu') || {}).value || '';
  var den = (document.getElementById('seDen') || {}).value || '';
  var o = document.getElementById('seKq');
  if (o) o.innerHTML = '<div style="font-size:12.5px;color:#6b7280">Đang gọi sang SePay...</div>';
  var r;
  try {
    r = await api('vagabond.sepay.nap_bu', { so_tk: tk, tu_ngay: tu, den_ngay: den, that: that ? 1 : 0 });
  } catch (e) {
    if (o) o.innerHTML = '<div style="font-size:12.5px;color:#b3261e">' + h((e && e.message) || 'Không nạp được') + '</div>';
    return;
  }
  var chua = Object.keys(r.chua_map || {});
  if (o) {
    o.innerHTML =
      '<div style="font-size:12.5px;color:#374151;line-height:1.7;background:#f8fafc;' +
      'border:1px solid #e5e7eb;border-radius:9px;padding:10px 12px">' +
      '<b>' + (r.that ? 'Đã nạp thật' : 'Chạy thử, chưa ghi gì') + '</b><br>' +
      'Đọc từ SePay: ' + r.tong_doc + ' giao dịch<br>' +
      (r.that ? 'Đã thêm: ' : 'Sẽ thêm: ') + '<b>' + r.them + '</b> dòng<br>' +
      'Đã có sẵn: ' + r.da_co + ' dòng<br>' +
      'Bỏ qua vì chưa khai tài khoản: ' + r.bo_qua +
      (chua.length ? ' (' + h(chua.join(', ')) + ')' : '') + '</div>';
  }
  if (that) scrSePay();
}


/* ==================== NHẬP TỆP SAO KÊ NGÂN HÀNG ====================

Anh Việt 20/08/2026: *"Sao kê OCB của Uyên vẫn bị thiếu những khoản dưới
100k, và kéo về bị không đầy đủ."* Và 21/08/2026: *"Chỗ nhập tệp em cho vào
màn app luôn nhé để Uyên nhập."*

Đã dò tới cùng: gọi thẳng API SePay ba ngày 12, 13, 14/08 thì họ trả về 12,
10, 5 giao dịch và ERPNext đang giữ đủ cả ba con số. Gom theo tài khoản thì
OCB không có một khoản nào dưới 100k, trong khi MB có sáu. Chỗ mất nằm giữa
NGÂN HÀNG và SePay, ngoài tầm sửa của tiệm. Màn này là phần trong tầm.

Hai nhịp, cố ý: XEM TRƯỚC rồi mới GHI. Nhập tệp mà máy ghi luôn là cách nhân
đôi cả sổ ngân hàng chỉ bằng một cú bấm nhầm. */

var skTk = '', skFile = '', skTen = '', skXt = null;

async function scrNhapSaoKe() {
  frame('Nhập sao kê ngân hàng', '<div class="emp"><div class="e1">⏳</div><div>Đang mở...</div></div>');
  var tk;
  try { tk = await api('vagabond.nhap_sao_ke.danh_sach_tai_khoan', {}); }
  catch (e) {
    frame('Nhập sao kê ngân hàng',
      '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  var ds = (tk && tk.ds) || [];
  if (!skTk && ds.length) skTk = ds[0].ma;

  var html =
    '<div class="card" style="padding:13px 15px">' +
    '<div style="font-size:12.5px;color:#374151;line-height:1.65">' +
    'Ngân hàng gửi sao kê dạng Excel hoặc CSV thì tải lên đây. Máy chỉ thêm ' +
    'những dòng còn thiếu, dòng nào đã có trong sổ thì bỏ qua, không ghi đè.' +
    '</div></div>' +

    '<div class="sec">1. Chọn tài khoản</div>' +
    '<div class="card" style="padding:12px 14px">' +
    '<select id="skTk" class="vxs">' +
    ds.map(function (x) {
      return '<option value="' + h(x.ma) + '"' + (x.ma === skTk ? ' selected' : '') + '>' +
        h(x.ten) + (x.so_tk ? ' · ' + h(x.so_tk) : '') + (x.ngan_hang ? ' · ' + h(x.ngan_hang) : '') +
        '</option>';
    }).join('') +
    '</select>' +
    (ds.length ? '' : '<div style="font-size:12.5px;color:#b3261e;margin-top:8px">' +
      'Chưa có tài khoản ngân hàng nào trên hệ. Khai ở Desk rồi quay lại.</div>') +
    '</div>' +

    '<div class="sec">2. Chọn tệp sao kê</div>' +
    '<div class="card" style="padding:12px 14px">' +
    '<input type="file" id="skTep" accept=".xlsx,.xlsm,.csv" style="display:none">' +
    '<button class="btn gh" id="skChon" style="margin:0;width:100%">' +
    (skTen ? '📄 ' + h(skTen) : '📎 Chọn tệp .xlsx hoặc .csv') + '</button>' +
    '<div style="font-size:11.5px;color:#9ca3af;margin-top:8px;line-height:1.6">' +
    'Sao kê phải có các cột Nội dung và PS giảm hoặc PS tăng. Mấy dòng đầu là ' +
    'tên ngân hàng và kỳ sao kê thì cứ để nguyên, máy tự tìm dòng tiêu đề.</div>' +
    '</div>' +
    '<div id="skKq"></div>';

  var b = frame('Nhập sao kê ngân hàng', html);
  var oTk = document.getElementById('skTk');
  if (oTk) oTk.onchange = function () { skTk = oTk.value; skXt = null; skVeKq(); };
  var oT = document.getElementById('skTep');
  var oC = document.getElementById('skChon');
  if (oC && oT) {
    oC.onclick = function () { oT.value = ''; oT.click(); };
    oT.onchange = function () { skTaiLen(oT.files && oT.files[0]); };
  }
  skVeKq();
}

function skTaiLen(file) {
  if (!file) return;
  if (file.size > 20 * 1024 * 1024) {
    return baoTin('Tệp nặng quá 20 MB. Cắt sao kê theo tháng rồi tải từng tệp giúp em.', 'Tệp quá nặng');
  }
  var fr = new FileReader();
  fr.onload = async function () {
    busy(true);
    try {
      var r = await api('vagabond.nhap_sao_ke.tai_len', {
        ten: file.name || 'sao-ke.xlsx', noi_dung: String(fr.result || '')
      });
      skFile = r.file_url; skTen = r.ten; skXt = null;
      var xt = await api('vagabond.nhap_sao_ke.xem_truoc', { file_url: skFile, tai_khoan: skTk });
      busy(false);
      skXt = xt;
      go(scrNhapSaoKe, true);
    } catch (e) {
      busy(false);
      skFile = ''; skTen = ''; skXt = null;
      baoTin((e && e.message) || 'Chưa đọc được tệp.', 'Chưa nhập được');
    }
  };
  fr.readAsDataURL(file);
}

function skVeKq() {
  var o = document.getElementById('skKq');
  if (!o) return;
  if (!skXt) { o.innerHTML = ''; return; }
  var x = skXt;
  o.innerHTML =
    '<div class="sec">3. Xem trước, chưa ghi gì</div>' +
    '<div class="card" style="padding:13px 15px">' +
    '<div style="display:flex;gap:10px;text-align:center;margin-bottom:10px">' +
    skO('Đọc được', x.tong, '#374151') +
    skO('Sẽ thêm', x.se_them, '#047857') +
    skO('Đã có', x.bo_qua, '#9ca3af') +
    '</div>' +
    '<div style="font-size:12.5px;color:#4b5563;line-height:1.7;border-top:1px solid #f0f2f6;padding-top:9px">' +
    'Kỳ <b>' + h(x.tu_ngay) + '</b> đến <b>' + h(x.den_ngay) + '</b><br>' +
    'Tiền vào sẽ thêm: <b>' + money(x.tien_vao) + ' đ</b><br>' +
    'Tiền ra sẽ thêm: <b>' + money(x.tien_ra) + ' đ</b></div>' +
    (x.mau_them && x.mau_them.length
      ? '<div style="font-size:11.5px;color:#6b7280;margin-top:10px;font-weight:700">DÒNG SẼ THÊM (' +
        x.mau_them.length + (x.se_them > x.mau_them.length ? ' trên ' + x.se_them : '') + ')</div>' +
        x.mau_them.map(skDong).join('')
      : '<div style="font-size:12.5px;color:#047857;margin-top:10px">' +
        'Sổ đã đủ, không dòng nào thiếu. Không cần ghi gì thêm.</div>') +
    '</div>' +
    (x.se_them
      ? '<div style="padding:0 12px 14px"><button class="btn" id="skGhi" style="margin:0;width:100%">' +
        'Ghi ' + x.se_them + ' dòng vào sổ</button>' +
        '<div style="font-size:11px;color:#9ca3af;margin-top:7px;line-height:1.55;text-align:center">' +
        'Ghi rồi thì dòng nằm trong sổ ngân hàng thật. Muốn bỏ phải huỷ từng dòng trên Desk.</div></div>'
      : '');
  var n = document.getElementById('skGhi');
  if (n) n.onclick = skGhi;
}

function skO(nhan, so, mau) {
  return '<div style="flex:1;background:#f8fafc;border-radius:10px;padding:9px 4px">' +
    '<div style="font-size:19px;font-weight:800;color:' + mau + '">' + (so || 0) + '</div>' +
    '<div style="font-size:11px;color:#8a90a0;margin-top:1px">' + h(nhan) + '</div></div>';
}

function skDong(d) {
  var vao = Number(d.tien_vao) || 0, ra = Number(d.tien_ra) || 0;
  return '<div style="border-top:1px solid #f2f4f7;padding:7px 0;font-size:12px;line-height:1.5">' +
    '<div style="display:flex;gap:8px"><div style="flex:1;min-width:0;color:#374151">' +
    h(d.noi_dung || '(không có nội dung)') + '</div>' +
    '<div style="flex:none;font-weight:800;color:' + (vao ? '#047857' : '#b3261e') + '">' +
    (vao ? '+' + money(vao) : '-' + money(ra)) + '</div></div>' +
    '<div style="color:#9ca3af;font-size:11px">' + h(dmy(d.ngay)) +
    (d.so_gd ? ' · ' + h(d.so_gd) : ' · ngân hàng không ghi số giao dịch') +
    (d.vi_sao ? ' · ' + h(d.vi_sao) : '') + '</div></div>';
}

async function skGhi() {
  if (!skXt || !skXt.se_them) return;
  var ok = await hoiCo('Ghi sao kê vào sổ',
    'Máy sẽ thêm <b>' + skXt.se_them + '</b> dòng vào sổ ngân hàng, kỳ ' +
    h(skXt.tu_ngay) + ' đến ' + h(skXt.den_ngay) + '. Dòng đã có thì bỏ qua. ' +
    'Ghi rồi muốn bỏ phải huỷ từng dòng trên Desk.', 'Ghi vào sổ');
  if (!ok) return;
  busy(true);
  try {
    var r = await api('vagabond.nhap_sao_ke.nap', { file_url: skFile, tai_khoan: skTk });
    busy(false);
    skFile = ''; skTen = ''; skXt = null;
    var than = h(r.loi_nhan || 'Đã ghi xong.');
    if (r.hong && r.hong.length) {
      than += '<div style="margin-top:9px;font-size:12px;color:#b3261e;line-height:1.6">' +
        r.hong.slice(0, 8).map(function (x) {
          return h(x.ngay + ' ' + (x.so_gd || '')) + ': ' + h(x.loi);
        }).join('<br>') + '</div>';
    }
    baoTin(than, 'Nhập sao kê xong');
    go(scrNhapSaoKe, true);
  } catch (e) {
    busy(false);
    baoTin((e && e.message) || 'Chưa ghi được.', 'Lỗi');
  }
}


/* ==================== THÔNG BÁO TRÊN ĐIỆN THOẠI ====================

Anh Việt 20/08/2026: *"Khi có một phiếu mới chuyển sang trạng thái chờ duyệt
của đúng User đó, hệ thống phải bắn notification làm rung điện thoại."*

Vì sao có màn riêng chứ không hỏi quyền ngay lúc mở app: trình duyệt chỉ cho
hỏi MỘT lần, bấm Chặn là chặn vĩnh viễn và phải vào phần cài đặt của trình
duyệt tìm từng mục mới mở lại được. Nên chỉ hỏi khi người ta chủ động bấm,
hoặc khi đã thêm app ra màn hình chính - tức là đã tỏ ý dùng lâu dài. */

async function scrThongBao() {
  frame('Thông báo trên điện thoại', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc...</div></div>');
  var t = {};
  try { t = await api('vagabond.thong_bao.tinh_hinh', {}); } catch (e) { t = {}; }

  var daCai = pwaDaCaiRaManHinh();
  var quyen = ('Notification' in window) ? Notification.permission : 'khong_ho_tro';
  var ho_tro = ('Notification' in window) && !!navigator.serviceWorker;

  function hang(nhan, xong, phu) {
    return '<div style="display:flex;gap:11px;align-items:flex-start;padding:10px 0;' +
      'border-bottom:1px solid #f2f4f7">' +
      '<div style="flex:none;font-size:17px">' + (xong ? '✅' : '⬜') + '</div>' +
      '<div style="flex:1;min-width:0"><div style="font-size:13.5px;font-weight:700;color:#101828">' +
      h(nhan) + '</div>' +
      (phu ? '<div style="font-size:12px;color:#8a90a0;margin-top:2px;line-height:1.55">' + phu + '</div>' : '') +
      '</div></div>';
  }

  var html = '<div class="sec">Tình trạng</div><div class="card" style="padding:6px 15px 12px">' +
    hang('Trình duyệt hỗ trợ thông báo', ho_tro,
      ho_tro ? '' : 'Trình duyệt này không có Web Push. Dùng Safari trên iPhone hoặc Chrome trên Android.') +
    hang('Đã thêm app ra màn hình chính', daCai,
      daCai ? '' : 'Trên iPhone bắt buộc phải thêm ra màn hình chính thì mới bật thông báo được. ' +
        'Bấm nút Chia sẻ dưới thanh địa chỉ rồi chọn "Thêm vào MH chính".') +
    hang('Đã cho phép hiện thông báo', quyen === 'granted',
      quyen === 'denied'
        ? 'Trình duyệt đang CHẶN. Phải vào phần cài đặt của trình duyệt, tìm mục Thông báo ' +
          'của trang này và bật lại, vì trình duyệt không cho hỏi lần hai.'
        : '') +
    hang('Máy này đã đăng ký nhận', (t.may_cua_toi || 0) > 0,
      (t.may_cua_toi || 0) > 0 ? 'Bạn đang nhận trên ' + t.may_cua_toi + ' máy.' : '') +
    hang('Máy chủ gửi được', !!t.co_thu_vien,
      t.co_thu_vien ? '' : 'Bản build trên máy chủ chưa có thư viện gửi. Báo anh Việt deploy bản mới nhất.') +
    '</div>' +

    '<div style="padding:12px 12px 4px">' +
    '<button class="btn" id="tbBat" style="margin:0;width:100%">🔔 Bật thông báo trên máy này</button>' +
    '<button class="btn gh" id="tbThu" style="margin:8px 0 0;width:100%">Thử một tin, xem có rung không</button>' +
    '</div>' +
    '<div style="text-align:center;color:#a0a6b4;font-size:11.5px;padding:8px 16px 4px;line-height:1.6">' +
    'Thông báo bắn cho người phải xử lý ở bước kế tiếp, theo chức vụ chứ không theo tên. ' +
    'Ai nghỉ phép thì người cùng chức vụ vẫn nhận được.</div>';

  var b = frame('Thông báo trên điện thoại', html);
  document.getElementById('tbBat').onclick = async function () {
    busy(true);
    var r = await pwaXinQuyenThongBao(1);
    busy(false);
    var noi = {
      xong: 'Đã bật. Thử bấm nút dưới xem điện thoại có rung không.',
      da_chan: 'Trình duyệt đang chặn thông báo của trang này. Phải vào phần cài đặt ' +
        'của trình duyệt bật lại, vì trình duyệt không cho hỏi lần hai.',
      tu_choi: 'Bạn vừa bấm Không cho phép. Bấm lại nút này để hỏi lần nữa.',
      chua_cai: 'Phải thêm app ra màn hình chính trước đã.',
      khong_ho_tro: 'Trình duyệt này không có Web Push.',
      chua_khai_khoa: 'Máy chủ chưa sinh được khoá. Báo anh Việt xem nhật ký lỗi.',
      loi: 'Có lỗi lúc đăng ký. Thử lại một lần nữa; vẫn lỗi thì báo anh Việt.'
    }[r] || 'Chưa rõ kết quả, thử lại giúp em.';
    baoTin(noi, r === 'xong' ? 'Đã bật thông báo' : 'Chưa bật được');
    if (r === 'xong') go(scrThongBao, true);
  };
  document.getElementById('tbThu').onclick = async function () {
    busy(true);
    try {
      var r = await api('vagabond.thong_bao.thu_gui', {});
      busy(false);
      baoTin(h(r.loi_nhan || ''), r.ok ? 'Đã bắn thử' : 'Chưa gửi được');
    } catch (e) {
      busy(false);
      baoTin((e && e.message) || 'Chưa gửi được.', 'Lỗi');
    }
  };
}

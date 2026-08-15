/* ================= PHAN HE BAO CAO (anh Viet 12/08/2026) =================

Mot cho de ban giam doc, quan ly sales, quan ly cua hang, ke toan va
marketing nhin so lieu CA BA DIEM BAN. Man nay khong tu tinh toan gi het:
moi con so deu do may chu tra ve (vagabond/bao_cao.py), nho vay so tren
app luon bang so trong so sach.

Moi bao cao deu tra ve cung mot hinh dang { cot, dong, cong, bieu_do } nen
man hinh chi viet MOT lan - them bao cao moi ben may chu la app tu hien,
khong phai sua giao dien.

Ba kieu xem theo y anh Viet: bang hang cot, bieu do thanh ngang, va the.
Bang hop de doi chieu, bieu do hop de nhin ty trong, the hop tren dien
thoai khi bang co nhieu cot qua man hinh. */

var bcKy = 'ngay';
var bcMoc = null;      /* mot ngay bat ky nam trong ky dang xem */
var bcTu = null, bcDen = null;   /* chi dung khi ky la tuy_chon */
var bcDiem = '';       /* rong la ca ba diem ban */
var bcXem = 'bang';
var bcMa = null;
var bcLocNguon = '', bcLocPt = '';
var bcSS = 0;          /* 1 la bat so sanh voi ky lien truoc */

var BC_KY = [
  { k: 'ngay', nhan: 'Ngày' },
  { k: 'tuan', nhan: 'Tuần' },
  { k: 'thang', nhan: 'Tháng' },
  { k: 'quy', nhan: 'Quý' },
  { k: 'nam', nhan: 'Năm' },
  { k: 'tuy_chon', nhan: 'Tuỳ chọn' }
];
var BC_DIEM = [
  { ma: '', ten: 'Cả ba điểm' },
  { ma: 'SALES', ten: 'Sales Online' },
  { ma: 'TCV', ten: 'District 1' },
  { ma: 'NVHTN', ten: 'NVHTN' }
];

function bcThamSo() {
  var o = { ky: bcKy, diem: bcDiem };
  if (bcKy === 'tuy_chon') { o.tu = bcTu || today(); o.den = bcDen || today(); }
  else o.moc = bcMoc || today();
  if (bcSS) o.ss = 1;
  return o;
}

/* Chenh lech so voi ky truoc. Ky truoc bang 0 thi khong chia duoc - noi
   thang la chua co ky truoc de so, con hon la in ra mot con so bia. */
function bcDelta(pc) {
  if (pc == null) return '<span style="color:#98a2b3">chưa có kỳ trước để so</span>';
  var len = pc >= 0;
  return '<span style="color:' + (len ? '#0f766e' : '#dc2626') + ';font-weight:700">' +
    (len ? '▲ +' : '▼ ') + (Math.round(pc * 10) / 10) + '%</span>';
}

function bcHangSoSanh(ss) {
  if (!ss) return '';
  return '<div style="font-size:12.5px;color:#6b7280;margin-top:7px;padding-top:7px;border-top:1px dashed #e5e7eb">' +
    'So với ' + h(ss.nhan_ky) + ': <b>' + money(ss.tong_doanh_thu) + ' đ</b> · ' +
    bcDelta(ss.chenh) + ' doanh thu · ' + money(ss.so_hoa_don) + ' hoá đơn ' + bcDelta(ss.chenh_hd) +
    '</div>';
}

/* Doi ky ma van giu dung ngay dang xem: dang xem thang 8 bam sang "Quy"
   thi ra quy 3, chu khong nhay ve hom nay. */
function bcDoiKy(k) {
  bcKy = k;
  if (!bcMoc) bcMoc = today();
}

/* Lui hoac toi mot ky. Lam o may khach cho nhanh, may chu van tu tinh lai
   dau ky cuoi ky nen khong so lech. */
function bcNhay(huong) {
  var d = new Date((bcMoc || today()) + 'T00:00:00');
  if (bcKy === 'ngay') d.setDate(d.getDate() + huong);
  else if (bcKy === 'tuan') d.setDate(d.getDate() + 7 * huong);
  else if (bcKy === 'thang') d.setMonth(d.getMonth() + huong);
  else if (bcKy === 'quy') d.setMonth(d.getMonth() + 3 * huong);
  else if (bcKy === 'nam') d.setFullYear(d.getFullYear() + huong);
  else return;
  bcMoc = d.toISOString().slice(0, 10);
}

function bcThanhKy() {
  var h1 = BC_KY.map(function (x) {
    return posChipNut('data-bcky="' + x.k + '"', x.nhan, bcKy === x.k);
  }).join('');
  var h2 = BC_DIEM.map(function (x) {
    return posChipNut('data-bcdiem="' + x.ma + '"', x.ten, bcDiem === x.ma);
  }).join('');
  var dieu = bcKy === 'tuy_chon'
    ? '<div style="display:flex;gap:8px;margin-top:8px">' +
      '<input class="tin" id="bcTu" type="date" value="' + h(bcTu || today()) + '" style="flex:1">' +
      '<input class="tin" id="bcDen" type="date" value="' + h(bcDen || today()) + '" style="flex:1">' +
      '</div>'
    : '<div style="display:flex;gap:7px;margin-top:8px">' +
      posChipNut('data-bcnhay="-1"', '◀ Kỳ trước', false) +
      posChipNut('data-bcnhay="0"', 'Hiện tại', false) +
      posChipNut('data-bcnhay="1"', 'Kỳ sau ▶', false) + '</div>';
  var ss = '<div style="margin-top:7px">' +
    posChipNut('data-bcss="1"', '⇄ So với kỳ trước', !!bcSS) + '</div>';
  return '<div class="card" style="padding:11px 12px">' +
    kmHangChip(h1) + '<div style="height:7px"></div>' + kmHangChip(h2) + dieu + ss + '</div>';
}

function bcNoiThanh(b, veLai) {
  b.onclick = function (e) {
    var t = e.target.closest('[data-bcky]');
    if (t) { bcDoiKy(t.getAttribute('data-bcky')); return veLai(); }
    t = e.target.closest('[data-bcdiem]');
    if (t) { bcDiem = t.getAttribute('data-bcdiem'); return veLai(); }
    t = e.target.closest('[data-bcnhay]');
    if (t) {
      var hg = parseInt(t.getAttribute('data-bcnhay'), 10);
      if (!hg) bcMoc = today(); else bcNhay(hg);
      return veLai();
    }
    t = e.target.closest('[data-bcmo]');
    if (t) { bcMa = t.getAttribute('data-bcmo'); return go(scrBaoCaoXem, true); }
    t = e.target.closest('[data-bcxem]');
    if (t) { bcXem = t.getAttribute('data-bcxem'); return veLai(); }
    t = e.target.closest('[data-bcnguon]');
    if (t) { bcLocNguon = t.getAttribute('data-bcnguon'); return veLai(); }
    t = e.target.closest('[data-bcpt]');
    if (t) { bcLocPt = t.getAttribute('data-bcpt'); return veLai(); }
    t = e.target.closest('[data-bcss]');
    if (t) { bcSS = bcSS ? 0 : 1; return veLai(); }
  };
  ['bcTu', 'bcDen'].forEach(function (id) {
    var o = document.getElementById(id);
    if (o) o.onchange = function () {
      bcTu = document.getElementById('bcTu').value;
      bcDen = document.getElementById('bcDen').value;
      veLai();
    };
  });
}

/* ---------- man chinh: danh sach bao cao ---------- */
async function scrBaoCao() {
  frame('Báo cáo', '<div class="emp"><div class="e1">⏳</div><div>Đang cộng sổ ba điểm bán...</div></div>');
  var kq;
  try { kq = await api('vagabond.bao_cao.danh_sach', bcThamSo()); }
  catch (e) {
    frame('Báo cáo', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được báo cáo') + '</div></div>');
    return;
  }

  var html = bcThanhKy();

  html += '<div class="card" style="padding:14px">' +
    '<div style="font-size:12px;color:#98a2b3">TỔNG DOANH THU · ' + h(kq.nhan_ky) + '</div>' +
    '<div style="font-size:30px;font-weight:800;line-height:1.25">' + money(kq.tong_doanh_thu) + ' đ</div>' +
    '<div style="font-size:12.5px;color:#6b7280">' + money(kq.so_hoa_don) + ' hoá đơn · bình quân ' + money(Math.round(kq.binh_quan)) + ' đ/hoá đơn</div>' +
    bcHangSoSanh(kq.ss) +
    '<div style="height:10px"></div>' +
    kq.diem_ban.map(function (d) {
      var pc = kq.tong_doanh_thu ? d.tien / kq.tong_doanh_thu * 100 : 0;
      return '<div style="margin-bottom:9px">' +
        '<div style="display:flex;justify-content:space-between;font-size:13px">' +
        '<span><b>' + h(d.ten) + '</b> <span style="color:#a0a6b4">' + h(d.dia_chi) + '</span></span>' +
        '<b>' + money(d.tien) + ' đ</b></div>' +
        '<div style="height:7px;border-radius:99px;background:#eef0f5;overflow:hidden;margin-top:4px">' +
        '<div style="height:100%;width:' + Math.max(1, Math.round(pc)) + '%;background:#50DBF2"></div></div></div>';
    }).join('') + '</div>';

  var nhom = [];
  kq.bao_cao.forEach(function (b) {
    var g = null;
    nhom.forEach(function (x) { if (x.ten === b.nhom) g = x; });
    if (!g) { g = { ten: b.nhom, ds: [] }; nhom.push(g); }
    g.ds.push(b);
  });
  nhom.forEach(function (g) {
    html += '<div class="sec">' + h(g.ten) + '</div><div class="card">' +
      g.ds.map(function (b) {
        return '<div class="row" data-bcmo="' + h(b.ma) + '" style="display:flex;align-items:center;gap:11px;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
          '<div style="width:34px;height:34px;border-radius:9px;background:#f0fdfa;display:flex;align-items:center;justify-content:center;font-size:17px">' + b.ic + '</div>' +
          '<div style="flex:1;min-width:0"><b style="font-size:14.5px">' + h(b.ten) + '</b>' +
          '<div style="font-size:12px;color:#98a2b3">' + h(b.ma) + ' · ' + h(b.mo) + '</div></div>' +
          '<span style="color:#c3c8d4">›</span></div>';
      }).join('') + '</div>';
  });

  html += '<div style="text-align:center;color:#a0a6b4;font-size:11.5px;padding:8px 14px 2px;line-height:1.6">' +
    'Số liệu đọc thẳng từ hoá đơn đã ghi sổ, không qua bảng tổng hợp nên luôn khớp với sổ sách.</div>';

  var b = frame('Báo cáo', html);
  bcNoiThanh(b, function () { go(scrBaoCao, true); });
}

/* ---------- man xem mot bao cao ---------- */
function bcO(c, v) {
  if (c.kieu === 'tien') return money(Math.round(flt0(v))) + ' đ';
  if (c.kieu === 'so') return money(Math.round(flt0(v) * 100) / 100);
  if (c.kieu === 'phan_tram') {
    /* Cot Chenh de rong nghia la ky truoc khong co dong nay, khong phai
       0%. In "mới" de khoi hieu nham la khong tang khong giam. */
    if (v == null || v === '') return c.k === '_chenh' ? '<i style="color:#0f766e;font-style:normal">mới</i>' : '0%';
    var s = (Math.round(flt0(v) * 10) / 10) + '%';
    if (c.k !== '_chenh') return s;
    var len = flt0(v) >= 0;
    return '<b style="color:' + (len ? '#0f766e' : '#dc2626') + '">' + (len ? '+' : '') + s + '</b>';
  }
  if (c.kieu === 'ngay') return posNgayVn(String(v || ''));
  return h(String(v == null ? '' : v));
}
function flt0(v) { var n = parseFloat(v); return isNaN(n) ? 0 : n; }

function bcVeBang(kq) {
  if (!kq.dong.length) return '<div class="card"><div class="emp" style="padding:26px"><div class="e1">🫙</div><div>Kỳ này chưa có số liệu.</div></div></div>';
  var canPhai = { tien: 1, so: 1, phan_tram: 1 };
  var html = '<div class="card" style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:13px">' +
    '<thead><tr>' + kq.cot.map(function (c) {
      return '<th style="text-align:' + (canPhai[c.kieu] ? 'right' : 'left') + ';padding:10px 12px;background:#f8fafc;color:#6b7280;font-size:11.5px;font-weight:700;white-space:nowrap;position:sticky;top:0">' + h(c.nhan) + '</th>';
    }).join('') + '</tr></thead><tbody>';
  kq.dong.forEach(function (r, i) {
    html += '<tr style="border-top:1px solid #f2f4f7' + (i % 2 ? ';background:#fcfdfe' : '') + '">' +
      kq.cot.map(function (c, j) {
        return '<td style="text-align:' + (canPhai[c.kieu] ? 'right' : 'left') + ';padding:9px 12px;white-space:nowrap' + (j === 0 ? ';font-weight:600' : '') + '">' + bcO(c, r[c.k]) + '</td>';
      }).join('') + '</tr>';
  });
  if (kq.cong && Object.keys(kq.cong).length) {
    html += '<tr style="border-top:2px solid #e5e7eb;background:#f0fdfa;font-weight:800">' +
      kq.cot.map(function (c, j) {
        var v = j === 0 ? 'TỔNG' : (kq.cong[c.k] == null ? '' : bcO(c, kq.cong[c.k]));
        return '<td style="text-align:' + (canPhai[c.kieu] && j ? 'right' : 'left') + ';padding:10px 12px;white-space:nowrap">' + (j === 0 ? v : v) + '</td>';
      }).join('') + '</tr>';
  }
  return html + '</tbody></table></div>';
}

function bcVeBieuDo(kq) {
  var bd = kq.bieu_do;
  if (!bd) return '<div class="card"><div class="emp" style="padding:24px"><div class="e2">Báo cáo này không hợp để vẽ biểu đồ, xem dạng bảng nhé.</div></div></div>';
  var ds = kq.dong.slice(0, bd.so_dong || 15);
  if (!ds.length) return '<div class="card"><div class="emp" style="padding:26px"><div class="e1">🫙</div><div>Kỳ này chưa có số liệu.</div></div></div>';
  var cot = null;
  kq.cot.forEach(function (c) { if (c.k === bd.gia_tri) cot = c; });
  var lon = 0;
  ds.forEach(function (r) { lon = Math.max(lon, flt0(r[bd.gia_tri])); });
  return '<div class="card" style="padding:14px">' + ds.map(function (r) {
    var v = flt0(r[bd.gia_tri]);
    var pc = lon ? Math.max(2, Math.round(v / lon * 100)) : 2;
    return '<div style="margin-bottom:11px">' +
      '<div style="display:flex;justify-content:space-between;gap:10px;font-size:13px">' +
      '<span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + h(String(r[bd.nhan] == null ? '' : r[bd.nhan])) + '</span>' +
      '<b style="white-space:nowrap">' + bcO(cot || { kieu: 'so' }, v) + '</b></div>' +
      '<div style="height:9px;border-radius:99px;background:#eef0f5;overflow:hidden;margin-top:4px">' +
      '<div style="height:100%;width:' + pc + '%;background:linear-gradient(90deg,#50DBF2,#0ea5b7)"></div></div></div>';
  }).join('') + '</div>';
}

function bcVeThe(kq) {
  if (!kq.dong.length) return '<div class="card"><div class="emp" style="padding:26px"><div class="e1">🫙</div><div>Kỳ này chưa có số liệu.</div></div></div>';
  return '<div style="display:grid;gap:10px">' + kq.dong.map(function (r) {
    var dau = kq.cot[0];
    return '<div class="card" style="padding:12px 14px;margin:0">' +
      '<b style="font-size:14.5px">' + bcO(dau, r[dau.k]) + '</b>' +
      '<div style="display:grid;gap:4px;margin-top:7px">' +
      kq.cot.slice(1).map(function (c) {
        return '<div style="display:flex;justify-content:space-between;font-size:13px;color:#374151">' +
          '<span style="color:#98a2b3">' + h(c.nhan) + '</span><b>' + bcO(c, r[c.k]) + '</b></div>';
      }).join('') + '</div></div>';
  }).join('') + '</div>';
}

async function scrBaoCaoXem() {
  var ma = bcMa || 'BC01';
  frame('Báo cáo ' + ma, '<div class="emp"><div class="e1">⏳</div><div>Đang cộng sổ...</div></div>');
  var ts = bcThamSo();
  ts.ma = ma;
  if (bcLocNguon) ts.nguon = bcLocNguon;
  if (bcLocPt) ts.pt = bcLocPt;
  var kq;
  try { kq = await api('vagabond.bao_cao.chay', ts); }
  catch (e) {
    frame('Báo cáo ' + ma, '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không chạy được') + '</div></div>');
    return;
  }

  var html = bcThanhKy();
  html += '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">' + h(kq.ma) + ' · ' + h(kq.nhan_ky) + '</div>' +
    '<div style="font-size:19px;font-weight:800">' + kq.ic + ' ' + h(kq.ten) + '</div>' +
    '<div style="font-size:12.5px;color:#6b7280;margin-top:2px">' + h(kq.mo) + '</div>' +
    '<div style="font-size:13px;color:#0f766e;margin-top:8px"><b>' + money(kq.tong_doanh_thu) + ' đ</b> doanh thu · ' + money(kq.so_hoa_don) + ' hoá đơn trong phạm vi đang lọc</div>' +
    bcHangSoSanh(kq.ss) +
    (kq.ss && !kq.co_ss_dong
      ? '<div style="font-size:12px;color:#98a2b3;margin-top:5px">Báo cáo dạng bảng kê nên không so được từng dòng, chỉ so tổng.</div>'
      : '') +
    '</div>';

  /* Chip loc nguon don va phuong thuc thanh toan: chi hien khi ky nay
     that su co nhieu hon mot gia tri, khoi bay chip vo ich. */
  if ((kq.nguon_loc || []).length > 1) {
    html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
      posChipNut('data-bcnguon=""', 'Mọi nguồn đơn', !bcLocNguon) +
      kq.nguon_loc.map(function (n) { return posChipNut('data-bcnguon="' + h(n) + '"', h(n), bcLocNguon === n); }).join('')
    ) + '</div>';
  }
  if ((kq.pt_loc || []).length > 1) {
    html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
      posChipNut('data-bcpt=""', 'Mọi phương thức', !bcLocPt) +
      kq.pt_loc.map(function (n) { return posChipNut('data-bcpt="' + h(n) + '"', h(n), bcLocPt === n); }).join('')
    ) + '</div>';
  }

  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
    posChipNut('data-bcxem="bang"', '📋 Bảng', bcXem === 'bang') +
    posChipNut('data-bcxem="bieu_do"', '📊 Biểu đồ', bcXem === 'bieu_do') +
    posChipNut('data-bcxem="the"', '🗂️ Thẻ', bcXem === 'the')
  ) + '</div>';

  /* Bang ke chi tiet mot thang co the hang nghin dong. Man hinh chi nhan
     toi GIOI_HAN_DONG, noi ro cho nguoi xem biet la dang xem mot phan va
     file Excel moi la ban day du - im lang o cho nay la nguy hiem nhat,
     ke toan tuong da xem het roi cong tay ra so thieu. */
  if (kq.bi_cat) {
    /* Boc them mot lop div: the .card xep con theo cot nen de <b> tran o
       muc con thi moi con so bi day xuong mot dong rieng. */
    html += '<div class="card" style="padding:11px 13px;border:1.5px solid #fcd34d;background:#fffbeb">' +
      '<div style="font-size:12.5px;color:#92400e;line-height:1.65">' +
      'Kỳ này có <b>' + money(kq.tong_dong) + '</b> dòng, màn hình đang hiện <b>' + money(kq.gioi_han) +
      '</b> dòng đầu. Dòng TỔNG bên dưới vẫn cộng đủ cả ' + money(kq.tong_dong) +
      ' dòng. Bấm Xuất Excel để lấy bản đầy đủ.</div></div>';
  }

  if (bcXem === 'bieu_do') html += bcVeBieuDo(kq);
  else if (bcXem === 'the') html += bcVeThe(kq);
  else html += bcVeBang(kq);

  if (kq.phu && (kq.phu.dong || []).length) {
    html += '<div class="sec">' + h(kq.phu.tieu_de) + '</div>' +
      bcVeBang({ cot: kq.phu.cot, dong: kq.phu.dong, cong: null });
  }

  var b = frame('Báo cáo ' + kq.ma, html, { footer: '<button class="btn" id="bcExcel">📥 Xuất Excel cho kế toán</button>' });
  bcNoiThanh(b, function () { go(scrBaoCaoXem, true); });

  var nx = document.getElementById('bcExcel');
  if (nx) nx.onclick = async function () {
    busy(true);
    try {
      var ts2 = bcThamSo(); ts2.ma = kq.ma;
      if (bcLocNguon) ts2.nguon = bcLocNguon;
      if (bcLocPt) ts2.pt = bcLocPt;
      var f = await api('vagabond.bao_cao.xuat_excel', ts2);
      busy(false);
      bcTaiVe(f.ten_file, f.b64);
      toast('Đã tải ' + f.ten_file);
    } catch (e) { busy(false); toast((e && e.message) || 'Không xuất được'); }
  };
}

/* Doi chuoi base64 may chu gui ve thanh file tren may nguoi dung. Lam o
   day chu khong mo tab moi: tren dien thoai mo tab la trinh duyet hoi
   "tai xuong?" hai lan, nhan vien tuong hong. */
function bcTaiVe(ten, b64, kieu) {
  var thoi = atob(b64);
  var so = new Uint8Array(thoi.length);
  for (var i = 0; i < thoi.length; i++) so[i] = thoi.charCodeAt(i);
  /* Mac dinh van la xlsx vi ca chuc cho dang goi ham nay chi de tai Excel.
     Truyen them kieu khi tai tep khac (zip bo ho so chang han) - dat sai
     MIME thi Safari tren dien thoai doi duoi tep, mo ra khong duoc. */
  var blob = new Blob([so], { type: kieu || 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url; a.download = ten;
  document.body.appendChild(a); a.click();
  setTimeout(function () { URL.revokeObjectURL(url); a.remove(); }, 1500);
}



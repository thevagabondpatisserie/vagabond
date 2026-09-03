/* ---------- 5d. Ba man con lai cua phan he Xuat kho ----------

Anh Viet chot 02/09/2026. Truoc hom nay phan he chi co Xuat huy va Dieu
chuyen, nen:

- Banh cho Marketing chup anh phai lap phieu XUAT HUY. Gia tri to banh do
  vao cung tai khoan voi hang hong, va cuoi thang bao cao hao hut do oan
  cho Bep.
- Hang loi tra ve nha cung cap khong co duong nao ca. Lam phieu xuat thuong
  thi hang di ma cong no van nguyen, ke toan phai go but toan tay.
- Don si giao cho khach doanh nghiep khong co phieu giao hang, nen khong co
  chung tu nao ghi gia von cho no.

Ba man nay de moi viec that di dung mot duong, thay vi muon tam cai nut gan
giong nhat. Dat trong tep RIENG chu khong nhet vao 03-kho-chung-tu.js: tep
do dang la 1.184 dong va cac phien khac hay sua no, tach ra la bot mot cho
de dung nhau.

DUNG LAI 03/09/2026 (v396), anh Viet chup hai man nay va noi: *"giao dien
phan xuat kho dang khong dong bo voi giao dien dep cua app thi ca, lai bi rat
tho so"*. Ban dau tien dung bay o `<select>` xo danh sach, dong hang khong co
anh mon, man danh sach khong co chip loc va the tom tat. Nay ba man di theo
bo nguyen tac thiet ke o AGENTS.md muc 2b:

- Chon la tim: nha cung cap, phieu nhap goc, bo phan, khach hang mo bottom
  sheet co o tim (`sheet(..., true)`); muc dich, ly do, kho la hang chip.
- Chip trang thai, chip nhom, chip ngay tren man danh sach, kem the tom tat.
- Cho nao co ten mon la co anh mon (`anhMon`). Dong hang co nut tru cong,
  vuot ton thi vien do tai cho.
- Nut chinh dinh day man, noi ro viec.

Van dung lai khung san co cua 03: `frame`, `vxTheRow`, `scrXkChonHang`,
`vxUpAnh`, cac lop `.vf .vfh .vxr`. Bo cai ban chep `xktDongHtml` cu.
*/

var XKT = {
  /* Trang thai man Xuat dung noi bo */
  nb: { gio: [], kho: '', mucDich: '', boPhan: '', ghiChu: '', anh: '', tab: 'cho', nhom: '', ngay: 30, tim: '' },
  /* Trang thai man Tra nha cung cap */
  tra: { ncc: '', tenNcc: '', phieu: '', tenPhieu: '', lyDo: '', ghiChu: '', anh: '', dong: [], tab: '', nhom: '', ngay: 30, tim: '' },
  /* Trang thai man Xuat ban si */
  si: { gio: [], kho: '', khach: '', tenKhach: '', nguoiNhan: '', ghiChu: '', tab: '', nhom: '', ngay: 90, tim: '' },
  bootNb: null,
  bootTra: null,
  bootSi: null
};

/* ==================================================================
   0. BO DUNG CHUNG cua ba man: chip, o chon dang the, dong hang co anh,
      the tom tat, hang chip cuon ngang. Tat ca deu la ham thuan tra HTML.
   ================================================================== */

/* Hang chip CUON NGANG. kmHangChip cua 13 thi xuong dong (wrap), hop voi
   it chip; man danh sach co ba hang chip ma de wrap thi man cao gap doi
   truoc khi thay dong dau tien. */
function xktHangChip(noiDung) {
  return '<div style="display:flex;gap:7px;overflow-x:auto;padding:2px 2px 8px;' +
    '-webkit-overflow-scrolling:touch;scrollbar-width:none">' + noiDung + '</div>';
}

function xktChip(attr, chu, dangChon, mau) {
  return posChipNut(attr, chu, dangChon, false, mau);
}

/* Hang chip tu mot danh sach {k, ten, ic}, co dem so, mot cai dang chon. */
function xktChipNhom(ds, dangChon, thuoc, dem) {
  return xktHangChip(ds.map(function (n) {
    var so = dem ? dem[n.k] : null;
    return xktChip(thuoc + '="' + h(n.k) + '"',
      (n.ic ? n.ic + ' ' : '') + h(n.ten) + (so ? ' <b>' + so + '</b>' : ''), dangChon === n.k);
  }).join(''));
}

/* Chip trang thai tren tung dong: xanh xong, vang cho, do can xu, xam huy.
   MOT bang mau cho ca ba man, khong man nao tu chon mau rieng. */
var XKT_MAU_TT = {
  cho: ['#fef0c7', '#b54708'],
  xong: ['#d1fadf', '#027a48'],
  loi: ['#fee4e2', '#912018'],
  huy: ['#eceff2', '#5c6670']
};
function xktChipTT(loai, chu) {
  var m = XKT_MAU_TT[loai] || XKT_MAU_TT.cho;
  return '<span style="display:inline-block;font-size:12px;font-weight:700;border-radius:999px;' +
    'padding:3px 10px;background:' + m[0] + ';color:' + m[1] + ';white-space:nowrap">' + h(chu) + '</span>';
}
function xktLoaiTT(x) {
  if (x.vgb_huy || x.docstatus === 2) return 'huy';
  return x.docstatus === 1 ? 'xong' : 'cho';
}

/* O CHON DANG THE. Thay cho <select>: hien gia tri dang chon (anh hoac
   bieu tuong, ten dam, dong phu xam) va mui ten; cham vao la nguoi goi mo
   sheet tim hay hang chip. Chua chon thi hien loi nhac cham. */
function xktOChon(id, ic, nhan, gt, opt) {
  opt = opt || {};
  var coGt = !!(gt && gt.ten);
  var trai = coGt && gt.anh ? anhMon(gt.anh) :
    '<div class="imm immp" style="font-size:20px">' + (coGt ? (gt.ic || ic) : ic) + '</div>';
  return '<div class="vf" id="' + id + 'O">' +
    '<div class="vfh"><span class="ic">' + ic + '</span><b>' + h(nhan) + '</b>' +
    (opt.batBuoc ? '<span class="bat">Bắt buộc</span>' : '') + '</div>' +
    '<div class="xktthe" id="' + id + '" role="button" tabindex="0">' + trai +
    '<div style="flex:1;min-width:0">' +
    (coGt
      ? '<div style="font-size:15px;font-weight:700;color:#101828;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + h(gt.ten) + '</div>' +
        (gt.phu ? '<div style="font-size:12px;color:#98a2b3;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + h(gt.phu) + '</div>' : '')
      : '<div style="font-size:15px;color:#98a2b3">' + h(opt.nhac || 'Chạm để chọn') + '</div>') +
    '</div><span style="color:#98a2b3;font-size:20px;flex:none">›</span></div>' +
    (opt.mo ? '<div class="vfm" id="' + id + 'Mo" style="margin-top:8px">' + h(opt.mo) + '</div>' : '') +
    '</div>';
}

/* Khoi chip trong mot the bieu mau: nhan + hang chip, cho o chon duoi 8 lua
   chon (muc dich, ly do, kho). */
function xktOChip(id, ic, nhan, ds, dangChon, opt) {
  opt = opt || {};
  return '<div class="vf" id="' + id + 'O">' +
    '<div class="vfh"><span class="ic">' + ic + '</span><b>' + h(nhan) + '</b>' +
    (opt.batBuoc ? '<span class="bat">Bắt buộc</span>' : '') + '</div>' +
    '<div id="' + id + '">' + xktChipNhom(ds, dangChon, 'data-' + id) + '</div>' +
    (opt.mo !== undefined ? '<div class="vfm" id="' + id + 'Mo">' + h(opt.mo || '') + '</div>' : '') +
    '</div>';
}

function xktCss() {
  vgbCss();
  if (document.getElementById('xktCss')) return;
  var st = document.createElement('style');
  st.id = 'xktCss';
  st.textContent =
    '.xktthe{display:flex;align-items:center;gap:11px;border:1.5px solid #d0d5dd;border-radius:12px;' +
    'padding:10px 12px;min-height:56px;background:#fff;cursor:pointer;-webkit-tap-highlight-color:transparent}' +
    '.xktthe:active{background:#f8fafc}' +
    '.thieu>.xktthe,.xktthe.thieu{border-color:#fda29b;background:#fffbfa}' +
    '.thieu.vf{box-shadow:0 0 0 2px #fecdca}' +
    '.xktd{display:flex;align-items:center;gap:10px;background:#fff;border-radius:12px;' +
    'padding:10px 12px;margin-bottom:8px;box-shadow:0 1px 2px rgba(16,24,40,.06)}' +
    '.xktd .t{flex:1;min-width:0}' +
    '.xktd .t b{display:block;font-size:14.5px;color:#101828;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}' +
    '.xktd .t i{font-style:normal;font-size:12px;color:#98a2b3;display:block;margin-top:2px}' +
    '.xktd .t i.r{color:#b42318;font-weight:600}' +
    '.xktsl{display:flex;align-items:center;gap:0;flex:none}' +
    '.xktsl button{width:36px;height:40px;border:1px solid #d0d5dd;background:#fff;font-size:20px;color:#101828;cursor:pointer}' +
    '.xktsl button:first-child{border-radius:10px 0 0 10px}.xktsl button:last-child{border-radius:0 10px 10px 0}' +
    '.xktsl input{width:60px;height:40px;text-align:center;border:1px solid #d0d5dd;border-left:0;border-right:0;font-size:15px;font-weight:700;color:#101828}' +
    '.xktsl input.r{border-color:#fda29b;background:#fffbfa;color:#b42318}' +
    '.xktx{border:0;background:transparent;color:#d92d20;font-size:22px;padding:0 2px 0 6px;flex:none}' +
    '.xkttt{background:#fff;border-radius:14px;padding:14px;margin-bottom:12px;box-shadow:0 1px 2px rgba(16,24,40,.06)}' +
    '.xkttt .n{font-size:22px;font-weight:800;color:#101828}' +
    '.xkttt .m{font-size:12.5px;color:#667085;margin-top:3px;line-height:1.6}' +
    '.xktnut{position:sticky;bottom:0;padding:10px 0 calc(env(safe-area-inset-bottom,0px) + 8px);' +
    'background:linear-gradient(180deg,rgba(243,244,246,0),#f3f4f6 35%);margin-top:6px}' +
    '.xktnut .vxb{margin-top:0}' +
    '.xktvet{font-size:12px;color:#98a2b3;line-height:1.7;padding:6px 2px}';
  document.head.appendChild(st);
}

/* DONG HANG trong phieu: anh, ten, dong phu, nut tru cong, o so, nut bo.
   Vuot ton thi vien do va cau ngan ngay tai dong, khong doi bam Luu. */
function xktDongHtml(gio, opt) {
  opt = opt || {};
  if (!gio.length) {
    return '<div style="text-align:center;color:#98a2b3;padding:22px 0;font-size:14px">' +
      h(opt.rong || 'Chưa có món nào. Bấm Thêm hàng ở dưới.') + '</div>';
  }
  var s = '';
  for (var i = 0; i < gio.length; i++) {
    var d = gio[i];
    var toiDa = (opt.khoaTon && d.ton != null) ? Number(d.ton) : (d.con != null ? Number(d.con) : null);
    var qua = toiDa != null && Number(d.sl) > toiDa + 1e-9;
    var phu = h(d.ma) + (d.dvt ? ' · ' + h(d.dvt) : '');
    if (d.ton != null) phu += ' · tồn ' + vxSo(d.ton);
    if (d.da_nhan != null) phu += ' · đã nhận ' + vxSo(d.da_nhan) + (d.da_tra ? ', đã trả ' + vxSo(d.da_tra) : '') + ' · còn trả được ' + vxSo(d.con);
    s += '<div class="xktd">' + anhMon(d.anh) +
      '<div class="t"><b>' + h(d.ten || d.ma) + '</b><i>' + phu + '</i>' +
      (qua ? '<i class="r">Vượt ' + (d.ton != null && opt.khoaTon ? 'tồn' : 'số còn trả được') + ' ' + vxSo(toiDa) + '</i>' : '') +
      '</div>' +
      '<div class="xktsl"><button type="button" data-xkm="' + i + '">−</button>' +
      '<input type="number" inputmode="decimal" min="0" step="any" value="' + (d.sl == null ? 0 : d.sl) +
      '" data-xsl="' + i + '" class="' + (qua ? 'r' : '') + '">' +
      '<button type="button" data-xkp="' + i + '">+</button></div>' +
      (opt.khongBo ? '' : '<button type="button" class="xktx" data-xbo="' + i + '" aria-label="Bỏ món">&times;</button>') +
      '</div>';
  }
  return s;
}

function xktNoiDong(body, gio, opt, sauDoi) {
  var o = body.querySelector('#vxDong');
  if (o) o.innerHTML = xktDongHtml(gio, opt);
  xktNoiSuKien(body, gio, opt, sauDoi);
}

function xktNoiSuKien(body, gio, opt, sauDoi) {
  function doi(i, v) {
    v = Number(v || 0);
    if (v < 0) v = 0;
    /* Lam tron ba so le: kg va lit co phan le, con bam +/- thi buoc 1 */
    gio[i].sl = Math.round(v * 1000) / 1000;
    xktNoiDong(body, gio, opt, sauDoi);
    if (sauDoi) sauDoi();
  }
  var qs = body.querySelectorAll('[data-xsl]');
  for (var i = 0; i < qs.length; i++) {
    qs[i].onchange = function () { doi(+this.dataset.xsl, this.value); };
  }
  var ms = body.querySelectorAll('[data-xkm]');
  for (var j = 0; j < ms.length; j++) {
    ms[j].onclick = function () { var k = +this.dataset.xkm; doi(k, Number(gio[k].sl || 0) - 1); };
  }
  var ps = body.querySelectorAll('[data-xkp]');
  for (var k2 = 0; k2 < ps.length; k2++) {
    ps[k2].onclick = function () { var k = +this.dataset.xkp; doi(k, Number(gio[k].sl || 0) + 1); };
  }
  var bs = body.querySelectorAll('[data-xbo]');
  for (var l = 0; l < bs.length; l++) {
    bs[l].onclick = function () {
      gio.splice(+this.dataset.xbo, 1);
      xktNoiDong(body, gio, opt, sauDoi);
      if (sauDoi) sauDoi();
    };
  }
}

/* Tong gia tri dong hang khi biet don gia (phieu tra). */
function xktTongDong(gio) {
  var t = 0;
  for (var i = 0; i < gio.length; i++) t += Number(gio[i].sl || 0) * Number(gio[i].don_gia || 0);
  return t;
}

/* THE TOM TAT dau man danh sach: so phieu, tong tien, chia theo trang thai.
   Bam vao con so la loc theo trang thai do. */
function xktTomTat(ds, tienCua, ten) {
  var n = ds.length, tien = 0, cho = 0, xong = 0;
  for (var i = 0; i < n; i++) {
    tien += Number(tienCua(ds[i]) || 0);
    if (xktLoaiTT(ds[i]) === 'xong') xong++; else if (xktLoaiTT(ds[i]) === 'cho') cho++;
  }
  return '<div class="xkttt"><div class="n">' + n + ' ' + h(ten) + ' · ' + vxSo(tien) + ' đ</div>' +
    '<div class="m">' +
    '<span data-tt="cho" style="cursor:pointer">🟡 Chờ ghi sổ <b>' + cho + '</b></span> · ' +
    '<span data-tt="xong" style="cursor:pointer">🟢 Đã ghi sổ <b>' + xong + '</b></span>' +
    '</div></div>';
}

/* Dong danh sach: tieu de, meta, chip trang thai, tien ben phai. */
function xktTheRow(x, tieuDe, meta, tien) {
  return '<div class="vxr" data-xem="' + h(x.name) + '" style="align-items:flex-start">' +
    '<div class="t"><b>' + h(tieuDe) + '</b><i>' + h(meta) + '</i>' +
    '<div style="margin-top:6px">' + xktChipTT(xktLoaiTT(x), x.trang_thai || '') + '</div></div>' +
    '<div style="text-align:right;flex:none"><div style="font-weight:700;font-size:14px;color:#101828">' +
    (tien ? vxSo(tien) + ' đ' : '') + '</div></div></div>';
}

var XKT_NGAY = [[7, '7 ngày'], [30, '30 ngày'], [90, '90 ngày'], [365, 'Một năm']];

/* Loc danh sach theo bo loc cua man: trang thai, nhom, so ngay, o tim. */
function xktLoc(ds, st, khoa, nhomCua, timCua) {
  var moc = new Date(Date.now() - Number(st.ngay || 30) * 864e5).toISOString().slice(0, 10);
  var q = (st.tim || '').toLowerCase().trim();
  return ds.filter(function (x) {
    if (st.tab && xktLoaiTT(x) !== st.tab) return false;
    if (st.nhom && nhomCua(x) !== st.nhom) return false;
    if (x.posting_date && String(x.posting_date) < moc) return false;
    if (q && (timCua(x) || '').toLowerCase().indexOf(q) < 0) return false;
    return true;
  });
}

function xktDemNhom(ds, nhomCua) {
  var d = {};
  for (var i = 0; i < ds.length; i++) { var k = nhomCua(ds[i]); if (k) d[k] = (d[k] || 0) + 1; }
  return d;
}

function xktDemTT(ds) {
  var d = { '': ds.length };
  for (var i = 0; i < ds.length; i++) { var k = xktLoaiTT(ds[i]); d[k] = (d[k] || 0) + 1; }
  return d;
}

var XKT_TT = [{ k: '', ten: 'Tất cả' }, { k: 'cho', ten: 'Chờ ghi sổ', ic: '🟡' }, { k: 'xong', ten: 'Đã ghi sổ', ic: '🟢' }];

/* KHOI BAO LOI DO khi may chu khong tra duoc danh sach.

   Ban v387 nuot loi im lang (catch rong), nen khi xuat_ban.ds_phieu do vi doc
   cot `remarks` khong co tren Delivery Note, man chi hien "Chua co phieu nao"
   nhu binh thuong. Loi nam do ba ngay khong ai biet (03/09/2026). Tu nay may
   chu do thi noi ro, va bao chup man gui anh Viet. */
function xktLoiHtml(loi) {
  return '<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:10px;' +
    'padding:14px;margin:8px 0;font-size:13px;color:#991b1b;line-height:1.6">' +
    '<b>Không đọc được danh sách phiếu.</b><br>' + h(loi) +
    '<br><span style="color:#7f1d1d;font-size:12px">Chụp màn này gửi anh Việt giúp.</span></div>';
}

/* Man danh sach dung chung: tim, ba hang chip, the tom tat, cac dong. */
function xktManDanhSach(cfg) {
  var st = cfg.st;
  function ve() {
    var loc = xktLoc(cfg.ds, st, cfg.khoa, cfg.nhomCua, cfg.timCua);
    var demTT = xktDemTT(cfg.ds);
    var demNhom = xktDemNhom(cfg.ds, cfg.nhomCua);
    var nhoms = [{ k: '', ten: cfg.nhomTatCa || 'Mọi nhóm' }].concat(cfg.nhoms.filter(function (n) { return demNhom[n.k]; }));
    var rows = '';
    for (var i = 0; i < loc.length; i++) rows += cfg.row(loc[i]);
    if (cfg.loi && !cfg.ds.length) {
      rows = xktLoiHtml(cfg.loi);
    } else if (!loc.length) {
      rows = '<div class="emp"><div class="e1">' + (cfg.ds.length ? '🔎' : '📭') + '</div><div class="e2">' +
        h(cfg.ds.length ? 'Không có phiếu nào khớp bộ lọc. Chạm chip để bỏ bớt điều kiện.' : (cfg.rong || 'Chưa có phiếu nào. Bấm nút + để lập phiếu.')) + '</div></div>';
    }
    return (cfg.moTa ? '<div style="font-size:11.5px;color:#98a2b3;padding:0 2px 8px;line-height:1.6">' + cfg.moTa + '</div>' : '') +
      srchBox('xktTim', cfg.timNhac || 'Tìm số phiếu, tên, người lập...', st.tim) +
      xktTomTat(cfg.ds, cfg.tienCua, cfg.tenPhieu || 'phiếu') +
      xktChipNhom(XKT_TT, st.tab, 'data-tb', demTT) +
      xktChipNhom(nhoms, st.nhom, 'data-nh', demNhom) +
      xktHangChip(XKT_NGAY.map(function (n) {
        return xktChip('data-ng="' + n[0] + '"', h(n[1]), Number(st.ngay) === n[0]);
      }).join('')) +
      (st.tab || st.nhom || st.tim
        ? '<div style="font-size:12px;color:#0b7c93;font-weight:700;padding:4px 2px 8px">Tổng theo bộ lọc · ' + loc.length + ' phiếu · ' +
          vxSo(loc.reduce(function (t, x) { return t + Number(cfg.tienCua(x) || 0); }, 0)) + ' đ</div>'
        : '') +
      '<div id="xktLst">' + rows + '</div>';
  }
  var body = frame(cfg.tieuDe, '<div class="vxf">' + ve() + '</div>', { fab: 1, onFab: cfg.onFab });
  function veLai() {
    var el = body.querySelector('.vxf'); if (el) el.innerHTML = ve();
    var inp = body.querySelector('#xktTim');
    if (inp) inp.oninput = function () { st.tim = this.value; var lst = body.querySelector('#xktLst'); if (lst) { var loc2 = xktLoc(cfg.ds, st, cfg.khoa, cfg.nhomCua, cfg.timCua); lst.innerHTML = loc2.map(cfg.row).join('') || '<div class="emp"><div class="e1">🔎</div><div class="e2">Không có phiếu nào khớp.</div></div>'; } };
  }
  veLai();
  body.onclick = function (e) {
    var t;
    if ((t = e.target.closest('[data-tb]'))) { st.tab = t.dataset.tb; return veLai(); }
    if ((t = e.target.closest('[data-tt]'))) { st.tab = st.tab === t.dataset.tt ? '' : t.dataset.tt; return veLai(); }
    if ((t = e.target.closest('[data-nh]'))) { st.nhom = t.dataset.nh; return veLai(); }
    if ((t = e.target.closest('[data-ng]'))) { st.ngay = Number(t.dataset.ng); return veLai(); }
    if ((t = e.target.closest('[data-xem]'))) { var n = t.dataset.xem; go(function () { cfg.xem(n); }); }
  };
  return body;
}

/* Mo sheet tim tu mot danh sach {value,label,phu,img,icon}. */
function xktSheetTim(tieuDe, items, cur, onPick) {
  return sheet(tieuDe, items, cur, onPick, true);
}

/* Danh dau o thieu va cuon toi o dau tien. */
function xktBaoThieu(body, ds) {
  var dau = null;
  for (var i = 0; i < ds.length; i++) {
    var el = body.querySelector('#' + ds[i][0] + 'O');
    if (!el) continue;
    el.classList.toggle('thieu', !!ds[i][1]);
    if (ds[i][1] && !dau) dau = el;
  }
  if (dau) { try { dau.scrollIntoView({ block: 'center', behavior: 'smooth' }); } catch (e) { } }
  return !!dau;
}

/* Khoi anh dinh kem, dung chung. */
function xktOAnh(id, nhan, nhac, phu, anhCu) {
  return '<div class="vf">' +
    '<div class="vfh"><span class="ic">📷</span><b>' + h(nhan) + '</b></div>' +
    '<label class="vfa' + (anhCu ? ' xong' : '') + '" id="' + id + 'O">' +
    '<input type="file" accept="image/*" id="' + id + '">' +
    '<div class="i">📷</div>' +
    '<div class="t" id="' + id + 'T">' + h(anhCu ? 'Đã có ảnh' : nhac) + '</div>' +
    '<div class="p" id="' + id + 'P">' + h(anhCu ? 'Chạm để đổi ảnh khác' : phu) + '</div>' +
    '</label><div id="' + id + 'Ok">' + (anhCu ? '<img class="vfanh" alt="" src="' + h(anhCu) + '">' : '') + '</div>' +
    '</div>';
}
function xktNoiAnh(body, id, luu) {
  var inp = body.querySelector('#' + id);
  if (!inp) return;
  inp.onchange = async function () {
    var f = this.files && this.files[0];
    if (!f) return;
    var t = body.querySelector('#' + id + 'T');
    var pp = body.querySelector('#' + id + 'P');
    var ok = body.querySelector('#' + id + 'Ok');
    t.textContent = 'Đang tải ảnh lên...';
    pp.textContent = f.name || '';
    ok.textContent = '';
    try {
      var url = await vxUpAnh(f);
      luu(url);
      body.querySelector('#' + id + 'O').classList.add('xong');
      t.textContent = 'Đã có ảnh';
      pp.textContent = 'Chạm để đổi ảnh khác';
      ok.innerHTML = '<img class="vfanh" alt="" src="' + h(url) + '">';
    } catch (e) {
      t.textContent = 'Không tải được ảnh';
      pp.textContent = (e && e.message) || String(e);
    }
  };
}

/* Chon kho xuat: duoi 8 kho thi chip, nhieu hon thi sheet tim. Tra ve HTML
   va ham noi su kien. Kho da chon duoc nho lai cho lan sau. */
function xktKhoHtml(id, dsKho, chon) {
  var g0 = khoGiuCuaToi();
  var ds = dsKho || [];
  if (g0.length) {
    var loc = ds.filter(function (x) { return g0.indexOf(x.name) >= 0; });
    if (loc.length) ds = loc;
  }
  var items = ds.map(function (k) { return { k: k.name, ten: k.warehouse_name || k.name }; });
  if (items.length <= 8) return { html: xktOChip(id, '🏬', 'Kho xuất', items, chon, { batBuoc: 1 }), items: items, chip: 1 };
  var gt = null;
  for (var i = 0; i < items.length; i++) if (items[i].k === chon) gt = { ten: items[i].ten, phu: items[i].k, ic: '🏬' };
  return { html: xktOChon(id, '🏬', 'Kho xuất', gt, { batBuoc: 1, nhac: 'Chạm để chọn kho' }), items: items, chip: 0 };
}

function xktVet(d) {
  var s = 'Lập bởi ' + h(d.nguoi_tao || '') + (d.ngay ? ' · ' + h(d.ngay) : '');
  if (d.nguoi_ghi_so) s += '<br>Ghi sổ bởi ' + h(d.nguoi_ghi_so) + (d.luc_ghi_so ? ' · ' + h(d.luc_ghi_so) : '');
  if (d.so_lan_sua) s += '<br>' + xktChipTT('cho', 'Đã sửa ' + d.so_lan_sua + ' lần');
  return '<div class="xktvet">' + s + '</div>';
}

/* Dong hang tren man XEM: anh, ten, ma, so luong, tien. */
function xktDongXem(rows) {
  var s = '';
  for (var i = 0; i < rows.length; i++) {
    var x = rows[i];
    s += '<div class="xktd">' + anhMon(x.anh) + '<div class="t"><b>' + h(x.ten || x.ma) + '</b>' +
      '<i>' + h(x.ma) + (x.tien ? ' · ' + vxSo(x.tien) + ' đ' : '') + '</i></div>' +
      '<span style="font-weight:800;font-size:15px;flex:none">' + vxSo(x.sl) + ' ' + h(x.dvt || '') + '</span></div>';
  }
  return s;
}

function xktDauPhieu(d, dongPhu) {
  return '<div class="xkttt" style="display:flex;align-items:center;gap:10px">' +
    '<div style="flex:1;min-width:0"><div class="n" style="font-size:17px">' + h(d.name) + '</div>' +
    '<div class="m">' + h(dongPhu || '') + '</div></div>' +
    xktChipTT(xktLoaiTT(d), d.trang_thai || '') + '</div>';
}

function xktNutChinh(id, chu, phu) {
  return '<div class="xktnut"><button class="vxb" id="' + id + '">' + h(chu) + '</button>' +
    (phu ? '<div style="font-size:12px;color:#98a2b3;text-align:center;margin-top:8px">' + h(phu) + '</div>' : '') + '</div>';
}

function xktBoPhanItems(khoi) {
  var ra = [];
  for (var i = 0; i < (khoi || []).length; i++) {
    var k = khoi[i];
    for (var j = 0; j < k.bo_phan.length; j++) {
      ra.push({ value: k.bo_phan[j].ten, label: k.bo_phan[j].ten, phu: k.nhom, icon: '🏛️', tim: k.nhom });
    }
  }
  return ra;
}

/* ==================================================================
   1. XUAT DUNG NOI BO
   ================================================================== */

async function xktBootNb() {
  if (!XKT.bootNb) XKT.bootNb = await api('vagabond.xuat_noi_bo.khoi_dong');
  return XKT.bootNb;
}

async function scrXkNbList() {
  xktCss();
  frame('Xuất dùng nội bộ', '<div class="emp"><div class="e1">⏳</div></div>');
  var b = await xktBootNb();
  var loiDs = '';
  var ds = [];
  try { ds = (await api('vagabond.xuat_noi_bo.ds_phieu', { gioi_han: 200 })) || []; } catch (e) { loiDs = errMsg(e) || 'Không đọc được danh sách phiếu.'; }
  var nhoms = (b.muc_dich || []).map(function (m) { return { k: m.ma, ten: m.ten }; });
  xktManDanhSach({
    tieuDe: 'Xuất dùng nội bộ',
    st: XKT.nb,
    ds: ds,
    loi: loiDs,
    moTa: 'Hàng ra khỏi kho mà <b>tiệm vẫn dùng</b>: chụp ảnh, mẫu thử, mời khách, ăn ca. Hàng hỏng thật thì vẫn đi đường Xuất huỷ.',
    tenPhieu: 'phiếu',
    nhoms: nhoms,
    nhomTatCa: 'Mọi mục đích',
    nhomCua: function (x) { return x.vgb_muc_dich_xuat || ''; },
    tienCua: function (x) { return x.total_outgoing_value; },
    timCua: function (x) { return [x.name, x.ten_muc_dich, x.nguoi_tao, x.remarks].join(' '); },
    timNhac: 'Tìm số phiếu, mục đích, người lập...',
    rong: 'Chưa có phiếu xuất dùng nào. Bấm nút + để lập phiếu.',
    row: function (x) {
      return xktTheRow(x, x.ten_muc_dich || x.name,
        [x.name, x.posting_date, x.so_dong ? x.so_dong + ' món' : '', x.nguoi_tao].filter(Boolean).join(' · '),
        x.total_outgoing_value);
    },
    xem: scrXkNbView,
    onFab: function () {
      XKT.nb.gio = []; XKT.nb.mucDich = ''; XKT.nb.boPhan = '';
      XKT.nb.ghiChu = ''; XKT.nb.anh = '';
      go(scrXkNbNew);
    }
  });
}

/* Keo gio tu man chon hang (03) ve trang thai cua man lap phieu. Man chon
   hang ghi vao XK.gio roi back(); man lap phieu ve lai tu dau ham nen phai
   doc XK.gio o day, va chi doc khi chinh minh vua mo man chon (co dangChon),
   keo lan mo sau tu danh sach lai keo nham gio cu cua man khac. */
function xktKeoGioVe(st) {
  if (!st.dangChon) return;
  st.dangChon = false;
  st.gio = (XK.gio || []).slice();
}

async function scrXkNbNew() {
  xktCss();
  if (!XKT.nb.kho) { try { XKT.nb.kho = localStorage.getItem('vgbKhoXuat') || ''; } catch (e) { } }
  frame('Lập phiếu xuất dùng nội bộ', '<div class="emp"><div class="e1">⏳</div></div>');
  var b = await xktBootNb();
  var st = XKT.nb;
  xktKeoGioVe(st);
  var mucDichs = (b.muc_dich || []).map(function (m) { return { k: m.ma, ten: m.ten }; });
  var bpItems = xktBoPhanItems(b.bo_phan);

  function moMucDich() {
    for (var i = 0; i < b.muc_dich.length; i++) if (b.muc_dich[i].ma === st.mucDich) return b.muc_dich[i].mo;
    return 'Chọn mục đích để máy ghi chi phí vào đúng chỗ.';
  }

  function ve() {
    var kho = xktKhoHtml('nbkho', b.kho, st.kho);
    return '<div class="vxf">' +
      kho.html +
      xktOChip('nbmd', '🎯', 'Mục đích xuất dùng', mucDichs, st.mucDich, { batBuoc: 1, mo: moMucDich() }) +
      /* O bo phan la ly do ton tai cua ca man nay. Chon xong thi gia tri hang
         xuat vao dung so cua bo phan do, khong con lan vao hao hut cua Bep. */
      xktOChon('nbbp', '🏛️', 'Bộ phận chịu chi phí',
        st.boPhan ? { ten: st.boPhan, phu: (bpItems.filter(function (x) { return x.value === st.boPhan; })[0] || {}).phu, ic: '🏛️' } : null,
        { batBuoc: 1, nhac: 'Chạm để tìm bộ phận', mo: 'Cuối tháng đọc báo cáo là biết bộ phận nào dùng bao nhiêu.' }) +
      '<div class="vf" id="nbgioO">' +
      '<div class="vfh"><span class="ic">📦</span><b>Danh sách hàng</b><span class="bat">Bắt buộc</span></div>' +
      '<div id="vxDong">' + xktDongHtml(st.gio, { khoaTon: 1 }) + '</div>' +
      '<button class="vxb o" id="nbthem" style="margin-top:8px">+ Thêm hàng</button>' +
      '</div>' +
      /* Anh KHONG bat buoc o day, khac han Xuat huy. Banh mang di chup thi
         chinh tam anh san pham la bang chung. */
      xktOAnh('nbanh', 'Ảnh (không bắt buộc)', 'Chụp hoặc chọn ảnh', 'Chạm vào đây để mở máy ảnh', st.anh) +
      '<div class="vf"><div class="vfh"><span class="ic">📝</span><b>Ghi chú</b></div>' +
      '<input class="vfi" id="nbgc" placeholder="Ví dụ: chụp bộ ảnh Trung thu" value="' + h(st.ghiChu) + '"></div>' +
      xktNutChinh('nbluu', 'Lưu phiếu, chờ quản lý ghi sổ', 'Tồn kho chỉ trừ sau khi quản lý kho bấm Ghi sổ.') +
      '</div>';
  }

  var body = frame('Lập phiếu xuất dùng nội bộ', ve());

  function noi() {
    xktNoiSuKien(body, st.gio, { khoaTon: 1 });
    xktNoiAnh(body, 'nbanh', function (u) { st.anh = u; });
    var gc = body.querySelector('#nbgc');
    gc.oninput = function () { st.ghiChu = this.value; };

    var kho = xktKhoHtml('nbkho', b.kho, st.kho);
    if (!kho.chip) {
      body.querySelector('#nbkho').onclick = function () {
        xktSheetTim('Chọn kho xuất', kho.items.map(function (k) { return { value: k.k, label: k.ten, phu: k.k, icon: '🏬' }; }), st.kho, function (it) { doiKho(it.value); });
      };
    }
    body.querySelector('#nbbp').onclick = function () {
      xktSheetTim('Chọn bộ phận chịu chi phí', bpItems, st.boPhan, function (it) { st.boPhan = it.value; veLai(); });
    };
    body.querySelector('#nbthem').onclick = function () {
      if (!st.kho) { toast('Chọn kho xuất trước đã.'); xktBaoThieu(body, [['nbkho', 1]]); return; }
      var kho2 = st.kho;
      /* Man chon hang cua 03 ghi thang vao XK.gio roi goi back(), KHONG goi
         ham quay ve. Nen muon tam XK.gio, cam co "dang chon", va luc man
         nay ve lai (dau ham) thi keo XK.gio ve gio cua minh. Loi v397 tren
         site that: chon mon xong ve man van "Chua co mon nao". */
      XK.gio = st.gio.slice();
      st.dangChon = true;
      go(function () { scrXkChonHang(kho2, null); });
    };
    body.querySelector('#nbluu').onclick = luu;
  }

  function doiKho(k) {
    if (st.kho && k !== st.kho && st.gio.length) { st.gio = []; toast('Đổi kho nên phải chọn lại hàng.'); }
    st.kho = k;
    try { localStorage.setItem('vgbKhoXuat', st.kho); } catch (e) { }
    veLai();
  }

  function veLai() {
    var vb = body.querySelector('.vxf'); if (vb) vb.outerHTML = ve();
    noi();
  }

  body.onclick = function (e) {
    var t;
    if ((t = e.target.closest('[data-nbkho]'))) return doiKho(t.getAttribute('data-nbkho'));
    if ((t = e.target.closest('[data-nbmd]'))) {
      st.mucDich = t.getAttribute('data-nbmd');
      /* Dien san bo phan hay gap cua muc dich do, nguoi lap doi duoc. Chi
         dien khi o dang TRONG: da chon roi ma bi ghi de la mat cong go lai. */
      for (var i = 0; i < b.muc_dich.length; i++) {
        if (b.muc_dich[i].ma === st.mucDich && b.muc_dich[i].bo_phan && !st.boPhan) st.boPhan = b.muc_dich[i].bo_phan;
      }
      return veLai();
    }
  };

  async function luu() {
    if (xktBaoThieu(body, [['nbkho', !st.kho], ['nbmd', !st.mucDich], ['nbbp', !st.boPhan], ['nbgio', !st.gio.length]])) {
      if (!st.kho) toast('Chưa chọn kho xuất.');
      else if (!st.mucDich) toast('Chưa chọn mục đích xuất dùng.');
      else if (!st.boPhan) toast('Chưa chọn bộ phận chịu chi phí.');
      else toast('Chưa có món nào.');
      return;
    }
    var qua = st.gio.filter(function (d) { return d.ton != null && Number(d.sl) > Number(d.ton) + 1e-9; });
    if (qua.length) { toast('Có ' + qua.length + ' món vượt tồn, sửa số lượng trước.'); return; }
    if (st.gio.some(function (d) { return !(Number(d.sl) > 0); })) { toast('Có món số lượng 0, bỏ món đó hoặc gõ số.'); return; }
    this.disabled = true;
    try {
      var r = await api('vagabond.xuat_noi_bo.luu', {
        kho: st.kho, muc_dich: st.mucDich, bo_phan_chiu: st.boPhan,
        ghi_chu: st.ghiChu, anh: st.anh,
        dong: JSON.stringify(st.gio.map(function (d) { return { ma: d.ma, sl: d.sl }; }))
      });
      st.gio = []; st.anh = ''; st.ghiChu = ''; st.tab = 'cho';
      toast('Đã lưu ' + r.name + ', phiếu chờ quản lý ghi sổ.');
      go(function () { scrXkNbView(r.name); }, true);
    } catch (e) {
      this.disabled = false;
      toast(errMsg(e) || 'Không lưu được phiếu.');
    }
  }

  noi();
}

async function scrXkNbView(name) {
  xktCss();
  frame('Phiếu xuất dùng nội bộ', '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api('vagabond.xuat_noi_bo.chi_tiet', { name: name }); }
  catch (e) { return frame('Phiếu xuất dùng nội bộ', '<div class="emp"><div class="e1">⚠️</div><div class="e2">' + h(errMsg(e) || 'Không mở được phiếu này. Lùi lại rồi thử lại.') + '</div></div>'); }
  var nut = '';
  if (d.docstatus === 0 && !d.vgb_huy) {
    if (d.duoc_duyet) nut += '<button class="vxb" id="nbghi">Ghi sổ phiếu này</button>';
    if (d.la_cua_toi || d.duoc_duyet) nut += '<button class="vxb o" id="nbbo" style="color:#b42318;border-color:#fda29b">Bỏ phiếu này</button>';
    if (!d.duoc_duyet) {
      nut += '<div style="font-size:12px;color:#98a2b3;text-align:center;margin-top:10px">Phiếu đang chờ quản lý kho ghi sổ.</div>';
    }
  }
  var body = frame('Phiếu xuất dùng nội bộ',
    '<div class="vxf">' +
    xktDauPhieu(d, (d.ten_muc_dich || d.muc_dich) + (d.tong_tien ? ' · ' + vxSo(d.tong_tien) + ' đ' : '')) +
    '<div class="vf"><div class="vfh"><span class="ic">🏬</span><b>Kho xuất</b></div><div style="font-size:15px;font-weight:600;padding:2px 0 8px">' + h(d.kho_xuat || '') + '</div>' +
    '<div class="vfh"><span class="ic">🏛️</span><b>Bộ phận chịu chi phí</b></div><div style="font-size:15px;font-weight:600;padding:2px 0 8px">' + h(d.bo_phan || 'chưa ghi') + '</div>' +
    (d.ghi_chu ? '<div class="vfh"><span class="ic">📝</span><b>Ghi chú</b></div><div style="font-size:14px;padding:2px 0 8px">' + h(d.ghi_chu) + '</div>' : '') +
    '</div>' +
    (d.anh ? '<div class="vf"><div class="vfh"><span class="ic">📷</span><b>Ảnh</b></div><img src="' + h(d.anh) + '" style="width:100%;border-radius:12px;display:block;margin:4px 0 8px"></div>' : '') +
    '<div class="vxl">Hàng trong phiếu (' + d.dong.length + ' món)</div>' + xktDongXem(d.dong) +
    (d.tong_tien ? '<div style="text-align:right;font-weight:800;margin-top:4px">Giá trị: ' + vxSo(d.tong_tien) + ' đ</div>' : '') +
    xktVet(d) +
    (nut ? '<div class="xktnut">' + nut + '</div>' : '') + '</div>');

  var g = body.querySelector('#nbghi');
  if (g) g.onclick = async function () {
    if (!await xacNhan('Ghi sổ phiếu ' + d.name + '?\n\nTồn kho sẽ trừ thật và không hoàn lại được từ app.', 'Ghi sổ', 'Ghi sổ')) return;
    busy(true);
    try {
      await api('vagabond.xuat_noi_bo.ghi_so', { name: d.name });
      busy(false); toast('Đã ghi sổ ' + d.name);
      go(function () { scrXkNbView(d.name); }, true);
    } catch (e) { busy(false); baoTin(errMsg(e) || 'Không ghi sổ được'); }
  };
  var bo = body.querySelector('#nbbo');
  if (bo) bo.onclick = async function () {
    if (!await xacNhan('Bỏ phiếu ' + d.name + '?\n\nPhiếu vẫn nằm nguyên trong hệ thống, chỉ không ghi sổ được nữa.', 'Bỏ phiếu', 'Bỏ')) return;
    busy(true);
    try {
      await api('vagabond.xuat_noi_bo.bo_phieu', { name: d.name, ly_do: 'Bỏ phiếu nháp sai' });
      busy(false); toast('Đã bỏ phiếu ' + d.name);
      go(scrXkNbList, true);
    } catch (e) { busy(false); baoTin(errMsg(e) || 'Không bỏ được phiếu'); }
  };
}

/* ==================================================================
   2. XUAT TRA LAI NHA CUNG CAP
   ================================================================== */

async function xktBootTra() {
  if (!XKT.bootTra) XKT.bootTra = await api('vagabond.tra_ncc.khoi_dong');
  return XKT.bootTra;
}

async function scrXkTraList() {
  xktCss();
  frame('Xuất trả nhà cung cấp', '<div class="emp"><div class="e1">⏳</div></div>');
  await xktBootTra();
  var loiDs = '';
  var ds = [];
  try { ds = (await api('vagabond.tra_ncc.ds_phieu', { gioi_han: 200 })) || []; } catch (e) { loiDs = errMsg(e) || 'Không đọc được danh sách phiếu.'; }
  var nccs = {};
  ds.forEach(function (x) { if (x.supplier) nccs[x.supplier] = x.supplier_name || x.supplier; });
  xktManDanhSach({
    tieuDe: 'Xuất trả nhà cung cấp',
    st: XKT.tra,
    ds: ds,
    loi: loiDs,
    moTa: 'Phiếu này vừa <b>giảm tồn kho</b> vừa <b>giảm công nợ phải trả</b>, nên kế toán không phải gõ bút toán tay để nắn lại.',
    tenPhieu: 'phiếu trả',
    nhoms: Object.keys(nccs).map(function (k) { return { k: k, ten: nccs[k], ic: '🏭' }; }),
    nhomTatCa: 'Mọi nhà cung cấp',
    nhomCua: function (x) { return x.supplier || ''; },
    tienCua: function (x) { return Math.abs(Number(x.grand_total || 0)); },
    timCua: function (x) { return [x.name, x.supplier_name, x.return_against, x.vgb_ly_do_tra, x.nguoi_tao].join(' '); },
    timNhac: 'Tìm số phiếu, nhà cung cấp, lý do...',
    rong: 'Chưa có phiếu trả hàng nào. Bấm nút + để lập phiếu.',
    row: function (x) {
      return xktTheRow(x, x.supplier_name || x.supplier || x.name,
        [x.name, x.posting_date, x.vgb_ly_do_tra, x.so_dong ? x.so_dong + ' món' : '', x.nguoi_tao].filter(Boolean).join(' · '),
        Math.abs(Number(x.grand_total || 0)));
    },
    xem: scrXkTraView,
    onFab: function () {
      XKT.tra.ncc = ''; XKT.tra.tenNcc = ''; XKT.tra.phieu = ''; XKT.tra.tenPhieu = ''; XKT.tra.lyDo = '';
      XKT.tra.ghiChu = ''; XKT.tra.anh = ''; XKT.tra.dong = [];
      go(scrXkTraNew);
    }
  });
}

async function scrXkTraNew() {
  xktCss();
  frame('Lập phiếu trả hàng', '<div class="emp"><div class="e1">⏳</div></div>');
  var b = await xktBootTra();
  var st = XKT.tra;
  if (!b.ncc.length) {
    return frame('Lập phiếu trả hàng',
      '<div class="emp"><div class="e1">🏭</div><div class="e2">Không có nhà cung cấp nào có phiếu nhập trong 90 ngày qua, nên chưa trả hàng theo phiếu nào được.</div></div>');
  }
  var nccItems = b.ncc.map(function (n) { return { value: n.ma, label: n.ten, phu: n.ma, icon: '🏭' }; });
  var lyDos = (b.ly_do || []).map(function (l) { return { k: l, ten: l }; });
  var dsPhieu = [];

  function ve() {
    var co = st.dong.filter(function (d) { return Number(d.sl) > 0; });
    return '<div class="vxf">' +
      xktOChon('trncc', '🏭', 'Nhà cung cấp', st.ncc ? { ten: st.tenNcc || st.ncc, phu: st.ncc, ic: '🏭' } : null,
        { batBuoc: 1, nhac: 'Chạm để tìm nhà cung cấp' }) +
      /* Phai chon phieu nhap goc, khong phai de cho kho. Tra hang ma khong
         neo vao phieu nao thi ERPNext khong biet hoan gia nao: mot ma bot
         mua thang truoc 80 nghin mot ky, thang nay 95 nghin. */
      xktOChon('trphieu', '📄', 'Phiếu nhập gốc', st.phieu ? { ten: st.phieu, phu: st.tenPhieu, ic: '📄' } : null,
        { batBuoc: 1, nhac: st.ncc ? 'Chạm để chọn phiếu nhập' : 'Chọn nhà cung cấp trước', mo: 'Neo vào phiếu gốc thì máy hoàn đúng giá đã nhập của lô đó.' }) +
      xktOChip('trly', '❓', 'Lý do trả', lyDos, st.lyDo, { batBuoc: 1 }) +
      '<div class="vf" id="trdongO">' +
      '<div class="vfh"><span class="ic">📦</span><b>Hàng trả lại</b><span class="bat">Bắt buộc</span></div>' +
      '<div id="vxDong">' + (st.phieu
        ? xktDongHtml(st.dong, { khongBo: 1, rong: 'Phiếu này không còn món nào trả được.' })
        : '<div style="text-align:center;color:#98a2b3;padding:22px 0;font-size:14px">Chọn phiếu nhập gốc để máy hiện các món trả được.</div>') +
      '</div>' +
      (co.length ? '<div style="text-align:right;font-weight:800;margin-top:4px">Trả ' + co.length + ' món · ' + vxSo(xktTongDong(st.dong)) + ' đ</div>' : '') +
      '</div>' +
      xktOAnh('tranh', 'Ảnh hàng lỗi (không bắt buộc)', 'Chụp hoặc chọn ảnh hàng lỗi', 'Ảnh này để đối chiếu với nhà cung cấp', st.anh) +
      '<div class="vf"><div class="vfh"><span class="ic">📝</span><b>Ghi chú</b></div>' +
      '<input class="vfi" id="trgc" placeholder="Ví dụ: 2 bịch bột bị mốc góc" value="' + h(st.ghiChu) + '"></div>' +
      xktNutChinh('trluu', 'Lưu và ghi sổ phiếu trả', 'Phiếu ghi sổ ngay: tồn giảm và công nợ phải trả giảm cùng lúc.') +
      '</div>';
  }

  var body = frame('Lập phiếu trả hàng', ve());

  async function napPhieu() {
    if (!st.ncc) return [];
    busy(true);
    try { dsPhieu = (await api('vagabond.tra_ncc.phieu_cua_ncc', { ncc: st.ncc })) || []; }
    catch (e) { dsPhieu = []; }
    busy(false);
    return dsPhieu;
  }

  async function chonPhieu(ten) {
    st.phieu = ten;
    var p = dsPhieu.filter(function (x) { return x.name === ten; })[0] || {};
    st.tenPhieu = [p.posting_date, p.so_dong ? p.so_dong + ' món' : '', p.grand_total ? vxSo(p.grand_total) + ' đ' : ''].filter(Boolean).join(' · ');
    st.dong = [];
    busy(true);
    try {
      var kq = await api('vagabond.tra_ncc.dong_cua_phieu', { phieu: st.phieu });
      /* Chi giu dong CON tra duoc. Bay ca dong con 0 chi lam nguoi ta go
         vao roi bi may tu chuyen ve 0. */
      st.dong = (kq.dong || []).filter(function (d) { return d.con > 0; }).map(function (d) { d.sl = 0; return d; });
      busy(false);
    } catch (e) { busy(false); toast(errMsg(e) || 'Không đọc được phiếu nhập.'); }
    veLai();
  }

  function moSheetPhieu() {
    if (!st.ncc) { toast('Chọn nhà cung cấp trước.'); xktBaoThieu(body, [['trncc', 1]]); return; }
    var items = dsPhieu.map(function (p) {
      return { value: p.name, label: p.name, icon: '📄',
        phu: [p.posting_date, p.so_dong ? p.so_dong + ' món' : '', p.grand_total ? vxSo(p.grand_total) + ' đ' : '', p.set_warehouse].filter(Boolean).join(' · '),
        tim: p.posting_date };
    });
    if (!items.length) { toast('Nhà cung cấp này không có phiếu nhập nào trong 90 ngày.'); return; }
    xktSheetTim('Chọn phiếu nhập gốc', items, st.phieu, function (it) { chonPhieu(it.value); });
  }

  function noi() {
    xktNoiSuKien(body, st.dong, { khongBo: 1 }, function () {
      /* Cap nhat tong ngay khi go, khong ve lai ca man. */
      var el = body.querySelector('#trdongO');
      if (el) veLai();
    });
    xktNoiAnh(body, 'tranh', function (u) { st.anh = u; });
    body.querySelector('#trgc').oninput = function () { st.ghiChu = this.value; };
    body.querySelector('#trncc').onclick = function () {
      xktSheetTim('Chọn nhà cung cấp', nccItems, st.ncc, async function (it) {
        if (it.value !== st.ncc) { st.phieu = ''; st.tenPhieu = ''; st.dong = []; }
        st.ncc = it.value; st.tenNcc = it.label;
        await napPhieu();
        veLai();
        if (!st.phieu) moSheetPhieu();
      });
    };
    body.querySelector('#trphieu').onclick = moSheetPhieu;
    body.querySelector('#trluu').onclick = luu;
  }

  function veLai() {
    var vb = body.querySelector('.vxf'); if (vb) vb.outerHTML = ve();
    noi();
  }

  body.onclick = function (e) {
    var t = e.target.closest('[data-trly]');
    if (t) { st.lyDo = t.getAttribute('data-trly'); veLai(); }
  };

  async function luu() {
    var co = st.dong.filter(function (d) { return Number(d.sl) > 0; });
    if (xktBaoThieu(body, [['trncc', !st.ncc], ['trphieu', !st.phieu], ['trly', !st.lyDo], ['trdong', !co.length]])) {
      toast(!st.ncc ? 'Chưa chọn nhà cung cấp.' : (!st.phieu ? 'Chưa chọn phiếu nhập gốc.' : (!st.lyDo ? 'Chưa chọn lý do trả.' : 'Chưa nhập số lượng trả cho món nào.')));
      return;
    }
    var qua = st.dong.filter(function (d) { return Number(d.sl) > Number(d.con) + 1e-9; });
    if (qua.length) { toast('Có ' + qua.length + ' món trả nhiều hơn số còn trả được.'); return; }
    if (!await xacNhan('Trả ' + co.length + ' món về ' + (st.tenNcc || st.ncc) + '?\n\nPhiếu ghi sổ ngay: tồn giảm và công nợ phải trả giảm cùng lúc.', 'Ghi sổ phiếu trả', 'Ghi sổ')) return;
    this.disabled = true;
    try {
      var r = await api('vagabond.tra_ncc.luu', {
        phieu: st.phieu, ly_do: st.lyDo, ghi_chu: st.ghiChu, anh: st.anh,
        dong: JSON.stringify(co.map(function (d) { return { ma: d.ma, sl: Number(d.sl) }; }))
      });
      st.dong = []; st.anh = ''; st.ghiChu = '';
      toast('Đã ghi sổ phiếu trả ' + r.name);
      go(function () { scrXkTraView(r.name); }, true);
    } catch (e) {
      this.disabled = false;
      baoTin(errMsg(e) || 'Không ghi sổ được phiếu trả.');
    }
  }

  noi();
  if (st.ncc && !dsPhieu.length) napPhieu();
}

async function scrXkTraView(name) {
  xktCss();
  frame('Phiếu trả hàng', '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api('vagabond.tra_ncc.chi_tiet', { name: name }); }
  catch (e) { return frame('Phiếu trả hàng', '<div class="emp"><div class="e1">⚠️</div><div class="e2">' + h(errMsg(e) || 'Không mở được phiếu này. Lùi lại rồi thử lại.') + '</div></div>'); }
  frame('Phiếu trả hàng',
    '<div class="vxf">' +
    xktDauPhieu(d, (d.ten_ncc || d.ncc) + (d.tong_tien ? ' · ' + vxSo(d.tong_tien) + ' đ' : '')) +
    '<div class="vf">' +
    '<div class="vfh"><span class="ic">📄</span><b>Trả theo phiếu nhập</b></div><div style="font-size:15px;font-weight:600;padding:2px 0 8px">' + h(d.phieu_goc || 'chưa neo') + '</div>' +
    '<div class="vfh"><span class="ic">❓</span><b>Lý do trả</b></div><div style="font-size:15px;font-weight:600;padding:2px 0 8px">' + h(d.ly_do || 'chưa ghi') + '</div>' +
    (d.ghi_chu ? '<div class="vfh"><span class="ic">📝</span><b>Ghi chú</b></div><div style="font-size:14px;padding:2px 0 8px">' + h(d.ghi_chu) + '</div>' : '') +
    '</div>' +
    (d.anh ? '<div class="vf"><div class="vfh"><span class="ic">📷</span><b>Ảnh hàng lỗi</b></div><img src="' + h(d.anh) + '" style="width:100%;border-radius:12px;display:block;margin:4px 0 8px"></div>' : '') +
    '<div class="vxl">Hàng trả lại (' + d.dong.length + ' món)</div>' + xktDongXem(d.dong) +
    (d.tong_tien ? '<div style="text-align:right;font-weight:800;margin-top:4px">Giá trị: ' + vxSo(d.tong_tien) + ' đ</div>' : '') +
    xktVet(d) +
    '<div style="font-size:12px;color:#98a2b3;text-align:center;margin-top:8px">Công nợ phải trả nhà cung cấp đã giảm đúng số này.</div></div>');
}

/* ==================================================================
   3. XUAT BAN SI
   ================================================================== */

async function xktBootSi() {
  if (!XKT.bootSi) XKT.bootSi = await api('vagabond.xuat_ban.khoi_dong');
  return XKT.bootSi;
}

async function scrXkSiList() {
  xktCss();
  frame('Xuất bán sỉ', '<div class="emp"><div class="e1">⏳</div></div>');
  await xktBootSi();
  var loiDs = '';
  var ds = [];
  try { ds = (await api('vagabond.xuat_ban.ds_phieu', { gioi_han: 200, so_ngay: 365 })) || []; } catch (e) { loiDs = errMsg(e) || 'Không đọc được danh sách phiếu.'; }
  var khs = {};
  ds.forEach(function (x) { if (x.customer) khs[x.customer] = x.customer_name || x.customer; });
  xktManDanhSach({
    tieuDe: 'Xuất bán sỉ',
    st: XKT.si,
    ds: ds,
    loi: loiDs,
    moTa: 'Phiếu giao hàng cho khách sỉ và khách doanh nghiệp. Phiếu này <b>trừ kho thật</b> và ghi giá vốn.',
    tenPhieu: 'phiếu giao',
    nhoms: Object.keys(khs).map(function (k) { return { k: k, ten: khs[k], ic: '🏢' }; }),
    nhomTatCa: 'Mọi khách',
    nhomCua: function (x) { return x.customer || ''; },
    tienCua: function (x) { return x.grand_total; },
    timCua: function (x) { return [x.name, x.customer_name, x.customer, x.nguoi_tao, x.remarks].join(' '); },
    timNhac: 'Tìm số phiếu, tên khách, người lập...',
    rong: 'Chưa có phiếu giao hàng nào. Bấm nút + để lập phiếu.',
    row: function (x) {
      return xktTheRow(x, x.customer_name || x.customer || x.name,
        [x.name, x.posting_date, x.so_dong ? x.so_dong + ' món' : '', x.nguoi_tao].filter(Boolean).join(' · '),
        x.grand_total);
    },
    xem: scrXkSiView,
    onFab: function () {
      XKT.si.gio = []; XKT.si.khach = ''; XKT.si.tenKhach = '';
      XKT.si.nguoiNhan = ''; XKT.si.ghiChu = '';
      go(scrXkSiNew);
    }
  });
}

/* Sheet tim khach hoi MAY CHU theo tu khoa (danh muc khach hon vai nghin,
   khong tai het ve). Cho go xong hang cai roi moi hoi. */
function xktSheetTimKhach(tieuDe, cur, onPick) {
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>' + h(tieuDe) + '</b><div class="x">&times;</div></div>' +
    '<div style="flex:0 0 auto;padding:10px 14px 4px"><input class="nt" id="xktKhTim" placeholder="Gõ tên hoặc mã khách..." style="height:46px;padding:0 12px;width:100%;box-sizing:border-box"></div>' +
    '<div class="shl"><div class="emp"><div class="e2">Gõ vài chữ tên khách để tìm.</div></div></div>';
  var lst = box.querySelector('.shl');
  var ds = [];
  function ve() {
    lst.innerHTML = ds.length ? ds.map(function (x, i) {
      return '<div class="shi' + (x.name === cur ? ' on' : '') + '" data-i="' + i + '"><span>🏢</span>' +
        '<span style="flex:1;min-width:0">' + h(x.customer_name || x.name) +
        '<div style="color:#a0a6b4;font-size:12px;margin-top:2px">' + h(x.name) + '</div></span>' +
        (x.name === cur ? '<span>&#10003;</span>' : '') + '</div>';
    }).join('') : '<div class="emp"><div class="e2">Không tìm thấy khách nào. Kế toán tạo khách bên Next trước nhé.</div></div>';
  }
  ov.appendChild(box); document.body.appendChild(ov);
  var inp = box.querySelector('#xktKhTim');
  var hen = null;
  inp.oninput = function () {
    clearTimeout(hen);
    var tu = this.value;
    hen = setTimeout(async function () {
      try { ds = (await api('vagabond.xuat_ban.tim_khach', { tu_khoa: tu })) || []; } catch (e) { ds = []; }
      ve();
    }, 350);
  };
  function close() { ov.remove(); }
  ov.onclick = function (e) { if (e.target === ov) close(); };
  box.querySelector('.x').onclick = close;
  lst.onclick = function (e) {
    var r = e.target.closest('.shi'); if (!r) return;
    close(); onPick(ds[+r.dataset.i]);
  };
  setTimeout(function () { try { inp.focus(); } catch (e) { } }, 50);
  return close;
}

async function scrXkSiNew() {
  xktCss();
  if (!XKT.si.kho) { try { XKT.si.kho = localStorage.getItem('vgbKhoXuat') || ''; } catch (e) { } }
  frame('Lập phiếu giao hàng', '<div class="emp"><div class="e1">⏳</div></div>');
  var b = await xktBootSi();
  var st = XKT.si;
  xktKeoGioVe(st);

  function ve() {
    var kho = xktKhoHtml('sikho', b.kho, st.kho);
    return '<div class="vxf">' +
      /* Canh bao nay den tu may chu chu khong go cung o day: co ca kiem chot
         rang cau nay con ton tai. Bo no di la nguoi lap khong con biet vi sao
         ton kho cua don si di khac ban le tai quay. */
      '<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:10px;padding:11px 13px;margin-bottom:12px;font-size:12.5px;color:#92400e;line-height:1.6">⚠️ ' + h(b.canh_bao || '') + '</div>' +
      xktOChon('sikhach', '🏢', 'Khách hàng', st.khach ? { ten: st.tenKhach || st.khach, phu: st.khach, ic: '🏢' } : null,
        { batBuoc: 1, nhac: 'Chạm để tìm khách' }) +
      kho.html +
      '<div class="vf" id="sigioO">' +
      '<div class="vfh"><span class="ic">📦</span><b>Hàng giao</b><span class="bat">Bắt buộc</span></div>' +
      '<div id="vxDong">' + xktDongHtml(st.gio, { khoaTon: 1 }) + '</div>' +
      '<button class="vxb o" id="sithem" style="margin-top:8px">+ Thêm hàng</button>' +
      '</div>' +
      '<div class="vf"><div class="vfh"><span class="ic">✍️</span><b>Người nhận hàng</b></div>' +
      '<input class="vfi" id="sinn" placeholder="Tên người ký nhận bên khách" value="' + h(st.nguoiNhan) + '">' +
      '<div class="vfm" style="margin-top:8px">Ghi tên để sau này còn đối chiếu khi có tranh chấp.</div></div>' +
      '<div class="vf"><div class="vfh"><span class="ic">📝</span><b>Ghi chú</b></div>' +
      '<input class="vfi" id="sigc" placeholder="Ví dụ: giao đợt 1 của hợp đồng tháng 9" value="' + h(st.ghiChu) + '"></div>' +
      xktNutChinh('siluu', 'Lưu và ghi sổ phiếu giao', 'Phiếu ghi sổ ngay: hàng lên xe rồi thì chờ duyệt là sai tồn trong lúc chờ.') +
      '</div>';
  }

  var body = frame('Lập phiếu giao hàng', ve());

  function doiKho(k) {
    if (st.kho && k !== st.kho && st.gio.length) { st.gio = []; toast('Đổi kho nên phải chọn lại hàng.'); }
    st.kho = k;
    try { localStorage.setItem('vgbKhoXuat', st.kho); } catch (e) { }
    veLai();
  }

  function noi() {
    xktNoiSuKien(body, st.gio, { khoaTon: 1 });
    body.querySelector('#sinn').oninput = function () { st.nguoiNhan = this.value; };
    body.querySelector('#sigc').oninput = function () { st.ghiChu = this.value; };
    var kho = xktKhoHtml('sikho', b.kho, st.kho);
    if (!kho.chip) {
      body.querySelector('#sikho').onclick = function () {
        xktSheetTim('Chọn kho xuất', kho.items.map(function (k) { return { value: k.k, label: k.ten, phu: k.k, icon: '🏬' }; }), st.kho, function (it) { doiKho(it.value); });
      };
    }
    body.querySelector('#sikhach').onclick = function () {
      xktSheetTimKhach('Tìm khách hàng', st.khach, function (x) {
        st.khach = x.name; st.tenKhach = x.customer_name || x.name; veLai();
      });
    };
    body.querySelector('#sithem').onclick = function () {
      if (!st.kho) { toast('Chọn kho xuất trước đã.'); xktBaoThieu(body, [['sikho', 1]]); return; }
      var kho2 = st.kho;
      XK.gio = st.gio.slice();
      st.dangChon = true;
      go(function () { scrXkChonHang(kho2, null); });
    };
    body.querySelector('#siluu').onclick = luu;
  }

  function veLai() {
    var vb = body.querySelector('.vxf'); if (vb) vb.outerHTML = ve();
    noi();
  }

  body.onclick = function (e) {
    var t = e.target.closest('[data-sikho]');
    if (t) doiKho(t.getAttribute('data-sikho'));
  };

  async function luu() {
    if (xktBaoThieu(body, [['sikhach', !st.khach], ['sikho', !st.kho], ['sigio', !st.gio.length]])) {
      toast(!st.khach ? 'Chưa chọn khách hàng.' : (!st.kho ? 'Chưa chọn kho xuất.' : 'Chưa có món nào.'));
      return;
    }
    var qua = st.gio.filter(function (d) { return d.ton != null && Number(d.sl) > Number(d.ton) + 1e-9; });
    if (qua.length) { toast('Có ' + qua.length + ' món vượt tồn, sửa số lượng trước.'); return; }
    if (st.gio.some(function (d) { return !(Number(d.sl) > 0); })) { toast('Có món số lượng 0, bỏ món đó hoặc gõ số.'); return; }
    if (!await xacNhan('Giao ' + st.gio.length + ' món cho ' + st.tenKhach + '?\n\nPhiếu ghi sổ ngay, tồn kho trừ thật và ghi giá vốn.', 'Ghi sổ phiếu giao', 'Ghi sổ')) return;
    this.disabled = true;
    try {
      var r = await api('vagabond.xuat_ban.luu', {
        khach: st.khach, kho: st.kho, nguoi_nhan: st.nguoiNhan, ghi_chu: st.ghiChu,
        dong: JSON.stringify(st.gio.map(function (d) { return { ma: d.ma, sl: d.sl }; }))
      });
      st.gio = []; st.ghiChu = '';
      toast('Đã ghi sổ phiếu giao ' + r.name);
      go(function () { scrXkSiView(r.name); }, true);
    } catch (e) {
      this.disabled = false;
      baoTin(errMsg(e) || 'Không ghi sổ được phiếu giao.');
    }
  }

  noi();
}

async function scrXkSiView(name) {
  xktCss();
  frame('Phiếu giao hàng', '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api('vagabond.xuat_ban.chi_tiet', { name: name }); }
  catch (e) { return frame('Phiếu giao hàng', '<div class="emp"><div class="e1">⚠️</div><div class="e2">' + h(errMsg(e) || 'Không mở được phiếu này. Lùi lại rồi thử lại.') + '</div></div>'); }
  frame('Phiếu giao hàng',
    '<div class="vxf">' +
    xktDauPhieu(d, (d.ten_khach || d.khach) + (d.tong_tien ? ' · ' + vxSo(d.tong_tien) + ' đ' : '')) +
    '<div class="vf">' +
    '<div class="vfh"><span class="ic">🏬</span><b>Kho xuất</b></div><div style="font-size:15px;font-weight:600;padding:2px 0 8px">' + h(d.kho || '') + '</div>' +
    (d.nguoi_nhan ? '<div class="vfh"><span class="ic">✍️</span><b>Người nhận</b></div><div style="font-size:15px;font-weight:600;padding:2px 0 8px">' + h(d.nguoi_nhan) + '</div>' : '') +
    (d.hop_dong ? '<div class="vfh"><span class="ic">📑</span><b>Hợp đồng</b></div><div style="font-size:15px;font-weight:600;padding:2px 0 8px">' + h(d.hop_dong) + '</div>' : '') +
    (d.ghi_chu ? '<div class="vfh"><span class="ic">📝</span><b>Ghi chú</b></div><div style="font-size:14px;padding:2px 0 8px">' + h(d.ghi_chu) + '</div>' : '') +
    '</div>' +
    '<div class="vxl">Hàng đã giao (' + d.dong.length + ' món)</div>' + xktDongXem(d.dong) +
    (d.tong_tien ? '<div style="text-align:right;font-weight:800;margin-top:4px">Giá trị: ' + vxSo(d.tong_tien) + ' đ</div>' : '') +
    xktVet(d) + '</div>');
}

/* ==================================================================
   4. XAC NHAN NHAN HANG DIEU CHUYEN (anh Viet chot phuong an A 02/09/2026)
   ==================================================================

   MAN NAY KHONG DUNG TOI SO KHO. Day la cho de hieu nham nhat, nen noi ro
   ngay tren man hinh chu khong chi trong ma nguon.

   Bam "nhan 8 tren 10" KHONG lam ton kho bep giam di 2. So kho van ghi day
   du 10 nhu phieu dieu chuyen da ghi. Man nay ghi lai MOT LOI KHAI: nguoi
   nhan noi rang ho chi thay 8. Lech do co the do kho xuat soan thieu, mat
   tren duong di, hoac nguoi nhan dem sot - ba nguyen nhan ghi vao ba cho
   khac nhau trong so ke toan, ma may khong biet la cai nao.

   Nen may chi ghi lai roi treo thanh viec cho thu kho doi chieu. Xem doan
   dai o dau vagabond/nhan_dieu_chuyen.py. */

var NDC = { phieu: '', dong: [], ghiChu: '' };

async function scrNhanDcXacNhan(phieu) {
  vgbCss();
  frame('Xác nhận nhận hàng', '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api('vagabond.nhan_dieu_chuyen.dong_de_nhan', { phieu: phieu }); }
  catch (e) {
    return frame('Xác nhận nhận hàng',
      '<div class="emp"><div class="e1">⚠️</div><div>' +
      h(errMsg(e) || 'Không mở được phiếu') + '</div></div>');
  }
  if (d.da_xac_nhan) {
    return frame('Xác nhận nhận hàng',
      '<div class="vxf"><div class="vxr"><div class="t"><b>' + h(d.phieu) + '</b>' +
      '<i>' + h(d.kho_xuat) + ' → ' + h(d.kho_nhan) + '</i></div>' +
      '<span class="vxtag d">' + h(d.da_xac_nhan) + '</span></div>' +
      '<div style="font-size:12.5px;color:#98a2b3;line-height:1.7;margin-top:12px">' +
      'Phiếu này đã được ' + h(d.nhan_boi || 'người khác') + ' xác nhận' +
      (d.nhan_luc ? ' lúc ' + h(d.nhan_luc) : '') + '. Khai sai thì báo thủ kho, ' +
      'đừng xác nhận đè lên.' +
      (d.nhan_ghi_chu ? '<br><br>Ghi chú: ' + h(d.nhan_ghi_chu) : '') + '</div></div>');
  }

  NDC.phieu = d.phieu;
  NDC.dong = (d.dong || []).map(function (x) { return { ma: x.ma, ten: x.ten, dvt: x.dvt, giao: x.giao, nhan: x.giao }; });
  NDC.ghiChu = '';

  function rowsHtml() {
    var s = '';
    for (var i = 0; i < NDC.dong.length; i++) {
      var x = NDC.dong[i];
      var lech = Number(x.giao) - Number(x.nhan);
      s += '<div class="vxr"><div class="t"><b>' + h(x.ten || x.ma) + '</b>' +
        '<i>' + h(x.ma) + ' · kho giao ' + vxSo(x.giao) + ' ' + h(x.dvt || '') +
        (Math.abs(lech) > 0.0001
          ? ' · <b style="color:' + (lech > 0 ? '#b91c1c' : '#b45309') + '">' +
            (lech > 0 ? 'thiếu ' : 'thừa ') + vxSo(Math.abs(lech)) + '</b>'
          : '') + '</i></div>' +
        '<input class="vxq" type="number" inputmode="decimal" min="0" step="any" ' +
        'value="' + x.nhan + '" data-nsl="' + i + '"></div>';
    }
    return s;
  }

  var body = frame('Xác nhận nhận hàng',
    '<div class="vxf">' +
    '<div class="vxr"><div class="t"><b>' + h(d.phieu) + '</b>' +
    '<i>' + h(d.ngay) + ' · ' + h(d.kho_xuat) + ' → ' + h(d.kho_nhan) + '</i></div></div>' +

    /* Cau nay la phan quan trong nhat cua ca man. Bo di la nguoi nhan tuong
       bam vao day thi ton kho tu nan lai, va se khong bao ai nua. */
    '<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;' +
    'padding:11px 13px;margin:12px 0;font-size:12.5px;color:#1e40af;line-height:1.6">' +
    'ℹ️ Màn này <b>không sửa tồn kho</b>. Nó ghi lại số bạn đếm được thật, để ' +
    'thủ kho đối chiếu xem hàng thiếu đi đâu. Sổ kho vẫn giữ nguyên số kho giao.</div>' +

    '<div class="vxl">Số bạn đếm được (máy điền sẵn theo số kho giao)</div>' +
    '<div id="ndcDong">' + rowsHtml() + '</div>' +

    '<div class="vf" style="margin-top:12px">' +
    '<div class="vfh"><span class="ic">📝</span><b>Ghi chú</b></div>' +
    '<input class="vfi" id="ndcGc" placeholder="Ví dụ: thùng bị rách một góc khi nhận">' +
    '</div>' +

    '<button class="vxb" id="ndcGui">Xác nhận đã nhận</button>' +
    '<div style="font-size:12px;color:#98a2b3;text-align:center;margin-top:10px">' +
    'Đúng đủ thì bấm luôn, không phải sửa gì. Chỉ sửa dòng nào thực sự lệch.</div></div>');

  function noi() {
    var qs = body.querySelectorAll('[data-nsl]');
    for (var i = 0; i < qs.length; i++) {
      qs[i].onchange = function () {
        var k = +this.dataset.nsl;
        var v = Number(this.value || 0);
        if (v < 0) { v = 0; this.value = 0; }
        NDC.dong[k].nhan = v;
        var o = body.querySelector('#ndcDong');
        if (o) { o.innerHTML = rowsHtml(); noi(); }
      };
    }
  }
  noi();

  body.querySelector('#ndcGc').onchange = function () { NDC.ghiChu = this.value; };

  body.querySelector('#ndcGui').onclick = async function () {
    var lech = NDC.dong.filter(function (x) {
      return Math.abs(Number(x.giao) - Number(x.nhan)) > 0.0001;
    });
    var cau = lech.length
      ? 'Bạn khai NHẬN THIẾU ở ' + lech.length + ' món.\n\nPhần thiếu sẽ treo thành ' +
        'việc cần làm cho thủ kho đối chiếu. Tồn kho không đổi.'
      : 'Bạn khai ĐÃ NHẬN ĐỦ toàn bộ phiếu này.';
    if (!await xacNhan(cau, 'Xác nhận nhận hàng', 'Xác nhận')) return;
    this.disabled = true;
    try {
      var r = await api('vagabond.nhan_dieu_chuyen.xac_nhan', {
        phieu: NDC.phieu, ghi_chu: NDC.ghiChu,
        dong: JSON.stringify(NDC.dong.map(function (x) { return { ma: x.ma, nhan: x.nhan }; }))
      });
      toast(r.trang_thai + (r.cau_lech ? ': ' + r.cau_lech : ''), 5000);
      go(scrHangVeKho, true);
    } catch (e) {
      this.disabled = false;
      baoTin(errMsg(e) || 'Không xác nhận được.');
    }
  };
}

/* ---------- 49. Tru kho tung mon va tru bu (v550, anh Viet chot 01/10/2026) ----------

   Hoa don ban luc kho chua co hang (vi du banh dieu chuyen toi sau gio ban)
   van ghi so doanh thu, khong bao gio chan ban. May tru ngay nhung mon dang
   co, mon nao chua co thi tru bu khi hang ve, bang mot Phieu xuat dung (PXD-)
   gan voi hoa don. Xem dau tep vagabond/tru_kho_bu.py.

   Mot nguon cho chip: may chu tinh khoa `tt_kho`, man hinh chi tra bang mau
   va chu o day. Moi man (Tinh tien quay, Doanh thu Sales, Hoa don ban ra,
   Hoa don chua tru kho, chi tiet hoa don) goi cung ham, nen cung mot trang
   thai khong bao gio hien hai cach khac nhau.

   Hai ho chip, co y dat ten khac han nhau de khong nham (anh Viet dan
   "day du chip trang thai, chip loc cho khong nham lan"):
     - DA/CHUA TRU: viec da xay ra tren so kho cua hoa don.
     - KHO ...: tinh trang ton HIEN TAI cua phan con thieu, tuc la bam
       Tru bu luc nay thi duoc toi dau. Chi co tren man Hoa don chua tru kho. */

var TT_KHO_CHIP = {
  da_tru: ['#dcfce7', '#166534', '📦 Đã trừ kho'],
  chua_tru: ['#fee2e2', '#991b1b', '📦 Chưa trừ kho'],
  mot_phan: ['#ffedd5', '#9a3412', '📦 Đã trừ một phần'],
  da_tru_bu: ['#ccfbf1', '#115e59', '🔁 Đã trừ bù']
};
var KHO_NAY_CHIP = {
  kho_du: ['#dcfce7', '#166534', '✅ Kho đủ để trừ bù'],
  kho_mot_phan: ['#fef3c7', '#92400e', '🟠 Kho đủ một phần'],
  kho_het: ['#f3f4f6', '#374151', '⛔ Kho chưa có hàng']
};
var NHAN_MON = {
  da_tru: ['#166534', 'Đã trừ'],
  du: ['#166534', 'Đủ để trừ'],
  mot_phan: ['#92400e', 'Trừ được một phần'],
  het: ['#991b1b', 'Kho chưa có']
};

/* [nen, chu, noi dung] cua chip trang thai kho, hoac null khi khong co chip. */
function tkChip(r) {
  var m = TT_KHO_CHIP[(r && r.tt_kho) || ''];
  return m || null;
}
/* Con mon cho tru: gom ca to da tru mot phan. */
function tkConCho(r) { return !!r && (r.tt_kho === 'chua_tru' || r.tt_kho === 'mot_phan'); }

/* Hai chip loc dung chung cho man Tinh tien quay va Doanh thu Sales. */
function tkLoc() {
  return [
    { k: 'chua_tru_kho', nhan: '📦 Chưa trừ kho', loc: function (r) { return tkConCho(r); } },
    { k: 'da_tru_bu', nhan: '🔁 Đã trừ bù', loc: function (r) { return !!r && r.tt_kho === 'da_tru_bu'; } }
  ];
}

function tkSo(x) {
  var n = Number(x || 0);
  return Math.round(n * 1000) / 1000;
}

/* ---------- Man Hoa don chua tru kho ----------
   Dung thanh cong cu chung (15-khuon-danh-sach.js): chip chang, chip diem
   ban, chip ngay, o tim, Xuat Excel. May chu loc va dem chip (tru_kho_bu.
   ds_chua_tru_kho), man hinh chi ve. */
var tkDiem = '', tkLocChon = 'cho', tkKy = '', tkTu = '', tkDen = '', tkTim = '';

function tkThamSo() {
  return { diem: tkDiem, chang: tkLocChon, ky: tkKy, tu: tkTu, den: tkDen, tim: tkTim };
}

function tkTheChip(m) {
  return '<span style="display:inline-block;background:' + m[0] + ';color:' + m[1] +
    ';font-size:12px;font-weight:700;border-radius:999px;padding:3px 10px;margin:3px 5px 0 0;white-space:nowrap">' + m[2] + '</span>';
}

function tkBangMon(dong) {
  if (!dong || !dong.length) return '<div style="font-size:12.5px;color:#98a2b3">Hoá đơn không có món theo dõi tồn kho.</div>';
  return '<table style="width:100%;border-collapse:collapse;font-size:12.5px;margin-top:6px">' +
    '<tr style="color:#98a2b3;text-align:right"><th style="text-align:left;font-weight:600">Món</th>' +
    '<th style="font-weight:600">Bán</th><th style="font-weight:600">Đã trừ</th><th style="font-weight:600">Tồn kho</th><th></th></tr>' +
    dong.map(function (d) {
      var n = NHAN_MON[d.nhan] || ['#374151', ''];
      return '<tr style="border-top:1px solid #f2f4f7;text-align:right">' +
        '<td style="text-align:left;padding:5px 4px 5px 0">' + h(d.ten) + '<div style="color:#98a2b3;font-size:11px">' + h(d.ma) + '</div></td>' +
        '<td>' + tkSo(d.can) + '</td><td>' + tkSo(d.da_tru) + '</td><td>' + tkSo(d.ton) + ' ' + h(d.dvt || '') + '</td>' +
        '<td style="color:' + n[0] + ';font-weight:700;white-space:nowrap;padding-left:6px">' + n[1] + '</td></tr>';
    }).join('') + '</table>';
}

function tkThe(r, duocTru) {
  var c = [];
  var m = tkChip(r);
  if (m) c.push(tkTheChip(m));
  if (tkConCho(r) && KHO_NAY_CHIP[r.kho_nay]) c.push(tkTheChip(KHO_NAY_CHIP[r.kho_nay]));
  if (r.vgb_tru_bu === 'Gỡ tay' && tkConCho(r)) c.push(tkTheChip(['#ede9fe', '#5b21b6', '✋ Phiếu bù bị gỡ tay']));
  var nut = duocTru && tkConCho(r) && r.kho_nay !== 'kho_het'
    ? '<button class="btn" data-tkbu="' + h(r.name) + '" style="margin:8px 0 0;padding:8px 12px;font-size:13px">🔁 Trừ bù</button>' : '';
  return '<div class="card" style="padding:12px 14px">' +
    '<div style="display:flex;justify-content:space-between;gap:8px"><b style="font-size:14px">' + h(r.name) + '</b>' +
    '<span style="font-size:12px;color:#6b7280;white-space:nowrap">' + h(r.ten_diem || r.diem || '') + ' · ' +
    h(String(r.posting_date || '').split('-').reverse().join('/')) + ' ' + h(String(r.posting_time || '').slice(0, 5)) + '</span></div>' +
    '<div>' + c.join('') + '</div>' +
    (r.vgb_ly_do_chua_tru_kho ? '<div style="font-size:12px;color:#6b7280;margin-top:4px">' + h(r.vgb_ly_do_chua_tru_kho) + '</div>' : '') +
    tkBangMon(r.dong) +
    ((r.phieu || []).length ? '<div style="font-size:12px;color:#0f766e;margin-top:6px">Phiếu xuất dùng bù: ' + r.phieu.map(h).join(', ') + '</div>' : '') +
    nut + '</div>';
}

async function scrTruKho() {
  var tieuDe = 'Hoá đơn chưa trừ kho';
  frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc hoá đơn...</div></div>');
  var kq;
  try { kq = await api('vagabond.tru_kho_bu.ds_chua_tru_kho', tkThamSo()); }
  catch (e) { frame(tieuDe, '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>'); return; }
  var ds = kq.hd || [];
  var html = '<div class="card" style="padding:12px 14px;font-size:12.5px;color:#4b5563;line-height:1.55">' +
    'Hoá đơn bán lúc kho điểm bán chưa có hàng vẫn ghi sổ doanh thu. Máy trừ ngay món đang có, món còn thiếu tự trừ bù khi hàng nhập về kho điểm bán. ' +
    'Website đặt bánh không bị ảnh hưởng: số trên web đã trừ ngay lúc lưu hoá đơn.</div>';
  var cc = {
    ma: 'tk',
    chang: { ds: kq.chang || [], dem: kq.dem, chon: tkLocChon, tatCa: 'Tất cả' },
    ho: [{ k: 'diem', chon: tkDiem, tatCa: 'Cả các điểm', mau: '#0369a1',
      ds: (kq.diem || []).map(function (d) { return { k: d.ma, ten: d.ten }; }) }],
    ky: { chon: tkKy, tu: tkTu, den: tkDen },
    tim: { gt: tkTim, goiY: 'Tìm mã hoá đơn, khách, mã hay tên món...' },
    xuat: { man: 'tru_kho', loc: tkThamSo, so: ds.length }
  };
  html += dsCongCu(cc);
  if (kq.bi_cat) html += '<div class="card" style="padding:10px 12px;background:#fff7ed;border:1.5px solid #fed7aa;color:#9a3412;font-size:12.5px">' +
    'Máy chỉ đọc 500 hoá đơn mới nhất trong khoảng ngày này. Chọn khoảng ngày hẹp hơn để xem đủ.</div>';
  if (kq.duoc_tru && tkDiem && ds.some(function (r) { return tkConCho(r) && r.kho_nay !== 'kho_het'; })) {
    html += '<div class="card" style="padding:10px 12px"><button class="btn" id="tkBuDiem" style="margin:0;width:100%">🔁 Trừ bù cả điểm này</button></div>';
  }
  html += ds.length ? ds.map(function (r) { return tkThe(r, kq.duoc_tru); }).join('')
    : '<div class="card"><div class="emp" style="padding:26px"><div class="e1">✅</div><div>Không có hoá đơn nào ở nhóm này.</div></div></div>';
  var b = frame(tieuDe, html);
  dsCongCuNoi(b, cc, function (ho, k) {
    if (ho === 'chang') tkLocChon = k;
    else if (ho === 'diem') tkDiem = k;
    else if (ho === 'ky') tkKy = k;
    else if (ho === 'tu') tkTu = k;
    else if (ho === 'den') tkDen = k;
    else if (ho === 'tim') tkTim = k;
    go(scrTruKho, true);
  });
  b.onclick = function (e) {
    var t = e.target.closest('[data-tkbu]');
    if (t) return tkBam(t.getAttribute('data-tkbu'));
    if (e.target.closest('#tkBuDiem')) return tkBamDiem();
  };
}

async function tkBam(ten) {
  if (!await confirmSheet('Trừ bù kho', 'Trừ kho cho hoá đơn ' + ten + ' bằng tồn hiện có. Món nào kho còn thiếu thì để chờ hàng về.', 'Trừ bù')) return;
  busy(true);
  try {
    var r = await api('vagabond.tru_kho_bu.tru_bu_hd', { hoa_don: ten });
    busy(false);
    toast(tkCauKetQua(r), 4500);
  } catch (e) { busy(false); baoTin((e && e.message) || 'Chưa trừ bù được.'); }
  go(scrTruKho, true);
}

async function tkBamDiem() {
  if (!await confirmSheet('Trừ bù cả điểm', 'Trừ kho cho mọi hoá đơn đang chờ của điểm này bằng tồn hiện có, kể cả hoá đơn có phiếu bù bị gỡ tay.', 'Trừ bù')) return;
  busy(true);
  try {
    var r = await api('vagabond.tru_kho_bu.tru_bu_diem', { diem: tkDiem });
    busy(false);
    toast('Đã trừ đủ ' + (r.xong || 0) + ' hoá đơn, trừ một phần ' + (r.mot_phan || 0) +
      (r.loi ? ', ' + r.loi + ' hoá đơn lỗi (xem lý do trên thẻ)' : '') + '.', 5000);
  } catch (e) { busy(false); baoTin((e && e.message) || 'Chưa trừ bù được.'); }
  go(scrTruKho, true);
}

function tkCauKetQua(r) {
  r = r || {};
  if (r.bo_qua) return r.bo_qua;
  var con = Object.keys(r.con_thieu || {}).length;
  if (!(r.phieu || []).length) return con ? 'Kho chưa có hàng cho món còn thiếu, hoá đơn vẫn chờ.' : 'Hoá đơn đã trừ đủ.';
  return 'Đã lập ' + r.phieu.join(', ') + (con ? '. Còn ' + con + ' món chờ hàng về.' : '. Hoá đơn đã trừ đủ.');
}

/* ---------- Khoi Kho tren man chi tiet mot hoa don ----------
   Ve cho trong truoc, nap sau, giong the thanh vien: khong bat thu ngan
   ngoi nhin man trang cho mot luot hoi may chu. */
function tkKhoiChiTiet(d) {
  if (!d || d.docstatus !== 1 || !(d.vgb_tru_kho_ban || d.vgb_chua_tru_kho || d.vgb_tru_bu)) return '';
  return '<div class="card" id="tkKhoi" data-tkhd="' + h(d.name) + '" style="padding:12px 14px">' +
    '<div style="font-size:13px;color:#98a2b3">📦 Đang đọc trạng thái kho...</div></div>';
}
async function tkNapKhoi(goc) {
  var el = (goc || document).querySelector('#tkKhoi');
  if (!el) return;
  var ten = el.getAttribute('data-tkhd');
  var r;
  try { r = await api('vagabond.tru_kho_bu.tt_hoa_don', { hoa_don: ten }); }
  catch (e) { el.innerHTML = '<div style="font-size:12.5px;color:#98a2b3">Chưa đọc được trạng thái kho.</div>'; return; }
  var the = tkThe(r, r.duoc_tru);
  el.innerHTML = '<div style="font-weight:700;font-size:14px;margin-bottom:2px">Kho</div>' +
    the.replace(/^<div class="card" style="padding:12px 14px">/, '<div>');
  el.onclick = function (e) {
    var t = e.target.closest('[data-tkbu]');
    if (!t) return;
    e.stopPropagation();
    (async function () {
      if (!await confirmSheet('Trừ bù kho', 'Trừ kho cho hoá đơn ' + ten + ' bằng tồn hiện có.', 'Trừ bù')) return;
      busy(true);
      try { var k = await api('vagabond.tru_kho_bu.tru_bu_hd', { hoa_don: ten }); busy(false); toast(tkCauKetQua(k), 4500); }
      catch (er) { busy(false); baoTin((er && er.message) || 'Chưa trừ bù được.'); }
      tkNapKhoi(goc);
    })();
  };
}

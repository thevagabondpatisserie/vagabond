/* ---------------- Gọi món tại bàn qua QR (v638) ----------------

   Anh Việt duyệt 04/11/2026: khách quét QR dán trên bàn, gọi món trên trang
   đặt bánh (tab Tại quầy), quầy nhận trên màn Tính tiền. Hai phần ở đây:

   1. Dải chờ trên màn Tính tiền của một quầy: hỏi máy chủ mỗi 15 giây
      (goi_mon_ban.dem_cho), có đơn thì hiện "N đơn gọi món tại bàn đang chờ
      nhận" kèm tiếng chuông ngắn (tắt được, nhớ theo máy). Bấm mở danh sách
      thẻ; "Nhận đơn và in phiếu pha chế" gọi goi_mon_ban.nhan (máy chủ khoá
      đơn, thêm món vào phiếu tạm tính của bàn hoặc lập phiếu mới), rồi in
      phiếu bằng ĐÚNG posInPhieuMon của màn quầy và mở phiếu tạm tính của bàn.
      Thu tiền, chốt, ghi sổ đi luồng tạm tính có sẵn, không có nút mới.
   2. Màn "In QR tại bàn": chọn điểm có quầy, chọn khoảng bàn, in khổ A6 mỗi
      tờ một bàn. Quyền: quản lý cửa hàng, Giám đốc (máy chủ chặn thật,
      goi_mon_ban.QUYEN_IN_QR; danh sách dưới chỉ để ẩn ô menu, phải trùng). */
var QUYEN_GMB_QR = ['System Manager', 'Giám đốc', 'VGB - Quản lý cửa hàng'];
function coQuyenGmbQr() {
  return QUYEN_GMB_QR.some(function (v) { return hasRole(v); });
}

var GMB_NHIP = null, GMB_DIEM = '', GMB_DS = [], GMB_LY_DO = [], GMB_DA_THAY = {}, GMB_LUC = 0;
var GMB_HOI_MOI = 15000;
var GMB_KHOA_CHUONG = 'vgb_gmb_chuong';

function gmbChuongBat() {
  try { return localStorage.getItem(GMB_KHOA_CHUONG) !== '0'; } catch (e) { return true; }
}
function gmbDatChuong(bat) {
  try { localStorage.setItem(GMB_KHOA_CHUONG, bat ? '1' : '0'); } catch (e) { }
}
/* Chuông ngắn hai nốt bằng WebAudio, không cần tệp âm thanh. Trình duyệt chặn
   âm thanh khi chưa có cú chạm nào thì im lặng, dải chờ vẫn hiện. */
function gmbKeu() {
  try {
    var C = window.AudioContext || window.webkitAudioContext;
    if (!C) return;
    var ac = new C();
    [880, 1175].forEach(function (f, i) {
      var o = ac.createOscillator(), g = ac.createGain();
      o.frequency.value = f; o.connect(g); g.connect(ac.destination);
      var t0 = ac.currentTime + i * 0.18;
      g.gain.setValueAtTime(0.2, t0); g.gain.exponentialRampToValueAtTime(0.001, t0 + 0.16);
      o.start(t0); o.stop(t0 + 0.17);
    });
  } catch (e) { }
}

/* Chỗ trống trên màn Tính tiền; gmbVeDai đổ nội dung vào sau. */
function gmbKhoi() { return '<div id="gmbDai"></div>'; }

/* Gọi sau mỗi lần màn Tính tiền vẽ lại. Màn vẽ lại sau mỗi lần bấm món nên
   KHÔNG hỏi máy chủ lại mỗi lần: cùng quầy và nhịp còn chạy thì chỉ vẽ lại
   dải từ số đã có. */
function gmbBatDau(diem) {
  if (!diem) { gmbDung(); return; }
  if (diem === GMB_DIEM && GMB_NHIP && Date.now() - GMB_LUC < GMB_HOI_MOI) { gmbVeDai(); return; }
  gmbDung();
  GMB_DIEM = diem;
  GMB_NHIP = setInterval(gmbHoi, GMB_HOI_MOI);
  gmbHoi();
}
function gmbDung() {
  if (GMB_NHIP) clearInterval(GMB_NHIP);
  GMB_NHIP = null;
}

async function gmbHoi() {
  /* Rời màn Tính tiền thì tự tắt, khỏi gọi máy chủ vô ích. */
  if (!document.getElementById('gmbDai')) return gmbDung();
  var kq;
  try { kq = await api('vagabond.goi_mon_ban.dem_cho', { diem: GMB_DIEM }); } catch (e) { return; }
  GMB_LUC = Date.now();
  GMB_DS = (kq && kq.ds) || [];
  GMB_LY_DO = (kq && kq.ly_do) || [];
  var moi = GMB_DS.some(function (x) { return !GMB_DA_THAY[x.ma]; });
  GMB_DS.forEach(function (x) { GMB_DA_THAY[x.ma] = 1; });
  gmbVeDai();
  if (moi && gmbChuongBat()) gmbKeu();
}

function gmbVeDai() {
  var dai = document.getElementById('gmbDai');
  if (!dai) return;
  if (!GMB_DS.length) { dai.innerHTML = ''; return; }
  var ban = GMB_DS.map(function (x) { return 'Bàn ' + x.ban; });
  var phu = ban.slice(0, 4).join(', ') + (ban.length > 4 ? ' và ' + (ban.length - 4) + ' bàn nữa' : '');
  var bat = gmbChuongBat();
  dai.innerHTML = '<div class="card" style="padding:11px 13px;background:#fff7ed;border:1.5px solid #fdba74;display:flex;flex-direction:row;align-items:center;gap:10px">' +
    '<button data-gmbmo="1" style="flex:1;min-width:0;text-align:left;background:none;border:0;padding:4px 0;min-height:44px;cursor:pointer;color:#9a3412">' +
    '<div style="font-weight:800;font-size:15px">🔔 ' + GMB_DS.length + ' đơn gọi món tại bàn đang chờ nhận</div>' +
    '<div style="font-size:13px;margin-top:2px">' + h(phu) + ' · bấm để xem và nhận</div></button>' +
    '<button data-gmbchuong="1" aria-label="' + (bat ? 'Tắt chuông' : 'Bật chuông') + '" style="flex:none;min-width:44px;min-height:44px;border:1px solid #fdba74;background:#fff;border-radius:10px;font-size:13px;color:#9a3412;cursor:pointer">' +
    (bat ? '🔔 Tắt chuông' : '🔕 Bật chuông') + '</button></div>';
  dai.onclick = function (e) {
    if (e.target.closest('[data-gmbchuong]')) { gmbDatChuong(!gmbChuongBat()); gmbVeDai(); return; }
    if (e.target.closest('[data-gmbmo]')) gmbMoDs();
  };
}

function gmbCoNuoc(x) {
  return (x.mon || []).some(function (m) { return posLaNuoc({ item_code: m.ma, nhom: m.nhom }); });
}

function gmbThe(x) {
  var mon = (x.mon || []).map(function (m) {
    return '<div style="display:flex;gap:8px;align-items:center;padding:5px 0;border-bottom:1px solid #f1f3f5;font-size:14px">' +
      anhMon(m.anh) + '<b style="flex:none;min-width:28px">' + m.sl + 'x</b><div style="flex:1;min-width:0">' + h(m.ten) +
      ((m.tc || []).length ? '<div style="font-size:13px;color:#0f766e">⚙ ' + h(m.tc.join(', ')) + '</div>' : '') + '</div></div>';
  }).join('');
  return '<div class="card" data-gmbthe="' + h(x.ma) + '" style="padding:12px 13px;margin-bottom:10px">' +
    '<div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px">' +
    '<span style="font-size:20px;font-weight:800">Bàn ' + h(x.ban) + '</span>' +
    '<span style="background:#fef3c7;color:#92400e;border-radius:999px;padding:3px 10px;font-size:13px;font-weight:700;white-space:nowrap">⏳ chờ ' + x.phut + ' phút</span></div>' +
    '<div style="font-size:13.5px;color:#475467;margin:3px 0 6px">' + x.so_mon + ' món · tạm tính ' + money(x.tam_tinh) + ' đ' +
    (x.ten_goi ? ' · gọi tên: <b>' + h(x.ten_goi) + '</b>' : '') + '</div>' + mon +
    (x.ghi_chu ? '<div style="font-size:13.5px;margin-top:6px;background:#f8fafc;border-radius:8px;padding:7px 9px">📝 ' + h(x.ghi_chu) + '</div>' : '') +
    (x.gioi_thieu ? '<div style="font-size:13px;color:#475467;margin-top:5px">Người giới thiệu: ' + h(x.gioi_thieu) + '</div>' : '') +
    '<button class="btn" data-gmbnhan="' + h(x.ma) + '" style="margin-top:10px">Nhận đơn và in phiếu pha chế</button>' +
    '<button class="btn gh" data-gmbtuchoi="' + h(x.ma) + '" style="margin-top:8px">Từ chối</button></div>';
}

function gmbMoDs() {
  var cu = document.getElementById('gmbSheet');
  if (cu) cu.remove();
  var ov = document.createElement('div'); ov.className = 'sh'; ov.id = 'gmbSheet';
  function ve() {
    ov.innerHTML = '<div class="shb" style="padding:16px 14px calc(env(safe-area-inset-bottom,0px) + 16px);max-height:88vh;overflow:auto">' +
      '<div class="shh" style="padding:0 0 10px"><b>Gọi món tại bàn · ' + h((posQuay && (posQuay.ten_ngan || posQuay.ten)) || GMB_DIEM) + '</b><div class="x" data-gmbdong="1">&times;</div></div>' +
      (GMB_DS.length ? GMB_DS.map(gmbThe).join('')
        : '<div class="emp"><div class="e1">✅</div><div>Không còn đơn nào chờ. Đơn mới sẽ hiện ở dải trên màn Tính tiền.</div></div>') +
      '</div>';
  }
  ve();
  document.body.appendChild(ov);
  ov.onclick = async function (e) {
    if (e.target === ov || e.target.closest('[data-gmbdong]')) return ov.remove();
    var n = e.target.closest('[data-gmbnhan]');
    if (n) return gmbNhan(n.getAttribute('data-gmbnhan'), ov);
    var t = e.target.closest('[data-gmbtuchoi]');
    if (t) return gmbTuChoi(t.getAttribute('data-gmbtuchoi'), ov, ve);
  };
}

async function gmbNhan(ma, ov) {
  var x = GMB_DS.filter(function (d) { return d.ma === ma; })[0];
  if (!x) return toast('Đơn này vừa có người xử lý. Danh sách đã cập nhật.');
  /* Cửa sổ in phải mở NGAY trong cú chạm (27-in-ngam.js): mở trước, đợi máy
     chủ xong mới ghi phiếu vào. Đơn chỉ có bánh thì không in phiếu pha chế. */
  var w = gmbCoNuoc(x) ? inMoCuaSoNeuCan('phieu_mon') : 'khong';
  busy(true);
  var kq;
  try { kq = await api('vagabond.goi_mon_ban.nhan', { ma: ma }); }
  catch (e) {
    busy(false);
    if (w && w !== 'chan' && w !== 'khong' && w.close) w.close();
    toast((e && e.message) || 'Chưa nhận được đơn, thử lại.', 6000);
    GMB_LUC = 0; await gmbHoi();
    if (ov && ov.parentNode) gmbMoDs();
    return;
  }
  busy(false);
  GMB_DS = GMB_DS.filter(function (d) { return d.ma !== ma; });
  gmbVeDai();
  if (ov && ov.parentNode) ov.remove();
  if (w !== 'khong' && w !== 'chan') await posInPhieuMon(kq.phieu, w, true);
  else if (w === 'chan') toast('Chưa in được phiếu pha chế: trình duyệt chặn cửa sổ in. Mở phiếu tạm tính bàn ' + kq.ban + ' và bấm in phiếu món.', 6000);
  toast((kq.them_vao ? 'Đã thêm món vào phiếu tạm tính bàn ' : 'Đã lập phiếu tạm tính bàn ') + kq.ban + ' (' + (kq.bill || '') + ').', 4000);
  go(function () { scrPosBill(kq.hoa_don); });
}

function gmbTuChoi(ma, ov, veLai) {
  var x = GMB_DS.filter(function (d) { return d.ma === ma; })[0];
  if (!x) return toast('Đơn này vừa có người xử lý. Danh sách đã cập nhật.');
  var chon = '';
  var hop = document.createElement('div'); hop.className = 'sh';
  function ve() {
    hop.innerHTML = '<div class="shb" style="padding:18px 16px calc(env(safe-area-inset-bottom,0px) + 16px)">' +
      '<div style="font-size:17.5px;font-weight:700;margin-bottom:6px">Từ chối đơn bàn ' + h(x.ban) + '</div>' +
      '<div style="font-size:13.5px;color:#5a6070;margin-bottom:10px">Khách thấy lý do này trên điện thoại. Không lập phiếu nào.</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px">' +
      (GMB_LY_DO.length ? GMB_LY_DO : ['Hết món', 'Quầy quá đông', 'Khác']).map(function (l) {
        return posChipNut('data-gmblydo="' + h(l) + '"', h(l), chon === l, false, '#b91c1c');
      }).join('') + '</div>' +
      '<button class="btn dg" data-gmbtc="1"' + (chon ? '' : ' disabled style="opacity:.5"') + '>Từ chối đơn</button>' +
      '<button class="btn gh" data-gmbhuy="1" style="margin-top:9px">Quay lại</button></div>';
  }
  ve();
  document.body.appendChild(hop);
  hop.onclick = async function (e) {
    if (e.target === hop || e.target.closest('[data-gmbhuy]')) return hop.remove();
    var l = e.target.closest('[data-gmblydo]');
    if (l) { chon = l.getAttribute('data-gmblydo'); return ve(); }
    if (!e.target.closest('[data-gmbtc]')) return;
    if (!chon) return toast('Chọn một lý do để khách biết.');
    busy(true);
    try { await api('vagabond.goi_mon_ban.tu_choi', { ma: ma, ly_do: chon }); }
    catch (er) { busy(false); return toast((er && er.message) || 'Chưa từ chối được, thử lại.', 5000); }
    busy(false);
    hop.remove();
    GMB_DS = GMB_DS.filter(function (d) { return d.ma !== ma; });
    gmbVeDai();
    toast('Đã từ chối đơn bàn ' + x.ban + '.');
    if (ov && ov.parentNode && veLai) veLai();
  };
}

/* ---------------- Màn In QR tại bàn ---------------- */
var gqDiem = '', gqTu = 1, gqDen = 20, gqTo = null;

async function scrGmbInQr() {
  frame('In QR tại bàn', '<div class="emp"><div class="e1">⏳</div><div>Đang tải các điểm bán...</div></div>');
  var ds;
  try { ds = await api('vagabond.goi_mon_ban.diem_in_qr', {}); }
  catch (e) { frame('In QR tại bàn', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Chưa tải được điểm bán. Kéo xuống để thử lại.') + '</div></div>'); return; }
  ds = ds || [];
  if (!ds.length) { frame('In QR tại bàn', '<div class="emp"><div class="e1">🏬</div><div>Chưa có điểm bán nào có quầy. Bật quầy ở Cài đặt, Điểm bán.</div></div>'); return; }
  if (!ds.some(function (d) { return d.ma === gqDiem; })) { gqDiem = ds[0].ma; gqTo = null; }
  gmbVeInQr(ds);
}

function gmbVeInQr(ds) {
  var d = ds.filter(function (x) { return x.ma === gqDiem; })[0] || ds[0];
  var html = '<div class="card" style="padding:12px 14px">' +
    '<div style="font-size:13.5px;color:#475467;line-height:1.5">Mỗi bàn một mã QR. Khách quét là gọi món của đúng quầy, đúng bàn; quầy nhận trên màn Tính tiền. Mã không có hạn, in một lần dán lâu dài.</div></div>' +
    '<div class="sec">Điểm bán</div><div style="display:flex;gap:8px;overflow-x:auto;padding:0 2px 6px">' +
    ds.map(function (x) { return posChipNut('data-gqdiem="' + h(x.ma) + '"', h(x.ten), x.ma === gqDiem); }).join('') + '</div>' +
    '<div style="font-size:12.5px;color:#6b7280;margin:0 4px 8px">' + h(d.phu || '') + '</div>' +
    '<div class="sec">Bàn cần in</div><div class="card" style="padding:12px 14px;display:flex;flex-direction:row;gap:10px;align-items:flex-end">' +
    '<label style="flex:1;font-size:13px;color:#475467">Từ bàn<input class="tin" id="gqTu" type="number" inputmode="numeric" min="1" max="99" value="' + gqTu + '" style="margin-top:4px;min-height:44px"></label>' +
    '<label style="flex:1;font-size:13px;color:#475467">Đến bàn<input class="tin" id="gqDen" type="number" inputmode="numeric" min="1" max="99" value="' + gqDen + '" style="margin-top:4px;min-height:44px"></label></div>' +
    '<div style="font-size:12.5px;color:#6b7280;margin:0 4px 10px">In một bàn thì gõ cùng một số ở hai ô. Mỗi lần in tối đa 60 tờ.</div>';
  if (gqTo && gqTo.diem === gqDiem) {
    html += '<div class="sec">Xem trước · ' + gqTo.to.length + ' tờ A6</div><div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:10px">' +
      gqTo.to.map(function (t) {
        return '<div class="card" data-gqto="' + t.ban + '" style="padding:10px;text-align:center;margin:0"><img src="' + t.anh + '" alt="" style="width:100%;max-width:140px">' +
          '<div style="font-weight:800;font-size:14px;margin-top:4px">Bàn ' + t.ban + ' · ' + h(t.ten_diem) + '</div>' +
          '<div style="font-size:12.5px;color:#6b7280">Quét để gọi món tại bàn</div></div>';
      }).join('') + '</div>';
  }
  var coTo = gqTo && gqTo.diem === gqDiem && gqTo.to.length;
  var b = frame('In QR tại bàn', html, { footer: coTo
    ? '<button class="btn" id="gqIn">In ' + gqTo.to.length + ' tờ A6</button>'
    : '<button class="btn" id="gqTao">Tạo mã QR</button>' });
  b.addEventListener('click', function (e) {
    var c = e.target.closest('[data-gqdiem]');
    if (c) { gqDiem = c.getAttribute('data-gqdiem'); gqTo = null; return gmbVeInQr(ds); }
  });
  ['gqTu', 'gqDen'].forEach(function (id) {
    var o = document.getElementById(id);
    if (o) o.addEventListener('input', function () {
      if (id === 'gqTu') gqTu = parseInt(o.value, 10) || ''; else gqDen = parseInt(o.value, 10) || '';
      if (gqTo) { gqTo = null; gmbVeInQr(ds); }
    });
  });
  var tao = document.getElementById('gqTao');
  if (tao) tao.onclick = async function () {
    var tu = parseInt(gqTu, 10), den = parseInt(gqDen, 10);
    if (!(tu >= 1 && tu <= 99) || !(den >= 1 && den <= 99)) return toast('Số bàn từ 1 tới 99.');
    busy(true);
    try { gqTo = await api('vagabond.goi_mon_ban.to_qr', { diem: gqDiem, tu: tu, den: den }); }
    catch (er) { busy(false); return toast((er && er.message) || 'Chưa tạo được mã QR, thử lại.', 5000); }
    busy(false);
    gmbVeInQr(ds);
  };
  var nutIn = document.getElementById('gqIn');
  if (nutIn) nutIn.onclick = function () { gmbInA6(gqTo); };
}

/* Tờ in A6 dọc, mỗi bàn một trang. Mở cửa sổ ngay trong cú chạm. */
function gmbToA6Html(kq) {
  var trang = (kq.to || []).map(function (t) {
    return '<section class="to"><div class="ten">THE VAGABOND PÂTISSERIE</div>' +
      '<img src="' + t.anh + '" alt="">' +
      '<div class="ban">Bàn ' + t.ban + ' · ' + h(t.ten_diem) + '</div>' +
      '<div class="goi">Quét để gọi món tại bàn</div></section>';
  }).join('');
  return '<html><head><meta charset="utf-8"><title>QR tại bàn ' + h(kq.ten || '') + '</title><style>' +
    '@page{size:A6 portrait;margin:0}*{margin:0;padding:0;box-sizing:border-box}' +
    'body{font-family:Arial,sans-serif;color:#000}' +
    '.to{width:105mm;height:148mm;padding:10mm 8mm;display:flex;flex-direction:column;align-items:center;justify-content:center;page-break-after:always;text-align:center}' +
    '.ten{font-size:11px;letter-spacing:.12em;margin-bottom:6mm}' +
    '.to img{width:72mm;height:72mm}' +
    '.ban{font-size:22px;font-weight:bold;margin-top:6mm}' +
    '.goi{font-size:15px;margin-top:3mm}' +
    '</style></head><body>' + trang + '</body></html>';
}
function gmbInA6(kq) {
  if (!kq || !(kq.to || []).length) return toast('Bấm Tạo mã QR trước đã.');
  var w = window.open('', '_blank');
  if (!w) return toast('Trình duyệt chặn cửa sổ in. Cho phép popup rồi bấm lại.', 4000);
  w.document.write(inThemLenhIn(gmbToA6Html(kq), 700));
  w.document.close();
}

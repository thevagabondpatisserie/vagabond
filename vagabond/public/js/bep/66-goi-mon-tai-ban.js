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
      goi_mon_ban.QUYEN_IN_QR; danh sách dưới chỉ để ẩn ô menu, phải trùng).
   3. v639 (anh Việt duyệt mẫu 05/11/2026): khách bấm chuông Gọi nhân viên trên
      trang bàn thì dem_cho trả thêm `tro_giup`; dải chờ ghi "M bàn cần trợ
      giúp", thẻ đỏ đứng trước các đơn, nút "Đã tới bàn" gọi
      goi_mon_ban.xong_tro_giup; khách xin tính tiền thì có nút mở bill của bàn. */
var QUYEN_GMB_QR = ['System Manager', 'Giám đốc', 'VGB - Quản lý cửa hàng'];
function coQuyenGmbQr() {
  return QUYEN_GMB_QR.some(function (v) { return hasRole(v); });
}

var GMB_NHIP = null, GMB_DIEM = '', GMB_DS = [], GMB_TG = [], GMB_LY_DO = [], GMB_DA_THAY = {}, GMB_LUC = 0;
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
  GMB_TG = (kq && kq.tro_giup) || [];
  GMB_LY_DO = (kq && kq.ly_do) || [];
  var moi = GMB_DS.concat(GMB_TG).some(function (x) { return !GMB_DA_THAY[x.ma]; });
  GMB_DS.concat(GMB_TG).forEach(function (x) { GMB_DA_THAY[x.ma] = 1; });
  gmbVeDai();
  if (moi && gmbChuongBat()) gmbKeu();
}

function gmbVeDai() {
  var dai = document.getElementById('gmbDai');
  if (!dai) return;
  if (!GMB_DS.length && !GMB_TG.length) { dai.innerHTML = ''; return; }
  var ban = GMB_DS.map(function (x) { return 'Bàn ' + x.ban; });
  var phu = ban.slice(0, 4).join(', ') + (ban.length > 4 ? ' và ' + (ban.length - 4) + ' bàn nữa' : '');
  var tg = GMB_TG.map(function (x) { return 'Bàn ' + x.ban + ' ' + gmbLyDoNgan(x.ly_do); });
  var dong1 = (GMB_DS.length ? GMB_DS.length + ' đơn gọi món tại bàn đang chờ nhận' : '') +
    (GMB_DS.length && GMB_TG.length ? ' · ' : '') + (GMB_TG.length ? GMB_TG.length + ' bàn cần trợ giúp' : '');
  var dong2 = (GMB_DS.length ? phu : '') + (GMB_DS.length && GMB_TG.length ? ' · ' : '') + tg.slice(0, 3).join(', ') +
    (tg.length > 3 ? ' và ' + (tg.length - 3) + ' bàn nữa' : '');
  var bat = gmbChuongBat();
  var mau = GMB_TG.length ? 'background:#fef2f2;border:1.5px solid #fca5a5' : 'background:#fff7ed;border:1.5px solid #fdba74';
  var chu = GMB_TG.length ? '#991b1b' : '#9a3412';
  dai.innerHTML = '<div class="card" style="padding:11px 13px;' + mau + ';display:flex;flex-direction:row;align-items:center;gap:10px">' +
    '<button data-gmbmo="1" style="flex:1;min-width:0;text-align:left;background:none;border:0;padding:4px 0;min-height:44px;cursor:pointer;color:' + chu + '">' +
    '<div style="font-weight:800;font-size:15px">🔔 ' + h(dong1) + '</div>' +
    '<div style="font-size:13px;margin-top:2px">' + h(dong2) + ' · bấm để xem</div></button>' +
    '<button data-gmbchuong="1" aria-label="' + (bat ? 'Tắt chuông' : 'Bật chuông') + '" style="flex:none;min-width:44px;min-height:44px;border:1px solid #fdba74;background:#fff;border-radius:10px;font-size:13px;color:#9a3412;cursor:pointer">' +
    (bat ? '🔔 Tắt chuông' : '🔕 Bật chuông') + '</button></div>';
  dai.onclick = function (e) {
    if (e.target.closest('[data-gmbchuong]')) { gmbDatChuong(!gmbChuongBat()); gmbVeDai(); return; }
    if (e.target.closest('[data-gmbmo]')) gmbMoDs();
  };
}

/* Lý do khách bấm chuông, rút gọn cho dải. */
function gmbLyDoNgan(ly) {
  return { 'Gọi nhân viên tới bàn': 'gọi nhân viên', 'Xin tính tiền': 'xin tính tiền', 'Xin thêm nước lọc, đá': 'xin nước, đá',
    'Xin thêm dao, nĩa, khăn giấy': 'xin dao nĩa', 'Việc khác': 'cần hỗ trợ' }[ly] || 'cần hỗ trợ';
}

/* Thẻ "bàn cần trợ giúp" (v639): lý do, chữ khách nhắn, bill tạm tính nếu xin tính tiền. */
function gmbTheTroGiup(x) {
  return '<div class="card" data-gmbtg="' + h(x.ma) + '" style="padding:12px 13px;margin-bottom:10px;border:1.5px solid #fca5a5;background:#fff">' +
    '<div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px">' +
    '<span style="background:#fee2e2;color:#991b1b;border-radius:999px;padding:3px 10px;font-size:12.5px;font-weight:800;white-space:nowrap">BÀN ' + h(x.ban) + ' CẦN TRỢ GIÚP</span>' +
    '<span style="font-size:12.5px;color:#6b7280;white-space:nowrap">' + (x.phut ? x.phut + ' phút trước' : 'vừa xong') + '</span></div>' +
    '<div style="font-size:15px;font-weight:700;margin:8px 0 2px">' + h(x.ly_do) + '</div>' +
    (x.chi_tiet ? '<div style="font-size:13.5px;background:#f8fafc;border-radius:8px;padding:7px 9px;margin-top:4px">💬 ' + h(x.chi_tiet) + '</div>' : '') +
    (x.bill ? '<div style="font-size:13.5px;color:#475467;margin-top:6px">Bill tạm tính ' + h(x.bill) + (x.tam_tinh ? ' · ' + money(x.tam_tinh) + ' đ' : '') + '</div>'
      : (x.ly_do === 'Xin tính tiền' ? '<div style="font-size:13.5px;color:#475467;margin-top:6px">Bàn này chưa có phiếu tạm tính hôm nay.</div>' : '')) +
    '<div style="display:flex;gap:8px;margin-top:10px">' +
    '<button class="btn" data-gmbxong="' + h(x.ma) + '" style="flex:1;margin-top:0;background:#1570ef">Đã tới bàn</button>' +
    (x.hoa_don ? '<button class="btn gh" data-gmbbill="' + h(x.hoa_don) + '" style="flex:1;margin-top:0">Mở bill bàn ' + h(x.ban) + '</button>' : '') +
    '</div></div>';
}

async function gmbXongTroGiup(ma, veLai) {
  busy(true);
  try { await api('vagabond.goi_mon_ban.xong_tro_giup', { ma: ma }); }
  catch (e) { busy(false); return toast((e && e.message) || 'Chưa ghi được, thử lại.', 5000); }
  busy(false);
  GMB_TG = GMB_TG.filter(function (d) { return d.ma !== ma; });
  gmbVeDai();
  toast('Đã ghi: nhân viên đã tới bàn.');
  if (veLai) veLai();
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
      GMB_TG.map(gmbTheTroGiup).join('') +
      (GMB_DS.length ? GMB_DS.map(gmbThe).join('')
        : (GMB_TG.length ? '' : '<div class="emp"><div class="e1">✅</div><div>Không còn đơn nào chờ. Đơn mới sẽ hiện ở dải trên màn Tính tiền.</div></div>')) +
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
    var x = e.target.closest('[data-gmbxong]');
    if (x) return gmbXongTroGiup(x.getAttribute('data-gmbxong'), ve);
    var b = e.target.closest('[data-gmbbill]');
    if (b) { ov.remove(); return go(function () { scrPosBill(b.getAttribute('data-gmbbill')); }); }
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

/* ---------------- Màn In QR tại bàn ----------------
   v647 (anh Việt 10/11/2026): bàn đặt tên theo khu (A1, B1, VIP1) và tờ in
   đúng branding (mẫu Illustrator anh gửi). Quản lý khai sơ đồ bàn một lần
   (khu + khoảng số, màn Tính tiền dùng chung), tích các bàn cần in, chọn
   kích thước standee; máy dàn các miếng lên trang A4 kèm dấu cắt.
   Anh chốt: mã đậm trên ô trắng (máy đọc nào cũng quét được), nhãn "BÀN A1". */
var gqDiem = '', gqTo = null, gqSoDo = null, gqChon = {}, gqDiaChi = null, gqSua = false;
var gqKt = '70x70', gqW = 70, gqH = 70;
var GQ_KT = [
  { k: '70x70', w: 70, h: 70, ten: 'Mica 7 x 7 cm', giai: 'Miếng mica vuông đang dùng. Bố cục vuông, không có dòng địa chỉ.' },
  { k: '105x148', w: 105, h: 148, ten: 'A6 10,5 x 14,8 cm', giai: 'Standee để bàn cỡ thường, đủ dòng địa chỉ dưới cùng.' },
  { k: '148x210', w: 148, h: 210, ten: 'A5 14,8 x 21 cm', giai: 'Standee lớn, đúng khổ file thiết kế gốc.' },
  { k: 'tu', w: 0, h: 0, ten: 'Tự nhập', giai: 'Gõ rộng và cao (mm) theo khung standee thật.' }
];
var GMB_MAU = { w: 419.528, h: 595.276, nen: '#78CCCA', vien: '#A0D9D7', dam: '#245f5c',
  o: { x: 92.006, y: 253.344, c: 235.49 }, qr: 0.86,
  nhan: { y: 536, co: 44 }, dc: { x: 291.5, y: 574, co: 8.6, toi_da: 112 },
  logo: { w: 116.916, h: 50.41 }, chu: { w: 340, h: 128 } };
var GMB_KHUON = { doc: 'doc', nen: 'nen', logo: 'logo', chu: 'chu' };
var GMB_KHUON_SVG = null, gmbKhuonNap = null;

function gmbEsc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

/* Kích thước hợp lệ của standee (mm). THUẦN. */
function gmbKtHopLe(w, h) {
  w = Number(w); h = Number(h);
  return w >= 40 && h >= 40 && w <= 200 && h <= 287;
}

/* Xếp standee w x h (mm) lên A4 dọc, lề 5 mm; thử cả xoay ngang. THUẦN. */
function gmbXepA4(w, h) {
  var LE = 5, RONG = 210 - 2 * LE, CAO = 297 - 2 * LE;
  w = Number(w); h = Number(h);
  if (!(w > 0 && h > 0)) return { n: 0, cot: 0, hang: 0, xoay: false };
  function dem(a, b) { var c = Math.floor(RONG / a), r = Math.floor(CAO / b); return { cot: c, hang: r, n: c * r }; }
  var d = dem(w, h), x = dem(h, w);
  return x.n > d.n ? { n: x.n, cot: x.cot, hang: x.hang, xoay: true } : { n: d.n, cot: d.cot, hang: d.hang, xoay: false };
}

/* Gần vuông (cao không quá 1,25 lần rộng) thì dùng bố cục vuông: khuôn dọc
   thu vào ô vuông làm mã QR chỉ còn khoảng 24 mm trên miếng 7 cm. THUẦN. */
function gmbKieu(w, h) { return Number(h) / Number(w) < 1.25 ? 'vuong' : 'doc'; }

/* Đường path các ô đậm của mã QR, vẽ trong khung vuông cạnh c tại (x, y). */
function gmbQrPath(link, x, y, c) {
  var q = qrcode(0, 'M'); q.addData(String(link), 'Byte'); q.make();
  var n = q.getModuleCount(), m = c / n, d = [];
  for (var r = 0; r < n; r++) for (var k = 0; k < n; k++) if (q.isDark(r, k)) {
    d.push('M' + (x + k * m).toFixed(3) + ' ' + (y + r * m).toFixed(3) + 'h' + m.toFixed(3) + 'v' + m.toFixed(3) + 'h-' + m.toFixed(3) + 'z');
  }
  return d.join('');
}

/* Ô trắng có viền và mã QR đậm bên trong (anh chốt "mã đậm trên ô trắng"). */
function gmbOQr(link, x, y, c) {
  var q = c * GMB_MAU.qr, le = (c - q) / 2;
  return '<rect x="' + x.toFixed(2) + '" y="' + y.toFixed(2) + '" width="' + c.toFixed(2) + '" height="' + c.toFixed(2) + '" fill="#fff" stroke="' + GMB_MAU.vien + '" stroke-width="1.5"/>' +
    '<path fill="' + GMB_MAU.dam + '" d="' + gmbQrPath(link, x + le, y + le, q) + '"/>';
}

function gmbNhanSvg(chu, x, y, co) {
  return '<text x="' + x.toFixed(2) + '" y="' + y.toFixed(2) + '" text-anchor="middle" fill="#fff" ' +
    'style="font-family:\'Vagabond Sans\';font-size:' + co + 'px;letter-spacing:.04em">' + gmbEsc(chu) + '</text>';
}

/* Một miếng standee: SVG rộng w, cao h (mm). t: {link, nhan}. Cần các khuôn
   đã nạp (gmbNapKhuon) trong cùng trang. */
function gmbStandeeSvg(t, w, h, diaChi) {
  var M = GMB_MAU, VW = M.w, nhan = String(t.nhan || ('BÀN ' + (t.ban || ''))).toUpperCase();
  var dau = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" style="width:' + w + 'mm;height:' + h + 'mm;display:block;background:' + M.nen + '" ';
  if (gmbKieu(w, h) === 'vuong') {
    var VH = VW * h / w;
    var lw = 80, lh = lw * M.logo.h / M.logo.w, ly = VH * 0.04;
    var cw = 170, ch = cw * M.chu.h / M.chu.w, cy = ly + lh + 6;
    var top = cy + ch + 10, c = Math.min(VW * 0.6, VH - top - 62);
    return dau + 'viewBox="0 0 ' + VW + ' ' + VH.toFixed(3) + '">' +
      '<svg x="0" y="0" width="' + VW + '" height="' + VH.toFixed(3) + '" viewBox="0 0 ' + M.w + ' ' + M.h + '" preserveAspectRatio="xMidYMid slice"><use href="#gmbNen" xlink:href="#gmbNen"/></svg>' +
      '<use href="#gmbLogo" xlink:href="#gmbLogo" x="' + ((VW - lw) / 2).toFixed(2) + '" y="' + ly.toFixed(2) + '" width="' + lw + '" height="' + lh.toFixed(2) + '"/>' +
      '<use href="#gmbChu" xlink:href="#gmbChu" x="' + ((VW - cw) / 2).toFixed(2) + '" y="' + cy.toFixed(2) + '" width="' + cw + '" height="' + ch.toFixed(2) + '"/>' +
      gmbOQr(t.link, (VW - c) / 2, top, c) +
      gmbNhanSvg(nhan, VW / 2, top + c + 42, 36) + '</svg>';
  }
  var o = M.o, dc = String(diaChi || ''), uoc = dc.length * M.dc.co * 0.5;
  return dau + 'viewBox="0 0 ' + VW + ' ' + M.h + '" preserveAspectRatio="xMidYMid meet">' +
    '<use href="#gmbDoc" xlink:href="#gmbDoc"/>' + gmbOQr(t.link, o.x, o.y, o.c) +
    gmbNhanSvg(nhan, VW / 2, M.nhan.y, M.nhan.co) +
    (dc ? '<text x="' + M.dc.x + '" y="' + M.dc.y + '" fill="#fff" style="font-family:Barlow;font-weight:500;font-size:' + M.dc.co + 'px"' +
      (uoc > M.dc.toi_da ? ' textLength="' + M.dc.toi_da + '" lengthAdjust="spacingAndGlyphs"' : '') + '>' + gmbEsc(dc) + '</text>' : '') +
    '</svg>';
}

/* Các trang A4 in: xếp standee, dấu cắt ở lề theo mỗi đường chia. */
function gmbTrangA4(ds, w, h, diaChi) {
  var x = gmbXepA4(w, h), moi = x.n, trang = [];
  if (!moi) return '';
  var cw = x.xoay ? h : w, ch = x.xoay ? w : h;
  var ox = (210 - x.cot * cw) / 2, oy = (297 - x.hang * ch) / 2;
  for (var i = 0; i < ds.length; i += moi) {
    var o = ds.slice(i, i + moi).map(function (t, j) {
      var col = j % x.cot, row = Math.floor(j / x.cot);
      var xoay = x.xoay ? 'transform:translate(' + cw + 'mm,0) rotate(90deg);transform-origin:0 0;' : '';
      return '<div style="position:absolute;left:' + (ox + col * cw) + 'mm;top:' + (oy + row * ch) + 'mm;width:' + cw + 'mm;height:' + ch + 'mm">' +
        '<div style="position:absolute;left:0;top:0;' + xoay + '">' + gmbStandeeSvg(t, w, h, diaChi) + '</div></div>';
    }).join('');
    var dau = '';
    for (var k = 0; k <= x.cot; k++) {
      var xx = ox + k * cw;
      dau += '<i style="left:' + xx + 'mm;top:0;width:0;height:' + (oy - 1) + 'mm;border-left:.2mm solid #000"></i>' +
        '<i style="left:' + xx + 'mm;top:' + (oy + x.hang * ch + 1) + 'mm;width:0;height:' + (oy - 1) + 'mm;border-left:.2mm solid #000"></i>';
    }
    for (var r = 0; r <= x.hang; r++) {
      var yy = oy + r * ch;
      dau += '<i style="top:' + yy + 'mm;left:0;height:0;width:' + (ox - 1) + 'mm;border-top:.2mm solid #000"></i>' +
        '<i style="top:' + yy + 'mm;left:' + (ox + x.cot * cw + 1) + 'mm;height:0;width:' + (ox - 1) + 'mm;border-top:.2mm solid #000"></i>';
    }
    trang.push('<section class="a4">' + o + dau + '</section>');
  }
  return trang.join('');
}

/* Bốn khuôn SVG của mẫu (public/images/qr-ban), gói thành symbol một lần. */
function gmbBocKhuon(id, svg) {
  var m = /viewBox="([^"]+)"/.exec(svg);
  var than = String(svg).replace(/^[\s\S]*?<svg\b[^>]*>/, '').replace(/<\/svg>\s*$/, '');
  return '<symbol id="' + id + '" viewBox="' + (m ? m[1] : '0 0 100 100') + '">' + than + '</symbol>';
}
function gmbNapKhuon() {
  if (gmbKhuonNap) return gmbKhuonNap;
  var ten = { gmbDoc: 'doc', gmbNen: 'nen', gmbLogo: 'logo', gmbChu: 'chu' };
  gmbKhuonNap = Promise.all([(typeof qrcode === 'function' && qrcode.stringToBytes) ? 1 : inNapJs(IN_VENDOR.qr)].concat(
    Object.keys(ten).map(function (id) {
      return fetch('/assets/vagabond/images/qr-ban/' + ten[id] + '.svg', { credentials: 'same-origin' })
        .then(function (r) { if (!r.ok) throw new Error('Không tải được mẫu in.'); return r.text(); })
        .then(function (t) { return gmbBocKhuon(id, t); });
    }))).then(function (ds) {
      GMB_KHUON_SVG = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="0" height="0" style="position:absolute" aria-hidden="true">' + ds.slice(1).join('') + '</svg>';
      if (!document.getElementById('gmbKhuonDom')) {
        var d = document.createElement('div'); d.id = 'gmbKhuonDom'; d.innerHTML = GMB_KHUON_SVG + '<style>' + gmbFontCss() + '</style>';
        document.body.appendChild(d);
      }
      return GMB_KHUON_SVG;
    }).catch(function (e) { gmbKhuonNap = null; throw e; });
  return gmbKhuonNap;
}
function gmbFontCss() {
  var g = location.origin + '/assets/vagabond/mau_in/';
  return '@font-face{font-family:"Vagabond Sans";src:url(' + g + 'VagabondSans-Regular.otf)}' +
    '@font-face{font-family:Barlow;font-weight:500;src:url(' + g + 'Barlow-Medium.ttf)}';
}

/* Tệp in: các trang A4, chờ phông chữ nạp xong mới gọi in. */
function gmbTepIn(kq, w, h, diaChi) {
  return '<html><head><meta charset="utf-8"><title>QR tại bàn ' + h_(kq.ten || '') + '</title><style>' + gmbFontCss() +
    '@page{size:A4 portrait;margin:0}*{margin:0;padding:0;box-sizing:border-box}' +
    '.a4{position:relative;width:210mm;height:297mm;page-break-after:always;overflow:hidden;background:#fff}' +
    '.a4 i{position:absolute;display:block}' +
    '</style></head><body>' + GMB_KHUON_SVG + gmbTrangA4(kq.to || [], w, h, diaChi) +
    '<' + 'script>window.onload=function(){var f=document.fonts&&document.fonts.ready;(f||Promise.resolve()).then(function(){setTimeout(function(){window.print()},400)})}<' + '/script>' +
    '</body></html>';
  function h_(s) { return gmbEsc(s); }
}

function gmbKtDangChon() {
  var p = GQ_KT.filter(function (x) { return x.k === gqKt; })[0] || GQ_KT[0];
  return p.k === 'tu' ? { w: Number(gqW), h: Number(gqH) } : { w: p.w, h: p.h };
}

/* Sơ đồ bàn: tên bàn của một dòng khai, cùng luật máy chủ (so_do_ban). THUẦN. */
function gmbChuanKhu(s) {
  var t = String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[đĐ]/g, 'D').toUpperCase().replace(/[\s\-_.]/g, '');
  return /^[A-Z]{0,4}$/.test(t) ? t : null;
}
function gmbMoTaDong(d) {
  var khu = gmbChuanKhu(d.khu), tu = parseInt(d.tu, 10), den = parseInt(d.den, 10);
  if (khu === null) return { loi: 'Tên khu chỉ gồm chữ không dấu, tối đa 4 ký tự.' };
  if (!(tu >= 1 && tu <= 99 && den >= 1 && den <= 99)) return { loi: 'Số bàn từ 1 tới 99.' };
  if (tu > den) { var x = tu; tu = den; den = x; }
  var n = den - tu + 1, a = khu + tu, b = khu + den;
  return { ten: n === 1 ? a + ' · 1 bàn' : (n === 2 ? a + ', ' + b + ' · 2 bàn' : a + ' đến ' + b + ' · ' + n + ' bàn') };
}

async function scrGmbInQr() {
  frame('In QR tại bàn', '<div class="emp"><div class="e1">⏳</div><div>Đang tải các điểm bán...</div></div>');
  var ds;
  try { ds = await api('vagabond.goi_mon_ban.diem_in_qr', {}); }
  catch (e) { frame('In QR tại bàn', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Chưa tải được điểm bán. Kéo xuống để thử lại.') + '</div></div>'); return; }
  ds = ds || [];
  if (!ds.length) { frame('In QR tại bàn', '<div class="emp"><div class="e1">🏬</div><div>Chưa có điểm bán nào có quầy. Bật quầy ở Cài đặt, Điểm bán.</div></div>'); return; }
  if (!ds.some(function (d) { return d.ma === gqDiem; })) gmbDoiDiem(ds[0]);
  gmbVeInQr(ds);
}

function gmbDoiDiem(d) {
  gqDiem = d.ma; gqTo = null; gqSua = !d.da_khai; gqDiaChi = d.dia_chi_qr || '';
  gqSoDo = (d.so_do || []).map(function (x) { return { khu: x.khu, tu: x.tu, den: x.den }; });
  if (!gqSoDo.length) gqSoDo = [{ khu: 'A', tu: 1, den: 10 }];
  gqChon = {};
  (d.nhom || []).forEach(function (g) { g.ban.forEach(function (b) { gqChon[b] = 1; }); });
}

function gmbDsChon(d) {
  var ra = [];
  (d.nhom || []).forEach(function (g) { g.ban.forEach(function (b) { if (gqChon[b]) ra.push(b); }); });
  return ra;
}

function gmbVeInQr(ds) {
  var d = ds.filter(function (x) { return x.ma === gqDiem; })[0] || ds[0];
  var kt = gmbKtDangChon(), xep = gmbXepA4(kt.w, kt.h), chon = gmbDsChon(d);
  var html = '<div class="card" style="padding:12px 14px">' +
    '<div style="font-size:13.5px;color:#475467;line-height:1.5">Mỗi bàn một mã QR. Khách quét là gọi món của đúng quầy, đúng bàn; quầy nhận trên màn Tính tiền. Mã không có hạn, in một lần dán lâu dài.</div></div>' +
    '<div class="sec">Điểm bán</div><div style="display:flex;gap:8px;overflow-x:auto;padding:0 2px 6px">' +
    ds.map(function (x) { return posChipNut('data-gqdiem="' + h(x.ma) + '"', h(x.ten), x.ma === gqDiem); }).join('') + '</div>';
  /* Sơ đồ bàn */
  html += '<div class="sec">Sơ đồ bàn · ' + h(d.ten) + '</div><div class="card" style="padding:12px 14px">';
  if (!gqSua) {
    html += (d.nhom || []).map(function (g) {
      return '<div style="font-size:13.5px;margin:2px 0"><b>' + (g.khu ? 'Khu ' + h(g.khu) : 'Bàn số') + '</b> · ' + h(g.ban[0]) +
        (g.ban.length > 1 ? ' đến ' + h(g.ban[g.ban.length - 1]) : '') + ' · ' + g.ban.length + ' bàn</div>';
    }).join('') +
      (d.da_khai ? '' : '<div style="font-size:12.5px;color:#6b7280;margin-top:4px">Điểm này chưa khai sơ đồ nên đang dùng Bàn 1 tới 20.</div>') +
      '<div style="font-size:12.5px;color:#6b7280;margin-top:4px">Địa chỉ in dưới standee: ' + h(gqDiaChi || 'chưa có') + '</div>' +
      '<button class="btn gh" id="gqSua" style="margin-top:10px">Sửa sơ đồ bàn</button>';
  } else {
    html += '<div style="display:grid;grid-template-columns:70px 1fr 1fr 44px;gap:6px;font-size:12px;color:#6b7280"><span>Khu</span><span>Từ số</span><span>Đến số</span><span></span></div>' +
      gqSoDo.map(function (r, i) {
        var mt = gmbMoTaDong(r);
        return '<div style="display:grid;grid-template-columns:70px 1fr 1fr 44px;gap:6px;margin-top:6px">' +
          '<input class="tin" data-gqsd="' + i + '" data-k="khu" maxlength="4" value="' + h(r.khu) + '" placeholder="A" style="min-height:44px;text-transform:uppercase">' +
          '<input class="tin" data-gqsd="' + i + '" data-k="tu" type="number" inputmode="numeric" min="1" max="99" value="' + h(r.tu) + '" style="min-height:44px">' +
          '<input class="tin" data-gqsd="' + i + '" data-k="den" type="number" inputmode="numeric" min="1" max="99" value="' + h(r.den) + '" style="min-height:44px">' +
          '<button class="btn gh" data-gqxoa="' + i + '" aria-label="Bỏ dòng" style="margin:0;min-height:44px;padding:0">✕</button></div>' +
          '<div id="gqMt' + i + '" style="font-size:12px;margin:3px 2px 0;color:' + (mt.loi ? '#b42318' : '#0e7490') + '">' + h(mt.loi || mt.ten) + '</div>';
      }).join('') +
      '<button class="btn gh" id="gqThem" style="margin-top:10px">+ Thêm khu</button>' +
      '<div style="font-size:12.5px;color:#6b7280;line-height:1.5;margin-top:8px">Tên khu là chữ ngắn không dấu (A, B, VIP, SAN). Để trống tên khu thì bàn chỉ có số như cũ. Lưu một lần, màn Tính tiền dùng chung. Đổi tên khu thì QR đã in của khu cũ hết dùng.</div>' +
      '<label style="display:block;font-size:13px;color:#475467;margin-top:10px">Địa chỉ in dưới standee' +
      '<input class="tin" id="gqDc" maxlength="120" value="' + h(gqDiaChi || '') + '" placeholder="9 Tran Cao Van, Sai Gon Ward" style="margin-top:4px;min-height:44px"></label>' +
      '<div style="font-size:12px;color:#6b7280;margin-top:3px">Chỉ hiện trên standee dọc (A6, A5). Miếng vuông 7 x 7 cm không có dòng địa chỉ.</div>' +
      '<div style="display:flex;gap:8px;margin-top:10px">' + (d.da_khai ? '<button class="btn gh" id="gqHuy" style="flex:1;margin:0">Thôi</button>' : '') +
      '<button class="btn" id="gqLuu" style="flex:2;margin:0">Lưu sơ đồ bàn</button></div>';
  }
  html += '</div>';
  /* Chọn bàn */
  if (!gqSua) {
    html += '<div class="sec">Chọn bàn cần in · ' + chon.length + ' bàn</div><div class="card" style="padding:10px 14px">' +
      (d.nhom || []).map(function (g) {
        var du = g.ban.every(function (b) { return gqChon[b]; });
        return '<div style="display:flex;justify-content:space-between;align-items:center;margin:6px 0">' +
          '<b style="font-size:13px">' + (g.khu ? 'Khu ' + h(g.khu) : 'Bàn số') + '</b>' +
          '<button class="btn gh" data-gqkhu="' + h(g.khu) + '" style="margin:0;width:auto;min-height:44px;padding:4px 12px;font-size:13px">' + (du ? 'Bỏ chọn cả khu' : 'Chọn cả khu') + '</button></div>' +
          '<div style="display:flex;flex-wrap:wrap;gap:6px">' + g.ban.map(function (b) {
            return posChipNut('data-gqban="' + h(b) + '"', g.khu ? h(b) : 'Bàn ' + h(b), !!gqChon[b]);
          }).join('') + '</div>';
      }).join('') + '</div>';
    /* Kích thước */
    html += '<div class="sec">Kích thước standee</div><div class="card" style="padding:10px 14px">' +
      GQ_KT.map(function (p) {
        var on = p.k === gqKt;
        return '<button class="btn gh" data-gqkt="' + p.k + '" style="display:block;width:100%;text-align:left;margin:0 0 6px;min-height:44px;' +
          (on ? 'border-color:#0e7490;background:#ecfeff' : '') + '"><b>' + (on ? '● ' : '○ ') + h(p.ten) + '</b>' +
          '<div style="font-size:12px;color:#6b7280;font-weight:400">' + h(p.giai) + '</div></button>';
      }).join('') +
      (gqKt === 'tu' ? '<div style="display:flex;gap:10px;margin-top:4px">' +
        '<label style="flex:1;font-size:13px;color:#475467">Rộng (mm)<input class="tin" id="gqW" type="number" inputmode="numeric" min="40" max="200" value="' + h(gqW) + '" style="margin-top:4px;min-height:44px"></label>' +
        '<label style="flex:1;font-size:13px;color:#475467">Cao (mm)<input class="tin" id="gqH" type="number" inputmode="numeric" min="40" max="287" value="' + h(gqH) + '" style="margin-top:4px;min-height:44px"></label></div>' : '') +
      '<div id="gqXep" style="font-size:12.5px;color:#0e7490;margin-top:6px">' + h(gmbCauXep(kt, chon.length)) + '</div></div>';
  }
  if (!gqSua && gqTo && gqTo.diem === gqDiem && GMB_KHUON_SVG) {
    html += '<div class="sec">Xem trước · ' + gqTo.to.length + ' miếng ' + h(gmbTenKt(kt)) + '</div>' +
      '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px">' +
      gqTo.to.slice(0, 12).map(function (t) {
        return '<div style="width:100%;aspect-ratio:' + kt.w + '/' + kt.h + ';overflow:hidden;border-radius:6px">' +
          gmbStandeeSvg(t, kt.w, kt.h, gqTo.dia_chi_qr).replace(/style="width:[\d.]+mm;height:[\d.]+mm;/, 'style="width:100%;height:100%;') + '</div>';
      }).join('') + '</div>' +
      (gqTo.to.length > 12 ? '<div style="font-size:12.5px;color:#6b7280;margin:6px 4px">Hiện 12 miếng đầu, tệp in đủ ' + gqTo.to.length + ' miếng.</div>' : '');
  }
  var coTo = !gqSua && gqTo && gqTo.diem === gqDiem && gqTo.to.length && GMB_KHUON_SVG && gmbKtHopLe(kt.w, kt.h);
  var soTrang = coTo && xep.n ? Math.ceil(gqTo.to.length / xep.n) : 0;
  var b = frame('In QR tại bàn', html, { footer: gqSua ? '' : (coTo
    ? '<button class="btn" id="gqIn">In ' + gqTo.to.length + ' miếng trên ' + soTrang + ' trang A4</button>'
    : '<button class="btn" id="gqTao">Tạo ' + chon.length + ' mã QR</button>') });
  b.addEventListener('click', function (e) {
    var c = e.target.closest('[data-gqdiem]');
    if (c) { var dd = ds.filter(function (x) { return x.ma === c.getAttribute('data-gqdiem'); })[0]; if (dd) gmbDoiDiem(dd); return gmbVeInQr(ds); }
    c = e.target.closest('[data-gqban]');
    if (c) { var bb = c.getAttribute('data-gqban'); if (gqChon[bb]) delete gqChon[bb]; else gqChon[bb] = 1; gqTo = null; return gmbVeInQr(ds); }
    c = e.target.closest('[data-gqkhu]');
    if (c) {
      var g = (d.nhom || []).filter(function (x) { return x.khu === c.getAttribute('data-gqkhu'); })[0];
      if (g) { var du = g.ban.every(function (x) { return gqChon[x]; }); g.ban.forEach(function (x) { if (du) delete gqChon[x]; else gqChon[x] = 1; }); }
      gqTo = null; return gmbVeInQr(ds);
    }
    c = e.target.closest('[data-gqkt]');
    if (c) { gqKt = c.getAttribute('data-gqkt'); return gmbVeInQr(ds); }
    c = e.target.closest('[data-gqxoa]');
    if (c) { gqSoDo.splice(Number(c.getAttribute('data-gqxoa')), 1); if (!gqSoDo.length) gqSoDo.push({ khu: '', tu: '', den: '' }); return gmbVeInQr(ds); }
    if (e.target.closest('#gqThem')) { gqSoDo.push({ khu: '', tu: 1, den: 10 }); return gmbVeInQr(ds); }
    if (e.target.closest('#gqSua')) { gqSua = true; return gmbVeInQr(ds); }
    if (e.target.closest('#gqHuy')) { gmbDoiDiem(d); return gmbVeInQr(ds); }
  });
  b.addEventListener('input', function (e) {
    var o = e.target;
    if (o.hasAttribute('data-gqsd')) {
      var i = Number(o.getAttribute('data-gqsd'));
      gqSoDo[i][o.getAttribute('data-k')] = o.value;
      var mt = gmbMoTaDong(gqSoDo[i]), el = document.getElementById('gqMt' + i);
      if (el) { el.textContent = mt.loi || mt.ten; el.style.color = mt.loi ? '#b42318' : '#0e7490'; }
    } else if (o.id === 'gqDc') gqDiaChi = o.value;
    else if (o.id === 'gqW' || o.id === 'gqH') {
      if (o.id === 'gqW') gqW = o.value; else gqH = o.value;
      var x = document.getElementById('gqXep');
      if (x) x.textContent = gmbCauXep(gmbKtDangChon(), gmbDsChon(d).length);
    }
  });
  var luu = document.getElementById('gqLuu');
  if (luu) luu.onclick = function () { gmbLuuSoDo(ds, d, 0); };
  var tao = document.getElementById('gqTao');
  if (tao) tao.onclick = async function () {
    var k = gmbKtDangChon(), dsBan = gmbDsChon(d);
    if (!dsBan.length) return toast('Chọn ít nhất một bàn để in.');
    if (!gmbKtHopLe(k.w, k.h)) return toast('Kích thước standee từ 40 x 40 mm tới 200 x 287 mm.', 4000);
    busy(true);
    try {
      var kq = await api('vagabond.goi_mon_ban.to_qr', { diem: gqDiem, ban: dsBan });
      await gmbNapKhuon();
      gqTo = kq;
    } catch (er) { busy(false); return toast((er && er.message) || 'Chưa tạo được mã QR, thử lại.', 5000); }
    busy(false);
    gmbVeInQr(ds);
  };
  var nutIn = document.getElementById('gqIn');
  if (nutIn) nutIn.onclick = function () { gmbInStandee(gqTo, gmbKtDangChon()); };
}

function gmbTenKt(kt) { return (kt.w / 10).toString().replace('.', ',') + ' x ' + (kt.h / 10).toString().replace('.', ',') + ' cm'; }

/* Câu "Một trang A4 dàn được N miếng". THUẦN. */
function gmbCauXep(kt, soBan) {
  if (!gmbKtHopLe(kt.w, kt.h)) return 'Kích thước từ 40 x 40 mm tới 200 x 287 mm.';
  var x = gmbXepA4(kt.w, kt.h);
  if (!x.n) return 'Khổ này không vừa trang A4.';
  return 'Một trang A4 dàn được ' + x.n + ' miếng ' + gmbTenKt(kt) + (soBan ? ', ' + soBan + ' bàn cần ' + Math.ceil(soBan / x.n) + ' trang.' : '.') +
    ' In đúng tỉ lệ 100%, cắt theo dấu ở lề.';
}

async function gmbLuuSoDo(ds, d, dongY) {
  busy(true);
  var kq;
  try { kq = await api('vagabond.goi_mon_ban.luu_so_do_ban', { diem: d.ma, so_do: gqSoDo, dia_chi_qr: gqDiaChi || '', dong_y_mat: dongY ? 1 : 0 }); }
  catch (er) { busy(false); return toast((er && er.message) || 'Chưa lưu được sơ đồ bàn, thử lại.', 6000); }
  busy(false);
  if (kq && !kq.ok && kq.mat) {
    var ok = await hoiCo('Mã QR đã in sẽ hết dùng', 'Sơ đồ mới không còn các bàn: ' + kq.mat.slice(0, 20).join(', ') +
      (kq.mat.length > 20 ? ' và ' + (kq.mat.length - 20) + ' bàn nữa' : '') + '.\nMã QR đã in của các bàn này sẽ không gọi món được nữa, phải in lại.', 'Vẫn lưu', true);
    if (ok) return gmbLuuSoDo(ds, d, 1);
    return;
  }
  var moi = kq && kq.diem;
  if (moi) { for (var i = 0; i < ds.length; i++) if (ds[i].ma === moi.ma) ds[i] = moi; gmbDoiDiem(moi); }
  toast('Đã lưu sơ đồ bàn. Màn Tính tiền dùng sơ đồ này từ lần mở sau.', 4000);
  gmbVeInQr(ds);
}

/* Mở cửa sổ in ngay trong cú chạm (khuôn và thư viện QR đã nạp lúc Tạo mã). */
function gmbInStandee(kq, kt) {
  if (!kq || !(kq.to || []).length || !GMB_KHUON_SVG) return toast('Bấm Tạo mã QR trước đã.');
  if (!gmbKtHopLe(kt.w, kt.h)) return toast('Kích thước standee từ 40 x 40 mm tới 200 x 287 mm.', 4000);
  var w = window.open('', '_blank');
  if (!w) return toast('Trình duyệt chặn cửa sổ in. Cho phép popup rồi bấm lại.', 4000);
  w.document.write(gmbTepIn(kq, kt.w, kt.h, kq.dia_chi_qr));
  w.document.close();
}

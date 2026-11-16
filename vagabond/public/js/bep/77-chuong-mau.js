/* v664 (anh Việt 16/11/2026, chị Dễ báo chuông O2O chỉ kêu một tiếng ngắn, dễ lỡ):
   năm mẫu chuông dài, êm, hợp không gian quán. Tổng hợp bằng WebAudio, không cần
   tệp âm thanh. Mỗi máy quầy chọn một mẫu (lưu trên máy), mặc định Hộp nhạc (anh Việt chọn 16/11).

   gmbNotChuong(ma) là phép THUẦN: trả danh sách nốt {t: giây bắt đầu, f: tần số Hz,
   d: giây ngân, v: độ to 0..1, k: kiểu âm sắc}. gmbPhatChuong dựng âm từ danh sách
   đó; ca kiểm và tệp nghe thử dùng đúng hai hàm này nên nghe thử là nghe thật. */
var GMB_KHOA_MAU = 'vgb_gmb_mau_chuong';
var GMB_MAU_CHUONG = [
  { ma: 'pha_le', ten: 'Chuông pha lê', mo_ta: 'Bốn nốt đi lên rồi ngân cả hợp âm, trong và êm. Khoảng 5 giây.' },
  { ma: 'le_tan', ten: 'Chuông quầy lễ tân', mo_ta: 'Ba tiếng chuông đồng gõ cách nhau, ngân dài như sảnh khách sạn. Khoảng 4 giây.' },
  { ma: 'thap', ten: 'Chuông tháp', mo_ta: 'Giai điệu chuông tháp đồng hồ cổ tám nốt, trầm và rõ, át được tiếng ồn. Khoảng 7 giây.' },
  { ma: 'chuong_gio', ten: 'Chuông gió', mo_ta: 'Chuỗi chuông gió lấp lánh rơi xuống, nhẹ, hợp quán yên tĩnh. Khoảng 5 giây.' },
  { ma: 'hop_nhac', ten: 'Hộp nhạc', mo_ta: 'Một câu nhạc ngắn như hộp nhạc lên dây cót, vui mà sang. Khoảng 5 giây.' }
];
var GMB_MAU_MAC_DINH = 'hop_nhac';

/* Âm sắc: tỉ lệ bồi âm và độ to tương đối của từng bồi âm, hệ số tắt dần. */
var GMB_AM_SAC = {
  pha_le: { boi: [[1, 1], [2, 0.32], [3, 0.12], [4.2, 0.05]] },
  dong: { boi: [[1, 1], [2.76, 0.42], [5.4, 0.2], [8.93, 0.08]] },
  ong: { boi: [[1, 1], [2, 0.5], [3, 0.28], [4.18, 0.14], [5.43, 0.06]] },
  gio: { boi: [[1, 1], [2.32, 0.25], [4.25, 0.12]] },
  hop: { boi: [[1, 1], [3, 0.18], [5.2, 0.07]] }
};

function gmbMauChuong() {
  var ma = '';
  try { ma = localStorage.getItem(GMB_KHOA_MAU) || ''; } catch (e) { }
  return GMB_MAU_CHUONG.some(function (m) { return m.ma === ma; }) ? ma : GMB_MAU_MAC_DINH;
}
function gmbDatMauChuong(ma) {
  try { localStorage.setItem(GMB_KHOA_MAU, ma); } catch (e) { }
}

/* THUẦN. Mã lạ thì ra Chuông pha lê (nhánh cuối); mẫu mặc định của máy là GMB_MAU_MAC_DINH. */
function gmbNotChuong(ma) {
  var N = function (t, f, d, v, k) { return { t: t, f: f, d: d, v: v, k: k }; };
  var C5 = 523.25, D5 = 587.33, E5 = 659.25, F5 = 698.46, G5 = 783.99, A5 = 880, B5 = 987.77;
  var C6 = 1046.5, D6 = 1174.66, E6 = 1318.51, G6 = 1567.98, A6 = 1760, C7 = 2093, D7 = 2349.32;
  var G4 = 392, B4 = 493.88;
  if (ma === 'le_tan') {
    return [0, 1.1, 2.2].map(function (t, i) { return N(t, A5, 2.4, i === 2 ? 0.8 : 0.7, 'dong'); })
      .concat([N(2.2, E6, 2.4, 0.3, 'dong')]);
  }
  if (ma === 'thap') {
    /* Giai điệu chuông tháp cổ (khúc một phần tư giờ), phổ biến từ thế kỷ 18. */
    var cau = [E5, C5, D5, G4, G4, D5, E5, C5];
    return cau.map(function (f, i) { return N(i * 0.55 + (i >= 4 ? 0.3 : 0), f, i === 7 ? 2.8 : 2.0, i === 7 ? 0.85 : 0.7, 'ong'); });
  }
  if (ma === 'chuong_gio') {
    var gio = [D7, A6, C7, G6, E6, A6, D6, G6, C6, E6, D6];
    var luc = [0, 0.16, 0.38, 0.52, 0.78, 0.95, 1.22, 1.4, 1.72, 1.95, 2.3];
    return gio.map(function (f, i) { return N(luc[i], f, 2.6, 0.5 + 0.06 * (i % 3), 'gio'); });
  }
  if (ma === 'hop_nhac') {
    var nhac = [[C6, 0], [E6, 0.28], [G6, 0.56], [E6, 0.84], [F5 * 2, 1.12], [D6, 1.4], [B5, 1.68], [C6, 2.1]];
    return nhac.map(function (x, i) { return N(x[1], x[0], i === 7 ? 2.6 : 1.5, i === 7 ? 0.6 : 0.5, 'hop'); })
      .concat([N(2.1, G5, 2.6, 0.3, 'hop'), N(2.1, E5, 2.6, 0.25, 'hop')]);
  }
  /* pha_le (mặc định): bốn nốt đi lên, nốt cuối đi cùng hợp âm ngân dài. */
  return [N(0, C6, 3.2, 0.55, 'pha_le'), N(0.24, E6, 3.0, 0.5, 'pha_le'), N(0.48, G6, 2.9, 0.48, 'pha_le'),
    N(0.72, C7, 3.6, 0.5, 'pha_le'), N(0.72, G5, 3.6, 0.3, 'pha_le'), N(0.72, E5, 3.6, 0.25, 'pha_le')];
}

/* THUẦN: độ dài cả mẫu (giây), để ca kiểm chốt "dài hơn một tiếng ngắn". */
function gmbDoDaiChuong(ma) {
  return gmbNotChuong(ma).reduce(function (m, n) { return Math.max(m, n.t + n.d); }, 0);
}

/* Dựng âm vào ac (AudioContext hay OfflineAudioContext). Trả thời điểm kết thúc. */
function gmbPhatChuong(ac, ma, batDau) {
  var t0 = (batDau == null ? ac.currentTime + 0.02 : batDau);
  var tong = ac.createGain(); tong.gain.value = 0.32; tong.connect(ac.destination);
  var het = t0;
  gmbNotChuong(ma).forEach(function (n) {
    var sac = (GMB_AM_SAC[n.k] || GMB_AM_SAC.pha_le).boi;
    sac.forEach(function (b, i) {
      var o = ac.createOscillator(), g = ac.createGain();
      o.type = 'sine'; o.frequency.value = n.f * b[0];
      o.connect(g); g.connect(tong);
      var bd = t0 + n.t, ngan = n.d / (1 + i * 0.9), dinh = n.v * b[1];
      g.gain.setValueAtTime(0.0001, bd);
      g.gain.linearRampToValueAtTime(dinh, bd + 0.006);
      g.gain.exponentialRampToValueAtTime(0.0001, bd + ngan);
      o.start(bd); o.stop(bd + ngan + 0.05);
      het = Math.max(het, bd + ngan + 0.05);
    });
  });
  return het;
}

/* Khối "Tiếng chuông" cuối bảng Gọi món tại bàn: năm chip (cao 44 điểm), dòng giải
   thích của mẫu đang chọn, nút Nghe thử. Lưu trên máy này (mỗi máy quầy một mẫu). */
function gmbKhoiChonChuong() {
  var dang = gmbMauChuong();
  var m = GMB_MAU_CHUONG.filter(function (x) { return x.ma === dang; })[0] || GMB_MAU_CHUONG[0];
  var md = function (x) { return x.ma === GMB_MAU_MAC_DINH ? ' (mặc định)' : ''; };
  return '<div style="margin-top:14px;padding-top:12px;border-top:1px solid #eee">' +
    '<div style="font-weight:700;font-size:14px;margin-bottom:8px">🔔 Tiếng chuông của máy này</div>' +
    '<div style="display:flex;flex-wrap:wrap;gap:8px">' + GMB_MAU_CHUONG.map(function (x) {
      var on = x.ma === dang;
      return '<button data-gmbmau="' + h(x.ma) + '" aria-pressed="' + on + '" style="min-height:44px;padding:0 14px;border-radius:999px;' +
        'font-size:13.5px;cursor:pointer;border:1.5px solid ' + (on ? '#0B7C93;background:#E4F9FD;color:#0B7C93;font-weight:700' : '#d4d4d8;background:#fff;color:#27272a') + '">' +
        h(x.ten + md(x)) + '</button>';
    }).join('') + '</div>' +
    '<div style="font-size:13px;color:#52525b;margin:8px 0">' + h(m.mo_ta) + ' Còn đơn chờ chưa xử lý thì cứ 1 phút kêu lại.</div>' +
    '<button data-gmbnghe="1" style="min-height:44px;padding:0 16px;border-radius:10px;border:1px solid #d4d4d8;background:#fff;font-size:13.5px;cursor:pointer">▶ Nghe thử</button>' +
    '</div>';
}

/* Nút "Chọn chuông" (dải báo đơn, màn Đơn giao của quầy): bảng riêng chỉ có khối
   chọn tiếng chuông, mở được cả khi không có đơn chờ. */
function gmbMoChonChuong() {
  var cu = document.getElementById('gmbChonChuong');
  if (cu) cu.remove();
  var ov = document.createElement('div'); ov.className = 'sh'; ov.id = 'gmbChonChuong';
  function ve() {
    /* Codex #575: .shb chung có overflow:hidden; điện thoại nằm ngang thì phần
       âm báo tiền và nút Nghe thử bị cắt. Bảng này tự cuộn dọc. */
    ov.innerHTML = '<div class="shb" style="padding:16px 14px calc(env(safe-area-inset-bottom,0px) + 16px);overflow-y:auto;-webkit-overflow-scrolling:touch">' +
      '<div class="shh" style="padding:0 0 4px"><b>Chọn chuông và âm báo</b><div class="x" data-gmbdong="1">&times;</div></div>' +
      '<div style="font-size:13px;color:#52525b">Chuông đơn kêu khi có đơn gọi món tại bàn, bàn cần trợ giúp, đơn giao chờ xác nhận. Âm báo tiền kêu khi khách chuyển khoản đủ tiền.</div>' +
      gmbKhoiChonChuong() + tienKhoiChonBao() + '</div>';
  }
  ve();
  document.body.appendChild(ov);
  ov.onclick = function (e) {
    if (e.target === ov || e.target.closest('[data-gmbdong]')) return ov.remove();
    var cm = e.target.closest('[data-gmbmau]');
    if (cm) { gmbDatMauChuong(cm.getAttribute('data-gmbmau')); ve(); return gmbKeu(); }
    if (e.target.closest('[data-gmbnghe]')) return gmbKeu();
    var tm = e.target.closest('[data-tienmau]');
    if (tm) { tienDatMauBao(tm.getAttribute('data-tienmau')); ve(); return tienBao(95000); }
    if (e.target.closest('[data-tiennghe]')) return tienBao(95000);
  };
  return ov;
}

/* ---------- v664 (anh Việt 16/11/2026): âm báo TIỀN CHUYỂN KHOẢN VỀ ----------
   "giọng người đọc đã nhận chuyển khoản bằng tiếng Anh cho sang". Anh nghe năm
   mẫu và chọn mẫu 2: hai nốt chuông rồi giọng nữ Anh-Anh đọc "Payment received.
   Thank you." Âm báo là TỆP THU SẴN (public/am_thanh), không dùng giọng đọc của
   máy, nên máy quầy nào nghe cũng giống hệt bản anh đã duyệt. Báo đúng MỘT lần
   cho một bill khi SePay nhận đủ tiền. Tệp chưa tải được thì kêu chuông. */
var TIEN_KHOA_MAU = 'vgb_tien_mau_bao';
/* ?v= là 8 ký tự đầu sha1 của tệp; đổi tệp thì đổi số (ca kiểm chốt). */
var TIEN_TEP = '/assets/vagabond/am_thanh/tien-ve-payment-received.mp3?v=02c3e730';
var TIEN_MAU_BAO = [
  { ma: 'giong', ten: 'Payment received', mo_ta: 'Chuông rồi giọng nữ Anh-Anh đọc "Payment received. Thank you."' },
  { ma: 'chi_chuong', ten: 'Chỉ chuông', mo_ta: 'Hai nốt chuông vàng sáng, không đọc.' }
];
var TIEN_MAU_MAC_DINH = 'giong';
var TIEN_DA_BAO = {};
var TIEN_BUF = null, TIEN_NAP = null;

function tienMauBao() {
  var ma = '';
  try { ma = localStorage.getItem(TIEN_KHOA_MAU) || ''; } catch (e) { }
  return TIEN_MAU_BAO.some(function (m) { return m.ma === ma; }) ? ma : TIEN_MAU_MAC_DINH;
}
function tienDatMauBao(ma) {
  try { localStorage.setItem(TIEN_KHOA_MAU, ma); } catch (e) { }
}

/* THUẦN: hai nốt chuông vàng sáng báo tiền về (khác hẳn chuông đơn O2O). Cũng là
   hai nốt mở đầu của tệp thu sẵn. */
function tienNotChuong() {
  return [{ t: 0, f: 1318.51, d: 1.4, v: 0.55, k: 'pha_le' }, { t: 0.16, f: 1975.53, d: 1.8, v: 0.5, k: 'pha_le' },
    { t: 0.16, f: 987.77, d: 1.8, v: 0.25, k: 'pha_le' }];
}

function tienAc() {
  var C = window.AudioContext || window.webkitAudioContext;
  if (!C) return null;
  if (!GMB_AC || GMB_AC.state === 'closed') GMB_AC = new C();
  if (GMB_AC.state === 'suspended' && GMB_AC.resume) GMB_AC.resume();
  return GMB_AC;
}

/* Tải và giải mã tệp một lần cho cả phiên. Hỏng thì lần sau tải lại. */
function tienNapTep(ac) {
  if (TIEN_BUF) return Promise.resolve(TIEN_BUF);
  if (TIEN_NAP) return TIEN_NAP;
  TIEN_NAP = fetch(TIEN_TEP, { credentials: 'same-origin' }).then(function (r) {
    if (!r.ok) throw new Error('tep am bao ' + r.status);
    return r.arrayBuffer();
  }).then(function (b) {
    /* Safari cũ chỉ có decodeAudioData kiểu gọi lại. */
    return new Promise(function (ok, hong) {
      var p = ac.decodeAudioData(b, ok, hong);
      if (p && p.then) p.then(ok, hong);
    });
  }).then(function (buf) { TIEN_BUF = buf; return buf; }, function (e) { TIEN_NAP = null; throw e; });
  return TIEN_NAP;
}

function tienKeuChuong(ac) {
  var t0 = ac.currentTime + 0.02, tong = ac.createGain();
  tong.gain.value = 0.32; tong.connect(ac.destination);
  tienNotChuong().forEach(function (n) {
    GMB_AM_SAC.pha_le.boi.forEach(function (b, i) {
      var o = ac.createOscillator(), g = ac.createGain(), bd = t0 + n.t, ngan = n.d / (1 + i * 0.9);
      o.type = 'sine'; o.frequency.value = n.f * b[0]; o.connect(g); g.connect(tong);
      g.gain.setValueAtTime(0.0001, bd); g.gain.linearRampToValueAtTime(n.v * b[1], bd + 0.006);
      g.gain.exponentialRampToValueAtTime(0.0001, bd + ngan); o.start(bd); o.stop(bd + ngan + 0.05);
    });
  });
}
function tienPhatTep(ac, buf) {
  var src = ac.createBufferSource(), g = ac.createGain();
  src.buffer = buf; g.gain.value = 0.9;
  src.connect(g); g.connect(ac.destination); src.start(ac.currentTime + 0.02);
}

/* Báo tiền về. khoa: nội dung chuyển khoản của bill, cùng bill chỉ báo một lần.
   Trả true khi đã báo. (soTien giữ cho nơi gọi cũ, tệp thu sẵn không đọc số.) */
function tienDaBao(khoa) {
  if (TIEN_DA_BAO[khoa]) return true;
  try { return sessionStorage.getItem('vgb_tien_bao:' + khoa) === '1'; } catch (e) { return false; }
}
function tienBao(soTien, khoa, ma) {
  /* Cùng bill chỉ báo một lần, kể cả khi màn tính tiền và bảng QR cùng thấy
     tiền về, hay quầy tải lại trang trong lúc còn mở bill. */
  if (khoa) {
    if (tienDaBao(khoa)) return false;
    TIEN_DA_BAO[khoa] = 1;
    try { sessionStorage.setItem('vgb_tien_bao:' + khoa, '1'); } catch (e) { }
  }
  ma = ma || tienMauBao();
  var ac = null;
  try { ac = tienAc(); } catch (e) { }
  if (!ac) return true;
  if (ma !== 'giong') { try { tienKeuChuong(ac); } catch (e) { } return true; }
  if (TIEN_BUF) { try { tienPhatTep(ac, TIEN_BUF); } catch (e) { } return true; }
  tienNapTep(ac).then(function (buf) { tienPhatTep(ac, buf); }, function () { try { tienKeuChuong(ac); } catch (e) { } });
  return true;
}

/* Khối "Âm báo tiền chuyển khoản về" trong bảng Chọn chuông. */
function tienKhoiChonBao() {
  var dang = tienMauBao();
  var m = TIEN_MAU_BAO.filter(function (x) { return x.ma === dang; })[0] || TIEN_MAU_BAO[0];
  return '<div style="margin-top:14px;padding-top:12px;border-top:1px solid #eee">' +
    '<div style="font-weight:700;font-size:14px;margin-bottom:8px">💸 Âm báo tiền chuyển khoản về</div>' +
    '<div style="display:flex;flex-wrap:wrap;gap:8px">' + TIEN_MAU_BAO.map(function (x) {
      var on = x.ma === dang;
      return '<button data-tienmau="' + h(x.ma) + '" aria-pressed="' + on + '" style="min-height:44px;padding:0 14px;border-radius:999px;' +
        'font-size:13.5px;cursor:pointer;border:1.5px solid ' + (on ? '#15803d;background:#dcfce7;color:#166534;font-weight:700' : '#d4d4d8;background:#fff;color:#27272a') + '">' +
        h(x.ten + (x.ma === TIEN_MAU_MAC_DINH ? ' (mặc định)' : '')) + '</button>';
    }).join('') + '</div>' +
    '<div style="font-size:13px;color:#52525b;margin:8px 0">' + h(m.mo_ta) + ' Báo một lần cho mỗi bill khi SePay nhận đủ tiền.</div>' +
    '<button data-tiennghe="1" style="min-height:44px;padding:0 16px;border-radius:10px;border:1px solid #d4d4d8;background:#fff;font-size:13.5px;cursor:pointer">▶ Nghe thử</button>' +
    '</div>';
}

/* iPad và iPhone chỉ cho phát âm thanh sau lần chạm đầu tiên của người dùng.
   Lần chạm đầu vào app thì mở loa (AudioContext) và tải sẵn tệp âm báo, để lúc
   tiền về máy phát được ngay. */
(function () {
  try {
    if (!document.addEventListener) return;
    var mo = function () {
      document.removeEventListener('click', mo, true);
      try { var ac = tienAc(); if (ac) tienNapTep(ac).catch(function () { }); } catch (e) { }
    };
    document.addEventListener('click', mo, true);
  } catch (e) { }
})();

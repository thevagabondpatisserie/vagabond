/* ---------- 69. Cài đặt tự động hoá: việc máy soạn sẵn (v646) ----------

   Anh Việt duyệt bản vẽ 09/11/2026: "Anh muốn nó là việc cụ thể luôn để cho
   nhân viên chỉ việc bấm vào là làm". Mỗi thẻ là một việc máy soạn sẵn rồi
   đưa vào Việc cần làm của đúng người; quá hạn mới nhắn nhóm Zalo.

   Màn này không tự tính con số nào: tên việc, giờ, hạn, tình hình hôm nay đều
   do máy chủ (vagabond/viec_tu_dong.py) gửi xuống. Chỉ Giám đốc và Quản trị
   thấy công tắc và nút Sửa; quản lý bộ phận chỉ xem. Máy chủ kiểm lại quyền ở
   cửa lưu, công tắc ẩn ở đây chỉ để khỏi bấm vào rồi bị từ chối. */

var TDH = { d: null, bp: '' };

function coQuyenTdh() {
  return hasRole('System Manager') || hasRole('AP Giám đốc') || hasRole('Giám đốc') ||
    hasRole('Manufacturing Manager') || hasRole('Stock Manager') || hasRole('Sales Manager') ||
    hasRole('Accounts Manager') || hasRole('Purchase Manager') || hasRole('VGB - Quản lý cửa hàng');
}

var TDH_MAU = { g: '#15803d', y: '#b45309', r: '#b91c1c', x: '#8a90a0' };
var TDH_O = {
  trong: ['Ô số để trống, người nhập', '#92400e', '#FEF3C7'],
  san: ['Điền sẵn, sửa được', '#0B7C93', '#E1F1F4']
};

/* THUẦN: đếm việc đang bật, đang tắt, đang có chuyện (đỏ) cho dải số trên đầu. */
function tdhDem(ds) {
  var ra = { bat: 0, tat: 0, do_: 0, vang: 0 };
  (ds || []).forEach(function (x) {
    if (x.bat) ra.bat++; else ra.tat++;
    if (x.mau === 'r') ra.do_++;
    if (x.mau === 'y') ra.vang++;
  });
  return ra;
}

/* THUẦN: lọc theo chip bộ phận; rỗng là tất cả. */
function tdhLoc(ds, bp) {
  return (ds || []).filter(function (x) { return !bp || x.bo_phan === bp; });
}

function tdhCongTac(ma, bat) {
  return '<button type="button" data-tdhbat="' + h(ma) + '" role="switch" aria-checked="' + (bat ? 'true' : 'false') +
    '" aria-label="Bật tắt việc" style="flex:none;width:52px;height:44px;border:0;background:none;padding:0;cursor:pointer">' +
    '<span style="display:block;position:relative;width:44px;height:26px;border-radius:13px;margin:auto;background:' + (bat ? '#0B7C93' : '#cfd4de') + '">' +
    '<span style="position:absolute;top:3px;' + (bat ? 'right:3px' : 'left:3px') + ';width:20px;height:20px;border-radius:50%;background:#fff"></span></span></button>';
}

function tdhNhan(chu, mau, nen) {
  return '<span style="display:inline-block;font-size:11.5px;font-weight:700;border-radius:20px;padding:2px 9px;color:' + mau + ';background:' + nen + '">' + h(chu) + '</span>';
}

function tdhDong(nhan, chu) {
  return '<div style="display:flex;gap:10px;padding:7px 0;border-top:1px solid #f0f2f6;font-size:13.5px;line-height:1.5">' +
    '<div style="flex:0 0 98px;color:#8a90a0;font-size:12.5px">' + h(nhan) + '</div><div style="flex:1;min-width:0">' + chu + '</div></div>';
}

function tdhThe(x, sua) {
  var o = TDH_O[x.o];
  var gio = x.gio ? '<b>' + h(x.gio) + '</b> · ' : '';
  var han = x.mo_ta_han ? '<b>' + h(x.mo_ta_han) + '</b>' + (x.bao ? '<br><span style="color:#5a6070">' + h(x.bao) + '</span>' : '') : '<span style="color:#8a90a0">Không có hạn riêng</span>';
  var coSua = sua && (x.gio_sua || x.han_kieu || x.nguong);
  return '<div class="card" style="padding:12px 14px;margin-bottom:10px' + (x.bat ? '' : ';opacity:.82') + '">' +
    '<div style="display:flex;align-items:flex-start;gap:10px">' +
    '<div style="font-size:24px;line-height:44px;flex:none">' + h(x.icon || '⚡') + '</div>' +
    '<div style="flex:1;min-width:0;padding-top:4px"><div style="font-weight:700;font-size:15.5px">' + h(x.ten) + '</div>' +
    '<div style="font-size:12.5px;color:#6b7280;margin-top:2px">' + h(x.mo) + '</div>' +
    '<div style="margin-top:6px">' + (x.co_san ? tdhNhan('Đã có, nâng thành việc', '#4338ca', '#eef2ff') : tdhNhan('Mới', '#b91c1c', '#FDE8E8')) + '</div></div>' +
    (sua && !x.chi_xem ? tdhCongTac(x.ma, x.bat) : (x.chi_xem ? '<span style="flex:none;font-size:12px;color:#8a90a0;padding-top:12px">Luôn chạy</span>' : '')) +
    '</div>' +
    '<div style="margin-top:8px">' +
    tdhDong('Máy soạn sẵn', gio + h(x.may)) +
    tdhDong('Người làm', h(x.nguoi) + (o ? '<div style="margin-top:5px">' + tdhNhan(o[0], o[1], o[2]) + '</div>' : '')) +
    tdhDong('Quá hạn thì', han) +
    tdhDong('Hôm nay', '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;background:' +
      (TDH_MAU[x.mau] || TDH_MAU.x) + '"></span>' + h(x.tinh_hinh || '')) +
    '</div>' +
    '<div style="display:flex;gap:8px;margin-top:8px">' +
    (coSua ? '<button class="btn gh" data-tdhsua="' + h(x.ma) + '" style="flex:1;margin:0">Sửa giờ, hạn</button>' : '') +
    (x.man ? '<button class="btn gh" data-tdhmo="' + h(x.man) + '" style="flex:1;margin:0">Mở màn làm việc</button>' : '') +
    '</div></div>';
}

async function scrTuDongHoa(giu) {
  if (!coQuyenTdh()) {
    frame('Cài đặt tự động hoá', '<div class="emp"><div class="e1">🔒</div><div class="e2">Bạn chưa được mở màn này. Nhờ quản trị cấp quyền.</div></div>');
    return;
  }
  if (!giu || !TDH.d) {
    frame('Cài đặt tự động hoá', '<div class="emp"><div class="e1">⏳</div></div>');
    try { TDH.d = await api('vagabond.viec_tu_dong.ds', {}); }
    catch (e) {
      frame('Cài đặt tự động hoá', '<div class="emp"><div class="e1">⚠️</div><div class="e2">' + h(errMsg(e)) + '</div></div>');
      return;
    }
  }
  var d = TDH.d, ds = d.viec || [];
  var dem = tdhDem(ds);
  var chips = [['', 'Tất cả', ds.length]].concat((d.bo_phan || []).map(function (b) {
    return [b, b, tdhLoc(ds, b).length];
  })).filter(function (c) { return c[2] > 0; }).map(function (c) {
    return '<div class="chip' + (TDH.bp === c[0] ? ' on' : '') + '" data-tdhbp="' + h(c[0]) + '">' + h(c[1]) + ' <b>' + c[2] + '</b></div>';
  }).join('');
  var o = function (n, chu, mau) {
    return '<div style="flex:1;background:#fff;border-radius:12px;padding:10px 12px;border:1px solid #e8ebf0">' +
      '<div style="font-size:22px;font-weight:800;color:' + mau + '">' + n + '</div><div style="font-size:12px;color:#6b7280">' + chu + '</div></div>';
  };
  var html = '<div class="card" style="padding:12px 14px;font-size:13.5px;line-height:1.55;color:#374151">' +
    'Mỗi thẻ là một việc máy <b>soạn sẵn</b> rồi đưa vào <b>Việc cần làm</b> của đúng người. Người làm chỉ mở ra, nhập số, bấm một nút. ' +
    'Tin Zalo chỉ là đường mở thẳng vào việc; quá hạn mới nhắn cấp trên.' +
    (d.sua ? '' : '<div style="margin-top:6px;color:#8a90a0">Bạn đang xem. Chỉ Giám đốc và Quản trị bật tắt, sửa giờ được.</div>') + '</div>' +
    '<div style="display:flex;gap:8px;margin:0 0 10px">' + o(dem.bat, 'Đang bật', '#15803d') + o(dem.tat, 'Đang tắt', '#6b7280') +
    o(dem.do_, 'Quá hạn hôm nay', '#b91c1c') + '</div>' +
    '<div style="display:flex;gap:16px;flex-wrap:wrap;font-size:12.5px;color:#374151;margin:0 2px 10px">' +
    '<span>' + tdhNhan(TDH_O.trong[0], TDH_O.trong[1], TDH_O.trong[2]) + ' số đếm, số làm ra, tiền trong két</span>' +
    '<span>' + tdhNhan(TDH_O.san[0], TDH_O.san[1], TDH_O.san[2]) + ' số đặt, số chuyển</span></div>' +
    '<div class="chips">' + chips + '</div>' +
    tdhLoc(ds, TDH.bp).map(function (x) { return tdhThe(x, d.sua); }).join('');
  var b = frame('Cài đặt tự động hoá', html, { action: '&#8635;', onAction: function () { TDH.d = null; scrTuDongHoa(); } });
  b.onclick = async function (e) {
    var c = e.target.closest('[data-tdhbp]');
    if (c) { TDH.bp = c.dataset.tdhbp; return scrTuDongHoa(1); }
    var m = e.target.closest('[data-tdhmo]');
    if (m) return vgbGo(m.dataset.tdhmo);
    var s = e.target.closest('[data-tdhsua]');
    if (s) return tdhSua(ds.filter(function (x) { return x.ma === s.dataset.tdhsua; })[0]);
    var t = e.target.closest('[data-tdhbat]');
    if (t) {
      var x = ds.filter(function (v) { return v.ma === t.dataset.tdhbat; })[0];
      if (!x) return;
      if (!x.bat && x.can_khai && !await confirmSheet('Bật "' + x.ten + '"?', x.can_khai, 'Vẫn bật')) return;
      return tdhLuu({ ma: x.ma, bat: x.bat ? 0 : 1 }, (x.bat ? 'Đã tắt: ' : 'Đã bật: ') + x.ten);
    }
  };
}

async function tdhLuu(gui, cau) {
  busy(1);
  try {
    await api('vagabond.viec_tu_dong.luu', gui);
    toast(cau || 'Đã lưu', 3500);
    TDH.d = null;
    await scrTuDongHoa();
  } catch (e) { toast(errMsg(e), 6000); } finally { busy(0); }
}

/* Tấm sửa giờ chạy và hạn. Chỉ hiện ô của đúng việc đó: việc có giờ cố định
   thì không có ô giờ; hạn kiểu giờ trong ngày hay kiểu số giờ chờ ghi rõ. */
function tdhSua(x) {
  if (!x) return;
  var o = function (id, nhan, gt, giaiThich, ph) {
    return '<div style="font-size:13px;font-weight:600;margin:12px 0 5px">' + h(nhan) + '</div>' +
      '<input class="tin" id="' + id + '" value="' + h(gt || '') + '" placeholder="' + h(ph) + '" style="margin:0;text-align:left;padding:0 12px">' +
      '<div style="font-size:12px;color:#8a90a0;margin-top:4px">' + h(giaiThich) + '</div>';
  };
  var ov = document.createElement('div'); ov.className = 'sh';
  ov.innerHTML = '<div class="shb" style="padding:18px 16px calc(env(safe-area-inset-bottom,0px) + 16px)">' +
    '<div style="font-size:17px;font-weight:700">' + h(x.ten) + '</div>' +
    (x.gio_sua ? o('tdhGio', 'Giờ chạy', x.gio, 'Kiểu 19:00 hoặc 19h. Máy soạn việc từ giờ này.', '19:00') : '') +
    (x.han_kieu === 'luc' ? o('tdhHan', 'Quá hạn lúc', x.han, 'Tới giờ này còn việc chưa làm thì nhắn nhóm Zalo của bộ phận.', '22:00') : '') +
    (x.han_kieu === 'sau_gio' ? o('tdhHan', 'Nhắn nhóm Kho sau (giờ)', x.han, 'Phiếu nằm chờ quá số giờ này thì nhắn nhóm Kho.', '24') : '') +
    (x.han2 ? o('tdhHan2', 'Nhắn Ban giám đốc sau (giờ)', x.han2, 'Phải lớn hơn ô trên.', '48') : '') +
    (x.nguong ? o('tdhNg', 'Còn đủ dùng dưới (ngày)', x.nguong, 'Theo lượng dùng 14 ngày qua của kho. Món còn ít hơn số ngày này thì máy soạn yêu cầu mua.', '3') +
      o('tdhDu', 'Mua đủ dùng (ngày)', x.du, 'Máy xin đủ dùng số ngày này. Phải lớn hơn ô trên.', '7') : '') +
    '<button class="btn gr" data-y style="margin-top:16px">Lưu</button>' +
    '<button class="btn gh" data-n style="margin-top:9px">Huỷ</button></div>';
  document.body.appendChild(ov);
  ov.onclick = function (e) {
    var t = e.target;
    if (t === ov || (t.hasAttribute && t.hasAttribute('data-n'))) return ov.remove();
    if (t.hasAttribute && t.hasAttribute('data-y')) {
      var gui = { ma: x.ma };
      var g = ov.querySelector('#tdhGio'), hn = ov.querySelector('#tdhHan'), h2 = ov.querySelector('#tdhHan2');
      if (g) gui.gio = g.value;
      if (hn) gui.han = hn.value;
      if (h2) gui.han2 = h2.value;
      var ng = ov.querySelector('#tdhNg'), du = ov.querySelector('#tdhDu');
      if (ng) gui.so_ngay_con = ng.value;
      if (du) gui.so_ngay_du = du.value;
      ov.remove();
      tdhLuu(gui, 'Đã lưu: ' + x.ten);
    }
  };
}

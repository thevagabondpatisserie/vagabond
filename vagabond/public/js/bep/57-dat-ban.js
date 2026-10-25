/* ---------------- Thông tin đặt bàn (v611)

   Anh Việt 25/10/2026: nút "Thông tin đặt bàn" trong phân hệ Bán hàng để quản
   lý cửa hàng xem yêu cầu đặt bàn khách gửi từ web, xác nhận (gửi email cho
   khách theo mẫu đã duyệt, nhắn Zalo nhóm Bán hàng), huỷ kèm lý do, và ghi
   nhận khách đã đến. Bố cục theo mockup anh duyệt cùng ngày.

   Quyền: chặn thật ở máy chủ (dat_ban.QUYEN_DAT_BAN); danh sách dưới đây chỉ
   để ẩn ô cho gọn mắt và phải trùng tuyệt đối danh sách máy chủ (ca kiểm
   thu_dat_ban_611 chốt). */
var QUYEN_DATBAN = ['Sales User', 'Sales Manager', 'System Manager', 'VGB - Quản lý cửa hàng'];
function coQuyenDatBan() {
  return QUYEN_DATBAN.some(function (v) { return hasRole(v); });
}

var dbKhoang = 'hom_nay';
var dbTt = '';
var dbTim = '';
var DB_KHOANG = [
  { k: 'hom_nay', ten: 'Hôm nay' },
  { k: 'ngay_mai', ten: 'Ngày mai' },
  { k: '7_ngay', ten: '7 ngày tới' },
  { k: 'da_qua', ten: 'Đã qua' },
];
/* Bốn trạng thái của phiếu đặt bàn, giá trị là đúng chữ lưu trên phiếu. */
var DB_TT = [
  { k: 'Chờ xác nhận', ten: 'Chờ xác nhận', ic: '⏳', mau: '#b45309', nen: '#fef3c7', chu: '#92400e' },
  { k: 'Đã xác nhận', ten: 'Đã xác nhận', ic: '✅', mau: '#15803d', nen: '#dcfce7', chu: '#166534' },
  { k: 'Đã đến', ten: 'Khách đã đến', ic: '🪑', mau: '#101828', nen: '#e5e7eb', chu: '#374151' },
  { k: 'Đã hủy', ten: 'Đã huỷ', ic: '✕', mau: '#98a2b3', nen: '#fee2e2', chu: '#991b1b' },
];
var DB_THU = ['Chủ Nhật', 'Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy'];

function dbTtCua(k) {
  for (var i = 0; i < DB_TT.length; i++) if (DB_TT[i].k === k) return DB_TT[i];
  return DB_TT[0];
}
function dbNgayDate(s) {
  var p = String(s || '').slice(0, 10).split('-');
  return new Date(+p[0], (+p[1] || 1) - 1, +p[2] || 1);
}
function dbDdMm(s) {
  var p = String(s || '').slice(0, 10).split('-');
  return p.length === 3 ? p[2] + '/' + p[1] : String(s || '');
}
/* "HÔM NAY · CHỦ NHẬT 25/10", "NGÀY MAI · THỨ HAI 26/10", "THỨ BA 27/10". */
function dbNhanNgay(ngay, homNay) {
  var thu = DB_THU[dbNgayDate(ngay).getDay()] + ' ' + dbDdMm(ngay);
  var lech = Math.round((dbNgayDate(ngay) - dbNgayDate(homNay)) / 86400000);
  var dau = lech === 0 ? 'Hôm nay · ' : lech === 1 ? 'Ngày mai · ' : lech === -1 ? 'Hôm qua · ' : '';
  return (dau + thu).toUpperCase();
}
function dbSoKhach(r) {
  var tre = +r.tre_em || 0;
  return (+r.so_khach || 0) + ' khách' + (tre ? ' (' + tre + ' trẻ em)' : '');
}
function dbTongKhach(ds) {
  return ds.reduce(function (t, r) { return t + (+r.so_khach || 0); }, 0);
}
/* Giờ hẹn đã qua chưa (theo đồng hồ máy). Đã qua thì không cho Xác nhận:
   máy chủ cũng chặn, ở đây chỉ để không hiện nút vô ích. */
function dbDaQuaGio(r, bayGio) {
  var p = String(r.gio || '00:00').split(':');
  var d = dbNgayDate(r.ngay);
  d.setHours(+p[0] || 0, +p[1] || 0, 0, 0);
  return d.getTime() <= (bayGio || new Date()).getTime();
}
/* Tìm theo tên (bỏ dấu, từng từ) hoặc số điện thoại (bỏ dấu cách, chấm). */
function dbKhopTim(r, q) {
  var t = String(q || '').trim();
  if (!t) return true;
  var so = t.replace(/[^0-9]/g, '');
  if (so.length >= 3 && so.length === t.replace(/[\s.+-]/g, '').length) {
    return String(r.sdt || '').replace(/[^0-9]/g, '').indexOf(so) >= 0;
  }
  return vgbKhop([r.ten, r.sdt, r.email], t);
}
function dbGioLuc(s) {
  var m = String(s || '').match(/(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})/);
  return m ? m[4] + ':' + m[5] + ' ' + m[3] + '/' + m[2] : '';
}

function dbOSo(t, ds, dong, dangChon) {
  return '<button class="btn gh" data-dbtt="' + h(t.k) + '" style="margin:0;min-height:44px;padding:8px 10px;text-align:left;' +
    'display:block;width:100%;border-radius:11px;' + (dangChon ? 'border:2px solid ' + t.mau + ';' : '') + '">' +
    '<div style="font-size:12.5px;color:#475467">' + t.ic + ' ' + h(t.ten) + '</div>' +
    '<div style="font-size:17px;font-weight:800;color:' + (ds.length ? t.mau : '#98a2b3') + '">' + ds.length + ' bàn</div>' +
    '<div style="font-size:12px;color:#475467">' + (dong || '&nbsp;') + '</div></button>';
}
function dbTheTomTat(tatCa, khoang, homNay) {
  var ten = (DB_KHOANG.filter(function (k) { return k.k === khoang; })[0] || DB_KHOANG[0]).ten;
  var coSo = [];
  tatCa.forEach(function (r) { var c = r.ten_co_so || r.co_so; if (c && coSo.indexOf(c) < 0) coSo.push(c); });
  var conGiu = tatCa.filter(function (r) { return r.trang_thai !== 'Đã hủy'; });
  var html = '<div class="card" data-dbtom="1" style="padding:12px 13px">' +
    '<div style="font-size:11.5px;color:#98a2b3;letter-spacing:.4px">ĐẶT BÀN ' + h(ten.toUpperCase()) +
    (coSo.length ? ' · ' + h(coSo.join(', ').toUpperCase()) : '') + '</div>' +
    '<div style="font-size:21px;font-weight:800;margin:2px 0 8px">' + conGiu.length + ' bàn · ' + dbTongKhach(conGiu) + ' khách</div>' +
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:7px">';
  DB_TT.forEach(function (t) {
    var ds = tatCa.filter(function (r) { return r.trang_thai === t.k; });
    var dong = '';
    if (t.k === 'Chờ xác nhận' && ds.length) {
      var toi = ds.filter(function (r) { return !dbDaQuaGio(r); });
      var g = toi[0] || ds[0];
      dong = (toi.length ? 'gần nhất ' : 'quá giờ ') + h(g.gio) + ' ' + h(dbNhanNgay(g.ngay, homNay).split(' · ')[0].toLowerCase());
    } else if (t.k !== 'Đã hủy' && ds.length) {
      dong = dbTongKhach(ds) + ' khách';
    }
    html += dbOSo(t, ds, dong, dbTt === t.k);
  });
  return html + '</div></div>';
}

function dbNut(attr, chu, kieu, rong) {
  var st = {
    goi: 'border:1.5px solid #0d9488;color:#0d9488;background:#fff;',
    ok: 'border:1.5px solid #52d8f0;background:#52d8f0;color:#0b2a33;',
    den: 'border:1.5px solid #15803d;color:#15803d;background:#fff;',
    huy: 'border:1.5px solid #f04438;color:#d92d20;background:#fff;',
  }[kieu];
  return '<button ' + attr + ' style="' + st + (rong ? 'flex:1;' : 'flex:0 0 76px;') +
    'height:44px;border-radius:11px;font-size:14px;font-weight:700;cursor:pointer;margin:0;padding:0 6px">' + chu + '</button>';
}
function dbThe(r, i) {
  var t = dbTtCua(r.trang_thai);
  var phu = [h(r.sdt)];
  if (r.khu_vuc) phu.push(h(r.khu_vuc));
  if (r.dip && r.dip !== 'Không có dịp riêng') phu.push((r.dip === 'Sinh nhật' ? '🎂 ' : '') + h(r.dip));
  /* Chữ thô, thoát HTML lúc vẽ (dbKhoiGhi) để đo được độ dài thấy trên màn. */
  var ghi = [];
  if (r.banh_kem_theo) ghi.push('🍰 Bánh đặt sẵn: ' + r.banh_kem_theo);
  if (r.ghi_chu) ghi.push('💬 Khách nhắn: ' + r.ghi_chu);
  if (r.trang_thai !== 'Chờ xác nhận' && r.xu_ly_boi) {
    var viec = { 'Đã xác nhận': 'Xác nhận', 'Đã hủy': 'Huỷ', 'Đã đến': 'Ghi khách đến' }[r.trang_thai] || 'Xử lý';
    ghi.push(viec + ' bởi ' + r.xu_ly_boi + (dbGioLuc(r.xu_ly_luc) ? ' lúc ' + dbGioLuc(r.xu_ly_luc) : ''));
  }
  if (r.trang_thai === 'Đã hủy' && r.ly_do_huy) ghi.push('Lý do đã báo khách: ' + r.ly_do_huy);
  if (r.thu_khach && r.trang_thai !== 'Chờ xác nhận') ghi.push('✉ ' + r.thu_khach);
  var nut = [];
  var tel = String(r.sdt || '').replace(/[^0-9+]/g, '');
  var goi = tel ? '<a href="tel:' + h(tel) + '" data-dbgoi="' + i + '" style="flex:0 0 76px;height:44px;border-radius:11px;' +
    'border:1.5px solid #0d9488;color:#0d9488;background:#fff;font-size:14px;font-weight:700;display:flex;align-items:center;' +
    'justify-content:center;text-decoration:none">📞 Gọi</a>' : '';
  if (r.trang_thai === 'Chờ xác nhận') {
    nut.push(goi);
    if (!dbDaQuaGio(r)) nut.push(dbNut('data-dbxn="' + i + '"', '✓ Xác nhận', 'ok', true));
    else nut.push('<div style="flex:1;font-size:12.5px;color:#b45309;align-self:center;text-align:center">Đã quá giờ hẹn</div>');
    nut.push(dbNut('data-dbhuy="' + i + '"', '✕ Huỷ', 'huy'));
  } else if (r.trang_thai === 'Đã xác nhận') {
    nut.push(goi, dbNut('data-dbden="' + i + '"', '🪑 Khách đã đến', 'den', true), dbNut('data-dbhuy="' + i + '"', '✕ Huỷ', 'huy'));
  }
  return '<div class="card" data-dbthe="' + h(r.name) + '" style="padding:12px 13px">' +
    '<div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px">' +
    '<span style="font-size:20px;font-weight:800;color:#0b2a33">' + h(r.gio) + '</span>' +
    '<span style="background:' + t.nen + ';color:' + t.chu + ';border-radius:999px;padding:2px 9px;font-size:11.5px;font-weight:700;white-space:nowrap">' +
    t.ic + ' ' + h(t.k === 'Đã đến' ? 'Đã đến' : t.ten) + '</span></div>' +
    '<div style="font-weight:700;font-size:15.5px">' + h(r.ten) + ' · ' + h(dbSoKhach(r)) + '</div>' +
    '<div style="font-size:13px;color:#475467;margin-top:2px">' + phu.join(' · ') + '</div>' +
    (nut.length ? '<div style="display:flex;gap:7px;margin-top:10px">' + nut.join('') + '</div>' : '') +
    dbKhoiGhi(ghi, i) + '</div>';
}

/* Codex #498 (4371298490), AGENTS 2b.17: khối chỉ để đọc
   không lấn chỗ khối để bấm. Ghi chú nằm DƯỚI hàng nút; tối đa hai dòng ngắn
   thì hiện thẳng, dài hơn (khách được gõ tới 1.000 ký tự) thì thu về một dòng
   đếm số, bấm mới mở. */
var DB_GHI_NGAN = 56;
function dbGhiNgan(ghi) {
  return ghi.length <= 2 && ghi.every(function (g) { return String(g).length <= DB_GHI_NGAN; });
}
function dbKhoiGhi(ghi, i) {
  if (!ghi.length) return '';
  var khung = 'font-size:12.5px;color:#475467;background:#f8fafc;border-radius:9px;padding:7px 9px;margin-top:8px;line-height:1.5;';
  var day = ghi.map(function (g) { return h(g); }).join('<br>');
  if (dbGhiNgan(ghi)) return '<div data-dbghi="' + i + '" style="' + khung + '">' + day + '</div>';
  var dau = String(ghi[0]);
  return '<button type="button" data-dbghimo="' + i + '" aria-expanded="false" style="' + khung +
    'display:block;width:100%;min-height:44px;text-align:left;border:0;cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' +
    '📝 ' + ghi.length + ' ghi chú · ' + h(dau.length > 40 ? dau.slice(0, 40) + '…' : dau) + ' <b style="color:#0d9488">Xem</b></button>' +
    '<div data-dbghi="' + i + '" hidden style="' + khung + 'display:none;white-space:pre-line;word-break:break-word">' + day + '</div>';
}

function dbVeDs(tatCa, homNay) {
  var ds = tatCa.filter(function (r) {
    if (dbTim) return dbKhopTim(r, dbTim);
    return !dbTt || r.trang_thai === dbTt;
  });
  var html = '';
  if (dbTim || dbTt) {
    html += '<div data-dbtongloc="1" style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;margin:0 14px 4px;' +
      'padding:8px 10px;border-radius:8px;background:#fffaeb;font-size:13px;color:#101828">' +
      '<span>Đang lọc' + (dbTim ? ' "' + h(dbTim) + '"' : ': ' + h(dbTtCua(dbTt).ten)) + '</span><b>' + ds.length + ' bàn · ' +
      dbTongKhach(ds) + ' khách</b></div>';
  }
  if (!ds.length) {
    return html + '<div class="card"><div class="emp" style="padding:24px"><div class="e1">🪑</div><div>' +
      (dbTim ? 'Không có đặt bàn nào khớp "' + h(dbTim) + '" trong khoảng ngày này.' :
        tatCa.length ? 'Không có đặt bàn nào ở nhóm này.' : 'Chưa có khách đặt bàn trong khoảng ngày này.') + '</div></div></div>';
  }
  var ngayCu = '';
  ds.forEach(function (r) {
    if (r.ngay !== ngayCu) {
      ngayCu = r.ngay;
      html += '<div style="font-size:12.5px;font-weight:700;color:#475467;margin:14px 16px 2px;letter-spacing:.3px">' +
        h(dbNhanNgay(r.ngay, homNay)) + '</div>';
    }
    html += dbThe(r, tatCa.indexOf(r));
  });
  return html;
}

/* Công tắc bật tắt (AGENTS 2b: bật tắt dùng công tắc, không hộp tích). */
function dbCongTac(id, bat, khoa) {
  return '<button type="button" role="switch" id="' + id + '" aria-checked="' + (bat ? 'true' : 'false') + '"' +
    (khoa ? ' disabled' : '') + ' style="flex:0 0 46px;width:46px;height:28px;border-radius:14px;border:0;padding:0;position:relative;' +
    'cursor:' + (khoa ? 'default' : 'pointer') + ';background:' + (bat ? '#0d9488' : '#d0d5dd') + '">' +
    '<span style="position:absolute;top:3px;' + (bat ? 'right:3px' : 'left:3px') + ';width:22px;height:22px;border-radius:50%;background:#fff"></span></button>';
}
function dbDatCongTac(nut, bat) {
  nut.setAttribute('aria-checked', bat ? 'true' : 'false');
  nut.style.background = bat ? '#0d9488' : '#d0d5dd';
  var cham = nut.querySelector('span');
  cham.style.left = bat ? '' : '3px';
  cham.style.right = bat ? '3px' : '';
}
function dbDauSheet(r, tieuDe, dayDu) {
  var dong3 = [h(r.ten_co_so || r.co_so)];
  if (r.khu_vuc) dong3.push(h(r.khu_vuc));
  if (r.dip && r.dip !== 'Không có dịp riêng') dong3.push(h(r.dip));
  return '<div style="width:40px;height:4px;background:#d0d5dd;border-radius:2px;margin:0 auto 6px"></div>' +
    '<div style="font-size:18px;font-weight:700;margin:4px 0 10px">' + h(tieuDe) + '</div>' +
    '<div style="font-size:13.5px;color:#475467;line-height:1.6"><b style="color:#101828">' + h(r.ten) + '</b> · ' + h(r.sdt) + '<br>' +
    h(DB_THU[dbNgayDate(r.ngay).getDay()]) + ' ' + h(dbDdMm(r.ngay)) + ' lúc <b>' + h(r.gio) + '</b> · ' + h(dbSoKhach(r)) +
    (dayDu ? '<br>' + dong3.join(' · ') : '') + '</div>';
}
function dbCauEmail(r, loai) {
  return r.email ? (loai === 'xac_nhan' ? 'Gửi email xác nhận tới ' : 'Gửi email báo khách tới ') + '<b>' + h(r.email) + '</b>'
    : 'Khách không để email. Máy chỉ nhắn Zalo nhóm, nhớ gọi báo khách.';
}
function dbMoSheet(html) {
  var ov = document.createElement('div'); ov.className = 'sh';
  ov.innerHTML = '<div class="shb" style="padding:16px 16px calc(env(safe-area-inset-bottom,0px) + 18px)">' + html + '</div>';
  document.body.appendChild(ov);
  ov.addEventListener('click', function (e) { if (e.target === ov) ov.remove(); });
  return ov;
}
async function dbGoi(method, args, xong) {
  busy(true);
  try {
    var kq = await api(method, args);
    busy(false);
    toast(xong + (kq && kq.thu_khach ? '. ' + kq.thu_khach : ''), 3600);
    go(scrDatBan, true);
    return true;
  } catch (e) {
    busy(false);
    toast(errMsg(e), 5000);
    return false;
  }
}

function dbSheetXacNhan(r) {
  var coMail = !!String(r.email || '').trim();
  var ov = dbMoSheet(dbDauSheet(r, 'Xác nhận đặt bàn', true) +
    '<div style="font-size:13.5px;font-weight:700;color:#344054;margin:12px 0 6px">Lời nhắn gửi khách (không bắt buộc)</div>' +
    '<textarea class="nt" id="dbLoiNhan" rows="3" maxlength="500" placeholder="Ví dụ: Tiệm đã ghi chú bánh sinh nhật, sẽ chuẩn bị nến cho anh chị."></textarea>' +
    '<div style="display:flex;align-items:center;gap:10px;margin:12px 0;font-size:14px">' + dbCongTac('dbGuiMail', coMail, !coMail) +
    '<span>' + dbCauEmail(r, 'xac_nhan') + '</span></div>' +
    '<div style="font-size:13px;color:#475467;line-height:1.55;margin-bottom:12px">Máy cũng nhắn nhóm Zalo Bán hàng: bàn đã xác nhận, ngày giờ, tên, số điện thoại, số khách, người xác nhận.</div>' +
    '<button class="btn" data-dbok="1" style="margin:0">' + (coMail ? 'Xác nhận và gửi email' : 'Xác nhận') + '</button>' +
    '<button class="btn gh" data-dbdong="1" style="margin-top:9px">Để sau</button>');
  var sw = ov.querySelector('#dbGuiMail'), ok = ov.querySelector('[data-dbok]');
  var bat = coMail;
  sw.onclick = function () {
    if (!coMail) return;
    bat = !bat; dbDatCongTac(sw, bat);
    ok.textContent = bat ? 'Xác nhận và gửi email' : 'Xác nhận, không gửi email';
  };
  ov.querySelector('[data-dbdong]').onclick = function () { ov.remove(); };
  ok.onclick = async function () {
    ok.disabled = true;
    var xong = await dbGoi('vagabond.dat_ban.xac_nhan', {
      name: r.name, loi_nhan: ov.querySelector('#dbLoiNhan').value.trim(), gui_email: bat ? 1 : 0
    }, 'Đã xác nhận bàn của ' + r.ten);
    if (xong) ov.remove(); else ok.disabled = false;
  };
}

function dbSheetHuy(r, lyDoMau) {
  var coMail = !!String(r.email || '').trim();
  var ov = dbMoSheet(dbDauSheet(r, 'Huỷ đặt bàn', false) +
    '<div style="font-size:13.5px;font-weight:700;color:#344054;margin:12px 0 6px">Lý do (bắt buộc, khách sẽ đọc câu này)</div>' +
    kmHangChip((lyDoMau || []).map(function (l, i) {
      return posChipNut('data-dbly="' + i + '"', h(l), false, false, '#4338ca');
    }).join('')) +
    '<textarea class="nt" id="dbLyDo" rows="2" maxlength="300" placeholder="Bấm một lý do ở trên hoặc tự ghi" style="margin-top:9px"></textarea>' +
    '<div style="display:flex;align-items:center;gap:10px;margin:12px 0;font-size:14px">' + dbCongTac('dbGuiMail', coMail, !coMail) +
    '<span>' + dbCauEmail(r, 'huy') + '</span></div>' +
    '<button class="btn" data-dbok="1" style="margin:0;background:#fff;border:2px solid #d92d20;color:#d92d20">Huỷ đặt bàn</button>' +
    '<button class="btn gh" data-dbdong="1" style="margin-top:9px">Không huỷ</button>');
  var ta = ov.querySelector('#dbLyDo'), sw = ov.querySelector('#dbGuiMail'), ok = ov.querySelector('[data-dbok]');
  var bat = coMail;
  ov.querySelectorAll('[data-dbly]').forEach(function (c) {
    c.onclick = function () {
      ta.value = lyDoMau[+c.getAttribute('data-dbly')];
      ov.querySelectorAll('[data-dbly]').forEach(function (x) {
        var chon = x === c;
        x.style.background = chon ? '#4338ca' : '#fff';
        x.style.color = chon ? '#fff' : '#374151';
        x.style.borderColor = chon ? '#4338ca' : '#d7dce5';
      });
    };
  });
  sw.onclick = function () { if (!coMail) return; bat = !bat; dbDatCongTac(sw, bat); };
  ov.querySelector('[data-dbdong]').onclick = function () { ov.remove(); };
  ok.onclick = async function () {
    var lyDo = ta.value.replace(/\s+/g, ' ').trim();
    if (lyDo.length < 5) { toast('Ghi lý do huỷ, khách sẽ đọc câu này.', 3200); ta.focus(); return; }
    ok.disabled = true;
    var xong = await dbGoi('vagabond.dat_ban.huy', { name: r.name, ly_do: lyDo, gui_email: bat ? 1 : 0 },
      'Đã huỷ bàn của ' + r.ten);
    if (xong) ov.remove(); else ok.disabled = false;
  };
}

async function scrDatBan() {
  var tieuDe = 'Thông tin đặt bàn';
  if (!coQuyenDatBan()) {
    frame(tieuDe, '<div class="emp"><div class="e1">🔒</div><div>Chỉ quản lý cửa hàng và Sales xem được đặt bàn.</div></div>');
    return;
  }
  frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc đặt bàn...</div></div>');
  var kq;
  try { kq = await api('vagabond.dat_ban.ds_dat_ban', { khoang: dbKhoang }); }
  catch (e) {
    frame(tieuDe, '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e)) + '</div></div>');
    return;
  }
  var tatCa = kq.rows || [], dem = kq.dem || {}, homNay = kq.hom_nay || today();
  /* Thanh công cụ chung (AGENTS 2b.6): hàng chip khoảng ngày, kèm số bàn còn
     giữ của từng khoảng, và ô tìm. Không có chip "tất cả": mỗi lần xem đúng
     một khoảng ngày. Mọi chip luôn hiện, kể cả khoảng chưa có ai đặt. */
  var cc = {
    ma: 'db',
    ho: [{ k: 'khoang', chon: dbKhoang, mau: '#0d9488', ds: DB_KHOANG.map(function (k) {
      return { k: k.k, ten: k.ten + (dem[k.k] && k.k !== 'da_qua' ? ' ' + dem[k.k] : '') };
    }) }],
    tim: { gt: dbTim, goiY: '🔎 Tìm tên khách, số điện thoại' },
  };
  var html = dsCongCu(cc);
  html += dbTheTomTat(tatCa, dbKhoang, homNay);
  html += '<div id="dbDs">' + dbVeDs(tatCa, homNay) + '</div>';
  html += '<div style="font-size:12px;color:#98a2b3;margin:10px 16px 18px;line-height:1.5">Đặt bàn khách gửi từ trang web. Xác nhận hoặc huỷ thì máy gửi email cho khách (nếu bật) và nhắn nhóm Zalo Bán hàng.</div>';
  var than = frame(tieuDe, html);
  var veLai = function () { var o = document.getElementById('dbDs'); if (o) o.innerHTML = dbVeDs(tatCa, homNay); };
  dsCongCuNoi(than, cc, function (ho, k) {
    if (ho === 'khoang') { dbKhoang = k || 'hom_nay'; dbTt = ''; dbTim = ''; }
    else if (ho === 'tim') dbTim = k;
    go(scrDatBan, true);
  });
  than.addEventListener('click', function (e) {
    var t = e.target.closest('[data-dbghimo]');
    if (t) {
      var mo = t.getAttribute('aria-expanded') !== 'true';
      var khoi = than.querySelectorAll('[data-dbghi="' + t.getAttribute('data-dbghimo') + '"]')[0];
      t.setAttribute('aria-expanded', mo ? 'true' : 'false');
      if (khoi) { khoi.style.display = mo ? 'block' : 'none'; if (mo) khoi.removeAttribute('hidden'); else khoi.setAttribute('hidden', ''); }
      return;
    }
    t = e.target.closest('[data-dbtt]');
    if (t) {
      var k = t.getAttribute('data-dbtt');
      dbTt = dbTt === k ? '' : k; dbTim = '';
      go(scrDatBan, true); return;
    }
    t = e.target.closest('[data-dbxn]');
    if (t) { dbSheetXacNhan(tatCa[+t.getAttribute('data-dbxn')]); return; }
    t = e.target.closest('[data-dbhuy]');
    if (t) { dbSheetHuy(tatCa[+t.getAttribute('data-dbhuy')], kq.ly_do_mau); return; }
    t = e.target.closest('[data-dbden]');
    if (t) {
      var r = tatCa[+t.getAttribute('data-dbden')];
      confirmSheet('Khách đã đến?', r.ten + ' · ' + dbSoKhach(r) + ' · ' + r.gio + '\nMáy chỉ ghi nhận, không gửi email hay tin nhắn.', 'Ghi khách đã đến')
        .then(function (dong) { if (dong) dbGoi('vagabond.dat_ban.da_den', { name: r.name }, 'Đã ghi khách ' + r.ten + ' đến'); });
    }
  });
  /* Tìm lọc ngay trên máy (danh sách đã có sẵn), chỉ vẽ lại phần danh sách
     nên ô tìm không mất con trỏ khi gõ. */
  var o = document.getElementById('dbDsTim');
  if (o) o.addEventListener('input', function () { dbTim = o.value.trim(); veLai(); });
}

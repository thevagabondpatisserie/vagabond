/* ---------------- Tuyển dụng (v622)

   Anh Việt 30/10/2026, duyệt bản đề xuất phân hệ Tuyển dụng (project doc
   de-xuat-phan-he-tuyen-dung-30-10-2026): làm ngay trong app; mọi quản lý bộ
   phận xem hồ sơ và chốt nhận người; ứng viên bắt buộc tích đồng ý lưu hồ sơ;
   buổi làm thử có trả công; bật tắt vị trí trên app là mục Tuyển dụng trên web
   đổi theo.

   Hai thẻ: Hồ sơ ứng viên (bảng trạng thái, gọi, Zalo, cập nhật, chấm phiếu,
   ghi công làm thử) và Vị trí (bật tắt Đang tuyển, sửa, mã QR cho cửa hàng).
   Con số đầu màn đo đúng điều quan trọng nhất của lao động theo ca: hồ sơ quá
   24 giờ chưa ai gọi.

   Quyền: chặn thật ở máy chủ (tuyen_dung.QUYEN_TUYEN_DUNG); danh sách dưới
   đây chỉ để ẩn ô, phải trùng tuyệt đối danh sách máy chủ (ca kiểm chốt). */
var QUYEN_TUYENDUNG = ['System Manager', 'Giám đốc', 'AP Giám đốc', 'VGB - Quản lý cửa hàng', 'Manufacturing Manager',
  'Stock Manager', 'Purchase Manager', 'Thu mua', 'Accounts Manager', 'VGB - Tuyển dụng'];
function coQuyenTuyenDung() {
  return QUYEN_TUYENDUNG.some(function (v) { return hasRole(v); });
}

var tdTab = 'hs';
var tdTt = '';
var tdVt = '';
var tdTim = '';
var tdLoc = '';
var tdKq = null;
/* Trạng thái một lượt ứng tuyển, giá trị là đúng chữ lưu trên hồ sơ. */
var TD_TT = [
  { k: 'Mới nhận', ic: '🆕', nen: '#fee4e2', chu: '#b42318', p: 'Hồ sơ vừa về, chưa ai liên hệ' },
  { k: 'Đã liên hệ', ic: '📞', nen: '#fef3c7', chu: '#92400e', p: 'Đã gọi hoặc nhắn, chờ chốt lịch' },
  { k: 'Hẹn phỏng vấn', ic: '📅', nen: '#e0f2fe', chu: '#075985', p: 'Đã có ngày giờ phỏng vấn' },
  { k: 'Làm thử', ic: '🧑‍🍳', nen: '#ede9fe', chu: '#5b21b6', p: 'Đang làm thử ca tại bếp hoặc quầy, có trả công' },
  { k: 'Đề nghị nhận việc', ic: '🤝', nen: '#ccfbf1', chu: '#115e59', p: 'Đã đề nghị, chờ ứng viên trả lời' },
  { k: 'Đã nhận việc', ic: '✅', nen: '#dcfce7', chu: '#166534', p: 'Đã nhận, chuyển sang nhận việc và thử việc' },
  { k: 'Dừng', ic: '✕', nen: '#f2f4f7', chu: '#475467', p: 'Không tiếp tục, bắt buộc ghi lý do' },
];
var TD_CAN_HEN = ['Hẹn phỏng vấn', 'Làm thử'];

function tdTtCua(k) {
  for (var i = 0; i < TD_TT.length; i++) if (TD_TT[i].k === k) return TD_TT[i];
  return TD_TT[0];
}
function tdLuc(s) {
  var m = String(s || '').match(/(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})/);
  return m ? new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5]) : null;
}
/* "14:00 31/10". */
function tdGioNgay(s) {
  var m = String(s || '').match(/(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})/);
  return m ? m[4] + ':' + m[5] + ' ' + m[3] + '/' + m[2] : '';
}
/* "nộp 3 giờ trước", "nộp 2 ngày trước". PHÉP THUẦN. */
function tdCachDay(s, bayGio) {
  var d = tdLuc(s), b = tdLuc(bayGio) || new Date();
  if (!d) return '';
  var gio = Math.max(0, Math.floor((b - d) / 3600000));
  if (gio < 1) return 'vừa nộp';
  if (gio < 48) return 'nộp ' + gio + ' giờ trước';
  return 'nộp ' + Math.floor(gio / 24) + ' ngày trước';
}
/* Lọc danh sách theo ô tìm, thẻ số đầu màn, chip trạng thái, chip vị trí. PHÉP THUẦN. */
function tdLocHs(rows, loc, homNay) {
  loc = loc || {};
  return (rows || []).filter(function (r) {
    if (loc.tim) {
      var so = String(loc.tim).replace(/[^0-9]/g, '');
      if (so.length >= 3 && so.length === String(loc.tim).replace(/[\s.+-]/g, '').length) {
        return String(r.sdt || '').indexOf(so) >= 0;
      }
      return vgbKhop([r.ho_ten, r.sdt, r.ten_vi_tri, r.khu_vuc], loc.tim);
    }
    if (loc.the === 'moi' && r.trang_thai !== 'Mới nhận') return false;
    if (loc.the === 'qua_han' && !+r.qua_han) return false;
    if (loc.the === 'hen' && !(TD_CAN_HEN.indexOf(r.trang_thai) >= 0 && String(r.lich_hen || '').slice(0, 10) === homNay)) return false;
    if (loc.the === 'cong' && !(+r.tien_cong_thu > 0 && !+r.da_tra_cong)) return false;
    if (loc.tt && r.trang_thai !== loc.tt) return false;
    if (loc.vt && r.vi_tri !== loc.vt) return false;
    return true;
  });
}

function tdTomTatHtml(t) {
  var o = function (k, ic, ten, so, dong, mau) {
    return '<button class="btn gh" data-tdthe="' + k + '" style="margin:0;min-height:44px;width:100%;padding:8px 10px;text-align:left;display:block;' +
      'border-radius:11px;' + (tdLoc === k ? 'border:2px solid ' + mau + ';' : '') + '">' +
      '<div style="font-size:12.5px;color:#475467">' + ic + ' ' + ten + '</div>' +
      '<div style="font-size:18px;font-weight:800;color:' + (so ? mau : '#98a2b3') + '">' + so + '</div>' +
      '<div style="font-size:12px;color:' + (dong && k === 'moi' ? '#b42318' : '#475467') + '">' + (dong || '&nbsp;') + '</div></button>';
  };
  return '<div class="card" data-tdtom="1" style="padding:12px 13px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:7px">' +
    o('moi', '🆕', 'Chưa gọi', t.moi || 0, t.qua_han ? t.qua_han + ' quá 24 giờ' : '', '#b42318') +
    o('hen', '📅', 'Hẹn hôm nay', t.hen_hom_nay || 0, '', '#075985') +
    o('cong', '💵', 'Công chưa trả', t.cong_chua_tra || 0, '', '#92400e') + '</div>';
}

function tdNut(attr, chu, kieu) {
  var st = {
    goi: 'border:1.5px solid #0d9488;color:#0d9488;background:#fff;',
    chinh: 'border:1.5px solid #52d8f0;background:#52d8f0;color:#0b2a33;',
    phu: 'border:1.5px solid #d0d5dd;color:#344054;background:#fff;',
  }[kieu || 'phu'];
  return '<button type="button" ' + attr + ' style="' + st + 'flex:1 1 0;width:auto;min-width:0;min-height:44px;border-radius:11px;' +
    'font-size:14px;font-weight:700;cursor:pointer;margin:0;padding:0 6px;white-space:nowrap">' + chu + '</button>';
}
function tdChipTt(k) {
  var t = tdTtCua(k);
  return '<span style="background:' + t.nen + ';color:' + t.chu + ';border-radius:999px;padding:2px 9px;font-size:12px;font-weight:700;white-space:nowrap">' +
    t.ic + ' ' + h(t.k) + '</span>';
}
function tdTheHs(r, i, bayGio) {
  var phu = [h(r.ten_vi_tri || r.vi_tri), h(r.nguon || '')];
  var cach = tdCachDay(r.creation, bayGio);
  phu.push(+r.qua_han ? '<b style="color:#b42318">' + h(cach) + ', chưa ai gọi</b>' : h(cach));
  if (+r.lan_nop > 1) phu.push('<b style="color:#92400e">nộp ' + r.lan_nop + ' lần</b>');
  var dong2 = [];
  if (r.ca_ranh) dong2.push('Ca: ' + h(r.ca_ranh));
  if (r.khu_vuc) dong2.push('Ở ' + h(r.khu_vuc));
  var hen = (TD_CAN_HEN.indexOf(r.trang_thai) >= 0 && r.lich_hen) ?
    '<div style="font-size:13.5px;color:#075985;font-weight:700;margin-top:4px">📅 ' + h(r.trang_thai === 'Làm thử' ? 'Làm thử' : 'Phỏng vấn') + ' lúc ' + h(tdGioNgay(r.lich_hen)) + '</div>' : '';
  var tel = String(r.sdt || '').replace(/[^0-9]/g, '');
  var nut = [];
  if (tel) {
    nut.push('<a href="tel:' + h(tel) + '" data-tdgoi="' + i + '" style="flex:1 1 0;min-width:0;min-height:44px;border-radius:11px;border:1.5px solid #0d9488;' +
      'color:#0d9488;background:#fff;font-size:14px;font-weight:700;display:flex;flex-direction:row;align-items:center;justify-content:center;text-decoration:none">📞 Gọi</a>');
    nut.push('<a href="https://zalo.me/' + h(tel) + '" target="_blank" rel="noopener" data-tdzalo="' + i + '" style="flex:1 1 0;min-width:0;min-height:44px;border-radius:11px;' +
      'border:1.5px solid #0068ff;color:#0068ff;background:#fff;font-size:14px;font-weight:700;display:flex;flex-direction:row;align-items:center;justify-content:center;text-decoration:none">💬 Zalo</a>');
  }
  if (r.trang_thai !== 'Đã nhận việc') nut.push(tdNut('data-tdcn="' + i + '"', 'Cập nhật', 'chinh'));
  if (['Hẹn phỏng vấn', 'Làm thử', 'Đề nghị nhận việc', 'Đã liên hệ'].indexOf(r.trang_thai) >= 0) nut.push(tdNut('data-tdcham="' + i + '"', '📝 Chấm'));
  var ghi = [];
  if (+r.tien_cong_thu > 0) {
    ghi.push('💵 Công làm thử ' + money(r.tien_cong_thu) + (+r.da_tra_cong ? ', đã trả' + (r.tra_cong_boi ? ' (' + r.tra_cong_boi + ')' : '') : ', CHƯA trả'));
  }
  (r.cham || []).forEach(function (c) {
    ghi.push('📝 ' + c.vong + ' · ' + c.nguoi + ': ' + c.ket_luan + ', điểm ' + c.diem_tb + (c.nhan_xet ? '. ' + c.nhan_xet : ''));
  });
  if (r.kinh_nghiem) ghi.push('Kinh nghiệm: ' + r.kinh_nghiem);
  if (r.gioi_thieu) ghi.push('Ứng viên nhắn: ' + r.gioi_thieu);
  if (r.nguoi_gioi_thieu) ghi.push('Giới thiệu bởi: ' + r.nguoi_gioi_thieu);
  if (r.email) ghi.push('Email: ' + r.email);
  if (r.trang_thai === 'Dừng' && r.ly_do_dung) ghi.push('Lý do dừng: ' + r.ly_do_dung);
  if (r.nhat_ky) ghi.push('Nhật ký: ' + String(r.nhat_ky).split('\n').slice(-3).join(' | '));
  var congNut = (r.trang_thai === 'Làm thử' || (+r.tien_cong_thu > 0 && !+r.da_tra_cong)) ?
    '<button type="button" class="btn gh" data-tdcong="' + i + '" style="margin:8px 0 0;min-height:44px;width:100%">💵 ' +
    (+r.tien_cong_thu > 0 ? 'Ghi đã trả công làm thử' : 'Ghi công làm thử') + '</button>' : '';
  var cv = r.lien_ket_cv ? '<a href="' + h(r.lien_ket_cv) + '" target="_blank" rel="noopener" style="display:inline-block;margin-top:6px;font-size:13.5px;color:#0d9488;min-height:24px">📄 Mở CV</a>' : '';
  return '<div class="card" data-tdhs="' + h(r.name) + '" style="padding:12px 13px">' +
    '<div style="display:flex;flex-direction:row;justify-content:space-between;align-items:baseline;gap:8px">' +
    '<span style="font-size:16.5px;font-weight:800;color:#101828;min-width:0;overflow-wrap:anywhere">' + h(r.ho_ten) + '</span>' + tdChipTt(r.trang_thai) + '</div>' +
    '<div style="font-size:13px;color:#475467;margin-top:3px;line-height:1.5">' + phu.filter(Boolean).join(' · ') + '</div>' +
    (dong2.length ? '<div style="font-size:13px;color:#475467">' + dong2.join(' · ') + '</div>' : '') + hen + cv +
    (nut.length ? '<div style="display:flex;flex-direction:row;gap:7px;margin-top:10px">' + nut.join('') + '</div>' : '') + congNut +
    tdKhoiGhi(ghi, i) + '</div>';
}
/* AGENTS 2b.17: khối đọc nằm DƯỚI hàng nút; dài thì thu về một dòng đếm, bấm mới mở. */
function tdKhoiGhi(ghi, i) {
  if (!ghi.length) return '';
  var khung = 'font-size:12.5px;color:#475467;background:#f8fafc;border-radius:9px;padding:7px 9px;margin-top:8px;line-height:1.5;';
  var day = ghi.map(function (g) { return h(g); }).join('<br>');
  if (ghi.length <= 2 && ghi.every(function (g) { return String(g).length <= 56; })) return '<div data-tdghi="' + i + '" style="' + khung + '">' + day + '</div>';
  var dau = String(ghi[0]);
  return '<button type="button" data-tdghimo="' + i + '" aria-expanded="false" style="' + khung +
    'display:block;width:100%;min-height:44px;text-align:left;border:0;cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' +
    '📋 ' + ghi.length + ' mục · ' + h(dau.length > 40 ? dau.slice(0, 40) + '…' : dau) + ' <b style="color:#0d9488">Xem</b></button>' +
    '<div data-tdghi="' + i + '" hidden style="' + khung + 'display:none;white-space:pre-line;word-break:break-word">' + day + '</div>';
}

function tdCongTac(attr, bat) {
  return '<button type="button" role="switch" ' + attr + ' aria-checked="' + (bat ? 'true' : 'false') + '" style="flex:0 0 46px;width:46px;height:28px;' +
    'border-radius:14px;border:0;padding:0;position:relative;cursor:pointer;margin:0;background:' + (bat ? '#0d9488' : '#d0d5dd') + '">' +
    '<span style="position:absolute;top:3px;' + (bat ? 'right:3px' : 'left:3px') + ';width:22px;height:22px;border-radius:50%;background:#fff"></span></button>';
}
function tdTheVt(v, i) {
  var phu = [v.ten_bo_phan, v.noi_lam, v.hinh_thuc, 'cần ' + (v.so_can || 1) + ' người'].filter(Boolean).map(h).join(' · ');
  var mau = +v.khach_thay ? '#166534' : '#475467';
  return '<div class="card" data-tdvt="' + h(v.name) + '" style="padding:12px 13px">' +
    '<div style="display:flex;flex-direction:row;justify-content:space-between;align-items:center;gap:10px">' +
    '<div style="min-width:0;flex:1 1 auto"><div style="font-size:16px;font-weight:800;overflow-wrap:anywhere">' + h(v.tieu_de) + '</div>' +
    '<div style="font-size:13px;color:#475467;margin-top:2px">' + phu + '</div></div>' +
    tdCongTac('data-tdbat="' + i + '" aria-label="Đang tuyển trên web"', +v.dang_tuyen) + '</div>' +
    '<div style="font-size:13px;color:' + mau + ';margin-top:6px">' + (+v.khach_thay ? '🌐 ' : '⏸ ') + h(v.trang_thai_web || '') +
    (v.ket_thuc ? ' · hạn ' + h(v.ket_thuc.split('-').reverse().join('/')) : '') + '</div>' +
    '<div style="display:flex;flex-direction:row;gap:7px;margin-top:10px">' +
    tdNut('data-tdhsvt="' + i + '"', '👥 ' + (v.so_ho_so || 0) + ' hồ sơ', 'goi') + tdNut('data-tdsua="' + i + '"', '✎ Sửa') + '</div></div>';
}

function tdMoSheet(html) {
  var ov = document.createElement('div'); ov.className = 'sh';
  ov.innerHTML = '<div class="shb" style="padding:16px 16px calc(env(safe-area-inset-bottom,0px) + 18px)">' +
    '<div style="width:40px;height:4px;background:#d0d5dd;border-radius:2px;margin:0 auto 8px"></div>' + html + '</div>';
  document.body.appendChild(ov);
  ov.addEventListener('click', function (e) { if (e.target === ov) ov.remove(); });
  return ov;
}
async function tdGoi(method, args, xong) {
  busy(true);
  try {
    await api(method, args);
    busy(false);
    toast(xong, 3200);
    go(scrTuyenDung, true);
    return true;
  } catch (e) {
    busy(false);
    toast(errMsg(e), 5000);
    return false;
  }
}

/* Bảng Cập nhật: chọn trạng thái tiếp theo (chip có dòng giải thích), giờ hẹn
   khi hẹn phỏng vấn hay làm thử, lý do khi dừng, ghi chú. */
function tdSheetCapNhat(r) {
  var chon = r.trang_thai === 'Mới nhận' ? 'Đã liên hệ' : r.trang_thai;
  var ov = tdMoSheet('<div style="font-size:18px;font-weight:700;margin:4px 0 4px">Cập nhật hồ sơ</div>' +
    '<div style="font-size:13.5px;color:#475467;margin-bottom:10px"><b style="color:#101828">' + h(r.ho_ten) + '</b> · ' + h(r.ten_vi_tri || '') + '</div>' +
    '<div data-tdcntt="1" style="display:flex;flex-direction:column;gap:6px"></div>' +
    '<div data-tdhen="1" style="margin-top:12px"><div style="font-size:13.5px;font-weight:700;color:#344054;margin-bottom:6px">Ngày giờ hẹn</div>' +
    '<input class="nt" id="tdLichHen" type="datetime-local" style="height:46px" value="' + h(String(r.lich_hen || '').slice(0, 16).replace(' ', 'T')) + '"></div>' +
    '<div data-tdly="1" style="margin-top:12px"><div style="font-size:13.5px;font-weight:700;color:#344054;margin-bottom:6px">Lý do dừng (bắt buộc)</div>' +
    kmHangChip((tdKq.ly_do_dung || []).map(function (l, k) { return posChipNut('data-tdlymau="' + k + '"', h(l), false, false, '#475467'); }).join('')) +
    '<input class="nt" id="tdLyDo" maxlength="140" style="height:46px;margin-top:8px" placeholder="Bấm một lý do ở trên hoặc tự ghi"></div>' +
    '<div style="font-size:13.5px;font-weight:700;color:#344054;margin:12px 0 6px">Ghi chú (không bắt buộc)</div>' +
    '<textarea class="nt" id="tdGhiChu" rows="2" maxlength="500" placeholder="Ví dụ: hẹn mang CMND, muốn làm ca tối"></textarea>' +
    '<button class="btn" data-tdok="1" style="margin:12px 0 0">Lưu cập nhật</button>' +
    '<button class="btn gh" data-tddong="1" style="margin-top:9px">Để sau</button>');
  function ve() {
    ov.querySelector('[data-tdcntt]').innerHTML = TD_TT.filter(function (t) { return t.k !== 'Mới nhận'; }).map(function (t) {
      var dang = t.k === chon;
      return '<button type="button" data-tdchon="' + h(t.k) + '" aria-pressed="' + (dang ? 'true' : 'false') + '" style="margin:0;min-height:44px;width:100%;text-align:left;' +
        'padding:8px 12px;border-radius:11px;cursor:pointer;border:' + (dang ? '2px solid #0d9488;background:#f0fdfa' : '1.5px solid #e4e7ec;background:#fff') + '">' +
        '<div style="font-size:14.5px;font-weight:700;color:#101828">' + t.ic + ' ' + h(t.k) + '</div>' +
        '<div style="font-size:12.5px;color:#475467">' + h(t.p) + '</div></button>';
    }).join('');
    ov.querySelector('[data-tdhen]').style.display = TD_CAN_HEN.indexOf(chon) >= 0 ? 'block' : 'none';
    ov.querySelector('[data-tdly]').style.display = chon === 'Dừng' ? 'block' : 'none';
  }
  ve();
  ov.addEventListener('click', function (e) {
    var t = e.target.closest('[data-tdchon]');
    if (t) { chon = t.getAttribute('data-tdchon'); ve(); return; }
    t = e.target.closest('[data-tdlymau]');
    if (t) { ov.querySelector('#tdLyDo').value = tdKq.ly_do_dung[+t.getAttribute('data-tdlymau')]; return; }
    if (e.target.closest('[data-tddong]')) { ov.remove(); }
  });
  var ok = ov.querySelector('[data-tdok]');
  ok.onclick = async function () {
    var hen = ov.querySelector('#tdLichHen').value, ly = ov.querySelector('#tdLyDo').value.trim();
    if (TD_CAN_HEN.indexOf(chon) >= 0 && !hen) { toast('Chọn ngày giờ hẹn để ứng viên biết lúc nào tới.', 3500); return; }
    if (chon === 'Dừng' && ly.length < 3) { toast('Chọn lý do dừng.', 3200); return; }
    ok.disabled = true;
    var xong = await tdGoi('vagabond.tuyen_dung.cap_nhat', { name: r.name, trang_thai: chon, lich_hen: hen, ly_do: ly,
      ghi_chu: ov.querySelector('#tdGhiChu').value.trim() }, 'Đã cập nhật hồ sơ ' + r.ho_ten);
    if (xong) ov.remove(); else ok.disabled = false;
  };
}

/* Phiếu chấm: mỗi tiêu chí của vị trí chấm 1 đến 4, kết luận, nhận xét. */
function tdSheetCham(r) {
  var vt = (tdKq.vi_tri || []).filter(function (v) { return v.name === r.vi_tri; })[0] || {};
  var tc = vt.ds_tieu_chi || tdKq.tieu_chi_mac_dinh || [];
  var diem = {}, vong = r.trang_thai === 'Làm thử' ? 'Làm thử' : 'Phỏng vấn', kl = '';
  var hang = tc.map(function (t, k) {
    return '<div style="margin-top:10px"><div style="font-size:13.5px;font-weight:700;color:#344054;margin-bottom:5px">' + h(t) + '</div>' +
      kmHangChip([1, 2, 3, 4].map(function (n) { return posChipNut('data-tdd="' + k + '|' + n + '"', String(n), false, false, '#0d9488'); }).join('')) + '</div>';
  }).join('');
  var ov = tdMoSheet('<div style="font-size:18px;font-weight:700;margin:4px 0 4px">Phiếu chấm</div>' +
    '<div style="font-size:13.5px;color:#475467">' + h(r.ho_ten) + ' · ' + h(r.ten_vi_tri || '') + '. 1 là chưa đạt, 4 là rất tốt.</div>' +
    '<div style="margin-top:10px">' + kmHangChip(['Phỏng vấn', 'Làm thử'].map(function (v) { return posChipNut('data-tdvong="' + v + '"', v, v === vong, false, '#4338ca'); }).join('')) + '</div>' +
    hang +
    '<div style="font-size:13.5px;font-weight:700;color:#344054;margin:12px 0 5px">Kết luận</div>' +
    kmHangChip(['Nên nhận', 'Cân nhắc', 'Không nên nhận'].map(function (v) { return posChipNut('data-tdkl="' + v + '"', v, false, false, '#0d9488'); }).join('')) +
    '<textarea class="nt" id="tdNhanXet" rows="2" maxlength="1000" style="margin-top:10px" placeholder="Nhận xét ngắn, dựa trên việc ứng viên đã làm hoặc đã nói"></textarea>' +
    '<button class="btn" data-tdok="1" style="margin:12px 0 0">Nộp phiếu chấm</button>' +
    '<button class="btn gh" data-tddong="1" style="margin-top:9px">Để sau</button>');
  function toMot(x, on) {
    x.style.background = on ? (x.getAttribute('data-tdvong') ? '#4338ca' : '#0d9488') : '#fff';
    x.style.color = on ? '#fff' : '#374151';
    x.setAttribute('aria-pressed', on ? 'true' : 'false');
  }
  function to(sel, dk) { ov.querySelectorAll(sel).forEach(function (x) { toMot(x, dk(x)); }); }
  ov.addEventListener('click', function (e) {
    var t = e.target.closest('[data-tdd]');
    if (t) {
      var p = t.getAttribute('data-tdd').split('|'); diem[tc[+p[0]]] = +p[1];
      /* Chỉ tô lại hàng của tiêu chí vừa chấm, hàng khác giữ nguyên. */
      ov.querySelectorAll('[data-tdd]').forEach(function (x) {
        if (x.getAttribute('data-tdd').split('|')[0] === p[0]) toMot(x, x === t);
      });
      return;
    }
    t = e.target.closest('[data-tdvong]');
    if (t) { vong = t.getAttribute('data-tdvong'); to('[data-tdvong]', function (x) { return x === t; }); return; }
    t = e.target.closest('[data-tdkl]');
    if (t) { kl = t.getAttribute('data-tdkl'); to('[data-tdkl]', function (x) { return x === t; }); return; }
    if (e.target.closest('[data-tddong]')) ov.remove();
  });
  var ok = ov.querySelector('[data-tdok]');
  ok.onclick = async function () {
    var thieu = tc.filter(function (t) { return !diem[t]; });
    if (thieu.length) { toast('Chấm đủ tiêu chí, còn thiếu: ' + thieu[0], 3500); return; }
    if (!kl) { toast('Chọn kết luận: Nên nhận, Cân nhắc hay Không nên nhận.', 3500); return; }
    ok.disabled = true;
    var xong = await tdGoi('vagabond.tuyen_dung.cham', { name: r.name, vong: vong, diem: JSON.stringify(diem), ket_luan: kl,
      nhan_xet: ov.querySelector('#tdNhanXet').value.trim() }, 'Đã nộp phiếu chấm');
    if (xong) ov.remove(); else ok.disabled = false;
  };
}

/* Công làm thử (anh Việt 30/10/2026: làm thử có trả công). Giờ và tiền gợi ý
   theo vị trí; ghi là đã trả khi đưa tiền thật. */
function tdSheetCong(r) {
  var vt = (tdKq.vi_tri || []).filter(function (v) { return v.name === r.vi_tri; })[0] || {};
  var gio = +r.gio_lam_thu || +vt.gio_lam_thu || 4, tien = +r.tien_cong_thu || +vt.cong_lam_thu || '';
  var ov = tdMoSheet('<div style="font-size:18px;font-weight:700;margin:4px 0 4px">Công làm thử</div>' +
    '<div style="font-size:13.5px;color:#475467;margin-bottom:10px">' + h(r.ho_ten) + ' · ' + h(r.ten_vi_tri || '') + '</div>' +
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">' +
    '<label style="font-size:13.5px;font-weight:700;color:#344054">Số giờ<input class="nt" id="tdGio" inputmode="decimal" style="height:46px;margin-top:5px" value="' + h(gio) + '"></label>' +
    '<label style="font-size:13.5px;font-weight:700;color:#344054">Tiền công (đ)<input class="nt" id="tdTien" inputmode="numeric" style="height:46px;margin-top:5px" value="' + h(tien) + '"></label></div>' +
    '<div style="font-size:12.5px;color:#475467;margin-top:8px">Tiền gợi ý lấy từ vị trí. Trả tại quầy hoặc chuyển khoản rồi bấm Đã trả để không sót.</div>' +
    '<button class="btn" data-tdtra="1" style="margin:12px 0 0">Đã trả công</button>' +
    (+r.tien_cong_thu > 0 ? '' : '<button class="btn gh" data-tdghi="1" style="margin-top:9px">Ghi công, trả sau</button>') +
    '<button class="btn gh" data-tddong="1" style="margin-top:9px">Để sau</button>');
  async function luu(daTra, nut) {
    nut.disabled = true;
    var xong = await tdGoi('vagabond.tuyen_dung.ghi_cong_thu', { name: r.name, gio: ov.querySelector('#tdGio').value,
      tien: ov.querySelector('#tdTien').value, da_tra: daTra ? 1 : 0 }, daTra ? 'Đã ghi trả công làm thử' : 'Đã ghi công làm thử');
    if (xong) ov.remove(); else nut.disabled = false;
  }
  ov.addEventListener('click', function (e) {
    var t = e.target.closest('[data-tdtra]'); if (t) { luu(true, t); return; }
    t = e.target.closest('[data-tdghi]'); if (t) { luu(false, t); return; }
    if (e.target.closest('[data-tddong]')) ov.remove();
  });
}

/* Mã QR dán ở cửa hàng: mở form ứng tuyển, máy ghi nguồn "QR tại cửa hàng". */
async function tdSheetQr() {
  var link = (tdKq && tdKq.link_ung_tuyen) || '';
  var anh = '';
  try { anh = await inQrAnh(link + (link.indexOf('?') >= 0 ? '&' : '?') + 'nguon=qr'); } catch (e) { anh = ''; }
  tdMoSheet('<div style="font-size:18px;font-weight:700;margin:4px 0 6px">Mã QR ứng tuyển</div>' +
    '<div style="font-size:13.5px;color:#475467;line-height:1.55">In mã này dán ở quầy, cửa kính hoặc túi bánh. Ứng viên quét là mở form, hồ sơ ghi nguồn "QR tại cửa hàng".</div>' +
    (anh ? '<div style="text-align:center;margin:12px 0"><img src="' + h(anh) + '" alt="Mã QR ứng tuyển" style="width:220px;height:220px"></div>'
      : '<div style="margin:12px 0;color:#b42318;font-size:13.5px">Chưa vẽ được mã QR, dùng đường dẫn bên dưới.</div>') +
    '<div style="font-size:13px;word-break:break-all;background:#f8fafc;border-radius:9px;padding:8px 10px">' + h(link + '?nguon=qr') + '</div>');
}

async function scrTuyenDung() {
  var tieuDe = 'Tuyển dụng';
  if (!coQuyenTuyenDung()) {
    frame(tieuDe, '<div class="emp"><div class="e1">🔒</div><div>Phân hệ Tuyển dụng chỉ mở cho quản lý các bộ phận và giám đốc.</div></div>');
    return;
  }
  frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc hồ sơ ứng tuyển...</div></div>');
  var kq;
  try { kq = await api('vagabond.tuyen_dung.tong_quan', {}); }
  catch (e) {
    frame(tieuDe, '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e)) + ' Tải lại màn để thử lại.</div></div>');
    return;
  }
  tdKq = kq;
  var rows = kq.rows || [], vts = kq.vi_tri || [];
  var html = '<div class="card" style="padding:10px 12px">' + kmHangChip(
    posChipNut('data-tdtab="hs"', '👥 Hồ sơ ứng viên ' + rows.length, tdTab === 'hs', false, '#0d9488') +
    posChipNut('data-tdtab="vt"', '📌 Vị trí ' + vts.filter(function (v) { return +v.dang_tuyen; }).length + '/' + vts.length, tdTab === 'vt', false, '#0d9488')) + '</div>';
  var than;
  if (tdTab === 'vt') {
    html += '<div style="display:flex;flex-direction:row;gap:7px;margin:0 14px 8px">' +
      tdNut('data-tdthemvt="1"', '+ Thêm vị trí', 'chinh') + tdNut('data-tdqr="1"', '🔳 Mã QR cửa hàng') + '</div>';
    html += vts.length ? vts.map(tdTheVt).join('') :
      '<div class="card"><div class="emp" style="padding:24px"><div class="e1">📌</div><div>Chưa có vị trí nào. Bấm Thêm vị trí, bật Đang tuyển là web hiện ngay.</div></div></div>';
    html += '<div style="font-size:12px;color:#98a2b3;margin:10px 16px 18px;line-height:1.5">Mục Tuyển dụng trên web lấy thẳng từ đây. Bật Đang tuyển là khách thấy vị trí và nộp hồ sơ được; tắt hoặc qua hạn là web ẩn ngay.</div>';
    than = frame(tieuDe, html);
  } else {
    var bayGio = kq.bay_gio || '';
    var loc = { tim: tdTim, the: tdLoc, tt: tdTt, vt: tdVt };
    var demTt = {}, demVt = {};
    rows.forEach(function (r) { demTt[r.trang_thai] = (demTt[r.trang_thai] || 0) + 1; demVt[r.vi_tri] = (demVt[r.vi_tri] || 0) + 1; });
    var cc = {
      ma: 'td',
      ho: [
        { k: 'tt', chon: tdTt, tatCa: 'Mọi trạng thái', mau: '#0d9488', dem: Object.assign({ tat_ca: rows.length }, demTt),
          ds: TD_TT.map(function (t) { return { k: t.k, ten: t.k, ic: t.ic }; }) },
        { k: 'vt', chon: tdVt, tatCa: 'Mọi vị trí', mau: '#4338ca', dem: Object.assign({ tat_ca: rows.length }, demVt),
          ds: vts.map(function (v) { return { k: v.name, ten: v.tieu_de }; }) },
      ],
      tim: { gt: tdTim, goiY: '🔎 Tìm tên, số điện thoại' },
    };
    html += tdTomTatHtml(kq.tom_tat || {});
    html += dsCongCu(cc);
    html += '<div style="display:flex;flex-direction:row;gap:7px;margin:0 14px 8px">' + tdNut('data-tdthemhs="1"', '+ Thêm hồ sơ (TopCV, người quen...)', 'goi') + '</div>';
    var ds = tdLocHs(rows, loc, kq.hom_nay);
    if (tdTim || tdLoc || tdTt || tdVt) {
      html += '<div data-tdloc="1" style="display:flex;flex-direction:row;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;margin:0 14px 6px;' +
        'padding:8px 10px;border-radius:8px;background:#fffaeb;font-size:13px;color:#101828"><span>Đang lọc: ' + ds.length + ' hồ sơ. Hồ sơ khác đang ẩn.</span>' +
        '<button type="button" data-tdbo="1" style="margin:0;min-height:36px;width:auto;padding:0 12px;border-radius:999px;border:1.5px solid #d0d5dd;background:#fff;cursor:pointer;font-weight:700">✕ Bỏ lọc</button></div>';
    }
    if (!ds.length) {
      html += '<div class="card"><div class="emp" style="padding:24px"><div class="e1">🧑‍💼</div><div>' +
        (rows.length ? 'Không có hồ sơ nào khớp bộ lọc. Bấm Bỏ lọc để xem hết.' :
          vts.some(function (v) { return +v.khach_thay; }) ? 'Chưa có hồ sơ nào. Hồ sơ nộp trên web hiện ở đây ngay.' :
            'Chưa có hồ sơ nào. Mở thẻ Vị trí, thêm vị trí và bật Đang tuyển để web nhận hồ sơ.') + '</div></div></div>';
    } else {
      html += ds.map(function (r) { return tdTheHs(r, rows.indexOf(r), bayGio); }).join('');
    }
    html += '<div style="font-size:12px;color:#98a2b3;margin:10px 16px 18px;line-height:1.5">Hồ sơ không được nhận tự xoá thông tin cá nhân khi hết ' +
      (+kq.thang_luu || 12) + ' tháng lưu mà ứng viên đã đồng ý.</div>';
    than = frame(tieuDe, html);
    dsCongCuNoi(than, cc, function (ho, k) {
      if (ho === 'tt') { tdTt = k; tdLoc = ''; }
      else if (ho === 'vt') tdVt = k;
      else if (ho === 'tim') tdTim = k;
      go(scrTuyenDung, true);
    });
  }
  than.addEventListener('click', function (e) {
    var t = e.target.closest('[data-tdtab]');
    if (t) { tdTab = t.getAttribute('data-tdtab'); go(scrTuyenDung, true); return; }
    t = e.target.closest('[data-tdthe]');
    if (t) { var k = t.getAttribute('data-tdthe'); tdLoc = tdLoc === k ? '' : k; tdTt = ''; tdTim = ''; go(scrTuyenDung, true); return; }
    if (e.target.closest('[data-tdbo]')) { tdLoc = ''; tdTt = ''; tdVt = ''; tdTim = ''; go(scrTuyenDung, true); return; }
    t = e.target.closest('[data-tdghimo]');
    if (t) {
      var mo = t.getAttribute('aria-expanded') !== 'true';
      var khoi = than.querySelectorAll('[data-tdghi="' + t.getAttribute('data-tdghimo') + '"]')[0];
      t.setAttribute('aria-expanded', mo ? 'true' : 'false');
      if (khoi) { khoi.style.display = mo ? 'block' : 'none'; if (mo) khoi.removeAttribute('hidden'); else khoi.setAttribute('hidden', ''); }
      return;
    }
    t = e.target.closest('[data-tdcn]'); if (t) { tdSheetCapNhat(rows[+t.getAttribute('data-tdcn')]); return; }
    t = e.target.closest('[data-tdcham]'); if (t) { tdSheetCham(rows[+t.getAttribute('data-tdcham')]); return; }
    t = e.target.closest('[data-tdcong]'); if (t) { tdSheetCong(rows[+t.getAttribute('data-tdcong')]); return; }
    if (e.target.closest('[data-tdthemhs]')) { go(scrTdThemHs); return; }
    if (e.target.closest('[data-tdthemvt]')) { go(function () { return scrTdViTri(''); }); return; }
    if (e.target.closest('[data-tdqr]')) { tdSheetQr(); return; }
    t = e.target.closest('[data-tdsua]'); if (t) { var vs = vts[+t.getAttribute('data-tdsua')]; go(function () { return scrTdViTri(vs.name); }); return; }
    t = e.target.closest('[data-tdhsvt]');
    if (t) { tdVt = vts[+t.getAttribute('data-tdhsvt')].name; tdTt = ''; tdLoc = ''; tdTim = ''; tdTab = 'hs'; go(scrTuyenDung, true); return; }
    t = e.target.closest('[data-tdbat]');
    if (t) {
      var v = vts[+t.getAttribute('data-tdbat')], bat = !+v.dang_tuyen;
      confirmSheet(bat ? 'Bật Đang tuyển?' : 'Tắt Đang tuyển?', v.tieu_de + '\n' + (bat ? 'Web hiện vị trí này và nhận hồ sơ ngay.' : 'Web ẩn vị trí này ngay, không nhận hồ sơ mới.'),
        bat ? 'Bật, hiện trên web' : 'Tắt, ẩn khỏi web', !bat).then(function (dong) {
        if (dong) tdGoi('vagabond.tuyen_dung.bat_tat_vi_tri', { name: v.name, bat: bat ? 1 : 0 }, bat ? 'Đã bật, web đang hiện ' + v.tieu_de : 'Đã tắt, web đã ẩn ' + v.tieu_de);
      });
    }
  });
}

/* ---------- Thêm hoặc sửa vị trí (màn lập phiếu, có bản nháp tự lưu ở 48) ---------- */
var tdVtTay = null;
var tdVtKhoiPhuc = null;
function tdVtMoi(v) {
  v = v || {};
  return {
    name: v.name || '', tieu_de: v.tieu_de || '', bo_phan: v.bo_phan || '', ten_bo_phan: v.ten_bo_phan || '', noi_lam: v.noi_lam || '',
    hinh_thuc: v.hinh_thuc || 'Toàn thời gian', so_can: v.so_can || 1, dang_tuyen: v.name ? +v.dang_tuyen : 1,
    ket_thuc: v.ket_thuc || '', noi_dung: v.noi_dung || '', yeu_cau: v.yeu_cau || '', muc_luong: v.muc_luong || '',
    tieu_chi: v.tieu_chi || '', gio_lam_thu: v.gio_lam_thu != null ? v.gio_lam_thu : 4, cong_lam_thu: v.cong_lam_thu || ''
  };
}
async function scrTdViTri(name) {
  var tieuDe = name ? 'Sửa vị trí' : 'Thêm vị trí';
  if (!tdKq) { try { tdKq = await api('vagabond.tuyen_dung.tong_quan', {}); } catch (e) { frame(tieuDe, '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e)) + '</div></div>'); return; } }
  var goc = (tdKq.vi_tri || []).filter(function (v) { return v.name === name; })[0];
  var s = tdVtMoi(goc);
  if (tdVtKhoiPhuc && (tdVtKhoiPhuc.name || '') === (name || '')) s = Object.assign(s, tdVtKhoiPhuc);
  tdVtKhoiPhuc = null;
  tdVtTay = s;
  var o = function (nhan, id, gt, them, goiY) {
    return '<div style="font-size:13.5px;font-weight:700;color:#344054;margin:12px 0 5px">' + nhan + '</div>' +
      (them === 'nhieu' ? '<textarea class="nt" id="' + id + '" rows="3">' + h(gt) + '</textarea>' :
        '<input class="nt" id="' + id + '" style="height:46px" value="' + h(gt) + '"' + (them || '') + '>') +
      (goiY ? '<div style="font-size:12.5px;color:#475467;margin-top:4px">' + goiY + '</div>' : '');
  };
  var chipHt = (tdKq.hinh_thuc || []).map(function (x) { return posChipNut('data-tdht="' + h(x) + '"', h(x), s.hinh_thuc === x, false, '#0d9488'); }).join('');
  var chipNl = (tdKq.noi_lam || []).map(function (x) { return posChipNut('data-tdnl="' + h(x) + '"', h(x), s.noi_lam === x, false, '#4338ca'); }).join('');
  var html = '<div class="card" style="padding:12px 13px">' +
    '<div style="display:flex;flex-direction:row;align-items:center;gap:10px;justify-content:space-between">' +
    '<div><div style="font-size:15px;font-weight:700">Đang tuyển trên web</div><div style="font-size:12.5px;color:#475467">Bật là web hiện vị trí và nhận hồ sơ ngay sau khi lưu.</div></div>' +
    tdCongTac('data-tdvtbat="1" aria-label="Đang tuyển trên web"', +s.dang_tuyen) + '</div>' +
    o('Tên vị trí', 'tdTen', s.tieu_de, ' maxlength="140" placeholder="Ví dụ: Thu ngân ca tối, Phụ bếp Pastry"') +
    '<div style="font-size:13.5px;font-weight:700;color:#344054;margin:12px 0 5px">Bộ phận</div>' +
    '<button type="button" data-tdbp="1" style="margin:0;min-height:46px;width:100%;text-align:left;padding:8px 12px;border-radius:10px;border:1.5px solid #d0d5dd;background:#fff;cursor:pointer;font-size:15px">' +
    (s.ten_bo_phan ? h(s.ten_bo_phan) : '<span style="color:#98a2b3">Chọn bộ phận</span>') + ' <span style="float:right;color:#98a2b3">›</span></button>' +
    '<div style="font-size:13.5px;font-weight:700;color:#344054;margin:12px 0 5px">Nơi làm</div>' + kmHangChip(chipNl) +
    '<input class="nt" id="tdNoiLam" style="height:46px;margin-top:8px" maxlength="140" value="' + h(s.noi_lam) + '" placeholder="Hoặc gõ nơi làm khác">' +
    '<div style="font-size:13.5px;font-weight:700;color:#344054;margin:12px 0 5px">Hình thức</div>' + kmHangChip(chipHt) +
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">' +
    '<div>' + o('Số người cần', 'tdSoCan', s.so_can, ' inputmode="numeric"') + '</div>' +
    '<div>' + o('Hạn nhận hồ sơ', 'tdKetThuc', s.ket_thuc, ' type="date"') + '</div></div>' +
    '<div style="font-size:12.5px;color:#475467;margin-top:4px">Qua hạn web tự ẩn. Để trống là nhận tới khi đủ người.</div></div>' +
    '<div class="card" style="padding:12px 13px"><div style="font-size:15px;font-weight:800">Nội dung trên web</div>' +
    o('Mô tả công việc', 'tdNoiDung', s.noi_dung, 'nhieu', 'Một hai câu nói việc chính.') +
    o('Yêu cầu và quyền lợi', 'tdYeuCau', s.yeu_cau, 'nhieu', 'Mỗi dòng một ý, web hiện thành danh sách.') +
    o('Mức lương (không bắt buộc)', 'tdLuong', s.muc_luong, ' maxlength="140" placeholder="Ví dụ: 25.000 đ/giờ, thưởng doanh số"') + '</div>' +
    '<div class="card" style="padding:12px 13px"><div style="font-size:15px;font-weight:800">Phỏng vấn và làm thử</div>' +
    o('Tiêu chí chấm', 'tdTieuChi', s.tieu_chi, 'nhieu', 'Mỗi dòng một tiêu chí, tối đa 8. Để trống thì dùng: ' + h((tdKq.tieu_chi_mac_dinh || []).join(', ')) + '.') +
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">' +
    '<div>' + o('Số giờ làm thử', 'tdGioThu', s.gio_lam_thu, ' inputmode="decimal"') + '</div>' +
    '<div>' + o('Công làm thử (đ)', 'tdCongThu', s.cong_lam_thu, ' inputmode="numeric" placeholder="Ví dụ 100000"') + '</div></div>' +
    '<div style="font-size:12.5px;color:#475467;margin-top:4px">Buổi làm thử có trả công. Số này gợi ý sẵn khi ghi công cho ứng viên.</div></div>';
  var than = frame(tieuDe, html, { footer: '<button class="btn" id="tdLuuVt" style="margin:0">' + (name ? 'Lưu vị trí' : 'Tạo vị trí') + '</button>' });
  var ban = { tdTen: 'tieu_de', tdNoiLam: 'noi_lam', tdSoCan: 'so_can', tdKetThuc: 'ket_thuc', tdNoiDung: 'noi_dung', tdYeuCau: 'yeu_cau',
    tdLuong: 'muc_luong', tdTieuChi: 'tieu_chi', tdGioThu: 'gio_lam_thu', tdCongThu: 'cong_lam_thu' };
  Object.keys(ban).forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.addEventListener('input', function () { s[ban[id]] = el.value; });
  });
  than.addEventListener('click', function (e) {
    var t = e.target.closest('[data-tdht]');
    if (t) { s.hinh_thuc = t.getAttribute('data-tdht'); go(function () { tdVtKhoiPhuc = s; return scrTdViTri(name); }, true); return; }
    t = e.target.closest('[data-tdnl]');
    if (t) { s.noi_lam = t.getAttribute('data-tdnl'); var nl = document.getElementById('tdNoiLam'); if (nl) nl.value = s.noi_lam; go(function () { tdVtKhoiPhuc = s; return scrTdViTri(name); }, true); return; }
    if (e.target.closest('[data-tdvtbat]')) { s.dang_tuyen = +s.dang_tuyen ? 0 : 1; go(function () { tdVtKhoiPhuc = s; return scrTdViTri(name); }, true); return; }
    if (e.target.closest('[data-tdbp]')) {
      sheet('Bộ phận', (tdKq.bo_phan || []).map(function (b) { return { label: b.ten, value: b.k }; }), s.bo_phan, function (it) {
        s.bo_phan = it.value; s.ten_bo_phan = it.label; go(function () { tdVtKhoiPhuc = s; return scrTdViTri(name); }, true);
      }, true);
    }
  });
  var nut = document.getElementById('tdLuuVt');
  if (nut) nut.onclick = async function () {
    if (String(s.tieu_de || '').trim().length < 3) { toast('Điền tên vị trí.', 3000); return; }
    nut.disabled = true; busy(true);
    try {
      await api('vagabond.tuyen_dung.luu_vi_tri', { du_lieu: JSON.stringify(s), name: name || '' });
      busy(false);
      toast(+s.dang_tuyen ? 'Đã lưu, web đang hiện vị trí này' : 'Đã lưu, vị trí đang tắt trên web', 3200);
      tdTab = 'vt';
      back();
    } catch (e) { busy(false); nut.disabled = false; toast(errMsg(e), 5000); }
  };
}

/* ---------- Thêm hồ sơ tay: TopCV, trang việc làm khác, người quen, đến trực tiếp ---------- */
var tdHsTay = null;
var tdHsKhoiPhuc = null;
async function scrTdThemHs() {
  var tieuDe = 'Thêm hồ sơ';
  if (!tdKq) { try { tdKq = await api('vagabond.tuyen_dung.tong_quan', {}); } catch (e) { frame(tieuDe, '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e)) + '</div></div>'); return; } }
  var vts = tdKq.vi_tri || [];
  var s = { vi_tri: tdVt || (vts[0] && vts[0].name) || '', ho_ten: '', sdt: '', email: '', khu_vuc: '', ca_ranh: [], kinh_nghiem: '',
    gioi_thieu: '', lien_ket_cv: '', nguoi_gioi_thieu: '', nguon: 'TopCV', dong_y: 0 };
  if (tdHsKhoiPhuc) s = Object.assign(s, tdHsKhoiPhuc);
  tdHsKhoiPhuc = null;
  tdHsTay = s;
  if (!vts.length) {
    frame(tieuDe, '<div class="emp"><div class="e1">📌</div><div>Chưa có vị trí nào. Thêm vị trí trước rồi mới thêm hồ sơ.</div></div>');
    return;
  }
  var o = function (nhan, id, gt, them) {
    return '<div style="font-size:13.5px;font-weight:700;color:#344054;margin:12px 0 5px">' + nhan + '</div>' +
      (them === 'nhieu' ? '<textarea class="nt" id="' + id + '" rows="2">' + h(gt) + '</textarea>' :
        '<input class="nt" id="' + id + '" style="height:46px" value="' + h(gt) + '"' + (them || '') + '>');
  };
  var html = '<div class="card" style="padding:12px 13px">' +
    '<div style="font-size:13.5px;font-weight:700;color:#344054;margin:2px 0 5px">Vị trí</div>' +
    kmHangChip(vts.map(function (v) { return posChipNut('data-tdhsvt2="' + h(v.name) + '"', h(v.tieu_de), s.vi_tri === v.name, false, '#4338ca'); }).join('')) +
    '<div style="font-size:13.5px;font-weight:700;color:#344054;margin:12px 0 5px">Nguồn</div>' +
    kmHangChip((tdKq.nguon || []).map(function (x) { return posChipNut('data-tdng="' + h(x) + '"', h(x), s.nguon === x, false, '#0d9488'); }).join('')) +
    o('Họ tên', 'tdHsTen', s.ho_ten, ' maxlength="120" autocomplete="off"') +
    o('Số điện thoại', 'tdHsSdt', s.sdt, ' type="tel" inputmode="tel"') +
    '<div style="font-size:13.5px;font-weight:700;color:#344054;margin:12px 0 5px">Ca có thể làm</div>' +
    kmHangChip((tdKq.ca_ranh || []).map(function (x) { return posChipNut('data-tdca="' + h(x) + '"', h(x), s.ca_ranh.indexOf(x) >= 0, false, '#0d9488'); }).join('')) +
    o('Đang ở khu vực', 'tdHsKv', s.khu_vuc, ' maxlength="120"') +
    o('Kinh nghiệm', 'tdHsKn', s.kinh_nghiem, 'nhieu') +
    o('Đường dẫn CV (TopCV, Drive...)', 'tdHsCv', s.lien_ket_cv, ' maxlength="500" placeholder="https://"') +
    o('Người giới thiệu (nếu có)', 'tdHsGt', s.nguoi_gioi_thieu, ' maxlength="120"') +
    '<div style="display:flex;flex-direction:row;align-items:flex-start;gap:10px;margin-top:14px">' +
    tdCongTac('data-tddy="1" aria-label="Ứng viên đã đồng ý lưu hồ sơ"', +s.dong_y) +
    '<div style="font-size:13px;color:#344054;line-height:1.5">Ứng viên đã đồng ý: <i>' + h(tdKq.cau_dong_y || '') + '</i></div></div></div>';
  var than = frame(tieuDe, html, { footer: '<button class="btn" id="tdLuuHs" style="margin:0">Lưu hồ sơ</button>' });
  var ban = { tdHsTen: 'ho_ten', tdHsSdt: 'sdt', tdHsKv: 'khu_vuc', tdHsKn: 'kinh_nghiem', tdHsCv: 'lien_ket_cv', tdHsGt: 'nguoi_gioi_thieu' };
  Object.keys(ban).forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.addEventListener('input', function () { s[ban[id]] = el.value; });
  });
  var veLai = function () { go(function () { tdHsKhoiPhuc = s; return scrTdThemHs(); }, true); };
  than.addEventListener('click', function (e) {
    var t = e.target.closest('[data-tdhsvt2]'); if (t) { s.vi_tri = t.getAttribute('data-tdhsvt2'); veLai(); return; }
    t = e.target.closest('[data-tdng]'); if (t) { s.nguon = t.getAttribute('data-tdng'); veLai(); return; }
    t = e.target.closest('[data-tdca]');
    if (t) { var c = t.getAttribute('data-tdca'); s.ca_ranh = s.ca_ranh.indexOf(c) >= 0 ? s.ca_ranh.filter(function (x) { return x !== c; }) : s.ca_ranh.concat([c]); veLai(); return; }
    if (e.target.closest('[data-tddy]')) { s.dong_y = +s.dong_y ? 0 : 1; veLai(); }
  });
  var nut = document.getElementById('tdLuuHs');
  if (nut) nut.onclick = async function () {
    if (!+s.dong_y) { toast('Hỏi ứng viên đã đồng ý lưu hồ sơ chưa, rồi bật ô xác nhận.', 4000); return; }
    nut.disabled = true; busy(true);
    try {
      await api('vagabond.tuyen_dung.them_ho_so', { du_lieu: JSON.stringify(s) });
      busy(false);
      toast('Đã thêm hồ sơ ' + s.ho_ten, 3000);
      tdTab = 'hs';
      back();
    } catch (e) { busy(false); nut.disabled = false; toast(errMsg(e), 5000); }
  };
}

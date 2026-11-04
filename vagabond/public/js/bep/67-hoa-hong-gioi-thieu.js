/* ---------------- Hoa hồng giới thiệu (v638)

   Anh Việt duyệt 04/11/2026: khách gõ số điện thoại của nhân viên đã mời mình
   vào ô Mã giới thiệu (đặt bánh web, gọi món tại bàn). Hoá đơn ghi sổ xong thì
   nhân viên được hoa hồng, cuối tháng cộng vào phiếu KPI tháng.

   Một màn, hai chế độ:
   - Của tôi: ai cũng mở được, thấy từng đơn của mình trong tháng (mã đơn, loại,
     tiền hàng, hoa hồng, trạng thái) và dòng tạm tính tháng.
   - Toàn tiệm: quản lý, kế toán, giám đốc. Bảng theo nhân viên, nút "Đưa vào
     phiếu KPI tháng" (bấm lại không cộng hai lần, máy chủ ghi đè), "Xuất Excel"
     qua công cụ xuất dùng chung, và đổi người giới thiệu của một đơn (chỉ quản
     lý, máy ghi ai đổi, lúc nào).
   Mọi con số do máy chủ tính (gioi_thieu.py), màn chỉ lọc và bày ra. */
var HHGT = { ky: '', che: 'toi', tt: '', tim: '', mo: '', kq: null, tiem: null };

/* Ba tháng gần nhất cho hàng chip tháng. PHÉP THUẦN. homNay dạng YYYY-MM-DD. */
function hhgtCacKy(homNay) {
  var n = +String(homNay).slice(0, 4), t = +String(homNay).slice(5, 7), ra = [];
  for (var i = 0; i < 3; i++) {
    ra.push({ k: n + '-' + (t < 10 ? '0' : '') + t, ten: i === 0 ? 'Tháng này' : (i === 1 ? 'Tháng trước' : 'Tháng ' + t + '/' + n) });
    t -= 1; if (t < 1) { t = 12; n -= 1; }
  }
  return ra;
}
/* Nhóm trạng thái cho chip: Đã hoàn tiền đứng chung với Đơn huỷ. PHÉP THUẦN. */
function hhgtNhom(tt) { return tt === 'hoan' ? 'huy' : tt; }
function hhgtLoc(rows, tt, tim, nguoi) {
  return (rows || []).filter(function (r) {
    if (tt && hhgtNhom(r.tt) !== tt) return false;
    if (nguoi && r.nguoi !== nguoi) return false;
    if (tim && !vgbKhop([r.hien, r.ten_nguoi, r.nhan_loai], tim)) return false;
    return true;
  });
}
function hhgtDem(rows) {
  var d = { tat_ca: (rows || []).length, ghi_so: 0, cho: 0, huy: 0 };
  (rows || []).forEach(function (r) { d[hhgtNhom(r.tt)] = (d[hhgtNhom(r.tt)] || 0) + 1; });
  return d;
}
function hhgtNgay(s) { s = String(s || ''); return s.length >= 10 ? s.slice(8, 10) + '/' + s.slice(5, 7) : s; }
var HHGT_MAU = { ghi_so: ['#ecfdf3', '#067647'], cho: ['#fffaeb', '#b54708'], huy: ['#f2f4f7', '#475467'], hoan: ['#f2f4f7', '#475467'] };
function hhgtChipTt(r) {
  var m = HHGT_MAU[r.tt] || HHGT_MAU.huy;
  return '<span data-hhgttt="' + h(r.tt) + '" style="display:inline-block;font-size:12.5px;font-weight:700;border-radius:999px;padding:3px 9px;background:' +
    m[0] + ';color:' + m[1] + '">' + h(r.nhan_tt || '') + '</span>';
}

async function scrHhgt() {
  var td = 'Hoa hồng giới thiệu';
  if (!HHGT.ky) HHGT.ky = hhgtCacKy(today())[0].k;
  frame(td, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc hoa hồng giới thiệu...</div></div>');
  try {
    if (HHGT.che === 'tiem') HHGT.tiem = await api('vagabond.gioi_thieu.toan_tiem', { ky: HHGT.ky });
    else HHGT.kq = await api('vagabond.gioi_thieu.cua_toi', { ky: HHGT.ky });
  } catch (e) {
    frame(td, '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e) || 'Chưa đọc được hoa hồng. Kiểm mạng rồi mở lại màn này.') + '</div></div>');
    return;
  }
  hhgtVe();
}

function hhgtDongDon(r, doiDuoc) {
  return '<div data-hhgtdon="' + h(r.ma) + '" style="display:flex;flex-direction:row;align-items:center;gap:10px;padding:10px 0;border-top:1px solid #f2f4f7;min-height:44px">' +
    '<div style="flex:1;min-width:0"><div style="font-size:14px;font-weight:700;color:#101828;overflow-wrap:anywhere">' + h(r.hien) + '</div>' +
    '<div style="font-size:12.5px;color:#667085;line-height:1.5">' + h(r.nhan_loai) + ' · ' + hhgtNgay(r.ngay) + ' · tiền hàng ' + money(r.tien_hang) + ' đ · ' + (+r.pt || 0) + '%' +
    (HHGT.che === 'tiem' && r.ten_nguoi ? ' · ' + h(r.ten_nguoi) : '') + '</div>' +
    (r.ghi_chu ? '<div style="font-size:12.5px;color:#b54708">' + h(r.ghi_chu) + '</div>' : '') +
    (r.doi_boi ? '<div style="font-size:12.5px;color:#98a2b3">Quản lý đổi người lúc ' + h(hhgtNgay(r.doi_luc) + String(r.doi_luc || '').slice(10)) + '</div>' : '') + '</div>' +
    '<div style="flex:0 0 auto;text-align:right"><div style="font-size:14.5px;font-weight:800;color:#101828" data-hhgthh="' + (r.hoa_hong || 0) + '">' + money(r.hoa_hong) + ' đ</div>' + hhgtChipTt(r) + '</div>' +
    (doiDuoc && r.tt !== 'huy' && r.tt !== 'hoan' ? '<button class="btn gh" data-hhgtdoi="' + h(r.ma) + '" style="flex:0 0 auto;width:auto;margin:0;min-height:44px;padding:0 12px">Đổi</button>' : '') +
    '</div>';
}

function hhgtVe() {
  var tiem = HHGT.che === 'tiem', kq = (tiem ? HHGT.tiem : HHGT.kq) || {};
  var rows = kq.ds || [], tong = kq.tong || {}, html = '';
  var xemTiem = tiem || +((HHGT.kq || {}).xem_toan_tiem) === 1;
  var hang = [kmHangChip(hhgtCacKy(today()).map(function (x) {
    return posChipNut('data-hhgtky="' + h(x.k) + '"', h(x.ten), HHGT.ky === x.k, false, '#b45309');
  }).join(''))];
  if (xemTiem) {
    hang.unshift(kmHangChip(posChipNut('data-hhgtche="toi"', 'Của tôi', !tiem, false, '#0d9488') +
      posChipNut('data-hhgtche="tiem"', 'Toàn tiệm', tiem, false, '#0d9488')));
  }
  html += '<div class="card" style="padding:10px 12px;display:flex;flex-direction:column;gap:9px">' + hang.join('') + '</div>';
  if (+kq.bat === 0) {
    html += '<div style="font-size:12.5px;color:#92400e;margin:2px 16px 8px;line-height:1.5">Hoa hồng giới thiệu đang tắt trong Cài đặt: ô Mã giới thiệu đã ẩn khỏi web. Đơn nhận trước lúc tắt vẫn được tính.</div>';
  }
  var gs = tong.ghi_so || {}, ch = tong.cho || {}, hu = tong.huy || {};
  html += '<div class="card" data-hhgttong="1" style="padding:12px 14px;background:#f0fdfa;border:1.5px solid #99f6e4">' +
    '<div style="font-size:12.5px;color:#0f766e;font-weight:700">TẠM TÍNH ' + h(String(HHGT.ky).slice(5, 7) + '/' + String(HHGT.ky).slice(0, 4)) + (tiem ? ' · TOÀN TIỆM' : '') + '</div>' +
    '<div style="display:flex;flex-direction:row;justify-content:space-between;font-size:14px;padding:6px 0 2px"><span>Đã ghi sổ · ' + (gs.so_don || 0) + ' đơn</span>' +
    '<b data-hhgtghiso="' + (gs.hoa_hong || 0) + '" style="color:#0f766e">' + money(gs.hoa_hong) + ' đ</b></div>' +
    '<div style="display:flex;flex-direction:row;justify-content:space-between;font-size:13.5px;color:#b54708;padding:2px 0"><span>Đang chờ ghi sổ · ' + (ch.so_don || 0) + ' đơn</span>' +
    '<span data-hhgtcho="' + (ch.hoa_hong || 0) + '">' + money(ch.hoa_hong) + ' đ</span></div>' +
    (hu.so_don ? '<div style="font-size:12.5px;color:#667085;padding-top:2px">' + hu.so_don + ' đơn huỷ hoặc hoàn tiền, không tính hoa hồng.</div>' : '') +
    '<div style="font-size:12.5px;color:#475467;line-height:1.5;margin-top:6px">Chỉ đơn đã ghi sổ mới thành tiền. Số đang chờ là tạm tính, đổi theo hoá đơn khi ghi sổ.</div></div>';

  if (tiem) {
    var bang = kq.bang || [];
    html += '<div class="sec">Theo nhân viên · ' + bang.length + '</div><div class="card" style="padding:2px 12px">' +
      (bang.length ? bang.map(function (o) {
        var mo = HHGT.mo === o.nguoi;
        return '<div data-hhgtnv="' + h(o.nguoi) + '" style="display:flex;flex-direction:row;align-items:center;gap:10px;padding:11px 0;border-top:1px solid #f2f4f7;min-height:44px;cursor:pointer">' +
          '<div style="flex:1;min-width:0"><div style="font-size:14.5px;font-weight:700">' + h(o.ten_nguoi || o.nguoi) + '</div>' +
          '<div style="font-size:12.5px;color:#667085">' + o.so_don + ' đơn đã ghi sổ · tiền hàng ' + money(o.tien_hang) + ' đ' + (o.so_cho ? ' · ' + o.so_cho + ' đơn chờ' : '') + '</div></div>' +
          '<div style="text-align:right"><div style="font-size:15px;font-weight:800;color:#0f766e" data-hhgtnvhh="' + o.hoa_hong + '">' + money(o.hoa_hong) + ' đ</div>' +
          (o.hoa_hong_cho ? '<div style="font-size:12.5px;color:#b54708">+ ' + money(o.hoa_hong_cho) + ' đ chờ</div>' : '') + '</div>' +
          '<span style="color:#98a2b3">' + (mo ? '▾' : '›') + '</span></div>' +
          (mo ? '<div data-hhgtmo="' + h(o.nguoi) + '" style="padding:0 0 6px 8px">' + hhgtLoc(rows, '', '', o.nguoi).map(function (r) { return hhgtDongDon(r, +kq.doi_duoc === 1); }).join('') + '</div>' : '');
      }).join('') : '<div style="padding:18px 0;color:#667085;text-align:center">Tháng này chưa có đơn nào có người giới thiệu.</div>') + '</div>';
  } else {
    var dem = hhgtDem(rows), loc = hhgtLoc(rows, HHGT.tt, HHGT.tim);
    var chip = function (k, chu) { return posChipNut('data-hhgttt-chon="' + k + '"', chu + (dem[k || 'tat_ca'] ? ' · ' + dem[k || 'tat_ca'] : ''), HHGT.tt === k, false, '#4338ca'); };
    html += '<div class="card" style="padding:10px 12px;display:flex;flex-direction:column;gap:9px">' +
      kmHangChip(chip('', 'Mọi đơn') + chip('ghi_so', 'Đã ghi sổ') + chip('cho', 'Chờ') + chip('huy', 'Đơn huỷ')) +
      '<input class="tin" id="hhgtTim" type="search" placeholder="🔎 Tìm mã đơn" value="' + h(HHGT.tim) + '" style="width:100%;margin:0;height:44px"></div>';
    html += '<div class="card" style="padding:2px 12px">' + (loc.length ? loc.map(function (r) { return hhgtDongDon(r, false); }).join('')
      : '<div style="padding:18px 4px;color:#667085;text-align:center;line-height:1.6">' + (rows.length ? 'Không có đơn nào khớp bộ lọc. Bấm Mọi đơn để xem hết.'
        : 'Tháng này chưa có đơn nào khách gõ số của bạn. Mời khách gõ số điện thoại của bạn vào ô Mã giới thiệu khi đặt bánh trên web hoặc gọi món tại bàn.') + '</div>') + '</div>';
    html += '<div style="font-size:12px;color:#98a2b3;margin:10px 16px 18px;line-height:1.5">Hoa hồng tính trên tiền hàng sau ưu đãi, không gồm phí giao. Đặt bánh web ' +
      (+kq.pt_web || 0) + '%, tại bàn ' + (+kq.pt_tai_ban || 0) + '%, % chốt lúc khách đặt. Cuối tháng quản lý đưa vào phiếu KPI của bạn.</div>';
  }
  var footer = tiem ? '<div style="display:flex;flex-direction:row;gap:8px">' +
    '<button class="btn gh" data-hhgtxuat="1" style="margin:0;flex:1">Xuất Excel</button>' +
    '<button class="btn" data-hhgtkpi="1" style="margin:0;flex:2">Đưa vào phiếu KPI tháng</button></div>' : '';
  var b = frame('Hoa hồng giới thiệu', html, footer ? { footer: footer } : null);
  b.onclick = hhgtBam;
  /* Hai nút ở thanh đáy nằm ngoài thân màn (frame trả thân), gắn riêng. */
  var bx = document.querySelectorAll('[data-hhgtxuat]')[0];
  if (bx) bx.onclick = function () { return dsXuatExcel('hoa_hong_gioi_thieu', { ky: HHGT.ky }); };
  var bk = document.querySelectorAll('[data-hhgtkpi]')[0];
  if (bk) bk.onclick = function () { return hhgtDuaKpi(); };
  var tim = document.getElementById('hhgtTim');
  if (tim) {
    var cu = HHGT.tim;
    var chay = function () { var v = String(tim.value || '').trim(); if (v === cu) return; cu = v; HHGT.tim = v; hhgtVe(); };
    tim.addEventListener('change', chay);
    tim.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); chay(); } });
  }
}

async function hhgtBam(e) {
  var t;
  if ((t = e.target.closest('[data-hhgtky]'))) { HHGT.ky = t.getAttribute('data-hhgtky'); HHGT.mo = ''; return scrHhgt(); }
  if ((t = e.target.closest('[data-hhgtche]'))) { HHGT.che = t.getAttribute('data-hhgtche'); HHGT.mo = ''; return scrHhgt(); }
  if ((t = e.target.closest('[data-hhgttt-chon]'))) { HHGT.tt = t.getAttribute('data-hhgttt-chon'); return hhgtVe(); }
  if ((t = e.target.closest('[data-hhgtdoi]'))) return hhgtDoi(t.getAttribute('data-hhgtdoi'));
  if ((t = e.target.closest('[data-hhgtnv]'))) { var ng = t.getAttribute('data-hhgtnv'); HHGT.mo = HHGT.mo === ng ? '' : ng; return hhgtVe(); }
}

async function hhgtDuaKpi() {
  var ok = await hoiCo('Đưa vào phiếu KPI tháng ' + String(HHGT.ky).slice(5, 7) + '/' + String(HHGT.ky).slice(0, 4),
    'Máy ghi tổng hoa hồng giới thiệu đã ghi sổ của tháng vào phiếu KPI của từng nhân viên. Bấm lại lần nữa vẫn ra đúng một số, không cộng hai lần. Phiếu đã chốt thì để nguyên.',
    'Đưa vào phiếu KPI');
  if (!ok) return;
  var kq;
  try { kq = await api('vagabond.gioi_thieu.dua_vao_kpi', { ky: HHGT.ky }); }
  catch (e) { return toast(errMsg(e) || 'Chưa đưa được vào phiếu KPI. Thử lại sau ít phút.', 4200); }
  var cau = [];
  if ((kq.tao || []).length) cau.push('lập ' + kq.tao.length + ' phiếu mới');
  if ((kq.cap_nhat || []).length) cau.push('cập nhật ' + kq.cap_nhat.length + ' phiếu');
  if ((kq.giu || []).length) cau.push(kq.giu.length + ' phiếu đã đúng số');
  if ((kq.da_chot || []).length) cau.push(kq.da_chot.length + ' phiếu đã chốt, để nguyên');
  toast('Đã đưa ' + money(kq.tong) + ' đ vào phiếu KPI: ' + (cau.join(', ') || 'không có phiếu nào cần ghi') + '.', 5200);
}

async function hhgtDoi(ma) {
  var ds;
  try { ds = (await api('vagabond.gioi_thieu.nhan_vien', {})).ds || []; }
  catch (e) { return toast(errMsg(e) || 'Chưa đọc được danh sách nhân viên.', 4200); }
  var muc = [{ value: '', label: 'Gỡ người giới thiệu', phu: 'Đơn này không tính hoa hồng giới thiệu cho ai' }].concat(ds.map(function (x) {
    return { value: x.ma, label: x.ten, phu: x.duoi ? 'Số đuôi ' + x.duoi : '' };
  }));
  sheet('Người giới thiệu mới', muc, null, async function (it) {
    var lyDo = await hoiChu('Lý do đổi', 'Máy ghi lại ai đổi, lúc nào và lý do này.', '', { bat_buoc: true, goi_y: 'Ví dụ: khách báo gõ nhầm số' });
    if (!lyDo) return;
    try {
      await api('vagabond.gioi_thieu.doi_nguoi', { ma: ma, nguoi: it.value, ly_do: lyDo });
    } catch (e) { return toast(errMsg(e) || 'Chưa đổi được người giới thiệu.', 4200); }
    toast(it.value ? 'Đã đổi người giới thiệu thành ' + it.label + '.' : 'Đã gỡ người giới thiệu.', 3600);
    scrHhgt();
  }, true);
}

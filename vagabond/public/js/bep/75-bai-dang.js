/* ============================================================ bài đăng
   v662 Bài đăng mạng xã hội, phân hệ Khách hàng & Marketing (anh Việt 15/11/2026).

   Designer làm ảnh, Marketing tải lên rồi tự viết chữ cho từng kênh và đăng tay,
   không có chỗ nhìn cả tuần đã đăng gì, hẹn gì. Anh Việt duyệt ảnh bản 2 ngày
   15/11 (tham khảo lịch Hootsuite và Notion: trực quan, nhanh, hạn chế nhầm,
   không trùng):
   - Màn chính là LỊCH (Tuần, Tháng, Danh sách). Khung giờ vàng còn trống hiện
     sẵn, chạm là soạn bài cho đúng giờ đó.
   - Soạn bài: ảnh designer tải lên (nhiều ảnh), ba dòng thuộc tính (Kiểu bài,
     Lúc đăng, Kênh), AI SOẠN CHỮ từ vài dòng ý chính, xem trước từng kênh vuốt
     ngang như bài thật. AI chỉ soạn chữ, không sửa ảnh.
   - Tự lưu, không có nút Lưu nháp. Một nút chính ở đáy nói rõ việc sẽ làm.
   - Chống trùng: chọn giờ thấy ngay giờ nào cùng kênh đã có bài; bảng Kiểm
     trước khi duyệt; máy chủ khoá theo bài (bấm hai lần không đăng hai).
   - Đợt này mọi kênh đăng tay: "Chép và mở app" rồi "Đã đăng".

   Luật nằm ở máy chủ (vagabond/bai_dang.py); màn chỉ HIỆN số và trạng thái máy
   chủ trả về (QT-19). Bài tự lưu trên máy chủ nên không cần bản nháp trên máy
   (48-ban-soan-do.js). Trên nút và trạng thái chỉ ghi bộ phận, không ghi tên. */

var BD_P = 'vagabond.bai_dang.';
/* Chỉ để ẩn ô trên trang chủ; phải trùng tuyệt đối bai_dang.QUYEN_SOAN (ca thu_bai_dang_662 chốt). */
var BD_QUYEN = ['Marketing', 'System Manager', 'Giám đốc', 'AP Giám đốc', 'Sales Manager', 'VGB - Quản lý cửa hàng'];
function coQuyenBaiDang() { return BD_QUYEN.some(function (v) { return hasRole(v); }); }
var BD_KENH = [
  { k: 'fb', ten: 'Facebook', chu: 'f', nen: '#1877F2', cham: '#1877F2', tran: 5000, web: 'https://www.facebook.com/',
    giai: 'Bài trên Trang Facebook của tiệm. Nhiều ảnh thì Facebook tự xếp lưới theo ảnh đầu.' },
  { k: 'ig', ten: 'Instagram', chu: 'IG', nen: 'linear-gradient(45deg,#F58529,#DD2A7B 55%,#8134AF)', cham: '#DD2A7B', tran: 2200, web: 'https://www.instagram.com/',
    giai: 'Bài hoặc Story trên tài khoản Instagram của tiệm. Nhiều ảnh thành băng chuyền 4:5, tối đa 10 ảnh.' },
  { k: 'th', ten: 'Threads', chu: '@', nen: '#101828', cham: '#101828', tran: 500, web: 'https://www.threads.net/',
    giai: 'Một đến ba câu, tối đa 500 ký tự, tối đa 20 ảnh. Threads không có Story.' },
  { k: 'zl', ten: 'Zalo OA', chu: 'Z', nen: '#0068FF', cham: '#0068FF', tran: 5000, web: 'https://oa.zalo.me/',
    giai: 'Bài viết trên trang Zalo OA, có tiêu đề. Không gửi tin cho khách, không tốn phí tin. Zalo OA không có Story.' }
];
/* Màu trạng thái dùng chung mọi màn: thanh trái của thẻ, chấm trên ảnh kênh, chú thích lịch tháng. */
var BD_TT = {
  'Nháp': { ten: 'Nháp', mau: '#98a2b3', nen: '#f2f4f7' },
  'Chờ duyệt': { ten: 'Chờ Marketing duyệt', mau: '#f79009', nen: '#fffaeb' },
  'Đã hẹn giờ': { ten: 'Đã hẹn giờ', mau: '#2e90fa', nen: '#eff8ff' },
  'Chờ đăng tay': { ten: 'Chờ đăng tay', mau: '#7a5af8', nen: '#f4f3ff' },
  'Đã đăng': { ten: 'Đã đăng', mau: '#12b76a', nen: '#ecfdf3' },
  'Chưa đăng': { ten: 'Chưa đăng', mau: '#98a2b3', nen: '#f2f4f7' }
};
var BD_THU = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];
var BD_DS_LOC = [['', 'Mọi bài'], ['chua_gio', 'Chưa hẹn giờ'], ['Chờ duyệt', 'Chờ duyệt'], ['Chờ đăng tay', 'Chờ đăng tay'],
  ['Đã hẹn giờ', 'Đã hẹn giờ'], ['Đã đăng', 'Đã đăng'], ['Nháp', 'Nháp']];
var BD = { xem: 'tuan', moc: '', ngay: '', loc: [], tt: '', dl: null, bai: null, ban: 0, cho: null, thay: {}, thayMa: '', banMa: {}, loiMa: {}, chuoi: Promise.resolve(), tab: 0 };

function bdKenh(k) { return BD_KENH.filter(function (x) { return x.k === k; })[0] || {}; }
function bdThu(ngay) { var p = String(ngay).split('-'); return BD_THU[new Date(+p[0], +p[1] - 1, +p[2]).getDay()]; }
function bdNgayChu(ngay) { return bdThu(ngay) + ' ' + String(ngay).slice(8, 10) + '/' + String(ngay).slice(5, 7); }
function bdLucChu(s) { s = String(s || ''); return s.length >= 16 ? bdNgayChu(s.slice(0, 10)) + ' · ' + s.slice(11, 16) : ''; }
function bdTtMau(tt) { return BD_TT[tt] || BD_TT['Nháp']; }

/* Ảnh tròn của kênh. tt: trạng thái của kênh trong bài, hiện thành chấm góc. */
function bdAvatar(k, co, tt, tat) {
  var kn = bdKenh(k); co = co || 28;
  var cham = tt ? '<span style="position:absolute;right:-2px;bottom:-2px;width:' + Math.round(co * .42) + 'px;height:' + Math.round(co * .42) + 'px;border-radius:50%;' +
    'border:2px solid #fff;background:' + bdTtMau(tt).mau + '"></span>' : '';
  return '<span title="' + h(kn.ten) + '" style="position:relative;flex:0 0 ' + co + 'px;width:' + co + 'px;height:' + co + 'px;border-radius:50%;display:inline-flex;' +
    'align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:' + Math.round(co * (kn.chu.length > 1 ? .36 : .5)) + 'px;background:' + kn.nen +
    (tat ? ';opacity:.28;filter:grayscale(1)' : '') + '">' + kn.chu + cham + '</span>';
}
function bdChongAvatar(ds) {
  return '<span style="display:inline-flex;align-items:center">' + (ds || []).map(function (x, i) {
    return '<span style="margin-left:' + (i ? -6 : 0) + 'px;border-radius:50%;box-shadow:0 0 0 2px #fff;display:inline-flex">' + bdAvatar(x.k, 24, x.tt) + '</span>';
  }).join('') + '</span>';
}
/* Nút phân đoạn (Tuần, Tháng, Danh sách; Bài đăng, Story): một nhóm, một lựa chọn. */
function bdPhanDoan(attr, ds, chon) {
  return '<div role="tablist" style="display:flex;background:#eef0f5;border-radius:12px;padding:3px;gap:3px">' + ds.map(function (x) {
    var on = x[0] === chon;
    return '<button role="tab" aria-selected="' + on + '" ' + attr + '="' + h(x[0]) + '" style="flex:1;min-height:44px;border:0;border-radius:10px;font:inherit;font-size:14px;' +
      'font-weight:' + (on ? 800 : 600) + ';background:' + (on ? '#fff' : 'transparent') + ';color:' + (on ? '#05323C' : '#667085') +
      ';box-shadow:' + (on ? '0 1px 3px rgba(0,0,0,.12)' : 'none') + '">' + h(x[1]) + '</button>';
  }).join('') + '</div>';
}
/* Chip lọc của màn này cao 44 điểm (AGENTS 2b.13), không dùng posChipNut 37 điểm. */
function bdChip(attr, chu, on) {
  return '<button ' + attr + (on ? ' aria-pressed="true"' : '') + ' style="min-height:44px;border:1.5px solid ' + (on ? '#05323C' : '#d7dce5') + ';background:' + (on ? '#05323C' : '#fff') +
    ';color:' + (on ? '#fff' : '#374151') + ';border-radius:999px;padding:0 14px;font:inherit;font-size:14px;font-weight:' + (on ? 800 : 600) + ';white-space:nowrap;cursor:pointer">' + chu + '</button>';
}
function bdCongTac(bat) {
  return '<span aria-hidden="true" style="flex:0 0 50px;width:50px;height:30px;border-radius:15px;position:relative;background:' + (bat ? '#12a150' : '#d0d5dd') + '">' +
    '<span style="position:absolute;top:3px;' + (bat ? 'right:3px' : 'left:3px') + ';width:24px;height:24px;border-radius:50%;background:#fff"></span></span>';
}
function bdLoi(e) { toast(errMsg(e) || 'Chưa làm được. Thử lại sau ít phút.', 4000); }

/* ------------------------------------------------------------ lịch */

function bdTheLich(b) {
  var tt = bdTtMau(b.trang_thai);
  return '<div class="card" data-bdbai="' + h(b.name) + '" style="display:flex;flex-direction:row;gap:10px;align-items:center;padding:8px 10px 8px 0;margin:0 0 8px;' +
    'border-left:4px solid ' + tt.mau + ';cursor:pointer;min-height:64px">' +
    '<div style="flex:0 0 52px;text-align:center;font-size:15px;font-weight:800;color:#05323C">' + h(b.gio || '--:--') +
    (b.kieu === 'Story' ? '<div style="font-size:13px;font-weight:700;color:#7a5af8">Story</div>' : '') + '</div>' +
    '<div style="flex:0 0 48px;height:48px;border-radius:10px;background:#f2f4f7 center/cover no-repeat' + (b.anh ? ' url(' + h(b.anh) + ')' : '') + '"></div>' +
    '<div style="flex:1;min-width:0"><div style="font-size:14px;font-weight:700;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden">' + h(b.tieu_de || 'Bài chưa có ý chính') + '</div>' +
    '<div style="display:flex;align-items:center;gap:8px;margin-top:4px;flex-wrap:wrap">' + bdChongAvatar(b.kenh) +
    '<span style="font-size:13px;color:' + tt.mau + ';font-weight:700">' + h(tt.ten) + '</span></div>' +
    (b.trung ? '<div style="font-size:13px;color:#b42318;margin-top:3px">⚠️ ' + h(b.trung) + '</div>' : '') + '</div></div>';
}
function bdOTrong(gio, ngay) {
  return '<button data-bdtrong="' + h(ngay + ' ' + gio) + '" style="display:flex;align-items:center;gap:10px;width:100%;min-height:48px;margin:0 0 8px;padding:0 10px 0 0;' +
    'border:1.5px dashed #b9e9f3;border-radius:14px;background:#fbfeff;font:inherit;color:#0B7C93;text-align:left;cursor:pointer">' +
    '<span style="flex:0 0 52px;text-align:center;font-size:15px;font-weight:800">' + h(gio) + '</span>' +
    '<span style="font-size:14px;font-weight:700">＋ Soạn bài cho khung này</span>' +
    '<span style="margin-left:auto;font-size:13px;color:#667085">Giờ vàng</span></button>';
}

/* Các dòng của một ngày trên lịch tuần: bài có giờ, xen với khung giờ vàng còn
   trống. Khung nào trống do máy chủ tính (bai_dang.khung_trong), màn chỉ xếp theo giờ. */
function bdDongNgay(n) {
  var dong = (n.bai || []).map(function (b) { return { gio: b.gio, bai: b }; });
  (n.trong || []).forEach(function (g) { dong.push({ gio: g, trong: 1 }); });
  return dong.sort(function (a, b) { return a.gio < b.gio ? -1 : a.gio > b.gio ? 1 : (a.trong ? 1 : -1); });
}

function bdLichTuan(dl) {
  var ngay = dl.ngay || [];
  var chon = ngay.filter(function (n) { return n.ngay === BD.ngay; })[0] || ngay.filter(function (n) { return n.hom_nay; })[0] || ngay[0];
  if (!chon) return '';
  var dai = '<div style="display:flex;gap:4px;margin:10px 0 12px">' + ngay.map(function (n) {
    var on = n === chon, kenhNgay = {};
    (n.bai || []).forEach(function (b) { (b.kenh || []).forEach(function (x) { kenhNgay[x.k] = 1; }); });
    return '<button data-bdngay="' + n.ngay + '" aria-pressed="' + on + '" style="flex:1;min-width:0;min-height:68px;border-radius:14px;font:inherit;cursor:pointer;padding:6px 0;' +
      'border:' + (on ? '0' : n.hom_nay ? '2px solid #0B7C93' : '1px solid #e4e7ec') + ';background:' + (on ? '#05323C' : '#fff') + ';color:' + (on ? '#fff' : n.da_qua ? '#98a2b3' : '#101828') + '">' +
      '<div style="font-size:13px;font-weight:700;opacity:.8">' + bdThu(n.ngay) + '</div>' +
      '<div style="font-size:18px;font-weight:800;line-height:1.25">' + n.ngay.slice(8, 10) + '</div>' +
      '<div style="display:flex;justify-content:center;gap:2px;height:8px;margin-top:2px">' + BD_KENH.filter(function (x) { return kenhNgay[x.k]; }).map(function (x) {
        return '<span style="width:6px;height:6px;border-radius:50%;background:' + x.cham + ';box-shadow:0 0 0 1px #fff"></span>';
      }).join('') + '</div></button>';
  }).join('') + '</div>';
  var dong = bdDongNgay(chon);
  return dai + '<div style="font-size:13px;font-weight:700;color:#667085;margin:0 2px 8px">' + h(bdNgayChu(chon.ngay).toUpperCase()) + ' · ' + (chon.bai || []).length + ' bài</div>' +
    (dong.length ? dong.map(function (x) { return x.trong ? bdOTrong(x.gio, chon.ngay) : bdTheLich(x.bai); }).join('')
      : '<div class="card"><div class="emp" style="padding:18px">Ngày này chưa có bài.</div></div>');
}

function bdLichThang(dl) {
  return '<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:4px;margin-top:10px">' +
    ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'].map(function (t) { return '<div style="text-align:center;font-size:13px;font-weight:700;color:#667085;padding:4px 0">' + t + '</div>'; }).join('') +
    (dl.thang || []).map(function (n) {
      if (!n) return '<div></div>';
      var bai = n.bai || [];
      return '<button data-bdngay="' + n.ngay + '" style="min-height:76px;min-width:0;padding:4px;border-radius:10px;border:' + (n.hom_nay ? '2px solid #0B7C93' : '1px solid #e4e7ec') +
        ';background:' + (n.da_qua ? '#f9fafb' : '#fff') + ';font:inherit;text-align:left;cursor:pointer;display:flex;flex-direction:column;gap:3px">' +
        '<span style="font-size:13px;font-weight:800;color:' + (n.da_qua ? '#98a2b3' : '#101828') + '">' + (+n.ngay.slice(8, 10)) + '</span>' +
        (bai.length ? '<span style="display:flex;gap:2px;flex-wrap:wrap">' + bai.slice(0, 2).map(function (b) {
          return '<span style="width:22px;height:22px;border-radius:6px;background:#f2f4f7 center/cover' + (b.anh ? ' url(' + h(b.anh) + ')' : '') +
            ';box-shadow:inset 0 -3px 0 ' + bdTtMau(b.trang_thai).mau + '"></span>';
        }).join('') + (bai.length > 2 ? '<span style="font-size:13px;color:#667085;font-weight:700">+' + (bai.length - 2) + '</span>' : '') + '</span>' : '') + '</button>';
    }).join('') + '</div>' +
    '<div style="display:flex;flex-wrap:wrap;gap:10px;font-size:13px;color:#475467;margin:10px 2px">' + ['Nháp', 'Chờ duyệt', 'Đã hẹn giờ', 'Chờ đăng tay', 'Đã đăng'].map(function (k) {
      return '<span style="display:inline-flex;align-items:center;gap:5px"><span style="width:10px;height:10px;border-radius:3px;background:' + BD_TT[k].mau + '"></span>' + BD_TT[k].ten + '</span>';
    }).join('') + '</div>';
}

function bdDanhSach(dl) {
  var ds = dl.ds || [];
  return '<div style="margin-top:10px">' + kmHangChip(BD_DS_LOC.map(function (x) { return bdChip('data-bdloctt="' + h(x[0]) + '"', h(x[1]), BD.tt === x[0]); }).join('')) + '</div>' +
    '<div style="font-size:13px;color:#667085;margin:10px 2px 8px">' + h(dl.ky_chu || '') + '</div>' +
    (ds.length ? ds.map(function (b) {
      return (b.ngay ? '<div style="font-size:13px;font-weight:700;color:#667085;margin:4px 2px">' + h(bdNgayChu(b.ngay)) + '</div>' : '') + bdTheLich(b);
    }).join('') : '<div class="card"><div class="emp" style="padding:18px">Chưa có bài nào ở mục này.</div></div>');
}

async function scrBaiDang(dl) {
  var tieuDe = 'Bài đăng mạng xã hội';
  if (!dl) {
    /* Bấm đổi Tuần, Tháng, lọc kênh liên tiếp: lượt trả lời cũ đến muộn không được vẽ đè lượt mới. */
    var luot = BD.luot = (BD.luot || 0) + 1;
    frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc lịch đăng bài...</div></div>');
    try { dl = await api(BD_P + 'lich', { xem: BD.xem, moc: BD.moc, kenh: BD.loc.join(','), trang_thai: BD.xem === 'ds' ? BD.tt : '' }); }
    catch (e) { if (luot !== BD.luot) return; return frame(tieuDe, crmTrong('⚠️', h(errMsg(e)) + '<div style="margin-top:6px">Mở lại màn, hoặc báo quản trị hệ thống.</div>')); }
    if (luot !== BD.luot) return;
  }
  BD.dl = dl; BD.moc = dl.moc;
  var viec = dl.viec || {};
  var oViec = function (tt, so, chu, mau) {
    return so ? '<button data-bdviec="' + h(tt) + '" style="flex:1;min-width:0;min-height:52px;border:0;background:none;font:inherit;text-align:left;cursor:pointer;padding:4px 6px">' +
      '<b style="font-size:20px;color:' + mau + '">' + so + '</b> <span style="font-size:13.5px;font-weight:600">' + chu + ' ›</span></button>' : '';
  };
  var coViec = viec.cho_duyet || viec.dang_tay || viec.chua_gio;
  var html = (coViec ? '<div class="card" style="padding:2px 8px;display:flex;flex-direction:row;gap:2px;flex-wrap:wrap">' +
      oViec('Chờ duyệt', viec.cho_duyet, 'bài chờ duyệt', '#f79009') + oViec('Chờ đăng tay', viec.dang_tay, 'kênh chờ đăng tay', '#7a5af8') +
      oViec('chua_gio', viec.chua_gio, 'bài chưa hẹn giờ', '#667085') + '</div>' : '') +
    bdPhanDoan('data-bdxem', [['tuan', 'Tuần'], ['thang', 'Tháng'], ['ds', 'Danh sách']], BD.xem) +
    (BD.xem === 'ds' ? '' : '<div style="display:flex;align-items:center;gap:6px;margin-top:10px">' +
      '<button class="btn gh" data-bdlui="-1" aria-label="Kỳ trước" style="margin:0;width:44px;min-height:44px;padding:0;font-size:20px">‹</button>' +
      '<b style="flex:1;text-align:center;font-size:16px">' + h(dl.ky_chu || '') + '</b>' +
      '<button class="btn gh" data-bdlui="1" aria-label="Kỳ sau" style="margin:0;width:44px;min-height:44px;padding:0;font-size:20px">›</button></div>') +
    '<div style="display:flex;align-items:center;gap:4px;margin-top:8px"><span style="font-size:13px;color:#667085;font-weight:700;margin-right:4px">KÊNH</span>' +
    BD_KENH.map(function (x) {
      var tat = BD.loc.length && BD.loc.indexOf(x.k) < 0;
      return '<button data-bdlockenh="' + x.k + '" aria-pressed="' + !tat + '" aria-label="Lọc ' + x.ten + '" title="' + x.ten + '" style="width:44px;height:44px;border:0;background:none;padding:0;cursor:pointer;display:inline-flex;align-items:center;justify-content:center">' + bdAvatar(x.k, 32, '', tat) + '</button>';
    }).join('') + (BD.loc.length ? '<button data-bdlockenh="" style="min-height:44px;border:0;background:none;font:inherit;font-size:13.5px;font-weight:700;color:#0B7C93;padding:0 6px">Mọi kênh</button>' : '') + '</div>' +
    (BD.xem === 'thang' ? bdLichThang(dl) : BD.xem === 'ds' ? bdDanhSach(dl) : bdLichTuan(dl));
  var b = frame(tieuDe, html, { action: dl.duyet ? '⚙️' : '', footer: '<button class="btn" data-bdmoi="1" style="margin:0">＋ Bài mới</button>' });
  /* Nút Bài mới nằm ở chân màn (khối .vf), ngoài thân màn: nghe thẳng trên khối đó. */
  var vf = document.querySelector('.vf'); if (vf) vf.onclick = function (e) { if (e.target.closest('[data-bdmoi]')) bdTaoBai(''); };
  var cd = document.getElementById('vgbAct'); if (cd) cd.onclick = function () { bdSheetCaiDat(); };
  b.onclick = async function (e) {
    var t;
    if ((t = e.target.closest('[data-bdxem]'))) { BD.xem = t.getAttribute('data-bdxem'); return scrBaiDang(); }
    if ((t = e.target.closest('[data-bdviec]'))) { BD.xem = 'ds'; BD.tt = t.getAttribute('data-bdviec'); return scrBaiDang(); }
    if ((t = e.target.closest('[data-bdloctt]'))) { BD.tt = t.getAttribute('data-bdloctt'); return scrBaiDang(); }
    if ((t = e.target.closest('[data-bdngay]'))) { BD.ngay = t.getAttribute('data-bdngay'); if (BD.xem === 'thang') { BD.xem = 'tuan'; BD.moc = BD.ngay; return scrBaiDang(); } return scrBaiDang(BD.dl); }
    if ((t = e.target.closest('[data-bdlockenh]'))) {
      var k = t.getAttribute('data-bdlockenh');
      if (!k) BD.loc = [];
      else if (!BD.loc.length) BD.loc = [k];
      else BD.loc = BD.loc.indexOf(k) >= 0 ? BD.loc.filter(function (x) { return x !== k; }) : BD.loc.concat([k]);
      return scrBaiDang();
    }
    if ((t = e.target.closest('[data-bdlui]'))) {
      try { BD.moc = await api(BD_P + 'doi_moc', { moc: BD.moc, xem: BD.xem, buoc: +t.getAttribute('data-bdlui') }); BD.ngay = ''; } catch (er) { return bdLoi(er); }
      return scrBaiDang();
    }
    if ((t = e.target.closest('[data-bdbai]'))) { var ma = t.getAttribute('data-bdbai'); return go(function () { return scrBaiDangSoan(ma); }); }
    if ((t = e.target.closest('[data-bdtrong]'))) return bdTaoBai(t.getAttribute('data-bdtrong'));
  };
}

async function bdTaoBai(hen) {
  busy(true);
  var dl;
  try { dl = await api(BD_P + 'tao', { hen_luc: hen || '' }); } catch (e) { busy(false); return bdLoi(e); }
  busy(false);
  go(function () { return scrBaiDangSoan(dl.bai.name, dl); });
}

/* Giờ vàng: Marketing đặt sẵn, lịch tuần hiện khung trống ở các giờ này. */
async function bdSheetCaiDat() {
  var dl;
  try { dl = await api(BD_P + 'cai_dat', {}); } catch (e) { return bdLoi(e); }
  var ov = crmMoSheet('<div style="font-size:17px;font-weight:800;margin:0 2px 6px">Giờ vàng đăng bài</div>' +
    '<div style="font-size:13.5px;color:#667085;line-height:1.5;margin:0 2px 10px">Lịch tuần hiện sẵn khung trống ở các giờ này để soạn bài nhanh. Ghi giờ cách nhau bằng dấu phẩy, ví dụ 07:30, 11:30, 19:30.</div>' +
    '<input class="tin" id="bdGioVang" value="' + h((dl.gio_vang || []).join(', ')) + '" style="font-size:17px;text-align:left;padding:0 12px"' + (dl.sua ? '' : ' disabled') + '>' +
    (dl.sua ? '<button class="btn" data-bdluugv="1" style="margin:12px 0 0">Lưu giờ vàng</button>' : '<div style="font-size:13.5px;color:#667085;margin-top:8px">Chỉ Marketing sửa được giờ vàng.</div>'));
  var nut = ov.querySelector('[data-bdluugv]');
  if (nut) nut.onclick = async function () {
    try { await api(BD_P + 'cai_dat', { gio_vang_moi: document.getElementById('bdGioVang').value }); }
    catch (e) { return bdLoi(e); }
    ov.remove(); toast('Đã lưu giờ vàng'); scrBaiDang();
  };
}

/* ------------------------------------------------------------ soạn bài */

function bdKhung(tyLe) { var p = String(tyLe).split(':'); return (+p[1] / +p[0] * 100).toFixed(2) + '%'; }

/* THUẦN: lưới ảnh Facebook DỰ KIẾN theo số ảnh và khung ảnh đầu. Meta không công bố
   cách xếp; Facebook quyết định cuối cùng, màn ghi rõ như vậy. Trả các ô
   {x, y, w, h} theo phần trăm, và chiều cao khung theo phần trăm chiều rộng. */
function bdLuoiFb(n, khungDau) {
  var ngang = khungDau === '16:9' || khungDau === '1.91:1';
  var doc = khungDau === '4:5' || khungDau === '9:16' || khungDau === '3:4' || khungDau === '2:3';
  if (n <= 1) return { cao: ngang ? 56.25 : doc ? 125 : 100, o: [{ x: 0, y: 0, w: 100, h: 100 }] };
  if (n === 2) return ngang ? { cao: 100, o: [{ x: 0, y: 0, w: 100, h: 50 }, { x: 0, y: 50, w: 100, h: 50 }] }
    : { cao: doc ? 62.5 : 50, o: [{ x: 0, y: 0, w: 50, h: 100 }, { x: 50, y: 0, w: 50, h: 100 }] };
  if (n === 3) return doc ? { cao: 100, o: [{ x: 0, y: 0, w: 66.6, h: 100 }, { x: 66.6, y: 0, w: 33.4, h: 50 }, { x: 66.6, y: 50, w: 33.4, h: 50 }] }
    : { cao: 100, o: [{ x: 0, y: 0, w: 100, h: 66.6 }, { x: 0, y: 66.6, w: 50, h: 33.4 }, { x: 50, y: 66.6, w: 50, h: 33.4 }] };
  if (n === 4 && !ngang && !doc) return { cao: 100, o: [{ x: 0, y: 0, w: 50, h: 50 }, { x: 50, y: 0, w: 50, h: 50 }, { x: 0, y: 50, w: 50, h: 50 }, { x: 50, y: 50, w: 50, h: 50 }] };
  if (n === 4) return doc ? { cao: 100, o: [{ x: 0, y: 0, w: 66.6, h: 100 }, { x: 66.6, y: 0, w: 33.4, h: 33.3 }, { x: 66.6, y: 33.3, w: 33.4, h: 33.3 }, { x: 66.6, y: 66.6, w: 33.4, h: 33.4 }] }
    : { cao: 100, o: [{ x: 0, y: 0, w: 100, h: 66.6 }, { x: 0, y: 66.6, w: 33.3, h: 33.4 }, { x: 33.3, y: 66.6, w: 33.4, h: 33.4 }, { x: 66.7, y: 66.6, w: 33.3, h: 33.4 }] };
  return doc ? { cao: 100, o: [{ x: 0, y: 0, w: 50, h: 50 }, { x: 0, y: 50, w: 50, h: 50 }, { x: 50, y: 0, w: 50, h: 33.3 }, { x: 50, y: 33.3, w: 50, h: 33.4 }, { x: 50, y: 66.7, w: 50, h: 33.3 }] }
    : { cao: 83.3, o: [{ x: 0, y: 0, w: 50, h: 60 }, { x: 50, y: 0, w: 50, h: 60 }, { x: 0, y: 60, w: 33.3, h: 40 }, { x: 33.3, y: 60, w: 33.4, h: 40 }, { x: 66.7, y: 60, w: 33.3, h: 40 }] };
}

function bdAnhFb(anh) {
  if (!anh.length) return '<div style="padding-top:56%;background:#f2f4f7"></div>';
  var l = bdLuoiFb(anh.length, anh[0].khung);
  return '<div style="position:relative;width:100%;padding-top:' + l.cao + '%;background:#fff">' + l.o.map(function (o, i) {
    var a = anh[i]; if (!a) return '';
    var them = (i === l.o.length - 1 && anh.length > l.o.length) ? '<span style="position:absolute;inset:0;background:rgba(0,0,0,.45);color:#fff;font-size:26px;font-weight:800;display:flex;align-items:center;justify-content:center">+' + (anh.length - l.o.length) + '</span>' : '';
    return '<span style="position:absolute;left:' + o.x + '%;top:' + o.y + '%;width:' + o.w + '%;height:' + o.h + '%;box-sizing:border-box;border:1px solid #fff;background:#f2f4f7 center/cover no-repeat url(' + h(a.url) + ')">' + them + '</span>';
  }).join('') + '</div>' + '<div style="font-size:13px;color:#667085;padding:4px 12px 0">Lưới dự kiến; Facebook tự xếp theo ảnh đầu.</div>';
}
function bdAnhBang(anh, khung, story) {
  if (!anh.length) return '<div style="padding-top:' + bdKhung(khung) + ';background:#f2f4f7"></div>';
  var a = anh[0];
  return '<div style="position:relative;width:100%;padding-top:' + bdKhung(khung) + ';background:#f2f4f7 center/cover no-repeat url(' + h(a.url) + ')">' +
    (anh.length > 1 && !story ? '<span style="position:absolute;right:8px;top:8px;background:rgba(16,24,40,.72);color:#fff;font-size:13px;font-weight:700;border-radius:999px;padding:3px 9px">1/' + anh.length + '</span>' +
      '<span style="position:absolute;left:0;right:0;bottom:8px;display:flex;justify-content:center;gap:4px">' + anh.slice(0, 10).map(function (x, i) {
        return '<span style="width:6px;height:6px;border-radius:50%;background:' + (i ? 'rgba(255,255,255,.6)' : '#fff') + '"></span>';
      }).join('') + '</span>' : '') +
    (a.cat ? '<span style="position:absolute;left:8px;top:8px;background:#fffaeb;color:#93370d;font-size:13px;font-weight:700;border-radius:999px;padding:3px 9px">Ảnh cắt tự động ' + h(khung) + '</span>' : '') + '</div>';
}

/* Xem trước một kênh, dựng giống bài thật trên kênh đó. Chữ sửa thẳng tại chỗ. */
function bdTheXem(bai, k) {
  var kn = bdKenh(k), ban = (bai.ban || {})[k] || {}, anh = (bai.cho_kenh || {})[k] || [], story = bai.kieu === 'Story';
  var dai = String(ban.chu || '').length, qua = dai > kn.tran, khoa = !bai.sua;
  var dau = '<div style="display:flex;align-items:center;gap:8px;padding:10px 12px">' +
    '<span style="flex:0 0 34px;height:34px;border-radius:50%;background:#05323C;color:#50DBF2;display:flex;align-items:center;justify-content:center;font:700 17px Georgia,serif">V</span>' +
    '<div style="flex:1;min-width:0;line-height:1.25"><div style="font-size:14px;font-weight:700">' + (k === 'ig' || k === 'th' ? 'thevagabondpatisserie' : 'The Vagabond Pâtisserie') + '</div>' +
    '<div style="font-size:13px;color:#667085">' + h(story ? 'Story · 24 giờ' : (bdLucChu(bai.hen_luc) || 'Ngay khi duyệt')) + '</div></div>' + bdAvatar(k, 26) + '</div>';
  if (story) {
    return '<div data-bdthe="' + k + '" style="flex:0 0 62%;scroll-snap-align:center;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 1px 4px rgba(20,25,40,.12);border:1px solid #eef0f5">' +
      dau + bdAnhBang(anh, '9:16', 1) + '<div style="font-size:13px;color:#667085;padding:8px 12px">Không có sticker khi tự đăng. Cần sticker thì đăng tay trong app.</div></div>';
  }
  var dong = String(ban.chu || '').split('\n').reduce(function (a, d) { return a + Math.max(1, Math.ceil(d.length / 37)); }, 0);
  var chu = '<textarea data-bdchu="' + k + '"' + (khoa ? ' readonly' : '') + ' rows="' + Math.min(12, Math.max(3, dong + 1)) + '" placeholder="Chữ đăng ' + kn.ten + '" ' +
    'style="display:block;width:100%;box-sizing:border-box;border:0;padding:8px 12px;font:inherit;font-size:14.5px;line-height:1.5;resize:none;background:transparent">' + h(ban.chu || '') + '</textarea>';
  var anhHtml = k === 'fb' ? bdAnhFb(anh) : bdAnhBang(anh, k === 'zl' ? '16:9' : '4:5');
  var tieuDeZl = k === 'zl' ? '<input data-bdtieude="zl"' + (khoa ? ' readonly' : '') + ' value="' + h(ban.tieu_de || '') + '" placeholder="Tiêu đề bài viết Zalo OA" style="display:block;width:100%;box-sizing:border-box;border:0;padding:10px 12px 0;font:inherit;font-size:16px;font-weight:800;min-height:44px">' : '';
  /* Facebook: chữ trên ảnh; Instagram: ảnh trước chữ; Threads: chữ trước ảnh; Zalo OA: ảnh bìa, tiêu đề, chữ. */
  var than = k === 'ig' ? anhHtml + chu : k === 'zl' ? anhHtml + tieuDeZl + chu : chu + anhHtml;
  return '<div data-bdthe="' + k + '" style="flex:0 0 86%;scroll-snap-align:center;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 1px 4px rgba(20,25,40,.12);border:1px solid #eef0f5">' +
    dau + than +
    '<div style="display:flex;align-items:center;gap:6px;padding:6px 8px 8px 12px;border-top:1px solid #f2f4f7">' +
    '<span data-bddem="' + k + '" style="flex:1;font-size:13px;font-weight:700;color:' + (qua ? '#b42318' : '#667085') + '">' + money(dai) + '/' + money(kn.tran) + (qua ? ' · quá dài' : '') + '</span>' +
    (khoa ? '' : '<button data-bdsoanlai="' + k + '" style="min-height:44px;border:0;background:none;font:inherit;font-size:14px;font-weight:700;color:#0B7C93;padding:0 8px">✨ Soạn lại</button>') +
    '<button data-bdchep="' + k + '" style="min-height:44px;border:0;background:none;font:inherit;font-size:14px;font-weight:700;color:#0B7C93;padding:0 8px">📋 Chép</button></div></div>';
}

/* Bảng kiểm trước khi duyệt. Đỏ khoá nút Duyệt; vàng phải xác nhận đã đọc; xanh đạt. */
function bdBangKiem(kiem) {
  if (!kiem || !kiem.length) return '';
  var MAU = { ok: ['#12b76a', '✓'], nhac: ['#f79009', '!'], chan: ['#d92d20', '✕'] };
  return '<div class="card" data-bdkiem="1" style="padding:6px 14px"><div style="font-size:13px;font-weight:800;color:#667085;margin:8px 0 2px">KIỂM TRƯỚC KHI DUYỆT</div>' +
    kiem.map(function (x) {
      var m = MAU[x.muc] || MAU.ok;
      return '<div style="display:flex;gap:10px;align-items:flex-start;padding:9px 0;border-top:1px solid #f2f4f7">' +
        '<span style="flex:0 0 22px;height:22px;border-radius:50%;background:' + m[0] + ';color:#fff;font-size:13px;font-weight:800;display:flex;align-items:center;justify-content:center">' + m[1] + '</span>' +
        '<div style="flex:1;font-size:14px;line-height:1.4">' + h(x.chu) + (x.goi_y ? '<div style="font-size:13px;color:#667085">' + h(x.goi_y) + '</div>' : '') + '</div>' +
        (x.nut ? '<button data-bdsua="' + h(x.nut[0]) + '" style="flex:0 0 auto;min-height:44px;border:0;background:none;font:inherit;font-size:14px;font-weight:700;color:#0B7C93">' + h(x.nut[1]) + '</button>' : '') + '</div>';
    }).join('') + '</div>';
}

/* Sau khi duyệt: kênh nào còn đăng tay thì MỘT nút gom chép chữ, lưu ảnh đúng khung, mở app. */
function bdViecDangTay(bai) {
  var ds = bai.kenh || [];
  if (!ds.length) return '';
  var con = ds.filter(function (x) { return x.tt === 'Chờ đăng tay'; }).length;
  var hen = ds.filter(function (x) { return x.tt === 'Đã hẹn giờ'; }).length;
  return '<div class="card" style="padding:6px 14px"><div style="font-size:13px;font-weight:800;color:#667085;margin:8px 0 2px">' +
    (con ? 'CÒN ' + con + ' KÊNH PHẢI ĐĂNG TAY' : hen ? 'ĐÃ HẸN ' + h(bdLucChu(bai.hen_luc)).toUpperCase() : 'ĐÃ LÊN ĐỦ KÊNH') + '</div>' +
    ds.map(function (x) {
      var kn = bdKenh(x.k);
      var phu = x.tt === 'Đã đăng' ? 'Đã đăng ' + (x.luc || '') : x.tt === 'Đã hẹn giờ' ? 'Đến giờ hẹn hệ thống nhắn nhóm Marketing' : 'Đăng tay trong app';
      return '<div style="border-top:1px solid #f2f4f7"><div style="display:flex;gap:10px;align-items:center;padding:8px 0;min-height:52px">' + bdAvatar(x.k, 32, x.tt) +
        '<div style="flex:1;min-width:0"><div style="font-size:15px;font-weight:700">' + kn.ten + '</div><div style="font-size:13px;color:#667085">' + h(phu) + '</div></div>' +
        (x.link ? '<a href="' + h(x.link) + '" target="_blank" rel="noopener" style="min-height:44px;display:flex;align-items:center;font-size:14px;font-weight:700;color:#0B7C93;text-decoration:none">Xem bài ›</a>' :
          x.tt === 'Đã đăng' ? '<button class="btn gh" data-bdthemlink="' + x.k + '" style="margin:0;min-height:44px;padding:0 12px;font-size:14px">Thêm link</button>' : '') + '</div>' +
        (x.tt === 'Chờ đăng tay' ? '<div style="display:flex;gap:8px;padding:0 0 10px 42px">' +
          '<button class="btn gh" data-bdmotay="' + x.k + '" style="margin:0;flex:1.6;min-height:44px;padding:0 10px;font-size:14px">📋 Chép và mở app</button>' +
          '<button class="btn" data-bddadang="' + x.k + '" style="margin:0;flex:1;min-height:44px;padding:0 10px;font-size:14px">Đã đăng</button></div>' : '') + '</div>';
    }).join('') + '</div>';
}

function bdKhayAnh(bai) {
  var anh = bai.anh || [], story = bai.kieu === 'Story';
  if (!anh.length) {
    return '<button data-bdtaianh="1"' + (bai.sua ? '' : ' disabled') + ' style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;width:100%;min-height:150px;border:2px dashed #7FE5F6;border-radius:16px;background:#fbfeff;font:inherit;color:#0B7C93;cursor:pointer">' +
      '<span style="font-size:32px">📷</span><b style="font-size:17px">Tải ảnh designer lên</b>' +
      '<span style="font-size:13.5px;color:#667085;padding:0 16px;line-height:1.45">Chọn được nhiều ảnh một lần. Ảnh đăng nguyên bản, hệ thống không sửa ảnh.' +
      (story ? ' Story nên dùng ảnh 9:16.' : '') + '</span></button>';
  }
  return '<div style="display:flex;gap:8px;overflow-x:auto;padding:2px 0 6px">' + anh.map(function (a, i) {
    return '<button data-bdanh="' + h(a.ten) + '" aria-label="Ảnh ' + (i + 1) + '" style="position:relative;flex:0 0 92px;height:92px;border-radius:12px;border:' + (i ? '1px solid #e4e7ec' : '2px solid #05323C') +
      ';padding:0;background:#f2f4f7 center/cover no-repeat url(' + h(a.url) + ');cursor:pointer">' +
      '<span style="position:absolute;left:4px;top:4px;background:rgba(16,24,40,.72);color:#fff;font-size:13px;font-weight:800;border-radius:999px;min-width:20px;padding:1px 6px">' + (i + 1) + '</span>' +
      '<span style="position:absolute;left:4px;bottom:4px;background:#fff;color:#101828;font-size:13px;font-weight:700;border-radius:6px;padding:1px 5px">' + h(a.khung || 'khác') + '</span></button>';
  }).join('') + (bai.sua ? '<button data-bdtaianh="1" style="flex:0 0 92px;height:92px;border-radius:12px;border:2px dashed #7FE5F6;background:#fbfeff;font:inherit;font-size:13.5px;font-weight:700;color:#0B7C93;cursor:pointer">＋ Thêm ảnh</button>' : '') + '</div>' +
    '<div style="font-size:13px;color:#667085;margin:2px 2px 0">' + (story ? 'Story dùng ảnh số 1; nên là ảnh 9:16.' : 'Ảnh số 1 quyết định lưới ảnh Facebook. Chạm ảnh để đổi thứ tự hoặc bỏ ảnh.') + '</div>';
}

function bdNutDay(bai, duyet) {
  if (bai.sua) {
    var chan = (bai.kiem || []).filter(function (x) { return x.muc === 'chan'; }).length;
    var viec = bai.hen_luc ? 'hẹn ' + bdLucChu(bai.hen_luc) : 'đăng tay ngay';
    if (!duyet) return bai.trang_thai === 'Chờ duyệt' ? '<button class="btn gh" disabled style="margin:0">Đã gửi, chờ Marketing duyệt</button>'
      : '<button class="btn" data-bdgui="1"' + (chan ? ' disabled style="margin:0;background:#fef3f2;color:#b42318;border:1.5px solid #fda29b"' : ' style="margin:0"') + '>' +
        (chan ? 'Còn ' + chan + ' lỗi đỏ, sửa xong mới gửi được' : 'Gửi Marketing duyệt') + '</button>';
    return '<button class="btn" data-bdduyet="1"' + (chan ? ' disabled style="margin:0;background:#fef3f2;color:#b42318;border:1.5px solid #fda29b"' : ' style="margin:0"') + '>' +
      (chan ? 'Còn ' + chan + ' lỗi đỏ, sửa xong mới duyệt được' : 'Duyệt · ' + viec + ' · ' + (bai.kenh_chon || []).length + ' kênh') + '</button>';
  }
  if (bai.trang_thai === 'Đã hẹn giờ' || bai.trang_thai === 'Chờ đăng tay') {
    var daLen = (bai.kenh || []).some(function (x) { return x.tt === 'Đã đăng'; });
    return daLen ? '' : '<button class="btn gh" data-bdtrave="1" style="margin:0">Trả về nháp để sửa</button>';
  }
  return '';
}

function bdDongTinh(khoa, ic, nhan, gt, attr) {
  return '<button ' + (khoa ? 'disabled ' : '') + attr + ' style="display:flex;align-items:center;gap:10px;width:100%;min-height:50px;border:0;border-top:1px solid #f2f4f7;' +
    'background:none;font:inherit;text-align:left;padding:0;cursor:' + (khoa ? 'default' : 'pointer') + ';color:#101828">' +
    '<span style="flex:0 0 22px;font-size:17px">' + ic + '</span><span style="flex:0 0 86px;font-size:14px;color:#667085">' + nhan + '</span>' +
    '<span style="flex:1;min-width:0;display:flex;align-items:center;gap:6px;font-size:15px;font-weight:700;flex-wrap:wrap">' + gt + '</span>' +
    (khoa ? '' : '<span style="color:#98a2b3;font-size:20px">›</span>') + '</button>';
}

function bdNhanBai(dl) {
  BD.bai = dl.bai; BD.ban = dl.bai.ban_luu; BD.duyet = dl.duyet; BD.gioVang = dl.gio_vang || [];
  BD.banMa[dl.bai.name] = dl.bai.ban_luu;
  /* Phần sửa đang chờ thuộc về MỘT bài. Mở bài khác, hoặc đã chọn "Rời đi, bỏ thay đổi"
     (câu hỏi Chưa lưu đã bị xoá) thì phần chờ cũ bỏ đi, không bao giờ ghi sang bài này. */
  if (BD.thayMa !== dl.bai.name || !S.chuaLuu) { BD.thay = {}; BD.thayMa = dl.bai.name; }
}

async function scrBaiDangSoan(ma, dl) {
  if (!dl) {
    /* Mở bài từ lịch: kết quả lưu hỏng cũ của bài này (đã bỏ thay đổi) không còn giá trị. */
    delete BD.loiMa[ma];
    frame('Bài đăng', '<div class="emp"><div class="e1">⏳</div><div>Đang mở bài...</div></div>');
    try { dl = await api(BD_P + 'xem', { ma: ma }); }
    catch (e) { return frame('Bài đăng', crmTrong('⚠️', h(errMsg(e)))); }
  }
  bdNhanBai(dl);
  var bai = dl.bai, tt = bdTtMau(bai.trang_thai), khoa = !bai.sua, story = bai.kieu === 'Story';
  var chon = bai.kenh_chon || [];
  var html = '<div data-bdman="' + h(bai.name) + '"></div>' + bdKhayAnh(bai) +
    '<div class="card" style="padding:0 14px;margin-top:12px">' +
    '<div style="display:flex;align-items:center;gap:10px;min-height:50px"><span style="flex:0 0 22px;font-size:17px">🏷️</span><span style="flex:0 0 86px;font-size:14px;color:#667085">Trạng thái</span>' +
    '<span style="font-size:13px;font-weight:800;color:' + tt.mau + ';background:' + tt.nen + ';border-radius:999px;padding:5px 10px">' + h(tt.ten) + '</span>' +
    '<span id="bdLuuChu" style="margin-left:auto;font-size:13px;color:#98a2b3">' + (khoa ? '' : 'Đã tự lưu ' + h(bai.luu_luc || '')) + '</span></div>' +
    bdDongTinh(khoa, '🖼️', 'Kiểu bài', h(bai.kieu || 'Bài đăng'), 'data-bdkieu="1"') +
    bdDongTinh(khoa, '📅', 'Lúc đăng', bai.hen_luc ? h(bdLucChu(bai.hen_luc)) : '<span style="color:#98a2b3;font-weight:600">Ngay khi duyệt</span>', 'data-bdgio="1"') +
    bdDongTinh(khoa, '📣', 'Kênh', BD_KENH.filter(function (x) { return !story || x.k === 'fb' || x.k === 'ig'; }).map(function (x) { return bdAvatar(x.k, 28, '', chon.indexOf(x.k) < 0); }).join('') +
      '<span style="font-size:13px;color:#667085;font-weight:600">' + chon.length + ' kênh</span>', 'data-bdchonkenh="1"') + '</div>' +
    (khoa ? bdViecDangTay(bai) : '') +
    (!khoa && !story ? '<div style="font-size:13px;font-weight:800;color:#667085;margin:14px 2px 6px">AI SOẠN CHỮ</div>' +
      '<div class="card" style="padding:4px 4px 8px"><textarea id="bdY" rows="2" placeholder="Ý chính: món, dịp, có ưu đãi không. AI chỉ viết theo đúng ý này." style="display:block;width:100%;box-sizing:border-box;border:0;padding:8px 10px;font:inherit;font-size:15px;line-height:1.5;resize:none">' + h(bai.y_chinh || '') + '</textarea>' +
      '<button class="btn' + (Object.keys(bai.ban || {}).some(function (k) { return (bai.ban[k] || {}).chu; }) ? ' gh' : '') + '" data-bdsoan="1" style="margin:0 6px;width:calc(100% - 12px);min-height:44px;font-size:15px">✨ AI soạn chữ cho ' + chon.length + ' kênh</button></div>' : '') +
    (chon.length ? '<div style="display:flex;align-items:baseline;margin:14px 2px 6px"><span style="font-size:13px;font-weight:800;color:#667085">XEM TRƯỚC TỪNG KÊNH</span>' +
      (chon.length > 1 ? '<span style="margin-left:auto;font-size:13px;color:#98a2b3">vuốt ngang ‹ ›</span>' : '') + '</div>' +
      '<div data-bdcuon="1" style="display:flex;align-items:flex-start;gap:10px;overflow-x:auto;scroll-snap-type:x mandatory;margin:0 -12px;padding:2px 12px 8px">' +
      chon.map(function (k) { return bdTheXem(bai, k); }).join('') + '</div>' : '') +
    (khoa ? '' : '<div id="bdKiemO">' + bdBangKiem(bai.kiem) + '</div>');
  var chan = bdNutDay(bai, dl.duyet);
  var b = frame('Bài đăng', html, { action: (bai.sua || bai.trang_thai === 'Đã hẹn giờ') ? '🗑' : '', footer: chan ? '<div id="bdDay">' + chan + '</div>' : '' });
  var nh = document.getElementById('vgbAct'); if (nh) { nh.setAttribute('aria-label', 'Huỷ bài'); nh.onclick = function () { bdHuy(); }; }
  var vf = document.querySelector('.vf'); if (vf) vf.onclick = function (e) { return bdMotLan(function () { return bdBamDay(e); }); };
  b.oninput = function (e) {
    var t = e.target, k;
    if (t.id === 'bdY') return bdHenLuu({ y_chinh: t.value });
    if ((k = t.getAttribute('data-bdchu'))) {
      var kn = bdKenh(k), n = t.value.length, dem = b.querySelector('[data-bddem="' + k + '"]');
      if (dem) { dem.textContent = money(n) + '/' + money(kn.tran) + (n > kn.tran ? ' · quá dài' : ''); dem.style.color = n > kn.tran ? '#b42318' : '#667085'; }
      var thay = { ban: {} }; thay.ban[k] = { chu: t.value };
      return bdHenLuu(thay);
    }
    if (t.getAttribute('data-bdtieude')) return bdHenLuu({ ban: { zl: { tieu_de: t.value } } });
  };
  b.addEventListener('focusout', function () { bdLuuNgay(); });
  b.onclick = async function (e) {
    var t;
    if ((t = e.target.closest('[data-bdtaianh]'))) return bdChonAnh();
    if ((t = e.target.closest('[data-bdanh]'))) return bdSheetAnh(t.getAttribute('data-bdanh'));
    if (e.target.closest('[data-bdkieu]')) return bdSheetKieu();
    if (e.target.closest('[data-bdgio]')) return bdSheetGio();
    if (e.target.closest('[data-bdchonkenh]')) return bdSheetKenh();
    if (e.target.closest('[data-bdsoan]')) return bdMotLan(function () { return bdSoanAi(''); });
    if ((t = e.target.closest('[data-bdsoanlai]'))) { var kk = t.getAttribute('data-bdsoanlai'); return bdMotLan(function () { return bdSoanAi(kk); }); }
    if ((t = e.target.closest('[data-bdchep]'))) return bdChep(t.getAttribute('data-bdchep'));
    if ((t = e.target.closest('[data-bdmotay]'))) return bdMoTay(t.getAttribute('data-bdmotay'));
    if ((t = e.target.closest('[data-bddadang]'))) return bdDaDang(t.getAttribute('data-bddadang'));
    if ((t = e.target.closest('[data-bdthemlink]'))) return bdThemLink(t.getAttribute('data-bdthemlink'));
    if ((t = e.target.closest('[data-bdsua]'))) return bdSuaTheoKiem(t.getAttribute('data-bdsua'));
  };
}

/* Vẽ lại màn soạn CHỈ khi người dùng vẫn đang ở đúng bài đó: lượt lưu trả lời muộn
   sau khi đã rời màn không được kéo người dùng quay lại bài cũ. */
function bdDangMo(ma) { return !!document.querySelector('[data-bdman="' + ma + '"]'); }
function bdVeLai(dl) { if (!bdDangMo(dl.bai.name)) return; return scrBaiDangSoan(dl.bai.name, dl); }

/* ---------- tự lưu: một hàng đợi, mỗi lần một lượt, gửi kèm số lần lưu đang thấy ---------- */

function bdGop(a, b) {
  Object.keys(b).forEach(function (k) {
    if (k === 'ban') { a.ban = a.ban || {}; Object.keys(b.ban).forEach(function (kk) { a.ban[kk] = Object.assign(a.ban[kk] || {}, b.ban[kk]); }); }
    else a[k] = b[k];
  });
  return a;
}
function bdHenLuu(thay) {
  var ma = BD.bai && BD.bai.name;
  if (!ma) return;
  if (BD.thayMa !== ma) { BD.thay = {}; BD.thayMa = ma; }
  BD.thay = bdGop(BD.thay || {}, thay);
  S.chuaLuu = 'Bài đang lưu dở. Ở lại vài giây để hệ thống lưu xong.';
  var o = document.getElementById('bdLuuChu'); if (o) o.textContent = 'Đang lưu...';
  clearTimeout(BD.cho);
  BD.cho = setTimeout(bdLuuNgay, 800);
}
/* Lưu ngay phần đang chờ. Lượt sau chỉ chạy khi lượt trước xong, để số lần lưu
   gửi lên luôn là số máy chủ vừa trả (không tự báo xung đột với chính mình).
   Phần chờ, mã bài và số lần lưu đi cùng nhau theo TỪNG bài (Codex #572): mở bài B
   sau khi bài A lưu hỏng không được gửi nội dung A dưới mã B hay số lần lưu của B.
   Lưu hỏng: BD.loiMa[mã] = 1 và phần sửa trả lại BD.thay của đúng bài đó (nếu người
   dùng còn ở bài đó). Máy khác vừa sửa: BD.loiMa[mã] = 'xd' để việc kế tiếp trên bài
   đó dừng một lần.
   Lượt sau của chính bài đó lưu được thì xoá; mở lại bài từ lịch cũng xoá. Kết quả
   của bài A không bao giờ chặn việc trên bài B. */
function bdLuuNgay(veLai) {
  clearTimeout(BD.cho);
  var ma = BD.thayMa || (BD.bai && BD.bai.name);
  var thay = BD.thay; BD.thay = {};
  if ((!thay || !Object.keys(thay).length) && !veLai) return BD.chuoi;
  BD.chuoi = BD.chuoi.then(function () {}, function () {}).then(async function () {
    if (!ma) return;
    var dl;
    try { dl = await api(BD_P + 'luu', { ma: ma, ban_luu: BD.banMa[ma] != null ? BD.banMa[ma] : BD.ban, thay: JSON.stringify(thay || {}) }); }
    catch (e) {
      BD.loiMa[ma] = 1;
      /* Chỉ giữ lại để lưu lần sau khi người dùng vẫn ở đúng bài này. */
      if (BD.bai && BD.bai.name === ma && (BD.thayMa === ma || !Object.keys(BD.thay || {}).length)) { BD.thay = bdGop(thay || {}, BD.thay || {}); BD.thayMa = ma; }
      var o0 = document.getElementById('bdLuuChu'); if (o0) o0.textContent = 'Chưa lưu được'; bdLoi(e); return;
    }
    if (dl && dl.bai) BD.banMa[ma] = dl.bai.ban_luu;
    if (dl.xung_dot) BD.loiMa[ma] = 'xd'; else delete BD.loiMa[ma];
    if (!BD.bai || BD.bai.name !== ma || !bdDangMo(ma)) return;
    if (!Object.keys(BD.thay || {}).length) vgbBoChuaLuu();
    if (dl.xung_dot) { toast('Bài vừa được sửa ở máy khác, đã nạp bản mới nhất.', 4000); BD.thay = {}; vgbBoChuaLuu(); bdVeLai(dl); return; }
    bdNhanBai(dl);
    if (veLai) { bdVeLai(dl); return; }
    var o = document.getElementById('bdLuuChu'); if (o) o.textContent = 'Đã tự lưu ' + (dl.bai.luu_luc || '');
    var k = document.getElementById('bdKiemO'); if (k) k.innerHTML = bdBangKiem(dl.bai.kiem);
    var d = document.getElementById('bdDay'); if (d) d.innerHTML = bdNutDay(dl.bai, dl.duyet);
  });
  return BD.chuoi;
}
/* Việc dựa trên bản đã lưu (Duyệt, Gửi duyệt, AI soạn, thêm hay bỏ ảnh): lưu hết phần
   đang chờ và đợi tới khi hàng lưu THẬT SỰ yên (lượt nào nối thêm trong lúc chờ cũng
   phải xong, Codex #572 vòng 4). Lượt cuối của CHÍNH bài này hỏng, còn phần chưa lưu,
   hoặc máy khác vừa sửa (đã nạp bản mới) thì dừng; xung đột chỉ chặn một lần để người
   dùng xem lại bản mới rồi bấm lại. Mỗi việc chỉ chạy một lượt (bdMotLan). */
async function bdLuuChac() {
  var ma = BD.bai && BD.bai.name;
  for (var vong = 0; vong < 50; vong++) {
    var c = bdLuuNgay();
    await c;
    if (c !== BD.chuoi) continue;
    if (BD.loiMa[ma]) break;
    if (BD.thayMa === ma && Object.keys(BD.thay || {}).length) continue;
    break;
  }
  if (!ma || !BD.bai || BD.bai.name !== ma) return false;
  if (BD.loiMa[ma] === 'xd') {
    delete BD.loiMa[ma];
    toast('Bài vừa được sửa ở máy khác, đã nạp bản mới. Xem lại rồi bấm lại.', 4500);
    return false;
  }
  if (BD.loiMa[ma] || (BD.thayMa === ma && Object.keys(BD.thay || {}).length)) {
    toast('Phần vừa sửa chưa lưu được nên chưa làm tiếp. Kiểm mạng rồi bấm lại.', 4500);
    return false;
  }
  return true;
}
/* Một việc dựa trên bản đã lưu chạy một lượt: bấm đúp hay bấm việc khác khi việc trước
   chưa xong thì bỏ qua (H8 loại 4). */
async function bdMotLan(viec) {
  if (BD.dangLam) return;
  BD.dangLam = true;
  try { return await viec(); } finally { BD.dangLam = false; }
}
/* Đổi thuộc tính (kiểu bài, kênh, giờ, thứ tự ảnh): lưu ngay rồi vẽ lại cả màn. */
async function bdLuuVeLai(thay) {
  var ma = BD.bai && BD.bai.name;
  if (!ma) return false;
  if (BD.thayMa !== ma) { BD.thay = {}; BD.thayMa = ma; }
  BD.thay = bdGop(BD.thay || {}, thay);
  return bdLuuNgay(true);
}

/* ---------- ảnh ---------- */

function bdChonAnh() {
  var inp = document.createElement('input');
  inp.type = 'file'; inp.accept = 'image/jpeg,image/png,image/webp'; inp.multiple = true;
  inp.style.display = 'none'; document.body.appendChild(inp);
  inp.onchange = function () { return bdMotLan(bdTaiCacAnh); };
  async function bdTaiCacAnh() {
    var tep = [].slice.call(inp.files || []); inp.remove();
    if (!tep.length) return;
    if (!(await bdLuuChac())) return;
    /* Ảnh thuộc về bài lúc chọn ảnh: mã bài và số lần lưu giữ theo bài đó suốt vòng tải,
       kể cả khi người dùng đã sang bài khác giữa chừng (H8 loại 8). */
    var ma = BD.bai.name, dl = null, loi = 0;
    for (var i = 0; i < tep.length; i++) {
      busy(true);
      try {
        var url = await bdTaiTep(tep[i], ma);
        dl = await api(BD_P + 'them_anh', { ma: ma, ban_luu: BD.banMa[ma] != null ? BD.banMa[ma] : BD.ban, file_url: url });
        if (dl && dl.bai) BD.banMa[ma] = dl.bai.ban_luu;
        if (dl.xung_dot) { busy(false); toast('Bài vừa được sửa ở máy khác, đã nạp bản mới nhất. Tải lại ảnh còn thiếu.', 4000); return bdVeLai(dl); }
        if (BD.bai && BD.bai.name === ma) bdNhanBai(dl);
      } catch (e) { loi++; bdLoi(e); }
      busy(false);
    }
    if (dl) { toast(loi ? 'Đã tải ' + (tep.length - loi) + '/' + tep.length + ' ảnh' : 'Đã tải ' + tep.length + ' ảnh'); bdVeLai(dl); }
  }
  inp.click();
}
async function bdTaiTep(f, ma) {
  var fd = new FormData();
  fd.append('file', f, f.name || ('anh-' + Date.now() + '.jpg'));
  fd.append('is_private', '0');
  fd.append('doctype', 'Vagabond Bai Dang');
  fd.append('docname', ma || BD.bai.name);
  var hd = {};
  hd['X-Frappe-' + 'CSRF-' + 'Token'] = frappe.csrf_token;
  var r = await fetch('/api/method/upload_file', { method: 'POST', headers: hd, body: fd });
  var j = {};
  try { j = await r.json(); } catch (e) { }
  if (!r.ok || !j.message || !j.message.file_url) throw new Error('Chưa tải được ảnh ' + (f.name || '') + '. Ảnh có thể quá nặng; thử ảnh dưới 10 MB.');
  return j.message.file_url;
}
function bdSheetAnh(ten) {
  var anh = BD.bai.anh || [], i = anh.map(function (a) { return a.ten; }).indexOf(ten);
  if (i < 0 || !BD.bai.sua) return;
  var nut = function (attr, chu, phu, dg) {
    return '<button ' + attr + ' style="display:block;width:100%;text-align:left;min-height:52px;border:0;border-top:1px solid #f2f4f7;background:none;font:inherit;padding:8px 2px;cursor:pointer">' +
      '<b style="font-size:15px;color:' + (dg ? '#b42318' : '#101828') + '">' + chu + '</b><div style="font-size:13px;color:#667085">' + phu + '</div></button>';
  };
  var ov = crmMoSheet('<div style="display:flex;gap:12px;align-items:center;margin-bottom:8px"><span style="flex:0 0 64px;height:64px;border-radius:10px;background:#f2f4f7 center/cover url(' + h(anh[i].url) + ')"></span>' +
    '<div><b style="font-size:16px">Ảnh số ' + (i + 1) + '</b><div style="font-size:13px;color:#667085">Khung ' + h(anh[i].khung || 'khác') + ' · ' + anh[i].rong + 'x' + anh[i].cao + '</div></div></div>' +
    (i ? nut('data-bdthu="dau"', 'Đưa lên đầu', 'Thành ảnh số 1: ảnh bìa và quyết định lưới Facebook.') : '') +
    (i ? nut('data-bdthu="-1"', 'Sang trái', 'Đổi chỗ với ảnh số ' + i + '.') : '') +
    (i < anh.length - 1 ? nut('data-bdthu="1"', 'Sang phải', 'Đổi chỗ với ảnh số ' + (i + 2) + '.') : '') +
    nut('data-bdboanh="1"', 'Bỏ ảnh khỏi bài', 'Tệp vẫn còn trên máy chủ, chỉ bỏ khỏi bài này.', 1));
  ov.onclick = async function (e) {
    var t = e.target.closest('[data-bdthu],[data-bdboanh]');
    if (!t) { if (e.target === ov) ov.remove(); return; }
    ov.remove();
    var ds = anh.map(function (a) { return a.ten; });
    if (t.hasAttribute('data-bdboanh')) {
      return bdMotLan(async function () {
        if (!(await bdLuuChac())) return;
        var dl;
        try { dl = await api(BD_P + 'xoa_anh', { ma: BD.bai.name, ban_luu: BD.ban, dong: ten }); } catch (er) { return bdLoi(er); }
        if (dl.xung_dot) toast('Bài vừa được sửa ở máy khác, đã nạp bản mới nhất.', 4000);
        return bdVeLai(dl);
      });
    }
    var v = t.getAttribute('data-bdthu'), j = v === 'dau' ? 0 : i + (+v);
    ds.splice(i, 1); ds.splice(j, 0, ten);
    bdLuuVeLai({ thu_tu_anh: ds });
  };
}

/* ---------- thuộc tính ---------- */

function bdSheetKieu() {
  var ov = crmMoSheet('<div style="font-size:17px;font-weight:800;margin:0 2px 10px">Kiểu bài</div>' +
    [['Bài đăng', 'Bài trên tường của Trang. Một hoặc nhiều ảnh, có chữ. Đăng được cả bốn kênh.'],
      ['Story', 'Ảnh 9:16, mất sau 24 giờ, chỉ Facebook và Instagram. Không có chữ kèm theo; chữ và lời mời in sẵn trên ảnh. Cần sticker (link, bình chọn) thì đăng tay trong app.']].map(function (x) {
      var on = BD.bai.kieu === x[0];
      return '<button data-bdchonkieu="' + x[0] + '" style="display:block;width:100%;text-align:left;min-height:56px;border:' + (on ? '2px solid #05323C' : '1px solid #e4e7ec') + ';border-radius:14px;background:' + (on ? '#E4F9FD' : '#fff') + ';font:inherit;padding:10px 12px;margin-bottom:8px;cursor:pointer">' +
        '<b style="font-size:15px">' + x[0] + (on ? ' ✓' : '') + '</b><div style="font-size:13px;color:#667085;line-height:1.45">' + x[1] + '</div></button>';
    }).join(''));
  ov.onclick = function (e) {
    var t = e.target.closest('[data-bdchonkieu]');
    if (!t) { if (e.target === ov) ov.remove(); return; }
    ov.remove();
    if (t.getAttribute('data-bdchonkieu') !== BD.bai.kieu) bdLuuVeLai({ kieu: t.getAttribute('data-bdchonkieu') });
  };
}
function bdSheetKenh() {
  var story = BD.bai.kieu === 'Story', chon = (BD.bai.kenh_chon || []).slice();
  var ve = function () {
    return '<div style="font-size:17px;font-weight:800;margin:0 2px 4px">Đăng lên kênh</div>' +
      '<div style="font-size:13px;color:#667085;margin:0 2px 10px">Bật kênh nào thì bài có bản xem trước và chữ riêng cho kênh đó.</div>' +
      BD_KENH.map(function (x) {
        var duoc = !story || x.k === 'fb' || x.k === 'ig', bat = chon.indexOf(x.k) >= 0;
        /* Cả dòng là nút bật tắt (cao từ 52 điểm), công tắc chỉ để nhìn trạng thái. */
        return '<button type="button" role="switch" aria-checked="' + bat + '"' + (duoc ? ' data-bdbatkenh="' + x.k + '"' : ' disabled') +
          ' style="display:flex;gap:10px;align-items:center;width:100%;min-height:52px;padding:10px 0;border:0;border-top:1px solid #f2f4f7;background:none;font:inherit;text-align:left;cursor:pointer;opacity:' + (duoc ? 1 : .45) + '">' + bdAvatar(x.k, 32) +
          '<span style="flex:1;min-width:0"><b style="font-size:15px">' + x.ten + '</b><span style="display:block;font-size:13px;color:#667085;line-height:1.4">' + (duoc ? x.giai : x.ten + ' không có Story.') + '</span></span>' +
          (duoc ? bdCongTac(bat) : '') + '</button>';
      }).join('') + '<button class="btn" data-bdxongkenh="1" style="margin:12px 0 0">Xong</button>';
  };
  var ov = crmMoSheet('<div id="bdKenhSh">' + ve() + '</div>');
  ov.onclick = function (e) {
    var t;
    if ((t = e.target.closest('[data-bdbatkenh]'))) {
      var k = t.getAttribute('data-bdbatkenh');
      chon = chon.indexOf(k) >= 0 ? chon.filter(function (x) { return x !== k; }) : chon.concat([k]);
      ov.querySelector('#bdKenhSh').innerHTML = ve();
      return;
    }
    if (e.target.closest('[data-bdxongkenh]') || e.target === ov) {
      ov.remove();
      var cu = (BD.bai.kenh_chon || []).join(','), moi = BD_KENH.filter(function (x) { return chon.indexOf(x.k) >= 0; }).map(function (x) { return x.k; });
      if (moi.join(',') !== cu) bdLuuVeLai({ kenh_chon: moi });
    }
  };
}

/* Chọn giờ: ngày trên, ô giờ dưới. Ô đỏ là kênh đó đã có bài trong 2 giờ, ghi rõ
   trùng bài nào; chạm vẫn được (máy chủ nhắc lại ở bảng Kiểm). Ô kênh đã có bài ĐÚNG
   giờ đó thì khoá (máy chủ cũng chặn Duyệt). Giờ vàng có sao. */
bdSheetGio.luot = 0;
async function bdSheetGio(ngay) {
  await bdLuuNgay();
  var dl;
  try { dl = await api(BD_P + 'gio_trong', { ma: BD.bai.name, ngay: ngay || '' }); } catch (e) { return bdLoi(e); }
  var chon = { ngay: dl.chon, gio: (BD.bai.hen_luc || '').slice(0, 10) === dl.chon ? dl.gio : '' };
  var ve = function () {
    return '<div style="font-size:17px;font-weight:800;margin:0 2px 10px">Lúc đăng</div>' +
      '<div style="display:flex;gap:4px;margin-bottom:12px">' + (dl.ngay || []).map(function (n) {
        var on = n === chon.ngay;
        return '<button data-bdsgngay="' + n + '" style="flex:1;min-width:0;min-height:60px;border-radius:12px;font:inherit;border:' + (on ? 0 : '1px solid #e4e7ec') +
          ';background:' + (on ? '#05323C' : '#fff') + ';color:' + (on ? '#fff' : '#101828') + '"><div style="font-size:13px;font-weight:700;opacity:.8">' + bdThu(n) + '</div>' +
          '<div style="font-size:17px;font-weight:800">' + n.slice(8, 10) + '</div></button>';
      }).join('') + '</div>' +
      '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px">' + (dl.khung || []).map(function (x) {
        var on = x.gio === chon.gio, ban = !!x.trung, tat = x.qua || !!x.da_co;
        return '<button data-bdsggio="' + x.gio + '"' + (tat ? ' disabled' : '') + ' style="min-height:56px;border-radius:12px;font:inherit;padding:4px;opacity:' + (x.qua ? .35 : x.da_co ? .6 : 1) + ';' +
          'border:' + (on ? '2px solid #05323C' : ban ? '1px dashed #fda29b' : '1px solid #e4e7ec') + ';background:' + (on ? '#E4F9FD' : ban ? '#fef3f2' : '#fff') + '">' +
          '<div style="font-size:16px;font-weight:800;color:' + (ban ? '#b42318' : '#101828') + '">' + x.gio + (x.vang ? ' ★' : '') + '</div>' +
          (x.qua ? '<div style="font-size:13px;color:#667085">Đã qua</div>' : x.da_co ? '<div style="font-size:13px;color:#b42318;line-height:1.2">' + h(x.da_co) + ' đã có bài giờ này</div>' : ban ? '<div style="font-size:13px;color:#b42318;line-height:1.2">Trùng ' + h(x.trung) + '</div>' : (x.vang ? '<div style="font-size:13px;color:#0B7C93">Giờ vàng</div>' : '')) + '</button>';
      }).join('') + '</div>' +
      '<div style="font-size:13px;color:#667085;margin:10px 2px;line-height:1.45">★ Giờ vàng: khung Marketing đặt sẵn. Đỏ: kênh đó đã có bài trong vòng 2 giờ, đăng sát nhau dễ làm bài trước bị chìm. Ô mờ: kênh đó đã có bài đúng giờ này, không chọn được.</div>' +
      '<div style="display:flex;gap:8px"><button class="btn gh" data-bdsgngaykhi="1" style="margin:0;flex:1;min-height:48px;font-size:15px">Ngay khi duyệt</button>' +
      '<button class="btn" data-bdsgok="1"' + (chon.gio ? '' : ' disabled') + ' style="margin:0;flex:1.3;min-height:48px;font-size:15px">' + (chon.gio ? 'Chọn ' + chon.gio + ' · ' + bdNgayChu(chon.ngay) : 'Chọn một ô giờ') + '</button></div>';
  };
  var ov = crmMoSheet('<div id="bdGioSh">' + ve() + '</div>');
  ov.onclick = async function (e) {
    var t;
    if ((t = e.target.closest('[data-bdsgngay]'))) {
      var n = t.getAttribute('data-bdsgngay'), luot = ++bdSheetGio.luot;
      try { var d2 = await api(BD_P + 'gio_trong', { ma: BD.bai.name, ngay: n }); } catch (er) { return bdLoi(er); }
      /* Chạm ngày khác trước khi lượt này trả về: lượt cũ không được vẽ đè ô giờ của ngày mới. */
      if (luot !== bdSheetGio.luot) return;
      dl.khung = d2.khung;
      chon.ngay = n; chon.gio = '';
      ov.querySelector('#bdGioSh').innerHTML = ve(); return;
    }
    if ((t = e.target.closest('[data-bdsggio]'))) { chon.gio = t.getAttribute('data-bdsggio'); ov.querySelector('#bdGioSh').innerHTML = ve(); return; }
    if (e.target.closest('[data-bdsgngaykhi]')) { ov.remove(); return bdLuuVeLai({ hen_luc: '' }); }
    if (e.target.closest('[data-bdsgok]') && chon.gio) { ov.remove(); return bdLuuVeLai({ hen_luc: chon.ngay + ' ' + chon.gio }); }
    if (e.target === ov) ov.remove();
  };
}

/* ---------- AI soạn chữ ---------- */

async function bdSoanAi(kenh) {
  var y = document.getElementById('bdY');
  if (y && !y.value.trim()) { y.focus(); return toast('Ghi vài dòng ý chính trước: món, dịp, có ưu đãi không.', 3500); }
  if (!(await bdLuuChac())) return;
  var coChu = kenh ? ((BD.bai.ban || {})[kenh] || {}).chu : Object.keys(BD.bai.ban || {}).some(function (k) { return (BD.bai.ban[k] || {}).chu; });
  if (coChu && !(await confirmSheet('Soạn lại chữ?', 'Chữ đang có của ' + (kenh ? bdKenh(kenh).ten : 'các kênh') + ' sẽ được thay bằng chữ AI mới soạn.', 'Soạn lại'))) return;
  busy(true);
  var dl;
  try { dl = await api(BD_P + 'soan_ai', { ma: BD.bai.name, ban_luu: BD.ban, kenh: kenh || '' }); }
  catch (e) { busy(false); return bdLoi(e); }
  busy(false);
  if (dl.xung_dot) toast('Bài vừa được sửa ở máy khác, đã nạp bản mới nhất. Bấm soạn lại nếu cần.', 4000);
  bdVeLai(dl);
}
function bdSuaTheoKiem(viec) {
  if (viec === 'anh') return bdChonAnh();
  if (viec === 'kenh') return bdSheetKenh();
  if (viec === 'gio') return bdSheetGio();
  if (viec.indexOf('chu:') === 0) {
    var k = viec.slice(4), the = document.querySelector('[data-bdthe="' + k + '"]');
    if (the) { the.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' }); var o = the.querySelector('textarea'); if (o) setTimeout(function () { o.focus(); }, 300); }
  }
}

/* ---------- chép, đăng tay ---------- */

function bdChuKenh(k) {
  var ban = (BD.bai.ban || {})[k] || {};
  return k === 'zl' && ban.tieu_de ? ban.tieu_de + '\n\n' + (ban.chu || '') : (ban.chu || '');
}
async function bdChepChu(chu) {
  try { await navigator.clipboard.writeText(chu); return true; }
  catch (e) {
    var t = document.createElement('textarea'); t.value = chu; t.style.position = 'fixed'; t.style.opacity = '0';
    document.body.appendChild(t); t.select();
    var ok = false; try { ok = document.execCommand('copy'); } catch (e2) { }
    t.remove(); return ok;
  }
}
async function bdChep(k) {
  var chu = bdChuKenh(k);
  if (!chu) return toast('Kênh này chưa có chữ.');
  toast((await bdChepChu(chu)) ? 'Đã chép chữ ' + bdKenh(k).ten + '. Dán vào ô viết bài.' : 'Máy không cho chép tự động; giữ ngón tay trên chữ để chép.', 3500);
}
/* Ảnh cho một kênh đúng khung: ảnh đúng khung dùng nguyên tệp, ảnh lệch khung cắt giữa. */
async function bdTepKenh(k) {
  var ds = (BD.bai.cho_kenh || {})[k] || [], ra = [];
  for (var i = 0; i < ds.length; i++) {
    var a = ds[i], r = await fetch(a.url), blob = await r.blob(), ten = 'vagabond-' + k + '-' + (i + 1) + '.jpg';
    if (a.cat) blob = await bdCatKhung(blob, a.khung);
    ra.push(new File([blob], ten, { type: blob.type || 'image/jpeg' }));
  }
  return ra;
}
function bdCatKhung(blob, khung) {
  return new Promise(function (ok) {
    var img = new Image(), url = URL.createObjectURL(blob);
    img.onload = function () {
      var p = String(khung).split(':'), ty = (+p[0]) / (+p[1]), w = img.naturalWidth, hh = img.naturalHeight, cw = w, ch = hh;
      if (w / hh > ty) cw = Math.round(hh * ty); else ch = Math.round(w / ty);
      var c = document.createElement('canvas'); c.width = cw; c.height = ch;
      c.getContext('2d').drawImage(img, (w - cw) / 2, (hh - ch) / 2, cw, ch, 0, 0, cw, ch);
      URL.revokeObjectURL(url);
      c.toBlob(function (b) { ok(b || blob); }, 'image/jpeg', 0.92);
    };
    img.onerror = function () { URL.revokeObjectURL(url); ok(blob); };
    img.src = url;
  });
}
async function bdMoTay(k) {
  var kn = bdKenh(k), chu = bdChuKenh(k), tep = [];
  busy(true);
  try { tep = await bdTepKenh(k); } catch (e) { tep = []; }
  busy(false);
  var daChep = chu ? await bdChepChu(chu) : false;
  /* Điện thoại có bảng Chia sẻ thì đưa thẳng ảnh và chữ sang app; không có thì tải ảnh về máy và mở trang web của kênh. */
  if (tep.length && navigator.canShare && navigator.canShare({ files: tep })) {
    try { await navigator.share({ files: tep, text: chu }); toast((daChep ? 'Đã chép chữ. ' : '') + 'Đăng xong quay lại bấm Đã đăng.', 4000); return; }
    catch (e) { if (e && e.name === 'AbortError') return; }
  }
  tep.forEach(function (f) {
    var a = document.createElement('a'); a.href = URL.createObjectURL(f); a.download = f.name;
    document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1500);
  });
  try { window.open(kn.web, '_blank', 'noopener'); } catch (e) { }
  toast((daChep ? 'Đã chép chữ' : 'Chưa chép được chữ') + (tep.length ? ', đã lưu ' + tep.length + ' ảnh' : '') + '. Đăng xong quay lại bấm Đã đăng.', 4500);
}
function bdKiemLink(v) { return v && !/^https?:\/\/\S+$/i.test(v) ? 'Link phải bắt đầu bằng https:// và không có dấu cách.' : ''; }
/* Đã đăng: hỏi link bài ngay trong hộp xác nhận (không bắt buộc); kênh đã đăng mà chưa
   có link thì có nút Thêm link để dán sau. */
async function bdDaDang(k) {
  var kn = bdKenh(k);
  var link = await hoiChu('Đã đăng ' + kn.ten + '?', 'Chỉ bấm khi bài đã hiện trên ' + kn.ten + '. Dán link bài để mở lại sau (không bắt buộc).', '',
    { kieu: 'url', goi_y: 'https://...', nut: 'Đã đăng ' + kn.ten, kiem: bdKiemLink });
  if (link === null) return;
  var dl;
  try { dl = await api(BD_P + 'da_dang', { ma: BD.bai.name, kenh: k, link: link }); } catch (e) { return bdLoi(e); }
  toast('Đã ghi ' + kn.ten + ' đã đăng');
  bdVeLai(dl);
}
async function bdThemLink(k) {
  var kn = bdKenh(k);
  var link = await hoiChu('Link bài ' + kn.ten, 'Dán link bài đã đăng để mở lại sau.', '', { kieu: 'url', goi_y: 'https://...', nut: 'Lưu link', bat_buoc: true, kiem: bdKiemLink });
  if (!link) return;
  var dl;
  try { dl = await api(BD_P + 'da_dang', { ma: BD.bai.name, kenh: k, link: link }); } catch (e) { return bdLoi(e); }
  toast('Đã lưu link ' + kn.ten);
  bdVeLai(dl);
}

/* ---------- nút đáy, huỷ ---------- */

async function bdBamDay(e) {
  var t, dl;
  if ((t = e.target.closest('[data-bdduyet]'))) {
    if (!(await bdLuuChac())) return;
    try { dl = await api(BD_P + 'duyet', { ma: BD.bai.name, ban_luu: BD.ban }); } catch (er) { return bdLoi(er); }
    if (dl.can_doc_nhac && dl.can_doc_nhac.length) {
      if (!(await confirmSheet('Duyệt dù còn ' + dl.can_doc_nhac.length + ' điều cần để ý?', dl.can_doc_nhac.join('\n'), 'Vẫn duyệt'))) return bdVeLai(dl);
      try { dl = await api(BD_P + 'duyet', { ma: BD.bai.name, ban_luu: dl.bai.ban_luu, da_doc_nhac: 1 }); } catch (er) { return bdLoi(er); }
    }
    if (dl.xung_dot) { toast('Bài vừa được sửa ở máy khác, đã nạp bản mới. Xem lại rồi bấm Duyệt.', 4500); return bdVeLai(dl); }
    toast(dl.bai.trang_thai === 'Đã hẹn giờ' ? 'Đã duyệt, hẹn ' + bdLucChu(dl.bai.hen_luc) : 'Đã duyệt. Đăng tay từng kênh bên dưới.', 3500);
    return bdVeLai(dl);
  }
  if ((t = e.target.closest('[data-bdgui]'))) {
    if (!(await bdLuuChac())) return;
    try { dl = await api(BD_P + 'gui_duyet', { ma: BD.bai.name, ban_luu: BD.ban }); } catch (er) { return bdLoi(er); }
    if (dl.xung_dot) { toast('Bài vừa được sửa ở máy khác, đã nạp bản mới.', 4000); return bdVeLai(dl); }
    toast('Đã gửi Marketing duyệt'); return bdVeLai(dl);
  }
  if ((t = e.target.closest('[data-bdtrave]'))) {
    if (!(await confirmSheet('Trả về nháp để sửa?', 'Bài thôi hẹn giờ và các kênh thôi chờ đăng. Sửa xong Marketing phải duyệt lại.', 'Trả về nháp'))) return;
    try { dl = await api(BD_P + 'tra_ve', { ma: BD.bai.name }); } catch (er) { return bdLoi(er); }
    return bdVeLai(dl);
  }
}
async function bdHuy() {
  if (!(await confirmSheet('Huỷ bài này?', 'Bài không lên kênh nào và rời khỏi lịch. Bài huỷ vẫn tra được trên Desk.', 'Huỷ bài', true))) return;
  await bdLuuNgay();
  try { await api(BD_P + 'huy', { ma: BD.bai.name }); } catch (e) { return bdLoi(e); }
  vgbBoChuaLuu(); BD.bai = null;
  toast('Đã huỷ bài');
  back();
}

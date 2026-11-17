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
   (48-ban-soan-do.js). Trên nút và trạng thái chỉ ghi bộ phận, không ghi tên.

   v664 (anh Việt 16/11/2026):
   - Kênh đã nối (Facebook, Instagram, Threads) hệ thống TỰ ĐĂNG đúng giờ hẹn; lỗi thì
     kênh chuyển Chờ đăng tay kèm lý do, có nút Thử lại. v666: Zalo OA tự đăng thành Bài viết khi đã nối.
   - Máy tính (rộng từ 900 px): màn soạn hai cột như trang Tạo bài viết của Meta,
     trái là ảnh, thuộc tính, nội dung; phải là xem trước MỘT kênh, chạm tên kênh để
     đổi. Điện thoại giữ một cột, vuốt ngang xem từng kênh.
   - Kho bản thảo thay cho gửi ghi chú qua lại: bài chưa hẹn giờ, cùng sửa một chỗ;
     nhập tệp Word, Excel thành bản thảo. */

var BD_P = 'vagabond.bai_dang.';
/* Chỉ để ẩn ô trên trang chủ; phải trùng tuyệt đối bai_dang.QUYEN_SOAN (ca thu_bai_dang_662 chốt). */
var BD_QUYEN = ['Marketing', 'System Manager', 'Giám đốc', 'AP Giám đốc', 'Sales Manager', 'VGB - Quản lý cửa hàng'];
function coQuyenBaiDang() { return BD_QUYEN.some(function (v) { return hasRole(v); }); }
var BD_KENH = [
  { k: 'fb', ten: 'Facebook', anh: '/assets/vagabond/images/kenh-mxh/facebook.svg', cham: '#1877F2', tran: 5000, web: 'https://www.facebook.com/',
    giai: 'Bài trên Trang Facebook của tiệm. Nhiều ảnh thì Facebook tự xếp lưới theo ảnh đầu.' },
  { k: 'ig', ten: 'Instagram', anh: '/assets/vagabond/images/kenh-mxh/instagram.svg', cham: '#DD2A7B', tran: 2200, web: 'https://www.instagram.com/',
    giai: 'Bài hoặc Story trên tài khoản Instagram của tiệm. Nhiều ảnh thành băng chuyền 4:5, tối đa 10 ảnh.' },
  { k: 'th', ten: 'Threads', anh: '/assets/vagabond/images/kenh-mxh/threads.svg', cham: '#101828', tran: 500, web: 'https://www.threads.net/',
    giai: 'Một đến ba câu, tối đa 500 ký tự, tối đa 20 ảnh. Threads không có Story.' },
  { k: 'zl', ten: 'Zalo OA', anh: '/assets/vagabond/web_order/logo-kenh/zalo.png', cham: '#0068FF', tran: 5000, web: 'https://oa.zalo.me/',
    giai: 'Bài viết trên trang Zalo OA, có tiêu đề. Không gửi tin cho khách, không tốn phí tin. Zalo OA không có Story.' }
];
/* Màu trạng thái dùng chung mọi màn: thanh trái của thẻ, chấm trên ảnh kênh, chú thích lịch tháng. */
var BD_TT = {
  'Nháp': { ten: 'Nháp', mau: '#98a2b3', nen: '#f2f4f7' },
  'Chờ duyệt': { ten: 'Chờ Marketing duyệt', mau: '#f79009', nen: '#fffaeb' },
  'Đã hẹn giờ': { ten: 'Đã hẹn giờ', mau: '#2e90fa', nen: '#eff8ff' },
  'Chờ đăng tay': { ten: 'Chờ đăng tay', mau: '#7a5af8', nen: '#f4f3ff' },
  'Đang đăng': { ten: 'Đang đăng', mau: '#2e90fa', nen: '#eff8ff' },
  'Đã đăng': { ten: 'Đã đăng', mau: '#12b76a', nen: '#ecfdf3' },
  'Chưa đăng': { ten: 'Chưa đăng', mau: '#98a2b3', nen: '#f2f4f7' }
};
var BD_THU = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];
var BD_DS_LOC = [['', 'Mọi bài'], ['chua_gio', 'Chưa hẹn giờ'], ['Chờ duyệt', 'Chờ duyệt'], ['Chờ đăng tay', 'Chờ đăng tay'],
  ['Đã hẹn giờ', 'Đã hẹn giờ'], ['Đã đăng', 'Đã đăng'], ['Nháp', 'Nháp']];
var BD = { dk: {}, dkSo: 0, cd: '', theLoc: '', chon: {}, xemK: '', td: 0, tdCho: 5000, xem: 'tuan', moc: '', ngay: '', loc: [], tt: '', dl: null, bai: null, ban: 0, cho: null, thay: {}, thayMa: '', banMa: {}, loiMa: {}, xdLan: {}, chuoi: Promise.resolve(), tab: 0 };

/* Bố cục: một cột trên điện thoại; từ 900 px hai cột kiểu trang Tạo bài viết của Meta.
   Điện thoại dùng display:contents cho cột trái để thứ tự các khối giữ như cũ. */
function bdCss() {
  var cha = document.head;
  if (!cha || document.getElementById('bdCss')) return;
  var st = document.createElement('style'); st.id = 'bdCss';
  st.textContent = '.bd-hep{max-width:1100px;margin:0 auto}' +
    '.bd-2c{display:flex;flex-direction:column}.bd-trai{display:contents}.bd-chonxem{display:none}' +
    '@media (min-width:900px){' +
    '.bd-2c{display:grid;grid-template-columns:minmax(0,560px) minmax(0,460px);gap:28px;justify-content:center;align-items:start}' +
    '.bd-trai{display:block;min-width:0}.bd-phai{position:sticky;top:12px;min-width:0}' +
    '.bd-chonxem{display:flex}.bd-chidt{display:none}' +
    '.bd-phai [data-bdcuon]{display:block!important;overflow:visible!important;margin:0!important;padding:0!important}' +
    '.bd-phai [data-bdthe]{display:none}.bd-phai [data-bdthe].on{display:block}' +
    '.bd-bt{display:grid;grid-template-columns:240px minmax(0,1fr);gap:16px;align-items:start}.bd-cot{display:block!important;position:sticky;top:12px}.bd-chipcd{display:none!important}}';
  cha.appendChild(st);
}

function bdKenh(k) { return BD_KENH.filter(function (x) { return x.k === k; })[0] || {}; }
function bdThu(ngay) { var p = String(ngay).split('-'); return BD_THU[new Date(+p[0], +p[1] - 1, +p[2]).getDay()]; }
function bdNgayChu(ngay) { return bdThu(ngay) + ' ' + String(ngay).slice(8, 10) + '/' + String(ngay).slice(5, 7); }
function bdLucChu(s) { s = String(s || ''); return s.length >= 16 ? bdNgayChu(s.slice(0, 10)) + ' · ' + s.slice(11, 16) : ''; }
function bdTtMau(tt) { return BD_TT[tt] || BD_TT['Nháp']; }

/* Logo của kênh, dùng đúng tệp logo gốc của hãng (images/kenh-mxh), không vẽ lại.
   tt: trạng thái của kênh trong bài, hiện thành chấm góc. */
var BD_LOGO_TIEM = '/assets/vagabond/images/logo-vagabond-vuong.jpg';
function bdAvatar(k, co, tt, tat) {
  var kn = bdKenh(k); co = co || 28;
  var cham = tt ? '<span style="position:absolute;right:-2px;bottom:-2px;width:' + Math.round(co * .42) + 'px;height:' + Math.round(co * .42) + 'px;border-radius:50%;' +
    'border:2px solid #fff;background:' + bdTtMau(tt).mau + '"></span>' : '';
  return '<span title="' + h(kn.ten) + '" style="position:relative;flex:0 0 ' + co + 'px;width:' + co + 'px;height:' + co + 'px;display:inline-flex' +
    (tat ? ';opacity:.28;filter:grayscale(1)' : '') + '"><img src="' + kn.anh + '" alt="' + h(kn.ten) + '" width="' + co + '" height="' + co + '" ' +
    'style="display:block;width:' + co + 'px;height:' + co + 'px;object-fit:contain">' + cham + '</span>';
}
/* Dãy logo kênh của một bài. Logo là tệp gốc có nền trong, đặt chồng lên nhau thì dính
   chùm (anh Việt 17/11/2026), nên xếp cách nhau, không chồng. */
function bdChongAvatar(ds) {
  return '<span style="display:inline-flex;align-items:center;gap:6px">' + (ds || []).map(function (x) {
    return bdAvatar(x.k, 22, x.tt);
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

/* Ô tìm nhanh đầu danh sách (AGENTS 2b.5): gõ là lọc ngay trên máy, không dấu cũng khớp.
   Chỉ vẽ lại phần danh sách nên ô tìm giữ con trỏ. */
function bdBoDau(s) { return String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D').toLowerCase(); }
function bdKhopTim(chu, q) {
  var t = bdBoDau(chu);
  return bdBoDau(q).split(/\s+/).filter(Boolean).every(function (w) { return t.indexOf(w) >= 0; });
}
function bdOTim(goiY) {
  return '<input class="tin" id="bdTim" type="search" placeholder="' + h(goiY) + '" value="' + h(BD.tim || '') + '" style="font-size:16px;text-align:left;padding:0 12px;margin-top:10px">';
}
function bdDsLoc(dl) {
  var q = BD.tim || '';
  if (BD.xem === 'bt') {
    var bt = (dl.bt || []).filter(function (b) { return !q || bdKhopTim(b.tieu_de + ' ' + b.trich + ' ' + b.nguoi + ' ' + (b.the || []).map(function (t) { return '#' + t; }).join(' '), q); });
    return bt.length ? bt.map(bdTheBanThao).join('') : '<div class="card"><div class="emp" style="padding:18px">' + (q ? 'Không thấy bản thảo nào khớp "' + h(q) + '".' : 'Chưa có bản thảo nào.') + '</div></div>';
  }
  var ds = (dl.ds || []).filter(function (b) {
    return !q || bdKhopTim(b.tieu_de + ' ' + bdTtMau(b.trang_thai).ten + ' ' + (b.kenh || []).map(function (k) { return bdKenh(k.k).ten; }).join(' '), q);
  });
  var truoc = '';
  return ds.length ? ds.map(function (b) {
    var dau = b.ngay && b.ngay !== truoc ? '<div style="font-size:13px;font-weight:700;color:#667085;margin:4px 2px">' + h(bdNgayChu(b.ngay)) + '</div>' : '';
    truoc = b.ngay || truoc;
    return dau + bdTheLich(b);
  }).join('') : '<div class="card"><div class="emp" style="padding:18px">' + (q ? 'Không thấy bài nào khớp "' + h(q) + '".' : 'Chưa có bài nào ở mục này.') + '</div></div>';
}
/* v670 (anh Việt 17/11): dải chip trạng thái ở đầu màn thay thẻ "2 bài chưa hẹn giờ"
   lệch dòng. Đủ mọi loại chip lọc của Danh sách, mỗi chip một số đếm canh giữa trong
   viên tròn; bấm chip nào cũng mở Danh sách lọc đúng loại đó. Số đếm lấy từ máy chủ
   (viec.dem, một nguồn với câu lọc), không tự đếm ở máy. Chip đang chọn tô đậm khi đang
   ở Danh sách; Danh sách không còn hàng chip riêng. */
var BD_DAI_MAU = { '': '#05323C', chua_gio: '#667085' };
function bdDaiTrangThai(dl) {
  var v = dl.viec || {}, dem = v.dem || { chua_gio: v.chua_gio || 0, 'Chờ duyệt': v.cho_duyet || 0 };
  var o = BD_DS_LOC;
  return '<div class="card bd-dai" style="padding:8px;margin-bottom:10px"><div style="display:flex;flex-direction:row;flex-wrap:nowrap;gap:8px;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none">' +
    o.map(function (x) {
      var k = x[0], so = +dem[k] || 0, on = BD.xem === 'ds' && BD.tt === k;
      var mau = BD_DAI_MAU[k] || bdTtMau(k).mau;
      return '<button data-bdviec="' + h(k) + '" aria-pressed="' + on + '" aria-label="' + h(x[1]) + ': ' + so + ' bài" ' +
        'style="flex:0 0 auto;display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:0 6px 0 14px;border-radius:999px;cursor:pointer;font:inherit;white-space:nowrap;' +
        'border:1.5px solid ' + (on ? '#05323C' : '#d7dce5') + ';background:' + (on ? '#05323C' : '#fff') + ';color:' + (on ? '#fff' : so ? '#1d2939' : '#98a2b3') + '">' +
        '<span style="font-size:14px;font-weight:' + (on ? 800 : 600) + ';line-height:1">' + h(x[1]) + '</span>' +
        '<span style="display:inline-flex;align-items:center;justify-content:center;min-width:28px;height:28px;padding:0 7px;box-sizing:border-box;border-radius:14px;' +
        'font-size:13.5px;font-weight:800;line-height:28px;padding-top:1px;font-variant-numeric:tabular-nums;background:' + (on ? '#fff' : so ? mau : '#f2f4f7') + ';color:' + (on ? '#05323C' : so ? '#fff' : '#98a2b3') + '">' + so + '</span></button>';
    }).join('') + '</div></div>';
}
function bdDanhSach(dl) {
  return bdOTim('Tìm theo tên bài, kênh, trạng thái') +
    '<div style="font-size:13px;color:#667085;margin:10px 2px 8px">' + h(dl.ky_chu || '') + '</div>' +
    '<div id="bdDsO">' + bdDsLoc(dl) + '</div>';
}

function bdTheBanThao(b) {
  var nhan = b.cho_gd ? ' · Chờ giám đốc duyệt' : b.tra ? ' · Giám đốc trả lại' : b.trang_thai === 'Chờ duyệt' ? ' · Chờ duyệt' : '';
  return '<div style="position:relative;margin:0 0 8px">' +
    '<button data-bdbai="' + h(b.name) + '" class="card" style="display:flex;flex-direction:row;gap:12px;width:100%;box-sizing:border-box;text-align:left;border:0;font:inherit;color:inherit;cursor:pointer;padding:12px 52px 12px 12px;align-items:flex-start;margin:0">' +
    (b.anh ? '<span style="flex:0 0 56px;height:56px;border-radius:10px;background:#f2f4f7 center/cover no-repeat url(' + h(b.anh) + ')"></span>'
      : '<span style="flex:0 0 56px;height:56px;border-radius:10px;background:#f2f4f7;display:flex;align-items:center;justify-content:center;font-size:22px">📝</span>') +
    '<span style="flex:1;min-width:0"><b style="display:block;font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + h(b.tieu_de) + '</b>' +
    (b.trich ? '<span style="display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;font-size:13.5px;color:#475467;line-height:1.4;margin-top:2px">' + h(b.trich) + '</span>' : '') +
    ((b.the || []).length ? '<span style="display:block;font-size:13px;font-weight:700;color:#0B7C93;margin-top:4px;line-height:1.5">' + b.the.map(function (t) { return '#' + h(t); }).join(' ') + '</span>' : '') +
    '<span style="display:block;font-size:13px;color:#98a2b3;margin-top:4px">Sửa ' + h(bdLucChu(b.luc)) + ' · ' + h(b.nguoi || '') + (b.so_anh ? ' · ' + b.so_anh + ' ảnh' : ' · chưa có ảnh') +
    '<b style="color:' + (b.tra ? '#b42318' : '#b54708') + '">' + h(nhan) + '</b></span></span></button>' +
    '<button data-bdsao="' + h(b.name) + '" aria-pressed="' + (b.sao ? 'true' : 'false') + '" aria-label="' + (b.sao ? 'Bỏ sao' : 'Gắn sao') + '" ' +
    'style="position:absolute;top:4px;right:4px;width:44px;height:44px;border:0;background:none;font-size:22px;cursor:pointer;color:' + (b.sao ? '#f79009' : '#c0c5cf') + '">' + (b.sao ? '★' : '☆') + '</button></div>';
}
/* Sổ chủ đề (anh Việt 17/11/2026, phương án A như sổ Evernote): máy tính có cột chủ đề
   bên trái, điện thoại là dải chip. Lọc chủ đề, sao, thẻ ở máy chủ (trước giới hạn 200). */
function bdMucCd(cdl) {
  var ds = [['*', '⭐', 'Gắn sao', cdl.so_sao], ['', '🗂️', 'Tất cả', cdl.tong]];
  (cdl.ds || []).forEach(function (x) { ds.push([x.ma, x.bt || '🗂️', x.ten, x.so]); });
  if (cdl.khong_chu_de) ds.push(['-', '📂', 'Chưa có chủ đề', cdl.khong_chu_de]);
  return ds;
}
function bdTenCd(cdl, ma) {
  var m = bdMucCd(cdl).filter(function (x) { return x[0] === ma; })[0];
  return m ? m[1] + ' ' + m[2] : '🗂️ Tất cả';
}
function bdKhoBanThao(dl) {
  var cdl = dl.chu_de || { ds: [] }, muc = bdMucCd(cdl), cdThat = (cdl.ds || []).some(function (x) { return x.ma === BD.cd; });
  var cot = '<div class="bd-cot card" style="display:none;padding:8px">' +
    '<div style="font-size:13px;font-weight:800;color:#667085;margin:4px 8px 6px">CHỦ ĐỀ</div>' +
    muc.map(function (x, i) {
      var on = x[0] === BD.cd;
      return (i === 2 ? '<div style="border-top:1px solid #eaecf0;margin:4px 8px"></div>' : '') +
        '<button data-bdcd="' + h(x[0]) + '" aria-pressed="' + on + '" style="display:flex;align-items:center;gap:8px;width:100%;min-height:44px;border:0;border-radius:10px;padding:0 10px;font:inherit;font-size:14px;text-align:left;cursor:pointer;' +
        'background:' + (on ? '#E4F9FD' : 'none') + ';font-weight:' + (on ? 800 : 600) + ';color:#101828"><span style="flex:0 0 22px">' + x[1] + '</span><span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + h(x[2]) + '</span>' +
        '<span style="font-size:13px;color:#98a2b3;font-weight:600">' + (x[3] || '') + '</span></button>';
    }).join('') +
    (cdl.sua ? '<button class="btn gh" data-bdcdmoi="1" style="margin:8px 0 0;width:100%;min-height:44px;font-size:14px">＋ Chủ đề mới</button>' : '') + '</div>';
  var chip = '<div class="bd-chipcd" style="display:flex;gap:7px;overflow-x:auto;margin:10px -12px 0;padding:0 12px 2px">' +
    muc.map(function (x) { return bdChip('data-bdcd="' + h(x[0]) + '"', x[1] + ' ' + h(x[2]) + (x[3] ? ' <span style="opacity:.7">' + x[3] + '</span>' : ''), x[0] === BD.cd); }).join('') +
    (cdl.sua ? bdChip('data-bdcdmoi="1" aria-label="Chủ đề mới"', '＋', false) : '') + '</div>';
  var the = {};
  (dl.bt || []).forEach(function (b) { (b.the || []).forEach(function (t) { the[t] = (the[t] || 0) + 1; }); });
  var theDs = Object.keys(the).sort(function (a, c) { return the[c] - the[a] || (a < c ? -1 : 1); }).slice(0, 12);
  if (BD.theLoc && theDs.indexOf(BD.theLoc) < 0) theDs.unshift(BD.theLoc);
  var phai = '<div>' + chip +
    '<div style="display:flex;align-items:center;gap:8px;margin:12px 2px 0"><b style="flex:1;min-width:0;font-size:16px">' + h(bdTenCd(cdl, BD.cd)) + '</b>' +
    (cdThat && cdl.sua ? '<button data-bdcdsua="' + h(BD.cd) + '" style="min-height:44px;border:0;background:none;font:inherit;font-size:14px;font-weight:700;color:#0B7C93;padding:0 6px">✏️ Sửa chủ đề</button>' : '') + '</div>' +
    '<button class="btn gh" data-bdnhap="1" style="margin:8px 0 0;width:100%;min-height:44px;font-size:15px">📄 Nhập tệp Word, Excel thành bản thảo' + (cdThat ? ' vào chủ đề này' : '') + '</button>' +
    '<div style="font-size:13px;color:#667085;margin-top:6px;line-height:1.45">Word hoặc tệp chữ: mỗi tệp một bản thảo. Excel: mỗi dòng một bản thảo, cột Nội dung bắt buộc; có cột Tiêu đề, Ngày, Giờ, Kênh thì hệ thống điền sẵn.</div>' +
    bdOTim('Tìm trong ' + bdTenCd(cdl, BD.cd).replace(/^\S+ /, '') + ': tên, nội dung, #thẻ') +
    (theDs.length ? '<div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-top:8px"><span style="font-size:13px;color:#667085;font-weight:700">Lọc thẻ</span>' +
      theDs.map(function (t) { var on = t === BD.theLoc; return '<button data-bdlocthe="' + h(t) + '" aria-pressed="' + on + '" style="min-height:44px;border:0;border-radius:999px;padding:0 12px;font:inherit;font-size:13.5px;font-weight:700;cursor:pointer;background:' + (on ? '#05323C' : '#E4F9FD') + ';color:' + (on ? '#fff' : '#0B7C93') + '">#' + h(t) + (on ? ' ✕' : '') + '</button>'; }).join('') + '</div>' : '') +
    '<div style="font-size:13px;color:#667085;margin:10px 2px 8px">' + h(dl.ky_chu || '') + '</div>' +
    '<div id="bdDsO">' + bdDsLoc(dl) + '</div></div>';
  return '<div class="bd-bt" style="margin-top:10px">' + cot + phai + '</div>';
}
function bdNhap() {
  var inp = document.createElement('input');
  inp.type = 'file'; inp.accept = '.docx,.xlsx,.txt,.md';
  inp.onchange = function () { var f = inp.files && inp.files[0]; if (f) bdMotLan(function () { return bdNhapTep(f); }); };
  inp.click();
}
async function bdNhapTep(f) {
  busy(true);
  var dl;
  try {
    var fd = new FormData();
    fd.append('file', f, f.name);
    fd.append('is_private', '1');
    var hd = {};
    hd['X-Frappe-' + 'CSRF-' + 'Token'] = frappe.csrf_token;
    var r = await fetch('/api/method/upload_file', { method: 'POST', headers: hd, body: fd }), j = {};
    try { j = await r.json(); } catch (e) { }
    if (!r.ok || !j.message || !j.message.file_url) throw new Error('Chưa tải được tệp ' + f.name + '. Tệp có thể quá nặng; thử tệp dưới 10 MB.');
    dl = await api(BD_P + 'nhap_tep', { file_url: j.message.file_url, chu_de: bdCdThat() });
  } catch (e) { busy(false); return bdLoi(e); }
  busy(false);
  toast('Đã tạo ' + dl.so + ' bản thảo' + (dl.hen ? '; ' + dl.hen + ' bản có sẵn giờ hẹn nằm trên lịch' : ''), 4500);
  if (dl.so === 1 && !dl.hen) return go(function () { return scrBaiDangSoan(dl.ma[0]); });
  BD.xem = 'bt';
  return scrBaiDang();
}

async function scrBaiDang(dl) {
  var tieuDe = 'Bài đăng mạng xã hội';
  bdCss();
  if (!dl) {
    /* Bấm đổi Tuần, Tháng, lọc kênh liên tiếp: lượt trả lời cũ đến muộn không được vẽ đè lượt mới. */
    var luot = BD.luot = (BD.luot || 0) + 1;
    frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc lịch đăng bài...</div></div>');
    try { dl = await api(BD_P + 'lich', { xem: BD.xem, moc: BD.moc, kenh: BD.loc.join(','), trang_thai: BD.xem === 'ds' ? BD.tt : '', chu_de: BD.xem === 'bt' ? BD.cd : '', the: BD.xem === 'bt' ? BD.theLoc : '' }); }
    catch (e) { if (luot !== BD.luot) return; return frame(tieuDe, crmTrong('⚠️', h(errMsg(e)) + '<div style="margin-top:6px">Mở lại màn, hoặc báo quản trị hệ thống.</div>')); }
    if (luot !== BD.luot) return;
  }
  BD.dl = dl; BD.moc = dl.moc;
  var html = bdDaiTrangThai(dl) +
    bdPhanDoan('data-bdxem', [['tuan', 'Tuần'], ['thang', 'Tháng'], ['ds', 'Danh sách'], ['bt', 'Bản thảo']], BD.xem) +
    (BD.xem === 'bt' ? bdKhoBanThao(dl) : (BD.xem === 'ds' ? '' : '<div style="display:flex;align-items:center;gap:6px;margin-top:10px">' +
      '<button class="btn gh" data-bdlui="-1" aria-label="Kỳ trước" style="margin:0;width:44px;min-height:44px;padding:0;font-size:20px">‹</button>' +
      '<b style="flex:1;text-align:center;font-size:16px">' + h(dl.ky_chu || '') + '</b>' +
      '<button class="btn gh" data-bdlui="1" aria-label="Kỳ sau" style="margin:0;width:44px;min-height:44px;padding:0;font-size:20px">›</button></div>') +
    '<div style="display:flex;align-items:center;gap:4px;margin-top:8px"><span style="font-size:13px;color:#667085;font-weight:700;margin-right:4px">KÊNH</span>' +
    BD_KENH.map(function (x) {
      var tat = BD.loc.length && BD.loc.indexOf(x.k) < 0;
      return '<button data-bdlockenh="' + x.k + '" aria-pressed="' + !tat + '" aria-label="Lọc ' + x.ten + '" title="' + x.ten + '" style="width:44px;height:44px;border:0;background:none;padding:0;cursor:pointer;display:inline-flex;align-items:center;justify-content:center">' + bdAvatar(x.k, 32, '', tat) + '</button>';
    }).join('') + (BD.loc.length ? '<button data-bdlockenh="" style="min-height:44px;border:0;background:none;font:inherit;font-size:13.5px;font-weight:700;color:#0B7C93;padding:0 6px">Mọi kênh</button>' : '') + '</div>' +
    (BD.xem === 'thang' ? bdLichThang(dl) : BD.xem === 'ds' ? bdDanhSach(dl) : bdLichTuan(dl)));
  var b = frame(tieuDe, '<div class="bd-hep">' + html + '</div>', { action: '⚙️',
    footer: '<div class="bd-hep"><button class="btn" data-bdmoi="1" style="margin:0">' + (BD.xem === 'bt' ? '＋ Bản thảo mới' : '＋ Bài mới') + '</button></div>' });
  /* Nút Bài mới nằm ở chân màn (khối .vf), ngoài thân màn: nghe thẳng trên khối đó. */
  var vf = document.querySelector('.vf'); if (vf) vf.onclick = function (e) { if (e.target.closest('[data-bdmoi]')) bdTaoBai(''); };
  var cd = document.getElementById('vgbAct'); if (cd) cd.onclick = function () { bdSheetCaiDat(); };
  b.onclick = async function (e) {
    var t;
    if ((t = e.target.closest('[data-bdxem]'))) { BD.xem = t.getAttribute('data-bdxem'); BD.tim = ''; return scrBaiDang(); }
    if ((t = e.target.closest('[data-bdviec]'))) { BD.xem = 'ds'; BD.tt = t.getAttribute('data-bdviec'); return scrBaiDang(); }
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
    if (e.target.closest('[data-bdnhap]')) return bdNhap();
    if ((t = e.target.closest('[data-bdcd]'))) { BD.cd = t.getAttribute('data-bdcd'); BD.theLoc = ''; BD.tim = ''; return scrBaiDang(); }
    if ((t = e.target.closest('[data-bdlocthe]'))) { var th = t.getAttribute('data-bdlocthe'); BD.theLoc = BD.theLoc === th ? '' : th; return scrBaiDang(); }
    if ((t = e.target.closest('[data-bdsao]'))) return bdSaoThe(t);
    if (e.target.closest('[data-bdcdmoi]')) return bdSheetChuDe(null, function () { scrBaiDang(); });
    if ((t = e.target.closest('[data-bdcdsua]'))) return bdSheetChuDe(t.getAttribute('data-bdcdsua'), function () { scrBaiDang(); });
  };
  b.oninput = function (e) {
    if (e.target.id !== 'bdTim') return;
    BD.tim = e.target.value;
    var o = b.querySelector('#bdDsO');
    if (o) o.innerHTML = bdDsLoc(BD.dl);
  };
}

/* Mã chủ đề đang mở ở Kho bản thảo (không tính Gắn sao, Tất cả, Chưa có chủ đề). */
function bdCdThat() {
  var cdl = (BD.dl && BD.dl.chu_de) || { ds: [] };
  return (cdl.ds || []).some(function (x) { return x.ma === BD.cd; }) ? BD.cd : '';
}
/* Gắn, bỏ sao ngay trên thẻ bản thảo: đổi tại chỗ, không vẽ lại cả danh sách. */
async function bdSaoThe(t) {
  var ma = t.getAttribute('data-bdsao'), moi = t.getAttribute('aria-pressed') === 'true' ? 0 : 1, dl;
  try { dl = await api(BD_P + 'gan_sao', { ma: ma, sao: moi }); } catch (e) { return bdLoi(e); }
  (BD.dl && BD.dl.bt || []).forEach(function (b) { if (b.name === ma) b.sao = dl.sao; });
  if (BD.dl && BD.dl.chu_de) BD.dl.chu_de.so_sao = Math.max(0, (BD.dl.chu_de.so_sao || 0) + (dl.sao ? 1 : -1));
  if (BD.cd === '*' && !dl.sao) return scrBaiDang();
  t.setAttribute('aria-pressed', dl.sao ? 'true' : 'false'); t.setAttribute('aria-label', dl.sao ? 'Bỏ sao' : 'Gắn sao');
  t.textContent = dl.sao ? '★' : '☆'; t.style.color = dl.sao ? '#f79009' : '#c0c5cf';
  toast(dl.sao ? 'Đã gắn sao' : 'Đã bỏ sao');
}
var BD_BT = ['🗂️', '🎉', '📱', '🥐', '🎂', '🍰', '🧋', '☕', '🏛️', '🍂', '🌸', '🍓', '📚', '🎓', '🤝', '🧺', '🎁', '📣', '⭐', '💡'];
/* Tạo hay sửa một chủ đề: tên, biểu tượng, chân bài mẫu (mỗi dòng một câu). */
async function bdSheetChuDe(ma, xong) {
  var cdl;
  try { cdl = await api(BD_P + 'chu_de_ds', {}); } catch (e) { return bdLoi(e); }
  var cd = (cdl.ds || []).filter(function (x) { return x.ma === ma; })[0] || { ten: '', bt: '🗂️', cta: [] };
  var chon = cd.bt || '🗂️';
  var ov = crmMoSheet('<div style="font-size:17px;font-weight:800;margin:0 2px 10px">' + (ma ? 'Sửa chủ đề' : 'Chủ đề mới') + '</div>' +
    '<div style="font-size:14px;font-weight:700;margin:0 2px 6px">Tên chủ đề</div>' +
    '<input class="tin" id="bdCdTen" value="' + h(cd.ten) + '" placeholder="Ví dụ: Giới thiệu bánh ổ" style="font-size:16px;text-align:left;padding:0 12px">' +
    '<div style="font-size:14px;font-weight:700;margin:12px 2px 6px">Biểu tượng</div>' +
    '<div id="bdCdBt" style="display:flex;flex-wrap:wrap;gap:4px">' + BD_BT.map(function (x) {
      return '<button data-bdcdbt="' + x + '" aria-pressed="' + (x === chon) + '" style="width:44px;height:44px;border-radius:10px;font-size:22px;cursor:pointer;border:' + (x === chon ? '2px solid #05323C' : '1px solid #e4e7ec') + ';background:' + (x === chon ? '#E4F9FD' : '#fff') + '">' + x + '</button>';
    }).join('') + '</div>' +
    '<div style="font-size:14px;font-weight:700;margin:12px 2px 2px">Chân bài (CTA) mẫu</div>' +
    '<div style="font-size:13px;color:#667085;margin:0 2px 6px;line-height:1.45">Mỗi dòng một câu. Khi soạn bài thuộc chủ đề này, các câu hiện sẵn để tích thêm vào cuối chữ mọi kênh.</div>' +
    '<textarea class="nt" id="bdCdCta" rows="5" style="font-size:15px">' + h((cd.cta || []).join('\n')) + '</textarea>' +
    '<button class="btn" data-bdcdluu="1" style="margin:12px 0 0">' + (ma ? 'Lưu chủ đề' : 'Tạo chủ đề') + '</button>');
  ov.onclick = async function (e) {
    var t;
    if (e.target === ov) return ov.remove();
    if ((t = e.target.closest('[data-bdcdbt]'))) {
      chon = t.getAttribute('data-bdcdbt');
      ov.querySelectorAll('[data-bdcdbt]').forEach(function (b) { var on = b === t; b.setAttribute('aria-pressed', on); b.style.border = on ? '2px solid #05323C' : '1px solid #e4e7ec'; b.style.background = on ? '#E4F9FD' : '#fff'; });
      return;
    }
    if (!e.target.closest('[data-bdcdluu]')) return;
    var ten = ov.querySelector('#bdCdTen').value.trim();
    if (!ten) return toast('Ghi tên chủ đề.');
    var kq;
    try { kq = await api(BD_P + 'chu_de_luu', { ma: ma || '', ten: ten, bieu_tuong: chon, cta: JSON.stringify(ov.querySelector('#bdCdCta').value.split('\n')) }); }
    catch (er) { return bdLoi(er); }
    ov.remove();
    toast(ma ? 'Đã lưu chủ đề' : 'Đã tạo chủ đề ' + ten);
    if (!ma && BD.xem === 'bt') BD.cd = kq.ma;
    if (xong) xong(kq);
  };
}

async function bdTaoBai(hen) {
  busy(true);
  var dl;
  var ts = { hen_luc: hen || '' }, cd = BD.xem === 'bt' ? bdCdThat() : '';
  if (cd) ts.chu_de = cd;
  try { dl = await api(BD_P + 'tao', ts); } catch (e) { busy(false); return bdLoi(e); }
  busy(false);
  go(function () { return scrBaiDangSoan(dl.bai.name, dl); });
}

/* Kết nối kênh (hệ thống tự đăng kênh nào) và giờ vàng. Không bao giờ hiện token. */
async function bdSheetCaiDat(kiemLai) {
  var dl;
  try { dl = await api(BD_P + 'cai_dat', kiemLai ? { kiem_lai: 1 } : {}); } catch (e) { return bdLoi(e); }
  var kn = dl.ket_noi || {};
  var ov = crmMoSheet('<div style="font-size:17px;font-weight:800;margin:0 2px 6px">Kết nối kênh</div>' +
    '<div class="card" style="padding:2px 14px;margin:0 0 8px">' + BD_KENH.map(function (x, i) {
      var v = kn[x.k] || {}, mau = v.ok ? '#067647' : v.loi ? '#b42318' : '#667085';
      return '<div style="display:flex;gap:10px;align-items:center;padding:10px 0;' + (i ? 'border-top:1px solid #f2f4f7' : '') + '">' + bdAvatar(x.k, 32) +
        '<div style="flex:1;min-width:0"><div style="font-size:15px;font-weight:700">' + x.ten + '</div><div style="font-size:13.5px;color:' + mau + ';line-height:1.4">' + h(v.chu || 'Đăng tay') + '</div></div>' +
        '<span style="flex:0 0 auto;font-size:13px;font-weight:800;border-radius:999px;padding:4px 10px;background:' + (v.ok ? '#ecfdf3' : v.loi ? '#fef3f2' : '#f2f4f7') + ';color:' + mau + '">' + (v.ok ? 'Tự đăng' : v.loi ? 'Lỗi' : 'Đăng tay') + '</span></div>';
    }).join('') + '</div>' +
    '<div style="font-size:13.5px;color:#667085;line-height:1.5;margin:0 2px 8px">' + (dl.quan_tri ? 'Token dán ở Cài đặt lõi và API, mục Đăng bài mạng xã hội (Meta). Hệ thống không bao giờ hiện lại token.' : 'Nối kênh do quản trị hệ thống làm.') + '</div>' +
    '<div style="display:flex;gap:8px;margin-bottom:16px"><button class="btn gh" data-bdkiemkn="1" style="margin:0;flex:1;min-height:44px;font-size:14px">Kiểm lại kết nối</button>' +
    (dl.quan_tri ? '<button class="btn gh" data-bdcdloi="1" style="margin:0;flex:1;min-height:44px;font-size:14px">Mở Cài đặt lõi</button>' : '') + '</div>' +
    '<div style="font-size:17px;font-weight:800;margin:0 2px 6px">Giờ vàng đăng bài</div>' +
    '<div style="font-size:13.5px;color:#667085;line-height:1.5;margin:0 2px 10px">Lịch tuần hiện sẵn khung trống ở các giờ này để soạn bài nhanh. Ghi giờ cách nhau bằng dấu phẩy, ví dụ 07:30, 11:30, 19:30.</div>' +
    '<input class="tin" id="bdGioVang" value="' + h((dl.gio_vang || []).join(', ')) + '" style="font-size:17px;text-align:left;padding:0 12px"' + (dl.sua ? '' : ' disabled') + '>' +
    (dl.sua ? '<button class="btn" data-bdluugv="1" style="margin:12px 0 0">Lưu giờ vàng</button>' : '<div style="font-size:13.5px;color:#667085;margin-top:8px">Chỉ Marketing sửa được giờ vàng.</div>'));
  var nut = ov.querySelector('[data-bdluugv]');
  if (nut) nut.onclick = async function () {
    try { await api(BD_P + 'cai_dat', { gio_vang_moi: document.getElementById('bdGioVang').value }); }
    catch (e) { return bdLoi(e); }
    ov.remove(); toast('Đã lưu giờ vàng'); scrBaiDang();
  };
  var kl = ov.querySelector('[data-bdkiemkn]');
  if (kl) kl.onclick = function () { ov.remove(); bdSheetCaiDat(1); };
  var cd = ov.querySelector('[data-bdcdloi]');
  if (cd) cd.onclick = function () { ov.remove(); go(scrCaiDatLoi); };
}

/* ------------------------------------------------------------ soạn bài */

function bdKhung(tyLe) { var p = String(tyLe).split(':'); return (+p[1] / +p[0] * 100).toFixed(2) + '%'; }

/* THUẦN: lưới ảnh Facebook DỰ KIẾN theo số ảnh và khung ảnh đầu. Meta không công bố
   cách xếp; Facebook quyết định cuối cùng, màn ghi rõ như vậy. Trả các ô
   {x, y, w, h} theo phần trăm, và chiều cao khung theo phần trăm chiều rộng. */
function bdLuoiFb(n, khungDau) {
  /* v668: máy chủ đã đặt khung từng ô theo bảng cỡ ảnh Facebook (bo_cuc_fb):
     1 ảnh theo khung ảnh; 2 ảnh 2:1 chồng dọc, 1:2 hoặc vuông cạnh nhau;
     3 ảnh ảnh chính 2:1 trên, 1:2 trái, vuông lớn trái, hai ô vuông; 4 ảnh lưới
     vuông; 5 ảnh trở lên hai ô vuông lớn trên, ba ô vuông dưới. */
  var p = String(khungDau || '1:1').split(':'), ty = (+p[0] / +p[1]) || 1;
  var ngang = ty > 1.05, doc = ty < 0.95;
  if (n <= 1) return { cao: +(100 / ty).toFixed(2), o: [{ x: 0, y: 0, w: 100, h: 100 }] };
  if (n === 2) return ngang ? { cao: 100, o: [{ x: 0, y: 0, w: 100, h: 50 }, { x: 0, y: 50, w: 100, h: 50 }] }
    : { cao: doc ? 100 : 50, o: [{ x: 0, y: 0, w: 50, h: 100 }, { x: 50, y: 0, w: 50, h: 100 }] };
  if (n === 3) return ngang ? { cao: 100, o: [{ x: 0, y: 0, w: 100, h: 50 }, { x: 0, y: 50, w: 50, h: 50 }, { x: 50, y: 50, w: 50, h: 50 }] }
    : doc ? { cao: 100, o: [{ x: 0, y: 0, w: 50, h: 100 }, { x: 50, y: 0, w: 50, h: 50 }, { x: 50, y: 50, w: 50, h: 50 }] }
    : { cao: 66.67, o: [{ x: 0, y: 0, w: 66.67, h: 100 }, { x: 66.67, y: 0, w: 33.33, h: 50 }, { x: 66.67, y: 50, w: 33.33, h: 50 }] };
  if (n === 4) return { cao: 100, o: [{ x: 0, y: 0, w: 50, h: 50 }, { x: 50, y: 0, w: 50, h: 50 }, { x: 0, y: 50, w: 50, h: 50 }, { x: 50, y: 50, w: 50, h: 50 }] };
  return { cao: 83.33, o: [{ x: 0, y: 0, w: 50, h: 60 }, { x: 50, y: 0, w: 50, h: 60 }, { x: 0, y: 60, w: 33.33, h: 40 }, { x: 33.33, y: 60, w: 33.34, h: 40 }, { x: 66.67, y: 60, w: 33.33, h: 40 }] };
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
function bdTheXem(bai, k, on) {
  var kn = bdKenh(k), ban = (bai.ban || {})[k] || {}, anh = (bai.cho_kenh || {})[k] || [], story = bai.kieu === 'Story';
  var dai = String(ban.chu || '').length, qua = dai > kn.tran, khoa = !bai.sua;
  var dau = '<div style="display:flex;align-items:center;gap:8px;padding:10px 12px">' +
    '<img src="' + BD_LOGO_TIEM + '" alt="The Vagabond Pâtisserie" width="34" height="34" style="flex:0 0 34px;width:34px;height:34px;border-radius:50%;object-fit:cover;border:1px solid #eaecf0">' +
    '<div style="flex:1;min-width:0;line-height:1.25"><div style="font-size:14px;font-weight:700">' + (k === 'ig' || k === 'th' ? 'thevagabondpatisserie' : 'The Vagabond Pâtisserie') + '</div>' +
    '<div style="font-size:13px;color:#667085">' + h(story ? 'Story · 24 giờ' : (bdLucChu(bai.hen_luc) || 'Ngay khi duyệt')) + '</div></div>' + bdAvatar(k, 26) + '</div>';
  if (story) {
    return '<div data-bdthe="' + k + '"' + (on ? ' class="on"' : '') + ' style="flex:0 0 62%;scroll-snap-align:center;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 1px 4px rgba(20,25,40,.12);border:1px solid #eef0f5">' +
      dau + bdAnhBang(anh, '9:16', 1) + '<div style="font-size:13px;color:#667085;padding:8px 12px">Không có sticker khi tự đăng. Cần sticker thì đăng tay trong app.</div></div>';
  }
  var dong = String(ban.chu || '').split('\n').reduce(function (a, d) { return a + Math.max(1, Math.ceil(d.length / 37)); }, 0);
  var chu = '<textarea data-bdchu="' + k + '"' + (khoa ? ' readonly' : '') + ' rows="' + Math.min(12, Math.max(3, dong + 1)) + '" placeholder="Chữ đăng ' + kn.ten + '" ' +
    'style="display:block;width:100%;box-sizing:border-box;border:0;padding:8px 12px;font:inherit;font-size:14.5px;line-height:1.5;resize:none;background:transparent">' + h(ban.chu || '') + '</textarea>';
  var nutK = function (kieu, nhan, kieuChu) {
    return '<button data-bdkieuchu="' + kieu + '" data-k="' + k + '" style="min-height:44px;border:1px solid #e4e7ec;border-radius:10px;background:#fff;font:inherit;font-size:14px;padding:0 12px;cursor:pointer;' + kieuChu + '">' + nhan + '</button>';
  };
  /* Thanh kiểu chữ: bôi đen rồi chạm. Không hiện khi bài đã khoá. */
  var thanhKieu = khoa ? '' : '<div style="display:flex;gap:6px;flex-wrap:wrap;padding:6px 10px 0">' +
    nutK('d', 'Đậm', 'font-weight:800') + nutK('n', 'Nghiêng', 'font-style:italic') + nutK('dn', 'Đậm nghiêng', 'font-weight:800;font-style:italic') + nutK('bo', 'Bỏ kiểu', 'color:#667085') +
    '<button data-bdbieutuong="' + k + '" style="min-height:44px;border:1px solid #e4e7ec;border-radius:10px;background:#fff;font:inherit;font-size:14px;padding:0 12px;cursor:pointer">✨ Biểu tượng</button></div>';
  chu = thanhKieu + chu;
  var anhHtml = k === 'fb' ? bdAnhFb(anh) : bdAnhBang(anh, k === 'zl' ? '16:9' : '4:5');
  var tieuDeZl = k === 'zl' ? '<input data-bdtieude="zl"' + (khoa ? ' readonly' : '') + ' value="' + h(ban.tieu_de || '') + '" placeholder="Tiêu đề bài viết Zalo OA" style="display:block;width:100%;box-sizing:border-box;border:0;padding:10px 12px 0;font:inherit;font-size:16px;font-weight:800;min-height:44px">' : '';
  /* Facebook: chữ trên ảnh; Instagram: ảnh trước chữ; Threads: chữ trước ảnh; Zalo OA: ảnh bìa, tiêu đề, chữ. */
  var than = k === 'ig' ? anhHtml + chu : k === 'zl' ? anhHtml + tieuDeZl + chu : chu + anhHtml;
  return '<div data-bdthe="' + k + '"' + (on ? ' class="on"' : '') + ' style="flex:0 0 86%;scroll-snap-align:center;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 1px 4px rgba(20,25,40,.12);border:1px solid #eef0f5">' +
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

/* Sau khi duyệt: kênh đã nối hệ thống tự đăng; kênh còn đăng tay thì MỘT nút gom chép chữ,
   lưu ảnh đúng khung, mở app. Tự đăng lỗi: hiện lý do, nút Thử lại. */
function bdViecDangTay(bai) {
  var ds = bai.kenh || [];
  if (!ds.length) return '';
  var dem = function (tt) { return ds.filter(function (x) { return x.tt === tt; }).length; };
  var con = dem('Chờ đăng tay'), dang = dem('Đang đăng'), hen = dem('Đã hẹn giờ');
  var henTu = ds.some(function (x) { return x.tt === 'Đã hẹn giờ' && x.tu; });
  var dau = con ? 'CÒN ' + con + ' KÊNH PHẢI ĐĂNG TAY' : dang ? 'HỆ THỐNG ĐANG ĐĂNG' :
    hen ? (bai.hen_luc ? 'ĐÃ HẸN ' + h(bdLucChu(bai.hen_luc)).toUpperCase() : henTu ? 'HỆ THỐNG SẮP ĐĂNG' : 'ĐÃ HẸN') : 'ĐÃ LÊN ĐỦ KÊNH';
  return '<div class="card" style="padding:6px 14px"><div style="font-size:13px;font-weight:800;color:#667085;margin:8px 0 2px">' + dau + '</div>' +
    ds.map(function (x) {
      var kn = bdKenh(x.k);
      var phu = x.tt === 'Đã đăng' ? 'Đã đăng ' + (x.luc || '') + (x.tu ? ' · hệ thống tự đăng' : '') :
        x.tt === 'Đang đăng' ? 'Hệ thống đang đăng lên ' + kn.ten :
        x.tt === 'Đã hẹn giờ' ? (x.tu ? 'Hệ thống tự đăng ' + (bai.hen_luc ? 'lúc ' + bdLucChu(bai.hen_luc) : 'ngay') : 'Đến giờ hẹn hệ thống nhắn nhóm Marketing') :
        x.loi ? 'Hệ thống chưa tự đăng được' : 'Đăng tay trong app';
      return '<div style="border-top:1px solid #f2f4f7"><div style="display:flex;gap:10px;align-items:center;padding:8px 0;min-height:52px">' + bdAvatar(x.k, 32, x.tt) +
        '<div style="flex:1;min-width:0"><div style="font-size:15px;font-weight:700">' + kn.ten + '</div><div style="font-size:13px;color:#667085">' + h(phu) + '</div></div>' +
        (x.link ? '<a href="' + h(x.link) + '" target="_blank" rel="noopener" style="min-height:44px;display:flex;align-items:center;flex:none;font-size:14px;font-weight:700;color:#0B7C93;text-decoration:none">Xem bài ›</a>' :
          x.tt === 'Đã đăng' ? '<button class="btn gh" data-bdthemlink="' + x.k + '" style="margin:0;width:auto;flex:none;min-height:44px;padding:0 12px;font-size:14px">Thêm link</button>' : '') + '</div>' +
        (x.loi && x.tt === 'Chờ đăng tay' ? '<div style="margin:0 0 8px 42px;background:#fef3f2;color:#b42318;border-radius:10px;padding:8px 10px;font-size:13.5px;line-height:1.45">' + h(x.loi) + '</div>' : '') +
        (x.tt === 'Chờ đăng tay' && x.dang_duoc ? '<div style="padding:0 0 8px 42px"><button class="btn" data-bdthulai="' + x.k + '" style="margin:0;width:100%;min-height:44px;font-size:14px">' +
          (x.loi ? '🔁 Thử lại: hệ thống đăng lên ' : '⚡ Để hệ thống đăng lên ') + kn.ten + '</button></div>' : '') +
        (x.tt === 'Chờ đăng tay' ? '<div style="display:flex;gap:8px;padding:0 0 10px 42px">' +
          '<button class="btn gh" data-bdmotay="' + x.k + '" style="margin:0;flex:1.6;min-height:44px;padding:0 10px;font-size:14px">📋 Chép và mở app</button>' +
          '<button class="btn' + (x.dang_duoc ? ' gh' : '') + '" data-bddadang="' + x.k + '" style="margin:0;flex:1;min-height:44px;padding:0 10px;font-size:14px">Đã đăng</button></div>' : '') + '</div>';
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
    var viec = bai.hen_luc ? 'hẹn ' + bdLucChu(bai.hen_luc) : (bai.tu_dong || []).length ? 'đăng ngay' : 'đăng tay ngay';
    if (!duyet) return bai.trang_thai === 'Chờ duyệt' ? '<button class="btn gh" disabled style="margin:0">Đã gửi, chờ ' + (bai.cho_gd ? 'giám đốc' : 'Marketing') + ' duyệt</button>'
      : '<button class="btn" data-bdgui="1"' + (chan ? ' disabled style="margin:0;background:#fef3f2;color:#b42318;border:1.5px solid #fda29b"' : ' style="margin:0"') + '>' +
        (chan ? 'Còn ' + chan + ' lỗi đỏ, sửa xong mới gửi được' : 'Gửi Marketing duyệt') + '</button>';
    var soK = (bai.kenh_chon || []).length;
    /* v666: giám đốc mở bài đang chờ mình duyệt. Đồng ý nội dung (bài chưa đủ ảnh, giờ vẫn
       được), Trả lại kèm góp ý; bài đủ điều kiện thì thêm nút Duyệt để đăng luôn. */
    var hangGd = bai.cho_gd && BD.laGd ? '<div style="display:flex;gap:8px;margin-top:' + (chan ? 0 : 8) + 'px">' +
      '<button class="btn" data-bdgdok="1" style="margin:0;flex:1;background:#067647;color:#fff">✓ Đồng ý nội dung</button>' +
      '<button class="btn gh" data-bdgdtra="1" style="margin:0;flex:1">↩ Trả lại</button></div>' : '';
    var nutDuyet = '<button class="btn" data-bdduyet="1"' + (chan ? ' disabled style="margin:0;flex:1;background:#fef3f2;color:#b42318;border:1.5px solid #fda29b"' : ' style="margin:0;flex:1"') + '>' +
      (chan ? 'Còn ' + chan + ' lỗi đỏ, sửa xong mới duyệt được' : 'Duyệt · ' + viec + ' · ' + soK + ' kênh') + '</button>';
    if (hangGd && chan) return hangGd;
    if (!bai.hen_luc) return nutDuyet + hangGd;
    /* Bài có giờ hẹn: thêm nút Đăng ngay (anh Việt 17/11/2026). Đăng ngay bỏ giờ hẹn nên lỗi
       đỏ về giờ (giờ hẹn đã qua, trùng giờ bài khác) không chặn nút này; máy chủ kiểm lại. */
    var chanNgay = (bai.kiem || []).filter(function (x) { return x.muc === 'chan' && !(x.nut && x.nut[0] === 'gio'); }).length;
    return '<div style="display:flex;gap:8px;flex-wrap:wrap">' + nutDuyet +
      '<button class="btn" data-bddangngay="1"' + (chanNgay ? ' disabled' : '') + ' style="margin:0;flex:0 0 auto;min-width:150px;background:' + (chanNgay ? '#f2f4f7;color:#98a2b3' : '#0B7C93;color:#fff') + '">⚡ Đăng ngay</button></div>' + hangGd;
  }
  if (bai.trang_thai === 'Đã hẹn giờ' || bai.trang_thai === 'Chờ đăng tay') {
    var daLen = (bai.kenh || []).some(function (x) { return x.tt === 'Đã đăng'; });
    return daLen ? '' : '<button class="btn gh" data-bdtrave="1" style="margin:0">Trả về nháp để sửa</button>';
  }
  return '';
}

/* v666: dải trạng thái giám đốc duyệt ở đầu bài. */
function bdBangGd(bai) {
  var o = function (nen, vien, chu, than) {
    return '<div class="card" style="order:0;margin:0 0 12px;padding:12px 14px;background:' + nen + ';border:1px solid ' + vien + '"><div style="font-size:14px;font-weight:800;color:' + chu + '">' + than[0] + '</div>' +
      (than[1] ? '<div style="font-size:14px;line-height:1.5;color:#344054;margin-top:4px;white-space:pre-line">' + than[1] + '</div>' : '') + '</div>';
  };
  if (bai.cho_gd) return o('#fffaeb', '#fedf89', '#b54708', ['👔 Đang chờ giám đốc duyệt', h((bai.gui_gd ? bai.gui_gd + ' gửi ' : 'Gửi ') + (bdLucChu(bai.gui_gd_luc) || '')) +
    (BD.laGd ? '<br>Bấm Đồng ý nội dung khi chữ đã ổn, Duyệt để đăng luôn, hoặc Trả lại kèm góp ý. Sửa chữ trực tiếp được.' : '')]);
  if (bai.ly_do_tra && bai.sua) return o('#fef3f2', '#fecdca', '#b42318', ['↩ Giám đốc trả lại, góp ý:', h(bai.ly_do_tra) + '<br><span style="color:#667085">Sửa xong bấm Gửi giám đốc duyệt, hoặc tự duyệt.</span>']);
  if (bai.gd_dong_y_luc && bai.sua) return o('#ecfdf3', '#abefc6', '#067647', ['✓ Giám đốc đã đồng ý nội dung ' + h(bdLucChu(bai.gd_dong_y_luc)), 'Thêm ảnh, chọn giờ rồi bấm Duyệt để đăng.']);
  return '';
}
/* v666: chân bài (CTA). Câu mẫu của chủ đề cộng câu bài đang dùng; tích là thêm vào cuối
   chữ mọi kênh, bỏ tích là gỡ. Máy chủ đổi chữ (một nguồn), màn vẽ lại bằng chữ trả về. */
function bdCacCta(bai) {
  var ds = ((bai.chu_de || {}).cta || []).slice();
  (bai.chan_bai || []).forEach(function (x) { if (ds.indexOf(x) < 0) ds.push(x); });
  return ds;
}
function bdTheCta(bai) {
  var ds = bdCacCta(bai), dang = bai.chan_bai || [];
  var moiTrongMau = dang.filter(function (x) { return ((bai.chu_de || {}).cta || []).indexOf(x) < 0; }).length;
  return '<div style="font-size:13px;font-weight:800;color:#667085;margin:14px 2px 2px">CHÂN BÀI (CTA)</div>' +
    '<div style="font-size:13px;color:#667085;margin:0 2px 6px;line-height:1.45">Tích để thêm vào cuối chữ mọi kênh' + (bai.chu_de ? '. Gợi ý theo chủ đề ' + h(bai.chu_de.ten) : '. Chọn chủ đề để có câu mẫu') + '.</div>' +
    '<div class="card" style="padding:6px 8px">' +
    ds.map(function (x, i) {
      var on = dang.indexOf(x) >= 0;
      return '<button data-bdcta="' + i + '" aria-pressed="' + on + '" style="display:flex;align-items:center;gap:10px;width:100%;min-height:48px;border:1px solid ' + (on ? '#05323C' : '#eaecf0') + ';border-radius:12px;background:' + (on ? '#E4F9FD' : '#fff') + ';font:inherit;font-size:14px;line-height:1.4;text-align:left;padding:6px 10px;margin:4px 0;cursor:pointer;color:#101828">' +
        '<span style="flex:0 0 22px;height:22px;border-radius:6px;border:2px solid ' + (on ? '#05323C' : '#c0c5cf') + ';background:' + (on ? '#05323C' : '#fff') + ';color:#fff;font-size:14px;display:flex;align-items:center;justify-content:center">' + (on ? '✓' : '') + '</span>' +
        '<span style="flex:1;min-width:0">' + h(x) + '</span></button>';
    }).join('') +
    '<div style="display:flex;gap:6px;margin:6px 0 2px"><input id="bdCtaMoi" placeholder="Thêm câu chân bài khác" style="flex:1;min-width:0;min-height:44px;border:1px solid #e4e7ec;border-radius:10px;padding:0 10px;font:inherit;font-size:15px">' +
    '<button class="btn gh" data-bdctathem="1" style="margin:0;flex:0 0 auto;min-height:44px;width:auto;padding:0 14px;font-size:14px">Thêm</button></div>' +
    (bai.chu_de && BD.duyet && moiTrongMau ? '<button data-bdctamau="1" style="width:100%;min-height:44px;border:0;background:none;font:inherit;font-size:14px;font-weight:700;color:#0B7C93">＋ Lưu ' + moiTrongMau + ' câu mới thành mẫu của chủ đề</button>' : '') + '</div>';
}
async function bdCtaDoi(ds) { return bdLuuVeLai({ chan_bai: ds }); }
async function bdSheetChonChuDe() {
  var cdl;
  try { cdl = await api(BD_P + 'chu_de_ds', {}); } catch (e) { return bdLoi(e); }
  var dang = bdGt('chu_de') || '';
  var nut = function (ma, ic, ten, phu) {
    var on = ma === dang;
    return '<button data-bdchoncd="' + h(ma) + '" style="display:flex;align-items:center;gap:10px;width:100%;text-align:left;min-height:52px;border:' + (on ? '2px solid #05323C' : '1px solid #e4e7ec') + ';border-radius:14px;background:' + (on ? '#E4F9FD' : '#fff') + ';font:inherit;padding:6px 12px;margin-bottom:6px;cursor:pointer">' +
      '<span style="font-size:20px">' + ic + '</span><span style="flex:1;min-width:0"><b style="font-size:15px">' + h(ten) + (on ? ' ✓' : '') + '</b>' + (phu ? '<div style="font-size:13px;color:#667085">' + h(phu) + '</div>' : '') + '</span></button>';
  };
  var ov = crmMoSheet('<div style="font-size:17px;font-weight:800;margin:0 2px 4px">Chủ đề</div>' +
    '<div style="font-size:13px;color:#667085;margin:0 2px 10px;line-height:1.45">Bản thảo nằm trong sổ chủ đề này ở Kho bản thảo, AI viết đúng loại bài, và chân bài mẫu của chủ đề hiện sẵn để tích.</div>' +
    '<div style="max-height:56vh;overflow:auto">' + (cdl.ds || []).map(function (x) { return nut(x.ma, x.bt || '🗂️', x.ten, x.cta.length ? x.cta.length + ' câu chân bài mẫu' : ''); }).join('') +
    nut('', '📂', 'Không thuộc chủ đề nào', '') + '</div>' +
    (cdl.sua ? '<button class="btn gh" data-bdcdmoi2="1" style="margin:8px 0 0;min-height:44px">＋ Chủ đề mới</button>' : ''));
  ov.onclick = function (e) {
    var t;
    if (e.target.closest('[data-bdcdmoi2]')) { ov.remove(); return bdSheetChuDe(null, function (kq) { bdLuuVeLai({ chu_de: kq.ma }); }); }
    if (!(t = e.target.closest('[data-bdchoncd]'))) return;
    ov.remove();
    var ma = t.getAttribute('data-bdchoncd');
    if (ma !== (bdGt('chu_de') || '')) bdLuuVeLai({ chu_de: ma });
  };
}

function bdDongTinh(khoa, ic, nhan, gt, attr) {
  return '<button ' + (khoa ? 'disabled ' : '') + attr + ' style="display:flex;align-items:center;gap:10px;width:100%;min-height:50px;border:0;border-top:1px solid #f2f4f7;' +
    'background:none;font:inherit;text-align:left;padding:0;cursor:' + (khoa ? 'default' : 'pointer') + ';color:#101828">' +
    '<span style="flex:0 0 22px;font-size:17px">' + ic + '</span><span style="flex:0 0 86px;font-size:14px;color:#667085">' + nhan + '</span>' +
    '<span style="flex:1;min-width:0;display:flex;align-items:center;gap:6px;font-size:15px;font-weight:700;flex-wrap:wrap">' + gt + '</span>' +
    (khoa ? '' : '<span style="color:#98a2b3;font-size:20px">›</span>') + '</button>';
}

function bdNhanBai(dl) {
  BD.bai = dl.bai; BD.ban = dl.bai.ban_luu; BD.duyet = dl.duyet; BD.laGd = !!dl.la_gd; BD.gioVang = dl.gio_vang || [];
  BD.banMa[dl.bai.name] = dl.bai.ban_luu;
  /* Phần sửa đang chờ thuộc về MỘT bài. Mở bài khác, hoặc đã chọn "Rời đi, bỏ thay đổi"
     (câu hỏi Chưa lưu đã bị xoá) thì phần chờ cũ bỏ đi, không bao giờ ghi sang bài này. */
  if (BD.thayMa !== dl.bai.name || !S.chuaLuu) { BD.thay = {}; BD.thayMa = dl.bai.name; }
}

async function scrBaiDangSoan(ma, dl) {
  bdCss();
  if (!dl) {
    /* Mở bài từ lịch: kết quả lưu hỏng cũ của bài này (đã bỏ thay đổi) không còn giá trị. */
    delete BD.loiMa[ma]; delete BD.dk[ma];
    frame('Bài đăng', '<div class="emp"><div class="e1">⏳</div><div>Đang mở bài...</div></div>');
    try { dl = await api(BD_P + 'xem', { ma: ma }); }
    catch (e) { return frame('Bài đăng', crmTrong('⚠️', h(errMsg(e)))); }
  }
  bdNhanBai(dl);
  var bai = dl.bai, tt = bdTtMau(bai.trang_thai), khoa = !bai.sua, story = bai.kieu === 'Story';
  if (bai.cho_gd) tt = { ten: 'Chờ giám đốc duyệt', mau: tt.mau, nen: tt.nen };
  var chon = bai.kenh_chon || [];
  var tuDong = bai.tu_dong || [];
  var xemK = chon.indexOf(BD.xemK) >= 0 ? BD.xemK : chon[0];
  var dongY = String(bai.y_chinh || '').split('\n').reduce(function (a, d) { return a + Math.max(1, Math.ceil(d.length / 60)); }, 0);
  /* Cột trái: ảnh, thuộc tính, nội dung gốc, kiểm. Cột phải: xem trước. Mỗi khối có
     order để điện thoại (một cột) giữ thứ tự cũ: xem trước đứng trước bảng Kiểm. */
  var trai = bdBangGd(bai) + '<div style="order:1">' + bdKhayAnh(bai) + '</div>' +
    '<div class="card" style="order:2;padding:0 14px;margin-top:12px">' +
    '<div style="display:flex;align-items:center;gap:10px;min-height:50px"><span style="flex:0 0 22px;font-size:17px">🏷️</span><span style="flex:0 0 86px;font-size:14px;color:#667085">Trạng thái</span>' +
    '<span style="font-size:13px;font-weight:800;color:' + tt.mau + ';background:' + tt.nen + ';border-radius:999px;padding:5px 10px">' + h(tt.ten) + '</span>' +
    '<span id="bdLuuChu" style="margin-left:auto;font-size:13px;color:#98a2b3">' + (khoa ? '' : 'Đã tự lưu ' + h(bai.luu_luc || '')) + '</span></div>' +
    bdDongTinh(khoa, '🖼️', 'Kiểu bài', h(bai.kieu || 'Bài đăng'), 'data-bdkieu="1"') +
    bdDongTinh(khoa, '📅', 'Lúc đăng', bai.hen_luc ? h(bdLucChu(bai.hen_luc)) : '<span style="color:#98a2b3;font-weight:600">Ngay khi duyệt</span>', 'data-bdgio="1"') +
    bdDongTinh(khoa, '📣', 'Kênh', BD_KENH.filter(function (x) { return !story || x.k === 'fb' || x.k === 'ig'; }).map(function (x) { return bdAvatar(x.k, 28, '', chon.indexOf(x.k) < 0); }).join('') +
      '<span style="font-size:13px;color:#667085;font-weight:600">' + chon.length + ' kênh' + (tuDong.length ? ', ' + tuDong.length + ' tự đăng' : '') + '</span>', 'data-bdchonkenh="1"') +
    bdDongTinh(khoa, '📁', 'Chủ đề', bai.chu_de ? h((bai.chu_de.bt || '') + ' ' + bai.chu_de.ten) : '<span style="color:#98a2b3;font-weight:600">Chưa chọn</span>', 'data-bdchude="1"') +
    '<label style="display:flex;align-items:center;gap:10px;min-height:50px;border-top:1px solid #f2f4f7"><span style="flex:0 0 22px;font-size:17px">#</span><span style="flex:0 0 86px;font-size:14px;color:#667085">Thẻ</span>' +
    '<input data-bdthevao="1"' + (khoa ? ' readonly' : '') + ' value="' + h((bai.the || []).map(function (t) { return '#' + t; }).join(' ')) + '" placeholder="#peachruby #millecrepes" ' +
    'style="flex:1;min-width:0;min-height:44px;border:0;font:inherit;font-size:15px;font-weight:700;color:#0B7C93;background:transparent"></label>' +
    '<button data-bdsaobai="1" aria-pressed="' + (bai.sao ? 'true' : 'false') + '" style="display:flex;align-items:center;gap:10px;width:100%;min-height:50px;border:0;border-top:1px solid #f2f4f7;background:none;font:inherit;text-align:left;padding:0;cursor:pointer;color:#101828">' +
    '<span style="flex:0 0 22px;font-size:17px;color:#f79009">' + (bai.sao ? '★' : '☆') + '</span><span style="flex:0 0 86px;font-size:14px;color:#667085">Gắn sao</span>' +
    '<span style="flex:1;font-size:13.5px;color:#667085">Bản thảo hay dùng lại, hiện ở mục Gắn sao</span>' + bdCongTac(bai.sao) + '</button></div>' +
    (khoa ? '<div style="order:3">' + bdViecDangTay(bai) + '</div>' : '') +
    (!khoa && !story ? '<div style="order:4"><div style="font-size:13px;font-weight:800;color:#667085;margin:14px 2px 6px">NỘI DUNG GỐC</div>' +
      '<div class="card" style="padding:4px 4px 8px"><textarea id="bdY" rows="' + Math.min(14, Math.max(3, dongY + 1)) + '" placeholder="Gõ hoặc dán nội dung: món, dịp, câu chuyện, ưu đãi nếu có. AI viết chữ từng kênh theo đúng nội dung này." style="display:block;width:100%;box-sizing:border-box;border:0;padding:8px 10px;font:inherit;font-size:15px;line-height:1.5;resize:vertical">' + h(bai.y_chinh || '') + '</textarea>' +
      '<div style="border-top:1px solid #f2f4f7;margin:4px 6px 0;padding-top:6px"><div style="font-size:13px;font-weight:700;color:#667085;padding:0 4px">Muốn AI viết thế nào (không bắt buộc)</div>' +
      '<textarea id="bdYc" rows="2" placeholder="Ví dụ: giọng khoa học, kể nguồn gốc Ruby Chocolate; Facebook dài, Threads một câu." style="display:block;width:100%;box-sizing:border-box;border:0;padding:6px 4px;font:inherit;font-size:15px;line-height:1.5;resize:vertical">' + h(bai.yeu_cau_ai || '') + '</textarea></div>' +
      '<button class="btn' + (Object.keys(bai.ban || {}).some(function (k) { return (bai.ban[k] || {}).chu; }) ? ' gh' : '') + '" data-bdsoan="1" style="margin:0 6px;width:calc(100% - 12px);min-height:44px;font-size:15px">✨ AI soạn chữ cho ' + chon.length + ' kênh</button>' +
      '<div style="font-size:13px;color:#667085;margin:6px 8px 0;line-height:1.45">AI viết theo giọng văn The Vagabond' + (bai.chu_de ? ', đúng chủ đề ' + h(bai.chu_de.ten) : '') + ((bai.chan_bai || []).length ? ', rồi gắn chân bài đã tích' : '') + '.</div></div>' +
      bdTheCta(bai) + '</div>' : '') +
    (khoa ? '' : '<div id="bdKiemO" style="order:6">' + bdBangKiem(bai.kiem) + '</div>') +
    (khoa || bai.cho_gd || BD.laGd ? '' : '<div style="order:7;margin-top:12px"><button class="btn gh" data-bdguigd="1" style="margin:0;min-height:44px;font-size:15px">👔 Gửi giám đốc duyệt</button>' +
      '<div style="font-size:13px;color:#667085;margin:6px 2px 0;line-height:1.45">Bài vào Việc cần làm của giám đốc. Giám đốc duyệt hay trả lại, nhóm Zalo Marketing nhận tin. Bạn vẫn tự duyệt được.</div></div>');
  var phai = chon.length ? '<div class="bd-phai" style="order:5"><div style="display:flex;align-items:baseline;margin:14px 2px 6px"><span style="font-size:13px;font-weight:800;color:#667085">XEM TRƯỚC TỪNG KÊNH</span>' +
      (chon.length > 1 ? '<span class="bd-chidt" style="margin-left:auto;font-size:13px;color:#98a2b3">vuốt ngang ‹ ›</span>' : '') + '</div>' +
      '<div class="bd-chonxem" style="gap:6px;flex-wrap:wrap;margin:0 0 8px">' + chon.map(function (k) {
        var on = k === xemK;
        return '<button data-bdxemk="' + k + '" aria-pressed="' + on + '" style="min-height:44px;border-radius:999px;border:1px solid ' + (on ? '#05323C' : '#e4e7ec') + ';background:' + (on ? '#E4F9FD' : '#fff') +
          ';padding:0 14px 0 6px;display:inline-flex;align-items:center;gap:6px;font:inherit;font-size:14px;font-weight:700;color:#101828;cursor:pointer">' + bdAvatar(k, 28) + bdKenh(k).ten + '</button>';
      }).join('') + '</div>' +
      '<div data-bdcuon="1" style="display:flex;align-items:flex-start;gap:10px;overflow-x:auto;scroll-snap-type:x mandatory;margin:0 -12px;padding:2px 12px 8px">' +
      chon.map(function (k) { return bdTheXem(bai, k, k === xemK); }).join('') + '</div></div>' : '';
  var html = '<div data-bdman="' + h(bai.name) + '"></div><div class="bd-2c"><div class="bd-trai">' + trai + '</div>' + phai + '</div>';
  var chan = bdNutDay(bai, dl.duyet);
  var b = frame('Bài đăng', html, { action: (bai.sua || bai.trang_thai === 'Đã hẹn giờ') ? '🗑' : '', footer: chan ? '<div id="bdDay" class="bd-hep" style="max-width:1048px">' + chan + '</div>' : '' });
  bdTheoDoi(bai);
  bdCaoChu(b);
  var nh = document.getElementById('vgbAct'); if (nh) { nh.setAttribute('aria-label', 'Huỷ bài'); nh.onclick = function () { bdHuy(); }; }
  var vf = document.querySelector('.vf'); if (vf) vf.onclick = function (e) { return bdMotLan(function () { return bdBamDay(e); }); };
  b.oninput = function (e) {
    var t = e.target, k;
    if (t.id === 'bdY') return bdHenLuu({ y_chinh: t.value });
    if (t.id === 'bdYc') return bdHenLuu({ yeu_cau_ai: t.value });
    if (t.getAttribute('data-bdthevao')) return bdHenLuu({ the_bai: t.value });
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
    if ((t = e.target.closest('[data-bdxemk]'))) return bdChonXem(b, t.getAttribute('data-bdxemk'));
    if ((t = e.target.closest('[data-bdthulai]'))) { var kt = t.getAttribute('data-bdthulai'); return bdMotLan(function () { return bdThuLai(kt); }); }
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
    if (e.target.closest('[data-bdchude]')) return bdSheetChonChuDe();
    if (e.target.closest('[data-bdsaobai]')) return bdMotLan(bdSaoBai);
    if ((t = e.target.closest('[data-bdcta]'))) {
      var cx = bdCacCta(BD.bai)[+t.getAttribute('data-bdcta')], dang = (bdGt('chan_bai') || []).slice();
      if (cx == null) return;
      return bdCtaDoi(dang.indexOf(cx) >= 0 ? dang.filter(function (y) { return y !== cx; }) : dang.concat([cx]));
    }
    if (e.target.closest('[data-bdctathem]')) {
      var o = b.querySelector('#bdCtaMoi'), v = o ? o.value.trim() : '';
      if (!v) return toast('Gõ câu chân bài trước, ví dụ giờ mở cửa hay số hotline.');
      return bdCtaDoi((bdGt('chan_bai') || []).filter(function (y) { return y !== v; }).concat([v]));
    }
    if (e.target.closest('[data-bdctamau]')) return bdMotLan(bdCtaLuuMau);
    if (e.target.closest('[data-bdguigd]')) return bdMotLan(bdGuiGd);
    if ((t = e.target.closest('[data-bdkieuchu]'))) return bdApKieu(b, t.getAttribute('data-k'), t.getAttribute('data-bdkieuchu'));
    if ((t = e.target.closest('[data-bdbieutuong]'))) return bdSheetBieuTuong(b, t.getAttribute('data-bdbieutuong'));
  };
  /* Kiểu chữ: nhớ vùng đang bôi đen của từng ô chữ, vì chạm nút trên điện thoại làm ô mất focus. */
  ['select', 'keyup', 'mouseup', 'touchend'].forEach(function (ev) {
    b.addEventListener(ev, function (e) { var k = e.target && e.target.getAttribute && e.target.getAttribute('data-bdchu'); if (k) BD.chon[k] = [e.target.selectionStart, e.target.selectionEnd]; });
  });
  b.addEventListener('mousedown', function (e) { if (e.target.closest('[data-bdkieuchu],[data-bdbieutuong]')) e.preventDefault(); });
  if (!BD.ngheChon && document.addEventListener) {
    BD.ngheChon = 1;
    document.addEventListener('selectionchange', function () {
      var a = document.activeElement, k = a && a.getAttribute && a.getAttribute('data-bdchu');
      if (k) BD.chon[k] = [a.selectionStart, a.selectionEnd];
    });
  }
  BD.chon = {};
}

/* ---------- v666: sao, chân bài mẫu, gửi giám đốc, kiểu chữ ---------- */

async function bdSaoBai() {
  var dl;
  try { dl = await api(BD_P + 'gan_sao', { ma: BD.bai.name, sao: BD.bai.sao ? 0 : 1 }); } catch (e) { return bdLoi(e); }
  BD.bai.sao = dl.sao;
  var t = document.querySelector('[data-bdsaobai]');
  if (t) { t.setAttribute('aria-pressed', dl.sao ? 'true' : 'false'); t.firstChild.textContent = dl.sao ? '★' : '☆'; t.lastChild.outerHTML = bdCongTac(dl.sao); }
  toast(dl.sao ? 'Đã gắn sao' : 'Đã bỏ sao');
}
/* Câu chân bài người soạn tự thêm cho bài này: lưu luôn vào mẫu của chủ đề để bài sau dùng lại. */
async function bdCtaLuuMau() {
  /* Lưu xong phần đang chờ (câu chân bài vừa tích) rồi mới đọc chân bài của bài. */
  if (!(await bdLuuChac())) return;
  var cd = BD.bai.chu_de;
  if (!cd) return;
  var moi = (cd.cta || []).concat((BD.bai.chan_bai || []).filter(function (x) { return (cd.cta || []).indexOf(x) < 0; }));
  try { await api(BD_P + 'chu_de_luu', { ma: cd.ma, ten: cd.ten, bieu_tuong: cd.bt, cta: JSON.stringify(moi) }); } catch (e) { return bdLoi(e); }
  toast('Đã lưu vào mẫu của chủ đề ' + cd.ten);
  var dl;
  try { dl = await api(BD_P + 'xem', { ma: BD.bai.name }); } catch (e) { return; }
  bdVeLai(dl);
}
async function bdGuiGd() {
  if (!(await confirmSheet('Gửi giám đốc duyệt?', 'Bài vào Việc cần làm của giám đốc. Giám đốc sửa chữ, đồng ý nội dung, duyệt đăng hoặc trả lại kèm góp ý; nhóm Zalo Marketing nhận tin.', 'Gửi giám đốc duyệt'))) return;
  if (!(await bdLuuChac())) return;
  var dl;
  try { dl = await api(BD_P + 'gui_giam_doc', { ma: BD.bai.name, ban_luu: BD.ban }); } catch (e) { return bdLoi(e); }
  if (dl.xung_dot) { toast('Bài vừa được sửa ở máy khác, đã nạp bản mới.', 4000); return bdVeLai(dl); }
  toast('Đã gửi giám đốc duyệt');
  bdVeLai(dl);
}

/* Chữ đậm, nghiêng kiểu YayText: đổi chữ cái Latinh sang ký tự toán học Unicode (sans-serif).
   Tách dấu tiếng Việt ra (NFD) rồi gắn lại sau chữ đã đổi, nên chữ có dấu vẫn giữ dấu;
   chữ Đ, đ không có bản đậm nên giữ nguyên. Đây là ký tự, không phải định dạng: Facebook
   không tìm được chữ kiểu này, máy đọc màn hình đọc sai, nên chỉ dùng cho tiêu đề, điểm nhấn. */
var BD_KIEU = { d: [0x1D5D4, 0x1D5EE, 0x1D7EC], n: [0x1D608, 0x1D622, 0], dn: [0x1D63C, 0x1D656, 0] };
function bdBoKieu(s) {
  return Array.from(String(s || '')).map(function (ch) {
    var c = ch.codePointAt(0);
    for (var k in BD_KIEU) {
      var g = BD_KIEU[k];
      if (c >= g[0] && c < g[0] + 26) return String.fromCharCode(65 + c - g[0]);
      if (c >= g[1] && c < g[1] + 26) return String.fromCharCode(97 + c - g[1]);
      if (g[2] && c >= g[2] && c < g[2] + 10) return String.fromCharCode(48 + c - g[2]);
    }
    return ch;
  }).join('').normalize('NFC');
}
function bdKieuChu(s, kieu) {
  var goc = bdBoKieu(s), g = BD_KIEU[kieu];
  if (!g) return goc;
  return Array.from(goc.normalize('NFD')).map(function (ch) {
    var c = ch.charCodeAt(0);
    if (ch.length === 1 && c >= 65 && c <= 90) return String.fromCodePoint(g[0] + c - 65);
    if (ch.length === 1 && c >= 97 && c <= 122) return String.fromCodePoint(g[1] + c - 97);
    if (ch.length === 1 && c >= 48 && c <= 57 && g[2]) return String.fromCodePoint(g[2] + c - 48);
    return ch;
  }).join('');
}
function bdOChu(b, k) { return b.querySelector('[data-bdchu="' + k + '"]'); }
function bdThayVung(b, k, doi) {
  var t = bdOChu(b, k);
  if (!t || t.readOnly) return;
  var c = BD.chon[k] || [t.value.length, t.value.length], dau = Math.min(c[0], t.value.length), cuoi = Math.min(c[1], t.value.length);
  var moi = doi(t.value.slice(dau, cuoi), dau === cuoi);
  if (moi == null) return;
  t.value = t.value.slice(0, dau) + moi + t.value.slice(cuoi);
  BD.chon[k] = [dau, dau + moi.length];
  try { t.focus({ preventScroll: true }); t.setSelectionRange(dau, dau + moi.length); } catch (e) { }
  t.dispatchEvent(new Event('input', { bubbles: true }));
}
function bdApKieu(b, k, kieu) {
  bdThayVung(b, k, function (vung, trong) {
    if (trong) { toast('Bôi đen chữ cần đổi kiểu rồi chạm lại nút.'); return null; }
    return bdKieuChu(vung, kieu);
  });
}
var BD_BIEU_TUONG = ['✨', '🌸', '🍓', '🍑', '🍋', '🥭', '🍫', '☕', '🧁', '🍰', '🎂', '🥐', '🎁', '🎉', '🎄', '🌙', '🔥', '⭐', '❤️', '🤍',
  '⏰', '📍', '🛒', '💬', '📞', '🚚', '👉', '✅', '•', '◦', '✦', '✧', '★', '☆', '→', '➤', '✿', '❀', '·', '×'];
function bdSheetBieuTuong(b, k) {
  var ov = crmMoSheet('<div style="font-size:17px;font-weight:800;margin:0 2px 4px">Biểu tượng</div>' +
    '<div style="font-size:13px;color:#667085;margin:0 2px 10px">Chạm để chèn vào chỗ con trỏ trong chữ ' + h(bdKenh(k).ten) + '.</div>' +
    '<div style="display:flex;flex-wrap:wrap;gap:4px">' + BD_BIEU_TUONG.map(function (x) {
      return '<button data-bdchen="' + h(x) + '" style="width:48px;height:48px;border:1px solid #e4e7ec;border-radius:10px;background:#fff;font-size:22px;cursor:pointer">' + h(x) + '</button>';
    }).join('') + '</div>');
  ov.onclick = function (e) {
    var t = e.target.closest('[data-bdchen]');
    if (!t) return;
    ov.remove();
    var x = t.getAttribute('data-bdchen');
    bdThayVung(b, k, function () { return x; });
  };
}

/* Ô chữ trong thẻ xem trước cao vừa đủ chữ (máy tính rộng hơn điện thoại nên số dòng khác). */
function bdCaoChu(b) {
  b.querySelectorAll('[data-bdchu]').forEach(function (t) {
    if (!t.scrollHeight) return;
    t.style.height = 'auto'; t.style.height = (t.scrollHeight + 2) + 'px';
  });
}

/* Máy tính: chạm tên kênh để đổi bài xem trước, không vẽ lại cả màn (giữ chữ đang gõ). */
function bdChonXem(b, k) {
  BD.xemK = k;
  b.querySelectorAll('[data-bdthe]').forEach(function (el) { el.classList.toggle('on', el.getAttribute('data-bdthe') === k); });
  b.querySelectorAll('[data-bdxemk]').forEach(function (el) {
    var on = el.getAttribute('data-bdxemk') === k;
    el.setAttribute('aria-pressed', on); el.style.background = on ? '#E4F9FD' : '#fff'; el.style.borderColor = on ? '#05323C' : '#e4e7ec';
  });
  bdCaoChu(b);
}

/* Hệ thống đang đăng (hoặc sắp đăng ngay): đọc lại bài vài giây một lần để hiện kết quả,
   tối đa 3 phút. Chỉ một vòng đọc cho mỗi lần mở; lượt trả lời muộn sau khi rời bài bị bỏ. */
function bdChoKetQua(bai) {
  var hen = bai.hen_luc ? new Date(String(bai.hen_luc).replace(' ', 'T')) : null;
  return (bai.kenh || []).some(function (x) {
    return x.tt === 'Đang đăng' || (x.tt === 'Đã hẹn giờ' && x.tu && (!hen || hen <= new Date()));
  });
}
function bdTheoDoi(bai) {
  var luot = ++BD.td;
  if (!bdChoKetQua(bai)) { BD.tdLan = 0; return; }
  if ((BD.tdMa !== bai.name)) { BD.tdMa = bai.name; BD.tdLan = 0; }
  if ((BD.tdLan = (BD.tdLan || 0) + 1) > 36) return;
  setTimeout(async function () {
    if (luot !== BD.td || !bdDangMo(bai.name)) return;
    var dl;
    try { dl = await api(BD_P + 'xem', { ma: bai.name }); } catch (e) { return; }
    if (luot !== BD.td) return;
    bdVeLai(dl);
  }, BD.tdCho);
}

async function bdThuLai(k) {
  var kn = bdKenh(k), x = (BD.bai.kenh || []).filter(function (y) { return y.k === k; })[0] || {};
  var hoi = x.loi ? 'Chỉ bấm khi đã mở ' + kn.ten + ' kiểm và chưa thấy bài, để không đăng hai lần.'
    : 'Hệ thống đăng ngay bài này lên ' + kn.ten + '. Đã đăng tay rồi thì bấm Đã đăng thay vì nút này.';
  if (!(await confirmSheet('Để hệ thống đăng lên ' + kn.ten + '?', hoi, 'Đăng lên ' + kn.ten))) return;
  var dl;
  try { dl = await api(BD_P + 'thu_lai', { ma: BD.bai.name, kenh: k }); } catch (e) { return bdLoi(e); }
  toast('Hệ thống đang đăng lên ' + kn.ten + '. Màn tự cập nhật khi xong.', 3500);
  bdVeLai(dl);
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
/* v670 (Codex #577, H8 loại 4 và 8): giá trị người dùng vừa chọn mà máy chủ chưa xác
   nhận (đang chờ hoặc đang gửi). Mọi phép bật tắt, đổi thứ tự, so "có đổi không" đọc
   qua bdGt, không đọc thẳng BD.bai: bấm chọn A rồi B khi lượt lưu A chưa về thì B
   tính từ [A], không từ bản cũ, nên không xoá mất A. Mỗi lần ghi mang một số thứ tự;
   máy chủ xác nhận đúng số đang giữ thì bỏ; lưu hỏng thì giữ (phần sửa được gửi lại);
   xung đột hay mở lại bài thì bỏ hết của bài đó. */
function bdDkGhi(ma, thay) {
  if (!ma) return;
  var d = BD.dk[ma] = BD.dk[ma] || {};
  Object.keys(thay || {}).forEach(function (k) { if (k !== 'ban') d[k] = { v: thay[k], so: ++BD.dkSo }; });
}
function bdGt(k) {
  var b = BD.bai || {}, d = BD.dk[b.name] || {};
  if (d[k]) return d[k].v;
  if (k === 'chu_de') return (b.chu_de || {}).ma || '';
  if (k === 'thu_tu_anh') return (b.anh || []).map(function (a) { return a.ten; });
  return b[k];
}
/* Ảnh theo thứ tự người dùng vừa xếp (kể cả lượt xếp chưa lưu xong). */
function bdAnhDangXep() {
  var anh = (BD.bai && BD.bai.anh) || [], thu = bdGt('thu_tu_anh') || [];
  var theo = {}; anh.forEach(function (a) { theo[a.ten] = a; });
  var ra = thu.filter(function (t) { return theo[t]; }).map(function (t) { return theo[t]; });
  anh.forEach(function (a) { if (thu.indexOf(a.ten) < 0) ra.push(a); });
  return ra;
}
function bdHenLuu(thay) {
  var ma = BD.bai && BD.bai.name;
  if (!ma) return;
  if (BD.thayMa !== ma) { BD.thay = {}; BD.thayMa = ma; }
  BD.thay = bdGop(BD.thay || {}, thay);
  bdDkGhi(ma, thay);
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
   dùng còn ở bài đó). Máy khác vừa sửa: tăng BD.xdLan[mã]; lượt nào của bài đó viết
   TRƯỚC lần xung đột này (người dùng chưa thấy bản mới) bị bỏ, không ghi đè bản mới;
   việc nào đang chờ lưu lúc xung đột xảy ra thì dừng (bdLuuChac).
   Lượt sau của chính bài đó lưu được thì xoá; mở lại bài từ lịch cũng xoá. Kết quả
   của bài A không bao giờ chặn việc trên bài B. */
function bdLuuNgay(veLai) {
  clearTimeout(BD.cho);
  var ma = BD.thayMa || (BD.bai && BD.bai.name);
  var thay = BD.thay; BD.thay = {};
  if ((!thay || !Object.keys(thay).length) && !veLai) return BD.chuoi;
  var xdTruoc = BD.xdLan[ma] || 0, soGui = {}, d0 = BD.dk[ma] || {};
  Object.keys(thay || {}).forEach(function (k) { if (d0[k]) soGui[k] = d0[k].so; });
  var boDk = function () { var d1 = BD.dk[ma]; if (d1) Object.keys(soGui).forEach(function (k) { if (d1[k] && d1[k].so === soGui[k]) delete d1[k]; }); };
  BD.chuoi = BD.chuoi.then(function () {}, function () {}).then(async function () {
    if (!ma) return;
    if ((BD.xdLan[ma] || 0) !== xdTruoc) { boDk(); return; }
    var dl;
    try { dl = await api(BD_P + 'luu', { ma: ma, ban_luu: BD.banMa[ma] != null ? BD.banMa[ma] : BD.ban, thay: JSON.stringify(thay || {}) }); }
    catch (e) {
      BD.loiMa[ma] = 1;
      /* Chỉ giữ lại để lưu lần sau khi người dùng vẫn ở đúng bài này. */
      if (BD.bai && BD.bai.name === ma && (BD.thayMa === ma || !Object.keys(BD.thay || {}).length)) { BD.thay = bdGop(thay || {}, BD.thay || {}); BD.thayMa = ma; }
      var o0 = document.getElementById('bdLuuChu'); if (o0) o0.textContent = 'Chưa lưu được'; bdLoi(e); return;
    }
    if (dl && dl.bai) BD.banMa[ma] = dl.bai.ban_luu;
    delete BD.loiMa[ma];
    boDk();
    if (dl.xung_dot) { BD.xdLan[ma] = (BD.xdLan[ma] || 0) + 1; delete BD.dk[ma]; }
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
   hoặc có xung đột xảy ra TRONG lúc việc này đang chờ (máy khác vừa sửa, đã nạp bản mới)
   thì dừng; người dùng xem lại bản mới rồi bấm lại là việc mới. Mỗi việc chỉ chạy một lượt (bdMotLan). */
async function bdLuuChac() {
  var ma = BD.bai && BD.bai.name, xdTruoc = BD.xdLan[ma] || 0;
  for (var vong = 0; vong < 50; vong++) {
    var c = bdLuuNgay();
    await c;
    if (c !== BD.chuoi) continue;
    if (BD.loiMa[ma]) break;
    if (BD.thayMa === ma && Object.keys(BD.thay || {}).length) continue;
    break;
  }
  if (!ma || !BD.bai || BD.bai.name !== ma) return false;
  if ((BD.xdLan[ma] || 0) !== xdTruoc) {
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
  bdDkGhi(ma, thay);
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
  var anh = bdAnhDangXep(), i = anh.map(function (a) { return a.ten; }).indexOf(ten);
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
      var on = bdGt('kieu') === x[0];
      return '<button data-bdchonkieu="' + x[0] + '" style="display:block;width:100%;text-align:left;min-height:56px;border:' + (on ? '2px solid #05323C' : '1px solid #e4e7ec') + ';border-radius:14px;background:' + (on ? '#E4F9FD' : '#fff') + ';font:inherit;padding:10px 12px;margin-bottom:8px;cursor:pointer">' +
        '<b style="font-size:15px">' + x[0] + (on ? ' ✓' : '') + '</b><div style="font-size:13px;color:#667085;line-height:1.45">' + x[1] + '</div></button>';
    }).join(''));
  ov.onclick = function (e) {
    var t = e.target.closest('[data-bdchonkieu]');
    if (!t) { if (e.target === ov) ov.remove(); return; }
    ov.remove();
    if (t.getAttribute('data-bdchonkieu') !== bdGt('kieu')) bdLuuVeLai({ kieu: t.getAttribute('data-bdchonkieu') });
  };
}
function bdSheetKenh() {
  var story = bdGt('kieu') === 'Story', chon = (bdGt('kenh_chon') || []).slice();
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
      var cu = (bdGt('kenh_chon') || []).join(','), moi = BD_KENH.filter(function (x) { return chon.indexOf(x.k) >= 0; }).map(function (x) { return x.k; });
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
    var tuK = (dl.bai.kenh || []).filter(function (x) { return x.tu; }).length, tayK = (dl.bai.kenh || []).length - tuK;
    toast(dl.bai.hen_luc && dl.bai.trang_thai === 'Đã hẹn giờ' ? 'Đã duyệt, hẹn ' + bdLucChu(dl.bai.hen_luc) + (tuK ? '. Tới giờ hệ thống tự đăng ' + tuK + ' kênh.' : '') :
      tuK ? 'Đã duyệt. Hệ thống đang đăng ' + tuK + ' kênh' + (tayK ? ', còn ' + tayK + ' kênh đăng tay bên dưới.' : '.') : 'Đã duyệt. Đăng tay từng kênh bên dưới.', 4000);
    return bdVeLai(dl);
  }
  if ((t = e.target.closest('[data-bddangngay]'))) {
    var soKenh = (bdGt('kenh_chon') || []).length;
    if (!(await confirmSheet('Đăng ngay ' + soKenh + ' kênh?', 'Bỏ giờ hẹn ' + bdLucChu(BD.bai.hen_luc) + '. Kênh đã nối hệ thống đăng ngay; kênh chưa nối chuyển sang Chờ đăng tay.', 'Đăng ngay ' + soKenh + ' kênh'))) return;
    if (!(await bdLuuChac())) return;
    try { dl = await api(BD_P + 'duyet', { ma: BD.bai.name, ban_luu: BD.ban, dang_ngay: 1 }); } catch (er) { return bdLoi(er); }
    if (dl.can_doc_nhac && dl.can_doc_nhac.length) {
      if (!(await confirmSheet('Đăng dù còn ' + dl.can_doc_nhac.length + ' điều cần để ý?', dl.can_doc_nhac.join('\n'), 'Vẫn đăng ngay'))) return bdVeLai(dl);
      try { dl = await api(BD_P + 'duyet', { ma: BD.bai.name, ban_luu: dl.bai.ban_luu, da_doc_nhac: 1, dang_ngay: 1 }); } catch (er) { return bdLoi(er); }
    }
    if (dl.xung_dot) { toast('Bài vừa được sửa ở máy khác, đã nạp bản mới. Xem lại rồi bấm Đăng ngay.', 4500); return bdVeLai(dl); }
    var tuN = (dl.bai.kenh || []).filter(function (x) { return x.tu; }).length, tayN = (dl.bai.kenh || []).length - tuN;
    toast(tuN ? 'Hệ thống đang đăng ' + tuN + ' kênh' + (tayN ? ', còn ' + tayN + ' kênh đăng tay bên dưới.' : '.') : 'Đã duyệt. Đăng tay từng kênh bên dưới.', 4000);
    return bdVeLai(dl);
  }
  if ((t = e.target.closest('[data-bdgui]'))) {
    if (!(await bdLuuChac())) return;
    try { dl = await api(BD_P + 'gui_duyet', { ma: BD.bai.name, ban_luu: BD.ban }); } catch (er) { return bdLoi(er); }
    if (dl.xung_dot) { toast('Bài vừa được sửa ở máy khác, đã nạp bản mới.', 4000); return bdVeLai(dl); }
    toast('Đã gửi Marketing duyệt'); return bdVeLai(dl);
  }
  if ((t = e.target.closest('[data-bdgdok]'))) {
    if (!(await confirmSheet('Đồng ý nội dung bài này?', 'Bài về Nháp để Marketing thêm ảnh, chọn giờ rồi duyệt đăng. Nhóm Zalo Marketing nhận tin.', 'Đồng ý nội dung'))) return;
    if (!(await bdLuuChac())) return;
    try { dl = await api(BD_P + 'gd_dong_y', { ma: BD.bai.name, ban_luu: BD.ban }); } catch (er) { return bdLoi(er); }
    if (dl.xung_dot) { toast('Bài vừa được sửa ở máy khác, đã nạp bản mới.', 4000); return bdVeLai(dl); }
    toast('Đã đồng ý nội dung, Marketing nhận tin trên Zalo'); return bdVeLai(dl);
  }
  if ((t = e.target.closest('[data-bdgdtra]'))) {
    var lyDo = await promptSheet('Trả lại bài: góp ý cho Marketing', 'Ví dụ: đoạn đầu dài quá, thêm nguồn gốc Ruby Chocolate, bỏ hashtag thứ ba.');
    if (lyDo == null) return;
    if (!lyDo) return toast('Ghi góp ý để Marketing biết cần sửa gì.');
    if (!(await bdLuuChac())) return;
    try { dl = await api(BD_P + 'gd_tra_lai', { ma: BD.bai.name, ban_luu: BD.ban, ly_do: lyDo }); } catch (er) { return bdLoi(er); }
    if (dl.xung_dot) { toast('Bài vừa được sửa ở máy khác, đã nạp bản mới.', 4000); return bdVeLai(dl); }
    toast('Đã trả lại, Marketing nhận góp ý trên Zalo'); return bdVeLai(dl);
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

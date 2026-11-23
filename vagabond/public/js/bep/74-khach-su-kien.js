/* ---------------- Khách sự kiện (v658)

   Anh Việt chọn A ngày 14/11/2026: mục Tiệc trên web nâng thành "Vé sự kiện"
   (tiệc, ra mắt món, diễn giả). Khách đăng ký giữ chỗ, nhận mã vé; Sales gọi
   xác nhận và thu tiền như trước. Màn này cho Quầy, Sales, Marketing xem danh
   sách khách từng sự kiện và bấm "Đã vào cửa" trên điện thoại.

   Mọi con số (số vé, đã vào cửa) do máy chủ tính (tiec_web.ds_su_kien,
   khach_su_kien), màn chỉ hiện. Quyền chặn thật ở máy chủ (tiec_web.QUYEN_SK);
   danh sách dưới đây chỉ để ẩn ô và phải trùng tuyệt đối danh sách máy chủ
   (ca thu_ve_su_kien_658 chốt). */
var QUYEN_SK = ['Sales User', 'Sales Manager', 'System Manager', 'VGB - Quản lý cửa hàng', 'Marketing', 'Giám đốc'];
function coQuyenSk() {
  return QUYEN_SK.some(function (v) { return hasRole(v); });
}

var skMo = '';
var skTim = '';
var SK_THU = ['Chủ Nhật', 'Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy'];
/* Màu chip trạng thái theo bảng chung: vàng chờ, xanh dương đang, xanh xong, xám huỷ. */
var SK_TT = {
  'Chờ xác nhận': { ic: '⏳', nen: '#fef3c7', chu: '#92400e' },
  'Đã xác nhận': { ic: '✅', nen: '#e0f2fe', chu: '#075985' },
  'Đã thanh toán': { ic: '💳', nen: '#dcfce7', chu: '#166534' },
  'Đã hủy': { ic: '✕', nen: '#fee2e2', chu: '#991b1b' },
};

function skNhanNgay(ngay, homNay) {
  if (!ngay) return 'CHƯA ĐẶT NGÀY';
  var p = String(ngay).split('-'), q = String(homNay || '').split('-');
  var d = new Date(+p[0], (+p[1] || 1) - 1, +p[2] || 1), n = new Date(+q[0], (+q[1] || 1) - 1, +q[2] || 1);
  var lech = Math.round((d - n) / 86400000);
  var dau = lech === 0 ? 'Hôm nay · ' : lech === 1 ? 'Ngày mai · ' : lech < 0 ? 'Đã qua · ' : '';
  return (dau + SK_THU[d.getDay()] + ' ' + p[2] + '/' + p[1]).toUpperCase();
}
function skKhop(r, q) {
  var t = String(q || '').trim();
  if (!t) return true;
  /* Codex #566 vòng 3: mã vé có thể toàn chữ số (8 ký tự đầu mã băm), nên luôn
     xét mã vé TRƯỚC rồi mới tới nhánh số điện thoại; hai nhánh cộng dồn. */
  var gon = t.replace(/\s+/g, '').toUpperCase();
  if (gon && String(r.ma_ve || '').toUpperCase().indexOf(gon) >= 0) return true;
  var so = t.replace(/[^0-9]/g, '');
  if (so.length >= 3 && so.length === t.replace(/[\s.+-]/g, '').length) return String(r.sdt || '').replace(/[^0-9]/g, '').indexOf(so) >= 0;
  return vgbKhop([r.ma_ve, r.ten, r.sdt], t);
}
function skChip(tt) {
  var m = SK_TT[tt] || SK_TT['Chờ xác nhận'];
  return '<span style="background:' + m.nen + ';color:' + m.chu + ';border-radius:999px;padding:2px 9px;font-size:13px;font-weight:700;white-space:nowrap">' +
    m.ic + ' ' + h(tt) + '</span>';
}

async function scrKhachSuKien() {
  var tieuDe = 'Khách sự kiện';
  if (!coQuyenSk()) {
    frame(tieuDe, '<div class="emp"><div class="e1">🔒</div><div>Màn này mở cho Quầy, Sales, Marketing và giám đốc.</div></div>');
    return;
  }
  frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc các sự kiện...</div></div>');
  var conMan = vgbManNay(scrKhachSuKien);
  var kq;
  try { kq = await api('vagabond.tiec_web.ds_su_kien', {}); }
  catch (e) { if (!conMan()) return; frame(tieuDe, '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e)) + ' Kiểm tra mạng rồi mở lại màn.</div></div>'); return; }
  if (!conMan()) return;
  var ds = kq.su_kien || [];
  var html = ds.length ? ds.map(function (s) {
    var cho = s.tong_cho ? s.so_ve + ' / ' + s.tong_cho + ' chỗ' : s.so_ve + ' vé';
    return '<button class="card" data-skmo="' + h(s.id) + '" style="display:block;width:calc(100% - 28px);text-align:left;padding:12px 13px;min-height:44px;border:0;font:inherit;color:inherit">' +
      '<div style="font-size:13px;font-weight:700;color:#0d9488;letter-spacing:.04em">' + h(skNhanNgay(s.ngay, kq.hom_nay)) + (s.gio ? ' · ' + h(s.gio) : '') + '</div>' +
      '<div style="font-size:16px;font-weight:700;margin-top:3px">' + h(s.ten) + '</div>' +
      '<div style="font-size:13.5px;color:#475467;margin-top:2px">' + h(s.loai) + ' · ' + s.so_dk + ' đăng ký · ' + h(cho) + '</div>' +
      '<div style="font-size:13.5px;margin-top:6px"><b>' + s.da_vao + '</b> / ' + s.so_ve + ' vé đã vào cửa' + (s.hien ? '' : ' · <span style="color:#98a2b3">đang ẩn trên web</span>') + '</div></button>';
  }).join('') : '<div class="emp"><div class="e1">🎟️</div><div>Chưa có sự kiện nào. Marketing tạo sự kiện ở Biên tập website, thẻ Sự kiện.</div></div>';
  html += '<div style="font-size:13px;color:#98a2b3;margin:10px 16px 18px;line-height:1.5">Khách đăng ký trên web nhận mã vé. Sales gọi xác nhận và thu tiền. Ở cửa, tìm mã vé hoặc số điện thoại rồi bấm Đã vào cửa.</div>';
  if (!conMan()) return;
  var than = frame(tieuDe, html);
  than.addEventListener('click', function (e) {
    var t = e.target.closest('[data-skmo]');
    if (t) { skMo = t.getAttribute('data-skmo'); skTim = ''; go(scrKhachSuKienCt); }
  });
}

async function scrKhachSuKienCt() {
  var tieuDe = 'Khách của sự kiện';
  if (!coQuyenSk() || !skMo) { go(scrKhachSuKien, true); return; }
  frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc danh sách khách...</div></div>');
  var kq;
  try { kq = await api('vagabond.tiec_web.khach_su_kien', { tiec_id: skMo }); }
  catch (e) { frame(tieuDe, '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e)) + ' Bấm quay lại rồi mở lại.</div></div>'); return; }
  var ds = kq.khach || [], tong = kq.tong || {};
  function veDs() {
    var loc = ds.filter(function (r) { return skKhop(r, skTim); });
    if (!loc.length) return '<div class="emp"><div class="e1">🔎</div><div>' + (ds.length ? 'Không có vé khớp. Thử mã vé hoặc 4 số cuối điện thoại.' : 'Chưa có khách đăng ký.') + '</div></div>';
    return loc.map(function (r) {
      var huy = r.trang_thai === 'Đã hủy';
      var nut = huy ? '' : r.da_vao
        ? '<div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:8px"><span style="color:#15803d;font-weight:700;font-size:14px">✓ Đã vào cửa' + (r.vao_luc ? ' lúc ' + h(r.vao_luc.slice(11, 16)) : '') + '</span>' +
          '<button class="btn gh" data-skbo="' + h(r.name) + '" style="margin:0;min-height:44px;padding:6px 12px;font-size:13px">Bỏ dấu</button></div>'
        : '<button class="btn" data-skvao="' + h(r.name) + '" style="margin:8px 0 0;width:100%;min-height:48px;font-size:15px">Đã vào cửa · ' + r.so_ve + ' vé</button>';
      return '<div class="card" data-skdong="' + h(r.name) + '" style="padding:12px 13px' + (huy ? ';opacity:.55' : '') + '">' +
        '<div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px"><b style="font-size:18px;letter-spacing:.06em">' + h(r.ma_ve) + '</b>' + skChip(r.trang_thai) + '</div>' +
        '<div style="font-size:15px;font-weight:700;margin-top:4px">' + h(r.ten) + ' · ' + r.so_ve + ' vé</div>' +
        '<div style="font-size:13.5px;margin-top:2px"><a href="tel:' + h(String(r.sdt || '').replace(/[^0-9+]/g, '')) + '">' + h(r.sdt) + '</a></div>' +
        (r.ghi_chu ? '<div style="font-size:13px;color:#475467;margin-top:4px">' + h(r.ghi_chu) + '</div>' : '') + nut + '</div>';
    }).join('');
  }
  var html = '<div class="card" style="padding:12px 13px;font-size:13.5px"><b style="font-size:20px">' + (tong.da_vao || 0) + '</b> / ' + (tong.so_ve || 0) +
    ' vé đã vào cửa · ' + (tong.so_dk || 0) + ' đăng ký</div>' +
    '<div style="margin:0 14px 8px"><input id="skTim" type="search" value="' + h(skTim) + '" placeholder="🔎 Mã vé, tên, số điện thoại" style="width:100%;min-height:44px;font-size:15px;padding:8px 12px;border:1px solid #d0d5dd;border-radius:10px"></div>' +
    '<div id="skDs">' + veDs() + '</div>';
  var than = frame(tieuDe, html);
  var o = document.getElementById('skTim');
  if (o) o.addEventListener('input', function () { skTim = o.value; document.getElementById('skDs').innerHTML = veDs(); });
  than.addEventListener('click', async function (e) {
    var t = e.target.closest('[data-skvao],[data-skbo]');
    if (!t || t.disabled) return;
    var ten = t.getAttribute('data-skvao') || t.getAttribute('data-skbo'), vao = t.hasAttribute('data-skvao');
    t.disabled = true;
    try {
      var moi = await api('vagabond.tiec_web.vao_cua', { ten: ten, co: vao ? 1 : 0 });
      ds = ds.map(function (r) { return r.name === ten ? moi : r; });
      toast(vao ? 'Đã ghi khách vào cửa' : 'Đã bỏ dấu vào cửa');
      go(scrKhachSuKienCt, true);
    } catch (er) { t.disabled = false; toast(errMsg(er)); }
  });
}

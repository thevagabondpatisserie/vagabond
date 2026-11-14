/* ---------- v657: biết máy chủ đã có bản app mới, tải lại cho kịp ----------

   Dễ báo 14/11/2026: phiếu tạm tính HDB-26-11-02668 in 13:11 có mã QR chỉ
   còn một góc, đúng lỗi v655 đã sửa và deploy 01:43 cùng ngày. Máy quầy để
   trang app mở từ hôm trước nên vẫn chạy bản cũ. App nạp mã một lần lúc mở
   trang, không biết máy chủ đã có bản mới, nên bản sửa không tới quầy cho tới
   khi có người tự tải lại.

   Cách làm: vài phút một lần (và mỗi lần quay lại thẻ app) hỏi máy chủ số
   bản đang cài (vagabond.phien_ban_app.hien_tai). Máy chủ mới hơn thì:
   - đang ở trang chủ, không có phiếu soạn dở: tự tải lại ngay;
   - đang làm dở một màn: hiện dải báo trên cùng, người dùng lưu xong việc
     rồi bấm Tải lại. Không tự tải giữa chừng làm mất đơn đang bấm.
   Mỗi số bản chỉ tự tải MỘT lần trong một phiên thẻ: tải xong mà mã vẫn cũ
   (bộ nhớ đệm) thì chỉ hiện dải báo, không tải lặp vô hạn. */

var BAN_MOI = { so: 0, luc: 0, dang: 0 };
var BAN_MOI_NHIP = 5 * 60 * 1000;

/* THUẦN: máy chủ có bản mới hơn bản đang chạy không. */
function banMoiCanTai(dangChay, mayChu) {
  var a = parseInt(dangChay, 10), b = parseInt(mayChu, 10);
  return isFinite(a) && isFinite(b) && b > 0 && b > a;
}

function banMoiDaThu(so) {
  try { return sessionStorage.getItem('vgb_ban_moi') === String(so); } catch (e) { return false; }
}
function banMoiGhiThu(so) {
  try { sessionStorage.setItem('vgb_ban_moi', String(so)); } catch (e) { }
}

/* Đứng ở trang chủ, không có phiếu soạn dở: tải lại không mất gì. */
function banMoiRanh() {
  if (!S || !S.stack || S.stack.length !== 1) return false;
  if (typeof scrHome !== 'function' || S.stack[0] !== scrHome) return false;
  return !(S.draft && (S.draft.items || []).length);
}

function banMoiTaiLai() {
  if (typeof sdLuuNgay === 'function') { try { sdLuuNgay(); } catch (e) { } }
  banMoiGhiThu(BAN_MOI.so);
  hardNav();
}

function banMoiDai() {
  var d = document.getElementById('vgbBanMoi');
  if (d) return;
  d = document.createElement('div');
  d.id = 'vgbBanMoi';
  d.setAttribute('role', 'status');
  d.setAttribute('style', 'position:fixed;top:0;left:0;right:0;z-index:2147483000;background:#fff7ed;' +
    'border-bottom:1px solid #fdba74;padding:8px 12px;display:flex;gap:10px;align-items:center;' +
    'font-size:14px;line-height:1.35;color:#7c2d12;box-shadow:0 2px 8px rgba(0,0,0,.08)');
  d.innerHTML = '<div style="flex:1;min-width:0">Hệ thống đã có bản app mới. Lưu xong việc đang làm rồi bấm Tải lại để dùng bản mới.</div>' +
    '<button type="button" id="vgbBanMoiTai" style="min-height:44px;min-width:96px;padding:0 14px;border:0;border-radius:10px;' +
    'background:#ea580c;color:#fff;font-size:15px;font-weight:700">🔄 Tải lại</button>';
  document.body.appendChild(d);
  document.getElementById('vgbBanMoiTai').onclick = banMoiTaiLai;
}

/* Quyết định sau khi biết số bản máy chủ. Trả về việc đã làm, để kiểm thử. */
function banMoiXuLy(mayChu) {
  if (!banMoiCanTai(APPVER, mayChu)) return 'giu';
  BAN_MOI.so = parseInt(mayChu, 10);
  if (banMoiRanh() && !banMoiDaThu(BAN_MOI.so)) { banMoiTaiLai(); return 'tai'; }
  banMoiDai();
  return 'bao';
}

async function banMoiKiem(ep) {
  if (BAN_MOI.dang || document.hidden) return;
  if (!ep && Date.now() - BAN_MOI.luc < BAN_MOI_NHIP) {
    /* Đã biết có bản mới thì mỗi nhịp xem lại đã về trang chủ chưa. */
    if (BAN_MOI.so) banMoiXuLy(BAN_MOI.so);
    return;
  }
  BAN_MOI.dang = 1;
  BAN_MOI.luc = Date.now();
  try {
    /* Gọi thẳng, không qua api(): lỗi phiên ở nhịp nền không được bật màn
       đăng nhập giữa lúc người dùng đang làm. */
    var r = await fetch('/api/method/vagabond.phien_ban_app.hien_tai?t=' + Date.now(),
      { credentials: 'same-origin', headers: { 'Accept': 'application/json' }, cache: 'no-store' });
    if (r.ok) {
      var j = await r.json();
      banMoiXuLy(j && j.message && j.message.appver);
    }
  } catch (e) { /* mất mạng: nhịp sau hỏi lại */ }
  BAN_MOI.dang = 0;
}

if (typeof document !== 'undefined' && document.addEventListener) {
  setInterval(function () { banMoiKiem(0); }, 60 * 1000);
  document.addEventListener('visibilitychange', function () { if (!document.hidden) banMoiKiem(0); });
}

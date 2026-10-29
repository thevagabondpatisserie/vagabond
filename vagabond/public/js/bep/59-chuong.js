/* ---------- Chuông thông báo (v619) ----------

Anh Việt 28/10/2026 chọn "một chuông gộp cả hai": chuông ở góc trên trang chủ, số
đỏ là việc đang chờ mình cộng tin chưa đọc. Bấm vào mở màn có hai thẻ: Thông báo
(chính các tin Zalo đã gửi cho bộ phận mình, xem lại không phải lục Zalo, bấm tin
là mở đúng màn) và Việc cần làm (màn đã có). Máy chủ lọc tin theo bộ phận, màn chỉ
vẽ: vagabond/chuong.py. */
var CH_SO = { luc: 0, kq: null };
var CH_MO = {};

/* Nút chuông trên thanh đầu màn gốc. Chỉ người đã đăng nhập mới có. */
function vgbNutChuong() {
  if (!S.user || S.user === 'Guest') return '<span class="ic"></span>';
  return '<button class="ic" id="vgbChuong" aria-label="Thông báo và việc cần làm" style="position:relative">' +
    '&#128276;<span id="vgbChuongSo" style="display:none;position:absolute;top:2px;right:0;min-width:17px;height:17px;' +
    'padding:0 4px;border-radius:9px;background:#dc2626;color:#fff;font-size:10.5px;font-weight:800;line-height:17px;' +
    'text-align:center;box-sizing:border-box"></span></button>';
}
window.vgbNutChuong = vgbNutChuong;

function chVeSo(kq) {
  var o = document.getElementById('vgbChuongSo');
  if (!o) return;
  var n = (kq && kq.tong) || 0;
  o.textContent = n > 99 ? '99+' : String(n);
  o.style.display = n ? '' : 'none';
}

/* Gắn nút và đeo số. Hỏi máy chủ tối đa một lần mỗi phút; hỏng thì im lặng. */
async function vgbGanChuong() {
  var nut = document.getElementById('vgbChuong');
  if (!nut) return;
  nut.onclick = function () { vgbGo('CHUONG'); };
  if (CH_SO.kq && Date.now() - CH_SO.luc < 60000) { chVeSo(CH_SO.kq); return; }
  try {
    var kq = await api('vagabond.chuong.dem', {});
    CH_SO = { luc: Date.now(), kq: kq };
    chVeSo(kq);
  } catch (e) { }
}
window.vgbGanChuong = vgbGanChuong;

function chLuc(s) {
  var t = String(s || '');
  return t.length >= 16 ? t.slice(8, 10) + '/' + t.slice(5, 7) + ' ' + t.slice(11, 16) : t;
}

/* Bấm "Mở" của một tin. Đường của chính app thì mở trong app; có tham số
   (vd ?mo=<mã phiếu>) thì tải lại đúng địa chỉ để màn đọc được tham số. */
function chMo(link) {
  var u;
  try { u = new URL(link, location.href); } catch (e) { return; }
  var cung = u.hostname === location.hostname || /(^|\.)thevagabondpatisserie\.com$/.test(u.hostname);
  if (!cung) { window.open(u.href, '_blank'); return; }
  var d = u.pathname.replace(/^\/+|\/+$/g, '');
  if (!u.search && VGB_DUONG[d]) { vgbGo(VGB_DUONG[d]); return; }
  location.href = u.pathname + u.search;
}

function chVe(kq, viec) {
  var ds = kq.ds || [];
  var moi = ds.filter(function (x) { return x.moi; }).length;
  var body = '<div style="display:flex;gap:8px;padding:12px 12px 4px">' +
    '<button class="chip on" style="flex:1;margin:0">🔔 Thông báo' + (moi ? ' · ' + moi + ' mới' : '') + '</button>' +
    '<button class="chip" id="chViec" style="flex:1;margin:0">📌 Việc cần làm' + (viec ? ' · ' + viec : '') + '</button></div>' +
    '<div style="padding:4px 14px 6px;font-size:12px;color:#8a90a0">Tin Zalo đã gửi cho bộ phận của bạn trong ' +
    (kq.so_ngay || 14) + ' ngày gần nhất. Bấm Mở để vào đúng màn.</div>';
  if (!kq.co_phong_ban) {
    body += '<div class="emp"><div class="e1">🏷️</div><div class="e2">Tài khoản của bạn chưa gắn phòng ban, nên máy chưa biết tin nào là của bạn. ' +
      'Nhờ quản trị gắn phòng ban ở màn Người dùng.</div></div>';
  } else if (!ds.length) {
    body += '<div class="emp"><div class="e1">📭</div><div class="e2">Chưa có tin nào cho bộ phận của bạn.</div></div>';
  } else {
    ds.forEach(function (x, i) {
      var mo = !!CH_MO[x.ten];
      var than = String(x.than || '');
      var dai = than.split('\n').length > 3 || than.length > 240;
      var hien = mo || !dai ? than : than.split('\n').slice(0, 3).join('\n').slice(0, 240) + '…';
      body += '<div class="card" data-chi="' + i + '" style="padding:12px 14px;' + (x.moi ? 'border-left:4px solid #0f766e;' : '') + '">' +
        '<div style="display:flex;justify-content:space-between;gap:8px;align-items:baseline">' +
        '<b style="font-size:14px;line-height:1.35">' + h(x.tieu_de) + '</b>' +
        '<span style="font-size:11.5px;color:#98a2b3;white-space:nowrap">' + h(chLuc(x.luc)) + '</span></div>' +
        (hien ? '<div style="font-size:13px;color:#475467;white-space:pre-line;margin-top:6px;line-height:1.5">' + h(hien) + '</div>' : '') +
        '<div style="display:flex;gap:8px;margin-top:8px">' +
        (dai ? '<button class="chip" data-chxem="' + i + '" style="margin:0">' + (mo ? 'Thu gọn' : 'Xem hết') + '</button>' : '') +
        (x.link ? '<button class="chip on" data-chmo="' + i + '" style="margin:0">Mở</button>' : '') +
        '</div></div>';
    });
    /* Codex 4404477923: tin cũ hơn không bị cắt mất, bấm là tải thêm. */
    if (kq.con_nua) body += '<div style="padding:4px 12px 16px"><button class="chip" id="chCuHon" style="margin:0;width:100%">Xem tin cũ hơn</button></div>';
  }
  var b = frame('Chuông thông báo', body);
  var nv = document.getElementById('chViec');
  if (nv) nv.onclick = function () { vgbGo('VCL'); };
  var nc = document.getElementById('chCuHon');
  if (nc) nc.onclick = async function () {
    nc.disabled = true;
    try {
      var r = await api('vagabond.chuong.thong_bao', { truoc: ds[ds.length - 1].luc });
      /* Codex 4407978626: máy chủ gộp từng trang riêng, tin gửi nhiều nhóm có thể nằm hai bên
         ranh trang. Gộp lại khi nối, cùng khoá với máy chủ (mã tin, tiêu đề, thân, đường mở). */
      var khoa = function (x) { return [x.ma_tin, x.tieu_de, x.than, x.link].join('\u0001'); };
      var da = {};
      ds.forEach(function (x) { da[khoa(x)] = 1; });
      kq.ds = ds.concat((r.ds || []).filter(function (x) { var k = khoa(x); if (da[k]) return false; da[k] = 1; return true; }));
      kq.con_nua = r.con_nua;
    } catch (e) { kq.con_nua = 1; }
    chVe(kq, viec);
  };
  b.onclick = function (e) {
    var t = e.target.closest('[data-chmo]');
    if (t) { chMo(ds[+t.getAttribute('data-chmo')].link); return; }
    t = e.target.closest('[data-chxem]');
    if (t) {
      var x = ds[+t.getAttribute('data-chxem')];
      CH_MO[x.ten] = !CH_MO[x.ten];
      chVe(kq, viec);
    }
  };
}

async function scrChuong() {
  frame('Chuông thông báo', '<div class="emp"><div class="e1">⏳</div><div class="e2">Đang gom tin của bạn...</div></div>');
  var kq, dem = null;
  try {
    var r = await Promise.all([api('vagabond.chuong.thong_bao', {}), api('vagabond.chuong.dem', {}).catch(function () { return null; })]);
    kq = r[0]; dem = r[1];
  } catch (e) {
    frame('Chuông thông báo', '<div class="emp"><div class="e1">⚠️</div><div class="e2">' +
      h((e && e.message) || 'Không gom được tin') + '</div></div>');
    return;
  }
  chVe(kq, (dem && dem.viec) || 0);
  /* Đã mở thẻ Thông báo là đã đọc, nhưng chỉ tới tin mới nhất ĐÃ HIỆN (máy chủ luôn
     trả hết tin chưa đọc); tin tới sau lúc mở màn vẫn là tin mới. */
  try {
    await api('vagabond.chuong.da_xem', { den: kq.moc_moi || '' });
    CH_SO = { luc: Date.now(), kq: { tong: (dem && dem.viec) || 0, viec: (dem && dem.viec) || 0, tin: 0 } };
  } catch (e) { }
}

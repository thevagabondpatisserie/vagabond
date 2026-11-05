/* ---------- v640 Biên tập menu (anh Việt duyệt mẫu 05/11/2026) ----------
   Bán hàng > Menu > Biên tập menu. MỖI ĐIỂM MỘT MENU (NVHTN nhỏ, ít món).
   Ba tab: Thứ tự (kéo thả nhóm, ẩn hiện nhóm trên web), Tuỳ chọn (Đá, Đường
   là nhóm riêng, chọn một, có mặc định, chọn nhóm món được áp), Topping (bảng
   tích topping x nhóm). Bấm một nhóm: kéo thả món, ẩn hiện món, xếp món mới;
   bấm một món: mô tả trên web, chuyển nhóm, tắt riêng tuỳ chọn hay topping.
   Mọi thay đổi tự lưu vào BẢN NHÁP (khách chưa thấy); màn Xem và xuất bản
   đưa nháp lên trang bàn và màn Tính tiền cùng lúc, có quay về bản trước.
   Giá chỉ xem: sửa giá ở danh mục, Bảng giá điểm bán (anh Việt chốt).
   Máy chủ: vagabond/bien_tap_menu.py. */

var BTM = null, BTM_DIEM = '', BTM_TAB = 'thu_tu', BTM_NHOM = '', BTM_MON = '', BTM_TIM = '';
var BTM_HEN = null, BTM_CHO_LUU = 0, BTM_DANG_LUU = null;
var BTM_TAB_DS = [['thu_tu', 'Thứ tự'], ['tuy_chon', 'Tuỳ chọn'], ['topping', 'Topping']];

function coQuyenBtm() { return coQuyenGmbQr(); }

/* THUẦN: đưa phần tử ở vị trí tu tới vị trí den, trả mảng mới. */
function btmDoiCho(ds, tu, den) {
  var ra = (ds || []).slice();
  if (tu < 0 || tu >= ra.length || den < 0 || den >= ra.length || tu === den) return ra;
  var x = ra.splice(tu, 1)[0];
  ra.splice(den, 0, x);
  return ra;
}
/* THUẦN: thả ở độ cao y thì dòng tu đứng ở vị trí nào (đếm dòng khác có tâm cao hơn y). */
function btmViTri(tam, y, tu) {
  var n = 0;
  for (var j = 0; j < tam.length; j++) if (j !== tu && tam[j] < y) n++;
  return n;
}
/* THUẦN: mã nhóm mới không trùng, dựng từ tên. */
function btmMaNhom(ten, daCo) {
  var s = String(ten || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd')
    .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 30) || 'nhom';
  var ma = 'n-' + s, k = 2;
  while ((daCo || []).indexOf(ma) >= 0) ma = 'n-' + s + '-' + (k++);
  return ma;
}
/* THUẦN, trùng bien_tap_menu.nhom_cua_mon / tc_cua_mon / tp_cua_mon của máy chủ. */
function btmNhomCua(menu, ma, goc) {
  var nuoc = (menu.nhom || []).filter(function (g) { return g.loai === 'nuoc'; });
  for (var i = 0; i < nuoc.length; i++) if ((nuoc[i].mon || []).indexOf(ma) >= 0) return nuoc[i];
  if (goc) for (var j = 0; j < nuoc.length; j++) if (nuoc[j].goc === goc) return nuoc[j];
  return null;
}
function btmTcCua(menu, m) {
  if (!m || m.khong_pha) return [];
  var g = btmNhomCua(menu, m.ma, m.goc); if (!g) return [];
  return (menu.tuy_chon || []).filter(function (t) { return (t.ap || []).indexOf(g.ma) >= 0; });
}
function btmTpCua(menu, m) {
  if (!m || m.khong_pha) return [];
  var g = btmNhomCua(menu, m.ma, m.goc); if (!g) return [];
  return Object.keys(menu.topping || {}).filter(function (tp) { return (menu.topping[tp] || []).indexOf(g.ma) >= 0; });
}
function btmMon(ma) { return ((BTM && BTM.d.mon) || []).filter(function (x) { return x.ma === ma; })[0] || null; }
function btmTp(ma) { return ((BTM && BTM.d.topping) || []).filter(function (x) { return x.ma === ma; })[0] || null; }
function btmNhom(ma) { return ((BTM && BTM.d.nhap.nhom) || []).filter(function (g) { return g.ma === ma; })[0] || null; }
function btmRieng(ma) { var r = BTM.d.nhap.mon || (BTM.d.nhap.mon = {}); return r[ma] || (r[ma] = {}); }
function btmChuaXep() {
  var da = {};
  BTM.d.nhap.nhom.forEach(function (g) { (g.mon || []).forEach(function (m) { da[m] = 1; }); });
  return BTM.d.mon.filter(function (x) { return !da[x.ma]; });
}

/* ---------- lưu nháp: mọi thay đổi gom lại, 0,6 giây sau gửi một lần ---------- */
function btmDoi(veLai) {
  BTM_CHO_LUU++;
  if (BTM_HEN) clearTimeout(BTM_HEN);
  BTM_HEN = setTimeout(btmLuu, 600);
  btmBang();
  if (veLai !== false && BTM.ve) BTM.ve();
}
function btmLuu() {
  BTM_HEN = null;
  if (!BTM) return Promise.resolve();
  var bt = BTM;
  /* TUẦN TỰ: lần lưu sau chỉ gửi khi lần trước đã xong, và gửi nội dung MỚI NHẤT lúc
     đó. Máy chủ ghi nguyên bản nháp không kiểm phiên, nên hai lần chạy song song có
     thể để lần cũ về sau ghi đè bản mới (Codex PR #543 vòng 2). */
  var truoc = BTM_DANG_LUU || Promise.resolve();
  var p = truoc.then(async function () {
    var dot = BTM_CHO_LUU;
    try {
      var kq = await api('vagabond.bien_tap_menu.luu_nhap', { diem: bt.d.diem, noi_dung: JSON.stringify(bt.d.nhap) });
      if (dot === BTM_CHO_LUU) { bt.d.thay_doi = kq.thay_doi || []; bt.loi = ''; BTM_CHO_LUU = 0; }
    } catch (e) {
      bt.loi = (e && e.message) || 'Chưa lưu được bản nháp. Kiểm tra mạng rồi sửa lại một chỗ bất kỳ.';
      toast(bt.loi, 6000);
    }
    btmBang();
  });
  BTM_DANG_LUU = p;
  p.then(function () { if (BTM_DANG_LUU === p) BTM_DANG_LUU = null; });
  return p;
}
/* Chờ mọi lần lưu nháp xong: lần đang hẹn giờ thì gửi ngay, lần đã gửi mà máy
   chủ chưa trả lời thì đợi (Codex PR #543: trước đây màn Xem chỉ xét lần đang
   hẹn giờ, nên dựng với số thay đổi cũ hoặc xuất bản bản nháp cũ). Trả true khi
   bản nháp trên máy chủ đã khớp màn hình. */
async function btmChoLuu() {
  for (var i = 0; i < 6; i++) {
    if (BTM_HEN) { clearTimeout(BTM_HEN); await btmLuu(); continue; }
    if (BTM_DANG_LUU) { await BTM_DANG_LUU; continue; }
    break;
  }
  return !BTM_HEN && !BTM_DANG_LUU && !!BTM && !BTM.loi;
}
/* Thanh vàng "Bản nháp" vẽ lại tại chỗ, không vẽ lại cả màn (giữ con trỏ trong ô đang gõ). */
function btmBangHtml() {
  var so = (BTM.d.thay_doi || []).length;
  var dang = BTM_HEN || BTM_CHO_LUU;
  var cau = dang ? 'Đang lưu bản nháp...' : (BTM.loi ? BTM.loi : (so ? so + ' thay đổi so với menu đang chạy' : 'Giống hệt menu đang chạy'));
  return '<div id="btmBang" style="display:flex;align-items:center;gap:10px;background:' + (so || dang ? '#fff4e0;border:1px solid #f3d39a' : '#f6f8fc;border:1px solid #e6e9f0') + ';border-radius:14px;padding:10px 12px;margin-bottom:12px">' +
    '<div style="flex:1;font-size:13px;color:' + (so || dang ? '#8a5a00' : '#6b7280') + ';line-height:1.35"><b style="display:block;font-size:14px;color:' + (so || dang ? '#5c3c00' : '#16181d') + '">' +
    (so || dang ? 'Bản nháp, khách chưa thấy' : 'Menu đang chạy') + '</b>' + h(cau) + '</div>' +
    '<button type="button" data-btmxuat style="flex:none;border:0;background:#50DBF2;color:#05323C;font-weight:700;font-size:14px;border-radius:12px;padding:10px 14px;min-height:44px;cursor:pointer">Xem và xuất bản</button></div>';
}
function btmBang() {
  var cu = document.getElementById('btmBang');
  if (!cu) return;
  var tam = document.createElement('div'); tam.innerHTML = btmBangHtml();
  var moi = tam.querySelector('#btmBang');
  if (!moi) return;
  cu.setAttribute('style', moi.getAttribute('style'));
  cu.innerHTML = moi.innerHTML;
}

/* ---------- kéo thả: giữ ≡ rồi kéo, dòng nổi lên, thả là đổi thứ tự ---------- */
function btmGanKeo(goc, chonHang, xong) {
  goc.addEventListener('pointerdown', function (e) {
    /* Đang lọc bằng ô tìm thì không kéo: thứ tự các dòng đang thấy không phải
       thứ tự thật của nhóm (Codex PR #543). */
    if (goc.getAttribute('data-dang-loc')) return;
    var hd = e.target && e.target.closest && e.target.closest('[data-keo]'); if (!hd) return;
    var hang = hd.closest(chonHang); if (!hang) return;
    var ds = Array.prototype.slice.call(goc.querySelectorAll(chonHang));
    var tu = ds.indexOf(hang); if (tu < 0) return;
    var tam = ds.map(function (r) { var b = r.getBoundingClientRect(); return b.top + b.height / 2; });
    var y0 = e.clientY, den = tu;
    if (e.preventDefault) e.preventDefault();
    try { hd.setPointerCapture(e.pointerId); } catch (x) { }
    hang.style.position = 'relative'; hang.style.zIndex = '3';
    hang.style.boxShadow = '0 10px 26px rgba(11,124,147,.28)'; hang.style.outline = '1.5px solid #0FB5CE';
    function di(ev) {
      var dy = ev.clientY - y0;
      hang.style.transform = 'translateY(' + dy + 'px)';
      den = btmViTri(tam, tam[tu] + dy, tu);
    }
    function tha() {
      goc.removeEventListener('pointermove', di); goc.removeEventListener('pointerup', tha); goc.removeEventListener('pointercancel', tha);
      hang.style.transform = ''; hang.style.boxShadow = ''; hang.style.outline = ''; hang.style.zIndex = '';
      if (den !== tu) xong(tu, den);
    }
    goc.addEventListener('pointermove', di); goc.addEventListener('pointerup', tha); goc.addEventListener('pointercancel', tha);
  });
}
var BTM_KEO = '<span data-keo style="flex:none;width:30px;height:44px;display:grid;place-content:center;gap:3px;touch-action:none;cursor:grab" aria-label="Giữ để kéo">' +
  '<i style="display:block;width:16px;height:2px;background:#b8bfcc;border-radius:2px"></i><i style="display:block;width:16px;height:2px;background:#b8bfcc;border-radius:2px"></i><i style="display:block;width:16px;height:2px;background:#b8bfcc;border-radius:2px"></i></span>';
function btmCongTac(attr, bat, nhan) {
  return '<button type="button" ' + attr + ' role="switch" aria-checked="' + (bat ? 'true' : 'false') + '" aria-label="' + h(nhan) + '" style="flex:none;width:52px;height:44px;border:0;background:none;padding:0;cursor:pointer">' +
    '<span style="display:block;position:relative;width:44px;height:26px;border-radius:13px;margin:auto;background:' + (bat ? '#12a150' : '#cfd4de') + '">' +
    '<span style="position:absolute;top:3px;' + (bat ? 'right:3px' : 'left:3px') + ';width:20px;height:20px;border-radius:50%;background:#fff"></span></span></button>';
}
function btmChip(attr, chu, on, phu) {
  return '<button type="button" ' + attr + ' style="display:inline-flex;align-items:center;gap:6px;min-height:40px;border:1px solid ' + (on ? '#7FE5F6' : '#dfe3ec') +
    ';background:' + (on ? '#E4F9FD' : '#fff') + ';color:' + (on ? '#0B7C93' : '#4a5061') + ';border-radius:999px;padding:7px 13px;font-size:14px;font-weight:' + (on ? 700 : 500) +
    ';margin:0 6px 6px 0;cursor:pointer">' + chu + (phu || '') + '</button>';
}
function btmAnh(src, co) {
  co = co || 44;
  return '<span style="flex:none;width:' + co + 'px;height:' + co + 'px;border-radius:10px;overflow:hidden;background:#eef0f5;display:block">' +
    (src ? '<img src="' + h(src) + '" alt="" loading="lazy" style="width:100%;height:100%;object-fit:cover" onerror="this.style.display=\'none\'">' : '') + '</span>';
}

/* ---------- màn chính ---------- */
async function scrBienTapMenu() {
  if (!coQuyenBtm()) { frame('Biên tập menu', '<div class="emp"><div class="e1">🔒</div><div>Chỉ quản lý cửa hàng mới biên tập menu được.</div></div>'); return; }
  if (BTM && BTM.d && (!BTM_DIEM || BTM.d.diem === BTM_DIEM)) return btmVe();
  frame('Biên tập menu', '<div class="emp"><div class="e1">⏳</div><div>Đang tải menu...</div></div>');
  try { BTM = { d: await api('vagabond.bien_tap_menu.mo', { diem: BTM_DIEM || '' }), loi: '' }; }
  catch (e) { frame('Biên tập menu', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Chưa tải được menu. Thử lại sau.') + '</div></div>'); return; }
  BTM_DIEM = BTM.d.diem;
  btmVe();
}
async function btmDoiDiem(ma) {
  /* Lưu chưa được thì ở lại điểm đang sửa, giữ nguyên thay đổi để quản lý thử lại;
     đổi điểm lúc này là mất thay đổi chưa lưu (Codex PR #543 vòng 3). */
  if (!(await btmChoLuu())) return toast('Bản nháp của ' + ((BTM && BTM.d.ten_diem) || 'điểm này') + ' chưa lưu được. Kiểm tra mạng, sửa lại một chỗ bất kỳ để lưu rồi mới đổi điểm.', 6000);
  BTM_DIEM = ma; BTM = null;
  return scrBienTapMenu();
}
function btmVe() {
  BTM.ve = btmVe;
  var d = BTM.d, html = '';
  if ((d.cac_diem || []).length > 1) {
    html += '<div style="display:flex;gap:8px;overflow-x:auto;padding:0 2px 10px">' +
      d.cac_diem.map(function (x) { return btmChip('data-btmdiem="' + h(x.ma) + '"', h(x.ten), x.ma === d.diem); }).join('') + '</div>';
  }
  html += btmBangHtml();
  html += '<div style="display:flex;gap:6px;background:#fff;padding:6px;border-radius:14px;margin-bottom:12px">' +
    BTM_TAB_DS.map(function (t) {
      var on = BTM_TAB === t[0];
      return '<button type="button" data-btmtab="' + t[0] + '" style="flex:1;min-height:42px;border:0;border-radius:10px;font-size:14px;font-weight:700;cursor:pointer;background:' + (on ? '#E4F9FD' : 'transparent') + ';color:' + (on ? '#0B7C93' : '#6b7280') + '">' + t[1] + '</button>';
    }).join('') + '</div>';
  if (BTM_TAB === 'tuy_chon') html += btmTabTuyChon();
  else if (BTM_TAB === 'topping') html += btmTabTopping();
  else html += btmTabThuTu();
  var b = frame('Biên tập menu · ' + d.ten_diem, html);
  b.addEventListener('click', btmBamChinh);
  var ds = b.querySelector('#btmDsNhom');
  if (ds) btmGanKeo(ds, '[data-btmhang]', function (tu, den) { d.nhap.nhom = btmDoiCho(d.nhap.nhom, tu, den); btmDoi(); });
}
function btmTabThuTu() {
  var d = BTM.d, cx = btmChuaXep().length;
  var html = '<div class="sec">Nhóm trên web và màn Tính tiền</div><div class="card" id="btmDsNhom">';
  d.nhap.nhom.forEach(function (g) {
    var so = g.loai === 'banh' ? 'lấy theo tồn trên tủ trong ngày' : ((g.mon || []).length + ' món');
    html += '<div data-btmhang data-ma="' + h(g.ma) + '" style="display:flex;align-items:center;gap:8px;padding:6px 10px;border-bottom:1px solid #f0f2f6;background:#fff">' +
      BTM_KEO + '<div style="flex:1;min-width:0;padding:6px 0"><b style="display:block;font-size:15px">' + h(g.ten) + '</b>' +
      '<small style="display:block;font-size:12.5px;color:#8a8f9c;margin-top:2px">' + h(so) + (g.hien ? '' : ' · đang ẩn trên web') + '</small></div>' +
      btmCongTac('data-btmhien="' + h(g.ma) + '"', !!g.hien, 'Hiện nhóm ' + g.ten + ' trên web') +
      (g.loai === 'nuoc' ? '<button type="button" data-btmnhom="' + h(g.ma) + '" aria-label="Mở nhóm ' + h(g.ten) + '" style="flex:none;width:36px;min-height:44px;border:0;background:none;color:#c3c8d4;font-size:24px;cursor:pointer">&#8250;</button>' : '<span style="width:36px"></span>') +
      '</div>';
  });
  html += '</div>' +
    '<div style="font-size:12.5px;color:#8a8f9c;line-height:1.5;padding:0 4px 12px">Giữ ≡ rồi kéo để đổi thứ tự. Công tắc tắt: nhóm ẩn trên web, quầy vẫn bán được.</div>' +
    '<button type="button" class="btn" data-btmthemnhom style="background:#fff;color:#0B7C93;border:1.5px dashed #7FE5F6">+ Thêm nhóm</button>';
  if (cx) html += '<div style="font-size:13px;color:#c07800;margin:12px 4px">' + cx + ' món mới chưa xếp vào nhóm nào, đang ẩn trên web. Mở một nhóm để xếp.</div>';
  return html;
}
function btmTabTuyChon() {
  var d = BTM.d, nuoc = d.nhap.nhom.filter(function (g) { return g.loai === 'nuoc'; });
  var html = '';
  (d.nhap.tuy_chon || []).forEach(function (t, i) {
    html += '<div class="card" style="padding:14px;margin-bottom:12px">' +
      '<div style="display:flex;align-items:center;gap:8px"><b style="font-size:16px;flex:1">' + h(t.ten) + '</b>' +
      '<span style="font-size:12px;font-weight:600;color:#0B7C93;background:#E4F9FD;border-radius:999px;padding:3px 8px">chọn một</span>' +
      '<button type="button" data-btmtcten="' + i + '" style="border:0;background:none;color:#0B7C93;font-weight:600;font-size:13px;min-height:40px;cursor:pointer">Đổi tên</button>' +
      '<button type="button" data-btmtcxoa="' + i + '" style="border:0;background:none;color:#b3261e;font-weight:600;font-size:13px;min-height:40px;cursor:pointer">Xoá</button></div>' +
      '<div style="font-size:12.5px;color:#8a8f9c;margin:4px 0 10px;line-height:1.4">Khách chọn đúng một mức. Bấm một mức để đặt làm mặc định (★, sáng sẵn khi mở món, không ghi lên bill).</div>' +
      t.muc.map(function (x, k) {
        return btmChip('data-btmmuc="' + i + ':' + k + '"', (x === t.mac_dinh ? '★ ' : '') + h(x), true,
          '<span data-btmmucxoa="' + i + ':' + k + '" aria-label="Bỏ mức ' + h(x) + '" style="margin-left:4px;color:#8a8f9c;font-weight:400">×</span>');
      }).join('') +
      btmChip('data-btmmucthem="' + i + '"', '+ Thêm mức', false) +
      '<div style="font-size:12px;font-weight:700;color:#8a8f9c;text-transform:uppercase;letter-spacing:.3px;margin:10px 0 6px">Áp cho nhóm món</div>' +
      nuoc.map(function (g) { return btmChip('data-btmtcap="' + i + ':' + h(g.ma) + '"', h(g.ten), (t.ap || []).indexOf(g.ma) >= 0); }).join('') +
      '<div style="font-size:12.5px;color:#8a8f9c">Tự bỏ qua món đóng chai, lon, set trà.</div></div>';
  });
  html += '<button type="button" class="btn" data-btmtcthem style="background:#fff;color:#0B7C93;border:1.5px dashed #7FE5F6">+ Thêm nhóm tuỳ chọn</button>' +
    '<div style="font-size:12.5px;color:#8a8f9c;line-height:1.5;padding:10px 4px">Ví dụ: Nóng hay đá, Độ ngọt kem. Tuỳ chọn không cộng tiền; món có tính tiền thì khai ở tab Topping.</div>';
  return html;
}
function btmTabTopping() {
  var d = BTM.d, nuoc = d.nhap.nhom.filter(function (g) { return g.loai === 'nuoc'; });
  if (!d.topping.length) return '<div class="card" style="padding:14px;font-size:13.5px;color:#6b7280;line-height:1.5">Điểm này chưa có topping nào. Topping là món trong nhóm "Topping cho món nước" của danh mục, có giá trong bảng giá điểm bán.</div>';
  var html = '<div style="font-size:12.5px;color:#8a8f9c;line-height:1.45;padding:0 4px 10px">Topping là món trong nhóm "Topping cho món nước", giá lấy từ bảng giá điểm bán. Tích để topping hiện khi khách chọn món thuộc nhóm đó.</div>' +
    '<div class="card" style="overflow-x:auto"><table style="border-collapse:collapse;font-size:13px;min-width:100%">' +
    '<tr><th style="text-align:left;padding:8px 12px;font-size:11.5px;color:#8a8f9c;position:sticky;left:0;background:#fff">Topping</th>' +
    nuoc.map(function (g) { return '<th style="padding:8px 4px;font-size:11.5px;color:#8a8f9c;white-space:nowrap">' + h(g.ten) + '</th>'; }).join('') + '</tr>';
  d.topping.forEach(function (t) {
    var ap = (d.nhap.topping || {})[t.ma] || [];
    html += '<tr><td style="padding:8px 12px;border-top:1px solid #f3f4f8;position:sticky;left:0;background:#fff"><b style="display:block;font-size:13.5px">' + h(t.ten) + '</b><small style="color:#8a8f9c">+' + money(t.gia) + ' đ</small></td>' +
      nuoc.map(function (g) {
        var on = ap.indexOf(g.ma) >= 0;
        return '<td style="text-align:center;border-top:1px solid #f3f4f8"><button type="button" data-btmtp="' + h(t.ma) + ':' + h(g.ma) + '" role="checkbox" aria-checked="' + (on ? 'true' : 'false') + '" aria-label="' + h(t.ten) + ' cho ' + h(g.ten) + '" style="width:44px;height:44px;border:0;background:none;cursor:pointer">' +
          '<span style="display:inline-grid;place-items:center;width:22px;height:22px;border-radius:6px;border:1.5px solid ' + (on ? '#0FB5CE;background:#0FB5CE' : '#cfd4de;background:#fff') + '">' +
          (on ? '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>' : '') + '</span></button></td>';
      }).join('') + '</tr>';
  });
  html += '</table></div><div style="font-size:12.5px;color:#8a8f9c;line-height:1.5;padding:8px 4px">Thêm topping mới hoặc đổi giá topping vẫn ở danh mục món và Bảng giá điểm bán.</div>';
  return html;
}
async function btmBamChinh(e) {
  var t = e.target, d = BTM.d, x;
  if ((x = t.closest('[data-btmxuat]'))) return go(scrBtmXuat);
  if ((x = t.closest('[data-btmdiem]'))) { if (x.getAttribute('data-btmdiem') !== d.diem) await btmDoiDiem(x.getAttribute('data-btmdiem')); return; }
  if ((x = t.closest('[data-btmtab]'))) { BTM_TAB = x.getAttribute('data-btmtab'); return btmVe(); }
  if ((x = t.closest('[data-btmhien]'))) { var g = btmNhom(x.getAttribute('data-btmhien')); if (g) { g.hien = g.hien ? 0 : 1; btmDoi(); } return; }
  if ((x = t.closest('[data-btmnhom]'))) { BTM_NHOM = x.getAttribute('data-btmnhom'); BTM_TIM = ''; return go(scrBtmNhom); }
  if (t.closest('[data-btmthemnhom]')) {
    var ten = await hoiChu('Thêm nhóm', 'Tên nhóm hiện trên web, ví dụ Trà sữa, Nước ép.', '', { bat_buoc: true });
    if (!ten) return;
    if (d.nhap.nhom.some(function (g2) { return g2.ten.toLowerCase() === ten.toLowerCase(); })) return toast('Đã có nhóm tên này.');
    d.nhap.nhom.push({ ma: btmMaNhom(ten, d.nhap.nhom.map(function (g2) { return g2.ma; })), ten: ten.slice(0, 40), loai: 'nuoc', hien: 1, goc: '', mon: [] });
    return btmDoi();
  }
  /* tab Tuỳ chọn */
  if ((x = t.closest('[data-btmmucxoa]'))) {
    var p = x.getAttribute('data-btmmucxoa').split(':'), tc = d.nhap.tuy_chon[+p[0]];
    if (!tc) return;
    if (tc.muc.length <= 1) return toast('Nhóm tuỳ chọn phải còn ít nhất một mức. Muốn bỏ hẳn thì bấm Xoá nhóm.');
    var bo = tc.muc.splice(+p[1], 1)[0];
    if (tc.mac_dinh === bo) tc.mac_dinh = '';
    return btmDoi();
  }
  if ((x = t.closest('[data-btmmuc]'))) {
    var q = x.getAttribute('data-btmmuc').split(':'), tc2 = d.nhap.tuy_chon[+q[0]];
    if (!tc2) return;
    var muc = tc2.muc[+q[1]];
    tc2.mac_dinh = tc2.mac_dinh === muc ? '' : muc;
    return btmDoi();
  }
  if ((x = t.closest('[data-btmmucthem]'))) {
    var tc3 = d.nhap.tuy_chon[+x.getAttribute('data-btmmucthem')];
    var muc2 = await hoiChu('Thêm mức', 'Ví dụ: 30% đá, Ít ngọt.', '', { bat_buoc: true });
    if (!muc2 || !tc3) return;
    if (tc3.muc.some(function (y) { return y.toLowerCase() === muc2.toLowerCase(); })) return toast('Đã có mức này.');
    if (tc3.muc.length >= 12) return toast('Mỗi nhóm tối đa 12 mức.');
    tc3.muc.push(muc2.slice(0, 40));
    return btmDoi();
  }
  if ((x = t.closest('[data-btmtcap]'))) {
    var r = x.getAttribute('data-btmtcap'), i = +r.slice(0, r.indexOf(':')), ma = r.slice(r.indexOf(':') + 1), tc4 = d.nhap.tuy_chon[i];
    if (!tc4) return;
    var k = (tc4.ap || []).indexOf(ma);
    tc4.ap = tc4.ap || [];
    if (k >= 0) tc4.ap.splice(k, 1); else tc4.ap.push(ma);
    return btmDoi();
  }
  if ((x = t.closest('[data-btmtcten]'))) {
    var tc5 = d.nhap.tuy_chon[+x.getAttribute('data-btmtcten')];
    var moi = tc5 && await hoiChu('Đổi tên nhóm tuỳ chọn', '', tc5.ten, { bat_buoc: true });
    if (!moi) return;
    var cu = tc5.ten; tc5.ten = moi.slice(0, 40);
    Object.keys(d.nhap.mon || {}).forEach(function (m) {
      var tt = d.nhap.mon[m].tat_tc || []; var j = tt.indexOf(cu); if (j >= 0) tt[j] = tc5.ten;
    });
    return btmDoi();
  }
  if ((x = t.closest('[data-btmtcxoa]'))) {
    var tc6 = d.nhap.tuy_chon[+x.getAttribute('data-btmtcxoa')];
    if (!tc6 || !(await confirmSheet('Xoá nhóm tuỳ chọn', 'Bỏ nhóm "' + tc6.ten + '" khỏi menu. Khách và quầy không còn chọn được các mức của nhóm này.', 'Xoá nhóm', true))) return;
    d.nhap.tuy_chon.splice(d.nhap.tuy_chon.indexOf(tc6), 1);
    return btmDoi();
  }
  if (t.closest('[data-btmtcthem]')) {
    var ten2 = await hoiChu('Thêm nhóm tuỳ chọn', 'Ví dụ: Nóng hay đá, Độ ngọt kem.', '', { bat_buoc: true });
    if (!ten2) return;
    if ((d.nhap.tuy_chon || []).some(function (y) { return y.ten.toLowerCase() === ten2.toLowerCase(); })) return toast('Đã có nhóm tuỳ chọn tên này.');
    (d.nhap.tuy_chon = d.nhap.tuy_chon || []).push({ ten: ten2.slice(0, 40), muc: ['Bình thường'], mac_dinh: 'Bình thường',
      ap: d.nhap.nhom.filter(function (g3) { return g3.loai === 'nuoc'; }).map(function (g3) { return g3.ma; }) });
    return btmDoi();
  }
  /* tab Topping */
  if ((x = t.closest('[data-btmtp]'))) {
    var s = x.getAttribute('data-btmtp'), tp = s.slice(0, s.indexOf(':')), gm = s.slice(s.indexOf(':') + 1);
    var bang = d.nhap.topping || (d.nhap.topping = {});
    var ap = bang[tp] || (bang[tp] = []);
    var k2 = ap.indexOf(gm);
    if (k2 >= 0) ap.splice(k2, 1); else ap.push(gm);
    return btmDoi();
  }
}

/* ---------- một nhóm: kéo thả món, ẩn hiện, xếp món mới ---------- */
function scrBtmNhom() {
  if (!BTM) return scrBienTapMenu();
  BTM.ve = scrBtmNhom;
  var g = btmNhom(BTM_NHOM);
  if (!g) { back(); return; }
  var an = BTM.d.nhap.an || (BTM.d.nhap.an = []);
  var html = btmBangHtml() + '<div class="card" style="padding:12px 14px;display:flex;flex-direction:row;align-items:center;gap:10px">' +
    '<div id="btmNhomGhi" style="flex:1;font-size:13px;color:#6b7280;line-height:1.4">' + (g.mon || []).length + ' món · kéo ≡ để xếp thứ tự trên web</div>' +
    '<button type="button" data-btmdoiten style="border:0;background:none;color:#0B7C93;font-weight:600;font-size:13.5px;min-height:44px;cursor:pointer">Đổi tên</button>' +
    ((g.mon || []).length ? '' : '<button type="button" data-btmxoanhom style="border:0;background:none;color:#b3261e;font-weight:600;font-size:13.5px;min-height:44px;cursor:pointer">Xoá nhóm</button>') + '</div>' +
    /* Ô tìm nhanh đầu danh sách (AGENTS mục 2b.5): gõ tên hoặc mã, bỏ dấu. */
    '<input class="tin" id="btmTimMon" type="search" autocomplete="off" enterkeyhint="search" placeholder="🔎 Tìm món theo tên hoặc mã" value="' + h(BTM_TIM) + '" style="margin:0 0 9px">' +
    '<div id="btmTimTrong" style="display:none;font-size:12.5px;color:#b45309;padding:6px 2px 9px;line-height:1.55">Không có món nào khớp. Xoá bớt chữ rồi tìm lại.</div>' +
    '<div class="card" id="btmDsMon">';
  (g.mon || []).forEach(function (ma) {
    var m = btmMon(ma); if (!m) return;
    var tc = btmTcCua(BTM.d.nhap, m).length, tp = btmTpCua(BTM.d.nhap, m).length;
    var rieng = (BTM.d.nhap.mon || {})[ma] || {};
    tc -= (rieng.tat_tc || []).length; tp -= (rieng.tat_tp || []).length;
    var tom = money(m.gia) + ' đ' + (m.khong_pha ? ' · đóng sẵn, không hỏi đá đường' : (' · ' + (tc > 0 ? tc + ' tuỳ chọn' : 'không tuỳ chọn') + ' · ' + (tp > 0 ? tp + ' topping' : 'không topping'))) +
      (m.ban_web ? '' : ' · tắt bán web hôm nay');
    html += '<div data-btmhang data-ma="' + h(ma) + '" data-btmtim="' + h(m.ten + ' ' + ma) + '" style="display:flex;align-items:center;gap:8px;padding:6px 10px;border-bottom:1px solid #f0f2f6;background:#fff">' + BTM_KEO +
      '<button type="button" data-btmmon="' + h(ma) + '" style="flex:1;min-width:0;display:flex;align-items:center;gap:10px;border:0;background:none;text-align:left;padding:4px 0;cursor:pointer">' +
      btmAnh(m.anh) + '<span style="flex:1;min-width:0"><b style="display:block;font-size:15px;color:#16181d">' + h(m.ten) + '</b><small style="display:block;font-size:12.5px;color:#8a8f9c;margin-top:2px;line-height:1.35">' + h(tom) + '</small></span></button>' +
      btmCongTac('data-btman="' + h(ma) + '"', an.indexOf(ma) < 0, 'Hiện ' + m.ten + ' trên web') + '</div>';
  });
  html += '</div>';
  var cx = btmChuaXep();
  if (cx.length) {
    html += '<div class="sec">Món mới chưa xếp · đang ẩn trên web</div><div class="card">' +
      cx.map(function (m) {
        return '<div data-btmtim="' + h(m.ten + ' ' + m.ma) + '" style="display:flex;align-items:center;gap:10px;padding:8px 12px;border-bottom:1px solid #f0f2f6">' + btmAnh(m.anh) +
          '<div style="flex:1;min-width:0"><b style="display:block;font-size:14.5px">' + h(m.ten) + '</b><small style="color:#8a8f9c;font-size:12.5px">' + money(m.gia) + ' đ' + (m.goc ? ' · ' + h(m.goc) : '') + '</small></div>' +
          '<button type="button" data-btmxep="' + h(m.ma) + '" style="flex:none;border:1.5px solid #7FE5F6;background:#E4F9FD;color:#0B7C93;font-weight:700;font-size:13px;border-radius:10px;padding:8px 10px;min-height:44px;cursor:pointer">Xếp vào ' + h(g.ten) + '</button></div>';
      }).join('') + '</div>';
  }
  var b = frame(g.ten, html);
  b.addEventListener('click', btmBamNhom);
  var ds = b.querySelector('#btmDsMon');
  if (ds) btmGanKeo(ds, '[data-btmhang]', function (tu, den) { g.mon = btmDoiCho(g.mon, tu, den); btmDoi(); });
  var o = b.querySelector('#btmTimMon');
  if (o) { o.addEventListener('input', function () { BTM_TIM = o.value; btmLocMon(b, g); }); btmLocMon(b, g); }
}
/* Lọc các dòng món (đã xếp và chưa xếp) theo ô tìm, không vẽ lại màn (giữ con
   trỏ trong ô). Đang lọc thì ẩn tay cầm ≡ và khoá kéo thả. */
function btmLocMon(b, g) {
  var q = String(BTM_TIM || '').trim(), thay = 0;
  [].slice.call(b.querySelectorAll('[data-btmtim]')).forEach(function (r) {
    var hop = !q || vgbKhop(r.getAttribute('data-btmtim'), q);
    r.style.display = hop ? 'flex' : 'none';
    if (hop) thay++;
  });
  var ds = b.querySelector('#btmDsMon');
  if (ds) {
    if (q) ds.setAttribute('data-dang-loc', '1'); else ds.removeAttribute('data-dang-loc');
    [].slice.call(ds.querySelectorAll('[data-keo]')).forEach(function (k) { k.style.visibility = q ? 'hidden' : ''; });
  }
  var ghi = b.querySelector('#btmNhomGhi');
  if (ghi) ghi.textContent = (g.mon || []).length + ' món · ' + (q ? 'đang lọc, xoá ô tìm để kéo thả' : 'kéo ≡ để xếp thứ tự trên web');
  var tr = b.querySelector('#btmTimTrong');
  if (tr) tr.style.display = (q && !thay) ? '' : 'none';
}
async function btmBamNhom(e) {
  var t = e.target, g = btmNhom(BTM_NHOM), x;
  if (!g) return;
  var an = BTM.d.nhap.an || (BTM.d.nhap.an = []);
  if ((x = t.closest('[data-btmxuat]'))) return go(scrBtmXuat);
  if ((x = t.closest('[data-btman]'))) {
    var ma = x.getAttribute('data-btman'), k = an.indexOf(ma);
    if (k >= 0) an.splice(k, 1); else an.push(ma);
    return btmDoi();
  }
  if ((x = t.closest('[data-btmmon]'))) { BTM_MON = x.getAttribute('data-btmmon'); return go(scrBtmMon); }
  if ((x = t.closest('[data-btmxep]'))) { (g.mon = g.mon || []).push(x.getAttribute('data-btmxep')); return btmDoi(); }
  if (t.closest('[data-btmdoiten]')) {
    var ten = await hoiChu('Đổi tên nhóm', '', g.ten, { bat_buoc: true });
    if (!ten) return;
    if (BTM.d.nhap.nhom.some(function (y) { return y !== g && y.ten.toLowerCase() === ten.toLowerCase(); })) return toast('Đã có nhóm tên này.');
    g.ten = ten.slice(0, 40);
    return btmDoi();
  }
  if (t.closest('[data-btmxoanhom]')) {
    if ((g.mon || []).length) return toast('Chuyển hết món sang nhóm khác rồi mới xoá được nhóm.');
    if (!(await confirmSheet('Xoá nhóm', 'Bỏ nhóm "' + g.ten + '" khỏi menu.', 'Xoá nhóm', true))) return;
    var nh = BTM.d.nhap;
    nh.nhom = nh.nhom.filter(function (y) { return y !== g; });
    (nh.tuy_chon || []).forEach(function (tc) { tc.ap = (tc.ap || []).filter(function (m) { return m !== g.ma; }); });
    Object.keys(nh.topping || {}).forEach(function (tp) { nh.topping[tp] = nh.topping[tp].filter(function (m) { return m !== g.ma; }); });
    btmDoi(false);
    return back();
  }
}

/* ---------- một món: mô tả web, chuyển nhóm, tắt riêng tuỳ chọn và topping ---------- */
function scrBtmMon() {
  if (!BTM) return scrBienTapMenu();
  BTM.ve = scrBtmMon;
  var m = btmMon(BTM_MON);
  if (!m) { back(); return; }
  var nh = BTM.d.nhap, g = btmNhomCua(nh, m.ma, ''), rieng = (nh.mon || {})[m.ma] || {};
  var an = (nh.an || []).indexOf(m.ma) >= 0;
  var html = btmBangHtml() + '<div class="card" style="padding:14px;margin-bottom:12px">' +
    '<div style="display:flex;gap:12px;align-items:center">' + btmAnh(m.anh, 64) +
    '<div style="flex:1;min-width:0;font-size:13px;color:#8a8f9c;line-height:1.45">Ảnh và tên lấy từ danh mục món.<br>' + (g ? 'Nhóm ' + h(g.ten) : 'Chưa xếp vào nhóm nào, đang ẩn trên web') + '</div>' +
    btmCongTac('data-btman1', !an && !!g, 'Hiện món trên web') + '</div>' +
    '<label for="btmMoTa" style="display:block;font-size:12px;font-weight:700;color:#8a8f9c;text-transform:uppercase;letter-spacing:.3px;margin:14px 0 6px">Mô tả ngắn trên web</label>' +
    '<textarea id="btmMoTa" class="tin" rows="3" maxlength="300" placeholder="' + h(m.mo_ta || 'Một câu giới thiệu món cho khách') + '" style="margin:0">' + h(rieng.mo_ta || '') + '</textarea>' +
    '<div style="font-size:12px;color:#8a8f9c;margin-top:4px">Để trống thì dùng mô tả trong danh mục món.</div>' +
    '<div style="font-size:12px;font-weight:700;color:#8a8f9c;text-transform:uppercase;letter-spacing:.3px;margin:14px 0 6px">Giá</div>' +
    '<div style="display:flex;justify-content:space-between;align-items:center;background:#f6f8fc;border-radius:12px;padding:11px 12px;font-size:14px"><span>' + money(m.gia) + ' đ · ' + h(BTM.d.ten_diem) + '</span><span style="color:#8a8f9c;font-size:12.5px">Sửa ở Bảng giá điểm bán</span></div></div>';
  html += '<div class="card" style="padding:14px;margin-bottom:12px"><b style="font-size:15px">Nhóm trên web</b><div style="margin-top:8px">' +
    nh.nhom.filter(function (y) { return y.loai === 'nuoc'; }).map(function (y) { return btmChip('data-btmchuyen="' + h(y.ma) + '"', h(y.ten), g && g.ma === y.ma); }).join('') + '</div></div>';
  if (m.khong_pha) {
    html += '<div class="card" style="padding:14px;font-size:13.5px;color:#6b7280;line-height:1.5">Món đóng sẵn (chai, lon, set trà): không hỏi tuỳ chọn, không kèm topping.</div>';
  } else {
    var tc = btmTcCua(nh, m), tp = btmTpCua(nh, m);
    html += '<div class="card" style="padding:14px"><b style="font-size:15px">Tuỳ chọn</b>' +
      '<div style="font-size:12.5px;color:#8a8f9c;margin:4px 0 8px">' + (g ? 'Theo nhóm ' + h(g.ten) + '. Bấm để tắt riêng cho món này.' : 'Xếp món vào một nhóm trước.') + '</div>' +
      (tc.length ? tc.map(function (t) { var tat = (rieng.tat_tc || []).indexOf(t.ten) >= 0; return btmChip('data-btmtattc="' + h(t.ten) + '"', tat ? '<s>' + h(t.ten) + '</s>' : h(t.ten), !tat); }).join('') : '<div style="font-size:13px;color:#8a8f9c">Nhóm này chưa áp tuỳ chọn nào.</div>') +
      '<b style="display:block;font-size:15px;margin-top:12px">Topping</b>' +
      (tp.length ? '<div style="margin-top:8px">' + tp.map(function (ma) { var x = btmTp(ma); var tat = (rieng.tat_tp || []).indexOf(ma) >= 0; return btmChip('data-btmtattp="' + h(ma) + '"', tat ? '<s>' + h(x ? x.ten : ma) + '</s>' : h(x ? x.ten : ma), !tat); }).join('') + '</div>'
        : '<div style="font-size:13px;color:#8a8f9c;margin-top:6px">Nhóm này chưa áp topping nào.</div>') +
      ((rieng.tat_tc || []).length || (rieng.tat_tp || []).length ? '<div style="font-size:12.5px;color:#c07800;margin-top:6px">Món này tắt riêng: ' + h([].concat(rieng.tat_tc || [], (rieng.tat_tp || []).map(function (ma) { var x = btmTp(ma); return x ? x.ten : ma; })).join(', ')) + '</div>' : '') +
      '</div>';
  }
  var b = frame(m.ten, html, { footer: '<button class="btn" id="btmMonXong">Xong</button>' });
  b.addEventListener('click', btmBamMon);
  var o = b.querySelector('#btmMoTa');
  if (o) o.addEventListener('input', function () {
    var r = btmRieng(m.ma); r.mo_ta = String(o.value || '').slice(0, 300);
    if (!r.mo_ta) delete r.mo_ta;
    btmDoi(false);
  });
  var xong = document.getElementById('btmMonXong');
  if (xong) xong.onclick = function () { back(); };
}
function btmBamMon(e) {
  var t = e.target, m = btmMon(BTM_MON), nh = BTM.d.nhap, x;
  if (!m) return;
  if ((x = t.closest('[data-btmxuat]'))) return go(scrBtmXuat);
  if (t.closest('[data-btman1]')) {
    if (!btmNhomCua(nh, m.ma, '')) return toast('Chọn nhóm cho món ở phần Nhóm trên web trước.');
    var an = nh.an || (nh.an = []), k = an.indexOf(m.ma);
    if (k >= 0) an.splice(k, 1); else an.push(m.ma);
    return btmDoi();
  }
  if ((x = t.closest('[data-btmchuyen]'))) {
    var den = btmNhom(x.getAttribute('data-btmchuyen'));
    if (!den) return;
    nh.nhom.forEach(function (y) { if (y.mon) y.mon = y.mon.filter(function (ma) { return ma !== m.ma; }); });
    (den.mon = den.mon || []).push(m.ma);
    return btmDoi();
  }
  if ((x = t.closest('[data-btmtattc]'))) {
    var r = btmRieng(m.ma), ten = x.getAttribute('data-btmtattc'), ds = r.tat_tc || (r.tat_tc = []), j = ds.indexOf(ten);
    if (j >= 0) ds.splice(j, 1); else ds.push(ten);
    return btmDoi();
  }
  if ((x = t.closest('[data-btmtattp]'))) {
    var r2 = btmRieng(m.ma), tp = x.getAttribute('data-btmtattp'), ds2 = r2.tat_tp || (r2.tat_tp = []), j2 = ds2.indexOf(tp);
    if (j2 >= 0) ds2.splice(j2, 1); else ds2.push(tp);
    return btmDoi();
  }
}

/* ---------- xem và xuất bản ---------- */
async function scrBtmXuat() {
  if (!BTM) return scrBienTapMenu();
  var daLuu = await btmChoLuu();
  if (!BTM) return scrBienTapMenu();
  BTM.ve = scrBtmXuat;
  var d = BTM.d, nh = d.nhap, an = nh.an || [];
  var xem = nh.nhom.filter(function (g) { return g.hien; }).map(function (g) {
    if (g.loai === 'banh') return '<div style="padding:8px 12px;border-bottom:1px solid rgba(255,255,255,.08);font-size:12.5px;color:#3FD8CD">' + h(g.ten) + ' <span style="color:rgba(255,255,255,.5)">· theo tồn trong ngày</span></div>';
    var mon = (g.mon || []).filter(function (ma) { return an.indexOf(ma) < 0 && btmMon(ma); });
    if (!mon.length) return '';
    return '<div style="padding:8px 12px 2px;font-size:12.5px;color:#3FD8CD">' + h(g.ten) + ' · ' + mon.length + '</div>' +
      mon.slice(0, 3).map(function (ma) { var m = btmMon(ma); return '<div style="display:flex;justify-content:space-between;gap:8px;padding:4px 12px;font-size:13px;color:#fff"><span>' + h(m.ten) + '</span><span style="color:#29BDB3">' + money(m.gia) + '</span></div>'; }).join('') +
      (mon.length > 3 ? '<div style="padding:2px 12px 8px;font-size:12px;color:rgba(255,255,255,.5)">và ' + (mon.length - 3) + ' món nữa</div>' : '<div style="height:6px"></div>');
  }).join('');
  var td = d.thay_doi || [];
  /* Bản nháp chưa lưu được lên máy chủ: không cho xuất bản (máy chủ chỉ có bản cũ). */
  var choXuat = daLuu && td.length;
  var html = (daLuu ? '' : '<div style="background:#fdecec;border:1px solid #f5c2c2;color:#9b1c1c;border-radius:12px;padding:10px 12px;margin-bottom:12px;font-size:13.5px;line-height:1.4">Bản nháp chưa lưu được nên chưa xuất bản được. Kiểm tra mạng, quay lại sửa một chỗ bất kỳ để lưu lại rồi mở màn này.</div>') +
    '<div class="sec">Trang bàn như khách sẽ thấy · ' + h(d.ten_diem) + '</div>' +
    '<div style="background:#000;border-radius:16px;overflow:hidden;margin-bottom:12px;padding:4px 0">' + xem + '</div>' +
    '<div class="sec">' + (td.length ? td.length + ' thay đổi so với menu đang chạy' : 'Không có thay đổi nào') + '</div>' +
    '<div class="card">' + (td.length ? td.slice(0, 60).map(function (c) { return '<div style="padding:10px 12px;border-bottom:1px solid #f0f2f6;font-size:13.5px;line-height:1.4">' + h(c) + '</div>'; }).join('') +
      (td.length > 60 ? '<div style="padding:10px 12px;font-size:13px;color:#8a8f9c">và ' + (td.length - 60) + ' thay đổi nữa</div>' : '')
      : '<div style="padding:12px;font-size:13.5px;color:#6b7280">Bản nháp giống hệt menu đang chạy.</div>') + '</div>';
  if ((d.lich_su || []).length) {
    html += '<div class="sec">Các bản đã xuất bản</div><div class="card">' + d.lich_su.map(function (r, i) {
      return '<div style="display:flex;align-items:center;gap:10px;padding:10px 12px;border-bottom:1px solid #f0f2f6"><div style="flex:1;min-width:0;font-size:13px;line-height:1.4"><b>Phiên ' + r.phien + '</b> · ' + h(String(r.luc).slice(0, 16)) + '<br><span style="color:#8a8f9c">' + h(String(r.thay_doi || '').split('\n')[0]) + '</span></div>' +
        (i ? '<button type="button" data-btmkhoiphuc="' + r.phien + '" style="flex:none;border:1.5px solid #cfd4de;background:#fff;color:#4a5061;font-weight:600;font-size:13px;border-radius:10px;padding:8px 10px;min-height:44px;cursor:pointer">Quay về bản này</button>' : '<span style="font-size:12px;color:#12a150;font-weight:700">Đang chạy</span>') + '</div>';
    }).join('') + '</div>';
  }
  var b = frame('Xem và xuất bản', html, { footer: '<div style="display:flex;gap:10px"><button class="btn gh" id="btmBoNhap" style="flex:1;margin:0"' + (td.length ? '' : ' disabled') + '>Bỏ bản nháp</button>' +
    '<button class="btn" id="btmXuatBan" style="flex:2;margin:0"' + (choXuat ? '' : ' disabled') + '>Xuất bản</button></div>' });
  b.addEventListener('click', async function (e) {
    var x = e.target.closest('[data-btmkhoiphuc]'); if (!x) return;
    var p = +x.getAttribute('data-btmkhoiphuc');
    if (!(await confirmSheet('Quay về phiên ' + p, 'Trang bàn và màn Tính tiền của ' + d.ten_diem + ' chạy lại menu phiên ' + p + '. Bản nháp đang sửa dở bị thay bằng bản đó.', 'Quay về bản này'))) return;
    busy(true);
    try { await api('vagabond.bien_tap_menu.khoi_phuc', { diem: d.diem, phien: p }); if (typeof posQuenTc === 'function') posQuenTc(); }
    catch (er) { busy(false); return toast((er && er.message) || 'Chưa quay về được, thử lại.', 5000); }
    busy(false); toast('Đã quay về phiên ' + p + '.');
    BTM = null; back();
  });
  var nb = document.getElementById('btmBoNhap');
  if (nb) nb.onclick = async function () {
    if (!(await confirmSheet('Bỏ bản nháp', 'Mọi thay đổi chưa xuất bản sẽ mất, bản nháp trở về đúng menu đang chạy.', 'Bỏ bản nháp', true))) return;
    busy(true);
    try { await api('vagabond.bien_tap_menu.bo_nhap', { diem: d.diem }); }
    catch (er) { busy(false); return toast((er && er.message) || 'Chưa bỏ được bản nháp, thử lại.', 5000); }
    busy(false); BTM = null; back();
  };
  var xb = document.getElementById('btmXuatBan');
  if (xb) xb.onclick = async function () {
    if (!(await btmChoLuu())) return toast('Bản nháp chưa lưu được nên chưa xuất bản. Kiểm tra mạng rồi thử lại.', 5000);
    if (!(await confirmSheet('Xuất bản menu', 'Trang gọi món tại bàn và màn Tính tiền của ' + d.ten_diem + ' đổi ngay theo bản nháp (' + td.length + ' thay đổi).', 'Xuất bản'))) return;
    busy(true);
    var kq;
    try { kq = await api('vagabond.bien_tap_menu.xuat_ban', { diem: d.diem }); if (typeof posQuenTc === 'function') posQuenTc(); }
    catch (er) { busy(false); return toast((er && er.message) || 'Chưa xuất bản được, thử lại.', 5000); }
    busy(false);
    toast('Đã xuất bản menu phiên ' + kq.phien + ' cho ' + d.ten_diem + '.', 5000);
    BTM = null; back();
  };
}

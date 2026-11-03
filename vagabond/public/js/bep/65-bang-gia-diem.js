/* ---------------- Bảng giá theo điểm bán (v631)

   Anh Việt 02/11/2026, duyệt mẫu "Điểm bán tự nhận theo tài khoản và bảng giá
   riêng NVH" (ảnh 3): NVH bán khoảng 36 món một tháng, giá khác District 1.
   Khai một lượt trên một bảng, hoặc tải Excel về điền rồi nạp lại, không phải
   mở từng món. Ô để trống là điểm đó bán giá chung.

   Máy chủ giữ bảng giá (một Price List bán ra cho mỗi điểm bật Giá riêng) và
   tự tính lại giá theo điểm khi lưu bill quầy, nên giá ở đây là giá thật quầy
   thu, không ai sửa tay trên màn Tính tiền được. Mỗi lần đổi giá máy ghi vết
   trên món: ai đổi, lúc nào, giá cũ, giá mới. */
var BGD = { ma: '', kq: null, chip: 'da_ban', tim: '', sua: {}, nhap: {} };

/* Đổi điểm đang xem. Giá gõ dở (chưa lưu) giữ RIÊNG cho từng điểm: rời điểm A
   thì cất nháp của A, sang B thì lấy nháp của B (hoặc trống). Mọi đường vào
   (chip điểm, nút Bảng giá ở Cài đặt, trang chủ) đều đi qua đây, nên giá gõ
   cho A không bao giờ thành giá lưu của B (Codex PR #532). */
function bgdDoiDiem(ma) {
  if (!ma || ma === BGD.ma) return;
  if (!BGD.nhap) BGD.nhap = {};
  if (BGD.ma) BGD.nhap[BGD.ma] = BGD.sua;
  BGD.ma = ma;
  BGD.sua = BGD.nhap[ma] || {};
}

/* Lọc món theo chip. PHÉP THUẦN. chip: da_ban (đã bán ở điểm trong 30 ngày),
   chua_gia (đã bán mà chưa có giá riêng), tat_ca, hoặc "nhom:<nhóm món>". */
function bgdLoc(mon, chip, tim) {
  return (mon || []).filter(function (m) {
    if (chip === 'da_ban' && !(+m.da_ban > 0)) return false;
    if (chip === 'chua_gia' && !(+m.da_ban > 0 && !(+m.gia_diem > 0))) return false;
    if (String(chip || '').indexOf('nhom:') === 0 && m.nhom !== chip.slice(5)) return false;
    if (tim && !vgbKhop([m.ten, m.ma, m.nhom], tim)) return false;
    return true;
  });
}
/* Giá đang hiện trong ô: giá đã sửa trên màn (chưa lưu) hoặc giá đang lưu. */
function bgdGiaO(m) {
  if (Object.prototype.hasOwnProperty.call(BGD.sua, m.ma)) return BGD.sua[m.ma];
  return +m.gia_diem > 0 ? String(m.gia_diem) : '';
}
/* Các ô đã đổi so với giá đang lưu. PHÉP THUẦN trên BGD.kq. */
function bgdDsDoi() {
  var ra = [];
  ((BGD.kq && BGD.kq.mon) || []).forEach(function (m) {
    if (!Object.prototype.hasOwnProperty.call(BGD.sua, m.ma)) return;
    var moi = +String(BGD.sua[m.ma] || '').replace(/[^0-9]/g, '') || 0;
    if (moi !== (+m.gia_diem || 0)) ra.push({ ma: m.ma, gia: moi ? String(moi) : '' });
  });
  return ra;
}

async function scrBangGiaDiem(ma) {
  var tieuDe = 'Bảng giá theo điểm bán';
  if (ma) bgdDoiDiem(ma);
  await cfgBanHang();
  /* Chưa chọn điểm (mở từ trang chủ): lấy điểm đầu tiên có giá riêng. */
  var coGia = ((CFGBH && CFGBH.diem) || []).filter(function (d) { return d.co_quay && d.co_bang_gia; });
  if (!BGD.ma && coGia.length) bgdDoiDiem(coGia[0].ma);
  if (!BGD.ma) {
    frame(tieuDe, '<div class="emp"><div class="e1">💲</div><div>Chưa điểm bán nào dùng giá riêng. Vào Cài đặt, Điểm bán, chọn điểm rồi bật Giá riêng ở mục Bảng giá của điểm.</div>' +
      '<button type="button" class="btn gh" data-bgdcd="1" style="margin:14px auto 0;width:auto;padding:0 18px">Mở Cài đặt Điểm bán</button></div>')
      .addEventListener('click', function (e) { if (e.target.closest('[data-bgdcd]')) go(scrDiemBan); });
    return;
  }
  frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc bảng giá...</div></div>');
  try { BGD.kq = await api('vagabond.diem_ban.bang_gia_diem', { ma: BGD.ma }); }
  catch (e) {
    frame(tieuDe, '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e)) + '</div></div>');
    return;
  }
  bgdVe();
}

function bgdVe() {
  var kq = BGD.kq || {}, d = kq.diem || {}, mon = kq.mon || [], sua = !!kq.sua_duoc;
  var tenNgan = d.ten_ngan || d.ma || '';
  var daBan = mon.filter(function (m) { return +m.da_ban > 0; });
  var chuaGia = daBan.filter(function (m) { return !(+m.gia_diem > 0); });
  var nhom = {};
  daBan.forEach(function (m) { if (m.nhom) nhom[m.nhom] = (nhom[m.nhom] || 0) + 1; });
  var dsDiem = ((CFGBH && CFGBH.diem) || []).filter(function (x) { return x.co_quay && x.co_bang_gia; });
  var html = '';
  if (dsDiem.length > 1) {
    html += '<div class="card" style="padding:10px 12px">' + kmHangChip(dsDiem.map(function (x) {
      return posChipNut('data-bgddiem="' + h(x.ma) + '"', h(x.ten_ngan || x.ma), x.ma === BGD.ma, false, '#0d9488');
    }).join('')) + '</div>';
  }
  var chip = function (k, chu, so) { return posChipNut('data-bgdchip="' + h(k) + '"', chu + (so != null ? ' · ' + money(so) : ''), BGD.chip === k, false, '#0d9488'); };
  html += '<div class="card" style="padding:10px 12px;display:flex;flex-direction:column;gap:9px">' +
    '<div style="font-size:13.5px;color:#475467;line-height:1.5"><b style="color:#101828">' + h(d.ten || tenNgan) + '</b> · món có giá ở đây thì quầy bán giá này, ô trống là bán giá chung.</div>' +
    kmHangChip(chip('da_ban', 'Đã bán ở ' + h(tenNgan) + ' ' + (kq.so_ngay || 30) + ' ngày', daBan.length) +
      chip('chua_gia', 'Chưa có giá ' + h(tenNgan), chuaGia.length) +
      Object.keys(nhom).sort().map(function (n) { return chip('nhom:' + n, h(n), nhom[n]); }).join('') +
      chip('tat_ca', 'Tất cả món bán', mon.length)) +
    '<input class="tin" id="bgdTim" type="search" placeholder="🔎 Tìm tên món, mã món" value="' + h(BGD.tim) + '" style="width:100%;margin:0;height:44px"></div>';
  var ds = bgdLoc(mon, BGD.chip, BGD.tim);
  html += '<div class="card" style="padding:4px 12px">' +
    '<div style="display:flex;flex-direction:row;justify-content:space-between;font-size:12.5px;color:#667085;padding:8px 0 4px">' +
    '<span>Món</span><span>Giá chung · Giá ' + h(tenNgan) + '</span></div>' +
    (ds.length ? ds.map(function (m) {
      var o = bgdGiaO(m), doi = Object.prototype.hasOwnProperty.call(BGD.sua, m.ma) && (+String(o).replace(/[^0-9]/g, '') || 0) !== (+m.gia_diem || 0);
      return '<div data-bgdmon="' + h(m.ma) + '" style="display:flex;flex-direction:row;align-items:center;gap:8px;padding:8px 0;border-top:1px solid #f2f4f7">' +
        anhMon(m.anh) +
        '<div style="flex:1;min-width:0"><div style="font-size:14px;color:#101828;overflow-wrap:anywhere">' + h(m.ten) + '</div>' +
        '<div style="font-size:12.5px;color:#667085">' + h(m.ma) + (+m.da_ban > 0 ? ' · đã bán ' + money(m.da_ban) : '') + '</div></div>' +
        '<div style="flex:0 0 auto;font-size:13px;color:#667085;min-width:58px;text-align:right">' + (+m.gia_chung ? money(m.gia_chung) : 'chưa có') + '</div>' +
        '<input data-bgdgia="' + h(m.ma) + '" inputmode="numeric" placeholder="trống" value="' + h(o ? money(+String(o).replace(/[^0-9]/g, '') || 0) : '') + '"' + (sua ? '' : ' disabled') +
        ' style="flex:0 0 96px;width:96px;height:44px;box-sizing:border-box;text-align:right;padding:0 9px;border-radius:9px;font-size:14px;font-family:inherit;border:1.5px solid ' +
        (doi ? '#0d9488;background:#f0fdfa' : '#e4e7ec;background:#fff') + '"></div>';
    }).join('') : '<div style="padding:18px 0;color:#667085;text-align:center">Không có món nào khớp. Bấm Tất cả món bán để thêm giá cho món mới.</div>') + '</div>';
  if (!sua) html += '<div style="font-size:12.5px;color:#92400e;margin:4px 16px 0;line-height:1.5">Bạn xem được giá, chỉ quản lý cửa hàng, Sales quản lý hoặc kế toán mới sửa được.</div>';
  html += '<div style="font-size:12px;color:#98a2b3;margin:10px 16px 18px;line-height:1.5">Mỗi lần đổi giá, máy ghi trên món: ai đổi, lúc nào, giá cũ và giá mới. Bill quầy ' + h(tenNgan) + ' tự lấy giá này, thu ngân không sửa tay được.</div>';
  var soDoi = bgdDsDoi().length;
  var footer = sua ? '<div style="display:flex;flex-direction:column;gap:8px"><div style="display:flex;flex-direction:row;gap:8px">' +
    '<button class="btn gh" data-bgdxuat="1" style="margin:0;flex:1">Tải Excel</button>' +
    '<button class="btn gh" data-bgdnap="1" style="margin:0;flex:1">Nạp Excel</button></div>' +
    '<button class="btn" data-bgdluu="1" style="margin:0"' + (soDoi ? '' : ' disabled') + '>' + (soDoi ? 'Lưu ' + soDoi + ' giá đã đổi' : 'Chưa đổi giá nào') + '</button></div>' : '';
  var b = frame('Bảng giá · ' + tenNgan, html, footer ? { footer: footer } : null);
  var tim = document.getElementById('bgdTim');
  if (tim) tim.oninput = function () { BGD.tim = tim.value; clearTimeout(BGD.tre); BGD.tre = setTimeout(function () { bgdVe(); var o = document.getElementById('bgdTim'); if (o) { o.focus(); try { o.setSelectionRange(o.value.length, o.value.length); } catch (x) { } } }, 350); };
  /* Gõ giá thì cập nhật tại chỗ (viền ô, số trên nút Lưu), KHÔNG vẽ lại màn:
     vẽ lại lúc chuyển sang ô kế tiếp là mất chỗ con trỏ vừa bấm. */
  b.addEventListener('input', function (e) {
    var o = e.target.closest('[data-bgdgia]');
    if (!o) return;
    var maMon = o.getAttribute('data-bgdgia');
    BGD.sua[maMon] = String(o.value || '').replace(/[^0-9]/g, '');
    var m = ((BGD.kq && BGD.kq.mon) || []).filter(function (x) { return x.ma === maMon; })[0] || {};
    var doi = (+BGD.sua[maMon] || 0) !== (+m.gia_diem || 0);
    o.style.borderColor = doi ? '#0d9488' : '#e4e7ec';
    o.style.background = doi ? '#f0fdfa' : '#fff';
    var n = bgdDsDoi().length, nl = document.querySelectorAll('[data-bgdluu]')[0];
    if (nl) { nl.disabled = !n; nl.textContent = n ? 'Lưu ' + n + ' giá đã đổi' : 'Chưa đổi giá nào'; }
  });
  b.addEventListener('click', function (e) {
    var t = e.target.closest('[data-bgdchip]');
    if (t) { BGD.chip = t.getAttribute('data-bgdchip'); return bgdVe(); }
    t = e.target.closest('[data-bgddiem]');
    if (t) {
      if (bgdDsDoi().length) return toast('Lưu hoặc bỏ các giá đã đổi trước khi sang điểm khác.', 3600);
      bgdDoiDiem(t.getAttribute('data-bgddiem'));
      return go(function () { return scrBangGiaDiem(BGD.ma); }, true);
    }
  });
  var bx = document.querySelectorAll('[data-bgdxuat]')[0];
  if (bx) bx.onclick = bgdXuat;
  var bn = document.querySelectorAll('[data-bgdnap]')[0];
  if (bn) bn.onclick = bgdNap;
  var bl = document.querySelectorAll('[data-bgdluu]')[0];
  if (bl) bl.onclick = bgdLuu;
}

async function bgdLuu() {
  var ds = bgdDsDoi();
  if (!ds.length) return;
  busy(true);
  try {
    var kq = await api('vagabond.diem_ban.luu_gia', { ma: BGD.ma, thay_doi: JSON.stringify(ds) });
    busy(false);
    BGD.sua = {};
    CFGBH = null;
    toast('Đã lưu ' + ((kq && kq.so) || ds.length) + ' giá. Quầy dùng giá mới từ bill kế tiếp.', 3600);
    go(function () { return scrBangGiaDiem(BGD.ma); }, true);
  } catch (e) { busy(false); baoTin(errMsg(e)); }
}

async function bgdXuat() {
  busy(true);
  try {
    var f = await api('vagabond.diem_ban.xuat_excel_gia', { ma: BGD.ma });
    busy(false);
    bcTaiVe(f.ten_file, f.b64);
  } catch (e) { busy(false); baoTin(errMsg(e)); }
}

function bgdNap() {
  var inp = document.createElement('input');
  inp.type = 'file';
  inp.accept = '.xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
  inp.style.display = 'none';
  inp.onchange = function () {
    var f = inp.files && inp.files[0];
    inp.remove();
    if (!f) return;
    var rd = new FileReader();
    rd.onload = async function () {
      var b64 = String(rd.result || '').split(',').pop();
      busy(true);
      try {
        var kq = await api('vagabond.diem_ban.nap_excel_gia', { ma: BGD.ma, b64: b64 });
        busy(false);
        bgdApNap((kq && kq.thay_doi) || []);
      } catch (e) { busy(false); baoTin(errMsg(e)); }
    };
    rd.readAsDataURL(f);
  };
  document.body.appendChild(inp);
  inp.click();
}
/* Giá đọc từ Excel thành ô "đã đổi" để người dùng xem lại rồi mới bấm Lưu.
   Món không có trên bảng thì bỏ, báo số. */
function bgdApNap(ds) {
  var co = {};
  ((BGD.kq && BGD.kq.mon) || []).forEach(function (m) { co[m.ma] = m; });
  var lay = 0, bo = 0;
  ds.forEach(function (x) {
    if (!co[x.ma]) { bo++; return; }
    BGD.sua[x.ma] = x.gia ? String(x.gia) : '';
    lay++;
  });
  BGD.chip = 'tat_ca';
  bgdVe();
  var doi = bgdDsDoi().length;
  baoTin('Đã đọc ' + lay + ' dòng từ Excel, ' + doi + ' giá khác giá đang lưu.' + (bo ? ' Bỏ ' + bo + ' dòng có mã món không còn bán.' : '') +
    (doi ? ' Xem lại rồi bấm Lưu ' + doi + ' giá đã đổi.' : ''));
}

/* ---------- Van don: sales phan don, shipper giao kem anh, book xe, chi phi ---------- */
var vdNgay = null, vdLoc = null, vdTay = null;
function vdChupAnh(cb, nguon) {
  var inp = document.createElement('input');
  inp.type = 'file'; inp.accept = 'image/*';
  // Bo capture thi iOS va Android deu hien bang chon: chup anh moi HOAC
  // lay anh co san trong album. Truyen nguon la 'camera' neu cho nao do
  // muon ep mo thang camera.
  if (nguon === 'camera') inp.setAttribute('capture', 'environment');
  inp.onchange = function () {
    var f = inp.files && inp.files[0]; inp.remove(); if (!f) return;
    busy(true);
    var img = new Image();
    var url = URL.createObjectURL(f);
    img.onload = function () {
      var max = 1280, w = img.width, h2 = img.height;
      if (w >= h2 && w > max) { h2 = Math.round(h2 * max / w); w = max; }
      else if (h2 > w && h2 > max) { w = Math.round(w * max / h2); h2 = max; }
      var cv = document.createElement('canvas'); cv.width = w; cv.height = h2;
      cv.getContext('2d').drawImage(img, 0, 0, w, h2);
      cv.toBlob(function (b) { URL.revokeObjectURL(url); cb(b); }, 'image/jpeg', 0.72);
    };
    img.onerror = function () { busy(false); baoTin('Không đọc được ảnh, chụp lại giúp em.'); };
    img.src = url;
  };
  inp.style.display = 'none'; document.body.appendChild(inp); inp.click();
}
async function vdUpload(blob, doctype, docname, fieldname) {
  var fd = new FormData();
  fd.append('file', new File([blob], 'giao-' + docname + '-' + Date.now() + '.jpg', { type: 'image/jpeg' }));
  fd.append('is_private', '1');
  fd.append('doctype', doctype);
  fd.append('docname', docname);
  fd.append('fieldname', fieldname);
  var hd = {};
  hd['X-Frappe-' + 'CSRF-' + 'Token'] = frappe.csrf_token;
  var r = await fetch('/api/method/upload_file', { method: 'POST', headers: hd, body: fd });
  var j = await r.json();
  if (!r.ok || !j.message) throw new Error('Upload ảnh lỗi');
  return j.message.file_url;
}
function vdLaShipper() { return hasRole('Shipper'); }
function vdLaKeToan() { return hasRole('Accounts User') || hasRole('Purchase User') || hasRole('System Manager'); }

async function scrVanDon() {
  vdTuLamMoi();
  if (!vdNgay) vdNgay = today();
  frame('Vận đơn', '<div class="emp"><div class="e1">⏳</div><div>Đang tải vận đơn...</div></div>');
  var ds;
  try { ds = await api('vagabond.van_don.danh_sach', vdThamSo()); try { vdBoLoc = await api('vagabond.van_don.bo_loc', { ngay: vdNgay }); } catch (e9) { vdBoLoc = null; }
  if (!vtShipper) { try { vtShipper = await api('vagabond.van_don.ds_shipper'); } catch (e10) { vtShipper = []; } } }
  catch (e) { frame('Vận đơn', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var chonMode = !!window.vdChon;
  /* Hai nut lui/toi mot ngay: tren dien thoai bam nhanh hon mo bang chon
     ngay, va khong dinh loi bang chon ngay lam trang bi ve lai. */
  var html = '<div class="card" style="padding:12px 14px;display:flex;flex-direction:row;align-items:center;gap:8px">' +
    '<button class="btn gh" id="vdLui" style="margin:0;width:auto;padding:8px 13px;flex:0 0 auto">◀</button>' +
    '<input type="date" class="hin" id="vdDate" value="' + vdNgay + '" style="flex:1;margin:0;min-width:0">' +
    '<button class="btn gh" id="vdToi" style="margin:0;width:auto;padding:8px 13px;flex:0 0 auto">▶</button></div>';
  if (isSales() || vdLaKeToan()) html += '<button class="btn gh" id="vdDongBo" style="margin:0 0 10px">🔄 Đồng bộ đơn Pancake ngày ' + vdNgay.split('-').reverse().join('/') + '</button>';
  var ICON = VD_TT_ICON;
  html += vdChipsHtml(ds);
  var dsTho = ds;
  ds = vdLocRa(dsTho);
  html += vdKhoiTong(ds, vdNhanLoc(dsTho));
  if (chonMode) html += '<div class="sec" style="color:#0369a1">' + (window.vdChonDe === 'in' ? 'ĐANG CHỌN ĐƠN ĐỂ IN' : 'ĐANG GỘP CHUYẾN') + ' - BẤM VÀO TỪNG ĐƠN ĐỂ CHỌN</div>';
  else html += '<div class="sec">' + ds.length + ' vận đơn · bấm vào để xử lý</div>';
  html += '<div class="card">';
  if (!dsTho.length) html += '<div class="emp" style="padding:24px"><div class="e1">🛵</div><div>Chưa có vận đơn nào cho ngày này.</div></div>';
  else if (!ds.length) html += '<div class="emp" style="padding:24px"><div class="e1">✅</div><div>Không có đơn nào thuộc nhóm <b>' + h(vdNhanLoc(dsTho)) + '</b>.</div></div>';
  ds.forEach(function (r) {
    var daChon = chonMode && window.vdChon[r.name];
    /* Trang thai da co chip mau ben duoi nen bo khoi dong chu xam nay. */
    var d2 = (r.tag_gio ? '\u{1F552} ' + h(r.tag_gio) + ' · ' : (r.gio_giao ? r.gio_giao + ' · ' : '')) + (r.phuong ? h(vdPhuongNgan(r.phuong)) + ' · ' : '') + h(r.kenh) + (r.shipper ? ' · ' + h(vdTen(r.shipper)) : '') + (r.chuyen ? ' · 🧺' + h(r.chuyen) : '');
    /* Ten mon rut gon: mon dau + "còn N món". Ten day du xem trong chi tiet. */
    var mon1 = r.mon_chinh ? (h(r.mon_chinh) + (r.so_mon > 1 ? ' · còn ' + (r.so_mon - 1) + ' món' : '')) : h(r.mon_tat || '');
    var oAnh = daChon ? '☑️'
      : (r.anh ? '<img src="' + h(r.anh) + '" alt="" style="width:100%;height:100%;object-fit:cover;border-radius:13px;display:block" onerror="this.style.display=\'none\'">'
              : (ICON[r.trang_thai] || '📦'));
    html += '<div class="hub" data-vd="' + h(r.name) + '" data-tt="' + h(r.trang_thai) + '"' + (daChon ? ' style="background:#dbeafe"' : '') + '><div class="hi" style="overflow:hidden">' + oAnh + '</div>' +
      '<div class="ht"><div class="h1">' + (r.ma_don ? '#' + h(r.ma_don) + ' · ' : '') + h(r.khach || 'Khách lẻ') + '</div>' +
      '<div class="h2">' + d2 + '</div>' +
      '<div class="h2">' + h((r.dia_chi || '').slice(0, 70)) + '</div>' +
      (mon1 ? '<div class="h2" style="color:#7a5b2e">🎂 ' + mon1 + '</div>' : '') + vdHuyHieu(r) + '</div>' +
      '<div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;flex:0 0 auto">'
      + (r.tien_thu_ho ? '<b style="white-space:nowrap;font-size:13px">COD ' + money(r.tien_thu_ho) + '</b>' : '')
      + vdNutDong(r, chonMode) + '</div></div>';
  });
  html += '</div>';
  var foot = '';
  if (chonMode) {
    foot = '<div style="display:flex;gap:10px"><button class="btn" id="vdGan" style="flex:2">'
      + (window.vdChonDe === 'in' ? '🖨️ In ' : '✅ Gán ') + Object.keys(window.vdChon).length + ' đơn</button>'
      + '<button class="btn gh" id="vdThoi" style="flex:1">✖ Thôi</button></div>';
  } else {
    var nutF = [];
    if (isSales()) nutF.push('<button class="btn gh" id="vdGop" style="flex:1">🧺 Gộp chuyến</button>');
    if (isSales()) nutF.push('<button class="btn gh" id="vdTuyen" style="flex:1">🧭 Xếp tuyến</button>');
    nutF.push('<button class="btn gh" id="vdIn" style="flex:1">🖨️ In đơn</button>');
    if (vdLaShipper() && !isSales()) nutF.push('<button class="btn gh" id="vdDuong" style="flex:1">🗺️ Chỉ đường</button>');
    if (isSales() || vdLaKeToan()) nutF.push('<button class="btn gh" id="vdCod" style="flex:1">💵 Đối soát COD</button>');
    if (nutF.length) foot = '<div style="display:flex;gap:8px">' + nutF.join('') + '</div>';
  }
  var b = frame('Vận đơn', html, Object.assign({ action: '➕', onAction: function () { go(scrVdTao); } }, foot ? { footer: foot } : {}));
  var di = document.getElementById('vdDate');
  if (di) di.onchange = function () { if (di.value) { vdNgay = di.value; go(scrVanDon, true); } };
  function vdDoiNgay(buoc) {
    var t = new Date((vdNgay || today()) + 'T00:00:00');
    t.setDate(t.getDate() + buoc);
    vdNgay = t.getFullYear() + '-' + String(t.getMonth() + 1).padStart(2, '0') + '-' + String(t.getDate()).padStart(2, '0');
    go(scrVanDon, true);
  }
  var bLui = document.getElementById('vdLui'); if (bLui) bLui.onclick = function () { vdDoiNgay(-1); };
  var bToi = document.getElementById('vdToi'); if (bToi) bToi.onclick = function () { vdDoiNgay(1); };
  vdGanChips();
  var btq = document.getElementById('vdTuyen'); if (btq) btq.onclick = function () { go(scrVdTuyen, true); };
  var bcd = document.getElementById('vdDuong'); if (bcd) bcd.onclick = vdChiDuongToi;
  var db = document.getElementById('vdDongBo');
    if (db) db.onclick = async function () {
      busy(true);
      try {
        var kq = await api('vagabond.van_don.dong_bo_pancake', { ngay: vdNgay });
        busy(false);
        toast(kq.them ? ('Đã kéo về ' + kq.them + ' vận đơn mới') : ('Không có đơn mới - ' + (kq.da_co || 0) + ' đơn đã kéo về trước đó'), 3200);
        go(scrVanDon, true);
      } catch (e) {
        busy(false);
        baoTin((e && e.message) || 'Đồng bộ Pancake lỗi');
      }
    };
  var gp = document.getElementById('vdGop');
  if (gp) gp.onclick = function () { window.vdChon = {}; window.vdChonDe = 'gan'; go(scrVanDon, true); };
  var bin = document.getElementById('vdIn');
  if (bin) bin.onclick = function () { window.vdChon = {}; window.vdChonDe = 'in'; go(scrVanDon, true); };
  var cod = document.getElementById('vdCod');
  if (cod) cod.onclick = function () { go(scrVdCod); };
  var th = document.getElementById('vdThoi');
  if (th) th.onclick = function () { window.vdChon = null; go(scrVanDon, true); };
  var gan = document.getElementById('vdGan');
  if (gan) gan.onclick = async function () {
    var names = Object.keys(window.vdChon || {});
    if (window.vdChonDe === 'in') {
      if (!names.length) return toast('Chưa chọn đơn nào để in.');
      window.vdChon = null; window.vdChonDe = null;
      await vdInPhieu(names);
      go(scrVanDon, true);
      return;
    }
    if (!names.length) return toast('Chưa chọn đơn nào, bấm vào các đơn cần gộp trước.');
    var ships;
    try { ships = await api('vagabond.van_don.ds_shipper', {}); } catch (er) { return baoTin((er && er.message) || 'Lỗi'); }
    if (!ships.length) return baoTin('Chưa có tài khoản nào gắn role Shipper. Anh Việt tạo user shipper trước.');
    var chot = async function (shipper, chuyen) {
      busy(true);
      try {
        var kq = await api('vagabond.van_don.gop_chuyen', { names: JSON.stringify(names), shipper: shipper, chuyen: chuyen || '' });
        busy(false);
        toast('Đã gộp ' + kq.so_don + ' đơn vào chuyến ' + kq.chuyen + (kq.bo_qua && kq.bo_qua.length ? ' · bỏ qua: ' + kq.bo_qua.join(', ') : ''), 4500);
      } catch (er) { busy(false); return baoTin((er && er.message) || 'Gộp lỗi'); }
      window.vdChon = null;
      go(scrVanDon, true);
    };
    sheet('Giao chuyến cho shipper nào?', ships.map(function (s) { return { value: s.user, label: s.ten, icon: '🛵' }; }), null, async function (o) {
      var chay = [];
      try { chay = (await api('vagabond.van_don.chuyen_dang_chay', { ngay: vdNgay })).filter(function (x) { return x.shipper === o.value; }); } catch (er) {}
      if (!chay.length) return chot(o.value, '');
      sheet('Chuyến mới hay chèn vào chuyến đang chạy?', [{ value: '', label: 'Chuyến mới', icon: '🆕' }].concat(chay.map(function (x) { return { value: x.chuyen, label: 'Chèn vào ' + x.chuyen + ' (' + x.so_don + ' đơn đang chạy)', icon: '➕' }; })), null, function (o2) { chot(o.value, o2.value); });
    });
  };
  b.addEventListener('click', function (e) {
    var r = e.target.closest('[data-vd]'); if (!r) return;
    var nutN = e.target.closest('[data-di],[data-pc]');
    if (nutN && !window.vdChon) {
      e.stopPropagation();
      if (nutN.hasAttribute('data-di')) { vdMoDuong(nutN.getAttribute('data-di')); return; }
      vdChonShipper(r.getAttribute('data-vd'));
      return;
    }
    var nm = r.getAttribute('data-vd');
    if (window.vdChon) {
      var tt = r.getAttribute('data-tt');
      if (tt !== 'Chờ giao' && tt !== 'Đang giao') return toast('Đơn ' + tt + ' không gộp chuyến được.');
      if (window.vdChon[nm]) { delete window.vdChon[nm]; r.style.background = ''; r.querySelector('.hi').textContent = '📦'; }
      else { window.vdChon[nm] = 1; r.style.background = '#dbeafe'; r.querySelector('.hi').textContent = '☑️'; }
      var g2 = document.getElementById('vdGan');
      if (g2) g2.textContent = (window.vdChonDe === 'in' ? '🖨️ In ' : '✅ Gán ') + Object.keys(window.vdChon).length + ' đơn';
      return;
    }
    go(function () { scrVdView(nm); });
  });
}

async function scrVdCod() {
  frame('Đối soát COD', '<div class="emp"><div class="e1">⏳</div></div>');
  var ng = vdNgay || today();
  var ds;
  try { ds = await api('vagabond.van_don.doi_soat_cod', { ngay: ng }); }
  catch (e) { frame('Đối soát COD', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var html = '<div class="card" style="padding:12px 14px"><input type="date" class="hin" id="codDate" value="' + ng + '" style="margin:0"></div>';
  if (!ds.length) html += '<div class="emp"><div class="e1">💵</div><div>Chưa có đơn Đã giao nào trong ngày này.</div></div>';
  ds.forEach(function (g) {
    html += '<div class="sec">' + h(g.ten) + ' · ' + g.so_don + ' đơn đã giao</div><div class="card" style="padding:12px 14px;line-height:1.9">';
    g.don.forEach(function (d) {
      /* Bay ra vi sao mot don khong con COD: truoc day man nay chi hien con
         so, don khach da chuyen khoan van doi shipper nop tien ma khong noi
         ly do (Sales bao lai 13/08/2026). */
      var ghi = d.chua_ro
        ? '<span style="color:#b45309">⚠️ chưa chọn phương thức</span>'
        : (d.thu_tien_mat ? '<span style="color:#6b7280">' + h(d.pt) + '</span>'
                          : '<span style="color:#0e7490">' + h(d.pt) + ' · không thu</span>');
      html += '<div style="display:flex;justify-content:space-between;font-size:13px;gap:8px;align-items:flex-start">'
        + '<span style="flex:1;min-width:0">' + (d.ma_don ? '#' + h(d.ma_don) : h(d.name)) + ' · ' + h(d.khach || 'Khách lẻ')
        + (d.chuyen ? ' · 🧺' + h(d.chuyen) : '')
        + '<br>' + ghi
        + (d.lech ? '<br><span style="color:#0e7490;font-size:12px">vận đơn đang ghi ' + money(d.cod_tren_van_don) + ' đ, máy đã trừ ra</span>' : '')
        + '</span>'
        + '<span style="white-space:nowrap"><b>' + (d.cod ? money(d.cod) : '0') + '</b>' + (d.da_doi_soat ? ' ✅' : '') + '</span></div>';
    });
    html += '<div style="display:flex;justify-content:space-between;margin-top:6px;border-top:1px solid #e5e7eb;padding-top:6px"><b>Tổng COD phải nộp</b><b>' + money(g.tong_cod) + ' đ</b></div>';
    if (g.so_don_chua_ro > 0) html += '<div style="color:#b45309;font-size:12.5px;margin-top:3px">⚠️ ' + g.so_don_chua_ro + ' đơn chưa chọn phương thức thanh toán, con số trên có thể còn sai. Vào Doanh thu sửa hoá đơn rồi mở lại màn này.</div>';
    if (g.chua_doi_soat > 0) html += '<div style="display:flex;justify-content:space-between;color:#b3261e"><span>Chưa nộp về</span><b>' + money(g.chua_doi_soat) + ' đ</b></div>';
    else if (g.tong_cod > 0) html += '<div style="color:#15803d;font-size:13px">Đã đối soát đủ ✅</div>';
    /* Sales bam duoc tu 13/08/2026: cuoi ngay chinh cac ban Sales ngoi dem
       tien shipper nop ve. */
    if ((isSales() || vdLaKeToan()) && g.so_don_chua > 0 && g.shipper.indexOf('@') > -1)
      html += '<button class="btn" data-cod="' + h(g.shipper) + '" style="margin-top:8px">✔ Đã nhận đủ ' + money(g.chua_doi_soat) + ' đ từ ' + h(g.ten) + '</button>';
    html += '</div>';
  });
  var b = frame('Đối soát COD', html);
  var di = document.getElementById('codDate');
  if (di) di.onchange = function () { if (di.value) { vdNgay = di.value; go(scrVdCod, true); } };
  b.addEventListener('click', async function (e) {
    var el = e.target.closest('[data-cod]'); if (!el) return;
    if (!await xacNhan('Xác nhận ĐÃ NHẬN ĐỦ tiền COD shipper nộp về? Toàn bộ đơn Đã giao của bạn này trong ngày sẽ được đánh dấu đã đối soát.')) return;
    busy(true);
    try {
      var kq = await api('vagabond.van_don.xac_nhan_cod', { shipper: el.getAttribute('data-cod'), ngay: vdNgay || today() });
      busy(false);
      toast('Đã xác nhận ' + kq.so_don + ' đơn · ' + money(kq.tong) + ' đ', 3500);
    } catch (er) { busy(false); baoTin((er && er.message) || 'Lỗi'); }
    go(scrVdCod, true);
  });
}

function vdGioNgan(t) {
  var s = String(t || '');
  if (s.length < 16) return s;
  return s.slice(11, 16) + ' ngày ' + s.slice(8, 10) + '/' + s.slice(5, 7);
}
/* Man khach ky tay. May chu nhan data URL PNG cua the canvas roi luu thanh
   tep dinh kem (vagabond.van_don.luu_chu_ky). */
function scrVdKy(name, d) {
  var html = '<div class="card" style="padding:12px 14px;line-height:1.6">' +
    '<div><b>' + (d.ma_don ? '#' + h(d.ma_don) : h(name)) + '</b> · ' + h(d.khach || 'Khách lẻ') + '</div>' +
    (d.dia_chi ? '<div style="color:#6b7280;font-size:13px">' + h(d.dia_chi) + '</div>' : '') +
    (d.tien_thu_ho ? '<div><b>Thu hộ (COD): ' + money(d.tien_thu_ho) + ' đ</b></div>' : '') + '</div>';
  html += '<div class="card" style="padding:12px 14px">' +
    '<input class="tin" id="vdkTen" placeholder="Tên người ký" value="' + h(d.nguoi_nhan || d.khach || '') + '">' +
    '<div style="font-size:12px;color:#6b7280;margin:10px 0 6px">Mời khách ký vào khung dưới</div>' +
    '<canvas id="vdkCanvas" style="width:100%;height:200px;background:#fff;border:1.5px dashed #b9c7cc;border-radius:12px;touch-action:none;display:block"></canvas>' +
    '</div>';
  frame('Khách ký nhận', html, { footer: '<div style="display:flex;gap:8px"><button class="btn gh" id="vdkXoa" style="flex:1">Xoá nét</button><button class="btn" id="vdkLuu" style="flex:2">Lưu chữ ký</button></div>' });
  setTimeout(function () {
    var cv = document.getElementById('vdkCanvas');
    if (!cv) return;
    var ctx = cv.getContext('2d');
    var tl = window.devicePixelRatio || 1;
    var rong = cv.clientWidth || cv.offsetWidth || 300, cao = cv.clientHeight || 200;
    cv.width = Math.round(rong * tl); cv.height = Math.round(cao * tl);
    ctx.scale(tl, tl);
    function xoa() { ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, rong, cao); }
    xoa();
    ctx.lineWidth = 2.2; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.strokeStyle = '#111827';
    var dangVe = false, daVe = false;
    function toa(ev) { var q = cv.getBoundingClientRect(); return { x: ev.clientX - q.left, y: ev.clientY - q.top }; }
    cv.addEventListener('pointerdown', function (ev) {
      ev.preventDefault(); dangVe = true; daVe = true;
      var p = toa(ev); ctx.beginPath(); ctx.moveTo(p.x, p.y);
      try { cv.setPointerCapture(ev.pointerId); } catch (e0) { }
    });
    cv.addEventListener('pointermove', function (ev) {
      if (!dangVe) return; ev.preventDefault();
      var p = toa(ev); ctx.lineTo(p.x, p.y); ctx.stroke();
    });
    cv.addEventListener('pointerup', function () { dangVe = false; });
    cv.addEventListener('pointercancel', function () { dangVe = false; });
    cv.addEventListener('pointerleave', function () { dangVe = false; });
    var bx = document.getElementById('vdkXoa');
    if (bx) bx.onclick = function () { xoa(); daVe = false; };
    var bl = document.getElementById('vdkLuu');
    if (bl) bl.onclick = async function () {
      if (!daVe) return baoTin('Chưa có nét ký nào, mời khách ký giúp em.');
      var ten = (document.getElementById('vdkTen') || {}).value || '';
      busy(true);
      try {
        await api('vagabond.van_don.luu_chu_ky', { name: name, anh: cv.toDataURL('image/png'), nguoi_ky: ten });
        busy(false); toast('Đã lưu chữ ký');
      } catch (er) { busy(false); return baoTin((er && er.message) || 'Lưu chữ ký lỗi'); }
      go(function () { scrVdView(name); }, true);
    };
  }, 0);
}
async function scrVdView(name) {
  frame('Chi tiết vận đơn', '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api('frappe.client.get', { doctype: 'Van Don', name: name }); if (!vtShipper) { try { vtShipper = await api('vagabond.van_don.ds_shipper'); } catch (e11) { vtShipper = []; } } }
  catch (e) { frame('Chi tiết vận đơn', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không đọc được') + '</div></div>'); return; }
  var html = '<div class="card" style="padding:12px 14px;line-height:1.7">' +
    '<div style="display:flex;justify-content:space-between"><b>' + (d.ma_don ? '#' + h(d.ma_don) : h(d.name)) + '</b><span>' + h(d.trang_thai) + '</span></div>' +
    '<div>' + h(d.khach || 'Khách lẻ') + (d.sdt ? ' · <a href="tel:' + h(d.sdt) + '">' + h(d.sdt) + '</a>' : '') + '</div>' +
    '<div style="font-size:13px">' + h(d.dia_chi || '(chưa có địa chỉ)') + '</div>' +
    '<div style="color:#6b7280;font-size:13px">' + h(d.kenh) + (d.gio_giao ? ' · khung ' + h(d.gio_giao) : '') + (d.shipper ? ' · ' + h(vdTen(d.shipper)) : '') + (d.chuyen ? ' · 🧺' + h(d.chuyen) : '') + '</div>' +
    ((d.mon && d.mon.length) ? '<div style="margin-top:8px;padding-top:8px;border-top:1px dashed #e5e7eb">' +
      '<div style="font-size:12px;color:#6b7280;letter-spacing:.4px">HÀNG TRONG ĐƠN</div>' +
      d.mon.map(function (m) {
        return '<div style="display:flex;gap:8px;align-items:flex-start;padding:4px 0">' +
          '<span style="flex:1;min-width:0"><b>' + h(m.ten || m.ma_hang || '') + '</b>' +
          (m.ma_hang ? '<span style="color:#a0a6b4;font-size:12px"> · ' + h(m.ma_hang) + '</span>' : '') +
          (m.tang ? '<span style="color:#b45309;font-size:12px"> · tặng</span>' : '') +
          (m.ghi_chu ? '<div style="color:#7a5b2e;font-size:12px;line-height:1.4">' + h(m.ghi_chu) + '</div>' : '') +
          '</span><b style="flex:none">&times;' + (m.so_luong || 0) + '</b></div>';
      }).join('') + '</div>' : '') +
    (d.tien_thu_ho ? '<div><b>Thu hộ (COD): ' + money(d.tien_thu_ho) + ' đ</b>' + (d.da_doi_soat ? ' <span style="color:#15803d;font-size:13px">đã đối soát ✅</span>' : '') + '</div>' : '') +
    (d.booking_id ? '<div style="font-size:13px">Mã app ngoài: ' + h(d.booking_id) + (d.tracking_url ? ' · <a href="' + h(d.tracking_url) + '" target="_blank">theo dõi</a>' : '') + '</div>' : '') +
    (d.hoa_don ? '<div style="color:#6b7280;font-size:13px">Hoá đơn: ' + h(d.hoa_don) + '</div>' : '') +
    (d.anh_giao ? '<div style="margin-top:10px">' +
      '<div style="font-size:12px;color:#6b7280;margin-bottom:5px">Ảnh giao thành công' + (d.da_bao_pancake ? ' · đã báo Pancake ✅' : '') + '</div>' +
      '<a href="' + h(d.anh_giao) + '" target="_blank" rel="noopener" style="display:inline-block">' +
      '<img src="' + h(d.anh_giao) + '" alt="Ảnh giao" style="width:118px;height:118px;object-fit:cover;border-radius:10px;border:1px solid #d7e6ea;display:block">' +
      '</a></div>' : '') +
    (d.chu_ky ? '<div style="margin-top:10px">' +
      '<div style="font-size:12px;color:#6b7280;margin-bottom:5px">✍️ Khách ký nhận' +
      (d.nguoi_ky ? ' · ' + h(d.nguoi_ky) : '') + (d.ky_luc ? ' · ' + h(vdGioNgan(d.ky_luc)) : '') + '</div>' +
      '<a href="' + h(d.chu_ky) + '" target="_blank" rel="noopener" style="display:inline-block">' +
      '<img src="' + h(d.chu_ky) + '" alt="Chữ ký khách" style="width:230px;max-width:100%;background:#fff;border:1px solid #d7e6ea;border-radius:10px;display:block">' +
      '</a></div>'
      : (d.khong_ky ? '<div style="color:#b45309;font-size:13px;margin-top:8px">✍️ Khách không ký: ' + h(d.khong_ky) + '</div>' : '')) +
    (d.ly_do_loi ? '<div style="color:#b3261e;font-size:13px">Không giao được: ' + h(d.ly_do_loi) + '</div>' : '') +
    (d.ghi_chu ? '<div style="color:#6b7280;font-size:13px;white-space:pre-wrap">' + h(d.ghi_chu) + '</div>' : '') + vdKhoiNhan(d) + '</div>' + vdNutPhanCong(d);
  var dangGiao = d.trang_thai === 'Chờ giao' || d.trang_thai === 'Đang giao';
  if (dangGiao) {
    html += '<button class="btn" data-va="giao" style="margin-top:4px">📷 Đã giao, chụp ảnh</button>';
    var hang = [];
    if (vdLaShipper() && !d.shipper) hang.push('<button class="btn gh" data-va="nhan" style="flex:1">🙋 Nhận đơn</button>');
    if (isSales() && !d.booking_id) hang.push('<button class="btn gh" data-va="book" style="flex:1">🚕 Book xe app</button>');
    hang.push('<button class="btn gh" data-va="loi" style="flex:1;color:#b3261e">⚠️ Không giao được</button>');
    html += '<div style="display:flex;gap:8px;padding:8px 0 0">' + hang.join('') + '</div>';
  }
  /* Chu ky la chung tu giao nhan: cho ky ca truoc va sau khi bam Da giao,
     chi giau di khi don da huy hoac da co chu ky. */
  if (!d.chu_ky && d.trang_thai !== 'Huỷ') {
    html += '<div style="display:flex;gap:8px;padding:8px 0 0">' +
      '<button class="btn gh" data-va="ky" style="flex:2">✍️ Khách ký nhận</button>' +
      (d.khong_ky ? '' : '<button class="btn gh" data-va="khongky" style="flex:1">Khách không ký</button>') +
      '</div>';
  }
  var b = frame('Chi tiết vận đơn', html);
  b.addEventListener('click', async function (e) {
    var el = e.target.closest('[data-va]'); if (!el) return;
    var k = el.getAttribute('data-va');
    if (k === 'chiduong') { vdMoDuong(vdDich(d)); return; }
    if (k === 'phancong') {
      if (!vtShipper) { busy(true); try { vtShipper = await api('vagabond.van_don.ds_shipper'); } catch (e7) { vtShipper = []; } busy(false); }
      var opsP = vdOpsGiao(vtShipper);
      sheet('Phân công đơn này cho ai', opsP, d.shipper || '', async function (o) {
        busy(true);
        try {
          var kq = await vdGanNguoiGiao(name, o);
          busy(false);
          if (kq.app) {
            if (kq.goiXe) { go(function () { scrVdGoiXe(name, kq.app); }); return; }
            toast('Đã ghi nhận đơn đi ' + kq.app);
          go(function () { scrVdView(name); }, true);
            return;
          }
          toast(o.value ? 'Đã phân công cho ' + o.label : 'Đã gỡ người giao khỏi đơn');
          go(function () { scrVdView(name); }, true);
        } catch (e8) { busy(false); baoTin((e8 && e8.message) || 'Phân công lỗi'); }
      });
      return;
    }
    if (k === 'ky') { return go(function () { scrVdKy(name, d); }); }
    if (k === 'khongky') {
      var lk = await hoiNhap('Vì sao khách không ký? (gửi bảo vệ, giao qua cửa, khách bận tay...)', 'Khách không ký');
      if (!lk) return;
      busy(true);
      try { await api('vagabond.van_don.khach_khong_ky', { name: name, ly_do: lk }); busy(false); toast('Đã ghi nhận'); }
      catch (er) { busy(false); baoTin((er && er.message) || 'Lỗi'); }
      return go(function () { scrVdView(name); }, true);
    }
    if (k === 'nhan') {
      busy(true);
      try { await api('vagabond.van_don.nhan_don', { name: name }); busy(false); toast('Đã nhận đơn'); }
      catch (er) { busy(false); baoTin((er && er.message) || 'Lỗi'); }
      return go(function () { scrVdView(name); }, true);
    }
    if (k === 'giao') {
      return vdChupAnh(async function (blob) {
        try {
          var fu = await vdUpload(blob, 'Van Don', name, 'anh_giao');
          var kq = await api('vagabond.van_don.giao_xong', { name: name, file_url: fu });
          busy(false);
          toast(kq.da_bao_pancake ? 'Đã giao + báo Pancake ✅' : 'Đã giao (Pancake chưa nhận được, sales kiểm lại)', 3500);
        } catch (er) { busy(false); baoTin((er && er.message) || 'Lỗi khi lưu ảnh giao'); }
        go(function () { scrVdView(name); }, true);
      });
    }
    if (k === 'loi') {
      var ld = await hoiNhap('Vì sao không giao được? (khách không nghe máy, sai địa chỉ...)', '');
      if (!ld) return;
      busy(true);
      try { await api('vagabond.van_don.giao_loi', { name: name, ly_do: ld }); busy(false); }
      catch (er) { busy(false); baoTin((er && er.message) || 'Lỗi'); }
      return go(function () { scrVdView(name); }, true);
    }
    if (k === 'book') {
      return sheet('Book xe qua app', [
        { value: 'Ahamove', label: 'Ahamove (chạy thật)', icon: '🔵' },
        { value: 'GreenSM', label: 'GreenSM (chờ key NDA)', icon: '🟢' },
        { value: 'BE', label: 'BE Delivery (chờ API)', icon: '🟡' }
      ], null, async function (o) {
        busy(true);
        try {
          var kq = await api('vagabond.van_don.book_xe', { name: name, kenh: o.value });
          busy(false);
          toast('Đã book ' + o.value + (kq.booking_id ? ' · mã ' + kq.booking_id : '') + (kq.phi_giao ? ' · phí ' + money(kq.phi_giao) : ''), 4000);
        } catch (er) { busy(false); baoTin((er && er.message) || 'Book lỗi'); }
        go(function () { scrVdView(name); }, true);
      });
    }
  });
}

var vdTay = null;
function vdTayDoc() {
  if (!vdTay) return;
  var g = function (id) { var el = document.getElementById(id); return el ? el.value : ''; };
  vdTay.ma = g('vdtMa'); vdTay.khach = g('vdtKhach'); vdTay.sdt = g('vdtSdt');
  vdTay.diachi = g('vdtDiaChi'); vdTay.cod = g('vdtCod');
  vdTay.ngay = g('vdtNgay') || vdTay.ngay;
}
var VD_KHUNG_GIO = ['7h - 9h', '8h - 10h', '9h - 11h', '10h - 12h', '11h - 13h', '12h - 14h', '13h - 15h', '14h - 16h', '15h - 17h', '16h - 18h', '17h - 19h', '18h - 20h', '19h - 21h'];
var VD_KENH_TAO = [
  { ten: 'Shipper nội bộ', icon: '🛵', mo: 'Shipper của tiệm, có xếp tuyến và đối soát COD' },
  { ten: 'Ahamove', mo: 'Gọi xe qua API, báo giá được trước khi book' },
  { ten: 'GreenSM', mo: 'Gọi xe qua API, đang chờ khoá đối tác' },
  { ten: 'BE', mo: 'Đặt tay trên app BE rồi ghi mã vào đơn' },
  { ten: 'Grab', mo: 'Đặt tay trên app Grab rồi ghi mã vào đơn' },
  { ten: 'Lalamove', mo: 'Đặt tay trên app Lalamove rồi ghi mã vào đơn' },
  { ten: 'Khách tự lấy', icon: '🏬', mo: 'Khách ra tiệm nhận, không cần shipper' }
];
async function scrVdTao() {
  if (!isSales()) return baoTin('Chỉ sales tạo được vận đơn.');
  if (!vdTay) vdTay = { si: '', ma: '', khach: '', sdt: '', diachi: '', ngay: vdNgay || today(), gio: '', kenh: 'Shipper nội bộ', cod: '' };
  var html = '<div class="card" style="padding:12px 14px;display:grid;gap:10px">' +
    '<div class="hub" data-t="si" style="padding:10px 0;border:none"><div class="ht"><div class="h2">Lấy từ hoá đơn (tự điền khách + địa chỉ Pancake)</div><div class="h1">' + h(vdTay.si || 'Chọn hoá đơn hoặc bỏ qua...') + '</div></div><span style="color:#c3c8d4">&#8250;</span></div>' +
    '<input class="tin" id="vdtMa" placeholder="Số đơn (91xxx / GF-xxx)" value="' + h(vdTay.ma) + '">' +
    '<input class="tin" id="vdtKhach" placeholder="Tên khách" value="' + h(vdTay.khach) + '">' +
    '<input class="tin" id="vdtSdt" placeholder="SĐT khách" inputmode="tel" value="' + h(vdTay.sdt) + '">' +
    '<textarea class="tin" id="vdtDiaChi" rows="2" placeholder="Địa chỉ giao - gõ vài chữ rồi bấm gợi ý">' + h(vdTay.diachi) + '</textarea>' +
    '<div id="vdtGoiY" style="display:none;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden"></div>' +
    '<div id="vdtToaDo" style="font-size:12px;color:' + (vdTay.lat ? '#15803d' : '#a0a6b4') + '">' + (vdTay.lat ? '📍 Đã có toạ độ chính xác, xếp tuyến khỏi đoán' : 'Gõ địa chỉ rồi chọn gợi ý để lưu kèm toạ độ') + '</div>' +
    '<input class="tin" id="vdtCod" placeholder="Tiền thu hộ COD (đ), 0 nếu đã thanh toán" inputmode="numeric" value="' + h(vdTay.cod) + '">' +
    '</div>';
  html += '<div class="sec">Giao khi nào, kênh nào</div><div class="card" style="padding:12px 14px;display:grid;gap:10px">' +
    '<div style="display:flex;flex-direction:row;align-items:center;gap:10px"><span style="width:80px">Ngày giao</span><input type="date" class="hin" id="vdtNgay" value="' + h(vdTay.ngay) + '" style="flex:1;margin:0"></div>' +
    '<div class="hub" data-t="gio" style="padding:10px 0;border:none"><div class="ht"><div class="h2">Khung giờ giao</div><div class="h1">' + h(vdTay.gio || 'Chọn khung giờ...') + '</div></div><span style="color:#c3c8d4">&#8250;</span></div>' +
    '<div class="hub" data-t="kenh" style="padding:10px 0;border:none"><div class="ht"><div class="h2">Kênh giao</div><div class="h1">' + h(vdTay.kenh) + '</div></div><span style="color:#c3c8d4">&#8250;</span></div>' +
    '</div>';
  var b = frame('Tạo vận đơn', html, { footer: '<button class="btn" id="vdtLuu">Lưu vận đơn</button>' });
  b.addEventListener('click', async function (e) {
    if (e.target.closest('[data-t="si"]')) {
      vdTayDoc(); busy(true);
      var si;
      try { si = await getList('Sales Invoice', { fields: ['name', 'customer_name', 'grand_total', 'remarks', 'custom_pancake_display_id'], filters: { posting_date: ['>=', vdTay.ngay || today()], docstatus: ['<', 2], vgb_huy: 0 }, limit_page_length: 100, order_by: 'creation desc' }); }
      catch (er) { busy(false); return baoTin('Không tải được hoá đơn'); }
      busy(false);
      return sheet('Chọn hoá đơn', si.map(function (x) {
        var kh = (x.remarks || '').split(' - ');
        return { value: x.name, label: '#' + (x.custom_pancake_display_id || '?') + ' · ' + (kh[1] || x.customer_name || '') + ' · ' + money(x.grand_total) + ' đ', icon: '🧾' };
      }), vdTay.si, function (o) { vdTay.si = o.value; go(scrVdTao, true); }, true);
    }
    if (e.target.closest('[data-t="gio"]')) {
      vdTayDoc();
      var dsGio = [{ value: '', label: 'Không đặt khung giờ', icon: '🕓' }].concat(VD_KHUNG_GIO.map(function (t) { return { value: t, label: t, icon: '🕐' }; }));
      return sheet('Khung giờ giao', dsGio, vdTay.gio || '', function (o) { vdTay.gio = o.value; go(scrVdTao, true); });
    }
    if (e.target.closest('[data-t="kenh"]')) {
      vdTayDoc();
      return sheet('Kênh giao', VD_KENH_TAO.map(function (t) {
        var a = vdApp(t.ten); var it = { value: t.ten, label: t.ten, phu: t.mo };
        if (a) it.img = vdLogoApp(a); else it.icon = t.icon;
        return it;
      }), vdTay.kenh, function (o) { vdTay.kenh = o.value; go(scrVdTao, true); });
    }
  });
  var vdtTimer = null;
  var vdtOto = document.getElementById('vdtDiaChi');
  var vdtBox = document.getElementById('vdtGoiY');
  function vdtVeGoiY(ds) {
    if (!ds || !ds.length) { vdtBox.style.display = 'none'; vdtBox.innerHTML = ''; return; }
    vdtBox.innerHTML = ds.map(function (s, i) {
      return '<div data-gy="' + i + '" style="padding:10px 12px;border-bottom:1px solid #f1f2f4;cursor:pointer;font-size:14px">📍 ' + h(s.mo_ta) + '</div>';
    }).join('');
    vdtBox.style.display = 'block';
    vdtBox.onclick = async function (ev) {
      var el = ev.target.closest('[data-gy]');
      if (!el) return;
      var s = ds[parseInt(el.getAttribute('data-gy'), 10)];
      vdtBox.style.display = 'none';
      var td = document.getElementById('vdtToaDo');
      try {
        var ct = await api('vagabond.dia_chi.chi_tiet_dia_chi', { place_id: s.place_id });
        vdtOto.value = ct.dia_chi || s.mo_ta;
        vdTay.diachi = vdtOto.value; vdTay.lat = ct.lat || null; vdTay.lng = ct.lng || null;
        if (td) { td.innerHTML = vdTay.lat ? '📍 Đã có toạ độ chính xác, xếp tuyến khỏi đoán' : 'Chưa lấy được toạ độ, vẫn lưu được địa chỉ'; td.style.color = vdTay.lat ? '#15803d' : '#b45309'; }
      } catch (e) {
        vdtOto.value = s.mo_ta; vdTay.diachi = s.mo_ta;
        if (td) { td.innerHTML = 'Chưa lấy được toạ độ, vẫn lưu được địa chỉ'; td.style.color = '#b45309'; }
      }
    };
  }
  if (vdtOto) vdtOto.addEventListener('input', function () {
    vdTay.lat = null; vdTay.lng = null;
    if (vdtTimer) clearTimeout(vdtTimer);
    var q = (vdtOto.value || '').trim();
    if (q.length < 4) { vdtVeGoiY([]); return; }
    vdtTimer = setTimeout(async function () {
      try { var kq = await api('vagabond.dia_chi.goi_y_dia_chi', { q: q }); vdtVeGoiY((kq && kq.suggestions) || []); }
      catch (e) { vdtVeGoiY([]); }
    }, 450);
  });
  document.getElementById('vdtLuu').onclick = async function () {
    vdTayDoc();
    if (!vdTay.si && !vdTay.diachi.trim() && vdTay.kenh !== 'Khách tự lấy') return baoTin('Chọn hoá đơn hoặc nhập địa chỉ giao đã nhé.');
    busy(true);
    try {
      var nm = await api('vagabond.van_don.tao_van_don', {
        si_name: vdTay.si || '', ma_don: vdTay.ma, khach: vdTay.khach, sdt: vdTay.sdt, dia_chi: vdTay.diachi,
        ngay_giao: vdTay.ngay, gio_giao: vdTay.gio, tag_gio: vdTay.gio, lat: vdTay.lat || 0, lng: vdTay.lng || 0, kenh: vdTay.kenh, tien_thu_ho: parseFloat(vdTay.cod || 0) || 0
      });
      busy(false); toast('Đã tạo vận đơn'); vdTay = null;
      go(function () { scrVdView(nm); }, true);
    } catch (er) { busy(false); baoTin((er && er.message) || 'Lưu lỗi'); }
  };
}

var cpTay = null;
function cpTayDoc() {
  if (!cpTay) return;
  var g = function (id) { var el = document.getElementById(id); return el ? el.value : ''; };
  cpTay.tien = g('cptTien'); cpTay.shd = g('cptShd'); cpTay.noi = g('cptNoi'); cpTay.ghichu = g('cptGhiChu');
}
/* ---------- Chi phi xang xe - sua xe (anh Viet + chi Dung 13/08/2026) -------
   Truoc day man nay nam lap trong chan man Van don, chi co mot danh sach
   tho khong loc duoc gi. Chi Dung theo doi chi phi xe hang thang nen xin
   chip loc, chip trang thai va nut xuat Excel.

   Nay tach han ra mot cua rieng duoi nut Van don. */
var cpTu = null, cpDen = null, cpKhoang = 30, cpTT = '', cpLoai = '';

function cpKhoangNgay() {
  if (cpTu && cpDen) return { tu_ngay: cpTu, den_ngay: cpDen };
  var d = new Date(); d.setDate(d.getDate() - (cpKhoang - 1));
  var t = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  return { tu_ngay: t, den_ngay: today() };
}

async function scrVdChiPhi() {
  if (!cpTay) cpTay = { loai: 'Đổ xăng', tien: '', shd: '', noi: '', ghichu: '' };
  frame('Chi phí xăng xe - sửa xe', '<div class="emp"><div class="e1">⏳</div><div>Đang tải chi phí...</div></div>');
  var kq;
  try { kq = await api('vagabond.van_don.chi_phi_danh_sach', cpKhoangNgay()); }
  catch (e) { frame('Chi phí xăng xe - sửa xe', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var ds = kq.rows || [];
  var laKt = !!kq.la_ke_toan;

  var html = '<div class="card" style="padding:10px 12px">' + kmHangChip(
    [[7, '7 ngày'], [30, '30 ngày'], [90, '90 ngày'], [365, '1 năm']].map(function (x) {
      return posChipNut('data-cpng="' + x[0] + '"', x[1], !cpTu && cpKhoang === x[0]);
    }).join('')) + '</div>';
  html += '<div class="card" style="padding:10px 12px;display:flex;align-items:center;gap:8px">' +
    '<input type="date" class="hin" id="cpTu" value="' + h(cpKhoangNgay().tu_ngay) + '" style="flex:1;margin:0;min-width:0">' +
    '<span style="color:#9aa1ad">đến</span>' +
    '<input type="date" class="hin" id="cpDen" value="' + h(cpKhoangNgay().den_ngay) + '" max="' + today() + '" style="flex:1;margin:0;min-width:0">' +
    '</div>';

  /* Chip TRANG THAI va chip LOAI CHI: hai hang rieng, giao nhau duoc, moi
     chip deo so khoan cua nhom do. */
  var TT = [{ k: '', nhan: '📚 Tất cả', loc: function () { return true; } }];
  var TTICON = { 'Chờ duyệt': '⏳', 'Đã duyệt': '👍', 'Từ chối': '⛔', 'Đã hoàn ứng': '✅' };
  (kq.trang_thai_co || []).forEach(function (t) {
    TT.push({ k: t, nhan: (TTICON[t] || '•') + ' ' + h(t), loc: function (r) { return (r.trang_thai || '') === t; } });
  });
  var LO = [{ k: '', nhan: 'Mọi loại chi', loc: function () { return true; } }];
  (kq.loai_co || []).forEach(function (t) {
    LO.push({ k: t, nhan: h(t), loc: function (r) { return (r.loai || '') === t; } });
  });
  if (!locTim(TT, cpTT) || locTim(TT, cpTT).k !== cpTT) cpTT = '';
  if (!locTim(LO, cpLoai) || locTim(LO, cpLoai).k !== cpLoai) cpLoai = '';
  var fT = locTim(TT, cpTT), fL = locTim(LO, cpLoai);
  html += '<div class="card" style="padding:10px 12px;display:flex;flex-direction:column;gap:7px">' +
    locHang(TT, cpTT, 'data-cptt', ds) +
    locHang(LO, cpLoai, 'data-cplo', ds.filter(fT.loc)) + '</div>';

  var loc = ds.filter(function (r) { return fT.loc(r) && fL.loc(r); });
  var tong = loc.reduce(function (a, r) { return a + Number(r.so_tien || 0); }, 0);
  var nhanLoc = [cpTT ? fT.nhan : '', cpLoai ? fL.nhan : ''].filter(Boolean).join(' · ');
  html += '<div class="card" style="padding:12px 14px;background:#f0fdfa;border:1.5px solid #99f6e4">' +
    '<div style="font-size:11.5px;color:#0f766e;font-weight:800;letter-spacing:.3px">TỔNG THEO BỘ LỌC' +
    (nhanLoc ? ' · ' + h(nhanLoc) : '') + '</div>' +
    '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:5px">' +
    '<span style="font-size:13.5px;color:#374151">' + loc.length + ' khoản chi</span>' +
    '<b style="font-size:20px;color:#0f766e">' + money(tong) + ' đ</b></div></div>';

  if (laKt || isSales()) {
    html += '<button class="btn gh" id="cpXuat" style="margin:0 0 10px">📊 Xuất Excel ' + loc.length + ' khoản</button>';
  }

  if (vdLaShipper() || laKt) {
    html += '<div class="sec">Khai chi phí mới (chụp kèm hoá đơn Petrolimex, biên lai...)</div>' +
      '<div class="card" style="padding:12px 14px;display:grid;gap:10px">' +
      '<div class="hub" data-t="loai" style="padding:10px 0;border:none"><div class="ht"><div class="h2">Loại chi phí</div><div class="h1">' + h(cpTay.loai) + '</div></div><span style="color:#c3c8d4">&#8250;</span></div>' +
      '<input class="tin" id="cptTien" placeholder="Số tiền (đ)" inputmode="numeric" value="' + h(cpTay.tien) + '">' +
      '<input class="tin" id="cptShd" placeholder="Số hoá đơn / biên lai (nếu có)" value="' + h(cpTay.shd) + '">' +
      '<input class="tin" id="cptNoi" placeholder="Nơi chi (vd Petrolimex CHXD 25)" value="' + h(cpTay.noi) + '">' +
      '<input class="tin" id="cptGhiChu" placeholder="Ghi chú" value="' + h(cpTay.ghichu) + '">' +
      '<button class="btn" id="cptLuu">📷 Chụp hoá đơn và gửi duyệt</button>' +
      '</div>';
  }

  html += '<div class="sec">' + (laKt ? 'Tất cả chi phí · bấm vào để duyệt' : 'Chi phí của tôi') + '</div><div class="card">';
  if (!ds.length) html += '<div class="emp" style="padding:20px"><div class="e1">⛽</div><div>Chưa có khoản nào trong khoảng này.</div></div>';
  else if (!loc.length) html += '<div class="emp" style="padding:20px"><div class="e1">✅</div><div>Không có khoản nào thuộc nhóm <b>' + h(nhanLoc) + '</b>.</div></div>';
  loc.forEach(function (r) {
    var vn = String(r.ngay || '').split('-').reverse().join('/');
    html += '<div class="hub" data-cp="' + h(r.name) + '"><div class="hi">' + (TTICON[r.trang_thai] || '⏳') + '</div>' +
      '<div class="ht"><div class="h1">' + h(r.loai) + ' · ' + money(r.so_tien) + ' đ</div>' +
      '<div class="h2">' + vn + ' · ' + h((r.shipper || '').split('@')[0]) + ' · ' + h(r.trang_thai) + (r.so_hoa_don ? ' · HĐ ' + h(r.so_hoa_don) : '') + '</div>' +
      (r.nha_cung_cap ? '<div class="h2">' + h(r.nha_cung_cap) + '</div>' : '') +
      (r.ghi_chu_duyet ? '<div class="h2" style="color:#b3261e">' + h(r.ghi_chu_duyet) + '</div>' : '') + '</div>' +
      (r.anh_hoa_don ? '<a href="' + h(r.anh_hoa_don) + '" target="_blank">📷</a>' : '') + '</div>';
  });
  html += '</div>';

  var b = frame('Chi phí xăng xe - sửa xe', html, {});
  Array.prototype.forEach.call(document.querySelectorAll('[data-cpng]'), function (el) {
    el.onclick = function () { cpKhoang = +el.getAttribute('data-cpng'); cpTu = null; cpDen = null; go(scrVdChiPhi, true); };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-cptt]'), function (el) {
    el.onclick = function () { cpTT = el.getAttribute('data-cptt'); go(scrVdChiPhi, true); };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-cplo]'), function (el) {
    el.onclick = function () { cpLoai = el.getAttribute('data-cplo'); go(scrVdChiPhi, true); };
  });
  var it = document.getElementById('cpTu'), id2 = document.getElementById('cpDen');
  var doiNgay = function () {
    if (!it.value || !id2.value) return;
    if (it.value > id2.value) return toast('Ngày bắt đầu phải trước ngày kết thúc.');
    cpTu = it.value; cpDen = id2.value; go(scrVdChiPhi, true);
  };
  if (it) it.onchange = doiNgay;
  if (id2) id2.onchange = doiNgay;

  var bx = document.getElementById('cpXuat');
  if (bx) bx.onclick = async function () {
    busy(true);
    try {
      var ts = cpKhoangNgay();
      if (cpTT) ts.trang_thai = cpTT;
      if (cpLoai) ts.loai = cpLoai;
      var f = await api('vagabond.van_don.chi_phi_xuat_excel', ts);
      busy(false);
      bcTaiVe(f.ten_file, f.b64);
      toast('Đã tải ' + f.ten_file);
    } catch (e) { busy(false); baoTin((e && e.message) || 'Xuất Excel lỗi'); }
  };

  b.addEventListener('click', function (e) {
    if (e.target.closest('[data-t="loai"]')) {
      cpTayDoc();
      return sheet('Loại chi phí', (kq.loai_co || []).map(function (t) { return { value: t, label: t, icon: '⛽' }; }), cpTay.loai, function (o) { cpTay.loai = o.value; go(scrVdChiPhi, true); });
    }
    var cp = e.target.closest('[data-cp]');
    if (cp && laKt && !e.target.closest('a')) {
      var nm = cp.getAttribute('data-cp');
      return sheet('Xử lý ' + nm, [
        { value: 'duyet', label: 'Duyệt khoản chi này', icon: '👍' },
        { value: 'hoan_ung', label: 'Đã hoàn ứng (đưa tiền lại shipper)', icon: '✅' },
        { value: 'tu_choi', label: 'Từ chối', icon: '⛔' }
      ], null, async function (o) {
        var gc = o.value === 'tu_choi' ? (await hoiNhap('Lý do từ chối?', '') || '') : '';
        if (o.value === 'tu_choi' && !gc) return;
        busy(true);
        try { await api('vagabond.van_don.duyet_chi_phi', { name: nm, hanh_dong: o.value, ghi_chu: gc }); busy(false); toast('Đã cập nhật'); }
        catch (er) { busy(false); baoTin((er && er.message) || 'Lỗi'); }
        go(scrVdChiPhi, true);
      });
    }
  });

  var nl = document.getElementById('cptLuu');
  if (nl) nl.onclick = function () {
    cpTayDoc();
    var tien = parseFloat(cpTay.tien || 0) || 0;
    if (tien <= 0) return baoTin('Nhập số tiền đã nhé.');
    vdChupAnh(async function (blob) {
      try {
        var nm = await api('vagabond.van_don.tao_chi_phi', { loai: cpTay.loai, so_tien: tien, so_hoa_don: cpTay.shd, nha_cung_cap: cpTay.noi, ghi_chu: cpTay.ghichu });
        var fu = await vdUpload(blob, 'Chi Phi Shipper', nm, 'anh_hoa_don');
        await api('vagabond.van_don.gan_anh', { doctype: 'Chi Phi Shipper', name: nm, fieldname: 'anh_hoa_don', file_url: fu });
        busy(false); toast('Đã gửi, chờ Thu mua/Kế toán duyệt'); cpTay = null;
      } catch (er) { busy(false); baoTin((er && er.message) || 'Lỗi khi lưu'); }
      go(scrVdChiPhi, true);
    });
  };
}

var APPVER = '252';
function freshN() { try { return parseInt(sessionStorage.getItem('vgb_fresh') || '0', 10) || 0; } catch (e) { return 0; } }
function setFreshN(n) { try { sessionStorage.setItem('vgb_fresh', String(n)); } catch (e) { } }
function clearFresh() { try { sessionStorage.removeItem('vgb_fresh'); } catch (e) { } }
function hardNav() { window.location.replace(location.pathname + '?v=' + APPVER + '&t=' + (new Date()).getTime()); }
function goFresh() {
  var n = freshN();
  if (n >= 2) return false;
  setFreshN(n + 1);
  hardNav();
  return true;
}
function napAgain(ms) { return new Promise(function (res) { setTimeout(res, ms); }); }
async function whoAmI() {
  try {
    var r = await fetch('/api/method/frappe.auth.get_logged_user', { credentials: 'same-origin', headers: { 'Accept': 'application/json' } });
    if (!r.ok) return '';
    var j = await r.json();
    return j && j.message ? j.message : '';
  } catch (e) { return ''; }
}
function adopt(u) {
  S.user = u; S.me.user = u;
  try { if (window.frappe) { if (!frappe.session) frappe.session = {}; frappe.session.user = u; } } catch (e) { }
}
/* Xin quyen thong bao SAU khi da vao duoc man hinh chinh.

   Khong await, va cham 1,5 giay: xin quyen la viec nen, hop thoai cua trinh
   duyet ma bat ngay luc app dang ve man hinh chinh thi vua che mat man vua
   de bi bam Chan theo phan xa. Ban than pwaXinQuyenThongBao con tu im lang
   neu app chua duoc them ra man hinh chinh.

   Ham nay ton tai vi ban v242 khai pwaXinQuyenThongBao ma khong cho nao goi. */
function pwaSauDangNhap() {
  try { setTimeout(function () { pwaXinQuyenThongBao(0); }, 1500); } catch (e) { }
}

async function __boot(){
  clearFresh();
  try {
    var real = await whoAmI();
    if (real && real !== 'Guest') { adopt(real); reset(scrHome); pwaSauDangNhap(); return; }
    if (real === 'Guest') { reset(scrLogin); return; }
    syncUser();
    for (var i = 0; i < 5 && (!S.user || S.user === 'Guest'); i++) { await napAgain(200); syncUser(); }
    if (S.user && S.user !== 'Guest') { reset(scrHome); pwaSauDangNhap(); return; }
    reset(scrLogin);
  } catch(e) { var el=document.getElementById('vgb'); if(el) el.textContent = 'Loi khoi dong: '+String(e.message||e); }
}
if (document.readyState === 'complete') { __boot(); } else { window.addEventListener('load', __boot); }
window.addEventListener('popstate', function (ev) {
  /* Nut ‹ trong app da tu lui va goi history.back(), popstate nay chi la dong bo, bo qua */
  if (VGB_LUI_TAY > 0) { VGB_LUI_TAY--; return; }
  var st = ev.state;
  var d = (st && typeof st.vgbD === 'number') ? st.vgbD : 0;
  if (d + 1 < S.stack.length) {
    if (roiPhieuDo(S.stack[d])) {
      var giu = S.stack.length - 1;
      confirmSheet('Phiếu đang soạn dở', 'Rời màn này thì danh sách món đang chọn sẽ mất.', 'Rời đi, bỏ phiếu nháp', true)
        .then(function (ok) {
          if (ok) { S.draft = null; S.stack.length = d + 1; render(); }
          else { try { history.pushState({ vgbD: giu }, '', location.href); } catch (e) { } }
        });
      return;
    }
    S.stack.length = d + 1; render(); return;
  }
  if (d + 1 > S.stack.length) {
    /* Nut Tien hoac moc cu con sot lai: khong dung lai man hinh nao duoc, chi dong bo lai moc */
    try { history.replaceState({ vgbD: S.stack.length - 1 }, '', location.href); } catch (e) { }
  }
});
try { history.replaceState({ vgbD: 0 }, '', location.href); } catch (e) { }


/* ---------- Van don: nguoi nhan, phan cong, va phieu in (02/08/2026) ---------- */
function vdKhoiNhan(d) {
  var s = '';
  var khac = (d.nguoi_nhan || '') && ((d.nguoi_nhan || '') !== (d.khach || '') || (d.sdt_nhan || '') !== (d.sdt || ''));
  if (khac) {
    s += '<div style="font-size:13px;margin-top:2px">Người nhận: <b>' + h(d.nguoi_nhan) + '</b>'
      + (d.sdt_nhan ? ' · <a href="tel:' + h(d.sdt_nhan) + '">' + h(d.sdt_nhan) + '</a>' : '') + '</div>';
  }
  var t = [];
  if (d.goi_truoc) t.push(vdThe('#b45309', '📞 Gọi trước khi giao'));
  if (d.chup_truoc) t.push(vdThe('#7c3aed', '📷 Gửi ảnh trước khi giao'));
  if (t.length) s += '<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:6px">' + t.join('') + '</div>';
  if (d.ghi_chu_in) s += '<div style="margin-top:8px;background:#f7f1e6;border-left:3px solid #c9a24b;padding:8px 10px;font-size:13px;white-space:pre-wrap">' + h(d.ghi_chu_in) + '</div>';
  return s;
}
function vdNutPhanCong(d) {
  var b = [];
  if (d.dia_chi || (d.lat && d.lng)) b.push('<button class="btn gh" data-va="chiduong" style="flex:1">' + vdAnhMap(20) + ' Chỉ đường</button>');
  if (isSales() && d.trang_thai !== 'Đã giao' && d.trang_thai !== 'Huỷ') {
    var ten = vdTen(d.shipper);
    b.push('<button class="btn gh" data-va="phancong" style="flex:1">🛵 ' + (ten ? h(ten) : 'Phân công') + '</button>');
  }
  if (!b.length) return '';
  return '<div style="display:flex;gap:8px;margin-top:10px">' + b.join('') + '</div>';
}

var VD_CSS = ''
  + '@import url("https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700&family=Inter:wght@300;400;500;600;700&display=swap");'
  + '*{margin:0;padding:0;box-sizing:border-box}'
  + 'body{font-family:Inter,sans-serif;color:#1f1c19;background:#e9e5de;padding:8mm 0}'
  + '.p{width:190mm;margin:0 auto 5mm;background:#fff;border:1.5px solid #1f1c19;page-break-inside:avoid;break-inside:avoid}'
  + '.hd{background:#f2efe9;border-bottom:1.5px solid #1f1c19;padding:9px 14px;display:flex;justify-content:space-between;align-items:center;gap:14px}'
  + '.bd{font-family:"Cormorant Garamond",serif;font-size:19px;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;color:#1f1c19}'
  + '.dt{font-family:"Cormorant Garamond",serif;font-size:15px;letter-spacing:4px;text-transform:uppercase;font-weight:700;color:#1f1c19}'
  + '.stt{font-size:10.5px;letter-spacing:.8px;text-transform:uppercase;color:#6b645b}'
  + '.qr{width:21mm;height:21mm;flex:0 0 auto}'
  + '.qr svg{width:100%;height:100%;display:block}'
  + '.gr{display:grid;grid-template-columns:1fr 1fr;gap:0 16px;padding:10px 14px;border-bottom:1px solid #d9d3c9}'
  + '.f{padding:3px 0}'
  + '.l{text-transform:uppercase;letter-spacing:1px;font-size:8.5px;color:#6b645b;font-weight:700}'
  + '.v{font-size:13px;font-weight:500;line-height:1.45;color:#1f1c19}'
  + '.v.big{font-size:15px;font-weight:700}'
  + '.v .mo{color:#8a8279;font-weight:400}'
  + '.wide{grid-column:1 / -1}'
  + '.the{display:inline-block;border:1.2px solid #1f1c19;border-radius:3px;padding:1px 7px;font-size:10px;font-weight:700;margin:3px 5px 0 0;text-transform:uppercase;letter-spacing:.5px}'
  + '.note{margin:9px 14px;background:#f4f2ed;border-left:3px solid #1f1c19;padding:8px 11px;font-size:12.5px;white-space:pre-wrap;line-height:1.5}'
  + '.note b{display:block;text-transform:uppercase;letter-spacing:1px;font-size:8.5px;color:#6b645b;margin-bottom:3px}'
  + 'table{width:100%;border-collapse:collapse;font-size:12px}'
  + 'thead th{background:#f2efe9;color:#3d372f;text-transform:uppercase;letter-spacing:1px;font-size:8.5px;font-weight:700;padding:6px 8px;text-align:left;border-bottom:1px solid #1f1c19}'
  + 'th.q,th.a,td.q,td.a{text-align:right}'
  + 'tbody td{padding:5px 8px;border-bottom:1px solid #e6e1d8;vertical-align:top}'
  + 'td.n{color:#8a8279;width:20px}'
  + '.code{color:#8a8279;font-size:10px}'
  + '.cod{padding:9px 14px;display:flex;justify-content:space-between;align-items:center;gap:16px;border-top:1.5px solid #1f1c19}'
  + '.dan{font-size:11.5px;line-height:1.45;color:#3d372f;flex:1}'
  + '.cod .so{font-family:"Cormorant Garamond",serif;font-size:22px;font-weight:700;color:#1f1c19;white-space:nowrap}'
  + '.sig{display:flex;gap:18px;padding:10px 14px 4px}'
  + '.sig div{flex:1;text-align:center;font-size:9.5px;color:#6b645b;text-transform:uppercase;letter-spacing:1px}'
  + '.sig span{display:block;border-top:1px dotted #8a8279;margin-top:32px;padding-top:4px}'
  + '.ft{background:#f2efe9;border-top:1.5px solid #1f1c19;color:#3d372f;padding:6px 14px;font-size:9.5px;letter-spacing:.3px;text-align:center}'
  + '.ft b{color:#1f1c19}'
  + '@page{size:A4;margin:7mm}'
  + '@media print{body{background:#fff;padding:0}.p{margin:0 auto 3mm;width:100%}}';

function vdO(nhan, giatri, to) {
  if (!giatri) return '';
  return '<div class="f"><div class="l">' + nhan + '</div><div class="v' + (to ? ' big' : '') + '">' + giatri + '</div></div>';
}
var VD_DAN = 'Quý khách vui lòng kiểm tra bánh khi nhận, bảo quản ngăn mát tủ lạnh và dùng hết trong ngày.';
function vdPhieuHtml(d) {
  var s = '<div class="p">';
  s += '<div class="hd"><div><div class="bd">The Vagabond Pâtisserie</div>'
    + '<div class="stt">' + h(d.name || '') + (d.nguoi_tao ? ' · lập bởi ' + h(d.nguoi_tao) : '') + '</div></div>'
    + '<div style="text-align:right"><div class="dt">Phiếu giao hàng</div>'
    + '<div class="stt">' + h(d.trang_thai || '') + '</div></div>'
    + (d.qr ? '<div class="qr">' + d.qr + '</div>' : '')
    + '</div>';

  s += '<div class="gr">';
  s += vdO('Số đơn', h(d.ma_don || d.name || ''), true);
  s += vdO('Ngày giao', h(String(d.ngay_giao || '').split('-').reverse().join('/')) + (d.tag_gio ? ' · ' + h(d.tag_gio) : (d.gio_giao ? ' · ' + h(d.gio_giao) : '')), true);
  s += vdO('Người đặt', h(d.khach || '') + (d.sdt ? ' · ' + h(d.sdt) : ''));
  s += vdO('Người nhận', (d.nguoi_nhan ? h(d.nguoi_nhan) : '<span class="mo">như người đặt</span>') + (d.sdt_nhan ? ' · ' + h(d.sdt_nhan) : ''));
  s += '<div class="f wide"><div class="l">Địa chỉ giao</div><div class="v big">' + h(d.dia_chi || '') + '</div></div>';
  s += vdO('Phường / Xã', h(d.phuong || '') || '<span class="mo">chưa rõ</span>');
  var ten = d.ten_shipper || (d.shipper ? String(d.shipper).split('@')[0] : '');
  s += vdO('Shipper giao', (ten ? h(ten) : '<span class="mo">chưa phân công</span>') + (d.chuyen ? ' · ' + h(d.chuyen) : '') + (d.thu_tu ? ' · điểm số ' + d.thu_tu : ''), true);
  s += vdO('Kênh giao', h(d.kenh || '') + (d.booking_id ? ' · ' + h(d.booking_id) : ''));
  s += vdO('Giờ dự kiến đến', h(d.gio_du_kien || '') + (d.km_chang ? ' · ' + d.km_chang + ' km' : ''));
  s += vdO('Hoá đơn', h(d.hoa_don || ''));
  var the = [];
  if (d.goi_truoc) the.push('Gọi trước khi giao');
  if (d.chup_truoc) the.push('Chụp ảnh gửi trước khi giao');
  (String(d.the_don || '').split(', ')).forEach(function (x) { x = x.trim(); if (x && the.indexOf(x) < 0) the.push(x); });
  if (the.length) s += '<div class="f wide"><div class="l">Lưu ý khi giao</div><div>' + the.map(function (x) { return '<span class="the">' + h(x) + '</span>'; }).join('') + '</div></div>';
  s += '</div>';

  if (d.mon && d.mon.length) {
    s += '<table><thead><tr><th style="width:20px">#</th><th>Sản phẩm</th><th class="q" style="width:42px">SL</th><th class="a" style="width:92px">Thành tiền</th></tr></thead><tbody>';
    d.mon.forEach(function (m, i) {
      s += '<tr><td class="n">' + (i + 1) + '</td><td>' + h(m.item_name || m.item_code || '')
        + (m.item_code ? '<div class="code">' + h(m.item_code) + '</div>' : '') + '</td>'
        + '<td class="q">' + (m.qty != null ? m.qty : '') + '</td>'
        + '<td class="a">' + (Number(m.amount) ? money(m.amount) + ' đ' : '-') + '</td></tr>';
    });
    s += '</tbody></table>';
  }

  if (d.ghi_chu_in) s += '<div class="note"><b>Ghi chú giao hàng</b>' + h(d.ghi_chu_in) + '</div>';
  if (d.ghi_chu) s += '<div class="note" style="border-left-color:#8a8279"><b>Ghi chú nội bộ</b>' + h(d.ghi_chu) + '</div>';

  s += '<div class="cod"><div class="dan">' + VD_DAN + '</div>'
    + '<div style="text-align:right"><div class="l">Tiền thu hộ (COD)</div>'
    + '<div class="so">' + (Number(d.tien_thu_ho) ? money(d.tien_thu_ho) + ' đ' : 'Không thu') + '</div></div></div>';
  s += '<div class="sig"><div><span>Người giao</span></div><div><span>Người nhận ký</span></div></div>';
  s += '<div class="ft"><b>THE VAGABOND PÂTISSERIE</b> · 307/1 Nguyễn Văn Trỗi &amp; 9 Trần Cao Vân · Cảm ơn Quý khách đã tin chọn</div>';
  return s + '</div>';
}

// Logo Google Maps ve bang SVG cho net o moi co, khong phai tai anh ngoai.
var VD_GMAP_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">'
  + '<defs><clipPath id="k"><rect x="3" y="3" width="42" height="42" rx="6"/></clipPath></defs>'
  + '<g clip-path="url(#k)">'
  + '<rect x="3" y="3" width="42" height="42" fill="#1B9E4B"/>'
  + '<polygon points="3,45 24,20 45,45" fill="#1A73E8"/>'
  + '<polygon points="3,33 25,3 34,3 3,45" fill="#FBD200"/>'
  + '<polygon points="30,3 45,20 45,45 21,45" fill="#E8EAED"/>'
  + '</g>'
  + '<path d="M33 4c-5 0-9 4-9 9 0 6.6 9 17 9 17s9-10.4 9-17c0-5-4-9-9-9z" fill="#F03127"/>'
  + '<circle cx="33" cy="13" r="4.2" fill="#9E1B14"/></svg>';
var VD_GMAP = 'data:image/svg+xml;utf8,' + encodeURIComponent(VD_GMAP_SVG);
function vdAnhMap(px) {
  return '<img src="' + VD_GMAP + '" alt="Google Maps" style="width:' + px + 'px;height:' + px + 'px;display:inline-block;vertical-align:middle">';
}
function vdTen(u) {
  if (!u) return '';
  var x = (vtShipper || []).filter(function (s) { return s.user === u; })[0];
  return x && x.ten ? x.ten : String(u).split('@')[0];
}
function vdDich(r) {
  if (r.lat && r.lng) return encodeURIComponent(r.lat + ',' + r.lng);
  return encodeURIComponent(r.dia_chi || '');
}
function vdMoDuong(dich) {
  var u = 'https://www.google.com/maps/dir/?api=1&travelmode=driving&destination=' + dich;
  var a = document.createElement('a');
  a.href = u;
  a.target = '_blank';
  a.rel = 'noopener';
  a.style.display = 'none';
  document.body.appendChild(a);
  a.click();
  setTimeout(function () { if (a.parentNode) a.parentNode.removeChild(a); }, 0);
}
function vdNutDong(r, chon) {
  if (chon) return '';
  var b = [];
  if (r.dia_chi || (r.lat && r.lng)) b.push('<button class="btn gh" data-di="' + vdDich(r) + '" style="width:auto;padding:3px 10px;line-height:0">' + vdAnhMap(24) + '</button>');
  if (isSales() && r.trang_thai !== 'Đã giao' && r.trang_thai !== 'Huỷ') {
    b.push('<button class="btn gh" data-pc="1" style="width:auto;padding:4px 10px;font-size:12px">🛵 ' + (r.shipper ? h(vdTen(r.shipper)) : 'Phân công') + '</button>');
  }
  if (!b.length) return '';
  return '<div style="display:flex;gap:6px">' + b.join('') + '</div>';
}
var vdAhaDv = null, vdDaGanLamMoi = 0;
function vdDangOManDS() {
  return S.stack.length && S.stack[S.stack.length - 1] === scrVanDon;
}
var vdAnLuc = 0;
function vdTuLamMoi() {
  if (vdDaGanLamMoi) return;
  vdDaGanLamMoi = 1;
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) { vdAnLuc = Date.now(); return; }
    /* Tren dien thoai, bang chon ngay cua he dieu hanh lam trang bi coi la an
       di. Neu ve lai man hinh ngay luc quay ve thi o ngay bi dung ve gia tri
       cu truoc khi kip bao da doi - do la ly do Loan Anh khong chon duoc ngay
       con anh Viet ngoi may tinh thi chon duoc. Chi lam moi khi that su roi
       di cho khac tren 20 giay. */
    if (Date.now() - vdAnLuc < 20000) return;
    if (vdDangOManDS()) go(scrVanDon, true);
  });
  setInterval(function () {
    if (!document.hidden && vdDangOManDS() && !isSales()) go(scrVanDon, true);
  }, 45000);
}

async function scrVdGoiXe(name, kenh) {
  frame('Gọi xe ' + kenh, '<div class="emp"><div class="e1">⏳</div></div>');
  if (kenh !== 'Ahamove') {
    frame('Gọi xe ' + kenh, '<div class="emp"><div class="e1">🔑</div><div>' + h(kenh) + ' chưa cấp khoá API. Điền khoá vào Vagabond Settings là màn này chạy được ngay.</div></div>');
    return;
  }
  var d;
  try {
    d = await api('frappe.client.get', { doctype: 'Van Don', name: name });
    if (!vdAhaDv) vdAhaDv = await api('vagabond.van_don.aha_dich_vu');
  } catch (e) {
    frame('Gọi xe ' + kenh, '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không đọc được') + '</div></div>');
    return;
  }
  var dsDv = (vdAhaDv && vdAhaDv.dich_vu) || [];
  if (!dsDv.length) { frame('Gọi xe ' + kenh, '<div class="emp"><div class="e1">⚠️</div><div>Ahamove không trả về loại xe nào.</div></div>'); return; }
  var chonDv = (vdAhaDv && vdAhaDv.mac_dinh) || dsDv[0].id;
  var chonAdd = {};
  var gia = null, dangTinh = false;
  function dvHienTai() { for (var i = 0; i < dsDv.length; i++) { if (dsDv[i].id === chonDv) return dsDv[i]; } return dsDv[0]; }
  function ve() {
    var dv = dvHienTai();
    var html = '<div class="card" style="padding:12px 14px;line-height:1.7">' +
      '<div><b>' + (d.ma_don ? '#' + h(d.ma_don) : h(d.name)) + '</b> · ' + h(d.khach || 'Khách lẻ') + '</div>' +
      '<div style="font-size:13px">' + h(d.dia_chi || '(chưa có địa chỉ)') + '</div>' +
      (d.tien_thu_ho ? '<div><b>Thu hộ (COD): ' + money(d.tien_thu_ho) + ' đ</b></div>' : '') +
      '</div>';
    html += '<div class="sec">Loại xe</div><div class="card">';
    dsDv.forEach(function (x) {
      html += '<div class="row" data-dv="' + h(x.id) + '" style="cursor:pointer"><div>' + h(x.ten) + '</div><div>' + (x.id === chonDv ? '✓' : '') + '</div></div>';
    });
    html += '</div>';
    html += '<div class="sec">Dịch vụ thêm (Ahamove tính thêm tiền)</div><div class="card">';
    if (!(dv.addon || []).length) html += '<div class="row"><div style="color:#6b7280">Loại xe này không có dịch vụ thêm.</div></div>';
    (dv.addon || []).forEach(function (r) {
      html += '<div class="row" data-add="' + h(r.id) + '" style="cursor:pointer"><div>' + (chonAdd[r.id] ? '☑️ ' : '⬜ ') + h(r.ten) + '</div><div style="color:#6b7280">' + (r.gia ? '+' + money(r.gia) + ' đ' : '') + '</div></div>';
    });
    html += '</div>';
    html += '<div class="card" style="padding:12px 14px;margin-top:10px">' +
      (dangTinh ? '<div style="color:#6b7280">Đang hỏi giá Ahamove...</div>' :
        (gia === null ? '<div style="color:#6b7280">Bấm Xem giá để Ahamove báo cước.</div>' :
          '<div style="font-size:17px"><b>Cước: ' + money(gia.tong) + ' đ</b>' + (gia.km ? ' <span style="color:#6b7280;font-size:13px">· ' + num(gia.km) + ' km</span>' : '') + '</div>')) +
      '</div>';
    var ft = '<button class="btn gh" id="gxGia" style="flex:1">Xem giá</button>' +
      '<button class="btn" id="gxDat" style="flex:1"' + (gia === null ? ' disabled' : '') + '>Gọi xe</button>';
    var b = frame('Gọi xe Ahamove', html, { footer: '<div style="display:flex;gap:8px">' + ft + '</div>' });
    b.addEventListener('click', function (e) {
      var dvEl = e.target.closest('[data-dv]');
      if (dvEl) { chonDv = dvEl.getAttribute('data-dv'); chonAdd = {}; gia = null; ve(); return; }
      var adEl = e.target.closest('[data-add]');
      if (adEl) { var k = adEl.getAttribute('data-add'); chonAdd[k] = !chonAdd[k]; gia = null; ve(); return; }
    });
    document.getElementById('gxGia').onclick = async function () {
      dangTinh = true; ve();
      try {
        gia = await api('vagabond.van_don.aha_bao_gia', { name: name, service_id: chonDv, requests_them: JSON.stringify(Object.keys(chonAdd).filter(function (k) { return chonAdd[k]; })) });
      } catch (e2) { baoTin((e2 && e2.message) || 'Ahamove không báo giá được'); }
      dangTinh = false; ve();
    };
    document.getElementById('gxDat').onclick = async function () {
      if (gia === null) return;
      if (!await xacNhan('Gọi xe Ahamove cho đơn này, cước ' + money(gia.tong) + ' đ?')) return;
      busy(true);
      try {
        await api('vagabond.van_don.book_xe', { name: name, kenh: 'Ahamove', service_id: chonDv, requests_them: JSON.stringify(Object.keys(chonAdd).filter(function (k) { return chonAdd[k]; })) });
        busy(false); toast('Đã gọi xe, Ahamove đang tìm tài xế');
        go(function () { scrVdView(name); }, true);
      } catch (e3) { busy(false); baoTin((e3 && e3.message) || 'Gọi xe lỗi'); }
    };
  }
  ve();
}
var VD_APPS = [
  { ten: 'Ahamove', api: 1, anh: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEgAAABICAMAAABiM0N1AAAAkFBMVEX///////7+/////v7//v3+/v/+/v7//fz9/v79/f78/f39/Pz/+vf6+/z+9/P19/n38vDq7vLm4+Tj2NXAzdrDwcX/nGGar8SAm7b/jUf/hj7/gjb/gTL/gDP8gDP/fzP/fzL/fzH7fzL/fC7/eir/dyV9hJNhgqNMbpMzXYggTHsOP3ICNGoALWUAKmMAJF4QARquAAADF0lEQVR42u1Wf5OaMBAN4oEyQC4xJRGPFkSbHwT4/t+uu6jt6c10Dq//leeEkBhf3r7sZiRkwYIFC/5LhHG8/ic0U/dlqpCQ192Of5kpJGlRns5NsfsCUxAE63VenNuqqs7t80zh9CzOh6qu68NpnwfBk0xpnqe706FGNIfzjsTPsKzJrizL/aGpJiKQVDyhKAiDOECisq1vqFo+26XrzjGGdr6GVh/OxfzYwJ0rwOumPjbN8a067dO5p/Va/gaEdrTueHTm7ftpZgYA0f6Ctm2rG9HPt2dii/M0Tddw9HhkzXcMrWmqtsxn2o1m5/nrHvXUP6oJmAHzUynMi7o8tD+QpzlNmIiKa7p/XhFUannR0xyKCXB48P46kwkzoJiKA8IJYkAAefBMbDFBp6sKajUNwyC4jKFM1rOvxf25RWuuGsJ1Ok3AcKZLcbEvMJVuOQg1DEbti2dMQtw5EsefqZFNkly6iLy77IM/nqxRShg8ddE+XEDBhwtp9eFXL4RLEZEIOgaDT+IjD4kiM3hBMqJGuc2mmWQTbWA+gli3W+RebeF1tcHQ4bHCSUofeLZEdJ1XSDTIaafto4XwASQ3HdOISUlJ9H5ZAgTKObpBIiGQhwnOOOWcC5YIgeszIRhMM0IyznFEuQIj7ogItR3TAzAo73qvMyK7oXNe2K4brO17ywm3/dBJ4S19kYPmdhicuOzwXpAYNDZQ1DtlByF6J7UHot4Y77UZNbW9Vq4XBraz0PVKdu7RooTo3mrTOY5mY1OoTvegiNHOZcwb3IqIXotRi94I76S0sDa5N5I573vfeYkeJXKUuoe/DcBmHcvAO9YZAb8i0FPnDPjonXXWPhAlBIKGeKU306kBkRw1E+iRY3QisrxzgulRgYudYwzUU6XurV5F1I4C3+zIMTQ5qsyMHYjE0DKwgnlHJEgeDX3h3aDIZWRZFN1HZnS2TbIXacU3K4gAyVQZpTTXmmZaZxQWEKHNlDbKcEw8bVT2cPafQ3StpfejD7hUPoEawOqH6oCGiPCLW9vixLQ4In9GCxYsWLDg7/gF2A1dchuCKjkAAAAASUVORK5CYII=' },
  { ten: 'GreenSM', api: 1, nen: '#00A94F', chu: '#FFFFFF', nhan: 'GSM' },
  { ten: 'Grab', api: 0, anh: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEgAAABICAMAAABiM0N1AAAAkFBMVEX///////7+///+//79//7+/v79/v38///8/v78/v38/vz7/vz6/vz6/fv2/Pnx+/bs+fLi9uvb9ObP8N7H7tjA7NO26Muk4r6V3rSL2quE2Kd71aB005xu0plsz5Rnzo9dzIxZyYRPxn5GxXtIwnQ9wXM0v280vGcou2Yjt10XtVkMsE4ArEQAqT4AqDoApDMl1P0BAAAEQElEQVR42u1WiY6jOBCtxYQdQsIVwBzmMpjDgPn/v9ty0t3T3TudtDTSaKXNk5KyDSm/eq6qGOCJJ5544n8Bw/jyAfm+F2LbANbR+l029tvXLx7leR3B97awwMu6QYgqAvI5WBvqZkzg+D0+ydyXjLF6jNGpaROwbLAPAAc0UNV9onezH/uhS8bGcZh4GcJBB4FUkJrronHQ0RiB53wV+xtMEi5pNya+F9A+BgeCSghOIe2nSaRgQt0mTEwDj3F8n1DDq/Fl4loQSc7KOm1nVpZs5ieDpd1QVGUls7uSG4Y75TICh5xc1z053lSV05RlczoOw5jODMKxYRi3SJfkXnQEwqmYXAJe2/f9yJKpmEMrlJlMAdI5k17b1jOK1Agm7gVn4o7FdMaocsbymme8Rw9UNC04DvC6L3ghA01lZGMA5A4jb85laBGPj+OY11nbUxMyzrOzc7SLlmepTC9n0zm0lbjcU8mGruYt5onvXaaqTnlPMSbR1poRQ7dz3BRwfsgILCNe6Fz5AIGoeHpzFEot7Q+/QoHyPJMx/J2PhbhfKRaUM+UT7+c6l17eYg6doOkz2fdN2aBiHU9n3o9UJg9y0oRyqbTUDe7MuKDgWN4g8rLK6nakf/kTjlkhi0e5DQeI+SjEWAdg0LyI4UDgVAxirNIMZ+CyUYzo/6vAyA3X6MANw/O7ctKrYfA2dvTY/E4juXo44qvEssit1aExreuM6Kfml3E5vu9p3AgbhBj/YvyzkAj5On0uUi6I2bePN1LXvR3HfmF0HeD8SG5Tx3l54Ug+OopWKRCd9ybKq5rW68h4nZO3A/4Fo2hrr6OQYqchENPQAI8yRl0gBwjSnKLASVGmge7FtGBZCODjC+mHBH/nSG6Yy3STIUST2pQa8QeJVNvOznzDBcyuYFBq3TvsFArXG2x/Hxx1l+gSBRCvMgiXJQZ/2po4btXgevNaJllQ7CKJ2Dad872NojSDUtVRlKXvM0prpLEXBPK96/YMCFVcC9Op5LJ1OPKWWW/dbFGhmJbSaFTu/Vujdaqqqk6wytt1bZwzMEWN8xnSPYtVSdxjtEjedXxS9LKoReQ+JOsmReaB8SuNsETTdc2wU5QqsU8nm6ocHeE8wuRATHMCcT2tSng3y913afXTkal/sCwRoKNCL5Q71Y5O4C/SfzvxH+Gwxfr1cFov78pXh9ZdNEx3UJSqyYNqXVPfT9fFTxQD5wc0qot8/5IFEQ29QGxRRAMvGD45ipUWe1vDdkdqzd651So2KdVKge7YIE2Cp75Kuaog3Re5KGEXaDG087tywqZfVxosqhm2R581IVMJHQa8MhgX7G42pp2Pd4KhTSDIO2xKvhEWYtJiP7jooNjw4V5CPlnjk32Z2Te8luvt1JxrSzFuvQSILlBc0E1Ff8wX++C/WzOyf//uRyCIHkb/h2Ha/y0+TzzxxBN/HP8AE5lzqxH/g6sAAAAASUVORK5CYII=' },
  { ten: 'BE', api: 0, anh: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEgAAABICAMAAABiM0N1AAAAkFBMVEX/zQz/yhD/yRD/yA3/yAD4yBH/xw//xwb7xxP+xRj/xBn+xBv+xBr+xBn/xBj+xBj/xhX/xBf+xBf/xg3/xgz+xg39xB39xBv9xBr9xBj4xBj9wxn8wxr8wxn8wxj8whr7whrqvyHTti20qUJmh3QzdJsXa68XaK0SaLIRZ7MNZrYIY7oJYbMBYL8JUpwEQ40ERo27AAACN0lEQVR42u2XDW/bIBCGgXaquzSJ46Zd8ceKOSBgwP7//26H205rJ60hiSZV8imKuCh6DHf33hlyfSEjC2gBLaD/Crrf7x8e9ifY/XvQzeruRFvdvAettxXn1Tbf1n+Dnn4soK8M2qVS2J0N4mWv0fqSnwnqyn7w3smyOx9knDOXAQ3DJUGiE+INxnEtWn4SqLqllJWdSL8Jzii5YjvB80E96SXInl01vGloIQFA1mTTZoNAjeMYDhrY7paCdjHGQauaiTyQs9M0jeMhxKjqWgXvjDHWRy3Zcx7IzaBgjY1aTeMBIQkWP2bzKBDWd/DW+nEag9dKO29N1AXPPRr0ZQ0aSbjWULBS6ogkICIDZMMkyebnlvRIciM6dV2zb9obr4smAzQ/mG+5IBCtC+mUsw0OC+PPKH0eI1mkv3fVS8AwSLM55wbJ2nytNWV/GKxLaXszfyyI73o9WA9z6YlCBpdS+LojtEEeeTTeMhVNVCTpVBAVrPM6KQQ1Mn93G35cq50DbL1ihBGKxegcOuSaEIJiY4xtju3ZvKpTzqPGp+sRT4XRxvIGUFHXpWiPb/4tAz/gnlCnKNxpst7MTkS59BXPGEeCwoBFbMwhcQDM7MyqhQ/y/2SuCSo17sGHMGqgTKrk4AebSps3IAVjoJRWCgr6LEoqX5yaNbmTtm1YyhChDfafDh2anO8if2TzVrRNK167NC66387yNrKA/gF6ugRodbd+fFyff4W42KVmuUEuoAX0VUC/AHYG+ERa95YPAAAAAElFTkSuQmCC' },
  { ten: 'Lalamove', api: 0, anh: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEgAAABICAMAAABiM0N1AAAAkFBMVEX9rCHnmh7WjhzKhRv8cifKfBu4eRipcBb1bCXraCTeYyK9ZByibRaXZRTAVh63URyyTxylSRmKURSVQxeEOxVtRw9ePg14NRNbNA5qLxFKLQtYJw5QIw1IIgtDHgs2IwcvGwctFAceEAUXDAMWCgQQCQMIAwEEAgEDAgACAgADAQACAQECAQABAQABAAAAAADZNdywAAAB/0lEQVR42u2V2Y7jIBBF8b4o3u04eA8OsZMB6v//bspJpPT0rErnYR5AQsZIHOpWXYDAmxrRIA3SIA3SIA3SoH8FyfeAlPhCREKoB+W6ALBpVa+BthjkFRdv68+05uolkMK13WkbLcBpEZfLq9KUZHVRd0wBj227hOWWJYEhittI4ketl1uXqxIrCKzHqi5CiB+lSTi1tCzLvveDcL7L+pM4+ftkw0zbtg6CwM7gXAzblnXCoC0xdzDFFJjn8ZPnzTxynAZ2BxDRIXdc93hL8LP8qIrSvrQDewAWDJitIfBbSDPUKRM/gYYQtifGbLljTpi1k3tjNKqx4ffQnz4SuG9ap3ayITiaIK6zEmK6nKGNuxAq02pc02sIh7NxyF0wqyPJ8+Ye0EdDSozEt0MmgMb424dlkC3hEe0QF7F/inZbiyoTYCLT3mlMWRlV3qifQFfR2n42o6gs7NpjWLMinGzaTnXIOr+zKo80ZjWRarRcGA1jD545jvOjKE+QUiIOh83jUCZJ2mYcpmJI05gWLUDRRVPl8d0Ie8fJOcxe9A1y17UauHwCXaELT7DIX9VYqg+p/NuhFdekh+UxxKOHhw+7uDWcUkKiDy8SVilXCeqy4iQaUn4GCegLWN5wH6lzyaT8OghrfwT1phtSvumqVfo50iAN0iAN0iAN+m9B3wHXSpRqyofP9gAAAABJRU5ErkJggg==' }
];
function vdOpsGiao(ds) {
  return [{ value: '', label: 'Gỡ ra, trả về Chờ giao', icon: '↩️' }]
    .concat((ds || []).map(function (x) { return { value: x.user, label: x.ten, icon: '🛵' }; }))
    .concat(VD_APPS.map(function (a) {
      return { value: 'app:' + a.ten, label: a.ten + (a.api ? '' : ' (đặt tay trên app)'), img: vdLogoApp(a) };
    }));
}
async function vdGanNguoiGiao(name, o) {
  var ten = (o.value || '').indexOf('app:') === 0 ? o.value.slice(4) : '';
  if (ten) {
    await api('vagabond.van_don.gan_shipper', { name: name, kenh: ten });
    var a = vdApp(ten);
    return { app: ten, goiXe: !!(a && a.api) };
  }
  await api('vagabond.van_don.gan_shipper', { name: name, shipper: o.value || '' });
  return { app: '' };
}
function vdApp(ten) {
  for (var i = 0; i < VD_APPS.length; i++) { if (VD_APPS[i].ten === ten) return VD_APPS[i]; }
  return null;
}
function vdLogoApp(a) {
  // Logo that cua don vi van chuyen (anh Viet gui 03/08), nhung thang vao ma
  // duoi dang data URI cho khoi phu thuoc tep ngoai. GreenSM chua co logo nen
  // van dung khoi chu tam.
  if (a.anh) return a.anh;
  var co = a.nhan.length <= 2 ? 15 : (a.nhan.length <= 3 ? 13 : 11);
  var svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 40" width="64" height="40">' +
    '<rect x="0" y="0" width="64" height="40" rx="9" fill="' + a.nen + '"/>' +
    '<text x="32" y="20" fill="' + a.chu + '" font-family="Helvetica,Arial,sans-serif" font-size="' + co +
    '" font-weight="bold" text-anchor="middle" dominant-baseline="central">' + a.nhan + '</text></svg>';
  return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
}
async function vdChonShipper(name) {
  if (!vtShipper) { busy(true); try { vtShipper = await api('vagabond.van_don.ds_shipper'); } catch (e) { vtShipper = []; } busy(false); }
  var ops = vdOpsGiao(vtShipper);
  sheet('Phân công đơn này cho ai', ops, '', async function (o) {
    busy(true);
    try {
      var kq = await vdGanNguoiGiao(name, o);
      busy(false);
      if (kq.app) {
        if (kq.goiXe) { go(function () { scrVdGoiXe(name, kq.app); }); return; }
        toast('Đã ghi nhận đơn đi ' + kq.app);
      go(scrVanDon, true);
        return;
      }
      toast(o.value ? 'Đã phân công cho ' + o.label : 'Đã gỡ người giao khỏi đơn');
      go(scrVanDon, true);
    } catch (e) { busy(false); baoTin((e && e.message) || 'Phân công lỗi'); }
  });
}

async function vdInPhieu(names) {
  busy(true);
  var ds;
  try { ds = await api('vagabond.van_don.phieu_in', { names: JSON.stringify(names) }); }
  catch (e) { busy(false); baoTin((e && e.message) || 'Không lấy được dữ liệu để in'); return; }
  busy(false);
  if (!ds || !ds.length) { toast('Không có đơn nào để in.'); return; }
  var body = ds.map(vdPhieuHtml).join('');
  var doc = '<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8">'
    + '<title>Phiếu giao hàng - The Vagabond Pâtisserie</title>'
    + '<style>' + VD_CSS + '</style></head><body>' + body
    + '<script>window.onload=function(){setTimeout(function(){window.print();},600);};<\/script>'
    + '</body></html>';
  var w = window.open('', '_blank');
  if (!w) { baoTin('Trình duyệt chặn cửa sổ in. Anh chị cho phép mở cửa sổ mới rồi bấm In đơn lại giúp em.'); return; }
  w.document.open(); w.document.write(doc); w.document.close();
}

/* ---------- Van don: loc theo phuong / khung gio + xep tuyen (03/08/2026) ----------
   Sales truoc day loc tay tren Pancake roi in mot to A4 moi shipper. Khoi nay dua
   the khung gio + phuong ve app, va de xuat thu tu chay cho tung chuyen. ---------- */
var vdPhuong = null, vdTagGio = null, vdBuoi = null, vdBoLoc = null;
var vdKenh = null, vdGio = null;
var vtBuoiChon = null, vtSoTuyen = 2, vtDiemLay = 'Bếp', vtKq = null, vtShipper = null;

/* Truoc 13/08/2026 cac bo loc day het xuong may chu, nen man hinh chi nhan
   ve phan DA LOC - khong the dem duoc moi nhom con bao nhieu don de ghi len
   chip. Nay keo ca ngay ve mot lan (moi ngay toi da 500 don, khong nang) roi
   loc ngay tren may, chip nao cung mang dung con so cua no. */
function vdThamSo() {
  return { ngay: vdNgay };
}
function vdPhuongNgan(x) {
  var t = String(x || '').replace(/^(Phường|Xã|Thị trấn)\s+/i, '');
  return /^[0-9]+$/.test(t) ? 'P.' + t : t;
}
function vdThe(bg, txt) {
  return '<span style="display:inline-block;background:' + bg + ';color:#fff;border-radius:6px;padding:1px 6px;font-size:11px;line-height:16px">' + txt + '</span>';
}
/* Mau va icon cua tung trang thai van don, dung chung cho icon dau dong va
   chip mau. Loan Anh 08/08/2026: dau tick xanh nho o dau dong kho nhin, doi
   sang chip co chu. */
var VD_TT_ICON = { 'Chờ giao': '📦', 'Đang giao': '🛵', 'Đã giao': '✅', 'Không giao được': '⚠️', 'Huỷ': '⛔' };
var VD_TT_MAU = { 'Chờ giao': '#64748b', 'Đang giao': '#0369a1', 'Đã giao': '#12a150', 'Không giao được': '#b91c1c', 'Huỷ': '#7f1d1d' };
function vdHuyHieu(r) {
  var t = [];
  var tt = r.trang_thai || '';
  if (tt) t.push(vdThe(VD_TT_MAU[tt] || '#64748b', (VD_TT_ICON[tt] || '') + ' ' + h(tt)));
  /* Hai cho hay sot nhat: don chua ai nhan giao, va tien COD da thu ma chua
     doi soat. */
  if (tt === 'Chờ giao' && !r.shipper) t.push(vdThe('#c2410c', '🛵 Chưa phân công'));
  if (tt === 'Đã giao' && r.tien_thu_ho && !r.da_doi_soat) t.push(vdThe('#a16207', '💵 COD chưa đối soát'));
  if (r.thu_tu) t.push(vdThe('#0f766e', '#' + r.thu_tu + (r.gio_du_kien ? ' ~' + h(r.gio_du_kien) : '')));
  if (r.goi_truoc) t.push(vdThe('#b45309', '📞 Gọi trước'));
  if (r.chup_truoc) t.push(vdThe('#7c3aed', '📷 Gửi ảnh trước'));
  if (r.tre_khung_gio) t.push(vdThe('#b91c1c', '⚠️ Dễ trễ giờ'));
  if (r.ghi_chu_in) t.push(vdThe('#475569', '📝 ' + h(String(r.ghi_chu_in).replace(/[\r\n]+/g, ' ').slice(0, 38))));
  if (!t.length) return '';
  return '<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:5px">' + t.join('') + '</div>';
}
function vdChip(id, nhan, dang) {
  return '<button class="btn gh" id="' + id + '" style="flex:0 0 auto;width:auto;padding:6px 12px;font-size:13px' + (dang ? ';background:#0f766e;color:#fff;border-color:#0f766e' : '') + '">' + nhan + '</button>';
}
/* ---------- Chip loc man Van don (anh Viet 13/08/2026) ----------
   Truoc day man nay chi co mot nut "Tat ca ▾" mo bang chon trang thai, va
   ba nut khung gio / buoi / phuong khong mang con so nao. Nhin vao khong
   biet hom nay con bao nhieu don cho giao, bao nhieu don chua gan shipper.

   Nay ba hang chip dung chung khung voi man Doanh thu Sales: chip nao cung
   deo so don cua nhom do, chip nao khong co don thi tu an di. */
function vdNhomTrangThai() {
  return [
    { k: '', nhan: '📚 Tất cả', loc: function () { return true; } },
    { k: 'Chờ giao', nhan: '📦 Chờ giao', loc: function (r) { return r.trang_thai === 'Chờ giao'; } },
    { k: 'Đang giao', nhan: '🛵 Đang giao', loc: function (r) { return r.trang_thai === 'Đang giao'; } },
    { k: 'Đã giao', nhan: '✅ Đã giao', loc: function (r) { return r.trang_thai === 'Đã giao'; } },
    { k: 'Không giao được', nhan: '⚠️ Không giao được', loc: function (r) { return r.trang_thai === 'Không giao được'; } },
    { k: 'Huỷ', nhan: '🚫 Huỷ', loc: function (r) { return r.trang_thai === 'Huỷ'; } },
    { k: '@chua_gan', nhan: '🙋 Chưa gán shipper', loc: function (r) { return !r.shipper && r.trang_thai !== 'Huỷ'; } },
    { k: '@cod', nhan: '💵 Có COD', loc: function (r) { return Number(r.tien_thu_ho || 0) > 0; } },
    { k: '@chua_gio', nhan: '🕒 Thiếu thẻ giờ', loc: function (r) { return !(r.tag_gio || '').trim() && r.trang_thai === 'Chờ giao'; } }
  ];
}
function vdNhomKenh(ds) {
  var out = [{ k: '', nhan: 'Mọi kênh', loc: function () { return true; } }];
  var kenh = [], ship = [];
  ds.forEach(function (r) {
    var a = (r.kenh || '').trim();
    if (a && kenh.indexOf(a) < 0) kenh.push(a);
    var b = (r.shipper || '').trim();
    if (b && ship.indexOf(b) < 0) ship.push(b);
  });
  kenh.sort(function (a, b) { return a.localeCompare(b, 'vi'); });
  ship.sort(function (a, b) { return vdTen(a).localeCompare(vdTen(b), 'vi'); });
  kenh.forEach(function (a) {
    out.push({ k: 'kenh:' + a, nhan: h(a), loc: function (r) { return (r.kenh || '') === a; } });
  });
  ship.forEach(function (b) {
    out.push({ k: 'ship:' + b, nhan: '🛵 ' + h(vdTen(b)), loc: function (r) { return (r.shipper || '') === b; } });
  });
  return out;
}
function vdNhomGio(ds) {
  var out = [{ k: '', nhan: 'Cả ngày', loc: function () { return true; } }];
  var gio = [], phuong = [], chuyen = [];
  ds.forEach(function (r) {
    var a = (r.tag_gio || '').trim();
    if (a && gio.indexOf(a) < 0) gio.push(a);
    var b = (r.phuong || '').trim();
    if (b && phuong.indexOf(b) < 0) phuong.push(b);
    var c = (r.chuyen || '').trim();
    if (c && chuyen.indexOf(c) < 0) chuyen.push(c);
  });
  gio.sort(); phuong.sort(function (a, b) { return a.localeCompare(b, 'vi'); }); chuyen.sort();
  gio.forEach(function (a) {
    out.push({ k: 'gio:' + a, nhan: '🕒 ' + h(a), loc: function (r) { return (r.tag_gio || '') === a; } });
  });
  ['Sáng', 'Chiều', 'Tối'].forEach(function (b) {
    out.push({ k: 'buoi:' + b, nhan: '🌤️ ' + b, loc: function (r) { return (r.buoi || '') === b; } });
  });
  phuong.forEach(function (p) {
    out.push({ k: 'ph:' + p, nhan: '📍 ' + h(vdPhuongNgan(p)), loc: function (r) { return (r.phuong || '') === p; } });
  });
  chuyen.forEach(function (c) {
    out.push({ k: 'ch:' + c, nhan: '🧺 ' + h(c), loc: function (r) { return (r.chuyen || '') === c; } });
  });
  return out;
}
/* Tong theo bo loc: loc cai gi thi phai biet loc ra bao nhieu don, bao
   nhieu tien COD - khong thi phai cong tay tung dong tren man. */
function vdKhoiTong(ds, nhan) {
  var cod = 0, xong = 0, con = 0;
  ds.forEach(function (r) {
    cod += Number(r.tien_thu_ho || 0);
    if (r.trang_thai === 'Đã giao') xong++;
    else if (r.trang_thai !== 'Huỷ') con++;
  });
  return '<div class="card" style="padding:12px 14px;background:#f0fdfa;border:1.5px solid #99f6e4">' +
    '<div style="font-size:11.5px;color:#0f766e;font-weight:800;letter-spacing:.3px">TỔNG THEO BỘ LỌC' +
    (nhan ? ' · ' + h(nhan) : '') + '</div>' +
    '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:5px">' +
    '<span style="font-size:13.5px;color:#374151">' + ds.length + ' vận đơn</span>' +
    '<b style="font-size:19px;color:#0f766e">COD ' + money(cod) + ' đ</b></div>' +
    '<div style="display:flex;justify-content:space-between;font-size:12.5px;color:#6b7280;margin-top:3px">' +
    '<span>Đã giao ' + xong + ' · còn phải giao ' + con + '</span></div>' +
    '</div>';
}
function vdChipsHtml(ds) {
  var A = vdNhomTrangThai(), B = vdNhomKenh(ds), C = vdNhomGio(ds);
  if (!locTim(A, vdLoc || '') || locTim(A, vdLoc || '').k !== (vdLoc || '')) vdLoc = null;
  if (!locTim(B, vdKenh || '') || locTim(B, vdKenh || '').k !== (vdKenh || '')) vdKenh = null;
  if (!locTim(C, vdGio || '') || locTim(C, vdGio || '').k !== (vdGio || '')) vdGio = null;
  var fa = locTim(A, vdLoc || ''), fb = locTim(B, vdKenh || ''), fc = locTim(C, vdGio || '');
  var s = '<div class="card" style="padding:10px 12px;display:flex;flex-direction:column;gap:7px">' +
    locHang(A, vdLoc || '', 'data-vdla', ds) +
    locHang(B, vdKenh || '', 'data-vdlb', ds.filter(fa.loc)) +
    locHang(C, vdGio || '', 'data-vdlc', ds.filter(fa.loc)) + '</div>';
  if (vdBoLoc && vdBoLoc.so_thieu_the_gio) s += '<div class="sec" style="color:#b45309">⚠️ ' + vdBoLoc.so_thieu_the_gio + ' đơn chưa có thẻ khung giờ. Gắn thẻ bên Pancake rồi bấm Đồng bộ, đơn mới vào được tuyến.</div>';
  return s;
}
function vdLocRa(ds) {
  var fa = locTim(vdNhomTrangThai(), vdLoc || '');
  var fb = locTim(vdNhomKenh(ds), vdKenh || '');
  var fc = locTim(vdNhomGio(ds), vdGio || '');
  return ds.filter(function (r) { return fa.loc(r) && fb.loc(r) && fc.loc(r); });
}
function vdNhanLoc(ds) {
  var fa = locTim(vdNhomTrangThai(), vdLoc || '');
  var fb = locTim(vdNhomKenh(ds), vdKenh || '');
  var fc = locTim(vdNhomGio(ds), vdGio || '');
  return [vdLoc ? fa.nhan : '', vdKenh ? fb.nhan : '', vdGio ? fc.nhan : ''].filter(Boolean).join(' · ');
}
function vdGanChips() {
  var g = function (attr, dat) {
    Array.prototype.forEach.call(document.querySelectorAll('[' + attr + ']'), function (el) {
      el.onclick = function () { dat(el.getAttribute(attr)); go(scrVanDon, true); };
    });
  };
  g('data-vdla', function (v) { vdLoc = v || null; });
  g('data-vdlb', function (v) { vdKenh = v || null; });
  g('data-vdlc', function (v) { vdGio = v || null; });
}
async function vdChiDuongToi() {
  busy(true);
  try {
    var ds = await api('vagabond.van_don.chuyen_cua_toi', { ngay: vdNgay });
    busy(false);
    var co = (ds || []).filter(function (x) { return x.link_chi_duong; });
    if (!co.length) { toast('Chưa có đơn nào còn phải giao trong chuyến của mình.'); return; }
    if (co.length === 1) { window.open(co[0].link_chi_duong, '_blank'); return; }
    sheet('Mở chỉ đường chuyến nào?', co.map(function (x) { return { value: x.link_chi_duong, label: x.chuyen + ' · còn ' + x.con_lai + ' đơn', icon: '🗺️' }; }), '', function (o) { window.open(o.value, '_blank'); });
  } catch (e) { busy(false); baoTin((e && e.message) || 'Không tải được chuyến'); }
}

async function scrVdTuyen() {
  if (!vdNgay) vdNgay = today();
  var html = '<div class="card" style="padding:12px 14px">'
    + '<div class="sec" style="margin:0 0 8px;padding:0">Xếp tuyến ngày ' + h(vdNgay) + ' · chỉ lấy đơn nội bộ đang chờ giao, chưa gán ai</div>'
    + '<div style="display:flex;gap:8px;flex-wrap:wrap">'
    + '<button class="btn gh" id="vtB" style="flex:1;min-width:110px">🌤️ ' + h(vtBuoiChon || 'Cả ngày') + '</button>'
    + '<button class="btn gh" id="vtS" style="flex:1;min-width:110px">🛵 ' + vtSoTuyen + ' shipper</button>'
    + '<button class="btn gh" id="vtL" style="flex:1;min-width:110px">🏠 ' + h(vtDiemLay) + '</button>'
    + '</div>'
    + '<button class="btn" id="vtChay" style="margin-top:10px;width:100%">🧭 Đề xuất tuyến</button>'
    + '</div>';
  if (vtKq) {
    if (vtKq.thong_bao) html += '<div class="sec">' + h(vtKq.thong_bao) + '</div>';
    (vtKq.bo_qua || []).length && (html += '<div class="sec" style="color:#b45309">⚠️ ' + vtKq.bo_qua.length + ' đơn không xếp được vì chưa ra toạ độ: ' + h(vtKq.bo_qua.map(function (x) { return x.ma_don; }).join(', ')) + '</div>');
    (vtKq.tuyen || []).forEach(function (t, ix) {
      html += '<div class="sec">Tuyến ' + t.tuyen + ' · ' + t.so_don + ' đơn · ' + t.tong_km + ' km · ' + h(t.bat_dau) + ' đến ' + h(t.ket_thuc) + (t.tong_cod ? ' · COD ' + money(t.tong_cod) : '') + (t.phut_tre ? ' · ⚠️ trễ ' + t.phut_tre + ' phút' : '') + '</div>';
      html += '<div class="card">';
      t.diem.forEach(function (d) {
        html += '<div style="display:flex;gap:10px;padding:10px 14px;border-bottom:1px solid #f0f0f0">'
          + '<div style="flex:1;min-width:0">'
          + '<div class="h1">#' + d.thu_tu + ' · ' + h(d.ma_don || '') + ' · ' + h(d.khach || '') + '</div>'
          + '<div class="h2">' + (d.gio_du_kien ? 'đến ~' + h(d.gio_du_kien) + ' · ' : '') + (d.tag_gio ? h(d.tag_gio) + ' · ' : '') + h(vdPhuongNgan(d.phuong || '')) + ' · ' + d.km_chang + ' km</div>'
          + '<div class="h2">' + h((d.dia_chi || '').slice(0, 70)) + '</div>'
          + vdHuyHieu({ goi_truoc: d.goi_truoc, chup_truoc: d.chup_truoc, tre_khung_gio: d.tre, ghi_chu_in: d.ghi_chu_in })
          + '</div>'
          + (d.tien_thu_ho ? '<b style="white-space:nowrap;font-size:13px">' + money(d.tien_thu_ho) + '</b>' : '')
          + '</div>';
      });
      html += '</div>';
      html += '<div style="display:flex;gap:8px;padding:0 14px 16px">'
        + '<button class="btn" data-chot="' + ix + '" style="flex:2">✅ Giao tuyến này</button>'
        + '<button class="btn gh" data-map="' + ix + '" style="flex:1">🗺️ Chỉ đường</button>'
        + '</div>';
    });
  }
  frame('Xếp tuyến', html);
  var g = function (id, fn) { var b = document.getElementById(id); if (b) b.onclick = fn; };
  g('vtB', function () {
    sheet('Xếp cho buổi nào', [
      { value: '', label: 'Cả ngày', icon: '🗓️' },
      { value: 'Sáng', label: 'Sáng (7h - 12h)', icon: '🌅' },
      { value: 'Chiều', label: 'Chiều (12h - 17h)', icon: '☀️' },
      { value: 'Tối', label: 'Tối (17h - 22h)', icon: '🌙' }
    ], vtBuoiChon || '', function (o) { vtBuoiChon = o.value || null; vtKq = null; go(scrVdTuyen, true); });
  });
  g('vtS', function () {
    var ops = []; for (var i = 1; i <= 6; i++) ops.push({ value: String(i), label: i + ' shipper', icon: '🛵' });
    sheet('Chia cho mấy shipper', ops, String(vtSoTuyen), function (o) { vtSoTuyen = parseInt(o.value, 10) || 2; vtKq = null; go(scrVdTuyen, true); });
  });
  g('vtL', function () {
    sheet('Lấy bánh ở đâu', [{ value: 'Bếp', label: 'Bếp Nguyễn Văn Trỗi', icon: '🍳' }, { value: 'Tiệm', label: 'Tiệm Trần Cao Vân', icon: '🏬' }], vtDiemLay, function (o) { vtDiemLay = o.value; vtKq = null; go(scrVdTuyen, true); });
  });
  g('vtChay', async function () {
    busy(true);
    try {
      vtKq = await api('vagabond.xep_tuyen.de_xuat_tuyen', { ngay: vdNgay, buoi: vtBuoiChon || '', so_tuyen: vtSoTuyen, diem_lay: vtDiemLay });
      busy(false); go(scrVdTuyen, true);
    } catch (e) { busy(false); baoTin((e && e.message) || 'Không xếp được tuyến'); }
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-map]'), function (b) {
    b.onclick = function () { var t = vtKq.tuyen[parseInt(b.getAttribute('data-map'), 10)]; if (t && t.link_chi_duong) window.open(t.link_chi_duong, '_blank'); };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-chot]'), function (b) {
    b.onclick = async function () {
      var t = vtKq.tuyen[parseInt(b.getAttribute('data-chot'), 10)];
      if (!t) return;
      if (!vtShipper) { busy(true); try { vtShipper = await api('vagabond.van_don.ds_shipper'); } catch (e) { vtShipper = []; } busy(false); }
      sheet('Giao tuyến ' + t.tuyen + ' (' + t.so_don + ' đơn) cho ai', (vtShipper || []).map(function (x) { return { value: x.user, label: x.ten, icon: '🛵' }; }), '', async function (o) {
        busy(true);
        try {
          await api('vagabond.xep_tuyen.chot_tuyen', { tuyen: JSON.stringify([{ tuyen: t.tuyen, shipper: o.value, diem: t.diem.map(function (d) { return { name: d.name, thu_tu: d.thu_tu, gio_du_kien: d.gio_du_kien, km_chang: d.km_chang, tre: d.tre }; }) }]) });
          busy(false); toast('Đã giao tuyến ' + t.tuyen + ' cho ' + o.label);
          vtKq.tuyen.splice(parseInt(b.getAttribute('data-chot'), 10), 1);
          go(scrVdTuyen, true);
        } catch (e) { busy(false); baoTin((e && e.message) || 'Chốt tuyến lỗi'); }
      });
    };
  });
}

// Trang chu cua site gio la app nhan vien (de app.thevagabondpatisserie.com
// mo ra la vao thang app). Rieng ten mien dat banh cua khach thi day ve /banh.
(function () {
  try {
    if ((location.hostname || '').indexOf('order') === 0 && location.pathname === '/') {
      location.replace('/banh');
    }
  } catch (eo) {}
})();

// Quet ma QR tren phieu in: /bep?vd=VD-2026-xxxxx mo thang van don do.
// Phai cho app boot xong (dang nhap + dung man chinh) roi moi nhay, nen doi
// theo nhip thay vi hen gio cung - 1,5 giay la chua kip.
(function () {
  var vdQR = null;
  try { vdQR = new URLSearchParams(location.search).get('vd'); } catch (e0) { return; }
  if (!vdQR) return;
  var n = 0;
  var hen = setInterval(function () {
    n++;
    if (n > 40) { clearInterval(hen); return; }
    try {
      if (S && S.stack && S.stack.length === 1 && root && (root.innerHTML || '').length > 400) {
        clearInterval(hen);
        history.replaceState({ vgbD: 0 }, '', location.pathname);
        go(function () { scrVdView(vdQR); });
      }
    } catch (e1) {}
  }, 400);
})();


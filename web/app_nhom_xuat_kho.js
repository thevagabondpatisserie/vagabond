/* ---------- 5b. Nhom nghiep vu: o lon o trang chu, bam vao moi hien o nho ----------

Anh Viet dat ngay 03/08/2026: nghiep vu nhieu qua roi, trang chu cuon dai
khong nhin het. Gom thanh 8 o lon kieu iPOS, bam o lon moi ra danh sach o nho.

Cach lam co y: KHONG dung lai phan dem so cua scrHome. scrHome van dung so
lieu va van dung ham card() cu de dung tung dong; xong roi vgbGomNhom() moi
doc lai cac dong da dung duoc, xep vao nhom rong. Them nghiep vu moi chi can
them key vao VGB_NHOM, khong phai sua cho nao khac.
*/
var VGB_NHOM = [
  { k: 'DH', ten: 'Đặt hàng', icon: '🛒', keys: ['Purchase', 'Transfer', 'RND', 'PAY'] },
  { k: 'SX', ten: 'Sản xuất', icon: '🧑‍🍳', keys: ['Manufacture', 'KIT', 'MFG', 'BTPO'] },
  { k: 'NK', ten: 'Nhập kho', icon: '📥', keys: ['RCV'] },
  { k: 'XK', ten: 'Xuất kho', icon: '📤', keys: ['XKH', 'XKD'] },
  { k: 'KK', ten: 'Kiểm kê', icon: '🧮', keys: ['KK', 'STOCK'] },
  { k: 'BH', ten: 'Bán hàng', icon: '🎂', keys: ['KBD', 'DS', 'HDG'] },
  { k: 'GH', ten: 'Giao hàng', icon: '🚚', keys: ['VD'] },
  { k: 'KHAC', ten: 'Khác', icon: '⚙️', keys: ['ACC'] }
];

var VGB_HUB = {};

function vgbCss() {
  if (document.getElementById('vgbHubCss')) return;
  var st = document.createElement('style');
  st.id = 'vgbHubCss';
  st.textContent =
    '.gwrap{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:12px}' +
    '.gt{position:relative;background:#fff;border-radius:16px;padding:16px 14px 14px;' +
    'box-shadow:0 1px 3px rgba(16,24,40,.08);min-height:104px;display:flex;' +
    'flex-direction:column;justify-content:space-between;cursor:pointer;' +
    '-webkit-tap-highlight-color:transparent}' +
    '.gt:active{transform:scale(.98)}' +
    '.gt .gi{font-size:30px;line-height:1}' +
    '.gt .gn{font-size:17px;font-weight:700;color:#101828}' +
    '.gt .gs{font-size:12px;color:#98a2b3;margin-top:2px}' +
    '.gt .gb{position:absolute;top:12px;right:12px;background:#fee4e2;color:#d92d20;' +
    'font-size:13px;font-weight:700;border-radius:999px;padding:2px 9px}' +
    '.vxf{padding:12px}' +
    '.vxl{font-size:13px;color:#667085;margin:14px 2px 6px;font-weight:600}' +
    '.vxi,.vxs{width:100%;box-sizing:border-box;border:1px solid #d0d5dd;border-radius:10px;' +
    'padding:11px 12px;font-size:16px;background:#fff;color:#101828}' +
    '.vxb{width:100%;box-sizing:border-box;border:0;border-radius:12px;padding:14px;' +
    'font-size:16px;font-weight:700;background:#101828;color:#fff;margin-top:16px}' +
    '.vxb.o{background:#fff;color:#101828;border:1px solid #d0d5dd;margin-top:8px}' +
    '.vxb.r{background:#d92d20;color:#fff}' +
    '.vxb[disabled]{opacity:.45}' +
    '.vxr{display:flex;align-items:center;gap:10px;background:#fff;border-radius:12px;' +
    'padding:10px 12px;margin-bottom:8px;box-shadow:0 1px 2px rgba(16,24,40,.06)}' +
    '.vxr .t{flex:1;min-width:0}' +
    '.vxr .t b{display:block;font-size:15px;color:#101828;font-weight:600;' +
    'white-space:nowrap;overflow:hidden;text-overflow:ellipsis}' +
    '.vxr .t i{font-style:normal;font-size:12px;color:#98a2b3}' +
    '.vxq{width:78px;text-align:right;border:1px solid #d0d5dd;border-radius:8px;' +
    'padding:8px;font-size:15px}' +
    '.vxx{border:0;background:transparent;color:#d92d20;font-size:20px;padding:0 4px}' +
    '.vxtag{display:inline-block;font-size:12px;font-weight:600;border-radius:999px;' +
    'padding:2px 9px}' +
    '.vxtag.c{background:#fef0c7;color:#b54708}' +
    '.vxtag.d{background:#d1fadf;color:#027a48}';
  document.head.appendChild(st);
}

function vgbSoNhom(nh) {
  var t = 0;
  for (var i = 0; i < nh.keys.length; i++) {
    var o = VGB_HUB[nh.keys[i]];
    if (o && o.cnt) t += o.cnt;
  }
  return t;
}

function vgbGomNhom() {
  vgbCss();
  VGB_HUB = {};
  var body = document.getElementById('vgbBody');
  if (!body) return;
  var rows = body.querySelectorAll('[data-go]');
  for (var i = 0; i < rows.length; i++) {
    var el = rows[i];
    var b = el.querySelector('.bdg');
    var n = b ? parseInt((b.textContent || '').replace(/\D/g, ''), 10) : 0;
    VGB_HUB[el.dataset.go] = { html: el.outerHTML, cnt: n || 0 };
  }

  /* Hai o nho cua Xuat kho - dung o day de khong phai dong vao scrHome. */
  VGB_HUB.XKH = {
    cnt: 0,
    html: vgbODong('XKH', '🗑️', 'Xuất huỷ', 'Hàng hỏng, hết hạn, không đạt')
  };
  VGB_HUB.XKD = {
    cnt: 0,
    html: vgbODong('XKD', '🔁', 'Xuất điều chuyển nội bộ', 'Chuyển hàng sang kho khác')
  };

  var daXep = {};
  for (var a = 0; a < VGB_NHOM.length; a++) {
    for (var c = 0; c < VGB_NHOM[a].keys.length; c++) daXep[VGB_NHOM[a].keys[c]] = 1;
  }
  var khac = VGB_NHOM[VGB_NHOM.length - 1];
  for (var kk in VGB_HUB) {
    if (!daXep[kk] && khac.keys.indexOf(kk) < 0) khac.keys.push(kk);
  }

  var g = '<div class="gwrap">';
  for (var j = 0; j < VGB_NHOM.length; j++) {
    var nh = VGB_NHOM[j];
    var co = 0;
    for (var m = 0; m < nh.keys.length; m++) if (VGB_HUB[nh.keys[m]]) co++;
    if (!co) continue;
    var so = vgbSoNhom(nh);
    g +=
      '<div class="gt" data-nhom="' + nh.k + '">' +
      (so ? '<span class="gb">' + so + '</span>' : '') +
      '<div class="gi">' + nh.icon + '</div>' +
      '<div><div class="gn">' + h(nh.ten) + '</div>' +
      '<div class="gs">' + co + ' nghiệp vụ</div></div></div>';
  }
  g += '</div>';
  body.innerHTML = g;
  body.onclick = function (e) {
    var t = e.target.closest('[data-nhom]');
    if (!t) return;
    var nh = null;
    for (var i = 0; i < VGB_NHOM.length; i++) if (VGB_NHOM[i].k === t.dataset.nhom) nh = VGB_NHOM[i];
    if (nh) go(function () { scrNhom(nh); });
  };
}

function vgbODong(k, icon, t1, t2) {
  return '<div class="hub" data-go="' + k + '"><div class="hi">' + icon + '</div>' +
    '<div class="ht"><div class="h1">' + h(t1) + '</div><div class="h2">' + h(t2) + '</div></div>' +
    '<span class="fc" style="color:#c3c8d4;font-size:22px">&#8250;</span></div>';
}

function scrNhom(nh) {
  vgbCss();
  var rows = '';
  for (var i = 0; i < nh.keys.length; i++) {
    var o = VGB_HUB[nh.keys[i]];
    if (o) rows += o.html;
  }
  var body = frame(nh.ten, '<div class="card">' + rows + '</div>');
  root.onclick = null;
  body.onclick = function (e) {
    var r = e.target.closest('[data-go]');
    if (r) vgbGo(r.dataset.go);
  };
}

/* Mot cho duy nhat dinh tuyen tu o nho sang man hinh. */
function vgbGo(k) {
  if (k === 'KBD') { location.href = '/kiem-banh'; return; }
  if (k === 'BTPO') { location.href = '/btp'; return; }
  if (k === 'PAY') return go(scrPayList);
  if (k === 'STOCK') return go(scrStock);
  if (k === 'KIT') return go(scrKitchen);
  if (k === 'MFG') return go(scrMfgList);
  if (k === 'RCV') return go(scrRecvList);
  if (k === 'KK') return go(scrKkList);
  if (k === 'DS') return go(scrDoanhSo);
  if (k === 'HDG') return go(scrHopDong);
  if (k === 'VD') return go(scrVanDon);
  if (k === 'RND') return go(scrRndList);
  if (k === 'ACC') return go(scrAccount);
  if (k === 'XKH') return go(scrXkHuyList);
  if (k === 'XKD') return go(scrXkCkList);
  go(function () { scrMRList(TYPES[k]); });
}

/* ---------- 5c. Xuat kho: xuat huy va xuat dieu chuyen noi bo ----------

Hai luat khac nhau, co y:
- Xuat huy: nhan vien luu ban nhap, quan ly kho bam Ghi so thi ton moi tru.
- Dieu chuyen: ghi so ngay, vi hang chi doi kho chu khong mat di.
*/
var XK = { boot: null, gio: [], kho: '', khoNhan: '', lyDo: '', ghiChu: '', anh: '', yc: '' };

async function xkBoot() {
  if (!XK.boot) XK.boot = await api('vagabond.xuat_kho.khoi_dong');
  return XK.boot;
}

function vxSo(n) {
  n = Number(n || 0);
  var s = (Math.round(n * 1000) / 1000).toString();
  var p = s.split('.');
  p[0] = p[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return p.join(',');
}

function vxKhoOpt(ds, chon) {
  var s = '<option value="">-- chọn kho --</option>';
  for (var i = 0; i < ds.length; i++) {
    s += '<option value="' + h(ds[i].name) + '"' + (ds[i].name === chon ? ' selected' : '') + '>' +
      h(ds[i].warehouse_name || ds[i].name) + '</option>';
  }
  return s;
}

function vxDongHtml() {
  if (!XK.gio.length) {
    return '<div style="text-align:center;color:#98a2b3;padding:22px 0;font-size:14px">' +
      'Chưa có món nào. Bấm <b>Thêm hàng</b> ở dưới.</div>';
  }
  var s = '';
  for (var i = 0; i < XK.gio.length; i++) {
    var d = XK.gio[i];
    s += '<div class="vxr"><div class="t"><b>' + h(d.ten || d.ma) + '</b>' +
      '<i>' + h(d.ma) + ' · tồn ' + vxSo(d.ton) + ' ' + h(d.dvt || '') + '</i></div>' +
      '<input class="vxq" type="number" inputmode="decimal" min="0" step="any" ' +
      'value="' + d.sl + '" data-sl="' + i + '">' +
      '<button class="vxx" data-bo="' + i + '">&times;</button></div>';
  }
  return s;
}

function vxNoiDong(body) {
  var o = body.querySelector('#vxDong');
  if (o) o.innerHTML = vxDongHtml();
  vxNoiSuKien(body);
}

function vxNoiSuKien(body) {
  var qs = body.querySelectorAll('[data-sl]');
  for (var i = 0; i < qs.length; i++) {
    qs[i].onchange = function () {
      XK.gio[+this.dataset.sl].sl = Number(this.value || 0);
    };
  }
  var bs = body.querySelectorAll('[data-bo]');
  for (var j = 0; j < bs.length; j++) {
    bs[j].onclick = function () {
      XK.gio.splice(+this.dataset.bo, 1);
      vxNoiDong(body);
    };
  }
}

/* Man chon hang: chi liet ke ma CON TON trong kho da chon. */
function scrXkChonHang(kho, quayVe) {
  vgbCss();
  var body = frame('Thêm hàng', '<div class="vxf">' +
    '<input class="vxi" id="vxQ" placeholder="Gõ tên hoặc mã hàng rồi Enter">' +
    '<div id="vxKq" style="margin-top:12px"></div></div>');
  var q = body.querySelector('#vxQ');
  var kq = body.querySelector('#vxKq');

  async function tim() {
    kq.innerHTML = '<div style="text-align:center;color:#98a2b3;padding:18px">Đang tìm...</div>';
    var ds = await api('vagabond.xuat_kho.tim_hang', { kho: kho, tu_khoa: q.value || '' });
    if (!ds || !ds.length) {
      kq.innerHTML = '<div style="text-align:center;color:#98a2b3;padding:18px;font-size:14px">' +
        'Kho này không còn tồn mã nào khớp.</div>';
      return;
    }
    var s = '';
    for (var i = 0; i < ds.length; i++) {
      s += '<div class="vxr" data-th="' + i + '"><div class="t"><b>' + h(ds[i].ten || ds[i].ma) +
        '</b><i>' + h(ds[i].ma) + ' · tồn ' + vxSo(ds[i].ton) + ' ' + h(ds[i].dvt || '') +
        '</i></div><span style="color:#0b7c93;font-weight:700;font-size:22px">+</span></div>';
    }
    kq.innerHTML = s;
    var rs = kq.querySelectorAll('[data-th]');
    for (var j = 0; j < rs.length; j++) {
      rs[j].onclick = function () {
        var d = ds[+this.dataset.th];
        for (var m = 0; m < XK.gio.length; m++) {
          if (XK.gio[m].ma === d.ma) { toast('Món này đã có trong phiếu.'); return; }
        }
        XK.gio.push({ ma: d.ma, ten: d.ten, dvt: d.dvt, ton: d.ton, sl: 1 });
        toast('Đã thêm ' + (d.ten || d.ma));
        back();
      };
    }
  }

  q.onkeydown = function (e) { if (e.key === 'Enter') tim(); };
  tim();
}

/* ----- Xuat huy ----- */
async function scrXkHuyList() {
  vgbCss();
  frame('Xuất huỷ', '<div class="emp"><div class="e1">⏳</div></div>');
  var b = await xkBoot();
  var ds = await api('vagabond.xuat_kho.ds_phieu', { loai: 'huy', gioi_han: 40 });
  var s = '';
  if (!ds || !ds.length) {
    s = '<div style="text-align:center;color:#98a2b3;padding:40px 20px;font-size:14px">' +
      'Chưa có phiếu xuất huỷ nào.<br>Bấm nút + để lập phiếu.</div>';
  } else {
    for (var i = 0; i < ds.length; i++) {
      var d = ds[i];
      s += '<div class="vxr" data-xem="' + h(d.name) + '"><div class="t">' +
        '<b>' + h(d.name) + ' · ' + h(d.from_warehouse || '') + '</b>' +
        '<i>' + h(d.posting_date) + ' · ' + d.so_dong + ' món · ' + h(d.nguoi_tao) + '</i></div>' +
        '<span class="vxtag ' + (d.docstatus === 0 ? 'c' : 'd') + '">' + h(d.trang_thai) + '</span></div>';
    }
  }
  var body = frame('Xuất huỷ', '<div class="vxf">' + s + '</div>', {
    fab: 1,
    onFab: function () { XK.gio = []; XK.lyDo = ''; XK.ghiChu = ''; XK.anh = ''; go(scrXkHuyNew); }
  });
  var rs = body.querySelectorAll('[data-xem]');
  for (var j = 0; j < rs.length; j++) {
    rs[j].onclick = function () {
      var n = this.dataset.xem;
      go(function () { scrXkView(n); });
    };
  }
}

async function scrXkHuyNew() {
  vgbCss();
  frame('Lập phiếu xuất huỷ', '<div class="emp"><div class="e1">⏳</div></div>');
  var b = await xkBoot();
  var ly = '<option value="">-- chọn lý do --</option>';
  for (var i = 0; i < b.ly_do.length; i++) {
    ly += '<option value="' + h(b.ly_do[i]) + '"' + (b.ly_do[i] === XK.lyDo ? ' selected' : '') +
      '>' + h(b.ly_do[i]) + '</option>';
  }
  var body = frame('Lập phiếu xuất huỷ',
    '<div class="vxf">' +
    '<div class="vxl">Kho xuất</div><select class="vxs" id="vxKho">' + vxKhoOpt(b.kho, XK.kho) + '</select>' +
    '<div class="vxl">Lý do huỷ</div><select class="vxs" id="vxLy">' + ly + '</select>' +
    '<div class="vxl">Ảnh chứng minh (không bắt buộc)</div>' +
    '<input class="vxi" type="file" accept="image/*" id="vxAnh">' +
    '<div id="vxAnhOk" style="font-size:13px;color:#027a48;margin-top:6px"></div>' +
    '<div class="vxl">Danh sách hàng huỷ</div><div id="vxDong">' + vxDongHtml() + '</div>' +
    '<button class="vxb o" id="vxThem">+ Thêm hàng</button>' +
    '<div class="vxl">Ghi chú</div>' +
    '<input class="vxi" id="vxGc" placeholder="Ví dụ: bánh trưng bày hết ngày 03/08" value="' + h(XK.ghiChu) + '">' +
    '<button class="vxb" id="vxLuu">Lưu phiếu, chờ quản lý ghi sổ</button>' +
    '<div style="font-size:12px;color:#98a2b3;text-align:center;margin-top:10px">' +
    'Tồn kho chỉ trừ sau khi quản lý kho bấm Ghi sổ.</div></div>');

  var eKho = body.querySelector('#vxKho');
  var eLy = body.querySelector('#vxLy');
  var eGc = body.querySelector('#vxGc');

  eKho.onchange = function () {
    if (XK.kho && this.value !== XK.kho && XK.gio.length) {
      XK.gio = [];
      toast('Đổi kho nên phải chọn lại hàng.');
    }
    XK.kho = this.value;
    vxNoiDong(body);
  };
  eLy.onchange = function () { XK.lyDo = this.value; };
  eGc.onchange = function () { XK.ghiChu = this.value; };
  vxNoiSuKien(body);

  body.querySelector('#vxThem').onclick = function () {
    XK.kho = eKho.value;
    XK.ghiChu = eGc.value;
    XK.lyDo = eLy.value;
    if (!XK.kho) { toast('Chọn kho xuất trước đã.'); return; }
    var kho = XK.kho;
    go(function () { scrXkChonHang(kho, scrXkHuyNew); });
  };

  body.querySelector('#vxAnh').onchange = async function () {
    var f = this.files && this.files[0];
    if (!f) return;
    var ok = body.querySelector('#vxAnhOk');
    ok.textContent = 'Đang tải ảnh lên...';
    try {
      XK.anh = await vxUpAnh(f);
      ok.textContent = 'Đã tải ảnh lên.';
    } catch (e) {
      ok.style.color = '#d92d20';
      ok.textContent = 'Không tải được ảnh: ' + (e.message || e);
    }
  };

  body.querySelector('#vxLuu').onclick = async function () {
    XK.kho = eKho.value; XK.lyDo = eLy.value; XK.ghiChu = eGc.value;
    if (!XK.kho) { toast('Chưa chọn kho xuất.'); return; }
    if (!XK.lyDo) { toast('Chưa chọn lý do huỷ.'); return; }
    if (!XK.gio.length) { toast('Chưa có món nào.'); return; }
    this.disabled = true;
    try {
      var r = await api('vagabond.xuat_kho.luu_xuat_huy', {
        kho: XK.kho, ly_do: XK.lyDo, ghi_chu: XK.ghiChu, anh: XK.anh,
        dong: JSON.stringify(XK.gio.map(function (d) { return { ma: d.ma, sl: d.sl }; }))
      });
      XK.gio = []; XK.anh = ''; XK.ghiChu = '';
      toast('Đã lưu ' + r.name);
      go(function () { scrXkView(r.name); }, true);
    } catch (e) {
      this.disabled = false;
      toast(e.message || 'Không lưu được phiếu.');
    }
  };
}

/* ----- Xuat dieu chuyen noi bo ----- */
async function scrXkCkList() {
  vgbCss();
  frame('Xuất điều chuyển', '<div class="emp"><div class="e1">⏳</div></div>');
  await xkBoot();
  var ds = await api('vagabond.xuat_kho.ds_phieu', { loai: 'chuyen', gioi_han: 40 });
  var s = '';
  if (!ds || !ds.length) {
    s = '<div style="text-align:center;color:#98a2b3;padding:40px 20px;font-size:14px">' +
      'Chưa có phiếu điều chuyển nào.<br>Bấm nút + để lập phiếu.</div>';
  } else {
    for (var i = 0; i < ds.length; i++) {
      var d = ds[i];
      s += '<div class="vxr" data-xem="' + h(d.name) + '"><div class="t">' +
        '<b>' + h(d.from_warehouse || '') + ' → ' + h(d.to_warehouse || '') + '</b>' +
        '<i>' + h(d.name) + ' · ' + h(d.posting_date) + ' · ' + d.so_dong + ' món</i></div>' +
        '<span class="vxtag d">' + h(d.trang_thai) + '</span></div>';
    }
  }
  var body = frame('Xuất điều chuyển', '<div class="vxf">' + s + '</div>', {
    fab: 1,
    onFab: function () { XK.gio = []; XK.khoNhan = ''; XK.ghiChu = ''; XK.yc = ''; go(scrXkCkNew); }
  });
  var rs = body.querySelectorAll('[data-xem]');
  for (var j = 0; j < rs.length; j++) {
    rs[j].onclick = function () {
      var n = this.dataset.xem;
      go(function () { scrXkView(n); });
    };
  }
}

async function scrXkCkNew() {
  vgbCss();
  frame('Lập phiếu điều chuyển', '<div class="emp"><div class="e1">⏳</div></div>');
  var b = await xkBoot();
  var yc = await api('vagabond.xuat_kho.yeu_cau_cho_chuyen', { kho_xuat: XK.kho || '' });
  var ycOpt = '<option value="">-- không theo phiếu nào --</option>';
  for (var i = 0; i < (yc || []).length; i++) {
    ycOpt += '<option value="' + h(yc[i].name) + '"' + (yc[i].name === XK.yc ? ' selected' : '') +
      '>' + h(yc[i].name) + ' → ' + h(yc[i].set_warehouse || '') + '</option>';
  }
  var body = frame('Lập phiếu điều chuyển',
    '<div class="vxf">' +
    '<div class="vxl">Theo phiếu đặt hàng nội bộ</div>' +
    '<select class="vxs" id="vxYc">' + ycOpt + '</select>' +
    '<div class="vxl">Kho xuất</div><select class="vxs" id="vxKho">' + vxKhoOpt(b.kho, XK.kho) + '</select>' +
    '<div class="vxl">Kho nhận</div><select class="vxs" id="vxKhoN">' + vxKhoOpt(b.kho, XK.khoNhan) + '</select>' +
    '<div class="vxl">Danh sách hàng chuyển</div><div id="vxDong">' + vxDongHtml() + '</div>' +
    '<button class="vxb o" id="vxThem">+ Thêm hàng</button>' +
    '<div class="vxl">Ghi chú</div>' +
    '<input class="vxi" id="vxGc" placeholder="Ví dụ: chuyển bánh cho cửa hàng Trần Cao Vân" value="' + h(XK.ghiChu) + '">' +
    '<button class="vxb" id="vxLuu">Ghi sổ phiếu chuyển</button>' +
    '<div style="font-size:12px;color:#98a2b3;text-align:center;margin-top:10px">' +
    'Ghi sổ xong hàng đã nằm ở kho nhận. Kho nhận vẫn phải đếm lại khi nhận.</div></div>');

  var eKho = body.querySelector('#vxKho');
  var eKhoN = body.querySelector('#vxKhoN');
  var eGc = body.querySelector('#vxGc');
  var eYc = body.querySelector('#vxYc');

  eKho.onchange = function () {
    if (XK.kho && this.value !== XK.kho && XK.gio.length) {
      XK.gio = [];
      toast('Đổi kho nên phải chọn lại hàng.');
    }
    XK.kho = this.value;
    vxNoiDong(body);
  };
  eKhoN.onchange = function () { XK.khoNhan = this.value; };
  eGc.onchange = function () { XK.ghiChu = this.value; };
  vxNoiSuKien(body);

  eYc.onchange = async function () {
    XK.yc = this.value;
    if (!XK.yc) return;
    var ct = await api('vagabond.xuat_kho.dong_cua_yeu_cau', { name: XK.yc });
    XK.gio = (ct.dong || []).map(function (d) {
      return { ma: d.ma, ten: d.ten, dvt: d.dvt, ton: d.sl, sl: d.sl };
    });
    if (ct.kho_xuat) { XK.kho = ct.kho_xuat; eKho.value = ct.kho_xuat; }
    if (ct.kho_nhan) { XK.khoNhan = ct.kho_nhan; eKhoN.value = ct.kho_nhan; }
    vxNoiDong(body);
    toast('Đã điền ' + XK.gio.length + ' món theo phiếu.');
  };

  body.querySelector('#vxThem').onclick = function () {
    XK.kho = eKho.value; XK.khoNhan = eKhoN.value; XK.ghiChu = eGc.value;
    if (!XK.kho) { toast('Chọn kho xuất trước đã.'); return; }
    var kho = XK.kho;
    go(function () { scrXkChonHang(kho, scrXkCkNew); });
  };

  body.querySelector('#vxLuu').onclick = async function () {
    XK.kho = eKho.value; XK.khoNhan = eKhoN.value; XK.ghiChu = eGc.value;
    if (!XK.kho || !XK.khoNhan) { toast('Phải chọn cả kho xuất và kho nhận.'); return; }
    if (XK.kho === XK.khoNhan) { toast('Kho xuất và kho nhận trùng nhau.'); return; }
    if (!XK.gio.length) { toast('Chưa có món nào.'); return; }
    this.disabled = true;
    try {
      var r = await api('vagabond.xuat_kho.luu_dieu_chuyen', {
        kho_xuat: XK.kho, kho_nhan: XK.khoNhan, ghi_chu: XK.ghiChu, yeu_cau: XK.yc,
        dong: JSON.stringify(XK.gio.map(function (d) { return { ma: d.ma, sl: d.sl }; }))
      });
      XK.gio = []; XK.ghiChu = ''; XK.yc = '';
      toast('Đã ghi sổ ' + r.name);
      go(function () { scrXkView(r.name); }, true);
    } catch (e) {
      this.disabled = false;
      toast(e.message || 'Không ghi sổ được.');
    }
  };
}

/* ----- Xem mot phieu xuat ----- */
async function scrXkView(name) {
  vgbCss();
  frame('Phiếu xuất', '<div class="emp"><div class="e1">⏳</div></div>');
  var d = await api('vagabond.xuat_kho.chi_tiet', { name: name });
  var laHuy = d.loai === 'Material Issue';
  var rows = '';
  for (var i = 0; i < d.dong.length; i++) {
    var x = d.dong[i];
    rows += '<div class="vxr"><div class="t"><b>' + h(x.ten || x.ma) + '</b>' +
      '<i>' + h(x.ma) + (x.tien ? ' · ' + vxSo(x.tien) + 'đ' : '') + '</i></div>' +
      '<span style="font-weight:700">' + vxSo(x.sl) + ' ' + h(x.dvt || '') + '</span></div>';
  }
  var nut = '';
  if (d.docstatus === 0) {
    if (d.duoc_duyet) nut += '<button class="vxb" id="vxGhi">Ghi sổ phiếu này</button>';
    if (d.la_cua_toi || d.duoc_duyet) nut += '<button class="vxb o" id="vxXoa">Xoá bản nháp</button>';
    if (!d.duoc_duyet) {
      nut += '<div style="font-size:12px;color:#98a2b3;text-align:center;margin-top:10px">' +
        'Phiếu đang chờ quản lý kho ghi sổ.</div>';
    }
  }
  var body = frame(laHuy ? 'Phiếu xuất huỷ' : 'Phiếu điều chuyển',
    '<div class="vxf">' +
    '<div class="vxr"><div class="t"><b>' + h(d.name) + '</b>' +
    '<i>' + h(d.ngay) + ' · ' + h(d.nguoi_tao) + '</i></div>' +
    '<span class="vxtag ' + (d.docstatus === 0 ? 'c' : 'd') + '">' + h(d.trang_thai) + '</span></div>' +
    '<div class="vxl">' + (laHuy ? 'Kho xuất' : 'Chuyển kho') + '</div>' +
    '<div class="vxr"><div class="t"><b>' + h(d.kho_xuat || '') +
    (d.kho_nhan ? ' → ' + h(d.kho_nhan) : '') + '</b></div></div>' +
    (d.ly_do ? '<div class="vxl">Lý do huỷ</div><div class="vxr"><div class="t"><b>' +
      h(d.ly_do) + '</b></div></div>' : '') +
    (d.ghi_chu ? '<div class="vxl">Ghi chú</div><div class="vxr"><div class="t"><b>' +
      h(d.ghi_chu) + '</b></div></div>' : '') +
    (d.anh ? '<div class="vxl">Ảnh chứng minh</div><img src="' + h(d.anh) +
      '" style="width:100%;border-radius:12px">' : '') +
    '<div class="vxl">Hàng trong phiếu (' + d.dong.length + ' món)</div>' + rows +
    (d.tong_tien ? '<div style="text-align:right;font-weight:700;margin-top:8px">Giá trị: ' +
      vxSo(d.tong_tien) + 'đ</div>' : '') +
    nut + '</div>');

  var g = body.querySelector('#vxGhi');
  if (g) g.onclick = async function () {
    this.disabled = true;
    try {
      await api('vagabond.xuat_kho.ghi_so_xuat_huy', { name: name });
      toast('Đã ghi sổ, tồn kho đã trừ.');
      go(function () { scrXkView(name); }, true);
    } catch (e) {
      this.disabled = false;
      toast(e.message || 'Không ghi sổ được.');
    }
  };
  var x = body.querySelector('#vxXoa');
  if (x) x.onclick = async function () {
    this.disabled = true;
    try {
      await api('vagabond.xuat_kho.xoa_ban_nhap', { name: name });
      toast('Đã xoá bản nháp.');
      back();
    } catch (e) {
      this.disabled = false;
      toast(e.message || 'Không xoá được.');
    }
  };
}

async function vxUpAnh(f) {
  var fd = new FormData();
  fd.append('file', f, f.name);
  fd.append('is_private', '0');
  fd.append('folder', 'Home');
  var r = await fetch('/api/method/upload_file', {
    method: 'POST',
    headers: { 'X-Frappe-CSRF-Token': CSRFT },
    body: fd
  });
  var j = await r.json();
  if (!r.ok || !j.message || !j.message.file_url) throw new Error('máy chủ không nhận ảnh');
  return j.message.file_url;
}

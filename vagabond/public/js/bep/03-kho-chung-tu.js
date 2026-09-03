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

function khoGiuCuaToi() { return (S.me && S.me.khoGiu) ? S.me.khoGiu : []; }
function laKhoCuaToi(k) { var g0 = khoGiuCuaToi(); return !!(k && g0.length && g0.indexOf(k) >= 0); }
function vxKhoXuatOpt(ds, chon) {
  var g0 = khoGiuCuaToi();
  if (g0.length) {
    var loc = (ds || []).filter(function (x) { return g0.indexOf(x.name) >= 0; });
    if (loc.length) ds = loc;
  }
  return vxKhoOpt(ds, chon);
}
try {
  window.vgbLapPhieuChuyen = function (khoXuat, khoNhan) {
    XK.gio = []; XK.ghiChu = ''; XK.yc = '';
    XK.kho = khoXuat || ''; XK.khoNhan = khoNhan || '';
    go(scrXkCkNew);
  };
} catch (eW) { }

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
    srchBox('vxQ', 'Gõ tên hoặc mã hàng, ví dụ banh o', '', true) +
    '<div id="vxKq" style="margin-top:12px"></div></div>');
  var q = body.querySelector('#vxQ');
  var kq = body.querySelector('#vxKq');
  var ds = [];
  /* Tran may chu dang tra ve. Bang dung con so ben xuat_kho.tim_hang, de
     man hinh biet luc nao danh sach BI CAT chu khong phai het hang. */
  var XK_TRAN = 200;
  var choTim = null;

  function themMon(x) {
    for (var m = 0; m < XK.gio.length; m++) {
      if (XK.gio[m].ma === x.ma) { toast('Món này đã có trong phiếu.'); return; }
    }
    /* Mang anh theo vao gio: dong hang trong phieu phai co anh mon (nguyen
       tac thiet ke 03/09/2026). */
    XK.gio.push({ ma: x.ma, ten: x.ten, dvt: x.dvt, ton: x.ton, sl: 1, anh: x.anh || '' });
    toast('Đã thêm ' + (x.ten || x.ma));
    back();
  }

  async function tim() {
    var dang = (q.value || '');
    kq.innerHTML = '<div style="text-align:center;color:#98a2b3;padding:18px">Đang tìm...</div>';
    ds = (await api('vagabond.xuat_kho.tim_hang',
      { kho: kho, tu_khoa: dang, gioi_han: XK_TRAN })) || [];
    /* Go tiep trong luc dang hoi thi bo ket qua cu di, khong ve de len ket
       qua moi hon. */
    if ((q.value || '') !== dang) return;
    if (!ds.length) {
      kq.innerHTML = '<div style="text-align:center;color:#98a2b3;padding:18px;font-size:14px">' +
        (dang
          ? 'Không có mã nào còn tồn khớp với <b>' + h(dang) + '</b> trong kho này.'
          : 'Kho này không còn tồn mã nào.') + '</div>';
      return;
    }
    var anh = {};
    try {
      var its = await getList('Item', { fields: ['name', 'image'], filters: { name: ['in', ds.map(function (x) { return x.ma; })] }, limit_page_length: 0 });
      its.forEach(function (x) { if (x.image) anh[x.name] = x.image; });
    } catch (e) { }
    ds.forEach(function (x) { x.anh = anh[x.ma] || ''; });
    var MAU = ['#e0f2fe', '#fce7f3', '#ecfdf3', '#fef0c7', '#ede9fe', '#fee4e2'];
    var s = '<div class="vxg">';
    for (var i = 0; i < ds.length; i++) {
      var x = ds[i];
      var a = anh[x.ma] ?
        '<img class="vxga" src="' + h(anh[x.ma]) + '" loading="lazy">' :
        '<div class="vxga t" style="background:' + MAU[i % MAU.length] + '">' + h((x.ten || x.ma).charAt(0).toUpperCase()) + '</div>';
      s += '<div class="vxgi" data-th="' + i + '">' + a +
        '<div class="vxgn">' + h(x.ten || x.ma) + '</div>' +
        '<div class="vxgm">' + h(x.ma) + '</div>' +
        '<div class="vxgt' + (x.ton > 0 ? '' : ' r') + '">Tồn ' + vxSo(x.ton) + ' ' + h(x.dvt || '') + '</div></div>';
    }
    /* NOI RO KHI DANH SACH BI CAT.

       Ngay 26/08/2026 Sales bao "ben xuat huy dang bi thieu ma cac san pham
       nhu banh o, banh nuong". Khong ma nao thieu ca: tran cu la 60 dong xep
       theo van chu cai, ma ten banh nao cung bat dau bang chu "Banh", nen 60
       dong dau la het sach Croissant va Banh O nam qua khoi vach cat.

       Cat thi van phai cat, nhung cat ma im lang thi nguoi dung doc thanh
       "he thong thieu ma". Nen no phai tu noi ra. */
    s += '</div>';
    if (ds.length >= XK_TRAN) {
      s += '<div style="font-size:12.5px;color:#b45309;background:#fffbeb;' +
        'border:1px solid #fde68a;border-radius:9px;padding:9px 11px;margin-top:10px;line-height:1.55">' +
        'Kho này còn nhiều hơn ' + XK_TRAN + ' mã, đây mới là ' + XK_TRAN + ' mã đầu. ' +
        'Gõ tên hoặc mã vào ô tìm ở trên để lọc, ví dụ <b>banh o</b> hoặc <b>BAWC</b>.</div>';
    }
    kq.innerHTML = s;
    var rs = kq.querySelectorAll('[data-th]');
    for (var j = 0; j < rs.length; j++) {
      rs[j].onclick = function () { themMon(ds[+this.dataset.th]); };
    }
  }

  async function quet() {
    var code = await scanBarcode(null);
    if (!code) return;
    var ic = await itemByBarcode(String(code).trim());
    if (!ic) { toast('Chưa nhận ra mã ' + code); return; }
    for (var i = 0; i < ds.length; i++) if (ds[i].ma === ic) return themMon(ds[i]);
    var them = (await api('vagabond.xuat_kho.tim_hang',
      { kho: kho, tu_khoa: ic, gioi_han: XK_TRAN })) || [];
    for (var j = 0; j < them.length; j++) if (them[j].ma === ic) return themMon(them[j]);
    toast(ic + ' không còn tồn trong kho này');
  }

  /* TIM NGAY KHI GO, khong bat cho bam Enter.

     Ban cu chi tim khi bam Enter. Tren may tinh o quay va tren dien thoai,
     Sales go xong nhin thay danh sach mac dinh van y nguyen va ket luan la
     "khong co ma do". Anh chup man hinh 26/08 thay ro: o tim dang co chu
     ma luoi ben duoi van la danh sach chua loc.

     Cho 320 mi li giay roi moi hoi, de go mot tu khong thanh nam luot hoi.
     Man Don tiec da lam dung kieu nay tu truoc, nay hai man giong nhau. */
  q.oninput = function () {
    if (choTim) clearTimeout(choTim);
    choTim = setTimeout(tim, 320);
  };
  q.onkeydown = function (e) {
    if (e.key !== 'Enter') return;
    if (choTim) clearTimeout(choTim);
    tim();
  };
  var sb = body.querySelector('#vxQscan');
  if (sb) sb.onclick = quet;
  tim();
}

/* Tab dung chung cho cac danh sach xuat kho */
function vxTabsHtml(TB, cur, dem) {
  return '<div class="vtb">' + TB.map(function (t) {
    return '<div class="vt' + (cur === t.k ? ' on' : '') + '" data-tb="' + t.k + '">' +
      h(t.ten) + (dem[t.k] ? ' <b>' + dem[t.k] + '</b>' : '') + '</div>';
  }).join('') + '</div>';
}
async function vxDsHuy(loai) {
  var moc = new Date(Date.now() - 30 * 864e5).toISOString().slice(0, 10);
  var ds = [];
  try {
    ds = await getList('Stock Entry', {
      fields: ['name', 'posting_date', 'from_warehouse', 'to_warehouse'],
      filters: { docstatus: 2, purpose: loai === 'huy' ? 'Material Issue' : 'Material Transfer', posting_date: ['>=', moc] },
      limit_page_length: 40, order_by: 'modified desc'
    });
  } catch (e) { }
  return ds.map(function (x) {
    return { name: x.name, posting_date: x.posting_date, from_warehouse: shortWh(x.from_warehouse) || '',
      to_warehouse: shortWh(x.to_warehouse) || '', so_dong: 0, nguoi_tao: '', docstatus: 2, trang_thai: 'Đã huỷ' };
  });
}
function vxTheRow(d, tag) {
  var meta = [d.posting_date, d.so_dong ? d.so_dong + ' món' : '', d.nguoi_tao].filter(Boolean).join(' · ');
  return '<div class="vxr" data-xem="' + h(d.name) + '"><div class="t">' +
    '<b>' + h(d.tieu_de || d.name) + '</b>' +
    '<i>' + h(meta) + '</i></div>' + tag + '</div>';
}



/* ----- Xuat huy ----- */
async function scrXkHuyList() {
  vgbCss();
  frame('Xuất huỷ', '<div class="emp"><div class="e1">⏳</div></div>');
  await xkBoot();
  var ds = [];
  try { ds = (await api('vagabond.xuat_kho.ds_phieu', { loai: 'huy', gioi_han: 40 })) || []; } catch (e) { }
  var D = {
    cho: ds.filter(function (x) { return x.docstatus === 0; }),
    xong: ds.filter(function (x) { return x.docstatus === 1; }),
    huy: await vxDsHuy('huy')
  };
  if (!XK.tabH) XK.tabH = 'cho';
  var dem = { cho: D.cho.length, xong: D.xong.length, huy: D.huy.length };
  var TB = [{ k: 'cho', ten: 'Chờ ghi sổ' }, { k: 'xong', ten: 'Đã ghi sổ' }, { k: 'huy', ten: 'Đã huỷ' }];
  var TAG = { cho: ['c', 'Chờ ghi sổ'], xong: ['d', 'Đã ghi sổ'], huy: ['x', 'Đã huỷ'] };

  function listHtml() {
    var ls = D[XK.tabH] || [];
    if (!ls.length) {
      return '<div style="text-align:center;color:#98a2b3;padding:40px 20px;font-size:14px">' +
        (XK.tabH === 'cho' ? 'Không có phiếu nào chờ ghi sổ.<br>Bấm nút + để lập phiếu.' :
          XK.tabH === 'xong' ? 'Chưa có phiếu huỷ nào đã ghi sổ.' : 'Không có phiếu bị huỷ trong 30 ngày qua.') + '</div>';
    }
    var c = TAG[XK.tabH], s = '';
    for (var i = 0; i < ls.length; i++) {
      var x = ls[i];
      x.tieu_de = x.name + (x.from_warehouse ? ' · ' + x.from_warehouse : '');
      s += vxTheRow(x, '<span class="vxtag ' + c[0] + '">' + h(x.trang_thai || c[1]) + '</span>');
    }
    return s;
  }

  var body = frame('Xuất huỷ',
    vxTabsHtml(TB, XK.tabH, dem) + '<div class="vxf" id="vxLst">' + listHtml() + '</div>', {
    fab: 1,
    onFab: function () { XK.gio = []; XK.lyDo = ''; XK.ghiChu = ''; XK.anh = ''; go(scrXkHuyNew); }
  });
  body.onclick = function (e) {
    var tb = e.target.closest('[data-tb]');
    if (tb) {
      XK.tabH = tb.dataset.tb;
      var ts = body.querySelectorAll('[data-tb]');
      for (var i = 0; i < ts.length; i++) ts[i].classList.toggle('on', ts[i].dataset.tb === XK.tabH);
      var el = body.querySelector('#vxLst'); if (el) el.innerHTML = listHtml();
      return;
    }
    var r = e.target.closest('[data-xem]');
    if (r) { var n = r.dataset.xem; go(function () { scrXkView(n); }); }
  };
}



async function scrXkHuyNew() {
  vgbCss();
  if (!XK.kho) { try { XK.kho = localStorage.getItem('vgbKhoXuat') || ''; } catch (e) { } }
  frame('Lập phiếu xuất huỷ', '<div class="emp"><div class="e1">⏳</div></div>');
  var b = await xkBoot();
  var ly = '<option value="">-- chọn lý do --</option>';
  for (var i = 0; i < b.ly_do.length; i++) {
    ly += '<option value="' + h(b.ly_do[i]) + '"' + (b.ly_do[i] === XK.lyDo ? ' selected' : '') +
      '>' + h(b.ly_do[i]) + '</option>';
  }
  /* ANH CHUNG MINH NAY LA BAT BUOC (anh Viet 27/08/2026).

     Truoc day o nay ghi "khong bat buoc". Xuat huy la hang roi khoi cong ty
     va gia tri mat that, nen tam anh la thu duy nhat con lai de doi chieu
     khi co ai hoi lai sau ba thang. Khong co anh thi phieu chi con la mot
     dong chu.

     May chu CHUA chan o nay - phep chan nam ben xuat_kho.luu_xuat_huy va
     doi mot dong o do la doi luat cho ca cac duong goi khac. Man hinh chan
     truoc, va noi ro la bat buoc, con viec siet o may chu de mot ban rieng
     sau khi anh Viet duyet. */
  var body = frame('Lập phiếu xuất huỷ',
    '<div class="vxf">' +

    '<div class="vf">' +
    '<div class="vfh"><span class="ic">🏬</span><b>Kho xuất</b>' +
    '<span class="bat">Bắt buộc</span></div>' +
    '<select class="vfs" id="vxKho">' + vxKhoXuatOpt(b.kho, XK.kho) + '</select>' +
    '<div class="vfm">Hàng sẽ trừ khỏi kho này sau khi quản lý ghi sổ.</div>' +
    '</div>' +

    '<div class="vf">' +
    '<div class="vfh"><span class="ic">❓</span><b>Lý do huỷ</b>' +
    '<span class="bat">Bắt buộc</span></div>' +
    '<select class="vfs" id="vxLy">' + ly + '</select>' +
    '</div>' +

    '<div class="vf">' +
    '<div class="vfh"><span class="ic">📷</span><b>Ảnh chứng minh</b>' +
    '<span class="bat">Bắt buộc</span></div>' +
    '<label class="vfa" id="vxAnhO">' +
    '<input type="file" accept="image/*" id="vxAnh">' +
    '<div class="i">📷</div>' +
    '<div class="t" id="vxAnhT">Chụp hoặc chọn ảnh hàng huỷ</div>' +
    '<div class="p" id="vxAnhP">Chạm vào đây để mở máy ảnh</div>' +
    '</label>' +
    '<div id="vxAnhOk"></div>' +
    '<div class="vfm">Ảnh là thứ duy nhất còn lại để đối chiếu khi có người hỏi lại sau này.</div>' +
    '</div>' +

    '<div class="vf">' +
    '<div class="vfh"><span class="ic">🗑</span><b>Danh sách hàng huỷ</b>' +
    '<span class="bat">Bắt buộc</span></div>' +
    '<div id="vxDong">' + vxDongHtml() + '</div>' +
    '<button class="vxb o" id="vxThem" style="margin-top:8px">+ Thêm hàng</button>' +
    '</div>' +

    '<div class="vf">' +
    '<div class="vfh"><span class="ic">📝</span><b>Ghi chú</b></div>' +
    '<input class="vfi" id="vxGc" placeholder="Ví dụ: bánh trưng bày hết ngày 03/08" value="' + h(XK.ghiChu) + '">' +
    '</div>' +

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
    this.classList.remove('thieu');
    try { localStorage.setItem('vgbKhoXuat', XK.kho); } catch (e) { }
    var seYc = body.querySelector('#vxYc');
    if (seYc && XK.yc) { XK.yc = ''; seYc.value = ''; toast('Đổi kho xuất nên đã bỏ liên kết phiếu yêu cầu.'); }
    vxNoiDong(body);
  };
  eLy.onchange = function () { XK.lyDo = this.value; this.classList.remove('thieu'); };
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
    var o = body.querySelector('#vxAnhO');
    var t = body.querySelector('#vxAnhT');
    var pp = body.querySelector('#vxAnhP');
    var ok = body.querySelector('#vxAnhOk');
    o.classList.remove('thieu');
    t.textContent = 'Đang tải ảnh lên...';
    pp.textContent = f.name || '';
    ok.textContent = '';
    try {
      XK.anh = await vxUpAnh(f);
      o.classList.add('xong');
      t.textContent = 'Đã có ảnh chứng minh';
      pp.textContent = 'Chạm để đổi ảnh khác';
      /* Cho nhin thay ANH THAT vua chon. Ban cu chi hien mot dong chu, nen
         chon nham anh trong thu vien thi khong ai biet cho den luc quan ly
         mo phieu ra xem. */
      ok.innerHTML = '<img class="vfanh" alt="Ảnh chứng minh" src="' + h(XK.anh) + '">';
    } catch (e) {
      o.classList.add('thieu');
      t.textContent = 'Không tải được ảnh';
      pp.textContent = (e && e.message) || String(e);
    }
  };

  body.querySelector('#vxLuu').onclick = async function () {
    XK.kho = eKho.value; XK.lyDo = eLy.value; XK.ghiChu = eGc.value;
    /* To do o nao con thieu roi keo no vao giua man. Ban cu chi bung mot
       cau toast roi tat sau vai giay, nguoi dung doc xong van khong biet
       phai go vao dau - nhat la khi bieu mau dai hon mot man hinh. */
    var thieu = null;
    var to = function (el, co) {
      if (!el) return;
      el.classList.toggle('thieu', !!co);
      if (co && !thieu) thieu = el;
    };
    to(eKho, !XK.kho);
    to(eLy, !XK.lyDo);
    to(body.querySelector('#vxAnhO'), !XK.anh);
    if (thieu) {
      try { thieu.scrollIntoView({ block: 'center', behavior: 'smooth' }); } catch (e) { }
      if (!XK.kho) toast('Chưa chọn kho xuất.');
      else if (!XK.lyDo) toast('Chưa chọn lý do huỷ.');
      else toast('Phiếu xuất huỷ bắt buộc có ảnh chứng minh.', 4000);
      return;
    }
    if (!XK.gio.length) { toast('Chưa có món nào.'); return; }
    this.disabled = true;
    try {
      var r = await api('vagabond.xuat_kho.luu_xuat_huy', {
        kho: XK.kho, ly_do: XK.lyDo, ghi_chu: XK.ghiChu, anh: XK.anh,
        dong: JSON.stringify(XK.gio.map(function (d) { return { ma: d.ma, sl: d.sl }; }))
      });
      XK.gio = []; XK.anh = ''; XK.ghiChu = ''; XK.tabH = 'cho';
      toast('Đã lưu ' + r.name + ', phiếu chờ quản lý ghi sổ.');
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
  var ds = [];
  try { ds = (await api('vagabond.xuat_kho.ds_phieu', { loai: 'chuyen', gioi_han: 40 })) || []; } catch (e) { }
  var D = {
    cho: ds.filter(function (x) { return x.docstatus === 0; }),
    xong: ds.filter(function (x) { return x.docstatus === 1; }),
    huy: await vxDsHuy('chuyen')
  };
  if (!XK.tabC) XK.tabC = 'xong';
  if (D.cho.length) XK.tabC = 'cho';
  var dem = { cho: D.cho.length, xong: D.xong.length, huy: D.huy.length };
  var TB = [{ k: 'cho', ten: 'Chờ ghi sổ' }, { k: 'xong', ten: 'Đã chuyển' }, { k: 'huy', ten: 'Đã huỷ' }];
  var TAG = { cho: ['c', 'Chờ ghi sổ'], xong: ['d', 'Đã chuyển'], huy: ['x', 'Đã huỷ'] };

  function listHtml() {
    var ls = D[XK.tabC] || [];
    if (!ls.length) {
      return '<div style="text-align:center;color:#98a2b3;padding:40px 20px;font-size:14px">' +
        (XK.tabC === 'cho' ? 'Không có phiếu nào chờ ghi sổ.<br>Bấm nút + để lập phiếu.' :
          XK.tabC === 'xong' ? 'Chưa có phiếu điều chuyển nào.<br>Bấm nút + để lập phiếu.' : 'Không có phiếu bị huỷ trong 30 ngày qua.') + '</div>';
    }
    var c = TAG[XK.tabC], s = '';
    for (var i = 0; i < ls.length; i++) {
      var x = ls[i];
      x.tieu_de = (x.from_warehouse || '') + ' → ' + (x.to_warehouse || '');
      var meta0 = x.so_dong; x.nguoi_tao = x.nguoi_tao || x.name;
      s += vxTheRow(x, '<span class="vxtag ' + c[0] + '">' + h(x.trang_thai || c[1]) + '</span>');
    }
    return s;
  }

  var body = frame('Xuất điều chuyển',
    vxTabsHtml(TB, XK.tabC, dem) + '<div class="vxf" id="vxLst">' + listHtml() + '</div>', {
    fab: 1,
    onFab: function () { XK.gio = []; XK.khoNhan = ''; XK.ghiChu = ''; XK.yc = ''; go(scrXkCkNew); }
  });
  body.onclick = function (e) {
    var tb = e.target.closest('[data-tb]');
    if (tb) {
      XK.tabC = tb.dataset.tb;
      var ts = body.querySelectorAll('[data-tb]');
      for (var i = 0; i < ts.length; i++) ts[i].classList.toggle('on', ts[i].dataset.tb === XK.tabC);
      var el = body.querySelector('#vxLst'); if (el) el.innerHTML = listHtml();
      return;
    }
    var r = e.target.closest('[data-xem]');
    if (r) { var n = r.dataset.xem; go(function () { scrXkView(n); }); }
  };
}



async function scrXkCkNew() {
  vgbCss();
  if (!XK.kho) { try { XK.kho = localStorage.getItem('vgbKhoXuat') || ''; } catch (e) { } }
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
    '<div class="vxl">Theo phiếu yêu cầu điều chuyển</div>' +
    '<select class="vxs" id="vxYc">' + ycOpt + '</select>' +
    '<div class="vxl">Kho xuất</div><select class="vxs" id="vxKho">' + vxKhoXuatOpt(b.kho, XK.kho) + '</select>' +
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
    this.classList.remove('thieu');
    try { localStorage.setItem('vgbKhoXuat', XK.kho); } catch (e) { }
    var seYc = body.querySelector('#vxYc');
    if (seYc && XK.yc) { XK.yc = ''; seYc.value = ''; toast('Đổi kho xuất nên đã bỏ liên kết phiếu yêu cầu.'); }
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
  if (XK.yc && !XK.gio.length) { eYc.value = XK.yc; eYc.onchange(); }

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
      XK.gio = []; XK.ghiChu = ''; XK.yc = ''; XK.tabC = 'xong';
      toast('✓ Đã ghi sổ ' + r.name + '. Phiếu nằm ở tab Đã chuyển.');
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
  if (d.docstatus === 1 && !laHuy && d.kho_nhan && (!khoGiuCuaToi().length || laKhoCuaToi(d.kho_nhan))) {
    nut += '<button class="vxb o" id="vxHuyTiep">🗑️ Xuất huỷ hàng này tại ' + h(shortWh(d.kho_nhan)) + '</button>';
  }
  if (d.docstatus === 0 && d.vgb_huy) {
    /* Phieu da bo: khong ghi so duoc nua, nhung van con nguyen de truy. */
    nut += '<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:10px;padding:11px 13px;margin-top:10px">' +
      '<b style="color:#991b1b;font-size:14px">🚫 Phiếu này đã bỏ</b>' +
      '<div style="font-size:12.5px;color:#7f1d1d;line-height:1.6;margin-top:3px">Lý do: ' +
      h(d.vgb_huy_ly_do || 'không ghi') + (d.vgb_huy_boi ? ' - ' + h(d.vgb_huy_boi) : '') +
      '<br>Phiếu vẫn nằm nguyên trong hệ thống, chỉ không ghi sổ được nữa.</div></div>';
  } else if (d.docstatus === 0) {
    if (d.duoc_duyet) nut += '<button class="vxb" id="vxGhi">Ghi sổ phiếu này</button>';
    if (d.la_cua_toi || d.duoc_duyet) nut += '<button class="vxb o" id="vxXoa">🚫 Bỏ phiếu này</button>';
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
    /* Nút X ở góc ảnh (anh Việt 24/08/2026). Chỉ bày khi phiếu CHƯA ghi sổ
       và chưa bị bỏ: ghi sổ rồi thì tồn kho đã trừ thật và tấm ảnh là căn cứ
       của lần trừ đó. Máy chủ chặn lại lần nữa. */
    (d.anh ? '<div class="vxl">Ảnh chứng minh</div>' +
      '<div style="position:relative;padding-top:6px">' +
      '<img src="' + h(d.anh) + '" style="width:100%;border-radius:12px;display:block">' +
      (d.docstatus === 0 && !d.vgb_huy
        ? '<span class="xo" id="vxGoAnh" title="Gỡ ảnh này" ' +
          'style="position:absolute;top:-1px;right:-7px">✕</span>' : '') +
      '</div>' : '') +
    '<div class="vxl">Hàng trong phiếu (' + d.dong.length + ' món)</div>' + rows +
    (d.tong_tien ? '<div style="text-align:right;font-weight:700;margin-top:8px">Giá trị: ' +
      vxSo(d.tong_tien) + 'đ</div>' : '') +
    nut + '</div>');

  var ga = body.querySelector('#vxGoAnh');
  if (ga) ga.onclick = async function () {
    if (!await xacNhan('Gỡ ảnh chứng minh khỏi phiếu ' + d.name + '?\n\n' +
      'Tệp vẫn còn trên máy chủ, chỉ bỏ khỏi phiếu này. Chụp lại rồi đính vào ' +
      'trước khi ghi sổ.', 'Gỡ ảnh', 'Gỡ')) return;
    busy(true);
    try {
      await api('vagabond.xuat_kho.go_anh_xuat_huy', { name: d.name });
      busy(false);
      toast('Đã gỡ ảnh', 2800);
      go(function () { scrXkView(d.name); }, true);
    } catch (e) { busy(false); baoTin(errMsg(e) || 'Không gỡ được ảnh'); }
  };

  var hu = body.querySelector('#vxHuyTiep');
  if (hu) hu.onclick = function () {
    XK.kho = d.kho_nhan; XK.lyDo = ''; XK.anh = ''; XK.ghiChu = 'Hàng nhận từ phiếu ' + d.name + ' không bán được';
    XK.gio = (d.dong || []).map(function (x) { return { ma: x.ma, ten: x.ten, dvt: x.dvt, ton: x.sl, sl: x.sl }; });
    go(scrXkHuyNew);
  };
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
    /* Khong con xoa phieu nua (anh Viet 11/08/2026): phieu kho cung la
       chung tu. Danh dau da bo, phieu van nam lai de con truy. */
    var ly_do = await promptSheet('Vì sao bỏ phiếu này?', 'Lập nhầm, sai kho, sai số lượng...');
    if (ly_do === null) return;
    if (!ly_do) return toast('Phải ghi lý do thì sau này còn biết vì sao.', 4000);
    this.disabled = true;
    try {
      await api('vagabond.xuat_kho.xoa_ban_nhap', { name: name, ly_do: ly_do });
      toast('Đã bỏ phiếu. Phiếu vẫn còn trong danh sách, đánh dấu đã bỏ.', 4000);
      back();
    } catch (e) {
      this.disabled = false;
      toast(e.message || 'Không bỏ được.');
    }
  };
}

/* Nen anh truoc khi tai len: canh dai toi da 1600px, JPEG 72% - anh dien thoai 5MB con ~300KB */
async function vxNenAnh(f) {
  if (!/^image\//.test(f.type || '')) return f;
  var url = '';
  try {
    url = URL.createObjectURL(f);
    var img = await new Promise(function (res, rej) {
      var i = new Image();
      i.onload = function () { res(i); };
      i.onerror = function () { rej(new Error('anh loi')); };
      i.src = url;
    });
    var MAX = 1600, w = img.naturalWidth, hh = img.naturalHeight;
    if (!w || !hh) return f;
    if (w > MAX || hh > MAX) { var ty = Math.min(MAX / w, MAX / hh); w = Math.round(w * ty); hh = Math.round(hh * ty); }
    var cv = document.createElement('canvas');
    cv.width = w; cv.height = hh;
    cv.getContext('2d').drawImage(img, 0, 0, w, hh);
    var blob = await new Promise(function (res) { cv.toBlob(res, 'image/jpeg', 0.72); });
    if (!blob || blob.size >= f.size) return f;
    var ten = (f.name || 'anh').replace(/\.[a-zA-Z0-9]+$/, '') + '.jpg';
    return new File([blob], ten, { type: 'image/jpeg' });
  } catch (e) { return f; }
  finally { try { if (url) URL.revokeObjectURL(url); } catch (e2) { } }
}
async function vxUpAnh(f) {
  f = await vxNenAnh(f);
  function ban() {
    var fd = new FormData();
    fd.append('file', f, f.name);
    fd.append('is_private', '0');
    fd.append('folder', 'Home');
    return fetch('/api/method/upload_file', {
      method: 'POST', credentials: 'same-origin', cache: 'no-store',
      headers: { 'X-Frappe-CSRF-Token': csrfTok() },
      body: fd
    });
  }
  var r = await ban();
  if (r.status === 400 || r.status === 403) {
    if (await refreshCsrf()) r = await ban();
  }
  var j = {};
  try { j = await r.json(); } catch (e) { }
  if (!r.ok || !j.message || !j.message.file_url) throw new Error('máy chủ không nhận ảnh (mã ' + r.status + ')');
  return j.message.file_url;
}

/* ---------- 6. Danh sach chung tu ---------- */
var mrFilter = { status: 'Tất cả', q: '' };
function bepWhFg(v) {
  var lw = String(v || '').toLowerCase();
  var k = lw.indexOf('baker') >= 0 ? 'baker' : (lw.indexOf('lab') >= 0 ? 'lab' : (lw.indexOf('pastry') >= 0 ? 'pastry' : ''));
  if (!k) return '';
  return whFind(k, 'thành phẩm') || whFind(k) || '';
}
function canGiaoBep(d, dlv) {
  if (!d || d.docstatus !== 1) return false;
  if (d.material_request_type !== 'Manufacture') return false;
  if (d.status === 'Stopped' || d.status === 'Cancelled') return false;
  if (!d.set_warehouse) return false;
  if (!bepWhFg(d.custom_bep_nhan)) return false;
  return (d.items || []).some(function (it) {
    var con = (it.stock_qty || (it.qty || 0) * (it.conversion_factor || 1)) - ((dlv || {})[it.name] || 0);
    return con > 0.0001;
  });
}
function bepMau(v) {
  var C = { 'Bếp Pastry': ['#fce7f3', '#9d174d'], 'Bếp Baker': ['#fef3c7', '#92400e'], 'Bếp Lab': ['#dbeafe', '#1e40af'], 'Cả hai bếp': ['#ede9fe', '#5b21b6'] };
  return C[v] || ['#e5e7eb', '#4b5563'];
}
function bepBadge(v) {
  var c = bepMau(v), t = v || 'Chưa rõ bếp';
  return '<span style="display:inline-block;margin-left:6px;padding:1px 7px;border-radius:9px;font-size:11px;font-weight:700;vertical-align:middle;background:' + c[0] + ';color:' + c[1] + '">' + h(t) + '</span>';
}
var BEPS = ['Tất cả', 'Bếp Pastry', 'Bếp Baker', 'Bếp Lab', 'Cả hai bếp', 'Chưa rõ bếp'];

async function scrMRList(T) {
  var body = frame(T.title, '<div class="emp"><div class="e1">⏳</div></div>', { fab: true, onFab: function () { startDraft(T); } });
  var f = { material_request_type: T.key };
  var docs = await getList('Material Request', {
    fields: ['name', 'transaction_date', 'schedule_date', 'status', 'docstatus', 'set_warehouse', 'set_from_warehouse', 'owner', 'title', 'custom_bep_nhan', 'trang_thai_bep'],
    filters: f, limit_page_length: 60, order_by: 'creation desc'
  });
  var STATS = T.key === 'Manufacture'
    ? ['Tất cả', 'Draft', 'Chưa làm', 'Đang làm', 'Đã xong', 'Cancelled']
    : ['Tất cả', 'Draft', 'Pending', 'Partially Ordered', 'Ordered', 'Received', 'Cancelled'];
  function stKey(d) {
    if (T.key !== 'Manufacture') return d.status;
    if (d.docstatus === 0) return 'Draft';
    if (d.status === 'Cancelled') return 'Cancelled';
    return d.trang_thai_bep || 'Chưa làm';
  }
  function drawList() {
    var q = mrFilter.q.toLowerCase();
    var rows = docs.filter(function (d) {
      if (mrFilter.status !== 'Tất cả' && stKey(d) !== mrFilter.status) return false;
      if (T.key === 'Manufacture' && mrFilter.bep && mrFilter.bep !== 'Tất cả' && (d.custom_bep_nhan || 'Chưa rõ bếp') !== mrFilter.bep) return false;
      if (q && (d.name + ' ' + (d.title || '')).toLowerCase().indexOf(q) < 0) return false;
      return true;
    });
    var chips = STATS.map(function (s) {
      var c = s === 'Tất cả' ? docs.length : docs.filter(function (d) { return stKey(d) === s; }).length;
      if (s !== 'Tất cả' && !c) return '';
      return '<div class="chip' + (mrFilter.status === s ? ' on' : '') + '" data-s="' + h(s) + '">' + h(vnSt(s)) + ' ' + c + '</div>';
    }).join('');
    var lst = rows.length ? '<div class="lst">' + rows.map(function (d) {
      var k = stKey(d);
      var cls = k === 'Cancelled' ? 'r' : (k === 'Draft' ? 'w' : ((k === 'Pending' || k === 'Chưa làm') ? 'b' : ((k === 'Đang làm') ? 'w' : 'g')));
      return '<div class="li" data-n="' + h(d.name) + '"><div class="lt">' +
        '<div class="l1">' + h(d.name) + (T.key === 'Manufacture' ? bepBadge(d.custom_bep_nhan) : '') + '</div>' +
        '<div class="l2">' + dmy(d.transaction_date) + ' &middot; cần ' + dmy(d.schedule_date) +
        (d.set_warehouse ? ' &middot; ' + h(shortWh(d.set_warehouse)) : '') + '</div></div>' +
        '<span class="st ' + cls + '">' + h(vnSt(k)) + '</span></div>';
    }).join('') + '</div>' : '<div class="emp"><div class="e1">📄</div><div class="e2">Không có chứng từ nào</div></div>';
    var bchips = T.key !== 'Manufacture' ? '' : '<div class="chips">' + BEPS.map(function (s) {
      var n = s === 'Tất cả' ? docs.length : docs.filter(function (d) { return (d.custom_bep_nhan || 'Chưa rõ bếp') === s; }).length;
      if (s !== 'Tất cả' && !n) return '';
      var cl = bepMau(s === 'Chưa rõ bếp' ? '' : s);
      var on = (mrFilter.bep || 'Tất cả') === s;
      return '<div class="chip' + (on ? ' on' : '') + '" data-bp="' + h(s) + '"' + (on ? '' : ' style="background:' + cl[0] + ';color:' + cl[1] + '"') + '>' + h(s) + ' ' + n + '</div>';
    }).join('') + '</div>';
    var b2 = frame(T.title, '<div class="chips">' + chips + '</div>' + bchips +
      srchBox('mrq', 'Nhập mã chứng từ', mrFilter.q, true) + lst,
      { fab: true, onFab: function () { startDraft(T); } });
    b2.querySelector('#mrq').oninput = function (e) { mrFilter.q = e.target.value; var v = e.target.value; drawList(); var i = document.getElementById('mrq'); i.focus(); i.value = v; i.setSelectionRange(v.length, v.length); };
    document.getElementById('mrqscan').onclick = async function () {
      var code = await scanBarcode();
      if (code) { mrFilter.q = code; drawList(); }
    };
    b2.onclick = function (e) {
      var c = e.target.closest('[data-s]'); if (c) { mrFilter.status = c.dataset.s; return drawList(); }
      var cb = e.target.closest('[data-bp]'); if (cb) { mrFilter.bep = cb.dataset.bp; return drawList(); }
      var r = e.target.closest('[data-n]'); if (r) go(function () { scrMRView(r.dataset.n, T); });
    };
  }
  mrFilter.q = ''; mrFilter.bep = 'Tất cả'; drawList();
}

async function scrMRView(name, T) {
  frame(name, '<div class="emp"><div class="e1">⏳</div></div>');
  var d = await api('frappe.client.get', { doctype: 'Material Request', name: name });
  var dlv = {};
  if (T.key === 'Manufacture' && d.docstatus === 1) {
    try {
      var sedRows = await getList('Stock Entry Detail', {
        parent: 'Stock Entry',
        fields: ['material_request_item', 'transfer_qty'],
        filters: { material_request: name, docstatus: 1 },
        limit_page_length: 0
      });
      (sedRows || []).forEach(function (x) {
        if (!x.material_request_item) return;
        dlv[x.material_request_item] = (dlv[x.material_request_item] || 0) + (x.transfer_qty || 0);
      });
    } catch (eDlv) { }
  }
  var CU_MAU = { 'Chờ mua': '#8a8f98', 'Đang xử lý': '#c77700', 'Đã đặt NCC': '#1a73c7', 'Về một phần': '#7a4bbf', 'Đã nhập kho': '#1f9254', 'Lấy từ kho nội bộ': '#0a8f9e', 'Đã dừng': '#c0392b' };
  function chipCU(v) {
    if (!v) return '';
    return '<span style="display:inline-block;margin-top:5px;padding:2px 9px;border-radius:11px;font-size:12px;font-weight:600;color:#fff;background:' + (CU_MAU[v] || '#8a8f98') + '">' + h(v) + '</span>';
  }
  var laMua = d.material_request_type === 'Purchase';
  var rows = (d.items || []).map(function (it, i) {
    return '<div class="ic1"><div class="ih"><div class="n">' + (i + 1) + '</div>' +
      '<div class="in">' + h(it.item_name || it.item_code) + '<div class="ig">Mã: ' + h(it.item_code) + '</div>' + (laMua ? chipCU(it.trang_thai_cung_ung) : '') + '</div></div>' +
      '<div class="stk"><div><div class="s1">Số lượng</div><div class="s2">' + num(it.qty) + ' ' + h(it.uom) + '</div></div>' +
      (T.hasTime ? '<div><div class="s1">' + h(T.timeLabel) + '</div><div class="s2">' + h(it.gio_can_lay ? String(it.gio_can_lay).slice(0, 5) : '-') + '</div></div>' : '') +
      '<div><div class="s1">Ngày cần</div><div class="s2">' + dmy(it.schedule_date) + '</div></div>' + (laMua && it.ncc_dat_hang ? '<div><div class="s1">Nhà cung cấp</div><div class="s2">' + h(it.ncc_dat_hang) + '</div></div>' : '') + (laMua && it.ngay_hen_giao ? '<div><div class="s1">NCC hẹn giao</div><div class="s2">' + dmy(it.ngay_hen_giao) + '</div></div>' : '') + ((dlv[it.name] || 0) > 0.0001 ? '<div><div class="s1">Đã giao</div><div class="s2">' + num(dlv[it.name] / (it.conversion_factor || 1)) + ' ' + h(it.uom) + '</div></div>' : '') + '</div>' +
      (it.description && it.description.replace(/<[^>]*>/g, '').trim() && it.description.indexOf(it.item_name) < 0 ?
        '<div style="padding:10px 14px;font-size:13.5px;color:#5a6070">' + h(it.description.replace(/<[^>]*>/g, '').trim()) + '</div>' : '') +
      '</div>';
  }).join('');
  var b = frame(name, '<div class="card">' +
    '<div class="kv"><span>Loại phiếu</span><b>' + h(T.title) + '</b></div>' +
    '<div class="kv"><span>Ngày lập</span><b>' + dmy(d.transaction_date) + '</b></div>' +
    '<div class="kv"><span>Ngày cần</span><b>' + dmy(d.schedule_date) + '</b></div>' +
    (d.set_from_warehouse ? '<div class="kv"><span>Kho xuất</span><b>' + h(shortWh(d.set_from_warehouse)) + '</b></div>' : '') +
    (d.set_warehouse ? '<div class="kv"><span>Kho nhận</span><b>' + h(shortWh(d.set_warehouse)) + '</b></div>' : '') +
    (d.bo_phan_yeu_cau ? '<div class="kv"><span>Bộ phận yêu cầu</span><b>' + h(d.bo_phan_yeu_cau) + '</b></div>' : '') +
    (d.nguoi_yeu_cau ? '<div class="kv"><span>Người yêu cầu</span><b>' + h(d.nguoi_yeu_cau) + '</b></div>' : '') +
    (d.custom_bep_nhan ? '<div class="kv"><span>Bếp nhận</span><b>' + h(d.custom_bep_nhan) + '</b></div>' : '') +
    (T.key === 'Manufacture' ? '<div class="kv"><span>Trạng thái bếp</span><b>' + h(d.trang_thai_bep || 'Chưa làm') + (d.bep_nguoi_xong ? ' (' + h(d.bep_nguoi_xong) + ')' : '') + '</b></div>' : '') +
    '<div class="kv"><span>Trạng thái</span><b>' + h(vnSt(d.status)) + '</b></div>' +
    '<div class="kv"><span>Người lập</span><b>' + h(d.nguoi_lap_ten || d.owner) + '</b></div>' + (laMua && d.trang_thai_cung_ung ? '<div class="kv"><span>Cung ứng</span><b>' + chipCU(d.trang_thai_cung_ung) + (d.tom_tat_cung_ung ? '<div style="font-weight:400;font-size:12.5px;color:#5a6070;margin-top:3px">' + h(d.tom_tat_cung_ung) + '</div>' : '') + '</b></div>' : '') + '</div>' +
    '<div class="sec">' + (d.items || []).length + ' hàng hoá</div>' + rows,
    (d.docstatus === 0 ? { footer: '<button class="btn" id="vSub">Gửi duyệt</button>' }
      : (canReceive(d) ? { footer: '<div style="display:flex;gap:10px"><button class="btn" id="vSoan" style="background:#fff;color:#101828;border:1px solid #d0d5dd">🧺 Soạn hàng (kho xuất)</button><button class="btn" id="vRecv">📦 Đã nhận hàng</button></div>' }
      : (canGiaoBep(d, dlv) ? { footer: '<button class="btn" id="vGiao">🚚 Giao hàng sang ' + h(shortWh(d.set_warehouse)) + '</button>' } : {}))));
  var sn = document.getElementById('vSoan');
  if (sn) sn.onclick = function () {
    XK.gio = []; XK.ghiChu = '';
    XK.yc = d.name;
    XK.kho = d.set_from_warehouse || '';
    XK.khoNhan = d.set_warehouse || '';
    go(scrXkCkNew);
  };
  var rc = document.getElementById('vRecv');
  if (rc) rc.onclick = async function () {
    var nhap = [];
    try { nhap = await getList('Stock Entry Detail', { parent: 'Stock Entry', fields: ['parent'], filters: { material_request: d.name, docstatus: 0 }, limit_page_length: 1 }); } catch (e) { }
    if (nhap.length) {
      if (!await confirmSheet('Kho xuất đang soạn phiếu ' + nhap[0].parent, 'Phiếu điều chuyển nháp của yêu cầu này đang chờ ghi sổ. Bấm nhận ở đây nữa là trừ kho HAI LẦN. Chỉ tiếp tục nếu chắc chắn phiếu kia sẽ bị huỷ.', 'Vẫn tiếp tục')) return;
    }
    go(function () { scrRecvTransfer(d); });
  };
  var gb = document.getElementById('vGiao');
  if (gb) gb.onclick = function () {
    var srcW = bepWhFg(d.custom_bep_nhan);
    if (!srcW) return toast('Phiếu chưa ghi bếp nhận nên chưa biết xuất từ kho nào');
    go(function () {
      scrRecvTransfer(d, {
        src: srcW,
        doneMap: dlv,
        title: 'Giao hàng ',
        okLabel: 'Xác nhận giao hàng',
        emptyMsg: 'Phiếu này đã giao đủ hàng',
        remarks: 'Bếp giao hàng cho kho nhận theo phiếu '
      });
    });
  };
  var s = document.getElementById('vSub');
  if (s) s.onclick = async function () {
    if (!await confirmSheet('Gửi duyệt phiếu?', 'Sau khi gửi sẽ không sửa được nội dung.', 'Gửi duyệt')) return;
    busy(1);
    try { await api('frappe.client.submit', { doc: d }); toast('Đã gửi phiếu ' + name); back(); }
    catch (err) { toast(errMsg(err)); } finally { busy(0); }
  };
}

/* ---------- 6b. Xac nhan nhan hang cua phieu dieu chuyen noi bo ---------- */
function canReceive(d) {
  if (!d || d.docstatus !== 1) return false;
  if (d.material_request_type !== 'Material Transfer') return false;
  if (d.status === 'Stopped' || d.status === 'Cancelled') return false;
  var left = (d.items || []).some(function (it) { return (it.qty || 0) - (it.ordered_qty || 0) > 0.0001; });
  return left;
}

async function fefoPick(code, wh, need) {
  var q = {};
  try {
    var bq = await api('erpnext.stock.doctype.batch.batch.get_batch_qty', { item_code: code, warehouse: wh }) || [];
    bq.forEach(function (x) { if (x.batch_no) q[x.batch_no] = (q[x.batch_no] || 0) + (x.qty || 0); });
  } catch (e) {
    var sle = await getList('Stock Ledger Entry', {
      fields: ['batch_no', 'actual_qty'],
      filters: { item_code: code, warehouse: wh, is_cancelled: 0 }, limit_page_length: 0
    });
    sle.forEach(function (x) { if (x.batch_no) q[x.batch_no] = (q[x.batch_no] || 0) + (x.actual_qty || 0); });
  }
  var names = Object.keys(q).filter(function (b) { return q[b] > 0.0000001; });
  if (!names.length) return { short: need, list: [] };
  var ex = {};
  try {
    var bs = await getList('Batch', { fields: ['name', 'expiry_date'], filters: { name: ['in', names] }, limit_page_length: 0 });
    bs.forEach(function (b) { ex[b.name] = b.expiry_date || '9999-12-31'; });
  } catch (e2) { }
  names.sort(function (a, b) {
    var ea = ex[a] || '9999-12-31', eb = ex[b] || '9999-12-31';
    if (ea !== eb) return ea < eb ? -1 : 1;
    return a < b ? -1 : 1;
  });
  var out = [], rem = need;
  for (var i = 0; i < names.length && rem > 0.0000001; i++) {
    var take = q[names[i]] < rem ? q[names[i]] : rem;
    out.push({ batch: names[i], qty: Math.round(take * 1000000) / 1000000 });
    rem -= take;
  }
  return { short: rem > 0.0000001 ? rem : 0, list: out };
}

var rcv = { mr: null, rows: [] };
async function scrRecvTransfer(mr, opt) {
  opt = opt || {};
  rcv.mr = mr;
  rcv.rows = (mr.items || []).map(function (it) {
    var done = opt.doneMap ? ((opt.doneMap[it.name] || 0) / (it.conversion_factor || 1)) : (it.ordered_qty || 0);
    var left = (it.qty || 0) - done;
    return {
      row: it.name, item_code: it.item_code, item_name: it.item_name || it.item_code,
      uom: it.uom, stock_uom: it.stock_uom || it.uom, cf: it.conversion_factor || 1,
      max: left, qty: left > 0 ? left : 0, done: done
    };
  }).filter(function (r) { return r.max > 0.0001; });

  var src = opt.src || mr.set_from_warehouse || (mr.items && mr.items[0] && mr.items[0].from_warehouse) || '';
  var dst = mr.set_warehouse || (mr.items && mr.items[0] && mr.items[0].warehouse) || '';

  function draw() {
    var cards = rcv.rows.map(function (r, i) {
      return '<div class="ic1">' +
        '<div class="ih"><div class="n">' + (i + 1) + '</div>' +
        '<div class="in">' + h(r.item_name) + '<div class="ig">Mã: ' + h(r.item_code) + '</div></div></div>' +
        '<div class="stk"><div><div class="s1">Phiếu xin</div><div class="s2">' + num(r.max) + ' ' + h(r.uom) + '</div></div>' +
        (r.done > 0.0001 ? '<div><div class="s1">Đã nhận trước</div><div class="s2">' + num(r.done) + ' ' + h(r.uom) + '</div></div>' : '') +
        '</div>' +
        '<div class="qw"><div style="flex:1;min-width:0"><div class="lb">Số lượng thực nhận</div>' +
        '<div class="qr"><div class="stp"><button data-m="' + i + '">&minus;</button>' +
        '<input type="number" inputmode="decimal" data-q="' + i + '" value="' + r.qty + '"><button data-p="' + i + '">+</button></div>' +
        '<div class="uom" style="display:flex;align-items:center;justify-content:center">' + h(r.uom) + '</div></div></div></div>' +
        '</div>';
    }).join('');

    var head = '<div class="card">' +
      '<div class="kv"><span>Phiếu</span><b>' + h(mr.name) + '</b></div>' +
      '<div class="kv"><span>Kho xuất</span><b>' + h(shortWh(src) || '-') + '</b></div>' +
      '<div class="kv"><span>Kho nhận</span><b>' + h(shortWh(dst) || '-') + '</b></div>' +
      '</div>' +
      '<div style="padding:2px 16px 0;font-size:12.5px;color:#8a8f9c;line-height:1.5">Sửa lại số lượng nếu nhận thiếu. Bấm xác nhận là máy trừ kho ' + h(shortWh(src)) + ' và nhập vào kho ' + h(shortWh(dst)) + '. Lô hàng máy tự chọn theo hạn dùng gần nhất trước.</div>';

    var body = rcv.rows.length
      ? head + '<div class="sec">' + rcv.rows.length + ' hàng hoá</div>' + cards
      : head + '<div class="emp"><div class="e1">✅</div><div class="e2">' + h(opt.emptyMsg || 'Phiếu này đã nhận đủ hàng') + '</div></div>';

    var b = frame((opt.title || 'Nhận hàng ') + mr.name, body,
      rcv.rows.length ? { footer: '<button class="btn" id="rcOk">' + h(opt.okLabel || 'Xác nhận nhập kho') + '</button>' } : {});

    b.onclick = function (e) {
      var p = e.target.closest('[data-p]'), m = e.target.closest('[data-m]');
      var i = p ? +p.dataset.p : (m ? +m.dataset.m : -1);
      if (i < 0) return;
      var r = rcv.rows[i];
      var v = (r.qty || 0) + (p ? 1 : -1);
      if (v < 0) v = 0;
      if (v > r.max) v = r.max;
      r.qty = Math.round(v * 1000000) / 1000000;
      var inp = b.querySelector('[data-q="' + i + '"]');
      if (inp) inp.value = r.qty;
    };
    b.addEventListener('input', function (e) {
      var q = e.target.closest('[data-q]'); if (!q) return;
      var i = +q.dataset.q, r = rcv.rows[i];
      var v = parseFloat(q.value); if (!(v >= 0)) v = 0;
      if (v > r.max) { v = r.max; q.value = v; toast('Không nhận quá số trên phiếu'); }
      r.qty = v;
    });

    var ok = document.getElementById('rcOk');
    if (ok) ok.onclick = function () { doReceive(mr, src, dst, opt); };
  }
  draw();
}

async function doReceive(mr, src, dst, opt) {
  opt = opt || {};
  var use = rcv.rows.filter(function (r) { return r.qty > 0.0001; });
  if (!use.length) return toast('Chưa nhập số lượng nào');
  if (!src) return toast('Phiếu chưa có kho xuất, không nhập kho được');
  if (!dst) return toast('Phiếu chưa có kho nhận, không nhập kho được');
  var ok = await confirmSheet('Nhập hàng vào kho ' + shortWh(dst),
    'Máy sẽ trừ ' + use.length + ' món ở kho ' + shortWh(src) + ' và nhập vào kho ' + shortWh(dst) + '. Bút toán kho không sửa lại được.',
    'Xác nhận nhập kho');
  if (!ok) return;
  busy(1);
  try {
    var codes = use.map(function (r) { return r.item_code; });
    var metas = await getList('Item', { fields: ['name', 'has_batch_no'], filters: { name: ['in', codes] }, limit_page_length: 0 });
    var hb = {};
    metas.forEach(function (x) { hb[x.name] = x.has_batch_no ? 1 : 0; });

    var items = [], thieu = [];
    for (var i = 0; i < use.length; i++) {
      var r = use[i];
      if (hb[r.item_code]) {
        var need = r.qty * (r.cf || 1);
        var al = await fefoPick(r.item_code, src, need);
        if (al.short > 0.0001) { thieu.push(r.item_name + ' (thiếu ' + num(al.short) + ' ' + r.stock_uom + ')'); continue; }
        al.list.forEach(function (a) {
          items.push({
            item_code: r.item_code, qty: a.qty, uom: r.stock_uom, conversion_factor: 1,
            s_warehouse: src, t_warehouse: dst, use_serial_batch_fields: 1, batch_no: a.batch,
            material_request: mr.name, material_request_item: r.row
          });
        });
      } else {
        items.push({
          item_code: r.item_code, qty: r.qty, uom: r.uom, conversion_factor: r.cf || 1,
          s_warehouse: src, t_warehouse: dst,
          material_request: mr.name, material_request_item: r.row
        });
      }
    }
    if (thieu.length) { busy(0); return toast('Kho ' + shortWh(src) + ' không đủ lô hàng: ' + thieu.join('; '), 7000); }
    if (!items.length) { busy(0); return toast('Không có dòng nào để nhập kho'); }

    var doc = {
      doctype: 'Stock Entry', company: COMPANY,
      stock_entry_type: 'Material Transfer', purpose: 'Material Transfer',
      set_posting_time: 1, posting_date: today(), posting_time: nowStamp().slice(11),
      from_warehouse: src, to_warehouse: dst, items: items,
      remarks: (opt.remarks || 'Nhận hàng điều chuyển nội bộ trên app - phiếu ') + mr.name + ' - ' + (S.me.full_name || S.user)
    };
    var ins = await api('frappe.client.insert', { doc: doc });
    await api('frappe.client.submit', { doc: ins });
    busy(0);
    toast('Đã nhập kho ' + shortWh(dst) + ' theo phiếu ' + mr.name + ' (' + ins.name + ')', 4500);
    back();
    setTimeout(function () { render(); }, 60);
  } catch (err) { busy(0); toast(errMsg(err), 6000); }
}

function errMsg(e) {
  var m = (e && (e.message || e._server_messages || '')) + '';
  try { var a = JSON.parse(e._server_messages); m = JSON.parse(a[0]).message; } catch (x) { }
  return (m || 'Có lỗi xảy ra').replace(/<[^>]*>/g, '').slice(0, 180);
}



/* ---------- Hàng chuyển về kho tôi (anh Việt 18/08/2026) ----------

Anh nói bộ phận Bếp "đang bị nghẽn ở khâu nhận hàng". Em đọc lại luồng thì
thấy không ai chặn các bạn ấy cả: phiếu điều chuyển ở hệ này ghi sổ MỘT BƯỚC
bên kho xuất, nên hàng vào kho bếp ngay lập tức mà bên bếp không có màn nào
thấy nó đã về, về lúc nào, ai chuyển, gồm những gì.

Màn này lấp đúng chỗ trống đó, và nó CHỈ ĐỌC. Bước "xác nhận đã nhận" và xử
lý nhận thiếu (chênh lệch sinh bút toán hao hụt) đụng vào giá vốn nên phải
chờ anh Việt duyệt phương án trước - em để trong bảng mapping luồng kho. */
var HVK = { ngay: 14, mo: '' };

async function scrHangVeKho() {
  vgbCss();
  frame('Hàng chuyển về kho tôi', '<div class="emp"><div class="e1">⏳</div><div>Đang xem hàng về kho...</div></div>');
  var kq;
  try { kq = await api('vagabond.xuat_kho.hang_chuyen_ve', { so_ngay: HVK.ngay }); }
  catch (e) {
    return frame('Hàng chuyển về kho tôi',
      '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không đọc được') + '</div></div>');
  }
  if (!kq.co_kho) {
    return frame('Hàng chuyển về kho tôi',
      '<div class="emp"><div class="e1">🏷️</div><div>' + h(kq.nhac || 'Chưa khai kho phụ trách.') + '</div></div>');
  }
  var ds = kq.ds || [];
  var html =
    '<div style="font-size:11.5px;color:#98a2b3;padding:0 2px 8px;line-height:1.6">' +
    'Hàng các kho khác đã chuyển sang <b>' + h((kq.kho || []).join(', ')) + '</b>. ' +
    'Bấm một phiếu để xem danh sách hàng bên trong.</div>' +
    '<div class="vtb" style="padding-left:0;padding-right:0">' +
    [[7, '7 ngày'], [14, '14 ngày'], [30, '30 ngày']].map(function (x) {
      return '<div class="vt' + (HVK.ngay === x[0] ? ' on' : '') + '" data-hvn="' + x[0] + '">' + x[1] + '</div>';
    }).join('') + '</div>';

  if (!ds.length) {
    html += '<div class="emp"><div class="e1">📦</div><div>Không có phiếu nào chuyển về kho của bạn trong ' +
      HVK.ngay + ' ngày qua.</div></div>';
  } else {
    html += '<div class="card">' + ds.map(function (x) {
      var mo = HVK.mo === x.ma;
      return '<div style="border-bottom:1px solid #f2f4f7">' +
        '<div data-hvm="' + h(x.ma) + '" style="padding:12px 14px;display:flex;gap:10px;align-items:center;cursor:pointer">' +
        '<div style="flex:1;min-width:0">' +
        '<b style="font-size:13.5px">' + h(x.kho_xuat || 'Kho khác') + ' → ' + h(x.kho_nhan) + '</b>' +
        '<div style="font-size:11.5px;color:#98a2b3;margin-top:2px">' +
        dmy(x.ngay) + (x.gio ? ' ' + h(x.gio) : '') + ' · ' + h(x.nguoi_ten) + ' · ' + h(x.ma) + '</div></div>' +
        '<div style="text-align:right"><b style="font-size:14px;color:#0f766e">' + money(x.so_dong) + ' món</b>' +
        '<div style="font-size:11px;color:#9ca3af">' + money(x.tong_sl) + ' đơn vị</div></div>' +
        '<span style="color:#c3c8d4;font-size:20px">' + (mo ? '&#8964;' : '&#8250;') + '</span></div>' +
        (mo
          ? '<div style="padding:0 14px 12px">' + (x.hang || []).map(function (m) {
            return '<div style="display:flex;gap:8px;padding:6px 0;border-top:1px solid #f6f7f9;font-size:12.5px">' +
              '<div style="flex:1;min-width:0">' + h(m.ten) + '<div style="font-size:11px;color:#aeb4bf">' + h(m.ma) + '</div></div>' +
              '<b style="color:#0f766e;white-space:nowrap">' + money(m.sl) + ' ' + h(m.dvt) + '</b></div>';
          }).join('') +
          (x.ghi_chu ? '<div style="font-size:11px;color:#98a2b3;margin-top:8px">' + h(x.ghi_chu) + '</div>' : '') +
          /* Nut xac nhan nhan hang (anh Viet chot phuong an A ngay
             02/09/2026). Man nay von CHI DOC; nut nay van khong dung toi so
             kho, no chi ghi lai loi khai cua nguoi nhan. Xem doan dai o dau
             vagabond/nhan_dieu_chuyen.py. */
          (x.da_nhan
            ? '<div style="font-size:11.5px;color:#0f766e;margin-top:10px;font-weight:600">' +
              '\u2713 ' + h(x.da_nhan) + (x.nhan_boi ? ' - ' + h(x.nhan_boi) : '') + '</div>'
            : '<button class="vxb o" data-hvx="' + h(x.ma) + '" style="margin-top:10px">' +
              '\u2713 X\u00e1c nh\u1eadn nh\u1eadn h\u00e0ng</button>') +
          '</div>'
          : '') +
        '</div>';
    }).join('') + '</div>';
  }

  var b = frame('Hàng chuyển về kho tôi', html);
  b.querySelectorAll('[data-hvn]').forEach(function (n) {
    n.onclick = function () { HVK.ngay = +n.getAttribute('data-hvn'); HVK.mo = ''; go(scrHangVeKho, true); };
  });
  b.querySelectorAll('[data-hvm]').forEach(function (n) {
    n.onclick = function () {
      var m = n.getAttribute('data-hvm');
      HVK.mo = (HVK.mo === m) ? '' : m;
      go(scrHangVeKho, true);
    };
  });
  b.querySelectorAll('[data-hvx]').forEach(function (n) {
    n.onclick = function (ev) {
      /* Chan noi len: the cha co onclick dong lai phan dang mo, bam nut
         xac nhan ma the cha nghe duoc thi man tu sap lai truoc khi di. */
      ev.stopPropagation();
      var m = n.getAttribute('data-hvx');
      go(function () { return scrNhanDcXacNhan(m); });
    };
  });
}

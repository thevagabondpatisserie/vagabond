/* ---------- 5d. Ba man con lai cua phan he Xuat kho ----------

Anh Viet chot 02/09/2026. Truoc hom nay phan he chi co Xuat huy va Dieu
chuyen, nen:

- Banh cho Marketing chup anh phai lap phieu XUAT HUY. Gia tri to banh do
  vao cung tai khoan voi hang hong, va cuoi thang bao cao hao hut do oan
  cho Bep.
- Hang loi tra ve nha cung cap khong co duong nao ca. Lam phieu xuat thuong
  thi hang di ma cong no van nguyen, ke toan phai go but toan tay.
- Don si giao cho khach doanh nghiep khong co phieu giao hang, nen khong co
  chung tu nao ghi gia von cho no.

Ba man nay de moi viec that di dung mot duong, thay vi muon tam cai nut gan
giong nhat. Dat trong tep RIENG chu khong nhet vao 03-kho-chung-tu.js: tep
do dang la 1.184 dong va cac phien khac hay sua no, tach ra la bot mot cho
de dung nhau.

Dung lai het khung san co cua 03: `frame`, `vxTheRow`, `vxTabsHtml`,
`vxKhoXuatOpt`, `vxDongHtml`, `vxNoiDong`, `scrXkChonHang`, `vxUpAnh`. Ba
man nay chi lo phan khac nhau.
*/

var XKT = {
  /* Trang thai man Xuat dung noi bo */
  nb: { gio: [], kho: '', mucDich: '', boPhan: '', ghiChu: '', anh: '', tab: 'cho' },
  /* Trang thai man Tra nha cung cap */
  tra: { ncc: '', tenNcc: '', phieu: '', lyDo: '', ghiChu: '', anh: '', dong: [], tab: 'xong' },
  /* Trang thai man Xuat ban si */
  si: { gio: [], kho: '', khach: '', tenKhach: '', nguoiNhan: '', ghiChu: '', tab: 'xong' },
  bootNb: null,
  bootTra: null,
  bootSi: null
};

function xktBoPhanOpt(khoi, chon) {
  var s = '<option value="">-- chọn bộ phận --</option>';
  for (var i = 0; i < (khoi || []).length; i++) {
    var k = khoi[i];
    s += '<optgroup label="' + h(k.nhom) + '">';
    for (var j = 0; j < k.bo_phan.length; j++) {
      var b = k.bo_phan[j];
      s += '<option value="' + h(b.ten) + '"' + (b.ten === chon ? ' selected' : '') +
        '>' + h(b.ten) + '</option>';
    }
    s += '</optgroup>';
  }
  return s;
}

/* ==================================================================
   1. XUAT DUNG NOI BO
   ================================================================== */

async function xktBootNb() {
  if (!XKT.bootNb) XKT.bootNb = await api('vagabond.xuat_noi_bo.khoi_dong');
  return XKT.bootNb;
}

async function scrXkNbList() {
  vgbCss();
  frame('Xuất dùng nội bộ', '<div class="emp"><div class="e1">⏳</div></div>');
  await xktBootNb();
  var ds = [], loiDs = '';
  /* KHONG nuot loi (sua 03/09/2026). Ban v387 nuot im, nen khi may chu do
     thi man hien "chua co phieu nao" - nhin nhu binh thuong, va loi cua man
     Xuat ban si nam do ba ngay khong ai biet. */
  try { ds = (await api('vagabond.xuat_noi_bo.ds_phieu', { gioi_han: 40 })) || []; }
  catch (e) { loiDs = errMsg(e) || 'Không đọc được danh sách phiếu.'; }
  var D = {
    cho: ds.filter(function (x) { return x.docstatus === 0; }),
    xong: ds.filter(function (x) { return x.docstatus === 1; })
  };
  var dem = { cho: D.cho.length, xong: D.xong.length };
  var TB = [{ k: 'cho', ten: 'Chờ ghi sổ' }, { k: 'xong', ten: 'Đã ghi sổ' }];
  var TAG = { cho: ['c', 'Chờ ghi sổ'], xong: ['d', 'Đã ghi sổ'] };

  function listHtml() {
    var ls = D[XKT.nb.tab] || [];
    if (loiDs) return xktLoiHtml(loiDs);
    if (!ls.length) {
      return '<div style="text-align:center;color:#98a2b3;padding:40px 20px;font-size:14px">' +
        (XKT.nb.tab === 'cho'
          ? 'Không có phiếu nào chờ ghi sổ.<br>Bấm nút + để lập phiếu.'
          : 'Chưa có phiếu xuất dùng nội bộ nào đã ghi sổ.') + '</div>';
    }
    var c = TAG[XKT.nb.tab], s = '';
    for (var i = 0; i < ls.length; i++) {
      var x = ls[i];
      x.tieu_de = x.name + (x.ten_muc_dich ? ' · ' + x.ten_muc_dich : '');
      s += vxTheRow(x, '<span class="vxtag ' + c[0] + '">' + h(x.trang_thai || c[1]) + '</span>');
    }
    return s;
  }

  var body = frame('Xuất dùng nội bộ',
    '<div style="font-size:11.5px;color:#98a2b3;padding:0 2px 8px;line-height:1.6">' +
    'Hàng ra khỏi kho mà <b>tiệm vẫn dùng</b>: chụp ảnh, mẫu thử, mời khách, ' +
    'ăn ca. Hàng hỏng thật thì vẫn đi đường Xuất huỷ.</div>' +
    vxTabsHtml(TB, XKT.nb.tab, dem) + '<div class="vxf" id="vxLst">' + listHtml() + '</div>', {
    fab: 1,
    onFab: function () {
      XKT.nb.gio = []; XKT.nb.mucDich = ''; XKT.nb.boPhan = '';
      XKT.nb.ghiChu = ''; XKT.nb.anh = '';
      go(scrXkNbNew);
    }
  });
  body.onclick = function (e) {
    var tb = e.target.closest('[data-tb]');
    if (tb) {
      XKT.nb.tab = tb.dataset.tb;
      var ts = body.querySelectorAll('[data-tb]');
      for (var i = 0; i < ts.length; i++) ts[i].classList.toggle('on', ts[i].dataset.tb === XKT.nb.tab);
      var el = body.querySelector('#vxLst'); if (el) el.innerHTML = listHtml();
      return;
    }
    var r = e.target.closest('[data-xem]');
    if (r) { var n = r.dataset.xem; go(function () { scrXkNbView(n); }); }
  };
}

async function scrXkNbNew() {
  vgbCss();
  if (!XKT.nb.kho) { try { XKT.nb.kho = localStorage.getItem('vgbKhoXuat') || ''; } catch (e) { } }
  frame('Lập phiếu xuất dùng nội bộ', '<div class="emp"><div class="e1">⏳</div></div>');
  var b = await xktBootNb();

  var md = '<option value="">-- chọn mục đích --</option>';
  for (var i = 0; i < b.muc_dich.length; i++) {
    var m = b.muc_dich[i];
    md += '<option value="' + h(m.ma) + '"' + (m.ma === XKT.nb.mucDich ? ' selected' : '') +
      ' data-bp="' + h(m.bo_phan || '') + '">' + h(m.ten) + '</option>';
  }

  var body = frame('Lập phiếu xuất dùng nội bộ',
    '<div class="vxf">' +

    '<div class="vf">' +
    '<div class="vfh"><span class="ic">🏬</span><b>Kho xuất</b>' +
    '<span class="bat">Bắt buộc</span></div>' +
    '<select class="vfs" id="nbKho">' + vxKhoXuatOpt(b.kho, XKT.nb.kho) + '</select>' +
    '</div>' +

    '<div class="vf">' +
    '<div class="vfh"><span class="ic">🎯</span><b>Mục đích xuất dùng</b>' +
    '<span class="bat">Bắt buộc</span></div>' +
    '<select class="vfs" id="nbMd">' + md + '</select>' +
    '<div class="vfm" id="nbMdMo">Chọn mục đích để máy ghi chi phí vào đúng chỗ.</div>' +
    '</div>' +

    /* O bo phan la ly do ton tai cua ca man nay. Chon xong thi gia tri hang
       xuat vao dung so cua bo phan do, khong con lan vao hao hut cua Bep. */
    '<div class="vf">' +
    '<div class="vfh"><span class="ic">🏛️</span><b>Bộ phận chịu chi phí</b>' +
    '<span class="bat">Bắt buộc</span></div>' +
    '<select class="vfs" id="nbBp">' + xktBoPhanOpt(b.bo_phan, XKT.nb.boPhan) + '</select>' +
    '<div class="vfm">Cuối tháng đọc báo cáo là biết bộ phận nào dùng bao nhiêu.</div>' +
    '</div>' +

    '<div class="vf">' +
    '<div class="vfh"><span class="ic">📦</span><b>Danh sách hàng</b>' +
    '<span class="bat">Bắt buộc</span></div>' +
    '<div id="vxDong">' + xktDongHtml(XKT.nb.gio) + '</div>' +
    '<button class="vxb o" id="nbThem" style="margin-top:8px">+ Thêm hàng</button>' +
    '</div>' +

    /* Anh KHONG bat buoc o day, khac han Xuat huy. Banh mang di chup thi
       chinh tam anh san pham la bang chung; bat chup them mot tam nua chi
       de luu ho so la them mot buoc vo ich. */
    '<div class="vf">' +
    '<div class="vfh"><span class="ic">📷</span><b>Ảnh (không bắt buộc)</b></div>' +
    '<label class="vfa" id="nbAnhO">' +
    '<input type="file" accept="image/*" id="nbAnh">' +
    '<div class="i">📷</div>' +
    '<div class="t" id="nbAnhT">Chụp hoặc chọn ảnh</div>' +
    '<div class="p" id="nbAnhP">Chạm vào đây để mở máy ảnh</div>' +
    '</label><div id="nbAnhOk"></div>' +
    '</div>' +

    '<div class="vf">' +
    '<div class="vfh"><span class="ic">📝</span><b>Ghi chú</b></div>' +
    '<input class="vfi" id="nbGc" placeholder="Ví dụ: chụp bộ ảnh Trung thu" value="' +
    h(XKT.nb.ghiChu) + '">' +
    '</div>' +

    '<button class="vxb" id="nbLuu">Lưu phiếu, chờ quản lý ghi sổ</button>' +
    '<div style="font-size:12px;color:#98a2b3;text-align:center;margin-top:10px">' +
    'Tồn kho chỉ trừ sau khi quản lý kho bấm Ghi sổ.</div></div>');

  var eKho = body.querySelector('#nbKho');
  var eMd = body.querySelector('#nbMd');
  var eBp = body.querySelector('#nbBp');
  var eGc = body.querySelector('#nbGc');

  eKho.onchange = function () {
    if (XKT.nb.kho && this.value !== XKT.nb.kho && XKT.nb.gio.length) {
      XKT.nb.gio = [];
      toast('Đổi kho nên phải chọn lại hàng.');
    }
    XKT.nb.kho = this.value;
    this.classList.remove('thieu');
    try { localStorage.setItem('vgbKhoXuat', XKT.nb.kho); } catch (e) { }
    xktNoiDong(body, XKT.nb.gio);
  };
  eMd.onchange = function () {
    XKT.nb.mucDich = this.value;
    this.classList.remove('thieu');
    var o = this.options[this.selectedIndex];
    var mo = body.querySelector('#nbMdMo');
    for (var i = 0; i < b.muc_dich.length; i++) {
      if (b.muc_dich[i].ma === this.value && mo) mo.textContent = b.muc_dich[i].mo;
    }
    /* Dien san bo phan hay gap cua muc dich do, nguoi lap doi duoc. Chi
       dien khi o dang TRONG: da chon roi ma bi ghi de la mat cong go lai. */
    var goi = o ? (o.dataset.bp || '') : '';
    if (goi && !eBp.value) { eBp.value = goi; XKT.nb.boPhan = goi; eBp.classList.remove('thieu'); }
  };
  eBp.onchange = function () { XKT.nb.boPhan = this.value; this.classList.remove('thieu'); };
  eGc.onchange = function () { XKT.nb.ghiChu = this.value; };
  xktNoiSuKien(body, XKT.nb.gio);

  body.querySelector('#nbThem').onclick = function () {
    XKT.nb.kho = eKho.value; XKT.nb.mucDich = eMd.value;
    XKT.nb.boPhan = eBp.value; XKT.nb.ghiChu = eGc.value;
    if (!XKT.nb.kho) { toast('Chọn kho xuất trước đã.'); return; }
    var kho = XKT.nb.kho;
    /* Man chon hang cua 03 ghi thang vao XK.gio. Muon dung lai no ma khong
       sua no thi muon tam XK.gio, chon xong keo ve gio cua man nay. */
    XK.gio = XKT.nb.gio.slice();
    go(function () { scrXkChonHang(kho, function () { XKT.nb.gio = XK.gio.slice(); return scrXkNbNew(); }); });
  };

  body.querySelector('#nbAnh').onchange = async function () {
    var f = this.files && this.files[0];
    if (!f) return;
    var t = body.querySelector('#nbAnhT');
    var pp = body.querySelector('#nbAnhP');
    var ok = body.querySelector('#nbAnhOk');
    t.textContent = 'Đang tải ảnh lên...';
    pp.textContent = f.name || '';
    ok.textContent = '';
    try {
      XKT.nb.anh = await vxUpAnh(f);
      body.querySelector('#nbAnhO').classList.add('xong');
      t.textContent = 'Đã có ảnh';
      pp.textContent = 'Chạm để đổi ảnh khác';
      ok.innerHTML = '<img class="vfanh" alt="Ảnh phiếu" src="' + h(XKT.nb.anh) + '">';
    } catch (e) {
      t.textContent = 'Không tải được ảnh';
      pp.textContent = (e && e.message) || String(e);
    }
  };

  body.querySelector('#nbLuu').onclick = async function () {
    XKT.nb.kho = eKho.value; XKT.nb.mucDich = eMd.value;
    XKT.nb.boPhan = eBp.value; XKT.nb.ghiChu = eGc.value;
    var thieu = null;
    var to = function (el, co) {
      if (!el) return;
      el.classList.toggle('thieu', !!co);
      if (co && !thieu) thieu = el;
    };
    to(eKho, !XKT.nb.kho);
    to(eMd, !XKT.nb.mucDich);
    to(eBp, !XKT.nb.boPhan);
    if (thieu) {
      try { thieu.scrollIntoView({ block: 'center', behavior: 'smooth' }); } catch (e) { }
      if (!XKT.nb.kho) toast('Chưa chọn kho xuất.');
      else if (!XKT.nb.mucDich) toast('Chưa chọn mục đích xuất dùng.');
      else toast('Chưa chọn bộ phận chịu chi phí.');
      return;
    }
    if (!XKT.nb.gio.length) { toast('Chưa có món nào.'); return; }
    this.disabled = true;
    try {
      var r = await api('vagabond.xuat_noi_bo.luu', {
        kho: XKT.nb.kho, muc_dich: XKT.nb.mucDich, bo_phan_chiu: XKT.nb.boPhan,
        ghi_chu: XKT.nb.ghiChu, anh: XKT.nb.anh,
        dong: JSON.stringify(XKT.nb.gio.map(function (d) { return { ma: d.ma, sl: d.sl }; }))
      });
      XKT.nb.gio = []; XKT.nb.anh = ''; XKT.nb.ghiChu = ''; XKT.nb.tab = 'cho';
      toast('Đã lưu ' + r.name + ', phiếu chờ quản lý ghi sổ.');
      go(function () { scrXkNbView(r.name); }, true);
    } catch (e) {
      this.disabled = false;
      toast(errMsg(e) || 'Không lưu được phiếu.');
    }
  };
}

async function scrXkNbView(name) {
  vgbCss();
  frame('Phiếu xuất dùng nội bộ', '<div class="emp"><div class="e1">⏳</div></div>');
  var d = await api('vagabond.xuat_noi_bo.chi_tiet', { name: name });
  var rows = '';
  for (var i = 0; i < d.dong.length; i++) {
    var x = d.dong[i];
    rows += '<div class="vxr"><div class="t"><b>' + h(x.ten || x.ma) + '</b>' +
      '<i>' + h(x.ma) + (x.tien ? ' · ' + vxSo(x.tien) + 'đ' : '') + '</i></div>' +
      '<span style="font-weight:700">' + vxSo(x.sl) + ' ' + h(x.dvt || '') + '</span></div>';
  }
  var nut = '';
  if (d.docstatus === 0 && !d.vgb_huy) {
    if (d.duoc_duyet) nut += '<button class="vxb" id="nbGhi">Ghi sổ phiếu này</button>';
    if (d.la_cua_toi || d.duoc_duyet) nut += '<button class="vxb o" id="nbBo">🚫 Bỏ phiếu này</button>';
    if (!d.duoc_duyet) {
      nut += '<div style="font-size:12px;color:#98a2b3;text-align:center;margin-top:10px">' +
        'Phiếu đang chờ quản lý kho ghi sổ.</div>';
    }
  }
  var body = frame('Phiếu xuất dùng nội bộ',
    '<div class="vxf">' +
    '<div class="vxr"><div class="t"><b>' + h(d.name) + '</b>' +
    '<i>' + h(d.ngay) + ' · ' + h(d.nguoi_tao) + '</i></div>' +
    '<span class="vxtag ' + (d.docstatus === 0 ? 'c' : 'd') + '">' + h(d.trang_thai) + '</span></div>' +
    '<div class="vxl">Kho xuất</div>' +
    '<div class="vxr"><div class="t"><b>' + h(d.kho_xuat || '') + '</b></div></div>' +
    '<div class="vxl">Mục đích</div>' +
    '<div class="vxr"><div class="t"><b>' + h(d.ten_muc_dich || d.muc_dich) + '</b></div></div>' +
    '<div class="vxl">Bộ phận chịu chi phí</div>' +
    '<div class="vxr"><div class="t"><b>' + h(d.bo_phan || 'chưa ghi') + '</b></div></div>' +
    (d.ghi_chu ? '<div class="vxl">Ghi chú</div><div class="vxr"><div class="t"><b>' +
      h(d.ghi_chu) + '</b></div></div>' : '') +
    (d.anh ? '<div class="vxl">Ảnh</div><img src="' + h(d.anh) +
      '" style="width:100%;border-radius:12px;display:block;margin-top:6px">' : '') +
    '<div class="vxl">Hàng trong phiếu (' + d.dong.length + ' món)</div>' + rows +
    (d.tong_tien ? '<div style="text-align:right;font-weight:700;margin-top:8px">Giá trị: ' +
      vxSo(d.tong_tien) + 'đ</div>' : '') +
    nut + '</div>');

  var g = body.querySelector('#nbGhi');
  if (g) g.onclick = async function () {
    if (!await xacNhan('Ghi sổ phiếu ' + d.name + '?\n\nTồn kho sẽ trừ thật và ' +
      'không hoàn lại được từ app.', 'Ghi sổ', 'Ghi sổ')) return;
    busy(true);
    try {
      await api('vagabond.xuat_noi_bo.ghi_so', { name: d.name });
      busy(false); toast('Đã ghi sổ ' + d.name);
      go(function () { scrXkNbView(d.name); }, true);
    } catch (e) { busy(false); baoTin(errMsg(e) || 'Không ghi sổ được'); }
  };
  var bo = body.querySelector('#nbBo');
  if (bo) bo.onclick = async function () {
    if (!await xacNhan('Bỏ phiếu ' + d.name + '?\n\nPhiếu vẫn nằm nguyên trong ' +
      'hệ thống, chỉ không ghi sổ được nữa.', 'Bỏ phiếu', 'Bỏ')) return;
    busy(true);
    try {
      await api('vagabond.xuat_noi_bo.bo_phieu', { name: d.name, ly_do: 'Bỏ phiếu nháp sai' });
      busy(false); toast('Đã bỏ phiếu ' + d.name);
      go(scrXkNbList, true);
    } catch (e) { busy(false); baoTin(errMsg(e) || 'Không bỏ được phiếu'); }
  };
}

/* ==================================================================
   2. XUAT TRA LAI NHA CUNG CAP
   ================================================================== */

async function xktBootTra() {
  if (!XKT.bootTra) XKT.bootTra = await api('vagabond.tra_ncc.khoi_dong');
  return XKT.bootTra;
}

async function scrXkTraList() {
  vgbCss();
  frame('Xuất trả nhà cung cấp', '<div class="emp"><div class="e1">⏳</div></div>');
  await xktBootTra();
  var ds = [], loiDs = '';
  try { ds = (await api('vagabond.tra_ncc.ds_phieu', { gioi_han: 40 })) || []; }
  catch (e) { loiDs = errMsg(e) || 'Không đọc được danh sách phiếu.'; }
  var s = '';
  for (var i = 0; i < ds.length; i++) {
    var x = ds[i];
    x.tieu_de = x.name + ' · ' + (x.supplier_name || x.supplier || '');
    s += vxTheRow(x, '<span class="vxtag ' + (x.docstatus === 0 ? 'c' : 'd') + '">' +
      h(x.trang_thai) + '</span>');
  }
  if (loiDs) s = xktLoiHtml(loiDs);
  else if (!ds.length) {
    s = '<div style="text-align:center;color:#98a2b3;padding:40px 20px;font-size:14px">' +
      'Chưa có phiếu trả hàng nào.<br>Bấm nút + để lập phiếu.</div>';
  }
  var body = frame('Xuất trả nhà cung cấp',
    '<div style="font-size:11.5px;color:#98a2b3;padding:0 2px 8px;line-height:1.6">' +
    'Phiếu này vừa <b>giảm tồn kho</b> vừa <b>giảm công nợ phải trả</b>, nên ' +
    'kế toán không phải gõ bút toán tay để nắn lại.</div>' +
    '<div class="vxf" id="vxLst">' + s + '</div>', {
    fab: 1,
    onFab: function () {
      XKT.tra.ncc = ''; XKT.tra.phieu = ''; XKT.tra.lyDo = '';
      XKT.tra.ghiChu = ''; XKT.tra.anh = ''; XKT.tra.dong = [];
      go(scrXkTraNew);
    }
  });
  body.onclick = function (e) {
    var r = e.target.closest('[data-xem]');
    if (r) { var n = r.dataset.xem; go(function () { scrXkTraView(n); }); }
  };
}

async function scrXkTraNew() {
  vgbCss();
  frame('Lập phiếu trả hàng', '<div class="emp"><div class="e1">⏳</div></div>');
  var b = await xktBootTra();
  if (!b.ncc.length) {
    return frame('Lập phiếu trả hàng',
      '<div class="emp"><div class="e1">🏭</div><div>Không có nhà cung cấp nào ' +
      'có phiếu nhập trong 90 ngày qua, nên chưa trả hàng theo phiếu nào được.</div></div>');
  }
  var nc = '<option value="">-- chọn nhà cung cấp --</option>';
  for (var i = 0; i < b.ncc.length; i++) {
    nc += '<option value="' + h(b.ncc[i].ma) + '"' + (b.ncc[i].ma === XKT.tra.ncc ? ' selected' : '') +
      '>' + h(b.ncc[i].ten) + '</option>';
  }
  var ly = '<option value="">-- chọn lý do --</option>';
  for (var j = 0; j < b.ly_do.length; j++) {
    ly += '<option value="' + h(b.ly_do[j]) + '"' + (b.ly_do[j] === XKT.tra.lyDo ? ' selected' : '') +
      '>' + h(b.ly_do[j]) + '</option>';
  }

  var body = frame('Lập phiếu trả hàng',
    '<div class="vxf">' +

    '<div class="vf">' +
    '<div class="vfh"><span class="ic">🏭</span><b>Nhà cung cấp</b>' +
    '<span class="bat">Bắt buộc</span></div>' +
    '<select class="vfs" id="trNcc">' + nc + '</select>' +
    '</div>' +

    /* Phai chon phieu nhap goc, khong phai de cho kho. Tra hang ma khong
       neo vao phieu nao thi ERPNext khong biet hoan gia nao: mot ma bot
       mua thang truoc 80 nghin mot ky, thang nay 95 nghin. */
    '<div class="vf">' +
    '<div class="vfh"><span class="ic">📄</span><b>Phiếu nhập gốc</b>' +
    '<span class="bat">Bắt buộc</span></div>' +
    '<select class="vfs" id="trPhieu"><option value="">-- chọn nhà cung cấp trước --</option></select>' +
    '<div class="vfm">Neo vào phiếu gốc thì máy hoàn đúng giá đã nhập của lô đó.</div>' +
    '</div>' +

    '<div class="vf">' +
    '<div class="vfh"><span class="ic">❓</span><b>Lý do trả</b>' +
    '<span class="bat">Bắt buộc</span></div>' +
    '<select class="vfs" id="trLy">' + ly + '</select>' +
    '</div>' +

    '<div class="vf">' +
    '<div class="vfh"><span class="ic">📦</span><b>Hàng trả lại</b>' +
    '<span class="bat">Bắt buộc</span></div>' +
    '<div id="trDong"><div style="text-align:center;color:#98a2b3;padding:22px 0;font-size:14px">' +
    'Chọn phiếu nhập gốc để máy hiện các món trả được.</div></div>' +
    '</div>' +

    '<div class="vf">' +
    '<div class="vfh"><span class="ic">📷</span><b>Ảnh hàng lỗi (không bắt buộc)</b></div>' +
    '<label class="vfa" id="trAnhO">' +
    '<input type="file" accept="image/*" id="trAnh">' +
    '<div class="i">📷</div>' +
    '<div class="t" id="trAnhT">Chụp hoặc chọn ảnh hàng lỗi</div>' +
    '<div class="p" id="trAnhP">Ảnh này để đối chiếu với nhà cung cấp</div>' +
    '</label><div id="trAnhOk"></div>' +
    '</div>' +

    '<div class="vf">' +
    '<div class="vfh"><span class="ic">📝</span><b>Ghi chú</b></div>' +
    '<input class="vfi" id="trGc" placeholder="Ví dụ: 2 bịch bột bị mốc góc" value="' +
    h(XKT.tra.ghiChu) + '">' +
    '</div>' +

    '<button class="vxb" id="trLuu">Lưu và ghi sổ phiếu trả</button>' +
    '<div style="font-size:12px;color:#98a2b3;text-align:center;margin-top:10px">' +
    'Phiếu ghi sổ ngay: tồn giảm và công nợ phải trả giảm cùng lúc.</div></div>');

  var eNcc = body.querySelector('#trNcc');
  var ePhieu = body.querySelector('#trPhieu');
  var eLy = body.querySelector('#trLy');
  var eGc = body.querySelector('#trGc');

  async function napPhieu(ncc) {
    ePhieu.innerHTML = '<option value="">-- đang tải --</option>';
    var ds = [];
    try { ds = (await api('vagabond.tra_ncc.phieu_cua_ncc', { ncc: ncc })) || []; } catch (e) { }
    if (!ds.length) {
      ePhieu.innerHTML = '<option value="">-- không có phiếu nhập nào --</option>';
      return;
    }
    var s = '<option value="">-- chọn phiếu nhập --</option>';
    for (var i = 0; i < ds.length; i++) {
      s += '<option value="' + h(ds[i].name) + '">' + h(ds[i].name) + ' · ' +
        h(ds[i].posting_date) + ' · ' + ds[i].so_dong + ' món</option>';
    }
    ePhieu.innerHTML = s;
  }

  function veDong() {
    var o = body.querySelector('#trDong');
    if (!XKT.tra.dong.length) {
      o.innerHTML = '<div style="text-align:center;color:#98a2b3;padding:22px 0;font-size:14px">' +
        'Phiếu này không còn món nào trả được.</div>';
      return;
    }
    var s = '';
    for (var i = 0; i < XKT.tra.dong.length; i++) {
      var d = XKT.tra.dong[i];
      s += '<div class="vxr"><div class="t"><b>' + h(d.ten || d.ma) + '</b>' +
        '<i>' + h(d.ma) + ' · đã nhận ' + vxSo(d.da_nhan) +
        (d.da_tra ? ', đã trả ' + vxSo(d.da_tra) : '') +
        ' · còn trả được ' + vxSo(d.con) + ' ' + h(d.dvt || '') + '</i></div>' +
        '<input class="vxq" type="number" inputmode="decimal" min="0" max="' + d.con +
        '" step="any" value="' + (d.sl || 0) + '" data-tsl="' + i + '"></div>';
    }
    o.innerHTML = s;
    var qs = o.querySelectorAll('[data-tsl]');
    for (var j = 0; j < qs.length; j++) {
      qs[j].onchange = function () {
        var k = +this.dataset.tsl;
        var v = Number(this.value || 0);
        if (v > XKT.tra.dong[k].con) {
          v = XKT.tra.dong[k].con;
          this.value = v;
          toast('Chỉ còn ' + vxSo(v) + ' trả được cho món này.');
        }
        if (v < 0) { v = 0; this.value = 0; }
        XKT.tra.dong[k].sl = v;
      };
    }
  }

  eNcc.onchange = async function () {
    XKT.tra.ncc = this.value;
    XKT.tra.phieu = ''; XKT.tra.dong = [];
    this.classList.remove('thieu');
    veDong();
    if (XKT.tra.ncc) await napPhieu(XKT.tra.ncc);
    else ePhieu.innerHTML = '<option value="">-- chọn nhà cung cấp trước --</option>';
  };
  ePhieu.onchange = async function () {
    XKT.tra.phieu = this.value;
    this.classList.remove('thieu');
    XKT.tra.dong = [];
    if (!XKT.tra.phieu) { veDong(); return; }
    busy(true);
    try {
      var kq = await api('vagabond.tra_ncc.dong_cua_phieu', { phieu: XKT.tra.phieu });
      /* Chi giu dong CON tra duoc. Bay ca dong con 0 chi lam nguoi ta go
         vao roi bi may tu chuyen ve 0. */
      XKT.tra.dong = (kq.dong || []).filter(function (d) { return d.con > 0; })
        .map(function (d) { d.sl = 0; return d; });
      busy(false);
    } catch (e) { busy(false); toast(errMsg(e) || 'Không đọc được phiếu nhập.'); }
    veDong();
  };
  eLy.onchange = function () { XKT.tra.lyDo = this.value; this.classList.remove('thieu'); };
  eGc.onchange = function () { XKT.tra.ghiChu = this.value; };

  body.querySelector('#trAnh').onchange = async function () {
    var f = this.files && this.files[0];
    if (!f) return;
    var t = body.querySelector('#trAnhT');
    var pp = body.querySelector('#trAnhP');
    var ok = body.querySelector('#trAnhOk');
    t.textContent = 'Đang tải ảnh lên...';
    pp.textContent = f.name || '';
    try {
      XKT.tra.anh = await vxUpAnh(f);
      body.querySelector('#trAnhO').classList.add('xong');
      t.textContent = 'Đã có ảnh hàng lỗi';
      pp.textContent = 'Chạm để đổi ảnh khác';
      ok.innerHTML = '<img class="vfanh" alt="Ảnh hàng lỗi" src="' + h(XKT.tra.anh) + '">';
    } catch (e) {
      t.textContent = 'Không tải được ảnh';
      pp.textContent = (e && e.message) || String(e);
    }
  };

  body.querySelector('#trLuu').onclick = async function () {
    XKT.tra.lyDo = eLy.value; XKT.tra.ghiChu = eGc.value;
    var thieu = null;
    var to = function (el, co) {
      if (!el) return;
      el.classList.toggle('thieu', !!co);
      if (co && !thieu) thieu = el;
    };
    to(eNcc, !XKT.tra.ncc);
    to(ePhieu, !XKT.tra.phieu);
    to(eLy, !XKT.tra.lyDo);
    if (thieu) {
      try { thieu.scrollIntoView({ block: 'center', behavior: 'smooth' }); } catch (e) { }
      toast(!XKT.tra.ncc ? 'Chưa chọn nhà cung cấp.'
        : (!XKT.tra.phieu ? 'Chưa chọn phiếu nhập gốc.' : 'Chưa chọn lý do trả.'));
      return;
    }
    var co = XKT.tra.dong.filter(function (d) { return Number(d.sl) > 0; });
    if (!co.length) { toast('Chưa nhập số lượng trả cho món nào.'); return; }
    if (!await xacNhan('Trả ' + co.length + ' món về ' + h(XKT.tra.tenNcc || XKT.tra.ncc) +
      '?\n\nPhiếu ghi sổ ngay: tồn giảm và công nợ phải trả giảm cùng lúc.',
      'Ghi sổ phiếu trả', 'Ghi sổ')) return;
    this.disabled = true;
    try {
      var r = await api('vagabond.tra_ncc.luu', {
        phieu: XKT.tra.phieu, ly_do: XKT.tra.lyDo, ghi_chu: XKT.tra.ghiChu, anh: XKT.tra.anh,
        dong: JSON.stringify(co.map(function (d) { return { ma: d.ma, sl: Number(d.sl) }; }))
      });
      XKT.tra.dong = []; XKT.tra.anh = ''; XKT.tra.ghiChu = '';
      toast('Đã ghi sổ phiếu trả ' + r.name);
      go(function () { scrXkTraView(r.name); }, true);
    } catch (e) {
      this.disabled = false;
      baoTin(errMsg(e) || 'Không ghi sổ được phiếu trả.');
    }
  };
}

async function scrXkTraView(name) {
  vgbCss();
  frame('Phiếu trả hàng', '<div class="emp"><div class="e1">⏳</div></div>');
  var d = await api('vagabond.tra_ncc.chi_tiet', { name: name });
  var rows = '';
  for (var i = 0; i < d.dong.length; i++) {
    var x = d.dong[i];
    rows += '<div class="vxr"><div class="t"><b>' + h(x.ten || x.ma) + '</b>' +
      '<i>' + h(x.ma) + (x.tien ? ' · ' + vxSo(x.tien) + 'đ' : '') + '</i></div>' +
      '<span style="font-weight:700">' + vxSo(x.sl) + ' ' + h(x.dvt || '') + '</span></div>';
  }
  frame('Phiếu trả hàng',
    '<div class="vxf">' +
    '<div class="vxr"><div class="t"><b>' + h(d.name) + '</b>' +
    '<i>' + h(d.ngay) + ' · ' + h(d.nguoi_tao) + '</i></div>' +
    '<span class="vxtag ' + (d.docstatus === 0 ? 'c' : 'd') + '">' + h(d.trang_thai) + '</span></div>' +
    '<div class="vxl">Nhà cung cấp</div>' +
    '<div class="vxr"><div class="t"><b>' + h(d.ten_ncc || d.ncc) + '</b></div></div>' +
    '<div class="vxl">Trả theo phiếu nhập</div>' +
    '<div class="vxr"><div class="t"><b>' + h(d.phieu_goc || 'chưa neo') + '</b></div></div>' +
    '<div class="vxl">Lý do trả</div>' +
    '<div class="vxr"><div class="t"><b>' + h(d.ly_do || 'chưa ghi') + '</b></div></div>' +
    (d.ghi_chu ? '<div class="vxl">Ghi chú</div><div class="vxr"><div class="t"><b>' +
      h(d.ghi_chu) + '</b></div></div>' : '') +
    (d.anh ? '<div class="vxl">Ảnh hàng lỗi</div><img src="' + h(d.anh) +
      '" style="width:100%;border-radius:12px;display:block;margin-top:6px">' : '') +
    '<div class="vxl">Hàng trả lại (' + d.dong.length + ' món)</div>' + rows +
    (d.tong_tien ? '<div style="text-align:right;font-weight:700;margin-top:8px">Giá trị: ' +
      vxSo(d.tong_tien) + 'đ</div>' : '') +
    '<div style="font-size:12px;color:#98a2b3;text-align:center;margin-top:14px">' +
    'Công nợ phải trả nhà cung cấp đã giảm đúng số này.</div></div>');
}

/* ==================================================================
   3. XUAT BAN SI
   ================================================================== */

async function xktBootSi() {
  if (!XKT.bootSi) XKT.bootSi = await api('vagabond.xuat_ban.khoi_dong');
  return XKT.bootSi;
}

async function scrXkSiList() {
  vgbCss();
  frame('Xuất bán sỉ', '<div class="emp"><div class="e1">⏳</div></div>');
  await xktBootSi();
  var ds = [], loiDs = '';
  try { ds = (await api('vagabond.xuat_ban.ds_phieu', { gioi_han: 40 })) || []; }
  catch (e) { loiDs = errMsg(e) || 'Không đọc được danh sách phiếu.'; }
  var s = '';
  for (var i = 0; i < ds.length; i++) {
    var x = ds[i];
    x.tieu_de = x.name + ' · ' + (x.customer_name || x.customer || '');
    s += vxTheRow(x, '<span class="vxtag ' + (x.docstatus === 0 ? 'c' : 'd') + '">' +
      h(x.trang_thai) + '</span>');
  }
  if (loiDs) s = xktLoiHtml(loiDs);
  else if (!ds.length) {
    s = '<div style="text-align:center;color:#98a2b3;padding:40px 20px;font-size:14px">' +
      'Chưa có phiếu giao hàng nào trong 60 ngày qua.<br>Bấm nút + để lập phiếu.</div>';
  }
  var body = frame('Xuất bán sỉ',
    '<div style="font-size:11.5px;color:#98a2b3;padding:0 2px 8px;line-height:1.6">' +
    'Phiếu giao hàng cho khách sỉ và khách doanh nghiệp. Phiếu này <b>trừ kho ' +
    'thật</b> và ghi giá vốn.</div>' +
    '<div class="vxf" id="vxLst">' + s + '</div>', {
    fab: 1,
    onFab: function () {
      XKT.si.gio = []; XKT.si.khach = ''; XKT.si.tenKhach = '';
      XKT.si.nguoiNhan = ''; XKT.si.ghiChu = '';
      go(scrXkSiNew);
    }
  });
  body.onclick = function (e) {
    var r = e.target.closest('[data-xem]');
    if (r) { var n = r.dataset.xem; go(function () { scrXkSiView(n); }); }
  };
}

async function scrXkSiNew() {
  vgbCss();
  if (!XKT.si.kho) { try { XKT.si.kho = localStorage.getItem('vgbKhoXuat') || ''; } catch (e) { } }
  frame('Lập phiếu giao hàng', '<div class="emp"><div class="e1">⏳</div></div>');
  var b = await xktBootSi();

  var body = frame('Lập phiếu giao hàng',
    '<div class="vxf">' +

    /* Canh bao nay den tu may chu chu khong go cung o day: co ca kiem chot
       rang cau nay con ton tai. Bo no di la nguoi lap khong con biet vi sao
       ton kho cua don si di khac ban le tai quay. */
    '<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:10px;' +
    'padding:11px 13px;margin-bottom:12px;font-size:12.5px;color:#92400e;line-height:1.6">' +
    '⚠️ ' + h(b.canh_bao || '') + '</div>' +

    '<div class="vf">' +
    '<div class="vfh"><span class="ic">👤</span><b>Khách hàng</b>' +
    '<span class="bat">Bắt buộc</span></div>' +
    '<input class="vfi" id="siTim" placeholder="Gõ tên khách để tìm" ' +
    'value="' + h(XKT.si.tenKhach) + '">' +
    '<div id="siKq" style="margin-top:6px"></div>' +
    '</div>' +

    '<div class="vf">' +
    '<div class="vfh"><span class="ic">🏬</span><b>Kho xuất</b>' +
    '<span class="bat">Bắt buộc</span></div>' +
    '<select class="vfs" id="siKho">' + vxKhoXuatOpt(b.kho, XKT.si.kho) + '</select>' +
    '</div>' +

    '<div class="vf">' +
    '<div class="vfh"><span class="ic">📦</span><b>Hàng giao</b>' +
    '<span class="bat">Bắt buộc</span></div>' +
    '<div id="vxDong">' + xktDongHtml(XKT.si.gio) + '</div>' +
    '<button class="vxb o" id="siThem" style="margin-top:8px">+ Thêm hàng</button>' +
    '</div>' +

    '<div class="vf">' +
    '<div class="vfh"><span class="ic">✍️</span><b>Người nhận hàng</b></div>' +
    '<input class="vfi" id="siNn" placeholder="Tên người ký nhận bên khách" value="' +
    h(XKT.si.nguoiNhan) + '">' +
    '<div class="vfm">Ghi tên để sau này còn đối chiếu khi có tranh chấp.</div>' +
    '</div>' +

    '<div class="vf">' +
    '<div class="vfh"><span class="ic">📝</span><b>Ghi chú</b></div>' +
    '<input class="vfi" id="siGc" placeholder="Ví dụ: giao đợt 1 của hợp đồng tháng 9" value="' +
    h(XKT.si.ghiChu) + '">' +
    '</div>' +

    '<button class="vxb" id="siLuu">Lưu và ghi sổ phiếu giao</button>' +
    '<div style="font-size:12px;color:#98a2b3;text-align:center;margin-top:10px">' +
    'Phiếu ghi sổ ngay: hàng lên xe rồi thì chờ duyệt là sai tồn trong lúc chờ.</div></div>');

  var eTim = body.querySelector('#siTim');
  var eKho = body.querySelector('#siKho');
  var eNn = body.querySelector('#siNn');
  var eGc = body.querySelector('#siGc');
  var eKq = body.querySelector('#siKq');

  function veKq(ds) {
    if (!ds.length) { eKq.innerHTML = ''; return; }
    var s = '';
    for (var i = 0; i < ds.length; i++) {
      s += '<div class="vxr" data-kh="' + h(ds[i].name) + '" data-tk="' +
        h(ds[i].customer_name || ds[i].name) + '"><div class="t"><b>' +
        h(ds[i].customer_name || ds[i].name) + '</b><i>' + h(ds[i].name) + '</i></div></div>';
    }
    eKq.innerHTML = s;
    var rs = eKq.querySelectorAll('[data-kh]');
    for (var j = 0; j < rs.length; j++) {
      rs[j].onclick = function () {
        XKT.si.khach = this.dataset.kh;
        XKT.si.tenKhach = this.dataset.tk;
        eTim.value = XKT.si.tenKhach;
        eTim.classList.remove('thieu');
        eKq.innerHTML = '<div style="font-size:12px;color:#16a34a;padding:4px 2px">' +
          '✓ Đã chọn ' + h(XKT.si.tenKhach) + '</div>';
      };
    }
  }

  var hen = null;
  eTim.oninput = function () {
    /* Cho go xong hang cai roi moi hoi may chu. Hoi tung phim la moi chu
       mot loi goi, va o quay song ba man hinh thi no thanh nghen that. */
    XKT.si.khach = '';
    clearTimeout(hen);
    var tu = this.value;
    hen = setTimeout(async function () {
      try { veKq((await api('vagabond.xuat_ban.tim_khach', { tu_khoa: tu })) || []); }
      catch (e) { eKq.innerHTML = ''; }
    }, 350);
  };

  eKho.onchange = function () {
    if (XKT.si.kho && this.value !== XKT.si.kho && XKT.si.gio.length) {
      XKT.si.gio = [];
      toast('Đổi kho nên phải chọn lại hàng.');
    }
    XKT.si.kho = this.value;
    this.classList.remove('thieu');
    try { localStorage.setItem('vgbKhoXuat', XKT.si.kho); } catch (e) { }
    xktNoiDong(body, XKT.si.gio);
  };
  eNn.onchange = function () { XKT.si.nguoiNhan = this.value; };
  eGc.onchange = function () { XKT.si.ghiChu = this.value; };
  xktNoiSuKien(body, XKT.si.gio);

  body.querySelector('#siThem').onclick = function () {
    XKT.si.kho = eKho.value; XKT.si.nguoiNhan = eNn.value; XKT.si.ghiChu = eGc.value;
    if (!XKT.si.kho) { toast('Chọn kho xuất trước đã.'); return; }
    var kho = XKT.si.kho;
    XK.gio = XKT.si.gio.slice();
    go(function () { scrXkChonHang(kho, function () { XKT.si.gio = XK.gio.slice(); return scrXkSiNew(); }); });
  };

  body.querySelector('#siLuu').onclick = async function () {
    XKT.si.kho = eKho.value; XKT.si.nguoiNhan = eNn.value; XKT.si.ghiChu = eGc.value;
    var thieu = null;
    var to = function (el, co) {
      if (!el) return;
      el.classList.toggle('thieu', !!co);
      if (co && !thieu) thieu = el;
    };
    to(eTim, !XKT.si.khach);
    to(eKho, !XKT.si.kho);
    if (thieu) {
      try { thieu.scrollIntoView({ block: 'center', behavior: 'smooth' }); } catch (e) { }
      toast(!XKT.si.khach ? 'Chưa chọn khách hàng trong danh sách gợi ý.' : 'Chưa chọn kho xuất.');
      return;
    }
    if (!XKT.si.gio.length) { toast('Chưa có món nào.'); return; }
    if (!await xacNhan('Giao ' + XKT.si.gio.length + ' món cho ' + XKT.si.tenKhach +
      '?\n\nPhiếu ghi sổ ngay, tồn kho trừ thật và ghi giá vốn.',
      'Ghi sổ phiếu giao', 'Ghi sổ')) return;
    this.disabled = true;
    try {
      var r = await api('vagabond.xuat_ban.luu', {
        khach: XKT.si.khach, kho: XKT.si.kho, nguoi_nhan: XKT.si.nguoiNhan,
        ghi_chu: XKT.si.ghiChu,
        dong: JSON.stringify(XKT.si.gio.map(function (d) { return { ma: d.ma, sl: d.sl }; }))
      });
      XKT.si.gio = []; XKT.si.ghiChu = '';
      toast('Đã ghi sổ phiếu giao ' + r.name);
      go(function () { scrXkSiView(r.name); }, true);
    } catch (e) {
      this.disabled = false;
      baoTin(errMsg(e) || 'Không ghi sổ được phiếu giao.');
    }
  };
}

async function scrXkSiView(name) {
  vgbCss();
  frame('Phiếu giao hàng', '<div class="emp"><div class="e1">⏳</div></div>');
  var d = await api('vagabond.xuat_ban.chi_tiet', { name: name });
  var rows = '';
  for (var i = 0; i < d.dong.length; i++) {
    var x = d.dong[i];
    rows += '<div class="vxr"><div class="t"><b>' + h(x.ten || x.ma) + '</b>' +
      '<i>' + h(x.ma) + (x.tien ? ' · ' + vxSo(x.tien) + 'đ' : '') + '</i></div>' +
      '<span style="font-weight:700">' + vxSo(x.sl) + ' ' + h(x.dvt || '') + '</span></div>';
  }
  frame('Phiếu giao hàng',
    '<div class="vxf">' +
    '<div class="vxr"><div class="t"><b>' + h(d.name) + '</b>' +
    '<i>' + h(d.ngay) + ' · ' + h(d.nguoi_tao) + '</i></div>' +
    '<span class="vxtag ' + (d.docstatus === 0 ? 'c' : 'd') + '">' + h(d.trang_thai) + '</span></div>' +
    '<div class="vxl">Khách hàng</div>' +
    '<div class="vxr"><div class="t"><b>' + h(d.ten_khach || d.khach) + '</b></div></div>' +
    '<div class="vxl">Kho xuất</div>' +
    '<div class="vxr"><div class="t"><b>' + h(d.kho || '') + '</b></div></div>' +
    (d.nguoi_nhan ? '<div class="vxl">Người nhận</div><div class="vxr"><div class="t"><b>' +
      h(d.nguoi_nhan) + '</b></div></div>' : '') +
    (d.ghi_chu ? '<div class="vxl">Ghi chú</div><div class="vxr"><div class="t"><b>' +
      h(d.ghi_chu) + '</b></div></div>' : '') +
    '<div class="vxl">Hàng đã giao (' + d.dong.length + ' món)</div>' + rows +
    (d.tong_tien ? '<div style="text-align:right;font-weight:700;margin-top:8px">Giá trị: ' +
      vxSo(d.tong_tien) + 'đ</div>' : '') + '</div>');
}

/* ==================================================================
   Ho tro chung cho ba man tren
   ================================================================== */

/* Khoi bao loi thay cho danh sach. Loi may chu phai NHIN THAY duoc, khong
   duoc hoa trang thanh "chua co phieu nao". */
function xktLoiHtml(loi) {
  return '<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:10px;' +
    'padding:14px;margin:8px 0;font-size:13px;color:#991b1b;line-height:1.6">' +
    '<b>Không đọc được danh sách phiếu.</b><br>' + h(loi) +
    '<br><span style="color:#7f1d1d;font-size:12px">Chụp màn này gửi anh Việt giúp.</span></div>';
}

/* Ban sao cua vxDongHtml nhung nhan gio TRUYEN VAO thay vi doc XK.gio.

   Vi sao khong sua thang vxDongHtml cho no nhan tham so: ham do dang duoc
   Xuat huy va Dieu chuyen goi o bon cho, doi chu ky cua no la sua bon cho
   trong mot tep ma phien khac hay dong vao. Chep mot ban 12 dong o day re
   hon nhieu so voi rui ro do. */
function xktDongHtml(gio) {
  if (!gio.length) {
    return '<div style="text-align:center;color:#98a2b3;padding:22px 0;font-size:14px">' +
      'Chưa có món nào. Bấm <b>Thêm hàng</b> ở dưới.</div>';
  }
  var s = '';
  for (var i = 0; i < gio.length; i++) {
    var d = gio[i];
    s += '<div class="vxr"><div class="t"><b>' + h(d.ten || d.ma) + '</b>' +
      '<i>' + h(d.ma) + ' · tồn ' + vxSo(d.ton) + ' ' + h(d.dvt || '') + '</i></div>' +
      '<input class="vxq" type="number" inputmode="decimal" min="0" step="any" ' +
      'value="' + d.sl + '" data-xsl="' + i + '">' +
      '<button class="vxx" data-xbo="' + i + '">&times;</button></div>';
  }
  return s;
}

function xktNoiDong(body, gio) {
  var o = body.querySelector('#vxDong');
  if (o) o.innerHTML = xktDongHtml(gio);
  xktNoiSuKien(body, gio);
}

function xktNoiSuKien(body, gio) {
  var qs = body.querySelectorAll('[data-xsl]');
  for (var i = 0; i < qs.length; i++) {
    qs[i].onchange = function () { gio[+this.dataset.xsl].sl = Number(this.value || 0); };
  }
  var bs = body.querySelectorAll('[data-xbo]');
  for (var j = 0; j < bs.length; j++) {
    bs[j].onclick = function () {
      gio.splice(+this.dataset.xbo, 1);
      xktNoiDong(body, gio);
    };
  }
}

/* ==================================================================
   4. XAC NHAN NHAN HANG DIEU CHUYEN (anh Viet chot phuong an A 02/09/2026)
   ==================================================================

   MAN NAY KHONG DUNG TOI SO KHO. Day la cho de hieu nham nhat, nen noi ro
   ngay tren man hinh chu khong chi trong ma nguon.

   Bam "nhan 8 tren 10" KHONG lam ton kho bep giam di 2. So kho van ghi day
   du 10 nhu phieu dieu chuyen da ghi. Man nay ghi lai MOT LOI KHAI: nguoi
   nhan noi rang ho chi thay 8. Lech do co the do kho xuat soan thieu, mat
   tren duong di, hoac nguoi nhan dem sot - ba nguyen nhan ghi vao ba cho
   khac nhau trong so ke toan, ma may khong biet la cai nao.

   Nen may chi ghi lai roi treo thanh viec cho thu kho doi chieu. Xem doan
   dai o dau vagabond/nhan_dieu_chuyen.py. */

var NDC = { phieu: '', dong: [], ghiChu: '' };

async function scrNhanDcXacNhan(phieu) {
  vgbCss();
  frame('Xác nhận nhận hàng', '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api('vagabond.nhan_dieu_chuyen.dong_de_nhan', { phieu: phieu }); }
  catch (e) {
    return frame('Xác nhận nhận hàng',
      '<div class="emp"><div class="e1">⚠️</div><div>' +
      h(errMsg(e) || 'Không mở được phiếu') + '</div></div>');
  }
  if (d.da_xac_nhan) {
    return frame('Xác nhận nhận hàng',
      '<div class="vxf"><div class="vxr"><div class="t"><b>' + h(d.phieu) + '</b>' +
      '<i>' + h(d.kho_xuat) + ' → ' + h(d.kho_nhan) + '</i></div>' +
      '<span class="vxtag d">' + h(d.da_xac_nhan) + '</span></div>' +
      '<div style="font-size:12.5px;color:#98a2b3;line-height:1.7;margin-top:12px">' +
      'Phiếu này đã được ' + h(d.nhan_boi || 'người khác') + ' xác nhận' +
      (d.nhan_luc ? ' lúc ' + h(d.nhan_luc) : '') + '. Khai sai thì báo thủ kho, ' +
      'đừng xác nhận đè lên.' +
      (d.nhan_ghi_chu ? '<br><br>Ghi chú: ' + h(d.nhan_ghi_chu) : '') + '</div></div>');
  }

  NDC.phieu = d.phieu;
  NDC.dong = (d.dong || []).map(function (x) { return { ma: x.ma, ten: x.ten, dvt: x.dvt, giao: x.giao, nhan: x.giao }; });
  NDC.ghiChu = '';

  function rowsHtml() {
    var s = '';
    for (var i = 0; i < NDC.dong.length; i++) {
      var x = NDC.dong[i];
      var lech = Number(x.giao) - Number(x.nhan);
      s += '<div class="vxr"><div class="t"><b>' + h(x.ten || x.ma) + '</b>' +
        '<i>' + h(x.ma) + ' · kho giao ' + vxSo(x.giao) + ' ' + h(x.dvt || '') +
        (Math.abs(lech) > 0.0001
          ? ' · <b style="color:' + (lech > 0 ? '#b91c1c' : '#b45309') + '">' +
            (lech > 0 ? 'thiếu ' : 'thừa ') + vxSo(Math.abs(lech)) + '</b>'
          : '') + '</i></div>' +
        '<input class="vxq" type="number" inputmode="decimal" min="0" step="any" ' +
        'value="' + x.nhan + '" data-nsl="' + i + '"></div>';
    }
    return s;
  }

  var body = frame('Xác nhận nhận hàng',
    '<div class="vxf">' +
    '<div class="vxr"><div class="t"><b>' + h(d.phieu) + '</b>' +
    '<i>' + h(d.ngay) + ' · ' + h(d.kho_xuat) + ' → ' + h(d.kho_nhan) + '</i></div></div>' +

    /* Cau nay la phan quan trong nhat cua ca man. Bo di la nguoi nhan tuong
       bam vao day thi ton kho tu nan lai, va se khong bao ai nua. */
    '<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;' +
    'padding:11px 13px;margin:12px 0;font-size:12.5px;color:#1e40af;line-height:1.6">' +
    'ℹ️ Màn này <b>không sửa tồn kho</b>. Nó ghi lại số bạn đếm được thật, để ' +
    'thủ kho đối chiếu xem hàng thiếu đi đâu. Sổ kho vẫn giữ nguyên số kho giao.</div>' +

    '<div class="vxl">Số bạn đếm được (máy điền sẵn theo số kho giao)</div>' +
    '<div id="ndcDong">' + rowsHtml() + '</div>' +

    '<div class="vf" style="margin-top:12px">' +
    '<div class="vfh"><span class="ic">📝</span><b>Ghi chú</b></div>' +
    '<input class="vfi" id="ndcGc" placeholder="Ví dụ: thùng bị rách một góc khi nhận">' +
    '</div>' +

    '<button class="vxb" id="ndcGui">Xác nhận đã nhận</button>' +
    '<div style="font-size:12px;color:#98a2b3;text-align:center;margin-top:10px">' +
    'Đúng đủ thì bấm luôn, không phải sửa gì. Chỉ sửa dòng nào thực sự lệch.</div></div>');

  function noi() {
    var qs = body.querySelectorAll('[data-nsl]');
    for (var i = 0; i < qs.length; i++) {
      qs[i].onchange = function () {
        var k = +this.dataset.nsl;
        var v = Number(this.value || 0);
        if (v < 0) { v = 0; this.value = 0; }
        NDC.dong[k].nhan = v;
        var o = body.querySelector('#ndcDong');
        if (o) { o.innerHTML = rowsHtml(); noi(); }
      };
    }
  }
  noi();

  body.querySelector('#ndcGc').onchange = function () { NDC.ghiChu = this.value; };

  body.querySelector('#ndcGui').onclick = async function () {
    var lech = NDC.dong.filter(function (x) {
      return Math.abs(Number(x.giao) - Number(x.nhan)) > 0.0001;
    });
    var cau = lech.length
      ? 'Bạn khai NHẬN THIẾU ở ' + lech.length + ' món.\n\nPhần thiếu sẽ treo thành ' +
        'việc cần làm cho thủ kho đối chiếu. Tồn kho không đổi.'
      : 'Bạn khai ĐÃ NHẬN ĐỦ toàn bộ phiếu này.';
    if (!await xacNhan(cau, 'Xác nhận nhận hàng', 'Xác nhận')) return;
    this.disabled = true;
    try {
      var r = await api('vagabond.nhan_dieu_chuyen.xac_nhan', {
        phieu: NDC.phieu, ghi_chu: NDC.ghiChu,
        dong: JSON.stringify(NDC.dong.map(function (x) { return { ma: x.ma, nhan: x.nhan }; }))
      });
      toast(r.trang_thai + (r.cau_lech ? ': ' + r.cau_lech : ''), 5000);
      go(scrHangVeKho, true);
    } catch (e) {
      this.disabled = false;
      baoTin(errMsg(e) || 'Không xác nhận được.');
    }
  };
}

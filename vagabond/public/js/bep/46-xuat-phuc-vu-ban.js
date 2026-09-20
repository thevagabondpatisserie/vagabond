/* ---------- 5e. Xuat kho phuc vu ban hang ----------

Anh Viet giao 16/09/2026, sau khi do tren site that: trong mot thang, hang
ra khoi Kho D1 va Kho Sales Online chi co dung 18 dong va ca 18 deu la
dieu chuyen sang kho khac. Bao bi, cong cu dung cu, nguyen lieu, ban thanh
pham deu khong co duong ra. Khoang 320 trieu dang treo o hai kho do.

MAN NAY KHONG GIONG CAC MAN XUAT KHAC, VA CO Y KHONG GIONG
-----------------------------------------------------------
Ba man o tep 45 deu la GIO HANG: chon mon, go so luong xuat. Man nay la
BANG DEM: may liet ke san moi ma dang co ton, quay chi go so CON LAI, may
tu ra so da dung.

Anh Viet chon cach nay ngay 16/09/2026, va ly do rat thuc te: khong ai nho
duoc trong tuan da phat ra bao nhieu cai tui. Nhung dem con lai bao nhieu
thi nhin ke la biet, va con so ay khop voi thuc te chu khong khop voi tri
nho cua ai ca.

Nen o day KHONG co nut "Them hang", khong co man chon hang, khong co gio.
Dung nhieu phan cua bo dung chung XKT o tep 45 (the, chip, sheet tim, nut
chinh) nhung dong hang thi rieng.

HAI TAI KHOAN, HIEN THANG RA CHU KHONG BAT DOAN
------------------------------------------------
Bao bi, cong cu dung cu, van phong pham ve chi phi ban hang. Nguyen lieu va
ban thanh pham ve gia von hang ban, vi ly ca phe hay cai ruot banh do co
ban ra that. May chu quyet dinh theo nhom mon, nguoi dung khong chon, nhung
man phai HIEN cho ho thay dong nao ve dau.

BANH THANH PHAM KHONG CO TRONG BANG
------------------------------------
Co y. Banh tru kho theo hoa don ban, khai ca o day nua la tru hai lan. Man
co mot khoi noi ro dieu do chu khong de nguoi ta tu di tim roi tu ket luan
la may hong.
*/

var XPV = {
  st: { kho: '', boPhan: '', ghiChu: '', tim: '', nhan: '', tab: 'cho', nhom: '', ngay: 30 },
  /* con: { ma -> chuoi nguoi dung go }. De rieng khoi danh sach dong de ve
     lai bang khong lam mat nhung o vua go. */
  con: {},
  bang: null,
  bangKho: '',
  boot: null
};

async function xpvBoot() {
  if (!XPV.boot) XPV.boot = await api('vagabond.xuat_phuc_vu_ban.khoi_dong');
  return XPV.boot;
}

/* Boot hong (mat mang, thieu quyen, may chu loi) thi phai HIEN ra chu khong
   de nguoi ta nhin cai dong ho cat mai. Codex bat tren PR #341. Tra ve null
   khi hong, va man da duoc ve loi kem nut thu lai. */
async function xpvBootHoacBaoLoi(tieuDe, veLai) {
  try {
    return await xpvBoot();
  } catch (e) {
    var body = frame(tieuDe, xktLoiHtml(errMsg(e) || 'Không mở được màn này.') +
      '<div style="padding:0 16px"><button class="vxb o" id="xpvThuLai">Thử lại</button></div>');
    var nut = body.querySelector('#xpvThuLai');
    if (nut) nut.onclick = function () { XPV.boot = null; go(veLai, true); };
    return null;
  }
}

/* So da dung cua mot dong. Tra null khi chua go gi.

   Viet rieng mot ham thay vi tinh tai cho o ba noi: dong hang, the tong,
   va luc luu. Ba noi tu tinh lay la ba co hoi lech nhau. */
function xpvDaDung(d) {
  var v = XPV.con[d.ma];
  if (v === undefined || v === null || String(v).trim() === '') return null;
  var n = Number(v);
  if (!isFinite(n)) return null;
  return Math.round((Number(d.ton_so) - n) * 1000) / 1000;
}

function xpvLoiDong(d) {
  var v = XPV.con[d.ma];
  if (v === undefined || v === null || String(v).trim() === '') return '';
  var n = Number(v);
  if (!isFinite(n)) return 'Chưa phải là số';
  if (n < 0) return 'Không thể là số âm';
  if (n > Number(d.ton_so) + 1e-9) return 'Đếm nhiều hơn sổ, việc này đi đường Kiểm kê';
  return '';
}

function xpvCss() {
  xktCss();
  if (document.getElementById('xpvCss')) return;
  var st = document.createElement('style');
  st.id = 'xpvCss';
  st.textContent =
    '.xpvd{display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid #f2f4f7}' +
    '.xpvd:last-child{border-bottom:0}' +
    '.xpvd .t{flex:1;min-width:0}' +
    '.xpvd .t b{display:block;font-size:14px;color:#101828;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}' +
    '.xpvd .t i{display:block;font-style:normal;font-size:12px;color:#98a2b3;margin-top:2px}' +
    '.xpvd .t i.r{color:#d92d20;font-weight:600}' +
    '.xpvo{flex:none;width:94px;text-align:right}' +
    '.xpvo input{width:94px;height:38px;border:1.5px solid #e4e7ec;border-radius:10px;text-align:right;' +
    'padding:0 9px;font-size:15px;font-weight:700;color:#101828;background:#fff}' +
    '.xpvo input.r{border-color:#d92d20;background:#fef3f2}' +
    '.xpvo input.ok{border-color:#12b76a;background:#f6fef9}' +
    '.xpvo .dd{display:block;font-size:11px;color:#12b76a;font-weight:700;margin-top:3px}' +
    '.xpvn{font-size:12px;font-weight:700;color:#475467;background:#f2f4f7;border-radius:8px;' +
    'padding:6px 10px;margin:14px 0 4px}' +
    '.xpvbao{background:#fffaeb;border:1px solid #fedf89;border-radius:12px;padding:12px 14px;' +
    'font-size:13px;color:#b54708;line-height:1.55;margin-top:12px}' +
    '.xpvbao b{color:#93370d}';
  document.head.appendChild(st);
}

/* ================================================================
   1. DANH SACH PHIEU
   ================================================================ */

async function scrXkPvList() {
  xpvCss();
  frame('Xuất kho phục vụ bán hàng', '<div class="emp"><div class="e1">⏳</div></div>');
  var b0 = await xpvBootHoacBaoLoi('Xuất kho phục vụ bán hàng', scrXkPvList);
  if (!b0) return;
  var loiDs = '';
  var ds = [];
  try {
    ds = (await api('vagabond.xuat_phuc_vu_ban.ds_phieu', { gioi_han: 200 })) || [];
  } catch (e) {
    loiDs = errMsg(e) || 'Không đọc được danh sách phiếu.';
  }
  xktManDanhSach({
    tieuDe: 'Xuất kho phục vụ bán hàng',
    st: XPV.st,
    ds: ds,
    loi: loiDs,
    moTa: 'Cuối tuần mỗi điểm bán chốt một phiếu: <b>đếm còn lại bao nhiêu</b>, máy tự ra số đã dùng. Bánh thành phẩm không khai ở đây.',
    tenPhieu: 'phiếu',
    /* Chip loc theo kho, dung tu chinh danh sach: co phieu cua kho nao thi
       moi co chip cua kho do. Codex bat tren PR #341: de [] thi hang chip
       chi con mot cai "Moi kho" bat dong. */
    nhoms: (function () {
      var ra = [];
      var da = {};
      for (var i = 0; i < ds.length; i++) {
        var k = ds[i].from_warehouse || '';
        if (k && !da[k]) { da[k] = 1; ra.push({ k: k, ten: k.replace(/ - [A-Z]+$/, '') }); }
      }
      return ra;
    })(),
    nhomTatCa: 'Mọi kho',
    nhomCua: function (x) { return x.from_warehouse || ''; },
    tienCua: function (x) { return x.total_outgoing_value; },
    timCua: function (x) { return [x.name, x.from_warehouse, x.nguoi_tao, x.remarks].join(' '); },
    timNhac: 'Tìm số phiếu, kho, người lập...',
    rong: 'Chưa có phiếu nào. Bấm nút + để chốt kho tuần này.',
    row: function (x) {
      return xktTheRow(x, x.from_warehouse || x.name,
        [x.name, x.posting_date, x.so_dong ? x.so_dong + ' mã' : '', x.nguoi_tao].filter(Boolean).join(' · '),
        x.total_outgoing_value);
    },
    xem: scrXkPvView,
    onFab: function () {
      XPV.con = {};
      XPV.bang = null;
      XPV.bangKho = '';
      XPV.st.ghiChu = '';
      XPV.st.tim = '';
      XPV.st.nhan = '';
      go(scrXkPvNew);
    }
  });
}

/* ================================================================
   2. BANG DEM
   ================================================================ */

async function scrXkPvNew() {
  xpvCss();
  if (!XPV.st.kho) { try { XPV.st.kho = localStorage.getItem('vgbKhoXuat') || ''; } catch (e) { } }
  frame('Chốt kho điểm bán', '<div class="emp"><div class="e1">⏳</div></div>');
  var b = await xpvBootHoacBaoLoi('Chốt kho điểm bán', scrXkPvNew);
  if (!b) return;
  var st = XPV.st;
  var bpItems = xktBoPhanItems(b.bo_phan);

  async function napBang() {
    if (!st.kho) { XPV.bang = null; XPV.bangKho = ''; return; }
    if (XPV.bangKho === st.kho && XPV.bang) return;
    /* Ghim kho DA HOI truoc khi cho. Codex bat tren PR #344: chon kho A
       roi doi sang B khi A chua ve, cau tra loi cua A ve sau se duoc gan
       cho B, bang dem cua B thanh hang cua A. Cau tra loi nao khong con
       khop kho dang chon thi bo, khong ghi. */
    var khoHoi = st.kho;
    try {
      var r = await api('vagabond.xuat_phuc_vu_ban.bang_dem', { kho: khoHoi });
      if (st.kho !== khoHoi) return;
      XPV.bang = r.dong || [];
      XPV.bangKho = khoHoi;
    } catch (e) {
      if (st.kho !== khoHoi) return;
      XPV.bang = null;
      XPV.bangKho = '';
      toast(errMsg(e) || 'Không đọc được bảng đếm.');
    }
  }

  function dongTrongBang() {
    var ds = XPV.bang || [];
    var q = (st.tim || '').toLowerCase().trim();
    return ds.filter(function (d) {
      if (st.nhan && d.nhan !== st.nhan) return false;
      if (!q) return true;
      return (d.ten + ' ' + d.ma + ' ' + d.nhom).toLowerCase().indexOf(q) >= 0;
    });
  }

  function dongHtml(d) {
    var dd = xpvDaDung(d);
    var loi = xpvLoiDong(d);
    var v = XPV.con[d.ma];
    var lop = loi ? 'r' : (dd > 0 ? 'ok' : '');
    return '<div class="xpvd">' + anhMon(d.anh) +
      '<div class="t"><b>' + h(d.ten) + '</b>' +
      '<i>' + h(d.ma) + ' · sổ ghi ' + vxSo(d.ton_so) + ' ' + h(d.dvt || '') + '</i>' +
      (loi ? '<i class="r">' + h(loi) + '</i>' : '') +
      '</div>' +
      '<div class="xpvo">' +
      '<input type="number" inputmode="decimal" min="0" step="any" class="' + lop + '"' +
      ' data-xpv="' + h(d.ma) + '" placeholder="còn lại"' +
      ' value="' + (v === undefined || v === null ? '' : h(String(v))) + '">' +
      (!loi && dd > 0 ? '<span class="dd">đã dùng ' + vxSo(dd) + '</span>' : '') +
      '</div></div>';
  }

  function bangHtml() {
    if (!st.kho) {
      return '<div style="text-align:center;color:#98a2b3;padding:26px 0;font-size:14px">' +
        'Chọn kho để máy mở bảng đếm.</div>';
    }
    if (XPV.bang === null) {
      return '<div class="emp"><div class="e1">⏳</div></div>';
    }
    var ds = dongTrongBang();
    if (!ds.length) {
      return '<div style="text-align:center;color:#98a2b3;padding:26px 0;font-size:14px">' +
        (XPV.bang.length ? 'Không có mã nào khớp bộ lọc.' : 'Kho này chưa có mã nào trong phạm vi màn.') +
        '</div>';
    }
    var s = '';
    var nhanCu = '';
    for (var i = 0; i < ds.length; i++) {
      if (ds[i].nhan !== nhanCu) {
        nhanCu = ds[i].nhan;
        s += '<div class="xpvn">' + h(nhanCu) + '</div>';
      }
      s += dongHtml(ds[i]);
    }
    return s;
  }

  function demXong() {
    var ds = XPV.bang || [];
    var n = 0;
    var loi = 0;
    for (var i = 0; i < ds.length; i++) {
      if (xpvLoiDong(ds[i])) { loi++; continue; }
      if (xpvDaDung(ds[i]) > 0) n++;
    }
    return { n: n, loi: loi };
  }

  function tomTatHtml() {
    var d = demXong();
    return '<div class="vfm" id="xpvTom" style="margin-top:8px">' +
      (d.loi ? '<b style="color:#d92d20">' + d.loi + ' dòng đang sai, sửa trước khi lưu.</b> ' : '') +
      (d.n ? d.n + ' mã có hàng đi ra.' : 'Chưa mã nào có hàng đi ra.') +
      ' Mã chưa đếm thì bỏ trống, máy không tính.</div>';
  }

  function nhanChips() {
    var ds = [{ k: '', ten: 'Tất cả' }];
    for (var i = 0; i < (b.nhom || []).length; i++) {
      var n = b.nhom[i].nhan;
      var co = false;
      for (var j = 0; j < ds.length; j++) if (ds[j].k === n) co = true;
      if (!co) ds.push({ k: n, ten: n });
    }
    return xktChipNhom(ds, st.nhan, 'data-xpvnhan');
  }

  function ngoaiPhamViHtml() {
    var s = '';
    for (var i = 0; i < (b.ngoai_pham_vi || []).length; i++) {
      var n = b.ngoai_pham_vi[i];
      s += '<div style="margin-top:6px"><b>' + h(n.ten) + ':</b> ' + h(n.vi_sao) + '</div>';
    }
    return '<div class="xpvbao"><b>Có mấy thứ cố ý không nằm trong bảng này</b>' + s + '</div>';
  }

  function ve() {
    var kho = xktKhoHtml('xpvkho', b.kho, st.kho);
    return '<div class="vxf">' +
      kho.html +
      xktOChon('xpvbp', '🏛️', 'Bộ phận chịu chi phí',
        st.boPhan ? { ten: st.boPhan, phu: (bpItems.filter(function (x) { return x.value === st.boPhan; })[0] || {}).phu, ic: '🏛️' } : null,
        { batBuoc: 1, nhac: 'Chạm để tìm bộ phận', mo: 'Cuối tháng đọc báo cáo là biết điểm bán nào dùng bao nhiêu.' }) +
      '<div class="vf" id="xpvbangO">' +
      '<div class="vfh"><span class="ic">🧾</span><b>Đếm còn lại</b><span class="bat">Bắt buộc</span></div>' +
      '<input class="vfi" id="xpvtim" placeholder="Tìm tên hoặc mã hàng..." value="' + h(st.tim) + '" style="margin-bottom:8px">' +
      xktHangChip(nhanChips()) +
      '<div id="xpvBang">' + bangHtml() + '</div>' +
      tomTatHtml() +
      '</div>' +
      '<div class="vf"><div class="vfh"><span class="ic">📝</span><b>Ghi chú</b></div>' +
      '<input class="vfi" id="xpvgc" placeholder="Ví dụ: chốt tuần 38" value="' + h(st.ghiChu) + '"></div>' +
      ngoaiPhamViHtml() +
      xktNutChinh('xpvluu', 'Ghi sổ phiếu xuất', 'Bấm là tồn kho trừ ngay theo số đã dùng (từ 20/09/2026, không chờ kế toán).') +
      '</div>';
  }

  var body = frame('Chốt kho điểm bán', ve());

  function veLaiBang() {
    var o = body.querySelector('#xpvBang');
    if (o) o.innerHTML = bangHtml();
    var t = body.querySelector('#xpvTom');
    if (t) t.outerHTML = tomTatHtml();
    noiBang();
  }

  function noiBang() {
    var os = body.querySelectorAll('[data-xpv]');
    for (var i = 0; i < os.length; i++) {
      os[i].oninput = function () {
        XPV.con[this.getAttribute('data-xpv')] = this.value;
        /* Chi ve lai KHI can: moi lan ve lai la o dang go bi thay the va
           con tro nhay ve dau. Nen chi doi lop mau va nhan "da dung" tai
           cho, ve lai ca bang thi de luc doi kho hoac doi bo loc. */
        var d = null;
        var ds = XPV.bang || [];
        for (var k = 0; k < ds.length; k++) if (ds[k].ma === this.getAttribute('data-xpv')) d = ds[k];
        if (!d) return;
        var loi = xpvLoiDong(d);
        var dd = xpvDaDung(d);
        this.className = loi ? 'r' : (dd > 0 ? 'ok' : '');
        var cuDd = this.parentNode.querySelector('.dd');
        if (cuDd) cuDd.parentNode.removeChild(cuDd);
        if (!loi && dd > 0) {
          var moiDd = document.createElement('span');
          moiDd.className = 'dd';
          moiDd.textContent = 'đã dùng ' + vxSo(dd);
          this.parentNode.appendChild(moiDd);
        }
        var cu = this.parentNode.parentNode.querySelector('.t i.r');
        if (cu) cu.parentNode.removeChild(cu);
        if (loi) {
          var i2 = document.createElement('i');
          i2.className = 'r';
          i2.textContent = loi;
          this.parentNode.parentNode.querySelector('.t').appendChild(i2);
        }
        var t = body.querySelector('#xpvTom');
        if (t) t.outerHTML = tomTatHtml();
      };
    }
  }

  function noi() {
    var gc = body.querySelector('#xpvgc');
    if (gc) gc.oninput = function () { st.ghiChu = this.value; };
    var tim = body.querySelector('#xpvtim');
    if (tim) {
      tim.oninput = function () { st.tim = this.value; veLaiBang(); };
    }
    var kho = xktKhoHtml('xpvkho', b.kho, st.kho);
    if (!kho.chip) {
      body.querySelector('#xpvkho').onclick = function () {
        xktSheetTim('Chọn kho', kho.items.map(function (k) {
          return { value: k.k, label: k.ten, phu: k.k, icon: '🏬' };
        }), st.kho, function (it) { doiKho(it.value); });
      };
    }
    body.querySelector('#xpvbp').onclick = function () {
      xktSheetTim('Chọn bộ phận chịu chi phí', bpItems, st.boPhan, function (it) {
        st.boPhan = it.value;
        veLai();
      });
    };
    body.querySelector('#xpvluu').onclick = luu;
    noiBang();
  }

  async function doiKho(k) {
    if (st.kho && k !== st.kho && Object.keys(XPV.con).length) {
      XPV.con = {};
      toast('Đổi kho nên bảng đếm bắt đầu lại.');
    }
    st.kho = k;
    try { localStorage.setItem('vgbKhoXuat', st.kho); } catch (e) { }
    /* Dien san bo phan cua diem ban do, nguoi lap doi duoc. Chi dien khi o
       dang TRONG: da chon roi ma bi ghi de la mat cong go lai. */
    if (!st.boPhan) {
      for (var i = 0; i < (b.kho || []).length; i++) {
        if (b.kho[i].name === k && b.kho[i].bo_phan_goi_y) st.boPhan = b.kho[i].bo_phan_goi_y;
      }
    }
    XPV.bang = null;
    XPV.bangKho = '';
    veLai();
    await napBang();
    veLai();
  }

  function veLai() {
    var vb = body.querySelector('.vxf');
    if (vb) vb.outerHTML = ve();
    noi();
  }

  body.onclick = function (e) {
    var t;
    if ((t = e.target.closest('[data-xpvkho]'))) return doiKho(t.getAttribute('data-xpvkho'));
    if ((t = e.target.closest('[data-xpvnhan]'))) {
      st.nhan = t.getAttribute('data-xpvnhan');
      return veLai();
    }
  };

  async function luu() {
    if (xktBaoThieu(body, [['xpvkho', !st.kho], ['xpvbp', !st.boPhan]])) {
      toast(!st.kho ? 'Chưa chọn kho.' : 'Chưa chọn bộ phận chịu chi phí.');
      return;
    }
    var d = demXong();
    if (d.loi) { toast('Có ' + d.loi + ' dòng đang sai, sửa trước khi lưu.'); return; }
    if (!d.n) { toast('Chưa mã nào có hàng đi ra. Gõ số còn lại cho ít nhất một mã.'); return; }
    /* Ghi so la tru kho THAT, tu app khong hoan lai duoc: hoi mot lan. */
    if (!await xacNhan('Ghi sổ ' + d.n + ' mã đã dùng ở ' + shortWh(st.kho) + '?\n\nTồn kho sẽ trừ ngay và không hoàn lại được từ app.', 'Ghi sổ phiếu xuất', 'Ghi sổ')) return;
    var gui = [];
    var ds = XPV.bang || [];
    for (var i = 0; i < ds.length; i++) {
      var v = XPV.con[ds[i].ma];
      if (v === undefined || v === null || String(v).trim() === '') continue;
      gui.push({ ma: ds[i].ma, nhom: ds[i].nhom, ton_so: ds[i].ton_so, con_lai: Number(v) });
    }
    this.disabled = true;
    try {
      var r = await api('vagabond.xuat_phuc_vu_ban.luu', {
        kho: st.kho,
        bo_phan_chiu: st.boPhan,
        ghi_chu: st.ghiChu,
        dong: JSON.stringify(gui)
      });
      XPV.con = {};
      XPV.bang = null;
      XPV.bangKho = '';
      st.ghiChu = '';
      /* 20/09/2026: quay lap la tru kho ngay (phuong an 1 anh Viet chot). */
      st.tab = 'xong';
      toast('Đã ghi sổ ' + r.name + ' với ' + r.so_dong + ' mã, tồn kho đã trừ.' + (r.thay_phieu_cu ? ' Phiếu nháp cũ ' + r.thay_phieu_cu + ' đã bỏ.' : ''), 5000);
      go(function () { scrXkPvView(r.name); }, true);
    } catch (e) {
      this.disabled = false;
      toast(errMsg(e) || 'Không lưu được phiếu.');
    }
  }

  noi();
  await napBang();
  veLai();
}

/* ================================================================
   3. XEM MOT PHIEU
   ================================================================ */

async function scrXkPvView(name) {
  xpvCss();
  frame('Phiếu xuất kho phục vụ bán hàng', '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try {
    d = await api('vagabond.xuat_phuc_vu_ban.chi_tiet', { name: name });
  } catch (e) {
    frame('Phiếu xuất kho phục vụ bán hàng', xktLoiHtml(errMsg(e) || 'Không đọc được phiếu.'));
    return;
  }

  /* Gom dong theo nhan tai khoan, va cong tien tung nhom: day la con so ke
     toan can khi doi chieu cuoi thang. */
  function nhomTien() {
    var g = {};
    for (var i = 0; i < d.dong.length; i++) {
      var n = d.dong[i].nhan || 'Khác';
      g[n] = (g[n] || 0) + Number(d.dong[i].tien || 0);
    }
    var s = '';
    for (var k in g) {
      s += '<div style="display:flex;justify-content:space-between;padding:5px 0;font-size:13px">' +
        '<span style="color:#475467">' + h(k) + '</span>' +
        '<b style="color:#101828">' + vxSo(g[k]) + ' đ</b></div>';
    }
    return s;
  }

  function dongTheoNhan() {
    var ds = d.dong.slice().sort(function (a, b2) {
      return (a.nhan || '').localeCompare(b2.nhan || '');
    });
    var s = '';
    var cu = '';
    for (var i = 0; i < ds.length; i++) {
      if (ds[i].nhan !== cu) {
        cu = ds[i].nhan;
        s += '<div class="xpvn">' + h(cu || 'Khác') + '</div>';
      }
      s += xktDongXem([ds[i]]);
    }
    return s;
  }

  function ve() {
    return '<div class="vxf">' +
      xktDauPhieu(d, [d.kho_xuat, d.bo_phan].filter(Boolean).join(' · ')) +
      (d.vgb_huy ? '<div class="xpvbao"><b>Phiếu đã bỏ.</b> Lý do: ' + h(d.vgb_huy_ly_do || 'không ghi') + '</div>' : '') +
      '<div class="vf"><div class="vfh"><span class="ic">📦</span><b>Hàng đã dùng</b></div>' +
      dongTheoNhan() +
      '<div style="border-top:1px solid #e4e7ec;margin-top:10px;padding-top:6px">' + nhomTien() +
      '<div style="display:flex;justify-content:space-between;padding:7px 0 0;font-size:15px">' +
      '<b style="color:#101828">Tổng</b><b style="color:#101828">' + vxSo(d.tong_tien) + ' đ</b></div>' +
      '</div></div>' +
      (d.ghi_chu ? '<div class="vf"><div class="vfh"><span class="ic">📝</span><b>Ghi chú</b></div>' +
        '<div style="font-size:14px;color:#475467">' + h(d.ghi_chu) + '</div></div>' : '') +
      xktVet(d) +
      (d.docstatus === 0 && !d.vgb_huy && d.duoc_duyet
        ? xktNutChinh('xpvghi', 'Ghi sổ phiếu này', 'Ghi sổ xong tồn kho mới thực sự trừ.') : '') +
      (d.docstatus === 0 && !d.vgb_huy && (d.la_cua_toi || d.duoc_duyet)
        ? '<button class="vxb o" id="xpvbo" style="margin-top:10px">Bỏ phiếu này</button>' : '') +
      '</div>';
  }

  var body = frame('Phiếu xuất kho phục vụ bán hàng', ve());

  var nutGhi = body.querySelector('#xpvghi');
  if (nutGhi) {
    nutGhi.onclick = async function () {
      /* Ghi so la tru kho THAT va tu app khong hoan lai duoc. Bam nham tren
         dien thoai thi phai ra may tinh huy dung nghiep vu. Hoi truoc, giong
         man Xuat dung noi bo. Codex bat tren PR #341. */
      if (!await xacNhan('Ghi sổ phiếu ' + d.name + '?\n\nTồn kho sẽ trừ thật và không hoàn lại được từ app.', 'Ghi sổ', 'Ghi sổ')) return;
      this.disabled = true;
      try {
        await api('vagabond.xuat_phuc_vu_ban.ghi_so', { name: d.name });
        toast('Đã ghi sổ ' + d.name + '.');
        go(function () { scrXkPvView(d.name); }, true);
      } catch (e) {
        this.disabled = false;
        toast(errMsg(e) || 'Không ghi sổ được.');
      }
    };
  }
  var nutBo = body.querySelector('#xpvbo');
  if (nutBo) {
    nutBo.onclick = async function () {
      /* `hoiChu` tra ve Promise, va tra null khi nguoi ta bam Thoi. Bat
         buoc go ly do: phieu bi bo ma khong biet vi sao thi lan sau khong
         ai hoc duoc gi tu no. */
      var ly = await hoiChu('Bỏ phiếu này',
        'Vì sao bỏ phiếu? Câu này nằm lại trong nhật ký của phiếu.', '',
        { bat_buoc: 1 });
      if (ly === null || ly === undefined) return;
      try {
        await api('vagabond.xuat_phuc_vu_ban.bo_phieu', { name: d.name, ly_do: ly });
        toast('Đã bỏ phiếu ' + d.name + '.');
        go(function () { scrXkPvView(d.name); }, true);
      } catch (e) {
        toast(errMsg(e) || 'Không bỏ được phiếu.');
      }
    };
  }
}

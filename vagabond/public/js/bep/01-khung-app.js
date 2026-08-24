/* ---------- 3. State + router ---------- */
var APPNAME = 'The Vagabond Pâtisserie';
var S = {
  user: frappe.session.user, roles: [], wh: [], groups: [], suppliers: null,
  gtree: {}, gis: {}, gbep: {}, me: { user: frappe.session.user, full_name: '', bo_phan: '' },
  draft: null, stack: [], counts: {}
};
var DEPT_ORDER = ['Pha chế', 'Thu ngân', 'Phục vụ', 'Sales', 'Marketing', 'Bếp Pastry', 'Bếp Baker', 'Tạp vụ', 'Bảo vệ', 'Kế toán', 'Thu mua', 'Kho', 'Vận hành', 'Giám đốc', 'Sonneto Lab'];
var DEPTS = DEPT_ORDER.map(function (x) { return x + ' - TV'; });
function shortDep(x) { return shortWh(x); }
function deptRank(x) { var i = DEPT_ORDER.indexOf(shortDep(x)); return i < 0 ? 99 : i; }
var TYPES = {
  Purchase:  { key: 'Purchase',          icon: '🛒', title: 'Yêu cầu mua hàng',  sub: 'Mua từ nhà cung cấp, nhận về kho', timeLabel: 'Giờ cần hàng',  needFrom: false, needSup: true,  hasTime: false, roots: ['Mua vào'] },
  Transfer:  { key: 'Material Transfer', icon: '🚚', title: 'Yêu cầu điều chuyển nội bộ', sub: 'Xin kho khác soạn hàng chuyển sang', timeLabel: 'Giờ cần hàng',  needFrom: true,  needSup: false, hasTime: false, roots: null },
  Manufacture: { key: 'Manufacture',     icon: '🎂', title: 'Phiếu yêu cầu sản xuất', sub: 'Đặt bếp làm bánh, ghi rõ giờ cần', timeLabel: 'Giờ cần bánh', needFrom: false, needSup: false, hasTime: true, roots: ['Bán ra', 'Sản xuất'] }
};
function typeOf(k) { for (var x in TYPES) if (TYPES[x].key === k) return TYPES[x]; return TYPES.Purchase; }
function curUser() {
  var u = '';
  try { u = (window.frappe && frappe.session && frappe.session.user) || ''; } catch (e) { }
  if (!u || u === 'Guest') { try { u = (window.frappe && frappe.boot && frappe.boot.user && frappe.boot.user.name) || u; } catch (e) { } }
  if (!u || u === 'Guest') u = S.user || '';
  return u;
}
function syncUser() { var u = curUser(); if (u) { S.user = u; S.me.user = u; } return S.user; }

/* Moi man hinh trong app la MOT moc lich su that (vgbD = do sau trong S.stack).
   Nho vay nut Back / vuot lui cua trinh duyet lui dung tung man trong app,
   het canh dang o Chi tiet don ma Back lai vang sang trang /kiem-banh. */
var VGB_LUI_TAY = 0;

/* ---------- DIA CHI DI THEO TUNG NAC CUA CHONG MAN HINH (v292) ----------

Anh Viet 24/08/2026: *"bam vao 'hoa don mua' thi co duoi url hoa-don-mua,
nhung back ve thi trang van mang duoi hoa-don-mua"*.

VI SAO BAN CU HONG. Truoc v292, `vgbGo` doi dia chi TRUOC roi moi goi `go`:

    vgbDatDuong(k);        // replaceState: doi dia chi cua NAC DANG DUNG
    go(scrHdMua);          // pushState(location.href): nac moi cung dia chi do

replaceState ghi de dia chi cua chinh moc lich su dang dung, tuc moc cua man
CHA. Nen sau mot lan bam, ca hai moc cha va con deu mang `/hoa-don-mua`. Nut
Back lui dung mot man nhung dia chi thi khong co gi de lui ve.

CACH SUA. Dia chi thoi khong con la mot hieu ung phu bam vao luc bam nut nua,
no thanh MOT THUOC TINH cua tung nac trong chong: `S.duong[i]` la slug cua
`S.stack[i]`. Moi cho lam chong doi - go, back, reset, va ca popstate - deu
ap lai dia chi cua nac dang o tren cung. Nac nao khong co slug rieng, vi du
man chi tiet mo tu mot danh sach, thi thua slug cua nac cha, nen dia chi
dung im trong suot mot mach xem chi tiet roi tro ve dung cho khi lui.

Nac 0 mang chuoi rong, va chuoi rong nghia la dia chi goc cua app. */
S.duong = [];

/* Slug cua nac dang dung. */
function vgbNacDuong() { return S.duong[S.duong.length - 1] || ''; }

/* Ap dia chi cua nac dang dung len thanh dia chi.

   Ham that nam ben 02-trang-chu.js vi o do moi co bang VGB_DUONG. Goi qua
   window va boc try: tep nay ghep TRUOC tep kia, va mot loi o day thi ca
   app khong di lai duoc nua - dat hon nhieu so voi mot dia chi sai. */
function vgbApNac() {
  try { if (window.vgbApDiaChi) window.vgbApDiaChi(vgbNacDuong()); } catch (e) { }
}
function manSoan(f) {
  try { return f === scrStep1 || f === scrStep2 || f === scrStep3 || f === scrStep4; } catch (e) { return false; }
}
function roiPhieuDo(dich) {
  /* Dang dung o man soan phieu, co it nhat mot mon, va dich den KHONG con
     trong luong soan -> roi di la mat ban nhap, phai hoi mot cau. */
  return !!(S.draft && (S.draft.items || []).length) && manSoan(S.stack[S.stack.length - 1]) && !manSoan(dich);
}
function go(fn, replace) {
  /* Khoa man sap mo do vgbGo dat, doc mot lan roi xoa. Man nao khong di qua
     vgbGo, vi du man chi tiet mo tu mot danh sach, thi khong co khoa va se
     thua dia chi cua nac cha. */
  var slug = '';
  try { if (window.vgbSlugSapMo) slug = window.vgbSlugSapMo(); } catch (e) { }
  if (!replace) {
    S.stack.push(fn);
    S.duong.push(slug || vgbNacDuong());
    /* pushState TRUOC khi doi dia chi: moc moi phai chup lai dia chi CU thi
       moc cua man cha moi con nguyen dia chi cua no. Doi thu tu hai dong
       nay chinh la loi anh Viet bao ngay 24/08. */
    try { history.pushState({ vgbD: S.stack.length - 1 }, '', location.href); } catch (e) { }
  } else {
    S.stack[S.stack.length - 1] = fn;
    if (slug) S.duong[S.duong.length - 1] = slug;
  }
  vgbApNac();
  render();
}
function back() {
  if (S.stack.length <= 1) return;
  var buoc = function () {
    S.stack.pop(); S.duong.pop(); vgbApNac(); render();
    VGB_LUI_TAY++;
    try { history.back(); } catch (e) { VGB_LUI_TAY--; }
  };
  if (roiPhieuDo(S.stack[S.stack.length - 2])) {
    confirmSheet('Phiếu đang soạn dở', 'Rời màn này thì danh sách món đang chọn sẽ mất.', 'Rời đi, bỏ phiếu nháp', true)
      .then(function (ok) { if (ok) { S.draft = null; buoc(); } });
    return;
  }
  buoc();
}
function reset(fn) {
  var slug = '';
  try { if (window.vgbSlugSapMo) slug = window.vgbSlugSapMo(); } catch (e) { }
  S.stack = [fn];
  S.duong = [slug];
  try { history.replaceState({ vgbD: 0 }, '', location.href); } catch (e) { }
  vgbApNac();
  return render();
}
/* TRA VE ket qua cua ham man hinh, dung nuot di.

   Phan lon man hinh la `async`: no ve tam mot cai dong ho cat roi `await`
   du lieu, xong moi ve that. Nuot promise di thi ai goi render() cung khong
   biet luc nao man ve xong.

   Ngay 23/08/2026 dinh dung loi do: __boot goi reset(scrHome) roi mo ngay
   man theo dia chi, nhung scrHome ve THAT muon hon va de len man vua mo,
   nen F5 tai /don-da-huy van ra trang chu. */
function render() { var f = S.stack[S.stack.length - 1]; if (f) return f(); }

/* GIU VI TRI CUON, dung chung cho MOI man hinh.

   Man nao cung ve lai bang cach ghi de root.innerHTML, nen moi lan bam mot
   nut la khung cuon moi tinh va nguoi dung bi nem len dau trang. Anh Viet
   bao lan dau 09/08/2026 o man tinh tien quay, va lan hai 22/08/2026 o man
   thanh toan truoc cho NCC: *"cu bam nut nao trong phieu la lai bi cuon ve
   dau trang"*.

   BAN VA DAU TIEN CHUA DU, VA DAY LA LY DO
   ----------------------------------------
   Ban truoc doc vi tri cuon ngay dau `frame()` roi tra lai o cuoi. Nghe thi
   dung, nhung hau het man hinh goi `frame()` HAI LAN cho mot lan bam:

       frame(tieu_de, '<div class="emp">⏳ Dang tai...</div>');   // lan 1
       ... await may chu ...
       frame(tieu_de, noi_dung_that);                            // lan 2

   Lan 1 ve ra mot khung ngan tun, scrollTop tut ve 0. Lan 2 doc scrollTop
   thay 0, tuong nguoi dung dang o dau trang, va ghi de mat vi tri that.
   Cang nhieu man dung khung cho thi cang dinh, nen nhin vao thi giong nhu
   "bam nut nao cung nhay len dau".

   CACH CHUA
   ---------
   Ghi vi tri NGAY LUC NGUOI DUNG CUON chu khong doi den luc ve lai man. Cai
   bay duy nhat: chinh minh dat `scrollTop` cung sinh ra su kien `scroll`, va
   luc khung con ngan thi trinh duyet ket qua ve 0 - neu ghi lai gia tri do
   thi vi tri lai mat lan nua. Nen co co `VGB_DANG_TRA` de bo qua dung nhung
   su kien do minh gay ra.

   Doi sang man khac thi tieu de khac, xoa vi tri de bat dau tu dau trang. */
var VGB_TD = '', VGB_CUON = 0, VGB_DANG_TRA = 0;

function vgbTheoDoiCuon(ob) {
  if (!ob || ob.vgbDaNghe) return;
  ob.vgbDaNghe = 1;
  ob.addEventListener('scroll', function () {
    if (VGB_DANG_TRA) return;
    VGB_CUON = ob.scrollTop || 0;
  }, { passive: true });
}

function vgbTraCuon(ob, dat) {
  if (!ob || !dat) return;
  VGB_DANG_TRA = 1;
  ob.scrollTop = dat;
  var thoi = function () { VGB_DANG_TRA = 0; };
  try {
    requestAnimationFrame(function () {
      /* Anh mon, ma QR... tai xong moi day chieu cao len, dat lai mot nhip
         nua cho chac. Chi dat khi khung dang o 0, tuc lan truoc bi ket. */
      if (ob.isConnected && ob.scrollTop !== dat && ob.scrollTop === 0) ob.scrollTop = dat;
      requestAnimationFrame(thoi);
    });
  } catch (e) { setTimeout(thoi, 80); }
}

function frame(title, bodyHtml, opt) {
  opt = opt || {};
  /* Tieu de tab trinh duyet theo man hinh, liec tab biet ngay dang o dau */
  try { document.title = (title && title !== APPNAME) ? title + ' · Vagabond' : APPNAME; } catch (e) { }
  var doiMan = (VGB_TD !== title);
  if (doiMan) VGB_CUON = 0;
  VGB_TD = title;
  var giuCuon = (!doiMan && VGB_CUON > 0);
  var showBack = S.stack.length > 1;
  root.innerHTML =
    '<div class="vh">' +
      (showBack ? '<button class="ic" id="vgbBack">&#8249;</button>' : '<span class="ic"></span>') +
      (showBack ? '<button class="ic" id="vgbHome" aria-label="Ve trang chu">&#127968;</button>' : '') +
      '<b>' + h(title) + '</b>' +
      (opt.action ? '<button class="ic" id="vgbAct">' + opt.action + '</button>' : '') +
      (showBack ? (opt.action ? '' : '<span class="ic"></span>') : '<button class="ic" id="vgbAcc" aria-label="Tai khoan">&#128100;</button>') +
    '</div>' +
    '<div class="vb" id="vgbBody">' + bodyHtml + '</div>' +
    (opt.footer ? '<div class="vf">' + opt.footer + '</div>' : '') +
    (opt.fab ? '<button class="fab" id="vgbFab">+</button>' : '');
  var b = document.getElementById('vgbBack'); if (b) b.onclick = back;
  var hb = document.getElementById('vgbHome'); if (hb) hb.onclick = function () {
    if (roiPhieuDo(scrHome)) {
      confirmSheet('Phiếu đang soạn dở', 'Về trang chủ thì danh sách món đang chọn sẽ mất.', 'Về trang chủ, bỏ phiếu nháp', true)
        .then(function (ok) { if (ok) { S.draft = null; reset(scrHome); } });
      return;
    }
    reset(scrHome);
  };
  var ab = document.getElementById('vgbAcc'); if (ab) ab.onclick = function () { go(scrAccount); };
  var a = document.getElementById('vgbAct'); if (a && opt.onAction) a.onclick = opt.onAction;
  var f = document.getElementById('vgbFab'); if (f && opt.onFab) f.onclick = opt.onFab;
  dSkin(root);
  var moiOb = document.getElementById('vgbBody');
  vgbTheoDoiCuon(moiOb);
  if (giuCuon) vgbTraCuon(moiOb, VGB_CUON);
  return moiOb;
}

/* ---------- 4. Master data ---------- */
async function loadMasters() {
  if (S.wh.length) return;
  syncUser();
  var _kd = null;
  try { _kd = await api('vagabond.nhan_su.khoi_dong', {}); } catch (e) { _kd = null; }
  var r = (_kd && _kd.kho) ? [
    _kd.kho.map(function (n) { return { name: n }; }),
    _kd.nhom || [],
    (_kd.vai || []).map(function (v) { return { role: v }; })
  ] : await Promise.all([
    getList('Warehouse', { fields: ['name'], filters: { is_group: 0, disabled: 0, company: COMPANY }, limit_page_length: 200, order_by: 'name' }),
    getList('Item Group', { fields: ['name', 'parent_item_group', 'is_group', 'custom_bep_phu_trach'], limit_page_length: 0, order_by: 'name' }),
    getList('Has Role', { parent: 'User', fields: ['role'], filters: { parent: S.user || '__khong_co__', parenttype: 'User' }, limit_page_length: 100 })
  ]);
  S.wh = r[0].map(function (x) { return x.name; });
  S.roles = r[2].map(function (x) { return x.role; });
  S.gtree = {}; S.gis = {}; S.groups = []; S.gbep = {};
  r[1].forEach(function (g) {
    S.gis[g.name] = g.is_group ? 1 : 0;
    if (!g.is_group) S.groups.push(g.name);
    if (g.custom_bep_phu_trach) S.gbep[g.name] = g.custom_bep_phu_trach;
    var p = g.parent_item_group || '';
    if (!S.gtree[p]) S.gtree[p] = [];
    S.gtree[p].push(g.name);
  });
  r[1].forEach(function (g) {
    if (S.gbep[g.name]) return;
    var p = g.parent_item_group, n = 0;
    while (p && n < 8) { if (S.gbep[p]) { S.gbep[g.name] = S.gbep[p]; break; } var f = r[1].filter(function (x) { return x.name === p; })[0]; p = f ? f.parent_item_group : ''; n++; }
  });
  if (S.user) {
    try {
      var u = await api('frappe.client.get_value', { doctype: 'User', filters: { name: S.user }, fieldname: ['name', 'full_name', 'custom_phong_ban', 'custom_bo_phan', 'custom_kho_phu_trach'] });
      if (u && u.name === S.user) { S.me.full_name = u.full_name || ''; S.me.bo_phan = u.custom_phong_ban || u.custom_bo_phan || ''; S.me.khoGiu = String(u.custom_kho_phu_trach || '').split(',').map(function (s2) { return s2.trim(); }).filter(function (s2) { return !!s2; }); }
    } catch (e) { }
  }
  if (!S.me.full_name) { try { S.me.full_name = frappe.session.user_fullname || ''; } catch (e) { } }
  if (!S.me.bo_phan) { try { S.me.bo_phan = localStorage.getItem('vgb_bp_' + S.user) || ''; } catch (e) { } }
  try {
    var dp = await getList('Department', { fields: ['name'], filters: { is_group: 0, disabled: 0 }, limit_page_length: 0 });
    if (dp && dp.length) DEPTS = dp.map(function (x) { return x.name; }).sort(function (a, b2) { return (deptRank(a) - deptRank(b2)) || (a < b2 ? -1 : 1); });
  } catch (e) { }
}

/* tat ca nhom la nam duoi cac nhom goc */
function leavesUnder(roots) {
  if (!roots || !roots.length) return null;
  var out = [];
  function walk(nm) {
    if (S.gis[nm]) { (S.gtree[nm] || []).forEach(walk); }
    else if (out.indexOf(nm) < 0) out.push(nm);
  }
  roots.forEach(walk);
  return out;
}
function hasRole(r) { return S.roles.indexOf(r) >= 0; }

/* Ai duoc vao phan he Thu mua: thu mua, ke toan, giam doc.

   Khop voi QUYEN_THU_MUA ben vagabond/quyen_phan_he.py - o day chi de an
   nut cho gon mat, con chan that su thi nam o may chu.

   Anh Viet 18/08/2026 bao cac nut mua hang "de chung chung khien toan bo
   nhan vien deu nhin thay". Thu pham la vai 'Bo phan dat hang' truoc day
   nam trong danh sach nay: vai do sinh ra de LAP YEU CAU MUA nen gan nhu ai
   cung co, ke ca bep va sales. Da go ra khoi day. */
function coQuyenMua() {
  return hasRole('System Manager') || hasRole('Thu mua') || hasRole('Giám đốc')
    || hasRole('Purchase Manager') || hasRole('Purchase User')
    || hasRole('Accounts Manager') || hasRole('Accounts User');
}

/* Ai duoc go dau huy mot phieu nhap. Khop voi QUYEN_HUY ben
   vagabond/chung_tu.py - o day chi de an nut, chan that nam o may chu. */
function coQuyenHuy() {
  return hasRole('System Manager') || hasRole('Accounts Manager') || hasRole('Accounts User');
}

/* ---------- Bep: dinh tuyen phieu yeu cau san xuat ---------- */
var BEPS = ['Bếp Pastry', 'Bếp Baker', 'Bếp Lab'];
function myKitchen() {
  var d = shortDep(S.me.bo_phan || '');
  for (var i = 0; i < BEPS.length; i++) if (d.indexOf(BEPS[i]) === 0) return BEPS[i];
  if (d.indexOf('Sonneto Lab') === 0 || d.indexOf('Lab') === 0) return 'Bếp Lab';
  return '';
}
function bepOfItem(it) { return it.bep || S.gbep[it.item_group] || ''; }
function autoKitchen(items) {
  var seen = {}, ks = [];
  (items || []).forEach(function (it) { var k = bepOfItem(it); if (k && !seen[k]) { seen[k] = 1; ks.push(k); } });
  if (!ks.length) return '';
  if (ks.length === 1) return ks[0];
  return 'Cả hai bếp';
}
function bepSeesRow(v) {
  var me = myKitchen();
  if (!me) return true;
  if (!v) return true;
  return v === me || v === 'Cả hai bếp';
}
function whOpts() { return S.wh.map(function (w) { return { value: w, label: shortWh(w) }; }); }


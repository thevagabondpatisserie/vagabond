/* ---------- 48. Ban soan do: tu luu phieu dang soan tren may (v533) ----------

   Loan Anh bao anh Viet 27/09/2026: "cai file bao gia tren ERP lam ma khong
   bam luu vo tinh thoat ra hay may sap nguon la no mat het luon". Anh Viet
   chot: MOI man lap phieu deu phai co ban nhap, tu luu ngay tren may (khong
   doi mang, khong tao chung tu nhap tren may chu), mo lai thi hoi co lam
   tiep khong.

   Cach lam, gom ve MOT cho (bai hoc #205: dung di rai loi goi o tung man):
     - Moi man lap phieu khai mot dong trong SD_MAN: doc trang thai o dau,
       dat lai ra sao, luu thanh cong la goi ham may chu nao.
     - sdBoc boc ham man do. Khung app (frame, api, trang chu) duoc boc mot
       lan o cuoi tep nay, nen man nao cung di qua dung mot duong.
     - Ban nhap nam trong localStorage cua MAY DO, theo tung tai khoan, het
       han sau 14 ngay. Anh chup chua tai len (base64, File) KHONG luu: qua
       nang, day bo nho la hong ca ban nhap. Mo lai thi bao can chup lai.
     - Luu ngay sau khi go (tre 0,6 giay), truoc moi lan bam, khi roi man,
       khi an tab va khi dong trang. May sap nguon thi mat toi da 0,6 giay
       go cuoi cung.
     - Luu phieu thanh cong (dung ham may chu da khai) thi xoa ban nhap.
     - Mo lai man ma co ban nhap thi hoi: mo tiep, hay soan moi. Soan moi
       KHONG xoa ban cu, chi cat sang mot khoa rieng, van mo lai duoc tu the
       "Phieu dang soan do" tren trang chu. Khong nhanh nao lam mat ban nhap
       ma nguoi dung chua tu tay bo.

   Bat bien quan trong:
     - Chua dang ky thi KHONG luu gi. Dang ky chi xay ra SAU khi nguoi dung da
       tra loi cau hoi mo tiep hay soan moi, de mot cu bam trong hop hoi
       khong ghi de ban nhap cu bang to trang.
     - Trang thai doc ra la null (man vua roi da xoa trang thai cua no) thi
       giu nguyen ban da luu, khong ghi to rong de len. */

var SD_TIEN_TO = 'vgbSoanDo:';
var SD_HAN_NGAY = 14;
var SD_CHO_MS = 600;
var SD_DAU_BO = '__vgbSoanDoBo__';
var SD_BO_KIEU = { file: 1, password: 1, hidden: 1, button: 1, submit: 1, reset: 1, image: 1 };
var SD = {
  dk: '', loai: '', man: '', ma: '', fn: null, args: [], nen: '', hopEl: null, laHop: 0,
  daGhi: 0, oCu: null, roi: null, moNgay: null, ghepCho: null, hen: 0, baoDay: 0
};
var SD_MAN = {};
var SD_BOC = {};

/* ---- kho tren may ---- */
function sdKho() { try { return window.localStorage || null; } catch (e) { return null; } }
function sdNguoi() {
  var u = '';
  try { u = String((S && S.user) || ''); } catch (e) { }
  return (u && u !== 'Guest') ? u : '';
}
function sdKhoa(loai, ma) { return SD_TIEN_TO + sdNguoi() + ':' + loai + ':' + (ma ? String(ma) : 'moi'); }
function sdDoc(k) {
  var ls = sdKho(); if (!ls || !k) return null;
  try { var r = JSON.parse(ls.getItem(k) || 'null'); return (r && r.v === 1 && r.js) ? r : null; }
  catch (e) { return null; }
}
function sdXoa(k) { var ls = sdKho(); if (!ls || !k) return; try { ls.removeItem(k); } catch (e) { } }
function sdGhi(k, rec) {
  var ls = sdKho(); if (!ls || !k) return false;
  try { ls.setItem(k, JSON.stringify(rec)); return true; }
  catch (e) {
    /* Day bo nho: bao MOT lan, khong tu xoa ban nhap nao khac de lay cho. */
    if (!SD.baoDay) { SD.baoDay = 1; try { toast('Máy hết chỗ lưu bản nháp. Bấm Lưu phiếu sớm giúp nhé.', 6000); } catch (e2) { } }
    return false;
  }
}
/* Moi ban nhap cua tai khoan dang dung, moi nhat truoc. Ban qua han thi xoa. */
function sdDs() {
  var ls = sdKho(), u = sdNguoi(), ra = [];
  if (!ls || !u) return ra;
  var dau = SD_TIEN_TO + u + ':', han = Date.now() - SD_HAN_NGAY * 864e5, cac = [];
  try { for (var i = 0; i < ls.length; i++) { var k = ls.key(i); if (k && k.indexOf(dau) === 0) cac.push(k); } }
  catch (e) { return ra; }
  cac.forEach(function (k) {
    var r = sdDoc(k);
    if (!r || !(r.luc > han)) { sdXoa(k); return; }
    r.khoa = k; ra.push(r);
  });
  ra.sort(function (a, b) { return b.luc - a.luc; });
  return ra;
}

/* ---- chup va dat lai ---- */
function sdLoc(dem) {
  return function (k, v) {
    if (v && typeof v === 'object') {
      if (v.nodeType) return undefined;
      if (typeof Blob !== 'undefined' && v instanceof Blob) { dem.n++; return SD_DAU_BO; }
    }
    if (typeof v === 'string' && (v.length > 60000 || (v.length > 400 && /^data:[a-z]+\/[a-z0-9.+-]+;base64,/i.test(v)))) {
      dem.n++; return SD_DAU_BO;
    }
    return v;
  };
}
/* Bo dau "anh da bo": phan tu mang mang dau thi bo ca phan tu (vi du mot anh
   {ten, b64}), thuoc tinh mang dau thi bo thuoc tinh do. */
function sdCoDau(o) { for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k) && o[k] === SD_DAU_BO) return true; return false; }
function sdBoDau(x) {
  if (Array.isArray(x)) {
    var ra = [];
    x.forEach(function (p) {
      if (p === SD_DAU_BO) return;
      if (p && typeof p === 'object' && !Array.isArray(p) && sdCoDau(p)) return;
      ra.push(sdBoDau(p));
    });
    return ra;
  }
  if (x && typeof x === 'object') {
    Object.keys(x).forEach(function (k) { if (x[k] === SD_DAU_BO) delete x[k]; else x[k] = sdBoDau(x[k]); });
  }
  return x;
}
function sdMoJs(rec) {
  try { var v = JSON.parse(rec.js); return { s: sdBoDau(v.s), o: v.o || {} }; }
  catch (e) { return { s: null, o: {} }; }
}

function sdKieu(el) { return String(el.type || (el.getAttribute && el.getAttribute('type')) || '').toLowerCase(); }
/* Khoa on dinh cua mot o nhap: id, roi name, roi thuoc tinh data- dau tien.
   KHONG dung vi tri: danh sach ca hay dong hang doi thu tu thi so thu tu
   tro nham sang o khac. */
function sdKhoaO(el) {
  if (el.id) return '#' + el.id;
  var ty = sdKieu(el);
  var nm = el.getAttribute && el.getAttribute('name');
  if (nm) return 'n:' + nm + (ty === 'radio' ? '=' + el.value : '');
  var tt = el.attributes || [];
  for (var i = 0; i < tt.length; i++) {
    if (tt[i] && String(tt[i].name).indexOf('data-') === 0) return '@' + tt[i].name + '=' + tt[i].value;
  }
  return '';
}
function sdCacO(goc) {
  var ra = [];
  if (!goc || !goc.querySelectorAll) return ra;
  var ds = goc.querySelectorAll('input,textarea,select');
  for (var i = 0; i < ds.length; i++) {
    var el = ds[i];
    if (SD_BO_KIEU[sdKieu(el)]) continue;
    if (el.closest && el.closest('.srch')) continue;
    var k = sdKhoaO(el);
    if (k) ra.push([k, el]);
  }
  return ra;
}
function sdDocO(goc) {
  var ra = {};
  sdCacO(goc).forEach(function (p) {
    if (Object.prototype.hasOwnProperty.call(ra, p[0])) return;
    var el = p[1], ty = sdKieu(el);
    ra[p[0]] = (ty === 'checkbox' || ty === 'radio') ? (el.checked ? 1 : 0) : String(el.value == null ? '' : el.value);
  });
  return ra;
}
function sdPhat(el) {
  ['input', 'change'].forEach(function (t) {
    try {
      var ev;
      try { ev = new Event(t, { bubbles: true }); }
      catch (e) { ev = document.createEvent('Event'); ev.initEvent(t, true, true); }
      el.dispatchEvent(ev);
    } catch (e2) { }
  });
}
function sdApO(goc, o, phat) {
  var n = 0;
  if (!o) return n;
  sdCacO(goc).forEach(function (p) {
    if (!Object.prototype.hasOwnProperty.call(o, p[0])) return;
    var el = p[1], ty = sdKieu(el), v = o[p[0]];
    if (ty === 'checkbox' || ty === 'radio') {
      if (!!el.checked === !!v) return;
      el.checked = !!v;
    } else {
      if (String(el.value) === String(v)) return;
      el.value = v;
    }
    n++;
    if (phat) sdPhat(el);
  });
  return n;
}

function sdDinh() { return S.stack[S.stack.length - 1]; }
function sdConGan(el) {
  if (!el) return false;
  if (typeof el.isConnected === 'boolean') return el.isConnected;
  for (var n = el; n; n = n.parentNode) if (n === document.body) return true;
  return false;
}
function sdHopHien() {
  var cfg = SD_MAN[SD.loai];
  var el = null;
  try { el = (cfg && cfg.hop) ? cfg.hop() : SD.hopEl; } catch (e) { el = null; }
  return (el && sdConGan(el)) ? el : null;
}
function sdGoc() { return SD.laHop ? sdHopHien() : document.getElementById('vgbBody'); }

function sdChup(loai, goc) {
  var cfg = SD_MAN[loai]; if (!cfg) return null;
  /* KHONG goi ham doc o nhap cua man (bgDoc, dsTayDoc...): vai ham gan ''
     cho o khong tim thay, ma luc man dang ve tam dong ho cat thi chua co o
     nao, goi vao la xoa trang trang thai that. Chu dang go nam trong so lieu
     o (o) va duoc dien lai sau khi ve. */
  var s = null;
  if (cfg.lay) {
    try { s = cfg.lay(); } catch (e) { return null; }
    if (s == null) return null;
  } else if (!goc) return null;
  var o = sdDocO(goc);
  /* Man dang ve tam dong ho cat (chua co o nao) thi giu so lieu o cua lan
     truoc, khong ghi de bang to rong. */
  if (!Object.keys(o).length && SD.oCu && loai === SD.loai) o = SD.oCu;
  var dem = { n: 0 }, js;
  try { js = JSON.stringify({ s: s, o: o }, sdLoc(dem)); } catch (e) { return null; }
  return { js: js, anh: dem.n, o: o, s: s };
}

function sdMa(cfg, args) {
  try { return cfg.ma ? String(cfg.ma(args) || '') : ''; } catch (e) { return ''; }
}
function sdArgs(a) { try { return JSON.parse(JSON.stringify(a || [])); } catch (e) { return []; } }

function sdDangKy(loai, man, dk, fn, args, nen, ma, laHop, hopEl) {
  if (SD.hen) { clearTimeout(SD.hen); SD.hen = 0; }
  SD.dk = dk; SD.loai = loai; SD.man = man; SD.fn = fn || null; SD.args = args || [];
  SD.nen = nen || ''; SD.ma = ma || ''; SD.laHop = laHop ? 1 : 0; SD.hopEl = hopEl || null;
  SD.daGhi = 0; SD.oCu = null;
}
function sdThoi() {
  if (SD.hen) { clearTimeout(SD.hen); SD.hen = 0; }
  SD.dk = ''; SD.fn = null; SD.hopEl = null; SD.laHop = 0; SD.oCu = null;
}

/* dangRoi: goi tu khung luc DANG roi man. Luc do chong da doi (nut lui da
   cat nac, man moi da day len) nhung o nhap cua man cu van con tren trang,
   nen van chup duoc va phai chup ngay. */
function sdLuuNgay(dangRoi) {
  if (SD.hen) { clearTimeout(SD.hen); SD.hen = 0; }
  if (!SD.dk) return;
  if (SD.laHop) { if (!sdHopHien()) { sdThoi(); return; } }
  else if (!dangRoi && sdDinh() !== SD.fn) return;
  var c = sdChup(SD.loai, sdGoc());
  if (!c) return;
  if (Object.keys(c.o).length) SD.oCu = c.o;
  if (c.js === SD.nen) {
    /* Nguoi dung sua roi lai tra ve dung nhu luc mo: khong con gi de giu. */
    if (SD.daGhi) { sdXoa(SD.dk); SD.daGhi = 0; }
    return;
  }
  var cfg = SD_MAN[SD.loai] || {};
  var td = '';
  try { td = cfg.tieuDe ? String(cfg.tieuDe(JSON.parse(c.js).s, c.o) || '') : ''; } catch (e) { td = ''; }
  var rec = {
    v: 1, loai: SD.loai, man: SD.man, ma: SD.ma, args: sdArgs(SD.args),
    luc: Date.now(), tieu_de: td.slice(0, 140), anh: c.anh, js: c.js
  };
  if (sdGhi(SD.dk, rec)) SD.daGhi = 1;
}
function sdHen() {
  if (!SD.dk) return;
  if (SD.hen) clearTimeout(SD.hen);
  SD.hen = setTimeout(function () { sdLuuNgay(); }, SD_CHO_MS);
}

/* Luu phieu thanh cong: xoa ban nhap, thoi theo doi. */
function sdDaLuu(dk) {
  sdXoa(dk);
  if (SD.dk === dk) sdThoi();
  if (SD.roi && SD.roi.dk === dk) SD.roi = null;
}
function sdLaLuu(loai, method, args) {
  var cfg = SD_MAN[loai]; if (!cfg || !cfg.luu) return false;
  for (var i = 0; i < cfg.luu.length; i++) {
    var l = cfg.luu[i];
    if (typeof l === 'function' ? l(method, args || {}) : l === method) return true;
  }
  return false;
}
/* May chu tra ve thanh cong CHUA chac da co phieu: nop_quy.tao va
   tao_theo_ngay tra {can_ly_do: 1} truoc khi insert de man hoi ly do lech,
   roi goi lai (Codex #378). Mot cho duy nhat quyet "da tao that chua": co
   hoi them (can_ly_do) hoac bao ok: 0 thi CHUA, giu nguyen ban nhap. */
function sdDaTaoPhieu(kq) {
  if (kq && typeof kq === 'object') {
    if (kq.can_ly_do) return false;
    if (kq.ok === 0 || kq.ok === false) return false;
  }
  return true;
}
/* Mot phieu insert thang bang frappe.client.insert: chi tinh la luu khi dung
   doctype, vi cung man do con insert mau don, tep dinh kem... */
function sdChen(dt) {
  return function (m, a) { return m === 'frappe.client.insert' && !!(a && a.doc && a.doc.doctype === dt); };
}

/* Tra trang thai da luu vao cho man doc: dat thang, hoac hen de man tu ghep
   khi no dung xong trang thai tu may chu (sdGhep). */
function sdNapLai(cfg, loai, v, args) {
  if (cfg.ghep) SD.ghepCho = { loai: loai, s: v.s };
  else if (cfg.dat && v.s != null) cfg.dat(v.s, args || []);
}
/* Man nao dung trang thai ngay trong ham cua no (nhap kho theo phieu, form
   hoan tien...) thi goi ham nay ngay sau khi dung xong, truoc khi ve. */
function sdGhep(loai, giaTri) {
  var g = SD.ghepCho;
  if (!g || g.loai !== loai || g.s == null) return giaTri;
  SD.ghepCho = null;
  var cfg = SD_MAN[loai];
  try { return (cfg && typeof cfg.ghep === 'function') ? cfg.ghep(giaTri, g.s) : g.s; }
  catch (e) { return giaTri; }
}

function sdGio(ms) {
  var d = new Date(ms), p = function (n) { return (n < 10 ? '0' : '') + n; };
  return p(d.getHours()) + ':' + p(d.getMinutes()) + ' ngày ' + p(d.getDate()) + '/' + p(d.getMonth() + 1);
}
function sdBaoAnh(rec) {
  if (rec && rec.anh) { try { toast('Đã mở lại bản nháp. Ảnh chụp chưa lưu được trong bản nháp, chụp lại giúp nhé.', 6000); } catch (e) { } }
  else { try { toast('Đã mở lại bản đang soạn lúc ' + sdGio(rec.luc), 3500); } catch (e) { } }
}
function sdHoi(cfg, rec) {
  return hoiChon('Có ' + (cfg.ten || 'phiếu').toLowerCase() + ' đang soạn dở',
    'Máy đã tự lưu bản nháp lúc <b>' + h(sdGio(rec.luc)) + '</b>' +
    (rec.tieu_de ? ': <b>' + h(rec.tieu_de) + '</b>' : '') + '. Mở tiếp để làm nốt, không phải gõ lại.',
    [
      { k: 'tiep', icon: '📝', nhan: 'Mở tiếp bản đang soạn',
        mo_ta: 'Điền lại đúng những gì đã gõ' + (rec.anh ? '. Ảnh chụp cần chụp lại' : '') },
      { k: 'moi', icon: '📄', nhan: 'Soạn mới từ đầu',
        mo_ta: 'Bản cũ vẫn giữ ở mục Phiếu đang soạn dở trên trang chủ' }
    ]);
}
/* Soan moi: chuyen ban cu sang khoa rieng, KHONG xoa. */
function sdCatRieng(dk, rec) {
  if (sdGhi(dk + '~' + rec.luc, rec)) sdXoa(dk);
}

/* ---- boc man hinh ---- */
async function sdMoMan(loai, ten, goc, self, args, top) {
  var cfg = SD_MAN[loai];
  var mo = SD.moNgay; SD.moNgay = null;
  if (mo && mo.loai !== loai) mo = null;
  var rec = mo ? sdDoc(mo.dk) : null;
  var v = rec ? sdMoJs(rec) : null;
  if (v) sdNapLai(cfg, loai, v, args);
  var kq = await goc.apply(self, args);
  SD.ghepCho = null;
  if (sdDinh() !== top) return kq;
  if (v) {
    /* Mo tu the tren trang chu: khong hoi nua, nguoi ta vua chon ban nay. */
    sdDangKy(loai, ten, mo.dk, top, args, '', rec.ma);
    SD.daGhi = 1;
    sdApO(sdGoc(), v.o, cfg.phat);
    sdBaoAnh(rec);
    return kq;
  }
  var ma = sdMa(cfg, args), dk = sdKhoa(loai, ma);
  if (!sdNguoi()) return kq;
  var c = sdChup(loai, document.getElementById('vgbBody'));
  var nen = c ? c.js : '';
  var cu = sdDoc(dk);
  if (!cu || cu.js === nen) {
    sdDangKy(loai, ten, dk, top, args, nen, ma);
    if (cu) SD.daGhi = 1;
    return kq;
  }
  var chon = await sdHoi(cfg, cu);
  if (sdDinh() !== top) return kq;
  if (chon === 'tiep') {
    var v2 = sdMoJs(cu);
    sdDangKy(loai, ten, dk, top, args, nen, ma);
    SD.daGhi = 1;
    sdNapLai(cfg, loai, v2, args);
    await goc.apply(self, args);
    SD.ghepCho = null;
    sdApO(sdGoc(), v2.o, cfg.phat);
    sdBaoAnh(cu);
    return kq;
  }
  sdCatRieng(dk, cu);
  sdDangKy(loai, ten, dk, top, args, nen, ma);
  return kq;
}

function sdBoc(loai, ten, goc) {
  var boc = async function () {
    var args = Array.prototype.slice.call(arguments), self = this;
    var top = sdDinh();
    /* Van la ban dang soan: ve lai sau khi chon, sang buoc sau, lui buoc truoc. */
    if (SD.dk && !SD.laHop && SD.loai === loai) {
      SD.fn = top; SD.man = ten; SD.args = args;
      return goc.apply(self, args);
    }
    /* Quay ve tu man con (chon khach, chon hang...): dang ky lai im lang. */
    if (SD.roi && SD.roi.loai === loai && SD.roi.fn === top) {
      var r0 = SD.roi; SD.roi = null;
      sdDangKy(loai, ten, r0.dk, top, args, r0.nen, r0.ma);
      SD.daGhi = r0.daGhi; SD.oCu = r0.oCu;
      return goc.apply(self, args);
    }
    return sdMoMan(loai, ten, goc, self, args, top);
  };
  SD_BOC[ten] = boc;
  return boc;
}

function sdCacHop() { try { return Array.prototype.slice.call(document.querySelectorAll('.sh')); } catch (e) { return []; } }
function sdHopMoi(truoc) {
  var nay = sdCacHop();
  for (var i = nay.length - 1; i >= 0; i--) if (truoc.indexOf(nay[i]) < 0) return nay[i];
  return null;
}
function sdBocHop(loai, ten, goc) {
  var boc = async function () {
    var args = Array.prototype.slice.call(arguments), self = this, cfg = SD_MAN[loai];
    if (SD.dk) { if (SD.hen) sdLuuNgay(); sdThoi(); }
    var mo = SD.moNgay; SD.moNgay = null;
    if (mo && mo.loai !== loai) mo = null;
    var rec = mo ? sdDoc(mo.dk) : null;
    var v = rec ? sdMoJs(rec) : null;
    var truoc = sdCacHop();
    if (v) sdNapLai(cfg, loai, v, args);
    var kq = await goc.apply(self, args);
    SD.ghepCho = null;
    var hop = cfg.hop ? cfg.hop() : sdHopMoi(truoc);
    if (!hop || !sdConGan(hop)) return kq;
    if (v) {
      sdDangKy(loai, ten, mo.dk, null, args, '', rec.ma, 1, hop);
      SD.daGhi = 1;
      sdApO(hop, v.o, cfg.phat);
      sdBaoAnh(rec);
      return kq;
    }
    var ma = sdMa(cfg, args), dk = sdKhoa(loai, ma);
    if (!sdNguoi()) return kq;
    var c = sdChup(loai, hop), nen = c ? c.js : '';
    var cu = sdDoc(dk);
    if (!cu || cu.js === nen) {
      sdDangKy(loai, ten, dk, null, args, nen, ma, 1, hop);
      if (cu) SD.daGhi = 1;
      return kq;
    }
    var chon = await sdHoi(cfg, cu);
    if (!sdConGan(hop) && !(cfg.hop && cfg.hop())) return kq;
    if (chon === 'tiep') {
      var v2 = sdMoJs(cu);
      try { if (cfg.dong) cfg.dong(); else hop.remove(); } catch (e) { }
      truoc = sdCacHop();
      sdNapLai(cfg, loai, v2, args);
      await goc.apply(self, args);
      SD.ghepCho = null;
      hop = cfg.hop ? cfg.hop() : sdHopMoi(truoc);
      if (!hop) return kq;
      sdDangKy(loai, ten, dk, null, args, nen, ma, 1, hop);
      SD.daGhi = 1;
      sdApO(hop, v2.o, cfg.phat);
      sdBaoAnh(cu);
      return kq;
    }
    sdCatRieng(dk, cu);
    sdDangKy(loai, ten, dk, null, args, nen, ma, 1, hop);
    return kq;
  };
  SD_BOC[ten] = boc;
  return boc;
}

/* ---- the "Phieu dang soan do" tren trang chu ---- */
function sdVeThe() {
  if (sdDinh() !== scrHome) return;
  var body = document.getElementById('vgbBody');
  if (!body) return;
  var cu = document.getElementById('sdThe');
  if (cu) cu.remove();
  var ds = sdDs().filter(function (r) { return !!SD_MAN[r.loai]; });
  if (!ds.length) return;
  var the = document.createElement('div');
  the.id = 'sdThe';
  var html = '<div class="sec">Phiếu đang soạn dở (' + ds.length + ')</div><div class="card">';
  ds.forEach(function (r) {
    var cfg = SD_MAN[r.loai];
    html += '<div class="hub" data-sdmo="' + h(r.khoa) + '"><div class="hi">📝</div>' +
      '<div class="ht"><div class="h1">' + h(cfg.ten + (r.tieu_de ? ' · ' + r.tieu_de : '')) + '</div>' +
      '<div class="h2">Tự lưu lúc ' + h(sdGio(r.luc)) + (r.anh ? ' · ảnh cần chụp lại' : '') + '. Bấm để làm tiếp</div></div>' +
      '<button class="ic" data-sdbo="' + h(r.khoa) + '" aria-label="Bỏ bản nháp" ' +
      'style="flex:none;width:44px;height:44px;min-width:44px;border:0;background:none;color:#a0a6b4;font-size:18px">&times;</button></div>';
  });
  html += '</div>';
  the.innerHTML = html;
  the.onclick = function (e) {
    var bo = e.target.closest('[data-sdbo]');
    if (bo) {
      if (e.stopPropagation) e.stopPropagation();
      var kb = bo.getAttribute('data-sdbo');
      return confirmSheet('Bỏ bản nháp này?', 'Bỏ rồi không lấy lại được.', 'Bỏ bản nháp', true)
        .then(function (ok) { if (ok) { sdXoa(kb); sdVeThe(); } });
    }
    var mo = e.target.closest('[data-sdmo]');
    if (mo) return sdMoLai(mo.getAttribute('data-sdmo'));
  };
  body.insertBefore(the, body.firstChild);
}
function sdMoLai(k) {
  var r = sdDoc(k);
  if (!r) { toast('Bản nháp này không còn nữa'); return sdVeThe(); }
  var cfg = SD_MAN[r.loai], boc = SD_BOC[r.man];
  if (!cfg || !boc) return toast('Màn này không mở lại được bản nháp');
  SD.moNgay = { loai: r.loai, dk: k };
  var args = r.args || [];
  if (cfg.laHop) return boc.apply(null, args);
  if (cfg.mo) return cfg.mo(boc, args, r);
  if (!args.length) return go(boc);
  return go(function () { return boc.apply(null, args); });
}

/* ---- boc khung app, MOT lan ---- */
var sdApiGoc = api;
api = async function (method, args) {
  var dk = SD.dk, loai = SD.loai;
  var kq = await sdApiGoc(method, args);
  try { if (dk && sdLaLuu(loai, method, args) && sdDaTaoPhieu(kq)) sdDaLuu(dk); } catch (e) { }
  return kq;
};

var sdFrameGoc = frame;
frame = function (title, bodyHtml, opt) {
  var top = sdDinh();
  if (SD.roi && S.stack.indexOf(SD.roi.fn) < 0) SD.roi = null;
  if (SD.dk && !SD.laHop && top !== SD.fn) {
    /* Roi man dang soan. Con thay doi chua ghi thi ghi not TRUOC khi khung
       moi xoa man cu. Man cu con trong chong (man con nhu chon khach) thi
       nho lai de quay ve dang ky tiep, khong hoi lai. */
    if (SD.hen) sdLuuNgay(true);
    SD.roi = (S.stack.indexOf(SD.fn) >= 0)
      ? { loai: SD.loai, dk: SD.dk, fn: SD.fn, nen: SD.nen, ma: SD.ma, daGhi: SD.daGhi, oCu: SD.oCu }
      : null;
    sdThoi();
  }
  var r = sdFrameGoc(title, bodyHtml, opt);
  if (SD.dk && !SD.laHop && sdDinh() === SD.fn) sdHen();
  return r;
};

var sdGomGoc = vgbGomNhom;
vgbGomNhom = function () {
  var r = sdGomGoc.apply(this, arguments);
  try { sdVeThe(); } catch (e) { }
  return r;
};

document.addEventListener('input', function () { if (SD.dk) sdHen(); }, true);
document.addEventListener('change', function () { if (SD.dk) sdHen(); }, true);
/* Bam: ghi not phan dang cho TRUOC khi nut chay (nut dong hop, nut lui xoa
   mat o nhap), roi hen ghi lai sau khi nut da doi trang thai. */
document.addEventListener('click', function () { if (!SD.dk) return; if (SD.hen) sdLuuNgay(); sdHen(); }, true);
window.addEventListener('pagehide', function () { sdLuuNgay(); });
window.addEventListener('beforeunload', function () { sdLuuNgay(); });
document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'hidden') sdLuuNgay(); });

/* ---- danh sach man lap phieu ----
   Moi dong: ten hien thi, doc/dat trang thai, ham may chu luu thanh cong.
   Them man lap phieu moi thi them mot dong o day; ca kiem
   thu_ban_soan_do_533.py doi chieu danh sach nay voi cac man lap phieu. */
function sdChon(o, cac) { var r = {}; cac.forEach(function (k) { if (o && Object.prototype.hasOwnProperty.call(o, k)) r[k] = o[k]; }); return r; }
function sdGan(o, v) { if (o && v) Object.keys(v).forEach(function (k) { o[k] = v[k]; }); }
/* Tieu de tren the: uu tien chu dang go (so lieu o, khoa '#id'), roi toi
   truong trong trang thai. */
function sdTieuDe() {
  var cac = Array.prototype.slice.call(arguments);
  return function (v, o) {
    for (var i = 0; i < cac.length; i++) {
      var k = cac[i], x = (k.charAt(0) === '#') ? (o && o[k]) : (v && v[k]);
      if (x && typeof x === 'string' && x.trim()) return x.trim();
    }
    return '';
  };
}
function sdKhai(loai, man, cfg) { SD_MAN[loai] = cfg; cfg.man = man; }

sdKhai('bao_gia', 'scrBgSua', {
  ten: 'Báo giá', lay: function () { return bgTay; },
  dat: function (v) { bgTay = v; bgMoRong = {}; },
  ma: function (a) { return a[0] || (bgTay && bgTay.name) || ''; },
  tieuDe: sdTieuDe('#bgf_ten', '#bgf_ten_khach', 'ten', 'ten_khach'), luu: ['vagabond.bao_gia.luu']
});
sdKhai('thu_vien_bg', 'scrTvSua', {
  ten: 'Mục thư viện báo giá', lay: function () { return tvTay; },
  dat: function (v) { tvTay = v; }, ma: function (a) { return a[0] || ''; },
  tieuDe: sdTieuDe('ten_vi', 'ten_en'), luu: ['vagabond.bao_gia.tv_luu']
});
sdKhai('phieu_kho', 'scrStep1', {
  ten: 'Phiếu yêu cầu',
  lay: function () { if (!S.draft) return null; var o = {}; sdGan(o, S.draft); delete o.T; return o; },
  dat: function (v) { v.T = typeOf(v.type); v.items = v.items || []; v.photos = v.photos || []; S.draft = v; },
  ma: function () { return (S.draft && S.draft.type) || ''; },
  tieuDe: function (v) { return v ? (typeOf(v.type).title + ' · ' + (v.items || []).length + ' món') : ''; },
  mo: function (boc) { go(boc); },
  luu: [sdChen('Material Request')]
});
sdKhai('xuat_huy', 'scrXkHuyNew', {
  ten: 'Phiếu xuất huỷ', lay: function () { return sdChon(XK, ['gio', 'kho', 'lyDo', 'ghiChu', 'anh']); },
  dat: function (v) { sdGan(XK, v); }, tieuDe: function (v) { return v ? (v.gio || []).length + ' món' : ''; },
  luu: ['vagabond.xuat_kho.luu_xuat_huy']
});
sdKhai('dieu_chuyen', 'scrXkCkNew', {
  ten: 'Phiếu điều chuyển', lay: function () { return sdChon(XK, ['gio', 'kho', 'khoNhan', 'ghiChu', 'yc']); },
  dat: function (v) { sdGan(XK, v); }, tieuDe: function (v) { return v ? (v.gio || []).length + ' món' : ''; },
  luu: ['vagabond.xuat_kho.luu_dieu_chuyen']
});
sdKhai('mua_phat_sinh', 'scrRndNew', {
  ten: 'Phiếu mua hàng phát sinh', lay: function () { return rnd.newf; }, dat: function (v) { rnd.newf = v; },
  tieuDe: sdTieuDe('muc_dich'), luu: [sdChen('RnD Purchase Request')]
});
sdKhai('don_tay', 'scrDsNhapTay', {
  ten: 'Đơn nhập tay', lay: function () { return dsTay; }, dat: function (v) { dsTay = v; },
  tieuDe: sdTieuDe('ten', 'ma', 'nguon'), luu: ['vagabond.ban_hang.tao_don_tay']
});
sdKhai('hop_dong', 'scrHdTao', {
  ten: 'Hợp đồng', lay: function () { return hdTay; }, dat: function (v) { hdTay = v; },
  tieuDe: sdTieuDe('ten', 'so'), luu: ['vagabond.hop_dong.tao']
});
sdKhai('hd_dieu_chinh', 'scrHdSuaSoLieu', {
  ten: 'Điều chỉnh hợp đồng', lay: function () { return hdSua; }, dat: function (v) { hdSua = v; },
  ma: function () { return (hdSua && hdSua.name) || ''; }, tieuDe: sdTieuDe('name'),
  luu: ['vagabond.hop_dong_dieu_chinh.cap_nhat_so_lieu']
});
sdKhai('hd_ghi_so', 'scrHdGhiSo', {
  ten: 'Ghi sổ hợp đồng', lay: function () { return hdGsDong === null ? null : { dong: hdGsDong, kieu: hdGsKieu }; },
  dat: function (v) { hdGsDong = v.dong || null; hdGsKieu = v.kieu || hdGsKieu; },
  ma: function (a) { return a[0] || ''; }, luu: ['vagabond.hop_dong_hoa_don.ghi_so']
});
sdKhai('van_don', 'scrVdTao', {
  ten: 'Vận đơn', lay: function () { return vdTay; }, dat: function (v) { vdTay = v; },
  tieuDe: sdTieuDe('ma', 'khach'), luu: ['vagabond.van_don.tao_van_don']
});
sdKhai('chi_phi_xe', 'scrVdChiPhi', {
  ten: 'Chi phí xăng xe', lay: function () { return cpTay; }, dat: function (v) { cpTay = v; },
  tieuDe: sdTieuDe('loai'), luu: ['vagabond.van_don.tao_chi_phi']
});
sdKhai('khuon_ds', 'scrKgTao', {
  ten: 'Chứng từ mới', lay: function () { return kgForm; }, dat: function (v) { kgForm = v; },
  ma: function () { return (kgForm && kgForm.ma) || ''; }, tieuDe: sdTieuDe('nhan'),
  luu: ['vagabond.khung.ds.tao_moi']
});
sdKhai('nha_cung_cap', 'scrNccTao', {
  ten: 'Nhà cung cấp mới', lay: function () { return nccF; }, dat: function (v) { nccF = v; },
  tieuDe: sdTieuDe('ten', 'supplier_name'), luu: ['vagabond.nha_cung_cap.tao']
});
sdKhai('de_nghi_chi', 'scrDeNghiChi', {
  ten: 'Đề nghị chi', lay: function () { return dncForm; }, dat: function (v) { dncForm = v; },
  tieuDe: sdTieuDe('dien_giai'), luu: ['vagabond.de_nghi_chi.tao']
});
sdKhai('ho_so_tt', 'scrHoSoTTTao', {
  ten: 'Hồ sơ thanh toán',
  lay: function () {
    return { ncc: hsTaoNcc, chon: hsTaoChon, ghi: hsTaoGhiChu, loai: hsTaoLoai, ung: hsTaoNguoiUng,
      tk: hsTkHoan, tkCua: hsTkCua, phieu: hsPhieuCua, hdTu: hsHdTu };
  },
  dat: function (v) {
    hsTaoNcc = v.ncc || ''; hsTaoChon = v.chon || {}; hsTaoGhiChu = v.ghi || ''; hsTaoLoai = v.loai || hsTaoLoai;
    hsTaoNguoiUng = v.ung || ''; hsTkHoan = v.tk || ''; hsTkCua = v.tkCua || ''; hsPhieuCua = v.phieu || {}; hsHdTu = v.hdTu || '';
  },
  tieuDe: sdTieuDe('ncc', 'ung', 'ghi'), luu: ['vagabond.ho_so_tt.tao']
});
sdKhai('hoan_ung', 'scrHoanUngTao', {
  ten: 'Hồ sơ hoàn ứng',
  lay: function () { return { nguoi: huNguoi, dong: huDong, ghi: huGhiChu, tamUng: huTamUng, tk: huTkHoan, gd: huGdChon }; },
  dat: function (v) {
    huNguoi = v.nguoi || ''; huDong = v.dong || []; huGhiChu = v.ghi || ''; huTamUng = v.tamUng || 0;
    huTkHoan = v.tk || ''; huGdChon = v.gd || {};
  },
  tieuDe: sdTieuDe('nguoi', 'ghi'), luu: ['vagabond.ho_so_tt.tao_hoan_ung']
});
sdKhai('chi_cong_ty', 'scrChiCongTyTao', {
  ten: 'Chi từ TK công ty',
  lay: function () {
    return { nguoi: huNguoi, tkChi: huTkChi, cpThue: huCpThue, veSau: huVeSau, chonHd: huChonHd, dong: huDong, ghi: huGhiChu };
  },
  dat: function (v) {
    huNguoi = v.nguoi || ''; huTkChi = v.tkChi || ''; huCpThue = v.cpThue || ''; huVeSau = v.veSau || 0;
    huChonHd = v.chonHd || {}; huDong = v.dong || []; huGhiChu = v.ghi || '';
  },
  tieuDe: sdTieuDe('nguoi', 'ghi'), luu: ['vagabond.ho_so_tt.tao', 'vagabond.ho_so_tt.tao_chi_cong_ty']
});
sdKhai('but_toan', 'scrBtLap', {
  ten: 'Bút toán', lay: function () { return { dong: btDong, mau: btMau, ngay: btNgay, dg: btDienGiai }; },
  dat: function (v) { btDong = v.dong || []; btMau = v.mau || null; btNgay = v.ngay || btNgay; btDienGiai = v.dg || ''; },
  tieuDe: sdTieuDe('dg'), luu: ['vagabond.but_toan.tao']
});
sdKhai('nop_quy', 'scrNopQuyTao', { ten: 'Phiếu nộp quỹ', phat: 1, luu: ['vagabond.nop_quy.tao'] });
sdKhai('nop_quy_sua', 'scrNopQuySua', {
  ten: 'Sửa phiếu nộp quỹ', phat: 1, ma: function () { return nqSuaMa || ''; }, luu: ['vagabond.nop_quy.sua']
});
sdKhai('cong_thuc', 'scrCongThucSua', {
  ten: 'Công thức', lay: function () { return ctE; }, dat: function (v) { ctE = v; },
  ma: function () { return ctE ? (ctE.bom || ('mon-' + ctE.ma)) : ''; }, tieuDe: sdTieuDe('ten', 'ma'),
  luu: ['vagabond.cong_thuc.tao_moi', 'vagabond.cong_thuc.sua_nhap', 'vagabond.cong_thuc.ghi_so']
});
sdKhai('tra_truoc', 'scrTraTruocTao', {
  ten: 'Thanh toán trước NCC',
  lay: function () { return { don: ttDon, ct: ttChiTiet, tien: ttSoTien, nguon: ttNguon, loaiCt: ttLoaiCt, tep: ttTep, ghi: ttGhiChu }; },
  dat: function (v) {
    ttDon = v.don || ''; ttChiTiet = v.ct || null; ttSoTien = v.tien || 0; ttNguon = v.nguon || '';
    ttLoaiCt = v.loaiCt || ''; ttTep = v.tep || []; ttGhiChu = v.ghi || '';
  },
  tieuDe: sdTieuDe('don', 'ghi'), luu: ['vagabond.tra_truoc.tao_phieu']
});
sdKhai('xuat_tiec', 'scrTiecXuat', {
  ten: 'Xuất nguyên liệu tiệc', lay: function () { return tcX; }, dat: function (v) { tcX = v; },
  ma: function () { return (tcX && tcX.hop_dong) || ''; }, tieuDe: sdTieuDe('ten'), luu: ['vagabond.tiec.xuat_nvl']
});
sdKhai('tang_qua', 'scrTqSua', {
  ten: 'Phiếu tặng quà', lay: function () { return tq.form; }, dat: function (v) { tq.form = v; },
  ma: function () { return (tq.form && (tq.form.name || tq.form.ma)) || ''; }, tieuDe: sdTieuDe('ten_khach', 'ten', 'name'),
  luu: ['vagabond.tang_qua.luu']
});
sdKhai('dot_tang_qua', 'scrTqLapDot', {
  ten: 'Đợt tặng quà', lay: function () { return tqd.form; }, dat: function (v) { tqd.form = v; },
  ma: function () { return (tqd.form && tqd.form.name) || ''; }, tieuDe: sdTieuDe('ten_dot', 'ten', 'name'),
  luu: ['vagabond.tang_qua.luu_dot']
});
sdKhai('bien_nhan_tien', 'scrBntTao', { ten: 'Biên nhận nộp tiền', phat: 1, luu: ['vagabond.nop_quy.tao_theo_ngay'] });
sdKhai('kpi_tu_khai', 'scrKPITuKhai', { ten: 'Phiếu tự khai KPI', phat: 1, luu: ['vagabond.kpi.tu_khai'] });
sdKhai('xuat_noi_bo', 'scrXkNbNew', {
  ten: 'Phiếu xuất dùng nội bộ', lay: function () { return sdChon(XKT.nb, ['gio', 'kho', 'mucDich', 'boPhan', 'ghiChu', 'anh']); },
  dat: function (v) { sdGan(XKT.nb, v); }, tieuDe: function (v) { return v ? (v.gio || []).length + ' món' : ''; },
  luu: ['vagabond.xuat_noi_bo.luu']
});
sdKhai('tra_ncc', 'scrXkTraNew', {
  ten: 'Phiếu trả hàng NCC',
  lay: function () { return sdChon(XKT.tra, ['ncc', 'tenNcc', 'phieu', 'tenPhieu', 'lyDo', 'ghiChu', 'anh', 'dong']); },
  dat: function (v) { sdGan(XKT.tra, v); }, tieuDe: sdTieuDe('tenNcc', 'ncc'), luu: ['vagabond.tra_ncc.luu']
});
sdKhai('xuat_ban_si', 'scrXkSiNew', {
  ten: 'Phiếu giao hàng', lay: function () { return sdChon(XKT.si, ['gio', 'kho', 'khach', 'tenKhach', 'nguoiNhan', 'ghiChu']); },
  dat: function (v) { sdGan(XKT.si, v); }, tieuDe: sdTieuDe('tenKhach', 'khach'), luu: ['vagabond.xuat_ban.luu']
});
sdKhai('chot_kho_diem', 'scrXkPvNew', {
  ten: 'Chốt kho điểm bán', lay: function () { return { st: sdChon(XPV.st, ['kho', 'boPhan', 'ghiChu']), con: XPV.con }; },
  dat: function (v) { sdGan(XPV.st, v.st); XPV.con = v.con || {}; }, luu: ['vagabond.xuat_phuc_vu_ban.luu']
});
sdKhai('nhap_kho', 'scrRecvDoc', {
  ten: 'Nhập kho theo phiếu',
  lay: function () {
    if (!rcvD) return null;
    return { anh1: rcvD.anh1, anh2: rcvD.anh2, scan: rcvD.scan,
      lines: (rcvD.lines || []).map(function (x) { return { row: x.row, got: x.got, hsd: x.hsd, ok: x.ok }; }) };
  },
  ghep: function (moi, v) { return sdGhepDong(moi, v, 'row'); },
  ma: function (a) { return a[0] || ''; }, tieuDe: function () { return ''; }, luu: ['vagabond.nhan_hang.ghi_phieu_nhap']
});
sdKhai('nhan_hang', 'scrNhpDon', {
  ten: 'Nhận hàng theo đơn mua',
  lay: function () {
    if (!nhpD) return null;
    return { anh1: nhpD.anh1, anh2: nhpD.anh2, scan: nhpD.scan,
      lines: (nhpD.lines || []).map(function (x) { return { dong: x.dong, got: x.got, hsd: x.hsd, ok: x.ok }; }) };
  },
  ghep: function (moi, v) { return sdGhepDong(moi, v, 'dong'); },
  ma: function (a) { return a[0] || ''; }, luu: ['vagabond.nhan_hang.tao_phieu']
});
sdKhai('khai_sx', 'scrMfgDeclare', {
  ten: 'Khai nguyên liệu sản xuất', lay: function () { return mfgD; }, dat: function (v) { mfgD = v; },
  ma: function () { return (mfgD && mfgD.code) || ''; }, tieuDe: sdTieuDe('name', 'code'),
  luu: [sdChen('Stock Entry')]
});
/* Form hoan tien ve lai bang cach dong hop cu mo hop moi, nen hop lay theo
   bien cua form chu khong giu phan tu cu. */
var SD_HOAN = {
  ghep: function (moi, v) {
    var r = moi || {};
    ['tien', 'muc', 'ly_do', 'dien_giai', 'ten_tk', 'so_tk', 'ngan_hang', 'sdt', 'ten_khach', 'anh'].forEach(function (k) {
      if (v && Object.prototype.hasOwnProperty.call(v, k)) r[k] = v[k];
    });
    return r;
  }
};
['hoan_tien:hoanMoForm:Hoàn tiền', 'hoan_du:hoanMoFormDu:Chuyển lại tiền dư', 'hoan_huy:hoanMoFormHuy:Hoàn tiền đơn huỷ'].forEach(function (x) {
  var p = x.split(':');
  sdKhai(p[0], p[1], {
    ten: p[2], laHop: 1, lay: function () { return htF; }, ghep: SD_HOAN.ghep,
    hop: function () { return htFHop ? htFHop.ov : null; }, dong: function () { htFDong(); },
    ma: function (a) { var d = a[0]; return (d && (d.name || d)) || ''; }, tieuDe: sdTieuDe('don', 'ten_khach'),
    luu: ['vagabond.hoan_tien.tao', 'vagabond.hoan_tien.tao_huy_nhap', 'vagabond.hoan_tien.tao_tien_du']
  });
});
sdKhai('don_huy_hoan', 'dhMo', {
  ten: 'Hoàn tiền đơn đã huỷ', laHop: 1, lay: function () { return dhF; },
  ghep: function (moi, v) {
    var r = moi || {};
    ['tien', 'ly_do', 'dien_giai', 'ten_tk', 'so_tk', 'ngan_hang', 'bang_chung'].forEach(function (k) {
      if (v && Object.prototype.hasOwnProperty.call(v, k)) r[k] = v[k];
    });
    return r;
  },
  hop: function () { return dhOv; }, dong: function () { dhDong(); },
  ma: function (a) { return a[0] || ''; }, tieuDe: sdTieuDe('hien', 'ten'), luu: ['vagabond.don_huy.tao_hoan']
});
sdKhai('ctkm', 'kmSheetCtkm', {
  ten: 'Chương trình khuyến mãi', laHop: 1, lay: function () { return kmSua; },
  ghep: function (moi, v) { return v || moi; },
  ma: function (a) { return a[0] || ''; }, tieuDe: sdTieuDe('ten', 'name'), luu: ['vagabond.khuyen_mai.luu_ctkm']
});

/* Ghep so da dem cua ban nhap vao phieu vua doc lai tu may chu, theo MA DONG
   chu khong theo vi tri: phieu co the da doi tu luc luu nhap. */
function sdGhepDong(moi, v, khoa) {
  if (!moi || !v) return moi;
  ['anh1', 'anh2', 'scan'].forEach(function (k) { if (v[k]) moi[k] = v[k]; });
  var m = {};
  (v.lines || []).forEach(function (x) { if (x && x[khoa] != null) m[x[khoa]] = x; });
  (moi.lines || []).forEach(function (x) {
    var c = m[x[khoa]]; if (!c) return;
    if (c.got != null) x.got = c.got;
    if (c.hsd != null) x.hsd = c.hsd;
    if (c.ok != null) x.ok = c.ok;
  });
  return moi;
}

/* Boc that. Ten ham giu nguyen nen go(scrBgSua), manSoan(), huManHienTai()...
   deu tro vao ban da boc vi chung doc ten luc chay, khong luc nap. */
scrBgSua = sdBoc('bao_gia', 'scrBgSua', scrBgSua);
scrTvSua = sdBoc('thu_vien_bg', 'scrTvSua', scrTvSua);
scrStep1 = sdBoc('phieu_kho', 'scrStep1', scrStep1);
scrStep2 = sdBoc('phieu_kho', 'scrStep2', scrStep2);
scrStep3 = sdBoc('phieu_kho', 'scrStep3', scrStep3);
scrStep4 = sdBoc('phieu_kho', 'scrStep4', scrStep4);
scrXkHuyNew = sdBoc('xuat_huy', 'scrXkHuyNew', scrXkHuyNew);
scrXkCkNew = sdBoc('dieu_chuyen', 'scrXkCkNew', scrXkCkNew);
scrRndNew = sdBoc('mua_phat_sinh', 'scrRndNew', scrRndNew);
scrDsNhapTay = sdBoc('don_tay', 'scrDsNhapTay', scrDsNhapTay);
scrHdTao = sdBoc('hop_dong', 'scrHdTao', scrHdTao);
scrHdSuaSoLieu = sdBoc('hd_dieu_chinh', 'scrHdSuaSoLieu', scrHdSuaSoLieu);
scrHdGhiSo = sdBoc('hd_ghi_so', 'scrHdGhiSo', scrHdGhiSo);
scrVdTao = sdBoc('van_don', 'scrVdTao', scrVdTao);
scrVdChiPhi = sdBoc('chi_phi_xe', 'scrVdChiPhi', scrVdChiPhi);
scrKgTao = sdBoc('khuon_ds', 'scrKgTao', scrKgTao);
scrNccTao = sdBoc('nha_cung_cap', 'scrNccTao', scrNccTao);
scrDeNghiChi = sdBoc('de_nghi_chi', 'scrDeNghiChi', scrDeNghiChi);
scrHoSoTTTao = sdBoc('ho_so_tt', 'scrHoSoTTTao', scrHoSoTTTao);
scrHoanUngTao = sdBoc('hoan_ung', 'scrHoanUngTao', scrHoanUngTao);
scrChiCongTyTao = sdBoc('chi_cong_ty', 'scrChiCongTyTao', scrChiCongTyTao);
scrBtLap = sdBoc('but_toan', 'scrBtLap', scrBtLap);
scrNopQuyTao = sdBoc('nop_quy', 'scrNopQuyTao', scrNopQuyTao);
scrNopQuySua = sdBoc('nop_quy_sua', 'scrNopQuySua', scrNopQuySua);
scrCongThucSua = sdBoc('cong_thuc', 'scrCongThucSua', scrCongThucSua);
scrTraTruocTao = sdBoc('tra_truoc', 'scrTraTruocTao', scrTraTruocTao);
scrTiecXuat = sdBoc('xuat_tiec', 'scrTiecXuat', scrTiecXuat);
scrTqSua = sdBoc('tang_qua', 'scrTqSua', scrTqSua);
scrTqLapDot = sdBoc('dot_tang_qua', 'scrTqLapDot', scrTqLapDot);
scrBntTao = sdBoc('bien_nhan_tien', 'scrBntTao', scrBntTao);
scrKPITuKhai = sdBoc('kpi_tu_khai', 'scrKPITuKhai', scrKPITuKhai);
scrXkNbNew = sdBoc('xuat_noi_bo', 'scrXkNbNew', scrXkNbNew);
scrXkTraNew = sdBoc('tra_ncc', 'scrXkTraNew', scrXkTraNew);
scrXkSiNew = sdBoc('xuat_ban_si', 'scrXkSiNew', scrXkSiNew);
scrXkPvNew = sdBoc('chot_kho_diem', 'scrXkPvNew', scrXkPvNew);
scrRecvDoc = sdBoc('nhap_kho', 'scrRecvDoc', scrRecvDoc);
scrNhpDon = sdBoc('nhan_hang', 'scrNhpDon', scrNhpDon);
scrMfgDeclare = sdBoc('khai_sx', 'scrMfgDeclare', scrMfgDeclare);
hoanMoForm = sdBocHop('hoan_tien', 'hoanMoForm', hoanMoForm);
hoanMoFormDu = sdBocHop('hoan_du', 'hoanMoFormDu', hoanMoFormDu);
hoanMoFormHuy = sdBocHop('hoan_huy', 'hoanMoFormHuy', hoanMoFormHuy);
dhMo = sdBocHop('don_huy_hoan', 'dhMo', dhMo);
kmSheetCtkm = sdBocHop('ctkm', 'kmSheetCtkm', kmSheetCtkm);

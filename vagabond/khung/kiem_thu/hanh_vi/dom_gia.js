/* DOM gia, du dung de CHAY THAT chuoi bam tren man hinh app bep.
 *
 * Vi sao co tep nay. Bo kiem thu tang khung viet bang Python va khong co DOM,
 * nen moi ca kiem dinh toi giao dien deu chi do duoc CHUOI trong ma nguon.
 * Do chuoi khong chung minh duoc hanh vi: mot bien khai ra roi khong dung van
 * qua duoc. Codex neu dung diem nay tren PR #207 va doi bang chung hanh vi.
 *
 * Day KHONG phai mot trinh duyet. No chi lam du nhung viec ma man hinh app
 * bep that su dung toi: doc HTML thanh cay, tim theo id va theo thuoc tinh,
 * gan onclick, noi va ban su kien, doc ghi value va innerHTML. Gap thu gi
 * chua lam thi bao thang chu khong lang le tra ve rong.
 */
'use strict';

var VOID = { input: 1, br: 1, img: 1, hr: 1, meta: 1, link: 1 };

function ElementGia(ten) {
  this.tagName = (ten || 'div').toUpperCase();
  this.attrs = {};
  this.children = [];
  this.parentNode = null;
  this.style = {};
  this.value = '';
  this._nghe = {};
  this.onclick = null;
  this._chu = '';
}

ElementGia.prototype.getAttribute = function (t) {
  return Object.prototype.hasOwnProperty.call(this.attrs, t) ? this.attrs[t] : null;
};
ElementGia.prototype.setAttribute = function (t, v) { this.attrs[t] = String(v); };
ElementGia.prototype.hasAttribute = function (t) {
  return Object.prototype.hasOwnProperty.call(this.attrs, t);
};

ElementGia.prototype.addEventListener = function (loai, ham) {
  (this._nghe[loai] = this._nghe[loai] || []).push(ham);
};
ElementGia.prototype.removeEventListener = function (loai, ham) {
  var ds = this._nghe[loai] || [];
  var i = ds.indexOf(ham);
  if (i >= 0) ds.splice(i, 1);
};

/* Ban su kien. Khong co bat/noi bot that: chay listener cua chinh phan tu,
   roi di nguoc len cha nhu giai doan noi bot. Du cho man nay vi cac cho bat
   su kien deu la ban than o nhap hoac mot khung cha duy nhat. */
ElementGia.prototype.dispatchEvent = function (ev) {
  ev.target = ev.target || this;
  var nut = this;
  while (nut) {
    ev.currentTarget = nut;
    (nut._nghe[ev.type] || []).slice().forEach(function (f) { f.call(nut, ev); });
    if (ev.type === 'click' && typeof nut.onclick === 'function') nut.onclick.call(nut, ev);
    if (ev._dungNoi) break;
    nut = nut.parentNode;
  }
  return !ev._daChan;
};

ElementGia.prototype.click = function () {
  return this.dispatchEvent(suKien('click', {}, this));
};

ElementGia.prototype.closest = function (chon) {
  var nut = this;
  while (nut) {
    if (nut.hasAttribute && hopBoChon(nut, chon)) return nut;
    nut = nut.parentNode;
  }
  return null;
};

ElementGia.prototype.querySelectorAll = function (chon) {
  var ra = [];
  di(this, function (n) { if (hopBoChon(n, chon)) ra.push(n); });
  return ra;
};

ElementGia.prototype.appendChild = function (con) {
  if (con.parentNode) {
    var i = con.parentNode.children.indexOf(con);
    if (i >= 0) con.parentNode.children.splice(i, 1);
  }
  con.parentNode = this;
  this.children.push(con);
  return con;
};

ElementGia.prototype.remove = function () {
  if (!this.parentNode) return;
  var i = this.parentNode.children.indexOf(this);
  if (i >= 0) this.parentNode.children.splice(i, 1);
  this.parentNode = null;
};

/* Khong co con tro that, nhung ma nguon co goi focus() nen phai co mat. */
ElementGia.prototype.focus = function () { this._daFocus = true; };
ElementGia.prototype.blur = function () { this._daFocus = false; };
ElementGia.prototype.querySelector = function (chon) {
  return this.querySelectorAll(chon)[0] || null;
};

Object.defineProperty(ElementGia.prototype, 'innerHTML', {
  get: function () { return this._html == null ? '' : this._html; },
  set: function (v) {
    this._html = String(v == null ? '' : v);
    /* PHAI don con cu TRUOC khi doc lai. `doc()` day thang vao
       `cha.children`, nen khong don thi ve lai mot khoi la con cu con
       nguyen va con moi nam ke ben: dem so phan tu ra gap doi, ma ca kiem
       nao chi hoi "co ton tai khong" thi van xanh. Bat duoc ngay 06/09/2026
       khi viet ca kiem loc trong tam truot chon ben nhan tien: go tim xong
       dem duoc 4 dong trong khi chi con dung 1 dong khop. */
    this.children = [];
    this._chu = '';
    this.children = doc(this._html, this);
  },
});

Object.defineProperty(ElementGia.prototype, 'textContent', {
  get: function () {
    var ra = this._chu || '';
    this.children.forEach(function (c) { ra += c.textContent; });
    return ra;
  },
});

Object.defineProperty(ElementGia.prototype, 'className', {
  get: function () { return this.getAttribute('class') || ''; },
  set: function (v) { this.setAttribute('class', v); },
});

Object.defineProperty(ElementGia.prototype, 'id', {
  get: function () { return this.getAttribute('id') || ''; },
  set: function (v) { this.setAttribute('id', v); },
});

function di(nut, ham) {
  nut.children.forEach(function (c) { ham(c); di(c, ham); });
}

function chonThuocTinh(chon) {
  var m = /^\[([a-zA-Z0-9_-]+)\]$/.exec(String(chon).trim());
  return m ? m[1] : null;
}

/* Bo chon. Chi ba dang, dung het cho man bep can toi: [thuoc-tinh], #id,
   .lop, va DANH SACH cac dang do ngan bang dau phay - `huNoiBang` uy quyen
   bam bang mot danh sach muoi mot bo chon nhu vay. Gap dang khac thi NEM
   LOI chu khong lang le tra ve rong, vi mot bo chon go sai ma tra ve rong
   se lam ca kiem xanh oan. */
function hopBoChon(el, chon) {
  var t = String(chon).trim();
  if (t.indexOf(',') >= 0) {
    return t.split(',').some(function (m) {
      m = m.trim();
      return m ? hopBoChon(el, m) : false;
    });
  }
  var m = /^\[([a-zA-Z0-9_-]+)\]$/.exec(t);
  if (m) return el.hasAttribute(m[1]);
  if (t.charAt(0) === '#') return el.getAttribute('id') === t.slice(1);
  if (t.charAt(0) === '.') {
    var lop = String(el.getAttribute('class') || '').split(/\s+/);
    return lop.indexOf(t.slice(1)) >= 0;
  }
  throw new Error('DOM gia chi hieu [thuoc-tinh], #id, .lop va danh sach ngan bang dau phay, khong hieu: ' + chon);
}

/* Doc HTML. Du cho markup ma man bep sinh ra: the mo co thuoc tinh trong nhay
   kep hoac nhay don, the dong, the rong. Khong lam comment, khong lam script,
   vi man bep khong sinh ra hai thu do. */
function doc(html, cha) {
  var goc = cha || new ElementGia('div');
  var ngan = [goc];
  var re = /<\/?([a-zA-Z][a-zA-Z0-9]*)((?:\s+[a-zA-Z0-9_:-]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+))?)*)\s*\/?>/g;
  var i = 0, m;
  while ((m = re.exec(html))) {
    var chu = html.slice(i, m.index);
    if (chu) ngan[ngan.length - 1]._chu += chu;
    i = m.index + m[0].length;
    var ten = m[1].toLowerCase();
    if (m[0].charAt(1) === '/') {
      if (ngan.length > 1) ngan.pop();
      continue;
    }
    var el = new ElementGia(ten);
    docThuocTinh(m[2] || '', el);
    el.parentNode = ngan[ngan.length - 1];
    el.parentNode.children.push(el);
    if (el.tagName === 'INPUT' && el.getAttribute('value') != null) el.value = el.getAttribute('value');
    if (!VOID[ten] && m[0].slice(-2) !== '/>') ngan.push(el);
  }
  var duoi = html.slice(i);
  if (duoi) ngan[ngan.length - 1]._chu += duoi;
  return goc.children;
}

function docThuocTinh(chuoi, el) {
  var re = /([a-zA-Z0-9_:-]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?/g;
  var m;
  while ((m = re.exec(chuoi))) {
    var v = m[2] != null ? m[2] : (m[3] != null ? m[3] : (m[4] != null ? m[4] : ''));
    el.attrs[m[1]] = v;
  }
}

function suKien(loai, them, dich) {
  var ev = {
    type: loai,
    target: dich || null,
    _daChan: false,
    _dungNoi: false,
    preventDefault: function () { ev._daChan = true; },
    stopPropagation: function () { ev._dungNoi = true; },
  };
  Object.keys(them || {}).forEach(function (k) { ev[k] = them[k]; });
  return ev;
}

function taiLieuGia() {
  var than = new ElementGia('body');
  return {
    body: than,
    createElement: function (t) { return new ElementGia(t); },
    getElementById: function (id) {
      var ra = null;
      di(than, function (n) { if (!ra && n.getAttribute('id') === id) ra = n; });
      return ra;
    },
    querySelectorAll: function (chon) { return than.querySelectorAll(chon); },
    querySelector: function (chon) { return than.querySelector(chon); },
    addEventListener: function () {},
    removeEventListener: function () {},
  };
}

module.exports = { ElementGia: ElementGia, taiLieuGia: taiLieuGia, suKien: suKien, doc: doc };

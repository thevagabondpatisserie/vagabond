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

/* `el.dataset.abc` đọc và ghi thuộc tính `data-abc`. Màn bếp dùng dataset
   rất nhiều (data-them, data-bo, data-q...) nên DOM giả phải có, không thì
   ca kiểm hỏng ở chỗ không liên quan gì đến việc đang kiểm.

   Thêm 06/09/2026 cho bộ ca kiểm màn tạo lệnh sản xuất (#206). Thêm mới,
   không đổi hành vi cũ của tệp này. */
Object.defineProperty(ElementGia.prototype, 'dataset', {
  get: function () {
    var el = this;
    if (el._dataset) return el._dataset;
    el._dataset = new Proxy({}, {
      get: function (_, k) {
        if (typeof k !== 'string') return undefined;
        var v = el.getAttribute('data-' + k.replace(/[A-Z]/g, function (c) { return '-' + c.toLowerCase(); }));
        return v === null ? undefined : v;
      },
      set: function (_, k, v) {
        el.setAttribute('data-' + String(k).replace(/[A-Z]/g, function (c) { return '-' + c.toLowerCase(); }), v);
        return true;
      },
      has: function (_, k) {
        return el.hasAttribute('data-' + String(k).replace(/[A-Z]/g, function (c) { return '-' + c.toLowerCase(); }));
      },
    });
    return el._dataset;
  },
});

ElementGia.prototype.getAttribute = function (t) {
  return Object.prototype.hasOwnProperty.call(this.attrs, t) ? this.attrs[t] : null;
};
ElementGia.prototype.setAttribute = function (t, v) { this.attrs[t] = String(v); };
ElementGia.prototype.removeAttribute = function (t) { delete this.attrs[t]; };
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
    /* Gọi cả thuộc tính `on<loại>` chứ không riêng `onclick`. Màn thật gán
       `inp.oninput` cho ô tìm của tấm chọn món; bản cũ chỉ gọi `onclick`
       nên bắn sự kiện input vào ô đó KHÔNG chạy gì, và ca kiểm tưởng là
       tấm chọn không tìm ra hàng. Bắt được ngày 06/09/2026 khi viết ca 26
       của màn lệnh sản xuất. */
    var ho = nut['on' + ev.type];
    if (typeof ho === 'function') ho.call(nut, ev);
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
    /* PHẢI DỌN CON CŨ TRƯỚC. doc() đẩy node mới vào chính mảng children của
       cha, nên nếu không dọn thì vẽ lại màn một cái là DOM giả giữ cả bản cũ
       lẫn bản mới. Ca kiểm nào đếm "không còn dòng nào" sẽ thấy dòng cũ còn
       nguyên và báo xanh oan, hoặc hỏng oan.
       Sửa 06/09/2026 khi dựng bộ ca kiểm màn tạo lệnh sản xuất (#206): ca
       "bỏ một món đã chọn" đếm ra 1 trong khi màn đã vẽ lại không còn dòng. */
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
  /* Gán textContent thì xoá hết con, chỉ còn chữ. Thêm cho #206 khi nút tạo
     đổi chữ tại chỗ mà không vẽ lại cả màn. */
  set: function (v) {
    this.children = [];
    this._html = '';
    this._chu = String(v == null ? '' : v);
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
   .lop. Gap dang khac thi NEM LOI chu khong lang le tra ve rong, vi mot bo
   chon go sai ma tra ve rong se lam ca kiem xanh oan. */
function hopBoChon(el, chon) {
  var t = String(chon).trim();
  /* Danh sách ngăn cách bằng dấu phẩy: khớp một phần là khớp. Màn bếp viết
     closest('[data-m],[data-p],[data-dec]') rất nhiều chỗ.
     Thêm 06/09/2026 cho bộ ca kiểm màn tạo lệnh sản xuất (#206). */
  if (t.indexOf(',') >= 0) {
    var phan = t.split(',');
    for (var i = 0; i < phan.length; i++) {
      if (phan[i].trim() && hopBoChon(el, phan[i])) return true;
    }
    return false;
  }
  var m = /^\[([a-zA-Z0-9_-]+)\]$/.exec(t);
  if (m) return el.hasAttribute(m[1]);
  /* [thuoc-tinh="gia-tri"]: màn tạo lệnh dùng để tìm ô số lượng theo chỉ
     số dòng khi bấm cộng trừ. Thêm cho #206. */
  var mg = /^\[([a-zA-Z0-9_-]+)=(?:"([^"]*)"|'([^']*)'|([^\]]*))\]$/.exec(t);
  if (mg) return el.getAttribute(mg[1]) === (mg[2] != null ? mg[2] : mg[3] != null ? mg[3] : mg[4]);
  if (t.charAt(0) === '#') return el.getAttribute('id') === t.slice(1);
  if (t.charAt(0) === '.') {
    var lop = String(el.getAttribute('class') || '').split(/\s+/);
    return lop.indexOf(t.slice(1)) >= 0;
  }
  throw new Error('DOM gia chi hieu [thuoc-tinh], [thuoc-tinh="gia-tri"], #id va .lop, khong hieu: ' + chon);
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

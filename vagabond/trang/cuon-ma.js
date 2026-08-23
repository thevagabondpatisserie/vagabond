/* Cuốn mã vạch nguyên vật liệu - Vagabond - CM v5 (co hinh anh) */
(function () {
  var CMVER = '5';

  /* ---------- Code 39 ---------- */
  var C39 = {
    '0': 'nnnwwnwnn', '1': 'wnnwnnnnw', '2': 'nnwwnnnnw', '3': 'wnwwnnnnn',
    '4': 'nnnwwnnnw', '5': 'wnnwwnnnn', '6': 'nnwwwnnnn', '7': 'nnnwnnwnw',
    '8': 'wnnwnnwnn', '9': 'nnwwnnwnn', 'A': 'wnnnnwnnw', 'B': 'nnwnnwnnw',
    'C': 'wnwnnwnnn', 'D': 'nnnnwwnnw', 'E': 'wnnnwwnnn', 'F': 'nnwnwwnnn',
    'G': 'nnnnnwwnw', 'H': 'wnnnnwwnn', 'I': 'nnwnnwwnn', 'J': 'nnnnwwwnn',
    'K': 'wnnnnnnww', 'L': 'nnwnnnnww', 'M': 'wnwnnnnwn', 'N': 'nnnnwnnww',
    'O': 'wnnnwnnwn', 'P': 'nnwnwnnwn', 'Q': 'nnnnnnwww', 'R': 'wnnnnnwwn',
    'S': 'nnwnnnwwn', 'T': 'nnnnwnwwn', 'U': 'wwnnnnnnw', 'V': 'nwwnnnnnw',
    'W': 'wwwnnnnnn', 'X': 'nwnnwnnnw', 'Y': 'wwnnwnnnn', 'Z': 'nwwnwnnnn',
    '-': 'nwnnnnwnw', '.': 'wwnnnnwnn', ' ': 'nwwnnnwnn', '$': 'nwnwnwnnn',
    '/': 'nwnwnnnwn', '+': 'nwnnnwnwn', '%': 'nnnwnwnwn', '*': 'nwnnwnwnn'
  };

  function c39svg(code) {
    var txt = '*' + String(code || '').toUpperCase() + '*';
    var NAR = 1, WID = 3, GAP = 1, H = 40;
    var segs = [], x = 0, i, j, ch, pat, w;
    for (i = 0; i < txt.length; i++) {
      ch = txt.charAt(i);
      pat = C39[ch];
      if (!pat) continue;
      for (j = 0; j < 9; j++) {
        w = pat.charAt(j) === 'w' ? WID : NAR;
        if (j % 2 === 0) segs.push('<rect x="' + x + '" y="0" width="' + w + '" height="' + H + '"/>');
        x += w;
      }
      x += GAP;
    }
    return '<svg viewBox="0 0 ' + x + ' ' + H + '" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges" fill="#000">' + segs.join('') + '</svg>';
  }

  /* ---------- helpers ---------- */
  function esc(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function api(method, args) {
    return fetch('/api/method/' + method, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': (window.frappe && frappe.csrf_token) || '' },
      body: JSON.stringify(args || {})
    }).then(function (r) { return r.json(); }).then(function (j) {
      if (j && j.exc) throw new Error(j.exc);
      return j.message;
    });
  }
  function getList(dt, opt) {
    var a = { doctype: dt };
    for (var k in opt) a[k] = opt[k];
    return api('frappe.client.get_list', a);
  }
  function dmy(iso) {
    if (!iso) return '';
    var p = String(iso).slice(0, 10).split('-');
    return p[2] + '/' + p[1] + '/' + p[0];
  }
  function el(id) { return document.getElementById(id); }

  /* ten file anh cua item hay co dau cach va tieng Viet, phai encode truoc khi cho vao src */
  function imgUrl(u) {
    u = String(u || '').trim();
    if (!u) return '';
    if (/^https?:/i.test(u)) return u;
    try { return encodeURI(u); } catch (e) { return u; }
  }

  /* an item counts as already carrying a manufacturer barcode when one of its
     Item Barcode rows is 8 to 13 digits and does not start with 2
     (GS1 prefixes 20-29 are restricted circulation, iPOS used 200... internally) */
  function isReal(b) {
    b = String(b || '').trim();
    return /^[0-9]{8,13}$/.test(b) && b.charAt(0) !== '2';
  }

  /* ---------- state ---------- */
  var S = {
    groups: [],      /* {name, cnt} */
    sel: {},         /* group name -> 1 */
    items: [],       /* all items of selected groups */
    real: {},        /* item_code -> first real barcode */
    withReal: 0,
    noImg: 0,        /* so mon khong co anh trong cac nhom dang chon */
    q: '',
    from: '',
    inclReal: 0,
    showImg: 1,      /* in kem hinh anh */
    onlyNoImg: 0,    /* chi hien mon chua co anh, de bep chup bo sung */
    cols: 2,
    loading: 0
  };

  /* 2 cột: vạch to gấp rưỡi, điện thoại quét chắc ăn hơn (mặc định)
     3 cột: tiết kiệm giấy, hợp với máy quét cầm tay */
  var DENSITY = {
    2: { cols: 2, per: 16, note: '2 cột · mỗi trang 16 ô · vạch to, quét bằng camera điện thoại chắc ăn hơn' },
    3: { cols: 3, per: 24, note: '3 cột · mỗi trang 24 ô · tiết kiệm giấy, hợp với máy quét cầm tay' }
  };
  /* co hinh anh thi o cao hon nen moi trang chua duoc it hon */
  var DENSITY_IMG = {
    2: { cols: 2, per: 12, note: '2 cột có hình · mỗi trang 12 ô · hình 20mm, vạch to, dễ nhận mặt hàng nhất' },
    3: { cols: 3, per: 21, note: '3 cột có hình · mỗi trang 21 ô · hình 15mm, tiết kiệm giấy hơn' }
  };
  function den() { return (S.showImg ? DENSITY_IMG : DENSITY)[S.cols] || DENSITY[2]; }

  var DEFAULT_GROUPS = ['Nguyên vật liệu Thô', 'Bao bì'];

  /* ---------- load ---------- */
  async function loadGroups() {
    var mv = await getList('Item Group', { fields: ['name', 'lft', 'rgt'], filters: { name: 'Mua vào' }, limit_page_length: 1 });
    var lft = mv && mv[0] ? mv[0].lft : 0, rgt = mv && mv[0] ? mv[0].rgt : 0;
    var gs = await getList('Item Group', {
      fields: ['name'],
      filters: { is_group: 0, lft: ['>', lft], rgt: ['<', rgt] },
      order_by: 'lft', limit_page_length: 0
    });
    var out = [];
    for (var i = 0; i < gs.length; i++) {
      var n = await api('frappe.client.get_count', { doctype: 'Item', filters: { item_group: gs[i].name, disabled: 0 } });
      if (n > 0) out.push({ name: gs[i].name, cnt: n });
    }
    S.groups = out;
    if (!Object.keys(S.sel).length) {
      DEFAULT_GROUPS.forEach(function (g) {
        if (out.some(function (o) { return o.name === g; })) S.sel[g] = 1;
      });
      if (!Object.keys(S.sel).length && out.length) S.sel[out[0].name] = 1;
    }
  }

  async function loadItems() {
    var gs = Object.keys(S.sel);
    if (!gs.length) { S.items = []; S.real = {}; S.withReal = 0; S.noImg = 0; return; }
    S.items = await getList('Item', {
      fields: ['name', 'item_name', 'stock_uom', 'item_group', 'creation', 'image'],
      filters: { item_group: ['in', gs], disabled: 0 },
      order_by: 'item_group asc, item_name asc',
      limit_page_length: 0
    });
    var bcs = [];
    try {
      bcs = await getList('Item Barcode', {
        parent: 'Item',
        fields: ['parent', 'barcode'],
        filters: { parenttype: 'Item' },
        limit_page_length: 0
      });
    } catch (e) { bcs = []; }
    var real = {};
    bcs.forEach(function (b) {
      if (!real[b.parent] && isReal(b.barcode)) real[b.parent] = String(b.barcode).trim();
    });
    S.real = real;
    var n = 0, ni = 0;
    S.items.forEach(function (it) {
      if (real[it.name]) n++;
      if (!it.image) ni++;
    });
    S.withReal = n;
    S.noImg = ni;
  }

  /* ---------- filter ---------- */
  function visible() {
    var q = S.q.trim().toLowerCase();
    return S.items.filter(function (it) {
      if (!S.inclReal && S.real[it.name]) return false;
      if (S.onlyNoImg && it.image) return false;
      if (S.from && String(it.creation).slice(0, 10) < S.from) return false;
      if (q) {
        var hay = (it.item_name + ' ' + it.name).toLowerCase();
        if (hay.indexOf(q) < 0) return false;
      }
      return true;
    });
  }

  /* ---------- render ---------- */
  function drawChips() {
    el('cmGrp').innerHTML = S.groups.map(function (g) {
      return '<button class="cmChip' + (S.sel[g.name] ? ' on' : '') + '" data-g="' + esc(g.name) + '">' +
        esc(g.name) + ' (' + g.cnt + ')</button>';
    }).join('');
    Array.prototype.forEach.call(el('cmGrp').querySelectorAll('.cmChip'), function (b) {
      b.onclick = function () {
        var g = b.getAttribute('data-g');
        if (S.sel[g]) delete S.sel[g]; else S.sel[g] = 1;
        drawChips();
        refresh();
      };
    });
  }

  function drawBcBar() {
    var n = S.withReal;
    el('cmBcBar').innerHTML =
      '<button class="cmTg' + (S.showImg ? ' on' : '') + '" id="cmTgImg">' +
      (S.showImg ? 'Đang in kèm hình ảnh' : 'In kèm hình ảnh') + '</button>' +
      '<button class="cmTg' + (S.inclReal ? ' on' : '') + '" id="cmTgReal">' +
      (S.inclReal ? 'Đang in cả hàng đã có mã NCC' : 'In cả hàng đã có mã NCC') +
      (n ? ' (' + n + ')' : '') + '</button>' +
      '<button class="cmTg' + (S.cols === 2 ? ' on' : '') + '" data-c="2">Mã to, 2 cột</button>' +
      '<button class="cmTg' + (S.cols === 3 ? ' on' : '') + '" data-c="3">Tiết kiệm giấy, 3 cột</button>' +
      (S.noImg ? '<button class="cmTg' + (S.onlyNoImg ? ' on' : '') + '" id="cmTgNo">Chỉ hiện món chưa có ảnh (' + S.noImg + ')</button>' : '');
    var ti = el('cmTgImg');
    if (ti) ti.onclick = function () { S.showImg = S.showImg ? 0 : 1; drawBcBar(); paint(); };
    var t = el('cmTgReal');
    if (t) t.onclick = function () { S.inclReal = S.inclReal ? 0 : 1; drawBcBar(); paint(); };
    var tn = el('cmTgNo');
    if (tn) tn.onclick = function () { S.onlyNoImg = S.onlyNoImg ? 0 : 1; drawBcBar(); paint(); };
    Array.prototype.forEach.call(el('cmBcBar').querySelectorAll('[data-c]'), function (b) {
      b.onclick = function () { S.cols = parseInt(b.getAttribute('data-c'), 10); drawBcBar(); paint(); };
    });
    el('cmNote').textContent = 'Mã vạch dùng chuẩn Code 39, quét được bằng máy quét cầm tay và bằng camera trong app điện thoại. ' +
      den().note + '. Mỗi nhóm hàng bắt đầu ở một trang mới.';
  }

  function drawSkip() {
    var box = el('cmSkip');
    var n = S.withReal;
    if (!n || S.inclReal) { box.className = 'cmSkip'; box.innerHTML = ''; return; }
    var ex = [];
    for (var i = 0; i < S.items.length && ex.length < 3; i++) {
      if (S.real[S.items[i].name]) ex.push(S.items[i].item_name + ' (' + S.real[S.items[i].name] + ')');
    }
    box.className = 'cmSkip show';
    box.innerHTML = 'Đã bỏ qua <b>' + n + ' món</b> vì trên bao bì đã có sẵn mã vạch của nhà sản xuất, quét thẳng trên bao bì là ra, không cần in vào cuốn. ' +
      (ex.length ? 'Ví dụ: ' + esc(ex.join(' · ')) + '. ' : '') +
      'Nếu vẫn muốn in thì bấm nút "In cả hàng đã có mã NCC" ở trên.';
  }

  function drawImgNote() {
    var box = el('cmImgN');
    if (!S.showImg || !S.noImg) { box.className = 'cmImgN'; box.innerHTML = ''; return; }
    box.className = 'cmImgN show';
    box.innerHTML = 'Còn <b>' + S.noImg + ' món</b> trong các nhóm đang chọn chưa có ảnh, in ra sẽ là ô gạch đứt ghi "chưa có ảnh". ' +
      'Muốn có ảnh thì vào thẻ hàng hoá trên ERP, mục Hình ảnh, tải ảnh lên rồi bấm Làm mới ở đây. ' +
      'Bấm nút "Chỉ hiện món chưa có ảnh" ở trên để in riêng danh sách cần chụp bổ sung.';
  }

  function cell(it) {
    var bc = '<div class="cmBc">' + c39svg(it.name) + '</div>' +
      '<div class="cmCd">' + esc(it.name) + '</div>';
    if (!S.showImg) {
      return '<div class="cmCell">' +
        '<div class="cmNm">' + esc(it.item_name || it.name) + '</div>' +
        '<div class="cmUm">ĐVT ' + esc(it.stock_uom || '') + '</div>' +
        bc + '</div>';
    }
    var pic = it.image
      ? '<div class="cmPic"><img src="' + esc(imgUrl(it.image)) + '" alt="" loading="eager" onerror="this.parentNode.className=\'cmPic no\';this.parentNode.innerHTML=\'chưa có ảnh\'"></div>'
      : '<div class="cmPic no">chưa có ảnh</div>';
    return '<div class="cmCell">' +
      '<div class="cmTop2">' + pic +
      '<div class="cmTx"><div class="cmNm">' + esc(it.item_name || it.name) + '</div>' +
      '<div class="cmUm">ĐVT ' + esc(it.stock_uom || '') + '</div></div></div>' +
      bc + '</div>';
  }

  function paint() {
    drawSkip();
    drawImgNote();
    var list = visible();
    el('cmCount').innerHTML = '<b>' + list.length + '</b> mã sẽ in' +
      (S.withReal && !S.inclReal ? ' · bỏ qua ' + S.withReal + ' món đã có mã NCC' : '');

    var wrap = el('cmPages');
    if (!list.length) {
      wrap.innerHTML = '<div class="cmEmp">' + (S.loading ? 'Đang tải danh sách hàng hoá...' : 'Không có mã nào cần in với bộ lọc hiện tại.') + '</div>';
      return;
    }
    var byG = {}, order = [];
    list.forEach(function (it) {
      var g = it.item_group || 'Khác';
      if (!byG[g]) { byG[g] = []; order.push(g); }
      byG[g].push(it);
    });

    var d = den();
    var per = d.per;
    var pages = [];
    order.forEach(function (g) {
      var arr = byG[g], tot = Math.ceil(arr.length / per);
      for (var p = 0; p < tot; p++) pages.push({ g: g, p: p + 1, tot: tot, rows: arr.slice(p * per, (p + 1) * per) });
    });

    var today = dmy(new Date().toISOString());
    var gcls = 'cmGrid' + (d.cols === 3 ? ' c3' : '') + (S.showImg ? ' img' : '');
    wrap.innerHTML = pages.map(function (pg) {
      return '<div class="cmPage"><div class="cmPh">' +
        '<div class="g">' + esc(pg.g) + '</div>' +
        '<div class="m">The Vagabond Pâtisserie<br>In ngày ' + today + ' · trang ' + pg.p + '/' + pg.tot + '</div>' +
        '</div><div class="' + gcls + '">' + pg.rows.map(cell).join('') + '</div></div>';
    }).join('');
  }

  /* doi anh tai xong roi moi mo hop thoai in, khong thi trang in ra bi trong o hinh */
  function waitImgs(ms) {
    var imgs = Array.prototype.slice.call(document.querySelectorAll('#cmPages img'));
    var pend = imgs.filter(function (im) { return !im.complete; });
    if (!pend.length) return Promise.resolve(0);
    return new Promise(function (res) {
      var left = pend.length, done = 0, fin = function () { done = 1; res(left); };
      var to = setTimeout(fin, ms || 20000);
      pend.forEach(function (im) {
        var one = function () {
          left--;
          if (left <= 0 && !done) { clearTimeout(to); fin(); }
        };
        im.addEventListener('load', one, { once: true });
        im.addEventListener('error', one, { once: true });
      });
    });
  }

  async function doPrint() {
    var b = el('cmPrint');
    if (b) { b.disabled = true; b.textContent = 'Đang tải hình...'; }
    try { await waitImgs(20000); } catch (e) { }
    if (b) { b.disabled = false; b.textContent = 'In cuốn'; }
    window.print();
  }

  async function refresh() {
    S.loading = 1;
    paint();
    try { await loadItems(); } catch (e) { }
    S.loading = 0;
    drawBcBar();
    paint();
  }

  /* ---------- boot ---------- */
  async function boot() {
    if (!el('cmWrap')) return;
    el('cmQ').oninput = function () { S.q = this.value; paint(); };
    el('cmFrom').onchange = function () { S.from = this.value; paint(); };
    el('cmReload').onclick = function () { refresh(); };
    el('cmPrint').onclick = function () { doPrint(); };
    S.loading = 1;
    paint();
    try { await loadGroups(); } catch (e) { }
    drawChips();
    await refresh();
    if (window.console) console.log('[cuon-ma] v' + CMVER + ' ready');
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();

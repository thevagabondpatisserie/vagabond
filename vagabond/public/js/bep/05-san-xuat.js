/* ---------- 12. Tra ton kho ---------- */
var stk = { wh: 'Kho tổng 307 - TV', q: '' };
async function scrStock() {
  frame('Tra tồn kho', '<div class="emp"><div class="e1">⏳</div></div>');
  var rows = await getList('Bin', { fields: ['item_code', 'actual_qty', 'stock_uom'], filters: { warehouse: stk.wh, actual_qty: ['!=', 0] }, limit_page_length: 0, order_by: 'item_code' });
  var codes = rows.map(function (r) { return r.item_code; });
  var names = {};
  for (var ci = 0; ci < codes.length; ci += 400) {
    var lot = codes.slice(ci, ci + 400);
    var its = await getList('Item', { fields: ['name', 'item_name'], filters: { name: ['in', lot] }, limit_page_length: 0 });
    its.forEach(function (i) { names[i.name] = i.item_name; });
  }
  function draw() {
    var q = stk.q.toLowerCase();
    var f = rows.filter(function (r) { return !q || ((names[r.item_code] || '') + ' ' + r.item_code).toLowerCase().indexOf(q) >= 0; }).slice(0, 250);
    var b = frame('Tra tồn kho',
      '<div class="card"><div class="fld" data-w><div class="fi">🏬</div><div class="ft"><div class="fl">Kho</div>' +
      '<div class="fv">' + h(shortWh(stk.wh)) + '</div></div><div class="fc">&#8250;</div></div></div>' +
      srchBox('sq', 'Tìm hàng hoá', stk.q, true) +
      (f.length ? '<div class="lst">' + f.map(function (r) {
        return '<div class="li"><div class="lt"><div class="l1">' + h(names[r.item_code] || r.item_code) + '</div>' +
          '<div class="l2">Mã: ' + h(r.item_code) + '</div></div>' +
          '<div style="text-align:right"><div class="amt">' + num(r.actual_qty) + '</div>' +
          '<div class="l2">' + h(r.stock_uom) + '</div></div></div>';
      }).join('') + '</div>' : '<div class="emp"><div class="e1">📦</div><div class="e2">Kho này chưa có tồn</div></div>'));
    var sq = document.getElementById('sq');
    var tm = null;
    sq.oninput = function () { stk.q = sq.value; clearTimeout(tm); tm = setTimeout(function () { var v = stk.q; draw(); var i = document.getElementById('sq'); i.focus(); i.value = v; i.setSelectionRange(v.length, v.length); }, 200); };
    document.getElementById('sqscan').onclick = async function () {
      var code = await scanBarcode();
      if (!code) return;
      busy(1);
      var ic = null;
      try { ic = await itemByBarcode(code); } catch (e) { }
      busy(0);
      stk.q = ic || code;
      if (!ic) toast('Không tìm thấy hàng hoá có mã vạch này');
      draw();
    };
    b.onclick = function (e) {
      if (e.target.closest('[data-w]')) sheet('Chọn kho', whOpts(), stk.wh, function (o) { stk.wh = o.value; stk.q = ''; scrStock(); }, true);
    };
  }
  draw();
}

/* ---------- 12b. Bang bep ---------- */
function isBep() { return hasRole('Bếp phó') || hasRole('Manufacturing User') || hasRole('Manufacturing Manager') || hasRole('System Manager'); }
function nowStamp() {
  var d = new Date(), p = function (n) { return ('0' + n).slice(-2); };
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) + ' ' + p(d.getHours()) + ':' + p(d.getMinutes()) + ':' + p(d.getSeconds());
}
var kit = { date: '', mine: 1 };

async function scrKitchen() {
  if (!kit.date) kit.date = today();
  var td = today();
  frame('Bảng bếp', '<div class="emp"><div class="e1">⏳</div></div>');

  var meBep = myKitchen();
  var docs = await getList('Material Request', {
    fields: ['name', 'schedule_date', 'set_warehouse', 'bo_phan_yeu_cau', 'nguoi_yeu_cau', 'trang_thai_bep', 'status', 'custom_bep_nhan'],
    filters: { material_request_type: 'Manufacture', docstatus: 1, schedule_date: kit.date },
    limit_page_length: 0, order_by: 'creation asc'
  });
  var tong = docs.length;
  if (meBep && kit.mine) docs = docs.filter(function (x) { return bepSeesRow(x.custom_bep_nhan); });
  var an = tong - docs.length;
  var late = [];
  try {
    var lt = await getList('Material Request', {
      fields: ['name', 'trang_thai_bep', 'custom_bep_nhan'],
      filters: { material_request_type: 'Manufacture', docstatus: 1, schedule_date: ['<', td] },
      limit_page_length: 0
    });
    late = lt.filter(function (x) { return x.trang_thai_bep !== 'Đã xong' && (!meBep || !kit.mine || bepSeesRow(x.custom_bep_nhan)); });
  } catch (e) { }

  var names = docs.map(function (d) { return d.name; });
  var lines = [];
  if (names.length) {
    lines = await getList('Material Request Item', {
      parent: 'Material Request',
      fields: ['name', 'parent', 'item_code', 'item_name', 'qty', 'uom', 'gio_can_lay', 'warehouse', 'bep_da_lam'],
      filters: { parent: ['in', names] }, limit_page_length: 0
    });
  }
  var byDoc = {}; docs.forEach(function (d) { byDoc[d.name] = d; });

  var groups = {}, order = [];
  lines.forEach(function (l) {
    var k = l.item_code + '|' + l.uom;
    if (!groups[k]) { groups[k] = { code: l.item_code, name: l.item_name || l.item_code, uom: l.uom, qty: 0, rows: [], gio: '99:99' }; order.push(k); }
    var g = groups[k];
    g.qty += (l.qty || 0);
    g.rows.push(l);
    var t = hm(l.gio_can_lay) || '99:99';
    if (t < g.gio) g.gio = t;
  });
  order.sort(function (a, b) {
    if (groups[a].gio !== groups[b].gio) return groups[a].gio < groups[b].gio ? -1 : 1;
    return groups[a].name.localeCompare(groups[b].name, 'vi');
  });
  function gDone(k) { return groups[k].rows.every(function (r) { return !!r.bep_da_lam; }); }
  function docDone(n) {
    var rs = lines.filter(function (l) { return l.parent === n; });
    return rs.length > 0 && rs.every(function (r) { return !!r.bep_da_lam; });
  }

  function draw() {
    var doneN = order.filter(gDone).length, allN = order.length;
    var pct = allN ? Math.round(doneN * 100 / allN) : 0;
    var chips = [['prev', 'Hôm qua', addDays(td, -1)], ['td', 'Hôm nay', td], ['tm', 'Ngày mai', addDays(td, 1)]]
      .map(function (c) { return '<div class="chip' + (kit.date === c[2] ? ' on' : '') + '" data-d="' + c[2] + '">' + c[1] + '</div>'; }).join('') +
      '<div class="chip" data-pick>📅 ' + dmy(kit.date) + '</div>' +
      (meBep ? '<div class="chip' + (kit.mine ? ' on' : '') + '" data-bep>' + (kit.mine ? '🧑‍🍳 ' + meBep : '👥 Tất cả bếp') + '</div>' : '');

    var warn = (late.length && kit.date === td) ?
      '<div class="kwn">⚠️ Còn ' + late.length + ' phiếu của những ngày trước chưa xác nhận xong. Bấm vào chip Hôm qua để xem.</div>' : '';
    if (meBep && kit.mine && an > 0) warn += '<div class="kwn" style="background:#E4F9FD;color:#05323C">Đang lọc phiếu gửi cho ' + h(meBep) + '. Còn ' + an + ' phiếu gửi cho bếp khác, bấm chip bên trên để xem tất cả.</div>';

    var body = '<div class="kbar">' + chips + '</div>' + warn;

    if (!allN) {
      body += '<div class="emp"><div class="e1">🎂</div><div class="e2">Ngày ' + dmy(kit.date) + ' chưa có phiếu sản xuất nào</div></div>';
    } else {
      body += '<div class="card"><div class="kpg"><div class="kpt">ĐÃ LÀM ' + doneN + '/' + allN + ' MÓN &middot; TỔNG ' + docs.length + ' PHIẾU</div>' +
        '<div class="kpb"><i style="width:' + pct + '%"></i></div></div></div>';
      body += '<div class="sec">Cần làm - gộp theo món</div><div class="card">' +
        order.map(function (k) {
          var g = groups[k];
          var det = g.rows.map(function (r) {
            var d = byDoc[r.parent] || {};
            return h(shortWh(r.warehouse || d.set_warehouse)) + ' ' + num(r.qty) + (hm(r.gio_can_lay) ? ' lúc ' + hm(r.gio_can_lay) : '');
          }).join(' &middot; ');
          return '<div class="kc' + (gDone(k) ? ' on' : '') + '" data-g="' + h(k) + '">' +
            '<div class="ktk">&#10003;</div>' +
            '<div class="kb"><div class="kn">' + h(g.name) + '</div><div class="kd">' + det + '</div></div>' +
            '<div class="kq"><b>' + num(g.qty) + '</b><small>' + h(g.uom) + '</small></div></div>';
        }).join('') + '</div>';
      body += '<div class="sec">Phiếu trong ngày</div><div class="card"><div class="lst">' +
        docs.map(function (d) {
          var rs = lines.filter(function (l) { return l.parent === d.name; });
          var dn = rs.filter(function (r) { return !!r.bep_da_lam; }).length;
          var fin = d.trang_thai_bep === 'Đã xong';
          var rdy = !fin && rs.length > 0 && dn === rs.length;
          var cls = fin ? 'g' : (rdy ? 'b' : (dn ? 'w' : 'n'));
          var lbl = fin ? 'Đã giao' : (rdy ? 'Sẵn sàng giao' : (dn ? 'Đang làm ' + dn + '/' + rs.length : 'Chưa làm'));
          var whs = [];
          rs.forEach(function (r) { var w = shortWh(r.warehouse); if (w && whs.indexOf(w) < 0) whs.push(w); });
          var p2 = [d.name];
          if (d.bo_phan_yeu_cau) p2.push(d.bo_phan_yeu_cau);
          if (d.nguoi_yeu_cau) p2.push(d.nguoi_yeu_cau);
          return '<div class="li" data-n="' + h(d.name) + '"><div class="lt">' +
            '<div class="l1">' + h(whs.join(', ') || shortWh(d.set_warehouse) || d.name) + '</div>' +
            '<div class="l2">' + h(p2.join(' \u00b7 ')) + '</div></div>' +
            '<span class="st ' + cls + '">' + h(lbl) + '</span></div>';
        }).join('') + '</div></div>';
    }

    var ready = docs.filter(function (d) { return d.trang_thai_bep !== 'Đã xong' && docDone(d.name); });
    var b = frame('Bảng bếp ' + dmy(kit.date), body,
      ready.length ? { footer: '<button class="btn" id="kfin">Xác nhận đã giao ' + ready.length + ' phiếu</button>' } : {});

    b.onclick = async function (e) {
      var dc = e.target.closest('[data-d]');
      if (dc) { kit.date = dc.dataset.d; return scrKitchen(); }
      if (e.target.closest('[data-bep]')) { kit.mine = kit.mine ? 0 : 1; return scrKitchen(); }
      if (e.target.closest('[data-pick]')) {
        var v = await promptSheet('Xem ngày khác', 'Nhập ngày dạng nn/tt/nnnn');
        if (!v) return;
        var m = String(v).match(/^(\d{1,2})\D(\d{1,2})\D(\d{4})$/);
        if (!m) return toast('Ngày chưa đúng dạng nn/tt/nnnn');
        kit.date = m[3] + '-' + ('0' + m[2]).slice(-2) + '-' + ('0' + m[1]).slice(-2);
        return scrKitchen();
      }
      var rw = e.target.closest('[data-n]');
      if (rw) return go(function () { scrMRView(rw.dataset.n, TYPES.Manufacture); });
      var gc = e.target.closest('[data-g]');
      if (!gc) return;
      var k = gc.dataset.g, g = groups[k];
      if (!g) return;
      var want = gDone(k) ? 0 : 1;
      busy(1);
      try {
        for (var i = 0; i < g.rows.length; i++) {
          if ((g.rows[i].bep_da_lam ? 1 : 0) === want) continue;
          await api('frappe.client.set_value', { doctype: 'Material Request Item', name: g.rows[i].name, fieldname: { bep_da_lam: want } });
          g.rows[i].bep_da_lam = want;
        }
        if (want) {
          var ps = {};
          g.rows.forEach(function (r) { ps[r.parent] = 1; });
          for (var p in ps) {
            var dd = byDoc[p];
            if (dd && !dd.trang_thai_bep) {
              try { await api('frappe.client.set_value', { doctype: 'Material Request', name: p, fieldname: { trang_thai_bep: 'Đang làm' } }); dd.trang_thai_bep = 'Đang làm'; } catch (x2) { }
            }
          }
        }
      } catch (err) { toast(errMsg(err)); }
      busy(0);
      draw();
    };

    var fb = document.getElementById('kfin');
    if (fb) fb.onclick = async function () {
      if (!await confirmSheet('Xác nhận đã giao bánh?', 'Đánh dấu ' + ready.length + ' phiếu là đã làm xong và đã giao cho nơi nhận. Phiếu sẽ chuyển sang trạng thái Đã giao.', 'Xác nhận')) return;
      busy(1);
      try {
        for (var i = 0; i < ready.length; i++) {
          await api('frappe.client.set_value', {
            doctype: 'Material Request', name: ready[i].name,
            fieldname: { trang_thai_bep: 'Đã xong', bep_xong_luc: nowStamp(), bep_nguoi_xong: (S.me.full_name || S.user) }
          });
          ready[i].trang_thai_bep = 'Đã xong';
        }
        toast('Đã xác nhận ' + ready.length + ' phiếu');
      } catch (err) { toast(errMsg(err)); }
      busy(0);
      draw();
    };
  }
  draw();
}

/* ---------- 12c. Lenh san xuat ---------- */
var WOST = {
  'Draft': 'Nháp', 'Submitted': 'Đã duyệt', 'Not Started': 'Chưa bắt đầu', 'In Process': 'Đang làm',
  'Completed': 'Đã xong', 'Stopped': 'Đã dừng', 'Closed': 'Đã đóng', 'Cancelled': 'Đã huỷ'
};
var WODONE = ['Completed', 'Stopped', 'Closed', 'Cancelled'];
var mfg = { src: '', fg: '', tab: 'open', bep: '', han: '', mon: '' };
/* Nhung the mon dang xo ra o man danh sach lenh, giu theo ma mon de
   ve lai man khong dong het cac the bep vua mo. */
var mfgMo = {};
var mfgN = { horizon: 0, rows: null };
var mfgD = null;
var mfgL = null;

function whFind() {
  var a = Array.prototype.slice.call(arguments);
  for (var i = 0; i < S.wh.length; i++) {
    var lw = S.wh[i].toLowerCase(), ok = 1;
    for (var j = 0; j < a.length; j++) { if (lw.indexOf(String(a[j]).toLowerCase()) < 0) { ok = 0; break; } }
    if (ok) return S.wh[i];
  }
  return '';
}
function mfgKey() {
  var bp = (S.me.bo_phan || '').toLowerCase();
  if (bp.indexOf('baker') >= 0) return 'baker';
  if (bp.indexOf('pastry') >= 0) return 'pastry';
  if (bp.indexOf('lab') >= 0) return 'lab';
  return '';
}
function mfgInitWh() {
  try {
    if (!mfg.src) mfg.src = localStorage.getItem('vgb_mfg_src') || '';
    if (!mfg.fg) mfg.fg = localStorage.getItem('vgb_mfg_fg') || '';
  } catch (e) { }
  if (S.wh.indexOf(mfg.src) < 0) mfg.src = '';
  if (S.wh.indexOf(mfg.fg) < 0) mfg.fg = '';
  var k = mfgKey();
  if (k && !mfgQuanLy()) {
    var hopLe = mfgWhOpts().map(function (o) { return o.value; });
    if (hopLe.length && hopLe.indexOf(mfg.src) < 0) mfg.src = '';
    if (hopLe.length && hopLe.indexOf(mfg.fg) < 0) mfg.fg = '';
  }
  if (!mfg.src) mfg.src = (k && whFind(k, 'nguyên liệu')) || whFind('pastry', 'nguyên liệu') || whFind('nguyên liệu') || S.wh[0] || '';
  if (!mfg.fg) mfg.fg = (k && whFind(k, 'thành phẩm')) || whFind('pastry', 'thành phẩm') || whFind('thành phẩm') || S.wh[0] || '';
}
function mfgSaveWh() { try { localStorage.setItem('vgb_mfg_src', mfg.src); localStorage.setItem('vgb_mfg_fg', mfg.fg); } catch (e) { } }
function mfgShift() { var hh = (new Date()).getHours(); return hh < 12 ? 'Sáng' : (hh < 18 ? 'Chiều' : 'Đêm'); }
function mfgArea() { var k = mfgKey(); return k === 'baker' ? 'Bếp Baker' : (k === 'pastry' ? 'Bếp Pastry' : (k === 'lab' ? 'Sonneto Lab' : '')); }

async function inChunks(arr, n, fn) {
  var out = [];
  for (var i = 0; i < arr.length; i += n) {
    var r = await fn(arr.slice(i, i + n));
    if (r && r.length) out = out.concat(r);
  }
  return out;
}
function pad2(n) { return ('0' + n).slice(-2); }
function hmOf(d) { return pad2(d.getHours()) + ':' + pad2(d.getMinutes()) + ':00'; }
function ymdOf(d) { return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate()); }
async function freshOf(codes) {
  /* Mon "lam tuoi" ma may tu lam giup khi hoan tat mon cha. CHI mon con
     theo ton kho. Tu 25/08/2026 ban thanh pham phantom (is_stock_item = 0)
     tu no trong lenh cha, khong can lenh con; tao lenh con cho no thi
     ERPNext cho tao nhung phieu kho chan "is not a stock Item", lenh con
     nam lai thanh rac, moi lan bam them mot cai. Ra soat 03/09/2026. */
  var m = {};
  if (!codes || !codes.length) return m;
  var rows = await inChunks(codes, 80, function (lot) {
    return getList('Item', { fields: ['name', 'custom_lam_tuoi', 'is_stock_item'], filters: { name: ['in', lot] }, limit_page_length: 0 });
  });
  rows.forEach(function (r) { if (r.custom_lam_tuoi && r.is_stock_item) m[r.name] = 1; });
  return m;
}
/* Me nao cua lenh nay con dung duoc. THUAN.

   `cacMe` xep me moi nhat len truoc, `daGhiSo` la cac me DA bi tru tren mot
   phieu kho da ghi so. Tra ve me moi nhat chua ghi so, khong co thi tra ve
   chuoi rong de ben goi tu lam me moi. */
function mfgMeChuaGhiSo(cacMe, daGhiSo) {
  var xong = {};
  (daGhiSo || []).forEach(function (t) { if (t) xong[t] = 1; });
  var ds = cacMe || [];
  for (var i = 0; i < ds.length; i++) { if (ds[i] && !xong[ds[i]]) return ds[i]; }
  return '';
}
/* Truoc 04/09/2026 ham nay tra ve me MOI NHAT cua lenh, bat ke me do da nam
   tren phieu kho ghi so hay chua. Lenh hoan tat lam hai lan vi the dung lai
   dung mot me: banh ra lo chieu mang ngay san xuat, gio va han dung cua me
   lam ban sang, ma hai me that gop thanh mot so lo nen truy vet mat duong.
   Nay chi nhan me chua tung bi tru tren so. */
async function mfgBatchOf(woName) {
  if (!woName) return '';
  var ten = [];
  try {
    var r = await getList('Batch', { fields: ['name'], filters: { custom_lenh_san_xuat: woName }, order_by: 'creation desc', limit_page_length: 20 });
    ten = r.map(function (x) { return x.name; });
  } catch (e) { return ''; }
  if (!ten.length) return '';
  try {
    var d = await getList('Stock Entry Detail', { parent: 'Stock Entry', fields: ['batch_no'], filters: { parenttype: 'Stock Entry', batch_no: ['in', ten], docstatus: 1 }, limit_page_length: 0 });
    return mfgMeChuaGhiSo(ten, d.map(function (x) { return x.batch_no; }));
  } catch (e) {
    /* Hoi khong duoc (mang rot, hoac tai khoan bep khong doc duoc bang
       dong phieu kho) thi GIU NEP CU: tra ve me moi nhat. Tra ve rong o
       day la moi lan bam lai de ra mot me moi, tem da dan tren banh se
       khong con khop voi me ghi so - hong nang hon cai dang sua. */
    return ten[0];
  }
}
async function bomOf(codes) {
  var m = {};
  if (!codes || !codes.length) return m;
  var rows = await inChunks(codes, 80, function (lot) {
    return getList('BOM', { fields: ['name', 'item', 'quantity', 'uom'], filters: { item: ['in', lot], docstatus: 1, is_active: 1, is_default: 1 }, limit_page_length: 0 });
  });
  rows.forEach(function (r) { if (!m[r.item]) m[r.item] = r; });
  return m;
}
async function stockOf(codes, wh) {
  var m = {};
  if (!codes || !codes.length || !wh) return m;
  var rows = await inChunks(codes, 80, function (lot) {
    return getList('Bin', { fields: ['item_code', 'actual_qty'], filters: { warehouse: wh, item_code: ['in', lot] }, limit_page_length: 0 });
  });
  rows.forEach(function (r) { m[r.item_code] = (m[r.item_code] || 0) + (r.actual_qty || 0); });
  return m;
}
async function openWoQty(codes) {
  var m = {};
  if (!codes || !codes.length) return m;
  var rows = await inChunks(codes, 80, function (lot) {
    return getList('Work Order', { fields: ['production_item', 'qty', 'produced_qty', 'status'], filters: { docstatus: 1, production_item: ['in', lot] }, limit_page_length: 0 });
  });
  rows.forEach(function (w) {
    if (WODONE.indexOf(w.status) >= 0) return;
    var left = (w.qty || 0) - (w.produced_qty || 0);
    if (left > 0) m[w.production_item] = (m[w.production_item] || 0) + left;
  });
  return m;
}
async function mfgLoadItem(code) {
  var m = await getList('Item', { fields: ['name', 'item_name', 'stock_uom', 'image', 'shelf_life_in_days', 'has_batch_no', 'custom_dieu_kien_bao_quan', 'custom_lam_tuoi', 'custom_han_dung_gio'], filters: { name: code }, limit_page_length: 1 });
  if (!m.length) throw new Error('Không tìm thấy hàng hoá ' + code);
  var it = m[0];
  var us = [];
  try {
    var conv = await getList('UOM Conversion Detail', { parent: 'Item', fields: ['uom', 'conversion_factor'], filters: { parent: code, parenttype: 'Item' }, limit_page_length: 60 });
    us = conv.map(function (c) { return { uom: c.uom, cf: c.conversion_factor }; });
  } catch (e) { }
  if (!us.some(function (u) { return u.uom === it.stock_uom; })) us.unshift({ uom: it.stock_uom, cf: 1 });
  it.uoms = us;
  return it;
}

/* --- o chon kho nguyen lieu / kho thanh pham dung chung cho ca phan he --- */
function mfgWhCard() {
  return '<div class="card">' +
    '<div class="fld" data-mw="src"><div class="fi">🧂</div><div class="ft"><div class="fl">Lấy nguyên liệu từ kho</div>' +
    '<div class="fv">' + h(shortWh(mfg.src) || 'Chưa chọn') + '</div></div><div class="fc">&#8250;</div></div>' +
    '<div class="fld" data-mw="fg"><div class="fi">🎂</div><div class="ft"><div class="fl">Nhập thành phẩm vào kho</div>' +
    '<div class="fv">' + h(shortWh(mfg.fg) || 'Chưa chọn') + '</div></div><div class="fc">&#8250;</div></div></div>';
}
/* Kho cua bep nao thi bep do thay (anh Viet 21/08/2026). Truoc day o chon
   kho xo ra ca 14 kho, va 70 tren 75 lenh cua ca hai bep deu lap nham o
   kho Pastry. Nguoi thuoc mot bep chi con thay kho cua bep minh; quan ly
   (Giam doc, Manufacturing Manager, System Manager) van thay het de xu
   ca le. Bep chua khai bo phan cung thay het, vi chan nham nguoi con te
   hon cho chon rong. */
function mfgQuanLy() {
  return hasRole('System Manager') || hasRole('Giám đốc') || hasRole('Manufacturing Manager');
}
function mfgWhOpts() {
  var k = mfgKey();
  if (!k || mfgQuanLy()) return whOpts();
  var tu = k === 'baker' ? 'baker' : (k === 'pastry' ? 'pastry' : 'lab');
  var loc = whOpts().filter(function (o) {
    return String(o.value).toLowerCase().indexOf(tu) >= 0;
  });
  return loc.length ? loc : whOpts();
}
function mfgWhTap(e, redraw) {
  var t = e.target.closest('[data-mw]');
  if (!t) return false;
  var k = t.dataset.mw;
  sheet(k === 'src' ? 'Kho nguyên liệu' : 'Kho thành phẩm', mfgWhOpts(), mfg[k], function (o) {
    mfg[k] = o.value; mfgSaveWh(); redraw();
  }, true);
  return true;
}

/* --- o nhap so luong dang bottom sheet --- */
function qtySheet(title, label, def, uom) {
  return new Promise(function (res) {
    var ov = document.createElement('div'); ov.className = 'sh';
    ov.innerHTML = '<div class="shb" style="padding:18px 16px calc(env(safe-area-inset-bottom,0px) + 16px)">' +
      '<div style="font-size:17.5px;font-weight:700;margin-bottom:12px">' + h(title) + '</div>' +
      '<div style="font-size:12px;color:#8a8f9c;margin-bottom:6px">' + h(label || '') + '</div>' +
      '<div class="qr"><div class="stp"><button data-m>&minus;</button>' +
      '<input type="number" inputmode="decimal" id="qsv" value="' + (def || 0) + '">' +
      '<button data-p>+</button></div>' + (uom ? '<div class="uml">' + h(uom) + '</div>' : '') + '</div>' +
      '<button class="btn" data-y style="margin-top:14px">Xác nhận</button>' +
      '<button class="btn gh" data-n style="margin-top:9px">Huỷ</button></div>';
    document.body.appendChild(ov);
    var inp = ov.querySelector('#qsv');
    ov.onclick = function (e) {
      var t = e.target;
      if (t.hasAttribute && t.hasAttribute('data-m')) { inp.value = Math.max(0, r3((parseFloat(inp.value) || 0) - 1)); return; }
      if (t.hasAttribute && t.hasAttribute('data-p')) { inp.value = r3((parseFloat(inp.value) || 0) + 1); return; }
      if (t === ov || (t.hasAttribute && t.hasAttribute('data-n'))) { ov.remove(); res(null); return; }
      if (t.hasAttribute && t.hasAttribute('data-y')) { var v = parseFloat(inp.value) || 0; ov.remove(); res(v > 0 ? v : null); }
    };
    setTimeout(function () { try { inp.focus(); inp.select(); } catch (e) { } }, 150);
  });
}

/* --- tim hang hoa nhanh (dung cho khai nguyen lieu va them mon) --- */
function mfgPickItem(title, groups, onPick) {
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>' + h(title) + '</b><div class="x">&times;</div></div>' +
    '<div style="padding:10px 14px 6px;display:flex;gap:8px;align-items:center">' +
    '<input class="nt" id="mpq" placeholder="Gõ tên hoặc mã (từ 2 ký tự)" style="height:46px;padding:0 12px;flex:1">' +
    '<button class="sbtn" id="mpsc" style="width:46px;height:46px;flex:0 0 46px">&#128247;</button></div>' +
    '<div class="shl" style="min-height:170px"></div>';
  ov.appendChild(box); document.body.appendChild(ov);
  var lst = box.querySelector('.shl'), inp = box.querySelector('#mpq'), seq = 0, tmr = null;
  function close() { ov.remove(); }
  function msg(s) { lst.innerHTML = '<div class="emp" style="padding:34px 20px"><div class="e2">' + h(s) + '</div></div>'; }
  msg('Gõ để tìm hàng hoá');
  ov.onclick = function (e) { if (e.target === ov) close(); };
  box.querySelector('.x').onclick = close;
  async function run(q) {
    var my = ++seq;
    lst.innerHTML = '<div class="emp" style="padding:34px"><div class="e1">⏳</div></div>';
    var f = { disabled: 0, has_variants: 0 };
    if (groups && groups.length) f.item_group = ['in', groups];
    var res = [];
    try {
      res = await getList('Item', {
        fields: ['name', 'item_name', 'stock_uom', 'image'], filters: f,
        or_filters: { item_name: ['like', '%' + q + '%'], name: ['like', '%' + q + '%'] },
        limit_page_length: 60, order_by: 'item_name'
      });
    } catch (e) { }
    if (my !== seq) return;
    if (!res.length) return msg('Không tìm thấy hàng hoá');
    lst.innerHTML = res.map(function (it) {
      return '<div class="li" data-c="' + h(it.name) + '">' +
        (it.image ? '<img class="im" src="' + h(it.image) + '" loading="lazy">' : '<div class="im imp">🍰</div>') +
        '<div class="lt"><div class="l1">' + h(it.item_name) + '</div>' +
        '<div class="l2">Mã: ' + h(it.name) + ' &middot; ' + h(it.stock_uom) + '</div></div></div>';
    }).join('');
  }
  inp.oninput = function () {
    clearTimeout(tmr);
    var v = inp.value.trim();
    if (v.length < 2) return msg('Gõ ít nhất 2 ký tự');
    tmr = setTimeout(function () { run(v); }, 280);
  };
  lst.onclick = function (e) { var r = e.target.closest('[data-c]'); if (!r) return; close(); onPick(r.dataset.c); };
  box.querySelector('#mpsc').onclick = async function () {
    close();
    var code = await scanBarcode();
    if (!code) return;
    busy(1); var ic = null;
    try { ic = await itemByBarcode(code); } catch (e) { }
    busy(0);
    if (!ic) return toast('Không tìm thấy hàng hoá có mã vạch này');
    onPick(ic);
  };
  setTimeout(function () { try { inp.focus(); } catch (e) { } }, 160);
}

/* ---------- 12c-1. Danh sach lenh san xuat ---------- */
/* Danh sach lenh san xuat.

   Anh Viet 30/08/2026, sau khi may tao ra 6 lenh cho 6 phieu YCSX cung mot
   mon Cane le: "nhin vao thi khong ro lenh nao voi lenh nao la dung cho
   phieu YCSX, ngay can banh, em can gan cac chip noi thong tin nay vao LSX
   khi tao. Hay co the gom lai nhung lenh san xuat chung 1 mon thi vao chung
   1 lenh, khi bam vao se thay nhung lenh con ben trong."

   Lam CA HAI, vi hai cai giai hai viec khac nhau:
   - Chip noi tra loi "lenh nay cua phieu nao, can ngay nao". Re, va can ca
     khi mon chi co dung mot lenh.
   - Gop the tra loi "sao mot mon lai ra sau dong". Chi bat khi mon do co
     tu hai lenh tro len; mon mot lenh van la mot hang phang, khong bat bep
     mo them mot lop chi de thay dung mot dong ben trong.

   Ca danh sach doc trong MOT vong goi `ds_lenh`, va cac chip loc loc ngay
   tren mang da co. Bep nhap 40-50 phieu mot ngay nen moi vong goi thua la
   mot nhip cho thua. */
async function scrMfgList() {
  await loadMasters();
  mfgInitWh();
  frame('Lệnh sản xuất', '<div class="emp"><div class="e1">⏳</div></div>');
  var kq = { lenh: [], nhom: [], cac_bep: [] };
  try { kq = await api('vagabond.ke_hoach_sx.ds_lenh', {}); }
  catch (e) { toast(errMsg(e), 6000); }
  var all = kq.lenh || [];

  function hopLe(w) {
    if (mfg.tab === 'open' && w.xong) return false;
    if (mfg.tab === 'chua' && !(!w.xong && !(w.so_da > 0))) return false;
    if (mfg.tab === 'dang' && !(!w.xong && w.so_da > 0)) return false;
    if (mfg.tab === 'done' && w.trang_thai !== 'Completed') return false;
    if (mfg.bep && w.bep !== mfg.bep) return false;
    if (mfg.han === 'qua' && !(w.ngay_can && w.ngay_can < today() && !w.xong)) return false;
    if (mfg.han === 'nay' && w.ngay_can !== today()) return false;
    if (mfg.han === 'thieu' && !(w.thieu && w.thieu.length)) return false;
    if (mfg.mon && w.ma_mon !== mfg.mon) return false;
    return true;
  }
  function noiChip(w) {
    /* Chip "Thieu nguyen lieu" doc duoc TRUOC luc bam (anh Viet 31/08/2026,
       y so 4), de bep khong bam hoan thanh roi moi bi may chan. */
    var them = (w.thieu && w.thieu.length)
      ? '<i class="q">⚠️ Thiếu ' + w.thieu.length + ' nguyên liệu</i>' : '';
    if ((!w.chip || !w.chip.length) && !them) return '';
    var qua = w.ngay_can && w.ngay_can < today() && !w.xong;
    return '<div class="noi">' + them + (w.chip || []).map(function (c) {
      var cls = '';
      if (c.indexOf('Cần ') === 0) cls = qua ? ' class="q"' : ' class="d"';
      return '<i' + cls + '>' + h(c) + '</i>';
    }).join('') + '</div>';
  }
  function mauTt(w) {
    if (w.trang_thai === 'Completed') return 'g';
    if (w.trang_thai === 'Stopped' || w.trang_thai === 'Closed') return 'n';
    return (w.so_da > 0) ? 'w' : 'b';
  }
  function coLam(w) { return !w.xong && (w.so_can - w.so_da) > 0.0001; }
  function hangLenh(w, con) {
    return '<div class="li" data-n="' + h(w.ten) + '">' +
      (con ? '' : anhMon(w.anh)) +
      '<div class="lt"><div class="l1">' + h(con ? w.ten : (w.ten_mon || w.ma_mon)) + '</div>' +
      '<div class="l2">' + h(con ? '' : w.ten + ' · ') + h(dmy(w.ngay_lam)) + '</div>' +
      noiChip(w) + '</div>' +
      '<div style="text-align:right"><div class="amt">' + kl(w.so_da, w.dvt) + ' / ' + kl(w.so_can, w.dvt) + '</div>' +
      '<div class="st ' + mauTt(w) + '" style="margin-top:4px">' + h(w.ten_trang_thai) + '</div></div>' +
      '<button class="lok" data-ok="' + h(w.ten) + '"' + (coLam(w) ? '' : ' disabled') + '>✓</button></div>';
  }
  function theGop(g) {
    var mo = !!mfgMo[g.ma_mon];
    var conLai = g.so_can - g.so_da;
    return '<div class="lgop"><div class="li" data-g="' + h(g.ma_mon) + '">' +
      anhMon(g.anh) +
      '<div class="lt"><div class="l1">' + h(g.ten_mon) + '</div>' +
      '<div class="l2">' + g.so_lenh + ' lệnh · còn ' + kl(Math.max(0, conLai), g.dvt) + '</div>' +
      noiChip({ chip: gopChip(g), ngay_can: g.ngay_can, xong: 0 }) + '</div>' +
      '<div style="text-align:right"><div class="amt">' + kl(g.so_da, g.dvt) + ' / ' + kl(g.so_can, g.dvt) + '</div>' +
      '<div class="lsl" style="margin-top:5px;display:inline-block">' + (mo ? 'Thu lại' : 'Xem ' + g.so_lenh + ' lệnh') + '</div></div>' +
      '<button class="lok" data-gok="' + h(g.ma_mon) + '"' + (conLai > 0.0001 ? '' : ' disabled') + '>✓</button></div>' +
      (mo ? '<div class="lcon">' + g.con.map(function (c) { return hangLenh(c, 1); }).join('') +
        '<button class="btn gh" data-gin="' + h(g.ma_mon) + '" style="margin-top:2px">🖨️ In tem cả ' + g.so_lenh + ' lệnh</button></div>' : '') +
      '</div>';
  }
  function gopChip(g) {
    var ra = (g.ycsx || []).slice(0, 2);
    var du = (g.ycsx || []).length - 2;
    if (du > 0) ra.push('và ' + du + ' phiếu nữa');
    if (g.ngay_can) ra.push('Cần ' + dmy(g.ngay_can));
    return ra;
  }

  function draw() {
    var f = all.filter(hopLe);
    var nhom = mfgGomMon(f);
    var cTt = [['open', 'Đang làm'], ['chua', 'Chưa bắt đầu'], ['dang', 'Làm dở'],
    ['done', 'Đã xong'], ['all', 'Tất cả']].map(function (c) {
      return '<div class="chip' + (mfg.tab === c[0] ? ' on' : '') + '" data-t="' + c[0] + '">' + c[1] + '</div>';
    }).join('');
    var cLoc = [['bep', '', 'Mọi bếp']].concat((kq.cac_bep || []).map(function (b) {
      return ['bep', b.ma, b.ten];
    })).concat([['han', 'qua', '⏰ Quá hạn'], ['han', 'nay', '📅 Cần hôm nay'],
    ['han', 'thieu', '⚠️ Thiếu nguyên liệu']])
      .map(function (c) {
        var on = (c[0] === 'bep') ? (mfg.bep === c[1]) : (mfg.han === c[1]);
        return '<div class="chip' + (on ? ' on' : '') + '" data-f="' + c[0] + '" data-v="' + h(c[1]) + '">' + h(c[2]) + '</div>';
      }).join('');

    /* Dang loc theo mot mon (vua quet ma) thi hien mot chip rieng, bam la
       bo loc. Khong co no thi bep quet nham mot mon roi khong hieu vi sao
       danh sach trong tron. */
    var cMon = mfg.mon
      ? '<div class="chip on" data-xmon="1">✕ Chỉ món ' + h(mfg.mon) + '</div>' : '';
    var body =
      '<div class="row2" style="margin-bottom:12px">' +
      '<button class="btn gh" id="mNoBom">🧾 Món chưa có công thức</button>' +
      '<button class="btn gh" id="mQuet">📷 Quét mã mẻ</button></div>' +
      '<div class="chips">' + cTt + '</div>' +
      '<div class="chips">' + cMon + cLoc + '</div>' +
      (f.length ? '<div class="lst">' + nhom.map(function (g) {
        return g.gop ? theGop(g) : hangLenh(g.con[0], 0);
      }).join('') + '</div>'
        : '<div class="emp"><div class="e1">🏭</div><div class="e2">' +
        (all.length ? 'Không có lệnh nào khớp bộ lọc' : 'Chưa có lệnh sản xuất nào') + '</div></div>');

    var b = frame('Lệnh sản xuất', body, { fab: true, onFab: function () { mfgN.rows = null; go(scrMfgNew); } });
    b.onclick = function (e) {
      var ok = e.target.closest('[data-ok]');
      if (ok) { if (!ok.disabled) mfgHoanTatNhanh(ok.dataset.ok, all, draw); return; }
      /* Nut cua the cha phai bat TRUOC [data-g], khong thi bam ✓ chi lam
         the xo ra chu khong ghi so gi ca. */
      var gok = e.target.closest('[data-gok]');
      if (gok) {
        if (!gok.disabled) {
          var gg = nhom.filter(function (x) { return x.ma_mon === gok.dataset.gok; })[0];
          if (gg) mfgHoanTatNhom(gg, function () { go(scrMfgList, true); });
        }
        return;
      }
      var gin = e.target.closest('[data-gin]');
      if (gin) {
        var g2 = nhom.filter(function (x) { return x.ma_mon === gin.dataset.gin; })[0];
        if (g2) mfgInTemNhom(g2);
        return;
      }
      if (e.target.closest('[data-xmon]')) { mfg.mon = ''; return draw(); }
      var c = e.target.closest('[data-t]');
      if (c) { mfg.tab = c.dataset.t; return draw(); }
      var lo = e.target.closest('[data-f]');
      if (lo) {
        var v = lo.dataset.v;
        if (lo.dataset.f === 'bep') mfg.bep = (mfg.bep === v ? '' : v);
        else mfg.han = (mfg.han === v ? '' : v);
        return draw();
      }
      var g = e.target.closest('[data-g]');
      if (g) { var k = g.dataset.g; mfgMo[k] = mfgMo[k] ? 0 : 1; return draw(); }
      var r = e.target.closest('[data-n]');
      if (r) { var nm = r.dataset.n; return go(function () { scrMfgView(nm); }); }
    };
    document.getElementById('mQuet').onclick = async function () {
      var code = await scanBarcode();
      if (!code) return;
      busy(1);
      var r = null;
      try { r = await api('vagabond.ke_hoach_sx.tim_lenh', { ma: code }); }
      catch (err) { busy(0); return toast(errMsg(err), 6000); }
      busy(0);
      if (!r || !r.ok) return toast((r && r.ghi_chu) || 'Không tìm thấy gì với mã này', 6000);
      if (r.lenh) { toast(r.ghi_chu, 3500); return go(function () { scrMfgView(r.lenh); }); }
      /* Khong ra duoc MOT lenh thi loc danh sach theo mon, va mo het bo loc
         trang thai ra: mon vua quet co the dang o tab khac, loc xong van
         trong tron thi bep tuong may hong. */
      mfg.mon = r.ma_mon || '';
      mfg.tab = 'all'; mfg.han = '';
      toast(r.ghi_chu, 5000);
      draw();
    };
    document.getElementById('mNoBom').onclick = function () {
      mfgPickItem('Chọn món cần làm', leavesUnder(['Bán ra', 'Sản xuất']), async function (code) {
        busy(1);
        try {
          var it = await mfgLoadItem(code);
          mfgD = { code: code, name: it.item_name || code, stock_uom: it.stock_uom, meta: it, qty: 1, mats: [], saveBom: 1 };
          go(scrMfgDeclare);
        } catch (err) { toast(errMsg(err)); } finally { busy(0); }
      });
    };
  }
  draw();
}

/* Gom theo mon NGAY TREN MANG DA LOC.

   Khong dung san `kq.nhom` cua may chu: cai do gom tren ca danh sach, con
   bep dang nhin qua bo loc. Loc "qua han" ra ba lenh ma the cha van keu
   "5 lenh" thi con so tren the noi doi.

   Cung mot luat voi `gom_lenh_theo_mon` ben Python: mon chi mot lenh thi
   khong gop. */
function mfgGomMon(ds) {
  var m = {}, thu_tu = [];
  (ds || []).forEach(function (w) {
    var k = w.ma_mon || w.ten;
    if (!m[k]) {
      m[k] = {
        ma_mon: k, ten_mon: w.ten_mon || k, anh: w.anh || '', dvt: w.dvt || '',
        so_can: 0, so_da: 0, ngay_can: '', ycsx: [], con: []
      };
      thu_tu.push(k);
    }
    var o = m[k];
    if (!o.anh && w.anh) o.anh = w.anh;
    o.so_can = r3(o.so_can + (w.so_can || 0));
    o.so_da = r3(o.so_da + (w.so_da || 0));
    if (w.ngay_can && (!o.ngay_can || w.ngay_can < o.ngay_can)) o.ngay_can = w.ngay_can;
    (w.ycsx || []).forEach(function (y) { if (y && o.ycsx.indexOf(y) < 0) o.ycsx.push(y); });
    o.con.push(w);
  });
  return thu_tu.map(function (k) {
    var o = m[k];
    o.so_lenh = o.con.length;
    o.gop = o.con.length > 1 ? 1 : 0;
    return o;
  });
}

/* Nut ✓ ngay tren hang: bam mot phat la ra o nhap so.

   Khai de nghi cat bot thao tac, anh Viet 30/08/2026: "anh muon chi can
   nhap so roi bam hoan thanh la xong". Truoc day phai mo phieu ra roi moi
   thay nut Hoan tat, tuc hai lan cham va mot lan cho tai trang.

   Lenh con NHAP thi may tu ghi so truoc khi hoan tat. Ghi so mot lenh la
   viec tien toi, khong phai sua du lieu cu, nen khong hoi lai. */
async function mfgHoanTatNhanh(ten, all, veLai) {
  busy(1);
  var d = null;
  try { d = await api('frappe.client.get', { doctype: 'Work Order', name: ten }); }
  catch (e) { busy(0); return toast(errMsg(e), 6000); }
  busy(0);
  var goc = (all || []).filter(function (x) { return x.ten === ten; })[0] || {};
  var xong = 0;
  /* `mfgHoanTatMot` nem loi len de che do chay theo lo con dem duoc lenh
     nao hong. Duong mot lenh da toast loi roi nen o day chi can nuot. */
  try { xong = await mfgChayHoanTat(d, goc.cac_dvt || null); } catch (e2) { return; }
  if (xong === 'lai') return go(scrMfgList, true);
  if (xong && veLai) veLai();
}

/* ---------- 12c-2. Tao lenh: gop nhu cau tu cac phieu yeu cau ---------- */
async function scrMfgNew() {
  mfgInitWh();
  if (!mfgN.rows) {
    frame('Tạo lệnh sản xuất', '<div class="emp"><div class="e1">⏳</div></div>');
    try { mfgN.rows = await mfgDemand(mfgN.horizon); }
    catch (e) { mfgN.rows = []; toast(errMsg(e), 5000); }
  }
  var rows = mfgN.rows;

  function draw() {
    var nsel = rows.filter(function (r) { return r.on && r.bom; }).length;
    var chips = [[0, 'Đến hôm nay'], [1, 'Đến ngày mai'], [7, 'Đến hết tuần']].map(function (c) {
      return '<div class="chip' + (mfgN.horizon === c[0] ? ' on' : '') + '" data-hz="' + c[0] + '">' + c[1] + '</div>';
    }).join('');
    var coBom = rows.filter(function (r) { return r.bom; });
    var chonHet = coBom.length && coBom.every(function (r) { return r.on; });
    var chipChon = rows.length
      ? '<div class="chip" data-all="1">' + (chonHet ? '✕ Bỏ chọn hết' : '✓ Chọn tất cả') + '</div>'
      : '';
    var body = mfgWhCard() + '<div class="chips">' + chips + chipChon + '</div>' +
      (rows.length ? rows.map(function (r, i) {
        var img = r.image ? '<img class="im3" src="' + h(r.image) + '">' : '<div class="im3 im3p">🍰</div>';
        return '<div class="ic1' + (r.on && r.bom ? ' ok' : '') + '" data-i="' + i + '">' +
          '<div class="ih">' + img +
          '<div class="in">' + h(r.name) + '<div class="ig">Mã: ' + h(r.code) +
          (r.bom ? '' : ' &middot; <span class="mno">Chưa có công thức</span>') + '</div></div>' +
          (r.bom ? '<div class="rok" data-k="' + i + '">&#10003;</div>' : '') + '</div>' +
          '<div class="stk">' +
          '<div><div class="s1">Phòng ban cần</div><div class="s2">' + num(r.need) + ' ' + h(r.uom) + '</div></div>' +
          '<div><div class="s1">Đã có lệnh</div><div class="s2">' + num(r.wo) + '</div></div>' +
          '<div><div class="s1">Tồn thành phẩm</div><div class="s2">' + num(r.ton) + '</div></div></div>' +
          (r.bom ?
            '<div class="qw"><div style="flex:1;min-width:0"><div class="lb">Số lượng sẽ làm</div>' +
            '<div class="qr"><div class="stp"><button data-m="' + i + '">&minus;</button>' +
            '<input type="number" inputmode="decimal" data-q="' + i + '" value="' + r.qty + '">' +
            '<button data-p="' + i + '">+</button></div><div class="uml">' + h(r.uom) + '</div></div></div></div>'
            : '<div class="qw"><button class="btn gh" data-dec="' + i + '">🧾 Khai nguyên liệu đã dùng</button></div>') +
          '</div>';
      }).join('')
        : '<div class="emp"><div class="e1">✅</div><div class="e2">Không còn món nào cần sản xuất trong khoảng này</div></div>') +
      '<button class="btn gh" id="mAdd" style="margin-top:4px">+ Thêm món ngoài phiếu yêu cầu</button>';

    var b = frame('Tạo lệnh sản xuất', body, {
      footer: '<button class="btn" id="mGo"' + (nsel ? '' : ' disabled') + '>Tạo ' + (nsel || '') + ' lệnh sản xuất</button>'
    });
    b.addEventListener('input', function (e) {
      var t = e.target;
      if (t.dataset.q != null) rows[+t.dataset.q].qty = parseFloat(t.value) || 0;
    });
    b.onclick = function (e) {
      if (mfgWhTap(e, draw)) return;
      var hz = e.target.closest('[data-hz]');
      if (hz) { mfgN.horizon = +hz.dataset.hz; mfgN.rows = null; return scrMfgNew(); }
      var ca = e.target.closest('[data-all]');
      if (ca) {
        var dangHet = rows.filter(function (r) { return r.bom; }).every(function (r) { return r.on; });
        rows.forEach(function (r) { if (r.bom) r.on = dangHet ? 0 : 1; });
        return draw();
      }
      var t = e.target.closest('[data-k],[data-m],[data-p],[data-dec]');
      if (!t) return;
      if (t.dataset.k != null) { var i = +t.dataset.k; rows[i].on = !rows[i].on; return draw(); }
      if (t.dataset.m != null) { var j = +t.dataset.m; rows[j].qty = Math.max(0, r3(rows[j].qty - 1)); var el = b.querySelector('[data-q="' + j + '"]'); if (el) el.value = rows[j].qty; return; }
      if (t.dataset.p != null) { var k2 = +t.dataset.p; rows[k2].qty = r3(rows[k2].qty + 1); var e2 = b.querySelector('[data-q="' + k2 + '"]'); if (e2) e2.value = rows[k2].qty; return; }
      if (t.dataset.dec != null) {
        var r = rows[+t.dataset.dec];
        busy(1);
        mfgLoadItem(r.code).then(function (it) {
          mfgD = { code: r.code, name: r.name, stock_uom: it.stock_uom, meta: it, qty: r.qty || 1, mats: [], saveBom: 1 };
          go(scrMfgDeclare);
        }).catch(function (err) { toast(errMsg(err)); }).then(function () { busy(0); });
      }
    };
    document.getElementById('mAdd').onclick = function () {
      mfgPickItem('Thêm món cần làm', leavesUnder(['Bán ra', 'Sản xuất']), async function (code) {
        if (rows.some(function (x) { return x.code === code; })) return toast('Món này đã có trong danh sách');
        busy(1);
        try {
          var it = await mfgLoadItem(code);
          var bm = await bomOf([code]);
          var tn = await stockOf([code], mfg.fg);
          rows.push({ code: code, name: it.item_name || code, uom: it.stock_uom, image: it.image || '', need: 0, wo: 0, ton: tn[code] || 0, bom: bm[code] ? bm[code].name : '', qty: 1, on: 1 });
          draw();
        } catch (err) { toast(errMsg(err)); } finally { busy(0); }
      });
    };
    document.getElementById('mGo').onclick = async function () {
      var sel = rows.filter(function (r) { return r.on && r.bom && r.qty > 0; });
      if (!sel.length) return toast('Chưa chọn món nào');
      if (!mfg.src || !mfg.fg) return toast('Chưa chọn kho nguyên liệu hoặc kho thành phẩm');
      busy(1);
      var made = [], errs = [];
      for (var i = 0; i < sel.length; i++) {
        try { made.push(await mfgCreateWO(sel[i])); }
        catch (err) { errs.push(sel[i].name + ': ' + errMsg(err)); }
      }
      busy(0);
      if (errs.length) toast(errs[0], 6000);
      if (!made.length) return;
      toast('Đã tạo ' + made.length + ' lệnh sản xuất');
      mfgN.rows = null;
      go(function () { scrMfgBtp(made, 1); }, true);
    };
  }
  draw();
}

/* gop nhu cau tu cac phieu yeu cau san xuat da duyet */
async function mfgDemand(horizon) {
  var td = today();
  var to = addDays(td, horizon || 0);
  var from = addDays(td, -45);
  var docs = await getList('Material Request', {
    fields: ['name', 'trang_thai_bep'],
    filters: [['material_request_type', '=', 'Manufacture'], ['docstatus', '=', 1],
    ['schedule_date', '>=', from], ['schedule_date', '<=', to]],
    limit_page_length: 0
  });
  var names = docs.filter(function (d) { return d.trang_thai_bep !== 'Đã xong'; }).map(function (d) { return d.name; });
  var lines = [];
  if (names.length) {
    lines = await inChunks(names, 60, function (lot) {
      return getList('Material Request Item', {
        parent: 'Material Request',
        fields: ['item_code', 'item_name', 'qty', 'stock_qty', 'uom', 'stock_uom', 'bep_da_lam'],
        filters: { parent: ['in', lot] }, limit_page_length: 0
      });
    });
  }
  var agg = {}, order = [];
  lines.forEach(function (l) {
    if (l.bep_da_lam) return;
    var c = l.item_code;
    if (!agg[c]) { agg[c] = { code: c, name: l.item_name || c, uom: l.stock_uom || l.uom, need: 0, wo: 0, ton: 0 }; order.push(c); }
    agg[c].need += (l.stock_qty || l.qty || 0);
  });
  if (!order.length) return [];
  var wq = await openWoQty(order);
  var tn = await stockOf(order, mfg.fg);
  var bm = await bomOf(order);
  var meta = {};
  var mrows = await inChunks(order, 80, function (lot) {
    return getList('Item', { fields: ['name', 'item_name', 'image', 'stock_uom'], filters: { name: ['in', lot] }, limit_page_length: 0 });
  });
  mrows.forEach(function (m) { meta[m.name] = m; });
  return order.map(function (c) {
    var a = agg[c], m = meta[c] || {};
    a.wo = wq[c] || 0;
    a.ton = tn[c] || 0;
    a.image = m.image || '';
    a.name = m.item_name || a.name;
    a.uom = m.stock_uom || a.uom;
    a.bom = bm[c] ? bm[c].name : '';
    a.qty = Math.max(0, r3(a.need - a.wo));
    /* KHONG tu tick san mon nao (anh Viet 21/08/2026). Truoc day mon nao
       con thieu la may tick het, bep quen nhin la mot cham "Tao 38 lenh"
       de ra 38 lenh that. Gio bep tu tick tung mon, hoac cham "Chon tat
       ca" khi that su muon het. */
    a.on = 0;
    return a;
  }).filter(function (a) { return a.need > 0; });
}

/* Nổ nhiều cấp: LUÔN LÀ 1 kể từ 03/09/2026.

   Từ 21/08 tới 03/09 chỗ này hỏi hệ qua phantom.trang_thai, và hàm đó trả
   0 hễ CÒN MỘT mã bán thành phẩm chưa chuyển phantom. Ngày 03/09 đo trên
   site: đúng một mã BTPB00024 còn theo tồn, thế là toàn bộ lệnh từ app nổ
   một cấp. Nổ một cấp thì ERPNext lọc IM LẶNG mọi dòng bán thành phẩm
   phantom khỏi bảng nguyên liệu, hoàn tất vẫn báo thành công mà bột trứng
   bên trong không bị trừ. Một công tắc "tất cả hoặc không" cho cả tiệm là
   quá mong manh.

   Phantom là luật đã chốt (21/08 và 25/08), và từ v402 các công thức BTP
   mang cờ phantom chính thức của ERPNext nên nổ đúng ở cả hai chế độ. Ghi
   cứng 1. Mã nào lỡ còn theo tồn thì phantom.trang_thai vẫn liệt kê để
   quản lý đi gỡ, nhưng không được kéo cả tiệm về nổ một cấp nữa. */
var mfgPhantom = 1;

async function mfgNoNhieuCap() {
  return 1;
}

async function mfgCreateWO(row) {
  var doc = {
    doctype: 'Work Order', company: COMPANY,
    production_item: row.code, item_name: row.name, bom_no: row.bom,
    qty: row.qty, stock_uom: row.uom,
    fg_warehouse: row.fg || mfg.fg, source_warehouse: row.src || mfg.src,
    skip_transfer: 1, use_multi_level_bom: await mfgNoNhieuCap(),
    planned_start_date: today() + ' 05:00:00'
  };
  var ins = await api('frappe.client.insert', { doc: doc });
  var sub = await api('frappe.client.submit', { doc: ins });
  return (sub && sub.name) || ins.name;
}

/* ---------- 12c-3. May de xuat lenh ban thanh pham, bep bam duyet ---------- */
async function scrMfgBtp(woNames, depth) {
  depth = depth || 1;
  frame('Bán thành phẩm cần làm', '<div class="emp"><div class="e1">⏳</div></div>');
  var rows = [];
  try {
    var wis = await inChunks(woNames, 50, function (lot) {
      return getList('Work Order Item', {
        parent: 'Work Order', fields: ['item_code', 'item_name', 'required_qty', 'stock_uom'],
        filters: { parent: ['in', lot] }, limit_page_length: 0
      });
    });
    var agg = {}, order = [];
    wis.forEach(function (w) {
      var c = w.item_code;
      if (!agg[c]) { agg[c] = { code: c, name: w.item_name || c, uom: w.stock_uom, need: 0 }; order.push(c); }
      agg[c].need += (w.required_qty || 0);
    });
    var bm = await bomOf(order);
    var fr = await freshOf(order);
    var prod = order.filter(function (c) { return !!bm[c] && !fr[c]; });
    if (prod.length) {
      var tn = await stockOf(prod, mfg.src);
      var wq = await openWoQty(prod);
      rows = prod.map(function (c) {
        var a = agg[c];
        a.ton = tn[c] || 0; a.wo = wq[c] || 0; a.bom = bm[c].name;
        a.short = r3(a.need - a.ton - a.wo);
        a.qty = a.short > 0 ? Math.ceil(a.short) : 0;
        a.on = a.short > 0 ? 1 : 0;
        /* Ban thanh pham nhap ve KHO NGUYEN LIEU cua bep, khong phai kho
           thanh pham (luat 28/08/2026). Truoc 03/09 dong nay khong co fg
           nen mfgCreateWO lay mfg.fg = kho Thanh pham: lenh banh cha rut
           ruot banh o kho Nguyen lieu bao thieu, stockOf doc ton o do bang
           0, may lai de xuat lam ruot banh lan nua, ra lenh trung. */
        a.fg = mfg.src; a.src = mfg.src;
        return a;
      }).filter(function (a) { return a.short > 0; });
    }
  } catch (e) { toast(errMsg(e), 5000); }

  if (!rows.length) {
    toast('Không cần làm thêm bán thành phẩm nào', 4000);
    return go(scrMfgList, true);
  }

  function draw() {
    var nsel = rows.filter(function (r) { return r.on; }).length;
    var body = '<div class="rcvh">Máy tính ra các bán thành phẩm còn thiếu để làm được số bánh vừa tạo lệnh. ' +
      'Bếp xem lại rồi bấm duyệt, máy sẽ tạo lệnh sản xuất cho từng loại. ' +
      'Các loại làm tươi như mousse hay bán thành phẩm cấp 2 không hiện ở đây, máy sẽ tự làm khi bếp bấm hoàn tất lệnh của món cha.</div>' +
      rows.map(function (r, i) {
        return '<div class="ic1' + (r.on ? ' ok' : '') + '">' +
          '<div class="ih"><div class="n">' + (i + 1) + '</div>' +
          '<div class="in">' + h(r.name) + '<div class="ig">Mã: ' + h(r.code) + '</div></div>' +
          '<div class="rok" data-k="' + i + '">&#10003;</div></div>' +
          '<div class="stk">' +
          '<div><div class="s1">Công thức cần</div><div class="s2">' + num(r.need) + ' ' + h(r.uom) + '</div></div>' +
          '<div><div class="s1">Tồn kho NVL</div><div class="s2">' + num(r.ton) + '</div></div>' +
          '<div><div class="s1">Còn thiếu</div><div class="s2" style="color:#c93a3a">' + num(r.short) + '</div></div></div>' +
          '<div class="qw"><div style="flex:1;min-width:0"><div class="lb">Số lượng sẽ làm</div>' +
          '<div class="qr"><div class="stp"><button data-m="' + i + '">&minus;</button>' +
          '<input type="number" inputmode="decimal" data-q="' + i + '" value="' + r.qty + '">' +
          '<button data-p="' + i + '">+</button></div><div class="uml">' + h(r.uom) + '</div></div></div></div>' +
          '</div>';
      }).join('') +
      '<button class="btn gh" id="mSkip" style="margin-top:4px">Bỏ qua bước này</button>';

    var b = frame('Bán thành phẩm cần làm', body, {
      footer: '<button class="btn" id="mBtpGo"' + (nsel ? '' : ' disabled') + '>Duyệt và tạo ' + (nsel || '') + ' lệnh</button>'
    });
    b.addEventListener('input', function (e) {
      if (e.target.dataset.q != null) rows[+e.target.dataset.q].qty = parseFloat(e.target.value) || 0;
    });
    b.onclick = function (e) {
      var t = e.target.closest('[data-k],[data-m],[data-p]'); if (!t) return;
      if (t.dataset.k != null) { var i = +t.dataset.k; rows[i].on = !rows[i].on; return draw(); }
      if (t.dataset.m != null) { var j = +t.dataset.m; rows[j].qty = Math.max(0, r3(rows[j].qty - 1)); var el = b.querySelector('[data-q="' + j + '"]'); if (el) el.value = rows[j].qty; return; }
      if (t.dataset.p != null) { var k2 = +t.dataset.p; rows[k2].qty = r3(rows[k2].qty + 1); var e2 = b.querySelector('[data-q="' + k2 + '"]'); if (e2) e2.value = rows[k2].qty; }
    };
    document.getElementById('mSkip').onclick = function () { go(scrMfgList, true); };
    document.getElementById('mBtpGo').onclick = async function () {
      var sel = rows.filter(function (r) { return r.on && r.qty > 0; });
      if (!sel.length) return toast('Chưa chọn món nào');
      busy(1);
      var made = [], errs = [];
      for (var i = 0; i < sel.length; i++) {
        try { made.push(await mfgCreateWO(sel[i])); }
        catch (err) { errs.push(sel[i].name + ': ' + errMsg(err)); }
      }
      busy(0);
      if (errs.length) toast(errs[0], 6000);
      if (!made.length) return;
      toast('Đã tạo ' + made.length + ' lệnh bán thành phẩm');
      if (depth < 4) return go(function () { scrMfgBtp(made, depth + 1); }, true);
      go(scrMfgList, true);
    };
  }
  draw();
}

/* ---------- 12c-4. Chi tiet lenh va hoan tat san xuat ---------- */
/* Hop hoan tat: hai o so - "lam theo lenh" de tru nguyen lieu, va "thuc te
   can duoc" de nhap kho thanh pham (anh Viet 21/08/2026). Trai dua nay ra
   900 gram cui, trai mai 1.100; khoa cung so ly thuyet la ep bep khai man
   cho khop, va so lieu chet tu do. Tran vuot lenh dat o may chu (50%%),
   vuot nua thi may chu tu chan voi cau ro rang. */
/* O nhap so luc hoan tat, co CHO CHON DON VI TINH.

   Anh Viet 30/08/2026: "voi BTP thi se la can so luong lam duoc la bao
   nhieu theo don vi tinh la gram chang han, nen can co cho chon don vi
   tinh luc nhap, goi y theo don vi tinh mac dinh cua mon".

   Don vi mac dinh la don vi kho cua mon, tuc dung cai ma so lieu trong he
   dang tinh theo. Doi sang kg thi may quy doi lai CA HAI o ngay tai cho,
   de bep nhin thay 0,7 kg chu khong phai tu chia 700 cho 1000 trong dau.

   Con so tra ve LUON quy ve don vi kho. Tra ve theo don vi bep vua chon
   thi moi noi goi ham nay phai tu nho ma nhan lai, quen mot cho la ghi sai
   kho gap nghin lan. */
/* Nho so bep hay go cho tung mon.

   Anh Viet duyet 31/08/2026: "bep hay lam chan me, may hoc so bep hay go
   cho tung mon roi goi y san".

   May KHONG tu dien so cu de len o nhap. So mac dinh van la "con lai" cua
   lenh, vi do moi la so dung theo phieu yeu cau; so cu chi hien thanh chip
   ben duoi, bam mot cai la vao o. Tu dien de len thi bep go Enter theo
   thoi quen la ghi so sai vao but toan kho, ma but toan kho khong sua lai
   duoc.

   Nho theo DON VI bep da chon, khong quy ve don vi kho: bep nho "2 kg"
   chu khong nho "2000 gram". */
var MFG_NHO = 'vgb_mfg_so';
function mfgDocNho() {
  try { return JSON.parse(localStorage.getItem(MFG_NHO) || '{}') || {}; }
  catch (e) { return {}; }
}
function mfgNhoCua(ma) {
  if (!ma) return null;
  var m = mfgDocNho();
  var o = m[ma];
  return (o && o.ds && o.ds.length) ? o : null;
}
function mfgNhoSo(ma, soKho, dvt, heSo) {
  if (!ma || !(soKho > 0)) return;
  try {
    var m = mfgDocNho();
    var v = { so: r3(soKho / (heSo || 1)), dvt: dvt || '' };
    var ds = ((m[ma] || {}).ds || []).filter(function (x) {
      return !(x.dvt === v.dvt && Math.abs(x.so - v.so) < 0.0001);
    });
    ds.unshift(v);
    m[ma] = { dvt: v.dvt, ds: ds.slice(0, 2) };
    /* Chan localStorage phinh mai: bo mon cu nhat khi qua 150 mon. */
    var k = Object.keys(m);
    while (k.length > 150) { delete m[k.shift()]; }
    localStorage.setItem(MFG_NHO, JSON.stringify(m));
  } catch (e) { }
}

/* O nhap so luc hoan tat, co CHO CHON DON VI TINH.

   Anh Viet 30/08/2026: "voi BTP thi se la can so luong lam duoc la bao
   nhieu theo don vi tinh la gram chang han, nen can co cho chon don vi
   tinh luc nhap, goi y theo don vi tinh mac dinh cua mon".

   Don vi mac dinh la don vi kho cua mon, tuc dung cai ma so lieu trong he
   dang tinh theo; neu bep da tung chon don vi khac cho mon nay thi lay lai
   don vi do. Doi don vi thi may quy doi lai CA HAI o ngay tai cho, de bep
   nhin thay 0,7 kg chu khong phai tu chia 700 cho 1000 trong dau.

   Con so tra ve LUON quy ve don vi kho. Tra ve theo don vi bep vua chon
   thi moi noi goi ham nay phai tu nho ma nhan lai, quen mot cho la ghi sai
   kho gap nghin lan. */
function mfgSheetHoanTat(left, uom, cacDvt, maMon, tieuDe) {
  return new Promise(function (res) {
    var ds = (cacDvt && cacDvt.length) ? cacDvt.slice() : [{ dvt: uom || '', he_so: 1 }];
    if (!ds.filter(function (x) { return x.dvt === uom; }).length) ds.unshift({ dvt: uom || '', he_so: 1 });
    var nho = mfgNhoCua(maMon);
    var hs = 1, dvt = uom || '';
    if (nho && nho.dvt) {
      var u0 = ds.filter(function (x) { return x.dvt === nho.dvt; })[0];
      if (u0) { dvt = u0.dvt; hs = u0.he_so || 1; }
    }
    function q(v) { return r3((v || 0) / hs); }
    var sel = ds.length > 1
      ? '<select class="uom" id="htDvt">' + ds.map(function (u) {
        return '<option value="' + h(u.dvt) + '" data-hs="' + u.he_so + '"' +
          (u.dvt === dvt ? ' selected' : '') + '>' + h(u.dvt) + '</option>';
      }).join('') + '</select>'
      : '<div class="uml">' + h(dvt) + '</div>';
    var goi = (nho && nho.ds.length)
      ? '<div class="goiy">' + nho.ds.map(function (x, i) {
        return '<i data-goi="' + i + '">' + (i ? 'Rồi ' : 'Lần trước ') + h(num(x.so)) + ' ' + h(x.dvt) + '</i>';
      }).join('') + '</div>' : '';
    var ov = document.createElement('div'); ov.className = 'sh';
    ov.innerHTML = '<div class="shb" style="padding:18px 16px calc(env(safe-area-inset-bottom,0px) + 16px)">' +
      '<div style="font-size:17.5px;font-weight:700;margin-bottom:4px">' + h(tieuDe || 'Hoàn thành phiếu') + '</div>' +
      '<div style="font-size:12.5px;color:#8a8f9c;margin-bottom:12px;line-height:1.5">Nguyên liệu trừ theo số làm; thành phẩm nhập kho theo số CÂN THỰC TẾ. Hai số lệch nhau bao nhiêu, máy ghi lại bấy nhiêu.</div>' +
      '<div style="font-size:12px;color:#8a8f9c;margin-bottom:6px">Số lượng làm theo lệnh (còn lại <span id="htCon">' + num(q(left)) + '</span>)</div>' +
      '<div class="qr" style="margin-bottom:8px"><div class="stp"><button data-m1>&minus;</button>' +
      '<input type="number" inputmode="decimal" id="htLenh" value="' + r3(left / hs) + '"><button data-p1>+</button></div>' +
      sel + '</div>' + goi +
      '<div style="font-size:12px;color:#8a8f9c;margin:12px 0 6px">Thực tế cân được</div>' +
      '<div class="qr"><div class="stp"><button data-m2>&minus;</button>' +
      '<input type="number" inputmode="decimal" id="htCan" value="' + r3(left / hs) + '"><button data-p2>+</button></div>' +
      '<div class="uml" id="htU2">' + h(dvt) + '</div></div>' +
      '<button class="btn gr" data-y style="margin-top:14px">✅ Hoàn thành</button>' +
      '<button class="btn gh" data-n style="margin-top:9px">Huỷ</button></div>';
    document.body.appendChild(ov);
    var i1 = ov.querySelector('#htLenh'), i2 = ov.querySelector('#htCan');
    var cham = 0;
    i2.addEventListener('input', function () { cham = 1; });
    function v(x) { return Math.max(0, parseFloat(x.value) || 0); }
    var sl = ov.querySelector('#htDvt');
    if (sl) sl.onchange = function () {
      var o = sl.options[sl.selectedIndex];
      var moi = parseFloat(o.getAttribute('data-hs')) || 1;
      /* Quy doi tai cho: con so dang hien la theo don vi CU, nhan he so cu
         de ve don vi kho roi chia he so moi. */
      i1.value = r3(v(i1) * hs / moi);
      i2.value = r3(v(i2) * hs / moi);
      hs = moi; dvt = sl.value;
      ov.querySelector('#htU2').textContent = dvt;
      ov.querySelector('#htCon').textContent = num(r3(left / hs));
    };
    ov.onclick = function (e) {
      var t = e.target;
      var g = t.closest && t.closest('[data-goi]');
      if (g && nho) {
        var x = nho.ds[+g.dataset.goi];
        if (x) {
          if (sl && x.dvt && x.dvt !== dvt) {
            sl.value = x.dvt;
            var o2 = sl.options[sl.selectedIndex];
            hs = parseFloat(o2.getAttribute('data-hs')) || 1;
            dvt = sl.value;
            ov.querySelector('#htU2').textContent = dvt;
            ov.querySelector('#htCon').textContent = num(r3(left / hs));
          }
          i1.value = x.so;
          if (!cham) i2.value = x.so;
        }
        return;
      }
      function bum(inp, d) { inp.value = Math.max(0, r3(v(inp) + d)); if (inp === i1 && !cham) i2.value = inp.value; }
      if (t.hasAttribute && t.hasAttribute('data-m1')) return bum(i1, -1);
      if (t.hasAttribute && t.hasAttribute('data-p1')) return bum(i1, 1);
      if (t.hasAttribute && t.hasAttribute('data-m2')) { cham = 1; return bum(i2, -1); }
      if (t.hasAttribute && t.hasAttribute('data-p2')) { cham = 1; return bum(i2, 1); }
      if (t.hasAttribute && t.hasAttribute('data-y')) {
        var r = { theo_lenh: r3(v(i1) * hs), thuc_te: r3((cham ? v(i2) : v(i1)) * hs), dvt: dvt, he_so: hs };
        ov.remove(); return res(r);
      }
      if (t.hasAttribute && t.hasAttribute('data-n') || t === ov) { ov.remove(); return res(null); }
    };
    i1.addEventListener('input', function () { if (!cham) i2.value = i1.value; });
  });
}

/* Hop "May lam luon giup bep" ve lai bang chip (anh Viet 21/08/2026):
   truoc la mot khoi chu gach dau dong kho doc tren dien thoai, gio moi
   nguyen lieu la mot vien chip, thieu ton thi chip do, va nut xac nhan
   ro rang o cuoi. */
function mfgSheetKe(plan, nvl, src) {
  return new Promise(function (res) {
    function chip(t, phu, bad) {
      return '<span style="display:inline-block;margin:0 6px 8px 0;padding:7px 11px;border-radius:99px;' +
        'font-size:12.5px;font-weight:600;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;' +
        (bad ? 'background:#fde8e8;color:#b3261e;border:1px solid #f5c2c0'
             : 'background:#eef2f7;color:#374151;border:1px solid #e2e8f0') + '">' +
        h(t) + (phu ? ' <span style="font-weight:500;opacity:.75">' + h(phu) + '</span>' : '') + '</span>';
    }
    var thieu = (nvl || []).filter(function (x) { return x.thieu > 0.0001; });
    var html = '<div class="shb" style="padding:18px 16px calc(env(safe-area-inset-bottom,0px) + 16px);max-height:82vh;overflow:auto">' +
      '<div style="font-size:17.5px;font-weight:700;margin-bottom:4px">Máy làm luôn giúp bếp</div>' +
      '<div style="font-size:12.5px;color:#8a8f9c;margin-bottom:12px;line-height:1.5">' +
      'Các bán thành phẩm làm tươi chưa có tồn. Máy tự tạo lệnh và trừ nguyên liệu ngay trước khi hoàn tất món chính. Bút toán kho ghi xong không sửa lại được.</div>' +
      '<div style="font-size:11.5px;color:#98a2b3;margin-bottom:7px;letter-spacing:.4px">SẼ LÀM TƯƠI</div><div>' +
      (plan || []).map(function (f) { return chip(f.name, num(f.qty) + ' ' + (f.uom || ''), false); }).join('') + '</div>';
    if ((nvl || []).length) {
      html += '<div style="font-size:11.5px;color:#98a2b3;margin:10px 0 7px;letter-spacing:.4px">NGUYÊN LIỆU SẼ TRỪ · KHO ' +
        h(shortWh(src).toUpperCase()) + '</div><div>' +
        nvl.slice(0, 24).map(function (x) {
          var bad = x.thieu > 0.0001;
          return chip(x.name, num(x.need) + (bad ? ' · thiếu ' + num(x.thieu) : ''), bad);
        }).join('') +
        (nvl.length > 24 ? chip('và ' + (nvl.length - 24) + ' nguyên liệu nữa', '', false) : '') + '</div>';
      if (thieu.length) {
        html += '<div style="font-size:12.5px;color:#b3261e;margin-top:6px;line-height:1.5">Có ' + thieu.length +
          ' nguyên liệu không đủ tồn tại kho này. Máy sẽ tự lấy mã thay thế đã duyệt nếu còn, hết cả thì báo thiếu chứ không ghi âm kho.</div>';
      }
    }
    html += '<button class="btn gr" data-y style="margin-top:14px">✅ Xác nhận tạo lệnh</button>' +
      '<button class="btn gh" data-n style="margin-top:9px">Huỷ</button></div>';
    var ov = document.createElement('div'); ov.className = 'sh';
    ov.innerHTML = html;
    document.body.appendChild(ov);
    ov.onclick = function (e) {
      var t = e.target;
      if (t.hasAttribute && t.hasAttribute('data-y')) { ov.remove(); return res(true); }
      if ((t.hasAttribute && t.hasAttribute('data-n')) || t === ov) { ov.remove(); return res(false); }
    };
  });
}

async function scrMfgView(name) {
  frame('Lệnh sản xuất', '<div class="emp"><div class="e1">⏳</div></div>');
  var d = null;
  try { d = await api('frappe.client.get', { doctype: 'Work Order', name: name }); }
  catch (e) { toast(errMsg(e), 5000); return; }
  var mats = d.required_items || [];
  var src = d.source_warehouse || mfg.src;
  var tn = {};
  try { tn = await stockOf(mats.map(function (m) { return m.item_code; }), src); } catch (e) { }
  var left = r3((d.qty || 0) - (d.produced_qty || 0));
  var canDo = d.docstatus === 1 && WODONE.indexOf(d.status) < 0 && left > 0;

  var anh = '';
  try { var it0 = await mfgLoadItem(d.production_item); anh = it0.image || ''; } catch (e) { }
  var head = '<div class="card"><div class="kpg" style="display:flex;gap:10px;align-items:flex-start">' +
    anhMon(anh) + '<div style="flex:1;min-width:0">' +
    '<div style="font-size:18px;font-weight:700;line-height:1.3">' + h(d.item_name || d.production_item) + '</div>' +
    '<div style="font-size:12.5px;color:#8a8f9c;margin-top:5px">' + h(d.name) + ' &middot; ' + h(WOST[d.status] || d.status) + '</div>' +
    '</div></div><div class="stk">' +
    '<div><div class="s1">Cần làm</div><div class="s2">' + kl(d.qty, d.stock_uom) + '</div></div>' +
    '<div><div class="s1">Đã làm</div><div class="s2">' + kl(d.produced_qty || 0, d.stock_uom) + '</div></div>' +
    '<div><div class="s1">Còn lại</div><div class="s2">' + kl(left, d.stock_uom) + '</div></div></div>' +
    '<div class="fld"><div class="fi">🧂</div><div class="ft"><div class="fl">Trừ nguyên liệu tại kho</div>' +
    '<div class="fv">' + h(shortWh(src) || 'Chưa có') + '</div></div></div>' +
    '<div class="fld"><div class="fi">🎂</div><div class="ft"><div class="fl">Nhập thành phẩm vào kho</div>' +
    '<div class="fv">' + h(shortWh(d.fg_warehouse) || 'Chưa có') + '</div></div></div></div>';

  var short = 0;
  var list = mats.length ? '<div class="sec">Nguyên liệu sẽ trừ</div><div class="lst">' + mats.map(function (m) {
    var have = tn[m.item_code] || 0;
    var per = (d.qty || 1);
    var needNow = r3((m.required_qty || 0) / per * left);
    var bad = have < needNow - 0.0001;
    if (bad) short++;
    return '<div class="li"><div class="lt"><div class="l1">' + h(m.item_name || m.item_code) + '</div>' +
      '<div class="l2">Tồn ' + kl(have, m.stock_uom) + '</div></div>' +
      '<div style="text-align:right"><div class="amt"' + (bad ? ' style="color:#c93a3a"' : '') + '>' + kl(needNow, m.stock_uom) + '</div>' +
      '<div class="l2">' + h(m.stock_uom || '') + '</div></div></div>';
  }).join('') + '</div>' : '';

  var warn = short ? '<div class="kwn">⚠️ Có ' + short + ' nguyên liệu tồn kho không đủ. Nếu vẫn bấm hoàn tất thì máy sẽ báo lỗi thiếu hàng.</div>' : '';

  /* Nut huy va sua so (anh Viet 29/08/2026). Sua so chi hien khi lenh con
     nhap: lenh da ghi so ma doi so thi bang nguyen lieu can dung khong doi
     theo, bep lay hang theo so cu ma lam theo so moi. */
  var choHuy = d.docstatus < 2 && !(d.produced_qty > 0);
  var choSua = d.docstatus === 0;
  var hang2 = '';
  if (choSua) hang2 += '<button class="btn gh" id="mQty" style="margin-top:9px">✏️ Sửa số lượng</button>';
  if (choHuy) hang2 += '<button class="btn gh" id="mDel" style="margin-top:9px;color:#b3261e">🗑️ Huỷ lệnh này</button>';

  var b = frame('Lệnh sản xuất', head + warn + list, {
    footer: (canDo
      ? '<div class="row2"><button class="btn gh" id="mLbl">🖨️ In tem</button>' +
        '<button class="btn gr" id="mFin">✅ Hoàn tất</button></div>'
      : '<button class="btn gh" id="mLbl">🖨️ In lại tem</button>') + hang2
  });
  var nQty = document.getElementById('mQty');
  if (nQty) nQty.onclick = async function () {
    var v = await qtySheet('Sửa số lượng lệnh', d.item_name || d.production_item, d.qty, d.stock_uom);
    if (!(v > 0)) return;
    busy(1);
    try {
      var r = await api('vagabond.ke_hoach_sx.sua_so_lenh', { ten: d.name, so_luong: v });
      toast(r.ghi_chu, 6000);
      if (r.ok) return go(function () { scrMfgView(d.name); });
    } catch (err) { toast(errMsg(err), 6000); } finally { busy(0); }
  };
  var nDel = document.getElementById('mDel');
  if (nDel) nDel.onclick = async function () {
    if (!await confirmSheet('Huỷ lệnh ' + d.name + '?',
      'Số của món sẽ được trả lại cho kế hoạch, ra lệnh mới được ngay.\n\n' +
      'Lệnh đã làm ra hàng hoặc đã chuyển nguyên liệu vào sản xuất thì máy không cho huỷ.',
      'Huỷ lệnh', 1)) return;
    busy(1);
    try {
      var r = await api('vagabond.ke_hoach_sx.huy_lenh', { ten: d.name });
      toast(r.ghi_chu, 7000);
      if (r.ok) return go(scrMfgList);
    } catch (err) { toast(errMsg(err), 7000); } finally { busy(0); }
  };
  document.getElementById('mLbl').onclick = async function () {
    busy(1);
    try {
      var it = await mfgLoadItem(d.production_item);
      if (!it.has_batch_no) { busy(0); return toast('Món này chưa bật theo dõi lô nên chưa in được tem', 5000); }
      var bt = await mfgBatchOf(d.name);
      if (!bt) bt = await mfgMakeBatch(d.production_item, it, left || d.qty, d.name);
      busy(0);
      if (!bt) return toast('Chưa tạo được mẻ để in tem', 5000);
      mfgL = { batch: bt, item: d.production_item, name: d.item_name || d.production_item, qty: left || d.qty, uom: d.stock_uom, meta: it, pre: canDo ? 1 : 0 };
      return go(scrMfgLabel);
    } catch (err) { busy(0); toast(errMsg(err), 7000); }
  };
  if (!canDo) return;
  document.getElementById('mFin').onclick = function () { mfgChayHoanTat(d, null); };
}
/* Chia so bep go cho tung lenh con. THUAN.

   Cung mot luat voi `chia_so_luong` ben Python, co ca kiem canh hai ben.
   Rot lan luot tu lenh dau: go it hon tong thi lenh cuoi chua duoc rot van
   con nguyen so cu, lan sau ra tiep. Go NHIEU hon tong thi phan doi tra ve
   rieng - KHONG nhet vao mot lenh bat ky, vi lam vay la lam sai so cua
   phieu yeu cau ma lenh do dang neo vao. */
function mfgChiaSo(cacCon, tong) {
  var ra = [], conLai = Math.max(0, tong || 0);
  (cacCon || []).forEach(function (c) {
    var can = Math.max(0, c || 0);
    if (conLai <= 0) { ra.push(0); return; }
    var phan = can <= conLai ? can : conLai;
    ra.push(r3(phan));
    conLai = r3(conLai - phan);
  });
  return { phan: ra, doi: conLai > 0 ? r3(conLai) : 0 };
}

/* Chay mot lan hoan tat cho MOT lenh.

   Tach ra khoi man chi tiet (anh Viet 30/08/2026) de nut ✓ ngay tren hang
   danh sach dung lai DUNG mot duong: cung phep tru kho, cung cach tu lam
   ban thanh pham tuoi, cung cach ghi chenh lech giua so lam va so can. Hai
   duong ma cung mot viec thi som muon cung lech nhau, ma lech o day la
   lech but toan kho.

   Tra ve 'lai' khi da ghi so xong va man goi nen tai lai danh sach; tra ve
   0 khi bep bam huy hay co loi. */
async function mfgChayHoanTat(d, cacDvt) {
  var left = r3((d.qty || 0) - (d.produced_qty || 0));
  if (!(left > 0)) { toast('Lệnh này đã làm đủ số rồi', 4000); return 0; }
  if (WODONE.indexOf(d.status) >= 0) { toast('Lệnh ' + (WOST[d.status] || d.status) + ' nên không hoàn tất được', 5000); return 0; }

  var hai = await mfgSheetHoanTat(left, d.stock_uom, cacDvt, d.production_item);
  if (!hai) return 0;
  var q = hai.theo_lenh;
  var can = hai.thuc_te;
  if (!q && !can) return 0;
  if (!q) q = can;
  if (q > left + 0.0001) { toast('Số làm theo lệnh không được quá số còn lại là ' + num(left) + ' ' + (d.stock_uom || '') + '. Thực tế cân dư thì ghi vào ô cân được.', 6000); return 0; }
  mfgNhoSo(d.production_item, can, hai.dvt, hai.he_so);
  return await mfgHoanTatMot(d, q, can, 0);
}

/* Phan chay that, KHONG hoi gi them ngoai hop "May lam luon giup bep".

   `imLang = 1` la che do chay theo lo: hop xac nhan da hien MOT lan cho ca
   nhom o tren roi, hoi lai tung lenh con la bat bep bam sau lan cho mot
   viec ho da duyet. Phan tu lam ban thanh pham tuoi VAN chay, chi khong
   hoi lai. */
async function mfgHoanTatMot(d, q, can, imLang) {
  var mats = d.required_items || [];
  var src = d.source_warehouse || mfg.src;
  var ratio = (d.qty || 1) ? q / (d.qty || 1) : 1;
  var plan = [];
  busy(1);
  try { plan = await mfgFreshPlan(mats, ratio, src); } catch (e) { }
  var nvl = [];
  if (plan.length && !imLang) { try { nvl = await mfgNvlCuaKe(plan, src); } catch (e3) { nvl = []; } }
  busy(0);
  if (plan.length && !imLang) {
    var okf = await mfgSheetKe(plan, nvl, src);
    if (!okf) return 0;
  }
  busy(1);
  try {
    if (d.docstatus === 0) {
      await api('frappe.client.submit', { doc: d });
      d = await api('frappe.client.get', { doctype: 'Work Order', name: d.name });
    }
    if (plan.length) await mfgRunFresh(plan, 1);
    var it = await mfgLoadItem(d.production_item);
    var batch = await mfgBatchOf(d.name);
    if (!batch) batch = await mfgMakeBatch(d.production_item, it, can, d.name);
    var se = await api('erpnext.manufacturing.doctype.work_order.work_order.make_stock_entry',
      { work_order_id: d.name, purpose: 'Manufacture', qty: q });
    se.set_posting_time = 1;
    se.posting_date = today();
    se.posting_time = nowStamp().slice(11);
    /* Nguyen lieu tru theo so LAM (q); thanh pham nhap kho theo so CAN
       THUC TE (can). Hai con so do MAY CHU dat (kho_san_xuat.so_hoan_tat),
       app chi gan me. Truoc 03/09/2026 app tu dat ca hai o cua phieu bang
       so can nen ERPNext khong ghi hao hut, can thieu la lenh treo mai va
       bam tiep la tru nguyen lieu lan hai.

       Insert va submit gop vao MOT yeu cau (hoan_tat_phieu): rot mang
       giua chung thi khong con phieu nhap nao roi lai khoa lenh. */
    (se.items || []).forEach(function (r) {
      if (r.is_finished_item && batch) { r.use_serial_batch_fields = 1; r.batch_no = batch; }
    });
    await api('vagabond.kho_san_xuat.hoan_tat_phieu', { phieu: se, q: q, can: can });
    busy(0);
    if (imLang) return 'lai';
    toast('Đã hoàn tất: trừ nguyên liệu theo ' + num(q) + ', nhập kho ' + num(can) + ' ' + (d.stock_uom || ''), 5000);
    if (!batch) return 'lai';
    mfgL = { batch: batch, item: d.production_item, name: d.item_name || d.production_item, qty: can, uom: d.stock_uom, meta: it };
    go(scrMfgLabel, true);
    return 0;
  } catch (err) { busy(0); if (!imLang) toast(errMsg(err), 7000); throw err; }
}

/* Hoan thanh CA THE GOP bang mot lan go so.

   Anh Viet duyet 31/08/2026, y so 1: "bam mot nut tren the cha la chia so
   cho cac lenh con theo thu tu, do phai bam sau lan cho sau phieu cung
   mot mon".

   Hop xac nhan liet ke ro tung lenh con nhan bao nhieu TRUOC khi ghi so.
   But toan kho khong sua lai duoc nen bep phai nhin thay con so truoc, chu
   khong phai bam mot phat roi doc lai o so cai. */
async function mfgHoanTatNhom(g, veLai) {
  var con = (g.con || []).filter(function (c) {
    return !c.xong && (c.so_can - c.so_da) > 0.0001;
  });
  if (!con.length) return toast('Nhóm này không còn lệnh nào phải làm', 4000);
  if (con.length === 1) return mfgHoanTatNhanh(con[0].ten, g.con, veLai);

  var conLai = con.map(function (c) { return r3(c.so_can - c.so_da); });
  var tong = r3(conLai.reduce(function (a, b) { return a + b; }, 0));
  var hai = await mfgSheetHoanTat(tong, g.dvt, (con[0] || {}).cac_dvt, g.ma_mon,
    'Hoàn thành ' + con.length + ' lệnh');
  if (!hai) return;
  var q = hai.theo_lenh || hai.thuc_te;
  if (!(q > 0)) return;
  if (q > tong + 0.0001) return toast('Số làm không được quá tổng còn lại là ' + num(tong) + ' ' + (g.dvt || ''), 6000);
  var chia = mfgChiaSo(conLai, q);
  var tyLe = q > 0 ? (hai.thuc_te / q) : 1;

  var dong = con.map(function (c, i) {
    return chia.phan[i] > 0
      ? '<i>' + h(c.ten) + ' · ' + h(num(chia.phan[i])) + ' ' + h(g.dvt || '') + '</i>'
      : '<i class="d">' + h(c.ten) + ' · để lần sau</i>';
  }).join('');
  var ok = await confirmSheet('Ghi sổ ' + con.length + ' lệnh',
    'Máy chia ' + num(q) + ' ' + (g.dvt || '') + ' cho các lệnh theo thứ tự, lệnh nào chưa tới lượt thì để nguyên số cũ cho lần sau. ' +
    (Math.abs(tyLe - 1) > 0.0001 ? 'Số cân thực tế chia theo cùng tỷ lệ. ' : '') +
    'Bút toán kho ghi xong không sửa lại được.\n\n' +
    con.map(function (c, i) {
      return (chia.phan[i] > 0 ? '• ' + c.ten + ': ' + num(chia.phan[i]) + ' ' + (g.dvt || '')
        : '• ' + c.ten + ': để lần sau');
    }).join('\n'),
    'Ghi sổ ' + con.length + ' lệnh', 0);
  if (!ok) return;
  mfgNhoSo(g.ma_mon, hai.thuc_te, hai.dvt, hai.he_so);

  var xong = 0, hong = [];
  for (var i = 0; i < con.length; i++) {
    if (!(chia.phan[i] > 0)) continue;
    busy(1);
    var d = null;
    try { d = await api('frappe.client.get', { doctype: 'Work Order', name: con[i].ten }); }
    catch (e) { busy(0); hong.push(con[i].ten + ': ' + errMsg(e)); continue; }
    busy(0);
    try {
      await mfgHoanTatMot(d, chia.phan[i], r3(chia.phan[i] * tyLe), 1);
      xong++;
    } catch (e2) { hong.push(con[i].ten + ': ' + errMsg(e2)); }
  }
  if (hong.length) {
    toast('Ghi sổ được ' + xong + ' lệnh. ' + hong.length + ' lệnh hỏng: ' + hong[0], 9000);
  } else {
    toast('Đã ghi sổ ' + xong + ' lệnh, tổng ' + num(q) + ' ' + (g.dvt || ''), 6000);
  }
  if (veLai) veLai();
}

/* In tem cho ca the gop, mot lan bam.

   Anh Viet duyet 31/08/2026, y so 3. Chi di duoc duong in ngam qua QZ
   Tray: duong trinh duyet mo MOT cua so cho MOT ban in, sau lenh la sau
   cua so bung ra roi trinh duyet chan bot. Neu chua noi QZ thi noi thang
   ra chu khong im lang in thieu. */
async function mfgInTemNhom(g) {
  var con = (g.con || []).filter(function (c) { return !c.nhap; });
  if (!con.length) return toast('Nhóm này chưa có lệnh nào đã ghi sổ để in tem', 5000);
  if (!inSanSang('tem')) {
    return toast('Máy in tem chưa nối qua QZ Tray nên chỉ in được từng lệnh một. ' +
      'Mở từng lệnh rồi bấm In tem, hoặc bật QZ Tray lên rồi bấm lại.', 9000);
  }
  busy(1);
  var me = [], thieu = [];
  try {
    var it = await mfgLoadItem(g.ma_mon);
    if (!it.has_batch_no) { busy(0); return toast('Món này chưa bật theo dõi lô nên chưa in được tem', 5000); }
    for (var i = 0; i < con.length; i++) {
      var b = await mfgBatchOf(con[i].ten);
      if (!b) b = await mfgMakeBatch(g.ma_mon, it, r3(con[i].so_can - con[i].so_da) || con[i].so_can, con[i].ten);
      if (b) me.push({ me: b, n: Math.max(1, Math.ceil(con[i].so_da || con[i].so_can || 1)) });
      else thieu.push(con[i].ten);
    }
  } catch (e) { busy(0); return toast(errMsg(e), 7000); }
  busy(0);
  if (!me.length) return toast('Chưa tạo được mẻ nào để in tem', 5000);
  var tong = me.reduce(function (a, x) { return a + x.n; }, 0);
  var ok = await confirmSheet('In tem cả nhóm',
    'Máy in ' + tong + ' tem cho ' + me.length + ' mẻ của món ' + g.ten_mon + ', đẩy thẳng sang máy in tem.' +
    (thieu.length ? '\n\n' + thieu.length + ' lệnh chưa tạo được mẻ nên không có tem.' : ''),
    'In ' + tong + ' tem');
  if (!ok) return;
  busy(1);
  for (var j = 0; j < me.length; j++) {
    try { await mfgPrintCho(me[j].me, me[j].n); } catch (e2) { }
  }
  busy(0);
  toast('Đã đẩy ' + tong + ' tem sang máy in', 5000);
}

async function mfgMakeBatch(code, meta, qty, woName) {
  if (!meta || !meta.has_batch_no) return null;
  var now = new Date();
  var d0 = ymdOf(now);
  var doc = {
    doctype: 'Batch', item: code, manufacturing_date: d0,
    custom_gio_san_xuat: hmOf(now),
    custom_nguoi_san_xuat: S.user || undefined,
    custom_ca_san_xuat: mfgShift(),
    custom_khu_vuc_san_xuat: mfgArea() || undefined,
    custom_dieu_kien_bao_quan: meta.custom_dieu_kien_bao_quan || undefined,
    custom_trang_thai_qc: 'Chờ kiểm',
    custom_so_tem: Math.max(1, Math.ceil(qty || 1)),
    custom_lenh_san_xuat: woName || undefined
  };
  if (meta.custom_han_dung_gio > 0) {
    var e = new Date(now.getTime() + meta.custom_han_dung_gio * 3600000);
    doc.expiry_date = ymdOf(e);
    doc.custom_gio_het_han = hmOf(e);
  } else if (meta.shelf_life_in_days > 0) {
    doc.expiry_date = addDays(d0, meta.shelf_life_in_days);
    doc.custom_gio_het_han = hmOf(now);
  }
  var b = await api('frappe.client.insert', { doc: doc });
  return b && b.name;
}

/* --- Ban thanh pham lam tuoi: may tu lam noi duoi truoc khi hoan tat mon cha --- */
async function mfgFreshPlan(mats, ratio, src) {
  if (!mats || !mats.length) return [];
  var codes = mats.map(function (m) { return m.item_code; });
  var fr = await freshOf(codes);
  var fresh = codes.filter(function (c) { return fr[c]; });
  if (!fresh.length) return [];
  var bm = await bomOf(fresh);
  var tn = await stockOf(fresh, src);
  var out = [];
  mats.forEach(function (m) {
    var c = m.item_code;
    if (!fr[c] || !bm[c]) return;
    var need = r3((m.required_qty || 0) * ratio);
    var miss = r3(need - (tn[c] || 0));
    if (miss > 0.0001) out.push({
      code: c, name: m.item_name || c, uom: m.stock_uom,
      qty: miss, bom: bm[c].name, fg: src, src: src
    });
  });
  return out;
}
/* Ke hoach lam tuoi se tru nhung nguyen lieu nao, bao nhieu.

   Chi doc MOT cap cong thuc: neu trong do lai co ban thanh pham lam tuoi
   thi may van tu lam tiep, nhung hop xac nhan khong nen bay ca cay ra man
   hinh dien thoai. Cot "tồn" doc tai dung cai kho se bi tru. */
async function mfgNvlCuaKe(plan, src) {
  if (!plan || !plan.length) return [];
  var boms = plan.map(function (f) { return f.bom; }).filter(Boolean);
  if (!boms.length) return [];
  var bq = {};
  (await getList('BOM', {
    fields: ['name', 'quantity'], filters: { name: ['in', boms] }, limit_page_length: 0
  })).forEach(function (b) { bq[b.name] = b.quantity || 1; });

  var dong = await inChunks(boms, 40, function (lot) {
    return getList('BOM Item', {
      parent: 'BOM',
      fields: ['parent', 'item_code', 'item_name', 'stock_qty', 'stock_uom'],
      filters: { parent: ['in', lot] }, limit_page_length: 0
    });
  });

  var ti = {};
  plan.forEach(function (f) {
    if (!f.bom) return;
    ti[f.bom] = (ti[f.bom] || 0) + ((f.qty || 0) / (bq[f.bom] || 1));
  });

  var gom = {}, thu_tu = [];
  dong.forEach(function (r) {
    var t = ti[r.parent];
    if (!t) return;
    var c = r.item_code;
    if (!gom[c]) { gom[c] = { code: c, name: r.item_name || c, uom: r.stock_uom, need: 0 }; thu_tu.push(c); }
    gom[c].need = r3(gom[c].need + (r.stock_qty || 0) * t);
  });
  if (!thu_tu.length) return [];

  var tn = await stockOf(thu_tu, src);
  return thu_tu.map(function (c) {
    var x = gom[c];
    x.ton = tn[c] || 0;
    x.thieu = r3(Math.max(0, x.need - x.ton));
    return x;
  }).sort(function (a, b) { return (b.thieu > 0 ? 1 : 0) - (a.thieu > 0 ? 1 : 0); });
}

async function mfgRunFresh(list, depth) {
  depth = depth || 1;
  for (var i = 0; i < list.length; i++) {
    var f = list[i];
    var wo = await mfgCreateWO(f);
    var d = await api('frappe.client.get', { doctype: 'Work Order', name: wo });
    if (depth < 3) {
      var sub = await mfgFreshPlan(d.required_items || [], 1, d.source_warehouse || mfg.src);
      if (sub.length) await mfgRunFresh(sub, depth + 1);
    }
    var it = await mfgLoadItem(f.code);
    var batch = await mfgMakeBatch(f.code, it, f.qty, wo);
    var se = await api('erpnext.manufacturing.doctype.work_order.work_order.make_stock_entry',
      { work_order_id: wo, purpose: 'Manufacture', qty: f.qty });
    se.set_posting_time = 1; se.posting_date = today(); se.posting_time = nowStamp().slice(11);
    (se.items || []).forEach(function (r) {
      if (r.is_finished_item && batch) { r.use_serial_batch_fields = 1; r.batch_no = batch; }
    });
    var ins = await api('frappe.client.insert', { doc: se });
    await api('frappe.client.submit', { doc: ins });
  }
}

/* ---------- 12c-5. Mon chua co cong thuc: khai nguyen lieu ngay tren app ---------- */
async function scrMfgDeclare() {
  mfgInitWh();
  var st = mfgD;
  if (!st) return go(scrMfgList, true);

  function draw() {
    var body = mfgWhCard() +
      '<div class="ic1"><div class="ih">' +
      (st.meta && st.meta.image ? '<img class="im3" src="' + h(st.meta.image) + '">' : '<div class="im3 im3p">🍰</div>') +
      '<div class="in">' + h(st.name) + '<div class="ig">Mã: ' + h(st.code) + '</div></div></div>' +
      '<div class="qw"><div style="flex:1;min-width:0"><div class="lb">Số lượng làm được</div>' +
      '<div class="qr"><div class="stp"><button data-fm>&minus;</button>' +
      '<input type="number" inputmode="decimal" id="mdq" value="' + st.qty + '"><button data-fp>+</button></div>' +
      '<div class="uml">' + h(st.stock_uom) + '</div></div></div></div></div>' +
      '<div class="sec">Nguyên liệu đã dùng</div>' +
      (st.mats.length ? st.mats.map(function (m, i) {
        var sel = '<select class="uom" data-u="' + i + '">' + (m.uoms || [{ uom: m.stock_uom, cf: 1 }]).map(function (u) {
          return '<option value="' + h(u.uom) + '"' + (u.uom === m.uom ? ' selected' : '') + '>' + h(u.uom) + '</option>';
        }).join('') + '</select>';
        return '<div class="ic1"><div class="ih"><div class="n">' + (i + 1) + '</div>' +
          '<div class="in">' + h(m.name) + '<div class="ig">Tồn ' + num(m.ton) + ' ' + h(m.stock_uom) + '</div></div>' +
          '<div class="del" data-x="' + i + '">&times;</div></div>' +
          '<div class="qw"><div style="flex:1;min-width:0"><div class="lb">Số lượng đã dùng</div>' +
          '<div class="qr"><div class="stp"><button data-m="' + i + '">&minus;</button>' +
          '<input type="number" inputmode="decimal" data-q="' + i + '" value="' + m.qty + '">' +
          '<button data-p="' + i + '">+</button></div>' + sel + '</div></div></div></div>';
      }).join('') : '<div class="emp" style="padding:26px"><div class="e2">Chưa khai nguyên liệu nào</div></div>') +
      '<button class="btn gh" id="mdAdd">+ Thêm nguyên liệu</button>' +
      '<div class="card" style="margin-top:12px"><div class="fld" data-sb>' +
      '<div class="fi">💾</div><div class="ft"><div class="fl">Lần sau khỏi khai lại</div>' +
      '<div class="fv">Lưu thành công thức của món này</div></div>' +
      '<div class="ck' + (st.saveBom ? ' on' : '') + '">&#10003;</div></div></div>';

    var b = frame('Khai nguyên liệu', body, {
      footer: '<button class="btn gr" id="mdGo"' + (st.mats.length ? '' : ' disabled') + '>Xong - trừ kho nguyên liệu</button>'
    });
    b.addEventListener('input', function (e) {
      var t = e.target;
      if (t.id === 'mdq') st.qty = parseFloat(t.value) || 0;
      if (t.dataset.q != null) st.mats[+t.dataset.q].qty = parseFloat(t.value) || 0;
    });
    b.addEventListener('change', function (e) {
      var t = e.target;
      if (t.dataset.u != null) {
        var m = st.mats[+t.dataset.u];
        m.uom = t.value;
        var u = (m.uoms || []).filter(function (x) { return x.uom === t.value; })[0];
        m.cf = u ? u.cf : 1;
      }
    });
    b.onclick = function (e) {
      if (mfgWhTap(e, draw)) return;
      if (e.target.closest('[data-sb]')) { st.saveBom = st.saveBom ? 0 : 1; return draw(); }
      var t = e.target.closest('[data-fm],[data-fp],[data-x],[data-m],[data-p]'); if (!t) return;
      if (t.hasAttribute('data-fm')) { st.qty = Math.max(0, r3(st.qty - 1)); document.getElementById('mdq').value = st.qty; return; }
      if (t.hasAttribute('data-fp')) { st.qty = r3(st.qty + 1); document.getElementById('mdq').value = st.qty; return; }
      if (t.dataset.x != null) { st.mats.splice(+t.dataset.x, 1); return draw(); }
      if (t.dataset.m != null) { var i = +t.dataset.m; st.mats[i].qty = Math.max(0, r3(st.mats[i].qty - 1)); var el = b.querySelector('[data-q="' + i + '"]'); if (el) el.value = st.mats[i].qty; return; }
      if (t.dataset.p != null) { var j = +t.dataset.p; st.mats[j].qty = r3(st.mats[j].qty + 1); var e2 = b.querySelector('[data-q="' + j + '"]'); if (e2) e2.value = st.mats[j].qty; }
    };
    document.getElementById('mdAdd').onclick = function () {
      mfgPickItem('Chọn nguyên liệu', null, async function (code) {
        if (code === st.code) return toast('Không thể dùng chính món đang làm làm nguyên liệu');
        if (st.mats.some(function (x) { return x.code === code; })) return toast('Nguyên liệu này đã có trong danh sách');
        busy(1);
        try {
          var it = await mfgLoadItem(code);
          var tn = await stockOf([code], mfg.src);
          var u0 = it.uoms[0] || { uom: it.stock_uom, cf: 1 };
          st.mats.push({ code: code, name: it.item_name || code, stock_uom: it.stock_uom, uom: it.stock_uom, cf: 1, uoms: it.uoms, qty: 1, ton: tn[code] || 0 });
          draw();
        } catch (err) { toast(errMsg(err)); } finally { busy(0); }
      });
    };
    document.getElementById('mdGo').onclick = mfgDeclareSubmit;
  }
  draw();
}

async function mfgDeclareSubmit() {
  var st = mfgD;
  if (!(st.qty > 0)) return toast('Chưa nhập số lượng làm được');
  if (!st.mats.length) return toast('Chưa khai nguyên liệu nào');
  if (st.mats.some(function (m) { return !(m.qty > 0); })) return toast('Có nguyên liệu chưa nhập số lượng');
  if (!mfg.src || !mfg.fg) return toast('Chưa chọn kho nguyên liệu hoặc kho thành phẩm');
  var ok = await confirmSheet('Trừ kho nguyên liệu',
    'Máy sẽ trừ ' + st.mats.length + ' nguyên liệu tại kho ' + shortWh(mfg.src) + ' và nhập ' + num(st.qty) + ' ' + st.stock_uom + ' ' + st.name + ' vào kho ' + shortWh(mfg.fg) + '. Bút toán kho không sửa lại được.',
    'Xác nhận trừ kho');
  if (!ok) return;
  busy(1);
  try {
    var batch = await mfgMakeBatch(st.code, st.meta, st.qty, '');
    var items = st.mats.map(function (m) {
      return { item_code: m.code, qty: m.qty, uom: m.uom, conversion_factor: m.cf || 1, s_warehouse: mfg.src };
    });
    var fg = { item_code: st.code, qty: st.qty, uom: st.stock_uom, conversion_factor: 1, t_warehouse: mfg.fg, is_finished_item: 1 };
    if (batch) { fg.use_serial_batch_fields = 1; fg.batch_no = batch; }
    items.push(fg);
    var doc = {
      doctype: 'Stock Entry', company: COMPANY,
      stock_entry_type: 'Manufacture', purpose: 'Manufacture', from_bom: 0,
      set_posting_time: 1, posting_date: today(), posting_time: nowStamp().slice(11),
      from_warehouse: mfg.src, to_warehouse: mfg.fg, items: items,
      remarks: 'Bếp khai nguyên liệu trên app - ' + (S.me.full_name || S.user)
    };
    var ins = await api('frappe.client.insert', { doc: doc });
    await api('frappe.client.submit', { doc: ins });
    busy(0);
    toast('Đã trừ kho nguyên liệu');
    if (st.saveBom) {
      busy(1);
      try {
        await api('frappe.client.insert', {
          doc: {
            doctype: 'BOM', item: st.code, company: COMPANY, quantity: st.qty, uom: st.stock_uom,
            currency: 'VND', is_active: 1, is_default: 1, with_operations: 0, rm_cost_as_per: 'Valuation Rate',
            items: st.mats.map(function (m) {
              return { item_code: m.code, qty: m.qty, uom: m.uom, stock_uom: m.stock_uom, conversion_factor: m.cf || 1 };
            })
          }
        });
        toast('Đã lưu công thức nháp, quản lý bếp duyệt là lần sau khỏi khai lại', 5000);
      } catch (e2) { toast('Đã trừ kho xong. Phần lưu công thức chưa được: ' + errMsg(e2), 6000); }
      busy(0);
    }
    if (!batch) return go(scrMfgList, true);
    mfgL = { batch: batch, item: st.code, name: st.name, qty: st.qty, uom: st.stock_uom, meta: st.meta };
    return go(scrMfgLabel, true);
  } catch (err) { busy(0); toast(errMsg(err), 7000); }
}

/* ---------- 12c-6. In tem HACCP ---------- */
function mfgBqText(v) {
  return v === 'Freeze' ? 'CẤP ĐÔNG -18°C' : (v === 'Chill' ? 'BẢO QUẢN MÁT 0 - 5°C' : (v === 'Room Temp' ? 'NHIỆT ĐỘ PHÒNG dưới 25°C' : ''));
}
function scrMfgLabel() {
  var L = mfgL;
  if (!L) return go(scrMfgList, true);
  if (!L.n) L.n = Math.max(1, Math.ceil(L.qty || 1));
  var m = L.meta || {};
  var nw = new Date();
  var nsx = ymdOf(nw), gsx = hmOf(nw).slice(0, 5), hsd = '', ghh = '';
  if (m.custom_han_dung_gio > 0) {
    var ex = new Date(nw.getTime() + m.custom_han_dung_gio * 3600000);
    hsd = ymdOf(ex); ghh = hmOf(ex).slice(0, 5);
  } else if (m.shelf_life_in_days > 0) {
    hsd = addDays(nsx, m.shelf_life_in_days); ghh = gsx;
  }
  var bq = mfgBqText(m.custom_dieu_kien_bao_quan);

  function draw() {
    var body = '<div class="rcvh">' + (L.pre
      ? 'Đây là tem của mẻ này. Bếp in trước để dán cũng được, sau đó quay lại bấm Hoàn tất để trừ nguyên liệu.'
      : 'Sản xuất xong rồi. Bấm In tem để gửi sang máy in Brother, rồi dán lên từng cái bánh.') + '</div>' +
      '<div class="mtem"><div class="t1">' + h(L.name) + '</div>' +
      '<div class="t2"><b>NSX</b> ' + dmy(nsx) + ' ' + gsx +
      (hsd ? ' &nbsp; <b>HSD</b> ' + dmy(hsd) + ' ' + ghh : '') + '</div>' +
      (bq ? '<div class="bq">' + h(bq) + '</div>' : '') +
      '<div class="bcd">' + h(L.batch) + '</div></div>' +
      '<div class="card"><div class="qw"><div style="flex:1;min-width:0"><div class="lb">Số tem cần in</div>' +
      '<div class="qr"><div class="stp"><button data-m>&minus;</button>' +
      '<input type="number" inputmode="numeric" id="mln" value="' + L.n + '"><button data-p>+</button></div>' +
      '<div class="uml">tem</div></div></div></div></div>' +
      '<button class="btn gh" id="mlOne" style="margin-bottom:12px">In thử 1 tem</button>';

    var b = frame('In tem HACCP', body, { footer: '<button class="btn" id="mlGo">🖨️ In ' + L.n + ' tem</button>' });
    b.addEventListener('input', function (e) { if (e.target.id === 'mln') L.n = Math.max(1, parseInt(e.target.value, 10) || 1); });
    b.onclick = function (e) {
      var t = e.target.closest('[data-m],[data-p]'); if (!t) return;
      if (t.hasAttribute('data-m')) L.n = Math.max(1, L.n - 1); else L.n = L.n + 1;
      var el = document.getElementById('mln'); if (el) el.value = L.n;
      var g = document.getElementById('mlGo'); if (g) g.textContent = '🖨️ In ' + L.n + ' tem';
    };
    document.getElementById('mlOne').onclick = function () { mfgPrint(L.batch, 1); };
    document.getElementById('mlGo').onclick = function () { mfgPrint(L.batch, L.n); };
  }
  draw();
}
function mfgTemUrl(batch, n) {
  var fmt = n > 1 ? 'Vagabond - Tem HACCP nhieu tem' : 'Vagabond - Tem HACCP';
  return '/printview?doctype=Batch&name=' + encodeURIComponent(batch) +
    '&format=' + encodeURIComponent(fmt) + '&no_letterhead=1&trigger_print=1';
}

/* In mot me va CHO in xong moi tra ve. Chi dung cho duong in ngam QZ, nen
   nguoi goi phai tu kiem `inSanSang('tem')` truoc. Co no thi in ca nhom
   moi xep hang duoc, chu `mfgPrint` ban ra roi khong doi ai. */
async function mfgPrintCho(batch, n) {
  try {
    await api('frappe.client.set_value',
      { doctype: 'Batch', name: batch, fieldname: { custom_so_tem: n } });
  } catch (e) { }
  return await inToTuDuongDan('tem', 'Tem HACCP', mfgTemUrl(batch, n),
    inKho('tem').rong, null);
}

function mfgPrint(batch, n) {
  /* Tem HACCP do may chu dung bang Print Format, khong phai app tu ve.
     Van di duoc duong in ngam: xem inToTuDuongDan o 27-in-ngam.js. */
  var w = inMoCuaSoNeuCan('tem');
  if (w === 'chan') return;
  api('frappe.client.set_value', { doctype: 'Batch', name: batch, fieldname: { custom_so_tem: n } })
    .catch(function () { })
    .then(function () {
      inToTuDuongDan('tem', 'Tem HACCP', mfgTemUrl(batch, n),
        inKho('tem').rong, w);
    });
}


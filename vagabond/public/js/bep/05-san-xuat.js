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
var mfg = { src: '', fg: '', tab: 'open' };
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
  var m = {};
  if (!codes || !codes.length) return m;
  var rows = await inChunks(codes, 80, function (lot) {
    return getList('Item', { fields: ['name', 'custom_lam_tuoi'], filters: { name: ['in', lot] }, limit_page_length: 0 });
  });
  rows.forEach(function (r) { if (r.custom_lam_tuoi) m[r.name] = 1; });
  return m;
}
async function mfgBatchOf(woName) {
  if (!woName) return '';
  try {
    var r = await getList('Batch', { fields: ['name'], filters: { custom_lenh_san_xuat: woName }, order_by: 'creation desc', limit_page_length: 1 });
    return r.length ? r[0].name : '';
  } catch (e) { return ''; }
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
async function scrMfgList() {
  await loadMasters();
  mfgInitWh();
  frame('Lệnh sản xuất', '<div class="emp"><div class="e1">⏳</div></div>');
  var wos = [];
  try {
    wos = await getList('Work Order', {
      fields: ['name', 'production_item', 'item_name', 'qty', 'produced_qty', 'status', 'planned_start_date', 'stock_uom'],
      filters: { docstatus: ['<', 2] }, limit_page_length: 80, order_by: 'creation desc'
    });
  } catch (e) { toast(errMsg(e)); }

  /* Anh mon di kem ten mon (anh Viet 29/08/2026). Doc mot luot cho ca
     danh sach chu khong hoi tung mon. */
  var mfgAnh = {};
  try {
    var maMon = [];
    wos.forEach(function (w) {
      if (w.production_item && maMon.indexOf(w.production_item) < 0) maMon.push(w.production_item);
    });
    if (maMon.length) {
      var its = await getList('Item', {
        fields: ['name', 'image'], filters: { name: ['in', maMon] },
        limit_page_length: 200
      });
      its.forEach(function (x) { if (x.image) mfgAnh[x.name] = x.image; });
    }
  } catch (e) { }

  function draw() {
    var f = wos.filter(function (w) {
      if (mfg.tab === 'open') return WODONE.indexOf(w.status) < 0;
      if (mfg.tab === 'done') return w.status === 'Completed';
      return true;
    });
    var chips = [['open', 'Đang làm'], ['done', 'Đã xong'], ['all', 'Tất cả']].map(function (c) {
      return '<div class="chip' + (mfg.tab === c[0] ? ' on' : '') + '" data-t="' + c[0] + '">' + c[1] + '</div>';
    }).join('');
    /* KHONG con the chon kho o day. Anh Viet 29/08/2026: moi lenh da chon
       kho rieng cua no roi, de them mot o chon kho chung o trang danh sach
       la mau thuan, nguoi dung khong biet o nao thang. Hai man con dung
       kho chung (Tao lenh gop, Lam mon chua co cong thuc) van giu the do. */
    var body =
      '<button class="btn gh" id="mNoBom" style="margin-bottom:12px">🧾 Làm món chưa có công thức</button>' +
      '<div class="chips">' + chips + '</div>' +
      (f.length ? '<div class="lst">' + f.map(function (w) {
        var done = w.status === 'Completed';
        var cls = done ? 'g' : (w.status === 'Stopped' || w.status === 'Closed' ? 'n' : ((w.produced_qty || 0) > 0 ? 'w' : 'b'));
        return '<div class="li" data-n="' + h(w.name) + '">' + anhMon(mfgAnh[w.production_item]) +
          '<div class="lt" style="margin-left:9px">' +
          '<div class="l1">' + h(w.item_name || w.production_item) + '</div>' +
          '<div class="l2">' + h(w.name) + ' &middot; ' + h(dmy(w.planned_start_date)) + '</div></div>' +
          '<div style="text-align:right"><div class="amt">' + kl(w.produced_qty || 0, w.stock_uom) + ' / ' + kl(w.qty, w.stock_uom) + '</div>' +
          '<div class="st ' + cls + '" style="margin-top:4px">' + h(WOST[w.status] || w.status) + '</div></div></div>';
      }).join('') + '</div>'
        : '<div class="emp"><div class="e1">🏭</div><div class="e2">Chưa có lệnh sản xuất nào</div></div>');

    var b = frame('Lệnh sản xuất', body, { fab: true, onFab: function () { mfgN.rows = null; go(scrMfgNew); } });
    b.onclick = function (e) {
      if (mfgWhTap(e, draw)) return;
      var c = e.target.closest('[data-t]');
      if (c) { mfg.tab = c.dataset.t; return draw(); }
      var r = e.target.closest('[data-n]');
      if (r) { var nm = r.dataset.n; return go(function () { scrMfgView(nm); }); }
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

/* Nổ nhiều cấp hay không thì HỎI HỆ, không ghi cứng ở đây.

   Trước 21/08/2026 chỗ này ghi cứng 0, đúng vì bán thành phẩm cấp 1 còn
   theo tồn kho nên lệnh phải đòi thẳng mã đó. Sau khi chuyển cấp đó thành
   Phantom thì ngược lại: để 0 là lệnh đòi một mã không còn kho để lấy, và
   bếp đứng. Bật cứng lên 1 trước ngày chuyển cũng sai, vì 71 dòng bán
   thành phẩm đang sẵn công thức con sẽ nổ ngay hôm nay.

   Nên đọc trạng thái thật một lần mỗi phiên rồi nhớ lại. */
var mfgPhantom = null;

async function mfgNoNhieuCap() {
  if (mfgPhantom !== null) return mfgPhantom;
  try {
    var r = await api('vagabond.phantom.trang_thai', {});
    mfgPhantom = (r && r.da_phantom) ? 1 : 0;
  } catch (e) { mfgPhantom = 0; }
  return mfgPhantom;
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
function mfgSheetHoanTat(left, uom) {
  return new Promise(function (res) {
    var ov = document.createElement('div'); ov.className = 'sh';
    ov.innerHTML = '<div class="shb" style="padding:18px 16px calc(env(safe-area-inset-bottom,0px) + 16px)">' +
      '<div style="font-size:17.5px;font-weight:700;margin-bottom:4px">Hoàn tất sản xuất</div>' +
      '<div style="font-size:12.5px;color:#8a8f9c;margin-bottom:12px;line-height:1.5">Nguyên liệu trừ theo số làm; thành phẩm nhập kho theo số CÂN THỰC TẾ. Hai số lệch nhau bao nhiêu, máy ghi lại bấy nhiêu.</div>' +
      '<div style="font-size:12px;color:#8a8f9c;margin-bottom:6px">Số lượng làm theo lệnh (còn lại ' + num(left) + ')</div>' +
      '<div class="qr" style="margin-bottom:12px"><div class="stp"><button data-m1>&minus;</button>' +
      '<input type="number" inputmode="decimal" id="htLenh" value="' + left + '"><button data-p1>+</button></div>' +
      '<div class="uml">' + h(uom || '') + '</div></div>' +
      '<div style="font-size:12px;color:#8a8f9c;margin-bottom:6px">Thực tế cân được</div>' +
      '<div class="qr"><div class="stp"><button data-m2>&minus;</button>' +
      '<input type="number" inputmode="decimal" id="htCan" value="' + left + '"><button data-p2>+</button></div>' +
      '<div class="uml">' + h(uom || '') + '</div></div>' +
      '<button class="btn" data-y style="margin-top:14px">Tiếp tục</button>' +
      '<button class="btn gh" data-n style="margin-top:9px">Huỷ</button></div>';
    document.body.appendChild(ov);
    var i1 = ov.querySelector('#htLenh'), i2 = ov.querySelector('#htCan');
    var cham = 0;
    i2.addEventListener('input', function () { cham = 1; });
    function v(x) { return Math.max(0, parseFloat(x.value) || 0); }
    ov.onclick = function (e) {
      var t = e.target;
      function bum(inp, d) { inp.value = Math.max(0, r3(v(inp) + d)); if (inp === i1 && !cham) i2.value = inp.value; }
      if (t.hasAttribute && t.hasAttribute('data-m1')) return bum(i1, -1);
      if (t.hasAttribute && t.hasAttribute('data-p1')) return bum(i1, 1);
      if (t.hasAttribute && t.hasAttribute('data-m2')) { cham = 1; return bum(i2, -1); }
      if (t.hasAttribute && t.hasAttribute('data-p2')) { cham = 1; return bum(i2, 1); }
      if (t.hasAttribute && t.hasAttribute('data-y')) {
        var r = { theo_lenh: v(i1), thuc_te: cham ? v(i2) : v(i1) };
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
  document.getElementById('mFin').onclick = async function () {
    var hai = await mfgSheetHoanTat(left, d.stock_uom);
    if (!hai) return;
    var q = hai.theo_lenh;
    var can = hai.thuc_te;
    if (!q && !can) return;
    if (!q) q = can;
    if (q > left + 0.0001) return toast('Số làm theo lệnh không được quá số còn lại là ' + num(left) + '. Thực tế cân dư thì ghi vào ô cân được.', 6000);
    var ratio = (d.qty || 1) ? q / (d.qty || 1) : 1;
    var plan = [];
    busy(1);
    try { plan = await mfgFreshPlan(mats, ratio, src); } catch (e) { }
    var nvl = [];
    if (plan.length) { try { nvl = await mfgNvlCuaKe(plan, src); } catch (e3) { nvl = []; } }
    busy(0);
    if (plan.length) {
      var okf = await mfgSheetKe(plan, nvl, src);
      if (!okf) return;
    }
    busy(1);
    try {
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
         THUC TE (can). Lech nhau la hao hut hay doi du that cua me,
         ghi thang vao phieu de ke toan gia thanh doc duoc. */
      (se.items || []).forEach(function (r) {
        if (r.is_finished_item) {
          if (batch) { r.use_serial_batch_fields = 1; r.batch_no = batch; }
          if (Math.abs(can - q) > 0.0001) r.qty = can;
        }
      });
      if (Math.abs(can - q) > 0.0001) {
        se.fg_completed_qty = can;
        se.remarks = 'Làm theo lệnh ' + num(q) + ' ' + (d.stock_uom || '') +
          ', cân thực tế ' + num(can) + '. Chênh ' + num(r3(can - q)) +
          ' (' + (q ? Math.round((can - q) / q * 1000) / 10 : 0) + '%).';
      }
      var ins = await api('frappe.client.insert', { doc: se });
      await api('frappe.client.submit', { doc: ins });
      busy(0);
      toast('Đã hoàn tất: trừ nguyên liệu theo ' + num(q) + ', nhập kho ' + num(can) + ' ' + (d.stock_uom || ''), 5000);
      if (!batch) return go(scrMfgList, true);
      mfgL = { batch: batch, item: d.production_item, name: d.item_name || d.production_item, qty: can, uom: d.stock_uom, meta: it };
      return go(scrMfgLabel, true);
    } catch (err) { busy(0); toast(errMsg(err), 7000); }
  };
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
function mfgPrint(batch, n) {
  /* Tem HACCP do may chu dung bang Print Format, khong phai app tu ve.
     Van di duoc duong in ngam: xem inToTuDuongDan o 27-in-ngam.js. */
  var w = inMoCuaSoNeuCan('tem');
  if (w === 'chan') return;
  var fmt = n > 1 ? 'Vagabond - Tem HACCP nhieu tem' : 'Vagabond - Tem HACCP';
  api('frappe.client.set_value', { doctype: 'Batch', name: batch, fieldname: { custom_so_tem: n } })
    .catch(function () { })
    .then(function () {
      var u = '/printview?doctype=Batch&name=' + encodeURIComponent(batch) +
        '&format=' + encodeURIComponent(fmt) + '&no_letterhead=1&trigger_print=1';
      inToTuDuongDan('tem', 'Tem HACCP', u, inKho('tem').rong, w);
    });
}


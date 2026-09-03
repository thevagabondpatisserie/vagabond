/* ---------- 13. Nhap kho tu Don mua hang ---------- */
function isKho() { return hasRole('Stock Manager') || hasRole('Stock User') || hasRole('System Manager'); }
function r3(v) { return Math.round((v || 0) * 1000) / 1000; }
var rcv = { q: '', tab: 'cho' };

async function scrRecvList() {
  vgbCss();
  frame('Nhập kho', '<div class="emp"><div class="e1">⏳</div></div>');
  /* Tab "Còn phải nhận" (anh Việt duyệt 15/08/2026, PA-B).

     Trước đây một đơn ba món mà nhà cung cấp chỉ giao một món thì phiếu
     nháp bị dùng hết, tab Chờ nhận trống trơn, thủ kho tưởng hết việc -
     trong khi đơn mua vẫn còn nợ hai món. Nay phần còn nợ nằm ở tab này,
     lấy thẳng từ đơn mua chứ không cần ai tạo phiếu nháp đợt hai. */
  var TB = [
    { k: 'cho', ten: 'Chờ nhận', ds: 0 },
    { k: 'po', ten: 'Còn phải nhận', ds: -1 },
    { k: 'xong', ten: 'Đã nhập kho', ds: 1 },
    { k: 'huy', ten: 'Đã huỷ', ds: 2 }
  ];
  if (!rcv.tab) rcv.tab = 'cho';
  var D = {}, dem = {};
  var poDs = [];
  try { poDs = (await api('vagabond.nhan_hang.danh_sach', { so_ngay: 120 })).don || []; }
  catch (ePo) { poDs = []; }
  dem.po = poDs.length;
  for (var ti = 0; ti < TB.length; ti++) {
    /* `is_return: 0` - man NHAN hang chi bay phieu hang DI VAO.
       Phieu tra hang lai nha cung cap cung la Purchase Receipt, chi khac o
       co `is_return`, va no duoc ghi so ngay luc lap ben man Tra hang NCC.
       Khong loc thi moi lan tra hang la tab "Đã nhập kho" lai cong them mot
       to, thu kho doc so lai tuong hang vua ve. */
    var t = TB[ti], f = { docstatus: t.ds, is_return: 0 };
    if (t.ds < 0) { D[t.k] = []; continue; }
    if (t.ds === 1) f.posting_date = ['>=', new Date(Date.now() - 7 * 864e5).toISOString().slice(0, 10)];
    if (t.ds === 2) f.posting_date = ['>=', new Date(Date.now() - 30 * 864e5).toISOString().slice(0, 10)];
    var docs = [];
    try {
      docs = await getList('Purchase Receipt', {
        fields: ['name', 'supplier', 'supplier_name', 'posting_date', 'set_warehouse'],
        filters: f, limit_page_length: 0, order_by: 'modified desc'
      });
    } catch (e) { }
    D[t.k] = docs; dem[t.k] = docs.length;
  }
  var all = [];
  for (var k2 in D) D[k2].forEach(function (x) { all.push(x.name); });
  var rows = [];
  if (all.length) {
    try {
      rows = await getList('Purchase Receipt Item', {
        parent: 'Purchase Receipt', fields: ['parent', 'qty', 'warehouse'],
        filters: { parent: ['in', all] }, limit_page_length: 0
      });
    } catch (e) { }
  }
  var CHIP = { cho: ['c2', 'Chờ nhận'], xong: ['d', 'Đã nhập kho'], huy: ['x', 'Đã huỷ'] };

  function tabsHtml() {
    return '<div class="vtb">' + TB.map(function (t) {
      return '<div class="vt' + (rcv.tab === t.k ? ' on' : '') + '" data-tb="' + t.k + '">' +
        h(t.ten) + (dem[t.k] ? ' <b>' + dem[t.k] + '</b>' : '') + '</div>';
    }).join('') + '</div>';
  }
  /* Danh sách đơn mua còn nợ hàng. Trễ hẹn lên đầu, vì đó là chuyến hàng
     đang chạy muộn chứ không phải chuyến vừa đặt hôm qua. */
  function poHtml() {
    var q = (rcv.q || '').toLowerCase().trim();
    var ls = poDs.filter(function (x) {
      if (!q) return true;
      return (x.name + ' ' + (x.ncc || '')).toLowerCase().indexOf(q) >= 0;
    });
    if (!ls.length) {
      return '<div class="emp"><div class="e1">✅</div><div class="e2">' +
        (poDs.length ? 'Không tìm thấy đơn nào' :
          'Không còn đơn mua nào đang nợ hàng.<br>Nhà cung cấp giao thiếu thì đơn đó sẽ hiện ở đây cho tới khi nhận đủ.') +
        '</div></div>';
    }
    return '<div class="lst">' + ls.map(function (x) {
      var tre = x.tre_ngay > 0;
      return '<div class="li" data-po="' + h(x.name) + '"><div class="lt">' +
        '<div class="l1">' + h(x.ncc || x.name) + '</div>' +
        '<div class="l2">' + h(x.name) + ' · còn ' + x.so_mon_con + '/' + x.so_mon + ' món' +
        (x.hen ? ' · hẹn ' + h(dmy(x.hen)) : '') + '</div></div>' +
        '<span style="text-align:right;flex:none">' +
        '<span class="vxtag ' + (tre ? 'x' : 'c2') + '">' + (tre ? 'Trễ ' + x.tre_ngay + ' ngày' : 'Chờ giao') + '</span>' +
        '<div style="font-size:12px;color:#98a2b3;margin-top:4px">đã nhận ' + Math.round(x.da_nhan_pt) + '%</div>' +
        '</span></div>';
    }).join('') + '</div>';
  }

  function listHtml() {
    if (rcv.tab === 'po') return poHtml();
    var q = (rcv.q || '').toLowerCase().trim();
    var ls = (D[rcv.tab] || []).filter(function (x) {
      if (!q) return true;
      return (x.name + ' ' + (x.supplier_name || x.supplier || '')).toLowerCase().indexOf(q) >= 0;
    });
    if (!ls.length) {
      var rong = rcv.tab === 'cho' ?
        'Chưa có phiếu nào chờ nhận hàng.<br>Thu mua tạo phiếu nhập kho nháp từ Đơn mua hàng thì phiếu sẽ hiện ở đây.' :
        (rcv.tab === 'xong' ? 'Chưa có phiếu nào nhập kho trong 7 ngày qua.' : 'Không có phiếu huỷ nào trong 30 ngày qua.');
      return '<div class="emp"><div class="e1">📦</div><div class="e2">' +
        ((D[rcv.tab] || []).length ? 'Không tìm thấy phiếu nào' : rong) + '</div></div>';
    }
    var c = CHIP[rcv.tab];
    return '<div class="lst">' + ls.map(function (x) {
      var rs = rows.filter(function (r) { return r.parent === x.name; });
      var whs = [];
      rs.forEach(function (r) { var w = shortWh(r.warehouse); if (w && whs.indexOf(w) < 0) whs.push(w); });
      return '<div class="li" data-p="' + h(x.name) + '"><div class="lt">' +
        '<div class="l1">' + h(x.supplier_name || x.supplier || x.name) + '</div>' +
        '<div class="l2">' + h(x.name) + ' · ' + rs.length + ' món · ' + h(whs.join(', ') || shortWh(x.set_warehouse) || '') + '</div></div>' +
        '<span style="text-align:right;flex:none"><span class="vxtag ' + c[0] + '">' + c[1] + '</span>' +
        '<div style="font-size:12px;color:#98a2b3;margin-top:4px">' + h(dmy(x.posting_date)) + '</div></span></div>';
    }).join('') + '</div>';
  }

  var body = tabsHtml() +
    '<div class="rcvh">Quét mã vạch số phiếu ở đầu tờ phiếu in để mở đúng phiếu, hoặc chọn trong danh sách bên dưới.</div>' +
    srchBox('rcvq', 'Tìm số phiếu hoặc nhà cung cấp', rcv.q, true) +
    '<div id="rcvl">' + listHtml() + '</div>';

  var b = frame('Nhập kho', body, { action: '&#128247;', onAction: rcvScanOpen });
  var qi = document.getElementById('rcvq');
  if (qi) qi.oninput = function () { rcv.q = qi.value; var el = document.getElementById('rcvl'); if (el) el.innerHTML = listHtml(); };
  var sb = document.getElementById('rcvqscan');
  if (sb) sb.onclick = rcvScanOpen;
  b.onclick = function (e) {
    var tb = e.target.closest('[data-tb]');
    if (tb) {
      rcv.tab = tb.dataset.tb;
      var ts = b.querySelectorAll('[data-tb]');
      for (var i = 0; i < ts.length; i++) ts[i].classList.toggle('on', ts[i].dataset.tb === rcv.tab);
      var el = document.getElementById('rcvl'); if (el) el.innerHTML = listHtml();
      return;
    }
    var rp = e.target.closest('[data-po]');
    if (rp) { var pn = rp.dataset.po; return go(function () { scrNhpDon(pn); }); }
    var r = e.target.closest('[data-p]');
    if (r) {
      var nm = r.dataset.p;
      if (rcv.tab === 'cho') return go(function () { scrRecvDoc(nm); });
      return go(function () { rcvXemXong(nm); });
    }
  };
}

/* Khu chung tu giao nhan: 2 anh hang + ban scan bien ban NCC */
/* Nút X ở góc từng tấm (anh Việt 24/08/2026). Phiếu nhập được ghi sổ ngay
   lúc lập nên không có nấc "chưa ghi sổ" để chặn; anh Việt chốt chỉ chặn khi
   phiếu đã huỷ. Đổi lại mỗi lần gỡ đều ghi vết ai gỡ, gỡ tấm nào. */
function rcvAnhHtml(doc) {
  var goDuoc = Number(doc.docstatus) !== 2;
  function o(url, ten, truong) {
    if (!url) return '';
    var laPdf = String(url).toLowerCase().indexOf('.pdf') >= 0;
    var trong = laPdf ? '<div class="rcvthf">📄</div>' : '<img class="rcvthi" src="' + h(url) + '" loading="lazy">';
    return '<span style="position:relative;display:inline-block">' +
      '<a class="rcvth" href="' + h(url) + '" target="_blank">' + trong + '<span>' + ten + '</span></a>' +
      (goDuoc
        ? '<span class="xo" data-rcvgo="' + h(truong) + '" data-ten="' + h(ten) + '" ' +
          'title="Gỡ tấm này" style="position:absolute;top:-6px;right:-6px">✕</span>' : '') +
      '</span>';
  }
  var s = o(doc.custom_hinh_nhan_hang_1, 'Ảnh hàng (1)', 'custom_hinh_nhan_hang_1') +
    o(doc.custom_hinh_nhan_hang_2, 'Ảnh hàng (2)', 'custom_hinh_nhan_hang_2') +
    o(doc.custom_scan_bien_ban, 'Biên bản NCC', 'custom_scan_bien_ban');
  if (!s) s = '<div style="color:#98a2b3;font-size:13px;padding:2px 14px 8px">Chưa đính kèm ảnh hay biên bản lúc nhận.</div>';
  return '<div class="sec">Chứng từ giao nhận</div><div class="rcvths">' + s + '</div>';
}

/* Xem phieu da nhap / da huy - chi doc */
async function rcvXemXong(name) {
  frame('Nhập kho', '<div class="emp"><div class="e1">⏳</div></div>');
  var doc = null;
  try { doc = await api('frappe.client.get', { doctype: 'Purchase Receipt', name: name }); }
  catch (e) { toast(errMsg(e)); return back(); }
  vgbCss();
  var tag = doc.docstatus === 1 ? '<span class="vxtag d">Đã nhập kho</span>' :
    (doc.docstatus === 2 ? '<span class="vxtag x">Đã huỷ</span>' : '<span class="vxtag c2">Chờ nhận</span>');
  var s = '<div class="card">' +
    '<div class="kv"><span>Nhà cung cấp</span><b>' + h(doc.supplier_name || doc.supplier || '') + '</b></div>' +
    '<div class="kv"><span>Ngày</span><b>' + h(dmy(doc.posting_date)) + '</b></div>' +
    '<div class="kv"><span>Trạng thái</span><b>' + tag + '</b></div></div>' +
    '<div class="sec">' + (doc.items || []).length + ' hàng hoá</div><div class="lst">' +
    (doc.items || []).map(function (r) {
      return '<div class="li"><div class="lt"><div class="l1">' + h(r.item_name || r.item_code) + '</div>' +
        '<div class="l2">' + h(r.item_code) + ' · ' + h(shortWh(r.warehouse) || '') + '</div></div>' +
        '<span class="st b">' + num(r.qty) + ' ' + h(r.uom || '') + '</span></div>';
    }).join('') + '</div>' + rcvAnhHtml(doc);
  var b = frame('Phiếu ' + name, s);
  b.addEventListener('click', async function (e) {
    var n = e.target.closest('[data-rcvgo]');
    if (!n) return;
    e.preventDefault();
    e.stopPropagation();
    var tr = n.getAttribute('data-rcvgo'), ten = n.getAttribute('data-ten');
    if (!await xacNhan('Gỡ "' + ten + '" khỏi phiếu ' + name + '?\n\n' +
      'Tệp vẫn còn trên máy chủ, chỉ bỏ khỏi phiếu này. Việc gỡ được ghi vết.',
      'Gỡ chứng từ giao nhận', 'Gỡ')) return;
    busy(1);
    try {
      await api('vagabond.nhan_hang.go_anh_nhan', { name: name, truong: tr });
      busy(0);
      toast('Đã gỡ ' + ten, 2800);
      go(function () { rcvXemXong(name); }, true);
    } catch (e2) { busy(0); baoTin(errMsg(e2) || 'Không gỡ được'); }
  });
}


async function rcvScanOpen() {
  var code = await scanBarcode(null);
  if (!code) return;
  code = String(code).trim().replace(/^\*+|\*+$/g, '').toUpperCase();
  busy(1);
  var r = [];
  try { r = await getList('Purchase Receipt', { fields: ['name', 'docstatus'], filters: { name: code }, limit_page_length: 1 }); } catch (e) { }
  busy(0);
  if (!r.length) return toast('Không thấy phiếu ' + code + ' trong hệ thống');
  if (r[0].docstatus === 1) return toast('Phiếu ' + code + ' đã nhập máy xong rồi');
  if (r[0].docstatus === 2) return toast('Phiếu ' + code + ' đã bị huỷ');
  go(function () { scrRecvDoc(code); });
}

var rcvD = null;

function hsdNote(x) {
  if (!x.hsd) return 'Món này chưa có hạn chuẩn, xem bao bì rồi điền giúp.';
  if (x.dflt) return 'Máy tự tính sẵn: ' + dmy(x.hsd) + '. Bao bì ghi hạn khác thì bấm vào sửa lại.';
  return 'Lấy theo bao bì: ' + dmy(x.hsd) + ', khác với hạn chuẩn.';
}
async function scrRecvDoc(name) {
  frame('Nhập kho', '<div class="emp"><div class="e1">\u23f3</div></div>');
  var doc = null;
  try { doc = await api('frappe.client.get', { doctype: 'Purchase Receipt', name: name }); }
  catch (e) { toast(errMsg(e)); return back(); }
  if (!doc || !doc.items || !doc.items.length) { toast('Phiếu này không có dòng hàng nào'); return back(); }

  var codes = doc.items.map(function (r) { return r.item_code; });
  var bat = {}, slf = {};
  var base = String(doc.posting_date || '').slice(0, 10) || today();
  try {
    var its = await getList('Item', { fields: ['name', 'has_batch_no', 'shelf_life_in_days'], filters: { name: ['in', codes] }, limit_page_length: 0 });
    its.forEach(function (x) { bat[x.name] = x.has_batch_no ? 1 : 0; slf[x.name] = x.shelf_life_in_days || 0; });
  } catch (e) { }

  /* Số CÒN PHẢI NHẬN của từng dòng đơn mua (anh Việt 15/08/2026).

     Phiếu nháp do thu mua tạo mang số ĐÃ ĐẶT. Nếu đơn này đã nhận một đợt
     rồi thì số đó lớn hơn số thực sự còn thiếu, và ô nhập điền sẵn theo nó
     là đường thẳng dẫn tới nhập trùng nguyên lô. Nên đọc lại từ đơn mua và
     lấy số nhỏ hơn trong hai số làm mặc định. */
  var poRow = {};
  var poKeys = [];
  doc.items.forEach(function (r) { if (r.purchase_order_item) poKeys.push(r.purchase_order_item); });
  if (poKeys.length) {
    try {
      var pos = await getList('Purchase Order Item', {
        parent: 'Purchase Order', fields: ['name', 'qty', 'received_qty'],
        filters: { name: ['in', poKeys] }, limit_page_length: 0
      });
      pos.forEach(function (x) {
        var con = (x.qty || 0) - (x.received_qty || 0);
        poRow[x.name] = { dat: x.qty || 0, daNhan: x.received_qty || 0, con: con > 0.0001 ? con : 0 };
      });
    } catch (ePo) { poRow = {}; }
  }

  rcvD = {
    name: name, doc: doc,
    anh1: doc.custom_hinh_nhan_hang_1 || '', anh2: doc.custom_hinh_nhan_hang_2 || '', scan: doc.custom_scan_bien_ban || '',
    lines: doc.items.map(function (r) {
      var po = poRow[r.purchase_order_item] || null;
      var tren = r.qty || 0;
      /* Trần và số điền sẵn LUÔN là số nhỏ hơn giữa "ghi trên phiếu nháp"
         và "còn thiếu thật trên đơn mua". Dòng không nối đơn mua nào thì
         giữ nguyên cách cũ. */
      var tran = po ? Math.min(tren, po.con) : tren;
      return {
        row: r.name, code: r.item_code, nm: r.item_name || r.item_code,
        uom: r.uom || r.stock_uom || '', wh: r.warehouse, ord: tran,
        tren: tren, po: po,
        got: tran, sl: slf[r.item_code] || 0,
        hsd: r.han_su_dung || (slf[r.item_code] ? addDays(base, slf[r.item_code]) : ''),
        dflt: r.han_su_dung ? 0 : 1, batch: bat[r.item_code] ? 1 : 0, ok: 0
      };
    })
  };

  function syncHdr() {
    var L = rcvD.lines, okN = L.filter(function (x) { return x.ok; }).length;
    var t = document.getElementById('rcvpt'), pb = document.getElementById('rcvpb');
    if (t) t.textContent = 'ĐÃ ĐẾM ' + okN + '/' + L.length + ' MÓN';
    if (pb) pb.style.width = (L.length ? Math.round(okN * 100 / L.length) : 0) + '%';
  }
  function syncRow(i) {
    var x = rcvD.lines[i], el = document.querySelector('#vgbBody [data-r="' + i + '"]');
    if (!el) return;
    if (x.ok) el.classList.add('ok'); else el.classList.remove('ok');
    if (x.got > 0) el.classList.remove('zero'); else el.classList.add('zero');
    var q = el.querySelector('[data-q]');
    if (q && String(q.value) !== String(x.got)) q.value = x.got;
    var lb = el.querySelector('.lb');
    if (lb) lb.innerHTML = 'Số lượng thực nhận' + (Math.abs(x.got - x.ord) > 0.0001 ? ' <b class="lbw">(khác số còn lại)</b>' : '');
    syncHdr();
  }

  async function scanTick() {
    await scanBarcode(async function (code) {
      var ic = await itemByBarcode(code);
      if (!ic) return 'Chưa nhận ra mã ' + code;
      var i = -1, L = rcvD.lines;
      for (var j = 0; j < L.length; j++) if (L[j].code === ic) { i = j; break; }
      if (i < 0) return ic + ' không có trong phiếu này';
      L[i].ok = 1;
      syncRow(i);
      return '\u2713 ' + L[i].nm + ' \u00b7 còn phải nhận ' + num(L[i].ord) + ' ' + L[i].uom;
    });
  }

  async function doSubmit() {
    var L = rcvD.lines;
    var keep = L.filter(function (x) { return (x.got || 0) > 0; });
    if (!keep.length) return toast('Chưa có món nào có số lượng, chưa nhập kho được');
    var du = L.filter(function (x) { return (x.got || 0) > (x.ord || 0) + 0.0001; });
    if (du.length) return toast('Nhà cung cấp giao dư ' + du.length + ' món so với số còn phải nhận. Chỉ nhập đúng số còn lại, phần dư báo chị Uyên lên đơn bổ sung rồi nhập sau.', 7000);
    var thieu = L.filter(function (x) { return (x.got || 0) < (x.ord || 0) - 0.0001; });
    var msg = 'Nhập kho ' + keep.length + ' món.';
    if (thieu.length) msg += ' Có ' + thieu.length + ' món nhận thiếu hoặc không về, phần còn lại vẫn treo trên đơn mua hàng - vào tab "Còn phải nhận" để nhận đợt sau.';
    msg += ' Xác nhận xong là phiếu khoá lại, muốn sửa phải báo kế toán.';
    if (!await confirmSheet('Xác nhận nhập kho?', msg, 'Nhập kho')) return;
    busy(1);
    try {
      var d = rcvD.doc, byRow = {};
      if (rcvD.anh1) d.custom_hinh_nhan_hang_1 = rcvD.anh1;
      if (rcvD.anh2) d.custom_hinh_nhan_hang_2 = rcvD.anh2;
      if (rcvD.scan) d.custom_scan_bien_ban = rcvD.scan;
      L.forEach(function (x) { byRow[x.row] = x; });
      d.items = d.items.filter(function (r) { var x = byRow[r.name]; return x && x.got > 0; });
      d.items.forEach(function (r) {
        var x = byRow[r.name];
        r.qty = x.got; r.received_qty = x.got; r.rejected_qty = 0;
        if (x.batch && x.hsd) r.han_su_dung = x.hsd;
      });
      /* Bo sung gia tam cho dong chua co gia tren don */
      var zeroRows = d.items.filter(function (r) { return !((r.rate || 0) > 0); });
      var chuaGia = [];
      if (zeroRows.length) {
        var zc = [];
        zeroRows.forEach(function (r) { if (zc.indexOf(r.item_code) < 0) zc.push(r.item_code); });
        var lastP = {};
        try {
          var pri = await getList('Purchase Receipt Item', {
            parent: 'Purchase Receipt',
            fields: ['item_code', 'rate', 'conversion_factor', 'creation'],
            filters: { item_code: ['in', zc], docstatus: 1, rate: ['>', 0] },
            order_by: 'creation desc', limit_page_length: 0
          });
          pri.forEach(function (x) { if (!lastP[x.item_code]) lastP[x.item_code] = x; });
        } catch (e1) { }
        var conCan = zc.filter(function (c0) { return !lastP[c0]; });
        if (conCan.length) {
          try {
            var poi = await getList('Purchase Order Item', {
              parent: 'Purchase Order',
              fields: ['item_code', 'rate', 'conversion_factor', 'creation'],
              filters: { item_code: ['in', conCan], docstatus: 1, rate: ['>', 0] },
              order_by: 'creation desc', limit_page_length: 0
            });
            poi.forEach(function (x) { if (!lastP[x.item_code]) lastP[x.item_code] = x; });
          } catch (e2) { }
        }
        zeroRows.forEach(function (r) {
          var gg = r.purchase_order ? null : lastP[r.item_code];
          if (gg) {
            var donVi = (gg.rate || 0) / (gg.conversion_factor || 1);
            r.rate = Math.round(donVi * (r.conversion_factor || 1) * 100) / 100;
          } else {
            r.allow_zero_valuation_rate = 1;
            chuaGia.push(r.item_name || r.item_code);
          }
        });
        d.remarks = (d.remarks || '') + (chuaGia.length
          ? ' | Nhap kho khi chua co gia: ' + chuaGia.join(', ') + ' - ke toan bo sung gia sau.'
          : ' | May tu lay gia mua gan nhat cho ' + zeroRows.length + ' dong chua co gia tren don.');
        if (chuaGia.length) setTimeout(function () { toast('Có ' + chuaGia.length + ' món nhập kho khi chưa có giá. Vui lòng báo kế toán bổ sung giá.', 7000); }, 1400);
      }

      await api('frappe.client.submit', { doc: d });
      busy(0);
      rcv.tab = 'xong';
      toast('✓ Đã nhập kho phiếu ' + rcvD.name + '. Phiếu nằm ở tab Đã nhập kho.');
      return back();
    } catch (e) { busy(0); toast(errMsg(e)); }
  }

  function draw() {
    var L = rcvD.lines;
    var okN = L.filter(function (x) { return x.ok; }).length;
    var body = '<div class="card"><div class="kpg"><div class="kpt" id="rcvpt">ĐÃ ĐẾM ' + okN + '/' + L.length + ' MÓN</div>' +
      '<div class="kpb"><i id="rcvpb" style="width:' + (L.length ? Math.round(okN * 100 / L.length) : 0) + '%"></i></div></div>' +
      '<div class="kv"><span>Nhà cung cấp</span><b>' + h(doc.supplier_name || doc.supplier || '') + '</b></div>' +
      '<div class="kv"><span>Số phiếu</span><b>' + h(name) + '</b></div></div>';
    body += '<div class="rcvh">Số điền sẵn là <b>số còn lại phải nhận</b>, không phải số đã đặt ban đầu. Đếm tới đâu sửa số tới đó. Không nhập quá số còn lại: nhà cung cấp giao dư thì báo thu mua lên đơn bổ sung. Bấm nút máy ảnh ở góc trên để quét mã từng món cho nhanh.</div>';
    var chuaGiaN = (doc.items || []).filter(function (rr) { return !((rr.rate || 0) > 0); }).length;
    if (chuaGiaN) body += '<div style="margin:10px 12px;padding:12px 14px;border-radius:14px;background:#fff6e5;color:#8a5b00;font-size:13px;line-height:1.5">Đơn này có ' + chuaGiaN + ' món chưa có đơn giá. Vẫn nhập kho được nhưng giá vốn ghi 0, nhớ báo kế toán bổ sung giá.</div>';
    body += L.map(function (x, i) {
      return '<div class="ic1' + (x.ok ? ' ok' : '') + (x.got > 0 ? '' : ' zero') + '" data-r="' + i + '">' +
        '<div class="ih"><div class="n">' + (i + 1) + '</div>' +
        '<div class="in">' + h(x.nm) +
        '<div class="ig">' + h(x.code) + ' \u00b7 ' + h(shortWh(x.wh) || '') + '</div></div>' +
        '<div class="rok" data-ok="' + i + '">&#10003;</div></div>' +
        (x.po
          ? nhpBaSo({ sl_dat: x.po.dat, sl_da_nhan: x.po.daNhan, sl_con: x.po.con })
          : '<div style="padding:0 12px 8px;font-size:12.5px;color:#5a6070">Đặt ' + num(x.ord) + ' ' + h(x.uom) + '</div>') +
        '<div class="qw"><div style="flex:1;min-width:0">' +
        '<div class="lb">Số lượng thực nhận' + (Math.abs(x.got - x.ord) > 0.0001 ? ' <b class="lbw">(khác số còn lại)</b>' : '') + '</div>' +
        '<div class="qr"><div class="stp"><button data-m="' + i + '">&minus;</button>' +
        '<input type="number" inputmode="decimal" step="any" data-q="' + i + '" value="' + x.got + '">' +
        '<button data-a="' + i + '">+</button></div>' +
        '<div class="uml">' + h(x.uom) + '</div></div></div></div>' +
        (x.batch ? '<div class="hw"><div class="hl">Hạn sử dụng' +
          (x.sl ? '<b class="hbd">chuẩn ' + x.sl + ' ngày</b>' : '') + '</div>' +
          '<input type="date" class="hin' + (x.dflt ? '' : ' ed') + '" data-h="' + i + '" value="' + h(x.hsd) + '">' +
          '<div class="hn' + (x.dflt ? '' : ' ed') + '" data-hn="' + i + '">' + hsdNote(x) + '</div></div>' : '') +
        '</div>';
    }).join('');
    vgbCss();
    body += '<div class="sec">Chứng từ giao nhận (không bắt buộc)</div><div class="card" style="padding:12px">' +
      '<div class="vxl" style="margin-top:0">Ảnh hàng đã nhận (1)</div>' +
      '<input class="vxi" type="file" accept="image/*" id="rcvA1">' +
      '<div id="rcvA1ok" style="font-size:13px;color:#027a48;margin-top:4px"></div>' +
      '<div class="vxl">Ảnh hàng đã nhận (2)</div>' +
      '<input class="vxi" type="file" accept="image/*" id="rcvA2">' +
      '<div id="rcvA2ok" style="font-size:13px;color:#027a48;margin-top:4px"></div>' +
      '<div class="vxl">Bản scan hoặc ảnh biên bản giao nhận của NCC</div>' +
      '<input class="vxi" type="file" accept="image/*,.pdf" id="rcvA3">' +
      '<div id="rcvA3ok" style="font-size:13px;color:#027a48;margin-top:4px"></div></div>';

    var b = frame('Nhập kho', body, {
      action: '&#128247;', onAction: scanTick,
      footer: '<button class="btn" id="rcvSub">Xác nhận nhập kho</button>'
    });
    b.onclick = function (e) {
      var t = e.target.closest('[data-ok]');
      if (t) { var i = parseInt(t.dataset.ok, 10); L[i].ok = L[i].ok ? 0 : 1; return syncRow(i); }
      t = e.target.closest('[data-m]');
      if (t) { var j = parseInt(t.dataset.m, 10); L[j].got = Math.max(0, r3(L[j].got - 1)); L[j].ok = 1; return syncRow(j); }
      t = e.target.closest('[data-a]');
      if (t) { var k = parseInt(t.dataset.a, 10); var v1 = r3(L[k].got + 1); if (v1 > L[k].ord + 0.0001) { v1 = L[k].ord; toast('Chỉ nhập được tối đa ' + num(L[k].ord) + ' ' + L[k].uom + ' vì đơn chỉ còn thiếu chừng đó. Hàng giao dư phải báo thu mua lên đơn bổ sung.', 5500); } L[k].got = v1; L[k].ok = 1; return syncRow(k); }
    };
    Array.prototype.forEach.call(b.querySelectorAll('[data-q]'), function (el) {
      el.onchange = function () { var i = parseInt(el.dataset.q, 10); var v2 = Math.max(0, parseFloat(el.value) || 0); if (v2 > L[i].ord + 0.0001) { v2 = L[i].ord; toast('Chỉ nhập được tối đa ' + num(L[i].ord) + ' ' + L[i].uom + ' vì đơn chỉ còn thiếu chừng đó. Hàng giao dư phải báo thu mua lên đơn bổ sung.', 5500); } L[i].got = v2; L[i].ok = 1; syncRow(i); };
    });
    Array.prototype.forEach.call(b.querySelectorAll('[data-h]'), function (el) {
      el.onchange = function () {
        var i = parseInt(el.dataset.h, 10), x = L[i];
        if (!el.value && x.sl) el.value = addDays(base, x.sl);
        x.hsd = el.value || '';
        x.dflt = (x.sl && x.hsd === addDays(base, x.sl)) ? 1 : 0;
        el.classList.toggle('ed', !x.dflt);
        var nt = b.querySelector('[data-hn="' + i + '"]');
        if (nt) { nt.textContent = hsdNote(x); nt.classList.toggle('ed', !x.dflt); }
      };
    });
    var sb = document.getElementById('rcvSub');
    if (sb) sb.onclick = doSubmit;
    function ganAnh(id, key) {
      var inp = document.getElementById(id), ok = document.getElementById(id + 'ok');
      if (!inp) return;
      if (rcvD[key]) ok.innerHTML = 'Đã có tệp: <a href="' + h(rcvD[key]) + '" target="_blank">xem</a>';
      inp.onchange = async function () {
        var f = this.files && this.files[0];
        if (!f) return;
        ok.textContent = 'Đang tải lên...';
        try {
          rcvD[key] = await vxUpAnh(f);
          ok.innerHTML = 'Đã tải lên: <a href="' + h(rcvD[key]) + '" target="_blank">xem</a>';
        } catch (e) { ok.style.color = '#d92d20'; ok.textContent = 'Không tải được: ' + (e.message || e); }
      };
    }
    ganAnh('rcvA1', 'anh1'); ganAnh('rcvA2', 'anh2'); ganAnh('rcvA3', 'scan');
  }
  draw();
}

/* ---------- 13b. Nhan hang dot tiep theo, mo thang tu Don mua ----------

   Anh Viet duyet 15/08/2026, phuong an B: KHONG sinh phieu nhap nhap cho
   phan con lai. Nguon su that la don mua, dung thiet ke ERPNext. Thu kho mo
   thang don ra bam "Nhan hang dot nay", may chu dung phieu moi tu don.

   Ba diem chong nham, xep theo muc quan trong:

   1. O nhap MAC DINH bang CON LAI, khong phai bang so da dat. Man phieu
      nhap cu dang mac dinh bang so dat, nen dot hai ma quen sua la nhap
      trung nguyen lo. Day la loi ton tien that.
   2. Moi dong bay du BA con so: Dat, Da nhan, Con lai. Khong bat ai tru
      trong dau.
   3. Mon da nhan du thi lam mo, khong cho go, va nam cuoi danh sach.

   Tien to nhp = nhan hang theo phieu dat. Da kiem va cham ten truoc khi
   dat, dung QT-28. */

var nhpD = null;

function nhpSo(v) { return Math.round((Number(v) || 0) * 1000) / 1000; }

/* Ba con so tren mot dong. Con lai to dam va doi mau khi con no hang, vi
   day moi la con so thu kho phai nhin. */
/* Cau nhac ngay duoi o so luong: nhan du bao nhieu, con trong dung sai hay
   khong, va han dung co du dai khong. */
function nhpNhac(x) {
  var ra = [];
  var du = (x.got || 0) - (x.con || 0);
  if (du > 0.0001) {
    if (du <= (x.duCP || 0) + 0.0005) {
      ra.push('<span style="color:#b45309">Nhận dư ' + num(du) + ' ' + h(x.uom) +
        ', còn trong dung sai nên máy cho nhận và ghi lại vết.</span>');
    } else {
      ra.push('<span style="color:#b3261e">Nhận dư ' + num(du) + ' ' + h(x.uom) +
        ', vượt mức cho phép ' + num(x.duCP || 0) + ' ' + h(x.uom) + '. Báo thu mua lên đơn bổ sung.</span>');
    }
  }
  if (x.batHsd && (x.got || 0) > 0.0001 && !x.hsd) {
    ra.push('<span style="color:#b3261e">Mặt hàng theo lô: phải điền hạn sử dụng mới nhập được.</span>');
  }
  if (x.hsdMin && x.hsd) {
    var con = Math.round((new Date(x.hsd) - new Date(today())) / 86400000);
    if (con < x.hsdMin) {
      ra.push('<span style="color:#b3261e">Hạn dùng chỉ còn ' + con + ' ngày, mặt hàng này cần ít nhất ' +
        x.hsdMin + ' ngày. Đổi lô khác hoặc báo thu mua.</span>');
    }
  }
  if (!ra.length) return '';
  return '<div style="font-size:12.5px;line-height:1.5;padding:0 12px 8px">' + ra.join('<br>') + '</div>';
}

function nhpBaSo(x) {
  function o(nhan, gt, mau, dam) {
    return '<div style="flex:1;min-width:0;text-align:center">' +
      '<div style="font-size:11px;color:#98a2b3;text-transform:uppercase;letter-spacing:.3px">' + nhan + '</div>' +
      '<div style="font-size:15px;font-weight:' + (dam ? '800' : '600') + ';color:' + mau + '">' + num(gt) + '</div></div>';
  }
  var con = x.sl_con > 0.0001;
  return '<div style="display:flex;gap:6px;padding:8px 12px;background:#f7f8fa;border-radius:11px;margin:0 12px 8px">' +
    o('Đặt', x.sl_dat, '#5a6070', 0) +
    o('Đã nhận', x.sl_da_nhan, '#5a6070', 0) +
    o('Còn lại', x.sl_con, con ? '#0d9488' : '#98a2b3', 1) + '</div>';
}

async function scrNhpDon(don) {
  frame('Nhận hàng', '<div class="emp"><div class="e1">⏳</div></div>');
  var d = null;
  try { d = await api('vagabond.nhan_hang.chi_tiet', { don: don }); }
  catch (e) { toast(errMsg(e)); return back(); }
  vgbCss();

  var base = today();
  nhpD = {
    don: don, d: d,
    anh1: '', anh2: '', scan: '',
    lines: (d.mon || []).map(function (m) {
      return {
        dong: m.dong, code: m.ma, nm: m.ten, uom: m.dvt, wh: m.kho,
        dat: m.sl_dat, daNhan: m.sl_da_nhan, con: m.sl_con,
        /* MAC DINH BANG CON LAI. Day la chot chan chong nhap trung lo. */
        got: m.sl_con,
        batch: m.co_lo ? 1 : 0, sl: m.han_chuan || 0,
        hsd: m.han_chuan ? addDays(base, m.han_chuan) : '',
        /* Dung sai giao thua va han dung toi thieu (v406, hoc tu SAP). Man
           hinh noi TRUOC, khong de nguoi ta dem xong bam Luu moi biet la
           may khong nhan. */
        duCP: m.du_cho_phep || 0,
        hsdMin: m.hsd_toi_thieu || 0,
        batHsd: m.bat_buoc_hsd ? 1 : 0,
        dflt: 1, ok: 0
      };
    })
  };
  var L = nhpD.lines;
  var conL = L.filter(function (x) { return x.con > 0.0001; });

  function syncHdr() {
    var okN = conL.filter(function (x) { return x.ok; }).length;
    var t = document.getElementById('nhppt'), pb = document.getElementById('nhppb');
    if (t) t.textContent = 'ĐÃ ĐẾM ' + okN + '/' + conL.length + ' MÓN';
    if (pb) pb.style.width = (conL.length ? Math.round(okN * 100 / conL.length) : 0) + '%';
  }
  function syncRow(i) {
    var x = L[i], el = document.querySelector('#vgbBody [data-nr="' + i + '"]');
    if (!el) return;
    el.classList.toggle('ok', !!x.ok);
    el.classList.toggle('zero', !(x.got > 0));
    var q = el.querySelector('[data-nq]');
    if (q && String(q.value) !== String(x.got)) q.value = x.got;
    var lb = el.querySelector('.lb');
    if (lb) lb.innerHTML = 'Số lượng thực nhận' +
      (Math.abs(x.got - x.con) > 0.0001 ? ' <b class="lbw">(khác số còn lại)</b>' : '');
    var wn = el.querySelector('[data-nwn]');
    if (wn) wn.innerHTML = nhpNhac(x);
    syncHdr();
  }

  async function nhpLuu() {
    var gui = L.filter(function (x) { return (x.got || 0) > 0.0001; });
    if (!gui.length) return toast('Chưa có món nào có số lượng, chưa nhập kho được');
    var thieu = conL.filter(function (x) { return (x.got || 0) < x.con - 0.0001; });
    var msg = 'Nhập kho ' + gui.length + ' món cho đợt ' + d.dot_toi + '.';
    if (thieu.length) msg += ' Còn ' + thieu.length + ' món nhận thiếu, phần chưa nhận vẫn treo trên đơn mua để lần sau nhận tiếp.';
    msg += ' Xác nhận xong là phiếu khoá lại, muốn sửa phải báo kế toán.';
    if (!await confirmSheet('Xác nhận nhận hàng?', msg, 'Nhận hàng')) return;
    busy(1);
    try {
      var r = await api('vagabond.nhan_hang.tao_phieu', {
        don: don,
        dong: JSON.stringify(gui.map(function (x) {
          return { dong: x.dong, sl: x.got, hsd: (x.batch && x.hsd) ? x.hsd : '' };
        })),
        anh1: nhpD.anh1, anh2: nhpD.anh2, scan: nhpD.scan
      });
      busy(0);
      if (r.nhan_du && r.nhan_du.length) {
        setTimeout(function () { toast('Đã ghi vết ' + r.nhan_du.length + ' món nhận dư trong dung sai lên phiếu nhập.', 6000); }, 700);
      }
      if (r.thieu_gia && r.thieu_gia.length) {
        setTimeout(function () { toast('Có ' + r.thieu_gia.length + ' món nhập khi chưa có giá. Vui lòng báo kế toán bổ sung giá.', 7000); }, 1400);
      }
      toast('✓ Đã nhận hàng đợt ' + r.dot + ', phiếu ' + r.phieu + '.' +
        (r.con_lai > 0.0001 ? ' Đơn còn nợ ' + num(r.con_lai) + ' đơn vị của ' + r.so_mon_con + ' món.' : ' Đơn đã nhận đủ.'), 6000);
      rcv.tab = r.con_lai > 0.0001 ? 'po' : 'xong';
      return back();
    } catch (e) { busy(0); toast(errMsg(e), 7000); }
  }

  async function nhpDong() {
    var ly = await promptSheet('Đóng phần còn lại của đơn ' + don,
      'Nhà cung cấp báo không giao nữa, hay mình đổi sang mua nơi khác? Ghi lý do để sau này còn đối chiếu.');
    if (ly === null) return;
    if (!ly) return toast('Phải ghi lý do thì sau này còn biết vì sao đơn không nhận đủ.', 5000);
    if (!await confirmSheet('Đóng phần còn lại?',
      'Đơn ' + don + ' sẽ không hiện ở tab Còn phải nhận nữa. Số lượng đã đặt giữ nguyên, không sửa và không xoá dòng nào - mở lại được bất cứ lúc nào.', 'Đóng phần còn lại', true)) return;
    busy(1);
    try {
      await api('vagabond.nhan_hang.dong_con_lai', { don: don, ly_do: ly });
      busy(0); toast('Đã đóng phần còn lại của đơn ' + don);
      rcv.tab = 'po'; return back();
    } catch (e) { busy(0); toast(errMsg(e), 6000); }
  }

  function draw() {
    var okN = conL.filter(function (x) { return x.ok; }).length;
    var tre = d.tre_ngay > 0;
    var body = '<div class="card"><div class="kpg"><div class="kpt" id="nhppt">ĐÃ ĐẾM ' + okN + '/' + conL.length + ' MÓN</div>' +
      '<div class="kpb"><i id="nhppb" style="width:' + (conL.length ? Math.round(okN * 100 / conL.length) : 0) + '%"></i></div></div>' +
      '<div class="kv"><span>Nhà cung cấp</span><b>' + h(d.ncc) + '</b></div>' +
      '<div class="kv"><span>Đơn mua</span><b>' + h(don) + '</b></div>' +
      (d.hen ? '<div class="kv"><span>Hẹn giao</span><b' + (tre ? ' style="color:#b3261e"' : '') + '>' + h(dmy(d.hen)) +
        (tre ? ' · trễ ' + d.tre_ngay + ' ngày' : '') + '</b></div>' : '') +
      '<div class="kv"><span>Đã nhận</span><b>' + Math.round(d.da_nhan_pt) + '% · còn ' + d.so_mon_con + ' món</b></div></div>';

    /* Băng lịch sử: thủ kho biết ngay đợt trước ai nhận cái gì, không phải
       mở đơn mua ra dò. */
    if ((d.lich_su || []).length) {
      body += '<div class="sec">Đã nhận ' + d.lich_su.length + ' đợt trước</div><div class="lst">' +
        d.lich_su.map(function (x) {
          return '<div class="li"><div class="lt"><div class="l1">Đợt ' + x.dot + ' · ' + h(dmy(x.ngay)) + '</div>' +
            '<div class="l2">Phiếu ' + h(x.name) + '</div></div>' +
            '<span class="st b">' + x.so_mon + ' món · ' + num(x.sl) + '</span></div>';
        }).join('') + '</div>';
    }

    body += '<div class="rcvh">Số điền sẵn là <b>số còn lại phải nhận</b>, không phải số đã đặt ban đầu. Đếm tới đâu sửa số tới đó. Nhà cung cấp giao dư trong <b>' +
      num(d.dung_sai_thua || 0) + '%</b> thì máy cho nhận và ghi lại vết; dư nhiều hơn thì báo thu mua lên đơn bổ sung.</div>';

    body += '<div class="sec">Đợt ' + d.dot_toi + ' · ' + conL.length + ' món còn phải nhận</div>';
    body += L.map(function (x, i) {
      var het = x.con <= 0.0001;
      /* Món đã nhận đủ: làm mờ, không cho gõ. Thủ kho chỉ nhìn thấy việc
         còn phải làm, phần đã xong chỉ để đối chiếu. */
      if (het) {
        return '<div class="ic1" data-nr="' + i + '" style="opacity:.5">' +
          '<div class="ih"><div class="n">✓</div>' +
          '<div class="in">' + h(x.nm) + '<div class="ig">' + h(x.code) + ' · đã nhận đủ ' + num(x.dat) + ' ' + h(x.uom) + '</div></div></div></div>';
      }
      return '<div class="ic1' + (x.ok ? ' ok' : '') + (x.got > 0 ? '' : ' zero') + '" data-nr="' + i + '">' +
        '<div class="ih"><div class="n">' + (i + 1) + '</div>' +
        '<div class="in">' + h(x.nm) +
        '<div class="ig">' + h(x.code) + ' · ' + h(shortWh(x.wh) || '') + '</div></div>' +
        '<div class="rok" data-nok="' + i + '">&#10003;</div></div>' +
        nhpBaSo({ sl_dat: x.dat, sl_da_nhan: x.daNhan, sl_con: x.con }) +
        '<div class="qw"><div style="flex:1;min-width:0">' +
        '<div class="lb">Số lượng thực nhận' + (Math.abs(x.got - x.con) > 0.0001 ? ' <b class="lbw">(khác số còn lại)</b>' : '') + '</div>' +
        '<div class="qr"><div class="stp"><button data-nm2="' + i + '">&minus;</button>' +
        '<input type="number" inputmode="decimal" step="any" data-nq="' + i + '" value="' + x.got + '">' +
        '<button data-na="' + i + '">+</button></div>' +
        '<div class="uml">' + h(x.uom) + '</div></div></div></div>' +
        (x.batch ? '<div class="hw"><div class="hl">Hạn sử dụng' +
          (x.sl ? '<b class="hbd">chuẩn ' + x.sl + ' ngày</b>' : '') +
          (x.hsdMin ? '<b class="hbd">tối thiểu ' + x.hsdMin + ' ngày</b>' : '') + '</div>' +
          '<input type="date" class="hin' + (x.dflt ? '' : ' ed') + '" data-nh="' + i + '" value="' + h(x.hsd) + '">' +
          '<div class="hn' + (x.dflt ? '' : ' ed') + '" data-nhn="' + i + '">' + hsdNote(x) + '</div></div>' : '') +
        '<div data-nwn="' + i + '">' + nhpNhac(x) + '</div>' +
        '</div>';
    }).join('');

    body += '<div class="sec">Chứng từ giao nhận (không bắt buộc)</div><div class="card" style="padding:12px">' +
      '<div class="vxl" style="margin-top:0">Ảnh hàng đã nhận (1)</div>' +
      '<input class="vxi" type="file" accept="image/*" id="nhpA1">' +
      '<div id="nhpA1ok" style="font-size:13px;color:#027a48;margin-top:4px"></div>' +
      '<div class="vxl">Ảnh hàng đã nhận (2)</div>' +
      '<input class="vxi" type="file" accept="image/*" id="nhpA2">' +
      '<div id="nhpA2ok" style="font-size:13px;color:#027a48;margin-top:4px"></div>' +
      '<div class="vxl">Bản scan hoặc ảnh biên bản giao nhận của NCC</div>' +
      '<input class="vxi" type="file" accept="image/*,.pdf" id="nhpA3">' +
      '<div id="nhpA3ok" style="font-size:13px;color:#027a48;margin-top:4px"></div></div>';

    body += '<div class="card" style="padding:12px"><button class="btn" id="nhpDong" style="background:#fff;color:#b3261e;border:1px solid #fecaca;margin:0">Nhà cung cấp không giao nữa · đóng phần còn lại</button>' +
      '<div style="font-size:11.5px;color:#98a2b3;margin-top:8px;line-height:1.55">Đóng thì đơn không hiện ở tab Còn phải nhận nữa. Số đã đặt giữ nguyên, không xoá dòng nào, mở lại được bất cứ lúc nào.</div></div>';

    var b = frame('Nhận hàng đợt ' + d.dot_toi, body, {
      footer: '<button class="btn" id="nhpSub">Xác nhận nhận hàng đợt ' + d.dot_toi + '</button>'
    });
    b.onclick = function (e) {
      var t = e.target.closest('[data-nok]');
      if (t) { var i = parseInt(t.dataset.nok, 10); L[i].ok = L[i].ok ? 0 : 1; return syncRow(i); }
      t = e.target.closest('[data-nm2]');
      if (t) { var j = parseInt(t.dataset.nm2, 10); L[j].got = Math.max(0, nhpSo(L[j].got - 1)); L[j].ok = 1; return syncRow(j); }
      t = e.target.closest('[data-na]');
      if (t) {
        var k = parseInt(t.dataset.na, 10), v = nhpSo(L[k].got + 1);
        if (v > L[k].con + 0.0001) { v = L[k].con; toast('Chỉ nhận được tối đa ' + num(L[k].con) + ' ' + L[k].uom + ' vì đơn chỉ còn thiếu chừng đó. Giao dư thì báo thu mua lên đơn bổ sung.', 5500); }
        L[k].got = v; L[k].ok = 1; return syncRow(k);
      }
    };
    Array.prototype.forEach.call(b.querySelectorAll('[data-nq]'), function (el) {
      el.onchange = function () {
        var i = parseInt(el.dataset.nq, 10), v = Math.max(0, parseFloat(el.value) || 0);
        if (v > L[i].con + 0.0001) { v = L[i].con; toast('Chỉ nhận được tối đa ' + num(L[i].con) + ' ' + L[i].uom + ' vì đơn chỉ còn thiếu chừng đó. Giao dư thì báo thu mua lên đơn bổ sung.', 5500); }
        L[i].got = v; L[i].ok = 1; syncRow(i);
      };
    });
    Array.prototype.forEach.call(b.querySelectorAll('[data-nh]'), function (el) {
      el.onchange = function () {
        var i = parseInt(el.dataset.nh, 10), x = L[i];
        if (!el.value && x.sl) el.value = addDays(base, x.sl);
        x.hsd = el.value || '';
        x.dflt = (x.sl && x.hsd === addDays(base, x.sl)) ? 1 : 0;
        el.classList.toggle('ed', !x.dflt);
        var nt = b.querySelector('[data-nhn="' + i + '"]');
        if (nt) { nt.textContent = hsdNote(x); nt.classList.toggle('ed', !x.dflt); }
      };
    });
    var sb = document.getElementById('nhpSub');
    if (sb) sb.onclick = nhpLuu;
    var db = document.getElementById('nhpDong');
    if (db) db.onclick = nhpDong;
    function ganAnh(id, key) {
      var inp = document.getElementById(id), ok = document.getElementById(id + 'ok');
      if (!inp) return;
      inp.onchange = async function () {
        var f = this.files && this.files[0];
        if (!f) return;
        ok.textContent = 'Đang tải lên...';
        try {
          nhpD[key] = await vxUpAnh(f);
          ok.innerHTML = 'Đã tải lên: <a href="' + h(nhpD[key]) + '" target="_blank">xem</a>';
        } catch (e) { ok.style.color = '#d92d20'; ok.textContent = 'Không tải được: ' + (e.message || e); }
      };
    }
    ganAnh('nhpA1', 'anh1'); ganAnh('nhpA2', 'anh2'); ganAnh('nhpA3', 'scan');
  }
  draw();
}

/* ---------- 14. Dang nhap - Tai khoan ---------- */
function scrLogin() {
  root.innerHTML =
    '<div class="lgw"><div class="lgb">' +
      '<img class="lgo" src="/files/vagabond_logo_print.png" alt="The Vagabond Pâtisserie">' +
      '<div class="lgc">' +
        '<div class="lgl">Tài khoản (email)</div>' +
        '<input class="lgi" id="lgU" type="email" inputmode="email" autocomplete="username" autocapitalize="off" autocorrect="off" spellcheck="false" placeholder="email@vagabond">' +
        '<div class="lgl">Mật khẩu</div>' +
        '<input class="lgi" id="lgP" type="password" autocomplete="current-password" placeholder="Nhập mật khẩu">' +
        '<div class="lge" id="lgE"></div>' +
        '<button class="btn" id="lgGo">Đăng nhập</button>' +
        '<div class="lgfp" id="lgFp">Quên mật khẩu?</div>' +
      '</div>' +
      '<div class="lgf">Ứng dụng nghiệp vụ nội bộ<br>Chưa có mật khẩu thì bấm dòng Quên mật khẩu ở trên.</div>' +
    '</div></div>';
  var iu = document.getElementById('lgU'), ip = document.getElementById('lgP'), ie = document.getElementById('lgE');
  function fail(m) { ie.textContent = m || ''; }
  var running = 0;
  async function doLogin() {
    if (running) return;
    var usr = (iu.value || '').trim(), pwd = ip.value || '';
    if (!usr || !pwd) return fail('Nhập đủ tài khoản và mật khẩu.');
    fail(''); running = 1; busy(1);
    try {
      var hd = { 'Content-Type': 'application/json', 'Accept': 'application/json' };
      try { if (window.frappe && frappe.csrf_token) hd['X-Frappe-CSRF-Token'] = frappe.csrf_token; } catch (e) { }
      var r = await fetch('/api/method/login', { method: 'POST', headers: hd, credentials: 'same-origin', body: JSON.stringify({ usr: usr, pwd: pwd }) });
      running = 0; busy(0);
      if (r.ok) { clearFresh(); hardNav(); return; }
      if (r.status === 401) return fail('Sai tài khoản hoặc mật khẩu.');
      if (r.status === 417) return fail('Tài khoản đang bị khoá hoặc chưa được kích hoạt.');
      fail('Không đăng nhập được (mã ' + r.status + ').');
    } catch (e) { running = 0; busy(0); fail('Lỗi kết nối, kiểm tra mạng rồi thử lại.'); }
  }
  var fp = document.getElementById('lgFp');
  if (fp) fp.onclick = async function () {
    var em = (iu.value || '').trim();
    ie.style.color = '#c0392b';
    if (!em) { iu.focus(); return fail('Nhập địa chỉ email của bạn vào ô trên rồi bấm lại dòng này.'); }
    fail(''); busy(1);
    try {
      var hf = { 'Content-Type': 'application/json', 'Accept': 'application/json' };
      try { if (window.frappe && frappe.csrf_token) hf['X-Frappe-CSRF-Token'] = frappe.csrf_token; } catch (e) { }
      var rr = await fetch('/api/method/frappe.core.doctype.user.user.reset_password', { method: 'POST', headers: hf, credentials: 'same-origin', body: JSON.stringify({ user: em }) });
      busy(0);
      if (rr.ok) { ie.style.color = '#0B7C93'; return fail('Đã gửi thư đặt lại mật khẩu tới ' + em + '. Mở thư rồi đặt mật khẩu mới, nhớ xem cả mục thư rác.'); }
      if (rr.status === 404 || rr.status === 417) return fail('Không có tài khoản nào dùng email này.');
      fail('Chưa gửi được thư (mã ' + rr.status + '), báo quản trị viên giúp.');
    } catch (e) { busy(0); fail('Lỗi kết nối, kiểm tra mạng rồi thử lại.'); }
  };
  document.getElementById('lgGo').onclick = doLogin;
  ip.onkeydown = function (e) { if (e.key === 'Enter') doLogin(); };
  iu.onkeydown = function (e) { if (e.key === 'Enter') ip.focus(); };
}

async function scrAccount() {
  var rl = (S.roles || []).slice().sort().join(', ');
  frame('Tài khoản', '<div class="card">' +
    '<div class="kv"><span>Họ tên</span><b>' + h(S.me.full_name || '-') + '</b></div>' +
    '<div class="kv"><span>Tài khoản</span><b>' + h(S.user || '-') + '</b></div>' +
    '<div class="kv"><span>Bộ phận</span><b>' + h(shortDep(S.me.bo_phan) || 'Chưa gắn') + '</b></div>' +
    '</div>' +
    '<div class="sec">Vai trò được cấp</div><div class="card">' +
    '<div style="padding:13px 14px;font-size:13.5px;color:#5a6070;line-height:1.6">' + h(rl || 'Chưa gắn vai trò nào') + '</div></div>' +
    '<div style="text-align:center;color:#a0a6b4;font-size:12px;padding:10px 10px 4px;line-height:1.6">' + h(APPNAME) + '</div>',
    { footer: '<button class="btn gh" id="acOut">Đăng xuất</button>' });
  var o = document.getElementById('acOut');
  if (o) o.onclick = async function () {
    if (!await confirmSheet('Đăng xuất khỏi app?', 'Bạn sẽ phải nhập lại tài khoản và mật khẩu.', 'Đăng xuất')) return;
    busy(1);
    var hdo = { 'Accept': 'application/json' };
    try { if (window.frappe && frappe.csrf_token) hdo['X-Frappe-CSRF-Token'] = frappe.csrf_token; } catch (e) { }
    try { await fetch('/api/method/logout', { method: 'POST', headers: hdo, credentials: 'same-origin' }); } catch (e) { }
    try { localStorage.removeItem('vgb_bp_' + S.user); } catch (e) { }
    clearFresh(); hardNav();
  };
}

/* ---------- 14. Kiem ke (stocktake) ---------- */
var KKSCOPE = [
  { value: 'Nguyên vật liệu', icon: '🥚', sub: 'Bột, sữa, trứng, trái cây, chocolate...', roots: ['Nguyên vật liệu Thô', 'Nguyên vật liệu Sonneto'] },
  { value: 'Bán thành phẩm', icon: '🧁', sub: 'Cốt bánh, nhân, kem, sốt đã làm sẵn', roots: ['Bán thành phẩm Bánh', 'Bán thành phẩm Nước', 'Nhân bán thành phẩm'] },
  { value: 'Thành phẩm', icon: '🎂', sub: 'Bánh và nước đã hoàn thiện, chờ bán', roots: ['Thành phẩm Bánh', 'Thành phẩm Nước'] },
  { value: 'Công cụ - Bao bì', icon: '📦', sub: 'Hộp, túi, khuôn, dụng cụ, văn phòng phẩm', roots: ['Công cụ Dụng cụ', 'Công cụ dụng cụ Sonneto', 'Bao bì', 'Văn phòng phẩm'] },
  { value: 'Tất cả', icon: '🗂️', sub: 'Toàn bộ hàng hoá có quản lý tồn kho', roots: null }
];
var KKST = {
  'Đang kiểm': { c: 'w', t: 'Đang kiểm' },
  'Chờ duyệt': { c: 'b', t: 'Chờ duyệt' },
  'Đã chốt': { c: 'b', t: 'Đã chốt' },
  'Đã ghi sổ': { c: 'g', t: 'Đã ghi sổ' },
  'Đã huỷ': { c: 'n', t: 'Đã huỷ' }
};
function kkScope(v) { for (var i = 0; i < KKSCOPE.length; i++) if (KKSCOPE[i].value === v) return KKSCOPE[i]; return KKSCOPE[0]; }
function kkAllUnder(roots) {
  var out = [];
  function walk(nm) { if (out.indexOf(nm) < 0) out.push(nm); (S.gtree[nm] || []).forEach(walk); }
  (roots || []).forEach(walk);
  return out;
}
function kkGroups(v) { var s = kkScope(v); return s.roots ? kkAllUnder(s.roots) : null; }
function kkCanPost() { return hasRole('Stock Manager') || hasRole('System Manager') || shortDep(S.me.bo_phan) === 'Giám đốc'; }
/* Kho khoa so: chi nhung nguoi trong danh sach (hoac nguoi ghi so duoc) moi sua duoc so kiem ke.
   Nguoi khac van mo phieu xem binh thuong de tham chieu ton kho luc dat hang. */
var KKWLOCK = { 'Kho tổng 307 - TV': ['kiendoforwork@gmail.com'] };
function kkWhOwner(wh) { return KKWLOCK[wh] || null; }
function kkCanEditWh(wh) {
  var l = kkWhOwner(wh);
  if (!l) return true;
  return l.indexOf(S.user) >= 0 || kkCanPost();
}
function kkLockNote(wh) {
  return 'Kho ' + h(shortWh(wh)) + ' do bộ phận Kho tổng 307 chốt số. Bạn mở được để xem và tham chiếu tồn, nhưng không sửa số trong phiếu kho này.';
}
function kkNum(v) { var n = parseFloat(v); return isNaN(n) ? 0 : r3(n); }

var kk = { doc: null, rows: [], cat: null, catKey: '', sys: {}, conv: {}, convLoaded: 0, tab: 'da', q: '', dirty: 0, savedAt: '', saving: 0, tmr: null, newf: null };

/* ---------- 14-0. Quy doi don vi tinh khi dem ----------
   Ton kho luon ghi so bang don vi goc (gram / ml / cai). Nhung luc dem thi
   nguoi kiem can dem theo quy cach: 3 bich nguyen + 800 gram cua bich mo do.
   Nen 1 mon co the co nhieu dong dem bang nhieu don vi, cong lai ra don vi goc. */

/* Kg / Lit la don vi chung, khong phai quy cach dong goi cua rieng mon nao */
var KKGEN = { 'Kg': 1, 'KG': 1, 'Kilogram': 1, 'Tấn': 1, 'Lít': 1, 'Lit': 1, 'Litre': 1, 'Liter': 1, 'Gram': 1, 'ML': 1, 'Ml': 1, 'ml': 1 };

async function kkLoadConv() {
  if (kk.convLoaded) return kk.conv;
  var m = {};
  try {
    var rs = await getList('UOM Conversion Detail', {
      parent: 'Item', parenttype: 'Item',
      fields: ['parent', 'uom', 'conversion_factor'],
      filters: { parenttype: 'Item' }, limit_page_length: 0
    });
    rs.forEach(function (x) {
      var f = parseFloat(x.conversion_factor);
      if (!x.parent || !x.uom || !f || f <= 0) return;
      (m[x.parent] = m[x.parent] || []).push({ uom: x.uom, f: f });
    });
    kk.convLoaded = 1;
  } catch (e) { }
  kk.conv = m;
  return m;
}

/* danh sach o nhap cho 1 mon: quy cach lon -> nho, cuoi cung luon la don vi goc */
function kkUnits(r) {
  var out = (kk.conv[r.item_code] || []).filter(function (u) {
    return u.uom !== r.dvt && Math.abs(u.f - 1) > 1e-9;
  }).slice().sort(function (a, b) { return b.f - a.f; });
  out.push({ uom: r.dvt || 'Đơn vị', f: 1 });
  return out;
}
/* don vi dong goi thuc su (bo qua Kg/Lit chung chung) - dung cho quet lien tuc */
function kkPack(r) {
  var c = (kk.conv[r.item_code] || []).filter(function (u) {
    return u.f > 0 && Math.abs(u.f - 1) > 1e-9 && !KKGEN[u.uom] && u.uom !== r.dvt;
  }).slice().sort(function (a, b) { return a.f - b.f; });
  return c[0] || null;
}
/* ma hoa cach dem: "Bịch|3|2500;Gram|800|1" */
function kkPartsEnc(ps) {
  return ps.filter(function (p) { return kkNum(p.qty) > 0; })
    .map(function (p) { return p.uom + '|' + r3(kkNum(p.qty)) + '|' + (parseFloat(p.f) || 1); }).join(';');
}
function kkPartsDec(s) {
  return String(s || '').split(';').filter(Boolean).map(function (x) {
    var a = x.split('|');
    return { uom: a[0], qty: kkNum(a[1]), f: parseFloat(a[2]) || 1 };
  });
}
function kkPartsSum(ps) {
  var t = 0;
  ps.forEach(function (p) { t += kkNum(p.qty) * (parseFloat(p.f) || 1); });
  return r3(t);
}
function kkPartsText(s) {
  var ps = kkPartsDec(s).filter(function (p) { return kkNum(p.qty) > 0; });
  if (!ps.length) return '';
  return ps.map(function (p) { return num(p.qty) + ' ' + p.uom; }).join(' + ');
}

/* ---- o nhap so luong: 1 o cho moi don vi, tu cong ra don vi goc ---- */
function kkCountSheet(title, label, r, initEnc) {
  var units = kkUnits(r);
  var base = r.dvt || 'Đơn vị';
  var init = {};
  kkPartsDec(initEnc).forEach(function (p) { init[p.uom] = p.qty; });
  if (!Object.keys(init).length && kkNum(r.so_luong) > 0 && r.da_dem) init[base] = kkNum(r.so_luong);
  var multi = units.length > 1;

  return new Promise(function (res) {
    var ov = document.createElement('div'); ov.className = 'sh';
    var rows = units.map(function (u, k) {
      return '<div class="kku">' +
        '<div class="qr"><div class="stp">' +
        '<button data-m="' + k + '">&minus;</button>' +
        '<input type="number" inputmode="decimal" step="any" data-u="' + k + '" value="' +
        (init[u.uom] == null ? '' : init[u.uom]) + '" placeholder="0">' +
        '<button data-p="' + k + '">+</button></div>' +
        '<div class="uml">' + h(u.uom) + '</div></div>' +
        (Math.abs(u.f - 1) > 1e-9 ? '<div class="kkuf">1 ' + h(u.uom) + ' = ' + num(u.f) + ' ' + h(base) + '</div>' : '') +
        '</div>';
    }).join('');

    ov.innerHTML = '<div class="shb" style="padding:18px 16px calc(env(safe-area-inset-bottom,0px) + 16px);max-height:88vh;overflow:auto">' +
      '<div style="font-size:17.5px;font-weight:700;margin-bottom:4px;line-height:1.3">' + h(title) + '</div>' +
      '<div style="font-size:12.5px;color:#8a8f9c;margin-bottom:12px">' + h(label || '') + '</div>' +
      (multi ? '<div class="kkuh">Nguyên đai nguyên kiện đếm theo quy cách, hàng đã mở dở thì cân rồi nhập ở dòng ' + h(base) + '. Hệ thống tự cộng lại.</div>' : '') +
      rows +
      (multi ? '<div class="kkut">Tổng: <b id="kkuts">0</b> ' + h(base) + '</div>' : '') +
      '<button class="btn" data-y style="margin-top:14px">Xác nhận</button>' +
      '<button class="btn gh" data-n style="margin-top:9px">Huỷ</button></div>';
    document.body.appendChild(ov);

    var ins = [].slice.call(ov.querySelectorAll('[data-u]'));
    function parts() {
      return units.map(function (u, k) { return { uom: u.uom, qty: kkNum(ins[k].value), f: u.f }; });
    }
    function sync() {
      var t = ov.querySelector('#kkuts');
      if (t) t.textContent = num(kkPartsSum(parts()));
    }
    ov.addEventListener('input', sync);
    ov.onclick = function (e) {
      var t = e.target;
      var m = t.closest && t.closest('[data-m]'); if (m) { var a = ins[+m.dataset.m]; a.value = Math.max(0, r3((parseFloat(a.value) || 0) - 1)); return sync(); }
      var p = t.closest && t.closest('[data-p]'); if (p) { var b = ins[+p.dataset.p]; b.value = r3((parseFloat(b.value) || 0) + 1); return sync(); }
      if (t === ov || (t.closest && t.closest('[data-n]'))) { ov.remove(); return res(null); }
      if (t.closest && t.closest('[data-y]')) {
        var ps = parts();
        var any = ins.some(function (x) { return String(x.value).trim() !== ''; });
        ov.remove();
        return res(any ? { qty: kkPartsSum(ps), enc: kkPartsEnc(ps) } : null);
      }
    };
    sync();
    setTimeout(function () { try { ins[0].focus(); ins[0].select(); } catch (e) { } }, 150);
  });
}

function kkPackHtml(r, i, live) {
  var us = kkUnits(r);
  if (us.length < 2) return '';
  var txt = kkPartsText(r.cach_dem);
  if (!txt && !live) return '';
  return '<div class="tw"><div class="lb kkpk"' + (live ? ' data-pack="' + i + '"' : '') + '>' +
    (txt ? '&#9878; Đếm theo quy cách: <b>' + h(txt) + '</b> = ' + num(kkNum(r.so_luong)) + ' ' + h(r.dvt)
      : '&#9878; Đếm theo quy cách (' + h(us.filter(function (u) { return Math.abs(u.f - 1) > 1e-9; }).map(function (u) { return u.uom; }).join(', ')) + ')') +
    '</div></div>';
}

/* mo bang dem theo quy cach cho 1 dong da co tren phieu */
async function kkPackAsk(i) {
  if (!kkLive()) return;
  var r = kk.rows[i];
  var v = await kkCountSheet(r.item_name,
    r.item_code + (kkNum(r.ton_he_thong) ? ' · máy đang có ' + num(r.ton_he_thong) + ' ' + r.dvt : ' · máy chưa có tồn'),
    r, r.cach_dem);
  if (v === null) return;
  r.so_luong = v.qty; r.cach_dem = v.enc; r.da_dem = 1;
  var inp = document.querySelector('[data-q="' + i + '"]');
  if (inp) inp.value = r.so_luong;
  kkRowSync(i); kkTouch();
}


/* ---------- 14a. Danh sach phieu kiem ke ---------- */
async function scrKkList() {
  frame('Kiểm kê', '<div class="emp"><div class="e1">⏳</div></div>');
  await loadMasters();
  var docs = [];
  try {
    docs = await getList('Phieu Kiem Ke', {
      fields: ['name', 'ngay_kiem', 'kho', 'pham_vi', 'trang_thai', 'so_mon', 'nguoi_kiem', 'owner', 'modified'],
      filters: {}, limit_page_length: 80, order_by: 'modified desc'
    });
  } catch (e) { toast(errMsg(e)); }

  var dang = docs.filter(function (d) { return d.trang_thai === 'Đang kiểm'; });
  var xong = docs.filter(function (d) { return d.trang_thai !== 'Đang kiểm' && d.trang_thai !== 'Đã huỷ'; });
  var huy = docs.filter(function (d) { return d.trang_thai === 'Đã huỷ'; });

  function row(d) {
    var s = KKST[d.trang_thai] || KKST['Đang kiểm'];
    return '<div class="li" data-p="' + h(d.name) + '"><div class="lt">' +
      '<div class="l1">' + h(shortWh(d.kho)) + ' · ' + h(d.pham_vi || '') + '</div>' +
      '<div class="l2">' + h(d.name) + ' · ' + h(dmy(d.ngay_kiem)) + ' · ' + (d.so_mon || 0) + ' món' +
      (d.nguoi_kiem ? ' · ' + h(d.nguoi_kiem) : '') + '</div></div>' +
      '<span class="st ' + s.c + '">' + h(s.t) + '</span></div>';
  }

  var body = '<div class="rcvh">Mỗi phiếu kiểm kê là <b>một kho, một nhóm hàng</b>. Quét mã vạch rồi nhập số đếm được, phiếu tự lưu lại nên có thể kiểm nhiều buổi. Đếm xong mới bấm <b>Chốt phiếu</b>.</div>';
  if (dang.length) body += '<div class="sec">Đang kiểm dở</div><div class="lst">' + dang.map(row).join('') + '</div>';
  if (xong.length) body += '<div class="sec">Đã chốt</div><div class="lst">' + xong.map(row).join('') + '</div>';
  if (huy.length) body += '<div class="sec">Đã huỷ</div><div class="lst">' + huy.map(row).join('') + '</div>';
  if (!docs.length) body += '<div class="emp"><div class="e1">📋</div><div class="e2">Chưa có phiếu kiểm kê nào.<br>Bấm dấu + để bắt đầu kiểm kho.</div></div>';

  var b = frame('Kiểm kê', body, { fab: true, onFab: function () { go(scrKkNew); } });
  b.onclick = function (e) {
    var r = e.target.closest('[data-p]'); if (!r) return;
    go(function () { scrKkDoc(r.dataset.p); });
  };
}

/* ---------- 14b. Tao phieu kiem ke moi ---------- */
async function scrKkNew() {
  await loadMasters();
  if (!kk.newf) {
    kk.newf = {
      ngay: today(),
      kho: (S.wh.filter(function (w) { return shortWh(w).indexOf('Kho tổng') === 0; })[0] || S.wh[0] || ''),
      pv: 'Nguyên vật liệu',
      vt: ''
    };
  }
  var f = kk.newf;
  if (!kk.vtAll) {
    try { kk.vtAll = await getList('Vi Tri Kho', { fields: ['name', 'kho', 'loai', 'thu_tu'], filters: { active: 1 }, limit_page_length: 0, order_by: 'thu_tu asc, name asc' }); }
    catch (e) { kk.vtAll = []; }
  }
  function vtOpts() {
    var l = (kk.vtAll || []).filter(function (v) { return v.kho === f.kho; });
    return [{ value: '', label: 'Cả kho (không chia tủ)' }].concat(l.map(function (v) {
      return { value: v.name, label: v.name + (v.loai ? ' · ' + v.loai : '') };
    }));
  }
  function draw() {
    var vtl = (kk.vtAll || []).filter(function (v) { return v.kho === f.kho; });
    if (f.vt && vtl.map(function (v) { return v.name; }).indexOf(f.vt) < 0) f.vt = '';
    var sc = kkScope(f.pv);
    var body = '<div class="rcvh">Chọn đúng <b>kho</b> và <b>nhóm hàng</b> sẽ kiểm. Bếp thứ 6 chỉ kịp nguyên vật liệu thì cứ chọn Nguyên vật liệu, bán thành phẩm để phiếu riêng kiểm sau cũng được.</div>' +
      '<div class="card">' +
      '<div class="fld" data-d><div class="fi">📅</div><div class="ft"><div class="fl">Ngày kiểm</div><div class="fv">' + h(dmy(f.ngay)) + '</div></div><div class="fc">&#8250;</div></div>' +
      '<div class="fld" data-w><div class="fi">🏬</div><div class="ft"><div class="fl">Kho kiểm</div><div class="fv' + (f.kho ? '' : ' ph') + '">' + h(shortWh(f.kho) || 'Chọn kho') + '</div></div><div class="fc">&#8250;</div></div>' +
      '<div class="fld" data-s><div class="fi">' + sc.icon + '</div><div class="ft"><div class="fl">Nhóm hàng kiểm</div><div class="fv">' + h(f.pv) + '</div></div><div class="fc">&#8250;</div></div>' +
      (vtl.length ? '<div class="fld" data-v><div class="fi">📍</div><div class="ft"><div class="fl">Vị trí kiểm</div><div class="fv' + (f.vt ? '' : ' ph') + '">' + h(f.vt || 'Cả kho (không chia tủ)') + '</div></div><div class="fc">&#8250;</div></div>' : '') +
      '</div>' +
      '<div class="kwn">' + h(sc.sub) + '</div>' +
      (kkCanEditWh(f.kho) ? '' : '<div class="kkq" style="margin-top:10px">🔒 ' + kkLockNote(f.kho) + '</div>');
    var b = frame('Phiếu kiểm kê mới', body, {
      footer: kkCanEditWh(f.kho)
        ? '<button class="btn" id="kknew">Bắt đầu kiểm</button>'
        : '<div class="kkq">Chọn kho khác để bắt đầu kiểm.</div>'
    });
    b.onclick = function (e) {
      if (e.target.closest('[data-w]')) return sheet('Chọn kho kiểm', whOpts(), f.kho, function (o) { f.kho = o.value; f.vt = ''; draw(); }, true);
      if (e.target.closest('[data-v]')) return sheet('Vị trí kiểm', vtOpts(), f.vt, function (o) { f.vt = o.value; draw(); }, true);
      if (e.target.closest('[data-s]')) return sheet('Nhóm hàng kiểm', KKSCOPE.map(function (x) { return { value: x.value, label: x.value, icon: x.icon }; }), f.pv, function (o) { f.pv = o.value; draw(); });
      if (e.target.closest('[data-d]')) {
        return pickDate(f.ngay, function (v) { f.ngay = v; draw(); });
      }
    };
    var bn = document.getElementById('kknew'); if (bn) bn.onclick = kkCreate;
  }
  draw();
}

async function kkCreate() {
  var f = kk.newf;
  if (!f.kho) return toast('Chọn kho trước đã');
  if (!kkCanEditWh(f.kho)) return toast('Kho ' + shortWh(f.kho) + ' chỉ bộ phận Kho tổng 307 kiểm số');
  busy(1);
  try {
    var dup = await getList('Phieu Kiem Ke', {
      fields: ['name', 'nguoi_kiem', 'so_mon'],
      filters: { kho: f.kho, pham_vi: f.pv, vi_tri: f.vt || '', trang_thai: 'Đang kiểm' },
      limit_page_length: 1
    });
    busy(0);
    if (dup && dup.length) {
      var ok = await confirmSheet('Kho này đang có phiếu kiểm dở',
        'Phiếu ' + dup[0].name + ' (' + (dup[0].nguoi_kiem || 'chưa rõ người kiểm') + ', ' + (dup[0].so_mon || 0) + ' món) vẫn đang kiểm cùng kho, cùng nhóm hàng.\n\nNên kiểm tiếp phiếu đó thay vì tạo phiếu mới, tránh đếm trùng.',
        'Mở phiếu đang kiểm');
      if (ok) return go(function () { scrKkDoc(dup[0].name); }, true);
    }
    busy(1);
    var d = await api('frappe.client.insert', {
      doc: {
        doctype: 'Phieu Kiem Ke',
        ngay_kiem: f.ngay, kho: f.kho, pham_vi: f.pv, vi_tri: f.vt || '',
        trang_thai: 'Đang kiểm',
        nguoi_kiem: S.me.full_name || S.user,
        so_mon: 0, items: []
      }
    });
    busy(0);
    if (!d || !d.name) return toast('Không tạo được phiếu, thử lại giúp');
    toast('Đã tạo phiếu ' + d.name);
    go(function () { scrKkDoc(d.name); }, true);
  } catch (e) { busy(0); toast(errMsg(e)); }
}

/* ---------- 14c. Man hinh dem ---------- */
async function kkLoadCat(pv, vt) {
  var key = pv + '|' + (vt || '');
  if (kk.cat && kk.catKey === key) return kk.cat;
  var gs = kkGroups(pv);
  var flt = { is_stock_item: 1, disabled: 0 };
  if (gs && gs.length) flt.item_group = ['in', gs];
  if (vt) flt.custom_vi_tri_luu = vt;
  var its = await getList('Item', {
    fields: ['name', 'item_name', 'item_group', 'stock_uom', 'has_batch_no', 'custom_vi_tri_luu'],
    filters: flt, limit_page_length: 0, order_by: 'item_name'
  });
  kk.cat = its; kk.catKey = key;
  return its;
}

/* DEM MU (anh Viet duyet 03/09/2026, SAP goi la blind count).

   Nguoi di dem khong duoc thay may dang ghi bao nhieu, chi go so dem duoc.
   Thay so truoc la sinh ra thoi quen "dem cho khop", va con so kiem ke mat
   het y nghia.

   Che o MAY CHU chu khong chi giau tren man: cua `mo_phieu` khong tra cot
   ton so khi phieu dang dem va nguoi mo khong phai quan ly. Man hinh cung
   khong nap bang Bin nua trong luc do - nap la tu tay dua lai dung cai vua
   duoc giau. */
async function scrKkDoc(name) {
  frame('Kiểm kê', '<div class="emp"><div class="e1">⏳</div></div>');
  await loadMasters();
  var doc = null;
  try { doc = await api('vagabond.kiem_ke.mo_phieu', { name: name }); }
  catch (e) { toast(errMsg(e)); return back(); }
  kk.doc = doc; kk.q = ''; kk.tab = 'da'; kk.dirty = 0; kk.savedAt = '';
  kk.mu = doc.dem_mu ? 1 : 0;
  kk.lyDo = doc.ly_do_lech || [];
  kk.rows = (doc.items || []).map(function (r) {
    return {
      item_code: r.item_code, item_name: r.item_name || r.item_code, item_group: r.item_group || '',
      dvt: r.dvt || '', ton_he_thong: kkNum(r.ton_he_thong), so_luong: kkNum(r.so_luong),
      cach_dem: r.cach_dem || '',
      han_su_dung: r.han_su_dung || '', ghi_chu: r.ghi_chu || '', da_dem: r.da_dem ? 1 : 0,
      ly_do_lech: r.ly_do_lech || '',
      name: r.name, docstatus: 0
    };
  });
  try { await kkLoadCat(doc.pham_vi, doc.vi_tri); } catch (e) { kk.cat = kk.cat || []; }
  try { await kkLoadConv(); } catch (e) { kk.conv = kk.conv || {}; }
  kk.sys = {};
  if (!kk.mu) {
    try {
      var bins = await getList('Bin', { fields: ['item_code', 'actual_qty'], filters: { warehouse: doc.kho, actual_qty: ['!=', 0] }, limit_page_length: 0 });
      bins.forEach(function (b) { kk.sys[b.item_code] = b.actual_qty; });
    } catch (e) { kk.sys = {}; }
  }
  kkDraw();
}

function kkCatMap() {
  var m = {};
  (kk.cat || []).forEach(function (i) { m[i.name] = i; });
  return m;
}
function kkIdx(code) {
  for (var i = 0; i < kk.rows.length; i++) if (kk.rows[i].item_code === code) return i;
  return -1;
}
function kkLive() { return (kk.doc || {}).trang_thai === 'Đang kiểm' && kkCanEditWh((kk.doc || {}).kho); }

/* them 1 mon vao phieu, tra ve chi so dong */
function kkAdd(code) {
  var i = kkIdx(code);
  if (i >= 0) return i;
  var m = kkCatMap(), it = m[code];
  kk.rows.push({
    item_code: code,
    item_name: (it && it.item_name) || code,
    item_group: (it && it.item_group) || '',
    dvt: (it && it.stock_uom) || '',
    ton_he_thong: kkNum(kk.sys[code]),
    so_luong: 0, cach_dem: '', han_su_dung: '', ghi_chu: '', da_dem: 0, name: ''
  });
  return kk.rows.length - 1;
}

function kkDraw(keepScroll) {
  var d = kk.doc, live = kkLive();
  var sc = kkScope(d.pham_vi);
  var cat = kk.cat || [];
  var done = kk.rows.filter(function (r) { return r.da_dem; });
  var inSheet = {}; kk.rows.forEach(function (r) { inSheet[r.item_code] = 1; });
  var missing = cat.filter(function (i) { return !inSheet[i.name]; });
  var q = (kk.q || '').toLowerCase().trim();
  var st = KKST[d.trang_thai] || KKST['Đang kiểm'];

  var head = '<div class="card">' +
    '<div class="stk" style="border-top:0">' +
    '<div><div class="s1">KHO</div><div class="s2">' + h(shortWh(d.kho)) + '</div></div>' +
    '<div><div class="s1">NHÓM HÀNG</div><div class="s2">' + h(d.pham_vi) + '</div></div>' +
    '<div><div class="s1">NGÀY</div><div class="s2">' + h(dmy(d.ngay_kiem)) + '</div></div>' +
    '</div>' +
    '<div class="kpg"><div class="kpt" id="kkpt">' + kkProgText() + '</div>' +
    '<div class="kpb"><i id="kkpb" style="width:' + kkProgPct() + '%"></i></div></div>' +
    '<div class="kv" style="border-top:1px solid #f0f2f6"><span>Trạng thái</span><b><span class="st ' + st.c + '">' + h(st.t) + '</span></b></div>' +
    (d.vi_tri ? '<div class="kv"><span>Vị trí</span><b>📍 ' + h(d.vi_tri) + '</b></div>' : '') +
    '<div class="kv"><span>Người kiểm</span><b>' + h(d.nguoi_kiem || '') + '</b></div>' +
    '<div class="kv"><span>Số phiếu</span><b>' + h(d.name) + '</b></div>' +
    '</div>';

  var bar = live ? '<button class="kkbig" id="kkscan">📷 &nbsp;Quét mã vạch liên tục</button>' : '';

  var tabs = '<div class="chips">' +
    '<div class="chip' + (kk.tab === 'da' ? ' on' : '') + '" data-t="da">Đã đếm (' + kk.rows.length + ')</div>' +
    '<div class="chip' + (kk.tab === 'chua' ? ' on' : '') + '" data-t="chua">Chưa đếm (' + missing.length + ')</div>' +
    (kk.rows.filter(kkHasLech).length ? '<div class="chip' + (kk.tab === 'lech' ? ' on' : '') + '" data-t="lech">Lệch tồn (' + kk.rows.filter(kkHasLech).length + ')</div>' : '') +
    '</div>';

  var srch = srchBox('kkq', kk.tab === 'chua' ? 'Tìm theo tên hoặc mã để thêm' : 'Tìm theo tên hoặc mã hàng', kk.q, live);

  var listHtml = '';
  if (kk.tab === 'chua') {
    var ms = missing.filter(function (i) { return !q || (i.item_name + ' ' + i.name).toLowerCase().indexOf(q) >= 0; });
    listHtml = ms.length
      ? '<div class="lst">' + ms.slice(0, 300).map(function (i) {
        return '<div class="li" data-add="' + h(i.name) + '"><div class="lt">' +
          '<div class="l1">' + h(i.item_name) + '</div>' +
          '<div class="l2">' + h(i.name) + ' · ' + h(i.item_group) + '</div></div>' +
          '<div class="ck" style="border-radius:50%;font-size:20px;color:#0B7C93;border-color:#7FE5F6">+</div></div>';
      }).join('') + '</div>' + (ms.length > 300 ? '<div class="kkq">Còn ' + (ms.length - 300) + ' món nữa, gõ tên vào ô tìm để lọc bớt.</div>' : '')
      : '<div class="emp"><div class="e1">✅</div><div class="e2">' + (missing.length ? 'Không tìm thấy món nào' : 'Đã đếm hết ' + cat.length + ' món trong nhóm này') + '</div></div>';
  } else {
    var rs = kk.rows.map(function (r, i) { return { r: r, i: i }; });
    if (kk.tab === 'lech') rs = rs.filter(function (x) { return kkHasLech(x.r); });
    if (q) rs = rs.filter(function (x) { return (x.r.item_name + ' ' + x.r.item_code).toLowerCase().indexOf(q) >= 0; });
    listHtml = rs.length ? rs.map(function (x) { return kkRowHtml(x.r, x.i, live); }).join('') : '';
    if (q && live) {
      var mq = missing.filter(function (i) { return (i.item_name + ' ' + i.name).toLowerCase().indexOf(q) >= 0; });
      if (mq.length) {
        listHtml += '<div class="kkq" style="padding-top:10px">' +
          (rs.length ? 'Món khớp nhưng <b>chưa có trong phiếu</b>, bấm + để thêm và đếm:'
                     : 'Chưa có món nào khớp trong phiếu. <b>' + mq.length + ' món chưa đếm</b> khớp với từ khoá, bấm + để thêm:') +
          '</div><div class="lst">' + mq.slice(0, 60).map(function (i) {
            return '<div class="li" data-add="' + h(i.name) + '"><div class="lt">' +
              '<div class="l1">' + h(i.item_name) + '</div>' +
              '<div class="l2">' + h(i.name) + ' · ' + h(i.item_group) + '</div></div>' +
              '<div class="ck" style="border-radius:50%;font-size:20px;color:#0B7C93;border-color:#7FE5F6">+</div></div>';
          }).join('') + '</div>' +
          (mq.length > 60 ? '<div class="kkq">Còn ' + (mq.length - 60) + ' món nữa khớp, gõ thêm chữ cho gọn.</div>' : '');
      }
    }
    if (!listHtml) listHtml = '<div class="emp"><div class="e1">🔍</div><div class="e2">' +
      (q ? 'Không tìm thấy món nào tên hoặc mã có <b>' + h(kk.q) + '</b>'
         : (kk.rows.length ? 'Không tìm thấy món nào' : 'Phiếu còn trống.<br>Gõ tên món vào ô tìm ở trên, hoặc bấm <b>Quét mã vạch liên tục</b>.')) + '</div></div>';
  }

  var foot = '';
  if (live) {
    foot = '<div class="kkq" id="kksv">' + (kk.savedAt ? 'Đã lưu lúc ' + kk.savedAt : (kk.rows.length ? 'Có thay đổi chưa lưu' : 'Phiếu mới, chưa có món nào')) + '</div>' +
      '<div class="row2"><button class="btn gh" id="kksave">Lưu lại</button>' +
      '<button class="btn gr" id="kkdone">Chốt phiếu</button></div>' +
      '<button class="kkcx" id="kkcancel">Huỷ phiếu kiểm kê này</button>';
  } else if (d.trang_thai === 'Đang kiểm') {
    foot = '<div class="kkq">🔒 ' + kkLockNote(d.kho) + '</div>';
  } else if (d.trang_thai === 'Chờ duyệt' || d.trang_thai === 'Đã chốt') {
    foot = (kkCanPost() ? '<button class="btn" id="kkpost">Ghi sổ vào phần mềm</button>' : '<div class="kkq">Phiếu đã chốt, chờ kho hoặc giám đốc ghi sổ.</div>') +
      '<button class="btn gh" id="kkreopen" style="margin-top:9px">Mở lại để sửa</button>';
  } else if (d.trang_thai === 'Đã huỷ') {
    foot = '<div class="kkq">Phiếu đã huỷ, số đếm trong phiếu không được ghi vào sổ.</div>' +
      '<button class="btn gh" id="kkreopen">Mở lại để kiểm tiếp</button>';
  } else if (d.trang_thai === 'Đã ghi sổ') {
    foot = '<div class="kkq">Đã ghi sổ' + (d.stock_reconciliation ? ' bằng phiếu ' + h(d.stock_reconciliation) : '') + '. Phiếu này chỉ còn để tra cứu.</div>';
  }

  var b = frame('Kiểm kê ' + shortWh(d.kho), head + bar + tabs + srch + '<div id="kkl">' + listHtml + '</div>',
    { footer: foot, action: live ? '&#128247;' : '' , onAction: live ? kkScanTick : null });

  var sv = document.getElementById('kkq');
  if (sv) {
    var tm = null;
    sv.oninput = function () {
      kk.q = sv.value; clearTimeout(tm);
      tm = setTimeout(function () { var v = kk.q, p = sv.selectionStart; kkDraw(); var i2 = document.getElementById('kkq'); if (i2) { i2.focus(); i2.value = v; try { i2.setSelectionRange(p, p); } catch (e) { } } }, 220);
    };
  }
  var sb = document.getElementById('kkqscan');
  if (sb) sb.onclick = kkScanOne;
  var bs = document.getElementById('kkscan');
  if (bs) bs.onclick = kkScanTick;
  var s1 = document.getElementById('kksave'); if (s1) s1.onclick = function () { kkSave(1); };
  var s2 = document.getElementById('kkdone'); if (s2) s2.onclick = kkFinish;
  var s3 = document.getElementById('kkpost'); if (s3) s3.onclick = function () { go(function () { scrKkPost(kk.doc.name); }); };
  var s4 = document.getElementById('kkreopen'); if (s4) s4.onclick = kkReopen;
  var s5 = document.getElementById('kkcancel'); if (s5) s5.onclick = kkCancel;

  b.onclick = function (e) {
    var t = e.target.closest('[data-t]');
    if (t) { kk.tab = t.dataset.t; return kkDraw(); }
    var ad = e.target.closest('[data-add]');
    if (ad) return kkAddAsk(ad.dataset.add);
    var dl = e.target.closest('[data-x]');
    if (dl) return kkDel(+dl.dataset.x);
    var mi = e.target.closest('[data-m]');
    if (mi) return kkStep(+mi.dataset.m, -1);
    var pl = e.target.closest('[data-a]');
    if (pl) return kkStep(+pl.dataset.a, 1);
    var tm = e.target.closest('[data-tem]');
    if (tm) return kkTem(+tm.dataset.tem);
    var nb = e.target.closest('[data-note]');
    if (nb) return kkNote(+nb.dataset.note);
    var pk = e.target.closest('[data-pack]');
    if (pk) return kkPackAsk(+pk.dataset.pack);
  };
  b.addEventListener('change', function (e) {
    var qi = e.target.closest('[data-q]');
    if (qi) { var i = +qi.dataset.q; kk.rows[i].so_luong = kkNum(qi.value); kk.rows[i].cach_dem = ''; kk.rows[i].da_dem = 1; kkTouch(); kkRowSync(i); return; }
    var hi = e.target.closest('[data-h]');
    if (hi) { kk.rows[+hi.dataset.h].han_su_dung = hi.value || ''; kkTouch(); }
  });
  b.addEventListener('input', function (e) {
    var qi = e.target.closest('[data-q]');
    if (qi) { var i = +qi.dataset.q; kk.rows[i].so_luong = kkNum(qi.value); kk.rows[i].cach_dem = ''; kk.rows[i].da_dem = 1; kkTouch(); kkRowSync(i); }
  });
}

function kkHasLech(r) { return !kk.mu && r.da_dem && Math.abs(kkNum(r.so_luong) - kkNum(r.ton_he_thong)) > 0.0001; }
function kkProgText() {
  var cat = (kk.cat || []).length, done = kk.rows.filter(function (r) { return r.da_dem; }).length;
  return 'ĐÃ ĐẾM ' + done + '/' + cat + ' MÓN TRONG NHÓM';
}
function kkProgPct() {
  var cat = (kk.cat || []).length, done = kk.rows.filter(function (r) { return r.da_dem; }).length;
  return cat ? Math.min(100, Math.round(done * 100 / cat)) : 0;
}
function kkProgSync() {
  var p = document.getElementById('kkpt'); if (p) p.textContent = kkProgText();
  var b = document.getElementById('kkpb'); if (b) b.style.width = kkProgPct() + '%';
}

function kkLechHtml(r) {
  if (kk.mu) return '';
  if (!r.da_dem) return '';
  var s = kkNum(r.ton_he_thong), c = kkNum(r.so_luong), d = r3(c - s);
  if (!s && !c) return '';
  if (Math.abs(d) < 0.0001) return '<div class="kkl eq">Khớp với tồn trên máy (' + num(s) + ' ' + h(r.dvt) + ')</div>';
  return '<div class="kkl ' + (d > 0 ? 'up' : 'dn') + '">' + (d > 0 ? 'Thừa ' : 'Thiếu ') + num(Math.abs(d)) + ' ' + h(r.dvt) +
    ' so với máy (máy ' + num(s) + ', đếm ' + num(c) + ')</div>';
}

function kkRowHtml(r, i, live) {
  var it = kkCatMap()[r.item_code] || {};
  return '<div class="ic1' + (r.da_dem ? ' ok' : '') + '" id="kkr' + i + '">' +
    '<div class="ih"><div class="n">' + (i + 1) + '</div>' +
    '<div class="in">' + h(r.item_name) +
    '<div class="ig">' + h(r.item_code) + (r.item_group ? ' · ' + h(r.item_group) : '') +
    (kk.mu ? '' : (kkNum(r.ton_he_thong) ? ' · máy ' + num(r.ton_he_thong) + ' ' + h(r.dvt) : ' · máy chưa có tồn')) + '</div></div>' +
    (live ? '<div class="del" data-x="' + i + '">&times;</div>' : '<div class="rok">&#10003;</div>') + '</div>' +
    '<div class="qw"><div style="flex:1;min-width:0">' +
    '<div class="lb">Số lượng thực đếm' + (r.da_dem ? '' : ' <b class="lbw">(chưa nhập)</b>') + '</div>' +
    '<div class="qr"><div class="stp">' +
    (live ? '<button data-m="' + i + '">&minus;</button>' : '') +
    '<input type="number" inputmode="decimal" step="any" data-q="' + i + '" value="' + (r.da_dem ? r.so_luong : '') + '" placeholder="0"' + (live ? '' : ' readonly') + '>' +
    (live ? '<button data-a="' + i + '">+</button>' : '') +
    '</div><div class="uml">' + h(r.dvt) + '</div></div></div></div>' +
    '<div id="kkp' + i + '">' + kkPackHtml(r, i, live) + '</div>' +
    (it.has_batch_no ? '<div class="hw"><div class="hl">Hạn sử dụng lô đang tồn <b class="hbd">nếu có</b></div>' +
      '<input type="date" class="hin' + (r.han_su_dung ? ' ed' : '') + '" data-h="' + i + '" value="' + h(r.han_su_dung) + '"' + (live ? '' : ' disabled') + '>' +
      '<div class="hn">Món này quản lý theo lô. Ghi hạn trên bao bì để hệ thống lấy hàng theo FEFO cho đúng.</div>' +
      (live ? '<button class="btn gh" data-tem="' + i + '" style="height:44px;font-size:14px;margin-top:8px">&#127991; In tem dán lên hàng</button>' : '') +
      '</div>' : '') +
    '<div id="kkw' + i + '">' + kkLechHtml(r) + '</div>' +
    (live ? '<div class="tw"><div class="lb" data-note="' + i + '" style="color:#0B7C93;font-weight:600;cursor:pointer">' +
      (r.ghi_chu ? '✎ Ghi chú: ' + h(r.ghi_chu) : '✎ Thêm ghi chú (hàng hỏng, hàng gửi, đang mượn...)') + '</div></div>'
      : (r.ghi_chu ? '<div class="tw"><div class="lb">Ghi chú: ' + h(r.ghi_chu) + '</div></div>' : '')) +
    '</div>';
}

/* ---- in tem nhap kho ngay tai dong dang dem ---- */
function kkBatchId(docname, code) {
  return 'KK' + String(docname).replace(/[^0-9A-Za-z]/g, '').slice(-8) + '-' + String(code).replace(/[^0-9A-Za-z]/g, '');
}
async function kkTem(i) {
  if (!kkLive()) return;
  var r = kk.rows[i];
  var it = kkCatMap()[r.item_code] || {};
  if (!it.has_batch_no) return toast('Món này không quản lý theo lô nên chưa in tem lô được');
  if (!kk.doc || !kk.doc.name) return toast('Lưu phiếu một lần trước đã rồi in tem nhé');
  if (!r.han_su_dung) {
    var go1 = await confirmSheet('Chưa điền hạn sử dụng', r.item_name + '\n\nTem in ra sẽ không có HSD. Điền hạn vào ô ngay phía trên rồi in lại sẽ đầy đủ hơn.', 'Cứ in không HSD');
    if (!go1) return;
  }
  var nv = await promptSheet('In bao nhiêu tem cho ' + r.item_name + '?', 'Số tem, ví dụ 1');
  if (nv === null) return;
  var n = Math.max(1, parseInt(nv, 10) || 1);
  /* Cua so nay mo o day chu khong doi toi sau khi luu phieu: sau vai await
     la trinh duyet chan popup. In ngam duoc thi khong mo gi ca. */
  var w = inMoCuaSoNeuCan('tem');
  if (w === 'chan') return;
  busy(1);
  try {
    if (kk.dirty) { try { await kkSave(0); } catch (e0) { } }
    var bid = kkBatchId(kk.doc.name, r.item_code);
    var ex = await getList('Batch', { fields: ['name'], filters: { name: bid }, limit_page_length: 1 });
    if (ex && ex.length) {
      var fv = { custom_so_tem: n };
      if (r.han_su_dung) fv.expiry_date = r.han_su_dung;
      await api('frappe.client.set_value', { doctype: 'Batch', name: bid, fieldname: fv });
    } else {
      var bd = { doctype: 'Batch', batch_id: bid, item: r.item_code, custom_so_tem: n };
      if (r.han_su_dung) bd.expiry_date = r.han_su_dung;
      await api('frappe.client.insert', { doc: bd });
    }
    busy(0);
    var u = '/printview?doctype=Batch&name=' + encodeURIComponent(bid) +
      '&format=' + encodeURIComponent('Vagabond - Tem nhan hang') + '&no_letterhead=1&trigger_print=1';
    await inToTuDuongDan('tem', 'Tem nhãn hàng', u, inKho('tem').rong, w);
  } catch (e) {
    busy(0);
    if (w && w !== 'chan') { try { w.close(); } catch (e2) { } }
    toast(errMsg(e), 7000);
  }
}

function kkRowSync(i) {
  var el = document.getElementById('kkr' + i); if (!el) return;
  var r = kk.rows[i];
  if (r.da_dem) el.classList.add('ok'); else el.classList.remove('ok');
  var w = document.getElementById('kkw' + i); if (w) w.innerHTML = kkLechHtml(r);
  var p = document.getElementById('kkp' + i); if (p) p.innerHTML = kkPackHtml(r, i, kkLive());
  kkProgSync();
}

function kkStep(i, d) {
  if (!kkLive()) return;
  var r = kk.rows[i];
  r.so_luong = Math.max(0, r3(kkNum(r.so_luong) + d));
  r.cach_dem = '';
  r.da_dem = 1;
  var inp = document.querySelector('[data-q="' + i + '"]');
  if (inp) inp.value = r.so_luong;
  kkRowSync(i); kkTouch();
}

async function kkNote(i) {
  var v = await promptSheet('Ghi chú cho ' + kk.rows[i].item_name, 'Ví dụ: 2 hộp bị móp, 1 thùng đang gửi bên bếp Lab...');
  if (v === null) return;
  kk.rows[i].ghi_chu = v;
  kkTouch(); kkDraw();
}

async function kkDel(i) {
  var ok = await confirmSheet('Bỏ món này khỏi phiếu?', kk.rows[i].item_name + '\n' + kk.rows[i].item_code, 'Bỏ ra', true);
  if (!ok) return;
  kk.rows.splice(i, 1);
  kkTouch(); kkDraw();
}

async function kkAddAsk(code) {
  if (!kkLive()) return;
  var i = kkAdd(code), r = kk.rows[i];
  var v = await kkCountSheet(r.item_name, r.item_code + (kkNum(r.ton_he_thong) ? ' · máy đang có ' + num(r.ton_he_thong) + ' ' + r.dvt : ' · máy chưa có tồn'), r, r.cach_dem);
  if (v === null) { if (!r.da_dem) kk.rows.splice(i, 1); kkDraw(); return; }
  r.so_luong = v.qty; r.cach_dem = v.enc; r.da_dem = 1;
  kkTouch(); kkDraw();
}

/* quet 1 lan tu o tim kiem */
async function kkScanOne() {
  var code = await scanBarcode(null);
  if (!code) return;
  busy(1);
  var ic = null;
  try { ic = await itemByBarcode(String(code).trim().replace(/^\*+|\*+$/g, '')); } catch (e) { }
  busy(0);
  if (!ic) return toast('Chưa nhận ra mã ' + code + '. Vui lòng tìm bằng tên món.');
  if (kk.tab === 'chua' && kkIdx(ic) < 0) return kkAddAsk(ic);
  kk.q = ic; kk.tab = 'da'; kkDraw();
}

/* quet lien tuc: moi lan quet cong them 1 don vi, tien cho hang dem tung cai */
async function kkScanTick() {
  if (!kkLive()) return;
  var cat = kkCatMap();
  await scanBarcode(async function (code) {
    var raw = String(code).trim().replace(/^\*+|\*+$/g, '');
    var ic = null;
    try { ic = await itemByBarcode(raw); } catch (e) { }
    if (!ic) { try { ic = await itemByBarcode(raw.toUpperCase()); } catch (e) { } }
    if (!ic) return '✗ Chưa nhận ra mã ' + raw;
    if (!cat[ic]) {
      var extra = null;
      try { extra = (await getList('Item', { fields: ['name', 'item_name', 'item_group', 'stock_uom', 'has_batch_no'], filters: { name: ic }, limit_page_length: 1 }))[0]; } catch (e) { }
      if (!extra) return '✗ ' + ic + ' không có trong hệ thống';
      return '✗ ' + (extra.item_name || ic) + ' thuộc nhóm ' + (extra.item_group || '?') + ', không nằm trong phiếu này';
    }
    var i = kkAdd(ic), r = kk.rows[i];
    var pk = kkPack(r);
    if (pk) {
      var ps = kkPartsDec(r.cach_dem);
      if (!ps.length && kkNum(r.so_luong) > 0 && r.da_dem) ps.push({ uom: r.dvt, qty: kkNum(r.so_luong), f: 1 });
      var hit = null;
      ps.forEach(function (x) { if (x.uom === pk.uom) hit = x; });
      if (!hit) { hit = { uom: pk.uom, qty: 0, f: pk.f }; ps.push(hit); }
      hit.qty = r3(kkNum(hit.qty) + 1); hit.f = pk.f;
      r.cach_dem = kkPartsEnc(ps); r.so_luong = kkPartsSum(ps);
    } else {
      r.so_luong = r3(kkNum(r.so_luong) + 1); r.cach_dem = '';
    }
    r.da_dem = 1;
    kkTouch();
    return '✓ ' + r.item_name + '\n' +
      (pk ? kkPartsText(r.cach_dem) + ' = ' + num(r.so_luong) + ' ' + r.dvt : num(r.so_luong) + ' ' + r.dvt);
  });
  kkDraw();
}

/* ---------- 14d. Luu phieu ---------- */
function kkTouch() {
  kk.dirty = 1;
  var el = document.getElementById('kksv');
  if (el) el.textContent = 'Có thay đổi chưa lưu...';
  clearTimeout(kk.tmr);
  kk.tmr = setTimeout(function () { kkSave(0); }, 3000);
}

async function kkSave(loud) {
  if (!kk.doc || !kkLive()) return true;
  if (kk.saving) { clearTimeout(kk.tmr); kk.tmr = setTimeout(function () { kkSave(loud); }, 1500); return false; }
  if (!kk.dirty && !loud) return true;
  kk.saving = 1;
  clearTimeout(kk.tmr);
  if (loud) busy(1);
  var el = document.getElementById('kksv');
  if (el) el.textContent = 'Đang lưu...';
  try {
    var d = kk.doc;
    d.items = kk.rows.map(function (r, i) {
      var o = {
        idx: i + 1, item_code: r.item_code, item_name: r.item_name, item_group: r.item_group,
        dvt: r.dvt, ton_he_thong: kkNum(r.ton_he_thong), so_luong: kkNum(r.so_luong),
        cach_dem: r.cach_dem || '',
        lech: r3(kkNum(r.so_luong) - kkNum(r.ton_he_thong)),
        han_su_dung: r.han_su_dung || null, ghi_chu: r.ghi_chu || '', da_dem: r.da_dem ? 1 : 0
      };
      if (r.name) { o.name = r.name; o.parent = d.name; o.parenttype = 'Phieu Kiem Ke'; o.parentfield = 'items'; o.doctype = 'Chi Tiet Kiem Ke'; }
      return o;
    });
    d.so_mon = kk.rows.filter(function (r) { return r.da_dem; }).length;
    if (!d.nguoi_kiem) d.nguoi_kiem = S.me.full_name || S.user;
    var nd = await api('frappe.client.save', { doc: d });
    if (nd && nd.name) {
      kk.doc = nd; kk.dirty = 0;
      var byc = {}; (nd.items || []).forEach(function (x) { byc[x.item_code] = x.name; });
      kk.rows.forEach(function (r) { if (byc[r.item_code]) r.name = byc[r.item_code]; });
    }
    var t = new Date();
    kk.savedAt = pad2(t.getHours()) + ':' + pad2(t.getMinutes());
    if (loud) busy(0);
    var e2 = document.getElementById('kksv');
    if (e2) e2.textContent = 'Đã lưu lúc ' + kk.savedAt + ' · ' + d.so_mon + ' món';
    if (loud) toast('Đã lưu phiếu ' + d.name);
    kk.saving = 0;
    return true;
  } catch (e) {
    kk.saving = 0;
    if (loud) busy(0);
    var e3 = document.getElementById('kksv');
    if (e3) e3.textContent = 'Chưa lưu được, sẽ thử lại...';
    if (loud) toast(errMsg(e));
    if (String(errMsg(e)).indexOf('sửa') >= 0 || String(errMsg(e)).indexOf('Timestamp') >= 0) {
      try { kk.doc = await api('frappe.client.get', { doctype: 'Phieu Kiem Ke', name: kk.doc.name }); } catch (x) { }
    }
    clearTimeout(kk.tmr);
    kk.tmr = setTimeout(function () { kkSave(0); }, 6000);
    return false;
  }
}

async function kkFinish() {
  var chua = (kk.cat || []).length - kk.rows.filter(function (r) { return r.da_dem; }).length;
  var msg = 'Phiếu ' + kk.doc.name + ' · ' + shortWh(kk.doc.kho) + ' · ' + kk.doc.pham_vi +
    '\nĐã đếm ' + kk.rows.filter(function (r) { return r.da_dem; }).length + ' món.';
  if (chua > 0) msg += '\n\nCòn ' + chua + ' món trong nhóm chưa đếm. Những món này sẽ KHÔNG được ghi vào sổ, tồn kho của chúng giữ nguyên như cũ.';
  msg += '\n\nChốt xong thì không sửa số được nữa (vẫn mở lại được nếu cần).';
  var ok = await confirmSheet('Chốt phiếu kiểm kê?', msg, 'Chốt phiếu');
  if (!ok) return;
  if (!await kkSave(1)) return toast('Chưa lưu được phiếu, kiểm tra mạng rồi chốt lại');
  busy(1);
  try {
    kk.doc.trang_thai = 'Chờ duyệt';
    kk.doc = await api('frappe.client.save', { doc: kk.doc });
    busy(0);
    toast('Đã chốt phiếu ' + kk.doc.name);
    kkDraw();
  } catch (e) { busy(0); kk.doc.trang_thai = 'Đang kiểm'; toast(errMsg(e)); }
}

async function kkCancel() {
  var ok = await confirmSheet('Huỷ phiếu kiểm kê này?',
    'Phiếu ' + kk.doc.name + ' sẽ chuyển sang trạng thái Đã huỷ và không ghi vào sổ kho.\nSố đã đếm vẫn giữ lại trong phiếu để tra cứu, mở lại được nếu cần.',
    'Huỷ phiếu', true);
  if (!ok) return;
  busy(1);
  try {
    await kkSave(0);
    kk.doc.trang_thai = 'Đã huỷ';
    kk.doc = await api('frappe.client.save', { doc: kk.doc });
    busy(0); toast('Đã huỷ phiếu ' + kk.doc.name); kkDraw();
  } catch (e) { busy(0); kk.doc.trang_thai = 'Đang kiểm'; toast(errMsg(e)); }
}

async function kkReopen() {
  var ok = await confirmSheet('Mở lại phiếu để sửa?', 'Phiếu sẽ quay về trạng thái Đang kiểm để đếm hoặc sửa tiếp.', 'Mở lại');
  if (!ok) return;
  busy(1);
  try {
    kk.doc.trang_thai = 'Đang kiểm';
    kk.doc = await api('frappe.client.save', { doc: kk.doc });
    busy(0); toast('Đã mở lại phiếu'); kkDraw();
  } catch (e) { busy(0); toast(errMsg(e)); }
}

/* ---------- 14e. Ghi so: tao Stock Reconciliation ---------- */
var kkp = { doc: null, rows: [], rates: {}, opening: 1 };

async function scrKkPost(name) {
  frame('Ghi sổ kiểm kê', '<div class="emp"><div class="e1">⏳</div></div>');
  var d = null;
  try { d = await api('vagabond.kiem_ke.mo_phieu', { name: name }); }
  catch (e) { toast(errMsg(e)); return back(); }
  if (d.trang_thai === 'Đã ghi sổ') { toast('Phiếu này đã ghi sổ rồi'); return back(); }
  kkp.doc = d;
  kkp.lyDo = d.ly_do_lech || [];
  kkp.rows = (d.items || []).filter(function (r) { return r.da_dem; });
  var codes = kkp.rows.map(function (r) { return r.item_code; });
  var info = {};
  try {
    var its = await inChunks(codes, 80, function (lot) {
      return getList('Item', { fields: ['name', 'item_name', 'stock_uom', 'has_batch_no', 'valuation_rate', 'last_purchase_rate'], filters: { name: ['in', lot] }, limit_page_length: 0 });
    });
    its.forEach(function (i) { info[i.name] = i; });
  } catch (e) { toast(errMsg(e)); }
  kkp.info = info;
  kkp.acc = ''; kkp.cc = ''; kkp.accs = [];
  try {
    var cp = await api('frappe.client.get_value', { doctype: 'Company', filters: { name: COMPANY }, fieldname: ['stock_adjustment_account', 'cost_center'] });
    kkp.accAdj = (cp && cp.stock_adjustment_account) || '';
    kkp.cc = (cp && cp.cost_center) || '';
  } catch (e) { }
  kkp.accOpen = '';
  try {
    var tmpa = await getList('Account', { fields: ['name'], filters: { company: COMPANY, account_type: 'Temporary', is_group: 0 }, limit_page_length: 1 });
    if (tmpa && tmpa.length) kkp.accOpen = tmpa[0].name;
  } catch (e) { }
  kkp.acc = kkp.opening ? (kkp.accOpen || kkp.accAdj) : (kkp.accAdj || kkp.accOpen);
  try {
    kkp.accs = (await getList('Account', { fields: ['name'], filters: { company: COMPANY, is_group: 0 }, limit_page_length: 0, order_by: 'name' })).map(function (a) { return { value: a.name, label: a.name }; });
  } catch (e) { kkp.accs = []; }
  kkp.rates = {};
  kkp.rows.forEach(function (r) {
    var i = info[r.item_code] || {};
    kkp.rates[r.item_code] = kkNum(i.valuation_rate) || kkNum(i.last_purchase_rate) || 0;
  });
  kkpDraw();
}

/* Ly do chenh lech chuan (anh Viet duyet 03/09/2026, SAP goi la reason for
   movement). Chip chu khong o xo danh sach, theo bo nguyen tac muc 2b: it
   lua chon thi chip cham mot lan la xong. Chi bay ra nhung ly do DUNG CHIEU
   voi chenh lech - chon "hao hut" cho mot dong thua hang la sai nghia. */
function kkpLyDoHop(dv) {
  return (kkp.lyDo || []).filter(function (x) {
    return dv > 0 ? x.dau >= 0 : (dv < 0 ? x.dau <= 0 : true);
  });
}
function kkpLyDoChip(r, dv) {
  var ds = kkpLyDoHop(dv);
  if (!ds.length) return '';
  return '<div style="display:flex;gap:6px;overflow-x:auto;padding:8px 0 2px;-webkit-overflow-scrolling:touch">' +
    ds.map(function (x) {
      var on = r.vgb_ly_do_lech === x.ma;
      return '<button class="chp' + (on ? ' on' : '') + '" data-ly="' + h(r.name) + '" data-lyma="' + h(x.ma) + '" ' +
        'style="flex:0 0 auto;min-height:36px;padding:0 12px;border-radius:999px;font-size:13px;' +
        'border:1px solid ' + (on ? '#0B7C93' : '#d7dbe0') + ';background:' + (on ? '#0B7C93' : '#fff') + ';' +
        'color:' + (on ? '#fff' : '#374151') + '">' + h(x.ten) + '</button>';
    }).join('') + '</div>';
}

function kkpDraw() {
  var d = kkp.doc;
  var noRate = kkp.rows.filter(function (r) { return kkNum(r.so_luong) > 0 && !kkp.rates[r.item_code]; });
  var batchN = kkp.rows.filter(function (r) { return (kkp.info[r.item_code] || {}).has_batch_no && kkNum(r.so_luong) > 0; }).length;

  var body = '<div class="rcvh">Bước này ghi số đã đếm vào sổ kho thật. Máy sẽ tạo <b>một phiếu điều chỉnh tồn kho</b> (Stock Reconciliation) và nộp luôn. Sau khi nộp thì tồn kho đổi theo số đã đếm.</div>' +
    '<div class="card">' +
    '<div class="kv"><span>Phiếu kiểm kê</span><b>' + h(d.name) + '</b></div>' +
    '<div class="kv"><span>Kho</span><b>' + h(shortWh(d.kho)) + '</b></div>' +
    '<div class="kv"><span>Nhóm hàng</span><b>' + h(d.pham_vi) + '</b></div>' +
    '<div class="kv"><span>Số món ghi sổ</span><b>' + kkp.rows.length + '</b></div>' +
    '<div class="kv"><span>Món quản lý theo lô</span><b>' + batchN + '</b></div>' +
    '</div>' +
    '<div class="card"><div class="fld" data-op><div class="fi">📘</div><div class="ft">' +
    '<div class="fl">Kiểu ghi sổ</div><div class="fv">' + (kkp.opening ? 'Tồn đầu kỳ (lần đầu đưa số lên máy)' : 'Điều chỉnh tồn (kiểm kê định kỳ)') + '</div></div>' +
    '<div class="fc">&#8250;</div></div>' +
    '<div class="fld" data-acc><div class="fi">🧾</div><div class="ft">' +
    '<div class="fl">Tài khoản đối ứng chênh lệch</div><div class="fv' + (kkp.acc ? '' : ' ph') + '">' + h(kkp.acc || 'Chọn tài khoản') + '</div></div>' +
    '<div class="fc">&#8250;</div></div>' +
    '<div class="fld" data-cc><div class="fi">🏷️</div><div class="ft">' +
    '<div class="fl">Trung tâm chi phí</div><div class="fv' + (kkp.cc ? '' : ' ph') + '">' + h(kkp.cc || 'Chọn') + '</div></div>' +
    '<div class="fc">&#8250;</div></div></div>' +
    (kkp.opening ? '<div class="kwn">Ghi <b>tồn đầu kỳ</b> thì phần chênh lệch đối ứng vào tài khoản ở trên. Kế toán đã chốt dùng <b>Temporary Opening</b> cho lần đầu đưa số lên máy. Bút toán sẽ vào sổ cái thật.</div>' : '<div class="kwn">Kiểm kê định kỳ thì chênh lệch đối ứng vào tài khoản chi phí ở trên (mặc định 811 - Chi phí khác). Hỏi kế toán nếu không chắc.</div>');

  if (batchN) {
    body += '<div class="kwn">Có ' + batchN + ' món quản lý theo lô. Máy sẽ tự tạo một lô tồn đầu kỳ cho mỗi món, đặt tên theo phiếu kiểm kê này, lấy hạn sử dụng đã nhập nếu có.</div>';
  }

  if (noRate.length) {
    body += '<div class="sec">Cần điền giá vốn (' + noRate.length + ' món)</div>' +
      '<div class="kwn">Máy chưa biết giá vốn của những món này nên chưa ghi sổ được. Điền giá mua 1 đơn vị (chưa VAT) rồi bấm ghi sổ.</div>' +
      noRate.slice(0, 120).map(function (r) {
        return '<div class="ic1"><div class="ih"><div class="n">!</div><div class="in">' + h(r.item_name || r.item_code) +
          '<div class="ig">' + h(r.item_code) + ' · đếm ' + num(r.so_luong) + ' ' + h(r.dvt) + '</div></div></div>' +
          '<div class="qw"><div style="flex:1;min-width:0"><div class="lb">Giá vốn 1 ' + h(r.dvt) + ' (VND)</div>' +
          '<div class="qr"><div class="stp"><input type="number" inputmode="decimal" step="any" data-rate="' + h(r.item_code) + '" value="" placeholder="0"></div>' +
          '<div class="uml">VND</div></div></div></div></div>';
      }).join('');
  }

  var lech = kkp.rows.filter(function (r) { return Math.abs(kkNum(r.so_luong) - kkNum(r.ton_he_thong)) > 0.0001; });
  if (lech.length) {
    var chuaLy = lech.filter(function (r) { return !r.vgb_ly_do_lech; }).length;
    body += '<div class="sec">Lệch so với máy (' + lech.length + ' món)</div>' +
      (chuaLy ? '<div class="kwn">Còn <b>' + chuaLy + ' món</b> chưa chọn lý do chênh lệch. Chọn đủ rồi mới ghi sổ được. Cuối tháng đọc báo cáo lệch theo lý do là biết nên sửa chỗ nào trong quy trình.</div>' : '') +
      '<div class="lst">' +
      lech.slice(0, 200).map(function (r, i) {
        var dv = r3(kkNum(r.so_luong) - kkNum(r.ton_he_thong));
        return '<div class="li" style="display:block"><div style="display:flex;align-items:center;gap:8px">' +
          '<div class="lt" style="flex:1;min-width:0"><div class="l1">' + h(r.item_name || r.item_code) + '</div>' +
          '<div class="l2">máy ' + num(r.ton_he_thong) + ' → đếm ' + num(r.so_luong) + ' ' + h(r.dvt) +
          (kkPartsText(r.cach_dem) ? ' (' + h(kkPartsText(r.cach_dem)) + ')' : '') + '</div></div>' +
          '<span class="st ' + (dv > 0 ? 'g' : 'r') + '">' + (dv > 0 ? '+' : '') + num(dv) + '</span></div>' +
          kkpLyDoChip(r, dv) + '</div>';
      }).join('') + '</div>';
  }

  var b = frame('Ghi sổ kiểm kê', body, { footer: '<button class="btn" id="kkpgo">Tạo phiếu điều chỉnh và nộp</button>' });
  b.onclick = function (e) {
    if (e.target.closest('[data-acc]')) {
      return sheet('Tài khoản đối ứng', kkp.accs, kkp.acc, function (o) { kkp.acc = o.value; kkpDraw(); }, true);
    }
    if (e.target.closest('[data-cc]')) {
      if (!kkp.ccs) {
        return getList('Cost Center', { fields: ['name'], filters: { company: COMPANY, is_group: 0 }, limit_page_length: 0 }).then(function (cs) {
          kkp.ccs = cs.map(function (c) { return { value: c.name, label: c.name }; });
          sheet('Trung tâm chi phí', kkp.ccs, kkp.cc, function (o) { kkp.cc = o.value; kkpDraw(); }, true);
        });
      }
      return sheet('Trung tâm chi phí', kkp.ccs, kkp.cc, function (o) { kkp.cc = o.value; kkpDraw(); }, true);
    }
    var ly = e.target.closest('[data-ly]');
    if (ly) {
      var ten = ly.dataset.ly, ma = ly.dataset.lyma;
      var d0 = kkp.rows.filter(function (x) { return x.name === ten; })[0];
      if (d0) {
        var moi = d0.vgb_ly_do_lech === ma ? '' : ma;
        d0.vgb_ly_do_lech = moi;
        kkpDraw();
        api('vagabond.kiem_ke.ghi_ly_do', { name: kkp.doc.name, dong: ten, ly_do: moi })
          .catch(function (er) { toast(errMsg(er)); });
      }
      return;
    }
    if (e.target.closest('[data-op]')) {
      sheet('Kiểu ghi sổ', [
        { value: 1, label: 'Tồn đầu kỳ (lần đầu đưa số lên máy)' },
        { value: 0, label: 'Điều chỉnh tồn (kiểm kê định kỳ)' }
      ], kkp.opening, function (o) { kkp.opening = o.value; kkp.acc = o.value ? (kkp.accOpen || kkp.accAdj) : (kkp.accAdj || kkp.accOpen); kkpDraw(); });
    }
  };
  b.addEventListener('input', function (e) {
    var ri = e.target.closest('[data-rate]');
    if (ri) kkp.rates[ri.dataset.rate] = kkNum(ri.value);
  });
  document.getElementById('kkpgo').onclick = kkpSubmit;
}

async function kkpSubmit() {
  var d = kkp.doc;
  var rows = kkp.rows.filter(function (r) { return kkNum(r.so_luong) > 0 || kkNum(r.ton_he_thong) > 0; });
  if (!rows.length) return toast('Phiếu không có món nào để ghi sổ');
  var bad = rows.filter(function (r) { return kkNum(r.so_luong) > 0 && !kkp.rates[r.item_code]; });
  if (bad.length) return toast('Còn ' + bad.length + ' món chưa có giá vốn, vui lòng điền rồi ghi sổ lại');
  if (!kkp.acc) return toast('Chọn tài khoản đối ứng chênh lệch trước đã');
  var thieuLy = kkp.rows.filter(function (r) {
    return Math.abs(kkNum(r.so_luong) - kkNum(r.ton_he_thong)) > 0.0001 && !r.vgb_ly_do_lech;
  });
  if (thieuLy.length) return toast('Còn ' + thieuLy.length + ' món lệch chưa chọn lý do, chọn đủ rồi ghi sổ');

  var ok = await confirmSheet('Ghi sổ ' + rows.length + ' món?',
    'Kho ' + shortWh(d.kho) + ' · ' + d.pham_vi + '\n\nMáy sẽ tạo phiếu điều chỉnh tồn kho và NỘP luôn. Sau đó tồn kho đổi theo số đã đếm và không sửa lại bằng app được, phải huỷ phiếu trên máy tính.',
    'Ghi sổ ngay');
  if (!ok) return;

  busy(1);
  try {
    /* 1. tao lo ton dau ky cho cac mon quan ly theo lo */
    var batches = {};
    var need = rows.filter(function (r) { return (kkp.info[r.item_code] || {}).has_batch_no && kkNum(r.so_luong) > 0; });
    for (var i = 0; i < need.length; i++) {
      var r = need[i];
      var bid = kkBatchId(d.name, r.item_code);
      var bd = { doctype: 'Batch', batch_id: bid, item: r.item_code };
      if (r.han_su_dung) bd.expiry_date = r.han_su_dung;
      var exist = await getList('Batch', { fields: ['name'], filters: { name: bid }, limit_page_length: 1 });
      if (exist && exist.length) {
        if (r.han_su_dung) { try { await api('frappe.client.set_value', { doctype: 'Batch', name: bid, fieldname: { expiry_date: r.han_su_dung } }); } catch (eb) { } }
        batches[r.item_code] = bid; continue;
      }
      var nb = await api('frappe.client.insert', { doc: bd });
      batches[r.item_code] = (nb && nb.name) || bid;
    }

    /* 2. dung phieu dieu chinh ton kho */
    var now = new Date();
    var sr = {
      doctype: 'Stock Reconciliation',
      company: COMPANY,
      purpose: kkp.opening ? 'Opening Stock' : 'Stock Reconciliation',
      posting_date: d.ngay_kiem || ymdOf(now),
      posting_time: hmOf(now),
      set_posting_time: 1,
      set_warehouse: d.kho,
      expense_account: kkp.acc,
      cost_center: kkp.cc || undefined,
      items: rows.map(function (r) {
        var it = { item_code: r.item_code, warehouse: d.kho, qty: kkNum(r.so_luong), valuation_rate: kkp.rates[r.item_code] || 0 };
        if (kkp.cc) it.cost_center = kkp.cc;
        if (batches[r.item_code]) { it.use_serial_batch_fields = 1; it.batch_no = batches[r.item_code]; }
        return it;
      })
    };
    var doc = await api('frappe.client.insert', { doc: sr });
    if (!doc || !doc.name) throw new Error('Không tạo được phiếu điều chỉnh');
    await api('frappe.client.submit', { doc: doc });

    /* 3. dong phieu kiem ke */
    d.trang_thai = 'Đã ghi sổ';
    d.stock_reconciliation = doc.name;
    await api('frappe.client.save', { doc: d });

    busy(0);
    toast('Đã ghi sổ bằng phiếu ' + doc.name, 4200);
    kk.doc = null; kk.cat = null; kk.catKey = '';
    reset(scrHome); go(scrKkList);
  } catch (e) { busy(0); toast(errMsg(e), 5000); }
}

/* ---------- 15. Yeu cau mua hang test (R&D) ---------- */
var RNDST = {
  'Mới tạo': { c: 'w', t: 'Mới tạo' },
  'Đang xử lý': { c: 'b', t: 'Đang xử lý' },
  'Hoàn thành': { c: 'g', t: 'Hoàn thành' },
  'Huỷ': { c: 'n', t: 'Đã huỷ' }
};
var RNDLS = {
  'Chưa mua': { c: 'w', t: 'Chưa mua' },
  'Đã mua': { c: 'g', t: 'Đã mua' },
  'Không mua được': { c: 'r', t: 'Không mua được' }
};
var rnd = { newf: null };
function isRnd() { return hasRole('Mua hàng R&D') || hasRole('System Manager'); }
function isSales() { return hasRole('Sales User') || hasRole('Sales Manager') || hasRole('Bộ phận đặt hàng') || hasRole('System Manager'); }

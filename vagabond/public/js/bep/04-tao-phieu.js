/* ---------- 7. Tao moi: buoc 1 thong tin chung ---------- */
function startDraft(T) {
  S.draft = {
    T: T, type: T.key,
    schedule_date: addDays(today(), 1),
    time: T.key === 'Manufacture' ? '06:00' : '08:00',
    set_warehouse: '', set_from_warehouse: '',
    bo_phan: S.me.bo_phan || '', nguoi_yeu_cau: S.me.full_name || S.user, note: '',
    bep_nhan: '', items: [], photos: []
  };
  var pref = { Purchase: 'Kho tổng 307 - TV', 'Material Transfer': '', Manufacture: '' };
  if (S.wh.indexOf(pref[T.key]) >= 0) S.draft.set_warehouse = pref[T.key];
  if (T.key === 'Manufacture') S.draft.bep_nhan = myKitchen() || '';
  go(scrStep1);
}

var TIMES = ['05:00', '06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00', '14:00', '16:00', '18:00'];

function scrStep1() {
  var d = S.draft, T = d.T;
  function fld(icon, label, val, ph, act) {
    return '<div class="fld" data-a="' + act + '"><div class="fi">' + icon + '</div>' +
      '<div class="ft"><div class="fl">' + h(label) + '</div>' +
      '<div class="fv' + (val ? '' : ' ph') + '">' + h(val || ph) + '</div></div>' +
      '<div class="fc">&#8250;</div></div>';
  }
  var html = '<div class="card">' +
    (T.needFrom ? fld('📤', 'Kho xuất hàng', shortWh(d.set_from_warehouse), 'Chọn kho lấy hàng', 'from') : '') +
    (T.needFrom && laKhoCuaToi(d.set_from_warehouse) ? '<div style="margin:10px 0 0;padding:12px 14px;border-radius:14px;background:#fff6e5;color:#8a5b00;font-size:13px;line-height:1.5">Kho này do bạn phụ trách, không cần xin ai. <b onclick="vgbLapPhieuChuyen(\'' + h(d.set_from_warehouse) + '\', \'' + h(d.set_warehouse || '') + '\')" style="text-decoration:underline">Lập thẳng phiếu điều chuyển</b></div>' : '') +
    fld('📥', T.key === 'Manufacture' ? 'Kho nhận bánh' : 'Kho nhận hàng', shortWh(d.set_warehouse), 'Chọn kho nhận', 'to') +
    (T.key === 'Manufacture' ? fld('🧑‍🍳', 'Gửi yêu cầu đến bếp', d.bep_nhan, 'Bắt buộc - chọn bếp', 'bep') : '') +
    fld('📅', 'Ngày cần', dmy(d.schedule_date), '', 'date') +
    '</div>' +
    (T.key === 'Manufacture' && !d.bep_nhan ?
      '<div style="padding:2px 16px 0;font-size:12.5px;color:#8a8f9c;line-height:1.5">Bếp nào được gửi thì bếp đó mới thấy phiếu.</div>' : '') +
    (T.hasTime ?
      '<div class="card"><div style="padding:14px 14px 4px"><div class="fl" style="font-size:12px;color:#8a8f9c;margin-bottom:8px">' + h(T.timeLabel) + ' (áp dụng cho cả phiếu)</div>' +
      '<input type="time" class="tin" id="t1time" value="' + h(hm(d.time)) + '" step="60">' +
      '<div class="tch">' + TIMES.map(function (t) { return '<span data-t="' + t + '"' + (t === hm(d.time) ? ' class="on"' : '') + '>' + t + '</span>'; }).join('') + '</div></div>' +
      '<div style="padding:10px 14px 14px;font-size:12.5px;color:#8a8f9c;line-height:1.5">Từng món có thể đổi giờ riêng ở bước sau.</div></div>'
      : '') +
    '<div class="sec">Người yêu cầu</div><div class="card">' +
    fld('🏢', 'Bộ phận yêu cầu', shortDep(d.bo_phan), 'Bắt buộc - chọn bộ phận', 'dept') +
    '<div class="fld" style="cursor:default"><div class="fi">👤</div><div class="ft">' +
    '<div class="fl">Người yêu cầu</div><div class="fv">' + h(d.nguoi_yeu_cau) + '</div></div></div>' +
    '</div>';

  var b = frame(T.title, html, { footer: '<button class="btn" id="t1next">Tiếp tục</button>' });
  var ti = document.getElementById('t1time');
  if (ti) ti.onchange = function () { d.time = hm(ti.value); scrStep1(); };
  b.onclick = function (e) {
    var t = e.target.closest('[data-t]'); if (t) { d.time = t.dataset.t; return scrStep1(); }
    var a = e.target.closest('[data-a]'); if (!a) return;
    var k = a.dataset.a;
    if (k === 'from') sheet('Kho xuất hàng', whOpts(), d.set_from_warehouse, function (o) { d.set_from_warehouse = o.value; scrStep1(); }, true);
    if (k === 'to') sheet('Kho nhận hàng', whOpts(), d.set_warehouse, function (o) { d.set_warehouse = o.value; scrStep1(); }, true);
    if (k === 'bep') {
      var bo = [];
      BEPS.forEach(function (x) { bo.push({ value: x, label: x, icon: '🧑‍🍳' }); });
      sheet('Gửi yêu cầu đến bếp', bo, d.bep_nhan, function (o) { d.bep_nhan = o.value; scrStep1(); }, true);
    }
    if (k === 'dept') {
      sheet('Bộ phận yêu cầu', DEPTS.map(function (x) { return { value: x, label: shortDep(x) }; }), d.bo_phan, function (o) {
        d.bo_phan = o.value;
        S.me.bo_phan = o.value;
        if (syncUser()) {
          try { localStorage.setItem('vgb_bp_' + S.user, o.value); } catch (x) { }
          api('frappe.client.set_value', { doctype: 'User', name: S.user, fieldname: 'custom_phong_ban', value: o.value }).catch(function () { });
        }
        scrStep1();
      }, true);
    }
    if (k === 'date') {
      var opts = [];
      for (var i = 0; i <= 14; i++) { var iso = addDays(today(), i); opts.push({ value: iso, label: dmy(iso) + (i === 0 ? ' (hôm nay)' : i === 1 ? ' (ngày mai)' : '') }); }
      sheet('Ngày cần hàng', opts, d.schedule_date, function (o) { d.schedule_date = o.value; scrStep1(); });
    }
  };
  document.getElementById('t1next').onclick = function () {
    if (T.needFrom && !d.set_from_warehouse) return toast('Chưa chọn kho xuất hàng');
    if (!d.set_warehouse) return toast('Chưa chọn kho nhận hàng');
    if (T.key === 'Manufacture' && !d.bep_nhan) return toast('Chưa chọn bếp nhận yêu cầu');
    if (!d.bo_phan) return toast('Chưa chọn bộ phận yêu cầu');
    go(scrStep2);
  };
}

/* ---------- 8. Buoc 2: chon hang hoa ---------- */
var pick = { group: '', q: '', cache: {}, sel: {}, nm: {}, sl: {}, allow: null, seq: 0 };
async function scrStep2() {
  var d = S.draft;
  pick.sel = {}; pick.nm = {}; pick.sl = {};
  (d.items || []).forEach(function (it) { pick.sel[it.item_code] = 1; pick.nm[it.item_code] = it.item_name; });
  pick.cache = {}; pick.group = ''; pick.q = '';
  pick.allow = leavesUnder(d.T.roots);
  await drawPick(true);
}

/* dung danh sach hang hoa day du tu [{item_code, qty, uom, note, time}] */
async function buildItems(reqs, existing) {
  var d = S.draft;
  existing = existing || [];
  var codes = reqs.map(function (r) { return r.item_code; });
  var keep = existing.filter(function (it) { return codes.indexOf(it.item_code) >= 0; });
  var have = keep.map(function (it) { return it.item_code; });
  var need = codes.filter(function (c) { return have.indexOf(c) < 0; });
  if (need.length) {
    var meta = await getList('Item', { fields: ['name', 'item_name', 'stock_uom', 'purchase_uom', 'item_group', 'image', 'custom_bep_phu_trach'], filters: { name: ['in', need] }, limit_page_length: 500 });
    var conv = await getList('UOM Conversion Detail', { parent: 'Item', fields: ['parent', 'uom', 'conversion_factor'], filters: { parent: ['in', need], parenttype: 'Item' }, limit_page_length: 500 });
    var bins = await getList('Bin', { fields: ['item_code', 'actual_qty'], filters: { item_code: ['in', need], warehouse: 'Kho tổng 307 - TV' }, limit_page_length: 500 });
    var bm = {}; bins.forEach(function (x) { bm[x.item_code] = x.actual_qty; });
    var rq = {}; reqs.forEach(function (r) { rq[r.item_code] = r; });
    meta.forEach(function (m) {
      var us = conv.filter(function (c) { return c.parent === m.name; }).map(function (c) { return { uom: c.uom, cf: c.conversion_factor }; });
      if (!us.some(function (u) { return u.uom === m.stock_uom; })) us.unshift({ uom: m.stock_uom, cf: 1 });
      var r = rq[m.name] || {};
      var dfl = (m.purchase_uom && us.some(function (u) { return u.uom === m.purchase_uom; })) ? m.purchase_uom : m.stock_uom;
      var uom = (r.uom && us.some(function (u) { return u.uom === r.uom; })) ? r.uom : dfl;
      var cf = (us.filter(function (u) { return u.uom === uom; })[0] || { cf: 1 }).cf;
      keep.push({
        item_code: m.name, item_name: m.item_name, image: m.image || '',
        item_group: m.item_group || '', bep: m.custom_bep_phu_trach || '',
        stock_uom: m.stock_uom, uom: uom, cf: cf, uoms: us,
        qty: (r.qty > 0 ? r.qty : 1), time: hm(r.time || d.time), note: r.note || '', ton: bm[m.name] || 0
      });
    });
  }
  keep.sort(function (a, b2) { return codes.indexOf(a.item_code) - codes.indexOf(b2.item_code); });
  return keep;
}

/* lay hang hoa tu mau don da luu */
async function loadTemplate() {
  var d = S.draft;
  var tpls = [];
  busy(1);
  try {
    tpls = await getList('VGB Order Template', { fields: ['name', 'template_name', 'items_json', 'bo_phan'], filters: { request_type: d.type }, limit_page_length: 100, order_by: 'template_name' });
  } catch (e) { busy(0); return toast(errMsg(e)); }
  busy(0);
  if (!tpls.length) return toast('Chưa có mẫu nào cho loại phiếu này');
  /* bang chon mau tu dung, moi dong co nut doi ten va xoa (Uyen/De yeu cau 07/08) */
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>Mẫu đơn đã lưu</b><div class="x">&times;</div></div>' +
    '<div style="padding:2px 14px 6px;display:flex;gap:8px"><input class="nt" placeholder="Tìm nhanh..." style="height:46px;padding:0 12px;flex:1"></div>' +
    '<div style="padding:0 14px 6px;color:#a0a6b4;font-size:12.5px">Bấm tên mẫu để lấy món vào phiếu. Mẫu dùng chung cả tiệm, xoá là mất với mọi người.</div>' +
    '<div class="shl"></div>';
  var lst = box.querySelector('.shl');
  var q0 = '';
  function veDs() {
    var f = tpls.filter(function (t) { return !q0 || (t.template_name + ' ' + (t.bo_phan || '')).toLowerCase().indexOf(q0) >= 0; });
    lst.innerHTML = f.length ? f.map(function (t) {
      var i = tpls.indexOf(t);
      return '<div class="shi" data-i="' + i + '"><span>📋</span>' +
        '<span style="flex:1;min-width:0">' + h(t.template_name) +
        (t.bo_phan ? '<div style="color:#a0a6b4;font-size:12px;margin-top:2px">' + h(t.bo_phan) + '</div>' : '') + '</span>' +
        '<button class="nt" data-s="' + i + '" title="Đổi tên mẫu" style="height:40px;width:46px;flex:none;font-size:16px;cursor:pointer">✏️</button>' +
        '<button class="nt" data-x="' + i + '" title="Xoá mẫu" style="height:40px;width:46px;flex:none;font-size:16px;cursor:pointer;margin-left:6px;color:#b91c1c">🗑️</button></div>';
    }).join('') : '<div class="emp"><div class="e2">Không tìm thấy</div></div>';
  }
  veDs();
  ov.appendChild(box); document.body.appendChild(ov);
  var tim = box.querySelector('input');
  tim.oninput = function () { q0 = (tim.value || '').toLowerCase(); veDs(); };
  function dong() { ov.remove(); }
  ov.onclick = function (e) { if (e.target === ov) dong(); };
  box.querySelector('.x').onclick = dong;
  lst.onclick = async function (e) {
    var bs = e.target.closest('[data-s]');
    if (bs) {
      var ts = tpls[+bs.dataset.s];
      var nm2 = await promptSheet('Đổi tên mẫu "' + ts.template_name + '"', ts.template_name);
      if (!nm2 || nm2 === ts.template_name) return;
      busy(1);
      try {
        await api('frappe.client.set_value', { doctype: 'VGB Order Template', name: ts.name, fieldname: 'template_name', value: nm2 });
        ts.template_name = nm2; veDs(); toast('Đã đổi tên mẫu');
      } catch (err) { toast(errMsg(err), 4200); } finally { busy(0); }
      return;
    }
    var bx = e.target.closest('[data-x]');
    if (bx) {
      var tx = tpls[+bx.dataset.x];
      var chac = await confirmSheet('Xoá mẫu "' + tx.template_name + '"?', 'Mẫu dùng chung cả tiệm, xoá rồi là mất với mọi người, không lấy lại được.', 'Xoá mẫu', true);
      if (!chac) return;
      busy(1);
      try {
        await api('frappe.client.delete', { doctype: 'VGB Order Template', name: tx.name });
        tpls.splice(tpls.indexOf(tx), 1); veDs(); toast('Đã xoá mẫu "' + tx.template_name + '"');
      } catch (err) { toast(errMsg(err), 4200); } finally { busy(0); }
      return;
    }
    var r = e.target.closest('.shi'); if (!r) return;
    var t = tpls[+r.dataset.i];
    var arr = [];
    try { arr = JSON.parse(t.items_json || '[]'); } catch (e2) { }
    if (!arr.length) return toast('Mẫu này không có hàng hoá');
    dong();
    busy(1);
    try {
      d.items = await buildItems(arr, d.items);
      arr.forEach(function (r2) { pick.sel[r2.item_code] = 1; });
      (d.items || []).forEach(function (it) { pick.nm[it.item_code] = it.item_name; });
      toast('Đã lấy ' + arr.length + ' món từ mẫu ' + t.template_name);
      go(scrStep3);
    } catch (err) { toast(errMsg(err)); } finally { busy(0); }
  };
}
function selInner() {
  var selc = Object.keys(pick.sel).filter(function (k) { return pick.sel[k]; });
  if (!selc.length) return '';
  return '<div class="selh">Đã chọn (' + selc.length + ')</div><div class="sell">' +
    selc.map(function (c) {
      return '<div class="selc" data-r="' + h(c) + '">' + h(pick.nm[c] || c) + '<span>&times;</span></div>';
    }).join('') + '</div>';
}
function paintSel() {
  var n = Object.keys(pick.sel).filter(function (k) { return pick.sel[k]; }).length;
  var w = document.getElementById('selw');
  if (w) { w.innerHTML = selInner(); w.style.display = n ? '' : 'none'; }
  var bt = document.getElementById('p2next');
  if (bt) { bt.disabled = !n; bt.textContent = 'Tiếp tục' + (n ? ' (' + n + ')' : ''); }
}
async function drawPick(fetch) {
  var d = S.draft;
  var key = pick.group || '*';
  var qs = (pick.q || '').trim();
  var qk = qs.length >= 2 ? 'q|' + key + '|' + qs.toLowerCase() : null;
  var ck = qk || key;
  if ((qk && !pick.cache[qk]) || (!qk && fetch && !pick.cache[key])) {
    var myq = ++pick.seq;
    if (!qk) frame('Chọn hàng hoá', '<div class="emp"><div class="e1">⏳</div></div>');
    var f = { disabled: 0, has_variants: 0 };
    if (pick.group) f.item_group = pick.group;
    else if (pick.allow && pick.allow.length) f.item_group = ['in', pick.allow];
    if (d.type === 'Purchase') f.is_purchase_item = 1;
    var ar = { fields: ['name', 'item_name', 'item_group', 'stock_uom', 'image'], filters: f, limit_page_length: 500, order_by: 'item_name' };
    if (qk) { ar.or_filters = { item_name: ['like', '%' + qs + '%'], name: ['like', '%' + qs + '%'] }; ar.limit_page_length = 300; }
    var res = [];
    try { res = await getList('Item', ar); } catch (e) { toast(errMsg(e)); }
    if (myq !== pick.seq) return;
    pick.cache[ck] = res;
  }
  var all = pick.cache[ck] || [];
  all.forEach(function (it) { if (!pick.nm[it.name]) pick.nm[it.name] = it.item_name; });
  var q = qs.toLowerCase();
  var rows = qk ? all.slice(0, 300)
    : all.filter(function (it) { return !q || (it.item_name + ' ' + it.name).toLowerCase().indexOf(q) >= 0; }).slice(0, 300);
  var nsel = Object.keys(pick.sel).filter(function (k) { return pick.sel[k]; }).length;
  var selHtml = '<div class="selw" id="selw"' + (nsel ? '' : ' style="display:none"') + '>' + selInner() + '</div>';
  var html = '<div class="card"><div class="fld" data-g><div class="fi">🏷️</div><div class="ft">' +
    '<div class="fl">Nhóm hàng hoá</div><div class="fv">' + h(pick.group || 'Tất cả') + '</div></div><div class="fc">&#8250;</div></div></div>' +
    srchBox('pq', 'Tìm theo tên hoặc mã', pick.q, true) + selHtml +
    (d.type === 'Manufacture' ? '<button class="btn gh" id="p2goi" style="margin-bottom:9px">✨ Gợi ý từ hệ thống</button>' : '') +
    '<button class="btn gh" id="p2tpl" style="margin-bottom:12px">📋 Lấy từ mẫu đã lưu</button>' +
    (rows.length ? '<div class="lst">' + rows.map(function (it) {
      return '<div class="li" data-c="' + h(it.name) + '">' +
        (it.image ? '<img class="im" src="' + h(it.image) + '" loading="lazy">' : '<div class="im imp">🍰</div>') +
        '<div class="lt"><div class="l1">' + h(it.item_name) + '</div>' +
        '<div class="l2">Mã: ' + h(it.name) + ' &middot; ' + h(it.stock_uom) + '</div></div>' +
        '<div class="ck' + (pick.sel[it.name] ? ' on' : '') + '">&#10003;</div></div>';
    }).join('') + '</div>' : '<div class="emp"><div class="e1">🔎</div><div class="e2">Không tìm thấy hàng hoá</div></div>');

  var b = frame('Chọn hàng hoá', html, { footer: '<button class="btn" id="p2next"' + (nsel ? '' : ' disabled') + '>Tiếp tục' + (nsel ? ' (' + nsel + ')' : '') + '</button>' });
  var pq = document.getElementById('pq');
  var tmr = null;
  pq.oninput = function () { pick.q = pq.value; clearTimeout(tmr); tmr = setTimeout(async function () { var v = pick.q; await drawPick(false); var i = document.getElementById('pq'); if (!i) return; i.focus(); i.value = v; i.setSelectionRange(v.length, v.length); }, 260); };
  document.getElementById('pqscan').onclick = async function () {
    var added = 0, miss = 0;
    await scanBarcode(async function (code) {
      var ic = null;
      try { ic = await itemByBarcode(code); } catch (e) { }
      if (!ic) { miss++; return '❌ Không có hàng hoá cho mã ' + code; }
      if (pick.sel[ic]) return '• Đã có trong danh sách: ' + (pick.nm[ic] || ic);
      if (!pick.nm[ic]) {
        try {
          var mm = await getList('Item', { fields: ['name', 'item_name'], filters: { name: ic }, limit_page_length: 1 });
          if (mm && mm.length) pick.nm[ic] = mm[0].item_name;
        } catch (e) { }
      }
      pick.sel[ic] = 1; added++;
      return '✅ ' + (pick.nm[ic] || ic) + '  (đã thêm ' + added + ')';
    });
    if (added) { await drawPick(false); toast('Đã thêm ' + added + ' món từ mã vạch'); }
    else if (miss) toast('Không tìm thấy hàng hoá có mã vạch này');
  };
  document.getElementById('p2tpl').onclick = function () { loadTemplate(); };
  var bgy = document.getElementById('p2goi');
  if (bgy) bgy.onclick = function () { goiYSheet(); };
  b.onclick = function (e) {
    if (e.target.closest('[data-g]')) {
      var gl = (pick.allow && pick.allow.length) ? pick.allow : S.groups;
      var opts = [{ value: '', label: 'Tất cả' }].concat(gl.map(function (g) { return { value: g, label: g }; }));
      return sheet('Nhóm hàng hoá', opts, pick.group, function (o) { pick.group = o.value; pick.q = ''; drawPick(true); }, true);
    }
    var rm = e.target.closest('[data-r]');
    if (rm) {
      var rc = rm.dataset.r;
      pick.sel[rc] = 0;
      var row = document.querySelector('#vgb .li[data-c="' + rc.replace(/"/g, '\\"') + '"]');
      if (row) row.querySelector('.ck').classList.remove('on');
      return paintSel();
    }
    var r = e.target.closest('[data-c]'); if (!r) return;
    var c = r.dataset.c;
    pick.sel[c] = pick.sel[c] ? 0 : 1;
    r.querySelector('.ck').classList.toggle('on', !!pick.sel[c]);
    paintSel();
  };
  document.getElementById('p2next').onclick = async function () {
    var codes = Object.keys(pick.sel).filter(function (k) { return pick.sel[k]; });
    busy(1);
    try {
      d.items = await buildItems(codes.map(function (c) { return { item_code: c, qty: pick.sl[c] }; }), d.items);
      go(scrStep3);
    } catch (err) { toast(errMsg(err)); } finally { busy(0); }
  };
}

/* ---------- 8b. Goi y so tu he thong (v285) ----------

Anh Viet 23/08/2026: Loan Anh lap phieu YCSX ma khong co goi y so nao tu he.
Ba nguon so nam san trong he ma khong ai noi chung lai: kiem banh theo ngay,
kiem banh theo mua, va hop dong da len voi khach.

May chu chot so (may chu la noi duy nhat biet du ba nguon), man hinh chi bay
ra cho nguoi doc va sua. So goi y luon SUA DUOC: goi y sai mot lan ma khong
sua duoc thi lan sau khong ai bam nua.
*/
function goiYDong(x, i) {
  var ng = (x.nguon || []).map(function (n) {
    return '<div style="color:#8a8f9c;font-size:12px;margin-top:3px;line-height:1.45">' +
      '<b style="color:#5a6070;font-weight:600">' + h(n.nhan || '') + '</b>' +
      (n.so ? ' &middot; ' + n.so : '') +
      (n.giai_thich ? '<br>' + h(n.giai_thich) : '') + '</div>';
  }).join('');
  return '<div class="shi" style="align-items:flex-start;padding-top:12px;padding-bottom:12px" data-gi="' + i + '">' +
    '<div class="ck' + (x._on ? ' on' : '') + '" data-gt="' + i + '" style="flex:none;margin-top:2px">&#10003;</div>' +
    '<span style="flex:1;min-width:0">' + h(x.ten_banh || x.ma_hang) +
    '<div style="color:#a0a6b4;font-size:12px;margin-top:2px">Mã: ' + h(x.ma_hang) + '</div>' + ng + '</span>' +
    '<input class="nt" type="number" min="1" inputmode="numeric" data-gq="' + i + '" value="' + (x._sl || x.can) +
    '" style="height:44px;width:74px;flex:none;text-align:center;padding:0 6px">' +
    '</div>';
}
async function goiYSheet() {
  var d = S.draft;
  var kq = null;
  busy(1);
  try { kq = await api('vagabond.goi_y_ycsx.goi_y', { ngay: d.schedule_date }); }
  catch (e) { busy(0); return toast(errMsg(e), 4600); }
  busy(0);
  var ds = (kq && kq.dong) || [];
  var km = (kq && kq.khong_ma) || [];
  var gc = (kq && kq.ghi_chu) || [];
  if (!ds.length && !km.length) {
    return toast('Ngày ' + dmy(d.schedule_date) + ' hệ thống chưa thấy món nào thiếu' +
      (gc.length ? '. ' + gc[0] : ''), 5200);
  }
  ds.forEach(function (x) { x._on = 1; x._sl = x.can; });

  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>Gợi ý cho ngày ' + h(dmy(d.schedule_date)) + '</b><div class="x">&times;</div></div>' +
    '<div style="padding:0 14px 8px;color:#a0a6b4;font-size:12.5px;line-height:1.5">' +
    'Số lấy từ đơn đã đặt, đã trừ tồn và phần bếp đã lên. Sửa được trước khi thêm vào phiếu.</div>' +
    (gc.length ? '<div style="margin:0 14px 10px;padding:11px 13px;border-radius:12px;background:#fff6e5;color:#8a5b00;font-size:12.5px;line-height:1.5">' +
      gc.map(function (c) { return h(c); }).join('<br>') + '</div>' : '') +
    '<div class="shl" id="gyl"></div>' +
    (km.length ? '<div style="padding:4px 14px 0"><div class="selh">Món không có mã hàng (' + km.length + ')</div>' +
      '<div style="padding:10px 13px;border-radius:12px;background:#f4f5f7;color:#5a6070;font-size:12.5px;line-height:1.6">' +
      'Phiếu YCSX bắt buộc mỗi dòng một mã hàng, nên mấy món này máy không tự thêm được. ' +
      'Mở mã hàng cho món rồi thêm, hoặc ghi vào ô Ghi chú của phiếu.<br><br>' +
      km.map(function (k) {
        return '&bull; <b>' + h(k.ten_mon) + '</b> &times; ' + h(String(k.so_luong)) + ' ' + h(k.dvt || '') +
          '<br><span style="color:#a0a6b4">' + h(k.nhan || '') + (k.trang_thai ? ' &middot; ' + h(k.trang_thai) : '') + '</span>';
      }).join('<br>') + '</div></div>' : '') +
    '<div style="padding:12px 14px calc(env(safe-area-inset-bottom,0px) + 14px)">' +
    '<button class="btn" id="gyok"' + (ds.length ? '' : ' disabled') + '>Thêm vào phiếu</button></div>';
  var lst = box.querySelector('#gyl');
  function ve() {
    lst.innerHTML = ds.length ? ds.map(goiYDong).join('') :
      '<div class="emp"><div class="e2">Không có món nào thiếu</div></div>';
    var b = document.getElementById('gyok');
    var n = ds.filter(function (x) { return x._on; }).length;
    if (b) { b.disabled = !n; b.textContent = n ? 'Thêm ' + n + ' món vào phiếu' : 'Chưa chọn món nào'; }
  }
  ve();
  ov.appendChild(box); document.body.appendChild(ov);
  function dong() { ov.remove(); }
  ov.onclick = function (e) { if (e.target === ov) dong(); };
  box.querySelector('.x').onclick = dong;
  lst.onclick = function (e) {
    var t = e.target.closest('[data-gt]'); if (!t) return;
    var x = ds[+t.dataset.gt]; x._on = x._on ? 0 : 1;
    t.classList.toggle('on', !!x._on); ve();
  };
  lst.oninput = function (e) {
    var q = e.target.closest('[data-gq]'); if (!q) return;
    var x = ds[+q.dataset.gq];
    var v = parseInt(q.value, 10);
    x._sl = (v > 0) ? v : 0;
    if (!x._on && x._sl > 0) { x._on = 1; ve(); }
  };
  document.getElementById('gyok').onclick = function () {
    var them = 0;
    ds.forEach(function (x) {
      if (!x._on || !(x._sl > 0)) return;
      pick.sel[x.ma_hang] = 1;
      pick.sl[x.ma_hang] = x._sl;
      if (x.ten_banh) pick.nm[x.ma_hang] = x.ten_banh;
      them++;
    });
    dong();
    if (!them) return toast('Chưa chọn món nào');
    drawPick(false);
    toast('Đã thêm ' + them + ' món từ gợi ý, số lượng điền sẵn ở bước sau');
  };
}

/* ---------- 9. Buoc 3: danh sach da chon ---------- */
function qdText(it) {
  return (it.uom === it.stock_uom || !(it.cf > 0) || it.cf === 1)
    ? '1 ' + it.uom + ' (gốc)'
    : '1 ' + it.uom + ' = ' + num(it.cf) + ' ' + it.stock_uom;
}
function setQty(b, i, v) {
  var el = b.querySelector('[data-q="' + i + '"]');
  if (el) el.value = v;
}
function scrStep3() {
  var d = S.draft, T = d.T;
  var rows = d.items.map(function (it, i) {
    var uomSel = '<select class="uom" data-u="' + i + '">' + (it.uoms || [{ uom: it.stock_uom, cf: 1 }]).map(function (u) {
      return '<option value="' + h(u.uom) + '"' + (u.uom === it.uom ? ' selected' : '') + '>' + h(u.uom) + '</option>';
    }).join('') + '</select>';
    var img = it.image ? '<img class="im3" src="' + h(it.image) + '" alt="">' : '<div class="im3 im3p">🍰</div>';
    var qd = h(qdText(it));
    return '<div class="ic1">' +
      '<div class="ih"><div class="n">' + (i + 1) + '</div>' + img +
      '<div class="in">' + h(it.item_name) + '<div class="ig">Mã: ' + h(it.item_code) + '</div></div>' +
      '<div class="del" data-x="' + i + '" title="Xoá món này">&times;</div></div>' +
      '<div class="stk"><div><div class="s1">Tồn kho tổng 307</div><div class="s2">' + num(it.ton) + ' ' + h(it.stock_uom) + '</div></div>' +
      '<div><div class="s1">Quy đổi</div><div class="s2">' + qd + '</div></div></div>' +
      '<div class="qw"><div style="flex:1;min-width:0"><div class="lb">Số lượng đặt</div>' +
      '<div class="qr"><div class="stp"><button data-m="' + i + '">&minus;</button>' +
      '<input type="number" inputmode="decimal" data-q="' + i + '" value="' + it.qty + '"><button data-p="' + i + '">+</button></div>' + uomSel + '</div></div></div>' +
      (T.hasTime ?
        '<div class="tw"><div class="lb">' + h(T.timeLabel) + '</div>' +
        '<input type="time" class="tin" data-t="' + i + '" value="' + h(hm(it.time)) + '" step="60">' +
        '<div class="tch">' + TIMES.map(function (t) { return '<span data-tc="' + i + '_' + t + '"' + (t === hm(it.time) ? ' class="on"' : '') + '>' + t + '</span>'; }).join('') + '</div></div>'
        : '') +
      '<div class="tw"><textarea class="nt" rows="2" data-n="' + i + '" placeholder="Ghi chú cho món này...">' + h(it.note) + '</textarea></div>' +
      '</div>';
  }).join('');
  var b = frame('Danh sách đã chọn', (d.items.length ? rows : '<div class="emp"><div class="e1">🧺</div><div class="e2">Chưa chọn món nào</div></div>') +
    '<button class="btn gh" id="s3add" style="margin-top:4px">+ Thêm hàng hoá</button>' +
    (d.items.length ? '<button class="btn gh" id="s3tpl" style="margin-top:9px">💾 Lưu danh sách này thành mẫu</button>' : ''),
    { footer: '<button class="btn" id="s3next"' + (d.items.length ? '' : ' disabled') + '>Tiếp tục</button>' });

  b.addEventListener('input', function (e) {
    var t = e.target;
    if (t.dataset.q != null) { d.items[+t.dataset.q].qty = parseFloat(t.value) || 0; }
    if (t.dataset.n != null) { d.items[+t.dataset.n].note = t.value; }
    if (t.dataset.t != null) { var i = +t.dataset.t; var tv = hm(t.value); d.items[i].time = tv; syncChips(b, i, tv); }
  });
  b.addEventListener('change', function (e) {
    var t = e.target;
    if (t.dataset.u != null) {
      var i = +t.dataset.u, it = d.items[i];
      it.uom = t.value;
      var u = (it.uoms || []).filter(function (x) { return x.uom === t.value; })[0];
      it.cf = u ? u.cf : 1;
      var card = t.closest('.ic1');
      var cell = card ? card.querySelectorAll('.stk .s2')[1] : null;
      if (cell) { cell.textContent = qdText(it); } else { scrStep3(); }
    }
  });
  b.addEventListener('click', function (e) {
    var t = e.target.closest('[data-x],[data-m],[data-p],[data-tc]'); if (!t) return;
    if (t.dataset.x != null) {
      var sc = b.scrollTop;
      d.items.splice(+t.dataset.x, 1);
      scrStep3();
      var nb = document.getElementById('vgbBody');
      if (nb) nb.scrollTop = sc;
      return;
    }
    if (t.dataset.m != null) { var i = +t.dataset.m; d.items[i].qty = Math.max(0, Math.round((d.items[i].qty - 1) * 1000) / 1000); return setQty(b, i, d.items[i].qty); }
    if (t.dataset.p != null) { var j = +t.dataset.p; d.items[j].qty = Math.round((d.items[j].qty + 1) * 1000) / 1000; return setQty(b, j, d.items[j].qty); }
    if (t.dataset.tc != null) {
      var p = t.dataset.tc.split('_'); var k = +p[0];
      d.items[k].time = p[1];
      b.querySelector('[data-t="' + k + '"]').value = p[1];
      syncChips(b, k, p[1]);
    }
  });
  document.getElementById('s3add').onclick = function () { go(scrStep2, true); };
  var s3t = document.getElementById('s3tpl');
  if (s3t) s3t.onclick = async function () {
    var nm = await promptSheet('Tên mẫu đơn hàng', 'VD: Đơn NVL hàng tuần - Bếp Baker');
    if (!nm) return;
    var noiDung = JSON.stringify(d.items.map(function (it) {
      return { item_code: it.item_code, qty: it.qty, uom: it.uom, note: it.note || '', time: it.time };
    }));
    busy(1);
    try {
      /* trung ten voi mau cu cung loai phieu thi hoi ghi de, do la cach SUA noi dung mau */
      var cu = await getList('VGB Order Template', { fields: ['name'], filters: { template_name: nm, request_type: d.type }, limit_page_length: 1 });
      if (cu.length) {
        busy(0);
        var ghiDe = await confirmSheet('Đã có mẫu tên "' + nm + '"', 'Ghi đè mẫu cũ bằng danh sách món hiện tại? Mẫu dùng chung cả tiệm.', 'Ghi đè mẫu cũ');
        if (!ghiDe) return;
        busy(1);
        await api('frappe.client.set_value', { doctype: 'VGB Order Template', name: cu[0].name, fieldname: { items_json: noiDung, bo_phan: shortDep(d.bo_phan) || '' } });
        toast('Đã cập nhật mẫu "' + nm + '"', 3200);
      } else {
        await api('frappe.client.insert', {
          doc: {
            doctype: 'VGB Order Template', template_name: nm, request_type: d.type,
            bo_phan: shortDep(d.bo_phan) || undefined, dung_chung: 1,
            items_json: noiDung
          }
        });
        toast('Đã lưu mẫu "' + nm + '"', 3200);
      }
    } catch (err) { toast(errMsg(err), 4200); } finally { busy(0); }
  };
  document.getElementById('s3next').onclick = function () {
    if (d.items.some(function (it) { return !(it.qty > 0); })) return toast('Có món chưa nhập số lượng');
    go(scrStep4);
  };
}
function syncChips(b, i, v) {
  b.querySelectorAll('[data-tc^="' + i + '_"]').forEach(function (s) { s.classList.toggle('on', s.dataset.tc === i + '_' + v); });
}

/* ---------- 10. Buoc 4: xem lai va luu ---------- */
function scrStep4() {
  var d = S.draft, T = d.T;
  var times = {};
  d.items.forEach(function (it) { var k = hm(it.time); times[k] = (times[k] || 0) + 1; });
  var tSum = Object.keys(times).sort().map(function (t) { return t + ' (' + times[t] + ')'; }).join(', ');
  var lines = d.items.map(function (it, i) {
    return '<div class="kv"><span style="flex:1;color:#16181d;text-align:left">' + (i + 1) + '. ' + h(it.item_name) + '</span>' +
      '<b style="flex:0 0 auto">' + num(it.qty) + ' ' + h(it.uom) + (T.hasTime ? ' &middot; ' + h(hm(it.time)) : '') + '</b></div>';
  }).join('');
  var photos = d.photos.map(function (p, i) { return '<img src="' + p.url + '" data-rm="' + i + '">'; }).join('');
  var html = '<div class="card">' +
    '<div class="kv"><span>Loại phiếu</span><b>' + h(T.title) + '</b></div>' +
    (d.set_from_warehouse ? '<div class="kv"><span>Kho xuất</span><b>' + h(shortWh(d.set_from_warehouse)) + '</b></div>' : '') +
    '<div class="kv"><span>Kho nhận</span><b>' + h(shortWh(d.set_warehouse)) + '</b></div>' +
    '<div class="kv"><span>Ngày cần</span><b>' + dmy(d.schedule_date) + '</b></div>' +
    (T.hasTime ? '<div class="kv"><span>' + h(T.timeLabel) + '</span><b>' + h(tSum) + '</b></div>' : '') +
    '<div class="kv"><span>Bộ phận yêu cầu</span><b>' + h(shortDep(d.bo_phan)) + '</b></div>' +
    '<div class="kv"><span>Người yêu cầu</span><b>' + h(d.nguoi_yeu_cau) + '</b></div>' +
    '</div>' +
    '<div class="sec">' + d.items.length + ' hàng hoá</div><div class="card">' + lines + '</div>' +
    '<div class="sec">Ghi chú chung</div><div class="card"><div style="padding:12px 14px">' +
    '<textarea class="nt" id="s4note" rows="3" placeholder="Ghi chú cho cả phiếu...">' + h(d.note) + '</textarea></div>' +
    '<div class="att">' + photos + '<div class="ph" id="s4cam"><div style="font-size:22px">📷</div>Thêm ảnh</div></div></div>' +
    '<input type="file" accept="image/*" id="s4file" style="display:none">';
  var b = frame('Xem lại phiếu', html, {
    footer: '<div class="row2"><button class="btn gh" id="s4save">Lưu nháp</button><button class="btn" id="s4send">Lưu và gửi</button></div>'
  });
  var fi = document.getElementById('s4file');
  document.getElementById('s4cam').onclick = function () { fi.click(); };
  fi.onchange = function () { if (fi.files[0]) addPhoto(fi.files[0]); };
  b.onclick = function (e) {
    var r = e.target.closest('[data-rm]');
    if (r) { d.photos.splice(+r.dataset.rm, 1); scrStep4(); }
  };
  document.getElementById('s4save').onclick = function () { d.note = document.getElementById('s4note').value; saveDraft(0); };
  document.getElementById('s4send').onclick = function () { d.note = document.getElementById('s4note').value; saveDraft(1); };
}

function addPhoto(file) {
  var fr = new FileReader();
  fr.onload = function () {
    var img = new Image();
    img.onload = function () {
      var mx = 1280, w = img.width, ht = img.height;
      if (w > mx || ht > mx) { var s = mx / Math.max(w, ht); w = Math.round(w * s); ht = Math.round(ht * s); }
      var cv = document.createElement('canvas'); cv.width = w; cv.height = ht;
      cv.getContext('2d').drawImage(img, 0, 0, w, ht);
      var url = cv.toDataURL('image/jpeg', 0.72);
      S.draft.photos.push({ url: url, b64: url.split(',')[1], name: 'anh-' + (S.draft.photos.length + 1) + '.jpg' });
      scrStep4();
    };
    img.src = fr.result;
  };
  fr.readAsDataURL(file);
}

async function saveDraft(submitIt) {
  var d = S.draft, T = d.T;
  busy(1);
  try {
    var doc = {
      doctype: 'Material Request', naming_series: 'MAT-MR-.YYYY.-', company: COMPANY,
      material_request_type: T.key, transaction_date: today(), schedule_date: d.schedule_date,
      set_warehouse: d.set_warehouse || undefined,
      set_from_warehouse: d.set_from_warehouse || undefined,
      bo_phan_yeu_cau: shortDep(d.bo_phan) || undefined,
      nguoi_yeu_cau: d.nguoi_yeu_cau || undefined,
      custom_bep_nhan: (T.key === 'Manufacture' ? d.bep_nhan : '') || undefined,
      items: d.items.map(function (it) {
        return {
          doctype: 'Material Request Item', item_code: it.item_code, item_name: it.item_name,
          qty: it.qty, uom: it.uom, stock_uom: it.stock_uom, conversion_factor: it.cf || 1,
          schedule_date: d.schedule_date,
          gio_can_lay: T.hasTime ? (hm(it.time) + ':00') : undefined,
          warehouse: d.set_warehouse || undefined,
          from_warehouse: d.set_from_warehouse || undefined,
          description: (it.note ? it.item_name + ' - ' + it.note : it.item_name)
        };
      })
    };
    var saved = await api('frappe.client.insert', { doc: doc });
    if (d.note) {
      try { await api('frappe.desk.form.utils.add_comment', { reference_doctype: 'Material Request', reference_name: saved.name, content: d.note, comment_email: S.user, comment_by: S.user }); } catch (e) { }
    }
    for (var i = 0; i < d.photos.length; i++) {
      try {
        await api('frappe.client.insert', {
          doc: {
            doctype: 'File', file_name: saved.name + '-' + d.photos[i].name, is_private: 0,
            attached_to_doctype: 'Material Request', attached_to_name: saved.name,
            content: d.photos[i].b64, decode: 1
          }
        });
      } catch (e) { }
    }
    if (submitIt) {
      var full = await api('frappe.client.get', { doctype: 'Material Request', name: saved.name });
      await api('frappe.client.submit', { doc: full });
    }
    busy(0);
    toast('Đã lưu phiếu ' + saved.name, 3200);
    S.draft = null;
    reset(scrHome);
    go(function () { scrMRList(T); });
  } catch (err) { busy(0); toast(errMsg(err), 4200); }
}

/* ---------- 11. Duyet phieu chi ---------- */
var PAYFLOW = [
  { state: 'Nháp', action: 'Gửi kiểm tra', next: 'Chờ FIN kiểm tra', role: 'AP Officer', ok: 1 },
  { state: 'Chờ FIN kiểm tra', action: 'Xác nhận hợp lệ', next: 'Chờ giám đốc duyệt', role: 'AP Kiểm soát (FIN)', ok: 1 },
  { state: 'Chờ FIN kiểm tra', action: 'Trả lại', next: 'Bị trả lại', role: 'AP Kiểm soát (FIN)', ok: 0 },
  /* Giam doc ky thi phieu sang buoc CHO CHUYEN TIEN, khong ghi so.
     Anh Viet 03/09/2026: *"giam doc duyet la moi duyet chi thoi, ke toan
     chi tien roi dinh kem UNC, khop giao dich SePay vao thi moi ghi so"*. */
  { state: 'Chờ giám đốc duyệt', action: 'Duyệt chi', next: 'Đã duyệt chi - chờ chuyển tiền', role: 'AP Giám đốc', ok: 1 },
  { state: 'Chờ giám đốc duyệt', action: 'Trả lại', next: 'Bị trả lại', role: 'AP Giám đốc', ok: 0 },
  /* Buoc nay KHONG di qua apply_workflow: no phai qua cua rieng de soat uy
     nhiem chi va giao dich ngan hang truoc khi ghi so. Xem pvXacNhan. */
  { state: 'Đã duyệt chi - chờ chuyển tiền', action: 'Xác nhận đã chuyển tiền', next: 'Đã duyệt - Đã ghi sổ', role: 'AP Kiểm soát (FIN)', ok: 1, cua_rieng: 1 },
  { state: 'Đã duyệt chi - chờ chuyển tiền', action: 'Trả lại', next: 'Bị trả lại', role: 'AP Kiểm soát (FIN)', ok: 0 },
  { state: 'Bị trả lại', action: 'Gửi kiểm tra', next: 'Chờ FIN kiểm tra', role: 'AP Officer', ok: 1 }
];

/* Nhan doc tren man. O trang thai giu ten cu de phieu cu khong mo coi, con
   chu hien ra thi noi dung nghia moi. */
var PAYNHAN = {
  'Nháp': 'Nháp',
  'Chờ FIN kiểm tra': 'Chờ kế toán kiểm tra',
  'Chờ giám đốc duyệt': 'Chờ giám đốc duyệt chi',
  'Đã duyệt chi - chờ chuyển tiền': 'Đã duyệt chi, chờ chuyển tiền',
  'Đã duyệt - Đã ghi sổ': 'Đã chuyển tiền, đã ghi sổ',
  'Bị trả lại': 'Bị trả lại'
};
function payNhan(s) { return PAYNHAN[s] || s || ''; }
function myPayStates() {
  var s = [];
  PAYFLOW.forEach(function (t) { if (hasRole(t.role) && s.indexOf(t.state) < 0) s.push(t.state); });
  return s.length ? s : ['__none__'];
}
function myPayRoleLabel() {
  if (hasRole('AP Giám đốc')) return 'Giám đốc duyệt chi';
  if (hasRole('AP Kiểm soát (FIN)')) return 'Kiểm soát tài chính';
  return 'Lập và gửi phiếu chi';
}
var payTab = '';
async function scrPayList() {
  frame('Duyệt phiếu chi', '<div class="emp"><div class="e1">⏳</div></div>');
  var mine = myPayStates();
  /* CHI phieu CHI, tuc payment_type = "Pay".

     Anh Viet 22/08/2026: *"sao tu nhien lai co ca HDM cua khach le online
     the nhi"*. Vi sao lot vao: luong duyet dat tren CA doctype Payment
     Entry, nen Frappe gan trang thai "Nhap" cho MOI phieu tien moi, ke ca
     phieu THU tien khach do may tu tao khi doi soat sao ke. O `custom_loai_chi`
     khong phan biet duoc vi no co gia tri mac dinh, phieu thu cung mang
     "Thanh toan cong no NCC".

     Loc theo `payment_type` la cach chac nhat: phieu thu tien khach khong
     phai phieu chi, khong bao gio duoc xuat hien o man nay. */
  var docs = await getList('Payment Entry', {
    fields: ['name', 'posting_date', 'party_name', 'party', 'party_type', 'paid_amount', 'workflow_state', 'mode_of_payment', 'custom_loai_chi', 'remarks', 'owner'],
    filters: { payment_type: 'Pay', workflow_state: ['in', mine] }, limit_page_length: 60, order_by: 'posting_date desc, name desc'
  });
  /* LOC THEM MOT TANG: phieu tra tien cho KHACH khong thuoc man nay.

     Loc `payment_type = "Pay"` o tren da duoi duoc phieu THU tien khach ra,
     nhung con mot loai nua lot qua: phieu HOAN tien cho khach. No cung la
     tien di ra nen cung mang "Pay", chi khac o cho ben nhan la Customer chu
     khong phai Supplier. Ngay 03/09/2026 tab "Nháp" dang giu hai to nhu vay,
     APP-26-08-413 va APP-26-08-388, ca hai deu neo vao hoa don ban.

     Chung khong bien mat: luong hoan tien khach co man rieng. O day chi go
     chung ra khoi hang doi duyet chi cho nha cung cap, va noi ro con bao
     nhieu to nam nham cho de con biet duong di don.
     Loc tren may chu khong loc o may chu: `party_type != Customer` trong SQL
     se an luon nhung phieu bo trong o do, ma phieu chi noi bo thi hay bo
     trong that. */
  var lac = docs.filter(function (d) { return (d.party_type || '') === 'Customer'; });
  docs = docs.filter(function (d) { return (d.party_type || '') !== 'Customer'; });
  var done = await getList('Payment Entry', {
    fields: ['name', 'posting_date', 'party_name', 'paid_amount', 'workflow_state'],
    filters: { payment_type: 'Pay', workflow_state: ['in', ['Đã duyệt - Đã ghi sổ', 'Bị trả lại']] }, limit_page_length: 25, order_by: 'modified desc'
  });
  /* TAB "TÔI LẬP": phieu cua chinh minh, dang o bat ky buoc nao.

     Man nay chia tab theo VAI: moi tab la mot buoc, va chi ai co vai xu ly
     buoc do moi thay tab do. Rat gon cho nguoi duyet, nhung nguoi LAP thi
     mat dau phieu ngay sau khi gui: AP Officer chi co hai tab "Nháp" va
     "Bị trả lại", nen phieu vua chuyen sang "Chờ FIN kiểm tra" la bien khoi
     man hinh cua ho, khong con cho nao trong app xem lai duoc.

     Uyen 03/09/2026 bao dung canh nay voi phieu tra truoc: lap xong thi ben
     app khong hien len, tren desktop thi co. Chip "Trả trước NCC" ben man Ho
     so thanh toan lo cho phieu tra truoc; tab nay lo cho moi phieu chi khac.

     Tab chi bay ra khi nguoi do THAT SU co phieu dang treo. */
  var cuaToi = [];
  try {
    cuaToi = await getList('Payment Entry', {
      fields: ['name', 'posting_date', 'party_name', 'party', 'party_type', 'paid_amount', 'workflow_state', 'custom_loai_chi'],
      filters: { payment_type: 'Pay', owner: S.user, docstatus: 0 }, limit_page_length: 40, order_by: 'creation desc'
    });
    cuaToi = cuaToi.filter(function (d) { return (d.party_type || '') !== 'Customer'; });
  } catch (e) { cuaToi = []; }
  var TAB_TOI = '📄 Tôi lập';
  if (!payTab) payTab = mine[0] || 'Xong';
  function draw() {
    var tabs = mine.concat(cuaToi.length ? [TAB_TOI] : []).concat(['Đã xử lý']);
    if (tabs.indexOf(payTab) < 0) payTab = tabs[0];
    var chips = tabs.map(function (s) {
      var c = s === 'Đã xử lý' ? done.length
        : (s === TAB_TOI ? cuaToi.length : docs.filter(function (d) { return d.workflow_state === s; }).length);
      return '<div class="chip' + (payTab === s ? ' on' : '') + '" data-s="' + h(s) + '">' + h(s) + ' ' + c + '</div>';
    }).join('');
    var rows = payTab === 'Đã xử lý' ? done
      : (payTab === TAB_TOI ? cuaToi : docs.filter(function (d) { return d.workflow_state === payTab; }));
    var lst = rows.length ? '<div class="lst">' + rows.map(function (d) {
      var cls = d.workflow_state === 'Đã duyệt - Đã ghi sổ' ? 'g' : (d.workflow_state === 'Bị trả lại' ? 'r' : (d.workflow_state === 'Nháp' ? 'w' : 'b'));
      return '<div class="li" data-n="' + h(d.name) + '"><div class="lt">' +
        '<div class="l1">' + h(d.party_name || d.party || d.name) + '</div>' +
        '<div class="l2">' + h(d.name) + ' &middot; ' + dmy(d.posting_date) + (d.custom_loai_chi ? '<br>' + h(d.custom_loai_chi) : '') + '</div></div>' +
        '<div style="text-align:right"><div class="amt">' + money(d.paid_amount) + '</div>' +
        '<span class="st ' + cls + '" style="margin-top:4px">' + h(d.workflow_state) + '</span></div></div>';
    }).join('') + '</div>' : payRong();
    /* Nhac ho so thanh toan NGAY TREN danh sach, khong doi den luc trong.
       Ban cu chi noi khi tab dang mo khong con to nao. Nguoi nao tab con
       mot to le thi khong bao gio thay dong nay, ma ben kia van dang co
       tam bo cho ho. */
    var nhac = (paySoHoSo && rows.length)
      ? '<div class="card" style="padding:10px 12px;background:#fff7ed;border:1.5px solid #fed7aa;font-size:12.5px;color:#9a3412;line-height:1.55">' +
        '🏦 Còn <b>' + paySoHoSo + '</b> hồ sơ thanh toán đang chờ bạn xử lý' +
        (paySoTre ? ', <b>' + paySoTre + '</b> đã quá hạn' : '') + '. ' +
        '<button class="btn gh" data-hstt="1" style="margin:8px 0 0;padding:7px 10px;font-size:12.5px">Mở Hồ sơ thanh toán</button></div>'
      : '';
    var nhacLac = lac.length
      ? '<div class="card" style="padding:10px 12px;background:#f8fafc;border:1px solid #e2e8f0;font-size:12px;color:#64748b;line-height:1.55">' +
        'Có ' + lac.length + ' phiếu hoàn tiền cho khách đang nằm nhầm trong hàng đợi duyệt chi nhà cung cấp. ' +
        'Chúng được ẩn khỏi màn này, xử lý ở màn Hoàn tiền.</div>'
      : '';
    var b = frame('Duyệt phiếu chi', '<div class="chips">' + chips + '</div>' + nhac + lst + nhacLac);
    b.onclick = function (e) {
      var c = e.target.closest('[data-s]'); if (c) { payTab = c.dataset.s; return draw(); }
      if (e.target.closest('[data-hstt]')) return vgbGo('APPTT');
      var r = e.target.closest('[data-n]'); if (r) go(function () { scrPayView(r.dataset.n); });
    };
  }
  draw();
  payDoHoSo(draw);
}

/* So ho so thanh toan dang cho CHINH nguoi nay, doc mot lan moi lan mo man. */
var paySoHoSo = 0;

var paySoTre = 0;

async function payDoHoSo(ve) {
  paySoHoSo = 0; paySoTre = 0;
  try {
    var kq = await api('vagabond.viec_can_lam.danh_sach', { loai: 'ho_so_tt' });
    var ds = (kq && kq.ds) || [];
    /* DEM THEO BUOC, KHONG DEM THEO MAU.

       Ban cu dem `tt === 'cho_duyet'`. Ma o `tt` con mang mot nghia thu hai
       la mau bay tren man Viec can lam, va tre han an tren tat ca - ho so
       nao qua han la doi thanh 'tre_hen'. Ket qua: cang de lau cang bi dem
       sot, tuc la dung nguoc voi cai minh muon.

       Chi Dung 03/09/2026 mo man nay thay dau tich xanh "khong co phieu nao
       can xu ly", trong khi ben Ho so thanh toan dang co tam bo cho chi
       chuyen tien, vai bo qua han tu 12/08.

       Danh sach tra ve DA loc theo vai roi, moi dong deu la viec cua chinh
       nguoi nay. Nen dem tat ca, tru ban nhap cua nguoi khac. */
    var cua_toi = ds.filter(function (x) { return (x.buoc || x.tt) !== 'ban_nhap'; });
    paySoHoSo = cua_toi.length;
    paySoTre = cua_toi.filter(function (x) { return x.tt === 'tre_hen'; }).length;
  } catch (e) { return; }
  if (paySoHoSo && ve) ve();
}

/* O RONG cua man Duyet phieu chi.

   Anh Viet 27/08/2026: ke toan gui ba ho so thanh toan len cho giam doc
   duyet, anh mo man nay va thay trong tron, tuong he thong khong dong bo.

   That ra co HAI hang doi tien khac nhau. Man nay doc Payment Entry, tuc
   tung phieu chi le. Con ho so thanh toan APP la mot loai chung tu khac,
   gom nhieu hoa don cua mot nha cung cap vao mot bo, va no nam ben man Ho
   so thanh toan. Hai hang doi, ma chi mot cai mang ten "Duyet phieu chi".

   Nen o rong khong duoc noi trong khong. No phai noi ro hang doi kia con
   bao nhieu bo, va bay san duong sang do. */
function payRong() {
  if (paySoHoSo) {
    return '<div class="emp"><div class="e1">🏦</div>' +
      '<div class="e2">Không có phiếu chi lẻ nào ở bước này</div>' +
      '<div style="font-size:13px;color:#8a90a0;margin-top:10px;line-height:1.6;padding:0 18px">' +
      'Nhưng còn <b style="color:#c0392b">' + paySoHoSo + '</b> hồ sơ thanh toán đang chờ bạn xử lý' +
      (paySoTre ? ', trong đó <b style="color:#c0392b">' + paySoTre + '</b> hồ sơ đã quá hạn trả' : '') + '. ' +
      'Hồ sơ thanh toán gom nhiều hoá đơn của một nhà cung cấp vào một bộ, nằm ở màn riêng.</div>' +
      '<button class="btn" data-hstt="1" style="margin:14px 18px 0">Mở Hồ sơ thanh toán</button></div>';
  }
  return '<div class="emp"><div class="e1">✅</div><div class="e2">Không có phiếu nào cần xử lý</div></div>';
}

/* Tinh hinh chuyen tien cua phieu dang mo, de nut xac nhan biet dang thieu
   gi ma noi cho dung. */
var pvTh = null;

/* Ke toan xac nhan da chuyen tien. Di qua cua rieng chu khong qua duong
   workflow chung: cua nay soat uy nhiem chi va giao dich ngan hang truoc
   khi cho phieu ghi so. */
async function pvXacNhan(d, name) {
  var unc = tdkDs('pvunc') || [];
  var th = pvTh || {};
  if (!unc.length && !th.so_unc) {
    return baoTin('Đính tờ uỷ nhiệm chi vào phiếu trước đã. Đó là bằng chứng tiền đã rời tài khoản.',
      'Chưa có uỷ nhiệm chi');
  }
  var lyDo = null;
  if (!th.du_tien) {
    if (!th.duoc_bo_qua_sepay) {
      return baoTin('Chưa thấy giao dịch ngân hàng nào mang mã phiếu này. Chờ ngân hàng đẩy về rồi xác nhận lại. ' +
        'Nếu tiền đã đi thật thì nhờ kế toán trưởng xác nhận.', 'Chưa thấy tiền ra khỏi tài khoản');
    }
    lyDo = await promptSheet('Ngân hàng chưa báo giao dịch',
      'Tiền đã chuyển thật thì ghi một câu lý do, câu này nằm lại trên phiếu để kỳ sau đối chiếu.');
    if (lyDo === null) return;
    if (!lyDo) return toast('Phải ghi lý do thì mới ghi sổ sớm được');
  }
  var ma = await promptSheet('Mã giao dịch ngân hàng', 'Số tham chiếu trên uỷ nhiệm chi. Bỏ trống cũng được.');
  if (ma === null) return;
  if (!await confirmSheet('Xác nhận đã chuyển tiền?',
    'Phiếu ' + name + ' · ' + money(d.paid_amount) + ' đ cho ' + (d.party_name || d.party) +
    '.\n\nXác nhận xong là phiếu ghi sổ, tiền trừ khỏi sổ và công nợ nhà cung cấp giảm.',
    'Đã chuyển tiền')) return;
  busy(1);
  try {
    await api('vagabond.duyet_chi.xac_nhan_da_chuyen', {
      name: name, ma_giao_dich: ma || '', ly_do_som: lyDo || '',
      unc: JSON.stringify(unc.map(function (x) { return x.url; }))
    });
    busy(0);
    tdkNap('pvunc', []);
    toast('Đã ghi sổ phiếu ' + name, 3200);
    back();
  } catch (err) { busy(0); toast(errMsg(err), 6000); }
}

async function scrPayView(name) {
  frame(name, '<div class="emp"><div class="e1">⏳</div></div>');
  var d = await api('frappe.client.get', { doctype: 'Payment Entry', name: name });
  /* Chan ca o man chi tiet: mo bang duong dan cu hoac bang lich su trinh
     duyet thi van khong duoc bay nut duyet chi len mot phieu THU tien. */
  if (d && d.payment_type !== 'Pay') {
    frame(name, '<div class="emp"><div class="e1">🧾</div>' +
      '<div class="e2">Đây là phiếu THU tiền khách, không phải phiếu chi</div>' +
      '<div style="font-size:13px;color:#8a90a0;margin-top:8px;line-height:1.6;padding:0 18px">' +
      'Màn Duyệt phiếu chi chỉ dành cho tiền đi ra. Phiếu thu tiền khách do máy ' +
      'tự tạo khi đối soát sao kê, kế toán xử lý ở màn khác.</div></div>');
    return;
  }
  var files = await getList('File', { fields: ['file_url', 'file_name'], filters: { attached_to_doctype: 'Payment Entry', attached_to_name: name }, limit_page_length: 20 });
  var acts = PAYFLOW.filter(function (t) { return t.state === d.workflow_state && hasRole(t.role); });
  var refs = (d.references || []).map(function (r) {
    return '<div class="kv"><span style="flex:1;text-align:left;color:#16181d">' + h(r.reference_name) + '</span><b>' + money(r.allocated_amount) + '</b></div>';
  }).join('');
  var imgs = files.filter(function (f) { return /\.(jpe?g|png|webp|gif)$/i.test(f.file_url || ''); });
  var docs2 = files.filter(function (f) { return imgs.indexOf(f) < 0; });
  var html = '<div class="card">' +
    '<div style="padding:16px 14px;background:#E4F9FD"><div style="font-size:12.5px;color:#4E7C88;margin-bottom:4px">Số tiền chi</div>' +
    '<div style="font-size:28px;font-weight:800;color:#0B7C93">' + money(d.paid_amount) + ' đ</div></div>' +
    '<div class="kv"><span>Số phiếu</span><b>' + h(d.name) + '</b></div>' +
    '<div class="kv"><span>Ngày</span><b>' + dmy(d.posting_date) + '</b></div>' +
    '<div class="kv"><span>Người nhận</span><b>' + h(d.party_name || d.party || '-') + '</b></div>' +
    (d.custom_loai_chi ? '<div class="kv"><span>Loại chi</span><b>' + h(d.custom_loai_chi) + '</b></div>' : '') +
    '<div class="kv"><span>Hình thức</span><b>' + h(d.mode_of_payment || '-') + '</b></div>' +
    '<div class="kv"><span>Tài khoản chi</span><b>' + h(d.paid_from || '-') + '</b></div>' +
    '<div class="kv"><span>Trạng thái</span><b>' + h(payNhan(d.workflow_state)) + '</b></div>' +
    '<div class="kv"><span>Người lập</span><b>' + h(d.nguoi_lap_ten || d.owner) + '</b></div>' +
    '</div>' +
    (refs ? '<div class="sec">Hoá đơn thanh toán</div><div class="card">' + refs + '</div>' : '') +
    (d.remarks ? '<div class="sec">Diễn giải</div><div class="card"><div style="padding:12px 14px;font-size:14.5px;line-height:1.55;color:#3a404e">' + h(String(d.remarks).replace(/<[^>]*>/g, '')) + '</div></div>' : '') +
    (files.length ? '<div class="sec">Chứng từ đính kèm (' + files.length + ')</div><div class="card"><div class="att">' +
      imgs.map(function (f) { return '<a href="' + h(f.file_url) + '" target="_blank"><img src="' + h(f.file_url) + '"></a>'; }).join('') + '</div>' +
      docs2.map(function (f) { return '<div class="kv"><span style="flex:1;text-align:left">📎 ' + h(f.file_name) + '</span><a href="' + h(f.file_url) + '" target="_blank"><b style="color:#0B7C93">Mở</b></a></div>'; }).join('') +
      '</div>' : '') +
    '<button class="btn gh" id="pvPrint" style="margin-bottom:10px">Xem bản in đầy đủ</button>';

  /* BUOC CHUYEN TIEN. Phieu da co chu ky giam doc, gio la viec cua ke
     toan: chuyen tien that, dinh to uy nhiem chi, doi chieu giao dich ngan
     hang. Man noi ro dang thieu cai nao chu khong de nguoi ta bam roi mo
     doan cau bao loi. */
  var chuyenTien = d.workflow_state === 'Đã duyệt chi - chờ chuyển tiền' && hasRole('AP Kiểm soát (FIN)');
  if (chuyenTien) {
    var th = null;
    try { th = await api('vagabond.duyet_chi.tinh_hinh', { name: name }); } catch (e) { th = null; }
    html += '<div class="sec">Chuyển tiền</div><div class="card" style="padding:13px 14px">' +
      '<div style="font-size:13.5px;color:#3a404e;line-height:1.6">Giám đốc đã duyệt chi. ' +
      'Chuyển tiền xong thì đính tờ uỷ nhiệm chi vào đây, máy dò giao dịch ngân hàng mang mã phiếu, ' +
      'đủ hai thứ thì phiếu mới ghi sổ.</div>' +
      (th ? '<div style="margin-top:10px;display:flex;flex-direction:column;gap:6px;font-size:13.5px">' +
        '<div>' + (th.so_unc ? '✅' : '⬜') + ' Uỷ nhiệm chi: <b>' + (th.so_unc ? th.so_unc + ' tờ' : 'chưa có') + '</b></div>' +
        '<div>' + (th.du_tien ? '✅' : '⬜') + ' Ngân hàng báo đã chi: <b>' + money(th.da_chi) + ' đ</b> trên ' + money(th.tong_tien) + ' đ' +
        (th.ma_gd ? ' · giao dịch ' + h(th.ma_gd) : '') + '</div></div>' : '') +
      '<div id="pvUnc" style="margin-top:12px"></div>' +
      '</div>';
    pvTh = th;
  }

  var ft = acts.map(function (t) {
    return '<button class="btn ' + (t.ok ? 'gr' : 'dg') + '" data-act="' + h(t.action) + '" style="margin-bottom:9px">' + h(t.action) + '</button>';
  }).join('');
  var b = frame(name, html, { footer: ft || '<button class="btn gh" disabled>Không có thao tác cho vai trò của bạn</button>' });
  if (chuyenTien) {
    var khungUnc = document.getElementById('pvUnc');
    if (khungUnc) {
      var oUnc = {
        nhan: '📎 Đính uỷ nhiệm chi',
        goi_y: 'Tải tờ uỷ nhiệm chi từ e-banking về rồi chọn ở đây. Đính đúng tờ uỷ nhiệm chi, đừng đính bảng báo giá.',
        style: 'margin-top:0'
      };
      tdkNap('pvunc', []);
      khungUnc.innerHTML = tdkKhoi('pvunc', oUnc);
      tdkNoi(khungUnc, 'pvunc', oUnc);
    }
  }
  document.getElementById('pvPrint').onclick = function () {
    window.open('/printview?doctype=Payment%20Entry&name=' + encodeURIComponent(name) + '&format=' + encodeURIComponent('Vagabond - Chứng từ thanh toán') + '&no_letterhead=0&_lang=vi', '_blank');
  };
  var f = root.querySelector('.vf');
  if (f) f.onclick = async function (e) {
    var t = e.target.closest('[data-act]'); if (!t) return;
    var action = t.dataset.act;
    var tr = acts.filter(function (x) { return x.action === action; })[0];
    if (tr && tr.cua_rieng) return pvXacNhan(d, name);
    var reason = null;
    if (!tr.ok) {
      reason = await promptSheet('Lý do trả lại', 'Nhập lý do để người lập biết cần sửa gì...');
      if (reason === null) return;
      if (!reason) return toast('Cần nhập lý do trả lại');
    } else {
      var msg = action === 'Duyệt chi'
        ? 'Duyệt chi ' + money(d.paid_amount) + ' đ cho ' + (d.party_name || d.party) + '. Chữ ký và con dấu của anh sẽ được in lên chứng từ.'
        : 'Chuyển phiếu sang bước "' + tr.next + '".';
      if (!await confirmSheet(action + '?', msg, action)) return;
    }
    busy(1);
    try {
      if (reason) {
        await api('frappe.desk.form.utils.add_comment', { reference_doctype: 'Payment Entry', reference_name: name, content: 'Trả lại: ' + reason, comment_email: S.user, comment_by: S.user });
      }
      await api('frappe.model.workflow.apply_workflow', { doc: d, action: action });
      busy(0);
      toast(action === 'Duyệt chi' ? 'Đã duyệt và ký ' + name : 'Đã ' + action.toLowerCase() + ' ' + name, 3200);
      back();
    } catch (err) { busy(0); toast(errMsg(err), 4200); }
  };
}


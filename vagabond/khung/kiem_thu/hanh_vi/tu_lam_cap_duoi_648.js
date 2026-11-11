/* v648 (anh Việt chốt 11/11/2026, phương án C): bếp chỉ bấm Hoàn tất món chính,
 * ruột bánh cấp 1, bánh khuôn cấp 2 còn thiếu tồn thì máy tự tạo và hoàn tất
 * lệnh của chúng theo công thức, trước món chính.
 *
 * CHẠY THẬT các hàm của 05-san-xuat.js (freshOf, mfgFreshPlan, mfgRunFresh)
 * trên một kho giả trong bộ nhớ: lệnh, tồn, công thức, phiếu kho. Máy chủ giả
 * chỉ trả lời câu "món nào máy được tự làm" (vagabond.kho_san_xuat.mon_tu_lam,
 * luật thật có ca Python riêng) và ghi lại thứ tự lệnh, phiếu.
 *
 * Chạy: node vagabond/khung/kiem_thu/hanh_vi/tu_lam_cap_duoi_648.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var SRC = fs.readFileSync(path.join(GOC, 'vagabond', 'public', 'js', 'bep', '05-san-xuat.js'), 'utf8');

function layHam(src, ten) {
  var dau = src.indexOf('function ' + ten + '(');
  if (dau < 0) throw new Error('Khong thay ham ' + ten);
  if (src.slice(Math.max(0, dau - 6), dau) === 'async ') dau -= 6;
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Ham ' + ten + ' khong dong ngoac');
}

var ket = { dat: 0, hong: 0 };
function bang(mo, a, b) {
  var x = JSON.stringify(a), y = JSON.stringify(b);
  if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y);
}

/* Thế giới: TP (bánh ổ) cần 2 bánh khuôn C2; mỗi C2 cần 1 ruột C1 và 100 g NVL;
 * mỗi C1 cần 50 g NVL. TU_LAM là câu trả lời của máy chủ (cấp 1, cấp 2 giữ tồn
 * có công thức); NVL và mặt hàng ảo không bao giờ tự làm. */
function theGioi(ton, tuLam) {
  var BOM = {
    C2: { name: 'BOM-C2', qty: 1, dong: [{ item_code: 'C1', item_name: 'Ruột C1', stock_uom: 'Cái', so: 1 }, { item_code: 'NVL', item_name: 'Bột', stock_uom: 'Gram', so: 100 }] },
    C1: { name: 'BOM-C1', qty: 1, dong: [{ item_code: 'NVL', item_name: 'Bột', stock_uom: 'Gram', so: 50 }] },
    AO: { name: 'BOM-AO', qty: 1, dong: [] }
  };
  var nhat = { lenh: [], phieu: [], hoi: [], giaoTho: [] }, dem = 0, lenh = {};
  var the = {
    console: console, Math: Math, JSON: JSON, Promise: Promise, Object: Object, String: String,
    r3: function (n) { return Math.round(n * 1000) / 1000; },
    mfg: { src: 'Pastry - Nguyên liệu - TV' },
    today: function () { return '2026-11-11'; },
    nowStamp: function () { return '2026-11-11 10:00:00'; },
    api: async function (m, a) {
      if (m === 'vagabond.kho_san_xuat.mon_tu_lam') {
        nhat.hoi.push(JSON.parse(a.ma));
        return JSON.parse(a.ma).filter(function (c) { return tuLam.indexOf(c) >= 0; });
      }
      if (m === 'frappe.client.get') {
        var w = lenh[a.name];
        var b = BOM[w.code];
        return { name: a.name, source_warehouse: w.src, required_items: b.dong.map(function (d) {
          return { item_code: d.item_code, item_name: d.item_name, stock_uom: d.stock_uom, required_qty: d.so * w.qty };
        }) };
      }
      if (m === 'erpnext.manufacturing.doctype.work_order.work_order.make_stock_entry') {
        return { work_order: a.work_order_id, qty: a.qty, items: [{ is_finished_item: 1 }] };
      }
      if (m === 'vagabond.kho_san_xuat.hoan_tat_phieu') {
        /* Codex #551: lenh con ghi so qua cung cua voi mon chinh (gio may chu). */
        var w2 = lenh[a.phieu.work_order];
        if (a.q !== a.can || a.q !== a.phieu.qty) throw new Error('so lam lech: ' + JSON.stringify([a.q, a.can, a.phieu.qty]));
        nhat.phieu.push(w2.code + ' x' + a.q);
        ton[w2.code] = (ton[w2.code] || 0) + a.q;
        return { name: 'SE-' + nhat.phieu.length };
      }
      if (m === 'frappe.client.insert' || m === 'frappe.client.submit') {
        nhat.giaoTho.push(m);
        return a.doc;
      }
      throw new Error('api la: ' + m);
    },
    bomOf: async function (ds) { var r = {}; ds.forEach(function (c) { if (BOM[c]) r[c] = { name: BOM[c].name }; }); return r; },
    stockOf: async function (ds) { var r = {}; ds.forEach(function (c) { r[c] = ton[c] || 0; }); return r; },
    mfgCreateWO: async function (f) {
      var ten = 'WO-' + (++dem);
      lenh[ten] = { code: f.code, qty: f.qty, src: f.src };
      nhat.lenh.push(f.code + ' x' + f.qty);
      return ten;
    },
    num: function (n) { var v = Math.round((n || 0) * 1000) / 1000; return v.toLocaleString('vi-VN'); },
    getList: async function (dt, o) {
      if (dt === 'BOM') return Object.keys(BOM).filter(function (c) { return o.filters.name[1].indexOf(BOM[c].name) >= 0; })
        .map(function (c) { return { name: BOM[c].name, quantity: BOM[c].qty }; });
      if (dt === 'BOM Item') {
        var ra = [];
        Object.keys(BOM).forEach(function (c) {
          if (o.filters.parent[1].indexOf(BOM[c].name) < 0) return;
          BOM[c].dong.forEach(function (d) { ra.push({ parent: BOM[c].name, item_code: d.item_code, item_name: d.item_name, stock_qty: d.so, stock_uom: d.stock_uom }); });
        });
        return ra;
      }
      throw new Error('getList la: ' + dt);
    },
    mfgLoadItem: async function () { return {}; },
    mfgMakeBatch: async function () { return ''; }
  };
  vm.createContext(the);
  ['inChunks', 'freshOf', 'mfgFreshPlan', 'mfgRunFresh', 'mfgNvlCuaKe', 'mfgChipNvl'].forEach(function (t) {
    vm.runInContext(layHam(SRC, t), the);
  });
  the.nhat = nhat;
  return the;
}

/* Lệnh món chính: 2 bánh ổ cần 2 C2 và 30 g NVL rắc mặt. */
var MATS = [
  { item_code: 'C2', item_name: 'Bánh khuôn C2', stock_uom: 'Cái', required_qty: 2 },
  { item_code: 'NVL', item_name: 'Bột', stock_uom: 'Gram', required_qty: 30 },
  { item_code: 'AO', item_name: 'Kem ảo', stock_uom: 'Gram', required_qty: 10 }
];

async function ca(ten, fn) {
  try { await fn(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); }
}

(async function () {
  await ca('1. cap 2, cap 1 deu het ton: may lam C1 truoc, C2 sau, du so; NVL va mat hang ao khong bao gio tu lam', async function () {
    var t = theGioi({}, ['C1', 'C2']);
    var ke = await t.mfgFreshPlan(MATS, 1, t.mfg.src);
    bang('ke hoach', ke.map(function (f) { return f.code + ' x' + f.qty; }), ['C2 x2']);
    await t.mfgRunFresh(ke, 1);
    bang('lenh tao theo thu tu', t.nhat.lenh, ['C2 x2', 'C1 x2']);
    bang('phieu ghi so: C1 truoc C2', t.nhat.phieu, ['C1 x2', 'C2 x2']);
    bang('may chu duoc hoi dung cac ma cua lenh', t.nhat.hoi[0], ['C2', 'NVL', 'AO']);
    bang('lenh con khong tu dat gio dien thoai, khong ghi so rieng', t.nhat.giaoTho, []);
  });

  await ca('2. ruot C1 lam san hom truoc con 1: may chi lam phan thieu (1), dung ton cho phan con lai', async function () {
    var t = theGioi({ C1: 1 }, ['C1', 'C2']);
    var ke = await t.mfgFreshPlan(MATS, 1, t.mfg.src);
    await t.mfgRunFresh(ke, 1);
    bang('chi lam 1 C1', t.nhat.lenh, ['C2 x2', 'C1 x1']);
  });

  await ca('3. banh khuon C2 du ton: khong tao lenh nao, hoan tat mon chinh nhu cu', async function () {
    var t = theGioi({ C2: 3 }, ['C1', 'C2']);
    var ke = await t.mfgFreshPlan(MATS, 1, t.mfg.src);
    bang('khong ke hoach', ke, []);
  });

  await ca('4. may chu khong cho tu lam (truoc v648, ma khong giu ton): giu dung luat cu, khong tao lenh', async function () {
    var t = theGioi({}, []);
    var ke = await t.mfgFreshPlan(MATS, 1, t.mfg.src);
    bang('khong ke hoach', ke, []);
  });

  await ca('5. hoan tat mot phan (1 trong 2 banh): may tinh theo ty le so lam', async function () {
    var t = theGioi({}, ['C1', 'C2']);
    var ke = await t.mfgFreshPlan(MATS, 0.5, t.mfg.src);
    bang('ke hoach', ke.map(function (f) { return f.code + ' x' + f.qty; }), ['C2 x1']);
    bang('nhap ve kho nguyen lieu cua bep', [ke[0].fg, ke[0].src], [t.mfg.src, t.mfg.src]);
  });

  await ca('6. hop xac nhan: ruot C1 thieu ma may tu lam ghi "may lam them", khong do; NVL thieu that van do va dung dau', async function () {
    var t = theGioi({ C1: 1 }, ['C1', 'C2']);
    var ke = await t.mfgFreshPlan(MATS, 1, t.mfg.src);
    var nvl = await t.mfgNvlCuaKe(ke, t.mfg.src);
    var chip = nvl.map(function (x) { var c = t.mfgChipNvl(x); return [x.code, c.phu, c.bad]; });
    bang('chip theo thu tu: thieu that len dau', chip, [['NVL', '200 · thiếu 200', true], ['C1', '2 · máy làm thêm 1', false]]);
  });

  console.log('\n' + ket.dat + ' dat, ' + ket.hong + ' hong');
  process.exit(ket.hong ? 1 : 0);
})();

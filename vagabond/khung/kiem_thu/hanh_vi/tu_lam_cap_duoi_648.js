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
function theGioi(ton, tuLam, tong) {
  tong = tong || {};
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
      if (m === 'vagabond.kho_san_xuat.hoan_tat_phieu' && a.phieu.work_order === 'WO-CHA') {
        /* Lệnh món chính (ca 14): máy chủ giả chỉ trả lời đúng luật hỏi/lấy bù. */
        nhat.cha = (nhat.cha || []).concat([{ lay_bu: a.lay_bu, hoi_lay_bu: a.hoi_lay_bu }]);
        if (a.hoi_lay_bu && !a.lay_bu) return { ok: 0, hoi_lay_bu: [{ ma: 'NVL', ten: 'Bột', sl: 60, dvt: 'Gram', kho_bep_con: 0 }], con_thieu: [] };
        return { name: 'SE-CHA', phieu_bu: a.lay_bu ? 'PDC-CHA' : '' };
      }
      if (m === 'vagabond.kho_san_xuat.hoan_tat_phieu') {
        /* Codex #551: lenh con ghi so qua cung cua voi mon chinh (gio may chu). */
        var w2 = lenh[a.phieu.work_order];
        if (a.q !== a.can || a.q !== a.phieu.qty) throw new Error('so lam lech: ' + JSON.stringify([a.q, a.can, a.phieu.qty]));
        /* Codex #551 vòng 3: phiếu Manufacture thật TRỪ nguyên liệu của lệnh
           con. Kho giả cũ chỉ cộng thành phẩm nên không thấy lệnh C2 ăn mất
           ruột C1 vừa làm cho món chính. Món giữ tồn (C1, C2) mà âm là ERPNext
           chặn thiếu tồn. */
        BOM[w2.code].dong.forEach(function (d) {
          var c = d.item_code, can = d.so * a.q / BOM[w2.code].qty;
          if (c === 'NVL') return;
          if ((ton[c] || 0) + 0.0001 < can) throw new Error('ERPNext: thieu ' + c + ' khi ghi so ' + w2.code + ' (con ' + (ton[c] || 0) + ', can ' + can + ')');
          ton[c] = (ton[c] || 0) - can;
        });
        nhat.phieu.push(w2.code + ' x' + a.q);
        nhat.layBu = (nhat.layBu || []).concat([a.lay_bu]);
        ton[w2.code] = (ton[w2.code] || 0) + a.q;
        return { name: 'SE-' + nhat.phieu.length, phieu_bu: a.lay_bu ? 'PDC-' + nhat.phieu.length : '' };
      }
      if (m === 'frappe.client.insert' || m === 'frappe.client.submit') {
        nhat.giaoTho.push(m);
        return a.doc;
      }
      throw new Error('api la: ' + m);
    },
    bomOf: async function (ds) { var r = {}; ds.forEach(function (c) { if (BOM[c]) r[c] = { name: BOM[c].name }; }); return r; },
    /* Kho tổng 307 tách riêng tồn kho bếp (v648 cách 1: lấy bù). */
    stockOf: async function (ds, wh) { var k = wh === 'Kho tổng 307 - TV' ? tong : ton; var r = {}; ds.forEach(function (c) { r[c] = k[c] || 0; }); return r; },
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
    mfgMakeBatch: async function () { return ''; },
    mfgBatchOf: async function () { return ''; },
    busy: function () {}, go: function () {}, scrMfgLabel: function () {}, mfgSheetKe: async function () { return true; },
    toast: function (c) { nhat.toast = (nhat.toast || []).concat([c]); },
    errMsg: function (e) { return String(e && e.message || e); },
    confirmSheet: async function (t, c, ok) { nhat.hoiBep = (nhat.hoiBep || []).concat([[t, c, ok]]).concat([[t, c, ok]]); return the.dongY !== false; }
  };
  /* Món chính ghi sổ: trừ đủ nguyên liệu giữ tồn của lệnh, như ERPNext. */
  the.ghiMonChinh = function (mats, ratio) {
    mats.forEach(function (m) {
      var c = m.item_code, can = (m.required_qty || 0) * ratio;
      if (c !== 'C1' && c !== 'C2') return;
      if ((ton[c] || 0) + 0.0001 < can) throw new Error('ERPNext: thieu ' + c + ' khi ghi so mon chinh (con ' + (ton[c] || 0) + ', can ' + can + ')');
      ton[c] = (ton[c] || 0) - can;
    });
    return ton;
  };
  the.MFG_KHO_TONG = 'Kho tổng 307 - TV';
  vm.createContext(the);
  ['inChunks', 'freshOf', 'mfgHoanTatMot', 'mfgCauLayBu', 'mfgGiuCuaLenh', 'mfgFreshPlan', 'mfgRunFresh', 'mfgNvlCuaKe', 'mfgChipNvl'].forEach(function (t) {
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

  /* Codex #551 vòng 3 (P2, kho_san_xuat.py:335): món chính cần CẢ ruột C1
     lẫn bánh khuôn C2, mà C2 cũng ăn C1. Trước đây máy làm C1 x2 rồi C2 x2;
     C2 ăn hết 2 ruột vừa làm cho món chính, món chính báo thiếu C1 sau khi
     hai lệnh con đã ghi sổ. Ca dựng đúng chuỗi của app: kế hoạch, chạy lệnh
     con, rồi ghi sổ món chính; kho giả trừ nguyên liệu như ERPNext. */
  var MATS2 = [
    { item_code: 'C1', item_name: 'Ruột C1', stock_uom: 'Cái', required_qty: 2 },
    { item_code: 'C2', item_name: 'Bánh khuôn C2', stock_uom: 'Cái', required_qty: 2 }
  ];
  await ca('7. mon chinh can ca C1 lan C2 (C2 cung an C1), het ton: may giu phan C1 cua mon chinh, lam du 4 C1', async function () {
    var t = theGioi({}, ['C1', 'C2']);
    var ke = await t.mfgFreshPlan(MATS2, 1, t.mfg.src);
    await t.mfgRunFresh(ke, 1);
    var con = t.ghiMonChinh(MATS2, 1);
    bang('ghi so mon chinh xong, ton trung gian ve 0', [con.C1 || 0, con.C2 || 0], [0, 0]);
    bang('tong C1 lam ra', t.nhat.phieu.filter(function (p) { return /^C1 /.test(p); }).reduce(function (s, p) { return s + +p.split('x')[1]; }, 0), 4);
  });

  await ca('8. nhu ca 7 nhung ruot C1 con 1: may chi lam them 3 C1, mon chinh van du', async function () {
    var t = theGioi({ C1: 1 }, ['C1', 'C2']);
    var ke = await t.mfgFreshPlan(MATS2, 1, t.mfg.src);
    await t.mfgRunFresh(ke, 1);
    var con = t.ghiMonChinh(MATS2, 1);
    bang('ton trung gian ve 0', [con.C1 || 0, con.C2 || 0], [0, 0]);
    bang('tong C1 lam ra', t.nhat.phieu.filter(function (p) { return /^C1 /.test(p); }).reduce(function (s, p) { return s + +p.split('x')[1]; }, 0), 3);
  });

  await ca('9. ruot C1 du cho mon chinh (2) nhung khong du cho C2: hop xac nhan ghi may lam them 2, khong coi ton do la dung duoc cho C2', async function () {
    var t = theGioi({ C1: 2 }, ['C1', 'C2']);
    var ke = await t.mfgFreshPlan(MATS2, 1, t.mfg.src);
    bang('ke hoach cap tren', ke.map(function (f) { return f.code + ' x' + f.qty; }), ['C2 x2']);
    var nvl = await t.mfgNvlCuaKe(ke, t.mfg.src);
    var c1 = nvl.filter(function (x) { return x.code === 'C1'; })[0];
    bang('chip C1', [t.mfgChipNvl(c1).phu, t.mfgChipNvl(c1).bad], ['2 · máy làm thêm 2', false]);
    await t.mfgRunFresh(ke, 1);
    var con = t.ghiMonChinh(MATS2, 1);
    bang('ton trung gian ve 0', [con.C1 || 0, con.C2 || 0], [0, 0]);
  });

  await ca('10. nhu ca 8 nhung lenh mon chinh ghi C2 truoc C1: thu tu dong cong thuc khong lam sai so', async function () {
    var t = theGioi({ C1: 1 }, ['C1', 'C2']);
    var mats = [MATS2[1], MATS2[0]];
    var ke = await t.mfgFreshPlan(mats, 1, t.mfg.src);
    await t.mfgRunFresh(ke, 1);
    var con = t.ghiMonChinh(mats, 1);
    bang('ton trung gian ve 0', [con.C1 || 0, con.C2 || 0], [0, 0]);
    bang('tong C1 lam ra', t.nhat.phieu.filter(function (p) { return /^C1 /.test(p); }).reduce(function (s, p) { return s + +p.split('x')[1]; }, 0), 3);
  });

  await ca('11. phan giu la phep thuan: cong don ong cha, khong sua ban truyen vao', async function () {
    var t = theGioi({}, []);
    var goc = { C1: 1 };
    var ra = t.mfgGiuCuaLenh(MATS2, 0.5, goc);
    bang('cong don', [ra.C1, ra.C2], [2, 1]);
    bang('ban goc giu nguyen', goc, { C1: 1 });
  });

  /* v648 cách 1 (anh Việt chọn 11/11/2026): kho bếp thiếu nguyên liệu thì máy
     lấy bù từ Kho tổng 307 khi hoàn tất. Hộp xác nhận báo trước phần lấy. */
  await ca('12. hop xac nhan: NVL thieu ma kho tong du thi ghi "lay kho tong", khong do; kho tong thieu thi do phan con thieu', async function () {
    var t = theGioi({ C1: 1 }, ['C1', 'C2'], { NVL: 500 });
    var ke = await t.mfgFreshPlan(MATS, 1, t.mfg.src);
    var nvl = await t.mfgNvlCuaKe(ke, t.mfg.src);
    var chip = nvl.map(function (x) { var c = t.mfgChipNvl(x); return [x.code, c.phu, c.bad]; });
    bang('kho tong du: khong con dong do nao', chip, [['C1', '2 · máy làm thêm 1', false], ['NVL', '200 · lấy kho tổng 200', false]]);
    t = theGioi({ C1: 1 }, ['C1', 'C2'], { NVL: 50 });
    ke = await t.mfgFreshPlan(MATS, 1, t.mfg.src);
    nvl = await t.mfgNvlCuaKe(ke, t.mfg.src);
    chip = nvl.map(function (x) { var c = t.mfgChipNvl(x); return [x.code, c.phu, c.bad]; });
    bang('kho tong chi co 50: thieu that len dau', chip[0], ['NVL', '200 · lấy kho tổng 50 · thiếu 150', true]);
  });

  await ca('13. bep dong y o hop xac nhan: moi lenh con gui lay_bu len may chu, may gom so phieu dieu chuyen', async function () {
    var t = theGioi({}, ['C1', 'C2'], { NVL: 1000 });
    var ke = await t.mfgFreshPlan(MATS, 1, t.mfg.src);
    var bu = { phieu: [] };
    await t.mfgRunFresh(ke, 1, bu);
    bang('ca hai lenh con deu xin lay bu', t.nhat.layBu, [1, 1]);
    bang('gom so phieu', bu.phieu, ['PDC-1', 'PDC-2']);
    t = theGioi({}, ['C1', 'C2']);
    ke = await t.mfgFreshPlan(MATS, 1, t.mfg.src);
    await t.mfgRunFresh(ke, 1);
    bang('khong co bu (goi kieu cu) thi khong xin', t.nhat.layBu, [0, 0]);
  });

  /* Ca 14 chạy THẬT mfgHoanTatMot (nút Hoàn tất) cho món không có phần máy tự
     làm: máy chủ chỉ hỏi, bếp đồng ý mới gửi lại với lay_bu; từ chối thì
     không gửi gì thêm. */
  await ca('14. nut Hoan tat, mon khong co phan may tu lam: hoi truoc, dong y moi lay bu; tu choi thi dung', async function () {
    var MAT = [{ item_code: 'NVL', item_name: 'Bột', stock_uom: 'Gram', required_qty: 60 }];
    var d = { name: 'WO-CHA', docstatus: 1, qty: 2, production_item: 'TP', stock_uom: 'Cái', source_warehouse: 'Pastry - Nguyên liệu - TV', required_items: MAT };
    var t = theGioi({}, ['C1', 'C2']);
    var kq = await t.mfgHoanTatMot(d, 2, 2, 0);
    bang('hai luot goi mon chinh', t.nhat.cha, [{ lay_bu: 0, hoi_lay_bu: 1 }, { lay_bu: 1 }]);
    bang('hop hoi ghi dung phan lay', [t.nhat.hoiBep[0][0], /Bột 60 Gram/.test(t.nhat.hoiBep[0][1]), t.nhat.hoiBep[0][2]],
      ['Kho bếp thiếu nguyên liệu', true, 'Lấy từ kho tổng và hoàn tất']);
    bang('bao so phieu dieu chuyen', /Đã lấy từ Kho tổng 307: PDC-CHA/.test(t.nhat.toast[0]), true);
    bang('ve man in tem', kq, 0);
    t = theGioi({}, ['C1', 'C2']);
    t.dongY = false;
    kq = await t.mfgHoanTatMot(d, 2, 2, 0);
    bang('tu choi: chi mot luot hoi, khong ghi', t.nhat.cha, [{ lay_bu: 0, hoi_lay_bu: 1 }]);
    t = theGioi({}, ['C1', 'C2']);
    await t.mfgHoanTatMot(d, 2, 2, 1);
    bang('che do theo lo: khong hoi them, nhu cu', t.nhat.cha, [{ lay_bu: 0, hoi_lay_bu: 0 }]);
  });

  /* Codex #551 vòng 5 (P2, 05-san-xuat.js:1899): hoàn tất theo lô (imLang = 1)
     bỏ hộp "Máy làm luôn giúp bếp", nên bếp CHƯA đồng ý lấy từ kho tổng. Chạy
     thật mfgHoanTatMot theo lô với món có phần máy tự làm: không lệnh nào được
     gửi lay_bu. */
  await ca('15. hoan tat theo lo co phan may tu lam: bep chua dong y lay kho tong, khong lenh nao gui lay_bu', async function () {
    var d = { name: 'WO-CHA', docstatus: 1, qty: 2, production_item: 'TP', stock_uom: 'Cái', source_warehouse: 'Pastry - Nguyên liệu - TV', required_items: MATS };
    var t = theGioi({}, ['C1', 'C2'], { NVL: 1000 });
    await t.mfgHoanTatMot(d, 2, 2, 1);
    bang('lenh con: khong lay bu', t.nhat.layBu, [0, 0]);
    bang('mon chinh: khong lay bu, khong hoi', t.nhat.cha, [{ lay_bu: 0, hoi_lay_bu: 0 }]);
    bang('khong hop hoi nao', t.nhat.hoiBep || [], []);
  });

  /* Codex #551 vòng 5 (P1, 05-san-xuat.js:1930): danh sách lấy bù dài thì hộp
     hỏi đẩy nút xác nhận ra khỏi màn. Câu hỏi phải gọn: đếm số, vài mục đầu,
     rồi "và N nữa" (AGENTS.md mục 17). */
  await ca('16. hop hoi lay bu: 12 nguyen lieu lay va 5 thieu ca kho tong van gon, nut khong bi day ra ngoai', async function () {
    var t = theGioi({}, []);
    var lay = [], con = [];
    for (var i = 1; i <= 12; i++) lay.push({ ma: 'N' + i, ten: 'Nguyên liệu ' + i, sl: i * 10, dvt: 'Gram', kho_bep_con: 0 });
    for (var j = 1; j <= 5; j++) con.push({ ma: 'K' + j, ten: 'Món ' + j, thieu: j, dvt: 'Kg' });
    var cau = t.mfgCauLayBu(lay, con);
    var dong = cau.split('\n').filter(function (x) { return x.trim(); });
    bang('toi da 3 dong', dong.length <= 3, true);
    bang('dem so va vai muc dau', [/Lấy 12 nguyên liệu/.test(cau), /Nguyên liệu 1 10 Gram/.test(cau), /và 10 nguyên liệu nữa/.test(cau)], [true, true, true]);
    bang('phan kho tong cung thieu gon', [/Kho tổng cũng thiếu 5 nguyên liệu/.test(cau), /và 3 nguyên liệu nữa/.test(cau)], [true, true]);
    bang('ngan', cau.length < 320, true);
  });

  /* Codex #551 vòng 6 (P2, 05-san-xuat.js:1900): hộp "Máy làm luôn giúp bếp"
     chỉ xét nguyên liệu của lệnh con. Lệnh con đủ nguyên liệu mà món chính
     thiếu một nguyên liệu khác thì hộp KHÔNG nói gì về kho tổng; bếp chỉ duyệt
     tạo lệnh con. Món chính phải hỏi riêng trước khi lấy bù. Chạy thật
     mfgHoanTatMot: lệnh con dùng hộp đầu, món chính hỏi lại. */
  await ca('17. lenh con du nguyen lieu, mon chinh thieu: hop dau khong noi kho tong nen mon chinh phai hoi rieng truoc khi lay bu', async function () {
    var d = { name: 'WO-CHA', docstatus: 1, qty: 2, production_item: 'TP', stock_uom: 'Cái', source_warehouse: 'Pastry - Nguyên liệu - TV', required_items: MATS };
    var t = theGioi({ NVL: 100000 }, ['C1', 'C2'], { NVL: 1000 });
    var kq = await t.mfgHoanTatMot(d, 2, 2, 0);
    bang('lenh con van lam', t.nhat.phieu, ['C1 x2', 'C2 x2']);
    bang('mon chinh: hoi truoc, dong y moi lay bu', t.nhat.cha, [{ lay_bu: 0, hoi_lay_bu: 1 }, { lay_bu: 1 }]);
    bang('hop hoi rieng cho mon chinh', t.nhat.hoiBep[0][0], 'Kho bếp thiếu nguyên liệu');
    bang('bao so phieu cua mon chinh, giu so phieu lenh con', /Đã lấy từ Kho tổng 307: PDC-1, PDC-2, PDC-CHA/.test(t.nhat.toast[0]), true);
    bang('ve man in tem', kq, 0);
    t = theGioi({ NVL: 100000 }, ['C1', 'C2'], { NVL: 1000 });
    t.dongY = false;
    kq = await t.mfgHoanTatMot(d, 2, 2, 0);
    bang('tu choi: khong lay bu, mon chinh dung', t.nhat.cha, [{ lay_bu: 0, hoi_lay_bu: 1 }]);
    bang('tu choi: bao phan may lam da xong, mon chinh chua', /món chính chưa hoàn tất/.test((t.nhat.toast || [''])[0]), true);
  });

  console.log('\n' + ket.dat + ' dat, ' + ket.hong + ' hong');
  process.exit(ket.hong ? 1 : 0);
})();

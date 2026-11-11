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
        return { name: a.name, qty: w.qty, source_warehouse: w.src, required_items: b.dong.map(function (d) {
          return { item_code: d.item_code, item_name: d.item_name, stock_uom: d.stock_uom, required_qty: d.so * w.qty };
        }) };
      }
      if (m === 'erpnext.manufacturing.doctype.work_order.work_order.make_stock_entry') {
        return { work_order: a.work_order_id, qty: a.qty, items: [{ is_finished_item: 1 }] };
      }
      if (m === 'vagabond.kho_san_xuat.hoan_tat_phieu' && a.phieu.work_order === 'WO-CHA') {
        /* Lệnh món chính (ca 14): máy chủ giả chỉ trả lời đúng luật hỏi/lấy bù.
           chaDu: món chính đủ nguyên liệu, máy chủ không hỏi. */
        nhat.cha = (nhat.cha || []).concat([{ lay_bu: a.lay_bu, hoi_lay_bu: a.hoi_lay_bu }]);
        if (a.lay_bu) nhat.chaToi = JSON.parse(a.lay_toi_da || 'null');
        if (a.hoi_lay_bu && !a.lay_bu && !the.chaDu) return { ok: 0, hoi_lay_bu: [{ ma: 'NVL', ten: 'Bột', sl: 60, dvt: 'Gram', kho_bep_con: 0 }], con_thieu: [] };
        return { name: 'SE-CHA', phieu_bu: a.lay_bu ? 'PDC-CHA' : '' };
      }
      if (m === 'vagabond.kho_san_xuat.hoan_tat_phieu') {
        /* Codex #551: lenh con ghi so qua cung cua voi mon chinh (gio may chu). */
        var w2 = lenh[a.phieu.work_order];
        if (a.q !== a.can || a.q !== a.phieu.qty) throw new Error('so lam lech: ' + JSON.stringify([a.q, a.can, a.phieu.qty]));
        /* v648 cách 1: khi app hỏi hoặc xin lấy bù, máy chủ giả tính NVL của
           kho bếp như hoan_tat_phieu thật: chỉ hỏi thì trả phần thiếu, không
           ghi gì; lấy bù thì chuyển đúng phần thiếu từ kho tổng. */
        var nvlCan = 0, layBuSo = 0;
        BOM[w2.code].dong.forEach(function (d) { if (d.item_code === 'NVL') nvlCan += d.so * a.q / BOM[w2.code].qty; });
        if (a.hoi_lay_bu || a.lay_bu) {
          /* truocGhi: đơn khác dùng kho bếp giữa lượt hỏi và lượt ghi (ca 21). */
          if (a.lay_bu && the.truocGhi) { var f0 = the.truocGhi; the.truocGhi = null; f0(ton); }
          var coNvl = ton.NVL || 0, thieuNvl = Math.round((nvlCan - coNvl) * 1000) / 1000;
          /* Như trong_han_lay của máy chủ: lượt ghi chỉ lấy trong số đã duyệt. */
          var toiDa = a.lay_bu ? JSON.parse(a.lay_toi_da || '{}') : {};
          if (thieuNvl > 0.0001 && (!a.lay_bu || thieuNvl > (toiDa.NVL || 0) + 0.0005)) {
            nhat.hoiCon = (nhat.hoiCon || []).concat([w2.code]);
            return { ok: 0, hoi_lay_bu: [{ ma: 'NVL', ten: 'Bột', sl: thieuNvl, dvt: 'Gram', kho_bep_con: coNvl }], con_thieu: [] };
          }
          layBuSo = a.lay_bu && thieuNvl > 0.0001 ? thieuNvl : 0;
          if (layBuSo) { tong.NVL = (tong.NVL || 0) - layBuSo; nhat.daLay = (nhat.daLay || 0) + layBuSo; }
          ton.NVL = Math.round((coNvl + layBuSo - nvlCan) * 1000) / 1000;
        }
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
        return { name: 'SE-' + nhat.phieu.length, phieu_bu: layBuSo ? 'PDC-' + nhat.phieu.length : '',
          da_lay: layBuSo ? [{ ma: 'NVL', sl: layBuSo }] : [] };
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
      /* v649: lệnh đang mở của cùng món (Chốt kế hoạch tạo sẵn). */
      if (dt === 'Work Order') {
        /* Như máy chủ Frappe thật: lọc theo đúng các ô bộ lọc gửi lên, cắt theo
           limit_page_length (0 là không cắt). Codex #552 P1: trước đây app chỉ
           lọc theo món, lấy 20 lệnh đầu, lệnh hợp lệ thứ 21 bị bỏ sót. */
        if (the.timLenhHong) throw new Error('mang rot');
        nhat.timLenhMo = (nhat.timLenhMo || []).concat([o.filters.production_item]);
        var f0 = o.filters;
        var ra0 = (the.lenhMo || []).filter(function (w) {
          return w.production_item === f0.production_item &&
            (!f0.fg_warehouse || w.fg_warehouse === f0.fg_warehouse) &&
            (!f0.source_warehouse || w.source_warehouse === f0.source_warehouse) &&
            (!f0.bom_no || w.bom_no === f0.bom_no);
        });
        if (o.limit_page_length) ra0 = ra0.slice(0, o.limit_page_length);
        /* Như máy chủ thật: chỉ trả các cột app xin trong fields. Codex #552
           vòng 2: quên xin process_loss_qty thì app không thấy phần hao. */
        return ra0.map(function (w) {
          lenh[w.name] = lenh[w.name] || { code: w.production_item, qty: w.qty, src: w.source_warehouse };
          var r = {};
          (o.fields || []).forEach(function (k) { if (k in w) r[k] = w[k]; });
          return r;
        });
      }
      throw new Error('getList la: ' + dt);
    },
    mfgLoadItem: async function () { return {}; },
    mfgMakeBatch: async function () { return ''; },
    mfgBatchOf: async function () { return ''; },
    busy: function () {}, go: function () {}, scrMfgLabel: function () {}, mfgSheetKe: async function () { return true; },
    toast: function (c) { nhat.toast = (nhat.toast || []).concat([c]); },
    errMsg: function (e) { return String(e && e.message || e); },
    confirmSheet: async function (t, c, ok) { nhat.hoiBep = (nhat.hoiBep || []).concat([[t, c, ok]]); return the.dongY !== false; }
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
  the.datTon = function (c, n) { ton[c] = n; };
  vm.createContext(the);
  ['inChunks', 'freshOf', 'mfgHoanTatMot', 'mfgGhiLenh', 'mfgCauLayBu', 'mfgGiuCuaLenh', 'mfgFreshPlan', 'mfgConLai', 'mfgChonLenhMo', 'mfgLenhChoTuLam', 'mfgRunFresh', 'mfgNvlCuaKe', 'mfgChipNvl'].forEach(function (t) {
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
    /* Codex #551 vòng 7: 200 g của 2 bánh khuôn cộng 50 g của 1 ruột máy làm thêm. */
    bang('chip theo thu tu: thieu that len dau', chip, [['NVL', '250 · thiếu 250', true], ['C1', '2 · máy làm thêm 1', false]]);
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
    bang('kho tong du: khong con dong do nao', chip, [['C1', '2 · máy làm thêm 1', false], ['NVL', '250 · lấy kho tổng 250', false]]);
    t = theGioi({ C1: 1 }, ['C1', 'C2'], { NVL: 50 });
    ke = await t.mfgFreshPlan(MATS, 1, t.mfg.src);
    nvl = await t.mfgNvlCuaKe(ke, t.mfg.src);
    chip = nvl.map(function (x) { var c = t.mfgChipNvl(x); return [x.code, c.phu, c.bad]; });
    bang('kho tong chi co 50: thieu that len dau', chip[0], ['NVL', '250 · lấy kho tổng 50 · thiếu 200', true]);
  });

  await ca('13. bep dong y o hop xac nhan: phan lay kho tong hop da neu thi lenh con lay luon, khong hoi lai; may gom so phieu', async function () {
    var t = theGioi({}, ['C1', 'C2'], { NVL: 1000 });
    var ke = await t.mfgFreshPlan(MATS, 1, t.mfg.src);
    var nvl = await t.mfgNvlCuaKe(ke, t.mfg.src);
    var bu = { phieu: [], duyet: {} };
    nvl.forEach(function (x) { if (x.lay_tong) bu.duyet[x.code] = x.lay_tong; });
    bang('hop neu du 300 g (C2 200, C1 100)', bu.duyet, { NVL: 300 });
    await t.mfgRunFresh(ke, 1, bu);
    bang('ca hai lenh con hoi truoc roi lay bu', [t.nhat.hoiCon, t.nhat.layBu], [['C1', 'C2'], [1, 1]]);
    bang('khong hop hoi nao them', t.nhat.hoiBep || [], []);
    bang('lay dung phan da neu', [t.nhat.daLay, bu.duyet.NVL], [300, 0]);
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
    bang('chi mot hop hoi, cho mon chinh', t.nhat.hoiBep.length, 1);
    bang('bao so phieu cua mon chinh', /Đã lấy từ Kho tổng 307: PDC-CHA/.test(t.nhat.toast[0]), true);
    bang('ve man in tem', kq, 0);
    t = theGioi({ NVL: 100000 }, ['C1', 'C2'], { NVL: 1000 });
    t.dongY = false;
    kq = await t.mfgHoanTatMot(d, 2, 2, 0);
    bang('tu choi: khong lay bu, mon chinh dung', t.nhat.cha, [{ lay_bu: 0, hoi_lay_bu: 1 }]);
    bang('tu choi: bao phan may lam da xong, mon chinh chua', /món chính chưa hoàn tất/.test((t.nhat.toast || [''])[0]), true);
  });

  /* Codex #551 vòng 7 (P2, 05-san-xuat.js:2270): bánh khuôn C2 cần ruột C1 máy
     tự làm, mà chỉ C1 thiếu nguyên liệu. Hộp "Máy làm luôn giúp bếp" trước
     đây chỉ đọc công thức C2 nên không nêu phần lấy kho tổng nào, vậy mà lệnh
     C1 vẫn được gửi lấy bù. Chạy thật nút Hoàn tất: hộp phải nêu đủ, và mọi
     phần máy lấy từ kho tổng phải nằm trong phần hộp đã nêu. */
  var MATS3 = [{ item_code: 'C2', item_name: 'Bánh khuôn C2', stock_uom: 'Cái', required_qty: 2 }];
  await ca('18. chi ruot C1 may tu lam thieu nguyen lieu: hop dau neu phan lay kho tong cua ca C1, may khong lay qua phan da neu', async function () {
    var d = { name: 'WO-CHA', docstatus: 1, qty: 2, production_item: 'TP', stock_uom: 'Cái', source_warehouse: 'Pastry - Nguyên liệu - TV', required_items: MATS3 };
    var t = theGioi({ NVL: 200 }, ['C1', 'C2'], { NVL: 1000 });
    t.chaDu = true;
    var hop = [];
    t.mfgSheetKe = async function (ke, nvl) { hop = nvl.map(function (x) { return [x.code, t.mfgChipNvl(x).phu]; }); return true; };
    var kq = await t.mfgHoanTatMot(d, 2, 2, 0);
    bang('hop dau nêu 300 g, lay kho tong 100', hop.filter(function (x) { return x[0] === 'NVL'; }), [['NVL', '300 · lấy kho tổng 100']]);
    bang('lay dung 100 g da neu, khong hoi lai', [t.nhat.daLay, t.nhat.hoiBep || []], [100, []]);
    bang('lenh con va mon chinh xong', [t.nhat.phieu, kq], [['C1 x2', 'C2 x2'], 0]);
  });

  /* Lớp chặn thứ hai: kho bếp đổi giữa lúc bếp đọc hộp và lúc máy ghi sổ (ai
     đó vừa dùng bột). Phần thiếu vượt phần đã nêu thì hỏi riêng; bếp từ chối
     thì dừng, không lấy gì thêm. */
  await ca('19. phan thieu vuot phan hop da neu: hoi rieng truoc khi lay; tu choi thi dung, khong lay', async function () {
    var d = { name: 'WO-CHA', docstatus: 1, qty: 2, production_item: 'TP', stock_uom: 'Cái', source_warehouse: 'Pastry - Nguyên liệu - TV', required_items: MATS3 };
    var t = theGioi({ NVL: 200 }, ['C1', 'C2'], { NVL: 1000 });
    t.chaDu = true;
    t.dongY = false;
    var ke = await t.mfgFreshPlan(MATS3, 1, t.mfg.src);
    var nvl = await t.mfgNvlCuaKe(ke, t.mfg.src);
    var bu = { phieu: [], duyet: {} };
    nvl.forEach(function (x) { if (x.lay_tong) bu.duyet[x.code] = x.lay_tong; });
    bang('hop neu 100 g', bu.duyet, { NVL: 100 });
    /* Hộp đọc tồn 200 g, rồi trước khi ghi sổ kho bếp chỉ còn 50 g. */
    t.datTon('NVL', 50);
    var loi = null;
    try { await t.mfgRunFresh(ke, 1, bu); } catch (e) { loi = e; }
    bang('C1 thieu 50, trong phan da neu: lay luon', t.nhat.daLay, 50);
    bang('C2 thieu 200, vuot phan con lai 50: hoi rieng', [t.nhat.hoiBep.length, t.nhat.hoiBep[0][0]], [1, 'Kho bếp thiếu nguyên liệu']);
    bang('tu choi: dung, khong lay them', [loi && loi.tuChoi, t.nhat.daLay, t.nhat.phieu], [1, 50, ['C1 x2']]);
  });

  /* Phần đã duyệt là của lệnh con. Hàng về giữa chừng làm lệnh con lấy ít hơn
     số đã nêu, phần dư KHÔNG được dùng để lấy bù cho món chính (hộp không nêu
     nguyên liệu của món chính). */
  await ca('20. phan duyet con du sau lenh con khong dung cho mon chinh: mon chinh van hoi rieng', async function () {
    var d = { name: 'WO-CHA', docstatus: 1, qty: 2, production_item: 'TP', stock_uom: 'Cái', source_warehouse: 'Pastry - Nguyên liệu - TV', required_items: MATS };
    var t = theGioi({}, ['C1', 'C2'], { NVL: 1000 });
    t.mfgSheetKe = async function () { t.datTon('NVL', 100); return true; };
    await t.mfgHoanTatMot(d, 2, 2, 0);
    bang('lenh con chi lay 200 trong 300 da neu', t.nhat.daLay, 200);
    bang('mon chinh hoi rieng', [t.nhat.cha, (t.nhat.hoiBep || []).length], [[{ lay_bu: 0, hoi_lay_bu: 1 }, { lay_bu: 1 }], 1]);
  });

  /* Codex #551 vòng 8 (P2, 05-san-xuat.js:2319): đơn khác dùng bớt kho bếp
     giữa lượt hỏi và lượt ghi. Lượt ghi mang số đã duyệt; máy chủ tính lại
     mà vượt thì chỉ hỏi lại, không ghi; vượt số hộp đã nêu thì hỏi bếp. */
  await ca('21. kho bep bi dung bot giua luot hoi va luot ghi: khong lay qua so da duyet; hoi lai, tu choi thi khong lay', async function () {
    var t = theGioi({ NVL: 50 }, ['C1', 'C2'], { NVL: 1000 });
    var bu = { phieu: [], duyet: { NVL: 50 } };
    var ke = [{ code: 'C1', qty: 2, bom: 'BOM-C1', src: t.mfg.src, giu: {} }];
    t.truocGhi = function (ton) { ton.NVL = 0; };
    t.dongY = false;
    var loi = null;
    try { await t.mfgRunFresh(ke, 1, bu); } catch (e) { loi = e; }
    bang('may chu khong ghi khi phan thieu (100) vuot so da duyet (50)', [t.nhat.daLay || 0, t.nhat.phieu], [0, []]);
    bang('hoi lai bep, tu choi thi dung', [(t.nhat.hoiBep || []).length, loi && loi.tuChoi], [1, 1]);
    t = theGioi({ NVL: 50 }, ['C1', 'C2'], { NVL: 1000 });
    bu = { phieu: [], duyet: { NVL: 50 } };
    t.truocGhi = function (ton) { ton.NVL = 0; };
    await t.mfgRunFresh(ke, 1, bu);
    bang('dong y o hop hoi lai: lay dung 100 g bep vua thay', [t.nhat.daLay, (t.nhat.hoiBep || []).length, t.nhat.phieu], [100, 1, ['C1 x2']]);
    bang('so da duyet tu hop dau khong bi tru vi phan nay duyet rieng', bu.duyet.NVL, 50);
  });

  await ca('22. v649 Chot ke hoach da tao san lenh C1, C2: bam ✓ mon chinh thi may DUNG lenh dang mo, khong tao lenh moi', async function () {
    var t = theGioi({}, ['C1', 'C2']);
    var K = t.mfg.src;
    t.lenhMo = [
      { name: 'WO-KH-C2', production_item: 'C2', qty: 5, produced_qty: 0, source_warehouse: K, fg_warehouse: K, bom_no: 'BOM-C2' },
      { name: 'WO-KH-C1', production_item: 'C1', qty: 9, produced_qty: 0, source_warehouse: K, fg_warehouse: K, bom_no: 'BOM-C1' }
    ];
    var ke = await t.mfgFreshPlan(MATS, 1, K);
    await t.mfgRunFresh(ke, 1);
    bang('khong tao lenh moi nao', t.nhat.lenh, []);
    bang('ghi so dung phan can: C1 x2 (tren lenh 9 cai), C2 x2 (tren lenh 5 cai)', t.nhat.phieu, ['C1 x2', 'C2 x2']);
  });

  await ca('23. v649 lenh dang mo khac kho, khac cong thuc hoac con thieu so thi khong dung, tao lenh moi nhu cu', async function () {
    var t = theGioi({}, ['C1', 'C2']);
    var K = t.mfg.src;
    t.lenhMo = [
      { name: 'WO-BAKER', production_item: 'C2', qty: 5, produced_qty: 0, source_warehouse: 'Baker - Nguyên liệu - TV', fg_warehouse: 'Baker - Nguyên liệu - TV', bom_no: 'BOM-C2' },
      { name: 'WO-BOM-CU', production_item: 'C2', qty: 5, produced_qty: 0, source_warehouse: K, fg_warehouse: K, bom_no: 'BOM-C2-CU' },
      { name: 'WO-GAN-XONG', production_item: 'C1', qty: 9, produced_qty: 8, source_warehouse: K, fg_warehouse: K, bom_no: 'BOM-C1' }
    ];
    var ke = await t.mfgFreshPlan(MATS, 1, K);
    await t.mfgRunFresh(ke, 1);
    bang('tao lenh moi cho ca hai', t.nhat.lenh, ['C2 x2', 'C1 x2']);
  });

  await ca('24. Codex #552 P1: hon 20 lenh dang mo cua cung mon, lenh hop le la lenh thu 21: van dung lenh do, khong tao moi', async function () {
    var t = theGioi({ C1: 9 }, ['C1', 'C2']);
    var K = t.mfg.src;
    t.lenhMo = [];
    for (var i = 0; i < 20; i++) {
      t.lenhMo.push({ name: 'WO-CU-' + i, production_item: 'C2', qty: 3, produced_qty: 2, source_warehouse: K, fg_warehouse: K, bom_no: 'BOM-C2' });
    }
    t.lenhMo.push({ name: 'WO-21', production_item: 'C2', qty: 5, produced_qty: 0, source_warehouse: K, fg_warehouse: K, bom_no: 'BOM-C2' });
    var ke = await t.mfgFreshPlan(MATS, 1, K);
    await t.mfgRunFresh(ke, 1);
    bang('khong tao lenh moi', t.nhat.lenh, []);
    bang('ghi so tren lenh thu 21', t.nhat.phieu, ['C2 x2']);
  });

  await ca('25. Codex #552 P2: doc lenh dang mo bi loi thi DUNG, khong tao lenh moi, khong ghi so gi', async function () {
    var t = theGioi({}, ['C1', 'C2']);
    t.timLenhHong = 1;
    var ke = await t.mfgFreshPlan(MATS, 1, t.mfg.src);
    var loi = null;
    try { await t.mfgRunFresh(ke, 1); } catch (e) { loi = e; }
    bang('bao loi cho bep', !!loi, true);
    bang('khong tao lenh', t.nhat.lenh, []);
    bang('khong ghi so', t.nhat.phieu, []);
  });

  /* Codex #552 vòng 2 (05-san-xuat.js mfgChonLenhMo): lệnh làm dở có ghi
     hao hụt. Số còn được làm = qty - produced_qty - process_loss_qty, như
     scrMfgView và kho_san_xuat.so_hoan_tat. Lệnh 10, đã làm 6, hao 3 chỉ còn
     1: không được nhận thêm 2. */
  await ca('26. Codex #552 vong 2: lenh lam do co hao hut, phan con lai (tru hao) khong du thi KHONG dung, tao lenh moi; con du thi dung', async function () {
    var t = theGioi({ C1: 9 }, ['C1', 'C2']);
    var K = t.mfg.src;
    t.lenhMo = [
      { name: 'WO-HAO', production_item: 'C2', qty: 10, produced_qty: 6, process_loss_qty: 3, source_warehouse: K, fg_warehouse: K, bom_no: 'BOM-C2' }
    ];
    var ke = await t.mfgFreshPlan(MATS, 1, K);
    await t.mfgRunFresh(ke, 1);
    bang('con 1 (10 - 6 - 3) < 2: tao lenh moi C2 x2', t.nhat.lenh, ['C2 x2']);
    t = theGioi({ C1: 9 }, ['C1', 'C2']);
    t.lenhMo = [
      { name: 'WO-HAO2', production_item: 'C2', qty: 10, produced_qty: 6, process_loss_qty: 2, source_warehouse: K, fg_warehouse: K, bom_no: 'BOM-C2' }
    ];
    ke = await t.mfgFreshPlan(MATS, 1, K);
    await t.mfgRunFresh(ke, 1);
    bang('con 2 (10 - 6 - 2) du 2: dung lenh dang mo', [t.nhat.lenh, t.nhat.phieu], [[], ['C2 x2']]);
  });

  console.log('\n' + ket.dat + ' dat, ' + ket.hong + ' hong');
  process.exit(ket.hong ? 1 : 0);
})();

/* v648 (anh Việt chốt 11/11/2026, phương án C): bếp chỉ bấm Hoàn tất món chính,
 * ruột bánh cấp 1, bánh khuôn cấp 2 còn thiếu tồn thì máy tự tạo và hoàn tất
 * lệnh của chúng theo công thức, trước món chính.
 *
 * CHẠY THẬT các hàm của 05-san-xuat.js (freshOf, mfgFreshPlan, mfgRunFresh)
 * trên một kho giả trong bộ nhớ: lệnh, tồn, công thức, phiếu kho. Máy chủ giả
 * chỉ trả lời câu "món nào máy được tự làm" (vagabond.kho_san_xuat.mon_tu_lam,
 * luật thật có ca Python riêng) và ghi lại thứ tự lệnh, phiếu.
 *
 * v655 (phương án B, anh Việt 13/11/2026): bỏ hẳn lấy bù Kho tổng 307. Kho
 * bếp thiếu thì máy chủ ném câu cau_thieu_nvl; app mời bếp gửi phiếu xin kho
 * tổng (xin_kho_tong) ngay trên hộp báo. Các ca 12 tới 21 cũ (hỏi, lấy bù)
 * thay bằng ca của luồng mới.
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
        if (a.work_order_id === 'WO-CHA') return { work_order: 'WO-CHA', qty: a.qty, items: the.itemsCha || [{ is_finished_item: 1 }] };
        var w3 = lenh[a.work_order_id], b3 = BOM[w3.code];
        return { work_order: a.work_order_id, qty: a.qty, items: b3.dong.map(function (d) {
          var sl = d.so * a.qty / b3.qty;
          return { item_code: d.item_code, s_warehouse: w3.src, qty: sl, transfer_qty: sl, conversion_factor: 1 };
        }).concat([{ item_code: w3.code, t_warehouse: w3.src, qty: a.qty, is_finished_item: 1 }]) };
      }
      if (m === 'vagabond.kho_san_xuat.xin_kho_tong') {
        nhat.xin = (nhat.xin || []).concat([{ dong: JSON.parse(a.dong), ten_lenh: a.ten_lenh }]);
        return { ok: 1, phieu: ['YCDC-1'], ghi_chu: 'Đã gửi phiếu xin YCDC-1 cho kho tổng.' };
      }
      if (m === 'vagabond.kho_san_xuat.hoan_tat_phieu' && a.phieu.work_order === 'WO-CHA') {
        /* Lệnh món chính: chaThieu thì máy chủ báo kho bếp thiếu (đúng câu
           cau_thieu_nvl); chaLoi là lỗi khác (rớt mạng). */
        nhat.cha = (nhat.cha || []).concat([Object.keys(a).sort().join(',')]);
        if (the.chaLoi) throw new Error(the.chaLoi);
        if (the.chaThieu) throw new Error('Chưa hoàn tất được lệnh WO-CHA: kho Pastry - Nguyên liệu chưa đủ nguyên liệu. Bột cần 60 Gram (kho đang có 0). Lệnh này chưa ghi sổ. Bấm Gửi phiếu xin kho tổng: kho tổng giao xong thì bấm Hoàn tất lại.');
        return { name: 'SE-CHA' };
      }
      if (m === 'vagabond.kho_san_xuat.hoan_tat_phieu') {
        /* Codex #551: lenh con ghi so qua cung cua voi mon chinh (gio may chu). */
        var w2 = lenh[a.phieu.work_order];
        if (a.q !== a.can || a.q !== a.phieu.qty) throw new Error('so lam lech: ' + JSON.stringify([a.q, a.can, a.phieu.qty]));
        /* v655: máy chủ không lấy bù. NVL (theo dõi khi đặt tồn) thiếu thì
           ném đúng câu thiếu nguyên liệu; app cũ có gửi cờ lấy bù thì ghi lại
           để ca bắt. */
        var nvlCan = 0;
        BOM[w2.code].dong.forEach(function (d) { if (d.item_code === 'NVL') nvlCan += d.so * a.q / BOM[w2.code].qty; });
        if (a.hoi_lay_bu || a.lay_bu || a.lay_toi_da) nhat.coLayBu = (nhat.coLayBu || 0) + 1;
        if ('NVL' in ton) {
          if (the.truocGhi) { var f0 = the.truocGhi; the.truocGhi = null; f0(ton); }
          if (ton.NVL + 0.0001 < nvlCan) throw new Error('Chưa hoàn tất được lệnh ' + a.phieu.work_order + ': kho Pastry - Nguyên liệu chưa đủ nguyên liệu. Bột cần ' + nvlCan + ' Gram (kho đang có ' + ton.NVL + '). Lệnh này chưa ghi sổ. Bấm Gửi phiếu xin kho tổng: kho tổng giao xong thì bấm Hoàn tất lại.');
          ton.NVL = Math.round((ton.NVL - nvlCan) * 1000) / 1000;
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
    /* Kho tổng 307 tách riêng tồn kho bếp: v655 app không còn đọc nó để lấy bù. */
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
  ['inChunks', 'freshOf', 'mfgKhoLenh', 'mfgHoanTatMot', 'mfgGhiLenh', 'mfgLaLoiThieuNvl', 'mfgDongXinCuaPhieu', 'mfgHoiXinKhoTong', 'mfgGiuCuaLenh', 'mfgFreshPlan', 'mfgConLai', 'mfgChonLenhMo', 'mfgLenhChoTuLam', 'mfgRunFresh', 'mfgNvlCuaKe', 'mfgChipNvl'].forEach(function (t) {
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

  /* v655 (phương án B, anh Việt 13/11/2026): không còn lấy bù Kho tổng 307.
     Kho bếp thiếu thì báo thiếu và mời bếp gửi phiếu xin. */
  var NUT = '📦 Gửi phiếu xin kho tổng';
  var CHA = { name: 'WO-CHA', docstatus: 1, qty: 2, production_item: 'TP', stock_uom: 'Cái', source_warehouse: 'Pastry - Nguyên liệu - TV' };
  var ITEMS_CHA = [
    { item_code: 'NVL', s_warehouse: 'Pastry - Nguyên liệu - TV', qty: 0.06, conversion_factor: 1000, uom: 'Kg', stock_uom: 'Gram' },
    { item_code: 'MUOI', s_warehouse: 'Kho tổng 307 - TV', qty: 5, transfer_qty: 5 },
    { item_code: 'VUN', t_warehouse: 'Kho phế - TV', qty: 1, is_scrap_item: 1 },
    { item_code: 'TP', t_warehouse: 'Pastry - Thành phẩm - TV', qty: 2, is_finished_item: 1 }
  ];

  await ca('12. v655 hop "May lam luon giup bep": NVL thieu ma Kho tong co hang van bao thieu (do), khong con chu "lay kho tong"', async function () {
    var t = theGioi({ C1: 1 }, ['C1', 'C2'], { NVL: 500 });
    var ke = await t.mfgFreshPlan(MATS, 1, t.mfg.src);
    var nvl = await t.mfgNvlCuaKe(ke, t.mfg.src);
    var chip = nvl.map(function (x) { var c = t.mfgChipNvl(x); return [x.code, c.phu, c.bad]; });
    bang('chip', chip, [['NVL', '250 · thiếu 250', true], ['C1', '2 · máy làm thêm 1', false]]);
  });

  await ca('13. v655 lenh con va mon chinh khong gui co lay bu nao len may chu', async function () {
    var t = theGioi({ NVL: 1000 }, ['C1', 'C2'], { NVL: 1000 });
    var kq = await t.mfgHoanTatMot(Object.assign({ required_items: MATS }, CHA), 2, 2, 0);
    bang('lenh con xong', t.nhat.phieu, ['C1 x2', 'C2 x2']);
    bang('khong co lay bu', [t.nhat.coLayBu || 0, t.nhat.cha], [0, ['can,phieu,q']]);
    bang('khong hop hoi, ve man in tem', [t.nhat.hoiBep || [], kq], [[], 0]);
  });

  await ca('14. nut Hoan tat, kho bep thieu: hop bao thieu co nut gui phieu xin; dong y thi xin theo dong nguyen lieu cua phieu, lenh van chua ghi', async function () {
    var t = theGioi({}, ['C1', 'C2']);
    t.chaThieu = 1; t.itemsCha = ITEMS_CHA;
    var loi = null;
    try { await t.mfgHoanTatMot(Object.assign({ required_items: [] }, CHA), 2, 2, 0); } catch (e) { loi = e; }
    bang('van bao loi (lenh chua ghi)', !!loi, true);
    bang('hop', [t.nhat.hoiBep.length, t.nhat.hoiBep[0][0], t.nhat.hoiBep[0][2]], [1, 'Kho bếp chưa đủ nguyên liệu', NUT]);
    bang('hop noi dung cau may chu', /Bột cần 60 Gram/.test(t.nhat.hoiBep[0][1]), true);
    bang('xin: chi dong xuat kho bep, theo don vi ton (0,06 Kg = 60 Gram); bo dong Kho tong, phe pham, thanh pham',
      t.nhat.xin, [{ dong: [{ ma: 'NVL', kho: 'Pastry - Nguyên liệu - TV', can: 60 }], ten_lenh: 'WO-CHA' }]);
    bang('bao da gui', /YCDC-1/.test(t.nhat.toast.join(' ')), true);
  });

  await ca('15. bep bam Huy o hop bao thieu: khong gui phieu xin; hoan tat theo lo (im lang): khong hop, khong xin', async function () {
    var t = theGioi({}, ['C1', 'C2']);
    t.chaThieu = 1; t.itemsCha = ITEMS_CHA; t.dongY = false;
    try { await t.mfgHoanTatMot(Object.assign({ required_items: [] }, CHA), 2, 2, 0); } catch (e) { }
    bang('huy: khong xin', [t.nhat.hoiBep.length, t.nhat.xin || []], [1, []]);
    t = theGioi({}, ['C1', 'C2']);
    t.chaThieu = 1; t.itemsCha = ITEMS_CHA;
    var loi = null;
    try { await t.mfgHoanTatMot(Object.assign({ required_items: [] }, CHA), 2, 2, 1); } catch (e) { loi = e; }
    bang('theo lo: nem loi kem dong xin cho nguoi goi, khong tu hien hop', [!!(loi && loi.dongXin), t.nhat.hoiBep || [], t.nhat.xin || []], [true, [], []]);
  });

  await ca('16. ruot C1 may tu lam thieu bot: dung o lenh con, hop xin dung phan cua lenh con do', async function () {
    var t = theGioi({ NVL: 50 }, ['C1', 'C2']);
    var loi = null;
    try { await t.mfgHoanTatMot(Object.assign({ required_items: MATS }, CHA), 2, 2, 0); } catch (e) { loi = e; }
    bang('chua ghi gi', t.nhat.phieu, []);
    bang('hop xin', [t.nhat.hoiBep.length, t.nhat.hoiBep[0][2]], [1, NUT]);
    bang('xin bot cua lenh C1 (WO-2), kho bep', t.nhat.xin, [{ dong: [{ ma: 'NVL', kho: 'Pastry - Nguyên liệu - TV', can: 100 }], ten_lenh: 'WO-2' }]);
    bang('mon chinh khong goi', t.nhat.cha || [], []);
  });

  await ca('17. loi khac (rot mang) khong phai thieu nguyen lieu: khong hien hop xin, bao loi nhu cu', async function () {
    var t = theGioi({}, ['C1', 'C2']);
    t.chaLoi = 'Mất kết nối, thử lại'; t.itemsCha = ITEMS_CHA;
    try { await t.mfgHoanTatMot(Object.assign({ required_items: [] }, CHA), 2, 2, 0); } catch (e) { }
    bang('khong hop, khong xin', [t.nhat.hoiBep || [], t.nhat.xin || []], [[], []]);
    bang('bao loi', t.nhat.toast, ['Mất kết nối, thử lại']);
  });

  await ca('18. THUAN mfgLaLoiThieuNvl va mfgDongXinCuaPhieu', async function () {
    var t = theGioi({}, []);
    bang('nhan cau may chu', t.mfgLaLoiThieuNvl('Chưa hoàn tất được lệnh X: kho Baker chưa đủ nguyên liệu. Rum cần 22,792 ML.'), true);
    bang('khong nhan cau khac', [t.mfgLaLoiThieuNvl('Cần 0.361 đơn vị Món A'), t.mfgLaLoiThieuNvl(''), t.mfgLaLoiThieuNvl(null)], [false, false, false]);
    bang('gop theo dong, bo dong 0', t.mfgDongXinCuaPhieu({ items: [{ item_code: 'A', s_warehouse: 'K', qty: 0 }, { item_code: 'B', s_warehouse: 'K', qty: 2 }] }),
      [{ ma: 'B', kho: 'K', can: 2 }]);
    bang('phieu rong', t.mfgDongXinCuaPhieu(null), []);
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

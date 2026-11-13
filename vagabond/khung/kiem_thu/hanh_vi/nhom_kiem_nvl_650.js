/* v650 (anh Việt 12/11/2026, chọn hướng A): Hoàn thành CẢ NHÓM lệnh sản xuất
 * kiểm nguyên liệu cho TỔNG số TRƯỚC khi ghi bất cứ gì.
 *
 * Đường lỗi anh gặp: thẻ gộp BÁNH MEAD 2 lệnh (2 + 3 cái), kho bếp thiếu Cacao
 * Mass. Bấm dấu tích, gõ số, Hoàn thành: app bỏ qua bước kiểm, lệnh nháp bị
 * ghi, phần máy làm thêm (lệnh con) ghi sổ, rồi món chính hỏng với câu dịch
 * máy "Cần 0.361 đơn vị Món ... để hoàn tất giao dịch này".
 *
 * CHẠY THẬT các hàm của 05-san-xuat.js (mfgHoanTatNhom, mfgHoanTatMot,
 * mfgKiemNvlNhom, mfgNvlCuaKe, mfgRunFresh, mfgGhiLenh...) trên kho giả trong
 * bộ nhớ. Máy chủ giả làm đúng luật hoan_tat_phieu từ v655 (phương án B, anh
 * Việt 13/11/2026): KHÔNG lấy bù Kho tổng 307; kho bếp thiếu thì ném câu
 * cau_thieu_nvl. Bếp được mời gửi phiếu xin kho tổng (xin_kho_tong) đúng phần
 * thiếu ngay trên hộp báo.
 *
 * Chạy: node vagabond/khung/kiem_thu/hanh_vi/nhom_kiem_nvl_650.js
 * Đo bản trước: NGUON=/duong/05-san-xuat.js node ... (bản cũ).
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var SRC = fs.readFileSync(process.env.NGUON || path.join(GOC, 'vagabond', 'public', 'js', 'bep', '05-san-xuat.js'), 'utf8');

function layHam(src, ten) {
  var dau = src.indexOf('function ' + ten + '(');
  if (dau < 0) return '';
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
function co(mo, chuoi, phan) {
  if (String(chuoi).indexOf(phan) < 0) throw new Error(mo + ': khong thay "' + phan + '" trong ' + JSON.stringify(chuoi));
}

var KHO = 'Pastry - Nguyên liệu - TV', TONG = 'Kho tổng 307 - TV';

/* Thế giới: bánh TP cần 1 bánh khuôn C2 (máy tự làm phần thiếu) và 0,1 Kg
 * cacao; mỗi C2 cần 100 g bột. Lệnh WO-A 2 cái, WO-B 3 cái, còn nháp. */
function theGioi(ton, tong, opt) {
  opt = opt || {};
  var tonKho = opt.tonKho || {};
  function tonCua(kho) { if (kho === KHO) return ton; if (kho === TONG) return tong; if (!tonKho[kho]) tonKho[kho] = {}; return tonKho[kho]; }
  var ALT = opt.alt || {};
  var BOM = {
    TP: { name: 'BOM-TP', qty: 1, dong: [{ item_code: 'C2', item_name: 'Bánh khuôn C2', stock_uom: 'Cái', so: 1 },
      { item_code: 'CACAO', item_name: 'Cacao Mass 100%', stock_uom: 'Kg', so: 0.1 }] },
    C2: { name: 'BOM-C2', qty: 1, dong: [{ item_code: 'BOT', item_name: 'Bột', stock_uom: 'Gram', so: 100 }] }
  };
  if (opt.dongThem) BOM.TP.dong = BOM.TP.dong.concat(opt.dongThem);
  var lenh = {
    'WO-A': { code: 'TP', qty: 2, src: KHO, docstatus: 0 },
    'WO-B': { code: 'TP', qty: 3, src: KHO, docstatus: 0 },
    'WO-D': { code: 'TP', qty: 1, src: KHO, docstatus: 0 }
  };
  /* Codex #553: lệnh qua bước chuyển kho (skip 0, kho dở dang) hoặc dòng
     nguyên liệu khai kho nguồn riêng (khoMon). */
  Object.keys(opt.lenh || {}).forEach(function (k) { Object.assign(lenh[k], opt.lenh[k]); });
  function khoTru(w, c) { return (w.skip === 0 && w.wip) ? w.wip : ((w.khoMon && w.khoMon[c]) || w.src); }
  var nhat = { lenh: [], phieu: [], ghiNhap: [], hoiBep: [], toast: [], xin: [], coLayBu: 0 }, dem = 0;
  function r3(n) { return Math.round(n * 1000) / 1000; }
  var the = {
    console: console, Math: Math, JSON: JSON, Promise: Promise, Object: Object, String: String, Error: Error,
    r3: r3,
    mfg: { src: KHO },
    MFG_KHO_TONG: TONG,
    today: function () { return '2026-11-12'; },
    nowStamp: function () { return '2026-11-12 05:40:00'; },
    api: async function (m, a) {
      if (m === 'vagabond.kho_san_xuat.mon_tu_lam') return JSON.parse(a.ma).filter(function (c) { return c === 'C2'; });
      if (m === 'frappe.client.get') {
        var w = lenh[a.name];
        return { name: a.name, qty: w.qty, docstatus: w.docstatus, production_item: w.code, bom_no: BOM[w.code].name,
          source_warehouse: w.src, fg_warehouse: w.src, stock_uom: 'Cái',
          skip_transfer: w.skip === 0 ? 0 : 1, from_wip_warehouse: 0, wip_warehouse: w.wip || '',
          required_items: BOM[w.code].dong.map(function (d) {
            return { item_code: d.item_code, item_name: d.item_name, stock_uom: d.stock_uom, required_qty: r3(d.so * w.qty / BOM[w.code].qty),
              source_warehouse: (w.khoMon && w.khoMon[d.item_code]) || w.src };
          }) };
      }
      if (m === 'vagabond.kho_san_xuat.thay_the_cho_thieu') {
        /* Máy chủ giả đúng hợp đồng của thay_the_cho_thieu: mã thay cùng kho,
           phần nhóm tự dùng mã thay trừ trước, cả nhóm chung một túi. */
        var dg = JSON.parse(a.dong), dungK = {}, tui = {}, ra0 = [];
        nhat.hoiThay = (nhat.hoiThay || 0) + 1;
        dg.forEach(function (x) { dungK[x.ma + '|' + x.kho] = (dungK[x.ma + '|' + x.kho] || 0) + x.can; });
        dg.forEach(function (x) {
          if (!(x.thieu > 0.0001)) return;
          var m2 = ALT[x.ma], bu = 0, thay = [];
          if (m2) {
            var k2 = m2 + '|' + x.kho;
            if (!(k2 in tui)) tui[k2] = Math.max(0, (tonCua(x.kho)[m2] || 0) - (dungK[k2] || 0));
            bu = r3(Math.min(x.thieu, tui[k2])); tui[k2] = r3(tui[k2] - bu);
            if (bu > 0.0001) thay.push({ ma: m2, ten: opt.tenAlt || m2, sl: bu });
          }
          ra0.push({ ma: x.ma, kho: x.kho, bu: bu, con: r3(x.thieu - bu), thay: thay });
        });
        return ra0;
      }
      if (m === 'frappe.client.submit') { nhat.ghiNhap.push(a.doc.name); lenh[a.doc.name].docstatus = 1; return a.doc; }
      if (m === 'erpnext.manufacturing.doctype.work_order.work_order.make_stock_entry') {
        var w1 = lenh[a.work_order_id], b1 = BOM[w1.code];
        return { work_order: a.work_order_id, qty: a.qty, items: b1.dong.map(function (d) {
          var sl = r3(d.so * a.qty / b1.qty);
          return { item_code: d.item_code, s_warehouse: khoTru(w1, d.item_code), qty: sl, transfer_qty: sl, conversion_factor: 1 };
        }).concat([{ item_code: w1.code, t_warehouse: w1.src, qty: a.qty, is_finished_item: 1 }]) };
      }
      if (m === 'vagabond.kho_san_xuat.xin_kho_tong') {
        nhat.xin.push({ dong: JSON.parse(a.dong), ten_lenh: a.ten_lenh });
        return { ok: 1, phieu: ['YCDC-1'], ghi_chu: 'Đã gửi phiếu xin YCDC-1 cho kho tổng.' };
      }
      if (m === 'vagabond.kho_san_xuat.hoan_tat_phieu') {
        if (the.truocGhi) { var f0 = the.truocGhi; the.truocGhi = null; f0(ton); }
        var w2 = lenh[a.phieu.work_order], b = BOM[w2.code];
        var can = {};
        b.dong.forEach(function (d) { can[d.item_code] = r3((can[d.item_code] || 0) + d.so * a.q / b.qty); });
        if (a.hoi_lay_bu || a.lay_bu || a.lay_toi_da) nhat.coLayBu++;
        var dungThay = {};
        Object.keys(can).forEach(function (c) {
          var tk = tonCua(khoTru(w2, c)), th2 = r3(can[c] - (tk[c] || 0));
          /* lo_hang.thay_ma_khong_lo: thiếu thì lấy mã thay cùng kho. */
          if (th2 > 0.0001 && ALT[c]) { var l2 = r3(Math.min(th2, tk[ALT[c]] || 0)); dungThay[c] = l2; th2 = r3(th2 - l2); }
          /* Đúng câu kho_san_xuat.cau_thieu_nvl của máy chủ. */
          if (th2 > 0.0001) throw new Error('Chưa hoàn tất được lệnh ' + a.phieu.work_order + ': kho ' + khoTru(w2, c) +
            ' chưa đủ nguyên liệu. ' + c + ' cần ' + th2 + '. Lệnh này chưa ghi sổ. Bấm Gửi phiếu xin kho tổng: kho tổng giao xong thì bấm Hoàn tất lại.');
        });
        Object.keys(can).forEach(function (c) {
          var tk = tonCua(khoTru(w2, c)), l3 = dungThay[c] || 0;
          tk[c] = r3((tk[c] || 0) - (can[c] - l3));
          if (l3) tk[ALT[c]] = r3(tk[ALT[c]] - l3);
        });
        ton[w2.code] = r3((ton[w2.code] || 0) + a.q);
        nhat.phieu.push(a.phieu.work_order + ' x' + a.q);
        return { name: 'SE-' + nhat.phieu.length };
      }
      throw new Error('api la: ' + m);
    },
    bomOf: async function (ds) { var r = {}; ds.forEach(function (c) { if (BOM[c]) r[c] = { name: BOM[c].name }; }); return r; },
    stockOf: async function (ds, wh) { var k = wh === TONG ? tong : tonCua(wh); var r = {}; ds.forEach(function (c) { r[c] = k[c] || 0; }); return r; },
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
      if (dt === 'Work Order') return [];
      throw new Error('getList la: ' + dt);
    },
    mfgCreateWO: async function (f) {
      var ten = 'WO-C' + (++dem);
      lenh[ten] = { code: f.code, qty: f.qty, src: f.src, docstatus: 1 };
      nhat.lenh.push(f.code + ' x' + f.qty);
      return ten;
    },
    mfgSheetHoanTat: async function (tong0) { return { theo_lenh: the.lam || tong0, thuc_te: the.lam || tong0 }; },
    mfgHoanTatNhanh: async function () { throw new Error('khong duoc di duong mot lenh'); },
    mfgNhoSo: function () {},
    mfgLoadItem: async function () { return {}; },
    mfgMakeBatch: async function () { return ''; },
    mfgBatchOf: async function () { return ''; },
    busy: function () {}, go: function () {}, scrMfgLabel: function () {},
    mfgSheetKe: async function () { throw new Error('nhom khong duoc hien hop tung lenh'); },
    toast: function (c) { nhat.toast.push(c); },
    errMsg: function (e) { return String(e && e.message || e); },
    num: function (n) { var v = Math.round((n || 0) * 1000) / 1000; return v.toLocaleString('vi-VN'); },
    h: function (s) { return String(s == null ? '' : s); },
    shortWh: function (w) { return String(w || '').replace(/ - TVD?$/, ''); },
    confirmSheet: async function (t, c, ok) {
      nhat.hoiBep.push([t, c, ok]);
      var tl = the.traLoi ? the.traLoi.shift() : true;
      return tl !== false;
    }
  };
  vm.createContext(the);
  ['inChunks', 'freshOf', 'mfgChiaSo', 'mfgHoanTatNhom', 'mfgHoanTatMot', 'mfgKiemNvlNhom', 'mfgPhanNvl', 'mfgCauThieuNhom',
    'mfgGhiLenh', 'mfgLaLoiThieuNvl', 'mfgDongXinCuaPhieu', 'mfgDongXinNhom', 'mfgHoiXinKhoTong', 'mfgGiuCuaLenh', 'mfgFreshPlan', 'mfgConLai', 'mfgChonLenhMo', 'mfgLenhChoTuLam',
    'mfgRunFresh', 'mfgNvlCuaKe', 'mfgChipNvl', 'mfgKhoLenh', 'mfgCauThay'].forEach(function (t) {
    var ma = layHam(SRC, t);
    if (ma) vm.runInContext(ma, the);
  });
  the.nhat = nhat;
  the.ton = ton; the.tong = tong; the.tonKho = tonKho;
  return the;
}

var NHOM = { con: [{ ten: 'WO-A', so_can: 2, so_da: 0 }, { ten: 'WO-B', so_can: 3, so_da: 0 }], dvt: 'Cái', ma_mon: 'TP' };

async function ca(ten, fn) {
  try { await fn(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); }
}

(async function () {
  var NUT = '📦 Gửi phiếu xin kho tổng';
  /* v655 Codex #562 (P1): app gửi MỌI nguyên liệu nhóm dùng, chỉ số cần, KHÔNG
     số thiếu (máy chủ tự đọc tồn và hàng thay thế lúc bấm Gửi). */
  function xinGon(t) { return t.nhat.xin.map(function (x) { return x.dong.map(function (d) { return 'thieu' in d ? [d.ma, d.kho, d.can, d.thieu] : [d.ma, d.kho, d.can]; }); }); }

  await ca('1. duong loi anh Viet: bep thieu cacao: dung TRUOC khi ghi, khong lenh nao bi ghi, hop noi ro thieu gi va moi gui phieu xin kho tong', async function () {
    var t = theGioi({ CACAO: 0.1, BOT: 1000 }, {});
    await t.mfgHoanTatNhom(NHOM);
    bang('khong ghi gi', [t.nhat.phieu, t.nhat.lenh, t.nhat.ghiNhap], [[], [], []]);
    bang('mot hop duy nhat, nut gui phieu xin', t.nhat.hoiBep.map(function (x) { return x[2]; }), [NUT]);
    var hop = t.nhat.hoiBep[0];
    co('tieu de', hop[0], 'máy chưa ghi lệnh nào');
    co('mon thieu va so thieu', hop[1], 'Cacao Mass 100%: thiếu 0,4 Kg (cần 0,5, Pastry - Nguyên liệu có 0,1)');
    co('viec can lam', hop[1], 'Bấm Gửi phiếu xin kho tổng');
    bang('gui moi nguyen lieu nhom dung, khong kem so thieu', xinGon(t), [[['CACAO', KHO, 0.5], ['BOT', KHO, 500]]]);
    bang('ghi ten ca hai lenh', t.nhat.xin[0].ten_lenh, 'WO-A, WO-B');
    co('bao da gui', t.nhat.toast.join(' | '), 'YCDC-1');
  });

  await ca('2. v655 bep thieu ma Kho tong 307 CO HANG: KHONG tu lay kho tong nua, van dung va moi gui phieu xin', async function () {
    var t = theGioi({ CACAO: 0.1, BOT: 1000 }, { CACAO: 2 });
    await t.mfgHoanTatNhom(NHOM);
    bang('khong ghi gi', [t.nhat.phieu, t.nhat.ghiNhap], [[], []]);
    bang('nut gui phieu xin, khong con nut lay kho tong', t.nhat.hoiBep.map(function (x) { return x[2]; }), [NUT]);
    bang('kho tong khong bi tru', t.tong.CACAO, 2);
    bang('gui phieu xin (may chu tinh 0,4)', xinGon(t), [[['CACAO', KHO, 0.5], ['BOT', KHO, 500]]]);
  });

  await ca('3. bep du: hop nhu cu, ghi ca 2 lenh, khong gui co lay bu nao len may chu', async function () {
    var t = theGioi({ CACAO: 1, BOT: 1000 }, { CACAO: 2 });
    await t.mfgHoanTatNhom(NHOM);
    bang('nut', t.nhat.hoiBep.map(function (x) { return x[2]; }), ['Ghi sổ 2 lệnh']);
    bang('ghi du', t.nhat.phieu.length, 4);
    bang('khong co lay bu', [t.nhat.coLayBu, t.nhat.xin.length], [0, 0]);
  });

  await ca('4. phan may lam them (bot cua banh khuon C2) cung duoc kiem: bot thieu thi dung truoc khi ghi, xin ca bot', async function () {
    var t = theGioi({ CACAO: 1, BOT: 100 }, {});
    await t.mfgHoanTatNhom(NHOM);
    bang('khong phieu kho nao', t.nhat.phieu, []);
    co('noi bot', t.nhat.hoiBep[0][1], 'Bột: thiếu 400 Gram');
    bang('gui ca bot (may chu tinh 400)', xinGon(t), [[['BOT', KHO, 500], ['CACAO', KHO, 0.5]]]);
  });

  await ca('5. bep bam Huy o hop bao thieu: khong gui phieu xin, khong ghi gi', async function () {
    var t = theGioi({ CACAO: 0.1, BOT: 1000 }, { CACAO: 2 });
    t.traLoi = [false];
    await t.mfgHoanTatNhom(NHOM);
    bang('khong gi', [t.nhat.phieu, t.nhat.lenh, t.nhat.ghiNhap, t.nhat.xin], [[], [], [], []]);
  });

  await ca('6. kho bep voi di giua luc kiem va luc ghi (don khac vua dung): dung o WO-B, bao dung so lenh da ghi, moi xin dung phan cua phieu WO-B', async function () {
    var t = theGioi({ CACAO: 0.5, BOT: 1000 }, { CACAO: 2 });
    var lan = 0, cu = t.api;
    t.api = async function (m, a) {
      if (m === 'vagabond.kho_san_xuat.hoan_tat_phieu' && a.phieu.work_order === 'WO-A' && !lan++) t.ton.CACAO = 0.2; /* đơn khác vừa dùng 0,1 */
      return cu(m, a);
    };
    await t.mfgHoanTatNhom(NHOM);
    bang('hai hop: xac nhan nhom, roi bao dung kem nut xin', t.nhat.hoiBep.map(function (x) { return x[2]; }), ['Ghi sổ 2 lệnh', NUT]);
    bang('chi lenh A (va lenh con cua B) da ghi', t.nhat.phieu, ['WO-C1 x2', 'WO-A x2', 'WO-C2 x3']);
    co('bao dung', t.nhat.hoiBep[1][1], 'Đã ghi sổ 1 lệnh, dừng ở WO-B');
    bang('xin theo dong nguyen lieu cua phieu WO-B (may chu tu doc ton)', xinGon(t), [[['C2', KHO, 3], ['CACAO', KHO, 0.3]]]);
    bang('ten lenh', t.nhat.xin[0].ten_lenh, 'WO-B');
  });

  await ca('8. ba lenh, lenh giua hong vi thieu: DUNG, lenh sau khong duoc ghi', async function () {
    var t = theGioi({ CACAO: 0.6, BOT: 1000 }, { CACAO: 2 });
    t.traLoi = [true, false];
    var lan = 0, cu = t.api;
    t.api = async function (m, a) {
      if (m === 'vagabond.kho_san_xuat.hoan_tat_phieu' && a.phieu.work_order === 'WO-A' && !lan++) t.ton.CACAO = 0.2;
      return cu(m, a);
    };
    await t.mfgHoanTatNhom({ con: NHOM.con.concat([{ ten: 'WO-D', so_can: 1, so_da: 0 }]), dvt: 'Cái', ma_mon: 'TP' });
    bang('hop bao dung o lenh B', t.nhat.hoiBep.length, 2);
    bang('WO-D khong ghi, khong ghi nhap', [t.nhat.phieu.filter(function (x) { return x.indexOf('WO-D') === 0; }), t.nhat.ghiNhap.indexOf('WO-D')], [[], -1]);
    bang('bep bam Huy: khong gui phieu', t.nhat.xin, []);
  });

  await ca('7. THUAN mfgPhanNvl: phan may tu lam khong tinh thieu; khong con phan lay kho tong', async function () {
    var t = theGioi({}, {});
    var kt = t.mfgPhanNvl([
      { code: 'C2', name: 'C2', thieu: 5, tu_lam: 1 },
      { code: 'CACAO', name: 'Cacao', uom: 'Kg', thieu: 0.4, lay_tong: 0.1, need: 0.5, ton: 0.1, kho: KHO },
      { code: 'BOT', name: 'Bột', thieu: 0 }
    ]);
    bang('khong co lay', kt.lay, undefined);
    bang('thieu du 0,4, bo qua lay_tong cua app cu', kt.thieu.map(function (x) { return [x.code, x.thieu, x.can]; }), [['CACAO', 0.4, 0.5]]);
  });

  await ca('9. Codex #553 P1: cacao het o bep, hang thay the da khai (Cacao 70%) du: KHONG chan, hop noi dung hang thay, ghi ca 2 lenh', async function () {
    var t = theGioi({ CACAO: 0, CACAO2: 1, BOT: 1000 }, {}, { alt: { CACAO: 'CACAO2' }, tenAlt: 'Cacao Mass 70%' });
    await t.mfgHoanTatNhom(NHOM);
    bang('mot hop xac nhan', t.nhat.hoiBep.map(function (x) { return x[2]; }), ['Ghi sổ 2 lệnh']);
    co('noi hang thay', t.nhat.hoiBep[0][1], 'Dùng hàng thay thế đã khai: Cacao Mass 70% 0,5 Kg thay Cacao Mass 100%');
    bang('ghi ca 2 lenh', t.nhat.phieu, ['WO-C1 x2', 'WO-A x2', 'WO-C2 x3', 'WO-B x3']);
    bang('cacao 70% con 0,5', t.ton.CACAO2, 0.5);
  });

  await ca('9b. hang thay the chi du mot phan: van chan truoc khi ghi, xin dung phan con thieu sau hang thay', async function () {
    var t = theGioi({ CACAO: 0, CACAO2: 0.2, BOT: 1000 }, {}, { alt: { CACAO: 'CACAO2' }, tenAlt: 'Cacao Mass 70%' });
    await t.mfgHoanTatNhom(NHOM);
    bang('khong phieu kho nao', t.nhat.phieu, []);
    co('thieu 0,3', t.nhat.hoiBep[0][1], 'Cacao Mass 100%: thiếu 0,3 Kg');
    bang('gui so can; phan hang thay may chu tinh lai luc gui (thu_xin_kho_tong_655)', xinGon(t), [[['CACAO', KHO, 0.5], ['BOT', KHO, 500]]]);
  });

  await ca('9c. bep du thi khong hoi may chu hang thay the (khong them buoc)', async function () {
    var t = theGioi({ CACAO: 1, BOT: 1000 }, {}, { alt: { CACAO: 'CACAO2' } });
    await t.mfgHoanTatNhom(NHOM);
    bang('khong hoi', t.nhat.hoiThay || 0, 0);
    bang('ghi du', t.nhat.phieu.length, 4);
  });

  await ca('10. Codex #553 P2: lenh qua buoc chuyen kho, nguyen lieu da o kho do dang: KHONG chan, kiem va tru dung kho do dang', async function () {
    var WIP = 'Kho dở dang - TV';
    var t = theGioi({}, {}, { lenh: { 'WO-A': { skip: 0, wip: WIP }, 'WO-B': { skip: 0, wip: WIP } },
      tonKho: { 'Kho dở dang - TV': { C2: 5, CACAO: 0.5 } } });
    await t.mfgHoanTatNhom(NHOM);
    bang('mot hop xac nhan', t.nhat.hoiBep.map(function (x) { return x[2]; }), ['Ghi sổ 2 lệnh']);
    bang('ghi ca 2 lenh, khong lam them C2', t.nhat.phieu, ['WO-A x2', 'WO-B x3']);
    bang('tru o kho do dang', [t.tonKho[WIP].C2, t.tonKho[WIP].CACAO], [0, 0]);
  });

  await ca('11. Codex #553 P2: dong cacao khai kho nguon rieng (kho lanh): kiem dung kho lanh, khong chan', async function () {
    var LANH = 'Kho lạnh - TV';
    var t = theGioi({ BOT: 1000 }, {}, { lenh: { 'WO-A': { khoMon: { CACAO: LANH } }, 'WO-B': { khoMon: { CACAO: LANH } } },
      tonKho: { 'Kho lạnh - TV': { CACAO: 0.5 } } });
    await t.mfgHoanTatNhom(NHOM);
    bang('mot hop xac nhan', t.nhat.hoiBep.map(function (x) { return x[2]; }), ['Ghi sổ 2 lệnh']);
    bang('ghi ca 2 lenh', t.nhat.phieu.length, 4);
    bang('kho lanh het cacao', t.tonKho[LANH].CACAO, 0);
  });

  await ca('13. hai lenh thieu cacao o hai kho khac nhau (0,2 va 0,3): MOT hop, xin tung kho dung phan thieu cua kho do', async function () {
    var LANH = 'Kho lạnh - TV';
    var t = theGioi({ BOT: 1000, CACAO: 0 }, { CACAO: 5 }, { lenh: { 'WO-B': { khoMon: { CACAO: LANH } } },
      tonKho: { 'Kho lạnh - TV': { CACAO: 0 } } });
    await t.mfgHoanTatNhom(NHOM);
    bang('khong phieu kho nao', t.nhat.phieu, []);
    bang('mot hop', t.nhat.hoiBep.length, 1);
    bang('xin theo tung kho', xinGon(t), [[['CACAO', KHO, 0.2], ['BOT', KHO, 500], ['CACAO', LANH, 0.3]]]);
  });

  await ca('14. lenh A tru thang cacao o Kho tong (du), lenh B thieu 0,3 o bep: chi xin phan cua kho bep', async function () {
    var t = theGioi({ BOT: 1000, CACAO: 0 }, { CACAO: 0.3 }, { lenh: { 'WO-A': { khoMon: { CACAO: TONG } } } });
    await t.mfgHoanTatNhom(NHOM);
    bang('khong phieu kho nao', t.nhat.phieu, []);
    bang('chi gui dong kho bep, bo dong Kho tong', xinGon(t), [[['CACAO', KHO, 0.3], ['BOT', KHO, 500]]]);
  });

  await ca('12. THUAN mfgPhanNvl: hang thay bu mot phan thi tach rieng, chi tinh phan con lai la thieu', async function () {
    var t = theGioi({}, {});
    var kt = t.mfgPhanNvl([{ code: 'CACAO', name: 'Cacao', uom: 'Kg', thieu: 0.5, thay: 0.3, thay_ds: [{ ten: 'Cacao 70%' }], need: 0.5, ton: 0, kho: KHO }]);
    bang('thay', kt.thay.map(function (x) { return x.sl; }), [0.3]);
    bang('thieu', kt.thieu.map(function (x) { return x.thieu; }), [0.2]);
  });

  console.log('\n' + ket.dat + ' dat, ' + ket.hong + ' hong');
  process.exit(ket.hong ? 1 : 0);
})();

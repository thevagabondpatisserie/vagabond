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
 * bộ nhớ. Máy chủ giả làm đúng luật hoan_tat_phieu: chỉ hỏi thì không ghi gì,
 * lấy bù trong số đã duyệt, kho bếp vẫn thiếu thì ERPNext ném lỗi thiếu tồn.
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
function theGioi(ton, tong) {
  var BOM = {
    TP: { name: 'BOM-TP', qty: 1, dong: [{ item_code: 'C2', item_name: 'Bánh khuôn C2', stock_uom: 'Cái', so: 1 },
      { item_code: 'CACAO', item_name: 'Cacao Mass 100%', stock_uom: 'Kg', so: 0.1 }] },
    C2: { name: 'BOM-C2', qty: 1, dong: [{ item_code: 'BOT', item_name: 'Bột', stock_uom: 'Gram', so: 100 }] }
  };
  var lenh = {
    'WO-A': { code: 'TP', qty: 2, src: KHO, docstatus: 0 },
    'WO-B': { code: 'TP', qty: 3, src: KHO, docstatus: 0 },
    'WO-D': { code: 'TP', qty: 1, src: KHO, docstatus: 0 }
  };
  var nhat = { lenh: [], phieu: [], ghiNhap: [], hoiBep: [], toast: [], laybu: 0 }, dem = 0;
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
          required_items: BOM[w.code].dong.map(function (d) {
            return { item_code: d.item_code, item_name: d.item_name, stock_uom: d.stock_uom, required_qty: r3(d.so * w.qty / BOM[w.code].qty) };
          }) };
      }
      if (m === 'frappe.client.submit') { nhat.ghiNhap.push(a.doc.name); lenh[a.doc.name].docstatus = 1; return a.doc; }
      if (m === 'erpnext.manufacturing.doctype.work_order.work_order.make_stock_entry') {
        return { work_order: a.work_order_id, qty: a.qty, items: [{ is_finished_item: 1 }] };
      }
      if (m === 'vagabond.kho_san_xuat.hoan_tat_phieu') {
        if (the.truocGhi) { var f0 = the.truocGhi; the.truocGhi = null; f0(ton); }
        var w2 = lenh[a.phieu.work_order], b = BOM[w2.code];
        var can = {};
        b.dong.forEach(function (d) { can[d.item_code] = r3((can[d.item_code] || 0) + d.so * a.q / b.qty); });
        var lay = [], conThieu = [];
        Object.keys(can).forEach(function (c) {
          var th = r3(can[c] - (ton[c] || 0));
          if (th <= 0.0001) return;
          var l = r3(Math.min(th, Math.max(0, tong[c] || 0)));
          if (l > 0.0001) lay.push({ ma: c, ten: c, sl: l, dvt: '' });
          if (th - l > 0.0001) conThieu.push({ ma: c, ten: c, sl: r3(th - l) });
        });
        if (a.hoi_lay_bu || a.lay_bu) {
          var toi = a.lay_bu ? JSON.parse(a.lay_toi_da || '{}') : null;
          var trong = toi && lay.every(function (x) { return (toi[x.ma] || 0) + 0.0005 >= x.sl; });
          if (lay.length && !trong) return { ok: 0, hoi_lay_bu: lay, con_thieu: conThieu };
          lay.forEach(function (x) { tong[x.ma] = r3(tong[x.ma] - x.sl); ton[x.ma] = r3((ton[x.ma] || 0) + x.sl); nhat.laybu = r3(nhat.laybu + x.sl); });
        } else { lay = []; }
        Object.keys(can).forEach(function (c) {
          if ((ton[c] || 0) + 0.0001 < can[c]) throw new Error('Cần ' + r3(can[c] - (ton[c] || 0)) + ' đơn vị Món ' + c + ' tại ' + KHO + ' để hoàn tất giao dịch này.');
        });
        Object.keys(can).forEach(function (c) { ton[c] = r3(ton[c] - can[c]); });
        ton[w2.code] = r3((ton[w2.code] || 0) + a.q);
        nhat.phieu.push(a.phieu.work_order + ' x' + a.q);
        return { name: 'SE-' + nhat.phieu.length, phieu_bu: lay.length ? 'PDC-' + nhat.phieu.length : '', da_lay: lay };
      }
      throw new Error('api la: ' + m);
    },
    bomOf: async function (ds) { var r = {}; ds.forEach(function (c) { if (BOM[c]) r[c] = { name: BOM[c].name }; }); return r; },
    stockOf: async function (ds, wh) { var k = wh === TONG ? tong : ton; var r = {}; ds.forEach(function (c) { r[c] = k[c] || 0; }); return r; },
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
    'mfgGhiLenh', 'mfgCauLayBu', 'mfgGiuCuaLenh', 'mfgFreshPlan', 'mfgConLai', 'mfgChonLenhMo', 'mfgLenhChoTuLam',
    'mfgRunFresh', 'mfgNvlCuaKe', 'mfgChipNvl'].forEach(function (t) {
    var ma = layHam(SRC, t);
    if (ma) vm.runInContext(ma, the);
  });
  the.nhat = nhat;
  the.ton = ton; the.tong = tong;
  return the;
}

var NHOM = { con: [{ ten: 'WO-A', so_can: 2, so_da: 0 }, { ten: 'WO-B', so_can: 3, so_da: 0 }], dvt: 'Cái', ma_mon: 'TP' };

async function ca(ten, fn) {
  try { await fn(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); }
}

(async function () {
  await ca('1. duong loi anh Viet: bep thieu cacao, kho tong cung khong co: dung TRUOC khi ghi, khong lenh nao bi ghi, khong lenh con, hop noi ro thieu gi', async function () {
    var t = theGioi({ CACAO: 0.1, BOT: 1000 }, {});
    await t.mfgHoanTatNhom(NHOM);
    bang('khong phieu kho nao', t.nhat.phieu, []);
    bang('khong tao lenh con', t.nhat.lenh, []);
    bang('khong ghi lenh nhap', t.nhat.ghiNhap, []);
    bang('mot hop duy nhat', t.nhat.hoiBep.length, 1);
    var hop = t.nhat.hoiBep[0];
    co('tieu de', hop[0], 'máy chưa ghi lệnh nào');
    co('mon thieu va so thieu', hop[1], 'Cacao Mass 100%: thiếu 0,4 Kg (cần 0,5, Pastry - Nguyên liệu có 0,1)');
    co('viec can lam', hop[1], 'Xin chuyển nguyên liệu');
    bang('khong toast cau dich may', t.nhat.toast.filter(function (x) { return x.indexOf('để hoàn tất giao dịch') >= 0; }), []);
  });

  await ca('2. bep thieu, kho tong 307 du: van MOT hop xac nhan, nut ghi ro lay kho tong; dong y thi ghi ca 2 lenh, khong hoi them', async function () {
    var t = theGioi({ CACAO: 0.1, BOT: 1000 }, { CACAO: 2 });
    await t.mfgHoanTatNhom(NHOM);
    bang('mot hop duy nhat', t.nhat.hoiBep.length, 1);
    var hop = t.nhat.hoiBep[0];
    bang('nut', hop[2], 'Lấy kho tổng và ghi sổ 2 lệnh');
    co('noi lay bao nhieu', hop[1], 'Cacao Mass 100% 0,4 Kg');
    co('van liet ke tung lenh', hop[1], '• WO-B: 3 Cái');
    bang('phieu: lenh con roi mon chinh, ca 2 lenh', t.nhat.phieu, ['WO-C1 x2', 'WO-A x2', 'WO-C2 x3', 'WO-B x3']);
    bang('lay kho tong dung 0,4', t.nhat.laybu, 0.4);
    co('bao xong', t.nhat.toast.join(' | '), 'Đã ghi sổ 2 lệnh');
  });

  await ca('3. bep du: hop nhu cu, khong nhac kho tong, ghi ca 2 lenh, khong lay bu', async function () {
    var t = theGioi({ CACAO: 1, BOT: 1000 }, { CACAO: 2 });
    await t.mfgHoanTatNhom(NHOM);
    bang('nut', t.nhat.hoiBep.map(function (x) { return x[2]; }), ['Ghi sổ 2 lệnh']);
    bang('khong lay bu', t.nhat.laybu, 0);
    bang('ghi du', t.nhat.phieu.length, 4);
  });

  await ca('4. phan may lam them (bot cua banh khuon C2) cung duoc kiem: bot thieu, kho tong khong co thi dung truoc khi ghi', async function () {
    var t = theGioi({ CACAO: 1, BOT: 100 }, {});
    await t.mfgHoanTatNhom(NHOM);
    bang('khong phieu kho nao', t.nhat.phieu, []);
    co('noi bot', t.nhat.hoiBep[0][1], 'Bột: thiếu 400 Gram');
  });

  await ca('5. bep bam Huy o hop xac nhan: khong ghi gi', async function () {
    var t = theGioi({ CACAO: 0.1, BOT: 1000 }, { CACAO: 2 });
    t.traLoi = [false];
    await t.mfgHoanTatNhom(NHOM);
    bang('khong phieu', [t.nhat.phieu, t.nhat.lenh, t.nhat.ghiNhap], [[], [], []]);
  });

  await ca('6. kho bep doi giua luc kiem va luc ghi, may chu doi lay them ngoai so da duyet: hoi rieng; bep tu choi thi dung, bao dung so lenh da ghi', async function () {
    var t = theGioi({ CACAO: 0.1, BOT: 1000 }, { CACAO: 2 });
    t.traLoi = [true, false];
    var lan = 0;
    var cu = t.api;
    t.api = async function (m, a) {
      if (m === 'vagabond.kho_san_xuat.hoan_tat_phieu' && a.phieu.work_order === 'WO-A' && !lan++) t.ton.CACAO = 0; /* đơn khác vừa dùng hết 0,1 Kg của bếp */
      return cu(m, a);
    };
    await t.mfgHoanTatNhom(NHOM);
    bang('hai hop: xac nhan nhom, roi hoi rieng', t.nhat.hoiBep.map(function (x) { return x[0]; }), ['Ghi sổ 2 lệnh', 'Kho bếp thiếu nguyên liệu']);
    bang('chi lenh A (va lenh con cua B) da ghi', t.nhat.phieu, ['WO-C1 x2', 'WO-A x2', 'WO-C2 x3']);
    co('bao dung', t.nhat.toast.join(' | '), 'Đã ghi sổ 1 lệnh, dừng ở WO-B: bếp chưa đồng ý lấy thêm từ kho tổng');
  });

  await ca('8. ba lenh, lenh giua bi tu choi lay them: DUNG, lenh sau khong duoc ghi', async function () {
    /* Lúc kiểm bếp có 0,3, duyệt lấy 0,3; đơn khác dùng hết 0,3 nên lệnh B cần lấy quá phần duyệt. */
    var t = theGioi({ CACAO: 0.3, BOT: 1000 }, { CACAO: 2 });
    t.traLoi = [true, false];
    var lan = 0, cu = t.api;
    t.api = async function (m, a) {
      if (m === 'vagabond.kho_san_xuat.hoan_tat_phieu' && a.phieu.work_order === 'WO-A' && !lan++) t.ton.CACAO = 0;
      return cu(m, a);
    };
    await t.mfgHoanTatNhom({ con: NHOM.con.concat([{ ten: 'WO-D', so_can: 1, so_da: 0 }]), dvt: 'Cái', ma_mon: 'TP' });
    bang('hop hoi rieng o lenh B', t.nhat.hoiBep.length, 2);
    bang('WO-D khong ghi, khong ghi nhap', [t.nhat.phieu.filter(function (x) { return x.indexOf('WO-D') === 0; }), t.nhat.ghiNhap.indexOf('WO-D')], [[], -1]);
  });

  await ca('7. THUAN mfgPhanNvl: phan may tu lam khong tinh thieu; kho tong phu mot phan thi tach lay va thieu', async function () {
    var t = theGioi({}, {});
    var kt = t.mfgPhanNvl([
      { code: 'C2', name: 'C2', thieu: 5, tu_lam: 1 },
      { code: 'CACAO', name: 'Cacao', uom: 'Kg', thieu: 0.4, lay_tong: 0.1, need: 0.5, ton: 0.1, kho: KHO },
      { code: 'BOT', name: 'Bột', thieu: 0 }
    ]);
    bang('lay', kt.lay.map(function (x) { return [x.code, x.lay]; }), [['CACAO', 0.1]]);
    bang('thieu', kt.thieu.map(function (x) { return [x.code, x.thieu]; }), [['CACAO', 0.3]]);
  });

  console.log('\n' + ket.dat + ' dat, ' + ket.hong + ' hong');
  process.exit(ket.hong ? 1 : 0);
})();

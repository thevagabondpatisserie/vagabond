/* Bo ca kiem HANH VI cho man "Nhan hang" va "Giao hang" cua phieu yeu cau.
 *
 * Vi sao co tep nay: truoc 06/09/2026 man Nhan hang TU chon lo o phia trinh
 * duyet bang ham fefoPick, goi get_batch_qty khong kem co for_stock_levels.
 * Khong co co do thi ERPNext loc bo moi lo qua han, nen bep xin nhan qua
 * phan con han la man hinh bao "khong du lo hang" trong khi kho van con.
 * Do that tren site 06/09: NVLT00109 con 330.000 gram o Kho Lab, ham do chi
 * thay 50.000.
 *
 * BAI HOC DAT NHAT cua tep nay (Codex bat tren #219, head 79d12b0): ban dau
 * bo kiem tu DUNG `rcv` va chi nap doReceive, nen no xanh trong khi ban sua
 * da xoa nham CA man scrRecvTransfer khoi nguon. Mot bo kiem tu cap lay cai
 * ma man hinh phai tu dung thi khong bao gio thay man hinh mat. Nay moi ca
 * di tu man CHI TIET PHIEU that: bam nut Nhan/Giao, chinh so, xac nhan, roi
 * moi soi payload. Khong tu cap rcv, khong stub scrRecvTransfer.
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/chay_nhan_hang.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');

function docTep(ten) { return fs.readFileSync(path.join(BEP, ten), 'utf8'); }

function layDong(src, dau) {
  var i = src.indexOf(dau);
  if (i < 0) throw new Error('Khong thay dong ' + dau);
  return src.slice(i, src.indexOf('\n', i));
}

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

/* Nap mot ham NEU nguon con no. Nguon thieu thi tra ve rong, de ca kiem
   nhin thay dung hanh vi cua ban thieu (ReferenceError luc bam nut) chu
   khong do vi "khong nap duoc ham". Do vi ha tang la mot kieu tu lua minh. */
function layNeuCo(src, ten) {
  return src.indexOf('function ' + ten + '(') >= 0 ? layHam(src, ten) : '';
}

var ket = { dat: 0, hong: 0, loi: [] };

function dung(mo, dk) {
  if (!dk) throw new Error(mo + ': duoc false, mong true');
}
function bang(mo, a, b) {
  if (a !== b) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b));
}

/* ---------- dung moi truong ---------- */

/* Phieu yeu cau dieu chuyen noi bo, dung so do that tren site 06/09/2026:
   NVLT00109 con 330.000 o Kho Lab nhung chi 50.000 nam o lo con han. */
function phieuMau(them) {
  var p = {
    name: 'MAT-MR-0001', docstatus: 1, material_request_type: 'Material Transfer',
    status: 'Pending', transaction_date: '2026-09-06', schedule_date: '2026-09-06',
    set_from_warehouse: 'Kho Lab - TV', set_warehouse: 'Kho Bep - TV', owner: 'khai',
    items: [{
      name: 'dong-1', item_code: 'NVLT00109', item_name: 'Bot mi', qty: 60000, uom: 'Gram',
      stock_uom: 'Gram', conversion_factor: 1, ordered_qty: 0, schedule_date: '2026-09-06',
    }],
  };
  Object.keys(them || {}).forEach(function (k) { p[k] = them[k]; });
  return p;
}

function dungMan(canh) {
  canh = canh || {};
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);

  var goiApi = [];
  var daToast = [];
  var daGo = [];

  var that = {
    document: tai,
    console: console,
    Math: Math, JSON: JSON, Date: Date, String: String, Number: Number,
    Array: Array, Object: Object, Promise: Promise, RegExp: RegExp,
    setTimeout: setTimeout, parseFloat: parseFloat, parseInt: parseInt,

    COMPANY: 'Cong ty TNHH Patisserie Vagabond',
    S: { me: { full_name: 'Khai' }, user: 'khai@vagabond' },
    VN: {},
    XK: {},
    /* frame that ve ca footer, vi nut Nhan/Giao va nut Xac nhan deu nam o
       footer. Khung cu khong ve footer la ca nay khong bao gio thay nut. */
    frame: function (tieuDe, html, opt) {
      opt = opt || {};
      khung.innerHTML = html + (opt.footer ? '<div class="vf">' + opt.footer + '</div>' : '');
      return khung;
    },
    go: function (fn) { daGo.push(fn); return fn(); },
    api: function (duong, ts) {
      goiApi.push({ duong: duong, ts: ts });
      if (duong === 'frappe.client.get') return Promise.resolve(canh.phieu || phieuMau());
      if (canh.hongKhiGui && duong === 'frappe.client.insert') {
        return Promise.reject(new Error('gia lap mat mang'));
      }
      if (duong === 'frappe.client.insert') {
        return new Promise(function (r) {
          setTimeout(function () { r({ name: 'MAT-STE-0001' }); }, 5);
        });
      }
      /* Bat chuoc DUNG hanh vi ERPNext: khong kem co for_stock_levels thi
         chi tra ve lo con han. Tra ve du 330.000 la ban cu cung xanh va ca
         kiem tu che mat cai loi no sinh ra de bat. */
      if (String(duong).indexOf('get_batch_qty') >= 0) {
        return Promise.resolve([{ batch_no: 'NVLT00109-006', qty: 50000, warehouse: 'Kho Lab - TV' }]);
      }
      return Promise.resolve({ name: 'MAT-STE-0001' });
    },
    getList: function (dt, ts) {
      if (dt === 'Item') {
        var ma = ((ts || {}).filters || {}).name || [];
        return Promise.resolve((ma[1] || []).map(function (m) { return { name: m, has_batch_no: 1 }; }));
      }
      if (dt === 'Batch') return Promise.resolve([{ name: 'NVLT00109-006', expiry_date: '2026-09-11' }]);
      return Promise.resolve([]);   /* khong co phieu nhap nao, khong co dong giao nao */
    },
    confirmSheet: function () { return Promise.resolve(canh.dongY !== 0); },
    busy: function () {},
    toast: function (t) { daToast.push(String(t)); },
    back: function () {},
    render: function () {},
    whFind: function (k, loai) { return k === 'lab' ? 'Kho Lab TP - TV' : ''; },
    today: function () { return '2026-09-06'; },
    nowStamp: function () { return '2026-09-06 09:00:00'; },
  };
  that.globalThis = that;

  var bay = new Proxy(that, {
    has: function () { return true; },
    get: function (t, k) {
      if (k in t) return t[k];
      if (typeof k === 'symbol') return undefined;
      if (k in globalThis) return globalThis[k];
      throw new ReferenceError('Ten toan cuc "' + k + '" chua duoc dat');
    },
    set: function (t, k, v) { t[k] = v; return true; },
  });

  var nen = docTep('00-nen.js');
  var kho = docTep('03-kho-chung-tu.js');
  var ma = [
    layHam(nen, 'h'),
    layHam(nen, 'num'),
    layHam(nen, 'dmy'),
    layHam(nen, 'vnSt'),
    layHam(nen, 'shortWh'),
    layHam(kho, 'bepWhFg'),
    layHam(kho, 'canGiaoBep'),
    layHam(kho, 'canReceive'),
    layHam(kho, 'scrMRView'),
    /* Ba cai duoi day la thu ban 79d12b0 da xoa nham. Nap NEU CO. */
    kho.indexOf('var rcv = ') >= 0 ? layDong(kho, 'var rcv = ') : '',
    layNeuCo(kho, 'scrRecvTransfer'),
    layNeuCo(kho, 'fefoPick'),
    kho.indexOf('var RCV_DANG_GUI') >= 0 ? layDong(kho, 'var RCV_DANG_GUI') : 'var RCV_DANG_GUI = 0;',
    layHam(kho, 'errMsg'),
    layHam(kho, 'doReceive'),
  ].join('\n;\n');

  vm.runInNewContext(ma, bay, { filename: '03-kho-chung-tu.js' });
  return { g: that, tai: tai, khung: khung, goiApi: goiApi, toast: daToast, daGo: daGo, nguon: kho };
}

/* Mo man chi tiet phieu that roi bam nut co id `idNut`. Tra ve loi (neu co)
   cua chinh cai onclick, vi onclick la ham async: loi trong do khong noi len
   qua click() ma nam trong promise. */
async function moTuManChiTiet(m, idNut, T) {
  await m.g.scrMRView('MAT-MR-0001', T || { key: 'Material Transfer', title: 'Dieu chuyen noi bo' });
  var nut = m.tai.getElementById(idNut);
  if (!nut) throw new Error('Man chi tiet khong co nut #' + idNut);
  try {
    await nut.onclick(dg.suKien('click', {}, nut));
    return null;
  } catch (e) {
    return e;
  }
}

function goSo(m, i, v) {
  var o = m.tai.querySelector('[data-q="' + i + '"]');
  if (!o) throw new Error('Khong thay o so luong ' + i);
  o.value = String(v);
  o.dispatchEvent(dg.suKien('input', {}, o));
}

async function bamXacNhan(m) {
  var ok = m.tai.getElementById('rcOk');
  if (!ok) throw new Error('Khong thay nut Xac nhan');
  ok.onclick(dg.suKien('click', {}, ok));
  /* doReceive khong duoc await tu onclick, cho no chay het. */
  for (var i = 0; i < 40; i++) await new Promise(function (r) { setTimeout(r, 2); });
}

function dongGui(m) {
  var g = m.goiApi.filter(function (x) { return x.duong === 'frappe.client.insert'; });
  return g.length ? (g[0].ts.doc.items || []) : [];
}

/* ---------- cac ca ---------- */

var CAC_CA = [];
function ca(ten, ham) { CAC_CA.push([ten, ham]); }

ca('1. tu man chi tiet phieu, bam "Da nhan hang" thi man Nhan hang phai MO RA', async function () {
  var m = dungMan();
  var loi = await moTuManChiTiet(m, 'vRecv');
  dung('nut khong nem loi' + (loi ? ': ' + loi.message : ''), !loi);
  dung('co o so luong', !!m.tai.querySelector('[data-q="0"]'));
  dung('co nut Xac nhan', !!m.tai.getElementById('rcOk'));
});

ca('2. chinh so 60000 roi xac nhan: dong gui di KHONG kem lo, may chu chon', async function () {
  var m = dungMan();
  await moTuManChiTiet(m, 'vRecv');
  goSo(m, 0, 60000);
  await bamXacNhan(m);
  var it = dongGui(m);
  bang('mot dong', it.length, 1);
  bang('dung ma', it[0].item_code, 'NVLT00109');
  bang('dung so vua chinh', it[0].qty, 60000);
  dung('khong kem batch_no', !('batch_no' in it[0]));
  dung('khong bat co use_serial_batch_fields', !('use_serial_batch_fields' in it[0]));
  bang('phieu yeu cau', it[0].material_request, 'MAT-MR-0001');
  bang('dong yeu cau', it[0].material_request_item, 'dong-1');
});

ca('3. khong con hoi get_batch_qty, va nguon khong con fefoPick', async function () {
  var m = dungMan();
  await moTuManChiTiet(m, 'vRecv');
  goSo(m, 0, 60000);
  await bamXacNhan(m);
  var co = m.goiApi.filter(function (x) { return String(x.duong).indexOf('get_batch_qty') >= 0; });
  bang('khong goi lan nao', co.length, 0);
  dung('nguon khong con fefoPick', m.nguon.indexOf('function fefoPick(') < 0);
});

ca('4. khong bao gio bao "khong du lo hang" o phia man hinh nua', async function () {
  var m = dungMan();
  await moTuManChiTiet(m, 'vRecv');
  goSo(m, 0, 60000);
  await bamXacNhan(m);
  dung('khong con cau do', m.toast.join(' ').indexOf('không đủ lô hàng') < 0);
  bang('phieu da duoc gui', dongGui(m).length, 1);
});

ca('5. giu don vi nguoi go va he so quy doi sau khi qua man', async function () {
  var p = phieuMau();
  p.items[0].uom = 'Tui'; p.items[0].qty = 2; p.items[0].conversion_factor = 1000;
  var m = dungMan({ phieu: p });
  await moTuManChiTiet(m, 'vRecv');
  await bamXacNhan(m);
  var d = dongGui(m)[0];
  bang('don vi nguoi go', d.uom, 'Tui');
  bang('he so quy doi', d.conversion_factor, 1000);
  bang('so luong theo don vi do', d.qty, 2);
});

ca('6. bam Xac nhan hai lan trong luc dang gui chi tao MOT phieu kho', async function () {
  var m = dungMan();
  await moTuManChiTiet(m, 'vRecv');
  var ok = m.tai.getElementById('rcOk');
  ok.onclick(dg.suKien('click', {}, ok));
  ok.onclick(dg.suKien('click', {}, ok));
  for (var i = 0; i < 40; i++) await new Promise(function (r) { setTimeout(r, 2); });
  var so = m.goiApi.filter(function (x) { return x.duong === 'frappe.client.insert'; });
  bang('dung mot lan insert', so.length, 1);
});

ca('7. gui hong thi bo co, bam lai duoc ngay', async function () {
  var m = dungMan({ hongKhiGui: 1 });
  await moTuManChiTiet(m, 'vRecv');
  await bamXacNhan(m);
  bang('co da duoc bo', m.g.RCV_DANG_GUI, 0);
  dung('co bao loi', m.toast.length > 0);
});

ca('8. nut + khong cho nhan qua so tren phieu', async function () {
  var m = dungMan();
  await moTuManChiTiet(m, 'vRecv');
  var cong = m.tai.querySelector('[data-p="0"]');
  cong.click();
  bang('da o max thi khong tang', m.g.rcv.rows[0].qty, 60000);
  goSo(m, 0, 70000);
  bang('go qua thi keo ve max', m.g.rcv.rows[0].qty, 60000);
});

ca('9. duong GIAO hang tu phieu san xuat cung mo duoc man va gui dung kho xuat', async function () {
  var p = phieuMau({ material_request_type: 'Manufacture', custom_bep_nhan: 'Bep Lab', set_warehouse: 'Kho Bep - TV' });
  p.items[0].stock_qty = 60000;
  var m = dungMan({ phieu: p });
  var loi = await moTuManChiTiet(m, 'vGiao', { key: 'Manufacture', title: 'Yeu cau san xuat' });
  dung('nut khong nem loi' + (loi ? ': ' + loi.message : ''), !loi);
  dung('co nut Xac nhan giao', !!m.tai.getElementById('rcOk'));
  await bamXacNhan(m);
  var g = m.goiApi.filter(function (x) { return x.duong === 'frappe.client.insert'; })[0];
  bang('kho xuat la kho thanh pham cua bep', g.ts.doc.from_warehouse, 'Kho Lab TP - TV');
  dung('ghi chu giao hang', g.ts.doc.remarks.indexOf('Bếp giao hàng') === 0);
  dung('khong kem lo', !('batch_no' in g.ts.doc.items[0]));
});

/* ---------- chay ---------- */

(async function () {
  console.log('Bo ca kiem HANH VI man Nhan hang va Giao hang\n');
  for (var i = 0; i < CAC_CA.length; i++) {
    var ten = CAC_CA[i][0];
    try {
      await CAC_CA[i][1]();
      ket.dat++;
    } catch (e) {
      ket.hong++;
      ket.loi.push(ten + '\n     ' + e.message);
    }
  }
  ket.loi.forEach(function (l) { console.log('  HONG  ' + l); });
  console.log('\n' + ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' +
    (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
})();

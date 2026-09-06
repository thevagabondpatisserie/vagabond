/* Bo ca kiem HANH VI cho man "Nhan hang" cua phieu dieu chuyen noi bo.
 *
 * Vi sao co tep nay: truoc 06/09/2026 man nay TU chon lo o phia trinh duyet
 * bang ham fefoPick, goi get_batch_qty khong kem co for_stock_levels. Khong
 * co co do thi ERPNext loc bo moi lo qua han, nen bep xin nhan qua phan con
 * han la man hinh bao "khong du lo hang" trong khi kho van con hang. Do that
 * tren site 06/09: NVLT00109 con 330.000 gram o Kho Lab, ham do chi thay
 * 50.000.
 *
 * Nay man hinh gui dong phieu KHONG kem lo, may chu chon. Cac ca duoi day
 * CHAY THAT ham doReceive chu khong do chuoi trong ma nguon (dieu 16).
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/chay_nhan_hang.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');

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
  /* Ham async thi tu khoa `async` nam TRUOC chu `function`, phai keo vao
     khong thi `await` ben trong thanh loi cu phap. */
  if (src.slice(Math.max(0, dau - 6), dau) === 'async ') dau -= 6;
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Ham ' + ten + ' khong dong ngoac');
}

var ket = { dat: 0, hong: 0, loi: [] };

function dung(mo, dk) {
  if (!dk) throw new Error(mo + ': duoc false, mong true');
}
function bang(mo, a, b) {
  if (a !== b) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b));
}

/* ---------- dung moi truong ---------- */

function dungMan(canh) {
  canh = canh || {};
  var goiApi = [];
  var daToast = [];

  var that = {
    console: console,
    Math: Math, JSON: JSON, Date: Date, String: String, Number: Number,
    Array: Array, Object: Object, Promise: Promise,
    setTimeout: setTimeout, parseFloat: parseFloat, parseInt: parseInt,

    COMPANY: 'Cong ty TNHH Patisserie Vagabond',
    S: { me: { full_name: 'Khai' }, user: 'khai@vagabond' },
    rcv: { rows: canh.rows || [] },
    api: function (duong, ts) {
      goiApi.push({ duong: duong, ts: ts });
      if (canh.hongKhiGui && duong === 'frappe.client.insert') {
        return Promise.reject(new Error('gia lap mat mang'));
      }
      if (duong === 'frappe.client.insert') {
        return new Promise(function (r) {
          setTimeout(function () { r({ name: 'MAT-STE-0001' }); }, 5);
        });
      }
      /* Bat chuoc DUNG hanh vi that cua ERPNext: goi khong kem co
         for_stock_levels thi no LOC BO moi lo qua han. Day la diem mau
         chot cua ca bo ca kiem nay - tra ve du 330.000 la ban cu cung
         xanh, va ca kiem tu che mat cai loi no sinh ra de bat. */
      if (String(duong).indexOf('get_batch_qty') >= 0) {
        return Promise.resolve(canh.loConHan || [
          { batch_no: 'NVLT00109-006', qty: 50000, warehouse: 'Kho Lab - TV' },
        ]);
      }
      return Promise.resolve({ name: 'MAT-STE-0001' });
    },
    getList: function (dt, ts) {
      /* Mon THEO LO. Tra ve rong la ban cu di duong "khong theo lo" va
         khong bao gio cham vao fefoPick, tuc ca kiem xanh oan. */
      if (dt === 'Item') {
        var ma = ((ts || {}).filters || {}).name || [];
        var ds = (ma[1] || []).map(function (m) {
          return { name: m, has_batch_no: 1 };
        });
        return Promise.resolve(ds);
      }
      if (dt === 'Batch') {
        return Promise.resolve([
          { name: 'NVLT00109-006', expiry_date: '2026-09-11' },
        ]);
      }
      return Promise.resolve([]);
    },
    confirmSheet: function () { return Promise.resolve(canh.dongY !== 0); },
    busy: function () {},
    toast: function (t) { daToast.push(String(t)); },
    back: function () {},
    render: function () {},
    shortWh: function (k) { return k; },
    num: function (x) { return String(x); },
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
      /* Khong co danh sach CHO_GIA o day: man nay khong goi ham dung san
         nao ngoai nhung cai da khai o tren. Go sai ten la NEM LOI ngay,
         chu khong tra ve ham rong roi de ca kiem xanh oan. */
      throw new ReferenceError('Ten toan cuc "' + k + '" chua duoc dat');
    },
    set: function (t, k, v) { t[k] = v; return true; },
  });

  var kho = docTep('03-kho-chung-tu.js');
  /* Co chan bam kep co the CHUA co (ban truoc 06/09/2026). Thieu no thi tu
     khai lay mot bien rong, de ca kiem van chay duoc tren ban cu va NHIN
     THAY hanh vi that cua no. Neu bat buoc phai co dong khai thi moi ca deu
     do vi "khong thay dong var RCV_DANG_GUI", tuc do vi ha tang chu khong
     phai do hanh vi - do la ca kiem tu lua minh (dieu 15). DUNG go doan
     nay di. */
  var khaiCo = kho.indexOf('var RCV_DANG_GUI') >= 0
    ? layDong(kho, 'var RCV_DANG_GUI')
    : 'var RCV_DANG_GUI = 0;';
  /* Ban CU con ham fefoPick, va doReceive cua no goi thang vao day. Khong
     nap thi ten do thanh chua dat, Proxy nem ReferenceError, doReceive
     nuot vao catch va bao mot cau loi hoan toan khac. Ca kiem van do,
     nhung do vi thieu ham chu khong phai vi cai loi minh dinh bat - lai la
     mot kieu tu lua minh. Nap vao de ban cu chay dung logic cua no. */
  var phanCu = kho.indexOf('function fefoPick(') >= 0 ? layHam(kho, 'fefoPick') : '';
  var ma = [
    khaiCo,
    phanCu,
    layHam(kho, 'errMsg'),
    layHam(kho, 'doReceive'),
  ].join('\n;\n');

  vm.runInNewContext(ma, bay, { filename: '03-kho-chung-tu.js' });
  return { g: that, goiApi: goiApi, toast: daToast, nguon: kho };
}

function dongGui(m) {
  var g = m.goiApi.filter(function (x) { return x.duong === 'frappe.client.insert'; });
  return g.length ? (g[0].ts.doc.items || []) : [];
}

/* ---------- cac ca ---------- */

var CAC_CA = [];
function ca(ten, ham) { CAC_CA.push([ten, ham]); }

var DONG_MAU = [{
  item_code: 'NVLT00109', item_name: 'Bot mi', qty: 60000, uom: 'Gram',
  stock_uom: 'Gram', cf: 1, row: 'dong-1', max: 100000,
}];

ca('1. dong phieu gui di KHONG kem lo, may chu chon lo', async function () {
  var m = dungMan({ rows: DONG_MAU });
  await m.g.doReceive({ name: 'MAT-MR-0001' }, 'Kho Lab - TV', 'Kho Bep - TV');
  var it = dongGui(m);
  bang('mot dong', it.length, 1);
  bang('dung ma', it[0].item_code, 'NVLT00109');
  dung('khong kem batch_no', !('batch_no' in it[0]));
  dung('khong bat co use_serial_batch_fields', !('use_serial_batch_fields' in it[0]));
});

ca('2. khong con hoi get_batch_qty o trinh duyet nua', async function () {
  // Chinh loi goi nay la cho lam bep dung: khong co co for_stock_levels
  // thi ERPNext giau het lo qua han.
  var m = dungMan({ rows: DONG_MAU });
  await m.g.doReceive({ name: 'MAT-MR-0001' }, 'Kho Lab - TV', 'Kho Bep - TV');
  var co = m.goiApi.filter(function (x) {
    return String(x.duong).indexOf('get_batch_qty') >= 0;
  });
  bang('khong goi lan nao', co.length, 0);
  dung('trong ma nguon cung khong con ham fefoPick', m.nguon.indexOf('function fefoPick(') < 0);
});

ca('3. khong bao gio bao "khong du lo hang" o phia man hinh nua', async function () {
  // Cau nay truoc day bat ra khi kho con hang nhung nam o lo qua han.
  var m = dungMan({ rows: DONG_MAU });
  await m.g.doReceive({ name: 'MAT-MR-0001' }, 'Kho Lab - TV', 'Kho Bep - TV');
  dung('khong con cau do', m.toast.join(' ').indexOf('khong du lo hang') < 0);
  dung('khong con cau do co dau', m.toast.join(' ').indexOf('không đủ lô hàng') < 0);
});

ca('4. giu phieu yeu cau, dong yeu cau, don vi va he so quy doi', async function () {
  // Mat material_request_item la phieu yeu cau khong bao gio tu dong lai.
  var m = dungMan({ rows: [{
    item_code: 'NVLT00109', item_name: 'Bot mi', qty: 2, uom: 'Tui',
    stock_uom: 'Gram', cf: 1000, row: 'dong-7', max: 10,
  }] });
  await m.g.doReceive({ name: 'MAT-MR-0009' }, 'Kho Lab - TV', 'Kho Bep - TV');
  var d = dongGui(m)[0];
  bang('phieu yeu cau', d.material_request, 'MAT-MR-0009');
  bang('dong yeu cau', d.material_request_item, 'dong-7');
  bang('don vi nguoi go', d.uom, 'Tui');
  bang('he so quy doi', d.conversion_factor, 1000);
  bang('so luong theo don vi do', d.qty, 2);
});

ca('5. bam kep trong luc dang gui chi tao MOT phieu kho', async function () {
  // Mang chap chon thi nguoi ta bam lai, ma moi lan bam la mot phieu kho.
  var m = dungMan({ rows: DONG_MAU });
  var a = m.g.doReceive({ name: 'MAT-MR-0001' }, 'Kho Lab - TV', 'Kho Bep - TV');
  var b = m.g.doReceive({ name: 'MAT-MR-0001' }, 'Kho Lab - TV', 'Kho Bep - TV');
  await Promise.all([a, b]);
  var so = m.goiApi.filter(function (x) { return x.duong === 'frappe.client.insert'; });
  bang('dung mot lan insert', so.length, 1);
});

ca('6. gui hong thi bo co, bam lai duoc ngay', async function () {
  var m = dungMan({ rows: DONG_MAU, hongKhiGui: 1 });
  await m.g.doReceive({ name: 'MAT-MR-0001' }, 'Kho Lab - TV', 'Kho Bep - TV');
  bang('co da duoc bo', m.g.RCV_DANG_GUI, 0);
  dung('co bao loi cho nguoi ta biet', m.toast.length > 0);
});

ca('7. bam Thoi o hop xac nhan thi khong gui gi', async function () {
  var m = dungMan({ rows: DONG_MAU, dongY: 0 });
  await m.g.doReceive({ name: 'MAT-MR-0001' }, 'Kho Lab - TV', 'Kho Bep - TV');
  bang('khong goi may chu', m.goiApi.length, 0);
});

ca('8. chua go so luong nao thi khong tao phieu rong', async function () {
  var m = dungMan({ rows: [{ item_code: 'X', qty: 0, uom: 'Gram', cf: 1, row: 'r' }] });
  await m.g.doReceive({ name: 'MAT-MR-0001' }, 'Kho Lab - TV', 'Kho Bep - TV');
  bang('khong goi may chu', m.goiApi.length, 0);
});

/* ---------- chay ---------- */

(async function () {
  console.log('Bo ca kiem HANH VI man Nhan hang dieu chuyen noi bo\n');
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

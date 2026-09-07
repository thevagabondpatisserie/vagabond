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

/* Cua may chu duy nhat cua man Nhan hang tu vong 3 cua #222. */
var GUI = 'vagabond.lan_nhan.nhan_theo_phieu';
var TRA = 'vagabond.lan_nhan.tra_lan_nhan';

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
  /* May chu gia va localStorage gia deu co the DUNG CHUNG giua hai lan
     dungMan, de dien duoc canh thoat man roi mo lai, hay tai lai trang. */
  var mayChu = canh.mayChu || { dem: 0, phieu: {} };
  var luuTru = canh.luuTru || {};
  var localStorage = {
    getItem: function (k) { return Object.prototype.hasOwnProperty.call(luuTru, k) ? luuTru[k] : null; },
    setItem: function (k, v) { luuTru[k] = String(v); },
    removeItem: function (k) { delete luuTru[k]; },
  };

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
      /* Tu vong 3 (#222) man hinh gui qua MOT cua may chu kem ma lan nhan.
         Duong cu frappe.client.insert/submit KHONG con duoc goi; goi la ca
         kiem 13 do. */
      if (duong === GUI) {
        var lanGui = goiApi.filter(function (x) { return x.duong === GUI; }).length;
        /* MAY CHU GIA co bo nho theo ma lan nhan, y nhu o duy nhat that:
           cung ma thi tra ve phieu cu (da_co), ma moi thi tao phieu moi.
           Loi gia lap xay ra SAU khi da luu (mat phan hoi) tru khi canh noi
           la loi truoc khi luu (loiTruocKhiLuu) hay may chu tu choi ro
           (loiRoRang: co status 417). */
        var kho = mayChu;
        var ma = ts.ma_lan_nhan;
        var hong = canh.hongKhiGui && (!canh.hongToiLan || lanGui <= canh.hongToiLan);
        if (hong && canh.loiRoRang) {
          var e417 = new Error('Kho xuat khong du hang'); e417.status = 417; e417.exc_type = 'ValidationError';
          return Promise.reject(e417);
        }
        if (hong && canh.loiTruocKhiLuu) return Promise.reject(new Error('gia lap mat mang'));
        var daCo = !!kho.phieu[ma];
        if (!daCo) {
          kho.dem++;
          kho.phieu[ma] = { name: 'MAT-STE-000' + kho.dem, dong: ts.dong, phieu: ts.phieu };
        }
        if (hong) return Promise.reject(new Error('gia lap mat mang sau khi may chu da luu'));
        return new Promise(function (r) {
          setTimeout(function () { r({ ok: 1, name: kho.phieu[ma].name, da_co: daCo ? 1 : 0 }); }, 5);
        });
      }
      if (duong === TRA) {
        /* traHong: may chu van chua voi toi duoc (mat mang keo dai). */
        if (canh.traHong) return Promise.reject(new Error('gia lap mat mang khi tra'));
        var co = mayChu.phieu[ts.ma_lan_nhan];
        return Promise.resolve(co ? { co: 1, name: co.name, docstatus: 1 } : { co: 0 });
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
    /* back() that roi khoi man Nhan hang: khung trong, nut Xac nhan bien
       mat. Khong gia lap the nay thi ca kiem bam duoc nut cua mot man da
       dong, la canh khong co that. */
    back: function () { khung.innerHTML = ''; },
    render: function () {},
    whFind: function (k, loai) { return k === 'lab' ? 'Kho Lab TP - TV' : ''; },
    today: function () { return '2026-09-06'; },
    nowStamp: function () { return '2026-09-06 09:00:00'; },
    localStorage: localStorage,
    isNaN: isNaN,
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
    layNeuCo(kho, 'sinhMaLanNhan'),
    layNeuCo(kho, 'khoaLanCho'),
    layNeuCo(kho, 'docLanCho'),
    layNeuCo(kho, 'ghiLanCho'),
    layNeuCo(kho, 'loiDaChacHong'),
    layNeuCo(kho, 'gioNgan'),
    layNeuCo(kho, 'traLanCho'),
    layNeuCo(kho, 'scrRecvTransfer'),
    layNeuCo(kho, 'fefoPick'),
    kho.indexOf('var RCV_DANG_GUI') >= 0 ? layDong(kho, 'var RCV_DANG_GUI') : 'var RCV_DANG_GUI = 0;',
    layHam(kho, 'errMsg'),
    layHam(kho, 'doReceive'),
  ].join('\n;\n');

  vm.runInNewContext(ma, bay, { filename: '03-kho-chung-tu.js' });
  return { g: that, tai: tai, khung: khung, goiApi: goiApi, toast: daToast, daGo: daGo, nguon: kho, mayChu: mayChu, luuTru: luuTru };
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

function cacLanGui(m) {
  return m.goiApi.filter(function (x) { return x.duong === GUI; });
}

function dongGui(m) {
  var g = cacLanGui(m);
  return g.length ? (g[0].ts.dong || []) : [];
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
  bang('dung mot lan gui', cacLanGui(m).length, 1);
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
  var g = cacLanGui(m)[0];
  bang('kho xuat la kho thanh pham cua bep', g.ts.kho_xuat, 'Kho Lab TP - TV');
  dung('ghi chu giao hang', g.ts.ghi_chu.indexOf('Bếp giao hàng') === 0);
  dung('khong kem lo', !('batch_no' in g.ts.dong[0]));
});

/* ---------- ma lan nhan chong trung (Codex P1 #222, vong 3 va vong 4) ---------- */

function maLan(m, i) { return cacLanGui(m)[i].ts.ma_lan_nhan; }
function soPhieu(m) { return Object.keys(m.mayChu.phieu).length; }
function tongNhan(m) {
  var t = 0;
  Object.keys(m.mayChu.phieu).forEach(function (k) { (m.mayChu.phieu[k].dong || []).forEach(function (d) { t += d.qty; }); });
  return t;
}
function coBangCho(m) { return m.khung.innerHTML.indexOf('chưa rõ kết quả') >= 0; }

/* Canh goc cua Codex: MR 100, nhan 30, may chu DA LUU nhung phan hoi mat. */
function phieu100() {
  var p = phieuMau();
  p.items[0].qty = 100;
  return p;
}
async function guiMatPhanHoi(canh) {
  /* Mac dinh mang VAN DUT sau do (traHong): lan cho khong tu giai quyet
     duoc, nguoi dung con dung truoc man va bam tiep. */
  var m = dungMan(Object.assign({ phieu: phieu100(), hongKhiGui: 1, hongToiLan: 1, traHong: 1 }, canh || {}));
  await moTuManChiTiet(m, 'vRecv');
  goSo(m, 0, 30);
  await bamXacNhan(m);
  bang('lan mot da gui', cacLanGui(m).length, 1);
  bang('may chu gia da luu mot phieu', soPhieu(m), 1);
  dung('man bao loi', m.toast.length > 0);
  return m;
}

ca('10. mat phan hoi sau khi may chu da luu: GO LAI dung 30 roi bam thi khong tao phieu thu hai', async function () {
  var m = await guiMatPhanHoi();
  dung('bay bang lan nhan dang cho', coBangCho(m));
  goSo(m, 0, 30);
  await bamXacNhan(m);
  bang('lan hai gui CUNG ma', maLan(m, 1), maLan(m, 0));
  bang('van chi MOT phieu', soPhieu(m), 1);
  bang('tong nhan 30, khong phai 60', tongNhan(m), 30);
  dung('may chu bao da co', m.toast.join(' ').indexOf('đã được ghi từ trước') >= 0);
  bang('lan cho da xoa', m.g.rcv.cho, null);
});

ca('10b. mat phan hoi nhung mang co lai ngay: may tu tra, bao da co, roi khoi man, khong con nut de bam lai', async function () {
  var m = await guiMatPhanHoi({ traHong: 0 });
  for (var i = 0; i < 20; i++) await new Promise(function (r) { setTimeout(r, 2); });
  var tra = m.goiApi.filter(function (x) { return x.duong === TRA; });
  bang('da tu hoi may chu dung ma', tra.length && tra[0].ts.ma_lan_nhan, maLan(m, 0));
  dung('bao da ghi tu truoc', m.toast.join(' ').indexOf('đã được ghi từ trước') >= 0);
  bang('lan cho da xoa', m.g.rcv.cho, null);
  bang('nut xac nhan khong con', m.tai.getElementById('rcOk'), null);
  bang('mot phieu', soPhieu(m), 1);
});

ca('11. mat phan hoi roi DOI 30 sang 20: o bi khoa, gui lai van la lan cu voi so 30, mot phieu', async function () {
  var m = await guiMatPhanHoi();
  var o = m.tai.querySelector('[data-q="0"]');
  dung('o so luong bi khoa', o.getAttribute('disabled') !== null || o.disabled === true);
  goSo(m, 0, 20);
  await bamXacNhan(m);
  bang('cung ma', maLan(m, 1), maLan(m, 0));
  bang('so gui lai la 30 cua lan cu', cacLanGui(m)[1].ts.dong[0].qty, 30);
  bang('mot phieu', soPhieu(m), 1);
  bang('tong 30', tongNhan(m), 30);
});

ca('12. mat phan hoi roi bam +/- ve lai 30: khong sinh ma moi, mot phieu', async function () {
  var m = await guiMatPhanHoi();
  var ma1 = maLan(m, 0);
  var tru = m.tai.querySelector('[data-m="0"]'), cong = m.tai.querySelector('[data-p="0"]');
  tru.click(); cong.click();
  bang('ma khong doi khi dang cho', m.g.rcv.ma_lan, ma1);
  await bamXacNhan(m);
  bang('cung ma', maLan(m, 1), ma1);
  bang('mot phieu', soPhieu(m), 1);
});

ca('13. thoat man roi MO LAI: lan cho doc lai tu localStorage, may tu tra va bao da co, khong gui them', async function () {
  var m1 = await guiMatPhanHoi();
  var ma1 = maLan(m1, 0);
  /* Mo lai bang mot man moi, dung chung may chu gia va localStorage. */
  var m2 = dungMan({ phieu: phieu100(), mayChu: m1.mayChu, luuTru: m1.luuTru });
  await moTuManChiTiet(m2, 'vRecv');
  for (var i = 0; i < 20; i++) await new Promise(function (r) { setTimeout(r, 2); });
  var tra = m2.goiApi.filter(function (x) { return x.duong === TRA; });
  bang('da hoi may chu dung ma cu', tra.length && tra[0].ts.ma_lan_nhan, ma1);
  bang('khong gui them lan nao', cacLanGui(m2).length, 0);
  dung('bao da ghi tu truoc', m2.toast.join(' ').indexOf('đã được ghi từ trước') >= 0);
  bang('lan cho da xoa khoi localStorage', Object.keys(m2.luuTru).length, 0);
  bang('van mot phieu', soPhieu(m2), 1);
});

ca('14. thoat man roi mo lai khi may chu CHUA co phieu (mat mang truoc khi luu): giu khoa, gui lai dung ma va payload cu', async function () {
  var m1 = await (async function () {
    var m = dungMan({ phieu: phieu100(), hongKhiGui: 1, hongToiLan: 1, loiTruocKhiLuu: 1 });
    await moTuManChiTiet(m, 'vRecv');
    goSo(m, 0, 30);
    await bamXacNhan(m);
    bang('may chu chua co phieu', soPhieu(m), 0);
    return m;
  })();
  var ma1 = maLan(m1, 0);
  var m2 = dungMan({ phieu: phieu100(), mayChu: m1.mayChu, luuTru: m1.luuTru });
  await moTuManChiTiet(m2, 'vRecv');
  for (var i = 0; i < 20; i++) await new Promise(function (r) { setTimeout(r, 2); });
  dung('van bay bang lan nhan dang cho', coBangCho(m2));
  bang('ma phuc hoi dung', m2.g.rcv.ma_lan, ma1);
  await bamXacNhan(m2);
  bang('gui lai cung ma', maLan(m2, 0), ma1);
  bang('payload la 30 cua lan cu', cacLanGui(m2)[0].ts.dong[0].qty, 30);
  bang('mot phieu', soPhieu(m2), 1);
  bang('tong 30', tongNhan(m2), 30);
});

ca('15. sau khi lan cu xac nhan xong, nhan tiep 20 la lan MOI: ma moi, hai phieu, tong 50', async function () {
  var m = await guiMatPhanHoi();
  await bamXacNhan(m);              /* giai quyet lan cu: da co */
  bang('mot phieu sau khi giai quyet', soPhieu(m), 1);
  /* Mo lai man chi tiet: phieu tra ve da nhan 30, con 70. */
  var p = phieu100(); p.items[0].ordered_qty = 30;
  var m2 = dungMan({ phieu: p, mayChu: m.mayChu, luuTru: m.luuTru });
  await moTuManChiTiet(m2, 'vRecv');
  dung('khong con bang cho', !coBangCho(m2));
  bang('so con phai nhan tai lai la 70', m2.g.rcv.rows[0].max, 70);
  goSo(m2, 0, 20);
  await bamXacNhan(m2);
  dung('ma moi khac ma cu', maLan(m2, 0) !== maLan(m, 0));
  bang('hai phieu', soPhieu(m2), 2);
  bang('tong 50', tongNhan(m2), 50);
});

ca('16. may chu TU CHOI ro rang (417): khong co phieu, khong khoa, sua so roi gui lai la lan moi', async function () {
  var m = dungMan({ phieu: phieu100(), hongKhiGui: 1, hongToiLan: 1, loiRoRang: 1 });
  await moTuManChiTiet(m, 'vRecv');
  goSo(m, 0, 30);
  await bamXacNhan(m);
  bang('khong co phieu', soPhieu(m), 0);
  dung('khong khoa', !coBangCho(m));
  bang('localStorage trong', Object.keys(m.luuTru).length, 0);
  var ma1 = maLan(m, 0);
  goSo(m, 0, 20);
  await bamXacNhan(m);
  dung('ma moi', maLan(m, 1) !== ma1);
  bang('mot phieu 20', tongNhan(m), 20);
});

ca('17. gui xong binh thuong: localStorage sach, ma doi, khong con duong frappe.client.insert/submit', async function () {
  var m = dungMan();
  await moTuManChiTiet(m, 'vRecv');
  await bamXacNhan(m);
  bang('localStorage trong', Object.keys(m.luuTru).length, 0);
  dung('ma da doi sang lan moi', m.g.rcv.ma_lan !== maLan(m, 0));
  var cu = m.goiApi.filter(function (x) { return x.duong === 'frappe.client.insert' || x.duong === 'frappe.client.submit'; });
  bang('duong cu khong duoc goi', cu.length, 0);
  var g = cacLanGui(m)[0].ts;
  bang('phieu', g.phieu, 'MAT-MR-0001');
  bang('kho xuat', g.kho_xuat, 'Kho Lab - TV');
  bang('kho nhan', g.kho_nhan, 'Kho Bep - TV');
  dung('dong khong kem batch_no', !('batch_no' in g.dong[0]));
});

ca('18. chua gui lan nao thi sua so luong la lan nhan khac: ma doi (khong lien quan lan cho)', async function () {
  var m = dungMan();
  await moTuManChiTiet(m, 'vRecv');
  var ma1 = m.g.rcv.ma_lan;
  goSo(m, 0, 50000);
  dung('ma doi khi sua so truoc khi gui', m.g.rcv.ma_lan !== ma1);
});

/* Mất phản hồi rồi bị từ chối retry không được quên phiếu đã ghi. */
[401, 403, 500, 417].forEach(function (st) {
  ca('retry lỗi ' + st + ' giữ mã cũ tới khi xác minh', async function () {
    var m = await guiMatPhanHoi();
    var apiCu = m.g.api, ma = m.g.rcv.cho.ma_lan;
    m.g.api = function (duong, ts) {
      if (duong === GUI) { var e = new Error('Từ chối retry'); e.status = st; e.exc_type = 'ValidationError'; return Promise.reject(e); }
      return apiCu(duong, ts);
    };
    await bamXacNhan(m);
    bang('giữ mã', m.g.rcv.cho && m.g.rcv.cho.ma_lan, ma);
    bang('giữ bản bền', Object.keys(m.luuTru).length, 1);
    m.g.api = apiCu;
    await bamXacNhan(m);
    bang('chỉ một phiếu', soPhieu(m), 1);
    bang('chỉ nhận 30', tongNhan(m), 30);
  });
});
['setItem', 'getItem'].forEach(function (ham) {
  ca('lỗi bộ nhớ ' + ham + ' không phát request nhận', async function () {
    var m = dungMan({ phieu: phieu100() });
    await moTuManChiTiet(m, 'vRecv');
    m.g.localStorage[ham] = function () { throw new Error('Bộ nhớ không dùng được'); };
    await bamXacNhan(m);
    bang('không gửi', cacLanGui(m).length, 0);
    bang('không tạo phiếu', soPhieu(m), 0);
  });
});
[0, 1, 2].forEach(function (trangThai) {
  ca('tra phiếu có docstatus ' + trangThai + ' chỉ xác nhận phiếu ghi sổ', async function () {
    var m = await guiMatPhanHoi();
    var apiCu = m.g.api;
    m.g.api = function (duong, ts) {
      return duong === TRA ? Promise.resolve({ co: 1, name: 'PHIEU-THU', docstatus: trangThai }) : apiCu(duong, ts);
    };
    await m.g.traLanCho(m.g.rcv.mr);
    bang('pending theo trạng thái', !!m.g.rcv.cho, trangThai !== 1);
    dung('chữ đúng trạng thái', m.toast.some(function (t) { return t.indexOf(trangThai === 0 ? 'còn nháp' : trangThai === 2 ? 'đã huỷ' : 'đã được ghi') >= 0; }));
  });
});
ca('dữ liệu chờ hỏng không mở đường nhận mới', async function () {
  var m = dungMan();
  m.g.localStorage.getItem = function () { return '{hong'; };
  await moTuManChiTiet(m, 'vRecv');
  dung('không có nút nhận', !m.tai.getElementById('rcOk'));
  bang('không gửi', cacLanGui(m).length, 0);
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

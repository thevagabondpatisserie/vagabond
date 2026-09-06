/* Bo ca kiem HANH VI cho man TAO LENH SAN XUAT (#206).
 *
 * Cung loi voi hanh_vi/chay.js: khong do chuoi trong ma nguon, ma CHAY THAT
 * ham `scrMfgNew` tren DOM gia roi ban su kien nhu nguoi that go va bam.
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/chay_san_xuat.js
 * Ma tra ve 0 la dat het.
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');

function docTep(ten) { return fs.readFileSync(path.join(BEP, ten), 'utf8'); }

function layHam(src, ten) {
  var dau = src.indexOf('function ' + ten + '(');
  if (dau < 0) throw new Error('Khong thay ham ' + ten);
  /* Ham async thi phai keo theo ca chu `async`, khong thi `await` ben trong
     thanh loi cu phap. Da vap dung cai nay khi lay scrMfgNew. */
  if (src.slice(Math.max(0, dau - 6), dau) === 'async ') dau -= 6;
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Ham ' + ten + ' khong dong ngoac');
}

var ket = { dat: 0, hong: 0, loi: [] };

function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) {
  if (a !== b) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b));
}

/* ---------- dung moi truong ---------- */

/* Nhu cau san xuat gia lap. Dung dang ma mfgDemand() that tra ve. */
function nhuCauMau() {
  return [
    { code: 'TP001', name: 'Bánh Su Kem', uom: 'Cái', image: '', need: 10, wo: 0, ton: 2, bom: 'BOM-TP001', qty: 8, on: 0 },
    { code: 'TP002', name: 'Matcha Croissant', uom: 'Cái', image: '', need: 4, wo: 0, ton: 0, bom: 'BOM-TP002', qty: 4, on: 0 },
    { code: 'TP003', name: 'Bánh Plain Croissant, Full size', uom: 'Món', image: '', need: 570, wo: 0, ton: 0, bom: 'BOM-TP003', qty: 570, on: 0 },
    { code: 'TP004', name: 'Bánh Chưa Có Công Thức', uom: 'Cái', image: '', need: 3, wo: 0, ton: 0, bom: '', qty: 3, on: 0 },
  ];
}

function dungMan(canh) {
  canh = canh || {};
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);

  var goiWO = [];
  var goiList = [];

  var that = {
    document: tai,
    window: {},
    console: console,
    Math: Math, JSON: JSON, Date: Date, String: String, Number: Number,
    Array: Array, Object: Object, RegExp: RegExp, Promise: Promise,
    setTimeout: setTimeout, clearTimeout: clearTimeout, isNaN: isNaN,
    parseInt: parseInt, parseFloat: parseFloat,

    /* frame that ve than man va chan man vao hai cho khac nhau; o day gop
       vao mot khung cho don gian, nhung KHONG duoc bo chan man di vi nut
       "Tao N lenh san xuat" nam trong do. */
    frame: function (tieuDe, html, o) {
      khung.innerHTML = html + ((o && o.footer) ? o.footer : '');
      return khung;
    },
    go: function (fn) { return fn; },
    busy: function () { }, toast: function (s) { that._toast.push(s); },
    COMPANY: 'VGB',
    mfg: { src: 'KHO NVL - VGB', fg: 'KHO TP - VGB' },
    mfgInitWh: function () { },
    mfgWhCard: function () { return '<div class="whc"></div>'; },
    mfgWhTap: function () { return false; },
    num: function (n) { return String(n); },
    r3: function (n) { return Math.round(n * 1000) / 1000; },
    leavesUnder: function () { return ['Bán ra', 'Sản xuất']; },

    /* Nhu cau san xuat: tra ban SAO moi lan, de moi ca mot the gioi rieng. */
    mfgDemand: function () { return Promise.resolve(canh.rows || nhuCauMau()); },

    /* Danh muc hang hoa cho phan "Mon khac trong danh muc". */
    getList: function (dt, ts) {
      goiList.push({ dt: dt, ts: ts });
      if (canh.getList) return canh.getList(dt, ts);
      return Promise.resolve(canh.danhMuc || []);
    },
    mfgLoadItem: function (ma) {
      return Promise.resolve((canh.item && canh.item[ma]) || { item_name: 'Món ' + ma, stock_uom: 'Cái', image: '' });
    },
    bomOf: function (ds) {
      var ra = {};
      ds.forEach(function (m) { if (!canh.khongBom || canh.khongBom.indexOf(m) < 0) ra[m] = { name: 'BOM-' + m }; });
      return Promise.resolve(ra);
    },
    stockOf: function (ds) { var ra = {}; ds.forEach(function (m) { ra[m] = 0; }); return Promise.resolve(ra); },
    mfgCreateWO: function (row) {
      goiWO.push({ code: row.code, qty: row.qty });
      if (canh.woLoi) return Promise.reject(new Error('may chu tu choi'));
      return Promise.resolve('WO-' + row.code);
    },
    scrMfgBtp: function () { },
    scrMfgDeclare: function () { },
    errMsg: function (e) { return String((e && e.message) || e); },
  };
  that._toast = [];
  that.globalThis = that;

  /* Ten toan cuc chua dat thi NEM LOI, tru danh sach duoi. Cung ly do nhu
     hanh_vi/chay.js: mot cai bay nuot moi ten se lam ca kiem xanh oan khi
     go sai ten ham. */
  var CHO_GIA = ['hasRole', 'today', 'addDays', 'inChunks', 'openWoQty', 'scanBarcode', 'itemByBarcode'];
  var daGia = {};
  var bay = new Proxy(that, {
    has: function () { return true; },
    get: function (t, k) {
      if (k in t) return t[k];
      if (typeof k === 'symbol') return undefined;
      if (k in globalThis) return globalThis[k];
      if (CHO_GIA.indexOf(k) < 0) {
        throw new ReferenceError('Ten toan cuc "' + k + '" chua duoc dat va khong nam trong CHO_GIA.');
      }
      daGia[k] = (daGia[k] || 0) + 1;
      return function () { return ''; };
    },
    set: function (t, k, v) { t[k] = v; return true; },
  });

  var nen = docTep('00-nen.js');
  var sx = docTep('05-san-xuat.js');
  /* Nap ham THAT, khong bia lai mot ban khac. */
  var ma = [
    layHam(nen, 'h'),
    layHam(sx, 'mfgKhongDau'),
    layHam(sx, 'mfgKhopMon'),
    layHam(sx, 'mfgLocGoiY'),
    layHam(sx, 'mfgViTriMon'),
    layHam(sx, 'mfgDemSeGui'),
    layHam(sx, 'mfgPickItem'),
    'var mfgN = { horizon: 0, rows: null, q: "", seq: 0, tmr: null, dangGui: 0 };',
    layHam(sx, 'scrMfgNew'),
  ].join('\n;\n');

  vm.runInNewContext(ma, bay, { filename: '05-san-xuat.js' });
  return { g: that, tai: tai, khung: khung, goiWO: goiWO, goiList: goiList };
}

function nhip(n) {
  var p = Promise.resolve();
  for (var i = 0; i < (n || 1); i++) p = p.then(function () { return new Promise(function (r) { setTimeout(r, 0); }); });
  return p;
}

function theoTt(m, tt, gt) {
  return m.tai.querySelectorAll('[' + tt + ']').filter(function (e) {
    return e.getAttribute(tt) === gt;
  })[0] || null;
}
function demTt(m, tt) { return m.tai.querySelectorAll('[' + tt + ']').length; }

/* O tim co nhip cho 260ms truoc khi ve lai, nen phai cho THAT chu khong the
   cho bang vai nhip vi mo. Cho du roi moi doc man. */
async function cho(ms) { await new Promise(function (r) { setTimeout(r, ms); }); }

async function goTim(m, chu) {
  var o = m.tai.getElementById('mfgQ');
  dung('co o tim tren man', !!o);
  o.value = chu;
  o.dispatchEvent(dg.suKien('input', {}, o));
  await cho(320);
  await nhip(6);
  return o;
}

/* ---------- cac ca ---------- */

async function chayHet() {
  await ca('1. mo man moi: khong mon nao tu chon san, va co o tim', async function () {
    var m = dungMan({});
    await m.g.scrMfgNew();
    await nhip(3);
    dung('co o tim', !!m.tai.getElementById('mfgQ'));
    bang('khong mon nao duoc chon san', demTt(m, 'data-bo'), 0);
    dung('co cau moi go de them', m.khung.innerHTML.indexOf('Chưa chọn món nào') > 0);
    var nut = m.tai.getElementById('mGo');
    dung('nut tao dang khoa', nut.getAttribute('disabled') !== null || /disabled/.test(m.khung.innerHTML));
  });

  await ca('2. tim mot mon trong nhu cau roi them: mon vao danh sach da chon', async function () {
    var m = dungMan({});
    await m.g.scrMfgNew();
    await nhip(3);
    await goTim(m, 'su kem');
    var them = theoTt(m, 'data-them', 'TP001');
    dung('tim ra Banh Su Kem', !!them);
    bang('chi ra dung mot mon trong nhu cau', demTt(m, 'data-them'), 1);
    them.click();
    await nhip(2);
    dung('mon da vao danh sach da chon', !!theoTt(m, 'data-bo', 'TP001'));
    dung('dem dung mot mon', m.khung.innerHTML.indexOf('Đã chọn 1 món') > 0);
  });

  await ca('2b. go khong dau van tim ra mon co dau', async function () {
    var m = dungMan({});
    await m.g.scrMfgNew();
    await nhip(3);
    await goTim(m, 'banh su');
    dung('go khong dau ra dung mon', !!theoTt(m, 'data-them', 'TP001'));
  });

  await ca('3. them mon NGOAI nhu cau qua danh muc hang hoa', async function () {
    var m = dungMan({ danhMuc: [{ name: 'TP999', item_name: 'Bánh Ngoài Nhu Cầu', stock_uom: 'Cái', image: '' }] });
    await m.g.scrMfgNew();
    await nhip(3);
    await goTim(m, 'ngoai nhu cau');
    var ng = theoTt(m, 'data-ngoai', 'TP999');
    dung('co goi y mon ngoai danh muc', !!ng);
    ng.click();
    await nhip(6);
    dung('mon ngoai da vao danh sach da chon', !!theoTt(m, 'data-bo', 'TP999'));
  });

  await ca('4. them mot mon DANG CO trong nhu cau thi giu nguyen so lieu cua dong do', async function () {
    /* Cho Codex neu tren #206: duong mAdd cu bao "Mon nay da co trong danh
       sach" roi bat bep tu di cuon tim. Nay tim ra la CHON CHINH DONG DO, va
       phai giu Phong ban can / Da co lenh / Ton thanh pham, chu khong dung
       mot dong moi rong tuech. */
    var m = dungMan({});
    m.g._toast.length = 0;
    await m.g.scrMfgNew();
    await nhip(3);
    await goTim(m, 'su kem');
    theoTt(m, 'data-them', 'TP001').click();
    await nhip(2);
    bang('chi mot dong cho ma do', demTt(m, 'data-bo'), 1);
    var r = m.g.mfgN.rows.filter(function (x) { return x.code === 'TP001'; });
    bang('khong nhan doi ma mon trong mang', r.length, 1);
    bang('van giu Phong ban can', r[0].need, 10);
    bang('van giu Ton thanh pham', r[0].ton, 2);
    bang('van giu so luong du kien', r[0].qty, 8);
    dung('man co hien lai con so Phong ban can', m.khung.innerHTML.indexOf('Phòng ban cần') > 0);
    bang('khong bao "da co trong danh sach"',
      m.g._toast.filter(function (s) { return /đã có trong danh sách/i.test(String(s)); }).length, 0);

    /* Tim lai chinh mon do: no khong duoc hien lai o phan goi y nua. */
    await goTim(m, 'su kem');
    dung('mon da them khong bay lai o goi y', theoTt(m, 'data-them', 'TP001') === null);
    bang('va van chi mot dong o danh sach da chon', demTt(m, 'data-bo'), 1);
  });

  await ca('4b. chip Chon tat ca van con, va chi chon mon CO cong thuc', async function () {
    /* Anh Viet chot 21/08/2026: khong tu tick san mon nao, nhung phai co mot
       cham de chon het khi bep that su muon lam het luot. Man moi khong trai
       danh sach ra nua nhung duong do phai con. */
    var m = dungMan({});
    await m.g.scrMfgNew();
    await nhip(3);
    var chip = theoTt(m, 'data-all', '1');
    dung('con chip chon tat ca', !!chip);
    dung('chip noi ro co bao nhieu mon', m.khung.innerHTML.indexOf('Chọn tất cả 3 món đang cần') > 0);
    bang('luc dau chua chon mon nao', demTt(m, 'data-bo'), 0);
    chip.click();
    await nhip(3);
    bang('chon het thi ra dung 3 mon co cong thuc', demTt(m, 'data-bo'), 3);
    bang('mon thieu cong thuc khong bi keo vao', theoTt(m, 'data-bo', 'TP004'), null);
    bang('so lenh se tao dung bang 3', m.g.mfgDemSeGui(m.g.mfgN.rows), 3);
    theoTt(m, 'data-all', '1').click();
    await nhip(3);
    bang('bam lan nua thi bo het', demTt(m, 'data-bo'), 0);
  });

  await ca('5. doi tu khoa KHONG lam mat mon da chon va so luong da nhap', async function () {
    var m = dungMan({});
    await m.g.scrMfgNew();
    await nhip(3);
    await goTim(m, 'su kem');
    theoTt(m, 'data-them', 'TP001').click();
    await nhip(2);
    var o = m.tai.querySelectorAll('[data-q]')[0];
    dung('co o so luong cua mon da chon', !!o);
    o.value = '37';
    o.dispatchEvent(dg.suKien('input', {}, o));
    await goTim(m, 'croissant');
    dung('mon cu van con trong danh sach da chon', !!theoTt(m, 'data-bo', 'TP001'));
    var o2 = m.tai.querySelectorAll('[data-q]')[0];
    bang('so luong da nhap van con', String(o2.value), '37');
    await goTim(m, '');
    bang('xoa het tu khoa cung khong mat', String(m.tai.querySelectorAll('[data-q]')[0].value), '37');
  });

  await ca('6. bo mot mon da chon', async function () {
    var m = dungMan({});
    await m.g.scrMfgNew();
    await nhip(3);
    await goTim(m, 'su kem');
    theoTt(m, 'data-them', 'TP001').click();
    await nhip(2);
    bang('dang co mot mon', demTt(m, 'data-bo'), 1);
    theoTt(m, 'data-bo', 'TP001').click();
    await nhip(2);
    bang('bo xong thi khong con mon nao', demTt(m, 'data-bo'), 0);
    await goTim(m, 'su kem');
    dung('mon quay lai nguon goi y, khong mat han', !!theoTt(m, 'data-them', 'TP001'));
  });

  await ca('7. mon THIEU CONG THUC: bao ro va khong tinh vao so lenh se tao', async function () {
    var m = dungMan({});
    await m.g.scrMfgNew();
    await nhip(3);
    await goTim(m, 'chua co cong thuc');
    theoTt(m, 'data-them', 'TP004').click();
    await nhip(2);
    dung('co bao chua co cong thuc', m.khung.innerHTML.indexOf('Chưa có công thức') > 0);
    dung('co duong khai nguyen lieu da dung', demTt(m, 'data-dec') > 0);
    bang('khong dem vao so lenh se tao', m.g.mfgDemSeGui(m.g.mfgN.rows), 0);
  });

  await ca('8. so luong khong hop le thi khong duoc gui', async function () {
    var m = dungMan({});
    await m.g.scrMfgNew();
    await nhip(3);
    await goTim(m, 'su kem');
    theoTt(m, 'data-them', 'TP001').click();
    await nhip(2);
    var o = m.tai.querySelectorAll('[data-q]')[0];
    o.value = '0';
    o.dispatchEvent(dg.suKien('input', {}, o));
    bang('so luong 0 thi khong tinh', m.g.mfgDemSeGui(m.g.mfgN.rows), 0);
    o.value = 'abc';
    o.dispatchEvent(dg.suKien('input', {}, o));
    bang('go chu cung khong tinh', m.g.mfgDemSeGui(m.g.mfgN.rows), 0);
    m.g._toast.length = 0;
    await m.tai.getElementById('mGo').onclick();
    await nhip(3);
    bang('khong goi tao lenh nao', m.goiWO.length, 0);
  });

  await ca('9. phan hoi tim ve NGUOC THU TU thi khong de len ket qua moi', async function () {
    var cho = [];
    var m = dungMan({
      getList: function (dt, ts) {
        var q = String((ts.or_filters && ts.or_filters.item_name && ts.or_filters.item_name[1]) || '');
        return new Promise(function (r) { cho.push({ q: q, r: r }); });
      },
    });
    await m.g.scrMfgNew();
    await nhip(3);
    await goTim(m, 'aaa');
    await goTim(m, 'bbb');
    dung('co hai lan hoi danh muc', cho.length >= 2);
    var cuoi = cho[cho.length - 1], dau = cho[cho.length - 2];
    /* Tra loi lan MOI truoc, roi moi tra loi lan CU. */
    cuoi.r([{ name: 'MOI', item_name: 'Ket qua MOI', stock_uom: 'Cái', image: '' }]);
    await nhip(3);
    dau.r([{ name: 'CU', item_name: 'Ket qua CU', stock_uom: 'Cái', image: '' }]);
    await nhip(3);
    dung('van la ket qua cua lan go moi nhat', !!theoTt(m, 'data-ngoai', 'MOI'));
    dung('ket qua cu KHONG de len', theoTt(m, 'data-ngoai', 'CU') === null);
  });

  await ca('10. bam tao: chi gui cac mon da chon, dung so luong', async function () {
    var m = dungMan({});
    await m.g.scrMfgNew();
    await nhip(3);
    await goTim(m, 'su kem');
    theoTt(m, 'data-them', 'TP001').click();
    await nhip(2);
    await goTim(m, 'matcha');
    theoTt(m, 'data-them', 'TP002').click();
    await nhip(2);
    await m.tai.getElementById('mGo').onclick();
    await nhip(6);
    bang('gui dung hai lenh', m.goiWO.length, 2);
    var ma = m.goiWO.map(function (x) { return x.code; }).sort().join(',');
    bang('dung hai ma da chon', ma, 'TP001,TP002');
    dung('khong gui mon khong chon', ma.indexOf('TP003') < 0);
  });

  await ca('11. bam LAP nut tao thi khong ra hai bo lenh', async function () {
    /* Bep bam hai lan vi lan dau tuong chua an. Lan bam thu hai roi vao dung
       luc lan mot con dang cho may chu, nen phai giu lenh dau lai giua chung
       moi mo ra dung khe do.

       DEM SO LAN GOI, khong dem so lenh da xong: neu dem so lenh xong thi ca
       kiem van xanh khi bo phep chan, vi lenh cua lan bam thu nhat con treo
       chua tra loi. Da dot bien va bat duoc dung cho nay. */
    var soGoi = 0, moKhoa = [];
    var m = dungMan({});
    m.g.mfgCreateWO = function (row) {
      soGoi++;
      return new Promise(function (r) { moKhoa.push(function () { r('WO-' + row.code); }); });
    };
    await m.g.scrMfgNew();
    await nhip(3);
    await goTim(m, 'su kem');
    theoTt(m, 'data-them', 'TP001').click();
    await nhip(2);
    var nut = m.tai.getElementById('mGo');
    nut.onclick();
    await nhip(3);
    bang('lan bam dau da goi tao lenh', soGoi, 1);
    nut.onclick();
    await nhip(3);
    bang('lan bam thu hai KHONG goi them lan nao', soGoi, 1);
    moKhoa.forEach(function (f) { f(); });
    await nhip(6);
    bang('tong cong van chi mot lan goi', soGoi, 1);
  });
}

var HAN_GIO_MS = 5000;

async function ca(ten, ham) {
  try {
    var dongHo;
    await Promise.race([
      ham(),
      new Promise(function (_, hong) {
        dongHo = setTimeout(function () { hong(new Error('Ca treo qua ' + HAN_GIO_MS + 'ms')); }, HAN_GIO_MS);
      }),
    ]);
    clearTimeout(dongHo);
    ket.dat++;
  } catch (e) {
    ket.hong++;
    ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 4).join('\n         ') : String(e)));
  }
}

chayHet().then(function () {
  console.log('Bo ca kiem HANH VI man tao lenh san xuat');
  ket.loi.forEach(function (d) { console.log('  HONG  ' + d); });
  console.log('');
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
}, function (e) {
  console.log('VO KHUNG: ' + (e && e.stack ? e.stack : e));
  process.exit(1);
});

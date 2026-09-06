/* Bộ ca kiểm HÀNH VI cho màn TẠO LỆNH SẢN XUẤT (#206).
 *
 * Cùng lối với hanh_vi/chay.js: không dò chuỗi trong mã nguồn, mà CHẠY THẬT
 * hàm `scrMfgNew` trên DOM giả rồi bắn sự kiện như người thật gõ và bấm.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/chay_san_xuat.js
 * Mã trả về 0 là đạt hết.
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
  /* Hàm async thì phải kéo theo cả chữ `async`, không thì `await` bên trong
     thành lỗi cú pháp. Đã vấp đúng cái này khi lấy scrMfgNew. */
  if (src.slice(Math.max(0, dau - 6), dau) === 'async ') dau -= 6;
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Ham ' + ten + ' khong dong ngoac');
}

function layDong(src, dau) {
  var i = src.indexOf(dau);
  if (i < 0) throw new Error('Khong thay dong ' + dau);
  return src.slice(i, src.indexOf('\n', i));
}

var ket = { dat: 0, hong: 0, loi: [] };

function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) {
  if (a !== b) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b));
}

/* ---------- dựng môi trường ---------- */

/* Nhu cầu sản xuất giả lập. Đúng dạng mà mfgDemand() thật trả về. */
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

    /* frame thật vẽ thân màn và chân màn vào hai chỗ khác nhau; ở đây gộp
       vào một khung cho đơn giản, nhưng KHÔNG được bỏ chân màn đi vì nút
       "Tạo N lệnh sản xuất" nằm trong đó. */
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

    /* Nhu cầu sản xuất: trả bản SAO mỗi lần, để mỗi ca một thế giới riêng. */
    mfgDemand: function () { return Promise.resolve(canh.rows || nhuCauMau()); },

    /* Danh mục hàng hoá cho phần "Món khác trong danh mục". */
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

  /* Tên toàn cục chưa đặt thì NÉM LỖI, trừ danh sách dưới. Cùng lý do như
     hanh_vi/chay.js: một cái bẫy nuốt mọi tên sẽ làm ca kiểm xanh oan khi
     gõ sai tên hàm. */
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
  /* Nạp hàm THẬT, không bịa lại một bản khác. */
  var ma = [
    layHam(nen, 'h'),
    layHam(sx, 'mfgKhongDau'),
    layHam(sx, 'mfgKhopMon'),
    layHam(sx, 'mfgLocGoiY'),
    layHam(sx, 'mfgViTriMon'),
    layHam(sx, 'mfgDemSeGui'),
    layHam(sx, 'mfgPickItem'),
    /* Lấy đúng dòng khai báo trạng thái trong nguồn, không chép tay một bản
       khác: bản chép tay đã lệch một lần khi nguồn thêm khoá dangThem. */
    layDong(sx, 'var mfgN = {'),
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

/* Ô tìm có nhịp chờ 260ms trước khi vẽ lại, nên phải chờ THẬT chứ không thể
   chờ bằng vài nhịp vi mô. Chờ đủ rồi mới đọc màn. */
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

/* ---------- các ca ---------- */

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
    /* Chỗ Codex nêu trên #206: tấm tìm cũ báo "Món này đã có trong danh
       sách" rồi bắt bếp tự đi cuộn tìm. Nay tìm ra là CHỌN CHÍNH DÒNG ĐÓ, và
       phải giữ Phòng ban cần / Đã có lệnh / Tồn thành phẩm, chứ không dựng
       một dòng mới rỗng tuếch. */
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

    /* Tìm lại chính món đó: nó không được hiện lại ở phần gợi ý nữa. */
    await goTim(m, 'su kem');
    dung('mon da them khong bay lai o goi y', theoTt(m, 'data-them', 'TP001') === null);
    bang('va van chi mot dong o danh sach da chon', demTt(m, 'data-bo'), 1);
  });

  await ca('4b. chip Chon tat ca van con, va chi chon mon CO cong thuc', async function () {
    /* Anh Việt chốt 21/08/2026: không tự tick sẵn món nào, nhưng phải có một
       chạm để chọn hết khi bếp thật sự muốn làm hết lượt. Màn mới không trải
       danh sách ra nữa nhưng đường đó phải còn. */
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
    /* Trả lời lần MỚI trước, rồi mới trả lời lần CŨ. */
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
    /* Bếp bấm hai lần vì lần đầu tưởng chưa ăn. Lần bấm thứ hai rơi vào đúng
       lúc lần một còn đang chờ máy chủ, nên phải giữ lệnh đầu lại giữa chừng
       mới mở ra đúng khe đó.

       ĐẾM SỐ LẦN GỌI, không đếm số lệnh đã xong: nếu đếm số lệnh xong thì ca
       kiểm vẫn xanh khi bỏ phép chặn, vì lệnh của lần bấm thứ nhất còn treo
       chưa trả lời. Đã đột biến và bắt được đúng chỗ này. */
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

  /* ----- Vòng 2, các finding của Codex trên #215 ----- */

  await ca('12. bam KEP mon ngoai trong luc dang tai thi van chi mot dong, mot lenh', async function () {
    /* Codex [P1] trên #215: hai lần bấm cùng một món ngoài trước khi
       Item/BOM/tồn về thì mảng có hai dòng cùng mã, rồi gửi hai lệnh. Đo
       trên SHA 642349d: rows=2, WO CALLS=2. Giữ Item treo để mở đúng khe. */
    var giu = [];
    var m = dungMan({ danhMuc: [{ name: 'EXT', item_name: 'Món Ngoài', stock_uom: 'Cái', image: '' }] });
    m.g.mfgLoadItem = function (ma) {
      return new Promise(function (r) { giu.push(function () { r({ item_name: 'Món ' + ma, stock_uom: 'Cái', image: '' }); }); });
    };
    await m.g.scrMfgNew();
    await nhip(3);
    await goTim(m, 'ngoai');
    var ng = theoTt(m, 'data-ngoai', 'EXT');
    dung('co goi y mon ngoai', !!ng);
    ng.click(); ng.click();
    await nhip(2);
    bang('chi mot lan hoi Item cho mot ma', giu.length, 1);
    giu.forEach(function (f) { f(); });
    await nhip(8);
    bang('chi mot dong cho ma EXT', m.g.mfgN.rows.filter(function (r) { return r.code === 'EXT'; }).length, 1);
    bang('man cung chi mot dong', demTt(m, 'data-bo'), 1);
    m.tai.getElementById('mGo').onclick();
    await nhip(8);
    bang('gui dung MOT lenh', JSON.stringify(m.goiWO), '[{"code":"EXT","qty":1}]');
  });

  await ca('13. so luong doi thi nut tao doi theo ngay, qua go va qua cong tru, hai chieu', async function () {
    /* Codex [P2] trên #215. Đo trên 642349d: gõ 0 mà nút vẫn "Tạo 1 lệnh",
       vẽ lại ở 0 rồi gõ 2 thì nút vẫn khoá. KHÔNG gọi thêm draw() hay vẽ
       lại nào để "cho chắc": vẽ lại chính là cái sẽ chữa lỗi trước khi ca
       kiểm nhìn (điều 15). */
    var m = dungMan({});
    await m.g.scrMfgNew();
    await nhip(3);
    await goTim(m, 'su kem');
    theoTt(m, 'data-them', 'TP001').click();
    await nhip(2);
    function nut() { return m.tai.getElementById('mGo'); }
    function khoa() { return nut().getAttribute('disabled') !== null; }
    bang('chon xong: nut mo, dem 1', nut().textContent.replace(/\s+/g, ' ').trim(), 'Tạo 1 lệnh sản xuất');
    var o = theoTt(m, 'data-q', '0');
    o.value = '0'; o.dispatchEvent(dg.suKien('input', {}, o));
    await nhip(1);
    dung('go 0: nut khoa', khoa());
    dung('go 0: khong con so 1 tren nut', nut().textContent.indexOf('1') < 0);
    o.value = '2'; o.dispatchEvent(dg.suKien('input', {}, o));
    await nhip(1);
    dung('go 2: nut mo lai', !khoa());
    bang('go 2: dem 1', nut().textContent.replace(/\s+/g, ' ').trim(), 'Tạo 1 lệnh sản xuất');
    /* Cộng trừ cũng phải đồng bộ với cùng một hàm tính nút. */
    theoTt(m, 'data-m', '0').click(); theoTt(m, 'data-m', '0').click();
    await nhip(1);
    bang('tru ve 0 trong mang', m.g.mfgN.rows[0].qty, 0);
    dung('tru ve 0: nut khoa', khoa());
    theoTt(m, 'data-p', '0').click();
    await nhip(1);
    dung('cong len 1: nut mo', !khoa());
    /* Vẽ lại ở 0 rồi gõ dương: đúng chuỗi Codex mô tả. */
    theoTt(m, 'data-m', '0').click();
    await goTim(m, 'su kem ');
    dung('sau ve lai o 0: nut khoa', khoa());
    o = theoTt(m, 'data-q', '0');
    o.value = '3'; o.dispatchEvent(dg.suKien('input', {}, o));
    await nhip(1);
    dung('go 3 sau ve lai: nut mo', !khoa());
  });

  await ca('14. phan hoi cua tu khoa CU ve trong cua so cho cua tu khoa moi thi bi bo', async function () {
    /* Codex [P2] trên #215: seq chỉ tăng khi lượt tìm phát, không tăng lúc
       gõ, nên OLD về trước 260ms của NEW vẫn được vẽ. Đo trên 642349d:
       STALE BEFORE DEBOUNCE true. Ca 9 không bao phủ vì ở đó cả hai lượt đã
       phát rồi mới trả. */
    var treo = null;
    var m = dungMan({ getList: function (dt, ts) {
      var q = ts.or_filters.name[1];
      if (q.indexOf('old') >= 0) return new Promise(function (r) { treo = function () { r([{ name: 'OLD1', item_name: 'Món Old', stock_uom: 'Cái' }]); }; });
      return Promise.resolve([{ name: 'NEW1', item_name: 'Món New', stock_uom: 'Cái' }]);
    } });
    await m.g.scrMfgNew();
    await nhip(3);
    await goTim(m, 'old');
    dung('luot old dang treo', typeof treo === 'function');
    var o = m.tai.getElementById('mfgQ');
    o.value = 'new'; o.dispatchEvent(dg.suKien('input', {}, o));
    await nhip(2);
    treo();
    await nhip(4);
    dung('OLD ve trong cua so cho: KHONG duoc hien', theoTt(m, 'data-ngoai', 'OLD1') === null);
    await cho(320); await nhip(6);
    dung('het cua so cho: NEW hien', !!theoTt(m, 'data-ngoai', 'NEW1'));
    dung('OLD van khong hien', theoTt(m, 'data-ngoai', 'OLD1') === null);
    /* Xoá về dưới hai ký tự thì phần danh mục phải trống. */
    await goTim(m, 'n');
    dung('duoi hai ky tu: khong con goi y danh muc', demTt(m, 'data-ngoai') === 0);
  });

  await ca('15. tim danh muc LOI thi bao loi co nut thu lai, giu danh sach da chon', async function () {
    /* Codex trên #215: catch thành [] nên lỗi mạng hay quyền trông y như
       "không tìm thấy". */
    var hong = true;
    var m = dungMan({ getList: function () {
      if (hong) return Promise.reject(new Error('mất kết nối'));
      return Promise.resolve([{ name: 'TP777', item_name: 'Món Về Sau', stock_uom: 'Cái' }]);
    } });
    await m.g.scrMfgNew();
    await nhip(3);
    await goTim(m, 'su kem');
    theoTt(m, 'data-them', 'TP001').click();
    await nhip(2);
    await goTim(m, 've sau');
    /* Đọc qua textContent của vùng danh mục, không đọc innerHTML của khung:
       innerHTML của khung là chuỗi lúc vẽ, không phản ánh phần đổi tại chỗ. */
    function chuNgoai() { var o = m.tai.getElementById('mNgoai'); return o ? o.textContent : ''; }
    dung('co cau bao loi noi ro la khong tim duoc trong danh muc', chuNgoai().indexOf('Không tìm được trong danh mục') >= 0);
    dung('cau loi mang theo ly do', chuNgoai().indexOf('mất kết nối') >= 0);
    var lai = m.tai.getElementById('mNgoaiLai');
    dung('co nut thu lai', !!lai);
    dung('danh sach da chon van con', !!theoTt(m, 'data-bo', 'TP001'));
    dung('khong hien nhu "khong tim thay"', chuNgoai().indexOf('Không tìm thấy hàng hoá') < 0);
    hong = false;
    lai.onclick();
    await nhip(6);
    dung('thu lai thanh cong thi ra ket qua', !!theoTt(m, 'data-ngoai', 'TP777'));
    dung('cau loi bien mat', chuNgoai().indexOf('Không tìm được trong danh mục') < 0);
  });

  await ca('16. quet ma canh o tim: mon trong nhu cau thi chon dong do, mon ngoai thi them, khong ra thi bao', async function () {
    /* Codex trên #215 và AGENTS.md mục 5: có mã thì có nút quét. Dùng lại
       đúng đường scanBarcode + itemByBarcode của các màn khác. */
    var maQuet = null, bang_ma = { '893001': 'TP002', '893999': 'TP555' };
    var m = dungMan({});
    m.g.scanBarcode = function () { return Promise.resolve(maQuet); };
    m.g.itemByBarcode = function (code) { return Promise.resolve(bang_ma[code] || null); };
    await m.g.scrMfgNew();
    await nhip(3);
    var q = m.tai.getElementById('mfgScan');
    dung('co nut quet canh o tim', !!q);
    maQuet = '893001';
    await q.onclick(); await nhip(6);
    dung('mon trong nhu cau: chon chinh dong do', !!theoTt(m, 'data-bo', 'TP002'));
    bang('khong nhan doi', m.g.mfgN.rows.filter(function (r) { return r.code === 'TP002'; }).length, 1);
    bang('giu Phong ban can cua dong do', m.g.mfgN.rows.filter(function (r) { return r.code === 'TP002'; })[0].need, 4);
    maQuet = '893999';
    await q.onclick(); await nhip(8);
    dung('mon ngoai nhu cau: duoc them', !!theoTt(m, 'data-bo', 'TP555'));
    m.g._toast.length = 0;
    maQuet = '000000';
    await q.onclick(); await nhip(4);
    bang('ma la thi bao cau nguoi doc hieu', m.g._toast.filter(function (s) { return /mã vạch/i.test(String(s)); }).length, 1);
    bang('va khong them gi', m.g.mfgN.rows.length, 5);
    maQuet = null;
    await q.onclick(); await nhip(2);
    bang('huy quet thi im', m.g.mfgN.rows.length, 5);
  });

  await ca('17. nut them/bo mang lop vung bam 44 va CSS chung khai dung 44 (chot tinh)', async function () {
    /* DOM giả không tính layout, nên đây là PHÉP DÒ TĨNH, chỉ chốt hai đầu
       nối: nút có lớp, và lớp có khai 44. Bằng chứng kích thước thật lấy từ
       Chromium, đính trên PR, không lấy từ ca này. */
    var m = dungMan({});
    await m.g.scrMfgNew();
    await nhip(3);
    var them = theoTt(m, 'data-them', 'TP001');
    dung('nut them mang lop rk44', /\brk44\b/.test(them.getAttribute('class') || ''));
    them.click(); await nhip(2);
    var bo = theoTt(m, 'data-bo', 'TP001');
    dung('nut bo mang lop rk44', /\brk44\b/.test(bo.getAttribute('class') || ''));
    var css = docTep('00-nen.js');
    var luat = css.match(/\.rok\.rk44\{([^}]*)\}/);
    dung('00-nen.js co luat .rok.rk44', !!luat);
    dung('luat khai rong 44', /width:44px/.test(luat[1]));
    dung('luat khai cao 44', /height:44px/.test(luat[1]));
    dung('chu khong trong suot', !/color:transparent/.test(luat[1]) && /color:#/.test(luat[1]));
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

/* Cho phép tệp khác (probe tái hiện, ca kiểm bổ sung) mượn lại khung dựng
   màn mà không tự chạy hết bộ ca. Chạy trực tiếp thì mới chạy hết. */
module.exports = { dungMan: dungMan, nhip: nhip, theoTt: theoTt, demTt: demTt, cho: cho, goTim: goTim, dung: dung, bang: bang };

if (require.main === module) chayHet().then(function () {
  console.log('Bo ca kiem HANH VI man tao lenh san xuat');
  ket.loi.forEach(function (d) { console.log('  HONG  ' + d); });
  console.log('');
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
}, function (e) {
  console.log('VO KHUNG: ' + (e && e.stack ? e.stack : e));
  process.exit(1);
});

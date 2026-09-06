/* Bo ca kiem HANH VI cho man danh sach ho so thanh toan.
 *
 * Khac han bo kiem thu tang khung: cho kia do CHUOI trong ma nguon, cho nay
 * CHAY THAT ham `scrHoSoTT`, dung DOM gia, roi ban su kien nhu nguoi that go
 * va bam. Codex neu tren PR #207: "hai ca moi dang kiem tra su co mat cua
 * chuoi code, chua chay chuoi tuong tac". Tep nay la cau tra loi cho cho do.
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/chay.js
 * Ma tra ve 0 la dat het. Chay duoc tren may CI vi buoc `node --check` cua
 * cong da chung minh may do co node, va tep nay khong can goi ngoai nao.
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');

function docTep(ten) { return fs.readFileSync(path.join(BEP, ten), 'utf8'); }

/* Lay dung mot ham that tu tep khac, khong bia lai. Bia lai la kiem thu tu
   noi chuyen voi chinh minh: `posChipNut` phai la ban that thi cai chip moi
   mang dung thuoc tinh `data-hstkc` ma man hinh dua vao. */
function layHam(src, ten) {
  var dau = src.indexOf('function ' + ten + '(');
  if (dau < 0) throw new Error('Khong thay ham ' + ten);
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
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);

  var goiApi = [];
  var daGo = [];

  var that = {
    document: tai,
    window: {},
    console: console,
    Math: Math, JSON: JSON, Date: Date, String: String, Number: Number,
    Array: Array, Object: Object, RegExp: RegExp, Promise: Promise,
    setTimeout: setTimeout, clearTimeout: clearTimeout, isNaN: isNaN, parseInt: parseInt,

    frame: function (tieuDe, html) { khung.innerHTML = html; return khung; },
    api: function (duong, ts) {
      goiApi.push({ duong: duong, ts: JSON.parse(JSON.stringify(ts || {})) });
      if (duong === 'vagabond.ho_so_tt.danh_sach') return Promise.resolve(canh.danhSach || { rows: [], nhan: {}, quyen: {}, tk_chi_co: [] });
      if (duong === 'vagabond.ho_so_tt.xuat_excel') return Promise.resolve({ ten_file: 'x.xlsx', b64: '' });
      if (duong === 'vagabond.ho_so_tt.ds_tai_khoan') return Promise.resolve({ tk: canh.tk || [] });
      return Promise.resolve({});
    },
    go: function (fn) { daGo.push(fn); return fn(); },
    busy: function () {}, toast: function () {}, baoTin: function () {},
    bcTaiVe: function () {}, vnSt: function (x) { return x || ''; },
    hoiChon: function (tieuDe, moTa, ds, dangChon) {
      that._hoiChon = { tieuDe: tieuDe, moTa: moTa, ds: ds, dangChon: dangChon };
      return Promise.resolve(canh.chon === undefined ? null : canh.chon);
    },
  };
  that.globalThis = that;

  /* Bat ky ten toan cuc nao chua dat thi tra ve mot ham rong, thay vi no
     ReferenceError. Man nay to va goi sang nhieu tep khac; ca kiem chi quan
     tam toi mot khuc, khong dung lai ca ung dung. */
  var bay = new Proxy(that, {
    has: function () { return true; },
    get: function (t, k) {
      if (k in t) return t[k];
      if (typeof k === 'symbol') return undefined;
      return function () { return ''; };
    },
    set: function (t, k, v) { t[k] = v; return true; },
  });

  var nen = docTep('00-nen.js');
  var ma = [
    layHam(nen, 'h'),
    layHam(nen, 'money'),
    layHam(docTep('09-tinh-tien-quay.js'), 'posChipNut'),
    layHam(docTep('09-tinh-tien-quay.js'), 'locTim'),
    layHam(docTep('13-khuyen-mai.js'), 'kmHangChip'),
    docTep('19-ho-so-tt.js'),
  ].join('\n;\n');

  vm.runInNewContext(ma, bay, { filename: '19-ho-so-tt.js' });
  return { g: that, tai: tai, khung: khung, goiApi: goiApi, daGo: daGo };
}

function chipTheo(m, thuocTinh, giaTri) {
  return m.tai.querySelectorAll('[' + thuocTinh + ']').filter(function (e) {
    return e.getAttribute(thuocTinh) === giaTri;
  })[0] || null;
}

var HAI_TK = {
  rows: [{ name: 'HS-1', ten_ncc: 'A', trang_thai: 'Da thanh toan', tong_tien: 100, ngay_thanh_toan: '2026-09-01', tk_chi: '6277 - VGB' }],
  nhan: {}, quyen: { lap: 1 },
  tk_chi_co: ['6277 - VGB', '1111 - VGB'],
};

async function chayHet() {
  await caAsync('A. dang loc tai khoan khong con trong ky: con chip bo loc va co loi giai thich', async function () {
    var m = dungMan({ danhSach: { rows: [], nhan: {}, quyen: {}, tk_chi_co: ['1111 - VGB'] } });
    m.g.hsTkChi = '6277 - VGB';
    await m.g.scrHoSoTT();
    var chipBo = chipTheo(m, 'data-hstkc', '');
    dung('van con chip "Moi tai khoan chi" de bam bo loc', !!chipBo);
    dung('chip cua tai khoan dang chon van co mat', !!chipTheo(m, 'data-hstkc', '6277 - VGB'));
    dung('co cau giai thich vi sao rong', m.khung.innerHTML.indexOf('Mọi tài khoản chi</b> để bỏ lọc') > 0);
    chipBo.click();
    bang('bam vao la bo loc that', m.g.hsTkChi, '');
  });

  await caAsync('A2. tai khoan dang chon CO trong ky thi khong bay cau giai thich thua', async function () {
    var m = dungMan({ danhSach: HAI_TK });
    m.g.hsTkChi = '6277 - VGB';
    await m.g.scrHoSoTT();
    dung('khong co cau giai thich', m.khung.innerHTML.indexOf('Mọi tài khoản chi</b> để bỏ lọc') < 0);
  });

  await caAsync('B. dang ap A, go B roi bam chip: giu B trong o, may chu van dung A', async function () {
    var m = dungMan({ danhSach: HAI_TK });
    m.g.hsTim = 'alpha'; m.g.hsTimGo = 'alpha';
    await m.g.scrHoSoTT();
    var o = m.tai.getElementById('hsTimO');
    bang('o tim tra lai chu dang ap', o.value, 'alpha');
    o.value = 'beta';
    o.dispatchEvent(dg.suKien('input', {}, o));
    bang('go toi dau ghi lai toi do', m.g.hsTimGo, 'beta');
    bang('chua bam Enter thi chu dang AP van la cai cu', m.g.hsTim, 'alpha');
    m.goiApi.length = 0;
    chipTheo(m, 'data-hsng', '30').click();
    await new Promise(function (r) { setTimeout(r, 0); });
    var goi = m.goiApi.filter(function (x) { return x.duong === 'vagabond.ho_so_tt.danh_sach'; });
    dung('bam chip co goi lai may chu', goi.length > 0);
    bang('may chu van nhan tu khoa CU', goi[goi.length - 1].ts.tu_khoa, 'alpha');
    bang('o tim khong mat chu vua go', m.tai.getElementById('hsTimO').value, 'beta');
  });

  await caAsync('B2. bam Enter thi moi ap, va may chu nhan chu moi', async function () {
    var m = dungMan({ danhSach: HAI_TK });
    m.g.hsTim = 'alpha'; m.g.hsTimGo = 'alpha';
    await m.g.scrHoSoTT();
    var o = m.tai.getElementById('hsTimO');
    o.value = 'beta';
    o.dispatchEvent(dg.suKien('input', {}, o));
    m.goiApi.length = 0;
    o.dispatchEvent(dg.suKien('keydown', { key: 'Enter' }, o));
    await new Promise(function (r) { setTimeout(r, 0); });
    bang('chu da ap doi sang chu moi', m.g.hsTim, 'beta');
    var goi = m.goiApi.filter(function (x) { return x.duong === 'vagabond.ho_so_tt.danh_sach'; });
    bang('may chu nhan chu moi', goi[goi.length - 1].ts.tu_khoa, 'beta');
  });

  await caAsync('B3. xuat Excel gui dung chu DA AP, khong phai chu dang go', async function () {
    var m = dungMan({ danhSach: HAI_TK });
    m.g.hsTim = 'alpha'; m.g.hsTimGo = 'alpha'; m.g.hsTkChi = '6277 - VGB'; m.g.hsCpThue = 'Hop le';
    await m.g.scrHoSoTT();
    var o = m.tai.getElementById('hsTimO');
    o.value = 'beta';
    o.dispatchEvent(dg.suKien('input', {}, o));
    m.goiApi.length = 0;
    await m.tai.getElementById('hsXuat').onclick();
    var goi = m.goiApi.filter(function (x) { return x.duong === 'vagabond.ho_so_tt.xuat_excel' })[0];
    dung('co goi xuat Excel', !!goi);
    bang('gui tu khoa da ap', goi.ts.tu_khoa, 'alpha');
    bang('gui ca o loc tai khoan', goi.ts.tk_chi, '6277 - VGB');
    bang('gui ca o loc chi phi thue', goi.ts.loai_cp_thue, 'Hop le');
  });

  await caAsync('C. go va xoa thi dong nhac doi NGAY, khong goi may chu, khong ve lai man', async function () {
    var m = dungMan({ danhSach: HAI_TK });
    m.g.hsTim = 'alpha'; m.g.hsTimGo = 'alpha';
    await m.g.scrHoSoTT();
    var o = m.tai.getElementById('hsTimO');
    var nhac = m.tai.getElementById('hsTimNhac');
    dung('luc ve man dong nhac noi dang loc theo chu nao', nhac.innerHTML.indexOf('Đang lọc theo') === 0);
    m.goiApi.length = 0;
    var soLanGo = m.daGo.length;

    o.value = 'alphab';
    o.dispatchEvent(dg.suKien('input', {}, o));
    dung('go them mot chu la dong nhac doi ngay',
      m.tai.getElementById('hsTimNhac').innerHTML.indexOf('Đã gõ nhưng chưa tìm') === 0);

    o.value = '';
    o.dispatchEvent(dg.suKien('input', {}, o));
    dung('xoa het chu thi nhac bam Enter de bo loc',
      m.tai.getElementById('hsTimNhac').innerHTML.indexOf('Bấm <b>Enter</b> để bỏ lọc') > 0);

    o.value = 'alpha';
    o.dispatchEvent(dg.suKien('input', {}, o));
    dung('go lai dung chu dang ap thi ve lai trang thai dang loc',
      m.tai.getElementById('hsTimNhac').innerHTML.indexOf('Đang lọc theo') === 0);

    bang('suot ca doan go khong goi may chu lan nao', m.goiApi.length, 0);
    bang('va khong ve lai ca man', m.daGo.length, soLanGo);
    dung('o nhap van la dung cai cu, tuc la con nguyen cho con tro',
      m.tai.getElementById('hsTimO') === o);
  });

  await caAsync('C2. chu nguoi ta go duoc loc the truoc khi dap vao dong nhac', async function () {
    var m = dungMan({ danhSach: HAI_TK });
    await m.g.scrHoSoTT();
    var o = m.tai.getElementById('hsTimO');
    o.value = '<img src=x>';
    o.dispatchEvent(dg.suKien('input', {}, o));
    var html = m.tai.getElementById('hsTimNhac').innerHTML;
    dung('the bi loc thanh chu', html.indexOf('&lt;img') > 0);
    dung('khong con the that trong dong nhac', html.indexOf('<img') < 0);
  });

  await caAsync('D. o chon tai khoan No: bay ca danh muc, bam Thoi tra ve duoc', async function () {
    var tk = [];
    for (var i = 0; i < 158; i++) tk.push({ ma: '6' + (100 + i) + ' - VGB', ten: 'Tai khoan ' + i, loai: 'Expense' });
    var m = dungMan({ tk: tk, chon: null });
    var kq = await m.g.huChonTaiKhoan('Tài khoản Nợ', '');
    var goi = m.goiApi.filter(function (x) { return x.duong === 'vagabond.ho_so_tt.ds_tai_khoan' })[0];
    dung('co hoi may chu danh muc tai khoan', !!goi);
    bang('xin LAY HET chu khong cat', goi.ts.gioi_han, 0);
    bang('bay du ca danh muc vao o chon', m.g._hoiChon.ds.length, 158);
    bang('bam Thoi thi tra ve null', kq, null);
  });

  await caAsync('D2. chon mot dong thi tra ve dung ma tai khoan, va khong hoi may chu lan hai', async function () {
    var m = dungMan({ tk: [{ ma: '6277 - VGB', ten: 'Chi phi dich vu mua ngoai', loai: 'Expense' }], chon: '6277 - VGB' });
    var a = await m.g.huChonTaiKhoan('Tài khoản Nợ', '');
    bang('tra ve ma tai khoan', a, '6277 - VGB');
    var soGoi = m.goiApi.length;
    await m.g.huChonTaiKhoan('Tài khoản Nợ', '');
    bang('lan hai dung lai danh muc da tai, khong hoi lai', m.goiApi.length, soGoi);
  });
}

async function caAsync(ten, ham) {
  try {
    await ham();
    ket.dat++;
  } catch (e) {
    ket.hong++;
    ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0,4).join('\n         ') : String(e)));
  }
}

chayHet().then(function () {
  console.log('Bo ca kiem HANH VI man ho so thanh toan');
  ket.loi.forEach(function (d) { console.log('  HONG  ' + d); });
  console.log('');
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
}, function (e) {
  console.log('VO KHUNG: ' + (e && e.stack ? e.stack : e));
  process.exit(1);
});

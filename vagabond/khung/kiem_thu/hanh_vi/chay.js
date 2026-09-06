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
/* Lay nguyen mot dong khai bao that, de con so nguong khong bi go lai o day
   roi lech voi ban that. */
function layDong(src, dau) {
  var i = src.indexOf(dau);
  if (i < 0) throw new Error('Khong thay dong ' + dau);
  return src.slice(i, src.indexOf('\n', i));
}

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
  };
  that.globalThis = that;

  /* Ten toan cuc chua dat thi tra ve ham rong - NHUNG chi trong danh sach
     duoi day. Codex neu vong ba tren PR #207: mot cai bay nuot moi ten chua
     biet se lam ca kiem xanh oan khi go sai ten ham. Nen danh sach phai viet
     ra, va ten ngoai danh sach thi NEM LOI.

     Moi ten o day deu la ham that o tep khac, ma man dang kiem co goi toi
     nhung khong phai la thu dang kiem. Them ten moi vao day la mot quyet
     dinh co y thuc, khong phai chuyen tu dong. */
  var CHO_GIA = [
    'busy', 'toast', 'baoTin', 'bcTaiVe', 'vnSt', 'hoiChu', 'hoiCo', 'hoiNhap',
    'hopKhungDong', 'sheet', 'nutDong', 'kmChipNut', 'posHangNut', 'icon',
    'scrHoSoTTView', 'scrPayView', 'scrChiCongTyTao', 'scrHoanUngTao',
    'scrTraTruocTao', 'scrHoSoTTTao', 'ttReset', 'huChonTep', 'napTep',
    'quyenCo', 'ngayVn', 'nowVn', 'tepTaiVe', 'moTep', 'hienAnh',
  ];
  var daGia = {};
  var bay = new Proxy(that, {
    has: function () { return true; },
    get: function (t, k) {
      if (k in t) return t[k];
      if (typeof k === 'symbol') return undefined;
      /* Do san co cua JavaScript (Error, Symbol, Intl...) thi tra ve do
         that, khong tinh la ten chua dat. */
      if (k in globalThis) return globalThis[k];
      if (CHO_GIA.indexOf(k) < 0) {
        throw new ReferenceError(
          'Ten toan cuc "' + k + '" chua duoc dat va cung khong nam trong ' +
          'danh sach CHO_GIA. Go sai ten, hay quen nap ham that?');
      }
      daGia[k] = (daGia[k] || 0) + 1;
      return function () { return ''; };
    },
    set: function (t, k, v) { t[k] = v; return true; },
  });
  that._daGia = daGia;

  var nen = docTep('00-nen.js');
  var hop = docTep('07-hop-thoai.js');
  /* Nap ham THAT, khong bia lai. `hoiChon` va bo o tim cua no la thu Codex
     doi phai chay that chu khong duoc thay bang stub: co chay that thi moi
     biet go tim co loc dung khong, bam Thoi co tra ve null khong. */
  var ma = [
    layHam(nen, 'h'),
    layHam(nen, 'money'),
    layHam(docTep('09-tinh-tien-quay.js'), 'posChipNut'),
    layHam(docTep('09-tinh-tien-quay.js'), 'locTim'),
    layHam(docTep('09-tinh-tien-quay.js'), 'locHang'),
    layHam(docTep('13-khuyen-mai.js'), 'kmHangChip'),
    layHam(docTep('11-khach-ca-hop-dong.js'), 'mvKhongDau'),
    layDong(hop, 'var VGB_NGUONG_TIM'),
    layHam(hop, 'hopKhung'),
    layHam(hop, 'vgbCanOTim'),
    layHam(hop, 'vgbOTim'),
    layHam(hop, 'vgbNoiOTim'),
    layHam(hop, 'hoiChon'),
    docTep('19-ho-so-tt.js'),
  ].join('\n;\n');

  vm.runInNewContext(ma, bay, { filename: '19-ho-so-tt.js' });
  return { g: that, tai: tai, khung: khung, goiApi: goiApi, daGo: daGo };
}

/* Hop chon hien ra sau mot vai nhip vi `huChonTaiKhoan` con doi may chu tra
   danh muc. Cho toi khi thay nut Thoi, toi da 50 nhip. */
async function choHopChon(m) {
  for (var i = 0; i < 50; i++) {
    if (m.tai.querySelectorAll('[data-hcx]').length) return;
    await new Promise(function (r) { setTimeout(r, 0); });
  }
  throw new Error('Cho mai khong thay hop chon hien ra');
}

function soDongHien(m) {
  return m.tai.querySelectorAll('[data-hc]').filter(function (e) {
    return e.style.display !== 'none';
  }).length;
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

  await caAsync('D. o chon tai khoan No: dung HOP CHON THAT, go tim loc dung, bam Thoi tra ve null', async function () {
    var tk = [];
    for (var i = 0; i < 158; i++) tk.push({ ma: '6' + (100 + i) + ' - VGB', ten: 'Tai khoan ' + i, loai: 'Expense' });
    tk[7] = { ma: '6277 - VGB', ten: 'Chi phí dịch vụ mua ngoài', loai: 'Expense' };
    var m = dungMan({ tk: tk });
    var hua = m.g.huChonTaiKhoan('Tài khoản Nợ', '');
    await choHopChon(m);

    var goi = m.goiApi.filter(function (x) { return x.duong === 'vagabond.ho_so_tt.ds_tai_khoan' })[0];
    dung('co hoi may chu danh muc tai khoan', !!goi);
    bang('xin LAY HET chu khong cat', goi.ts.gioi_han, 0);
    bang('bay du ca danh muc thanh dong bam duoc', m.tai.querySelectorAll('[data-hc]').length, 158);

    var oTim = m.tai.getElementById('hcTim');
    dung('danh sach dai thi co o tim', !!oTim);
    oTim.value = '6277';
    oTim.dispatchEvent(dg.suKien('input', {}, oTim));
    bang('go so hieu thi loc con dung mot dong', soDongHien(m), 1);

    // Bo loc di qua mvKhongDau CA HAI PHIA, nen phai thu ca hai chieu: go co
    // dau (loc phia nguoi go) va go khong dau (loc phia danh muc).
    oTim.value = 'dịch vụ';
    oTim.dispatchEvent(dg.suKien('input', {}, oTim));
    bang('go co dau van tim ra', soDongHien(m), 1);
    oTim.value = 'dich vu';
    oTim.dispatchEvent(dg.suKien('input', {}, oTim));
    bang('go khong dau cung tim ra', soDongHien(m), 1);

    oTim.value = 'khong co gi khop';
    oTim.dispatchEvent(dg.suKien('input', {}, oTim));
    bang('go bay ba thi khong con dong nao', soDongHien(m), 0);
    dung('va co cau bao khong khop',
      m.tai.getElementById('hcTimTrong').style.display !== 'none');

    m.tai.querySelectorAll('[data-hcx]')[0].click();
    var kq = await hua;
    bang('bam Thoi thi tra ve null', kq, null);
    bang('bam Thoi xong thi hop dong lai', m.tai.querySelectorAll('[data-hc]').length, 0);
  });

  await caAsync('D2. bam mot dong trong hop chon that thi tra ve dung ma tai khoan', async function () {
    var tk = [];
    for (var i = 0; i < 20; i++) tk.push({ ma: '6' + (100 + i) + ' - VGB', ten: 'Tai khoan ' + i, loai: 'Expense' });
    var m = dungMan({ tk: tk });
    var hua = m.g.huChonTaiKhoan('Tài khoản Nợ', '');
    await choHopChon(m);
    var dong = m.tai.querySelectorAll('[data-hc]').filter(function (e) {
      return e.getAttribute('data-hc') === '6105 - VGB';
    })[0];
    dung('tim duoc dong can bam', !!dong);
    dong.click();
    bang('tra ve ma tai khoan cua dong da bam', await hua, '6105 - VGB');

    // Lan hai: danh muc da tai roi thi khong hoi may chu nua.
    var soGoi = m.goiApi.length;
    var hua2 = m.g.huChonTaiKhoan('Tài khoản Nợ', '6105 - VGB');
    await choHopChon(m);
    bang('lan hai khong hoi lai may chu', m.goiApi.length, soGoi);
    m.tai.querySelectorAll('[data-hcx]')[0].click();
    bang('van bam Thoi ra duoc', await hua2, null);
  });

  await caAsync('D3. danh muc rong thi bao chu, khong bay hop rong', async function () {
    var m = dungMan({ tk: [] });
    var kq = await m.g.huChonTaiKhoan('Tài khoản Nợ', '');
    bang('tra ve null', kq, null);
    bang('khong bay hop chon nao', m.tai.querySelectorAll('[data-hc]').length, 0);
  });
}

/* Moi ca co han gio. Khong co han thi mot ca treo (vi du hop chon hien ra ma
   khong ai bam) se lam ca tien trinh thoat lang le voi ma 0, tuc la HONG ma
   bao XANH. Da vap dung cai do khi thu lam hong canh danh muc rong. */
var HAN_GIO_MS = 5000;

async function caAsync(ten, ham) {
  try {
    var dongHo;
    await Promise.race([
      ham(),
      new Promise(function (_, hong) {
        dongHo = setTimeout(function () {
          hong(new Error('Ca treo qua ' + HAN_GIO_MS + 'ms. Thuong la dang cho ' +
            'mot lua chon ma khong ai bam, hoac mot loi hua khong bao gio xong.'));
        }, HAN_GIO_MS);
      }),
    ]);
    clearTimeout(dongHo);
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

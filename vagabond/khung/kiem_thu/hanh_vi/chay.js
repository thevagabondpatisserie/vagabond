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

function layNeuCo(src, ten) {
  return src.indexOf('function ' + ten + '(') >= 0 ? layHam(src, ten) : '';
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
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);

  var goiApi = [];
  var daGo = [];
  var dangCho = [];

  var that = {
    document: tai,
    window: {},
    console: console,
    Math: Math, JSON: JSON, Date: Date, String: String, Number: Number,
    Array: Array, Object: Object, RegExp: RegExp, Promise: Promise,
    setTimeout: setTimeout, clearTimeout: clearTimeout, isNaN: isNaN, parseInt: parseInt,

    /* Chan ca phan chan trang vao cung mot khung. Man Chi tu TK cong ty dat
       hai nut Luu o chan va goi thang `getElementById('huLuu').onclick`, nen
       bo chan trang di la ca kiem no ngay o dong do chu khong phai o cho
       dang kiem. */
    frame: function (tieuDe, html, o) {
      khung.innerHTML = html + ((o && o.footer) || '');
      return khung;
    },
    api: function (duong, ts) {
      goiApi.push({ duong: duong, ts: JSON.parse(JSON.stringify(ts || {})) });
      if (duong === 'vagabond.ho_so_tt.danh_sach') return Promise.resolve(canh.danhSach || { rows: [], nhan: {}, quyen: {}, tk_chi_co: [] });
      if (duong === 'vagabond.ho_so_tt.xuat_excel') return Promise.resolve({ ten_file: 'x.xlsx', b64: '' });
      if (duong === 'vagabond.ho_so_tt.ds_tai_khoan') return Promise.resolve({ tk: canh.tk || [] });
      if (duong === 'vagabond.ho_so_tt.ds_tk_cong_ty') return Promise.resolve({ tk: canh.tkCty || [{ ma: '11211 - VGB', ten: 'MB', so_tk: '31561568' }] });
      if (duong === 'vagabond.ho_so_tt.ds_ncc_con_no') return Promise.resolve({ ncc: canh.nccNo || [] });
      if (duong === 'vagabond.ho_so_tt.ds_ncc_chon') return Promise.resolve({ ncc: canh.nccChon || [] });
      if (duong === 'vagabond.ho_so_tt.hoa_don_cho_tra') return Promise.resolve(canh.hoaDon || { rows: [], tong: 0, qua_han: 0 });
      if (duong === 'vagabond.ho_so_tt.ds_tk_hoan_ung') return Promise.resolve(canh.tkHoan || { tk: [], doan: 0 });
      if (duong === 'vagabond.ho_so_tt.ds_nguoi_ung') {
        /* Tra ve theo tu khoa de ca kiem chung minh duoc rang bam Enter la
           HOI THAT may chu, chu khong phai loc lai tren danh sach cu. Ham
           `nguoiUngTim` duoc tra ve mang HOAC mot promise, de ca kiem thu
           tu phan hoi giu duoc phan hoi lai roi tha ra sau. */
        var q = (ts && ts.tu_khoa) || '';
        if (q && canh.nguoiUngTim) {
          return Promise.resolve(canh.nguoiUngTim(q)).then(function (ds) { return { ncc: ds }; });
        }
        return Promise.resolve({ ncc: canh.nguoiUng || [] });
      }
      if (duong === 'frappe.client.get_value') {
        /* Tra theo MA, doc lap voi danh sach goi y. `canh.supplier` la
           {ma: {supplier_name, disabled}}; khong co thi null nhu Frappe. */
        var ma = ts && ts.filters && ts.filters.name;
        var hs = (canh.supplier || {})[ma];
        if (canh.supplierHong) return Promise.reject(new Error('mat mang'));
        return Promise.resolve(hs ? { name: ma, supplier_name: hs.supplier_name, disabled: hs.disabled || 0 } : null);
      }
      return Promise.resolve({});
    },
    hasRole: function (v) { return (canh.vai || ['Accounts Manager']).indexOf(v) >= 0; },
    /* Man hinh ve lai bang mot ham ASYNC. Goi xong tra ve ngay mot loi hua
       con dang chay, nen doc DOM lien sau do la doc phai ban cu. Bai hoc
       vong bon cua PR #213: giu lai loi hua de kich ban CHO duoc. */
    go: function (fn) {
      daGo.push(fn);
      var ra = fn();
      if (ra && typeof ra.then === 'function') dangCho.push(ra);
      return ra;
    },
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
    'scrHoSoTTView', 'scrPayView', 'scrTraTruocTao',
    'ttReset', 'huChonTep', 'napTep',
    'quyenCo', 'ngayVn', 'nowVn', 'tepTaiVe', 'moTep', 'hienAnh',
    'nccTaoNhanh', 'hoiNhap', 'hopKhung', 'locHang', 'locTim',
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
    layHam(nen, 'soTien'),
    layHam(nen, 'tienChuoi'),
    layHam(nen, 'tienGo'),
    layHam(docTep('09-tinh-tien-quay.js'), 'posChipNut'),
    layHam(docTep('09-tinh-tien-quay.js'), 'locTim'),
    layHam(docTep('09-tinh-tien-quay.js'), 'locHang'),
    layHam(docTep('13-khuyen-mai.js'), 'kmHangChip'),
    layHam(docTep('11-khach-ca-hop-dong.js'), 'mvKhongDau'),
    /* Quyen tao nha cung cap la ham THAT, khong bia lai: bay nut ra ma bam
       vao bi tu choi quyen thi con te hon la khong co nut. */
    layHam(docTep('01-khung-app.js'), 'coQuyenMua'),
    layDong(hop, 'var VGB_NGUONG_TIM'),
    layHam(hop, 'hopKhung'),
    layHam(hop, 'vgbCanOTim'),
    layHam(hop, 'vgbOTim'),
    layHam(hop, 'vgbNoiOTim'),
    layHam(hop, 'hoiChon'),
    /* Giu ben da chon va luot hoi may chu: phan dung chung moi (#217 P1).
       Nap NEU CO, de chay duoc tren ban cu chua co chung va nhin thay dung
       hanh vi cua ban cu (do vi the sai, khong phai do vi thieu ham). */
    hop.indexOf('var VGB_CHON') >= 0 ? layDong(hop, 'var VGB_CHON') : '',
    layNeuCo(hop, 'vgbGiuChon'),
    layNeuCo(hop, 'vgbBenDaChon'),
    layNeuCo(hop, 'vgbTraBenTheoMa'),
    layNeuCo(hop, 'vgbLuot'),
    layNeuCo(hop, 'vgbChonLaiGoLoi'),
    docTep('19-ho-so-tt.js'),
  ].join('\n;\n');

  vm.runInNewContext(ma, bay, { filename: '19-ho-so-tt.js' });
  return { g: that, tai: tai, khung: khung, goiApi: goiApi, daGo: daGo,
    dangCho: dangCho };
}

/* Cho het phan ve lai dang treo va TRA VE so lan da cho. Tra ve so de kich
   ban khang dinh duoc rang minh that su co cho mot cai gi do, chu khong
   phai goi cho vui roi doc ket qua cu. */
async function choVeLai(m) {
  var dem = 0;
  for (var vong = 0; vong < 50 && m.dangCho.length; vong++) {
    var ds = m.dangCho.splice(0, m.dangCho.length);
    dem += ds.length;
    await Promise.all(ds);
    await new Promise(function (r) { setTimeout(r, 0); });
  }
  return dem;
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
  await caAsync('PR263. chip viec can lam dem dung, loc giao va bo loc duoc khi rong', async function () {
    var canh = { danhSach: { rows: [
      {name:'APP-A', trang_thai:'Da thanh toan', tong_tien:100, chip_nghiep_vu:['da_chi','cho_hoa_don']},
      {name:'APP-B', trang_thai:'Da duyet', tong_tien:200, chip_nghiep_vu:['thieu_unc','cho_hoa_don']},
      {name:'APP-C', trang_thai:'Da duyet', tong_tien:300, chip_nghiep_vu:['thieu_unc']}
    ], nhan:{}, quyen:{}, trang_thai_co:['Da thanh toan','Da duyet'],
    nhan_chip:{cho_hoa_don:'Chờ hóa đơn đến sau',thieu_unc:'Chưa có UNC',da_chi:'Đã chi theo hồ sơ'} } };
    var m = dungMan(canh);
    await m.g.scrHoSoTT();
    dung('đếm 2 hồ sơ chờ', chipTheo(m,'data-hsviec','cho_hoa_don').textContent.includes('(2)'));
    chipTheo(m,'data-hsviec','cho_hoa_don').click();
    await m.g.scrHoSoTT();
    bang('hai dòng đúng nhóm', m.tai.querySelectorAll('[data-hs]').length, 2);
    m.g.hsTT='Da thanh toan';
    await m.g.scrHoSoTT();
    bang('giao hai bộ lọc', m.tai.querySelectorAll('[data-hs]').length, 1);
    m.g.hsViec='thieu_unc';
    await m.g.scrHoSoTT();
    bang('không lấy sai hồ sơ', m.tai.querySelectorAll('[data-hs]').length, 0);
    dung('chip chọn 0 vẫn hiện', !!chipTheo(m,'data-hsviec','thieu_unc'));
    chipTheo(m,'data-hsviec','').click();
    await m.g.scrHoSoTT();
    bang('bỏ lọc lấy lại dòng', m.tai.querySelectorAll('[data-hs]').length, 1);
    dung('nhắc không đánh đồng cấn nợ', m.khung.innerHTML.includes('chưa xác nhận đã cấn nợ'));
  });
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
    m.g.hsViec = 'cho_hoa_don';
    await m.tai.getElementById('hsXuat').onclick();
    var goi = m.goiApi.filter(function (x) { return x.duong === 'vagabond.ho_so_tt.xuat_excel' })[0];
    dung('co goi xuat Excel', !!goi);
    bang('gui tu khoa da ap', goi.ts.tu_khoa, 'alpha');
    bang('gui ca o loc tai khoan', goi.ts.tk_chi, '6277 - VGB');
    bang('gui ca o loc chi phi thue', goi.ts.loai_cp_thue, 'Hop le');
    bang('gui chip nghiep vu', goi.ts.chip, 'cho_hoa_don');
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

  /* ============ MOT CUA CHON BEN NHAN TIEN (Issue #196, con sot) ============
     Codex neu 06/09/2026: man Chi tu TK cong ty, nhanh Khong hop le tinh
     thue, muc 3 "Tra cho ai" VAN bay danh sach NCC dai thanh chip ngay tren
     form. Cac ca duoi day mo DUNG man do va dung man hoan ung co hoa don,
     kiem theo dung chuoi thao tac cua nguoi that. */

  var NCC_NO = [
    { ncc: 'NCC-1', ten: 'CÔNG TY ĐIỆN LỰC SÀI GÒN', so_hd: 2, tien: 5000000, qua_han: 1000000 },
    { ncc: 'NCC-2', ten: 'CÔNG TY TNHH TÁC KHÍ VIỆT', so_hd: 1, tien: 300000, qua_han: 0 },
  ];
  var NGUOI_UNG = [
    { ncc: 'NCC-9', ten: 'NGUYỄN HOÀNG VIỆT - HOÀN ỨNG', hay_dung: 1 },
    { ncc: 'NCC-1', ten: 'CÔNG TY ĐIỆN LỰC SÀI GÒN', hay_dung: 0 },
    { ncc: 'NCC-3', ten: 'Bếp Cô Minh', hay_dung: 0 },
  ];

  function canhChi(them) {
    var c = { nccNo: NCC_NO, nguoiUng: NGUOI_UNG };
    Object.keys(them || {}).forEach(function (k) { c[k] = them[k]; });
    return c;
  }

  async function moManChi(canh, cpThue, benDangChon) {
    var m = dungMan(canh);
    m.g.huCpThue = cpThue;
    m.g.huNguoi = benDangChon || '';
    await m.g.scrChiCongTyTao();
    return m;
  }

  function theThuGon(m) { return m.tai.querySelectorAll('[data-hsbn-mo]'); }
  function dongTrongTruot(m) { return m.tai.querySelectorAll('[data-hsbn]'); }
  function oTimTruot(m) { return m.tai.getElementById('hsbnTim'); }

  function goVao(m, chu) {
    var o = oTimTruot(m);
    o.value = chu;
    o.dispatchEvent(dg.suKien('input', {}, o));
  }

  async function bamEnter(m) {
    var o = oTimTruot(m);
    o.dispatchEvent(dg.suKien('keydown', { key: 'Enter' }, o));
    for (var i = 0; i < 50; i++) {
      if (m.tai.getElementById('hsbnDs').innerHTML.indexOf('Đang hỏi máy chủ') < 0) return;
      await new Promise(function (r) { setTimeout(r, 0); });
    }
  }

  await caAsync('E1. chi cong ty, nhanh KHONG hop le: form chi co MOT the, khong bay danh muc',
    async function () {
      var m = await moManChi(canhChi(), 'Chi phi khong hop le');
      bang('dung mot the thu gon cho ben nhan', theThuGon(m).length, 1);
      bang('chua mo tam truot', m.g.HS_BN_MO, 0);
      bang('khong dong danh muc nao bay san', dongTrongTruot(m).length, 0);
      dung('khong con chip nguoi nhan tren form',
        m.khung.innerHTML.indexOf('data-hun') < 0);
      dung('the noi ro la cham de chon',
        m.khung.innerHTML.indexOf('Chạm để chọn người nhận tiền') > 0);
      dung('ten cua nguoi trong danh muc KHONG lo tren form',
        m.khung.innerHTML.indexOf('Bếp Cô Minh') < 0);
    });

  await caAsync('E2. chi cong ty, nhanh HOP LE: cung mot the, cung khong bay danh muc',
    async function () {
      var m = await moManChi(canhChi(), 'Chi phi hop le');
      bang('dung mot the thu gon', theThuGon(m).length, 1);
      bang('khong dong danh muc nao bay san', dongTrongTruot(m).length, 0);
      dung('ten nha cung cap KHONG lo tren form',
        m.khung.innerHTML.indexOf('TÁC KHÍ VIỆT') < 0);
      dung('the noi ro la cham de chon',
        m.khung.innerHTML.indexOf('Chạm để chọn nhà cung cấp') > 0);
    });

  await caAsync('E3. cham the moi mo tam truot, trong do co o tim va loc duoc khong dau',
    async function () {
      var m = await moManChi(canhChi(), 'Chi phi khong hop le');
      theThuGon(m)[0].click();
      bang('tam truot dang mo', m.g.HS_BN_MO, 1);
      dung('co o tim', !!oTimTruot(m));
      bang('bay du ba nguoi', dongTrongTruot(m).length, 3);
      goVao(m, 'dien luc');
      bang('go khong dau van loc ra dung mot dong', dongTrongTruot(m).length, 1);
      bang('va dung dong can tim', dongTrongTruot(m)[0].getAttribute('data-hsbn'), 'NCC-1');
      goVao(m, 'khong co ai ten the nay');
      bang('khong khop thi khong con dong nao', dongTrongTruot(m).length, 0);
      dung('va noi ro duong di tiep',
        m.tai.getElementById('hsbnDs').innerHTML.indexOf('Bấm Enter để hỏi cả danh mục') > 0);
    });

  await caAsync('E4. bam Thoi: dong tam truot va GIU NGUYEN moi thu dang lam',
    async function () {
      var m = await moManChi(canhChi(), 'Chi phi khong hop le', 'NCC-9');
      m.g.huDong = [{ noi_dung: 'Tiền điện tháng 8', so_tien: 1234000, tk_no: '6277 - VGB' }];
      m.g.huGhiChu = 'ghi chu dang go';
      await m.g.scrChiCongTyTao();
      var truocHtml = m.khung.innerHTML;
      theThuGon(m)[0].click();
      m.tai.querySelectorAll('[data-hsbn-dong]')[0].click();
      bang('tam truot da dong', m.g.HS_BN_MO, 0);
      bang('khong con dong nao cua tam truot', dongTrongTruot(m).length, 0);
      bang('ben nhan giu nguyen', m.g.huNguoi, 'NCC-9');
      bang('khoan chi giu nguyen', m.g.huDong.length, 1);
      bang('so tien giu nguyen', m.g.huDong[0].so_tien, 1234000);
      bang('ghi chu giu nguyen', m.g.huGhiChu, 'ghi chu dang go');
      bang('man hinh khong he ve lai', m.khung.innerHTML, truocHtml);
    });

  await caAsync('E5. doi ben thi xoa tick hoa don cua ben cu, chon lai chinh no thi khong xoa',
    async function () {
      var m = await moManChi(canhChi({
        hoaDon: { rows: [{ hoa_don: 'HD-1', so_hd_ncc: 'A1', con_no: 500000 }], tong: 500000 },
      }), 'Chi phi hop le', 'NCC-1');
      m.g.huChonHd = { 'HD-1': { con_no: 500000 } };
      await m.g.scrChiCongTyTao();

      /* Chon lai DUNG ben dang chon: khong duoc coi la doi, khong duoc xoa. */
      theThuGon(m)[0].click();
      dongTrongTruot(m).filter(function (e) {
        return e.getAttribute('data-hsbn') === 'NCC-1';
      })[0].click();
      bang('chon lai chinh no thi tick con nguyen', Object.keys(m.g.huChonHd).length, 1);

      /* Doi sang ben khac: hoa don cua ben cu phai bi bo, khong duoc ghep
         nham no cua nha nay sang nha kia. */
      theThuGon(m)[0].click();
      dongTrongTruot(m).filter(function (e) {
        return e.getAttribute('data-hsbn') === 'NCC-2';
      })[0].click();
      bang('doi ben thi xoa tick hoa don cu', Object.keys(m.g.huChonHd).length, 0);
      bang('ben nhan da doi that', m.g.huNguoi, 'NCC-2');
      /* Ve lai man la mot ham async. Khong cho cho xong ma doc ngay la doc
         phai ban cu, va ca kiem se XANH ca tren ban chua sua. */
      dung('co cho man ve lai xong', (await choVeLai(m)) > 0);
      bang('the hien ten ben moi',
        m.khung.innerHTML.indexOf('TÁC KHÍ VIỆT') > 0, true);
    });

  await caAsync('E6. bam Enter la HOI THAT may chu, voi duoc nguoi ngoai danh sach da tai',
    async function () {
      var m = await moManChi(canhChi({
        nguoiUngTim: function (q) {
          return q.indexOf('bao hiem') >= 0
            ? [{ ncc: 'NCC-BH', ten: 'BẢO HIỂM XÃ HỘI QUẬN 1', hay_dung: 0 }] : [];
        },
      }), 'Chi phi khong hop le');
      theThuGon(m)[0].click();
      goVao(m, 'bao hiem');
      bang('loc tai cho khong ra gi', dongTrongTruot(m).length, 0);
      var soGoi = m.goiApi.length;
      await bamEnter(m);
      dung('co hoi them may chu', m.goiApi.length > soGoi);
      var goi = m.goiApi[m.goiApi.length - 1];
      bang('hoi dung cua', goi.duong, 'vagabond.ho_so_tt.ds_nguoi_ung');
      bang('va mang theo tu khoa dang go', goi.ts.tu_khoa, 'bao hiem');
      bang('bay ra nguoi vua tim duoc', dongTrongTruot(m).length, 1);
      dongTrongTruot(m)[0].click();
      bang('chon duoc nguoi nam ngoai danh sach dau', m.g.huNguoi, 'NCC-BH');
      /* Codex P1 (06/09/2026): truoc day ca nay dung o day, tuc chi kiem
         MA ngay sau click. Man ve lai roi tra ma trong danh sach goi y (300
         nguoi dau) khong thay nguoi vua tim, the bao "Chua chon ai" trong
         khi ma van duoc mang di luu. Phai CHO ve lai xong roi soi the. */
      dung('co cho man ve lai xong', (await choVeLai(m)) > 0);
      var the = m.tai.getElementById('huMoBen').textContent;
      dung('the hien dung nguoi vua chon, khong bao chua chon: ' + the,
        the.indexOf('BẢO HIỂM XÃ HỘI QUẬN 1') >= 0 && the.indexOf('Chưa chọn') < 0);
      bang('ma va the la cung mot nguoi', m.g.huNguoi, 'NCC-BH');
    });

  await caAsync('E7. may chu hong luc tim: noi ro va chi duong lam lai, khong im lang',
    async function () {
      var m = await moManChi(canhChi({
        nguoiUngTim: function () { throw new Error('mat mang'); },
      }), 'Chi phi khong hop le');
      theThuGon(m)[0].click();
      goVao(m, 'gi do');
      await bamEnter(m);
      var trong = m.tai.getElementById('hsbnDs').innerHTML;
      dung('noi ro loi cua may chu', trong.indexOf('mat mang') > 0);
      dung('va chi duong lam lai', trong.indexOf('bấm Enter tìm lại') > 0);
      bang('tam truot van con mo de nguoi ta thu lai', m.g.HS_BN_MO, 1);
    });

  await caAsync('E8. nut tao moi: co quyen thi co nut va mang dung chu dang go',
    async function () {
      var m = await moManChi(canhChi({ vai: ['Accounts Manager'] }), 'Chi phi khong hop le');
      theThuGon(m)[0].click();
      var nut = m.tai.getElementById('hsbnTao');
      dung('co nut tao moi', !!nut);
      goVao(m, 'bao hiem xa hoi');
      bang('nut van con sau khi go khong ra gi', !!m.tai.getElementById('hsbnTao'), true);
      var mang = null;
      m.g.nccTaoNhanh = function (goiY) { mang = goiY; };
      nut.click();
      bang('mang dung cai DANG go sang man tao', mang, 'bao hiem xa hoi');
      bang('bam xong thi tam truot dong lai', m.g.HS_BN_MO, 0);
    });

  await caAsync('E8b. o duoc dien san ma khong ban su kien: nut tao van mang dung chu',
    async function () {
      /* Chinh ra cai bay: neu nut tao doc BIEN da luu thay vi doc thang o,
         thi moi duong nao dien chu vao o ma khong ban su kien `input` (dan
         tu dong, hay chinh may dien san) deu lam nut tao mang chu rong.
         Ca E8 mot minh KHONG bat duoc, vi o do `goVao` co ban su kien nen
         hai duong doc ra cung mot ket qua. */
      var m = await moManChi(canhChi({ vai: ['Accounts Manager'] }), 'Chi phi khong hop le');
      theThuGon(m)[0].click();
      oTimTruot(m).value = 'bhxh co so tan dinh';
      var mang = null;
      m.g.nccTaoNhanh = function (goiY) { mang = goiY; };
      m.tai.getElementById('hsbnTao').click();
      bang('doc thang gia tri trong o', mang, 'bhxh co so tan dinh');
    });

  await caAsync('E9. khong co quyen thu mua thi KHONG bay nut tao moi',
    async function () {
      var m = await moManChi(canhChi({ vai: ['Nhân viên bán hàng'] }), 'Chi phi khong hop le');
      theThuGon(m)[0].click();
      bang('khong co nut tao moi', !!m.tai.getElementById('hsbnTao'), false);
      dung('nhung van chon duoc nguoi co san', dongTrongTruot(m).length > 0);
    });

  await caAsync('E10. man hoan ung CO hoa don: nguoi duoc hoan ung cung mot the, khong chip',
    async function () {
      var m = dungMan(canhChi({ nccChon: NCC_NO, tkHoan: { tk: [], doan: 0 } }));
      m.g.hsTaoLoai = 'Hoan ung HD';
      await m.g.scrHoSoTTTao();
      dung('co the chon nguoi duoc hoan ung',
        m.khung.innerHTML.indexOf('Chạm để chọn người được hoàn ứng') > 0);
      dung('khong con chip nguoi ung', m.khung.innerHTML.indexOf('data-hsu') < 0);
      bang('khong dong danh muc nao bay san', dongTrongTruot(m).length, 0);
      /* Hai the: mot cho nguoi duoc hoan ung, mot cho nha cung cap. Hai
         khai niem khac nhau nen phai la HAI o, khong duoc gop lam mot. */
      bang('co dung hai the ben nhan', theThuGon(m).length, 2);
      var the = theThuGon(m).filter(function (e) {
        return e.getAttribute('data-hsbn-mo') === 'hsMoUng';
      })[0];
      dung('the nguoi duoc hoan ung co that', !!the);
      the.click();
      bang('mo ra dung danh sach nguoi ung', dongTrongTruot(m).length, 3);
      dongTrongTruot(m).filter(function (e) {
        return e.getAttribute('data-hsbn') === 'NCC-3';
      })[0].click();
      bang('chon duoc nguoi nhan', m.g.hsTaoNguoiUng, 'NCC-3');
    });

  await caAsync('E11. man hoan ung KHONG hoa don van khong co o chon ben nhan',
    async function () {
      var m = dungMan(canhChi({ tkHoan: { tk: [{ ma: 'TK1', nhan: 'ACB · 123' }], doan: 0 } }));
      await m.g.scrHoanUngTao();
      bang('khong the ben nhan nao', theThuGon(m).length, 0);
      dung('van con o chon tai khoan nhan tien',
        m.khung.innerHTML.indexOf('data-hutk') > 0);
    });

  /* ============ GIU BEN DA CHON, LUOT HOI, PHIEN TAM (Codex #217, 06/09) ============
     Cac ca duoi day KIEM KET QUA SAU KHI BAT DONG BO XONG: ten tren the va
     ma se gui phai la cung mot nguoi. */

  /* Mot phan hoi giu duoc lai: tra ve promise va ham tha. */
  function giuPhanHoi() {
    var tha;
    var p = new Promise(function (r) { tha = r; });
    return { p: p, tha: tha };
  }

  await caAsync('E12. hai lan Enter ve NGUOC thu tu: lan CU khong duoc de len lan MOI',
    async function () {
      var g1 = giuPhanHoi(), g2 = giuPhanHoi();
      var m = await moManChi(canhChi({
        nguoiUngTim: function (q) { return q === 'bao hiem' ? g1.p : g2.p; },
      }), 'Chi phi khong hop le');
      theThuGon(m)[0].click();
      var o = oTimTruot(m);
      goVao(m, 'bao hiem');
      o.dispatchEvent(dg.suKien('keydown', { key: 'Enter' }, o));
      goVao(m, 'dien luc');
      o.dispatchEvent(dg.suKien('keydown', { key: 'Enter' }, o));
      /* Lan MOI ve truoc. */
      g2.tha([{ ncc: 'NCC-DL', ten: 'ĐIỆN LỰC', hay_dung: 0 }]);
      for (var i = 0; i < 5; i++) await new Promise(function (r) { setTimeout(r, 0); });
      bang('bay dung ket qua lan moi', dongTrongTruot(m)[0].getAttribute('data-hsbn'), 'NCC-DL');
      /* Lan CU ve sau: phai bi bo, khong duoc de len. */
      g1.tha([{ ncc: 'NCC-BH', ten: 'BẢO HIỂM', hay_dung: 0 }]);
      for (var j = 0; j < 5; j++) await new Promise(function (r) { setTimeout(r, 0); });
      bang('van la ket qua lan moi', dongTrongTruot(m).length, 1);
      bang('khong bi lan cu de len', dongTrongTruot(m)[0].getAttribute('data-hsbn'), 'NCC-DL');
    });

  await caAsync('E13. go tiep tu khoa trong luc dang tai: phan hoi cua tu khoa cu bi bo',
    async function () {
      var g1 = giuPhanHoi();
      var m = await moManChi(canhChi({ nguoiUngTim: function () { return g1.p; } }), 'Chi phi khong hop le');
      theThuGon(m)[0].click();
      var o = oTimTruot(m);
      goVao(m, 'bao');
      o.dispatchEvent(dg.suKien('keydown', { key: 'Enter' }, o));
      dung('dang bao la hoi may chu', m.tai.getElementById('hsbnDs').innerHTML.indexOf('Đang hỏi') >= 0);
      goVao(m, 'bao hiem xa');       /* nguoi ta go tiep, chua bam Enter */
      /* Ten tra ve KHOP CA tu khoa moi: ban cu se loc tai cho va bay ra,
         tuc bay ket qua cua mot cau hoi nguoi ta chua he bam Enter. Ban
         moi bo phan hoi do vi tu khoa trong o da khac tu khoa da hoi. */
      g1.tha([{ ncc: 'NCC-BH', ten: 'BẢO HIỂM XÃ HỘI', hay_dung: 0 }]);
      for (var i = 0; i < 5; i++) await new Promise(function (r) { setTimeout(r, 0); });
      bang('khong bay ket qua cua tu khoa cu', dongTrongTruot(m).length, 0);
      bang('o tim van giu chu dang go', o.value, 'bao hiem xa');
      dung('khong con bao dang hoi, cung khong bao loi',
        m.tai.getElementById('hsbnDs').innerHTML.indexOf('Đang hỏi') < 0 &&
        m.tai.getElementById('hsbnDs').innerHTML.indexOf('⚠️') < 0);
    });

  await caAsync('E14. dong tam roi mo tam MOI: phan hoi cua tam cu ve muon khong ve vao tam moi',
    async function () {
      var g1 = giuPhanHoi();
      var m = await moManChi(canhChi({
        nguoiUngTim: function (q) { return q === 'cu' ? g1.p : []; },
      }), 'Chi phi khong hop le');
      theThuGon(m)[0].click();
      var o = oTimTruot(m);
      goVao(m, 'cu');
      o.dispatchEvent(dg.suKien('keydown', { key: 'Enter' }, o));
      m.tai.querySelector('[data-hsbn-dong]').click();   /* dong tam */
      bang('tam da dong', m.g.HS_BN_MO, 0);
      theThuGon(m)[0].click();                            /* mo tam moi */
      bang('tam moi dang mo', m.g.HS_BN_MO, 1);
      var truoc = m.tai.getElementById('hsbnDs').innerHTML;
      g1.tha([{ ncc: 'NCC-CU', ten: 'CŨ', hay_dung: 0 }]);
      for (var i = 0; i < 5; i++) await new Promise(function (r) { setTimeout(r, 0); });
      bang('tam moi khong doi', m.tai.getElementById('hsbnDs').innerHTML, truoc);
      bang('khong co dong nao cua phien cu', dongTrongTruot(m).filter(function (e) {
        return e.getAttribute('data-hsbn') === 'NCC-CU'; }).length, 0);
    });

  await caAsync('E15. mo lai voi MA nam ngoai danh sach (ban nhap): the tra ten theo ma, khong bao chua chon',
    async function () {
      var m = await moManChi(canhChi({
        supplier: { 'NCC-XA': { supplier_name: 'CÔNG TY XA LẮC' } },
      }), 'Chi phi khong hop le', 'NCC-XA');
      var the = m.tai.getElementById('huMoBen').textContent;
      dung('the hien ten tra theo ma: ' + the, the.indexOf('CÔNG TY XA LẮC') >= 0);
      dung('khong noi chua chon', the.indexOf('Chưa chọn') < 0);
      var goi = m.goiApi.filter(function (x) { return x.duong === 'frappe.client.get_value'; });
      bang('co tra dung ma', goi.length && goi[0].ts.filters.name, 'NCC-XA');
    });

  await caAsync('E16. ma khong con trong danh muc: the noi ro, va CHAN gui',
    async function () {
      var m = await moManChi(canhChi({ supplier: {} }), 'Chi phi khong hop le', 'NCC-MAT');
      var the = m.tai.getElementById('huMoBen').textContent;
      dung('noi ro ma khong con: ' + the, the.indexOf('không còn trong danh mục') >= 0);
      dung('khong noi chua chon', the.indexOf('Chưa chọn') < 0);
      var baoTinGoi = [];
      m.g.baoTin = function (t) { baoTinGoi.push(String(t)); };
      var soGoi = m.goiApi.length;
      m.tai.getElementById('huLuu').click();
      for (var i = 0; i < 5; i++) await new Promise(function (r) { setTimeout(r, 0); });
      dung('bi chan voi cau ro', baoTinGoi.length && baoTinGoi[0].indexOf('không còn') >= 0);
      bang('khong goi may chu lap ho so', m.goiApi.length, soGoi);
    });

  await caAsync('E17. ben bi VO HIEU HOA: the noi ro va chan gui',
    async function () {
      var m = await moManChi(canhChi({
        supplier: { 'NCC-TAT': { supplier_name: 'NHÀ ĐÃ NGHỈ', disabled: 1 } },
      }), 'Chi phi khong hop le', 'NCC-TAT');
      var the = m.tai.getElementById('huMoBen').textContent;
      dung('noi ro bi vo hieu hoa: ' + the, the.indexOf('vô hiệu hoá') >= 0);
      var baoTinGoi = [];
      m.g.baoTin = function (t) { baoTinGoi.push(String(t)); };
      m.tai.getElementById('huLuu').click();
      for (var i = 0; i < 5; i++) await new Promise(function (r) { setTimeout(r, 0); });
      dung('bi chan', baoTinGoi.length && baoTinGoi[0].indexOf('vô hiệu') >= 0);
    });

  await caAsync('E18. hoan ung co HD: chon nguoi ngoai danh sach dau, the van hien dung ten sau ve lai',
    async function () {
      var m = dungMan(canhChi({ nccChon: NCC_NO, tkHoan: { tk: [], doan: 0 },
        nguoiUngTim: function (q) {
          return q === 'xa' ? [{ ncc: 'NCC-XA', ten: 'NGƯỜI Ở XA', hay_dung: 0 }] : [];
        } }));
      m.g.hsTaoLoai = 'Hoan ung HD';
      await m.g.scrHoSoTTTao();
      theThuGon(m).filter(function (e) { return e.getAttribute('data-hsbn-mo') === 'hsMoUng'; })[0].click();
      goVao(m, 'xa');
      await bamEnter(m);
      dongTrongTruot(m)[0].click();
      bang('ma da chon', m.g.hsTaoNguoiUng, 'NCC-XA');
      dung('co cho ve lai', (await choVeLai(m)) > 0);
      var the = m.tai.getElementById('hsMoUng').textContent;
      dung('the hien dung ten: ' + the, the.indexOf('NGƯỜI Ở XA') >= 0 && the.indexOf('Chưa chọn') < 0);
    });

  await caAsync('E19. tao NCC moi tu tam: chi co ma, the van tra ra ten',
    async function () {
      var m = await moManChi(canhChi({
        supplier: { 'NCC-MOI': { supplier_name: 'NHÀ VỪA TẠO' } },
      }), 'Chi phi khong hop le');
      /* nccTaoNhanh la ham gia trong CHO_GIA; goi thang callback tao_xong
         voi dung mot ma, y nhu duong tao that. */
      m.g.nccTaoNhanh = function (goiY, xong) { xong('NCC-MOI'); };
      theThuGon(m)[0].click();
      m.tai.getElementById('hsbnTao').click();
      dung('co cho ve lai', (await choVeLai(m)) > 0);
      var the = m.tai.getElementById('huMoBen').textContent;
      dung('the hien ten nha vua tao: ' + the, the.indexOf('NHÀ VỪA TẠO') >= 0);
      bang('ma dung', m.g.huNguoi, 'NCC-MOI');
    });

  /* ---- Vong 2 tren #221 (Codex P2 x2 + hai ca Codex doi them) ---- */

  await caAsync('E20. the dang bao loi tra ma: chon lai DUNG ma do phai go duoc loi va mo lai duong gui',
    async function () {
      /* Mo lai ban nhap luc mang rot: the bao "Chua tra duoc ten cua ma". Nguoi
         ta mo tam, tim ra dung nguoi do, bam chon. Ban cu: `ma === huNguoi`
         thoat som, loi con nguyen, nut gui van bi chan. */
      var canh = canhChi({ supplierHong: true,
        nguoiUngTim: function (q) {
          return q === 'xa' ? [{ ncc: 'NCC-XA', ten: 'CÔNG TY XA LẮC', hay_dung: 0 }] : [];
        } });
      var m = await moManChi(canh, 'Chi phi khong hop le', 'NCC-XA');
      var the = m.tai.getElementById('huMoBen').textContent;
      dung('the dang bao chua tra duoc: ' + the, the.indexOf('Chưa tra được') >= 0);
      dung('co cau loi dang cam', !!m.g.huBenLoi);
      /* Mang da co lai: tim thay nguoi qua Enter, chon lai chinh ma dang cam. */
      theThuGon(m)[0].click();
      goVao(m, 'xa');
      await bamEnter(m);
      bang('tim ra dung nguoi', dongTrongTruot(m)[0].getAttribute('data-hsbn'), 'NCC-XA');
      dongTrongTruot(m)[0].click();
      dung('co cho man ve lai', (await choVeLai(m)) > 0);
      bang('ma khong doi', m.g.huNguoi, 'NCC-XA');
      var the2 = m.tai.getElementById('huMoBen').textContent;
      dung('the hien ten that, het bao loi: ' + the2,
        the2.indexOf('CÔNG TY XA LẮC') >= 0 && the2.indexOf('Chưa tra được') < 0);
      bang('cau loi da duoc go', m.g.huBenLoi, '');
      var baoTinGoi = [];
      m.g.baoTin = function (t) { baoTinGoi.push(String(t)); };
      var soGoi = m.goiApi.length;
      m.tai.getElementById('huLuu').click();
      for (var i = 0; i < 5; i++) await new Promise(function (r) { setTimeout(r, 0); });
      bang('khong con bi chan vi ben chua ro', baoTinGoi.filter(function (t) { return t.indexOf('Chưa tra được') >= 0; }).length, 0);
      dung('duong gui da chay tiep (co goi may chu hoac chan vi ly do khac)', m.goiApi.length > soGoi || baoTinGoi.length > 0);
    });

  await caAsync('E20b. khong co loi: chon lai dung ben dang chon van KHONG ve lai, khong xoa tick (giu E5)',
    async function () {
      var m = await moManChi(canhChi({
        hoaDon: { rows: [{ hoa_don: 'HD-1', so_hd_ncc: 'A1', con_no: 500000 }], tong: 500000 },
      }), 'Chi phi hop le', 'NCC-1');
      m.g.huChonHd = { 'HD-1': { con_no: 500000 } };
      await m.g.scrChiCongTyTao();
      var truocHtml = m.khung.innerHTML;
      theThuGon(m)[0].click();
      dongTrongTruot(m).filter(function (e) { return e.getAttribute('data-hsbn') === 'NCC-1'; })[0].click();
      bang('khong ve lai man', (await choVeLai(m)), 0);
      bang('tick con nguyen', Object.keys(m.g.huChonHd).length, 1);
      bang('man y nguyen', m.khung.innerHTML, truocHtml);
    });

  await caAsync('E20c. hoan ung: nguoi dang cam bao loi tra ma, chon lai chinh nguoi do cung go duoc loi',
    async function () {
      var m = dungMan(canhChi({ nccChon: NCC_NO, tkHoan: { tk: [], doan: 0 }, supplierHong: true,
        nguoiUngTim: function (q) {
          return q === 'xa' ? [{ ncc: 'NCC-XA', ten: 'NGƯỜI Ở XA', hay_dung: 0 }] : [];
        } }));
      m.g.hsTaoLoai = 'Hoan ung HD';
      m.g.hsTaoNguoiUng = 'NCC-XA';
      await m.g.scrHoSoTTTao();
      dung('the dang bao chua tra duoc', m.tai.getElementById('hsMoUng').textContent.indexOf('Chưa tra được') >= 0);
      theThuGon(m).filter(function (e) { return e.getAttribute('data-hsbn-mo') === 'hsMoUng'; })[0].click();
      goVao(m, 'xa');
      await bamEnter(m);
      dongTrongTruot(m)[0].click();
      dung('co cho ve lai', (await choVeLai(m)) > 0);
      var the = m.tai.getElementById('hsMoUng').textContent;
      dung('the hien ten, het loi: ' + the, the.indexOf('NGƯỜI Ở XA') >= 0 && the.indexOf('Chưa tra được') < 0);
      bang('cau loi da go', m.g.hsUngLoi, '');
    });

  await caAsync('E21. tim may chu xong roi XOA tu khoa: goi y ban dau quay lai, ke ca sau lan tim khong ra',
    async function () {
      var m = await moManChi(canhChi({
        nguoiUngTim: function (q) {
          return q === 'bao hiem' ? [{ ncc: 'NCC-BH', ten: 'BẢO HIỂM XÃ HỘI', hay_dung: 0 }] : [];
        },
      }), 'Chi phi khong hop le');
      theThuGon(m)[0].click();
      bang('ban dau bay ba nguoi', dongTrongTruot(m).length, 3);
      goVao(m, 'bao hiem');
      await bamEnter(m);
      bang('ket qua may chu bay ra', dongTrongTruot(m).length, 1);
      /* Go tiep NOI TIEP tu khoa da hoi: van loc tren ket qua may chu. */
      goVao(m, 'bao hiem xa');
      bang('noi tiep tu khoa thi van dung ket qua may chu', dongTrongTruot(m).length, 1);
      goVao(m, '');
      bang('xoa trang thi goi y ban dau quay lai', dongTrongTruot(m).length, 3);
      goVao(m, 'dien luc');
      bang('tu khoa khac thi loc tren goi y ban dau', dongTrongTruot(m)[0].getAttribute('data-hsbn'), 'NCC-1');
      /* Tim KHONG RA roi xoa: khong duoc trong tron. */
      goVao(m, 'khong ai');
      await bamEnter(m);
      bang('may chu khong ra ai', dongTrongTruot(m).length, 0);
      goVao(m, '');
      bang('xoa trang sau lan tim khong ra: van du ba goi y', dongTrongTruot(m).length, 3);
    });

  await caAsync('E22. hai lan Enter CUNG tu khoa ve nguoc thu tu: lan cu khong de len lan moi',
    async function () {
      /* Dot bien M2a vong truoc song sot vi moi ca deu doi tu khoa giua hai
         lan Enter, nen cua kiem tu khoa do het. Ca nay giu NGUYEN tu khoa,
         chi cua kiem luot moi bat duoc. */
      var lan = 0, g1 = giuPhanHoi(), g2 = giuPhanHoi();
      var m = await moManChi(canhChi({
        nguoiUngTim: function () { lan++; return lan === 1 ? g1.p : g2.p; },
      }), 'Chi phi khong hop le');
      theThuGon(m)[0].click();
      var o = oTimTruot(m);
      goVao(m, 'bao hiem');
      o.dispatchEvent(dg.suKien('keydown', { key: 'Enter' }, o));
      o.dispatchEvent(dg.suKien('keydown', { key: 'Enter' }, o));
      bang('may chu bi hoi hai lan', lan, 2);
      g2.tha([{ ncc: 'NCC-MOI', ten: 'BẢO HIỂM BẢN MỚI', hay_dung: 0 }]);
      for (var i = 0; i < 5; i++) await new Promise(function (r) { setTimeout(r, 0); });
      bang('bay ket qua lan moi', dongTrongTruot(m)[0].getAttribute('data-hsbn'), 'NCC-MOI');
      g1.tha([{ ncc: 'NCC-CU', ten: 'BẢO HIỂM BẢN CŨ', hay_dung: 0 }]);
      for (var j = 0; j < 5; j++) await new Promise(function (r) { setTimeout(r, 0); });
      bang('lan cu ve sau bi bo', dongTrongTruot(m)[0].getAttribute('data-hsbn'), 'NCC-MOI');
      bang('chi con mot dong', dongTrongTruot(m).length, 1);
    });

  await caAsync('E23. hai nguoi TRUNG TEN khac ma: chu nhin thay phai khac nhau, chon nguoi thu hai thi ma, the va ho so la cua nguoi thu hai',
    async function () {
      var m = await moManChi(canhChi({
        nguoiUngTim: function (q) {
          return q === 'nguyen van a' ? [
            { ncc: 'NCC-A1', ten: 'NGUYỄN VĂN A', hay_dung: 0 },
            { ncc: 'NCC-A2', ten: 'NGUYỄN VĂN A', hay_dung: 0 },
          ] : [];
        },
      }), 'Chi phi khong hop le');
      theThuGon(m)[0].click();
      goVao(m, 'nguyen van a');
      await bamEnter(m);
      var ds = dongTrongTruot(m);
      bang('bay du hai nguoi trung ten', ds.length, 2);
      /* Codex P2 vong 3 tren #221: cung ten, cung hay_dung thi hai dong chi
         khac o data-hsbn, mat khong thay. Chu NHIN THAY phai khac nhau TRUOC
         khi bam, va cai khac do phai la ma. */
      var c1 = ds[0].textContent, c2 = ds[1].textContent;
      dung('chu hai dong khac nhau: ' + c1 + ' | ' + c2, c1 !== c2);
      dung('dong 1 co ma A1', c1.indexOf('NCC-A1') >= 0 && c1.indexOf('NCC-A2') < 0);
      dung('dong 2 co ma A2', c2.indexOf('NCC-A2') >= 0 && c2.indexOf('NCC-A1') < 0);
      ds.filter(function (e) { return e.getAttribute('data-hsbn') === 'NCC-A2'; })[0].click();
      bang('ma gui di la cua nguoi thu hai', m.g.huNguoi, 'NCC-A2');
      var giu = m.g.VGB_CHON['hu_ben'];
      dung('ho so giu lai dung nguoi thu hai', !!(giu && giu.ho_so && giu.ho_so.ncc === 'NCC-A2'));
      dung('co cho ve lai', (await choVeLai(m)) > 0);
      var the = m.tai.getElementById('huMoBen').textContent;
      dung('the hien ten', the.indexOf('NGUYỄN VĂN A') >= 0);
      dung('the hien dung ma A2, khong phai A1: ' + the, the.indexOf('NCC-A2') >= 0 && the.indexOf('NCC-A1') < 0);
      /* Chon lai nguoi thu nhat: ma va the phai doi sang A1, khong dinh A2. */
      theThuGon(m)[0].click();
      goVao(m, 'nguyen van a');
      await bamEnter(m);
      dongTrongTruot(m).filter(function (e) { return e.getAttribute('data-hsbn') === 'NCC-A1'; })[0].click();
      bang('doi sang nguoi thu nhat', m.g.huNguoi, 'NCC-A1');
      bang('ho so giu lai la A1', m.g.VGB_CHON['hu_ben'].ho_so.ncc, 'NCC-A1');
      dung('co cho ve lai lan hai', (await choVeLai(m)) > 0);
      var the2 = m.tai.getElementById('huMoBen').textContent;
      dung('the doi sang ma A1: ' + the2, the2.indexOf('NCC-A1') >= 0 && the2.indexOf('NCC-A2') < 0);
    });

  await caAsync('E24. hoan ung: hai nguoi trung ten, cung hay_dung, khac ma: dong va the deu bay ma, ma giu la nguoi da bam',
    async function () {
      var m = dungMan(canhChi({ nccChon: NCC_NO, tkHoan: { tk: [], doan: 0 },
        nguoiUngTim: function (q) {
          return q === 'tran thi b' ? [
            { ncc: 'NCC-B1', ten: 'TRẦN THỊ B', hay_dung: 1 },
            { ncc: 'NCC-B2', ten: 'TRẦN THỊ B', hay_dung: 1 },
          ] : [];
        } }));
      m.g.hsTaoLoai = 'Hoan ung HD';
      await m.g.scrHoSoTTTao();
      theThuGon(m).filter(function (e) { return e.getAttribute('data-hsbn-mo') === 'hsMoUng'; })[0].click();
      goVao(m, 'tran thi b');
      await bamEnter(m);
      var ds = dongTrongTruot(m);
      bang('bay du hai nguoi', ds.length, 2);
      var c1 = ds[0].textContent, c2 = ds[1].textContent;
      dung('chu hai dong khac nhau du cung hay_dung: ' + c1 + ' | ' + c2, c1 !== c2);
      dung('dong 2 mang ma B2', c2.indexOf('NCC-B2') >= 0 && c2.indexOf('NCC-B1') < 0);
      ds.filter(function (e) { return e.getAttribute('data-hsbn') === 'NCC-B2'; })[0].click();
      bang('ma nguoi duoc hoan ung la B2', m.g.hsTaoNguoiUng, 'NCC-B2');
      dung('co cho ve lai', (await choVeLai(m)) > 0);
      var the = m.tai.getElementById('hsMoUng').textContent;
      dung('the hien ten', the.indexOf('TRẦN THỊ B') >= 0);
      dung('the hien ma B2, khong phai B1: ' + the, the.indexOf('NCC-B2') >= 0 && the.indexOf('NCC-B1') < 0);
    });
  await caAsync('APP247 UX: tick, sua tien tai cho, Chi het va Luu nhap dung so da chon', async function () {
    var m = dungMan(canhChi({ nccChon: NCC_NO,
      supplier: { 'NCC-1': { supplier_name: 'NCC thử', disabled: 0 } },
      hoaDon: { rows: [{ hoa_don: 'HD-1', ncc: 'NCC-1', ten_ncc: 'NCC thử',
        so_hd_ncc: '123', con_no: 7000000, co_the_chi: 7000000 }] } }));
    m.g.scrHoSoTTView = function () {}; // màn đích sau tạo không thuộc ca nhập tiền
    m.g.hsTaoNcc = 'NCC-1'; m.g.hsTaoLoai = 'NCC';
    await m.g.scrHoSoTTTao();
    dung('chua tick thi chua co o chi dot nay', !m.tai.querySelector('[data-hstien]'));
    m.tai.querySelector('[data-hstick]').click(); await choVeLai(m);
    var o = m.tai.querySelector('[data-hstien]');
    dung('co o chi dot nay', !!o);
    bang('tick xong dien so con no', o.value, '7.000.000');
    o.dispatchEvent(dg.suKien('focus', {}, o));
    dung('cham o tien thi chon het chu', o._daChon === true);
    o.value = '3000000'; o.dispatchEvent(dg.suKien('input', {}, o));
    bang('go toi dau cham nghin toi do', o.value, '3.000.000');
    bang('khong bien thanh 3 dong', m.g.hsTaoChon['HD-1'].so_tien, 3000000);
    dung('so lech bay vien cam', o.closest('.otd').className.indexOf('lech') >= 0);
    bang('tong dang chon doi tai cho', m.tai.getElementById('hsTongChon').textContent, '3.000.000 đ');
    var oCu = o;
    m.tai.querySelector('[data-hshet]').click();
    bang('Chi het tra ve so con no', o.value, '7.000.000');
    bang('Chi het cap nhat trang thai', m.g.hsTaoChon['HD-1'].so_tien, 7000000);
    dung('Chi het bo vien lech', o.closest('.otd').className.indexOf('lech') < 0);
    bang('Chi het cap nhat tong dang chon', m.tai.getElementById('hsTongChon').textContent, '7.000.000 đ');
    dung('sua tien va Chi het khong ve lai man', m.tai.querySelector('[data-hstien]') === oCu);
    o.value = '3.000.000'; o.dispatchEvent(dg.suKien('input', {}, o));
    m.tai.getElementById('hsLuuNhap').click();
    for (var i = 0; i < 5; i++) await new Promise(function (r) { setTimeout(r, 0); });
    var tao = m.goiApi.filter(function (r) { return r.duong === 'vagabond.ho_so_tt.tao'; });
    bang('mot lan tao', tao.length, 1);
    bang('payload3 trieu', JSON.parse(tao[0].ts.hoa_don)[0].so_tien, 3000000);
  });

  await caAsync('APP247 P1-1: xoa trang o Chi dot nay giua chung van giu tick, khong ve lai man', async function () {
    /* Codex neu ra 10/09/2026: cham o, bam Xoa, chua kip go so moi thi o
       rong mot khoanh. Ban loi bo tick va ve lai NGAY luc do, mat con tro va
       xoa luon phieu noi bo da noi (QT-09). Chuoi duoi day lam DUNG thao tac
       do: input voi gia tri rong, CHUA roi o. */
    var m = dungMan(canhChi({ nccChon: NCC_NO,
      supplier: { 'NCC-1': { supplier_name: 'NCC thử', disabled: 0 } },
      hoaDon: { rows: [{ hoa_don: 'HD-1', ncc: 'NCC-1', ten_ncc: 'NCC thử',
        so_hd_ncc: '123', con_no: 7000000, co_the_chi: 7000000 }] } }));
    m.g.scrHoSoTTView = function () {};
    m.g.hsTaoNcc = 'NCC-1'; m.g.hsTaoLoai = 'NCC';
    await m.g.scrHoSoTTTao();
    m.tai.querySelector('[data-hstick]').click(); await choVeLai(m);
    var o = m.tai.querySelector('[data-hstien]');
    m.g.hsPhieuCua['HD-1'] = 'PHIEU-1';
    var soLanGoTruoc = m.daGo.length;
    o.value = ''; o.dispatchEvent(dg.suKien('input', {}, o));
    dung('dong van con tick giua luc o dang rong', !!m.g.hsTaoChon['HD-1']);
    dung('phieu noi bo da noi khong bi go', m.g.hsPhieuCua['HD-1'] === 'PHIEU-1');
    bang('khong ve lai man luc dang go', m.daGo.length, soLanGoTruoc);
    bang('o van la chinh no, khong mat con tro', m.tai.querySelector('[data-hstien]'), o);
    o.value = '2.000.000'; o.dispatchEvent(dg.suKien('input', {}, o));
    bang('go lai duoc so moi', m.g.hsTaoChon['HD-1'].so_tien, 2000000);
    o.dispatchEvent(dg.suKien('change', {}, o));
    bang('roi o giu nguyen so vua go lai', m.g.hsTaoChon['HD-1'].so_tien, 2000000);
  });

  await caAsync('APP247 P1-1b: xoa trang roi ROI O that su moi bo tick va ve lai man', async function () {
    var m = dungMan(canhChi({ nccChon: NCC_NO,
      supplier: { 'NCC-1': { supplier_name: 'NCC thử', disabled: 0 } },
      hoaDon: { rows: [{ hoa_don: 'HD-1', ncc: 'NCC-1', ten_ncc: 'NCC thử',
        so_hd_ncc: '123', con_no: 7000000, co_the_chi: 7000000 }] } }));
    m.g.scrHoSoTTView = function () {};
    m.g.hsTaoNcc = 'NCC-1'; m.g.hsTaoLoai = 'NCC';
    await m.g.scrHoSoTTTao();
    m.tai.querySelector('[data-hstick]').click(); await choVeLai(m);
    var o = m.tai.querySelector('[data-hstien]');
    var soLanGoTruoc = m.daGo.length;
    o.value = ''; o.dispatchEvent(dg.suKien('input', {}, o));
    o.dispatchEvent(dg.suKien('change', {}, o));
    await choVeLai(m);
    dung('roi o voi gia tri rong thi bo tick that', !m.g.hsTaoChon['HD-1']);
    dung('man co ve lai sau khi roi o', m.daGo.length > soLanGoTruoc);
  });

  await caAsync('APP247 P1-2: go so am bi chan ngay tai man, khong gui so am len may chu', async function () {
    /* Codex neu ra 10/09/2026: soTien() giu lai dau tru, dieu kien chan da
       mat mat ve tien <= 0 nen so am song qua ca buoc roi o va len toi
       payload gui may chu. */
    var m = dungMan(canhChi({ nccChon: NCC_NO,
      supplier: { 'NCC-1': { supplier_name: 'NCC thử', disabled: 0 } },
      hoaDon: { rows: [{ hoa_don: 'HD-1', ncc: 'NCC-1', ten_ncc: 'NCC thử',
        so_hd_ncc: '123', con_no: 7000000, co_the_chi: 7000000 }] } }));
    m.g.scrHoSoTTView = function () {};
    m.g.hsTaoNcc = 'NCC-1'; m.g.hsTaoLoai = 'NCC';
    await m.g.scrHoSoTTTao();
    m.tai.querySelector('[data-hstick]').click(); await choVeLai(m);
    var o = m.tai.querySelector('[data-hstien]');
    o.value = '-3000'; o.dispatchEvent(dg.suKien('input', {}, o));
    dung('so am bay vien canh lech ngay tai o', o.closest('.otd').className.indexOf('lech') >= 0);
    bang('chua ghi so am vao dang chon', m.g.hsTaoChon['HD-1'].so_tien, 7000000);
    o.dispatchEvent(dg.suKien('change', {}, o));
    bang('roi o thi tra lai so cu, khong giu so am', o.value, '7.000.000');
    bang('dang chon van la so cu, khong phai so am', m.g.hsTaoChon['HD-1'].so_tien, 7000000);
    m.tai.getElementById('hsLuuNhap').click();
    for (var i = 0; i < 5; i++) await new Promise(function (r) { setTimeout(r, 0); });
    var tao = m.goiApi.filter(function (r) { return r.duong === 'vagabond.ho_so_tt.tao'; });
    bang('mot lan tao', tao.length, 1);
    dung('khong gui so am len may chu', JSON.parse(tao[0].ts.hoa_don)[0].so_tien > 0);
  });

  await caAsync('APP247 P1 vong 2: cham nhan, don vi va chip lech khong bo tick hay mat phieu', async function () {
    var m = dungMan(canhChi({ nccChon: NCC_NO,
      supplier: { 'NCC-1': { supplier_name: 'NCC thử', disabled: 0 } },
      hoaDon: { rows: [{ hoa_don: 'HD-1', ncc: 'NCC-1', ten_ncc: 'NCC thử',
        so_hd_ncc: '123', con_no: 7000000, co_the_chi: 7000000 }] } }));
    m.g.hsTaoNcc = 'NCC-1'; m.g.hsTaoLoai = 'NCC';
    await m.g.scrHoSoTTTao();
    m.tai.querySelector('[data-hstick]').click(); await choVeLai(m);
    var o = m.tai.querySelector('[data-hstien]');
    o.value = '3000000'; o.dispatchEvent(dg.suKien('input', {}, o));
    m.g.hsPhieuCua['HD-1'] = 'PHIEU-1';
    var soLanGo = m.daGo.length;
    var vung = [o.closest('.otd').querySelector('.lb'), o.closest('.otd').querySelector('.dv'),
      m.tai.querySelector('[data-hslech]')];
    vung.forEach(function (n) {
      n.click();
      bang('cham trong khoi tien van giu 3 trieu', m.g.hsTaoChon['HD-1'].so_tien, 3000000);
      bang('cham trong khoi tien van giu phieu noi bo', m.g.hsPhieuCua['HD-1'], 'PHIEU-1');
      bang('cham trong khoi tien khong ve lai man', m.daGo.length, soLanGo);
    });
    m.tai.getElementById('hsChonHet').click(); await choVeLai(m);
    bang('Chon het khong ghi de so da go tay', m.g.hsTaoChon['HD-1'].so_tien, 3000000);
  });

  await caAsync('APP247: chi cong ty gui so tien tung dot thay vi ca hoa don', async function () {
    var m = dungMan(canhChi({ supplier: { 'NCC-1': { supplier_name: 'NCC thử' } },
      hoaDon: { rows: [{ hoa_don: 'HD-1', ncc: 'NCC-1', ten_ncc: 'NCC thử',
        con_no: 10000000, co_the_chi: 7000000, dang_giu: 3000000 }] } }));
    m.g.scrHoSoTTView = function () {};
    m.g.huCpThue = 'Chi phi hop le'; m.g.huNguoi = 'NCC-1'; m.g.huTkChi = '11211 - VGB';
    await m.g.scrChiCongTyTao();
    m.tai.querySelector('[data-huhd]').click(); await choVeLai(m);
    var o = m.tai.querySelector('[data-hucttien]'); dung('co o tien', !!o);
    var oCu = o, soLanGo = m.daGo.length;
    o.value = '2000000'; o.dispatchEvent(dg.suKien('input', {}, o));
    bang('chi cong ty cham nghin khi go', o.value, '2.000.000');
    bang('dang chon2 trieu', m.g.huChonHd['HD-1'], 2000000);
    bang('chi cong ty cap nhat tong tai cho', m.tai.getElementById('huTongChon').textContent, '2.000.000 đ');
    dung('chi cong ty bay canh bao lech', o.closest('.otd').className.indexOf('lech') >= 0);
    dung('chi cong ty khong ve lai man moi phim', m.daGo.length === soLanGo && m.tai.querySelector('[data-hucttien]') === oCu);
    m.tai.querySelector('[data-huhet]').click();
    bang('Chi het dung phan co the chi', m.g.huChonHd['HD-1'], 7000000);
    dung('Chi het bo canh bao lech', o.closest('.otd').className.indexOf('lech') < 0);
    o.value = '2.000.000'; o.dispatchEvent(dg.suKien('input', {}, o));
    m.tai.getElementById('huNhap').click();
    for (var i = 0; i < 5; i++) await new Promise(function (r) { setTimeout(r, 0); });
    var tao = m.goiApi.filter(function (r) { return r.duong === 'vagabond.ho_so_tt.tao'; });
    bang('mot lan tao', tao.length, 1);
    bang('payload2 trieu', JSON.parse(tao[0].ts.hoa_don)[0].so_tien, 2000000);
  });

  await caAsync('APP247 P1 vong 2: Chi cong ty cham moi vung o tien khong bo tick', async function () {
    var m = dungMan(canhChi({ supplier: { 'NCC-1': { supplier_name: 'NCC thử' } },
      hoaDon: { rows: [{ hoa_don: 'HD-1', ncc: 'NCC-1', ten_ncc: 'NCC thử',
        con_no: 10000000, co_the_chi: 7000000, dang_giu: 3000000 }] } }));
    m.g.huCpThue = 'Chi phi hop le'; m.g.huNguoi = 'NCC-1'; m.g.huTkChi = '11211 - VGB';
    await m.g.scrChiCongTyTao();
    m.tai.querySelector('[data-huhd]').click(); await choVeLai(m);
    var o = m.tai.querySelector('[data-hucttien]');
    o.value = '2000000'; o.dispatchEvent(dg.suKien('input', {}, o));
    var soLanGo = m.daGo.length;
    var vung = [o.closest('.otd').querySelector('.lb'), o.closest('.otd').querySelector('.dv'),
      m.tai.querySelector('[data-hulech]')];
    vung.forEach(function (n) {
      n.click();
      bang('Chi cong ty van giu 2 trieu', m.g.huChonHd['HD-1'], 2000000);
      bang('Chi cong ty khong ve lai man khi cham o tien', m.daGo.length, soLanGo);
    });
  });

  await caAsync('APP247 UX: man chon sao ke hoan ung dung checkbox that va mau chon chung', async function () {
    var m = dungMan(canhChi({}));
    await m.g.scrHuSepay({ ngan_hang: 'OCB', so_tk: '123', rows: [
      { ma_giao_dich: 'GD-1', ngay: '2026-09-10', noi_dung: 'Chi vat tu', so_tien: 120000 }
    ] });
    var tick = m.tai.querySelector('[data-hugdtick]');
    dung('sao ke hoan ung co checkbox that', !!tick && tick.tagName === 'INPUT');
    tick.click(); await choVeLai(m);
    dung('tick sao ke dung nen chon chung', m.tai.querySelector('[data-hugd]').className.indexOf('chon') >= 0);
    dung('tick sao ke khong dung ky tu gia', m.tai.querySelector('[data-hugd]').textContent.indexOf('☑') < 0);
  });

  await caAsync('APP247: nguoi lap khong co vai FIN khong thay nut can coc o ca hai man', async function () {
    var m = dungMan(canhChi({ vai: ['Purchase Manager', 'AP Officer'],
      nccChon: NCC_NO, supplier: { 'NCC-1': { supplier_name: 'NCC thử' } },
      hoaDon: { rows: [{ hoa_don: 'HD-1', ncc: 'NCC-1', ten_ncc: 'NCC thử',
        con_no: 1000000, co_the_chi: 1000000 }] } }));
    m.g.hsTaoNcc = 'NCC-1'; m.g.hsTaoLoai = 'NCC';
    await m.g.scrHoSoTTTao();
    dung('man APP khong bay nut khong bam duoc', !m.tai.getElementById('hsCanCoc'));
    dung('hiện lời nhắc kế toán', !!m.tai.getElementById('hsCanCocNhac'));
    m.g.huCpThue = 'Chi phi hop le'; m.g.huNguoi = 'NCC-1'; m.g.huTkChi = '11211 - VGB';
    await m.g.scrChiCongTyTao();
    dung('man chi cong ty khong bay nut khong bam duoc', !m.tai.getElementById('huCanCoc'));
    dung('hiện lời nhắc kế toán', !!m.tai.getElementById('huCanCocNhac'));
  });

  await caAsync('APP247: ke toan FIN van thay nut can coc o ca hai man', async function () {
    var m = dungMan(canhChi({ vai: ['Accounts User'], nccChon: NCC_NO,
      supplier: { 'NCC-1': { supplier_name: 'NCC thử' } },
      hoaDon: { rows: [{ hoa_don: 'HD-1', ncc: 'NCC-1', ten_ncc: 'NCC thử',
        con_no: 1000000, co_the_chi: 1000000 }] } }));
    m.g.hsTaoNcc = 'NCC-1'; m.g.hsTaoLoai = 'NCC';
    await m.g.scrHoSoTTTao();
    dung('man APP co nut', !!m.tai.getElementById('hsCanCoc'));
    dung('kế toán không có lời nhắc thừa', !m.tai.getElementById('hsCanCocNhac'));
    m.g.huCpThue = 'Chi phi hop le'; m.g.huNguoi = 'NCC-1'; m.g.huTkChi = '11211 - VGB';
    await m.g.scrChiCongTyTao();
    dung('man chi cong ty co nut', !!m.tai.getElementById('huCanCoc'));
    dung('kế toán không có lời nhắc thừa', !m.tai.getElementById('huCanCocNhac'));
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

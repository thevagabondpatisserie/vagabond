/* Bo ca kiem HANH VI v577: hop Khop tay va nut Huy phieu tren man Cong no.
 *
 * Ca that Loan Anh 05/10/2026, phieu DNTT-26-10-00004 (Ms.Dung, 8.450.000 d):
 * khach Kiet Tac chuyen 9.550.000 d. Hop Khop tay chi loc giao dich DUNG so
 * tien phieu nen giao dich that khong hien; Loan Anh chon "Khong thay giao
 * dich", go so tien, may bao xong ma 17 bill van o Dang no.
 *
 * Nap THAT 07-hop-thoai.js (hopKhung, hoiChon, hoiSo, hoiChu, hoiCo, baoTin),
 * 21-ke-toan-khac.js (cnKhopTay, cnHoiUnc) va 11-khach-ca-hop-dong.js (man
 * phieu, nut Huy). May chu va bo tai tep (43-tep-dinh-kem.js, da co ca kiem
 * rieng unc_app_518.js) la ban gia: tai tep len chi la dat danh sach duong dan
 * ma tdkDs se doc. Ca kiem chi bam nhu nguoi dung (quy tac 15).
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/khop_tay_577.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var domGia = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }

var ket = { dat: 0, hong: 0, loi: [] };
var xongHet = false;
process.on('exit', function () {
  if (!xongHet) { console.log('  HONG  bo kiem dung giua chung: co loi hua treo mai'); process.exitCode = 1; }
});
function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; }
  catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 4).join('\n         ') : String(e))); }
}
async function nghi() { for (var i = 0; i < 12; i++) await Promise.resolve(); await new Promise(function (r) { setImmediate(r); }); }
function chu(el) { return String(el.textContent || el.innerHTML || ''); }

var CAU_LON_HON = 'Giao dịch FT-KIETTAC là 9.550.000 đ, lớn hơn phần còn nợ chưa có phiếu thu của phiếu này (8.450.000 đ), dư 1.100.000 đ.';
var GD = [
  { ma: 'FT-DUNGSO', ngay: '2026-10-04', noi_dung: 'DNTT260900018', tien: 8450000, con: 8450000, dung_so: 1 },
  { ma: 'FT-KIETTAC', ngay: '2026-10-05', noi_dung: 'Kiet Tac doi soat Vagabond 8.9 nam 2026', tien: 9550000, con: 9550000, dung_so: 0 },
];
for (var i = 0; i < 8; i++) GD.push({ ma: 'FT-KHAC' + i, ngay: '2026-10-01', noi_dung: 'khach le ' + i, tien: 100000 + i, con: 100000 + i, dung_so: 0 });

function mayChu(tl) {
  var goi = [];
  return {
    goi: goi,
    cuoi: function (m) { var r = goi.filter(function (x) { return x.m === m; }); return r[r.length - 1]; },
    dem: function (m) { return goi.filter(function (x) { return x.m === m; }).length; },
    api: async function (m, a) {
      goi.push({ m: m, a: JSON.parse(JSON.stringify(a || {})) });
      if (m === 'vagabond.cong_no.tim_giao_dich_thu') {
        /* Codex #444 F2: may chu chi tra 300 dong moi nhat; khoan cu chi ra khi TIM. */
        if (tl.__nhieu) {
          if (a.tu_khoa) return { rows: tl.__nhieu.filter(function (r) { return r.noi_dung.toLowerCase().indexOf(a.tu_khoa.toLowerCase()) >= 0; }), tong: 1, con_nua: 0 };
          return { rows: tl.__nhieu.slice(0, 300), tong: tl.__nhieu.length, con_nua: tl.__nhieu.length - 300 };
        }
        return { rows: GD, tong: GD.length, con_nua: 0 };
      }
      if (m === 'vagabond.cong_no.khop_tay') {
        if (a.ma_giao_dich === 'FT-KIETTAC') throw new Error(CAU_LON_HON);
        return { ok: 1, pe: a.ma_giao_dich ? 'APP-1' : '', loi: [], loi_nhan: 'Đã ghi nhận.' };
      }
      if (m === 'vagabond.cong_no.xem_phieu') return tl.__phieu;
      if (m === 'vagabond.cong_no.huy_phieu') return { ok: 1, da_go_nhap: ['APP-26-10-134', 'APP-26-10-150'] };
      if (m === 'vagabond.cong_no.kiem_sepay') return tl.__sepay;
      return {};
    },
  };
}

function appMoi() {
  var tl = domGia.taiLieuGia();
  var vgb = tl.createElement('div'); vgb.id = 'vgb'; tl.body.appendChild(vgb);
  var mc = mayChu(tl);
  var tin = [], hoi = [], tep = {};
  var g = {
    console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array,
    Promise: Promise, Error: Error, RegExp: RegExp, parseFloat: parseFloat, parseInt: parseInt, isNaN: isNaN, Date: Date,
    encodeURIComponent: encodeURIComponent,
    document: tl,
    frappe: { session: { user: 'ntla.3008@gmail.com' } },
    location: { href: 'https://app.x/bep', pathname: '/bep', hostname: 'app.x', search: '', hash: '', replace: function () {} },
    history: { pushState: function () {}, replaceState: function () {}, back: function () {} },
    requestAnimationFrame: function (f) { f(); },
    setTimeout: function (f) { f(); return 1; }, clearTimeout: function () {},
    S: { me: { full_name: 'Loan Anh' }, user: 'ntla.3008@gmail.com' },
  };
  g.window = g;
  vm.createContext(g);
  vm.runInContext([
    'var root = document.getElementById("vgb");',
    'function h(s) { return String(s == null ? "" : s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;"); }',
    'function toast(s) { __tin.push("toast:" + s); }',
    'function busy() {}',
    'function dSkin() {}',
    'function money(x) { return String(x); }',
    'function hsNgayVn(x) { return String(x || ""); }',
    'function posNgayVn(x) { return String(x || ""); }',
    'function hsCopy() {}',
    'function posChipNut(thuoc, nhan) { return "<button " + thuoc + ">" + nhan + "</button>"; }',
    'function kmHangChip(noiDung) { return "<div>" + noiDung + "</div>"; }',
    'function errMsg(e) { return String((e && e.message) || e); }',
    'function api(m, a) { return __mc.api(m, a); }',
    'function confirmSheet(t, m) { __hoi.push(t + "\\n" + m); return Promise.resolve(true); }',
    'function go(f) { __tin.push("go"); }',
    /* Bo tai tep gia: tdkDs doc danh sach nguoi dung "da tai len". */
    'function tdkNap(id, ds) { __tep[id] = (ds || []).slice(); }',
    'function tdkKhoi(id) { return "<div data-tdkkhoi=\\"" + id + "\\"></div>"; }',
    'function tdkNoi() {}',
    'function tdkDs(id) { return __tep[id] || []; }',
  ].join('\n'), Object.assign(g, { __tin: tin, __mc: mc, __hoi: hoi, __tep: tep }));
  vm.runInContext(doc('01-khung-app.js'), g);
  vm.runInContext(doc('07-hop-thoai.js'), g);
  var kh = doc('11-khach-ca-hop-dong.js');
  vm.runInContext(doc('15-khuon-danh-sach.js'), g);
  vm.runInContext(kh, g);
  vm.runInContext(doc('21-ke-toan-khac.js'), g);
  /* Sau khi lam xong may chuyen man (go): ca kiem chi ghi lai, khong ve man
     khac, vi man dich da co bo kiem rieng. */
  vm.runInContext('go = function () { __tin.push("go"); };', g);
  return {
    g: g, tl: tl, mc: mc, tin: tin, hoi: hoi, tep: tep,
    tim: function (chon) { return tl.body.querySelectorAll(chon); },
    mot: function (chon) { var r = tl.body.querySelectorAll(chon); if (r.length !== 1) throw new Error('mong dung 1 ' + chon + ', co ' + r.length); return r[0]; },
    bam: async function (el) { el.dispatchEvent(domGia.suKien('click', {}, el)); await nghi(); await nghi(); },
    /* Go vao o dang mo (hoiSo, hoiChu) roi bam Xong. */
    go: async function (v) {
      var o = this.mot('#hqIn'); o.value = v;
      await this.bam(this.mot('[data-hqok]'));
    },
    /* Noi dung hop baoTin dang mo. */
    bao: function () { var r = tl.body.querySelectorAll('[data-hbok]'); return r.length ? chu(r[0].parentNode.parentNode) : ''; },
  };
}

var PHIEU = { name: 'DNTT-26-10-00004', ma_phieu: 'DNTT-26-10-00004', tong_tien: 8450000, con_thieu: 8450000 };

async function moKhop(app, them) {
  var d = Object.assign({}, PHIEU, them || {});
  /* Khong await cnKhopTay: hop dang cho nguoi bam. Tra lai loi hua trong mot
     doi tuong, de await moKhop khong cho luon ca chuoi. */
  var p = app.g.cnKhopTay(d);
  await nghi(); await nghi();
  return { xong: p };
}

(async function () {
  await ca('Ca Kiet Tac: hop Khop tay hien MOI giao dich chua noi, khoan dung so dau, ca giao dich 9.550.000 lon hon phieu', async function () {
    var app = appMoi();
    await moKhop(app);
    var t = app.mc.cuoi('vagabond.cong_no.tim_giao_dich_thu');
    bang('hoi may chu moi giao dich chua noi', [t.a.chua_noi, t.a.so_tien], [1, 8450000]);
    var muc = app.tim('[data-hc]');
    bang('muc Tim, du 10 giao dich va muc khong thay', muc.length, 12);
    bang('muc dau la Tim tren may chu', muc[0].getAttribute('data-hc'), '@tim');
    bang('khoan dung so dau tien', muc[1].getAttribute('data-hc'), 'FT-DUNGSO');
    dung('nhan dung so tien', chu(muc[1]).indexOf('đúng số tiền') >= 0);
    dung('giao dich Kiet Tac co trong hop', chu(muc[2]).indexOf('Kiet Tac doi soat') >= 0);
    dung('co o tim', app.tim('#hcTim').length === 1);
  });

  await ca('Chon giao dich 9.550.000: gui so khong vuot phieu, xac nhan noi lon hon, may chu tu choi thi bao dung cau', async function () {
    var app = appMoi();
    var p = (await moKhop(app)).xong;
    await app.bam(app.mot('[data-hc="FT-KIETTAC"]'));
    await app.go('Kiet Tac chuyen gop');
    var xn = chu(app.mot('[data-hkok]').parentNode.parentNode);
    dung('xac nhan noi giao dich lon hon: ' + xn.slice(0, 200), xn.indexOf('lớn hơn số phiếu còn phải thu') >= 0);
    await app.bam(app.mot('[data-hkok]'));
    await p;
    var k = app.mc.cuoi('vagabond.cong_no.khop_tay');
    bang('gui dung giao dich, so khong vuot phieu, khong UNC', [k.a.ma_giao_dich, k.a.so_tien, k.a.unc], ['FT-KIETTAC', 8450000, undefined]);
    dung('bao dung cau may chu', app.bao().indexOf('dư 1.100.000 đ') >= 0);
  });

  await ca('Sales chon "Khong thay giao dich": chi duong, KHONG hoi so tien, KHONG goi khop tay', async function () {
    var app = appMoi();
    var p = (await moKhop(app, { ke_toan: 0 })).xong;
    var muc = app.mot('[data-hc="@go_tay"]');
    dung('muc noi chi ke toan', chu(muc).indexOf('Chỉ kế toán') >= 0);
    await app.bam(muc);
    await p;
    bang('khong goi khop tay', app.mc.dem('vagabond.cong_no.khop_tay'), 0);
    bang('khong mo o nhap so', app.tim('#hqIn').length, 0);
    var b = app.bao();
    dung('bao chi ke toan: ' + b.slice(0, 120), b.indexOf('chỉ kế toán làm được') >= 0);
    dung('chi cach tim', b.indexOf('ô tìm') >= 0);
  });

  await ca('Ke toan chon "Khong thay": bat dinh UNC, chua tai thi khong qua, tai roi moi gui kem duong dan tep', async function () {
    var app = appMoi();
    var p = (await moKhop(app, { ke_toan: 1 })).xong;
    await app.bam(app.mot('[data-hc="@go_tay"]'));
    await app.go('8450000');
    dung('mo hop UNC', app.tim('[data-tdkkhoi="cnkunc"]').length === 1);
    await app.bam(app.mot('[data-cnkok]'));
    dung('chua tai thi nhac', app.bao().indexOf('Chọn ảnh chuyển khoản') >= 0);
    dung('hop UNC van mo', app.tim('[data-cnkok]').length === 1);
    await app.bam(app.mot('[data-hbok]'));
    app.tep.cnkunc = ['/private/files/unc-kiet-tac.jpg'];
    await app.bam(app.mot('[data-cnkok]'));
    await app.go('Khach chuyen tu tai khoan ca nhan');
    var xn = chu(app.mot('[data-hkok]').parentNode.parentNode);
    dung('xac nhan ke so tep UNC', xn.indexOf('kèm 1 tệp uỷ nhiệm chi') >= 0);
    await app.bam(app.mot('[data-hkok]'));
    await p;
    var k = app.mc.cuoi('vagabond.cong_no.khop_tay');
    bang('gui khong giao dich, kem UNC', [k.a.ma_giao_dich, k.a.so_tien, JSON.parse(k.a.unc)],
      ['', 8450000, ['/private/files/unc-kiet-tac.jpg']]);
  });

  await ca('Ke toan dong hop UNC (Thoi) thi khong goi khop tay', async function () {
    var app = appMoi();
    var p = (await moKhop(app, { ke_toan: 1 })).xong;
    await app.bam(app.mot('[data-hc="@go_tay"]'));
    await app.go('8450000');
    await app.bam(app.mot('[data-cnkx]'));
    await p;
    bang('khong goi khop tay', app.mc.dem('vagabond.cong_no.khop_tay'), 0);
  });

  await ca('Man phieu ket kieu Ms.Dung: co nut Huy, canh bao chi duong huy, xac nhan ke so nhap hong, goi huy', async function () {
    var app = appMoi();
    app.tl.__phieu = Object.assign({}, PHIEU, { khach: 'KL028403', ten_khach: 'Ms.Dung', trang_thai: 'Da thu du',
      da_thu: 8450000, sepay: 0, da_nhan: 8450000, con_thieu: 0, thieu_phieu_thu: 17, huy_duoc: 1, so_nhap_hong: 17,
      ke_toan: 0, qr: {}, han_qr: '2026-10-12', cac_khach: [], dong: [] });
    await app.g.scrCnPhieu('DNTT-26-10-00004'); await nghi();
    dung('canh bao chi duong huy roi gom lai', chu(app.tl.body).indexOf('rồi gom lại đủ các hoá đơn khách đã trả') >= 0);
    var nut = app.mot('#cnHuy');
    await app.bam(nut);
    dung('xac nhan ke 17 nhap hong, giu lai de tra: ' + app.hoi[0], app.hoi[0].indexOf('Máy gỡ 17 phiếu thu nháp hỏng') >= 0 && app.hoi[0].indexOf('giữ lại để tra') >= 0);
    bang('goi huy dung phieu', app.mc.cuoi('vagabond.cong_no.huy_phieu').a.name, 'DNTT-26-10-00004');
    dung('bao da go', app.tin.some(function (x) { return x.indexOf('Đã gỡ 2 phiếu thu nháp hỏng khỏi hoá đơn') >= 0; }));
  });

  await ca('Phieu da thu du ma may chu bao khong huy duoc thi KHONG co nut Huy', async function () {
    var app = appMoi();
    app.tl.__phieu = Object.assign({}, PHIEU, { trang_thai: 'Da thu du', da_thu: 8450000, sepay: 0, da_nhan: 8450000,
      con_thieu: 0, thieu_phieu_thu: 2, huy_duoc: 0, so_nhap_hong: 0, qr: {}, han_qr: '2026-10-12', cac_khach: [], dong: [] });
    await app.g.scrCnPhieu('DNTT-26-10-00004'); await nghi();
    bang('khong nut Huy', app.tim('#cnHuy').length, 0);
    dung('khong chi duong huy', chu(app.tl.body).indexOf('rồi gom lại đủ các hoá đơn khách đã trả') < 0);
    bang('van co nut Khop tay', app.tim('#cnKhop').length, 1);
  });

  await ca('Codex #444 F2: 450 giao dich chua noi, khoan Kiet Tac nam ngoai 300 dong: bam Tim, go ten, may chu tra ve, chon duoc', async function () {
    var app = appMoi();
    var nhieu = [];
    for (var j = 0; j < 449; j++) nhieu.push({ ma: 'FT-L' + j, ngay: '2026-10-01', noi_dung: 'khach le ' + j, tien: 100000 + j, con: 100000 + j, dung_so: 0 });
    nhieu.push({ ma: 'FT-KIETTAC', ngay: '2026-06-10', noi_dung: 'Kiet Tac doi soat Vagabond 8.9 nam 2026', tien: 8450000, con: 8450000, dung_so: 1 });
    app.tl.__nhieu = nhieu;
    var p = (await moKhop(app)).xong;
    bang('chua tim: khong co khoan Kiet Tac', app.tim('[data-hc="FT-KIETTAC"]').length, 0);
    dung('noi ro con bao nhieu khoan', chu(app.tl.body).indexOf('còn 150 khoản') >= 0);
    await app.bam(app.mot('[data-hc="@tim"]'));
    await app.go('kiet tac');
    bang('gui chu len may chu', app.mc.cuoi('vagabond.cong_no.tim_giao_dich_thu').a.tu_khoa, 'kiet tac');
    await app.bam(app.mot('[data-hc="FT-KIETTAC"]'));
    await app.go('Kiet Tac');
    await app.bam(app.mot('[data-hkok]'));
    await p;
    bang('khop dung giao dich tim ra', app.mc.cuoi('vagabond.cong_no.khop_tay').a.ma_giao_dich, 'FT-KIETTAC');
  });

  await ca('Codex #444 F1: tien da ve du ma phieu thu con nhap thi man KHONG bao cong no da sach', async function () {
    var app = appMoi();
    app.tl.__phieu = Object.assign({}, PHIEU, { trang_thai: 'Da thu du', da_thu: 8450000, sepay: 8450000, da_nhan: 8450000,
      con_thieu: 0, thieu_phieu_thu: 0, cho_ghi_so: 2, huy_duoc: 0, so_nhap_hong: 0, qr: {}, han_qr: '2026-10-12', cac_khach: [], dong: [] });
    await app.g.scrCnPhieu('DNTT-26-10-00004'); await nghi();
    dung('khong bao da sach', chu(app.tl.body).indexOf('đã sạch') < 0);
    dung('noi cho ke toan ghi so', chu(app.mot('[data-cnchoghiso]')).indexOf('2 hoá đơn đang ở tab Tiền đã về') >= 0);
    app.tl.__phieu.cho_ghi_so = 0;
    await app.g.scrCnPhieu('DNTT-26-10-00004'); await nghi();
    dung('so sach roi thi bao da sach', chu(app.tl.body).indexOf('Công nợ của khách này đã sạch') >= 0);
  });

  await ca('Codex #444 vong 2: bam Doi chieu SePay thay du tien ma con hoa don cho ghi so thi KHONG bao da xoa no', async function () {
    var app = appMoi();
    app.tl.__phieu = Object.assign({}, PHIEU, { trang_thai: 'Cho thu', da_thu: 0, sepay: 0, da_nhan: 0, con_thieu: 8450000,
      thieu_phieu_thu: 0, cho_ghi_so: 0, huy_duoc: 1, so_nhap_hong: 0, qr: {}, han_qr: '2026-10-12', cac_khach: [], dong: [] });
    await app.g.scrCnPhieu('DNTT-26-10-00004'); await nghi();
    app.tl.__sepay = { sepay: 8450000, tong_tien: 8450000, cho_ghi_so: 17 };
    await app.bam(app.mot('#cnKiem'));
    var t = app.tin.filter(function (x) { return x.indexOf('toast:') === 0; }).pop() || '';
    dung('khong bao da xoa no: ' + t, t.indexOf('xoá nợ') < 0);
    dung('noi 17 hoa don cho ghi so: ' + t, t.indexOf('17 hoá đơn chờ kế toán') >= 0);
    app.tl.__sepay = { sepay: 8450000, tong_tien: 8450000, cho_ghi_so: 0 };
    await app.bam(app.mot('#cnKiem'));
    t = app.tin.filter(function (x) { return x.indexOf('toast:') === 0; }).pop() || '';
    dung('so sach thi bao da xoa no: ' + t, t.indexOf('đã xoá nợ') >= 0);
  });

  console.log('Bo ca kiem HANH VI v577: hop Khop tay va Huy phieu ket (Loan Anh, Ms.Dung)');
  ket.loi.forEach(function (d) { console.log('  HONG  ' + d); });
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  xongHet = true;
  process.exit(ket.hong ? 1 : 0);
})();

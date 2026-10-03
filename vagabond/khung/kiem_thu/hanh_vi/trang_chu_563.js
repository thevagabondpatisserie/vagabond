/* Bo ca kiem HANH VI cho o tim nghiep vu, o ghim va viec gom nhom (v563).
 *
 * Nap THAT ca tep 02-trang-chu.js vao DOM gia, dung mot trang chu co san cac
 * dong [data-go] y nhu scrHome de lai, roi CHAY dung chuoi thao tac cua nhan
 * vien: mo trang chu, go vao o tim, bam nut ghim, bam o ghim, bam Sua ghim,
 * mo mot man phan he.
 *
 * Vi sao phai chay that chu khong do chuoi (CLAUDE.md dieu 16): ba viec quan
 * trong nhat o day deu khong the chung minh bang cach tim mot loi goi trong ma
 * nguon - ket qua tim co xep dung thu tu khong, bam nut ghim co mo nham man
 * khong, va o chua xep vao nhom co bien mat khoi man phan he khong.
 *
 * KHONG goi them ham nao "cho chac" ngoai chuoi thao tac (bai hoc 06/09/2026:
 * mot ca kiem goi openCoUI() "cho chac" da tu chua loi truoc khi kip nhin).
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/trang_chu_563.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
var SRC = fs.readFileSync(path.join(BEP, '02-trang-chu.js'), 'utf8');

/* Cac dong [data-go] ma scrHome de lai tren trang chu. Dung DUNG khuon HTML
   cua ham card() that (lay tu 02-trang-chu.js) chu khong bia khuon khac, vi
   vgbGomNhom doc lai chinh cai khuon do. */
function dong(k, ic, t1, t2, so) {
  return '<div class="hub" data-go="' + k + '"><div class="hi">' + ic + '</div>' +
    '<div class="ht"><div class="h1">' + t1 + '</div><div class="h2">' + t2 + '</div></div>' +
    (so ? '<span class="bdg">' + so + '</span>' : '') +
    '<span class="fc">&#8250;</span></div>';
}

var DONG = [
  dong('POS', '🧾', 'Tính tiền - hoá đơn bán hàng', 'Bán tại quầy, in bill', 0),
  dong('DTREO', '⏳', 'Đơn còn treo', 'Đơn chưa ghi sổ', 3),
  dong('KBD', '🎂', 'Kiểm bánh hôm nay', 'Đếm bánh đầu ngày', 0),
  dong('CN', '📒', 'Công nợ phải thu', 'Khách nào còn nợ mình', 0),
  dong('CNPT', '💸', 'Công nợ phải trả', 'Còn nợ nhà cung cấp nào', 0),
  dong('HDMUA', '🛒', 'Hoá đơn mua vào', 'Lọc theo nhà cung cấp, hạn trả', 0),
  dong('HDBAN', '🧾', 'Hoá đơn bán ra', 'Hoá đơn đã ghi sổ', 0),
  dong('DCM', '🔗', 'Đối chiếu hoá đơn mua', 'Nối hoá đơn NCC với phiếu nhập kho', 0),
  dong('HT', '↩️', 'Danh sách Phiếu hoàn tiền (Cash-back)', 'Hoàn tiền cho khách', 0),
  dong('APPTT', '📁', 'Tạo APP - Hồ sơ thanh toán', 'Lập hồ sơ trả tiền', 0),
  dong('BT', '🧮', 'Bút toán tay', 'Ghi bút toán tổng hợp', 0),
  dong('TS', '🏠', 'Tài sản và công cụ dụng cụ', 'Phân bổ hàng tháng', 0),
  dong('DUYETYC', '✅', 'Duyệt yêu cầu mua', 'Duyệt từng dòng', 0),
  dong('PO', '🧾', 'Đơn mua hàng', 'Đơn đã gửi nhà cung cấp', 0),
  dong('NCC', '🏭', 'Danh mục nhà cung cấp', 'Hồ sơ nhà cung cấp', 0),
  dong('BGIA', '💰', 'Bảng giá mua', 'Giá mua theo đơn vị mua', 0),
  dong('VD', '🛵', 'Vận đơn', 'Giao hàng trong ngày', 2),
  dong('PHIAPP', '🧾', 'Phí giao hàng book app', 'Phí trả cho app giao ngoài', 0),
  dong('DSCOD', '💵', 'Đối soát COD', 'Tiền shipper thu hộ', 0),
  dong('KK', '🧮', 'Kiểm kê kho', 'Đếm hàng thực tế', 0),
  dong('STOCK', '📊', 'Tra tồn kho', 'Tồn theo kho và theo mã', 0),
  dong('TONCHANG', '🪜', 'Tồn kho theo chặng', 'Tồn giữa các chặng', 0),
  /* O nay CO Y khong nam trong bang nhom nao cua phan he Giao hang, de ca
     kiem chot duoc rang o chua xep van hien chu khong bien mat. */
  dong('CPX', '⛽', 'Chi phí xăng xe - sửa xe', 'Tiền xe của tiệm', 0),
].join('');

function dungTrangChu(ghimTraVe) {
  var tai = dg.taiLieuGia();
  tai.head = new dg.ElementGia('head');
  var than = new dg.ElementGia('div');
  than.attrs.id = 'vgbBody';
  tai.body.appendChild(than);
  than.innerHTML = DONG;

  var goi = [];      /* moi lan goi may chu */
  var daGo = [];     /* moi lan dat dia chi qua vgbGo */
  var thongBao = []; /* moi cau toast */
  var khungVe = { t: '', el: null };

  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String,
    Array: Array, Object: Object, RegExp: RegExp, Date: Date, Promise: Promise,
    parseInt: parseInt, parseFloat: parseFloat, isNaN: isNaN, setTimeout: setTimeout,
    h: function (s) {
      return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
      });
    },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: ts });
      if (duong === 'vagabond.ghim.lay') {
        return Promise.resolve({ ghim: (ghimTraVe || []).slice(), toi_da: 5 });
      }
      if (duong === 'vagabond.ghim.luu') {
        return Promise.resolve({ ghim: JSON.parse(ts.ghim), toi_da: 5 });
      }
      return Promise.reject(new Error('khong co cua ' + duong));
    },
    toast: function (c) { thongBao.push(String(c)); },
    coQuyenKeToan: function () { return true; },
    coQuyenMua: function () { return true; },
    coQuyenHRM: function () { return true; },
    nenCoQuyen: function () { return false; },  /* vgbDemVCL ve ngay, khong goi mang */
    frame: function (t, html) {
      var el = new dg.ElementGia('div');
      el.parentNode = tai.body;
      tai.body.children.push(el);
      el.innerHTML = html;
      khungVe.t = t;
      khungVe.el = el;
      return el;
    },
    root: new dg.ElementGia('div'),
    location: { pathname: '/app/bep', search: '', hash: '' },
    history: { pushState: function () {}, replaceState: function () {} },
    money: function (x) { return String(x); },
    today: function () { return '2026-10-03'; },
    errMsg: function (e) { return String(e); },
  };
  that.globalThis = that;
  that.window = that;
  vm.runInNewContext(SRC, that, { filename: '02-trang-chu.js' });
  /* Dat lai vgbGo bang ban ghi nhan: ban that keo theo ca bang dinh tuyen va
     hang chuc man hinh khac, khong nap duoc trong node. Ca kiem o day chi can
     biet NO DUOC GOI VOI KHOA NAO - do dung la cho tung mat dia chi hom
     24/08/2026. */
  that.vgbGo = function (k) { daGo.push(k); };
  /* S.stack phai chua DUNG ham scrHome cua tep: vgbNapGhim chi ve lai o ghim
     khi nguoi dung con dung o trang chu, va no so bang === voi scrHome. */
  that.S = { stack: [that.scrHome], cuon: [0] };
  return { g: that, tai: tai, than: than, goi: goi, daGo: daGo, bao: thongBao, khung: khungVe };
}

var ket = { dat: 0, hong: 0, loi: [] };
function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) {
  if (a !== b) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b));
}
function tick() { return new Promise(function (r) { setTimeout(r, 5); }); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; ket.loi.push(ten); console.log('  HONG  ' + ten + '\n        ' + e.message); }
}

function bam(m, el) { m.than.onclick({ target: el }); }
function go(m, chu) {
  var o = m.tai.getElementById('vgbTim');
  o.value = chu;
  o.oninput();
  return o;
}

(async function () {
  console.log('\nO tim nghiep vu, o ghim va gom nhom (v563)\n');

  // ------------------------------------------------------------- o tim

  await ca('trang chu co o tim nghiep vu, nam tren luoi o lon', async function () {
    var m = dungTrangChu([]);
    m.g.vgbGomNhom();
    var o = m.tai.getElementById('vgbTim');
    dung('co o tim', !!o);
    bang('la o nhap', o.tagName, 'INPUT');
    dung('co luoi o lon', !!m.than.querySelector('.gwrap'));
    /* O tim phai nam TRUOC luoi trong cay DOM, khong thi phai cuon het trang
       chu moi thay no. */
    var ds = m.than.children;
    dung('o tim dung truoc luoi', ds.indexOf(m.than.querySelector('.vgbtimw')) <
      ds.indexOf(m.than.querySelector('.gwrap')));
  });

  await ca('go KHONG DAU van ra, va o dung ten dung tren o chi khop mo ta', async function () {
    var m = dungTrangChu([]);
    m.g.vgbGomNhom();
    go(m, 'cong no');
    var dsd = m.than.querySelectorAll('.vgbkqd');
    dung('co ket qua', dsd.length >= 2);
    var dau = dsd[0].querySelector('.h1').textContent;
    /* "Cong no phai thu" khop trong TEN; "Con no nha cung cap nao" chi khop
       trong mo ta cua o Cong no phai tra - nhung o do ten cung khop nen van
       len. Dieu phai chot la o chi khop MO TA (Hoa don mua vao, mo ta co
       "han tra") khong duoc chen len dau. */
    dung('dong dau la mot o Cong no, duoc: ' + dau, /^Công nợ/.test(dau));
  });

  await ca('go "don con treo" van ra, chu d gach cung phai bo dau', async function () {
    var m = dungTrangChu([]);
    m.g.vgbGomNhom();
    go(m, 'don con treo');
    var d = m.than.querySelectorAll('.vgbkqd');
    dung('co ket qua', d.length >= 1);
    bang('dong dau dung o', d[0].querySelector('.h1').textContent,
      '\u0110\u01a1n c\u00f2n treo');
  });

  await ca('go thi luoi o lon an di, xoa chu thi hien lai', async function () {
    var m = dungTrangChu([]);
    m.g.vgbGomNhom();
    go(m, 'cong no');
    bang('luoi an', m.than.querySelector('.gwrap').style.display, 'none');
    go(m, '');
    bang('luoi hien lai', m.than.querySelector('.gwrap').style.display, '');
    bang('khong con dong ket qua', m.than.querySelectorAll('.vgbkqd').length, 0);
  });

  await ca('go mot chu thi CHUA tim: mot chu ra ca tram o, khong giup gi', async function () {
    var m = dungTrangChu([]);
    m.g.vgbGomNhom();
    go(m, 'c');
    bang('chua co ket qua', m.than.querySelectorAll('.vgbkqd').length, 0);
    bang('luoi van hien', m.than.querySelector('.gwrap').style.display, '');
  });

  await ca('go them tu thi loc HEP lai chu khong no ra', async function () {
    var m = dungTrangChu([]);
    m.g.vgbGomNhom();
    go(m, 'cong no');
    var n1 = m.than.querySelectorAll('.vgbkqd').length;
    go(m, 'cong no phai tra');
    var n2 = m.than.querySelectorAll('.vgbkqd').length;
    dung('hep lai: ' + n1 + ' -> ' + n2, n2 > 0 && n2 < n1);
    bang('con dung o phai tra',
      m.than.querySelector('.vgbkqd').querySelector('.h1').textContent, 'Công nợ phải trả');
  });

  await ca('go tu khong co trong he thi noi ro khong khop, khong de man trong', async function () {
    var m = dungTrangChu([]);
    m.g.vgbGomNhom();
    go(m, 'zzzkhongcogi');
    bang('khong co dong ket qua', m.than.querySelectorAll('.vgbkqd').length, 0);
    dung('co cau noi khong khop', !!m.than.querySelector('.vgbtrong'));
  });

  await ca('bam ca dong ket qua thi mo man, bam bieu tuong cung mo man', async function () {
    var m = dungTrangChu([]);
    m.g.vgbGomNhom();
    go(m, 'van don');
    var d = m.than.querySelector('.vgbkqd');
    bam(m, d.querySelector('.hi'));
    bang('bam bieu tuong cung mo man', m.daGo.length, 1);
    bang('mo dung man', m.daGo[0], 'VD');
  });

  // -------------------------------------------------------------- ghim

  await ca('chua ghim gi thi khoi ghim AN hoan toan, khong chiem cho', async function () {
    var m = dungTrangChu([]);
    m.g.vgbGomNhom();
    await tick();
    bang('da hoi may chu', m.goi.filter(function (x) { return x.duong === 'vagabond.ghim.lay'; }).length, 1);
    bang('khong co khoi ghim', m.than.querySelectorAll('.vgbghim').length, 0);
  });

  await ca('bam nut ghim trong ket qua tim: khoi ghim hien ra va cat len may chu', async function () {
    var m = dungTrangChu([]);
    m.g.vgbGomNhom();
    await tick();
    go(m, 'cong no phai tra');
    bam(m, m.than.querySelector('[data-ghim]'));
    bang('mot o ghim', m.than.querySelectorAll('.vgbgo').length, 1);
    bang('bam nut ghim KHONG mo man', m.daGo.length, 0);
    await tick();
    var luu = m.goi.filter(function (x) { return x.duong === 'vagabond.ghim.luu'; });
    bang('da cat len may chu', luu.length, 1);
    bang('cat dung khoa', luu[0].ts.ghim, '["CNPT"]');
  });

  await ca('bam lai nut ghim thi BO ghim, khoi ghim an lai', async function () {
    var m = dungTrangChu(['CNPT']);
    m.g.vgbGomNhom();
    await tick();
    bang('co san mot o ghim', m.than.querySelectorAll('.vgbgo').length, 1);
    go(m, 'cong no phai tra');
    dung('nut ghim dang bat', m.than.querySelector('[data-ghim]').attrs['class'].indexOf('on') >= 0);
    bam(m, m.than.querySelector('[data-ghim]'));
    bang('het o ghim', m.than.querySelectorAll('.vgbgo').length, 0);
    await tick();
    var luu = m.goi.filter(function (x) { return x.duong === 'vagabond.ghim.luu'; });
    bang('cat danh sach rong', luu[luu.length - 1].ts.ghim, '[]');
  });

  await ca('ghim o thu sau bi chan, va KHONG day o cu nao ra', async function () {
    var m = dungTrangChu(['POS', 'DTREO', 'KBD', 'CN', 'CNPT']);
    m.g.vgbGomNhom();
    await tick();
    bang('nam o ghim', m.than.querySelectorAll('.vgbgo').length, 5);
    go(m, 'van don');
    bam(m, m.than.querySelector('[data-ghim]'));
    bang('van nam o, khong thanh sau', m.g.VGB_GHIM.length, 5);
    bang('o cu dau tien con nguyen', m.g.VGB_GHIM[0], 'POS');
    dung('co noi ly do', m.bao.join(' ').indexOf('5') >= 0);
    await tick();
    bang('khong cat gi len may chu',
      m.goi.filter(function (x) { return x.duong === 'vagabond.ghim.luu'; }).length, 0);
  });

  await ca('bam o ghim thi mo dung man do', async function () {
    var m = dungTrangChu(['PHIAPP']);
    m.g.vgbGomNhom();
    await tick();
    bam(m, m.than.querySelector('.vgbgo').querySelector('.vgbgn'));
    bang('mo mot man', m.daGo.length, 1);
    bang('dung man Phi giao hang book app', m.daGo[0], 'PHIAPP');
  });

  await ca('bam Sua ghim thi hien dau X, va bam X la bo ghim chu khong mo man', async function () {
    var m = dungTrangChu(['PHIAPP', 'POS']);
    m.g.vgbGomNhom();
    await tick();
    bang('chua sua thi khong co dau X', m.than.querySelectorAll('.vgbgx').length, 0);
    bam(m, m.than.querySelector('[data-suaghim]'));
    bang('hien dau X tren tung o', m.than.querySelectorAll('.vgbgx').length, 2);
    bam(m, m.than.querySelectorAll('.vgbgx')[0]);
    bang('KHONG mo man', m.daGo.length, 0);
    bang('con mot o ghim', m.g.VGB_GHIM.length, 1);
    bang('bo dung o', m.g.VGB_GHIM[0], 'POS');
  });

  await ca('ghim tro tim man nguoi nay khong con quyen xem thi bi bo im lang', async function () {
    /* Chi Dung ghim o Duyet yeu cau mua, sau do bi rut quyen thu mua. Lan mo
       app sau, o do khong con trong VGB_HUB. Neu cu ve thi ra mot o trong bam
       vao khong co gi, hoac vo. */
    var m = dungTrangChu(['DUYETYC', 'khong-ton-tai', 'POS']);
    m.g.vgbGomNhom();
    delete m.g.VGB_HUB.DUYETYC;
    await m.g.vgbNapGhim();
    bang('chi con o con dung duoc', m.g.VGB_GHIM.length, 1);
    bang('dung o con lai', m.g.VGB_GHIM[0], 'POS');
  });

  await ca('may chu hong thi trang chu van dung, khong vo', async function () {
    var m = dungTrangChu([]);
    m.g.api = function () { return Promise.reject(new Error('mang hong')); };
    m.g.vgbGomNhom();
    await tick();
    dung('luoi o lon van con', !!m.than.querySelector('.gwrap'));
    dung('o tim van con', !!m.tai.getElementById('vgbTim'));
    bang('khong ghim gi', m.g.VGB_GHIM, null);
  });

  // ------------------------------------------------------------ gom nhom

  await ca('man phan he ve theo nhom, co nhan nhom va ghi chu', async function () {
    var m = dungTrangChu([]);
    m.g.vgbGomNhom();
    m.g.scrNhom(m.g.vgbNhomTheoKhoa('KT'));
    var nhan = m.khung.el.querySelectorAll('.sec').map(function (x) {
      return x.querySelector('i') ? x.textContent.replace(x.querySelector('i').textContent, '') : x.textContent;
    });
    dung('co nhan Hoa don', nhan.indexOf('Hoá đơn') >= 0);
    dung('co nhan Cong no', nhan.indexOf('Công nợ') >= 0);
    dung('co ghi chu nho', m.khung.el.querySelectorAll('.sec').filter(
      function (x) { return !!x.querySelector('i'); }).length > 0);
    bang('tieu de man', m.khung.t, 'Kế toán');
  });

  await ca('nhom Cong no chi gom hai o phai thu va phai tra, dung thu tu', async function () {
    var m = dungTrangChu([]);
    m.g.vgbGomNhom();
    var nhom = m.g.vgbChiaNhom(m.g.vgbNhomTheoKhoa('KT'), function (k) { return !!m.g.VGB_HUB[k]; });
    var cn = nhom.filter(function (x) { return x.t === 'Công nợ'; })[0];
    dung('co nhom Cong no', !!cn);
    bang('dung hai o, dung thu tu', cn.keys.join(','), 'CN,CNPT');
  });

  await ca('o chua xep vao nhom nao KHONG bien mat, no roi xuong nhom Khac', async function () {
    var m = dungTrangChu([]);
    m.g.vgbGomNhom();
    /* Day la cho de mat nut nhat: them nghiep vu moi la viec hang tuan, con
       nho sua bang nhom thi khong. Dung mot phan he GIA vi moi phan he that
       hien dang xep het o - ca kiem ben Python chot viec do. */
    var nh = {
      k: 'THU', ten: 'Thu', keys: ['POS', 'KBD', 'CPX'],
      nhom: [{ t: 'A', p: '', keys: ['POS', 'KBD'] }],
    };
    var nhom = m.g.vgbChiaNhom(nh, function (k) { return !!m.g.VGB_HUB[k]; });
    bang('hai nhom', nhom.length, 2);
    bang('nhom cuoi ten Khac', nhom[1].t, 'Kh\u00e1c');
    bang('o chua xep nam o do', nhom[1].keys.join(','), 'CPX');
    /* Va khi ve ra man thi khong thieu o nao. */
    m.g.scrNhom(nh);
    bang('so dong tren man', m.khung.el.querySelectorAll('[data-go]').length, 3);
  });

  await ca('phan he khong khai nhom thi ve nhu truoc, khong them nhan nao', async function () {
    var m = dungTrangChu([]);
    m.g.vgbGomNhom();
    m.g.scrNhom(m.g.vgbNhomTheoKhoa('KK'));
    bang('khong co nhan nhom', m.khung.el.querySelectorAll('.sec').length, 0);
    bang('du ba o', m.khung.el.querySelectorAll('[data-go]').length, 3);
  });

  await ca('khoa danh may sai trong bang nhom KHONG lot vao man khac', async function () {
    var m = dungTrangChu([]);
    m.g.vgbGomNhom();
    var nh = {
      k: 'THU', ten: 'Thu', keys: ['POS', 'KBD'],
      /* HDBAN co that trong he, nhung KHONG thuoc keys cua phan he nay. */
      nhom: [{ t: 'A', p: '', keys: ['POS', 'HDBAN'] }],
    };
    var nhom = m.g.vgbChiaNhom(nh, function (k) { return !!m.g.VGB_HUB[k]; });
    var moi = [];
    nhom.forEach(function (x) { moi = moi.concat(x.keys); });
    dung('khong keo HDBAN vao', moi.indexOf('HDBAN') < 0);
    bang('du hai o cua phan he', moi.sort().join(','), 'KBD,POS');
  });

  await ca('mot o khai trong HAI nhom chi ve MOT lan', async function () {
    var m = dungTrangChu([]);
    m.g.vgbGomNhom();
    var nh = {
      k: 'THU', ten: 'Thu', keys: ['POS', 'KBD'],
      nhom: [{ t: 'A', p: '', keys: ['POS'] }, { t: 'B', p: '', keys: ['POS', 'KBD'] }],
    };
    var nhom = m.g.vgbChiaNhom(nh, function (k) { return !!m.g.VGB_HUB[k]; });
    var moi = [];
    nhom.forEach(function (x) { moi = moi.concat(x.keys); });
    bang('khong ve trung', moi.join(','), 'POS,KBD');
  });

  await ca('hai o ban khung cua Thu mua da an, va man Thu mua con dung o', async function () {
    var m = dungTrangChu([]);
    m.g.vgbGomNhom();
    var tm = m.g.vgbNhomTheoKhoa('TM');
    dung('khong con KHPO trong phan he', tm.keys.indexOf('KHPO') < 0);
    dung('khong con KHHDM trong phan he', tm.keys.indexOf('KHHDM') < 0);
    m.g.scrNhom(tm);
    bang('man Thu mua con nam o', m.khung.el.querySelectorAll('[data-go]').length, 5);
  });

  console.log('\n' + ket.dat + ' ca dat, ' + ket.hong + ' ca hong.');
  process.exit(ket.hong ? 1 : 0);
})();

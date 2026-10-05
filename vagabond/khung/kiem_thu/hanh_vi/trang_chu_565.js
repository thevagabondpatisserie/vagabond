/* Bo ca kiem HANH VI cho o tim nghiep vu, o ghim va viec gom nhom (v565).
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
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/trang_chu_565.js
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

function dungTrangChu(ghimTraVe, hoan) {
  hoan = hoan || {};
  var tai = dg.taiLieuGia();
  tai.head = new dg.ElementGia('head');
  var than = new dg.ElementGia('div');
  than.attrs.id = 'vgbBody';
  tai.body.appendChild(than);
  than.innerHTML = DONG;

  var goi = [];      /* moi lan goi may chu */
  var catXong = [];  /* thu tu may chu NHAN duoc tung ban ghim */
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
        /* Giu lai loi hua khi ca kiem muon tu quyet dinh luc may chu tra ve
           (ca "go o tim TRUOC khi may chu tra ve"). */
        if (hoan.lay) {
          return new Promise(function (r) {
            hoan.traLay = function () { r({ ghim: (ghimTraVe || []).slice(), toi_da: 5 }); };
          });
        }
        return Promise.resolve({ ghim: (ghimTraVe || []).slice(), toi_da: 5 });
      }
      if (duong === 'vagabond.ghim.luu') {
        var n = JSON.parse(ts.ghim).length;
        /* Cho phep ca kiem dat do tre theo so o, de dung lai canh may that:
           goi di truoc chua chac ve truoc. */
        var tre = hoan.treLuu ? hoan.treLuu(n) : 0;
        if (!tre) { catXong.push(ts.ghim); return Promise.resolve({ ghim: JSON.parse(ts.ghim), toi_da: 5 }); }
        return new Promise(function (r) {
          setTimeout(function () { catXong.push(ts.ghim); r({ ghim: JSON.parse(ts.ghim), toi_da: 5 }); }, tre);
        });
      }
      if (duong === 'vagabond.khung.ds.danh_ba') {
        /* Danh ba quyen. Giu lai loi hua khi ca kiem muon tu quyet dinh luc
           no ve, de dung lai canh "danh ba ve muon". */
        if (hoan.danhBa) {
          return new Promise(function (r) {
            hoan.traDanhBa = function (v) { r(v || hoan.dsDanhBa || []); };
          });
        }
        return Promise.resolve(hoan.dsDanhBa || []);
      }
      return Promise.reject(new Error('khong co cua ' + duong));
    },
    toast: function (c) { thongBao.push(String(c)); },
    /* Hop chon gia (v571): ghi lai danh sach duoc dua ra, tra ve khoa ca
       kiem dat san trong hoan.chon (null la bam Thoi). */
    hoiChon: function (tua, moTa, ds) {
      hoan.hoiChon = { tua: tua, moTa: moTa, ds: ds };
      return Promise.resolve(hoan.chon === undefined ? null : hoan.chon);
    },
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
  return { g: that, tai: tai, than: than, goi: goi, daGo: daGo, bao: thongBao,
    khung: khungVe, catXong: catXong, hoan: hoan };
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
  console.log('\nO tim nghiep vu, o ghim va gom nhom (v565)\n');

  // ------------------------------------------------------------- o tim

  await ca('trang chu co o tim nghiep vu, nam tren luoi o lon', async function () {
    var m = dungTrangChu([]);
    m.g.vgbGomNhom();
    var o = m.tai.getElementById('vgbTim');
    dung('co o tim', !!o);
    bang('la o nhap', o.tagName, 'INPUT');
    dung('co luoi o lon', !!m.than.querySelector('.gwrap'));
    /* O tim phai nam TRUOC phan thay doi trong cay DOM, khong thi phai cuon
       het trang chu moi thay no. Tu vong 2 cua #426, phan thay doi nam trong
       #vgbDuoi de luot gom sau khong dung toi o nhap. */
    var ds = m.than.children;
    dung('co khung #vgbDuoi rieng', !!m.tai.getElementById('vgbDuoi'));
    dung('o tim dung truoc phan thay doi', ds.indexOf(m.than.querySelector('.vgbtimw')) <
      ds.indexOf(m.tai.getElementById('vgbDuoi')));
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

  /* DOI LUAT v571 (anh Viet 04/10/2026 "sao khong thay bang ghim app hay
     dung?"). Ban v565 an han khoi ghim khi chua ghim gi; do tren site that
     thi khong tai khoan nao ghim duoc o nao vi khong ai thay loi vao. Nay
     chua ghim gi thi hien mot dai MOI GHIM, khong phai an han. Dung sua ca
     nay ve nhu cu. */
  await ca('chua ghim gi thi hien dai MOI GHIM, khong o ghim nao', async function () {
    var m = dungTrangChu([]);
    m.g.vgbGomNhom();
    await tick();
    bang('da hoi may chu', m.goi.filter(function (x) { return x.duong === 'vagabond.ghim.lay'; }).length, 1);
    bang('co dai moi ghim', m.than.querySelectorAll('.vgbgtrong').length, 1);
    bang('khong co o ghim nao', m.than.querySelectorAll('.vgbgo').length, 0);
    dung('noi ro bam vao de ghim', /Ch\u1ecdn \u00f4 \u0111\u1ec3 ghim/.test(m.tai.getElementById('vgbGhimW').innerHTML));
  });

  await ca('v571: bam dai moi ghim, chon mot o thi o do duoc ghim va cat len may chu', async function () {
    var hoan = { chon: 'CNPT' };
    var m = dungTrangChu([], hoan);
    m.g.vgbGomNhom();
    await tick();
    bam(m, m.than.querySelector('.vgbgm'));
    await tick();
    dung('da mo hop chon', !!hoan.hoiChon);
    dung('hop chon co o Cong no phai tra', hoan.hoiChon.ds.some(function (x) { return x.k === 'CNPT'; }));
    bang('mot o ghim', m.than.querySelectorAll('.vgbgo').length, 1);
    bang('bam dai KHONG mo man nao', m.daGo.length, 0);
    var luu = m.goi.filter(function (x) { return x.duong === 'vagabond.ghim.luu'; });
    bang('cat dung khoa', luu[luu.length - 1].ts.ghim, '["CNPT"]');
  });

  await ca('v571: bam Thoi trong hop chon thi khong ghim gi, khong cat gi', async function () {
    var hoan = {};
    var m = dungTrangChu([], hoan);
    m.g.vgbGomNhom();
    await tick();
    bam(m, m.than.querySelector('.vgbgtrong'));
    await tick();
    bang('khong o ghim', m.than.querySelectorAll('.vgbgo').length, 0);
    bang('khong cat', m.goi.filter(function (x) { return x.duong === 'vagabond.ghim.luu'; }).length, 0);
  });

  await ca('v571: da ghim vai o thi co o Them, hop chon KHONG dua lai o da ghim', async function () {
    var hoan = { chon: 'VD' };
    var m = dungTrangChu(['POS', 'CN'], hoan);
    m.g.vgbGomNhom();
    await tick();
    var them = m.than.querySelector('.vgbgthem');
    dung('co o Them', !!them);
    bam(m, them.querySelector('.vgbgn'));
    await tick();
    dung('khong dua lai POS', !hoan.hoiChon.ds.some(function (x) { return x.k === 'POS'; }));
    dung('khong dua lai CN', !hoan.hoiChon.ds.some(function (x) { return x.k === 'CN'; }));
    bang('ba o, o moi o cuoi', m.g.VGB_GHIM.join(','), 'POS,CN,VD');
  });

  await ca('v571: du 5 o thi het o Them; dang Sua ghim cung an o Them', async function () {
    var m = dungTrangChu(['POS', 'DTREO', 'KBD', 'CN', 'CNPT']);
    m.g.vgbGomNhom();
    await tick();
    bang('du 5 khong co o Them', m.than.querySelectorAll('.vgbgthem').length, 0);
    var m2 = dungTrangChu(['POS']);
    m2.g.vgbGomNhom();
    await tick();
    bam(m2, m2.than.querySelector('[data-suaghim]'));
    bang('dang sua khong co o Them', m2.than.querySelectorAll('.vgbgthem').length, 0);
  });

  await ca('Codex #437 vong 10: du 5 ghim nhung mot o mat quyen thi van them duoc', async function () {
    /* Dung lai canh: 5 ghim, danh ba ve chi con 4 o. Thu tren 2b069d9:
       danh ba ve thi vgbDonGhim tu go o mat quyen nen o Them hien lai; chua
       tai hien duoc canh "danh ba da biet ma chua go". Van khoa them hai cho:
       dem theo o con quyen, va go truoc khi tinh cho trong o hop chon. */
    var hoan = { danhBa: true, chon: 'VD' };
    var m = dungTrangChu(['POS', 'DTREO', 'KBD', 'CN', 'DM:DMSP'], hoan);
    m.g.vgbGomNhom();
    await tick();
    var p = m.g.vgbNapKhungCo();
    await tick();
    m.hoan.traDanhBa(['POS', 'DTREO', 'KBD', 'CN', 'VD', 'CNPT']);
    await p;
    await new Promise(function (r) { setTimeout(r, 40); });
    var them = m.than.querySelector('.vgbgthem');
    dung('co o Them', !!them);
    bam(m, them.querySelector('.vgbgn'));
    await new Promise(function (r) { setTimeout(r, 20); });
    dung('mo duoc hop chon', !!hoan.hoiChon);
    dung('da ghim o moi', m.g.VGB_GHIM.indexOf('VD') >= 0);
    dung('khong con o mat quyen', m.g.VGB_GHIM.indexOf('DM:DMSP') < 0);
  });

  await ca('v571: may chu hong thi KHONG hien dai moi ghim', async function () {
    var m = dungTrangChu([]);
    m.g.api = function () { return Promise.reject(new Error('mang hong')); };
    m.g.vgbGomNhom();
    await tick();
    bang('khong dai moi ghim', m.than.querySelectorAll('.vgbgtrong').length, 0);
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
    /* Danh ba quyen DA biet. Tu vong 2 cua #426, chua biet danh ba thi KHONG
       loc - mat mang khong phai la mat quyen (ca #426-R2F2b chot cho do). */
    m.g.VGB_KHUNG_CO = {};
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

  // ----------------------------------- bon finding cua Codex tren PR #426

  await ca('#426-1: luot gom THU HAI khong duoc nhan o ghim lam dong goc', async function () {
    /* Codex: vgbNapKhungCo ve muon thi vgbGomNhom chay lan hai. Tu v565 trang
       chu co them o ghim va ket qua tim, ca hai deu mang [data-go]. Luot hai
       doc phai chung va ghi de VGB_DONG_GOC. Do tren DOM gia voi mot o ghim:
       23 o nguon con 1, luoi mat gan het phan he. */
    var m = dungTrangChu(['POS']);
    m.g.vgbGomNhom();
    var truoc = Object.keys(m.g.VGB_DONG_GOC).length;
    await tick();
    bang('da ve o ghim', m.than.querySelectorAll('.vgbgo').length, 1);
    var luoiTruoc = m.than.querySelectorAll('.gt').length;
    m.g.vgbGomNhom();                      /* danh ba may chu ve muon */
    bang('so o nguon khong doi', Object.keys(m.g.VGB_DONG_GOC).length, truoc);
    bang('luoi o lon khong mat o nao', m.than.querySelectorAll('.gt').length, luoiTruoc);
  });

  await ca('#426-1b: gom lai trong luc DANG go o tim cung khong an mat o', async function () {
    var m = dungTrangChu([]);
    m.g.vgbGomNhom();
    var truoc = Object.keys(m.g.VGB_DONG_GOC).length;
    go(m, 'cong no');
    dung('dang co ket qua tim', m.than.querySelectorAll('.vgbkqd').length > 0);
    m.g.vgbGomNhom();
    bang('so o nguon khong doi', Object.keys(m.g.VGB_DONG_GOC).length, truoc);
  });

  await ca('#426-2: go o tim TRUOC khi may chu tra ve ghim thi ket qua phai ve lai', async function () {
    /* Codex: nut ghim hien o trang thai tat du o do da duoc ghim, bam vao la
       BO ghim chu khong phai ghim. */
    var m = dungTrangChu(['CNPT'], { lay: true });
    m.g.vgbGomNhom();
    go(m, 'cong no phai tra');
    bang('chua tra ve thi nut chua bat',
      m.than.querySelector('[data-ghim]').attrs['class'].indexOf('on') >= 0, false);
    m.hoan.traLay();
    await tick();
    dung('tra ve roi thi nut phai BAT',
      m.than.querySelector('[data-ghim]').attrs['class'].indexOf('on') >= 0);
    bam(m, m.than.querySelector('[data-ghim]'));
    bang('bam mot cai la BO ghim, khong phai ghim lai', m.g.VGB_GHIM.length, 0);
  });

  await ca('#426-3: bam hai o lien tiep thi ban cat SAU CUNG phai la ban moi nhat', async function () {
    /* Codex: hai loi goi chay song song co the ve nguoc thu tu, may chu giu
       ban cu trong khi man hien ban moi. Dat lan gui dau cham hon lan sau de
       dung lai dung canh do. */
    var m = dungTrangChu([], { treLuu: function (n) { return n === 1 ? 60 : 10; } });
    m.g.vgbGomNhom();
    await tick();
    m.g.vgbBatGhim('POS');
    m.g.vgbBatGhim('CNPT');
    await new Promise(function (r) { setTimeout(r, 200); });
    bang('may chu nhan ban cuoi dung bang man hinh',
      m.catXong[m.catXong.length - 1], JSON.stringify(m.g.VGB_GHIM));
    bang('man hinh dang hien hai o', m.g.VGB_GHIM.join(','), 'POS,CNPT');
  });

  await ca('#426-2b: bam ghim khi DANG go tim thi nut trong ket qua phai doi ngay', async function () {
    /* Them sau khi doc ket qua dot bien: dot bien "bam ghim xong chi ve khoi
       ghim" KHONG lam do ca nao, nghia la bo kiem yeu that (CLAUDE.md dieu
       17a). Ca nay vao dung cho do. */
    var m = dungTrangChu([]);
    m.g.vgbGomNhom();
    await tick();
    go(m, 'cong no phai tra');
    var nut = m.than.querySelector('[data-ghim]');
    bang('truoc khi bam thi nut tat', nut.attrs['class'].indexOf('on') >= 0, false);
    bam(m, nut);
    dung('bam xong nut trong KET QUA phai bat ngay',
      m.than.querySelector('[data-ghim]').attrs['class'].indexOf('on') >= 0);
    bam(m, m.than.querySelector('[data-ghim]'));
    bang('bam lan nua thi tat lai',
      m.than.querySelector('[data-ghim]').attrs['class'].indexOf('on') >= 0, false);
  });

  await ca('#426-3b: luot cat da bi luot sau vuot mat thi KHONG goi may chu nua', async function () {
    /* Hang doi mot minh da du giu dung thu tu (dot bien "bo phep bo luot" van
       xanh - CLAUDE.md dieu 17c, con mot lop do). Phep bo luot la de khong
       ban ba lan mang cho ba lan bam lien tiep, nen phai co ca rieng giu no,
       khong thi lan sau ai go di cung khong ai biet. */
    var m = dungTrangChu([], { treLuu: function () { return 40; } });
    m.g.vgbGomNhom();
    await tick();
    m.g.vgbBatGhim('POS');
    m.g.vgbBatGhim('CNPT');
    m.g.vgbBatGhim('VD');
    await new Promise(function (r) { setTimeout(r, 250); });
    var luu = m.goi.filter(function (x) { return x.duong === 'vagabond.ghim.luu'; });
    /* Ba lan bam lien tiep chi ban mang DUNG MOT lan: luot 1 va 2 deu bi
       luot 3 vuot mat ngay trong cung mot nhip, nen ca hai bi bo. Doi so nay
       la doi hanh vi, khong phai sua cho vua ca kiem - no phai la 1. */
    bang('ba lan bam chi ban mang mot lan', luu.length, 1);
    bang('ban cuoi la trang thai moi nhat',
      m.catXong[m.catXong.length - 1], JSON.stringify(m.g.VGB_GHIM));
  });

  await ca('#426-4: khai bao CSS cho vung bam, va GHI CHU vi sao cho nay con yeu', async function () {
    /* DOC KY TRUOC KHI SUA CA NAY.
     *
     * Ca nay DO CHUOI, va do chuoi KHONG chung minh duoc vung bam. Vong 2 cua
     * #426 da chung minh dung dieu do: ban dau `.vgbgb` khai 44x44, ca nay
     * xanh, nhung do that tren Chromium 390x844 ra 21x19 - vi `.vgbgb` la the
     * <span>, ma span mac dinh `display:inline` nen trinh duyet bo qua width
     * va height. Dau X cung vay: khai 44x44, do that ra 44x29 vi dai o ghim
     * co overflow-x:auto nen trinh duyet cat phan tran ra ngoai mep.
     *
     * Vi vay ca nay CHI chot nhung thu khong the quen: cac khai bao ma thieu
     * chung thi chac chan sai. Con phep do THAT nam o
     * vagabond/khung/kiem_thu/do_vung_bam_565.js, chay bang Chromium, va phai
     * chay no truoc khi ban giao giao dien. No khong nam trong cong vi may
     * chay CI cua GitHub khong co trinh duyet.
     */
    var m = dungTrangChu([]);
    m.g.vgbCss();
    var css = m.tai.head.children.map(function (x) { return x.textContent; }).join('');
    dung('nut ghim khai 44 diem', css.indexOf('width:44px;height:44px') >= 0);
    /* Dong nay la cai da tung thieu va lam vung bam that con 21x19. */
    dung('nut ghim KHONG con la the inline',
      /\.vgbgb\{[^}]*display:inline-flex/.test(css));
    dung('dau X co lop phu noi rong vung bam',
      /\.vgbgx::after\{[^}]*width:44px;height:44px/.test(css));
    /* Dau X phai nam HAN TRONG o, khong treo ra ngoai mep: treo ra ngoai la
       bi dai cuon ngang cat mat mot nua vung bam. */
    dung('dau X khong treo ra ngoai mep o', /\.vgbgx\{[^}]*top:10px;right:10px/.test(css));
    dung('ten o ghim khong duoi 13 diem', css.indexOf('.vgbgn{font-size:13px') >= 0);
  });

  // --------------------------- bon finding vong 2 cua Codex tren PR #426

  await ca('#426-R2F1: bam ghim TRUOC khi doc xong thi khong duoc mat ghim cu', async function () {
    /* Codex: `(VGB_GHIM || [])` coi "chua doc" la "chua ghim gi", nen bam mot
       o luc dang cho se cat len may chu dung o do va xoa sach ghim cu. Do
       duoc: ghim san ["CNPT"], bam POS truoc khi doc ve -> may chu giu
       ["POS"] con man hien ["CNPT"]. */
    var m = dungTrangChu(['CNPT'], { lay: true });
    m.g.vgbGomNhom();
    go(m, 'tinh tien');
    bam(m, m.than.querySelector('[data-ghim]'));
    await tick();
    m.hoan.traLay();
    await new Promise(function (r) { setTimeout(r, 40); });
    bang('giu ca ghim cu lan ghim moi', m.g.VGB_GHIM.join(','), 'CNPT,POS');
    bang('may chu giu dung cai man dang hien',
      m.catXong[m.catXong.length - 1], JSON.stringify(m.g.VGB_GHIM));
  });

  await ca('#429-R3F1: doc ghim hong mot lan thi lan sau PHAI hoi lai may chu', async function () {
    /* Codex bat R3-F1: ban cu giu lai loi hua da hong trong VGB_GHIM_NAP, nen
       moi lan mo lai trang chu va moi lan bam ghim deu dung lai dung ket qua
       hong do. Cau "Mo lai trang chu roi thu lai" ma chinh man hinh hien ra
       thanh loi noi suong: khong co duong nao hoi lai tru khi tai lai ca app. */
    var hong = true, soLanDoc = 0;
    var m = dungTrangChu([]);
    var apiThat = m.g.api;
    m.g.api = function (duong, ts) {
      if (duong === 'vagabond.ghim.lay') {
        soLanDoc++;
        if (hong) return Promise.reject(new Error('mang hong'));
        return Promise.resolve({ ghim: ['CNPT'], toi_da: 5 });
      }
      return apiThat(duong, ts);
    };
    m.g.vgbGomNhom();
    await new Promise(function (r) { setTimeout(r, 30); });
    bang('lan dau da hoi', soLanDoc, 1);
    bang('chua co ghim', m.g.VGB_GHIM, null);
    /* Mang tot tro lai. Nguoi dung mo lai trang chu dung nhu cau toast bao. */
    hong = false;
    m.g.vgbGomNhom();
    await new Promise(function (r) { setTimeout(r, 30); });
    bang('da hoi lai may chu', soLanDoc, 2);
    bang('va doc duoc ghim cu', (m.g.VGB_GHIM || []).join(','), 'CNPT');
    /* Ghim moi khong duoc de len mot danh sach rong. */
    go(m, 'tinh tien');
    bam(m, m.than.querySelector('[data-ghim]'));
    await new Promise(function (r) { setTimeout(r, 40); });
    bang('giu ca ghim cu lan ghim moi', m.g.VGB_GHIM.join(','), 'CNPT,POS');
  });

  await ca('#429-R3F1b: dang hoi do thi hai luot gom KHONG hoi trung', async function () {
    /* Bo loi hua khi hong nhung van phai chong goi trung trong LUC dang hoi. */
    var soLanDoc = 0;
    var m = dungTrangChu(['POS'], { lay: true });
    var apiThat = m.g.api;
    m.g.api = function (duong, ts) {
      if (duong === 'vagabond.ghim.lay') soLanDoc++;
      return apiThat(duong, ts);
    };
    m.g.vgbGomNhom();
    m.g.vgbGomNhom();
    m.g.vgbGomNhom();
    m.hoan.traLay();
    await new Promise(function (r) { setTimeout(r, 40); });
    bang('ba luot gom chi hoi mot lan', soLanDoc, 1);
  });

  await ca('#426-R2F1b: doc ghim HONG thi khong ghi de bang danh sach rong', async function () {
    var m = dungTrangChu([]);
    m.g.api = function (duong, ts) {
      m.goi.push({ duong: duong, ts: ts });
      return Promise.reject(new Error('mang hong'));
    };
    m.g.vgbGomNhom();
    await tick();
    go(m, 'tinh tien');
    bam(m, m.than.querySelector('[data-ghim]'));
    await new Promise(function (r) { setTimeout(r, 40); });
    bang('khong cat gi len may chu',
      m.goi.filter(function (x) { return x.duong === 'vagabond.ghim.luu'; }).length, 0);
    dung('co noi cho nguoi dung biet', m.bao.join(' ').length > 0);
  });

  await ca('#426-R2F1c: hai luot gom chong nhau chi hoi may chu MOT lan', async function () {
    var m = dungTrangChu(['POS'], { lay: true });
    m.g.vgbGomNhom();
    m.g.vgbGomNhom();
    m.hoan.traLay();
    await new Promise(function (r) { setTimeout(r, 40); });
    bang('chi mot lan doc', m.goi.filter(function (x) {
      return x.duong === 'vagabond.ghim.lay';
    }).length, 1);
  });

  await ca('#426-R2F2: ghim mat quyen that thi duoc go, khong chiem cho vo hinh', async function () {
    /* Codex: ghim 5 o Danh muc roi danh ba tra ve rong thi 5 o do bien mat
       khoi man nhung van chiem du 5 cho; bam ghim o moi chi nhan duoc cau
       "Chi ghim duoc 5 nghiep vu" trong khi khong con o cu nao de bo. */
    var m = dungTrangChu(['DM:DMSP', 'DM:DMNSP', 'DM:DMDVT', 'DM:DMQD', 'DM:DMKHO'],
      { danhBa: true });
    m.g.vgbGomNhom();
    await tick();
    bang('luot dau giu du nam ghim', m.g.VGB_GHIM.length, 5);
    var p = m.g.vgbNapKhungCo();
    await tick();
    m.hoan.traDanhBa([]);                 /* danh ba quyen: khong con man nao */
    await p;
    await new Promise(function (r) { setTimeout(r, 40); });
    bang('o mat quyen da duoc go', m.g.VGB_GHIM.length, 0);
    bang('va cat lai len may chu', m.catXong[m.catXong.length - 1], '[]');
    go(m, 'tinh tien');
    bam(m, m.than.querySelector('[data-ghim]'));
    await new Promise(function (r) { setTimeout(r, 40); });
    bang('ghim duoc o moi', m.g.VGB_GHIM.join(','), 'POS');
    bang('khong con bao het cho', m.bao.length, 0);
  });

  await ca('#426-R2F2b: danh ba CHUA biet thi KHONG duoc go ghim nao', async function () {
    /* Mat mang la chuyen thuong. Go ghim luc do la xoa du lieu cua nguoi ta
       chi vi mang cham, khong phai vi ho mat quyen.

       Phai chon mot khoa KHONG co san trong trang chu thu (KM - Khuyen mai),
       khong thi loc hay khong loc deu cho cung ket qua va ca kiem khong noi
       duoc gi. Viet lan dau da chon nham va dot bien "loc ca khi chua biet
       danh ba" khong bat duoc. */
    var m = dungTrangChu(['KM', 'POS'], { danhBa: true });
    bang('o KM co y khong co tren trang chu thu',
      DONG.indexOf('data-go="KM"') >= 0, false);
    m.g.vgbGomNhom();
    await new Promise(function (r) { setTimeout(r, 40); });
    bang('giu nguyen ca hai', m.g.VGB_GHIM.join(','), 'KM,POS');
    bang('khong cat lai gi', m.catXong.length, 0);
    /* Danh ba ve roi thi o do la mat quyen THAT, luc nay moi duoc go. */
    var p = m.g.vgbNapKhungCo();
    await tick();
    m.hoan.traDanhBa([]);
    await p;
    await new Promise(function (r) { setTimeout(r, 40); });
    bang('danh ba ve roi thi go', m.g.VGB_GHIM.join(','), 'POS');
    bang('va cat lai len may chu', m.catXong[m.catXong.length - 1], '["POS"]');
  });

  await ca('#426-R2F3: danh ba ve muon KHONG duoc xoa chu dang go', async function () {
    /* Codex: callback danh ba goi vgbGomNhom va ghi de ca body, keo theo o
       nhap. Do duoc: dang go "cong no" ra 3 ket qua, danh ba ve xong thi o
       trong va 0 ket qua. */
    var m = dungTrangChu([], { danhBa: true });
    m.g.vgbGomNhom();
    await tick();
    go(m, 'cong no');
    var oTruoc = m.tai.getElementById('vgbTim');
    var kqTruoc = m.than.querySelectorAll('.vgbkqd').length;
    dung('dang co ket qua', kqTruoc > 0);
    var p = m.g.vgbNapKhungCo();
    await tick();
    m.hoan.traDanhBa([]);
    await p;
    await new Promise(function (r) { setTimeout(r, 40); });
    var oSau = m.tai.getElementById('vgbTim');
    bang('chu dang go con nguyen', oSau.value, 'cong no');
    dung('van la DUNG o nhap cu, khong thay moi', oTruoc === oSau);
    dung('ket qua van hien', m.than.querySelectorAll('.vgbkqd').length > 0);
    bang('luoi o lon van dang an vi dang tim',
      m.than.querySelector('.gwrap').style.display, 'none');
  });

  await ca('#426-R2F4: Viec can lam va So tay tim duoc, mo duoc, ghim duoc', async function () {
    /* Codex: hai o nay ve rieng bang data-nhom nen khong co trong VGB_HUB;
       go "so tay" ra 0 ket qua du day la mot trong hai loi vao bam nhieu
       nhat tren trang chu. */
    var m = dungTrangChu([]);
    m.g.vgbGomNhom();
    await tick();
    go(m, 'so tay');
    bang('go khong dau ra dung mot ket qua', m.than.querySelectorAll('.vgbkqd').length, 1);
    bang('dung o So tay',
      m.than.querySelector('.vgbkqd').querySelector('.h1').textContent, 'S\u1ed5 tay');
    bam(m, m.than.querySelector('.vgbkqd'));
    bang('bam vao mo dung man', m.daGo.join(','), 'SOTAY');
    go(m, 'viec can lam');
    bang('o kia cung tim duoc', m.than.querySelectorAll('.vgbkqd').length, 1);
    bam(m, m.than.querySelector('[data-ghim]'));
    await new Promise(function (r) { setTimeout(r, 40); });
    bang('ghim duoc', m.g.VGB_GHIM.join(','), 'VCL');
    bang('o ghim ve ra duoc', m.than.querySelectorAll('.vgbgo').length, 1);
  });

  await ca('#426-R2F4b: hai o rieng KHONG mọc trung trong Cai dat hay nhom Khac', async function () {
    var m = dungTrangChu([]);
    m.g.vgbGomNhom();
    var truoc = m.than.querySelectorAll('.gt').length;
    var kh = m.g.vgbNhomTheoKhoa('KHAC');
    dung('khong keo VCL vao Cai dat', kh.keys.indexOf('VCL') < 0);
    dung('khong keo SOTAY vao Cai dat', kh.keys.indexOf('SOTAY') < 0);
    m.g.vgbGomNhom();
    bang('gom lai khong moc them o lon', m.than.querySelectorAll('.gt').length, truoc);
    var nhom = m.g.vgbChiaNhom(kh, function (k) { return !!m.g.VGB_HUB[k]; });
    var moi = [];
    nhom.forEach(function (x) { moi = moi.concat(x.keys); });
    dung('man Cai dat khong ve o So tay', moi.indexOf('SOTAY') < 0);
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

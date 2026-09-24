/* Bo ca kiem HANH VI v526 (chi Dung va anh Viet 24/09/2026).
 *
 * 1. Man Hach toan truoc khi ghi so thang (18-doi-chieu-may-in.js): bam nut
 *    Ghi so thang thi KHONG ghi ngay, ma mo man chon tai khoan tung dong; may
 *    dien san goi y; dong hang kho khong doi; dong 632 bi nhac va phai xac
 *    nhan; gui len may chu dung bo tai khoan da chon.
 * 2. Chip "Hoa don den sau" o man Chi tu TK cong ty (19-ho-so-tt.js): chon
 *    chip la moi khoan dang co va khoan them moi deu danh dau cho hoa don.
 *
 * Nap THAT scrDcmHachToan, dcmLa632, huChonCp, huThemDongTrong. Chi thay api,
 * frame, document, hop chon tai khoan va hop xac nhan.
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/hach_toan_526.js
 */
'use strict';
var fs = require('fs');
var path = require('path');
var vm = require('vm');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
var SRC18 = fs.readFileSync(path.join(BEP, '18-doi-chieu-may-in.js'), 'utf8');
var SRC19 = fs.readFileSync(path.join(BEP, '19-ho-so-tt.js'), 'utf8');

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

var ket = { dat: 0, hong: 0, loi: [] };
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
function dung(mo, x) { if (!x) throw new Error(mo); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; }
  catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n         ') : String(e))); }
}
function nghi() { return new Promise(function (r) { setTimeout(r, 0); }); }

var T632 = '632 - Giá vốn hàng bán - TV', T6417 = '6417 - Chi phí dịch vụ mua ngoài - TV';

/* Man hach toan: dong 1 xang (khong ma, goi y 632 vi NCC chua co lan truoc),
   dong 2 phi ship (goi y 6417 theo lan truoc), dong 3 hang kho da noi phieu. */
function kqXem() {
  return { name: 'HDM-26-09-00334', ncc: 'Xăng dầu KV II', tong: 80000, ghi_so_duoc: 1, dong: [
    { ten: 'R1', idx: 1, ten_hang: 'Xăng E10', tien: 50000, tk: T632, sua_duoc: 1, goi_y: T632, nguon: 'mac_dinh', nhan_nguon: 'mặc định của hệ thống' },
    { ten: 'R2', idx: 2, ten_hang: 'Phí ship', tien: 20000, tk: T632, sua_duoc: 1, goi_y: T6417, nguon: 'lan_truoc', nhan_nguon: 'lần trước của nhà cung cấp này' },
    { ten: 'R3', idx: 3, ten_hang: 'Bột mì', tien: 10000, tk: '2331 - Hàng chờ - TV', sua_duoc: 0 }
  ] };
}

function dung_man(opt) {
  opt = opt || {};
  var goi = [], ve = { html: '', footer: '' }, nut = {}, xacNhan = [], dieuHuong = [];
  var g = {
    JSON: JSON, Number: Number, String: String, Math: Math, Array: Array, Object: Object,
    h: function (s) { return String(s == null ? '' : s); },
    money: function (n) { return String(n); },
    busy: function () {}, toast: function () {}, baoLoi: [],
    dcmPhieu: [], dcmSs: null,
    api: async function (m, a) { goi.push({ m: m, a: a }); return m === 'vagabond.hach_toan_thang.xem' ? kqXem() : { loi_nhan: 'ok' }; },
    frame: function (tieu, html, o) { ve.html = html; ve.footer = (o && o.footer) || ''; nut = {}; return {}; },
    go: function (fn) { dieuHuong.push(fn); },
    scrDoiChieuMua: function () {},
    confirmSheet: async function (t, m) { xacNhan.push(t); return !!opt.dongY; },
    huChonTaiKhoan: async function (t, dang) { return opt.chonTk === undefined ? null : opt.chonTk; },
    document: {
      getElementById: function (id) {
        if ((ve.html + ve.footer).indexOf('id="' + id + '"') < 0) return null;
        return nut[id] || (nut[id] = { id: id });
      },
      querySelectorAll: function (sel) {
        var m = /\[(data-[a-z]+)\]/.exec(sel), ra = [];
        if (!m) return ra;
        var re = new RegExp(m[1] + '="([^"]*)"', 'g'), x;
        while ((x = re.exec(ve.html))) {
          var v = x[1];
          var key = m[1] + '|' + v;
          nut[key] = nut[key] || { getAttribute: (function (vv) { return function () { return vv; }; })(v) };
          ra.push(nut[key]);
        }
        return ra;
      }
    }
  };
  g.baoTin = function (s) { g.baoLoi.push(s); };
  vm.createContext(g);
  vm.runInContext('var dcmHt = null;\n' + layHam(SRC18, 'dcmLa632') + '\n' + layHam(SRC18, 'scrDcmHachToan'), g);
  return { g: g, goi: goi, ve: ve, nut: function (k) { return nut[k]; }, xacNhan: xacNhan, dieuHuong: dieuHuong };
}

(async function () {
  await ca('mo man: dien san goi y tung dong, dong hang kho khong co o chon', async function () {
    var m = dung_man();
    await m.g.scrDcmHachToan('HDM-26-09-00334');
    bang('lua chon dien san', JSON.parse(JSON.stringify(m.g.dcmHt.chon)), { R1: T632, R2: T6417 });
    dung('dong hang kho khong co o chon', m.ve.html.indexOf('data-dcmtk="R3"') < 0);
    dung('dong 632 bi nhac do', m.ve.html.indexOf('632 là giá vốn hàng bán') >= 0);
    dung('noi goi y theo lan truoc', m.ve.html.indexOf('lần trước của nhà cung cấp này') >= 0);
  });

  await ca('ca xang: doi dong 1 sang 6417 roi ghi so, may chu nhan dung bo tai khoan', async function () {
    var m = dung_man({ chonTk: T6417 });
    await m.g.scrDcmHachToan('HDM-26-09-00334');
    await m.nut('data-dcmtk|R1').onclick();
    bang('da doi dong 1', m.g.dcmHt.chon.R1, T6417);
    await m.g.scrDcmHachToan('HDM-26-09-00334');
    dung('het nhac 632', m.ve.html.indexOf('632 là giá vốn hàng bán') < 0);
    await m.nut('dcmHtGhi').onclick();
    var ghi = m.goi.filter(function (x) { return x.m === 'vagabond.doi_chieu_mua.ghi_so_thang'; });
    bang('goi ghi so mot lan', ghi.length, 1);
    bang('gui dung bo tai khoan', JSON.parse(ghi[0].a.tk), { R1: T6417, R2: T6417 });
    bang('khong hoi xac nhan 632', m.xacNhan.length, 0);
  });

  await ca('con dong 632 thi hoi xac nhan; bam Thoi la khong ghi so', async function () {
    var m = dung_man({ dongY: false });
    await m.g.scrDcmHachToan('HDM-26-09-00334');
    await m.nut('dcmHtGhi').onclick();
    bang('co hoi xac nhan', m.xacNhan.length, 1);
    bang('khong ghi so', m.goi.filter(function (x) { return x.m === 'vagabond.doi_chieu_mua.ghi_so_thang'; }).length, 0);
  });

  await ca('bam Thoi o hop chon tai khoan thi giu nguyen lua chon cu', async function () {
    var m = dung_man({ chonTk: undefined });
    await m.g.scrDcmHachToan('HDM-26-09-00334');
    await m.nut('data-dcmtk|R2').onclick();
    bang('giu 6417', m.g.dcmHt.chon.R2, T6417);
  });

  await ca('mo lai man cua to khac thi khong mang lua chon cua to cu sang', async function () {
    var m = dung_man();
    m.g.dcmHt = { name: 'HDM-KHAC', chon: { R1: 'X' } };
    await m.g.scrDcmHachToan('HDM-26-09-00334');
    bang('lua chon cua to nay', m.g.dcmHt.chon.R1, T632);
  });

  /* ---------- Chip "Hoa don den sau" ---------- */
  function man19() {
    var dieu = [];
    var g = { huDong: [], huCpThue: '', huVeSau: 0, huMode: 'tkct', huSuaO: -1,
      go: function (fn) { dieu.push(fn); }, scrChiCongTyTao: function () {},
      today: function () { return '2026-09-24'; }, setTimeout: function () {},
      document: { querySelector: function () { return null; } } };
    g.huManHienTai = function () { return g.scrChiCongTyTao; };
    vm.createContext(g);
    vm.runInContext(['huLaTkct', 'huChonCp', 'huThemDongTrong'].map(function (t) { return layHam(SRC19, t); }).join('\n'), g);
    return g;
  }

  await ca('chon chip Hoa don den sau: ghi thang chi phi, moi khoan dang co deu cho hoa don', async function () {
    var g = man19();
    g.huDong = [{ noi_dung: 'Xăng', cho_hoa_don: 0 }];
    g.huChonCp('vesau');
    bang('loai chi phi thue luc lap', g.huCpThue, 'Chi phi khong hop le');
    bang('dang lap hoa don den sau', g.huVeSau, 1);
    bang('khoan cu cho hoa don', g.huDong[0].cho_hoa_don, 1);
    g.huThemDongTrong();
    bang('khoan them moi cung cho hoa don', g.huDong[1].cho_hoa_don, 1);
  });

  await ca('doi sang chip khac thi thoi che do hoa don den sau, khoan moi khong tu danh dau', async function () {
    var g = man19();
    g.huChonCp('vesau');
    g.huChonCp('Chi phi khong hop le');
    bang('thoi che do', g.huVeSau, 0);
    g.huThemDongTrong();
    bang('khoan moi khong danh dau', g.huDong[0].cho_hoa_don, 0);
  });

  console.log('Bo ca kiem HANH VI hach toan ghi so thang va hoa don den sau (v526)');
  ket.loi.forEach(function (d) { console.log('  HONG  ' + d); });
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
})();

/* Ca kiem HANH VI v515: them tai khoan nhan tien NCC ngay tren man Thanh
 * toan truoc (Uyen bi ket 21/09/2026: man chi bao "chua co so tai khoan").
 *
 * Chay THAT scrTraTruocTao (30-tra-truoc.js), nccTkHop (20-danh-muc-quyen.js)
 * va hopKhung (07-hop-thoai.js) tren DOM gia, api gia. Chuoi thao tac dung
 * nhu nguoi dung: chon don -> bam Them tai khoan -> go so -> chon ngan hang
 * -> Luu. Khong goi them ham nao ngoai chuoi do.
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/stk_tai_cho_515.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
var TT = doc('30-tra-truoc.js'), DM = doc('20-danh-muc-quyen.js'), HT = doc('07-hop-thoai.js'), KM = doc('13-khuyen-mai.js'), POS = doc('09-tinh-tien-quay.js'), NEN = doc('00-nen.js');

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
function layDong(src, dau) {
  var i = src.indexOf(dau);
  if (i < 0) throw new Error('Khong thay dong ' + dau);
  return src.slice(i, src.indexOf('\n', i));
}

function dungMan(canh) {
  canh = canh || {};
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);
  var goi = [];
  var tk = canh.tk || {};
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, Date: Date, String: String, Number: Number,
    Array: Array, Object: Object, RegExp: RegExp, Promise: Promise, setTimeout: setTimeout, clearTimeout: clearTimeout,
    window: { open: function () {} },
    frame: function (t, html, o) { khung.innerHTML = html + ((o && o.footer) || ''); return khung; },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: JSON.parse(JSON.stringify(ts || {})) });
      if (duong === 'vagabond.tra_truoc.ds_don_mua') return Promise.resolve({ don: [{ don: 'DMH-1', ten_ncc: 'Duy Lợi', tong: 1620000, ngay: '2026-09-16', lap_duoc: 1 }] });
      if (duong === 'vagabond.tra_truoc.ds_nguon_tien') return Promise.resolve({ nguon: [{ ma: '11211', so_hieu: '11211', nhan: '11211 · MB Bank', nhom: 'cong_ty' }] });
      if (duong === 'vagabond.tra_truoc.chi_tiet_don') {
        return Promise.resolve({ don: ts.don, tong: 1620000, tran: 1620000, lap_duoc: 1,
          ncc: { ma: 'NCC-DL', ten: 'Duy Lợi', mst: '0315917706', tai_khoan: tk.so_tk ? JSON.parse(JSON.stringify(tk)) : {}, sua_tk: canh.sua === 0 ? 0 : 1 },
          loai_chung_tu: [] });
      }
      if (duong === 'vagabond.ncc.luu_tai_khoan') {
        if (canh.luuHong) return Promise.reject(new Error('Số tài khoản có ký tự lạ.'));
        tk = { so_tk: ts.so_tk, ngan_hang: ts.ngan_hang, chu_tk: ts.chu_tk || 'Duy Lợi' };
        return Promise.resolve({ ok: 1 });
      }
      return Promise.resolve({});
    },
    h: function (s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); },
    money: function (n) { return String(n); }, hsNgayVn: function (d) { return d; },
    busy: function () {}, toast: function (m) { (that._toast = that._toast || []).push(String(m)); },
    baoTin: function (m) { (that._bao = that._bao || []).push(String(m)); },
    go: function (f) { return f(); },
    nhChon: function (dang, xong) { xong('Ngân hàng TMCP Quân đội'); },
    vgbOTim: function () { return ''; },
  };
  that.globalThis = that;
  var ma = [
    layDong(TT, 'var ttDon = '), layDong(TT, 'var ttLoaiCt = '), layDong(TT, 'var ttDsDon = '),
    layHam(TT, 'ttReset'), layHam(TT, 'scrTraTruocTao'),
    layHam(DM, 'nccTkHop'), layHam(HT, 'hopKhung'), layHam(KM, 'kmHangChip'), layHam(POS, 'posChipNut'), layHam(NEN, 'oTep'),
  ].join('\n');
  vm.runInNewContext(ma, that, { filename: 'stk-tai-cho-515' });
  return { g: that, tai: tai, khung: khung, goi: goi };
}

var ket = { dat: 0, hong: 0, loi: [] };
function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) { if (a !== b) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
function tick() { return new Promise(function (r) { setTimeout(r, 5); }); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; }
  catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n         ') : String(e))); }
}
function bam(el) { el.dispatchEvent(dg.suKien('click', {}, el)); }
function hop(m) { return m.tai.body.querySelectorAll('.shb')[0] || null; }
async function moDon(m) {
  await m.g.scrTraTruocTao(); await tick();
  bam(m.khung.querySelectorAll('[data-ttd]')[0]); await tick(); await tick();
}

async function chayHet() {
  await ca('chua co tai khoan, nguoi co quyen: thay nut Them ngay duoi canh bao', async function () {
    var m = dungMan();
    await moDon(m);
    var html = m.khung.innerHTML;
    dung('van bao chua co so', html.indexOf('chưa có số tài khoản nhận tiền') >= 0);
    dung('co nut Them', html.indexOf('➕ Thêm tài khoản nhận tiền') >= 0);
    dung('co id ttSuaTk', m.khung.querySelectorAll('#ttSuaTk').length === 1);
  });
  await ca('khong co quyen: khong bay nut, chi dan nguoi co quyen', async function () {
    var m = dungMan({ sua: 0 });
    await moDon(m);
    bang('khong nut', m.khung.querySelectorAll('#ttSuaTk').length, 0);
    dung('co loi dan', m.khung.innerHTML.indexOf('Báo thu mua hoặc kế toán') >= 0);
  });
  await ca('chuoi day du: bam Them, go so, chon ngan hang, Luu -> ghi dung, doc lai don, man hien so moi', async function () {
    var m = dungMan();
    await moDon(m);
    bam(m.khung.querySelectorAll('#ttSuaTk')[0]); await tick();
    var b = hop(m);
    dung('mo hop', !!b);
    b.querySelectorAll('#tkhSo')[0].value = '0315 917 706';
    bam(b.querySelectorAll('#tkhNh')[0]); await tick();
    var soGoiTruoc = m.goi.length;
    bam(b.querySelectorAll('[data-tkhok]')[0]); await tick(); await tick(); await tick();
    var luu = m.goi.filter(function (x) { return x.duong === 'vagabond.ncc.luu_tai_khoan'; });
    bang('goi luu mot lan', luu.length, 1);
    bang('dung NCC cua don', luu[0].ts.ncc, 'NCC-DL');
    bang('so tai khoan gui len', luu[0].ts.so_tk, '0315 917 706');
    bang('ngan hang da chon', luu[0].ts.ngan_hang, 'Ngân hàng TMCP Quân đội');
    var sau = m.goi.slice(soGoiTruoc).map(function (x) { return x.duong; });
    dung('doc lai chi tiet don sau khi luu', sau.indexOf('vagabond.tra_truoc.chi_tiet_don') > sau.indexOf('vagabond.ncc.luu_tai_khoan'));
    dung('hop da dong', !hop(m));
    var html = m.khung.innerHTML;
    dung('man hien so moi', html.indexOf('Số tài khoản: 0315 917 706') >= 0);
    dung('nut doi thanh Sua', html.indexOf('✏️ Sửa tài khoản nhận tiền') >= 0);
    dung('van dung don dang lap', html.indexOf('☑️ Duy Lợi') >= 0);
  });
  await ca('chua chon ngan hang: bao ngay trong hop, khong goi may chu', async function () {
    var m = dungMan();
    await moDon(m);
    bam(m.khung.querySelectorAll('#ttSuaTk')[0]); await tick();
    var b = hop(m);
    b.querySelectorAll('#tkhSo')[0].value = '123456789';
    bam(b.querySelectorAll('[data-tkhok]')[0]); await tick();
    bang('khong goi luu', m.goi.filter(function (x) { return x.duong === 'vagabond.ncc.luu_tai_khoan'; }).length, 0);
    dung('bao loi ngan hang', b.querySelectorAll('#tkhLoi')[0].textContent.indexOf('ngân hàng') >= 0);
    dung('hop con mo', !!hop(m));
  });
  await ca('may chu tu choi: loi hien trong hop, hop con mo, man khong ve lai', async function () {
    var m = dungMan({ luuHong: 1 });
    await moDon(m);
    bam(m.khung.querySelectorAll('#ttSuaTk')[0]); await tick();
    var b = hop(m);
    b.querySelectorAll('#tkhSo')[0].value = '12@3';
    bam(b.querySelectorAll('#tkhNh')[0]); await tick();
    var n = m.goi.length;
    bam(b.querySelectorAll('[data-tkhok]')[0]); await tick(); await tick();
    dung('loi may chu hien ra', b.querySelectorAll('#tkhLoi')[0].textContent.indexOf('ký tự lạ') >= 0);
    dung('hop con mo', !!hop(m));
    bang('khong doc lai don', m.goi.slice(n).filter(function (x) { return x.duong === 'vagabond.tra_truoc.chi_tiet_don'; }).length, 0);
  });
  await ca('bam Thoi: dong hop, khong ghi gi', async function () {
    var m = dungMan();
    await moDon(m);
    bam(m.khung.querySelectorAll('#ttSuaTk')[0]); await tick();
    var n = m.goi.length;
    bam(hop(m).querySelectorAll('[data-tkhx]')[0]); await tick(); await tick();
    dung('hop dong', !hop(m));
    bang('khong goi gi them (khong doc lai don)', m.goi.length, n);
    bang('khong goi luu', m.goi.filter(function (x) { return x.duong === 'vagabond.ncc.luu_tai_khoan'; }).length, 0);
  });
  await ca('da co tai khoan: hien so va nut Sua, hop dien san so cu', async function () {
    var m = dungMan({ tk: { so_tk: '999888777', ngan_hang: 'MB', chu_tk: 'DUY LOI' } });
    await moDon(m);
    dung('hien so', m.khung.innerHTML.indexOf('Số tài khoản: 999888777') >= 0);
    bam(m.khung.querySelectorAll('#ttSuaTk')[0]); await tick();
    bang('dien san so cu', hop(m).querySelectorAll('#tkhSo')[0].value, '999888777');
  });

  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong');
  ket.loi.forEach(function (l) { console.log('  HONG ' + l); });
  if (ket.hong) process.exit(1);
}
chayHet();

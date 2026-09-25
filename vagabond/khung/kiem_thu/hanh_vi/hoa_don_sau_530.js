/* Bo ca kiem HANH VI v530: hop chon hoa don den sau o muc ho so, va loi dau
 * cham trong o chon co o tim.
 *
 * Nap THAT hsNoiHdSau, hsChonHdSau, hsKhoiHdSau (19-ho-so-tt.js), hopKhung,
 * hoiCo, baoTin, hoiChon, vgbOTim, vgbNoiOTim (07-hop-thoai.js), mvKhongDau,
 * h, money vao DOM gia; chi thay api, busy, toast, go. Moi ca bam dung chuoi
 * thao tac cua chi Dung, khong goi them ham nao "cho chac".
 *
 * So lieu lay tu hai ho so that 25/09/2026: APP.26.09.102 Mobifone (sau to
 * cong dung 778.784 d) va APP.26.09.009 Adecco (to so 5802, 686.810.159 d).
 *
 * Chay: node vagabond/khung/kiem_thu/hanh_vi/hoa_don_sau_530.js
 */
'use strict';
var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
var HS = doc('19-ho-so-tt.js'), HOP = doc('07-hop-thoai.js'), NEN = doc('00-nen.js'), KH = doc('11-khach-ca-hop-dong.js');

function layHam(src, ten) {
  var dau = src.indexOf('\nfunction ' + ten + '(');
  if (dau < 0) dau = src.indexOf('\nasync function ' + ten + '(');
  if (dau < 0) throw new Error('Khong thay ham ' + ten);
  dau += 1;
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
function nghi() { return new Promise(function (r) { setImmediate(r); }); }
async function cho(n) { for (var i = 0; i < (n || 6); i++) await nghi(); }

var MOBI = [
  ['HDM-26-09-00093', '5310710', 159000], ['HDM-26-09-00287', '5332207', 105570], ['HDM-26-09-00288', '5422323', 107000],
  ['HDM-26-09-00289', '5619189', 105290], ['HDM-26-09-00317', '5284552', 106390], ['HDM-26-09-00318', '5519595', 195534],
  ['ACC-PINV-2026-02461', '3952', 347133], ['HDM-26-08-00062', '769', 349533],
].map(function (x, i) {
  return { name: x[0], so_hd: x[1], ngay: '2026-09-05', ncc: 'MOBI-096', ncc_ten: 'MOBIFONE TP HCM 1', cung_nhom: 1,
    tong: x[2], tien: x[2], da_ghi_so: i < 6 ? 1 : 0, nhan: i < 6 ? 'Đã ghi sổ, còn nợ ' + x[2] + ' đ' : 'Nháp, chưa ghi sổ' };
});

function uvMobi() {
  return { ds: MOBI, tkct: 1, ncc: 'MOBI-002', mst_goc: '0100686209', so_ncc_nhom: 2, tim_moi_ncc: 0,
    phu: { can: 778784, da_noi: 0, con_thieu: 778784, thua: 0, du: false },
    goi_y: { hoa_don: MOBI.slice(0, 6).map(function (x) { return x.name; }), tong: 778784, ly_do: '6 hoá đơn cộng lại 778.784 đ', con_cach_khac: false } };
}

function dungMan(canh) {
  canh = canh || {};
  var tai = dg.taiLieuGia();
  var goi = [];
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, Date: Date, String: String, Number: Number,
    Array: Array, Object: Object, RegExp: RegExp, Promise: Promise, setTimeout: setTimeout, clearTimeout: clearTimeout,
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: JSON.parse(JSON.stringify(ts || {})) });
      if (duong === 'vagabond.ho_so_bo_sung.ung_vien_hoa_don') {
        if (ts.moi_ncc) return Promise.resolve(canh.moi || { ds: [], phu: {}, goi_y: null });
        return Promise.resolve(canh.uv || uvMobi());
      }
      if (duong === 'vagabond.ho_so_bo_sung.noi_nhieu') return Promise.resolve(canh.noi || { ok: 1, hop_le: 1, but_toan: ['PKT-2026-00099'], phu: { du: true } });
      return Promise.resolve({ ok: 1 });
    },
    busy: function () {}, toast: function (m) { (that._toast = that._toast || []).push(String(m)); },
    go: function (fn) { that._go = (that._go || 0) + 1; return null; },
    scrHoSoTTView: function () {},
  };
  that.globalThis = that;
  var ma = [layHam(NEN, 'h'), layHam(NEN, 'money'), layHam(KH, 'mvKhongDau'),
    layHam(HOP, 'hopKhung'), layHam(HOP, 'hoiCo'), layHam(HOP, 'baoTin'), layHam(HOP, 'hoiChon'),
    'var VGB_NGUONG_TIM = 7;', layHam(HOP, 'vgbCanOTim'), layHam(HOP, 'vgbOTim'), layHam(HOP, 'vgbNoiOTim'),
    layHam(HS, 'hsKhoiHdSau'), layHam(HS, 'hsNoiHdSau'), layHam(HS, 'hsChonHdSau')].join('\n');
  vm.runInNewContext(ma, that, { filename: 'v530.js' });
  return { g: that, tai: tai, goi: goi };
}

function hopDangMo(m) { var ds = m.tai.body.querySelectorAll('.shb'); return ds[ds.length - 1] || null; }
function bam(el) { dung('co phan tu de bam', !!el); el.click(); }
function goiNoi(m) { return m.goi.filter(function (x) { return x.duong === 'vagabond.ho_so_bo_sung.noi_nhieu'; }); }
function the(m, ma) { return hopDangMo(m).querySelector('[data-hdsmuc="' + ma + '"]'); }
function tong(m) { return hopDangMo(m).querySelector('[data-hdstong]').textContent; }

(async function () {
  var HSO = { ma: 'APP.26.09.102', loai: 'TK cong ty', trang_thai: 'Da thanh toan' };

  await ca('Mobifone: may goi y 6 to, bam Chon theo goi y roi Noi thi gui DUNG 6 to, khong to nhieu', async function () {
    var m = dungMan();
    var p = m.g.hsNoiHdSau(HSO); await cho();
    var hop = hopDangMo(m);
    dung('hop mo, co the may goi y', hop && hop.querySelector('[data-hdsgy]'));
    dung('goi y ghi ly do', hop.querySelector('[data-hdsgy]').textContent.indexOf('6 hoá đơn') >= 0);
    bam(hop.querySelector('[data-hdsgyb]')); await cho();
    bang('6 the dang tich', MOBI.filter(function (x) { var t = the(m, x.name); return t && t.getAttribute('aria-checked') === 'true'; }).length, 6);
    dung('tong bao khop so con thieu', tong(m).indexOf('khớp số còn thiếu') >= 0);
    dung('bao se lap but toan bu tru', tong(m).indexOf('bút toán bù trừ') >= 0);
    bam(hopDangMo(m).querySelector('[data-hdsok]')); await p; await cho();
    var n = goiNoi(m);
    bang('goi noi mot lan', n.length, 1);
    bang('dung 6 to, dung thu tu', JSON.parse(n[0].ts.hoa_don), MOBI.slice(0, 6).map(function (x) { return x.name; }));
    bang('khong ngoai NCC', n[0].ts.ngoai_ncc, 0);
    dung('bao da lap but toan', (m.g._toast || []).join(' ').indexOf('PKT-2026-00099') >= 0);
    bang('mo lai ho so', m.g._go, 1);
  });

  await ca('Tich tay: bam hai the roi bo mot the, Noi gui dung to con lai; so tien con thieu dung', async function () {
    var m = dungMan();
    var p = m.g.hsNoiHdSau(HSO); await cho();
    bam(the(m, 'HDM-26-09-00318')); await cho();
    bam(the(m, 'HDM-26-09-00093')); await cho();
    bam(the(m, 'HDM-26-09-00318')); await cho();
    dung('con thieu 778.784 - 159.000 = 619.784', tong(m).replace(/\./g, '').indexOf('619784') >= 0);
    bam(hopDangMo(m).querySelector('[data-hdsok]')); await p; await cho();
    bang('dung mot to', JSON.parse(goiNoi(m)[0].ts.hoa_don), ['HDM-26-09-00093']);
  });

  await ca('O tim: go so hoa don hoac so tien co dau cham thi chi con the khop', async function () {
    var m = dungMan();
    m.g.hsNoiHdSau(HSO); await cho();
    var o = hopDangMo(m).querySelector('#hdsTim');
    o.value = '5519595'; o.dispatchEvent(dg.suKien('input', {}, o)); await cho();
    bang('so hoa don', hopDangMo(m).querySelectorAll('[data-hdsmuc]').map(function (e) { return e.getAttribute('data-hdsmuc'); }), ['HDM-26-09-00318']);
    o.value = '105.570'; o.dispatchEvent(dg.suKien('input', {}, o)); await cho();
    bang('so tien go co dau cham', hopDangMo(m).querySelectorAll('[data-hdsmuc]').map(function (e) { return e.getAttribute('data-hdsmuc'); }), ['HDM-26-09-00287']);
  });

  await ca('Tim moi NCC: to khac MST hien ra, tich roi Noi thi hoi xac nhan; dong y moi gui ngoai_ncc 1', async function () {
    var ngoai = { name: 'HDM-X-1', so_hd: '777', ngay: '2026-09-05', ncc: 'KHAC', ncc_ten: 'NCC KHÁC', cung_nhom: 0, tong: 5000, tien: 5000, da_ghi_so: 0, nhan: 'Nháp, chưa ghi sổ' };
    var m = dungMan({ moi: { ds: [ngoai], phu: {}, goi_y: null } });
    var p = m.g.hsNoiHdSau(HSO); await cho();
    var o = hopDangMo(m).querySelector('#hdsTim');
    o.value = '777';
    bam(hopDangMo(m).querySelector('[data-hdsmoi]')); await cho();
    var tim = m.goi.filter(function (x) { return x.duong === 'vagabond.ho_so_bo_sung.ung_vien_hoa_don' && x.ts.moi_ncc; });
    bang('goi tim moi NCC dung tu khoa', tim.map(function (x) { return x.ts.tu_khoa; }), ['777']);
    dung('the ngoai NCC ghi ro khac nha cung cap', the(m, 'HDM-X-1').textContent.indexOf('khác nhà cung cấp') >= 0);
    bam(the(m, 'HDM-X-1')); await cho();
    bam(hopDangMo(m).querySelector('[data-hdsok]')); await cho();
    var hoi = hopDangMo(m);
    dung('hop xac nhan hien', hoi.textContent.indexOf('khác nhà cung cấp') >= 0 || hoi.textContent.indexOf('mã số thuế') >= 0);
    bang('chua gui gi truoc khi xac nhan', goiNoi(m).length, 0);
    bam(hoi.querySelector('[data-hkok]')); await p; await cho();
    bang('gui ngoai_ncc 1', [JSON.parse(goiNoi(m)[0].ts.hoa_don), goiNoi(m)[0].ts.ngoai_ncc], [['HDM-X-1'], 1]);
  });

  await ca('Tim moi NCC ma bam Thoi o hop xac nhan: khong gui gi, hop chon van mo', async function () {
    var ngoai = { name: 'HDM-X-1', so_hd: '777', ncc_ten: 'NCC KHÁC', cung_nhom: 0, tien: 5000, da_ghi_so: 0, nhan: 'Nháp' };
    var m = dungMan({ moi: { ds: [ngoai] } });
    m.g.hsNoiHdSau(HSO); await cho();
    hopDangMo(m).querySelector('#hdsTim').value = '777';
    bam(hopDangMo(m).querySelector('[data-hdsmoi]')); await cho();
    bam(the(m, 'HDM-X-1')); await cho();
    bam(hopDangMo(m).querySelector('[data-hdsok]')); await cho();
    bam(hopDangMo(m).querySelector('[data-hkx]')); await cho();
    bang('khong gui', goiNoi(m).length, 0);
    dung('hop chon con', hopDangMo(m) && hopDangMo(m).querySelector('[data-hdsds]'));
  });

  await ca('Thoi o hop chon: khong goi noi_nhieu, khong mo lai man', async function () {
    var m = dungMan();
    var p = m.g.hsNoiHdSau(HSO); await cho();
    bam(the(m, 'HDM-26-09-00093')); await cho();
    bam(hopDangMo(m).querySelector('[data-hdsx]')); await p; await cho();
    bang('khong gui', goiNoi(m).length, 0);
    bang('khong mo lai', m.g._go || 0, 0);
  });

  await ca('Chua tich to nao ma bam Noi: khong gui', async function () {
    var m = dungMan();
    m.g.hsNoiHdSau(HSO); await cho();
    bam(hopDangMo(m).querySelector('[data-hdsok]')); await cho();
    bang('khong gui', goiNoi(m).length, 0);
  });

  await ca('Anh 1 chi Dung: o chon co o tim (tu 7 muc) giu display:flex, khong con dau cham mo coi', async function () {
    var m = dungMan();
    var chon = [];
    for (var i = 0; i < 12; i++) chon.push({ k: 'K' + i, nhan: 'Số ' + (1000 + i), mo_ta: 'ACC-PINV-' + i + ' · 328.492' });
    m.g.hoiChon('Nối hóa đơn đến sau', 'x', chon);
    var hop = hopDangMo(m);
    var muc = hop.querySelectorAll('[data-hc]');
    bang('12 muc', muc.length, 12);
    bang('moi muc van la flex sau khi noi o tim', muc.map(function (e) { return e.style.display; }).filter(function (d) { return d !== 'flex'; }), []);
    var o = hop.querySelector('#hcTim');
    o.value = '1003'; o.dispatchEvent(dg.suKien('input', {}, o));
    bang('loc con mot', muc.filter(function (e) { return e.style.display !== 'none'; }).length, 1);
    o.value = ''; o.dispatchEvent(dg.suKien('input', {}, o));
    bang('xoa chu: tro lai flex het', muc.filter(function (e) { return e.style.display === 'flex'; }).length, 12);
    dung('khong con dau cham khi muc khong co bieu tuong', hop.innerHTML.indexOf('•') < 0);
  });

  await ca('Khoi tren ho so: con thieu thi co nut Noi; da noi du thi het nut, to co nut Go va but toan', async function () {
    var m = dungMan();
    var d = { dong: [{ so_tien: 686810159 }], hd_sau: [], phu_hd_sau: { can: 686810159, da_noi: 0, con_thieu: 686810159, thua: 0, du: false } };
    var html = m.g.hsKhoiHdSau(d, { trang_thai: 'Da thanh toan' }, { fin: 1 });
    dung('co nut noi', html.indexOf('data-hsv="noihds"') >= 0);
    dung('bao con thieu', html.indexOf('còn thiếu') >= 0);
    d.hd_sau = [{ hoa_don: 'HDM-26-09-00135', so_hd_ncc: '5802', ncc_ten: 'ADECCO', tien_khop: 686810159, bu_tru: 686810159, but_toan: 'PKT-2026-00100', nhan: 'Đã ghi sổ, đã trả hết', da_ghi_so: 1 }];
    d.phu_hd_sau = { can: 686810159, da_noi: 686810159, con_thieu: 0, thua: 0, du: true };
    html = m.g.hsKhoiHdSau(d, { trang_thai: 'Da thanh toan' }, { fin: 1 });
    dung('het nut noi', html.indexOf('noihds') < 0);
    dung('co nut go dung to', html.indexOf('data-hsv="gohds|HDM-26-09-00135"') >= 0);
    dung('ghi but toan bu tru', html.indexOf('PKT-2026-00100') >= 0);
    html = m.g.hsKhoiHdSau(d, { trang_thai: 'Da thanh toan' }, {});
    dung('sales: khong co nut go', html.indexOf('gohds') < 0);
  });

  console.log('Bo ca kiem HANH VI noi hoa don den sau muc ho so (v530)');
  ket.loi.forEach(function (l) { console.log('  HONG  ' + l); });
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
})();

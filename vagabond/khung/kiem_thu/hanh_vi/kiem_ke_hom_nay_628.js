/* Ca kiểm HÀNH VI v628: thẻ "Đếm hôm nay" trên màn Kiểm kê.
 *
 * Anh Việt 02/11/2026: bếp không chịu kiểm kê. Phiếu cả kho quá dài (Pastry
 * 205 món), nên mỗi sáng máy chia 10 món, tin Zalo 07:30 báo tên món, bếp mở
 * Kiểm kê bấm thẻ của bếp mình là có phiếu điền sẵn.
 *
 * Nạp THẬT 06-nhap-kho-kiem-ke.js vào DOM giả; máy chủ giả chỉ trả dữ liệu và
 * ghi lại lời gọi. Mỗi ca bấm đúng chuỗi thao tác của người dùng.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/kiem_ke_hom_nay_628.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var MAN = fs.readFileSync(path.join(GOC, 'vagabond', 'public', 'js', 'bep', '06-nhap-kho-kiem-ke.js'), 'utf8');

var BA_BEP = { ngay: '2026-11-02', kho: [
  { kho: 'Pastry - Nguyên liệu - TV', bep: 'Pastry', phieu: '', trang_thai: '', so_mon: 10, da_dem: 0, so_den_han: 188 },
  { kho: 'Baker - Nguyên liệu - TV', bep: 'Baker', phieu: 'PKK-7', trang_thai: 'Đang kiểm', so_mon: 10, da_dem: 4, so_den_han: 0 },
  { kho: 'Kho Lab - TV', bep: 'Lab', phieu: 'PKK-8', trang_thai: 'Đã ghi sổ', so_mon: 10, da_dem: 10, so_den_han: 0 },
] };

function dung(tl) {
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);
  var goi = [], toastDs = [], mo = [], cho = {};
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, Number: Number, Date: Date, setTimeout: setTimeout, isNaN: isNaN,
    S: { wh: [] },
    h: function (x) { return String(x == null ? '' : x).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;'); },
    dmy: String, shortWh: String, num: String,
    toast: function (m) { toastDs.push(m); },
    errMsg: function (e) { return String(e && e.message || e); },
    loadMasters: function () { return Promise.resolve(); },
    getList: function () { return Promise.resolve([]); },
    frame: function (t, html) { khung.innerHTML = html; khung.onclick = null; that._t = t; return khung; },
    go: function (fn) { return fn(); },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: ts });
      if (cho[duong]) return cho[duong];
      var f = tl[duong];
      if (!f) return Promise.resolve({});
      try { return Promise.resolve(f(ts)); } catch (e) { return Promise.reject(e); }
    },
  };
  that.window = that;
  vm.runInNewContext(MAN, that, { filename: '06-nhap-kho-kiem-ke.js' });
  /* Thay màn chi tiết phiếu bằng bản ghi lại: ca chỉ cần biết mở ĐÚNG phiếu nào. */
  that.scrKkDoc = function (ten) { mo.push(ten); };
  return { g: that, khung: khung, goi: goi, toast: toastDs, mo: mo, cho: cho };
}

var ket = { dat: 0, hong: 0 };
function chac(mo, dk) { if (!dk) throw new Error(mo); }
function bang(mo, a, b) {
  var x = JSON.stringify(a), y = JSON.stringify(b);
  if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y);
}
function tick() { return new Promise(function (r) { setTimeout(r, 5); }); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); }
}
function chu(el) { var s = el._chu || ''; (el.children || []).forEach(function (c) { s += chu(c); }); return s; }
function bam(m, el) { return m.khung.onclick({ target: el }); }
var TL = {
  'vagabond.kiem_ke.ds_dem_hom_nay': function () { return BA_BEP; },
  'vagabond.kiem_ke.mo_phieu_hom_nay': function (ts) { return { ok: 1, name: ts.kho === 'Baker - Nguyên liệu - TV' ? 'PKK-7' : 'PKK-MOI', so_mon: 10 }; },
};

(async function () {
  console.log('v628 Kiểm kê: thẻ Đếm hôm nay của từng bếp');

  await ca('ba bếp ba trạng thái: chưa đếm, đang đếm dở, đã xong; chỉ hai thẻ đầu bấm được', async function () {
    var m = dung(TL);
    await m.g.scrKkList(); await tick();
    var t = chu(m.khung);
    chac('có mục Đếm hôm nay', t.indexOf('Đếm hôm nay') >= 0);
    chac('Pastry nói số món và thời gian', t.indexOf('Máy chia sẵn 10 món, khoảng 10 phút') >= 0);
    chac('Baker nói đã đếm 4/10', t.indexOf('Đã đếm 4/10 món, bấm để đếm tiếp') >= 0);
    chac('Lab nói đã xong', t.indexOf('Đã ghi sổ') >= 0 && t.indexOf('Đã đếm 10/10 món') >= 0);
    bang('thẻ bấm được', m.khung.querySelectorAll('[data-dh]').map(function (x) { return x.dataset.dh; }),
      ['Pastry - Nguyên liệu - TV', 'Baker - Nguyên liệu - TV']);
    chac('không hiện tên kho mã nội bộ trên thẻ', t.indexOf('Bếp Pastry') >= 0 && t.indexOf('Bếp Lab') >= 0);
  });

  await ca('bấm thẻ Pastry: gọi mở phiếu đúng kho rồi vào đúng phiếu vừa tạo', async function () {
    var m = dung(TL);
    await m.g.scrKkList(); await tick();
    await bam(m, m.khung.querySelectorAll('[data-dh]')[0]); await tick();
    var g = m.goi.filter(function (x) { return x.duong === 'vagabond.kiem_ke.mo_phieu_hom_nay'; });
    bang('một lời gọi đúng kho', g.map(function (x) { return x.ts; }), [{ kho: 'Pastry - Nguyên liệu - TV' }]);
    bang('mở phiếu mới', m.mo, ['PKK-MOI']);
  });

  await ca('bấm thẻ Baker đang dở: mở lại đúng phiếu đang đếm', async function () {
    var m = dung(TL);
    await m.g.scrKkList(); await tick();
    await bam(m, m.khung.querySelectorAll('[data-dh]')[1]); await tick();
    bang('mở phiếu cũ', m.mo, ['PKK-7']);
  });

  await ca('bấm hai lần liền khi máy chủ chưa trả lời: chỉ một lời gọi', async function () {
    var m = dung(TL);
    await m.g.scrKkList(); await tick();
    var mo, hua = new Promise(function (r) { mo = r; });
    m.cho['vagabond.kiem_ke.mo_phieu_hom_nay'] = hua;
    var the = m.khung.querySelectorAll('[data-dh]')[0];
    var p1 = bam(m, the), p2 = bam(m, the);
    mo({ ok: 1, name: 'PKK-MOI' });
    await p1; await p2; await tick();
    bang('một lời gọi', m.goi.filter(function (x) { return x.duong === 'vagabond.kiem_ke.mo_phieu_hom_nay'; }).length, 1);
    bang('mở một lần', m.mo, ['PKK-MOI']);
  });

  await ca('máy chủ báo không có món đến hạn: hiện câu báo, không chuyển màn', async function () {
    var m = dung(Object.assign({}, TL, { 'vagabond.kiem_ke.mo_phieu_hom_nay': function () { return { ok: 0, ly_do: 'Hôm nay kho này không có mã nào đến hạn đếm.' }; } }));
    await m.g.scrKkList(); await tick();
    await bam(m, m.khung.querySelectorAll('[data-dh]')[0]); await tick();
    bang('không chuyển màn', m.mo, []);
    bang('câu báo', m.toast, ['Hôm nay kho này không có mã nào đến hạn đếm.']);
  });

  await ca('đọc thẻ hỏng: danh sách phiếu vẫn lên như cũ, không có mục Đếm hôm nay', async function () {
    var m = dung(Object.assign({}, TL, { 'vagabond.kiem_ke.ds_dem_hom_nay': function () { throw new Error('hỏng'); } }));
    await m.g.scrKkList(); await tick();
    var t = chu(m.khung);
    chac('không có mục', t.indexOf('Đếm hôm nay') < 0);
    chac('vẫn có lời hướng dẫn cũ', t.indexOf('Mỗi phiếu kiểm kê là') >= 0);
    bang('tiêu đề', m.g._t, 'Kiểm kê');
  });

  await ca('bấm phiếu cũ trong danh sách vẫn mở như trước', async function () {
    var m = dung(Object.assign({}, TL, {}));
    m.g.getList = function () { return Promise.resolve([{ name: 'PKK-1', ngay_kiem: '2026-11-01', kho: 'Kho D1 - TV', pham_vi: 'Tất cả', trang_thai: 'Đang kiểm', so_mon: 3 }]); };
    await m.g.scrKkList(); await tick();
    await bam(m, m.khung.querySelectorAll('[data-p]')[0]); await tick();
    bang('mở phiếu cũ', m.mo, ['PKK-1']);
  });

  console.log('\n' + (ket.hong ? 'HONG ' + ket.hong + ' / ' : 'PASS ') + ket.dat + ' ca');
  process.exit(ket.hong ? 1 : 0);
})();

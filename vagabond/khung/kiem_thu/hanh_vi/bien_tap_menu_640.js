/* Ca kiểm HÀNH VI v640: màn Biên tập menu (Bán hàng > Menu), anh Việt duyệt mẫu
 * 05/11/2026.
 *
 * Nạp THẬT toàn bộ 68-bien-tap-menu.js cùng các hàm nó dùng (h, money của 00,
 * coQuyenGmbQr của 66), chạy trong DOM giả với một máy chủ giả giữ bản nháp và
 * bản đang chạy. Bấm đúng chuỗi của quản lý: mở màn, kéo ≡ đổi thứ tự nhóm (bắn
 * pointerdown, pointermove, pointerup thật vào dòng), bật tắt nhóm, sửa tuỳ
 * chọn, tích bảng topping, mở nhóm, ẩn món, xếp món mới, sửa riêng một món,
 * xem và xuất bản, quay về bản trước. Đọc đúng nội dung bản nháp gửi lên máy
 * chủ. Kèm hai phép thuần của màn Tính tiền (một mức mỗi nhóm, mặc định không
 * ghi lên bill).
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/bien_tap_menu_640.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
var NEN = doc('00-nen.js'), POS = doc('09-tinh-tien-quay.js'), GMB = doc('66-goi-mon-tai-ban.js'), BTMJS = doc('68-bien-tap-menu.js');

function layHam(src, ten) {
  var dau = src.search(new RegExp('(?:async )?function ' + ten + '\\('));
  if (dau < 0) throw new Error('Khong thay ham ' + ten);
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Ham ' + ten + ' khong dong ngoac');
}
function layBien(src, ten) {
  var m = new RegExp('var ' + ten + ' = [\\s\\S]*?;\\n').exec(src);
  if (!m) throw new Error('Khong thay bien ' + ten);
  return m[0];
}
var MA = ['h', 'money'].map(function (t) { return layHam(NEN, t); }).join('\n') + '\n' +
  layBien(GMB, 'QUYEN_GMB_QR') + layHam(GMB, 'coQuyenGmbQr') + '\n' + layHam(POS, 'posNhomTc') + '\n' + layHam(POS, 'posChonTc') + '\n' + BTMJS;

var ket = { dat: 0, hong: 0 };
function dung(mo, dk) { if (!dk) throw new Error(mo); }
function bang(mo, a, b) {
  var x = JSON.stringify(a), y = JSON.stringify(b);
  if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y);
}
function cho(ms) { return new Promise(function (r) { setTimeout(r, ms || 30); }); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n        ') : e)); }
}
function chu(el) { var s = el._chu || ''; (el.children || []).forEach(function (c) { s += chu(c); }); return s; }

function menuGoc() {
  return {
    nhom: [{ ma: 'banh', ten: 'Bánh trên tủ', loai: 'banh', hien: 1 },
      { ma: 'n-tra', ten: 'Trà', loai: 'nuoc', hien: 1, goc: 'Trà', mon: ['NUTR00090', 'NUTR00040'] },
      { ma: 'n-ca-phe', ten: 'Cà phê', loai: 'nuoc', hien: 1, goc: 'Cà phê', mon: ['NUCF00003'] }],
    an: [],
    tuy_chon: [{ ten: 'Đá', muc: ['Bình thường', 'Ít đá', 'Không đá'], mac_dinh: 'Bình thường', ap: ['n-tra', 'n-ca-phe'] },
      { ten: 'Đường', muc: ['Bình thường', '50% đường'], mac_dinh: 'Bình thường', ap: ['n-tra', 'n-ca-phe'] }],
    topping: { TPNC00001: ['n-tra', 'n-ca-phe'], TPNC00005: ['n-tra', 'n-ca-phe'] },
    mon: {}
  };
}
var MON = [
  { ma: 'NUTR00090', ten: 'Kombucha Cherry', gia: 120000, anh: '/files/kom.jpg', goc: 'Trà', khong_pha: 0, mo_ta: 'Lên men', ban_web: 1 },
  { ma: 'NUTR00040', ten: 'Kombucha Chill, chai 300ml', gia: 100000, anh: '', goc: 'Trà', khong_pha: 1, mo_ta: '', ban_web: 1 },
  { ma: 'NUCF00003', ten: 'Cà phê sữa', gia: 40000, anh: '', goc: 'Cà phê', khong_pha: 0, mo_ta: '', ban_web: 1 },
  { ma: 'NUTR00099', ten: 'Trà Ô Long Đào', gia: 65000, anh: '', goc: 'Trà', khong_pha: 0, mo_ta: '', ban_web: 1 }];
var TOP = [{ ma: 'TPNC00001', ten: 'Trân châu ô long', gia: 10000 }, { ma: 'TPNC00005', ten: 'Thêm Cà Phê Phin', gia: 15000 }];

function moApp(o) {
  o = o || {};
  var tai = dg.taiLieuGia();
  var goi = [], tin = [], stack = [], hoi = (o.hoi || []).slice();
  var may = { dang: menuGoc(), nhap: menuGoc(), phien: 1 };
  function thayDoi() { return JSON.stringify(may.nhap) === JSON.stringify(may.dang) ? [] : ['Có thay đổi']; }
  var g = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, Number: Number, Date: Date, isNaN: isNaN, parseInt: parseInt,
    setTimeout: function (f, ms) { return setTimeout(f, ms > 100 ? 5 : ms); }, clearTimeout: clearTimeout,
    hasRole: function (r) { return (o.vai || ['VGB - Quản lý cửa hàng']).indexOf(r) >= 0; },
    busy: function () {}, toast: function (s) { tin.push(String(s)); },
    hoiChu: function () { return Promise.resolve(hoi.length ? hoi.shift() : null); },
    confirmSheet: function () { return Promise.resolve(o.xacNhan !== false); },
    go: function (fn) { stack.push(fn); return fn(); },
    back: function () { stack.pop(); var fn = stack[stack.length - 1]; if (fn) return fn(); },
    frame: function (tieuDe, html, opt) {
      tai.body.children = [];
      var vb = new dg.ElementGia('div'); vb.setAttribute('id', 'vgbBody');
      vb.innerHTML = html + ((opt && opt.footer) || '');
      tai.body.appendChild(vb);
      g._tieuDe = tieuDe;
      return vb;
    },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: JSON.parse(JSON.stringify(ts)) });
      if (duong === 'vagabond.bien_tap_menu.mo') {
        return Promise.resolve({ diem: ts.diem || 'TCV', ten_diem: ts.diem === 'NVHTN' ? 'NVHTN' : 'District 1',
          cac_diem: [{ ma: 'TCV', ten: 'District 1' }, { ma: 'NVHTN', ten: 'NVHTN' }],
          nhap: JSON.parse(JSON.stringify(may.nhap)), dang_chay: JSON.parse(JSON.stringify(may.dang)), phien: may.phien,
          thay_doi: thayDoi(), mon: JSON.parse(JSON.stringify(MON)), topping: TOP, chua_xep: ['NUTR00099'],
          lich_su: [{ phien: may.phien, luc: '2026-11-05 20:00:00', boi: 'de@x', thay_doi: 'Đổi thứ tự nhóm' }, { phien: may.phien - 1, luc: '2026-11-04 09:00:00', boi: 'de@x', thay_doi: 'Bản đầu' }] });
      }
      if (duong === 'vagabond.bien_tap_menu.luu_nhap') { may.nhap = JSON.parse(ts.noi_dung); return Promise.resolve({ ok: 1, thay_doi: thayDoi() }); }
      if (duong === 'vagabond.bien_tap_menu.xuat_ban') { may.dang = JSON.parse(JSON.stringify(may.nhap)); may.phien++; return Promise.resolve({ ok: 1, phien: may.phien }); }
      if (duong === 'vagabond.bien_tap_menu.bo_nhap') { may.nhap = JSON.parse(JSON.stringify(may.dang)); return Promise.resolve({ ok: 1 }); }
      if (duong === 'vagabond.bien_tap_menu.khoi_phuc') { may.phien++; return Promise.resolve({ ok: 1, phien: may.phien }); }
      return Promise.reject(new Error('api la: ' + duong));
    }
  };
  g.window = g;
  vm.runInNewContext(MA, g, { filename: 'bien-tap-menu.js' });
  return { g: g, tai: tai, goi: goi, tin: tin, may: may, stack: stack };
}
function q(m, chon) { var el = m.tai.body.querySelector(chon); if (!el) throw new Error('khong thay ' + chon); return el; }
function qs(m, chon) { return m.tai.body.querySelectorAll(chon); }
async function bam(m, chon) { q(m, chon).click(); await cho(); }
async function moMan(o) { var m = moApp(o); await m.g.go(m.g.scrBienTapMenu); await cho(); return m; }
function luuCuoi(m) { var ds = m.goi.filter(function (x) { return x.duong === 'vagabond.bien_tap_menu.luu_nhap'; }); return ds.length ? JSON.parse(ds[ds.length - 1].ts.noi_dung) : null; }

(async function () {
  console.log('v640 màn Biên tập menu');

  await ca('Mở màn: quản lý thấy chip hai điểm, thanh "Menu đang chạy", ba tab, các nhóm đúng thứ tự có ≡ kéo và công tắc; nhân viên thường bị chặn, không gọi máy chủ', async function () {
    var m = await moMan();
    bang('gọi mở', m.goi[0], { duong: 'vagabond.bien_tap_menu.mo', ts: { diem: '' } });
    bang('chip điểm', qs(m, '[data-btmdiem]').map(function (x) { return x.getAttribute('data-btmdiem'); }), ['TCV', 'NVHTN']);
    dung('thanh trạng thái', chu(q(m, '#btmBang')).indexOf('Menu đang chạy') >= 0 && chu(q(m, '#btmBang')).indexOf('Giống hệt menu đang chạy') >= 0);
    bang('ba tab', qs(m, '[data-btmtab]').map(function (x) { return chu(x); }), ['Thứ tự', 'Tuỳ chọn', 'Topping']);
    bang('nhóm', qs(m, '[data-btmhang]').map(function (x) { return x.getAttribute('data-ma'); }), ['banh', 'n-tra', 'n-ca-phe']);
    dung('mỗi dòng có ≡ kéo', qs(m, '[data-btmhang]').every(function (r) { return !!r.querySelector('[data-keo]'); }));
    dung('nhắc món chưa xếp', chu(m.tai.body).indexOf('1 món mới chưa xếp') >= 0);
    var m2 = await moMan({ vai: ['Sales User'] });
    dung('chặn', chu(m2.tai.body).indexOf('Chỉ quản lý cửa hàng') >= 0 && !m2.goi.length);
  });

  await ca('Kéo thả nhóm THẬT: giữ ≡ của Cà phê kéo lên trên Trà rồi thả; bản nháp gửi máy chủ đúng thứ tự mới; thanh đổi thành "Bản nháp, khách chưa thấy"', async function () {
    var m = await moMan();
    var hang = qs(m, '[data-btmhang]');
    hang.forEach(function (r, i) { r.getBoundingClientRect = function () { return { top: i * 60, height: 56 }; }; });
    var ds = q(m, '#btmDsNhom'), keo = hang[2].querySelector('[data-keo]');
    ds.dispatchEvent(dg.suKien('pointerdown', { clientY: 148, pointerId: 1 }, keo));
    dung('dòng nổi lên', String(hang[2].style.outline).indexOf('#0FB5CE') >= 0);
    ds.dispatchEvent(dg.suKien('pointermove', { clientY: 75 }, keo));
    ds.dispatchEvent(dg.suKien('pointerup', { clientY: 75 }, keo));
    await cho(60);
    bang('nhóm sau kéo', luuCuoi(m).nhom.map(function (x) { return x.ma; }), ['banh', 'n-ca-phe', 'n-tra']);
    bang('màn vẽ lại đúng thứ tự', qs(m, '[data-btmhang]').map(function (x) { return x.getAttribute('data-ma'); }), ['banh', 'n-ca-phe', 'n-tra']);
    dung('thanh nháp', chu(q(m, '#btmBang')).indexOf('Bản nháp, khách chưa thấy') >= 0 && chu(q(m, '#btmBang')).indexOf('1 thay đổi') >= 0);
    bang('phép thuần đổi chỗ', m.g.btmDoiCho(['a', 'b', 'c', 'd'], 3, 0), ['d', 'a', 'b', 'c']);
    bang('vị trí thả', [m.g.btmViTri([28, 88, 148], 75, 2), m.g.btmViTri([28, 88, 148], 200, 0)], [1, 2]);
  });

  await ca('Công tắc nhóm: tắt Trà là ẩn trên web (hien 0), dòng ghi "đang ẩn trên web"; thêm nhóm Trà sữa có mã không trùng', async function () {
    var m = await moMan({ hoi: ['Trà sữa'] });
    await bam(m, '[data-btmhien="n-tra"]');
    await cho(40);
    bang('hien', luuCuoi(m).nhom.filter(function (x) { return x.ma === 'n-tra'; })[0].hien, 0);
    dung('dòng ghi đang ẩn', chu(q(m, '[data-ma="n-tra"]')).indexOf('đang ẩn trên web') >= 0);
    await bam(m, '[data-btmthemnhom]');
    await cho(40);
    var nh = luuCuoi(m).nhom;
    bang('nhóm mới cuối', [nh[nh.length - 1].ma, nh[nh.length - 1].ten, nh[nh.length - 1].mon], ['n-tra-sua', 'Trà sữa', []]);
  });

  await ca('Tab Tuỳ chọn: bấm "Ít đá" làm mặc định (★), bấm lại bỏ; × bỏ một mức; tắt áp Đá cho Cà phê; + Thêm mức; nhóm phải còn ít nhất một mức', async function () {
    var m = await moMan({ hoi: ['Đá riêng'] });
    await bam(m, '[data-btmtab="tuy_chon"]');
    dung('★ ở Bình thường', chu(q(m, '[data-btmmuc="0:0"]')).indexOf('★ Bình thường') === 0);
    await bam(m, '[data-btmmuc="0:1"]');
    await cho(40);
    bang('mặc định mới', luuCuoi(m).tuy_chon[0].mac_dinh, 'Ít đá');
    await bam(m, '[data-btmmuc="0:1"]');
    await cho(40);
    bang('bấm lại: không mặc định', luuCuoi(m).tuy_chon[0].mac_dinh, '');
    await bam(m, '[data-btmmucxoa="0:2"]');
    await bam(m, '[data-btmtcap="0:n-ca-phe"]');
    await bam(m, '[data-btmmucthem="0"]');
    await cho(40);
    var t = luuCuoi(m).tuy_chon[0];
    bang('mức và áp', [t.muc, t.ap], [['Bình thường', 'Ít đá', 'Đá riêng'], ['n-tra']]);
    await bam(m, '[data-btmmucxoa="1:1"]');
    await bam(m, '[data-btmmucxoa="1:0"]');
    dung('không bỏ mức cuối', m.tin.some(function (s) { return s.indexOf('ít nhất một mức') >= 0; }));
  });

  await ca('Tab Topping: tích bỏ "Thêm Cà Phê Phin" cho Trà; ô tích ghi aria-checked đúng; giá topping chỉ xem', async function () {
    var m = await moMan();
    await bam(m, '[data-btmtab="topping"]');
    bang('ô đang tích', q(m, '[data-btmtp="TPNC00005:n-tra"]').getAttribute('aria-checked'), 'true');
    await bam(m, '[data-btmtp="TPNC00005:n-tra"]');
    await cho(40);
    bang('topping theo nhóm', luuCuoi(m).topping, { TPNC00001: ['n-tra', 'n-ca-phe'], TPNC00005: ['n-ca-phe'] });
    bang('ô bỏ tích', q(m, '[data-btmtp="TPNC00005:n-tra"]').getAttribute('aria-checked'), 'false');
    dung('giá hiện', chu(m.tai.body).indexOf('+15.000 đ') >= 0 && !qs(m, 'input').length);
  });

  await ca('Mở nhóm Trà: ẩn Kombucha trên web; xếp món mới vào Trà; mở món: sửa mô tả web, tắt riêng Đường và Thêm Cà Phê Phin, chuyển sang Cà phê; món chai ghi không hỏi đá đường', async function () {
    var m = await moMan();
    await bam(m, '[data-btmnhom="n-tra"]');
    bang('món trong nhóm', qs(m, '[data-btmhang]').map(function (x) { return x.getAttribute('data-ma'); }), ['NUTR00090', 'NUTR00040']);
    dung('chai ghi đóng sẵn', chu(q(m, '[data-ma="NUTR00040"]')).indexOf('đóng sẵn, không hỏi đá đường') >= 0);
    dung('Kombucha ghi 2 tuỳ chọn 2 topping', chu(q(m, '[data-ma="NUTR00090"]')).indexOf('2 tuỳ chọn · 2 topping') >= 0);
    await bam(m, '[data-btman="NUTR00090"]');
    await bam(m, '[data-btmxep="NUTR00099"]');
    await cho(40);
    var n = luuCuoi(m);
    bang('ẩn và xếp', [n.an, n.nhom[1].mon], [['NUTR00090'], ['NUTR00090', 'NUTR00040', 'NUTR00099']]);
    await bam(m, '[data-btmmon="NUTR00090"]');
    var mt = q(m, '#btmMoTa');
    mt.value = 'Cherry chín mọng';
    mt.dispatchEvent(dg.suKien('input', {}, mt));
    await bam(m, '[data-btmtattc="Đường"]');
    await bam(m, '[data-btmtattp="TPNC00005"]');
    await cho(40);
    bang('sửa riêng', luuCuoi(m).mon.NUTR00090, { mo_ta: 'Cherry chín mọng', tat_tc: ['Đường'], tat_tp: ['TPNC00005'] });
    dung('màn ghi tắt riêng', chu(m.tai.body).indexOf('Món này tắt riêng: Đường, Thêm Cà Phê Phin') >= 0);
    await bam(m, '[data-btmchuyen="n-ca-phe"]');
    await cho(40);
    var n2 = luuCuoi(m);
    bang('chuyển nhóm', [n2.nhom[1].mon, n2.nhom[2].mon], [['NUTR00040', 'NUTR00099'], ['NUCF00003', 'NUTR00090']]);
  });

  await ca('Xem và xuất bản: thay đổi hiện đủ; Xuất bản gọi máy chủ một lần, báo phiên mới, về màn chính tải lại; Quay về bản trước gọi đúng phiên; không thay đổi thì Xuất bản tắt', async function () {
    var m = await moMan();
    await bam(m, '[data-btmhien="n-ca-phe"]');
    await cho(40);
    await bam(m, '[data-btmxuat]');
    await cho(40);
    dung('liệt kê thay đổi', chu(m.tai.body).indexOf('1 thay đổi so với menu đang chạy') >= 0 && chu(m.tai.body).indexOf('Có thay đổi') >= 0);
    dung('xem trước có nhóm Trà, không còn Cà phê', chu(m.tai.body).indexOf('Trà · 2') >= 0 && chu(m.tai.body).indexOf('Cà phê · 1') < 0);
    m.tai.body.querySelector('#btmXuatBan').onclick();
    await cho(60);
    bang('gọi xuất bản một lần', m.goi.filter(function (x) { return x.duong === 'vagabond.bien_tap_menu.xuat_ban'; }).length, 1);
    dung('báo phiên 2', m.tin.some(function (s) { return s.indexOf('Đã xuất bản menu phiên 2 cho District 1') >= 0; }));
    dung('về màn chính, đọc lại', m.goi[m.goi.length - 1].duong === 'vagabond.bien_tap_menu.mo' && chu(q(m, '#btmBang')).indexOf('Menu đang chạy') >= 0);
    await bam(m, '[data-btmxuat]');
    await cho(40);
    dung('không đổi: Xuất bản tắt', q(m, '#btmXuatBan').hasAttribute('disabled'));
    await bam(m, '[data-btmkhoiphuc="1"]');
    await cho(60);
    bang('quay về phiên 1', m.goi.filter(function (x) { return x.duong === 'vagabond.bien_tap_menu.khoi_phuc'; }).map(function (x) { return x.ts; }), [{ diem: 'TCV', phien: 1 }]);
  });

  await ca('Màn Tính tiền (phép thuần): mỗi nhóm một mức, bấm mức khác thì thay, bấm lại hoặc bấm mặc định thì bỏ; nhóm theo món trước, theo nhóm gốc sau', async function () {
    var m = moApp();
    var da = { nhom: 'Đá', lua_chon: ['Bình thường', 'Ít đá', 'Không đá'], mac_dinh: 'Bình thường' };
    var duong = { nhom: 'Đường', lua_chon: ['Bình thường', '50% đường'], mac_dinh: 'Bình thường' };
    var tc = m.g.posChonTc([], da, 'Ít đá');
    tc = m.g.posChonTc(tc, duong, '50% đường');
    tc = m.g.posChonTc(tc, da, 'Không đá');
    bang('thay trong nhóm', tc, ['50% đường', 'Không đá']);
    bang('bấm lại thì bỏ', m.g.posChonTc(tc, da, 'Không đá'), ['50% đường']);
    bang('bấm mặc định thì bỏ, không ghi lên bill', m.g.posChonTc(tc, da, 'Bình thường'), ['50% đường']);
    var theoMon = { NUTR00090: [da] };
    bang('theo món', m.g.posNhomTc({ item_code: 'NUTR00090', nhom: 'Trà' }, theoMon, [duong]).map(function (x) { return x.nhom; }), ['Đá']);
    bang('món lạ: theo nhóm gốc', m.g.posNhomTc({ item_code: 'X', nhom: 'Trà' }, theoMon, [{ nhom: 'Đường', lua_chon: [], nhom_mon: ['Trà'] }, { nhom: 'Kem', lua_chon: [], nhom_mon: ['Ice Cream - Kem'] }]).map(function (x) { return x.nhom; }), ['Đường']);
  });

  console.log('\n' + ket.dat + ' ca dat, ' + ket.hong + ' ca hong');
  process.exit(ket.hong ? 1 : 0);
})();

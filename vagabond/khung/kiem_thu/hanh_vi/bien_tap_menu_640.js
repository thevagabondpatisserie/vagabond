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
var MA = ['h', 'money', 'vgbChuan', 'vgbKhop'].map(function (t) { return layHam(NEN, t); }).join('\n') + '\n' +
  layBien(GMB, 'QUYEN_GMB_QR') + layHam(GMB, 'coQuyenGmbQr') + '\n' + layHam(POS, 'posNhomTc') + '\n' + layHam(POS, 'posChonTc') + '\n' +
  layBien(POS, 'POS_TC') + layBien(POS, 'POS_TC_HAN') + ['posBayGio', 'posCanTaiTc', 'posQuenTc', 'posMoTuyChon'].map(function (t) { return layHam(POS, t); }).join('\n') + '\n' + BTMJS;

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
      { ten: 'Đường', muc: ['Bình thường', '50% đường'], mac_dinh: 'Bình thường', ap: ['n-tra', 'n-ca-phe'] },
      /* v642: nhóm tuỳ chọn chưa áp nhóm món nào, để ca sửa riêng bật "Có" cho một món. */
      { ten: 'Nhiệt độ', muc: ['Đá', 'Nóng'], mac_dinh: 'Đá', ap: [] }],
    topping: { TPNC00001: ['n-tra', 'n-ca-phe'], TPNC00005: ['n-tra', 'n-ca-phe'] },
    mon: {}
  };
}
var MON = [
  { ma: 'NUTR00090', ten: 'Kombucha Cherry', gia: 120000, anh: '/files/kom.jpg', goc: 'Trà', khong_pha: 0, mo_ta: 'Lên men', ban_web: 1 },
  { ma: 'NUTR00040', ten: 'Kombucha Chill, chai 300ml', gia: 100000, anh: '', goc: 'Trà', khong_pha: 1, mo_ta: '', ban_web: 1 },
  { ma: 'NUCF00003', ten: 'Cà phê sữa', gia: 40000, anh: '', goc: 'Cà phê', khong_pha: 0, mo_ta: '', ban_web: 1 },
  { ma: 'NUTR00099', ten: 'Trà Ô Long Đào', gia: 65000, anh: '', goc: 'Trà', khong_pha: 0, mo_ta: '', ban_web: 1 }];
/* v652: bánh từng bày ở tủ điểm (máy chủ bien_tap_menu.banh_cua_diem). */
var BANH = [
  { ma: 'BKMN00011', ten: 'Mille-feuille Vanilla', gia: 95000, anh: '/files/mille.jpg', mo_ta: 'Bánh ngàn lớp kem vani' },
  { ma: 'BKMN00020', ten: 'Tarte Chanh Dây', gia: 85000, anh: '', mo_ta: '' }];
var TOP = [{ ma: 'TPNC00001', ten: 'Trân châu ô long', gia: 10000 }, { ma: 'TPNC00005', ten: 'Thêm Cà Phê Phin', gia: 15000 },
  { ma: 'TPNC00007', ten: 'Thạch cà phê', gia: 15000 }];

function moApp(o) {
  o = o || {};
  var tai = dg.taiLieuGia();
  var goi = [], tin = [], stack = [], hoi = (o.hoi || []).slice(), treo = [];
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
          thay_doi: thayDoi(), mon: JSON.parse(JSON.stringify(MON)), topping: TOP, chua_xep: ['NUTR00099'], banh: o.khongBanh ? [] : JSON.parse(JSON.stringify(BANH)),
          lich_su: [{ phien: may.phien, luc: '2026-11-05 20:00:00', boi: 'de@x', thay_doi: 'Đổi thứ tự nhóm' }, { phien: may.phien - 1, luc: '2026-11-04 09:00:00', boi: 'de@x', thay_doi: 'Bản đầu' }] });
      }
      if (duong === 'vagabond.bien_tap_menu.luu_nhap') {
        /* o.giuLuu: lần lưu treo tới khi ca kiểm gọi m.thaLuu() (mạng chậm). */
        if (o.loiLuu) return Promise.reject(new Error('Mất kết nối, chưa lưu được.'));
        if (o.giuLuu) return new Promise(function (r) { treo.push(function () { may.nhap = JSON.parse(ts.noi_dung); r({ ok: 1, thay_doi: thayDoi() }); }); });
        may.nhap = JSON.parse(ts.noi_dung); return Promise.resolve({ ok: 1, thay_doi: thayDoi() });
      }
      if (duong === 'vagabond.bien_tap_menu.xuat_ban') { may.dang = JSON.parse(JSON.stringify(may.nhap)); may.phien++; return Promise.resolve({ ok: 1, phien: may.phien }); }
      if (duong === 'vagabond.bien_tap_menu.bo_nhap') { may.nhap = JSON.parse(JSON.stringify(may.dang)); return Promise.resolve({ ok: 1 }); }
      if (duong === 'vagabond.ban_hang.pos_ds_tuy_chon' && may.posLoi) { may.posLoi = 0; return Promise.reject(new Error('Mất mạng')); }
      if (duong === 'vagabond.ban_hang.pos_ds_tuy_chon') return Promise.resolve(JSON.parse(JSON.stringify(may.pos || { tc: [], mon: {} })));
      if (duong === 'vagabond.bien_tap_menu.khoi_phuc') { may.phien++; return Promise.resolve({ ok: 1, phien: may.phien }); }
      return Promise.reject(new Error('api la: ' + duong));
    }
  };
  g.window = g;
  vm.runInNewContext(MA, g, { filename: 'bien-tap-menu.js' });
  return { g: g, tai: tai, goi: goi, tin: tin, may: may, stack: stack, treo: treo, thaLuu: function () { while (treo.length) treo.shift()(); } };
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
    /* v642 (ảnh 2 anh Việt duyệt 06/11): ba nấc Theo nhóm / Có / Không cho MỌI tuỳ chọn, topping. */
    bang('đủ dòng: 3 tuỳ chọn, 3 topping', qs(m, '[data-nac="nhom"]').length, 6);
    await bam(m, '[data-btmnacid="tc:Đường:khong"]');
    await bam(m, '[data-btmnacid="tp:TPNC00005:khong"]');
    await bam(m, '[data-btmnacid="tc:Nhiệt độ:co"]');
    await bam(m, '[data-btmnacid="tp:TPNC00007:co"]');
    await cho(40);
    bang('sửa riêng', luuCuoi(m).mon.NUTR00090, { mo_ta: 'Cherry chín mọng', tat_tc: ['Đường'], tat_tp: ['TPNC00005'],
      bat_tc: ['Nhiệt độ'], bat_tp: ['TPNC00007'] });
    /* Codex PR #545 vòng 5: khối đọc có giới hạn (đếm số, ba mục đầu, "và N nữa"), danh sách đủ thu gọn. */
    var kt = chu(q(m, '#btmKhachThay'));
    dung('màn ghi khách sẽ thấy: ' + kt, kt.indexOf('Khách sẽ thấy 4: Đá, Nhiệt độ, Trân châu ô long và 1 nữa. Không thấy 2 mục.') >= 0);
    dung('danh sách đủ nằm trong mục thu gọn', kt.indexOf('Thấy: Đá, Nhiệt độ, Trân châu ô long, Thạch cà phê') >= 0 && kt.indexOf('Không thấy: Đường, Thêm Cà Phê Phin') >= 0 && m.tai.body.innerHTML.indexOf('<details') >= 0 && kt.indexOf('Xem đủ') >= 0);
    var vh = m.tai.body.innerHTML;
    dung('nút Về theo nhóm hết đứng trước khối chỉ để đọc', vh.indexOf('data-btmvenhom') >= 0 && vh.indexOf('data-btmvenhom') < vh.indexOf('id="btmKhachThay"'));
    bang('nấc đang chọn', q(m, '[data-btmnacid="tc:Nhiệt độ:co"]').getAttribute('aria-pressed'), 'true');
    /* Bấm Theo nhóm thì bỏ cài riêng của đúng dòng đó. */
    await bam(m, '[data-btmnacid="tp:TPNC00007:nhom"]');
    await cho(40);
    bang('về theo nhóm một dòng', luuCuoi(m).mon.NUTR00090.bat_tp, undefined);
    m.tai.body.querySelector('#btmMonXong').onclick();
    await cho(40);
    dung('danh sách món ghi nhãn Riêng 3 (Đường, Thêm Cà Phê Phin, Nhiệt độ)', chu(q(m, '[data-ma="NUTR00090"]')).indexOf('Riêng 3') >= 0);
    await bam(m, '[data-btmmon="NUTR00090"]');
    await bam(m, '[data-btmchuyen="n-ca-phe"]');
    await cho(40);
    var n2 = luuCuoi(m);
    await bam(m, '[data-btmvenhom]');
    await cho(40);
    bang('Về theo nhóm hết: bỏ mọi nấc riêng, giữ mô tả', luuCuoi(m).mon.NUTR00090, { mo_ta: 'Cherry chín mọng' });
    bang('chuyển nhóm', [n2.nhom[1].mon, n2.nhom[2].mon], [['NUTR00040', 'NUTR00099'], ['NUCF00003', 'NUTR00090']]);
  });

  await ca('v643 (anh Việt 07/11 không tìm ra chỗ chỉnh riêng từng món): tab Tuỳ chọn và tab Topping có khối Chỉnh riêng từng món với nút từng nhóm đồ uống; bấm nhóm ra danh sách món, bấm món tới khối Theo nhóm / Có / Không; tab Thứ tự có nút Món rõ chữ cao 44', async function () {
    var m = await moMan();
    var nut = qs(m, '[data-btmnhom]');
    dung('tab Thứ tự: nút Món rõ chữ ' + nut.map(chu).join('|'), nut.length >= 2 && nut.every(function (x) { return chu(x).indexOf('Món') === 0 && parseFloat(x.style.minHeight) >= 44; }));
    for (var tab of ['tuy_chon', 'topping']) {
      await bam(m, '[data-btmtab="' + tab + '"]');
      var khoi = q(m, '#btmLoiRieng');
      dung(tab + ': có khối chỉnh riêng từng món: ' + chu(khoi), chu(khoi).indexOf('Chỉnh riêng từng món') >= 0);
      var ds = khoi.querySelectorAll('[data-btmnhom]');
      dung(tab + ': nút nhóm Trà ghi số món ' + ds.map(chu).join('|'), ds.some(function (x) { return x.getAttribute('data-btmnhom') === 'n-tra' && /Trà · \d+ món/.test(chu(x)); }));
      dung(tab + ': nút cao 44', ds.every(function (x) { return parseFloat(x.style.minHeight) >= 44; }));
    }
    khoi.querySelectorAll('[data-btmnhom]').filter(function (x) { return x.getAttribute('data-btmnhom') === 'n-tra'; })[0].click();
    await cho();
    dung('mở nhóm Trà: thấy món', qs(m, '[data-btmmon="NUTR00090"]').length === 1);
    await bam(m, '[data-btmmon="NUTR00090"]');
    dung('tới khối riêng món', !!q(m, '#btmRiengMon') && qs(m, '[data-nac="nhom"]').length >= 1);
  });

  await ca('Codex PR #545 vòng 7 (AGENTS.md 2b.13): khối tuỳ chọn và topping riêng của món: mọi nút Theo nhóm / Có / Không, nút Về theo nhóm hết, Xem đủ cao ít nhất 44, mọi chữ ít nhất 13', async function () {
    var m = await moMan();
    await bam(m, '[data-btmnhom="n-tra"]');
    await bam(m, '[data-btmmon="NUTR00090"]');
    await bam(m, '[data-btmnacid="tc:Đường:khong"]');
    await cho(40);
    var html = m.tai.body.innerHTML;
    var dau = html.indexOf('id="btmRiengMon"');
    dung('có khối riêng món', dau >= 0);
    var khoi = html.slice(dau, html.indexOf('id="btmMonXong"') > dau ? html.indexOf('id="btmMonXong"') : html.length);
    var chu = (khoi.match(/font-size:\s*[0-9.]+px/g) || []).map(function (x) { return parseFloat(x.replace(/[^0-9.]/g, '')); });
    dung('có đọc được cỡ chữ', chu.length >= 8);
    bang('chữ nhỏ hơn 13', chu.filter(function (x) { return x < 13; }), []);
    var nut = khoi.match(/<(?:button|summary)\b[^>]*>/g) || [];
    dung('có nút', nut.length >= 18);
    bang('nút thấp hơn 44', nut.filter(function (x) { var c = /min-height:\s*([0-9.]+)px/.exec(x); return !c || parseFloat(c[1]) < 44; }), []);
  });

  await ca('Xem và xuất bản: thay đổi hiện đủ; Xuất bản gọi máy chủ một lần, báo phiên mới, về màn chính tải lại; Quay về bản trước gọi đúng phiên; không thay đổi thì Xuất bản tắt', async function () {
    var m = await moMan();
    await bam(m, '[data-btmhien="n-ca-phe"]');
    await cho(40);
    await bam(m, '[data-btmxuat]');
    await cho(40);
    dung('liệt kê thay đổi', chu(m.tai.body).indexOf('1 thay đổi so với menu đang chạy') >= 0 && chu(m.tai.body).indexOf('Có thay đổi') >= 0);
    dung('xem trước có nhóm Trà, không còn Cà phê', chu(m.tai.body).indexOf('Trà · 2') >= 0 && chu(m.tai.body).indexOf('Cà phê · 1') < 0);
    m.g.POS_TC = []; m.g.POS_TC_LUC = 1;
    m.tai.body.querySelector('#btmXuatBan').onclick();
    await cho(60);
    bang('xuất bản xong: màn Tính tiền trên máy này tải lại tuỳ chọn (Codex #543 vòng 3)', m.g.POS_TC, null);
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

  /* Codex PR #543: bấm "Xem và xuất bản" đúng lúc lần lưu nháp đã gửi đi mà máy
     chủ chưa trả lời. Màn xem phải chờ lần lưu đó xong, đọc đúng thay đổi mới và
     cho bấm Xuất bản; không được dựng với số thay đổi cũ (nút tắt mãi) hay xuất
     bản bản nháp cũ trên máy chủ. */
  await ca('Lưu nháp đang chạy dở khi bấm Xem và xuất bản: màn xem chờ lưu xong, thấy thay đổi mới, Xuất bản bấm được và chỉ gọi sau khi lưu xong', async function () {
    var m = await moMan({ giuLuu: true });
    await bam(m, '[data-btmhien="n-ca-phe"]');
    await cho(40);
    bang('lần lưu đã gửi, máy chủ chưa trả lời', [m.goi.filter(function (x) { return x.duong === 'vagabond.bien_tap_menu.luu_nhap'; }).length, m.treo.length], [1, 1]);
    q(m, '[data-btmxuat]').click();
    await cho(40);
    dung('chưa dựng màn xem với số cũ', chu(m.tai.body).indexOf('Không có thay đổi nào') < 0);
    m.thaLuu();
    await cho(60);
    var xb = m.tai.body.querySelector('#btmXuatBan');
    dung('màn xem thấy thay đổi mới', chu(m.tai.body).indexOf('1 thay đổi so với menu đang chạy') >= 0);
    dung('Xuất bản bấm được', xb && !xb.hasAttribute('disabled'));
    xb.onclick();
    await cho(60);
    var i = m.goi.map(function (x) { return x.duong; });
    dung('xuất bản gọi sau lần lưu', i.lastIndexOf('vagabond.bien_tap_menu.luu_nhap') < i.indexOf('vagabond.bien_tap_menu.xuat_ban'));
    bang('máy chủ xuất bản đúng bản nháp mới', m.may.dang.nhom.filter(function (x) { return x.ma === 'n-ca-phe'; })[0].hien, 0);
  });

  /* Codex PR #543 (AGENTS mục 2b.5): danh sách món trong nhóm phải có ô tìm nhanh. Gõ
     là lọc cả món đã xếp lẫn món chưa xếp, bỏ dấu, theo tên hoặc mã; đang lọc thì
     khoá kéo thả (thứ tự các dòng đang thấy không phải thứ tự thật của nhóm). */
  /* Codex PR #543 vòng 2: hai lần lưu nối nhau, lần đầu chưa xong mà lần sau đã gửi;
     máy chủ trả lần SAU trước. Không được báo "đã lưu" khi còn lần nào treo, và lần
     cũ về sau không được ghi đè bản mới. Ca này nhả các lần treo theo thứ tự NGƯỢC. */
  await ca('Hai lần lưu nháp nối nhau, máy chủ trả lần sau trước: chỉ báo đã lưu khi mọi lần xong, bản trên máy chủ là bản mới nhất, không bao giờ hai lần lưu cùng treo', async function () {
    var m = await moMan({ giuLuu: true });
    await bam(m, '[data-btmhien="n-ca-phe"]');
    await cho(40);
    await bam(m, '[data-btmhien="n-tra"]');
    await cho(40);
    var xong = null, toiDa = m.treo.length;
    m.g.btmChoLuu().then(function (v) { xong = v; });
    for (var i = 0; i < 6 && m.treo.length; i++) {
      toiDa = Math.max(toiDa, m.treo.length);
      m.treo.pop()();
      await cho(40);
      if (m.treo.length) dung('còn lần lưu treo mà đã báo xong', xong === null);
    }
    await cho(40);
    bang('không bao giờ hai lần lưu cùng treo', toiDa, 1);
    bang('báo đã lưu sau cùng', xong, true);
    bang('máy chủ giữ bản mới nhất', m.may.nhap.nhom.filter(function (x) { return x.loai === 'nuoc'; }).map(function (x) { return [x.ma, x.hien]; }), [['n-tra', 0], ['n-ca-phe', 0]]);
  });

  await ca('Ô tìm món trong nhóm: gõ tên không dấu hoặc mã là lọc cả món đã xếp và chưa xếp; không khớp thì báo; đang lọc thì khoá kéo thả; xoá chữ thì kéo lại được', async function () {
    var m = await moMan();
    await bam(m, '[data-btmnhom="n-tra"]');
    var o = q(m, '#btmTimMon');
    function go(chu) { o.value = chu; o.dispatchEvent(dg.suKien('input', {}, o)); }
    function thay() { return qs(m, '[data-btmtim]').filter(function (r) { return r.style.display !== 'none'; }).map(function (r) { return r.getAttribute('data-btmtim'); }); }
    bang('chưa gõ: đủ món đã xếp và chưa xếp', thay().length, 3);
    go('kombu');
    bang('gõ không dấu "kombu"', thay(), ['Kombucha Cherry NUTR00090', 'Kombucha Chill, chai 300ml NUTR00040']);
    go('o long dao');
    bang('tìm được món chưa xếp', thay(), ['Trà Ô Long Đào NUTR00099']);
    go('nutr00040');
    bang('tìm theo mã', thay(), ['Kombucha Chill, chai 300ml NUTR00040']);
    go('xyz');
    dung('không khớp thì báo', q(m, '#btmTimTrong').style.display !== 'none' && !thay().length);
    go('kombu');
    dung('đang lọc: ghi rõ, ẩn tay cầm', chu(q(m, '#btmNhomGhi')).indexOf('đang lọc') >= 0 && qs(m, '#btmDsMon [data-keo]').every(function (k) { return k.style.visibility === 'hidden'; }));
    var hang = qs(m, '[data-btmhang]');
    hang.forEach(function (r, i) { r.getBoundingClientRect = function () { return { top: i * 60, height: 56 }; }; });
    var ds = q(m, '#btmDsMon'), keo = hang[1].querySelector('[data-keo]');
    var truoc = m.goi.length;
    ds.dispatchEvent(dg.suKien('pointerdown', { clientY: 88, pointerId: 1 }, keo));
    ds.dispatchEvent(dg.suKien('pointermove', { clientY: 10 }, keo));
    ds.dispatchEvent(dg.suKien('pointerup', { clientY: 10 }, keo));
    await cho(60);
    bang('đang lọc: kéo không đổi gì', m.goi.length, truoc);
    go('');
    bang('xoá chữ: hiện lại đủ', thay().length, 3);
    ds.dispatchEvent(dg.suKien('pointerdown', { clientY: 88, pointerId: 1 }, keo));
    ds.dispatchEvent(dg.suKien('pointermove', { clientY: 10 }, keo));
    ds.dispatchEvent(dg.suKien('pointerup', { clientY: 10 }, keo));
    await cho(60);
    bang('hết lọc: kéo được', luuCuoi(m).nhom[1].mon, ['NUTR00040', 'NUTR00090']);
  });

  /* Codex PR #543 vòng 3: lưu nháp hỏng rồi bấm sang điểm khác thì không được bỏ
     thay đổi chưa lưu của điểm đang sửa. */
  await ca('Lưu nháp hỏng rồi bấm đổi điểm: ở lại điểm đang sửa, giữ thay đổi, báo rõ; không tải điểm mới', async function () {
    var m = await moMan({ loiLuu: true });
    await bam(m, '[data-btmhien="n-ca-phe"]');
    await cho(40);
    await bam(m, '[data-btmdiem="NVHTN"]');
    await cho(60);
    bang('vẫn điểm cũ', m.g.BTM && m.g.BTM.d.diem, 'TCV');
    bang('thay đổi chưa lưu còn nguyên', m.g.BTM.d.nhap.nhom.filter(function (x) { return x.ma === 'n-ca-phe'; })[0].hien, 0);
    dung('không mở điểm NVHTN', !m.goi.some(function (x) { return x.duong === 'vagabond.bien_tap_menu.mo' && x.ts.diem === 'NVHTN'; }));
    dung('báo chưa lưu được', m.tin.some(function (s) { return s.indexOf('chưa lưu được') >= 0 && s.indexOf('đổi điểm') >= 0; }));
  });

  /* Codex PR #543 vòng 3: quầy mở tuỳ chọn hai lần, giữa hai lần quản lý xuất bản
     menu mới (tắt hết tuỳ chọn của món) ở máy khác. Quá 60 giây phải hỏi lại máy chủ. */
  await ca('v645 ảnh trên web (Minh Vũ báo thiếu nút): mở món, bấm Tải ảnh lên, máy nén rồi gửi upload_file công khai, bản nháp ghi ảnh riêng, màn và danh sách hiện ảnh mới; Dùng ảnh danh mục bỏ ảnh riêng; tải lỗi thì báo, không ghi', async function () {
    var m = await moMan();
    var gui = [], tep = [];
    m.g.frappe = { csrf_token: 'tk' };
    m.g.FormData = function () { this.ds = []; this.append = function (k, v, ten) { this.ds.push([k, ten || (typeof v === 'string' ? v : '')]); }; };
    /* Ca chạy ĐÚNG đường bấm của màn; chỉ thay ba chỗ chạm trình duyệt: hộp chọn tệp,
       canvas (kiểm riêng bằng trình duyệt thật ở cong_cu/kiem_anh_menu_dom.cjs) và mạng. */
    m.g.btmChonTep = function () { return Promise.resolve({ name: 'IMG_7295.HEIC', size: 6 * 1024 * 1024 }); };
    m.g.btmNenVuong = function (f) { tep.push(f.name); return Promise.resolve({ blob: { size: 431000 }, canh: 1200, kb: 421 }); };
    var traLoi = { ok: true, j: { message: { file_url: '/files/menu-nutr00090.jpg' } } };
    m.g.fetch = function (u, o) { gui.push({ u: u, hd: o.headers, ds: o.body.ds }); return Promise.resolve({ ok: traLoi.ok, json: function () { return Promise.resolve(traLoi.j); } }); };
    await bam(m, '[data-btmnhom="n-tra"]');
    await bam(m, '[data-btmmon="NUTR00090"]');
    dung('khối Ảnh trên web', chu(q(m, '#btmAnhWeb')).indexOf('Đang dùng ảnh trong danh mục món') >= 0 && chu(q(m, '#btmAnhWeb')).indexOf('tự cắt vuông 1:1') >= 0);
    bang('chưa có nút bỏ', qs(m, '[data-btmanhbo]').length, 0);
    await bam(m, '[data-btmanhtai]');
    await cho(60);
    bang('nén đúng tệp đã chọn', tep, ['IMG_7295.HEIC']);
    bang('gửi upload_file một lần', gui.map(function (x) { return x.u; }), ['/api/method/upload_file']);
    bang('tệp công khai, tên theo mã món', gui[0].ds, [['file', 'menu-nutr00090.jpg'], ['is_private', '0'], ['folder', 'Home']]);
    bang('có khoá CSRF', gui[0].hd['X-Frappe-CSRF-Token'], 'tk');
    await cho(40);
    bang('bản nháp ghi ảnh riêng', luuCuoi(m).mon.NUTR00090, { anh: '/files/menu-nutr00090.jpg' });
    dung('báo kích thước', m.tin.some(function (x) { return x.indexOf('1200px') >= 0 && x.indexOf('421 KB') >= 0 && x.indexOf('Xem và xuất bản') >= 0; }));
    dung('màn hiện ảnh mới', m.tai.body.innerHTML.indexOf('/files/menu-nutr00090.jpg') >= 0);
    bang('nút đổi tên', chu(q(m, '[data-btmanhtai]')), 'Đổi ảnh');
    m.tai.body.querySelector('#btmMonXong').onclick();
    await cho(40);
    dung('danh sách món hiện ảnh web', q(m, '[data-ma="NUTR00090"]').innerHTML.indexOf('/files/menu-nutr00090.jpg') >= 0);
    await bam(m, '[data-btmmon="NUTR00090"]');
    await bam(m, '[data-btmanhbo]');
    await cho(40);
    bang('bỏ ảnh riêng (ô rỗng, máy chủ tự bỏ)', luuCuoi(m).mon.NUTR00090, {});
    dung('về ảnh danh mục', m.tai.body.innerHTML.indexOf('/files/kom.jpg') >= 0 && m.tai.body.innerHTML.indexOf('menu-nutr00090') < 0);
    traLoi = { ok: false, j: { _server_messages: JSON.stringify([JSON.stringify({ message: 'Tệp quá lớn' })]) } };
    var truoc = m.goi.length;
    await bam(m, '[data-btmanhtai]');
    await cho(60);
    dung('báo lỗi', m.tin[m.tin.length - 1].length > 0 && m.tin[m.tin.length - 1].indexOf('Đã cắt') < 0);
    bang('không ghi nháp', m.goi.slice(truoc).filter(function (x) { return x.duong === 'vagabond.bien_tap_menu.luu_nhap'; }).length, 0);
    m.g.btmChonTep = function () { return Promise.resolve(null); };
    await bam(m, '[data-btmanhtai]');
    await cho(30);
    bang('bỏ chọn tệp: không gửi gì', gui.length, 2);
    bang('cắt vuông chính giữa (thuần)', [m.g.btmCatVuong(4000, 3000), m.g.btmCatVuong(1080, 1920), m.g.btmCatVuong(600, 800)],
      [{ sx: 500, sy: 0, s: 3000, d: 1200 }, { sx: 0, sy: 420, s: 1080, d: 1080 }, { sx: 0, sy: 100, s: 600, d: 600 }]);
  });

  await ca('v652 bánh trên tủ (Minh Vũ không vào được danh mục món): nhóm Bánh trên tủ có nút Món; danh sách bánh từng bày ở tủ, tìm không dấu; mở bánh, tải ảnh, sửa mô tả thì bản nháp ghi ảnh và mô tả riêng; dòng nhóm đếm bánh sửa riêng; Dùng ảnh danh mục và xoá mô tả là bỏ hẳn; không có bánh thì báo rõ', async function () {
    var m = await moMan();
    var gui = [];
    m.g.frappe = { csrf_token: 'tk' };
    m.g.FormData = function () { this.ds = []; this.append = function (k, v, ten) { this.ds.push([k, ten || (typeof v === 'string' ? v : '')]); }; };
    m.g.btmChonTep = function () { return Promise.resolve({ name: 'banh.jpg', size: 3 * 1024 * 1024 }); };
    m.g.btmNenVuong = function () { return Promise.resolve({ blob: { size: 300000 }, canh: 1200, kb: 293 }); };
    m.g.fetch = function (u, o) { gui.push(o.body.ds); return Promise.resolve({ ok: true, json: function () { return Promise.resolve({ message: { file_url: '/files/menu-bkmn00020.jpg' } }); } }); };
    var nut = q(m, '[data-ma="banh"]').querySelector('[data-btmbanh]');
    dung('nút Món ở nhóm bánh cao 44', chu(nut).indexOf('Món') === 0 && String(nut.getAttribute('style')).indexOf('min-height:44px') >= 0);
    await bam(m, '[data-btmbanh]');
    bang('danh sách bánh', qs(m, '[data-btmbanhmon]').map(function (x) { return x.getAttribute('data-btmbanhmon'); }), ['BKMN00011', 'BKMN00020']);
    dung('giải thích', chu(m.tai.body).indexOf('Bánh tự lên menu theo tồn trên tủ') >= 0);
    var o = q(m, '#btmTimMon'); o.value = 'chanh day'; o.dispatchEvent(dg.suKien('input', {}, o)); await cho();
    bang('tìm không dấu', qs(m, '[data-btmbanhmon]').map(function (x) { return x.style.display; }), ['none', 'flex']);
    await bam(m, '[data-btmbanhmon="BKMN00020"]');
    dung('màn bánh: ảnh nền, chưa có nút bỏ ảnh', chu(q(m, '#btmAnhWeb')).indexOf('chưa có ảnh') >= 0 && !qs(m, '[data-btmanhbo]').length);
    await bam(m, '[data-btmanhtai]');
    await cho(60);
    bang('tải ảnh công khai, tên theo mã bánh', gui[0], [['file', 'menu-bkmn00020.jpg'], ['is_private', '0'], ['folder', 'Home']]);
    var mt = q(m, '#btmMoTa'); mt.value = 'Tart chanh dây chua nhẹ, vỏ giòn'; mt.dispatchEvent(dg.suKien('input', {}, mt));
    await cho(60);
    bang('bản nháp ghi ảnh và mô tả riêng', luuCuoi(m).mon.BKMN00020, { anh: '/files/menu-bkmn00020.jpg', mo_ta: 'Tart chanh dây chua nhẹ, vỏ giòn' });
    bang('đếm bánh sửa riêng (thuần)', m.g.btmSoBanhRieng(luuCuoi(m), BANH), 1);
    m.tai.body.querySelector('#btmMonXong').onclick();
    await cho(40);
    dung('danh sách hiện ảnh mới và nhãn', q(m, '[data-btmbanhmon="BKMN00020"]').innerHTML.indexOf('/files/menu-bkmn00020.jpg') >= 0 && chu(q(m, '[data-btmbanhmon="BKMN00020"]')).indexOf('ảnh riêng, mô tả riêng') >= 0);
    m.g.back(); await cho(40);
    dung('dòng nhóm Bánh trên tủ đếm', chu(q(m, '[data-ma="banh"]')).indexOf('1 bánh có ảnh, mô tả riêng') >= 0);
    await bam(m, '[data-btmbanh]');
    await bam(m, '[data-btmbanhmon="BKMN00020"]');
    await bam(m, '[data-btmanhbo]');
    mt = q(m, '#btmMoTa'); mt.value = ''; mt.dispatchEvent(dg.suKien('input', {}, mt));
    await cho(60);
    bang('bỏ hẳn: không còn khoá bánh trong nháp', Object.prototype.hasOwnProperty.call(luuCuoi(m).mon, 'BKMN00020'), false);
    var m2 = await moMan({ khongBanh: true });
    await bam(m2, '[data-btmbanh]');
    dung('không có bánh thì báo rõ', chu(m2.tai.body).indexOf('chưa có bánh nào lên tủ trong 60 ngày') >= 0 && !qs(m2, '[data-btmbanhmon]').length);
  });

  await ca('Màn Tính tiền: bảng tuỳ chọn giữ tối đa 60 giây rồi hỏi lại máy chủ; đổi quầy hỏi lại; lỗi mạng không giữ bảng rỗng', async function () {
    var m = moApp();
    var T = 1000;
    m.g.posBayGio = function () { return T; };
    m.g.posDon = { mon: [{ item_code: 'NUTR00090', ten: 'Kombucha Cherry', nhom: 'Trà', tc: [] }] };
    m.g.posQuay = { ma: 'Q1' };
    m.g.scrPosQuay = function () {};
    var da = { nhom: 'Đá', lua_chon: ['Bình thường', 'Ít đá', 'Không đá'], mac_dinh: 'Bình thường' };
    m.may.pos = { tc: [], mon: { NUTR00090: [da] } };
    function soGoi() { return m.goi.filter(function (x) { return x.duong === 'vagabond.ban_hang.pos_ds_tuy_chon'; }).length; }
    function soNut() { return m.tai.body.querySelectorAll('[data-tc]').length; }
    await m.g.posMoTuyChon(0);
    bang('lần đầu: hỏi máy chủ, hiện 3 mức Đá', [soGoi(), soNut()], [1, 3]);
    m.tai.body.children = [];
    m.may.pos = { tc: [], mon: { NUTR00090: [] } };
    T += 30000;
    await m.g.posMoTuyChon(0);
    bang('trong 60 giây: dùng bảng đang giữ', soGoi(), 1);
    m.tai.body.children = [];
    T += 31000;
    await m.g.posMoTuyChon(0);
    bang('quá 60 giây: hỏi lại, menu mới tắt hết nên không hiện bảng', [soGoi(), soNut()], [2, 0]);
    m.g.posQuay = { ma: 'Q2' };
    await m.g.posMoTuyChon(0);
    bang('đổi quầy: hỏi lại', soGoi(), 3);
    m.tai.body.children = [];
    m.may.pos = { tc: [], mon: { NUTR00090: [da] } };
    m.g.posQuay = { ma: 'Q3' };
    m.may.posLoi = 1;
    await m.g.posMoTuyChon(0);
    bang('lỗi mạng: không hiện bảng', [soGoi(), soNut()], [4, 0]);
    T += 1000;
    await m.g.posMoTuyChon(0);
    bang('mở lại ngay: hỏi lại máy chủ, có bảng', [soGoi(), soNut()], [5, 3]);
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
    /* Codex PR #543: món có trong bảng theo món với danh sách RỖNG (chai, tắt hết tuỳ
       chọn) không được rơi về nhóm gốc. */
    bang('tắt hết tuỳ chọn: không hỏi gì', m.g.posNhomTc({ item_code: 'NUTR00040', nhom: 'Trà' }, { NUTR00040: [] }, [{ nhom: 'Đá', lua_chon: [], nhom_mon: ['Trà'] }]), []);
    bang('món lạ: theo nhóm gốc', m.g.posNhomTc({ item_code: 'X', nhom: 'Trà' }, theoMon, [{ nhom: 'Đường', lua_chon: [], nhom_mon: ['Trà'] }, { nhom: 'Kem', lua_chon: [], nhom_mon: ['Ice Cream - Kem'] }]).map(function (x) { return x.nhom; }), ['Đường']);
  });

  console.log('\n' + ket.dat + ' ca dat, ' + ket.hong + ' ca hong');
  process.exit(ket.hong ? 1 : 0);
})();

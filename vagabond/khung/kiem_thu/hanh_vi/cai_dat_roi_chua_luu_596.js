/* Bộ ca kiểm HÀNH VI v596 (Codex #480): rời màn Cài đặt lõi khi còn thay đổi chưa lưu.
 *
 * Codex trên 3d0b446: chỉ nút ‹ trong app hỏi lại. Nút nhà gọi thẳng reset(scrHome),
 * nút Back của trình duyệt hay Android đi qua popstate cắt chồng màn mà không đọc
 * roiChuaLuu(), nên thay đổi đang sửa mất im lặng.
 *
 * Bộ này CHẠY THẬT:
 *   - khung app thật 01-khung-app.js (go, back, reset, frame, nút ‹ và nút nhà),
 *   - bộ nghe popstate thật lấy từ 12-van-don.js (chỉ lấy đúng câu đăng ký, không
 *     chạy __boot),
 *   - màn Cài đặt lõi thật 51-cai-dat-loi.js với tệp chung cai_dat_loi_chung.js.
 * Máy chủ, hộp hỏi và trang chủ là bản giả. Mỗi ca bấm đúng chuỗi thao tác của
 * quản trị, không gọi thêm hàm nào "cho chắc" (điều 15).
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/cai_dat_roi_chua_luu_596.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var cp = require('child_process');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
var KHUNG = doc('01-khung-app.js');
var CAI_DAT = doc('51-cai-dat-loi.js');
var CHUNG = fs.readFileSync(path.join(GOC, 'vagabond', 'public', 'js', 'cai_dat_loi_chung.js'), 'utf8');

/* Lấy ĐÚNG câu đăng ký popstate của app trong 12-van-don.js: phải có đúng một câu. */
function cauPopstate() {
  var src = doc('12-van-don.js');
  var dau = src.indexOf("window.addEventListener('popstate'");
  if (dau < 0 || src.indexOf("window.addEventListener('popstate'", dau + 1) >= 0) throw new Error('mong dung mot cau dang ky popstate trong 12-van-don.js');
  var mot = src.slice(dau);
  var het = /^window\.addEventListener\('popstate', \w+\);/.test(mot) ? mot.indexOf(';') + 1 : mot.indexOf('\n});') + 4;
  return mot.slice(0, het);
}

/* Kết quả lay() dựng bằng chính phép của máy chủ (cùng cách bộ 570). */
function layThat() {
  var py = [
    'import json, sys',
    'sys.path.insert(0, sys.argv[1])',
    'from vagabond.khung.kiem_thu import nen',
    'nen.gia_lap()',
    'from vagabond import cai_dat_loi as c',
    'from vagabond.khung.kiem_thu import thu_cai_dat_loi_570 as t',
    'tr = t._truong_da_xep()',
    'doc = {f["fieldname"]: (0 if f["fieldtype"] == "Check" else None) for f in tr}',
    'doc.update({"sepay_bat": 0, "sepay_khoa": "KHOA-SEPAY-THAT"})',
    'ra = {"bo_cuc": c.bo_cuc(tr), "gia_tri": c.gia_tri(tr, doc), "modified": "2026-10-04 09:00:00.000001", "bang": {}}',
    'sys.stdout.write(json.dumps(ra, ensure_ascii=False, default=str))',
  ].join('\n');
  return JSON.parse(cp.execFileSync('python3', ['-c', py, GOC], { encoding: 'utf8', maxBuffer: 1 << 26 }));
}
var LAY = layThat();

var ket = { dat: 0, hong: 0 };
function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + (e && e.message)); }
}
async function nghi() { for (var i = 0; i < 12; i++) await Promise.resolve(); await new Promise(function (r) { setImmediate(r); }); }

/* traLoi: hộp hỏi "Chưa lưu" trả gì (true là Rời đi). */
function appMoi(traLoi) {
  var tl = dg.taiLieuGia();
  tl.head = new dg.ElementGia('head');
  var vgb = tl.createElement('div'); vgb.id = 'vgb'; tl.body.appendChild(vgb);
  var hoi = [], lichSu = [], ngheW = {};
  var g = {
    console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array,
    Promise: Promise, Error: Error, RegExp: RegExp, parseFloat: parseFloat, parseInt: parseInt, isNaN: isNaN, Date: Date,
    document: tl, APPVER: 596,
    frappe: { session: { user: 'admin@vagabond.vn' } },
    location: { href: 'https://app.x/bep', pathname: '/bep', hostname: 'app.x', search: '', hash: '', replace: function () {} },
    history: {
      pushState: function (st) { lichSu.push(['push', st && st.vgbD]); },
      replaceState: function (st) { lichSu.push(['replace', st && st.vgbD]); },
      /* Như trình duyệt thật: history.back() lùi một mốc rồi BẮN popstate (bất đồng
         bộ) với mốc vừa tới. Thiếu bước này thì VGB_LUI_TAY không bao giờ được trả. */
      back: function () {
        lichSu.push(['back']);
        var toi = g.S.stack.length - 1;
        setImmediate(function () { (ngheW.popstate || []).forEach(function (f) { f({ state: { vgbD: toi } }); }); });
      },
    },
    requestAnimationFrame: function (f) { f(); },
    setTimeout: function (f) { f(); return 0; }, clearTimeout: function () {},
  };
  g.window = g;
  g.addEventListener = function (loai, ham) { (ngheW[loai] = ngheW[loai] || []).push(ham); };
  vm.createContext(g);
  vm.runInContext([
    'var root = document.getElementById("vgb");',
    'function h(s) { return String(s == null ? "" : s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;"); }',
    'function toast() {}', 'function sheet() {}', 'function dSkin() {}', 'function vgbGo() {}',
    'function shortWh(x) { return String(x || ""); }',
    'function inNapJs() { return Promise.resolve(); }',
    'function confirmSheet(t, m) { __hoi.push(t + ": " + m); return Promise.resolve(__traLoi); }',
    'function api(m) { if (m === "vagabond.cai_dat_loi.lay") return Promise.resolve(JSON.parse(JSON.stringify(__LAY))); return Promise.reject(new Error("api la " + m)); }',
    'async function scrHome() { frame(APPNAME, "<div>trang chu</div>"); }',
  ].join('\n'), Object.assign(g, { __hoi: hoi, __traLoi: traLoi, __LAY: LAY }));
  vm.runInContext(KHUNG, g);
  vm.runInContext(CHUNG, g);
  vm.runInContext(CAI_DAT, g);
  vm.runInContext(cauPopstate(), g);
  return {
    g: g, hoi: hoi, lichSu: lichSu,
    el: function (id) { return tl.getElementById(id); },
    sau: function () { return g.S.stack.length; },
    /* Nút Back của trình duyệt hay Android: trình duyệt lùi về mốc vgbD = d rồi bắn popstate. */
    backTrinhDuyet: async function (d) { (ngheW.popstate || []).forEach(function (f) { f({ state: { vgbD: d } }); }); await nghi(); },
    bam: async function (el) { if (el.onclick) el.onclick({ target: el, preventDefault: function () {} }); await nghi(); },
    bamTrongMan: async function (el) { var b = tl.getElementById('vgbBody'); b.onclick({ target: el, preventDefault: function () {} }); await nghi(); },
    cho: nghi,
  };
}

/* Mở trang chủ, vào Cài đặt lõi, mở nhóm Kế toán, bật công tắc SePay: còn 1 thay đổi. */
async function suaMotO(a) {
  await a.g.reset(a.g.scrHome); await a.cho();
  a.g.go(a.g.scrCaiDatLoi); await a.cho();
  var tab = a.g.document.querySelectorAll('[data-cdltab="tab_ke_toan"]');
  bang('một dòng nhóm Kế toán', tab.length, 1);
  await a.bamTrongMan(tab[0]);
  var cong = a.g.document.querySelectorAll('[data-cdlbat="sepay_bat"]');
  bang('một công tắc SePay', cong.length, 1);
  await a.bamTrongMan(cong[0]);
  bang('còn 1 thay đổi', a.g.cdlSoThay(), 1);
  bang('đang ở màn nhóm (nấc 3)', a.sau(), 3);
}

(async function () {
  await ca('Codex 3d0b446: bấm nút nhà ở màn nhóm khi còn thay đổi thì HỎI; chọn ở lại thì không mất gì', async function () {
    var a = appMoi(false);
    await suaMotO(a);
    await a.bam(a.el('vgbHome'));
    bang('hỏi đúng một lần', a.hoi.length, 1);
    dung('câu hỏi nói còn thay đổi chưa lưu', a.hoi[0].indexOf('Còn 1 thay đổi Cài đặt lõi chưa lưu') >= 0);
    bang('ở lại màn nhóm', a.sau(), 3);
    bang('thay đổi còn nguyên', a.g.cdlSoThay(), 1);
  });

  await ca('Bấm nút nhà khi còn thay đổi, chọn Rời đi: về trang chủ', async function () {
    var a = appMoi(true);
    await suaMotO(a);
    await a.bam(a.el('vgbHome'));
    bang('hỏi một lần', a.hoi.length, 1);
    bang('về trang chủ', a.sau(), 1);
    bang('không còn câu hỏi treo', a.g.roiChuaLuu(), '');
  });

  await ca('Codex 3d0b446: Back của trình duyệt từ tổng quan ra trang chủ khi còn thay đổi thì HỎI; ở lại thì giữ mốc lịch sử', async function () {
    var a = appMoi(false);
    await suaMotO(a);
    await a.bam(a.el('vgbBack'));
    bang('nút ‹ từ nhóm về tổng quan không hỏi', a.hoi.length, 0);
    bang('đang ở tổng quan', a.sau(), 2);
    a.lichSu.length = 0;
    await a.backTrinhDuyet(0);
    bang('hỏi một lần', a.hoi.length, 1);
    bang('ở lại tổng quan', a.sau(), 2);
    bang('thay đổi còn nguyên', a.g.cdlSoThay(), 1);
    dung('đẩy lại mốc của tổng quan để Back lần sau vẫn đúng', a.lichSu.some(function (x) { return x[0] === 'push' && x[1] === 1; }));
  });

  await ca('Back của trình duyệt nhảy thẳng từ màn nhóm về trang chủ (bỏ qua tổng quan) cũng HỎI', async function () {
    var a = appMoi(false);
    await suaMotO(a);
    await a.backTrinhDuyet(0);
    bang('hỏi một lần', a.hoi.length, 1);
    bang('ở lại màn nhóm', a.sau(), 3);
  });

  await ca('Back của trình duyệt từ màn nhóm về tổng quan KHÔNG hỏi (không mất gì), rồi Rời đi mới về trang chủ', async function () {
    var a = appMoi(true);
    await suaMotO(a);
    await a.backTrinhDuyet(1);
    bang('không hỏi', a.hoi.length, 0);
    bang('về tổng quan', a.sau(), 2);
    bang('thay đổi còn', a.g.cdlSoThay(), 1);
    await a.backTrinhDuyet(0);
    bang('lần này hỏi', a.hoi.length, 1);
    bang('chọn Rời đi thì về trang chủ', a.sau(), 1);
    bang('câu hỏi xoá theo', a.g.roiChuaLuu(), '');
  });

  await ca('Chưa sửa gì thì nút nhà và Back trình duyệt đi thẳng, không hỏi', async function () {
    var a = appMoi(false);
    await a.g.reset(a.g.scrHome); await a.cho();
    a.g.go(a.g.scrCaiDatLoi); await a.cho();
    await a.backTrinhDuyet(0);
    bang('Back không hỏi', a.hoi.length, 0);
    bang('về trang chủ', a.sau(), 1);
    a.g.go(a.g.scrCaiDatLoi); await a.cho();
    await a.bam(a.el('vgbHome'));
    bang('nút nhà không hỏi', a.hoi.length, 0);
    bang('về trang chủ', a.sau(), 1);
  });

  await ca('Nút ‹ từ tổng quan khi còn thay đổi vẫn hỏi như trước', async function () {
    var a = appMoi(false);
    await suaMotO(a);
    await a.bam(a.el('vgbBack'));
    await a.bam(a.el('vgbBack'));
    bang('hỏi một lần', a.hoi.length, 1);
    bang('ở lại tổng quan', a.sau(), 2);
  });

  await ca('Codex fbf05ff: Back trình duyệt rồi chọn ở lại thì ĐỊA CHỈ trở lại đúng màn Cài đặt (F5 không mở nhầm trang chủ)', async function () {
    // Trình duyệt đã nhảy sang mốc trang chủ (địa chỉ /bep) trước khi bắn popstate. Chọn
    // ở lại mà chỉ đẩy lại mốc với location.href cũ thì màn Cài đặt nằm dưới địa chỉ
    // trang chủ; F5 mở trang chủ và mất thay đổi. Sau khi đẩy lại mốc phải áp lại địa
    // chỉ của nấc đang đứng.
    var a = appMoi(false);
    a.g.window.vgbApDiaChi = function (slug) { a.lichSu.push(['ap', slug]); a.g.location.pathname = slug ? '/' + slug : '/bep'; };
    var sap = '';
    a.g.window.vgbSlugSapMo = function () { var s = sap; sap = ''; return s; };
    await a.g.reset(a.g.scrHome); await a.cho();
    sap = 'cai-dat-loi-va-api';
    a.g.go(a.g.scrCaiDatLoi); await a.cho();
    var tab = a.g.document.querySelectorAll('[data-cdltab="tab_ke_toan"]');
    await a.bamTrongMan(tab[0]);
    await a.bamTrongMan(a.g.document.querySelectorAll('[data-cdlbat="sepay_bat"]')[0]);
    a.lichSu.length = 0;
    a.g.location.pathname = '/bep'; a.g.location.href = 'https://app.x/bep';  // trình duyệt đã lùi
    await a.backTrinhDuyet(0);
    bang('hỏi một lần', a.hoi.length, 1);
    var iPush = -1;
    a.lichSu.forEach(function (x, i) { if (x[0] === 'push' && x[1] === 2) iPush = i; });
    dung('đẩy lại mốc của màn nhóm', iPush >= 0);
    var sau = a.lichSu.slice(iPush + 1).filter(function (x) { return x[0] === 'ap'; });
    bang('sau khi đẩy lại mốc thì áp lại địa chỉ Cài đặt', sau.map(function (x) { return x[1]; }), ['cai-dat-loi-va-api']);
    bang('thanh địa chỉ là Cài đặt', a.g.location.pathname, '/cai-dat-loi-va-api');
  });

  await ca('Khung app: lùi về đúng nấc giữ thay đổi thì GIỮ câu hỏi, kể cả khi màn đó không tự đặt lại lúc vẽ', async function () {
    // Đột biến "vgbSauCat luôn xoá" không đổ ca nào ở trên vì màn tổng quan Cài đặt lõi
    // tự đặt lại câu hỏi mỗi lần vẽ (dư một lớp, điều 17c). Ca này dùng màn giả không
    // tự đặt lại, để chốt đúng phần của khung app.
    var a = appMoi(false);
    await a.g.reset(a.g.scrHome); await a.cho();
    vm.runInContext('function scrCha() { frame("Cha", "<div>cha</div>"); } function scrCon() { frame("Con", "<div>con</div>"); }', a.g);
    a.g.go(a.g.scrCha); await a.cho();
    a.g.go(a.g.scrCon); await a.cho();
    a.g.S.chuaLuu = 'Còn thay đổi'; a.g.S.chuaLuuNac = 1;
    await a.backTrinhDuyet(1);
    bang('về màn cha không hỏi', a.hoi.length, 0);
    bang('câu hỏi vẫn còn sau khi cắt nấc con', a.g.roiChuaLuu(), 'Còn thay đổi');
    await a.bam(a.el('vgbHome'));
    bang('nút nhà vẫn hỏi', a.hoi.length, 1);
  });

  console.log('\n' + ket.dat + ' ca dat, ' + ket.hong + ' ca hong.');
  process.exitCode = ket.hong ? 1 : 0;
})();

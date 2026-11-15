/* Bộ ca kiểm HÀNH VI v660 (anh Việt 15/11/2026): nút Gửi thử WhatsApp ở Cài đặt lõi.
 *
 * Mã xác thực thật luôn đi Zalo trước, nên số có Zalo không bao giờ thử được
 * đường WhatsApp. Nút này gửi thẳng một mã thử qua whatsapp.gui_thu.
 *
 * CHẠY THẬT khung app 01-khung-app.js và màn Cài đặt lõi 51-cai-dat-loi.js (khung
 * dựng như bộ 596). Máy chủ là bản giả ghi lại mọi lời gọi. Mỗi ca bấm đúng chuỗi
 * thao tác của quản trị: mở Cài đặt lõi, mở nhóm Tin nhắn và cảnh báo, gõ số, bấm.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/wa_gui_thu_660.js
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
function appMoi(traLoi, traGuiThu) {
  var goi = [];
  var tl = dg.taiLieuGia();
  tl.head = new dg.ElementGia('head');
  var vgb = tl.createElement('div'); vgb.id = 'vgb'; tl.body.appendChild(vgb);
  var hoi = [], lichSu = [], ngheW = {};
  var g = {
    console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array,
    Promise: Promise, Error: Error, RegExp: RegExp, parseFloat: parseFloat, parseInt: parseInt, isNaN: isNaN, Date: Date,
    document: tl, APPVER: 660,
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
    'function api(m, a) { __goi.push([m, a]); if (m === "vagabond.cai_dat_loi.lay") return Promise.resolve(JSON.parse(JSON.stringify(__LAY))); if (m === "vagabond.whatsapp.gui_thu") return __traGuiThu(a); return Promise.reject(new Error("api la " + m)); }',
    'async function scrHome() { frame(APPNAME, "<div>trang chu</div>"); }',
  ].join('\n'), Object.assign(g, { __hoi: hoi, __traLoi: traLoi, __LAY: LAY, __goi: goi,
    __traGuiThu: function (a) { return traGuiThu ? traGuiThu(a) : Promise.resolve({ ok: 1, so: '+84901486556', ma: '482913' }); } }));
  vm.runInContext(KHUNG, g);
  vm.runInContext(CHUNG, g);
  vm.runInContext(CAI_DAT, g);
  vm.runInContext(cauPopstate(), g);
  return {
    g: g, hoi: hoi, lichSu: lichSu, goi: goi,
    el: function (id) { return tl.getElementById(id); },
    sau: function () { return g.S.stack.length; },
    /* Nút Back của trình duyệt hay Android: trình duyệt lùi về mốc vgbD = d rồi bắn popstate. */
    backTrinhDuyet: async function (d) { (ngheW.popstate || []).forEach(function (f) { f({ state: { vgbD: d } }); }); await nghi(); },
    bam: async function (el) { if (el.onclick) el.onclick({ target: el, preventDefault: function () {} }); await nghi(); },
    bamTrongMan: async function (el) { var b = tl.getElementById('vgbBody'); b.onclick({ target: el, preventDefault: function () {} }); await nghi(); },
    cho: nghi,
  };
}

async function moNhomTinNhan(a) {
  await a.g.reset(a.g.scrHome); await a.cho();
  a.g.go(a.g.scrCaiDatLoi); await a.cho();
  var tab = a.g.document.querySelectorAll('[data-cdltab="tab_tin_nhan"]');
  bang('một dòng nhóm Tin nhắn và cảnh báo', tab.length, 1);
  await a.bamTrongMan(tab[0]);
}
function nutGuiThu(a) {
  var n = a.g.document.querySelectorAll('[data-cdlwa="gui_thu"]');
  bang('đúng một nút Gửi thử WhatsApp', n.length, 1);
  return n[0];
}
function goiGuiThu(a) { return a.goi.filter(function (x) { return x[0] === 'vagabond.whatsapp.gui_thu'; }); }

(async function () {
  await ca('Gõ số anh Việt rồi bấm Gửi thử WhatsApp: gọi máy chủ đúng một lần với đúng số; màn báo đã gửi, nêu số và mã thử', async function () {
    var a = appMoi(true);
    await moNhomTinNhan(a);
    var o = a.el('cdl-wa-so');
    dung('có ô số nhận tin thử', !!o);
    o.value = '0901 486 556';
    await a.bamTrongMan(nutGuiThu(a));
    bang('gọi đúng một lần, đúng số', goiGuiThu(a).map(function (x) { return x[1]; }), [{ so: '0901 486 556' }]);
    var chu = a.el('cdl-wa').textContent;
    dung('báo đã gửi tới số', chu.indexOf('Đã gửi tới +84901486556') >= 0);
    dung('nêu mã thử', chu.indexOf('482913') >= 0);
    bang('ô số giữ nguyên sau khi vẽ lại', a.el('cdl-wa-so').value, '0901 486 556');
  });

  await ca('Chưa gõ số thì bấm KHÔNG gọi máy chủ', async function () {
    var a = appMoi(true);
    await moNhomTinNhan(a);
    await a.bamTrongMan(nutGuiThu(a));
    bang('không gọi gui_thu', goiGuiThu(a).length, 0);
  });

  await ca('Meta từ chối: màn hiện câu lỗi của máy chủ, không báo đã gửi', async function () {
    var a = appMoi(true, function () { return Promise.reject(new Error('WhatsApp chưa gửi được: Recipient not allowed')); });
    await moNhomTinNhan(a);
    a.el('cdl-wa-so').value = '+1 415 555 0100';
    await a.bamTrongMan(nutGuiThu(a));
    var chu = a.el('cdl-wa').textContent;
    dung('hiện câu lỗi', chu.indexOf('Recipient not allowed') >= 0 && chu.indexOf('Chưa gửi được') >= 0);
    dung('không báo đã gửi', chu.indexOf('Đã gửi tới') < 0);
  });

  await ca('Ô số nhận tin thử KHÔNG thành thay đổi Cài đặt chưa lưu (không bị hỏi khi rời màn)', async function () {
    var a = appMoi(true);
    await moNhomTinNhan(a);
    var o = a.el('cdl-wa-so');
    o.value = '0901486556';
    var b = a.el('vgbBody');
    if (b.oninput) b.oninput({ target: o });
    bang('không có thay đổi chưa lưu', a.g.cdlSoThay(), 0);
  });

  console.log('\n' + ket.dat + ' ca dat, ' + ket.hong + ' ca hong.');
  process.exitCode = ket.hong ? 1 : 0;
})();

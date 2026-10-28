/* Bộ ca kiểm HÀNH VI cho màn "Cài đặt lõi và API" trên app (v570, 04/10/2026).
 *
 * Nạp THẬT tệp 51-cai-dat-loi.js và tệp chung cai_dat_loi_chung.js vào DOM giả.
 * Dữ liệu máy chủ trả về KHÔNG gõ tay: chạy python dựng đúng kết quả của
 * vagabond.cai_dat_loi.lay() từ JSON thật của doctype cộng mọi trường tự thêm,
 * qua chính phép bo_cuc/gia_tri/tom_bang của máy chủ. Vì vậy thêm ô trên Desk
 * là bộ ca này tự thấy ô đó trên app.
 *
 * Mỗi ca bấm đúng chuỗi thao tác của quản trị: mở màn, mở tab, bật tắt, gõ, đổi
 * khoá, thêm nhóm Zalo, bấm Lưu. Không gọi thêm hàm nào "cho chắc" (điều 15).
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/cai_dat_loi_570.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var cp = require('child_process');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
var SRC = fs.readFileSync(path.join(BEP, '51-cai-dat-loi.js'), 'utf8');
var CHUNG = fs.readFileSync(path.join(GOC, 'vagabond', 'public', 'js', 'cai_dat_loi_chung.js'), 'utf8');

/* Kết quả lay() dựng bằng chính phép của máy chủ, trên dữ liệu mẫu có đủ hình dạng. */
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
    'doc.update({"pancake_api_key": "KHOA-PANCAKE-THAT", "sepay_bat": 0, "sepay_khoa": "KHOA-SEPAY-THAT",',
    '  "tk_hoan_tien": "MB - TV", "tu_xuat_hddt": 1, "ngan_hang_bin": "970422", "ngan_hang_hien_thi": "MB Bank", "diem_chu_ky": "Cuon chieu",',
    '  "zalo_chat_moi": json.dumps([{"chat_id": "g-777", "ten": "Nhóm Bếp", "loai": "GROUP"}, {"chat_id": "u-1", "ten": "Anh A", "loai": "USER"}]),',
    '  "vgb_diem_ban": json.dumps([{"ma": "Q1", "ten": "Quận 1", "co_quay": 1}])})',
    'cot = t._cot_zalo()',
    'dong = [{"name": "r1", "ten_nhom": "Vận hành", "chat_id": "g-1", "loai_tin": "thong_bao, canh_bao", "chu_de": "", "im_tu": "22:00", "im_den": "07:00", "bat": 1}]',
    'ra = {"bo_cuc": c.bo_cuc(tr), "gia_tri": c.gia_tri(tr, doc), "modified": "2026-10-04 09:00:00.000001",',
    '  "bang": {"zalo_nhom": {"cot": c.tom_bang(cot), "dong": [dict(c.gia_tri(cot, r), name=r["name"]) for r in dong],',
    '    "ghi_qua_hop_chon": list(c.GHI_QUA_HOP_CHON["zalo_nhom"])}}}',
    '# v606: bảng Bot thêm dựng bằng chính phép máy chủ trên JSON thật của doctype con.',
    'import os',
    'cot_bot = json.load(open(os.path.join(sys.argv[1], "vagabond", "vagabond", "doctype", "vagabond_bot_zalo", "vagabond_bot_zalo.json"), encoding="utf-8"))["fields"]',
    'bot = [{"name": "b2", "ma_bot": "2", "ten_bot": "Bot Bếp", "co_token": 1, "trang_thai": "Đã xác minh đường nhận lúc 20/10 10:00."}]',
    'ra["bang"]["zalo_bot_phu"] = {"cot": c.tom_bang(cot_bot), "dong": [dict(c.gia_tri(cot_bot, r), name=r["name"]) for r in bot],',
    '  "ghi_qua_hop_chon": list(c.GHI_QUA_HOP_CHON.get("zalo_bot_phu", ()))}',
    '# v591: danh sách nhóm của hộp chọn dựng bằng chính phép máy chủ trên cùng dữ liệu.',
    'u = sys.modules["frappe"].utils',
    'u.get_url = getattr(u, "get_url", None) or (lambda *a, **k: "https://vagabond.test")',
    'from vagabond import kenh_zalo as kz',
    'ra["nhom_bot"] = kz.ds_nhom_chon(json.loads(doc["zalo_chat_moi"]), dong)',
    'sys.stdout.write(json.dumps(ra, ensure_ascii=False, default=str))',
  ].join('\n');
  return JSON.parse(cp.execFileSync('python3', ['-c', py, GOC], { encoding: 'utf8', maxBuffer: 1 << 26 }));
}
var LAY = layThat();
var NGAN_HANG = [
  { bin: '970422', ten: 'MB Bank', ma: 'MB' }, { bin: '970405', ten: 'Agribank', ma: 'VBA' },
  { bin: '970436', ten: 'Vietcombank', ma: 'VCB' },
];

function dungMan() {
  var tai = dg.taiLieuGia();
  tai.head = new dg.ElementGia('head');
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);
  var goi = [], toastDs = [], sheetDs = [], diToi = [];
  var S = { stack: [] };
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, parseInt: parseInt, isNaN: isNaN, setTimeout: setTimeout, APPVER: 570, S: S,
    frame: function (t, html, opt) {
      khung.innerHTML = html + ((opt && opt.footer) || '');
      khung.onclick = null; khung.oninput = null;
      that._t = t; return khung;
    },
    go: function (fn) { S.stack.push(fn); fn(); },
    back: function () { S.stack.pop(); var top = S.stack[S.stack.length - 1]; if (top) top(); },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: ts });
      if (duong === 'vagabond.cai_dat_loi.lay') {
        // v606: _loiLay giả lỗi mạng ở lần đọc lại SAU lần mở đầu tiên.
        if (that._loiLay && goi.filter(function (x) { return x.duong === duong; }).length > 1) return Promise.reject(new Error('Mất mạng'));
        return Promise.resolve(JSON.parse(JSON.stringify(that._lay || LAY)));
      }
      // v606: máy chủ của bot Zalo thêm. luu_bot cấp số 3 cho bot mới, giữ số cũ khi đổi.
      if (duong === 'vagabond.kenh_zalo.luu_bot') {
        if (that._loiBot) return Promise.reject(new Error(that._loiBot));
        return Promise.resolve({ ma_bot: ts.ma || '3', ten: ts.ten || 'Bot Zalo' });
      }
      if (duong === 'vagabond.kenh_zalo.dang_ky_webhook') return Promise.resolve({ ok: 1, loi_nhan: 'Đã nối bot số ' + ts.bot + '.' });
      // v616: thử kết nối GreenSM. _gsm là phản hồi máy chủ, _gsmLoi là câu lỗi máy chủ ném.
      if (duong === 'vagabond.greensm.thu_ket_noi') {
        if (that._gsmLoi) return Promise.reject(new Error(that._gsmLoi));
        return Promise.resolve(JSON.parse(JSON.stringify(that._gsm || { ok: 1, buoc: [] })));
      }
      if (duong === 'vagabond.tai_khoan.danh_sach') return Promise.resolve({ ngan_hang: NGAN_HANG });
      if (duong === 'vagabond.cai_dat_loi.tim_lien_ket') return Promise.resolve(['Kho A', 'Kho B']);
      if (duong === 'vagabond.kenh_zalo.nhom_da_nhan_bot') return Promise.resolve(JSON.parse(JSON.stringify(that._nhomBot || LAY.nhom_bot)));
      if (duong === 'vagabond.cai_dat_loi.luu') {
        var d = JSON.parse(JSON.stringify(LAY));
        d.modified = '2026-10-04 09:05:00';
        return Promise.resolve(d);
      }
      return Promise.reject(new Error('api la: ' + duong));
    },
    sheet: function (title, items, cur, onPick) { sheetDs.push({ title: title, items: items, cur: cur, onPick: onPick }); },
    confirmSheet: function () { return Promise.resolve(true); },
    toast: function (m) { toastDs.push(m); },
    inNapJs: function () { return Promise.resolve(); },
    vgbGo: function (k) { diToi.push(k); },
    h: function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); },
  };
  that.window = that;
  that.globalThis = that;
  vm.runInNewContext(CHUNG, that, { filename: 'cai_dat_loi_chung.js' });
  vm.runInNewContext(SRC, that, { filename: '51-cai-dat-loi.js' });
  return { g: that, tai: tai, khung: khung, goi: goi, toast: toastDs, sheet: sheetDs, diToi: diToi, S: S };
}

var ket = { dat: 0, hong: 0, loi: [] };
function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) {
  var x = JSON.stringify(a), y = JSON.stringify(b);
  if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y);
}
function tick() { return new Promise(function (r) { setTimeout(r, 5); }); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; ket.loi.push(ten); console.log('  HONG  ' + ten + '\n        ' + e.message); }
}
function tim(m, chon) { return m.khung.querySelectorAll(chon); }
function mot(m, chon) { var r = tim(m, chon); if (r.length !== 1) throw new Error('mong 1 phan tu ' + chon + ', co ' + r.length); return r[0]; }
function bam(m, el) { m.khung.onclick({ target: el }); }
function nut(m) { return m.tai.getElementById('cdlLuu'); }
function chu(el) {
  var s = el._chu || '';
  (el.children || []).forEach(function (c) { s += chu(c); });
  return s;
}
async function moMan() {
  var m = dungMan();
  m.g.go(m.g.scrCaiDatLoi);
  await tick();
  return m;
}
function moTab(m, fn) { bam(m, mot(m, '[data-cdltab="' + fn + '"]')); }

(async function () {
  console.log('Cài đặt lõi và API v570: màn app');

  await ca('mở màn: đọc máy chủ đúng một lần, hiện 8 tab như Desk, nút Lưu tắt', async function () {
    var m = await moMan();
    bang('gọi lay một lần', m.goi.map(function (x) { return x.duong; }), ['vagabond.cai_dat_loi.lay']);
    bang('tiêu đề', m.g._t, 'Cài đặt lõi và API');
    bang('tab trên app trùng tab máy chủ gửi', tim(m, '[data-cdltab]').map(function (e) { return e.getAttribute('data-cdltab'); }),
      LAY.bo_cuc.map(function (t) { return t.fn; }));
    bang('đủ 8 tab', tim(m, '[data-cdltab]').length, 8);
    dung('nút Lưu tắt khi chưa đổi gì', nut(m).hasAttribute('disabled'));
    dung('có chip tình trạng kết nối', tim(m, '[data-cdltoi]').length >= 10);
  });

  await ca('khoá bí mật không có trên máy: không chữ nào của khoá lọt vào dữ liệu hay màn hình', async function () {
    var m = await moMan();
    var s = JSON.stringify(m.g.CDL.d);
    dung('dữ liệu máy chủ không chứa khoá', s.indexOf('KHOA-PANCAKE-THAT') < 0 && s.indexOf('KHOA-SEPAY-THAT') < 0);
    var tab = LAY.bo_cuc.filter(function (t) { return t.muc.some(function (mu) { return mu.o.some(function (o) { return o.fn === 'pancake_api_key'; }); }); })[0];
    moTab(m, tab.fn);
    var o = mot(m, '#cdl-o-pancake_api_key');
    dung('chip Đã khai', chu(o).indexOf('Đã khai') >= 0);
    dung('không có ô nhập lộ giá trị', o.querySelectorAll('[data-cdlo]').length === 0);
  });

  await ca('bật công tắc rồi lưu: chỉ gửi đúng ô đã đổi, kèm mốc modified', async function () {
    var m = await moMan();
    moTab(m, 'tab_ke_toan');
    var tg = mot(m, '[data-cdlbat="sepay_bat"]');
    bam(m, tg);
    bang('nút đếm 1 thay đổi', chu(nut(m)), 'Lưu 1 thay đổi');
    bam(m, mot(m, '[data-cdlbat="sepay_bat"]'));
    bang('bấm lại về như cũ thì không còn thay đổi', chu(nut(m)), 'Chưa có thay đổi');
    bam(m, mot(m, '[data-cdlbat="sepay_bat"]'));
    await m.g.cdlLuu();
    var g = m.goi.filter(function (x) { return x.duong === 'vagabond.cai_dat_loi.luu'; });
    bang('gọi lưu một lần', g.length, 1);
    bang('chỉ gửi ô đã đổi', JSON.parse(g[0].ts.thay), { sepay_bat: 1 });
    bang('không gỡ khoá nào', JSON.parse(g[0].ts.xoa_khoa), []);
    bang('gửi kèm mốc modified lúc mở', g[0].ts.modified, LAY.modified);
    dung('không gửi bảng khi bảng không đổi', !('bang' in g[0].ts));
    bang('lưu xong nhận mốc mới', m.g.CDL.d.modified, '2026-10-04 09:05:00');
    dung('báo đã lưu', m.toast.indexOf('Đã lưu 1 thay đổi') >= 0);
  });

  await ca('gõ chữ vào một ô: đếm thay đổi, gõ trả về như cũ thì hết', async function () {
    var m = await moMan();
    var o = LAY.bo_cuc.map(function (t) { return { t: t, o: [].concat.apply([], t.muc.map(function (mu) { return mu.o; })).filter(function (x) { return x.kieu === 'Data' && !x.chi_doc; })[0] }; })
      .filter(function (x) { return x.o; })[0];
    moTab(m, o.t.fn);
    var inp = mot(m, '[data-cdlo="' + o.o.fn + '"]');
    inp.value = 'gia tri moi';
    m.khung.oninput({ target: inp });
    bang('1 thay đổi', chu(nut(m)), 'Lưu 1 thay đổi');
    inp.value = LAY.gia_tri[o.o.fn] == null ? '' : String(LAY.gia_tri[o.o.fn]);
    m.khung.oninput({ target: inp });
    bang('gõ về như cũ thì hết thay đổi', chu(nut(m)), 'Chưa có thay đổi');
  });

  await ca('đổi khoá: bấm Đổi khoá mới hiện ô nhập; để trống thì KHÔNG gửi gì', async function () {
    var m = await moMan();
    moTab(m, 'tab_ke_toan');
    bam(m, mot(m, '[data-cdldoikhoa="sepay_khoa"]'));
    var inp = mot(m, '[data-cdlo="sepay_khoa"]');
    bang('ô nhập kiểu mật khẩu', inp.getAttribute('type'), 'password');
    bang('ô nhập trống, không đổ khoá cũ vào', inp.value, '');
    inp.value = '   ';
    m.khung.oninput({ target: inp });
    bang('khoá toàn khoảng trắng không tính là đổi', chu(nut(m)), 'Chưa có thay đổi');
    inp.value = 'khoa-moi-1';
    m.khung.oninput({ target: inp });
    await m.g.cdlLuu();
    var g = m.goi.filter(function (x) { return x.duong === 'vagabond.cai_dat_loi.luu'; })[0];
    bang('gửi đúng khoá mới', JSON.parse(g.ts.thay), { sepay_khoa: 'khoa-moi-1' });
  });

  await ca('gỡ khoá: hỏi lại rồi gửi tên ô trong xoa_khoa, không gửi giá trị', async function () {
    var m = await moMan();
    moTab(m, 'tab_ke_toan');
    bam(m, mot(m, '[data-cdlgokhoa="sepay_khoa"]'));
    await tick();
    bang('1 thay đổi', chu(nut(m)), 'Lưu 1 thay đổi');
    dung('chip chuyển Chưa khai', chu(mot(m, '#cdl-o-sepay_khoa')).indexOf('Chưa khai') >= 0);
    await m.g.cdlLuu();
    var g = m.goi.filter(function (x) { return x.duong === 'vagabond.cai_dat_loi.luu'; })[0];
    bang('xoa_khoa', JSON.parse(g.ts.xoa_khoa), ['sepay_khoa']);
    bang('không gửi giá trị khoá', JSON.parse(g.ts.thay), {});
  });

  await ca('chọn ngân hàng: lấy danh mục máy chủ, ghi cả BIN lẫn tên hiển thị', async function () {
    var m = await moMan();
    var tab = LAY.bo_cuc.filter(function (t) { return t.muc.some(function (mu) { return mu.o.some(function (o) { return o.fn === 'ngan_hang_bin'; }); }); })[0];
    moTab(m, tab.fn);
    bam(m, mot(m, '[data-cdlnganhang]'));
    await tick();
    bang('mở hộp chọn từ danh mục máy chủ', m.sheet[0].items.map(function (x) { return x.value; }), ['970422', '970405', '970436']);
    dung('mỗi dòng có mã và BIN', m.sheet[0].items[1].phu === 'VBA · BIN 970405');
    m.sheet[0].onPick(m.sheet[0].items[1]);
    bang('ghi đủ hai ô', m.g.CDL.thay, { ngan_hang_bin: '970405', ngan_hang_hien_thi: 'Agribank' });
    dung('chip hiện Agribank', chu(mot(m, '#cdl-o-ngan_hang_bin')).indexOf('Agribank') >= 0);
  });

  await ca('chip chọn: bấm Ngày kỷ niệm thì lưu mã Ngay ky niem', async function () {
    var m = await moMan();
    var tab = LAY.bo_cuc.filter(function (t) { return t.muc.some(function (mu) { return mu.o.some(function (o) { return o.fn === 'diem_chu_ky'; }); }); })[0];
    moTab(m, tab.fn);
    var b = tim(m, '[data-cdlchon="diem_chu_ky"]').filter(function (e) { return e.getAttribute('data-v') === 'Ngay ky niem'; })[0];
    dung('có chip Ngày kỷ niệm', b && chu(b) === 'Ngày kỷ niệm');
    bam(m, b);
    bang('lưu mã', m.g.CDL.thay, { diem_chu_ky: 'Ngay ky niem' });
  });

  await ca('Zalo: thêm nhóm, chọn nhóm đã nhắn bot, tích loại tin có giải thích, lưu gửi cả bảng', async function () {
    var m = await moMan();
    moTab(m, 'tab_tin_nhan');
    bang('đang có 1 nhóm', tim(m, '[data-cdldong]').length, 1);
    bam(m, mot(m, '[data-cdlbangthem="zalo_nhom"]'));
    bang('màn thêm nhóm', m.g._t, 'Thêm nhóm nhận tin');
    bam(m, mot(m, '[data-cdldnhom]'));
    await tick();
    bang('hộp chọn chỉ có nhóm GROUP', m.sheet[0].items.map(function (x) { return x.value; }), ['g-777']);
    bang('gọi nhóm bằng mã nhóm máy chủ tính, không bằng tên người nhắc', m.sheet[0].items[0].label, 'Nhóm Zalo mã ' + LAY.nhom_bot[0].ma);
    dung('không hiện tên "Nhóm Bếp" của bản tin cũ làm tên nhóm', m.sheet[0].items[0].label.indexOf('Nhóm Bếp') < 0);
    m.sheet[0].onPick(m.sheet[0].items[0]);
    // v591: chọn nhóm không còn tự lấy tên người nhắc bot làm tên nhóm; quản trị tự đặt.
    var oTen = m.khung.querySelectorAll('[data-cdld]').filter(function (e) { return e.getAttribute('data-cdld') === 'ten_nhom'; })[0];
    bang('tên nhóm vẫn trống sau khi chọn', oTen.value || '', '');
    oTen.value = 'Nhóm Bếp';
    m.khung.oninput({ target: oTen });
    var r = m.khung.querySelectorAll('[data-cdldchon]').filter(function (e) { return e.getAttribute('data-cdldchon') === 'loai_tin'; })[0];
    bam(m, r);
    var ov = m.tai.body.children[m.tai.body.children.length - 1];
    var box = ov.children[0];
    var dong = box.querySelectorAll('[data-cdlz]');
    bang('đủ năm loại tin', dong.length, 5);
    dong.forEach(function (d) {
      dung('loại ' + d.getAttribute('data-cdlz') + ' có dòng giải thích', chu(d.querySelectorAll('.cdl-mo')[0] || {}).length > 10);
    });
    box.onclick({ target: dong.filter(function (d) { return d.getAttribute('data-cdlz') === 'canh_bao'; })[0] });
    box.onclick({ target: box.querySelectorAll('[data-cdlzxong]')[0] });
    bam(m, mot(m, '#cdlDongXong'));
    bang('quay lại tab, có 2 nhóm', tim(m, '[data-cdldong]').length, 2);
    bang('1 thay đổi (bảng)', chu(nut(m)), 'Lưu 1 thay đổi');
    await m.g.cdlLuu();
    var g = m.goi.filter(function (x) { return x.duong === 'vagabond.cai_dat_loi.luu'; })[0];
    var b = JSON.parse(g.ts.bang).zalo_nhom;
    bang('gửi cả hai dòng', b.length, 2);
    bang('dòng cũ giữ name để máy chủ gộp', b[0].name, 'r1');
    bang('dòng mới', { ten: b[1].ten_nhom, chat: b[1].chat_id, lt: b[1].loai_tin, bat: b[1].bat }, { ten: 'Nhóm Bếp', chat: 'g-777', lt: 'canh_bao', bat: 1 });
  });

  // v579: anh Việt 06/10/2026 hỏi có nút gửi thử vào nhóm Zalo không. Desk và app cùng có.
  await ca('Zalo v579: thẻ nhóm có nút Gửi thử, bấm thì gửi đúng mã nhóm đó và không mở màn sửa', async function () {
    var m = await moMan();
    moTab(m, 'tab_tin_nhan');
    var b = tim(m, '[data-cdlguithu]');
    bang('một nút Gửi thử cho nhóm có mã chat', b.length, 1);
    bam(m, b[0]);
    await new Promise(function (ok) { setTimeout(ok, 0); });
    var g = m.goi.filter(function (x) { return x.duong === 'vagabond.kenh_zalo.gui_thu'; });
    bang('gọi gửi thử đúng mã nhóm', g.map(function (x) { return x.ts.chat_id; }), ['g-1']);
    dung('không mở màn sửa nhóm', m.g._t !== 'Sửa nhóm nhận tin');
  });

  // v591: anh Việt 12/10/2026 thêm nhóm Bán hàng nhưng hộp chọn chỉ có một dòng "Viet Nguyen".
  await ca('Zalo v591: nhóm vừa nhắc bot SAU khi mở màn vẫn hiện, vì hộp chọn hỏi máy chủ mỗi lần bấm', async function () {
    var m = await moMan();
    moTab(m, 'tab_tin_nhan');
    m.g._nhomBot = [
      { chat_id: 'zgr-50abae45f4271d794436', ma: '4436', luc: '2026-10-12 18:56', nguoi: 'Viet Nguyen', dang_gan: [] },
      { chat_id: 'g-777', ma: 'G-777', luc: '2026-10-04 12:23', nguoi: 'Viet Nguyen', dang_gan: [] },
    ];
    bam(m, mot(m, '[data-cdlbangthem="zalo_nhom"]'));
    bam(m, mot(m, '[data-cdldnhom]'));
    await tick();
    bang('có hỏi máy chủ', m.goi.filter(function (x) { return x.duong === 'vagabond.kenh_zalo.nhom_da_nhan_bot'; }).length, 1);
    bang('đủ hai nhóm, nhóm mới đứng đầu', m.sheet[0].items.map(function (x) { return x.label; }), ['Nhóm Zalo mã 4436', 'Nhóm Zalo mã -777']);
    dung('dòng phụ có giờ nhắc bot', m.sheet[0].items[0].phu.indexOf('18:56 ngày 12/10') >= 0);
    m.sheet[0].onPick(m.sheet[0].items[0]);
    dung('màn sửa hiện mã nhóm đã chọn', chu(m.khung).indexOf('Nhóm Zalo mã 4436') >= 0);
  });

  await ca('Zalo v591: nhóm đã gán cho dòng khác hiện "đang dùng" và không chọn được lần nữa', async function () {
    var m = await moMan();
    moTab(m, 'tab_tin_nhan');
    // Bản CDL mở từ trước chưa có dòng này; chỉ phản hồi mới của máy chủ biết
    // một phiên khác vừa gán nhóm cho "Kế toán mới".
    m.g._nhomBot = [{ chat_id: 'g-1', ma: 'G-1', luc: '2026-10-04 12:23', nguoi: 'Viet Nguyen', dang_gan: ['Kế toán mới'] }];
    bam(m, mot(m, '[data-cdlbangthem="zalo_nhom"]'));
    bam(m, mot(m, '[data-cdldnhom]'));
    await tick();
    var it = m.sheet[0].items[0];
    bang('nhãn báo đang dùng', it.label, 'Nhóm Zalo mã G-1 (đang dùng)');
    dung('dòng phụ nói đúng dòng máy chủ vừa báo', it.phu.indexOf('Đang gán cho: Kế toán mới') >= 0);
    m.sheet[0].onPick(it);
    dung('báo không chọn được', m.toast.some(function (t) { return t.indexOf('đang gán cho Kế toán mới') >= 0; }));
    dung('màn thêm vẫn chưa có nhóm', chu(m.khung).indexOf('Chưa chọn') >= 0);
  });

  await ca('Zalo v591: mở lại chính dòng đang dùng nhóm thì nhóm đó không bị coi là "đang dùng"', async function () {
    var m = await moMan();
    moTab(m, 'tab_tin_nhan');
    m.g._nhomBot = [{ chat_id: 'g-1', ma: 'G-1', luc: '2026-10-04 12:23', nguoi: 'Viet Nguyen', dang_gan: ['Vận hành'] }];
    bam(m, mot(m, '[data-cdldong]'));
    bam(m, mot(m, '[data-cdldnhom]'));
    await tick();
    bang('không gắn nhãn đang dùng', m.sheet[0].items[0].label, 'Nhóm Zalo mã G-1');
  });

  await ca('Zalo: thêm nhóm mà chưa đặt tên thì không cho Xong', async function () {
    var m = await moMan();
    moTab(m, 'tab_tin_nhan');
    bam(m, mot(m, '[data-cdlbangthem="zalo_nhom"]'));
    bam(m, mot(m, '#cdlDongXong'));
    dung('báo đặt tên', m.toast.some(function (t) { return t.indexOf('Đặt tên nhóm') >= 0; }));
    bang('vẫn ở màn thêm', m.g._t, 'Thêm nhóm nhận tin');
    bang('không tính thay đổi', m.g.cdlSoThay(), 0);
  });

  await ca('tab Dữ liệu app tự ghi: hiện thẻ tóm tắt, bấm Sửa ở màn riêng mở đúng màn app', async function () {
    var m = await moMan();
    moTab(m, 'tab_du_lieu_app');
    dung('có thẻ Điểm bán', chu(m.khung).indexOf('Điểm bán') >= 0 && chu(m.khung).indexOf('Quận 1') >= 0);
    var b = tim(m, '[data-cdlman="CDDB"]');
    dung('có nút mở màn Điểm bán', b.length >= 1);
    bam(m, b[0]);
    bang('mở màn CDDB', m.diToi, ['CDDB']);
  });

  await ca('Codex 91e8e8b: còn thay đổi Cài đặt lõi thì bấm "Sửa ở màn riêng" phải HỎI; ở lại thì giữ nguyên, không mở màn', async function () {
    // Màn riêng (Máy in, Mẫu in...) dùng chung ô S.chuaLuu và xoá nó khi nạp xong, nên
    // mở màn riêng khi còn thay đổi thì nút nhà hay Back sau đó bỏ thay đổi im lặng.
    var m = await moMan();
    var hoi = [];
    m.g.confirmSheet = function (t, c) { hoi.push(t + ': ' + c); return Promise.resolve(false); };
    moTab(m, 'tab_ke_toan');
    bam(m, mot(m, '[data-cdlbat="sepay_bat"]'));
    m.g.back();
    moTab(m, 'tab_du_lieu_app');
    bam(m, tim(m, '[data-cdlman="CDDB"]')[0]);
    await tick();
    bang('hỏi một lần', hoi.length, 1);
    dung('câu hỏi nói còn thay đổi chưa lưu', hoi[0].indexOf('Còn 1 thay đổi') >= 0);
    bang('không mở màn riêng', m.diToi, []);
    bang('thay đổi còn nguyên', m.g.cdlSoThay(), 1);
  });

  await ca('Còn thay đổi, chọn bỏ thay đổi rồi mở: thay đổi bỏ hết, câu hỏi xoá, mới mở màn riêng', async function () {
    var m = await moMan();
    m.g.confirmSheet = function () { return Promise.resolve(true); };
    moTab(m, 'tab_ke_toan');
    bam(m, mot(m, '[data-cdlbat="sepay_bat"]'));
    m.g.back();
    moTab(m, 'tab_du_lieu_app');
    bam(m, tim(m, '[data-cdlman="CDDB"]')[0]);
    await tick();
    bang('bỏ hết thay đổi', m.g.cdlSoThay(), 0);
    bang('không còn câu hỏi của Cài đặt lõi', m.S.chuaLuu, '');
    bang('mở màn CDDB', m.diToi, ['CDDB']);
  });

  await ca('ô tìm: gõ "ngan hang" không dấu ra ô ngân hàng, bấm kết quả mở đúng tab và tô sáng ô', async function () {
    var m = await moMan();
    var inp = mot(m, '#cdlTim');
    inp.value = 'ngan hang';
    m.khung.oninput({ target: inp });
    var kq = tim(m, '[data-cdlkq]');
    dung('có kết quả', kq.length >= 1);
    var o = kq.filter(function (e) { return e.getAttribute('data-cdlkq') === 'ngan_hang_bin'; })[0];
    dung('có ô ngan_hang_bin', !!o);
    bam(m, o);
    dung('ô được tô sáng', String(mot(m, '#cdl-o-ngan_hang_bin').getAttribute('class') || '').indexOf('cdl-sang') >= 0);
  });

  await ca('còn thay đổi chưa lưu thì mở lại màn KHÔNG đọc lại đè mất', async function () {
    var m = await moMan();
    moTab(m, 'tab_ke_toan');
    bam(m, mot(m, '[data-cdlbat="sepay_bat"]'));
    m.g.back();
    m.g.go(m.g.scrCaiDatLoi);
    await tick();
    bang('chỉ đọc máy chủ một lần', m.goi.filter(function (x) { return x.duong === 'vagabond.cai_dat_loi.lay'; }).length, 1);
    bang('thay đổi còn nguyên', m.g.CDL.thay, { sepay_bat: 1 });
  });

  await ca('máy chủ từ chối (ví dụ trang bị sửa ở nơi khác): giữ nguyên thay đổi, báo lỗi', async function () {
    var m = await moMan();
    m.g.api = function () { return Promise.reject(new Error('Cài đặt vừa được sửa ở nơi khác<br>Tải lại')); };
    moTab(m, 'tab_ke_toan');
    bam(m, mot(m, '[data-cdlbat="sepay_bat"]'));
    await m.g.cdlLuu();
    bang('thay đổi còn', m.g.CDL.thay, { sepay_bat: 1 });
    dung('báo lỗi không còn thẻ br', m.toast.some(function (t) { return t.indexOf('sửa ở nơi khác') >= 0 && t.indexOf('<br') < 0; }));
    bang('nút Lưu bật lại', chu(nut(m)), 'Lưu 1 thay đổi');
  });

  await ca('Codex #439 V2: ô Liên kết không bắt buộc bỏ chọn được, lưu gửi chuỗi rỗng', async function () {
    var m = await moMan();
    var tab = LAY.bo_cuc.filter(function (t) { return t.muc.some(function (mu) { return mu.o.some(function (o) { return o.fn === 'tk_hoan_tien'; }); }); })[0];
    moTab(m, tab.fn);
    var b = mot(m, '[data-cdlbo="tk_hoan_tien"]');
    dung('nút Bỏ chọn', chu(b) === 'Bỏ chọn');
    bam(m, b);
    bang('ghi thay đổi về rỗng', m.g.CDL.thay, { tk_hoan_tien: '' });
    bang('đã bỏ thì không còn nút Bỏ chọn', tim(m, '[data-cdlbo="tk_hoan_tien"]').length, 0);
    await m.g.cdlLuu();
    var g = m.goi.filter(function (x) { return x.duong === 'vagabond.cai_dat_loi.luu'; })[0];
    bang('lưu gửi chuỗi rỗng', JSON.parse(g.ts.thay), { tk_hoan_tien: '' });
  });

  /* ---------- v596: anh Việt duyệt mockup 15/10/2026 ---------- */
  // Dữ liệu thật của site ngày 15/10: Ahamove khai đủ nhưng trỏ máy chủ chạy thử.
  async function voiAhamoveThu(ham) {
    var cu = JSON.parse(JSON.stringify(LAY.gia_tri));
    LAY.gia_tri.ahamove_api_key = { da_khai: true };
    LAY.gia_tri.ahamove_mobile = '0900000000';
    LAY.gia_tri.ahamove_base = 'https://apistg.ahamove.com';
    try { await ham(); } finally { LAY.gia_tri = cu; }
  }
  function tomTatMay(m) { return m.g.VGB_CD.tongHop(m.g.VGB_CD.tinhTrang(m.g.cdlDoc())); }

  await ca('v596 tổng quan: câu tóm tắt đúng số máy tính, thanh màu, không còn "mục · ô"', async function () {
    var m = await moMan();
    var th = tomTatMay(m);
    dung('câu tóm tắt có trên màn', chu(mot(m, '#cdlTomTat')).indexOf(th.cau) >= 0);
    var khuc = mot(m, '#cdlTomTat').querySelectorAll('[data-mau]');
    bang('một khúc mỗi màu khác 0', khuc.map(function (e) { return e.getAttribute('data-mau'); }),
      ['ok', 'no', 'off', 'err'].filter(function (k) { return th.dem[k]; }));
    dung('không còn dòng phụ kiểu "3 mục · 18 ô"', !/\d+ mục · \d+ ô/.test(chu(m.khung)));
  });

  await ca('v596 tổng quan: dòng nhóm không dùng lớp .card (lớp này làm vỡ thành ô to căn giữa)', async function () {
    var m = await moMan();
    var dong = tim(m, '[data-cdltab]');
    bang('8 dòng nhóm', dong.length, 8);
    dong.forEach(function (d) {
      var lop = String(d.getAttribute('class') || '').split(' ');
      dung(d.getAttribute('data-cdltab') + ' không mang lớp card', lop.indexOf('card') < 0 && lop.indexOf('cdl-nhom') >= 0);
      dung(d.getAttribute('data-cdltab') + ' có dòng nói nhóm chứa gì', chu(d.querySelectorAll('small')[0] || {}).length > 8);
    });
    dung('khối danh sách không phải .card', String(mot(m, '#cdlNhom').getAttribute('class')).split(' ').indexOf('card') < 0);
  });

  await ca('v596 cần xử lý: Ahamove chạy thử là thẻ đỏ nói hậu quả; bấm Sửa mở Giao hàng, tô và nói cách sửa đúng ô API', async function () {
    await voiAhamoveThu(async function () {
      var m = await moMan();
      var the = tim(m, '.cdl-viec.err');
      bang('một thẻ đỏ', the.length, 1);
      dung('nói Ahamove và hậu quả', chu(the[0]).indexOf('Ahamove: đang trỏ máy chủ chạy thử') >= 0 && chu(the[0]).indexOf('phí giao') >= 0);
      bang('nhãn nhóm Giao hàng báo lỗi', chu(mot(m, '[data-cdltab="tab_giao_hang"]').querySelectorAll('.cdl-nhan')[0]), '1 lỗi');
      bam(m, the[0]);
      bang('mở nhóm Giao hàng', m.g._t, 'Giao hàng');
      var o = mot(m, '#cdl-o-ahamove_base');
      dung('ô API được tô sáng', String(o.getAttribute('class')).indexOf('cdl-sang') >= 0);
      dung('ô API mang dấu lỗi', o.getAttribute('data-cdlloi') === '1');
      dung('câu sửa ngay dưới ô', chu(o.querySelectorAll('.cdl-loi')[0] || {}).indexOf('https://partner-api.ahamove.com') >= 0);
      var muc = tim(m, '[data-cdlmuc]').filter(function (x) { return x.querySelectorAll('#cdl-o-ahamove_base').length; })[0];
      bang('mục Ahamove gắn nhãn Lỗi', chu(muc.querySelectorAll('.cdl-nhan')[0]), 'Lỗi');
      var inp = mot(m, '[data-cdlo="ahamove_base"]');
      inp.value = 'https://partner-api.ahamove.com';
      m.khung.oninput({ target: inp });
      bang('gõ đúng máy chủ thật thì câu đỏ dưới ô mất ngay', o.querySelectorAll('.cdl-loi').length, 0);
      dung('và bỏ dấu lỗi của ô', !o.hasAttribute('data-cdlloi'));
      inp.value = 'https://apistg.ahamove.com';
      m.khung.oninput({ target: inp });
      bang('gõ lại máy chạy thử thì câu đỏ hiện lại đúng một câu', o.querySelectorAll('.cdl-loi').length, 1);
      inp.value = 'https://partner-api.ahamove.com';
      m.khung.oninput({ target: inp });
      m.g.back();
      bang('sửa xong về tổng quan thì hết thẻ đỏ', tim(m, '.cdl-viec.err').length, 0);
    });
  });

  await ca('v596 mục có ô lỗi luôn mở sẵn, kể cả mục thu gọn, khi mở nhóm từ danh sách', async function () {
    await voiAhamoveThu(async function () {
      var cu = JSON.parse(JSON.stringify(LAY.bo_cuc));
      LAY.bo_cuc.forEach(function (t) { t.muc.forEach(function (mu) { if (mu.o.some(function (o) { return o.fn === 'ahamove_base'; })) mu.gon = 1; }); });
      try {
        var m = await moMan();
        moTab(m, 'tab_giao_hang');
        bang('ô API hiện ngay, không phải bấm mở mục', tim(m, '#cdl-o-ahamove_base').length, 1);
      } finally { LAY.bo_cuc = cu; }
    });
  });

  await ca('v596 cần xử lý: khai rồi mà đang tắt là thẻ vàng, bấm tới đúng công tắc', async function () {
    var m = await moMan();
    var the = tim(m, '.cdl-viec.off').filter(function (e) { return chu(e).indexOf('SePay') >= 0; });
    bang('một thẻ vàng SePay (đã khai khoá, công tắc tắt)', the.length, 1);
    bam(m, the[0]);
    dung('tô sáng công tắc SePay', String(mot(m, '#cdl-o-sepay_bat').getAttribute('class')).indexOf('cdl-sang') >= 0);
  });

  await ca('v596 cần xử lý: chưa khai gom một thẻ; bấm tên WhatsApp tới đúng ô còn thiếu đầu tiên', async function () {
    var m = await moMan();
    var th = tomTatMay(m);
    var chua = th.can.filter(function (t) { return t.trang === 'no'; });
    var theChua = tim(m, '.cdl-viec').filter(function (e) { return chu(e).indexOf('kết nối chưa khai') >= 0; });
    bang('một thẻ gom chưa khai', theChua.length, 1);
    var c = theChua[0].querySelectorAll('.cdl-chip');
    bang('mỗi kết nối chưa khai một chip', c.length, chua.length);
    var wa = c.filter(function (e) { return chu(e) === 'WhatsApp'; })[0];
    bam(m, wa);
    dung('tô sáng ô Mã số điện thoại WhatsApp', String(mot(m, '#cdl-o-wa_phone_id').getAttribute('class')).indexOf('cdl-sang') >= 0);
  });

  await ca('v596 nhãn nhóm: nhóm không có kết nối nào thì không tự nhận "Ổn"', async function () {
    var m = await moMan();
    bang('Khách hàng & điểm không có nhãn', mot(m, '[data-cdltab="tab_khach_hang"]').querySelectorAll('.cdl-nhan').length, 0);
  });

  await ca('v596 thanh Lưu: ẩn khi chưa sửa, hiện khi sửa, ẩn lại khi trả về như cũ', async function () {
    var m = await moMan();
    bang('tổng quan chưa sửa: ẩn', mot(m, '#cdlChan').style.display, 'none');
    moTab(m, 'tab_ke_toan');
    bang('vào nhóm chưa sửa: ẩn', mot(m, '#cdlChan').style.display, 'none');
    bam(m, mot(m, '[data-cdlbat="sepay_bat"]'));
    bang('bật công tắc: hiện', mot(m, '#cdlChan').style.display, '');
    var inp = tim(m, '[data-cdlo]')[0];
    var cu = inp.value;
    inp.value = cu + 'x'; m.khung.oninput({ target: inp });
    bang('gõ thêm: 2 thay đổi', chu(nut(m)), 'Lưu 2 thay đổi');
    inp.value = cu; m.khung.oninput({ target: inp });
    bam(m, mot(m, '[data-cdlbat="sepay_bat"]'));
    bang('trả hết về như cũ: ẩn lại', mot(m, '#cdlChan').style.display, 'none');
  });

  await ca('v596 rời màn: còn thay đổi thì có câu hỏi gắn với nấc tổng quan, lưu xong thì xoá', async function () {
    var m = await moMan();
    bang('chưa sửa: không hỏi', m.S.chuaLuu, '');
    moTab(m, 'tab_ke_toan');
    bam(m, mot(m, '[data-cdlbat="sepay_bat"]'));
    // v596 Codex 3d0b446: câu hỏi gắn với nấc TỔNG QUAN, nên lùi từ nhóm về tổng quan
    // không hỏi mà nút nhà hay Back trình duyệt cắt mất tổng quan thì hỏi. Hành vi
    // của khung app kiểm thật ở cai_dat_roi_chua_luu_596.js.
    dung('đang trong nhóm: có câu hỏi kèm số thay đổi', String(m.S.chuaLuu).indexOf('Còn 1 thay đổi') === 0);
    bang('câu hỏi gắn với nấc tổng quan', m.S.chuaLuuNac, 0);
    m.g.back();
    dung('về tổng quan: đặt câu hỏi kèm số thay đổi', String(m.S.chuaLuu).indexOf('Còn 1 thay đổi') === 0);
    moTab(m, 'tab_giao_hang');
    bang('mở nhóm khác khi còn thay đổi: câu hỏi vẫn gắn với tổng quan', m.S.chuaLuuNac, 0);
    m.g.back();
    dung('tổng quan nhắc còn thay đổi chưa lưu', chu(m.khung).indexOf('Còn 1 thay đổi chưa lưu') >= 0);
    await m.g.cdlLuu();
    m.g.back(); m.g.go(m.g.scrCaiDatLoi); await tick();
    bang('lưu xong: không hỏi nữa', m.S.chuaLuu, '');
  });

  await ca('v597 app đọc cả bảng nhóm Zalo như Desk: hết lệch đếm "Zalo bắn tin nhóm", còi báo đi Zalo', async function () {
    // Site 15/10: app đếm 11 ổn, Desk đếm 12 ổn vì cdlDoc() bỏ sót bảng zalo_nhom.
    var m = await moMan();
    var doc = m.g.cdlDoc();
    bang('có bảng nhóm Zalo trong doc của app', (doc.zalo_nhom || []).length, 1);
    // Codex #490: đường báo chỉ tính khi Zalo Bot đang bật (máy chủ tắt bot thì không gửi gì).
    var tt = m.g.VGB_CD.tinhTrang(Object.assign({}, doc, { zalo_bot_token: '*', zalo_bot_bat: 1 }));
    var zl = tt.filter(function (x) { return x.ten === 'Zalo bắn tin nhóm'; })[0];
    dung('có token và có nhóm thì không còn chưa khai', zl && zl.trang !== 'no');
    var thu = tt.filter(function (x) { return x.ten === 'Thư cảnh báo'; })[0];
    bang('không có email nhưng có nhóm Zalo nhận Cảnh báo (chủ đề để trống = nhận tất): đường báo ổn', thu.trang, 'ok');
    var botTat = m.g.VGB_CD.tinhTrang(Object.assign({}, doc, { zalo_bot_token: '*', zalo_bot_bat: 0 }));
    bang('có nhóm nhưng Zalo Bot tắt: vàng, không báo đạt', botTat.filter(function (x) { return x.ten === 'Thư cảnh báo'; })[0].trang, 'off');
    var khongNhom = m.g.VGB_CD.tinhTrang(Object.assign({}, doc, { zalo_nhom: [] }));
    bang('không email, không nhóm: còi chưa khai', khongNhom.filter(function (x) { return x.ten === 'Thư cảnh báo'; })[0].trang, 'no');
    var chiKho = m.g.VGB_CD.tinhTrang(Object.assign({}, doc, { zalo_nhom: [{ bat: 1, chat_id: 'g-1', loai_tin: 'canh_bao', chu_de: 'kho' }] }));
    bang('nhóm chỉ nhận chủ đề Kho thì không tính là đường báo hệ thống', chiKho.filter(function (x) { return x.ten === 'Thư cảnh báo'; })[0].trang, 'no');
  });

  // v604: anh Việt 18/10/2026 bỏ thư cảnh báo nội bộ, mỗi nhóm Zalo tích đúng tin cần
  // nhận. Bấm THẬT: thêm nhóm, Chọn tin nhận, Chọn cả mục, tích thêm một tin, Xong, Lưu.
  await ca('v604 Zalo: hộp Tin nhận gom theo bộ phận, có giải thích, Chọn cả mục, lưu mã theo thứ tự danh mục', async function () {
    var m = await moMan();
    moTab(m, 'tab_tin_nhan');
    bam(m, mot(m, '[data-cdlbangthem="zalo_nhom"]'));
    var oTen = m.khung.querySelectorAll('[data-cdld]').filter(function (e) { return e.getAttribute('data-cdld') === 'ten_nhom'; })[0];
    oTen.value = 'Kế toán';
    m.khung.oninput({ target: oTen });
    dung('màn sửa nhóm có ô Tin nhận và nút Chọn tin nhận', tim(m, '[data-cdldtin]').length === 1);
    dung('chưa tích tin nào thì nói rõ', chu(m.khung).indexOf('Chưa tích tin nào') >= 0);
    bam(m, mot(m, '[data-cdldtin]'));
    var ov = m.tai.body.children[m.tai.body.children.length - 1];
    var box = ov.children[0];
    var TIN = m.g.VGB_ZALO_TIN;
    var dong = box.querySelectorAll('[data-cdlt]');
    bang('mỗi tin trong danh mục một dòng', dong.length, Object.keys(TIN).length);
    dung('có câu dẫn đầu hộp', chu(box).indexOf('Tích tin nào thì nhóm nhận tin đó. Không tích tin nào thì nhóm nhận theo Loại tin và Chủ đề như cũ.') >= 0);
    m.g.VGB_ZALO_BO_PHAN.forEach(function (bp) { dung('có mục ' + bp, chu(box).indexOf(bp) >= 0); });
    dong.forEach(function (d) {
      var ma = d.getAttribute('data-cdlt');
      dung('tin ' + ma + ' hiện tên tiếng Việt', chu(d).indexOf(TIN[ma][1]) >= 0);
      dung('tin ' + ma + ' có dòng giải thích', chu(d.querySelectorAll('.cdl-mo')[0] || {}) === TIN[ma][2]);
    });
    bang('không lộ mã tin nào trong chữ của hộp', Object.keys(TIN).filter(function (ma) { return chu(box).indexOf(ma) >= 0; }), []);
    var ca0 = box.querySelectorAll('[data-cdltca]');
    bang('mỗi bộ phận một nút Chọn cả mục', ca0.length, m.g.VGB_ZALO_BO_PHAN.length);
    /* v606: mục Ban giám đốc đứng đầu, nên tìm nút theo tên bộ phận chứ không theo vị trí. */
    var iKt = m.g.VGB_ZALO_BO_PHAN.indexOf('Hoá đơn, kế toán');
    box.onclick({ target: ca0[iKt] });
    var kt = Object.keys(TIN).filter(function (ma) { return TIN[ma][0] === 'Hoá đơn, kế toán'; });
    bang('Chọn cả mục tích hết mục kế toán', box.querySelectorAll('[data-cdlt]').filter(function (d) { return chu(d).indexOf('☑') >= 0; }).length, kt.length);
    box.onclick({ target: box.querySelectorAll('[data-cdltca]')[iKt] });
    bang('bấm lần nữa thì bỏ hết', box.querySelectorAll('[data-cdlt]').filter(function (d) { return chu(d).indexOf('☑') >= 0; }).length, 0);
    box.onclick({ target: box.querySelectorAll('[data-cdltca]')[iKt] });
    box.onclick({ target: box.querySelectorAll('[data-cdlt]').filter(function (d) { return d.getAttribute('data-cdlt') === 'ht_email_loi'; })[0] });
    box.onclick({ target: box.querySelectorAll('[data-cdltxong]')[0] });
    dung('màn nhóm tóm tắt số tin', chu(m.khung).indexOf((kt.length + 1) + ' tin: ') >= 0);
    dung('loại tin, chủ đề ghi rõ không dùng', chu(m.khung).indexOf('Không dùng: nhóm đã chọn Tin nhận.') >= 0);
    bam(m, mot(m, '#cdlDongXong'));
    dung('thẻ nhóm ở danh sách nói số tin, không nói loại tin', chu(m.khung).indexOf((kt.length + 1) + ' tin: ') >= 0);
    await m.g.cdlLuu();
    var g = m.goi.filter(function (x) { return x.duong === 'vagabond.cai_dat_loi.luu'; })[0];
    var b = JSON.parse(g.ts.bang).zalo_nhom;
    bang('lưu mã theo thứ tự danh mục, nối dấu phẩy', b[1].tin_nhan, kt.concat(['ht_email_loi']).join(', '));
  });

  // v606 (Codex #492 P2 4325875324): bảng Bot thêm trên app không được đi lưới chung
  // (chỉ tạo được dòng không token, không bao giờ gửi được). App có Thêm bot, Đổi
  // token, Nối lại gọi đúng máy chủ như Desk. Bấm THẬT, không gọi hàm nào ngoài chuỗi.
  function tabBot() {
    return LAY.bo_cuc.filter(function (t) { return t.muc.some(function (mu) { return mu.o.some(function (o) { return o.fn === 'zalo_bot_phu'; }); }); })[0].fn;
  }
  function oBot(m, k) { return m.khung.querySelectorAll('[data-cdlbot]').filter(function (e) { return e.getAttribute('data-cdlbot') === k; })[0]; }
  function go_(m, k, v) { var o = oBot(m, k); o.value = v; m.khung.oninput({ target: o }); }
  function lan(m) { return m.goi.map(function (x) { return x.duong; }).filter(function (d) { return d !== 'vagabond.cai_dat_loi.lay'; }); }

  await ca('v606 bot thêm trên app: không có lưới chung "+ Thêm dòng"; mỗi bot một dòng có chip, Nối lại, Đổi token; có nút Thêm bot', async function () {
    var m = await moMan();
    moTab(m, tabBot());
    bang('không có nút thêm dòng chung cho bảng bot', tim(m, '[data-cdlbangthem="zalo_bot_phu"]').length, 0);
    bang('dòng bot không mở màn sửa dòng chung', tim(m, '[data-cdlbang="zalo_bot_phu"]').length, 0);
    var t = chu(m.khung);
    dung('tên và số bot', t.indexOf('Bot Bếp (số 2)') >= 0);
    dung('chip Đã nối', t.indexOf('Đã nối') >= 0);
    bang('nút Nối lại đúng số', tim(m, '[data-cdlbotnoi]').map(function (e) { return e.getAttribute('data-cdlbotnoi'); }), ['2']);
    bang('nút Đổi token đúng số', tim(m, '[data-cdlbottoken]').map(function (e) { return e.getAttribute('data-cdlbottoken'); }), ['2']);
    bang('một nút Thêm bot', tim(m, '[data-cdlbotthem]').length, 1);
  });

  await ca('v606 Thêm bot trên app: token trống thì không gọi máy chủ; dán token thì luu_bot rồi nối đúng số máy cấp, đọc lại cài đặt, không giữ token', async function () {
    var m = await moMan();
    moTab(m, tabBot());
    bam(m, mot(m, '[data-cdlbotthem]'));
    bang('màn Thêm bot', m.g._t, 'Thêm bot Zalo');
    dung('ô token là ô mật khẩu', oBot(m, 'token').getAttribute('type') === 'password');
    bam(m, mot(m, '#cdlBotXong'));
    bang('token trống: không gọi gì', lan(m), []);
    dung('token trống: nói cần dán token', m.toast.join(' ').indexOf('token') >= 0);
    go_(m, 'ten', 'Bot nhóm Bánh lạnh');
    go_(m, 'token', 'TOKEN-BOT-BA');
    bam(m, mot(m, '#cdlBotXong'));
    await tick(); await tick();
    var g = m.goi.filter(function (x) { return x.duong !== 'vagabond.cai_dat_loi.lay'; });
    bang('gọi đúng thứ tự', g.map(function (x) { return x.duong; }), ['vagabond.kenh_zalo.luu_bot', 'vagabond.kenh_zalo.dang_ky_webhook']);
    bang('luu_bot nhận số trống, tên, token', g[0].ts, { ma: '', ten: 'Bot nhóm Bánh lạnh', token: 'TOKEN-BOT-BA' });
    bang('nối đúng số máy cấp', g[1].ts, { bot: '3' });
    bang('đọc lại cài đặt sau khi thêm', m.goi.filter(function (x) { return x.duong === 'vagabond.cai_dat_loi.lay'; }).length, 2);
    dung('quay về tab', m.g._t !== 'Thêm bot Zalo');
    dung('báo kết quả nối', m.toast.join(' ').indexOf('Đã nối bot số 3.') >= 0);
    dung('đọc lại được thì không có câu nhắc đọc lại hỏng', m.toast.join(' ').indexOf('chưa tải lại') < 0);
    dung('token không còn trong trạng thái app', JSON.stringify(m.g.CDL).indexOf('TOKEN-BOT-BA') < 0);
    bang('không tạo thay đổi chờ lưu', m.g.cdlSoThay(), 0);
  });

  await ca('v606 Đổi token, tên trên app: chỉ đổi tên thì luu_bot với token trống và KHÔNG nối lại; Nối lại gọi đúng số bot', async function () {
    var m = await moMan();
    moTab(m, tabBot());
    bam(m, mot(m, '[data-cdlbottoken="2"]'));
    bang('ô tên điền sẵn tên cũ', oBot(m, 'ten').value, 'Bot Bếp');
    go_(m, 'ten', 'Bot Bếp mới');
    bam(m, mot(m, '#cdlBotXong'));
    await tick(); await tick();
    bang('chỉ luu_bot', lan(m), ['vagabond.kenh_zalo.luu_bot']);
    bang('đúng số, token trống', m.goi.filter(function (x) { return x.duong === 'vagabond.kenh_zalo.luu_bot'; })[0].ts, { ma: '2', ten: 'Bot Bếp mới', token: '' });
    bam(m, mot(m, '[data-cdlbotnoi="2"]'));
    await tick(); await tick();
    bang('Nối lại gọi đăng ký đường nhận bot 2', m.goi.filter(function (x) { return x.duong === 'vagabond.kenh_zalo.dang_ky_webhook'; }).map(function (x) { return x.ts; }), [{ bot: '2' }]);
  });

  await ca('v606 bot trên app: còn thay đổi chưa lưu thì không mở Thêm bot, không nối; luu_bot báo lỗi thì ở lại màn, không nối', async function () {
    var m = await moMan();
    moTab(m, 'tab_ke_toan');
    bam(m, mot(m, '[data-cdlbat="sepay_bat"]'));
    m.g.back();
    moTab(m, tabBot());
    bam(m, mot(m, '[data-cdlbotthem]'));
    bam(m, mot(m, '[data-cdlbotnoi="2"]'));
    await tick();
    bang('không gọi máy chủ', lan(m), []);
    dung('nhắc bấm Lưu trước', m.toast.join(' ').indexOf('Lưu') >= 0);
    var m2 = await moMan();
    m2.g._loiBot = 'Token sai hoặc bot đã bị xoá';
    moTab(m2, tabBot());
    bam(m2, mot(m2, '[data-cdlbotthem]'));
    go_(m2, 'token', 'TOKEN-SAI');
    bam(m2, mot(m2, '#cdlBotXong'));
    await tick(); await tick();
    bang('chỉ luu_bot, không nối', lan(m2), ['vagabond.kenh_zalo.luu_bot']);
    bang('ở lại màn Thêm bot', m2.g._t, 'Thêm bot Zalo');
    dung('báo lỗi máy chủ', m2.toast.join(' ').indexOf('Token sai') >= 0);
  });

  await ca('v606 (Codex #492 P2 4326242179): đọc lại cài đặt lỗi sau khi thêm hoặc nối bot thì nói thẳng, không chỉ báo thành công', async function () {
    var m = await moMan();
    m.g._loiLay = 1;
    moTab(m, tabBot());
    bam(m, mot(m, '[data-cdlbotthem]'));
    go_(m, 'token', 'TOKEN-BOT-BA');
    bam(m, mot(m, '#cdlBotXong'));
    await tick(); await tick();
    var t = m.toast.join(' | ');
    dung('vẫn báo việc đã làm xong trên máy chủ', t.indexOf('Đã nối bot số 3.') >= 0);
    dung('nói chưa tải lại được và cách làm: ' + t, t.indexOf('chưa tải lại được') >= 0 && t.indexOf('Mở lại màn Cài đặt lõi') >= 0);
    m.toast.length = 0;
    bam(m, mot(m, '[data-cdlbotnoi="2"]'));
    await tick(); await tick();
    t = m.toast.join(' | ');
    dung('Nối lại cũng nói chưa tải lại được: ' + t, t.indexOf('chưa tải lại được') >= 0);
    // Đọc lại hỏng thì lần mở màn sau phải đọc máy chủ (không có thay đổi chờ lưu nên không giữ bản cũ).
    bang('không còn thay đổi chờ lưu', m.g.cdlSoThay(), 0);
  });

  await ca('v606 thẻ nhóm Zalo trên app nói nhóm gửi bằng bot nào; bot đã xoá thì nói đang gửi bằng bot chính', async function () {
    var lay = JSON.parse(JSON.stringify(LAY));
    lay.bang.zalo_nhom.dong.push(Object.assign({}, lay.bang.zalo_nhom.dong[0], { name: 'r2', ten_nhom: 'Bánh lạnh', chat_id: 'g-2', bot: '2' }),
      Object.assign({}, lay.bang.zalo_nhom.dong[0], { name: 'r3', ten_nhom: 'Kho', chat_id: 'g-3', bot: '5' }));
    var m = dungMan(); m.g._lay = lay; m.g.go(m.g.scrCaiDatLoi); await tick();
    moTab(m, tabBot());
    var t = chu(m.khung);
    dung('nhóm bot 2', t.indexOf('gửi bằng Bot Bếp (số 2)') >= 0);
    dung('nhóm bot đã xoá', t.indexOf('bot số 5 đã xoá, đang gửi bằng bot chính') >= 0);
    var the0 = tim(m, '[data-cdldong="0"]')[0];
    dung('nhóm bot chính không ghi gửi bằng', chu(the0).indexOf('Vận hành') >= 0 && chu(the0).indexOf('gửi bằng') < 0);
  });

  /* v616 (Codex #499 4373739957): nút Thử kết nối GreenSM phải có cả trên app. */
  function tabGsm() {
    return LAY.bo_cuc.filter(function (t) { return t.muc.some(function (mu) { return mu.fn === 'sec_gsm'; }); })[0];
  }
  function moMucGsm(m) {
    var t = tabGsm();
    moTab(m, t.fn);
    var mu = t.muc.filter(function (x) { return x.fn === 'sec_gsm'; })[0];
    if (!tim(m, '[data-cdlthugsm]').length && mu.gon) bam(m, mot(m, '[data-cdlgon="sec_gsm"]'));
  }

  await ca('v616 app: mục GreenSM có nút Thử kết nối GreenSM, bấm thì chạy đủ chuỗi và hiện từng bước ngay dưới nút', async function () {
    dung('máy chủ có mục GreenSM trên app', !!tabGsm());
    var m = await moMan();
    m.g._gsm = { ok: 1, buoc: ['Danh sách loại xe: Express for partner (1878)', 'Báo giá: 80.000 đ, 5.33 km, mã giá f1', 'Tạo đơn: mã 01M5, trạng thái FINDING', 'Xem lại đơn: FINDING'] };
    moMucGsm(m);
    var n = mot(m, '[data-cdlthugsm]');
    bang('chữ nút giống Desk', chu(n), 'Thử kết nối GreenSM');
    dung('có dòng giải thích chỉ chạy môi trường thử', chu(mot(m, '#cdl-thu-gsm')).indexOf('không bao giờ gọi xe thật') >= 0);
    bam(m, n);
    dung('đang chạy thì nói chờ', chu(mot(m, '#cdl-thu-gsm')).indexOf('Đang thử kết nối GreenSM') >= 0);
    bam(m, mot(m, '[data-cdlthugsm]'));
    await tick(); await tick();
    var g = m.goi.filter(function (x) { return x.duong === 'vagabond.greensm.thu_ket_noi'; });
    bang('gọi máy chủ đúng một lần dù bấm hai lần', g.length, 1);
    var t = chu(mot(m, '#cdl-thu-gsm'));
    dung('báo kết nối được: ' + t, t.indexOf('GreenSM kết nối được') >= 0);
    dung('hiện đủ bốn bước', ['1878', '80.000 đ', 'FINDING', 'Xem lại đơn'].every(function (x) { return t.indexOf(x) >= 0; }));
  });

  await ca('v616 app: còn ô chưa lưu thì không thử; máy chủ chặn (ví dụ đang dùng khoá thật) thì nói đúng câu máy chủ', async function () {
    var m = await moMan();
    moTab(m, 'tab_ke_toan');
    bam(m, mot(m, '[data-cdlbat="sepay_bat"]'));
    m.g.back();
    moMucGsm(m);
    bam(m, mot(m, '[data-cdlthugsm]'));
    await tick();
    bang('không gọi máy chủ', m.goi.filter(function (x) { return x.duong === 'vagabond.greensm.thu_ket_noi'; }).length, 0);
    dung('nhắc lưu trước', m.toast.indexOf('Bấm Lưu trước rồi mới thử kết nối GreenSM.') >= 0);
    var m2 = await moMan();
    m2.g._gsmLoi = 'Nút thử chỉ chạy ở môi trường thử GreenSM, để không gọi xe thật.';
    moMucGsm(m2);
    bam(m2, mot(m2, '[data-cdlthugsm]'));
    await tick(); await tick();
    var t = chu(mot(m2, '#cdl-thu-gsm'));
    dung('chip chưa thử được', t.indexOf('Chưa thử được') >= 0);
    dung('câu máy chủ', t.indexOf('Nút thử chỉ chạy ở môi trường thử GreenSM') >= 0);
    dung('nút bấm lại được', !mot(m2, '[data-cdlthugsm]').hasAttribute('disabled'));
  });

  console.log('\n' + ket.dat + ' ca dat, ' + ket.hong + ' ca hong.');
  if (ket.hong) process.exit(1);
})();

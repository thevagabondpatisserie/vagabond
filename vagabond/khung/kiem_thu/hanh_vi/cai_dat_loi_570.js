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
    '  "tu_xuat_hddt": 1, "ngan_hang_bin": "970422", "ngan_hang_hien_thi": "MB Bank", "diem_chu_ky": "Cuon chieu",',
    '  "zalo_chat_moi": json.dumps([{"chat_id": "g-777", "ten": "Nhóm Bếp", "loai": "GROUP"}, {"chat_id": "u-1", "ten": "Anh A", "loai": "USER"}]),',
    '  "vgb_diem_ban": json.dumps([{"ma": "Q1", "ten": "Quận 1", "co_quay": 1}])})',
    'cot = t._cot_zalo()',
    'dong = [{"name": "r1", "ten_nhom": "Vận hành", "chat_id": "g-1", "loai_tin": "thong_bao, canh_bao", "chu_de": "", "im_tu": "22:00", "im_den": "07:00", "bat": 1}]',
    'ra = {"bo_cuc": c.bo_cuc(tr), "gia_tri": c.gia_tri(tr, doc), "modified": "2026-10-04 09:00:00.000001",',
    '  "bang": {"zalo_nhom": {"cot": c.tom_bang(cot), "dong": [dict(c.gia_tri(cot, r), name=r["name"]) for r in dong],',
    '    "ghi_qua_hop_chon": list(c.GHI_QUA_HOP_CHON["zalo_nhom"])}}}',
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
      if (duong === 'vagabond.cai_dat_loi.lay') return Promise.resolve(JSON.parse(JSON.stringify(LAY)));
      if (duong === 'vagabond.tai_khoan.danh_sach') return Promise.resolve({ ngan_hang: NGAN_HANG });
      if (duong === 'vagabond.cai_dat_loi.tim_lien_ket') return Promise.resolve(['Kho A', 'Kho B']);
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
    bang('hộp chọn chỉ có nhóm GROUP', m.sheet[0].items.map(function (x) { return x.value; }), ['g-777']);
    m.sheet[0].onPick(m.sheet[0].items[0]);
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

  console.log('\n' + ket.dat + ' ca dat, ' + ket.hong + ' ca hong.');
  if (ket.hong) process.exit(1);
})();

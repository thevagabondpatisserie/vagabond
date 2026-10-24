/* Ca kiểm HÀNH VI v610: bảng Dò tiền chuyển khoản có chip tài khoản, và màn
 * Đối soát chuyển khoản.
 *
 * Ca gốc: bill TCVEHQHG (HDB-26-10-04707) ngày 23/10/2026, 1.875.000 đ, khách
 * chuyển thẳng vào MB 31561568. Trước v610 bảng Dò tiền chỉ soi tài khoản ảo
 * của điểm nên khoản đó không bao giờ hiện ra.
 *
 * Nạp THẬT posSheetDoTien (09-tinh-tien-quay.js) và toàn bộ 56-doi-soat-ck.js
 * vào DOM giả. Máy chủ giả KHÔNG gõ tay kết quả: mỗi lượt pos_do_tien chạy
 * python dựng bảng bằng chính doi_soat_ck.dung_bang_do_tien trên sao kê mẫu
 * của thu_doi_soat_ck_610.py, đúng nguồn và đúng vai người bấm.
 *
 * Mỗi ca bấm đúng chuỗi thao tác của người dùng, không gọi thêm hàm nội bộ
 * nào "cho chắc" (điều 15).
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/doi_soat_ck_610.js
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
var NEN = doc('00-nen.js'), POS = doc('09-tinh-tien-quay.js'), KHUON = doc('15-khuon-danh-sach.js');
var KM = doc('13-khuyen-mai.js'), KHO = doc('03-kho-chung-tu.js');
var MAN = doc('56-doi-soat-ck.js');

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
var HAM = ['h', 'money', 'today'].map(function (t) { return layHam(NEN, t); })
  .concat(['posChipNut', 'posNgayVn', 'posDtCong', 'posSheetDoTien'].map(function (t) { return layHam(POS, t); }))
  .concat(['dsccHang', 'dsCongCu', 'dsCongCuNoi'].map(function (t) { return layHam(KHUON, t); }))
  .concat(['var scanBarcode = function () { return Promise.resolve(window.__maQuet || null); };'])
  .concat([layHam(KM, 'kmHangChip'), layHam(KHO, 'errMsg')]).join('\n');

/* pos_do_tien giả: chạy thật doi_soat_ck.dung_bang_do_tien. */
function doTienPy(ts, vai) {
  var py = [
    'import json, sys',
    'sys.path.insert(0, sys.argv[1])',
    'from vagabond.khung.kiem_thu import nen',
    'nen.gia_lap()',
    'from vagabond import doi_soat_ck as D',
    'from vagabond.khung.kiem_thu import thu_doi_soat_ck_610 as T',
    'a = json.loads(sys.argv[2])',
    'gds = T.GDS if a["ngay"] in ("", "2026-10-23") else []',
    'kq = D.dung_bang_do_tien(gds, D.bang_dau(T.CAU_HINH, T.TEN), "@diem:TCV", 1, a["tien"],',
    '  {"BT-CTY2": "phiếu công nợ CN-0001"}, a["vai"], a["nguon"], T._cung)',
    'kq.update(tien=a["tien"], ngay=a["ngay"] or "2026-10-23", diem="TCV", tk_rieng=1, tk_stk="VQRQALEAF2999")',
    'sys.stdout.write(json.dumps(kq, ensure_ascii=False))',
  ].join('\n');
  return JSON.parse(cp.execFileSync('python3', ['-c', py, GOC, JSON.stringify({
    tien: Number(ts.tien) || 1875000, ngay: ts.ngay || '', nguon: ts.nguon || '', vai: vai })], { encoding: 'utf8' }));
}

/* ds_bill_ck giả: trạng thái tiền do chính doi_soat_ck.trang_thai_tien tính. */
var BILL = JSON.parse(cp.execFileSync('python3', ['-c', [
  'import json, sys', 'sys.path.insert(0, sys.argv[1])',
  'from vagabond.khung.kiem_thu import nen', 'nen.gia_lap()',
  'from vagabond import doi_soat_ck as D',
  'b = [dict(name="HDB-26-10-04707", ma="TCVEHQHG", ma_tc="TCVEHQHG", quay="TCV", gio="13:46", tong=1875000, nhan=0, ghi_so=0, khach="PHUC"),',
  '     dict(name="HDB-26-10-04650", ma="NVHACDEF", ma_tc="FT26296000000009", quay="NVHTN", gio="11:02", tong=245000, nhan=245000, ghi_so=0, khach="")]',
  'for r in b: r["tt"] = D.trang_thai_tien(r["nhan"], r["tong"])',
  'sys.stdout.write(json.dumps({"ngay": "2026-10-23", "rows": b}, ensure_ascii=False))'].join('\n'), GOC], { encoding: 'utf8' }));

var QUAY = ['VGB - Nhân viên bán hàng'];
var QLCH = ['VGB - Nhân viên bán hàng', 'VGB - Quản lý cửa hàng'];

function dungMoi(vai) {
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);
  var goi = [], toastDs = [], hoi = [], sau = [];
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, Number: Number, Date: Date, setTimeout: setTimeout, isNaN: isNaN,
    posQuay: { ma: 'TCV' },
    S: { roles: vai, stack: [] },
    hasRole: function (r) { return vai.indexOf(r) >= 0; },
    frame: function (t, html) { khung.innerHTML = html; khung.onclick = null; that._t = t; return khung; },
    go: function (fn) { that.S.stack.push(fn); return fn(); },
    busy: function () {},
    toast: function (m) { toastDs.push(m); },
    confirmSheet: function (t, m) { hoi.push(m); return Promise.resolve(true); },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: ts });
      if (duong === 'vagabond.ban_hang.pos_do_tien') return Promise.resolve(doTienPy(ts, vai));
      if (duong === 'vagabond.ban_hang.pos_gan_tien') return Promise.resolve({ ma_tham_chieu: 'FT26296028012585', nhan: 1875000, lech: 0 });
      if (duong === 'vagabond.doi_soat_ck.ds_bill_ck') return Promise.resolve(JSON.parse(JSON.stringify(BILL)));
      return Promise.reject(new Error('api la: ' + duong));
    },
  };
  that.window = that;
  vm.runInNewContext(HAM, that, { filename: 'ham-nen.js' });
  vm.runInNewContext(MAN, that, { filename: '56-doi-soat-ck.js' });
  return { g: that, tai: tai, khung: khung, goi: goi, toast: toastDs, hoi: hoi, sau: sau };
}

var ket = { dat: 0, hong: 0 };
function dung(mo, dk) { if (!dk) throw new Error(mo); }
function bang(mo, a, b) {
  var x = JSON.stringify(a), y = JSON.stringify(b);
  if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y);
}
function tick() { return new Promise(function (r) { setTimeout(r, 5); }); }
async function choDen(dk) { for (var i = 0; i < 80 && !dk(); i++) await new Promise(function (r) { setTimeout(r, 50); }); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); }
}
function sheet(m) { var ds = m.tai.body.children; return ds[ds.length - 1]; }
function chu(el) { var s = el._chu || ''; (el.children || []).forEach(function (c) { s += chu(c); }); return s; }
function bam(m, el) { sheet(m).onclick({ target: el }); }
function goiDo(m) { return m.goi.filter(function (x) { return x.duong === 'vagabond.ban_hang.pos_do_tien'; }); }
function goiGan(m) { return m.goi.filter(function (x) { return x.duong === 'vagabond.ban_hang.pos_gan_tien'; }); }
function dong(m) { return sheet(m).querySelectorAll('[data-gan]'); }

async function moDoTien(vai, ten) {
  var m = dungMoi(vai);
  await m.g.posSheetDoTien(1875000, ten === undefined ? 'HDB-26-10-04707' : ten, function () { m.sau.push(1); });
  await tick();
  return m;
}

(async function () {
  console.log('v610 Đối soát chuyển khoản: bảng Dò tiền và màn danh sách');

  await ca('thu ngân mở bill đã lưu: không gửi mã quầy đang đứng, máy mở thẳng chip tài khoản chính', async function () {
    var m = await moDoTien(QUAY);
    var g0 = goiDo(m)[0].ts;
    bang('bill đã lưu: để máy chủ tự biết điểm của bill', g0.quay, '');
    bang('lần đầu để máy chọn chip', g0.nguon, '');
    var h = sheet(m).innerHTML;
    dung('chip tài khoản chính đang sáng kèm số dòng', /data-dtnguon="cty"[^>]*background:#0f766e[^>]*>🏦 Vào thẳng TK công ty · 2/.test(h));
    dung('dòng đầu là khoản 1.875.000 lúc 13:27', chu(dong(m)[0]).indexOf('1.875.000 đ · 13:27') >= 0);
    dung('dòng ghi rõ vào tài khoản chính', chu(dong(m)[0]).indexOf('Vào thẳng tài khoản chính công ty') >= 0);
    dung('thu ngân thấy khoá Quản lý gắn', chu(dong(m)[0]).indexOf('🔒 Quản lý gắn') >= 0);
    dung('nói rõ chỉ quản lý hoặc kế toán gắn', h.indexOf('Chỉ Quản lý cửa hàng hoặc Kế toán gắn được khoản ở đây') >= 0);
    dung('khoản đã thuộc phiếu công nợ nói rõ ai giữ', chu(dong(m)[1]).indexOf('Đã thuộc về phiếu công nợ CN-0001') >= 0);
  });

  await ca('thu ngân bấm khoản tài khoản chính: báo nhờ quản lý, KHÔNG gọi cửa gắn', async function () {
    var m = await moDoTien(QUAY);
    bam(m, dong(m)[0]);
    await tick();
    bang('không gọi pos_gan_tien', goiGan(m).length, 0);
    bang('không hỏi xác nhận', m.hoi.length, 0);
    dung('có câu nhờ quản lý', (m.toast[0] || '').indexOf('Chỉ Quản lý cửa hàng hoặc Kế toán gắn được') >= 0);
  });

  await ca('quản lý cửa hàng gắn khoản tài khoản chính: xác nhận rồi gọi cửa gắn đúng dòng', async function () {
    var m = await moDoTien(QLCH);
    dung('quản lý thấy nút Chọn', chu(dong(m)[0]).indexOf('Chọn') >= 0);
    bam(m, dong(m)[0]);
    await choDen(function () { return goiGan(m).length; });
    dung('câu xác nhận nêu tài khoản', (m.hoi[0] || '').indexOf('(Vào thẳng tài khoản chính công ty)') >= 0);
    bang('gắn đúng bill và dòng', goiGan(m)[0].ts, { name: 'HDB-26-10-04707', gd: 'BT-CTY' });
    await tick();
    bang('gắn xong gọi lại màn cha', m.sau.length, 1);
  });

  await ca('bấm chip tài khoản điểm: hỏi lại máy chủ đúng chip, hiện gợi ý khoản đúng tiền ở tài khoản chính', async function () {
    var m = await moDoTien(QUAY);
    bam(m, sheet(m).querySelectorAll('[data-dtnguon="diem"]')[0]);
    await choDen(function () { return goiDo(m).length === 2 && dong(m).length === 1; });
    bang('gọi lại với chip điểm', goiDo(m)[1].ts.nguon, 'diem');
    dung('chỉ còn khoản của TCV', chu(dong(m)[0]).indexOf('245.000 đ') >= 0);
    var goiY = sheet(m).querySelectorAll('[data-dtnguon="cty"]');
    dung('có khung gợi ý ngoài hàng chip', goiY.length === 2 && chu(goiY[1]).indexOf('Có 1 khoản đúng 1.875.000') >= 0);
    bam(m, goiY[1]);
    await choDen(function () { return goiDo(m).length === 3; });
    bang('bấm gợi ý là sang chip tài khoản chính', goiDo(m)[2].ts.nguon, 'cty');
  });

  await ca('bấm chip Hôm trước: hỏi máy chủ ngày trước của ngày bill, giữ chip tài khoản', async function () {
    var m = await moDoTien(QLCH);
    bam(m, sheet(m).querySelectorAll('[data-dtngay="2026-10-22"]')[0]);
    await choDen(function () { return goiDo(m).length === 2; });
    bang('ngày gửi lên', goiDo(m)[1].ts.ngay, '2026-10-22');
    bang('giữ chip đã chọn', goiDo(m)[1].ts.nguon, 'cty');
    await tick();
    dung('ngày không có khoản nào thì nói rõ', chu(sheet(m)).indexOf('Ngày này không có khoản nào vào thẳng tài khoản chính công ty.') >= 0);
  });

  await ca('bill chưa lưu: chỉ xem, bấm dòng không gắn', async function () {
    var m = await moDoTien(QLCH, '');
    bang('bill chưa lưu thì gửi mã quầy đang đứng', goiDo(m)[0].ts.quay, 'TCV');
    bam(m, dong(m)[0]);
    await tick();
    bang('không gắn', goiGan(m).length, 0);
  });

  await ca('màn Đối soát chuyển khoản: bill chưa khớp lên, bấm là mở Dò tiền đúng bill, đúng điểm, đúng ngày', async function () {
    var m = dungMoi(QLCH);
    dung('quản lý có quyền màn', m.g.coQuyenDsck());
    dung('thu ngân không có ô', !dungMoi(QUAY).g.coQuyenDsck());
    vm.runInNewContext('dsckNgay = "2026-10-23";', m.g);
    await m.g.scrDoiSoatCk();
    await tick();
    bang('tiêu đề', m.g._t, 'Đối soát chuyển khoản');
    var hang = m.khung.querySelectorAll('[data-dsckmo]');
    bang('mặc định chỉ bill chưa khớp đủ', hang.length, 1);
    dung('đúng bill TCVEHQHG', chu(hang[0]).indexOf('TCVEHQHG') >= 0);
    dung('chip chưa khớp', chu(hang[0]).indexOf('Chưa khớp khoản nào') >= 0);
    hang[0].onclick();
    await choDen(function () { return goiDo(m).length; });
    var ts = goiDo(m)[0].ts;
    bang('mở Dò tiền đúng bill, điểm, ngày', [ts.name, ts.quay, ts.ngay], ['HDB-26-10-04707', 'TCV', '2026-10-23']);
  });

  await ca('màn Đối soát chuyển khoản: chip Đã khớp đủ lọc đúng', async function () {
    var m = dungMoi(QLCH);
    vm.runInNewContext('dsckNgay = "2026-10-23";', m.g);
    m.g.S.stack.push(m.g.scrDoiSoatCk);
    await m.g.scrDoiSoatCk();
    await tick();
    var nut = m.khung.querySelectorAll('[data-dscc="tt|du"]')[0];
    dung('có chip Đã khớp đủ', !!nut);
    m.khung.dispatchEvent(dg.suKien('click', {}, nut));
    await choDen(function () { return m.goi.filter(function (x) { return x.duong === 'vagabond.doi_soat_ck.ds_bill_ck'; }).length === 2; });
    await tick();
    var hang = m.khung.querySelectorAll('[data-dsckmo]');
    bang('chỉ bill đã khớp', hang.length, 1);
    dung('bill NVH', chu(hang[0]).indexOf('NVHACDEF') >= 0);
  });

  /* Codex #497 v1 (4366436288): ô tìm và nút quét ở màn danh sách. */
  await ca('màn Đối soát chuyển khoản: gõ mã bill là thấy đúng bill, bỏ qua chip đang lọc', async function () {
    var m = dungMoi(QLCH);
    vm.runInNewContext('dsckNgay = "2026-10-23"; dsckTt = "du";', m.g);
    m.g.S.stack.push(m.g.scrDoiSoatCk);
    await m.g.scrDoiSoatCk();
    await tick();
    var o = m.tai.getElementById('dsckDsTim');
    dung('có ô tìm', !!o);
    dung('có nút quét cạnh ô tìm', m.khung.querySelectorAll('[data-dsquet]').length === 1);
    bang('đang ở chip Đã khớp đủ: chỉ thấy bill NVH', m.khung.querySelectorAll('[data-dsckmo]').length, 1);
    o.value = 'tcvehqhg';
    o.dispatchEvent(dg.suKien('change', {}, o));
    await choDen(function () { return m.goi.filter(function (x) { return x.duong === 'vagabond.doi_soat_ck.ds_bill_ck'; }).length === 2; });
    await tick();
    var hang = m.khung.querySelectorAll('[data-dsckmo]');
    bang('chỉ một bill', hang.length, 1);
    dung('đúng TCVEHQHG dù chip đang là Đã khớp đủ', chu(hang[0]).indexOf('TCVEHQHG') >= 0);
  });

  await ca('màn Đối soát chuyển khoản: quét chuỗi dài chứa mã bill là thấy đúng bill', async function () {
    var m = dungMoi(QLCH);
    vm.runInNewContext('dsckNgay = "2026-10-23"; dsckTt = "chua_xong"; dsckTim = "";', m.g);
    m.g.__maQuet = '00020101021238570010A000000727 NVHACDEF 5303704';
    m.g.S.stack.push(m.g.scrDoiSoatCk);
    await m.g.scrDoiSoatCk();
    await tick();
    var nut = m.khung.querySelectorAll('[data-dsquet]')[0];
    m.khung.dispatchEvent(dg.suKien('click', {}, nut));
    await choDen(function () { return m.goi.filter(function (x) { return x.duong === 'vagabond.doi_soat_ck.ds_bill_ck'; }).length === 2; });
    await tick();
    var hang = m.khung.querySelectorAll('[data-dsckmo]');
    bang('chỉ một bill', hang.length, 1);
    dung('đúng bill NVH', chu(hang[0]).indexOf('NVHACDEF') >= 0);
    m.g.__maQuet = 'FT26296000000009';
    m.khung.dispatchEvent(dg.suKien('click', {}, m.khung.querySelectorAll('[data-dsquet]')[0]));
    await choDen(function () { return m.goi.filter(function (x) { return x.duong === 'vagabond.doi_soat_ck.ds_bill_ck'; }).length === 3; });
    await tick();
    dung('tìm được theo số tham chiếu ngân hàng đã gắn', chu(m.khung.querySelectorAll('[data-dsckmo]')[0]).indexOf('NVHACDEF') >= 0);
  });

  console.log('\n' + ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng.');
  if (ket.hong) process.exit(1);
})();

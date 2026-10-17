/* Ca kiểm HÀNH VI màn "Giá vốn tạm tính" trên app (Issue #482).
 *
 * Nạp THẬT tệp 53-gia-von-tam.js cùng các hàm nền thật (h, money, kl,
 * anhMon, vgbKhop, posChipNut) vào DOM giả. Dữ liệu máy chủ KHÔNG gõ tay:
 * chạy python dựng đúng kết quả của gia_von_tam.dung_bang trên dữ liệu mẫu,
 * nên đổi hình dạng dữ liệu bên máy chủ là ca này thấy ngay.
 *
 * Mỗi ca bấm đúng chuỗi thao tác của Khải: mở màn, bấm chip, gõ tìm, bấm thẻ,
 * mở sheet tỷ lệ, bấm Chốt. Không gọi thêm hàm nội bộ nào "cho chắc" (điều 15).
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/gia_von_tam_482.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var cp = require('child_process');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
var SRC = fs.readFileSync(path.join(BEP, '53-gia-von-tam.js'), 'utf8');
var NEN = fs.readFileSync(path.join(BEP, '00-nen.js'), 'utf8');
var POS = fs.readFileSync(path.join(BEP, '09-tinh-tien-quay.js'), 'utf8');

function layHam(src, ten) {
  var dau = src.indexOf('function ' + ten + '(');
  if (dau < 0) throw new Error('Khong thay ham ' + ten);
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Ham ' + ten + ' khong dong ngoac');
}
var NEN_HAM = ['h', 'money', 'num', 'kl', 'anhMon', 'vgbChuan', 'vgbKhop'].map(function (t) { return layHam(NEN, t); }).join('\n') +
  '\n' + layHam(POS, 'posChipNut');

/* Dữ liệu màn dựng bằng chính phép máy chủ. */
function tinhThat(them) {
  var py = [
    'import json, sys',
    'sys.path.insert(0, sys.argv[1])',
    'from vagabond.khung.kiem_thu import nen',
    'nen.gia_lap()',
    'from vagabond import gia_von_tam as G',
    'ban = [',
    '  {"ma": "BAWC00067", "ten": "Bánh Ổ Roman De La Rose, size 16cm", "nhom": "Bánh ổ sinh nhật", "dvt": "Cái", "anh": "/files/roman.jpg"},',
    '  {"ma": "BAEN00073", "ten": "Slice MEKONG Cheesecake", "nhom": "Bánh lạnh", "dvt": "Cái"},',
    '  {"ma": "BANU00060", "ten": "Shiopan Kem Trứng Muối & Chà Bông Cay", "nhom": "Bánh nướng", "dvt": "Cái"},',
    '  {"ma": "BANU00099", "ten": "Bánh Dứa Bơ Nâu", "nhom": "Bánh nướng", "dvt": "Cái"},',
    '  {"ma": "BACF00001", "ten": "Biscotti Các Loại Hạt", "nhom": "Bánh khô", "dvt": "Hũ"},',
    '  {"ma": "BAEN00051", "ten": "Slice Tiramisu Mille Crepes", "nhom": "Bánh lạnh", "dvt": "Cái"},',
    ']',
    'ket = {"B1": {"gia": 250959, "thieu": set(), "vong": False}, "B2": {"gia": 23885, "thieu": set(), "vong": False},',
    '  "B3": {"gia": 379233, "thieu": set(), "vong": False},',
    '  "B4": {"gia": 9000, "thieu": {"BTPB00153", "BTPB00156", "BTPB00154"}, "vong": False},',
    '  "B5": {"gia": 21000, "thieu": set(), "vong": False}}',
    'ma_bom = {"BAWC00067": "B1", "BAEN00073": "B2", "BANU00060": "B3", "BANU00099": "B4", "BACF00001": "B5"}',
    'gia_ban = {"BAWC00067": 880000, "BAEN00073": 160000, "BANU00060": 65000, "BANU00099": 45000, "BACF00001": 190000}',
    'ten = {"BTPB00153": "BTP Brown Butter", "BTPB00156": "BTP Nước ép dứa", "BTPB00154": "BTP Thịt bí"}',
    'he_so = {"Bánh ổ sinh nhật": 4}',
    'mo_ho = {}',
    'if sys.argv[2] == "1":',
    '  ban.append({"ma": "BAVO00001", "ten": "Bánh Công Thức Vòng", "nhom": "Bánh nướng", "dvt": "Cái"})',
    '  ket["B6"] = {"gia": 0, "thieu": set(), "vong": True}',
    '  ma_bom["BAVO00001"] = "B6"',
    '  ban.append({"ma": "BAHAI0001", "ten": "Bánh Hai Công Thức", "nhom": "Bánh lạnh", "dvt": "Cái"})',
    '  mo_ho["BAHAI0001"] = ["BOM-BAHAI0001-001", "BOM-BAHAI0001-002"]',
    'b = G.dung_bang(ban, ma_bom, ket, gia_ban, {"BAWC00067": ("2026-10-12", 245000)}, he_so, ten, mo_ho)',
    'b.update({"he_so": he_so, "cap_nhat_luc": "09:15", "sua_duoc": True, "ngay": "2026-10-16"})',
    'sys.stdout.write(json.dumps(b, ensure_ascii=False, default=str))',
  ].join('\n');
  return JSON.parse(cp.execFileSync('python3', ['-c', py, GOC, them ? '1' : '0'], { encoding: 'utf8' }));
}
var TINH = tinhThat();
var TINH_VONG = tinhThat(true);  /* Codex #483 vong 3: co mon vong va mon hai cong thuc */

/* v600 phiếu thử: kết quả do CHÍNH gia_von_tam.chuan_phieu + tinh_phieu tính,
   với bảng giá mã cố định, để đổi hình dạng dữ liệu bên máy chủ là ca thấy. */
var GIA_MA_PY = 'GM = {"NVLT00001": {"gia": 30.0, "nguon": "Giá kho", "thieu": 0, "vong": False},' +
  ' "NBTP00006": {"gia": 400.0, "nguon": "Công thức", "thieu": 0, "vong": False},' +
  ' "NVLT00099": {"gia": 0.0, "nguon": "Thiếu giá", "thieu": 1, "vong": False}}';
function tinhPhieuPy(cacPhieu) {
  var py = [
    'import json, sys',
    'sys.path.insert(0, sys.argv[1])',
    'from vagabond.khung.kiem_thu import nen',
    'nen.gia_lap()',
    'from vagabond import gia_von_tam as G',
    GIA_MA_PY,
    'ra = []',
    'for p in json.loads(sys.argv[2]):',
    '  c = G.chuan_phieu(p)',
    '  r = dict(c, **G.tinh_phieu(c, lambda m: GM[m], {"Bánh lạnh": 5}))',
    '  r.update(name=p.get("name"), cap_nhat="2026-10-16 22:00")',
    '  ra.append(r)',
    'sys.stdout.write(json.dumps(ra, ensure_ascii=False, default=str))',
  ].join('\n');
  return JSON.parse(cp.execFileSync('python3', ['-c', py, GOC, JSON.stringify(cacPhieu)], { encoding: 'utf8' }));
}
var DS_THU = tinhPhieuPy([
  { name: 'GT-2610-001', ten_mon: 'Tart chanh dây', nhom: 'Bánh lạnh', so_ra: 4, gia_ban_du_kien: 30000, dong: [
    { item_code: 'NVLT00001', ten: 'Bột mì', dvt: 'Gram', so_luong: 1000 },
    { item_code: 'NBTP00006', ten: 'BTP kem', dvt: 'Gram', so_luong: 50 },
    { ten: 'Chanh dây Đà Lạt', dvt: 'Gram', so_luong: 200, don_gia_tay: 50 }] }
]);
var DS_THU_2 = tinhPhieuPy([
  { name: 'GT-2610-003', ten_mon: 'Mousse xoài', nhom: 'Bánh lạnh', so_ra: 1, gia_ban_du_kien: 0, dong: [
    { item_code: 'NVLT00001', ten: 'Bột mì', dvt: 'Gram', so_luong: 100 }] }
]);
/* Codex #486 vòng 6: phiếu có giá dự kiến, một mã có giá và một mã thiếu giá.
   Máy chủ trả he_so tính trên giá vốn THIẾU kèm trang_thai thieu_gia. */
var DS_THU_THIEU = tinhPhieuPy([
  { name: 'GT-2610-004', ten_mon: 'Bánh hạnh nhân thử', nhom: 'Bánh lạnh', so_ra: 1, gia_ban_du_kien: 60000, dong: [
    { item_code: 'NVLT00001', ten: 'Bột mì', dvt: 'Gram', so_luong: 100 },
    { item_code: 'NVLT00099', ten: 'Bột hạnh nhân', dvt: 'Gram', so_luong: 100 }] }
]);
/* Codex #486 vòng 7: thêm một phiếu chưa chọn nhóm để có đủ ba hàng chip. */
var DS_THU_KHONG_NHOM = tinhPhieuPy([
  { name: 'GT-2610-005', ten_mon: 'Su kem thử', nhom: '', so_ra: 2, gia_ban_du_kien: 40000, dong: [
    { item_code: 'NVLT00001', ten: 'Bột mì', dvt: 'Gram', so_luong: 100 }] }
]);
/* Codex #486 vòng 9: phiếu đã lưu có dấu vết do máy chủ trả (_doc_phieu), và
   một dòng có mã đã có giá kho nhưng còn giá tay cũ 500 (máy chủ phải bỏ qua). */
var DS_THU_VET = tinhPhieuPy([
  { name: 'GT-2610-006', ten_mon: 'Tart vani sửa nhiều', nhom: 'Bánh lạnh', so_ra: 1, gia_ban_du_kien: 30000, dong: [
    { item_code: 'NVLT00001', ten: 'Bột mì', dvt: 'Gram', so_luong: 100, don_gia_tay: 500 }] },
  { name: 'GT-2610-007', ten_mon: 'Su kem mới lập', nhom: 'Bánh lạnh', so_ra: 1, gia_ban_du_kien: 30000, dong: [
    { item_code: 'NVLT00001', ten: 'Bột mì', dvt: 'Gram', so_luong: 100 }] }
]).map(function (p, i) {
  return Object.assign(p, i === 0 ?
    { nguoi: 'khai@x', ten_nguoi: 'Khải', lap_luc: '2026-10-16 21:00:00', nguoi_sua: 'loan@x', ten_nguoi_sua: 'Loan', cap_nhat: '2026-10-17 09:30', so_lan_sua: 2 } :
    { nguoi: 'khai@x', ten_nguoi: 'Khải', lap_luc: '2026-10-17 08:05:00', nguoi_sua: 'khai@x', ten_nguoi_sua: 'Khải', cap_nhat: '2026-10-17 08:05', so_lan_sua: 0 });
});
/* Lọc chip, đếm chip, chia trang bằng CHÍNH gia_von_tam.loc_trang_thu (Codex
   #486 v7), để máy chủ giả không tự viết lại luật lọc. */
function locPy(ds, ts, co) {
  var py = ['import json, sys', 'sys.path.insert(0, sys.argv[1])', 'from vagabond.khung.kiem_thu import nen', 'nen.gia_lap()',
    'from vagabond import gia_von_tam as G', 'a = json.loads(sys.argv[2])',
    'tt, nh, kh = G.chuan_loc_thu(a["tt"], a["nhom"], a["kh"])',
    'r = G.loc_trang_thu(a["ds"], tt, nh, a["bd"], a["co"])',
    'r.update(trang_thai=tt, nhom=nh, khoang=kh, tong=len(a["ds"]))',
    'sys.stdout.write(json.dumps(r, ensure_ascii=False))'].join('\n');
  return JSON.parse(cp.execFileSync('python3', ['-c', py, GOC, JSON.stringify({ ds: ds, tt: ts.trang_thai || '', nhom: ts.nhom || '',
    kh: ts.khoang || '', bd: ts.bat_dau || 0, co: co })], { encoding: 'utf8' }));
}
/* Đủ chín nhóm bán thật của máy chủ (Codex #486 v7: hơn 8 lựa chọn là sheet có ô tìm). */
var NHOM_BAN = JSON.parse(cp.execFileSync('python3', ['-c', ['import json, sys', 'sys.path.insert(0, sys.argv[1])',
  'from vagabond.khung.kiem_thu import nen', 'nen.gia_lap()', 'from vagabond import gia_von_tam as G',
  'sys.stdout.write(json.dumps(G._nhom_ban(), ensure_ascii=False))'].join('\n'), GOC], { encoding: 'utf8' }));
var CHI_TIET = {
  '': { ma: 'BAWC00067', ten: 'Bánh Ổ Roman De La Rose, size 16cm', bom: 'B1', so_ra: 1, gia: 250959, dong: [
    { ma: 'NBTP00006', ten: 'BTP Cấp 2 Bánh Ổ Roman size 16', sl: 1, dvt: 'Cái', don_gia: 198466, nguon: 'Công thức', thanh_tien: 198466, bom_con: 'BOM-NBTP00006-001', thieu: 0 },
    { ma: 'NVLT00041', ten: 'Trứng gà', sl: 120, dvt: 'Gram', don_gia: 59, nguon: 'Giá kho', thanh_tien: 7080, bom_con: null, thieu: 0 }] },
  'BOM-NBTP00006-001': { ma: 'NBTP00006', ten: 'BTP Cấp 2 Bánh Ổ Roman size 16', bom: 'BOM-NBTP00006-001', so_ra: 1, gia: 198466, dong: [
    { ma: 'NVLT00001', ten: 'Bột mì', sl: 200, dvt: 'Gram', don_gia: 30, nguon: 'Giá kho', thanh_tien: 6000, bom_con: null, thieu: 0 }] }
};

function dungMan(tuyChon) {
  tuyChon = tuyChon || {};
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);
  var goi = [], toastDs = [], hoi = [], bao = [];
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, parseFloat: parseFloat, isNaN: isNaN, Number: Number, setTimeout: setTimeout,
    frame: function (t, html, opt) {
      khung.innerHTML = html + ((opt && opt.footer) || '');
      khung.onclick = null;
      that._t = t; return khung;
    },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: ts });
      if (tuyChon.loi && duong === 'vagabond.gia_von_tam.tinh' && goi.length === 1) return Promise.reject(new Error(tuyChon.loi));
      if (duong === 'vagabond.gia_von_tam.tinh') {
        var d = JSON.parse(JSON.stringify(tuyChon.vong ? TINH_VONG : TINH));
        if (tuyChon.khongSua) d.sua_duoc = false;
        return Promise.resolve(d);
      }
      if (duong === 'vagabond.gia_von_tam.chi_tiet') return Promise.resolve(JSON.parse(JSON.stringify(CHI_TIET[ts.bom || ''])));
      if (duong === 'vagabond.gia_von_tam.luu_he_so') return Promise.resolve({ he_so: {} });
      if (duong === 'vagabond.gia_von_tam.ds_thu') {
        /* Như máy chủ: lọc theo tên, chia trang theo bat_dau, báo con_nua. */
        var tat = tuyChon.khongPhieu ? [] : JSON.parse(JSON.stringify(tuyChon.nhieuTrang ? DS_THU.concat(DS_THU_2) :
          tuyChon.phieuThieu ? DS_THU.concat(DS_THU_THIEU) :
          tuyChon.locNhieu ? DS_THU.concat(DS_THU_2, DS_THU_THIEU, DS_THU_KHONG_NHOM) :
          tuyChon.vet ? DS_THU_VET : DS_THU));
        var tu = String((ts && ts.tu_khoa) || '').toLowerCase();
        if (tu) tat = tat.filter(function (p) { return p.ten_mon.toLowerCase().indexOf(tu) >= 0; });
        var bd = (ts && ts.bat_dau) || 0, co = tuyChon.co || (tuyChon.nhieuTrang ? 1 : 30);
        var tra = Object.assign(locPy(tat, ts || {}, co), { he_so: { 'Bánh lạnh': 5 }, nhom_ban: NHOM_BAN, sua_duoc: !tuyChon.khongSua,
          tu_khoa: tu, bat_dau: bd });
        if (tuyChon.vuot) { tra.vuot = true; tra.tong = 500; }   /* như máy chủ: hơn 500 phiếu khớp tên, chỉ tính 500 */
        var tre = tuyChon.treDs ? tuyChon.treDs.shift() : 0;
        return new Promise(function (r) { setTimeout(function () { r(tra); }, tre || 0); });
      }
      if (duong === 'vagabond.gia_von_tam.tinh_thu' && tuyChon.loiTinhThu) return Promise.reject(new Error(tuyChon.loiTinhThu));
      if (duong === 'vagabond.gia_von_tam.tinh_thu') {
        /* treTinhThu: độ trễ từng lượt, để dựng đúng cảnh trả về lệch thứ tự. */
        var kqT = tinhPhieuPy([JSON.parse(ts.phieu)])[0];
        var treT = tuyChon.treTinhThu ? tuyChon.treTinhThu.shift() : 0;
        return new Promise(function (r) { setTimeout(function () { r(kqT); }, treT || 0); });
      }
      if (duong === 'vagabond.gia_von_tam.luu_thu') return Promise.resolve(Object.assign(tinhPhieuPy([JSON.parse(ts.phieu)])[0], { name: 'GT-2610-002' }));
      if (duong === 'vagabond.gia_von_tam.bo_thu') return Promise.resolve({ ok: 1 });
      if (duong === 'vagabond.gia_von_tam.tim_nl') {
        return Promise.resolve([{ ma: 'NVLT00001', ten: 'Bột mì', dvt: 'Gram', nhom: 'Nguyên liệu' },
          { ma: 'NVLT00099', ten: 'Bột hạnh nhân', dvt: 'Gram', nhom: 'Nguyên liệu' }]);
      }
      if (duong === 'vagabond.gia_von_tam.chot') return Promise.resolve({ da_luu: 4, bo_qua: { 'Thiếu giá nguyên liệu': 1 } });
      return Promise.reject(new Error('api la: ' + duong));
    },
    confirmSheet: function (t, m) { hoi.push(m); return Promise.resolve(tuyChon.tuChoi ? false : true); },
    toast: function (m) { toastDs.push(m); },
    busy: function () {},
    clearTimeout: clearTimeout,
    /* Chồng màn tối giản như 01-khung-app.js: go đẩy và vẽ, back gỡ và vẽ lại. */
    S: { stack: [], chuaLuu: '', chuaLuuNac: null },
    go: function (fn) { that.S.stack.push(fn); return fn(); },
    back: function () { that.S.stack.pop(); var f = that.S.stack[that.S.stack.length - 1]; return f && f(); },
    vgbBoChuaLuu: function () { that.S.chuaLuu = ''; that.S.chuaLuuNac = null; },
    baoTin: function (m) { bao.push(m); },
  };
  that.window = that;
  vm.runInNewContext(NEN_HAM, that, { filename: '00-nen.js' });
  vm.runInNewContext(SRC, that, { filename: '53-gia-von-tam.js' });
  return { g: that, tai: tai, khung: khung, goi: goi, toast: toastDs, hoi: hoi, bao: bao };
}

var ket = { dat: 0, hong: 0 };
function dung(mo, dk) { if (!dk) throw new Error(mo); }
function bang(mo, a, b) {
  var x = JSON.stringify(a), y = JSON.stringify(b);
  if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y);
}
function tick() { return new Promise(function (r) { setTimeout(r, 5); }); }
function cho(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
/* Chờ tới khi điều kiện đúng (tối đa 3 giây): máy chủ giả chạy python thật nên
   lúc máy bận một lượt tính có thể lâu hơn 450ms; không dùng để che lỗi thứ tự. */
async function choDen(dk) { for (var i = 0; i < 60 && !dk(); i++) await cho(50); }
function go(m, el, v) { el.value = v; el.dispatchEvent(dg.suKien('input', {}, el)); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); }
}
function tim(m, chon) { return m.khung.querySelectorAll(chon); }
function bam(m, el) { m.khung.onclick({ target: el }); }
function chu(el) {
  var s = el._chu || '';
  (el.children || []).forEach(function (c) { s += chu(c); });
  return s;
}
function the(m) { return tim(m, '[data-gvtm]').map(function (e) { return e.getAttribute('data-gvtm'); }); }
function goiTen(m) { return m.goi.map(function (x) { return x.duong; }); }
async function moMan(tuyChon) {
  var m = dungMan(tuyChon);
  m.g.S.stack.push(m.g.scrGiaVonTam);
  await m.g.scrGiaVonTam();
  await tick();
  return m;
}
function sheetCuoi(m) { var ds = m.tai.body.children; return ds[ds.length - 1]; }

(async function () {
  console.log('Giá vốn tạm tính #482: màn app');

  await ca('mở màn: gọi tinh đúng một lần, không gọi chi_tiet trước, món vượt giá bán lên đầu nhóm', async function () {
    var m = await moMan();
    bang('chỉ gọi tinh', goiTen(m), ['vagabond.gia_von_tam.tinh']);
    bang('tiêu đề', m.g._t, 'Giá vốn tạm tính');
    bang('năm thẻ theo thứ tự máy chủ', the(m), ['BAWC00067', 'BAEN00073', 'BANU00060', 'BANU00099', 'BACF00001']);
    var shio = tim(m, '[data-gvtm="BANU00060"]')[0];
    dung('Shiopan có cờ vượt giá bán', chu(shio).indexOf('Giá vốn vượt giá bán') >= 0);
    /* Giao diện chip 17/10/2026: hệ số là chip "x0,2 · vốn 583,4%", ba ô số
       Giá vốn / Giá bán / Đề xuất. Đọc HTML vì DOM giả gom chữ của nút cha
       trước chữ của thẻ con <b>. */
    var H = m.khung.innerHTML;
    var o3 = function (nhan, gt) { return '<div class="l">' + nhan + '</div><div class="v">' + gt + '</div>'; };
    dung('Shiopan chip hệ số kèm % giá vốn, màu đỏ vượt giá bán', H.indexOf('style="color:#b3261e;background:#fef2f2"><b>x0,2</b>· vốn 583,4%</span>') >= 0);
    var roman = tim(m, '[data-gvtm="BAWC00067"]')[0];
    dung('Roman ô giá vốn', H.indexOf(o3('Giá vốn', '250.959đ')) >= 0);
    dung('Roman ô giá bán', H.indexOf(o3('Giá bán', '880.000đ')) >= 0);
    dung('Roman chip hệ số x3,5 kèm 28,5%, vàng dưới mục tiêu', H.indexOf('style="color:#b45309;background:#fffbeb"><b>x3,5</b>· vốn 28,5%</span>') >= 0);
    dung('Roman ô đề xuất làm tròn lên, ghi hệ số mục tiêu', H.indexOf('<div class="gvt-o dx">' + o3('Đề xuất x4', '1.004.000đ')) >= 0);
    dung('Roman chip lần chốt trước', chu(roman).indexOf('Chốt 12/10: 245.000đ (+2,4%)') >= 0);
    dung('món chưa đặt mục tiêu nói rõ ở ô đề xuất', chu(tim(m, '[data-gvtm="BAEN00073"]')[0]).indexOf('Đề xuấtChưa đặt hệ số') >= 0);
    dung('đầu nhóm có chip mục tiêu', H.indexOf('Mục tiêu <b style="margin:0 0 0 3px">x4</b>') >= 0);
    dung('nhóm chưa đặt có chip nói rõ', H.indexOf('<span class="gvt-c">Chưa đặt mục tiêu</span>') >= 0);
    dung('có nút Chốt', !!m.tai.getElementById('gvtChot'));
    dung('món chưa công thức không thành thẻ', the(m).indexOf('BAEN00051') < 0);
  });

  /* Codex #483 vòng 2: mọi thẻ phải có chip trạng thái có chữ, không chỉ màu
     của tỷ lệ (AGENTS 2b điều 3). Trước khi sửa, thẻ thiếu giá không có chip. */
  await ca('mỗi thẻ có đúng một chip trạng thái có chữ và đúng màu', async function () {
    var m = await moMan();
    var mong = { BAWC00067: ['duoi_muc_tieu', 'Dưới mục tiêu'], BAEN00073: ['chua_dat_muc_tieu', 'Chưa đặt mục tiêu'],
      BANU00060: ['vuot_gia_ban', 'Vượt giá bán'], BANU00099: ['thieu_gia', 'Thiếu giá NVL'], BACF00001: ['chua_dat_muc_tieu', 'Chưa đặt mục tiêu'] };
    Object.keys(mong).forEach(function (ma) {
      var the1 = tim(m, '[data-gvtm="' + ma + '"]')[0];
      var chip = the1.querySelectorAll('[data-gvttt]');
      bang(ma + ' một chip', chip.length, 1);
      bang(ma + ' trạng thái', chip[0].getAttribute('data-gvttt'), mong[ma][0]);
      bang(ma + ' chữ', chu(chip[0]), mong[ma][1]);
    });
    var mau = function (ma) { return tim(m, '[data-gvtm="' + ma + '"]')[0].querySelectorAll('[data-gvttt]')[0].getAttribute('style'); };
    dung('vượt giá bán màu đỏ', mau('BANU00060').indexOf('#b3261e') >= 0);
    dung('chưa đặt mục tiêu màu xám', mau('BAEN00073').indexOf('#6b7280') >= 0);
  });

  await ca('thẻ thiếu giá: đúng chữ, tối đa hai tên rồi "và N nữa", không có giá đề xuất', async function () {
    var m = await moMan();
    var t = chu(tim(m, '[data-gvtm="BANU00099"]')[0]);
    dung('câu thiếu giá: ' + t, t.indexOf('Thiếu giá 3 nguyên liệu: BTP Brown Butter, BTP Thịt bí và 1 nữa') >= 0);
    dung('ô đề xuất nói chưa tính, không có số', t.indexOf('Đề xuấtChưa tính') >= 0 && m.khung.innerHTML.indexOf('data-gvtm="BANU00099"') >= 0);
    var h99 = m.khung.innerHTML.slice(m.khung.innerHTML.indexOf('data-gvtm="BANU00099"'));
    h99 = h99.slice(0, h99.indexOf('data-gvtm=', 10) > 0 ? h99.indexOf('data-gvtm=', 10) : h99.length);
    dung('thẻ thiếu giá không có ô đề xuất xanh', h99.indexOf('gvt-o dx') < 0);
  });

  await ca('chip nhóm và chip trạng thái: số trên chip đúng, bấm là lọc, bấm lại chip trạng thái là bỏ lọc', async function () {
    var m = await moMan();
    var chipN = tim(m, '[data-gvtn]').map(function (e) { return chu(e); });
    bang('chip nhóm', chipN, ['Tất cả 5', 'Bánh ổ 1', 'Bánh lạnh 1', 'Bánh nướng 2', 'Bánh khô 1']);
    var chipT = tim(m, '[data-gvtt]').map(function (e) { return chu(e); });
    bang('chip trạng thái chỉ hiện chip có số', chipT, ['Vượt giá bán 1', 'Thiếu giá NVL 1', 'Dưới mục tiêu 1']);
    bam(m, tim(m, '[data-gvtn="Bánh nướng"]')[0]);
    bang('lọc nhóm', the(m), ['BANU00060', 'BANU00099']);
    bam(m, tim(m, '[data-gvtn=""]')[0]);
    bam(m, tim(m, '[data-gvtt="thieu_gia"]')[0]);
    bang('lọc trạng thái', the(m), ['BANU00099']);
    bam(m, tim(m, '[data-gvtt="thieu_gia"]')[0]);
    bang('bấm lại bỏ lọc', the(m).length, 5);
  });

  await ca('gõ tìm không dấu ra đúng món; không khớp thì có câu chỉ đường và nút Bỏ lọc', async function () {
    var m = await moMan();
    var q = m.tai.getElementById('gvtQ');
    q.value = 'shiopan trung muoi';
    q.oninput();
    bang('tìm không dấu', the(m), ['BANU00060']);
    q.value = 'khong co banh nay';
    q.oninput();
    bang('rỗng', the(m), []);
    dung('câu rỗng', chu(m.khung).indexOf('Không có bánh nào khớp. Bỏ bớt bộ lọc hoặc đổi từ khoá.') >= 0);
    bam(m, tim(m, '[data-gvtbo]')[0]);
    bang('Bỏ lọc trả đủ', the(m).length, 5);
  });

  await ca('khối món chưa có công thức nằm DƯỚI danh sách, thu gọn, bấm mới hiện tên', async function () {
    var m = await moMan();
    var html = m.khung.innerHTML;
    dung('đứng sau thẻ cuối', html.indexOf('data-gvtcct') > html.indexOf('data-gvtm="BACF00001"'));
    var k = tim(m, '[data-gvtcct]')[0];
    dung('câu đếm', chu(k).indexOf('1 món chưa có công thức nên chưa tính được. Bấm để xem.') >= 0);
    dung('chưa hiện tên', chu(k).indexOf('Tiramisu') < 0);
    bam(m, k);
    dung('bấm thì hiện tên', chu(tim(m, '[data-gvtcct]')[0]).indexOf('Slice Tiramisu Mille Crepes') >= 0);
  });

  await ca('lỗi mạng: câu tiếng người, bấm Thử lại gọi tinh lần nữa; lỗi quyền hiện đúng câu máy chủ', async function () {
    var m = await moMan({ loi: 'Failed to fetch' });
    dung('câu lỗi mạng', chu(m.khung).indexOf('Không tải được giá vốn. Kiểm mạng rồi bấm Thử lại.') >= 0);
    bam(m, tim(m, '[data-gvtlai]')[0]);
    await tick();
    bang('gọi lại tinh', goiTen(m), ['vagabond.gia_von_tam.tinh', 'vagabond.gia_von_tam.tinh']);
    bang('thử lại xong có thẻ', the(m).length, 5);
    var q = await moMan({ loi: 'Tài khoản của bạn không có quyền xem giá vốn tạm tính.' });
    dung('câu quyền', chu(q.khung).indexOf('Tài khoản của bạn không có quyền xem giá vốn tạm tính.') >= 0);
  });

  await ca('v600 sheet hệ số: ô không lớn hơn 1 hoặc quá 20 bị chặn tại chỗ không gửi; gõ là hiện % giá vốn; lưu gửi đúng dict rồi tải lại', async function () {
    var m = await moMan();
    bam(m, tim(m, '[data-gvthso]')[0]);
    var ov = sheetCuoi(m);
    var o = function (n) { return ov.querySelector('[data-gvthsn="' + n + '"]'); };
    dung('có ô cho nhóm Bánh ổ, đã điền 4', o('Bánh ổ sinh nhật') && o('Bánh ổ sinh nhật').value === '4');
    dung('gợi ý trung vị theo hệ số', chu(ov).indexOf('Hiện trung vị x') >= 0);
    dung('quy đổi sẵn cho ô đã có', chu(ov.querySelector('[data-gvtqd="Bánh ổ sinh nhật"]')) === 'tức giá vốn 25% giá bán');
    go(m, o('Bánh lạnh'), '5');
    bang('gõ là đổi', chu(ov.querySelector('[data-gvtqd="Bánh lạnh"]')), 'tức giá vốn 20% giá bán');
    o('Bánh lạnh').value = '1';
    await ov.onclick({ target: ov.querySelector('[data-gvtluu]') });
    bang('chưa gửi', goiTen(m).filter(function (x) { return x.indexOf('luu_he_so') >= 0; }).length, 0);
    dung('báo sai tại chỗ', chu(ov.querySelector('[data-gvtsai="Bánh lạnh"]')).indexOf('Nhập số lớn hơn 1, tối đa 20.') >= 0);
    o('Bánh lạnh').value = '5,5';
    o('Bánh ổ sinh nhật').value = '';
    await ov.onclick({ target: ov.querySelector('[data-gvtluu]') });
    await tick();
    var g = m.goi.filter(function (x) { return x.duong === 'vagabond.gia_von_tam.luu_he_so'; });
    bang('gửi một lần', g.length, 1);
    bang('đúng dict', JSON.parse(g[0].ts.he_so), { 'Bánh ổ sinh nhật': '', 'Bánh lạnh': 5.5, 'Bánh nướng': '', 'Bánh khô': '' });
    bang('tải lại sau khi lưu', goiTen(m).slice(-1), ['vagabond.gia_von_tam.tinh']);
  });

  await ca('Chốt: hỏi đúng số món lưu và bỏ qua, xác nhận gọi chot đúng một lần; huỷ thì không gọi', async function () {
    var m = await moMan();
    await m.g.document.getElementById('gvtChot').onclick();
    bang('câu hỏi', m.hoi[0], 'Lưu giá vốn tạm của 4 món vào bảng giá Giá vốn tạm tính, ngày 16/10/2026. ' +
      '1 món chưa tính đủ giá (thiếu giá nguyên liệu) sẽ bỏ qua. Không đổi công thức, tồn kho hay sổ sách.');
    bang('gọi chot một lần', goiTen(m).filter(function (x) { return x === 'vagabond.gia_von_tam.chot'; }).length, 1);
    dung('báo kết quả', m.toast[0] === 'Đã lưu 4 món. Bỏ qua 1 món.');
    var h2 = await moMan({ tuChoi: true });
    await h2.g.document.getElementById('gvtChot').onclick();
    bang('huỷ thì không chot', goiTen(h2).indexOf('vagabond.gia_von_tam.chot'), -1);
  });

  await ca('không có quyền chốt: không thấy nút Chốt, không thấy nút Hệ số mục tiêu', async function () {
    var m = await moMan({ khongSua: true });
    dung('không nút chốt', !m.tai.getElementById('gvtChot'));
    bang('không nút hệ số', tim(m, '[data-gvthso]').length, 0);
  });

  await ca('bấm thẻ mới gọi chi_tiet; dòng bán thành phẩm mở xuống tầng con, Quay lại về tầng trên', async function () {
    var m = await moMan();
    bam(m, tim(m, '[data-gvtm="BAWC00067"]')[0]);
    await tick();
    bang('gọi chi_tiet theo mã', m.goi[1], { duong: 'vagabond.gia_von_tam.chi_tiet', ts: { ma: 'BAWC00067' } });
    var ov = sheetCuoi(m);
    dung('dòng lá có nguồn giá', chu(ov).indexOf('59đ/Gram (Giá kho)') >= 0);
    await ov.onclick({ target: ov.querySelector('[data-gvtcon]') });
    await tick();
    bang('mở tầng con', m.goi[2].ts, { ma: 'NBTP00006', bom: 'BOM-NBTP00006-001' });
    var ov2 = sheetCuoi(m);
    dung('tầng con có Quay lại', !!ov2.querySelector('[data-gvtlui]'));
    await ov2.onclick({ target: ov2.querySelector('[data-gvtlui]') });
    await tick();
    bang('quay lại gọi lại tầng trên', m.goi[3].ts, { ma: 'BAWC00067' });
  });

  await ca('Codex #483 v3: có món công thức vòng thì có chip lọc "Công thức vòng" kèm số, bấm vào chỉ còn món đó', async function () {
    var m = await moMan({ vong: true });
    var chip = tim(m, '[data-gvtt="vong"]');
    bang('một chip vòng', chip.length, 1);
    dung('chip có chữ và số', chu(chip[0]).indexOf('Công thức vòng 1') >= 0);
    bam(m, chip[0]);
    bang('chỉ còn món vòng', the(m), ['BAVO00001']);
  });

  await ca('Codex #483 v3: không có món vòng thì không hiện chip vòng rỗng', async function () {
    var m = await moMan();
    bang('không chip vòng', tim(m, '[data-gvtt="vong"]').length, 0);
  });

  await ca('Codex #483 v3: món nhiều công thức chưa chọn mặc định không có thẻ giá, có khung nói tên và cách sửa', async function () {
    var m = await moMan({ vong: true });
    dung('không có thẻ giá', the(m).indexOf('BAHAI0001') < 0);
    var k = tim(m, '[data-gvtnct]');
    bang('một khung', k.length, 1);
    var c = chu(k[0]);
    dung('nói số và lý do', c.indexOf('1 món có nhiều công thức nhưng chưa chọn công thức mặc định') >= 0);
    dung('nói tên món', c.indexOf('Bánh Hai Công Thức') >= 0);
    dung('nói cách sửa', c.indexOf('tích Mặc định') >= 0);
  });

  /* ---------------- v600 tab Món thử (R&D) ---------------- */

  async function moThu(tuyChon) {
    var m = await moMan(tuyChon);
    bam(m, tim(m, '[data-gvttab="thu"]')[0]);
    await tick();
    return m;
  }
  function o(m, chon) { return m.khung.querySelector(chon) || m.tai.querySelector(chon); }

  await ca('v600 tab Món thử: bấm tab mới gọi ds_thu một lần, không tính lại tab bán; quay lại tab bán không gọi tinh lần hai', async function () {
    var m = await moThu();
    bang('gọi', goiTen(m), ['vagabond.gia_von_tam.tinh', 'vagabond.gia_von_tam.ds_thu']);
    var t = chu(tim(m, '[data-gvtp="GT-2610-001"]')[0]);
    // Bột 1000 x 30 + kem 50 x 400 + chanh dây 200 x 50 = 60.000, mẻ ra 4.
    var H = m.khung.innerHTML;
    var o3 = function (nhan, gt) { return '<div class="l">' + nhan + '</div><div class="v">' + gt + '</div>'; };
    dung('ô giá vốn mỗi cái', H.indexOf(o3('Giá vốn/Cái', '15.000đ')) >= 0);
    dung('chip mẻ ra và nhóm: ' + t, t.indexOf('Bánh lạnhMẻ ra 4 Cái') >= 0);
    dung('ô đề xuất theo hệ số nhóm', H.indexOf('<div class="gvt-o dx">' + o3('Đề xuất x5', '75.000đ')) >= 0);
    dung('ô giá dự kiến', H.indexOf(o3('Giá dự kiến', '30.000đ')) >= 0);
    dung('chip hệ số dự kiến kèm % vốn', H.indexOf('<b>x2</b>· vốn 50%</span>') >= 0);
    dung('chip trạng thái', t.indexOf('Dưới mục tiêu') >= 0);
    dung('có nút phiếu mới', !!m.tai.getElementById('gvtThuMoi'));
    dung('không có nút Chốt ở tab thử', !m.tai.getElementById('gvtChot'));
    bam(m, tim(m, '[data-gvttab="ban"]')[0]);
    await tick();
    bang('không gọi thêm', goiTen(m).length, 2);
    bang('thẻ bán còn đủ', the(m).length, 5);
  });

  await ca('v600 phiếu mới: tìm thêm mã, nhập số lượng thì tính thử ở máy chủ; dòng chưa có số lượng không gửi; Lưu gửi đủ dòng rồi về danh sách', async function () {
    var m = await moThu();
    m.tai.getElementById('gvtThuMoi').onclick();
    bang('tiêu đề màn nhập', m.g._t, 'Phiếu tính giá thử');
    go(m, m.tai.getElementById('gvtpTen'), 'Tart vani');
    dung('đánh dấu chưa lưu', m.g.S.chuaLuu.indexOf('chưa bấm Lưu phiếu') >= 0);
    bam(m, tim(m, '[data-gvtpnhom]')[0]);
    var ovn = sheetCuoi(m);
    await ovn.onclick({ target: ovn.querySelector('[data-gvtpnchon="Bánh lạnh"]') });
    await tick();
    bam(m, tim(m, '[data-gvtpthem]')[0]);
    var ov = sheetCuoi(m);
    go(m, ov.querySelector('[data-gvtntim]'), 'b');
    await cho(350);
    bang('một chữ chưa tìm', goiTen(m).filter(function (x) { return x.indexOf('tim_nl') >= 0; }).length, 0);
    go(m, ov.querySelector('[data-gvtntim]'), 'bột');
    await cho(350);
    bang('tìm một lần', m.goi.filter(function (x) { return x.duong === 'vagabond.gia_von_tam.tim_nl'; }).map(function (x) { return x.ts; }), [{ tu_khoa: 'bột' }]);
    await ov.onclick({ target: ov.querySelector('[data-gvtnchon="0"]') });
    var truoc = goiTen(m).filter(function (x) { return x.indexOf('tinh_thu') >= 0; }).length;
    bam(m, tim(m, '[data-gvtpthem]')[0]);
    var ov2 = sheetCuoi(m);
    await ov2.onclick({ target: ov2.querySelector('[data-gvtnmoi]') });
    dung('NVL mới thiếu tên báo tại chỗ', chu(ov2.querySelector('[data-gvtnsai]')) === 'Ghi cả tên và đơn vị.');
    ov2.querySelector('[data-gvtnmoiten]').value = 'Vani Tahiti';
    ov2.querySelector('[data-gvtnmoidvt]').value = 'Quả';
    await ov2.onclick({ target: ov2.querySelector('[data-gvtnmoi]') });
    bang('hai dòng', tim(m, '[data-gvtpd]').length, 2);
    dung('dòng NVL mới ghi rõ chưa có mã và có ô giá tay', chu(tim(m, '[data-gvtpd="1"]')[0]).indexOf('chưa có mã') >= 0 && !!o(m, '[data-gvtpgia="1"]'));
    dung('dòng có mã không có ô giá tay khi chưa thiếu giá', !o(m, '[data-gvtpgia="0"]'));
    go(m, o(m, '[data-gvtpsl="0"]'), '500');
    await cho(450);
    /* Máy chủ giả chạy python đồng bộ ngay lúc gọi, máy bận thì kết quả về sau
       mốc 450ms (ca này chập chờn 1/3 lần ngày 17/10). Chỉ chờ kết quả về,
       không gọi thêm hàm nào của màn. */
    await choDen(function () { return chu(o(m, '#gvtpKq')).indexOf('Giá vốn 15.000đ/Cái') >= 0; });
    var tt = m.goi.filter(function (x) { return x.duong === 'vagabond.gia_von_tam.tinh_thu'; });
    dung('có tính thử', tt.length > truoc);
    var gui = JSON.parse(tt[tt.length - 1].ts.phieu);
    bang('chỉ gửi dòng có số lượng', gui.dong.map(function (d) { return [d.item_code, d.so_luong]; }), [['NVLT00001', 500]]);
    dung('kết quả 500 x 30 = 15.000: ' + chu(o(m, '#gvtpKq')), chu(o(m, '#gvtpKq')).indexOf('Giá vốn 15.000đ/Cái') >= 0);
    dung('đề xuất x5', chu(o(m, '#gvtpKq')).indexOf('Đề xuất 75.000đ (mục tiêu x5)') >= 0);
    dung('dòng có nguồn giá', chu(o(m, '[data-gvtpgiadong="0"]')).indexOf('30đ/Gram (Giá kho)') >= 0);
    go(m, o(m, '[data-gvtpsl="1"]'), '2');
    go(m, o(m, '[data-gvtpgia="1"]'), '40000');
    await cho(450);
    await choDen(function () { return chu(o(m, '#gvtpKq')).indexOf('Giá vốn 95.000đ/Cái') >= 0; });
    dung('cộng dòng giá tay: ' + chu(o(m, '#gvtpKq')), chu(o(m, '#gvtpKq')).indexOf('Giá vốn 95.000đ/Cái') >= 0);
    await m.tai.getElementById('gvtpLuu').onclick();
    await tick();
    var l = m.goi.filter(function (x) { return x.duong === 'vagabond.gia_von_tam.luu_thu'; });
    bang('lưu một lần', l.length, 1);
    var p = JSON.parse(l[0].ts.phieu);
    bang('payload lưu', [p.name, p.ten_mon, p.nhom, p.dong.map(function (d) { return [d.item_code, d.ten, d.so_luong, d.don_gia_tay]; })],
      [null, 'Tart vani', 'Bánh lạnh', [['NVLT00001', 'Bột mì', 500, 0], [null, 'Vani Tahiti', 2, 40000]]]);
    bang('xoá cờ chưa lưu', m.g.S.chuaLuu, '');
    dung('báo đã lưu', m.toast.indexOf('Đã lưu phiếu GT-2610-002') >= 0);
    bang('về danh sách và tải lại', [m.g._t, goiTen(m).slice(-1)[0]], ['Giá vốn tạm tính', 'vagabond.gia_von_tam.ds_thu']);
  });

  await ca('v600 mở phiếu đã lưu: thấy kết quả ngay không gọi tính thử; bỏ dòng thì tính lại; Bỏ phiếu hỏi trước, huỷ thì không bỏ, xác nhận thì bỏ mềm (Codex #486 P1)', async function () {
    var m = await moThu();
    bam(m, tim(m, '[data-gvtp="GT-2610-001"]')[0]);
    bang('mở không gọi tính thử', goiTen(m).filter(function (x) { return x.indexOf('tinh_thu') >= 0; }).length, 0);
    dung('dòng kem theo công thức', chu(o(m, '[data-gvtpgiadong="1"]')).indexOf('400đ/Gram (Công thức)') >= 0);
    bam(m, tim(m, '[data-gvtpxoa="2"]')[0]);
    await tick();
    bang('còn hai dòng', tim(m, '[data-gvtpd]').length, 2);
    dung('tính lại 50.000 / 4: ' + chu(o(m, '#gvtpKq')), chu(o(m, '#gvtpKq')).indexOf('Giá vốn 12.500đ/Cái') >= 0);
    m.hoi.length = 0;
    var m2 = await moThu({ tuChoi: true });
    bam(m2, tim(m2, '[data-gvtp="GT-2610-001"]')[0]);
    bam(m2, tim(m2, '[data-gvtpbo]')[0]);
    await tick();
    dung('hỏi trước khi bỏ', m2.hoi[0].indexOf('Bỏ phiếu tính giá thử "Tart chanh dây"?') === 0);
    dung('nói rõ vẫn giữ để tra lại', m2.hoi[0].indexOf('vẫn giữ trên hệ thống để tra lại') >= 0);
    bang('huỷ thì không bỏ', goiTen(m2).indexOf('vagabond.gia_von_tam.bo_thu'), -1);
    bam(m, tim(m, '[data-gvtpbo]')[0]);
    await tick(); await tick();
    bang('xác nhận thì bỏ đúng phiếu', m.goi.filter(function (x) { return x.duong === 'vagabond.gia_von_tam.bo_thu'; }).map(function (x) { return x.ts; }), [{ name: 'GT-2610-001' }]);
    dung('báo đã bỏ', m.toast.indexOf('Đã bỏ phiếu. Vẫn tra lại được trên Desk.') >= 0);
  });


  /* Codex #486 P2: gõ lần hai khi lượt tính đầu còn đang chạy. Lượt đầu về
     SAU lượt hai thì màn không được quay lại số cũ. Trước khi sửa: màn hiện
     giá của lượt đầu (số lượng 100) dù ô đang ghi 200. */
  await ca('Codex #486 v600 tính thử về lệch thứ tự: kết quả cũ về sau không đè kết quả mới', async function () {
    var m = await moThu({ treTinhThu: [600, 10] });
    bam(m, tim(m, '[data-gvtp="GT-2610-001"]')[0]);
    go(m, o(m, '[data-gvtpsl="0"]'), '100');
    await cho(450);            /* lượt 1 đã gửi, đang chờ 600ms */
    go(m, o(m, '[data-gvtpsl="0"]'), '200');
    await cho(450);            /* lượt 2 gửi và về sau 10ms */
    await cho(250);            /* lượt 1 về sau cùng */
    var tt = m.goi.filter(function (x) { return x.duong === 'vagabond.gia_von_tam.tinh_thu'; });
    bang('hai lượt tính', tt.length, 2);
    /* 200 x 30 + kem 20.000 + chanh 10.000 = 36.000 / 4 = 9.000 */
    dung('màn giữ kết quả lượt mới: ' + chu(o(m, '#gvtpKq')), chu(o(m, '#gvtpKq')).indexOf('Giá vốn 9.000đ/Cái') >= 0);
    dung('dòng giữ thành tiền lượt mới', chu(o(m, '[data-gvtpgiadong="0"]')).indexOf('6.000đ') >= 0);
  });

  /* Codex #486 P2: bản đầu máy chủ cắt 200 phiếu, màn không có cách xem
     phần còn lại. Giờ có Xem thêm và tìm ở máy chủ. */
  await ca('Codex #486 v600 danh sách phiếu thử: Xem thêm nạp trang sau nối vào, tìm theo tên gọi máy chủ, kết quả tìm cũ về sau không đè', async function () {
    var m = await moThu({ nhieuTrang: true, treDs: [0, 0, 600, 10] });
    bang('trang đầu một phiếu', tim(m, '[data-gvtp]').length, 1);
    var them = tim(m, '[data-gvtthemds]');
    bang('có nút Xem thêm', them.length, 1);
    bam(m, them[0]);
    await cho(30);
    var ds = m.goi.filter(function (x) { return x.duong === 'vagabond.gia_von_tam.ds_thu'; });
    bang('xem thêm gọi trang sau', ds[ds.length - 1].ts, { tu_khoa: '', bat_dau: 1, trang_thai: '', nhom: '', khoang: '' });
    bang('đủ hai phiếu, giữ thứ tự', tim(m, '[data-gvtp]').map(function (e) { return e.getAttribute('data-gvtp'); }), ['GT-2610-001', 'GT-2610-003']);
    bang('hết trang thì không còn Xem thêm', tim(m, '[data-gvtthemds]').length, 0);
    var q = m.tai.getElementById('gvtThuQ');
    dung('có ô tìm phiếu', !!q);
    go(m, q, 'tart');
    await cho(350);              /* lượt tìm 'tart' gửi, chờ 600ms */
    go(m, m.tai.getElementById('gvtThuQ'), 'mousse');
    await cho(350);              /* lượt 'mousse' gửi, về sau 10ms */
    await cho(300);              /* lượt 'tart' về sau cùng */
    ds = m.goi.filter(function (x) { return x.duong === 'vagabond.gia_von_tam.ds_thu'; });
    bang('tìm ở máy chủ', ds.slice(-2).map(function (x) { return x.ts; }), [{ tu_khoa: 'tart', bat_dau: 0, trang_thai: '', nhom: '', khoang: '' },
      { tu_khoa: 'mousse', bat_dau: 0, trang_thai: '', nhom: '', khoang: '' }]);
    bang('màn giữ kết quả tìm mới', tim(m, '[data-gvtp]').map(function (e) { return e.getAttribute('data-gvtp'); }), ['GT-2610-003']);
    bang('ô tìm giữ chữ đang gõ', m.tai.getElementById('gvtThuQ').value, 'mousse');
  });

  /* Codex #486 v3: gõ 0 vào "Một mẻ ra" thì bản đầu tự gửi 1 lên máy chủ và
     hiện một giá vốn trông như thật, trong khi Lưu thì bị chặn. Màn phải nói
     ngay cần sửa gì và không giữ số của lần tính trước. */
  await ca('Codex #486 v600 mẻ ra 0 hoặc trống: không gửi tính thử với số tự thay, ô kết quả nói cần sửa gì, bỏ số cũ', async function () {
    var m = await moThu();
    bam(m, tim(m, '[data-gvtp="GT-2610-001"]')[0]);
    dung('lúc mở có giá vốn', chu(o(m, '#gvtpKq')).indexOf('Giá vốn 15.000đ/Cái') >= 0);
    var truoc = m.goi.filter(function (x) { return x.duong === 'vagabond.gia_von_tam.tinh_thu'; }).length;
    go(m, m.tai.getElementById('gvtpRa'), '0');
    await cho(450);
    var tt = m.goi.filter(function (x) { return x.duong === 'vagabond.gia_von_tam.tinh_thu'; });
    bang('không gửi tính thử với mẻ ra thay bằng 1', tt.slice(truoc).map(function (x) { return JSON.parse(x.ts.phieu).so_ra; }), []);
    dung('ô kết quả nói cần sửa: ' + chu(o(m, '#gvtpKq')), chu(o(m, '#gvtpKq')).indexOf('Một mẻ phải ra hơn 0') >= 0);
    dung('không còn giá vốn cũ', chu(o(m, '#gvtpKq')).indexOf('Giá vốn 15.000đ') < 0);
    go(m, m.tai.getElementById('gvtpRa'), '');
    await cho(450);
    dung('để trống cũng nói cần sửa', chu(o(m, '#gvtpKq')).indexOf('Một mẻ phải ra hơn 0') >= 0);
    await m.tai.getElementById('gvtpLuu').onclick();
    bang('bấm Lưu khi mẻ ra trống: không gửi lưu', goiTen(m).indexOf('vagabond.gia_von_tam.luu_thu'), -1);
    dung('báo cần sửa', m.bao.indexOf('Một mẻ phải ra hơn 0. Sửa ô Một mẻ ra rồi bấm Lưu.') >= 0);
    go(m, m.tai.getElementById('gvtpRa'), '2');
    await cho(450);
    await choDen(function () { return chu(o(m, '#gvtpKq')).indexOf('Giá vốn') >= 0; });
    tt = m.goi.filter(function (x) { return x.duong === 'vagabond.gia_von_tam.tinh_thu'; });
    bang('sửa thành 2 thì tính lại đúng 2', JSON.parse(tt[tt.length - 1].ts.phieu).so_ra, 2);
    dung('giá vốn theo 2 cái: ' + chu(o(m, '#gvtpKq')), chu(o(m, '#gvtpKq')).indexOf('Giá vốn 30.000đ/Cái') >= 0);
  });

  /* Codex #486 v3 (cùng gốc): máy chủ từ chối tính thử thì bản đầu im lặng
     giữ số cũ. Giờ ô kết quả hiện đúng câu máy chủ trả. */
  await ca('Codex #486 v600 máy chủ từ chối tính thử: ô kết quả hiện câu lỗi, bỏ số cũ', async function () {
    var m = await moThu({ loiTinhThu: 'Dòng 1 (Bột mì): số lượng phải lớn hơn 0.' });
    bam(m, tim(m, '[data-gvtp="GT-2610-001"]')[0]);
    go(m, o(m, '[data-gvtpsl="0"]'), '100');
    await cho(450);
    dung('hiện câu máy chủ: ' + chu(o(m, '#gvtpKq')), chu(o(m, '#gvtpKq')).indexOf('Dòng 1 (Bột mì): số lượng phải lớn hơn 0.') >= 0);
    dung('không còn giá vốn cũ', chu(o(m, '#gvtpKq')).indexOf('Giá vốn 15.000đ') < 0);
  });

  /* Codex #486 v4: mã vừa chọn chưa có giá (hoặc nhiều công thức) thì lúc
     thêm dòng chưa biết thiếu, nên chưa có ô giá tay. Tính xong máy chủ báo
     thiếu mà bản trước chỉ vẽ lại dòng chữ giá, ô giá tay không hiện. */
  await ca('Codex #486 v600 mã thiếu giá: tính xong hiện ngay ô giá tay ở đúng dòng, gõ giá thì tính lại có giá đó', async function () {
    var m = await moThu();
    m.tai.getElementById('gvtThuMoi').onclick();
    go(m, m.tai.getElementById('gvtpTen'), 'Bánh hạnh nhân');
    bam(m, tim(m, '[data-gvtpthem]')[0]);
    var ov = sheetCuoi(m);
    go(m, ov.querySelector('[data-gvtntim]'), 'hạnh nhân');
    await cho(350);
    await ov.onclick({ target: ov.querySelector('[data-gvtnchon="1"]') });
    dung('chưa tính thì chưa có ô giá tay', !o(m, '[data-gvtpgia="0"]'));
    go(m, o(m, '[data-gvtpsl="0"]'), '100');
    await cho(450);
    await choDen(function () { return chu(o(m, '[data-gvtpgiadong="0"]')).indexOf('thiếu giá') >= 0; });
    dung('máy chủ báo thiếu', chu(o(m, '[data-gvtpgiadong="0"]')).indexOf('thiếu giá') >= 0);
    dung('có ô giá tay ở dòng thiếu', !!o(m, '[data-gvtpgia="0"]'));
    bang('ô số lượng giữ chữ đã gõ', o(m, '[data-gvtpsl="0"]').value, '100');
    go(m, o(m, '[data-gvtpgia="0"]'), '400');
    await cho(450);
    await choDen(function () { return chu(o(m, '#gvtpKq')).indexOf('Giá vốn 40.000đ') >= 0; });
    var tt = m.goi.filter(function (x) { return x.duong === 'vagabond.gia_von_tam.tinh_thu'; });
    bang('gửi giá tay', JSON.parse(tt[tt.length - 1].ts.phieu).dong[0].don_gia_tay, 400);
    dung('tính có giá tay: ' + chu(o(m, '#gvtpKq')), chu(o(m, '#gvtpKq')).indexOf('Giá vốn 40.000đ/Cái') >= 0);
  });

  await ca('v600 không có quyền lập phiếu: không có nút Phiếu mới, mở phiếu thì không có Lưu, Thêm, Xoá', async function () {
    var m = await moThu({ khongSua: true });
    dung('không nút mới', !m.tai.getElementById('gvtThuMoi'));
    bam(m, tim(m, '[data-gvtp="GT-2610-001"]')[0]);
    dung('không Lưu', !m.tai.getElementById('gvtpLuu'));
    bang('không Thêm, Bỏ', [tim(m, '[data-gvtpthem]').length, tim(m, '[data-gvtpbo]').length], [0, 0]);
  });

  /* Codex #486 vòng 6 (P2): phiếu thử thiếu giá vẫn có he_so từ máy chủ (tính
     trên giá vốn thiếu). Chip hệ số kèm % vốn phải ẩn ở cả thẻ danh sách lẫn
     khối kết quả trong phiếu, như thẻ món đang bán. */
  await ca('Codex #486 v6 phiếu thử thiếu giá: không hiện chip hệ số ở thẻ danh sách và trong phiếu', async function () {
    var p = DS_THU_THIEU[0];
    bang('máy chủ trả hệ số kèm trạng thái thiếu giá', [p.he_so != null, p.trang_thai], [true, 'thieu_gia']);
    var m = await moThu({ phieuThieu: true });
    var tThieu = tim(m, '[data-gvtp="GT-2610-004"]')[0], tDu = tim(m, '[data-gvtp="GT-2610-001"]')[0];
    dung('thẻ đủ giá vẫn có chip hệ số', !!tDu.querySelector('[data-gvths]'));
    dung('thẻ thiếu giá không có chip hệ số: ' + chu(tThieu), !tThieu.querySelector('[data-gvths]'));
    dung('thẻ thiếu giá có chip Thiếu giá', chu(tThieu).indexOf('Thiếu giá') >= 0);
    bam(m, tThieu);
    await tick();
    dung('trong phiếu không có chip hệ số: ' + chu(o(m, '#gvtpKq')), !o(m, '#gvtpKq').querySelector('[data-gvths]'));
    dung('trong phiếu vẫn báo thiếu giá', chu(o(m, '#gvtpKq')).indexOf('Thiếu giá 1 nguyên liệu') >= 0);
  });

  /* Codex #486 vòng 6 (P2): AGENTS.md mục 4, chỗ nào có tên món thì có ô ảnh
     món; phiếu thử chưa có ảnh nên giữ ô 🍰 như thẻ món đang bán. */
  await ca('Codex #486 v6 thẻ phiếu thử có ô ảnh món giữ hàng như thẻ món đang bán', async function () {
    var m = await moThu({ phieuThieu: true });
    var ds = tim(m, '[data-gvtp]');
    bang('số thẻ', ds.length, 2);
    ds.forEach(function (t) {
      var dau = t.querySelector('.gvt-dau');
      dung('thẻ ' + t.getAttribute('data-gvtp') + ' có khối đầu', !!dau);
      dung('thẻ ' + t.getAttribute('data-gvtp') + ' có ô ảnh 🍰', !!dau.querySelector('.immp') && chu(dau).indexOf('🍰') >= 0);
    });
  });

  /* Codex #486 vòng 7 (P2, AGENTS.md 2b điều 2): chín nhóm bán là hơn 8 lựa
     chọn, không được bày hàng chip; dùng thẻ giá trị đang chọn mở sheet có ô tìm. */
  await ca('Codex #486 v7 nhóm bán của phiếu thử: thẻ đang chọn mở sheet có ô tìm, không còn hàng chín chip', async function () {
    var m = await moThu();
    m.tai.getElementById('gvtThuMoi').onclick();
    bang('không còn chip nhóm trên màn nhập', tim(m, '[data-gvtpn]').length, 0);
    var the1 = tim(m, '[data-gvtpnhom]');
    bang('một thẻ nhóm', the1.length, 1);
    dung('thẻ nói chưa chọn: ' + chu(the1[0]), chu(the1[0]).indexOf('Chọn nhóm bán') >= 0 && chu(the1[0]).indexOf('Chọn để có giá bán đề xuất') >= 0);
    bam(m, the1[0]);
    var ov = sheetCuoi(m);
    dung('mở sheet có ô tìm', !!ov.querySelector('[data-gvtpntim]'));
    bang('đủ chín nhóm và dòng Chưa chọn', ov.querySelectorAll('[data-gvtpnchon]').length, NHOM_BAN.length + 1);
    go(m, ov.querySelector('[data-gvtpntim]'), 'banh lanh');
    bang('gõ không dấu ra đúng nhóm', ov.querySelectorAll('[data-gvtpnchon]').map(function (e) { return e.getAttribute('data-gvtpnchon'); }), ['Bánh lạnh']);
    dung('dòng nhóm nói hệ số mục tiêu', chu(ov).indexOf('Hệ số mục tiêu x5') >= 0);
    go(m, ov.querySelector('[data-gvtpntim]'), 'khong co nhom nay');
    dung('gõ sai nói rõ', chu(ov).indexOf('Không có nhóm nào khớp.') >= 0);
    go(m, ov.querySelector('[data-gvtpntim]'), 'lanh');
    await ov.onclick({ target: ov.querySelector('[data-gvtpnchon="Bánh lạnh"]') });
    bang('đóng sheet', m.tai.body.children.indexOf(ov), -1);
    bang('phiếu nhận nhóm', m.g.GVT.p.nhom, 'Bánh lạnh');
    var the2 = tim(m, '[data-gvtpnhom]')[0];
    dung('thẻ hiện tên đậm và hệ số: ' + chu(the2), chu(the2).indexOf('Bánh lạnh') >= 0 && chu(the2).indexOf('Hệ số mục tiêu x5') >= 0);
    dung('đánh dấu chưa lưu', m.g.S.chuaLuu.indexOf('chưa bấm Lưu phiếu') >= 0);
    bam(m, the2);
    ov = sheetCuoi(m);
    await ov.onclick({ target: ov.querySelector('[data-gvtpnchon=""]') });
    bang('chọn Chưa chọn nhóm là bỏ nhóm', m.g.GVT.p.nhom, '');
  });

  /* Codex #486 vòng 7 (P2, AGENTS.md 2b điều 3): danh sách phiếu thử có ba
     hàng chip trạng thái có đếm, nhóm có đếm, khoảng ngày; lọc ở máy chủ. */
  function nhanSo(el) { var m2 = /(\d+)$/.exec(chu(el).trim()); return m2 ? +m2[1] : -1; }
  function goiDs(m) { return m.goi.filter(function (x) { return x.duong === 'vagabond.gia_von_tam.ds_thu'; }); }
  await ca('Codex #486 v7 danh sách phiếu thử: ba hàng chip, số trên chip bằng số thẻ khi bấm, lọc ở máy chủ', async function () {
    var m = await moThu({ locNhieu: true });
    var tt = tim(m, '[data-gvtft]'), nh = tim(m, '[data-gvtfn]'), kh = tim(m, '[data-gvtfk]');
    dung('đủ ba hàng chip: ' + [tt.length, nh.length, kh.length], tt.length >= 3 && nh.length >= 3 && kh.length === 4);
    bang('chip Tất cả đếm đủ', nhanSo(tt[0]), 4);
    var chipTt = tt.slice(1).map(function (e) { return [e.getAttribute('data-gvtft'), nhanSo(e)]; });
    dung('có chip Thiếu giá NVL', chipTt.some(function (x) { return x[0] === 'thieu_gia' && x[1] === 1; }));
    for (var i = 0; i < chipTt.length; i++) {
      bam(m, tim(m, '[data-gvtft="' + chipTt[i][0] + '"]')[0]);
      await choDen(function () { return (m.g.GVT.thu || {}).trang_thai === chipTt[i][0]; });
      var g = goiDs(m);
      bang('gửi trạng thái lên máy chủ từ trang đầu', [g[g.length - 1].ts.trang_thai, g[g.length - 1].ts.bat_dau], [chipTt[i][0], 0]);
      var the3 = tim(m, '[data-gvtp]');
      bang('chip ' + chipTt[i][0] + ': số thẻ bằng số trên chip', the3.length, chipTt[i][1]);
      dung('mọi thẻ đúng trạng thái', the3.every(function (e) { return !!e.querySelector('[data-gvttt="' + chipTt[i][0] + '"]'); }));
    }
    bam(m, tim(m, '[data-gvtft="' + chipTt[chipTt.length - 1][0] + '"]')[0]);
    await choDen(function () { return (m.g.GVT.thu || {}).trang_thai === ''; });
    bang('bấm lại chip đang chọn là bỏ lọc trạng thái', tim(m, '[data-gvtp]').length, 4);
    var chua = tim(m, '[data-gvtfn="__chua_nhom"]')[0];
    dung('có chip Chưa chọn nhóm 1', !!chua && nhanSo(chua) === 1);
    bam(m, chua);
    await choDen(function () { return (m.g.GVT.thu || {}).nhom === '__chua_nhom'; });
    bang('lọc nhóm ra đúng phiếu chưa chọn nhóm', tim(m, '[data-gvtp]').map(function (e) { return e.getAttribute('data-gvtp'); }), ['GT-2610-005']);
    var lanh = tim(m, '[data-gvtfn="Bánh lạnh"]')[0];
    bang('chip Bánh lạnh đếm 3', nhanSo(lanh), 3);
    bam(m, lanh);
    await choDen(function () { return (m.g.GVT.thu || {}).nhom === 'Bánh lạnh'; });
    bang('đếm trạng thái theo nhóm đang chọn', nhanSo(tim(m, '[data-gvtft=""]')[0]), 3);
    bam(m, tim(m, '[data-gvtfk="7_ngay"]')[0]);
    await choDen(function () { return (m.g.GVT.thu || {}).khoang === '7_ngay'; });
    var g2 = goiDs(m);
    bang('khoảng ngày gửi lên máy chủ cùng bộ lọc đang có', [g2[g2.length - 1].ts.khoang, g2[g2.length - 1].ts.nhom], ['7_ngay', 'Bánh lạnh']);
    dung('chip khoảng đang chọn tô đậm', tim(m, '[data-gvtfk="7_ngay"]')[0].getAttribute('style').indexOf('font-weight:800') >= 0);
  });

  await ca('Codex #486 v7 Xem thêm đi đúng bộ lọc đang chọn; lọc ra rỗng có nút Bỏ lọc', async function () {
    var m = await moThu({ locNhieu: true, co: 1 });
    bam(m, tim(m, '[data-gvtfn="Bánh lạnh"]')[0]);
    await choDen(function () { return (m.g.GVT.thu || {}).nhom === 'Bánh lạnh'; });
    bang('trang đầu một thẻ', tim(m, '[data-gvtp]').length, 1);
    bam(m, tim(m, '[data-gvtthemds]')[0]);
    await choDen(function () { return tim(m, '[data-gvtp]').length === 2; });
    var g = goiDs(m);
    bang('xem thêm giữ bộ lọc', g[g.length - 1].ts, { tu_khoa: '', bat_dau: 1, trang_thai: '', nhom: 'Bánh lạnh', khoang: '' });
    dung('thẻ nối vào đều thuộc Bánh lạnh', tim(m, '[data-gvtp]').every(function (e) { return chu(e).indexOf('Bánh lạnh') >= 0; }));
    go(m, m.tai.getElementById('gvtThuQ'), 'khong co mon nay');
    await cho(350);
    await choDen(function () { return (m.g.GVT.thu || {}).tu_khoa === 'khong co mon nay'; });
    dung('câu rỗng nói khớp bộ lọc: ' + chu(m.khung), chu(m.khung).indexOf('Không có phiếu nào khớp bộ lọc') >= 0);
    bam(m, tim(m, '[data-gvtthubo]')[0]);
    await choDen(function () { return (m.g.GVT.thu || {}).nhom === ''; });
    var g3 = goiDs(m);
    bang('Bỏ lọc gửi lại không bộ lọc, giữ chữ đang tìm', g3[g3.length - 1].ts, { tu_khoa: 'khong co mon nay', bat_dau: 0, trang_thai: '', nhom: '', khoang: '' });
  });

  /* Codex #486 vòng 8 (P2): hơn 500 phiếu khớp thì máy chủ chỉ lọc trong 500
     phiếu mới sửa nhất. Lọc ra rỗng mà không nói điều đó là bảo sai "không có". */
  await ca('Codex #486 v8 quá 500 phiếu: lọc ra rỗng vẫn nói chỉ lọc trong phiếu gần nhất và chỉ cách thu hẹp', async function () {
    var m = await moThu({ locNhieu: true, vuot: true });
    dung('có thẻ thì có câu giới hạn: ' + chu(m.khung), chu(m.khung).indexOf('Chỉ đếm và lọc trong 500 phiếu sửa gần nhất') >= 0);
    bam(m, tim(m, '[data-gvtft="thieu_gia"]')[0]);
    await choDen(function () { return (m.g.GVT.thu || {}).trang_thai === 'thieu_gia'; });
    go(m, m.tai.getElementById('gvtThuQ'), 'khong co mon nay');
    await cho(350);
    await choDen(function () { return (m.g.GVT.thu || {}).tu_khoa === 'khong co mon nay'; });
    bang('rỗng', tim(m, '[data-gvtp]').length, 0);
    var t = chu(m.khung);
    dung('rỗng vẫn có câu giới hạn: ' + t, t.indexOf('Chỉ đếm và lọc trong 500 phiếu sửa gần nhất') >= 0);
    dung('rỗng chỉ cách thu hẹp: ' + t, t.indexOf('Phiếu cũ hơn có thể khớp') >= 0);
    dung('vẫn có Bỏ lọc', tim(m, '[data-gvtthubo]').length === 1);
  });

  /* Codex #486 vòng 9 (P1, AGENTS.md 2b điều 11): thẻ và màn phiếu có dấu
     vết ai lập, ai sửa, lúc nào, chip "Đã sửa N lần" do máy chủ đếm. */
  await ca('Codex #486 v9 dấu vết phiếu thử: ai lập, ai sửa gần nhất, lúc nào, chip Đã sửa N lần ở thẻ và màn phiếu', async function () {
    var m = await moThu({ vet: true });
    var t1 = tim(m, '[data-gvtp="GT-2610-006"]')[0], t2 = tim(m, '[data-gvtp="GT-2610-007"]')[0];
    var v1 = chu(t1.querySelector('[data-gvtvet]'));
    dung('thẻ sửa nhiều: ' + v1, v1.indexOf('Lập: Khải 16/10 21:00') >= 0 && v1.indexOf('Sửa gần nhất: Loan 17/10 09:30') >= 0);
    bang('chip đếm sửa', chu(t1.querySelector('[data-gvtsua]')), 'Đã sửa 2 lần');
    var v2 = chu(t2.querySelector('[data-gvtvet]'));
    dung('thẻ chưa sửa chỉ có người lập: ' + v2, v2.indexOf('Lập: Khải 17/10 08:05') >= 0 && v2.indexOf('Sửa gần nhất') < 0);
    dung('thẻ chưa sửa không có chip sửa', !t2.querySelector('[data-gvtsua]'));
    bam(m, t1);
    await tick();
    var vf = o(m, '[data-gvtvet]');
    dung('màn phiếu có dấu vết: ' + (vf ? chu(vf) : ''), !!vf && chu(vf).indexOf('Sửa gần nhất: Loan 17/10 09:30') >= 0 && chu(vf).indexOf('Đã sửa 2 lần') >= 0);
    m.g.back(); await tick();
    m.tai.getElementById('gvtThuMoi').onclick();
    dung('phiếu mới chưa có dấu vết', !o(m, '[data-gvtvet]'));
  });

  /* Codex #486 vòng 9 (P1): mã đã có giá danh mục thì máy chủ bỏ qua giá tay
     cũ; màn không hiện ô giá tay cho dòng đó và giá vốn theo giá kho. */
  await ca('Codex #486 v9 mã có giá kho mà còn giá tay cũ: tính theo giá kho, không hiện ô giá tay', async function () {
    var p = DS_THU_VET[0];
    bang('máy chủ dùng giá kho, bỏ giá tay', [p.dong[0].nguon, p.dong[0].don_gia, p.dong[0].tay, p.gia_von], ['Giá kho', 30, 0, 3000]);
    var m = await moThu({ vet: true });
    bam(m, tim(m, '[data-gvtp="GT-2610-006"]')[0]);
    await tick();
    dung('không có ô giá tay ở dòng có giá kho', !o(m, '[data-gvtpgia="0"]'));
    dung('dòng nói nguồn giá kho: ' + chu(o(m, '[data-gvtpgiadong="0"]')), chu(o(m, '[data-gvtpgiadong="0"]')).indexOf('(Giá kho)') >= 0);
    dung('giá vốn theo giá kho: ' + chu(o(m, '#gvtpKq')), chu(o(m, '#gvtpKq')).indexOf('Giá vốn 3.000đ/Cái') >= 0);
  });

  /* Codex #486 vòng 10 (P2): sửa phiếu đã lưu thì kết quả tính thử thay
     GVT.pk mà không có dấu vết; lần vẽ lại cả màn sau đó (xoá dòng, thêm
     dòng, đổi nhóm) làm mất dòng dấu vết. Dấu vết phải giữ riêng. */
  await ca('Codex #486 v10 sửa phiếu đã lưu: tính thử xong rồi vẽ lại cả màn vẫn còn dấu vết', async function () {
    var m = await moThu({ vet: true });
    bam(m, tim(m, '[data-gvtp="GT-2610-006"]')[0]);
    await tick();
    go(m, o(m, '[data-gvtpsl="0"]'), '200');
    await cho(450);
    await choDen(function () { return chu(o(m, '#gvtpKq')).indexOf('Giá vốn 6.000đ/Cái') >= 0; });
    dung('đã tính thử: ' + chu(o(m, '#gvtpKq')), chu(o(m, '#gvtpKq')).indexOf('Giá vốn 6.000đ/Cái') >= 0);
    bam(m, tim(m, '[data-gvtpnhom]')[0]);
    var ov = sheetCuoi(m);
    await ov.onclick({ target: ov.querySelector('[data-gvtpnchon="Bánh khô"]') });
    var vf = o(m, '[data-gvtvet]');
    dung('vẽ lại cả màn vẫn còn dấu vết: ' + (vf ? chu(vf) : 'không có'), !!vf && chu(vf).indexOf('Sửa gần nhất: Loan 17/10 09:30') >= 0 && chu(vf).indexOf('Đã sửa 2 lần') >= 0);
  });

  await ca('v600 chưa có phiếu nào: câu chỉ đường nói nút cần bấm', async function () {
    var m = await moThu({ khongPhieu: true });
    dung('câu rỗng', chu(m.khung).indexOf('Chưa có phiếu tính giá thử nào. Bấm Phiếu tính giá thử mới để bắt đầu.') >= 0);
  });

  console.log('\n' + ket.dat + ' ca dat, ' + ket.hong + ' ca hong.');
  process.exitCode = ket.hong ? 1 : 0;
})().catch(function (e) { console.error(e); process.exitCode = 1; });

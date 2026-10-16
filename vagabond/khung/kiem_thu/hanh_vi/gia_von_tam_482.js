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
function tinhThat() {
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
    'ty_le = {"Bánh ổ sinh nhật": 25}',
    'b = G.dung_bang(ban, ma_bom, ket, gia_ban, {"BAWC00067": ("2026-10-12", 245000)}, ty_le, ten)',
    'b.update({"ty_le": ty_le, "cap_nhat_luc": "09:15", "sua_duoc": True, "ngay": "2026-10-16"})',
    'sys.stdout.write(json.dumps(b, ensure_ascii=False, default=str))',
  ].join('\n');
  return JSON.parse(cp.execFileSync('python3', ['-c', py, GOC], { encoding: 'utf8' }));
}
var TINH = tinhThat();
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
        var d = JSON.parse(JSON.stringify(TINH));
        if (tuyChon.khongSua) d.sua_duoc = false;
        return Promise.resolve(d);
      }
      if (duong === 'vagabond.gia_von_tam.chi_tiet') return Promise.resolve(JSON.parse(JSON.stringify(CHI_TIET[ts.bom || ''])));
      if (duong === 'vagabond.gia_von_tam.luu_ty_le') return Promise.resolve({ ty_le: {} });
      if (duong === 'vagabond.gia_von_tam.chot') return Promise.resolve({ da_luu: 4, bo_qua: { 'Thiếu giá nguyên liệu': 1 } });
      return Promise.reject(new Error('api la: ' + duong));
    },
    confirmSheet: function (t, m) { hoi.push(m); return Promise.resolve(tuyChon.tuChoi ? false : true); },
    toast: function (m) { toastDs.push(m); },
    busy: function () {},
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
    dung('Shiopan chip tỷ lệ 583,4%', chu(shio).indexOf('583,4%') >= 0);
    var roman = tim(m, '[data-gvtm="BAWC00067"]')[0];
    dung('Roman giá vốn và giá bán', chu(roman).indexOf('Giá vốn 250.959đ · Giá bán 880.000đ') >= 0);
    dung('Roman đề xuất làm tròn lên', chu(roman).indexOf('Đề xuất 1.004.000đ (mục tiêu 25%)') >= 0);
    dung('Roman lần chốt trước', chu(roman).indexOf('Lần chốt 12/10: 245.000đ (+2,4%)') >= 0);
    dung('món chưa đặt mục tiêu nói rõ', chu(tim(m, '[data-gvtm="BAEN00073"]')[0]).indexOf('Chưa đặt tỷ lệ mục tiêu') >= 0);
    dung('có nút Chốt', !!m.tai.getElementById('gvtChot'));
    dung('món chưa công thức không thành thẻ', the(m).indexOf('BAEN00051') < 0);
  });

  await ca('thẻ thiếu giá: đúng chữ, tối đa hai tên rồi "và N nữa", không có giá đề xuất', async function () {
    var m = await moMan();
    var t = chu(tim(m, '[data-gvtm="BANU00099"]')[0]);
    dung('câu thiếu giá: ' + t, t.indexOf('Thiếu giá 3 nguyên liệu: BTP Brown Butter, BTP Thịt bí và 1 nữa') >= 0);
    dung('không đề xuất giá', t.indexOf('Đề xuất') < 0);
  });

  await ca('chip nhóm và chip trạng thái: số trên chip đúng, bấm là lọc, bấm lại chip trạng thái là bỏ lọc', async function () {
    var m = await moMan();
    var chipN = tim(m, '[data-gvtn]').map(function (e) { return chu(e); });
    bang('chip nhóm', chipN, ['Tất cả 5', 'Bánh ổ 1', 'Bánh lạnh 1', 'Bánh nướng 2', 'Bánh khô 1']);
    var chipT = tim(m, '[data-gvtt]').map(function (e) { return chu(e); });
    bang('chip trạng thái chỉ hiện chip có số', chipT, ['Vượt giá bán 1', 'Thiếu giá NVL 1', 'Cao hơn mục tiêu 1']);
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

  await ca('sheet tỷ lệ: ô ngoài 1..95 bị chặn tại chỗ không gửi; lưu gửi đúng dict rồi tải lại', async function () {
    var m = await moMan();
    bam(m, tim(m, '[data-gvttyle]')[0]);
    var ov = sheetCuoi(m);
    var o = function (n) { return ov.querySelector('[data-gvtpct="' + n + '"]'); };
    dung('có ô cho nhóm Bánh ổ, đã điền 25', o('Bánh ổ sinh nhật') && o('Bánh ổ sinh nhật').value === '25');
    dung('gợi ý trung vị', chu(ov).indexOf('Hiện trung vị') >= 0);
    o('Bánh lạnh').value = '0';
    await ov.onclick({ target: ov.querySelector('[data-gvtluu]') });
    bang('chưa gửi', goiTen(m).filter(function (x) { return x.indexOf('luu_ty_le') >= 0; }).length, 0);
    dung('báo sai tại chỗ', chu(ov.querySelector('[data-gvtsai="Bánh lạnh"]')).indexOf('Nhập số từ 1 tới 95.') >= 0);
    o('Bánh lạnh').value = '15,5';
    o('Bánh ổ sinh nhật').value = '';
    await ov.onclick({ target: ov.querySelector('[data-gvtluu]') });
    await tick();
    var g = m.goi.filter(function (x) { return x.duong === 'vagabond.gia_von_tam.luu_ty_le'; });
    bang('gửi một lần', g.length, 1);
    bang('đúng dict', JSON.parse(g[0].ts.ty_le), { 'Bánh ổ sinh nhật': '', 'Bánh lạnh': 15.5, 'Bánh nướng': '', 'Bánh khô': '' });
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

  await ca('không có quyền chốt: không thấy nút Chốt, không thấy nút Tỷ lệ mục tiêu', async function () {
    var m = await moMan({ khongSua: true });
    dung('không nút chốt', !m.tai.getElementById('gvtChot'));
    bang('không nút tỷ lệ', tim(m, '[data-gvttyle]').length, 0);
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

  console.log('\n' + ket.dat + ' ca dat, ' + ket.hong + ' ca hong.');
  process.exitCode = ket.hong ? 1 : 0;
})().catch(function (e) { console.error(e); process.exitCode = 1; });

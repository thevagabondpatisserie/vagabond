/* Bo ca kiem HANH VI v574: phien dang nhap mat giua chung thi dua ve man dang nhap.
 *
 * Ca that Loan Anh 05/10/2026, man Cong no, phieu APP-26-10-132: dinh anh UNC
 * thi hien "UNC.jpg: You are not permitted to access this resource. Login to
 * accessFunction vagabond.tep_dinh_kem.nap_tam is not whitelisted". Ham co
 * quyen goi du. Tai khoan chi cho 2 phien cung luc, hom do dang nhap 3 lan nen
 * phien cua may dang mo man bi day vang. Frappe tra 403 PermissionError cho
 * khach chu khong phai 401, app tuong la thieu quyen.
 *
 * Nap THAT rawCall, api, srvErr, phienDaMat, sessionGone (00-nen.js) va
 * tdkMotTep (43-tep-dinh-kem.js). Chi chan mang (fetch) va buoc nen anh
 * (tdkNen can canvas). Khong goi ham nao ngoai chuoi: chon tep -> gui tep.
 *
 * Than tra loi 403 o ca 1 chep tu site that 05/10/2026 (goi nap_tam khong
 * kem cookie), ban tieng Viet, de chot rang phep do KHONG dua vao chu.
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/phien_mat_574.js
 */
'use strict';
var fs = require('fs');
var path = require('path');
var vm = require('vm');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
var NEN = fs.readFileSync(path.join(BEP, '00-nen.js'), 'utf8');
var TDK = fs.readFileSync(path.join(BEP, '43-tep-dinh-kem.js'), 'utf8');

function layHam(src, ten) {
  var dau = src.indexOf('function ' + ten + '(');
  if (dau < 0) throw new Error('Khong thay ham ' + ten);
  if (src.indexOf('function ' + ten + '(', dau + 1) >= 0) throw new Error('Ham ' + ten + ' co hai ban');
  if (src.slice(Math.max(0, dau - 6), dau) === 'async ') dau -= 6;
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Ham ' + ten + ' khong dong ngoac');
}
function layDong(src, dau) {
  var i = src.indexOf(dau);
  if (i < 0) throw new Error('Khong thay dong ' + dau);
  return src.slice(i, src.indexOf('\n', i));
}

var ket = { dat: 0, hong: 0, loi: [] };
/* Codex #441: lời hứa treo mãi thì node tự thoát với mã 0 mà không in gì,
   cổng kiểm tưởng là đạt. Chưa chạy tới cuối thì coi là hỏng. */
var xongHet = false;
process.on('exit', function () {
  if (!xongHet) { console.log('  HONG  bo kiem dung giua chung: co loi hua treo mai (mang treo khong het han)'); process.exitCode = 1; }
});
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
function dung(mo, v) { if (!v) throw new Error(mo); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; }
  catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n         ') : String(e))); }
}

var THAN_KHACH = JSON.stringify({
  exc_type: 'PermissionError',
  _server_messages: JSON.stringify([JSON.stringify({
    message: 'Bạn không được phép truy cập tài nguyên này. Đăng nhập để truy cậpHàm <strong>vagabond.tep_dinh_kem.nap_tam</strong> chưa được whitelist.',
    title: 'Phương thức không được phép', indicator: 'red', raise_exception: 1
  })])
});
var THAN_THIEU_QUYEN = JSON.stringify({
  exc_type: 'PermissionError',
  _server_messages: JSON.stringify([JSON.stringify({ message: 'Không đủ quyền đọc Payment Entry' })])
});

function traLoi(status, than) {
  return { status: status, ok: status >= 200 && status < 300, text: async function () { return than; } };
}

/* toi: ham (url) -> traLoi(...) hoac nem loi mang. */
function dung_trang(toi) {
  var goi = [], ve = [], gio = [];
  var g = {
    JSON: JSON, Error: Error, Date: Date, location: { pathname: '/bep' },
    /* Đồng hồ tua tay: hẹn giờ chỉ chạy khi ca kiểm gọi tuaGio(). */
    setTimeout: function (f) { gio.push(f); return gio.length; }, clearTimeout: function () {},
    AbortController: undefined, window: {},
    busy: function () {}, scrLogin: function scrLogin() {},
    reset: function (s) { ve.push(s && s.name); },
    fetch: async function (url, o) { goi.push(url); return toi(url, o); },
    tdkNen: function (f, ok) { ok('QUJD', f.name); }
  };
  g.window = g;
  vm.createContext(g);
  vm.runInContext([
    layDong(NEN, 'var CSRFT ='), layHam(NEN, 'csrfTok'), layDong(NEN, 'var csrfJob ='), layHam(NEN, 'refreshCsrf'),
    layDong(NEN, 'var goneOnce ='), layHam(NEN, 'sessionGone'), layHam(NEN, 'srvErr'),
    layDong(NEN, 'var API_HAN_GIO ='), layHam(NEN, 'rawCall'),
    layDong(NEN, 'var PHIEN_MAT_CAU ='), layDong(NEN, 'var PHIEN_HOI_HAN ='), layHam(NEN, 'phienHetGio'),
    layHam(NEN, 'phienDaMat'), layHam(NEN, 'api'),
    layHam(TDK, 'tdkMotTep')
  ].join('\n'), g);
  return { g: g, goi: goi, ve: ve, tuaGio: function () { while (gio.length) gio.shift()(); } };
}

async function choXong() { for (var i = 0; i < 5; i++) await new Promise(function (r) { setImmediate(r); }); }
/* Gửi tệp, cho mạng giả trả lời xong rồi mới tua đồng hồ: hẹn giờ không được
   chen trước một câu trả lời đã có (ca đó sẽ che lỗi, điều 15). */
async function guiTep(t) {
  var p = t.g.tdkMotTep({ name: 'UNC.jpg' }, 'APP-26-10-132').then(function () { return null; }, function (e) { return e; });
  await choXong();
  t.tuaGio();
  var e = await p;
  t.tuaGio();
  return e;
}

(async function () {
  await ca('Loan Anh 05/10: phien bi day vang, dinh UNC thi ve man dang nhap voi cau de hieu', async function () {
    var t = dung_trang(function (u) {
      if (u.indexOf('nap_tam') >= 0) return traLoi(403, THAN_KHACH);
      if (u.indexOf('get_logged_user') >= 0) return traLoi(403, THAN_KHACH.replace('vagabond.tep_dinh_kem.nap_tam', 'frappe.auth.get_logged_user'));
      throw new Error('mang la ' + u);
    });
    var e = await guiTep(t);
    dung('gui tep phai bao loi', e);
    dung('cau bao noi ro phien da het: ' + e.message, e.message.indexOf('Phiên đăng nhập đã hết') === 0);
    dung('khong con chu whitelist', e.message.indexOf('whitelist') < 0);
    bang('dua ve man dang nhap dung mot lan', t.ve, ['scrLogin']);
    bang('hoi may chu toi la ai dung mot lan', t.goi.filter(function (u) { return u.indexOf('get_logged_user') >= 0; }).length, 1);
  });
  await ca('may chu tra Guest (200) cung la phien da mat', async function () {
    var t = dung_trang(function (u) {
      if (u.indexOf('nap_tam') >= 0) return traLoi(403, THAN_KHACH);
      return traLoi(200, '{"message":"Guest"}');
    });
    var e = await guiTep(t);
    dung('cau bao phien het', e && e.message.indexOf('Phiên đăng nhập đã hết') === 0);
    bang('ve man dang nhap', t.ve, ['scrLogin']);
  });
  await ca('con dang nhap ma thieu quyen that: giu nguyen loi cu, khong da ra man dang nhap', async function () {
    var t = dung_trang(function (u) {
      if (u.indexOf('nap_tam') >= 0) return traLoi(403, THAN_THIEU_QUYEN);
      return traLoi(200, '{"message":"ntla.3008@gmail.com"}');
    });
    var e = await guiTep(t);
    bang('loi cu', e && e.message, 'Không đủ quyền đọc Payment Entry');
    bang('khong ve man dang nhap', t.ve, []);
  });
  await ca('mat mang luc hoi toi la ai: khong doan la het phien, giu loi cu', async function () {
    var t = dung_trang(function (u) {
      if (u.indexOf('nap_tam') >= 0) return traLoi(403, THAN_THIEU_QUYEN);
      throw new Error('mat mang');
    });
    var e = await guiTep(t);
    bang('loi cu', e && e.message, 'Không đủ quyền đọc Payment Entry');
    bang('khong ve man dang nhap', t.ve, []);
  });
  await ca('loi khac 403 (417 du lieu sai) khong hoi them may chu', async function () {
    var t = dung_trang(function (u) {
      if (u.indexOf('nap_tam') >= 0) return traLoi(417, JSON.stringify({ exc_type: 'ValidationError', _server_messages: JSON.stringify([JSON.stringify({ message: 'Tệp quá lớn' })]) }));
      throw new Error('khong duoc goi ' + u);
    });
    var e = await guiTep(t);
    bang('loi cu', e && e.message, 'Tệp quá lớn');
    bang('chi mot loi goi', t.goi.length, 1);
    bang('khong ve man dang nhap', t.ve, []);
  });
  await ca('403 khong phai PermissionError (tuong lua, trang HTML) khong hoi them may chu', async function () {
    var t = dung_trang(function (u) {
      if (u.indexOf('nap_tam') >= 0) return traLoi(403, '<html>Forbidden</html>');
      throw new Error('khong duoc goi ' + u);
    });
    var e = await guiTep(t);
    bang('cau mac dinh 403', e && e.message, 'Không đủ quyền thao tác');
    bang('chi mot loi goi', t.goi.length, 1);
  });
  await ca('Codex #441: hoi toi la ai ma mang treo thi het han, giu loi cu, khong dung man mai', async function () {
    var t = dung_trang(function (u) {
      if (u.indexOf('nap_tam') >= 0) return traLoi(403, THAN_THIEU_QUYEN);
      return new Promise(function () {});
    });
    var e = await guiTep(t);
    bang('loi cu', e && e.message, 'Không đủ quyền đọc Payment Entry');
    bang('khong ve man dang nhap', t.ve, []);
  });
  await ca('Codex #441: tra dau roi treo luc doc than cung het han', async function () {
    var t = dung_trang(function (u) {
      if (u.indexOf('nap_tam') >= 0) return traLoi(403, THAN_THIEU_QUYEN);
      return { status: 200, ok: true, text: function () { return new Promise(function () {}); } };
    });
    var e = await guiTep(t);
    bang('loi cu', e && e.message, 'Không đủ quyền đọc Payment Entry');
  });
  await ca('401 van ve man dang nhap nhu truoc', async function () {
    var t = dung_trang(function () { return traLoi(401, '{}'); });
    var e = await guiTep(t);
    dung('co loi', e);
    bang('ve man dang nhap', t.ve, ['scrLogin']);
  });
  console.log('Bo ca kiem HANH VI v574: phien dang nhap mat giua chung (Loan Anh, man Cong no)');
  ket.loi.forEach(function (d) { console.log('  HONG  ' + d); });
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  xongHet = true;
  process.exit(ket.hong ? 1 : 0);
})();

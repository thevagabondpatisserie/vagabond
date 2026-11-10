/* Ca kiểm HÀNH VI v647 (anh Việt 10/11/2026): tên bàn theo khu và tờ in QR
 * đúng branding.
 *
 *  1. Màn In QR tại bàn: quản lý khai sơ đồ bàn (khu A 1..12, B 1..8, VIP 1..2),
 *     Lưu; tích bàn theo khu; chọn kích thước standee (mica 7 x 7 cm, A6, tự
 *     nhập); Tạo mã QR; In: các miếng dàn lên trang A4 có dấu cắt, mã đậm trên
 *     ô trắng, nhãn "BÀN A1".
 *  2. Đổi sơ đồ làm mất bàn đã in: máy hỏi lại, chỉ lưu khi bấm Vẫn lưu.
 *  3. Màn Tính tiền: chip Số bàn chia theo khu, cùng sơ đồ.
 *  4. Trang khách: link QR mang tên bàn theo khu đọc đúng (docLinkBan).
 *
 * CHẠY THẬT 66-goi-mon-tai-ban.js và posVeSoBan, posNhomBan, posChipNut của
 * 09, thư viện qrcode thật, bốn khuôn SVG thật trong public/images/qr-ban.
 * Máy chủ là bản giả ghi lời gọi; luật sơ đồ ở máy chủ kiểm trong
 * thu_qr_ban_khu_647.py.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/qr_ban_khu_647.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var PUB = path.join(GOC, 'vagabond', 'public');
var BEP = path.join(PUB, 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
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
var NEN = doc('00-nen.js'), POS = doc('09-tinh-tien-quay.js'), IN = doc('27-in-ngam.js'), GMB = doc('66-goi-mon-tai-ban.js');
var MA = layHam(NEN, 'h') + '\n' + ['posChipNut', 'posVeSoBan', 'posNhomBan'].map(function (t) { return layHam(POS, t); }).join('\n') + '\n' +
  /var IN_VENDOR = [\s\S]*?\};\n/.exec(IN)[0] + layHam(IN, 'inNapJs') + '\nvar inDaNap = {};\n' + GMB;
var QR_LIB = fs.readFileSync(path.join(PUB, 'js', 'vendor', 'qrcode.js'), 'utf8');

var ket = { dat: 0, hong: 0, loi: [] };
function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 4).join('\n         ') : String(e))); }
}
async function nghi(n) { for (var k = 0; k < (n || 3); k++) { for (var i = 0; i < 12; i++) await Promise.resolve(); await new Promise(function (r) { setImmediate(r); }); } }
function chu(el) { var s = el._chu || ''; (el.children || []).forEach(function (c) { s += chu(c); }); return s; }

/* Máy chủ giả: dựng nhóm bàn từ sơ đồ y như so_do_ban.nhom_ban. */
function nhomTu(soDo) {
  var ra = [];
  (soDo || []).forEach(function (d) {
    var g = ra.filter(function (x) { return x.khu === d.khu; })[0];
    if (!g) { g = { khu: d.khu, ban: [] }; ra.push(g); }
    for (var n = d.tu; n <= d.den; n++) g.ban.push(d.khu + n);
  });
  return ra.length ? ra : [{ khu: '', ban: Array.from({ length: 20 }, function (_, i) { return String(i + 1); }) }];
}
function diemGia(ma, soDo, dc) {
  return { ma: ma, ten: ma === 'TCV' ? 'District 1' : 'NVHTN', phu: '', so_do: soDo || [], nhom: nhomTu(soDo), da_khai: soDo && soDo.length ? 1 : 0, dia_chi_qr: dc || '' };
}
var SO_DO = [{ khu: 'A', tu: 1, den: 12 }, { khu: 'B', tu: 1, den: 8 }, { khu: 'VIP', tu: 1, den: 2 }];

function khoi(o) {
  o = o || {};
  var tai = dg.taiLieuGia();
  var goi = [], tin = [], cuaSo = [], hoi = [], tai_ve = [];
  var dsDiem = o.ds || [diemGia('TCV', null, '9 Tran Cao Van, Sai Gon Ward'), diemGia('NVHTN', SO_DO, '21 Pham Ngoc Thach')];
  var g = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object, Error: Error,
    RegExp: RegExp, Promise: Promise, Number: Number, Date: Date, isNaN: isNaN, parseInt: parseInt, Uint8Array: Uint8Array,
    setTimeout: setTimeout, clearTimeout: clearTimeout, location: { origin: 'https://vagabond.s.frappe.cloud' },
    busy: function () {}, toast: function (s) { tin.push(String(s)); },
    hoiCo: function (t, nd, ok) { hoi.push({ t: t, nd: nd, ok: ok }); return Promise.resolve(o.traLoi !== undefined ? o.traLoi : true); },
    frame: function (tieuDe, html, opt) {
      tai.body.children = tai.body.children.filter(function (c) { return c.getAttribute('id') === 'gmbKhuonDom'; });
      var vb = new dg.ElementGia('div'); vb.setAttribute('id', 'vgbBody');
      vb.innerHTML = html + ((opt && opt.footer) || '');
      tai.body.appendChild(vb);
      return vb;
    },
    fetch: function (u) {
      tai_ve.push(u);
      var m = /\/assets\/vagabond\/images\/qr-ban\/(\w+)\.svg$/.exec(u);
      if (!m || o.khuonHong) return Promise.resolve({ ok: false, text: function () { return Promise.resolve(''); } });
      var t = fs.readFileSync(path.join(PUB, 'images', 'qr-ban', m[1] + '.svg'), 'utf8');
      return Promise.resolve({ ok: true, text: function () { return Promise.resolve(t); } });
    },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: JSON.parse(JSON.stringify(ts || {})) });
      if (duong === 'vagabond.goi_mon_ban.diem_in_qr') return Promise.resolve(JSON.parse(JSON.stringify(dsDiem)));
      if (duong === 'vagabond.goi_mon_ban.luu_so_do_ban') {
        if (o.mat && !ts.dong_y_mat) return Promise.resolve({ ok: 0, mat: o.mat });
        var sd = ts.so_do.filter(function (r) { return r.khu || r.tu; }).map(function (r) {
          return { khu: String(r.khu).toUpperCase(), tu: Number(r.tu), den: Number(r.den) };
        });
        return Promise.resolve({ ok: 1, diem: diemGia(ts.diem, sd, ts.dia_chi_qr) });
      }
      if (duong === 'vagabond.goi_mon_ban.to_qr') {
        return Promise.resolve({ diem: ts.diem, ten: 'District 1', dia_chi_qr: '9 Tran Cao Van, Sai Gon Ward',
          to: ts.ban.map(function (b) { return { ban: b, nhan: 'BÀN ' + b, ten_diem: 'District 1', link: 'https://order.thevagabondpatisserie.com/banh?diem=' + ts.diem + '&ban=' + b + '&k=0123456789abcdef#/in-store' }; }) });
      }
      return Promise.reject(new Error('api la: ' + duong));
    }
  };
  g.window = g;
  g.window.open = function () {
    if (o.chanPopup) return null;
    var w = { doc: '', document: { write: function (s) { w.doc += s; }, close: function () {} } }; cuaSo.push(w); return w;
  };
  /* Nạp thư viện QR như thẻ script của inNapJs. */
  tai.createElement = (function (cu) {
    return function (ten) {
      var el = cu ? cu.call(tai, ten) : new dg.ElementGia(ten);
      if (ten === 'script') setTimeout(function () { vm.runInContext(QR_LIB, g); if (el.onload) el.onload(); }, 0);
      return el;
    };
  })(tai.createElement);
  if (!tai.head) tai.head = new dg.ElementGia('head');
  vm.createContext(g);
  vm.runInContext(MA, g, { filename: 'qr-ban-khu.js' });
  return { g: g, tai: tai, goi: goi, tin: tin, cuaSo: cuaSo, hoi: hoi, tai_ve: tai_ve };
}
function than(m) { return m.tai.getElementById('vgbBody'); }
async function bam(m, chon) {
  var b = than(m), el = b.querySelector(chon);
  if (!el) throw new Error('khong thay ' + chon);
  b.dispatchEvent(dg.suKien('click', {}, el));
  await nghi();
}
async function go(m, chon, gt) {
  /* DOM giả chỉ hiểu một bộ chọn thuộc tính: ô sơ đồ ghi "dòng/trường". */
  var sd = /^sd:(\d+):(\w+)$/.exec(chon);
  var el = sd ? than(m).querySelectorAll('[data-gqsd="' + sd[1] + '"]').filter(function (x) { return x.getAttribute('data-k') === sd[2]; })[0]
    : than(m).querySelector(chon);
  if (!el) throw new Error('khong thay o ' + chon);
  el.value = gt;
  than(m).dispatchEvent(dg.suKien('input', {}, el));
}
function cuaGoi(m, d) { return m.goi.filter(function (x) { return x.duong === d; }); }
async function moMan(o) { var m = khoi(o); await m.g.scrGmbInQr(); await nghi(); return m; }
async function nutChan(m, id) { var el = m.tai.getElementById(id); if (!el) throw new Error('khong thay nut ' + id); await el.onclick(); await nghi(4); }

(async function () {
  console.log('v647 In QR tại bàn theo khu, tờ in branding, chip Số bàn theo khu');

  await ca('điểm chưa khai sơ đồ: mở thẳng ô khai; gõ ba khu A, B, vip thì dòng giải thích ra đúng tên bàn; Lưu gửi đủ sơ đồ và địa chỉ', async function () {
    var m = await moMan();
    dung('đang ở chế độ khai (nút Lưu sơ đồ bàn)', !!than(m).querySelector('#gqLuu'));
    dung('chưa có nút Tạo khi đang khai', !m.tai.getElementById('gqTao'));
    await go(m, 'sd:0:tu', '1');
    await go(m, 'sd:0:den', '12');
    bang('dòng 1', chu(m.tai.getElementById('gqMt0')), 'A1 đến A12 · 12 bàn');
    await bam(m, '#gqThem');
    await go(m, 'sd:1:khu', 'B');
    await go(m, 'sd:1:den', '8');
    await bam(m, '#gqThem');
    await go(m, 'sd:2:khu', 'vip');
    await go(m, 'sd:2:tu', '1');
    await go(m, 'sd:2:den', '2');
    bang('dòng 3 chữ thường vẫn ra tên chuẩn', chu(m.tai.getElementById('gqMt2')), 'VIP1, VIP2 · 2 bàn');
    await go(m, 'sd:2:khu', 'V1');
    dung('khu có chữ số thì báo đỏ', chu(m.tai.getElementById('gqMt2')).indexOf('chữ không dấu') >= 0);
    await go(m, 'sd:2:khu', 'vip');
    await go(m, '#gqDc', '9 Tran Cao Van, Sai Gon Ward');
    m.tai.getElementById('gqLuu').onclick(); await nghi(4);
    var l = cuaGoi(m, 'vagabond.goi_mon_ban.luu_so_do_ban');
    bang('một lần lưu', l.length, 1);
    bang('gửi đúng', l[0].ts, { diem: 'TCV', so_do: [{ khu: 'A', tu: '1', den: '12' }, { khu: 'B', tu: 1, den: '8' }, { khu: 'vip', tu: '1', den: '2' }],
      dia_chi_qr: '9 Tran Cao Van, Sai Gon Ward', dong_y_mat: 0 });
    dung('lưu xong về màn chọn bàn', !!m.tai.getElementById('gqTao') && !than(m).querySelector('#gqLuu'));
    dung('báo màn Tính tiền dùng chung', m.tin.some(function (t) { return t.indexOf('Màn Tính tiền dùng sơ đồ này') >= 0; }));
  });

  await ca('chọn bàn theo khu: mặc định chọn hết; Bỏ chọn cả khu B, bỏ VIP1; mica 7 x 7 cm dàn 8 miếng một trang', async function () {
    var m = await moMan();
    await bam(m, '[data-gqdiem="NVHTN"]');
    var b = than(m);
    bang('ba nhóm', b.querySelectorAll('[data-gqkhu]').map(function (x) { return x.getAttribute('data-gqkhu'); }), ['A', 'B', 'VIP']);
    bang('22 bàn đang chọn', chu(m.tai.getElementById('gqTao')), 'Tạo 22 mã QR');
    await bam(m, '[data-gqkhu="B"]');
    await bam(m, '[data-gqban="VIP1"]');
    bang('còn 13 bàn', chu(m.tai.getElementById('gqTao')), 'Tạo 13 mã QR');
    bang('nút khu B đổi chữ', chu(than(m).querySelector('[data-gqkhu="B"]')), 'Chọn cả khu');
    var x = chu(m.tai.getElementById('gqXep'));
    dung('câu dàn trang: ' + x, x.indexOf('Một trang A4 dàn được 8 miếng 7 x 7 cm, 13 bàn cần 2 trang') === 0);
  });

  await ca('Tạo mã QR rồi In: gửi đúng danh sách bàn; tệp in 2 trang A4, 13 miếng, mã đậm trên ô trắng, nhãn BÀN A1, dấu cắt, chờ phông rồi in', async function () {
    var m = await moMan();
    await bam(m, '[data-gqdiem="NVHTN"]');
    await bam(m, '[data-gqkhu="B"]');
    await bam(m, '[data-gqban="VIP1"]');
    await nutChan(m, 'gqTao');
    var t = cuaGoi(m, 'vagabond.goi_mon_ban.to_qr');
    bang('gửi bàn đã tích, đúng thứ tự sơ đồ', t[0].ts, { diem: 'NVHTN', ban: ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11', 'A12', 'VIP2'] });
    bang('tải đủ bốn khuôn', m.tai_ve.map(function (u) { return u.split('/').pop(); }).sort(), ['chu.svg', 'doc.svg', 'logo.svg', 'nen.svg']);
    dung('khuôn gắn một lần vào trang', !!m.tai.getElementById('gmbKhuonDom'));
    var nut = m.tai.getElementById('gqIn');
    bang('nút in', chu(nut), 'In 13 miếng trên 2 trang A4');
    nut.onclick();
    var w = m.cuaSo[m.cuaSo.length - 1];
    bang('2 trang A4', (w.doc.match(/<section class="a4">/g) || []).length, 2);
    bang('13 miếng', (w.doc.match(/<use href="#gmbLogo"/g) || []).length, 13);
    dung('bố cục vuông cho 7 x 7 cm (không dùng khuôn dọc)', w.doc.indexOf('<use href="#gmbDoc"') < 0);
    dung('đủ bốn khuôn trong tệp', ['gmbDoc', 'gmbNen', 'gmbLogo', 'gmbChu'].every(function (id) { return w.doc.indexOf('<symbol id="' + id + '"') >= 0; }));
    dung('nhãn BÀN A1, BÀN VIP2', w.doc.indexOf('>BÀN A1<') >= 0 && w.doc.indexOf('>BÀN VIP2<') >= 0 && w.doc.indexOf('>BÀN VIP1<') < 0);
    dung('mã đậm trên ô trắng', w.doc.indexOf('fill="#fff" stroke="#A0D9D7"') >= 0 && w.doc.indexOf('<path fill="#245f5c" d="M') >= 0);
    dung('khổ A4, cắt theo dấu', w.doc.indexOf('size:A4 portrait') >= 0 && (w.doc.match(/border-left:\.2mm solid #000/g) || []).length >= 6);
    dung('miếng đúng 70 x 70 mm', w.doc.indexOf('width:70mm;height:70mm') >= 0);
    dung('phông thương hiệu, chờ nạp rồi in', w.doc.indexOf('VagabondSans-Regular.otf') >= 0 && w.doc.indexOf('document.fonts') >= 0 && w.doc.indexOf('window.print') >= 0);
    dung('xem trước có miếng', than(m).querySelectorAll('svg').length >= 12);
  });

  await ca('mã QR trong tệp in đọc ra đúng link của bàn (giải lại ma trận ô đậm)', async function () {
    var m = await moMan();
    await bam(m, '[data-gqdiem="NVHTN"]');
    await m.g.gmbNapKhuon();
    var link = 'https://order.thevagabondpatisserie.com/banh?diem=NVHTN&ban=A1&k=0123456789abcdef#/in-store';
    var p = m.g.gmbQrPath(link, 0, 0, 100);
    var q = m.g.qrcode(0, 'M'); q.addData(link, 'Byte'); q.make();
    var n = q.getModuleCount(), o = 0;
    for (var r = 0; r < n; r++) for (var k = 0; k < n; k++) if (q.isDark(r, k)) o++;
    bang('số ô đậm vẽ ra bằng số ô của mã', (p.match(/M/g) || []).length, o);
    dung('ô đầu ở góc trên trái (mắt định vị)', p.indexOf('M0.000 0.000h') === 0);
  });

  await ca('A6 dọc: khuôn dọc, có địa chỉ; tự nhập 30 mm thì không tạo; trình duyệt chặn popup thì báo', async function () {
    var m = await moMan();
    await bam(m, '[data-gqdiem="NVHTN"]');
    await bam(m, '[data-gqkt="105x148"]');
    dung('câu dàn A6', chu(m.tai.getElementById('gqXep')).indexOf('dàn được 2 miếng 10,5 x 14,8 cm') >= 0);
    await nutChan(m, 'gqTao');
    m.tai.getElementById('gqIn').onclick();
    var w = m.cuaSo[m.cuaSo.length - 1];
    dung('khuôn dọc', w.doc.indexOf('<use href="#gmbDoc"') >= 0);
    dung('địa chỉ dưới standee', w.doc.indexOf('9 Tran Cao Van, Sai Gon Ward</text>') >= 0);
    bang('22 bàn trên 11 trang', (w.doc.match(/<section class="a4">/g) || []).length, 11);
    await bam(m, '[data-gqkt="tu"]');
    await go(m, '#gqW', '30');
    dung('câu báo kích thước', chu(m.tai.getElementById('gqXep')).indexOf('Kích thước từ 40 x 40 mm') === 0);
    var soCua = m.cuaSo.length;
    m.tai.getElementById('gqIn').onclick();
    bang('đã có mã mà kích thước sai: không mở cửa sổ in', m.cuaSo.length, soCua);
    dung('báo kích thước', m.tin.some(function (t) { return t.indexOf('Kích thước standee từ 40 x 40 mm') === 0; }));
    var n = await moMan();
    await bam(n, '[data-gqdiem="NVHTN"]');
    await bam(n, '[data-gqkt="tu"]');
    await go(n, '#gqW', '30');
    await nutChan(n, 'gqTao');
    bang('chưa có mã mà kích thước sai: không gọi máy chủ', cuaGoi(n, 'vagabond.goi_mon_ban.to_qr').length, 0);
    var c = await moMan({ chanPopup: 1 });
    await bam(c, '[data-gqdiem="NVHTN"]');
    await nutChan(c, 'gqTao');
    c.tai.getElementById('gqIn').onclick();
    dung('báo chặn popup', c.tin.some(function (t) { return t.indexOf('chặn cửa sổ in') >= 0; }));
  });

  await ca('không tải được khuôn in: báo lỗi, không hiện nút In; bỏ hết bàn thì không gọi máy chủ', async function () {
    var m = await moMan({ khuonHong: 1 });
    await bam(m, '[data-gqdiem="NVHTN"]');
    await nutChan(m, 'gqTao');
    dung('báo lỗi', m.tin.some(function (t) { return t.indexOf('Không tải được mẫu in') >= 0; }));
    dung('không có nút In', !m.tai.getElementById('gqIn'));
    var k = await moMan();
    await bam(k, '[data-gqdiem="NVHTN"]');
    ['A', 'B', 'VIP'].forEach(function () {});
    await bam(k, '[data-gqkhu="A"]'); await bam(k, '[data-gqkhu="B"]'); await bam(k, '[data-gqkhu="VIP"]');
    await nutChan(k, 'gqTao');
    bang('không gọi to_qr', cuaGoi(k, 'vagabond.goi_mon_ban.to_qr').length, 0);
    dung('báo chọn bàn', k.tin.indexOf('Chọn ít nhất một bàn để in.') >= 0);
  });

  await ca('sửa sơ đồ làm mất bàn đã in: máy hỏi lại; Thôi thì không lưu, Vẫn lưu thì gửi đồng ý', async function () {
    var m = await moMan({ mat: ['VIP1', 'VIP2'], traLoi: false });
    await bam(m, '[data-gqdiem="NVHTN"]');
    await bam(m, '#gqSua');
    await bam(m, '[data-gqxoa="2"]');
    m.tai.getElementById('gqLuu').onclick(); await nghi(4);
    bang('hỏi một lần', m.hoi.length, 1);
    dung('nêu bàn sẽ mất', m.hoi[0].nd.indexOf('VIP1, VIP2') >= 0 && m.hoi[0].nd.indexOf('phải in lại') >= 0);
    bang('Thôi: chỉ một lần gọi', cuaGoi(m, 'vagabond.goi_mon_ban.luu_so_do_ban').map(function (x) { return x.ts.dong_y_mat; }), [0]);
    var c = await moMan({ mat: ['VIP1', 'VIP2'], traLoi: true });
    await bam(c, '[data-gqdiem="NVHTN"]');
    await bam(c, '#gqSua');
    await bam(c, '[data-gqxoa="2"]');
    c.tai.getElementById('gqLuu').onclick(); await nghi(6);
    bang('Vẫn lưu: gọi lại có đồng ý', cuaGoi(c, 'vagabond.goi_mon_ban.luu_so_do_ban').map(function (x) { return x.ts.dong_y_mat; }), [0, 1]);
    bang('sơ đồ gửi đi còn hai khu', cuaGoi(c, 'vagabond.goi_mon_ban.luu_so_do_ban')[1].ts.so_do.map(function (r) { return r.khu; }), ['A', 'B']);
  });

  await ca('màn Tính tiền: chip Số bàn chia theo khu của sơ đồ; điểm chưa khai vẫn Bàn 1 tới 20; bàn số lạ đang chọn vẫn hiện', async function () {
    var m = khoi();
    var el = new dg.ElementGia('div');
    el.innerHTML = m.g.posVeSoBan({ ma: 'NVHTN', nhom_ban: nhomTu(SO_DO) }, 'B3');
    var cc = chu(el);
    dung('nhãn khu theo thứ tự', cc.indexOf('Khu A') >= 0 && cc.indexOf('Khu A') < cc.indexOf('Khu B') && cc.indexOf('Khu B') < cc.indexOf('Khu VIP'));
    var chip = el.querySelectorAll('[data-ban]').map(function (x) { return x.getAttribute('data-ban'); });
    bang('22 bàn + Mang đi + Bỏ chọn', chip.length, 24);
    dung('có A12 và VIP2', chip.indexOf('A12') >= 0 && chip.indexOf('VIP2') >= 0);
    dung('B3 đang chọn', /background/.test(el.querySelector('[data-ban="B3"]').getAttribute('style') || '') || chu(el.querySelector('[data-ban="B3"]')) === 'B3');
    var md = new dg.ElementGia('div');
    md.innerHTML = m.g.posVeSoBan({ ma: 'TCV', nhom_ban: [] }, '');
    bang('mặc định 20 bàn', md.querySelectorAll('[data-ban]').map(function (x) { return x.getAttribute('data-ban'); }).slice(0, 20).join(','),
      Array.from({ length: 20 }, function (_, i) { return String(i + 1); }).join(','));
    dung('chữ Bàn 1', chu(md).indexOf('Bàn 1') >= 0 && chu(md).indexOf('Khu') < 0);
    bang('bàn 5 (QR số cũ) ở điểm đã khai khu', m.g.posNhomBan({ nhom_ban: nhomTu(SO_DO) }, '5').map(function (g) { return g.khu + ':' + g.ban.length; }),
      ['A:12', 'B:8', 'VIP:2', ':1']);
  });

  await ca('trang khách đọc link QR theo khu: ban=A1, a01, VIP2; bàn số cũ ban=05 ra "5"; tên sai thì coi như không có link', async function () {
    var K = '0123456789abcdef';
    var mod = await import(path.join(PUB, 'web_vue', 'banh', 'kho-goi-ban.js'));
    bang('A1', mod.docLinkBan('?diem=tcv&ban=A1&k=' + K), { diem: 'TCV', ban: 'A1', k: K });
    bang('a01', mod.docLinkBan('?diem=TCV&ban=a01&k=' + K).ban, 'A1');
    bang('VIP2', mod.docLinkBan('?diem=TCV&ban=VIP2&k=' + K).ban, 'VIP2');
    bang('bàn số cũ', mod.docLinkBan('?diem=TCV&ban=05&k=' + K).ban, '5');
    ['-1', '100', 'A100', 'ABCDE1', '5a', '', '0'].forEach(function (b) {
      bang('sai ' + b, mod.docLinkBan('?diem=TCV&ban=' + encodeURIComponent(b) + '&k=' + K), null);
    });
  });

  console.log('Bo ca kiem HANH VI v647 (QR ban theo khu)');
  ket.loi.forEach(function (l) { console.log('  HONG ' + l); });
  console.log(ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng, tổng ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
})();

/* Ca kiểm HÀNH VI v638: màn quầy nhận đơn gọi món tại bàn, và màn In QR tại bàn.
 *
 * Nạp THẬT toàn bộ 66-goi-mon-tai-ban.js cùng các hàm nó dùng của màn quầy
 * (posChipNut, posLaNuoc, posInPhieuMon, inKho, inMau của 09/10) và hàm
 * ptTheoNguon của 08, chạy trong DOM giả. Bấm đúng chuỗi của thu ngân: dải
 * chờ hiện, bấm mở danh sách, bấm Nhận đơn; đọc đúng cửa máy chủ đã gọi và tờ
 * phiếu pha chế đi ra máy in (inTo là chỗ giấy ra, thay bằng bộ ghi). Màn In
 * QR: chọn điểm, gõ khoảng bàn, Tạo mã QR, In; đọc tờ A6 ghi vào cửa sổ in.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/goi_mon_quay_638.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
var NEN = doc('00-nen.js'), SALES = doc('08-doanh-so-sales.js'), POS = doc('09-tinh-tien-quay.js'), BILL = doc('10-bill-quay.js');
var GMB = doc('66-goi-mon-tai-ban.js'), IN = doc('27-in-ngam.js');

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

var MA = ['h', 'money', 'today', 'anhMon'].map(function (t) { return layHam(NEN, t); }).join('\n') + '\n' +
  layHam(POS, 'posChipNut') + '\n' + layHam(SALES, 'nguonBH') + '\n' + layHam(SALES, 'ptTheoNguon') + '\n' +
  layBien(BILL, 'POS_NHOM_NUOC') + layBien(BILL, 'IN_MAU_MD') +
  ['posLaNuoc', 'posMonNuoc', 'inKho', 'inMau', 'posInPhieuMon'].map(function (t) { return layHam(BILL, t); }).join('\n') + '\n' +
  layHam(IN, 'inThemLenhIn') + '\n' + GMB;

var ket = { dat: 0, hong: 0 };
function dung(mo, dk) { if (!dk) throw new Error(mo); }
function bang(mo, a, b) {
  var x = JSON.stringify(a), y = JSON.stringify(b);
  if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y);
}
async function choDen(dk) { for (var i = 0; i < 80 && !dk(); i++) await new Promise(function (r) { setTimeout(r, 10); }); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n        ') : e)); }
}
function chu(el) { var s = el._chu || ''; (el.children || []).forEach(function (c) { s += chu(c); }); return s; }

var THE = [{ ma: 'TQ-261104-0001', ban: 5, diem: 'TCV', ten_diem: 'District 1', so_mon: 3, tam_tinh: 185000, phut: 2,
  mon: [{ ma: 'NUTR00021', ten: 'Trà Hoa Lài', sl: 2, tc: ['Ít đá'], nhom: 'Trà', gia: 45000, anh: '/files/tra.jpg' },
    { ma: 'BAWC00115', ten: 'Mousse Chanh Dây', sl: 1, tc: [], nhom: 'Bánh lạnh', gia: 95000, anh: '' }],
  ghi_chu: 'mang trà ra trước', ten_goi: 'Lan', gioi_thieu: 'Chị Dễ' }];

function moApp(o) {
  o = o || {};
  var tai = dg.taiLieuGia();
  var goi = [], tin = [], di = [], giay = [], cuaSo = [], keu = [];
  var ls = {};
  var cho = o.cho || THE;
  var g = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, Number: Number, Date: Date, isNaN: isNaN, parseInt: parseInt,
    setTimeout: setTimeout, clearTimeout: clearTimeout,
    setInterval: function () { return 1; }, clearInterval: function () {},
    localStorage: { getItem: function (k) { return Object.prototype.hasOwnProperty.call(ls, k) ? ls[k] : null; }, setItem: function (k, v) { ls[k] = String(v); } },
    CFGBH: o.cfg || { nhom_nuoc: ['Trà', 'Cà phê', 'Matcha', 'Cacao', 'Ice Cream - Kem'], nguon_qr: 'QR tại bàn',
      pt_quay: ['Tiền mặt', 'Chuyển khoản'], pt_pancake: ['Chuyển khoản', 'COD'], nguon: [],
      pt: [{ v: 'Tiền mặt' }, { v: 'Chuyển khoản' }, { v: 'COD' }] },
    posQuay: { ma: 'TCV', ten: 'The Vagabond District 1', ten_ngan: 'District 1', quay: 'TCV' },
    S: { roles: o.vai || ['VGB - Quản lý cửa hàng'], stack: [] },
    hasRole: function (r) { return (o.vai || ['VGB - Quản lý cửa hàng']).indexOf(r) >= 0; },
    busy: function () {}, toast: function (s) { tin.push(String(s)); },
    inSanSang: function () { return false; }, inNgamDo: function () {}, IN_QZ: { do_roi: 1 },
    inMoCuaSoNeuCan: function (vai) { var w = { vai: vai, dong: 0, close: function () { w.dong = 1; } }; cuaSo.push(w); return o.chanPopup ? 'chan' : w; },
    inTo: function (vai, tieuDe, html, rong, cham, w) { giay.push({ vai: vai, tieuDe: tieuDe, html: html, w: w }); return Promise.resolve('trinh-duyet'); },
    scrPosBill: function (ten) { di.push('bill:' + ten); },
    go: function (fn) { fn(); },
    frame: function (tieuDe, html, opt) {
      tai.body.children = [];
      var vb = new dg.ElementGia('div'); vb.setAttribute('id', 'vgbBody');
      vb.innerHTML = html + ((opt && opt.footer) || '');
      tai.body.appendChild(vb);
      g._tieuDe = tieuDe;
      return vb;
    },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: ts });
      if (duong === 'vagabond.goi_mon_ban.dem_cho') return Promise.resolve({ so: cho.length, ds: JSON.parse(JSON.stringify(cho)), ly_do: ['Hết món', 'Quầy quá đông', 'Khác'],
        tro_giup: JSON.parse(JSON.stringify(o.troGiup || [])) });
      if (duong === 'vagabond.goi_mon_ban.xong_tro_giup') return Promise.resolve({ ok: 1, ban: 5 });
      if (duong === 'vagabond.goi_mon_ban.nhan') {
        if (o.nhanLoi) return Promise.reject(new Error(o.nhanLoi));
        return Promise.resolve({ ok: 1, hoa_don: 'ACC-SINV-0099', bill: 'TCVABCDE', them_vao: 0, ban: 5,
          phieu: { name: 'ACC-SINV-0099', bill: 'TCVABCDE', so_ban: '5', ghi_chu: 'mang trà ra trước',
            mon: [{ item_code: 'NUTR00021', ten: 'Trà Hoa Lài', qty: 2, nhom: 'Trà', tc: ['Ít đá'], gc: '' },
              { item_code: 'BAWC00115', ten: 'Mousse Chanh Dây', qty: 1, nhom: 'Bánh lạnh', tc: [], gc: '' }] } });
      }
      if (duong === 'vagabond.goi_mon_ban.tu_choi') return Promise.resolve({ ok: 1 });
      if (duong === 'vagabond.goi_mon_ban.diem_in_qr') return Promise.resolve([{ ma: 'TCV', ten: 'District 1', phu: '9 Trần Cao Vân' }, { ma: 'NVHTN', ten: 'NVHTN', phu: '21 Phạm Ngọc Thạch' }]);
      if (duong === 'vagabond.goi_mon_ban.to_qr') {
        var to = [];
        for (var b = Math.min(ts.tu, ts.den); b <= Math.max(ts.tu, ts.den); b++) to.push({ ban: b, ten_diem: ts.diem === 'TCV' ? 'District 1' : 'NVHTN', link: 'https://x/banh?ban=' + b, anh: 'data:image/svg+xml;base64,QR' + b });
        return Promise.resolve({ diem: ts.diem, ten: 'District 1', to: to });
      }
      return Promise.reject(new Error('api la: ' + duong));
    }
  };
  g.window = g;
  g.window.open = function () { var w = { doc: '', document: { write: function (s) { w.doc += s; }, close: function () {} } }; cuaSo.push(w); return w; };
  g.window.AudioContext = function () {
    return { currentTime: 0, destination: {}, createOscillator: function () { return { frequency: {}, connect: function () {}, start: function () { keu.push(1); }, stop: function () {} }; },
      createGain: function () { return { gain: { setValueAtTime: function () {}, exponentialRampToValueAtTime: function () {} }, connect: function () {} }; } };
  };
  vm.runInNewContext(MA, g, { filename: 'goi-mon-quay.js' });
  return { g: g, tai: tai, goi: goi, tin: tin, di: di, giay: giay, cuaSo: cuaSo, keu: keu, ls: ls };
}
function manQuay(m) {
  /* Khối dải chờ đúng như scrPosQuay chèn vào giữa màn (gmbKhoi). */
  var vb = new dg.ElementGia('div');
  vb.innerHTML = m.g.gmbKhoi();
  m.tai.body.appendChild(vb);
}
function sheetCuoi(m) { var ds = m.tai.body.children; return ds[ds.length - 1]; }
function bamTrong(goc, chon) { var el = goc.querySelector(chon); if (!el) throw new Error('khong thay ' + chon); goc.onclick({ target: el }); return el; }

(async function () {
  console.log('v638 màn quầy: đơn gọi món tại bàn, In QR tại bàn');

  await ca('Dải chờ: có đơn thì hiện "1 đơn gọi món tại bàn đang chờ nhận" kèm bàn, chuông kêu một lần cho đơn mới; tắt chuông thì nhớ', async function () {
    var m = moApp();
    manQuay(m);
    m.g.gmbBatDau('TCV');
    await choDen(function () { return chu(m.tai.getElementById('gmbDai')).indexOf('đang chờ nhận') >= 0; });
    var dai = m.tai.getElementById('gmbDai');
    dung('dải hiện', chu(dai).indexOf('1 đơn gọi món tại bàn đang chờ nhận') >= 0 && chu(dai).indexOf('Bàn 5') >= 0);
    bang('hỏi đúng cửa, đúng quầy', m.goi[0], { duong: 'vagabond.goi_mon_ban.dem_cho', ts: { diem: 'TCV' } });
    bang('chuông kêu (hai nốt)', m.keu.length, 2);
    m.g.GMB_LUC = 0; await m.g.gmbHoi();
    bang('đơn cũ không kêu lại', m.keu.length, 2);
    bamTrong(dai, '[data-gmbchuong]');
    bang('tắt chuông nhớ theo máy', m.ls.vgb_gmb_chuong, '0');
    dung('nút đổi chữ', chu(dai).indexOf('Bật chuông') >= 0);
  });

  await ca('v639 bàn cần trợ giúp: dải đỏ ghi "1 bàn cần trợ giúp", chuông kêu; thẻ đỏ đứng trước đơn, có bill tạm tính; Đã tới bàn gọi đúng cửa; Mở bill mở phiếu', async function () {
    var m = moApp({ troGiup: [{ ma: 'GNV-261105-0001', ban: 5, diem: 'TCV', ten_diem: 'District 1', ly_do: 'Xin tính tiền', chi_tiet: '', phut: 1,
      bill: 'TCVABCDE', tam_tinh: 335000, hoa_don: 'ACC-SINV-0099' },
      { ma: 'GNV-261105-0002', ban: 9, diem: 'TCV', ten_diem: 'District 1', ly_do: 'Việc khác', chi_tiet: 'xin thêm ghế em bé', phut: 0, bill: '', tam_tinh: 0, hoa_don: '' }] });
    manQuay(m);
    m.g.gmbBatDau('TCV');
    await choDen(function () { return chu(m.tai.getElementById('gmbDai')).indexOf('cần trợ giúp') >= 0; });
    var dai = m.tai.getElementById('gmbDai');
    dung('dải ghi cả hai', chu(dai).indexOf('1 đơn gọi món tại bàn đang chờ nhận · 2 bàn cần trợ giúp') >= 0 && chu(dai).indexOf('Bàn 5 xin tính tiền') >= 0 && chu(dai).indexOf('Bàn 9 cần hỗ trợ') >= 0);
    bang('chuông kêu', m.keu.length, 2);
    bamTrong(dai, '[data-gmbmo]');
    var sh = sheetCuoi(m);
    var the = sh.querySelectorAll('[data-gmbtg]');
    bang('hai thẻ trợ giúp', the.length, 2);
    dung('thẻ trợ giúp đứng trước thẻ đơn', chu(sh).indexOf('CẦN TRỢ GIÚP') < chu(sh).indexOf('Nhận đơn và in phiếu'));
    dung('thẻ xin tính tiền có bill', chu(the[0]).indexOf('Bill tạm tính TCVABCDE · 335.000 đ') >= 0 && the[0].querySelector('[data-gmbbill]'));
    dung('thẻ việc khác có chữ khách nhắn, không nút bill', chu(the[1]).indexOf('xin thêm ghế em bé') >= 0 && !the[1].querySelector('[data-gmbbill]'));
    bamTrong(sh, '[data-gmbxong="GNV-261105-0001"]');
    await choDen(function () { return m.goi.some(function (x) { return x.duong === 'vagabond.goi_mon_ban.xong_tro_giup'; }); });
    bang('gọi đúng cửa', m.goi.filter(function (x) { return x.duong === 'vagabond.goi_mon_ban.xong_tro_giup'; }).map(function (x) { return x.ts; }), [{ ma: 'GNV-261105-0001' }]);
    await new Promise(function (r) { setTimeout(r, 20); });
    bang('thẻ đó biến mất, còn một', sheetCuoi(m).querySelectorAll('[data-gmbtg]').length, 1);
    dung('dải còn 1 bàn', chu(m.tai.getElementById('gmbDai')).indexOf('1 bàn cần trợ giúp') >= 0);
    var m2 = moApp({ troGiup: [{ ma: 'GNV-261105-0003', ban: 5, diem: 'TCV', ten_diem: 'District 1', ly_do: 'Xin tính tiền', chi_tiet: '', phut: 1, bill: 'TCVABCDE', tam_tinh: 1000, hoa_don: 'ACC-SINV-0099' }] });
    manQuay(m2); m2.g.gmbBatDau('TCV');
    await choDen(function () { return chu(m2.tai.getElementById('gmbDai')).indexOf('cần trợ giúp') >= 0; });
    bamTrong(m2.tai.getElementById('gmbDai'), '[data-gmbmo]');
    bamTrong(sheetCuoi(m2), '[data-gmbbill]');
    bang('mở phiếu tạm tính của bàn', m2.di, ['bill:ACC-SINV-0099']);
  });

  await ca('Không có đơn: dải trống, không dải nổi, tên tab giữ nguyên; bỏ chọn quầy thì nhịp dừng, không gọi máy chủ', async function () {
    var m = moApp({ cho: [] });
    m.tai.title = 'Vagabond';
    manQuay(m);
    m.g.gmbBatDau('TCV');
    await choDen(function () { return m.goi.length; });
    await new Promise(function (r) { setTimeout(r, 20); });
    bang('dải trống', chu(m.tai.getElementById('gmbDai')), '');
    bang('không dải nổi', m.tai.getElementById('gmbNoi'), null);
    bang('tên tab', m.tai.title, 'Vagabond');
    m.g.gmbBatDau('');
    var truoc = m.goi.length;
    await m.g.gmbHoi();
    bang('không gọi thêm', m.goi.length, truoc);
  });

  await ca('v655 (Dễ báo 13/11, anh Việt chọn A): rời màn Tính tiền (sang Hoá đơn hôm nay, mở bill) vẫn hỏi đơn mới; có đơn thì dải NỔI trên cùng màn, bấm mở danh sách; tên tab "(1) Đơn mới"; quay lại Tính tiền thì dải về chỗ cũ, không còn dải nổi; bỏ chọn quầy thì dải nổi mất', async function () {
    var m2 = moApp({});
    m2.tai.title = 'Vagabond';
    manQuay(m2);
    m2.g.gmbBatDau('TCV');
    await choDen(function () { return m2.goi.length; });
    m2.g.frame('Hoá đơn hôm nay · TCV', '<div>danh sách</div>');
    var truoc = m2.goi.length;
    await m2.g.gmbHoi();
    bang('vẫn hỏi máy chủ khi rời màn Tính tiền', m2.goi.length, truoc + 1);
    var noi = m2.tai.getElementById('gmbNoi');
    dung('dải nổi có đơn', noi && chu(noi).indexOf('1 đơn gọi món tại bàn đang chờ nhận') >= 0);
    bang('tên tab', m2.tai.title, '(1) Đơn mới · Vagabond');
    bamTrong(noi, '[data-gmbmo]');
    dung('bấm dải nổi mở danh sách đơn', chu(sheetCuoi(m2)).indexOf('Bàn 5') >= 0);
    m2.g.frame('Tính tiền · TCV', m2.g.gmbKhoi());
    m2.g.gmbVeLai();
    bang('về màn Tính tiền: hết dải nổi', m2.tai.getElementById('gmbNoi'), null);
    dung('dải về chỗ cũ', chu(m2.tai.getElementById('gmbDai')).indexOf('đang chờ nhận') >= 0);
    m2.g.frame('Hoá đơn hôm nay · TCV', '<div>danh sách</div>');
    m2.g.gmbVeLai();
    dung('đổi màn: dải nổi lại hiện', !!m2.tai.getElementById('gmbNoi'));
    /* Màn thật chỉ thay phần thân app, dải nổi gắn ở body còn đó khi màn Tính
       tiền vẽ chỗ dải: không được hiện hai dải. */
    manQuay(m2);
    m2.g.gmbVeLai();
    bang('có chỗ dải mà dải nổi còn: bỏ dải nổi', m2.tai.getElementById('gmbNoi'), null);
    m2.g.frame('Hoá đơn hôm nay · TCV', '<div>danh sách</div>');
    m2.g.gmbVeLai();
    m2.g.gmbBatDau('');
    bang('bỏ chọn quầy: dải nổi mất, tên tab về gốc', [m2.tai.getElementById('gmbNoi'), m2.tai.title], [null, 'Vagabond']);
  });

  await ca('v655 THUẦN tên tab: có việc chờ thì "(N) Đơn mới · tên gốc", lượt nhấp nháy trả tên gốc, không việc thì tên gốc', async function () {
    var m = moApp({});
    bang('có 2', m.g.gmbChuTieuDe('Vagabond', 2, 0), '(2) Đơn mới · Vagabond');
    bang('nhấp nháy', m.g.gmbChuTieuDe('Vagabond', 2, 1), 'Vagabond');
    bang('không việc', m.g.gmbChuTieuDe('Vagabond', 0, 0), 'Vagabond');
  });

  await ca('Nhận đơn: thẻ đủ bàn, số món, tạm tính, phút chờ, món kèm đá đường, ghi chú, tên gọi, người giới thiệu; bấm Nhận gọi goi_mon_ban.nhan, in phiếu pha chế chỉ món nước, mở phiếu tạm tính của bàn', async function () {
    var m = moApp();
    manQuay(m);
    m.g.gmbBatDau('TCV');
    await choDen(function () { return m.g.GMB_DS && m.g.GMB_DS.length; });
    bamTrong(m.tai.getElementById('gmbDai'), '[data-gmbmo]');
    var sh = sheetCuoi(m);
    var the = sh.querySelector('[data-gmbthe]');
    var c = chu(the);
    ['Bàn 5', '3 món', '185.000 đ', 'chờ 2 phút', 'Trà Hoa Lài', 'Ít đá', 'mang trà ra trước', 'Lan', 'Người giới thiệu: Chị Dễ',
      'Nhận đơn và in phiếu pha chế', 'Từ chối'].forEach(function (x) { dung('thẻ có "' + x + '"', c.indexOf(x) >= 0); });
    // Codex PR #541 vòng 2 (AGENTS.md 2b.4): mỗi dòng món có ảnh qua anhMon; chưa có ảnh thì ô 🍰.
    var anh = the.querySelectorAll('img');
    bang('ảnh món có ảnh danh mục', anh.map(function (x) { return x.getAttribute('src'); }), ['/files/tra.jpg']);
    bang('món chưa có ảnh giữ hàng bằng ô 🍰', the.querySelectorAll('.immp').map(function (x) { return chu(x); }), ['🍰']);
    bamTrong(sh, '[data-gmbnhan]');
    await choDen(function () { return m.di.length; });
    bang('gọi đúng cửa với mã đơn', m.goi.filter(function (x) { return x.duong === 'vagabond.goi_mon_ban.nhan'; }).map(function (x) { return x.ts; }),
      [{ ma: 'TQ-261104-0001' }]);
    bang('mở cửa sổ in phiếu món TRƯỚC khi chờ máy chủ', m.cuaSo.map(function (w) { return w.vai; }), ['phieu_mon']);
    bang('một tờ phiếu món ra đúng cửa sổ đó', m.giay.map(function (x) { return [x.vai, x.w === m.cuaSo[0]]; }), [['phieu_mon', true]]);
    var p = m.giay[0].html;
    dung('phiếu có trà, đá đường, bàn 5, ghi chú', p.indexOf('Trà Hoa Lài') >= 0 && p.indexOf('Ít đá') >= 0 && p.indexOf('BÀN 5') >= 0 && p.indexOf('mang trà ra trước') >= 0);
    dung('phiếu pha chế không có bánh', p.indexOf('Mousse') < 0);
    bang('mở phiếu tạm tính của bàn', m.di, ['bill:ACC-SINV-0099']);
    dung('báo đã lập phiếu tạm tính', m.tin.some(function (s) { return s.indexOf('phiếu tạm tính bàn 5') >= 0; }));
    bang('dải hết đơn', chu(m.tai.getElementById('gmbDai')), '');
  });

  await ca('Nhận đơn chỉ có bánh: không mở cửa sổ in; máy chủ báo đơn đã có người nhận thì đóng cửa sổ in, báo lỗi, hỏi lại danh sách', async function () {
    var m = moApp({ cho: [{ ma: 'TQ-2', ban: 3, so_mon: 1, tam_tinh: 95000, phut: 1, mon: [{ ma: 'BAWC00115', ten: 'Mousse', sl: 1, tc: [], nhom: 'Bánh lạnh' }] }] });
    manQuay(m);
    m.g.gmbBatDau('TCV');
    await choDen(function () { return m.g.GMB_DS && m.g.GMB_DS.length; });
    bamTrong(m.tai.getElementById('gmbDai'), '[data-gmbmo]');
    bamTrong(sheetCuoi(m), '[data-gmbnhan]');
    await choDen(function () { return m.di.length; });
    bang('không cửa sổ in', [m.cuaSo.length, m.giay.length], [0, 0]);
    var m2 = moApp({ nhanLoi: 'Đơn bàn 5 đã được nhận, không cần nhận lại.' });
    manQuay(m2);
    m2.g.gmbBatDau('TCV');
    await choDen(function () { return m2.g.GMB_DS && m2.g.GMB_DS.length; });
    bamTrong(m2.tai.getElementById('gmbDai'), '[data-gmbmo]');
    bamTrong(sheetCuoi(m2), '[data-gmbnhan]');
    await choDen(function () { return m2.tin.length; });
    dung('báo câu máy chủ', m2.tin[0].indexOf('đã được nhận') >= 0);
    bang('đóng cửa sổ in đã mở', m2.cuaSo[0].dong, 1);
    bang('không mở bill', m2.di, []);
  });

  await ca('Từ chối: bắt chọn lý do (chưa chọn thì không gọi máy chủ), gửi đúng mã và lý do, không in, không mở bill', async function () {
    var m = moApp();
    manQuay(m);
    m.g.gmbBatDau('TCV');
    await choDen(function () { return m.g.GMB_DS && m.g.GMB_DS.length; });
    bamTrong(m.tai.getElementById('gmbDai'), '[data-gmbmo]');
    bamTrong(sheetCuoi(m), '[data-gmbtuchoi]');
    var hop = sheetCuoi(m);
    bamTrong(hop, '[data-gmbtc]');
    await new Promise(function (r) { setTimeout(r, 10); });
    bang('chưa chọn lý do: không gọi', m.goi.filter(function (x) { return x.duong === 'vagabond.goi_mon_ban.tu_choi'; }).length, 0);
    bamTrong(hop, '[data-gmblydo="Hết món"]');
    bamTrong(hop, '[data-gmbtc]');
    await choDen(function () { return m.goi.some(function (x) { return x.duong === 'vagabond.goi_mon_ban.tu_choi'; }); });
    bang('gửi lý do', m.goi.filter(function (x) { return x.duong === 'vagabond.goi_mon_ban.tu_choi'; })[0].ts, { ma: 'TQ-261104-0001', ly_do: 'Hết món' });
    await new Promise(function (r) { setTimeout(r, 10); });
    bang('không in, không mở bill', [m.giay.length, m.di.length], [0, 0]);
  });

  await ca('Thu tiền phiếu lập từ QR: phương thức như Tại chỗ (pt_quay), không rơi về danh sách đơn online', async function () {
    var m = moApp();
    bang('QR tại bàn', m.g.ptTheoNguon('QR tại bàn').map(function (p) { return p.v; }), ['Tiền mặt', 'Chuyển khoản']);
    bang('nguồn lạ khác vẫn như cũ', m.g.ptTheoNguon('Pancake').map(function (p) { return p.v; }), ['Chuyển khoản', 'COD']);
    dung('phiếu in nhận nhóm nước từ cấu hình', m.g.posLaNuoc({ item_code: 'X1', nhom: 'Trà' }) && !m.g.posLaNuoc({ item_code: 'X2', nhom: 'Topping cho món nước' }));
  });

  /* v647: màn In QR tại bàn làm lại (sơ đồ bàn theo khu, standee branding dàn
     trên A4). Ca "gõ bàn 1 tới 3, In 3 tờ A6" cũ không còn đúng màn; chuỗi
     thao tác mới kiểm ở hanh_vi/qr_ban_khu_647.js. */

  await ca('Menu: ô In QR tại bàn chỉ hiện cho quản lý cửa hàng, Giám đốc', async function () {
    bang('QLCH', moApp({ vai: ['VGB - Quản lý cửa hàng'] }).g.coQuyenGmbQr(), true);
    bang('Giám đốc', moApp({ vai: ['Giám đốc'] }).g.coQuyenGmbQr(), true);
    bang('Sales', moApp({ vai: ['Sales User'] }).g.coQuyenGmbQr(), false);
  });

  console.log('\n' + ket.dat + ' ca dat, ' + ket.hong + ' ca hong');
  process.exit(ket.hong ? 1 : 0);
})();

/* Bo ca kiem HANH VI v607: khoi Hang tang ly do chon san (54-ly-do-tang.js)
 * va khoi So du tra truoc tren don (55-so-du-tra-truoc.js).
 *
 * CHAY THAT: nap NGUYEN hai tep 54, 55 vao DOM gia, va o nhom cuoi nap
 * nguyen 01-khung-app.js + 08-doanh-so-sales.js de bam chip tren man Chi
 * tiet don Sales. May chu la ban gia ghi lai tung loi goi. Ca kiem bam dung
 * chuoi thao tac cua Sales: chon chip loai, chon ly do, go nguoi nhan, bam
 * Luu; roi doc dung tham so may chu nhan duoc. Khong goi them ham nao cua
 * man ngoai chuoi do (AGENTS, bai hoc 06/09: ham goi "cho chac" che loi).
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/tang_tra_truoc_607.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var domGia = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }

var ket = { dat: 0, hong: 0, loi: [] };
function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; }
  catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 4).join('\n         ') : String(e))); }
}
async function nghi() { for (var i = 0; i < 12; i++) await Promise.resolve(); await new Promise(function (r) { setImmediate(r); }); }

/* Dung y nguyen hang_tang.LY_DO_SAN va cai_dat() ben may chu. Ca kiem
   Python thu_tang_tra_truoc_607 chot rang bang nay trung bang may chu. */
var LY_DO = [
  ['V1', 'vip', 'Tặng sinh nhật khách', 'nguoi'], ['V2', 'vip', 'Quà lễ, Tết, Trung thu cho khách thân thiết', 'nguoi'],
  ['V3', 'vip', 'Quà cảm ơn khách quen', 'nguoi'], ['V4', 'vip', 'Đổi thẻ tích điểm (Croissant)', 'nguoi'],
  ['D1', 'den_bu', 'Giao trễ đơn', 'nguoi'], ['D2', 'den_bu', 'Sót món, sót đơn', 'nguoi'],
  ['D3', 'den_bu', 'Bánh hỏng, sai mẫu', 'nguoi'], ['D4', 'den_bu', 'Phục vụ nhầm tại quầy', 'nguoi'],
  ['M1', 'marketing', 'KOL, KOC đánh giá', 'kol'], ['M2', 'marketing', 'Giveaway, minigame', 'kol'],
  ['M3', 'marketing', 'Chụp hình, quay sản phẩm', 'kol'], ['T1', 'doi_tac', 'Quà doanh nghiệp, đối tác', 'doi_tac'],
  ['T2', 'doi_tac', 'Tài trợ sự kiện', 'doi_tac'], ['N1', 'noi_bo', 'Thử món, kiểm mẻ', ''],
  ['N2', 'noi_bo', 'Sinh nhật, phúc lợi nhân viên', 'nguoi'], ['N3', 'noi_bo', 'Ban giám đốc dùng, biếu', 'nguoi'],
  ['K1', 'khac', 'Từ thiện, cúng dường', ''], ['K2', 'khac', 'Khác', 'tay'],
];
var NHAN_CAN = { nguoi: 'Người nhận', kol: 'Tên KOL hoặc chương trình', doi_tac: 'Tên đối tác', tay: 'Lý do cụ thể' };
var CAI_DAT_TANG = {
  pt: 'Hàng tặng', loai_can_anh: ['den_bu'],
  chip_loai: [['vip', '⭐ Khách VIP'], ['den_bu', '🩹 Đền bù'], ['marketing', '📣 Marketing'], ['doi_tac', '🤝 Đối tác'],
    ['noi_bo', '🧑‍🍳 Nội bộ'], ['khac', '… Khác']].map(function (x) { return { k: x[0], ten: x[1] }; }),
  ly_do_san: LY_DO.map(function (r) {
    return { ma: r[0], loai: r[1], nhan: r[2], can: r[3], nhan_can: NHAN_CAN[r[3]] || '',
      toi_thieu: r[3] === 'tay' ? 10 : (r[3] ? 2 : 0) };
  }),
};

function mayChu(tuy) {
  tuy = tuy || {};
  var goi = [];
  return {
    goi: goi,
    cac: function (m) { return goi.filter(function (g) { return g.m === m; }); },
    api: function (m, a) {
      goi.push({ m: m, a: a });
      if (tuy[m]) { var r = tuy[m](a); return r instanceof Promise ? r : Promise.resolve(r); }
      if (m === 'vagabond.hang_tang.cai_dat') return Promise.resolve(CAI_DAT_TANG);
      if (m === 'vagabond.hang_tang.goi_y') return Promise.resolve({ khach: 'Nguyễn Hoàng Việt', ghi_chu_pancake: 'Bánh tặng', so_anh: 0 });
      if (m === 'vagabond.hang_tang.luu_tang') return Promise.resolve({ ok: 1, cau_thieu: [] });
      if (m === 'vagabond.tra_truoc_khach.ap_dung') return Promise.resolve({ ok: 1 });
      return Promise.resolve({});
    },
  };
}

/* Nap rieng hai tep 54, 55 voi bo tro toi thieu. */
function khoiMoi(tuy) {
  var tl = domGia.taiLieuGia();
  var mc = mayChu(tuy);
  var tin = [];
  var g = {
    console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array,
    Promise: Promise, Error: Error, RegExp: RegExp, parseFloat: parseFloat, parseInt: parseInt, isNaN: isNaN, Date: Date,
    document: tl, setTimeout: function (f) { return 1; }, clearTimeout: function () {},
    FileReader: function () {},
    __tin: tin, __mc: mc, __chonKhach: null,
  };
  g.window = g;
  vm.createContext(g);
  vm.runInContext([
    'function h(s) { return String(s == null ? "" : s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;"); }',
    'function toast(s) { __tin.push("toast:" + s); }',
    'function busy() {}',
    'function baoTin(s) { __tin.push("baoTin:" + s); return Promise.resolve(); }',
    'function money(x) { return String(x); }',
    'function errMsg(e) { return String((e && e.message) || e); }',
    'function api(m, a) { return __mc.api(m, a); }',
    'function sheetTimKhach(t, cb) { __tin.push("sheet:" + t); if (__chonKhach) cb(__chonKhach); }',
  ].join('\n'), g);
  vm.runInContext(doc('54-ly-do-tang.js'), g);
  vm.runInContext(doc('55-so-du-tra-truoc.js'), g);
  return {
    g: g, tl: tl, mc: mc, tin: tin,
    dat: function (html) { var o = tl.createElement('div'); o.innerHTML = html; tl.body.appendChild(o); return o; },
    mot: function (chon) { var r = tl.body.querySelectorAll(chon); if (r.length !== 1) throw new Error('mong dung 1 ' + chon + ', co ' + r.length); return r[0]; },
    tat: function (chon) { return tl.body.querySelectorAll(chon); },
    bam: async function (el) { el.dispatchEvent(domGia.suKien('click', {}, el)); await nghi(); await nghi(); },
    go: async function (el, v) { el.value = v; el.dispatchEvent(domGia.suKien('input', {}, el)); await nghi(); },
  };
}

function donTang(them) {
  return Object.assign({ name: 'SI-95631', docstatus: 0, vgb_pt_thanh_toan: 'Hàng tặng', grand_total: 750000,
    customer: 'KL001', customer_name: 'Nguyễn Hoàng Việt' }, them || {});
}

async function moKhoiTang(tuy, them, ghiChu) {
  var k = khoiMoi(tuy);
  k.dat('<div id="pbTgForm">Đang tải</div>');
  k.sauLuu = [];
  await k.g.tangGan('pb', donTang(them), ghiChu ? function () { return ghiChu; } : null,
    function (kq) { k.sauLuu.push(kq); });
  await nghi();
  return k;
}

function chuTrongKhoi(k) { return k.tl.getElementById('pbTgForm').innerHTML; }

(async function () {
  await ca('Đơn tặng chưa khai: bấm Lưu không gọi máy chủ, nói rõ chọn loại', async function () {
    var k = await moKhoiTang();
    dung('có sáu chip loại', k.tat('[data-tgl]').length === 6);
    bang('chưa có lý do nào khi chưa chọn loại', k.tat('[data-tgm]').length, 0);
    await k.bam(k.mot('#pbTgLuu'));
    bang('không gọi luu_tang', k.mc.cac('vagabond.hang_tang.luu_tang').length, 0);
    dung('nhắc chọn loại', k.tin.indexOf('toast:Chọn loại tặng.') >= 0);
  });

  await ca('Khách VIP, Tặng sinh nhật: người nhận lấy sẵn tên khách, lưu đúng một lần với mã và người nhận', async function () {
    var k = await moKhoiTang(null, null, 'ghi chú bill');
    await k.bam(k.mot('[data-tgl="vip"]'));
    bang('đúng bốn lý do của loại VIP', k.tat('[data-tgm]').map(function (b) { return b.getAttribute('data-tgm'); }),
      ['V1', 'V2', 'V3', 'V4']);
    await k.bam(k.mot('[data-tgm="V1"]'));
    bang('ô người nhận điền sẵn tên khách', k.mot('#pbTgThem').value || k.mot('#pbTgThem').getAttribute('value'), 'Nguyễn Hoàng Việt');
    dung('xem trước câu sẽ lưu', chuTrongKhoi(k).indexOf('Tặng sinh nhật khách: Nguyễn Hoàng Việt') >= 0);
    await k.bam(k.mot('#pbTgLuu'));
    var g = k.mc.cac('vagabond.hang_tang.luu_tang');
    bang('gọi luu_tang đúng một lần', g.length, 1);
    bang('tham số gửi lên', [g[0].a.name, g[0].a.ma_ly_do, g[0].a.them, g[0].a.ghi_chu],
      ['SI-95631', 'V1', 'Nguyễn Hoàng Việt', 'ghi chú bill']);
    bang('không gọi cửa cũ pos_chot', k.mc.cac('vagabond.ban_hang.pos_chot').length, 0);
    bang('chạy tiếp sau khi lưu', k.sauLuu.length, 1);
  });

  await ca('Đền bù chưa có ảnh: không lưu; đơn đã có ảnh trên máy chủ thì lưu được', async function () {
    var k = await moKhoiTang();
    await k.bam(k.mot('[data-tgl="den_bu"]'));
    await k.bam(k.mot('[data-tgm="D3"]'));
    await k.bam(k.mot('#pbTgLuu'));
    bang('không gọi luu_tang khi thiếu ảnh', k.mc.cac('vagabond.hang_tang.luu_tang').length, 0);
    dung('nói rõ thiếu ảnh', k.tin.some(function (t) { return t.indexOf('ảnh chứng minh') >= 0; }));
    var k2 = await moKhoiTang({ 'vagabond.hang_tang.goi_y': function () { return { khach: 'Chị Mai', ghi_chu_pancake: '', so_anh: 1 }; } });
    await k2.bam(k2.mot('[data-tgl="den_bu"]'));
    await k2.bam(k2.mot('[data-tgm="D3"]'));
    await k2.bam(k2.mot('#pbTgLuu'));
    bang('có ảnh rồi thì gửi', k2.mc.cac('vagabond.hang_tang.luu_tang').map(function (g) { return [g.a.ma_ly_do, g.a.them]; }),
      [['D3', 'Chị Mai']]);
  });

  await ca('Lý do Khác: gõ ngắn bị chặn tại chỗ, đủ 10 ký tự thì gửi', async function () {
    var k = await moKhoiTang();
    await k.bam(k.mot('[data-tgl="khac"]'));
    await k.bam(k.mot('[data-tgm="K2"]'));
    await k.go(k.mot('#pbTgThem'), 'tặng ai');
    dung('dòng thiếu hiện', k.mot('#pbTgThieu').style.display === 'block');
    await k.bam(k.mot('#pbTgLuu'));
    bang('chưa gọi', k.mc.cac('vagabond.hang_tang.luu_tang').length, 0);
    await k.go(k.mot('#pbTgThem'), 'Tặng chủ nhà mặt bằng dịp khai trương');
    dung('dòng thiếu ẩn', k.mot('#pbTgThieu').style.display === 'none');
    await k.bam(k.mot('#pbTgLuu'));
    bang('gửi đúng', k.mc.cac('vagabond.hang_tang.luu_tang').map(function (g) { return [g.a.ma_ly_do, g.a.them]; }),
      [['K2', 'Tặng chủ nhà mặt bằng dịp khai trương']]);
  });

  await ca('Ghi chú Pancake chỉ hiện để bấm chép, không tự đổ vào ô', async function () {
    var k = await moKhoiTang();
    dung('ghi chú Pancake hiện', chuTrongKhoi(k).indexOf('Ghi chú Pancake: &quot;Bánh tặng&quot;') >= 0 ||
      chuTrongKhoi(k).indexOf('Bánh tặng') >= 0);
    await k.bam(k.mot('[data-tgl="marketing"]'));
    await k.bam(k.mot('[data-tgm="M1"]'));
    bang('ô KOL trống, không tự chép', k.mot('#pbTgThem').getAttribute('value'), '');
    await k.bam(k.mot('[data-tgchep]'));
    bang('bấm Chép vào thì mới có', k.mot('#pbTgThem').getAttribute('value'), 'Bánh tặng');
  });

  await ca('Đơn cũ gõ tay tự do (không có mã): giữ loại, không tự đổ ghi chú Pancake, người nhận lấy tên khách', async function () {
    var k = await moKhoiTang(null, { vgb_tang_loai: 'vip', vgb_tang_ly_do: 'Bánh tặng' });
    dung('chip VIP đang chọn', k.mot('[data-tgl="vip"]').getAttribute('style').indexOf('font-weight:700') >= 0);
    await k.bam(k.mot('[data-tgm="V1"]'));
    bang('người nhận là tên khách, không phải ghi chú Pancake', k.mot('#pbTgThem').getAttribute('value'), 'Nguyễn Hoàng Việt');
  });

  await ca('Mở lại đơn đã khai: chọn lại đúng loại, lý do và phần người nhận', async function () {
    var k = await moKhoiTang(null, { vgb_tang_loai: 'marketing', vgb_tang_ma_ly_do: 'M1', vgb_tang_ly_do: 'KOL, KOC đánh giá: Linh Ngọc Đàm' });
    dung('chip Marketing đang chọn', k.mot('[data-tgl="marketing"]').getAttribute('style').indexOf('font-weight:700') >= 0);
    bang('phần thêm tách lại đúng', k.mot('#pbTgThem').getAttribute('value'), 'Linh Ngọc Đàm');
  });

  await ca('Máy chủ từ chối: báo lỗi, không chạy bước sau lưu', async function () {
    var k = await moKhoiTang({ 'vagabond.hang_tang.luu_tang': function () { return Promise.reject(new Error('Đơn đã ghi sổ')); } });
    await k.bam(k.mot('[data-tgl="noi_bo"]'));
    await k.bam(k.mot('[data-tgm="N1"]'));
    await k.bam(k.mot('#pbTgLuu'));
    dung('báo lỗi', k.tin.indexOf('baoTin:Đơn đã ghi sổ') >= 0);
    bang('không chạy tiếp', k.sauLuu.length, 0);
  });

  /* ---------------- So du tra truoc tren don ---------------- */
  async function moSoDu(soDu, them) {
    var k = khoiMoi({ 'vagabond.tra_truoc_khach.so_du': function (a) { k.hoi = a; return soDu; } });
    k.dat('<div id="dsvSoDu"></div>');
    k.sauLuu = 0;
    await k.g.sdtKhoiDon('dsv', Object.assign({ name: 'SI-1', grand_total: 1250000, customer: 'KL040476', customer_name: 'Mỹ Dung' }, them || {}),
      ['Tiền mặt', 'Chuyển khoản', 'Hàng tặng', 'Công nợ', 'Số dư trả trước'], function () { k.sauLuu++; });
    await nghi();
    return k;
  }

  await ca('Đủ số dư: trừ cả đơn, lưu một lần không kèm phương thức phụ', async function () {
    var k = await moSoDu({ kha_dung_tam: 48987500, cho_ghi_so: 0 });
    bang('hỏi số dư đúng khách và trừ chính đơn này', [k.hoi.khach, k.hoi.si], ['KL040476', 'SI-1']);
    bang('không bắt chọn phần còn lại', k.tat('[data-sdtpc]').length, 0);
    await k.bam(k.mot('[data-sdtluu]'));
    bang('gửi áp số dư', k.mc.cac('vagabond.tra_truoc_khach.ap_dung').map(function (g) { return [g.a.si_name, g.a.khach, g.a.pt_con_lai]; }),
      [['SI-1', 'KL040476', '']]);
    bang('chạy tiếp', k.sauLuu, 1);
  });

  await ca('Thiếu số dư: phải chọn phương thức phần còn lại, chip không có Hàng tặng, Công nợ, Số dư', async function () {
    var k = await moSoDu({ kha_dung_tam: 300000, cho_ghi_so: 0 });
    bang('chip phần còn lại', k.tat('[data-sdtpc]').map(function (b) { return b.getAttribute('data-sdtpc'); }), ['Tiền mặt', 'Chuyển khoản']);
    await k.bam(k.mot('[data-sdtluu]'));
    bang('chưa chọn thì không gửi', k.mc.cac('vagabond.tra_truoc_khach.ap_dung').length, 0);
    await k.bam(k.mot('[data-sdtpc="Chuyển khoản"]'));
    await k.bam(k.mot('[data-sdtluu]'));
    bang('gửi kèm phương thức phần còn lại', k.mc.cac('vagabond.tra_truoc_khach.ap_dung').map(function (g) { return g.a.pt_con_lai; }), ['Chuyển khoản']);
  });

  await ca('Đơn đang mang khách lẻ: phải chọn khách trước, chọn xong mới hỏi số dư khách đó', async function () {
    var k = khoiMoi({ 'vagabond.tra_truoc_khach.so_du': function (a) { k.hoi = a; return { kha_dung_tam: 5000000 }; } });
    k.g.__chonKhach = { name: 'KL040476', customer_name: 'Mỹ Dung' };
    k.dat('<div id="pbSoDu"></div>');
    await k.g.sdtKhoiDon('pb', { name: 'SI-2', grand_total: 100000, customer: 'Khách lẻ Online' }, ['Tiền mặt'], null);
    await nghi();
    bang('chưa hỏi số dư', k.mc.cac('vagabond.tra_truoc_khach.so_du').length, 0);
    bang('chưa có nút lưu', k.tat('[data-sdtluu]').length, 0);
    await k.bam(k.mot('[data-sdtkh]'));
    await nghi();
    bang('hỏi số dư của khách vừa chọn', k.hoi && k.hoi.khach, 'KL040476');
    bang('có nút lưu', k.tat('[data-sdtluu]').length, 1);
  });

  await ca('Khách chưa có số dư: không có nút lưu, nói rõ đi nạp', async function () {
    var k = await moSoDu({ kha_dung_tam: 0 });
    bang('không có nút lưu', k.tat('[data-sdtluu]').length, 0);
    dung('nói rõ', k.tl.getElementById('dsvSoDu').innerHTML.indexOf('chưa còn số dư') >= 0);
  });

  /* ---------------- Man Chi tiet don Sales that ---------------- */
  var GIA_RONG = ['khachTrenDon', 'khachMotDong', 'veKhachNo', 'dsvTaiHt', 'dsvVeHt', 'dsvKhoiHt', 'dsvVeThayThe',
    'dsvVeThu', 'dsvVeDiem', 'dsvVeTruDiem', 'dsvTheAnh', 'dsvHoiHt', 'dsvGanTruDiem', 'dsvGanHt', 'dsvChayDongHo',
    'dsvnNapKhoiHd', 'dsvnKhoiHd', 'dsvOSo', 'dsvNapLai', 'dsvTaiThe', 'ttnVe', 'tkNapKhoi', 'tkKhoiChiTiet',
    'promptSheet', 'posXinPhep', 'posTaiKhoan', 'posQrUrl', 'posNoiDungCk', 'hopKhung', 'hoanMoFormHuy', 'hoanMoFormDu', 'hoanMoForm',
    'hddtChoXuatChu', 'hdGanBind', 'hdAiLamGi', 'dstGanNganCach', 'dstDiemDs', 'dstSoThuan', 'dstNganCach', 'dsTayDoc',
    'veOMtc', 'xacNhan', 'confirmSheet', 'dsvGanThe', 'veTruDiem', 'sheetTimKhach'];
  function manSales(don) {
    var tl = domGia.taiLieuGia();
    var vgb = tl.createElement('div'); vgb.id = 'vgb'; tl.body.appendChild(vgb);
    var mc = mayChu({
      'frappe.client.get': function () { return don; },
      'vagabond.ban_hang.cau_hinh_ban_hang': function () {
        return { pt: [{ v: 'Tiền mặt' }, { v: 'Chuyển khoản' }, { v: 'Hàng tặng' }, { v: 'Số dư trả trước' }],
          pt_pancake: ['Tiền mặt', 'Chuyển khoản', 'Hàng tặng', 'Số dư trả trước'], nguon: [] };
      },
      'vagabond.tra_truoc_khach.so_du': function () { return { kha_dung_tam: 9000000 }; },
    });
    var tin = [];
    var g = {
      console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array,
      Promise: Promise, Error: Error, RegExp: RegExp, parseFloat: parseFloat, parseInt: parseInt, isNaN: isNaN, Date: Date,
      document: tl, frappe: { session: { user: 'sales@vagabond.vn' } },
      location: { href: 'https://app.x/bep', pathname: '/bep', hostname: 'app.x', search: '', hash: '', replace: function () {} },
      history: { pushState: function () {}, replaceState: function () {}, back: function () {} },
      requestAnimationFrame: function (f) { f(); },
      /* Chip phuong thuc ve lai cac khoi bang setTimeout(0): chay ngay de ca
         kiem thay dung cai Sales thay sau mot nhip. */
      setTimeout: function (f) { if (typeof f === 'function') f(); return 1; }, clearTimeout: function () {},
      setInterval: function () { return 1; }, clearInterval: function () {},
    };
    g.window = g;
    vm.createContext(g);
    vm.runInContext([
      'var root = document.getElementById("vgb");',
      'function h(s) { return String(s == null ? "" : s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;"); }',
      'function toast(s) { __tin.push("toast:" + s); }', 'function busy() {}',
      'function baoTin(s) { __tin.push("baoTin:" + s); return Promise.resolve(); }', 'function dSkin() {}',
      'function money(x) { return String(x); }', 'function num(x) { return Number(x) || 0; }',
      'function today() { return "2026-10-20"; }', 'function posNgayVn(x) { return x; }', 'function hasRole() { return true; }',
      'function errMsg(e) { return String((e && e.message) || e); }', 'function api(m, a) { return __mc.api(m, a); }',
      'var DS_MAU_HD = {}, KHACH_NO = {};', 'async function scrHome() { frame(APPNAME, "<div></div>"); }',
    ].concat(GIA_RONG.map(function (t) { return 'function ' + t + '() { return ""; }'; })).join('\n'),
    Object.assign(g, { __tin: tin, __mc: mc }));
    vm.runInContext(doc('01-khung-app.js'), g);
    vm.runInContext(doc('08-doanh-so-sales.js'), g);
    vm.runInContext(doc('54-ly-do-tang.js'), g);
    vm.runInContext(doc('55-so-du-tra-truoc.js'), g);
    return { g: g, tl: tl, mc: mc, tin: tin,
      mot: function (chon) { var r = tl.body.querySelectorAll(chon); if (r.length !== 1) throw new Error('mong dung 1 ' + chon + ', co ' + r.length); return r[0]; },
      bam: async function (el) { el.dispatchEvent(domGia.suKien('click', {}, el)); await nghi(); await nghi(); } };
  }
  function donSales(them) {
    return Object.assign({ name: 'ACC-SINV-2026-00009', docstatus: 0, posting_date: '2026-10-20', custom_nguon: 'Pancake',
      custom_pancake_display_id: '95631', items: [{ item_name: 'Bánh', qty: 1, rate: 750000, price_list_rate: 750000, amount: 750000 }],
      grand_total: 750000, vgb_pt_thanh_toan: 'Tiền mặt', customer: 'KL040476', customer_name: 'Mỹ Dung' }, them || {});
  }

  await ca('Màn Doanh thu Sales: bấm chip Hàng tặng thì khối lý do chọn sẵn hiện, lưu qua luu_tang', async function () {
    var app = manSales(donSales());
    await app.g.scrDsView('ACC-SINV-2026-00009'); await nghi(); await nghi();
    var ot = app.tl.getElementById('dsvTang');
    dung('có khối Hàng tặng', !!ot);
    bang('khối đang ẩn khi chọn Tiền mặt', ot.style.display, 'none');
    await app.bam(app.mot('#dsvPt [data-pt="Hàng tặng"]'.replace('#dsvPt ', '')));
    bang('khối hiện sau khi bấm chip', ot.style.display, 'block');
    await app.bam(app.mot('[data-tgl="noi_bo"]'));
    await app.bam(app.mot('[data-tgm="N1"]'));
    await app.bam(app.mot('#dsvTgLuu'));
    bang('lưu qua một cửa', app.mc.cac('vagabond.hang_tang.luu_tang').map(function (g) { return [g.a.name, g.a.ma_ly_do]; }),
      [['ACC-SINV-2026-00009', 'N1']]);
    bang('không đi cửa luu_thanh_toan', app.mc.cac('vagabond.ban_hang.luu_thanh_toan').length, 0);
  });

  await ca('Màn Doanh thu Sales: bấm chip Số dư trả trước thì khối số dư hiện và hỏi đúng khách trên đơn', async function () {
    var app = manSales(donSales());
    await app.g.scrDsView('ACC-SINV-2026-00009'); await nghi(); await nghi();
    var os = app.tl.getElementById('dsvSoDu');
    bang('ẩn lúc đầu', os.style.display, 'none');
    await app.bam(app.mot('[data-pt="Số dư trả trước"]'));
    await nghi();
    bang('hiện sau khi bấm', os.style.display, 'block');
    bang('hỏi số dư đúng khách', app.mc.cac('vagabond.tra_truoc_khach.so_du').map(function (g) { return g.a.khach; }).slice(-1), ['KL040476']);
    await app.bam(app.mot('[data-sdtluu]'));
    bang('áp số dư', app.mc.cac('vagabond.tra_truoc_khach.ap_dung').map(function (g) { return [g.a.khach, g.a.pt_con_lai]; }), [['KL040476', '']]);
  });

  await ca('Màn Nạp tiền: thiếu khách hay thiếu ảnh thì không lập phiếu; đủ thì gửi đúng khách, số tiền, nguồn', async function () {
    var app = manSales(donSales());
    app.mc.api = (function (cu) {
      return function (m, a) {
        if (m === 'vagabond.tra_truoc_khach.cai_dat') {
          app.mc.goi.push({ m: m, a: a });
          return Promise.resolve({ nguon: [
            { ma: 'ck_cty', nhan: 'Chuyển khoản vào tài khoản công ty', can_anh: 1, can_quay: 0, giai_thich: '' },
            { ma: 'gd_thu_ho', nhan: 'Tài khoản cá nhân Giám đốc', can_anh: 1, can_quay: 0, giai_thich: '' }],
            quay: [], thieu_tk_gd: 0 });
        }
        if (m === 'vagabond.tra_truoc_khach.tao_phieu_nap' || m === 'vagabond.tra_truoc_khach.so_khach') {
          app.mc.goi.push({ m: m, a: a });
          return Promise.resolve({ ok: 1, dong: [] });
        }
        return cu(m, a);
      };
    })(app.mc.api);
    app.g.xacNhan = function () { return Promise.resolve(true); };
    app.g.sheetTimKhach = function (t, cb) { cb({ name: 'KL040476', customer_name: 'Mỹ Dung' }); };
    await app.g.scrSoDuNap(); await nghi();
    await app.bam(app.mot('#sdtLuuNap'));
    bang('thiếu khách: không lập', app.mc.cac('vagabond.tra_truoc_khach.tao_phieu_nap').length, 0);
    await app.bam(app.mot('#sdtChonKh')); await nghi();
    app.mot('#sdtSoTien').value = '50.000.000';
    await app.bam(app.mot('[data-sdtng="gd_thu_ho"]')); await nghi();
    await app.bam(app.mot('#sdtLuuNap'));
    bang('thiếu ảnh: không lập', app.mc.cac('vagabond.tra_truoc_khach.tao_phieu_nap').length, 0);
    dung('nhắc đính ảnh', app.tin.some(function (t) { return t.indexOf('Đính ảnh') >= 0; }));
    app.g.sdtNap.anh = [{ ten: 'ck.jpg', noi_dung: 'data:image/jpeg;base64,AAA' }];
    await app.bam(app.mot('#sdtLuuNap'));
    var g = app.mc.cac('vagabond.tra_truoc_khach.tao_phieu_nap');
    bang('lập đúng một phiếu', g.length, 1);
    bang('tham số', [g[0].a.khach, g[0].a.so_tien, g[0].a.nguon, JSON.parse(g[0].a.anh).length], ['KL040476', 50000000, 'gd_thu_ho', 1]);
  });

  await ca('Codex #493 vòng 3: lần Lưu đầu mất phản hồi, bấm lại gửi CÙNG mã lần gửi; lập xong thì form mới có mã mới', async function () {
    var app = manSales(donSales());
    var lan = 0;
    app.mc.api = (function (cu) {
      return function (m, a) {
        if (m === 'vagabond.tra_truoc_khach.cai_dat') {
          app.mc.goi.push({ m: m, a: a });
          return Promise.resolve({ nguon: [{ ma: 'tien_mat', nhan: 'Tiền mặt tại quầy', can_anh: 0, can_quay: 1, giai_thich: '' }],
            quay: [{ ma: 'TCV', ten: 'Trần Cao Vân' }], thieu_tk_gd: 0 });
        }
        if (m === 'vagabond.tra_truoc_khach.tao_phieu_nap') {
          app.mc.goi.push({ m: m, a: a });
          lan++;
          /* Lần đầu máy chủ ĐÃ lập nhưng phản hồi mất giữa đường. */
          if (lan === 1) return Promise.reject(new Error('Mất kết nối'));
          return Promise.resolve({ ok: 1, doctype: 'Payment Entry', name: 'ACC-PAY-1', trung: 1 });
        }
        if (m === 'vagabond.tra_truoc_khach.so_khach') { app.mc.goi.push({ m: m, a: a }); return Promise.resolve({ dong: [] }); }
        return cu(m, a);
      };
    })(app.mc.api);
    app.g.xacNhan = function () { return Promise.resolve(true); };
    app.g.sheetTimKhach = function (t, cb) { cb({ name: 'KL040476', customer_name: 'Mỹ Dung' }); };
    await app.g.scrSoDuNap(); await nghi();
    await app.bam(app.mot('#sdtChonKh')); await nghi();
    app.mot('#sdtSoTien').value = '2.000.000';
    await app.bam(app.mot('[data-sdtng="tien_mat"]')); await nghi();
    await app.bam(app.mot('[data-sdtq="TCV"]')); await nghi();
    await app.bam(app.mot('#sdtLuuNap')); await nghi();
    await app.bam(app.mot('#sdtLuuNap')); await nghi();
    var g = app.mc.cac('vagabond.tra_truoc_khach.tao_phieu_nap');
    bang('hai lần gửi', g.length, 2);
    dung('có mã lần gửi: ' + g[0].a.ma_lan, /^[a-z0-9-]{16,64}$/.test(String(g[0].a.ma_lan)));
    bang('lần bấm lại dùng đúng mã cũ', g[1].a.ma_lan, g[0].a.ma_lan);
    dung('báo đã lập ở lần trước', app.tin.some(function (t) { return t.indexOf('đã lập ở lần bấm trước') >= 0; }));
    /* Form mới sau khi lập xong: mã mới. */
    await app.g.scrSoDuNap(); await nghi();
    dung('form mới có mã khác', app.g.sdtNap.ma_lan && app.g.sdtNap.ma_lan !== g[0].a.ma_lan);
  });

  /* ---------------- Man Duyet don tang: noi truoc con thieu gi ---------------- */
  function manDuyet(ct) {
    var goi = [], tin = [];
    var g = { console: console, JSON: JSON, String: String, Object: Object, Array: Array, Promise: Promise,
      h: function (s) { return String(s == null ? '' : s); }, money: function (x) { return String(x); },
      api: function (m, a) { goi.push({ m: m, a: a }); return Promise.resolve({ ok: 1, nguoi: 'ntla@x', ten: 'Loan Anh' }); },
      toast: function (m) { tin.push(m); }, baoTin: function (m) { tin.push(m); return Promise.resolve(); },
      errMsg: function (e) { return String(e && e.message); }, go: function () {}, hoiChu: function () { return Promise.resolve('ok'); },
      scrDuyetTang: function () {}, scrPosBill: function () {}, scrTangBaoCao: function () {} };
    vm.createContext(g);
    vm.runInContext(doc('41-duyet-don-tang.js'), g);
    g.dtgChiTiet['SI-95631'] = ct;
    return { g: g, goi: goi, tin: tin };
  }
  var DONG = { name: 'SI-95631', vgb_tang_duyet: 'Chờ duyệt', da_ghi_so: 0 };

  await ca('Màn duyệt: đơn thiếu lý do hiện thiếu gì ngay, không có nút Duyệt, có nút Nhắc người lập', async function () {
    var m = manDuyet({ mon: [], anh: [], cau_thieu: ['Đơn hàng tặng phải ghi rõ LÝ DO tặng cho ai.'] });
    var s = m.g.dtgThan(DONG, { duyet_duoc: 1 });
    dung('nói chưa duyệt được', s.indexOf('Chưa duyệt được, còn thiếu') >= 0);
    dung('liệt kê câu thiếu', s.indexOf('LÝ DO tặng cho ai') >= 0);
    bang('không có nút Duyệt', s.indexOf('data-dtgok'), -1);
    dung('có nút Nhắc', s.indexOf('data-dtgnhac="SI-95631"') >= 0);
    await m.g.dtgBam({ target: { closest: function (c) { return c === '[data-dtgnhac]' ? { getAttribute: function () { return 'SI-95631'; } } : null; } } });
    bang('gọi nhắc đúng đơn', m.goi.map(function (x) { return [x.m, x.a.name]; }), [['vagabond.hang_tang.nhac_nguoi_lap', 'SI-95631']]);
    dung('báo đã nhắc ai', m.tin.some(function (t) { return t.indexOf('Loan Anh') >= 0; }));
  });

  await ca('Màn duyệt: đơn đủ thông tin vẫn có nút Duyệt như cũ, không có nút Nhắc', async function () {
    var m = manDuyet({ mon: [], anh: [], cau_thieu: [] });
    var s = m.g.dtgThan(DONG, { duyet_duoc: 1 });
    dung('có nút Duyệt', s.indexOf('data-dtgok="SI-95631"') >= 0);
    bang('không có Nhắc', s.indexOf('data-dtgnhac'), -1);
    bang('không có khung thiếu', s.indexOf('Chưa duyệt được, còn thiếu'), -1);
  });

  console.log('Bo ca kiem HANH VI v607 (ly do tang chon san, so du tra truoc)');
  ket.loi.forEach(function (l) { console.log('  HONG ' + l); });
  console.log(ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng, tổng ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
})();

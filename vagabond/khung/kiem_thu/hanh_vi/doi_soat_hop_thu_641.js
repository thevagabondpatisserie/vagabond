/* Bo ca kiem HANH VI v641: doi soat tu dong qua hop thu doisoat@ tren app /bep.
 *
 * Anh Viet duyet 8 anh 06/11/2026: khoi Hop thu dau man, dai Tien do sau buoc,
 * chip Duong vao, moi nguon mot thanh sau buoc, man Thu bi chan / Chua ve / Cho
 * duyet, tai tay cho giam doc duyet, nut Xac nhan chi mo khi nam buoc truoc xanh.
 *
 * CHAY THAT: 01-khung-app.js, 15-khuon-danh-sach.js, 52-doi-soat-vendor.js.
 * May chu la ban gia. Ca bam dung chuoi thao tac cua ke toan va giam doc,
 * KHONG goi them ham nao cua man de "cho chac" (quy tac 15).
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/doi_soat_hop_thu_641.js
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

var NHAN = ['Từ hộp thư đối soát', 'Chữ ký số của đối tác hợp lệ', 'Đọc đủ dòng, khớp tổng trên tệp', 'Tiền về ngân hàng khớp',
  'Đủ chứng từ', 'Chờ kế toán xác nhận'];

function nguon(name, them) {
  return Object.assign({ name: name, vendor: 'OnePay', nhom: 'Tiền bán', ten_mau: 'OnePay tạm ứng ngày', tu_ngay: '2026-11-05',
    den_ngay: '2026-11-05', trang_thai: 'Đã nhận', trang_thai_tien: 'Đã thấy tiền về', so_dong: 31, thuc_nhan: 18014760,
    so_chua_noi: 0, so_da_noi: 31, kenh_nhan: 'Hộp thư đối soát', duong_vao: 'Từ thư' }, them || {});
}

function mayChu(canh) {
  canh = canh || {};
  var goi = [];
  return {
    goi: goi,
    cuoi: function (m) { var r = goi.filter(function (x) { return x.m === m; }); return r[r.length - 1]; },
    dem: function (m) { return goi.filter(function (x) { return x.m === m; }).length; },
    api: async function (m, a) {
      goi.push({ m: m, a: JSON.parse(JSON.stringify(a || {})) });
      if (m === 'vagabond.doi_soat_vendor.ds') {
        return { hang: [
          nguon('DSN-1', { buoc: 'xxxdnn', buoc_hien: 4, buoc_ghi: 'Lệch tiền về', duong: 'thu', trang_thai_tien: 'Lệch tiền về' }),
          nguon('DSN-2', { vendor: 'ShopeeFood', kenh_nhan: 'Tải tay', duong_vao: 'Chờ duyệt', buoc: 'xvxxxn', buoc_hien: 2,
            buoc_ghi: 'Tải tay, chờ Giám đốc duyệt', duong: 'cho_duyet' })],
          dem: { tat_ca: 2, 'Lệch tiền về': 1, 'Chờ tiền về': 1, 'nhom:Tiền bán': 2 },
          dem_vendor: { tat_ca: 2, OnePay: 1, ShopeeFood: 1 }, vendor: ['OnePay', 'ShopeeFood'], con: 0, tong: { tat_ca: 1 },
          dem_duong: { tat_ca: 2, thu: 1, cho_duyet: 1 }, dem_buoc: { 4: 1, 6: 3 }, cong_ty_nhan: ['Vagabond'], nhan_cong_ty: {} };
      }
      if (m === 'vagabond.doi_soat_vendor.suc_khoe') return [];
      if (m === 'vagabond.doi_soat_vendor.hop_thu') {
        if (canh.hopLoi) throw new Error('lỗi đọc');
        return Object.assign({ trang: 'chay', dia_chi: 'doisoat@thevagabondpatisserie.com', doc_luc: '2026-11-06 12:15:00', loi: '',
          ve_hom_nay: 7, chua_ve: 1, bi_chan: 1, cho_duyet: 1, quan_tri: 0 }, canh.ht || {});
      }
      if (m === 'vagabond.doi_soat_vendor.ds_thu') {
        if (a.loai === 'chua_ve') return { ds: [{ vendor: 'Payoo', tai_khoan: '', ngay: '2026-11-05', han: '12:00', khoa: 'k' }] };
        if (a.loai === 'tai_tay') return { ds: [nguon('DSN-2', { vendor: 'ShopeeFood', kenh_nhan: 'Tải tay', duong_vao: 'Chờ duyệt',
          ly_do_tai_tay: 'ShopeeFood không gửi thư ngày 04/11' })] };
        return { ds: [{ name: 'DST-9', nguoi_gui: 'OnePay <payment@onepay.vn>', ten_mien: 'onepay.vn', tieu_de: 'TB tam ung 06/11',
          nhan_luc: '2026-11-06 09:40:00', doi_tac: 'OnePay', ly_do: 'Thư không có chữ ký số của onepay.vn.', so_tep: 1,
          bao_zalo: '2026-11-06 09:41:00' }] };
      }
      if (m === 'vagabond.doi_soat_vendor.chi_tiet') {
        var n = canh.ct || nguon(a.name);
        return { nguon: n, buoc: canh.buoc || { tt: 'xxxxxv', hien: 6, ghi: 'Chờ kế toán xác nhận', nhan: NHAN, xac_nhan_duoc: 1 },
          quyen: canh.quyen || { xac_nhan: 1, duyet: 0, cua_minh: 0 },
          can_cu: canh.canCu === false ? null : { name: 'DST-1', nguoi_gui: 'OnePay <no-reply@onepay.vn>', nhan_luc: '2026-11-06 08:02:00',
            ky_boi: 'onepay.vn', sha256: '9f2c…b71a' },
          them: { tien_ve: '', ban_sua: [], phi_vuot: canh.phiVuot || null }, dong: [], con: 0 };
      }
      if (m === 'vagabond.doi_soat_vendor.duyet_nguon') return { ok: 1 };
      if (m === 'vagabond.doi_soat_vendor.tu_choi_nguon') return { ok: 1 };
      if (m === 'vagabond.doi_soat_vendor.xac_nhan_nguon') return { ok: 1 };
      if (m === 'vagabond.doi_soat_vendor.tai_thu_goc') return { ten: 'thu-DST-1.eml', noi_dung: 'RnJvbTog' };
      if (m === 'vagabond.doi_soat_vendor.thu_ket_noi') return { ok: 1, so_thu: 12 };
      if (m === 'vagabond.doi_soat_vendor.doc_hop_thu_ngay') return canh.docLoi ? { so_thu: 0, loi: 'sai mật khẩu hoặc tên đăng nhập hộp thư.' } : { so_thu: 3 };
      throw new Error('API ngoài dự kiến ' + m);
    },
  };
}

function appMoi(canh) {
  canh = canh || {};
  var tl = domGia.taiLieuGia();
  var vgb = tl.createElement('div'); vgb.id = 'vgb'; tl.body.appendChild(vgb);
  var mc = mayChu(canh);
  var tin = [], tai = [];
  var g = {
    console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array,
    Promise: Promise, Error: Error, RegExp: RegExp, parseFloat: parseFloat, parseInt: parseInt, isNaN: isNaN, Date: Date,
    Uint8Array: Uint8Array, document: tl,
    atob: function (s) { return Buffer.from(s, 'base64').toString('binary'); },
    Blob: function (ds, o) { this.ds = ds; this.type = o && o.type; },
    URL: { createObjectURL: function (b) { tai.push(b.type); return 'blob:x'; } },
    frappe: { session: { user: 'ketoan@vagabond.vn' } },
    location: { href: 'https://app.x/bep', pathname: '/bep', hostname: 'app.x', search: '', hash: '', replace: function () {} },
    history: { pushState: function () {}, replaceState: function () {}, back: function () {} },
    requestAnimationFrame: function (f) { f(); },
    setTimeout: function (f) { f(); return 1; }, clearTimeout: function () {},
  };
  g.window = g;
  vm.createContext(g);
  vm.runInContext([
    'var root = document.getElementById("vgb");',
    'function h(s) { return String(s == null ? "" : s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;"); }',
    'function toast(s) { __tin.push("toast:" + s); }',
    'var __ban = 0; function busy(b) { __ban += b ? 1 : -1; }',
    'function baoTin(s) { __tin.push("baoTin:" + s); return Promise.resolve(); }',
    'function dSkin() {}',
    'function money(x) { return String(x); }',
    'function dmy(x) { var p = String(x || "").split("-"); return p.length === 3 ? p[2] + "/" + p[1] + "/" + p[0] : ""; }',
    'function posChipNut(thuoc, nhan, bat) { return "<button class=\\"chip\\" data-bat=\\"" + (bat ? 1 : 0) + "\\" " + thuoc + ">" + nhan + "</button>"; }',
    'function kmHangChip(noiDung) { return "<div>" + noiDung + "</div>"; }',
    'function errMsg(e) { return String((e && e.message) || e); }',
    'var __hoi = []; function confirmSheet(t, m, ok, nguy) { __hoi.push(t + "|" + m); return Promise.resolve(__canh.dongY !== false); }',
    'function api(m, a) { return __mc.api(m, a); }',
    'async function scrHome() { frame(APPNAME, "<div></div>"); }',
  ].join('\n'), Object.assign(g, { __tin: tin, __mc: mc, __canh: canh }));
  vm.runInContext(doc('01-khung-app.js'), g);
  vm.runInContext(doc('15-khuon-danh-sach.js'), g);
  vm.runInContext(doc('52-doi-soat-vendor.js'), g);
  vm.runInContext('S.roles = ["Accounts User"];', g);
  return {
    g: g, tl: tl, mc: mc, tin: tin, tai: tai,
    tim: function (chon) { return tl.body.querySelectorAll(chon); },
    mot: function (chon) { var r = tl.body.querySelectorAll(chon); if (r.length !== 1) throw new Error('mong dung 1 ' + chon + ', co ' + r.length); return r[0]; },
    bam: async function (el) { el.dispatchEvent(domGia.suKien('click', {}, el)); await nghi(); await nghi(); },
    chu: function () { return tl.body.outerHTML; },
  };
}

async function moTrungTam(canh) {
  var app = appMoi(canh);
  await app.g.reset(app.g.scrDsvn); await nghi(); await nghi();
  return app;
}

async function moChiTiet(canh) {
  var app = await moTrungTam(canh);
  await app.bam(app.tim('[data-dsvnct="DSN-1"]')[0]);
  return app;
}

(async function () {
  await ca('Khối hộp thư: trạng thái, giờ đọc, bốn ô đếm do máy chủ gửi', async function () {
    var app = await moTrungTam();
    var c = app.chu();
    dung('tên hộp', c.indexOf('Hộp thư doisoat@thevagabondpatisserie.com') >= 0);
    dung('đang chạy', c.indexOf('Đang chạy') >= 0);
    dung('giờ đọc', c.indexOf('Đọc lần cuối 12:15 06/11') >= 0);
    bang('bốn ô', app.tim('[data-dsvnthu]').map(function (x) { return x.getAttribute('data-dsvnthu'); }), ['ve', 'chua_ve', 'chan', 'tai_tay']);
    bang('không phải quản trị thì không có nút thử kết nối', app.tim('#dsvnThuKetNoi').length, 0);
  });

  await ca('Khối hộp thư: máy chủ báo lỗi đọc thì hiện lời lỗi; khối hỏng thì màn vẫn mở', async function () {
    var app = await moTrungTam({ ht: { trang: 'loi', loi: 'sai mật khẩu hoặc tên đăng nhập hộp thư.' } });
    var c = app.chu();
    dung('lỗi', c.indexOf('Lỗi đọc thư') >= 0 && c.indexOf('Không đọc được hộp thư: sai mật khẩu') >= 0);
    var app2 = await moTrungTam({ hopLoi: true });
    bang('màn vẫn có danh sách', app2.tim('[data-dsvnct]').length, 2);
  });

  await ca('Dải tiến độ: bước 4 đếm 1, bấm thì lọc theo bước ở máy chủ, bấm lại bỏ lọc', async function () {
    var app = await moTrungTam();
    dung('ô bước 4', app.mot('[data-dsvnbuoc="4"]').outerHTML.indexOf('Lệch tiền') >= 0);
    await app.bam(app.mot('[data-dsvnbuoc="4"]'));
    bang('lọc bước 4', app.mc.cuoi('vagabond.doi_soat_vendor.ds').a.buoc, '4');
    dung('nói đang lọc', app.chu().indexOf('Đang xem nguồn kẹt ở bước 4: Khớp tiền') >= 0);
    await app.bam(app.mot('[data-dsvnbuoc="4"]'));
    bang('bỏ lọc', app.mc.cuoi('vagabond.doi_soat_vendor.ds').a.buoc, '');
  });

  await ca('Dải tiến độ: bước 1 mở thẻ Thư chưa về, bước 2 mở thẻ Chờ duyệt', async function () {
    var app = await moTrungTam();
    await app.bam(app.mot('[data-dsvnbuoc="1"]'));
    bang('thẻ chưa về', app.mc.cuoi('vagabond.doi_soat_vendor.ds_thu').a.loai, 'chua_ve');
    var c = app.chu();
    dung('thiếu thư Payoo', c.indexOf('Payoo · ngày 05/11') >= 0 && c.indexOf('Thiếu thư') >= 0 && c.indexOf('Thư dự kiến trước 12:00') >= 0);
    await app.bam(app.mot('[data-dsvntab="tai_tay"]'));
    bang('thẻ chờ duyệt', app.mc.cuoi('vagabond.doi_soat_vendor.ds_thu').a.loai, 'tai_tay');
    dung('lý do tải tay', app.chu().indexOf('Lý do: ShopeeFood không gửi thư ngày 04/11') >= 0);
    await app.bam(app.mot('[data-dsvnct="DSN-2"]'));
    bang('mở chi tiết', app.mc.cuoi('vagabond.doi_soat_vendor.chi_tiet').a.name, 'DSN-2');
  });

  await ca('Thư bị chặn: nói rõ không nhận số liệu, không có nút Nhận, có Đã báo Zalo, tải được thư gốc', async function () {
    var app = await moTrungTam();
    await app.bam(app.mot('[data-dsvnthu="chan"]'));
    bang('thẻ chặn', app.mc.cuoi('vagabond.doi_soat_vendor.ds_thu').a.loai, 'chan');
    var c = app.chu();
    dung('tự xưng', c.indexOf('Thư tự xưng OnePay') >= 0);
    dung('không nhận số liệu', c.indexOf('Không nhận số liệu nào từ thư này') >= 0);
    dung('đã báo Zalo', c.indexOf('Đã báo Zalo 09:41') >= 0);
    bang('không có nút nhận hay duyệt', app.tim('#dsvnNhan').length + app.tim('[data-dsvnduyet]').length, 0);
    await app.bam(app.mot('[data-dsvneml="DST-9"]'));
    bang('tải thư gốc', app.mc.cuoi('vagabond.doi_soat_vendor.tai_thu_goc').a.name, 'DST-9');
    bang('tệp thư', app.tai, ['message/rfc822']);
  });

  await ca('Chip đường vào: gửi đúng khoá lên máy chủ; dòng mang thanh sáu bước và nhãn đường vào', async function () {
    var app = await moTrungTam();
    var c = app.chu();
    dung('nhãn chờ duyệt', c.indexOf('Chờ giám đốc duyệt') >= 0 && c.indexOf('Từ thư ✓') >= 0);
    dung('thanh bước nói kẹt gì', c.indexOf('Lệch tiền về</span></div>') >= 0);
    dung('không lộ mã bước', c.indexOf('xxxdnn') < 0 && c.indexOf('cho_duyet<') < 0);
    await app.bam(app.mot('[data-dscc="duong|cho_duyet"]'));
    bang('lọc chờ duyệt', app.mc.cuoi('vagabond.doi_soat_vendor.ds').a.duong, 'cho_duyet');
    await app.bam(app.mot('[data-dscc="duong|"]'));
    bang('bỏ lọc', app.mc.cuoi('vagabond.doi_soat_vendor.ds').a.duong, '');
  });

  await ca('Ô Thư về hôm nay lọc chip Đường vào Từ thư', async function () {
    var app = await moTrungTam();
    await app.bam(app.mot('[data-dsvnthu="ve"]'));
    bang('lọc từ thư', app.mc.cuoi('vagabond.doi_soat_vendor.ds').a.duong, 'thu');
  });

  await ca('Đọc hộp thư ngay: lỗi mật khẩu thì báo lời của máy chủ', async function () {
    var app = await moTrungTam({ docLoi: true });
    await app.bam(app.mot('#dsvnDocThu'));
    dung('báo', app.tin.some(function (t) { return t.indexOf('Chưa đọc được hộp thư: sai mật khẩu') >= 0; }));
    bang('busy cân bằng', app.g.__ban, 0);
  });

  await ca('Quản trị: có nút Thử kết nối, bấm thì báo số thư trong thư mục', async function () {
    var app = await moTrungTam({ ht: { quan_tri: 1 } });
    await app.bam(app.mot('#dsvnThuKetNoi'));
    dung('báo', app.tin.some(function (t) { return t.indexOf('Kết nối được. Thư mục đang có 12 thư') >= 0; }));
  });

  await ca('Chi tiết: căn cứ thư gốc có chữ ký, mã băm, tải .eml; năm bước xanh thì Xác nhận mở và gọi đúng nguồn', async function () {
    var app = await moChiTiet();
    var c = app.chu();
    dung('chữ ký', c.indexOf('✓ onepay.vn, hợp lệ') >= 0 && c.indexOf('9f2c…b71a') >= 0);
    dung('đường đi', c.indexOf('Hộp thư công ty → doisoat@') >= 0);
    var nut = app.mot('#dsvnXacNhan');
    dung('mở', !nut.hasAttribute('disabled'));
    await app.bam(nut);
    bang('xác nhận đúng nguồn', app.mc.cuoi('vagabond.doi_soat_vendor.xac_nhan_nguon').a.name, 'DSN-1');
  });

  await ca('Chi tiết: chưa đủ năm bước thì nút Xác nhận khoá, nói lý do, bấm không gọi máy chủ', async function () {
    var app = await moChiTiet({ buoc: { tt: 'xxxdxn', hien: 4, ghi: 'Lệch tiền về', nhan: NHAN, xac_nhan_duoc: 0 } });
    var nut = app.mot('#dsvnXacNhan');
    dung('khoá', nut.hasAttribute('disabled'));
    dung('lý do', app.chu().indexOf('Mở khi năm bước trước xanh: Lệch tiền về') >= 0);
    await app.bam(nut);
    bang('không gọi', app.mc.dem('vagabond.doi_soat_vendor.xac_nhan_nguon'), 0);
  });

  await ca('Chi tiết tải tay: giám đốc duyệt gọi đúng nguồn; từ chối phải ghi lý do', async function () {
    var ct = nguon('DSN-2', { kenh_nhan: 'Tải tay', duong_vao: 'Chờ duyệt', ly_do_tai_tay: 'ShopeeFood không gửi thư' });
    var app = await moChiTiet({ ct: ct, canCu: false, quyen: { duyet: 1, xac_nhan: 0 },
      buoc: { tt: 'xvxxxn', hien: 2, ghi: 'Tải tay, chờ Giám đốc duyệt', nhan: NHAN, xac_nhan_duoc: 0 } });
    dung('khối chờ duyệt', app.chu().indexOf('Tải tay, chờ giám đốc duyệt') >= 0 && app.chu().indexOf('Lý do tải tay: ShopeeFood không gửi thư') >= 0);
    await app.bam(app.mot('[data-dsvnduyet="0"]'));
    bang('thiếu lý do: không từ chối', app.mc.dem('vagabond.doi_soat_vendor.tu_choi_nguon'), 0);
    dung('nhắc lý do', app.tin.some(function (t) { return t.indexOf('Ghi lý do từ chối') >= 0; }));
    app.mot('#dsvnLyTc').value = 'Sai kỳ báo cáo';
    await app.bam(app.mot('[data-dsvnduyet="0"]'));
    bang('từ chối kèm lý do', app.mc.cuoi('vagabond.doi_soat_vendor.tu_choi_nguon').a, { name: 'DSN-2', ly_do: 'Sai kỳ báo cáo' });
    await app.bam(app.mot('[data-dsvnduyet="1"]'));
    bang('duyệt', app.mc.cuoi('vagabond.doi_soat_vendor.duyet_nguon').a, { name: 'DSN-2' });
    bang('busy cân bằng', app.g.__ban, 0);
  });

  await ca('Chi tiết tải tay của chính mình: không có nút duyệt, nói giám đốc còn lại duyệt', async function () {
    var ct = nguon('DSN-2', { kenh_nhan: 'Tải tay', duong_vao: 'Chờ duyệt' });
    var app = await moChiTiet({ ct: ct, canCu: false, quyen: { duyet: 0, cua_minh: 1, xac_nhan: 1 },
      buoc: { tt: 'xvxxxn', hien: 2, ghi: 'Tải tay, chờ Giám đốc duyệt', nhan: NHAN, xac_nhan_duoc: 0 } });
    bang('không nút duyệt', app.tim('[data-dsvnduyet]').length, 0);
    dung('nói rõ', app.chu().indexOf('không tự duyệt được') >= 0);
  });

  await ca('Chi tiết: phí thu cao hơn biểu phí hiện từng loại thẻ và số dư', async function () {
    var app = await moChiTiet({ phiVuot: { tong: 2544, ct: [{ the: 'MASTERCARD', vung: 'DOMESTIC', mdr: 2.5, bieu: 1.44, du: 2544, gop: 240000 }] } });
    var c = app.chu();
    dung('phí', c.indexOf('Phí thu cao hơn biểu phí hợp đồng') >= 0 && c.indexOf('thu 2,5%, hợp đồng 1,44%, dư <b>2544 đ</b>') >= 0);
  });

  console.log('Doi soat hop thu 641: ' + ket.dat + ' dat, ' + ket.hong + ' hong');
  if (ket.hong) { console.log('  HONG  ' + ket.loi.join('\n  HONG  ')); process.exit(1); }
})().catch(function (e) { console.error(e); process.exit(1); });

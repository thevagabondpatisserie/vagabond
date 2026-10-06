/* Bo ca kiem HANH VI v579 (#420): man Doi soat nha cung cap tren app /bep.
 *
 * CHAY THAT:
 *   - khung app that (01-khung-app.js: go, reset, frame),
 *   - thanh cong cu danh sach that (15-khuon-danh-sach.js),
 *   - man doi soat that (52-doi-soat-vendor.js).
 * May chu va FileReader la ban gia. Ca kiem bam dung chuoi thao tac cua ke
 * toan (bam chip, bam dong, chon tep, bam Nhan), KHONG goi them ham nao cua
 * man de "cho chac" (quy tac 15). Khong do CSS: anh chup nam tren PR.
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/doi_soat_vendor_579.js
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

/* ---------------- may chu gia ---------------- */
function nguon(name, vendor, tt, them) {
  return Object.assign({ name: name, vendor: vendor, nhom: 'Tiền bán', ten_mau: 'Báo cáo ngày', tu_ngay: '2026-07-17',
    den_ngay: '2026-07-17', trang_thai: tt, trang_thai_tien: '', so_dong: 3, thuc_nhan: 668915, so_chua_noi: 0,
    so_da_noi: 3, kenh_nhan: 'Tải tay' }, them || {});
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
        if (canh.dsLoi) throw new Error('Đối soát nhà cung cấp chỉ mở cho Kế toán và Giám đốc.');
        return { hang: [nguon('DSN-1', 'GrabFood', 'Đã nhận', { so_chua_noi: 2 }), nguon('DSN-2', 'Payoo', 'Cần xử lý')],
          dem: { tat_ca: 2, 'Cần xử lý': 1, 'Chưa thấy tiền về': 1, 'nhom:Tiền bán': 2, 'nhom:Thẻ tín dụng': 1 },
          dem_vendor: { tat_ca: 2, GrabFood: 1, Payoo: 1 }, vendor: ['GrabFood', 'Payoo'], con: 0 };
      }
      if (m === 'vagabond.doi_soat_vendor.suc_khoe') {
        return [{ vendor: 'GrabFood', so_nguon: 1, ky_moi: '2026-07-17' }, { vendor: 'Be', so_nguon: 0 }];
      }
      if (m === 'vagabond.doi_soat_vendor.tai_len') return { file_url: '/private/files/x.pdf', ten: a.ten };
      if (m === 'vagabond.doi_soat_vendor.xem_truoc') {
        if (canh.daCo) return [{ ten_tep: 'x.pdf', ten_mau: 'GrabFood: báo cáo ngày', da_co: 'DSN-1', mau: 'grabfood', loi: [], so: {} }];
        return [{ ten_tep: 'x.pdf', ten_mau: 'GrabFood: báo cáo ngày', mau: 'grabfood', nhom: 'Tiền bán', trang_thai: 'Cần xử lý',
          tu_ngay: '2026-07-17', den_ngay: '2026-07-17', ngay_tien_ve: '2026-07-18', so: { moi: 4, trung: 0, loi: 1 },
          tong: { thuc_nhan: 668915 }, tong_tep: { thuc_nhan: 668915 }, loi: [], canh_bao: [],
          dong_loi: [{ vi_tri: 9, ly_do: 'Dòng đơn không đọc được' }] }];
      }
      if (m === 'vagabond.doi_soat_vendor.nhan') return [{ name: 'DSN-9' }];
      if (m === 'vagabond.doi_soat_vendor.chi_tiet') {
        var dong = [
          { name: 'a', ma_don: 'GF-101', loai: 'ban', ngay: '2026-07-17', gio: '21:28:00', thuc_nhan: 210641, phi: 49359,
            trang_thai_khop: 'Đã nối', sales_invoice: 'HDB-1' },
          { name: 'b', ma_don: '', mo_ta: '', loai: 'phi_ky', ngay: '2026-07-17', thuc_nhan: -49140, trang_thai_khop: 'Không áp dụng' },
          { name: 'c', ma_don: 'GF-103F', loai: 'ban', ngay: '2026-07-17', thuc_nhan: 144976, trang_thai_khop: 'Không thấy chứng từ',
            ghi_chu_khop: 'Không có hoá đơn bán cùng mã hoặc cùng tiền trong khoảng ngày.' }];
        if (a.loc === 'chua_noi') dong = dong.filter(function (d) { return d.trang_thai_khop !== 'Đã nối' && d.trang_thai_khop !== 'Không áp dụng'; });
        return { nguon: nguon(a.name, 'GrabFood', 'Đã nhận', { trang_thai_tien: 'Đã thấy tiền về', giao_dich_ngan_hang: 'BT-1', tong_tep: 668915,
          so_chua_noi: 1, so_da_noi: 1 }), them: { tien_ve: '' }, dong: dong, con: 0 };
      }
      if (m === 'vagabond.doi_soat_vendor.doi_chieu_lai') return { ok: 1 };
      if (m === 'vagabond.doi_soat_vendor.quet_email') return { so_tep: 2 };
      if (m === 'vagabond.doi_soat_vendor.cua_hoa_don') {
        return [{ vendor: 'GrabFood', ma_don: 'GF-101', trang_thai_khop: 'Đã nối', tien_hang: 260000, phi: 49359, thuc_nhan: 210641, nguon: 'DSN-1' }];
      }
      throw new Error('API ngoài dự kiến ' + m);
    },
  };
}

function appMoi(canh) {
  canh = canh || {};
  var tl = domGia.taiLieuGia();
  var vgb = tl.createElement('div'); vgb.id = 'vgb'; tl.body.appendChild(vgb);
  var mc = mayChu(canh);
  var tin = [], tep = { doc: 0 };
  var g = {
    console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array,
    Promise: Promise, Error: Error, RegExp: RegExp, parseFloat: parseFloat, parseInt: parseInt, isNaN: isNaN, Date: Date,
    document: tl,
    frappe: { session: { user: 'ketoan@vagabond.vn' } },
    location: { href: 'https://app.x/bep', pathname: '/bep', hostname: 'app.x', search: '', hash: '', replace: function () {} },
    history: { pushState: function () {}, replaceState: function () {}, back: function () {} },
    requestAnimationFrame: function (f) { f(); },
    setTimeout: function (f) { f(); return 1; }, clearTimeout: function () {},
    /* FileReader gia: doc xong la goi onload ngay, nhu trinh duyet sau khi doc tep. */
    FileReader: function () {
      var r = this;
      r.readAsDataURL = function (f) { tep.doc++; r.result = 'data:application/pdf;base64,JVBERi0='; Promise.resolve().then(function () { r.onload(); }); };
    },
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
    'function api(m, a) { return __mc.api(m, a); }',
    'var __xemDon = []; function scrDsView(si) { __xemDon.push(si); frame("Đơn " + si, "<div>don</div>"); }',
    'async function scrHome() { frame(APPNAME, "<div></div>"); }',
  ].join('\n'), Object.assign(g, { __tin: tin, __mc: mc }));
  vm.runInContext(doc('01-khung-app.js'), g);
  vm.runInContext(doc('15-khuon-danh-sach.js'), g);
  vm.runInContext(doc('52-doi-soat-vendor.js'), g);
  /* Quyen that cua khung app (coQuyenKeToan doc S.roles), khong bia lai. */
  vm.runInContext('S.roles = ' + JSON.stringify(canh.keToan === false ? ['Thu ngân'] : ['Accounts User']) + ';', g);
  return {
    g: g, tl: tl, mc: mc, tin: tin, tep: tep,
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

(async function () {
  await ca('Trung tâm: bốn ô việc cần làm, ba nhóm, danh sách đọc từ máy chủ, không tự đếm', async function () {
    var app = await moTrungTam();
    var ds = app.mc.cuoi('vagabond.doi_soat_vendor.ds');
    bang('lọc mặc định', [ds.a.nhom, ds.a.trang_thai, ds.a.ky], ['Tiền bán', '', '']);
    var c = app.chu();
    dung('ô cần xử lý', c.indexOf('Cần xử lý') >= 0);
    dung('sức khoẻ: 1/2 nguồn, 1 chưa có tệp', c.indexOf('1/2 nguồn đã từng nhận') >= 0 && c.indexOf('1 nguồn chưa có tệp nào') >= 0);
    bang('hai dòng nguồn', app.tim('[data-dsvnct]').length, 2);
    dung('tiền về trống hiện Chưa đối chiếu, không hiện ô rỗng', c.indexOf('Chưa đối chiếu') >= 0);
    dung('đếm nhóm Thẻ tín dụng lấy từ máy chủ', c.indexOf('Thẻ tín dụng 1') >= 0);
  });

  await ca('Bấm nhóm Thẻ tín dụng: hỏi lại máy chủ đúng nhóm, bỏ lọc nguồn cũ', async function () {
    var app = await moTrungTam();
    app.g.DSVN.vendor = 'Payoo';
    await app.bam(app.mot('[data-dsvnnhom="Thẻ tín dụng"]'));
    var ds = app.mc.cuoi('vagabond.doi_soat_vendor.ds');
    bang('nhóm và nguồn', [ds.a.nhom, ds.a.vendor], ['Thẻ tín dụng', '']);
  });

  await ca('Thanh công cụ dùng chung: chip ngày 7 ngày và chip nguồn gửi đúng khoá lên máy chủ', async function () {
    var app = await moTrungTam();
    await app.bam(app.mot('[data-dscc="ky|7_ngay"]'));
    bang('kỳ', app.mc.cuoi('vagabond.doi_soat_vendor.ds').a.ky, '7_ngay');
    await app.bam(app.mot('[data-dscc="ven|Payoo"]'));
    bang('nguồn', app.mc.cuoi('vagabond.doi_soat_vendor.ds').a.vendor, 'Payoo');
    await app.bam(app.mot('[data-dscc="tt|Cần xử lý"]'));
    bang('trạng thái', app.mc.cuoi('vagabond.doi_soat_vendor.ds').a.trang_thai, 'Cần xử lý');
  });

  await ca('Bấm ô Cần xử lý trong việc cần làm thì lọc đúng trạng thái', async function () {
    var app = await moTrungTam();
    await app.bam(app.mot('[data-dsvntt="Cần xử lý"]'));
    bang('trạng thái', app.mc.cuoi('vagabond.doi_soat_vendor.ds').a.trang_thai, 'Cần xử lý');
  });

  await ca('Không có quyền: máy chủ chặn thì hiện lời của máy chủ, không vẽ danh sách rỗng giả', async function () {
    var app = await moTrungTam({ dsLoi: true });
    dung('lời chặn', app.chu().indexOf('chỉ mở cho Kế toán và Giám đốc') >= 0);
    bang('không có nút tải', app.tim('#dsvnTai').length, 0);
  });

  await ca('Nhận lại từ email: gọi quét 7 ngày rồi báo số tệp', async function () {
    var app = await moTrungTam();
    await app.bam(app.mot('#dsvnEmail'));
    bang('số ngày', app.mc.cuoi('vagabond.doi_soat_vendor.quet_email').a.so_ngay, 7);
    dung('báo', app.tin.some(function (t) { return t.indexOf('Đã đọc 2 tệp') >= 0; }));
  });

  await ca('Tải file: chọn tệp, xem trước rồi mới nhận; dòng lỗi hiện kèm lý do; nhận một nguồn thì mở thẳng chi tiết', async function () {
    var app = await moTrungTam();
    await app.bam(app.mot('#dsvnTai'));
    bang('chưa xem trước thì chưa có nút Nhận', app.tim('#dsvnNhan').length, 0);
    var inp = app.mot('#dsvnFile');
    inp.files = [{ name: 'GrabFood-20260717.pdf' }];
    inp.onchange(); await nghi(); await nghi(); await nghi();
    bang('tải lên đúng tên', app.mc.cuoi('vagabond.doi_soat_vendor.tai_len').a.ten, 'GrabFood-20260717.pdf');
    bang('xem trước đúng tệp vừa tải', app.mc.cuoi('vagabond.doi_soat_vendor.xem_truoc').a.file_url, '/private/files/x.pdf');
    bang('chưa nhận gì khi mới xem trước', app.mc.dem('vagabond.doi_soat_vendor.nhan'), 0);
    var c = app.chu();
    dung('lý do dòng lỗi', c.indexOf('Dòng 9: Dòng đơn không đọc được') >= 0);
    dung('nói rõ chưa ghi sổ', c.indexOf('Chưa ghi sổ hoặc thanh toán') >= 0);
    var nb = app.mot('#dsvnNhan');
    dung('nhãn đếm dòng hợp lệ', nb.outerHTML.indexOf('Nhận 4 dòng hợp lệ') >= 0);
    await app.bam(nb); await nghi();
    bang('nhận đúng tệp', app.mc.cuoi('vagabond.doi_soat_vendor.nhan').a.file_url, '/private/files/x.pdf');
    bang('mở chi tiết nguồn vừa nhận', app.mc.cuoi('vagabond.doi_soat_vendor.chi_tiet').a.name, 'DSN-9');
    bang('busy cân bằng', app.g.__ban, 0);
  });

  await ca('Tệp đã nhận trước: không có nút Nhận, có nút mở nguồn cũ', async function () {
    var app = await moTrungTam({ daCo: true });
    await app.bam(app.mot('#dsvnTai'));
    var inp = app.mot('#dsvnFile');
    inp.files = [{ name: 'GrabFood-20260717.pdf' }];
    inp.onchange(); await nghi(); await nghi(); await nghi();
    bang('không nhận lần hai', app.tim('#dsvnNhan').length, 0);
    await app.bam(app.mot('[data-dsvnct="DSN-1"]'));
    bang('mở nguồn cũ', app.mc.cuoi('vagabond.doi_soat_vendor.chi_tiet').a.name, 'DSN-1');
  });

  await ca('Chi tiết: ba lớp, loại dòng tiếng Việt không lộ mã, chip Chưa nối lọc ở máy chủ, bấm hoá đơn mở đơn', async function () {
    var app = await moTrungTam();
    await app.bam(app.tim('[data-dsvnct="DSN-1"]')[0]);
    var c = app.chu();
    dung('ba lớp', c.indexOf('1. Đủ nguồn') >= 0 && c.indexOf('2. Tiền về ngân hàng') >= 0 && c.indexOf('3. Chứng từ') >= 0);
    dung('khớp tổng tệp', c.indexOf('khớp tổng in trên tệp 668915') >= 0);
    dung('không lộ mã phi_ky', c.indexOf('phi_ky') < 0 && c.indexOf('Phí trong kỳ') >= 0);
    dung('nói không lập phiếu', c.indexOf('không lập phiếu') >= 0);
    await app.bam(app.mot('[data-dsvnloc="chua_noi"]'));
    bang('lọc máy chủ', app.mc.cuoi('vagabond.doi_soat_vendor.chi_tiet').a.loc, 'chua_noi');
    bang('chỉ còn một dòng', app.tim('[data-dsvnsi]').length, 0);
    await app.bam(app.mot('[data-dsvnloc=""]'));
    await app.bam(app.mot('[data-dsvnsi="HDB-1"]'));
    bang('mở đơn', app.g.__xemDon, ['HDB-1']);
  });

  await ca('Chi tiết: Đối chiếu lại gọi máy chủ đúng nguồn rồi vẽ lại', async function () {
    var app = await moTrungTam();
    await app.bam(app.tim('[data-dsvnct="DSN-2"]')[0]);
    var truoc = app.mc.dem('vagabond.doi_soat_vendor.chi_tiet');
    await app.bam(app.mot('#dsvnLai'));
    bang('đúng nguồn', app.mc.cuoi('vagabond.doi_soat_vendor.doi_chieu_lai').a.name, 'DSN-2');
    bang('vẽ lại', app.mc.dem('vagabond.doi_soat_vendor.chi_tiet'), truoc + 1);
  });

  await ca('Chi tiết đơn: kế toán thấy khối đối soát và nút sang nguồn; nhân viên khác không gọi máy chủ', async function () {
    var app = appMoi();
    app.g.frame('Đơn', app.g.dsvnKhoiHd());
    await app.g.dsvnNapKhoiHd('HDB-1'); await nghi();
    dung('khối', app.mot('#dsvnKhoiHd').outerHTML.indexOf('ĐỐI SOÁT TIỀN BÁN') >= 0);
    await app.bam(app.mot('[data-dsvnnguon="DSN-1"]'));
    bang('sang nguồn', app.mc.cuoi('vagabond.doi_soat_vendor.chi_tiet').a.name, 'DSN-1');
    var app2 = appMoi({ keToan: false });
    app2.g.frame('Đơn', app2.g.dsvnKhoiHd());
    await app2.g.dsvnNapKhoiHd('HDB-1'); await nghi();
    bang('không gọi', app2.mc.dem('vagabond.doi_soat_vendor.cua_hoa_don'), 0);
  });

  console.log('Doi soat vendor 579: ' + ket.dat + ' dat, ' + ket.hong + ' hong');
  if (ket.hong) { console.log('  HONG  ' + ket.loi.join('\n  HONG  ')); process.exit(1); }
})().catch(function (e) { console.error(e); process.exit(1); });

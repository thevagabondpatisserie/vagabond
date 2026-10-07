/* Bo ca kiem HANH VI v534 (issue #380): thanh cong cu danh sach dung chung,
 * so hang tang, tab Tien da ve cua man Cong no.
 *
 * Sales Manager bao 28/09/2026: khach da tra tien van nam trong Cong no, va
 * don tang xong khong co cho xem lai bill. Anh Viet chot: chip loc, Excel,
 * chip chang la toi can thiet cho moi man.
 *
 * Bo ca nay CHAY THAT:
 *   - khung app that (01-khung-app.js: go, reset, frame),
 *   - thanh cong cu that (15-khuon-danh-sach.js: dsCongCu, dsCongCuNoi, dsXuatExcel),
 *   - man Hang tang that (41-duyet-don-tang.js),
 *   - man Cong no that (11-khach-ca-hop-dong.js).
 * May chu, hop thoai, o tai tep la ban gia. Ca kiem bam dung chuoi thao tac
 * cua nguoi dung (bam chip, go o tim roi Enter, bam Excel), KHONG goi them
 * ham nao cua man de "cho chac" (quy tac 15).
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/cong_cu_ds_534.js
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
function donTang(i, chang) {
  return { name: 'HDB-26-09-0' + (100 + i), grand_total: 250000, customer_name: 'Khách ' + i, vgb_tang_ly_do: 'Tặng khách VIP',
    vgb_tang_duyet: chang === 'cho_duyet' ? 'Chờ duyệt' : 'Đã duyệt', da_ghi_so: chang === 'hoan_tat' ? 1 : 0, chang: chang,
    nhan_loai: 'Khách VIP, khách quen', diem_ban: 'D1', creation: '2026-09-2' + (i % 9) + ' 10:00', posting_date: '2026-09-20' };
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
      if (m === 'vagabond.hang_tang.ds_don') {
        var tat = [donTang(1, 'hoan_tat'), donTang(2, 'hoan_tat'), donTang(3, 'cho_duyet')];
        var ra = tat.filter(function (d) { return !a.chang || d.chang === a.chang; });
        return { dong: ra, tong_dong: ra.length, con_nua: 0,
          diem: [{ k: 'D1', ten: 'District 1' }, { k: 'NV', ten: 'NVHTN' }],
          loai: [{ k: 'vip', ten: 'Khách VIP' }, { k: 'den_bu', ten: 'Đền bù' }],
          cac_chang: [{ k: 'cho_duyet', ten: 'Chờ duyệt', ic: '⏳' }, { k: 'cho_ghi_so', ten: 'Chờ ghi sổ', ic: '📝' },
            { k: 'hoan_tat', ten: 'Hoàn tất', ic: '✅' }, { k: 'tu_choi', ten: 'Từ chối', ic: '✖️' }],
          dem_chang: { tat_ca: 3, hoan_tat: 2, cho_duyet: 1 }, dem_diem: { tat_ca: 3, D1: 3 }, dem_loai: { tat_ca: 3, vip: 3 },
          tien_cho: 250000, tien_duyet: 0, duyet_duoc: 0, thieu_tai_khoan: 0 };
      }
      if (m === 'vagabond.hang_tang.chi_tiet') return { mon: [{ item_name: 'Bánh', qty: 1, amount: 250000 }], nhan_loai: 'VIP' };
      if (m === 'vagabond.khung.cong_cu_ds.xuat_excel') {
        if (canh.excelLoi) throw new Error('Máy chủ bận, thử lại sau');
        return { ten_file: a.man + '.xlsx', b64: 'UEsDBA==', so_dong: 3 };
      }
      if (m === 'vagabond.cong_no.ds_khach_no') {
        if (a.tim) {
          return { khach: [{ khach: 'KL1', ten: 'Công ty A', so_hd: 1, tien: 1000000, so_ngay: 3, hd: [{ name: 'HDB-1', tien: 1000000, ngay: '2026-09-25' }] }],
            tong: 6000000, tong_loc: 1000000, dang_loc: 1, so_khach_tat_ca: 2, cho_ghi_so: { so_hd: 0, tien: 0, so_khach: 0 } };
        }
        if (canh.veMotPhan) {
          return { khach: [{ khach: 'KL1', ten: 'Công ty A', so_hd: 1, tien: 400000, so_ngay: 3,
            hd: [{ name: 'HDB-1', tien: 400000, ngay: '2026-09-25', tong_don: 1000000, da_thu: 0, da_ve: 600000 }] }],
            tong: 400000, so_khach_tat_ca: 1, cho_ghi_so: { so_hd: 1, tien: 600000, so_khach: 1 } };
        }
        return { khach: [{ khach: 'KL1', ten: 'Công ty A', so_hd: 1, tien: 1000000, so_ngay: 3, hd: [{ name: 'HDB-1', tien: 1000000, ngay: '2026-09-25' }] }],
          tong: 1000000, so_khach_tat_ca: 1, cho_ghi_so: { so_hd: 7, tien: 27622100, so_khach: 7 } };
      }
      if (m === 'vagabond.cong_no.ds_phieu') return { phieu: [] };
      if (m === 'vagabond.cong_no.ds_tien_da_ve') {
        if (canh.veLoi && a.nguon !== 'chuyen_khoan') throw new Error('Máy chủ bận');
        if (canh.demTheoNguon && a.nguon === 'chuyen_khoan') {
          return { dong: [{ pe: 'APP-26-09-950', tien: 300000, ten_khach: 'Khách C', hd_dau: 'HDB-3', so_hd: 1, ngay_ve: '2026-09-25',
            ma_gd: 'FT3', duoi_gd: '0003', so_tep: 0 }], tong_dong: 1, con_nua: 0, tien: 300000,
            dem: { tat_ca: 3, cong_no: 2, chuyen_khoan: 1 }, nguon: a.nguon,
            cac_nguon: [{ k: 'cong_no', ten: 'Khách công nợ' }, { k: 'chuyen_khoan', ten: 'Đơn chuyển khoản' }], chua_xac_minh: 0 };
        }
        return { dong: [
          { pe: 'APP-26-09-894', tien: 5785500, ten_khach: 'Khách Jen', hd_dau: 'HDB-26-09-04242', so_hd: 1, ngay_ve: '2026-09-23',
            ma_gd: 'FT26266374066864', duoi_gd: '6864', so_tep: canh.coTep ? 1 : 0 },
          { pe: 'APP-26-09-900', tien: 1200000, ten_khach: 'Khách B', hd_dau: 'HDB-2', so_hd: 2, ngay_ve: '2026-09-24',
            ma_gd: 'FT1', duoi_gd: '0001', so_tep: 0 }],
          tong_dong: 2, con_nua: 0, tien: 6985500, dem: { tat_ca: 9, cong_no: 7, chuyen_khoan: 2 }, nguon: a.nguon,
          cac_nguon: [{ k: 'cong_no', ten: 'Khách công nợ' }, { k: 'chuyen_khoan', ten: 'Đơn chuyển khoản' }],
          chua_xac_minh: 3, ke_toan: canh.keToan ? 1 : 0 };
      }
      if (m === 'vagabond.thu_tien.ung_vien_tien_ve' && canh.nhieuGd) {
        var het = [];
        for (var i = 1; i <= 15; i++) het.push({ name: 'BT-N' + i, ngay: '2026-09-' + (10 + i), tien: 1000000, con: 1000000,
          mo_ta: 'CK ' + i, ma_gd: 'FTN' + (100 + i), khop: ['đúng số tiền'] });
        return { si: a.si, khach: 'Ms.Thanh', con_no: 1000000, ngay_hd: '2026-09-01', gd: het };
      }
      if (m === 'vagabond.thu_tien.ung_vien_tien_ve') {
        return { si: a.si, khach: 'Ms.Thanh', con_no: 1000000, ngay_hd: '2026-09-25', gd: canh.khongGd ? [] : [
          { name: 'BT-7', ngay: '2026-09-26', tien: 1000000, con: 1000000, mo_ta: 'NGUYEN VAN A CHUYEN TIEN', ma_gd: 'FT7', khop: ['đúng số tiền'] },
          { name: 'BT-9', ngay: '2026-09-27', tien: 1500000, con: 1500000, mo_ta: 'CK DON 93367', ma_gd: 'FT9', khop: ['nội dung có mã đơn 93367'] }] };
      }
      if (m === 'vagabond.thu_tien.nhan_tien_ve') {
        if (canh.nhanLoi) throw new Error('Giao dịch FT7 đã có phiếu thu APP-1. Mở tab Tiền đã về.');
        return { pe: 'APP-MOI', tien: 1000000, ma_gd: a.gd === 'BT-7' ? 'FT7' : 'FT9', ngay_ve: '2026-09-26', ten_khach: 'Ms.Thanh', con_no_sau: 0 };
      }
      if (m === 'vagabond.thu_tien.ghi_so_phieu_thu') {
        if (canh.ghiSoLoi) throw new Error('Giao dịch FT1 vừa được nối với chứng từ khác.');
        return canh.keToan ? { ok: 1, name: a.name } : { ok: 0, da_dinh: 1, so_tep: 1, vi_sao: 'Đã có uỷ nhiệm chi. Chỉ kế toán bấm ghi sổ phiếu thu.' };
      }
      return {};
    },
  };
}

function appMoi(canh) {
  canh = canh || {};
  var tl = domGia.taiLieuGia();
  var vgb = tl.createElement('div'); vgb.id = 'vgb'; tl.body.appendChild(vgb);
  var mc = mayChu(canh);
  var tin = [], tai = [], bill = [], tep = { cnunc: canh.tepChon || [] };
  var g = {
    console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array,
    Promise: Promise, Error: Error, RegExp: RegExp, parseFloat: parseFloat, parseInt: parseInt, isNaN: isNaN, Date: Date,
    document: tl,
    frappe: { session: { user: 'loananh@vagabond.vn' } },
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
    'function busy() {}',
    'function baoTin(s, t) { __tin.push("baoTin:" + s); return Promise.resolve(); }',
    'function dSkin() {}',
    'function money(x) { return String(x); }',
    'function posNgayVn(x) { return String(x || ""); }',
    'function posChipNut(thuoc, nhan, bat) { return "<button class=\\"chip\\" data-bat=\\"" + (bat ? 1 : 0) + "\\" " + thuoc + ">" + nhan + "</button>"; }',
    'function kmHangChip(noiDung) { return "<div>" + noiDung + "</div>"; }',
    'function errMsg(e) { return String((e && e.message) || e); }',
    'function api(m, a) { return __mc.api(m, a); }',
    'function bcTaiVe(ten, b64) { __tai.push(ten); }',
    'function scrPosBill(ma) { __bill.push(ma); frame("Hoá đơn " + ma, "<div>bill</div>"); }',
    'function tdkNap(id, ds) { __tep[id] = ds; }',
    'function tdkKhoi(id) { return "<div id=\\"tdkKhoi_" + id + "\\"></div>"; }',
    'function tdkNoi() {}',
    'function tdkDs(id) { return (__tep[id] || []).slice(); }',
    'function hopKhung(t, than, chan) { var ov = document.createElement("div"); ov.setAttribute("data-hop", t); var box = document.createElement("div"); box.innerHTML = than + (chan || ""); ov.appendChild(box); document.body.appendChild(ov); return { ov: ov, box: box, dong: function () { ov.setAttribute("data-dong", "1"); } }; }',
    'function hoiChu() { return Promise.resolve(null); }',
    'function confirmSheet() { return Promise.resolve(true); }',
    'function locHang() { return ""; }',
    'function locTim(ds) { return ds[0]; }',
    'async function scrHome() { frame(APPNAME, "<div></div>"); }',
    'function scrTangBaoCao() {}',
  ].join('\n'), Object.assign(g, { __tin: tin, __mc: mc, __tai: tai, __bill: bill, __tep: tep }));
  /* sheet() THẬT từ 00-nen.js (Codex #389: hộp chọn giao dịch là bottom sheet có ô tìm). */
  var nen = doc('00-nen.js');
  vm.runInContext(require('./tim_chung.js'), g);
  vm.runInContext(nen.slice(nen.indexOf('function sheet('), nen.indexOf('function confirmSheet(')), g);
  vm.runInContext(doc('01-khung-app.js'), g);
  vm.runInContext(doc('15-khuon-danh-sach.js'), g);
  vm.runInContext(doc('41-duyet-don-tang.js'), g);
  vm.runInContext(doc('11-khach-ca-hop-dong.js'), g);
  return {
    g: g, tl: tl, mc: mc, tin: tin, tai: tai, bill: bill,
    tim: function (chon) { return tl.body.querySelectorAll(chon); },
    mot: function (chon) { var r = tl.body.querySelectorAll(chon); if (r.length !== 1) throw new Error('mong dung 1 ' + chon + ', co ' + r.length); return r[0]; },
    bam: async function (el) { el.dispatchEvent(domGia.suKien('click', {}, el)); await nghi(); await nghi(); },
    goTim: async function (id, chu) {
      var o = tl.getElementById(id); if (!o) throw new Error('khong thay o #' + id);
      o.value = chu;
      o.dispatchEvent(domGia.suKien('keydown', { key: 'Enter' }, o));
      await nghi(); await nghi();
    },
    doiNgay: async function (id, v) {
      var o = tl.getElementById(id); if (!o) throw new Error('khong thay o #' + id);
      o.value = v; o.dispatchEvent(domGia.suKien('change', {}, o)); await nghi(); await nghi();
    },
  };
}

function chip(app, ma) { return app.mot('[data-dscc="' + ma + '"]'); }

async function moTang(canh) {
  var app = appMoi(canh);
  await app.g.reset(app.g.scrDuyetTang); await nghi(); await nghi();
  return app;
}
async function moCongNo(canh) {
  var app = appMoi(canh);
  await app.g.reset(app.g.scrCongNo); await nghi(); await nghi();
  return app;
}

(async function () {
  await ca('Hàng tặng: màn mở với bốn khối thanh công cụ, đúng thứ tự', async function () {
    var app = await moTang();
    var cc = app.mot('[data-dscongcu]');
    var chips = cc.querySelectorAll('[data-dscc]').map(function (b) { return b.getAttribute('data-dscc').split('|')[0]; });
    var thuTu = [];
    chips.forEach(function (x) { if (thuTu.indexOf(x) < 0) thuTu.push(x); });
    bang('thứ tự họ chip', thuTu, ['chang', 'diem', 'loai', 'ky']);
    dung('có ô tìm', !!app.tl.getElementById('dtgDsTim'));
    dung('có nút Excel', cc.querySelectorAll('[data-dsxuat]').length === 1);
    /* Chip không có dòng thì ẩn: "Chờ ghi sổ" và "Từ chối" đếm 0. */
    bang('chip chặng hiện theo số đếm', cc.querySelectorAll('[data-dscc]').filter(function (b) { return b.getAttribute('data-dscc').indexOf('chang|') === 0; })
      .map(function (b) { return b.getAttribute('data-dscc'); }), ['chang|', 'chang|cho_duyet', 'chang|hoan_tat']);
  });

  await ca('Hàng tặng: bấm chip Hoàn tất thì máy chủ nhận chang=hoan_tat, chip đó sáng', async function () {
    var app = await moTang();
    await app.bam(chip(app, 'chang|hoan_tat'));
    bang('tham số chặng', app.mc.cuoi('vagabond.hang_tang.ds_don').a.chang, 'hoan_tat');
    bang('chip sáng', chip(app, 'chang|hoan_tat').getAttribute('data-bat'), '1');
    bang('còn đúng hai đơn', app.tim('[data-dtgm]').length, 2);
  });

  await ca('Hàng tặng: chip ngày Tháng trước và Tuỳ chọn gửi đúng khoảng lên máy chủ', async function () {
    var app = await moTang();
    await app.bam(chip(app, 'ky|thang_truoc'));
    bang('ky', app.mc.cuoi('vagabond.hang_tang.ds_don').a.ky, 'thang_truoc');
    dung('chưa có ô ngày', !app.tl.getElementById('dtgDsTu'));
    await app.bam(chip(app, 'ky|tuy_chon'));
    dung('hiện ô từ ngày', !!app.tl.getElementById('dtgDsTu'));
    await app.doiNgay('dtgDsTu', '2026-09-01');
    await app.doiNgay('dtgDsDen', '2026-09-15');
    var a = app.mc.cuoi('vagabond.hang_tang.ds_don').a;
    bang('khoảng tuỳ chọn', [a.ky, a.tu, a.den], ['tuy_chon', '2026-09-01', '2026-09-15']);
    await app.bam(chip(app, 'ky|'));
    a = app.mc.cuoi('vagabond.hang_tang.ds_don').a;
    bang('bỏ lọc ngày xoá luôn hai ô', [a.ky, a.tu, a.den], ['', '', '']);
  });

  await ca('Hàng tặng: gõ tìm rồi Enter chỉ hỏi máy chủ MỘT lần', async function () {
    var app = await moTang();
    var truoc = app.mc.dem('vagabond.hang_tang.ds_don');
    await app.goTim('dtgDsTim', 'Khách 1');
    var o = app.tl.getElementById('dtgDsTim');
    o.dispatchEvent(domGia.suKien('change', {}, o)); await nghi();
    bang('một lượt hỏi', app.mc.dem('vagabond.hang_tang.ds_don') - truoc, 1);
    bang('tham số tìm', app.mc.cuoi('vagabond.hang_tang.ds_don').a.tim, 'Khách 1');
  });

  await ca('Hàng tặng: Xuất Excel gửi ĐÚNG bộ lọc đang áp, tải tệp về', async function () {
    var app = await moTang();
    await app.bam(chip(app, 'chang|hoan_tat'));
    await app.bam(chip(app, 'ky|thang_nay'));
    await app.bam(app.mot('[data-dsxuat]'));
    var x = app.mc.cuoi('vagabond.khung.cong_cu_ds.xuat_excel');
    dung('có gọi cửa Excel', !!x);
    bang('màn', x.a.man, 'hang_tang');
    var loc = JSON.parse(x.a.loc);
    bang('bộ lọc khớp màn', [loc.chang, loc.ky, loc.diem, loc.loai], ['hoan_tat', 'thang_nay', '', '']);
    bang('bộ lọc Excel bằng bộ lọc màn vừa gửi', loc, app.mc.cuoi('vagabond.hang_tang.ds_don').a);
    bang('tải tệp', app.tai, ['hang_tang.xlsx']);
  });

  await ca('Hàng tặng: Excel hỏng thì báo câu tiếng người, không tải tệp rỗng', async function () {
    var app = await moTang({ excelLoi: 1 });
    await app.bam(app.mot('[data-dsxuat]'));
    bang('không tải', app.tai, []);
    dung('có câu báo', app.tin.some(function (t) { return t.indexOf('baoTin:Máy chủ bận') === 0; }));
  });

  await ca('Hàng tặng: mở một đơn rồi bấm Xem lại bill thì mở đúng tờ bill', async function () {
    var app = await moTang();
    await app.bam(app.tim('[data-dtgm]')[0]);
    var nut = app.mot('[data-dtgbill]');
    var ma = nut.getAttribute('data-dtgbill');
    await app.bam(nut);
    bang('mở bill', app.bill, [ma]);
  });

  await ca('Công nợ: thẻ số có Tiền đã về, tab Tiền đã về gửi nguồn mặc định Khách công nợ', async function () {
    var app = await moCongNo();
    var chu = app.tl.body.querySelectorAll('div').map(function (d) { return d._chu; }).join('|');
    dung('có nhãn tiền đã về', chu.indexOf('TIỀN ĐÃ VỀ, CHỜ GHI SỔ') >= 0);
    dung('có dòng nhắc sổ cái', chu.indexOf('Sổ cái vẫn tính nợ') >= 0);
    /* Trước vòng 6 tab Đang nợ không hỏi danh sách tiền về, nên chip phải
       mượn số hoá đơn phủ đủ và lệch với tab (Codex #382 vòng 6). Giờ hỏi
       đúng một lần, cùng bộ lọc tab sẽ dùng, để chip đếm đúng tập đó. */
    bang('tab Đang nợ hỏi danh sách tiền về đúng một lần', app.mc.dem('vagabond.cong_no.ds_tien_da_ve'), 1);
    bang('cùng bộ lọc mặc định của tab', app.mc.cuoi('vagabond.cong_no.ds_tien_da_ve').a.nguon, 'cong_no');
    await app.bam(app.mot('[data-cntab="ve"]'));
    bang('nguồn mặc định', app.mc.cuoi('vagabond.cong_no.ds_tien_da_ve').a.nguon, 'cong_no');
    bang('hai dòng', app.tim('[data-cnunc]').length, 2);
    bang('Sales không thấy nút ghi sổ', app.tim('[data-cngs]').length, 0);
  });

  await ca('Công nợ: Sales đính UNC khách gửi thì gửi đúng phiếu và tệp, máy báo chờ kế toán', async function () {
    var app = await moCongNo();
    await app.bam(app.mot('[data-cntab="ve"]'));
    await app.bam(app.tim('[data-cnunc="APP-26-09-894"]')[0]);
    var hop = app.mot('[data-hop]');
    dung('hộp đúng phiếu', hop.querySelectorAll('[data-cnluu]').length === 1);
    /* Người dùng chọn tệp SAU khi hộp mở (ô tải tệp dùng chung ghi vào kho
       của nó); hộp mở thì kho được làm sạch trước. */
    bang('hộp mở với kho tệp sạch', app.g.tdkDs('cnunc'), []);
    app.g.__tep.cnunc = ['/private/files/unc-jen.jpg'];
    await app.bam(hop.querySelectorAll('[data-cnluu]')[0]);
    var x = app.mc.cuoi('vagabond.thu_tien.ghi_so_phieu_thu');
    bang('gửi đúng phiếu', x.a.name, 'APP-26-09-894');
    bang('gửi đúng tệp', JSON.parse(x.a.unc), ['/private/files/unc-jen.jpg']);
    dung('báo chờ kế toán', app.tin.some(function (t) { return t.indexOf('Chỉ kế toán bấm ghi sổ') >= 0; }));
  });

  await ca('Công nợ: bấm lưu mà chưa chọn tệp thì không gọi máy chủ', async function () {
    var app = await moCongNo({ tepChon: [] });
    await app.bam(app.mot('[data-cntab="ve"]'));
    await app.bam(app.tim('[data-cnunc="APP-26-09-894"]')[0]);
    await app.bam(app.mot('[data-cnluu]'));
    bang('không gọi ghi sổ', app.mc.dem('vagabond.thu_tien.ghi_so_phieu_thu'), 0);
    dung('nhắc chọn tệp', app.tin.some(function (t) { return t.indexOf('Chọn ảnh chuyển khoản') >= 0; }));
  });

  await ca('Công nợ: kế toán thấy nút Ghi sổ ở dòng đã có UNC, bấm là ghi sổ đúng phiếu', async function () {
    var app = await moCongNo({ keToan: 1, coTep: 1 });
    await app.bam(app.mot('[data-cntab="ve"]'));
    var nut = app.tim('[data-cngs]');
    bang('chỉ dòng có UNC mới có nút', nut.map(function (b) { return b.getAttribute('data-cngs'); }), ['APP-26-09-894']);
    await app.bam(nut[0]);
    var x = app.mc.cuoi('vagabond.thu_tien.ghi_so_phieu_thu');
    bang('ghi sổ không gửi lại tệp', [x.a.name, x.a.unc], ['APP-26-09-894', undefined]);
    dung('báo đã ghi sổ', app.tin.some(function (t) { return t.indexOf('toast:Đã ghi sổ phiếu thu APP-26-09-894') === 0; }));
  });

  await ca('Công nợ: ghi sổ hỏng thì báo nguyên câu máy chủ, màn không trắng', async function () {
    var app = await moCongNo({ keToan: 1, coTep: 1, ghiSoLoi: 1 });
    await app.bam(app.mot('[data-cntab="ve"]'));
    await app.bam(app.tim('[data-cngs]')[0]);
    dung('câu lỗi máy chủ', app.tin.some(function (t) { return t.indexOf('vừa được nối với chứng từ khác') >= 0; }));
    dung('danh sách còn nguyên', app.tim('[data-cnunc]').length === 2);
  });

  await ca('Công nợ: Excel tab Tiền đã về gửi màn tien_da_ve và nguồn đang chọn', async function () {
    var app = await moCongNo();
    await app.bam(app.mot('[data-cntab="ve"]'));
    await app.bam(chip(app, 'nguon|chuyen_khoan'));
    bang('máy chủ nhận nguồn mới', app.mc.cuoi('vagabond.cong_no.ds_tien_da_ve').a.nguon, 'chuyen_khoan');
    await app.bam(app.mot('[data-dsxuat]'));
    var x = app.mc.cuoi('vagabond.khung.cong_cu_ds.xuat_excel');
    bang('màn', x.a.man, 'tien_da_ve');
    bang('nguồn', JSON.parse(x.a.loc).nguon, 'chuyen_khoan');
  });

  await ca('Công nợ: tab Đang nợ tìm ở máy chủ, Excel mang theo chữ tìm', async function () {
    var app = await moCongNo();
    await app.goTim('cnnoDsTim', 'Công ty A');
    bang('tìm gửi lên máy chủ', app.mc.cuoi('vagabond.cong_no.ds_khach_no').a.tim, 'Công ty A');
    await app.bam(app.mot('[data-dsxuat]'));
    var x = app.mc.cuoi('vagabond.khung.cong_cu_ds.xuat_excel');
    bang('màn', x.a.man, 'cong_no');
    bang('chữ tìm', JSON.parse(x.a.loc).tim, 'Công ty A');
  });

  /* Codex #382 vòng 6: chip "Tiền đã về" từng lấy số hoá đơn đã phủ đủ nợ
     (cho_ghi_so.so_hd = 7 trong máy chủ giả) trong khi tab liệt kê từng
     phiếu thu (2 dòng). Chip phải đếm ĐÚNG tập phiếu mà tab đang hiện. */
  await ca('Công nợ: chip Tiền đã về đếm đúng số phiếu tab đang hiện, ở cả hai tab và khi đổi nguồn', async function () {
    var app = await moCongNo({ demTheoNguon: 1 });
    var chipVe = function () { return app.mot('[data-cntab="ve"]').textContent; };
    bang('tab Đang nợ: chip bằng số phiếu tab Tiền đã về sẽ hiện', chipVe(), '💰 Tiền đã về 2');
    await app.bam(app.mot('[data-cntab="ve"]'));
    bang('tab Tiền đã về: số dòng', app.tim('[data-cnunc]').length, 2);
    bang('chip khớp số dòng', chipVe(), '💰 Tiền đã về 2');
    await app.bam(chip(app, 'nguon|chuyen_khoan'));
    bang('đổi nguồn: số dòng', app.tim('[data-cnunc]').length, 1);
    bang('đổi nguồn: chip khớp', chipVe(), '💰 Tiền đã về 1');
    await app.bam(app.mot('[data-cntab="no"]'));
    bang('về tab Đang nợ vẫn đếm theo nguồn đang chọn', chipVe(), '💰 Tiền đã về 1');
  });

  await ca('Công nợ: tải Tiền đã về hỏng thì tab Đang nợ vẫn mở, chip không bịa số', async function () {
    var app = await moCongNo({ veLoi: 1 });
    bang('tab Đang nợ vẫn có khách', app.tim('[data-cntab="no"]').length, 1);
    bang('chip không kèm số', app.mot('[data-cntab="ve"]').textContent, '💰 Tiền đã về');
  });

  await ca('Công nợ: hoá đơn có tiền về một phần hiện số còn đòi và dòng đã về chờ ghi sổ (Codex #382 vòng 8)', async function () {
    var app = await moCongNo({ veMotPhan: 1 });
    await app.bam(app.mot('[data-cnmo="KL1"]'));
    var dv = app.mot('[data-cndave]');
    bang('dòng tiền đã về', dv.textContent, '600000 đ đã về tài khoản, chờ ghi sổ');
    var chu = app.tl.body.querySelectorAll('b').map(function (x) { return x.textContent; });
    dung('số bên phải là số còn đòi 400000', chu.indexOf('400000 đ') >= 0);
    dung('không còn hiện đòi 1000000', chu.indexOf('1000000 đ') < 0);
  });

  await ca('Công nợ: hoá đơn không có tiền về thì không hiện dòng chờ ghi sổ', async function () {
    var app = await moCongNo();
    await app.bam(app.mot('[data-cnmo="KL1"]'));
    bang('không có dòng', app.tim('[data-cndave]').length, 0);
  });

  await ca('Công nợ: đang tìm thì hiện tổng của phần khớp, thẻ trên đầu giữ tổng thật (Codex #382 vòng 9)', async function () {
    var app = await moCongNo();
    bang('chưa tìm thì không có dòng tổng lọc', app.tim('[data-cntongloc]').length, 0);
    await app.goTim('cnnoDsTim', 'Công ty A');
    bang('dòng tổng phần khớp, số của máy chủ', app.mot('[data-cntongloc]').textContent, 'Khớp ô tìm: 1 khách · 1000000 đ');
    var chu = app.tl.body.querySelectorAll('div').map(function (d) { return d._chu; }).join('|');
    dung('thẻ Còn phải đòi vẫn là tổng thật 6000000', chu.indexOf('6000000 đ') >= 0);
  });

  /* v541 (anh Việt 29/09/2026): tiền đã về mà hoá đơn nằm ở Đang nợ vì nội
     dung chuyển khoản không mang mã đơn. Ca đi ĐÚNG chuỗi của người dùng:
     mở khách, bấm nút trên dòng hoá đơn, chọn giao dịch trong bottom sheet có
     ô tìm (Codex #389 vòng 2), xác nhận, đính UNC. sheet() là bản THẬT. */
  function shiCua(app, ten) {
    var lst = app.tl.body.querySelectorAll('.shl'); lst = lst[lst.length - 1];
    /* Tìm dòng theo chữ trong HTML của sheet: mỗi mảnh sau 'class="shi' là một dòng, cùng thứ tự querySelectorAll. */
    var manh = lst.innerHTML.split('class="shi').slice(1), rows = lst.querySelectorAll('.shi'), r = [];
    manh.forEach(function (m, i) { if (m.indexOf(ten) >= 0) r.push(rows[i]); });
    return { lst: lst, row: r[0], dem: r.length };
  }
  await ca('Công nợ v541: dòng hoá đơn Đang nợ có nút Khách đã chuyển tiền cao 44px; bấm không làm đổi dấu tick', async function () {
    var app = await moCongNo();
    await app.bam(app.mot('[data-cnmo="KL1"]'));
    var nut = app.mot('[data-cnnhan="HDB-1"]');
    var cao = /min-height:\s*(\d+)px/.exec(nut.getAttribute('style') || '');
    dung('nút cao ít nhất 44px (AGENTS.md điều 13)', cao && +cao[1] >= 44);
    await app.bam(nut);
    bang('hỏi đúng hoá đơn', app.mc.cuoi('vagabond.thu_tien.ung_vien_tien_ve').a, { si: 'HDB-1' });
    var lst = app.mot('.shl');
    bang('hai giao dịch để người chọn', lst.querySelectorAll('.shi').length, 2);
    dung('bottom sheet có ô tìm', app.mot('.shb').querySelectorAll('input').length === 1);
    dung('hiện lý do khớp mã đơn', lst.innerHTML.indexOf('nội dung có mã đơn 93367') >= 0);
    bang('chưa lập phiếu khi chưa chọn', app.mc.dem('vagabond.thu_tien.nhan_tien_ve'), 0);
    var o = app.mot('[data-cnhd="KL1|HDB-1"]');
    dung('ô tick không bị bật', o.innerHTML.indexOf('✓') < 0);
  });

  await ca('Công nợ v541: chọn giao dịch thì lập phiếu thu đúng hoá đơn và giao dịch, mở hộp UNC cho phiếu mới', async function () {
    var app = await moCongNo();
    await app.bam(app.mot('[data-cnmo="KL1"]'));
    await app.bam(app.mot('[data-cnnhan="HDB-1"]'));
    var c = shiCua(app, 'CK DON 93367');
    bang('đúng một dòng của giao dịch BT-9', c.dem, 1);
    c.lst.onclick({ target: c.row }); await nghi(); await nghi(); await nghi();
    bang('gửi đúng hoá đơn và giao dịch', app.mc.cuoi('vagabond.thu_tien.nhan_tien_ve').a, { si: 'HDB-1', gd: 'BT-9' });
    dung('báo đã lập phiếu', app.tin.some(function (t) { return t.indexOf('toast:Đã lập phiếu thu APP-MOI') === 0; }));
    var unc = app.tim('[data-hop="Uỷ nhiệm chi khách gửi"]');
    dung('mở hộp đính UNC', unc.length >= 1);
    app.g.__tep.cnunc = ['/private/files/unc-thanh.jpg'];
    await app.bam(unc[unc.length - 1].querySelectorAll('[data-cnluu]')[0]);
    var x = app.mc.cuoi('vagabond.thu_tien.ghi_so_phieu_thu');
    bang('đính UNC vào đúng phiếu mới', [x.a.name, JSON.parse(x.a.unc)], ['APP-MOI', ['/private/files/unc-thanh.jpg']]);
  });

  await ca('Công nợ v541: không có giao dịch nào thì nói rõ, lập phiếu hỏng thì báo nguyên câu máy chủ', async function () {
    var app = await moCongNo({ khongGd: 1 });
    await app.bam(app.mot('[data-cnmo="KL1"]'));
    await app.bam(app.mot('[data-cnnhan="HDB-1"]'));
    dung('câu chưa thấy giao dịch', app.tin.some(function (t) { return t.indexOf('baoTin:Chưa thấy giao dịch tiền vào') === 0; }));
    bang('không mở sheet rỗng', app.tim('.shl').length, 0);
    var app2 = await moCongNo({ nhanLoi: 1 });
    await app2.bam(app2.mot('[data-cnmo="KL1"]'));
    await app2.bam(app2.mot('[data-cnnhan="HDB-1"]'));
    var c = shiCua(app2, 'NGUYEN VAN A');
    c.lst.onclick({ target: c.row }); await nghi(); await nghi(); await nghi();
    dung('câu lỗi máy chủ', app2.tin.some(function (t) { return t.indexOf('đã có phiếu thu APP-1') >= 0; }));
    bang('không mở hộp UNC', app2.tim('[data-hop="Uỷ nhiệm chi khách gửi"]').length, 0);
  });

  /* Codex #389 P2 (hai vòng): mọi khoản thoả luật đều có mặt, không cắt; nhiều
     khoản thì gõ tìm theo mã giao dịch, số tiền, nội dung, ngày rồi chọn. */
  await ca('Công nợ v541: nhiều giao dịch thì hiện đủ, gõ tìm mã giao dịch còn đúng một dòng và chọn được', async function () {
    var app = await moCongNo({ nhieuGd: 1 });
    await app.bam(app.mot('[data-cnmo="KL1"]'));
    await app.bam(app.mot('[data-cnnhan="HDB-1"]'));
    var lst = app.mot('.shl');
    bang('đủ 15 giao dịch, không cắt', lst.querySelectorAll('.shi').length, 15);
    var o = app.mot('.shb').querySelectorAll('input')[0];
    o.value = 'FTN103'; o.oninput();
    var r = lst.querySelectorAll('.shi');
    bang('tìm mã giao dịch còn một dòng', r.length, 1);
    lst.onclick({ target: r[0] }); await nghi(); await nghi(); await nghi();
    bang('chọn đúng giao dịch tìm được', app.mc.cuoi('vagabond.thu_tien.nhan_tien_ve').a, { si: 'HDB-1', gd: 'BT-N3' });
  });

  console.log('  cong_cu_ds_534: ' + ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng');
  if (ket.hong) { ket.loi.forEach(function (l) { console.log('  HỎNG  ' + l); }); process.exit(1); }
})();

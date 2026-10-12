/* Bo ca kiem HANH VI v550: tru kho tung mon va tru bu (anh Viet chot 01/10/2026).
 *
 * Chay THAT:
 *   - khung app (01-khung-app.js: go, reset, frame),
 *   - thanh cong cu chung (15-khuon-danh-sach.js),
 *   - man Hoa don chua tru kho, chip va khoi Kho (49-tru-kho-bu.js),
 *   - chip bill quay that (posChipBill trong 10-bill-quay.js),
 *   - chip don Sales that (dsChips trong 08-doanh-so-sales.js).
 * May chu, hop thoai la ban gia. Ca kiem bam dung chuoi thao tac cua nguoi
 * dung (bam chip, bam Tru bu, bam Excel), khong goi them ham nao cua man
 * "cho chac" (quy tac 15).
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/tru_kho_bu_550.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var domGia = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
function layHam(src, ten) {
  var dau = src.indexOf('function ' + ten + '(');
  if (dau < 0) throw new Error('Khong thay ham ' + ten);
  if (src.slice(Math.max(0, dau - 6), dau) === 'async ') dau -= 6;
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Ham ' + ten + ' khong dong ngoac');
}

var ket = { dat: 0, hong: 0, loi: [] };
function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; }
  catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 4).join('\n         ') : String(e))); }
}
async function nghi() { for (var i = 0; i < 12; i++) await Promise.resolve(); await new Promise(function (r) { setImmediate(r); }); }

/* ---------------- may chu gia ---------------- */
function hd(ten, tt, khoNay, bu, dong) {
  return { name: ten, posting_date: '2026-10-01', posting_time: '10:10:00', diem: 'TCV', ten_diem: 'District 1',
    tt_kho: tt, kho_nay: khoNay, vgb_tru_bu: bu || '', vgb_chua_tru_kho: (tt === 'chua_tru' || tt === 'mot_phan') ? 1 : 0,
    vgb_ly_do_chua_tru_kho: tt === 'da_tru_bu' ? 'Đã trừ bù đủ lúc 2026-10-01 14:20.' : 'Còn chờ hàng về: BANU00062 tại Kho D1 - TV cần 1, còn 0',
    phieu: tt === 'chua_tru' ? [] : ['PXD-2026-00010'], docstatus: 1, dong: dong || [
      { ma: 'BANU00062', ten: 'Bánh su kem', dvt: 'Cái', can: 1, da_tru: 0, ton: khoNay === 'kho_het' ? 0 : 3, nhan: khoNay === 'kho_het' ? 'het' : 'du' }] };
}
var CHANG = [{ k: 'cho', ten: 'Chưa trừ kho', ic: '📦' }, { k: 'kho_du', ten: 'Kho đủ để trừ bù', ic: '✅' },
  { k: 'kho_mot_phan', ten: 'Kho đủ một phần', ic: '🟠' }, { k: 'kho_het', ten: 'Kho chưa có hàng', ic: '⛔' },
  { k: 'mot_phan', ten: 'Đã trừ một phần', ic: '📦' }, { k: 'go_tay', ten: 'Phiếu bù bị gỡ tay', ic: '✋' },
  { k: 'da_tru_bu', ten: 'Đã trừ bù', ic: '🔁' }];

function mayChu(canh) {
  canh = canh || {};
  var goi = [];
  var tat = [hd('HDB-26-10-00033', 'chua_tru', 'kho_du'), hd('HDB-26-10-00021', 'mot_phan', 'kho_het', '', [
      { ma: 'BACF00001', ten: 'Biscotti', dvt: 'Cái', can: 2, da_tru: 2, ton: 10, nhan: 'da_tru' },
      { ma: 'BANU00032', ten: 'Tart chanh', dvt: 'Cái', can: 1, da_tru: 0, ton: 0, nhan: 'het' }]),
    hd('HDB-26-10-00040', 'da_tru_bu', '', 'Đủ')];
  return {
    goi: goi,
    cuoi: function (m) { var r = goi.filter(function (x) { return x.m === m; }); return r[r.length - 1]; },
    dem: function (m) { return goi.filter(function (x) { return x.m === m; }).length; },
    api: async function (m, a) {
      goi.push({ m: m, a: JSON.parse(JSON.stringify(a || {})) });
      if (m === 'vagabond.tru_kho_bu.ds_chua_tru_kho') {
        var thuoc = function (o, k) {
          var cho = o.tt_kho === 'chua_tru' || o.tt_kho === 'mot_phan';
          if (!k) return true;
          if (k === 'cho') return cho;
          if (k.indexOf('kho_') === 0) return cho && o.kho_nay === k;
          return o.tt_kho === k;
        };
        var dem = { '': tat.length };
        CHANG.forEach(function (c) { dem[c.k] = tat.filter(function (o) { return thuoc(o, c.k); }).length; });
        return { hd: tat.filter(function (o) { return thuoc(o, a.chang); }), dem: dem, chang: CHANG, bi_cat: 0,
          duoc_tru: canh.thuNgan ? 0 : 1, diem: [{ ma: 'SALES', ten: 'Sales Online' }, { ma: 'TCV', ten: 'District 1' }] };
      }
      if (m === 'vagabond.tru_kho_bu.tru_bu_hd') {
        if (canh.truLoi) throw new Error('Đang kiểm kê kho D1');
        return { ok: 1, phieu: ['PXD-2026-00011'], da_tru: { 'BANU00062|Kho D1 - TV': 1 }, con_thieu: {} };
      }
      if (m === 'vagabond.tru_kho_bu.tru_bu_diem') return { xong: 1, mot_phan: 0, khong_doi: 1, loi: 0 };
      if (m === 'vagabond.tru_kho_bu.tt_hoa_don') {
        var o = JSON.parse(JSON.stringify(tat[0])); o.name = a.hoa_don; o.duoc_tru = canh.thuNgan ? 0 : 1; return o;
      }
      if (m === 'vagabond.khung.cong_cu_ds.xuat_excel') return { ten_file: a.man + '.xlsx', b64: 'UEsDBA==', so_dong: 3 };
      return {};
    },
  };
}

function appMoi(canh) {
  canh = canh || {};
  var tl = domGia.taiLieuGia();
  var vgb = tl.createElement('div'); vgb.id = 'vgb'; tl.body.appendChild(vgb);
  var mc = mayChu(canh);
  var tin = [], tai = [], hoi = [];
  var g = {
    console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array,
    Promise: Promise, Error: Error, RegExp: RegExp, parseFloat: parseFloat, parseInt: parseInt, isNaN: isNaN, Date: Date,
    document: tl,
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
    'function busy() {}',
    'function baoTin(s) { __tin.push("baoTin:" + s); return Promise.resolve(); }',
    'function dSkin() {}',
    'function money(x) { return String(x); }',
    'function posChipNut(thuoc, nhan, bat) { return "<button class=\\"chip\\" data-bat=\\"" + (bat ? 1 : 0) + "\\" " + thuoc + ">" + nhan + "</button>"; }',
    'function kmHangChip(noiDung) { return "<div>" + noiDung + "</div>"; }',
    'function errMsg(e) { return String((e && e.message) || e); }',
    'function api(m, a) { return __mc.api(m, a); }',
    'function bcTaiVe(ten) { __tai.push(ten); }',
    'function confirmSheet(t, m) { __hoi.push(t); return Promise.resolve(__dongY); }',
    'function locHang(ds, chon, attr, rows) { return ds.map(function (c) { return "<button " + attr + "=\\"" + c.k + "\\">" + c.nhan + " " + rows.filter(c.loc).length + "</button>"; }).join(""); }',
    'function locTim(ds, k) { for (var i = 0; i < ds.length; i++) if (ds[i].k === k) return ds[i]; return ds[0]; }',
    'async function scrHome() { frame(APPNAME, "<div></div>"); }',
    'var DS_MAU_HD = {};',
    'function hddtChoXuatChu(x) { return "Chờ xuất " + x; }',
  ].join('\n'), Object.assign(g, { __tin: tin, __mc: mc, __tai: tai, __hoi: hoi, __dongY: canh.huy ? false : true }));
  vm.runInContext(doc('01-khung-app.js'), g);
  vm.runInContext(doc('15-khuon-danh-sach.js'), g);
  vm.runInContext(doc('49-tru-kho-bu.js'), g);
  vm.runInContext(layHam(doc('10-bill-quay.js'), 'posChipBill'), g);
  var s08 = doc('08-doanh-so-sales.js');
  vm.runInContext(layHam(s08, 'dsChip') + '\n' + layHam(s08, 'dsChips'), g);
  return {
    g: g, tl: tl, mc: mc, tin: tin, tai: tai, hoi: hoi,
    tim: function (chon) { return tl.body.querySelectorAll(chon); },
    mot: function (chon) { var r = tl.body.querySelectorAll(chon); if (r.length !== 1) throw new Error('mong dung 1 ' + chon + ', co ' + r.length); return r[0]; },
    bam: async function (el) { el.dispatchEvent(domGia.suKien('click', {}, el)); await nghi(); await nghi(); },
  };
}
function chip(app, ma) { return app.mot('[data-dscc="' + ma + '"]'); }
async function moMan(canh) {
  var app = appMoi(canh);
  await app.g.reset(app.g.scrTruKho); await nghi(); await nghi();
  return app;
}
function chu(el) { return String(el.innerHTML || ''); }

(async function () {
  await ca('Màn mở mặc định ở chip Chưa trừ kho, có chip điểm, chip ngày, ô tìm, Excel', async function () {
    var app = await moMan();
    bang('máy chủ nhận chặng mặc định', app.mc.cuoi('vagabond.tru_kho_bu.ds_chua_tru_kho').a.chang, 'cho');
    bang('chip Chưa trừ kho đang sáng', chip(app, 'chang|cho').getAttribute('data-bat'), '1');
    dung('có chip điểm District 1', !!chip(app, 'diem|TCV'));
    dung('có chip ngày Tuỳ chọn', !!chip(app, 'ky|tuy_chon'));
    dung('có ô tìm', !!app.tl.getElementById('tkDsTim'));
    bang('có một nút Excel', app.tim('[data-dsxuat]').length, 1);
    bang('một nút Trừ bù ở chip mặc định', app.tim('[data-tkbu]').length, 1);
  });

  await ca('Hai họ chip không lẫn: thẻ chờ có chip Chưa trừ kho VÀ chip Kho đủ để trừ bù', async function () {
    var app = await moMan();
    var html = chu(app.tl.getElementById('vgb'));
    dung('có chip Chưa trừ kho', html.indexOf('📦 Chưa trừ kho') >= 0);
    dung('có chip Kho đủ để trừ bù', html.indexOf('✅ Kho đủ để trừ bù') >= 0);
    dung('tờ đã trừ một phần có chip riêng', html.indexOf('📦 Đã trừ một phần') >= 0);
    dung('tờ đã trừ một phần mà kho hết có chip Kho chưa có hàng', html.indexOf('⛔ Kho chưa có hàng') >= 0);
    dung('món đã trừ ghi Đã trừ', html.indexOf('Đã trừ</td>') >= 0);
    dung('món chưa có ghi Kho chưa có', html.indexOf('Kho chưa có</td>') >= 0);
    dung('chưa thấy tờ đã trừ bù ở chip Chưa trừ kho', html.indexOf('HDB-26-10-00040') < 0);
  });

  await ca('Nút Trừ bù chỉ hiện ở tờ kho đủ, không hiện ở tờ kho chưa có hàng', async function () {
    var app = await moMan();
    bang('một nút, đúng tờ kho đủ', app.tim('[data-tkbu]').map(function (b) { return b.getAttribute('data-tkbu'); }), ['HDB-26-10-00033']);
  });

  await ca('Thu ngân (không có quyền trừ bù) xem được danh sách nhưng không có nút', async function () {
    var app = await moMan({ thuNgan: 1 });
    bang('không có nút Trừ bù', app.tim('[data-tkbu]').length, 0);
    dung('vẫn thấy hoá đơn', chu(app.tl.getElementById('vgb')).indexOf('HDB-26-10-00033') >= 0);
  });

  await ca('Bấm chip Đã trừ bù: máy chủ nhận chang=da_tru_bu, chỉ còn tờ đã trừ bù', async function () {
    var app = await moMan();
    await app.bam(chip(app, 'chang|da_tru_bu'));
    bang('tham số', app.mc.cuoi('vagabond.tru_kho_bu.ds_chua_tru_kho').a.chang, 'da_tru_bu');
    var html = chu(app.tl.getElementById('vgb'));
    dung('có tờ đã trừ bù', html.indexOf('HDB-26-10-00040') >= 0 && html.indexOf('🔁 Đã trừ bù') >= 0);
    dung('không còn tờ chờ', html.indexOf('HDB-26-10-00033') < 0);
  });

  await ca('Bấm Trừ bù: hỏi xác nhận, gọi đúng hoá đơn, báo phiếu vừa lập, tải lại màn', async function () {
    var app = await moMan();
    var lanDau = app.mc.dem('vagabond.tru_kho_bu.ds_chua_tru_kho');
    await app.bam(app.mot('[data-tkbu="HDB-26-10-00033"]'));
    bang('có hỏi', app.hoi, ['Trừ bù kho']);
    bang('gọi trừ bù đúng hoá đơn', app.mc.cuoi('vagabond.tru_kho_bu.tru_bu_hd').a, { hoa_don: 'HDB-26-10-00033' });
    dung('báo phiếu', app.tin.some(function (t) { return t.indexOf('PXD-2026-00011') >= 0; }));
    bang('tải lại danh sách', app.mc.dem('vagabond.tru_kho_bu.ds_chua_tru_kho'), lanDau + 1);
  });

  await ca('Bấm Trừ bù rồi bấm Huỷ ở hộp xác nhận: không gọi máy chủ', async function () {
    var app = await moMan({ huy: 1 });
    await app.bam(app.mot('[data-tkbu="HDB-26-10-00033"]'));
    bang('không gọi trừ bù', app.mc.dem('vagabond.tru_kho_bu.tru_bu_hd'), 0);
  });

  await ca('Trừ bù lỗi (đang kiểm kê): báo câu của máy chủ, không vỡ màn', async function () {
    var app = await moMan({ truLoi: 1 });
    await app.bam(app.mot('[data-tkbu="HDB-26-10-00033"]'));
    dung('có báo lỗi', app.tin.some(function (t) { return t.indexOf('baoTin:Đang kiểm kê') === 0; }));
  });

  await ca('Chọn điểm rồi bấm Trừ bù cả điểm: gọi đúng điểm', async function () {
    var app = await moMan();
    bang('chưa chọn điểm thì chưa có nút cả điểm', app.tim('#tkBuDiem').length, 0);
    await app.bam(chip(app, 'diem|TCV'));
    bang('máy chủ nhận điểm', app.mc.cuoi('vagabond.tru_kho_bu.ds_chua_tru_kho').a.diem, 'TCV');
    await app.bam(app.mot('#tkBuDiem'));
    bang('gọi trừ bù cả điểm', app.mc.cuoi('vagabond.tru_kho_bu.tru_bu_diem').a, { diem: 'TCV' });
  });

  await ca('Xuất Excel gửi đúng bộ lọc đang áp', async function () {
    var app = await moMan();
    await app.bam(chip(app, 'chang|kho_het'));
    await app.bam(app.mot('[data-dsxuat]'));
    var x = app.mc.cuoi('vagabond.khung.cong_cu_ds.xuat_excel');
    bang('màn', x.a.man, 'tru_kho');
    bang('bộ lọc Excel bằng bộ lọc màn', JSON.parse(x.a.loc), app.mc.cuoi('vagabond.tru_kho_bu.ds_chua_tru_kho').a);
    bang('tải tệp', app.tai, ['tru_kho.xlsx']);
  });

  await ca('Chip bill quầy và chip đơn Sales đọc cùng một khoá tt_kho, cùng chữ', async function () {
    var app = appMoi();
    var mong = { da_tru: '📦 Đã trừ kho', chua_tru: '📦 Chưa trừ kho', mot_phan: '📦 Đã trừ một phần', da_tru_bu: '🔁 Đã trừ bù' };
    Object.keys(mong).forEach(function (k) {
      var r = { docstatus: 1, tt_kho: k, vgb_pt_thanh_toan: 'Tiền mặt' };
      dung('bill quầy ' + k, app.g.posChipBill(r).indexOf(mong[k]) >= 0);
      dung('đơn Sales ' + k, app.g.dsChips(r).indexOf(mong[k]) >= 0);
    });
    var r0 = { docstatus: 1, tt_kho: '', vgb_pt_thanh_toan: 'Tiền mặt' };
    dung('không có khoá thì không có chip kho ở bill', !/Đã trừ|Chưa trừ kho|trừ bù/.test(app.g.posChipBill(r0)));
    dung('không có khoá thì không có chip kho ở đơn Sales', !/Đã trừ|Chưa trừ kho|trừ bù/.test(app.g.dsChips(r0)));
  });

  await ca('Chip lọc Chưa trừ kho gồm cả tờ trừ một phần, không gồm tờ đã trừ hay đã trừ bù', async function () {
    var app = appMoi();
    var loc = app.g.tkLoc();
    bang('hai chip lọc', loc.map(function (c) { return c.k; }), ['chua_tru_kho', 'da_tru_bu']);
    var ds = ['da_tru', 'chua_tru', 'mot_phan', 'da_tru_bu', ''].map(function (k) { return { tt_kho: k }; });
    bang('Chưa trừ kho', ds.filter(loc[0].loc).map(function (r) { return r.tt_kho; }), ['chua_tru', 'mot_phan']);
    bang('Đã trừ bù', ds.filter(loc[1].loc).map(function (r) { return r.tt_kho; }), ['da_tru_bu']);
  });

  await ca('Khối Kho trên chi tiết hoá đơn: chỉ tờ đã ghi sổ có cờ, nạp sau, bấm Trừ bù gọi đúng tờ', async function () {
    var app = appMoi();
    bang('nháp không có khối', app.g.tkKhoiChiTiet({ name: 'X', docstatus: 0, vgb_tru_kho_ban: 1 }), '');
    bang('tờ không qua luồng trừ kho không có khối', app.g.tkKhoiChiTiet({ name: 'X', docstatus: 1 }), '');
    var b = app.g.frame('Hoá đơn', '<div>bill</div>' + app.g.tkKhoiChiTiet({ name: 'HDB-26-10-00033', docstatus: 1, vgb_tru_kho_ban: 1, vgb_chua_tru_kho: 1 }));
    await app.g.tkNapKhoi(b); await nghi();
    bang('hỏi trạng thái đúng tờ', app.mc.cuoi('vagabond.tru_kho_bu.tt_hoa_don').a, { hoa_don: 'HDB-26-10-00033' });
    var khoi = app.mot('#tkKhoi');
    dung('khối có chip Chưa trừ kho', chu(khoi).indexOf('📦 Chưa trừ kho') >= 0);
    var nut = khoi.querySelectorAll('[data-tkbu]');
    bang('khối có đúng một nút Trừ bù', nut.length, 1);
    await app.bam(nut[0]);
    bang('gọi trừ bù', app.mc.cuoi('vagabond.tru_kho_bu.tru_bu_hd').a, { hoa_don: 'HDB-26-10-00033' });
  });

  console.log('  tru_kho_bu_550: ' + ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng');
  if (ket.hong) { ket.loi.forEach(function (l) { console.log('  HỎNG  ' + l); }); process.exit(1); }
})();

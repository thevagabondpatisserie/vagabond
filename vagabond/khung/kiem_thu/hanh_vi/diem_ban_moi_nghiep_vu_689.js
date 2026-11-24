/* Ca kiểm HÀNH VI v689: điểm bán mới hoặc đang tắt hiện ở màn nghiệp vụ (anh Việt 23/11/2026).
 *
 * Chị Dung báo màn Biên nhận nộp tiền không có điểm Hội chợ, trong khi Báo cáo BC03 có
 * 11 đơn Hội chợ. Điểm Hội chợ đang tắt sau sự kiện, và màn nghiệp vụ đọc danh sách
 * "chỉ điểm đang bật", hoặc gõ tay ba điểm ngay trong mã. Ca này nạp THẬT hàm vẽ của
 * màn Hoá đơn bán ra (16-mua-hang.js) và phần chip phạm vi khuyến mãi (13-khuyen-mai.js),
 * máy chủ giả trả danh mục có điểm thứ tư, rồi chốt điểm đó có chip và có tên.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/diem_ban_moi_nghiep_vu_689.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
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
var NEN = doc('00-nen.js'), TT = doc('09-tinh-tien-quay.js'), KM = doc('13-khuyen-mai.js');
// Nạp NGUYÊN tệp của bốn phần màn (khuôn danh sách, trừ kho bù có chip dùng chung,
// khuyến mãi, mua hàng), chỉ lấy lẻ vài hàm nền và nút chip của màn tính tiền.
var HAM = [layHam(NEN, 'h'), layHam(NEN, 'money'), layHam(TT, 'posChipNut')].join('\n');
var TEP = ['15-khuon-danh-sach.js', '49-tru-kho-bu.js', '13-khuyen-mai.js', '16-mua-hang.js'];

// Danh mục điểm bán giả: ba điểm cũ và một điểm thứ tư đang tắt (hội chợ).
var DIEM = [
  { ma: 'SALES', ten: 'Sales Online' }, { ma: 'TCV', ten: 'District 1' },
  { ma: 'NVHTN', ten: 'NVHTN' }, { ma: 'SUKIEN', ten: 'Hội chợ' },
];

function dungMoi() {
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);
  var goi = [];
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, Number: Number, Date: Date, setTimeout: setTimeout, isNaN: isNaN, parseInt: parseInt,
    frame: function (t, html) { khung.innerHTML = html; that._t = t; return khung; },
    go: function (fn) { return fn(); },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: ts });
      if (duong === 'vagabond.ke_toan.ds_hoa_don_ban') {
        return Promise.resolve({
          hd: [{ name: 'SINV-GIA-1', diem: 'SUKIEN', grand_total: 105000, posting_date: '2026-11-21', customer_name: 'Khách lẻ',
            docstatus: 1, nhom: 'da_ghi' }],
          diem_ds: DIEM, tong_dong: 1, bi_cat: 0, dem: {}, nhom: [], tu: '2026-10-24', den: '2026-11-23', tong: 105000, con_thu: 0,
        });
      }
      if (duong === 'vagabond.khuyen_mai.danh_muc') return Promise.resolve({ quay: DIEM, nhom_mon: [], hang: [], nhom_khach: [] });
      if (duong === 'vagabond.khuyen_mai.xem_ctkm') return Promise.resolve({ km: { name: 'CTKM-GIA-1', ten: 'Giảm thử', cach: 'Giam tong hoa don', quay: 'SUKIEN', kenh: '', dong: [] } });
      return Promise.resolve({});
    },
    toast: function () {}, sdGhep: function (a) { return a; }, CFGBH: null,
  };
  that.window = that;
  vm.runInNewContext(HAM, that, { filename: 'ham-689.js' });
  TEP.forEach(function (t) { vm.runInNewContext(doc(t), that, { filename: t }); });
  return { g: that, khung: khung, goi: goi };
}

var ket = { dat: 0, hong: 0 };
function dung(mo, dk) { if (!dk) throw new Error(mo); }
function bang(mo, a, b) { var x = JSON.stringify(a), y = JSON.stringify(b); if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y); }
function tick() { return new Promise(function (r) { setTimeout(r, 5); }); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); }
}
function chu(el) { var s = el._chu || ''; (el.children || []).forEach(function (c) { s += chu(c); }); return s; }

(async function () {
  console.log('v689 điểm bán mới hoặc đang tắt hiện ở màn nghiệp vụ');

  await ca('Hoá đơn bán ra: chip điểm bán theo danh mục máy chủ, có điểm thứ tư; bấm chip lọc đúng mã', async function () {
    var m = dungMoi();
    await m.g.scrHdBan(); await tick();
    var chip = m.khung.querySelectorAll('[data-ktbquay]').map(function (x) { return x.getAttribute('data-ktbquay'); });
    bang('đủ chip, đúng thứ tự', chip, ['', 'SALES', 'TCV', 'NVHTN', 'SUKIEN']);
    var t = chu(m.khung);
    dung('chip đầu là Mọi điểm bán, không còn "Cả ba điểm"', t.indexOf('Mọi điểm bán') >= 0 && t.indexOf('Cả ba điểm') < 0);
    dung('dòng hoá đơn hiện tên điểm, không hiện mã nội bộ', t.indexOf('Hội chợ') >= 0 && t.indexOf(' · SUKIEN') < 0);
    var hc = m.khung.querySelectorAll('[data-ktbquay]').filter(function (x) { return x.getAttribute('data-ktbquay') === 'SUKIEN'; })[0];
    m.khung.onclick({ target: { closest: function (s) { return s === '[data-ktbquay]' ? hc : null; } } }); await tick();
    bang('gửi máy chủ đúng mã điểm', m.goi[m.goi.length - 1].ts.quay, 'SUKIEN');
  });

  await ca('Khuyến mãi: tên điểm trong chip phạm vi lấy từ danh mục, có điểm thứ tư; trống là "mọi điểm bán"', async function () {
    var m = dungMoi();
    m.g.kmDm = { quay: DIEM };
    vm.runInNewContext('kmDm = window.kmDm;', m.g);
    var t = m.g.kmChipPhamVi({ kenh: [], quay_ds: ['SUKIEN', 'TCV'] });
    dung('có tên Hội chợ và District 1: ' + t, t.indexOf('Hội chợ') >= 0 && t.indexOf('District 1') >= 0);
    var rong = m.g.kmChipPhamVi({ kenh: [], quay_ds: [] });
    dung('không chọn quầy: mọi điểm bán', rong.indexOf('mọi điểm bán') >= 0 && rong.indexOf('ba điểm') < 0);
  });

  await ca('Codex #617: mở sheet chương trình thẳng từ CRM Zalo (chưa vào màn Khuyến mãi) vẫn có chip QUẦY đủ điểm', async function () {
    var m = dungMoi();
    bang('phiên mới: danh mục chưa nạp', vm.runInNewContext('kmDm', m.g), null);
    await m.g.kmSheetCtkm('CTKM-GIA-1'); await tick();
    dung('sheet tự gọi danh mục điểm bán', m.goi.some(function (x) { return x.duong === 'vagabond.khuyen_mai.danh_muc'; }));
    var chip = m.g.document.querySelectorAll('[data-kmquay]').map(function (x) { return x.getAttribute('data-kmquay'); });
    bang('đủ chip QUẦY, có điểm đang tắt', chip, ['SALES', 'TCV', 'NVHTN', 'SUKIEN']);
  });

  console.log('\n' + ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng.');
  process.exit(ket.hong ? 1 : 0);
})();

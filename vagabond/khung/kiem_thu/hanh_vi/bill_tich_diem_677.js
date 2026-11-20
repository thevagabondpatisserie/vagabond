/* Ca kiểm HÀNH VI v677: khối Khách thành viên trên màn bill Tạm tính.
 *
 * Dễ báo 20/11/2026: bill gọi qua QR đứng tên khách chung, màn Sửa hoá đơn chỉ
 * có ô xuất hoá đơn, chốt bill không cộng điểm cho ai. Nạp THẬT pbLaKhachChung,
 * pbKhoiTv, pbSoMoi, pbNoiTv của 10-bill-quay.js trong DOM giả, bấm đúng chuỗi
 * của thu ngân: gõ số, chọn khách, tạo khách mới bằng số, gỡ khách; đọc đúng
 * cửa máy chủ đã gọi (tich_diem_ban.gan_quay).
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/bill_tich_diem_677.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
var NEN = doc('00-nen.js'), BILL = doc('10-bill-quay.js');

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
var MA = layHam(NEN, 'h') + '\n' + ['pbLaKhachChung', 'pbKhoiTv', 'pbSoMoi', 'pbNoiTv'].map(function (t) { return layHam(BILL, t); }).join('\n');

var ket = { dat: 0, hong: 0 };
function bang(mo, a, b) {
  var x = JSON.stringify(a), y = JSON.stringify(b);
  if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y);
}
function dung(mo, dk) { if (!dk) throw new Error(mo); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n        ') : e)); }
}
function nghi(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
function chu(el) { var s = el._chu || ''; (el.children || []).forEach(function (c) { s += chu(c); }); return s; }

var KHACH = [{ name: 'CUST-0001', customer_name: 'Chị Lan', mobile_no: '0909123412' },
  { name: 'CUST-0003', customer_name: 'Chị Mai', mobile_no: '0988000111' },
  { name: 'Khách lẻ Online', customer_name: 'Khách lẻ Online', mobile_no: '' }];

function mo(d, o) {
  o = o || {};
  var tai = dg.taiLieuGia();
  var goi = [], tin = [], ve = [];
  var g = {
    document: tai, console: console, JSON: JSON, String: String, Object: Object, Promise: Promise, RegExp: RegExp,
    setTimeout: setTimeout, clearTimeout: clearTimeout,
    toast: function (s) { tin.push(String(s)); },
    promptSheet: function () { return Promise.resolve(o.ten === undefined ? 'Chị Hoa' : o.ten); },
    confirmSheet: function () { return Promise.resolve(o.dongY !== false); },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: ts });
      if (duong === 'vagabond.cong_no.tim_khach') {
        var tre = (o.tre && o.tre[ts.tu_khoa]) || 0;
        /* Như tim_kiem của máy chủ: tách theo từ, mỗi từ phải có trong tên hoặc số. */
        var ds = KHACH.filter(function (k) { return ts.tu_khoa.split(/\s+/).every(function (w) { return (k.customer_name + ' ' + k.mobile_no).indexOf(w) >= 0; }); });
        return nghi(tre).then(function () { return { khach: ds }; });
      }
      if (duong === 'vagabond.tich_diem_ban.gan_quay') {
        if (o.loi) return Promise.reject(new Error(o.loi));
        return Promise.resolve({ ok: 1, khach: ts.khach || (ts.sdt ? 'CUST-MOI' : ''), ten: ts.khach ? 'Chị Lan' : (ts.ten || '') });
      }
      return Promise.reject(new Error('api la: ' + duong));
    }
  };
  vm.runInNewContext(MA, g, { filename: 'bill-tich-diem.js' });
  var vb = new dg.ElementGia('div');
  vb.innerHTML = g.pbKhoiTv(d);
  tai.body.appendChild(vb);
  g.pbNoiTv(d, function () { ve.push(1); });
  return { g: g, tai: tai, goi: goi, tin: tin, ve: ve, vb: vb };
}
function id(m, x) { return m.tai.getElementById(x); }
function ganGoi(m) { return m.goi.filter(function (x) { return x.duong === 'vagabond.tich_diem_ban.gan_quay'; }).map(function (x) { return x.ts; }); }
async function go(m, chu1) {
  var i = id(m, 'pbTvTim');
  i.value = chu1;
  i.oninput();
  await nghi(320);
}

(async function () {
  var BILL_CHUNG = { name: 'ACC-SINV-0007', customer: 'Khách lẻ Online', customer_name: 'Khách lẻ Online' };
  var BILL_TV = { name: 'ACC-SINV-0007', customer: 'CUST-0001', customer_name: 'Chị Lan' };

  await ca('bill khách chung: khối nói vì sao không cộng điểm, có ô tìm, chưa có nút gỡ', async function () {
    var m = mo(BILL_CHUNG);
    dung('câu giải thích', chu(m.vb).indexOf('đứng tên khách chung') >= 0);
    dung('ô tìm', !!id(m, 'pbTvTim'));
    bang('không có nút gỡ, đổi', [!!id(m, 'pbTvGo'), !!id(m, 'pbTvDoi')], [false, false]);
  });

  await ca('gõ số có sẵn: hiện khách (bỏ khách chung khỏi danh sách), bấm là gắn đúng mã, vẽ lại màn', async function () {
    var m = mo(BILL_CHUNG);
    await go(m, '0909');
    var dong = m.vb.querySelectorAll('[data-tvkh]');
    bang('chỉ khách thật', dong.map(function (x) { return x.getAttribute('data-tvkh'); }), ['CUST-0001']);
    var h1 = id(m, 'pbTvGoi');
    await h1.onclick({ target: dong[0] });
    bang('gắn', ganGoi(m), [{ name: 'ACC-SINV-0007', khach: 'CUST-0001' }]);
    bang('vẽ lại, báo', [m.ve.length, /Đã gắn Chị Lan/.test(m.tin[0])], [1, true]);
    await go(m, '0909 123 412');
    bang('số đã có khách: không mời tạo trùng', [!!id(m, 'pbTvTao'), m.vb.querySelectorAll('[data-tvkh]').length], [false, 1]);
  });

  await ca('gõ đủ 10 số chưa ai có: nút tạo khách mới bằng số đó, hỏi tên, gửi số và tên', async function () {
    var m = mo(BILL_CHUNG);
    await go(m, '+84 912 345 678');
    var n = id(m, 'pbTvTao');
    dung('có nút tạo', !!n);
    bang('số chuẩn', n.getAttribute('data-so'), '0912345678');
    await id(m, 'pbTvGoi').onclick({ target: n });
    await nghi(5);
    bang('gửi', ganGoi(m), [{ name: 'ACC-SINV-0007', sdt: '0912345678', ten: 'Chị Hoa' }]);
  });

  await ca('bấm Huỷ ở hộp hỏi tên thì không tạo; số chưa đủ thì không có nút tạo', async function () {
    var m = mo(BILL_CHUNG, { ten: null });
    await go(m, '0912345678');
    await id(m, 'pbTvGoi').onclick({ target: id(m, 'pbTvTao') });
    bang('không gửi', ganGoi(m), []);
    await go(m, '091234');
    bang('số thiếu', !!id(m, 'pbTvTao'), false);
  });

  await ca('gõ nhanh hai lần, câu trả lời cũ về sau: giữ kết quả của lần gõ mới', async function () {
    var m = mo(BILL_CHUNG, { tre: { 'Chị': 400, '0909': 0 } });
    var i = id(m, 'pbTvTim');
    i.value = 'Chị'; i.oninput();
    await nghi(300);
    i.value = '0909'; i.oninput();
    await nghi(700);
    var dong = m.vb.querySelectorAll('[data-tvkh]').map(function (x) { return x.getAttribute('data-tvkh'); });
    bang('của 0909', dong, ['CUST-0001']);
    bang('hai lượt tìm', m.goi.map(function (x) { return x.ts.tu_khoa; }), ['Chị', '0909']);
  });

  await ca('bill đã có khách thành viên: hiện tên, Gỡ khách hỏi lại rồi gửi khách rỗng; Đổi khách mở ô tìm', async function () {
    var m = mo(BILL_TV);
    dung('tên', chu(m.vb).indexOf('Chị Lan') >= 0 && chu(m.vb).indexOf('cộng điểm cho khách này') >= 0);
    bang('ô tìm ẩn', id(m, 'pbTvTimO').getAttribute('style').indexOf('display:none') >= 0, true);
    id(m, 'pbTvDoi').onclick();
    bang('mở ô tìm', id(m, 'pbTvTimO').style.display, '');
    await id(m, 'pbTvGo').onclick();
    bang('gỡ', ganGoi(m), [{ name: 'ACC-SINV-0007', khach: '' }]);
    var m2 = mo(BILL_TV, { dongY: false });
    await m2.tai.getElementById('pbTvGo').onclick();
    bang('không đồng ý thì thôi', ganGoi(m2), []);
  });

  await ca('máy chủ từ chối: báo đúng câu, không vẽ lại', async function () {
    var m = mo(BILL_CHUNG, { loi: 'Chỉ gắn khách cho bill Tạm tính chưa chốt. Bill đã chốt thì giữ nguyên khách.' });
    await go(m, '0909');
    await id(m, 'pbTvGoi').onclick({ target: m.vb.querySelectorAll('[data-tvkh]')[0] });
    bang('báo', [m.tin[0], m.ve.length], ['Chỉ gắn khách cho bill Tạm tính chưa chốt. Bill đã chốt thì giữ nguyên khách.', 0]);
  });

  console.log('\nBill tích điểm v677: ' + ket.dat + ' đạt, ' + ket.hong + ' hỏng');
  process.exit(ket.hong ? 1 : 0);
})();

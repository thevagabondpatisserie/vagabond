/* Codex #573 (AGENTS.md 2b.3, 2b.5, 2b.6): màn Đơn giao của quầy có ba hàng chip
 * (trạng thái có đếm số, cách nhận, khoảng ngày), ô tìm nhanh, thẻ tóm tắt bấm số
 * là lọc và thanh "Tổng theo bộ lọc". Nhiều đơn: tìm hoặc chọn trạng thái chỉ hiện
 * đúng tập đơn tương ứng.
 *
 * CHẠY THẬT toàn bộ 76-don-giao-quay.js cùng posChipNut (09), kmHangChip (13),
 * anhMon, money (00) lấy nguyên từ mã nguồn, trong vm. Máy chủ là bản giả ghi lời gọi.
 * Chạy: node vagabond/khung/kiem_thu/hanh_vi/don_giao_quay_663.js
 */
'use strict';
var fs = require('fs'), path = require('path'), vm = require('vm');
var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
function layHam(src, ten) {
  var dau = src.indexOf('function ' + ten + '(');
  if (dau < 0) throw new Error('không thấy hàm ' + ten);
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error(ten);
}

var ket = { dat: 0, hong: 0 };
function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + (e && e.message)); }
}
async function nghi() { for (var i = 0; i < 8; i++) await Promise.resolve(); }

function don(ma, tt, ten, sdt, tuLay, daThu, mon) {
  return { ma: ma, tt: tt, ten: ten, sdt: sdt, tu_lay: tuLay ? 1 : 0, dia_chi: tuLay ? '' : '12 Lê Lợi, Quận 1', luc: '2026-11-16 09:15',
    mon: [{ ten: mon || 'Mousse chanh dây', sl: 1, tc: '', tp: [], anh: '/files/mousse.jpg' }], tien_hang: daThu, giam: 0, phi: 22000, mien_phi: 0,
    da_thu: daThu, cach_thu: 'Chuyển khoản', hen: 0, ghi_chu: '', gsm_link: '', bill: '', can_hoan: 0, ly_do: tt === 'Từ chối' ? 'Hết món' : '' };
}
var DS = [
  don('DW-2611-00001', 'Chờ quầy xác nhận', 'Lan', '0909123456', false, 117000),
  don('DW-2611-00002', 'Chờ quầy xác nhận', 'Lân Nguyễn', '0912000111', true, 95000, 'Trà lài'),
  don('DW-2611-00003', 'Đã xác nhận', 'Minh', '0933444555', false, 140000),
  don('DW-2611-00004', 'Đã gọi xe', 'Hoa', '0977888999', false, 210000),
  don('DW-2611-00005', 'Đã giao', 'Tuấn', '0988777666', true, 85000),
  don('DW-2611-00006', 'Từ chối', 'Lan', '0909123456', false, 60000),
];

function app(traDs) {
  var goi = [], man = { html: '', nghe: {}, nut: {} };
  var g = {
    console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array, Promise: Promise, Error: Error,
    posQuay: { ma: 'TCV' },
    h: function (s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;'); },
    /* v689: màn hỏi vgbManNay (phần 01) trước khi vẽ; ca nạp riêng phần màn nên giả hàm đó luôn còn đứng. */
    vgbManNay: function () { return function () { return true; }; },
    busy: function () {}, toast: function () {}, go: function () {},
    api: function (m, a) { goi.push([m, a]); return Promise.resolve(JSON.parse(JSON.stringify(traDs ? traDs(a) : { ds: DS, diem: 'TCV', ten_diem: 'District 1', cac_diem: [], hen: [10, 15, 20], ly_do: ['Hết món'] }))); },
    frame: function (tieuDe, html, opt) { man.html = html; man.chan = (opt && opt.footer) || ''; man.nghe = {}; man.nut = {};
      return { addEventListener: function (loai, f) { man.nghe[loai] = f; } }; },
    document: { getElementById: function (id) { return man.nut[id] || (man.nut[id] = { id: id, innerHTML: '', value: '' }); } },
  };
  vm.createContext(g);
  vm.runInContext(layHam(doc('00-nen.js'), 'money'), g);
  vm.runInContext(layHam(doc('00-nen.js'), 'anhMon'), g);
  vm.runInContext(layHam(doc('09-tinh-tien-quay.js'), 'posChipNut'), g);
  vm.runInContext(layHam(doc('13-khuyen-mai.js'), 'kmHangChip'), g);
  vm.runInContext(doc('76-don-giao-quay.js'), g);
  return {
    g: g, goi: goi, man: man, get nut() { return man.nut; },
    /* Bấm một phần tử có thuộc tính data-...: closest() trả chính nó khi khớp. */
    bam: async function (thuoc, gt) {
      var el = { getAttribute: function (k) { return k === thuoc ? String(gt) : null; },
        closest: function (sel) { return sel === '[' + thuoc + ']' ? el : null; } };
      await man.nghe.click({ target: el }); await nghi();
    },
    go: function (chu) { var o = { id: 'dqTim', value: chu }; man.nghe.input({ target: o }); },
    the: function (html) { return (String(html).match(/data-dq="([^"]+)"/g) || []).map(function (x) { return x.slice(9, -1); }); },
  };
}

(async function () {
  await ca('Mở màn: thẻ tóm tắt đủ số đơn, tiền đã thu (trừ đơn từ chối), đếm từng trạng thái; ba hàng chip và ô tìm; mọi chip cao 44 điểm; món có ảnh', async function () {
    var a = app(); await a.g.scrDonGiaoQuay(); await nghi();
    var h = a.man.html;
    dung('tổng 6 đơn, đã thu 647.000 đ', h.indexOf('6 đơn · 647.000 đ') >= 0);
    ['data-dqtt=""', 'data-dqcach="giao"', 'data-dqcach="lay"', 'data-dqngay="1"', 'data-dqngay="7"', 'id="dqTim"'].forEach(function (k) { dung('có ' + k, h.indexOf(k) >= 0); });
    dung('chip chờ xác nhận có đếm 2', /data-dqtt="Chờ quầy xác nhận"[^>]*>Chờ xác nhận <b>2<\/b>/.test(h));
    var chip = h.match(/<button data-dq(tt|cach|ngay)="[^"]*"[^>]*>/g) || [];
    dung('có chip', chip.length >= 11);
    chip.forEach(function (c) { if (c.indexOf('border-radius:999px') >= 0) dung('chip cao 44: ' + c.slice(0, 40), c.indexOf('min-height:44px') >= 0); });
    dung('ảnh món', h.indexOf('/files/mousse.jpg') >= 0);
    bang('đủ 6 thẻ', a.the(a.nut.dqDs ? a.nut.dqDs.innerHTML || h : h).length, 6);
  });

  await ca('Bấm chip Từ chối: chỉ hiện đơn từ chối, có thanh Tổng theo bộ lọc; bấm lại thì bỏ lọc', async function () {
    var a = app(); await a.g.scrDonGiaoQuay(); await nghi();
    await a.bam('data-dqtt', 'Từ chối');
    bang('chỉ một thẻ', a.the(a.man.html), ['DW-2611-00006']);
    dung('thanh tổng theo bộ lọc', a.man.html.indexOf('Tổng theo bộ lọc: <b>1</b> đơn · đã thu <b>0 đ</b>') >= 0);
    await a.bam('data-dqtt', 'Từ chối');
    bang('bỏ lọc: đủ 6', a.the(a.man.html).length, 6);
    dung('hết thanh lọc', a.man.html.indexOf('Tổng theo bộ lọc') < 0);
  });

  await ca('Bấm số Chờ xác nhận trên thẻ tóm tắt là lọc; thêm chip Tự lấy thì chỉ đơn tự lấy đang chờ', async function () {
    var a = app(); await a.g.scrDonGiaoQuay(); await nghi();
    await a.bam('data-dqtt', 'Chờ quầy xác nhận');
    bang('hai đơn chờ', a.the(a.man.html), ['DW-2611-00001', 'DW-2611-00002']);
    await a.bam('data-dqcach', 'lay');
    bang('chờ và tự lấy', a.the(a.man.html), ['DW-2611-00002']);
  });

  await ca('Gõ tìm: tên không dấu ra tên có dấu, số điện thoại ra đúng khách, mã đơn ra đúng đơn, tên món cũng tìm được; danh sách vẽ lại tại chỗ', async function () {
    var a = app(); await a.g.scrDonGiaoQuay(); await nghi();
    a.go('lan');
    bang('tên lan', a.the(a.nut.dqDs.innerHTML), ['DW-2611-00001', 'DW-2611-00002', 'DW-2611-00006']);
    a.go('0912 000');
    bang('số điện thoại', a.the(a.nut.dqDs.innerHTML), ['DW-2611-00002']);
    a.go('2611-00004');
    bang('mã đơn', a.the(a.nut.dqDs.innerHTML), ['DW-2611-00004']);
    a.go('tra lai');
    bang('tên món không dấu', a.the(a.nut.dqDs.innerHTML), ['DW-2611-00002']);
    a.go('khong co ai');
    dung('rỗng có câu chỉ đường', a.nut.dqDs.innerHTML.indexOf('Không có đơn khớp bộ lọc') >= 0);
    bang('ô tìm giữ chữ, không vẽ lại cả màn', a.g.DQ_TIM, 'khong co ai');
  });

  await ca('Chip 7 ngày gọi máy chủ với ngay=7; lỗi tải hiện câu làm gì tiếp, không để trắng', async function () {
    var a = app(); await a.g.scrDonGiaoQuay(); await nghi();
    await a.bam('data-dqngay', 7); await nghi();
    bang('lời gọi cuối', a.goi[a.goi.length - 1], ['vagabond.don_quay.danh_sach', { diem: 'TCV', ngay: 7 }]);
    var b = app(function () { throw new Error('mất mạng'); });
    b.g.api = function () { return Promise.reject(new Error('Mất kết nối')); };
    await b.g.scrDonGiaoQuay(); await nghi();
    dung('câu lỗi', b.man.html.indexOf('Chưa tải được đơn giao: Mất kết nối') >= 0 && b.man.html.indexOf('Tải lại') >= 0);
  });

  await ca('v664 chân màn có nút Chọn chuông cạnh Tải lại, bấm mở bảng chọn tiếng chuông', async function () {
    var a = app(); var mo = 0; a.g.gmbMoChonChuong = function () { mo++; };
    await a.g.scrDonGiaoQuay(); await nghi();
    dung('có nút', a.man.chan.indexOf('id="dqChuong"') >= 0 && a.man.chan.indexOf('Chọn chuông') >= 0 && a.man.chan.indexOf('id="dqTai"') >= 0);
    a.nut.dqChuong.onclick();
    bang('mở bảng chọn', mo, 1);
  });

  console.log('\n' + ket.dat + ' ca dat, ' + ket.hong + ' ca hong.');
  process.exitCode = ket.hong ? 1 : 0;
})();

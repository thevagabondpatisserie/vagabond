/* Codex #614 P2 (v691): giao diện mới thay ô chọn của hệ điều hành bằng nút mở hộp chọn sheet().
 * Người chỉ dùng bàn phím phải đổi được giá trị: Tab tới dòng, Enter hoặc Space chọn, mũi tên
 * lên xuống đi giữa các dòng. Ca nạp THẬT sheet() và hopPhim() của 00-nen.js vào DOM giả,
 * bấm phím qua đúng bộ phím chung của app, không gọi onPick hay click() thay người dùng.
 *
 *   node hop_chon_phim_614.js [đường 00-nen.js]     in JSON kết quả
 */
'use strict';
var fs = require('fs');
var path = require('path');
var dg = require('./dom_gia.js');
var NEN = process.argv[2] || path.resolve(__dirname, '..', '..', '..', 'public', 'js', 'bep', '00-nen.js');
var src = fs.readFileSync(NEN, 'utf8');
function cat(ten) {
  var i = src.indexOf('\nfunction ' + ten + '('), j = src.indexOf('\n}\n', i);
  if (i < 0 || j < 0) throw new Error('Không thấy ' + ten + ' trong 00-nen.js');
  return src.slice(i + 1, j + 2);
}
var tai = dg.taiLieuGia();
var hop = new Function('document', 'scanBarcode', 'hopTren', 'hopDangSua', 'hopDong', 'tlDong',
  cat('vgbChuan') + cat('vgbKhop') + cat('h') + cat('sheet') + cat('hopPhim') + '; return { sheet: sheet, hopPhim: hopPhim };')(
  tai, function () { return Promise.resolve(null); }, function () { return null; }, function () { return false; }, function () { }, function () { });

function phim(el, k) {
  var chan = 0;
  var ev = { key: k, target: el, preventDefault: function () { chan++; }, stopPropagation: function () { } };
  hop.hopPhim(ev);
  if (el.parentNode && typeof el.parentNode.onkeydown === 'function') el.parentNode.onkeydown(ev);
  return chan;
}
var ITEMS = [{ label: 'Mọi điểm bán', value: '' }, { label: 'Quận 1', value: 'Q1' }, { label: 'Tân Bình', value: 'TB' }];
var kq = {};
['Enter', ' '].forEach(function (k) {
  var chon = [];
  hop.sheet('Phạm vi', ITEMS, 'Q1', function (it) { chon.push(it.value); }, false);
  var ds = tai.querySelectorAll('.shi');
  kq[k === ' ' ? 'space' : 'enter'] = {
    tabindex: ds.map(function (d) { return d.getAttribute('tabindex'); }),
    role: ds.map(function (d) { return d.getAttribute('role'); }),
    chan: phim(ds[2], k), chon: chon, con_hop: tai.querySelectorAll('.sh').length
  };
  tai.querySelectorAll('.sh').forEach(function (o) { o.remove(); });
});
/* Mũi tên: tiêu điểm ở dòng 1, xuống tới dòng 2, xuống nữa vẫn dòng cuối, lên về dòng 1. */
hop.sheet('Phạm vi', ITEMS, 'Q1', function () { }, false);
var ds = tai.querySelectorAll('.shi'), buoc = [];
ds[1].focus();
[['ArrowDown', 2], ['ArrowDown', 2], ['ArrowUp', 1]].forEach(function (b) {
  phim(tai.activeElement || ds[1], b[0]);
  buoc.push(ds.indexOf(tai.activeElement));
});
kq.mui_ten = buoc;
process.stdout.write(JSON.stringify(kq));

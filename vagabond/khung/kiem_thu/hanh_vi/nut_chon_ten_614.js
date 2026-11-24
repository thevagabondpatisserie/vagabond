/* Codex #614 P2 vòng 2 (v691): nút thay ô chọn phải cho trình đọc màn hình đọc cả nhãn trường lẫn
 * giá trị đang chọn, và đọc giá trị MỚI sau khi chọn hay khi mã cũ đặt value. Ca nạp THẬT
 * uiBTenChon và uiBVeChon của 81-ui-b.js, select giả mang đúng phần hai hàm đọc.
 *
 *   node nut_chon_ten_614.js [đường 81-ui-b.js]     in JSON kết quả
 */
'use strict';
var fs = require('fs');
var path = require('path');
var dg = require('./dom_gia.js');
var TEP = process.argv[2] || path.resolve(__dirname, '..', '..', '..', 'public', 'js', 'bep', '81-ui-b.js');
var src = fs.readFileSync(TEP, 'utf8');
function cat(ten) {
  var i = src.indexOf('\nfunction ' + ten + '('), j = src.indexOf('\n}\n', i);
  if (i < 0 || j < 0) throw new Error('Không thấy ' + ten);
  return src.slice(i + 1, j + 2);
}
var tai = dg.taiLieuGia();
var ham = new Function('document', 'h', 'uiBSvg', cat('uiBTenChon') + cat('uiBVeChon') + '; return { ve: uiBVeChon };')(
  tai, function (s) { return String(s); }, function () { return '<svg></svg>'; });
var nhanTren = { tagName: 'DIV', textContent: 'Phạm vi', querySelector: function () { return null; } };
var sel = {
  id: '', disabled: false, selectedIndex: 0, previousElementSibling: nhanTren,
  options: [{ text: 'Một ngày', value: 'ngay' }, { text: 'Khoảng ngày', value: 'khoang' }],
  getAttribute: function () { return null; }, closest: function () { return null; },
  __uibNut: new dg.ElementGia('button')
};
var kq = {};
ham.ve(sel); kq.dau = sel.__uibNut.getAttribute('aria-label');
sel.selectedIndex = 1; ham.ve(sel); kq.sau_chon = sel.__uibNut.getAttribute('aria-label');
sel.selectedIndex = -1; ham.ve(sel); kq.trong = sel.__uibNut.getAttribute('aria-label');
process.stdout.write(JSON.stringify(kq));

/* v693 (test live #614, UI18, UI101): mọi emoji có trong nguồn app (lớp vẽ, danh mục Zalo chung,
 * mô đun máy chủ) phải được BỘ QUÉT THẬT của 81-ui-b.js nhận ra (UIB_RE_KY) và đổi được ra tên
 * biểu tượng (uiBTenKy). Bẫy đã gặp: ℹ️ (U+2139) nằm ngoài dải của bộ quét nên lọt ra màn dù đã
 * có trong bảng; 🩺 🏧 do máy chủ trả về chưa có trong bảng.
 *
 *   echo '["ℹ️","🩺"]' | node ui_b_ky_ve_duoc_693.js [đường 81-ui-b.js]   in JSON {ky: lý do}
 */
'use strict';
var fs = require('fs');
var path = require('path');
var TEP = process.argv[2] || path.resolve(__dirname, '..', '..', '..', 'public', 'js', 'bep', '81-ui-b.js');
var src = fs.readFileSync(TEP, 'utf8');
function khoi(dau) {
  var i = src.indexOf('\n' + dau);
  if (i < 0) throw new Error('Không thấy ' + dau);
  var j = src.indexOf(dau.indexOf('function') === 0 ? '\n}\n' : ';\n', i + 1);
  return src.slice(i + 1, j + (dau.indexOf('function') === 0 ? 3 : 2));
}
var ham = new Function(khoi('var UIB_EMOJI = ') + khoi('var UIB_CHAM = ') + khoi('var UIB_RE_KY = ') +
  khoi('function uiBTenKy(') + '; return { re: UIB_RE_KY, ten: uiBTenKy };')();
var ds = JSON.parse(fs.readFileSync(0, 'utf8'));
var hong = {};
ds.forEach(function (ky) {
  var chu = 'Mở ' + ky + ' Thông báo';
  ham.re.lastIndex = 0;
  var m = ham.re.exec(chu);
  if (!m) { hong[ky] = 'bộ quét không nhận ra'; return; }
  if (m[0].replace(/️/g, '') !== ky.replace(/️/g, '')) { hong[ky] = 'bộ quét cắt sai: ' + JSON.stringify(m[0]); return; }
  if (!ham.ten(m[0])) hong[ky] = 'không có biểu tượng';
});
process.stdout.write(JSON.stringify({ so: ds.length, hong: hong }));

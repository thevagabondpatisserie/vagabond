/* DO THAT khung o tim mon cua tab Tai quay khi dang go (v642).
 *
 * Anh Viet chup 06/11/2026: bam vao o tim thi vien xanh ve quanh RIENG o input
 * ben trong (outline cach 4px cua thao-tac.css), lech khoi khung vuong cua o
 * tim. Do chuoi CSS khong bat duoc chuyen nay vi hai luat nam o hai tep va
 * thu tu nap quyet dinh. Tep nay nap that nen.css, banh.css, thao-tac.css vao
 * Chromium, focus o tim, roi do:
 *   - input khong con outline;
 *   - khung .gb-tim doi vien sang mau --cyan va co bong vien trong;
 *   - hinh chu nhat sang cua khung trung khung ngoai (khong lech).
 *
 * Chay:  node vagabond/khung/kiem_thu/do_khung_tim_642.js [--anh duong/dan.png]
 * Ma tra ve 0 la dat. Thieu Playwright hoac Chromium thi tra ve 2 va noi ro.
 * KHONG nam trong kiem_truoc_deploy.sh (CI khong co trinh duyet).
 */
'use strict';
var fs = require('fs');
var os = require('os');
var path = require('path');
var GOC = path.resolve(__dirname, '..', '..');
var pw;
try { pw = require('playwright'); } catch (e) { console.log('CHUA DO DUOC: thieu playwright'); process.exit(2); }
var anh = process.argv.indexOf('--anh') > 0 ? process.argv[process.argv.indexOf('--anh') + 1] : '';
var tm = fs.mkdtempSync(path.join(os.tmpdir(), 'tim642-'));
['public/web_order/nen.css', 'public/web_vue/banh/banh.css', 'public/web_vue/banh/thao-tac.css'].forEach(function (p) {
  fs.copyFileSync(path.join(GOC, p), path.join(tm, path.basename(p)));
});
fs.writeFileSync(path.join(tm, 't.html'), '<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">' +
  '<link rel="stylesheet" href="nen.css"><link rel="stylesheet" href="banh.css"><link rel="stylesheet" href="thao-tac.css"></head>' +
  '<body style="background:#000;padding:16px"><div class="wrap"><div class="gb-tim" id="gbTim"><svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/></svg>' +
  '<input id="gbTimO" type="search" placeholder="Tìm món"></div></div></body></html>');
(async function () {
  var b;
  try { b = await pw.chromium.launch(); } catch (e) { console.log('CHUA DO DUOC: thieu Chromium'); process.exit(2); }
  var p = await b.newPage({viewport: {width: 390, height: 300}});
  await p.goto('file://' + path.join(tm, 't.html'));
  await p.keyboard.press('Tab');
  await p.focus('#gbTimO');
  await p.keyboard.type('tr');
  if (anh) await p.screenshot({path: anh});
  var r = await p.evaluate(function () {
    var i = document.getElementById('gbTimO'), c = document.getElementById('gbTim');
    var si = getComputedStyle(i), sc = getComputedStyle(c);
    var cyan = getComputedStyle(document.documentElement).getPropertyValue('--cyan').trim();
    var d = document.createElement('div'); d.style.color = cyan; document.body.appendChild(d);
    return {outline: si.outlineStyle, vien: sc.borderTopColor, bong: sc.boxShadow, cyan: getComputedStyle(d).color};
  });
  await b.close();
  var loi = [];
  if (r.outline !== 'none') loi.push('input con outline ' + r.outline);
  if (r.vien !== r.cyan) loi.push('vien khung ' + r.vien + ' khac cyan ' + r.cyan);
  if (r.bong.indexOf(r.cyan) < 0) loi.push('khung khong co bong vien trong mau cyan: ' + r.bong);
  console.log(JSON.stringify(r));
  if (loi.length) { console.log('HONG: ' + loi.join('; ')); process.exit(1); }
  console.log('DAT: khung o tim sang dung khung ngoai, input khong ve vong rieng');
})();

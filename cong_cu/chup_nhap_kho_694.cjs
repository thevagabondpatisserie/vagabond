/* v694: chụp và đo màn Nhập kho (phiếu chờ nhập) và hộp hỏi lại dòng chưa đánh dấu
 * Đã đếm trên Chromium 390x844, chạy ĐÚNG mã 06-nhap-kho-kiem-ke.js và chonSheet của
 * 00-nen.js với API giả lập, CSS nền của app. Dữ liệu giả.
 *
 * Đo: không cuộn ngang; vùng Đã đếm và hai nút hộp hỏi lại cao từ 44 điểm; chữ trong
 * vùng đo từ 13 điểm.
 * Chạy: node cong_cu/chup_nhap_kho_694.cjs /thu/muc/anh
 * Mã trả 0: đạt; 1: có số đo hỏng; 2: thiếu Playwright/Chromium.
 */
'use strict';
var fs = require('fs'), path = require('path');
var GOC = path.resolve(__dirname, '..'), BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
var RA = process.argv[2] || '/tmp';
var pw;
try { pw = require('playwright'); } catch (e) { console.log('THIẾU Playwright, chưa đo được'); process.exit(2); }
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
var NEN = doc('00-nen.js');
var a = NEN.indexOf('var CSS = `') + 'var CSS = `'.length, CSS = NEN.slice(a, NEN.indexOf('`;', a));
var HAM = ['h', 'today', 'chonSheet'].map(function (t) { return layHam(NEN, t); }).join('\n') + '\n' + doc('06-nhap-kho-kiem-ke.js');
var STUB = [
  'var root = document.getElementById("vgb");',
  'function frame(t, html, o) { o = o || {}; root.innerHTML = "<div class=\\"vh\\"><b>" + h(t) + "</b></div><div class=\\"vb\\" id=\\"vgbBody\\">" + html + "</div>" + (o.footer || ""); return document.getElementById("vgbBody"); }',
  'function api(m) { if (m === "frappe.client.get") return Promise.resolve({doctype:"Purchase Receipt",name:"PNK-GIA-0001",supplier_name:"Nhà cung cấp giả",modified:"m",items:[' +
    '{name:"D1",item_code:"CCDC90001",item_name:"Cây đánh trứng 460mm, French Whip",qty:1,uom:"PC",rate:1000,warehouse:"Kho tổng 307"},' +
    '{name:"D2",item_code:"CCDC90002",item_name:"Xẻng 290mm, Spatula",qty:1,uom:"PC",rate:1000,warehouse:"Kho tổng 307"},' +
    '{name:"D3",item_code:"CCDC90003",item_name:"Thìa gỗ L30cm, Food Spatula",qty:2,uom:"PC",rate:1000,warehouse:"Kho tổng 307"}]}); return Promise.reject(new Error("API giả lập thiếu " + m)); }',
  'function getList(dt) { return Promise.resolve(dt === "Item" ? [] : []); }',
  'function num(x) { return String(x); } function shortWh(x) { return x || ""; } function dmy(x) { return x; } function vgbCss() {} function busy() {} function toast() {} function errMsg(e) { return e.message; } function back() {}',
  'function confirmSheet() { return Promise.resolve(false); }',
].join('\n');

async function chay() {
  var b = await pw.chromium.launch();
  var trang = await b.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  var loi = [], hong = [];
  trang.on('pageerror', function (e) { loi.push(e.message); });
  await trang.setContent('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>' + CSS + '</style></head><body><div id="vgb"></div></body></html>');
  await trang.addScriptTag({ content: STUB + '\n' + HAM });
  async function doDo(ten, vung) {
    var kq = await trang.evaluate(function (vung) {
      var r = { tran: document.scrollingElement.scrollWidth > window.innerWidth + 1, nhoNut: [], nhoChu: [] };
      var goc = Array.prototype.slice.call(document.querySelectorAll(vung));
      function trong(n) { return goc.some(function (g) { return g.contains(n); }); }
      Array.prototype.slice.call(document.querySelectorAll('button, [role=button]')).filter(trong).forEach(function (n) {
        var rc = n.getBoundingClientRect();
        if (rc.width && rc.height < 43.5) r.nhoNut.push((n.textContent || '').trim().slice(0, 30) + ' ' + Math.round(rc.height));
      });
      var tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      while (tw.nextNode()) {
        var t = tw.currentNode, s = (t.nodeValue || '').trim();
        if (!s || !t.parentElement || !trong(t.parentElement)) continue;
        var px = parseFloat(getComputedStyle(t.parentElement).fontSize);
        if (px < 12.95 && t.parentElement.getBoundingClientRect().width) r.nhoChu.push(s.slice(0, 24) + ' ' + px);
      }
      return r;
    }, vung);
    if (kq.tran) hong.push(ten + ': cuộn ngang');
    if (kq.nhoNut.length) hong.push(ten + ': nút thấp hơn 44: ' + kq.nhoNut.join(' | '));
    if (kq.nhoChu.length) hong.push(ten + ': chữ dưới 13: ' + kq.nhoChu.join(' | '));
  }
  await trang.evaluate(function () { return scrRecvDoc('PNK-GIA-0001'); });
  await trang.waitForTimeout(300);
  await trang.click('[data-ok="0"]');
  await doDo('694-1-nhap-kho', '.rokw, .rcvh');
  await trang.screenshot({ path: path.join(RA, '694-1-nhap-kho.png') });
  await trang.click('#rcvSub');
  await trang.waitForSelector('.sh .shb');
  await trang.waitForTimeout(200);
  await doDo('694-2-hoi-lai', '.sh .shb');
  var hop = await trang.evaluate(function () { var s = document.querySelector('.sh .shb'); return { chu: s.innerText, nut: Array.prototype.map.call(s.querySelectorAll('button'), function (x) { return x.textContent.trim(); }) }; });
  if (hop.nut[0] !== 'Quay lại kiểm' || hop.nut[1] !== 'Xác nhận nhập cả các dòng chưa đánh dấu') hong.push('694-2: nút sai ' + hop.nut.join(' | '));
  if (hop.chu.indexOf('Xẻng 290mm, Spatula') < 0 || hop.chu.indexOf('Thìa gỗ L30cm') < 0 || hop.chu.indexOf('2 PC') < 0) hong.push('694-2: thiếu dòng trong danh sách');
  if (hop.chu.indexOf('Cây đánh trứng') >= 0) hong.push('694-2: dòng đã đánh dấu lại hiện trong danh sách');
  await trang.screenshot({ path: path.join(RA, '694-2-hoi-lai.png') });
  await b.close();
  if (loi.length) hong.push('lỗi trang: ' + loi.slice(0, 3).join(' | '));
  console.log(hong.length ? 'HỎNG:\n- ' + hong.join('\n- ') : 'Đạt: không cuộn ngang, vùng Đã đếm và nút từ 44 điểm, chữ từ 13 điểm.');
  process.exit(hong.length ? 1 : 0);
}
chay().catch(function (e) { console.log('Lỗi chạy: ' + e.message); process.exit(2); });

/* v654 màn Hoá đơn mua vào: nhãn XML, PDF theo tệp thật (HDM-26-11-00195).
   Chạy THẬT hdTepNhan, hdHopThu của 16-mua-hang.js trong node.
   Chốt: đủ tệp thì hai nhãn bấm mở được (đường tệp thật, cao 44 điểm); thiếu
   thì nhãn xám và lý do; người không có quyền không thấy nút đọc hộp thư. */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert');
const src = fs.readFileSync(path.resolve(__dirname, '../../../public/js/bep/16-mua-hang.js'), 'utf8');
function layHam(ten) {
  const dau = src.indexOf('function ' + ten + '(');
  if (dau < 0) throw new Error('Không thấy hàm ' + ten);
  let i = src.indexOf('{', dau), sau = 0;
  for (let j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Hàm ' + ten + ' không đóng ngoặc');
}
const g = { Date, String, Number };
vm.createContext(g);
vm.runInContext('function h(s) { return String(s == null ? "" : s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;"); }' +
  'function money(x) { return String(x); } function ngayNgan(s) { return String(s); }\n' + layHam('hdTepNhan') + '\n' + layHam('hdHopThu'), g);
const du = g.hdTepNhan({ tep_xml: '/private/files/XMLHD-1C26MYY-8882.xml', tep_pdf: '/private/files/HDDT-C26MYY-8882-NCC.pdf', tep_ly_do: '' });
assert((du.match(/<a /g) || []).length === 2, 'đủ tệp: hai nhãn bấm được');
assert(du.indexOf('href="/private/files/XMLHD-1C26MYY-8882.xml"') >= 0 && du.indexOf('href="/private/files/HDDT-C26MYY-8882-NCC.pdf"') >= 0, 'mở đúng tệp thật');
assert((du.match(/min-height:44px/g) || []).length === 2, 'nhãn cao 44 điểm');
const thieu = g.hdTepNhan({ tep_xml: '/private/files/a.xml', tep_pdf: '', tep_ly_do: 'Thư hoá đơn của nhà cung cấp không kèm PDF. Cần thì xin nhà cung cấp gửi lại.' });
assert(thieu.indexOf('Chưa có PDF') >= 0 && thieu.indexOf('không kèm PDF') >= 0, 'thiếu PDF: nhãn xám và lý do');
assert.equal(g.hdTepNhan({}), '', 'máy chủ cũ không gửi trường tệp: không vẽ gì');
const nho = (du + thieu).match(/font-size:\s*(\d+(?:\.\d+)?)px/g).map(x => parseFloat(x.replace(/[^\d.]/g, ''))).filter(x => x < 13);
assert.deepEqual(nho, [], 'chữ từ 13 điểm');
assert.equal(g.hdHopThu({ quyen: 0 }), '', 'không có quyền: không có nút đọc hộp thư');
const ht = g.hdHopThu({ quyen: 1, luc: '2026-11-13 11:17:00', con: 1950, dia_chi: 'hoadon@thevagabondpatisserie.com' });
assert(ht.indexOf('còn 1950 thư chưa đọc') >= 0 && ht.indexOf('data-hdthu="doc"') >= 0 && ht.indexOf('data-hdthu="quet"') >= 0, 'tình trạng hộp thư và hai nút');
assert((ht.match(/min-height:44px/g) || []).length >= 3, 'nút và ô ngày cao 44 điểm');
console.log('PASS 654 nhãn XML PDF trên Hoá đơn mua vào');

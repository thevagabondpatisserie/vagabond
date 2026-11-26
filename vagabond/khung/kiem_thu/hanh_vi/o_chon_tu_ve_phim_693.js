/* v693 (test live #614 UI102): ô chọn tự vẽ bằng div (Phân loại ở phiếu tặng quà, thẻ chọn kho và
 * phiếu ở Xuất kho, thẻ chọn bên nhận ở Hồ sơ thanh toán) phải vào được bằng Tab, đọc được
 * "nhãn: giá trị", và Enter hoặc Space mở như bấm chuột. Ca chạy THẬT hàm vẽ của từng tệp phần,
 * dựng HTML ra DOM giả, rồi bấm phím qua bộ phím chung hopPhim() của 00-nen.js; đếm số lần trình
 * xử lý click của màn chạy. Không gọi click() thay người dùng.
 *
 *   node o_chon_tu_ve_phim_693.js [thư mục bep]     in JSON {ô: {role, tabindex, ten, enter, space}}
 */
'use strict';
var fs = require('fs');
var path = require('path');
var dg = require('./dom_gia.js');
var BEP = process.argv[2] || path.resolve(__dirname, '..', '..', '..', 'public', 'js', 'bep');
function cat(tep, ten) {
  var src = fs.readFileSync(path.join(BEP, tep), 'utf8');
  var i = src.indexOf('\nfunction ' + ten + '('), j = src.indexOf('\n}\n', i);
  if (i < 0 || j < 0) throw new Error('Không thấy ' + ten + ' trong ' + tep);
  return src.slice(i + 1, j + 2);
}
var tai = dg.taiLieuGia();
var h = function (s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); };
var hopPhim = new Function('document', 'hopTren', 'hopDangSua', 'hopDong', 'tlDong',
  cat('00-nen.js', 'hopPhim') + '; return hopPhim;')(tai, function () { return null; }, function () { return false; }, function () { }, function () { });
var ve = new Function('h', 'anhMon',
  cat('34-crm-tang-qua.js', 'tqChon') + cat('45-xuat-kho-them.js', 'xktOChon') + cat('19-ho-so-tt.js', 'hsTheBenNhan') +
  '; return { tqChon: tqChon, xktOChon: xktOChon, hsTheBenNhan: hsTheBenNhan };')(h, function () { return '<img>'; });

var CA = {
  phan_loai: { html: ve.tqChon('Phân loại', 'tqNhom', 'Khách sỉ', 'Chọn phân loại'), chon: '#tqNhom' },
  phan_loai_trong: { html: ve.tqChon('Phân loại', 'tqNhom', '', 'Chọn phân loại'), chon: '#tqNhom' },
  kho_xuat: { html: ve.xktOChon('xktKho', '🏬', 'Kho xuất', { ten: 'Kho thành phẩm' }, { batBuoc: 1 }), chon: '#xktKho' },
  ben_nhan: { html: ve.hsTheBenNhan('hsMoUng', '🧑', 'Nhà cung cấp giả A', 'Mã NCC-0001', true), chon: '#hsMoUng' }
};
function phim(el, k) {
  var ev = { key: k, target: el, preventDefault: function () { }, stopPropagation: function () { } };
  hopPhim(ev);
}
var kq = {};
Object.keys(CA).forEach(function (ten) {
  var goc = tai.createElement('div');
  goc.innerHTML = CA[ten].html;
  tai.body.appendChild(goc);
  var o = goc.querySelector(CA[ten].chon);
  var bam = 0;
  o.addEventListener('click', function () { bam++; });
  phim(o, 'Enter'); var enter = bam;
  phim(o, ' '); var space = bam - enter;
  kq[ten] = { role: o.getAttribute('role'), tabindex: o.getAttribute('tabindex'), ten: o.getAttribute('aria-label'), enter: enter, space: space };
  goc.remove();
});
process.stdout.write(JSON.stringify(kq));

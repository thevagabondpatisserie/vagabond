/* v571, Codex #437 F2: phiếu đòi nợ ĐÃ thu đủ mà hoá đơn chưa có phiếu thu.
 *
 * Màn chi tiết phiếu phải hiện cảnh báo và nút Khớp tay để làm lại phiếu thu,
 * nhưng KHÔNG được hiện lại mã QR và khối chuyển khoản thủ công cho khách:
 * tiền đã về rồi, hiện QR là mời nhân viên gửi khách đòi lần hai.
 *
 * Nạp THẬT 11-khach-ca-hop-dong.js vào node, gọi đúng scrCnPhieu như khi bấm
 * vào một phiếu, đọc HTML và chân trang mà màn vẽ ra. Không gọi thêm hàm nào.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/phieu_doi_no_571.js
 */
'use strict';
var fs = require('fs');
var path = require('path');
var vm = require('vm');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var SRC = fs.readFileSync(path.join(GOC, 'vagabond', 'public', 'js', 'bep', '11-khach-ca-hop-dong.js'), 'utf8');

function moPhieu(d) {
  var ve = { html: '', foot: '' };
  var that = {
    console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Date: Date, Promise: Promise, parseInt: parseInt, parseFloat: parseFloat,
    isNaN: isNaN, encodeURIComponent: encodeURIComponent, setTimeout: setTimeout,
    h: function (s) { return String(s == null ? '' : s); },
    money: function (x) { return String(Math.round(x || 0)); },
    posNgayVn: function (x) { return String(x || ''); },
    hsCopy: function () {},
    api: function () { return Promise.resolve(d); },
    frame: function (t, html, o) { ve.html = html; ve.foot = (o && o.footer) || ''; return {}; },
    document: {
      getElementById: function () { return {}; },
      querySelectorAll: function () { return []; },
    },
  };
  that.window = that;
  vm.runInNewContext(SRC, that, { filename: '11-khach-ca-hop-dong.js' });
  return that.scrCnPhieu('X').then(function () { return ve; });
}

var PHIEU = {
  name: 'DNTT-26-10-00002', ma_phieu: 'DNTT-26-10-00002', khach: 'KH', ten_khach: 'Chị Hồng',
  ngay_tao: '2026-10-04', han_qr: '2026-10-11', het_han: false, tong_tien: 7600000,
  da_thu: 7600000, sepay: 0, con_thieu: 0, trang_thai: 'Da thu du', ghi_chu: '',
  qr: { bank: 'MB', stk: '123', ten: 'TV' }, dong: [{ hoa_don: 'HDB-1', so_tien: 4750000 }, { hoa_don: 'HDB-2', so_tien: 2850000 }],
  thieu_phieu_thu: 2,
};

var ket = { dat: 0, hong: 0 };
function ca(ten, ham) {
  return ham().then(function () { ket.dat++; console.log('  dat   ' + ten); },
    function (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); });
}
function dung(mo, dk) { if (!dk) throw new Error(mo); }

(async function () {
  console.log('Phieu doi no da thu du ma thieu phieu thu (v571, Codex #437 F2)\n');
  await ca('da thu du, thieu phieu thu: CO canh bao va nut Khop tay, KHONG co QR hay khoi chuyen khoan', async function () {
    var v = await moPhieu(Object.assign({}, PHIEU));
    dung('co canh bao chua co phieu thu', v.html.indexOf('chưa có phiếu thu') >= 0);
    dung('co nut Khop tay', v.foot.indexOf('cnKhop') >= 0);
    dung('KHONG co QR', v.html.indexOf('img.vietqr.io') < 0);
    dung('KHONG co khoi chuyen khoan thu cong', v.html.indexOf('CHUYỂN KHOẢN THỦ CÔNG') < 0);
  });
  await ca('phieu con thieu tien that thi van hien QR va khoi chuyen khoan nhu cu', async function () {
    var v = await moPhieu(Object.assign({}, PHIEU, { trang_thai: 'Thu thieu', da_thu: 2000000, con_thieu: 5600000, thieu_phieu_thu: 0 }));
    dung('co QR', v.html.indexOf('img.vietqr.io') >= 0);
    dung('co khoi chuyen khoan', v.html.indexOf('CHUYỂN KHOẢN THỦ CÔNG') >= 0);
  });
  await ca('da thu du va du phieu thu: bao da nhan du, khong nut Khop tay', async function () {
    var v = await moPhieu(Object.assign({}, PHIEU, { thieu_phieu_thu: 0 }));
    dung('bao da nhan du dung so', v.html.indexOf('ĐÃ NHẬN ĐỦ 7600000') >= 0);
    dung('khong nut Khop tay', v.foot.indexOf('cnKhop') < 0);
  });
  await ca('Codex #437 vong 7: khop tay mot phan (khong giao dich) thi QR va so chuyen khoan la PHAN CON LAI', async function () {
    // Tren 193b578: da_thu 2tr, sepay 0 thi QR van ma hoa 7,6tr va khoi
    // chuyen khoan van ghi 7,6tr, moi khach tra lai ca to.
    var v = await moPhieu(Object.assign({}, PHIEU, { trang_thai: 'Thu thieu', da_thu: 2000000, sepay: 0, con_thieu: 5600000, thieu_phieu_thu: 0 }));
    dung('QR ma hoa 5600000', v.html.indexOf('amount=5600000') >= 0);
    dung('QR KHONG ma hoa ca to', v.html.indexOf('amount=7600000') < 0);
    dung('khoi chuyen khoan ghi 5600000', v.html.indexOf('data-cnv="5600000 đ"') >= 0);
    dung('noi da nhan 2000000', v.html.indexOf('nhận 2000000') >= 0);
  });
  console.log('\n' + ket.dat + ' ca dat, ' + ket.hong + ' ca hong.');
  process.exit(ket.hong ? 1 : 0);
})();

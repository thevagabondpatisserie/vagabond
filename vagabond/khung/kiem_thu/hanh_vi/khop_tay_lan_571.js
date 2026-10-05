/* v571, Codex #437 vòng 11: khớp tay mất phản hồi thì bấm lại phải gửi
 * ĐÚNG mã lần cũ, để máy chủ nhận ra là một lần (không cộng tiền hai lần).
 *
 * Nạp THẬT 21-ke-toan-khac.js, chạy đúng chuỗi người dùng: bấm Khớp tay,
 * chọn "Không thấy giao dịch", gõ số, ghi chú, xác nhận. Lần đầu mạng rớt
 * (lời gọi lỗi), lần hai bấm lại; lần ba sau khi thành công là lần mới.
 *
 * Codex #437 vòng 12: hai lần chạm CÙNG LÚC (chưa lần nào tới máy chủ) cũng
 * phải dùng chung một mã lần. Ca này KHỞI ĐỘNG hai lời gọi rồi mới chờ,
 * không await lần lượt, vì await lần lượt đã che mất đường lỗi này.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/khop_tay_lan_571.js
 */
'use strict';
var fs = require('fs');
var path = require('path');
var vm = require('vm');
var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var SRC = fs.readFileSync(path.join(GOC, 'vagabond', 'public', 'js', 'bep', '21-ke-toan-khac.js'), 'utf8');

function dung(mo, dk) { if (!dk) throw new Error(mo); }

function dung_moi(hanh) {
  var goi = [], lanThu = 0;
  var that = {
    console: console, Math: Math, Date: Date, JSON: JSON, String: String, Promise: Promise,
    api: function (duong, ts) {
      if (duong === 'vagabond.cong_no.tim_giao_dich_thu') return new Promise(function (r) { setTimeout(function () { r({ rows: [] }); }, 5); });
      if (duong === 'vagabond.cong_no.khop_tay') {
        goi.push(ts.ma_lan);
        lanThu++;
        return hanh(lanThu);
      }
      return Promise.resolve({});
    },
    hoiChon: function () { return Promise.resolve('@go_tay'); },
    hoiSo: function () { return Promise.resolve(2000000); },
    hoiChu: function () { return Promise.resolve('khach dua'); },
    hoiCo: function () { return Promise.resolve(true); },
    busy: function () {}, baoTin: function () { return Promise.resolve(); }, toast: function () {},
    go: function () {}, money: function (x) { return String(x); }, hsNgayVn: function (x) { return x; },
  };
  vm.runInNewContext(SRC, that, { filename: '21-ke-toan-khac.js' });
  /* v577: loi "Khong thay giao dich" chi danh cho ke toan va bat dinh UNC.
     Ca nay do ma lan, nen hop dinh UNC tra ngay mot tep. */
  that.cnHoiUnc = function () { return Promise.resolve(['/private/files/unc.jpg']); };
  return { that: that, goi: goi };
}

var CA = [
  ['bam lai sau khi mat phan hoi gui dung ma lan cu, lan moi co ma moi', async function () {
    var m = dung_moi(function (n) { return n === 1 ? Promise.reject(new Error('mat ket noi')) : Promise.resolve({ ok: 1, loi_nhan: 'ok' }); });
    var d = { name: 'DNTT-1', ma_phieu: 'DNTT-1', tong_tien: 7600000, con_thieu: 7600000, ke_toan: 1 };
    await m.that.cnKhopTay(d);   // mat phan hoi
    await m.that.cnKhopTay(d);   // bam lai
    await m.that.cnKhopTay(d);   // lan khop moi sau khi da thanh cong
    dung('ba lan goi', m.goi.length === 3);
    dung('bam lai gui DUNG ma cu: ' + m.goi.join(','), m.goi[0] === m.goi[1]);
    dung('lan moi sau thanh cong co ma moi', m.goi[2] !== m.goi[1]);
  }],
  ['hai lan cham cung luc truoc khi toi may chu dung chung mot ma lan', async function () {
    var m = dung_moi(function () { return Promise.resolve({ ok: 1, loi_nhan: 'ok' }); });
    var d = { name: 'DNTT-2', ma_phieu: 'DNTT-2', tong_tien: 7600000, con_thieu: 7600000, ke_toan: 1 };
    // KHONG await lan luot: ca hai lan cham deu dang cho tim_giao_dich_thu.
    var a = m.that.cnKhopTay(d), b = m.that.cnKhopTay(d);
    await Promise.all([a, b]);
    dung('hai lan goi', m.goi.length === 2);
    dung('hai lan cham chung ma: ' + m.goi.join(','), m.goi[0] === m.goi[1]);
  }],
];

(async function () {
  var hong = 0;
  for (var i = 0; i < CA.length; i++) {
    try { await CA[i][1](); console.log('  dat   ' + CA[i][0]); }
    catch (e) { hong++; console.log('  HONG  ' + CA[i][0] + '\n        ' + e.message); }
  }
  console.log('\n' + (CA.length - hong) + ' ca dat, ' + hong + ' ca hong.');
  process.exit(hong ? 1 : 0);
})();

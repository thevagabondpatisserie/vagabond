/* v571, Codex #437 vòng 11: khớp tay mất phản hồi thì bấm lại phải gửi
 * ĐÚNG mã lần cũ, để máy chủ nhận ra là một lần (không cộng tiền hai lần).
 *
 * Nạp THẬT 21-ke-toan-khac.js, chạy đúng chuỗi người dùng: bấm Khớp tay,
 * chọn "Không thấy giao dịch", gõ số, ghi chú, xác nhận. Lần đầu mạng rớt
 * (lời gọi lỗi), lần hai bấm lại; lần ba sau khi thành công là lần mới.
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

(async function () {
  var goi = [], lanThu = 0;
  var that = {
    console: console, Math: Math, Date: Date, JSON: JSON, String: String, Promise: Promise,
    api: function (duong, ts) {
      if (duong === 'vagabond.cong_no.tim_giao_dich_thu') return Promise.resolve({ rows: [] });
      if (duong === 'vagabond.cong_no.khop_tay') {
        goi.push(ts.ma_lan);
        lanThu++;
        if (lanThu === 1) return Promise.reject(new Error('mat ket noi'));
        return Promise.resolve({ ok: 1, loi_nhan: 'ok' });
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
  var d = { name: 'DNTT-1', ma_phieu: 'DNTT-1', tong_tien: 7600000, con_thieu: 7600000 };
  var hong = 0;
  try {
    await that.cnKhopTay(d);   // mat phan hoi
    await that.cnKhopTay(d);   // bam lai
    await that.cnKhopTay(d);   // lan khop moi sau khi da thanh cong
    dung('ba lan goi', goi.length === 3);
    dung('bam lai gui DUNG ma cu: ' + goi.join(','), goi[0] === goi[1]);
    dung('lan moi sau thanh cong co ma moi', goi[2] !== goi[1]);
    console.log('  dat   bam lai sau khi mat phan hoi gui dung ma lan cu, lan moi co ma moi');
  } catch (e) {
    hong = 1;
    console.log('  HONG  ma lan khop tay\n        ' + e.message);
  }
  console.log('\n' + (hong ? 0 : 1) + ' ca dat, ' + hong + ' ca hong.');
  process.exit(hong);
})();

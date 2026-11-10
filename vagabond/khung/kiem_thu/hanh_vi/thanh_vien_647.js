/* Bo ca kiem HANH VI v647: luong qua quet QR theo mau A (anh Viet chon 10/11/2026).
 *
 * Anh Viet quet QR tren may da dang nhap san, trang nhay thang buoc Ho so nen
 * tuong trang khong hoi so dien thoai. Mau A: ba man cua luong qua nen sang,
 * thanh buoc co chu, buoc Ho so hien so da xac minh (che giua) kem Doi so,
 * nam sinh giau sau mot dong, nut ghi "Nhan qua 20.000d" (khong "Giam").
 *
 * CHAY THAT www/thanh-vien.html + chu.js + thanh-vien.js tren DOM gia
 * (tv_khung.js). Khach bam, go dung chuoi thao tac; khong goi ham noi bo.
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/thanh_vien_647.js
 */
'use strict';
var K = require('./tv_khung.js');

var ket = { dat: 0, hong: 0, loi: [] };
function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; ket.loi.push(ten + ' -> ' + (e && e.message)); }
}
function chuOf(el) { return el ? String(el.textContent || '') : ''; }
function sang(t) { return String(t.tl.body.getAttribute('class') || '').split(/\s+/).indexOf('tv-sang') >= 0; }

var SS = { otp: 1, qua: { mo: 1, uu_dai: 'Giảm 20.000đ' } };
/* Khach da xac minh so tu truoc (cookie con), ho so con thieu: dung ca anh Viet gap. */
function thieu(them) {
  var d = { ok: 1, ten: '', sdt: '0931224334', diem: 0, co_ho_so: true, don: [], don_loi: false, don_chua_mo: false,
    hang: { ten_hang: 'VOYAGER', anh: '', mo_ta: '', giam_gia: 0, tich_diem: 3 },
    ho_so: { ten: '', sinh_nhat: { ngay: '', thang: '', nam: '' }, email: '', so_thich: [], dong_y_zalo: 0, anh_mau: '' },
    anh: '', muc: { du: 0, tong: 5, thieu_qua: ['ten', 'sinh_nhat', 'dong_y'] },
    vi: [], qua: { mo: 1, uu_dai: 'Giảm 20.000đ', da_nhan: 0 }, tien_do: null, ma_tv: 'KL0412', tu_nam: '2026' };
  Object.keys(them || {}).forEach(function (k) { d[k] = them[k]; });
  return d;
}

(async function () {
  await ca('quét QR khi máy đã đăng nhập: bước Hồ sơ hiện số đã xác minh che giữa kèm Đổi số, nền sáng, thanh bước có chữ', async function () {
    var t = await K.dungTrang({ san_sang: SS, toi: thieu() }, '?qua=TCV');
    dung('mở hồ sơ ngắn', !K.an(t.tim('qua-ho-so')));
    dung('nền sáng mẫu A', sang(t));
    var x = t.tim('xm-so');
    dung('có dải số đã xác minh', !!x);
    bang('số che giữa', chuOf(x.children[0]), '0931 *** 334 đã xác minh');
    dung('không lộ số đầy đủ', chuOf(t.tim('qua-ho-so')).indexOf('0931224334') < 0);
    bang('nút Đổi số', chuOf(t.tim('nut-doi-so')), 'Đổi số');
    var buoc = t.tim('qua-ho-so').querySelector('.buoc').querySelectorAll('i');
    bang('ba bước có chữ', buoc.map(function (i) { return chuOf(i); }), ['Số điện thoại', 'Mã Zalo', 'Hồ sơ']);
  });

  await ca('năm sinh giấu sau một dòng; bấm Thêm năm sinh thì hiện ô và gửi đúng năm', async function () {
    var luu = null;
    var t = await K.dungTrang({ san_sang: SS, toi: thieu(), luu_ho_so: function (a) { luu = a.dat; return { ok: 1 }; },
      nhan_qua: { ok: 1, cu: 0, ma: 'QK7M2P', uu_dai: 'Giảm 20.000đ', han: '17/11/2026', trang_thai: 'dung_duoc' } }, '?qua=TCV');
    var f = t.tim('form-qua');
    dung('ô năm đang ẩn', K.an(f.querySelector('#o-nam')));
    dung('hai ô ngày tháng chiếm cả hàng', f.querySelector('.ba-o').classList.contains('hai-o'));
    bang('dòng mở năm', chuOf(t.tim('nut-them-nam')), '+ Thêm năm sinh (không bắt buộc)');
    bang('nhãn sinh nhật', chuOf(f.querySelector('.o-ngay').querySelector('.nhan')), 'Sinh nhật (để gửi quà đúng ngày)');
    t.tim('nut-them-nam').onclick();
    dung('bấm thì hiện ô năm', !K.an(f.querySelector('#o-nam')) && K.an(t.tim('nut-them-nam')));
    dung('về ba ô', !f.querySelector('.ba-o').classList.contains('hai-o'));
    bang('nút nói đúng giá trị quà', chuOf(t.tim('nut-nhan-qua')), 'Nhận quà 20.000đ');
    f.querySelector('#o-ten').value = 'Hoàng Việt';
    f.querySelector('#o-ngay').value = '13'; f.querySelector('#o-thang').value = '11'; f.querySelector('#o-nam').value = '1990';
    f.querySelector('#o-dong-y').checked = true;
    await f.onsubmit({ preventDefault: function () {} }); await K.nghi(3);
    bang('lưu đúng', [luu.ten, luu.ngay, luu.thang, luu.nam, luu.dong_y_zalo], ['Hoàng Việt', '13', '11', '1990', true]);
    dung('màn mã quà vẫn nền sáng', !K.an(t.tim('qua-ma')) && sang(t));
  });

  await ca('Đổi số: thoát phiên, về bước nhập số của đúng quầy, số mới đi qua mã Zalo như khách mới', async function () {
    // Khach go nham so 0931..., qua ma Zalo, toi buoc Ho so moi thay so sai.
    var phien = false;
    var t = await K.dungTrang({ san_sang: SS,
      toi: function () { return phien ? thieu() : { ok: 0, ly_do: 'chua_dang_nhap' }; },
      thoat: function () { phien = false; return { ok: 1 }; },
      gui_ma: { ok: 1 }, xac_thuc: function () { phien = true; return { ok: 1 }; } }, '?qua=TCV');
    t.tim('sdt').value = '0931 224 334';
    await t.tim('gui-ma').onsubmit({ preventDefault: function () {} });
    var o = t.tim('ma'); o.value = '482913'; o.oninput(); await K.nghi(4);
    dung('đã tới bước Hồ sơ', !K.an(t.tim('qua-ho-so')));
    await t.tim('nut-doi-so').onclick(); await K.nghi(2);
    bang('gọi thoát một lần', t.cac('thoat').length, 1);
    dung('về màn nhập số kiểu quà', !K.an(t.tim('dang-nhap')) && !K.an(t.tim('mo-dau-qua')) && K.an(t.tim('qua-ho-so')));
    dung('ô số trống, ô mã ẩn', t.tim('sdt').value === '' && K.an(t.tim('xac-thuc')));
    bang('bước 2 chưa sáng', t.tim('buoc-2').className, '');
    dung('vẫn nền sáng', sang(t));
    dung('câu hướng dẫn', chuOf(t.tim('trang-thai')).indexOf('Nhập số điện thoại có Zalo') >= 0);
    t.tim('sdt').value = '0909 123 412';
    await t.tim('gui-ma').onsubmit({ preventDefault: function () {} });
    bang('gửi mã số mới', t.cac('gui_ma').map(function (x) { return x.a; }), [{ sdt: '0931 224 334' }, { sdt: '0909 123 412' }]);
    bang('bước 2 sáng lên', t.tim('buoc-2').className, 'on');
  });

  await ca('trang thành viên thường (không quét QR) giữ nền đen, hồ sơ không có dải Đổi số, ô năm hiện sẵn', async function () {
    var d = thieu({ ten: 'Nguyễn Lan Anh', ho_so: { ten: 'Lan Anh', sinh_nhat: { ngay: 14, thang: 11, nam: '' }, email: '', so_thich: [], dong_y_zalo: 1, anh_mau: '' },
      muc: { du: 4, tong: 5, thieu_qua: [] }, qua: { mo: 1, uu_dai: 'Giảm 20.000đ', da_nhan: 1 } });
    var t = await K.dungTrang({ san_sang: SS, toi: d, cap_vi_tv: { ok: 1, moi: [] } }, '');
    dung('hiện trang thành viên', !K.an(t.tim('ho-so')));
    dung('không nền sáng', !sang(t));
    var f = t.tim('form-ho-so');
    dung('không có Đổi số', !f.querySelector('#nut-doi-so'));
    dung('ô năm hiện sẵn', !K.an(f.querySelector('#o-nam')) && !f.querySelector('#nut-them-nam'));
  });

  await ca('đi từ luồng quà sang trang thành viên (số của nhân viên) thì tắt nền sáng', async function () {
    var t = await K.dungTrang({ san_sang: SS, toi: thieu({ muc: { du: 5, tong: 5, thieu_qua: [] } }),
      nhan_qua: { ok: 0, ly_do: 'nhan_vien' } }, '?qua=TCV');
    dung('về trang thành viên', !K.an(t.tim('ho-so')));
    dung('nền đen lại', !sang(t));
  });

  console.log('Bo ca kiem HANH VI v647 (trang thanh vien mau A, luong qua quet QR)');
  ket.loi.forEach(function (l) { console.log('  HONG ' + l); });
  console.log(ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng, tổng ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
})();

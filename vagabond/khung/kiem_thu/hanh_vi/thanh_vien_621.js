/* Bo ca kiem HANH VI v621: trang thanh vien moi va luong qua chao mung tai quay.
 *
 * CHAY THAT www/thanh-vien.html + chu.js + thanh-vien.js tren DOM gia (tv_khung.js).
 * Khach bam, go dung chuoi thao tac; may chu gia ghi lai tung loi goi, ca kiem
 * doc dung tham so may chu nhan va chu khach thay. Khong goi ham noi bo nao.
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/thanh_vien_621.js
 */
'use strict';
var K = require('./tv_khung.js');
var dg = K.dg;

var ket = { dat: 0, hong: 0, loi: [] };
function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 4).join('\n         ') : String(e))); }
}
function bam(el) { if (!el) throw new Error('khong co nut de bam'); if (el.onclick) return el.onclick({ target: el }); el.dispatchEvent(dg.suKien('click', {}, el)); }
function chuOf(el) { return el ? String(el.textContent || '') : ''; }

var SS = { otp: 1, qua: { mo: 1, uu_dai: 'Giảm 20.000đ' } };
function hoSoDu(them) {
  var d = {
    ok: 1, ten: 'Nguyễn Lan Anh', sdt: '0909123412', diem: 184200, co_ho_so: true, don: [{ ma_don: '1', ngay_dat: '2026-10-30', tong: 1, mon: [] }],
    don_loi: false, don_chua_mo: false,
    hang: { ten_hang: 'VOYAGER', anh: '/files/the-voyager.jpg', mo_ta: 'Tích 3% mỗi hoá đơn', giam_gia: 0, tich_diem: 3 },
    ho_so: { ten: 'Lan Anh', sinh_nhat: { ngay: 14, thang: 11, nam: '' }, email: '', so_thich: ['entremet'], dong_y_zalo: 1, anh_mau: '' },
    anh: '', muc: { du: 4, tong: 5, thieu_qua: [] },
    vi: [{ ma: 'TT3F9A', ten: 'Trung thu', uu_dai: 'Giảm 15.000đ', dieu_kien: 'Dùng 1 lần cho 1 hoá đơn', han: '12/10/2026', trang_thai: 'da_dung', ngay_dung: '12/10/2026' },
      { ma: 'QK7M2P', ten: 'Quà chào mừng thành viên', uu_dai: 'Giảm 20.000đ', dieu_kien: 'Dùng 1 lần cho 1 hoá đơn', han: '06/11/2026', trang_thai: 'dung_duoc', ngay_dung: '' }],
    qua: { mo: 1, uu_dai: 'Giảm 20.000đ', han: '06/11/2026', so_ngay: 7, da_nhan: 1 },
    tien_do: { da_mua: 13580000, so_thang: 12, hang_tiep: 'VAGABONDER', con_thieu: 6420000, ty_le: 0.679 },
    ma_tv: 'KL0412', tu_nam: '2024',
  };
  Object.keys(them || {}).forEach(function (k) { d[k] = them[k]; });
  return d;
}

(async function () {
  await ca('trang chính: tên khách tự khai, số điểm lớn, hạng, tiến độ lên hạng, ba con số; đã nhận quà thì không mời', async function () {
    var t = await K.dungTrang({ san_sang: SS, toi: hoSoDu() });
    dung('hiện hồ sơ', !K.an(t.tim('ho-so')) && K.an(t.tim('dang-nhap')));
    bang('tên', chuOf(t.tim('ten')), 'Lan Anh');
    bang('điểm', chuOf(t.tim('diem')), (184200).toLocaleString('vi-VN'));
    bang('hạng', [chuOf(t.tim('hang-chip')), chuOf(t.tim('hang'))], ['VOYAGER', 'VOYAGER']);
    bang('ảnh thẻ thật', t.tim('anh-the').src, '/files/the-voyager.jpg');
    bang('thanh tiến độ 68%', t.tim('td-b').style.width, '68%');
    dung('câu tiến độ', chuOf(t.tim('td-chu')).indexOf('Thêm ' + (6420000).toLocaleString('vi-VN') + 'đ để lên VAGABONDER') >= 0);
    bang('ba con số', [chuOf(t.tim('so-don')), chuOf(t.tim('so-vc')), chuOf(t.tim('so-hs'))], ['01', '01', '4/5']);
    dung('đã nhận quà: không có khung mời', K.an(t.tim('moi-ho-so')));
    bang('mã thành viên trên thanh', chuOf(t.tim('vach-phai')), 'Mã KL0412');
    dung('ảnh đại diện mặc định là hình bánh đen trắng', t.tim('av-chinh').classList.contains('xam') && /anh-bia\.png/.test(t.tim('av-chinh').style.backgroundImage));
  });

  await ca('chưa nhận quà, hồ sơ thiếu: khung mời nói rõ giá trị quà và mở đúng tab Hồ sơ', async function () {
    var t = await K.dungTrang({ san_sang: SS, toi: hoSoDu({ muc: { du: 2, tong: 5, thieu_qua: ['sinh_nhat', 'dong_y'] }, qua: { mo: 1, uu_dai: 'Giảm 20.000đ', da_nhan: 0 } }) });
    dung('có khung mời', !K.an(t.tim('moi-ho-so')));
    dung('giá trị quà', chuOf(t.tim('moi-chu')).indexOf('voucher Giảm 20.000đ') >= 0 && chuOf(t.tim('moi-gia')) === '20.000đ');
    bam(t.tl.querySelector('[data-di]'));
    dung('mở tab Hồ sơ', !K.an(t.tim('tab-ho-so')) && K.an(t.tim('tab-chinh')));
    bang('nút tab đánh dấu', t.tl.querySelectorAll('[data-tab]').filter(function (b) { return b.getAttribute('aria-pressed') === 'true'; }).map(function (b) { return b.getAttribute('data-tab'); }), ['ho-so']);
  });

  await ca('trang thành viên (không qua quầy): bấm Cập nhật ngay, khai ngày sinh và đồng ý rồi Lưu là nhận voucher đã hứa (Codex PR #517 vòng 10)', async function () {
    // Đúng chuỗi Codex tái hiện: san_sang -> toi -> luu_ho_so -> toi. Trước khi
    // sửa: không có nhan_qua, ví rỗng, khung mời biến mất.
    var da = { luu: false, nhan: false };
    var thieu = hoSoDu({ ho_so: { ten: 'Lan Anh', sinh_nhat: { ngay: '', thang: '', nam: '' }, email: '', so_thich: [], dong_y_zalo: 0, anh_mau: '' },
      muc: { du: 1, tong: 5, thieu_qua: ['sinh_nhat', 'dong_y'] }, qua: { mo: 1, uu_dai: 'Giảm 20.000đ', han: '06/11/2026', so_ngay: 7, da_nhan: 0 }, vi: [] });
    var du = hoSoDu({ muc: { du: 3, tong: 5, thieu_qua: [] }, qua: { mo: 1, uu_dai: 'Giảm 20.000đ', han: '06/11/2026', so_ngay: 7, da_nhan: 0 }, vi: [] });
    var t = await K.dungTrang({
      san_sang: SS,
      toi: function () { return da.nhan ? hoSoDu() : da.luu ? du : thieu; },
      luu_ho_so: function () { da.luu = true; return { ok: 1 }; },
      nhan_qua: function () { da.nhan = true; return { ok: 1, cu: 0, ma: 'QK7M2P', uu_dai: 'Giảm 20.000đ', han: '06/11/2026', trang_thai: 'dung_duoc' }; },
    });
    dung('có khung mời', !K.an(t.tim('moi-ho-so')));
    bam(t.tim('moi-ho-so').querySelector('[data-di]'));
    var f = t.tim('form-ho-so');
    f.querySelector('#o-ngay').value = '14';
    f.querySelector('#o-thang').value = '11';
    f.querySelector('#o-dong-y').checked = true;
    f.onsubmit({ preventDefault: function () {} });
    await K.nghi(4);
    bang('lưu một lần', t.cac('luu_ho_so').length, 1);
    bang('nhận quà đúng một lần, không gắn quầy', t.cac('nhan_qua').map(function (x) { return x.a.quay; }), ['']);
    dung('ví có mã quà', t.tim('vi').querySelectorAll('[data-vc]').map(function (v) { return v.getAttribute('data-vc'); }).indexOf('QK7M2P') >= 0);
    dung('báo khách đã nhận', chuOf(t.tim('trang-thai')).indexOf('Giảm 20.000đ') >= 0);
  });

  await ca('hồ sơ đã đủ mà chưa nhận quà: khung mời đổi thành nút Nhận voucher, bấm là nhận', async function () {
    var nhan = false;
    var t = await K.dungTrang({
      san_sang: SS,
      toi: function () { return nhan ? hoSoDu() : hoSoDu({ muc: { du: 3, tong: 5, thieu_qua: [] }, qua: { mo: 1, uu_dai: 'Giảm 20.000đ', han: '06/11/2026', so_ngay: 7, da_nhan: 0 }, vi: [] }); },
      nhan_qua: function () { nhan = true; return { ok: 1, cu: 0, ma: 'QK7M2P', uu_dai: 'Giảm 20.000đ', han: '06/11/2026', trang_thai: 'dung_duoc' }; },
    });
    dung('vẫn có khung mời', !K.an(t.tim('moi-ho-so')));
    dung('nút Nhận voucher hiện, nút Cập nhật ẩn', !K.an(t.tim('nut-moi-nhan')) && K.an(t.tim('moi-ho-so').querySelector('[data-di]')));
    await bam(t.tim('nut-moi-nhan'));
    await K.nghi(4);
    bang('gọi nhận quà', t.cac('nhan_qua').length, 1);
    dung('mở Ví quà có mã', !K.an(t.tim('tab-vi')) && t.tim('vi').querySelectorAll('[data-vc]').map(function (v) { return v.getAttribute('data-vc'); }).indexOf('QK7M2P') >= 0);
    dung('đã nhận thì khung mời tắt', K.an(t.tim('moi-ho-so')));
  });

  await ca('đã nhận quà mà hồ sơ còn thiếu (rút đồng ý sau đó): không mời nhận quà lần nữa', async function () {
    var t = await K.dungTrang({ san_sang: SS, toi: hoSoDu({ muc: { du: 2, tong: 5, thieu_qua: ['dong_y'] } }) });
    dung('không có khung mời', K.an(t.tim('moi-ho-so')));
  });

  await ca('ví quà: mã thành viên có QR (mã khách, không phải số điện thoại), số che, voucher hiện đúng trạng thái', async function () {
    var t = await K.dungTrang({ san_sang: SS, toi: hoSoDu() });
    bam(t.tl.querySelector('[data-tab="vi"]'));
    dung('mở tab Ví quà', !K.an(t.tim('tab-vi')));
    bang('QR mang mã khách', t.qr, ['KL0412']);
    bang('mã chữ', chuOf(t.tim('the-tv-ma')), 'KL0412');
    dung('số điện thoại che', chuOf(t.tim('the-tv-ten')).indexOf('0909 *** 412') >= 0 && chuOf(t.tim('the-tv-ten')).indexOf('0909123412') < 0);
    var ve = t.tim('vi').querySelectorAll('[data-vc]');
    bang('thứ tự theo máy chủ', ve.map(function (v) { return v.getAttribute('data-vc'); }), ['TT3F9A', 'QK7M2P']);
    dung('mã đã dùng mờ đi và có chip', ve[0].className.indexOf('mo') >= 0 && chuOf(ve[0]).indexOf('Đã dùng') >= 0);
    dung('mã dùng được', chuOf(ve[1]).indexOf('Dùng được') >= 0 && chuOf(ve[1]).indexOf('Hạn 06/11/2026') >= 0);
  });

  await ca('hồ sơ: sửa tên, ngày sinh, món hay chọn, đồng ý Zalo rồi Lưu gửi đúng dữ liệu; hình bánh làm ảnh đại diện', async function () {
    var lan = 0;
    var t = await K.dungTrang({ san_sang: SS, toi: function () { lan++; return hoSoDu(); }, luu_ho_so: { ok: 1 } });
    bam(t.tl.querySelector('[data-tab="ho-so"]'));
    var f = t.tim('form-ho-so');
    bang('điền sẵn', [f.querySelector('#o-ten').value, f.querySelector('#o-ngay').value, f.querySelector('#o-thang').value, f.querySelector('#o-nam').value],
      ['Lan Anh', '14', '11', '']);
    dung('số đã xác minh hiện, không sửa được', chuOf(f).indexOf('Đã xác minh qua Zalo') >= 0 && !f.querySelector('#o-sdt'));
    f.querySelector('#o-ten').value = 'Lan Anh Nguyễn';
    f.querySelector('#o-nam').value = '1990';
    bam(f.querySelector('[data-st="tart"]'));
    bam(f.querySelector('[data-st="entremet"]'));
    f.querySelector('#o-dong-y').checked = false;
    f.onsubmit({ preventDefault: function () {} });
    await K.nghi(3);
    var l = t.cac('luu_ho_so');
    bang('một lần lưu', l.length, 1);
    bang('đúng dữ liệu', l[0].a.dat, { ten: 'Lan Anh Nguyễn', ngay: '14', thang: '11', nam: '1990', email: '', so_thich: ['tart'], dong_y_zalo: false });
    dung('có mã chống giả mạo', l[0].csrf === 'csrf-gia');
    dung('đọc lại hồ sơ', lan >= 2);
    bang('đã nhận quà rồi: lưu hồ sơ không gọi nhận quà', t.cac('nhan_qua').length, 0);
    bam(t.tim('anh-mau').querySelectorAll('[data-anh-mau]')[1]);
    await K.nghi(3);
    bang('chọn hình bánh', t.cac('luu_ho_so')[1].a.dat.anh_mau, 'entremet');
  });

  await ca('ảnh đại diện: thu về 512 px JPEG trên máy khách rồi mới gửi, không gửi ảnh gốc', async function () {
    var t = await K.dungTrang({ san_sang: SS, toi: hoSoDu(), doi_anh: { ok: 1 } });
    var ve = [];
    t.g.createImageBitmap = async function () { return { width: 3000, height: 2000 }; };
    var tao = t.tl.createElement;
    t.tl.createElement = function (ten) {
      if (ten !== 'canvas') return tao(ten);
      return { width: 0, height: 0, getContext: function () { return { drawImage: function () { ve.push([].slice.call(arguments, 1)); } }; },
        toDataURL: function (k, cl) { ve.push([k, cl, this.width, this.height]); return 'data:image/jpeg;base64,/9j/AAAA'; } };
    };
    var o = t.tim('chon-anh'); o.files = [{ name: 'goc.heic' }];
    await o.onchange(); await K.nghi(3);
    bang('cắt giữa ảnh ngang về vuông', ve[0], [500, 0, 2000, 2000, 0, 0, 512, 512]);
    bang('JPEG 512', ve[1], ['image/jpeg', 0.85, 512, 512]);
    bang('gửi ảnh đã thu nhỏ', t.cac('doi_anh').map(function (x) { return x.a.du_lieu; }), ['data:image/jpeg;base64,/9j/AAAA']);
  });

  await ca('quà tại quầy (?qua=TCV), khách mới: số Zalo, mã đủ 6 số tự gửi, hồ sơ ngắn, mã quà cho thu ngân', async function () {
    var phien = false, luu = null;
    var t = await K.dungTrang({
      san_sang: SS,
      toi: function () { return phien ? hoSoDu({ ho_so: { ten: '', sinh_nhat: { ngay: '', thang: '', nam: '' }, so_thich: [], dong_y_zalo: 0 }, muc: { du: 0, tong: 5, thieu_qua: ['ten', 'sinh_nhat', 'dong_y'] }, qua: { mo: 1, uu_dai: 'Giảm 20.000đ', da_nhan: 0 }, vi: [] }) : { ok: 0, ly_do: 'chua_dang_nhap' }; },
      gui_ma: { ok: 1 }, xac_thuc: function () { phien = true; return { ok: 1 }; },
      luu_ho_so: function (a) { luu = a.dat; return { ok: 1 }; },
      nhan_qua: function (a) { return { ok: 1, cu: 0, ma: 'QK7M2P', uu_dai: 'Giảm 20.000đ', han: '06/11/2026', trang_thai: 'dung_duoc', quay: a.quay }; },
    }, '?qua=tcv');
    dung('màn đăng nhập kiểu quà', !K.an(t.tim('dang-nhap')) && !K.an(t.tim('mo-dau-qua')) && K.an(t.tim('mo-dau-tv')));
    bang('giá trị quà từ máy chủ', chuOf(t.tim('qua-gia')), '20.000đ');
    t.tim('sdt').value = '0909 123 412';
    await t.tim('gui-ma').onsubmit({ preventDefault: function () {} });
    bang('gửi mã đúng số', t.cac('gui_ma')[0].a, { sdt: '0909 123 412' });
    dung('hiện ô mã', !K.an(t.tim('xac-thuc')));
    var o = t.tim('ma'); o.value = '48 2a913'; o.oninput(); await K.nghi(4);
    bang('đủ 6 số tự xác thực, bỏ ký tự lạ', t.cac('xac_thuc').map(function (x) { return x.a; }), [{ sdt: '0909 123 412', ma: '482913' }]);
    dung('hiện hồ sơ ngắn', !K.an(t.tim('qua-ho-so')));
    var f = t.tim('form-qua');
    dung('hồ sơ ngắn không hỏi email', !f.querySelector('#o-email'));
    f.querySelector('#o-ten').value = 'Lan Anh';
    f.querySelector('#o-ngay').value = '14'; f.querySelector('#o-thang').value = '11';
    await f.onsubmit({ preventDefault: function () {} });
    bang('chưa tích đồng ý: không gửi gì', [t.cac('luu_ho_so').length, t.cac('nhan_qua').length], [0, 0]);
    dung('nói rõ phải đồng ý', chuOf(t.tim('trang-thai')).indexOf('tích ô đồng ý') >= 0);
    f.querySelector('#o-dong-y').checked = true;
    await f.onsubmit({ preventDefault: function () {} }); await K.nghi(3);
    bang('lưu hồ sơ', [luu.ten, luu.ngay, luu.thang, luu.dong_y_zalo], ['Lan Anh', '14', '11', true]);
    bang('nhận quà đúng quầy', t.cac('nhan_qua').map(function (x) { return x.a; }), [{ quay: 'TCV' }]);
    dung('màn mã quà', !K.an(t.tim('qua-ma')) && K.an(t.tim('qua-ho-so')));
    bang('mã lớn', chuOf(t.tim('qua-ma-chu')), 'QK7M2P');
    bang('giá trị', chuOf(t.tim('qua-uu-dai')), '-20.000đ');
    bang('hạn', chuOf(t.tim('qua-han')), 'Dùng ngay hôm nay hoặc đến hết 06/11/2026');
    dung('lời chào', chuOf(t.tim('qua-chao')).indexOf('Lan Anh') >= 0);
  });

  await ca('quà tại quầy: số đã nhận trước đó thì hiện lại đúng mã cũ và nói rõ; mã cũ đã dùng thì không hiện mã', async function () {
    var t = await K.dungTrang({ san_sang: SS, toi: hoSoDu(),
      nhan_qua: { ok: 1, cu: 1, ma: 'QK7M2P', uu_dai: 'Giảm 20.000đ', han: '06/11/2026', trang_thai: 'dung_duoc' } }, '?qua=TCV');
    bang('đi thẳng nhận quà, không hỏi lại hồ sơ', [t.cac('luu_ho_so').length, t.cac('nhan_qua').length], [0, 1]);
    bang('mã cũ', chuOf(t.tim('qua-ma-chu')), 'QK7M2P');
    dung('câu đã nhận', chuOf(t.tim('qua-ghi')).indexOf('đã nhận quà chào mừng trước đó') >= 0);
    t = await K.dungTrang({ san_sang: SS, toi: hoSoDu(),
      nhan_qua: { ok: 1, cu: 1, ma: 'QK7M2P', uu_dai: 'Giảm 20.000đ', han: '06/11/2026', trang_thai: 'da_dung' } }, '?qua=TCV');
    dung('mã đã dùng: ẩn mã', K.an(t.tim('qua-ma-chu')));
    dung('câu đã dùng', chuOf(t.tim('qua-ghi')).indexOf('đã dùng. Mỗi số nhận một lần') >= 0);
  });

  await ca('quà tại quầy: máy chủ báo hồ sơ thiếu thì mở lại hồ sơ ngắn kèm câu; nhân viên thì báo lỗi, về trang thành viên', async function () {
    var t = await K.dungTrang({ san_sang: SS, toi: hoSoDu({ qua: { mo: 1, uu_dai: 'Giảm 20.000đ', da_nhan: 0 } }),
      nhan_qua: { ok: 0, ly_do: 'ho_so_thieu', thieu: ['dong_y'] } }, '?qua=TCV');
    dung('mở hồ sơ ngắn', !K.an(t.tim('qua-ho-so')));
    dung('câu', chuOf(t.tim('trang-thai')).indexOf('đồng ý nhận tin Zalo để nhận quà') >= 0);
    t = await K.dungTrang({ san_sang: SS, toi: hoSoDu({ qua: { mo: 1, uu_dai: 'Giảm 20.000đ', da_nhan: 0 } }),
      nhan_qua: { ok: 0, ly_do: 'nhan_vien' } }, '?qua=TCV');
    dung('về trang thành viên', !K.an(t.tim('ho-so')));
    dung('câu nhân viên', chuOf(t.tim('trang-thai')).indexOf('nhân viên Vagabond không nhận quà') >= 0);
  });

  await ca('bảng để quầy (?bang=TCV): QR mở đúng trang quà của quầy, giá trị quà từ chương trình; không hỏi hồ sơ', async function () {
    var t = await K.dungTrang({ san_sang: SS }, '?bang=tcv');
    dung('hiện bảng', !K.an(t.tim('bang-quay')) && K.an(t.tim('dang-nhap')) && K.an(t.tim('ho-so')));
    bang('QR', t.qr, ['https://thevagabond.vn/thanh-vien?qua=TCV']);
    bang('giá trị', chuOf(t.tim('bq-gia')), '20.000đ');
    bang('không hỏi hồ sơ', t.cac('toi').length, 0);
  });

  console.log('Bo ca kiem HANH VI v621 (trang thanh vien, qua chao mung tai quay)');
  ket.loi.forEach(function (l) { console.log('  HONG ' + l); });
  console.log(ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng, tổng ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
})();

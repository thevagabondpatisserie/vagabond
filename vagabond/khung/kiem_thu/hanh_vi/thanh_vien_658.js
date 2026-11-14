/* Bo ca kiem HANH VI v658: giao dien The Vagabond Club (anh Viet chot thiet ke
 * 14/11/2026): trang dang nhap L3 + K1, trang thanh vien J1c (hanh trinh hang),
 * T1 (the hang vuot ngang), U3 (dong thoi gian han diem).
 *
 * CHAY THAT www/thanh-vien.html + chu.js + thanh-vien.js tren DOM gia
 * (tv_khung.js). So lieu hang lay dung site that 14/11/2026: EXPLORER 2%,
 * VOYAGER tu 10 trieu 3%, VAGABONDER tu 20 trieu 5%, AMBASSADOR gan tay giam
 * 10% khong tich diem; qua sinh nhat 1 banh nhom Banh lanh toi da 185.000d.
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/thanh_vien_658.js
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
function chu(el) { return el ? String(el.textContent || '').replace(/\s+/g, ' ').trim() : ''; }
function lop(el) { return el ? String(el.getAttribute('class') || '') : ''; }

var QSN_TEN = 'Quà sinh nhật thành viên: tặng 1 bánh entremet';
var QSN_HANG = ['VOYAGER', 'VAGABONDER', 'AMBASSADOR', 'FAMILY'];
function hang(ten, tu, tich, giam, moi) {
  return { ten_hang: ten, chi_tieu_tu: tu, so_thang_xet: 12, tich_diem: tich, giam_gia: giam, moi: moi ? 1 : undefined,
    dac_quyen: QSN_HANG.indexOf(ten) >= 0 ? [QSN_TEN] : [] };
}
function theLe(them) {
  var tl = {
    hang: [hang('EXPLORER', 0, 2, 0), hang('VOYAGER', 10000000, 3, 0), hang('VAGABONDER', 20000000, 5, 0)],
    hang_moi: [hang('AMBASSADOR', 0, 0, 10, true)],
    qua_sn: { ten: QSN_TEN, nhom: 'Bánh lạnh', toi_da: 185000, hang: QSN_HANG },
    luat: { tran_pt: 50, toi_thieu: 10000, han_thang: 12, cach_han: 'Cuon chieu', nhac_ngay: 30, so_thang_hang: 12, nhan_diem: [] },
    sap_het: { diem: 12000, ngay: '30/11/2026' },
    lan_tich: { ds: [{ diem: 12000, ngay_tich: '29/11/2025', ngay_het: '30/11/2026' },
      { diem: 7200, ngay_tich: '17/10/2026', ngay_het: '18/10/2027' },
      { diem: 23400, ngay_tich: '01/11/2026', ngay_het: '02/11/2027' }],
      khac: { diem: 85800, so: 6 }, tong: 128400 },
  };
  Object.keys(them || {}).forEach(function (k) { tl[k] = them[k]; });
  return tl;
}
function toi(them) {
  var d = { ok: 1, ten: 'Minh Anh', sdt: '0931224334', diem: 128400, co_ho_so: true, don_loi: false, don_chua_mo: false, don: [],
    hang: { ten_hang: 'VOYAGER', anh: '', mo_ta: '', giam_gia: 0, tich_diem: 3 }, diem_dung_duoc: 1,
    ho_so: { ten: 'Minh Anh', sinh_nhat: { ngay: 2, thang: 12, nam: '' }, email: '', so_thich: [], dong_y_zalo: 1, anh_mau: '' },
    anh: '', muc: { du: 5, tong: 5, thieu_qua: [] }, vi: [], qua: { mo: 0 }, ma_tv: 'KL0412', tu_nam: '2025', tu_thang: '03/2025',
    tien_do: { da_mua: 13750000, so_thang: 12, hang_tiep: 'VAGABONDER', con_thieu: 6250000, ty_le: 0.6875 },
    the_le: theLe() };
  Object.keys(them || {}).forEach(function (k) { d[k] = them[k]; });
  return d;
}
var SS = { otp: 1, qua: { mo: 0 }, anh_club: [] };
var tien = function (v) { return v.toLocaleString('vi-VN') + 'đ'; };

(async function () {
  await ca('đầu trang thành viên: The Vagabond Club, thành viên từ tháng/năm, tên hạng lớn, lời chào', async function () {
    var t = await K.dungTrang({ san_sang: SS, toi: toi(), cap_vi_tv: { ok: 1, moi: [] } }, '');
    bang('hạng', chu(t.tim('hang')), 'VOYAGER');
    bang('dòng từ', t.tim('tab-chinh').querySelector('.cl-tu').querySelectorAll('.cum').map(chu), ['The Vagabond Club', 'Thành viên từ 03/2025']);
    bang('lời chào', t.tim('tab-chinh').querySelector('.cl-chao-ten').children.map(chu), ['Chào', 'Minh Anh']);
  });

  await ca('J1c: lõi ở góc, hạng cao gần lõi nhất; khách VOYAGER nằm đúng vòng giữa có chip Bạn ở đây; khung chi tiêu 12 tháng đúng số còn thiếu và hạng kế tiếp', async function () {
    var t = await K.dungTrang({ san_sang: SS, toi: toi(), cap_vi_tv: { ok: 1, moi: [] } }, '');
    dung('hiện khối', !K.an(t.tim('hanh-trinh')));
    var nhan = t.tim('ht-ve').querySelectorAll('.ht-ten-khoi');
    bang('thứ tự từ lõi ra', nhan.map(function (x) { return chu(x.querySelector('.ht-ten')); }), ['VAGABONDER', 'VOYAGER', 'EXPLORER']);
    bang('vòng của khách', nhan.map(function (x) { return lop(x).replace('ht-ten-khoi ', ''); }), ['tren', 'la', 'duoi']);
    dung('chip Bạn ở đây chỉ ở VOYAGER', chu(nhan[1]).indexOf('Bạn ở đây') >= 0 && chu(nhan[0]).indexOf('Bạn ở đây') < 0 && chu(nhan[2]).indexOf('Bạn ở đây') < 0);
    bang('điều kiện từng vòng', nhan.map(function (x) { return chu(x.querySelector('.ht-dk')); }), ['từ 20 triệu · tích 5%', 'từ 10 triệu · tích 3%', 'từ 0đ · tích 2%']);
    var cung = t.tim('ht-ve').querySelectorAll('.ht-cung');
    bang('bán kính ba cung', cung.map(function (x) { return x.style.width; }), ['300px', '520px', '740px']);
    dung('mô tả cho trình đọc màn hình', /Bạn đang ở hạng VOYAGER/.test(t.tim('ht-ve').getAttribute('aria-label')));
    dung('khung chi tiêu', !K.an(t.tim('ht-chi')));
    bang('tiêu đề khung', chu(t.tim('ht-tieu')), 'Chi tiêu 12 tháng');
    bang('số đã chi / mốc', chu(t.tim('ht-so')), tien(13750000) + ' / ' + tien(20000000));
    bang('thanh 69%', t.tim('ht-thanh').style.width, '69%');
    bang('hai chip', t.tim('ht-chips').querySelectorAll('.cl-chip').map(chu), ['Còn ' + tien(6250000), 'Vào vòng VAGABONDER · tích 5%']);
  });

  await ca('J1c: khách ở hạng cao nhất thì thanh đầy và chip vòng cao nhất; khách AMBASSADOR không nằm trên vòng nào nên không vẽ hành trình', async function () {
    var t = await K.dungTrang({ san_sang: SS, toi: toi({ hang: { ten_hang: 'VAGABONDER', giam_gia: 0, tich_diem: 5 },
      tien_do: { da_mua: 25000000, so_thang: 12, hang_tiep: '', con_thieu: 0, ty_le: 1 } }), cap_vi_tv: { ok: 1, moi: [] } }, '');
    bang('thanh đầy', t.tim('ht-thanh').style.width, '100%');
    bang('chip', chu(t.tim('ht-chips')), 'Bạn đang ở vòng cao nhất');
    bang('chỉ số đã chi', chu(t.tim('ht-so')), tien(25000000));
    var a = await K.dungTrang({ san_sang: SS, toi: toi({ hang: { ten_hang: 'AMBASSADOR', giam_gia: 10, tich_diem: 0 }, diem_dung_duoc: 0, diem: 0,
      tien_do: { da_mua: 4000000, so_thang: 12, hang_tiep: 'VOYAGER', con_thieu: 6000000, ty_le: 0.4 } }), cap_vi_tv: { ok: 1, moi: [] } }, '');
    dung('không vẽ hành trình cho hạng mời', K.an(a.tim('hanh-trinh')));
  });

  await ca('T1: đủ bốn hạng; AMBASSADOR không có dòng tích điểm, giảm 10% mỗi hoá đơn, do Vagabond mời; FAMILY, OWNER không hiện; hạng của khách nền xanh, hạng kế tiếp có số còn thiếu', async function () {
    var t = await K.dungTrang({ san_sang: SS, toi: toi(), cap_vi_tv: { ok: 1, moi: [] } }, '');
    var the = t.tim('the-le').querySelectorAll('.t1-the');
    bang('bốn hạng', the.map(function (x) { return chu(x.querySelector('.t1-ten')); }), ['EXPLORER', 'VOYAGER', 'VAGABONDER', 'AMBASSADOR']);
    bang('số lớn', the.map(function (x) { return chu(x.querySelector('.t1-so')); }), ['2% tích điểm', '3% tích điểm', '5% tích điểm', '-10% mỗi hoá đơn']);
    dung('AMBASSADOR không có chữ tích điểm', chu(the[3]).indexOf('tích điểm') < 0 && chu(the[3]).indexOf('1 điểm = 1đ') < 0);
    bang('điều kiện', the.map(function (x) { return chu(x.querySelector('.t1-dk')); }),
      ['Từ đơn đầu tiên', 'Chi từ 10 triệu trong 12 tháng', 'Chi từ 20 triệu trong 12 tháng', 'Do Vagabond mời']);
    dung('điều kiện không ngắt giữa số và đơn vị', the[1].querySelector('.t1-dk').querySelectorAll('.cum').map(chu).join('|') === '10 triệu|12 tháng');
    bang('kiểu thẻ', the.map(function (x) { return lop(x); }), ['t1-the', 't1-the la', 't1-the tiep', 't1-the moi']);
    dung('Hạng của bạn chỉ ở VOYAGER', chu(the[1]).indexOf('Hạng của bạn') >= 0 && the.filter(function (x) { return chu(x).indexOf('Hạng của bạn') >= 0; }).length === 1);
    dung('VAGABONDER: còn 6.250.000đ', chu(the[2]).indexOf('Còn ' + tien(6250000)) >= 0);
    bang('chip quà sinh nhật', the.map(function (x) { return chu(x).indexOf('Quà sinh nhật') >= 0; }), [false, true, true, true]);
    dung('không lặp tên chương trình dài', chu(the[1]).indexOf(QSN_TEN) < 0);
    dung('không hiện FAMILY, OWNER', chu(t.tim('the-le')).indexOf('FAMILY') < 0 && chu(t.tim('the-le')).indexOf('OWNER') < 0);
    bang('chấm chỉ vị trí đứng ở thẻ của khách', t.tim('the-le').querySelector('.t1-cham').children.map(function (x) { return lop(x); }), ['', 'on', '', '']);
    bang('ghi chú quà sinh nhật', chu(t.tim('the-le').querySelector('.t1-ghi')), 'Quà sinh nhật: 1 bánh nhóm Bánh lạnh, tối đa ' + tien(185000) + ', nhận trong tháng sinh nhật.');
    var hoaTiet = t.tim('the-le').querySelectorAll('.cl-mo14b');
    bang('hoạ tiết 14b ở ba thẻ theo chi tiêu', hoaTiet.length, 3);
    dung('hoạ tiết là trang trí', hoaTiet.every(function (x) { return x.getAttribute('aria-hidden') === 'true'; }));
  });

  await ca('T1: chương trình quà sinh nhật tắt (máy chủ không gửi qua_sn) thì không thẻ nào hứa quà và không có ghi chú', async function () {
    var t = await K.dungTrang({ san_sang: SS, toi: toi({ the_le: theLe({ qua_sn: null }) }), cap_vi_tv: { ok: 1, moi: [] } }, '');
    dung('không chip', chu(t.tim('the-le')).indexOf('Quà sinh nhật:') < 0 && t.tim('the-le').querySelectorAll('.t1-ghi').length === 0);
  });

  await ca('U3: các lần tích sắp theo hạn, lần sắp hết hạn nhất tô sáng kèm Dùng sớm, các lần khác gộp một dòng, tổng đang có, câu 50% đúng nguyên văn', async function () {
    var t = await K.dungTrang({ san_sang: SS, toi: toi(), cap_vi_tv: { ok: 1, moi: [] } }, '');
    var u = t.tim('dung-diem');
    dung('hiện', !K.an(u));
    var tieu = u.querySelector('.cl-tieu');
    bang('tiêu đề ngắt dòng chủ động', tieu.children.map(function (x) { return x.tagName.toLowerCase(); }), ['span', 'br', 'span']);
    bang('hai cụm', [chu(tieu.children[0]), chu(tieu.children[2])], ['Mỗi lần tích có hạn', '12 tháng riêng.']);
    dung('cụm 12 tháng không ngắt', tieu.querySelectorAll('.cum').map(chu).indexOf('12 tháng') >= 0);
    var moc = u.querySelectorAll('.u3-moc');
    bang('thứ tự hạn', moc.slice(0, 3).map(function (x) { return chu(x.querySelector('.u3-han')); }), ['Hết hạn 30/11/2026', 'Hết hạn 18/10/2027', 'Hết hạn 02/11/2027']);
    bang('số điểm từng lần', moc.slice(0, 3).map(function (x) { return chu(x.querySelector('.u3-diem')); }), ['12.000 điểm', '7.200 điểm', '23.400 điểm']);
    dung('lần đầu tô sáng', lop(moc[0]) === 'u3-moc gan' && lop(moc[1]) === 'u3-moc');
    dung('Dùng sớm ở lần đầu', chu(moc[0]).indexOf('Dùng sớm') >= 0 && chu(moc[1]).indexOf('Dùng sớm') < 0);
    bang('lần thứ hai ghi ngày tích', chu(moc[1].querySelector('.u3-tich')), 'Tích 17/10/2026');
    bang('dòng các lần khác', [chu(moc[3].querySelector('.u3-khac')), chu(moc[3].querySelector('.u3-so'))], ['Các lần tích khác', '85.800 điểm']);
    bang('tổng', u.querySelector('.u3-tong').children.map(chu), ['Tổng đang có', '128.400 điểm']);
    bang('câu 50%', chu(u.querySelector('.u3-tran')), 'Áp dụng thanh toán tối đa 50% giá trị đơn hàng');
    bang('ghi chú', chu(u.querySelector('.u3-ghi')), 'Zalo nhắc trước 30 ngày. Đơn bị huỷ thì điểm tự hoàn.');
    bang('khối điểm cùng câu 50%, hai dòng', t.tim('diem-chu').querySelectorAll('.dong').map(chu), ['Tương đương 128.400đ.', 'Áp dụng thanh toán tối đa 50% giá trị đơn hàng.']);
    bang('cụm không ngắt', t.tim('diem-chu').querySelectorAll('.cum').map(chu), ['128.400đ', 'tối đa 50%', 'giá trị đơn hàng.']);
    dung('dòng điểm sắp hết hạn', chu(t.tim('diem-het')).indexOf('12.000 điểm hết hạn ngày 30/11/2026') === 0);
  });

  await ca('U3: lần sắp hết hạn nhất chưa vào khung nhắc 30 ngày thì vẫn tô sáng nhưng không có Dùng sớm; không có lần tích thì chỉ còn tổng', async function () {
    var t = await K.dungTrang({ san_sang: SS, toi: toi({ the_le: theLe({ sap_het: null }) }), cap_vi_tv: { ok: 1, moi: [] } }, '');
    var moc = t.tim('dung-diem').querySelectorAll('.u3-moc');
    dung('tô sáng', lop(moc[0]) === 'u3-moc gan');
    dung('không Dùng sớm', chu(t.tim('dung-diem')).indexOf('Dùng sớm') < 0);
    var t2 = await K.dungTrang({ san_sang: SS, toi: toi({ diem: 0, the_le: theLe({ sap_het: null, lan_tich: { ds: [], khac: { diem: 0, so: 0 }, tong: 0 } }) }), cap_vi_tv: { ok: 1, moi: [] } }, '');
    bang('không mốc', t2.tim('dung-diem').querySelectorAll('.u3-moc').length, 0);
    bang('tổng 0', t2.tim('dung-diem').querySelector('.u3-tong').children.map(chu), ['Tổng đang có', '0 điểm']);
  });

  await ca('khách AMBASSADOR (không dùng điểm): khối điểm nói giảm thẳng, không nút Đặt bánh và dùng điểm, không khối U3', async function () {
    var t = await K.dungTrang({ san_sang: SS, toi: toi({ hang: { ten_hang: 'AMBASSADOR', giam_gia: 10, tich_diem: 0 }, diem_dung_duoc: 0 }), cap_vi_tv: { ok: 1, moi: [] } }, '');
    bang('câu', chu(t.tim('diem-chu')), 'Hạng của bạn được giảm thẳng trên mỗi hoá đơn, không dùng điểm.');
    dung('ẩn nút', K.an(t.tim('nut-dung-diem')));
    dung('ẩn U3', K.an(t.tim('dung-diem')));
    dung('ẩn dòng hết hạn', K.an(t.tim('diem-het')));
    dung('thẻ AMBASSADOR là hạng của bạn', lop(t.tim('the-le').querySelectorAll('.t1-the')[3]) === 't1-the la moi');
  });

  await ca('trang không còn chữ "tiền bánh" (anh Việt cấm), cả khi đã đăng nhập lẫn chưa', async function () {
    var t = await K.dungTrang({ san_sang: SS, toi: toi(), cap_vi_tv: { ok: 1, moi: [] } }, '');
    dung('đã đăng nhập', chu(t.tl.body).indexOf('tiền bánh') < 0);
    var g = await K.dungTrang({ san_sang: SS, toi: { ok: 0, ly_do: 'chua_dang_nhap' }, the_le: { the_le: theLe({ sap_het: null, lan_tich: null }) } }, '');
    dung('chưa đăng nhập', chu(g.tl.body).indexOf('tiền bánh') < 0);
  });

  await ca('đăng nhập L3 + K1: khối THE VAGABOND / CLUB, câu mời, ô Tích đến lấy % cao nhất từ máy chủ, đăng ký một dòng; khách xem thẻ hạng và luật điểm nhưng không có số riêng', async function () {
    var g = await K.dungTrang({ san_sang: SS, toi: { ok: 0, ly_do: 'chua_dang_nhap' }, the_le: { the_le: theLe({ sap_het: null, lan_tich: null }) } }, '');
    dung('màn đăng nhập', !K.an(g.tim('dang-nhap')) && !K.an(g.tim('mo-dau-tv')));
    bang('tên khối', g.tim('mo-dau-tv').querySelector('.cl-ten').children.map(chu), ['THE VAGABOND', 'CLUB']);
    bang('câu', g.tim('mo-dau-tv').querySelector('.cl-cau').querySelectorAll('.cum').map(chu), ['Đăng nhập để xem hạng,', 'điểm và quà của bạn.']);
    dung('không ghi quà sinh nhật trong câu', chu(g.tim('mo-dau-tv').querySelector('.cl-cau')).indexOf('sinh nhật') < 0);
    dung('ô Tích đến 5%', !K.an(g.tim('cl-tich')) && chu(g.tim('cl-tich-so')) === '5%');
    bang('nút đăng ký', g.tim('nut-dang-ky').querySelectorAll('.cum').map(chu).concat([chu(g.tim('nut-dang-ky').querySelector('.cl-chip'))]), ['Đăng ký thành viên tại đây', 'Đăng ký']);
    bang('nhãn ô số', chu(g.tim('gui-ma').querySelector('label').children[0]), 'Số điện thoại của bạn');
    bang('nút nhận mã', chu(g.tim('nut-gui')), 'Nhận mã đăng nhập');
    var k = g.tim('the-le-dn');
    dung('thẻ hạng cho khách', k.querySelectorAll('.t1-the').length === 4 && chu(k).indexOf('Hạng của bạn') < 0);
    dung('luật điểm không có tổng riêng', !K.an(g.tim('u3-dn')) && g.tim('u3-dn').querySelectorAll('.u3-tong').length === 0 && g.tim('u3-dn').querySelectorAll('.u3-moc').length === 0);
    g.tim('nut-dang-ky').onclick();
    dung('bấm Đăng ký: con trỏ vào ô số', g.tim('sdt')._daFocus === true);
    dung('và câu hướng dẫn', chu(g.tim('trang-thai')).indexOf('Nhập số điện thoại để đăng ký') === 0);
  });

  await ca('ảnh trang đăng nhập: lấy hai banner chỗ Trang thành viên từ máy chủ, ảnh điện thoại cho ô lớn; chưa có ảnh thì nền trơn; đường ảnh lạ bị bỏ', async function () {
    var ss = { otp: 1, qua: { mo: 0 }, anh_club: [{ id: 'a', anh: '/files/khach-1.jpg', anh_dt: '/files/khach-1-dt.jpg', mo_ta_anh: 'Khách ăn bánh ở cửa hàng' }, { id: 'b', anh: '/files/lat-banh.jpg' }] };
    var g = await K.dungTrang({ san_sang: ss, toi: { ok: 0, ly_do: 'chua_dang_nhap' }, the_le: { the_le: theLe() } }, '');
    bang('ô lớn', g.tim('cl-anh-1').style.backgroundImage, 'url("/files/khach-1-dt.jpg")');
    bang('ô nhỏ', g.tim('cl-anh-2').style.backgroundImage, 'url("/files/lat-banh.jpg")');
    bang('mô tả ảnh', g.tim('cl-anh-1').getAttribute('aria-label'), 'Khách ăn bánh ở cửa hàng');
    var r = await K.dungTrang({ san_sang: SS, toi: { ok: 0, ly_do: 'chua_dang_nhap' }, the_le: { the_le: theLe() } }, '');
    dung('chưa có ảnh: nền trơn', !r.tim('cl-anh-1').style.backgroundImage && !r.tim('cl-anh-2').style.backgroundImage);
    var x = await K.dungTrang({ san_sang: { otp: 1, qua: { mo: 0 }, anh_club: [{ anh: 'javascript:alert(1)' }, { anh: '/files/a.jpg") ; x(' }] }, toi: { ok: 0, ly_do: 'chua_dang_nhap' }, the_le: { the_le: theLe() } }, '');
    dung('đường lạ bị bỏ', !x.tim('cl-anh-1').style.backgroundImage && !x.tim('cl-anh-2').style.backgroundImage);
  });

  await ca('luồng quà quét QR ở quầy (?qua=) giữ màn sáng cũ: không khối CLUB, không nút đăng ký', async function () {
    var g = await K.dungTrang({ san_sang: { otp: 1, qua: { mo: 1, uu_dai: 'Giảm 20.000đ' }, anh_club: [] }, toi: { ok: 0, ly_do: 'chua_dang_nhap' }, the_le: { the_le: theLe() } }, '?qua=TCV');
    dung('ẩn khối CLUB', K.an(g.tim('mo-dau-tv')) && !K.an(g.tim('mo-dau-qua')));
    dung('ẩn nút đăng ký', K.an(g.tim('nut-dang-ky')));
  });

  console.log('Bo ca kiem HANH VI v658 (The Vagabond Club: dang nhap L3 + K1, J1c, T1, U3)');
  ket.loi.forEach(function (l) { console.log('  HONG ' + l); });
  console.log(ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng, tổng ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
})();

/* Bo ca kiem HANH VI v652: trang thanh vien co khoi The le, dong diem sap het
 * han, nut Dung diem dat banh, nut Mua lai (anh Viet 12/11/2026).
 *
 * CHAY THAT www/thanh-vien.html + chu.js + thanh-vien.js tren DOM gia
 * (tv_khung.js). Khach mo trang, bam dung nut; khong goi ham noi bo.
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/thanh_vien_652.js
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

var SS = { otp: 1, qua: { mo: 0 } };
/* So lieu that site 12/11/2026: VAGABONDER 3%, AMBASSADOR 7% va giam 10% (chi Ambassador giam). */
var THE_LE = {
  hang: [
    { ten_hang: 'VAGABONDER', chi_tieu_tu: 0, so_thang_xet: 12, tich_diem: 3, giam_gia: 0, dac_quyen: [] },
    { ten_hang: 'AMBASSADOR', chi_tieu_tu: 20000000, so_thang_xet: 12, tich_diem: 7, giam_gia: 10, dac_quyen: ['Quà sinh nhật Ambassador'] }],
  luat: { tran_pt: 50, toi_thieu: 10000, han_thang: 12, cach_han: 'Cuon chieu', nhac_ngay: 30, so_thang_hang: 12,
    nhan_diem: ['Thứ Năm hằng tuần, đặt bánh trên web được x2 điểm.'] },
  sap_het: { diem: 200, ngay: '21/11/2026' }
};
function toi(them) {
  var d = { ok: 1, ten: 'Lan Anh', sdt: '0931224334', diem: 1250, co_ho_so: true, don_loi: false, don_chua_mo: false,
    don: [{ ma: 'DW-2611-00007', ngay: '10/11/2026', tong: 450000, trang_thai: 'Đã nhận', mon: [{ ma: 'BAWC00139', ten: 'Entremet Mango', sl: 1 }, { ma: 'BKMN00011', ten: 'Mille-feuille', sl: 2 }] }],
    hang: { ten_hang: 'VAGABONDER', anh: '', mo_ta: '', giam_gia: 0, tich_diem: 3 },
    ho_so: { ten: 'Lan Anh', sinh_nhat: { ngay: 14, thang: 11, nam: '' }, email: '', so_thich: [], dong_y_zalo: 1, anh_mau: '' },
    anh: '', muc: { du: 5, tong: 5, thieu_qua: [] }, vi: [], qua: { mo: 0 }, tien_do: null, ma_tv: 'KL0412', tu_nam: '2026',
    the_le: THE_LE };
  Object.keys(them || {}).forEach(function (k) { d[k] = them[k]; });
  return d;
}

(async function () {
  await ca('thành viên đăng nhập: khối Thể lệ hai hạng đúng số site thật, chỉ Ambassador giảm 10%, chip Hạng hiện tại, bốn ô luật, câu nhân điểm, dòng điểm sắp hết hạn, nút Dùng điểm đặt bánh', async function () {
    var t = await K.dungTrang({ san_sang: SS, toi: toi(), cap_vi_tv: { ok: 1, moi: [] } }, '');
    var k = t.tim('the-le');
    dung('hiện khối thể lệ', !K.an(k));
    dung('ẩn khối quyền lợi cũ', K.an(t.tim('ql-cu')));
    var the = k.querySelectorAll('.tl-the');
    bang('hai hạng', the.map(function (x) { return chu(x.querySelector('.tl-ten')); }), ['VAGABONDER', 'AMBASSADOR']);
    dung('Vagabonder không có ô giảm', the[0].querySelectorAll('.tl-pt').length === 1);
    dung('Ambassador giảm 10%', chu(the[1]).indexOf('10%') >= 0 && the[1].querySelectorAll('.tl-pt').length === 2);
    dung('chip hạng hiện tại ở Vagabonder', !!the[0].querySelector('.tl-dang') && !the[1].querySelector('.tl-dang'));
    dung('quyền lợi lấy từ chương trình', chu(the[1].querySelector('.tl-quyen')) === 'Quà sinh nhật Ambassador');
    var o = function (x) { return chu(k.querySelector('[data-tlo="' + x + '"]')); };
    dung('ô Tích: % hạng và câu nhân điểm', o('tich').indexOf('3%') >= 0 && o('tich').indexOf('Thứ Năm hằng tuần, đặt bánh trên web được x2 điểm.') >= 0);
    dung('ô Dùng: 50% và web', o('dung').indexOf('50%') >= 0 && o('dung').indexOf('trên web') >= 0);
    dung('ô Hạn: 12 tháng, nhắc 30 ngày', o('han').indexOf('12 tháng') >= 0 && o('han').indexOf('30 ngày') >= 0);
    dung('ô Xét hạng', o('hang').indexOf('12 tháng') >= 0);
    dung('dòng điểm sắp hết hạn', !K.an(t.tim('diem-het')) && chu(t.tim('diem-het')).indexOf('200 điểm hết hạn ngày 21/11/2026') === 0);
    bang('nút dùng điểm dẫn tới trang đặt bánh', t.tim('nut-dung-diem').getAttribute('href'), '/banh');
  });

  await ca('không có điểm sắp hết hạn thì ẩn dòng; máy chủ chưa có thể lệ thì giữ khối quyền lợi cũ', async function () {
    var t = await K.dungTrang({ san_sang: SS, toi: toi({ the_le: { hang: [], luat: {}, sap_het: null } }), cap_vi_tv: { ok: 1, moi: [] } }, '');
    dung('ẩn thể lệ', K.an(t.tim('the-le')));
    dung('giữ quyền lợi cũ', !K.an(t.tim('ql-cu')));
    var t2 = await K.dungTrang({ san_sang: SS, toi: toi({ the_le: Object.assign({}, THE_LE, { sap_het: null }) }), cap_vi_tv: { ok: 1, moi: [] } }, '');
    dung('ẩn dòng hết hạn', K.an(t2.tim('diem-het')));
  });

  await ca('khách chưa đăng nhập vẫn xem được thể lệ (anh Việt 12/11): gọi the_le một lần, không có số riêng; lỗi thì ẩn khối', async function () {
    var t = await K.dungTrang({ san_sang: SS, toi: { ok: 0, ly_do: 'chua_dang_nhap' }, the_le: { the_le: Object.assign({}, THE_LE, { sap_het: null }) } }, '');
    var k = t.tim('the-le-dn');
    dung('hiện ở màn đăng nhập', !K.an(k) && !K.an(t.tim('dang-nhap')));
    bang('hai hạng', k.querySelectorAll('.tl-ten').map(chu), ['VAGABONDER', 'AMBASSADOR']);
    dung('không chip hạng hiện tại', !k.querySelector('.tl-dang'));
    bang('gọi the_le một lần', t.cac('the_le').length, 1);
    var t2 = await K.dungTrang({ san_sang: SS, toi: { ok: 0, ly_do: 'chua_dang_nhap' }, the_le: function () { throw new Error('mạng'); } }, '');
    dung('lỗi thì ẩn', K.an(t2.tim('the-le-dn')));
  });

  await ca('Mua lại: bấm ở đơn cũ thì giỏ trang Chọn bánh có đúng món và số, cộng dồn với giỏ đang có, rồi chuyển tới /banh', async function () {
    var kho = { 'vgb-gio-v1': JSON.stringify({ gio: [{ id: 'BKMN00011', qty: 1, cm: 1, nguon: 'order' }] }) };
    var t = await K.dungTrang({ san_sang: SS, toi: toi(), cap_vi_tv: { ok: 1, moi: [] } }, '');
    t.g.sessionStorage = { getItem: function (k) { return kho[k] || null; }, setItem: function (k, v) { kho[k] = v; } };
    var nut = t.tl.body.querySelectorAll('.mua-lai');
    bang('một nút Mua lại', nut.length, 1);
    bang('chữ nút', chu(nut[0]), 'Mua lại');
    nut[0].onclick();
    var gio = JSON.parse(kho['vgb-gio-v1']).gio.map(function (x) { return [x.id, x.qty, x.nguon]; });
    bang('giỏ cộng dồn', gio, [['BKMN00011', 3, 'order'], ['BAWC00139', 1, 'order']]);
    bang('chuyển trang', t.g.location.href, '/banh');
  });

  console.log('Bo ca kiem HANH VI v652 (the le, diem sap het han, mua lai)');
  ket.loi.forEach(function (l) { console.log('  HONG ' + l); });
  console.log(ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng, tổng ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
})();

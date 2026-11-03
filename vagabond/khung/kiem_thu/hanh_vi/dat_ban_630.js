/* Ca kiểm HÀNH VI v630: trang khách Đặt bàn kiểu mới (anh Việt duyệt mẫu 3).
 *
 * CHẠY THẬT www/dat-ban.html (phần <main>) + web_order/chu.js + web_order/dat-ban.js
 * trên DOM giả. Máy chủ giả trả cấu hình như dat_ban.cau_hinh và ghi lại đúng
 * thân lời gọi dat_ban.gui. Mỗi ca bấm, gõ đúng chuỗi khách làm; không gọi hàm
 * nội bộ nào của trang "cho chắc" (CLAUDE.md, ca kiểm có thể tự che lỗi).
 *
 * Nút đang tắt (disabled) thì bấm không có tác dụng, như trình duyệt thật: hàm
 * bam() không phát sự kiện vào nút tắt. Giờ đã qua hạn hôm nay là nút tắt.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/dat_ban_630.js
 */
'use strict';
var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
function doc(t) { return fs.readFileSync(path.join(GOC, t), 'utf8'); }
async function nghi(n) { for (var k = 0; k < (n || 4); k++) { for (var i = 0; i < 12; i++) await Promise.resolve(); await new Promise(function (r) { setImmediate(r); }); } }

var NHAN_TRANG = { dat_ban_nhan: 'HẸN MỘT BUỔI THONG THẢ', dat_ban_tieu_de: 'Đặt bàn tại Vagabond.', dat_ban_mo_ta: 'Chúng tôi sẽ liên hệ xác nhận chỗ.',
  dat_ban_dong: 'Tạm ngưng nhận đặt bàn online.', dat_ban_nut: 'Gửi yêu cầu đặt bàn', dat_ban_ho_tro: 'Cần hỗ trợ ngay?' };
var DIP = ['Không có dịp riêng', 'Sinh nhật', 'Kỷ niệm', 'Hẹn hò', 'Gặp đối tác', 'Họp nhóm', 'Khác'];
/* Thứ Hai 02/11/2026. Giờ máy chủ cỡ 13:30: 09:00, 11:30, 14:00 hôm nay đã qua hạn đặt. */
function cauHinh(them) {
  var c = { bat: true, co_so: 'TCV', ten_co_so: 'The Vagabond District 1', dia_chi: '9 Trần Cao Vân, Quận 1', hom_nay: '2026-11-02',
    toi_da_khach: 6, toi_da_ngay: 30, khung_gio: ['09:00', '11:30', '14:00', '18:00', '18:30', '21:00'],
    khung_gio_hom_nay: ['18:00', '18:30', '21:00'], khu_vuc: ['Bàn ghế cao - Cạnh quầy, hợp đi 2 người', 'Sofa thấp'], dip: DIP.slice(),
    anh: '/assets/vagabond/images/quay-tcv.jpg', dang_mo: true, gio_hom_nay: '9:00 - 21:00', hotline: '0931 224 334', hotline_so: '0931224334',
    chi_duong: 'https://maps.app.goo.gl/abc', zalo: 'javascript:alert(1)' };
  Object.keys(them || {}).forEach(function (k) { c[k] = them[k]; });
  return c;
}

/* traGui: mảng kịch bản trả lời cho từng lần gọi gui: 'mat_mang', {status, body}, hoặc bỏ trống là thành công. */
async function dungTrang(ch, traGui) {
  var html = doc('vagabond/www/dat-ban.html').replace(/\{\{ nhan\.([a-z_]+) \| e \}\}/g, function (_, k) { return NHAN_TRANG[k]; });
  var main = html.slice(html.indexOf('<main'), html.indexOf('</main>') + 7);
  var tl = dg.taiLieuGia();
  dg.doc(main, tl.body);
  var goc = tl.querySelector.bind(tl);
  tl.querySelector = function (chon) { return chon === 'meta[name=csrf-token]' ? { content: 'csrf-gia' } : goc(chon); };
  var gui = [], lan = 0;
  var g = {
    console: console, document: tl, setTimeout: setTimeout,
    crypto: { randomUUID: function () { return '11111111-2222-3333-4444-555555555555'; } },
    fetch: async function (url, c) {
      if (String(url).indexOf('vagabond.dat_ban.cau_hinh') >= 0) {
        if (ch === 'loi') throw new TypeError('Failed to fetch');
        return { ok: true, status: 200, json: async function () { return { message: ch }; } };
      }
      if (String(url).indexOf('vagabond.dat_ban.gui') < 0) throw new Error('goi la ' + url);
      gui.push({ body: c.body, csrf: c.headers['X-Frappe-CSRF-Token'] });
      var kb = (traGui || [])[lan++];
      if (kb === 'mat_mang') throw new TypeError('Failed to fetch');
      if (kb) return { ok: false, status: kb.status, json: async function () { return kb.body; } };
      return { ok: true, status: 200, json: async function () { return { message: { ok: 1, ma: 'ABCDEF123456' } }; } };
    },
  };
  g.window = g;
  vm.createContext(g);
  vm.runInContext(doc('vagabond/public/web_order/chu.js').split('(function ()')[0], g);
  vm.runInContext(doc('vagabond/public/web_order/dat-ban.js'), g);
  await nghi(4);
  function tim(id) { return tl.getElementById(id); }
  return {
    g: g, tl: tl, gui: gui, tim: tim,
    ngay: function () { return tim('ngay-dai').querySelectorAll('[data-ngay]'); },
    gio: function (k) { return tim('gio').querySelectorAll('[data-gio="' + k + '"]')[0]; },
    nut: function (cha, attr, gt) { return tim(cha).querySelectorAll('[' + attr + '="' + gt + '"]')[0]; },
    them: function (id) { return tim('dat-ban').querySelectorAll('[data-mo="' + id + '"]')[0]; },
    guiForm: async function () { await tim('dat-ban').onsubmit({ preventDefault: function () {} }); await nghi(2); },
  };
}

function bam(el) {
  if (!el) throw new Error('khong co nut de bam');
  if (el.disabled) return false;  /* trình duyệt không phát click vào nút tắt */
  el.dispatchEvent(dg.suKien('click', {}, el));
  return true;
}
function go(el, v) { el.value = v; el.dispatchEvent(dg.suKien('input', {}, el)); el.dispatchEvent(dg.suKien('change', {}, el)); }
function an(el) { return el.hidden !== undefined ? !!el.hidden : el.hasAttribute('hidden'); }
function chu(el) { return el ? String(el.textContent || '') : ''; }
function chon(el) { return el.getAttribute('aria-pressed') === 'true'; }

var ket = { dat: 0, hong: 0 };
function dung(mo, dk) { if (!dk) throw new Error(mo); }
function bang(mo, a, b) { var x = JSON.stringify(a), y = JSON.stringify(b); if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n        ') : e)); }
}

/* Đúng bộ khoá trang cũ đã gửi (#301), không thêm khoá mới. */
var KHOA_GUI = ['co_so', 'ngay', 'gio', 'so_khach', 'ten', 'sdt', 'ghi_chu', 'dip', 'khu_vuc', 'tre_em', 'email', 'banh_kem_theo'];

(async function () {
  console.log('v630 Trang khách Đặt bàn: dải ngày, số khách, giờ theo buổi, chỗ ngồi, liên hệ, gửi');

  await ca('mở trang: dải 14 ngày từ hôm nay, mặc định hôm nay, thông tin cửa hàng chỉ hiện nút có dữ liệu an toàn', async function () {
    var t = await dungTrang(cauHinh());
    dung('form hiện', t.tim('dat-ban').hidden === false);
    var ds = t.ngay();
    bang('14 ngày', ds.length, 14);
    bang('nhãn ba ngày đầu', ds.slice(0, 3).map(function (b) { return chu(b.children[0]) + '|' + chu(b.children[1]); }), ['Hôm nay|02', 'T3|03', 'T4|04']);
    bang('ngày cuối', ds[13].getAttribute('data-ngay'), '2026-11-15');
    bang('mặc định hôm nay', ds.filter(chon).map(function (b) { return b.getAttribute('data-ngay'); }), ['2026-11-02']);
    bang('tên cơ sở', chu(t.tim('co-so')), 'The Vagabond District 1');
    bang('giờ mở cửa', [an(t.tim('db-mo')), chu(t.tim('db-mo-chu')), chu(t.tim('db-mo-gio'))], [false, 'Đang mở cửa', ' · Hôm nay 9:00 - 21:00']);
    bang('nút liên hệ: Zalo không phải https thì ẩn', t.tim('db-lien').children.map(function (a) { return chu(a) + '>' + a.href; }),
      ['Chỉ đường>https://maps.app.goo.gl/abc', 'Gọi 0931 224 334>tel:0931224334']);
    bang('ảnh cơ sở', t.tim('db-anh').style.backgroundImage, 'url("/assets/vagabond/images/quay-tcv.jpg")');
    bang('dịp không có chip Không có dịp riêng', t.tim('dip').children.map(chu), DIP.slice(1));
    bang('khu vực: tên đậm, mô tả nhỏ', t.tim('khu-vuc').children.map(function (b) { return b.children.map(chu).join('|'); }),
      ['Bàn ghế cao|Cạnh quầy, hợp đi 2 người', 'Sofa thấp']);
    bang('giờ chia buổi', t.tim('gio').children.map(function (h) { return chu(h.children[0]) + ':' + h.children[1].children.map(chu).join(','); }),
      ['Sáng:09:00', 'Trưa:11:30', 'Chiều:14:00', 'Tối:18:00,18:30,21:00']);
  });

  await ca('giờ hôm nay đã qua hạn thì tắt, bấm không chọn được; sang ngày khác thì mở; quay lại hôm nay thì bỏ giờ đã qua', async function () {
    var t = await dungTrang(cauHinh());
    bang('tắt đúng ba giờ đã qua', ['09:00', '11:30', '14:00', '18:00'].map(function (k) { return t.gio(k).disabled; }), [true, true, true, false]);
    dung('bấm 14:00 không có tác dụng', !bam(t.gio('14:00')));
    bang('chưa chọn giờ', chu(t.tim('tom-tat')), 'Hôm nay 02/11 · Chưa chọn giờ · 2 khách');
    bam(t.ngay()[5]);
    bang('thứ Bảy mở mọi giờ', ['09:00', '14:00'].map(function (k) { return t.gio(k).disabled; }), [false, false]);
    bam(t.gio('09:00'));
    dung('chọn 09:00', chon(t.gio('09:00')));
    bang('tóm tắt', chu(t.tim('tom-tat')), 'Thứ Bảy 07/11 · 09:00 · 2 khách');
    bam(t.ngay()[0]);
    bang('về hôm nay: 09:00 bị bỏ', chu(t.tim('tom-tat')), 'Hôm nay 02/11 · Chưa chọn giờ · 2 khách');
    await t.guiForm();
    bang('không gửi khi chưa có giờ', t.gui.length, 0);
    dung('nhắc chọn giờ', chu(t.tim('trang-thai')).indexOf('Chọn giờ mong muốn') === 0 && t.tim('trang-thai').classList.contains('loi'));
  });

  await ca('hôm nay hết giờ nhận: ngày hôm nay tắt, mặc định ngày mai', async function () {
    var t = await dungTrang(cauHinh({ khung_gio_hom_nay: [] }));
    dung('hôm nay tắt', t.ngay()[0].disabled === true);
    bang('mặc định ngày mai', t.ngay().filter(chon).map(function (b) { return b.getAttribute('data-ngay'); }), ['2026-11-03']);
    bang('ngày mai không tắt giờ nào', t.tim('gio').querySelectorAll('[data-gio]').filter(function (b) { return b.disabled; }).length, 0);
  });

  await ca('số khách: nút cộng dừng ở mức tối đa, gõ quá thì kéo về tối đa, nút trừ dừng ở 1', async function () {
    var t = await dungTrang(cauHinh());
    bang('mặc định 2', t.tim('so-khach').value, '2');
    for (var i = 0; i < 6; i++) bam(t.tim('khach-them'));
    bang('dừng ở 6', t.tim('so-khach').value, '6');
    dung('nút cộng tắt', t.tim('khach-them').disabled === true);
    bang('câu gọi đặt tiệc', chu(t.tim('khach-goi')), 'Trên 6 khách, gọi 0931 224 334 để đặt tiệc riêng.');
    dung('câu gọi đổi màu khi chạm trần', t.tim('khach-goi').classList.contains('db-cham-tran'));
    go(t.tim('so-khach'), '40');
    bang('gõ 40 về 6', t.tim('so-khach').value, '6');
    for (i = 0; i < 9; i++) bam(t.tim('khach-bot'));
    bang('dừng ở 1', t.tim('so-khach').value, '1');
    dung('nút trừ tắt, nút cộng mở lại', t.tim('khach-bot').disabled === true && t.tim('khach-them').disabled === false);
    dung('bỏ màu trần', !t.tim('khach-goi').classList.contains('db-cham-tran'));
  });

  await ca('đủ bốn bước: tóm tắt, thanh dính đáy và đúng thân gửi máy chủ (đủ khoá cũ, không khoá mới)', async function () {
    var t = await dungTrang(cauHinh());
    bam(t.ngay()[5]);
    bam(t.tim('khach-them')); bam(t.tim('khach-them'));
    bam(t.gio('18:30'));
    bam(t.nut('khu-vuc', 'data-khu', 'Sofa thấp'));
    bam(t.nut('dip', 'data-dip', 'Kỷ niệm'));
    t.tim('ten').value = 'Nguyễn Minh Anh'; t.tim('sdt').value = '0909 123 123'; t.tim('ghi-chu').value = 'Góc yên tĩnh';
    bam(t.them('o-tre-em'));
    dung('mở ô trẻ em, bắt đầu 1', !an(t.tim('o-tre-em')) && t.tim('tre-em').value === '1' && t.them('o-tre-em').getAttribute('aria-expanded') === 'true');
    bam(t.tim('tre-them'));
    bam(t.them('o-banh')); t.tim('banh-kem-theo').value = '1 Entremet Pistachio 16cm';
    bam(t.them('o-email')); t.tim('email').value = 'minhanh@gmail.com';
    bang('tóm tắt máy tính', chu(t.tim('tom-tat')), 'Thứ Bảy 07/11 · 18:30 · 4 khách · Sofa thấp');
    bang('thanh dính đáy điện thoại', [chu(t.tim('tom-ngan-1')), chu(t.tim('tom-ngan-2'))], ['T7 07/11 · 18:30', '4 khách · Sofa thấp']);
    await t.guiForm();
    bang('một lần gửi', t.gui.length, 1);
    var b = JSON.parse(t.gui[0].body);
    bang('khoá lần gửi', b.ma_lan_gui, '11111111-2222-3333-4444-555555555555');
    bang('CSRF', t.gui[0].csrf, 'csrf-gia');
    bang('đúng bộ khoá cũ', Object.keys(b.du_lieu), KHOA_GUI);
    bang('thân gửi', b.du_lieu, { co_so: 'TCV', ngay: '2026-11-07', gio: '18:30', so_khach: 4, ten: 'Nguyễn Minh Anh', sdt: '0909 123 123',
      ghi_chu: 'Góc yên tĩnh', dip: 'Kỷ niệm', khu_vuc: 'Sofa thấp', tre_em: '2', email: 'minhanh@gmail.com', banh_kem_theo: '1 Entremet Pistachio 16cm' });
    dung('báo mã, ẩn form', chu(t.tim('trang-thai')).indexOf('Đã tiếp nhận yêu cầu ABCDEF123456') === 0 && t.tim('dat-ban').hidden === true);
  });

  await ca('ô gấp đã đóng thì gửi như để trống; bấm lại thẻ khu vực, chip dịp là bỏ chọn', async function () {
    var t = await dungTrang(cauHinh());
    bam(t.gio('21:00'));
    bam(t.nut('khu-vuc', 'data-khu', 'Sofa thấp')); bam(t.nut('khu-vuc', 'data-khu', 'Sofa thấp'));
    bam(t.nut('dip', 'data-dip', 'Hẹn hò')); bam(t.nut('dip', 'data-dip', 'Hẹn hò'));
    bam(t.them('o-email')); t.tim('email').value = 'nham@x.vn'; bam(t.them('o-email'));
    dung('ô email đóng lại', an(t.tim('o-email')));
    t.tim('ten').value = 'Lê Thu'; t.tim('sdt').value = '0987654321';
    await t.guiForm();
    var d = JSON.parse(t.gui[0].body).du_lieu;
    bang('để trống các ô chọn thêm', [d.ngay, d.gio, d.so_khach, d.dip, d.khu_vuc, d.tre_em, d.email, d.banh_kem_theo],
      ['2026-11-02', '21:00', 2, '', '', '0', '', '']);
  });

  await ca('số trẻ em không vượt số khách, bớt khách thì kéo trẻ em xuống theo', async function () {
    var t = await dungTrang(cauHinh());
    bam(t.tim('khach-them'));
    bam(t.them('o-tre-em'));
    for (var i = 0; i < 5; i++) bam(t.tim('tre-them'));
    bang('trẻ em dừng ở 3 khách', t.tim('tre-em').value, '3');
    dung('nút cộng trẻ em tắt', t.tim('tre-them').disabled === true);
    /* Nút cộng đã tắt nên chỉ đường gõ tay mới thử được phép kẹp (đột biến M6 lần đầu sót). */
    go(t.tim('tre-em'), '9');
    bang('gõ 9 trẻ em về 3', t.tim('tre-em').value, '3');
    bam(t.tim('khach-bot'));
    bang('bớt còn 2 khách thì 2 trẻ em', [t.tim('so-khach').value, t.tim('tre-em').value], ['2', '2']);
  });

  await ca('mất mạng: khoá mọi nút chọn, giữ nguyên yêu cầu, gửi lại đúng thân và khoá; máy chủ từ chối 4xx thì mở lại nhưng giờ đã qua vẫn tắt', async function () {
    var t = await dungTrang(cauHinh(), ['mat_mang', { status: 417, body: { _server_messages: JSON.stringify([JSON.stringify({ message: 'Đặt trước ít nhất 1 giờ.' })]) } }]);
    bam(t.gio('18:00'));
    t.tim('ten').value = 'Khách thử'; t.tim('sdt').value = '0912345678';
    await t.guiForm();
    dung('báo mất kết nối', chu(t.tim('trang-thai')).indexOf('Mất kết nối') === 0);
    bang('nút gửi lại', chu(t.tim('gui')), 'Gửi lại cùng yêu cầu');
    var khoa = [t.ngay()[3], t.gio('21:00'), t.tim('khach-them'), t.nut('dip', 'data-dip', 'Sinh nhật'), t.nut('khu-vuc', 'data-khu', 'Sofa thấp'), t.them('o-banh'), t.tim('ten')];
    bang('khoá hết', khoa.map(function (x) { return x.disabled; }), khoa.map(function () { return true; }));
    dung('bấm ngày khác không đổi', !bam(t.ngay()[3]));
    t.tim('ten').value = 'Đổi tên lén';
    await t.guiForm();
    bang('gửi lại đúng thân', t.gui[1].body, t.gui[0].body);
    dung('báo câu máy chủ', chu(t.tim('trang-thai')) === 'Đặt trước ít nhất 1 giờ.');
    bang('mở lại sau 4xx', [t.ngay()[3].disabled, t.gio('21:00').disabled, t.tim('khach-them').disabled, t.tim('ten').disabled], [false, false, false, false]);
    bang('giờ đã qua vẫn tắt', t.gio('09:00').disabled, true);
    bang('nút về chữ gốc', chu(t.tim('gui')), 'Gửi yêu cầu đặt bàn');
  });

  await ca('chưa mở nhận đặt bàn: hiện câu marketing, không hiện form; lỗi tải cấu hình: câu lỗi đỏ', async function () {
    var t = await dungTrang(cauHinh({ bat: false }));
    bang('câu đóng', chu(t.tim('trang-thai')), 'Tạm ngưng nhận đặt bàn online.');
    dung('form ẩn', an(t.tim('dat-ban')));
    var t2 = await dungTrang('loi');
    dung('câu lỗi', chu(t2.tim('trang-thai')).indexOf('Chưa tải được lịch') === 0 && t2.tim('trang-thai').classList.contains('loi'));
  });

  await ca('máy chủ chưa có giờ mở cửa và liên hệ: không hiện dòng Đang mở, không hiện nút nào', async function () {
    var c = cauHinh(); ['dang_mo', 'gio_hom_nay', 'hotline', 'hotline_so', 'chi_duong', 'zalo', 'khung_gio_hom_nay'].forEach(function (k) { delete c[k]; });
    var t = await dungTrang(c);
    dung('ẩn giờ mở', an(t.tim('db-mo')));
    dung('ẩn hàng nút', an(t.tim('db-lien')) && t.tim('db-lien').children.length === 0);
    bang('không có danh sách hôm nay thì không tắt giờ nào', t.tim('gio').querySelectorAll('[data-gio]').filter(function (b) { return b.disabled; }).length, 0);
  });

  console.log('\n' + ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng.');
  process.exit(ket.hong ? 1 : 0);
})();

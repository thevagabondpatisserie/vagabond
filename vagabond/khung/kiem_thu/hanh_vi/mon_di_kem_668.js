/* Ca kiểm HÀNH VI v668: màn Món đi kèm (78-mon-di-kem.js), Marketing duyệt cặp gợi ý.
 * Nạp THẬT 78-mon-di-kem.js cùng hàm nền vào DOM giả (khuôn của bai_dang_662.js).
 * Máy chủ giả trả đúng hình dạng goi_y_mua.man_hinh. Mỗi ca bấm đúng chuỗi thao tác.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/mon_di_kem_668.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
var NEN = doc('00-nen.js'), KHO = doc('03-kho-chung-tu.js'), CRM = doc('58-crm.js');
var MAN = doc('78-mon-di-kem.js');
function layHam(src, ten) {
  var dau = src.search(new RegExp('(?:async )?function ' + ten + '\\('));
  if (dau < 0) throw new Error('Khong thay ham ' + ten);
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Ham ' + ten + ' khong dong ngoac');
}
var HAM = ['h', 'money', 'anhMon'].map(function (t) { return layHam(NEN, t); }).concat([layHam(KHO, 'errMsg')])
  .concat(['crmMoSheet', 'crmCongTac', 'crmDatCongTac'].map(function (t) { return layHam(CRM, t); })).join('\n');
var P = 'vagabond.goi_y_mua.';
function manMau() {
  return { dem: { 'Nháp': 3, 'Đã duyệt': 1, 'Bỏ': 0 }, hom_nay: '2026-11-17', sua_cai_dat: 1,
    cai_dat: { bat_gio: true, bat_quay: true, bat_dbt: true, thanh_mien_phi: true, toi_da: 4, nguong: 3, nhom: ['Bánh khô', 'Bánh nướng'], kho_bep: ['Pastry - Thành phẩm - TV'], ly_do_nhom: [['Bánh khô', 'Giòn thơm', 'Crisp']] },
    cap: [{ name: 'c1', mon_goc: 'candle', mon_goi_y: 'BACF00028', ten_goi_y: 'Biscotti Cocoa', anh_goi_y: '/files/bis.jpg', ly_do_vn: 'Cacao đắng hợp sô cô la 70%', trang_thai: 'Nháp', uu_tien: 10 },
      { name: 'c2', mon_goc: 'candle', mon_goi_y: 'BANU00016', ten_goi_y: 'Triple Chocolatine', ly_do_vn: 'Ba lớp sô cô la', trang_thai: 'Nháp', uu_tien: 20, ghim_tu: '2026-11-17', ghim_den: '2026-11-30' },
      { name: 'c3', mon_goc: '', nhom_goc: 'Bánh lạnh', mon_goi_y: 'NUCF00007', ten_goi_y: 'Cà Phê Caramel Muối, Đá', ly_do_vn: 'Caramel muối hợp kem béo', trang_thai: 'Nháp', uu_tien: 10 }] };
}
function dungMoi(vai, traLoi) {
  var tai = dg.taiLieuGia();
  var goc = new dg.ElementGia('div');
  goc.parentNode = tai.body; tai.body.children.push(goc);
  var goi = [], toastDs = [], hoi = [];
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object, RegExp: RegExp, Promise: Promise,
    Number: Number, Date: Date, setTimeout: setTimeout, clearTimeout: clearTimeout, isNaN: isNaN, parseInt: parseInt, navigator: {},
    S: { roles: vai, stack: [1, 2], chuaLuu: '' }, frappe: { csrf_token: 'x' },
    hasRole: function (r) { return vai.indexOf(r) >= 0; },
    frame: function (t, html, opt) {
      opt = opt || {};
      goc.innerHTML = '<div class="vb" id="vgbBody">' + html + '</div>' + (opt.footer ? '<div class="vf">' + opt.footer + '</div>' : '') +
        (opt.action ? '<button id="vgbAct">' + opt.action + '</button>' : '');
      that._t = t;
      return goc.querySelector('#vgbBody');
    },
    go: function (fn) { return fn(); },
    back: function () { that._lui = (that._lui || 0) + 1; },
    busy: function () {},
    vgbBoChuaLuu: function () { that.S.chuaLuu = ''; },
    toast: function (m) { toastDs.push(m); },
    confirmSheet: function (t, m) { hoi.push(t + '|' + m); return Promise.resolve(that._dongY !== false); },
    /* Hộp nhập chữ giả: chạy đúng hàm kiem của màn như hộp thật; người dùng "dán" that._link. */
    hoiChu: function (t, m, md, o) {
      hoi.push(t + '|' + m + '|' + ((o || {}).nut || ''));
      if (that._dongY === false) return Promise.resolve(null);
      var v = that._link || '';
      var sai = o && o.kiem ? o.kiem(v) : '';
      if (sai) { that._loiHop = sai; return Promise.resolve(null); }
      return Promise.resolve(v);
    },
    /* Ô chọn giả (QT-31): ghi lại lựa chọn được bày, trả lời theo hàng đợi that._tra. */
    hoiChon: function (t, m, lc, dang) { that._bay = { t: t, lc: lc, dang: dang }; return Promise.resolve((that._tra || []).shift() || null); },
    hoiChonNhieu: function (t, m, lc, dang) { that._bay = { t: t, lc: lc, dang: dang }; return Promise.resolve((that._tra || []).shift() || null); },
    vgbChonMon: function (o) { that._bayMon = o; return Promise.resolve((that._tra || []).shift() || []); },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: ts });
      var f = (traLoi || {})[duong.replace(P, '')];
      if (typeof f === 'function') { try { return Promise.resolve(f(ts)); } catch (e) { return Promise.reject(e); } }
      if (f !== undefined) return Promise.resolve(JSON.parse(JSON.stringify(f)));
      return Promise.resolve({});
    }
  };
  that.window = that;
  vm.runInNewContext(HAM, that, { filename: 'ham-nen.js' });
  vm.runInNewContext(MAN, that, { filename: '78-mon-di-kem.js' });
  return { g: that, tai: tai, goc: goc, goi: goi, toast: toastDs, hoi: hoi };
}

var ket = { dat: 0, hong: 0 };
function dung(mo, dk) { if (!dk) throw new Error(mo); }
function bang(mo, a, b) { var x = JSON.stringify(a), y = JSON.stringify(b); if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y); }
function cho(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
async function choDen(dk) { for (var i = 0; i < 150 && !dk(); i++) await cho(10); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); }
}
function chu(el) { var s = el._chu || ''; (el.children || []).forEach(function (c) { s += chu(c); }); return s; }
function sheet(m) { var ds = m.tai.body.children; return ds.length > 1 ? ds[ds.length - 1] : null; }
function bam(m, el) { if (!el) throw new Error('khong co nut de bam'); el.dispatchEvent(dg.suKien('click', {}, el)); }
function go(m, el, gt) { el.value = gt; el.dispatchEvent(dg.suKien('input', {}, el)); }
function goiTen(m, t) { return m.goi.filter(function (x) { return x.duong === P + t; }); }
function mot(el, chon) { return el.querySelectorAll(chon)[0]; }
var MKT = ['Marketing'];

(async function () {
  console.log('v668 Món đi kèm');

  await ca('xem theo món gốc: hai nhóm (candle, Nhóm Bánh lạnh), câu lý do màu xanh, dòng ghim có ngày; không hiện mã nội bộ trạng thái', async function () {
    var m = dungMoi(MKT, { man_hinh: manMau() });
    await m.g.scrMonDiKem();
    bang('tiêu đề', m.g._t, 'Món đi kèm');
    var c = chu(m.goc);
    dung('nhóm candle', c.indexOf('candle') >= 0 && c.indexOf('Nhóm Bánh lạnh') >= 0);
    dung('câu lý do', c.indexOf('Cacao đắng hợp sô cô la 70%') >= 0);
    dung('ghim', c.indexOf('17/11') >= 0 && c.indexOf('30/11') >= 0);
    dung('chip chờ duyệt có số', c.indexOf('Chờ duyệt') >= 0);
    bang('hỏi máy chủ đúng mục', goiTen(m, 'man_hinh')[0].ts, { trang_thai: 'Nháp', tim: '' });
    /* Codex #584 (AGENTS.md 2b.4): tên món nào cũng có ảnh, chưa có ảnh thì ô bánh. */
    dung('dòng có ảnh món', m.goc.querySelectorAll('img').some(function (x) { return x.getAttribute('src') === '/files/bis.jpg'; }));
    bang('dòng chưa có ảnh dùng ô bánh', m.goc.querySelectorAll('.immp').length, 2);
  });

  await ca('chọn nhiều dòng (Chọn cả món + một dòng) rồi Duyệt 3 dòng: gửi MỘT lần đúng ba dòng, chọn dòng không hỏi lại máy chủ', async function () {
    var m = dungMoi(MKT, { man_hinh: manMau(), doi_nhieu: { ok: 1, doi: 3 } });
    await m.g.scrMonDiKem();
    bam(m, mot(m.goc, '[data-mdkchonnhom="candle"]'));
    bam(m, mot(m.goc, '[data-mdkchon="c3"]'));
    bang('chọn dòng không gọi lại máy chủ', goiTen(m, 'man_hinh').length, 1);
    var n = mot(m.goc, '[data-mdkdoi="Đã duyệt"]');
    dung('nút ghi số dòng', chu(n).indexOf('Duyệt 3 dòng') >= 0);
    bam(m, n);
    await choDen(function () { return goiTen(m, 'doi_nhieu').length === 1; });
    var ts = goiTen(m, 'doi_nhieu')[0].ts;
    bang('gửi đúng ba dòng, đúng trạng thái', [JSON.parse(ts.ten).sort(), ts.trang_thai], [['c1', 'c2', 'c3'], 'Đã duyệt']);
    await choDen(function () { return m.toast.length > 0; });
    dung('báo kết quả', m.toast[0].indexOf('Đã chuyển 3 dòng sang Đã duyệt') >= 0);
  });

  await ca('sửa câu một dòng: mở hộp, sửa câu, Lưu và duyệt gửi đúng dòng, đúng trạng thái', async function () {
    var m = dungMoi(MKT, { man_hinh: manMau(), luu_cap: { ok: 1, name: 'c1' } });
    await m.g.scrMonDiKem();
    bam(m, mot(m.goc, '[data-mdksua="c1"]'));
    var sh = sheet(m);
    dung('có hộp sửa', !!sh);
    dung('hộp sửa có ảnh món', sh.querySelectorAll('img').some(function (x) { return x.getAttribute('src') === '/files/bis.jpg'; }));
    mot(sh, '#mdkVn').value = 'Cacao hợp sô cô la';
    bam(m, mot(sh, '[data-mdkluu="Đã duyệt"]'));
    await choDen(function () { return goiTen(m, 'luu_cap').length === 1; });
    var d = JSON.parse(goiTen(m, 'luu_cap')[0].ts.du_lieu);
    bang('dữ liệu lưu', [d.name, d.ly_do_vn, d.trang_thai, d.ghim_tu], ['c1', 'Cacao hợp sô cô la', 'Đã duyệt', '']);
  });

  await ca('Cài đặt: công tắc và ô số, Lưu cài đặt gửi đủ; Mức giữ: món dưới mức hiện đỏ, đặt mức gửi đúng món', async function () {
    var m = dungMoi(MKT, { man_hinh: manMau(), luu_cai_dat: { ok: 1 }, duoi_muc_giu: { mon: [{ ma: 'BACF00034', ten: 'Canelé Tahitian Vanilla', anh: '/files/can.jpg', muc: 20, ton: 12 }], co_muc: 3 }, dat_muc_giu: { ok: 1 } });
    m.g.MDK.phan = 'cd';
    await m.g.scrMonDiKem();
    bam(m, mot(m.goc, '[data-mdkbat="bat_quay"]'));
    m.goc.querySelector('#mdkToiDa').value = '5';
    bam(m, mot(m.goc, '#mdkLuuCd'));
    await choDen(function () { return goiTen(m, 'luu_cai_dat').length === 1; });
    var d = JSON.parse(goiTen(m, 'luu_cai_dat')[0].ts.du_lieu);
    bang('cài đặt gửi', [d.bat_quay, d.bat_gio, d.toi_da, d.nhom], [0, 1, '5', ['Bánh khô', 'Bánh nướng']]);
    m.g.MDK.phan = 'muc';
    await m.g.scrMonDiKem();
    await choDen(function () { return chu(m.goc).indexOf('Canelé') >= 0; });
    dung('món dưới mức', chu(m.goc).indexOf('Tồn bếp 12, mức giữ 20') >= 0);
    dung('món dưới mức có ảnh', m.goc.querySelectorAll('img').some(function (x) { return x.getAttribute('src') === '/files/can.jpg'; }));
    dung('không còn ô gõ mã món', !m.goc.querySelector('#mdkMucMa'));
    m.goc.querySelector('#mdkMucSo').value = '25';
    bam(m, mot(m.goc, '#mdkMucLuu'));
    await choDen(function () { return m.toast.length > 0; });
    dung('chưa chọn món thì nhắc, không gửi', m.toast[m.toast.length - 1].indexOf('Chọn món') === 0 && !goiTen(m, 'dat_muc_giu').length);
    m.g._tra = [[{ ma: 'BACF00034', ten: 'Canelé Tahitian Vanilla' }]];
    bam(m, mot(m.goc, '[data-mdkmucchon]'));
    await choDen(function () { return chu(m.goc).indexOf('Canelé Tahitian Vanilla') >= 0 && !!m.goc.querySelector('#mdkMucChon [data-mdkmucchon]'); });
    bam(m, mot(m.goc, '#mdkMucLuu'));
    await choDen(function () { return goiTen(m, 'dat_muc_giu').length === 1; });
    bang('đặt mức', goiTen(m, 'dat_muc_giu')[0].ts, { ma: 'BACF00034', so: '25' });
  });

  await ca('Codex #581 thêm cặp: bánh gốc, nhóm, món gợi ý CHỌN từ danh mục (không ô gõ); chưa chọn thì nhắc; lưu gửi đúng khoá bánh và mã món', async function () {
    var dm = { banh: [{ k: 'candle', nhan: 'Candle' }], nhom: ['Bánh lạnh'], kho: ['Pastry - Thành phẩm - TV'], nhom_rieng: ['Bánh trên tủ'] };
    var m = dungMoi(MKT, { man_hinh: manMau(), danh_muc: dm, luu_cap: { ok: 1, name: 'c9' } });
    await m.g.scrMonDiKem();
    bam(m, mot(m.goc, '[data-mdkmoi]'));
    var sh = sheet(m);
    dung('không còn ô gõ bánh, nhóm, mã', !sh.querySelector('#mdkGoc') && !sh.querySelector('#mdkNhom') && !sh.querySelector('#mdkMa'));
    bam(m, mot(sh, '[data-mdkluu="Đã duyệt"]'));
    await choDen(function () { return m.toast.length > 0; });
    dung('chưa chọn thì nhắc', m.toast[0].indexOf('Chọn bánh gốc') === 0 && !goiTen(m, 'luu_cap').length);
    m.g._tra = ['b:candle'];
    bam(m, mot(sh, '[data-mdkchongoc]'));
    await choDen(function () { return chu(sh).indexOf('Candle') >= 0; });
    bang('bày cả bánh trên web lẫn nhóm món', m.g._bay.lc.map(function (x) { return x.k; }), ['b:candle', 'n:Bánh lạnh']);
    bam(m, mot(sh, '[data-mdkluu="Đã duyệt"]'));
    await choDen(function () { return m.toast.length > 1; });
    dung('có bánh gốc mà chưa chọn món gợi ý thì nhắc', m.toast[1].indexOf('Chọn món gợi ý') === 0 && !goiTen(m, 'luu_cap').length);
    m.g._tra = [[{ ma: 'BACF00034', ten: 'Canelé Tahitian Vanilla' }]];
    bam(m, mot(sh, '[data-mdkchonma]'));
    await choDen(function () { return chu(sh).indexOf('Canelé Tahitian Vanilla') >= 0; });
    dung('mở bảng chọn món một món', m.g._bayMon.nhieu === false);
    bam(m, mot(sh, '[data-mdkluu="Đã duyệt"]'));
    await choDen(function () { return goiTen(m, 'luu_cap').length === 1; });
    var d = JSON.parse(goiTen(m, 'luu_cap')[0].ts.du_lieu);
    bang('lưu đúng khoá', [d.mon_goc, d.nhom_goc, d.mon_goi_y, d.trang_thai], ['candle', '', 'BACF00034', 'Đã duyệt']);
  });

  await ca('Codex #581 Cài đặt: nhóm, kho chọn nhiều từ danh mục; câu lý do theo nhóm có nút Thêm câu cho nhóm; câu đang gõ không mất khi vẽ lại; lưu gửi danh sách', async function () {
    var dm = { banh: [], nhom: ['Bánh khô', 'Bánh lạnh'], kho: ['Pastry - Thành phẩm - TV', 'Baker - Thành phẩm - TV'], nhom_rieng: ['Bánh trên tủ'] };
    var m = dungMoi(MKT, { man_hinh: manMau(), danh_muc: dm, luu_cai_dat: { ok: 1 } });
    m.g.MDK.phan = 'cd';
    await m.g.scrMonDiKem();
    dung('không còn ô gõ nhóm, kho, câu theo nhóm', !m.goc.querySelector('#mdkNhomGy') && !m.goc.querySelector('#mdkKho') && !m.goc.querySelector('#mdkLy'));
    m.goc.querySelector('[data-mdklyvn="0"]').value = 'Giòn tan';
    m.g._tra = [['Bánh khô', 'Bánh lạnh']];
    bam(m, mot(m.goc, '[data-mdkchonnhomgy]'));
    await choDen(function () { return chu(m.goc).indexOf('Bánh khô, Bánh lạnh') >= 0; });
    bang('đánh dấu sẵn nhóm đang dùng', m.g._bay.dang, ['Bánh khô', 'Bánh nướng']);
    bang('câu đang gõ còn nguyên', m.goc.querySelector('[data-mdklyvn="0"]').value, 'Giòn tan');
    m.g._tra = [['Baker - Thành phẩm - TV']];
    bam(m, mot(m.goc, '[data-mdkchonkho]'));
    await choDen(function () { return chu(m.goc).indexOf('Baker - Thành phẩm - TV') >= 0; });
    m.g._tra = ['Bánh trên tủ'];
    bam(m, mot(m.goc, '[data-mdklythem]'));
    await choDen(function () { return !!m.goc.querySelector('[data-mdklyvn="1"]'); });
    dung('không bày lại nhóm đã có câu', m.g._bay.lc.map(function (x) { return x.k; }).indexOf('Bánh khô') < 0);
    m.goc.querySelector('[data-mdklyvn="1"]').value = 'Còn trên tủ hôm nay';
    bam(m, mot(m.goc, '#mdkLuuCd'));
    await choDen(function () { return goiTen(m, 'luu_cai_dat').length === 1; });
    var d = JSON.parse(goiTen(m, 'luu_cai_dat')[0].ts.du_lieu);
    bang('gửi danh sách', [d.nhom, d.kho_bep, d.ly_do_nhom], [['Bánh khô', 'Bánh lạnh'], ['Baker - Thành phẩm - TV'], [['Bánh khô', 'Giòn tan', 'Crisp'], ['Bánh trên tủ', 'Còn trên tủ hôm nay', '']]]);
  });

  await ca('Kết quả: tỉ lệ, giá trị trung bình, món thêm nhiều nhất từ báo cáo máy chủ', async function () {
    var m = dungMoi(MKT, { bao_cao_goi_y: { so_don: 40, don_co_goi_y: 10, ti_le: 25, gia_tri_tb: 820000, gia_tri_tb_co_goi_y: 990000, mon: [{ ma: 'A', ten: 'Canelé', anh: '/files/a.jpg', sl: 7 }] } });
    m.g.MDK.phan = 'kq';
    await m.g.scrMonDiKem();
    await choDen(function () { return chu(m.goc).indexOf('Canelé') >= 0; });
    var c = chu(m.goc);
    dung('số liệu', c.indexOf('25%') >= 0 && c.indexOf('10/40') >= 0 && c.indexOf('990.000') >= 0);
    dung('món thêm nhiều nhất có ảnh', m.goc.querySelectorAll('img').some(function (x) { return x.getAttribute('src') === '/files/a.jpg'; }));
  });

  console.log('\n' + ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng.');
  process.exit(ket.hong ? 1 : 0);
})();

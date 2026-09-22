/* Bo ca kiem HANH VI: thanh bao thuong truc tren man Hoa don mua hang (Desk).
 *
 * Codex #352 (22/09/2026): loi dung phieu mua chi hien trong hop ket qua luc
 * bam dong bo, dong hop la mat. Nay mo man danh sach Hoa don mua hang la
 * thay ngay: bao nhieu to dau vao chua thanh phieu, chia theo viec phai lam,
 * bam "Xem danh sach" ra bang tung to kem nut mo ban nguon.
 *
 * Nap THAT minvoice_list.js voi frappe gia, goi onload cua danh sach nhu
 * Frappe goi khi mo man. Khong goi them ham noi bo nao.
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/cho_dung_352.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var SRC = fs.readFileSync(path.join(GOC, 'vagabond', 'public', 'js', 'minvoice_list.js'), 'utf8');

function kqMau() {
  return {
    so_to: 3, tong_tien: 1290000, tu_ngay: '2026-03-26', den_ngay: '2026-09-22',
    theo_nhom: [{ nhom: 'quy_cach', ten: 'Cần khai quy cách mua', so_to: 2, tien: 1190000 },
      { nhom: 'khac', ten: 'Cần xem lý do', so_to: 1, tien: 100000 }],
    ds: [
      { ma: 'MI-3', ky_hieu: 'C26TAA', so_hd: '9', ngay_lap: '2026-09-01', ncc: 'NCC <b>đậm</b>', tong_tien: 100000, nhom: 'khac', ten_nhom: 'Cần xem lý do', ly_do: 'Lỗi lạ' },
      { ma: 'MI-1', ky_hieu: 'C26TMB', so_hd: '5310710', ngay_lap: '2026-09-10', ncc: 'MOBIFONE THÀNH PHỐ HỒ CHÍ MINH 1', tong_tien: 159000, nhom: 'quy_cach', ten_nhom: 'Cần khai quy cách mua', ly_do: "Món DVTI00014: chưa xác định được quy đổi đơn vị nhà cung cấp 'Lần' sang Set." },
      { ma: 'MI 2/x', ky_hieu: '', so_hd: '', ngay_lap: '2026-09-12', ncc: 'Duy Lợi', tong_tien: 1031000, nhom: 'quy_cach', ten_nhom: 'Cần khai quy cách mua', ly_do: '' },
    ],
  };
}

function dung(canh) {
  canh = canh || {};
  var tai = dg.taiLieuGia();
  var main = new dg.ElementGia('div');
  main.appendChild(new dg.ElementGia('div'));  // phan danh sach co san cua Frappe
  var goi = [], msg = [], nut = [];
  var frappe = {
    listview_settings: {},
    user_roles: canh.vai || ['Accounts User'],
    utils: { escape_html: function (s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); } },
    datetime: { get_today: function () { return '2026-09-22'; } },
    call: function (o) {
      goi.push(o.method);
      if (o.method !== 'vagabond.minvoice_chung_tu.cho_dung_phieu_mua') return;
      var k = (canh.lan || [])[goi.length - 1] || canh.kieu || 'dat';
      /* Nhu frappe.call that: may chu loi, het phien, mat mang goi `error`,
         khong goi callback; r.exc la loi tra ve trong than. */
      if (k === 'loi') return o.error && o.error({});
      if (k === 'exc') return o.callback({ exc: 'Traceback' });
      o.callback({ message: canh.kq === undefined ? kqMau() : canh.kq });
    },
    msgprint: function (o) { msg.push(o); },
  };
  var ctx = { frappe: frappe, document: tai, console: console, cur_list: null };
  vm.createContext(ctx);
  vm.runInContext(SRC, ctx, { filename: 'minvoice_list.js' });
  var lv = {
    doctype: canh.dt || 'Purchase Invoice',
    page: { main: { get: function () { return main; } }, add_inner_button: function (t, f) { nut.push([t, f]); } },
  };
  frappe.listview_settings[lv.doctype].onload(lv);
  return { main: main, goi: goi, msg: msg, nut: nut, moLai: function () { frappe.listview_settings[lv.doctype].onload(lv); } };
}

var ket = { dat: 0, hong: 0, loi: [] };
function dungDk(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) { if (a !== b) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
function ca(ten, ham) {
  try { ham(); ket.dat++; }
  catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n         ') : String(e))); }
}

ca('mo man Hoa don mua hang: thanh bao nam DAU man, dem so to, tong tien va chia theo viec', function () {
  var m = dung();
  var thanh = m.main.firstChild;
  bang('thanh nam dau man', thanh.getAttribute('class'), 'vgb-thanh-cho');
  var html = thanh.innerHTML;
  dungDk('dem so to', html.indexOf('<b>3 hoá đơn đầu vào đã nhận nhưng chưa thành phiếu mua</b>') >= 0);
  dungDk('chia theo viec', html.indexOf('Cần khai quy cách mua: <b>2</b>') >= 0 && html.indexOf('Cần xem lý do: <b>1</b>') >= 0);
  bang('van con nut dong bo', m.nut[0][0], 'Đồng bộ M-Invoice');
});

ca('bam Xem danh sach: bang tung to, xep theo viec, co nut mo ban nguon, chu nguon duoc thoat HTML', function () {
  var m = dung();
  m.main.firstChild.querySelector('[data-vgb-xem-cho]').onclick();
  bang('mo mot hop', m.msg.length, 1);
  var h = m.msg[0].message;
  dungDk('hai to quy cach dung truoc to ly do khac', h.indexOf('5310710') < h.indexOf('C26TAA'));
  dungDk('to chua co so thi noi ro', h.indexOf('(chưa có số)') >= 0);
  dungDk('mo ban nguon dung ban ghi, ma duoc ma hoa', h.indexOf('href="/app/minvoice-invoice/MI%202%2Fx"') >= 0);
  dungDk('ten NCC khong chen duoc the HTML', h.indexOf('NCC &lt;b&gt;đậm&lt;/b&gt;') >= 0 && h.indexOf('NCC <b>') < 0);
  dungDk('co ly do goc', h.indexOf("quy đổi đơn vị nhà cung cấp 'Lần'") >= 0);
});

ca('khong con to nao cho: khong hien thanh', function () {
  var m = dung({ kq: { so_to: 0, ds: [], theo_nhom: [] } });
  bang('chi con phan danh sach cua Frappe', m.main.children.length, 1);
});

ca('mo lai man: thay thanh cu, khong chong hai thanh', function () {
  var m = dung();
  m.moLai();
  bang('goi cua hai lan', m.goi.length, 2);
  bang('mot thanh', m.main.querySelectorAll('.vgb-thanh-cho').length, 1);
});

ca('nguoi khong co vai ke toan: khong goi cua, khong hien thanh', function () {
  var m = dung({ vai: ['Stock User'] });
  bang('khong goi may chu', m.goi.length, 0);
  bang('khong thanh', m.main.children.length, 1);
});

ca('man Hoa don ban ra: khong hien thanh dau vao', function () {
  var m = dung({ dt: 'Sales Invoice' });
  bang('khong goi cua dau vao', m.goi.indexOf('vagabond.minvoice_chung_tu.cho_dung_phieu_mua'), -1);
});

ca('Codex #357: may chu loi thi hien thanh DO kem Thu lai, khong trong nhu khi da sach', function () {
  var m = dung({ kieu: 'loi' });
  var thanh = m.main.firstChild;
  bang('co thanh', thanh.getAttribute('class'), 'vgb-thanh-cho');
  bang('kieu loi', thanh.getAttribute('data-kieu'), 'loi');
  dungDk('noi ro chua kiem duoc', thanh.innerHTML.indexOf('Chưa tải được danh sách') >= 0);
  var m2 = dung({ kieu: 'exc' });
  bang('loi trong than cung la loi', m2.main.firstChild.getAttribute('data-kieu'), 'loi');
});

ca('Codex #357: tai lai hong thi KHONG giu so cu; bam Thu lai goi lai va hien so moi', function () {
  var m = dung({ lan: ['dat', 'loi', 'dat'] });
  dungDk('lan 1 co so', m.main.firstChild.innerHTML.indexOf('<b>3 hoá đơn') >= 0);
  m.moLai();
  bang('lan 2 hong: thanh loi thay the', m.main.querySelectorAll('.vgb-thanh-cho').length, 1);
  dungDk('khong con so cu', m.main.firstChild.innerHTML.indexOf('<b>3 hoá đơn') < 0);
  bang('thanh la thanh loi', m.main.firstChild.getAttribute('data-kieu'), 'loi');
  m.main.firstChild.querySelector('[data-vgb-thu-lai]').onclick();
  bang('Thu lai goi may chu lan ba', m.goi.length, 3);
  bang('lai co so', m.main.firstChild.getAttribute('data-kieu'), 'cho');
});

console.log('Bo ca kiem HANH VI thanh bao hoa don dau vao chua thanh phieu mua (#352)');
ket.loi.forEach(function (d) { console.log('  HONG  ' + d); });
console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
process.exit(ket.hong ? 1 : 0);

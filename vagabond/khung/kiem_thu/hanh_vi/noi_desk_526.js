/* Bo ca kiem HANH VI v526 vong 3 (Codex #368, c1674cf): nut "Noi vao ho so
 * chi (hoa don den sau)" tren man Hoa don mua ben Desk.
 *
 * Nha cung cap co nhieu khoan cho hoa don (may chu tra toi 50) thi o chon
 * phai TIM DUOC, va gia tri chon phai mang dung dinh danh khoan (ho so +
 * so khoan), khong phai so thu tu trong danh sach.
 *
 * Nap THAT vgbHoaDonDenSau tu purchase_invoice.js; chi thay frappe, frm.
 * Chay: node vagabond/khung/kiem_thu/hanh_vi/noi_desk_526.js
 */
'use strict';
var fs = require('fs');
var path = require('path');
var vm = require('vm');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var SRC = fs.readFileSync(path.join(GOC, 'vagabond', 'public', 'js', 'purchase_invoice.js'), 'utf8');

function layHam(src, ten) {
  var dau = src.indexOf('function ' + ten + '(');
  if (dau < 0) throw new Error('Khong thay ham ' + ten);
  if (src.slice(Math.max(0, dau - 6), dau) === 'async ') dau -= 6;
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Ham ' + ten + ' khong dong ngoac');
}
function layBien(src, ten) {
  var m = new RegExp('var ' + ten + ' = [^;]*;').exec(src);
  if (!m) throw new Error('Khong thay bien ' + ten);
  return m[0];
}

var ket = { dat: 0, hong: 0, loi: [] };
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
function dung(mo, x) { if (!x) throw new Error(mo); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; }
  catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n         ') : String(e))); }
}

/* 12 khoan cho: hai ho so, noi dung giong nhau (Xang), so tien giong nhau. */
function khoan() {
  var ra = [];
  for (var i = 0; i < 12; i++) {
    ra.push({ ho_so: 'APP-26-09-' + (100 + (i % 2)), dong: i + 1, noi_dung: 'Xăng', so_tien: 80000, ngay: '2026-09-2' + (i % 9), ngay_hd: '' });
  }
  return ra;
}

function dung_man() {
  var goi = [], hop = null, nut = null;
  var g = {
    Number: Number, String: String, Object: Object, JSON: JSON, Array: Array,
    format_currency: function (n) { return String(n) + ' ₫'; },
    frappe: {
      user: { has_role: function () { return true; } },
      utils: { escape_html: function (s) { return String(s); } },
      show_alert: function () {}, msgprint: function (m) { goi.push({ msg: m }); },
      call: async function (o) {
        goi.push(o);
        if (o.method === 'vagabond.ho_so_bo_sung.khoan_cho_hoa_don') return { message: { da_noi: '', khoan: khoan() } };
        return { message: { ok: 1, hop_le: 0 } };
      },
      ui: { Dialog: function (cau) { hop = this; this.cau = cau; this.gia = {};
        this.show = function () {}; this.hide = function () {};
        this.set_value = function (k, v) { this.gia[k] = v; };
        this.get_value = function (k) { return this.gia[k]; }; } }
    }
  };
  var frm = { doc: { name: 'HDM-26-09-00400', docstatus: 0 }, is_new: function () { return false; },
    dashboard: { add_comment: function () {} }, reload_doc: function () {},
    add_custom_button: function (t, fn) { nut = fn; } };
  vm.createContext(g);
  vm.runInContext(layBien(SRC, 'VGB_VAI_NOI_HD_SAU') + '\n' + layHam(SRC, 'vgbHoaDonDenSau'), g);
  return { g: g, frm: frm, goi: goi, hop: function () { return hop; }, nut: function () { return nut; } };
}

(async function () {
  await ca('12 khoan cho: o chon khoan TIM DUOC (khong phai Select cuon tay)', async function () {
    var m = dung_man();
    await m.g.vgbHoaDonDenSau(m.frm);
    m.nut()();
    var o = m.hop().cau.fields.filter(function (f) { return f.fieldname === 'khoan'; })[0];
    dung('co o khoan', o);
    bang('o chon tim duoc', o.fieldtype, 'Autocomplete');
    bang('du 12 lua chon', o.options.length, 12);
  });

  await ca('gia tri chon mang dinh danh ho so + so khoan; noi dung khoan da chon, khong lech dong', async function () {
    var m = dung_man();
    await m.g.vgbHoaDonDenSau(m.frm);
    m.nut()();
    var o = m.hop().cau.fields.filter(function (f) { return f.fieldname === 'khoan'; })[0];
    var chon = o.options[7];
    var gt = typeof chon === 'string' ? chon : chon.value;
    dung('gia tri co ten ho so', gt.indexOf('APP-26-09-101') >= 0);
    dung('gia tri co so khoan', gt.indexOf('khoản 8') >= 0);
    await m.hop().cau.primary_action({ khoan: gt });
    var noi = m.goi.filter(function (x) { return x.method === 'vagabond.ho_so_bo_sung.noi_hoa_don'; });
    bang('noi mot lan', noi.length, 1);
    bang('dung ho so, dung khoan', [noi[0].args.name, noi[0].args.dong], ['APP-26-09-101', 8]);
  });

  await ca('khong chon san khoan dau tien; gia tri go tay khong khop thi khong noi', async function () {
    var m = dung_man();
    await m.g.vgbHoaDonDenSau(m.frm);
    m.nut()();
    bang('khong dat san gia tri', m.hop().gia.khoan, undefined);
    await m.hop().cau.primary_action({ khoan: 'APP-26-09-100' });
    bang('khong noi', m.goi.filter(function (x) { return x.method === 'vagabond.ho_so_bo_sung.noi_hoa_don'; }).length, 0);
  });

  console.log('Bo ca kiem HANH VI nut noi hoa don den sau tren Desk (v526 vong 3)');
  ket.loi.forEach(function (d) { console.log('  HONG  ' + d); });
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
})();

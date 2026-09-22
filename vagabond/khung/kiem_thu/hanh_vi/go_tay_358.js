/* Bo ca kiem HANH VI #358: may goi y, nguoi chot Mon va he so.
 *
 * Anh Viet 22/09/2026: "staff da nhap mon, nhap don vi thi may ghi luon vao
 * thong tin cua Mon de sau nay chi viec map cho nhanh". Truoc ban nay nut gan
 * ma gan tam he so 1 khi Mon chua khai don vi nha cung cap ghi.
 *
 * Nap THAT dcmGanXong (app, 18-doi-chieu-may-in.js) va vgbGanMonDesk (Desk,
 * purchase_invoice.js). May chu gia tra dung khuon gan_ma_hang: lan dau
 * `can_he_so`, lan sau (co he_so) thi gan. Ca kiem chi bam nhu nguoi dung.
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/go_tay_358.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var APP = fs.readFileSync(path.join(GOC, 'vagabond', 'public', 'js', 'bep', '18-doi-chieu-may-in.js'), 'utf8');
var DESK = fs.readFileSync(path.join(GOC, 'vagabond', 'public', 'js', 'purchase_invoice.js'), 'utf8');

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

var ket = { dat: 0, hong: 0, loi: [] };
function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; }
  catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n         ') : String(e))); }
}

/* May chu gia dung khuon gan_ma_hang #358. */
function mayChu() {
  var goi = [];
  return {
    goi: goi,
    api: async function (m, a) {
      goi.push({ m: m, a: JSON.parse(JSON.stringify(a)) });
      if (m.endsWith('gan_ma_hang')) {
        /* Chan vong lap: may khach quen gui he so thi hoi mai. Ca kiem phai
           HONG ro rang, khong treo may (dot bien M5 ngay 22/09). */
        if (goi.filter(function (x) { return x.m.endsWith('gan_ma_hang'); }).length > 3) throw new Error('goi gan_ma_hang qua 3 lan: he so khong duoc gui len');
        if (!a.he_so) return { can_he_so: 1, dvt_ncc: 'Lần', dvt_kho: 'Set', de_xuat: 1, item_code: a.item_code };
        return { item_code: a.item_code, dvt: 'Lần', he_so: a.he_so, loi_nhan: 'Đã gắn món cho dòng 3.' };
      }
      if (m.endsWith('goi_y_mon')) return { goi_y: [{ item_code: 'DVTI00014', item_name: 'Phí dịch vụ', vi_sao: 'Máy đoán: nhà cung cấp này từng gửi đúng tên hàng này' }] };
      return {};
    },
  };
}

function appMoi(canh) {
  var mc = mayChu(), hoi = [], tai = 0, bao = [];
  var g = {
    money: String, kl: String, busy: function () {}, toast: function () {}, go: function () { tai++; },
    baoTin: function (s) { bao.push(s); }, parseFloat: parseFloat, Number: Number,
    qtySheet: async function (t, nhan, deXuat, dvt) { hoi.push({ t: t, nhan: nhan, deXuat: deXuat, dvt: dvt }); return canh.go; },
    api: mc.api,
  };
  vm.createContext(g);
  vm.runInContext(layHam(APP, 'dcmDoiMaTheoNguon') + '\n' + layHam(APP, 'dcmGanXong'), g);
  return { g: g, goi: mc.goi, hoi: hoi, tai: function () { return tai; }, bao: bao };
}

async function chayHet() {
  await ca('app: Mon chua khai don vi thi HOI he so, gui lai kem he so; khong luu gi truoc khi nguoi go', async function () {
    var m = appMoi({ go: 1 });
    await m.g.dcmGanXong('HDM-1', 3, 'DVTI00014');
    bang('hai lan goi gan', m.goi.filter(function (x) { return x.m.endsWith('gan_ma_hang'); }).length, 2);
    bang('lan dau khong he so', m.goi[0].a.he_so, undefined);
    bang('lan hai mang he so nguoi go', m.goi[1].a.he_so, 1);
    bang('hoi dung don vi', [m.hoi[0].dvt, m.hoi[0].deXuat], ['Set', 1]);
    dung('noi ro so duoc ghi vao Mon', m.hoi[0].nhan.indexOf('ghi vào món') >= 0);
    bang('tai lai man mot lan', m.tai(), 1);
  });
  await ca('app: nguoi bo khong go he so thi dung, khong goi lan hai, khong bao da gan', async function () {
    var m = appMoi({ go: 0 });
    await m.g.dcmGanXong('HDM-1', 3, 'DVTI00014');
    bang('chi goi mot lan', m.goi.length, 1);
    bang('khong tai lai', m.tai(), 0);
    bang('khong bao gi', m.bao.length, 0);
  });

  await ca('Desk: nut Gan Mon cho dong trong ma: mo len da goi y san Mon may doan, hoi he so, gui kem he so', async function () {
    var mc = mayChu(), hop = null, reload = 0, alert = [];
    function Truong(df) { this.df = df; this.$wrapper = { html: function (h) { df._html = h; } }; this.refresh = function () {}; }
    var frm = {
      doc: { name: 'HDM-1', docstatus: 0, custom_minvoice_id: 'MI-1', items: [
        { idx: 1, item_code: 'NVLT1', qty: 1, rate: 1 },
        { idx: 3, item_code: '', ten_hang_ncc: 'Phí dịch vụ', qty: 1, rate: 30000 }] },
      is_dirty: function () { return false; }, reload_doc: async function () { reload++; },
    };
    var g = {
      format_currency: String, parseFloat: parseFloat, String: String,
      frappe: {
        utils: { escape_html: function (s) { return String(s).replace(/</g, '&lt;'); } },
        ui: { form: { on: function () {} }, Dialog: function (c) {
          hop = this; this.c = c; this.gt = {}; this.fields_dict = {};
          var self = this;
          c.fields.forEach(function (f) { if (f.fieldname) self.fields_dict[f.fieldname] = new Truong(f); });
          this.get_field = function (n) { return self.fields_dict[n]; };
          this.get_value = function (n) { return self.gt[n]; };
          this.set_value = function (n, v) { self.gt[n] = v; };
          this.show = function () {}; this.hide = function () { self.an = 1; };
          this.disable_primary_action = function () {}; this.enable_primary_action = function () {};
        } },
        call: async function (o) { return { message: await mc.api(o.method, o.args) }; },
        msgprint: function (s) { alert.push(s); }, show_alert: function (o) { alert.push(o.message); },
        user: { has_role: function () { return true; } },
      },
    };
    vm.createContext(g);
    vm.runInContext(layHam(DESK, 'vgbGanMonDesk'), g);
    await g.vgbGanMonDesk(frm);
    await new Promise(function (r) { setTimeout(r, 5); });
    bang('chi liet ke dong trong ma', hop.fields_dict.dong.df.options.map(function (o) { return o.value; }), ['3']);
    bang('Mon may doan dien san', hop.get_value('item_code'), 'DVTI00014');
    dung('hien ly do goi y', String(hop.fields_dict.goi_y.df._html).indexOf('Máy đoán') >= 0);
    await hop.c.primary_action(hop.gt);
    bang('chua dong hop, hien o he so', [hop.an, hop.fields_dict.he_so.df.hidden], [undefined, 0]);
    bang('nhan o he so noi dung don vi', hop.fields_dict.he_so.df.label, '1 Lần bằng bao nhiêu Set?');
    bang('de xuat 1 cho dich vu', hop.get_value('he_so'), 1);
    await hop.c.primary_action(hop.gt);
    var gan = mc.goi.filter(function (x) { return x.m.endsWith('gan_ma_hang'); });
    bang('lan hai gui kem he so', [gan.length, gan[1].a.he_so, gan[1].a.dong, gan[1].a.item_code], [2, 1, '3', 'DVTI00014']);
    bang('xong thi dong hop va tai lai phieu', [hop.an, reload], [1, 1]);
  });
}

chayHet().then(function () {
  console.log('Bo ca kiem HANH VI may goi y, nguoi chot (#358)');
  ket.loi.forEach(function (d) { console.log('  HONG  ' + d); });
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
}, function (e) { console.log('VO KHUNG: ' + (e && e.stack ? e.stack : e)); process.exit(1); });

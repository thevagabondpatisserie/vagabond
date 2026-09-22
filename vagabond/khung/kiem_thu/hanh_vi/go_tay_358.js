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
  var mc = mayChu(), hoi = [], tai = 0, bao = [], hoiXacNhan = [], goNguon = [], hoiChu = [];
  var g = {
    money: String, kl: String, busy: function () {}, toast: function () {}, go: function () { tai++; },
    baoTin: function (s) { bao.push(s); }, parseFloat: parseFloat, Number: Number,
    qtySheet: async function (t, nhan, deXuat, dvt) { hoi.push({ t: t, nhan: nhan, deXuat: deXuat, dvt: dvt }); return canh.go; },
    promptSheet: async function (t, gy) { hoiChu.push({ t: t, gy: gy }); return canh.goChu; },
    api: mc.api,
    confirmSheet: async function (t, n) { hoiXacNhan.push({ t: t, n: n }); return canh.dongY !== 0; },
  };
  vm.createContext(g);
  vm.runInContext(layHam(APP, 'dcmDoiMaTheoNguon') + '\n' + layHam(APP, 'dcmGanXong'), g);
  /* Cua "sua theo hoa don goc" dung ban gia: ca kiem chi soi dcmGanXong co mo
     dung cua do khong; ruot cua no di qua sheet nhieu tang, co ca rieng. */
  g.dcmDoiMaTheoNguon = async function (name, idx, ma) { goNguon.push([name, idx, ma]); return canh.coNguon !== 0; };
  return { g: g, goi: mc.goi, hoi: hoi, tai: function () { return tai; }, bao: bao,
    hoiXacNhan: hoiXacNhan, goNguon: goNguon, hoiChu: hoiChu };
}

async function chayHet() {
  await ca('Codex #358 vong 12: dong da mang Mon ke toan tu go thi hop Desk giu nguyen Mon do', async function () {
    var mc = mayChu(), hop = null;
    function Truong(df) { this.df = df; this.$wrapper = { html: function (h) { df._html = h; } }; this.refresh = function () {}; }
    var frm = {
      doc: { name: 'HDM-1', docstatus: 0, custom_minvoice_id: 'MI-1', items: [
        { idx: 3, item_code: 'NVLT00141', vgb_mon_may_doan: 'DVTI00014', ten_hang_ncc: 'Hạt dẻ', qty: 1, rate: 1 }] },
      is_dirty: function () { return false; }, reload_doc: async function () {},
    };
    var g = {
      format_currency: String, parseFloat: parseFloat, String: String,
      frappe: {
        utils: { escape_html: function (s) { return String(s); } },
        ui: { form: { on: function () {} }, Dialog: function (c) {
          hop = this; this.c = c; this.gt = {}; this.fields_dict = {};
          var self = this;
          c.fields.forEach(function (f) { if (f.fieldname) self.fields_dict[f.fieldname] = new Truong(f); });
          this.get_field = function (n) { return self.fields_dict[n]; };
          this.get_value = function (n) { return self.gt[n]; };
          this.set_value = function (n, v) {
            var cu = self.gt[n]; self.gt[n] = v;
            var t = self.fields_dict[n];
            if (cu !== v && t && t.df.onchange) t.df.onchange();
          };
          this.show = function () {}; this.hide = function () {};
          this.disable_primary_action = function () {}; this.enable_primary_action = function () {};
        } },
        call: async function (o) { return { message: await mc.api(o.method, o.args) }; },
        msgprint: function () {}, show_alert: function () {},
        user: { has_role: function () { return true; } },
      },
    };
    vm.createContext(g);
    vm.runInContext(layHam(DESK, 'vgbGanMonDesk'), g);
    await g.vgbGanMonDesk(frm);
    await new Promise(function (r) { setTimeout(r, 5); });
    bang('liet ke ca dong con dau du da co ma', hop.fields_dict.dong.df.options.map(function (o) { return o.value; }), ['3']);
    bang('giu Mon ke toan da go, khong de goi y len', hop.get_value('item_code'), 'NVLT00141');
  });

  await ca('Codex #358 vong 8: hang ton kho ma hoa don goc khong ghi don vi thi app mo thang cua sua theo hoa don goc', async function () {
    var m = appMoi({});
    m.g.api = async function (mm, a) {
      if (mm.endsWith('gan_ma_hang')) { m.goi.push({ m: mm, a: a }); return { can_nguon: 1, item_code: a.item_code, loi_nhan: 'Hoá đơn gốc không ghi đơn vị cho dòng 1, mà NVLT00141 là hàng tồn kho.' }; }
      return {};
    };
    await m.g.dcmGanXong('HDM-1', 1, 'NVLT00141');
    bang('chi goi gan mot lan', m.goi.length, 1);
    bang('hoi nguoi truoc khi mo cua khac', m.hoiXacNhan.length, 1);
    bang('mo cua sua theo hoa don goc dung dong, dung Mon', m.goNguon, [['HDM-1', 1, 'NVLT00141']]);
    bang('khong bao la da gan', m.bao.length, 0);
  });
  await ca('Codex #358 vong 8: nguoi khong dong y thi dung han, khong goi gi them', async function () {
    var m = appMoi({ dongY: 0 });
    m.g.api = async function (mm, a) {
      if (mm.endsWith('gan_ma_hang')) { m.goi.push({ m: mm, a: a }); return { can_nguon: 1, item_code: a.item_code, loi_nhan: 'x' }; }
      return {};
    };
    await m.g.dcmGanXong('HDM-1', 1, 'NVLT00141');
    bang('khong mo cua nao', m.goNguon.length, 0);
    bang('khong tai lai man', m.tai(), 0);
  });

  await ca('app: Mon chua khai don vi thi HOI he so, gui lai kem he so; khong luu gi truoc khi nguoi go', async function () {
    var m = appMoi({ go: 1 });
    await m.g.dcmGanXong('HDM-1', 3, 'DVTI00014');
    bang('hai lan goi gan', m.goi.filter(function (x) { return x.m.endsWith('gan_ma_hang'); }).length, 2);
    bang('lan dau khong he so', m.goi[0].a.he_so, undefined);
    bang('lan hai mang he so nguoi go', m.goi[1].a.he_so, 1);
    bang('lan hai noi ro he so cho Mon nao (Codex #358)', m.goi[1].a.he_so_cho, 'DVTI00014');
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
        { idx: 3, item_code: '', ten_hang_ncc: 'Phí <b>dịch vụ</b>', qty: 1, rate: 30000 }] },
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
          /* Nhu Frappe that: dat gia tri khac cu thi goi onchange cua o do.
             Nguoi go vao o Mon cung di dung duong nay. */
          this.set_value = function (n, v) {
            var cu = self.gt[n]; self.gt[n] = v;
            var t = self.fields_dict[n];
            if (cu !== v && t && t.df.onchange) t.df.onchange();
          };
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
    /* Codex #358 P2: o chon dong phai tim duoc (Autocomplete), khong xo Select.
       Nhan dong co ten nha cung cap ghi nen phai thoat HTML. */
    bang('o chon dong tim duoc', hop.fields_dict.dong.df.fieldtype, 'Autocomplete');
    dung('ten nha cung cap khong chen duoc the HTML', hop.fields_dict.dong.df.options[0].label.indexOf('<b>') < 0);
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

  await ca('Codex #358 P1 vong 2: goi y cua dong cu ve cham thi KHONG de len dong nguoi dang chon', async function () {
    /* Chuoi cua Codex: mo hop, goi y dong 2 dang cho; nguoi chon dong 3; goi y
       dong 3 ve truoc (Mon B), goi y dong 2 ve sau (Mon A). Ban cu dien Mon A
       vao o Mon trong khi dang o dong 3, bam Gan la gan nham Mon A cho dong 3. */
    var hop = null, cho = [];
    function Truong(df) { this.df = df; this.$wrapper = { html: function (h) { df._html = h; } }; this.refresh = function () {}; }
    var frm = {
      doc: { name: 'HDM-1', docstatus: 0, custom_minvoice_id: 'MI-1', items: [
        { idx: 2, item_code: '', ten_hang_ncc: 'Bột', qty: 1, rate: 1 },
        { idx: 3, item_code: '', ten_hang_ncc: 'Phí dịch vụ', qty: 1, rate: 30000 }] },
      is_dirty: function () { return false; }, reload_doc: async function () {},
    };
    var g = {
      format_currency: String, parseFloat: parseFloat, String: String,
      frappe: {
        utils: { escape_html: function (s) { return String(s); } },
        ui: { form: { on: function () {} }, Dialog: function (c) {
          hop = this; this.c = c; this.gt = {}; this.fields_dict = {};
          var self = this;
          c.fields.forEach(function (f) { if (f.fieldname) self.fields_dict[f.fieldname] = new Truong(f); });
          this.get_field = function (n) { return self.fields_dict[n]; };
          this.get_value = function (n) { return self.gt[n]; };
          this.set_value = function (n, v) {
            var cu = self.gt[n]; self.gt[n] = v;
            var t = self.fields_dict[n];
            if (cu !== v && t && t.df.onchange) t.df.onchange();
          };
          this.show = function () {}; this.hide = function () {};
          this.disable_primary_action = function () {}; this.enable_primary_action = function () {};
        } },
        /* Goi y tra ve khi ca kiem bao, de dung dung thu tu mang cham. */
        call: function (o) {
          return new Promise(function (tra) { cho.push({ dong: o.args.dong, tra: tra }); });
        },
        msgprint: function () {}, show_alert: function () {},
        user: { has_role: function () { return true; } },
      },
    };
    vm.createContext(g);
    vm.runInContext(layHam(DESK, 'vgbGanMonDesk'), g);
    g.vgbGanMonDesk(frm);
    await new Promise(function (r) { setTimeout(r, 5); });
    hop.set_value('dong', '3');
    await new Promise(function (r) { setTimeout(r, 5); });
    var mon = { '2': 'MON_A', '3': 'MON_B' };
    var cua3 = cho.filter(function (x) { return String(x.dong) === '3'; });
    var cua2 = cho.filter(function (x) { return String(x.dong) === '2'; });
    bang('co goi y dang cho cho ca hai dong', [cua2.length > 0, cua3.length > 0], [true, true]);
    cua3.forEach(function (x) { x.tra({ message: { goi_y: [{ item_code: mon['3'], item_name: 'B', vi_sao: 'x' }] } }); });
    await new Promise(function (r) { setTimeout(r, 5); });
    cua2.forEach(function (x) { x.tra({ message: { goi_y: [{ item_code: mon['2'], item_name: 'A', vi_sao: 'x' }] } }); });
    await new Promise(function (r) { setTimeout(r, 5); });
    bang('dang o dong 3 thi o Mon giu Mon cua dong 3', [hop.get_value('dong'), hop.get_value('item_code')], ['3', 'MON_B']);
  });

  await ca('Codex #358 P1 vong 2 (thu tu nguoc): goi y dong cu ve TRUOC khi o Mon con trong thi van KHONG de len dong moi', async function () {
    /* Chuoi cua Codex: mo hop, goi y dong 2 dang cho; nguoi chon dong 3; goi y
       dong 3 ve truoc (Mon B), goi y dong 2 ve sau (Mon A). Ban cu dien Mon A
       vao o Mon trong khi dang o dong 3, bam Gan la gan nham Mon A cho dong 3. */
    var hop = null, cho = [];
    function Truong(df) { this.df = df; this.$wrapper = { html: function (h) { df._html = h; } }; this.refresh = function () {}; }
    var frm = {
      doc: { name: 'HDM-1', docstatus: 0, custom_minvoice_id: 'MI-1', items: [
        { idx: 2, item_code: '', ten_hang_ncc: 'Bột', qty: 1, rate: 1 },
        { idx: 3, item_code: '', ten_hang_ncc: 'Phí dịch vụ', qty: 1, rate: 30000 }] },
      is_dirty: function () { return false; }, reload_doc: async function () {},
    };
    var g = {
      format_currency: String, parseFloat: parseFloat, String: String,
      frappe: {
        utils: { escape_html: function (s) { return String(s); } },
        ui: { form: { on: function () {} }, Dialog: function (c) {
          hop = this; this.c = c; this.gt = {}; this.fields_dict = {};
          var self = this;
          c.fields.forEach(function (f) { if (f.fieldname) self.fields_dict[f.fieldname] = new Truong(f); });
          this.get_field = function (n) { return self.fields_dict[n]; };
          this.get_value = function (n) { return self.gt[n]; };
          this.set_value = function (n, v) {
            var cu = self.gt[n]; self.gt[n] = v;
            var t = self.fields_dict[n];
            if (cu !== v && t && t.df.onchange) t.df.onchange();
          };
          this.show = function () {}; this.hide = function () {};
          this.disable_primary_action = function () {}; this.enable_primary_action = function () {};
        } },
        /* Goi y tra ve khi ca kiem bao, de dung dung thu tu mang cham. */
        call: function (o) {
          return new Promise(function (tra) { cho.push({ dong: o.args.dong, tra: tra }); });
        },
        msgprint: function () {}, show_alert: function () {},
        user: { has_role: function () { return true; } },
      },
    };
    vm.createContext(g);
    vm.runInContext(layHam(DESK, 'vgbGanMonDesk'), g);
    g.vgbGanMonDesk(frm);
    await new Promise(function (r) { setTimeout(r, 5); });
    hop.set_value('dong', '3');
    await new Promise(function (r) { setTimeout(r, 5); });
    var mon = { '2': 'MON_A', '3': 'MON_B' };
    var cua3 = cho.filter(function (x) { return String(x.dong) === '3'; });
    var cua2 = cho.filter(function (x) { return String(x.dong) === '2'; });
    bang('co goi y dang cho cho ca hai dong', [cua2.length > 0, cua3.length > 0], [true, true]);
    /* Ghi chu 22/09: lop "o Mon da co gia tri thi khong de" che mat thu tu
       kia; thu tu nay chi lop kiem dong moi do duoc. */
    cua2.forEach(function (x) { x.tra({ message: { goi_y: [{ item_code: mon['2'], item_name: 'A', vi_sao: 'x' }] } }); });
    await new Promise(function (r) { setTimeout(r, 5); });
    cua3.forEach(function (x) { x.tra({ message: { goi_y: [{ item_code: mon['3'], item_name: 'B', vi_sao: 'x' }] } }); });
    await new Promise(function (r) { setTimeout(r, 5); });
    bang('dang o dong 3 thi o Mon giu Mon cua dong 3', [hop.get_value('dong'), hop.get_value('item_code')], ['3', 'MON_B']);
  });

  await ca('Codex #358 P1 vong 3: nguoi tu chon Mon trong luc goi y dang tai thi goi y ve sau KHONG de len', async function () {
    /* Chuoi cua Codex: mo hop, goi y dong dang cho; nguoi go Mon DVBH00001
       vao o Mon; goi y ve (DVTI00014). Ban cu de DVTI00014 len lua chon cua
       nguoi, bam Gan la luu Mon may chu khong phai Mon nguoi chon. */
    var hop = null, cho = [];
    function Truong(df) { this.df = df; this.$wrapper = { html: function (h) { df._html = h; } }; this.refresh = function () {}; }
    var frm = {
      doc: { name: 'HDM-1', docstatus: 0, custom_minvoice_id: 'MI-1', items: [
        { idx: 3, item_code: '', ten_hang_ncc: 'Phí dịch vụ', qty: 1, rate: 30000 }] },
      is_dirty: function () { return false; }, reload_doc: async function () {},
    };
    var g = {
      format_currency: String, parseFloat: parseFloat, String: String,
      frappe: {
        utils: { escape_html: function (s) { return String(s); } },
        ui: { form: { on: function () {} }, Dialog: function (c) {
          hop = this; this.c = c; this.gt = {}; this.fields_dict = {};
          var self = this;
          c.fields.forEach(function (f) { if (f.fieldname) self.fields_dict[f.fieldname] = new Truong(f); });
          this.get_field = function (n) { return self.fields_dict[n]; };
          this.get_value = function (n) { return self.gt[n]; };
          this.set_value = function (n, v) {
            var cu = self.gt[n]; self.gt[n] = v;
            var t = self.fields_dict[n];
            if (cu !== v && t && t.df.onchange) t.df.onchange();
          };
          this.show = function () {}; this.hide = function () {};
          this.disable_primary_action = function () {}; this.enable_primary_action = function () {};
        } },
        call: function (o) { return new Promise(function (tra) { cho.push(tra); }); },
        msgprint: function () {}, show_alert: function () {},
        user: { has_role: function () { return true; } },
      },
    };
    vm.createContext(g);
    vm.runInContext(layHam(DESK, 'vgbGanMonDesk'), g);
    g.vgbGanMonDesk(frm);
    await new Promise(function (r) { setTimeout(r, 5); });
    hop.set_value('item_code', 'DVBH00001');
    cho.forEach(function (tra) { tra({ message: { goi_y: [{ item_code: 'DVTI00014', item_name: 'x', vi_sao: 'Máy đoán' }] } }); });
    await new Promise(function (r) { setTimeout(r, 5); });
    bang('giu Mon nguoi da chon', hop.get_value('item_code'), 'DVBH00001');
    dung('van hien goi y de nguoi tham khao', String(hop.fields_dict.goi_y.df._html).indexOf('DVTI00014') >= 0);
  });

  await ca('Codex #358 P1: hoi he so cho Mon A roi nguoi doi sang Mon B thi KHONG gui he so cu cho Mon B, may chu hoi lai cho B', async function () {
    /* Chuoi cua Codex: bam Gan, may hoi he so cho DVTI00014 (1 Lan = ? Set,
       dien san 1), nguoi sua o Mon sang NVLT00141, bam Gan lan nua. Ban cu
       gui he_so=1 kem NVLT00141 va may chu ghi vinh vien 1 Lan = 1 Gram. */
    var mc = mayChu(), hop = null;
    function Truong(df) { this.df = df; this.$wrapper = { html: function (h) { df._html = h; } }; this.refresh = function () {}; }
    var frm = {
      doc: { name: 'HDM-1', docstatus: 0, custom_minvoice_id: 'MI-1', items: [
        { idx: 3, item_code: '', ten_hang_ncc: 'Phí dịch vụ', qty: 1, rate: 30000 }] },
      is_dirty: function () { return false; }, reload_doc: async function () {},
    };
    var g = {
      format_currency: String, parseFloat: parseFloat, String: String,
      frappe: {
        utils: { escape_html: function (s) { return String(s); } },
        ui: { form: { on: function () {} }, Dialog: function (c) {
          hop = this; this.c = c; this.gt = {}; this.fields_dict = {};
          var self = this;
          c.fields.forEach(function (f) { if (f.fieldname) self.fields_dict[f.fieldname] = new Truong(f); });
          this.get_field = function (n) { return self.fields_dict[n]; };
          this.get_value = function (n) { return self.gt[n]; };
          this.set_value = function (n, v) {
            var cu = self.gt[n]; self.gt[n] = v;
            var t = self.fields_dict[n];
            if (cu !== v && t && t.df.onchange) t.df.onchange();
          };
          this.show = function () {}; this.hide = function () { self.an = 1; };
          this.disable_primary_action = function () {}; this.enable_primary_action = function () {};
        } },
        call: async function (o) { return { message: await mc.api(o.method, o.args) }; },
        msgprint: function () {}, show_alert: function () {},
        user: { has_role: function () { return true; } },
      },
    };
    vm.createContext(g);
    vm.runInContext(layHam(DESK, 'vgbGanMonDesk'), g);
    await g.vgbGanMonDesk(frm);
    await new Promise(function (r) { setTimeout(r, 5); });
    await hop.c.primary_action(hop.gt);
    bang('lan dau hoi he so cho Mon may doan', [hop.fields_dict.he_so.df.hidden, hop.get_value('he_so')], [0, 1]);
    hop.set_value('item_code', 'NVLT00141');
    bang('doi Mon thi an o he so va xoa so cu', [hop.fields_dict.he_so.df.hidden, hop.get_value('he_so') || 0], [1, 0]);
    await hop.c.primary_action(hop.gt);
    var gan = mc.goi.filter(function (x) { return x.m.endsWith('gan_ma_hang'); });
    bang('lan gui cho Mon moi KHONG kem he so cu', [gan[1].a.item_code, gan[1].a.he_so], ['NVLT00141', undefined]);
    bang('may chu duoc hoi lai, o he so hien lai', hop.fields_dict.he_so.df.hidden, 0);
    await hop.c.primary_action(hop.gt);
    var gan3 = mc.goi.filter(function (x) { return x.m.endsWith('gan_ma_hang'); })[2];
    bang('lan ba gui he so kem dung Mon da duoc hoi', [gan3.a.item_code, gan3.a.he_so, gan3.a.he_so_cho], ['NVLT00141', 1, 'NVLT00141']);
  });

  /* Codex #358 vong 19: to TRA HANG khong di duoc cua "sua theo hoa don goc".
     App phai hoi don vi ngay tai cho, khong duoc day nguoi sang cua dong. */
  await ca('Codex #358 vong 19: app hoi don vi va he so roi gui len, khong mo cua nguon', async function () {
    var m = appMoi({ goChu: 'Thùng', go: 24 });
    m.g.api = async function (mm, a) {
      if (!mm.endsWith('gan_ma_hang')) return {};
      m.goi.push({ m: mm, a: JSON.parse(JSON.stringify(a)) });
      /* Chan vong lap: may khach quen gui don vi thi hoi mai. Ca kiem phai
         HONG ro rang, khong treo may (dot bien M5 ngay 22/09). */
      if (m.goi.length > 3) throw new Error('goi gan_ma_hang qua 3 lan: don vi khong duoc gui len');
      if (!a.dvt_khai) return { can_dvt: 1, item_code: a.item_code, dvt_kho: 'Kg', loi_nhan: 'Tờ này không đi được cửa sửa theo hoá đơn gốc.' };
      return { item_code: a.item_code, dvt: a.dvt_khai, he_so: a.he_so, loi_nhan: 'Đã gắn món cho dòng 1.' };
    };
    await m.g.dcmGanXong('HDM-TRA', 1, 'NVLT00141');
    bang('hai lan goi gan', m.goi.length, 2);
    bang('khong mo cua nguon', m.goNguon.length, 0);
    bang('hoi chu mot lan', m.hoiChu.length, 1);
    bang('hoi he so theo don vi vua go', m.hoi[0].t, '1 Thùng bằng bao nhiêu Kg?');
    bang('lan hai gui du don vi, he so va Mon da hoi',
      [m.goi[1].a.dvt_khai, m.goi[1].a.he_so, m.goi[1].a.he_so_cho], ['Thùng', 24, 'NVLT00141']);
    bang('tai lai man mot lan', m.tai(), 1);
  });
  await ca('Codex #358 vong 19: nguoi bo trong o don vi thi dung, khong goi lan hai', async function () {
    var m = appMoi({ goChu: '   ', go: 24 });
    m.g.api = async function (mm, a) {
      if (!mm.endsWith('gan_ma_hang')) return {};
      m.goi.push({ m: mm, a: a });
      return { can_dvt: 1, item_code: a.item_code, dvt_kho: 'Kg', loi_nhan: 'x' };
    };
    await m.g.dcmGanXong('HDM-TRA', 1, 'NVLT00141');
    bang('chi goi mot lan', m.goi.length, 1);
    bang('khong hoi he so', m.hoi.length, 0);
    bang('khong tai lai, khong bao da gan', [m.tai(), m.bao.length], [0, 0]);
  });

  await ca('Codex #358 vong 19: hop Desk hoi ca don vi lan he so, doi Mon thi xoa het', async function () {
    var hop = null, goi = [], reload = 0;
    function Truong(df) { this.df = df; this.$wrapper = { html: function (h) { df._html = h; } }; this.refresh = function () {}; }
    var frm = {
      doc: { name: 'HDM-TRA', docstatus: 0, is_return: 1, custom_minvoice_id: 'MI-1', items: [
        { idx: 1, item_code: '', ten_hang_ncc: 'Hạt dẻ', qty: -1, rate: 280000 }] },
      is_dirty: function () { return false; }, reload_doc: async function () { reload++; },
    };
    var g = {
      format_currency: String, parseFloat: parseFloat, String: String,
      frappe: {
        utils: { escape_html: function (s) { return String(s); } },
        ui: { form: { on: function () {} }, Dialog: function (c) {
          hop = this; this.c = c; this.gt = {}; this.fields_dict = {};
          var self = this;
          c.fields.forEach(function (f) { if (f.fieldname) self.fields_dict[f.fieldname] = new Truong(f); });
          this.get_field = function (n) { return self.fields_dict[n]; };
          this.get_value = function (n) { return self.gt[n]; };
          this.set_value = function (n, v) {
            var cu = self.gt[n]; self.gt[n] = v;
            var t = self.fields_dict[n];
            if (cu !== v && t && t.df.onchange) t.df.onchange();
          };
          this.show = function () {}; this.hide = function () { self.an = 1; };
          this.disable_primary_action = function () {}; this.enable_primary_action = function () {};
        } },
        call: async function (o) {
          if (o.method.endsWith('goi_y_mon')) return { message: { goi_y: [] } };
          goi.push(JSON.parse(JSON.stringify(o.args)));
          if (!o.args.dvt_khai) return { message: { can_dvt: 1, item_code: o.args.item_code, dvt_kho: 'Kg', loi_nhan: 'Tờ này không đi được cửa sửa theo hoá đơn gốc.' } };
          return { message: { item_code: o.args.item_code, loi_nhan: 'Đã gắn Món.' } };
        },
        msgprint: function () {}, show_alert: function () {},
        user: { has_role: function () { return true; } },
      },
    };
    vm.createContext(g);
    vm.runInContext(layHam(DESK, 'vgbGanMonDesk'), g);
    await g.vgbGanMonDesk(frm);
    await new Promise(function (r) { setTimeout(r, 5); });
    hop.set_value('dong', '1');
    hop.set_value('item_code', 'NVLT00141');
    await hop.c.primary_action(hop.gt);
    bang('hien ca o don vi lan o he so',
      [hop.fields_dict.dvt_khai.df.hidden, hop.fields_dict.he_so.df.hidden], [0, 0]);
    dung('nhan o he so noi ro quy ve don vi kho', hop.fields_dict.he_so.df.label.indexOf('Kg') >= 0);
    /* Nguoi doi Mon sau khi duoc hoi: bo het cau hoi cu, khong ghi don vi cua
       Mon cu vao Mon moi (cung luat voi he so, Codex #358 P1). */
    hop.set_value('item_code', 'NVLT00999');
    bang('doi Mon thi an ca hai o',
      [hop.fields_dict.dvt_khai.df.hidden, hop.fields_dict.he_so.df.hidden], [1, 1]);
    hop.set_value('item_code', 'NVLT00141');
    await hop.c.primary_action(hop.gt);
    hop.set_value('dvt_khai', 'Thùng');
    hop.set_value('he_so', 24);
    await hop.c.primary_action(hop.gt);
    var cuoi = goi[goi.length - 1];
    bang('gui du don vi, he so va Mon da hoi',
      [cuoi.dvt_khai, cuoi.he_so, cuoi.he_so_cho, cuoi.item_code], ['Thùng', 24, 'NVLT00141', 'NVLT00141']);
    bang('xong thi dong hop va tai lai phieu', [hop.an, reload], [1, 1]);
  });
}

chayHet().then(function () {
  console.log('Bo ca kiem HANH VI may goi y, nguoi chot (#358)');
  ket.loi.forEach(function (d) { console.log('  HONG  ' + d); });
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
}, function (e) { console.log('VO KHUNG: ' + (e && e.stack ? e.stack : e)); process.exit(1); });

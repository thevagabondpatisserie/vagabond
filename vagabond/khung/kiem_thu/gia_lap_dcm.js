/* Chay THAT man Doi chieu hoa don mua (18-doi-chieu-may-in.js) trong node,
   voi API gia va DOM toi thieu, roi in HTML da ve ra stdout dang JSON.

   Vi sao khong do chuoi: nut "Gan ma hang" ton tai trong ma nguon suot mot
   tuan ma khong ai thay no, vi no nam trong mot nhanh dieu kien khac. Do
   chuoi thay nut, chay that moi thay nut co ve ra hay khong (#252, 10/09).

   Cach dung:
     node gia_lap_dcm.js <ket qua xem JSON> <ket qua so_sanh JSON>

   Khong tinh CSS, khong lam bang chung giao dien. Chi tra loi cau hoi: voi
   du lieu nay, man hinh CO ve ra nut/chu do hay khong. */

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const xem = JSON.parse(process.argv[2]);
const soSanh = JSON.parse(process.argv[3]);

const goc = path.join(__dirname, '..', '..', 'public', 'js', 'bep');
const nen = fs.readFileSync(path.join(goc, '00-nen.js'), 'utf8');
const man = fs.readFileSync(path.join(goc, '18-doi-chieu-may-in.js'), 'utf8');

/* Chi lay ba ham thuan h/money/num tu 00-nen.js, khong nap ca tep. */
function cat(ten) {
  const m = nen.match(new RegExp('\\nfunction ' + ten + '\\([^\\n]*\\n'));
  if (!m) throw new Error('khong thay ' + ten);
  return m[0];
}

const ghi = { html: [], footer: [], api: [] };
const phanTu = {};
function taoEl(id) {
  return phanTu[id] || (phanTu[id] = { id: id, innerHTML: '', onclick: null, addEventListener: function () {} });
}
const ctx = {
  console: console,
  document: {
    getElementById: function (id) { return taoEl(id); },
  },
  frame: function (title, body, opt) {
    ghi.html.push(body);
    if (opt && opt.footer) ghi.footer.push(opt.footer);
    return { onclick: null, addEventListener: function () {} };
  },
  api: async function (method, args) {
    ghi.api.push(method);
    if (method === 'vagabond.doi_chieu_mua.xem') return xem;
    if (method === 'vagabond.doi_chieu_mua.so_sanh') return soSanh;
    return {};
  },
  ngayNgan: function (s) { return String(s || ''); },
  busy: function () {}, toast: function () {}, baoTin: function () {},
  go: function (f) { f(); }, confirmSheet: async function () { return true; },
  sheet: function () {}, mfgPickItem: function () {},
  setTimeout: setTimeout,
};
vm.createContext(ctx);
vm.runInContext(cat('h') + cat('money') + cat('num'), ctx);
vm.runInContext(man, ctx);

(async function () {
  await ctx.scrDcmXem(xem.hd.name);
  /* veSoSanh ve vao #dcmSs sau mot vong await. */
  await new Promise(function (r) { setTimeout(r, 20); });
  process.stdout.write(JSON.stringify({
    khung: ghi.html.join('\n'),
    so_sanh: taoEl('dcmSs').innerHTML,
    footer: ghi.footer.join('\n'),
    api: ghi.api,
  }));
})().catch(function (e) { console.error(e && e.stack || e); process.exit(1); });

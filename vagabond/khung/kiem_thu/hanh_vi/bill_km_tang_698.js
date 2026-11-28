/* Bo ca kiem HANH VI v698: dong chuong trinh khuyen mai tren bill goi QR (Dễ báo
   27/11/2026). Chuong trinh Tang mon ma mon tang chua co trong bill: quay bam
   la may them mon tang roi tru dung so do, dong phai noi ro dieu do. Nap
   NGUYEN app_bep.js nhu trang /bep (khuon mua_vu_ngung_697.js), goi ham ve dong.

   Chay: node vagabond/khung/kiem_thu/hanh_vi/bill_km_tang_698.js */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const dom = require('./dom_gia.js');
{
  const qsa = dom.ElementGia.prototype.querySelectorAll;
  dom.ElementGia.prototype.querySelectorAll = function (q) {
    try { return qsa.call(this, q); } catch (e) { if (/khong hieu/.test(e.message)) return []; throw e; }
  };
}
const APP = process.env.NGUON_APP || path.resolve(__dirname, '../../../public/js/app_bep.js');
const ket = { dat: 0, hong: 0, loi: [] };
function dung(mo, x) { if (!x) throw new Error(mo); }
async function ca(ten, ham) { try { await ham(); ket.dat++; } catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.message)); } }
function appMoi() {
  const tl = dom.taiLieuGia();
  tl.addEventListener = () => {}; tl.readyState = 'loading';
  if (!tl.head) tl.head = tl.createElement('head');
  if (!tl.documentElement) tl.documentElement = tl.createElement('html');
  const vgb = tl.createElement('div'); vgb.id = 'vgb'; tl.body.appendChild(vgb);
  const goi = [];
  let ngung = [];
  const kho = () => { const m = {}; return { getItem: k => (k in m ? m[k] : null), setItem: (k, v) => { m[k] = String(v); }, removeItem: k => { delete m[k]; } }; };
  const g = {
    console: { log() {}, warn() {}, error() {}, info() {} }, document: tl,
    navigator: { userAgent: 'node', onLine: true },
    location: { href: 'https://app.x/bep', pathname: '/bep', hostname: 'app.x', search: '', hash: '', origin: 'https://app.x', replace() {}, reload() {} },
    history: { pushState() {}, replaceState() {}, back() {}, state: null },
    frappe: { session: { user: 'thu@vagabond.invalid' }, csrf_token: 'x' },
    localStorage: kho(), sessionStorage: kho(), fetch: () => new Promise(() => {}),
    setTimeout: () => 0, clearTimeout() {}, setInterval: () => 0, clearInterval() {},
    requestAnimationFrame: f => f(), matchMedia: () => ({ matches: false, addEventListener() {}, addListener() {} }),
    addEventListener() {}, removeEventListener() {}, getComputedStyle: () => ({}),
    URL, URLSearchParams, Blob, Intl, TextEncoder
  };
  g.window = g; g.self = g;
  /* Máy chủ giả: ngung_ngay cập nhật danh sách ngày rồi trả lại cả bảng; lời gọi khác trả rỗng. */
  g.__api = (m, a) => {
    goi.push({ m, a: JSON.parse(JSON.stringify(a || {})) });
    if (m === 'vagabond.mua_vu.ngung_ngay') {
      ngung = a.ngung ? ngung.concat([a.ngay]) : ngung.filter(x => x !== a.ngay);
      return Promise.resolve(duLieu(ngung));
    }
    return Promise.resolve({});
  };
  let src = fs.readFileSync(APP, 'utf8');
  const k = src.lastIndexOf('\n})();');
  src = src.slice(0, k) + '\nwindow.__k = { chay: function (c) { return eval(c); } };' + src.slice(k);
  vm.createContext(g);
  new vm.Script(src, { filename: 'app_bep.js' }).runInContext(g);
  const chay = c => g.__k.chay(c);
  chay('rawCall = function (m, a) { return window.__api(m, a); }; S.user = "thu@vagabond.invalid"; S.roles = ["System Manager"];');
  return {
    tl, goi, chay,
    tim: q => tl.body.querySelectorAll(q),
    bam: async el => { el.dispatchEvent(dom.suKien('click', {}, el)); if (el.onclick) await el.onclick({ target: el }); await nghi(); },
  };
}


(async function () {
  const a = appMoi();
  await ca('Tang mon: noi tang banh, may them vao bill, so tru', async () => {
    const s = a.chay('pbDongKm({ma: "KM-TANG", ten: "Tặng Bánh Giả", dung_duoc: 1, giam: 45000, tang: "1 Bánh Giả"})');
    dung('co chu tang: ' + s, /Tặng 1 Bánh Giả \(máy thêm vào bill\), trừ 45[.,]000 đ/.test(s));
    dung('bam duoc', /cursor:pointer/.test(s) && !/Không áp được/.test(s));
  });
  await ca('Chuong trinh giam thuong: giu nguyen chu Giam', async () => {
    const s = a.chay('pbDongKm({ma: "KM-GRAB", ten: "Voucher", dung_duoc: 1, giam: 40000, tang: ""})');
    dung('chu giam: ' + s, /Giảm 40[.,]000 đ/.test(s) && !/Tặng/.test(s));
  });
  await ca('Khong ap duoc: hien ly do may chu', async () => {
    const s = a.chay('pbDongKm({ma: "KM-WEB", ten: "Web", dung_duoc: 0, giam: 0, ly_do: "món tặng chưa có trong hoá đơn"})');
    dung('ly do: ' + s, /Không áp được: món tặng chưa có trong hoá đơn/.test(s));
  });
  console.log('Bo ca kiem HANH VI v698: dong khuyen mai bill QR');
  ket.loi.forEach(l => console.log('  HONG  ' + l));
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  if (ket.hong) process.exitCode = 1;
}());

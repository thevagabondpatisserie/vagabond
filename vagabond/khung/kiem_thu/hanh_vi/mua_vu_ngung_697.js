/* Bo ca kiem HANH VI v697: nut "Ngung nhan ngay nay" o man Kiem banh theo mua,
   the Lich thang (anh Viet 27/11/2026: tat khan cap mot ngay nhan tren web khi
   vuot tran dot xuat).

   Nap NGUYEN app_bep.js nhu trang /bep (cach cua man_cu_ve_muon_ui16.js), chi thay
   cua ra mang rawCall bang may chu gia giu dung hop dong mua_vu.ngung_ngay (tra
   lai bang). Ca bam nhu nguoi dung: bam o ngay, bam nut, bam xac nhan.

   Chay: node vagabond/khung/kiem_thu/hanh_vi/mua_vu_ngung_697.js */
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
let xongHet = false;
process.on('exit', () => { if (!xongHet) { console.log('  HONG  bo kiem dung giua chung'); process.exitCode = 1; } });
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
function dung(mo, x) { if (!x) throw new Error(mo); }
async function ca(ten, ham) { try { await ham(); ket.dat++; } catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n         ') : e)); } }
async function nghi() { for (let i = 0; i < 40; i++) await Promise.resolve(); await new Promise(r => setImmediate(r)); }

function iso(i) { const d = new Date(); d.setDate(d.getDate() + i); return d.toISOString().slice(0, 10); }
const NGAY = iso(5), NGAY_KHAC = iso(6);
function duLieu(ngung) {
  return {
    co_so: 1, ten_mua: 'Mùa thử', tu_ngay: iso(-3), den_ngay: iso(20), tinh_trang: 'Dang ban',
    dong: [{ ma_hang: 'GIA-P1', ten_banh: 'Panettone Thử', nhan_ngan: 'PT', tran_ngay: 3, san_xuat: 10, co_the_ban: 5 }],
    lich: { ngay: [NGAY], o: { [NGAY]: { 'GIA-P1': { chot: 2, cho: 1, khach: 'Khách A' } } }, muc: { [NGAY]: 2 }, tai: {}, tran: { 'GIA-P1': 3 },
      ty_le_vang: 0.75, ngung: ngung, da_nhan: { [NGAY]: { 'GIA-P1': 3 } } },
    dot: [], dinh_muc: [], doi_ruot: []
  };
}

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
  g.__du = duLieu([]);
  chay('MV.mua = "Mùa thử"; MV.xem = "lich"; MV.data = window.__du;');
  return {
    tl, goi, chay,
    tim: q => tl.body.querySelectorAll(q),
    bam: async el => { el.dispatchEvent(dom.suKien('click', {}, el)); if (el.onclick) await el.onclick({ target: el }); await nghi(); },
    oNgay: ng => tl.body.querySelectorAll('[data-mvng]').find(x => x.getAttribute('data-mvng') === ng),
  };
}

(async function () {
  await ca('Lich thang: ngay trong mua chua qua deu bam duoc (ke ca ngay chua co don); bam ngay, bam Ngung nhan ngay nay, xac nhan: goi dung cua, o ngay co chu Ngung', async () => {
    const a = appMoi();
    a.chay('mvVe()'); await nghi();
    dung('ngay chua co don van bam duoc', a.oNgay(NGAY_KHAC));
    dung('ngay qua khong bam duoc', !a.oNgay(iso(-2)));
    await a.bam(a.oNgay(NGAY));
    const nut = a.tim('#mvNgungNgay')[0];
    dung('co nut trong hop chi tiet ngay', nut && /Ngưng nhận ngày này/.test(nut.textContent));
    dung('hop ghi so da nhan tren tran', /3\/3 trần/.test(a.tl.body.textContent));
    await a.bam(nut);
    const y = a.tim('[data-y]')[0];
    dung('hoi xac nhan', y && /Ngưng nhận/.test(y.textContent));
    await a.bam(y); await nghi();
    bang('goi cua ngung_ngay', a.goi.filter(x => x.m === 'vagabond.mua_vu.ngung_ngay').map(x => x.a), [{ mua: 'Mùa thử', ngay: NGAY, ngung: 1 }]);
    dung('o ngay co chu Ngung', /Ngưng/.test(a.oNgay(NGAY).textContent));
  });

  await ca('Ngay da ngung: hop chi tiet ghi web dang ngung nhan, nut Mo nhan lai goi ngung 0', async () => {
    const a = appMoi();
    a.chay('MV.data = window.__dn;'.replace('window.__dn', JSON.stringify(duLieu([NGAY])))); a.chay('mvVe()'); await nghi();
    await a.bam(a.oNgay(NGAY));
    dung('ghi dang ngung', /ngưng nhận/.test(a.tl.body.textContent));
    const nut = a.tim('#mvNgungNgay')[0];
    dung('nut Mo nhan lai', /Mở nhận lại ngày này/.test(nut.textContent));
    await a.bam(nut); await a.bam(a.tim('[data-y]')[0]); await nghi();
    bang('goi mo lai', a.goi.filter(x => x.m === 'vagabond.mua_vu.ngung_ngay').map(x => x.a.ngung), [0]);
    dung('het chu Ngung', !/Ngưng/.test(a.oNgay(NGAY).textContent));
  });

  await ca('Bam Huy o hop xac nhan: khong goi may chu', async () => {
    const a = appMoi();
    a.chay('mvVe()'); await nghi();
    await a.bam(a.oNgay(NGAY_KHAC));
    await a.bam(a.tim('#mvNgungNgay')[0]);
    await a.bam(a.tim('[data-n]')[0]); await nghi();
    bang('khong goi', a.goi.filter(x => x.m === 'vagabond.mua_vu.ngung_ngay').length, 0);
  });

  xongHet = true;
  console.log('Bo ca kiem HANH VI v697: Ngung nhan ngay nay');
  ket.loi.forEach(l => console.log('  HONG  ' + l));
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  if (ket.hong) process.exitCode = 1;
}());

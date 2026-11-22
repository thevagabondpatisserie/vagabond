/* PR B (vòng 2 kiểm giao diện 22/11/2026): Trang chủ hiện ngay, số đếm về sau; màn cũ
   không vẽ đè màn mới.

   Chạy THẬT khung app (01) và trang chủ (02) trong node. Máy chủ giả GIỮ mọi lượt đếm
   tới khi ca kiểm cho trả, để dựng đúng cảnh máy chủ chậm. Chốt:
     1. Bấm Trang chủ: lưới ô lớn hiện trước khi bất kỳ lượt đếm nào trả về, và mọi lượt
        đếm đã được gửi cùng lúc (không đợi nhau).
     2. Số về: huy hiệu trên ô lớn khớp số máy chủ đếm; ô tìm đang gõ giữ nguyên chữ.
     3. Mở lại trong hạn giữ: không gửi lượt đếm nào, số hiện ngay.
     4. Quá hạn giữ: lưới vẫn hiện ngay với số cũ, đếm lại ở nền, số mới thay vào.
     5. Đã sang màn khác khi số về: màn đang đứng không bị đụng, nhưng bảng ô vẫn nhận số mới
        (màn phân hệ mở sau đọc đúng). Bấm sang màn khác ngay lúc trang chủ đang dựng: trang chủ
        không vẽ đè.
     6. Đổi tài khoản: không mượn số của người trước.
     7. Một lượt đếm hỏng: các ô khác vẫn cập nhật, ô hỏng giữ số cũ. Tổng trên ô giữ nguyên mà
        dòng cảnh báo trong ô đổi (phiếu treo quá lâu): màn phân hệ vẫn thấy cảnh báo mới.
     8. vgbManNay: màn async về muộn sau khi đã sang màn khác thì không vẽ; màn tự gọi thẳng
        màn kết quả (không qua điều hướng) vẫn vẽ; đổi ngày (vẽ lại chính màn) bỏ lượt cũ.

   Không gọi thêm hàm nào "cho chắc" ngoài thao tác của người dùng (reset, go, gõ ô tìm).
   Chạy:  node vagabond/khung/kiem_thu/hanh_vi/trang_chu_nhanh_pr_b.js */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert');
const dom = require('./dom_gia.js');
const BEP = path.resolve(__dirname, '../../../public/js/bep');
const doc = n => fs.readFileSync(path.join(BEP, n), 'utf8');
/* Cho phép chạy trên bản cũ để thấy ca đỏ: TRANG_CHU_NGUON=/tmp/02.js KHUNG_NGUON=/tmp/01.js */
const KHUNG = process.env.KHUNG_NGUON ? fs.readFileSync(process.env.KHUNG_NGUON, 'utf8') : doc('01-khung-app.js');
const TRANG = process.env.TRANG_CHU_NGUON ? fs.readFileSync(process.env.TRANG_CHU_NGUON, 'utf8') : doc('02-trang-chu.js');

async function nghi() { for (let i = 0; i < 30; i++) await Promise.resolve(); await new Promise(r => setImmediate(r)); }

/* Số máy chủ đếm cho từng lượt. Danh sách thì trả đúng chừng ấy dòng. */
const SO = {
  'Material Request': 3, 'Purchase Receipt': 2, 'Phieu Kiem Ke': 1, 'Sales Invoice': 4, 'RnD Purchase Request': 1,
  'Work Order': 0, 'Payment Entry': 0
};
function dong(n) { const a = []; for (let i = 0; i < n; i++) a.push({ name: 'X' + i, status: 'Draft', trang_thai_bep: 'Mới', party_type: 'Supplier' }); return a; }

function appMoi() {
  const tl = dom.taiLieuGia();
  tl.addEventListener = () => {};
  const vgb = tl.createElement('div'); vgb.id = 'vgb'; tl.body.appendChild(vgb);
  if (!tl.head) tl.head = tl.createElement('head');
  let bayGio = 1790000000000;
  const may = { giu: true, cho: [], goi: [], hong: {}, dat: {} };
  const g = { console, JSON, Math, Number, String, Object, Array, Promise, Error, RegExp, parseFloat, parseInt, isNaN,
    Date: (function () { function D(x) { return x === undefined ? new Date(bayGio) : new Date(x); } D.now = () => bayGio; return D; })(),
    document: tl, frappe: { session: { user: 'viet@vagabond.vn' } },
    location: { href: 'https://app.x/bep', pathname: '/bep', hostname: 'app.x', search: '', hash: '', replace() {} },
    history: { pushState() {}, replaceState() {}, back() {} }, requestAnimationFrame: f => f(),
    setTimeout: () => 0, clearTimeout: () => {}, setInterval: () => 0 };
  g.window = g; g.localStorage = { getItem: () => null, setItem() {}, removeItem() {} }; g.addEventListener = () => {};
  vm.createContext(g);
  /* Lượt gọi máy chủ: lượt đếm thì giữ lại khi may.giu; lượt khác trả ngay. */
  g.__goi = (loai, ten, ts) => {
    const k = loai === 'ds' ? ten : ten;
    may.goi.push(k);
    const tinh = () => {
      if (may.hong[k]) throw new Error('hong ' + k);
      if (loai === 'ds') return dong(may.dat[k] != null ? may.dat[k] : (SO[ten] || 0));
      if (ten === 'vagabond.dat_ban.dem_cho_xac_nhan') return { so: may.dat[k] != null ? may.dat[k] : 2 };
      if (ten === 'vagabond.don_huy.dem_phieu_cho') return may.dat[k] || { cho_chi: 1, treo: 0 };
      if (ten === 'vagabond.crm.tong_quan') return { viec_toi: 5 };
      if (ten === 'vagabond.ghim.lay') return { ghim: [], toi_da: 5 };
      if (ten === 'vagabond.khung.ds.danh_ba') return [];
      if (/\.dem_|tong_quan/.test(ten)) return { so: 0 };
      return {};
    };
    const laDem = loai === 'ds' || /\.dem_|tong_quan/.test(ten);
    if (!laDem || !may.giu) return new Promise((r, j) => { try { r(tinh()); } catch (e) { j(e); } });
    return new Promise((r, j) => may.cho.push(() => { try { r(tinh()); } catch (e) { j(e); } }));
  };
  vm.runInContext([
    'var root = document.getElementById("vgb");',
    'function h(s) { return String(s == null ? "" : s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;"); }',
    'function toast() {} function busy() {} function dSkin() {} function money(x) { return String(x); }',
    'function today() { return "2026-11-22"; } function errMsg(e) { return String((e && e.message) || e); }',
    'function confirmSheet() { return Promise.resolve(true); }',
    'function api(m, a) { return __goi("api", m, a); }',
    'function bsSoTrangChu() {} function vgbVeGhim() {} function shortWh(x) { return String(x || ""); }',
  ].join('\n'), g);
  vm.runInContext(KHUNG, g);
  vm.runInContext(TRANG, g);
  vm.runInContext([
    'getList = function (dt, a) { return __goi("ds", dt, a); };',
    'S.user = "viet@vagabond.vn"; S.wh = ["Kho"]; S.roles = ["System Manager", "Sales User", "Stock User", "Accounts Manager", "AP Giám đốc"];',
    'S.quyenNen = { bao_cao: false, bang_sang: false };',
    /* Hàm vai nằm ở các phần khác của app: bật hết để đi qua mọi khối có lượt đếm. */
    'isBep = function () { return true; }; isKho = function () { return true; }; isRnd = function () { return true; }; isSales = function () { return true; };',
    'ctXemDuoc = function () { return true; }; myPayStates = function () { return ["Chờ duyệt"]; }; myPayRoleLabel = function () { return "Giám đốc"; };',
    'WODONE = ["Completed"]; nenCoQuyen = function (k) { return k !== "bao_cao"; };',
  ].join('\n'), g);
  /* Mọi hàm coQuyen* trang chủ gọi mà phần 01/02 không có: coi như có quyền. */
  (TRANG.match(/coQuyen\w+/g) || []).forEach(t => { if (typeof g[t] !== 'function') vm.runInContext(t + ' = function () { return true; };', g); });
  const than = () => tl.getElementById('vgbBody');
  return {
    g, tl, may, than,
    tua(ms) { bayGio += ms; },
    async tha() { while (may.cho.length) { const c = may.cho.splice(0); c.forEach(f => f()); await nghi(); } await nghi(); },
    /* Không chờ hàm màn trả xong: người dùng nhìn màn sau một nhịp, không đợi máy chủ. */
    async trangChu() { g.reset(g.scrHome); await nghi(); },
    so() {
      const o = {};
      (than().querySelectorAll('[data-nhom]') || []).forEach(t => {
        if (!t.classList.contains('gt')) return;
        const b = t.querySelector('.gb'); o[t.getAttribute('data-nhom')] = b ? b.textContent : '';
      });
      return o;
    },
    soGui() { return may.goi.length; }
  };
}

let dat = 0, hong = 0;
async function ca(ten, f) {
  try { await f(); dat++; console.log('  ĐẠT   ' + ten); }
  catch (e) { hong++; console.log("  HỎNG  " + ten + "\n        " + (e && e.message) + (process.env.CHI_TIET ? "\n" + e.stack : "")); }
}

(async function () {
  console.log('\nTrang chủ hiện ngay, số đếm về sau; màn cũ không vẽ đè (PR B)\n');

  await ca('lưới hiện trước khi lượt đếm nào trả về, mọi lượt đếm gửi cùng lúc', async () => {
    const a = appMoi();
    await a.trangChu();
    assert(a.than() && a.than().querySelector('.gwrap'), 'chưa thấy lưới ô lớn khi máy chủ còn giữ số');
    const cho = a.may.cho.length;
    assert(cho >= 12, 'chỉ ' + cho + ' lượt đếm đang chờ cùng lúc, mong từ 12 (đếm song song)');
    /* Chưa có số nào: không ô nào đeo huy hiệu. */
    const s = a.so();
    assert(Object.keys(s).every(k => k === 'VCL' || !s[k]), 'chưa có số mà ô đã đeo số: ' + JSON.stringify(s));
  });

  await ca('số về thì huy hiệu khớp số máy chủ, ô tìm đang gõ giữ nguyên', async () => {
    const a = appMoi();
    await a.trangChu();
    const o = a.tl.getElementById('vgbTim');
    assert(o, 'thiếu ô tìm');
    o.value = 'công nợ';
    await a.tha();
    assert.strictEqual(a.tl.getElementById('vgbTim'), o, 'ô tìm bị dựng lại');
    assert.equal(o.value, 'công nợ', 'mất chữ đang gõ');
    /* Đặt hàng: 3 yêu cầu mua + 3 chuyển kho + 3 sản xuất. Kho: 2 phiếu nhập. */
    assert.equal(a.g.VGB_HUB.Purchase.cnt, 3);
    assert.equal(a.g.VGB_HUB.RCV.cnt, 2);
    assert.equal(a.g.VGB_HUB.DATBAN.cnt, 2);
    const s = a.so();
    const nhom = a.g.VGB_NHOM.filter(n => n.keys.indexOf('Purchase') >= 0)[0];
    assert.equal(s[nhom.k], String(a.g.vgbSoNhom(nhom)), 'ô ' + nhom.k + ' đeo ' + s[nhom.k]);
    assert(+s[nhom.k] > 0, 'ô ' + nhom.k + ' không đeo số');
    /* Số thay tại chỗ phải trùng từng ô với số khi vẽ trọn trang chủ từ đầu. */
    a.g.go(function () { a.g.frame('Khác', '<div></div>'); }); await nghi();
    await a.trangChu();
    assert.deepEqual(a.so(), s, 'số thay tại chỗ khác số vẽ trọn');
  });

  await ca('mở lại trong hạn giữ: không gửi lượt đếm, số hiện ngay', async () => {
    const a = appMoi();
    await a.trangChu(); await a.tha();
    const truoc = a.so();
    a.g.go(function () { a.g.frame('Khác', '<div id="khac"></div>'); }); await nghi();
    a.tua(5000);
    const n0 = a.may.cho.length, g0 = a.soGui();
    await a.trangChu();
    const demMoi = a.may.goi.slice(g0).filter(k => /^(Material|Purchase|Phieu|Sales|RnD|Work|Payment)|\.dem_|tong_quan/.test(k));
    assert.equal(demMoi.length, 0, 'mở lại trong hạn mà vẫn đếm: ' + demMoi.join(', '));
    assert.equal(a.may.cho.length, n0);
    assert.deepEqual(a.so(), truoc, 'số không hiện ngay khi mở lại');
  });

  await ca('quá hạn giữ: lưới hiện ngay với số cũ, đếm lại ở nền, số mới thay vào', async () => {
    const a = appMoi();
    await a.trangChu(); await a.tha();
    const truoc = a.so();
    a.g.go(function () { a.g.frame('Khác', '<div></div>'); }); await nghi();
    a.tua(16000);
    a.may.dat['Purchase Receipt'] = 7;
    await a.trangChu();
    assert.deepEqual(a.so(), truoc, 'lúc chờ đếm lại phải hiện số cũ');
    assert(a.may.cho.length >= 12, 'quá hạn mà không đếm lại');
    await a.tha();
    assert.equal(a.g.VGB_HUB.RCV.cnt, 7, 'số mới chưa thay vào');
    const nhom = a.g.VGB_NHOM.filter(n => n.keys.indexOf('RCV') >= 0)[0];
    assert.equal(a.so()[nhom.k], String(a.g.vgbSoNhom(nhom)));
    assert.notEqual(a.so()[nhom.k], truoc[nhom.k], 'ô ' + nhom.k + ' vẫn đeo số cũ');
  });

  await ca('đã sang màn khác khi số về: màn đang đứng không bị đụng', async () => {
    const a = appMoi();
    await a.trangChu();
    a.g.go(function () { a.g.frame('Đối soát COD', '<div id="cod">COD</div>'); }); await nghi();
    const html = a.than().innerHTML;
    await a.tha();
    assert.equal(a.than().innerHTML, html, 'màn đang đứng bị vẽ lại');
    assert(a.tl.getElementById('cod'), 'mất màn COD');
    /* Số vẫn được giữ cho lần sau. */
    assert.equal(a.g.TC_DEM.kq['ds_Purchase_Receipt'].length, 2);
  });

  await ca('bấm sang màn khác ngay lúc trang chủ đang dựng: trang chủ không vẽ đè', async () => {
    const a = appMoi();
    a.g.reset(a.g.scrHome);
    a.g.go(function () { a.g.frame('Vận đơn', '<div id="vd"></div>'); });
    await nghi(); await a.tha();
    assert(a.tl.getElementById('vd'), 'trang chủ vẽ đè màn vừa mở');
    assert(!a.than().querySelector('.gwrap'));
  });

  await ca('đang ở màn phân hệ khi số về: màn phân hệ đọc đúng số mới', async () => {
    const a = appMoi();
    await a.trangChu(); await a.tha();
    a.g.go(function () { a.g.frame('Khác', '<div></div>'); }); await nghi();
    a.tua(16000);
    a.may.dat['Purchase Receipt'] = 9;
    await a.trangChu();
    a.g.go(function () { a.g.frame('Nhập kho', '<div></div>'); }); await nghi();
    await a.tha();
    assert.equal(a.g.VGB_HUB.RCV.cnt, 9, 'bảng ô chưa có số mới');
    assert(String(a.g.VGB_HUB.RCV.html).indexOf('>9<') > 0, 'dòng ô Nhập kho chưa đeo số mới');
  });

  await ca('số trên ô giữ nguyên nhưng cảnh báo trong ô đổi (Codex #608): màn phân hệ thấy cảnh báo mới', async () => {
    const a = appMoi();
    await a.trangChu(); await a.tha();
    assert(String(a.g.VGB_HUB.PHHUY.html).indexOf('treo quá lâu') < 0);
    a.g.go(function () { a.g.frame('Khác', '<div></div>'); }); await nghi();
    a.tua(16000);
    /* Tổng phiếu chờ chi giữ 1, chỉ số phiếu treo quá lâu tăng. */
    a.may.dat['vagabond.don_huy.dem_phieu_cho'] = { cho_chi: 1, treo: 1 };
    await a.trangChu(); await a.tha();
    assert.equal(a.g.VGB_HUB.PHHUY.cnt, 1);
    assert(String(a.g.VGB_HUB.PHHUY.html).indexOf('1 phiếu treo quá lâu') > 0, 'màn phân hệ vẫn không có cảnh báo phiếu treo');
    assert(String(a.g.VGB_DONG_GOC.PHHUY.html).indexOf('1 phiếu treo quá lâu') > 0, 'bản chụp dòng gốc vẫn cũ');
  });

  await ca('đổi tài khoản: không mượn số của người trước', async () => {
    const a = appMoi();
    await a.trangChu(); await a.tha();
    a.g.S.user = 'thu.ngan@vagabond.vn';
    await a.trangChu();
    const s = a.so();
    assert(Object.keys(s).every(k => k === 'VCL' || !s[k]), 'người mới thấy số của người cũ: ' + JSON.stringify(s));
  });

  await ca('một lượt đếm hỏng: ô khác vẫn cập nhật, ô hỏng giữ số cũ', async () => {
    const a = appMoi();
    await a.trangChu(); await a.tha();
    a.g.go(function () { a.g.frame('Khác', '<div></div>'); }); await nghi();
    a.tua(16000);
    a.may.hong['Purchase Receipt'] = 1;
    a.may.dat['vagabond.dat_ban.dem_cho_xac_nhan'] = 6;
    await a.trangChu(); await a.tha();
    assert.equal(a.g.VGB_HUB.RCV.cnt, 2, 'ô hỏng mất số cũ');
    assert.equal(a.g.VGB_HUB.DATBAN.cnt, 6, 'ô khác không cập nhật');
  });

  /* ---------------- vgbManNay: màn cũ không vẽ đè ---------------- */
  function manCham(a, ten, id) {
    return async function () {
      a.g.frame(ten, '<div>⏳</div>');
      const con = a.g.vgbManNay();
      await new Promise(r => a.may.cho.push(r));
      if (!con()) return;
      a.g.frame(ten, '<div id="' + id + '"></div>');
    };
  }

  await ca('màn async về muộn sau khi đã sang màn khác thì không vẽ', async () => {
    const a = appMoi(); a.may.giu = true;
    await a.trangChu(); await a.tha();
    a.g.go(manCham(a, 'Vận đơn', 'vdXong')); await nghi();
    a.g.go(function () { a.g.frame('Đối soát COD', '<div id="cod"></div>'); }); await nghi();
    await a.tha();
    assert(a.tl.getElementById('cod'), 'màn Đối soát COD bị vẽ đè');
    assert(!a.tl.getElementById('vdXong'), 'màn Vận đơn đã rời vẫn vẽ');
  });

  await ca('lùi về trong lúc màn đang chờ: màn đã lùi không vẽ đè màn cha', async () => {
    const a = appMoi();
    await a.trangChu(); await a.tha();
    a.g.go(function () { a.g.frame('Giao hàng', '<div id="nhom"></div>'); }); await nghi();
    a.g.go(manCham(a, 'Vận đơn', 'vdXong')); await nghi();
    a.g.back(); await nghi();
    await a.tha();
    assert(a.tl.getElementById('nhom'), 'màn cha bị vẽ đè');
    assert(!a.tl.getElementById('vdXong'));
  });

  await ca('đổi ngày (vẽ lại chính màn): lượt cũ bỏ, lượt mới vẽ', async () => {
    const a = appMoi();
    await a.trangChu(); await a.tha();
    let lan = 0;
    const man = async function () {
      const toi = ++lan;
      a.g.frame('Vận đơn', '<div>⏳</div>');
      const con = a.g.vgbManNay();
      await new Promise(r => a.may.cho.push(r));
      if (!con()) return;
      a.g.frame('Vận đơn', '<div id="vd' + toi + '"></div>');
    };
    a.g.go(man); await nghi();
    a.g.go(man, true); await nghi();
    /* Lượt mới về trước, lượt cũ về sau. */
    const c = a.may.cho.splice(0); c[1](); await nghi(); c[0](); await nghi();
    assert(a.tl.getElementById('vd2'), 'lượt mới không vẽ');
    assert(!a.tl.getElementById('vd1'), 'lượt cũ về sau đè lên lượt mới');
  });

  await ca('màn tự gọi thẳng màn kết quả sau khi chờ máy chủ: vẫn vẽ', async () => {
    const a = appMoi();
    await a.trangChu(); await a.tha();
    const ketQua = async function () {
      a.g.frame('Đối soát ca', '<div>⏳</div>');
      const con = a.g.vgbManNay();
      await new Promise(r => a.may.cho.push(r));
      if (!con()) return;
      a.g.frame('Đối soát ca', '<div id="ketqua"></div>');
    };
    /* Từng mở Đối soát ca qua điều hướng, rồi sang màn Tính tiền. */
    a.g.go(ketQua); await nghi(); await a.tha();
    a.g.back(); await nghi();
    a.g.go(function () { a.g.frame('Tính tiền', '<div id="pos"></div>'); }); await nghi();
    /* Bấm Chốt ca: chờ máy chủ, xong gọi thẳng màn kết quả (không qua go). */
    const chot = new Promise(r => a.may.cho.push(r)).then(() => ketQua());
    await a.tha(); await chot;
    assert(a.tl.getElementById('ketqua'), 'màn kết quả gọi thẳng bị chặn nhầm');
  });

  console.log('\n' + dat + ' đạt, ' + hong + ' hỏng');
  process.exit(hong ? 1 : 0);
})();

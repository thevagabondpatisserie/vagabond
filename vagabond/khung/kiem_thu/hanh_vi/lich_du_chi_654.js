/* v654 Lịch dự chi (anh Việt 13/11/2026, ảnh đề xuất JPEG): chạy THẬT khung app
   (01) và màn Dự chi (71) trong node, máy chủ giả trả đúng số trên ảnh.
   Chốt:
     1. Màn chính: Tiền khả dụng có nguồn và giờ đọc, nút ＋ Thêm dự chi, ba
        ngày 15, 18, 20 đúng nguồn, dòng cảnh báo "Ngày 20/11 còn thiếu".
     2. Thêm dự chi: điền form, bấm Lưu dự chi nháp gửi đúng các ô; ô số có
        dấu chấm vẫn gửi số.
     3. Chưa đọc được số dư: màn nói chưa xác định được khả năng chi.
     4. Gợi ý lịch hằng tháng: bấm Thêm vào lịch mở form điền sẵn, Lưu gửi đúng.
     5. Chuẩn chạm: mọi nút, ô, dòng bấm được mới cao từ 44 điểm, chữ từ 13 điểm. */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert');
const dom = require('./dom_gia.js');
const BEP = path.resolve(__dirname, '../../../public/js/bep');
const doc = n => fs.readFileSync(path.join(BEP, n), 'utf8');
const KHUNG = doc('01-khung-app.js'), DCN = doc('71-du-chi.js'), SOAN_DO = doc('48-ban-soan-do.js');
function layHam(src, ten) {
  const dau = src.indexOf('function ' + ten + '(');
  if (dau < 0) throw new Error('Không thấy hàm ' + ten);
  let i = src.indexOf('{', dau), sau = 0;
  for (let j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Hàm ' + ten + ' không đóng ngoặc');
}
const NEN = doc('00-nen.js'), HOP = doc('07-hop-thoai.js');
const TIM = [layHam(NEN, 'vgbChuan'), layHam(NEN, 'vgbKhop'), HOP.match(/^var VGB_NGUONG_TIM = \d+;$/m)[0],
  layHam(HOP, 'vgbCanOTim'), layHam(HOP, 'vgbOTim')].join('\n');

function khoMay() {
  const m = new Map();
  return { _m: m, get length() { return m.size; }, key: i => Array.from(m.keys())[i] || null,
    getItem: k => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: k => m.delete(k) };
}
async function nghi() { for (let i = 0; i < 12; i++) await Promise.resolve(); await new Promise(r => setImmediate(r)); }

function appMoi(kho, may) {
  const tl = dom.taiLieuGia(), nghe = {};
  tl.addEventListener = (l, f) => (nghe[l] = nghe[l] || []).push(f);
  tl.createEvent = () => ({ initEvent(t) { this.type = t; } });
  const vgb = tl.createElement('div'); vgb.id = 'vgb'; tl.body.appendChild(vgb);
  let hen = [], soHen = 0, bayGio = 1790000000000;
  const goi = [], hop = [];
  const g = { console, JSON, Math, Number, String, Object, Array, Promise, Error, RegExp, parseFloat, parseInt, isNaN,
    Date: (function () { function D(x) { return x === undefined ? new Date(bayGio) : new Date(x); } D.now = () => bayGio; return D; })(),
    document: tl, frappe: { session: { user: 'uyen@vagabond.vn' } },
    location: { href: 'https://app.x/bep', pathname: '/bep', hostname: 'app.x', search: '', hash: '', replace() {} },
    history: { pushState() {}, replaceState() {}, back() {} }, requestAnimationFrame: f => f(),
    setTimeout: (f, ms) => { soHen++; hen.push({ id: soHen, f, luc: bayGio + (ms || 0) }); return soHen; },
    clearTimeout: id => { hen = hen.filter(x => x.id !== id); } };
  g.window = g; g.localStorage = kho; g.addEventListener = (l, f) => (nghe['w:' + l] = nghe['w:' + l] || []).push(f);
  vm.createContext(g);
  g.__hop = hop;
  g.__api = async (m, a) => {
    goi.push({ m, a });
    const d = may.d;
    if (m === 'vagabond.du_chi.ds') return { dot: [{ name: 'DC-26-11-20', ngay_dot: '2026-11-20', trang_thai: 'Nhap', nhan: 'Thu mua đang thương lượng', tong_tra: 60000000, tong_gia_han: 0 }], ke_tiep: '2026-11-20', da_co: 1 };
    if (m === 'vagabond.lich_du_chi.lich') return JSON.parse(JSON.stringify(may.l));
    if (m === 'vagabond.lich_du_chi.goi_y_lich') return JSON.parse(JSON.stringify(may.gy));
    if (m === 'vagabond.lich_du_chi.luu_muc' || m === 'vagabond.lich_du_chi.luu_lich') return { name: 'X-1' };
    if (m === 'vagabond.du_chi.chi_tiet') return JSON.parse(JSON.stringify(d));
    if (m === 'vagabond.du_chi.luu') {
      JSON.parse(a.dong).forEach(x => {
        const r = d.dong.filter(y => y.hoa_don === x.hoa_don)[0];
        if (x.so_tra != null) { r.so_tra = x.so_tra; r.gia_han = r.co_the_tra - x.so_tra; }
        if (x.ghi_chu != null) r.ghi_chu = x.ghi_chu;
        if (x.hen_dot != null) r.hen_dot = x.hen_dot;
      });
      return JSON.parse(JSON.stringify(d));
    }
    if (m === 'vagabond.du_chi.gui') { d.trang_thai = 'Cho ke toan'; return JSON.parse(JSON.stringify(d)); }
    if (m === 'vagabond.du_chi.duyet') { d.trang_thai = a.buoc === 'fin' ? 'Cho giam doc' : a.buoc === 'tra_lai' ? 'Nhap' : d.trang_thai; return JSON.parse(JSON.stringify(d)); }
    return {};
  };
  vm.runInContext([
    'var root = document.getElementById("vgb");',
    'function h(s) { return String(s == null ? "" : s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;"); }',
    'var __tin = []; function toast(s) { __tin.push(String(s)); } function busy() {} function baoTin(s) { __tin.push("baoTin:" + s); }',
    'function dSkin() {} function vgbCss() {} function money(x) { return String(Math.round(Number(x) || 0)); }',
    'function dmy(x) { var s = String(x || ""); return s.slice(8, 10) + "/" + s.slice(5, 7) + "/" + s.slice(0, 4); }',
    'function today() { return "2026-11-12"; }',
    'function errMsg(e) { return String((e && e.message) || e); }',
    'function confirmSheet(t) { __hop.push(["confirm", t]); return Promise.resolve(true); }',
    'var __chu = null; function hoiChu(t, n, m, o) { __hop.push(["hoiChu", t, !!(o && o.bat_buoc)]); return Promise.resolve(__chu); }',
    'function hoiChon(t, m, ds) { __hop.push(["hoiChon", t]); return Promise.resolve("tiep"); }',
    'function api(m, a) { return __api(m, a); }',
    'function vgbGomNhom() {} function hqLaHop() { return false; }',
    'async function scrHome() { frame(APPNAME, "<div class=\\"emp\\">...</div>"); }',
    'function scrHoSoTTView() {}',
  ].join('\n'), g);
  vm.runInContext(KHUNG, g);
  vm.runInContext(TIM, g);
  vm.runInContext('S.user = "uyen@vagabond.vn"; S.roles = ["Purchase User"]; coQuyenMua = function () { return true; };', g);
  vm.runInContext(DCN, g);
  const boc = SOAN_DO.match(/^(\w+) = sdBoc(?:Hop)?\(/gm).map(x => x.split(' ')[0]);
  boc.forEach(t => { if (typeof g[t] !== 'function') vm.runInContext('function ' + t + '() {}', g); });
  ['bgMoRong', 'bgTay', 'tvTay', 'XK', 'rnd', 'dsTay', 'hdTay', 'hdSua', 'hdGsDong', 'hdGsKieu', 'vdTay', 'cpTay', 'kgForm', 'nccF',
    'dncForm', 'nqSuaMa', 'ctE', 'tcX', 'tq', 'tqd', 'XKT', 'XPV', 'rcvD', 'nhpD', 'mfgD', 'htF', 'htFHop', 'dhF', 'dhOv', 'kmSua', 'GM', 'gmKhoiPhuc']
    .forEach(t => { if (!(t in g)) g[t] = null; });
  vm.runInContext(SOAN_DO, g);
  const o = hd => tl.querySelector('[data-dcntra="' + hd + '"]');
  const than = () => tl.getElementById('vgbBody');
  return {
    g, tl, goi, hop, o, than,
    async tua(ms) { bayGio += ms; for (let v = 0; v < 20; v++) { const toi = hen.filter(x => x.luc <= bayGio); if (!toi.length) break; hen = hen.filter(x => x.luc > bayGio); toi.forEach(x => x.f()); await nghi(); } },
    async go(hd, chu) {
      const el = o(hd); assert(el, 'thiếu ô ' + hd); el.value = chu;
      const ev = dom.suKien('input', {}, el); (nghe.input || []).forEach(f => f(ev)); el.dispatchEvent(ev); if (el.oninput) el.oninput(ev);
      await nghi();
      if (el.onchange) { el.onchange(); await nghi(); }
    },
    async bam(el) { assert(el, 'thiếu chỗ bấm'); const ev = dom.suKien('click', {}, el); (nghe.click || []).forEach(f => f(ev)); await than().onclick({ target: el }); await nghi(); },
    async bamNut(id) { const el = tl.getElementById(id); assert(el, 'thiếu nút ' + id); assert(el.onclick, 'nút ' + id + ' chưa nối'); await el.onclick(); await nghi(); await nghi(); },
    async moMan() { await g.reset(g.scrHome); await nghi(); g.go(g.scrDuChi); await nghi(); await nghi(); await nghi(); },
    async bamId(id) { const el = tl.getElementById(id); assert(el, 'thiếu ' + id); await than().onclick({ target: el }); await nghi(); await nghi(); },
    dat(id, v) { const el = tl.getElementById(id); assert(el, 'thiếu ô ' + id); el.value = v; },
  };
}


const MUC = (nguon, nhan, ngay, so, nd, ma, them) => Object.assign({ khoa: nguon + ':' + ma, nguon, nhan_nguon: nhan, ngay, so_tien: so, noi_dung: nd,
  nguoi_nhan: '', ma, han: '', tre: 0, co: '', qua_ngay: 0, thang: '', dot: '' }, them || {});
function lichAnh(soDu) {
  const ngay = [
    { ngay: '2026-11-15', tong: 10000000, con_lai: soDu == null ? null : 90000000, thieu: 0, muc: [MUC('tay', 'Nhập tay', '2026-11-15', 10000000, 'Chi gấp', 'DCM-26-11-00001')] },
    { ngay: '2026-11-18', tong: 60000000, con_lai: soDu == null ? null : 30000000, thieu: 0, muc: [MUC('may', 'Máy đề xuất', '2026-11-18', 60000000, 'Công nợ đến hạn', 'HDM-26-10-00900', { han: '2026-11-18', co: 'dung_han', dot: 'DC-26-11-20' })] },
    { ngay: '2026-11-20', tong: 40000000, con_lai: soDu == null ? null : -10000000, thieu: soDu == null ? null : 10000000, muc: [MUC('lich', 'Theo lịch hằng tháng', '2026-11-20', 40000000, 'Tiền nhà Nguyễn Hữu Phước', 'LC-00001')] }];
  return { hom_nay: '2026-11-13', den: '2026-12-18',
    so_du: soDu == null ? { so_tien: null, luc: '', nguon: 'Chưa đọc được số dư tài khoản chi từ SePay', chi_sau: 0 }
      : { so_tien: soDu, so_du_tk: soDu, chi_sau: 0, luc: '2026-11-13 09:30:00', nguon: 'Số dư tài khoản chi theo SePay' },
    ngay, tong: 110000000, thieu_dau: soDu == null ? null : { ngay: '2026-11-20', so_tien: 10000000 },
    can_thuong_luong: soDu == null ? [] : [ngay[1].muc[0]],
    lich_chi: [{ name: 'LC-00001', noi_dung: 'Tiền nhà', nguoi_nhan: 'Nguyễn Hữu Phước', so_tien: 40000000, ngay_trong_thang: 20, so_thang_thay: 3, ngoai_le: '' }],
    quyen: { sua: 1 } };
}
const GY = { thang_doc_duoc: ['2026-08', '2026-09', '2026-10', '2026-11'], goi_y: [
  { khoa: 'MA THANH SON', ten: 'MA THANH SON', so_thang: 3, thang: ['2026-09', '2026-10', '2026-11'], ngay_goi_y: 5, so_tien_goi_y: 37300000, ngoai_le: ['Tháng 10/2026 trả 2 lần (từng phần hoặc khoản lẻ)'], da_co: 0 },
  { khoa: 'Nguyễn Hữu Phước', ten: 'Nguyễn Hữu Phước', so_thang: 3, thang: ['2026-08', '2026-09', '2026-10'], ngay_goi_y: 20, so_tien_goi_y: 86900000, ngoai_le: [], da_co: 1 }] };

function chuanCham(a, chon, ten) {
  const html = a.than().innerHTML + ((a.tl.querySelector('.vf') || {}).innerHTML || '');
  const nho = (html.match(/font-size:\s*(\d+(?:\.\d+)?)px/g) || []).map(x => parseFloat(x.replace(/[^\d.]/g, ''))).filter(x => x < 13);
  assert.deepEqual(nho, [], ten + ': không có chữ nhỏ hơn 13 điểm');
  chon.forEach(sel => {
    const ds = a.tl.querySelectorAll(sel);
    assert(ds.length, ten + ': có ' + sel);
    ds.forEach(el => assert(/min-height:\s*4[4-9]px/.test(el.getAttribute('style') || ''), ten + ': ' + sel + ' cao ít nhất 44 điểm'));
  });
}

(async () => {
  {
    /* 1. Màn chính theo ảnh. */
    const a = appMoi(khoMay(), { l: lichAnh(100000000), gy: GY });
    await a.moMan();
    const t = a.than().innerHTML;
    assert(t.indexOf('Tiền khả dụng') >= 0 && t.indexOf('100000000 đ') >= 0, 'Tiền khả dụng 100 triệu');
    assert(t.indexOf('Số dư tài khoản chi theo SePay, đọc lúc 09:30 13/11') >= 0, 'nguồn và giờ đọc số dư');
    assert(t.indexOf('Tiền dự kiến về: chưa tính') >= 0, 'tách tiền dự kiến về, nói rõ chưa tính');
    assert(a.tl.getElementById('ldcThem'), 'có nút ＋ Thêm dự chi');
    assert(t.indexOf('⚠️ Ngày 20/11 còn thiếu 10000000 đ') >= 0, 'dòng cảnh báo ngày 20/11 thiếu 10 triệu');
    const lich = t.slice(t.indexOf('LỊCH DỰ CHI')), vt = s => lich.indexOf(s);
    assert(t.indexOf('Khoản có thể thương lượng dời: Công nợ đến hạn 60000000 đ (18/11)') >= 0, 'nêu khoản cần thương lượng');
    assert(vt('Chi gấp') < vt('Công nợ đến hạn') && vt('Công nợ đến hạn') < vt('Tiền nhà Nguyễn Hữu Phước'), 'ba khoản theo thứ tự ngày 15, 18, 20');
    ['Nhập tay', 'Máy đề xuất', 'Theo lịch hằng tháng'].forEach(c => assert(t.indexOf(c) >= 0, 'có chip ' + c));
    assert(t.indexOf('máy đề xuất trả đúng hạn. Dời sang đợt 11/20 là trễ') < 0, 'không hiện mã đợt lộn ngày');
    assert(t.indexOf('Hạn 18/11: máy đề xuất trả đúng hạn.') >= 0, 'khoản 18/11 nói rõ trả đúng hạn, không dồn sang 20');
    assert(t.indexOf('thiếu 10000000 đ</b>') >= 0, 'đầu ngày 20 ghi thiếu');
    assert(t.indexOf('Thu mua đang thương lượng') >= 0, 'đợt ghi tên bộ phận Thu mua');
    chuanCham(a, ['#ldcThem', '[data-ldcmo]', '[data-ldclich]', '#ldcThemLich', '#ldcGoiY', '[data-dcnxem]'], 'màn chính');
  }
  {
    /* 2. Thêm dự chi. */
    const a = appMoi(khoMay(), { l: lichAnh(100000000), gy: GY });
    await a.moMan();
    await a.bamId('ldcThem');
    assert(a.than().innerHTML.indexOf('Ngày cần chi') >= 0 && a.than().innerHTML.indexOf('Người nhận / Nhà cung cấp') >= 0, 'form đủ ô theo ảnh');
    chuanCham(a, ['#ldcNgay', '#ldcND', '#ldcTien', '#ldcNhan', '#ldcHD', '#ldcTimHD', '#ldcLuu'], 'form Thêm dự chi');
    a.dat('ldcNgay', '2026-11-15'); a.dat('ldcND', 'Chi gấp'); a.dat('ldcTien', '10.000.000'); a.dat('ldcNhan', 'Chợ Bến Thành'); a.dat('ldcLyDo', 'Hết bơ');
    await a.bamNut('ldcLuu');
    const l = a.goi.filter(x => x.m === 'vagabond.lich_du_chi.luu_muc');
    assert.equal(l.length, 1, 'Lưu dự chi nháp gọi máy chủ một lần');
    assert.deepEqual([l[0].a.ngay, l[0].a.noi_dung, l[0].a.so_tien, l[0].a.nguoi_nhan, l[0].a.ly_do, l[0].a.hoa_don, l[0].a.name],
      ['2026-11-15', 'Chi gấp', '10000000', 'Chợ Bến Thành', 'Hết bơ', '', ''], 'gửi đúng các ô, số bỏ dấu chấm');
  }
  {
    /* 3. Chưa đọc được số dư. */
    const a = appMoi(khoMay(), { l: lichAnh(null), gy: GY });
    await a.moMan();
    const t = a.than().innerHTML;
    assert(t.indexOf('Chưa xác định được khả năng chi') >= 0, 'nói rõ chưa xác định được');
    assert(t.indexOf('còn thiếu') < 0, 'không đoán thiếu tiền');
  }
  {
    /* 4. Gợi ý lịch hằng tháng. */
    const a = appMoi(khoMay(), { l: lichAnh(100000000), gy: GY });
    await a.moMan();
    await a.bamId('ldcGoiY');
    const t = a.than().innerHTML;
    assert(t.indexOf('Máy đọc 4 tháng có dữ liệu') >= 0, 'nói số tháng đọc được');
    assert(t.indexOf('Thấy 3 tháng: 09/26, 10/26, 11/26') >= 0, 'nói số tháng thấy');
    assert(t.indexOf('Tháng 10/2026 trả 2 lần') >= 0, 'nêu ngoại lệ');
    assert(t.indexOf('Đã có lịch') >= 0, 'tiền nhà đã có lịch thì không mời thêm');
    chuanCham(a, ['[data-lcgy]'], 'gợi ý');
    await a.bam(a.tl.querySelector('[data-lcgy="0"]'));
    assert.equal(a.tl.getElementById('lcNgay').value, '5', 'form lịch điền sẵn ngày 5');
    chuanCham(a, ['#lcND', '#lcNhan', '#lcTien', '#lcNgay', '#lcBat', '#lcLuu'], 'form lịch');
    await a.bamNut('lcBat');
    assert(a.tl.getElementById('lcBat').innerHTML.indexOf('tạm thôi tính') >= 0, 'bấm lần một: tạm thôi');
    await a.bamNut('lcBat');
    await a.bamNut('lcLuu');
    const l = a.goi.filter(x => x.m === 'vagabond.lich_du_chi.luu_lich');
    assert.deepEqual([l[0].a.noi_dung, l[0].a.so_tien, l[0].a.ngay_trong_thang, l[0].a.bat, l[0].a.so_thang_thay],
      ['MA THANH SON', '37300000', '5', 1, 3], 'lưu lịch đúng gợi ý');
  }
  console.log('PASS 654 Lịch dự chi: màn theo ảnh, Thêm dự chi, thiếu số dư, gợi ý lịch, chuẩn chạm');
})().catch(e => { console.error(e); process.exit(1); });

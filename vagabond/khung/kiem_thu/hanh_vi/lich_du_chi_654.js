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
    if (m === 'vagabond.lich_du_chi.chon_ncc') return [{ name: 'SUP-AN-PHU', ten: 'Bơ sữa An Phú', mst: '0301234567' }];
    if (m === 'vagabond.lich_du_chi.chon_hoa_don') return [{ name: 'HDM-26-11-00195', ncc: 'SUP-AN-PHU', ten: 'Bơ sữa An Phú', so: '8882', con_no: 820000 }];
    if (m === 'vagabond.lich_du_chi.chi_tiet_muc') return { name: a.name, ngay: '2026-11-15', noi_dung: 'Chi gấp', so_tien: 10000000, nguoi_nhan: 'Chợ', ly_do: '', hoa_don: '', trang_thai: 'Nhap', ho_so_app: '', nguon: 'Nhập tay', nha_cung_cap: '', ten_ncc: '' };
    if (m === 'vagabond.lich_du_chi.chon_app') return [{ name: 'APP.26.11.077', ten: 'Thợ', ngay: '2026-11-14', so_tien: 10000000, trang_thai: 'Chờ kế toán duyệt' }];
    if (m === 'vagabond.lich_du_chi.noi_app') return { name: a.name, ho_so_app: a.ho_so_app };
    if (m === 'vagabond.lich_du_chi.xoa_muc') return { name: a.name, da_xoa: 1 };
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
    'var __chon = {}; function hoiChon(t, m, ds) { __hop.push(["hoiChon", t, (ds || []).map(function (x) { return x.k; })]); return Promise.resolve(__chon[t] || "tiep"); }',
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
    /* Gõ thật: đặt chữ rồi phát sự kiện input như bàn phím (phần 48 nghe ở document). */
    async gõ(id, v) {
      const el = tl.getElementById(id); assert(el, 'thiếu ô ' + id); el.value = v;
      const ev = dom.suKien('input', {}, el); (nghe.input || []).forEach(f => f(ev)); el.dispatchEvent(ev); await nghi();
    },
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
    du_kien_ve: { trong_khung: 16000000, qua_han: 7000000, sau_khung: 5000000, tre_chung: 29, loi: '' },
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
    assert(t.indexOf('Tiền dự kiến về (công nợ cần thu): 16000000 đ trong khung') >= 0, 'tiền dự kiến về lấy từ công nợ cần thu');
    assert(t.indexOf('Khách quá hạn chưa trả 7000000 đ, không tính vào ngày nào') >= 0, 'nói rõ phần quá hạn không tính');
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
    assert(a.than().innerHTML.indexOf('Ngày cần chi') >= 0 && a.than().innerHTML.indexOf('Nhà cung cấp') >= 0 && a.than().innerHTML.indexOf('Người nhận khác') >= 0, 'form đủ ô theo ảnh');
    chuanCham(a, ['#ldcNgay', '#ldcND', '#ldcTien', '#ldcNcc', '#ldcNhan', '#ldcHDTim', '#ldcTimHD', '#ldcLuu'], 'form Thêm dự chi');
    a.dat('ldcNgay', '2026-11-15'); a.dat('ldcND', 'Chi gấp'); a.dat('ldcTien', '10.000.000'); a.dat('ldcNhan', 'Chợ Bến Thành'); a.dat('ldcLyDo', 'Hết bơ');
    await a.bamNut('ldcLuu');
    const l = a.goi.filter(x => x.m === 'vagabond.lich_du_chi.luu_muc');
    assert.equal(l.length, 1, 'Lưu dự chi nháp gọi máy chủ một lần');
    assert.deepEqual([l[0].a.ngay, l[0].a.noi_dung, l[0].a.so_tien, l[0].a.nguoi_nhan, l[0].a.ly_do, l[0].a.hoa_don, l[0].a.name, l[0].a.nha_cung_cap],
      ['2026-11-15', 'Chi gấp', '10000000', 'Chợ Bến Thành', 'Hết bơ', '', '', ''], 'gửi đúng các ô, số bỏ dấu chấm; người nhận khác không gắn nhà cung cấp');
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
    chuanCham(a, ['#lcND', '#lcNcc', '#lcNhan', '#lcTien', '#lcNgay', '#lcBat', '#lcLuu'], 'form lịch');
    await a.bamNut('lcBat');
    assert(a.tl.getElementById('lcBat').innerHTML.indexOf('tạm thôi tính') >= 0, 'bấm lần một: tạm thôi');
    await a.bamNut('lcBat');
    await a.bamNut('lcLuu');
    const l = a.goi.filter(x => x.m === 'vagabond.lich_du_chi.luu_lich');
    assert.deepEqual([l[0].a.noi_dung, l[0].a.so_tien, l[0].a.ngay_trong_thang, l[0].a.bat, l[0].a.so_thang_thay],
      ['MA THANH SON', '37300000', '5', 1, 3], 'lưu lịch đúng gợi ý');
  }
  {
    /* 5. Codex #561: nhà cung cấp chọn từ danh mục (QT-31), không gõ tự do. Chữ
       đang gõ không mất khi mở ô chọn; lưu gửi MÃ nhà cung cấp. */
    const a = appMoi(khoMay(), { l: lichAnh(100000000), gy: GY });
    await a.moMan();
    await a.bamId('ldcThem');
    a.dat('ldcNgay', '2026-11-15'); a.dat('ldcND', 'Trả bơ'); a.dat('ldcTien', '5.000.000');
    a.g.__chu = 'an phu'; a.g.__chon['Chọn nhà cung cấp'] = 'SUP-AN-PHU';
    await a.bamId('ldcNcc');
    const goiNcc = a.goi.filter(x => x.m === 'vagabond.lich_du_chi.chon_ncc');
    assert.deepEqual(goiNcc.map(x => x.a.tu_khoa), ['an phu'], 'tìm trong danh mục theo chữ gõ');
    assert(a.tl.getElementById('ldcNcc').innerHTML.indexOf('Bơ sữa An Phú') >= 0, 'nút chọn hiện tên nhà đã chọn');
    assert(!a.tl.getElementById('ldcNhan'), 'đã chọn nhà cung cấp thì không còn ô gõ tự do');
    assert.deepEqual([a.tl.getElementById('ldcNgay').value, a.tl.getElementById('ldcND').value, a.tl.getElementById('ldcTien').value],
      ['2026-11-15', 'Trả bơ', '5000000'], 'chữ đã gõ còn nguyên sau khi chọn');
    await a.bamNut('ldcLuu');
    const l = a.goi.filter(x => x.m === 'vagabond.lich_du_chi.luu_muc').pop();
    assert.deepEqual([l.a.nha_cung_cap, l.a.nguoi_nhan], ['SUP-AN-PHU', 'Bơ sữa An Phú'], 'lưu gửi mã nhà cung cấp');
  }
  {
    /* 6. Codex #561: form Thêm dự chi có bản nháp tự lưu. Gõ dở, tải lại trang:
       mở lại còn ngày, số tiền, người nhận, hoá đơn; không gọi lưu lên máy chủ. */
    const kho = khoMay();
    const a = appMoi(kho, { l: lichAnh(100000000), gy: GY });
    await a.moMan();
    await a.bamId('ldcThem');
    await a.gõ('ldcNgay', '2026-11-16'); await a.gõ('ldcND', 'Sửa lò'); await a.gõ('ldcTien', '7.500.000');
    await a.gõ('ldcNhan', 'Thợ điện Minh');
    await a.tua(2000);
    const khoa = Array.from(kho._m.keys()).filter(k => k.indexOf('vgbSoanDo:') === 0);
    assert.equal(khoa.length, 1, 'có đúng một bản nháp trên máy');
    assert.equal(a.goi.filter(x => /luu_muc|luu_lich/.test(x.m)).length, 0, 'bản nháp không tạo gì trên máy chủ');
    const b = appMoi(kho, { l: lichAnh(100000000), gy: GY });
    await b.moMan();
    await b.bamId('ldcThem'); await nghi(); await nghi();
    assert(b.hop.some(x => x[0] === 'hoiChon' && /đang soạn dở/.test(x[1])), 'hỏi mở tiếp bản đang soạn');
    assert.deepEqual(['ldcNgay', 'ldcND', 'ldcTien', 'ldcNhan'].map(id => b.tl.getElementById(id).value),
      ['2026-11-16', 'Sửa lò', '7.500.000', 'Thợ điện Minh'], 'mở lại còn đủ chữ đã gõ');
    assert.equal(b.goi.filter(x => /luu_muc|luu_lich/.test(x.m)).length, 0, 'mở lại cũng không tạo gì trên máy chủ');
    await b.bamNut('ldcLuu');
    await b.tua(2000);
    assert.equal(Array.from(kho._m.keys()).filter(k => k.indexOf('vgbSoanDo:') === 0).length, 0, 'lưu xong thì xoá bản nháp');
  }
  {
    /* 7. Codex #561: bản nháp giữ cả nhà cung cấp đã chọn (nằm ngoài ô gõ). */
    const kho = khoMay();
    const a = appMoi(kho, { l: lichAnh(100000000), gy: GY });
    await a.moMan();
    await a.bamId('ldcThem');
    await a.gõ('ldcND', 'Trả bơ');
    a.g.__chu = 'an phu'; a.g.__chon['Chọn nhà cung cấp'] = 'SUP-AN-PHU';
    await a.bamId('ldcNcc');
    await a.gõ('ldcTien', '5.000.000');
    /* Hoá đơn chọn từ kết quả tìm (QT-31), không gõ mã. */
    await a.gõ('ldcHDTim', 'an phu');
    await a.bamId('ldcTimHD');
    await a.bam(a.tl.querySelector('[data-ldchd="HDM-26-11-00195"]'));
    assert(a.tl.getElementById('ldcHDDa').innerHTML.indexOf('HDM-26-11-00195') >= 0, 'hiện hoá đơn đã chọn');
    assert.deepEqual([a.tl.getElementById('ldcND').value, a.tl.getElementById('ldcTien').value], ['Trả bơ', '5000000'], 'chọn hoá đơn không mất chữ đã gõ');
    await a.tua(2000);
    const b = appMoi(kho, { l: lichAnh(100000000), gy: GY });
    await b.moMan();
    await b.bamId('ldcThem'); await nghi(); await nghi();
    assert(b.tl.getElementById('ldcNcc').innerHTML.indexOf('Bơ sữa An Phú') >= 0, 'mở lại còn nhà cung cấp đã chọn');
    assert.deepEqual([b.tl.getElementById('ldcND').value, b.tl.getElementById('ldcTien').value], ['Trả bơ', '5000000'], 'và chữ đã gõ');
    assert(b.tl.getElementById('ldcHDDa').innerHTML.indexOf('HDM-26-11-00195') >= 0, 'mở lại còn hoá đơn đã chọn');
    await b.bamNut('ldcLuu');
    const l = b.goi.filter(x => x.m === 'vagabond.lich_du_chi.luu_muc').pop();
    assert.deepEqual([l.a.nha_cung_cap, l.a.hoa_don], ['SUP-AN-PHU', 'HDM-26-11-00195'], 'lưu sau khi mở lại vẫn gửi mã nhà cung cấp và hoá đơn');
  }
  {
    /* 8. Codex #561: form Lịch chi hằng tháng cũng có bản nháp tự lưu. */
    const kho = khoMay();
    const a = appMoi(kho, { l: lichAnh(100000000), gy: GY });
    await a.moMan();
    await a.bamId('ldcThemLich');
    await a.gõ('lcND', 'Tiền điện'); await a.gõ('lcNhan', 'EVN'); await a.gõ('lcTien', '3.200.000'); await a.gõ('lcNgay', '7');
    await a.tua(2000);
    assert.equal(a.goi.filter(x => /luu_lich/.test(x.m)).length, 0, 'chưa lưu lên máy chủ');
    const b = appMoi(kho, { l: lichAnh(100000000), gy: GY });
    await b.moMan();
    await b.bamId('ldcThemLich'); await nghi(); await nghi();
    assert.deepEqual(['lcND', 'lcNhan', 'lcTien', 'lcNgay'].map(id => b.tl.getElementById(id).value), ['Tiền điện', 'EVN', '3.200.000', '7'],
      'mở lại form lịch còn đủ chữ đã gõ');
  }
  {
    /* 9. Codex #561: lịch tạm thôi vẫn hiện để bật lại; gợi ý trỏ thẳng vào lịch đó. */
    const l = lichAnh(100000000);
    l.lich_chi.push({ name: 'LC-00002', noi_dung: 'Tiền điện', nguoi_nhan: 'EVN', nha_cung_cap: '', so_tien: 3200000, ngay_trong_thang: 7,
      so_thang_thay: 3, ngoai_le: '', bat: 0 });
    l.lich_chi[0].bat = 1;
    const gy = JSON.parse(JSON.stringify(GY));
    gy.goi_y.push({ khoa: 'EVN', ten: 'EVN', so_thang: 3, thang: ['2026-08', '2026-09', '2026-10'], ngay_goi_y: 7, so_tien_goi_y: 3200000,
      ngoai_le: [], da_co: 1, da_tat: 1, lich: 'LC-00002', ncc: '' });
    const a = appMoi(khoMay(), { l, gy });
    await a.moMan();
    const t = a.than().innerHTML;
    assert(t.indexOf('Đang tạm thôi tính, bấm để mở và dùng lại') >= 0, 'lịch tạm thôi vẫn hiện trong danh sách');
    await a.bam(a.tl.querySelector('[data-ldclich="LC-00002"]'));
    assert(a.tl.getElementById('lcBat').innerHTML.indexOf('Đang tạm thôi') >= 0, 'mở ra đúng trạng thái tạm thôi');
    await a.bamNut('lcBat');
    await a.bamNut('lcLuu');
    const s = a.goi.filter(x => x.m === 'vagabond.lich_du_chi.luu_lich').pop();
    assert.deepEqual([s.a.name, s.a.bat], ['LC-00002', 1], 'bật lại và lưu đúng lịch');
    const c = appMoi(khoMay(), { l, gy });
    await c.moMan();
    await c.bamId('ldcGoiY');
    const mo = c.tl.querySelector('[data-lcmo="LC-00002"]');
    assert(mo, 'gợi ý có nút mở lại lịch đang tạm thôi');
    chuanCham(c, ['[data-lcmo]'], 'gợi ý mở lại');
    await c.bam(mo);
    assert.equal(c.tl.getElementById('lcND').value, 'Tiền điện', 'mở đúng lịch tạm thôi từ gợi ý');
  }
  {
    /* 10. Codex #561 cùng loại QT-31: nối hồ sơ thanh toán bằng ô chọn, không gõ mã APP. */
    const a = appMoi(khoMay(), { l: lichAnh(100000000), gy: GY });
    await a.moMan();
    await a.bam(a.tl.querySelector('[data-ldcmo="tay|DCM-26-11-00001"]'));
    assert(!a.tl.getElementById('ldcApp'), 'không còn ô gõ mã APP');
    chuanCham(a, ['#ldcNoi', '#ldcNcc'], 'form Sửa dự chi');
    a.g.__chu = 'thợ'; a.g.__chon['Chọn hồ sơ thanh toán'] = 'APP.26.11.077';
    await a.bamId('ldcNoi');
    const n = a.goi.filter(x => x.m === 'vagabond.lich_du_chi.noi_app').pop();
    assert.deepEqual([n.a.name, n.a.ho_so_app], ['DCM-26-11-00001', 'APP.26.11.077'], 'nối đúng hồ sơ đã chọn');
  }
  {
    /* 11. Codex #561: sửa một dự chi đã có, gõ dở rồi tải lại trang: mở lại đúng
       dự chi đó còn chữ đang sửa, số máy chủ không đè lên. */
    const kho = khoMay();
    const a = appMoi(kho, { l: lichAnh(100000000), gy: GY });
    await a.moMan();
    await a.bam(a.tl.querySelector('[data-ldcmo="tay|DCM-26-11-00001"]'));
    a.g.__chu = 'an phu'; a.g.__chon['Chọn nhà cung cấp'] = 'SUP-AN-PHU';
    await a.bamId('ldcNcc');
    await a.gõ('ldcND', 'Chi gấp mua bơ thêm');
    await a.tua(2000);
    const b = appMoi(kho, { l: lichAnh(100000000), gy: GY });
    await b.moMan();
    await b.bam(b.tl.querySelector('[data-ldcmo="tay|DCM-26-11-00001"]')); await nghi(); await nghi();
    assert.equal(b.tl.getElementById('ldcND').value, 'Chi gấp mua bơ thêm', 'mở lại dự chi đang sửa còn chữ đã gõ');
    assert(b.tl.getElementById('ldcNcc').innerHTML.indexOf('Bơ sữa An Phú') >= 0, 'còn nhà cung cấp đã chọn khi sửa');
    await b.bamNut('ldcLuu');
    const l = b.goi.filter(x => x.m === 'vagabond.lich_du_chi.luu_muc').pop();
    assert.deepEqual([l.a.name, l.a.noi_dung, l.a.nha_cung_cap], ['DCM-26-11-00001', 'Chi gấp mua bơ thêm', 'SUP-AN-PHU'], 'lưu đúng dự chi đang sửa');
  }
  {
    /* 12. anh Việt 13/11: Thu mua không biết số dư. Máy chủ đã bỏ số; màn không hiện
       số nào, vẫn báo ngày không đủ tiền và khoản cần thương lượng. */
    const l = lichAnh(100000000);
    l.so_du = { an: 1 }; l.du_kien_ve = { an: 1 };
    l.ngay = l.ngay.map(g => Object.assign({}, g, { con_lai: null, thieu: null, ve: null, khong_du: g.thieu ? 1 : 0 }));
    l.thieu_dau = { ngay: '2026-11-20', so_tien: null };
    const a = appMoi(khoMay(), { l, gy: GY });
    await a.moMan();
    const t = a.than().innerHTML;
    assert(t.indexOf('Chỉ Giám đốc và người được xem mục Tài chính thấy số này') >= 0, 'nói rõ ai thấy số');
    assert(t.indexOf('100000000') < 0 && t.indexOf('còn 90000000') < 0, 'không có số dư, không có số còn lại');
    assert(t.indexOf('⚠️ Ngày 20/11 không đủ tiền chi') >= 0, 'vẫn báo ngày không đủ tiền');
    assert(t.indexOf('không đủ tiền</b>') >= 0, 'ngày 20 ghi không đủ tiền, không ghi số');
    assert(t.indexOf('Khoản có thể thương lượng dời') >= 0, 'vẫn nêu khoản cần thương lượng');
  }
  {
    /* 13. Tiền về hiện ở đầu ngày. */
    const l = lichAnh(100000000);
    l.ngay[2].ve = 16000000;
    const a = appMoi(khoMay(), { l, gy: GY });
    await a.moMan();
    assert(a.than().innerHTML.indexOf('chi 40000000 đ · về 16000000 đ') >= 0, 'ngày 20 ghi tiền về');
  }
  {
    /* 14. anh Việt 13/11: nút Xoá dự chi nháp xoá hẳn. */
    const a = appMoi(khoMay(), { l: lichAnh(100000000), gy: GY });
    await a.moMan();
    await a.bam(a.tl.querySelector('[data-ldcmo="tay|DCM-26-11-00001"]'));
    assert(!a.tl.getElementById('ldcHuy'), 'không còn nút Huỷ');
    chuanCham(a, ['#ldcXoa'], 'nút Xoá dự chi nháp');
    await a.bamId('ldcXoa');
    assert(a.hop.some(x => x[0] === 'confirm' && /Xoá dự chi nháp/.test(x[1])), 'hỏi lại trước khi xoá');
    const x = a.goi.filter(g => g.m === 'vagabond.lich_du_chi.xoa_muc');
    assert.deepEqual(x.map(g => g.a.name), ['DCM-26-11-00001'], 'xoá đúng dự chi');
  }
  console.log('PASS 654 Lịch dự chi: màn theo ảnh, Thêm dự chi, thiếu số dư, gợi ý lịch, chuẩn chạm, chọn nhà cung cấp, bản nháp, lịch tạm thôi');
})().catch(e => { console.error(e); process.exit(1); });

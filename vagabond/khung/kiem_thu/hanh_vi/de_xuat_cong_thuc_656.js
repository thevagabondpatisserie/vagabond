/* v656 Phiếu đề xuất công thức (anh Việt 13/11/2026, chọn hướng A cho cả 3
   câu): chạy THẬT khung app (01) và màn phiếu (72) trong node, máy chủ giả.
   Chốt:
     1. Bếp lập phiếu mới: tên bánh, size 16 và 20, thành phần mới gõ tên thì
        máy báo mã gần giống, bấm dùng mã có sẵn; chip Vào đâu; gram size 16
        rồi Gợi ý size còn trống ra size 20 theo diện tích khuôn (100 g thành
        156 g), dòng thành phẩm giữ nguyên.
     2. Lưu nháp gửi đúng dữ liệu; máy chủ trả giá vốn và dòng thiếu giá, màn
        hiện chữ đỏ Thiếu giá. Gửi Khải gọi lưu rồi gửi.
     3. Khải mở phiếu Chờ Khải: chọn mã thành phẩm từng size, Tạo mã và công
        thức gửi đúng mã từng size; thiếu mã size nào thì màn ghi đỏ.
     4. Đề xuất điều chỉnh: lấy dòng từ công thức đang dùng, sửa số lượng, Lưu
        ra bảng trước và sau kèm giá vốn; Khải bấm Duyệt và ghi sổ.
     5. Chuẩn chạm: mọi nút, ô, chip mới cao từ 44 điểm, chữ từ 13 điểm.
     6. Rời màn khi máy chủ chưa trả mã gần giống: không vẽ đè màn mới.
     7. Codex #563: danh sách có tìm và trang; Khải sửa rồi Tạo, Duyệt thì lưu
        trước; Gửi Khải hỏng thì bấm lại vẫn là phiếu đã lưu. */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert');
const dom = require('./dom_gia.js');
const BEP = path.resolve(__dirname, '../../../public/js/bep');
const doc = n => fs.readFileSync(path.join(BEP, n), 'utf8');
const KHUNG = doc('01-khung-app.js'), DX = doc('72-de-xuat-cong-thuc.js');
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
/* Thanh công cụ danh sách dùng chung, nạp THẬT từ 15, 09, 13. */
const K15 = doc('15-khuon-danh-sach.js');
const CONG_CU = [K15.match(/^var DS_KY = [\s\S]*?\]\];$/m)[0], layHam(K15, 'dsccHang'), layHam(K15, 'dsCongCu'), layHam(K15, 'dsCongCuNoi'),
  layHam(doc('09-tinh-tien-quay.js'), 'posChipNut'), layHam(doc('13-khuyen-mai.js'), 'kmHangChip')].join('\n');

async function nghi() { for (let i = 0; i < 12; i++) await Promise.resolve(); await new Promise(r => setImmediate(r)); }
const sao = x => JSON.parse(JSON.stringify(x));

function appMoi(may, vai) {
  const tl = dom.taiLieuGia();
  tl.addEventListener = () => {};
  tl.createEvent = () => ({ initEvent(t) { this.type = t; } });
  const vgb = tl.createElement('div'); vgb.id = 'vgb'; tl.body.appendChild(vgb);
  let hen = [], soHen = 0, bayGio = 1790000000000;
  const goi = [];
  const g = { console, JSON, Math, Number, String, Object, Array, Promise, Error, RegExp, parseFloat, parseInt, isNaN, isFinite, Date,
    document: tl, frappe: { session: { user: 'han@vagabond.vn' } },
    location: { href: 'https://app.x/bep', pathname: '/bep', hostname: 'app.x', search: '', hash: '', replace() {} },
    history: { pushState() {}, replaceState() {}, back() {} }, requestAnimationFrame: f => f(),
    setTimeout: (f, ms) => { soHen++; hen.push({ id: soHen, f, luc: bayGio + (ms || 0) }); return soHen; },
    clearTimeout: id => { hen = hen.filter(x => x.id !== id); }, addEventListener() {} };
  g.window = g; g.localStorage = { getItem: () => null, setItem() {}, removeItem() {}, key: () => null, length: 0 };
  vm.createContext(g);
  g.__api = async (m, a) => { goi.push({ m, a: sao(a || {}) }); const f = may[m.split('.').pop()]; return f ? sao(await f(a)) : {}; };
  g.__chonMa = [];
  vm.runInContext([
    'var root = document.getElementById("vgb");',
    'function h(s) { return String(s == null ? "" : s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;"); }',
    'var __tin = []; function toast(s) { __tin.push(String(s)); } function busy() {}',
    'function dSkin() {} function money(x) { return String(Math.round(Number(x) || 0)); } function num(x) { return String(x); }',
    'function errMsg(e) { return String((e && e.message) || e); }',
    'function confirmSheet() { return Promise.resolve(true); } function promptSheet() { return Promise.resolve("16 hay 18?"); }',
    'function sheet(t, ds, c, f) { f(ds[0]); }',
    'function leavesUnder(r) { return r; }',
    'function mfgPickItem(t, g, cb) { cb(__chonMa.shift()); }',
    'function api(m, a) { return __api(m, a); }',
    'var __vai = ' + JSON.stringify(vai) + ';',
    'function ctGhiSoDuoc() { return __vai.indexOf("ghi") >= 0; }',
    'function scrCongThucXem() {} async function scrHome() { frame(APPNAME, "<div></div>"); }',
  ].join('\n'), g);
  vm.runInContext(KHUNG, g);
  vm.runInContext(CONG_CU, g);
  vm.runInContext(DX, g);
  const than = () => tl.getElementById('vgbBody');
  const a = {
    g, tl, goi, than,
    html() { return than().innerHTML + ((tl.querySelector('.vf') || {}).innerHTML || ''); },
    async tua(ms) { bayGio += ms; for (let v = 0; v < 20; v++) { const toi = hen.filter(x => x.luc <= bayGio); if (!toi.length) break; hen = hen.filter(x => x.luc > bayGio); toi.forEach(x => x.f()); await nghi(); } },
    async bam(sel) { const el = tl.querySelector(sel); assert(el, 'thiếu chỗ bấm ' + sel); await than().onclick({ target: el }); await nghi(); await nghi(); },
    async nut(id) { const el = tl.getElementById(id); assert(el, 'thiếu nút ' + id); assert(el.onclick, 'nút ' + id + ' chưa nối'); await el.onclick(); await nghi(); await nghi(); await nghi(); },
    async go(sel, v) { const el = tl.querySelector(sel); assert(el, 'thiếu ô ' + sel); el.value = v; await than().oninput({ target: el }); await nghi(); },
    async mo(fn) { await g.reset(g.scrHome); await nghi(); await fn(); await nghi(); await nghi(); await nghi(); },
  };
  return a;
}

function chuanCham(a, chon, ten) {
  const nho = (a.html().match(/font-size:\s*(\d+(?:\.\d+)?)px/g) || []).map(x => parseFloat(x.replace(/[^\d.]/g, ''))).filter(x => x < 13);
  assert.deepEqual(nho, [], ten + ': không có chữ nhỏ hơn 13 điểm');
  chon.forEach(sel => {
    const ds = a.tl.querySelectorAll(sel);
    assert(ds.length, ten + ': có ' + sel);
    ds.forEach(el => {
      const m = (el.getAttribute('style') || '').match(/(?:^|;|\s)(?:min-)?height:\s*(\d+)px/);
      assert(m && +m[1] >= 44, ten + ': ' + sel + ' cao ít nhất 44 điểm');
    });
  });
}

const PHIEU = (tt, dl, them) => Object.assign({ name: 'DXCT-26-11-0001', loai: 'Mới', ten_banh: 'Bánh Pinkpom bưởi', trang_thai: tt, du_lieu: dl,
  bom_goc: '', ly_do: '', ghi_chu_khai: '', nguoi_de_xuat: 'han@vagabond.vn', ten_nguoi_de_xuat: 'Hân', ket_qua: {},
  gia: { '16': { von: 152000, ban: 0, ty_le: 0, ma_tp: '', ten_tp: '' }, '20': { von: 0, ban: 0, ty_le: 0, ma_tp: '', ten_tp: '' } },
  thieu_gia: ['Bột bưởi'], quyen: { sua: 1, duyet: 0 } }, them || {});

(async () => {
  {
    /* 1 và 2. Bếp lập phiếu mới. */
    let daLuu = null;
    const may = {
      danh_sach: a => ({ ds: a.tim ? [] : [{ name: 'DXCT-26-11-0009', loai: 'Mới', ten_banh: 'Bánh cũ', trang_thai: 'Nháp', ten_nguoi_de_xuat: 'Hân', modified: '2026-11-13 09:00' }],
        dem: { tat_ca: 120, 'Nháp': 70, 'Đã ghi sổ': 50 }, con_nua: a.trang ? 0 : 1 }),
      goi_y_ma: () => [{ ma: 'BTPB-0012', ten: 'Mousse bưởi hồng', dvt: 'Gram', diem: 3 }],
      luu: a => { daLuu = JSON.parse(a.du_lieu); return PHIEU('Nháp', daLuu); },
      gui: () => PHIEU('Chờ Khải', daLuu, { quyen: { sua: 0, duyet: 0 } }),
      /* Máy chủ giả trả đúng số goi_y_cac_size tính (ca Python chốt phép tính). */
      goi_y_size_dong: a => { const d = JSON.parse(a.dong), g = Object.assign({}, d.gram);
        g['20'] = d.dich === 'thanh_pham' ? g['16'] : Math.round(g['16'] * 400 / 256); return { goc: '16', gram: g }; },
    };
    const a = appMoi(may, ['soan']);
    await a.mo(() => a.g.go(a.g.scrDxDs));
    chuanCham(a, ['#dxDsTim', '[data-dxmo]', '#dxTruoc', '#dxSau'], 'danh sách');
    assert(a.html().indexOf('Nháp <b>70</b>') >= 0, 'chip trạng thái có đếm');
    /* Codex #563: hơn 50 phiếu thì có Trang sau; tìm theo mã hay tên lọc ở máy chủ. */
    await a.nut('dxSau');
    assert.deepEqual(a.goi.filter(x => x.m.endsWith('danh_sach')).map(x => x.a.trang), [0, 1], 'Trang sau hỏi trang 1');
    const oTim = a.tl.getElementById('dxDsTim'); oTim.value = 'DXCT-26-10-0001';
    oTim.dispatchEvent(dom.suKien('change', {}, oTim)); await nghi(); await nghi();
    const cuoi = a.goi.filter(x => x.m.endsWith('danh_sach')).pop().a;
    assert.deepEqual([cuoi.tim, cuoi.trang], ['DXCT-26-10-0001', 0], 'tìm gửi máy chủ, về trang đầu');
    assert(a.html().indexOf('Không có phiếu khớp bộ lọc') >= 0, 'không thấy thì nói cách mở rộng');
    a.g.dxMoi(); await nghi(); await nghi();
    await a.go('#dxTen', 'Bánh Pinkpom bưởi');
    await a.bam('[data-dxsize="16"]'); await a.bam('[data-dxsize="20"]');
    await a.nut('dxThemMoi'); await a.nut('dxThemMoi');
    const o = Array.from(a.tl.querySelectorAll('[data-dxten]'));
    const id1 = o[0].getAttribute('data-dxten'), id2 = o[1].getAttribute('data-dxten');
    await a.go('[data-dxten="' + id1 + '"]', 'mousse buoi');
    await a.tua(300);
    assert.equal(a.goi.filter(x => x.m.endsWith('goi_y_ma')).length, 0, 'chưa gọi tìm khi đang gõ dở (chờ ngừng gõ)');
    await a.tua(500);
    assert.deepEqual(a.goi.filter(x => x.m.endsWith('goi_y_ma')).map(x => x.a.ten), ['mousse buoi'], 'gõ xong mới tìm mã gần giống một lần');
    assert(a.html().indexOf('Đã có mã gần giống') >= 0 && a.html().indexOf('Mousse bưởi hồng') >= 0, 'báo mã gần giống');
    chuanCham(a, ['[data-dxdung]', '[data-dxboqua]', '[data-dxsize]', '[data-dxdich]', '[data-dxg]', '[data-dxbo]', '[data-dxgy]', '[data-dxme]', '[data-dxcco]', '[data-dxcmoi]', '#dxTen', '#dxLuu', '#dxGui', '#dxThemCo', '#dxThemMoi', '#dxSizeKhac'], 'phiếu mới');
    await a.bam('[data-dxdung="' + id1 + '|BTPB-0012"]');
    assert(a.html().indexOf('BTPB-0012 · mã có sẵn') >= 0, 'bấm dùng mã có sẵn');
    await a.bam('[data-dxdich="' + id1 + '|cap1"]');
    await a.go('[data-dxg="' + id1 + '|16"]', '100');
    await a.bam('[data-dxgy="' + id1 + '"]');
    assert.equal(a.tl.querySelector('[data-dxg="' + id1 + '|20"]').value, '156', 'gợi ý size 20 theo diện tích khuôn');
    const gy = a.goi.filter(x => x.m.endsWith('goi_y_size_dong'))[0].a;
    assert.deepEqual([JSON.parse(gy.dong), JSON.parse(gy.sizes)], [{ dich: 'cap1', gram: { '16': 100 } }, ['16', '20']], 'hỏi máy chủ đúng dòng và size');
    await a.go('[data-dxten="' + id2 + '"]', 'Hoa trang trí');
    await a.tua(800);
    await a.bam('[data-dxdich="' + id2 + '|thanh_pham"]');
    await a.go('[data-dxg="' + id2 + '|16"]', '3');
    await a.bam('[data-dxgy="' + id2 + '"]');
    assert.equal(a.tl.querySelector('[data-dxg="' + id2 + '|20"]').value, '3', 'dòng thành phẩm không nhân theo diện tích');
    await a.nut('dxLuu');
    const l = a.goi.filter(x => x.m.endsWith('.luu'));
    assert.equal(l.length, 1, 'Lưu nháp gọi máy chủ một lần');
    assert.equal(l[0].a.ten_banh, 'Bánh Pinkpom bưởi');
    assert.deepEqual(daLuu.sizes, ['16', '20']);
    assert.deepEqual(daLuu.dong.map(x => [x.ma || '', x.ten, x.dich, x.gram['16'], x.gram['20']]),
      [['BTPB-0012', 'Mousse bưởi hồng', 'cap1', 100, 156], ['', 'Hoa trang trí', 'thanh_pham', 3, 3]], 'gửi đúng dòng, vào đâu, gram');
    assert(a.html().indexOf('⚠️ Thiếu giá 1 nguyên liệu: Bột bưởi.') >= 0, 'thiếu giá hiện chữ đỏ');
    assert(a.html().indexOf('152000 đ') >= 0, 'hiện giá vốn dự kiến máy chủ tính');
    await a.nut('dxGui');
    assert.deepEqual(a.goi.slice(-2).map(x => x.m.split('.').pop()), ['luu', 'gui'], 'Gửi Khải lưu trước rồi gửi');
    assert(a.html().indexOf('Chờ Khải') >= 0 && !a.tl.getElementById('dxGui'), 'gửi xong thành Chờ Khải, hết nút sửa');
  }
  {
    /* 3. Khải lên mã. */
    const dl = { sizes: ['16', '20'], dong: [{ id: 'd1', ten: 'Mousse bưởi', dvt: 'Gram', dich: 'cap1', gram: { '16': 100, '20': 156 }, con: { me: 500, dong: [] } }] };
    let khaiLuu = null;
    const may = { chi_tiet: () => PHIEU('Chờ Khải', dl, { quyen: { sua: 1, duyet: 1 } }),
      luu: a => { khaiLuu = JSON.parse(a.du_lieu); return PHIEU('Chờ Khải', khaiLuu, { quyen: { sua: 1, duyet: 1 } }); },
      get_value: () => ({ item_name: 'Bánh Pinkpom size 16' }),
      tao_nhap: a => PHIEU('Đã tạo nháp', dl, { quyen: { sua: 0, duyet: 1 }, ket_qua: { bom: [{ bom: 'BOM-BTPB-0099-001', ma: 'BTPB-0099', bac: 0 }] } }) };
    const a = appMoi(may, ['ghi']);
    await a.mo(() => a.g.dxMo('DXCT-26-11-0001'));
    assert((a.html().match(/chưa chọn mã thành phẩm/g) || []).length === 2, 'hai size chưa có mã thì ghi đỏ cả hai');
    chuanCham(a, ['[data-dxtp]', '#dxTra', '#dxTao'], 'phần Khải');
    a.g.__chonMa.push('TP-PINK-16'); await a.bam('[data-dxtp="16"]');
    a.g.__chonMa.push('TP-PINK-20'); await a.bam('[data-dxtp="20"]');
    assert((a.html().match(/chưa chọn mã thành phẩm/g) || []).length === 0, 'chọn đủ mã');
    /* Codex #563: Khải sửa gram rồi bấm Tạo ngay: phần sửa phải lưu TRƯỚC. */
    await a.go('[data-dxg="d1|20"]', '150');
    await a.nut('dxTao');
    assert.deepEqual(a.goi.slice(-2).map(x => x.m.split('.').pop()), ['luu', 'tao_nhap'], 'lưu phần Khải sửa rồi mới tạo');
    assert.equal(khaiLuu.dong[0].gram['20'], 150, 'máy chủ nhận đúng số Khải vừa sửa');
    const t = a.goi.filter(x => x.m.endsWith('tao_nhap'));
    assert.equal(t.length, 1);
    assert.deepEqual(JSON.parse(t[0].a.ma_thanh_pham), { '16': 'TP-PINK-16', '20': 'TP-PINK-20' }, 'gửi đúng mã từng size');
    assert(a.tl.getElementById('dxGhiSo') && a.html().indexOf('BOM-BTPB-0099-001') >= 0, 'Đã tạo nháp: hiện công thức đã tạo và nút Ghi sổ tất cả');
    chuanCham(a, ['#dxGhiSo', '[data-dxbom]'], 'đã tạo nháp');
  }
  {
    /* 4. Đề xuất điều chỉnh. */
    let dl = null;
    const tu = { ten_banh: 'Bánh Ổ Very Berry', du_lieu: { sizes: [], dong: [{ id: 'd1', ma: 'NVL-BO', ten: 'Bơ', dvt: 'Gram', gram: { '': 200 } }] }, me: 1, dvt: 'Cái' };
    const dc = d => PHIEU('Nháp', d, { loai: 'Điều chỉnh', ten_banh: 'Bánh Ổ Very Berry', bom_goc: 'BOM-X-001', ly_do: 'Bớt béo', gia: {}, thieu_gia: ['Bột bưởi'],
      doi_chieu: { bang: [{ ma: 'NVL-BO', ten: 'Bơ', cu: 200, moi: 180, kieu: 'doi' }], von_cu: 50000, von_moi: 46000 } });
    const may = { tu_cong_thuc: () => tu, luu: a => { dl = JSON.parse(a.du_lieu); return dc(dl); } };
    const a = appMoi(may, ['soan']);
    await a.mo(() => a.g.dxDieuChinh('BOM-X-001'));
    assert(!a.tl.querySelector('[data-dxdich]') && !a.tl.querySelector('[data-dxsize]'), 'điều chỉnh không có chip size, vào đâu');
    await a.go('[data-dxg="d1|"]', '180');
    await a.go('#dxLyDo', 'Bớt béo');
    await a.nut('dxLuu');
    const l = a.goi.filter(x => x.m.endsWith('.luu'))[0].a;
    assert.deepEqual([l.loai, l.bom_goc, l.ly_do, dl.dong[0].gram['']], ['Điều chỉnh', 'BOM-X-001', 'Bớt béo', 180], 'lưu đúng phiếu điều chỉnh');
    assert(a.html().indexOf('Bơ (đổi)') >= 0 && ['<b>50000 đ</b>', '<b>46000 đ</b>', '(-4000 đ)'].every(c => a.html().indexOf(c) >= 0), 'bảng trước sau và giá vốn chênh');
    assert(a.html().indexOf('⚠️ Thiếu giá 1 nguyên liệu: Bột bưởi.') >= 0, 'Codex #563: phiếu điều chỉnh cũng ghi đỏ dòng thiếu giá');
    chuanCham(a, ['[data-dxg]', '#dxLyDo', '#dxLuu', '#dxGui', '#dxHuy'], 'điều chỉnh');
    let dl2 = null;
    const may2 = { chi_tiet: () => Object.assign(dc(dl), { trang_thai: 'Chờ Khải', quyen: { sua: 1, duyet: 1 } }),
      luu: a => { dl2 = JSON.parse(a.du_lieu); return Object.assign(dc(dl2), { trang_thai: 'Chờ Khải', quyen: { sua: 1, duyet: 1 } }); },
      duyet_dieu_chinh: () => Object.assign(dc(dl), { trang_thai: 'Đã ghi sổ', quyen: { sua: 0, duyet: 1 } }) };
    const k = appMoi(may2, ['ghi']);
    await k.mo(() => k.g.dxMo('DXCT-26-11-0001'));
    await k.go('[data-dxg="d1|"]', '170');
    await k.nut('dxDuyet');
    assert.deepEqual(k.goi.slice(-2).map(x => x.m.split('.').pop()), ['luu', 'duyet_dieu_chinh'], 'lưu phần Khải sửa rồi mới duyệt');
    assert.equal(dl2.dong[0].gram[''], 170, 'duyệt đúng số đang hiện');
    assert.equal(k.goi.filter(x => x.m.endsWith('duyet_dieu_chinh')).length, 1, 'Khải duyệt và ghi sổ');
    assert(k.html().indexOf('Đã ghi sổ') >= 0, 'phiếu thành Đã ghi sổ');
  }
  {
    /* 5. Gõ tên rồi rời màn trước khi máy chủ trả mã gần giống: không vẽ đè màn mới. */
    const may = { danh_sach: () => [], goi_y_ma: () => [{ ma: 'BTPB-0012', ten: 'Mousse bưởi hồng', dvt: 'Gram' }] };
    const a = appMoi(may, ['soan']);
    await a.mo(() => a.g.go(a.g.scrDxDs));
    a.g.dxMoi(); await nghi(); await nghi();
    await a.nut('dxThemMoi');
    const id1 = a.tl.querySelector('[data-dxten]').getAttribute('data-dxten');
    await a.go('[data-dxten="' + id1 + '"]', 'mousse buoi');
    await a.g.scrDxDs(); await nghi(); await nghi();
    await a.tua(800);
    assert.equal(a.goi.filter(x => x.m.endsWith('goi_y_ma')).length, 1, 'vẫn hỏi máy chủ');
    assert(a.html().indexOf('Đã có mã gần giống') < 0 && !a.tl.querySelector('[data-dxten]'), 'màn danh sách không bị vẽ đè bằng phiếu cũ');
  }
  {
    /* 6. Codex #563: Gửi Khải hỏng lần đầu (phiếu thiếu) thì bấm lại vẫn là
       phiếu đã lưu, không đẻ thêm phiếu. */
    let lanGui = 0;
    const may = { luu: a => PHIEU('Nháp', JSON.parse(a.du_lieu), { name: a.name || 'DXCT-26-11-0042' }),
      gui: () => { if (!lanGui++) throw new Error('Phiếu còn thiếu: Chọn ít nhất một size.'); return PHIEU('Chờ Khải', { sizes: ['16'], dong: [] }, { name: 'DXCT-26-11-0042', quyen: { sua: 0, duyet: 0 } }); } };
    const a = appMoi(may, ['soan']);
    await a.mo(() => { a.g.dxMoi(); });
    await a.go('#dxTen', 'Bánh thử');
    await a.nut('dxGui');
    assert(a.g.__tin.some(t => t.indexOf('Phiếu còn thiếu') >= 0), 'báo lỗi gửi');
    await a.nut('dxGui');
    const luu = a.goi.filter(x => x.m.endsWith('.luu')).map(x => x.a.name);
    assert.deepEqual(luu, [null, 'DXCT-26-11-0042'], 'lần hai lưu vào đúng phiếu đã có');
    assert(a.html().indexOf('Chờ Khải') >= 0, 'lần hai gửi được');
  }
  {
    /* 7. Codex #564 (AGENTS 2b.17): khối chỉ để đọc không lấn khối để bấm.
       Phiếu có 6 nguyên liệu thiếu giá, 8 dòng: Khải thấy nút Tạo mã trước
       danh sách thành phần; cảnh báo thiếu giá chỉ một dòng đếm số, ba tên đầu,
       "và 3 nữa", nằm dưới nút; bấm mới mở đủ. Phiếu điều chỉnh 8 dòng mà chỉ
       đổi 1: bảng chỉ hiện dòng đổi, còn lại gom vào nút xem. */
    const ten = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6'];
    const dl = { sizes: ['16'], dong: ten.concat(['B1', 'B2']).map((t, i) => ({ id: 'd' + i, ma: 'M' + i, ten: t, dvt: 'Gram', dich: 'cap2', gram: { '16': 10 } })) };
    const may = { chi_tiet: () => PHIEU('Chờ Khải', dl, { quyen: { sua: 1, duyet: 1 }, thieu_gia: ten }) };
    const a = appMoi(may, ['ghi']);
    await a.mo(() => a.g.dxMo('DXCT-26-11-0001'));
    const ht = a.html();
    const iTao = ht.indexOf('id="dxTao"'), iTp = ht.indexOf('>Thành phần<'), iCb = ht.indexOf('⚠️ Thiếu giá');
    assert(iTao > 0 && iTao < iTp, 'nút Tạo mã và công thức nằm trước danh sách thành phần');
    assert(iCb > iTao, 'cảnh báo thiếu giá nằm dưới khối hành động');
    assert(ht.indexOf('⚠️ Thiếu giá 6 nguyên liệu: A1, A2, A3 và 3 nữa.') >= 0 && ht.indexOf('A1, A2, A3, A4') < 0, 'chỉ ba tên đầu và đếm phần còn lại');
    chuanCham(a, ['[data-dxmothieu]'], 'nút xem đủ thiếu giá');
    await a.bam('[data-dxmothieu]');
    assert(a.html().indexOf('A1, A2, A3, A4, A5, A6.') >= 0, 'bấm mới mở đủ');
    const bang = ten.concat(['B1', 'B2']).map((t, i) => ({ ma: 'M' + i, ten: t, cu: 10, moi: i === 7 ? 12 : 10, kieu: i === 7 ? 'doi' : 'giu' }));
    const may2 = { chi_tiet: () => PHIEU('Chờ Khải', { sizes: [], dong: [] }, { loai: 'Điều chỉnh', bom_goc: 'BOM-X-001', quyen: { sua: 0, duyet: 1 }, gia: {}, thieu_gia: [],
      doi_chieu: { bang, von_cu: 1000, von_moi: 1020, thieu: [] } }) };
    const k = appMoi(may2, ['ghi']);
    await k.mo(() => k.g.dxMo('DXCT-26-11-0001'));
    const hk = k.html();
    assert(hk.indexOf('B2 (đổi)') >= 0 && hk.indexOf('>A1<') < 0, 'bảng chỉ hiện dòng đổi');
    assert(hk.indexOf('id="dxDuyet"') < hk.indexOf('B2 (đổi)'), 'nút Duyệt nằm trên bảng');
    assert(hk.indexOf('Xem cả 8 dòng (7 dòng đang ẩn)') >= 0, 'dòng giữ nguyên gom vào nút');
    await k.bam('[data-dxmobang]');
    assert(k.html().indexOf('>A1<') >= 0, 'bấm mới mở cả bảng');
  }
  {
    /* 8. Cùng loại trên màn Công thức: dòng Thiếu giá gọn một dòng. */
    const g = { h: x => String(x), money: x => String(x) };
    vm.createContext(g);
    vm.runInContext(layHam(doc('26-cong-thuc.js'), 'ctHopGiaVon'), g);
    const ht = g.ctHopGiaVon({ mot: 50000, ban: 0, thieu: ['A1', 'A2', 'A3', 'A4', 'A5'], dvt: 'Cái' });
    const dau = ht.split('<details')[0];
    assert(dau.indexOf('Thiếu giá 5 nguyên liệu: A1, A2, A3 và 2 nữa.') >= 0 && dau.indexOf('A4') < 0, 'màn Công thức: đếm số, ba tên đầu');
    /* Codex #564 vòng 2: phần còn lại bấm mới mở, không ẩn hẳn; ô bấm cao 44. */
    assert(/<details[^>]*><summary style="min-height:44px[^"]*">Xem đủ 5 nguyên liệu thiếu giá<\/summary><div[^>]*>A1, A2, A3, A4, A5<\/div><\/details>/.test(ht), 'có Xem đủ mở hết năm tên');
    assert(g.ctHopGiaVon({ mot: 1, thieu: ['A1'], dvt: 'Cái' }).indexOf('<details') < 0, 'ba tên trở xuống không cần nút');
  }
  console.log('de_xuat_cong_thuc_656: 8 nhóm ca đạt');
})().catch(e => { console.error(e); process.exit(1); });

/* v694 (giám đốc chốt 26/11/2026, Kho báo PNK-2026-01107): chạy nguyên màn Nhập kho
   (phiếu nháp) và Nhận hàng theo đơn trong DOM giả. Dòng chưa bấm Đã đếm mà số lượng
   lớn hơn 0 thì hỏi lại trước khi ghi; mặc định quay lại; tiếp tục chỉ bằng nút ghi rõ.
   Thêm phần chạy thật chonSheet của 00-nen.js. Không đo CSS. */
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const {taiLieuGia, ElementGia} = require('./dom_gia.js');
Object.defineProperty(ElementGia.prototype, 'classList', {get() { const e = this; return {add(k) { this.toggle(k, true); }, remove(k) { this.toggle(k, false); }, toggle(k, on) { const a = new Set((e.getAttribute('class') || '').split(' ')); if (on === undefined) on = !a.has(k); if (on) a.add(k); else a.delete(k); e.setAttribute('class', [...a].join(' ')); }}; }});

const MON = [
  {ma: 'CCDC90001', ten: 'Cây đánh trứng A', dvt: 'PC'},
  {ma: 'CCDC90002', ten: 'Xẻng gỗ B', dvt: 'PC'},
  {ma: 'CCDC90003', ten: 'Thìa gỗ C', dvt: 'Cái'},
];

async function man(cu, traLoi, danhDau) {
  const document = taiLieuGia(), goi = [], hoi = [];
  const tim = document.querySelector.bind(document);
  document.querySelector = sel => { const a = sel.split(' '); return a.length === 2 ? tim(a[0])?.querySelector(a[1]) : tim(sel); };
  const c = {document, console, Date, Math, JSON, Promise, setTimeout,
    today: () => '2026-11-26', addDays: (d, n) => d, h: x => String(x == null ? '' : x), num: String, dmy: String, shortWh: String,
    vgbCss: () => {}, busy: () => {}, toast: () => {}, errMsg: e => { throw e; }, back: () => {},
    getList: async dt => dt === 'Item' ? MON.map(m => ({name: m.ma, has_batch_no: 0, shelf_life_in_days: 0})) : [],
    confirmSheet: async () => true,
    chonSheet: async o => { hoi.push(o); return traLoi; },
    frame: (t, html, o = {}) => { document.body.innerHTML = ''; const b = new ElementGia('div'); b.setAttribute('id', 'vgbBody'); b.innerHTML = html + (o.footer || ''); b.parentNode = document.body; document.body.children.push(b); return b; },
    api: async (url, args) => {
      goi.push({url, args});
      if (url === 'frappe.client.get') return {doctype: 'Purchase Receipt', name: 'PNK-GIA-1', modified: 'm', items: MON.map((m, i) => ({name: 'D' + i, item_code: m.ma, item_name: m.ten, qty: 1, uom: m.dvt, rate: 1000, warehouse: 'K'}))};
      if (url === 'vagabond.nhan_hang.ghi_phieu_nhap') return {phieu: 'PNK-GIA-1'};
      if (url === 'vagabond.nhan_hang.chi_tiet') return {dot_toi: 1, ncc: 'NCC GIẢ', so_mon_con: 3, mon: MON.map((m, i) => ({dong: 'D' + i, ma: m.ma, ten: m.ten, dvt: m.dvt, kho: 'K', sl_dat: 1, sl_da_nhan: 0, sl_con: 1, co_lo: 0}))};
      if (url === 'vagabond.nhan_hang.tao_phieu') return {dot: 1, phieu: 'PNK-GIA-2', con_lai: 0};
      throw Error('API ngoài dự kiến ' + url);
    }};
  vm.createContext(c);
  vm.runInContext(fs.readFileSync('vagabond/public/js/bep/06-nhap-kho-kiem-ke.js', 'utf8'), c);
  if (cu) await c.scrRecvDoc('PNK-GIA-1'); else await c.scrNhpDon('DMH-GIA-1');
  const body = document.getElementById('vgbBody');
  const html = body.innerHTML;
  assert(html.includes('Đã đếm</span>'), 'vòng tròn có nhãn chữ Đã đếm');
  assert(html.includes('Hệ thống nhập theo ô <b>Số lượng thực nhận</b>'), 'dòng giải thích ý nghĩa dấu Đã đếm');
  const attr = cu ? 'data-ok' : 'data-nok';
  for (const i of danhDau) body.onclick({target: body.querySelector('[' + attr + '="' + i + '"]')});
  await document.getElementById(cu ? 'rcvSub' : 'nhpSub').onclick();
  const ghi = goi.find(x => x.url === (cu ? 'vagabond.nhan_hang.ghi_phieu_nhap' : 'vagabond.nhan_hang.tao_phieu'));
  return {hoi, ghi};
}

(async () => {
  for (const cu of [true, false]) {
    const ten = cu ? 'Nhập kho phiếu nháp' : 'Nhận hàng theo đơn';
    /* Chỉ đánh dấu dòng 0: hai dòng còn lại hiện đủ tên, số, đơn vị; mặc định quay lại thì không ghi. */
    let r = await man(cu, false, [0]);
    assert.strictEqual(r.hoi.length, 1, ten + ': có hỏi lại');
    const o = r.hoi[0];
    assert.strictEqual(o.tieuDe, 'Còn 2 dòng chưa đánh dấu Đã đếm', ten + ': tiêu đề đếm đúng');
    assert.strictEqual(JSON.stringify(o.ds), JSON.stringify([{ten: 'Xẻng gỗ B', phu: '1 PC'}, {ten: 'Thìa gỗ C', phu: '1 Cái'}]), ten + ': đúng dòng, số, đơn vị');
    assert.strictEqual(o.nutQuayLai, 'Quay lại kiểm');
    assert.strictEqual(o.nutTiepTuc, 'Xác nhận nhập cả các dòng chưa đánh dấu');
    assert.strictEqual(r.ghi, undefined, ten + ': quay lại kiểm thì không ghi phiếu');
    /* Bấm đúng nút tiếp tục: ghi cả ba dòng như trước. */
    r = await man(cu, true, [0]);
    assert.strictEqual(JSON.parse(r.ghi.args.dong).length, 3, ten + ': tiếp tục thì nhập cả dòng chưa đánh dấu');
    /* Đánh dấu đủ: không hỏi. */
    r = await man(cu, false, [0, 1, 2]);
    assert.strictEqual(r.hoi.length, 0, ten + ': đủ dấu thì không hỏi');
    assert.strictEqual(JSON.parse(r.ghi.args.dong).length, 3);
  }

  /* chonSheet của 00-nen.js chạy thật: nút chính quay lại, chạm ngoài quay lại, chỉ nút ghi rõ mới đi tiếp. */
  const nen = fs.readFileSync('vagabond/public/js/bep/00-nen.js', 'utf8');
  const dau = nen.indexOf('function chonSheet(o)'), cuoi = nen.indexOf('\nfunction ', dau + 10);
  for (const [bam, mong] of [['data-n', false], ['ov', false], ['data-y', true]]) {
    const document = taiLieuGia();
    const c = {document, Promise, h: x => String(x == null ? '' : x)};
    vm.createContext(c); vm.runInContext(nen.slice(dau, cuoi), c);
    const p = c.chonSheet({tieuDe: 'T', loi: 'L', ds: [{ten: 'Xẻng gỗ B', phu: '1 PC'}], nutQuayLai: 'Quay lại kiểm', nutTiepTuc: 'Xác nhận nhập cả các dòng chưa đánh dấu'});
    const ov = document.body.children[document.body.children.length - 1];
    const nutN = ov.querySelector('[data-n]'), nutY = ov.querySelector('[data-y]');
    assert.strictEqual(nutN.textContent || nutN.innerHTML, 'Quay lại kiểm');
    assert.strictEqual(nutY.textContent || nutY.innerHTML, 'Xác nhận nhập cả các dòng chưa đánh dấu');
    assert(ov.innerHTML.indexOf('data-n') < ov.innerHTML.indexOf('data-y'), 'nút quay lại đứng trước, là nút chính');
    assert(ov.innerHTML.includes('Xẻng gỗ B') && ov.innerHTML.includes('1 PC'), 'danh sách hiện tên và số');
    ov.onclick({target: bam === 'ov' ? ov : ov.querySelector('[' + bam + ']')});
    assert.strictEqual(await p, mong, 'bấm ' + bam);
  }
  console.log('PASS 694: hỏi lại dòng chưa đánh dấu Đã đếm ở cả hai màn nhận hàng');
})().catch(e => { console.error(e); process.exit(1); });

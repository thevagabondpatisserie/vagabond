// #225: chỉ báo thành công khi backend và phiếu đọc lại cùng xác nhận.
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const ma = fs.readFileSync('vagabond/public/js/sua_pkt_tang.js', 'utf8');
async function ca(vai, phanHoi, khop) {
  let handlers, nut, xacNhan, xanh = 0, loi = 0;
  const goi = [];
  const frm = {doc: {name: 'HDB-26-09-00710', docstatus: 1, vgb_but_toan_tang: 'PKT-2026-00012'},
    add_custom_button: (ten, f) => { nut = f; },
    reload_doc: async () => { frm.doc.vgb_but_toan_tang = khop ? 'JE-MOI' : 'JE-CU'; frm.doc.outstanding_amount = 0; }};
  vm.runInNewContext(ma, {__: s => s, frappe: {
    ui: {form: {on: (dt, h) => { handlers = h; }}}, user: {has_role: r => vai.includes(r)},
    utils: {escape_html: s => s}, confirm: (html, f) => { xacNhan = f; },
    call: async opts => { goi.push(opts); return {message: opts.method.endsWith('.xem') ? {
      ma_xac_nhan: 'hash-duyet', pkt_cu: 'PKT-2026-00012', hoa_don: frm.doc.name, so_hddt: '12165',
      pkt_moi_chi_dung_chot: [{account_number: '5111', debit: '9648148.14', credit: '0'}]
    } : phanHoi}; },
    msgprint: () => { loi++; }, show_alert: () => { xanh++; }
  }});
  handlers.refresh(frm);
  if (!nut) return {goi, xanh, loi};
  await nut(); await xacNhan();
  return {goi, xanh, loi};
}
(async () => {
  const ok = {ok: 1, hoa_don: 'HDB-26-09-00710', pkt_cu: 'PKT-2026-00012', pkt_moi: 'JE-MOI', con_no: 0};
  assert.equal((await ca(['Accounts User'], ok, true)).goi.length, 0);
  let r = await ca(['Accounts Manager'], ok, true);
  assert.equal(r.xanh, 1); assert.equal(r.goi[1].type, 'POST'); assert.equal(r.goi[1].args.ma_xac_nhan, 'hash-duyet');
  for (const kq of [{}, {...ok, ok: 0}, {...ok, hoa_don: 'SI-SAI'}, {...ok, con_no: 1}]) {
    r = await ca(['System Manager'], kq, true); assert.equal(r.xanh, 0); assert.equal(r.loi, 1);
  }
  r = await ca(['Accounts Manager'], ok, false); assert.equal(r.xanh, 0); assert.equal(r.loi, 1);
  process.stdout.write('PASS: PKT Cloud quyền, POST/hash, response và reload khớp mới báo xanh\n');
})().catch(e => { console.error(e); process.exitCode = 1; });

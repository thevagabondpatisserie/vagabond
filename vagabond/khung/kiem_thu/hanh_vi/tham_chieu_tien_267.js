'use strict';

const assert = require('assert');
let handlers = null;
global.frappe = {
  datetime: { get_today: () => '2026-09-10' },
  ui: { form: { on: (dt, h) => { assert.strictEqual(dt, 'Payment Entry'); handlers = h; } } }
};
const mod = require('../../../public/js/payment_entry.js');
assert(handlers && typeof handlers.validate === 'function');

function frm(doc) {
  const refreshed = [];
  return { doc, refreshed, refresh_field: x => refreshed.push(x) };
}

let f = frm({ paid_from: '11211 - MB - VGB', paid_to: '331 - NCC - VGB',
  posting_date: '2026-09-10', reference_no: '', reference_date: null });
handlers.validate(f);
assert.strictEqual(f.doc.reference_no, 'CK-20260910');
assert.strictEqual(f.doc.reference_date, '2026-09-10');
assert.deepStrictEqual(f.refreshed, ['reference_no', 'reference_date']);

f = frm({ paid_from: '11211 - MB - VGB', paid_to: '331 - NCC - VGB',
  posting_date: '2026-09-10', reference_no: 'FT-THAT-01', reference_date: '2026-09-09' });
handlers.validate(f);
assert.strictEqual(f.doc.reference_no, 'FT-THAT-01');
assert.strictEqual(f.doc.reference_date, '2026-09-09');
assert.deepStrictEqual(f.refreshed, []);

f = frm({ paid_from: '1111 - Quỹ - VGB', paid_to: '331 - NCC - VGB',
  posting_date: '2026-09-10', reference_no: '', reference_date: null });
handlers.validate(f);
assert.strictEqual(f.doc.reference_no, '');
assert.strictEqual(f.doc.reference_date, null);

f = frm({ paid_from: '1411 - Tạm ứng - VGB', paid_to: '331 - NCC - VGB',
  paid_from_account_type: 'Bank', posting_date: '2026-09-10', reference_no: '', reference_date: null });
assert.deepStrictEqual(mod.dien(f.doc), ['reference_no', 'reference_date']);

console.log('PASS Desk Payment Entry: validate dien tham chieu, giu ma that, tien mat khong doi');

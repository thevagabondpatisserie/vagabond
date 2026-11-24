/* v691 (#614, rà độc lập UI83, UI84, UI88, UI89): chạy HÀM THẬT của tệp phần (nạp nguyên tệp,
 * tên của tệp khác là bản giả trơ, frame bắt HTML) ở hai chế độ giao diện, soi HTML ra.
 *   UI83: mã nhóm Zalo đầy đủ gập trong <details>, giao diện cũ giữ nguyên dòng mã.
 *   UI84: ô bot của nhóm hiện tên bot, giao diện cũ giữ số trơn.
 *   UI88: nhãn "Chức danh riêng" thay "Title riêng".
 *   UI89: ô số tiền lịch chi có đơn vị (đ).
 *
 *   node ui_b_ra_doc_lap_v691.js [thư mục bep]      in JSON kết quả
 */
'use strict';
const vm = require('vm');
const fs = require('fs');
const path = require('path');
const BEP = process.argv[2] || path.resolve(__dirname, '../../../public/js/bep');

function chay(tep, goi, uiB, them) {
  const src = fs.readFileSync(path.join(BEP, tep), 'utf8');
  const khai = {};
  for (const m of src.matchAll(/^(?:async\s+)?function\s+([\w$]+)/gm)) khai[m[1]] = 1;
  for (const m of src.matchAll(/^(?:var|let|const)\s+([\w$]+)/gm)) khai[m[1]] = 1;
  const g = { console, JSON, String, Number, Array, Object, Math, Date, RegExp, Error, Promise, parseInt, parseFloat,
    setTimeout: () => 0, clearTimeout() {}, __ra: [], __khai: khai, __uiB: uiB, __them: them || {} };
  vm.createContext(g);
  vm.runInContext(`(function () {
    var XU = { get: function (t, k) { if (k === Symbol.toPrimitive) return function () { return ''; }; if (k === 'then') return undefined; if (k === 'length') return 0; if (k === Symbol.iterator) return [][Symbol.iterator].bind([]); return P(); }, apply: function () { return P(); } };
    function P() { return new Proxy(function () {}, XU); }
    var gia = {
      h: function (s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); },
      frame: function (t, html) { __ra.push(String(html)); return P(); },
      uiB: function () { return __uiB; },
      money: function (n) { return String(n); },
      VGB_CD: { nhanNhomZalo: function (x) { return 'Nhóm Zalo mã ' + String(x.chat_id).slice(-4).toUpperCase(); } }
    };
    for (var k in __them) gia[k] = __them[k];
    var THIEU = new Proxy({}, { has: function (t, k) { return typeof k === 'string' && !(k in globalThis) && !__khai[k]; },
      get: function (t, k) { if (k === Symbol.unscopables) return undefined; return k in gia ? gia[k] : P(); },
      set: function (t, k, v) { gia[k] = v; return true; } });
    with (THIEU) { ${src}
    ; __ra.push(String(${goi})); }
  })()`, g);
  return g.__ra.join('\n');
}

const MA = 'zgr-' + '0123456789'.repeat(6);
const BANG = "CDL.d = { bang: { zalo_nhom: { cot: [" +
  "{ fn: 'chat_id', nhan: 'Nhóm Zalo', kieu: 'Data' }," +
  "{ fn: 'bot', nhan: 'Bot gửi', kieu: 'Data', chi_doc: 1 }] } } };" +
  "CDL.bang.zalo_bot_phu = [{ ma_bot: '3', ten_bot: 'Bot kho' }];";
function nhom(bot, uiB) { return chay('51-cai-dat-loi.js', "(function () { " + BANG + " return cdlVeDong('zalo_nhom', 0, { chat_id: '" + MA + "', bot: '" + bot + "' }); })()", uiB); }
function giaTriBot(html) { const m = html.match(/<label>Bot gửi<\/label><div class="cdl-val">([^<]*)<\/div>/); return m ? m[1] : null; }

const kq = {};
const moi = nhom('1', true), cu = nhom('1', false);
kq.ma_nhom = {
  moi_gap: /<details class="cdl-ma"><summary class="cdl-mo">Xem mã đầy đủ<\/summary><div class="cdl-mo"[^>]*>zgr-0123/.test(moi),
  moi_ngoai_details: moi.replace(/<details[\s\S]*?<\/details>/g, '').indexOf(MA) >= 0,
  cu_hien_ma: cu.indexOf('<div class="cdl-mo">' + MA + '</div>') >= 0,
  cu_co_details: cu.indexOf('<details') >= 0
};
kq.bot = {
  moi_1: giaTriBot(moi), moi_trong: giaTriBot(nhom('', true)), moi_3: giaTriBot(nhom('3', true)),
  cu_1: giaTriBot(cu)
};
const tq = chay('34-crm-tang-qua.js', "tqVeForm({}, {}), ''", true);
kq.chuc_danh = { moi: tq.indexOf('Chức danh riêng') >= 0, cu: tq.indexOf('Title riêng') >= 0, truong: tq.indexOf('id="tqTitle"') >= 0 };
const lc = chay('71-du-chi.js', "(LDC.lichForm = { so_tien: 1500000 }, scrLichChi()), ''", true);
kq.don_vi = { co: lc.indexOf('Số tiền mỗi tháng (đ)') >= 0, o_tien: lc.indexOf('id="lcTien"') >= 0 };
process.stdout.write(JSON.stringify(kq));

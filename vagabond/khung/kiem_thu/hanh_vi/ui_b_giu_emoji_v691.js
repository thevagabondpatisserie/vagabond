/* v691 (Codex #614): vùng nội dung sẽ in ra hay chèn vào bài phải mang data-giu-emoji để lớp vẽ
 * mới không đổi emoji thành biểu tượng. Chạy HÀM THẬT của tệp phần (nạp nguyên tệp, tên của tệp
 * khác là bản giả trơ, frame và crmMoSheet bắt lại HTML), rồi soi HTML ra: mọi emoji của nội
 * dung phải nằm trong một khối [data-giu-emoji].
 *
 *   node ui_b_giu_emoji_v691.js [thư mục bep]      in JSON {ten: {html_co_emoji, ngoai_vung}}
 */
'use strict';
const vm = require('vm');
const fs = require('fs');
const path = require('path');
const BEP = process.argv[2] || path.resolve(__dirname, '../../../public/js/bep');

function chay(tep, goi) {
  const src = fs.readFileSync(path.join(BEP, tep), 'utf8');
  const khai = {};
  for (const m of src.matchAll(/^(?:async\s+)?function\s+([\w$]+)/gm)) khai[m[1]] = 1;
  for (const m of src.matchAll(/^(?:var|let|const)\s+([\w$]+)/gm)) khai[m[1]] = 1;
  const g = { console, JSON, String, Number, Array, Object, Math, Date, RegExp, Error, Promise, setTimeout: () => 0, clearTimeout() {}, __ra: [], __khai: khai };
  vm.createContext(g);
  vm.runInContext(`(function () {
    var XU = { get: function (t, k) { if (k === Symbol.toPrimitive) return function () { return ''; }; if (k === 'then') return undefined; if (k === 'length') return 0; if (k === Symbol.iterator) return [][Symbol.iterator]; return P(); }, apply: function () { return P(); } };
    function P() { return new Proxy(function () {}, XU); }
    var gia = {
      h: function (s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); },
      frame: function (t, html) { __ra.push(String(html)); return P(); },
      crmMoSheet: function (html) { __ra.push(String(html)); return P(); },
      bdKenh: function () { return { ten: 'Facebook' }; }
    };
    var THIEU = new Proxy({}, { has: function (t, k) { return typeof k === 'string' && !(k in globalThis) && !__khai[k]; },
      get: function (t, k) { if (k === Symbol.unscopables) return undefined; return k in gia ? gia[k] : P(); },
      set: function (t, k, v) { gia[k] = v; return true; } });
    with (THIEU) { ${src}
    ; ${goi}; }
  })()`, g);
  return g.__ra.join('\n');
}

/* Đếm emoji nằm NGOÀI mọi khối [data-giu-emoji]: đi theo thẻ mở, thẻ đóng. */
function ngoaiVung(html) {
  const re = /<(\/?)([a-zA-Z0-9]+)([^>]*)>|([^<]+)/g;
  const nganXep = [];
  let ngoai = 0, tong = 0, m;
  const EMO = /[\u{1F000}-\u{1FAFF}☀-➿]/gu;
  const RONG = /^(br|img|input|hr|meta|link)$/i;
  while ((m = re.exec(html))) {
    if (m[4] !== undefined) {
      const n = (m[4].match(EMO) || []).length;
      tong += n;
      if (n && !nganXep.some(Boolean)) ngoai += n;
    } else if (m[1]) nganXep.pop();
    else if (!RONG.test(m[2]) && !/\/$/.test(m[3])) nganXep.push(/\bdata-giu-emoji\b/.test(m[3]));
  }
  return { tong, ngoai };
}

const kq = {};
/* Lời chúc mẫu, chỉ thấy trong khung xem trước (các phần khác của phiếu là lớp vẽ). */
const lc = chay('34-crm-tang-qua.js', "tqVeForm({}, { loi_chuc: 'Mừng sinh nhật 🎉🎂' })");
const khung = (lc.match(/<div class="tqlc" id="tqXemLc"[^>]*>[^<]*<\/div>/) || [''])[0];
kq.loi_chuc = Object.assign({ co_khung: !!khung }, ngoaiVung(khung));
const bang = chay('75-bai-dang.js', "bdSheetBieuTuong({}, 'fb')");
const luoi = bang.slice(bang.indexOf('<div', bang.indexOf('Chạm để chèn')));
kq.bang_chen = Object.assign({ co_tim: luoi.indexOf('❤️') >= 0 && luoi.indexOf('🤍') >= 0 }, ngoaiVung(luoi));
process.stdout.write(JSON.stringify(kq));

/* v564: man Bo ao mot ma (24-phantom.js that). Chuoi bam: go ma, Xem truoc,
 * ghi ly do, Bo ao. Chay: node vagabond/khung/kiem_thu/hanh_vi/bo_ao_564.js */
'use strict';
var fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert');
var src = fs.readFileSync(path.resolve(__dirname, '..', '..', '..', 'public', 'js', 'bep', '24-phantom.js'), 'utf8');
function moi(ke) {
  var g = { api: [], toast: [], body: '', footer: '' }, els = {};
  var ctx = {
    console: console, h: function (s) { return String(s == null ? '' : s).replace(/</g, '&lt;'); },
    busy: function () {}, toast: function (x) { g.toast.push(x); }, confirmSheet: async function () { return true; },
    errMsg: String, go: function () {},
    frame: function (t, b, o) { g.body = b; g.footer = (o && o.footer) || ''; els = {}; return {}; },
    document: { getElementById: function (id) {
      if ((g.body + g.footer).indexOf('id="' + id + '"') < 0) return null;
      return els[id] || (els[id] = { value: '', onclick: null }); } },
    api: async function (m, p) { g.api.push([m, JSON.parse(JSON.stringify(p))]); return m.endsWith('.xem') ? ke : { tong_ket: 'Đã xong' }; }
  };
  vm.createContext(ctx); vm.runInContext(src, ctx);
  return { ctx: ctx, g: g, el: function (id) { return ctx.document.getElementById(id); } };
}
(async function () {
  var ke = { ma: 'BTPB00024', ten: 'Kem', chan: '', da_la_hang_ton: 0, bom_rieng: ['BOM-1'], dong: [{}], bom_cha: ['BOM-CHA-1'], tong_ket: 'Bỏ ảo BTPB00024: ...' };
  var m = moi(ke);
  m.ctx.scrBoAo();
  assert(m.g.footer === '', 'chua xem truoc thi khong co nut bo ao');
  m.el('boMa').value = 'BTPB00024';
  await m.el('boXem').onclick();
  assert.strictEqual(m.g.api[0][0], 'vagabond.bo_ao.xem');
  assert(m.g.body.indexOf('BOM-CHA-1') >= 0 && m.g.footer.indexOf('boChay') >= 0);
  // thieu ly do thi khong goi chay
  await m.el('boChay').onclick();
  assert(!m.g.api.some(function (c) { return c[0] === 'vagabond.bo_ao.chay'; }), 'thieu ly do khong duoc chay');
  m.el('boLyDo').value = 'Làm sẵn cất tủ';
  await m.el('boChay').onclick();
  var c = m.g.api.find(function (x) { return x[0] === 'vagabond.bo_ao.chay'; });
  assert.strictEqual(JSON.stringify(c[1]), JSON.stringify({ ma: 'BTPB00024', ly_do: 'Làm sẵn cất tủ', chay_that: 1 }));
  // ma bi chan (theo lo) thi hien cau chan, khong co nut
  m = moi({ ma: 'X', chan: 'Mã X đang theo lô nên công cụ không tự bỏ ảo. Báo kỹ thuật làm tay.' });
  m.ctx.scrBoAo(); m.el('boMa').value = 'X'; await m.el('boXem').onclick();
  assert(m.g.body.indexOf('làm tay') >= 0 && m.g.footer === '');
  // ma da co ton: khong co nut
  m = moi({ ma: 'Y', chan: '', da_la_hang_ton: 1, bom_rieng: [], dong: [], bom_cha: [], tong_ket: 'Mã Y đã có tồn kho từ trước' });
  m.ctx.scrBoAo(); m.el('boMa').value = 'Y'; await m.el('boXem').onclick();
  assert(m.g.footer === '');
  console.log('PASS 4 ca bo ao: xem truoc roi moi co nut, bat ly do, bi chan bao lam tay, ma da co ton khong lam gi');
})().catch(function (e) { console.error(e); process.exitCode = 1; });

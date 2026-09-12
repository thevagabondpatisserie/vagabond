// Kiểm quyền đọc phụ: chỉ bỏ khi server nói rõ false, lỗi thật vẫn truyền lên.
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert/strict');
const source = fs.readFileSync(path.join(__dirname, '../../public/js/bep/01-khung-app.js'), 'utf8');
const code = source.slice(source.indexOf('function nenCoQuyen('));
(async () => {
  const calls = [];
  const ctx = {S: {}, Promise, getList: (dt, args) => { calls.push({dt,args}); return Promise.resolve(['A']); }};
  vm.createContext(ctx); vm.runInContext(code, ctx);
  assert.equal(ctx.nenCoQuyen('ban_hang'), true);
  await ctx.nenDemDanhSach('Item', {q:1}); assert.equal(calls.length, 1);
  ctx.S.quyenNen = {ban_hang:false, doc:{Item:false}};
  assert.equal(ctx.nenCoQuyen('ban_hang'), false);
  assert.equal((await ctx.nenDemDanhSach('Item', {})).length, 0); assert.equal(calls.length, 1);
  ctx.S.quyenNen.doc.Item = true;
  await ctx.nenDemDanhSach('Item', {q:2}); assert.deepEqual(calls[1], {dt:'Item',args:{q:2}});
  ctx.getList = () => Promise.reject(new Error('network'));
  await assert.rejects(ctx.nenDemDanhSach('Item', {}), /network/);
  const home = fs.readFileSync(path.join(__dirname, '../../public/js/bep/02-trang-chu.js'), 'utf8');
  const expression = home.match(/var xemBaoCao = ([\s\S]*?);/)[1];
  for (const [cap, legacy, expected] of [[true,false,true],[false,true,false],[null,true,true],[null,false,false]]) {
    const c = {S:{quyenNen:cap === null ? null : {bao_cao:cap}},isSales:()=>legacy,hasRole:()=>false};
    assert.equal(vm.runInNewContext(expression,c),expected);
  }
  console.log('PASS quyen nen: explicit false, legacy fallback, permitted read, error propagation');
})().catch(e => {console.error(e);process.exitCode=1;});

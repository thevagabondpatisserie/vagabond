// #261: chạy hàm thêm combo thật, hai cấu hình cùng tên không được nhập một nhóm.
const fs=require('fs'), vm=require('vm'), assert=require('assert');
const src=fs.readFileSync('vagabond/public/js/bep/09-tinh-tien-quay.js','utf8');
const ctx={posDon:{mon:[{item_code:'BAWS1',qty:1,rate:50000}],combo:[]},flt0:Number,toast:()=>{},comboKhoa:(ma,chon)=>ma+JSON.stringify(chon)};
vm.createContext(ctx);
vm.runInContext(src.slice(src.indexOf('function posThemCombo('),src.indexOf('/* Bam combo o bang chon mon')),ctx);
const cb={name:'CB1',ma_hang:'KMCB00002',ten:'Ba bánh',dong:[{item_code:'BAWS1',so_luong:3,gia_goc:50000}]};
ctx.posThemCombo(cb);ctx.posThemCombo(cb);
ctx.posThemCombo({...cb,name:'CB2',ma_hang:'KMCB00003'});
assert.equal(ctx.posDon.mon.length,3);
assert.deepEqual(Array.from(ctx.posDon.mon,x=>x.qty),[1,6,3]);
assert.equal(ctx.posDon.mon[1].combo,'KMCB00002 - Ba bánh');
assert.equal(ctx.posDon.mon[2].combo,'KMCB00003 - Ba bánh');
assert.equal(ctx.posDon.combo[0].so_bo,2);
console.log('PASS #261: món lẻ, hai bộ, hai combo cùng tên giữ đúng lượng và mã nguồn');

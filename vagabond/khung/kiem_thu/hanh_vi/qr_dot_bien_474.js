'use strict';
const {spawnSync}=require('child_process'),assert=require('assert'),path=require('path');
const file=path.join(__dirname,'qr_chuyen_khoan_474.js');
const base=spawnSync(process.execPath,[file],{encoding:'utf8',env:{...process.env,QR474_MUTATION:''}});assert.equal(base.status,0,base.stderr);
for(const m of ['crc','amount','external']){
 const r=spawnSync(process.execPath,[file],{encoding:'utf8',env:{...process.env,QR474_MUTATION:m}});
 assert.notEqual(r.status,0,m+' lọt');assert(r.stderr.includes('AssertionError'),m+' phải bị bắt bằng assertion, không lỗi dựng nền');console.log('Bắt đột biến '+m);
}
console.log('3/3 đột biến bị bắt; nền nguyên bản đạt');

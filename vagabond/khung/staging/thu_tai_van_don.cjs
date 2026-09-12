// Kiểm bốn lượt bắt đầu trước khi có phản hồi, giữ lỗi chính/phụ và cache.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const s = fs.readFileSync('vagabond/public/js/bep/12-van-don.js', 'utf8');
const ham = s.slice(s.indexOf('async function vdNapDanhSach()'), s.indexOf('async function scrVanDon()'));
async function thu(cache, loiChinh) {
  const calls = [], pending = [];
  const tao = name => {calls.push(name);return new Promise((resolve,reject)=>pending.push({name,resolve,reject}));};
  const ctx = vm.createContext({Promise,vtShipper:cache,vdNgay:'2036-09-09',vdThamSo:()=>({ngay:'2036-09-09'}),
    api:tao,vdNapDiem:()=>tao('diem')});
  vm.runInContext(ham,ctx);
  const k = ctx.vdNapDanhSach().then(r=>({r}),e=>({e}));
  assert.equal(calls.length,cache?3:4,'Các API phải bắt đầu trước khi API đầu trả về');
  for (const p of pending) {
    if (p.name.endsWith('danh_sach')) loiChinh?p.reject(new Error('loi danh sach')):p.resolve(['don']);
    else if (p.name.endsWith('bo_loc') || p.name.endsWith('ds_shipper')) p.reject(new Error('loi phu'));
    else p.resolve([]);
  }
  const tra=await k;
  if(loiChinh) assert.match(tra.e.message,/loi danh sach/);
  else {
    assert.equal(JSON.stringify(tra.r[0]),'["don"]');
    assert.equal(tra.r[1],null);
    assert.equal(JSON.stringify(tra.r[2]),JSON.stringify(cache||[]));
  }
}
(async()=>{await thu(null,false);await thu(['shipper'],false);await thu(null,true);console.log('PASS: tai dong thoi, fallback, cache va loi danh sach');})().catch(e=>{console.error(e);process.exitCode=1;});

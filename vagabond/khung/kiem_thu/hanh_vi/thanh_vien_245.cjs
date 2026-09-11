// #245: lỗi nguồn đơn phải có câu thử lại, không bị biến thành lịch sử rỗng.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
function phanTu(the = 'div') {
  return {the, textContent:'', children:[], classList:{toggle(){}},
    append(...cacCon){this.children.push(...cacCon);}, replaceChildren(){this.children=[];}};
}
(async()=>{
  const cacO = {};
  const tim = id => cacO[id] ||= phanTu();
  let duLieu = {ok:1,ten:'Khách',diem:25000,don:[],don_loi:true,co_ho_so:true};
  const nguon = fs.readFileSync('vagabond/public/web_order/thanh-vien.js','utf8');
  await vm.runInNewContext(nguon, {document:{getElementById:tim,createElement:phanTu},
    fetch:async()=>({ok:true,json:async()=>({message:duLieu})})});
  assert.match(tim('don').children[0].textContent,/Chưa tải được/);
  assert.ok(!tim('don').children.some(x=>x.textContent.includes('Chưa có đơn')));
  const nut = tim('don').children.find(x=>x.the==='button');
  assert.ok(nut && nut.textContent==='Thử lại');
  duLieu = {...duLieu,don_loi:false};
  await nut.onclick();
  assert.match(tim('don').children[0].textContent,/Chưa có đơn/);
  assert.ok(!tim('don').children.some(x=>x.the==='button'));
  assert.match(tim('diem').textContent,/25/);
  console.log('PASS #245: lỗi nguồn, thử lại, rỗng hợp lệ, giữ điểm');
})().catch(e=>{console.error(e);process.exitCode=1;});

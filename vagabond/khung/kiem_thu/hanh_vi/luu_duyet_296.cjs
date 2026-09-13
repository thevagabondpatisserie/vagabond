/* #296: chạy hàm xử lý thật; không coi DOM giả là UAT trên site. */
const fs = require('fs'), vm = require('vm'), path = require('path'), assert = require('assert');
const bep = path.resolve(__dirname, '../../../public/js/bep');
function ham(src, ten) {
  const a = src.indexOf('async function ' + ten + '(');
  assert(a >= 0, ten);
  let n = 0;
  for (let i = src.indexOf('{', a); i < src.length; i++) {
    if (src[i] === '{') n++;
    if (src[i] === '}' && --n === 0) return src.slice(a, i + 1);
  }
  throw Error('Thiếu đóng hàm ' + ten);
}
(async () => {
  for (const loi of [false, true]) {
    const goi = [], bao = [], di = [];
    const c = vm.createContext({PB_PT:'Tiền mặt',d:{name:'SI296'},docO:()=>'',
      busy:()=>{},toast:m=>bao.push(m),go:()=>di.push(1),scrPosDs:()=>{},
      api:async (m,p)=>{goi.push(m);if(loi)throw Error('Thiếu khách công nợ');return {ok:1};}});
    vm.runInContext(ham(fs.readFileSync(path.join(bep,'10-bill-quay.js'),'utf8'),'luuVe'),c);
    await c.luuVe(true);
    assert.deepStrictEqual(goi,['vagabond.ban_hang.pos_luu_don']);
    assert.strictEqual(di.length,loi ? 0 : 1);
    assert(bao[0].includes(loi ? 'Thiếu khách công nợ' : 'Đã lưu đơn nháp'));
  }
  for (const truong of ['xong','loi','huy','api']) {
    const goi=[],bao=[];
    const c=vm.createContext({hoiChu:async()=>truong==='huy'?null:'Đồng ý',
      api:async()=>{goi.push(1);if(truong==='api')throw Error('Không kết nối');return {xuat_hddt:truong==='xong',loi:truong==='loi'?'Đã duyệt, đơn còn nháp. Kho thiếu 3 bánh.':''};},
      baoTin:async m=>bao.push(m),toast:m=>bao.push(m),errMsg:e=>e.message,
      go:()=>{},scrDuyetTang:()=>{},dtgChiTiet:{SI296:{}}});
    vm.runInContext(fs.readFileSync(path.join(bep,'41-duyet-don-tang.js'),'utf8'),c);
    await c.dtgBam({target:{closest:s=>s==='[data-dtgok]'?{getAttribute:()=> 'SI296'}:null}});
    assert.strictEqual(goi.length,truong==='huy'?0:1);
    if(truong==='loi')assert(bao.some(m=>m.includes('Kho thiếu 3 bánh')));
    if(truong==='xong')assert(bao.some(m=>m.includes('gửi phát hành')));
    if(truong==='api')assert(bao.some(m=>m.includes('Không kết nối')));
  }
  console.log('6/6 ca xử lý Lưu đơn và Duyệt đạt');
})().catch(e=>{console.error(e);process.exit(1);});

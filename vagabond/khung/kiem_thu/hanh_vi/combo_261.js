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
const bill=fs.readFileSync('vagabond/public/js/bep/10-bill-quay.js','utf8');
vm.runInContext(bill.slice(bill.indexOf('function posBoMonSua('),bill.indexOf('function posGopDongMon(')),ctx);
const bo=[{item_code:'M1',combo_ma_goc:'CB1',combo_tien:107308},
  {item_code:'M2',combo_ma_goc:'CB1',combo_tien:47692},
  {item_code:'M1',combo_tien:null},{item_code:'M2',combo_ma_goc:'CB2',combo_tien:50000}];
assert.deepEqual(Array.from(ctx.posBoMonSua(bo,0),x=>x.combo_ma_goc),[undefined,'CB2']);
assert.equal(ctx.posBoMonSua(bo,2).length,3);
console.log('PASS #261: xóa cả mã combo, giữ món lẻ và combo khác');
vm.runInContext(bill.slice(bill.indexOf('function posGopDongMon('),bill.indexOf('function posLaNuoc(')),ctx);
const dong={ten:'Món',qty:3,rate:35769,combo:'KMCB - Combo',combo_tien:107308};
const gop=ctx.posGopDongMon([dong,{...dong}]);
assert.equal(gop.length,1);assert.equal(gop[0].qty,6);assert.equal(gop[0].combo_tien,214616);
console.log('PASS #261: gộp dòng in cộng thành tiền đã chốt, không nhân lại rate làm tròn');

(async function () {
  Object.assign(ctx,{b:{},posSua:{mon:bo.slice()},hutSua:()=>{},go:()=>{},scrPosBill:()=>{},name:'SI1'});
  const batDau=bill.indexOf('  b.onclick = async function (e) {');
  vm.runInContext(bill.slice(batDau,bill.indexOf('  var ntm =',batDau)),ctx);
  const bam=i=>ctx.b.onclick({target:{closest:s=>s==='[data-sxoa]'?{getAttribute:()=>String(i)}:null}});
  let hoi=0;
  ctx.confirmSheet=async()=>{hoi++;return false;};
  await bam(0);assert.equal(ctx.posSua.mon.length,4);assert.equal(hoi,1);
  ctx.confirmSheet=async()=>{hoi++;return true;};
  await bam(0);assert.deepEqual(Array.from(ctx.posSua.mon,x=>x.combo_ma_goc),[undefined,'CB2']);
  await bam(0);assert.equal(ctx.posSua.mon.length,1);assert.equal(hoi,2);
  ctx.posSua={mon:bo.slice()};
  ctx.confirmSheet=async()=>{ctx.posSua.mon.splice(0,1);return true;};
  await bam(0);assert.equal(ctx.posSua.mon.length,3);
  console.log('PASS #261: handler xóa thật kiểm Hủy, xác nhận, món lẻ và dòng đổi lúc đang hỏi');
})().catch(e=>{console.error(e);process.exitCode=1;});

// #283: nạp nguyên màn tính tiền, mở sheet thật, tìm và bấm như thu ngân.
(async function () {
  const dg=require('./dom_gia.js');
  for (const lyDo of ['Ngoài khung giờ 07:00 - 11:00','Không áp dụng cho quầy TCV']) {
    const tai=dg.taiLieuGia(), bao=[];
    const m={document:tai,CFGBH:{},console,setTimeout:()=>0,scanBarcode:async()=> 'KMCB1',h:s=>String(s||''),money:s=>String(s||0),flt0:Number,num:String,toast:s=>bao.push(s)};
    vm.createContext(m);vm.runInContext(src,m);
    Object.assign(m,{posDoc:()=>{},posQuay:{ma:'TCV'},posDon:{mon:[],combo:[]},posNguonThuc:()=> 'Tại chỗ',dsItemsCache:[{name:'KMCB1',item_name:'Combo thử',standard_rate:100}],api:async ten=>ten.includes('ds_combo')?{combo:[{name:'CB1',ma_hang:'KMCB1',ten:'Combo thử',dung_duoc:0,ly_do:lyDo,dong:[],gia_combo:100}]}:{}});
    await m.posThemMon();
    const lst=tai.body.querySelector('.shl');
    assert(lst.innerHTML.includes(lyDo),'phải hiện lý do ngay trong sheet');
    const rows=lst.querySelectorAll('.shi');
    assert.equal(rows.length,2,'giữ cả thẻ combo không dùng được và mã hàng');
    for(const row of rows) lst.onclick({target:row});
    assert.deepEqual(bao,[lyDo,lyDo]);assert.equal(m.posDon.mon.length,0);
    await tai.body.querySelector('#shQuet').onclick();
    const quet=lst.querySelectorAll('.shi');assert.equal(quet.length,1,'quét chỉ hiện dòng mã hàng');
    lst.onclick({target:quet[0]});assert.equal(bao[2],lyDo);assert.equal(m.posDon.mon.length,0);
  }
  for (const coCauHinh of [false,true]) {
    const tai=dg.taiLieuGia(), bao=[];
    const m={document:tai,CFGBH:{},console,setTimeout:()=>0,scanBarcode:async()=> 'KMCB1',h:s=>String(s||''),money:s=>String(s||0),flt0:Number,num:String,toast:s=>bao.push(s),comboKhoa:ma=>ma};
    vm.createContext(m);vm.runInContext(src,m);
    Object.assign(m,{posDoc:()=>{},posQuay:{ma:'TCV'},posDon:{mon:[],combo:[]},posNguonThuc:()=> 'Tại chỗ',dsItemsCache:[{name:'KMCB1',item_name:'Combo thử',standard_rate:100}],api:async ten=>ten.includes('ds_combo')?{combo:coCauHinh?[{name:'CB1',ma_hang:'KMCB1',ten:'Combo thử',dung_duoc:1,dong:[{item_code:'BANH1',so_luong:1,gia_goc:100}],gia_combo:100}]:[]}:{}});
    await m.posThemMon();
    const lst=tai.body.querySelector('.shl'),rows=lst.querySelectorAll('.shi');
    lst.onclick({target:rows[rows.length-1]});
    if(coCauHinh) {assert.equal(m.posDon.mon[0].item_code,'BANH1');assert.equal(m.posDon.combo.length,1);}
    else {assert(bao[0].includes('chưa có cấu hình'));assert.equal(m.posDon.mon.length,0);}
  }
  console.log('PASS #283: sheet thật giữ lý do hết giờ/sai quầy, bấm cả thẻ và mã không thêm món');
})().catch(e=>{console.error(e);process.exitCode=1;});

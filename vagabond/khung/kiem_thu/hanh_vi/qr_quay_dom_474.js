'use strict';
const {nap,doc}=require('./qr_474_chung'),vm=require('vm'),assert=require('assert'),{taiLieuGia}=require('./dom_gia');
(async()=>{
 const document=taiLieuGia(),c={console,document,CFGBH:{qr_quay:{bank:'MB',bin:'970422',stk:'VQRQALEAF2999'},qr_nguon:{}},h:s=>String(s??''),money:String,today:()=> '2026-10-13',setTimeout:()=>0,clearInterval(){},location:{},S:{},fetch(){throw Error('Mạng ngoài bị chặn');}};c.window=c;nap(c);vm.runInContext(doc('vagabond/public/js/bep/09-tinh-tien-quay.js'),c);
 Object.assign(c,{posQuay:{ma:'TCV',ten:'TCV'},posDon:{bill:'TCVG8FRJ',che_do:'Tại chỗ',pt:'Tiền mặt',mon:[],xh:{}},posHomNayTxt:'',dsItemsCache:[{name:'BANH',item_name:'Bánh',standard_rate:160000}],cfgBanHang:async()=>{},inNgamDo(){},posTinhKm:async()=>{},posTaiThe:async()=>{},ptTheoNguon:()=>[{v:'Tiền mặt'},{v:'Chuyển khoản'}],posDsCheDo:()=>[{v:'Tại chỗ'}],posInTamTinh(){},posNoiKm(){},posNoiTimKhach(){},posKhoiKm:()=>'',posVeThe:()=>'',cfdKhoi:()=>'',cfdGan(){},cfdDay(){},posDemHomNay(){},posCaVe(){},posGanTruDiem(){},posPollBat(){},veOMtc(){},posDoc(){},posNguonThuc:()=> 'Tại chỗ',api:async method=>{assert(['vagabond.kiem_kho.con_lai','vagabond.khuyen_mai.ds_combo'].includes(method));return {};},frame:(title,html,opt)=>{document.body.innerHTML='';const root=document.createElement('div');root.innerHTML=html+opt.footer;document.body.appendChild(root);return root;},go:fn=>{c.veLai=fn();},toast:msg=>{throw Error(msg);},posSheetMon:(items,pick,close)=>{const item=items.find(x=>x.value==='BANH');assert(item);pick(item);close();}});
 await c.posThemMon();await c.veLai;
 assert.equal(c.posDon.mon.length,1);assert(!document.body.innerHTML.includes('data:image/svg+xml'));
 const button=document.body.querySelector('[data-pt="Chuyển khoản"]');assert(button,'Nút chuyển khoản');await button.onclick();await c.veLai;
 let imgs=document.body.querySelectorAll('img');let before=imgs.map(x=>x.getAttribute('src')).find(s=>s&&s.startsWith('data:image/svg+xml'));assert(before,'QR hiện sau chọn Chuyển khoản');
 const plus=document.body.querySelector('[data-cong="0"]');assert(plus);plus.dispatchEvent({type:'click',target:plus});await c.veLai;
 const after=document.body.querySelectorAll('img').map(x=>x.getAttribute('src')).find(s=>s&&s.startsWith('data:image/svg+xml'));assert(after);assert.notEqual(before,after);assert.equal(c.posDon.mon[0].qty,2);
 console.log('QR474 POS DOM: thêm món, chọn Chuyển khoản, tăng số lượng đổi QR đạt');
})().catch(e=>{console.error(e);process.exit(1);});

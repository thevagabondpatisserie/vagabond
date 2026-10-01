/* v547: chạy THẬT màn Ghi sổ kiểm kê (scrKkPost, kkpSubmit) trong DOM giả. Không đo CSS.
   Ca 1: giá lấy từ goi_y_gia (sổ kho đúng kho), mặc định Điều chỉnh tồn, ghi sổ gửi đúng giá.
   Ca 2 (Codex #401 F3): goi_y_gia lỗi thì CHẶN ghi sổ, không rơi về Item.valuation_rate.
   Vòng 3: tra giá và ghi sổ dùng CÙNG một mốc ngày giờ. */
const fs=require('fs'), vm=require('vm'), assert=require('assert');
const {taiLieuGia,ElementGia}=require('./dom_gia.js');
async function canh(loiGia){
 const document=taiLieuGia(),goi=[],toast=[];
 /* Codex #401 vong 3: moi lan goi hmOf ra mot gio KHAC, nen code nao goi hmOf
    hai lan (mot lan tra gia, mot lan ghi so) se lo ra gio lech. */
 let soGio=0;
 const c={document,console,Date,Math,JSON,Promise,setTimeout,COMPANY:'CTY',
  h:x=>String(x==null?'':x),num:String,dmy:String,shortWh:String,vgbCss:()=>{},busy:()=>{},
  toast:m=>toast.push(m),errMsg:e=>String(e&&e.message||e),back:()=>{},go:()=>{},reset:()=>{},scrHome:()=>{},scrKkList:()=>{},kk:{},
  sheet:()=>{},confirmSheet:async()=>true,ymdOf:()=> '2026-10-01',hmOf:()=> '08:'+String(10+(soGio++))+':00',
  inChunks:async(a,n,f)=>f(a),
  getList:async(dt)=>{
   if(dt==='Item')return [{name:'M',item_name:'Món',stock_uom:'Gram',has_batch_no:0,valuation_rate:0,last_purchase_rate:0}];
   if(dt==='Account')return [{name:'TK'}];
   return [];},
  frame:(t,html,o={})=>{document.body.innerHTML='';const b=new ElementGia('div');b.setAttribute('id','vgbBody');b.innerHTML=html+(o.footer||'');b.parentNode=document.body;document.body.children.push(b);return b;},
  api:async(url,args)=>{
   goi.push({url,args});
   if(url==='vagabond.kiem_ke.mo_phieu')return {name:'KK-1',kho:'Kho D1',pham_vi:'Tất cả',ngay_kiem:'2026-09-30',trang_thai:'Chờ duyệt',ly_do_lech:[],
     items:[{name:'R1',item_code:'M',item_name:'Món',dvt:'Gram',da_dem:1,so_luong:5,ton_he_thong:5}]};
   if(url==='frappe.client.get_value')return {stock_adjustment_account:'632',cost_center:'CC'};
   if(url==='vagabond.gia_von_kiem_ke.goi_y_gia'){if(loiGia)throw Error('hết giờ');return {M:{gia:400,nguon:'so_kho'}};}
   if(url==='frappe.client.insert')return {name:'PKK-1'};
   if(url==='frappe.client.submit'||url==='frappe.client.save')return {};
   throw Error('API ngoài dự kiến '+url);
  }};
 vm.createContext(c); vm.runInContext(fs.readFileSync('vagabond/public/js/bep/06-nhap-kho-kiem-ke.js','utf8'),c);
 await c.scrKkPost('KK-1');
 const kkp=vm.runInContext('kkp',c);
 assert.strictEqual(kkp.opening,0,'mặc định Điều chỉnh tồn, không phải Tồn đầu kỳ');
 let gy=goi.find(x=>x.url==='vagabond.gia_von_kiem_ke.goi_y_gia');assert(gy,'đã gọi goi_y_gia');assert.strictEqual(gy.args.kho,'Kho D1','tra đúng kho');
 if(loiGia){
  assert(!document.getElementById('kkpgo'),'không hiện nút ghi sổ khi tra lỗi');
  assert(!document.querySelector('[data-rate]'),'không mời nhập giá tay khi tra lỗi');
  assert(document.getElementById('vgbBody').innerHTML.includes('Chưa tra được giá vốn'),'hiện lỗi ngay');
  await c.kkpSubmit();
  assert(!goi.some(x=>x.url==='frappe.client.insert'),'chặn cả gọi submit trực tiếp');
  loiGia=false;
  await document.getElementById('kkpthulai').onclick();
  gy=goi.filter(x=>x.url==='vagabond.gia_von_kiem_ke.goi_y_gia').slice(-1)[0];
 }
 await document.getElementById('kkpgo').onclick();
 const ins=goi.find(x=>x.url==='frappe.client.insert');
 {
  assert(ins,'đã tạo phiếu điều chỉnh');
  assert.strictEqual(ins.args.doc.purpose,'Stock Reconciliation','kiểu Điều chỉnh tồn');
  assert.strictEqual(ins.args.doc.items[0].valuation_rate,400,'giá sổ kho 400, không phải Item.valuation_rate 0');
  assert.strictEqual(gy.args.ngay,ins.args.doc.posting_date,'tra giá đúng ngày ghi sổ');
  assert.strictEqual(gy.args.ngay,'2026-09-30','ngày ghi sổ là ngày kiểm');
  assert.strictEqual(gy.args.gio,ins.args.doc.posting_time,'tra giá đúng giờ ghi sổ (Codex #401 vòng 3)');
 }
}
(async()=>{await canh(false);await canh(true);console.log('PASS 547: gia von tu goi_y_gia, mac dinh dieu chinh ton, tra gia loi thi chan');})().catch(e=>{console.error(e);process.exit(1);});

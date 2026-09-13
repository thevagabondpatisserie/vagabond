/* Chạy nguyên phần nhận hàng, bấm ô ngày/nút thật trong DOM giả. Không đo CSS. */
const fs=require('fs'), vm=require('vm'), assert=require('assert');
const {taiLieuGia,ElementGia}=require('./dom_gia.js');
Object.defineProperty(ElementGia.prototype,'classList',{get(){const e=this;return {add(k){this.toggle(k,true)},remove(k){this.toggle(k,false)},toggle(k,on){const a=new Set((e.getAttribute('class')||'').split(' '));if(on)a.add(k);else a.delete(k);e.setAttribute('class',[...a].join(' '));}};}});
async function canh(ngay,canhBao,cu=false,loiDoc=null,chuaSua=false){
 const document=taiLieuGia(),goi=[],suKien=[];
 const tim=document.querySelector.bind(document);document.querySelector=sel=>{const a=sel.split(' ');return a.length===2 ? tim(a[0])?.querySelector(a[1]) : tim(sel);};
 const c={document,console,Date,Math,JSON,Promise,setTimeout,
  today:()=> '2026-09-13',addDays:(d,n)=>new Date(Date.parse(d)+n*86400000).toISOString().slice(0,10),
  h:x=>String(x||''),num:String,dmy:String,shortWh:String,vgbCss:()=>{},busy:()=>{},toast:m=>suKien.push(['toast',m]),
  errMsg:e=>{throw e;},back:()=>suKien.push(['back']),
  getList:async(dt)=>{if(dt==='Batch' && loiDoc==='loi')throw Error('mạng');return dt==='Item'?[{name:'M',has_batch_no:1,shelf_life_in_days:90}]:[];},
  confirmSheet:async(t,m)=>{suKien.push(['dialog',t,m]);return true;},
  frame:(t,html,o={})=>{document.body.innerHTML='';const b=new ElementGia('div'); b.setAttribute('id','vgbBody'); b.innerHTML=html+(o.footer||'');b.parentNode=document.body;document.body.children.push(b);return b;},
  api:async(url,args)=>{
   goi.push({url,args});
   if(url==='frappe.client.get')return {doctype:'Purchase Receipt',name:'PR-1',modified:'2026-09-13',items:[{name:'D1',item_code:'M',qty:1,rate:1000,warehouse:'K',batch_no:loiDoc?'LO-1':null}]};
   if(url==='vagabond.nhan_hang.ghi_phieu_nhap')return {phieu:'PR-1',canh_bao_han:canhBao};
   if(url==='vagabond.nhan_hang.chi_tiet')return {dot_toi:1,ncc:'NCC',so_mon_con:1,mon:[{dong:'D1',ma:'M',ten:'Món',dvt:'Gram',kho:'K',sl_dat:1,sl_con:1,co_lo:1,han_chuan:90,hsd_toi_thieu:0,bat_buoc_hsd:1}]};
   if(url==='vagabond.nhan_hang.tao_phieu')return {dot:1,phieu:'PR-1',con_lai:0,canh_bao_han:canhBao};
   throw Error('API ngoài dự kiến '+url);
  }
 };
 vm.createContext(c); vm.runInContext(fs.readFileSync('vagabond/public/js/bep/06-nhap-kho-kiem-ke.js','utf8'),c);
 if(cu)await c.scrRecvDoc('PR-1');else await c.scrNhpDon('PO-1');
 const el=document.querySelector(cu?'[data-h]':'[data-nh]');assert(el,'có ô HSD');assert.strictEqual(el.value,'','không tự gán ngày máy tính thành ngày nhãn');
 if(!chuaSua){el.value='2026-12-12';el.onchange();el.value=ngay;el.onchange();}
 assert.strictEqual(el.value,ngay,'xóa không bị tự điền lại');
 const nhac=cu?'':document.querySelector('[data-nwn]').innerHTML;
 if(!cu)assert(nhac.includes(ngay?'Hạn dùng đã qua':'Chưa có hạn sử dụng'),'nhắc ngay khi sửa, kể cả min0');
 await document.getElementById(cu?'rcvSub':'nhpSub').onclick();
 const gui=goi.find(x=>x.url===(cu?'vagabond.nhan_hang.ghi_phieu_nhap':'vagabond.nhan_hang.tao_phieu'));assert(gui,'đã gọi API');
 const dd=JSON.parse(gui.args.dong)[0];assert.strictEqual(dd.hsd,chuaSua?null:ngay,'chưa đọc khác xóa chủ động');if(cu)assert.strictEqual(dd.giu,chuaSua?1:0,'cờ giữ chỉ khi chưa sửa');
 const bao=suKien.findIndex(x=>x[0]==='dialog' && x[1].includes('kiểm tra hạn dùng'));
 const ve=suKien.findIndex(x=>x[0]==='back');
 assert(bao>=0 && ve>bao,'thấy cảnh báo máy chủ trước khi rời màn');
 assert(suKien[bao][2].includes(canhBao[0]),'đúng nội dung máy chủ');
}
(async()=>{await canh('',['Chưa có hạn sử dụng: Món']);await canh('2026-09-01',['Hạn dùng cần kiểm tra: Món']);await canh('',['Chưa có hạn sử dụng: Món'],true);await canh('2026-09-01',['Hạn dùng cần kiểm tra: Món'],true);for(const loi of ['loi','thieu']){await canh('',['Giữ HSD'],true,loi,true);await canh('',['Chưa có hạn sử dụng'],true,loi,false);}console.log('PASS 489: shelf90, clear date, min0 expired, payload and warning before back');})().catch(e=>{console.error(e);process.exit(1);});

'use strict';
const assert=require('assert'),vm=require('vm'),{doc,nap,ham}=require('./qr_474_chung'),{taiLieuGia}=require('./dom_gia');
function trang(file,ids){
 const document=taiLieuGia();for(const id of ids){let x=document.createElement('div');x.setAttribute('id',id);document.body.appendChild(x);}
 const c={CFD_GT:1,document,console,URLSearchParams,location:{search:'?m=demo'},navigator:{},setTimeout:()=>0,setInterval:()=>0,clearInterval(){},fetch(){throw Error('Mạng ngoài bị chặn');}};c.window=c;
 c.BroadcastChannel=function(){c.kenh=this;this.postMessage=()=>{};};nap(c);
 const source=doc(file);const scripts=[...source.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/g)];
 for(const s of scripts){if(s[1])assert(/src="\/assets\/vagabond\/js\//.test(s[1]),'Script phải cùng site');}
 c.chay=()=>{for(const s of scripts)if(!s[1])vm.runInContext(s[2],c);};return c;
}
(async()=>{
 const c=trang('vagabond/trang/tt.html',['than','toast']);const raw=c.VgbQr.chuoi({bin:'970422',stk:'VQRQALEAF2999',tien:160000,noi_dung:'TCVG8FRJ'});
 c.fetch=async url=>{assert(url.startsWith('/api/method/vagabond.thanh_toan.xem?'));return {json:async()=>({message:{ok:1,qr_text:raw,so_tien:160000,noi_dung_ck:'TCVG8FRJ',ngan_hang:{stk:'VQRQALEAF2999',ten:'MB'}}})};};
 c.chay();await new Promise(resolve=>setImmediate(resolve));let h=c.document.getElementById('than').innerHTML;assert(h.includes(c.VgbQr.tao({qr_text:raw}).anh));assert(!h.includes('https://'));
 c.qrcode=undefined;c.chay();await new Promise(resolve=>setImmediate(resolve));h=c.document.getElementById('than').innerHTML;assert(h.includes('thư viện'));assert(h.includes('VQRQALEAF2999'));assert(!h.includes('<img'));
 const d=trang('vagabond/www/man-hinh-khach.html',['man','nutTo']);d.chay();
 // Dữ liệu được tạo bởi sender thật; URL ngoài đưa lén không được dùng.
 vm.runInContext(ham(doc('vagabond/public/js/bep/25-man-hinh-khach.js'),'cfdDungGoi'),d);
 let g=d.cfdDungGoi({mon:[{ten:'Bánh',qty:1,rate:160000}],pt:'Chuyển khoản'},{ma:'TCV',ten:'TCV'},160000,{bin:'970422',stk:'VQRQALEAF2999',bank:'MB',nd:'TCVG8FRJ',tien:160000,url:'https://evil/qr'},'tab',Date.now(),'');
 assert.equal(g.qr.url,'','Không chuyển tiếp URL ngoài');
 d.kenh.onmessage({data:g});h=d.document.getElementById('man').innerHTML;assert(h.includes('data:image/svg+xml'));assert(!h.includes('https://evil'));assert(h.includes('TCVG8FRJ'));
 const local=d.VgbQr.tao({bin:'970422',stk:'VQRQALEAF2999',tien:160000,noi_dung:'TCVG8FRJ'}).anh;
 const cu=d.cfdDungGoi({mon:[],pt:'Chuyển khoản'},{ma:'TCV'},160000,{bin:'970422',stk:'VQRQALEAF2999',bank:'MB',nd:'TCVG8FRJ',tien:160000,url:local},'tab',Date.now(),'');
 assert.equal(cu.qr.url,local,'Tab khách cũ nhận data URI thay ảnh ngoài');
 Object.assign(d,{CFGBH:{qr_quay:{bin:'970422',bank:'MB',stk:'VQRQALEAF2999'}},cfdCo:()=>true,cfdMaTab:()=> 'tab',cfdPhat:goi=>{d.gui=goi;},cfdNhipBat(){},posNoiDungCk:()=> 'TCVG8FRJ',posSepayNhan:0});
 vm.runInContext(ham(doc('vagabond/public/js/bep/25-man-hinh-khach.js'),'cfdDay'),d);
 d.cfdDay({mon:[],bill:'TCVG8FRJ',pt:'Chuyển khoản'},{ma:'TCV'},160000,'Tại chỗ',false,'');
 assert.equal(d.gui.qr.url,local,'Sender thật phát ảnh tại máy cho tab cũ');

 g.qr.stk='';d.kenh.onmessage({data:g});h=d.document.getElementById('man').innerHTML;assert(h.includes('tài khoản'));assert(!h.includes('id="qrAnh"'));
 console.log('QR474: trang thanh toán raw Pancake, CFD sender/receiver, lỗi thư viện/tài khoản đạt');
})().catch(e=>{console.error(e);process.exit(1);});

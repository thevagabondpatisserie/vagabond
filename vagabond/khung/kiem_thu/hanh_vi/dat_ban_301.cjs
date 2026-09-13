/* #301: chạy form thật, giữ payload cả các chip mới khi mất phản hồi. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const {taiLieuGia,ElementGia}=require('./dom_gia.js');
Object.defineProperty(ElementGia.prototype,'classList',{get(){return {toggle:()=>{}};}});
ElementGia.prototype.append=function(...ds){ds.forEach(x=>this.appendChild(x));};
const query=ElementGia.prototype.querySelectorAll;
ElementGia.prototype.querySelectorAll=function(sel){
 if(sel==='meta[name=csrf-token]')return query.call(this,'[name=csrf-token]');
 if(sel==='input,textarea,.chip button')return [...query.call(this,'input,textarea'),...query.call(this,'.chip').flatMap(x=>query.call(x,'button'))];
 return query.call(this,sel);
};
(async()=>{
 const document=taiLieuGia();document.body.innerHTML=fs.readFileSync('vagabond/www/dat-ban.html','utf8');
 const tim=id=>document.getElementById(id),bodies=[];
 let thu=0;
 const fetch=async(url,opts)=>{
  if(!opts)return {ok:true,json:async()=>({message:{bat:true,co_so:'TCV',ten_co_so:'Tiệm thử',dia_chi:'Thử',hom_nay:'2026-09-14',toi_da_khach:8,khung_gio:['14:00'],dip:['Sinh nhật'],khu_vuc:['Bàn thử']}})};
  bodies.push(opts.body);if(++thu===1)throw Error('Failed to fetch');
  return {ok:true,json:async()=>({message:{ok:1,ma:'TEST'}})};
 };
 await vm.runInNewContext(fs.readFileSync('vagabond/public/web_order/dat-ban.js','utf8'),{document,fetch,crypto:{randomUUID:()=> '11111111-1111-1111-1111-111111111111'}});
 assert.equal(tim('dat-ban').hidden,false);
 tim('gio').querySelector('button').onclick();tim('dip').querySelector('button').onclick();tim('khu-vuc').querySelector('button').onclick();
 tim('ten').value='Khách thử';tim('sdt').value='0912345678';tim('tre-em').value='1';tim('email').value='a@example.com';tim('banh-kem-theo').value='Bánh';
 await tim('dat-ban').onsubmit({preventDefault(){}});
 assert.match(tim('trang-thai').textContent,/Mất kết nối/);
 assert.equal(tim('dip').querySelector('button').disabled,true);
 const goi=JSON.parse(bodies[0]);assert.equal(goi.du_lieu.dip,'Sinh nhật');assert.equal(goi.du_lieu.khu_vuc,'Bàn thử');assert.equal(goi.du_lieu.tre_em,'1');assert.equal(goi.du_lieu.email,'a@example.com');assert.equal(goi.du_lieu.banh_kem_theo,'Bánh');
 for(const ten of ['sdt_lien_he','di_ung','kenh_lien_he'])assert.ok(!(ten in goi.du_lieu));
 await tim('dat-ban').onsubmit({preventDefault(){}});
 assert.equal(bodies[0],bodies[1]);assert.equal(tim('dat-ban').hidden,true);
 console.log('PASS #301: chip cấu hình, năm ô, mất mạng và gửi lại đúng payload/khóa');
})().catch(e=>{console.error(e);process.exitCode=1;});

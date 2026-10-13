'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm');
const root=path.resolve(__dirname,'../../../..');
function doc(p){return fs.readFileSync(path.join(root,p),'utf8');}
function ham(src,ten){
 const i=src.indexOf('function '+ten+'(');if(i<0)throw Error(ten);
 let p=src.indexOf('{',i),n=0;
 for(let j=p;j<src.length;j++){if(src[j]==='{')n++;if(src[j]==='}'&&!--n)return src.slice(i,j+1);}
 throw Error('Thiếu dấu đóng '+ten);
}
function nap(c){
 vm.createContext(c);
 for(const p of ['vendor/qrcode.js','qr_chuyen_khoan.js']) {
  let src=doc('vagabond/public/js/'+p);
  if(p==='qr_chuyen_khoan.js' && process.env.QR474_MUTATION){
   const changes={crc:["return ra+crc16(ra)","return ra+'0000'"],amount:["if(so) ra+=", "if(false) ra+="],external:["anh:'data:image/svg+xml;charset=utf-8,'+encodeURIComponent", "anh:'https://external.invalid/qr?svg='+encodeURIComponent"]};
   const pair=changes[process.env.QR474_MUTATION];if(!pair||!src.includes(pair[0]))throw Error('Đột biến chưa được áp');src=src.replace(pair[0],pair[1]);
  }
  vm.runInContext(src,c);
 }
 const pos=doc('vagabond/public/js/bep/09-tinh-tien-quay.js');
 for(const ten of ['posDiemCua','posTaiKhoan','posQrTao','posQrUrl','posQrLoi','posKhoiQr'])vm.runInContext(ham(pos,ten),c);
 return c;
}
module.exports={root,doc,ham,nap};

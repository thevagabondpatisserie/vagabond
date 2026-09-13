/* #296: hộp đã có ruột tính từ bánh lẻ, không nhập Bếp làm lần hai. */
const fs=require('fs'),vm=require('vm'),path=require('path'),assert=require('assert');
const doc=require('./dom_gia.js').taiLieuGia();
const c=vm.createContext({document:doc,money:String,h:String});
vm.runInContext(fs.readFileSync(path.resolve(__dirname,'../../../public/js/bep/11-khach-ca-hop-dong.js'),'utf8'),c);
c.mvLocDs=ds=>ds;c.mvCon=()=>100;
for(const hop of [0,1]){
 const e=doc.createElement('div');e.innerHTML=c.mvDsSpHtml([{ma_hang:'HOP296',ten_banh:'Mẫu kiểm',la_hop:hop}]);
 assert.strictEqual(!!e.querySelector('[data-mvsx]'),!hop);
 assert(e.querySelector('[data-mvnhain]'));
 if(hop)assert(e.textContent.includes('Hộp chỉ nhận số nhà in giao'));
}
console.log('PASS 2: hộp chỉ nhận nhà in, bánh lẻ giữ Bếp làm');

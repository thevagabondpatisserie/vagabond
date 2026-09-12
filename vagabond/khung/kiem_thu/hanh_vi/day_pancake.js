/* #210: bấm gửi/kiểm/xác nhận giá0 qua đúng hàm của màn danh mục. */
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const src=fs.readFileSync(path.join(__dirname,'../../../public/js/bep/17-cai-dat.js'),'utf8');
function ham(name){let a=src.indexOf('function '+name+'(');if(src.slice(a-6,a)==='async ')a-=6;let b=src.indexOf('{',a),n=1,i=b+1;for(;n;i++){if(src[i]==='{')n++;if(src[i]==='}')n--;}return src.slice(a,i);}
async function test(){
 let calls=[],answers=[],yes=false,msg='';
 const c={api:async(m,a)=>{calls.push([m,a]);let x=answers.shift();if(x instanceof Error)throw x;return x;},confirmSheet:async()=>yes,dmBaoMot:(ma,t)=>msg=t};
 vm.createContext(c);vm.runInContext(['dmMauTrangThai','dmNutSau','dmDayMot','dmKiemMot'].map(ham).join('\n'),c);
 assert.equal(c.dmMauTrangThai('dang_cho'),'#b45309');
 let b={};answers=[{trang_thai:'chua_ro'}];await c.dmDayMot('M',b,0);assert.equal(b.textContent,'Kiểm lại');
 answers=[{trang_thai:'chua_ro'}];await b.onclick();assert(calls[1][0].endsWith('kiem_ma_tren_pancake'));assert.equal(calls.filter(x=>x[0].endsWith('day_sang_pancake')).length,1);
 calls=[];answers=[{trang_thai:'thieu_gia'}];yes=false;await c.dmDayMot('M',b,0);assert.equal(calls.length,1);
 calls=[];answers=[{trang_thai:'thieu_gia'},{trang_thai:'chua_ro'}];yes=true;await c.dmDayMot('M',b,0);assert.equal(calls.length,2);assert.equal(calls[1][1].cho_phep_gia_0,1);
 calls=[];answers=[new Error('mạng')];await c.dmDayMot('M',b,0);assert.equal(b.textContent,'Kiểm lại');assert(msg.includes('không gửi thêm'));
 answers=[{trang_thai:'da_co'}];await c.dmKiemMot('M',b);assert.equal(b.disabled,true);
 console.log('PASS #210: chưa rõ/mất mạng chỉ kiểm lại; hủy/duyệt giá0; đã có không tạo nữa.');
}
test().catch(e=>{console.error(e);process.exitCode=1;});

/* v644: nút Đưa lên web ở màn Danh mục sản phẩm (ngay dưới Đồng bộ Pancake).
   Bấm qua đúng hàm của màn, máy chủ giả trả đúng hình dạng banh_web.dua_len_web. */
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const src=fs.readFileSync(path.join(__dirname,'../../../public/js/bep/17-cai-dat.js'),'utf8');
function ham(name){let a=src.indexOf('function '+name+'(');if(src.slice(a-6,a)==='async ')a-=6;let b=src.indexOf('{',a),n=1,i=b+1;for(;n;i++){if(src[i]==='{')n++;if(src[i]==='}')n--;}return src.slice(a,i);}
async function test(){
 let calls=[],answers=[];
 const o={textContent:'',style:{}};
 const c={api:async(m,a)=>{calls.push([m,a]);let x=answers.shift();if(x instanceof Error)throw x;return x;},document:{getElementById:id=>id==='dmWebBao'?o:null}};
 vm.createContext(c);vm.runInContext(['dmChuWeb','dmWebMot'].map(ham).join('\n'),c);
 /* Bánh mới: tạo thẻ Chờ ảnh, báo người bấm khách chưa thấy, nút khoá. */
 let b={id:'dmWeb'};answers=[{trang_thai:'Chờ ảnh',moi:1,thong_bao:'Đã tạo thẻ Very Berry trên trình biên tập web và nhắn Marketing thêm ảnh. Khách chưa thấy tới khi Marketing bật Hiện trên web.'}];
 await c.dmWebMot('BAWC00086',b,'dmWebBao');
 assert.deepEqual(calls,[['vagabond.banh_web.dua_len_web',{item_code:'BAWC00086'}]]);
 assert(o.textContent.includes('Khách chưa thấy'));assert.equal(o.style.color,'#b45309');
 assert.equal(b.disabled,true);assert.equal(b.textContent,'Đã đưa lên web');
 /* Size khác của bánh đang hiện: báo xanh. */
 answers=[{trang_thai:'Đang hiện',moi:0,thong_bao:'Very Berry đã có trên web (Đang hiện): khách đang thấy, size mới hiện ngay khi có tồn.'}];
 b={id:'x'};await c.dmWebMot('BAWC00087',b,'dmWebBao');assert.equal(o.style.color,'#15803d');
 /* Lỗi (chưa có giá): báo đỏ đúng câu máy chủ, nút mở lại để bấm sau khi sửa. */
 answers=[new Error('Mã BAWC00999 chưa có giá bán. Đặt giá ở hồ sơ món rồi đưa lên web.')];
 b={id:'dmWeb'};await c.dmWebMot('BAWC00999',b,'dmWebBao');
 assert(o.textContent.includes('chưa có giá bán'));assert.equal(o.style.color,'#b3261e');assert.equal(b.disabled,false);assert.equal(b.textContent,'Đưa lên web');
 /* Chữ trạng thái web từng mã, không lộ mã nội bộ. */
 assert(c.dmChuWeb('').includes('Chưa đưa lên web'));assert(c.dmChuWeb('Chờ ảnh').includes('khách chưa thấy'));assert(c.dmChuWeb('Đang hiện').includes('Đang hiện'));
 console.log('PASS v644: Đưa lên web báo đúng trạng thái, lỗi giữ nút để bấm lại.');
}
test().catch(e=>{console.error(e);process.exitCode=1;});

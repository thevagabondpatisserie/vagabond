const fs=require('fs'),vm=require('vm'),assert=require('assert');
const dg=require('./dom_gia.js');
const source=fs.readFileSync('vagabond/public/js/bep/19-ho-so-tt.js','utf8');
const code=source.slice(source.indexOf('var hsCocLan = null;'));
const stored=new Map(); let calls=[],messages=[],khung,done=0,fail=true,sheetCalls=[];
let danhRows=[{name:'PE-1',ngay:'2026-09-10',con_coc:3000000}],saoRows=[];
function env(){
 const tai=dg.taiLieuGia();
 const c={console,JSON,Number,
  sinhMaLanNhan:()=> 'LN-request-coc-247-unique',hasRole:()=>true,
  sessionStorage:{getItem:k=>stored.get(k),setItem:(k,v)=>stored.set(k,v),removeItem:k=>stored.delete(k)},
  h:x=>String(x||''),money:x=>String(x),busy:()=>{},toast:x=>messages.push(x),baoTin:x=>messages.push(x),xacNhan:async()=>true,
  frame:(t,html)=>{khung=new dg.ElementGia('div');khung.innerHTML=html;tai.body.children=[khung];return khung;},
  sheet:(title,items,cur,onPick,searchable)=>{sheetCalls.push({title,items,cur,onPick,searchable});},
  api:async(m,a)=>{calls.push({m,a:JSON.parse(JSON.stringify(a))});
   if(m.endsWith('.danh_sach'))return {rows:danhRows};
   if(m.endsWith('.sao_ke_coc'))return {rows:saoRows};
   if(fail)throw Error('Mất phản hồi');return {ok:1,da_can:2000000,da_lam_roi:1};}
 };vm.createContext(c);vm.runInContext(code,c);return {c,tai};
}
(async()=>{
 let {c,tai}=env();
 assert.equal(JSON.stringify(c.hsChiaCoc([{hoa_don:'A',so_tien:2000000},{hoa_don:'B',so_tien:8000000}],3000000)),JSON.stringify([{hoa_don:'A',so_tien:2000000},{hoa_don:'B',so_tien:1000000}]));
 await c.hsMoCanCoc('NCC-1',[{hoa_don:'HD-1',so_tien:2000000}],()=>done++);
 const nutCoc=tai.querySelector('[data-hscoc]');assert.equal(nutCoc.tagName,'DIV');assert(nutCoc.className.split(/\s+/).includes('li'));
 const bamCoc=khung._nghe.click[0];
 await Promise.all([bamCoc({target:nutCoc}),bamCoc({target:nutCoc})]);
 assert.equal(done,0);assert(stored.has('vgb_coc_app_pending'));
 assert.equal(calls.filter(x=>x.m.endsWith('.can_coc')).length,1);
 assert.equal(nutCoc.getAttribute('data-hsdang'),null);assert.equal(nutCoc.style.pointerEvents,'');
 const sent=calls.at(-1).a;assert.equal(sent.ma_lan,'CC-request-coc-247-unique');
 ({c,tai}=env());fail=false;await c.hsThuLaiCanCoc(()=>done++);
 assert.deepStrictEqual(calls.at(-1).a,sent);assert.equal(done,1);assert.equal(stored.size,0);
 danhRows=Array.from({length:9},(_,i)=>({name:'PE-'+(i+1),ngay:'2026-09-'+String(i+1).padStart(2,'0'),con_coc:1000}));
 ({c,tai}=env());await c.hsMoCanCoc('NCC-1',[{hoa_don:'HD-1',so_tien:1000}],()=>{});
 let chon=sheetCalls.at(-1);assert.equal(chon.searchable,true);assert.equal(chon.items.length,9);
 assert(chon.items[8].tim.includes('PE-9'));
 const soCanTruoc=calls.filter(x=>x.m.endsWith('.can_coc')).length;
 await Promise.all([chon.onPick({value:'PE-1'}),chon.onPick({value:'PE-1'})]);
 assert.equal(calls.filter(x=>x.m.endsWith('.can_coc')).length,soCanTruoc+1,
  'callback sheet bi goi hai lan chi duoc gui mot yeu cau can coc');
 stored.clear();c.hsCocLan=null;
 saoRows=Array.from({length:9},(_,i)=>({name:'BT-'+(i+1),date:'2026-09-'+String(i+1).padStart(2,'0'),withdrawal:1000,description:'Giao dich '+(i+1)}));
 await c.hsNoiSaoKeCoc('NCC-1','PE-1',()=>{});
 chon=sheetCalls.at(-1);assert.equal(chon.searchable,true);assert.equal(chon.items.length,9);
 assert(chon.items[7].tim.includes('BT-8'));

 /* P2-1, Codex neu ra 10/09/2026: khoan can noi sao ke co hon 8 giao dich
    thi hsNoiSaoKeCoc mo TAM TRUOT (sheet) phu len chinh man can coc. Truoc
    day nhanh do tra ve true, nen hsChonCanCoc KHONG mo khoa nut ngoai; dong
    tam bang X hay cham ra ngoai (khong bam chon giao dich nao trong sheet -
    dung mock sheet() o tren, chi ghi lai loi goi chu khong tu bam) thi
    khong con duong nao goi lai hsKhoaDongCoc(nut,false) nua, nut khoa vinh
    vien. Chuoi duoi day lam DUNG thao tac khach: mo man can coc, bam DUNG
    mot khoan can noi sao ke, roi bam lai LAN HAI - khong goi them ham nao
    khac ngoai chuoi do (dieu 15). */
 danhRows=[{name:'PE-1',ngay:'2026-09-10',con_coc:3000000,can_noi_sao_ke:true}];
 ({c,tai}=env());
 await c.hsMoCanCoc('NCC-1',[{hoa_don:'HD-1',so_tien:2000000}],()=>{});
 const nutCanNoi=tai.querySelector('[data-hscoc]');
 const bamCanNoi=khung._nghe.click[0];
 const soSheetTruoc=sheetCalls.length;
 await bamCanNoi({target:nutCanNoi});
 assert.equal(sheetCalls.length,soSheetTruoc+1);
 assert.equal(nutCanNoi.getAttribute('data-hsdang'),null,'nut phai duoc mo khoa ngay sau khi tam truot da mo, vi tam truot che het man nen khong ai bam trung nut cu duoc');
 assert.equal(nutCanNoi.style.pointerEvents,'');
 assert.equal(nutCanNoi.disabled,false);
 await bamCanNoi({target:nutCanNoi});
 assert.equal(sheetCalls.length,soSheetTruoc+2,'bam lai lan hai phai mo duoc tam truot lan nua, khong bi khoa vinh vien');
 console.log('PASS APP cọc P2-1: đóng tấm trượt sao kê (>8 giao dịch) không khoá vĩnh viễn nút cấn cọc');

 console.log('PASS APP cọc: mất phản hồi, tải lại trang, retry giữ nguyên mã và payload');
})().catch(e=>{console.error(e);process.exitCode=1;});

// Đối chứng: dialog mở đúng nhưng lỗi JS vẫn phải làm kiểm Desk đỏ.
const fs=require('fs'),path=require('path'),{spawnSync}=require('child_process');
if(process.env.GITHUB_ACTIONS!=='true'||!process.env.VGB_ARTIFACTS)throw Error('Chỉ CI riêng');
const out=path.join(process.env.VGB_ARTIFACTS,'doi-chung-pageerror');
fs.mkdirSync(out,{recursive:true});
const r=spawnSync(process.execPath,[path.join(__dirname,'kiem_pancake.cjs')],{
  env:{...process.env,VGB_ARTIFACTS:out,VGB_KIEM_PAGEERROR:'1'},encoding:'utf8',timeout:120000
});
if(r.status!==1||!r.stderr.includes('THU210_PAGEERROR')){
  throw Error('Ca Desk không bắt lỗi JS đúng đường: '+r.status+' '+r.stderr);
}
const evidence=JSON.parse(fs.readFileSync(path.join(out,'pancake-desk-loi-390.json'),'utf8'));
if(!evidence.errors.includes('THU210_PAGEERROR'))throw Error('Không có pageerror thật');
console.log('PASS #210: dialog mở nhưng pageerror làm ca đỏ');

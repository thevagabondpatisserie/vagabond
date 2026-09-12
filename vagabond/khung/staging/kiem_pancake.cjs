// #210: mở form Desk thật và hộp đối soát; không xác nhận mở lại hoặc POST nhà cung cấp.
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {chromium}=require('playwright');
(async()=>{
  if(process.env.GITHUB_ACTIONS!=='true'||!process.env.VGB_ARTIFACTS)throw Error('Chỉ CI riêng');
  const base='http://127.0.0.1:8000',out=process.env.VGB_ARTIFACTS;
  const name=crypto.createHash('sha256').update('THU210\0THU210-HAI-JOB').digest('hex');
  const browser=await chromium.launch({headless:true});
  try{
    for(const width of [390,1280]){
      const ctx=await browser.newContext({viewport:{width,height:900},serviceWorkers:'block'});
      await ctx.route('**/*',r=>new URL(r.request().url()).origin===base?r.continue():r.abort());
      const login=await ctx.request.post(base+'/api/method/login',{form:{usr:'Administrator',pwd:'bench-only-admin'}});
      if(!login.ok())throw Error('Đăng nhập CI lỗi');
      const page=await ctx.newPage();
      await page.goto(base+'/app/vagabond-day-pancake/'+name,{waitUntil:'load'});
      await page.getByRole('button',{name:'Đối soát và mở lại',exact:true}).click({timeout:60000});
      const dialog=page.locator('.modal:visible');
      await dialog.locator('[data-fieldname="ly_do"] textarea').waitFor();
      await dialog.locator('[data-fieldname="bang_chung"] textarea').waitFor();
      if(await dialog.locator('[data-fieldname="xac_nhan_chua_tao"] input').isChecked())throw Error('Xác nhận không được tick sẵn');
      await page.screenshot({path:path.join(out,'pancake-doi-soat-'+width+'.png'),fullPage:true});
      await page.keyboard.press('Escape');
      await ctx.close();
    }
    fs.writeFileSync(path.join(out,'pancake-desk.json'),JSON.stringify({dat:true,widths:[390,1280],xac_nhan:false}));
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});

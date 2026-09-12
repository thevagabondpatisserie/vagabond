// Kiểm mở màn thật trước khi dựng dữ liệu benchmark đại diện cho Kiểm bánh.
const fs = require('fs');
const path = require('path');
const {chromium} = require('playwright');
(async () => {
  if (process.env.GITHUB_ACTIONS !== 'true') throw new Error('Chỉ dùng CI riêng.');
  const dich = process.env.VGB_ARTIFACTS;
  if (!dich) throw new Error('Thiếu thư mục bằng chứng.');
  const goc = 'http://127.0.0.1:8000';
  const browser = await chromium.launch({headless:true});
  const ket = [];
  try {
    for (const rong of [390, 1280]) {
      const canh = await browser.newContext({viewport:{width:rong,height:900},serviceWorkers:'block'});
      await canh.route('**/*', r => new URL(r.request().url()).origin === goc ? r.continue() : r.abort());
      const login = await canh.request.post(goc+'/api/method/login',{form:{usr:'Administrator',pwd:'bench-only-admin'}});
      if (!login.ok()) throw new Error('Đăng nhập CI thất bại.');
      const p = await canh.newPage();
      const loi = [];
      p.on('pageerror', e => loi.push(e.message));
      p.on('response', r => {if(r.url().includes('/api/') && r.status() >= 400) loi.push(new URL(r.url()).pathname+':'+r.status());});
      await canh.tracing.start({screenshots:true,snapshots:true});
      let dat = false;
      const dau = Date.now();
      try {
        const dongBo = p.waitForResponse(r => new URL(r.url()).pathname === '/api/method/vagabond.kiem_banh.dong_bo')
          .then(r => ({r}), e => ({e}));
        const html = await p.goto(goc+'/kiem-banh',{waitUntil:'load'});
        if (!html || !html.ok()) throw new Error('Không mở được trang Kiểm bánh.');
        const ketDongBo = await dongBo;
        if (ketDongBo.e) throw ketDongBo.e;
        const r = ketDongBo.r;
        const body = await r.json();
        if (!r.ok() || !body.message || body.message.loi) throw new Error('Đồng bộ Kiểm bánh chưa thành công.');
        await p.locator('#kb-luoi .kb-trong').filter({hasText:'chưa có đơn nào'}).waitFor();
        if (await p.locator('#kb-canh').isVisible()) throw new Error('Màn đang hiện cảnh báo nguồn.');
        if (loi.length) throw new Error('Có lỗi JS/API trên màn.');
        dat = true;
      } catch(e) {loi.push(e.message);}
      ket.push({rong,dat,ms:Date.now()-dau,loi,du_lieu:'ngày trống, chưa phải baseline'});
      await p.screenshot({path:path.join(dich,'kiem-banh-'+rong+'.png'),fullPage:true});
      await canh.tracing.stop({path:path.join(dich,'kiem-banh-'+rong+'.zip')});
      await canh.close();
    }
  } finally {
    await browser.close();
    fs.writeFileSync(path.join(dich,'kiem-banh-mo-man.json'),JSON.stringify(ket,null,2));
  }
  console.log(JSON.stringify(ket));
  if (ket.length !== 2 || ket.some(x=>!x.dat)) process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});

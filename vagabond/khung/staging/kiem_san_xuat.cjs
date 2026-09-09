// #257: hoàn tất lệnh trên app, gói lô và SLE/GL được kiểm bằng CLI kế tiếp.
const fs = require('fs');
const path = require('path');
const {chromium} = require('playwright');

(async () => {
  if (process.env.GITHUB_ACTIONS !== 'true') throw new Error('Chỉ dùng CI riêng.');
  const dich = process.env.VGB_ARTIFACTS;
  const f = JSON.parse(fs.readFileSync(path.join(dich, 'san-xuat-fixture.json')));
  const goc = 'http://127.0.0.1:8000';
  const trinh = await chromium.launch({headless: true});
  const c = await trinh.newContext({viewport: {width: 390, height: 900}, serviceWorkers: 'block'});
  const ket = {dat: false};
  try {
    await c.route('**/*', r => new URL(r.request().url()).origin === goc ? r.continue() : r.abort());
    const dn = await c.request.post(goc + '/api/method/login', {form: {usr: 'Administrator', pwd: 'bench-only-admin'}});
    if (!dn.ok()) throw new Error('Đăng nhập thất bại');
    await c.tracing.start({screenshots: true, snapshots: true});
    const p = await c.newPage();
    const loi = [];
    p.on('pageerror', e => loi.push(e.message));
    await p.goto(goc + '/san-xuat');
    await p.locator('[data-n="' + f.lenh + '"]').click();
    await p.locator('#mFin').click();
    if (await p.locator('#htLenh').inputValue() !== '2') throw new Error('Phải còn làm2');
    await p.locator('#htCan').fill('2');
    const doi = p.waitForResponse(r => r.url().includes('/api/method/vagabond.kho_san_xuat.hoan_tat_phieu'), {timeout: 60000});
    await p.locator('.sh [data-y]').click();
    const r = await doi;
    if (!r.ok() || !(await r.json()).message) throw new Error('Hoàn tất sản xuất thất bại');
    // Có thành phẩm theo lô thì app mở màn in tem; không bấm in thật.
    await p.locator('#mlGo').waitFor({timeout: 60000});
    await p.screenshot({path: path.join(dich, 'san-xuat-tem.png'), fullPage: true});
    await p.goto(goc + '/san-xuat');
    await p.locator('[data-t="done"]').click();
    await p.locator('[data-n="' + f.lenh + '"]').click();
    await p.locator('#mLbl').waitFor();
    if (await p.locator('#mFin').count()) throw new Error('Lệnh đã đủ vẫn cho hoàn tất tiếp');
    if (loi.length) throw new Error(loi.join('\n'));
    await p.screenshot({path: path.join(dich, 'san-xuat-xong.png'), fullPage: true});
    ket.dat = true;
  } catch (e) {ket.loi = e.stack; throw e;}
  finally {
    await c.tracing.stop({path: path.join(dich, 'san-xuat.zip')}).catch(() => {});
    await trinh.close();
    fs.writeFileSync(path.join(dich, 'san-xuat-browser.json'), JSON.stringify(ket, null, 2));
  }
})().catch(e => {console.error(e); process.exitCode = 1;});

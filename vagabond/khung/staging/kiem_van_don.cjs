// #257: bấm đúng nút app, không gọi helper hoặc tự sửa DB thay thao tác.
const fs = require('fs');
const path = require('path');
const {chromium} = require('playwright');

(async () => {
  if (process.env.GITHUB_ACTIONS !== 'true') throw new Error('Chỉ chạy trên CI riêng.');
  const dich = process.env.VGB_ARTIFACTS;
  const f = JSON.parse(fs.readFileSync(path.join(dich, 'van-don-fixture.json')));
  const goc = 'http://127.0.0.1:8000';
  const trinh = await chromium.launch({headless: true});
  const canh = await trinh.newContext({viewport: {width: 390, height: 900}, serviceWorkers: 'block'});
  const ket = {dat: false, buoc: []};
  try {
    await canh.route('**/*', r => new URL(r.request().url()).origin === goc ? r.continue() : r.abort());
    const dn = await canh.request.post(goc + '/api/method/login', {form: {usr: 'Administrator', pwd: 'bench-only-admin'}});
    if (!dn.ok()) throw new Error('Đăng nhập thất bại');
    await canh.tracing.start({screenshots: true, snapshots: true});
    const p = await canh.newPage();
    const loi = [];
    p.on('pageerror', e => loi.push(e.message));
    await p.goto(goc + '/van-don');
    await p.locator('#vdDate').waitFor();
    async function ngay(d) {
      const oCu = await p.locator('#vdDate').elementHandle();
      const doi = p.waitForResponse(r => r.url().includes('/api/method/vagabond.van_don.danh_sach'));
      await p.locator('#vdDate').fill(d);
      const r = await doi;
      if (!r.ok() || !(await r.json()).message) throw new Error('Không tải được ngày ' + d);
      await p.waitForFunction(o => !o.isConnected, oCu);
      await p.locator('#vdDate').waitFor({state: 'visible'});
      if (await p.locator('#vdDate').inputValue() !== d) throw new Error('Màn đang hiện sai ngày');
      await oCu.dispose();
    }
    const the = p.locator('[data-vd="' + f.ten + '"]');
    await ngay(f.ngay_cu);
    await the.waitFor({state: 'visible'});
    ket.buoc.push('Đơn có ở ngày cũ trước cập nhật');
    async function dongBo() {
      const nutCu = await p.locator('#vdDongBo').elementHandle();
      const doi = p.waitForResponse(r => r.url().includes('/api/method/vagabond.van_don.dong_bo_pancake'));
      const taiLai = p.waitForResponse(r => r.url().includes('/api/method/vagabond.van_don.danh_sach'));
      await p.locator('#vdDongBo').click();
      const r = await doi;
      const k = (await r.json()).message;
      if (!r.ok() || !k || (k.loi || []).length) throw new Error('Đồng bộ trả lỗi');
      const ds = await taiLai;
      if (!ds.ok() || !(await ds.json()).message) throw new Error('Tải lại sau đồng bộ thất bại');
      await p.waitForFunction(nut => !nut.isConnected, nutCu);
      await p.locator('#vdDongBo').waitFor({state: 'visible'});
      await nutCu.dispose();
    }
    await dongBo();
    await the.waitFor({state: 'hidden'});
    ket.buoc.push('Đơn rời ngày cũ sau khi bấm đồng bộ');
    await ngay(f.ngay_moi);
    await the.waitFor({state: 'visible'});
    await dongBo();
    await the.waitFor({state: 'visible'});
    if (await the.count() !== 1) throw new Error('Trùng đơn trên màn');
    if (loi.length) throw new Error(loi.join('\n'));
    ket.buoc.push('Đơn ở ngày mới, đồng bộ lại vẫn đúng một thẻ');
    await p.screenshot({path: path.join(dich, 'van-don-doi-ngay.png'), fullPage: true});
    ket.dat = true;
  } catch (e) {ket.loi = e.stack; throw e;}
  finally {
    await canh.tracing.stop({path: path.join(dich, 'van-don-doi-ngay.zip')}).catch(() => {});
    await trinh.close();
    fs.writeFileSync(path.join(dich, 'van-don-browser.json'), JSON.stringify(ket, null, 2));
  }
})().catch(e => {console.error(e); process.exitCode = 1;});

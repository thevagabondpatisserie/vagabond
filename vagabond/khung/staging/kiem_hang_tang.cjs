// Duyệt và ghi sổ từ app. CLI kế tiếp đối chiếu SLE/GL; chưa kiểm hủy/HĐĐT.
const fs = require('fs');
const path = require('path');
const {chromium} = require('playwright');

(async () => {
  if (process.env.GITHUB_ACTIONS !== 'true') throw new Error('Chỉ dùng CI riêng.');
  const dich = process.env.VGB_ARTIFACTS;
  const f = JSON.parse(fs.readFileSync(path.join(dich, 'hang-tang-fixture.json')));
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
    await p.goto(goc + '/duyet-don-hang-tang');
    await p.locator('[data-dtgm="' + f.hoa_don + '"]').click();
    await p.locator('[data-dtgok="' + f.hoa_don + '"]').click();
    await p.locator('#hqIn').fill('Duyet ca thu staging257');
    const duyet = p.waitForResponse(r => r.url().includes('/api/method/vagabond.hang_tang.duyet'));
    await p.locator('[data-hqok]').click();
    if (!(await duyet).ok()) throw new Error('Duyệt hàng tặng thất bại');
    await p.goto(goc + '/hoa-don-ban');
    const sepay = p.waitForResponse(r => r.url().includes('/api/method/vgb_gd_sepay'))
      .then(r => ({r}), e => ({e}));
    await p.locator('[data-hdb="' + f.hoa_don + '"]').click();
    const tra = await sepay;
    if (tra.e) throw tra.e;
    const gd = tra.r;
    const duLieu = await gd.json();
    ket.sepay = {status: gd.status(), body: duLieu};
    if (!gd.ok() || duLieu.message?.don !== 'THU257-TANG' ||
        duLieu.message?.so_giao_dich !== 0 || duLieu.message?.tong_da_nhan !== 0 ||
        !Array.isArray(duLieu.message?.giao_dich) || duLieu.message.giao_dich.length)
      throw new Error('API SePay không trả đúng đơn thử chưa chuyển khoản');
    await p.locator('#dsvSepay').getByText('Chưa nhận được chuyển khoản nào mang mã đơn này.', {exact: true}).waitFor();
    await p.locator('#dsvChot').click();
    const ghi = p.waitForResponse(r => r.url().includes('/api/method/vagabond.ban_hang.chot_mot_don'), {timeout: 60000});
    await p.locator('[data-hkok]').click();
    const r = await ghi;
    const kq = await r.json();
    if (!r.ok() || !kq.message?.ok || kq.message.name !== f.hoa_don) throw new Error('Ghi sổ hàng tặng thất bại');
    if (kq.message.da_xuat_hddt) throw new Error('Ca chỉ ghi sổ không được nhận đã xuất HĐĐT');
    // Trang mới đọc lại chứng từ, không dùng thẻ trước POST làm bằng chứng.
    await p.goto(goc + '/hoa-don-ban');
    await p.locator('[data-hdb="' + f.hoa_don + '"]').click();
    await p.getByText('✅ Đã chốt', {exact: true}).waitFor();
    if (await p.locator('#dsvChot').count()) throw new Error('Vẫn còn nút ghi sổ trên đơn đã chốt');
    if (loi.length) throw new Error(loi.join('\n'));
    await p.screenshot({path: path.join(dich, 'hang-tang-xong.png'), fullPage: true});
    ket.dat = true;
  } catch (e) {ket.loi = e.stack; throw e;}
  finally {
    await c.tracing.stop({path: path.join(dich, 'hang-tang.zip')}).catch(() => {});
    await trinh.close();
    fs.writeFileSync(path.join(dich, 'hang-tang-browser.json'), JSON.stringify(ket, null, 2));
  }
})().catch(e => {console.error(e); process.exitCode = 1;});

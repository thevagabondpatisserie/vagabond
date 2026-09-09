// Đo lọc300 hồ sơ nháp và tìm một mã bằng Enter đúng thao tác app.
const fs = require('fs');
const path = require('path');
const {chromium} = require('playwright');
(async () => {
  if (process.env.GITHUB_ACTIONS !== 'true') throw new Error('Chỉ dùng CI riêng.');
  const dich = process.env.VGB_ARTIFACTS;
  const f = JSON.parse(fs.readFileSync(path.join(dich, 'tai-ho-so.json')));
  const goc = 'http://127.0.0.1:8000';
  const browser = await chromium.launch({headless: true});
  const ket = [];
  try {
    for (const rong of [390, 1280]) for (let lan = 0; lan < 5; lan++) {
      const c = await browser.newContext({viewport: {width: rong, height: 900}, serviceWorkers: 'block'});
      let p;
      await c.tracing.start({screenshots: true, snapshots: true});
      try {
        await c.route('**/*', r => new URL(r.request().url()).origin === goc ? r.continue() : r.abort());
        const dn = await c.request.post(goc + '/api/method/login', {form: {usr: 'Administrator', pwd: 'bench-only-admin'}});
        if (!dn.ok()) throw new Error('Đăng nhập thất bại');
        p = await c.newPage();
        const loi = [];
        p.on('pageerror', e => loi.push(e.message));
        p.on('response', r => {if (r.url().includes('/api/') && r.status() >= 400) loi.push('API ' + r.status());});
        await p.goto(goc + '/ho-so-thanh-toan');
        await p.locator('#hsTimO').waitFor();
        for (const [tu, ids] of [[f.tu_khoa, f.ten], [f.tim_ma, [f.tim_ma]]]) {
          const cu = await p.locator('#hsTimO').elementHandle();
          const doi = p.waitForResponse(r => r.url().includes('/api/method/vagabond.ho_so_tt.danh_sach'))
            .then(r => ({r}), e => ({e}));
          const dau = performance.now();
          await p.locator('#hsTimO').fill(tu);
          await p.locator('#hsTimO').press('Enter');
          const tra = await doi;
          if (tra.e) throw tra.e;
          const m = (await tra.r.json()).message;
          if (!tra.r.ok() || !Array.isArray(m?.rows) ||
              JSON.stringify(m.rows.map(r => r.name).sort()) !== JSON.stringify([...ids].sort()))
            throw new Error('API sai tập hồ sơ');
          if (m.rows.some(r => r.tong_tien !== 6000 || r.trang_thai !== 'Nhap')) throw new Error('API sai tiền/trạng thái');
          await p.waitForFunction(o => !o.isConnected, cu);
          await cu.dispose();
          await p.waitForFunction(n => document.querySelectorAll('[data-hs]').length === n, ids.length);
          const ds = await p.locator('[data-hs]').evaluateAll(rows => rows.map(r => r.getAttribute('data-hs')).sort());
          if (JSON.stringify(ds) !== JSON.stringify([...ids].sort()) || loi.length) throw new Error('DOM sai tập hoặc có lỗi');
          ket.push({rong, lan, so_ho_so: ids.length, ms: performance.now() - dau, dat: true,
            lenh_driver: {fill: 1, enter: 1}, nguon: '300 hoàn ứng nháp tổng hợp, gồm driver/đối chiếu'});
        }
      } catch (e) {
        if (p) {
          await p.screenshot({path: path.join(dich, 'do-ho-so-' + rong + '-' + lan + '.png'), fullPage: true}).catch(() => {});
          fs.writeFileSync(path.join(dich, 'do-ho-so-' + rong + '-' + lan + '.html'), await p.content().catch(() => ''));
        }
        ket.push({rong, lan, dat: false, loi: String(e.stack)});
        throw e;
      } finally {
        await c.tracing.stop({path: path.join(dich, 'do-ho-so-' + rong + '-' + lan + '.zip')});
        await c.close();
      }
    }
  } finally {
    await browser.close();
    fs.writeFileSync(path.join(dich, 'do-ho-so.json'), JSON.stringify(ket, null, 2));
  }
  if (ket.length !== 20) throw new Error('Thiếu lượt đo');
})().catch(e => {console.error(e); process.exitCode = 1;});

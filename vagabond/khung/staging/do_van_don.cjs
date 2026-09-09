// Đo đổi ngày và tìm mã trên app thật, xác nhận đủ thẻ trước ghi thời gian.
// Mức100/500 là tải tổng hợp, chưa phải phân bố dữ liệu site đã đo.
const fs = require('fs');
const path = require('path');
const {chromium} = require('playwright');
(async () => {
  if (process.env.GITHUB_ACTIONS !== 'true') throw new Error('Chỉ dùng CI riêng.');
  const dich = process.env.VGB_ARTIFACTS;
  const mau = JSON.parse(fs.readFileSync(path.join(dich, 'tai-van-don.json')));
  const goc = 'http://127.0.0.1:8000';
  const browser = await chromium.launch({headless: true});
  const ket = [];
  try {
    for (const rong of [390, 1280]) {
      for (let lan = 0; lan < 5; lan++) {
        const c = await browser.newContext({viewport: {width: rong, height: 900}, serviceWorkers: 'block'});
        try {
          await c.route('**/*', r => new URL(r.request().url()).origin === goc ? r.continue() : r.abort());
          const dn = await c.request.post(goc + '/api/method/login', {form: {usr: 'Administrator', pwd: 'bench-only-admin'}});
          if (!dn.ok()) throw new Error('Đăng nhập thất bại');
          const p = await c.newPage();
          const loi = [];
          p.on('pageerror', e => loi.push(e.message));
          p.on('response', r => {if (r.url().includes('/api/') && r.status() >= 400) loi.push('API ' + r.status());});
          await p.goto(goc + '/van-don');
          await p.locator('#vdDate').waitFor();
          for (const f of mau) {
            const cu = await p.locator('#vdDate').elementHandle();
            const doi = p.waitForResponse(r => r.url().includes('/api/method/vagabond.van_don.danh_sach'))
              .then(r => ({r}), e => ({e}));
            const dau = performance.now();
            await p.locator('#vdDate').fill(f.ngay);
            const tra = await doi;
            if (tra.e) throw tra.e;
            const body = await tra.r.json();
            if (!tra.r.ok() || body.message?.length !== f.so_don) throw new Error('API thiếu vận đơn tải thử');
            if (JSON.stringify(body.message.map(d => d.name).sort()) !== JSON.stringify([...f.ten].sort()))
              throw new Error('API trả sai tập vận đơn');
            await p.waitForFunction(o => !o.isConnected, cu);
            await cu.dispose();
            await p.waitForFunction(n => document.querySelectorAll('[data-vd]').length === n, f.so_don);
            const the = await p.locator('[data-vd]').evaluateAll(ds => ds.map(d => d.getAttribute('data-vd')).sort());
            if (JSON.stringify(the) !== JSON.stringify([...f.ten].sort())) throw new Error('DOM sai tập vận đơn');
            const mo_ms = performance.now() - dau;
            const tim = performance.now();
            await p.locator('#vdQ').fill(f.tim_ma);
            await p.waitForFunction(() => document.querySelectorAll('[data-vd]').length === 1);
            if (!(await p.locator('[data-vd]').innerText()).includes(f.tim_ma)) throw new Error('Tìm ra sai đơn');
            const tim_ms = performance.now() - tim;
            if (loi.length) throw new Error(loi.join('; '));
            ket.push({rong, lan, so_don: f.so_don, mo_ms, tim_ms, dat: true,
              lenh_driver: {fill_ngay: 1, fill_tim: 1}, nguon: 'tải tổng hợp'});
            // Xoá bộ lọc qua ô thật, đợi đủ thẻ trước phép đo ngày tiếp theo.
            await p.locator('#vdQ').fill('');
            await p.waitForFunction(n => document.querySelectorAll('[data-vd]').length === n, f.so_don);
          }
        } finally {await c.close();}
      }
    }
  } finally {
    await browser.close();
    fs.writeFileSync(path.join(dich, 'do-van-don.json'), JSON.stringify(ket, null, 2));
  }
  if (ket.length !== 20) throw new Error('Thiếu lượt đo');
})().catch(e => {console.error(e); process.exitCode = 1;});

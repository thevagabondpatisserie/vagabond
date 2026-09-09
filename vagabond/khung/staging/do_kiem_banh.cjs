// Đo chọn ngày Kiểm bánh, so đủ mã và số bán được trên API lẫn màn hình.
const fs = require('fs');
const path = require('path');
const {chromium} = require('playwright');
(async () => {
  if (process.env.GITHUB_ACTIONS !== 'true') throw new Error('Chỉ dùng CI riêng.');
  const dich = process.env.VGB_ARTIFACTS;
  const mau = JSON.parse(fs.readFileSync(path.join(dich, 'tai-kiem-banh.json')));
  const goc = 'http://127.0.0.1:8000';
  const browser = await chromium.launch({headless: true});
  const ket = [];
  try {
    for (const rong of [390, 1280]) {
      for (let lan = 0; lan < 5; lan++) {
        const c = await browser.newContext({viewport: {width: rong, height: 900}, timezoneId: 'Asia/Ho_Chi_Minh', serviceWorkers: 'block'});
        try {
          await c.route('**/*', r => new URL(r.request().url()).origin === goc ? r.continue() : r.abort());
          const dn = await c.request.post(goc + '/api/method/login', {form: {usr: 'Administrator', pwd: 'bench-only-admin'}});
          if (!dn.ok()) throw new Error('Đăng nhập thất bại');
          const p = await c.newPage();
          const loi = [];
          p.on('pageerror', e => loi.push(e.message));
          p.on('response', r => {if (r.url().includes('/api/') && r.status() >= 400) loi.push('API ' + r.status());});
          await p.goto(goc + '/kiem-banh');
          await p.locator('#kb-chips').waitFor();
          for (const f of mau) {
            const doi = p.waitForResponse(r => r.url().includes('/api/method/vagabond.kiem_banh.dong_bo') && r.request().postData()?.includes(f.ngay))
              .then(r => ({r}), e => ({e}));
            const dau = performance.now();
            await p.locator('#kb-chips [data-ngay="' + f.ngay + '"]').click();
            const tra = await doi;
            if (tra.e) throw tra.e;
            const soNguon = Number(tra.r.headers()['x-vgb-ci-source-calls']);
            if (!Number.isInteger(soNguon) || soNguon < 0) throw new Error('Thiếu bộ đếm nguồn theo request');
            const m = (await tra.r.json()).message;
            if (!tra.r.ok() || m?.loi || m?.ngay !== f.ngay || m?.dong?.length !== f.so_dong)
              throw new Error('Đồng bộ không trả đúng ngày và đủ dòng');
            if (JSON.stringify(m.dong.map(d => d.ma_hang).sort()) !== JSON.stringify([...f.ma].sort()) ||
                m.dong.some(d => d.co_the_ban !== f.co_the_ban)) throw new Error('API sai mã/số bán được');
            await p.waitForFunction(n => document.querySelectorAll('#kb-luoi .kb-the').length === n, f.so_dong);
            const ds = await p.locator('#kb-luoi .kb-the').evaluateAll(rows => rows.map(r => ({
              ma: r.querySelector('.kb-ten b').textContent,
              ban: Number(r.querySelector('.kb-ban b').textContent)
            })));
            if (JSON.stringify(ds.map(d => d.ma).sort()) !== JSON.stringify([...f.ma].sort()) ||
                ds.some(d => d.ban !== f.co_the_ban)) throw new Error('DOM sai mã/số bán được');
            if (await p.locator('#kb-canh').isVisible() || loi.length) throw new Error('Màn có cảnh báo/lỗi');
            ket.push({rong, lan, so_dong: f.so_dong, mo_ms: performance.now() - dau,
              dat: true, so_goi_nguon: soNguon, duong_doc: soNguon ? 'đọc nguồn HTTP giả' : 'không gọi nguồn trong request', lenh_driver: {click_ngay: 1}, nguon: 'tải tổng hợp, gồm driver và đối chiếu'});
          }
        } finally {await c.close();}
      }
    }
  } finally {
    await browser.close();
    fs.writeFileSync(path.join(dich, 'do-kiem-banh.json'), JSON.stringify(ket, null, 2));
  }
  if (ket.length !== 20) throw new Error('Thiếu lượt đo');
})().catch(e => {console.error(e); process.exitCode = 1;});

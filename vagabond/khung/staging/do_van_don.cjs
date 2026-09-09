// Đo đổi ngày và tìm mã trên app thật, xác nhận đủ thẻ trước ghi thời gian.
// Mức100/500 là tải tổng hợp, chưa phải phân bố dữ liệu site đã đo.
const fs = require('fs');
const path = require('path');
const {chromium} = require('playwright');
const crypto = require('crypto');
(async () => {
  if (process.env.GITHUB_ACTIONS !== 'true') throw new Error('Chỉ dùng CI riêng.');
  const dich = process.env.VGB_ARTIFACTS;
  const mau = JSON.parse(fs.readFileSync(path.join(dich, 'tai-van-don.json')));
  const goc = 'http://127.0.0.1:8000';
  const ket = [];
  const ab = process.env.VGB_DOI_CHUNG_VD === '1';
  const doiChung = JSON.parse(fs.readFileSync(path.join(__dirname, 'doi_chung_van_don.json')));
  const asset = fs.readFileSync(path.join(__dirname, '../../public/js/app_bep.js'), 'utf8');
  const assetHash = crypto.createHash('sha256').update(asset).digest('hex');
  // Chỉ thay đoạn tải dữ liệu trong bộ nhớ trình duyệt CI; không ghi bundle/site.
  if (ab && asset.split(doiChung.moi).length !== 2) throw new Error('Đối chứng không khớp đúng một đoạn code');
  const tenDo = ab ? 'doi-chung-van-don' : 'do-van-don';
  const browser = await chromium.launch({headless: true});
  try {
    for (const rong of [390, 1280]) {
      for (let lan = 0; lan < (ab ? 6 : 5); lan++) {
        // Đảo thứ tự AB/BA theo cặp để giảm ảnh hưởng máy nóng và cache.
        for (const bienThe of (ab ? (lan % 2 ? ['moi', 'cu'] : ['cu', 'moi']) : ['moi'])) {
        const c = await browser.newContext({viewport: {width: rong, height: 900}, serviceWorkers: 'block'});
        let p;
        let soAsset = 0;
        const loiRoute = [];
        const noiDung = ab && bienThe === 'cu' ? asset.replace(doiChung.moi, doiChung.cu) : asset;
        const noiDungHash = crypto.createHash('sha256').update(noiDung).digest('hex');
        await c.tracing.start({screenshots: true, snapshots: true});
        try {
          await c.route('**/*', r => new URL(r.request().url()).origin === goc ? r.continue() : r.abort());
          if (ab) await c.route('**/assets/vagabond/js/app_bep.js*', async r => {
            try {
            if (new URL(r.request().url()).origin !== goc) return r.abort();
            const response = await r.fetch();
            if (!response.ok() || await response.text() !== asset) throw new Error('Asset site không khớp checkout');
            soAsset++;
            await r.fulfill({response, body: noiDung});
            } catch (e) {
              loiRoute.push(String(e.stack || e));
              await r.abort().catch(() => {});
            }
          });
          const dn = await c.request.post(goc + '/api/method/login', {form: {usr: 'Administrator', pwd: 'bench-only-admin'}});
          if (!dn.ok()) throw new Error('Đăng nhập thất bại');
          p = await c.newPage();
          const loi = [];
          p.on('pageerror', e => loi.push(e.message));
          p.on('response', r => {if (r.url().includes('/api/') && r.status() >= 400) loi.push('API ' + r.status());});
          await p.goto(goc + '/van-don');
          await p.locator('#vdDate').waitFor();
          if (loiRoute.length) throw new Error(loiRoute.join('; '));
          if (ab && soAsset !== 1) throw new Error('Không xác minh được asset đối chứng');
          for (const f of mau) {
            const cu = await p.locator('#vdDate').elementHandle();
            const doi = p.waitForResponse(r => r.url().includes('/api/method/vagabond.van_don.danh_sach'))
              .then(r => ({r}), e => ({e}));
            const dau = performance.now();
            await p.locator('#vdDate').fill(f.ngay);
            const tra = await doi;
            if (tra.e) throw tra.e;
            // Headers của API danh sách, gồm fill/driver; body có thể chưa đủ.
            const api_ms = performance.now() - dau;
            const docApi = performance.now();
            const body = await tra.r.json();
            if (!tra.r.ok() || body.message?.length !== f.so_don) throw new Error('API thiếu vận đơn tải thử');
            if (JSON.stringify(body.message.map(d => d.name).sort()) !== JSON.stringify([...f.ten].sort()))
              throw new Error('API trả sai tập vận đơn');
            const doi_chieu_api_ms = performance.now() - docApi;
            const doiDom = performance.now();
            await p.waitForFunction(o => !o.isConnected, cu);
            await cu.dispose();
            await p.waitForFunction(n => document.querySelectorAll('[data-vd]').length === n, f.so_don);
            const the = await p.locator('[data-vd]').evaluateAll(ds => ds.map(d => d.getAttribute('data-vd')).sort());
            if (JSON.stringify(the) !== JSON.stringify([...f.ten].sort())) throw new Error('DOM sai tập vận đơn');
            // Phần chờ còn lại có thể gồm API phụ, không phải riêng CPU render.
            const dom_ms = performance.now() - doiDom;
            const mo_ms = performance.now() - dau;
            const tim = performance.now();
            await p.locator('#vdQ').fill(f.tim_ma);
            await p.waitForFunction(() => document.querySelectorAll('[data-vd]').length === 1);
            if (!(await p.locator('[data-vd]').innerText()).includes(f.tim_ma)) throw new Error('Tìm ra sai đơn');
            const tim_ms = performance.now() - tim;
            if (loi.length) throw new Error(loi.join('; '));
            ket.push({rong, lan, bien_the: bienThe, asset_sha256: assetHash, noi_dung_sha256: ab ? noiDungHash : null, baseline_sha: ab ? doiChung.baseline_sha : null, so_don: f.so_don, mo_ms, tim_ms, api_ms, doi_chieu_api_ms, dom_ms, dat: true,
              lenh_driver: {fill_ngay: 1, fill_tim: 1}, nguon: 'tải tổng hợp'});
            // Xoá bộ lọc qua ô thật, đợi đủ thẻ trước phép đo ngày tiếp theo.
            await p.locator('#vdQ').fill('');
            await p.waitForFunction(n => document.querySelectorAll('[data-vd]').length === n, f.so_don);
          }
        } catch (e) {
          const tep = tenDo + '-' + rong + '-' + lan + '-' + bienThe;
          if (p) {
            await p.screenshot({path: path.join(dich, tep + '.png'), fullPage: true}).catch(() => {});
            fs.writeFileSync(path.join(dich, tep + '.html'), await p.content().catch(() => ''));
          }
          ket.push({rong, lan, bien_the: bienThe, loi_route: loiRoute, dat: false, loi: String(e.stack)});
          throw e;
        } finally {
          await c.tracing.stop({path: path.join(dich, tenDo + '-' + rong + '-' + lan + '-' + bienThe + '.zip')});
          await c.close();
        }
      }
    }
    }
  } finally {
    await browser.close();
    fs.writeFileSync(path.join(dich, tenDo + '.json'), JSON.stringify(ket, null, 2));
  }
  if (ket.length !== (ab ? 48 : 20)) throw new Error('Thiếu lượt đo');
})().catch(e => {console.error(e); process.exitCode = 1;});

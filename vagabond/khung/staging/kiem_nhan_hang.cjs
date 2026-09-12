// #257: lỗi kho thật phải thả ô số; sửa rồi gửi lại phải ghi đúng một phiếu.
const fs = require('fs');
const path = require('path');
const {chromium} = require('playwright');

(async () => {
  if (process.env.GITHUB_ACTIONS !== 'true') throw new Error('Chỉ dùng CI riêng.');
  const dich = process.env.VGB_ARTIFACTS;
  const f = JSON.parse(fs.readFileSync(path.join(dich, 'nhan-hang-fixture.json')));
  const goc = 'http://127.0.0.1:8000';
  const trinh = await chromium.launch({headless: true});
  const c = await trinh.newContext({viewport: {width: 390, height: 900}, serviceWorkers: 'block'});
  const ket = {dat: false, buoc: []};
  try {
    await c.route('**/*', r => new URL(r.request().url()).origin === goc ? r.continue() : r.abort());
    const dn = await c.request.post(goc + '/api/method/login', {form: {usr: 'Administrator', pwd: 'bench-only-admin'}});
    if (!dn.ok()) throw new Error('Đăng nhập thất bại');
    await c.tracing.start({screenshots: true, snapshots: true});
    const p = await c.newPage();
    const loi = [];
    p.on('pageerror', e => loi.push(e.message));
    async function moNhan() {
      await p.goto(goc + '/phan-he-dat-hang');
      await p.locator('[data-go="Transfer"]').click();
      await p.locator('[data-n="' + f.phieu + '"]').click();
      await p.locator('#vRecv').click();
    }
    await moNhan();
    const o = p.locator('[data-q="0"]');
    await o.waitFor();
    if (await o.inputValue() !== '50') throw new Error('Mặc định số còn phải nhận phải là50');
    async function gui() {
      await p.locator('#rcOk').click();
      const doi = p.waitForResponse(r => r.url().includes('/api/method/vagabond.lan_nhan.nhan_theo_phieu'));
      await p.locator('.sh [data-y]').click();
      const r = await doi;
      return {status: r.status(), body: await r.json()};
    }
    const oCu = await o.elementHandle();
    const lan1 = await gui();
    if (lan1.status < 400 || lan1.body.exc_type !== 'NegativeStockError') {
      throw new Error('Phải tái hiện đúng lỗi kho âm từ core: ' + JSON.stringify(lan1));
    }
    await p.waitForFunction(el => !el.isConnected, oCu);
    await o.waitFor();
    if (await o.isDisabled()) throw new Error('Lỗi kho âm làm khoá cứng ô số');
    await o.fill('20');
    await o.press('Tab');
    if (await o.inputValue() !== '20') throw new Error('Số sửa bị trả về số cũ');
    ket.buoc.push('Kho30 từ chối nhận50, ô số mở lại và giữ số sửa20');
    const lan2 = await gui();
    if (lan2.status !== 200 || !lan2.body.message || !lan2.body.message.name) throw new Error('Sửa rồi nhận lại thất bại');
    ket.phieu = lan2.body.message.name;
    // Mở lại từ trang mới: không bấm vào chi tiết cũ trong lúc back/render
    // sau POST đang chạy; đồng thời kiểm khoá localStorage qua lần tải mới.
    await moNhan();
    await o.waitFor();
    if (await o.inputValue() !== '30' || await o.isDisabled()) throw new Error('Mở lại phải còn30 và không bị khoá');
    const cho = await p.evaluate(k => localStorage.getItem(k), 'vgbLanNhanCho:Administrator:' + f.phieu);
    if (cho !== null) throw new Error('Lần nhận thành công còn lưu trạng thái chờ');
    if (loi.length) throw new Error(loi.join('\n'));
    ket.buoc.push('Nhận20 thành công, mở lại còn30, không giữ khoá chờ');
    await p.screenshot({path: path.join(dich, 'nhan-hang.png'), fullPage: true});
    ket.dat = true;
  } catch (e) {ket.loi = e.stack; throw e;}
  finally {
    await c.tracing.stop({path: path.join(dich, 'nhan-hang.zip')}).catch(() => {});
    await trinh.close();
    fs.writeFileSync(path.join(dich, 'nhan-hang-browser.json'), JSON.stringify(ket, null, 2));
  }
})().catch(e => {console.error(e); process.exitCode = 1;});

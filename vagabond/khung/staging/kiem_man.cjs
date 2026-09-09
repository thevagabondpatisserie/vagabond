// #257: mở app thật qua HTTP trên bench CI, lưu lỗi và thời gian từng màn.
// Đây là kiểm mở màn, chưa thay các ca E2E ghi sổ và kiểm GL/SLE.
const fs = require('fs');
const path = require('path');
const {chromium} = require('playwright');

(async () => {
  if (process.env.GITHUB_ACTIONS !== 'true') throw new Error('Chỉ chạy trên CI riêng.');
  const goc = 'http://127.0.0.1:8000';
  const dich = process.env.VGB_ARTIFACTS;
  if (!dich) throw new Error('Thiếu thư mục bằng chứng.');
  const trinh = await chromium.launch({headless: true});
  const ket = [];
  try {
    for (const rong of [390, 1280]) {
      const canh = await trinh.newContext({viewport: {width: rong, height: 900}, serviceWorkers: 'block'});
      // Không gửi telemetry, ảnh ngoài hay API của nhà cung cấp thật.
      await canh.route('**/*', r => new URL(r.request().url()).origin === goc ? r.continue() : r.abort());
      const dangNhap = await canh.request.post(goc + '/api/method/login', {form: {usr: 'Administrator', pwd: 'bench-only-admin'}});
      if (!dangNhap.ok()) throw new Error('Không đăng nhập được site CI: ' + dangNhap.status());
      await canh.tracing.start({screenshots: true, snapshots: true});
      for (const [duong, nhan, sanSang] of [
        ['van-don', 'Vận đơn', '#vdDate'],
        ['ho-so-thanh-toan', 'Hồ sơ', '#hsTimO'],
        ['san-xuat', 'Lệnh sản xuất', '#mNoBom'],
        ['don-mua-hang', 'Đơn mua', '#poTim'],
        ['hoa-don-ban', 'Hoá đơn', '#ktBanTim']
      ]) {
        const trang = await canh.newPage();
        const loi = [], api = [];
        trang.on('pageerror', e => loi.push(e.message));
        trang.on('response', r => {if (r.url().includes('/api/')) api.push({duong: new URL(r.url()).pathname, status: r.status()});});
        const batDau = Date.now();
        let dat = false;
        try {
          await trang.goto(goc + '/' + duong, {waitUntil: 'load', timeout: 60000});
          await trang.locator('#vgb .vh b').filter({hasText: nhan}).waitFor({timeout: 60000});
          // Chỉ nhận màn có control cuối cùng, không coi chữ "Đang tải" là sẵn sàng.
          await trang.locator(sanSang).waitFor({state: 'visible', timeout: 60000});
          const than = await trang.locator('#vgb').innerText();
          if (/Loi khoi dong|Traceback|Không tải được/.test(than)) throw new Error('Màn hiện lỗi tải.');
          if (loi.length || api.some(r => r.status >= 400)) throw new Error('Có lỗi JS/API.');
          dat = true;
        } catch (e) {loi.push(e.message);}
        ket.push({duong, rong, dat, ms: Date.now() - batDau, api, loi});
        await trang.screenshot({path: path.join(dich, duong + '-' + rong + '.png'), fullPage: true});
        await trang.close();
      }
      await canh.tracing.stop({path: path.join(dich, 'man-' + rong + '.zip')});
      await canh.close();
    }
  } finally {
    await trinh.close();
    fs.writeFileSync(path.join(dich, 'mo-man.json'), JSON.stringify(ket, null, 2));
  }
  console.log(JSON.stringify({tong: ket.length, dat: ket.filter(x => x.dat).length, ket}, null, 2));
  if (ket.length !== 10 || ket.some(x => !x.dat)) process.exitCode = 1;
})().catch(e => {console.error(e); process.exitCode = 1;});

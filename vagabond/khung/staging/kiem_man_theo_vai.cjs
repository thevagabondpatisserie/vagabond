// #257: mở màn theo ba vai nghiệp vụ, tránh chỉ kiểm bằng Administrator.
// Đây là kiểm mở màn, chưa thay các ca E2E ghi sổ và kiểm GL/SLE.
const fs = require('fs');
const path = require('path');
const {chromium} = require('playwright');

(async () => {
  if (process.env.GITHUB_ACTIONS !== 'true') throw new Error('Chỉ chạy trên CI riêng.');
  const goc = 'http://127.0.0.1:8000';
  const dich = process.env.VGB_ARTIFACTS;
  if (!dich) throw new Error('Thiếu thư mục bằng chứng.');
  const profiles = JSON.parse(fs.readFileSync(path.join(dich, 'vai-fixture.json')));
  const trinh = await chromium.launch({headless: true});
  const ket = [];
  try {
    for (const rong of [390, 1280]) {
      for (const [vai, duong, nhan, sanSang] of [
        ['sales', 'van-don', 'Vận đơn', '#vdDate'],
        ['bep', 'san-xuat', 'Lệnh sản xuất', '#mNoBom'],
        ['ke_toan', 'ho-so-thanh-toan', 'Hồ sơ', '#hsTimO']
      ]) {
      const canh = await trinh.newContext({viewport: {width: rong, height: 900}, serviceWorkers: 'block'});
      // Không gửi telemetry, ảnh ngoài hay API của nhà cung cấp thật.
      await canh.route('**/*', r => new URL(r.request().url()).origin === goc ? r.continue() : r.abort());
      const dangNhap = await canh.request.post(goc + '/api/method/login', {form: {usr: profiles[vai].user, pwd: 'bench-only-roles-257'}});
      if (!dangNhap.ok()) throw new Error('Không đăng nhập được site CI: ' + dangNhap.status());
      await canh.tracing.start({screenshots: true, snapshots: true});
        const trang = await canh.newPage();
        const loi = [], api = [], taiHong = [], phepDo = [];
        trang.on('pageerror', e => loi.push(e.message));
        trang.on('requestfailed', r => {
          const u = new URL(r.url());
          const chiTiet = r.failure()?.errorText || 'requestfailed';
          taiHong.push({duong: u.pathname, loi: chiTiet});
          // API cùng site mất phản hồi cũng là lỗi, kể cả không có HTTP status.
          // Ảnh ngoài bị chặn bởi fixture chỉ giữ làm chẩn đoán.
          if (u.origin === goc && u.pathname.startsWith('/api/')) loi.push(u.pathname + ': ' + chiTiet);
        });
        trang.on('response', r => {if (r.url().includes('/api/')) api.push({duong: new URL(r.url()).pathname, status: r.status()});});
        // Chỉ đo metadata mạng, không lưu request/response body hoặc cookie.
        // requestfinished đến sau khi đọc đủ body, khác thời gian chỉ nhận headers.
        trang.on('requestfinished', r => {
          if (!r.url().includes('/api/')) return;
          phepDo.push((async () => {
            const moc = r.timing();
            const co = await r.sizes();
            return {duong: new URL(r.url()).pathname,
              ms: moc.responseEnd,
              ttfb_ms: moc.responseStart >= 0 && moc.requestStart >= 0
                ? moc.responseStart - moc.requestStart : null,
              response_body_bytes: co.responseBodySize,
              response_headers_bytes: co.responseHeadersSize};
          })().then(value => ({status: 'fulfilled', value}),
            reason => ({status: 'rejected', reason: String(reason)})));
        });
        const batDau = Date.now();
        let dat = false;
        try {
          const html = await trang.goto(goc + '/' + duong, {waitUntil: 'load', timeout: 60000});
          if (!html || !html.ok()) throw new Error('Trang trả HTTP ' + (html ? html.status() : 'không có phản hồi'));
          await trang.locator('#vgb .vh b').filter({hasText: nhan}).waitFor({timeout: 60000});
          // Chỉ nhận màn có control cuối cùng, không coi chữ "Đang tải" là sẵn sàng.
          await trang.locator(sanSang).waitFor({state: 'visible', timeout: 60000});
          const than = await trang.locator('#vgb').innerText();
          if (/Loi khoi dong|Traceback|Không tải được/.test(than)) throw new Error('Màn hiện lỗi tải.');
          if (loi.length || api.some(r => r.status >= 400)) throw new Error('Có lỗi JS/API.');
          dat = true;
        } catch (e) {loi.push(e.message);}
        const ms = Date.now() - batDau;
        const doMang = await Promise.all(phepDo);
        const kq = {vai, duong, rong, dat, ms, api, loi, taiHong,
          mang: doMang.filter(x => x.status === 'fulfilled').map(x => x.value),
          loiDoMang: doMang.filter(x => x.status === 'rejected').map(x => String(x.reason))};
        ket.push(kq);
        // Xuất từng ca để log chỉ rõ màn nào hỏng, không đợi cả sáu ca.
        console.log(JSON.stringify(kq));
        if (!dat) fs.writeFileSync(path.join(dich, 'vai-' + vai + '-' + duong + '-' + rong + '-loi.html'), await trang.content());
        await trang.screenshot({path: path.join(dich, 'vai-' + vai + '-' + duong + '-' + rong + '.png'), fullPage: true});
        await trang.close();
      await canh.tracing.stop({path: path.join(dich, 'vai-' + vai + '-' + rong + '.zip')});
      await canh.close();
      }
    }
  } finally {
    await trinh.close();
    fs.writeFileSync(path.join(dich, 'mo-man-theo-vai.json'), JSON.stringify(ket, null, 2));
  }
  console.log(JSON.stringify({tong: ket.length, dat: ket.filter(x => x.dat).length, ket}, null, 2));
  if (ket.length !== 6 || ket.some(x => !x.dat)) process.exitCode = 1;
})().catch(e => {console.error(e); process.exitCode = 1;});

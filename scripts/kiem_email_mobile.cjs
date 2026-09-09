// #249: kiểm kích thước thực để khung cố định/chuỗi dài không lọt qua ca chuỗi.
// PLAYWRIGHT_MODULE trỏ tới gói playwright đã cài, CHROME_BIN tuỳ chọn.
// node scripts/kiem_email_mobile.cjs /tmp/mau-email
const fs = require('fs');
const path = require('path');
const {pathToFileURL} = require('url');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
(async () => {
  const dich = path.resolve(process.argv[2]);
  const trinhDuyet = await chromium.launch({headless: true, ...(process.env.CHROME_BIN ? {executablePath: process.env.CHROME_BIN} : {})});
  const ketQua = [];
  try {
    for (const rong of [320, 375, 390, 600, 1024]) {
      const trang = await trinhDuyet.newPage({viewport: {width: rong, height: 900}});
      for (const tep of fs.readdirSync(dich).filter(t => t.endsWith('.html'))) {
        await trang.goto(pathToFileURL(path.join(dich, tep)).href);
        await trang.evaluate(() => document.fonts.ready);
        const tran = await trang.evaluate(() => {
          const rong = document.documentElement.clientWidth;
          return [...document.querySelectorAll('body *')].filter(e => {
            const o = e.getBoundingClientRect();
            return o.width && (o.right > rong + 1 || o.left < -1 || e.scrollWidth > e.clientWidth + 1);
          }).map(e => ({the: e.tagName, rong: e.clientWidth, noiDung: e.scrollWidth}));
        });
        ketQua.push({tep, rong, dat: tran.length === 0, tran});
        if (['bao_ncc.html', 'chu_dai.html'].includes(tep) && [320, 1024].includes(rong)) {
          await trang.screenshot({path: path.join(dich, tep.replace('.html', '-' + rong + '.png')), fullPage: true});
        }
      }
      await trang.close();
    }
  } finally { await trinhDuyet.close(); }
  fs.writeFileSync(path.join(dich, 'ket-qua.json'), JSON.stringify(ketQua, null, 2));
  const hong = ketQua.filter(k => !k.dat);
  console.log(JSON.stringify({tong: ketQua.length, dat: ketQua.length - hong.length, hong}, null, 2));
  process.exitCode = hong.length ? 1 : 0;
})().catch(e => {console.error(e); process.exitCode = 1;});

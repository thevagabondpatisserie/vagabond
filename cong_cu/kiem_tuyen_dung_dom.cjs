/* v625: thao tác DOM THẬT trên Chromium cho mục Tuyển dụng (phương án A) và
   form /ung-tuyen 3 bước, dữ liệu fixture tại localhost (cong_cu/xem_thu_web_vue.py,
   vị trí mẫu cong_cu/tuyen_dung_mau.json). Không gửi gì ra Internet.

   Chạy: NODE_PATH=<thư mục node_modules có playwright> node cong_cu/kiem_tuyen_dung_dom.cjs */
const {chromium} = require('playwright');
const {spawn} = require('node:child_process');
const assert = require('node:assert/strict');
const root = require('node:path').resolve(__dirname, '..');
const url = 'http://127.0.0.1:8798';
const server = spawn(process.env.PYTHON || 'python3', ['cong_cu/xem_thu_web_vue.py', '8798'], {cwd: root, stdio: 'ignore'});
const sleep = ms => new Promise(r => setTimeout(r, ms));
let browser, passed = 0;

async function cho() {
  for (let i = 0; i < 80; i++) {
    try { const r = await fetch(url + '/ung-tuyen'); if (r.ok) return; } catch (e) { /* chưa mở */ }
    await sleep(100);
  }
  throw new Error('Máy chủ fixture không mở được');
}
async function trang(duong) {
  const ctx = await browser.newContext({viewport: {width: 390, height: 844}});
  const p = await ctx.newPage();
  p.loi = [];
  p.on('pageerror', e => p.loi.push(e.message));
  p.on('console', m => { if (m.type() === 'error' && !/Failed to load resource/.test(m.text())) p.loi.push(m.text()); });
  await p.goto(url + duong);
  return p;
}
async function khongTran(p, ten) {
  const r = await p.evaluate(() => [document.documentElement.scrollWidth, window.innerWidth]);
  assert.ok(r[0] <= r[1], ten + ': cuộn ngang ' + r);
}

(async () => {
  try {
    await cho();
    browser = await chromium.launch();

    // T1: danh sách -> chi tiết -> quay lại, bằng bấm thật.
    let p = await trang('/web_moi/banh#/tuyen-dung');
    await p.waitForSelector('.td-the');
    assert.equal(await p.locator('.td-the').count(), 2);
    assert.equal(await p.locator('.td-the').first().locator('.td-luong').innerText(), 'Từ 7,5 triệu/tháng');
    await khongTran(p, 'danh sách');
    await p.locator('.td-the').first().click();
    await p.waitForSelector('.td-chi-tiet');
    assert.equal(await p.evaluate(() => location.hash), '#/tuyen-dung/VTT-0002');
    assert.match(await p.locator('.td-chi-tiet h1').innerText(), /Sales Online/);
    assert.equal(await p.locator('.td-o').count(), 4);
    assert.equal(await p.getAttribute('.td-ung', 'href'), '/ung-tuyen?vt=VTT-0002');
    await khongTran(p, 'chi tiết');
    await p.locator('.td-lui').click();
    await p.waitForSelector('.td-the');
    assert.equal(await p.evaluate(() => location.hash), '#/tuyen-dung');
    // Nút lùi của trình duyệt về lại chi tiết rồi danh sách.
    await p.goBack(); await p.waitForSelector('.td-chi-tiet');
    await p.goBack(); await p.waitForSelector('.td-the');
    // Mở thẳng link chi tiết (khách bấm link chia sẻ).
    await p.goto(url + '/web_moi/banh#/tuyen-dung/VTT-0001');
    await p.waitForSelector('.td-chi-tiet');
    assert.match(await p.locator('.td-chi-tiet h1').innerText(), /Pastry/);
    assert.deepEqual(p.loi, []);
    passed++;

    // T2: form 3 bước bằng bấm và gõ thật, gửi tới máy chủ fixture.
    p = await trang('/ung-tuyen?vt=VTT-0002');
    await p.waitForSelector('#ung-tuyen:not([hidden]) .ut-cau');
    await khongTran(p, 'form bước 1');
    await p.locator('[data-ma="ho_ten"] input').fill('Trần Thị Bình');
    await p.locator('[data-ma="gioi_tinh"] button', {hasText: 'Nữ (Female)'}).click();
    const ngay = p.locator('[data-ma="sinh_nhat"] input');
    await ngay.nth(0).fill('17'); await ngay.nth(1).fill('5'); await ngay.nth(2).fill('2001');
    await p.locator('[data-ma="sdt"] input').fill('0909123456');
    await p.locator('[data-ma="email"] input').fill('binh@gmail.com');
    await p.locator('#gui').click();
    await p.waitForSelector('[data-ma="hoc_van"]');
    await p.locator('[data-ma="hoc_van"] button', {hasText: 'Tốt nghiệp THPT'}).click();
    await p.locator('[data-ma="cv"] input[type=file]').setInputFiles({name: 'cv.pdf', mimeType: 'application/pdf', buffer: Buffer.from('%PDF-1.4 mau')});
    await p.waitForSelector('.ut-tep-dong em');
    await p.locator('#gui').click();
    await p.waitForSelector('[data-ma="luong"]');
    await p.locator('[data-ma="luong"] input').pressSequentially('9000000');
    assert.equal(await p.locator('[data-ma="luong"] input').inputValue(), '9.000.000');
    await p.locator('[data-ma="biet_tin"] button', {hasText: 'Mạng xã hội'}).click();
    // Nút gửi cố định ở đáy không che câu đồng ý khi cuộn tới cuối.
    await p.locator('#dong-y').check();
    await khongTran(p, 'form bước 3');
    const gui = p.waitForRequest(r => r.url().endsWith('vagabond.tuyen_dung.ung_tuyen'));
    await p.locator('#gui').click();
    const than = JSON.parse((await gui).postData());
    assert.equal(than.du_lieu.ma_cv, 'cv-thu-1');
    assert.equal(than.du_lieu.tra_loi.luong, '9000000');
    assert.equal(than.du_lieu.tra_loi.sinh_nhat, '2001-05-17');
    await p.waitForSelector('#xong:not([hidden])');
    assert.match(await p.locator('#xong-chu').innerText(), /UV-THU-0001/);
    assert.deepEqual(p.loi, []);
    passed++;

    console.log(`kiem_tuyen_dung_dom: ${passed} kịch bản đạt`);
  } catch (e) {
    console.error(e);
    process.exitCode = 1;
  } finally {
    if (browser) await browser.close();
    server.kill();
  }
})();

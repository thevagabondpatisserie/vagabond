/* #471: thao tác DOM thật, HTTP fixture tại localhost; không gọi hàm kho phụ.
   NODE_PATH trỏ tới Playwright đã cài. Không gửi dữ liệu ra Internet. */
const {chromium} = require('playwright');
const {spawn} = require('node:child_process');
const assert = require('node:assert/strict');
const root = require('node:path').resolve(__dirname, '..');
const url = 'http://127.0.0.1:8797';
const server = spawn(process.env.PYTHON || 'python3', ['cong_cu/xem_thu_web_vue.py', '8797'], {cwd:root, stdio:'ignore'});
const sleep = ms => new Promise(r=>setTimeout(r,ms));
let browser, passed=0;
async function test(name, fn) { await fn(); console.log('PASS '+name); passed++; }
(async()=>{try {
 for(let i=0;i<60;i++){try{await fetch(url+'/banh');break;}catch(e){await sleep(100);}}
 browser=await chromium.launch({headless:true, ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH} : {})});
  await test('F21 trang cũ: hết lúc gửi giữ giỏ, nonce và nạp lại tồn',async()=>{
    for(const route of ['/banh']) {
      const c=await browser.newContext({viewport:{width:390,height:844},timezoneId:'Asia/Ho_Chi_Minh'});
      await c.route('**/*',r=>r.request().url().startsWith(url)?r.continue():r.abort());
      const p=await c.newPage();let nap=0;const gui=[];
      await p.route('**/api/method/vagabond.kiem_banh.co_the_ban_hom_nay*',async r=>{nap++;return r.continue();});
      await p.route('**/api/method/vagabond.don_hang.tao_don',r=>{
        gui.push(JSON.parse(r.request().postDataJSON().don));
        return r.fulfill({json:{message:{ok:0,ly_do:'het_hang',nhac:['CANDLE ngày 13/10/2026 chỉ còn 0 cái.']}}});
      });
      await p.goto(url+route+'#/banh/candle');await p.locator('#s-cta').waitFor({state:'visible'});
      await p.locator('#s-wish').fill('Giữ lời chúc');await p.locator('#s-cta').click();await p.locator('#bar .go').click();
      await p.locator('#f-name').fill('Khách thử');await p.locator('#f-phone').fill('0900000000');
      await p.locator('#m-pick').click();await p.locator('#pickList button').first().click();
      await p.locator('#c-days button').nth(2).click();await p.locator('#c-slots button:not([disabled])').first().click();
      await p.locator('#c-dongy').click();
      const truoc=await p.locator('#cartList').innerText(),cu=nap;
      await p.locator('#btnSend').click();await p.waitForFunction(()=>document.querySelector('#sendHint').innerText.includes('chỉ còn 0'));
      assert.equal(await p.locator('#cartList').innerText(),truoc);
      assert.match(await p.locator('#sendHint').innerText(),/giảm số lượng, đổi ngày nhận hoặc nhắn Sales/);
      await p.waitForTimeout(250);assert(nap>cu);
      await p.locator('#btnSend').click();await p.waitForTimeout(250);
      assert.equal(gui.length,2);assert.equal(gui[0].nonce,gui[1].nonce);
      assert.equal(await p.locator('#cartList').innerText(),truoc);
      if (process.env.VGB_F21_ANH) {
        const fs=require('node:fs'),path=require('node:path');
        fs.mkdirSync(process.env.VGB_F21_ANH,{recursive:true});
        for (const width of [390,1440]) {
          await p.setViewportSize({width,height:width===390?844:1000});
          await p.locator('#sendHint').scrollIntoViewIfNeeded();
          await p.screenshot({path:path.join(process.env.VGB_F21_ANH,`f21-cu-${width}.jpg`),type:'jpeg',quality:85});
        }
      }
      await c.close();
    }
  });
 console.log(`${passed} ca DOM trang cũ đạt`);
} finally {if(browser)await browser.close();server.kill();}})().catch(e=>{console.error(e);process.exitCode=1;});

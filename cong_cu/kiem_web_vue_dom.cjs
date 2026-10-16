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
// Đối chứng bằng hai hàm tiền/phí thật của Python, bảng giá fixture độc lập.
// Hàm này chỉ đọc kết quả, không cập nhật hay trợ giúp trạng thái Vue.
function tongMayChu(tuLay,nguong,baoPhi) {
  const code=`import ast,json,sys
from pathlib import Path
cay=ast.parse(Path('vagabond/don_web.py').read_text())
names=('tinh_tien_banh','quyet_phi_giao')
g={}
exec(compile(ast.Module(body=[n for n in cay.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'don_web.py','exec'),g)
x=json.loads(sys.argv[1])
hang=[{'variation_id':'BAWC00139','quantity':1},{'variation_id':'BAPK00005','quantity':1},{'variation_id':'BAPK00002','quantity':1}]
tien,thieu=g['tinh_tien_banh'](hang,{'BAWC00139':650000,'BAPK00005':17000,'BAPK00002':17000})
phi=g['quyet_phi_giao'](tien,x['nguong'],x['tuLay'],x['baoPhi'])
print(json.dumps({'tong':tien+(phi['phi_khach'] or 0),'phi':phi}))`;
  const r=require('node:child_process').spawnSync(process.env.PYTHON||'python3',['-c',code,JSON.stringify({tuLay,nguong,baoPhi})],{cwd:root,encoding:'utf8'});
  assert.equal(r.status,0,r.stderr);return JSON.parse(r.stdout);
}
async function soTong(page,tuLay,nguong,baoPhi){
  const actual=Number((await page.locator('#sum .tot b').innerText()).replace(/\D/g,''));
  assert.equal(actual,tongMayChu(tuLay,nguong,baoPhi).tong);
}
/* VGB_CA=F36 chỉ chạy ca có tên bắt đầu như vậy (dùng khi chạy đột biến); mặc định chạy hết. */
async function test(name, fn) { if (process.env.VGB_CA && !name.startsWith(process.env.VGB_CA)) return; await fn(); console.log('PASS '+name); passed++; }
(async()=>{try {
  for(let i=0;i<60;i++){try{await fetch(url+'/banh');break;}catch(e){await sleep(100);}}
  browser=await chromium.launch({headless:true, ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH} : {})});
  const context=await browser.newContext({viewport:{width:390,height:844},timezoneId:'Asia/Ho_Chi_Minh'});
  await context.route('**/*',r=>r.request().url().startsWith(url)?r.continue():r.abort());
  const page=await context.newPage();
  let nguong=0;
  await page.route('**/api/method/vagabond.don_web.cau_hinh_web*',async r=>{
    const data=await (await r.fetch()).json(); data.message.pixel_id='123'; data.message.mien_phi_tu=nguong;
    return r.fulfill({json:data});
  });
  const errors=[]; page.on('pageerror',e=>errors.push(e.message));
  await test('F02/F03 đổi D1/NVHTN: đúng món, số lượng, không trộn quầy', async()=>{
    await page.route('**/api/method/vagabond.kiem_kho.con_tren_quay_web*',r=>r.fulfill({json:{message:{quay:[
      {ma:'TCV',ten:'D1 fixture',mon:[{ma:'D1',ten:'Bánh D1 riêng',nhom:'Nhẹ',gia:10000,con:12}]},
      {ma:'NVHTN',ten:'NVHTN fixture',mon:[{ma:'NV',ten:'Bánh NV riêng',nhom:'Mặn',gia:20000,con:3}]}]}}}));
    await page.goto(url+'/web_moi/banh');
    await page.locator('#tabStore').click();
    await page.locator('.quay-chon button').filter({hasText:'D1 fixture'}).click();
    assert.match(await page.locator('#storeBody').innerText(),/Bánh D1 riêng/i);
    assert.equal(await page.locator('#storeBody .card').count(),1);
    assert.match(await page.locator('.q-con').innerText(),/12/);
    await page.locator('.quay-chon button').filter({hasText:'NVHTN fixture'}).click();
    assert.match(await page.locator('#storeBody').innerText(),/Bánh NV riêng/i);
    assert.doesNotMatch(await page.locator('#storeBody').innerText(),/Bánh D1 riêng/i);
    assert.match(await page.locator('.q-con').innerText(),/3/);
    await page.locator('.quay-chon button').filter({hasText:'D1 fixture'}).click();
    assert.doesNotMatch(await page.locator('#storeBody').innerText(),/Bánh NV riêng/i);
  });
  await test('F06/F09 thêm bánh qua DOM, tăng giảm giỏ và tổng cập nhật',async()=>{
    await page.goto(url+'/web_moi/banh#/banh/candle');
    await page.locator('#sheet.open').waitFor({state:'visible'});
    await page.locator('#s-wish').fill('Chúc vui');
    await page.locator('#s-sizes button').last().click();
    await page.locator('#s-sizes button').first().click();
    await page.locator('#s-phu-kien > summary').click();
    await page.locator('#s-nia').fill('2'); await page.locator('#s-dia').fill('3');
    await page.getByRole('button',{name:'Nến số 2',exact:true}).click();
    /* v598: hộp, túi, nến xoắn chuyển vào dòng gấp dự phòng, món mua thêm đầu tiên là Thiệp BAPK00002. */
    await page.locator('#s-addons button').first().click();
    await page.locator('#s-cta').click();
    await page.locator('#bar .go').click();
    await page.locator('#checkout.open').waitFor();
    assert.match(await page.locator('#cartList').innerText(),/Chúc vui/);
    const before=await page.locator('#sum').innerText();
    await page.getByRole('button',{name:'Tăng số lượng',exact:true}).click();
    assert.notEqual(await page.locator('#sum').innerText(),before);
    await page.getByRole('button',{name:'Giảm số lượng',exact:true}).click();
    assert.equal(await page.locator('#sum').innerText(),before);
    const ev=await page.evaluate(()=>Array.from(window.fbq?.queue||[],a=>Array.from(a)[1]));
    for(const e of ['PageView','ViewContent','AddToCart','InitiateCheckout']) assert(ev.includes(e),e);
  });
  await test('F08/F10/F18/F33 nhập người nhận, hóa đơn, thanh toán rồi reload giữ đủ',async()=>{
    await page.locator('#f-phone').fill('0900000000'); await page.locator('#f-name').fill('Khách thử');
    await page.locator('#c-other').click(); await page.locator('#f-rname').fill('Người nhận');
    await page.locator('#f-rphone').fill('0911111111'); await page.locator('#c-gift').click();
    await page.locator('#c-vat').click();
    for(const code of ['0312345678','123456789012','0312345678001']) {
      await page.locator('#f-mst').fill(code);
      await page.waitForResponse(r=>r.url().includes('tra_mst')&&r.url().includes(code));
    }
    await page.waitForFunction(()=>document.querySelector('#f-cname').value !== '');
    await page.locator('#f-cname').fill('Công ty thử'); await page.locator('#f-caddr').fill('Địa chỉ thử');
    await page.locator('#payList button').last().click();
    const pay=await page.locator('#payList .on').innerText();
    await page.waitForTimeout(450); await page.reload();
    await page.locator('#f-name').waitFor({state:'visible'});
    assert.equal(await page.locator('#f-name').inputValue(),'Khách thử');
    assert.equal(await page.locator('#f-rname').inputValue(),'Người nhận');
    assert.equal(await page.locator('#f-cname').inputValue(),'Công ty thử');
    assert.equal(await page.locator('#payList .on').innerText(),pay);
  });
  await test('F13/F14 giao đúng phí, tự lấy phí0, địa chỉ sửa bỏ tọa độ cũ',async()=>{
    await page.locator('#f-addr').fill('12 Nguyễn Huệ');
    await page.locator('#addrGoiY button').first().click();
    await page.waitForFunction(()=>document.querySelector('#sum').innerText.includes('42.000'));
    await soTong(page,false,0,{ok:1,total_fee:42000});
    await page.locator('#m-pick').click(); await page.locator('#pickList button').first().click();
    await soTong(page,true,0,null);
    assert.doesNotMatch(await page.locator('#sum').innerText(),/42.000/);
    await page.locator('#m-ship').click();
    await page.locator('#f-addr').fill('Địa chỉ mới');
    await page.locator('#addrGoiY button').first().waitFor();
    assert.equal(await page.locator('#f-addr').inputValue(),'Địa chỉ mới');
    await page.route('**/api/method/vagabond.giao_hang.phi_giao*',r=>r.fulfill({json:{message:{ok:false}}}));
    await page.locator('#addrGoiY button').first().click();
    await page.waitForFunction(()=>document.querySelector('#shipHint').innerText.includes('Chưa lấy được'));
    assert.match(await page.locator('#sum').innerText(),/Tạm tính/i);
    await soTong(page,false,0,{ok:0});
    await page.unroute('**/api/method/vagabond.giao_hang.phi_giao*');
    await page.locator('#shipHint button').click();
    await page.waitForFunction(()=>document.querySelector('#sum').innerText.includes('42.000'));
    await page.route('**/api/method/vagabond.giao_hang.phi_giao*',r=>r.fulfill({json:{message:{ok:false,ly_do:'ngoai_vung_giao',ban_kinh:12}}}));
    await page.locator('#f-addr').fill('Địa chỉ ngoài vùng'); await page.locator('#addrGoiY button').first().click();
    await page.waitForFunction(()=>document.querySelector('#shipHint').innerText.includes('chưa hỗ trợ'));
    await page.unroute('**/api/method/vagabond.giao_hang.phi_giao*');
    nguong=1; await page.reload(); await page.locator('#f-addr').fill('12 Nguyễn Huệ');
    await page.locator('#addrGoiY button').first().click();
    await page.waitForFunction(()=>document.querySelector('#sum').innerText.includes('Miễn phí'));
    await soTong(page,false,1,{ok:1,total_fee:42000});
    nguong=0; await page.reload(); await page.locator('#f-name').waitFor({state:'visible'});
  });
  await test('F19/F20 DOM mạng lỗi giữ giỏ, thử lại cùng nonce và chuyển biên nhận',async()=>{
    await page.locator('#m-pick').click(); await page.locator('#pickList button').first().click();
    await page.locator('#c-days button').nth(2).click();
    await page.locator('#c-slots button:not([disabled])').first().click();
    await page.locator('#c-dongy').click();
    await page.locator('#f-ma').fill('GIAM10'); await page.locator('#btnMa').click();
    await page.waitForFunction(()=>document.querySelector('#sum').innerText.includes('100.000'));
    const calls=[];
    await page.route('**/api/method/vagabond.don_hang.tao_don',async r=>{
      calls.push(JSON.parse(r.request().postDataJSON().don));
      if(calls.length===1) {await sleep(100);return r.abort('connectionreset');}
      if(calls.length===2) return r.fulfill({json:{message:{ok:0,ly_do:'uu_dai_doi',uu:{giam:0,ap:[]}}}});
      return r.fulfill({json:{message:{ok:1,duong_dan:'/banh/xong/token-cu'}}});
    });
    await page.route('**/web_moi/banh/xong/token-cu',r=>r.fulfill({contentType:'text/html',body:'<p>Biên nhận cũ</p>'}));
    await Promise.all([page.locator('#btnSend').dispatchEvent('click'),page.locator('#btnSend').dispatchEvent('click')]);
    await page.waitForFunction(()=>document.querySelector('#sendHint').innerText.includes('Chưa gửi'));
    assert.equal(calls.length,1);
    assert(await page.locator('#cartList li').count()>0);
    await page.locator('#btnSend').click();
    await page.waitForFunction(()=>document.querySelector('#sendHint').innerText.includes('Tổng tiền vừa cập nhật'));
    await sleep(150); assert.equal(calls.length,2);
    assert.doesNotMatch(await page.locator('#sum').innerText(),/100.000/);
    await page.locator('#btnSend').click(); await page.waitForURL('**/web_moi/banh/xong/token-cu');
    assert.equal(calls.length,3); assert.equal(calls[2].nonce,calls[0].nonce);
    assert.equal(calls[2].giam_da_xem,0); assert.equal(calls[0].nonce,calls[1].nonce);
    assert(calls[0].nonce); assert.equal(calls[0].tu_lay,true);
    assert.equal(calls[0].hoa_don.tax_code,'0312345678001');
    assert.equal(calls[0].nguoi_nhan.ho_ten,'Người nhận');
    assert.match(calls[0].note,/2.*nĩa|nĩa.*2/i);
  });
  await test('F22/F23 biên nhận DOM, gỡ token, reload cùng biên nhận, Pixel một GuiDon',async()=>{
    const fs=require('node:fs');
    const bn={ma:'DW-FIXTURE',ten:'K. T.',mon:[{ten:'CANDLE',sl:1,thanh_tien:'650.000 đ'}],
      tien_banh:'650.000 đ',giam:'- 50.000 đ',phi_giao:'42.000 đ',tong:'642.000 đ',trang_thai:'Đã nhận'};
    const doc={loai:'bien_nhan',bien_nhan:bn,pixel_id:'123',su_kien:{ban:true,event_id:'ev-capi-fixture',gia_tri:650000,ma_mon:['BAWC00139']}};
    await page.addInitScript(()=>{window.suKienThu=[];window.fbq=(...args)=>window.suKienThu.push({args,path:location.pathname});});
    /* v598: dùng hàm so đường dẫn, không dùng glob '**' dính chữ: Playwright 1.55 (CI) không khớp
       '/xong**' với '/xong/TOKEN' còn 1.56 thì khớp, ca xanh trên máy mà đỏ trên CI. */
    await page.route(u=>new URL(String(u)).pathname.startsWith('/web_moi/banh/xong'),r=>{
      const d=r.request().url().endsWith('/TOKEN')?doc:{loai:'bien_nhan',khong_token:1};
      const html=fs.readFileSync(root+'/vagabond/www/web_moi/xong.html','utf8')
        .replace('{{ du_lieu }}',JSON.stringify(d)).replace('{{ csrf_token }}','fixture').replace('{{ chan_trang }}','');
      return r.fulfill({contentType:'text/html',body:html});
    });
    await page.goto(url+'/web_moi/banh/xong/TOKEN'); await page.locator('.bn-in').waitFor();
    assert.equal(new URL(page.url()).pathname,'/web_moi/banh/xong');
    assert.match(await page.locator('.bn-tien .tong').innerText(),/642.000/);
    const events=await page.evaluate(()=>window.suKienThu);
    assert.equal(events.filter(x=>x.args[1]==='GuiDon').length,1);
    assert.equal(events.find(x=>x.args[1]==='GuiDon').args[3].eventID,'ev-capi-fixture');
    assert(events.every(x=>!x.path.includes('TOKEN')));
    await page.reload(); await page.locator('.bn-in').waitFor();
    assert.match(await page.locator('h1').innerText(),/DW-FIXTURE/);
    assert.equal((await page.evaluate(()=>window.suKienThu)).length,0);
  });
  await test('F27 chính sách DOM giữ chữ như text, không thực thi ngoặc Vue',async()=>{
    const fs=require('node:fs');
    for(const route of ['chinh-sach-bao-mat','dieu-khoan','giao-hang-doi-tra']) {
      await page.route('**/web_moi/'+route,r=>r.fulfill({contentType:'text/html',body:
        fs.readFileSync(root+'/vagabond/www/web_moi/chinh-sach.html','utf8')
          .replace('{{ du_lieu }}',JSON.stringify({loai:'chinh_sach',ten:route,cay:[{tag:'p',con:['{{alert(1)}} chữ đã xuất bản']}]}))
          .replace('{{ csrf_token }}','fixture').replace('{{ chan_trang }}','').replace('{{ doi_ngon_ngu }}','')}));
      await page.goto(url+'/web_moi/'+route); await page.locator('.cs-in p').last().waitFor();
      assert.match(await page.locator('.cs-in').innerText(),/\{\{alert\(1\)\}\}/);
      assert.equal(await page.locator('meta[name=robots]').getAttribute('content'),'noindex,nofollow');
    }
  });
  await test('F05 hàng mùa vụ hết hàng và còn hàng; F01 tải tồn lỗi có đường thử lại',async()=>{
    await page.goto(url+'/web_moi/banh'); await page.locator('#tabMua').click();
    assert.match(await page.locator('#muaLuoi').innerText(),/Hộp Trăng Rằm/i);
    assert.match(await page.locator('#muaLuoi').innerText(),/Hộp Sương Thu/i);
    await page.goto(url+'/web_moi/banh#/in-season/TTHOP02');
    await page.locator('#sheetMua.open').waitFor(); assert(await page.locator('#sm-cta').isDisabled());
    await page.goto(url+'/web_moi/banh#/in-season/TTHOP01');
    await page.locator('#sm-cta').click(); await page.locator('#sheetMua .close').click(); await page.locator('#bar .go').click();
    assert.match(await page.locator('#cartList').innerText(),/Hộp Trăng Rằm/i);
    await page.route('**/api/method/vagabond.kiem_banh.co_the_ban_hom_nay*',r=>r.fulfill({status:500,json:{}}));
    await page.goto(url+'/web_moi/banh');
    await page.locator('#tonLoi').waitFor({state:'visible'});
    assert.match(await page.locator('#tonLoi').innerText(),/Chưa cập nhật/);
    await page.unroute('**/api/method/vagabond.kiem_banh.co_the_ban_hom_nay*');
    await page.locator('#tonLoi button').click();
    await page.locator('#tonLoi').waitFor({state:'hidden'});
    assert(await page.locator('#grid-today .card').count()>0);
  });
  await test('F11 bản cũ sang Vue rồi quay lại giữ giỏ và thông tin cùng phiên',async()=>{
    const c=await browser.newContext({viewport:{width:390,height:844},timezoneId:'Asia/Ho_Chi_Minh'});
    await c.route('**/*',r=>r.request().url().startsWith(url)?r.continue():r.abort());
    const p=await c.newPage();
    await p.goto(url+'/banh#/banh/candle'); await p.locator('#s-cta').waitFor({state:'visible'});
    await p.locator('#s-wish').fill('Nháp cũ'); await p.locator('#s-cta').click(); await p.locator('#bar .go').click();
    await p.locator('#f-name').fill('Tên từ bản cũ'); await p.locator('#f-phone').fill('0900000000');
    await p.goto(url+'/web_moi/banh#/gio-hang'); await p.locator('#f-name').waitFor({state:'visible'});
    assert.equal(await p.locator('#f-name').inputValue(),'Tên từ bản cũ');
    assert.match(await p.locator('#cartList').innerText(),/Nháp cũ/);
    await p.locator('#f-name').fill('Tên từ Vue'); await p.goto(url+'/banh#/gio-hang');
    await p.locator('#f-name').waitFor({state:'visible'}); assert.equal(await p.locator('#f-name').inputValue(),'Tên từ Vue');
    assert.match(await p.locator('#cartList').innerText(),/Nháp cũ/); await c.close();
  });
  await test('F21 cả trang cũ và Vue: hết lúc gửi giữ giỏ, nonce và nạp lại tồn',async()=>{
    for(const route of ['/banh','/web_moi/banh']) {
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
          await p.screenshot({path:path.join(process.env.VGB_F21_ANH,`f21-${route.includes('web_moi')?'vue':'cu'}-${width}.jpg`),type:'jpeg',quality:85});
        }
      }
      await c.close();
    }
  });
  await test('F36 v598 port v597 cả trang cũ và Vue: đồ có sẵn luôn hiện, hộp Cách chọn size, dự phòng gấp, thiệp nhỏ vào giỏ và ghi chú',async()=>{
    /* Chuỗi thao tác của khách, không gọi hàm kho nào ngoài chuỗi (điều 15). */
    for(const route of ['/banh','/web_moi/banh']) {
      const ten=route.includes('web_moi')?'Vue':'cũ';
      const c=await browser.newContext({viewport:{width:390,height:844},timezoneId:'Asia/Ho_Chi_Minh'});
      await c.route('**/*',r=>r.request().url().startsWith(url)?r.continue():r.abort());
      const p=await c.newPage();const gui=[];const loi=[];p.on('pageerror',e=>loi.push(e.message));
      await p.route('**/api/method/vagabond.don_hang.tao_don',r=>{
        gui.push(JSON.parse(r.request().postDataJSON().don));
        return r.fulfill({json:{message:{ok:0,ly_do:'pancake_tu_choi'}}});
      });
      await p.goto(url+route+'#/banh/candle');await p.locator('#s-cta').waitFor({state:'visible'});
      /* Đồ có sẵn hiện ngay, không cần mở mục gấp nào. */
      assert(await p.locator('#s-acc').isVisible(),ten+': khung đồ có sẵn phải hiện');
      const acc=await p.locator('#s-acc').innerText();
      for(const chu of ['Hộp bánh','Túi vải đen','Dao gỗ','Nến xoắn','Cờ cắm']) assert.match(acc,new RegExp(chu),ten+': thiếu '+chu);
      assert.equal(await p.locator('#s-acc .tag-co-san').count(),5,ten);
      /* Hộp Cách chọn size: mở bằng nút, Escape đóng hộp nhưng bảng bánh vẫn mở, con trỏ về nút. */
      await p.locator('#s-huongsize').click();
      await p.locator('#huongSize').waitFor({state:'visible'});
      assert.equal(await p.locator('#hs-luoi .hs-o').count(),4,ten);
      assert.match(await p.locator('#hs-luoi').innerText(),/Ø 20 cm[\s\S]*14 - 16 miếng[\s\S]*10 - 12 người/,ten);
      assert.equal(await p.locator('#hs-luoi .hs-o').last().locator('line').count(),16,ten+': size 4 cắt 16 lát');
      await p.keyboard.press('Escape');
      await p.locator('#huongSize').waitFor({state:'hidden'});
      assert.equal(await p.locator('#sheet.open').count(),1,ten+': Escape không được đóng luôn bảng bánh');
      assert.equal(await p.evaluate(()=>document.activeElement&&document.activeElement.id),'s-huongsize',ten+': con trỏ về nút mở hộp');
      /* Đồ dự phòng nằm trong dòng gấp đang đóng, không lẫn vào đồ trang trí. */
      if(await p.locator('#s-phu-kien > summary').count()) await p.locator('#s-phu-kien > summary').click();
      assert.equal(await p.locator('#s-duphong').evaluate(d=>d.open),false,ten);
      assert.doesNotMatch(await p.locator('#s-addons').innerText(),/Hộp bánh kem|Túi vải/,ten);
      assert.equal(await p.locator('#s-addons-dp li').count(),3,ten);
      await p.locator('#s-nia').fill('1');await p.locator('#s-thiep').fill('2');
      await p.locator('#s-cta').click();await p.locator('#bar .go').click();
      await p.locator('#checkout.open').waitFor();
      const gio=await p.locator('#cartList').innerText();
      assert.match(gio,/1 nĩa gỗ, 0 dĩa bã mía, 2 thiệp nhỏ/,ten+': giỏ phải ghi thiệp nhỏ');
      await p.locator('#f-name').fill('Khách thử');await p.locator('#f-phone').fill('0900000000');
      await p.locator('#m-pick').click();await p.locator('#pickList button').first().click();
      await p.locator('#c-days button').nth(2).click();await p.locator('#c-slots button:not([disabled])').first().click();
      await p.locator('#c-dongy').click();
      await p.locator('#btnSend').click();await p.waitForTimeout(300);
      assert.equal(gui.length,1,ten);
      assert.match(String(gui[0].note||''),/1 nĩa gỗ, 0 dĩa bã mía, 2 thiệp nhỏ/,ten+': ghi chú bếp phải có thiệp nhỏ');
      assert.deepEqual(loi,[],ten);
      await c.close();
    }
  });
  assert.deepEqual(errors,[]);
  console.log(`${passed} ca DOM đạt`);
} finally {if(browser)await browser.close();server.kill();}})().catch(e=>{console.error(e);process.exitCode=1;});

/* Kiểm bố cục #613 bằng CSS và hàm vẽ thật, toàn bộ API giả. Không kết nối ERP.
 * node cong_cu/ui_b/kiem_dong_chon.cjs --ra /tmp/ui613 [--app tệp] [--che-do tat]
 * --dot-bien xuong-hang|be-chu|nut-nho: cố ý làm hỏng bản trong bộ nhớ, phải trả mã 1.
 * Khung 683 tương đương máy quầy phóng 200%; cỡ chữ điện thoại cần máy thật. */
'use strict';
var fs = require('fs');
var path = require('path');
var cp = require('child_process');
var GOC = path.resolve(__dirname, '..', '..');
var CONG = path.join(GOC, 'vagabond', 'public');
var DL = require('./du_lieu_thu.cjs');

function thamSo(ten, macDinh) {
  var i = process.argv.indexOf('--' + ten);
  return i > 0 && process.argv[i + 1] ? process.argv[i + 1] : macDinh;
}
var APP = thamSo('app', '');
var DOT_BIEN = thamSo('dot-bien', '');
var RA = thamSo('ra', '/tmp/ui613');
fs.mkdirSync(RA,{recursive:true});
var BAT = thamSo('che-do', 'bat') === 'bat';
var ORIGIN = 'http://vgb.thu';
var pw;
try { pw = require('playwright'); } catch (e) { console.log('Thiếu Playwright: npm i playwright'); process.exit(2); }

function dauTrang(bat) {
  var ver = fs.readFileSync(APP || path.join(CONG, 'js/app_bep.js'),'utf8').match(/var APPVER = ['"](\d+)['"]/)[1];
  var ma = 'import sys; sys.path.insert(0, %r); from vagabond.giao_dien import dau_trang_html, doc_appver; sys.stdout.write(dau_trang_html(%d, ' + ver + '))';
  var r = cp.spawnSync('python3', ['-B', '-c', ma.replace('%r', JSON.stringify(GOC)).replace('%d', bat ? 1 : 0)], { encoding: 'utf8' });
  if (r.status !== 0) throw new Error('Không lấy được đoạn head: ' + r.stderr);
  return r.stdout;
}
function trangHtml() {
  var user = DL.tra('/api/method/frappe.auth.get_logged_user', {}, 'quan-tri').message;
  return '<!doctype html><html lang="vi"><head><meta charset="utf-8">' +
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">' +
    '<title>Màn hình nghiệp vụ</title>' + dauTrang(BAT) +
    '<script>window.frappe={csrf_token:"thu",session:{user:' + JSON.stringify(user) + '},boot:{}};</script></head>' +
    '<body><div id="vgb"></div><script>window.addEventListener("load",function(){var s=document.createElement("script");' +
    's.src="/assets/vagabond/js/app_bep.js";document.body.appendChild(s);});</script></body></html>';
}
var LOAI = { '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.woff2': 'font/woff2', '.svg': 'image/svg+xml', '.json': 'application/json' };
var ANH = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');

async function moTrang(trinh) {
  var ctx = await trinh.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, locale: 'vi-VN',
    timezoneId: 'Asia/Ho_Chi_Minh', isMobile: true, hasTouch: true, reducedMotion: 'reduce' });
  var trang = await ctx.newPage();
  var loi = [];
  trang.on('pageerror', function (e) { loi.push(String(e.message || e)); });
  await ctx.route('**/*', async function (route) {
    var u = new URL(route.request().url());
    if (u.origin !== ORIGIN) return route.abort();
    var p = decodeURIComponent(u.pathname);
    if (p.indexOf('/api/') === 0) {
      var than = {};
      try { than = JSON.parse(route.request().postData() || '{}'); } catch (e) {
        try { new URLSearchParams(route.request().postData() || '').forEach(function (v, k) { than[k] = v; }); } catch (e2) { }
      }
      u.searchParams.forEach(function (v, k) { if (!(k in than)) than[k] = v; });
      var kq = DL.tra(p, than, 'quan-tri');
      if (kq === undefined) kq = {message: null};
      await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(kq)});
      return;
    }
    if (p.indexOf('/assets/vagabond/') === 0) {
      var tep = path.join(CONG, p.slice('/assets/vagabond/'.length));
      if (APP && p === '/assets/vagabond/js/app_bep.js') tep = APP;
      if (fs.existsSync(tep)) return route.fulfill({ status: 200, contentType: LOAI[path.extname(tep)] || 'application/octet-stream', body: p === '/assets/vagabond/js/app_bep.js' ? themCuaThu(fs.readFileSync(tep,'utf8')) : fs.readFileSync(tep) });
      return route.fulfill({ status: 404, body: '' });
    }
    if (/\.(png|jpe?g|webp|gif|ico)$/i.test(p) || p.indexOf('/files/') === 0) return route.fulfill({ status: 200, contentType: 'image/png', body: ANH });
    if (p === '/sw.js') return route.fulfill({ status: 404, body: '' });
    return route.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: trangHtml() });
  });
  await trang.addInitScript(function () {
    try { Object.defineProperty(navigator, 'serviceWorker', { get: function () { return undefined; } }); } catch (e) { }
  });
  return { ctx: ctx, trang: trang, loi: loi };
}


/* Chỉ nối cửa thử vào bản trong bộ nhớ. Không sửa tệp app hay gọi API ghi. */
function themCuaThu(src) {
  var db = {
    'xuong-hang': ['html.ui-b .ui-dong-chon{display:flex;flex-wrap:wrap', 'html.ui-b .ui-dong-chon{display:flex;flex-wrap:nowrap'],
    'be-chu': ['gap:8px;word-break:normal;overflow-wrap:anywhere', 'gap:8px;word-break:break-all;overflow-wrap:anywhere'],
    'nut-nho': ['flex:0 1 auto;min-width:44px;min-height:44px', 'flex:0 1 auto;min-width:20px;min-height:20px']
  };
  if (DOT_BIEN) {
    if (!db[DOT_BIEN] || !src.includes(db[DOT_BIEN][0])) throw Error('Không áp được đột biến');
    src = src.replace(db[DOT_BIEN][0], db[DOT_BIEN][1]);
  }
  var i = src.lastIndexOf('})();');
  if (i < 0) throw Error('Không tìm thấy cuối vỏ app');
  return src.slice(0,i) + `window.thu613 = {nhom: function(n) {
    cdlCss();
    CDL.d={bang:{zalo_nhom:{cot:[
      {fn:'ten_nhom',nhan:'Tên nhóm',kieu:'Data'},
      {fn:'chat_id',nhan:'Mã chat Zalo',kieu:'Data'},
      {fn:'tin_nhan',nhan:'Tin nhận',kieu:'Data'},
      {fn:'loai_tin',nhan:'Loại tin nhận',kieu:'Data'},
      {fn:'chu_de',nhan:'Chủ đề nhận',kieu:'Data'}]}}};
    var tin=Object.keys(VGB_CD.ZALO_TIN).slice(0,n).join(', ');
    this.nhap={ten_nhom:'Nhóm thử bố cục',chat_id:n?'zgr-'+ '0123456789'.repeat(8):'',tin_nhan:tin};
    cdlVeDong('zalo_nhom',-1,this.nhap);
  }, khac: function() {
    cdlCss();
    var html=cdlVeO({fn:'ngan_hang_bin',nhan:'Ngân hàng',kieu:'Data'}, {ngan_hang_bin:'12345678901234567890'})+
      cdlVeO({fn:'tai_khoan_thu',nhan:'Tài khoản',kieu:'Link'}, {tai_khoan_thu:'Tài khoản thử nhận chuyển khoản tại quầy có tên dài '+ 'A'.repeat(80)})+
      cdlVeO({fn:'mat_khau_thu',nhan:'Khoá thử',kieu:'Password'}, {mat_khau_thu:'*'});
    frame('Các ô chọn dùng chung',html);
  }, hop: function(trang) { frame('Đối soát nhà cung cấp',dsvnKhoiHop({trang:trang,dia_chi:'hop-thu-doi-soat-rat-dai@'+ 'a'.repeat(60)+'.invalid'})); }
};\n` +src.slice(i);
}
async function doKichThuoc(page) {
 return page.evaluate(function(){
  var loi=[], nut=[];
  function tuGay(el) {
   var walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT), node;
   while((node=walker.nextNode())) {
    var re=/\S+/gu, m;
    while((m=re.exec(node.textContent))) {
     // Mã liền dài được phép ngắt; các từ thông thường phải còn nguyên.
     if(m[0].length>15)continue;
     var r=document.createRange(); r.setStart(node,m.index);r.setEnd(node,m.index+m[0].length);
     var top=Array.from(r.getClientRects()).map(x=>Math.round(x.top));
     if(new Set(top).size>1) return m[0];
    }
   }
   return '';
  }
  document.querySelectorAll('#vgbBody .cdl-val, #vgbBody .card, .shb .ui-dong-chon').forEach(function(row){
   var rr=row.getBoundingClientRect();
   row.querySelectorAll('button,span,b').forEach(function(el){
    var r=el.getBoundingClientRect();
    if(r.width && (r.right>rr.right+1 || r.left<rr.left-1))loi.push('Ra ngoài thẻ: '+el.textContent.slice(0,30));
   });
   var gay=tuGay(row);if(gay)loi.push('Bẻ giữa từ: '+gay);
  });
  document.querySelectorAll('.cdl-lnk').forEach(function(el){
   var r=el.getBoundingClientRect();if(!r.width)return;
   nut.push({nhan:el.textContent,w:r.width,h:r.height});
   if(r.width<44 || r.height<44)loi.push('Nút dưới 44: '+el.textContent);
  });
  if(document.documentElement.scrollWidth>innerWidth+1)loi.push('Tràn ngang trang');
  return {loi:loi,nut:nut};
 });
}
(async function(){
 var browser=await pw.chromium.launch({channel:'chrome'}), rows=[];
 try {
  var t=await moTrang(browser), page=t.trang;
  await page.goto(ORIGIN+'/bep');
  await page.waitForSelector('.gwrap .gt');
  if (await page.evaluate(()=>document.documentElement.classList.contains('ui-b')) !== BAT) throw Error('Sai chế độ giao diện');
  await page.addScriptTag({url:ORIGIN+'/assets/vagabond/js/cai_dat_loi_chung.js'});
  for(var w of [360,390,1366,683]) {
   await page.setViewportSize({width:w,height:w>700?768:844});
   for(var ten of ['nhom-0','nhom-1','nhom-23','khac','hop-chay','hop-chua','hop-loi','hop-tat']) {
    await page.evaluate(function(ten){
     if(ten.startsWith('nhom-'))window.thu613.nhom(+ten.split('-')[1]);
     else if(ten.startsWith('hop-'))window.thu613.hop(ten.split('-')[1]);
     else window.thu613.khac();
    },ten);
    await page.evaluate(()=>document.fonts.ready);
    var kq=await doKichThuoc(page);
    rows.push({ten:ten,w:w,bat:BAT,...kq});
    await page.locator('#vgbBody').screenshot({path:path.join(RA,ten+'-'+w+'.png')});
    if(w===390 || w===1366) await page.locator('#vgbBody').screenshot({path:path.join(RA,ten+'-'+w+'.jpg'),quality:85});
   }
   // Đi qua nút thật, gõ tên trước rồi chọn tin và đóng; không gọi Lưu.
   await page.evaluate(()=>window.thu613.nhom(23));
   await page.locator('[data-cdld="ten_nhom"]').fill('Nhóm thử đã nhập');
   var tinTruoc = await page.evaluate(()=>window.thu613.nhap.tin_nhan);
   await page.locator('[data-cdldtin]').click();
   await page.waitForSelector('[data-cdltca]');
   var sheet=await doKichThuoc(page);
   await page.locator('.shb').screenshot({path:path.join(RA,'chon-tin-'+w+'.png')});
   await page.locator('[data-cdlt]').first().click();
   await page.locator('[data-cdltxong]').click();
   if(await page.locator('[data-cdld="ten_nhom"]').inputValue()!=='Nhóm thử đã nhập')sheet.loi.push('Mất tên nhập dở');
   if(await page.evaluate(()=>window.thu613.nhap.tin_nhan)===tinTruoc)sheet.loi.push('Không đổi được tin đã chọn');
   rows.push({ten:'chon-tin',w:w,bat:BAT,...sheet});
  }
  fs.writeFileSync(path.join(RA,'ket-qua.json'),JSON.stringify(rows,null,2));
  rows.forEach(r=>console.log(r.w+' '+r.ten+' '+(r.loi.length?r.loi.join('; '):'Đạt')));
  if(t.loi.length)throw Error(t.loi.join('\n'));
  process.exitCode=BAT && rows.some(r=>r.loi.length)?1:0;
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=2;});

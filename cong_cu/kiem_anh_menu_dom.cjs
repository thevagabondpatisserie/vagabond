/* v645: ảnh món của màn Biên tập menu, chạy THẬT trên Chromium (canvas, toBlob,
   createImageBitmap thật). Nạp đúng các hàm btm* của 68-bien-tap-menu.js vào
   một trang trống, đưa vào ảnh lớn dựng ngay trong trang (như ảnh chụp điện
   thoại vài MB), rồi đọc lại ảnh ra: phải vuông, cạnh tối đa 1200, dưới 500 KB,
   và đúng phần GIỮA ảnh (hai dải màu ở hai mép bị cắt bỏ).
   Chạy: NODE_PATH=$(npm root -g) node cong_cu/kiem_anh_menu_dom.cjs */
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const SRC = fs.readFileSync(path.resolve(__dirname, '..', 'vagabond/public/js/bep/68-bien-tap-menu.js'), 'utf8');
function layHam(ten) {
  const dau = SRC.search(new RegExp('(?:async )?function ' + ten + '\\('));
  if (dau < 0) throw new Error('Không thấy hàm ' + ten);
  let sau = 0;
  for (let j = SRC.indexOf('{', dau); j < SRC.length; j++) {
    if (SRC[j] === '{') sau++;
    else if (SRC[j] === '}' && !--sau) return SRC.slice(dau, j + 1);
  }
  throw new Error('Hàm ' + ten + ' không đóng ngoặc');
}
function layBien(ten) {
  const m = new RegExp('var ' + ten + ' = [^;]*;').exec(SRC);
  if (!m) throw new Error('Không thấy biến ' + ten);
  return m[0];
}
const MA = ['BTM_ANH_CANH', 'BTM_ANH_TOI_DA', 'BTM_ANH_CHAT'].map(layBien).join('\n') + '\n' +
  ['btmCatVuong', 'btmDocAnh', 'btmNenVuong'].map(layHam).join('\n');

let dat = 0;
(async () => {
  const b = await chromium.launch({headless: true, ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? {executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH} : {})});
  try {
    const p = await b.newPage();
    await p.setContent('<!doctype html><meta charset="utf-8"><body></body>');
    await p.addScriptTag({content: MA + '\nwindow.btmNenVuong = btmNenVuong;'});
    /* Dựng ảnh w x cao: dải đỏ mép trái, dải xanh mép phải (hoặc trên, dưới nếu ảnh dọc),
       giữa là nhiễu (nặng như ảnh thật nhiều chi tiết) hay dải màu mịn. */
    const thu = (w, cao, kieu) => p.evaluate(async ({w, cao, kieu}) => {
      const cv = document.createElement('canvas'); cv.width = w; cv.height = cao;
      const cx = cv.getContext('2d');
      if (kieu === 'nhieu') {
        const d = cx.createImageData(w, cao);
        for (let i = 0; i < d.data.length; i += 4) { d.data[i] = Math.random() * 255; d.data[i + 1] = Math.random() * 255; d.data[i + 2] = Math.random() * 255; d.data[i + 3] = 255; }
        cx.putImageData(d, 0, 0);
      } else {
        const g = cx.createLinearGradient(0, 0, w, cao); g.addColorStop(0, '#d9a066'); g.addColorStop(1, '#5b3a1e');
        cx.fillStyle = g; cx.fillRect(0, 0, w, cao);
      }
      const doc = cao > w, le = Math.abs(w - cao) / 2;
      cx.fillStyle = '#ff0000'; doc ? cx.fillRect(0, 0, w, le) : cx.fillRect(0, 0, le, cao);
      cx.fillStyle = '#0000ff'; doc ? cx.fillRect(0, cao - le, w, le) : cx.fillRect(w - le, 0, le, cao);
      const goc = await new Promise(r => cv.toBlob(r, 'image/png'));
      const f = new File([goc], 'IMG_7295.PNG', {type: 'image/png'});
      const n = await window.btmNenVuong(f);
      const bm = await createImageBitmap(n.blob);
      const c2 = document.createElement('canvas'); c2.width = bm.width; c2.height = bm.height;
      const x2 = c2.getContext('2d'); x2.drawImage(bm, 0, 0);
      const mau = (x, y) => Array.from(x2.getImageData(x, y, 1, 1).data.slice(0, 3));
      const e = bm.width - 3;
      return {goc: goc.size, size: n.blob.size, type: n.blob.type, canh: n.canh, kb: n.kb, w: bm.width, cao: bm.height,
        bon_goc: [mau(2, 2), mau(e, 2), mau(2, e), mau(e, e)]};
    }, {w, cao, kieu});
    const khongDai = (r, ten) => r.bon_goc.forEach(c => assert.ok(!(c[0] > 200 && c[1] < 60 && c[2] < 60) && !(c[2] > 200 && c[0] < 60 && c[1] < 60), ten + ': góc còn dải mép ' + JSON.stringify(r.bon_goc)));

    const a = await thu(4032, 3024, 'min');
    assert.ok(a.goc > 1024 * 1024, 'ảnh vào đủ lớn: ' + a.goc);
    assert.deepEqual([a.w, a.cao, a.canh, a.type], [1200, 1200, 1200, 'image/jpeg']);
    assert.ok(a.size <= 500 * 1024 && a.kb === Math.ceil(a.size / 1024), 'dưới 500 KB: ' + a.size);
    khongDai(a, 'ảnh ngang');
    console.log('PASS ảnh ngang 4032x3024 (' + Math.round(a.goc / 1024) + ' KB) ra 1200x1200 JPEG ' + a.kb + ' KB, cắt đúng giữa'); dat++;

    const c = await thu(1080, 1920, 'min');
    assert.deepEqual([c.w, c.cao], [1080, 1080], 'ảnh dọc nhỏ hơn 1200 không phóng to');
    khongDai(c, 'ảnh dọc');
    console.log('PASS ảnh dọc 1080x1920 ra 1080x1080, cắt bỏ trên dưới'); dat++;

    const n = await thu(3000, 2400, 'nhieu');
    assert.ok(n.goc > 5 * 1024 * 1024, 'ảnh nhiễu rất nặng: ' + n.goc);
    assert.equal(n.w, n.cao);
    assert.ok(n.size <= 500 * 1024, 'ảnh nhiều chi tiết vẫn dưới 500 KB: ' + n.size);
    khongDai(n, 'ảnh nhiễu');
    console.log('PASS ảnh nhiều chi tiết ' + Math.round(n.goc / 1024 / 1024) + ' MB ra ' + n.canh + 'x' + n.canh + ' JPEG ' + n.kb + ' KB'); dat++;

    /* Hạ nấc chất lượng chưa đủ thì phải hạ cạnh: đặt trần thấp để buộc đi nhánh này. */
    await p.evaluate(() => { window.BTM_ANH_TOI_DA = 120 * 1024; });
    const k = await thu(3000, 2400, 'nhieu');
    await p.evaluate(() => { window.BTM_ANH_TOI_DA = 500 * 1024; });
    assert.ok(k.size <= 120 * 1024 && k.canh < 1200 && k.w === k.canh && k.cao === k.canh, 'hạ cạnh: ' + JSON.stringify([k.size, k.canh]));
    console.log('PASS chất lượng thấp nhất vẫn nặng thì hạ cạnh còn ' + k.canh + 'px, ' + k.kb + ' KB'); dat++;

    const hong = await p.evaluate(async () => {
      try { await window.btmNenVuong(new File([new Uint8Array([1, 2, 3])], 'x.jpg', {type: 'image/jpeg'})); return 'không báo'; }
      catch (e) { return e.message; }
    });
    assert.match(hong, /Không đọc được ảnh/);
    console.log('PASS tệp không phải ảnh: báo không đọc được'); dat++;

    /* Trang gọi món tại bàn: khung ảnh món phải VUÔNG ở máy điện thoại lẫn màn rộng, ảnh
       vuông tải lên không bị cắt. Nạp đúng banh.css thật cùng khung bảng chọn món. */
    const css = fs.readFileSync(path.resolve(__dirname, '..', 'vagabond/public/web_vue/banh/banh.css'), 'utf8');
    for (const [w, cao] of [[390, 844], [390, 600], [1440, 900]]) {
      const q = await b.newPage({viewport: {width: w, height: cao}});
      await q.setContent('<!doctype html><meta charset="utf-8"><body><div class="sheet gb-sheet open"><div class="gb-khung"><div class="gb-than">' +
        '<div class="gb-anh"><img alt="" src="data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%221200%22 height=%221200%22/%3E"></div></div></div></div></body>');
      await q.addStyleTag({content: css});
      const k = await q.evaluate(() => { const r = document.querySelector('.gb-anh').getBoundingClientRect(); const i = document.querySelector('.gb-anh img').getBoundingClientRect(); return {w: r.width, h: r.height, iw: i.width, ih: i.height, vh: innerHeight}; });
      assert.ok(k.w > 100 && Math.abs(k.w - k.h) <= 2, w + 'x' + cao + ': khung ảnh không vuông ' + JSON.stringify(k));
      assert.ok(Math.abs(k.iw - k.ih) <= 2, w + 'x' + cao + ': ảnh trong khung không vuông ' + JSON.stringify(k));
      assert.ok(k.h <= k.vh * 0.46 + 2, w + 'x' + cao + ': ảnh cao quá 46% màn ' + JSON.stringify(k));
      await q.close();
      console.log('PASS khung ảnh món trang gọi món ' + w + 'x' + cao + ': vuông ' + Math.round(k.w) + 'px'); dat++;
    }
  } finally { await b.close(); }
  console.log(dat + ' ca ảnh menu đạt');
})().catch(e => { console.error(e); process.exitCode = 1; });

/* v653 Nhật ký BTP (sự cố Tira 18cm, Loan Anh báo 12/11/2026): chạy THẬT khối
 * đầu của trang /kiem-banh trong node, máy chủ giả. Chốt:
 *   1. dưới BTP sẵn và Đủ decor luôn có dòng "ai đổi, lúc nào" (chữ máy chủ
 *      dựng sẵn), dưới Bếp làm có "Hân 21:05";
 *   2. bấm dòng đó mở hộp 10 lần đổi gần nhất, gọi đúng lich_su_btp của mã,
 *      không mở ô sửa số;
 *   3. tên lạ có thẻ HTML không chèn được vào trang;
 *   4. chữ mới trên màn từ 13 điểm, dòng bấm được cao từ 44 điểm.
 * Phần dựng trang chép nguyên từ hanh_vi/kiem_banh.js. */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var TRANG = path.join(GOC, 'vagabond', 'trang');

/* Trang /kiem-banh có HAI khối độc lập trong một tệp: khối Kiểm bánh ngày và
   khối Kiểm kho điểm. Chỉ nạp khối ĐẦU, vì khối sau gọi API khác và sẽ ẩn
   mất thành phần của khối đầu khi danh sách điểm rỗng. Cắt theo dấu đóng
   `})();` ở cột 0 - nếu tệp đổi cấu trúc thì phép cắt hỏng và ca kiểm nổ
   ngay, chứ không lặng lẽ kiểm nhầm khối. */
function napKhoiDau() {
  var src = fs.readFileSync(path.join(TRANG, 'kiem-banh.js'), 'utf8');
  var het = src.indexOf('\n})();');
  if (het < 0) throw new Error('Khong tim thay cuoi khoi dau cua kiem-banh.js');
  var khoi = src.slice(0, het + '\n})();'.length);
  if (khoi.indexOf('function luuO(') < 0) {
    throw new Error('Khoi dau khong chua luuO - tep da doi cau truc, sua lai phep cat');
  }
  return khoi;
}

var HTML_TRANG = [
  '<div id="kb-tabs"></div>',
  '<div id="kb-ngay-to"></div>',
  '<div id="kb-chips"></div>',
  '<div id="kb-luc"></div>',
  '<div id="kb-btp-luc"></div>',
  '<button id="kb-dongbo"></button>',
  '<button id="kb-them"></button>',
  '<button id="kb-tuvan"></button>',
  '<button id="kb-chot"></button>',
  '<div id="kb-dachot"></div>',
  '<div id="kb-bao"></div>',
  '<div id="kb-canh"></div>',
  '<div id="kb-luoi"></div>',
].join('');

/* Một lời hẹn giữ lại được: trả về promise cho mã nguồn, còn ca kiểm giữ dây
   cương để quyết định BAO GIỜ máy chủ trả lời. Không có nó thì không kiểm
   được "trong lúc chờ thì màn hình nói gì". */
function loiHen() {
  var mo = {};
  mo.p = new Promise(function (ok, hong) { mo.ok = ok; mo.hong = hong; });
  return mo;
}

function dungMan(canh) {
  canh = canh || {};
  var tai = dg.taiLieuGia();
  tai.body.innerHTML = HTML_TRANG;
  tai.readyState = 'complete';
  tai.visibilityState = 'visible';

  var goi = [];          // moi loi goi may chu, theo dung thu tu
  var hen = [];          // cac loi hen dang treo, ca kiem tu tha
  var nhip = [];         // cac setInterval bi chan lai

  function traLoi(ten, ts) {
    if (canh.traLoi) { var r = canh.traLoi(ten, ts); if (r) return { ok: 1, than: r }; }
    if (ten === 'kiem_banh.bang' || ten === 'kiem_banh.dong_bo') {
      return { ok: 1, than: canh.bang() };
    }
    if (ten === 'kiem_banh.quyen_btp') return { ok: 1, than: { sua: false } };
    if (ten === 'btp.bang') return { ok: 1, than: { dong: [], cap_nhat_luc: '' } };
    return { ok: 1, than: {} };
  }

  var that = {
    console: console, Math: Math, JSON: JSON, Date: Date, String: String,
    Number: Number, Array: Array, Object: Object, RegExp: RegExp,
    Promise: Promise, isNaN: isNaN, parseInt: parseInt, parseFloat: parseFloat,
    setTimeout: setTimeout, clearTimeout: clearTimeout,
    /* Chặn bốn vòng setInterval của boot: ca kiểm này đo một chuỗi thao tác,
       không đời nào muốn một vòng nền chạy chen vào giữa rồi vẽ lại lưới. */
    setInterval: function (f, ms) { nhip.push(ms); return nhip.length; },
    clearInterval: function () {},
    document: tai,
    fetch: function (duong, tuy) {
      var ten = String(duong).split('/api/method/vagabond.')[1] || String(duong);
      var ts = {};
      try { ts = JSON.parse((tuy && tuy.body) || '{}'); } catch (e) { ts = {}; }
      var ban = { ten: ten, ts: ts };
      goi.push(ban);
      var giu = canh.giu && canh.giu(ten);
      if (giu) { hen.push(giu); ban.hen = giu; return giu.p; }
      var kq = traLoi(ten, ts);
      return Promise.resolve({
        ok: true, status: 200,
        json: function () { return Promise.resolve({ message: kq.than }); },
      });
    },
  };
  that.window = that;
  that.globalThis = that;
  that.window.addEventListener = function () {};
  that.window.confirm = function () { return true; };
  that.csrf_token = 'x';

  vm.runInNewContext(napKhoiDau(), that, { filename: 'kiem-banh.js' });
  return { g: that, tai: tai, goi: goi, hen: hen, nhip: nhip };
}

/* ---------- cong cu ---------- */

var ket = { dat: 0, hong: 0 };

function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) {
  if (a !== b) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b));
}

/* Chờ tới khi điều kiện đúng, TỐI ĐA `tran` nhịp. Hết nhịp là NÉM LỖI.
   Không dùng ngủ cố định: ngủ cố định thì máy chậm một chút là đỏ oan, mà
   máy nhanh thì phí thời gian. */
async function choToi(mo, dieuKien, tran) {
  tran = tran || 200;
  for (var i = 0; i < tran; i++) {
    if (dieuKien()) return i;
    await new Promise(function (r) { setTimeout(r, 0); });
  }
  throw new Error('Cho mai khong thay: ' + mo);
}

function oTheo(m, id) {
  return m.tai.querySelectorAll('[data-id]').filter(function (e) {
    return e.getAttribute('data-id') === id;
  })[0] || null;
}

/* Đọc số trong một ô theo NHÃN, đúng như người nhìn bảng. */
function soTheoNhan(m, nhan) {
  var o = m.tai.querySelectorAll('.kb-o').filter(function (e) {
    var l = e.querySelector('label');
    return l && l.textContent.trim() === nhan;
  })[0];
  if (!o) throw new Error('Khong thay o co nhan ' + nhan);
  var b = o.querySelector('b');
  return b ? b.textContent.trim() : null;
}

function dong(kw) {
  var d = {
    ma_hang: 'BAWC00055', ten_banh: 'Bánh thử', hinh: '',
    ton_cu: 0, nsx_cu: '', ton_d2: 0, nsx_d2: '', ton_d1: 0, nsx_d1: '',
    sx: 0, huy: 0, da_dat: 0, phat_sinh: 0, ten_khach_ps: '',
    cho_chot: 0, ten_khach_cho: '', don_khac: 0, ten_khach_khac: '',
    co_the_ban: 0, tat_web: 0, tat_web_den: '',
  };
  Object.keys(kw || {}).forEach(function (k) { d[k] = kw[k]; });
  d.co_the_ban = d.ton_cu + d.ton_d2 + d.ton_d1 + d.sx
    - d.huy - d.da_dat - d.phat_sinh - d.cho_chot - d.don_khac;
  return d;
}

/* Ngay theo GIO DIA PHUONG, dung cach trang ghep (ngayISO trong kiem-banh.js).
   Truoc day dung toISOString() la gio UTC: trang gui ngay dia phuong, bo ca
   tra ve ngay UTC, nhan() thay lech ngay thi bo qua, luoi khong ve, 7/7 ca
   hong khi may chay o mui gio lech UTC qua nua dem (Codex neu tren PR #223).
   Cong deploy chay tep nay them o hai mui gio doi nhau de bat lai loi nay. */
function ngayDiaPhuong(d) {
  return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
}

function bangCua(ds, tinh_trang) {
  return {
    ngay: ngayDiaPhuong(new Date()),
    co_so: 1, tinh_trang: tinh_trang || 'Dang ban',
    dong_bo_luc: '', chot_luc: '', dong: ds,
  };
}

async function moMan(canh) {
  var m = dungMan(canh);
  await choToi('luoi ve xong lan dau', function () {
    return m.tai.querySelectorAll('[data-id]').length > 0;
  });
  return m;
}


var CA = [];
function ca(ten, ham) { CA.push([ten, ham]); }

var MA = 'BAWC00079';
function canhTira(them) {
  return Object.assign({
    bang: function () { return bangCua([dong({ ma_hang: MA, ten_banh: 'Bánh Ổ Tira-Missing-U 3.0, 18cm', sx: 1, sx_ai: 'Hân 21:05' })]); },
    traLoi: function (ten, ts) {
      if (ten === 'btp.quyen_btp') return { sua: 1 };
      if (ten === 'btp.bang_btp') return { cap_nhat_luc: '2026-11-12 22:27:55', dat_xa: {}, lich_refill: [], dong: [
        { ma_hang: MA, ten_banh: 'Tira 18', so_btp: 2, so_decor: 2, con_nhan: 2, giao_mai: 2,
          doi: { so_btp: { chu: 'Linh 22:27 · nhập tay' }, so_decor: { chu: 'Máy trừ · Bếp làm 13/11 (Hân)' } } }] };
      if (ten === 'btp.lich_su_btp') return { ma_hang: ts.ma_hang, dong: [
        { o: 'BTP sẵn', truoc: '1', sau: '2', chu: 'Linh 22:27 · nhập tay' },
        { o: 'Đủ decor', truoc: '2', sau: '1', chu: 'Máy trừ · Bếp làm 13/11 (Hân)' }] };
      return null;
    },
  }, them || {});
}

function chuDuoi(m, nhan) {
  var o = m.tai.querySelectorAll('.kb-o').filter(function (e) {
    var l = e.querySelector('label');
    return l && l.textContent.trim().indexOf(nhan) === 0;
  })[0];
  if (!o) throw new Error('Khong thay o ' + nhan);
  var n = o.querySelectorAll('.kb-nguon').map(function (x) { return x.textContent.trim(); });
  return n.join(' | ');
}

ca('duoi BTP san, Du decor, Bep lam luon co dong ai doi luc nao', async function () {
  var m = await moMan(canhTira());
  await choToi('bang BTP ve xong', function () { return m.tai.querySelectorAll('[data-lsbtp]').length === 2; });
  bang('BTP san', chuDuoi(m, 'BTP sẵn'), 'Linh 22:27 · nhập tay');
  bang('Du decor', chuDuoi(m, 'Đủ decor'), 'Máy trừ · Bếp làm 13/11 (Hân)');
  bang('Bep lam', chuDuoi(m, 'Bếp làm'), 'Hân 21:05');
});

ca('bam dong ai doi mo hop lich su dung ma, khong mo o sua so', async function () {
  var m = await moMan(canhTira());
  await choToi('bang BTP ve xong', function () { return m.tai.querySelectorAll('[data-lsbtp]').length === 2; });
  var el = m.tai.querySelectorAll('[data-lsbtp]')[0];
  el.click();
  await choToi('goi lich su', function () { return m.goi.some(function (g) { return g.ten === 'btp.lich_su_btp'; }); });
  var g = m.goi.filter(function (x) { return x.ten === 'btp.lich_su_btp'; })[0];
  bang('dung ma', g.ts.ma_hang, MA);
  bang('10 lan', g.ts.so, 10);
  dung('khong mo o nhap so', !m.tai.getElementById('kb-inp'));
  await choToi('hop hien dong lich su', function () { var d = m.tai.getElementById('kb-ls-ds'); return d && d.innerHTML.indexOf('kb-ls-dong') >= 0; });
  var t = m.tai.getElementById('kb-ls-ds').textContent;
  dung('hien BTP san 1 thanh 2', t.indexOf('BTP sẵn: 1 → 2') >= 0);
  dung('hien ai doi', t.indexOf('Linh 22:27 · nhập tay') >= 0);
  m.tai.getElementById('kb-ls-dong').click();
  dung('dong hop', !m.tai.getElementById('kb-ls-lop'));
});

ca('ten la co the HTML khong chen duoc vao trang', async function () {
  var m = await moMan(canhTira({ bang: function () { return bangCua([dong({ ma_hang: MA, sx: 1, sx_ai: '<img src=x onerror=1> 21:05' })]); } }));
  await choToi('ve', function () { return m.tai.querySelectorAll('.kb-ai').length === 1; });
  dung('khong co the img la', m.tai.querySelectorAll('img').filter(function (x) { return x.getAttribute('onerror'); }).length === 0);
});

ca('chu moi tu 13 diem, dong bam duoc cao tu 44 diem', async function () {
  var css = fs.readFileSync(path.join(TRANG, 'kiem-banh.html'), 'utf8');
  var moi = css.split('\n').filter(function (l) { return /kb-doi|kb-ls-/.test(l); });
  dung('co luat CSS moi', moi.length >= 5);
  moi.forEach(function (l) {
    (l.match(/font-size:(\d+(?:\.\d+)?)px/g) || []).forEach(function (f) {
      dung('co chu >= 13: ' + l.slice(0, 40), parseFloat(f.replace(/[^\d.]/g, '')) >= 13);
    });
  });
  dung('dong bam cao 44', /\.kb-nguon\.kb-doi\{[^}]*min-height:44px/.test(css));
  var btp = fs.readFileSync(path.join(TRANG, 'btp.html'), 'utf8');
  dung('trang /btp chu ai doi 13 diem', /\.bt-ai\{font-size:13px/.test(btp));
});

(async function () {
  for (var i = 0; i < CA.length; i++) {
    try { await CA[i][1](); ket.dat++; console.log('  DAT  ' + CA[i][0]); }
    catch (e) { ket.hong++; console.log('  HONG ' + CA[i][0] + '\n       ' + (e && e.stack || e)); }
  }
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong');
  process.exit(ket.hong ? 1 : 0);
})();

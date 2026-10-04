/* v571: ô tìm, chip nhóm bánh, chip trạng thái trên trang /kiem-banh.
 *
 * Anh Việt 04/10/2026: màn kiểm bánh thiếu chip lọc, chip trạng thái, phân
 * loại theo nhóm bánh (Bánh nướng, bánh lạnh, bánh khô), ô tìm theo tên theo
 * mã. Ca kiểm nạp THẬT khối Kiểm bánh ngày (kèm bộ lọc dùng chung KB_LOC ở
 * đầu tệp) vào DOM giả, rồi gõ và bấm đúng như người dùng. Không gọi thêm
 * hàm nào ngoài chuỗi thao tác (điều 15). Phần dựng màn chép từ kiem_banh.js,
 * chỉ thêm hộp #kb-loc.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/kiem_banh_loc_571.js
 */
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
  '<div id="kb-loc"></div>',
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

  function traLoi(ten) {
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
      var kq = traLoi(ten);
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

function maTrenLuoi(m) {
  /* Ma o tung the doc tu o dau co data-id "MA|truong", dung thu tu tren luoi. */
  var ra = [];
  m.tai.querySelectorAll('.kb-the').forEach(function (t) {
    var o = t.querySelector('[data-id]');
    if (o) ra.push(o.getAttribute('data-id').split('|')[0]);
  });
  return ra;
}
function nhomTrenLuoi(m) {
  return m.tai.querySelectorAll('.kb-nhom-td').map(function (e) { return e.textContent.trim(); });
}
function chipCo(m, attr, k) {
  return m.tai.querySelectorAll('[' + attr + ']').filter(function (e) { return e.getAttribute(attr) === k; })[0];
}
function go(m, chu) {
  var o = m.tai.getElementById('kb-loc-tim');
  o.value = chu;
  o.oninput();
}

var BANG = [
  dong({ ma_hang: 'BAEN00012', ten_banh: 'Mousse Trà Xanh', ton_d1: 4 }),
  dong({ ma_hang: 'BANU00003', ten_banh: 'Pâté chaud', ton_d1: 0 }),
  dong({ ma_hang: 'BACF00007', ten_banh: 'Cookie Bơ Đậu Phộng', ton_d1: 2, cho_chot: 3 }),
  dong({ ma_hang: 'BAEN00020', ten_banh: 'Tiramisu', ton_d1: 1, huy: 1 }),
  dong({ ma_hang: 'BAWC00055', ten_banh: 'Bánh sinh nhật Dâu', ton_d1: 5 }),
];

ca('bang chia theo nhom banh, dung thu tu nuong, lanh, kho roi toi nhom khac', async function () {
  var m = await moMan({ bang: function () { return bangCua(BANG); } });
  var td = nhomTrenLuoi(m);
  bang('so nhom', td.length, 4);
  dung('nhom dau la Banh nuong, duoc ' + td[0], /^Bánh nướng/.test(td[0]));
  dung('nhom hai la Banh lanh co 2 dong, duoc ' + td[1], /^Bánh lạnh\s*2$/.test(td[1]));
  dung('nhom ba la Banh kho', /^Bánh khô/.test(td[2]));
  dung('banh sinh nhat KHONG bi giau, nam nhom rieng', /^Bánh sinh nhật/.test(td[3]));
  bang('du 5 dong', maTrenLuoi(m).length, 5);
});

ca('go ten KHONG DAU thi loc dung banh, go ma cung ra', async function () {
  var m = await moMan({ bang: function () { return bangCua(BANG); } });
  go(m, 'tra xanh');
  bang('chi Mousse Tra Xanh', maTrenLuoi(m).join(','), 'BAEN00012');
  go(m, 'bacf');
  bang('go ma', maTrenLuoi(m).join(','), 'BACF00007');
  go(m, 'pate');
  bang('pâté go khong dau', maTrenLuoi(m).join(','), 'BANU00003');
  go(m, '');
  bang('xoa chu thi hien lai du', maTrenLuoi(m).length, 5);
});

ca('bam chip nhom Banh lanh thi chi con banh lanh, chip mang so dem dung', async function () {
  var m = await moMan({ bang: function () { return bangCua(BANG); } });
  var c = chipCo(m, 'data-lcn', 'lanh');
  dung('co chip Banh lanh', !!c);
  dung('chip ghi so 2, duoc ' + c.textContent, /2/.test(c.textContent));
  c.click();
  bang('chi banh lanh', maTrenLuoi(m).join(','), 'BAEN00012,BAEN00020');
  dung('chip dang chon', (chipCo(m, 'data-lcn', 'lanh').className || '').indexOf('on') >= 0);
});

ca('chip trang thai: Het, Khach cho chot, Co huy loc dung dong', async function () {
  var m = await moMan({ bang: function () { return bangCua(BANG); } });
  chipCo(m, 'data-lct', 'het').click();
  bang('het: Tiramisu (1-1) va Pate (0)', maTrenLuoi(m).join(','), 'BANU00003,BAEN00020');
  chipCo(m, 'data-lct', 'cho').click();
  bang('khach cho chot', maTrenLuoi(m).join(','), 'BACF00007');
  chipCo(m, 'data-lct', 'huy').click();
  bang('co huy', maTrenLuoi(m).join(','), 'BAEN00020');
});

ca('ba bo loc chong nhau, loc ra rong thi noi ro va co nut Bo loc', async function () {
  var m = await moMan({ bang: function () { return bangCua(BANG); } });
  chipCo(m, 'data-lcn', 'kho').click();
  go(m, 'tiramisu');
  bang('khong dong nao', maTrenLuoi(m).length, 0);
  var nut = m.tai.querySelector('[data-boloc]');
  dung('co nut Bo loc', !!nut);
  nut.click();
  bang('bo loc thi hien lai du', maTrenLuoi(m).length, 5);
  bang('o tim duoc xoa', m.tai.getElementById('kb-loc-tim').value, '');
});

ca('dang loc ma may chu tra bang moi thi bo loc VAN GIU, o tim khong bi ve lai', async function () {
  var lan = 0;
  var m = await moMan({ bang: function () { lan++; return bangCua(lan > 1 ? BANG.concat([dong({ ma_hang: 'BAEN00099', ten_banh: 'Trà xanh Matcha' })]) : BANG); } });
  go(m, 'tra xanh');
  var oTruoc = m.tai.getElementById('kb-loc-tim');
  m.tai.getElementById('kb-dongbo').click();
  await choToi('bang moi ve', function () { return maTrenLuoi(m).length === 2; });
  bang('ca hai banh tra xanh', maTrenLuoi(m).join(','), 'BAEN00012,BAEN00099');
  dung('o tim van la o cu (khong mat con tro)', m.tai.getElementById('kb-loc-tim') === oTruoc);
});

ca('CSS: chip loc va o tim du 44 diem', async function () {
  var css = fs.readFileSync(path.join(TRANG, 'kiem-banh.html'), 'utf8');
  dung('chip loc min-height 44', /\.kb-lc\{[^}]*min-height:44px/.test(css));
  dung('o tim min-height 44', /\.kb-tim\{[^}]*min-height:44px/.test(css));
  dung('trang that co hop kb-loc', css.indexOf('id="kb-loc"') >= 0);
  dung('trang that co hop kk-loc', css.indexOf('id="kk-loc"') >= 0);
});

/* ---------- chay ---------- */

async function chay() {
  console.log('Bo loc trang /kiem-banh (v571, DOM gia)');
  console.log('');
  for (var i = 0; i < CA.length; i++) {
    var ten = CA[i][0];
    try {
      await CA[i][1]();
      ket.dat++;
      console.log('  dat   ' + ten);
    } catch (e) {
      ket.hong++;
      console.log('  HONG  ' + ten);
      console.log('        ' + (e && e.message ? e.message : e));
    }
  }
  console.log('');
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + CA.length + ' ca.');
  process.exit(ket.hong ? 1 : 0);
}

chay();

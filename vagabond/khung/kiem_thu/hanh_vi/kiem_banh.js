/* Bộ ca kiểm HÀNH VI cho trang /kiem-banh, phần CHUỖI GÕ Ô HUỶ.
 *
 * Vì sao có tệp này. Codex đòi trên PR #218: "có ca giao diện gõ Huỷ -> lưu
 * -> chờ đúng phản hồi -> kiểm BÁN ĐƯỢC". Bộ kiểm thử tầng khung viết bằng
 * Python, không có DOM, nên mọi ca dính tới giao diện đều chỉ dò được CHUỖI
 * trong mã nguồn. Dò chuỗi không chứng minh được rằng bấm vào ô Huỷ thì ô
 * nhập hiện ra, gõ 3 thì lời gọi đi đúng trường, và số BÁN ĐƯỢC chỉ đổi SAU
 * KHI máy chủ trả lời.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/kiem_banh.js
 *        (cổng kiem_truoc_deploy.sh chạy tệp này ở công đoạn 10)
 *
 * KHÔNG cần trình duyệt. Dùng đúng `dom_gia.js` của bộ hành vi sẵn có, nên
 * chạy được trên máy CI tay không - cùng chỗ mà công đoạn 10 đang chạy.
 *
 * HAI LUẬT CỦA TỆP NÀY, đừng sửa cho gọn:
 *
 *   1. KHÔNG gọi thêm hàm nào ngoài chuỗi thao tác của khách. Điều 15 của bộ
 *      quy tắc sinh ra từ một ca gọi thêm một hàm "cho chắc", mà chính hàm đó
 *      lại chữa lỗi ngay trước khi ca kiểm kịp nhìn. Ở đây chỉ được bấm, gõ
 *      và bắn sự kiện.
 *   2. Chờ phải CÓ HẠN. Không ngủ một khoảng cố định rồi khẳng định. `choToi`
 *      quay tối đa N nhịp rồi NÉM LỖI - treo thì ca đỏ, không xanh oan.
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

/* ---------- cac ca ---------- */

var CA = [];
function ca(ten, ham) { CA.push([ten, ham]); }


ca('bam o Huy thi hien o nhap, go 3 thi goi luu_o dung truong va dung so', async function () {
  var soNha = dong({ ton_d1: 10 });
  var m = await moMan({ bang: function () { return bangCua([soNha]); } });

  bang('ban dau BAN DUOC la 10', soTheoNhan(m, 'BÁN ĐƯỢC'), '10');
  bang('ban dau Huy la 0', soTheoNhan(m, 'Huỷ'), '0');

  var o = oTheo(m, 'BAWC00055|huy');
  dung('co o Huy bam duoc', !!o);
  dung('o Huy mang lop sua duoc', (o.className || '').indexOf('sua') >= 0);
  o.click();

  var inp = m.tai.getElementById('kb-inp');
  dung('bam xong thi o nhap hien ra', !!inp);

  var truoc = m.goi.length;
  inp.value = '3';
  inp.dispatchEvent(dg.suKien('change', {}, inp));

  await choToi('loi goi luu_o bay di', function () { return m.goi.length > truoc; });
  var g = m.goi[truoc];
  bang('goi dung cua', g.ten, 'kiem_banh.luu_o');
  bang('dung ma hang', g.ts.ma_hang, 'BAWC00055');
  bang('dung truong', g.ts.truong, 'huy');
  bang('dung so vua go', g.ts.gia_tri, 3);
  dung('co kem ngay', !!g.ts.ngay);
});


ca('so tren bang chi doi SAU KHI may chu tra loi, khong doi ngay luc go', async function () {
  /* Đây là chỗ dễ sai nhất: vẽ lại bằng số vừa gõ là màn hình nói dối. Nếu
     máy chủ từ chối thì người dùng đã tin vào một con số không có thật. */
  var soNha = dong({ ton_d1: 10 });
  var daLuu = false;
  var m = await moMan({
    bang: function () { return bangCua([daLuu ? dong({ ton_d1: 10, huy: 3 }) : soNha]); },
    giu: function (ten) { return ten === 'kiem_banh.luu_o' ? loiHen() : null; },
  });

  oTheo(m, 'BAWC00055|huy').click();
  var inp = m.tai.getElementById('kb-inp');
  inp.value = '3';
  inp.dispatchEvent(dg.suKien('change', {}, inp));
  await choToi('loi goi luu_o treo lai', function () { return m.hen.length === 1; });

  /* ĐANG TREO: quay vài nhịp cho mọi promise rảnh rồi mới kiểm. Không gọi
     ve() hay taiLai() để "cho chắc" - gọi là chính tay chữa lấy trạng thái
     mình sắp kiểm, đúng cái bẫy của điều 15. */
  for (var i = 0; i < 5; i++) await new Promise(function (r) { setTimeout(r, 0); });
  bang('dang cho thi BAN DUOC van la 10', soTheoNhan(m, 'BÁN ĐƯỢC'), '10');
  bang('dang cho thi chua bao da luu', m.tai.getElementById('kb-bao').textContent, '');

  /* Thả máy chủ ra, và từ đây trở đi bảng trả về số mới. */
  daLuu = true;
  m.hen[0].ok({ ok: true, status: 200, json: function () { return Promise.resolve({ message: { ok: 1 } }); } });

  await choToi('bang doi sang huy 3', function () {
    try { return soTheoNhan(m, 'Huỷ') === '3'; } catch (e) { return false; }
  });
  bang('BAN DUOC tut tu 10 xuong 7', soTheoNhan(m, 'BÁN ĐƯỢC'), '7');
});


ca('may chu loi thi bao do va tai lai, KHONG bao da luu', async function () {
  var m = await moMan({
    bang: function () { return bangCua([dong({ ton_d1: 10 })]); },
    giu: function (ten) { return ten === 'kiem_banh.luu_o' ? loiHen() : null; },
  });

  oTheo(m, 'BAWC00055|huy').click();
  var inp = m.tai.getElementById('kb-inp');
  inp.value = '3';
  inp.dispatchEvent(dg.suKien('change', {}, inp));
  await choToi('loi goi luu_o treo lai', function () { return m.hen.length === 1; });

  var soGoiTruoc = m.goi.length;
  m.hen[0].ok({
    ok: false, status: 417,
    json: function () {
      return Promise.resolve({ exception: 'Số huỷ phải là số nguyên không âm' });
    },
  });

  var el = m.tai.getElementById('kb-bao');
  await choToi('man hinh bao loi', function () { return el.textContent !== ''; });
  bang('bao do chu khong bao thuong', el.className, 'loi');
  dung('loi nhac dung viec', el.textContent.indexOf('không âm') >= 0);

  /* Đường thử lại: màn tự tải lại từ máy chủ, nên số trên bảng là số THẬT
     chứ không phải số vừa gõ hỏng. */
  await choToi('co goi tai lai sau khi loi', function () {
    return m.goi.slice(soGoiTruoc).some(function (g) { return g.ten === 'kiem_banh.bang'; });
  });
  bang('so tren bang tro ve so that', soTheoNhan(m, 'Huỷ'), '0');
  bang('BAN DUOC khong bi tru oan', soTheoNhan(m, 'BÁN ĐƯỢC'), '10');
});


ca('ngay da chot thi bam o Huy khong mo duoc o nhap', async function () {
  var m = await moMan({
    bang: function () { return bangCua([dong({ ton_d1: 10 })], 'Da chot'); },
  });
  var truoc = m.goi.length;
  oTheo(m, 'BAWC00055|huy').click();
  dung('khong mo o nhap', !m.tai.getElementById('kb-inp'));
  bang('va khong goi may chu', m.goi.length, truoc);
  dung('co noi ly do', m.tai.getElementById('kb-bao').textContent.indexOf('chốt sổ') >= 0);
});


ca('go so huy KHONG hop le (-0.5, 1.9, am, chu, vo han): khong gui, khong dong o, bao ro ma hang, bang giu nguyen', async function () {
  /* Codex vong 4 tren #218: luuO parseInt truoc khi may chu kip nhin gia
     tri goc, nen 1.9 di thanh 1 va -0.5 thanh 0 ma nguoi go khong biet.
     Nay kiem CHUOI GOC. Sai thi khong gui, o nhap van mo voi dung chuoi vua
     go, bang khong doi. */
  var cacXau = ['-0.5', '1.9', '-2', 'abc', 'Infinity', 'NaN', '1e3', '3.0'];
  for (var i = 0; i < cacXau.length; i++) {
    var xau = cacXau[i];
    var m = await moMan({ bang: function () { return bangCua([dong({ ton_d1: 10, huy: 2 })]); } });
    oTheo(m, 'BAWC00055|huy').click();
    var inp = m.tai.getElementById('kb-inp');
    dung('o nhap mo (' + xau + ')', !!inp);
    var truoc = m.goi.length;
    inp.value = xau;
    inp.dispatchEvent(dg.suKien('change', {}, inp));
    for (var k = 0; k < 5; k++) await new Promise(function (r) { setTimeout(r, 0); });
    bang('KHONG goi may chu (' + xau + ')', m.goi.length, truoc);
    var el = m.tai.getElementById('kb-bao');
    dung('bao do (' + xau + '): ' + el.textContent, el.className === 'loi' && el.textContent.indexOf('BAWC00055') >= 0);
    dung('noi ro phai la so nguyen khong am (' + xau + ')', el.textContent.indexOf('số nguyên không âm') >= 0);
    var inp2 = m.tai.getElementById('kb-inp');
    dung('o nhap VAN MO de sua (' + xau + ')', !!inp2);
    bang('o nhap giu nguyen chuoi vua go, khong bi doi thanh so gia (' + xau + ')', inp2.value, xau);
    bang('BAN DUOC khong doi (' + xau + ')', soTheoNhan(m, 'BÁN ĐƯỢC'), '8');
    /* Sua lai thanh so dung thi luu duoc, dung o vua mo, khong phai mo lai. */
    inp2.value = '3';
    inp2.dispatchEvent(dg.suKien('change', {}, inp2));
    await choToi('luu_o bay di sau khi sua (' + xau + ')', function () { return m.goi.length > truoc; });
    bang('gui dung so da sua (' + xau + ')', m.goi[truoc].ts.gia_tri, 3);
  }
});


ca('go so huy hop le: rong la 0, 0 la 0, so nguyen gui dung so, va chu Enter cung nhu nut OK', async function () {
  var cacXau = [['', 0], ['0', 0], ['7', 7], [' 4 ', 4]];
  for (var i = 0; i < cacXau.length; i++) {
    var xau = cacXau[i][0], mong = cacXau[i][1];
    var m = await moMan({ bang: function () { return bangCua([dong({ ton_d1: 10, huy: 2 })]); } });
    oTheo(m, 'BAWC00055|huy').click();
    var inp = m.tai.getElementById('kb-inp');
    var truoc = m.goi.length;
    inp.value = xau;
    inp.dispatchEvent(dg.suKien('keydown', { key: 'Enter' }, inp));
    await choToi('luu_o bay di (' + JSON.stringify(xau) + ')', function () { return m.goi.length > truoc; });
    var g = m.goi[truoc];
    bang('dung cua', g.ten, 'kiem_banh.luu_o');
    bang('gui dung so (' + JSON.stringify(xau) + ')', g.ts.gia_tri, mong);
    bang('so nguyen kieu number, khong phai chuoi', typeof g.ts.gia_tri, 'number');
    bang('khong bao do', m.tai.getElementById('kb-bao').className === 'loi', false);
  }
});


ca('cot khac (san xuat) van doc theo cach cu, khong bi doi chinh sach lay', async function () {
  var m = await moMan({ bang: function () { return bangCua([dong({ ton_d1: 10 })]); } });
  var o = oTheo(m, 'BAWC00055|sx');
  dung('co o san xuat sua duoc', !!o);
  o.click();
  var inp = m.tai.getElementById('kb-inp');
  var truoc = m.goi.length;
  inp.value = '1.9';
  inp.dispatchEvent(dg.suKien('change', {}, inp));
  await choToi('luu_o bay di cho cot sx', function () { return m.goi.length > truoc; });
  bang('cot sx van parseInt nhu cu (1.9 -> 1)', m.goi[truoc].ts.gia_tri, 1);
  bang('dung truong', m.goi[truoc].ts.truong, 'sx');
});


/* ---------- chay ---------- */

async function chay() {
  console.log('Bo ca kiem HANH VI trang /kiem-banh (DOM gia)');
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
      if (e && e.stack && !e.message) console.log(e.stack);
    }
  }
  console.log('');
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + CA.length + ' ca.');
  process.exit(ket.hong ? 1 : 0);
}

chay();

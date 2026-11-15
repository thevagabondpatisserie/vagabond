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
  '<div id="kb-refill"></div>',
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
    /* v660: ca refill nhiều đợt cần bảng BTP và quyền bếp thật của trang. */
    if (ten === 'btp.quyen_btp' && canh.bep) return { ok: 1, than: { sua: 1 } };
    if (ten === 'btp.bang_btp' && canh.btp) return { ok: 1, than: canh.btp() };
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
    // Nhánh từ chối của luuO chạy đồng bộ trong change. Kiểm ngay trước
    // khi nhường event loop: toast tự xoá sau 4 giây, máy bị treo lịch có
    // thể làm năm nhịp ngủ vượt hạn dù app đã báo đúng lỗi.
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


/* ---------- nguon cua o ton (#216, v444) ---------- */

function nguonCua(m, id) {
  var o = oTheo(m, id);
  if (!o) throw new Error('Khong thay o ' + id);
  var n = o.querySelector('.kb-nguon');
  return n ? { chu: n.textContent.trim(), lop: n.className } : null;
}

ca('o ton bay NGUON: Tu chuyen, Da kiem dem kem so may va chenh lech, Can xac nhan; khong nguon thi khong bay gi', async function () {
  var d = dong({ ton_d1: 4, ton_d2: 7, ton_cu: 9 });
  d.nguon = {
    ton_d1: { trang_thai: 'Đã kiểm đếm', may_chuyen: 7, ai: 'loananh@vagabond', luc: '2026-09-07 06:10:00' },
    ton_d2: { trang_thai: 'Tự chuyển', may_chuyen: 7, ai: '', luc: '' },
    ton_cu: { trang_thai: 'Cần xác nhận', may_chuyen: 0, ai: '', luc: '' },
  };
  var d2 = dong({ ma_hang: 'BAWC00056', ton_d1: 3 });   /* ban ghi cu, khong co khoa nguon */
  var m = await moMan({ bang: function () { return bangCua([d, d2]); } });
  var a = nguonCua(m, 'BAWC00055|ton_d1');
  /* Gio dem bay THANG trong chu (Codex P2 vong 4): dien thoai khong co hover. */
  bang('dem tay 4, may 7: bay chenh lech -3, ten nguoi va GIO dem', a.chu, 'Đã kiểm đếm · máy 7 (-3) · loananh 07/09 06:10');
  dung('khong con giau gio trong title', !oTheo(m, 'BAWC00055|ton_d1').querySelector('.kb-nguon').getAttribute('title'));
  dung('to do khi lech', a.lop.indexOf('lech') >= 0);
  var b = nguonCua(m, 'BAWC00055|ton_d2');
  bang('may chuyen: chi nhan', b.chu, 'Tự chuyển');
  dung('khong to', b.lop.indexOf('lech') < 0 && b.lop.indexOf('xn') < 0);
  var c = nguonCua(m, 'BAWC00055|ton_cu');
  bang('can xac nhan kem so may', c.chu, 'Cần xác nhận · máy 0');
  dung('to cam', c.lop.indexOf('xn') >= 0);
  bang('dong khong co khoa nguon thi khong bay gi', nguonCua(m, 'BAWC00056|ton_d1'), null);
  bang('so tren o van la so nguoi dem', oTheo(m, 'BAWC00055|ton_d1').querySelector('b').textContent, '4');
});

ca('dem tay o ton khop so may thi khong bay chenh lech; bam o van mo duoc o nhap va luu_o gui dung truong', async function () {
  var d = dong({ ton_d1: 7 });
  d.nguon = { ton_d1: { trang_thai: 'Đã kiểm đếm', may_chuyen: 7, ai: '', luc: '' } };
  var m = await moMan({ bang: function () { return bangCua([d]); } });
  bang('khop thi chi nhan', nguonCua(m, 'BAWC00055|ton_d1').chu, 'Đã kiểm đếm');
  oTheo(m, 'BAWC00055|ton_d1').click();
  var inp = m.tai.getElementById('kb-inp');
  dung('mo o nhap', !!inp);
  inp.value = '5';
  var truoc = m.goi.length;
  m.tai.getElementById('kb-ok').click();
  await choToi('luu_o bay di', function () { return m.goi.length > truoc; });
  bang('dung truong', m.goi[truoc].ts.truong, 'ton_d1');
  bang('dung so', m.goi[truoc].ts.gia_tri, 5);
});

ca('nut xoa dong theo xoa_duoc cua may chu: dem ra 0 (moi so deu 0) thi KHONG co nut xoa; dong moi thi co', async function () {
  var d1 = dong({ ma_hang: 'BAWC00055' }); d1.xoa_duoc = 0;
  d1.nguon = { ton_d2: { trang_thai: 'Đã kiểm đếm', may_chuyen: 0, ai: 'de@vagabond', luc: '2026-09-07 06:10:00' } };
  var d2 = dong({ ma_hang: 'BAWC00056' }); d2.xoa_duoc = 1;
  var m = await moMan({ bang: function () { return bangCua([d1, d2]); } });
  var xoa = m.tai.querySelectorAll('[data-xoa]').map(function (e) { return e.getAttribute('data-xoa'); });
  bang('chi dong moi co nut xoa', JSON.stringify(xoa), JSON.stringify(['BAWC00056']));
  bang('dong dem 0 van bay nhan', nguonCua(m, 'BAWC00055|ton_d2').chu, 'Đã kiểm đếm · de 07/09 06:10');
});

ca('chu dong nguon toi thieu 13px trong CSS trang', async function () {
  var css = fs.readFileSync(path.join(TRANG, 'kiem-banh.html'), 'utf8');
  var mt = css.match(/\.kb-nguon\{[^}]*font-size:\s*([\d.]+)px/);
  dung('co luat font-size cho .kb-nguon', !!mt);
  dung('>= 13px, duoc ' + (mt && mt[1]), mt && parseFloat(mt[1]) >= 13);
});

/* ---------- v660: xem lại ngày cũ, bán sau chốt, refill nhiều đợt ---------- */

function isoLui(n) {
  var d = new Date(); d.setHours(0, 0, 0, 0); d.setDate(d.getDate() - n);
  return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
}

ca('v660 chip Hom qua dung truoc Hom nay; bam thi CHI DOC bang ngay do (khong keo Pancake), an nut Dong bo va Them ma; o Ngay khac mo duoc ngay trong 30 ngay', async function () {
  var m = await moMan({ bang: function () { return bangCua([dong({ ton_d1: 2 })]); } });
  var chips = m.tai.querySelectorAll('[data-ngay]');
  bang('chip dau la Hom qua', chips[0].textContent.indexOf('Hôm qua') === 0, true);
  bang('chip dau mang ngay hom qua', chips[0].getAttribute('data-ngay'), isoLui(1));
  bang('chip thu hai la Hom nay', chips[1].textContent.indexOf('Hôm nay') === 0, true);
  var truoc = m.goi.length;
  chips[0].click();
  await choToi('goi doc bang hom qua', function () { return m.goi.length > truoc; });
  bang('chi doc bang', m.goi[truoc].ten, 'kiem_banh.bang');
  bang('dung ngay hom qua', m.goi[truoc].ts.ngay, isoLui(1));
  dung('khong goi dong_bo cho ngay cu', m.goi.slice(truoc).every(function (g) { return g.ten !== 'kiem_banh.dong_bo'; }));
  var o = m.tai.getElementById('kb-ngay-khac');
  dung('co o Ngay khac', !!o);
  bang('lui xa nhat 30 ngay', o.getAttribute('min'), isoLui(30));
  bang('khong chon duoc tu hom nay tro di o day', o.getAttribute('max'), isoLui(1));
  truoc = m.goi.length;
  o.value = isoLui(9);
  o.dispatchEvent(dg.suKien('change', {}, o));
  await choToi('goi doc bang 9 ngay truoc', function () { return m.goi.length > truoc; });
  bang('doc dung ngay da chon', [m.goi[truoc].ten, m.goi[truoc].ts.ngay].join('|'), 'kiem_banh.bang|' + isoLui(9));
});

ca('v660 bang da chot: ghi gio chot, noi ro la so luc chot; dong co ban sau chot hien o Ban sau chot, dong khong co thi khong hien', async function () {
  var b = bangCua([dong({ ton_d1: 1, sx: 2, don_khac: 2, co_the_ban: 0, ban_sau_chot: 1 }),
    dong({ ma_hang: 'BAWC00056', ten_banh: 'Bánh hai', ton_d1: 3, co_the_ban: 3 })]);
  b.tinh_trang = 'Da chot'; b.chot_luc = '2026-11-14 20:25:14.419339';
  var m = await moMan({ bang: function () { return b; } });
  var chu = m.tai.getElementById('kb-dachot').textContent;
  dung('ghi gio chot 20:25', chu.indexOf('Đã chốt lúc 20:25') === 0);
  dung('noi ro so luc chot va ban sau chot', chu.indexOf('số lúc chốt') > 0 && chu.indexOf('Bán sau chốt') > 0);
  var o = m.tai.querySelectorAll('.kb-sau-chot');
  bang('chi mot dong co o Ban sau chot', o.length, 1);
  bang('so ban sau chot', o[0].querySelector('b').textContent, '1');
});

function btpHaiDot() {
  return { cap_nhat_luc: '', dat_xa: {}, refill_loi: '', dot_xong: [
    { ma_hang: 'BAWC00055', ten: 'Bánh thử', so: 12, tu: '2026-11-01', den: '2026-11-07', da_dat: 9, con: 3 }],
    lich_refill: [], dong: [{ ma_hang: 'BAWC00055', ten_banh: 'Bánh thử', so_btp: 0, so_decor: 0, dang_giu: 0, con_nhan: 0, giao_mai: 0, doi: {},
      refill: [{ id: 'd1', so: 20, tu: '2026-11-14', den: '2026-11-20', da_dat: 7, con: 13, mo_ta: 'có từ T7 14/11, nhận tới 20/11' },
        { id: 'd2', so: 15, tu: '2026-11-21', den: '2026-11-27', da_dat: 3, con: 12, mo_ta: 'có từ T7 21/11, nhận tới 27/11' }] }] };
}

ca('v660 refill nhieu dot: o Refill va Con nhan refill ghi tung dot; bam mo danh sach dot; Sua gui dung ma dot, Them dot gui ma dot trong; Dot da xong hien so lam, da nhan, con', async function () {
  var m = await moMan({ bang: function () { return bangCua([dong({ ton_d1: 2 })]); }, bep: true, btp: btpHaiDot });
  await choToi('o Refill co hai dot', function () {
    var o = m.tai.querySelector('[data-refill]');
    return o && o.textContent.indexOf('2 đợt') >= 0;
  });
  var o = m.tai.querySelector('[data-refill]');
  bang('so lon la tong hai dot', o.querySelector('b').textContent, '35');
  var con = m.tai.querySelectorAll('.kb-nh2').filter(function (e) { return e.querySelector('label').textContent === 'Còn nhận refill'; })[0];
  dung('con cua tung dot', con.textContent.indexOf('đợt 14/11: còn 13') >= 0 && con.textContent.indexOf('đợt 21/11: còn 12') >= 0);
  var xong = m.tai.getElementById('kb-refill').textContent;
  dung('Dot da xong ghi lam 12, da nhan 9, con 3', xong.indexOf('Đợt đã xong (1)') >= 0 && xong.indexOf('làm 12 · đã nhận 9 · còn 3') >= 0);
  o.click();
  var ds = m.tai.querySelectorAll('[data-suadot]');
  bang('tam liet ke hai dot', ds.length, 2);
  dung('moi dot ghi da nhan va con', m.tai.getElementById('kb-rf-lop').textContent.indexOf('20 bánh · đã nhận 7 · còn 13') >= 0);
  ds[1].click();
  bang('o ngay cua dot 2', m.tai.getElementById('kb-rf-tu').value + '|' + m.tai.getElementById('kb-rf-den').value, '2026-11-21|2026-11-27');
  m.tai.getElementById('kb-rf-so').value = '18';
  var truoc = m.goi.length;
  m.tai.getElementById('kb-rf-luu').click();
  await choToi('goi luu dot 2', function () { return m.goi.some(function (g, i) { return i >= truoc && g.ten === 'btp.luu_refill'; }); });
  var g = m.goi.filter(function (x, i) { return i >= truoc && x.ten === 'btp.luu_refill'; })[0];
  bang('sua dung dot 2', [g.ts.ma_hang, g.ts.dot, g.ts.so_refill, g.ts.refill_tu].join('|'), 'BAWC00055|d2|18|2026-11-21');
  await choToi('tam dong sau khi luu', function () { return !m.tai.getElementById('kb-rf-lop'); });
  m.tai.querySelector('[data-refill]').click();
  m.tai.getElementById('kb-rf-them').click();
  bang('dot moi goi y bat dau ngay sau dot cuoi', m.tai.getElementById('kb-rf-tu').value, '2026-11-28');
  dung('nhac cac dot dang co', m.tai.getElementById('kb-rf-lop').textContent.indexOf('Đợt mới không được trùng ngày') >= 0);
  m.tai.getElementById('kb-rf-so').value = '10';
  truoc = m.goi.length;
  m.tai.getElementById('kb-rf-luu').click();
  await choToi('goi luu dot moi', function () { return m.goi.some(function (g2, i) { return i >= truoc && g2.ten === 'btp.luu_refill'; }); });
  g = m.goi.filter(function (x, i) { return i >= truoc && x.ten === 'btp.luu_refill'; })[0];
  bang('them dot: ma dot trong', [g.ts.dot, g.ts.so_refill, g.ts.refill_tu, g.ts.refill_den].join('|'), '|10|2026-11-28|2026-12-04');
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

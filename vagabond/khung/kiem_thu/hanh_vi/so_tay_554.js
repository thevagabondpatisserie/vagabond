/* Bo ca kiem HANH VI cho man So tay va bo ve stMd (v554, 02/10/2026).
 *
 * Nap THAT ca tep 50-so-tay.js vao DOM gia, api gia tra ve so tay that doc
 * tu thu muc vagabond/so_tay qua dung phep tach cua may chu (chay python).
 * Moi ca bam dung chuoi thao tac cua nhan vien: mo man, bam chuong, bam muc,
 * go o tim. Khong goi them ham nao "cho chac" (CLAUDE.md, bai hoc 06/09).
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/so_tay_554.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var cp = require('child_process');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
var SRC = fs.readFileSync(path.join(BEP, '50-so-tay.js'), 'utf8');

/* So tay THAT, tach bang dung ham chuong_cho_man cua may chu. Lay phan
   thuan cua tro_ly_so_tay.py (truoc moc "phan can Frappe") nhu thu_tro_ly.py. */
function soTayThat() {
  var py = [
    'import io, json, os, sys',
    'goc = sys.argv[1]',
    'ma = io.open(os.path.join(goc, "vagabond", "tro_ly_so_tay.py"), encoding="utf-8").read()',
    'moc = "# ------------------------------------------------------- phan can Frappe"',
    'ns = {}',
    'exec(compile(ma.split(moc)[0], "tlst", "exec"), ns)',
    'td = os.path.join(goc, "vagabond", "so_tay")',
    'ra = [ns["chuong_cho_man"](io.open(os.path.join(td, f), encoding="utf-8").read(), f[:-3])',
    '      for f in sorted(os.listdir(td)) if f.endswith(".md") and not f.startswith("_")]',
    'sys.stdout.write(json.dumps({"chuong": ra}, ensure_ascii=False))',
  ].join('\n');
  return JSON.parse(cp.execFileSync('python3', ['-c', py, GOC], { encoding: 'utf8', maxBuffer: 1 << 26 }));
}
var SO_TAY = soTayThat();

function dungMan() {
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);
  var goi = [];
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, parseInt: parseInt,
    frame: function (t, html) { khung.innerHTML = html; that._t = t; return khung; },
    api: function (duong, ts) { goi.push(duong); return Promise.resolve(JSON.parse(JSON.stringify(SO_TAY))); },
    h: function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); },
    errMsg: function (e) { return String(e); },
  };
  that.globalThis = that;
  vm.runInNewContext(SRC, that, { filename: '50-so-tay.js' });
  return { g: that, tai: tai, khung: khung, goi: goi };
}

var ket = { dat: 0, hong: 0, loi: [] };
function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) { if (a !== b) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
function tick() { return new Promise(function (r) { setTimeout(r, 5); }); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; ket.loi.push(ten); console.log('  HONG  ' + ten + '\n        ' + e.message); }
}

function bam(m, el) { m.khung.onclick({ target: el }); }
function tim(m, chon) { return m.khung.querySelectorAll(chon); }

(async function () {
  console.log('So tay v554: bo ve va man hinh');

  await ca('stMd THOAT ky tu truoc: HTML trong cau tra loi khong thanh the that', async function () {
    var m = dungMan();
    var o = m.g.stMd('<img src=x onerror=alert(1)> Bấm [[Lưu <b>x</b>]] **đậm**');
    dung('khong con the img', o.indexOf('<img') < 0);
    dung('the img thanh chu', o.indexOf('&lt;img') >= 0);
    dung('chu trong nut cung bi thoat', o.indexOf('Lưu &lt;b&gt;x&lt;/b&gt;') >= 0);
    dung('chu dam van ve', o.indexOf('<b>đậm</b>') >= 0);
  });

  await ca('[[...]] ve thanh nut app, [[desk:...]] thanh nut Desk, ca hai co mui ten chi vao', async function () {
    var m = dungMan();
    var o = m.g.stMd('Bấm [[Xác nhận nhập kho]] rồi [[desk:Lưu]]');
    dung('nut app', o.indexOf('<span class="stNut">Xác nhận nhập kho</span>') >= 0);
    dung('nut desk', o.indexOf('<span class="stNut stDesk">Lưu</span>') >= 0);
    bang('hai mui ten', (o.match(/class="stTro"/g) || []).length, 2);
    dung('mui ten dung NGAY truoc nut', /<\/svg><span class="stNut">Xác nhận/.test(o));
    dung('khong con ky hieu tho', o.indexOf('[[') < 0);
  });

  await ca('bang markdown thanh bang that, bo dong gach phan cach', async function () {
    var m = dungMan();
    var o = m.g.stMd('| Nợ | Có |\n|---|---|\n| 152 | 3311 |');
    dung('co bang', o.indexOf('<table>') >= 0);
    dung('dong dau la th', o.indexOf('<th>Nợ</th><th>Có</th>') >= 0);
    dung('dong so lieu', o.indexOf('<td>152</td><td>3311</td>') >= 0);
    dung('khong ve dong gach', o.indexOf('---') < 0);
  });

  await ca('cac buoc danh so thanh danh sach so, tieu de khoi thanh dong tieu de', async function () {
    var m = dungMan();
    var o = m.g.stMd('**Các bước**\n1. Mở màn\n2. Bấm [[Lưu]]\n- Lưu ý một');
    dung('tieu de khoi', o.indexOf('<div class="stH">Các bước</div>') >= 0);
    bang('hai buoc', (o.match(/<li>/g) || []).length, 3);
    dung('co ol', o.indexOf('<ol>') >= 0 && o.indexOf('<ul>') >= 0);
  });

  await ca('lien ket CHI nhan dia chi noi bo dang /chu-thuong', async function () {
    var m = dungMan();
    var o = m.g.stMd('Màn Nhập kho (/nhap-kho), ngoài (http://x.com), lạ (/../etc)');
    dung('noi bo thanh lien ket', o.indexOf('<a class="stLk" href="/nhap-kho">') >= 0);
    bang('chi mot lien ket', (o.match(/<a /g) || []).length, 1);
  });

  await ca('dau CHUA XAC MINH thanh o canh bao mau, nguoi doc thay', async function () {
    var m = dungMan();
    var o = m.g.stMd('Bước 2 [CHƯA XÁC MINH: nhãn nút chưa thử]');
    dung('o canh bao', o.indexOf('<span class="stCxm">Chưa xác minh: nhãn nút chưa thử</span>') >= 0);
  });

  /* Codex #412 F2: moi phan bep/ ghep chung MOT pham vi. Ca nay nap hai
     dong THAT cua 00-nen.js (the <style> `st` va keepCss) cung pham vi voi
     toan tep 50-so-tay.js, dung nhu app_bep.js, roi goi keepCss. Ca nap
     rieng 50-so-tay khong the bat dung ten voi nen. */
  await ca('cung pham vi voi nen: nap So tay xong keepCss cua nen van chay', async function () {
    var NEN = fs.readFileSync(path.join(BEP, '00-nen.js'), 'utf8');
    function dong(dau) { var i = NEN.indexOf(dau); if (i < 0) throw new Error('khong thay ' + dau); return NEN.slice(i, NEN.indexOf('\n', i)); }
    var tai = dg.taiLieuGia();
    var dau = { children: [], lastElementChild: null, appendChild: function (x) {
      if (!x || typeof x.nodeType !== 'number') throw new Error("appendChild: parameter 1 is not of type 'Node'");
      this.children.push(x); x.parentNode = this; this.lastElementChild = x; return x; } };
    tai.head = dau;
    var goc = tai.createElement;
    tai.createElement = function (t) { var e = goc ? goc.call(tai, t) : new dg.ElementGia(t); e.nodeType = 1; return e; };
    var that = { document: tai, CSS: '', h: function (x) { return String(x); }, console: console };
    that.globalThis = that;
    var ma = dong('var st = document.createElement') + '\n' + dong('function keepCss()') + '\n' + SRC +
      '\nkeepCss(); __ok = 1;';
    vm.runInNewContext(ma, that, { filename: 'nen+so-tay' });
    bang('keepCss chay xong', that.__ok, 1);
  });

  await ca('mo man: luoi chuong cua so tay that, moi chuong mot o', async function () {
    var m = dungMan();
    await m.g.scrSoTay(); await tick();
    bang('tieu de man', m.g._t, 'Sổ tay');
    bang('goi dung mot cua', m.goi.join(','), 'vagabond.tro_ly_so_tay.doc_so_tay');
    bang('so o chuong', tim(m, '.stO').length, SO_TAY.chuong.length);
    dung('it nhat 6 chuong', SO_TAY.chuong.length >= 6);
  });

  await ca('bam chuong roi bam muc: muc mo ra co nut ve that va nut mo man', async function () {
    var m = dungMan();
    await m.g.scrSoTay(); await tick();
    var kho = tim(m, '.stO').filter(function (x) { return x.dataset.stc === 'kho'; })[0];
    dung('co o Kho', !!kho);
    bam(m, kho);
    var muc = tim(m, '[data-stk]');
    bang('so muc chuong kho', muc.length, SO_TAY.chuong.filter(function (c) { return c.ma === 'kho'; })[0].muc.length);
    /* Bam muc DAU TIEN co man rieng trong app (muc lam tren Desk thi khong
       co nut Mo man nay, dung y). */
    var mk = SO_TAY.chuong.filter(function (c) { return c.ma === 'kho'; })[0].muc;
    var j = 0;
    while (j < mk.length && !mk[j].duong) j++;
    dung('chuong kho co muc co man rieng', j < mk.length);
    bam(m, muc[j]);
    /* Doc tren cay DOM, khong doc khung.innerHTML: man chi ve lai khoi
       #stDs, nen chuoi HTML cua khung la ban cu tu lan ve ca man. */
    bang('mot muc dang mo', tim(m, '.stMucT').length, 1);
    dung('co nut ve', tim(m, '.stNut').length > 0);
    dung('co bang tom tat', tim(m, 'table').length > 0);
    bang('co nut Mo man nay', tim(m, '.stMo').length, 1);
    bam(m, tim(m, '[data-stk]')[j]);
    bang('bam lan nua thi dong', tim(m, '.stMucT').length, 0);
  });

  await ca('go o tim KHONG DAU van ra muc dung, cau that "mat khau"', async function () {
    var m = dungMan();
    await m.g.scrSoTay(); await tick();
    var o = m.tai.getElementById('stTim');
    o.value = 'quen mat khau';
    o.dispatchEvent(dg.suKien('input'));
    dung('co ket qua tren man', tim(m, '.stMucD').length > 0);
    /* Thu tu xep do chinh ham loc cua man quyet dinh; doc ten muc dau tu do,
       cung du lieu, khong tu xep lai o day. */
    var dau = m.g.stLoc(m.g.stS.d, 'quen mat khau')[0].m.ten;
    dung('muc dau ve mat khau: ' + dau, /mật khẩu/i.test(dau));
    bang('man hien dung so ket qua', tim(m, '.stMucD').length, Math.min(40, m.g.stLoc(m.g.stS.d, 'quen mat khau').length));
    /* Ve lai ca man thi o tim moi thay o cu, tren may that la mat con tro
       dang go. Kiem bang DUNG doi tuong o, khong chi kiem co o. */
    dung('van la dung o dang go (khong ve lai ca man)', m.tai.getElementById('stTim') === o);
  });

  console.log('\n' + ket.dat + ' ca dat, ' + ket.hong + ' ca hong.');
  process.exit(ket.hong ? 1 : 0);
})();

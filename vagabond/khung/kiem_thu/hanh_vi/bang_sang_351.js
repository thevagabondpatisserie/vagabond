/* Bo ca kiem HANH VI cho man Viec hom nay (Bang sang), issue #351 dot 1.
 *
 * Nap THAT ca tep 47-bang-sang.js, hopKhung that tu 07-hop-thoai.js va the
 * Nhan dinh that tu 14-bao-cao.js vao DOM gia, api gia. Moi ca bam dung chuoi
 * thao tac cua nguoi quan ly, khong goi them ham nao "cho chac" (bai hoc
 * 06/09, CLAUDE.md muc "Ca kiem co the tu che mat loi").
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/bang_sang_351.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
var SRC = fs.readFileSync(path.join(BEP, '47-bang-sang.js'), 'utf8');
var HOP = fs.readFileSync(path.join(BEP, '07-hop-thoai.js'), 'utf8');
var BC = fs.readFileSync(path.join(BEP, '14-bao-cao.js'), 'utf8');
var NEN = fs.readFileSync(path.join(BEP, '00-nen.js'), 'utf8');

function layHam(src, ten) {
  var dau = src.indexOf('function ' + ten + '(');
  if (dau < 0) throw new Error('Khong thay ham ' + ten);
  if (src.slice(Math.max(0, dau - 6), dau) === 'async ') dau -= 6;
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Ham ' + ten + ' khong dong ngoac');
}

function nd(i, luat, muc, bp, them) {
  var x = {
    khoa: luat + '|M' + i + '|tat_ca', luat: luat, muc: muc, bo_phan: bp, han: 3, bo_qua_toi_da: luat === 'lo_qua_han' ? 3 : 14,
    tieu_de: 'Nhận định ' + i, cau: 'Câu số ' + i, goi_y: 'Gợi ý ' + i,
    doi: { loai: luat.indexOf('lo_') === 0 ? 'kho' : 'mon', ma: 'M' + i, ten: 'Món ' + i, anh: i === 1 ? '/files/m1.jpg' : '' },
    so_lieu: luat === 'mon_tang' ? { chuoi: [10, 20, 40], nhan: ['a', 'b', 'c'] } : {}
  };
  return Object.assign(x, them || {});
}

function duLieu(tab) {
  var ds;
  if (tab === 'da_giao' || tab === 'tre') {
    ds = [
      { name: 'TASK-1', tieu_de: 'Croissant đang lên', luat: 'mon_tang', bo_phan: ['marketing'], tt: 'tre', han: '2026-09-19', nguoi: ['Vũ'], anh: '' },
      { name: 'TASK-2', tieu_de: '2 lô quá hạn', luat: 'lo_qua_han', bo_phan: ['kho'], tt: 'mo', han: '2026-09-21', nguoi: ['Khải'], anh: '' },
    ];
  } else {
    ds = [
      nd(1, 'lo_qua_han', 'cao', ['kho'], { so_lieu: { lo: [{ lo: 'L1', ma: 'NVLT1', ten: 'Bơ', han: '2024-01-21', sl: 2000, dvt: 'Gram' }, { lo: 'L2', ten: 'Kem', han: '2026-09-19', sl: 3 }, { lo: 'L3', ten: 'Sữa', han: '2026-09-18', sl: 1 }, { lo: 'L4', ten: 'Đường', han: '2026-09-17', sl: 1 }] } }),
      nd(2, 'mon_tang', 'vua', ['marketing']),
      nd(3, 'mon_giam', 'vua', ['marketing', 'bep']),
      nd(4, 'mon_tang', 'vua', ['marketing']),
      nd(5, 'mon_moi', 'thap', ['marketing']),
    ];
  }
  return {
    dang_dung: 0, chot_luc: '2026-09-21 07:00:02', den_ngay: '2026-09-20', tab: tab || 'can_giao', bo_phan: '',
    dem: { can_giao: 5, da_giao: 2, xong: 0, bo_qua: 0 }, so_tre: 1, ky: '',
    chip_ky: [{ k: '', ten: 'Tất cả' }, { k: 'hom_nay', ten: 'Hôm nay' }, { k: '7', ten: '7 ngày' }, { k: '30', ten: '30 ngày' }],
    chip_bo_phan: [{ k: 'marketing', ten: 'Marketing', ic: '📣', so: 4 }, { k: 'kho', ten: 'Kho', ic: '📦', so: 1 }],
    ds: ds,
    chat_luong: [{ ma: 'nhap', cau: '100 trên 320 đơn tuần qua chưa ghi sổ; số bán đang là số tạm tính.' }, { ma: 'kiem_banh', cau: 'Chưa có bảng kiểm bánh.' }],
    ten_bo_phan: { marketing: 'Marketing', kho: 'Kho', bep: 'Bếp' },
  };
}

function dungMan(canh) {
  canh = canh || {};
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);
  var goi = [];
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, Date: Date, String: String, Number: Number,
    Array: Array, Object: Object, RegExp: RegExp, Promise: Promise, setTimeout: setTimeout, clearTimeout: clearTimeout, setInterval: setInterval, clearInterval: clearInterval,
    S: { quyenNen: { bang_sang: true } },
    /* Chan man (footer) cung ve vao khung, dung nhu frame that dat no trong
       cay DOM, de getElementById tim duoc nut o chan man. */
    frame: function (t, html, opt) { khung.innerHTML = html + ((opt && opt.footer) || ''); that._frame = { t: t, opt: opt || {} }; return khung; },
    go: function (fn) { return fn(); },
    vgbCss: function () {},
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: JSON.parse(JSON.stringify(ts || {})) });
      if (duong === 'vagabond.phan_tich.bang_sang') {
        if (canh.hongBang) return Promise.reject(new Error('Mất mạng, thử lại'));
        var d = duLieu(ts.tab);
        d.dem.tre = d.so_tre;
        d.tong_loc = d.ds.length; d.dang_loc = 0;
        /* Nhu may chu that: loc bo phan thi dem va ds cung loc, so_tre cu giu
           so toan bo de ca kiem thay man doc dung dem da loc. */
        if (ts.bo_phan) {
          d.ds = d.ds.filter(function (x) { return (x.bo_phan || []).indexOf(ts.bo_phan) >= 0; });
          d.bo_phan = ts.bo_phan; d.dang_loc = 1; d.tong_loc = d.ds.length;
          d.dem = { can_giao: 0, da_giao: d.ds.length, tre: d.ds.filter(function (x) { return x.tt === 'tre'; }).length, xong: 0, bo_qua: 0 };
        }
        if (ts.ky && ts.tab !== 'can_giao') { d.ky = ts.ky; d.dang_loc = 1; }
        if (canh.dangDung) { d.dang_dung = 1; d.ds = []; d.chot_luc = ''; }
        return Promise.resolve(d);
      }
      if (duong === 'vagabond.phan_tich.nguoi_de_giao') {
        var ng = canh.khongGoiY ? [] : [{ email: 'vu@vgb', ten: 'Minh Vũ', anh: '', goi_y: 1 }];
        return Promise.resolve({ han_goi_y: 3, tieu_de: 'x', nguoi: ng.concat([{ email: 'khai@vgb', ten: 'Khải', anh: '', goi_y: 0 }]) });
      }
      if (duong === 'vagabond.phan_tich.giao') return Promise.resolve({ ok: 1, name: 'TASK-9', han: ts.han });
      if (duong === 'vagabond.phan_tich.bo_qua') return Promise.resolve({ ok: 1, nhac_lai: '2026-09-24', so_ngay: ts.so_ngay });
      if (duong === 'vagabond.phan_tich.viec') {
        return Promise.resolve({ name: ts.name, tieu_de: 'Croissant đang lên', luat: 'mon_tang', tt: 'mo', han: '2026-09-23', nguoi: ['Vũ'], anh: '',
          cau: 'Tuần qua bán 105', so_lieu: { chuoi: [60, 70, 105], nhan: ['a', 'b', 'c'] }, goi_y: 'Đẩy story', ghi_chu_giao: '', nguoi_nhan: ['Vũ'],
          giao_boi: 'Việt', giao_luc: '2026-09-21 08:00:00', den_ngay: '2026-09-20', sua_duoc: 1, quyen: 'nhan' });
      }
      if (duong === 'vagabond.phan_tich.cap_nhat_viec') return Promise.resolve({ ok: 1 });
      return Promise.resolve({});
    },
    h: function (s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); },
    num: function (n) { var v = Math.round((n || 0) * 1000) / 1000; return v.toLocaleString('vi-VN'); }, money: function (n) { return String(n); },
    anhMon: function (u) { return u ? '<img class="imm" src="' + u + '">' : '<div class="imm immp">🍰</div>'; },
    busy: function () {}, toast: function (m) { (that._toast = that._toast || []).push(String(m)); }, errMsg: function (e) { return e && e.message ? e.message : String(e); },
    sheet: function (t, items, cur, onPick) { that._sheet = { t: t, items: items, onPick: onPick }; },
    confirmSheet: function () { return Promise.resolve(true); },
    hoiChu: function () { return Promise.resolve(canh.ketQua === undefined ? 'Đã đăng 2 story' : canh.ketQua); },
    vgbOTim: function () { return ''; }, vgbNoiOTim: function () {},
    scrBangSang: null,
  };
  that.globalThis = that;
  vm.runInNewContext(SRC + '\n' + layHam(HOP, 'hopKhung') + '\n' + layHam(BC, 'bcTheNhanDinh') + '\n' + layHam(NEN, 'kl'), that, { filename: '47-bang-sang.js' });
  return { g: that, tai: tai, khung: khung, goi: goi };
}

var ket = { dat: 0, hong: 0, loi: [] };
function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) { if (a !== b) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
function tick() { return new Promise(function (r) { setTimeout(r, 5); }); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; }
  catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n         ') : String(e))); }
}
function bam(el) { el.dispatchEvent(dg.suKien('click', {}, el)); }
function tim(goc, chon, giaTri, thuocTinh) {
  return goc.querySelectorAll(chon).filter(function (c) { return giaTri === undefined || c.getAttribute(thuocTinh) === giaTri; })[0];
}
function tam(m) { var t = m.tai.body.children[m.tai.body.children.length - 1]; return t; }
function cong(n) {
  var d = new Date(); d.setDate(d.getDate() + n);
  return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
}

async function chayHet() {
  await ca('mo man: ba the uu tien co nut Giao, phan con lai thu gon, luu y so lieu thu ve mot dong dem so', async function () {
    var m = dungMan();
    await m.g.scrBangSang(); await tick();
    bang('goi bang_sang tab can_giao', m.goi[0].ts.tab, 'can_giao');
    var html = m.khung.innerHTML;
    bang('ba nut Giao viec', m.khung.querySelectorAll('[data-bsg]').length, 3);
    bang('ba nut Bo qua', m.khung.querySelectorAll('[data-bsbq]').length, 3);
    bang('hai dong gon', m.khung.querySelectorAll('[data-bsmo]').length, 2);
    dung('tieu de nhom con lai co dem so', html.indexOf('Còn 2 nhận định') >= 0);
    dung('muc cao la chip do Lam ngay', html.indexOf('st r" style="margin-right:4px">Làm ngay') >= 0);
    /* Codex #353 vong 3: truoc day ca nay CHOT la khong in lo thu 4 ('Đường' < 0).
       Chinh dieu do la loi: nguoi nhan khong co cach nao xem lo bi an. Nay lo
       thu 4 nam trong <details> thu gon, mo ra duoc. Dung sua ve nhu cu. */
    dung('lo: ba dong, phan con lai nam trong khoi mo ra duoc', html.indexOf('Xem thêm 1 lô nữa') >= 0 && html.indexOf('Đường') > html.indexOf('<details'));
    dung('so con kem don vi, gram lon doi ra kg', html.indexOf('còn 2 kg') >= 0);
    dung('han lo nam cu ghi ca nam', html.indexOf('Hạn 21/01/2024') >= 0);
    dung('cot ba tuan cho mon tang', html.indexOf('>40</div>') >= 0);
    dung('luu y so lieu thu gon: dem so, chua in cau', html.indexOf('<b>2</b> lưu ý về số liệu') >= 0 && html.indexOf('100 trên 320') < 0);
    dung('luu y nam SAU cac the (dieu 17)', html.indexOf('lưu ý về số liệu') > html.lastIndexOf('data-bsg='));
    dung('dau man: so tre to do', html.indexOf('color:#c93a3a">1</div>') >= 0);
    dung('gio chot', html.indexOf('chốt lúc 07:00') >= 0);
    dung('nut tinh lai tren thanh tieu de', !!m.g._frame.opt.onAction);
  });
  await ca('Codex #353 F5: phan lo con lai dem theo so_lo that, khong theo 12 lo may chu gui', async function () {
    var m = dungMan();
    var lo = [];
    for (var i = 0; i < 12; i++) lo.push({ lo: 'L' + i, ten: 'Món ' + i, han: '2026-09-01', sl: 1 });
    var html = m.g.bsLo({ luat: 'lo_qua_han', so_lieu: { so_lo: 20, lo: lo } });
    dung('ba dong roi con 17', html.indexOf('Xem thêm 17 lô nữa') >= 0);
    dung('du 12 lo may chu gui deu co trong the', lo.every(function (l) { return html.indexOf('>' + l.lo + '<') >= 0; }));
    dung('noi ro may chi gui 12 trong 20 va cho xem du', html.indexOf('Máy chỉ gửi 12 lô đầu trong 20 lô') >= 0);
  });
  await ca('bam dong gon: mo the day du ngay tai cho, dong gon con lai giu nguyen', async function () {
    var m = dungMan();
    await m.g.scrBangSang(); await tick();
    bam(tim(m.khung, '[data-bsmo]', 'mon_tang|M4|tat_ca', 'data-bsmo')); await tick(); await tick();
    bang('bon nut Giao', m.khung.querySelectorAll('[data-bsg]').length, 4);
    bang('con mot dong gon', m.khung.querySelectorAll('[data-bsmo]').length, 1);
  });
  await ca('bam luu y: mo ra du cau', async function () {
    var m = dungMan();
    await m.g.scrBangSang(); await tick();
    bam(m.khung.querySelector('[data-bsly]')); await tick(); await tick();
    dung('in cau luu y', m.khung.innerHTML.indexOf('100 trên 320') >= 0);
  });
  await ca('bam chip Da giao: goi lai may chu voi tab da_giao, dong tre co chip do', async function () {
    var m = dungMan();
    await m.g.scrBangSang(); await tick();
    bam(m.khung.querySelectorAll('[data-bst]').filter(function (c) { return c.getAttribute('data-bst') === 'da_giao' && /chip/.test(c.getAttribute('class') || ''); })[0]); await tick(); await tick();
    var cuoi = m.goi[m.goi.length - 1];
    bang('tab gui len', cuoi.ts.tab, 'da_giao');
    var html = m.khung.innerHTML;
    dung('chip Da giao dang on', html.indexOf('chip on" data-bst="da_giao"') >= 0);
    dung('dong tre co chip Tre han', html.indexOf('st r">Trễ hạn') >= 0);
    dung('dong co nguoi va han', html.indexOf('Vũ · hạn 19/09') >= 0);
  });
  await ca('Giao viec: dung khoa, nguoi goi y chon san, doi han 1 tuan, gui dung tham so roi tai lai', async function () {
    var m = dungMan();
    await m.g.scrBangSang(); await tick();
    bam(tim(m.khung, '[data-bsg]', '1', 'data-bsg')); await tick(); await tick();
    var g = m.goi[m.goi.length - 1];
    bang('hoi nguoi cua dung nhan dinh', g.ts.khoa, 'mon_tang|M2|tat_ca');
    var t = tam(m);
    var th = t.querySelector('#bsgThan');
    dung('nguoi goi y da chon san', th.innerHTML.indexOf('chip on" data-bsgn="vu@vgb"') >= 0);
    dung('han mac dinh 3 ngay', th.innerHTML.indexOf('chip on" data-bsgh="3"') >= 0);
    bang('nut noi so nguoi', t.querySelector('[data-bsgok]').textContent, 'Giao cho 1 người');
    bam(tim(t, '[data-bsgh]', '7', 'data-bsgh')); await tick();
    bam(t.querySelector('[data-bsgok]')); await tick(); await tick();
    var gi = m.goi.filter(function (x) { return x.duong === 'vagabond.phan_tich.giao'; })[0];
    dung('co goi giao', !!gi);
    bang('khoa', gi.ts.khoa, 'mon_tang|M2|tat_ca');
    bang('nguoi', gi.ts.nguoi, '["vu@vgb"]');
    bang('han 7 ngay', gi.ts.han, cong(7));
    bang('tai lai bang sau khi giao', m.goi[m.goi.length - 1].duong, 'vagabond.phan_tich.bang_sang');
    dung('bao da giao', (m.g._toast || []).some(function (s) { return s.indexOf('Đã giao cho Minh Vũ') === 0; }));
  });
  await ca('Giao viec khi may khong goi y ai: nut khoa, bam khong goi may chu; tim nguoi khac roi moi giao', async function () {
    var m = dungMan({ khongGoiY: true });
    await m.g.scrBangSang(); await tick();
    bam(tim(m.khung, '[data-bsg]', '0', 'data-bsg')); await tick(); await tick();
    var t = tam(m);
    bang('nut noi chua chon', t.querySelector('[data-bsgok]').textContent, 'Chọn người nhận');
    bam(t.querySelector('[data-bsgok]')); await tick();
    bang('khong goi giao', m.goi.filter(function (x) { return x.duong === 'vagabond.phan_tich.giao'; }).length, 0);
    bam(t.querySelector('[data-bsgtim]')); await tick();
    dung('mo sheet tim nguoi', m.g._sheet && m.g._sheet.items.length === 1);
    m.g._sheet.onPick(m.g._sheet.items[0]); await tick();
    dung('nguoi vua chon hien thanh chip', t.querySelector('#bsgThan').innerHTML.indexOf('chip on" data-bsgn="khai@vgb"') >= 0);
    bam(t.querySelector('[data-bsgok]')); await tick(); await tick();
    var gi = m.goi.filter(function (x) { return x.duong === 'vagabond.phan_tich.giao'; })[0];
    bang('giao cho Khai', gi && gi.ts.nguoi, '["khai@vgb"]');
  });
  await ca('Bo qua lo qua han: chi hien lua chon toi 3 ngay, phai chon ly do va ngay moi gui', async function () {
    var m = dungMan();
    await m.g.scrBangSang(); await tick();
    bam(tim(m.khung, '[data-bsbq]', '0', 'data-bsbq')); await tick();
    var t = tam(m);
    dung('co 1 va 3 ngay', !!tim(t, '[data-bsqn]', '1', 'data-bsqn') && !!tim(t, '[data-bsqn]', '3', 'data-bsqn'));
    dung('khong co 1 tuan', !tim(t, '[data-bsqn]', '7', 'data-bsqn'));
    bam(tim(t, '[data-bsql]', 'so_sai', 'data-bsql')); await tick();
    bam(t.querySelector('[data-bsqok]')); await tick();
    bang('chua chon ngay: khong gui', m.goi.filter(function (x) { return x.duong === 'vagabond.phan_tich.bo_qua'; }).length, 0);
    bam(tim(t, '[data-bsqn]', '3', 'data-bsqn')); await tick();
    bam(t.querySelector('[data-bsqok]')); await tick(); await tick();
    var bq = m.goi.filter(function (x) { return x.duong === 'vagabond.phan_tich.bo_qua'; })[0];
    dung('gui bo qua', !!bq);
    bang('ly do', bq.ts.ly_do, 'so_sai');
    bang('so ngay', bq.ts.so_ngay, 3);
    bang('khoa', bq.ts.khoa, 'lo_qua_han|M1|tat_ca');
  });
  await ca('tai hong: cau loi nguoi doc hieu va nut Tai lai', async function () {
    var m = dungMan({ hongBang: true });
    await m.g.scrBangSang(); await tick();
    var html = m.khung.innerHTML;
    dung('cau loi', html.indexOf('Mất mạng, thử lại') >= 0);
    dung('nut tai lai', !!m.khung.querySelector('#bsThuLai'));
  });
  await ca('bang dang dung: noi ro, co nut Tai lai, khong noi "khong co viec"', async function () {
    var m = dungMan({ dangDung: true });
    await m.g.scrBangSang(); await tick();
    var html = m.khung.innerHTML;
    dung('noi dang dung', html.indexOf('Đang dựng bảng hôm nay') >= 0 && html.indexOf('chưa dựng xong') >= 0);
    dung('nut tai lai', !!m.khung.querySelector('#bsTaiLai'));
    dung('khong noi khong co viec', html.indexOf('chưa có việc nào cần giao') < 0);
  });
  await ca('man viec duoc giao: Bao da xong goi may chu kem ket qua; bam Thoi thi khong goi', async function () {
    var m = dungMan();
    await m.g.scrViecGoiY('TASK-1'); await tick();
    dung('trang thai Cho lam', m.khung.innerHTML.indexOf('st w">Chờ làm') >= 0);
    dung('cot ba tuan', m.khung.innerHTML.indexOf('>105</div>') >= 0);
    bam(m.tai.getElementById('bsvXong')); await tick(); await tick();
    var c = m.goi.filter(function (x) { return x.duong === 'vagabond.phan_tich.cap_nhat_viec'; })[0];
    dung('co goi cap nhat', !!c);
    bang('trang thai xong', c.ts.trang_thai, 'xong');
    bang('ket qua', c.ts.ket_qua, 'Đã đăng 2 story');
    var m2 = dungMan({ ketQua: null });
    await m2.g.scrViecGoiY('TASK-1'); await tick();
    bam(m2.tai.getElementById('bsvXong')); await tick(); await tick();
    bang('thoi thi khong goi', m2.goi.filter(function (x) { return x.duong === 'vagabond.phan_tich.cap_nhat_viec'; }).length, 0);
  });
  await ca('the Nhan dinh BC08: mon tang xanh, mon giam do kem chu can kiem tra, lien ket chi khi co quyen', async function () {
    var m = dungMan();
    var html = m.g.bcTheNhanDinh({ so_voi: 'Tuần 07/09', tang: [{ ma: 'A', ten: 'Croissant', anh: '', nay: 60, truoc: 30, pt: 100 }],
      giam: [{ ma: 'B', ten: 'Slice', anh: '', nay: 10, truoc: 30, pt: -67 }], so_tang: 3, so_giam: 1, moi: 1, mo_bang_sang: 1 });
    dung('tang xanh', html.indexOf('st g">+100%') >= 0);
    dung('giam do, can kiem tra', html.indexOf('st r">-67%') >= 0 && html.indexOf('cần kiểm tra') >= 0);
    dung('dem phan con lai', html.indexOf('Còn 2 món tăng, 1 món mới bán.') >= 0);
    dung('co lien ket Viec hom nay', html.indexOf('data-bcbs') >= 0);
    var html2 = m.g.bcTheNhanDinh({ so_voi: 'x', tang: [], giam: [], so_tang: 0, so_giam: 0, moi: 2, mo_bang_sang: 0 });
    dung('khong quyen thi khong co lien ket', html2.indexOf('data-bcbs') < 0);
  });
  await ca('Codex #356 N4: form Task Desk co nut Bo qua cho quan ly, chon ly do theo ten, gui ma ly do', async function () {
    var TASK = fs.readFileSync(path.join(GOC, 'vagabond', 'public', 'js', 'task_bang_sang.js'), 'utf8');
    function chay(quyen, doc) {
      var goi = [], hop = null, nut = null, reload = 0;
      var frappe = {
        ui: { form: { on: function (dt, hh) { frappe._h = hh; } },
          Dialog: function (o) { hop = o; this.show = function () {}; this.hide = function () {}; } },
        show_alert: function () {}, msgprint: function (m) { goi.push('msg:' + m); },
        call: function (o) {
          goi.push(o.method); goi.args = o.args;
          if (o.method === 'vagabond.phan_tich.viec') return o.callback({ message: { quyen: quyen, bo_qua_toi_da: 3,
            ly_do_bo_qua: [{ k: 'dang_xu_ly', ten: 'Đã biết, đang xử lý' }, { k: 'so_sai', ten: 'Số liệu chưa đúng' }] } });
          return o.callback({ message: { ok: 1 } });
        }
      };
      vm.runInNewContext(TASK, { frappe: frappe, parseInt: parseInt, Number: Number });
      var frm = { doc: doc, is_new: function () { return false; }, add_custom_button: function (t, f) { nut = { t: t, f: f }; }, reload_doc: function () { reload++; } };
      frappe._h.refresh(frm);
      return { goi: goi, nut: nut, hop: function () { return hop; }, reload: function () { return reload; } };
    }
    var ng = chay('nhan', { name: 'T1', status: 'Open', vgb_goi_y_khoa: 'k' });
    dung('nguoi nhan khong co nut', !ng.nut);
    var ngoai = chay('quan_ly', { name: 'T2', status: 'Open' });
    dung('Task khong phai bang sang: khong goi may, khong nut', !ngoai.nut && ngoai.goi.length === 0);
    var ql = chay('quan_ly', { name: 'T3', status: 'Open', vgb_goi_y_khoa: 'k' });
    bang('quan ly co nut', ql.nut && ql.nut.t, 'Bỏ qua việc này');
    ql.nut.f();
    var o = ql.hop().fields;
    dung('ly do la danh sach chon, lay tu may chu', o[0].fieldtype === 'Select' && o[0].options.indexOf('Số liệu chưa đúng') >= 0);
    dung('so ngay khong vuot tran luat (3)', o[1].options.split('\n').join(',') === '1 ngày,3 ngày');
    ql.hop().primary_action({ ly_do: 'Số liệu chưa đúng', so_ngay: '3 ngày' });
    bang('goi bo_qua_viec', ql.goi[ql.goi.length - 1], 'vagabond.phan_tich.bo_qua_viec');
    bang('gui MA ly do, khong gui chu', ql.goi.args.ly_do, 'so_sai');
    bang('gui so ngay', ql.goi.args.so_ngay, 3);
    bang('tai lai form', ql.reload(), 1);
  });
  await ca('Codex #356 P3: tab Can giao cung co o tim, loc ca the lan dong gon', async function () {
    var m = dungMan();
    await m.g.scrBangSang(); await tick();
    var tim = m.khung.querySelector('#bsTim');
    dung('co o tim o Can giao', !!tim);
    tim.value = 'mon 5';
    tim.dispatchEvent(dg.suKien('input', {}, tim));
    var the = m.khung.querySelectorAll('[data-bsthe]'), gon = m.khung.querySelectorAll('[data-bsi]');
    dung('the dau an', the.every(function (e) { return e.style.display === 'none'; }));
    bang('dong gon mon 5 hien', gon.filter(function (e) { return e.style.display !== 'none'; }).length, 1);
  });
  await ca('Codex #356 S1: tab viec co hang chip khoang ngay, bam chip gui ky len may chu; Can giao khong co', async function () {
    var m = dungMan();
    await m.g.scrBangSang(); await tick();
    bang('Can giao khong co chip ngay', m.khung.querySelectorAll('[data-bsk]').length, 0);
    m.g.bsLoc.tab = 'da_giao';
    await m.g.scrBangSang(); await tick();
    var c = m.khung.querySelectorAll('[data-bsk]');
    bang('bon chip ngay', c.length, 4);
    bam(c.filter(function (x) { return x.getAttribute('data-bsk') === '7'; })[0]); await tick(); await tick();
    var cuoi = m.goi[m.goi.length - 1];
    bang('gui ky 7', cuoi.ts.ky, '7');
    bang('giu tab', cuoi.ts.tab, 'da_giao');
  });
  await ca('Codex #356 N2: bam o Tre han goi may chu voi tab tre, o do sang len', async function () {
    var m = dungMan();
    await m.g.scrBangSang(); await tick();
    var o = m.khung.querySelectorAll('[data-bst]').filter(function (c) { return c.getAttribute('data-bst') === 'tre'; });
    bang('co dung mot o Tre han', o.length, 1);
    bam(o[0]); await tick(); await tick();
    bang('tab gui len', m.goi[m.goi.length - 1].ts.tab, 'tre');
  });
  await ca('Codex #356 N3: o tim nhanh loc dong theo ten viec va nguoi nhan, khong dau', async function () {
    var m = dungMan();
    m.g.bsLoc.tab = 'da_giao';
    await m.g.scrBangSang(); await tick();
    var tim = m.khung.querySelector('#bsTim');
    dung('co o tim', !!tim);
    var soGoi = m.goi.length;
    tim.value = 'khai';
    tim.dispatchEvent(dg.suKien('input', {}, tim));
    var dong = m.khung.querySelectorAll('[data-bsv]');
    bang('dong Vu an', dong[0].style.display, 'none');
    bang('dong Khai hien', dong[1].style.display, '');
    tim.value = 'KHẢI';
    tim.dispatchEvent(dg.suKien('input', {}, tim));
    bang('go co dau, hoa van khop', [dong[0].style.display, dong[1].style.display].join('|'), 'none|');
    tim.value = 'croissant';
    tim.dispatchEvent(dg.suKien('input', {}, tim));
    bang('tim theo ten viec', [dong[0].style.display, dong[1].style.display].join('|'), '|none');
    tim.value = 'zzz';
    tim.dispatchEvent(dg.suKien('input', {}, tim));
    bang('khong khop thi bao', m.khung.querySelector('#bsKhongThay').style.display, '');
    bang('loc tai cho, khong goi may chu', m.goi.length, soGoi);
  });
  await ca('Codex #356 T4: loc bo phan thi o so va chip tab dem theo loc, co thanh Tong theo bo loc, Bo loc xoa loc', async function () {
    var m = dungMan();
    m.g.bsLoc.tab = 'da_giao';
    await m.g.scrBangSang(); await tick();
    var hienThanh = function () { var t = m.khung.querySelector('#bsThanhLoc'); return t.style.display || (/display:none/.test(t.getAttribute('style')) ? 'none' : 'flex'); };
    bang('chua loc thi thanh an', hienThanh(), 'none');
    var kho = m.khung.querySelectorAll('[data-bsb]').filter(function (c) { return c.getAttribute('data-bsb') === 'kho'; })[0];
    bam(kho); await tick(); await tick();
    bang('gui bo phan kho', m.goi[m.goi.length - 1].ts.bo_phan, 'kho');
    var oSo = function (k) { return m.khung.querySelectorAll('[data-bst]').filter(function (c) { return c.getAttribute('data-bst') === k; }); };
    dung('o Tre han doc dem da loc (0), khong phai so_tre toan bo', oSo('tre')[0].textContent.trim().indexOf('0Trễ hạn') === 0);
    dung('chip tab Da giao dem 1', oSo('da_giao').some(function (c) { return /^Đã giao\s*1$/.test(c.textContent.trim()); }));
    var thanh = m.khung.querySelector('#bsThanhLoc');
    bang('thanh loc hien', hienThanh(), 'flex');
    dung('thanh ghi tong va ten bo phan', thanh.textContent.indexOf('Tổng theo bộ lọc:') >= 0 && thanh.textContent.indexOf('Kho') >= 0 &&
      m.khung.querySelector('#bsTongLoc').textContent === '1');
    bang('mot dong hien', m.khung.querySelectorAll('[data-bsv]').length, 1);
    var tim = m.khung.querySelector('#bsTim');
    tim.value = 'zzz';
    tim.dispatchEvent(dg.suKien('input', {}, tim));
    bang('go tim thi tong theo so dong con', m.khung.querySelector('#bsTongLoc').textContent, '0');
    bam(m.khung.querySelectorAll('[data-bsk]').filter(function (x) { return x.getAttribute('data-bsk') === '7'; })[0]); await tick(); await tick();
    bang('dang loc kho va 7 ngay', [m.goi[m.goi.length - 1].ts.bo_phan, m.goi[m.goi.length - 1].ts.ky].join('|'), 'kho|7');
    bam(m.khung.querySelector('[data-bsbo]')); await tick(); await tick();
    var cuoi = m.goi[m.goi.length - 1].ts;
    bang('Bo loc gui rong ca bo phan va khoang', [cuoi.bo_phan, cuoi.ky, cuoi.tab].join('|'), '||da_giao');
    bang('het loc thi thanh an', hienThanh(), 'none');
  });
  await ca('Codex #356 U2: dang loc 7 ngay o tab viec, bam sang Can giao thi bo khoang ngay', async function () {
    var m = dungMan();
    m.g.bsLoc.tab = 'da_giao'; m.g.bsLoc.ky = '7';
    await m.g.scrBangSang(); await tick();
    var cg = m.khung.querySelectorAll('[data-bst]').filter(function (c) { return c.getAttribute('data-bst') === 'can_giao'; })[0];
    bam(cg); await tick(); await tick();
    var cuoi = m.goi[m.goi.length - 1].ts;
    bang('sang Can giao gui ky rong', [cuoi.tab, cuoi.ky].join('|'), 'can_giao|');
  });
}

chayHet().then(function () {
  console.log('Bo ca kiem HANH VI man Viec hom nay (#351)');
  ket.loi.forEach(function (d) { console.log('  HONG  ' + d); });
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
}, function (e) { console.log('VO KHUNG: ' + (e && e.stack ? e.stack : e)); process.exit(1); });

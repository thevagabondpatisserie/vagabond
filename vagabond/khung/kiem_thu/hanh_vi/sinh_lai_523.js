/* Bo ca kiem HANH VI: nut Sinh lai chung tu tren man Phieu hoan tien (v523).
 *
 * Ca that HT-2026-02900 (anh Viet 23/09/2026): tien da ra, chung tu hong,
 * man ghi "buoc con lai la dinh uy nhiem chi" ma khong co phieu chi nao de
 * dinh, va thanh duoi cung chi co nut Chuyen khoan. Codex #363 vong 4: viec
 * chinh phai nam o thanh duoi cung, va khong duoc moi chuyen tien lan nua.
 *
 * Nap THAT htCtVe, htCtDong, htCtKhopSepay, htSinhLai (11-khach-ca-hop-dong.js).
 * Cac khoi khac cua man (hoa don dien tu, UNC, don huy...) thay bang chuoi
 * rong vi da co ca kiem rieng. Chi bam nhu nguoi dung: mo phieu, bam nut.
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/sinh_lai_523.js
 */
'use strict';
var fs = require('fs');
var path = require('path');
var vm = require('vm');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var SRC = fs.readFileSync(path.join(GOC, 'vagabond', 'public', 'js', 'bep', '11-khach-ca-hop-dong.js'), 'utf8');

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

var ket = { dat: 0, hong: 0, loi: [] };
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
function dung(mo, x) { if (!x) throw new Error(mo); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; }
  catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n         ') : String(e))); }
}

var THAT = ['htCtVe', 'htCtDong', 'htCtKhopSepay', 'htSinhLai'];
var GIA = ['htCtDonHuy', 'htCtHddt', 'htCtUnc', 'htCtSepayTrong', 'htLyDoTen', 'htDsTen', 'oTep',
  'htMbBiz', 'htFormTuChoi', 'htFormGdVao', 'htKhopSepayTuDong', 'htFormGdRa', 'htGoAnhBangChung',
  'rndXemAnh', 'htUncGui', 'htUncPhongTo', 'htUncTaiTep', 'htUncNapAnh', 'htUncKetThuc', 'htUncGo',
  'htTtLuu', 'htTtGo', 'htHddtMo', 'htHddtChep'];

function dung_man(d, traVe) {
  var goi = [], mo = [], nut = {};
  var ve = { html: '', footer: '' };
  var g = {
    JSON: JSON, Number: Number, String: String, Math: Math,
    h: function (s) { return String(s == null ? '' : s); },
    money: function (n) { return String(n); },
    busy: function () {}, toast: function () {}, baoTin: function () {},
    api: async function (m, a) { goi.push({ m: m, a: a }); return traVe || { ok: 1 }; },
    htChiTiet: function (ma) { mo.push(ma); },
    frame: function (tieu, html, opt) {
      ve.html = html; ve.footer = (opt && opt.footer) || '';
      return { querySelectorAll: function () { return []; } };
    },
    document: {
      getElementById: function (id) {
        if ((ve.html + ve.footer).indexOf('id="' + id + '"') < 0) return null;
        return nut[id] || (nut[id] = { id: id });
      },
    },
    htCtData: d,
  };
  GIA.forEach(function (t) { g[t] = function () { return ''; }; });
  vm.createContext(g);
  vm.runInContext(THAT.map(function (t) { return layHam(SRC, t); }).join('\n'), g);
  return { g: g, goi: goi, mo: mo, nut: nut, ve: ve };
}

function hoSo(them) {
  var d = { name: 'HT-2026-02900', trang_thai: 'Da doi soat', da_doi_soat: 1, duoc_doi_chieu: 1,
    ma_gd: 'ACC-BTN-2026-05949', loi_sinh_ct: 'Tien da ra ... CK bo sung', hoa_don_tra: '', phieu_chi: '' };
  Object.keys(them || {}).forEach(function (k) { d[k] = them[k]; });
  return d;
}

(async function () {
  await ca('HT-2026-02900: ho so ket chung tu thi nut Sinh lai nam o thanh duoi cung, khong con nut Chuyen khoan', async function () {
    var m = dung_man(hoSo({ sinh_lai_duoc: 1 }));
    m.g.htCtVe();
    dung('thanh duoi cung co nut Sinh lai chung tu', m.ve.footer.indexOf('id="htCtSinhLai"') >= 0);
    dung('thanh duoi cung KHONG moi chuyen khoan lan nua', m.ve.footer.indexOf('id="htCtMb"') < 0);
    dung('than man khong con cau "buoc con lai la dinh uy nhiem chi"', m.ve.html.indexOf('Bước còn lại là đính uỷ nhiệm chi') < 0);
    bang('chi mot nut Sinh lai tren ca man', (m.ve.html + m.ve.footer).split('id="htCtSinhLai"').length - 1, 1);
  });
  await ca('bam Sinh lai chung tu thi goi dung may chu va mo lai phieu', async function () {
    var m = dung_man(hoSo({ sinh_lai_duoc: 1 }), { ok: 1, phieu_chi: 'APP-1' });
    m.g.htCtVe();
    dung('nut da gan viec', m.nut.htCtSinhLai && typeof m.nut.htCtSinhLai.onclick === 'function');
    m.nut.htCtSinhLai.onclick();
    /* onclick khong tra promise (giong nguoi bam); cho vong su kien chay xong. */
    for (var k = 0; k < 5; k++) await new Promise(function (r) { setImmediate(r); });
    var x = m.goi.filter(function (c) { return c.m === 'vagabond.hoan_tien.sinh_lai'; });
    bang('goi sinh_lai mot lan dung ho so', x.map(function (c) { return c.a.ho_so; }), ['HT-2026-02900']);
    bang('mo lai phieu de hien nut Dinh UNC', m.mo, ['HT-2026-02900']);
  });
  await ca('ho so binh thuong van giu nut Chuyen khoan va cau huong dan cu', async function () {
    var m = dung_man(hoSo({ sinh_lai_duoc: 0, loi_sinh_ct: '', phieu_chi: 'APP-9' }));
    m.g.htCtVe();
    dung('co nut Chuyen khoan', m.ve.footer.indexOf('id="htCtMb"') >= 0);
    dung('khong co nut Sinh lai', (m.ve.html + m.ve.footer).indexOf('id="htCtSinhLai"') < 0);
    dung('van ghi buoc con lai la dinh UNC', m.ve.html.indexOf('Bước còn lại là đính uỷ nhiệm chi') >= 0);
  });
  console.log('Bo ca kiem HANH VI nut Sinh lai chung tu (HT-2026-02900, v523)');
  ket.loi.forEach(function (d) { console.log('  HONG  ' + d); });
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
})();

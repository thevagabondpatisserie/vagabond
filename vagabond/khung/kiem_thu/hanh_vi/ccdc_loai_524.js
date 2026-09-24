/* Bo ca kiem HANH VI: man Mo ma hang moi doi chip Loai hang theo nhom CCDC
 * dung ngay (v524, Codex #364 vong 2).
 *
 * Nguoi dung chon nhom "CCDC dùng ngay" trong khi chip Loai hang con de mac
 * dinh Thanh pham. May chu tra ve loai that cua nhom; man phai doi chip theo,
 * de ten, canh bao va ba co mua - ban - ton tren man khop voi ma se tao.
 *
 * Nap THAT dmHoiXem (17-cai-dat.js). Chi thay api, dmDraw, dmVeXem va dong ho.
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/ccdc_loai_524.js
 */
'use strict';
var fs = require('fs');
var path = require('path');
var vm = require('vm');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var SRC = fs.readFileSync(path.join(GOC, 'vagabond', 'public', 'js', 'bep', '17-cai-dat.js'), 'utf8');

function layHam(src, ten) {
  var dau = src.indexOf('function ' + ten + '(');
  if (dau < 0) throw new Error('Khong thay ham ' + ten);
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Ham ' + ten + ' khong dong ngoac');
}

var ket = { dat: 0, hong: 0, loi: [] };
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; }
  catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n         ') : String(e))); }
}

function dung_man(ve, traVe) {
  var goi = [], ve_lai = [], xem = 0, hen = [];
  var g = {
    JSON: JSON, String: String,
    dmVe: ve, dmKq: null, dmTre: null, dmHoiLuot: 0,
    api: function (m, a) {
      goi.push({ m: m, a: JSON.parse(JSON.stringify(a)) });
      // traVe là hàm thì ca tự quyết lúc nào lượt này về (dựng về trễ).
      return typeof traVe === 'function' ? traVe(a) : Promise.resolve(traVe);
    },
    dmDraw: function (giu) { ve_lai.push(g.dmVe.loai); },
    dmVeXem: function () { xem++; },
    setTimeout: function (f) { hen.push(f); return hen.length; },
    clearTimeout: function () {},
  };
  vm.createContext(g);
  vm.runInContext(layHam(SRC, 'dmHoiXem'), g);
  return { g: g, goi: goi, ve_lai: ve_lai, xem: function () { return xem; }, hen: hen };
}

async function chay(m) {
  m.g.dmHoiXem();
  // Nguoi dung ngung go 320 ms: chay dung ham hen gio, doi api xong.
  await m.hen[m.hen.length - 1]();
}

(async function () {
  await ca('chon nhom CCDC dung ngay khi chip con de Thanh pham: man doi chip sang loai cua nhom', async function () {
    var m = dung_man({ nhom: 'CCDC dùng ngay', loai: 'thanh_pham', ten: 'Quạt đứng Midea', quy_cach: 'Trắng' },
      { loai: 'ccdc_dung_ngay', ten_day_du: 'Quạt đứng Midea', tien_to: 'CCDN', trung: [], canh_bao: [] });
    await chay(m);
    bang('hoi xem truoc dung mot lan voi loai dang chon', m.goi.map(function (c) { return c.a.loai; }), ['thanh_pham']);
    bang('chip doi sang loai cua nhom', m.g.dmVe.loai, 'ccdc_dung_ngay');
    bang('ve lai ca man de chip va ba co doi theo', m.ve_lai, ['ccdc_dung_ngay']);
  });
  await ca('loai may tra ve trung loai dang chon thi chi ve phan xem truoc, khong ve lai ca man', async function () {
    var m = dung_man({ nhom: 'Công cụ Dụng cụ', loai: 'nvl', ten: 'Nồi inox', quy_cach: '' },
      { loai: 'nvl', ten_day_du: 'Nồi inox', tien_to: 'CCDC', trung: [], canh_bao: [] });
    await chay(m);
    bang('khong ve lai ca man', m.ve_lai, []);
    bang('ve phan xem truoc', m.xem(), 1);
  });
  await ca('Codex #364 v3: luot xem truoc ve tre sau khi nguoi da doi nhom thi bi bo, khong ep loai CCDC len nhom khac', async function () {
    var cho = [];
    var m = dung_man({ nhom: 'CCDC dùng ngay', loai: 'thanh_pham', ten: 'Quạt đứng', quy_cach: '' }, function (a) {
      return new Promise(function (tra) { cho.push({ a: a, tra: tra }); });
    });
    // Lượt 1: nhóm CCDC, máy chưa trả lời.
    m.g.dmHoiXem();
    var l1 = m.hen[m.hen.length - 1]();
    // Người dùng đổi sang nhóm Công cụ Dụng cụ, loại Nguyên vật liệu: lượt 2.
    m.g.dmVe.nhom = 'Công cụ Dụng cụ'; m.g.dmVe.loai = 'nvl';
    m.g.dmHoiXem();
    var l2 = m.hen[m.hen.length - 1]();
    // Lượt 2 về trước, lượt 1 về sau.
    cho[1].tra({ loai: 'nvl', ten_day_du: 'Quạt đứng', trung: [], canh_bao: [] });
    await l2;
    cho[0].tra({ loai: 'ccdc_dung_ngay', ten_day_du: 'Quạt đứng', trung: [], canh_bao: [] });
    await l1;
    bang('hai luot da hoi', m.goi.map(function (c) { return c.a.nhom; }), ['CCDC dùng ngay', 'Công cụ Dụng cụ']);
    bang('loai giu nguyen theo nhom hien tai', m.g.dmVe.loai, 'nvl');
    bang('khong ve lai ca man vi luot tre', m.ve_lai, []);
    bang('ket qua dang hien la cua luot moi', m.g.dmKq && m.g.dmKq.loai, 'nvl');
  });
  await ca('Codex #364 v3: chi go them ten trong luc cho thi ket qua luot cu ve tre khong de len luot moi', async function () {
    var cho = [];
    var m = dung_man({ nhom: 'CCDC dùng ngay', loai: 'ccdc_dung_ngay', ten: 'Quạt', quy_cach: '' }, function (a) {
      return new Promise(function (tra) { cho.push({ a: a, tra: tra }); });
    });
    m.g.dmHoiXem();
    var l1 = m.hen[m.hen.length - 1]();
    m.g.dmVe.ten = 'Quạt đứng Midea';
    m.g.dmHoiXem();
    var l2 = m.hen[m.hen.length - 1]();
    cho[1].tra({ loai: 'ccdc_dung_ngay', ten_day_du: 'Quạt đứng Midea', trung: [], canh_bao: [] });
    await l2;
    cho[0].tra({ loai: 'ccdc_dung_ngay', ten_day_du: 'Quạt', trung: [], canh_bao: [] });
    await l1;
    bang('ten dang hien la cua luot moi', m.g.dmKq && m.g.dmKq.ten_day_du, 'Quạt đứng Midea');
  });
  console.log('Bo ca kiem HANH VI chip Loai hang theo nhom CCDC dung ngay (v524)');
  ket.loi.forEach(function (d) { console.log('  HONG  ' + d); });
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
})();

/* v674: chụp và đo bốn màn mới (Bảng kê 242, sheet khai, sheet phân bổ tháng, Chi phí
 * quảng cáo Meta, Đối soát chi phí Meta, chi tiết tháng) và phần CCDC của màn Lập phiếu
 * xuất dùng nội bộ, trên Chromium 390x844, chạy ĐÚNG mã 79-chi-phi-242.js,
 * 80-chi-phi-meta.js, 45-xuat-kho-them.js thật với API giả lập.
 *
 * Đo: không cuộn ngang; mọi nút, chip bấm được cao từ 44 điểm; chữ trong vùng màn
 * từ 13 điểm; nút không bị lớp khác che ở tâm.
 *
 * Bằng chứng loại "tệp trong repo, API giả lập, CSS nền của app (00-nen.js, CSS màn
 * xuất kho)". Không thay ảnh trên site thật (thiếu CSS Frappe).
 *
 * Chạy: node cong_cu/chup_chi_phi_674.cjs /thu/muc/anh
 * Mã trả 0: đạt hết; 1: có số đo hỏng; 2: thiếu Playwright/Chromium.
 */
'use strict';
var fs = require('fs');
var path = require('path');
var GOC = path.resolve(__dirname, '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
var RA = process.argv[2] || '/tmp';
var pw;
try { pw = require('playwright'); } catch (e) { console.log('THIẾU Playwright, chưa đo được'); process.exit(2); }

function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
function layHam(src, ten) {
  var dau = src.search(new RegExp('(?:async )?function ' + ten + '\\('));
  if (dau < 0) throw new Error('Khong thay ham ' + ten);
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Ham ' + ten + ' khong dong ngoac');
}
function layBien(src, ten) {
  var dau = src.indexOf('var ' + ten + ' = ');
  if (dau < 0) throw new Error('Khong thay bien ' + ten);
  var i = src.indexOf('=', dau) + 1, sau = 0, vao = false;
  for (var j = i; j < src.length; j++) {
    var c = src[j];
    if (c === '{' || c === '[') { sau++; vao = true; } else if (c === '}' || c === ']') sau--;
    else if (c === ';' && sau === 0) return src.slice(dau, j + 1);
    if (vao && sau === 0 && src[j + 1] === ';') return src.slice(dau, j + 2);
  }
  throw new Error('Bien ' + ten + ' khong dong');
}
function cssNen() {
  var n = doc('00-nen.js');
  var a = n.indexOf('var CSS = `') + 'var CSS = `'.length;
  return n.slice(a, n.indexOf('`;', a));
}
var NEN = doc('00-nen.js'), KHUNG = doc('01-khung-app.js'), TC = doc('02-trang-chu.js'), XK = doc('45-xuat-kho-them.js');
var HAM = [
  ['00-nen.js', ['h', 'money', 'num', 'anhMon', 'vgbChuan', 'vgbKhop', 'sheet']],
  ['02-trang-chu.js', ['vgbCss']],
  ['15-khuon-danh-sach.js', ['ngayNgan']],
  ['09-tinh-tien-quay.js', ['posChipNut']],
  ['58-crm.js', ['crmMoSheet', 'crmNutChon']],
  ['45-xuat-kho-them.js', ['xktHangChip', 'xktChip', 'xktChipNhom', 'xktOChon', 'xktOChip', 'xktOChipLon', 'xktCss', 'xktDongHtml', 'xktNoiDong', 'xktNoiSuKien', 'xktTongDong',
    'xktSheetTim', 'xktBaoThieu', 'xktOAnh', 'xktNoiAnh', 'xktKhoHtml', 'xktNutChinh', 'xktBoPhanItems', 'xktBootNb', 'xktKeoGioVe', 'scrXkNbNew']]
].map(function (x) { var s = doc(x[0]); return x[1].map(function (t) { return layHam(s, t); }).join('\n'); }).join('\n') +
  '\n' + layBien(XK, 'XKT') + '\n' + doc('79-chi-phi-242.js') + '\n' + doc('80-chi-phi-meta.js');

/* Dữ liệu giả lập theo hình dạng máy chủ trả (chi_phi_242.danh_sach, chi_tiet, xem_thang;
   quang_cao_meta.tong_quan; chi_phi_meta.ds_thang, chi_tiet_thang). Tên món, nhà cung cấp
   lấy từ danh sách CCDC thật trên site 18/11/2026. */
var KHOAN = [
  { name: 'CP242-00021', nguon_loai: 'Phiếu xuất CCDC', nguon_so: 'PXD-26-11-0004', ngay: '2026-11-18', dien_giai: 'Khuôn ring inox 304, 20 x 6 cm, 1 ly, Inox Tiến Dũng và 3 món nữa', nguyen_gia: 3600000, so_ky: 12, da_phan_bo: 0, con_lai: 3600000, trang_thai_hien: 'Đang phân bổ', anh: '' },
  { name: 'CP242-00012', nguon_loai: 'Hoá đơn mua', nguon_so: 'ACC-PINV-2026-00412', ngay: '2026-10-21', dien_giai: 'Tủ đông, MF1-766WWE2, Hoshizaki - CÔNG TY TNHH THƯƠNG MẠI VÀ DỊCH VỤ KỸ THUẬT DIỆU PHÚC', nguyen_gia: 28500000, so_ky: 0, da_phan_bo: 0, con_lai: 28500000, trang_thai_hien: 'Chờ khai số tháng', anh: '' },
  { name: 'CP242-00007', nguon_loai: 'Hoá đơn mua', nguon_so: 'ACC-PINV-2026-00233', ngay: '2026-09-25', dien_giai: 'Quạt đứng, FS40-24EVN(K), Media - Điện Máy Xanh', nguyen_gia: 650000, so_ky: 3, da_phan_bo: 650000, con_lai: 0, trang_thai_hien: 'Đã phân bổ xong', anh: '' },
  { name: 'CP242-00002', nguon_loai: 'Bút toán', nguon_so: 'ACC-JV-2026-00031', ngay: '2026-08-30', dien_giai: 'Tiền thuê kho Tân Bình trả trước 6 tháng', nguyen_gia: 60000000, so_ky: 0, da_phan_bo: 0, con_lai: 60000000, trang_thai_hien: 'Không phân bổ', anh: '' }
];
var FX = {
  'vagabond.chi_phi_242.danh_sach': { rows: KHOAN, dem: { trang_thai: { '': 4, 'Chờ khai số tháng': 1, 'Đang phân bổ': 1, 'Đã phân bổ xong': 1, 'Không phân bổ': 1 }, nguon: { '': 4, 'Hoá đơn mua': 2, 'Phiếu xuất CCDC': 1, 'Bút toán': 1 } },
    tong: { nguyen_gia: 92750000, da_phan_bo: 650000, con_lai: 92100000 }, co_chua_gan: [{ dong: 'x1', je: 'ACC-JV-2026-00044', ngay: '2026-10-31', tien: 1500000, dien_giai: 'Phân bổ khuôn tháng 10 (lập tay)' }], duoc_lap: 1, duoc_ghi: 1, hom_nay: '2026-11-18' },
  'vagabond.chi_phi_242.chi_tiet': { name: 'CP242-00021', nguon_loai: 'Phiếu xuất CCDC', nguon_doctype: 'Stock Entry', nguon_so: 'PXD-26-11-0004', ngay: '2026-11-18', dien_giai: KHOAN[0].dien_giai, nguyen_gia: 3600000, so_ky: 12, ky_bat_dau: '2026-11', bo_phan: 'Bếp Pastry - TV', tk_chi_phi: '6273 - Chi phí dụng cụ sản xuất - TV',
    da_phan_bo_truoc: 0, da_tren_so: 0, da_phan_bo: 0, con_lai: 3600000, trang_thai: '', trang_thai_hien: 'Đang phân bổ', ghi_chu: '', lich: Array.apply(null, Array(12)).map(function (_, i) { return { ky: '2026-' + String(11 + i).padStart(2, '0'), so_tien: 300000 }; }),
    lan_phan_bo: [], mon: [{ ma: 'CCDC00224', ten: 'Khuôn ring inox 304, 20 x 6 cm, 1 ly, Inox Tiến Dũng', sl: 6, dvt: 'Cái', tien: 1080000, anh: '' }, { ma: 'CCDC00223', ten: 'Khuôn ring inox 304, 18 x 6 cm, 1 ly, Inox Tiến Dũng', sl: 6, dvt: 'Cái', tien: 960000, anh: '' }],
    chon_so_ky: [2, 3, 6, 12, 18, 24, 36], so_ky_toi_da: 36, duoc_lap: 1, duoc_ghi: 1 },
  'vagabond.chi_phi_242.danh_muc': { bo_phan: [{ value: 'Bếp Pastry - TV', label: 'Bếp Pastry', phu: 'Khối sản xuất' }], tai_khoan: [{ value: '6273 - Chi phí dụng cụ sản xuất - TV', label: '6273 - Chi phí dụng cụ sản xuất', phu: 'Tài khoản chi phí' }] },
  'vagabond.chi_phi_242.xem_thang': { ky: '2026-10', trang_thai: 'Nháp chờ ghi sổ', journal_entry: 'ACC-JV-2026-00058', tong: 1950000, tuong_lai: 0, duoc_lap: 1, duoc_ghi: 1,
    dong: [{ khoan: 'CP242-00012', so_tien: 1187500, tk_chi_phi: '6273 - Chi phí dụng cụ sản xuất - TV', dien_giai: 'Tủ đông, MF1-766WWE2, Hoshizaki' }, { khoan: 'CP242-00007', so_tien: 216667, tk_chi_phi: '6413 - Chi phí dụng cụ, đồ dùng - TV', dien_giai: 'Quạt đứng, FS40-24EVN(K), Media' }],
    cho_khai: [{ name: 'CP242-00011', dien_giai: 'Bếp điện từ công nghiệp', nguyen_gia: 9800000 }], co_chua_gan: [] },
  'vagabond.quang_cao_meta.tong_quan': { tu: '2026-10-19', den: '2026-11-17', tong_chi: { VND: 20557590 }, tong_doanh_thu_web: 146800000, co_nhom_nhan: 0, duoc_doc_lai: 1,
    dem: { '': 30, 'Đã chốt': 26, 'Meta còn điều chỉnh': 3, 'Chưa đọc': 0, 'Không chi': 1 },
    cau_hinh: { bat: 1, loi: [], doc_lai: 3 }, tai_khoan: [{ ma: 'act_1234567890', ten: 'Vagabond Pâtisserie', mui_gio: 'Asia/Ho_Chi_Minh', tien_te: 'VND', moc: '2026-11-17', lan_cuoi: '2026-11-18 07:13:22', loi: '' }],
    rows: [['2026-11-17', 812000, 6250000, 'Meta còn điều chỉnh'], ['2026-11-16', 790500, 5100000, 'Meta còn điều chỉnh'], ['2026-11-15', 801200, 4890000, 'Meta còn điều chỉnh'], ['2026-11-14', 0, 3120000, 'Không chi'], ['2026-11-13', 650000, 7200000, 'Đã chốt']].map(function (r) { return { ngay: r[0], chi: r[1] ? { VND: r[1] } : {}, doanh_thu_web: r[2], trang_thai: r[3] }; }) },
  'vagabond.quang_cao_meta.chi_tiet_ngay': [{ tai_khoan: 'act_1234567890', ten_tai_khoan: 'Vagabond Pâtisserie', chien_dich: '1202', ten_chien_dich: 'Bánh Trung thu - tin nhắn', so_tien: 512000, tien_te: 'VND' }, { tai_khoan: 'act_1234567890', ten_tai_khoan: 'Vagabond Pâtisserie', chien_dich: '1203', ten_chien_dich: 'Web đặt bánh - chuyển đổi', so_tien: 300000, tien_te: 'VND' }],
  'vagabond.chi_phi_meta.ds_thang': { cho_duyet_sao_ke: 1, duoc_lap: 1, duoc_ghi: 1, dem: { '': 6, 'Khớp': 2, 'Lệch': 1, 'Chưa đủ chứng từ': 2, 'Chưa có sao kê': 1 },
    rows: [{ ky: '2026-11', trang_thai: 'Chưa đủ chứng từ', da_tieu: { VND: 12400000 }, da_tru: 16500000, da_ghi_so: 0, so_giao_dich: 1, so_cho: 0, thieu: [['2026-11-30', '2026-12-10']], but_toan: 'Chưa lập' },
      { ky: '2026-10', trang_thai: 'Lệch', da_tieu: { VND: 21300400 }, da_tru: 20557590, da_ghi_so: 0, so_giao_dich: 7, so_cho: 0, thieu: [], but_toan: 'Nháp chờ ghi sổ' },
      { ky: '2026-09', trang_thai: 'Khớp', da_tieu: { VND: 38021110 }, da_tru: 37664995, da_ghi_so: 37664995, so_giao_dich: 6, so_cho: 0, thieu: [], but_toan: 'Đã ghi sổ' }] },
  'vagabond.chi_phi_meta.chi_tiet_thang': { ky: '2026-10', trang_thai: 'Lệch', da_tieu: { VND: 21300400 }, da_tru: 20557590, da_ghi_so: 0, thieu: [], cho_duyet_sao_ke: 0, duoc_lap: 1, duoc_ghi: 1,
    chung_tu_khac: [{ doctype: 'Journal Entry', name: 'ACC-JV-2026-00049', ngay: '2026-10-31', mo: 'Chi quảng cáo Facebook tháng 10 (lập tay)', tien: 4057590, da_ghi_so: 0, da_xem: 0 }],
    giao_dich: [{ khoa: 'a', the4: '0000', ngay_gd: '2026-10-05', ngay_bt: '2026-10-07', dv: 'FACEBK *LRBD57EPJ4', tien: 16500000, phan_loai: 'meta', trang_thai: 'Vào bút toán', so_bang_chung: 2, can_quyet: null,
        nut_tay: { khoa_quyet: 'chon:a', gia_tri: 'bo', ly_do: 1, nhan: 'Đã ghi ở chứng từ khác' } },
      { khoa: 'b', the4: '0000', ngay_gd: '2026-10-18', ngay_bt: '2026-10-21', dv: 'FACEBK *VKZTV66PJ4', tien: 4057590, phan_loai: 'meta', trang_thai: 'Kế toán bỏ', so_bang_chung: 2, can_quyet: null,
        nut_tay: { khoa_quyet: 'chon:b', gia_tri: 'vao', ly_do: 0, nhan: 'Đưa lại vào bút toán', ly_do_bo: 'Đã ghi ở bút toán tay ACC-JV-2026-00049' } },
      { khoa: 'c', the4: '0000', ngay_gd: '2026-10-18', ngay_bt: '2026-10-21', dv: 'FOREIGN TRANSACTION FEE', tien: 33000, phan_loai: 'phi_chua_ro', trang_thai: 'Chờ kế toán chọn', so_bang_chung: 1,
        can_quyet: { loai: 'chon', khoa_quyet: 'chon:c', mo: 'Phí này không ghi rõ của giao dịch nào. Có phải phí đi kèm quảng cáo Meta không?' } }],
    but_toan: { trang_thai: 'Nháp chờ ghi sổ', journal_entry: 'ACC-JV-2026-00057', du_kien_qc: 20557590, du_kien_phi: 0,
      dong: [{ account: '6417 - Chi phí dịch vụ mua ngoài - TV', debit: 20557590, credit: 0 }, { account: '3411 - Các khoản đi vay - TV', debit: 0, credit: 20557590 }] },
    tk: { qc: '6417 - Chi phí dịch vụ mua ngoài - TV', phi: '6427 - Chi phí dịch vụ mua ngoài - TV', the: '3411 - Các khoản đi vay - TV' } },
  'vagabond.xuat_noi_bo.khoi_dong': { cong_ty: 'CÔNG TY TNHH PATISSERIE VAGABOND', kho: [{ name: 'Kho Tổng - TV', warehouse_name: 'Kho Tổng' }],
    muc_dich: [{ ma: 'marketing', ten: 'Marketing chụp ảnh, quay phim', mo: '', bo_phan: 'Marketing' }, { ma: 'ccdc', ten: 'Đưa công cụ dụng cụ vào dùng', mo: 'Khuôn, dụng cụ, thiết bị lấy từ kho ra dùng. Chọn phân bổ một lần hay nhiều tháng.', bo_phan: '' },
      { ma: 'khac', ten: 'Việc nội bộ khác', mo: '', bo_phan: '' }],
    bo_phan: [{ nhom: 'Khối sản xuất', bo_phan: [{ ten: 'Bếp Pastry' }] }], cach_phan_bo: [{ ma: 'mot_lan', ten: 'Phân bổ một lần', mo: 'Giá trị hàng vào thẳng chi phí tháng này của bộ phận dùng. Hợp với đồ rẻ, dùng nhanh hỏng.' },
      { ma: 'nhieu_ky', ten: 'Phân bổ nhiều tháng', mo: 'Giá trị vào 242, Kế toán chia dần vào chi phí từng tháng theo Bảng kê 242. Hợp với khuôn, thiết bị dùng lâu.' }],
    chon_so_ky: [2, 3, 6, 12, 18, 24, 36], duoc_duyet: 1, toi: 'kho@vagabond' }
};

var STUB = [
  'var S = { stack: [1], roles: ["System Manager"] }; var root = document.getElementById("vgb");',
  'function frame(t, html, opt) { opt = opt || {}; root.innerHTML = "<div class=\\"vh\\"><button class=\\"ic\\">&#8249;</button><b>" + h(t) + "</b><span class=\\"ic\\"></span></div>" +',
  '  "<div class=\\"vb\\" id=\\"vgbBody\\">" + html + "</div>" + (opt.footer ? "<div class=\\"vf\\">" + opt.footer + "</div>" : "");',
  '  document.body.classList.toggle("vgb-co-vf", !!opt.footer); return document.getElementById("vgbBody"); }',
  'function api(m, a) { var r = FX[m]; return r === undefined ? Promise.reject(new Error("API giả lập thiếu " + m)) : Promise.resolve(JSON.parse(JSON.stringify(r))); }',
  'function go(f) { return f(); } function toast() {} function errMsg(e) { return (e && e.message) || ""; } function hasRole() { return true; }',
  'function xacNhan() { return Promise.resolve(false); } function hoiChu() { return Promise.resolve(""); } function busy() {}',
  'function scrXkChonHang() {} var XK = { gio: [] }; function vgbCssKeep() {} function khoGiuCuaToi() { return []; }'
].join('\n');

async function chay() {
  var b = await pw.chromium.launch();
  var trang = await b.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  var loi = [];
  trang.on('pageerror', function (e) { loi.push(e.message); });
  await trang.setContent('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>' + cssNen() +
    '</style></head><body><div id="vgb"></div></body></html>');
  await trang.addScriptTag({ content: 'var FX = ' + JSON.stringify(FX) + ';\n' + STUB + '\n' + HAM });
  var hong = [];
  /* Đo phần MỚI hoặc ĐÃ SỬA của màn: có sheet mở thì chỉ trong sheet; khung đầu màn
     (.vh, nút lùi của vỏ app) không thuộc PR này nên không đo. vung: bộ chọn riêng. */
  async function doDo(ten, vung) {
    var kq = await trang.evaluate(function (vung) {
      var r = { tran: document.scrollingElement.scrollWidth > window.innerWidth + 1, nhoNut: [], nhoChu: [], che: [] };
      var sh = document.querySelectorAll('.sh');
      var goc = vung ? Array.prototype.slice.call(document.querySelectorAll(vung)) : (sh.length ? [sh[sh.length - 1]] : [document.getElementById('vgbBody'), document.querySelector('#vgb > .vf')].filter(Boolean));
      function trong(n) { return goc.some(function (g) { return g.contains(n); }); }
      var nut = Array.prototype.slice.call(document.querySelectorAll('button, [role=button], input, textarea')).filter(trong);
      nut.forEach(function (n) {
        var rc = n.getBoundingClientRect();
        if (!rc.width || !rc.height) return;
        if (rc.height < 43.5 && n.type !== 'file') r.nhoNut.push((n.textContent || n.id || n.type || '').trim().slice(0, 30) + ' ' + Math.round(rc.height));
        if (rc.top >= 0 && rc.bottom <= window.innerHeight && rc.left >= 0 && rc.right <= window.innerWidth) {
          var x = rc.left + rc.width / 2, y = rc.top + rc.height / 2, e = document.elementFromPoint(x, y);
          if (e && e !== n && !n.contains(e) && !(e.closest && e.closest('label') && e.closest('label').contains(n))) r.che.push((n.textContent || n.id || '').trim().slice(0, 30));
        }
      });
      var tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      while (tw.nextNode()) {
        var t = tw.currentNode, s = (t.nodeValue || '').trim();
        if (!s || !t.parentElement || !trong(t.parentElement)) continue;
        var el = t.parentElement, cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden' || el.closest('svg')) continue;
        var px = parseFloat(cs.fontSize);
        if (px < 12.95 && el.getBoundingClientRect().width) r.nhoChu.push(s.slice(0, 24) + ' ' + px);
      }
      return r;
    }, vung || null);
    if (kq.tran) hong.push(ten + ': cuộn ngang');
    if (kq.nhoNut.length) hong.push(ten + ': nút thấp hơn 44: ' + kq.nhoNut.slice(0, 5).join(' | '));
    if (kq.nhoChu.length) hong.push(ten + ': chữ dưới 13: ' + kq.nhoChu.slice(0, 5).join(' | '));
    if (kq.che.length) hong.push(ten + ': nút bị che: ' + kq.che.slice(0, 5).join(' | '));
  }
  async function chup(ten, ham, cuon, vung) {
    await trang.evaluate(function () { document.querySelectorAll('.sh').forEach(function (x) { x.remove(); }); window.scrollTo(0, 0); });
    await trang.evaluate(ham);
    await trang.waitForTimeout(250);
    if (cuon) await trang.evaluate(cuon);
    await doDo(ten, vung);
    await trang.screenshot({ path: path.join(RA, ten + '.png') });
  }
  await chup('674-1-bang-ke-242', function () { return scrCp242(); });
  await chup('674-2-chi-tiet-khoan', function () { return scrCp242().then(function () { return cp2ChiTiet('CP242-00021'); }); });
  await chup('674-3-khai-phan-bo', function () { return cp2SheetKhai(FX['vagabond.chi_phi_242.chi_tiet']); });
  await chup('674-4-phan-bo-thang', function () { return cp2SheetThang('2026-10'); });
  await chup('674-5-chi-phi-meta', function () { return scrQcMeta(); });
  await chup('674-6-doi-soat-meta', function () { return scrDsMeta(); });
  await chup('674-7-doi-soat-thang', function () { return scrDsMetaThang('2026-10'); });
  /* Codex #590: đường tay bỏ giao dịch đã ghi ở chứng từ khác, và đưa lại. */
  var nutTay = await trang.evaluate(function () {
    return Array.prototype.slice.call(document.querySelectorAll('[data-dsmq]')).map(function (n) { return n.textContent.trim() + '|' + n.getAttribute('data-gt') + '|' + (n.getAttribute('data-lydo') || ''); });
  });
  ['Đã ghi ở chứng từ khác|bo|1', 'Đưa lại vào bút toán|vao|', 'Không phải|bo|1'].forEach(function (m) { if (nutTay.indexOf(m) < 0) hong.push('674-7: thiếu nút ' + m); });
  await chup('674-8-doi-soat-thang-duoi', function () { return scrDsMetaThang('2026-10'); }, function () { window.scrollTo(0, document.body.scrollHeight); });
  await chup('674-9-xuat-ccdc', function () { XKT.nb.mucDich = 'ccdc'; XKT.nb.cachPb = 'nhieu_ky'; XKT.nb.soKy = 12; XKT.nb.kho = 'Kho Tổng - TV'; return scrXkNbNew(); }, function () { var o = document.getElementById('nbpbO'); if (o) o.scrollIntoView({ block: 'start' }); }, '#nbpbO, #nbskO');
  await b.close();
  if (loi.length) hong.push('lỗi trang: ' + loi.slice(0, 3).join(' | '));
  console.log(hong.length ? 'HỎNG\n- ' + hong.join('\n- ') : 'ĐẠT: 9 ảnh, không cuộn ngang, nút từ 44, chữ từ 13, không nút bị che');
  process.exit(hong.length ? 1 : 0);
}
chay().catch(function (e) { console.log('LỖI', e && e.stack || e); process.exit(1); });

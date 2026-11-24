/* Rà lại từng mục của báo cáo rà giao diện độc lập (Codex, v690, UI17 tới UI98) trên bản đang có.
 *
 * Mỗi mục có cách mở màn (gọi thẳng hàm màn qua một cửa thử chèn vào bản app trong bộ nhớ, rồi
 * bấm vài bước) và một phép kiểm riêng cho hiện tượng đã báo. Dữ liệu là dữ liệu giả có hình dạng
 * như máy chủ trả (du_lieu_thu.cjs, dữ liệu Cài đặt lõi dựng bằng chính phép máy chủ, và bộ
 * FIX dưới đây). Lời gọi chưa có dữ liệu thử được ghi tên và trả "rỗng" như quet_man.cjs.
 * Không gọi API thật, không ghi gì.
 *
 *   node cong_cu/ui_b/ra_muc.cjs --ra /tmp/ra                     cả 82 mục, 390x844, Chromium
 *   node cong_cu/ui_b/ra_muc.cjs --ra /tmp/ra --khung 360x780 --may webkit
 *   node cong_cu/ui_b/ra_muc.cjs --ra /tmp/ra --ma UI50,UI62      vài mục
 *   node cong_cu/ui_b/ra_muc.cjs --ra /tmp/ra --app /tmp/app_cu.js   chạy trên bản app khác (ca đỏ)
 *
 * Mã trả 0: mọi mục đã khép; 1: còn mục chưa khép; 2: thiếu Playwright.
 * Ghi ra-muc.json (từng mục: còn hay khép, chi tiết đo) và ảnh từng màn.
 */
'use strict';
var fs = require('fs');
var path = require('path');
var cp = require('child_process');
var GOC = path.resolve(__dirname, '..', '..');
var CONG = path.join(GOC, 'vagabond', 'public');
var DL = require('./du_lieu_thu.cjs');

function thamSo(ten, macDinh) {
  var i = process.argv.indexOf('--' + ten);
  return i > 0 && process.argv[i + 1] ? process.argv[i + 1] : macDinh;
}
var RA = thamSo('ra', '/tmp/ui-b-ra-muc');
var KH = thamSo('khung', '390x844').split('x');
var KHUNG = { w: +KH[0], h: +KH[1] };
var MAY = thamSo('may', 'chromium');
var APP = thamSo('app', '');
var CHON = thamSo('ma', '');
var BAT = thamSo('che-do', 'bat') === 'bat';
var ORIGIN = 'http://vgb.thu';

/* Dữ liệu Cài đặt lõi: dựng bằng chính phép máy chủ như ca cai_dat_loi_570.js. */
function layCdl() {
  var py = [
    'import json, sys', 'sys.path.insert(0, sys.argv[1])',
    'from vagabond.khung.kiem_thu import nen', 'nen.gia_lap()',
    'from vagabond import cai_dat_loi as c', 'from vagabond.khung.kiem_thu import thu_cai_dat_loi_570 as t',
    'tr = t._truong_da_xep()',
    'doc = {f["fieldname"]: (0 if f["fieldtype"] == "Check" else None) for f in tr}',
    'doc.update({"tk_hoan_tien": "MB - TV", "tu_xuat_hddt": 1, "ngan_hang_bin": "970422", "ngan_hang_hien_thi": "MB Bank",',
    '  "zalo_chat_moi": json.dumps([{"chat_id": "g-777", "ten": "Nhóm Bếp", "loai": "GROUP", "luc": "2026-11-20 08:00"}]),',
    '  "vgb_diem_ban": json.dumps([{"ma": "Q1", "ten": "Quận 1", "co_quay": 1}])})',
    'cot = t._cot_zalo()',
    'dong = [{"name": "r1", "ten_nhom": "Vận hành", "chat_id": "zgr-" + "0123456789" * 6, "loai_tin": "thong_bao, canh_bao", "chu_de": "", "im_tu": "22:00", "im_den": "07:00", "bat": 1}]',
    'ra = {"bo_cuc": c.bo_cuc(tr), "gia_tri": c.gia_tri(tr, doc), "modified": "2026-10-04 09:00:00.000001",',
    '  "bang": {"zalo_nhom": {"cot": c.tom_bang(cot), "dong": [dict(c.gia_tri(cot, r), name=r["name"]) for r in dong],',
    '    "ghi_qua_hop_chon": list(c.GHI_QUA_HOP_CHON["zalo_nhom"])}}}',
    'import os',
    'cot_bot = json.load(open(os.path.join(sys.argv[1], "vagabond", "vagabond", "doctype", "vagabond_bot_zalo", "vagabond_bot_zalo.json"), encoding="utf-8"))["fields"]',
    'bot = [{"name": "b2", "ma_bot": "2", "ten_bot": "Bot Bếp", "co_token": 1, "trang_thai": "Đã xác minh."}]',
    'ra["bang"]["zalo_bot_phu"] = {"cot": c.tom_bang(cot_bot), "dong": [dict(c.gia_tri(cot_bot, r), name=r["name"]) for r in bot],',
    '  "ghi_qua_hop_chon": list(c.GHI_QUA_HOP_CHON.get("zalo_bot_phu", ()))}',
    'u = sys.modules["frappe"].utils', 'u.get_url = getattr(u, "get_url", None) or (lambda *a, **k: "https://vagabond.test")',
    'from vagabond import kenh_zalo as kz',
    'ra["nhom_bot"] = kz.ds_nhom_chon(json.loads(doc["zalo_chat_moi"]), dong)',
    'sys.stdout.write(json.dumps(ra, ensure_ascii=False, default=str))'
  ].join('\n');
  return JSON.parse(cp.execFileSync('python3', ['-B', '-c', py, GOC], { encoding: 'utf8', maxBuffer: 1 << 26 }));
}

/* Dữ liệu thử thêm cho các màn trong báo cáo (bịa, cùng hình dạng máy chủ trả). */
var HAM_THAT = ['vagabond.ban_hang.cau_hinh_ban_hang', 'vagabond.bao_cao.danh_sach', 'vagabond.chuong.dem', 'vagabond.crm.tong_quan',
  'vagabond.don_dau_web.doc_cai_dat', 'vagabond.don_quay.danh_sach', 'vagabond.gioi_thieu.cua_toi', 'vagabond.hang_tang.dem_cho_duyet',
  'vagabond.hop_dong.danh_sach', 'vagabond.in_ngam.dinh_tuyen', 'vagabond.khuyen_mai.danh_muc', 'vagabond.khuyen_mai.ds_combo',
  'vagabond.khuyen_mai.ds_ctkm', 'vagabond.mua_vu.danh_sach', 'vagabond.nhan_banh.bang', 'vagabond.nhan_hang.danh_sach',
  'vagabond.nhap_sao_ke.danh_sach_tai_khoan', 'vagabond.tai_khoan.danh_sach', 'vagabond.tang_qua.danh_muc', 'vagabond.tang_qua.thu_boc_sdt',
  'vagabond.tra_ncc.ds_phieu', 'vagabond.tra_ncc.khoi_dong', 'vagabond.tru_kho_bu.dem_chua_tru_kho', 'vagabond.van_don.bo_loc',
  'vagabond.van_don.danh_sach', 'vagabond.van_don.ds_diem_pickup', 'vagabond.van_don.ds_shipper', 'vagabond.viec_can_lam.dem',
  'vagabond.xuat_ban.ds_phieu'];
function dungFix() {
  var CDL = layCdl();
  var that = JSON.parse(cp.execFileSync('python3', ['-B', path.join(__dirname, 'du_lieu_that.py'), GOC, JSON.stringify(HAM_THAT)], { encoding: 'utf8', maxBuffer: 1 << 26 }));
  var fix = {};
  Object.keys(that).forEach(function (k) { if (that[k].ok) fix[k] = { message: that[k].message }; });
  /* Vài màn cần bản ghi để hiện đúng phần đã báo (dữ liệu bịa). */
  fix['vagabond.van_don.bo_loc'] = { message: Object.assign({}, (fix['vagabond.van_don.bo_loc'] || {}).message, { so_thieu_the_gio: 3 }) };
  return Object.assign(fix, {
    'vagabond.cai_dat_loi.lay': { message: CDL },
    'vagabond.cai_dat_loi.ngan_hang': { message: [{ bin: '970422', ten: 'MB Bank', ma: 'MB' }, { bin: '970436', ten: 'Vietcombank', ma: 'VCB' }] }
  });
}

/* Mục: mã, nhóm, cách mở (biểu thức chạy trong vỏ app), bước bấm thêm, phép kiểm.
   kiem: 'emoji' (danh sách ký tự), 'gay' (chữ gợi ý của nút/nhãn bị xuống dòng hay ép),
   'nho' (chữ hay bộ chọn của vùng bấm dưới 44), 'dinh' (hai nút sát nhau), 'chu' (chữ dưới 13),
   'select' (ô chọn gốc của trình duyệt), 'co' (chữ phải KHÔNG còn), 'phai' (chữ phải có),
   'mau' (màu cũ trên chip, nút). */
var MAN = {
  bep: { mo: 'go(scrKitchen)' },
  cdl: { mo: 'go(scrCaiDatLoi)' },
  cdl_bh: { mo: 'go(scrCaiDatLoi)', buoc: [['chu', 'Bán hàng & thanh toán']] },
  cdl_nhom: { mo: 'cdlCss(); CDL.d = window.__cdl; cdlVeDong("zalo_nhom", 0, JSON.parse(JSON.stringify(window.__cdl.bang.zalo_nhom.dong[0])))' },
  cdl_loai: { mo: 'cdlCss(); CDL.d = window.__cdl; cdlVeDong("zalo_nhom", 0, JSON.parse(JSON.stringify(window.__cdl.bang.zalo_nhom.dong[0])))', buoc: [['sel', '[data-cdldchon="loai_tin"]']] },
  cdl_chude: { mo: 'cdlCss(); CDL.d = window.__cdl; cdlVeDong("zalo_nhom", 0, JSON.parse(JSON.stringify(window.__cdl.bang.zalo_nhom.dong[0])))', buoc: [['sel', '[data-cdldchon="chu_de"]']] },
  cdl_bot: { mo: 'cdlCss(); CDL.d = window.__cdl; cdlVeDong("zalo_nhom", 0, JSON.parse(JSON.stringify(window.__cdl.bang.zalo_nhom.dong[0])))', buoc: [['chu', 'Chọn nhóm đã nhắn bot']] },
  hd: { mo: 'go(scrHopDong)' },
  km: { mo: 'go(scrKhuyenMai)' },
  nbanh: { mo: 'go(scrNhanBanh)' },
  rcv: { mo: 'go(scrRecvList)' },
  kk: { mo: 'go(scrKkNew)' },
  sotay: { mo: 'go(scrSoTay)' },
  stock: { mo: 'go(scrStock)' },
  pos: { mo: 'cfgBanHang().then(function (c) { posQuay = c.quay[0]; go(scrPosQuay); })' },
  pos_mon: { mo: 'cfgBanHang().then(function (c) { posQuay = c.quay[0]; go(scrPosQuay); })', buoc: [['sel', '#posThem']] },
  hdtao: { mo: 'go(scrHdTao)' },
  mfg: { mo: 'go(scrMfgNew)' },
  vdtao: { mo: 'go(scrVdTao)' },
  xksi: { mo: 'go(scrXkSiList)' },
  xktra: { mo: 'go(scrXkTraList)' },
  rnd: { mo: 'go(scrRndNew)' },
  tq: { mo: 'go(scrTqSua)' },
  lich: { mo: 'go(scrLichChi)' },
  dm: { mo: 'go(scrDanhMuc)' },
  gvt: { mo: 'go(scrGiaVonTam)' },
  hhgt: { mo: 'go(scrHhgt)' },
  bt: { mo: 'go(scrBtLap)' },
  ph: { mo: 'go(scrPhLap)' },
  tdh: { mo: 'go(scrTuDongHoa)' },
  muavu: { mo: 'go(scrMuaVuDs)' },
  sk: { mo: 'go(scrNhapSaoKe)' },
  tk: { mo: 'go(scrTaiKhoan)' },
  dgq: { mo: 'go(scrDonGiaoQuay)' },
  vd: { mo: 'go(scrVanDon)' }
};
var MUC = [
  ['UI26', 'A', 'bep', 'emoji', ['⚠']], ['UI17', 'A', 'cdl', 'emoji', ['🛒', '🧾', '🛵', '⭐', '💬', '🌐', '🖨', '⚙', '📋']],
  ['UI34', 'A', 'hd', 'emoji', ['➕']], ['UI27', 'A', 'km', 'emoji', ['🤝']], ['UI28', 'A', 'km', 'emoji', ['🎫', '🧺', '📮', '📊']],
  ['UI29', 'A', 'km', 'emoji', ['🧾', '🍰', '🔁', '🎁', '🍬', '🏷', '📈', '⭐']], ['UI30', 'A', 'nbanh', 'emoji', ['📅', '🏬']],
  ['UI21', 'A', 'rcv', 'emoji', ['🔍', '📷']], ['UI37', 'A', 'kk', 'emoji', ['📅', '🏬', '🥚']], ['UI25', 'A', 'sotay', 'emoji', ['🔍']],
  ['UI20', 'A', 'cdl_bot', 'emoji', ['📷']], ['UI19', 'A', 'cdl_chude', 'emoji', ['📦', '🧑', '💳', '🎂', '🧾', '🌐', '🪑', '🚀', '🛠']],
  ['UI18', 'A', 'cdl_loai', 'emoji', ['ℹ', '✅', '🚨', '📊', '🚀']], ['UI22', 'A', 'stock', 'emoji', ['🏬']],
  ['UI23', 'A', 'stock', 'emoji', ['🔍', '📷']], ['UI24', 'A', 'stock', 'emoji', ['📊']],
  ['UI39', 'A', 'pos', 'emoji', ['📋', '✅']], ['UI40', 'A', 'pos', 'emoji', ['🕐']], ['UI41', 'A', 'pos', 'emoji', ['🖥']],
  ['UI42', 'A', 'pos', 'emoji', ['🏬', '🥡']], ['UI43', 'A', 'pos', 'emoji', ['🥡']], ['UI44', 'A', 'pos', 'emoji', ['💵', '🏦', '💳']],
  ['UI45', 'A', 'pos', 'emoji', ['🎫', '🎟']], ['UI46', 'A', 'pos', 'emoji', ['🧾']], ['UI47', 'A', 'pos_mon', 'emoji', ['📷']],
  ['UI33', 'A', 'hdtao', 'emoji', ['📅']], ['UI38', 'A', 'mfg', 'emoji', ['🧂', '🎂', '📷']], ['UI36', 'A', 'vdtao', 'emoji', ['📅']],
  ['UI31', 'A', 'xksi', 'emoji', ['🔍', '🟡', '🟢']], ['UI32', 'A', 'xktra', 'emoji', ['🔍', '🟡', '🟢']],
  ['UI35', 'A', 'rnd', 'emoji', ['🧪', '📅', '📝', '📷']],
  ['UI50', 'B', 'cdl_bh', 'gay', 'Đổi'], ['UI48', 'B', 'cdl_nhom', 'gay', 'Chọn tin nhận'], ['UI49', 'B', 'cdl_nhom', 'gay', 'Chọn nhóm đã nhắn bot'],
  ['UI51', 'B', 'tq', 'gay', 'Lưu và thêm khách tiếp theo'], ['UI52', 'B', 'lich', 'gay', 'Chọn nhà cung cấp'],
  ['UI62', 'C', 'cdl_bh', 'nho', '[role=switch], .cdl-tg, input[type=checkbox]'], ['UI60', 'C', 'dm', 'nho', 'Phần nâng cao'],
  ['UI56', 'C', 'gvt', 'nho', 'Món đang bán|Món thử|Tất cả'], ['UI57', 'C', 'hhgt', 'nho', '*chip'], ['UI55', 'C', 'km', 'nho', '*chip'],
  ['UI66', 'C', 'bt', 'dinh', 'Lưu nháp|Lưu và ghi sổ'], ['UI61', 'C', 'ph', 'nho', 'Mọi điểm bán'],
  ['UI53', 'C', 'rcv', 'nho', 'Quét|📷|camera'], ['UI54', 'C', 'stock', 'nho', 'Quét|📷|camera'],
  ['UI63', 'C', 'pos', 'nho', 'Bàn 1|Mang đi'], ['UI64', 'C', 'pos', 'nho', 'Chương trình|Nhập mã'], ['UI65', 'C', 'pos_mon', 'nho', 'Tất cả|Xong'],
  ['UI58', 'C', 'xksi', 'nho', '*chip'], ['UI59', 'C', 'xktra', 'nho', '*chip'],
  ['UI67', 'D', 'cdl', 'chu', ''], ['UI70', 'D', 'tdh', 'chu', ''], ['UI68', 'D', 'dm', 'chu', ''], ['UI71', 'D', 'hhgt', 'chu', ''],
  ['UI73', 'D', 'km', 'chu', ''], ['UI72', 'D', 'muavu', 'chu', ''], ['UI74', 'D', 'nbanh', 'chu', ''], ['UI75', 'D', 'sk', 'chu', ''],
  ['UI82', 'D', 'cdl_bot', 'chu', ''], ['UI76', 'D', 'stock', 'chu', ''], ['UI69', 'D', 'tk', 'chu', ''], ['UI81', 'D', 'pos', 'chu', ''],
  ['UI80', 'D', 'vdtao', 'chu', ''], ['UI77', 'D', 'xksi', 'chu', ''], ['UI78', 'D', 'xktra', 'chu', ''], ['UI79', 'D', 'rnd', 'chu', ''],
  ['UI86', 'E', 'dm', 'select', ''], ['UI87', 'E', 'sk', 'select', ''], ['UI85', 'E', 'tk', 'select', ''],
  ['UI83', 'E', 'cdl_nhom', 'co', 'zgr-0123456789012345'], ['UI84', 'E', 'cdl_nhom', 'phai', 'Bot chính|Máy tự chọn khi lưu|(số '],
  ['UI88', 'E', 'tq', 'co', 'Title riêng'], ['UI89', 'E', 'lich', 'phai', 'Số tiền mỗi tháng (đ)|Số tiền mỗi tháng (VNĐ)|đ/tháng'],
  ['UI95', 'F', 'dm', 'mau', ''], ['UI92', 'F', 'hhgt', 'mau', ''], ['UI90', 'F', 'km', 'mau', ''], ['UI91', 'F', 'stock', 'mau', ''],
  ['UI97', 'F', 'pos', 'mau', ''], ['UI98', 'F', 'pos_mon', 'mau', ''], ['UI93', 'F', 'xksi', 'mau', ''], ['UI94', 'F', 'xktra', 'mau', ''],
  ['UI96', 'F', 'dgq', 'mau', ''],
  /* Việc còn tồn PR #614 tự ghi: hàng chip lọc Vận đơn xếp dọc. */
  ['VD-CHIP', 'B', 'vd', 'doc', '']
];

/* Đo trong trang, phạm vi #vgb và hộp đang mở (.sh). */
function doMan() {
  var CU = ['rgb(15, 118, 110)', 'rgb(180, 83, 9)', 'rgb(146, 64, 14)', 'rgb(13, 148, 136)', 'rgb(124, 58, 237)', 'rgb(120, 53, 15)', 'rgb(17, 94, 89)'];
  var r = { emoji: [], gay: [], nho: [], dinh: [], chu: [], select: [], mau: [], chuMan: '', doc: null, gobot: [] };
  var phamVi = Array.prototype.slice.call(document.querySelectorAll('#vgb, .sh'));
  function hien(n) {
    var rc = n.getBoundingClientRect(), cs = getComputedStyle(n);
    return rc.width > 0 && rc.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none';
  }
  function chuCua(n) { return ((n.getAttribute && n.getAttribute('aria-label')) || n.textContent || '').replace(/\s+/g, ' ').trim(); }
  var GIU = 'textarea, input, [contenteditable], [data-giu-emoji], .bd-phai, svg, script, style, .uisr';
  var EMO = /[\u{1F000}-\u{1FAFF}←-⇿⌀-⏿☀-➿⬀-⯿]/gu;
  phamVi.forEach(function (goc) {
    r.chuMan += ' ' + (goc.innerText || '');
    var w = document.createTreeWalker(goc, NodeFilter.SHOW_TEXT);
    for (var n = w.nextNode(); n; n = w.nextNode()) {
      var cha = n.parentElement; if (!cha || cha.closest(GIU) || !hien(cha)) continue;
      var t = n.nodeValue; if (!/\S/.test(t)) continue;
      var m = t.match(EMO); if (m) r.emoji.push({ ky: m.join(''), chu: t.trim().slice(0, 40) });
      var fs = parseFloat(getComputedStyle(cha).fontSize);
      if (fs < 12.95 && !cha.closest('.uisr')) r.chu.push({ co: fs, chu: t.trim().slice(0, 40) });
    }
    /* Vùng bấm, xuống dòng, sát nhau. */
    var bam = Array.prototype.slice.call(goc.querySelectorAll('button, a[href], [role=button], [role=switch], [role=checkbox], .chip, .posc, input:not([type=hidden]), select, label.cdl-tg, .cdl-tg'));
    bam.forEach(function (b) {
      if (!hien(b)) return;
      var rc = b.getBoundingClientRect(), ten = chuCua(b) || b.id || b.className || b.tagName;
      if (b.type === 'checkbox' || b.type === 'radio') { var lb = b.closest('label'); if (lb) rc = lb.getBoundingClientRect(); }
      if (rc.width < 43.5 || rc.height < 43.5) r.nho.push({ chu: String(ten).slice(0, 40), w: Math.round(rc.width * 10) / 10, h: Math.round(rc.height * 10) / 10, the: b.tagName.toLowerCase() + (b.id ? '#' + b.id : '') + (typeof b.className === 'string' && b.className ? '.' + b.className.split(/\s+/)[0] : '') });
      var nhanNut = (b.textContent || '').replace(/\s+/g, ' ').trim();
      if (nhanNut && nhanNut.length <= 40 && (b.tagName === 'BUTTON' || b.matches('.chip,.posc,[role=button]'))) {
        var rg = document.createRange(); rg.selectNodeContents(b);
        var dong = {}; Array.prototype.forEach.call(rg.getClientRects(), function (x) { if (x.width > 1) dong[Math.round(x.top)] = 1; });
        var soDong = Object.keys(dong).length;
        var cs = getComputedStyle(b), lh = parseFloat(cs.lineHeight) || parseFloat(cs.fontSize) * 1.3;
        if (soDong > 1) r.gay.push({ chu: nhanNut, w: Math.round(rc.width * 10) / 10, dong: soDong });
      }
      if (b.tagName === 'SELECT') r.select.push({ ten: b.id || b.name || chuCua(b.closest('label') || b).slice(0, 30), so: b.options.length });
      var mau = [getComputedStyle(b).backgroundColor, getComputedStyle(b).color, getComputedStyle(b).borderTopColor];
      if (mau.some(function (x) { return CU.indexOf(x) >= 0; })) r.mau.push({ chu: String(ten).slice(0, 30), mau: mau.filter(function (x) { return CU.indexOf(x) >= 0; })[0] });
      if (/bot/i.test(b.getAttribute('data-cdld') || '') && b.tagName === 'INPUT') r.gobot.push(b.getAttribute('data-cdld'));
    });
    /* Nút cùng cha xếp dọc sát nhau (khe dưới 4). */
    var nut = Array.prototype.slice.call(goc.querySelectorAll('button, .btn')).filter(hien);
    for (var i = 0; i < nut.length; i++) for (var j = 0; j < nut.length; j++) {
      if (i === j) continue;
      var a = nut[i].getBoundingClientRect(), c = nut[j].getBoundingClientRect();
      var ngang = Math.min(a.right, c.right) - Math.max(a.left, c.left);
      if (ngang > 20 && c.top >= a.top && c.top - a.bottom < 4 && c.top - a.bottom > -2) r.dinh.push(chuCua(nut[i]).slice(0, 24) + ' | ' + chuCua(nut[j]).slice(0, 24));
    }
    /* Hàng chip lọc: các chip anh em xếp mỗi chip một hàng. */
    var hang = Array.prototype.slice.call(goc.querySelectorAll('.chips, [data-vdloc], .vdchips'));
    hang.forEach(function (h) {
      var ch = Array.prototype.slice.call(h.children).filter(hien);
      if (ch.length < 3) return;
      var tops = {}; ch.forEach(function (x) { tops[Math.round(x.getBoundingClientRect().top)] = 1; });
      if (Object.keys(tops).length === ch.length && r.doc === null) r.doc = ch.length;
    });
  });
  /* Ô nhập số bot (UI84): còn là ô gõ thì báo. */
  Array.prototype.forEach.call(document.querySelectorAll('#vgb input, .sh input'), function (x) {
    var nhan = (x.closest('.cdl-o, label, .fld, div') || x).textContent || '';
    if (/bot số|Gửi bằng bot/i.test(nhan) && hien(x)) r.gobot.push('ô gõ: ' + nhan.replace(/\s+/g, ' ').trim().slice(0, 40));
  });
  return r;
}

function phanXu(muc, d) {
  var kieu = muc[3], hint = muc[4];
  function co(ds, k) { return ds.filter(function (x) { return String(x.chu || x).indexOf(k) >= 0 || new RegExp(k).test(String(x.chu || x)); }); }
  if (!d) return { con: null, chi: 'không mở được màn' };
  if (kieu === 'emoji') {
    var thay = d.emoji.filter(function (e) { return hint.some(function (k) { return e.ky.indexOf(k) >= 0; }); });
    return { con: thay.length > 0, chi: thay.slice(0, 4) };
  }
  if (kieu === 'gay') { var g = d.gay.filter(function (x) { return x.chu.indexOf(hint) >= 0; }); var cm = d.chuMan.indexOf(hint) >= 0; return { con: cm ? g.length > 0 : null, chi: cm ? g : 'không thấy chữ "' + hint + '" trên màn' }; }
  if (kieu === 'nho') {
    var ds;
    if (hint === '*chip') ds = d.nho.filter(function (x) { return /chip|posc|button/.test(x.the) && x.h < 43.5; });
    else if (/^[\[.#]/.test(hint)) ds = d.nho.filter(function (x) { return hint.split(', ').some(function (s) { return x.the.indexOf(s.replace(/^[.#]/, '')) >= 0 || /checkbox|switch/.test(s) && /input/.test(x.the); }); });
    else {
      if (!hint.split('|').some(function (k) { return d.chuMan.indexOf(k) >= 0; }) && !/Quét/.test(hint)) return { con: null, chi: 'không thấy "' + hint + '" trên màn' };
      ds = d.nho.filter(function (x) { return hint.split('|').some(function (k) { return x.chu.indexOf(k) >= 0; }); });
    }
    return { con: ds.length > 0, chi: ds.slice(0, 6) };
  }
  if (kieu === 'dinh') { if (!hint.split('|').some(function (k) { return d.chuMan.indexOf(k) >= 0; })) return { con: null, chi: 'không thấy nút' }; var dd = d.dinh.filter(function (x) { return hint.split('|').some(function (k) { return x.indexOf(k) >= 0; }); }); return { con: dd.length > 0, chi: dd }; }
  if (kieu === 'chu') return { con: d.chu.length > 0, chi: d.chu.slice(0, 6) };
  if (kieu === 'select') return { con: d.select.length > 0, chi: d.select };
  if (kieu === 'co') return { con: d.chuMan.indexOf(hint) >= 0, chi: d.chuMan.indexOf(hint) >= 0 ? 'còn chữ "' + hint + '"' : '' };
  if (kieu === 'phai') return { con: !hint.split('|').some(function (k) { return d.chuMan.indexOf(k) >= 0; }), chi: '' };
  if (kieu === 'gobot') return { con: d.gobot.length > 0, chi: d.gobot };
  if (kieu === 'mau') return { con: d.mau.length > 0, chi: d.mau.slice(0, 6) };
  if (kieu === 'doc') return { con: d.doc !== null, chi: d.doc === null ? '' : d.doc + ' chip mỗi chip một hàng' };
  return { con: null, chi: 'chưa có phép kiểm' };
}

function themCua(src) {
  var i = src.lastIndexOf('})();');
  if (i < 0) throw new Error('Không thấy cuối vỏ app');
  return src.slice(0, i) + 'window.__vgbK = { chay: function (c) { return eval(c); } };\n' + src.slice(i);
}

function dauTrang() {
  var ver = fs.readFileSync(APP || path.join(CONG, 'js/app_bep.js'), 'utf8').match(/var APPVER = ['"](\d+)['"]/)[1];
  var ma = 'import sys; sys.path.insert(0, %r); from vagabond.giao_dien import dau_trang_html; sys.stdout.write(dau_trang_html(%d, ' + ver + '))';
  var r = cp.spawnSync('python3', ['-B', '-c', ma.replace('%r', JSON.stringify(GOC)).replace('%d', BAT ? 1 : 0)], { encoding: 'utf8' });
  if (r.status !== 0) throw new Error('Không lấy được đoạn head: ' + r.stderr);
  return r.stdout;
}

async function chay() {
  var pw;
  try { pw = require('playwright'); } catch (e) { try { pw = require('/opt/npm-tools/node_modules/playwright'); } catch (e2) { console.log('THIẾU Playwright'); process.exit(2); } }
  fs.mkdirSync(RA, { recursive: true });
  var FIX = dungFix();
  var DAU = dauTrang();
  var APPSRC = themCua(fs.readFileSync(APP || path.join(CONG, 'js/app_bep.js'), 'utf8'));
  var user = DL.tra('/api/method/frappe.auth.get_logged_user', {}, 'quan-tri').message;
  var html = '<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><title>Rà</title>' + DAU +
    '<script>window.frappe={csrf_token:"thu",session:{user:' + JSON.stringify(user) + '},boot:{}};</script></head><body><div id="vgb"></div>' +
    '<script>window.addEventListener("load",function(){var s=document.createElement("script");s.src="/assets/vagabond/js/app_bep.js";document.body.appendChild(s);});</script></body></html>';
  var muc = CHON ? MUC.filter(function (m) { return CHON.split(',').indexOf(m[0]) >= 0; }) : MUC;
  var manCan = []; muc.forEach(function (m) { if (manCan.indexOf(m[2]) < 0) manCan.push(m[2]); });
  var trinh = await pw[MAY].launch();
  var doDuoc = {}, thieu = {}, loiJs = {};
  for (var k = 0; k < manCan.length; k++) {
    var ten = manCan[k], cach = MAN[ten];
    var ctx = await trinh.newContext({ viewport: { width: KHUNG.w, height: KHUNG.h }, deviceScaleFactor: 1, locale: 'vi-VN', timezoneId: 'Asia/Ho_Chi_Minh',
      isMobile: MAY !== 'firefox' && KHUNG.w < 700, hasTouch: KHUNG.w < 700, reducedMotion: 'reduce' });
    var trang = await ctx.newPage();
    var loi = [];
    trang.on('pageerror', function (e) { loi.push(String(e.message || e).split('\n')[0]); });
    await ctx.route('**/*', function (route) {
      var u = new URL(route.request().url());
      if (u.origin !== ORIGIN) return route.abort();
      var p = decodeURIComponent(u.pathname);
      if (p.indexOf('/api/') === 0) {
        var than = {};
        try { than = JSON.parse(route.request().postData() || '{}'); } catch (e) { }
        var m = p.replace('/api/method/', '');
        var kq = FIX[m] !== undefined ? FIX[m] : DL.tra(p, than, 'quan-tri');
        if (kq === undefined) { thieu[m] = (thieu[m] || 0) + 1; kq = { message: null }; }
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(kq) });
      }
      if (p === '/assets/vagabond/js/app_bep.js') return route.fulfill({ status: 200, contentType: 'text/javascript; charset=utf-8', body: APPSRC });
      if (p.indexOf('/assets/vagabond/') === 0) {
        var tep = path.join(CONG, p.slice('/assets/vagabond/'.length));
        if (fs.existsSync(tep)) return route.fulfill({ status: 200, body: fs.readFileSync(tep), contentType: { '.js': 'text/javascript', '.css': 'text/css', '.woff2': 'font/woff2', '.svg': 'image/svg+xml' }[path.extname(tep)] || 'application/octet-stream' });
        return route.fulfill({ status: 404, body: '' });
      }
      if (/\.(png|jpe?g|webp|gif|ico)$/i.test(p) || p.indexOf('/files/') === 0) return route.fulfill({ status: 200, contentType: 'image/png', body: Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64') });
      if (p === '/sw.js') return route.fulfill({ status: 404, body: '' });
      return route.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: html });
    });
    await trang.addInitScript(function (cdl) {
      window.__cdl = cdl;
      try { Object.defineProperty(navigator, 'serviceWorker', { get: function () { return undefined; } }); } catch (e) { }
      /* Hàm chưa có dữ liệu thử: "rỗng" đọc trường nào cũng được (như quet_man.cjs). */
      var MANG = ['map', 'filter', 'forEach', 'reduce', 'some', 'every', 'find', 'findIndex', 'indexOf', 'includes', 'slice', 'concat', 'join', 'sort', 'flatMap', 'flat'];
      var XU = { get: function (t, k) {
        if (k === 'then' || k === 'toJSON') return undefined;
        if (k === Symbol.toPrimitive) return function (h) { return h === 'number' ? 0 : ''; };
        if (k === 'length') return 0;
        if (k === Symbol.iterator) return [][Symbol.iterator].bind([]);
        if (typeof k === 'string' && MANG.indexOf(k) >= 0) return Array.prototype[k].bind([]);
        if (k === 'toString' || k === 'valueOf') return function () { return ''; };
        return rong(); }, has: function () { return false; }, apply: function () { return rong(); } };
      function rong() { return new Proxy(function () {}, XU); }
      var parse = JSON.parse;
      JSON.parse = function (t, f) { var o = parse.call(JSON, t, f); if (o && typeof o === 'object' && o.message === null && Object.keys(o).length === 1) o.message = rong(); return o; };
    }, FIX['vagabond.cai_dat_loi.lay'].message);
    var d = null;
    try {
      await trang.goto(ORIGIN + '/bep');
      await trang.waitForSelector('.gwrap', { timeout: 15000 });
      /* Hộp Zalo của Cài đặt lõi dùng danh mục chung nạp riêng như trang Desk (cai_dat_loi_chung.js). */
      if (/^cdl/.test(ten)) await trang.addScriptTag({ url: ORIGIN + '/assets/vagabond/js/cai_dat_loi_chung.js' });
      await trang.evaluate(function (c) { return window.__vgbK.chay(c); }, cach.mo);
      await trang.waitForTimeout(900);
      for (var b of cach.buoc || []) {
        if (b[0] === 'sel') await trang.click(b[1], { timeout: 4000 });
        else await trang.getByText(b[1], { exact: false }).first().click({ timeout: 4000 });
        await trang.waitForTimeout(700);
      }
      await trang.evaluate(function () { return document.fonts.ready; });
      d = await trang.evaluate(doMan);
      if (process.env.RA_JS) console.log('JS ' + ten + ': ' + JSON.stringify(await trang.evaluate(process.env.RA_JS)));
      if (process.env.RA_GO) console.log('GỠ ' + ten + ': ' + JSON.stringify(await trang.evaluate(function (q) { var e = document.querySelector(q); if (!e) return null; var c = getComputedStyle(e); return { bs: c.boxSizing, b: c.borderTopWidth, w: c.width, h: c.height, cls: e.className, rule: Array.prototype.slice.call(document.styleSheets).map(function (x) { try { return Array.prototype.filter.call(x.cssRules, function (r) { return r.selectorText && e.matches(r.selectorText.replace(/::?after|::?before/g, '')); }).map(function (r) { return r.cssText.slice(0, 140); }); } catch (er) { return []; } }).reduce(function (a, b) { return a.concat(b); }, []) }; }, process.env.RA_GO)));
      await trang.screenshot({ path: path.join(RA, ten + '.png'), fullPage: true });
    } catch (e) { loi.unshift('mở: ' + String(e.message || e).split('\n')[0]); }
    doDuoc[ten] = d; loiJs[ten] = loi.slice(0, 3);
    await ctx.close();
  }
  await trinh.close();
  var bang = muc.map(function (m) {
    var x = phanXu(m, doDuoc[m[2]]);
    return { ma: m[0], loai: m[1], man: m[2], con: x.con, chi: x.chi };
  });
  var con = bang.filter(function (b) { return b.con; }), khongRo = bang.filter(function (b) { return b.con === null; });
  bang.forEach(function (b) { console.log((b.con === null ? 'KHÔNG RÕ' : b.con ? 'CÒN    ' : 'KHÉP   ') + ' ' + b.ma + ' ' + b.loai + ' ' + b.man + (b.con !== false ? '  ' + JSON.stringify(b.chi).slice(0, 160) : '')); });
  Object.keys(loiJs).forEach(function (k) { if (loiJs[k].length) console.log('LỖI ' + k + ': ' + loiJs[k].join(' | ').slice(0, 200)); });
  fs.writeFileSync(path.join(RA, 'ra-muc.json'), JSON.stringify({ khung: KHUNG, may: MAY, bang: bang, do: doDuoc, thieu: thieu, loi: loiJs }, null, 1));
  console.log(bang.length + ' mục: khép ' + (bang.length - con.length - khongRo.length) + ', còn ' + con.length + ', không rõ ' + khongRo.length + '. Thiếu dữ liệu thử: ' + Object.keys(thieu).length + ' hàm.');
  process.exit(con.length || khongRo.length ? 1 : 0);
}
chay().catch(function (e) { console.error(e); process.exit(1); });

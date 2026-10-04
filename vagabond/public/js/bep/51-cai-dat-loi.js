/* ---------- 51. Cài đặt lõi và API (v570) ----------
 *
 * Anh Việt 04/10/2026: đưa trang Vagabond Settings thành một ô trong phân hệ Cài
 * đặt của app, *"sau này anh chỉ việc điền trên app. Mỗi lần em thêm gì trong
 * trang này thì phải thêm cả trên bản desk và bản app."* Tên ô anh đặt: "Cài đặt
 * lõi và API".
 *
 * Màn này KHÔNG giữ danh sách ô riêng. Tab, mục, ô, nhãn, mô tả, kiểu ô đều do
 * máy chủ đọc từ doctype rồi gửi xuống (vagabond.cai_dat_loi.lay), nên thêm ô vào
 * trang Desk là màn này tự có. Chip tình trạng, ô tìm, thẻ tóm tắt, nhãn loại tin
 * Zalo, tìm ngân hàng dùng chung tệp /assets/vagabond/js/cai_dat_loi_chung.js với
 * Desk.
 *
 * Chỉ quản trị mở được (máy chủ kiểm lại). Khoá bí mật không bao giờ xuống máy:
 * chỉ biết đã khai hay chưa, muốn đổi thì gõ khoá mới. Lưu đi qua doc.save() trên
 * máy chủ, nên mọi kiểm tra của Cài đặt chạy y như bấm Lưu trên Desk.
 */
var CDL = { d: null, thay: {}, xoaKhoa: {}, bang: {}, bangDoi: {}, nganHang: null };

var CDL_IC = {
  tab_ban_hang: '🛒', tab_ke_toan: '🧾', tab_giao_hang: '🛵', tab_khach_hang: '⭐',
  tab_tin_nhan: '💬', tab_web: '🌐', tab_thiet_bi: '🖨️', tab_du_lieu_app: '📋'
};
/* Thẻ tóm tắt dữ liệu app tự ghi -> màn sửa riêng trên app (vgbGo). Đường Desk
   trong tệp chung là đường web; trên app thì mở thẳng màn bằng mã. */
var CDL_MAN = {
  '/tai-khoan-ke-toan': 'CDTK', '/diem-ban': 'CDDB', '/phuong-thuc-thanh-toan': 'CDPT',
  '/may-in': 'CDMI', '/mau-in': 'CDMU', '/quyen-quay': 'CDQQ', '/kpi-bang-chi-tieu': 'KPICD',
  '/phan-he-cai-dat': 'PH:KHAC'
};

function cdlNapChung() {
  if (typeof VGB_CD !== 'undefined' && VGB_CD && VGB_CD.tinhTrang) return Promise.resolve();
  return inNapJs('/assets/vagabond/js/cai_dat_loi_chung.js?v=' + APPVER);
}

function cdlSoThay() {
  return Object.keys(CDL.thay).length + Object.keys(CDL.xoaKhoa).length + Object.keys(CDL.bangDoi).length;
}

/* Giá trị hiện tại để vẽ: giá trị máy chủ đè bằng các ô đang sửa dở. Khoá bí
   mật đổi thành '*' khi đã khai để phép chip tình trạng dùng chung với Desk. */
function cdlDoc() {
  var g = (CDL.d && CDL.d.gia_tri) || {}, ra = {};
  Object.keys(g).forEach(function (k) {
    var v = g[k];
    ra[k] = (v && typeof v === 'object' && 'da_khai' in v) ? (v.da_khai ? '*' : '') : v;
  });
  Object.keys(CDL.thay).forEach(function (k) {
    ra[k] = cdlLaKhoa(k) ? (CDL.thay[k] ? '*' : ra[k]) : CDL.thay[k];
  });
  Object.keys(CDL.xoaKhoa).forEach(function (k) { ra[k] = ''; });
  return ra;
}

function cdlO(fn) {
  var ra = null;
  ((CDL.d && CDL.d.bo_cuc) || []).forEach(function (t) {
    t.muc.forEach(function (m) { m.o.forEach(function (o) { if (o.fn === fn) ra = { o: o, muc: m, tab: t }; }); });
  });
  return ra;
}
function cdlLaKhoa(fn) { var x = cdlO(fn); return !!(x && x.o.kieu === 'Password'); }

function cdlDatThay(fn, v) {
  var goc = ((CDL.d && CDL.d.gia_tri) || {})[fn];
  if (cdlLaKhoa(fn)) {
    if (String(v || '').trim()) CDL.thay[fn] = v; else delete CDL.thay[fn];
    delete CDL.xoaKhoa[fn];
    return;
  }
  var a = goc == null ? '' : String(goc), b = v == null ? '' : String(v);
  if (a === b) delete CDL.thay[fn]; else CDL.thay[fn] = v;
}

function cdlCss() {
  if (document.getElementById('cdl-css')) return;
  var s = document.createElement('style'); s.id = 'cdl-css';
  s.textContent =
    '.cdl-chip{display:inline-flex;align-items:center;gap:6px;min-height:36px;padding:4px 11px;border-radius:999px;font-size:13px;font-weight:500;border:1px solid;cursor:pointer;background:#fff}' +
    '.cdl-chip i{width:7px;height:7px;border-radius:50%;flex:none}' +
    '.cdl-ok{background:#e9f7ef;color:#1e6b3c;border-color:#c6ead4}.cdl-ok i{background:#22a05a}' +
    '.cdl-no{background:#f3f4f6;color:#5b636b;border-color:#e2e5e8}.cdl-no i{background:#a3abb2}' +
    '.cdl-off{background:#fff6e5;color:#8a5a00;border-color:#f6dfaa}.cdl-off i{background:#e0a100}' +
    '.cdl-err{background:#fdecec;color:#a42424;border-color:#f6caca}.cdl-err i{background:#d93636}' +
    '.cdl-chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}' +
    '.cdl-tab{display:flex;align-items:center;gap:12px;min-height:60px;padding:8px 14px;cursor:pointer}' +
    '.cdl-tab b{display:block;font-size:15px}.cdl-tab small{display:block;font-size:13px;color:#6b737b}' +
    '.cdl-row{display:flex;align-items:center;gap:12px;min-height:56px;padding:8px 0;border-top:1px dashed #eceef0}' +
    '.cdl-row:first-child{border-top:0}' +
    '.cdl-x{flex:1;min-width:0}.cdl-x b{display:block;font-size:14px;font-weight:500}' +
    '.cdl-x small{display:block;font-size:13px;color:#6b737b;line-height:1.4}' +
    '.cdl-tg{width:48px;height:30px;border-radius:15px;background:#cfd6db;position:relative;flex:none;border:0;cursor:pointer}' +
    '.cdl-tg:after{content:"";position:absolute;width:24px;height:24px;border-radius:50%;background:#fff;top:3px;left:3px;box-shadow:0 1px 2px rgba(0,0,0,.2)}' +
    '.cdl-tg.on{background:#22a05a}.cdl-tg.on:after{left:21px}' +
    '.cdl-f{padding:8px 0;border-top:1px dashed #eceef0}.cdl-f:first-child{border-top:0}' +
    '.cdl-f label{display:block;font-size:13px;color:#4b545c;margin-bottom:5px}' +
    '.cdl-f .tin,.cdl-f textarea{width:100%;min-height:44px;font-size:15px}' +
    '.cdl-f textarea{border:1px solid #dfe3ea;border-radius:10px;padding:10px 12px;font-family:inherit;resize:vertical}' +
    '.cdl-f .mono{font-family:ui-monospace,Menlo,monospace;font-size:13px}' +
    '.cdl-mo{font-size:13px;color:#6b737b;line-height:1.4;margin-top:4px}' +
    '.cdl-val{min-height:44px;display:flex;align-items:center;gap:8px;background:#f4f5f6;border-radius:10px;padding:6px 12px;font-size:14px;word-break:break-all}' +
    '.cdl-lnk{color:#0a7ea4;font-size:14px;font-weight:600;min-height:44px;display:inline-flex;align-items:center;padding:0 6px;background:none;border:0;cursor:pointer}' +
    '.cdl-seg{display:flex;flex-wrap:wrap;gap:6px}' +
    '.cdl-seg button{min-height:44px;padding:0 13px;border-radius:10px;border:1px solid #d8dde1;background:#fff;font-size:14px;color:#1f272e}' +
    '.cdl-seg button.on{background:#171717;color:#fff;border-color:#171717}' +
    '.cdl-muc{font-weight:600;font-size:14px;display:flex;align-items:center;gap:8px;min-height:44px}' +
    '.cdl-grp{border:1px solid #e2e6e9;border-radius:12px;padding:10px 12px;margin-top:8px;cursor:pointer;min-height:56px}' +
    '.cdl-kq{display:flex;flex-direction:column;align-items:flex-start;min-height:52px;padding:8px 4px;border-top:1px solid #eef0f2;cursor:pointer}' +
    '.cdl-kq b{font-size:14px}.cdl-kq small{font-size:13px;color:#6b737b}' +
    '.cdl-sang{box-shadow:0 0 0 2px #0FB5CE;border-radius:10px}';
  document.head.appendChild(s);
}

function cdlChip(tr, chu, attr) {
  return '<span class="cdl-chip cdl-' + tr + '"' + (attr || '') + '><i></i>' + h(chu) + '</span>';
}

/* Mở từ phân hệ Cài đặt. Còn thay đổi chưa lưu thì GIỮ, không đọc lại đè mất. */
async function scrCaiDatLoi() {
  cdlCss();
  if (!CDL.d || !cdlSoThay()) {
    frame('Cài đặt lõi và API', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc cài đặt...</div></div>');
    try {
      var kq = await Promise.all([api('vagabond.cai_dat_loi.lay', {}), cdlNapChung()]);
      cdlNhan(kq[0]);
    } catch (e) {
      frame('Cài đặt lõi và API', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
      return;
    }
  }
  cdlVeTong();
}

function cdlNhan(d) {
  CDL.d = d; CDL.thay = {}; CDL.xoaKhoa = {}; CDL.bangDoi = {}; CDL.bang = {};
  Object.keys(d.bang || {}).forEach(function (k) {
    CDL.bang[k] = (d.bang[k].dong || []).map(function (r) { return Object.assign({}, r); });
  });
}

function cdlChiMuc() {
  var ds = [];
  (CDL.d.bo_cuc || []).forEach(function (t) {
    t.muc.forEach(function (m) {
      m.o.forEach(function (o) { ds.push({ fn: o.fn, nhan: o.nhan, mo: o.mo || '', tab: t.nhan, muc: m.nhan, tabFn: t.fn }); });
    });
  });
  return ds;
}

function cdlFooter() {
  var n = cdlSoThay();
  return '<button class="btn" id="cdlLuu" style="margin:0;width:100%"' + (n ? '' : ' disabled') + '>' +
    (n ? 'Lưu ' + n + ' thay đổi' : 'Chưa có thay đổi') + '</button>';
}

function cdlGanLuu() {
  var b = document.getElementById('cdlLuu');
  if (b) b.onclick = cdlLuu;
}

function cdlVeTong() {
  var doc = cdlDoc();
  var tt = VGB_CD.tinhTrang(doc);
  var html = '<input class="tin" id="cdlTim" placeholder="Tìm cài đặt: mã QR, Ahamove, máy in..." style="width:100%;min-height:46px;margin-bottom:6px">' +
    '<div id="cdlKq"></div>' +
    '<div class="card" style="padding:12px 14px"><div style="font-weight:600;font-size:15px">Tình trạng kết nối</div>' +
    '<div class="cdl-mo">Xanh là đã khai đủ, xám là chưa khai, vàng là đã khai nhưng đang tắt, đỏ là vừa có sự cố. Bấm một ô để mở đúng phần đó.</div>' +
    '<div class="cdl-chips">' + tt.map(function (t) {
      return cdlChip(t.trang, t.ten + (t.trang === 'err' ? ': ' + t.ghi : ''), ' data-cdltoi="' + h(t.toi) + '" role="button"');
    }).join('') + '</div></div>';
  html += (CDL.d.bo_cuc || []).map(function (t) {
    var so = 0; t.muc.forEach(function (m) { so += m.o.length; });
    var phu = t.fn === 'tab_du_lieu_app' ? 'Chỉ xem, mở màn sửa riêng' : t.muc.length + ' mục · ' + so + ' ô';
    return '<div class="card cdl-tab" data-cdltab="' + h(t.fn) + '" style="padding:8px 14px"><span style="font-size:20px">' + (CDL_IC[t.fn] || '⚙️') +
      '</span><span class="cdl-x"><b>' + h(t.nhan) + '</b><small>' + h(phu) + '</small></span><span style="color:#9aa1a8">&#8250;</span></div>';
  }).join('');
  var b = frame('Cài đặt lõi và API', html, { footer: cdlFooter() });
  cdlGanLuu();
  var index = cdlChiMuc();
  b.onclick = function (e) {
    var t = e.target.closest('[data-cdltab]');
    if (t) return cdlMoTab(t.getAttribute('data-cdltab'));
    var c = e.target.closest('[data-cdltoi]');
    if (c) return cdlToiO(c.getAttribute('data-cdltoi'));
    var k = e.target.closest('[data-cdlkq]');
    if (k) return cdlToiO(k.getAttribute('data-cdlkq'));
  };
  b.oninput = function (e) {
    if (!e.target || e.target.id !== 'cdlTim') return;
    var q = e.target.value || '';
    var kq = VGB_CD.timTruong(q, index);
    document.getElementById('cdlKq').innerHTML = kq.length
      ? '<div class="card" style="padding:4px 12px">' + kq.map(function (x) {
          return '<div class="cdl-kq" data-cdlkq="' + h(x.fn) + '"><b>' + h(x.nhan) + '</b><small>' + h(x.tab) + ' › ' + h(x.muc) + '</small></div>';
        }).join('') + '</div>'
      : (q.trim() ? '<div class="cdl-mo" style="padding:4px 4px 10px">Không thấy cài đặt nào khớp.</div>' : '');
  };
}

function cdlToiO(fn) {
  var x = cdlO(fn);
  if (!x) {
    /* Ô thuộc một bảng con (ví dụ nhóm Zalo) hoặc mục ẩn: mở tab có bảng đó. */
    var tab = null;
    (CDL.d.bo_cuc || []).forEach(function (t) { t.muc.forEach(function (m) { if (m.fn === fn) tab = t.fn; }); });
    if (tab) return cdlMoTab(tab);
    return;
  }
  cdlMoTab(x.tab.fn, fn);
}

function cdlMoTab(fnTab, oToi) {
  go(function () { cdlVeTab(fnTab, oToi); });
}

function cdlVeTab(fnTab, oToi) {
  var t = null;
  (CDL.d.bo_cuc || []).forEach(function (x) { if (x.fn === fnTab) t = x; });
  if (!t) return cdlVeTong();
  var doc = cdlDoc();
  var ttMuc = VGB_CD.tinhTrangMuc(doc);
  var html = t.muc.map(function (m) {
    var mo = (oToi && m.o.some(function (o) { return o.fn === oToi; })) || !m.gon || CDL['mo_' + m.fn];
    var dau = '<div class="cdl-muc"' + (m.gon ? ' data-cdlgon="' + h(m.fn) + '" role="button" style="cursor:pointer"' : '') + '>' +
      (m.gon ? (mo ? '▾ ' : '▸ ') : '') + h(m.nhan || '') +
      (ttMuc[m.fn] ? ' ' + cdlChip(ttMuc[m.fn].trang, ttMuc[m.fn].ghi) : '') + '</div>';
    return '<div class="card" style="padding:10px 14px">' + dau +
      (m.mo && mo ? '<div class="cdl-mo" style="margin-bottom:6px">' + h(m.mo) + '</div>' : '') +
      (mo ? m.o.map(function (o) { return cdlVeO(o, doc); }).join('') : '') + '</div>';
  }).join('');
  var b = frame(t.nhan, html, { footer: cdlFooter() });
  cdlGanLuu();
  if (oToi) {
    var el = document.getElementById('cdl-o-' + oToi);
    if (el) { el.className = (el.className || '') + ' cdl-sang'; if (el.scrollIntoView) el.scrollIntoView({ block: 'center' }); }
  }
  b.onclick = function (e) { cdlBam(e, fnTab); };
  b.oninput = function (e) {
    var el = e.target, fn = el && el.getAttribute && el.getAttribute('data-cdlo');
    if (!fn) return;
    cdlDatThay(fn, el.value);
    cdlCapNhatNut();
  };
}

function cdlCapNhatNut() {
  var b = document.getElementById('cdlLuu');
  if (!b) return;
  var n = cdlSoThay();
  b.disabled = !n;
  b.textContent = n ? 'Lưu ' + n + ' thay đổi' : 'Chưa có thay đổi';
}

function cdlVeO(o, doc) {
  var v = doc[o.fn];
  var mo = o.mo ? '<div class="cdl-mo">' + h(o.mo) + '</div>' : '';
  var id = ' id="cdl-o-' + h(o.fn) + '"';
  if (o.fn === 'html_du_lieu_app') return cdlVeTomTat(doc);
  if (o.kieu === 'HTML') return '';
  if (o.kieu === 'Table') return '<div class="cdl-f"' + id + '>' + cdlVeBang(o) + '</div>';
  if (o.kieu === 'Check') {
    var bat = parseInt(v, 10) === 1;
    return '<div class="cdl-row"' + id + '><div class="cdl-x"><b>' + h(o.nhan) + '</b>' + (o.mo ? '<small>' + h(o.mo) + '</small>' : '') + '</div>' +
      (o.chi_doc ? cdlChip(bat ? 'ok' : 'no', bat ? 'Bật' : 'Tắt')
        : '<button class="cdl-tg' + (bat ? ' on' : '') + '" data-cdlbat="' + h(o.fn) + '" aria-label="' + h(o.nhan) + '"></button>') + '</div>';
  }
  var nhan = '<label>' + h(o.nhan) + (o.bat_buoc ? ' *' : '') + '</label>';
  if (o.kieu === 'Password') {
    var co = v && String(v).trim() !== '';
    var dangGo = Object.prototype.hasOwnProperty.call(CDL.thay, o.fn) || CDL['go_' + o.fn];
    return '<div class="cdl-f"' + id + '>' + nhan +
      '<div class="cdl-val">' + cdlChip(co ? 'ok' : 'no', co ? 'Đã khai' : 'Chưa khai') +
      (o.chi_doc ? '' : '<span style="margin-left:auto"></span><button class="cdl-lnk" data-cdldoikhoa="' + h(o.fn) + '">' + (co ? 'Đổi khoá' : 'Khai khoá') + '</button>' +
        (co ? '<button class="cdl-lnk" data-cdlgokhoa="' + h(o.fn) + '" style="color:#a42424">Gỡ</button>' : '')) + '</div>' +
      (dangGo ? '<input class="tin" type="password" autocomplete="new-password" data-cdlo="' + h(o.fn) + '" placeholder="Dán khoá mới vào đây" value="' + h(CDL.thay[o.fn] || '') + '" style="margin-top:6px">' : '') +
      '<div class="cdl-mo">Khoá bí mật không hiện lên máy. Muốn đổi thì gõ khoá mới.' + (o.mo ? ' ' + h(o.mo) : '') + '</div></div>';
  }
  if (o.chi_doc) {
    var dai = String(v == null ? '' : v);
    var ma = o.kieu === 'Code' || o.kieu === 'Long Text';
    return '<div class="cdl-f"' + id + '>' + nhan + '<div class="cdl-val' + (ma ? ' mono' : '') + '" style="white-space:pre-wrap">' +
      (dai ? h(dai.length > 1200 ? dai.slice(0, 1200) + '…' : dai) : '<span style="color:#9aa1a8">Trống</span>') + '</div>' + mo + '</div>';
  }
  if (o.fn === 'ngan_hang_bin') {
    var nh = CDL.nganHang ? VGB_CD.nganHangTheoBin(CDL.nganHang, v) : null;
    return '<div class="cdl-f"' + id + '>' + nhan + '<div class="cdl-val">' +
      (nh ? cdlChip('ok', nh.ten) : (v ? cdlChip('err', 'Mã BIN ' + v + ' chưa có trong danh mục') : cdlChip('no', 'Chưa chọn'))) +
      '<span style="margin-left:auto"></span><button class="cdl-lnk" data-cdlnganhang="1">Đổi</button></div>' + mo + '</div>';
  }
  if (o.kieu === 'Select') {
    var nhanChon = VGB_CD.NHAN_CHON[o.fn];
    var cac = nhanChon || String(o.tuy_chon || '').split('\n').map(function (x) { return [x, x || 'Không chọn']; });
    return '<div class="cdl-f"' + id + '>' + nhan + '<div class="cdl-seg">' + cac.map(function (p) {
      return '<button class="' + (String(v == null ? '' : v) === p[0] ? 'on' : '') + '" data-cdlchon="' + h(o.fn) + '" data-v="' + h(p[0]) + '">' + h(p[1]) + '</button>';
    }).join('') + '</div>' + mo + '</div>';
  }
  if (o.kieu === 'Link') {
    return '<div class="cdl-f"' + id + '>' + nhan + '<div class="cdl-val">' +
      (v ? h(v) : '<span style="color:#9aa1a8">Chưa chọn</span>') +
      '<span style="margin-left:auto"></span><button class="cdl-lnk" data-cdllk="' + h(o.fn) + '">Chọn</button></div>' + mo + '</div>';
  }
  var giaTri = v == null ? '' : String(v);
  if (o.kieu === 'Small Text' || o.kieu === 'Text' || o.kieu === 'Long Text' || o.kieu === 'Code') {
    return '<div class="cdl-f"' + id + '>' + nhan + '<textarea rows="3" data-cdlo="' + h(o.fn) + '"' +
      (o.kieu === 'Code' ? ' class="mono"' : '') + '>' + h(giaTri) + '</textarea>' + mo + '</div>';
  }
  var kieuNhap = { Int: 'number', Float: 'number', Currency: 'number', Percent: 'number', Date: 'date', Datetime: 'datetime-local', Time: 'time' }[o.kieu] || 'text';
  if (kieuNhap === 'datetime-local') giaTri = giaTri.replace(' ', 'T').slice(0, 16);
  return '<div class="cdl-f"' + id + '>' + nhan + '<input class="tin" type="' + kieuNhap + '"' +
    (kieuNhap === 'number' ? ' inputmode="decimal" step="any"' : '') + ' data-cdlo="' + h(o.fn) + '" value="' + h(giaTri) + '">' + mo + '</div>';
}

/* Thẻ tóm tắt dữ liệu app tự ghi: cùng hàm VGB_CD.tomTat với Desk, chỉ khác
   nút: Desk mở đường web, app mở thẳng màn sửa bằng mã (CDL_MAN). */
function cdlVeTomTat(doc) {
  var t = VGB_CD.tomTat(doc);
  var nut = function (d) {
    return CDL_MAN[d] ? '<button class="cdl-lnk" data-cdlman="' + h(CDL_MAN[d]) + '">Sửa ở màn riêng ›</button>' : '';
  };
  return t.the.map(function (c) {
    return '<div class="cdl-grp"><b style="font-size:14px">' + h(c.ten) + '</b><div class="cdl-mo">' +
      (c.loi ? cdlChip('err', c.phu) : h(c.phu || '')) + '</div>' +
      (c.dong || []).map(function (r) {
        return '<div class="cdl-row" style="min-height:40px"><div class="cdl-x"><b>' + h(r.trai || '') + '</b><small>' + h(r.giua || '') + '</small></div>' + cdlChip(r.trang, r.nhan) + '</div>';
      }).join('') +
      (c.con ? '<div class="cdl-mo">và ' + c.con + ' tài khoản, điểm bán nữa. Xem đủ ở màn riêng.</div>' : '') +
      (c.chip && c.chip.length ? '<div class="cdl-chips">' + c.chip.map(function (x) { return cdlChip('no', x); }).join('') + '</div>' : '') +
      nut(c.duong) + '</div>';
  }).join('') + t.dong.map(function (r) {
    return '<div class="cdl-row"><div class="cdl-x"><b>' + h(r.ten) + '</b><small>' + (r.loi ? '' : h(r.ghi || '')) + '</small></div>' +
      (r.loi ? cdlChip('err', r.ghi) : '') + nut(r.duong) + '</div>';
  }).join('');
}

function cdlBam(e, fnTab) {
  var el;
  if ((el = e.target.closest('[data-cdlman]'))) return vgbGo(el.getAttribute('data-cdlman'));
  if ((el = e.target.closest('[data-cdlgon]'))) {
    var k = 'mo_' + el.getAttribute('data-cdlgon'); CDL[k] = !CDL[k]; return cdlVeTab(fnTab);
  }
  if ((el = e.target.closest('[data-cdlbat]'))) {
    var fn = el.getAttribute('data-cdlbat');
    var doc = cdlDoc();
    cdlDatThay(fn, parseInt(doc[fn], 10) === 1 ? 0 : 1);
    return cdlVeTab(fnTab);
  }
  if ((el = e.target.closest('[data-cdlchon]'))) {
    cdlDatThay(el.getAttribute('data-cdlchon'), el.getAttribute('data-v'));
    return cdlVeTab(fnTab);
  }
  if ((el = e.target.closest('[data-cdldoikhoa]'))) {
    CDL['go_' + el.getAttribute('data-cdldoikhoa')] = 1; delete CDL.xoaKhoa[el.getAttribute('data-cdldoikhoa')];
    return cdlVeTab(fnTab, el.getAttribute('data-cdldoikhoa'));
  }
  if ((el = e.target.closest('[data-cdlgokhoa]'))) {
    var f2 = el.getAttribute('data-cdlgokhoa');
    return confirmSheet('Gỡ khoá này?', 'Sau khi lưu, kết nối dùng khoá này sẽ ngừng chạy cho tới khi khai khoá mới.', 'Gỡ khoá', true)
      .then(function (ok) { if (!ok) return; delete CDL.thay[f2]; CDL.xoaKhoa[f2] = 1; cdlVeTab(fnTab); });
  }
  if ((el = e.target.closest('[data-cdlnganhang]'))) return cdlChonNganHang(fnTab);
  if ((el = e.target.closest('[data-cdllk]'))) return cdlChonLienKet(el.getAttribute('data-cdllk'), fnTab);
  if ((el = e.target.closest('[data-cdlbangthem]'))) return cdlMoDong(el.getAttribute('data-cdlbangthem'), -1);
  if ((el = e.target.closest('[data-cdldong]'))) {
    return cdlMoDong(el.getAttribute('data-cdlbang'), parseInt(el.getAttribute('data-cdldong'), 10));
  }
}

async function cdlChonNganHang(fnTab) {
  if (!CDL.nganHang) {
    try { CDL.nganHang = ((await api('vagabond.tai_khoan.danh_sach', {})) || {}).ngan_hang || []; }
    catch (e) { return toast((e && e.message) || 'Không đọc được danh mục ngân hàng'); }
  }
  var cur = cdlDoc().ngan_hang_bin;
  sheet('Chọn ngân hàng nhận tiền', CDL.nganHang.map(function (n) {
    return { label: n.ten, value: n.bin, phu: n.ma + ' · BIN ' + n.bin, tim: VGB_CD.boDau(n.ten + ' ' + n.ma) };
  }), cur, function (it) {
    var n = VGB_CD.nganHangTheoBin(CDL.nganHang, it.value);
    if (!n) return;
    cdlDatThay('ngan_hang_bin', n.bin);
    cdlDatThay('ngan_hang_hien_thi', n.ten);
    cdlVeTab(fnTab);
  }, true);
}

async function cdlChonLienKet(fn, fnTab) {
  var ds;
  try { ds = await api('vagabond.cai_dat_loi.tim_lien_ket', { o: fn, tu: '' }); }
  catch (e) { return toast((e && e.message) || 'Không đọc được danh mục'); }
  sheet((cdlO(fn) || { o: { nhan: 'Chọn' } }).o.nhan, (ds || []).map(function (x) { return { label: x, value: x }; }),
    cdlDoc()[fn], function (it) { cdlDatThay(fn, it.value); cdlVeTab(fnTab); }, true);
}

/* ---------- Bảng con, ví dụ Nhóm nhận tin Zalo ---------- */
function cdlTomDongZalo(r) {
  var N = VGB_CD.ZALO_NHAN;
  var tach = function (s) { return String(s || '').split(/[,;]/).map(function (x) { return x.trim(); }).filter(Boolean); };
  var lt = tach(r.loai_tin).map(function (x) { return (N.loai_tin[x] || ['', x])[1]; });
  var cd = tach(r.chu_de).map(function (x) { return (N.chu_de[x] || ['', x])[1]; });
  return [lt.length ? lt.join(' · ') : 'Mọi loại tin', cd.length ? 'chủ đề ' + cd.join(', ') : '',
    (r.im_tu && r.im_den) ? 'im ' + r.im_tu + ' đến ' + r.im_den : '', parseInt(r.bat, 10) === 1 ? '' : 'Đang tắt',
    r.chat_id ? '' : 'Chưa chọn nhóm Zalo'].filter(Boolean).join(' · ');
}

function cdlVeBang(o) {
  var rows = CDL.bang[o.fn] || [];
  return '<label style="display:block;font-size:13px;color:#4b545c">' + h(o.nhan) + '</label>' +
    (rows.length ? rows.map(function (r, i) {
      return '<div class="cdl-grp" data-cdlbang="' + h(o.fn) + '" data-cdldong="' + i + '"><b style="font-size:14px">' + h(r.ten_nhom || ('Dòng ' + (i + 1))) +
        '</b><div class="cdl-mo">' + h(o.fn === 'zalo_nhom' ? cdlTomDongZalo(r) : '') + '</div></div>';
    }).join('') : '<div class="cdl-mo">Chưa có dòng nào.</div>') +
    '<button class="cdl-lnk" data-cdlbangthem="' + h(o.fn) + '">+ Thêm ' + (o.fn === 'zalo_nhom' ? 'nhóm nhận tin' : 'dòng') + '</button>';
}

function cdlMoDong(fnBang, i) {
  var nhap = i < 0 ? {} : Object.assign({}, (CDL.bang[fnBang] || [])[i]);
  if (i < 0) ((CDL.d.bang[fnBang] || {}).cot || []).forEach(function (c) { if (c.kieu === 'Check' && c.fn === 'bat') nhap.bat = 1; });
  go(function () { cdlVeDong(fnBang, i, nhap); });
}

function cdlVeDong(fnBang, i, nhap) {
  var meta = CDL.d.bang[fnBang] || { cot: [] };
  var choGhi = meta.ghi_qua_hop_chon || [];
  var html = '<div class="card" style="padding:10px 14px">' + meta.cot.map(function (c) {
    var v = nhap[c.fn];
    var mo = c.mo ? '<div class="cdl-mo">' + h(c.mo) + '</div>' : '';
    var nhan = '<label>' + h(c.nhan) + (c.bat_buoc ? ' *' : '') + '</label>';
    if (c.kieu === 'Check') {
      var b = parseInt(v, 10) === 1;
      return '<div class="cdl-row"><div class="cdl-x"><b>' + h(c.nhan) + '</b></div><button class="cdl-tg' + (b ? ' on' : '') + '" data-cdldbat="' + h(c.fn) + '"></button></div>';
    }
    if (fnBang === 'zalo_nhom' && (c.fn === 'loai_tin' || c.fn === 'chu_de')) {
      var tach = String(v || '').split(/[,;]/).map(function (x) { return x.trim(); }).filter(Boolean);
      var N = VGB_CD.ZALO_NHAN[c.fn];
      return '<div class="cdl-f">' + nhan + '<div class="cdl-val">' + h(tach.length ? tach.map(function (x) { return (N[x] || ['', x])[1]; }).join(', ') : 'Tất cả') +
        '<span style="margin-left:auto"></span><button class="cdl-lnk" data-cdldchon="' + h(c.fn) + '">Chọn</button></div></div>';
    }
    if (fnBang === 'zalo_nhom' && c.fn === 'chat_id') {
      return '<div class="cdl-f">' + nhan + '<div class="cdl-val">' + (v ? h(v) : '<span style="color:#9aa1a8">Chưa chọn</span>') +
        '<span style="margin-left:auto"></span><button class="cdl-lnk" data-cdldnhom="1">Chọn nhóm đã nhắn bot</button></div>' + mo + '</div>';
    }
    if (c.chi_doc && choGhi.indexOf(c.fn) < 0) {
      return '<div class="cdl-f">' + nhan + '<div class="cdl-val">' + h(v == null ? '' : v) + '</div>' + mo + '</div>';
    }
    return '<div class="cdl-f">' + nhan + '<input class="tin" data-cdld="' + h(c.fn) + '" value="' + h(v == null ? '' : v) + '">' + mo + '</div>';
  }).join('') + '</div>' +
    '<button class="btn" id="cdlDongXong" style="width:100%">Xong</button>' +
    (i >= 0 ? '<button class="cdl-lnk" id="cdlDongXoa" style="color:#a42424;width:100%;justify-content:center">Xoá dòng này</button>' : '') +
    '<div class="cdl-mo" style="text-align:center">Bấm Xong rồi bấm Lưu ở cuối màn Cài đặt để ghi lên máy chủ.</div>';
  var b = frame(fnBang === 'zalo_nhom' ? (i < 0 ? 'Thêm nhóm nhận tin' : 'Sửa nhóm nhận tin') : 'Sửa dòng', html);
  b.oninput = function (e) {
    var fn = e.target && e.target.getAttribute && e.target.getAttribute('data-cdld');
    if (fn) nhap[fn] = e.target.value;
  };
  b.onclick = function (e) {
    var el;
    if ((el = e.target.closest('[data-cdldbat]'))) {
      var f = el.getAttribute('data-cdldbat'); nhap[f] = parseInt(nhap[f], 10) === 1 ? 0 : 1; return cdlVeDong(fnBang, i, nhap);
    }
    if ((el = e.target.closest('[data-cdldchon]'))) return cdlChonZalo(el.getAttribute('data-cdldchon'), nhap, function () { cdlVeDong(fnBang, i, nhap); });
    if ((el = e.target.closest('[data-cdldnhom]'))) return cdlChonNhomZalo(nhap, function () { cdlVeDong(fnBang, i, nhap); });
    if (e.target.closest('#cdlDongXong')) {
      if (!String(nhap.ten_nhom || '').trim() && fnBang === 'zalo_nhom') return toast('Đặt tên nhóm trước, ví dụ Kế toán.');
      var rows = CDL.bang[fnBang] = (CDL.bang[fnBang] || []).slice();
      if (i < 0) rows.push(nhap); else rows[i] = nhap;
      CDL.bangDoi[fnBang] = 1;
      return back();
    }
    if (e.target.closest('#cdlDongXoa')) {
      return confirmSheet('Xoá dòng này?', 'Nhóm này sẽ thôi nhận tin sau khi lưu.', 'Xoá', true).then(function (ok) {
        if (!ok) return;
        var rows = CDL.bang[fnBang] = (CDL.bang[fnBang] || []).slice();
        rows.splice(i, 1);
        CDL.bangDoi[fnBang] = 1;
        back();
      });
    }
  };
}

/* Hộp chọn loại tin, chủ đề: mỗi lựa chọn có tên, biểu tượng và một dòng giải
   thích (cùng nguồn với Desk). Không tích gì là nhận tất cả. */
function cdlChonZalo(cot, nhap, xong) {
  var N = VGB_CD.ZALO_NHAN[cot], DM = VGB_CD.ZALO_DANH_MUC[cot];
  var dang = String(nhap[cot] || '').split(/[,;]/).map(function (x) { return x.trim(); }).filter(Boolean);
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  function ve() {
    box.innerHTML = '<div class="shh"><b>' + (cot === 'loai_tin' ? 'Nhóm này nhận loại tin nào?' : 'Nhóm này nhận chủ đề nào?') + '</b><div class="x">&times;</div></div>' +
      '<div class="cdl-mo" style="padding:6px 14px">Không tích ô nào là nhóm nhận <b>tất cả</b> ' + (cot === 'loai_tin' ? 'loại tin.' : 'chủ đề.') + '</div>' +
      '<div class="shl">' + DM.map(function (m) {
        var n = N[m] || ['', m, ''];
        return '<div class="shi" data-cdlz="' + h(m) + '" style="align-items:flex-start;min-height:60px"><span style="font-size:18px">' + (dang.indexOf(m) >= 0 ? '☑' : '☐') +
          '</span><span style="font-size:18px">' + h(n[0]) + '</span><span style="flex:1"><b>' + h(n[1]) + '</b><div class="cdl-mo">' + h(n[2]) + '</div></span></div>';
      }).join('') + '</div><div style="padding:10px 14px"><button class="btn" data-cdlzxong="1" style="width:100%;margin:0">Xong</button></div>';
  }
  ve();
  ov.appendChild(box); document.body.appendChild(ov);
  box.onclick = function (e) {
    var r = e.target.closest('[data-cdlz]');
    if (r) {
      var m = r.getAttribute('data-cdlz'), k = dang.indexOf(m);
      if (k >= 0) dang.splice(k, 1); else dang.push(m);
      return ve();
    }
    if (e.target.closest('[data-cdlzxong]') || e.target.closest('.x')) {
      if (e.target.closest('[data-cdlzxong]')) nhap[cot] = DM.filter(function (m) { return dang.indexOf(m) >= 0; }).join(', ');
      ov.remove();
      xong();
    }
  };
  return { ov: ov, box: box };
}

function cdlChonNhomZalo(nhap, xong) {
  var ds = [];
  try { ds = JSON.parse(cdlDoc().zalo_chat_moi || '[]'); } catch (e) { ds = []; }
  ds = (ds || []).filter(function (x) { return String(x.loai || '').toUpperCase() === 'GROUP'; });
  if (!ds.length) return toast('Chưa có nhóm nào nhắn bot. Thêm bot vào nhóm Zalo, @nhắc bot một lần rồi mở lại màn này.');
  sheet('Chọn nhóm đã nhắn bot', ds.map(function (x) {
    return { label: x.ten || 'Nhóm không tên', value: x.chat_id, phu: x.chat_id };
  }), nhap.chat_id, function (it) {
    nhap.chat_id = it.value;
    if (!nhap.ten_nhom) nhap.ten_nhom = it.label;
    xong();
  }, true);
}

/* ---------- Lưu ---------- */
async function cdlLuu() {
  var n = cdlSoThay();
  if (!n) return;
  var ts = { thay: JSON.stringify(CDL.thay), xoa_khoa: JSON.stringify(Object.keys(CDL.xoaKhoa)), modified: CDL.d.modified };
  var bang = {};
  Object.keys(CDL.bangDoi).forEach(function (k) { bang[k] = CDL.bang[k]; });
  if (Object.keys(bang).length) ts.bang = JSON.stringify(bang);
  var nut = document.getElementById('cdlLuu');
  if (nut) { nut.disabled = true; nut.textContent = 'Đang lưu...'; }
  try {
    var d = await api('vagabond.cai_dat_loi.luu', ts);
    cdlNhan(d);
    toast('Đã lưu ' + n + ' thay đổi');
  } catch (e) {
    toast(String((e && e.message) || 'Không lưu được').replace(/<br\s*\/?>/g, ' '), 6000);
    cdlCapNhatNut();
    return;
  }
  var top = S.stack[S.stack.length - 1];
  if (top) top(); else cdlVeTong();
}

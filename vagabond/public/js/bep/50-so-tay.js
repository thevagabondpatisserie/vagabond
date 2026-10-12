
/* ---------- 50. So tay huong dan dung app (v554, 02/10/2026) ----------

   Anh Viet: "Anh thay hoi nhieu chu, nhin hoi don thuan... lam nut so tay
   trong app", va chon "Ve nut bang chinh giao dien app", "Mui ten chi vao
   nut".

   HAI NOI DUNG CHUNG MOT BO VE
   Man So tay va cau tra loi cua tro ly (35-tro-ly.js) cung goi stMd(). Mot
   bo ve thi nut trong so tay va nut trong cau tra loi trong y het nhau, va
   sua kieu nut mot cho la ca hai cung doi.

   VI SAO VE NUT BANG CSS CHU KHONG DUNG ANH CHUP
   Anh chup dung dung mot ban. Doi mau nut hay doi chu la anh thanh sai, ma
   khong ai nho chup lai. Nut ve bang chinh mau va bo goc cua .btn trong
   00-nen.js thi luon khop. Ky hieu trong so tay: [[Ten nut]] cho nut app,
   [[desk:Ten nut]] cho nut tren Desk. Quy uoc o vagabond/so_tay/_quy-uoc.md.

   AN TOAN
   stMd() THOAT KY TU TRUOC (h()) roi moi chen the cua minh. Cau tra loi cua
   mo hinh di qua day, nen khong bao gio duoc dao thu tu nay: chen the truoc
   roi moi thoat la de mo hinh (hay ai sua so tay) chen HTML tuy y vao app.
   Lien ket chi nhan dia chi dang /chu-thuong-gach-ngang, khong nhan duong
   dan ngoai. */

/* Ten trang thai PHAI rieng: moi phan bep/ ghep chung MOT pham vi ham, va
   00-nen.js da co `var st` giu the <style> cua ca app. Ban dau phan nay
   khai lai `var st` nen keepCss() cua nen goi appendChild voi doi tuong
   trang thai, nem loi o moi man (Codex #412 F2, bench 37013787339). Ca kiem
   thu_so_tay_554.py `_khong_trung_ten` chot khong cho trung ten lan nua. */
var stS = { d: null, chuong: '', tim: '', mo: {} };

function stCss() {
  if (document.getElementById('stCss')) return;
  var s = document.createElement('style');
  s.id = 'stCss';
  s.textContent =
    '.stMd{font-size:14.5px;line-height:1.6;color:#16181d}' +
    '.stMd p{margin:0 0 8px}' +
    '.stMd .stH{font-weight:700;color:#05323C;margin:12px 0 6px;font-size:14px;' +
    'text-transform:none;letter-spacing:.1px}' +
    '.stMd ol,.stMd ul{margin:0 0 8px;padding-left:22px}' +
    '.stMd li{margin:0 0 5px}' +
    '.stMd ol li::marker{color:#05323C;font-weight:700}' +
    '.stBg{overflow-x:auto;margin:0 0 10px;-webkit-overflow-scrolling:touch}' +
    '.stMd table{border-collapse:collapse;width:100%;font-size:13.5px;min-width:260px}' +
    '.stMd th{background:#eaf9fc;color:#05323C;text-align:left;font-weight:700;' +
    'padding:7px 9px;border:1px solid #d6eef3;white-space:nowrap}' +
    '.stMd td{padding:7px 9px;border:1px solid #e8ebf1;vertical-align:top}' +
    '.stMd tr:nth-child(even) td{background:#fafbfc}' +
    /* Nut app: cung mau, cung do dam chu voi .btn trong 00-nen.js, chi thu
       nho de nam vua trong dong chu. */
    '.stNut{display:inline-block;background:#50DBF2;color:#05323C;font-weight:700;' +
    'border-radius:9px;padding:2px 10px;font-size:13px;line-height:1.55;' +
    'white-space:nowrap;box-shadow:0 1px 0 rgba(5,50,60,.18);vertical-align:baseline}' +
    /* Nut Desk: kieu nut mac dinh cua Frappe, nen trang vien xam. */
    '.stNut.stDesk{background:#f3f3f3;color:#1f272e;border:1px solid #d1d8dd;' +
    'border-radius:6px;font-weight:600;box-shadow:none}' +
    '.stTro{display:inline-block;width:15px;height:11px;margin:0 3px 0 1px;vertical-align:-1px}' +
    '.stTro path{fill:#E8590C}' +
    '.stLk{color:#0b7285;font-weight:600;text-decoration:none;border-bottom:1px dashed #0b7285}' +
    '.stCxm{display:inline;background:#fff4e5;color:#8a4b00;border:1px solid #f5c98a;' +
    'border-radius:6px;padding:1px 6px;font-size:12.5px}' +
    '.stLuoi{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin-bottom:12px}' +
    '.stO{background:#fff;border-radius:14px;padding:13px 14px;box-shadow:0 1px 3px rgba(20,25,40,.07);cursor:pointer}' +
    '.stO .stOt{font-weight:700;color:#05323C;font-size:15px;margin-bottom:3px}' +
    '.stO .stOs{font-size:12.5px;color:#6b7280}' +
    '.stMuc{background:#fff;border-radius:14px;margin-bottom:10px;box-shadow:0 1px 3px rgba(20,25,40,.07);overflow:hidden}' +
    '.stMucD{display:flex;align-items:center;gap:10px;padding:13px 14px;cursor:pointer}' +
    '.stMucD b{flex:1;font-size:15px;color:#16181d;font-weight:600}' +
    '.stMucD .stCh{font-size:11.5px;color:#6b7280;white-space:nowrap}' +
    '.stMucT{padding:2px 14px 14px;border-top:1px solid #f0f2f6}' +
    /* Mui ten va nut dinh lien mot cum: xuong dong giua chung thi mui ten
       chi vao khoang trong. */
    '.stCum{white-space:nowrap;display:inline-block}' +
    '.stMo{margin-top:10px;display:block;box-sizing:border-box;text-align:center;text-decoration:none}' +
    '.stRong{color:#6b7280;font-size:14px;padding:18px 4px;text-align:center}';
  (document.head || document.body).appendChild(s);
}

/* Mui ten nho mau cam chi vao nut. SVG chu khong dung ky tu emoji: emoji ve
   khac nhau tren tung may, va quy uoc so tay khong dung emoji. */
var ST_TRO = '<svg class="stTro" viewBox="0 0 15 11" aria-hidden="true">' +
  '<path d="M0 4h9V0l6 5.5L9 11V7H0z"/></svg>';

/* Mot dong chu: thoat ky tu truoc, roi moi chen nut, chu dam, lien ket. */
function stDong(s) {
  var t = h(s);
  t = t.replace(/\[CHƯA XÁC MINH:\s*([^\]]*)\]/g, function (m, y) {
    return '<span class="stCxm">Chưa xác minh: ' + y + '</span>';
  });
  t = t.replace(/\[\[desk:([^\]]+)\]\]/g, function (m, x) {
    return '<span class="stCum">' + ST_TRO + '<span class="stNut stDesk">' + x.trim() + '</span></span>';
  });
  t = t.replace(/\[\[([^\]]+)\]\]/g, function (m, x) {
    return '<span class="stCum">' + ST_TRO + '<span class="stNut">' + x.trim() + '</span></span>';
  });
  t = t.replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>');
  t = t.replace(/\((\/[a-z0-9][a-z0-9-]*)\)/g, function (m, d) {
    return '(<a class="stLk" href="' + d + '">' + d + '</a>)';
  });
  return t;
}

function stO(dong) {
  var o = dong.trim();
  if (o.charAt(0) === '|') o = o.slice(1);
  if (o.charAt(o.length - 1) === '|') o = o.slice(0, -1);
  return o.split('|').map(function (x) { return x.trim(); });
}

/* Ve mot doan chu theo quy uoc so tay thanh HTML. Nhan: bang (dong bat dau
   bang |), danh sach so (1. ), danh sach gach (- ), dong tieu de khoi
   (**Cac buoc**), con lai la doan van. */
function stMd(txt) {
  var dong = String(txt == null ? '' : txt).replace(/\r/g, '').split('\n');
  var ra = [], i = 0;
  while (i < dong.length) {
    var d = dong[i], t = d.trim();
    if (!t) { i++; continue; }
    if (t.charAt(0) === '|') {
      var hang = [];
      while (i < dong.length && dong[i].trim().charAt(0) === '|') { hang.push(dong[i]); i++; }
      var dau = stO(hang[0]);
      var than = hang.slice(1).filter(function (x) { return !/^\s*\|?[\s:|-]+\|?\s*$/.test(x); });
      ra.push('<div class="stBg"><table><thead><tr>' +
        dau.map(function (x) { return '<th>' + stDong(x) + '</th>'; }).join('') +
        '</tr></thead><tbody>' +
        than.map(function (r) {
          return '<tr>' + stO(r).map(function (x) { return '<td>' + stDong(x) + '</td>'; }).join('') + '</tr>';
        }).join('') + '</tbody></table></div>');
      continue;
    }
    if (/^\d+[.)]\s/.test(t)) {
      var li = [];
      while (i < dong.length && /^\d+[.)]\s/.test(dong[i].trim())) {
        li.push('<li>' + stDong(dong[i].trim().replace(/^\d+[.)]\s+/, '')) + '</li>'); i++;
      }
      ra.push('<ol>' + li.join('') + '</ol>');
      continue;
    }
    if (/^[-*]\s/.test(t)) {
      var ul = [];
      while (i < dong.length && /^[-*]\s/.test(dong[i].trim())) {
        ul.push('<li>' + stDong(dong[i].trim().replace(/^[-*]\s+/, '')) + '</li>'); i++;
      }
      ra.push('<ul>' + ul.join('') + '</ul>');
      continue;
    }
    if (/^\*\*[^*]+\*\*:?$/.test(t)) {
      ra.push('<div class="stH">' + h(t.replace(/^\*\*|\*\*:?$/g, '')) + '</div>');
      i++;
      continue;
    }
    ra.push('<p>' + stDong(t) + '</p>');
    i++;
  }
  return '<div class="stMd">' + ra.join('') + '</div>';
}

/* Bo dau tieng Viet de tim khong can go dau. Cung cach voi bo_dau ben
   tro_ly_so_tay.py. */
function stBoDau(s) {
  return String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd').replace(/Đ/g, 'd').toLowerCase();
}

/* Muc nao khop o tim: MOI chu cua o tim deu phai co trong ten, tu khoa hay
   than muc. Xep ten khop truoc. */
function stLoc(d, tim) {
  var tu = stBoDau(tim).split(/[^a-z0-9]+/).filter(function (x) { return x.length > 1; });
  var ra = [];
  (d.chuong || []).forEach(function (c) {
    (c.muc || []).forEach(function (m, j) {
      if (!tu.length) return;
      var ten = stBoDau(m.ten), tk = stBoDau(m.tu_khoa), th = stBoDau(m.than);
      var du = tu.every(function (x) { return ten.indexOf(x) >= 0 || tk.indexOf(x) >= 0 || th.indexOf(x) >= 0; });
      if (!du) return;
      var diem = 0;
      tu.forEach(function (x) { if (ten.indexOf(x) >= 0) diem += 3; if (tk.indexOf(x) >= 0) diem += 2; });
      ra.push({ c: c, m: m, k: c.ma + ':' + j, diem: diem });
    });
  });
  ra.sort(function (a, b) { return b.diem - a.diem; });
  return ra;
}

function stTheMuc(c, m, k, hienChuong) {
  var mo = !!stS.mo[k];
  return '<div class="stMuc"><div class="stMucD" data-stk="' + h(k) + '">' +
    '<b>' + h(m.ten) + '</b>' +
    (hienChuong ? '<span class="stCh">' + h(c.ten) + '</span>' : '') +
    '<span style="color:#c3c8d4;font-size:20px">' + (mo ? '&#8964;' : '&#8250;') + '</span></div>' +
    (mo ? '<div class="stMucT">' + stMd(m.than) +
      (m.duong ? '<a class="btn stMo" href="' + h(m.duong) + '">Mở màn này</a>' : '') +
      '</div>' : '') +
    '</div>';
}

async function scrSoTay() {
  stCss();
  if (!stS.d) {
    frame('Sổ tay', '<div class="emp"><div class="e1">⏳</div></div>');
    try { stS.d = await api('vagabond.tro_ly_so_tay.doc_so_tay', {}); }
    catch (e) {
      frame('Sổ tay', '<div class="emp"><div class="e1">🔒</div><div>' + h(errMsg(e)) + '</div></div>');
      return;
    }
  }
  stVe();
}

/* Phan danh sach (luoi chuong, danh sach muc, hay ket qua tim). Tach rieng
   de go o tim hay mo mot muc chi ve lai khoi nay, khong ve lai ca man: ve
   lai ca man la mat con tro dang go trong o tim. */
function stDsHtml() {
  var d = stS.d || { chuong: [] };
  if (stS.tim.trim()) {
    var kq = stLoc(d, stS.tim);
    return kq.length
      ? kq.slice(0, 40).map(function (x) { return stTheMuc(x.c, x.m, x.k, 1); }).join('')
      : '<div class="stRong">Chưa có mục nào khớp. Thử chữ khác, hoặc hỏi trợ lý.</div>';
  }
  if (!stS.chuong) {
    return '<div class="stLuoi">' + (d.chuong || []).map(function (c) {
      return '<div class="stO" data-stc="' + h(c.ma) + '"><div class="stOt">' + h(c.ten) + '</div>' +
        '<div class="stOs">' + (c.muc || []).length + ' việc</div></div>';
    }).join('') + '</div>';
  }
  var c = null;
  (d.chuong || []).forEach(function (x) { if (x.ma === stS.chuong) c = x; });
  return c ? (c.muc || []).map(function (m, j) { return stTheMuc(c, m, c.ma + ':' + j, 0); }).join('')
    : '<div class="stRong">Không thấy chương này.</div>';
}

function stChipHtml() {
  var d = stS.d || { chuong: [] };
  return '<div class="chips" id="stChip"><div class="chip' + (!stS.chuong ? ' on' : '') + '" data-stc="">Tất cả chương</div>' +
    (d.chuong || []).map(function (c) {
      return '<div class="chip' + (stS.chuong === c.ma ? ' on' : '') + '" data-stc="' + h(c.ma) + '">' + h(c.ten) + '</div>';
    }).join('') + '</div>';
}

function stVe() {
  var html = '<div class="srch"><span style="color:#98a2b3">&#128269;</span>' +
    '<input id="stTim" placeholder="Tìm: nhập kho, hoàn tiền, mật khẩu..." value="' + h(stS.tim) + '"></div>';
  var body = frame('Sổ tay', html + stChipHtml() + '<div id="stDs">' + stDsHtml() + '</div>');
  var o = document.getElementById('stTim');
  if (o) {
    o.addEventListener('input', function () {
      stS.tim = o.value;
      var ds = document.getElementById('stDs');
      if (ds) ds.innerHTML = stDsHtml();
    });
  }
  if (body) body.onclick = function (e) {
    var c = e.target.closest('[data-stc]');
    if (c) { stS.chuong = c.dataset.stc; stS.tim = ''; stS.mo = {}; stVe(); return; }
    var m = e.target.closest('[data-stk]');
    if (m) {
      var k = m.dataset.stk;
      stS.mo[k] = !stS.mo[k];
      var ds = document.getElementById('stDs');
      if (ds) ds.innerHTML = stDsHtml();
    }
  };
}

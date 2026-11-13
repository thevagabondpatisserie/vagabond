/* ---------- 72. Phiếu Đề xuất công thức (v656, anh Việt 13/11/2026) ----------

   Bếp (Hân, Linh, Lab) ghi công thức bánh mới trên điện thoại: tên bánh, các
   size, từng thành phần chọn mã có sẵn hoặc gõ tên mới, gram từng size, và
   bấm chip thành phần đó VÀO ĐÂU (ruột cấp 1, khuôn cấp 2, thành phẩm). Bấm
   Gửi Khải. Khải chọn mã thành phẩm từng size, bấm Tạo mã và công thức (máy
   tạo mã BTP, mã cấp 1, cấp 2, công thức nháp), xem lại rồi Ghi sổ tất cả.

   Bốn ý thêm anh duyệt: gõ tên mới thì máy báo mã gần giống; giá vốn dự kiến
   và % giá bán (tính ở máy chủ, một nguồn, hiện sau mỗi lần Lưu); nhập một
   size, bấm Gợi ý size khác; sửa công thức đang dùng cũng qua phiếu (Đề xuất
   điều chỉnh) có bảng trước và sau. Máy chủ: vagabond/de_xuat_cong_thuc.py. */

var DX = { ds: null, tt: '', f: null, goiY: {} };
var dxKhoiPhuc = null;
var DX_SIZE = ['12', '16', '18', '20', 'Slice'];
var DX_DICH = [
  ['cap1', 'Ruột (cấp 1)', 'Ghép vào ruột bánh'],
  ['cap2', 'Khuôn (cấp 2)', 'Bọc vào khuôn, chờ trang trí'],
  ['thanh_pham', 'Thành phẩm', 'Trang trí lúc hoàn thiện']
];
var DX_TT = [['', 'Tất cả'], ['Nháp', 'Nháp'], ['Chờ Khải', 'Chờ Khải'], ['Trả lại bếp', 'Trả lại bếp'],
  ['Đã tạo nháp', 'Đã tạo nháp'], ['Đã ghi sổ', 'Đã ghi sổ']];
var DX_MAU_TT = { 'Nháp': 'n', 'Chờ Khải': 'w', 'Trả lại bếp': 'r', 'Đã tạo nháp': 'w', 'Đã ghi sổ': 'g', 'Đã huỷ': 'n' };
var DX_NUT = 'min-height:44px;font-size:14px';

function dxSo(v) { var n = parseFloat(String(v == null ? '' : v).replace(',', '.')); return isFinite(n) ? n : 0; }
function dxId() { return 'd' + Date.now().toString(36) + Math.floor(Math.random() * 1000); }

async function scrDxDs() {
  frame('Phiếu đề xuất công thức', '<div class="emp"><div class="e1">⏳</div></div>');
  try { DX.ds = await api('vagabond.de_xuat_cong_thuc.danh_sach', { trang_thai: DX.tt || null }); }
  catch (e) { frame('Phiếu đề xuất công thức', '<div class="emp"><div class="e1">🔒</div><div>' + h(errMsg(e)) + '</div></div>'); return; }
  var chips = DX_TT.map(function (c) {
    return '<div class="chip' + (DX.tt === c[0] ? ' on' : '') + '" data-dxtt="' + h(c[0]) + '" style="' + DX_NUT + '">' + h(c[1]) + '</div>';
  }).join('');
  var body = '<div class="mut" style="font-size:13px;line-height:1.5;margin-bottom:9px">Bếp ghi công thức bánh mới hoặc đề xuất sửa công thức đang dùng; Khải lên mã và ghi sổ.</div>' +
    '<div class="chips">' + chips + '</div>' +
    (DX.ds.length ? '<div class="lst">' + DX.ds.map(function (x) {
      return '<div class="li" data-dxmo="' + h(x.name) + '" style="min-height:44px;cursor:pointer"><div class="lt">' +
        '<div class="l1">' + h(x.ten_banh || '(chưa đặt tên)') + '</div>' +
        '<div class="l2">' + h(x.loai) + ' · ' + h(x.ten_nguoi_de_xuat) + ' · ' + h(x.modified) + '</div></div>' +
        '<div style="text-align:right"><div class="st ' + (DX_MAU_TT[x.trang_thai] || 'n') + '">' + h(x.trang_thai) + '</div></div></div>';
    }).join('') + '</div>' : '<div class="emp"><div class="e1">📝</div><div class="e2">Chưa có phiếu nào</div></div>');
  var b = frame('Phiếu đề xuất công thức', body, { fab: true, onFab: dxMoi });
  b.onclick = function (e) {
    var t = e.target.closest('[data-dxtt]');
    if (t) { DX.tt = t.getAttribute('data-dxtt'); return scrDxDs(); }
    var m = e.target.closest('[data-dxmo]');
    if (m) return dxMo(m.getAttribute('data-dxmo'));
  };
}

function dxMoi() {
  DX.f = { name: '', loai: 'Mới', ten_banh: '', trang_thai: 'Nháp', du_lieu: { sizes: [], dong: [] }, ma_tp: {}, gia: {}, thieu_gia: [],
    quyen: { sua: 1, duyet: ctGhiSoDuoc() ? 1 : 0 } };
  DX.goiY = {};
  go(function () { return scrDxSua(''); });
}

async function dxMo(name) {
  busy(1);
  try { var r = await api('vagabond.de_xuat_cong_thuc.chi_tiet', { name: name }); busy(0); dxNap(r); }
  catch (e) { busy(0); return toast(errMsg(e), 6000); }
  DX.goiY = {};
  go(function () { return scrDxSua(name); });
}

/* Từ màn công thức: bếp đề xuất sửa công thức đang dùng. */
async function dxDieuChinh(bom) {
  busy(1);
  try { var r = await api('vagabond.de_xuat_cong_thuc.tu_cong_thuc', { bom: bom }); busy(0); }
  catch (e) { busy(0); return toast(errMsg(e), 6000); }
  DX.f = { name: '', loai: 'Điều chỉnh', bom_goc: bom, ten_banh: r.ten_banh, trang_thai: 'Nháp', du_lieu: r.du_lieu, me: r.me, dvt_me: r.dvt,
    ly_do: '', ma_tp: {}, gia: {}, thieu_gia: [], quyen: { sua: 1, duyet: ctGhiSoDuoc() ? 1 : 0 } };
  DX.goiY = {};
  go(function () { return scrDxSua(''); });
}

function dxNap(r) {
  var mtp = {};
  Object.keys(r.gia || {}).forEach(function (s) { if (r.gia[s].ma_tp) mtp[s] = { ma: r.gia[s].ma_tp, ten: r.gia[s].ten_tp }; });
  DX.f = Object.assign({}, r, { ma_tp: mtp });
}

function dxSuaDuoc() { var f = DX.f; return !!(f && f.quyen && f.quyen.sua); }

function scrDxSua(name) {
  if (dxKhoiPhuc && (dxKhoiPhuc.name || '') === (name || '')) DX.f = dxKhoiPhuc;
  dxKhoiPhuc = null;
  var f = DX.f;
  if (!f) return go(scrDxDs, true);
  /* Lượt dựng màn này. Lời gọi máy chủ trả về muộn (tìm mã gần giống, gợi ý
     size) sau khi người dùng đã sang màn khác thì bỏ, không vẽ đè. */
  var luot = DX.luot = (DX.luot || 0) + 1;
  var thanNay = null;
  function conMan() { return DX.luot === luot && DX.f === f && !!thanNay && document.getElementById('vgbBody') === thanNay; }
  var dc = f.loai === 'Điều chỉnh';
  var sua = dxSuaDuoc();
  var dl = f.du_lieu;

  function oGram(x, s) {
    var v = (x.gram || {})[s];
    return '<label style="display:block;flex:1;min-width:84px"><div class="lb" style="font-size:13px">' + (dc ? 'Số lượng' : 'Size ' + h(s)) +
      ' (' + h(x.dvt || 'Gram') + ')</div><input class="nt" type="number" inputmode="decimal" data-dxg="' + h(x.id) + '|' + h(s) + '" value="' +
      (v == null ? '' : h(String(v))) + '"' + (sua ? '' : ' disabled') + ' style="height:44px;font-size:15px;width:100%"></label>';
  }

  function theDong(x, i) {
    var gy = DX.goiY[x.id] || [];
    var dau = x.ma
      ? '<div class="l1">' + h(x.ten || x.ma) + '</div><div class="l2">' + h(x.ma) + ' · mã có sẵn</div>'
      : '<input class="nt" data-dxten="' + h(x.id) + '" placeholder="Tên thành phần mới" value="' + h(x.ten || '') + '"' + (sua ? '' : ' disabled') +
        ' style="height:44px;font-size:15px;width:100%"><div class="l2" style="margin-top:4px">Thành phần mới · Khải sẽ tạo mã</div>';
    var goiY = (!x.ma && sua && gy.length && !x.bo_goi_y)
      ? '<div style="background:#fff7e6;border-radius:8px;padding:8px 10px;margin-top:8px;font-size:13px;line-height:1.45">' +
        '<b>Đã có mã gần giống, dùng luôn cho khỏi tạo trùng?</b>' +
        gy.map(function (g) {
          return '<div class="chip" data-dxdung="' + h(x.id) + '|' + h(g.ma) + '" style="' + DX_NUT + ';display:flex;align-items:center;margin-top:6px">' +
            h(g.ten) + ' · ' + h(g.ma) + '</div>';
        }).join('') +
        '<button class="btn gh" data-dxboqua="' + h(x.id) + '" style="' + DX_NUT + ';margin-top:6px">Không phải, vẫn tạo mới</button></div>'
      : '';
    var chip = dc ? '' : '<div class="lb" style="font-size:13px;margin-top:9px">Vào đâu</div><div class="chips" style="margin-top:4px">' + DX_DICH.map(function (c) {
      return '<div class="chip' + (x.dich === c[0] ? ' on' : '') + '" data-dxdich="' + h(x.id) + '|' + c[0] + '" style="' + DX_NUT + '">' +
        '<div>' + h(c[1]) + '<div style="font-size:13px;font-weight:400;opacity:.8">' + h(c[2]) + '</div></div></div>';
    }).join('') + '</div>';
    var sizes = dc ? [''] : dl.sizes;
    var gram = '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:8px">' + sizes.map(function (s) { return oGram(x, s); }).join('') + '</div>' +
      (!dc && sua && dl.sizes.length > 1 ? '<button class="btn gh" data-dxgy="' + h(x.id) + '" style="' + DX_NUT + ';margin-top:8px">Gợi ý các size còn trống</button>' : '');
    var con = (!x.ma && !dc) ? dxCon(x, sua) : '';
    return '<div class="card" style="padding:12px 13px;margin-bottom:10px"><div style="display:flex;gap:8px;align-items:flex-start">' +
      '<div style="flex:1;min-width:0">' + dau + '</div>' +
      (sua ? '<button class="btn gh" data-dxbo="' + h(x.id) + '" style="width:44px;min-height:44px;flex:0 0 44px;color:#b3261e">&times;</button>' : '') +
      '</div>' + goiY + chip + gram + con + '</div>';
  }

  function hopGia() {
    if (dc) {
      var d = f.doi_chieu;
      if (!d) return '<div class="mut" style="font-size:13px">Bấm Lưu nháp để máy tính bảng trước và sau, kèm giá vốn.</div>';
      var cl = d.von_moi - d.von_cu;
      return '<table style="width:100%;border-collapse:collapse;font-size:13.5px">' +
        '<tr><th style="text-align:left;padding:5px">Dòng</th><th style="text-align:right;padding:5px">Trước</th><th style="text-align:right;padding:5px">Sau</th></tr>' +
        d.bang.map(function (r) {
          var mau = r.kieu === 'them' ? '#178a4c' : r.kieu === 'bot' ? '#b3261e' : r.kieu === 'doi' ? '#b45309' : '#475467';
          return '<tr style="color:' + mau + '"><td style="padding:5px;border-top:1px solid #eef0f3">' + h(r.ten || r.ma) +
            (r.kieu === 'them' ? ' (thêm)' : r.kieu === 'bot' ? ' (bỏ)' : r.kieu === 'doi' ? ' (đổi)' : '') + '</td>' +
            '<td style="text-align:right;padding:5px;border-top:1px solid #eef0f3">' + (r.cu == null ? '' : num(r.cu)) + '</td>' +
            '<td style="text-align:right;padding:5px;border-top:1px solid #eef0f3">' + (r.moi == null ? '' : num(r.moi)) + '</td></tr>';
        }).join('') + '</table>' +
        '<div style="font-size:14px;margin-top:8px">Giá vốn: <b>' + money(d.von_cu) + ' đ</b> → <b>' + money(d.von_moi) + ' đ</b> (' +
        (cl >= 0 ? '+' : '') + money(cl) + ' đ)</div>';
    }
    var g = f.gia || {};
    if (!dl.sizes.length) return '';
    return dl.sizes.map(function (s) {
      var x = g[s] || {};
      return '<div style="display:flex;justify-content:space-between;font-size:14px;padding:5px 0;border-top:1px solid #eef0f3">' +
        '<span>Size ' + h(s) + '</span><span><b>' + money(x.von || 0) + ' đ</b>' +
        (x.ban ? ' · bán ' + money(x.ban) + ' đ · <b>' + x.ty_le + '%</b>' : '') + '</span></div>';
    }).join('') +
      ((f.thieu_gia || []).length ? '<div style="color:#b3261e;font-size:13px;margin-top:6px;line-height:1.45">⚠️ Thiếu giá: ' + h(f.thieu_gia.join(', ')) + '. Giá vốn trên đang thiếu phần này.</div>' : '') +
      '<div class="mut" style="font-size:13px;margin-top:6px">Giá vốn dự kiến, tính lại mỗi lần Lưu nháp. % giá bán hiện khi Khải đã chọn mã thành phẩm.</div>';
  }

  function phanKhai() {
    if (!f.name || !(f.quyen || {}).duyet) return '';
    if (f.trang_thai === 'Chờ Khải' && !dc) {
      return '<div class="sec">Khải lên mã</div><div class="card" style="padding:12px 13px">' +
        dl.sizes.map(function (s) {
          var m = (f.ma_tp || {})[s];
          return '<div style="display:flex;gap:8px;align-items:center;margin-bottom:8px"><div style="flex:1;font-size:14px">Size ' + h(s) + ': ' +
            (m ? '<b>' + h(m.ten || m.ma) + '</b> · ' + h(m.ma) : '<span style="color:#b3261e">chưa chọn mã thành phẩm</span>') + '</div>' +
            '<button class="btn gh" data-dxtp="' + h(s) + '" style="' + DX_NUT + ';width:auto;padding:0 12px">Chọn mã</button></div>';
        }).join('') +
        '<div class="mut" style="font-size:13px;line-height:1.45">Mã thành phẩm là mã bán ra của từng size. Máy tạo mã thành phần mới, mã cấp 1, cấp 2 rồi công thức nháp; chưa ghi sổ.</div>' +
        '<div class="row2" style="margin-top:9px"><button class="btn gh" id="dxTra" style="' + DX_NUT + '">Hỏi lại bếp</button>' +
        '<button class="btn gr" id="dxTao" style="' + DX_NUT + '">Tạo mã và công thức</button></div></div>';
    }
    if (f.trang_thai === 'Chờ Khải' && dc) {
      return '<div class="row2" style="margin-top:9px"><button class="btn gh" id="dxTra" style="' + DX_NUT + '">Hỏi lại bếp</button>' +
        '<button class="btn gr" id="dxDuyet" style="' + DX_NUT + '">Duyệt và ghi sổ</button></div>';
    }
    if (f.trang_thai === 'Đã tạo nháp') {
      return '<button class="btn gr" id="dxGhiSo" style="' + DX_NUT + ';margin-top:9px">✅ Ghi sổ tất cả</button>';
    }
    return '';
  }

  function ketQua() {
    var kq = f.ket_qua || {};
    if (!(kq.bom || []).length) return '';
    return '<div class="sec">Đã tạo</div><div class="lst">' + kq.bom.map(function (b) {
      return '<div class="li" data-dxbom="' + h(b.bom) + '" style="min-height:44px;cursor:pointer"><div class="lt"><div class="l1">' + h(b.ma) + '</div>' +
        '<div class="l2">' + h(b.bom) + '</div></div></div>';
    }).join('') + '</div>';
  }

  function draw() {
    var tt = '<div class="st ' + (DX_MAU_TT[f.trang_thai] || 'n') + '" style="display:inline-block">' + h(f.trang_thai) + '</div>';
    var body = '<div class="card" style="padding:12px 13px">' +
      (dc ? '<div style="font-size:16px;font-weight:700">' + h(f.ten_banh) + '</div><div class="l2">Đề xuất sửa công thức ' + h(f.bom_goc) + '</div>'
        : '<div class="lb" style="font-size:13px">Tên bánh</div><input class="nt" id="dxTen" value="' + h(f.ten_banh || '') + '" placeholder="Ví dụ: Bánh Pinkpom bưởi"' +
          (sua ? '' : ' disabled') + ' style="height:44px;font-size:15px;width:100%">') +
      '<div style="margin-top:8px">' + tt + (f.ten_nguoi_de_xuat ? ' <span class="l2">· ' + h(f.ten_nguoi_de_xuat) + '</span>' : '') + '</div>' +
      (f.ghi_chu_khai && f.trang_thai === 'Trả lại bếp' ? '<div style="background:#fff7e6;border-radius:8px;padding:8px 10px;margin-top:8px;font-size:14px;line-height:1.45"><b>Khải hỏi lại:</b> ' + h(f.ghi_chu_khai) + '</div>' : '') +
      (dc ? '<div class="lb" style="font-size:13px;margin-top:9px">Lý do sửa</div><textarea class="nt" id="dxLyDo" rows="2"' + (sua ? '' : ' disabled') +
        ' style="width:100%;min-height:64px;font-size:14.5px">' + h(f.ly_do || '') + '</textarea>' : '') + '</div>';
    if (!dc) {
      body += '<div class="sec">Size</div><div class="chips">' + DX_SIZE.concat(dl.sizes.filter(function (s) { return DX_SIZE.indexOf(s) < 0; })).map(function (s) {
        return '<div class="chip' + (dl.sizes.indexOf(s) >= 0 ? ' on' : '') + '" data-dxsize="' + h(s) + '" style="' + DX_NUT + '">' + h(/^\d/.test(s) ? s + 'cm' : s) + '</div>';
      }).join('') + (sua ? '<div class="chip" id="dxSizeKhac" style="' + DX_NUT + '">+ Size khác</div>' : '') + '</div>';
    }
    body += '<div class="sec">Thành phần</div>' + (dl.dong.length ? dl.dong.map(theDong).join('')
      : '<div class="emp" style="padding:20px"><div class="e2">Chưa có thành phần nào</div></div>') +
      (sua ? '<div class="row2"><button class="btn gh" id="dxThemCo" style="' + DX_NUT + '">+ Mã có sẵn</button>' +
        (dc ? '' : '<button class="btn gh" id="dxThemMoi" style="' + DX_NUT + '">+ Thành phần mới</button>') + '</div>' : '');
    body += '<div class="sec">Giá vốn dự kiến</div><div class="card" style="padding:12px 13px">' + hopGia() + '</div>' + phanKhai() + ketQua();
    var nut = sua ? '<div class="row2"><button class="btn gh" id="dxLuu" style="' + DX_NUT + '">💾 Lưu nháp</button>' +
      '<button class="btn gr" id="dxGui" style="' + DX_NUT + '">📤 Gửi Khải</button></div>' +
      (f.name ? '<button class="btn gh" id="dxHuy" style="' + DX_NUT + ';margin-top:8px;color:#b3261e">Huỷ phiếu</button>' : '') : '';
    var b = frame(dc ? 'Đề xuất điều chỉnh' : 'Đề xuất công thức', body, nut ? { footer: nut } : {});
    thanNay = b;
    b.oninput = dxGo;
    b.onclick = dxBam;
    dxNoi();
  }

  function timDong(id) { return dl.dong.filter(function (x) { return x.id === id; })[0]; }

  var tmr = {};
  function dxGo(e) {
    var t = e.target;
    if (t.id === 'dxTen') { f.ten_banh = t.value; return; }
    if (t.id === 'dxLyDo') { f.ly_do = t.value; return; }
    var g = t.getAttribute('data-dxg');
    if (g) { var p = g.split('|'), x = timDong(p[0]); if (x) { x.gram = x.gram || {}; x.gram[p[1]] = t.value === '' ? null : dxSo(t.value); } return; }
    var tn = t.getAttribute('data-dxten');
    if (tn) {
      var y = timDong(tn); if (!y) return;
      y.ten = t.value; y.bo_goi_y = 0;
      clearTimeout(tmr[tn]);
      tmr[tn] = setTimeout(async function () {
        if ((y.ten || '').trim().length < 3) { DX.goiY[tn] = []; return; }
        try { DX.goiY[tn] = await api('vagabond.de_xuat_cong_thuc.goi_y_ma', { ten: y.ten }); } catch (er) { DX.goiY[tn] = []; }
        if (!(DX.goiY[tn] || []).length || !conMan()) return;
        draw();
        /* Vẽ lại để hiện mã gần giống: trả con trỏ về ô đang gõ. */
        var o = document.querySelector('[data-dxten="' + tn + '"]');
        if (o) { o.focus(); try { o.setSelectionRange(o.value.length, o.value.length); } catch (e2) { } }
      }, 700);
      return;
    }
    var cm = t.getAttribute('data-dxme');
    if (cm) { var z = timDong(cm); if (z) { z.con = z.con || { me: 0, dong: [] }; z.con.me = dxSo(t.value); } return; }
    var cs = t.getAttribute('data-dxcsl');
    if (cs) { var q = cs.split('|'), w = timDong(q[0]); if (w && w.con && w.con.dong[+q[1]]) w.con.dong[+q[1]].sl = dxSo(t.value); }
  }

  function dxBam(e) {
    var t;
    if ((t = e.target.closest('[data-dxsize]')) && sua) {
      var s = t.getAttribute('data-dxsize'), k = dl.sizes.indexOf(s);
      if (k >= 0) dl.sizes.splice(k, 1); else dl.sizes.push(s);
      return draw();
    }
    if ((t = e.target.closest('[data-dxdich]')) && sua) {
      var p = t.getAttribute('data-dxdich').split('|'), x = timDong(p[0]); if (x) x.dich = p[1];
      return draw();
    }
    if ((t = e.target.closest('[data-dxbo]'))) {
      var id = t.getAttribute('data-dxbo');
      dl.dong = dl.dong.filter(function (y) { return y.id !== id; });
      return draw();
    }
    if ((t = e.target.closest('[data-dxgy]'))) return dxGoiYSize(timDong(t.getAttribute('data-dxgy')));
    if ((t = e.target.closest('[data-dxboqua]'))) { var bq = timDong(t.getAttribute('data-dxboqua')); if (bq) bq.bo_goi_y = 1; return draw(); }
    if ((t = e.target.closest('[data-dxdung]'))) {
      var q = t.getAttribute('data-dxdung').split('|'), d = timDong(q[0]), gy = (DX.goiY[q[0]] || []).filter(function (g) { return g.ma === q[1]; })[0];
      if (d && gy) { d.ma = gy.ma; d.ten = gy.ten; d.dvt = gy.dvt === 'Gram' ? 'Gram' : (gy.dvt || 'Gram'); delete d.con; }
      return draw();
    }
    if ((t = e.target.closest('[data-dxcbo]'))) {
      var c = t.getAttribute('data-dxcbo').split('|'), w = timDong(c[0]); if (w && w.con) w.con.dong.splice(+c[1], 1);
      return draw();
    }
    if ((t = e.target.closest('[data-dxcco]'))) return dxThemCon(timDong(t.getAttribute('data-dxcco')), 'co');
    if ((t = e.target.closest('[data-dxcmoi]'))) return dxThemCon(timDong(t.getAttribute('data-dxcmoi')), 'moi');
    if ((t = e.target.closest('[data-dxtp]'))) {
      var sz = t.getAttribute('data-dxtp');
      return mfgPickItem('Mã thành phẩm size ' + sz, leavesUnder(['Bán ra']), function (code) {
        f.ma_tp = f.ma_tp || {}; f.ma_tp[sz] = { ma: code, ten: code };
        api('frappe.client.get_value', { doctype: 'Item', filters: { name: code }, fieldname: 'item_name' })
          .then(function (r) { if (r && r.item_name) f.ma_tp[sz].ten = r.item_name; draw(); }, function () { draw(); });
      });
    }
    if ((t = e.target.closest('[data-dxbom]'))) { var bn = t.getAttribute('data-dxbom'); return go(function () { scrCongThucXem(bn); }); }
  }

  function dxThemCon(x, kieu) {
    if (!x) return;
    x.con = x.con || { me: 0, dong: [] };
    if (kieu === 'co') {
      return mfgPickItem('Nguyên liệu của ' + (x.ten || 'thành phần'), leavesUnder(['Mua vào', 'Sản xuất']), async function (code) {
        try { var it = await api('frappe.client.get', { doctype: 'Item', name: code }); x.con.dong.push({ ma: code, ten: it.item_name || code, sl: 0, dvt: it.stock_uom }); }
        catch (er) { return toast(errMsg(er), 5000); }
        draw();
      });
    }
    var moi = dl.dong.filter(function (y) { return !y.ma && y.id !== x.id; });
    if (!moi.length) return toast('Chưa có thành phần mới nào khác trong phiếu.', 4000);
    sheet('Thành phần mới trong phiếu', moi.map(function (y) { return { label: y.ten || '(chưa đặt tên)', value: y.id }; }), null, function (it) {
      var y = timDong(it.value); x.con.dong.push({ dong_id: y.id, ten: y.ten, sl: 0, dvt: 'Gram' }); draw();
    });
  }

  function dxNoi() {
    var tc = document.getElementById('dxThemCo');
    if (tc) tc.onclick = function () {
      mfgPickItem('Thành phần có sẵn', leavesUnder(['Mua vào', 'Sản xuất']), async function (code) {
        if (dl.dong.some(function (y) { return y.ma === code; })) return toast('Thành phần này đã có trong phiếu');
        try { var it = await api('frappe.client.get', { doctype: 'Item', name: code });
          dl.dong.push({ id: dxId(), ma: code, ten: it.item_name || code, dvt: it.stock_uom, dich: dc ? '' : 'cap2', gram: {} }); }
        catch (er) { return toast(errMsg(er), 5000); }
        draw();
      });
    };
    var tm = document.getElementById('dxThemMoi');
    if (tm) tm.onclick = function () { dl.dong.push({ id: dxId(), ten: '', dvt: 'Gram', dich: 'cap2', gram: {}, con: { me: 0, dong: [] } }); draw(); };
    var sk = document.getElementById('dxSizeKhac');
    if (sk) sk.onclick = async function () {
      var v = await promptSheet('Thêm size', 'Ví dụ: 14 hoặc Khuôn vuông 20');
      v = (v || '').trim().replace(/cm$/i, '').trim();
      if (v && dl.sizes.indexOf(v) < 0) { dl.sizes.push(v); draw(); }
    };
    var lu = document.getElementById('dxLuu');
    if (lu) lu.onclick = function () { dxLuu(false); };
    var gu = document.getElementById('dxGui');
    if (gu) gu.onclick = function () { dxLuu(true); };
    var hu = document.getElementById('dxHuy');
    if (hu) hu.onclick = async function () {
      if (!await confirmSheet('Huỷ phiếu?', 'Phiếu ' + f.name + ' sẽ chuyển sang Đã huỷ, không gửi Khải nữa.', 'Huỷ phiếu')) return;
      dxGoi('huy', { name: f.name }, 'Đã huỷ phiếu.');
    };
    var tr = document.getElementById('dxTra');
    if (tr) tr.onclick = async function () {
      var v = await promptSheet('Hỏi lại bếp', 'Cần bếp sửa hay trả lời gì');
      if (v && v.trim()) dxGoi('tra_lai', { name: f.name, ghi_chu: v.trim() }, 'Đã trả phiếu về bếp kèm câu hỏi.');
    };
    var ta = document.getElementById('dxTao');
    if (ta) ta.onclick = async function () {
      if (!await confirmSheet('Tạo mã và công thức?', 'Máy tạo mã thành phần mới, mã cấp 1, cấp 2 từng size và công thức nháp. Chưa ghi sổ: xem lại rồi bấm Ghi sổ tất cả.', 'Tạo')) return;
      var m = {}; Object.keys(f.ma_tp || {}).forEach(function (s) { m[s] = f.ma_tp[s].ma; });
      dxGoi('tao_nhap', { name: f.name, ma_thanh_pham: JSON.stringify(m) }, 'Đã tạo mã và công thức nháp.');
    };
    var gs = document.getElementById('dxGhiSo');
    if (gs) gs.onclick = async function () {
      if (!await confirmSheet('Ghi sổ tất cả?', 'Các công thức nháp của phiếu thành bản đang dùng, ghi từ thành phần lên thành phẩm.', 'Ghi sổ')) return;
      dxGoi('ghi_so_tat_ca', { name: f.name }, 'Đã ghi sổ các công thức của phiếu.');
    };
    var du = document.getElementById('dxDuyet');
    if (du) du.onclick = async function () {
      if (!await confirmSheet('Duyệt và ghi sổ?', 'Máy ra phiên bản mới của ' + f.ten_banh + ' theo phiếu, bản cũ lui về làm bản lưu.', 'Duyệt')) return;
      dxGoi('duyet_dieu_chinh', { name: f.name }, 'Đã ghi sổ phiên bản mới.');
    };
  }

  async function dxGoi(ham, args, xong) {
    busy(1);
    try { var r = await api('vagabond.de_xuat_cong_thuc.' + ham, args); busy(0); dxNap(r); toast(xong, 5000); }
    catch (er) { busy(0); return toast(errMsg(er), 8000); }
    DX.ds = null;
    go(function () { return scrDxSua(DX.f.name); }, true);
  }

  async function dxLuu(guiLuon) {
    var m = {}; Object.keys(f.ma_tp || {}).forEach(function (s) { m[s] = f.ma_tp[s].ma; });
    busy(1);
    try {
      var r = await api('vagabond.de_xuat_cong_thuc.luu', { name: f.name || null, ten_banh: f.ten_banh || '', du_lieu: JSON.stringify(dl),
        loai: f.loai, bom_goc: f.bom_goc || null, ly_do: f.ly_do || '', ma_thanh_pham: JSON.stringify(m) });
      if (guiLuon) r = await api('vagabond.de_xuat_cong_thuc.gui', { name: r.name });
      busy(0);
      dxNap(r);
      toast(guiLuon ? 'Đã gửi Khải.' : 'Đã lưu nháp ' + r.name + '.', 5000);
    } catch (er) { busy(0); return toast(errMsg(er), 9000); }
    DX.ds = null;
    go(function () { return scrDxSua(DX.f.name); }, true);
  }

  /* Gợi ý size: máy chủ tính (de_xuat_cong_thuc.goi_y_cac_size), một nguồn. */
  async function dxGoiYSize(x) {
    if (!x) return;
    var r;
    try { r = await api('vagabond.de_xuat_cong_thuc.goi_y_size_dong', { dong: JSON.stringify({ dich: x.dich, gram: x.gram || {} }), sizes: JSON.stringify(dl.sizes) }); }
    catch (er) { return toast(errMsg(er), 5000); }
    if (!conMan()) return;
    if (!r || !r.goc) return toast('Nhập gram cho một size tròn (ví dụ 16) trước.', 4000);
    x.gram = r.gram;
    toast('Đã gợi ý theo diện tích khuôn từ size ' + r.goc + '. Sửa lại ô nào lệch.', 5000);
    draw();
  }

  draw();
}

function dxCon(x, sua) {
  var c = x.con || { me: 0, dong: [] };
  return '<div style="background:#f6f8fa;border-radius:8px;padding:9px 10px;margin-top:9px">' +
    '<div style="font-size:13.5px;font-weight:700">Công thức con của thành phần mới</div>' +
    '<label style="display:block;margin-top:6px"><div class="lb" style="font-size:13px">Một mẻ ra được (gram)</div>' +
    '<input class="nt" type="number" inputmode="decimal" data-dxme="' + h(x.id) + '" value="' + (c.me ? h(String(c.me)) : '') + '"' + (sua ? '' : ' disabled') +
    ' style="height:44px;font-size:15px;width:100%"></label>' +
    (c.dong || []).map(function (y, i) {
      return '<div style="display:flex;gap:8px;align-items:flex-end;margin-top:7px"><div style="flex:1;min-width:0;font-size:14px">' + h(y.ten || y.ma || '') +
        '<div class="l2">' + (y.ma ? h(y.ma) : 'thành phần mới trong phiếu') + '</div></div>' +
        '<input class="nt" type="number" inputmode="decimal" data-dxcsl="' + h(x.id) + '|' + i + '" value="' + (y.sl ? h(String(y.sl)) : '') + '" placeholder="' + h(y.dvt || 'Gram') + '"' +
        (sua ? '' : ' disabled') + ' style="height:44px;width:96px;font-size:15px">' +
        (sua ? '<button class="btn gh" data-dxcbo="' + h(x.id) + '|' + i + '" style="width:44px;min-height:44px;flex:0 0 44px;color:#b3261e">&times;</button>' : '') + '</div>';
    }).join('') +
    (sua ? '<div class="row2" style="margin-top:8px"><button class="btn gh" data-dxcco="' + h(x.id) + '" style="' + DX_NUT + '">+ Nguyên liệu</button>' +
      '<button class="btn gh" data-dxcmoi="' + h(x.id) + '" style="' + DX_NUT + '">+ Thành phần mới</button></div>' : '') + '</div>';
}

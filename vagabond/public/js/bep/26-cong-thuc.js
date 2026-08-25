
/* ---------------- Danh muc cong thuc BOM (anh Viet giao 21/08/2026)

   Man danh rieng cho bep truong: xem, tao moi va dieu chinh cong thuc
   ngay tren dien thoai. Ba tab theo khu lam viec, o tim kiem, chip trang
   thai. Dieu chinh mot cong thuc dang chay KHONG cancel ban cu: tao ban
   nhap moi, ghi so xong thi ban cu tu lui ve lam ban luu (van tra cuu
   duoc) - xem ly do ky thuat o dau tep cong_thuc.py.

   Tien to ct = cong thuc. Da kiem va cham ten truoc khi dat (QT-28). */

var ctD = { tab: 'pastry', tt: '', hd: '', tim: '', ds: null, tong: 0 };
var ctE = null;

var CT_TAB = [['pastry', '🎂 Pastry'], ['baker', '🥐 Baker'], ['bar', '🍵 Quầy Bar'], ['khac', '❓ Chưa phân']];
var CT_TT = [['', 'Tất cả'], ['dang_dung', 'Đang dùng'], ['nhap', 'Nháp'], ['ban_cu', 'Bản cũ'], ['da_huy', 'Đã huỷ']];
var CT_TEN_TT = { nhap: 'Nháp', dang_dung: 'Đang dùng', ban_cu: 'Bản cũ', da_huy: 'Đã huỷ' };
var CT_MAU_TT = { nhap: 'w', dang_dung: 'g', ban_cu: 'n', da_huy: 'n' };

/* Chip loc theo TINH TRANG HUONG DAN, them 25/08/2026.

   Anh Viet xin chip loc "hop ly nhat de Khai tien theo doi nhat, han che
   lam sai". Cau hoi that su hay phai tra loi khong phai "mon nay co huong
   dan chua" ma la HAI cau nay:
     - mon nao con thieu huong dan, tuc bep dang lam theo tri nho
     - mon nao co huong dan nhung CONG THUC DA DOI sau do, tuc bep dang lam
       theo to giay khong con dung nua. Cai nay nguy hon cai tren, vi nhin
       vao thi thay du, khong ai nghi la thieu. */
var CT_HD = [['', 'Hướng dẫn: tất cả'], ['chua', '📋 Chưa soạn'], ['nhap', '✏️ Đang nháp'], ['xong', '✅ Đã có'], ['lech', '⚠️ Công thức đã đổi']];
var CT_HD_NHAN = { chua: 'Soạn hướng dẫn', nhap: 'HD nháp', xong: 'Hướng dẫn' };

function ctQuanLy() {
  return hasRole('Manufacturing Manager') || hasRole('System Manager') ||
    hasRole('Giám đốc') || hasRole('AP Giám đốc');
}

/* Nut mo Huong dan che bien tren mot the cong thuc.

   Anh Viet ve mot o vuong ngay canh ten mon va hoi dat nut o do co hop ly
   khong. Co: bep truong dang nhin mon nao thi mo huong dan cua dung mon
   ay, khong phai tim lai trong mot danh sach thu hai.

   Mau nut noi luon tinh trang, khong phai bam vao moi biet:
     cam   chua soan, bep dang lam theo tri nho
     do    co soan nhung cong thuc da doi sau do, to giay dang sai
     xanh  da co va con dung
   Ban da huy thi khong hien nut: soan huong dan cho mot cong thuc da huy
   la dan nguoi ta lam theo ban sai. */
function ctNutHd(x) {
  if (x.trang_thai === 'da_huy') return '';
  var tt = x.huong_dan || 'chua';
  var lop = tt === 'chua' ? ' chua' : (x.hd_lech ? ' lech' : '');
  var nhan = x.hd_lech ? '⚠️ Soát lại HD' : ('📖 ' + (CT_HD_NHAN[tt] || 'Hướng dẫn'));
  return '<button class="ct-hd' + lop + '" data-hdm="' + h(x.ma) +
    '" data-hdt="' + h(x.ten) + '" style="margin-top:7px">' + nhan + '</button>';
}

async function ctTai() {
  var r = await api('vagabond.cong_thuc.danh_sach',
    { tab: ctD.tab, trang_thai: ctD.tt || null, tim: ctD.tim || null, huong_dan: ctD.hd || null });
  ctD.ds = (r && r.ds) || [];
  ctD.tong = (r && r.tong) || 0;
}

async function scrCongThuc() {
  if (ctD.ds === null) {
    frame('Danh mục công thức', '<div class="emp"><div class="e1">⏳</div></div>');
    try { await ctTai(); }
    catch (e) {
      frame('Danh mục công thức', '<div class="emp"><div class="e1">🔒</div><div>' + h(errMsg(e)) + '</div></div>');
      return;
    }
  }

  function draw() {
    var tabs = CT_TAB.map(function (c) {
      return '<div class="chip' + (ctD.tab === c[0] ? ' on' : '') + '" data-tab="' + c[0] + '">' + c[1] + '</div>';
    }).join('');
    var tts = CT_TT.map(function (c) {
      return '<div class="chip' + (ctD.tt === c[0] ? ' on' : '') + '" data-tt="' + c[0] + '">' + c[1] + '</div>';
    }).join('');
    var hds = CT_HD.map(function (c) {
      return '<div class="chip' + (ctD.hd === c[0] ? ' on' : '') + '" data-hd="' + c[0] + '">' + c[1] + '</div>';
    }).join('');
    var body = '<div class="chips">' + tabs + '</div>' +
      '<input class="tin" id="ctTim" placeholder="Tìm theo tên hoặc mã món" value="' + h(ctD.tim) + '" ' +
      'style="text-align:left;font-size:14.5px;padding:0 13px;margin-bottom:9px;width:100%">' +
      '<div class="chips">' + tts + '</div>' +
      '<div class="chips">' + hds + '</div>' +
      (ctD.ds.length ? '<div class="lst">' + ctD.ds.map(function (x) {
        return '<div class="li"><div class="lt" data-n="' + h(x.bom) + '">' +
          '<div class="l1">' + h(x.ten) + '</div>' +
          '<div class="l2">' + h(x.ma) + ' · mẻ ' + num(x.so_luong) + ' ' + h(x.dvt || '') +
          (x.phien_ban ? ' · bản ' + h(x.phien_ban) : '') +
          (x.ban_truoc ? ' · có bản trước' : '') + '</div>' +
          ctNutHd(x) + '</div>' +
          '<div style="text-align:right" data-n="' + h(x.bom) + '"><div class="st ' + (CT_MAU_TT[x.trang_thai] || 'n') + '">' +
          h(CT_TEN_TT[x.trang_thai] || x.trang_thai) + '</div>' +
          '<div class="l2" style="margin-top:4px">' + h(x.sua_luc.slice(0, 10)) + '</div></div></div>';
      }).join('') + '</div>' +
      (ctD.tong > ctD.ds.length ? '<div style="text-align:center;font-size:12px;color:#98a2b3;padding:10px">Đang hiện ' + ctD.ds.length + ' trên ' + ctD.tong + ', gõ ô tìm để thu hẹp</div>' : '')
        : '<div class="emp"><div class="e1">📖</div><div class="e2">Không có công thức nào khớp bộ lọc</div></div>');

    var b = frame('Danh mục công thức', body,
      ctQuanLy() ? { fab: true, onFab: ctTaoMoi } : {});
    b.onclick = function (e) {
      var t = e.target.closest('[data-tab]');
      if (t) { ctD.tab = t.dataset.tab; ctD.ds = null; return scrCongThuc(); }
      var t2 = e.target.closest('[data-tt]');
      if (t2) { ctD.tt = t2.dataset.tt; ctD.ds = null; return scrCongThuc(); }
      var t3 = e.target.closest('[data-hd]');
      if (t3) { ctD.hd = t3.dataset.hd; ctD.ds = null; return scrCongThuc(); }
      /* Nut huong dan phai xet TRUOC the cong thuc: no nam LONG trong the,
         nen bam vao no cung la bam vao the. Xet the truoc thi khong bao gio
         toi luot nut. */
      var g = e.target.closest('[data-hdm]');
      if (g) {
        var mm = g.dataset.hdm, mt = g.dataset.hdt || mm;
        return go(function () { scrHuongDanSoan(mm, mt); });
      }
      var r = e.target.closest('[data-n]');
      if (r) { var nm = r.dataset.n; return go(function () { scrCongThucXem(nm); }); }
    };
    var ti = document.getElementById('ctTim');
    if (ti) {
      var cho = null;
      ti.oninput = function () {
        ctD.tim = ti.value;
        if (cho) clearTimeout(cho);
        cho = setTimeout(async function () {
          try { await ctTai(); } catch (e) { }
          var giu = document.activeElement === ti;
          var vt = ti.selectionStart;
          draw();
          if (giu) {
            var ti2 = document.getElementById('ctTim');
            if (ti2) { ti2.focus(); try { ti2.setSelectionRange(vt, vt); } catch (e) { } }
          }
        }, 420);
      };
    }
  }
  draw();
}

function ctTaoMoi() {
  mfgPickItem('Món cần lập công thức', leavesUnder(['Bán ra', 'Sản xuất']), async function (code) {
    busy(1);
    try {
      var it = await api('frappe.client.get', { doctype: 'Item', name: code });
      ctE = {
        bom: '', ma: code, ten: it.item_name || code,
        so_luong: 1, dvt: it.stock_uom, moi: 1, dong: []
      };
      go(scrCongThucSua);
    } catch (err) { toast(errMsg(err), 5000); } finally { busy(0); }
  });
}

async function scrCongThucXem(name) {
  frame('Công thức', '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api('vagabond.cong_thuc.chi_tiet', { name: name }); }
  catch (e) {
    frame('Công thức', '<div class="emp"><div class="e1">🔒</div><div>' + h(errMsg(e)) + '</div></div>');
    return;
  }
  var html = '<div class="card"><div class="kpg">' +
    '<div style="font-size:18px;font-weight:700;line-height:1.3">' + h(d.ten) + '</div>' +
    '<div style="font-size:12.5px;color:#8a8f9c;margin-top:5px">' + h(d.ma) + ' · ' + h(d.bom) +
    (d.chang ? ' · ' + h(d.chang) : '') + '</div></div>' +
    '<div class="stk">' +
    '<div><div class="s1">Trạng thái</div><div class="s2">' + h(CT_TEN_TT[d.trang_thai] || d.trang_thai) + '</div></div>' +
    '<div><div class="s1">Mẻ ra</div><div class="s2">' + num(d.so_luong) + ' ' + h(d.dvt || '') + '</div></div>' +
    '<div><div class="s1">Nguyên liệu</div><div class="s2">' + d.dong.length + ' dòng</div></div></div></div>';

  html += '<div class="sec">Nguyên liệu</div><div class="lst">' + d.dong.map(function (m) {
    return '<div class="li"><div class="lt"><div class="l1">' + h(m.ten || m.ma) + '</div>' +
      '<div class="l2">' + h(m.ma) +
      (m.note ? ' · <b style="color:#0b6bcb">' + h(m.note) + '</b>' : '') + '</div></div>' +
      '<div style="text-align:right"><div class="amt">' + num(m.sl) + '</div>' +
      '<div class="l2">' + h(m.dvt || '') + '</div></div></div>';
  }).join('') + '</div>';

  if (d.ban_truoc.length || d.ban_sau.length) {
    html += '<div class="sec">Chuỗi phiên bản</div><div class="card" style="padding:12px 14px;font-size:13px;line-height:1.9">' +
      d.ban_sau.map(function (x) { return '⬆️ Bản sau: <a data-v="' + h(x) + '" style="color:#0b6bcb;font-weight:600">' + h(x) + '</a><br>'; }).join('') +
      '▪️ Bản này: <b>' + h(d.bom) + '</b><br>' +
      d.ban_truoc.map(function (x) { return '⬇️ Bản trước: <a data-v="' + h(x) + '" style="color:#0b6bcb;font-weight:600">' + h(x) + '</a><br>'; }).join('') +
      '</div>';
  }

  var nut = '';
  if (d.trang_thai !== 'da_huy') {
    nut = '<button class="btn gh" id="ctHd" style="margin-bottom:9px">📖 Hướng dẫn chế biến</button>';
  }
  if (ctQuanLy()) {
    if (d.trang_thai === 'nhap') {
      nut += '<div class="row2"><button class="btn gh" id="ctSua">✏️ Sửa nháp</button>' +
        '<button class="btn gr" id="ctGhiSo">✅ Ghi sổ</button></div>' +
        '<button class="btn gh" id="ctBo" style="margin-top:9px;color:#b3261e">Bỏ bản nháp này</button>';
    } else if (d.trang_thai !== 'da_huy') {
      nut += '<button class="btn" id="ctDc">🔁 Điều chỉnh (ra phiên bản mới)</button>';
    }
  }
  var b = frame('Công thức', html, nut ? { footer: nut } : {});
  b.onclick = function (e) {
    var v = e.target.closest('[data-v]');
    if (v) return go(function () { scrCongThucXem(v.dataset.v); });
  };
  var nhd = document.getElementById('ctHd');
  if (nhd) nhd.onclick = function () { go(function () { scrHuongDanSoan(d.ma, d.ten); }); };
  var sua = document.getElementById('ctSua');
  if (sua) sua.onclick = function () { ctNapSua(d); };
  var gs = document.getElementById('ctGhiSo');
  if (gs) gs.onclick = async function () {
    if (!await confirmSheet('Ghi sổ công thức?',
      'Bản ' + d.bom + ' thành bản đang dùng. Lệnh sản xuất từ giờ nổ theo bản này.' +
      '\n\nGhi sổ xong muốn đổi thì phải Điều chỉnh ra phiên bản mới.', 'Ghi sổ')) return;
    busy(1);
    try { var r = await api('vagabond.cong_thuc.ghi_so', { bom_nhap: d.bom }); busy(0); toast(r.ghi_chu, 6000); }
    catch (err) { busy(0); return toast(errMsg(err), 7000); }
    ctD.ds = null;
    go(scrCongThuc, true);
  };
  var bo = document.getElementById('ctBo');
  if (bo) bo.onclick = async function () {
    if (!await confirmSheet('Bỏ bản nháp?', 'Bản nháp ' + d.bom + ' sẽ bị bỏ. Các bản đã ghi sổ không bị đụng tới.', 'Bỏ nháp')) return;
    busy(1);
    try { var r = await api('vagabond.cong_thuc.bo_nhap', { bom_nhap: d.bom }); busy(0); toast(r.ghi_chu, 5000); }
    catch (err) { busy(0); return toast(errMsg(err), 7000); }
    ctD.ds = null;
    go(scrCongThuc, true);
  };
  var dc = document.getElementById('ctDc');
  if (dc) dc.onclick = async function () {
    busy(1);
    var r;
    try { r = await api('vagabond.cong_thuc.dieu_chinh', { bom_cu: d.bom }); }
    catch (err) { busy(0); return toast(errMsg(err), 7000); }
    busy(0);
    toast(r.ghi_chu, 5500);
    var d2;
    try { busy(1); d2 = await api('vagabond.cong_thuc.chi_tiet', { name: r.bom_nhap }); }
    catch (e2) { busy(0); return go(function () { scrCongThucXem(r.bom_nhap); }, true); }
    busy(0);
    ctNapSua(d2);
  };
}

function ctNapSua(d) {
  ctE = {
    bom: d.bom, ma: d.ma, ten: d.ten, so_luong: d.so_luong, dvt: d.dvt, moi: 0,
    dong: d.dong.map(function (m) { return { ma: m.ma, ten: m.ten || m.ma, sl: m.sl, dvt: m.dvt }; })
  };
  go(scrCongThucSua, true);
}

function scrCongThucSua() {
  var st = ctE;
  if (!st) return go(scrCongThuc, true);

  function draw() {
    var body = '<div class="card" style="padding:13px 14px">' +
      '<div style="font-size:16px;font-weight:700">' + h(st.ten) + '</div>' +
      '<div style="font-size:12px;color:#8a8f9c;margin-top:3px">' + h(st.ma) +
      (st.bom ? ' · sửa bản nháp ' + h(st.bom) : ' · công thức mới') + '</div>' +
      '<div class="qw" style="margin-top:11px"><div style="flex:1;min-width:0"><div class="lb">Một mẻ ra được</div>' +
      '<div class="qr"><div class="stp"><button data-fm>&minus;</button>' +
      '<input type="number" inputmode="decimal" id="ctQ" value="' + st.so_luong + '"><button data-fp>+</button></div>' +
      '<div class="uml">' + h(st.dvt || '') + '</div></div></div></div></div>' +
      '<div class="sec">Nguyên liệu</div>' +
      (st.dong.length ? st.dong.map(function (m, i) {
        return '<div class="ic1"><div class="ih"><div class="n">' + (i + 1) + '</div>' +
          '<div class="in">' + h(m.ten) + '<div class="ig">' + h(m.ma) + '</div></div>' +
          '<div class="del" data-x="' + i + '">&times;</div></div>' +
          '<div class="qw"><div style="flex:1;min-width:0"><div class="lb">Số lượng cho một mẻ</div>' +
          '<div class="qr"><div class="stp"><button data-m="' + i + '">&minus;</button>' +
          '<input type="number" inputmode="decimal" data-q="' + i + '" value="' + m.sl + '">' +
          '<button data-p="' + i + '">+</button></div><div class="uml">' + h(m.dvt || '') + '</div></div></div></div></div>';
      }).join('') : '<div class="emp" style="padding:24px"><div class="e2">Chưa có dòng nguyên liệu nào</div></div>') +
      '<button class="btn gh" id="ctThem">+ Thêm nguyên liệu</button>';

    var b = frame(st.bom ? 'Sửa công thức' : 'Công thức mới', body, {
      footer: '<div class="row2"><button class="btn gh" id="ctLuu">💾 Lưu nháp</button>' +
        '<button class="btn gr" id="ctLuuGhi">✅ Lưu và ghi sổ</button></div>'
    });
    b.addEventListener('input', function (e) {
      var t = e.target;
      if (t.id === 'ctQ') st.so_luong = parseFloat(t.value) || 0;
      if (t.dataset.q != null) st.dong[+t.dataset.q].sl = parseFloat(t.value) || 0;
    });
    b.onclick = function (e) {
      var t = e.target;
      if (t.hasAttribute && t.hasAttribute('data-fm')) { st.so_luong = Math.max(0, r3(st.so_luong - 1)); return draw(); }
      if (t.hasAttribute && t.hasAttribute('data-fp')) { st.so_luong = r3(st.so_luong + 1); return draw(); }
      if (t.dataset && t.dataset.x != null) { st.dong.splice(+t.dataset.x, 1); return draw(); }
      if (t.dataset && t.dataset.m != null) { var i = +t.dataset.m; st.dong[i].sl = Math.max(0, r3(st.dong[i].sl - 1)); return draw(); }
      if (t.dataset && t.dataset.p != null) { var j = +t.dataset.p; st.dong[j].sl = r3(st.dong[j].sl + 1); return draw(); }
    };
    document.getElementById('ctThem').onclick = function () {
      mfgPickItem('Thêm nguyên liệu', leavesUnder(['Mua vào', 'Sản xuất']), async function (code) {
        if (st.dong.some(function (x) { return x.ma === code; })) return toast('Nguyên liệu này đã có trong công thức');
        busy(1);
        try {
          var it = await api('frappe.client.get', { doctype: 'Item', name: code });
          st.dong.push({ ma: code, ten: it.item_name || code, sl: 0, dvt: it.stock_uom });
          draw();
        } catch (err) { toast(errMsg(err), 5000); } finally { busy(0); }
      });
    };
    async function luu(ghiSo) {
      if (!st.dong.length) return toast('Công thức phải có ít nhất một dòng nguyên liệu.');
      if (st.dong.some(function (x) { return !(x.sl > 0); })) return toast('Có nguyên liệu chưa nhập số lượng.');
      if (!(st.so_luong > 0)) return toast('Chưa nhập mẻ ra được bao nhiêu.');
      if (ghiSo && !await confirmSheet('Lưu và ghi sổ?',
        'Công thức thành bản đang dùng ngay, lệnh sản xuất nổ theo bản này.' +
        (st.bom ? '' : ' Món chưa có công thức nào thì đây là bản đầu tiên.'), 'Ghi sổ')) return;
      busy(1);
      var dong = st.dong.map(function (x) { return { ma: x.ma, sl: x.sl, dvt: x.dvt }; });
      var ten_nhap = st.bom;
      try {
        if (!ten_nhap) {
          var r1 = await api('vagabond.cong_thuc.tao_moi',
            { ma_item: st.ma, so_luong: st.so_luong, dvt: st.dvt, dong: JSON.stringify(dong) });
          ten_nhap = r1.bom_nhap;
          st.bom = ten_nhap;
        } else {
          await api('vagabond.cong_thuc.sua_nhap',
            { bom_nhap: ten_nhap, so_luong: st.so_luong, dong: JSON.stringify(dong) });
        }
        if (ghiSo) {
          var r2 = await api('vagabond.cong_thuc.ghi_so', { bom_nhap: ten_nhap });
          busy(0);
          toast(r2.ghi_chu, 6000);
        } else {
          busy(0);
          toast('Đã lưu bản nháp ' + ten_nhap + '. Ghi sổ lúc nào cũng được.', 5000);
        }
      } catch (err) { busy(0); return toast(errMsg(err), 7000); }
      ctE = null;
      ctD.ds = null;
      go(scrCongThuc, true);
    }
    document.getElementById('ctLuu').onclick = function () { luu(false); };
    document.getElementById('ctLuuGhi').onclick = function () { luu(true); };
  }
  draw();
}

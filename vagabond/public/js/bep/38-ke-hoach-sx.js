
/* ---------- 38. Lap ke hoach san xuat (28/08/2026) ----------

   Anh Viet: nut "Lap ke hoach san xuat", ghi chu "tinh toan nguyen vat
   lieu, ban thanh pham, thanh pham san xuat trong ngay".

   0h dem may tu lap phieu cho ngay vua sang, gom moi phieu YCSX cac diem
   ban va sales online da gui. 5h sang bep vao ca mo man nay ra doc.

   Man nay KHONG tu tinh mot con so nao. Moi phep no BOM la phep cua
   Production Plan ben ERPNext, may chu chi don ket qua ra. Nho vay man
   app va man Desk luon noi cung mot con so - do la yeu cau "luon dong bo
   giua 2 ban" cua anh Viet. Tinh o day thi hai ban lech nhau ngay tuan
   sau, ma luc lech khong ai biet ben nao dung.

   Ba tab:
     Thanh pham   mon ban ra, tu YCSX
     BTP          ban thanh pham, xo ra duoc danh sach NVL cua tung mon
     NVL          tong nguyen lieu ca ngay, kem ton kho tong */

var khsx = { ngay: '', d: null, tab: 'tp', bep: '', muc: '', tim: '', mo: {} };

var KHSX_TAB = [['tp', '🎂 Thành phẩm'], ['btp', '🥣 Bán thành phẩm'], ['nvl', '🌾 Nguyên liệu']];
var KHSX_BEP = [['', '🏠 Cả hai bếp'], ['pastry', '🎂 Pastry'], ['baker', '🥐 Baker']];
/* Chip loc theo tinh trang. "Phai lam" dung dau vi do la cau hoi dau tien
   cua bep luc 5h sang: hom nay phai lam nhung gi. */
var KHSX_MUC = [['', 'Tất cả'], ['thieu', '🔴 Phải làm'], ['mot_phan', '🟡 Thiếu một phần'],
  ['da_co_lenh', '⚙️ Đã có lệnh'], ['du', '🟢 Đủ tồn']];

function khsxQuanLy() {
  return hasRole('Manufacturing Manager') || hasRole('System Manager') ||
    hasRole('Giám đốc') || hasRole('AP Giám đốc');
}

function khsxNgayVN(s) {
  if (!s) return '';
  var p = String(s).slice(0, 10).split('-');
  return p.length === 3 ? (p[2] + '/' + p[1] + '/' + p[0]) : s;
}

async function khsxTai() {
  khsx.d = await api('vagabond.ke_hoach_sx.xem', { ngay: khsx.ngay || null });
  if (khsx.d && khsx.d.ngay) khsx.ngay = khsx.d.ngay;
}

/* Bon cot so cua mot dong. Dat canh nhau dung thu tu de bep doc mot mach:
   can bao nhieu, dau ngay co gi, gio con gi, vay con phai lam bao nhieu. */
function khsxCot(x, coKhoGoc) {
  var o = '<div class="stk" style="margin:8px 0 0">' +
    '<div><div class="s1">Cần</div><div class="s2">' + num(x.can) + '</div></div>' +
    '<div><div class="s1">Tồn đầu</div><div class="s2">' + num(x.ton_dau) + '</div></div>' +
    '<div><div class="s1">Tồn giờ</div><div class="s2">' + num(x.ton_nay) + '</div></div>';
  if (coKhoGoc) o += '<div><div class="s1">Kho tổng</div><div class="s2">' + num(x.ton_goc) + '</div></div>';
  o += '<div><div class="s1">Phải làm</div><div class="s2" style="color:' +
    (x.con_lam > 0 ? '#b3261e' : '#0f766e') + '">' + num(x.con_lam) + '</div></div></div>';
  return o;
}

function khsxThe(x, loai) {
  /* Nut tao lenh chi hien khi phieu da chot VA con phai lam. Hien nut tren
     phieu nhap thi bam vao chi an mot cau tu choi cua ERPNext, khong giup
     duoc gi. */
  var nut = '';
  if (khsx.d.da_chot && khsxQuanLy() && x.con_lam > 0 && loai !== 'nvl') {
    nut = '<button class="btn gh" data-lenh="' + h(x.khoa) + '" data-loai="' + h(loai) +
      '" style="margin-top:8px">⚙️ Tạo lệnh sản xuất</button>';
  }
  var phu = h(x.ma) + (x.dvt ? ' · ' + h(x.dvt) : '') +
    (x.chip_chang ? ' · ' + h(x.chip_chang) : '') +
    (x.bep ? ' · ' + h(x.bep === 'baker' ? 'Baker' : 'Pastry') : '') +
    (x.da_lenh > 0 ? ' · đã ra lệnh ' + num(x.da_lenh) : '');
  var xo = '';
  if (loai === 'btp' && (x.nvl || []).length) {
    var dangMo = !!khsx.mo[x.khoa];
    xo = '<div data-xo="' + h(x.khoa) + '" style="margin-top:8px;font-size:12.5px;color:#0b6bcb;font-weight:600">' +
      (dangMo ? '▾ Ẩn ' : '▸ Xem ') + x.nvl.length + ' nguyên liệu</div>';
    if (dangMo) {
      xo += '<div style="margin-top:6px;border-left:2px solid #e3e6ee;padding-left:10px">' +
        x.nvl.map(function (n) {
          return '<div style="padding:6px 0;border-bottom:1px solid #f1f3f7">' +
            '<div style="font-size:13px;font-weight:600">' + h(n.ten) + '</div>' +
            '<div class="l2">' + h(n.ma) + ' · cần ' + num(n.can) + ' ' + h(n.dvt) +
            ' · tồn bếp ' + num(n.ton_nay) + ' · kho tổng ' + num(n.ton_goc) +
            (n.con_lam > 0 ? ' · <b style="color:#b3261e">thiếu ' + num(n.con_lam) + '</b>' : '') +
            '</div></div>';
        }).join('') + '</div>';
    }
  }
  return '<div class="li" style="display:block"><div style="display:flex;justify-content:space-between;gap:10px">' +
    '<div class="lt"><div class="l1">' + h(x.ten) + '</div><div class="l2">' + phu + '</div></div>' +
    '<div class="st ' + h(x.mau) + '" style="flex:none">' + h(x.ten_muc) + '</div></div>' +
    khsxCot(x, loai === 'nvl') + xo + nut + '</div>';
}

async function scrKeHoachSX() {
  if (!khsx.d) {
    frame('Kế hoạch sản xuất', '<div class="emp"><div class="e1">⏳</div></div>');
    try { await khsxTai(); }
    catch (e) {
      frame('Kế hoạch sản xuất', '<div class="emp"><div class="e1">🔒</div><div>' + h(errMsg(e)) + '</div></div>');
      return;
    }
  }

  function draw() {
    var d = khsx.d;
    var dau = '<div class="card" style="padding:12px 14px">' +
      '<div style="display:flex;justify-content:space-between;align-items:center;gap:10px">' +
      '<div><div style="font-size:12px;color:#8a8f9c">Ngày bếp làm</div>' +
      '<div style="font-size:17px;font-weight:700">' + h(khsxNgayVN(d.ngay)) + '</div></div>' +
      '<div style="display:flex;gap:6px">' +
      '<button class="chip" data-lui="1">◀ Hôm trước</button>' +
      '<button class="chip" data-toi="1">Hôm sau ▶</button></div></div>' +
      (d.co_phieu ? '<div class="l2" style="margin-top:7px">Phiếu ' + h(d.ten) +
        ' · ' + (d.da_chot ? '<b style="color:#0f766e">đã chốt</b>' : '<b style="color:#b3261e">còn nháp</b>') +
        ' · gom ' + d.so_ycsx + ' phiếu yêu cầu' +
        (d.qua_han ? ' · <b style="color:#b3261e">' + d.qua_han + ' phiếu quá hạn</b>' : '') +
        (d.tu_dong ? ' · máy tự lập' : '') + '</div>' : '') +
      '</div>';

    var loi = '<div style="font-size:12.5px;color:#0f766e;background:#ccfbf1;border-radius:8px;padding:8px 11px;margin-bottom:9px;line-height:1.5">📋 ' +
      h(d.tom_tat || '') + '</div>';

    if (!d.co_phieu) {
      var b0 = frame('Kế hoạch sản xuất', dau + loi +
        '<div class="emp"><div class="e1">📋</div><div class="e2">Ngày này chưa có phiếu kế hoạch</div></div>',
        khsxQuanLy() ? { footer: '<button class="btn gr" id="khsxLap">📋 Lập kế hoạch cho ngày này</button>' } : {});
      khsxGan(b0, draw);
      var nl = document.getElementById('khsxLap');
      if (nl) nl.onclick = khsxLap;
      return;
    }

    var tabs = KHSX_TAB.map(function (c) {
      var so = c[0] === 'tp' ? d.thanh_pham.length : (c[0] === 'btp' ? d.btp.length : d.nvl.length);
      return '<div class="chip' + (khsx.tab === c[0] ? ' on' : '') + '" data-tab="' + c[0] + '">' +
        c[1] + ' <b>' + so + '</b></div>';
    }).join('');
    var beps = KHSX_BEP.map(function (c) {
      return '<div class="chip' + (khsx.bep === c[0] ? ' on' : '') + '" data-bep="' + c[0] + '">' + c[1] + '</div>';
    }).join('');
    var mucs = KHSX_MUC.map(function (c) {
      return '<div class="chip' + (khsx.muc === c[0] ? ' on' : '') + '" data-muc="' + c[0] + '">' + c[1] + '</div>';
    }).join('');

    var goc = khsx.tab === 'tp' ? d.thanh_pham : (khsx.tab === 'btp' ? d.btp : d.nvl);
    var q = (khsx.tim || '').toLowerCase();
    var ds = goc.filter(function (x) {
      if (khsx.bep && x.bep !== khsx.bep) return false;
      if (khsx.muc && x.muc !== khsx.muc) return false;
      if (q && (x.ten + ' ' + x.ma).toLowerCase().indexOf(q) < 0) return false;
      return true;
    });

    var than = dau + loi +
      '<div class="chips">' + tabs + '</div>' +
      '<div class="chips">' + beps + '</div>' +
      '<div class="chips">' + mucs + '</div>' +
      '<input class="tin" id="khsxTim" placeholder="Tìm theo tên hoặc mã món" value="' + h(khsx.tim) + '" ' +
      'style="text-align:left;font-size:14.5px;padding:0 13px;margin-bottom:9px;width:100%">' +
      (ds.length ? '<div class="lst">' + ds.map(function (x) { return khsxThe(x, khsx.tab); }).join('') + '</div>'
        : '<div class="emp"><div class="e1">🔍</div><div class="e2">Không có dòng nào khớp bộ lọc</div></div>');

    var nut = '';
    if (khsxQuanLy()) {
      if (!d.da_chot) {
        nut = '<button class="btn gr" id="khsxChot">✅ Chốt kế hoạch</button>';
      } else {
        nut = '<button class="btn gh" id="khsxXin">📦 Xin chuyển nguyên liệu từ kho tổng</button>';
      }
    }
    var b = frame('Kế hoạch sản xuất', than, nut ? { footer: nut } : {});
    khsxGan(b, draw);

    var nc = document.getElementById('khsxChot');
    if (nc) nc.onclick = khsxChot;
    var nx = document.getElementById('khsxXin');
    if (nx) nx.onclick = khsxXinNvl;

    var ti = document.getElementById('khsxTim');
    if (ti) {
      var cho = null;
      ti.oninput = function () {
        khsx.tim = ti.value;
        if (cho) clearTimeout(cho);
        cho = setTimeout(function () {
          var vt = ti.selectionStart, giu = document.activeElement === ti;
          draw();
          if (giu) {
            var t2 = document.getElementById('khsxTim');
            if (t2) { t2.focus(); try { t2.setSelectionRange(vt, vt); } catch (e) { } }
          }
        }, 320);
      };
    }
  }

  function khsxGan(b, ve) {
    b.onclick = async function (e) {
      var t = e.target.closest('[data-tab]');
      if (t) { khsx.tab = t.dataset.tab; return ve(); }
      var bp = e.target.closest('[data-bep]');
      if (bp) { khsx.bep = bp.dataset.bep; return ve(); }
      var mc = e.target.closest('[data-muc]');
      if (mc) { khsx.muc = mc.dataset.muc; return ve(); }
      var xo = e.target.closest('[data-xo]');
      if (xo) { var k = xo.dataset.xo; khsx.mo[k] = !khsx.mo[k]; return ve(); }
      var lui = e.target.closest('[data-lui]');
      if (lui) return khsxDoiNgay(-1);
      var toi = e.target.closest('[data-toi]');
      if (toi) return khsxDoiNgay(1);
      var lenh = e.target.closest('[data-lenh]');
      if (lenh) return khsxTaoLenh(lenh.dataset.lenh, lenh.dataset.loai);
    };
  }

  draw();
}

function khsxDoiNgay(buoc) {
  var d = new Date(khsx.ngay + 'T00:00:00');
  d.setDate(d.getDate() + buoc);
  var p = function (n) { return ('0' + n).slice(-2); };
  khsx.ngay = d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
  khsx.d = null;
  khsx.mo = {};
  return scrKeHoachSX();
}

async function khsxLap() {
  if (!await confirmSheet('Lập kế hoạch cho ngày ' + khsxNgayVN(khsx.ngay) + '?',
    'Máy gom mọi phiếu yêu cầu sản xuất hẹn ngày này (kể cả phiếu quá hạn chưa làm) ' +
    'rồi nổ ra thành phẩm, bán thành phẩm và nguyên liệu.\n\nPhiếu lập ra ở dạng nháp, ' +
    'chưa tạo lệnh sản xuất nào cả.', 'Lập kế hoạch')) return;
  busy(1);
  try {
    var r = await api('vagabond.ke_hoach_sx.lap', { ngay: khsx.ngay, chay_that: 1 });
    toast(r.ghi_chu, 6000);
    khsx.d = null;
    await scrKeHoachSX();
  } catch (e) { toast(errMsg(e), 6000); } finally { busy(0); }
}

async function khsxChot() {
  if (!await confirmSheet('Chốt kế hoạch ' + khsx.d.ten + '?',
    'Chốt xong mới tạo được lệnh sản xuất. Muốn sửa số sau khi chốt thì phải huỷ ' +
    'phiếu rồi lập lại, nên đọc kỹ các con số trước khi bấm.', 'Chốt kế hoạch')) return;
  busy(1);
  try {
    var r = await api('vagabond.ke_hoach_sx.chot', { ten: khsx.d.ten });
    toast(r.ghi_chu, 5000);
    khsx.d = null;
    await scrKeHoachSX();
  } catch (e) { toast(errMsg(e), 6000); } finally { busy(0); }
}

async function khsxTaoLenh(khoa, loai) {
  busy(1);
  try {
    var r = await api('vagabond.ke_hoach_sx.tao_lenh',
      { ten: khsx.d.ten, khoa: khoa, loai: loai === 'tp' ? 'tp' : 'btp' });
    toast(r.ghi_chu, 5000);
    khsx.d = null;
    await scrKeHoachSX();
  } catch (e) { toast(errMsg(e), 6000); } finally { busy(0); }
}

async function khsxXinNvl() {
  if (!await confirmSheet('Xin chuyển nguyên liệu từ kho tổng?',
    'Máy tạo phiếu xin chuyển kho từ Kho tổng 307 sang kho nguyên liệu của bếp, ' +
    'đúng theo bảng nguyên liệu của kế hoạch này.\n\nPhiếu ở dạng nháp, anh Kiên ' +
    'còn xem kho tổng có đủ hàng không rồi mới ghi sổ.', 'Tạo phiếu xin')) return;
  busy(1);
  try {
    var r = await api('vagabond.ke_hoach_sx.xin_chuyen_nvl', { ten: khsx.d.ten });
    toast(r.ghi_chu, 7000);
  } catch (e) { toast(errMsg(e), 6000); } finally { busy(0); }
}

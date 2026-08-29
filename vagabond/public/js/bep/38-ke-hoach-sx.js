
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

var khsx = { ngay: '', d: null, tab: 'tp', bep: '', muc: '', tim: '', mo: {}, chon: {} };

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
    '<div><div class="s1">Cần</div><div class="s2">' + kl(x.can, x.dvt) + '</div></div>' +
    '<div><div class="s1">Tồn đầu</div><div class="s2">' + kl(x.ton_dau, x.dvt) + '</div></div>' +
    '<div><div class="s1">Tồn giờ</div><div class="s2">' + kl(x.ton_nay, x.dvt) + '</div></div>';
  if (coKhoGoc) o += '<div><div class="s1">Kho tổng</div><div class="s2">' + kl(x.ton_goc, x.dvt) + '</div></div>';
  o += '<div><div class="s1">Phải làm</div><div class="s2" style="color:' +
    (x.con_lam > 0 ? '#b3261e' : '#0f766e') + '">' + kl(x.con_lam, x.dvt) + '</div></div></div>';
  return o;
}

function khsxThe(x, loai) {
  /* Nut tao lenh chi hien khi phieu da chot VA con phai lam. Hien nut tren
     phieu nhap thi bam vao chi an mot cau tu choi cua ERPNext, khong giup
     duoc gi. */
  /* Nut tao lenh hien ngay ca khi phieu con nhap: buoc ghi so lui xuong
     server, chay ngam o lan ra lenh dau tien. Anh Viet 29/08/2026 bo nut
     chot tong vi bep khong chot ca phieu mot luot duoc. */
  var nut = '', tick = '';
  if (khsxQuanLy() && x.con_lam > 0 && loai !== 'nvl') {
    nut = '<button class="btn gh" data-lenh="' + h(x.khoa) + '" data-loai="' + h(loai) +
      '" style="margin-top:8px">⚙️ Tạo lệnh sản xuất</button>';
    tick = '<div class="chip' + (khsx.chon[x.khoa] ? ' on' : '') + '" data-tick="' + h(x.khoa) +
      '" data-tloai="' + h(loai) + '" style="flex:none;margin-right:8px">' +
      (khsx.chon[x.khoa] ? '☑' : '☐') + '</div>';
  }
  var phu = h(x.ma) + (x.dvt ? ' · ' + h(x.dvt) : '') +
    (loai !== 'nvl' ? ' · nhập ' + (x.kho_dich ? h(shortWh(x.kho_dich)) :
      '<b style="color:#b3261e">chưa có kho</b>') : '') +
    (x.kho_giao ? ' · giao ' + h(shortWh(x.kho_giao)) : '') +
    (x.chip_chang ? ' · ' + h(x.chip_chang) : '') +
    (x.bep ? ' · ' + h(x.bep === 'baker' ? 'Baker' : 'Pastry') : '') +
    (x.da_lenh > 0 ? ' · đã ra lệnh ' + kl(x.da_lenh, x.dvt) : '') +
    (x.so_nguon > 1 ? ' · gom ' + x.so_nguon + ' phiếu' : '');
  var xo = '';
  /* Thanh pham gom theo ma nen mot the co the la sau phieu yeu cau cua sau
     diem ban. Xo ra cho bep thay so do cua ai, khong thi con so trong ma
     khong ai truy lai duoc. */
  if (loai === 'tp' && (x.nguon || []).length > 1) {
    var dangMoN = !!khsx.mo[x.khoa];
    xo = '<div data-xo="' + h(x.khoa) + '" style="margin-top:8px;font-size:12.5px;color:#0b6bcb;font-weight:600">' +
      (dangMoN ? '▾ Ẩn ' : '▸ Xem ') + x.nguon.length + ' phiếu yêu cầu</div>';
    if (dangMoN) {
      xo += '<div style="margin-top:6px;border-left:2px solid #e3e6ee;padding-left:10px">' +
        x.nguon.map(function (n) {
          return '<div class="l2" style="padding:4px 0">' + h(n.ycsx) + ' · ' +
            h(shortWh(n.kho || '')) + ' · <b>' + kl(n.sl, x.dvt) + '</b></div>';
        }).join('') + '</div>';
    }
  }
  if (loai === 'btp' && (x.nvl || []).length) {
    var dangMo = !!khsx.mo[x.khoa];
    xo = '<div data-xo="' + h(x.khoa) + '" style="margin-top:8px;font-size:12.5px;color:#0b6bcb;font-weight:600">' +
      (dangMo ? '▾ Ẩn ' : '▸ Xem ') + x.nvl.length + ' nguyên liệu</div>';
    if (dangMo) {
      xo += '<div style="margin-top:6px;border-left:2px solid #e3e6ee;padding-left:10px">' +
        x.nvl.map(function (n) {
          return '<div style="padding:6px 0;border-bottom:1px solid #f1f3f7">' +
            '<div style="font-size:13px;font-weight:600">' + h(n.ten) + '</div>' +
            '<div class="l2">' + h(n.ma) + ' · cần ' + kl(n.can, n.dvt) +
            ' · tồn bếp ' + kl(n.ton_nay, n.dvt) + ' · kho tổng ' + kl(n.ton_goc, n.dvt) +
            (n.con_lam > 0 ? ' · <b style="color:#b3261e">thiếu ' + kl(n.con_lam, n.dvt) + '</b>' : '') +
            '</div></div>';
        }).join('') + '</div>';
    }
  }
  return '<div class="li" style="display:block"><div style="display:flex;justify-content:space-between;gap:10px;align-items:flex-start">' +
    tick + anhMon(x.anh) +
    '<div class="lt" style="margin-left:9px"><div class="l1">' + h(x.ten) + '</div><div class="l2">' + phu + '</div></div>' +
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
      '<div style="display:flex;gap:6px;margin-top:8px"><div class="chip" data-dsp="1">📑 Các phiếu kế hoạch</div></div>' +
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

    /* KHONG con nut "Chot ke hoach". Anh Viet 29/08/2026: chot ca phieu
       mot luot thi kho, ma chot xong cung khong biet phieu nam dau. Nay
       bep tick chon tung mon roi ra lenh; buoc ghi so phieu chay ngam ben
       server o lan ra lenh dau tien. */
    var daChon = Object.keys(khsx.chon).filter(function (k) { return khsx.chon[k]; });
    var nut = '';
    if (khsxQuanLy()) {
      nut = daChon.length
        ? '<button class="btn gr" id="khsxLenhLo">⚙️ Tạo lệnh cho ' + daChon.length + ' món đã chọn</button>'
        : '<div class="row2"><button class="btn gh" id="khsxXin">📦 Xin chuyển nguyên liệu</button>' +
          '<button class="btn gh" id="khsxMoLenh">🏭 Xem lệnh đã tạo</button></div>';
    }
    var b = frame('Kế hoạch sản xuất', than, nut ? { footer: nut } : {});
    khsxGan(b, draw);

    var nx = document.getElementById('khsxXin');
    if (nx) nx.onclick = khsxXinNvl;
    var nm = document.getElementById('khsxMoLenh');
    if (nm) nm.onclick = function () { go(scrMfgList); };
    var nlo = document.getElementById('khsxLenhLo');
    if (nlo) nlo.onclick = function () { khsxTaoLenhLo(daChon); };

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
      var dsp = e.target.closest('[data-dsp]');
      if (dsp) return go(scrKhsxDsPhieu);
      var lui = e.target.closest('[data-lui]');
      if (lui) return khsxDoiNgay(-1);
      var toi = e.target.closest('[data-toi]');
      if (toi) return khsxDoiNgay(1);
      var tk = e.target.closest('[data-tick]');
      if (tk) {
        var kk = tk.dataset.tick;
        khsx.chon[kk] = khsx.chon[kk] ? 0 : { khoa: kk, loai: tk.dataset.tloai };
        return ve();
      }
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

/* Tim mot dong trong ban dang xem theo khoa, de biet don vi va so can. */
function khsxDong(khoa) {
  var d = khsx.d || {};
  var ds = (d.thanh_pham || []).concat(d.btp || []);
  for (var i = 0; i < ds.length; i++) if (ds[i].khoa === khoa) return ds[i];
  return null;
}

/* To nhap so luong va chon kho truoc khi ra lenh.

   Anh Viet 29/08/2026: bep hay lam chan me nen nhieu hon so may can, va
   "lo co nhung mon ca 2 bep deu dung thi sao" nen kho phai doi duoc. So
   mac dinh van la so may tinh; phan lam doi ra thanh mot lenh rieng khong
   gan vao phieu yeu cau nao, phia server lo. */
function khsxToLenh(x) {
  return new Promise(function (res) {
    var kho = x.kho_dich || '';
    var cac = (khsx.d && khsx.d.cac_kho) || [];
    if (kho && cac.indexOf(kho) < 0) cac = [kho].concat(cac);
    var ov = document.createElement('div'); ov.className = 'sh';
    ov.innerHTML = '<div class="shb" style="padding:18px 16px calc(env(safe-area-inset-bottom,0px) + 16px)">' +
      '<div style="font-size:17.5px;font-weight:700;margin-bottom:3px">Tạo lệnh sản xuất</div>' +
      '<div class="l2" style="margin-bottom:14px">' + h(x.ten) + ' · ' + h(x.ma) + '</div>' +
      '<div class="l2" style="margin-bottom:5px">Số lượng làm (' + h(x.dvt || '') + ')</div>' +
      '<input class="tin" id="khsxSl" inputmode="decimal" value="' + (Math.round((x.con_lam || 0) * 100) / 100) + '" ' +
      'style="text-align:left;font-size:16px;padding:0 13px;width:100%">' +
      '<div class="l2" style="margin:12px 0 5px">Nhập thành phẩm vào kho</div>' +
      '<select class="tin" id="khsxKho" style="text-align:left;font-size:15px;padding:0 9px;width:100%">' +
      (kho ? '' : '<option value="">-- chưa chọn kho --</option>') +
      cac.map(function (w) {
        return '<option value="' + h(w) + '"' + (w === kho ? ' selected' : '') + '>' + h(shortWh(w)) + '</option>';
      }).join('') + '</select>' +
      '<div class="l2" style="margin-top:9px;line-height:1.5">Máy cần ' + kl(x.con_lam, x.dvt) +
      '. Gõ nhiều hơn thì phần dôi ra thành một lệnh riêng, không tính vào phiếu yêu cầu của điểm bán nào.</div>' +
      '<button class="btn" data-y style="margin-top:14px">Tạo lệnh</button>' +
      '<button class="btn gh" data-n style="margin-top:9px">Huỷ</button></div>';
    document.body.appendChild(ov);
    ov.onclick = function (e) {
      if (e.target === ov || e.target.hasAttribute('data-n')) { ov.remove(); return res(null); }
      if (e.target.hasAttribute('data-y')) {
        var sl = parseFloat(String(ov.querySelector('#khsxSl').value).replace(/[^0-9.]/g, ''));
        var w = ov.querySelector('#khsxKho').value;
        if (!(sl > 0)) { toast('Số lượng phải lớn hơn 0'); return; }
        if (!w) { toast('Chọn kho nhập thành phẩm đã'); return; }
        ov.remove();
        res({ so_luong: sl, kho: w });
      }
    };
  });
}

async function khsxTaoLenh(khoa, loai) {
  var x = khsxDong(khoa);
  if (!x) return toast('Không thấy dòng này nữa, tải lại màn hình rồi thử lại');
  var c = await khsxToLenh(x);
  if (!c) return;
  busy(1);
  try {
    var r = await api('vagabond.ke_hoach_sx.tao_lenh',
      { ten: khsx.d.ten, khoa: khoa, loai: loai === 'tp' ? 'tp' : 'btp',
        so_luong: c.so_luong, kho: c.kho });
    toast(r.ghi_chu, 6000);
    delete khsx.chon[khoa];
    khsx.d = null;
    await scrKeHoachSX();
  } catch (e) { toast(errMsg(e), 6000); } finally { busy(0); }
}

/* Ra lenh hang loat cho cac mon da tick. Khong hoi so luong tung mon: lo
   nay la duong nhanh cho "lam dung so may can", muon sua so thi bam nut
   tren tung the. */
async function khsxTaoLenhLo(cacKhoa) {
  var ds = cacKhoa.map(function (k) { return khsx.chon[k]; }).filter(Boolean);
  if (!ds.length) return;
  if (!await confirmSheet('Tạo lệnh cho ' + ds.length + ' món?',
    'Máy ra lệnh đúng số cần làm và nhập vào kho máy đoán cho từng món.\n\n' +
    'Muốn sửa số hoặc đổi kho thì huỷ, rồi bấm nút Tạo lệnh trên từng thẻ.',
    'Tạo ' + ds.length + ' lệnh')) return;
  busy(1);
  var xong = [], loi = [];
  try {
    for (var i = 0; i < ds.length; i++) {
      try {
        var r = await api('vagabond.ke_hoach_sx.tao_lenh',
          { ten: khsx.d.ten, khoa: ds[i].khoa, loai: ds[i].loai === 'tp' ? 'tp' : 'btp' });
        if (r.ok) { xong = xong.concat(r.lenh || []); delete khsx.chon[ds[i].khoa]; }
        else loi.push(r.ghi_chu);
      } catch (e) { loi.push(errMsg(e)); }
    }
  } finally { busy(0); }
  toast('Đã tạo ' + xong.length + ' lệnh' + (loi.length ? ', ' + loi.length + ' món không tạo được: ' + loi[0] : '') +
    '. Bấm Xem lệnh đã tạo để mở danh sách.', 7000);
  khsx.d = null;
  await scrKeHoachSX();
}

async function khsxXinNvl() {
  if (!await confirmSheet('Xin chuyển nguyên liệu từ kho tổng?',
    'Máy tạo phiếu xin chuyển kho từ Kho tổng 307 sang kho nguyên liệu của bếp, ' +
    'đúng theo bảng nguyên liệu của kế hoạch này.\n\nPhiếu ở dạng NHÁP, kho tổng ' +
    'còn soát hàng rồi mới ghi sổ. Bấm xong máy hiện số phiếu vừa tạo.', 'Tạo phiếu xin')) return;
  busy(1);
  try {
    var r = await api('vagabond.ke_hoach_sx.xin_chuyen_nvl',
      { ten: khsx.d.ten, bep: khsx.bep || null });
    toast(r.ghi_chu, 9000);
    if (r.ok && (r.phieu || []).length) {
      khsx.d = null;
      await scrKeHoachSX();
    }
  } catch (e) { toast(errMsg(e), 7000); } finally { busy(0); }
}

/* ---------- Danh muc phieu ke hoach, kem nut huy ----------

   Anh Viet 29/08/2026: "Danh muc phieu ke hoach san xuat da chot hien
   khong co man nay (can huy/sua phieu)".

   ERPNext KHONG cho sua phieu da ghi so, chi cho huy roi lap lai. Nen o
   day cung chi co nut Huy, khong hua sua: hua sua roi de ERPNext bao loi
   thi te hon la noi thang tu dau. */
async function scrKhsxDsPhieu() {
  frame('Các phiếu kế hoạch', '<div class="emp"><div class="e1">⏳</div></div>');
  var ds = [];
  try { ds = await api('vagabond.ke_hoach_sx.ds_phieu', { so_ngay: 30 }); }
  catch (e) { toast(errMsg(e), 6000); }

  function draw() {
    var body = ds.length ? '<div class="lst">' + ds.map(function (p) {
      return '<div class="li" style="display:block">' +
        '<div style="display:flex;justify-content:space-between;gap:10px">' +
        '<div class="lt"><div class="l1">' + h(khsxNgayVN(p.ngay)) + '</div>' +
        '<div class="l2">' + h(p.ten) + (p.tu_dong ? ' · máy tự lập' : '') + '</div></div>' +
        '<div class="st ' + (p.da_chot ? 'g' : 'b') + '" style="flex:none">' +
        (p.da_chot ? 'Đã ghi sổ' : 'Còn nháp') + '</div></div>' +
        '<div class="row2" style="margin-top:9px">' +
        '<button class="btn gh" data-mo="' + h(p.ngay) + '">Mở phiếu</button>' +
        '<button class="btn gh" data-huy="' + h(p.ten) + '" style="color:#b3261e">🗑️ Huỷ phiếu</button>' +
        '</div></div>';
    }).join('') + '</div>'
      : '<div class="emp"><div class="e1">📑</div><div class="e2">Chưa có phiếu kế hoạch nào trong 30 ngày</div></div>';
    var b = frame('Các phiếu kế hoạch', body);
    b.onclick = async function (e) {
      var mo = e.target.closest('[data-mo]');
      if (mo) {
        khsx.ngay = mo.dataset.mo; khsx.d = null; khsx.mo = {}; khsx.chon = {};
        return go(scrKeHoachSX);
      }
      var hu = e.target.closest('[data-huy]');
      if (!hu) return;
      var ten = hu.dataset.huy;
      if (!await confirmSheet('Huỷ phiếu ' + ten + '?',
        'Phiếu còn nháp thì xoá hẳn, phiếu đã ghi sổ thì chuyển sang trạng thái huỷ.\n\n' +
        'Phiếu đã tạo lệnh sản xuất thì máy không cho huỷ, phải huỷ các lệnh đó trước.',
        'Huỷ phiếu', 1)) return;
      busy(1);
      try {
        var r = await api('vagabond.ke_hoach_sx.huy_phieu', { ten: ten });
        toast(r.ghi_chu, 7000);
        if (r.ok) { ds = await api('vagabond.ke_hoach_sx.ds_phieu', { so_ngay: 30 }); draw(); }
      } catch (err) { toast(errMsg(err), 7000); } finally { busy(0); }
    };
  }
  draw();
}

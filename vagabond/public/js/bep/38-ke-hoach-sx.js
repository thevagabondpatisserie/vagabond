
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

var khsx = { ngay: '', d: null, tab: 'tp', bep: '', muc: '', tim: '', mo: {}, chon: {}, sua: {}, kho: {} };

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
   can bao nhieu, dau ngay co gi, gio con gi, vay con phai lam bao nhieu.

   O "Can" va o "Ton gio" GO DUOC (anh Viet 30/08/2026). O "Ton dau" thi
   khong: con so do la chuyen da xay ra luc 0h, doc tu so kho ra. Sua no
   nghia la chen mot but toan lui ngay vao ngay da chot so, lam lech gia
   von cua ngay do. Ai can sua that thi di duong kiem ke tren Desk. */
function khsxCot(x, loai) {
  /* Nhac lai cho nguoi doc ham nay: o Ton dau KHONG go duoc, va do la co
     y. Sua no la chen mot but toan lui ngay vao ngay da chot so. */
  var suaDuoc = khsxQuanLy() && loai !== 'nvl';
  var can = khsx.sua[x.khoa] != null ? khsx.sua[x.khoa] : x.can;
  var oCan = suaDuoc
    ? '<input class="tin khsx-o" data-can="' + h(x.khoa) + '" inputmode="decimal" value="' +
      h(khsxSo(can)) + '">'
    : kl(x.can, x.dvt);
  var oTon = (suaDuoc && x.kho_dich)
    ? '<input class="tin khsx-o" data-ton="' + h(x.khoa) + '" inputmode="decimal" value="' +
      h(khsxSo(x.ton_nay)) + '">'
    : kl(x.ton_nay, x.dvt);
  var o = '<div class="stk" style="margin:8px 0 0">' +
    '<div><div class="s1">Cần</div><div class="s2">' + oCan + '</div></div>' +
    '<div><div class="s1">Tồn đầu</div><div class="s2">' + kl(x.ton_dau, x.dvt) + '</div></div>' +
    '<div><div class="s1">Tồn giờ</div><div class="s2">' + oTon + '</div></div>';
  if (loai === 'nvl') o += '<div><div class="s1">Kho tổng</div><div class="s2">' + kl(x.ton_goc, x.dvt) + '</div></div>';
  o += '<div><div class="s1">Phải làm</div><div class="s2" style="color:' +
    (x.con_lam > 0 ? '#b3261e' : '#0f766e') + '">' + kl(x.con_lam, x.dvt) + '</div></div></div>';
  return o;
}

/* So de dat vao o go: bo duoi thap phan vun cho de doc, nhung KHONG lam
   tron so nho hon 1 thanh 0. */
function khsxSo(v) {
  var n = Number(v) || 0;
  if (n === 0) return '0';
  return Math.abs(n) >= 1 ? String(Math.round(n * 100) / 100) : String(Math.round(n * 1000) / 1000);
}

/* Danh sach nguyen lieu cua mot mon, xo ra ngay tren the. */
function khsxBangNvl(ds, tieu_de) {
  if (!ds || !ds.length) return '<div class="l2" style="padding:8px 0">Món này chưa có công thức nên chưa xổ ra được nguyên liệu.</div>';
  return '<div class="l2" style="margin:10px 0 4px;font-weight:700">' + h(tieu_de) + '</div>' +
    ds.map(function (n) {
      return '<div style="display:flex;gap:9px;align-items:center;padding:7px 0;border-bottom:1px solid #f1f3f7">' +
        anhMon(n.anh) +
        '<div style="flex:1;min-width:0">' +
        '<div style="font-size:13.5px;font-weight:600">' + h(n.ten) + '</div>' +
        /* Mon khong quan ton (nuoc may, dien) khong co phieu nhap nen ton
           doc ra luon bang khong. In "ton bep 0 g" cho nhung mon do la noi
           mot con so vo nghia, con to hon la lam bep tuong minh thieu. */
        (n.quan_ton === 0
          ? '<div class="l2">không quản tồn</div></div>'
          : '<div class="l2">tồn bếp ' + kl(n.ton_nay, n.dvt) +
            (n.ton_goc ? ' · kho tổng ' + kl(n.ton_goc, n.dvt) : '') + '</div></div>') +
        '<div style="text-align:right;flex:none">' +
        '<div class="amt"' + (n.con_lam > 0 ? ' style="color:#b3261e"' : '') + '>' + kl(n.can, n.dvt) + '</div>' +
        (n.con_lam > 0 ? '<div class="l2" style="color:#b3261e">thiếu ' + kl(n.con_lam, n.dvt) + '</div>' : '') +
        '</div></div>';
    }).join('');
}

function khsxThe(x, loai) {
  /* MOT NHIP, KHONG QUA TO GIAY. Khai de nghi 30/08/2026 cat bot thao tac.
     Bam vao the la xo ra: danh sach nguyen lieu de duyet, o go so, va mot
     nut ra lenh. Truoc day phai bam nut, doi to giay hien len, go so, chon
     kho, bam xac nhan - nam nhip cho mot me banh. */
  var mo = !!khsx.mo[x.khoa];
  var raLenh = khsxQuanLy() && loai !== 'nvl';
  var tick = raLenh && x.con_lam > 0
    ? '<input type="checkbox" class="tik" data-tick="' + h(x.khoa) +
      '" data-tloai="' + h(loai) + '"' + (khsx.chon[x.khoa] ? ' checked' : '') +
      ' aria-label="Chọn ' + h(x.ten) + '">'
    : '';
  var phu = h(x.ma) + (x.dvt ? ' · ' + h(x.dvt) : '') +
    (loai !== 'nvl' ? ' · nhập ' + (x.kho_dich ? h(shortWh(x.kho_dich)) :
      '<b style="color:#b3261e">chưa có kho</b>') : '') +
    (x.kho_giao ? ' · giao ' + h(shortWh(x.kho_giao)) : '') +
    (x.chip_chang ? ' · ' + h(x.chip_chang) : '') +
    (x.bep ? ' · ' + h(x.bep === 'baker' ? 'Baker' : 'Pastry') : '') +
    (x.da_lenh > 0 ? ' · đã ra lệnh ' + kl(x.da_lenh, x.dvt) : '') +
    (x.so_nguon > 1 ? ' · gom ' + x.so_nguon + ' phiếu' : '');

  var xo = '';
  if (loai !== 'nvl') {
    xo = '<div data-xo="' + h(x.khoa) + '" style="margin-top:8px;font-size:12.5px;color:#0b6bcb;font-weight:600">' +
      (mo ? '▾ Thu gọn' : '▸ Xem nguyên liệu và ra lệnh') + '</div>';
  }
  if (mo && loai !== 'nvl') {
    xo += '<div style="margin-top:4px;border-left:2px solid #e3e6ee;padding-left:10px">' +
      khsxBangNvl(x.nvl, 'Nguyên liệu cho ' + khsxSo(x.can) + ' ' + (x.dvt || '')) +
      ((x.nguon || []).length > 1
        ? '<div class="l2" style="margin:10px 0 4px;font-weight:700">Gom từ ' + x.nguon.length + ' phiếu yêu cầu</div>' +
          x.nguon.map(function (n) {
            return '<div class="l2" style="padding:3px 0">' + h(n.ycsx) + ' · ' +
              h(shortWh(n.kho || '')) + ' · <b>' + kl(n.sl, x.dvt) + '</b></div>';
          }).join('')
        : '') +
      (x.kho_dich
        ? '<div class="l2" style="margin-top:10px">Nhập vào <b>' + h(shortWh(x.kho_dich)) +
          '</b> · <span data-doikho="' + h(x.khoa) + '" style="color:#0b6bcb;font-weight:600">đổi kho</span></div>'
        : '<div class="l2" style="margin-top:10px;color:#b3261e">Chưa có kho nhập · ' +
          '<span data-doikho="' + h(x.khoa) + '" style="color:#0b6bcb;font-weight:600">chọn kho</span></div>') +
      (khsxQuanLy()
        ? '<button class="btn gr" data-lenh="' + h(x.khoa) + '" data-loai="' + h(loai) +
          '" style="margin:10px 0 4px">✅ Hoàn thành, tạo lệnh sản xuất</button>'
        : '') +
      '</div>';
  }

  /* Hang tren cung dung dung lop .li cua he thong thiet ke, von da
     display:flex, align-items:center, gap:12px, padding:14px. Ban v351
     boc them mot lop flex tay roi dat align-items:flex-start, thanh ra
     tick va anh khong thang hang voi ten mon. Nay tra lai cho .li lam
     dung viec cua no, phan xo ra day xuong mot khoi rieng ben duoi. */
  return '<div class="khsx-the">' +
    '<div class="li"' + (loai !== 'nvl' ? ' data-xo="' + h(x.khoa) + '"' : '') + '>' +
    tick + anhMon(x.anh) +
    '<div class="lt"><div class="l1">' + h(x.ten) + '</div><div class="l2">' + phu + '</div></div>' +
    '<div class="st ' + h(x.mau) + '" style="flex:0 0 auto">' + h(x.ten_muc) + '</div></div>' +
    '<div class="khsx-than">' + khsxCot(x, loai) + xo + '</div></div>';
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

    /* O "Can": go den dau nho den do, KHONG ve lai man giua chung keo
       mat con tro. Chi ghi vao khsx.sua, luc ra lenh moi dung toi. */
    Array.prototype.forEach.call(b.querySelectorAll('[data-can]'), function (o) {
      o.onclick = function (ev) { ev.stopPropagation(); };
      o.oninput = function () {
        var v = parseFloat(String(o.value).replace(/[^0-9.]/g, ''));
        khsx.sua[o.dataset.can] = isNaN(v) ? null : v;
      };
    });
    /* O "Ton gio": go xong roi ROI KHOI O thi may hoi lai va ghi so bang
       mot phieu kiem ke that. Ghi ngay luc dang go thi moi phim la mot
       phieu. */
    Array.prototype.forEach.call(b.querySelectorAll('[data-ton]'), function (o) {
      o.onclick = function (ev) { ev.stopPropagation(); };
      o.dataset.cu = o.value;
      o.onblur = function () { khsxLuuTon(o.dataset.ton, o, ve); };
    });

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

  /* Thu tu xet CO CHU Y: cac nut nam BEN TRONG hang the phai duoc xet
     TRUOC cai hang. Ca hang nay mang data-xo de bam vao dau cung xo ra
     duoc nguyen lieu (anh Viet 30/08/2026), nen neu xet hang truoc thi
     bam vao o tick hay chu "doi kho" cung chi xo ra chu khong lam dung
     viec cua no. */
  function khsxGan(b, ve) {
    b.onclick = async function (e) {
      var tk = e.target.closest('[data-tick]');
      if (tk) {
        var kk = tk.dataset.tick;
        khsx.chon[kk] = khsx.chon[kk] ? 0 : { khoa: kk, loai: tk.dataset.tloai };
        return ve();
      }
      var dk = e.target.closest('[data-doikho]');
      if (dk) return khsxDoiKho(dk.dataset.doikho, ve);
      var lenh = e.target.closest('[data-lenh]');
      if (lenh) return khsxTaoLenh(lenh.dataset.lenh, lenh.dataset.loai);
      var t = e.target.closest('[data-tab]');
      if (t) { khsx.tab = t.dataset.tab; return ve(); }
      var bp = e.target.closest('[data-bep]');
      if (bp) { khsx.bep = bp.dataset.bep; return ve(); }
      var mc = e.target.closest('[data-muc]');
      if (mc) { khsx.muc = mc.dataset.muc; return ve(); }
      var dsp = e.target.closest('[data-dsp]');
      if (dsp) return go(scrKhsxDsPhieu);
      var lui = e.target.closest('[data-lui]');
      if (lui) return khsxDoiNgay(-1);
      var toi = e.target.closest('[data-toi]');
      if (toi) return khsxDoiNgay(1);
      var xo = e.target.closest('[data-xo]');
      if (xo) { var k = xo.dataset.xo; khsx.mo[k] = !khsx.mo[k]; return ve(); }
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
  khsx.sua = {};
  khsx.kho = {};
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

/* Doi kho nhap cua mot mon. To chon kho chi hien khi bep BAM VAO chu
   truoc do may da doan san, nen duong thuong khong ai phai cham toi no. */
function khsxDoiKho(khoa, ve) {
  var cac = (khsx.d && khsx.d.cac_kho) || [];
  if (!cac.length) return toast('Chưa khai kho nào cho bếp');
  sheet('Kho nhập thành phẩm', cac.map(function (w) {
    return { label: shortWh(w), value: w };
  }), khsx.kho[khoa] || '', function (o) {
    khsx.kho[khoa] = o.value;
    var x = khsxDong(khoa);
    if (x) x.kho_dich = o.value;
    ve();
  }, true);
}

/* Go lai so ton = mot lenh kiem ke that.

   Anh Viet 30/08/2026: "cho bep do phai lam kiem ke ma van co the nhap
   vao luon roi san xuat luon cho gon". Nen o day may dung phieu Stock
   Reconciliation cua ERPNext roi ghi so ngay, chu KHONG sua lut so ton.
   Sua so ton ma khong di qua phieu la de lai mot khoan chenh khong ai
   giai thich duoc. Vi la but toan that nen phai HOI LAI truoc khi ghi. */
async function khsxLuuTon(khoa, o, ve) {
  var x = khsxDong(khoa);
  if (!x) return;
  var moi = parseFloat(String(o.value).replace(/[^0-9.]/g, ''));
  if (isNaN(moi) || Math.abs(moi - (x.ton_nay || 0)) < 0.0001) { o.value = o.dataset.cu; return; }
  if (!x.kho_dich) { o.value = o.dataset.cu; return toast('Chọn kho nhập trước đã', 4000); }
  if (!await confirmSheet('Đặt tồn ' + h(x.ten) + ' thành ' + khsxSo(moi) + ' ' + (x.dvt || '') + '?',
    'Máy ghi một phiếu kiểm kê thật tại kho ' + shortWh(x.kho_dich) + ', đúng như bếp đi đếm kho.\n\n' +
    'Số cũ là ' + kl(x.ton_nay, x.dvt) + '. Phiếu ghi sổ ngay lúc này, không lùi ngày.',
    'Ghi phiếu kiểm kê')) { o.value = o.dataset.cu; return; }
  busy(1);
  try {
    var r = await api('vagabond.ke_hoach_sx.dat_ton',
      { ma: x.ma, kho: x.kho_dich, so_luong: moi });
    toast(r.ghi_chu, 7000);
    if (r.ok) { khsx.d = null; await scrKeHoachSX(); return; }
    o.value = o.dataset.cu;
  } catch (e) { toast(errMsg(e), 7000); o.value = o.dataset.cu; } finally { busy(0); }
}

/* Ra lenh cho mot mon. MOT NHIP: so da go ngay tren the, kho da doan san,
   bam mot nut la xong. Khong con to giay hoi lai. */
async function khsxTaoLenh(khoa, loai) {
  var x = khsxDong(khoa);
  if (!x) return toast('Không thấy dòng này nữa, tải lại màn hình rồi thử lại');
  var sl = khsx.sua[khoa] != null ? khsx.sua[khoa] : x.con_lam;
  if (!(sl > 0)) return toast('Số lượng phải lớn hơn 0');
  var kho = khsx.kho[khoa] || x.kho_dich || '';
  if (!kho) return toast('Chọn kho nhập trước đã', 4000);
  busy(1);
  try {
    var r = await api('vagabond.ke_hoach_sx.tao_lenh',
      { ten: khsx.d.ten, khoa: khoa, loai: loai === 'tp' ? 'tp' : 'btp',
        so_luong: sl, kho: kho });
    toast(r.ghi_chu, 6000);
    delete khsx.chon[khoa];
    delete khsx.sua[khoa];
    khsx.mo[khoa] = 0;
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
    'Máy ra lệnh theo số đang hiện trên từng thẻ và nhập vào kho máy đoán.\n\n' +
    'Muốn sửa số hoặc đổi kho thì huỷ, gõ lại ngay trên thẻ rồi bấm lại.',
    'Tạo ' + ds.length + ' lệnh')) return;
  busy(1);
  var xong = [], loi = [];
  try {
    for (var i = 0; i < ds.length; i++) {
      try {
        var k0 = ds[i].khoa;
        var r = await api('vagabond.ke_hoach_sx.tao_lenh',
          { ten: khsx.d.ten, khoa: k0, loai: ds[i].loai === 'tp' ? 'tp' : 'btp',
            so_luong: khsx.sua[k0] != null ? khsx.sua[k0] : null,
            kho: khsx.kho[k0] || null });
        if (r.ok) { xong = xong.concat(r.lenh || []); delete khsx.chon[k0]; delete khsx.sua[k0]; }
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

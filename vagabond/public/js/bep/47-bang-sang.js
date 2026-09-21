/* ---------- 47. Viec hom nay (Bang sang) - issue #351, dot 1 ----------

Anh Viet 21/09/2026: "Ban than anh thuong bi stuck moi ngay khong biet nen
giao viec gi cho cac bo phan vi anh cung la SME, tu quan het tat ca cac bo
phan nen bi overload". Muon phan he Bao cao bien so kho thanh goi y kieu tro
ly cua Fabi.

Man nay la tang GIAO VIEC nam tren cac bao cao co san. May chu (phan_tich.py)
doc so ban ba tuan, lo sap het han va bang kiem banh ngay mai luc 7 gio sang,
nhap san mot danh sach nhan dinh. Nguoi quan ly chi viec doc, bam Giao viec
hoac Bo qua. Viec giao di la mot Task that cua ERPNext, nen tren Desk cung
thay dung viec do o danh sach Task va o Assigned To.

Thu tu khoi theo AGENTS.md muc 2b dieu 17: khoi de BAM (cac nhan dinh uu
tien) dung dau; khoi chi de DOC (luu y ve so lieu) thu ve mot dong dem so,
dat duoi cung, bam moi mo.

Moi con so tren man do may chu tinh (QT-19). Man nay khong cong tru gi. */

var bsLoc = { tab: 'can_giao', bp: '', moRong: '', xemLuuY: 0, dangTai: 0 };
var BS_MUC = { cao: ['r', 'Làm ngay'], vua: ['w', 'Trong tuần'], thap: ['b', 'Theo dõi'] };
var BS_TT = {
  tre: ['r', 'Trễ hạn'], mo: ['w', 'Chờ làm'], dang_lam: ['b', 'Đang làm'],
  xong: ['g', 'Xong'], bo_qua: ['n', 'Bỏ qua']
};
var BS_TAB = [['can_giao', 'Cần giao'], ['da_giao', 'Đã giao'], ['xong', 'Xong'], ['bo_qua', 'Bỏ qua']];
var BS_HAN = [[0, 'Hôm nay'], [1, 'Ngày mai'], [3, '3 ngày'], [7, '1 tuần']];
var BS_NGAY_BQ = [[1, '1 ngày'], [3, '3 ngày'], [7, '1 tuần'], [14, '2 tuần']];

function bsNgay(iso) { if (!iso) return ''; var p = String(iso).slice(0, 10).split('-'); return p[2] + '/' + p[1]; }
/* Han lo: khac nam hien tai thi ghi ca nam, "Han 21/01" cua nam 2024 ma
   doc thanh thang 1 nam nay la hieu sai hoan toan. */
function bsNgayLo(iso) {
  if (!iso) return '';
  var nam = String(iso).slice(0, 4);
  return bsNgay(iso) + (nam !== String(new Date().getFullYear()) ? '/' + nam : '');
}
function bsCongNgay(n) {
  var d = new Date(); d.setDate(d.getDate() + (Number(n) || 0));
  return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
}

/* O anh cua mot nhan dinh: mon thi anh mon, kho thi bieu tuong kho. */
function bsAnh(x) {
  var d = (x && x.doi) || {};
  if (d.loai === 'kho') return '<div class="imm immp" style="width:44px;height:44px;flex:0 0 44px;font-size:22px">📦</div>';
  return anhMon(d.anh || (x && x.anh) || '').replace('class="imm', 'style="width:44px;height:44px;flex:0 0 44px" class="imm');
}

/* Ba cot so ba tuan: nhin mot cai la thay len hay xuong. Cot cuoi to mau
   theo chieu, hai cot truoc mau nhat. */
function bsCot(x) {
  var sl = (x && x.so_lieu) || {};
  var c = sl.chuoi || [];
  if (c.length !== 3) return '';
  var max = Math.max(c[0], c[1], c[2], 1);
  var mau = x.luat === 'mon_giam' ? '#c93a3a' : '#0B7C93';
  var nhan = sl.nhan || [];
  return '<div style="display:flex;gap:10px;align-items:flex-end;padding:2px 14px 12px;height:84px">' +
    c.map(function (v, i) {
      var cao = Math.max(4, Math.round(v / max * 40));
      return '<div style="flex:1;text-align:center;min-width:0">' +
        '<div style="font-size:13px;font-weight:700;color:' + (i === 2 ? mau : '#4a5061') + '">' + money(v) + '</div>' +
        '<div style="height:' + cao + 'px;border-radius:6px;margin:3px auto 4px;max-width:56px;background:' + (i === 2 ? mau : '#dfe3ec') + '"></div>' +
        '<div style="font-size:11px;color:#8a8f9c;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + h(nhan[i] || '') + '</div></div>';
    }).join('') + '</div>';
}

/* Lo trong nhan dinh kho: toi da ba dong, con lai dem so (dieu 17). */
function bsLo(x) {
  var lo = ((x && x.so_lieu) || {}).lo || [];
  if (!lo.length) return '';
  var qua = x.luat === 'lo_qua_han';
  /* Codex #353: may chu chi gui 12 lo dau kem so_lo that; phan con lai phai
     dem theo so_lo, dem theo lo.length la bao thieu pham vi viec cua kho. */
  var tong = Math.max(Number(((x && x.so_lieu) || {}).so_lo) || 0, lo.length);
  return '<div style="padding:0 14px 10px">' + lo.slice(0, 3).map(function (l) {
    return '<div style="display:flex;gap:8px;padding:7px 0;border-top:1px solid #f0f2f6;font-size:13px">' +
      '<div style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + h(l.ten || l.ma) +
      '<div style="font-size:12px;color:#8a8f9c">' + h(l.lo || '') + '</div></div>' +
      '<div style="text-align:right;white-space:nowrap"><span class="st ' + (qua ? 'r' : 'w') + '">' + (qua ? 'Hạn ' : 'Hết ') + bsNgayLo(l.han) + '</span>' +
      '<div style="font-size:12px;color:#8a8f9c;margin-top:3px">còn ' + num(l.sl) + '</div></div></div>';
  }).join('') + (tong > 3 ? '<div style="font-size:12.5px;color:#8a8f9c;padding-top:6px">và ' + (tong - 3) + ' lô nữa</div>' : '') + '</div>';
}

function bsChipBp(ds, tenBp) {
  return (ds || []).map(function (k) {
    return '<span class="st n" style="margin-right:4px">' + h((tenBp && tenBp[k]) || k) + '</span>';
  }).join('');
}

/* The day du cua mot nhan dinh, co hai nut Giao viec va Bo qua. */
function bsThe(x, i, tenBp) {
  var m = BS_MUC[x.muc] || BS_MUC.vua;
  return '<div class="card" data-bsthe="' + i + '">' +
    '<div style="display:flex;gap:12px;padding:14px 14px 10px">' + bsAnh(x) +
    '<div style="flex:1;min-width:0">' +
    '<div style="margin-bottom:6px"><span class="st ' + m[0] + '" style="margin-right:4px">' + m[1] + '</span>' + bsChipBp(x.bo_phan, tenBp) + '</div>' +
    '<div style="font-size:15.5px;font-weight:600;line-height:1.3">' + h(x.tieu_de) + '</div>' +
    '<div style="font-size:13px;color:#4a5061;line-height:1.55;margin-top:4px">' + h(x.cau_ngan || x.cau) + '</div>' +
    '</div></div>' +
    bsCot(x) + bsLo(x) +
    '<div style="margin:0 14px;padding:10px 12px;background:#E4F9FD;border-radius:12px;font-size:13px;color:#05323C;line-height:1.55">' +
    '<b style="color:#0B7C93">Gợi ý:</b> ' + h(x.goi_y) + '</div>' +
    '<div style="display:flex;gap:8px;padding:12px 14px 14px">' +
    '<button class="btn gh" data-bsbq="' + i + '" style="flex:1;padding:12px 8px;font-size:15px;min-height:46px">Bỏ qua</button>' +
    '<button class="btn" data-bsg="' + i + '" style="flex:2;padding:12px 8px;font-size:15px;min-height:46px">Giao việc</button>' +
    '</div></div>';
}

/* Dong gon cho nhan dinh ngoai ba cai uu tien. Cham vao la mo the day du
   ngay tai cho, khong doi man. */
function bsDongGon(x, i) {
  var m = BS_MUC[x.muc] || BS_MUC.vua;
  return '<div class="li" data-bsmo="' + h(x.khoa) + '">' + bsAnh(x) +
    '<div class="lt"><div class="l1">' + h(x.tieu_de) + '</div>' +
    '<div class="l2" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + h(x.cau) + '</div></div>' +
    '<span class="st ' + m[0] + '">' + m[1] + '</span></div>';
}

/* Dong viec da giao, da xong hay da bo qua. */
function bsDongViec(d, i) {
  var t = BS_TT[d.tt] || BS_TT.mo;
  var phu;
  if (d.tt === 'xong') phu = 'Xong ' + bsNgay(d.xong_luc) + (d.nguoi.length ? ' · ' + d.nguoi.join(', ') : '') + (d.ket_qua ? ' · ' + d.ket_qua : '');
  else if (d.tt === 'bo_qua') phu = (d.ly_do || 'Bỏ qua') + ' · nhắc lại ' + bsNgay(d.nhac_lai);
  else phu = (d.nguoi.length ? d.nguoi.join(', ') : 'Chưa có người nhận') + (d.han ? ' · hạn ' + bsNgay(d.han) : '');
  return '<div class="li" data-bsv="' + i + '">' + bsAnh({ anh: d.anh, doi: { loai: d.luat.indexOf('lo_') === 0 ? 'kho' : 'mon', anh: d.anh } }) +
    '<div class="lt"><div class="l1">' + h(d.tieu_de) + '</div>' +
    '<div class="l2" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + h(phu) + '</div></div>' +
    '<span class="st ' + t[0] + '">' + t[1] + '</span></div>';
}

/* O so dau man: bam so la chuyen tab (dieu 6). */
function bsOSo(k, nhan, so, mauDo, khongTo) {
  var on = !khongTo && bsLoc.tab === k;
  return '<div data-bst="' + k + '" style="flex:1;min-width:0;text-align:center;padding:10px 4px;border-radius:12px;cursor:pointer;' +
    (on ? 'background:#E4F9FD;border:1.5px solid #7FE5F6' : 'background:#f6f8fc;border:1.5px solid transparent') + '">' +
    '<div style="font-size:21px;font-weight:800;color:' + (mauDo && so ? '#c93a3a' : '#05323C') + '">' + money(so) + '</div>' +
    '<div style="font-size:11.5px;color:#8a8f9c;margin-top:2px">' + h(nhan) + '</div></div>';
}

async function scrBangSang() {
  vgbCss();
  frame('Việc hôm nay', '<div class="emp"><div class="e1">⏳</div><div class="e2">Đang mở bảng việc hôm nay...</div></div>');
  var kq;
  try { kq = await api('vagabond.phan_tich.bang_sang', { tab: bsLoc.tab, bo_phan: bsLoc.bp }); }
  catch (e) {
    var b0 = frame('Việc hôm nay', '<div class="emp"><div class="e1">⚠️</div><div class="e2">' +
      h(errMsg(e) || 'Không mở được bảng việc hôm nay.') + '</div>' +
      '<button class="btn gh" id="bsThuLai" style="margin-top:16px">Tải lại</button></div>');
    var tl = b0.querySelector('#bsThuLai');
    if (tl) tl.onclick = function () { go(scrBangSang, true); };
    return;
  }
  bsLoc.tab = kq.tab;
  var ds = kq.ds || [];
  var tenBp = kq.ten_bo_phan || {};
  var dem = kq.dem || {};

  var html = '<div class="card" style="padding:12px 14px">' +
    '<div style="font-size:12.5px;color:#8a8f9c">' +
    (kq.dang_dung ? '⏳ Đang dựng bảng hôm nay từ số tới hết ' + bsNgay(kq.den_ngay) + '. Khoảng một phút nữa bấm Tải lại.'
      : 'Số tới hết ' + bsNgay(kq.den_ngay) + ' · chốt lúc ' + h(String(kq.chot_luc || '').slice(11, 16))) + '</div>' +
    '<div style="display:flex;gap:8px;margin-top:10px">' +
    bsOSo('can_giao', 'Cần giao', dem.can_giao || 0) +
    bsOSo('da_giao', 'Đã giao', dem.da_giao || 0) +
    bsOSo('da_giao', 'Trễ hạn', kq.so_tre || 0, true, true) +
    '</div>' +
    (kq.dang_dung ? '<button class="btn gh" id="bsTaiLai" style="margin-top:10px;padding:12px;font-size:15px">Tải lại</button>' : '') +
    '</div>';

  html += '<div class="chips" style="padding:2px 2px 8px">' + BS_TAB.map(function (t) {
    return '<div class="chip' + (bsLoc.tab === t[0] ? ' on' : '') + '" data-bst="' + t[0] + '">' + t[1] + ' <b>' + money(dem[t[0]] || 0) + '</b></div>';
  }).join('') + '</div>';
  if ((kq.chip_bo_phan || []).length > 1) {
    html += '<div class="chips" style="padding:0 2px 10px">' +
      '<div class="chip' + (!bsLoc.bp ? ' on' : '') + '" data-bsb="">Mọi bộ phận</div>' +
      kq.chip_bo_phan.map(function (c) {
        return '<div class="chip' + (bsLoc.bp === c.k ? ' on' : '') + '" data-bsb="' + h(c.k) + '">' + c.ic + ' ' + h(c.ten) + ' <b>' + money(c.so) + '</b></div>';
      }).join('') + '</div>';
  }

  if (bsLoc.tab === 'can_giao') {
    if (!ds.length) {
      html += '<div class="emp" style="padding:40px 20px"><div class="e1">🌤️</div><div class="e2">' +
        (kq.dang_dung ? 'Bảng hôm nay chưa dựng xong.' : 'Hôm nay chưa có việc nào cần giao' + (bsLoc.bp ? ' cho bộ phận này.' : '.')) + '</div>' +
        '<div style="font-size:13px;color:#8a8f9c;margin-top:8px;line-height:1.55">Máy xét món tăng, món giảm, lô sắp hết hạn và bánh có thể thiếu ngày mai. Không có gì vượt ngưỡng là tin tốt.</div></div>';
    } else {
      html += '<div class="sec">Ưu tiên</div>';
      ds.slice(0, 3).forEach(function (x, i) { html += bsThe(x, i, tenBp); });
      if (ds.length > 3) {
        /* Dong dang mo rong tach khoi danh sach gon thanh mot the rieng,
           nen gom cac dong gon lien nhau thanh tung khoi .lst. */
        html += '<div class="sec">Còn ' + (ds.length - 3) + ' nhận định</div>';
        var gon = [];
        var xa = function () { if (gon.length) html += '<div class="lst" style="margin-bottom:12px">' + gon.join('') + '</div>'; gon = []; };
        ds.slice(3).forEach(function (x, j) {
          var i = j + 3;
          if (bsLoc.moRong === x.khoa) { xa(); html += bsThe(x, i, tenBp); }
          else gon.push(bsDongGon(x, i));
        });
        xa();
      }
    }
  } else if (!ds.length) {
    var rong = { da_giao: 'Chưa có việc nào đang giao.', xong: 'Chưa có việc nào xong trong 14 ngày qua.', bo_qua: 'Không có nhận định nào đang bỏ qua.' };
    html += '<div class="emp" style="padding:40px 20px"><div class="e1">📋</div><div class="e2">' + rong[bsLoc.tab] + '</div></div>';
  } else {
    html += '<div class="lst" style="margin-bottom:12px">' + ds.map(bsDongViec).join('') + '</div>';
  }

  var ly = kq.chat_luong || [];
  if (ly.length) {
    html += '<div class="card" data-bsly style="padding:12px 14px;cursor:pointer">' +
      '<div style="display:flex;gap:8px;align-items:center;font-size:13.5px;color:#4a5061"><span>ⓘ</span>' +
      '<span style="flex:1"><b>' + ly.length + '</b> lưu ý về số liệu</span><span style="color:#c3c8d4">' + (bsLoc.xemLuuY ? '&#8964;' : '&#8250;') + '</span></div>' +
      (bsLoc.xemLuuY ? ly.map(function (c) {
        return '<div style="font-size:13px;color:#4a5061;line-height:1.55;padding-top:9px;margin-top:9px;border-top:1px solid #f0f2f6">' + h(c.cau) + '</div>';
      }).join('') : '') + '</div>';
  }

  var b = frame('Việc hôm nay', html, { action: '&#8635;', onAction: bsTinhLai });
  b.onclick = function (e) {
    var el;
    if ((el = e.target.closest('[data-bsg]'))) return bsGiao(ds[+el.getAttribute('data-bsg')]);
    if ((el = e.target.closest('[data-bsbq]'))) return bsBoQua(ds[+el.getAttribute('data-bsbq')]);
    if ((el = e.target.closest('[data-bsmo]'))) {
      var k = el.getAttribute('data-bsmo');
      bsLoc.moRong = bsLoc.moRong === k ? '' : k;
      return go(scrBangSang, true);
    }
    if ((el = e.target.closest('[data-bsv]'))) return bsMoViec(ds[+el.getAttribute('data-bsv')]);
    if ((el = e.target.closest('[data-bst]'))) {
      bsLoc.tab = el.getAttribute('data-bst'); bsLoc.moRong = '';
      return go(scrBangSang, true);
    }
    if ((el = e.target.closest('[data-bsb]'))) {
      bsLoc.bp = el.getAttribute('data-bsb'); bsLoc.moRong = '';
      return go(scrBangSang, true);
    }
    if (e.target.closest('[data-bsly]')) { bsLoc.xemLuuY = bsLoc.xemLuuY ? 0 : 1; return go(scrBangSang, true); }
    if (e.target.closest('#bsTaiLai')) return go(scrBangSang, true);
  };
}

async function bsTinhLai() {
  try {
    var r = await api('vagabond.phan_tich.tinh_lai', {});
    toast(r.cau || 'Đang tính lại');
  } catch (e) { toast(errMsg(e) || 'Không tính lại được'); }
}

/* Giao viec: chon nguoi bang chip (nguoi may goi y) hoac tim trong mot sheet
   (moi tai khoan dang bat), chon han bang chip. Khong o go tay (QT-31). */
async function bsGiao(x) {
  if (!x) return;
  var d;
  busy(true);
  try { d = await api('vagabond.phan_tich.nguoi_de_giao', { khoa: x.khoa }); }
  catch (e) { busy(false); return toast(errMsg(e) || 'Không mở được danh sách người nhận'); }
  busy(false);
  var ds = d.nguoi || [];
  var goiY = ds.filter(function (u) { return u.goi_y; });
  var chon = {};
  if (goiY.length && goiY.length <= 2) goiY.forEach(function (u) { chon[u.email] = 1; });
  var han = Number(d.han_goi_y || 0);
  var tenCua = {};
  ds.forEach(function (u) { tenCua[u.email] = u.ten; });

  var k = hopKhung('Giao việc', '<div id="bsgThan"></div>',
    '<button class="btn gh" data-bsgx style="flex:1;margin:0">Thôi</button>' +
    '<button class="btn" data-bsgok style="flex:2;margin:0">Giao việc</button>');
  function ve() {
    var than = k.box.querySelector('#bsgThan');
    var soChon = Object.keys(chon).length;
    var ngoai = Object.keys(chon).filter(function (e) { return !goiY.some(function (u) { return u.email === e; }); });
    than.innerHTML =
      '<div style="font-size:15px;font-weight:600;line-height:1.35;margin-bottom:12px">' + h(x.tieu_de) + '</div>' +
      '<div class="sec" style="margin-left:0">Người nhận</div>' +
      '<div class="chips" style="flex-wrap:wrap;overflow:visible;padding-bottom:6px">' +
      goiY.map(function (u) {
        return '<div class="chip' + (chon[u.email] ? ' on' : '') + '" data-bsgn="' + h(u.email) + '" title="' + h(u.email) + '">' + (chon[u.email] ? '✓ ' : '') + h(u.ten) + '</div>';
      }).join('') +
      ngoai.map(function (e) {
        return '<div class="chip on" data-bsgn="' + h(e) + '">✓ ' + h(tenCua[e] || e) + '</div>';
      }).join('') +
      '<div class="chip" data-bsgtim>🔎 Người khác</div></div>' +
      (goiY.length ? '' : '<div style="font-size:12.5px;color:#8a8f9c;margin-bottom:6px">Chưa có ai giữ vai của bộ phận này; bấm Người khác để tìm.</div>') +
      '<div class="sec" style="margin-left:0;margin-top:8px">Hạn</div>' +
      '<div class="chips" style="flex-wrap:wrap;overflow:visible;padding-bottom:6px">' +
      BS_HAN.map(function (o) {
        return '<div class="chip' + (han === o[0] ? ' on' : '') + '" data-bsgh="' + o[0] + '">' + o[1] + '</div>';
      }).join('') + '</div>' +
      '<textarea class="nt" id="bsgGhi" rows="2" placeholder="Dặn thêm (không bắt buộc)" style="margin-top:6px;box-sizing:border-box">' + h(k.ghi || '') + '</textarea>';
    var nut = k.box.querySelector('[data-bsgok]');
    nut.textContent = soChon ? 'Giao cho ' + soChon + ' người' : 'Chọn người nhận';
    nut.disabled = !soChon;
    nut.style.opacity = soChon ? '1' : '.55';
  }
  ve();
  k.box.onclick = async function (e) {
    var ghi = k.box.querySelector('#bsgGhi');
    if (ghi) k.ghi = ghi.value;
    var el;
    if (e.target.closest('.x') || e.target.closest('[data-bsgx]')) return k.dong();
    if ((el = e.target.closest('[data-bsgn]'))) {
      var em = el.getAttribute('data-bsgn');
      if (chon[em]) delete chon[em]; else chon[em] = 1;
      return ve();
    }
    if ((el = e.target.closest('[data-bsgh]'))) { han = +el.getAttribute('data-bsgh'); return ve(); }
    if (e.target.closest('[data-bsgtim]')) {
      return sheet('Chọn người nhận', ds.map(function (u) {
        return { value: u.email, label: u.ten, phu: (u.goi_y ? 'Máy gợi ý · ' : '') + u.email, img: u.anh || '', icon: '👤' };
      }), '', function (it) { chon[it.value] = 1; ve(); }, true);
    }
    if (e.target.closest('[data-bsgok]')) {
      var ng = Object.keys(chon);
      if (!ng.length) return;
      busy(true);
      try {
        var r = await api('vagabond.phan_tich.giao', { khoa: x.khoa, nguoi: JSON.stringify(ng), han: bsCongNgay(han), ghi_chu: k.ghi || '' });
        busy(false);
        k.dong();
        toast(r.da_co ? 'Việc này đã được giao trước đó.' : 'Đã giao cho ' + ng.map(function (m) { return tenCua[m] || m; }).join(', ') + ', hạn ' + bsNgay(r.han));
        go(scrBangSang, true);
      } catch (err) { busy(false); toast(errMsg(err) || 'Chưa giao được'); }
    }
  };
  k.ov.onclick = function (e) { if (e.target === k.ov) k.dong(); };
}

/* Bo qua: bat buoc chon ly do va so ngay nhac lai. Luat nao gioi han ngan
   (lo qua han chi toi da 3 ngay) thi chi hien lua chon trong gioi han. */
async function bsBoQua(x) {
  if (!x) return;
  var ly = '', ngay = 0;
  var toiDa = Number(x.bo_qua_toi_da || 7);
  var cacNgay = BS_NGAY_BQ.filter(function (o) { return o[0] <= toiDa; });
  var dsLy = [['dang_xu_ly', 'Đã biết, đang xử lý'], ['so_sai', 'Số liệu chưa đúng'], ['khong_can', 'Không cần làm lúc này'], ['khac', 'Lý do khác']];
  var k = hopKhung('Bỏ qua nhận định', '<div id="bsqThan"></div>',
    '<button class="btn gh" data-bsqx style="flex:1;margin:0">Thôi</button>' +
    '<button class="btn" data-bsqok style="flex:2;margin:0">Bỏ qua</button>');
  function ve() {
    k.box.querySelector('#bsqThan').innerHTML =
      '<div style="font-size:15px;font-weight:600;line-height:1.35;margin-bottom:12px">' + h(x.tieu_de) + '</div>' +
      '<div class="sec" style="margin-left:0">Vì sao bỏ qua</div>' +
      '<div class="chips" style="flex-wrap:wrap;overflow:visible;padding-bottom:6px">' + dsLy.map(function (o) {
        return '<div class="chip' + (ly === o[0] ? ' on' : '') + '" data-bsql="' + o[0] + '">' + o[1] + '</div>';
      }).join('') + '</div>' +
      '<div class="sec" style="margin-left:0;margin-top:8px">Nhắc lại sau</div>' +
      '<div class="chips" style="flex-wrap:wrap;overflow:visible;padding-bottom:6px">' + cacNgay.map(function (o) {
        return '<div class="chip' + (ngay === o[0] ? ' on' : '') + '" data-bsqn="' + o[0] + '">' + o[1] + '</div>';
      }).join('') + '</div>' +
      (x.luat === 'lo_qua_han' ? '<div style="font-size:12.5px;color:#c93a3a;margin-top:4px">Lô quá hạn chỉ bỏ qua được tối đa ' + toiDa + ' ngày.</div>' : '');
    var nut = k.box.querySelector('[data-bsqok]');
    var du = ly && ngay;
    nut.textContent = du ? 'Bỏ qua ' + (cacNgay.filter(function (o) { return o[0] === ngay; })[0] || [0, ''])[1] : 'Chọn lý do và ngày nhắc';
    nut.disabled = !du;
    nut.style.opacity = du ? '1' : '.55';
  }
  ve();
  k.box.onclick = async function (e) {
    var el;
    if (e.target.closest('.x') || e.target.closest('[data-bsqx]')) return k.dong();
    if ((el = e.target.closest('[data-bsql]'))) { ly = el.getAttribute('data-bsql'); return ve(); }
    if ((el = e.target.closest('[data-bsqn]'))) { ngay = +el.getAttribute('data-bsqn'); return ve(); }
    if (e.target.closest('[data-bsqok]')) {
      if (!ly || !ngay) return;
      busy(true);
      try {
        var r = await api('vagabond.phan_tich.bo_qua', { khoa: x.khoa, ly_do: ly, so_ngay: ngay });
        busy(false);
        k.dong();
        toast('Đã bỏ qua, ngày ' + bsNgay(r.nhac_lai) + ' máy nhắc lại nếu vẫn còn.');
        go(scrBangSang, true);
      } catch (err) { busy(false); toast(errMsg(err) || 'Chưa bỏ qua được'); }
    }
  };
  k.ov.onclick = function (e) { if (e.target === k.ov) k.dong(); };
}

/* Viec da bo qua: mo mot sheet nho de dua lai vao bang. Viec khac: mo man
   chi tiet. */
async function bsMoViec(d) {
  if (!d) return;
  if (d.tt !== 'bo_qua') return go(function () { return scrViecGoiY(d.name); });
  var ok = await confirmSheet('Đưa lại vào bảng?', d.tieu_de + '\n\nĐang bỏ qua vì: ' + (d.ly_do || 'không ghi') + '. Đưa lại thì nhận định hiện ngay trong tab Cần giao nếu số vẫn còn.', 'Đưa lại vào bảng');
  if (!ok) return;
  try {
    await api('vagabond.phan_tich.hien_lai', { name: d.name });
    toast('Đã đưa lại vào bảng.');
    go(scrBangSang, true);
  } catch (e) { toast(errMsg(e) || 'Chưa đưa lại được'); }
}

/* Man chi tiet mot viec: nguoi nhan mo tu Viec can lam, nguoi quan ly mo
   tu tab Da giao. Bao xong bat buoc ghi ket qua: may khong tu dong viec chi
   vi so da het vuot nguong. */
async function scrViecGoiY(name) {
  vgbCss();
  frame('Việc được giao', '<div class="emp"><div class="e1">⏳</div><div class="e2">Đang mở việc...</div></div>');
  var d;
  try { d = await api('vagabond.phan_tich.viec', { name: name }); }
  catch (e) {
    return frame('Việc được giao', '<div class="emp"><div class="e1">⚠️</div><div class="e2">' + h(errMsg(e) || 'Không mở được việc này.') + '</div></div>');
  }
  var t = BS_TT[d.tt] || BS_TT.mo;
  var html = '<div class="card">' +
    '<div style="display:flex;gap:12px;padding:14px 14px 10px">' + bsAnh({ anh: d.anh, doi: { loai: d.luat.indexOf('lo_') === 0 ? 'kho' : 'mon', anh: d.anh } }) +
    '<div style="flex:1;min-width:0"><div style="margin-bottom:6px"><span class="st ' + t[0] + '">' + t[1] + '</span></div>' +
    '<div style="font-size:16px;font-weight:600;line-height:1.3">' + h(d.tieu_de) + '</div>' +
    (d.cau ? '<div style="font-size:13px;color:#4a5061;line-height:1.55;margin-top:4px">' + h(d.cau) + '</div>' : '') +
    '</div></div>' +
    bsCot({ luat: d.luat, so_lieu: d.so_lieu }) + bsLo({ luat: d.luat, so_lieu: d.so_lieu }) +
    (d.goi_y ? '<div style="margin:0 14px 14px;padding:10px 12px;background:#E4F9FD;border-radius:12px;font-size:13px;color:#05323C;line-height:1.55"><b style="color:#0B7C93">Gợi ý:</b> ' + h(d.goi_y) + '</div>' : '') +
    '</div>';
  if (d.ghi_chu_giao) {
    html += '<div class="card" style="padding:12px 14px;font-size:13.5px;line-height:1.55"><b>Người giao dặn:</b> ' + h(d.ghi_chu_giao) + '</div>';
  }
  html += '<div class="card">' +
    '<div class="kv"><span>Người nhận</span><b>' + h((d.nguoi_nhan || []).join(', ') || 'Chưa có') + '</b></div>' +
    '<div class="kv"><span>Người giao</span><b>' + h(d.giao_boi || '') + '</b></div>' +
    '<div class="kv"><span>Giao lúc</span><b>' + h(bsNgay(d.giao_luc) + ' ' + String(d.giao_luc || '').slice(11, 16)) + '</b></div>' +
    '<div class="kv"><span>Hạn</span><b' + (d.tt === 'tre' ? ' style="color:#c93a3a"' : '') + '>' + h(bsNgay(d.han) || 'Không đặt') + '</b></div>' +
    (d.den_ngay ? '<div class="kv"><span>Số liệu tới hết</span><b>' + h(bsNgay(d.den_ngay)) + '</b></div>' : '') +
    (d.tt === 'xong' ? '<div class="kv"><span>Xong</span><b>' + h(bsNgay(d.xong_luc) + (d.xong_boi ? ' · ' + d.xong_boi : '')) + '</b></div>' +
      '<div style="padding:12px 14px;font-size:14px;line-height:1.55"><div style="font-size:12px;color:#8a8f9c;margin-bottom:3px">Kết quả</div>' + h(d.ket_qua || '') + '</div>' : '') +
    '</div>';
  var chan = '';
  if (d.sua_duoc) {
    chan = '<div style="display:flex;gap:8px">' +
      (d.tt !== 'dang_lam' ? '<button class="btn gh" id="bsvLam" style="flex:1">Đang làm</button>' : '') +
      '<button class="btn" id="bsvXong" style="flex:2">Báo đã xong</button></div>';
  }
  var b = frame('Việc được giao', html, chan ? { footer: chan } : {});
  var nl = document.getElementById('bsvLam');
  if (nl) nl.onclick = async function () {
    busy(true);
    try { await api('vagabond.phan_tich.cap_nhat_viec', { name: name, trang_thai: 'dang_lam' }); busy(false); toast('Đã báo đang làm.'); go(function () { return scrViecGoiY(name); }, true); }
    catch (e) { busy(false); toast(errMsg(e) || 'Chưa cập nhật được'); }
  };
  var nx = document.getElementById('bsvXong');
  if (nx) nx.onclick = async function () {
    var kq = await hoiChu('Báo đã xong', 'Ghi ngắn đã làm gì, kết quả ra sao. Người giao đọc dòng này sáng mai.', '', { nhieu_dong: true, bat_buoc: true, goi_y: 'Ví dụ: đã đăng story 2 lần, bếp làm thêm 10 cái' });
    if (!kq) return;
    busy(true);
    try { await api('vagabond.phan_tich.cap_nhat_viec', { name: name, trang_thai: 'xong', ket_qua: kq }); busy(false); toast('Đã báo xong. Cảm ơn bạn.'); go(function () { return scrViecGoiY(name); }, true); }
    catch (e) { busy(false); toast(errMsg(e) || 'Chưa báo được'); }
  };
  return b;
}

/* O "Viec hom nay" tren trang chu: dong phu noi so viec can giao va so viec
   tre. Chay SAU khi ve trang chu, hong thi giu nguyen dong chu cu. */
async function bsSoTrangChu() {
  if (!(S.quyenNen && S.quyenNen.bang_sang)) return;
  var el = document.querySelector('[data-go="BCSANG"]');
  if (!el) return;
  try {
    var r = await api('vagabond.phan_tich.dem_trang_chu', {});
    var h2 = el.querySelector('.h2');
    if (h2) h2.textContent = r.dang_dung ? 'Đang dựng bảng hôm nay...'
      : (r.can_giao ? r.can_giao + ' việc cần giao' : 'Không có việc mới cần giao') + (r.tre ? ' · ' + r.tre + ' việc trễ hạn' : '');
    if (r.can_giao && !el.querySelector('.bdg')) {
      var bd = document.createElement('span');
      bd.className = 'bdg';
      bd.textContent = String(r.can_giao);
      el.insertBefore(bd, el.querySelector('.fc'));
    }
  } catch (e) { }
}

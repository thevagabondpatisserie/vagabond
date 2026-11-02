/* ---------------- Bánh sỉ trên web: Đơn sỉ web, Khách sỉ web (v630)

   Anh Việt chốt 02/11/2026 (Phần 2 đề xuất, hướng sau góp ý Codex vòng 1):
   quán cà phê, khách sạn, nhà hàng đăng ký trên trang /banh-si, Sales gọi lại
   rồi duyệt ở đây; giá RIÊNG từng khách; khách đặt trên web thành phiếu đặt
   trong app; ngày giao là bước riêng (phiếu giao hàng + hoá đơn).

   Hai màn:
     - Đơn sỉ web (BSI): đơn theo ngày giao. Sales, cửa hàng, kho, kế toán
       giao hàng và xuất hoá đơn; bếp chỉ xem món và số lượng (máy chủ bỏ mọi
       số tiền khỏi gói trả về cho vai bếp).
     - Khách sỉ web (BSIKH): đăng ký chờ duyệt, khách đang đặt, giá riêng từng
       khách (gợi ý giá đã trả gần nhất từ hoá đơn và mã sỉ BAWS).

   Mọi con số (tổng, VAT, còn phải thu, trạng thái) do máy chủ tính
   (banh_si.tom_tat), màn chỉ hiện. Quyền chặn thật ở máy chủ; hai danh sách
   dưới chỉ để ẩn thẻ và phải trùng tuyệt đối máy chủ (ca thu_banh_si_630). */
var QUYEN_BSI_SALES = ['Sales User', 'Sales Manager', 'System Manager', 'Giám đốc'];
var QUYEN_BSI_XEM = ['Sales User', 'Sales Manager', 'System Manager', 'VGB - Quản lý cửa hàng',
  'Accounts User', 'Accounts Manager', 'Giám đốc', 'Stock User', 'Stock Manager',
  'Manufacturing User', 'Manufacturing Manager'];
function coQuyenBsiSales() { return QUYEN_BSI_SALES.some(function (v) { return hasRole(v); }); }
function coQuyenBsiXem() { return QUYEN_BSI_XEM.some(function (v) { return hasRole(v); }); }

var bsiTt = '';
var bsiTim = '';
/* Codex #531 vòng 3 (AGENTS 2b.3): hàng nhóm là khách, hàng ngày theo ngày
   giao. Mặc định "Mọi" để không giấu đơn nào khi mới mở màn. */
var bsiKhach = '';
var bsiNgay = '';
var bsiMo = '';
var BSI_MAU = {
  cho_tt: { ic: '⏳', nen: '#fef3c7', chu: '#92400e', mau: '#b45309' },
  cho_giao: { ic: '📦', nen: '#e0f2fe', chu: '#075985', mau: '#0369a1' },
  da_giao: { ic: '✅', nen: '#dcfce7', chu: '#166534', mau: '#15803d' },
  da_huy: { ic: '✕', nen: '#e5e7eb', chu: '#475467', mau: '#98a2b3' },
};
var BSI_THU = ['Chủ Nhật', 'Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy'];

function bsiDdMm(s) {
  var p = String(s || '').slice(0, 10).split('-');
  return p.length === 3 ? p[2] + '/' + p[1] : String(s || '');
}
function bsiNhanNgay(ngay, homNay) {
  var p = String(ngay || '').split('-'), q = String(homNay || '').split('-');
  var d = new Date(+p[0], (+p[1] || 1) - 1, +p[2] || 1), n = new Date(+q[0], (+q[1] || 1) - 1, +q[2] || 1);
  var lech = Math.round((d - n) / 86400000);
  var dau = lech === 0 ? 'Hôm nay · ' : lech === 1 ? 'Ngày mai · ' : lech < 0 ? 'Đã qua · ' : '';
  return (dau + BSI_THU[d.getDay()] + ' ' + bsiDdMm(ngay)).toUpperCase();
}
function bsiChip(r) {
  var m = BSI_MAU[r.trang_thai] || BSI_MAU.cho_giao;
  return '<span style="background:' + m.nen + ';color:' + m.chu + ';border-radius:999px;padding:2px 9px;font-size:12px;font-weight:700;white-space:nowrap">' +
    m.ic + ' ' + h(r.nhan) + '</span>';
}
/* AGENTS 2b.4: khách có logo (Customer.image, máy chủ chỉ trả ảnh /files/
   công khai) thì hiện logo qua anhMon; chưa có thì ô biểu tượng nhóm 🏢. */
function bsiLogo(url) {
  return url ? anhMon(url) : '<div class="imm immp">🏢</div>';
}
function bsiKhop(r, q) {
  return vgbKhop([r.ma, r.khach, r.ma_khach].concat((r.dong || []).map(function (d) { return d.ten; })), q);
}
function bsiThe(r, coTien) {
  var nhap = (r.phieu || []).filter(function (p) { return p.docstatus === 0; }).length;
  return '<div class="card" data-bsithe="' + h(r.name) + '" role="button" tabindex="0" style="padding:12px 13px;cursor:pointer;min-height:44px">' +
    '<div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px">' +
    '<span style="font-size:15.5px;font-weight:800;color:#0b2a33">' + h(r.ma) + '</span>' + bsiChip(r) + '</div>' +
    '<div style="display:flex;align-items:center;gap:10px;margin-top:4px">' + bsiLogo(r.logo) +
    '<div style="font-weight:700;font-size:15px;flex:1;min-width:0">' + h(r.khach) + '</div></div>' +
    '<div style="font-size:13px;color:#475467;margin-top:2px">' + (r.dong || []).length + ' món · ' + money(r.so_cai) + ' cái' +
    (coTien ? ' · ' + (r.tra_truoc ? 'Trả trước' : 'Trả cuối kỳ') : '') + '</div>' +
    (coTien ? '<div style="display:flex;justify-content:space-between;font-size:13.5px;margin-top:6px"><span>Tổng ' + money(r.tong) + 'đ</span>' +
      (r.trang_thai === 'cho_tt' ? '<b style="color:#b45309">Chờ ' + money(r.con_lai) + 'đ</b>' : '') + '</div>' : '') +
    (nhap ? '<div style="font-size:12.5px;color:#0369a1;margin-top:4px">' + nhap + ' phiếu chuyển khoản chờ kế toán ghi sổ</div>' : '') +
    '</div>';
}
function bsiTomTat(kq) {
  var rows = kq.rows || [], dem = kq.dem || {};
  var mo = rows.filter(function (r) { return r.trang_thai === 'cho_tt' || r.trang_thai === 'cho_giao'; });
  var cai = mo.reduce(function (a, r) { return a + (r.so_cai || 0); }, 0);
  var o = (kq.trang_thai || []).filter(function (t) { return t.k !== 'da_huy'; }).map(function (t) {
    var m = BSI_MAU[t.k] || BSI_MAU.cho_giao, chon = bsiTt === t.k;
    return '<button class="btn gh" data-bsiso="' + h(t.k) + '" style="margin:0;min-height:44px;padding:8px 10px;text-align:left;display:block;width:100%;border-radius:11px;' +
      (chon ? 'border:2px solid ' + m.mau + ';' : '') + '"><div style="font-size:12.5px;color:#475467">' + m.ic + ' ' + h(t.ten) + '</div>' +
      '<div style="font-size:17px;font-weight:800;color:' + ((dem[t.k] || 0) ? m.mau : '#98a2b3') + '">' + (dem[t.k] || 0) + ' đơn</div></button>';
  }).join('');
  return '<div class="card" data-bsitom="1" style="padding:12px 13px">' +
    '<div style="font-size:11.5px;color:#98a2b3;letter-spacing:.4px">ĐƠN SỈ WEB CHƯA GIAO</div>' +
    '<div style="font-size:21px;font-weight:800;margin:2px 0 8px">' + mo.length + ' đơn · ' + money(cai) + ' cái</div>' +
    '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:7px">' + o + '</div></div>';
}
function bsiVeDs(kq) {
  var tatCa = kq.rows || [];
  var ds = tatCa.filter(function (r) { return bsiTim ? bsiKhop(r, bsiTim) : (!bsiTt || r.trang_thai === bsiTt); });
  var html = '';
  if (bsiTim || bsiTt || bsiKhach || bsiNgay) {
    html += '<div data-bsiloc="1" style="display:flex;justify-content:space-between;gap:8px;margin:0 14px 4px;padding:8px 10px;border-radius:8px;background:#fffaeb;font-size:13px">' +
      '<span>Đang lọc' + (bsiTim ? ' "' + h(bsiTim) + '"' : '') + '</span><b>' + ds.length + ' đơn · ' +
      money(ds.reduce(function (a, r) { return a + (r.so_cai || 0); }, 0)) + ' cái</b></div>';
  }
  if (!ds.length) {
    return html + '<div class="card"><div class="emp" style="padding:24px"><div class="e1">🏢</div><div>' +
      (tatCa.length || kq.tong_goc ? 'Không có đơn nào khớp bộ lọc. Bấm Tất cả, Mọi khách hoặc Mọi ngày để xem hết.' :
        'Chưa có đơn sỉ trên web. Khách sỉ đã duyệt đặt ở trang Bánh sỉ, đơn hiện ở đây theo ngày giao.') + '</div></div></div>';
  }
  var ngayCu = '';
  ds.forEach(function (r) {
    if (r.ngay !== ngayCu) {
      ngayCu = r.ngay;
      html += '<div style="font-size:12.5px;font-weight:700;color:#475467;margin:14px 16px 2px;letter-spacing:.3px">' + h(bsiNhanNgay(r.ngay, kq.hom_nay)) + '</div>';
    }
    html += bsiThe(r, !!kq.co_tien);
  });
  return html;
}

async function scrDonSiWeb() {
  var tieuDe = 'Đơn sỉ web';
  if (!coQuyenBsiXem()) {
    frame(tieuDe, '<div class="emp"><div class="e1">🔒</div><div>Màn này mở cho Sales, cửa hàng, kho, bếp, kế toán và giám đốc.</div></div>');
    return;
  }
  frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc đơn sỉ...</div></div>');
  var kq;
  try { kq = await api('vagabond.banh_si.ds_don', {}); }
  catch (e) { frame(tieuDe, '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e)) + ' Kiểm tra mạng rồi mở lại màn.</div></div>'); return; }
  /* Lọc khách và ngày giao áp cả thẻ tóm tắt lẫn danh sách; mỗi hàng chip đếm
     theo các hàng còn lại để số trên chip khớp số thẻ hiện ra. */
  var goc = kq.rows || [], homNay = kq.hom_nay;
  var theoNgay = goc.filter(function (r) { return dsTrongKhoangToi(r.ngay, bsiNgay, homNay); });
  var theoKhach = goc.filter(function (r) { return !bsiKhach || r.khach === bsiKhach; });
  var loc = theoNgay.filter(function (r) { return !bsiKhach || r.khach === bsiKhach; });
  var kqLoc = Object.assign({}, kq, { rows: loc, dem: dsDemTheo(loc, function (r) { return r.trang_thai; }), tong_goc: goc.length });
  var cacKhach = [];
  goc.forEach(function (r) { if (r.khach && cacKhach.indexOf(r.khach) < 0) cacKhach.push(r.khach); });
  var cc = {
    ma: 'bsi',
    ho: [{ k: 'tt', chon: bsiTt, mau: '#0d9488', tatCa: 'Tất cả', dem: kqLoc.dem,
      ds: (kq.trang_thai || []).map(function (t) { return { k: t.k, ten: t.ten, ic: (BSI_MAU[t.k] || {}).ic }; }) },
      { k: 'khach', chon: bsiKhach, tatCa: 'Mọi khách', dem: dsDemTheo(theoNgay, function (r) { return r.khach; }),
        ds: cacKhach.sort().map(function (d) { return { k: d, ten: dsNhanGon(d), ic: '🏢' }; }) },
      { k: 'ngay', chon: bsiNgay, mau: '#b45309', tatCa: 'Mọi ngày', dem: dsDemKhoangToi(theoKhach, homNay), ds: dsKhoangToi() }],
    tim: { gt: bsiTim, goiY: '🔎 Tìm mã đơn, tên khách, tên món' },
  };
  var html = dsCongCu(cc) + bsiTomTat(kqLoc) + '<div id="bsiDs">' + bsiVeDs(kqLoc) + '</div>' +
    '<div style="font-size:12px;color:#98a2b3;margin:10px 16px 18px;line-height:1.5">Ngày giao sớm nhất là ngày đặt + 3. Khách trả cuối kỳ: giao được ngay, hoá đơn ghi công nợ hạn 15 ngày. Khách trả trước: tiền về và kế toán ghi sổ phiếu thu rồi mới giao.</div>';
  var than = frame(tieuDe, html);
  dsCongCuNoi(than, cc, function (ho, k) {
    if (ho === 'tt') { bsiTt = k || ''; bsiTim = ''; }
    else if (ho === 'khach') bsiKhach = k || '';
    else if (ho === 'ngay') bsiNgay = k || '';
    else if (ho === 'tim') bsiTim = k;
    go(scrDonSiWeb, true);
  });
  than.addEventListener('click', function (e) {
    var t = e.target.closest('[data-bsiso]');
    if (t) { var k = t.getAttribute('data-bsiso'); bsiTt = bsiTt === k ? '' : k; bsiTim = ''; go(scrDonSiWeb, true); return; }
    t = e.target.closest('[data-bsithe]');
    if (t) { bsiMo = t.getAttribute('data-bsithe'); go(scrDonSiWebCt); }
  });
  var o = document.getElementById('bsiDsTim');
  if (o) o.addEventListener('input', function () { bsiTim = o.value.trim(); var d = document.getElementById('bsiDs'); if (d) d.innerHTML = bsiVeDs(kqLoc); });
}

function bsiMoSheet(html) {
  var ov = document.createElement('div'); ov.className = 'sh';
  ov.innerHTML = '<div class="shb" style="padding:16px 16px calc(env(safe-area-inset-bottom,0px) + 18px)">' +
    '<div style="width:40px;height:4px;background:#d0d5dd;border-radius:2px;margin:0 auto 8px"></div>' + html + '</div>';
  document.body.appendChild(ov);
  ov.addEventListener('click', function (e) { if (e.target === ov) ov.remove(); });
  return ov;
}
async function bsiGoi(method, args, xong, man) {
  busy(true);
  try {
    var kq = await api(method, args);
    busy(false);
    toast(xong, 3600);
    if (man) go(man, true);
    return kq || true;
  } catch (e) {
    busy(false);
    toast(errMsg(e), 6000);
    return false;
  }
}
function bsiDocAnh(tep) {
  return new Promise(function (xong) {
    if (!tep) { xong(null); return; }
    var fr = new FileReader();
    fr.onload = function () { xong({ ten: tep.name, noi_dung: String(fr.result || '') }); };
    fr.onerror = function () { xong(null); };
    fr.readAsDataURL(tep);
  });
}
/* Kho nhớ theo máy, lần chọn gần nhất (AGENTS 2b.9). */
function bsiKhoNho() { try { return localStorage.getItem('vgb_bsi_kho') || ''; } catch (e) { return ''; } }
function bsiNhoKho(k) { try { localStorage.setItem('vgb_bsi_kho', k); } catch (e) { } }

function bsiSheetGiao(r) {
  var dsKho = r.kho || [], kho = bsiKhoNho();
  if (!dsKho.some(function (k) { return k.ma === kho; })) kho = '';
  var ov = bsiMoSheet('<div style="font-size:18px;font-weight:700;margin:2px 0 6px">Giao hàng và xuất hoá đơn</div>' +
    '<div style="font-size:14px;color:#475467;line-height:1.6">' + h(r.ma) + ' · ' + h(r.khach) + '<br>' + (r.dong || []).length + ' món · ' + money(r.so_cai) + ' cái · tổng ' + money(r.tong) + 'đ</div>' +
    '<div style="font-size:13.5px;font-weight:700;color:#344054;margin:12px 0 6px">Kho xuất hàng</div>' +
    '<button class="card" data-bsichonkho="1" style="display:flex;flex-direction:row;align-items:center;gap:10px;width:100%;margin:0;padding:10px 12px;min-height:48px;text-align:left;cursor:pointer">' +
    '<span style="font-size:20px">🏬</span><span style="flex:1"><b id="bsiKhoTen">' + h(kho ? (dsKho.filter(function (k) { return k.ma === kho; })[0] || {}).ten : 'Chọn kho') + '</b>' +
    '<div style="font-size:12px;color:#98a2b3">Phiếu giao trừ kho và ghi giá vốn ở kho này</div></span><span>›</span></button>' +
    '<div style="font-size:13.5px;font-weight:700;color:#344054;margin:12px 0 6px">Người nhận bên khách (không bắt buộc)</div>' +
    '<input class="nt" id="bsiNguoiNhan" maxlength="140" placeholder="Ví dụ: chị Lan, quản lý quầy" style="height:46px;padding:0 12px;width:100%;box-sizing:border-box">' +
    '<div style="font-size:12.5px;color:#475467;margin:10px 0 12px;line-height:1.5">' +
    (r.tra_truoc ? 'Hoá đơn ngày hôm nay, phương thức Trả trước, cấn đúng các phiếu thu đã ghi sổ của đơn.' :
      'Hoá đơn ngày hôm nay, phương thức Công nợ, hạn trả 15 ngày; khách thấy trên trang Bánh sỉ và màn Công nợ.') + '</div>' +
    '<button class="btn" data-bsigiaook="1" style="margin:0">Giao hàng và xuất hoá đơn</button>' +
    '<button class="btn gh" data-bsidong="1" style="margin-top:9px">Để sau</button>');
  ov.addEventListener('click', async function (e) {
    if (e.target.closest('[data-bsidong]')) { ov.remove(); return; }
    if (e.target.closest('[data-bsichonkho]')) {
      sheet('Chọn kho xuất', dsKho.map(function (k) { return { label: k.ten, value: k.ma, icon: '🏬' }; }), kho, function (it) {
        kho = it.value; bsiNhoKho(kho); ov.querySelector('#bsiKhoTen').textContent = it.label;
      }, dsKho.length > 8);
      return;
    }
    var t = e.target.closest('[data-bsigiaook]');
    if (t) {
      if (!kho) { toast('Chọn kho xuất hàng.', 3000); return; }
      t.disabled = true;
      var ok = await bsiGoi('vagabond.banh_si.giao_hang', { name: r.name, kho: kho, nguoi_nhan: ov.querySelector('#bsiNguoiNhan').value.trim() },
        'Đã giao ' + r.ma + ', lập phiếu giao hàng và hoá đơn', scrDonSiWebCt);
      if (ok) ov.remove(); else t.disabled = false;
    }
  });
}

function bsiSheetHuy(r) {
  var ov = bsiMoSheet('<div style="font-size:18px;font-weight:700;margin:2px 0 6px">Huỷ đơn ' + h(r.ma) + '</div>' +
    '<div style="font-size:13.5px;color:#475467;line-height:1.5">Chỉ huỷ được đơn chưa giao và chưa có tiền chuyển về. Đơn đã có tiền phải lập phiếu hoàn tiền.</div>' +
    '<div style="font-size:13.5px;font-weight:700;color:#344054;margin:12px 0 6px">Lý do (bắt buộc)</div>' +
    '<textarea class="nt" id="bsiLyDo" rows="2" maxlength="300" placeholder="Ví dụ: khách báo đổi ngày, đặt lại đơn khác"></textarea>' +
    '<button class="btn" data-bsihuyok="1" style="margin:12px 0 0;background:#fff;border:2px solid #d92d20;color:#d92d20">Huỷ đơn</button>' +
    '<button class="btn gh" data-bsidong="1" style="margin-top:9px">Không huỷ</button>');
  ov.addEventListener('click', async function (e) {
    if (e.target.closest('[data-bsidong]')) { ov.remove(); return; }
    var t = e.target.closest('[data-bsihuyok]');
    if (!t) return;
    var lyDo = ov.querySelector('#bsiLyDo').value.replace(/\s+/g, ' ').trim();
    if (lyDo.length < 5) { toast('Ghi lý do huỷ.', 3000); return; }
    t.disabled = true;
    var ok = await bsiGoi('vagabond.banh_si.huy_don', { name: r.name, ly_do: lyDo }, 'Đã huỷ đơn ' + r.ma, scrDonSiWebCt);
    if (ok) ov.remove(); else t.disabled = false;
  });
}

function bsiSheetQr(r) {
  var q = r.qr || {};
  var ov = bsiMoSheet('<div style="font-size:18px;font-weight:700;margin:2px 0 6px">Chờ khách chuyển khoản</div>' +
    '<div style="font-size:14px;color:#475467">' + h(r.ma) + ' · còn ' + money(r.con_lai) + 'đ</div>' +
    (q.anh ? '<div style="text-align:center;margin-top:8px"><img alt="Mã QR chuyển khoản" src="' + h(q.anh) + '" style="width:220px;height:220px;background:#fff"></div>' :
      '<div style="color:#b3261e;font-size:13.5px;margin-top:8px">Không vẽ được mã QR. Đọc số tài khoản bên dưới cho khách chuyển tay.</div>') +
    '<div style="font-size:13.5px;line-height:1.7;margin:8px 0">' + h(q.ngan_hang || '') + ' · ' + h(q.stk || '') + '<br>Nội dung: <b>' + h(q.noi_dung || r.ma) + '</b></div>' +
    '<button class="btn" data-bsikiem="1" style="margin:0">Khách đã chuyển, kiểm tiền về</button>' +
    '<div style="font-size:12.5px;color:#475467;margin-top:8px;line-height:1.5">Tiền về thì máy lập phiếu thu chờ kế toán đính giấy báo Có và ghi sổ. Ghi sổ xong mới giao được.</div>');
  ov.addEventListener('click', async function (e) {
    var t = e.target.closest('[data-bsikiem]');
    if (!t) return;
    t.disabled = true;
    busy(true);
    try {
      var kq = await api('vagabond.banh_si.kiem_tien_ve', { name: r.name });
      busy(false);
      if (kq && kq.lap) { toast('Đã thấy tiền về, máy lập phiếu thu chờ kế toán ghi sổ.', 4200); ov.remove(); go(scrDonSiWebCt, true); }
      else { toast('Chưa thấy tiền về. Chờ một hai phút rồi bấm lại.', 4200); t.disabled = false; }
    } catch (er) { busy(false); toast(errMsg(er), 6000); t.disabled = false; }
  });
}

/* Nút chính dính đáy theo trạng thái (2b.8). Bếp không có nút. */
function bsiNutChinh(r) {
  if (r.tong == null || r.trang_thai === 'da_giao' || r.trang_thai === 'da_huy') return '';
  if (r.trang_thai === 'cho_tt') return '<button class="btn" id="bsiChinh" data-bsiqr="1" style="margin:0">Chờ chuyển khoản ' + money(r.con_lai) + 'đ</button>';
  if (r.loi_giao) return '<button class="btn" id="bsiChinh" disabled data-bsicho="1" style="margin:0">Chờ kế toán ghi sổ phiếu chuyển khoản</button>';
  return '<button class="btn" id="bsiChinh" data-bsigiao="1" style="margin:0">Giao hàng và xuất hoá đơn</button>';
}

async function scrDonSiWebCt() {
  var tieuDe = 'Chi tiết đơn sỉ web';
  if (!coQuyenBsiXem() || !bsiMo) { go(scrDonSiWeb, true); return; }
  frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc đơn...</div></div>');
  var r;
  try { r = await api('vagabond.banh_si.xem_don', { name: bsiMo }); }
  catch (e) { frame(tieuDe, '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e)) + ' Bấm quay lại rồi mở lại đơn.</div></div>'); return; }
  var coTien = r.tong != null, keToan = !!r.la_ke_toan;
  var html = '<div class="card" data-bsict="' + h(r.name) + '" style="padding:12px 13px">' +
    '<div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px"><b style="font-size:18px">' + h(r.ma) + '</b>' + bsiChip(r) + '</div>' +
    '<div style="display:flex;align-items:center;gap:10px;margin-top:6px">' + bsiLogo(r.logo) +
    '<div style="font-size:15px;font-weight:700;flex:1;min-width:0">' + h(r.khach) + '</div></div>' +
    '<div style="font-size:13.5px;color:#475467;margin-top:2px">Giao ' + h(bsiNhanNgay(r.ngay, today())) + ' · đặt lúc ' + h(String(r.dat_luc || '').slice(11, 16)) + ' ' + h(bsiDdMm(r.dat_luc)) + '</div>' +
    (coTien ? '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-top:10px;font-size:12.5px;color:#475467">' +
      '<div>Tổng (gồm VAT)<br><b data-bsitong="1" style="font-size:15px;color:#101828">' + money(r.tong) + 'đ</b></div>' +
      '<div>Trong đó VAT<br><b style="font-size:15px;color:#101828">' + money(r.vat) + 'đ</b></div>' +
      '<div>' + (r.tra_truoc ? 'Còn phải thu' : 'Cách trả') + '<br><b data-bsiconlai="1" style="font-size:15px;color:' + (r.tra_truoc && r.con_lai > 0 ? '#b45309' : '#15803d') + '">' +
      (r.tra_truoc ? money(r.con_lai) + 'đ' : 'Cuối kỳ 15 ngày') + '</b></div></div>' : '') +
    (r.ghi_chu ? '<div style="font-size:13px;color:#344054;margin-top:8px;padding:8px 10px;background:#f8fafc;border-radius:8px">📝 ' + h(r.ghi_chu) + '</div>' : '') +
    '</div>';
  html += '<div class="card" style="padding:6px 13px"><div style="font-size:13.5px;font-weight:700;margin:6px 0 2px">' + (r.dong || []).length + ' món · ' + money(r.so_cai) + ' cái</div>' +
    (r.dong || []).map(function (d) {
      return '<div data-bsidong="' + h(d.ma) + '" style="display:flex;align-items:center;gap:10px;padding:8px 0;border-top:1px solid #eef0f3">' + anhMon(d.anh) +
        '<div style="flex:1;min-width:0"><div style="font-weight:700;font-size:14.5px">' + h(d.ten) + '</div><div style="font-size:12.5px;color:#98a2b3">' + h(d.ma) +
        (coTien ? ' · ' + money(d.gia) + 'đ' : '') + '</div></div><div style="text-align:right"><b style="font-size:16px">' + money(d.sl) + '</b>' +
        (coTien ? '<div style="font-size:12.5px;color:#475467">' + money(d.tien) + 'đ</div>' : '') + '</div></div>';
    }).join('') + '</div>';
  if (coTien && r.tra_truoc) {
    html += '<div class="card" style="padding:12px 13px"><div style="font-size:13.5px;font-weight:700;margin-bottom:4px">Phiếu thu của đơn</div>' +
      ((r.phieu || []).length ? (r.phieu || []).map(function (p, i) {
        var cho = p.docstatus === 0;
        return '<div data-bsipe="' + h(p.name) + '" style="display:flex;justify-content:space-between;align-items:center;gap:8px;padding:8px 0;border-top:1px solid #eef0f3;font-size:13.5px">' +
          '<span>Chuyển khoản · ' + h(bsiDdMm(p.ngay)) + '<br><span style="color:' + (cho ? '#0369a1' : '#15803d') + ';font-size:12.5px">' +
          (cho ? 'Chờ kế toán đính giấy báo Có và ghi sổ' : 'Đã ghi sổ') + ' · ' + h(p.name) + '</span></span>' +
          '<span style="text-align:right"><b>' + money(p.so_tien) + 'đ</b>' + (cho && keToan ? '<br><label class="btn gh" style="margin:4px 0 0;min-height:40px;padding:6px 10px;font-size:12.5px;display:inline-block">Đính và ghi sổ<input type="file" accept="image/*,application/pdf" data-bsighiso="' + i + '" style="display:none"></label>' : '') + '</span></div>';
      }).join('') : '<div style="font-size:13px;color:#475467">Chưa có đồng nào. Khách chuyển theo mã ' + h(r.ma) + ', máy tự nhận.</div>') + '</div>';
  }
  if (r.hoa_don) html += '<div class="card" style="padding:12px 13px;font-size:13.5px">Hoá đơn: <b>' + h(r.hoa_don) + '</b>' + (r.han_no ? ' · hạn trả ' + h(bsiDdMm(r.han_no)) : '') + '</div>';
  if (coTien && (r.trang_thai === 'cho_tt' || r.trang_thai === 'cho_giao') && !(r.phieu || []).length) {
    html += '<button class="btn gh" data-bsihuy="1" style="margin:4px 14px 18px;width:calc(100% - 28px);border:1.5px solid #f04438;color:#d92d20">Huỷ đơn chưa giao</button>';
  }
  if (!coTien) html += '<div style="font-size:12px;color:#98a2b3;margin:6px 16px 18px">Bếp xem món và số lượng để lên kế hoạch. Giao hàng do Sales, cửa hàng hoặc kho bấm.</div>';
  var than = frame(tieuDe, html, { footer: bsiNutChinh(r) });
  var chinh = document.getElementById('bsiChinh');
  if (chinh) chinh.onclick = function () {
    if (chinh.hasAttribute('data-bsigiao')) bsiSheetGiao(r);
    else if (chinh.hasAttribute('data-bsiqr')) bsiSheetQr(r);
  };
  than.addEventListener('click', function (e) {
    if (e.target.closest('[data-bsihuy]')) bsiSheetHuy(r);
  });
  than.querySelectorAll('[data-bsighiso]').forEach(function (inp) {
    inp.addEventListener('change', async function () {
      var p = r.phieu[+inp.getAttribute('data-bsighiso')];
      var anh = await bsiDocAnh(inp.files && inp.files[0]);
      if (!anh) { toast('Chưa đọc được tệp. Chọn lại ảnh hoặc PDF giấy báo Có.', 4000); return; }
      await bsiGoi('vagabond.banh_si.ghi_so_phieu', { name: r.name, phieu: p.name, anh: JSON.stringify([anh]) }, 'Đã ghi sổ phiếu ' + p.name, scrDonSiWebCt);
    });
  });
}

/* ---------------- Khách sỉ web: đăng ký, khách, giá riêng */

var bsiKhTab = 'dk';
var bsiDkTt = 'Chờ duyệt';
var bsiKhTim = '';
var bsiKhMo = '';

function bsiTheDk(r) {
  var m = r.trang_thai === 'Chờ duyệt' ? BSI_MAU.cho_tt : r.trang_thai === 'Đã duyệt' ? BSI_MAU.da_giao : BSI_MAU.da_huy;
  return '<div class="card" data-bsidk="' + h(r.name) + '" role="button" tabindex="0" style="padding:12px 13px;cursor:pointer;min-height:44px">' +
    '<div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px"><b style="font-size:15.5px">' + h(r.ten_quan) + '</b>' +
    '<span style="background:' + m.nen + ';color:' + m.chu + ';border-radius:999px;padding:2px 9px;font-size:12px;font-weight:700;white-space:nowrap">' + h(r.trang_thai) + '</span></div>' +
    '<div style="font-size:13px;color:#475467;margin-top:2px">' + h(r.loai_hinh) + ' · ' + h(r.luong_tuan) + '/tuần</div>' +
    '<div style="font-size:13px;margin-top:2px"><a href="tel:' + h(r.sdt) + '">' + h(r.sdt) + '</a>' + (r.mst ? ' · MST ' + h(r.mst) : '') + ' · ' + h(bsiDdMm(r.luc)) + '</div>' +
    (r.ten_khach ? '<div style="font-size:12.5px;color:#15803d;margin-top:3px">Đã gắn khách ' + h(r.ten_khach) + '</div>' : '') +
    (r.xu_ly ? '<div style="font-size:12.5px;color:#475467;margin-top:3px">' + h(r.xu_ly) + '</div>' : '') + '</div>';
}
function bsiTheKhach(r) {
  return '<div class="card" data-bsikh="' + h(r.name) + '" role="button" tabindex="0" style="padding:12px 13px;cursor:pointer;min-height:44px">' +
    '<div style="display:flex;align-items:center;gap:10px">' + bsiLogo(r.logo) +
    '<b style="font-size:15.5px;flex:1;min-width:0">' + h(r.customer_name || r.name) + '</b>' +
    (r.vgb_si_cuoi_ky ? '<span style="background:#e0f2fe;color:#075985;border-radius:999px;padding:2px 9px;font-size:12px;font-weight:700">Cuối kỳ 15 ngày</span>' :
      '<span style="background:#f2f4f7;color:#475467;border-radius:999px;padding:2px 9px;font-size:12px;font-weight:700">Trả trước</span>') + '</div>' +
    '<div style="font-size:13px;color:#475467;margin-top:2px">Zalo ' + h(r.vgb_si_sdt || 'chưa có') + (r.tax_id ? ' · MST ' + h(r.tax_id) : '') + '</div>' +
    '<div style="font-size:13px;margin-top:2px;color:' + (r.so_mon ? '#15803d' : '#b45309') + '">' + (r.so_mon ? r.so_mon + ' món có giá riêng' : 'Chưa khai giá riêng: khách chưa thấy món nào') + '</div></div>';
}
function bsiCongTac(k, nhan, giai, bat) {
  return '<button data-bsict="' + k + '" aria-pressed="' + (bat ? 'true' : 'false') + '" style="display:flex;align-items:center;gap:10px;width:100%;min-height:48px;padding:8px 0;background:none;border:none;text-align:left;cursor:pointer">' +
    '<span style="flex:1"><b style="font-size:14.5px">' + h(nhan) + '</b><div style="font-size:12.5px;color:#98a2b3">' + h(giai) + '</div></span>' +
    '<span style="width:46px;height:28px;border-radius:999px;background:' + (bat ? '#0d9488' : '#d0d5dd') + ';position:relative;flex:none"><i style="position:absolute;top:3px;left:' + (bat ? '21px' : '3px') + ';width:22px;height:22px;border-radius:50%;background:#fff"></i></span></button>';
}

function bsiSheetDuyet(r) {
  var cach = 'moi', khach = null, datWeb = true, cuoiKy = false;
  var ov = bsiMoSheet('<div style="font-size:18px;font-weight:700;margin:2px 0 4px">Duyệt ' + h(r.ten_quan) + '</div>' +
    '<div style="font-size:13px;color:#475467">' + h(r.loai_hinh) + ' · ' + h(r.sdt) + (r.mst ? ' · MST ' + h(r.mst) : '') + '</div>' +
    '<div style="font-size:13.5px;font-weight:700;color:#344054;margin:12px 0 6px">Hồ sơ khách</div><div id="bsiCach"></div><div id="bsiCachThan" style="margin-top:8px"></div>' +
    '<div id="bsiCt" style="margin-top:8px"></div>' +
    '<button class="btn" data-bsiduyetok="1" style="margin:12px 0 0">Duyệt và mở đặt sỉ</button>' +
    '<button class="btn gh" data-bsituchoi="1" style="margin-top:9px;border:1.5px solid #f04438;color:#d92d20">Từ chối</button>');
  function ve() {
    ov.querySelector('#bsiCach').innerHTML = kmHangChip([['moi', 'Tạo khách mới'], ['co', 'Gắn khách có sẵn']].map(function (c) {
      return posChipNut('data-bsicach="' + c[0] + '"', c[1], cach === c[0], false, '#0d9488');
    }).join(''));
    ov.querySelector('#bsiCachThan').innerHTML = cach === 'moi' ?
      '<input class="nt" id="bsiTenMoi" maxlength="140" value="' + h(r.ten_quan) + '" style="height:46px;padding:0 12px;width:100%;box-sizing:border-box">' +
      '<div style="font-size:12px;color:#98a2b3;margin-top:4px">Nhóm Khách sỉ B2B, mã khách máy tự đặt. MST lấy theo đăng ký.</div>' :
      '<button class="card" data-bsichonkh="1" style="display:flex;flex-direction:row;align-items:center;gap:10px;width:100%;margin:0;padding:10px 12px;min-height:48px;text-align:left;cursor:pointer">' + bsiLogo(khach && khach.logo) + '<span style="flex:1"><b>' +
      h(khach ? (khach.customer_name || khach.name) : 'Chọn khách') + '</b><div style="font-size:12px;color:#98a2b3">' + h(khach ? khach.name + (khach.tax_id ? ' · MST ' + khach.tax_id : '') : 'Tìm theo tên, mã, MST, số điện thoại') + '</div></span><span>›</span></button>';
    ov.querySelector('#bsiCt').innerHTML = bsiCongTac('web', 'Đặt sỉ trên web', 'Khách đăng nhập bằng số ' + r.sdt + ' qua mã Zalo', datWeb) +
      bsiCongTac('ky', 'Trả cuối kỳ 15 ngày', 'Bật: hoá đơn ghi công nợ hạn 15 ngày. Tắt: chuyển khoản trước khi giao', cuoiKy);
  }
  ve();
  ov.addEventListener('click', async function (e) {
    var t = e.target.closest('[data-bsicach]');
    if (t) { cach = t.getAttribute('data-bsicach'); ve(); return; }
    t = e.target.closest('[data-bsict]');
    if (t) { if (t.getAttribute('data-bsict') === 'web') datWeb = !datWeb; else cuoiKy = !cuoiKy; ve(); return; }
    if (e.target.closest('[data-bsichonkh]')) {
      bsiSheetTimKhach(function (x) { khach = x; ve(); });
      return;
    }
    if (e.target.closest('[data-bsituchoi]')) { ov.remove(); bsiSheetTuChoi(r); return; }
    t = e.target.closest('[data-bsiduyetok]');
    if (!t) return;
    var args = { name: r.name, dat_web: datWeb ? 1 : 0, cuoi_ky: cuoiKy ? 1 : 0 };
    if (cach === 'co') {
      if (!khach) { toast('Chọn khách có sẵn để gắn.', 3000); return; }
      args.khach = khach.name;
    } else {
      args.ten_khach = (ov.querySelector('#bsiTenMoi').value || '').trim();
      if (args.ten_khach.length < 2) { toast('Điền tên khách.', 3000); return; }
    }
    t.disabled = true;
    var ok = await bsiGoi('vagabond.banh_si.duyet', args, 'Đã duyệt ' + r.ten_quan + '. Khai giá riêng để khách thấy món.', null);
    if (ok) { ov.remove(); bsiKhMo = ok.khach; go(scrGiaSi); } else t.disabled = false;
  });
}
function bsiSheetTimKhach(onChon) {
  var ds = [], tre = null;
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>Gắn khách có sẵn</b><div class="x">&times;</div></div>' +
    '<div style="padding:10px 14px 4px"><input class="nt" id="bsiTkTim" placeholder="Gõ tên, mã khách, MST hoặc số điện thoại..." style="height:46px;padding:0 12px;width:100%;box-sizing:border-box"></div><div class="shl"></div>';
  var lst = box.querySelector('.shl');
  function ve() {
    lst.innerHTML = ds.length ? ds.map(function (x) {
      return '<div class="shi" data-bsikhchon="' + h(x.name) + '">' + bsiLogo(x.logo) + '<span style="flex:1;min-width:0">' + h(x.customer_name || x.name) +
        '<div style="color:#a0a6b4;font-size:12px;margin-top:2px">' + h(x.name) + (x.tax_id ? ' · MST ' + h(x.tax_id) : '') + (x.mobile_no ? ' · ' + h(x.mobile_no) : '') +
        (x.customer_group ? ' · ' + h(x.customer_group) : '') + '</div></span></div>';
    }).join('') : '<div class="emp"><div class="e2">Không tìm thấy khách. Chọn "Tạo khách mới".</div></div>';
  }
  async function tai(q) {
    try { ds = (await api('vagabond.banh_si.tim_khach', { tu_khoa: q || '' })) || []; } catch (e) { ds = []; }
    ve();
  }
  ov.appendChild(box); document.body.appendChild(ov);
  var inp = box.querySelector('#bsiTkTim');
  inp.oninput = function () { if (tre) clearTimeout(tre); tre = setTimeout(function () { tai(inp.value); }, 260); };
  function dong() { ov.remove(); }
  ov.onclick = function (e) { if (e.target === ov) dong(); };
  box.querySelector('.x').onclick = dong;
  lst.onclick = function (e) {
    var r = e.target.closest('[data-bsikhchon]'); if (!r) return;
    var x = ds.filter(function (y) { return y.name === r.getAttribute('data-bsikhchon'); })[0];
    dong(); if (x) onChon(x);
  };
  tai('');
  return ov;
}
function bsiSheetTuChoi(r) {
  var ov = bsiMoSheet('<div style="font-size:18px;font-weight:700;margin:2px 0 6px">Từ chối ' + h(r.ten_quan) + '</div>' +
    '<div style="font-size:13.5px;font-weight:700;color:#344054;margin:8px 0 6px">Lý do (bắt buộc)</div>' +
    '<textarea class="nt" id="bsiLyDoTc" rows="2" maxlength="300" placeholder="Ví dụ: ngoài khu vực giao, đã gọi báo khách"></textarea>' +
    '<button class="btn" data-bsitcok="1" style="margin:12px 0 0;background:#fff;border:2px solid #d92d20;color:#d92d20">Từ chối đăng ký</button>' +
    '<button class="btn gh" data-bsidong="1" style="margin-top:9px">Để sau</button>');
  ov.addEventListener('click', async function (e) {
    if (e.target.closest('[data-bsidong]')) { ov.remove(); return; }
    var t = e.target.closest('[data-bsitcok]');
    if (!t) return;
    var lyDo = ov.querySelector('#bsiLyDoTc').value.replace(/\s+/g, ' ').trim();
    if (lyDo.length < 5) { toast('Ghi lý do từ chối.', 3000); return; }
    t.disabled = true;
    var ok = await bsiGoi('vagabond.banh_si.tu_choi', { name: r.name, ly_do: lyDo }, 'Đã từ chối ' + r.ten_quan, scrKhachSiWeb);
    if (ok) ov.remove(); else t.disabled = false;
  });
}

async function scrKhachSiWeb() {
  var tieuDe = 'Khách sỉ web';
  if (!coQuyenBsiSales()) {
    frame(tieuDe, '<div class="emp"><div class="e1">🔒</div><div>Màn này mở cho Sales và giám đốc.</div></div>');
    return;
  }
  frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc...</div></div>');
  var dk, kh;
  try {
    dk = await api('vagabond.banh_si.ds_dang_ky', { trang_thai: bsiKhTab === 'dk' ? bsiDkTt : '' });
    kh = await api('vagabond.banh_si.ds_khach', { tim: bsiKhTab === 'kh' ? bsiKhTim : '' });
  } catch (e) { frame(tieuDe, '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e)) + ' Kiểm tra mạng rồi mở lại màn.</div></div>'); return; }
  var dem = dk.dem || {};
  /* Thanh công cụ chung (v534): hàng thẻ Đăng ký / Khách đang đặt, hàng trạng
     thái đăng ký có đếm, ô tìm khách ở thẻ Khách đang đặt. */
  var cc = { ma: 'bsikh', ho: [{ k: 'tab', chon: bsiKhTab, mau: '#0d9488', dem: { dk: dem['Chờ duyệt'] || 0, kh: (kh.rows || []).length },
    ds: [{ k: 'dk', ten: 'Đăng ký chờ duyệt', ic: '📝' }, { k: 'kh', ten: 'Khách đang đặt', ic: '🏢' }] }] };
  if (bsiKhTab === 'dk') cc.ho.push({ k: 'tt', chon: bsiDkTt, mau: '#4338ca', dem: dem, ds: (dk.trang_thai || []).map(function (t) { return { k: t, ten: t }; }) });
  else cc.tim = { gt: bsiKhTim, goiY: '🔎 Tìm tên khách, số Zalo, MST' };
  var html = dsCongCu(cc);
  if (bsiKhTab === 'dk') {
    var rows = dk.rows || [];
    html += rows.length ? rows.map(bsiTheDk).join('') : '<div class="card"><div class="emp" style="padding:24px"><div class="e1">📝</div><div>' +
      (bsiDkTt === 'Chờ duyệt' ? 'Chưa có quán nào chờ duyệt. Quán đăng ký ở trang Bánh sỉ, nhóm Zalo Bán hàng nhận tin.' : 'Không có đăng ký nào ở trạng thái này.') + '</div></div></div>';
  } else {
    var ks = kh.rows || [];
    html += ks.length ? ks.map(bsiTheKhach).join('') : '<div class="card"><div class="emp" style="padding:24px"><div class="e1">🏢</div><div>' +
      (bsiKhTim ? 'Không có khách nào khớp ô tìm.' : 'Chưa có khách nào mở đặt sỉ trên web. Duyệt một đăng ký ở thẻ Đăng ký.') + '</div></div></div>';
  }
  var than = frame(tieuDe, html);
  dsCongCuNoi(than, cc, function (ho, k) {
    if (ho === 'tab') bsiKhTab = k || 'dk';
    else if (ho === 'tt') bsiDkTt = k || 'Chờ duyệt';
    else if (ho === 'tim') bsiKhTim = k;
    go(scrKhachSiWeb, true);
  });
  than.addEventListener('click', function (e) {
    var t = e.target.closest('[data-bsidk]');
    if (t) {
      var r = (dk.rows || []).filter(function (x) { return x.name === t.getAttribute('data-bsidk'); })[0];
      if (r && r.trang_thai === 'Chờ duyệt') bsiSheetDuyet(r);
      else if (r && r.khach) { bsiKhMo = r.khach; go(scrGiaSi); }
      return;
    }
    t = e.target.closest('[data-bsikh]');
    if (t) { bsiKhMo = t.getAttribute('data-bsikh'); go(scrGiaSi); }
  });
}

function bsiSheetGia(khach, mon, giaGoiY, coSan) {
  var ov = bsiMoSheet('<div style="display:flex;gap:10px;align-items:center">' + anhMon(mon.anh) + '<div><div style="font-size:17px;font-weight:700">' + h(mon.ten || mon.ma) + '</div>' +
    '<div style="font-size:12.5px;color:#98a2b3">' + h(mon.ma) + (mon.dvt ? ' · ' + h(mon.dvt) : '') + '</div></div></div>' +
    '<div style="font-size:13.5px;font-weight:700;color:#344054;margin:12px 0 6px">Giá riêng cho khách này, đã gồm VAT</div>' +
    '<input class="nt" id="bsiGia" inputmode="numeric" value="' + h(giaGoiY ? String(giaGoiY) : '') + '" placeholder="Ví dụ 28000" style="height:50px;padding:0 12px;width:100%;box-sizing:border-box;font-size:20px;font-weight:700">' +
    (mon.goi_y ? '<div style="font-size:12.5px;color:#475467;margin-top:6px">Gợi ý: khách đã trả ' + money(mon.goi_y.gia) + 'đ ngày ' + h(bsiDdMm(mon.goi_y.ngay)) +
      (mon.goi_y.tu_ma ? ' (mã sỉ ' + h(mon.goi_y.tu_ma) + ')' : '') + ', hoá đơn ' + h(mon.goi_y.hoa_don) + '</div>' : '') +
    '<button class="btn" data-bsigiaok="1" style="margin:12px 0 0">Lưu giá</button>' +
    (coSan ? '<button class="btn gh" data-bsibo="1" style="margin-top:9px;border:1.5px solid #f04438;color:#d92d20">Thôi bán món này cho khách</button>' : '') +
    '<button class="btn gh" data-bsidong="1" style="margin-top:9px">Để sau</button>');
  ov.addEventListener('click', async function (e) {
    if (e.target.closest('[data-bsidong]')) { ov.remove(); return; }
    if (e.target.closest('[data-bsibo]')) {
      if (!(await confirmSheet('Thôi bán ' + (mon.ten || mon.ma) + '?', 'Khách sẽ không thấy món này trên trang Bánh sỉ từ hôm nay. Đơn đã đặt giữ nguyên giá.', 'Thôi bán', true))) return;
      var okb = await bsiGoi('vagabond.banh_si.bo_gia', { khach: khach, ma: mon.ma }, 'Đã thôi bán ' + (mon.ten || mon.ma), scrGiaSi);
      if (okb) ov.remove();
      return;
    }
    var t = e.target.closest('[data-bsigiaok]');
    if (!t) return;
    var g = String(ov.querySelector('#bsiGia').value || '').replace(/[^0-9]/g, '');
    if (!g || +g <= 0) { toast('Gõ giá là số tiền đồng.', 3000); return; }
    t.disabled = true;
    var ok = await bsiGoi('vagabond.banh_si.luu_gia', { khach: khach, ma: mon.ma, gia: g }, 'Đã lưu giá ' + money(+g) + 'đ cho ' + (mon.ten || mon.ma), scrGiaSi);
    if (ok) ov.remove(); else t.disabled = false;
  });
}
function bsiSheetThemMon(khach) {
  var ds = [], tre = null;
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>Thêm món có giá riêng</b><div class="x">&times;</div></div>' +
    '<div style="padding:10px 14px 4px"><input class="nt" id="bsiMonTim" placeholder="Gõ tên hoặc mã món..." style="height:46px;padding:0 12px;width:100%;box-sizing:border-box"></div><div class="shl"></div>';
  var lst = box.querySelector('.shl');
  function ve() {
    lst.innerHTML = ds.length ? ds.map(function (x) {
      return '<div class="shi" data-bsimon="' + h(x.name) + '">' + anhMon(x.image) + '<span style="flex:1;min-width:0">' + h(x.item_name || x.name) +
        '<div style="color:#a0a6b4;font-size:12px;margin-top:2px">' + h(x.name) + (x.item_group ? ' · ' + h(x.item_group) : '') + '</div></span></div>';
    }).join('') : '<div class="emp"><div class="e2">Không tìm thấy món đang bán nào.</div></div>';
  }
  async function tai(q) {
    try { ds = (await api('vagabond.banh_si.tim_mon', { tu_khoa: q || '' })) || []; } catch (e) { ds = []; }
    ve();
  }
  ov.appendChild(box); document.body.appendChild(ov);
  var inp = box.querySelector('#bsiMonTim');
  inp.oninput = function () { if (tre) clearTimeout(tre); tre = setTimeout(function () { tai(inp.value); }, 260); };
  function dong() { ov.remove(); }
  ov.onclick = function (e) { if (e.target === ov) dong(); };
  box.querySelector('.x').onclick = dong;
  lst.onclick = function (e) {
    var r = e.target.closest('[data-bsimon]'); if (!r) return;
    var x = ds.filter(function (y) { return y.name === r.getAttribute('data-bsimon'); })[0];
    dong();
    if (x) bsiSheetGia(khach, { ma: x.name, ten: x.item_name, anh: x.image, dvt: x.stock_uom }, '', false);
  };
  tai('');
}

async function scrGiaSi() {
  var tieuDe = 'Giá riêng khách sỉ';
  if (!coQuyenBsiSales() || !bsiKhMo) { go(scrKhachSiWeb, true); return; }
  frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc giá riêng...</div></div>');
  var kq;
  try { kq = await api('vagabond.banh_si.bang_gia', { khach: bsiKhMo }); }
  catch (e) { frame(tieuDe, '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e)) + ' Bấm quay lại rồi mở lại khách.</div></div>'); return; }
  var k = kq.khach || {}, gia = kq.gia || [], goiY = kq.goi_y || [];
  var html = '<div class="card" data-bsigiakh="' + h(k.name) + '" style="padding:12px 13px">' +
    '<div style="display:flex;align-items:center;gap:10px">' + bsiLogo(k.logo) +
    '<div style="font-size:17px;font-weight:800;flex:1;min-width:0">' + h(k.customer_name || k.name) + '</div></div>' +
    '<div style="font-size:12.5px;color:#98a2b3;margin-bottom:4px">' + h(k.name) + (k.tax_id ? ' · MST ' + h(k.tax_id) : '') + '</div>' +
    bsiCongTac('web', 'Đặt sỉ trên web', 'Khách đăng nhập trang Bánh sỉ bằng mã Zalo', !!k.vgb_si_web) +
    bsiCongTac('ky', 'Trả cuối kỳ 15 ngày', 'Bật: hoá đơn ghi công nợ hạn 15 ngày. Tắt: chuyển khoản trước khi giao', !!k.vgb_si_cuoi_ky) +
    '<button data-bsisdt="1" style="display:flex;align-items:center;gap:10px;width:100%;min-height:48px;padding:8px 0;background:none;border:none;text-align:left;cursor:pointer">' +
    '<span style="flex:1"><b style="font-size:14.5px">Số Zalo đăng nhập</b><div style="font-size:12.5px;color:#98a2b3">' + h(k.vgb_si_sdt || 'Chưa có, khách chưa đăng nhập được') + '</div></span><span>›</span></button></div>';
  html += '<div class="card" style="padding:6px 13px"><div style="font-size:13.5px;font-weight:700;margin:6px 0 2px">Giá riêng đang áp · ' + gia.length + ' món</div>' +
    (gia.length ? gia.map(function (g) {
      return '<div data-bsigiamon="' + h(g.ma) + '" role="button" style="display:flex;align-items:center;gap:10px;padding:8px 0;border-top:1px solid #eef0f3;min-height:44px;cursor:pointer">' + anhMon(g.anh) +
        '<div style="flex:1;min-width:0"><div style="font-weight:700;font-size:14.5px">' + h(g.ten) + '</div><div style="font-size:12.5px;color:#98a2b3">' + h(g.ma) + (g.dvt ? ' · ' + h(g.dvt) : '') + '</div></div>' +
        '<b style="font-size:15px">' + money(g.gia) + 'đ</b></div>';
    }).join('') : '<div style="font-size:13px;color:#b45309;padding:6px 0 10px">Chưa có món nào. Khách chỉ thấy món đã khai giá riêng. Chọn từ gợi ý bên dưới hoặc thêm món.</div>') + '</div>';
  if (goiY.length) {
    html += '<div class="card" style="padding:6px 13px"><div style="font-size:13.5px;font-weight:700;margin:6px 0 2px">Gợi ý từ hoá đơn 180 ngày · ' + goiY.length + ' món</div>' +
      goiY.map(function (g) {
        return '<div data-bsigoiy="' + h(g.ma) + '" role="button" style="display:flex;align-items:center;gap:10px;padding:8px 0;border-top:1px solid #eef0f3;min-height:44px;cursor:pointer">' + anhMon(g.anh) +
          '<div style="flex:1;min-width:0"><div style="font-weight:700;font-size:14.5px">' + h(g.ten) + '</div><div style="font-size:12.5px;color:#98a2b3">Đã trả ' + h(bsiDdMm(g.ngay)) + (g.tu_ma ? ' · mã sỉ ' + h(g.tu_ma) : '') + '</div></div>' +
          '<span style="font-size:14px;color:#0369a1;font-weight:700">' + money(g.gia) + 'đ ›</span></div>';
      }).join('') + '</div>';
  }
  var than = frame(tieuDe, html, { footer: '<button class="btn" id="bsiThemMon" style="margin:0">+ Thêm món có giá riêng</button>' });
  document.getElementById('bsiThemMon').onclick = function () { bsiSheetThemMon(k.name); };
  than.addEventListener('click', async function (e) {
    var t = e.target.closest('[data-bsict]');
    if (t) {
      var la = t.getAttribute('data-bsict') === 'web';
      var moi = la ? !k.vgb_si_web : !k.vgb_si_cuoi_ky;
      if (!la && moi && !(await confirmSheet('Bật trả cuối kỳ 15 ngày?', 'Đơn của ' + (k.customer_name || k.name) + ' giao không cần chuyển khoản trước; hoá đơn ghi công nợ, hạn 15 ngày.', 'Bật công nợ'))) return;
      await bsiGoi('vagabond.banh_si.luu_khach', la ? { khach: k.name, dat_web: moi ? 1 : 0 } : { khach: k.name, cuoi_ky: moi ? 1 : 0 }, 'Đã lưu', scrGiaSi);
      return;
    }
    if (e.target.closest('[data-bsisdt]')) {
      var s = await promptSheet('Số Zalo đăng nhập của khách', 'Ví dụ 0909123456');
      if (s) await bsiGoi('vagabond.banh_si.luu_khach', { khach: k.name, sdt: s }, 'Đã đổi số Zalo đăng nhập', scrGiaSi);
      return;
    }
    t = e.target.closest('[data-bsigiamon]');
    if (t) { var g = gia.filter(function (x) { return x.ma === t.getAttribute('data-bsigiamon'); })[0]; if (g) bsiSheetGia(k.name, g, g.gia, true); return; }
    t = e.target.closest('[data-bsigoiy]');
    if (t) { var y = goiY.filter(function (x) { return x.ma === t.getAttribute('data-bsigoiy'); })[0]; if (y) bsiSheetGia(k.name, { ma: y.ma, ten: y.ten, anh: y.anh, dvt: y.dvt, goi_y: y }, y.gia, false); }
  });
}

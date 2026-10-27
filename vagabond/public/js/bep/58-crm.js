/* ---------------- Phân hệ Khách hàng (CRM) đợt 1, v614

   Anh Việt 26/10/2026: "giờ mình tới cái phần CRM vì rất quan trọng, chuẩn bị
   đến mùa giáng sinh, tết". Bản định hướng qua Codex rà năm điểm (PR #503),
   anh duyệt 8 màn mẫu ngày 27/10/2026. Tệp này dựng các màn:
     - Danh sách gọi của tôi (CRMGOI): Sales gọi, chép tin Zalo, ghi kết quả.
     - Nhóm khách (CRMNHOM): 6 nhóm máy chia mỗi đêm, bộ lọc đã lưu.
     - Sổ đồng ý nhận tin (CRMDY): ai đồng ý, ai từ chối, kênh nào, ở đâu.
     - Chiến dịch (CRMCD) và Hiệu quả chiến dịch (CRMHQ).
     - Khối CRM trong hồ sơ khách (18-doi-chieu-may-in.js gọi crmGanHoSo).
     - Tấm hỏi đồng ý ở quầy (13-khuyen-mai.js gọi crmTheHoi, crmSheetDongY).

   Luật nghiệp vụ chặn thật ở máy chủ (vagabond/crm.py). Màn hình chỉ HIỆN số,
   không tự tính số (QT-19). Danh sách quyền dưới đây chỉ để ẩn ô và phải trùng
   tuyệt đối danh sách máy chủ (ca kiểm thu_crm_614 chốt). */
var CRM_XEM = ['Sales User', 'Sales Manager', 'System Manager', 'VGB - Quản lý cửa hàng', 'Marketing'];
var CRM_LAP = ['Sales Manager', 'System Manager'];
function coQuyenCrm() { return CRM_XEM.some(function (v) { return hasRole(v); }); }
function crmCoLap() { return CRM_LAP.some(function (v) { return hasRole(v); }); }

/* Sáu nhóm, đúng chữ lưu ở máy chủ (crm.NHOM). */
var CRM_NHOM = ['Trung thành', 'Mới', 'Sắp rời đi', 'Đã ngủ', 'Chỉ mua dịp lễ', 'Chưa mua'];
var CRM_KENH = ['Zalo', 'Gọi điện', 'Email'];
var CRM_IC_KENH = { 'Zalo': '💬', 'Gọi điện': '📞', 'Email': '✉️' };
var CRM_TT_GOI = ['Chưa gọi', 'Hẹn gọi lại', 'Đã xong'];

function crmNgay(s) {
  var p = String(s || '').slice(0, 10).split('-');
  return p.length === 3 && p[0] ? p[2] + '/' + p[1] + '/' + p[0] : '';
}
function crmGioNgay(s) {
  var m = String(s || '').match(/(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})/);
  return m ? m[4] + ':' + m[5] + ' ' + m[3] + '/' + m[2] : '';
}
/* Nhãn màu cho trạng thái đồng ý: xanh đồng ý, đỏ từ chối, xám chưa hỏi. */
function crmTagDy(kenh, tt) {
  var mau = tt === 'Đồng ý' ? 'background:#d1fadf;color:#05603a' : tt === 'Từ chối' ? 'background:#fee4e2;color:#b42318' : 'background:#f2f4f7;color:#475467';
  var chu = tt === 'Đồng ý' ? kenh + ' ✓' : tt === 'Từ chối' ? kenh + ': từ chối' : kenh + ': chưa hỏi';
  return '<span data-crmdytag="' + h(kenh) + '" style="display:inline-block;font-size:12px;font-weight:600;border-radius:999px;padding:4px 10px;margin:0 6px 6px 0;' + mau + '">' + h(chu) + '</span>';
}
function crmTag(chu, kieu) {
  var st = { lam: 'background:#E4F9FD;color:#0B7C93', vang: 'background:#fef0c7;color:#93370d', xam: 'background:#f2f4f7;color:#475467', xanh: 'background:#d1fadf;color:#05603a', do: 'background:#fee4e2;color:#b42318' }[kieu || 'xam'];
  return '<span style="display:inline-block;font-size:12px;font-weight:600;border-radius:999px;padding:4px 10px;margin:0 6px 6px 0;' + st + '">' + h(chu) + '</span>';
}
function crmTrong(ic, chu) {
  return '<div class="card"><div class="emp" style="padding:24px"><div class="e1">' + ic + '</div><div>' + chu + '</div></div></div>';
}
function crmChan(chu) {
  return '<div style="font-size:12px;color:#667085;background:#fffaeb;border:1px dashed #fec84b;border-radius:10px;padding:8px 10px;margin:4px 0 12px;line-height:1.45">' + chu + '</div>';
}
function crmMoSheet(html) {
  var ov = document.createElement('div'); ov.className = 'sh';
  ov.innerHTML = '<div class="shb" style="padding:16px 16px calc(env(safe-area-inset-bottom,0px) + 18px)">' +
    '<div style="width:40px;height:4px;background:#d0d5dd;border-radius:2px;margin:0 auto 10px"></div>' + html + '</div>';
  document.body.appendChild(ov);
  ov.addEventListener('click', function (e) { if (e.target === ov) ov.remove(); });
  return ov;
}
/* Công tắc bật tắt (skill thiết kế: bật tắt dùng công tắc, không hộp tích). */
function crmCongTac(attr, bat) {
  return '<button type="button" role="switch" ' + attr + ' aria-checked="' + (bat ? 'true' : 'false') + '" style="flex:0 0 50px;width:50px;height:30px;' +
    'border-radius:15px;border:0;padding:0;position:relative;cursor:pointer;background:' + (bat ? '#12a150' : '#d0d5dd') + '">' +
    '<span style="position:absolute;top:3px;' + (bat ? 'right:3px' : 'left:3px') + ';width:24px;height:24px;border-radius:50%;background:#fff"></span></button>';
}
function crmDatCongTac(nut, bat) {
  nut.setAttribute('aria-checked', bat ? 'true' : 'false');
  nut.style.background = bat ? '#12a150' : '#d0d5dd';
  var c = nut.querySelector('span');
  c.style.left = bat ? '' : '3px';
  c.style.right = bat ? '3px' : '';
}

/* ================================================================ đồng ý */

/* Tấm hỏi khách nhận tin. noiGhi: 'Quầy' hoặc 'Hồ sơ khách'. Xong thì gọi
   xong(kq) với kết quả máy chủ, khách bỏ qua thì không gọi gì: khách vẫn là
   "chưa hỏi", lần sau quầy được hỏi lại. */
function crmSheetDongY(khach, tenKhach, dangCo, noiGhi, xong) {
  dangCo = dangCo || {};
  var bat = {};
  CRM_KENH.forEach(function (k) { bat[k] = dangCo[k] === 'Đồng ý'; });
  var cau = dangCo.cau_hoi || '';
  var html = '<div style="font-size:18px;font-weight:700;margin-bottom:4px">Hỏi khách nhận tin ưu đãi</div>' +
    '<div style="font-size:13px;color:#8a8f9c;line-height:1.45;margin-bottom:12px">Bật kênh khách đồng ý. Kênh để tắt là khách chưa đồng ý: máy không gọi, không nhắn quảng cáo qua kênh đó.</div>' +
    (cau ? '<div style="background:#f3fcfe;border:1px solid #c6f1f9;border-radius:14px;padding:12px 14px;margin-bottom:10px">' +
      '<div style="font-size:12px;color:#0B7C93;font-weight:600;margin-bottom:4px">CÂU ĐỌC CHO KHÁCH</div>' +
      '<div data-crmcau="1" style="font-size:15px;line-height:1.45">"' + h(cau) + '"</div></div>' : '') +
    '<div style="font-size:12px;color:#0B7C93;font-weight:600;margin:6px 0 2px">' + h(tenKhach || khach) + '</div>';
  CRM_KENH.forEach(function (k) {
    html += '<div style="display:flex;align-items:center;justify-content:space-between;padding:12px 0;border-bottom:1px solid #f0f2f6;font-size:15.5px;min-height:44px">' +
      CRM_IC_KENH[k] + ' ' + (k === 'Gọi điện' ? 'Cho phép gọi điện' : 'Nhận tin qua ' + k) +
      (dangCo[k] === 'Từ chối' ? ' <span style="font-size:12px;color:#b42318;margin-left:6px">đang từ chối</span>' : '') +
      '<span style="flex:1"></span>' + crmCongTac('data-crmsw="' + h(k) + '"', bat[k]) + '</div>';
  });
  html += '<div style="display:flex;gap:10px;margin-top:14px">' +
    '<button class="btn gh" data-crmtuchoi="1" style="margin:0;flex:1">Khách từ chối hết</button>' +
    '<button class="btn" data-crmluu="1" style="margin:0;flex:1">Lưu</button></div>' +
    '<div style="font-size:12.5px;color:#8a8f9c;text-align:center;margin-top:12px">Bấm ra ngoài để bỏ qua: khách vẫn là "chưa hỏi"</div>';
  var ov = crmMoSheet(html);
  ov.querySelectorAll('[data-crmsw]').forEach(function (n) {
    n.onclick = function () { var k = n.getAttribute('data-crmsw'); bat[k] = !bat[k]; crmDatCongTac(n, bat[k]); };
  });
  async function gui(dat) {
    busy(true);
    try {
      var kq = await api('vagabond.crm.ghi_dong_y', { khach: khach, dat: JSON.stringify(dat), noi_ghi: noiGhi || 'Quầy' });
      busy(false);
      ov.remove();
      toast(kq && kq.doi ? 'Đã ghi ' + kq.doi + ' kênh vào sổ đồng ý' : 'Không có gì đổi');
      if (xong) xong(kq);
    } catch (e) { busy(false); toast(errMsg(e), 5000); }
  }
  ov.querySelector('[data-crmluu]').onclick = function () {
    var dat = {};
    CRM_KENH.forEach(function (k) {
      if (bat[k]) dat[k] = 'Đồng ý';
      /* Tắt một kênh đang đồng ý là khách rút lại: ghi Từ chối. Tắt kênh
         chưa hỏi thì để nguyên chưa hỏi, không tự nhận thay khách. */
      else if (dangCo[k] === 'Đồng ý') dat[k] = 'Từ chối';
    });
    gui(dat);
  };
  ov.querySelector('[data-crmtuchoi]').onclick = function () {
    gui({ 'Zalo': 'Từ chối', 'Gọi điện': 'Từ chối', 'Email': 'Từ chối' });
  };
  return ov;
}

/* Dải nhắc trong khối thẻ thành viên ở màn Tính tiền. Chỉ hiện khi khách chưa
   được hỏi cả gọi điện lẫn Zalo. Không chặn thu tiền: thu ngân hỏi lúc rảnh. */
function crmTheHoi(dy) {
  if (!dy || !dy.co || !dy.can_hoi) return '';
  return '<div data-crmhoi="1" style="display:flex;align-items:center;gap:10px;margin-top:10px;background:#fffaeb;border:1.5px solid #fde68a;border-radius:10px;padding:9px 11px">' +
    '<div style="flex:1;font-size:13px;color:#92400e;line-height:1.4"><b>Chưa hỏi khách nhận tin ưu đãi</b><br>Hỏi một lần, máy nhớ cho lần sau.</div>' +
    '<button type="button" data-crmhoimo="1" style="border:0;background:#0b7c93;color:#fff;border-radius:9px;padding:0 14px;min-height:44px;font-size:13.5px;font-weight:700">Hỏi khách</button></div>';
}

/* ================================================================ hồ sơ */

/* Gắn khối CRM vào hồ sơ khách (màn Chi tiết khách hàng). Gọi sau frame. */
async function crmGanHoSo(khach, tenKhach) {
  var o = document.getElementById('crmHs');
  if (!o || !coQuyenCrm()) return;
  o.innerHTML = '<div class="card" style="padding:12px 14px;color:#98a2b3">Đang đọc phần chăm sóc khách...</div>';
  var d;
  try { d = await api('vagabond.crm.ho_so_crm', { khach: khach }); }
  catch (e) { o.innerHTML = '<div class="card" style="padding:12px 14px;color:#b42318">' + h(errMsg(e)) + '</div>'; return; }
  o.innerHTML = crmVeHoSo(d);
  o.onclick = function (e) {
    if (e.target.closest('[data-crmhsdy]')) {
      var dy = Object.assign({ cau_hoi: '' }, d.dong_y);
      return crmSheetDongY(khach, tenKhach, dy, 'Hồ sơ khách', function () { crmGanHoSo(khach, tenKhach); });
    }
    if (e.target.closest('[data-crmhslh]')) return crmSheetLienHe(khach, function () { crmGanHoSo(khach, tenKhach); });
    if (e.target.closest('[data-crmhskqc]')) return crmDatKqc(khach, !d.khong_quang_cao, function () { crmGanHoSo(khach, tenKhach); });
  };
}

function crmVeHoSo(d) {
  var NHOM_MAU = { 'Trung thành': 'xanh', 'Mới': 'lam', 'Sắp rời đi': 'vang', 'Đã ngủ': 'xam', 'Chỉ mua dịp lễ': 'lam', 'Chưa mua': 'xam' };
  var html = '<div class="sec">Chăm sóc khách</div><div class="card" style="padding:12px 14px">' +
    '<div>' + crmTag(d.nhom, NHOM_MAU[d.nhom]) + (d.dip || []).map(function (x) { return crmTag('Hay mua dịp ' + x, 'xam'); }).join('') + '</div>' +
    '<div style="font-size:12.5px;color:#8a8f9c;margin:0 0 8px">' + h(d.giai_thich_nhom || '') +
    (d.nhip_ngay ? ' · nhịp mua khoảng ' + d.nhip_ngay + ' ngày' : '') + '</div>' +
    '<div>' + CRM_KENH.map(function (k) { return crmTagDy(k, d.dong_y[k]); }).join('') +
    (d.khong_quang_cao ? crmTag('Danh sách không quảng cáo', 'do') : '') + '</div>' +
    '<div style="display:flex;gap:8px;margin-top:6px">' +
    '<button class="btn gh" data-crmhsdy="1" style="margin:0;flex:1;padding:12px">✅ Đồng ý nhận tin</button>' +
    '<button class="btn gh" data-crmhslh="1" style="margin:0;flex:1;padding:12px">+ Ghi liên hệ</button></div>' +
    (d.duoc_dat_kqc ? '<button class="btn gh" data-crmhskqc="1" style="margin:8px 0 0;padding:10px;font-size:13.5px">' +
      (d.khong_quang_cao ? 'Bỏ khỏi Danh sách không quảng cáo' : 'Số này nằm trong Danh sách không quảng cáo') + '</button>' : '') +
    '</div>';
  /* Codex PR #505 vòng 3 (AGENTS: chỗ nào có tên món thì có ảnh món): mỗi món
     một dòng có ảnh, chưa có ảnh thì ô 🍰 của anhMon. */
  html += '<div class="sec">Món hay mua <span style="text-transform:none;font-weight:500">· từ 08/2026</span></div><div class="card">' +
    ((d.mon || []).length ? d.mon.map(function (m) {
      return '<div class="li" data-crmhsmon="' + h(m.item_code) + '" style="padding:10px 14px;cursor:default">' + anhMon(m.anh) +
        '<div class="lt"><div class="l1" style="font-size:14.5px">' + h(m.ten || m.item_code) + '</div>' +
        '<div class="l2">' + money(m.so_don) + ' đơn</div></div></div>';
    }).join('')
      : '<div style="color:#98a2b3;font-size:13px;padding:12px 14px">Chưa có hoá đơn nào trên ERP. Fabi không để lại từng món.</div>') +
    '<div style="font-size:12.5px;color:#8a8f9c;padding:10px 14px">Đơn chưa ghi sổ: ' + d.khac.chua_ghi_so + ' · Đơn huỷ: ' + d.khac.huy + ' · Hàng trả: ' + d.khac.tra + '</div></div>';
  html += '<div class="sec">Nhật ký liên hệ</div><div class="card">' +
    ((d.lien_he || []).length ? d.lien_he.map(function (r) {
      return '<div data-crmlh="' + h(r.name) + '" style="padding:12px 14px;border-bottom:1px solid #f0f2f6">' +
        '<div style="font-size:14.5px;font-weight:600">' + (CRM_IC_KENH[r.kenh] || '•') + ' ' + h(r.ket_qua || r.kenh) + '</div>' +
        (r.ghi_chu ? '<div style="font-size:13px;color:#475467;margin-top:2px">' + h(r.ghi_chu) + '</div>' : '') +
        '<div style="font-size:12px;color:#8a8f9c;margin-top:2px">' + h(r.ten_nguoi || '') + ' · ' + crmGioNgay(r.luc) +
        (r.ten_chien_dich ? ' · ' + h(r.ten_chien_dich) : '') + '</div></div>';
    }).join('') : '<div style="padding:14px;color:#98a2b3;font-size:13px">Chưa ai ghi liên hệ với khách này.</div>') + '</div>';
  return html;
}

function crmSheetLienHe(khach, xong) {
  var kenh = 'Gọi điện';
  var ov = crmMoSheet('<div style="font-size:18px;font-weight:700;margin-bottom:10px">Ghi liên hệ</div>' +
    kmHangChip(['Gọi điện', 'Zalo', 'Gặp tại quầy', 'Email'].map(function (k) {
      return posChipNut('data-crmlhk="' + h(k) + '"', (CRM_IC_KENH[k] || '🏪') + ' ' + h(k), k === kenh);
    }).join('')) +
    '<input class="tin" id="crmLhKq" placeholder="Kết quả, ví dụ: quan tâm, hẹn tuần sau" style="font-size:15px;font-weight:500;text-align:left;margin-top:12px;padding:0 12px">' +
    '<textarea class="nt" id="crmLhGhi" rows="3" maxlength="1000" placeholder="Ghi chú thêm (không bắt buộc)" style="margin-top:9px"></textarea>' +
    '<button class="btn" data-crmlhluu="1" style="margin-top:12px">Lưu</button>');
  ov.querySelectorAll('[data-crmlhk]').forEach(function (c) {
    c.onclick = function () {
      kenh = c.getAttribute('data-crmlhk');
      ov.querySelectorAll('[data-crmlhk]').forEach(function (x) {
        var on = x === c;
        x.style.background = on ? '#0d9488' : '#fff'; x.style.color = on ? '#fff' : '#374151'; x.style.borderColor = on ? '#0d9488' : '#d7dce5';
      });
    };
  });
  ov.querySelector('[data-crmlhluu]').onclick = async function () {
    var kq = ov.querySelector('#crmLhKq').value.trim(), ghi = ov.querySelector('#crmLhGhi').value.trim();
    if (!kq && !ghi) { toast('Ghi kết quả hoặc vài chữ ghi chú.', 3000); return; }
    busy(true);
    try {
      await api('vagabond.crm.ghi_lien_he', { khach: khach, kenh: kenh, ket_qua: kq, ghi_chu: ghi });
      busy(false); ov.remove(); toast('Đã ghi liên hệ'); if (xong) xong();
    } catch (e) { busy(false); toast(errMsg(e), 5000); }
  };
}

async function crmDatKqc(khach, bat, xong) {
  busy(true);
  try {
    await api('vagabond.crm.dat_khong_quang_cao', { khach: khach, bat: bat ? 1 : 0 });
    busy(false); toast(bat ? 'Đã đánh dấu: không gọi, không nhắn quảng cáo cho số này' : 'Đã bỏ đánh dấu'); if (xong) xong();
  } catch (e) { busy(false); toast(errMsg(e), 5000); }
}

/* Codex PR #505 vòng 3: màn Chi tiết khách hàng đọc hồ sơ bán hàng, chỉ mở
   cho Sales và kế toán (trùng ban_hang.QUYEN_BAN_VA_KE_TOAN). Marketing và
   quản lý cửa hàng chỉ có quyền CRM thì mở màn Chăm sóc khách, đọc ho_so_crm
   (cổng CRM_XEM), không mở rộng cổng bán hàng. */
var CRM_HO_SO_DAY_DU = ['System Manager', 'Sales User', 'Sales Manager', 'Accounts User', 'Accounts Manager'];
function crmMoHoSo(khach, ten) {
  if (!khach) return;
  if (typeof scrKhachChiTiet === 'function' && CRM_HO_SO_DAY_DU.some(function (v) { return hasRole(v); })) {
    khMa = khach; return go(scrKhachChiTiet);
  }
  return go(function () { return scrCrmHoSo(khach, ten); });
}
async function scrCrmHoSo(khach, ten) {
  frame('Chăm sóc khách', '<div class="card" style="padding:12px 14px"><div style="font-size:16px;font-weight:700">' + h(ten || khach) + '</div>' +
    '<div style="font-size:12.5px;color:#8a8f9c">Phần chăm sóc khách. Hoá đơn, công nợ của khách chỉ Sales và kế toán xem.</div></div><div id="crmHs"></div>');
  return crmGanHoSo(khach, ten);
}

/* ================================================================ danh sách gọi */

var crmGoiTt = 'Chưa gọi';
var crmGoiDs = [];

var crmGoiKq = [];

var crmGoiTim = '';
var crmGoiCd = '';

/* Lọc danh sách gọi trên máy: chiến dịch, trạng thái, chữ tìm (tên hoặc số).
   THUẦN, để ca kiểm gọi thẳng. Trả các dòng còn lại theo đúng thứ tự máy chủ. */
function crmGoiLoc(ds, tt, cd, tim) {
  var so = String(tim || '').replace(/[^0-9]/g, '');
  var chiSo = so.length >= 3 && so.length === String(tim || '').replace(/[\s.+-]/g, '').length;
  return (ds || []).filter(function (r) {
    if (cd && r.chien_dich !== cd) return false;
    if (tim) {
      if (chiSo) return String(r.sdt || '').replace(/[^0-9]/g, '').indexOf(so) >= 0;
      return vgbKhop([r.ten_khach, r.khach], tim);
    }
    return !tt || r.trang_thai === tt;
  });
}

/* daCo === true: vẽ lại từ dữ liệu đang có (đổi chip, tìm, vừa ghi kết quả),
   không hỏi lại máy chủ. Mở từ ô hay F5 thì đọc lại. */
async function scrCrmGoi(daCo) {
  var tieuDe = 'Danh sách gọi của tôi';
  if (!coQuyenCrm()) return frame(tieuDe, crmTrong('🔒', 'Phân hệ Khách hàng chỉ mở cho Sales, quản lý cửa hàng và Marketing.'));
  if (daCo !== true) {
    frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc danh sách gọi...</div></div>');
    var d;
    try { d = await api('vagabond.crm.ds_goi_cua_toi', {}); }
    catch (e) { return frame(tieuDe, crmTrong('⚠️', h(errMsg(e)))); }
    crmGoiDs = d.dong || [];
    crmGoiKq = d.ket_qua || [];
  }
  var ketQua = crmGoiKq, ds = crmGoiDs;
  if (!ds.length) {
    return frame(tieuDe, crmTrong('📞', 'Chưa có khách nào được chia cho bạn. Khi quản lý chốt một chiến dịch, khách của bạn hiện ở đây.'));
  }
  var cd = {}, dsCd = [];
  ds.forEach(function (r) {
    var c = cd[r.chien_dich];
    if (!c) { c = cd[r.chien_dich] = { ten: r.ten_chien_dich, tong: 0, xong: 0, kich_ban: r.kich_ban }; dsCd.push(r.chien_dich); }
    c.tong++; if (r.trang_thai !== 'Chưa gọi') c.xong++;
  });
  var html = '';
  dsCd.forEach(function (k) {
    var c = cd[k];
    if (crmGoiCd && crmGoiCd !== k) return;
    html += '<div class="card" data-crmcd="' + h(k) + '" style="padding:12px 14px"><div style="display:flex;justify-content:space-between;gap:8px;font-size:14.5px">' +
      '<span>' + h(c.ten) + '</span><b>Đã gọi ' + c.xong + ' / ' + c.tong + '</b></div>' +
      '<div style="height:8px;background:#f0f2f6;border-radius:4px;overflow:hidden;margin-top:6px"><i style="display:block;height:100%;background:#50DBF2;width:' +
      Math.round(c.xong * 100 / c.tong) + '%"></i></div>' +
      (c.kich_ban ? '<button class="btn gh" data-crmkb="' + h(k) + '" style="margin:10px 0 0;padding:10px;font-size:14px">📜 Xem kịch bản gọi</button>' : '') + '</div>';
  });
  /* Thanh công cụ chung (AGENTS 2b.3, 2b.5): chip trạng thái có đếm, chip
     chiến dịch khi có hơn một chiến dịch, ô tìm tên hoặc số điện thoại. */
  var dem = {}, demCd = {};
  ds.filter(function (r) { return !crmGoiCd || r.chien_dich === crmGoiCd; }).forEach(function (r) {
    dem[r.trang_thai] = (dem[r.trang_thai] || 0) + 1; dem.tat_ca = (dem.tat_ca || 0) + 1;
  });
  ds.forEach(function (r) { demCd[r.chien_dich] = (demCd[r.chien_dich] || 0) + 1; demCd.tat_ca = (demCd.tat_ca || 0) + 1; });
  var cc = {
    ma: 'crmGoi',
    chang: { ds: CRM_TT_GOI.map(function (t) { return { k: t, ten: t }; }), dem: dem, chon: crmGoiTt, tatCa: 'Tất cả' },
    ho: dsCd.length > 1 ? [{ k: 'cd', tatCa: 'Mọi chiến dịch', chon: crmGoiCd, dem: demCd,
      ds: dsCd.map(function (k) { return { k: k, ten: cd[k].ten }; }) }] : [],
    tim: { gt: crmGoiTim, goiY: '🔎 Tìm tên khách, số điện thoại' }
  };
  html += dsCongCu(cc);
  var loc = crmGoiLoc(ds, crmGoiTt, crmGoiCd, crmGoiTim);
  if (crmGoiTim) html += '<div data-crmgoiloc="1" style="font-size:13px;color:#101828;background:#fffaeb;border-radius:8px;padding:8px 10px;margin:0 0 10px">Đang tìm "' + h(crmGoiTim) + '": <b>' + loc.length + ' khách</b></div>';
  if (!loc.length) html += crmTrong('✅', crmGoiTim ? 'Không có khách nào khớp chữ tìm.' : crmGoiTt === 'Chưa gọi' ? 'Bạn đã gọi hết khách được chia. Xem lại nhóm Hẹn gọi lại.' : 'Không có khách nào ở nhóm này.');
  else html += '<div class="card">' + loc.map(function (r) { return crmGoiDong(r); }).join('') + '</div>';
  html += crmChan('"Không muốn nhận tin nữa" ghi ngay vào Sổ đồng ý: khách bị loại khỏi mọi chiến dịch sau.');
  var b = frame(tieuDe, html);
  dsCongCuNoi(b, cc, function (ho, v) {
    if (ho === 'chang') crmGoiTt = v;
    else if (ho === 'cd') crmGoiCd = v;
    else if (ho === 'tim') crmGoiTim = v;
    scrCrmGoi(true);
  });
  b.onclick = function (e) {
    var kb = e.target.closest('[data-crmkb]');
    if (kb) return crmSheetKichBan(cd[kb.getAttribute('data-crmkb')]);
    var ch = e.target.closest('[data-crmchep]');
    if (ch) return crmChep(crmGoiDs[+ch.getAttribute('data-crmchep')]);
    var kq = e.target.closest('[data-crmkq]');
    if (kq) return crmSheetKetQua(crmGoiDs[+kq.getAttribute('data-crmkq')], ketQua, function () { scrCrmGoi(true); });
    var ten = e.target.closest('[data-crmmohs]');
    if (ten) { var rr = crmGoiDs.filter(function (x) { return x.khach === ten.getAttribute('data-crmmohs'); })[0] || {};
      return crmMoHoSo(ten.getAttribute('data-crmmohs'), rr.ten_khach); }
  };
}

function crmGoiDong(r) {
  var i = crmGoiDs.indexOf(r);
  var kenh = String(r.kenh_duoc || '');
  var tel = String(r.sdt || '').replace(/[^0-9+]/g, '');
  var coGoi = kenh.indexOf('Gọi điện') >= 0 && tel;
  var coZalo = kenh.indexOf('Zalo') >= 0 && r.tin_zalo;
  var nut = 'flex:1;text-align:center;border-radius:10px;padding:10px 4px;font-size:14px;font-weight:600;min-height:44px;display:flex;align-items:center;justify-content:center;text-decoration:none;border:0;';
  return '<div data-crmdong="' + h(r.name) + '" style="padding:13px 14px;border-bottom:1px solid #f0f2f6">' +
    '<div data-crmmohs="' + h(r.khach) + '" style="font-size:15.5px;font-weight:600;cursor:pointer">' + h(r.ten_khach || r.khach) +
    (r.hang ? ' <span style="font-size:12px;font-weight:600;color:#0B7C93;background:#E4F9FD;border-radius:999px;padding:3px 9px;margin-left:4px">' + h(r.hang) + '</span>' : '') + '</div>' +
    '<div style="font-size:13px;color:#8a8f9c;margin:2px 0 8px;line-height:1.35">' +
    (r.mua_cuoi ? 'Mua lần cuối ' + crmNgay(r.mua_cuoi) : 'Chưa có ngày mua') + (r.nhom ? ' · ' + h(r.nhom) : '') +
    ' · đồng ý: ' + h(kenh || 'không kênh nào') +
    (r.ket_qua ? '<br>Lần trước: <b style="color:#475467">' + h(r.ket_qua) + '</b>' + (r.lan_cuoi ? ' lúc ' + crmGioNgay(r.lan_cuoi) : '') : '') + '</div>' +
    /* Codex PR #505: kênh theo đồng ý HIỆN TẠI (máy chủ tính). Khách rút đồng ý
       hay vào Danh sách không quảng cáo sau lúc chốt thì không còn nút liên hệ. */
    (+r.ngung ? '<div data-crmngung="1" style="font-size:12.5px;color:#b42318;background:#fef3f2;border-radius:8px;padding:7px 9px;margin:0 0 8px;line-height:1.4">' +
      'Khách đã rút đồng ý hoặc xin không nhận quảng cáo. Không gọi, không nhắn; vẫn ghi kết quả được.</div>' : '') +
    '<div style="display:flex;gap:8px">' +
    (coGoi ? '<a href="tel:' + h(tel) + '" data-crmgoi="' + i + '" style="' + nut + 'background:#12a150;color:#fff">📞 Gọi</a>' : '') +
    (coZalo ? '<button type="button" data-crmchep="' + i + '" style="' + nut + 'background:#E4F9FD;color:#0B7C93">💬 Chép tin</button>' : '') +
    '<button type="button" data-crmkq="' + i + '" style="' + nut + 'background:#f2f4f7;color:#475467">✍ Kết quả</button></div></div>';
}

/* Codex PR #505 vòng 2: Sales ghi "Không muốn nhận tin nữa" thì máy chủ rút
   đồng ý cả hai kênh, nhưng danh sách trên máy vẫn giữ kênh cũ: sang chip Đã
   xong là nút Gọi, Chép tin hiện lại, và dòng của cùng khách ở chiến dịch khác
   vẫn gọi được. Khoá liên hệ MỌI dòng của khách đó ngay trên máy. THUẦN. */
function crmGoiNgungKhach(ds, khach) {
  (ds || []).forEach(function (x) {
    if (x && khach && x.khach === khach) { x.kenh_duoc = ''; x.tin_zalo = ''; x.ngung = 1; }
  });
}

function crmChep(r) {
  if (!r || !r.tin_zalo) return;
  var xong = function () { toast('Đã chép tin cho ' + (r.ten_khach || r.khach) + '. Mở Zalo dán vào.', 3200); };
  try {
    if (navigator && navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(r.tin_zalo).then(xong, function () { baoTin(h(r.tin_zalo), 'Chép tin này gửi khách'); });
      return;
    }
  } catch (e) { }
  baoTin(h(r.tin_zalo), 'Chép tin này gửi khách');
}

function crmSheetKichBan(c) {
  crmMoSheet('<div style="font-size:18px;font-weight:700;margin-bottom:10px">Kịch bản gọi · ' + h(c.ten) + '</div>' +
    '<div style="font-size:15px;line-height:1.55;white-space:pre-line">' + h(c.kich_ban) + '</div>');
}

function crmSheetKetQua(r, ketQua, xong) {
  var chon = '';
  var ov = crmMoSheet('<div style="font-size:18px;font-weight:700;margin-bottom:4px">Kết quả gọi · ' + h(r.ten_khach || r.khach) + '</div>' +
    '<div style="font-size:13px;color:#8a8f9c;margin-bottom:10px">Không nghe máy hay hẹn gọi lại thì khách chuyển sang nhóm Hẹn gọi lại.</div>' +
    kmHangChip((ketQua || []).map(function (k) { return posChipNut('data-crmkqc="' + h(k) + '"', h(k), false, k === 'Không muốn nhận tin nữa'); }).join('')) +
    '<textarea class="nt" id="crmKqGhi" rows="3" maxlength="1000" placeholder="Ghi chú, ví dụ: đặt 2 hộp quà ngày 20/12" style="margin-top:12px"></textarea>' +
    '<button class="btn" data-crmkqluu="1" style="margin-top:12px">Lưu kết quả</button>');
  ov.querySelectorAll('[data-crmkqc]').forEach(function (c) {
    c.onclick = function () {
      chon = c.getAttribute('data-crmkqc');
      ov.querySelectorAll('[data-crmkqc]').forEach(function (x) {
        var on = x === c;
        x.style.background = on ? '#0d9488' : '#fff'; x.style.color = on ? '#fff' : '#374151'; x.style.borderColor = on ? '#0d9488' : '#d7dce5';
      });
    };
  });
  ov.querySelector('[data-crmkqluu]').onclick = async function () {
    if (!chon) { toast('Chọn một kết quả trước.', 3000); return; }
    busy(true);
    try {
      var kq = await api('vagabond.crm.ghi_ket_qua', { name: r.name, ket_qua: chon, ghi_chu: ov.querySelector('#crmKqGhi').value.trim() });
      busy(false); ov.remove();
      r.trang_thai = kq.trang_thai; r.ket_qua = chon;
      if (chon === 'Không muốn nhận tin nữa') { crmGoiNgungKhach(crmGoiDs, r.khach); crmGoiNgungKhach([r], r.khach); }
      toast(chon === 'Không muốn nhận tin nữa' ? 'Đã ghi. Khách sẽ không được gọi hay nhắn quảng cáo nữa.' : 'Đã lưu kết quả');
      if (xong) xong();
    } catch (e) { busy(false); toast(errMsg(e), 5000); }
  };
}

/* ================================================================ nhóm khách */

var crmNhomChon = 'Sắp rời đi';
var crmNhomD = null;

async function scrCrmNhom() {
  var tieuDe = 'Nhóm khách';
  if (!coQuyenCrm()) return frame(tieuDe, crmTrong('🔒', 'Phân hệ Khách hàng chỉ mở cho Sales, quản lý cửa hàng và Marketing.'));
  frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đếm nhóm khách...</div></div>');
  try { crmNhomD = await api('vagabond.crm.nhom_khach', {}); }
  catch (e) { return frame(tieuDe, crmTrong('⚠️', h(errMsg(e)))); }
  crmNhomVe(tieuDe);
}

function crmNhomVe(tieuDe) {
  var d = crmNhomD;
  var tong = d.nhom.reduce(function (t, n) { return t + n.so; }, 0);
  var html = '<div style="font-size:13px;color:#8a8f9c;margin:0 2px 10px;line-height:1.45">Máy chia lại mỗi đêm theo ba câu hỏi: mua gần đây không, mua thường xuyên không, chi bao nhiêu.' +
    (d.tinh_luc ? ' Lần tính gần nhất ' + crmGioNgay(d.tinh_luc) + '.' : ' Chưa tính lần nào: máy sẽ tính trong đêm nay.') + '</div>';
  if (!tong) {
    html += crmTrong('🧩', 'Chưa có số nhóm. Máy tính lần đầu ngay sau khi cập nhật, vài phút sau mở lại màn này.');
  } else {
    html += '<div style="display:flex;gap:8px;flex-wrap:wrap;padding:2px 0 10px">' + d.nhom.map(function (n) {
      return posChipNut('data-crmnh="' + h(n.nhom) + '"', h(n.nhom) + ' <b>' + money(n.so) + '</b>', crmNhomChon === n.nhom);
    }).join('') + '</div>';
    var n = d.nhom.filter(function (x) { return x.nhom === crmNhomChon; })[0] || d.nhom[0];
    var pt = n.so ? Math.round(n.it_nhat_mot * 100 / n.so) : 0;
    html += '<div class="card" data-crmnhthe="1" style="padding:14px">' +
      '<div style="font-weight:700;font-size:16px">' + h(n.nhom) + ' · ' + money(n.so) + ' khách</div>' +
      '<div style="font-size:13px;color:#8a8f9c;margin:2px 0 10px">' + h(n.giai_thich) + '</div>' +
      crmKv('Đã đồng ý Zalo', money(n.zalo)) + crmKv('Đã đồng ý gọi điện', money(n.goi)) +
      crmKv('Đã từ chối', money(n.tu_choi)) + crmKv('Chưa hỏi, hoặc chưa đồng ý kênh nào', money(n.so - n.it_nhat_mot)) +
      '<div style="height:8px;background:#f0f2f6;border-radius:4px;overflow:hidden;margin-top:8px"><i style="display:block;height:100%;background:#50DBF2;width:' + pt + '%"></i></div>' +
      '<div style="font-size:13px;color:#8a8f9c;margin-top:4px">' + pt + '% nhóm này đã đồng ý ít nhất một kênh. Chỉ những khách này được gọi hay nhắn trong chiến dịch.</div>' +
      '<button class="btn gh" data-crmxemkh="1" style="margin:10px 0 0;padding:11px">👀 Xem khách trong nhóm</button></div>';
  }
  html += '<div class="sec">Bộ lọc đã lưu</div><div class="card">' +
    (d.bo_loc.length ? d.bo_loc.map(function (b) {
      return '<div class="hub" data-crmbl="' + h(b.name) + '"><div class="hi">🎯</div><div class="ht"><div class="h1">' + h(b.ten) + '</div>' +
        '<div class="h2">' + h(b.mo_ta) + ' · ' + money(b.so) + ' khách</div></div><span class="fc" style="color:#c3c8d4;font-size:22px">&#8250;</span></div>';
    }).join('') : '<div style="padding:14px;color:#98a2b3;font-size:13px">Chưa có bộ lọc nào. Lưu một bộ lọc để dùng lại khi lập chiến dịch.</div>') +
    '<div style="padding:8px 14px 14px"><button class="btn gh" data-crmblmoi="1" style="margin:0;padding:12px">+ Lưu bộ lọc mới</button></div></div>';
  if (d.duoc_lap && tong) html += '<button class="btn" data-crmlapnhom="1" style="margin:0">📣 Lập chiến dịch từ nhóm ' + h(crmNhomChon) + '</button>';
  var b = frame(tieuDe, html);
  b.onclick = function (e) {
    var c = e.target.closest('[data-crmnh]');
    if (c) { crmNhomChon = c.getAttribute('data-crmnh'); return crmNhomVe(tieuDe); }
    if (e.target.closest('[data-crmxemkh]')) return crmSheetXemLoc({ nhom: [crmNhomChon] }, 'Nhóm ' + crmNhomChon);
    var bl = e.target.closest('[data-crmbl]');
    if (bl) {
      var x = d.bo_loc.filter(function (y) { return y.name === bl.getAttribute('data-crmbl'); })[0];
      return crmSheetXemLoc(x.loc, x.ten, x);
    }
    if (e.target.closest('[data-crmblmoi]')) return crmSheetBoLoc(null, function () { scrCrmNhom(); });
    if (e.target.closest('[data-crmlapnhom]')) { crmCdMoi = { loc: { nhom: [crmNhomChon] } }; return go(function () { scrCrmCd(''); }); }
  };
}

function crmKv(nhan, gt) {
  return '<div style="display:flex;justify-content:space-between;gap:10px;padding:9px 0;border-bottom:1px solid #f0f2f6;font-size:14.5px"><span>' + h(nhan) + '</span><b>' + h(gt) + '</b></div>';
}

/* Xem mẫu khách khớp một bộ lọc, kèm nút lập chiến dịch và ẩn bộ lọc. */
async function crmSheetXemLoc(loc, ten, boLoc) {
  busy(true);
  var d;
  try { d = await api('vagabond.crm.ds_khach_loc', { loc: JSON.stringify(loc), so_dong: 30 }); }
  catch (e) { busy(false); return toast(errMsg(e), 5000); }
  busy(false);
  var ov = crmMoSheet('<div style="font-size:18px;font-weight:700">' + h(ten) + '</div>' +
    '<div style="font-size:13px;color:#8a8f9c;margin:2px 0 10px">' + h(d.mo_ta) + ' · <b>' + money(d.so) + ' khách</b>' + (d.so > d.dong.length ? ', hiện ' + d.dong.length + ' khách mua gần nhất' : '') + '</div>' +
    (d.dong.length ? d.dong.map(function (r) {
      return '<div data-crmxkh="' + h(r.khach) + '" data-crmxten="' + h(r.ten || '') + '" style="padding:10px 0;border-bottom:1px solid #f0f2f6;cursor:pointer;min-height:44px">' +
        '<div style="font-size:14.5px;font-weight:600">' + h(r.ten || r.khach) + (r.hang ? ' · <span style="color:#0B7C93">' + h(r.hang) + '</span>' : '') + '</div>' +
        '<div style="font-size:12.5px;color:#8a8f9c">' + h(r.nhom || '') + (r.lan_cuoi ? ' · mua lần cuối ' + crmNgay(r.lan_cuoi) : '') +
        ' · Zalo ' + (r.dy_zalo === 'Đồng ý' ? '✓' : '✗') + ' · gọi ' + (r.dy_goi === 'Đồng ý' ? '✓' : '✗') + '</div></div>';
    }).join('') : '<div style="color:#98a2b3;padding:10px 0">Không có khách nào khớp.</div>') +
    (crmCoLap() && d.so ? '<button class="btn" data-crmxlap="1" style="margin-top:12px">📣 Lập chiến dịch từ ' + (boLoc ? 'bộ lọc' : 'nhóm') + ' này</button>' : '') +
    (boLoc ? '<button class="btn gh" data-crmxan="1" style="margin-top:9px">Ẩn bộ lọc này</button>' : ''));
  ov.onclick = async function (e) {
    if (e.target === ov) return ov.remove();
    var kh = e.target.closest('[data-crmxkh]');
    if (kh) { ov.remove(); return crmMoHoSo(kh.getAttribute('data-crmxkh'), kh.getAttribute('data-crmxten') || ''); }
    if (e.target.closest('[data-crmxlap]')) {
      ov.remove();
      crmCdMoi = { loc: loc, bo_loc: boLoc ? boLoc.name : '', ten_loc: ten };
      return go(function () { scrCrmCd(''); });
    }
    if (e.target.closest('[data-crmxan]')) {
      busy(true);
      try { await api('vagabond.crm.an_bo_loc', { name: boLoc.name }); busy(false); ov.remove(); toast('Đã ẩn bộ lọc'); scrCrmNhom(); }
      catch (er) { busy(false); toast(errMsg(er), 5000); }
    }
  };
}

/* Tấm dựng bộ lọc: nhóm, khoảng ngày mua cuối, số ngày chưa mua, món đã mua,
   kênh đã đồng ý. Món chọn từ danh mục (QT-31), không gõ tay mã. */
function crmSheetBoLoc(cu, xong) {
  var loc = JSON.parse(JSON.stringify((cu && cu.loc) || {}));
  loc.nhom = loc.nhom || []; loc.dong_y = loc.dong_y || [];
  var tenMon = (cu && cu.ten_mon) || loc.mon || '';
  var ov = crmMoSheet('');
  var box = ov.querySelector('.shb');
  function ve() {
    box.innerHTML = '<div style="font-size:18px;font-weight:700;margin-bottom:10px">Bộ lọc khách mới</div>' +
      '<div style="font-size:12px;color:#0B7C93;font-weight:600;margin-bottom:6px">TÊN BỘ LỌC</div>' +
      '<input class="tin" id="crmBlTen" value="' + h((cu && cu.ten) || '') + '" placeholder="Ví dụ: Khách mùa lễ năm ngoái" style="font-size:15px;font-weight:500;text-align:left;padding:0 12px">' +
      '<div style="font-size:12px;color:#0B7C93;font-weight:600;margin:12px 0 6px">NHÓM (không chọn là mọi nhóm)</div>' +
      kmHangChip(CRM_NHOM.map(function (n) { return posChipNut('data-crmbln="' + h(n) + '"', h(n), loc.nhom.indexOf(n) >= 0); }).join('')) +
      '<div style="font-size:12px;color:#0B7C93;font-weight:600;margin:12px 0 6px">MUA LẦN CUỐI TỪ NGÀY, TỚI NGÀY</div>' +
      '<div style="display:flex;gap:8px"><input class="tin" type="date" id="crmBlTu" value="' + h(loc.lan_cuoi_tu || '') + '" style="font-size:15px;font-weight:500">' +
      '<input class="tin" type="date" id="crmBlDen" value="' + h(loc.lan_cuoi_den || '') + '" style="font-size:15px;font-weight:500"></div>' +
      '<div style="font-size:12px;color:#0B7C93;font-weight:600;margin:12px 0 6px">ĐÃ ÍT NHẤT BAO NHIÊU NGÀY CHƯA MUA</div>' +
      '<input class="tin" type="number" inputmode="numeric" id="crmBlNgay" value="' + h(loc.chua_mua_ngay || '') + '" placeholder="Để trống là không xét" style="font-size:15px;font-weight:500">' +
      '<div style="font-size:12px;color:#0B7C93;font-weight:600;margin:12px 0 6px">ĐÃ MUA MÓN (hoá đơn từ 08/2026)</div>' +
      '<button class="btn gh" data-crmblmon="1" style="margin:0;padding:12px;text-align:left">' + (loc.mon ? '🍰 ' + h(tenMon) + ' · bấm để đổi' : '🍰 Chọn món từ danh mục') + '</button>' +
      (loc.mon ? '<button class="btn gh" data-crmblbomon="1" style="margin:6px 0 0;padding:9px;font-size:13px">Bỏ điều kiện món</button>' : '') +
      '<div style="font-size:12px;color:#0B7C93;font-weight:600;margin:12px 0 6px">CHỈ KHÁCH ĐÃ ĐỒNG Ý (không chọn là không xét)</div>' +
      kmHangChip(['Gọi điện', 'Zalo'].map(function (k) { return posChipNut('data-crmbldy="' + h(k) + '"', CRM_IC_KENH[k] + ' ' + h(k), loc.dong_y.indexOf(k) >= 0); }).join('')) +
      '<div id="crmBlDem" style="font-size:13.5px;color:#475467;margin-top:12px"></div>' +
      '<div style="display:flex;gap:10px;margin-top:12px"><button class="btn gh" data-crmbldem="1" style="margin:0;flex:1">Đếm thử</button>' +
      '<button class="btn" data-crmblluu="1" style="margin:0;flex:1">Lưu bộ lọc</button></div>';
  }
  function docO() {
    loc.lan_cuoi_tu = box.querySelector('#crmBlTu').value || '';
    loc.lan_cuoi_den = box.querySelector('#crmBlDen').value || '';
    loc.chua_mua_ngay = parseInt(box.querySelector('#crmBlNgay').value, 10) || '';
    if (cu) cu.ten = box.querySelector('#crmBlTen').value; else cu = { ten: box.querySelector('#crmBlTen').value };
  }
  ve();
  box.onclick = async function (e) {
    var n = e.target.closest('[data-crmbln]');
    if (n) { docO(); var v = n.getAttribute('data-crmbln'), i = loc.nhom.indexOf(v); if (i >= 0) loc.nhom.splice(i, 1); else loc.nhom.push(v); return ve(); }
    var dy = e.target.closest('[data-crmbldy]');
    if (dy) { docO(); var k = dy.getAttribute('data-crmbldy'), j = loc.dong_y.indexOf(k); if (j >= 0) loc.dong_y.splice(j, 1); else loc.dong_y.push(k); return ve(); }
    if (e.target.closest('[data-crmblmon]')) {
      docO();
      var ds = await vgbChonMon({ tieu_de: 'Khách đã mua món nào?', nhieu: false });
      if (ds && ds.length) { loc.mon = ds[0].ma; tenMon = ds[0].ten; }
      return ve();
    }
    if (e.target.closest('[data-crmblbomon]')) { docO(); loc.mon = ''; tenMon = ''; return ve(); }
    if (e.target.closest('[data-crmbldem]')) {
      docO();
      try {
        var d = await api('vagabond.crm.ds_khach_loc', { loc: JSON.stringify(loc), so_dong: 1 });
        box.querySelector('#crmBlDem').innerHTML = h(d.mo_ta) + ': <b>' + money(d.so) + ' khách</b>';
      } catch (er) { toast(errMsg(er), 5000); }
      return;
    }
    if (e.target.closest('[data-crmblluu]')) {
      docO();
      busy(true);
      try {
        await api('vagabond.crm.luu_bo_loc', { ten: (cu && cu.ten) || '', loc: JSON.stringify(loc) });
        busy(false); ov.remove(); toast('Đã lưu bộ lọc'); if (xong) xong();
      } catch (er) { busy(false); toast(errMsg(er), 5000); }
    }
  };
}

/* ================================================================ sổ đồng ý */

var crmDyLoc = '';
/* Codex PR #505 vòng 2: sổ chỉ trả 100 dòng mới nhất, không tìm được bằng
   chứng của một khách cũ. Ô tìm hỏi máy chủ (tên, mã, một phần số điện thoại),
   nút Xem thêm lấy tiếp các dòng cũ hơn. */
var crmDyTim = '', crmDyDong = [], crmDyCon = 0;

async function scrCrmDongY(them) {
  var tieuDe = 'Sổ đồng ý nhận tin';
  if (!coQuyenCrm()) return frame(tieuDe, crmTrong('🔒', 'Phân hệ Khách hàng chỉ mở cho Sales, quản lý cửa hàng và Marketing.'));
  var bat = them === true ? crmDyDong.length : 0;
  if (bat) busy(true);
  else frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc sổ đồng ý...</div></div>');
  var d;
  try { d = await api('vagabond.crm.so_dong_y', { trang_thai: crmDyLoc, tim: crmDyTim, bat_dau: bat }); }
  catch (e) {
    if (bat) { busy(false); return toast(errMsg(e), 5000); }
    return frame(tieuDe, crmTrong('⚠️', h(errMsg(e))));
  }
  if (bat) busy(false);
  crmDyDong = bat ? crmDyDong.concat(d.dong || []) : (d.dong || []);
  crmDyCon = +d.con_nua ? 1 : 0;
  d.dong = crmDyDong;
  var html = '<div style="font-size:13px;color:#8a8f9c;margin:0 2px 10px;line-height:1.45">Mỗi lần khách đồng ý hay từ chối đều có một dòng ở đây: kênh nào, ghi ở đâu, ai ghi, lúc nào. Đây là bằng chứng khi cần.</div>' +
    '<div class="card" style="padding:4px 14px 10px">';
  ['Zalo', 'Gọi điện', 'Email'].forEach(function (k) {
    var t = d.tong[k] || {};
    html += '<div data-crmdytong="' + h(k) + '" style="display:flex;justify-content:space-between;gap:10px;padding:10px 0;border-bottom:1px solid #f0f2f6;font-size:14.5px">' +
      '<span>' + CRM_IC_KENH[k] + ' ' + h(k) + '</span><span><b style="color:#05603a">' + money(t['Đồng ý'] || 0) + ' đồng ý</b> · ' +
      '<b style="color:#b42318">' + money(t['Từ chối'] || 0) + ' từ chối</b> · ' + money(t['Chưa hỏi'] || 0) + ' chưa hỏi</span></div>';
  });
  html += '<div style="display:flex;justify-content:space-between;padding:10px 0;font-size:14.5px"><span>🚫 Danh sách không quảng cáo</span><b>' + money(d.khong_quang_cao) + ' số</b></div></div>';
  var cc = {
    ma: 'crmDy',
    chang: { ds: [{ k: 'Đồng ý', ten: 'Đồng ý' }, { k: 'Từ chối', ten: 'Từ chối' }], dem: null, chon: crmDyLoc, tatCa: 'Tất cả' },
    tim: { gt: crmDyTim, goiY: '🔎 Tìm tên khách, mã khách, số điện thoại' }
  };
  html += dsCongCu(cc);
  if (crmDyTim) html += '<div data-crmdyloc="1" style="font-size:13px;color:#101828;background:#fffaeb;border-radius:8px;padding:8px 10px;margin:0 0 10px">Đang tìm "' +
    h(crmDyTim) + '": <b>' + money(crmDyDong.length) + (crmDyCon ? '+' : '') + ' dòng</b></div>';
  html += (d.dong || []).length ? '<div class="card">' + d.dong.map(function (r) {
    return '<div data-crmdykh="' + h(r.khach) + '" style="padding:12px 14px;border-bottom:1px solid #f0f2f6;cursor:pointer">' +
      '<div style="display:flex;justify-content:space-between;gap:8px"><b style="font-size:14.5px">' + h(r.ten_khach) + '</b>' +
      crmTagDy(r.kenh, r.trang_thai) + '</div>' +
      '<div style="font-size:12.5px;color:#8a8f9c">' + h(r.noi_ghi || '') + ' · ' + h(r.ten_nguoi || '') + ' · ' + crmGioNgay(r.luc) + '</div></div>';
  }).join('') + '</div>' : crmTrong(crmDyTim ? '🔎' : '✅', crmDyTim ? 'Không có dòng nào khớp chữ tìm. Thử tên khác hoặc vài số cuối của điện thoại.'
    : 'Chưa có dòng nào. Khi thu ngân hỏi khách ở quầy, dòng đầu tiên hiện ở đây.');
  if (crmDyCon) html += '<button class="btn gh" data-crmdythem="1" style="margin:0">Xem thêm dòng cũ hơn</button>';
  var b = frame(tieuDe, html);
  dsCongCuNoi(b, cc, function (ho, v) {
    if (ho === 'chang') crmDyLoc = v; else if (ho === 'tim') crmDyTim = v;
    scrCrmDongY();
  });
  b.onclick = function (e) {
    if (e.target.closest('[data-crmdythem]')) return scrCrmDongY(true);
    var kh = e.target.closest('[data-crmdykh]');
    if (kh) { var dd = crmDyDong.filter(function (x) { return x.khach === kh.getAttribute('data-crmdykh'); })[0] || {};
      return crmMoHoSo(kh.getAttribute('data-crmdykh'), dd.ten_khach); }
  };
}

/* ================================================================ chiến dịch */

var crmCdMoi = null;   /* dữ liệu mở sẵn khi lập chiến dịch từ màn Nhóm khách */

function crmTagTt(tt) {
  return crmTag(tt, tt === 'Đang chạy' ? 'xanh' : tt === 'Nháp' ? 'vang' : 'xam');
}

var crmCdTt = '', crmCdTim = '';
/* Codex PR #505 vòng 3: máy chủ lọc theo trạng thái và chữ tìm, trả từng
   trang; nút Xem thêm lấy tiếp chiến dịch cũ hơn. Không lọc trên số dòng đã
   tải, vì chiến dịch cũ nằm ngoài trang đầu. */
var crmCdDsDong = [], crmCdDsCon = 0;
async function crmDsCd(them, loc) {
  var bat = them === true ? crmCdDsDong.length : 0;
  var d = await api('vagabond.crm.ds_chien_dich', Object.assign({ bat_dau: bat }, loc));
  crmCdDsDong = bat ? crmCdDsDong.concat(d.ds || []) : (d.ds || []);
  crmCdDsCon = +d.con_nua ? 1 : 0;
  return d;
}

async function scrCrmCdDs(them) {
  var tieuDe = 'Chiến dịch';
  if (!coQuyenCrm()) return frame(tieuDe, crmTrong('🔒', 'Phân hệ Khách hàng chỉ mở cho Sales, quản lý cửa hàng và Marketing.'));
  if (them === true) busy(true);
  else frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc chiến dịch...</div></div>');
  var d;
  try { d = await crmDsCd(them, { trang_thai: crmCdTt, tim: crmCdTim }); }
  catch (e) { if (them === true) { busy(false); return toast(errMsg(e), 5000); } return frame(tieuDe, crmTrong('⚠️', h(errMsg(e)))); }
  if (them === true) busy(false);
  var dem = d.dem || {};
  var cc = {
    ma: 'crmCd',
    chang: { ds: ['Nháp', 'Đang chạy', 'Đã kết thúc'].map(function (t) { return { k: t, ten: t }; }), dem: dem, chon: crmCdTt, tatCa: 'Tất cả' },
    tim: { gt: crmCdTim, goiY: '🔎 Tìm tên hoặc mã chiến dịch' }
  };
  var ds = crmCdDsDong, coGi = +dem.tat_ca || crmCdTim || crmCdTt;
  var html = (coGi ? dsCongCu(cc) : '') + (ds.length ? '<div class="card">' + ds.map(function (c) {
    var td = c.tien_do || {}, tong = (td['Chưa gọi'] || 0) + (td['Hẹn gọi lại'] || 0) + (td['Đã xong'] || 0);
    return '<div class="hub" data-crmcdmo="' + h(c.name) + '"><div class="hi">📣</div><div class="ht"><div class="h1">' + h(c.ten) + '</div>' +
      '<div class="h2">' + crmTagTt(c.trang_thai) + (c.ngay_chot ? 'chốt ' + crmNgay(c.ngay_chot) + ' · ' : '') +
      (tong ? 'đã gọi ' + (tong - (td['Chưa gọi'] || 0)) + ' / ' + tong : 'chưa chốt danh sách') + '</div></div>' +
      '<span class="fc" style="color:#c3c8d4;font-size:22px">&#8250;</span></div>';
  }).join('') + '</div>' : crmTrong('📣', coGi ? 'Không có chiến dịch nào khớp.' : 'Chưa có chiến dịch nào.' + (d.duoc_lap ? ' Bấm nút dưới để lập chiến dịch đầu tiên.' : '')));
  if (crmCdDsCon) html += '<button class="btn gh" data-crmcdthem="1" style="margin:0 0 10px">Xem thêm chiến dịch cũ hơn</button>';
  if (d.duoc_lap) html += '<button class="btn" data-crmcdnew="1" style="margin:0">+ Chiến dịch mới</button>';
  var b = frame(tieuDe, html);
  dsCongCuNoi(b, cc, function (ho, v) {
    if (ho === 'chang') crmCdTt = v; else if (ho === 'tim') crmCdTim = v;
    scrCrmCdDs();
  });
  b.onclick = function (e) {
    if (e.target.closest('[data-crmcdthem]')) return scrCrmCdDs(true);
    var m = e.target.closest('[data-crmcdmo]');
    if (m) { var ten = m.getAttribute('data-crmcdmo'); return go(function () { scrCrmCd(ten); }); }
    if (e.target.closest('[data-crmcdnew]')) { crmCdMoi = null; return go(function () { scrCrmCd(''); }); }
  };
}

var crmCd = null;
/* Codex PR #505 (AGENTS.md: màn lập phiếu phải có bản nháp tự lưu, v533).
   48-ban-soan-do.js khai loại 'chien_dich' và bọc scrCrmCd. Phần 58 đứng sau
   48 nên không dùng móc sdGhep: 48 gọi dat() TRƯỚC khi mở màn, gán bản nháp
   vào crmCdKhoiPhuc, rồi scrCrmCd ghép vào ngay sau khi dựng trạng thái. */
var crmCdKhoiPhuc = null;
var CRM_CD_NHAP = ['name', 'ten', 'loc', 'bo_loc', 'mo_ta_loc', 'kenh_goi', 'kenh_zalo', 'mon', 'sales', 'ctkm',
  'ma_uu_dai', 'han', 'kich_ban', 'noi_dung_zalo', 'ty_le_doi_chung'];
function crmCdNhap() {
  var c = crmCd;
  if (!c || c.trang_thai !== 'Nháp' || !+c.duoc_lap) return null;
  crmCdDocO();
  var o = {};
  CRM_CD_NHAP.forEach(function (k) { o[k] = c[k]; });
  return JSON.parse(JSON.stringify(o));
}
function crmCdGhepNhap() {
  var v = crmCdKhoiPhuc; crmCdKhoiPhuc = null;
  if (!v || !crmCd || crmCd.trang_thai !== 'Nháp' || (v.name || '') !== (crmCd.name || '')) return;
  CRM_CD_NHAP.forEach(function (k) { if (v[k] !== undefined) crmCd[k] = v[k]; });
  /* Khung số "Ai sẽ được liên hệ" tính theo bản trên máy chủ, có thể đã cũ so
     với bản nháp: ẩn đi tới khi Lưu nháp đếm lại. */
  if (v.name) { crmCd.dong_chay = null; crmCd.ly_do_chua_chot = 'Lưu nháp để máy đếm lại khách theo bản đang soạn.'; }
}

/* Codex PR #505 vòng 2: Duyệt và Chốt chỉ gửi mã chiến dịch, máy chủ làm trên
   bản ĐÃ LƯU. Sửa kịch bản, nhóm, kênh hay Sales mà chưa Lưu nháp rồi bấm Chốt
   thì chốt nhầm bản cũ và mất phần vừa sửa. Giữ dấu của bản máy chủ trả về,
   khác dấu thì bắt Lưu nháp trước. */
var crmCdGoc = '';
var CRM_CD_CHUA_LUU = 'Có thay đổi chưa lưu. Bấm Lưu nháp để máy đếm lại khách và kiểm duyệt, rồi mới duyệt hay chốt.';
function crmCdDau(c) {
  c = c || {};
  var s = function (x) { return String(x == null ? '' : x); };
  var xep = function (o) {
    if (!o || typeof o !== 'object') return o == null ? '' : o;
    if (Array.isArray(o)) return o.map(xep);
    var r = {}; Object.keys(o).sort().forEach(function (k) { r[k] = xep(o[k]); }); return r;
  };
  return JSON.stringify([s(c.ten), xep(c.loc || {}), s(c.bo_loc), +c.kenh_goi ? 1 : 0, +c.kenh_zalo ? 1 : 0,
    (c.mon || []).map(function (x) { return s(x && x.item); }), (c.sales || []).map(function (x) { return s(x && x.nguoi); }),
    s(c.ctkm), s(c.han), s(c.kich_ban), s(c.noi_dung_zalo), +c.ty_le_doi_chung || 0]);
}
function crmCdChuaLuu() { return !!(crmCd && crmCd.name) && crmCdDau(crmCd) !== crmCdGoc; }
/* Codex PR #505 vòng 4: Lưu nháp xong thì 48 thôi theo dõi (sdDaLuu) mà màn
   vẫn sửa tiếp được, tải lại trang là mất phần sửa sau. Lưu xong mở lại màn
   qua bản bọc của 48 với mã chiến dịch vừa có, để bản nháp tự lưu theo dõi
   lại đúng chiến dịch đó; dùng luôn bản máy chủ vừa trả, không hỏi lại. */
var crmCdSan = null;

async function scrCrmCd(name) {
  var tieuDe = name ? 'Chiến dịch' : 'Chiến dịch mới';
  crmCdGoc = '';
  if (name && crmCdSan && crmCdSan.name === name) {
    crmCd = crmCdSan; crmCdSan = null;
    crmCdGoc = crmCdDau(crmCd);
  } else if (name) {
    crmCdSan = null;
    frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc chiến dịch...</div></div>');
    try { crmCd = await api('vagabond.crm.doc_chien_dich', { name: name }); }
    catch (e) { return frame(tieuDe, crmTrong('⚠️', h(errMsg(e)))); }
    crmCdGoc = crmCdDau(crmCd);
  } else {
    var m = crmCdMoi || {};
    crmCd = {
      name: '', ten: '', trang_thai: 'Nháp', loc: m.loc || {}, bo_loc: m.bo_loc || '', mo_ta_loc: m.ten_loc || '',
      kenh_goi: 1, kenh_zalo: 0, ty_le_doi_chung: 10, mon: [], sales: [], kich_ban: '', noi_dung_zalo: '',
      ctkm: '', ma_uu_dai: '', han: '', kich_ban_duyet: 0, duoc_lap: crmCoLap() ? 1 : 0, duoc_duyet: hasRole('System Manager') ? 1 : 0,
      dong_chay: null, ly_do_chua_chot: ''
    };
    crmCdMoi = null;
  }
  crmCdGhepNhap();
  crmCdVe();
}

function crmCdNhan(t) { return '<div style="font-size:12px;color:#0B7C93;font-weight:600;margin:12px 0 6px">' + t + '</div>'; }

function crmCdVe() {
  var c = crmCd, nhap = c.trang_thai === 'Nháp', sua = nhap && c.duoc_lap;
  var dis = sua ? '' : ' disabled';
  var html = '';
  if (!nhap) html += '<div class="card" style="padding:12px 14px">' + crmTagTt(c.trang_thai) +
    '<div style="font-size:13px;color:#475467">Chốt ' + crmGioNgay(c.ngay_chot) + '. Danh sách đã khoá, không đổi theo nhóm chạy đêm.</div></div>';
  html += '<div class="card" style="padding:4px 14px 14px">' +
    crmCdNhan('TÊN CHIẾN DỊCH') +
    '<input class="tin" id="crmCdTen" value="' + h(c.ten) + '"' + dis + ' placeholder="Ví dụ: Giáng sinh 2026 gọi khách mùa lễ cũ" style="font-size:15px;font-weight:500;text-align:left;padding:0 12px">' +
    crmCdNhan('NHÓM KHÁCH') +
    '<button class="btn gh" data-crmcdloc="1"' + dis + ' style="margin:0;padding:12px;text-align:left">🎯 ' + h(c.mo_ta_loc || 'Chọn nhóm hoặc bộ lọc đã lưu') + '</button>' +
    crmCdNhan('KÊNH') +
    kmHangChip(
      (sua ? posChipNut('data-crmcdk="goi"', '📞 Gọi điện', !!+c.kenh_goi) + posChipNut('data-crmcdk="zalo"', '💬 Zalo cá nhân', !!+c.kenh_zalo)
        : (+c.kenh_goi ? posChipNut('data-x', '📞 Gọi điện', true) : '') + (+c.kenh_zalo ? posChipNut('data-x', '💬 Zalo cá nhân', true) : '')) +
      '<span style="border:1.5px dashed #d0d5dd;color:#a0a6b2;border-radius:999px;padding:9px 13px;font-size:13px">Zalo OA hàng loạt · đợt 2</span>') +
    crmCdNhan('MÓN GIỚI THIỆU') +
    /* Codex PR #505 vòng 4: mỗi món giới thiệu một dòng có ảnh món (ô 🍰 khi chưa có ảnh). */
    '<div>' + (c.mon || []).map(function (x, i) {
      return '<div class="li" data-crmcdmonr="' + h(x.item) + '" style="padding:8px 0;cursor:default">' + anhMon(x.anh) +
        '<div class="lt"><div class="l1" style="font-size:14.5px">' + h(x.ten || x.item) + '</div></div>' +
        (sua ? '<button type="button" data-crmcdbomon="' + i + '" aria-label="Bỏ món này" style="border:0;background:#f2f4f7;color:#475467;border-radius:10px;min-width:44px;min-height:44px;font-size:16px">✕</button>' : '') + '</div>';
    }).join('') + (sua ? '<button class="btn gh" data-crmcdmon="1" style="margin:4px 0 0;padding:10px;font-size:14px">+ Thêm món</button>' : '') + '</div>' +
    crmCdNhan('MÃ ƯU ĐÃI RIÊNG') +
    '<button class="btn gh" data-crmcdkm="1"' + dis + ' style="margin:0;padding:12px;text-align:left">🎫 ' +
    (c.ctkm ? h(c.ctkm) + (c.ma_uu_dai ? ' · mã ' + h(c.ma_uu_dai) : '') : 'Chọn chương trình khuyến mãi có mã cố định') + '</button>' +
    '<div style="font-size:12px;color:#8a8f9c;margin-top:4px">Mã riêng của chiến dịch để đếm đơn chiến dịch mang về. Tạo chương trình ở Khuyến mãi trước, chọn "Mã cố định".</div>' +
    crmCdNhan('HẠN CHIẾN DỊCH') +
    '<input class="tin" type="date" id="crmCdHan" value="' + h(c.han || '') + '"' + dis + ' style="font-size:15px;font-weight:500">' +
    crmCdNhan('SALES NHẬN DANH SÁCH') +
    '<div>' + (c.sales || []).map(function (s, i) {
      return crmTag('👤 ' + (s.ten || s.nguoi), 'xam').replace('</span>', sua ? ' <b data-crmcdbosl="' + i + '" style="cursor:pointer">✕</b></span>' : '</span>');
    }).join('') + (sua ? '<button class="btn gh" data-crmcdsl="1" style="margin:4px 0 0;padding:10px;font-size:14px">+ Thêm Sales</button>' : '') + '</div>' +
    crmCdNhan('KỊCH BẢN GỌI ' + (+c.kich_ban_duyet ? '<span style="color:#05603a">· đã duyệt</span>' : '<span style="color:#93370d">· chưa duyệt</span>')) +
    '<textarea class="nt" id="crmCdKb" rows="4"' + dis + ' placeholder="Ví dụ: chào khách, giới thiệu món mới mùa lễ, nhắc mã ưu đãi và hạn dùng">' + h(c.kich_ban || '') + '</textarea>' +
    (sua ? '<div style="font-size:12px;color:#8a8f9c;margin-top:4px">Sửa kịch bản sau khi duyệt thì phải duyệt lại.</div>' : '') +
    crmCdNhan('TIN ZALO SOẠN SẴN ({ten} là tên khách)') +
    '<textarea class="nt" id="crmCdZalo" rows="3"' + dis + ' placeholder="Ví dụ: Chào {ten}, The Vagabond có món mới mùa Giáng sinh...">' + h(c.noi_dung_zalo || '') + '</textarea>' +
    '</div>';
  var dc = c.dong_chay;
  if (dc) {
    html += '<div class="sec">Ai sẽ được liên hệ</div><div class="card" data-crmdc="1">' +
      crmDcDong('Trong nhóm', money(dc.trong_nhom), '') +
      crmDcDong('Loại: chưa đồng ý kênh đã chọn', '− ' + money(dc.chua_dong_y), 'loai') +
      crmDcDong('Loại: trong Danh sách không quảng cáo', '− ' + money(dc.khong_quang_cao), 'loai') +
      crmDcDong('Đối chứng ' + (c.ty_le_doi_chung || 0) + '%: giữ lại, không liên hệ', money(dc.doi_chung), 'dc') +
      crmDcDong('Chia cho ' + (dc.so_sales || 0) + ' Sales', money(dc.nhan), 'ok') + '</div>' +
      crmChan('Máy chọn đối chứng ngẫu nhiên và khoá cố định lúc chốt. Danh sách đã chốt không đổi theo nhóm chạy đêm.');
  }
  if (sua) {
    var chuaLuu = crmCdChuaLuu(), lyDo = c.ly_do_chua_chot || (chuaLuu ? CRM_CD_CHUA_LUU : '');
    html += '<button class="btn gh" data-crmcdluu="1" style="margin:0 0 10px">💾 Lưu nháp' + (c.name ? '' : ' và đếm khách') + '</button>';
    if (c.name && c.duoc_duyet && !+c.kich_ban_duyet) html += '<button class="btn gh" data-crmcdduyet="1"' + (chuaLuu ? ' disabled' : '') + ' style="margin:0 0 10px">✔ Duyệt kịch bản gọi</button>';
    if (c.name) {
      if (lyDo) html += '<div data-crmlydo="1" style="font-size:13px;color:#93370d;margin:0 2px 8px">' + h(lyDo) + '</div>';
      html += '<button class="btn" data-crmcdchot="1"' + (lyDo ? ' disabled' : '') + ' style="margin:0">Chốt danh sách và chia việc</button>';
    }
  } else if (!nhap) {
    html += '<button class="btn" data-crmcdhq="1" style="margin:0 0 10px">📊 Xem hiệu quả</button>';
    if (c.duoc_lap && c.trang_thai === 'Đang chạy') html += '<button class="btn gh" data-crmcdkt="1" style="margin:0">Kết thúc chiến dịch</button>';
  }
  var b = frame(c.name ? c.ten || 'Chiến dịch' : 'Chiến dịch mới', html);
  b.onclick = crmCdBam;
}

function crmDcDong(nhan, so, kieu) {
  var nen = kieu === 'ok' ? 'background:#f3fcfe;' : kieu === 'dc' ? 'background:#fffaeb;' : '';
  var mau = kieu === 'loai' ? '#b42318' : kieu === 'ok' ? '#0B7C93' : kieu === 'dc' ? '#93370d' : '#16181d';
  return '<div data-crmdcd="' + h(kieu || 'tong') + '" style="display:flex;align-items:center;justify-content:space-between;gap:8px;padding:10px 14px;border-bottom:1px solid #f0f2f6;font-size:14.5px;' + nen + '">' +
    '<span style="color:#475467">' + h(nhan) + '</span><b style="font-size:16px;color:' + mau + '">' + h(so) + '</b></div>';
}

function crmCdDocO() {
  /* Ô không có trên màn (đã rời màn, bản nháp tự lưu gọi tới) thì giữ giá trị
     cũ, không ghi chuỗi rỗng đè lên. */
  var c = crmCd, v = function (id, cu) { var n = document.getElementById(id); return n ? n.value : cu; };
  c.ten = v('crmCdTen', c.ten); c.han = v('crmCdHan', c.han); c.kich_ban = v('crmCdKb', c.kich_ban);
  c.noi_dung_zalo = v('crmCdZalo', c.noi_dung_zalo);
}

async function crmCdBam(e) {
  var c = crmCd;
  if (e.target.closest('[disabled]')) return;
  var k = e.target.closest('[data-crmcdk]');
  if (k) { crmCdDocO(); var kk = k.getAttribute('data-crmcdk') === 'goi' ? 'kenh_goi' : 'kenh_zalo'; c[kk] = +c[kk] ? 0 : 1; return crmCdVe(); }
  var bm = e.target.closest('[data-crmcdbomon]');
  if (bm) { crmCdDocO(); c.mon.splice(+bm.getAttribute('data-crmcdbomon'), 1); return crmCdVe(); }
  var bs = e.target.closest('[data-crmcdbosl]');
  if (bs) { crmCdDocO(); c.sales.splice(+bs.getAttribute('data-crmcdbosl'), 1); return crmCdVe(); }
  if (e.target.closest('[data-crmcdmon]')) {
    crmCdDocO();
    var ds = await vgbChonMon({ tieu_de: 'Món giới thiệu trong chiến dịch', nhieu: true });
    (ds || []).forEach(function (m) {
      if (!c.mon.some(function (x) { return x.item === m.ma; })) c.mon.push({ item: m.ma, ten: m.ten, anh: m.hinh || '' });
    });
    return crmCdVe();
  }
  if (e.target.closest('[data-crmcdsl]')) {
    crmCdDocO();
    var sl;
    try { sl = await api('vagabond.crm.ds_sales', {}); } catch (er) { return toast(errMsg(er), 5000); }
    var chon = await hoiChonNhieu('Sales nhận danh sách gọi', 'Khách được chia đều, lần lượt từng người.',
      (sl.ds || []).map(function (u) { return { k: u.name, nhan: u.ten, mo_ta: u.name }; }),
      c.sales.map(function (s) { return s.nguoi; }), 'Chọn');
    if (chon) {
      c.sales = chon.map(function (u) {
        var x = (sl.ds || []).filter(function (y) { return y.name === u; })[0];
        return { nguoi: u, ten: x ? x.ten : u };
      });
    }
    return crmCdVe();
  }
  if (e.target.closest('[data-crmcdkm]')) {
    crmCdDocO();
    var km;
    try { km = await api('vagabond.crm.ds_ctkm_ma', {}); } catch (er) { return toast(errMsg(er), 5000); }
    if (!(km.ds || []).length) return baoTin('Chưa có chương trình khuyến mãi nào đang bật mà dùng "Mã cố định". Tạo ở phân hệ Bán hàng, Chương trình khuyến mãi, rồi quay lại chọn.', 'Chưa có mã để chọn');
    var ma = await hoiChon('Mã ưu đãi riêng của chiến dịch', 'Chọn một chương trình có mã cố định.',
      km.ds.map(function (x) { return { k: x.name, nhan: x.ten || x.name, mo_ta: 'Mã ' + x.ma + (x.den_ngay ? ' · tới ' + crmNgay(x.den_ngay) : '') }; }), c.ctkm);
    if (ma) { c.ctkm = ma; c.ma_uu_dai = (km.ds.filter(function (x) { return x.name === ma; })[0] || {}).ma || ''; }
    return crmCdVe();
  }
  if (e.target.closest('[data-crmcdloc]')) {
    crmCdDocO();
    var nk;
    try { nk = await api('vagabond.crm.nhom_khach', {}); } catch (er) { return toast(errMsg(er), 5000); }
    var lua = nk.bo_loc.map(function (b) { return { k: 'BL:' + b.name, icon: '🎯', nhan: b.ten, mo_ta: b.mo_ta + ' · ' + money(b.so) + ' khách' }; })
      .concat(nk.nhom.map(function (n) { return { k: 'NH:' + n.nhom, icon: '🧩', nhan: 'Nhóm ' + n.nhom, mo_ta: n.giai_thich + ' · ' + money(n.so) + ' khách' }; }));
    var x = await hoiChon('Chọn nhóm khách', 'Bộ lọc đã lưu ở trên, nhóm máy chia ở dưới.', lua, '');
    if (x && x.indexOf('BL:') === 0) {
      var b = nk.bo_loc.filter(function (y) { return 'BL:' + y.name === x; })[0];
      c.loc = b.loc; c.bo_loc = b.name; c.mo_ta_loc = b.ten;
    } else if (x) {
      c.loc = { nhom: [x.slice(3)] }; c.bo_loc = ''; c.mo_ta_loc = 'Nhóm ' + x.slice(3);
    }
    return crmCdVe();
  }
  if (e.target.closest('[data-crmcdluu]')) { crmCdDocO(); return crmCdLuu(); }
  /* Chữ gõ trong ô không vẽ lại màn, nên nút còn sáng: kiểm lại lúc bấm. */
  if (e.target.closest('[data-crmcdduyet], [data-crmcdchot]')) {
    crmCdDocO();
    if (crmCdChuaLuu()) { crmCdVe(); return toast(CRM_CD_CHUA_LUU, 5000); }
  }
  if (e.target.closest('[data-crmcdduyet]')) return crmCdGoi('vagabond.crm.duyet_kich_ban', 'Đã duyệt kịch bản gọi');
  if (e.target.closest('[data-crmcdchot]')) {
    var dc = c.dong_chay || {};
    var ok = await confirmSheet('Chốt danh sách?', 'Máy giữ ' + money(dc.doi_chung || 0) + ' khách làm đối chứng và chia ' + money(dc.nhan || 0) +
      ' khách cho ' + (dc.so_sales || 0) + ' Sales. Sau khi chốt, danh sách không đổi nữa.');
    if (ok) return crmCdGoi('vagabond.crm.chot_chien_dich', 'Đã chốt danh sách, Sales đã thấy khách của mình');
    return;
  }
  if (e.target.closest('[data-crmcdhq]')) { var n = c.name; return go(function () { scrCrmHieuQua(n); }); }
  if (e.target.closest('[data-crmcdkt]')) {
    if (await confirmSheet('Kết thúc chiến dịch?', 'Danh sách gọi không còn hiện cho Sales. Số liệu hiệu quả vẫn giữ.')) {
      busy(true);
      try { await api('vagabond.crm.ket_thuc_chien_dich', { name: c.name }); busy(false); toast('Đã kết thúc'); scrCrmCd(c.name); }
      catch (er) { busy(false); toast(errMsg(er), 5000); }
    }
  }
}

async function crmCdLuu() {
  var c = crmCd;
  busy(true);
  try {
    var d = await api('vagabond.crm.luu_chien_dich', { dat: JSON.stringify({
      name: c.name || '', ten: c.ten, loc: c.loc, bo_loc: c.bo_loc || '', kenh_goi: +c.kenh_goi ? 1 : 0, kenh_zalo: +c.kenh_zalo ? 1 : 0,
      ctkm: c.ctkm || '', han: c.han || '', kich_ban: c.kich_ban, noi_dung_zalo: c.noi_dung_zalo, ty_le_doi_chung: c.ty_le_doi_chung,
      mon: c.mon, sales: c.sales.map(function (s) { return s.nguoi; })
    }) });
    busy(false);
    d.mo_ta_loc = c.bo_loc ? (c.mo_ta_loc || d.mo_ta_loc) : d.mo_ta_loc;
    crmCd = d; crmCdGoc = crmCdDau(d);
    toast('Đã lưu nháp');
    if (d.name && d.trang_thai === 'Nháp' && +d.duoc_lap) {
      /* Thay nấc đang đứng (không đẩy thêm nấc): lùi ra vẫn về danh sách. */
      var ma = d.name; crmCdSan = d;
      return go(function () { return scrCrmCd(ma); }, true);
    }
    crmCdVe();
  } catch (e) { busy(false); toast(errMsg(e), 5000); }
}

async function crmCdGoi(method, xong) {
  busy(true);
  try {
    crmCd = await api(method, { name: crmCd.name }); crmCdGoc = crmCdDau(crmCd);
    busy(false); toast(xong, 3600); crmCdVe();
  } catch (e) { busy(false); toast(errMsg(e), 5000); }
}

/* ================================================================ hiệu quả */

var crmHqTt = '', crmHqTim = '';
async function scrCrmHqDs(them) {
  /* Ô Hiệu quả chiến dịch mở danh sách chiến dịch đã chốt. Codex PR #505
     vòng 3: có ô tìm và chip trạng thái (AGENTS: ô tìm nhanh ở đầu mọi danh
     sách), máy chủ lọc "đã chốt" nên nháp mới không đẩy chiến dịch cũ ra. */
  var tieuDe = 'Hiệu quả chiến dịch';
  if (!coQuyenCrm()) return frame(tieuDe, crmTrong('🔒', 'Phân hệ Khách hàng chỉ mở cho Sales, quản lý cửa hàng và Marketing.'));
  if (them === true) busy(true);
  else frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc chiến dịch...</div></div>');
  var d;
  try { d = await crmDsCd(them, { trang_thai: crmHqTt, tim: crmHqTim, da_chot: 1 }); }
  catch (e) { if (them === true) { busy(false); return toast(errMsg(e), 5000); } return frame(tieuDe, crmTrong('⚠️', h(errMsg(e)))); }
  if (them === true) busy(false);
  var dem = d.dem || {}, ds = crmCdDsDong;
  var cc = {
    ma: 'crmHq',
    chang: { ds: ['Đang chạy', 'Đã kết thúc'].map(function (t) { return { k: t, ten: t }; }), dem: dem, chon: crmHqTt, tatCa: 'Tất cả' },
    tim: { gt: crmHqTim, goiY: '🔎 Tìm tên hoặc mã chiến dịch' }
  };
  var coGi = +dem.tat_ca || crmHqTim || crmHqTt;
  var html = (coGi ? dsCongCu(cc) : '') + (ds.length ? '<div class="card">' + ds.map(function (c) {
    return '<div class="hub" data-crmhqmo="' + h(c.name) + '"><div class="hi">📊</div><div class="ht"><div class="h1">' + h(c.ten) + '</div>' +
      '<div class="h2">' + crmTagTt(c.trang_thai) + 'chốt ' + crmNgay(c.ngay_chot) + ' · ' + money(c.so_nhan) + ' khách được liên hệ, ' +
      money(c.so_doi_chung) + ' đối chứng</div></div><span class="fc" style="color:#c3c8d4;font-size:22px">&#8250;</span></div>';
  }).join('') + '</div>' : crmTrong('📊', coGi ? 'Không có chiến dịch nào khớp.' : 'Chưa có chiến dịch nào đã chốt danh sách.'));
  if (crmCdDsCon) html += '<button class="btn gh" data-crmhqthem="1" style="margin:0">Xem thêm chiến dịch cũ hơn</button>';
  var b = frame(tieuDe, html);
  dsCongCuNoi(b, cc, function (ho, v) {
    if (ho === 'chang') crmHqTt = v; else if (ho === 'tim') crmHqTim = v;
    scrCrmHqDs();
  });
  b.onclick = function (e) {
    if (e.target.closest('[data-crmhqthem]')) return scrCrmHqDs(true);
    var m = e.target.closest('[data-crmhqmo]');
    if (m) { var n = m.getAttribute('data-crmhqmo'); return go(function () { scrCrmHieuQua(n); }); }
  };
}

async function scrCrmHieuQua(name) {
  var tieuDe = 'Hiệu quả chiến dịch';
  frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đếm đơn của hai nhóm...</div></div>');
  var d;
  try { d = await api('vagabond.crm.hieu_qua_chien_dich', { name: name }); }
  catch (e) { return frame(tieuDe, crmTrong('⚠️', h(errMsg(e)))); }
  var a = d.nhan, b = d.doi_chung;
  var o = function (t, g) {
    return '<div style="flex:1;background:#fff;border-radius:16px;padding:14px;box-shadow:0 1px 3px rgba(20,25,40,.07)">' +
      '<div style="font-size:13px;color:#8a8f9c">' + t + '</div><div style="font-size:22px;font-weight:700;margin:4px 0">' + money(g.so_khach) + '</div>' +
      '<div style="font-size:13px;color:#8a8f9c">khách</div>' + crmKv('Có mua', String(g.ty_le_mua).replace('.', ',') + '%') +
      crmKv('Bình quân / khách', money(g.binh_quan) + ' đ') + '</div>';
  };
  var html = '<div class="card" style="padding:12px 14px"><div style="font-weight:700;font-size:16px">' + h(d.ten) + '</div>' +
    '<div data-crmhqmoc="1" style="font-size:13px;color:#8a8f9c">Đo từ ' + crmGioNgay(d.tu) + ' (lúc chốt) tới ' + crmGioNgay(d.den) + ', cùng mốc cho cả hai nhóm' +
    (d.dang_do ? ' · <b style="color:#93370d">đang đo, số còn tăng</b>' : '') + '</div></div>' +
    '<div data-crmhqhai="1" style="display:flex;gap:10px">' + o('Nhóm được liên hệ', a) + o('Nhóm đối chứng', b) + '</div>';
  html += '<div class="card" style="margin-top:12px;padding:12px 14px">';
  if (d.co_doi_chung) {
    html += '<div style="font-size:12px;color:#0B7C93;font-weight:600">CHIẾN DỊCH MANG VỀ THÊM</div>' +
      '<div data-crmhqthem="1" style="font-size:24px;font-weight:700;color:' + (d.mang_ve_them >= 0 ? '#05603a' : '#b42318') + '">≈ ' + money(d.mang_ve_them) + ' đ</div>' +
      '<div style="font-size:13px;color:#8a8f9c">(' + money(a.binh_quan) + ' − ' + money(b.binh_quan) + ') × ' + money(a.so_khach) + ' khách. So bình quân mỗi khách, không trừ thẳng hai tổng.</div>';
  } else {
    html += '<div style="font-size:13.5px;color:#475467">Chiến dịch này không giữ nhóm đối chứng (dưới 10 khách đủ điều kiện), nên chỉ có số đơn, chưa tách được phần chiến dịch mang về thêm.</div>';
  }
  html += crmKv('Đơn dùng mã ' + (d.ma_uu_dai || d.ctkm || ''), d.ctkm ? money(d.don_dung_ma) + ' đơn' : 'chưa gắn mã') +
    crmKv('Khách xin ngừng nhận tin', money(d.khach_tu_choi)) + '</div>';
  if ((d.theo_sales || []).length) {
    html += '<div class="sec">Theo từng Sales</div><div class="card" style="padding:4px 14px 10px">' + d.theo_sales.map(function (s) {
      return crmKv((s.ten || s.sales || '') + ' · ' + money(s.so_khach) + ' khách, đã gọi xong ' + money(s.da_xong), money(s.so_don) + ' đơn');
    }).join('') + '</div>';
  }
  frame(tieuDe, html);
}

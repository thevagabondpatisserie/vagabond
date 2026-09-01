/* =============== PHÂN HỆ HRM: KPI VÀ HOA HỒNG (anh Việt 01/09/2026) ======

Anh Việt chốt bảy điều ngày 01/09 và bảo làm bản demo ngay. Màn này gồm ba
cửa:

  scrKPI      danh sách phiếu của một kỳ, quản lý và giám đốc dùng
  scrKPICau   bảng chỉ tiêu, bậc hoa hồng, trần, và ô thử tính
  scrKPIToi   nhân viên xem điểm của chính mình

MỌI CON SỐ ĐỀU DO MÁY CHỦ TÍNH. Màn này không tự cộng điểm, không tự tính
hoa hồng, không tự đoán ai bấm được bước nào. Tính ở hai nơi là sớm muộn hai
nơi ra hai con số, mà con số này đi thẳng vào lương của người ta. */

var kpiKy = null;
var kpiBo = '';
var kpiTT = '';
var kpiMa = null;

function kpiMau(tt) {
  return {
    'Cho quan ly': '#b45309',
    'Cho ke toan': '#4338ca',
    'Cho giam doc': '#be123c',
    'Da duyet': '#0f766e',
    'Da day chi': '#0f766e',
    'Da huy': '#6b7280'
  }[tt] || '#6b7280';
}

function kpiChipLoai(x) {
  var m = { 'Xuất sắc': '#0f766e', 'Tốt': '#4338ca', 'Đạt': '#b45309', 'Chưa đạt': '#b3261e' }[x] || '#6b7280';
  return '<span style="background:' + m + ';color:#fff;border-radius:999px;padding:2px 9px;' +
    'font-size:11px;font-weight:800;white-space:nowrap">' + h(x || '') + '</span>';
}

/* ---------------- màn chính: danh sách phiếu của một kỳ ---------------- */
async function scrKPI() {
  frame('KPI và hoa hồng', '<div class="emp"><div class="e1">⏳</div><div>Đang cộng sổ kỳ...</div></div>');
  var kq;
  try { kq = await api('vagabond.kpi.danh_sach', { ky: kpiKy || '', bo: kpiBo, trang_thai: kpiTT }); }
  catch (e) {
    frame('KPI và hoa hồng', '<div class="emp"><div class="e1">🔒</div><div>' +
      h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  kpiKy = kq.ky;

  var html = '<div class="card" style="padding:13px 14px;background:#f0fdfa;border:1.5px solid #99f6e4">' +
    '<div style="font-size:12px;color:#0f766e">KỲ ' + h(kq.ky) + ' · ' +
    posNgayVn(kq.tu) + ' đến ' + posNgayVn(kq.den) + '</div>' +
    '<div style="font-size:26px;font-weight:800;color:#0f766e;line-height:1.3">' +
    money(kq.tong_hoa_hong) + ' đ</div>' +
    '<div style="font-size:12.5px;color:#0f766e">tổng hoa hồng của ' + kq.so_phieu + ' phiếu trong kỳ</div></div>';

  /* Bảng bậc có chỗ gợn thì nói ngay trên đầu màn, đừng để nó nằm im trong
     bảng cấu hình mà không ai mở. */
  if ((kq.canh_bao_bac || []).length) {
    html += '<div class="card" style="padding:11px 13px;border:1.5px solid #fcd34d;background:#fffbeb">' +
      '<div style="font-size:12.5px;color:#92400e;line-height:1.7">' +
      '<b>Bảng bậc hoa hồng có chỗ cần xem lại</b><br>' +
      kq.canh_bao_bac.map(function (x) { return '· ' + h(x); }).join('<br>') + '</div></div>';
  }

  /* Rổ chưa gán người bán. Đây là con số quan trọng nhất của bản demo này,
     nên nó nằm ngay trên đầu chứ không giấu trong chi tiết. */
  if (kq.chua_gan && kq.chua_gan.so_don) {
    html += '<div class="card" style="padding:11px 13px;border:1.5px solid #bfdbfe;background:#eff6ff">' +
      '<div style="font-size:12.5px;color:#1e40af;line-height:1.7">' +
      'Kỳ này có <b>' + money(kq.chua_gan.so_don) + '</b> hoá đơn (<b>' +
      money(kq.chua_gan.tien) + ' đ</b>) do máy dựng, chưa biết ai là người bán. ' +
      'Số này <b>chưa tính cho ai cả</b>. Mở một phiếu ở bước chờ quản lý rồi gán tay từng đơn.' +
      '</div></div>';
  }

  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
    posChipNut('data-kpibo=""', 'Mọi bộ phận', !kpiBo, false, '#4338ca') +
    (kq.bo || []).map(function (b) {
      return posChipNut('data-kpibo="' + h(b.k) + '"', h(b.ten), kpiBo === b.k, false, '#4338ca');
    }).join('')
  ) + '<div style="height:7px"></div>' + kmHangChip(
    posChipNut('data-kpitt=""', 'Mọi trạng thái', !kpiTT) +
    (kq.trang_thai || []).map(function (t) {
      /* Chip hiện CHỮ CÓ DẤU, còn giá trị gửi lên máy chủ vẫn là chữ lưu
         trong kho. Hai thứ khác nhau, đừng gộp làm một. */
      return posChipNut('data-kpitt="' + h(t) + '"',
        h((kq.nhan_trang_thai || {})[t] || t), kpiTT === t);
    }).join('')
  ) + '<div style="display:flex;gap:7px;margin-top:8px;flex-wrap:wrap">' +
    posChipNut('data-kpiky="-1"', '◀ Kỳ trước', false) +
    posChipNut('data-kpiky="1"', 'Kỳ sau ▶', false) +
    posChipNut('data-kpidung="1"', '➕ Dựng phiếu cho người', false, false, '#b45309') +
    '</div></div>';

  if (!(kq.ds || []).length) {
    html += '<div class="card"><div class="emp" style="padding:26px"><div class="e1">🗂️</div>' +
      '<div>Kỳ này chưa có phiếu nào. Bấm "Dựng phiếu cho người" để bắt đầu.</div></div></div>';
  } else {
    html += '<div class="sec">Phiếu trong kỳ · ' + kq.ds.length + '</div><div class="card">' +
      kq.ds.map(function (r) {
        return '<div class="row" data-kpimo="' + h(r.name) + '" style="padding:12px 14px;' +
          'border-bottom:1px solid #f2f4f7;cursor:pointer">' +
          '<div style="display:flex;gap:10px;align-items:baseline">' +
          '<div style="flex:1;min-width:0"><b style="font-size:14px">' + h(r.ten_nguoi || r.nguoi) + '</b>' +
          '<div style="font-size:11.5px;color:#98a2b3;margin-top:2px">' +
          '<span style="color:' + kpiMau(r.trang_thai) + ';font-weight:700">' +
          h((kq.nhan_trang_thai || {})[r.trang_thai] || r.trang_thai) + '</span>' +
          (r.con_thieu ? ' · còn ' + r.con_thieu + ' tiêu chí chưa chấm' : '') +
          (r.phieu_chi ? ' · ' + h(r.phieu_chi) : '') + '</div></div>' +
          '<div style="text-align:right">' +
          '<div style="font-size:15px;font-weight:800">' + money(r.hoa_hong) + ' đ</div>' +
          '<div style="font-size:11.5px;color:#6b7280">' + (r.diem_tong || 0) + ' điểm</div></div></div>' +
          '<div style="margin-top:7px;display:flex;gap:6px;align-items:center;flex-wrap:wrap">' +
          kpiChipLoai(r.xep_loai) +
          (r.bi_tran ? '<span style="font-size:11px;color:#b45309;font-weight:700">đã chạm trần</span>' : '') +
          (r.dong_bang ? '<span style="font-size:11px;color:#0f766e;font-weight:700">số đã đóng băng</span>' : '') +
          '<span style="font-size:11.5px;color:#98a2b3">doanh thu ' + money(r.doanh_thu) + ' đ</span>' +
          '</div></div>';
      }).join('') + '</div>';
  }

  html += '<div style="text-align:center;color:#a0a6b4;font-size:11.5px;padding:8px 14px 2px;line-height:1.6">' +
    'Máy đo được thì máy đo, người chỉ chấm cái máy không đo được. ' +
    'Giám đốc bấm duyệt là số liệu đóng băng, sau đó dữ liệu gốc đổi thì phiếu không đổi theo.</div>';

  var b = frame('KPI và hoa hồng', html, {
    footer: '<button class="btn gh" id="kpiCau" style="margin:0;width:100%">⚙️ Bảng chỉ tiêu và bậc hoa hồng</button>'
  });
  kpiNoi(b);
  var nc = document.getElementById('kpiCau');
  if (nc) nc.onclick = function () { go(scrKPICau, true); };
}

function kpiNoi(b) {
  b.onclick = function (e) {
    var t = e.target.closest('[data-kpibo]');
    if (t) { kpiBo = t.getAttribute('data-kpibo'); return go(scrKPI, true); }
    t = e.target.closest('[data-kpitt]');
    if (t) { kpiTT = t.getAttribute('data-kpitt'); return go(scrKPI, true); }
    t = e.target.closest('[data-kpiky]');
    if (t) { kpiKy = kpiDoiKy(kpiKy, parseInt(t.getAttribute('data-kpiky'), 10)); return go(scrKPI, true); }
    t = e.target.closest('[data-kpimo]');
    if (t) { kpiMa = t.getAttribute('data-kpimo'); return go(scrKPICt, true); }
    t = e.target.closest('[data-kpidung]');
    if (t) return kpiChonNguoi();
  };
}

/* Lùi hoặc tới một kỳ. Kỳ là chuỗi 2026-08, cộng trừ tháng chứ không cộng
   trừ 30 ngày: tháng 2 có 28 ngày và tháng 7 có 31. */
function kpiDoiKy(ky, huong) {
  var p = String(ky || '').split('-');
  var n = parseInt(p[0], 10), t = parseInt(p[1], 10) + huong;
  while (t < 1) { t += 12; n -= 1; }
  while (t > 12) { t -= 12; n += 1; }
  return n + '-' + (t < 10 ? '0' : '') + t;
}

async function kpiChonNguoi() {
  var ds;
  try { ds = (await api('vagabond.kpi.nguoi_dung', {})).ds || []; }
  catch (e) { return baoTin((e && e.message) || 'Không đọc được danh sách người dùng'); }
  if (!ds.length) return baoTin('Chưa có tài khoản nào để dựng phiếu.');
  var cf;
  try { cf = await api('vagabond.kpi.cai_dat', {}); } catch (e) { cf = null; }
  var bo = Object.keys((cf && cf.cf && cf.cf.bo) || { sales: 1 });
  sheet('Dựng phiếu KPI cho ai',
    ds.map(function (x) { return { value: x.ma, label: x.ten, phu: x.ma }; }), '',
    function (it) {
      sheet('Bộ tiêu chí nào',
        bo.map(function (k) {
          return { value: k, label: ((cf.cf.bo[k] || {}).ten) || k, phu: k };
        }), 'sales',
        async function (b2) {
          busy(true);
          try {
            var r = await api('vagabond.kpi.dung_phieu', { ky: kpiKy, nguoi: it.value, bo: b2.value });
            busy(false);
            kpiMa = r.ma;
            toast('Đã dựng phiếu ' + r.ma, 3500);
            go(scrKPICt, true);
          } catch (e2) { busy(false); baoTin((e2 && e2.message) || 'Không dựng được phiếu'); }
        }, true);
    }, true);
}

/* -------------------- chi tiết một phiếu: chấm và duyệt ---------------- */
async function scrKPICt() {
  frame('Phiếu KPI', '<div class="emp"><div class="e1">⏳</div><div>Đang mở...</div></div>');
  var d;
  try { d = await api('vagabond.kpi.chi_tiet', { ma: kpiMa }); }
  catch (e) {
    frame('Phiếu KPI', '<div class="emp"><div class="e1">⚠️</div><div>' +
      h((e && e.message) || 'Không mở được phiếu') + '</div></div>');
    return;
  }
  var suaDuoc = d.duoc_bam && d.trang_thai === 'Cho quan ly' && !d.dong_bang;

  var html = '<div class="card" style="padding:13px 14px;background:#f0fdfa;border:1.5px solid #99f6e4">' +
    '<div style="display:flex;gap:10px;align-items:baseline">' +
    '<div style="flex:1;min-width:0"><b style="font-size:16px">' + h(d.ten_nguoi || d.nguoi) + '</b>' +
    '<div style="font-size:12px;color:#0f766e">kỳ ' + h(d.ky) + ' · bước ' + d.buoc + '/' + d.tong_buoc +
    ' · ' + h(d.nhan_trang_thai) + '</div></div>' +
    '<div style="text-align:right"><div style="font-size:24px;font-weight:800;color:#0f766e">' +
    (d.diem_tong || 0) + '</div><div style="font-size:11px;color:#0f766e">điểm tổng</div></div></div>' +
    '<div style="margin-top:9px;display:flex;gap:7px;align-items:center;flex-wrap:wrap">' +
    kpiChipLoai(d.xep_loai) +
    '<span style="font-size:12px;color:#0f766e">hệ số ' + (d.he_so || 0) + '</span>' +
    (d.ky_truoc ? '<span style="font-size:12px;color:#6b7280">kỳ trước ' +
      (d.ky_truoc.diem_tong || 0) + ' điểm · ' + money(d.ky_truoc.hoa_hong) + ' đ</span>' : '') +
    '</div></div>';

  /* Khối tiền. Bày cả số thô lẫn số sau trần: người bị chạm trần phải thấy
     mình bị chạm trần chứ không phải chỉ thấy một con số thấp hơn mình nghĩ. */
  html += '<div class="card" style="padding:12px 14px">' +
    '<div style="display:flex;justify-content:space-between;font-size:13px;padding:4px 0">' +
    '<span style="color:#6b7280">Doanh thu tính hoa hồng</span><b>' + money(d.doanh_thu) + ' đ</b></div>' +
    (d.doanh_thu_gan_tay ? '<div style="display:flex;justify-content:space-between;font-size:12.5px;padding:4px 0">' +
      '<span style="color:#98a2b3">trong đó quản lý gán tay</span><span>' + money(d.doanh_thu_gan_tay) + ' đ</span></div>' : '') +
    '<div style="display:flex;justify-content:space-between;font-size:13px;padding:4px 0;border-top:1px dashed #e5e7eb">' +
    '<span style="color:#6b7280">Hoa hồng trước trần</span><span>' + money(d.hoa_hong_tho) + ' đ</span></div>' +
    '<div style="display:flex;justify-content:space-between;font-size:15px;padding:6px 0;border-top:1px solid #e5e7eb">' +
    '<b style="color:#0f766e">Hoa hồng phải trả</b><b style="color:#0f766e">' + money(d.hoa_hong) + ' đ</b></div>' +
    (d.bi_tran ? '<div style="font-size:11.5px;color:#b45309;line-height:1.6;margin-top:4px">' +
      'Đã chạm trần một kỳ. Phần vượt trần không được cộng dồn sang kỳ sau.</div>' : '') +
    '</div>';

  if (d.tra_lai_ly_do) {
    html += '<div class="card" style="padding:11px 13px;border:1.5px solid #fecaca;background:#fef2f2">' +
      '<div style="font-size:12.5px;color:#b3261e;line-height:1.65"><b>Phiếu đã bị trả lại</b><br>' +
      h(d.tra_lai_ly_do) + '</div></div>';
  }
  if (d.y_kien_nhan_vien) {
    html += '<div class="card" style="padding:11px 13px;border:1.5px solid #bfdbfe;background:#eff6ff">' +
      '<div style="font-size:12.5px;color:#1e40af;line-height:1.65"><b>Ý kiến của người được chấm</b><br>' +
      h(d.y_kien_nhan_vien) + '</div></div>';
  }

  html += '<div class="sec">Bảng tiêu chí</div><div class="card">' +
    (d.cac_dong || []).map(function (r) {
      var may = r.nguon === 'may';
      var o = may
        ? '<b style="font-size:14px">' + money(Math.round(r.dat || 0)) + ' ' + h(r.don_vi || '') + '</b>'
        : '<input class="tin" data-kpid="' + h(r.k) + '" inputmode="decimal" style="width:110px;text-align:right;' +
          'padding:7px 9px;font-size:14px" value="' + h(r.dat == null ? '' : r.dat) + '"' +
          (suaDuoc ? '' : ' disabled') + '>';
      return '<div style="padding:11px 14px;border-bottom:1px solid #f2f4f7">' +
        '<div style="display:flex;gap:10px;align-items:center">' +
        '<div style="flex:1;min-width:0"><b style="font-size:13.5px">' + h(r.ten) + '</b>' +
        '<div style="font-size:11.5px;color:#98a2b3;margin-top:2px">' +
        'trọng số ' + (r.trong_so || 0) + ' · mục tiêu ' + money(Math.round(r.muc_tieu || 0)) + ' ' + h(r.don_vi || '') +
        (r.nguoc ? ' · càng thấp càng tốt' : '') +
        ' · <span style="color:' + (may ? '#0f766e' : '#b45309') + ';font-weight:700">' +
        (may ? 'máy đo' : 'người chấm') + '</span></div></div>' +
        '<div style="text-align:right">' + o +
        '<div style="font-size:11.5px;color:#6b7280;margin-top:3px">' + (r.diem || 0) + ' điểm</div></div>' +
        '</div></div>';
    }).join('') + '</div>';

  if (suaDuoc) {
    html += '<div class="sec">Nhận xét của quản lý</div><div class="card" style="padding:12px 14px">' +
      '<textarea class="tin" id="kpiNx" rows="3" placeholder="Nhận xét để người được chấm đọc">' +
      h(d.ghi_chu_quan_ly || '') + '</textarea></div>';

    /* Rổ chưa gán người bán. Gán tay ghi vào PHIẾU, không sửa hoá đơn:
       nguyên tắc không sửa dữ liệu quá khứ anh Việt chốt 13/08/2026. */
    var cg = d.chua_gan || [];
    var daGan = d.da_gan || [];
    if (cg.length || daGan.length) {
      html += '<div class="sec">Đơn chưa gán người bán · ' + cg.length + '</div>' +
        '<div class="card" style="padding:11px 13px">' +
        '<div style="font-size:11.5px;color:#98a2b3;line-height:1.6;margin-bottom:9px">' +
        'Hệ chưa có trường người bán trên hoá đơn, nên đơn do máy dựng nằm ở đây. ' +
        'Tích đơn nào thuộc về ' + h(d.ten_nguoi || d.nguoi) + '. Một đơn chỉ gán được cho một người trong kỳ.</div>' +
        cg.slice(0, 60).map(function (x) {
          var co = daGan.indexOf(x.ma) >= 0;
          return '<label style="display:flex;gap:9px;align-items:center;padding:7px 0;border-top:1px solid #f2f4f7">' +
            '<input type="checkbox" data-kpigan="' + h(x.ma) + '"' + (co ? ' checked' : '') + '>' +
            '<span style="flex:1;min-width:0;font-size:12.5px">' + h(x.ma) +
            '<span style="color:#98a2b3"> · ' + h(x.diem) + (x.nguon ? ' · ' + h(x.nguon) : '') + '</span></span>' +
            '<b style="font-size:12.5px">' + money(x.tien) + ' đ</b></label>';
        }).join('') +
        (cg.length > 60 ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:8px">Còn ' +
          (cg.length - 60) + ' đơn nữa, gán xong lô này rồi mở lại.</div>' : '') +
        '</div>';
    }
  }

  if (d.duoc_bam && d.trang_thai !== 'Cho quan ly' && d.trang_thai !== 'Da duyet') {
    html += '<div style="padding:12px 0 2px">' +
      '<button class="btn gh" id="kpiTra" style="margin:0;width:100%;border-color:#fecaca;color:#b3261e">' +
      '↩︎ Trả phiếu về bước trước</button></div>';
  }

  var chan = '';
  if (d.duoc_bam) {
    var nhan = { 'Cho quan ly': '✅ Xác nhận, chuyển kế toán', 'Cho ke toan': '✅ Soát xong, chuyển giám đốc',
      'Cho giam doc': '✅ Duyệt và chốt kỳ', 'Da duyet': '💸 Đẩy sang đề nghị chi' }[d.trang_thai] || '';
    chan = '<div style="display:flex;gap:8px">' +
      (suaDuoc ? '<button class="btn gh" id="kpiLuu" style="margin:0;flex:1">💾 Lưu chấm</button>' : '') +
      '<button class="btn" id="kpiDuyet" style="margin:0;flex:2">' + nhan + '</button></div>';
  } else if (d.vi_sao_khong_bam) {
    chan = '<div style="font-size:12.5px;color:#6b7280;text-align:center;padding:6px 4px;line-height:1.6">' +
      h(d.vi_sao_khong_bam) + '</div>';
  }

  var b = frame('Phiếu KPI · ' + h(d.ky), html, { footer: chan });

  var luu = async function (roiDuyet) {
    var diem = {}, gan = [];
    b.querySelectorAll('[data-kpid]').forEach(function (n) {
      var v = (n.value || '').trim();
      if (v !== '') diem[n.getAttribute('data-kpid')] = soTien(v);
    });
    b.querySelectorAll('[data-kpigan]').forEach(function (n) {
      if (n.checked) gan.push(n.getAttribute('data-kpigan'));
    });
    var nx = document.getElementById('kpiNx');
    busy(true);
    try {
      await api('vagabond.kpi.cham', {
        ma: d.name,
        du_lieu: JSON.stringify({
          diem: diem, nhan_xet: nx ? nx.value : undefined, don_gan_tay: gan
        })
      });
      busy(false);
      if (!roiDuyet) { toast('Đã lưu chấm'); return go(scrKPICt, true); }
      return true;
    } catch (e) { busy(false); baoTin((e && e.message) || 'Không lưu được'); return false; }
  };

  var nl = document.getElementById('kpiLuu');
  if (nl) nl.onclick = function () { luu(0); };

  var nd = document.getElementById('kpiDuyet');
  if (nd) nd.onclick = async function () {
    if (d.trang_thai === 'Cho quan ly' && !(await luu(1))) return;
    if (d.trang_thai === 'Cho giam doc') {
      var ok = await confirmSheet('Duyệt và chốt kỳ',
        'Duyệt phiếu của ' + (d.ten_nguoi || d.nguoi) + ', hoa hồng ' + money(d.hoa_hong) + ' đ. ' +
        'Bấm xong số liệu ĐÓNG BĂNG: dữ liệu gốc sau này có đổi thì phiếu này không đổi theo.',
        'Đúng, duyệt và chốt', 1);
      if (!ok) return;
    }
    busy(true);
    try {
      if (d.trang_thai === 'Da duyet') {
        var r = await api('vagabond.kpi.day_chi', { ma: d.name });
        busy(false);
        baoTin(r.nhac || 'Đã đẩy sang đề nghị chi.', 'Xong');
      } else {
        await api('vagabond.kpi.duyet', { ma: d.name });
        busy(false);
        toast('Đã chuyển bước');
      }
      go(scrKPICt, true);
    } catch (e) { busy(false); baoTin((e && e.message) || 'Không bấm được'); }
  };

  /* Nút trả lại đặt CUỐI THÂN MÀN chứ không cạnh nút duyệt ở chân: hai nút
     cạnh nhau thì ngón cái trên điện thoại bấm nhầm, mà trả lại là bắt
     người khác làm lại việc. */
  var nt = document.getElementById('kpiTra');
  if (nt) {
    nt.onclick = async function () {
      var ly = await hoiChu('Trả phiếu về bước trước', 'Ghi lý do để người nhận biết sửa chỗ nào', '');
      if (!ly) return;
      busy(true);
      try { await api('vagabond.kpi.tra_lai', { ma: d.name, ly_do: ly }); busy(false); toast('Đã trả lại'); go(scrKPICt, true); }
      catch (e) { busy(false); baoTin((e && e.message) || 'Không trả lại được'); }
    };
  }
}

/* ------------- bảng chỉ tiêu, bậc hoa hồng và ô thử tính -------------- */
async function scrKPICau() {
  frame('Bảng chỉ tiêu', '<div class="emp"><div class="e1">⏳</div><div>Đang mở...</div></div>');
  var kq;
  try { kq = await api('vagabond.kpi.cai_dat', {}); }
  catch (e) {
    frame('Bảng chỉ tiêu', '<div class="emp"><div class="e1">🔒</div><div>' +
      h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  var cf = kq.cf || {};

  var html = '<div class="card" style="padding:12px 14px;font-size:13px;line-height:1.7;color:#374151">' +
    'Sàn <b>' + money(cf.san) + ' đ</b> · trần <b>' + money(cf.tran) + ' đ</b> một người một kỳ · ' +
    'chu kỳ <b>tháng</b>.<br>' +
    'Hợp đồng B2B và các nguồn voucher đối tác được bóc riêng, không tính vào doanh thu lẻ tại quầy.' +
    '</div>';

  /* Cảnh báo bậc là thứ quan trọng nhất trên màn này, nên nó nằm trên đầu
     chứ không nằm dưới bảng. Một bảng bậc có chỗ nhảy sẽ xui người ta dồn
     đơn qua tháng, và không ai nhìn ra bằng mắt thường. */
  if ((kq.canh_bao || []).length) {
    html += '<div class="card" style="padding:11px 13px;border:1.5px solid #fcd34d;background:#fffbeb">' +
      '<div style="font-size:12.5px;color:#92400e;line-height:1.75"><b>Máy soát bảng bậc và thấy:</b><br>' +
      kq.canh_bao.map(function (x) { return '· ' + h(x); }).join('<br>') + '</div></div>';
  }

  html += '<div class="sec">Bậc hoa hồng</div><div class="card">' +
    (cf.bac || []).map(function (b2, i) {
      var kieu = (b2.kieu || 'phan_vuot') === 'tu_moc'
        ? 'tính trên TOÀN BỘ phần vượt ' + money(b2.moc) + ' đ, thay cho các bậc dưới'
        : 'tính trên phần doanh thu nằm trong bậc này';
      return '<div style="padding:11px 14px;border-bottom:1px solid #f2f4f7">' +
        '<div style="display:flex;gap:10px;align-items:baseline">' +
        '<div style="flex:1;min-width:0"><b style="font-size:13.5px">Mốc ' + (i + 1) + ': ' +
        money(b2.tu) + ' đ' + (b2.den ? ' tới ' + money(b2.den) + ' đ' : ' trở lên') + '</b>' +
        '<div style="font-size:11.5px;color:#98a2b3;margin-top:2px">' + h(kieu) + '</div></div>' +
        '<b style="font-size:15px;color:#0f766e">' + b2.ty_le + '%</b></div></div>';
    }).join('') + '</div>';

  /* Ô thử tính. Cho người khai thấy TIỀN THẬT ở từng mức doanh thu, chứ
     không bắt họ nhẩm ba bậc trong đầu. Bậc nhảy tô đỏ. */
  var truoc = null;
  html += '<div class="sec">Thử tính</div><div class="card" style="overflow-x:auto">' +
    '<table style="width:100%;border-collapse:collapse;font-size:13px">' +
    '<thead><tr><th style="text-align:left;padding:9px 12px;background:#f8fafc;color:#6b7280;font-size:11.5px">Doanh thu</th>' +
    '<th style="text-align:right;padding:9px 12px;background:#f8fafc;color:#6b7280;font-size:11.5px">Hoa hồng</th>' +
    '<th style="text-align:right;padding:9px 12px;background:#f8fafc;color:#6b7280;font-size:11.5px">Tăng so với dòng trên</th></tr></thead><tbody>' +
    (kq.thu_tinh || []).map(function (r) {
      var tang = truoc == null ? null : r.tien - truoc;
      truoc = r.tien;
      var doNhay = tang != null && tang > 2000000;
      return '<tr style="border-top:1px solid #f2f4f7' + (doNhay ? ';background:#fef2f2' : '') + '">' +
        '<td style="padding:8px 12px">' + money(r.dt) + ' đ</td>' +
        '<td style="padding:8px 12px;text-align:right;font-weight:700">' + money(r.tien) + ' đ</td>' +
        '<td style="padding:8px 12px;text-align:right;color:' + (doNhay ? '#b3261e' : '#98a2b3') + '">' +
        (tang == null ? '' : (tang >= 0 ? '+' : '') + money(tang) + ' đ') + '</td></tr>';
    }).join('') + '</tbody></table></div>';

  html += '<div class="sec">Bộ tiêu chí theo vai</div>';
  Object.keys(cf.bo || {}).forEach(function (k) {
    var bo = cf.bo[k];
    var ts = (kq.tong_trong_so || {})[k] || 0;
    html += '<div class="card"><div style="padding:11px 14px;border-bottom:1px solid #f2f4f7;' +
      'display:flex;gap:10px;align-items:baseline">' +
      '<b style="flex:1;font-size:14px">' + h(bo.ten || k) + '</b>' +
      '<span style="font-size:11.5px;color:' + (Math.abs(ts - 100) < 0.01 ? '#0f766e' : '#b3261e') +
      ';font-weight:700">tổng trọng số ' + ts + '</span>' +
      (bo.co_hoa_hong ? '<span style="font-size:11px;background:#0f766e;color:#fff;border-radius:999px;' +
        'padding:2px 8px;font-weight:800">có hoa hồng</span>' : '') + '</div>' +
      (bo.tieu_chi || []).map(function (t) {
        return '<div style="padding:9px 14px;border-bottom:1px solid #f2f4f7;display:flex;gap:10px">' +
          '<div style="flex:1;min-width:0"><span style="font-size:13px">' + h(t.ten) + '</span>' +
          '<div style="font-size:11px;color:#98a2b3;margin-top:2px">mục tiêu ' +
          money(Math.round(t.muc_tieu || 0)) + ' ' + h(t.don_vi || '') +
          (t.nguoc ? ' · càng thấp càng tốt' : '') +
          ' · <span style="color:' + (t.nguon === 'may' ? '#0f766e' : '#b45309') + ';font-weight:700">' +
          (t.nguon === 'may' ? 'máy đo' : 'người chấm') + '</span></div></div>' +
          '<b style="font-size:13.5px">' + (t.trong_so || 0) + '</b></div>';
      }).join('') + '</div>';
  });

  /* Ô sửa. Anh Việt chốt 01/09/2026: sàn, trần và ba mốc phải đổi được theo
     từng thời điểm. Chỉ giám đốc thấy khối này; máy chủ vẫn chặn lại một lần
     nữa, ô này chỉ là để khỏi phải gọi người viết code mỗi lần đổi số. */
  if (kq.sua_duoc) {
    html += '<div class="sec">Sửa số</div><div class="card" style="padding:12px 14px">' +
      kpiORow('Sàn (dưới mức này không tính hoa hồng)', 'kpiSan', cf.san) +
      kpiORow('Trần một người một kỳ', 'kpiTran', cf.tran) +
      (cf.bac || []).map(function (b2, i) {
        return '<div style="border-top:1px solid #f2f4f7;padding-top:10px;margin-top:10px">' +
          '<b style="font-size:13px;color:#374151">Mốc ' + (i + 1) + '</b>' +
          kpiORow('Từ', 'kpiBacTu' + i, b2.tu) +
          kpiORow('Tới (để trống là trở lên)', 'kpiBacDen' + i, b2.den) +
          kpiORow('Tỷ lệ phần trăm', 'kpiBacTl' + i, b2.ty_le) +
          ((b2.kieu || 'phan_vuot') === 'tu_moc'
            ? kpiORow('Tính trên toàn bộ phần vượt', 'kpiBacMoc' + i, b2.moc) : '') +
          '</div>';
      }).join('') +
      '<button id="kpiLuuCau" class="btn" style="width:100%;margin-top:13px">Lưu bảng số</button>' +
      '<div style="font-size:11.5px;color:#98a2b3;margin-top:8px;line-height:1.6">' +
      'Lưu xong máy soát lại bảng bậc ngay và báo nếu có chỗ nhảy. ' +
      'Số mới chỉ áp cho phiếu dựng SAU khi lưu, phiếu đã chốt giữ nguyên.</div></div>';
  }

  html += '<div style="text-align:center;color:#a0a6b4;font-size:11.5px;padding:10px 14px 2px;line-height:1.6">' +
    (kq.sua_duoc
      ? 'Sửa bảng này thì chỉ ảnh hưởng kỳ SAU, không đụng kỳ đã chốt.'
      : 'Chỉ ban giám đốc sửa được bảng này.') + '</div>';

  var b = frame('Bảng chỉ tiêu và bậc hoa hồng', html);
  var nl = b && b.querySelector('#kpiLuuCau');
  if (nl) nl.onclick = function () { kpiLuuCau(cf); };
}

/* Một dòng nhãn cộng ô số. Để riêng ra vì khối sửa có tới mười mấy dòng
   giống hệt nhau, viết thẳng vào thì không ai soát nổi. */
function kpiORow(nhan, id, gt) {
  return '<div style="display:flex;gap:10px;align-items:center;margin-top:8px">' +
    '<div style="flex:1;min-width:0;font-size:12.5px;color:#6b7280">' + h(nhan) + '</div>' +
    '<input class="tin" id="' + id + '" type="number" step="any" value="' +
    (gt === null || gt === undefined ? '' : h(String(gt))) +
    '" style="width:150px;text-align:right"></div>';
}

/* Đọc ô số. Trống trả về null chứ không trả 0: "tới" của mốc cuối để trống
   nghĩa là trở lên, mà 0 thì nghĩa là bậc rỗng. Hai cái khác hẳn nhau. */
function kpiSo(id) {
  var o = document.getElementById(id);
  if (!o) return null;
  var v = String(o.value || '').trim();
  if (v === '') return null;
  var n = Number(v);
  return isNaN(n) ? null : n;
}

async function kpiLuuCau(cf) {
  var bac = (cf.bac || []).map(function (b2, i) {
    var r = {
      tu: kpiSo('kpiBacTu' + i),
      den: kpiSo('kpiBacDen' + i),
      ty_le: kpiSo('kpiBacTl' + i),
      kieu: b2.kieu || 'phan_vuot'
    };
    if (r.kieu === 'tu_moc') r.moc = kpiSo('kpiBacMoc' + i);
    return r;
  });
  for (var i = 0; i < bac.length; i++) {
    if (bac[i].tu === null || bac[i].ty_le === null) {
      return toast('Mốc ' + (i + 1) + ' còn thiếu số, chưa lưu được.');
    }
  }
  var san = kpiSo('kpiSan'), tran = kpiSo('kpiTran');
  if (san === null || tran === null) return toast('Sàn và trần không được để trống.');
  try {
    await api('vagabond.kpi.luu_cai_dat', { du_lieu: JSON.stringify({ san: san, tran: tran, bac: bac }) });
  } catch (e) {
    return toast((e && e.message) || 'Không lưu được');
  }
  toast('Đã lưu bảng số');
  go(scrKPICau, true);
}

/* ------------------- nhân viên xem điểm của chính mình ---------------- */
async function scrKPIToi() {
  frame('KPI của tôi', '<div class="emp"><div class="e1">⏳</div><div>Đang mở...</div></div>');
  var d;
  try { d = await api('vagabond.kpi.cua_toi', { ky: kpiKy || '' }); }
  catch (e) {
    frame('KPI của tôi', '<div class="emp"><div class="e1">⚠️</div><div>' +
      h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  if (!d.co) {
    frame('KPI của tôi', '<div class="card"><div class="emp" style="padding:28px">' +
      '<div class="e1">🗂️</div><div>Kỳ ' + h(d.ky) + ' chưa có phiếu KPI cho anh chị.<br>' +
      'Quản lý dựng phiếu xong thì anh chị sẽ thấy ở đây.</div></div></div>');
    return;
  }

  var html = '<div class="card" style="padding:14px;background:#f0fdfa;border:1.5px solid #99f6e4">' +
    '<div style="font-size:12px;color:#0f766e">KỲ ' + h(d.ky) + ' · ' + h(d.nhan_trang_thai) + '</div>' +
    '<div style="font-size:32px;font-weight:800;color:#0f766e;line-height:1.25">' + (d.diem_tong || 0) + '</div>' +
    '<div style="margin-top:6px;display:flex;gap:8px;align-items:center;flex-wrap:wrap">' +
    kpiChipLoai(d.xep_loai) +
    (d.hoa_hong ? '<b style="font-size:15px;color:#0f766e">' + money(d.hoa_hong) + ' đ hoa hồng</b>' : '') +
    '</div>' +
    (d.ky_truoc ? '<div style="font-size:12.5px;color:#0f766e;margin-top:7px;padding-top:7px;' +
      'border-top:1px dashed #99f6e4">Kỳ trước: ' + (d.ky_truoc.diem_tong || 0) + ' điểm · ' +
      h(d.ky_truoc.xep_loai || '') + ' · ' + money(d.ky_truoc.hoa_hong) + ' đ</div>' : '') +
    '</div>';

  html += '<div class="sec">Từng tiêu chí</div><div class="card">' +
    (d.cac_dong || []).map(function (r) {
      var pc = Math.max(2, Math.min(100, Math.round(r.diem || 0)));
      return '<div style="padding:11px 14px;border-bottom:1px solid #f2f4f7">' +
        '<div style="display:flex;gap:10px;font-size:13px">' +
        '<span style="flex:1;min-width:0">' + h(r.ten) + '</span>' +
        '<b>' + (r.diem || 0) + '</b></div>' +
        '<div style="height:8px;border-radius:99px;background:#eef0f5;overflow:hidden;margin-top:5px">' +
        '<div style="height:100%;width:' + pc + '%;background:' +
        ((r.diem || 0) >= 100 ? '#0f766e' : ((r.diem || 0) >= 70 ? '#50DBF2' : '#f59e0b')) + '"></div></div>' +
        '<div style="font-size:11px;color:#98a2b3;margin-top:3px">đạt ' +
        money(Math.round(r.dat || 0)) + ' ' + h(r.don_vi || '') + ' trên mục tiêu ' +
        money(Math.round(r.muc_tieu || 0)) + ' ' + h(r.don_vi || '') +
        (r.ghi_chu ? ' · ' + h(r.ghi_chu) : '') + '</div></div>';
    }).join('') + '</div>';

  if (d.ghi_chu_quan_ly) {
    html += '<div class="sec">Nhận xét của quản lý</div>' +
      '<div class="card" style="padding:12px 14px;font-size:13px;line-height:1.7">' +
      h(d.ghi_chu_quan_ly) + '</div>';
  }

  /* Cửa nói lại. Không có cửa này thì mỗi kỳ là một lần đến bàn giám đốc
     cãi, và cái đến bàn thì không lưu được ở đâu. */
  html += '<div class="sec">Anh chị thấy chưa đúng chỗ nào</div>' +
    '<div class="card" style="padding:12px 14px">' +
    '<textarea class="tin" id="kpiYk" rows="3" placeholder="Ghi vào đây, quản lý và giám đốc đọc được ngay trên phiếu"' +
    (d.dong_bang ? ' disabled' : '') + '>' + h(d.y_kien_nhan_vien || '') + '</textarea>' +
    (d.dong_bang
      ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px;line-height:1.6">' +
        'Phiếu đã chốt nên ô này khoá lại. Anh chị trao đổi trực tiếp với quản lý nhé.</div>'
      : '<button class="btn gh" id="kpiGuiYk" style="margin:9px 0 0;width:100%">Gửi ý kiến</button>') +
    '</div>';

  var b = frame('KPI của tôi', html);
  var ng = document.getElementById('kpiGuiYk');
  if (ng) ng.onclick = async function () {
    busy(true);
    try {
      await api('vagabond.kpi.y_kien', { ma: d.name, noi_dung: document.getElementById('kpiYk').value });
      busy(false);
      toast('Đã gửi ý kiến, quản lý sẽ thấy ngay trên phiếu', 4000);
    } catch (e) { busy(false); baoTin((e && e.message) || 'Không gửi được'); }
  };
}

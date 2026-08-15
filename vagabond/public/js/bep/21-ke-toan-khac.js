/* ================= TAI SAN CO DINH VA CONG CU DUNG CU =================
   Anh Viet 14/08/2026: "chi Dung ke toan cung mong muon co the thao tac
   hach toan, dinh khoan, phan bo tai san (anh khong ranh nghiep vu nay)".

   Do that truoc khi lam: bang tai khoan da co san 2111, 2141, 242, 153 va
   ba tai khoan chi phi khau hao 6274 / 6414 / 6424. Nhung KHONG mot tai
   san nao duoc khai. Nen viec thieu khong phai bang tai khoan ma la du
   lieu - va cai kho khong phai "bam o dau" ma la "khai lam sao cho dung".

   Vi vay man nay hoi dung nam thu ke toan biet: ten, nhom, ngay dua vao
   su dung, nguyen gia, so nam. Con Item, Location, Asset Category - ba
   khai niem cua ERPNext - may tu dung o duoi, chi Dung khong thay. */
var tsChip = null, tsTim = '', tsNhom = null;

async function scrTaiSan() {
  frame('Tài sản', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc sổ tài sản...</div></div>');
  var kq;
  var ts = {};
  if (tsChip) ts.chip = tsChip;
  if (tsTim) ts.tu_khoa = tsTim;
  if (tsNhom) ts.nhom = tsNhom;
  try { kq = await api('vagabond.tai_san.danh_sach', ts); }
  catch (e) { frame('Tài sản', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var rows = kq.rows || [], dem = kq.dem || {};

  var html = '';
  if (kq.chua_cai_dat) {
    html += '<div class="card" style="padding:14px;background:#fffbeb;border:1.5px solid #fde68a">' +
      '<div style="font-size:14px;font-weight:800;color:#92400e">Chưa lập nhóm tài sản</div>' +
      '<div style="font-size:13px;line-height:1.65;color:#92400e;margin-top:6px">' +
      'Trước khi khai tài sản đầu tiên, cần lập sáu nhóm tài sản để máy biết ghi sổ vào tài khoản nào. ' +
      'Bấm nút dưới, máy lập một lần rồi thôi.</div>' +
      (kq.sua_duoc ? '<button class="btn" id="tsCaiDat" style="margin-top:12px">🧱 Lập sáu nhóm tài sản</button>' : '') +
      '</div>';
  }

  var ccdc = (kq.nhom || []).filter(function (n) { return n.k === 'ccdc'; })[0];
  if (!kq.chua_cai_dat && ccdc && !ccdc.co_roi && kq.sua_duoc) {
    html += '<div class="card" style="padding:14px;background:#fffbeb;border:1.5px solid #fde68a">' +
      '<div style="font-size:14px;font-weight:800;color:#92400e">Nhóm công cụ dụng cụ chưa lập được</div>' +
      '<div style="font-size:13px;line-height:1.65;color:#92400e;margin-top:6px">' +
      'Năm nhóm tài sản cố định đã sẵn sàng. Riêng nhóm công cụ dụng cụ ghi vào tài khoản 242, ' +
      'mà ERPNext đòi tài khoản này phải được đánh dấu là tài khoản giữ giá trị. ' +
      'Đây là sửa bảng hệ thống tài khoản nên máy không tự làm.</div>' +
      '<button class="btn" id="tsMoKhoa" style="margin-top:12px">🔓 Xem và mở khoá</button></div>';
  }
  html += '<div class="card" style="padding:12px 14px"><input class="tin" id="tsQ" placeholder="Tìm theo tên tài sản hoặc mã" value="' + h(tsTim) + '" style="margin:0"></div>';

  var CHIP = [
    ['', '📚 Tất cả', kq.tat_ca],
    ['dang_dung', '✅ Đang dùng', dem.dang_dung],
    ['nhap', '📝 Còn nháp', dem.nhap],
    ['het_khau_hao', '🏁 Hết khấu hao', dem.het_khau_hao],
    ['da_thanh_ly', '🚫 Đã thanh lý', dem.da_thanh_ly]
  ];
  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(CHIP.map(function (x) {
    return posChipNut('data-tsc="' + x[0] + '"', x[1] + ' · ' + (x[2] || 0), (tsChip || '') === x[0]);
  }).join('')) + '</div>';

  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
    [['', '🏷 Mọi nhóm']].concat((kq.nhom || []).map(function (n) { return [n.ten, n.icon + ' ' + n.ten]; })).map(function (x) {
      return posChipNut('data-tsn="' + h(x[0]) + '"', h(x[1]), (tsNhom || '') === x[0]);
    }).join('')) + '</div>';

  html += '<div class="card" style="padding:12px 14px;background:#f0fdfa;border:1.5px solid #99f6e4">' +
    '<div style="font-size:11.5px;color:#0f766e;font-weight:800">THEO BỘ LỌC</div>' +
    '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:5px">' +
    '<span style="font-size:13.5px;color:#374151">' + rows.length + ' tài sản · nguyên giá ' + money(kq.tong_nguyen_gia) + ' đ</span>' +
    '<b style="font-size:19px;color:#0f766e">còn lại ' + money(kq.tong_con_lai) + ' đ</b></div></div>';

  if (kq.sua_duoc) {
    html += '<div style="display:flex;gap:8px;margin-bottom:10px">' +
      '<button class="btn" id="tsKhai" style="flex:2;margin:0">➕ Khai tài sản</button>' +
      '<button class="btn gh" id="tsKh" style="flex:1;margin:0">🧮 Khấu hao</button></div>';
  }

  html += '<div class="sec">Danh sách · bấm để xem lịch khấu hao</div><div class="card">';
  if (!rows.length) html += '<div class="emp" style="padding:24px"><div class="e1">🏗️</div><div>Chưa có tài sản nào khớp bộ lọc.</div></div>';
  rows.forEach(function (r) {
    var pct = r.gross_purchase_amount ? Math.round(r.da_khau_hao * 100 / r.gross_purchase_amount) : 0;
    html += '<div class="hub" data-ts="' + h(r.name) + '">' +
      '<div class="hub-i" style="background:#f5f7fa">' + r.icon + '</div>' +
      '<div class="hub-t"><div class="t1">' + h(r.asset_name) + '</div>' +
      '<div class="t2">' + h(r.asset_category || '') + (r.bo_phan ? ' · ' + h(r.bo_phan) : '') + (r.docstatus === 0 ? ' · <span style="color:#b45309">còn nháp</span>' : '') + '</div>' +
      '<div class="t2">Nguyên giá ' + money(r.gross_purchase_amount) + ' đ · đã ' + (r.la_ccdc ? 'phân bổ ' : 'khấu hao ') + pct + '%</div>' +
      '</div><b style="white-space:nowrap;color:#0f766e">' + money(r.con_lai) + ' đ</b></div>';
  });
  html += '</div>';

  var b = frame('Tài sản', html, {});
  var q = document.getElementById('tsQ');
  if (q) q.onchange = function () { tsTim = q.value.trim(); go(scrTaiSan, true); };
  Array.prototype.forEach.call(document.querySelectorAll('[data-tsc]'), function (el) {
    el.onclick = function () { tsChip = el.getAttribute('data-tsc') || null; go(scrTaiSan, true); };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-tsn]'), function (el) {
    el.onclick = function () { tsNhom = el.getAttribute('data-tsn') || null; go(scrTaiSan, true); };
  });
  b.addEventListener('click', function (e) {
    var r = e.target.closest('[data-ts]'); if (!r) return;
    go(function () { scrTaiSanXem(r.getAttribute('data-ts')); });
  });
  var mk = document.getElementById('tsMoKhoa');
  if (mk) mk.onclick = async function () {
    var t;
    try { t = await api('vagabond.tai_san.mo_khoa_ccdc', { that_su: 0 }); } catch (er) { return baoTin((er && er.message) || 'Không đọc được'); }
    if (!await hoiCo('Mở khoá nhóm công cụ dụng cụ',
      'Nhóm công cụ dụng cụ ghi giá trị vào tài khoản ' + t.tk + '. ERPNext đòi tài khoản này phải được đánh dấu là tài khoản giữ giá trị thì mới cho phân bổ dần.\n\n' +
      'Loại hiện tại: ' + t.loai_hien_tai + '\nSẽ đổi thành: Fixed Asset\nSố bút toán đang nằm ở tài khoản này: ' + t.so_but_toan + '\n\n' +
      'Đây là sửa bảng hệ thống tài khoản. Chỉ đổi một trường loại tài khoản, không đổi số hiệu, không đổi tên, không đụng số dư. Chị Dung nên xem trước khi bấm.',
      'Mở khoá')) return;
    busy(true);
    try { var kq = await api('vagabond.tai_san.mo_khoa_ccdc', { that_su: 1 }); busy(false); toast(kq.loi_nhan, 5000); }
    catch (er) { busy(false); return baoTin((er && er.message) || 'Mở khoá lỗi'); }
    go(scrTaiSan, true);
  };
  var cd = document.getElementById('tsCaiDat');
  if (cd) cd.onclick = async function () {
    var thu;
    try { thu = await api('vagabond.tai_san.cai_dat', { that_su: 0 }); } catch (er) { return baoTin((er && er.message) || 'Không đọc được'); }
    var mo = (thu.rows || []).map(function (x) { return x.ten + ': ' + x.ket_qua; }).join('\n');
    if (!await hoiCo('Lập nhóm tài sản', mo + '\n\nLập luôn?', 'Lập')) return;
    busy(true);
    try { var kq2 = await api('vagabond.tai_san.cai_dat', { that_su: 1 }); busy(false); toast('Xong ' + (kq2.rows || []).length + ' nhóm', 4000); }
    catch (er) { busy(false); return baoTin((er && er.message) || 'Lập nhóm lỗi'); }
    go(scrTaiSan, true);
  };
  var kh = document.getElementById('tsKh');
  if (kh) kh.onclick = function () { go(scrKhauHao); };
  var kt = document.getElementById('tsKhai');
  if (kt) kt.onclick = function () { tsKhai(kq.nhom || []); };
}


async function scrTaiSanXem(ma) {
  frame('Tài sản', '<div class="emp"><div class="e1">⏳</div><div>Đang mở...</div></div>');
  var d;
  try { d = await api('vagabond.tai_san.chi_tiet', { ma: ma }); }
  catch (e) { frame('Tài sản', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>'); return; }

  function o(nhan, giaTri) {
    if (!giaTri && giaTri !== 0) return '';
    return '<div style="display:flex;justify-content:space-between;gap:12px;padding:9px 0;border-bottom:1px solid #f1f3f6">' +
      '<span style="font-size:13px;color:#6b7280">' + h(nhan) + '</span>' +
      '<b style="font-size:13.5px;text-align:right">' + h(String(giaTri)) + '</b></div>';
  }

  var html = '<div class="card" style="padding:14px">' +
    '<div style="font-size:19px;font-weight:800">' + d.icon + ' ' + h(d.ten) + '</div>' +
    '<div style="font-size:13px;color:#6b7280;margin-top:2px">' + h(d.ma) + ' · ' + h(d.nhom || '') + '</div>' +
    '<div style="margin-top:10px"><span class="vxtag ' + (d.nhap ? 'c' : 'd') + '">' + h(d.trang_thai) + '</span>' +
    (d.bo_phan ? ' <span class="vxtag c2">' + h(d.bo_phan) + '</span>' : '') + '</div></div>';

  html += '<div class="card" style="padding:4px 14px 10px">' +
    o('Nguyên giá', money(d.nguyen_gia) + ' đ') +
    o(d.la_ccdc ? 'Đã phân bổ' : 'Đã khấu hao', money(d.da_khau_hao) + ' đ') +
    o('Giá trị còn lại', money(d.con_lai) + ' đ') +
    o('Ngày đưa vào sử dụng', d.ngay_dung ? hsNgayVn(String(d.ngay_dung).slice(0, 10)) : '') +
    o('Nơi để', d.noi_de) + o('Người giữ', d.nguoi_giu) +
    o('Số kỳ', d.so_ky_da_chay + ' / ' + d.so_ky + ' kỳ đã ghi sổ') +
    '</div>';

  var lich = (d.lich || []);
  var chuaGhi = lich.filter(function (x) { return !x.da_ghi; });
  html += '<div class="sec">Lịch ' + (d.la_ccdc ? 'phân bổ' : 'khấu hao') + ' · ' + lich.length + ' kỳ</div><div class="card">';
  if (!lich.length) html += '<div class="emp" style="padding:20px"><div class="e1">🧮</div><div>Chưa có lịch. Tài sản còn nháp thì ghi sổ trước.</div></div>';
  var batDau = Math.max(0, d.so_ky_da_chay - 2);
  lich.slice(batDau, batDau + 24).forEach(function (x) {
    html += '<div class="hub" style="cursor:default">' +
      '<div class="hub-i" style="background:' + (x.da_ghi ? '#f0fdf4' : '#f9fafb') + '">' + (x.da_ghi ? '✅' : '⏳') + '</div>' +
      '<div class="hub-t"><div class="t1" style="font-size:14.5px">' + hsNgayVn(String(x.ngay).slice(0, 10)) + '</div>' +
      '<div class="t2">Luỹ kế ' + money(x.luy_ke) + ' đ' + (x.but_toan ? ' · ' + h(x.but_toan) : '') + '</div></div>' +
      '<b style="white-space:nowrap">' + money(x.so_tien) + ' đ</b></div>';
  });
  if (lich.length > batDau + 24) html += '<div style="padding:10px 14px;font-size:12.5px;color:#6b7280">Còn ' + (lich.length - batDau - 24) + ' kỳ nữa phía sau.</div>';
  html += '</div>';

  if (chuaGhi.length) {
    html += '<div style="font-size:12.5px;color:#6b7280;padding:10px 4px;line-height:1.6">' +
      chuaGhi.length + ' kỳ chưa ghi sổ. Vào Tài sản, bấm Khấu hao để chạy chung cho mọi tài sản.</div>';
  }

  if (d.nhap && d.sua_duoc) html += '<button class="btn" id="tsGhi">📗 Ghi sổ tài sản này</button>';

  frame('Tài sản', html, { back: function () { go(scrTaiSan); } });
  var g = document.getElementById('tsGhi');
  if (g) g.onclick = async function () {
    if (!await hoiCo('Ghi sổ tài sản', 'Ghi sổ ' + d.ten + '? Máy sẽ dựng lịch khấu hao và từ đó khoá nguyên giá.', 'Ghi sổ')) return;
    busy(true);
    try { var kq = await api('vagabond.tai_san.ghi_so', { ma: d.ma }); busy(false); toast(kq.loi_nhan, 4000); }
    catch (er) { busy(false); return baoTin((er && er.message) || 'Ghi sổ lỗi'); }
    go(function () { scrTaiSanXem(d.ma); }, true);
  };
}


/* Khai tai san: hoi dung nam thu, khong hoi Item hay Location. */
async function tsKhai(dsNhom) {
  if (!dsNhom || !dsNhom.length) return baoTin('Chưa lập nhóm tài sản.');
  var chuaCo = dsNhom.filter(function (n) { return !n.co_roi; });
  if (chuaCo.length === dsNhom.length) return baoTin('Chưa lập nhóm tài sản. Bấm nút Lập sáu nhóm tài sản trước.');

  var nhom = await hoiChon('Khai tài sản', 'Tài sản này thuộc nhóm nào? Nhóm quyết định số năm khấu hao và tài khoản chi phí.',
    dsNhom.filter(function (n) { return n.co_roi; }).map(function (n) {
      return { k: n.k, nhan: n.ten + ' · ' + n.nam + ' năm', mo_ta: n.mo_ta, icon: n.icon };
    }), null);
  if (!nhom) return;
  var n = dsNhom.filter(function (x) { return x.k === nhom; })[0] || {};

  var ten = await hoiChu('Khai tài sản', 'Tên tài sản, ghi như trên hoá đơn mua để sau này còn đối chiếu.', '', { bat_buoc: 1, goi_y: 'Lò nướng Unox XB695' });
  if (!ten) return;
  var gia = await hoiSo('Khai tài sản', 'Nguyên giá (chưa gồm thuế GTGT được khấu trừ).', '');
  if (!gia) return;
  var ngay = await hoiNgay(today());
  if (!ngay) return;
  var nam = await hoiSo('Khai tài sản', 'Số năm sử dụng. Nhóm ' + h(n.ten || '') + ' mặc định ' + (n.nam || '') + ' năm, sửa được.', String(n.nam || 5));
  if (!nam) return;
  var da = await hoiSo('Khai tài sản', 'Nếu tài sản mua từ trước và đã trích khấu hao rồi thì điền số đã trích. Chưa trích lần nào thì để 0.', '0');
  if (da === null) return;
  var noi = await hoiChu('Khai tài sản', 'Để ở đâu? Bỏ trống thì máy ghi The Vagabond Pâtisserie.', '', { goi_y: 'Bếp 307' });
  if (noi === null) return;

  if (!await hoiCo('Khai tài sản',
    ten + '\n' + (n.ten || '') + '\nNguyên giá ' + money(gia) + ' đ\nSử dụng từ ' + hsNgayVn(ngay) + '\nKhấu hao ' + nam + ' năm (' + (nam * 12) + ' tháng)' +
    (da ? '\nĐã trích trước ' + money(da) + ' đ' : '') +
    '\n\nMáy sẽ ghi sổ luôn và dựng lịch khấu hao ' + (nam * 12) + ' kỳ.', 'Khai và ghi sổ')) return;

  busy(true);
  try {
    var kq = await api('vagabond.tai_san.khai', {
      ten: ten, nhom: nhom, nguyen_gia: gia, ngay_dung: ngay,
      so_nam: nam, da_khau_hao: da || 0, noi_de: noi || '', ghi_so: 1
    });
    busy(false); toast(kq.loi_nhan, 5000);
    go(function () { scrTaiSanXem(kq.ma); }, true);
  } catch (er) { busy(false); baoTin((er && er.message) || 'Khai tài sản lỗi'); }
}


async function scrKhauHao() {
  frame('Khấu hao', '<div class="emp"><div class="e1">⏳</div><div>Đang soát kỳ tới hạn...</div></div>');
  var d;
  try { d = await api('vagabond.tai_san.xem_truoc_khau_hao', {}); }
  catch (e) { frame('Khấu hao', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }

  var html = '<div class="card" style="padding:14px;background:' + (d.so_ky ? '#fffbeb;border:1.5px solid #fde68a' : '#f0fdf4;border:1.5px solid #bbf7d0') + '">' +
    '<div style="font-size:11.5px;font-weight:800;color:' + (d.so_ky ? '#92400e' : '#166534') + '">TỚI HẠN TÍNH ĐẾN HÔM NAY</div>' +
    '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:6px">' +
    '<span style="font-size:14px;color:#374151">' + d.so_ky + ' kỳ chưa ghi sổ</span>' +
    '<b style="font-size:20px;color:' + (d.so_ky ? '#92400e' : '#166534') + '">' + money(d.tong) + ' đ</b></div></div>';

  if ((d.theo_bo_phan || []).length) {
    html += '<div class="sec">Chia theo bộ phận</div><div class="card" style="padding:4px 14px 10px">' +
      (d.theo_bo_phan || []).map(function (x) {
        return '<div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid #f1f3f6">' +
          '<span style="font-size:13.5px;color:#374151">' + h(x.bo_phan) + '</span>' +
          '<b style="font-size:13.5px">' + money(x.so_tien) + ' đ</b></div>';
      }).join('') + '</div>';
  }

  if ((d.rows || []).length) {
    html += '<div class="sec">Từng kỳ</div><div class="card">';
    (d.rows || []).slice(0, 60).forEach(function (r) {
      html += '<div class="hub" style="cursor:default"><div class="hub-i" style="background:#f9fafb">⏳</div>' +
        '<div class="hub-t"><div class="t1" style="font-size:14.5px">' + h(r.ten) + '</div>' +
        '<div class="t2">' + hsNgayVn(String(r.ngay).slice(0, 10)) + ' · ' + h(r.nhom || '') + '</div></div>' +
        '<b style="white-space:nowrap">' + money(r.so_tien) + ' đ</b></div>';
    });
    if (d.con_nua) html += '<div style="padding:10px 14px;font-size:12.5px;color:#6b7280">Còn ' + d.con_nua + ' kỳ nữa.</div>';
    html += '</div>';
  } else {
    html += '<div class="card"><div class="emp" style="padding:24px"><div class="e1">✅</div><div>Không có kỳ nào tới hạn. Khấu hao đã ghi sổ đủ.</div></div></div>';
  }

  if (d.so_ky && d.sua_duoc) html += '<button class="btn" id="khChay">🧮 Ghi sổ khấu hao ' + d.so_ky + ' kỳ</button>';
  html += '<div style="font-size:12px;color:#98a2b3;padding:12px 4px;line-height:1.6">' +
    'Ghi sổ khấu hao sinh bút toán Nợ tài khoản chi phí của bộ phận, Có 214 hao mòn (hoặc Có 242 với công cụ dụng cụ). ' +
    'Bút toán đã ghi thì phải huỷ trong sổ chứ không xoá được.</div>';

  frame('Khấu hao', html, { back: function () { go(scrTaiSan); } });
  var c = document.getElementById('khChay');
  if (c) c.onclick = async function () {
    if (!await hoiCo('Ghi sổ khấu hao', 'Ghi sổ ' + d.so_ky + ' kỳ, tổng ' + money(d.tong) + ' đ?\n\nBút toán vào sổ rồi thì chỉ huỷ được chứ không sửa.', 'Ghi sổ')) return;
    busy(true);
    try { var kq = await api('vagabond.tai_san.chay_khau_hao', {}); busy(false); toast(kq.loi_nhan, 6000); }
    catch (er) { busy(false); return baoTin((er && er.message) || 'Chạy khấu hao lỗi'); }
    go(scrKhauHao, true);
  };
}


/* ================= HACH TOAN TAY VA DINH KHOAN MAU =================
   Do that: cong ty co 2.888 but toan so cai ma chi DUNG HAI but toan go
   tay. Nghia la moi thu trong so deu do may sinh tu hoa don va phieu kho;
   nhung viec ke toan phai tu go - trich luong, trich bao hiem, phan bo
   242, ket chuyen thue - chua tung duoc ghi lan nao.

   Man nay khong bat chi Dung nho so hieu tai khoan doi ung. Chon dinh
   khoan mau theo viec that, may bay san cap No va Co, chi dien so tien. */
var btChip = null, btTim = '', btDong = [], btMau = null, btNgay = null, btDienGiai = '';

async function scrButToan() {
  frame('Bút toán', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc...</div></div>');
  var kq;
  var ts = { so_ngay: 60 };
  if (btChip) ts.chip = btChip;
  if (btTim) ts.tu_khoa = btTim;
  try { kq = await api('vagabond.but_toan.danh_sach', ts); }
  catch (e) { frame('Bút toán', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var rows = kq.rows || [], dem = kq.dem || {};

  var html = '<div class="card" style="padding:12px 14px"><input class="tin" id="btQ" placeholder="Tìm theo diễn giải hoặc mã bút toán" value="' + h(btTim) + '" style="margin:0"></div>';

  var CHIP = [
    ['', '📚 Tất cả', kq.tat_ca],
    ['nhap', '📝 Còn nháp', dem.nhap],
    ['da_ghi', '📗 Đã ghi sổ', dem.da_ghi],
    ['da_huy', '🚫 Đã huỷ', dem.da_huy]
  ];
  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(CHIP.map(function (x) {
    return posChipNut('data-btc="' + x[0] + '"', x[1] + ' · ' + (x[2] || 0), (btChip || '') === x[0]);
  }).join('')) + '</div>';

  if (kq.lap_duoc) html += '<button class="btn" id="btMoi">✍️ Lập bút toán</button>';

  html += '<div class="sec">60 ngày gần nhất</div><div class="card">';
  if (!rows.length) html += '<div class="emp" style="padding:24px"><div class="e1">📒</div><div>Chưa có bút toán nào trong 60 ngày.</div></div>';
  rows.forEach(function (r) {
    var mau = r.docstatus === 0 ? 'c' : (r.docstatus === 2 ? 'x' : 'd');
    var chu = r.docstatus === 0 ? 'Nháp' : (r.docstatus === 2 ? 'Đã huỷ' : 'Đã ghi sổ');
    html += '<div class="hub" data-bt="' + h(r.name) + '">' +
      '<div class="hub-i" style="background:#f5f7fa">📒</div>' +
      '<div class="hub-t"><div class="t1">' + h(r.user_remark || r.title || r.name) + '</div>' +
      '<div class="t2">' + h(r.name) + ' · ' + hsNgayVn(String(r.posting_date).slice(0, 10)) + '</div>' +
      '<div class="t2"><span class="vxtag ' + mau + '">' + chu + '</span></div></div>' +
      '<b style="white-space:nowrap">' + money(r.total_debit) + ' đ</b></div>';
  });
  if (kq.con_nua) html += '<div style="padding:10px 14px;font-size:12.5px;color:#6b7280">Còn ' + kq.con_nua + ' tờ nữa, gõ vào ô tìm để lọc bớt.</div>';
  html += '</div>';

  var b = frame('Bút toán', html, {});
  var q = document.getElementById('btQ');
  if (q) q.onchange = function () { btTim = q.value.trim(); go(scrButToan, true); };
  Array.prototype.forEach.call(document.querySelectorAll('[data-btc]'), function (el) {
    el.onclick = function () { btChip = el.getAttribute('data-btc') || null; go(scrButToan, true); };
  });
  b.addEventListener('click', function (e) {
    var r = e.target.closest('[data-bt]'); if (!r) return;
    go(function () { scrButToanXem(r.getAttribute('data-bt')); });
  });
  var m = document.getElementById('btMoi');
  if (m) m.onclick = function () { btChonMau(); };
}


async function btChonMau() {
  var d;
  try { d = await api('vagabond.but_toan.danh_sach_mau'); }
  catch (e) { return baoTin((e && e.message) || 'Không đọc được định khoản mẫu'); }
  var lc = (d.mau || []).map(function (m) {
    return { k: m.k, nhan: m.ten + (m.thieu_tk.length ? ' (thiếu ' + m.thieu_tk.length + ' TK)' : ''), mo_ta: m.mo_ta, icon: m.icon };
  });
  lc.push({ k: '@tu_do', nhan: 'Tự gõ từng dòng', mo_ta: 'Không theo mẫu nào, tự chọn tài khoản Nợ và Có.', icon: '✏️' });
  var chon = await hoiChon('Lập bút toán', 'Chọn việc muốn hạch toán. Máy bày sẵn cặp tài khoản, chị chỉ điền số tiền.', lc, null);
  if (!chon) return;
  var m = (d.mau || []).filter(function (x) { return x.k === chon; })[0];
  btMau = chon === '@tu_do' ? null : chon;
  btNgay = today();
  btDienGiai = m ? m.ten : '';
  btDong = m ? m.dong.filter(function (x) { return x.tk_day_du; }).map(function (x) {
    return { tk: x.tk_day_du, ten: x.tk + ' - ' + x.ten_tk, ben: x.ben, nhan: x.nhan, so: 0, tu_tinh: x.tu_tinh, can_ben: x.can_ben, ben_ten: '' };
  }) : [];
  go(scrBtLap);
}


function btTinhTuDong() {
  var no = 0, co = 0;
  btDong.forEach(function (x) { if (!x.tu_tinh) { if (x.ben === 'no') no += (+x.so || 0); else co += (+x.so || 0); } });
  btDong.forEach(function (x) {
    if (!x.tu_tinh) return;
    x.so = x.ben === 'co' ? Math.max(0, no - co) : Math.max(0, co - no);
  });
  var tn = 0, tc = 0;
  btDong.forEach(function (x) { if (x.ben === 'no') tn += (+x.so || 0); else tc += (+x.so || 0); });
  return { no: tn, co: tc, lech: tn - tc };
}


function scrBtLap() {
  var t = btTinhTuDong();
  var html = '<div class="card" style="padding:12px 14px">' +
    '<div class="vxl" style="margin-top:0">Diễn giải</div>' +
    '<input class="tin" id="btDg" style="margin:0" value="' + h(btDienGiai) + '" placeholder="Ví dụ: Trích lương tháng 08/2026">' +
    '<div class="vxl">Ngày hạch toán</div>' +
    '<button class="btn gh" id="btNg" style="margin:0;text-align:left">' + hsNgayVn(btNgay) + '</button></div>';

  html += '<div class="sec">Định khoản · điền số tiền cho dòng cần dùng</div><div class="card" style="padding:6px 12px 12px">';
  if (!btDong.length) html += '<div style="font-size:13px;color:#98a2b3;padding:14px 2px">Chưa có dòng nào. Bấm Thêm dòng bên dưới.</div>';
  btDong.forEach(function (x, i) {
    html += '<div style="padding:10px 0;border-bottom:1px solid #f1f3f6">' +
      '<div style="display:flex;align-items:center;gap:8px">' +
      '<span class="vxtag ' + (x.ben === 'no' ? 'c' : 'd') + '" style="flex:0 0 auto">' + (x.ben === 'no' ? 'Nợ' : 'Có') + '</span>' +
      '<div style="flex:1;min-width:0"><div style="font-size:14px;font-weight:600;color:#101828;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + h(x.nhan || x.ten) + '</div>' +
      '<div style="font-size:11.5px;color:#98a2b3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + h(x.ten) + '</div></div>' +
      '<button class="vxx" data-btxoa="' + i + '">&times;</button></div>' +
      '<input class="tin" data-btso="' + i + '" type="tel" inputmode="numeric" style="margin:8px 0 0;text-align:right' + (x.tu_tinh ? ';background:#f3f4f6' : '') + '" ' +
      (x.tu_tinh ? 'readonly ' : '') + 'value="' + (x.so ? money(x.so) : '') + '" placeholder="0">' +
      (x.tu_tinh ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:4px">Dòng này máy tự tính cho cân</div>' : '') +
      (x.can_ben ? '<input class="tin" data-btben="' + i + '" style="margin:6px 0 0" value="' + h(x.ben_ten || '') + '" placeholder="Mã khách hàng hoặc nhà cung cấp">' : '') +
      '</div>';
  });
  html += '<button class="btn gh" id="btThem" style="margin-top:12px">➕ Thêm dòng</button></div>';

  var canBang = Math.abs(t.lech) < 1 && t.no > 0;
  html += '<div class="card" style="padding:12px 14px;background:' + (canBang ? '#f0fdfa;border:1.5px solid #99f6e4' : '#fef2f2;border:1.5px solid #fecaca') + '">' +
    '<div style="display:flex;justify-content:space-between;font-size:13.5px;color:#374151"><span>Tổng bên Nợ</span><b>' + money(t.no) + ' đ</b></div>' +
    '<div style="display:flex;justify-content:space-between;font-size:13.5px;color:#374151;margin-top:4px"><span>Tổng bên Có</span><b>' + money(t.co) + ' đ</b></div>' +
    '<div style="display:flex;justify-content:space-between;font-size:14px;margin-top:8px;font-weight:800;color:' + (canBang ? '#0f766e' : '#b3261e') + '">' +
    '<span>' + (canBang ? 'Đã cân' : 'Chênh lệch') + '</span><b>' + money(Math.abs(t.lech)) + ' đ</b></div></div>';

  html += '<button class="btn" id="btLuu"' + (canBang ? '' : ' disabled') + '>📝 Lưu nháp</button>' +
    '<button class="btn gh" id="btLuuGhi"' + (canBang ? '' : ' disabled') + '>📗 Lưu và ghi sổ luôn</button>';

  frame('Lập bút toán', html, { back: function () { go(scrButToan); } });

  var dg = document.getElementById('btDg');
  if (dg) dg.onchange = function () { btDienGiai = dg.value; };
  document.getElementById('btNg').onclick = async function () {
    var v = await hoiNgay(btNgay); if (v) { btNgay = v; go(scrBtLap, true); }
  };
  Array.prototype.forEach.call(document.querySelectorAll('[data-btso]'), function (el) {
    el.onchange = function () {
      var i = +el.getAttribute('data-btso');
      btDong[i].so = Number(String(el.value).replace(/[^0-9]/g, '')) || 0;
      go(scrBtLap, true);
    };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-btben]'), function (el) {
    el.onchange = function () { btDong[+el.getAttribute('data-btben')].ben_ten = el.value.trim(); };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-btxoa]'), function (el) {
    el.onclick = function () { btDong.splice(+el.getAttribute('data-btxoa'), 1); go(scrBtLap, true); };
  });
  document.getElementById('btThem').onclick = function () { btThemDong(); };

  document.getElementById('btLuu').onclick = function () { btGui(0); };
  document.getElementById('btLuuGhi').onclick = function () { btGui(1); };
}


async function btThemDong() {
  var tu = await hoiChu('Thêm dòng', 'Gõ số hiệu hoặc tên tài khoản để tìm.', '', { goi_y: '642 hoặc lương' });
  if (tu === null) return;
  var d;
  try { d = await api('vagabond.but_toan.tim_tai_khoan', { tu_khoa: tu || '' }); }
  catch (e) { return baoTin((e && e.message) || 'Tìm lỗi'); }
  if (!(d.rows || []).length) return baoTin('Không thấy tài khoản nào khớp "' + tu + '".');
  var tk = await hoiChon('Chọn tài khoản', 'Chỉ hiện tài khoản chi tiết, không hiện tài khoản nhóm.',
    (d.rows || []).slice(0, 30).map(function (x) { return { k: x.ma, nhan: x.ten, mo_ta: x.kieu || x.loai, icon: '🏷' }; }), null);
  if (!tk) return;
  var r = (d.rows || []).filter(function (x) { return x.ma === tk; })[0] || {};
  var ben = await hoiChon('Ghi bên nào', 'Dòng này ghi bên Nợ hay bên Có?',
    [{ k: 'no', nhan: 'Bên Nợ', mo_ta: 'Tăng tài sản, tăng chi phí, giảm nợ phải trả.', icon: '🔺' },
     { k: 'co', nhan: 'Bên Có', mo_ta: 'Tăng nợ phải trả, tăng doanh thu, giảm tài sản.', icon: '🔻' }], null);
  if (!ben) return;
  btDong.push({ tk: tk, ten: r.ten || tk, ben: ben, nhan: r.ten || tk, so: 0, tu_tinh: 0, can_ben: r.can_ben, ben_ten: '' });
  go(scrBtLap, true);
}


async function btGui(ghi) {
  var t = btTinhTuDong();
  if (Math.abs(t.lech) >= 1 || !t.no) return baoTin('Bút toán chưa cân, chưa lưu được.');
  var dung = btDong.filter(function (x) { return (+x.so || 0) > 0; });
  var mo = dung.map(function (x) {
    return (x.ben === 'no' ? 'Nợ ' : 'Có ') + x.ten + ': ' + money(x.so) + ' đ';
  }).join('\n');
  if (!await hoiCo(ghi ? 'Lưu và ghi sổ' : 'Lưu nháp',
    (btDienGiai || 'Bút toán tay') + '\nNgày ' + hsNgayVn(btNgay) + '\n\n' + mo + '\n\nTổng ' + money(t.no) + ' đ' +
    (ghi ? '\n\nGhi sổ rồi thì chỉ huỷ được chứ không sửa.' : ''), ghi ? 'Ghi sổ' : 'Lưu nháp')) return;
  busy(true);
  try {
    var kq = await api('vagabond.but_toan.tao', {
      dong: JSON.stringify(dung.map(function (x) {
        return { tk: x.tk, no: x.ben === 'no' ? x.so : 0, co: x.ben === 'co' ? x.so : 0, ben: x.ben_ten || '' };
      })),
      ngay: btNgay, dien_giai: btDienGiai, mau: btMau || '', ghi_so: ghi ? 1 : 0
    });
    busy(false); toast(kq.loi_nhan, 5000);
    btDong = []; btMau = null;
    go(function () { scrButToanXem(kq.ma); }, true);
  } catch (er) { busy(false); baoTin((er && er.message) || 'Lưu bút toán lỗi'); }
}


async function scrButToanXem(ma) {
  frame('Bút toán', '<div class="emp"><div class="e1">⏳</div><div>Đang mở...</div></div>');
  var d;
  try { d = await api('vagabond.but_toan.xem', { ma: ma }); }
  catch (e) { frame('Bút toán', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>'); return; }

  var html = '<div class="card" style="padding:14px">' +
    '<div style="font-size:18px;font-weight:800">' + h(d.dien_giai) + '</div>' +
    '<div style="font-size:13px;color:#6b7280;margin-top:2px">' + h(d.ma) + ' · ' + hsNgayVn(String(d.ngay).slice(0, 10)) + '</div>' +
    '<div style="margin-top:10px"><span class="vxtag ' + (d.nhap ? 'c' : (d.trang_thai === 'Đã huỷ' ? 'x' : 'd')) + '">' + h(d.trang_thai) + '</span></div></div>';

  html += '<div class="sec">Định khoản</div><div class="card" style="padding:6px 12px 12px">';
  (d.dong || []).forEach(function (x) {
    var no = x.no > 0;
    html += '<div style="display:flex;align-items:center;gap:9px;padding:10px 0;border-bottom:1px solid #f1f3f6">' +
      '<span class="vxtag ' + (no ? 'c' : 'd') + '" style="flex:0 0 auto">' + (no ? 'Nợ' : 'Có') + '</span>' +
      '<div style="flex:1;min-width:0"><div style="font-size:14px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + h(x.ten_tk || x.tk) + '</div>' +
      (x.ben ? '<div style="font-size:11.5px;color:#98a2b3">' + h(x.ben) + '</div>' : '') + '</div>' +
      '<b style="white-space:nowrap">' + money(no ? x.no : x.co) + ' đ</b></div>';
  });
  html += '<div style="display:flex;justify-content:space-between;padding:12px 0 2px;font-weight:800">' +
    '<span>Tổng</span><b>' + money(d.tong) + ' đ</b></div></div>';

  if (d.nhap && d.ghi_duoc) html += '<button class="btn" id="btGhi">📗 Ghi sổ</button>';
  if (!d.nhap && d.trang_thai === 'Đã ghi sổ' && d.ghi_duoc) html += '<button class="btn dg" id="btHuy">🚫 Huỷ bút toán</button>';

  frame('Bút toán', html, { back: function () { go(scrButToan); } });
  var g = document.getElementById('btGhi');
  if (g) g.onclick = async function () {
    if (!await hoiCo('Ghi sổ', 'Ghi sổ bút toán ' + d.ma + '? Ghi rồi thì chỉ huỷ được chứ không sửa.', 'Ghi sổ')) return;
    busy(true);
    try { var kq = await api('vagabond.but_toan.ghi_so', { ma: d.ma }); busy(false); toast(kq.loi_nhan, 4000); }
    catch (er) { busy(false); return baoTin((er && er.message) || 'Ghi sổ lỗi'); }
    go(function () { scrButToanXem(d.ma); }, true);
  };
  var hu = document.getElementById('btHuy');
  if (hu) hu.onclick = async function () {
    var ly = await hoiChu('Huỷ bút toán', 'Vì sao huỷ? Ghi lại để sau này còn truy.', '', { bat_buoc: 1, nhieu_dong: 1 });
    if (!ly) return;
    busy(true);
    try { var kq = await api('vagabond.but_toan.huy', { ma: d.ma, ly_do: ly }); busy(false); toast(kq.loi_nhan, 5000); }
    catch (er) { busy(false); return baoTin((er && er.message) || 'Huỷ lỗi'); }
    go(function () { scrButToanXem(d.ma); }, true);
  };
}


/* ================= TIM GIAO DICH NGAN HANG DE KHOP TAY =================
   Anh Viet 14/08/2026: "tao chuc nang tim kiem giao dich de khop thu cong
   duoc khong em? Sao em khong de xuat phuong an nua vay?"

   Boi canh: hai ho so APPMEREJM va APPHHKAPC mang ma giao dich tu dot dong
   bo SePay cu, bang Bank Transaction hien tai khong con ban ghi do. Truoc
   day gap vay la chiu, khong co duong nao noi lai. Man nay bay moi giao
   dich ra cho ke toan tu tim theo so tien, theo ngay, theo noi dung.

   Chi GAN MA, khong sinh but toan. Viec ghi so van di duong cu. */
var tgdTim = '', tgdSoTien = 0, tgdNgay = 120, tgdChuaGom = 0, tgdHoSo = '';

async function scrTimGiaoDich(maHoSo, soTien) {
  if (maHoSo !== undefined) { tgdHoSo = maHoSo || ''; tgdSoTien = Math.round(soTien || 0); }
  frame('Tìm giao dịch', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc sao kê...</div></div>');
  var d;
  try {
    d = await api('vagabond.ho_so_tt.tim_giao_dich', {
      tu_khoa: tgdTim, so_ngay: tgdNgay, so_tien: tgdSoTien || '', chi_chua_gom: tgdChuaGom ? 1 : 0
    });
  } catch (e) { frame('Tìm giao dịch', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không đọc được') + '</div></div>'); return; }
  var rows = d.rows || [];

  var html = '';
  if (tgdHoSo) {
    html += '<div class="card" style="padding:12px 14px;background:#f0fdfa;border:1.5px solid #99f6e4">' +
      '<div style="font-size:12px;color:#0f766e;font-weight:800">ĐANG KHỚP CHO HỒ SƠ</div>' +
      '<div style="font-size:15px;font-weight:700;margin-top:3px">' + h(tgdHoSo) + '</div>' +
      '<div style="font-size:12.5px;color:#0f766e;margin-top:2px">Bấm vào một giao dịch bên dưới để gán mã vào hồ sơ này.</div></div>';
  }

  html += '<div class="card" style="padding:12px 14px">' +
    '<input class="tin" id="tgdQ" placeholder="Tìm theo nội dung chuyển khoản hoặc mã giao dịch" value="' + h(tgdTim) + '" style="margin:0">' +
    '<div class="vxl">Lọc đúng số tiền (để 0 là bỏ lọc)</div>' +
    '<input class="tin" id="tgdT" type="tel" inputmode="numeric" style="margin:0;text-align:right" value="' + (tgdSoTien ? money(tgdSoTien) : '') + '" placeholder="0"></div>';

  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
    [[30, '30 ngày'], [120, '4 tháng'], [365, '1 năm'], [1200, 'Tất cả']].map(function (x) {
      return posChipNut('data-tgdn="' + x[0] + '"', x[1], tgdNgay === x[0]);
    }).join('') + posChipNut('data-tgdg="1"', '🚫 Ẩn giao dịch đã gom', !!tgdChuaGom)
  ) + '</div>';

  html += '<div class="sec">' + d.tong + ' giao dịch khớp bộ lọc</div><div class="card">';
  if (!rows.length) html += '<div class="emp" style="padding:24px"><div class="e1">🏦</div><div>Không có giao dịch nào khớp. Nới bộ lọc ngày hoặc bỏ lọc số tiền.</div></div>';
  rows.forEach(function (r) {
    html += '<div class="hub" data-tgd="' + h(r.ma) + '" data-tgdt="' + Math.round(r.tien) + '">' +
      '<div class="hub-i" style="background:' + (r.thu > 0 ? '#f0fdf4' : '#fef2f2') + '">' + (r.thu > 0 ? '⬇️' : '⬆️') + '</div>' +
      '<div class="hub-t"><div class="t1" style="font-size:14px">' + h(r.noi_dung || '(không có nội dung)') + '</div>' +
      '<div class="t2">' + hsNgayVn(String(r.ngay).slice(0, 10)) + ' · ' + h(r.ma) + '</div>' +
      (r.da_gom ? '<div class="t2"><span class="vxtag c">đã nằm trong một hồ sơ</span></div>' : '') +
      '</div><b style="white-space:nowrap;color:' + (r.thu > 0 ? '#15803d' : '#b3261e') + '">' + money(r.tien) + ' đ</b></div>';
  });
  if (d.con_nua) html += '<div style="padding:10px 14px;font-size:12.5px;color:#6b7280">Còn ' + d.con_nua + ' giao dịch nữa, lọc bớt để thấy hết.</div>';
  html += '</div>';

  var b = frame('Tìm giao dịch', html, {});
  var q = document.getElementById('tgdQ');
  if (q) q.onchange = function () { tgdTim = q.value.trim(); go(function () { scrTimGiaoDich(); }, true); };
  var t = document.getElementById('tgdT');
  if (t) t.onchange = function () { tgdSoTien = Number(String(t.value).replace(/[^0-9]/g, '')) || 0; go(function () { scrTimGiaoDich(); }, true); };
  Array.prototype.forEach.call(document.querySelectorAll('[data-tgdn]'), function (el) {
    el.onclick = function () { tgdNgay = +el.getAttribute('data-tgdn'); go(function () { scrTimGiaoDich(); }, true); };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-tgdg]'), function (el) {
    el.onclick = function () { tgdChuaGom = tgdChuaGom ? 0 : 1; go(function () { scrTimGiaoDich(); }, true); };
  });
  b.addEventListener('click', async function (e) {
    var r = e.target.closest('[data-tgd]'); if (!r) return;
    if (!tgdHoSo) return baoTin('Vào hồ sơ cần khớp rồi bấm nút Khớp tay giao dịch, màn này sẽ biết gán vào đâu.');
    var ma = r.getAttribute('data-tgd');
    var tien = +r.getAttribute('data-tgdt') || 0;
    if (!await hoiCo('Khớp tay giao dịch',
      'Gán giao dịch ' + ma + ' (' + money(tien) + ' đ) vào hồ sơ ' + tgdHoSo + '?\n\n' +
      'Chỉ ghi mã giao dịch lên hồ sơ để sau này còn tra. Không sinh bút toán, không đụng vào sổ.', 'Gán')) return;
    busy(true);
    try { var kq = await api('vagabond.ho_so_tt.gan_giao_dich', { name: tgdHoSo, ma_giao_dich: ma }); busy(false); toast(kq.loi_nhan, 5000); }
    catch (er) { busy(false); return baoTin((er && er.message) || 'Gán lỗi'); }
    var hs = tgdHoSo; tgdHoSo = '';
    go(function () { scrHoSoTTView(hs); }, true);
  });
}


/* ================= CANH BAO PHUONG THUC THANH TOAN =================
   Anh Viet 14/08/2026: "em co bien phap gi canh bao voi cac hoa don chon
   sai phuong thuc thanh toan chua?"

   Truoc day loi nay chi lo ra luc doi soat COD cuoi ngay - tuc la sau khi
   shipper da di roi. Don Oshima 1.480.000 hom 13/08 dung kieu do: hoa don
   chua chon phuong thuc nen may mac dinh coi la thu tien mat, van don mang
   COD, shipper di doi tien cua khach da hen chuyen khoan.

   Man nay soat truoc, ba loai loi xep theo muc nguy hiem. */
var cbNgay = 7, cbLoai = null;

async function scrCanhBaoTT() {
  frame('Cảnh báo thanh toán', '<div class="emp"><div class="e1">⏳</div><div>Đang soát hoá đơn...</div></div>');
  var d;
  try { d = await api('vagabond.van_don.canh_bao_thanh_toan', { so_ngay: cbNgay }); }
  catch (e) { frame('Cảnh báo thanh toán', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var rows = d.rows || [], dem = d.dem || {};

  var MAU = {
    chua_chon: ['#fef2f2', '#fecaca', '#b91c1c', '❗', 'Chưa chọn phương thức'],
    lech_cod: ['#fffbeb', '#fde68a', '#92400e', '⚠️', 'Vận đơn treo COD nhầm'],
    no_khong_khach: ['#f5f3ff', '#ddd6fe', '#5b21b6', '👤', 'Công nợ không có khách']
  };

  var html = '<div class="card" style="padding:14px;background:' + (rows.length ? '#fef2f2;border:1.5px solid #fecaca' : '#f0fdf4;border:1.5px solid #bbf7d0') + '">' +
    '<div style="font-size:11.5px;font-weight:800;color:' + (rows.length ? '#b91c1c' : '#166534') + '">SOÁT ' + d.so_hoa_don_soat + ' HOÁ ĐƠN ' + cbNgay + ' NGÀY GẦN NHẤT</div>' +
    '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:6px">' +
    '<span style="font-size:14px;color:#374151">' + (rows.length ? 'Cần xem lại' : 'Không có hoá đơn nào sai') + '</span>' +
    '<b style="font-size:22px;color:' + (rows.length ? '#b91c1c' : '#166534') + '">' + d.tong + '</b></div></div>';

  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
    [[7, '7 ngày'], [30, '30 ngày'], [90, '3 tháng']].map(function (x) {
      return posChipNut('data-cbn="' + x[0] + '"', x[1], cbNgay === x[0]);
    }).join('')) + '</div>';

  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
    [['', '📚 Tất cả', d.tong]].concat(Object.keys(MAU).map(function (k) {
      return [k, MAU[k][3] + ' ' + MAU[k][4], dem[k] || 0];
    })).map(function (x) {
      return posChipNut('data-cbl="' + x[0] + '"', x[1] + ' · ' + (x[2] || 0), (cbLoai || '') === x[0]);
    }).join('')) + '</div>';

  var loc = cbLoai ? rows.filter(function (r) { return r.loi === cbLoai; }) : rows;
  html += '<div class="sec">Bấm để mở hoá đơn</div><div class="card">';
  if (!loc.length) html += '<div class="emp" style="padding:24px"><div class="e1">✅</div><div>Không có hoá đơn nào khớp bộ lọc. Sales đang chọn phương thức đúng.</div></div>';
  loc.forEach(function (r) {
    var m = MAU[r.loi] || ['#f9fafb', '#eee', '#374151', '•', ''];
    html += '<div class="hub" data-cbhd="' + h(r.hoa_don) + '">' +
      '<div class="hub-i" style="background:' + m[0] + '">' + m[3] + '</div>' +
      '<div class="hub-t"><div class="t1">' + h(r.khach || '(chưa có khách)') + '</div>' +
      '<div class="t2">' + h(r.hoa_don) + ' · ' + hsNgayVn(String(r.ngay).slice(0, 10)) + (r.nguon ? ' · ' + h(r.nguon) : '') + '</div>' +
      '<div class="t2" style="color:' + m[2] + '">' + h(r.nhac) + '</div></div>' +
      '<b style="white-space:nowrap">' + money(r.tong) + ' đ</b></div>';
  });
  html += '</div>';

  html += '<div style="font-size:12px;color:#98a2b3;padding:12px 4px;line-height:1.6">' +
    'Sửa phương thức trên hoá đơn xong thì vào Đối soát COD bấm lại, số COD sẽ tự tính lại theo phương thức mới.' +
    (d.bo_qua_nhap_lieu ? '<br><br>Đã bỏ qua ' + d.bo_qua_nhap_lieu + ' tờ nhập từ đợt chuyển dữ liệu Fabi. Những tờ đó không có phương thức vì bên Fabi không có trường này, không phải Sales chọn thiếu.' : '') +
    '</div>';

  var b = frame('Cảnh báo thanh toán', html, {});
  Array.prototype.forEach.call(document.querySelectorAll('[data-cbn]'), function (el) {
    el.onclick = function () { cbNgay = +el.getAttribute('data-cbn'); go(scrCanhBaoTT, true); };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-cbl]'), function (el) {
    el.onclick = function () { cbLoai = el.getAttribute('data-cbl') || null; go(scrCanhBaoTT, true); };
  });
  b.addEventListener('click', function (e) {
    var r = e.target.closest('[data-cbhd]'); if (!r) return;
    go(function () { scrDsView(r.getAttribute('data-cbhd'), true); });
  });
}


/* ---------- Khop tay giao dich cho phieu de nghi thanh toan ----------
   Anh Viet 14/08/2026: "lo dau may doi chieu khong duoc". May doi chieu
   theo NOI DUNG chuyen khoan, ma ke toan ben khach si hay go noi dung
   theo he thong cua ho chu khong theo ma minh dat. Day la duong lui. */
async function cnKhopTay(d) {
  var con = d.con_thieu || d.tong_tien;
  var ds;
  try { ds = await api('vagabond.cong_no.tim_giao_dich_thu', { so_ngay: 120, so_tien: Math.round(con) }); }
  catch (e) { return baoTin((e && e.message) || 'Không đọc được sao kê'); }

  var lc = (ds.rows || []).slice(0, 25).map(function (r) {
    return {
      k: r.ma,
      nhan: money(r.tien) + ' đ · ' + hsNgayVn(String(r.ngay).slice(0, 10)),
      mo_ta: (r.noi_dung || '(không có nội dung)').slice(0, 110),
      icon: '⬇️'
    };
  });
  lc.push({ k: '@go_tay', nhan: 'Không thấy giao dịch nào khớp', mo_ta: 'Tự gõ số tiền đã nhận, không gắn giao dịch nào.', icon: '✏️' });

  var chon = await hoiChon('Khớp tay phiếu ' + d.ma_phieu,
    'Đang lọc giao dịch tiền về đúng ' + money(con) + ' đ trong 4 tháng. Chọn giao dịch của khách này.',
    lc, null);
  if (!chon) return;

  var soTien = con, maGd = '';
  if (chon === '@go_tay') {
    soTien = await hoiSo('Khớp tay', 'Số tiền thực nhận cho phiếu này.', String(Math.round(con)));
    if (!soTien) return;
  } else {
    maGd = chon;
    var g = (ds.rows || []).filter(function (x) { return x.ma === chon; })[0] || {};
    soTien = Math.round(g.tien || con);
  }
  var gc = await hoiChu('Khớp tay', 'Ghi chú vì sao phải khớp tay (để sau này còn truy).', '', { nhieu_dong: 1, goi_y: 'Khách chuyển từ tài khoản công ty, nội dung không mang mã phiếu' });
  if (gc === null) return;

  if (!await hoiCo('Xác nhận khớp tay',
    'Phiếu ' + d.ma_phieu + '\nGhi nhận đã thu ' + money(soTien) + ' đ' +
    (maGd ? '\nGắn với giao dịch ' + maGd : '\nKhông gắn giao dịch nào') +
    '\n\nCông nợ của khách sẽ được cập nhật theo số này. Nếu đủ, máy gửi luôn thư báo nhận tiền cho khách.', 'Khớp')) return;
  busy(true);
  try {
    var kq = await api('vagabond.cong_no.khop_tay', { name: d.name, so_tien: soTien, ma_giao_dich: maGd, ghi_chu: gc || '' });
    busy(false); toast(kq.loi_nhan, 5500);
  } catch (e) { busy(false); return baoTin((e && e.message) || 'Khớp tay lỗi'); }
  go(function () { scrCnPhieu(d.name); }, true);
}


/* ================= BANG GIA MUA NGUYEN VAT LIEU =================
   Anh Viet 14/08/2026 hoi nen dat cho khai gia o dau, em tra loi khong nen
   de trong Danh muc san pham. Goc cua su co lap xuong khong phai sai gia
   ma la SAI DON VI: mon do don vi kho la Gram, nguoi nhap nghi theo Tui,
   go 135.185 vao o don gia moi gram, thanh 365 trieu tien lap xuong.

   Nen man nay bat khai ba thu: don vi mua, quy doi ra don vi kho, va gia
   moi don vi mua. May tu chia. Uyen khong bao gio go so per gram nua. */
var bgTim = '', bgChip = null, bgNhom = null;

async function scrBangGia() {
  frame('Bảng giá mua', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc bảng giá...</div></div>');
  var kq;
  var ts = {};
  if (bgTim) ts.tu_khoa = bgTim;
  if (bgChip) ts.chip = bgChip;
  if (bgNhom) ts.nhom = bgNhom;
  try { kq = await api('vagabond.bang_gia.danh_sach', ts); }
  catch (e) { frame('Bảng giá mua', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var rows = kq.rows || [], dem = kq.dem || {};

  var html = '<div class="card" style="padding:12px 14px"><input class="tin" id="bgQ" placeholder="Tìm theo tên mặt hàng" value="' + h(bgTim) + '" style="margin:0"></div>';

  var CHIP = [
    ['', '📚 Tất cả', kq.tat_ca],
    ['chua_gia', '⭕ Chưa có giá', dem.chua_gia],
    ['co_gia', '✅ Đã có giá', dem.co_gia],
    ['lech_dvt', '⚠️ Thiếu quy đổi', dem.lech_dvt]
  ];
  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(CHIP.map(function (x) {
    return posChipNut('data-bgc="' + x[0] + '"', x[1] + ' · ' + (x[2] || 0), (bgChip || '') === x[0]);
  }).join('')) + '</div>';

  if (kq.sua_duoc) {
    html += '<div style="display:flex;gap:8px;margin-bottom:10px">' +
      '<button class="btn gh" id="bgMau" style="flex:1;margin:0">📊 Tải mẫu Excel</button>' +
      '<button class="btn" id="bgNhap" style="flex:1;margin:0">📥 Nhập từ Excel</button></div>';
  }

  if (dem.lech_dvt) {
    html += '<div class="card" style="padding:12px 14px;background:#fffbeb;border:1.5px solid #fde68a">' +
      '<div style="font-size:13px;line-height:1.65;color:#92400e">' + dem.lech_dvt +
      ' mặt hàng khai giá theo đơn vị mua khác đơn vị kho mà chưa điền quy đổi. ' +
      'Những món này máy chưa tính được giá mỗi đơn vị kho, nên giá vốn vẫn chưa đúng.</div></div>';
  }

  html += '<div class="sec">Bấm vào một dòng để khai giá</div><div class="card">';
  if (!rows.length) html += '<div class="emp" style="padding:24px"><div class="e1">💰</div><div>Không có mặt hàng nào khớp bộ lọc.</div></div>';
  rows.forEach(function (r) {
    html += '<div class="hub" data-bg="' + h(r.ma) + '">' +
      '<div class="hub-i" style="background:' + (r.canh_bao ? '#fffbeb' : (r.gia_mua ? '#f0fdf4' : '#f9fafb')) + '">' +
      (r.canh_bao ? '⚠️' : (r.gia_mua ? '✅' : '⭕')) + '</div>' +
      '<div class="hub-t"><div class="t1">' + h(r.ten) + '</div>' +
      '<div class="t2">' + h(r.ma) + ' · kho tính bằng ' + h(r.dvt_kho) + '</div>' +
      (r.gia_mua
        ? '<div class="t2">' + money(r.gia_mua) + ' đ mỗi ' + h(r.dvt_mua) +
          (r.gia_kho && r.dvt_mua !== r.dvt_kho ? ' · ' + money(Math.round(r.gia_kho)) + ' đ mỗi ' + h(r.dvt_kho) : '') + '</div>'
        : '<div class="t2" style="color:#98a2b3">Chưa khai giá</div>') +
      (r.canh_bao ? '<div class="t2" style="color:#b45309">' + h(r.canh_bao) + '</div>' : '') +
      '</div></div>';
  });
  if (kq.con_nua) html += '<div style="padding:10px 14px;font-size:12.5px;color:#6b7280">Còn ' + kq.con_nua + ' mặt hàng nữa, gõ vào ô tìm để lọc bớt.</div>';
  html += '</div>';

  var b = frame('Bảng giá mua', html, {});
  var q = document.getElementById('bgQ');
  if (q) q.onchange = function () { bgTim = q.value.trim(); go(scrBangGia, true); };
  Array.prototype.forEach.call(document.querySelectorAll('[data-bgc]'), function (el) {
    el.onclick = function () { bgChip = el.getAttribute('data-bgc') || null; go(scrBangGia, true); };
  });
  b.addEventListener('click', function (e) {
    var r = e.target.closest('[data-bg]'); if (!r) return;
    var ma = r.getAttribute('data-bg');
    var d = rows.filter(function (x) { return x.ma === ma; })[0];
    if (d && kq.sua_duoc) bgKhaiGia(d);
  });
  var nm = document.getElementById('bgMau');
  if (nm) nm.onclick = async function () {
    busy(true);
    try { var fl = await api('vagabond.bang_gia.mau_excel', {}); busy(false); bcTaiVe(fl.ten_file, fl.b64, fl.kieu); toast('Đã tải ' + fl.ten_file, 4000); }
    catch (e) { busy(false); baoTin((e && e.message) || 'Tải mẫu lỗi'); }
  };
  var nn = document.getElementById('bgNhap');
  if (nn) nn.onclick = function () { bgNhapExcel(); };
}


async function bgKhaiGia(d) {
  var dvt = await hoiChu('Khai giá ' + d.ten,
    'Đơn vị MUA - thứ ghi trên hoá đơn nhà cung cấp. Kho đang tính bằng <b>' + h(d.dvt_kho) + '</b>.',
    d.dvt_mua || d.dvt_kho, { bat_buoc: 1, goi_y: 'Túi' });
  if (!dvt) return;

  var hs = 1;
  if (dvt !== d.dvt_kho) {
    hs = await hoiSo('Khai giá ' + d.ten,
      'Một <b>' + h(dvt) + '</b> bằng bao nhiêu <b>' + h(d.dvt_kho) + '</b>? Ví dụ một túi 400gr thì điền 400.',
      d.he_so ? String(d.he_so) : '');
    if (!hs) return;
  }

  var gia = await hoiSo('Khai giá ' + d.ten,
    'Giá mỗi <b>' + h(dvt) + '</b>, chưa gồm thuế GTGT.',
    d.gia_mua ? String(Math.round(d.gia_mua)) : '');
  if (!gia) return;

  var moiKho = Math.round(gia / (hs || 1));
  if (!await hoiCo('Xác nhận giá',
    d.ten + '\n\n' + money(gia) + ' đ mỗi ' + dvt +
    (dvt !== d.dvt_kho ? '\n1 ' + dvt + ' = ' + hs + ' ' + d.dvt_kho + '\n\nTức ' + money(moiKho) + ' đ mỗi ' + d.dvt_kho : '') +
    '\n\nGiá này sẽ tự điền vào đơn đặt hàng và dùng để tính giá vốn.', 'Lưu giá')) return;

  busy(true);
  try { var kq = await api('vagabond.bang_gia.dat_gia', { ma_mon: d.ma, gia: gia, dvt_mua: dvt, he_so: hs }); busy(false); toast(kq.loi_nhan, 5000); }
  catch (e) { busy(false); return baoTin((e && e.message) || 'Lưu giá lỗi'); }
  go(scrBangGia, true);
}


async function bgNhapExcel() {
  var inp = document.createElement('input');
  inp.type = 'file';
  inp.accept = '.xlsx';
  inp.onchange = async function () {
    var f = inp.files && inp.files[0];
    if (!f) return;
    var b64 = await new Promise(function (ok) {
      var fr = new FileReader();
      fr.onload = function () { ok(String(fr.result).split(',')[1] || ''); };
      fr.readAsDataURL(f);
    });
    busy(true);
    var thu;
    try { thu = await api('vagabond.bang_gia.nhap_excel', { b64: b64, that_su: 0 }); busy(false); }
    catch (e) { busy(false); return baoTin((e && e.message) || 'Đọc tệp lỗi'); }

    var mo = 'Tệp có ' + thu.so_ok + ' dòng khai được' +
      (thu.bo_qua ? ', ' + thu.bo_qua + ' dòng bỏ trống giá nên bỏ qua' : '') +
      (thu.so_loi ? ', ' + thu.so_loi + ' dòng lỗi' : '') + '.';
    if ((thu.mau || []).length) {
      mo += '\n\nVài dòng đầu:\n' + thu.mau.slice(0, 5).map(function (x) {
        return x.ma + ' · ' + money(x.gia) + ' đ mỗi ' + x.dvt_mua +
          (x.dvt_mua !== x.dvt_kho ? ' = ' + money(Math.round(x.gia_kho)) + ' đ mỗi ' + x.dvt_kho : '');
      }).join('\n');
    }
    if (thu.so_loi) mo += '\n\nDòng lỗi:\n' + (thu.loi || []).slice(0, 6).join('\n');
    if (!thu.so_ok) return baoTin(mo + '\n\nKhông có dòng nào khai được.');
    if (!await hoiCo('Nhập bảng giá', mo + '\n\nNhập ' + thu.so_ok + ' dòng này vào hệ?', 'Nhập')) return;

    busy(true);
    try { var kq = await api('vagabond.bang_gia.nhap_excel', { b64: b64, that_su: 1 }); busy(false); toast(kq.loi_nhan, 6000);
      if (kq.so_loi) baoTin((kq.loi || []).join('\n'), 'Dòng không nhập được'); }
    catch (e) { busy(false); return baoTin((e && e.message) || 'Nhập lỗi'); }
    go(scrBangGia, true);
  };
  inp.click();
}




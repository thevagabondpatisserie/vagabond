/* Issue 328: cùng một màn chọn sao kê cho TTNB, APP và hoàn tiền.
   Chỉ chọn dòng; xác nhận và ghi vẫn đi cửa nghiệp vụ đang có. */
async function scrKhopSepay(o, loc, giuTim) {
  var luot = scrKhopSepay.luot = (scrKhopSepay.luot || 0) + 1;
  loc = Object.assign({tai_khoan:'', so_ngay:45, tu_khoa:'', thu_tu:'goi_y', bat_dau:0}, loc || {});
  frame('Khớp SePay thủ công', '<div class="emp">Đang đọc sao kê...</div>');
  var kq;
  try {
    kq = await api('vagabond.doi_soat_sepay.ung_vien', Object.assign({loai:o.loai, ma_phieu:o.ma}, loc));
  } catch (e) {
    if (luot !== scrKhopSepay.luot) return;
    frame('Khớp SePay thủ công', '<div class="emp">' + h((e && e.message) || 'Chưa đọc được sao kê. Tải lại để thử tiếp.') + '</div>');
    return;
  }
  if (luot !== scrKhopSepay.luot) return;
  if (o.loai === 'cong_no' && o.tien_ky != null) {
    var ky = Number(o.tien_ky);
    if (!Number.isFinite(ky) || ky <= 0 || ky > Number(kq.so_tien)) {
      frame('Khớp SePay thủ công', '<div class="emp">Khoản còn phải thu đã đổi. Quay lại phiếu để chọn khoản thu mới.</div>');
      return;
    }
    kq.so_tien = ky;
  }
  var rows = kq.rows || [], cd = kq.chan_doan || {};
  var nhieu = kq.chon_bo === 1, chon = o._boSepay || (o._boSepay = {}), dangGan = false;
  function tongChon() { return Object.keys(chon).reduce(function (t, ma) { return t + chon[ma].phan_bo; }, 0); }
  function duBo() { return Object.keys(chon).length > 0 && Number.isFinite(tongChon()) && Math.abs(tongChon() - Number(kq.so_tien)) < 0.001; }
  // Làm mới phần còn lại của những dòng vừa đọc, không giữ số dư cũ sau lọc.
  if (nhieu) rows.forEach(function (r) {
    if (chon[r.name] && (r.dung_duoc === 0 || Number(r.con_lai) < chon[r.name].phan_bo || r.bank_account !== chon[r.name].bank_account)) delete chon[r.name];
  });
  var html = '<div class="card" style="padding:12px 14px"><b>' + h(o.ma) + ' · ' + money(kq.so_tien) + ' đ</b></div>';
  html += '<div style="padding:0 12px"><input class="tin" id="ksTim" aria-label="Tìm sao kê" placeholder="Tìm nội dung, mã giao dịch hoặc số tiền" value="' + h(loc.tu_khoa) + '"></div>';
  function chip(thuoc, ds, daChon) {
    return '<div class="chips" style="padding:2px 12px 8px">' + ds.map(function (t) {
      return '<button class="chip' + (String(daChon) === String(t.ma) ? ' on' : '') + '" ' + thuoc + '="' + h(t.ma) + '" title="' + h(t.ten_day_du || t.nhan) + '" style="min-height:44px">' + h(t.nhan) + '</button>';
    }).join('') + '</div>';
  }
  html += chip('data-sepaytk', [{ma:'',nhan:'Tất cả'}].concat(kq.tai_khoan_sepay || []), loc.tai_khoan);
  html += chip('data-ksngay', [{ma:45,nhan:'45 ngày'},{ma:120,nhan:'4 tháng'},{ma:365,nhan:'1 năm'},{ma:1200,nhan:'40 tháng'}], loc.so_ngay);
  html += chip('data-ksxep', [{ma:'goi_y',nhan:'Gợi ý'},{ma:'moi_nhat',nhan:'Mới nhất'}], loc.thu_tu);
  if (!(kq.tai_khoan_sepay || []).length) html += '<div style="padding:8px 12px;font-size:13px">Chưa có tài khoản SePay đang hoạt động. Nhờ kế toán kiểm tra Cài đặt SePay.</div>';
  if (!rows.length) html += '<div class="emp">Không có giao dịch khớp bộ lọc. Đã đọc ' + Number(cd.so_dong_quet || 0) + ' dòng trong ' + Number(cd.so_ngay || loc.so_ngay) + ' ngày. Thử chọn Tất cả, mở rộng ngày hoặc bỏ từ tìm.</div>';
  rows.forEach(function (r) {
    var chan = r.dung_duoc === 0, nen = chan ? '#f3f4f6' : (r.khop_ma ? '#f0fdf4' : (r.dung_tien ? '#eff6ff' : '#fff'));
    html += '<div class="ksDong ' + h(o.lop || '') + '" data-gd="' + h(r.name) + '" data-chan="' + h(chan ? r.vi_sao_khong : '') + '" data-tien="' + Number(r.tien || 0) + '" style="min-height:44px;padding:12px;margin:8px 12px;border:1px solid #d1d5db;border-radius:12px;background:' + nen + '">' +
      (nhieu ? '<button type="button" class="chip ksChon" aria-pressed="' + (chon[r.name] ? 'true' : 'false') + '">' + (chon[r.name] ? '✓ Đã chọn' : '+ Chọn') + '</button>' : '') +
      '<div style="display:flex;justify-content:space-between;gap:8px"><b>' + money(r.tien) + ' đ</b><span>' + h(hsNgayVn(String(r.date || '').slice(0,10))) + '</span></div>' +
      (nhieu ? '<div class="ksPhan" style="font-size:13px;margin-top:4px"></div>' : '') +
      '<div style="font-size:13px;font-weight:700;margin-top:4px">' + h(r.nhan_ngan_hang || 'Chưa xác định tài khoản') + '</div>' +
      '<div style="font-size:13px;overflow-wrap:anywhere;margin-top:4px">' + h(r.mo_ta || '(không có nội dung)') + (r.reference_number ? '<br>Tham chiếu: ' + h(r.reference_number) : '') + '</div>' +
      '<div style="font-size:13px;color:#6b7280;margin-top:4px">' + h(chan ? r.vi_sao_khong : ((r.khop_ma ? 'Khớp mã · ' : '') + (r.dung_tien ? 'Đúng số tiền' : 'Lệch ' + money(r.lech) + ' đ'))) + '</div></div>';
  });
  if (loc.bat_dau || kq.con_nua) html += '<div style="display:flex;gap:8px;padding:12px">' + (loc.bat_dau ? '<button class="btn gh" id="ksTruoc">Trang trước</button>' : '') + (kq.con_nua ? '<button class="btn gh" id="ksTiep">Xem tiếp (' + Number(kq.con_nua) + ')</button>' : '') + '</div>';
  html += '<details style="padding:12px;font-size:13px"><summary>Thông tin tìm sao kê</summary>' +
    'Đã đọc ' + Number(cd.so_dong_quet || 0) + ' dòng; ' + Number(kq.tong || rows.length) + ' dòng khớp bộ lọc; ' + Number(cd.so_dong_chua_dung || 0) + ' dòng chưa dùng được.' +
    (cd.moi_nhat ? '<br>Mới nhất trong khoảng tìm: ' + h(hsNgayVn(cd.moi_nhat)) : '') +
    '<br>Gợi ý: dòng dùng được, khớp mã, đúng tiền; trong mỗi nhóm ngày mới nhất trước. Mới nhất: tất cả theo ngày giảm dần.</details>';
  if (nhieu) html += '<div style="position:sticky;bottom:0;background:#fff;padding:12px;border-top:1px solid #ddd;z-index:4"><div id="ksTong" role="status" aria-live="polite"></div><button class="btn" id="ksGan" disabled>Gán các dòng đã chọn</button><button class="btn gh" id="ksXoa">Bỏ chọn tất cả</button></div>';
  var b = frame('Khớp SePay thủ công', html);
  function capNhatTong() {
    if (!nhieu) return;
    var t = tongChon(), lech = Number(kq.so_tien) - t, el = document.getElementById('ksTong'), gan = document.getElementById('ksGan');
    if (el) el.textContent = 'Đã chọn ' + Object.keys(chon).length + ' dòng: ' + money(t) + ' / ' + money(kq.so_tien) + ' đ. ' + (duBo() ? 'Đủ tiền.' : (lech >= 0 ? 'Còn thiếu ' : 'Đang thừa ') + money(Math.abs(lech)) + ' đ.');
    if (gan) gan.disabled = !duBo() || dangGan;
    b.querySelectorAll('.ksDong').forEach(function (n) {
      var bt = n.querySelector && n.querySelector('.ksChon'), da = !!chon[n.getAttribute('data-gd')];
      if (bt) { bt.textContent = da ? '✓ Đã chọn' : '+ Chọn'; bt.setAttribute('aria-pressed', String(da)); }
      var ma = n.getAttribute('data-gd'), r = rows.find(function (x) { return x.name === ma; }), phan = n.querySelector('.ksPhan');
      if (phan && r) phan.textContent = 'Còn dùng được ' + money(r.con_lai) + ' đ.' + (da ? ' Gán cho phiếu này ' + money(chon[ma].phan_bo) + ' đ; còn lại ' + money(Number(r.con_lai) - chon[ma].phan_bo) + ' đ.' : '');
    });
  }
  if (nhieu) {
    document.getElementById('ksGan').onclick = async function () {
      if (dangTim || dangGan || !duBo() || luot !== scrKhopSepay.luot) return;
      dangGan = true; capNhatTong();
      try {
        await o.chon(JSON.stringify(Object.keys(chon).map(function (ma) { return {name:ma, phan_bo:chon[ma].phan_bo}; })), tongChon());
      } finally { dangGan = false; capNhatTong(); }
    };
    document.getElementById('ksXoa').onclick = function () { if (dangGan) return; Object.keys(chon).forEach(function (ma) { delete chon[ma]; }); capNhatTong(); };
    capNhatTong();
  }
  var henTim = null, dangTim = false;
  function doi(cot, giaTri, giuO) { if (henTim) clearTimeout(henTim); var moi = Object.assign({}, loc, {bat_dau:0}); moi[cot] = giaTri; return scrKhopSepay(o, moi, giuO); }
  [['data-sepaytk','tai_khoan'],['data-ksngay','so_ngay'],['data-ksxep','thu_tu']].forEach(function (c) {
    b.querySelectorAll('[' + c[0] + ']').forEach(function (n) { n.onclick = function () { return doi(c[1], n.getAttribute(c[0])); }; });
  });
  var q = document.getElementById('ksTim');
  if (q) {
    if (giuTim) { q.focus(); if (q.setSelectionRange) q.setSelectionRange(q.value.length, q.value.length); }
    q.oninput = function () {
      dangTim = true;
      if (henTim) clearTimeout(henTim);
      henTim = setTimeout(function () { doi('tu_khoa', q.value, true); }, 250);
    };
  }
  [['ksTruoc',-60],['ksTiep',60]].forEach(function (c) {
    var n = document.getElementById(c[0]);
    if (n) n.onclick = function () { return scrKhopSepay(o, Object.assign({},loc,{bat_dau:Math.max(0,Number(loc.bat_dau)+c[1])})); };
  });
  b.querySelectorAll('.ksDong').forEach(function (n) {
    n.onclick = function () {
      if (dangTim || luot !== scrKhopSepay.luot) return baoTin('Đang lọc sao kê, chờ kết quả mới rồi chọn.');
      var lyDo = n.getAttribute('data-chan');
      if (lyDo) return baoTin(lyDo);
      if (!nhieu) return o.chon(n.getAttribute('data-gd'), Number(n.getAttribute('data-tien') || 0));
      if (dangGan) return;
      var ma = n.getAttribute('data-gd'), r = rows.find(function (x) { return x.name === ma; });
      if (chon[ma]) { delete chon[ma]; capNhatTong(); return; }
      if (!r || !r.bank_account || !Number.isFinite(Number(r.con_lai)) || Number(r.con_lai) <= 0) return baoTin('Dòng này chưa có phần tiền khả dụng. Tải lại sao kê.');
      var cacMa = Object.keys(chon);
      if (cacMa.length && chon[cacMa[0]].bank_account !== r.bank_account) return baoTin('Chọn các dòng cùng một tài khoản ngân hàng.');
      var thieu = Number(kq.so_tien) - tongChon();
      if (thieu <= 0) return baoTin('Đã đủ tiền. Bỏ một dòng trước nếu muốn đổi lựa chọn.');
      chon[ma] = {phan_bo:Math.min(Number(r.con_lai), thieu), bank_account:r.bank_account};
      capNhatTong();
    };
  });
}

async function boBoSepay(loai, ma, ve) {
  var ok = await confirmSheet('Bỏ bộ đối chiếu', 'Bỏ toàn bộ các dòng sao kê đã chọn của phiếu này. Máy không huỷ bút toán; nếu còn chứng từ hiệu lực, kế toán cần xử lý trước. Không chuyển tiền thêm.', 'Bỏ bộ đã chọn', true);
  if (!ok) return;
  busy(true);
  try {
    var kq = await api('vagabond.bo_sao_ke_luong.bo', {loai:loai, ma:ma});
    toast(kq.loi_nhan || 'Đã bỏ bộ đối chiếu.', 6500);
    return ve();
  } catch (e) { return baoTin((e && e.message) || 'Chưa bỏ được bộ đối chiếu.'); }
  finally { busy(false); }
}

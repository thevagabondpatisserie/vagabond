/* Trang /xhd: khach quet QR cuoi bill giay, tu dien thong tin xuat hoa don.
   ERP map thang vao don ban hang; 23h30 he thong tu tao hoa don cho ky ben
   m-invoice, 23h tu ky, hoa don dien tu gui ve email khach trong dem. */
(function () {
  var qs = new URLSearchParams(location.search);
  var D = qs.get('d') || '', T = qs.get('t') || '';
  var goc = document.getElementById('vxThan');
  function h(t) { return String(t == null ? '' : t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
  function goi(m, args) {
    var u = '/api/method/vagabond.ban_hang.' + m + '?' + new URLSearchParams(args).toString();
    return fetch(u, { headers: { Accept: 'application/json' } }).then(function (r) { return r.json(); }).then(function (j) {
      if (j.exc_type || j.exception) {
        var loi = 'Có lỗi, thử lại giúp tiệm.';
        try { loi = JSON.parse(j._server_messages)[0]; loi = JSON.parse(loi).message || loi; } catch (e) { }
        throw new Error(String(loi).replace(/<[^>]+>/g, ''));
      }
      return j.message;
    });
  }
  function tien(n) { return (Math.round(n || 0)).toLocaleString('vi-VN'); }
  if (!D || !T) { goc.innerHTML = '<div class="loi">Đường dẫn không hợp lệ. Anh chị quét lại mã QR trên bill giúp tiệm.</div>'; return; }
  goi('xhd_khach_xem', { d: D, t: T }).then(function (b) {
    if (b.da_xuat) {
      goc.innerHTML = '<div class="ok"><div class="e">✅</div><b>Bill này đã xuất hoá đơn điện tử rồi.</b><div class="phu" style="margin-top:6px">Cần điều chỉnh thông tin thì anh chị liên hệ tiệm giúp em.</div></div>';
      return;
    }
    var ngay = String(b.posting_date || '').split('-').reverse().join('/');
    goc.innerHTML =
      '<h1>Thông tin xuất hoá đơn</h1>' +
      '<div class="phu">Anh chị điền thông tin công ty <b>trước 22h hôm nay</b>.<br>Hoá đơn điện tử sẽ gửi về email trong ngày.</div>' +
      '<div class="card"><div class="dong"><span>Bill</span><b>' + h(D) + '</b></div>' +
      '<div class="dong"><span>Ngày</span><b>' + h(ngay) + '</b></div>' +
      '<div class="dong"><span>Tổng tiền</span><b class="to">' + tien(b.grand_total) + ' đ</b></div></div>' +
      '<div class="card">' +
      '<label>Mã số thuế (10 hoặc 13 số)</label><input id="xMst" inputmode="numeric" value="' + h(b.vgb_xhd_mst) + '" placeholder="Nhập xong máy tự tra tên công ty">' +
      '<div class="bao" id="xBao"></div>' +
      '<label>Tên pháp nhân trên hoá đơn</label><input id="xTen" value="' + h(b.vgb_xhd_ten) + '">' +
      '<label>Địa chỉ trên hoá đơn</label><textarea id="xDc" rows="2">' + h(b.vgb_xhd_dia_chi) + '</textarea>' +
      '<label>Email nhận hoá đơn <span style="color:#ff8a95">*</span></label><input id="xEmail" type="email" value="' + h(b.vgb_xhd_email) + '" placeholder="Bắt buộc - hoá đơn điện tử gửi về đây">' +
      '<button id="xLuu">Lưu thông tin xuất hoá đơn</button></div>';
    var oM = document.getElementById('xMst'), oT = document.getElementById('xTen'),
      oD = document.getElementById('xDc'), oE = document.getElementById('xEmail'),
      oB = document.getElementById('xBao'), oL = document.getElementById('xLuu');
    oM.onblur = function () {
      var so = (oM.value || '').replace(/[^0-9]/g, '');
      if (so.length !== 10 && so.length !== 13) { oB.textContent = so ? 'Mã số thuế phải 10 hoặc 13 số.' : ''; return; }
      oB.textContent = 'Đang tra mã số thuế...';
      goi('xhd_khach_tra_mst', { mst: so }).then(function (kq) {
        if (kq && kq.ok) {
          if (!oT.value.trim()) oT.value = kq.ten || '';
          if (!oD.value.trim()) oD.value = kq.dia_chi || '';
          /* Cong thong tin thue co luc tra ve ten chi co loai hinh phap ly.
             Da xay ra that 22/08/2026. May chu chan lai luc luu, nhung bao
             ngay o day thi khach sua duoc lien. */
          if (kq.nghi_thieu) {
            oB.innerHTML = '<b style="color:#ffb020">Tên công ty tra về bị thiếu.</b> '
              + 'Cổng thuế chỉ trả về "' + h(kq.ten || '') + '". Anh chị xem giấy phép kinh doanh '
              + 'rồi gõ đủ tên vào ô bên dưới giúp tiệm.';
            oT.focus();
          } else oB.textContent = 'Tra được: ' + (kq.ten || '');
        } else oB.textContent = 'Không tra được mã này, anh chị điền tay giúp tiệm.';
      }).catch(function () { oB.textContent = 'Không tra được mã này, anh chị điền tay giúp tiệm.'; });
    };
    oL.onclick = function () {
      var so = (oM.value || '').replace(/[^0-9]/g, '');
      if (so.length !== 10 && so.length !== 13) return alert('Mã số thuế phải 10 hoặc 13 số.');
      if (!oT.value.trim()) return alert('Thiếu tên pháp nhân trên hoá đơn.');
      var mail = (oE.value || '').trim();
      if (!mail || mail.indexOf('@') < 0 || mail.indexOf('.') < 0) return alert('Vui lòng nhập email để tiệm gửi hoá đơn điện tử cho anh chị.');
      oL.disabled = true; oL.textContent = 'Đang lưu...';
      goi('xhd_khach_luu', { d: D, t: T, mst: so, ten: oT.value.trim(), dia_chi: oD.value.trim(), email: oE.value.trim() })
        .then(function () {
          goc.innerHTML = '<div class="ok"><div class="e">🧾</div><b>Đã nhận thông tin xuất hoá đơn!</b>' +
            '<div class="phu" style="margin-top:8px">Hoá đơn điện tử của <b>' + h(oT.value.trim()) + '</b><br>sẽ gửi về <b>' + h(oE.value.trim() || 'email anh chị cung cấp') + '</b> trong ngày.<br><br>The Vagabond Pâtisserie cảm ơn anh chị!</div></div>';
        })
        .catch(function (e) { oL.disabled = false; oL.textContent = 'Lưu thông tin xuất hoá đơn'; alert(e.message || 'Lưu lỗi, thử lại giúp tiệm.'); });
    };
  }).catch(function (e) {
    goc.innerHTML = '<div class="loi">' + h(e.message || 'Không mở được bill này.') + '</div>';
  });
})();

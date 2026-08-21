/* ================= PHIEU THANH TOAN TRUOC CHO NHA CUNG CAP =================
   Anh Viet giao 21/08/2026, sau ca don in an phai tra truoc khi chua co hoa
   don. Bon luong cu cua man Ho so thanh toan deu khong nhan ca nay, xem dau
   tep vagabond/tra_truoc.py.

   Khac ba man kia o mot cho quan trong: man nay KHONG dung Ho so TT, no
   dung thang mot Payment Entry o trang thai nhap roi tha vao workflow
   "Duyet phieu chi APP" da chay san. Ly do: khoan tra truoc phai neo vao
   DON MUA HANG de ERPNext con can tru khi hoa don ve, ma Ho so TT thi neo
   vao hoa don.

   Don mua la mo neo, khong phai ma so thue. Chon don xong la nha cung cap,
   ma so thue, dia chi, so tai khoan tu hien ra tu ho so tren he. */

var ttDon = '', ttChiTiet = null, ttSoTien = 0, ttNguon = '';
var ttLoaiCt = '', ttTep = [], ttGhiChu = '', ttTim = '';
var ttDsDon = null, ttDsNguon = null;

function ttReset() {
  ttDon = ''; ttChiTiet = null; ttSoTien = 0; ttNguon = '';
  ttLoaiCt = ''; ttTep = []; ttGhiChu = ''; ttTim = '';
  ttDsDon = null; ttDsNguon = null;
}

async function ttChonTep() {
  return new Promise(function (ok) {
    var i = document.createElement('input');
    i.type = 'file';
    i.accept = 'image/*,application/pdf';
    i.onchange = function () { ok(i.files && i.files[0]); };
    i.click();
  });
}

async function scrTraTruocTao() {
  frame('Thanh toán trước cho NCC', '<div class="emp"><div class="e1">⏳</div><div>Đang tải đơn mua hàng...</div></div>');
  try {
    if (!ttDsDon) ttDsDon = await api('vagabond.tra_truoc.ds_don_mua', ttTim ? { tu_khoa: ttTim } : {});
    if (!ttDsNguon) ttDsNguon = await api('vagabond.tra_truoc.ds_nguon_tien', {});
  } catch (e) {
    frame('Thanh toán trước cho NCC', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>');
    return;
  }
  var dons = (ttDsDon && ttDsDon.don) || [];
  var nguon = (ttDsNguon && ttDsNguon.nguon) || [];
  if (!ttNguon) {
    var mac = nguon.filter(function (x) { return x.nhom === 'cong_ty'; })[0] || nguon[0];
    if (mac) ttNguon = mac.ma;
  }

  var html = '<div class="card" style="padding:12px 14px;font-size:13px;line-height:1.6;color:#374151">' +
    'Trả trước cho nhà cung cấp khi <b>chưa có hoá đơn</b>, thường là đơn in ấn hay đơn đặt sản xuất có điều khoản đặt cọc.<br>' +
    'Khoản này <b>không phải chi phí</b>. Nó nằm bên Nợ 331 cho tới khi hoá đơn về thì tự cấn trừ, nên phải neo vào một đơn mua hàng.</div>';

  /* ---------- 1. Don mua hang, mo neo ---------- */
  html += '<div class="sec">1 · Đơn mua hàng · bắt buộc</div><div class="card" style="padding:10px 12px">' +
    '<input class="tin" id="ttTim" placeholder="Gõ tên nhà cung cấp để lọc" value="' + h(ttTim) + '" style="margin-bottom:9px">';
  if (!dons.length) {
    html += '<div style="font-size:13px;color:#6b7280;padding:8px 0">Không có đơn mua nào đã duyệt và còn phần chưa trả trước.</div>';
  }
  html += '<div style="max-height:270px;overflow-y:auto">';
  dons.forEach(function (x) {
    var on = ttDon === x.don;
    html += '<div data-ttd="' + h(x.don) + '" style="cursor:pointer;padding:9px 10px;border-radius:9px;margin-bottom:6px;border:1.5px solid ' +
      (on ? '#0f766e' : '#e5e7eb') + ';background:' + (on ? '#f0fdfa' : '#fff') + ';opacity:' + (x.lap_duoc ? '1' : '.5') + '">' +
      '<div style="display:flex;justify-content:space-between;gap:8px">' +
      '<b style="font-size:13px;overflow-wrap:anywhere">' + (on ? '☑️ ' : '') + h(x.ten_ncc) + '</b>' +
      '<span style="font-size:13px;font-weight:800;white-space:nowrap">' + money(x.tong) + ' đ</span></div>' +
      '<div style="font-size:11.5px;color:#6b7280;margin-top:3px">' + h(x.don) + ' · ' + h(hsNgayVn(x.ngay) || x.ngay) +
      (x.da_tra_truoc > 0 ? ' · <span style="color:#0f766e">đã ứng ' + money(x.da_tra_truoc) + '</span>' : '') +
      (x.da_lap_hd > 0 ? ' · đã lập HĐ ' + Math.round(x.da_lap_hd) + '%' : '') + '</div>' +
      (x.lap_duoc ? '' : '<div style="font-size:11.5px;color:#b45309;margin-top:4px">' + h(x.vi_sao) + '</div>') +
      '</div>';
  });
  html += '</div></div>';

  /* ---------- 2. Nha cung cap, chi doc ---------- */
  if (ttChiTiet && ttChiTiet.ncc) {
    var n = ttChiTiet.ncc;
    html += '<div class="sec">2 · Nhà cung cấp · máy lấy từ đơn</div><div class="card" style="padding:10px 12px;font-size:13px;line-height:1.7">' +
      '<div><b>' + h(n.ten || '') + '</b></div>' +
      '<div style="color:#6b7280">Mã số thuế: ' + (n.mst ? h(n.mst) : '<span style="color:#b45309">chưa khai trên hồ sơ NCC</span>') + '</div>' +
      (n.dia_chi ? '<div style="color:#6b7280">Địa chỉ: ' + h(n.dia_chi) + '</div>' : '') +
      (n.tai_khoan && n.tai_khoan.so_tk
        ? '<div style="color:#6b7280">Số tài khoản: ' + h(n.tai_khoan.so_tk) + (n.tai_khoan.ngan_hang ? ' · ' + h(n.tai_khoan.ngan_hang) : '') + '</div>'
        : '<div style="color:#b45309">Hồ sơ NCC chưa có số tài khoản nhận tiền. Kế toán tra lại trước khi chuyển.</div>') +
      (n.mst ? '<button class="btn gh" id="ttTraMst" style="margin-top:9px">🔎 Đối chiếu tên với cơ quan thuế</button>' : '') +
      '</div>';
  }

  /* ---------- 3. So tien ---------- */
  if (ttChiTiet && ttChiTiet.lap_duoc) {
    html += '<div class="sec">3 · Số tiền trả trước</div><div class="card" style="padding:10px 12px">' +
      '<input class="tin" id="ttTien" inputmode="numeric" placeholder="0" value="' + (ttSoTien ? money(ttSoTien) : '') + '" style="font-size:20px;font-weight:800;text-align:right">' +
      '<div style="font-size:12px;color:#6b7280;margin-top:7px;line-height:1.5">Nhiều nhất <b>' + money(ttChiTiet.tran) + ' đ</b>, là phần còn lại của đơn sau khi trừ khoản đã ứng.</div>' +
      kmHangChip([25, 30, 50, 70, 100].map(function (p) {
        return posChipNut('data-ttp="' + p + '"', p + '%', false);
      }).join('')) + '</div>';
  }

  /* ---------- 4. Nguon tien ---------- */
  if (ttChiTiet && ttChiTiet.lap_duoc) {
    var cty = nguon.filter(function (x) { return x.nhom === 'cong_ty'; });
    var tu = nguon.filter(function (x) { return x.nhom === 'tam_ung'; });
    html += '<div class="sec">4 · Tiền đi ra từ đâu</div><div class="card" style="padding:10px 12px">' +
      '<div style="font-size:11.5px;color:#6b7280;font-weight:800;margin-bottom:6px">TÀI KHOẢN CÔNG TY</div>' +
      kmHangChip(cty.map(function (x) {
        return posChipNut('data-ttn="' + h(x.ma) + '"', h(x.so_hieu) + ' · ' + h(x.nhan.replace(/^[^·]*· /, '')), ttNguon === x.ma);
      }).join(''));
    if (tu.length) {
      html += '<div style="font-size:11.5px;color:#6b7280;font-weight:800;margin:11px 0 6px">QUỸ TẠM ỨNG CÁ NHÂN</div>' +
        kmHangChip(tu.map(function (x) {
          return posChipNut('data-ttn="' + h(x.ma) + '"', h(x.so_hieu) + ' · ' + h(x.nhan.replace(/^[^·]*· /, '')), ttNguon === x.ma);
        }).join('')) +
        '<div style="font-size:12px;color:#b45309;margin-top:8px;line-height:1.5">' +
        'Quỹ tạm ứng đứng tên cá nhân, không phải quỹ của bộ phận mua hàng. Chi từ đây là cá nhân bỏ tiền ra trước, sau vẫn phải đi tiếp đường hoàn ứng để công ty trả lại.</div>';
    }
    html += '</div>';
  }

  /* ---------- 5. Chung tu ---------- */
  if (ttChiTiet && ttChiTiet.lap_duoc) {
    var dsCt = (ttChiTiet.loai_chung_tu) || [];
    html += '<div class="sec">5 · Chứng từ đính kèm · bắt buộc</div><div class="card" style="padding:10px 12px">' +
      kmHangChip(dsCt.map(function (x) {
        return posChipNut('data-ttc="' + h(x) + '"', h(x), ttLoaiCt === x);
      }).join(''));
    if (!ttLoaiCt) {
      html += '<div style="font-size:12.5px;color:#b45309;margin-top:8px">Chọn loại chứng từ trước, em mới bày nút đính kèm.</div>';
    } else {
      html += '<div style="margin-top:9px">';
      ttTep.forEach(function (t, i) {
        html += '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;padding:6px 0;border-top:1px solid #f1f5f9">' +
          '<span style="flex:1 1 auto;min-width:0;font-size:12.5px;color:#0f766e;overflow-wrap:anywhere">📎 ' + h(t.ten) + '</span>' +
          '<button class="btn gh" data-ttx="' + i + '" style="flex:0 0 auto;width:auto;margin:0;padding:4px 9px;font-size:12px">Bỏ</button></div>';
      });
      html += '<button class="btn gh" id="ttGanTep" style="margin-top:9px">➕ Đính kèm ' + h(ttLoaiCt) + '</button></div>';
    }
    html += '<div style="font-size:12px;color:#6b7280;margin-top:8px;line-height:1.5">Khoản này chưa có hoá đơn, nên báo giá hoặc hợp đồng chính là căn cứ duy nhất. Không có tệp thì không lập được phiếu.</div></div>';

    html += '<div class="card" style="padding:12px 14px"><input class="tin" id="ttGc" placeholder="Ghi chú cho kế toán (không bắt buộc)" value="' + h(ttGhiChu) + '"></div>';

    html += '<div class="card" style="padding:12px 14px;background:#f0fdfa;border:1.5px solid #99f6e4;font-size:12.5px;color:#0f766e;line-height:1.6">' +
      'Bấm lập thì phiếu ở trạng thái <b>Nháp</b>, tiền chưa đi đâu cả. Phiếu chạy tiếp: kế toán kiểm tra, rồi giám đốc duyệt chi, lúc đó mới ghi sổ.</div>';
  }

  var foot = (ttChiTiet && ttChiTiet.lap_duoc)
    ? '<button class="btn" id="ttLap">📤 Lập phiếu và gửi kế toán</button>'
    : '';
  var b = frame('Thanh toán trước cho NCC', html, foot ? { footer: foot } : undefined);

  var ot = document.getElementById('ttTim');
  if (ot) ot.onchange = function () { ttTim = ot.value.trim(); ttDsDon = null; go(scrTraTruocTao, true); };

  var oTien = document.getElementById('ttTien');
  if (oTien) oTien.oninput = function () {
    var v = Number(String(oTien.value).replace(/\D/g, '')) || 0;
    var tr = Number((ttChiTiet && ttChiTiet.tran) || 0);
    if (v > tr) v = tr;
    ttSoTien = v;
    oTien.value = v ? money(v) : '';
  };

  b.addEventListener('click', async function (e) {
    var rd = e.target.closest('[data-ttd]');
    if (rd) {
      var ma = rd.getAttribute('data-ttd');
      if (ttDon === ma) return;
      ttDon = ma; ttSoTien = 0; ttChiTiet = null;
      busy(true);
      try { ttChiTiet = await api('vagabond.tra_truoc.chi_tiet_don', { don: ma }); }
      catch (er) { busy(false); ttDon = ''; return baoTin((er && er.message) || 'Không đọc được đơn'); }
      busy(false);
      return go(scrTraTruocTao, true);
    }
    var rp = e.target.closest('[data-ttp]');
    if (rp && ttChiTiet) {
      var pt = Number(rp.getAttribute('data-ttp')) || 0;
      ttSoTien = Math.round(Number(ttChiTiet.tong || 0) * pt / 100);
      if (ttSoTien > Number(ttChiTiet.tran || 0)) ttSoTien = Number(ttChiTiet.tran || 0);
      return go(scrTraTruocTao, true);
    }
    var rn = e.target.closest('[data-ttn]');
    if (rn) { ttNguon = rn.getAttribute('data-ttn'); return go(scrTraTruocTao, true); }
    var rc = e.target.closest('[data-ttc]');
    if (rc) { ttLoaiCt = rc.getAttribute('data-ttc'); return go(scrTraTruocTao, true); }
    var rx = e.target.closest('[data-ttx]');
    if (rx) { ttTep.splice(+rx.getAttribute('data-ttx'), 1); return go(scrTraTruocTao, true); }
  });

  var ng = document.getElementById('ttGanTep');
  if (ng) ng.onclick = async function () {
    var f = await ttChonTep();
    if (!f) return;
    busy(true);
    try { ttTep.push(await huUpTep(f)); busy(false); go(scrTraTruocTao, true); }
    catch (er) { busy(false); baoTin((er && er.message) || 'Không tải được tệp'); }
  };

  var nm = document.getElementById('ttTraMst');
  if (nm) nm.onclick = async function () {
    var mst = (ttChiTiet && ttChiTiet.ncc && ttChiTiet.ncc.mst) || '';
    if (!mst) return;
    busy(true);
    var kq = null;
    try { kq = await api('vagabond.api.tra_mst', { mst: mst }); } catch (er) { }
    busy(false);
    if (!kq || !kq.ok) return baoTin('Cổng thuế không tìm thấy mã số ' + mst + '. Kiểm lại hồ sơ nhà cung cấp.');
    var tenHe = String((ttChiTiet.ncc.ten || '')).trim().toUpperCase();
    var tenThue = String(kq.ten || '').trim().toUpperCase();
    baoTin('Cơ quan thuế: ' + (kq.ten || '') + (kq.dia_chi ? '\n' + kq.dia_chi : '') +
      (tenHe && tenThue && tenHe !== tenThue ? '\n\n⚠️ Tên trên hệ đang khác tên đăng ký. Kế toán soát lại hồ sơ NCC.' : ''));
  };

  var nl = document.getElementById('ttLap');
  if (nl) nl.onclick = async function () {
    if (!ttDon) return baoTin('Chưa chọn đơn mua hàng.');
    if (!ttSoTien) return baoTin('Chưa nhập số tiền trả trước.');
    if (!ttNguon) return baoTin('Chưa chọn tiền đi ra từ tài khoản nào.');
    if (!ttLoaiCt) return baoTin('Chưa chọn loại chứng từ đính kèm.');
    if (!ttTep.length) return baoTin('Chưa đính kèm chứng từ nào. Khoản trả trước chưa có hoá đơn nên bắt buộc phải có báo giá hoặc hợp đồng.');
    var og = document.getElementById('ttGc');
    if (og) ttGhiChu = og.value.trim();
    var xac = await hoiChon('Lập phiếu trả trước',
      'Trả trước ' + money(ttSoTien) + ' đ cho ' + ((ttChiTiet.ncc && ttChiTiet.ncc.ten) || '') + ', đơn ' + ttDon +
      '. Phiếu lập ra ở trạng thái Nháp, tiền chưa đi đâu cả.',
      [{ k: 'ok', icon: '📤', nhan: 'Lập phiếu', mo_ta: 'Gửi cho kế toán kiểm tra.' }]);
    if (xac !== 'ok') return;
    busy(true);
    var kq;
    try {
      kq = await api('vagabond.tra_truoc.tao_phieu', {
        don: ttDon, so_tien: ttSoTien, nguon_tien: ttNguon,
        loai_chung_tu: ttLoaiCt, tep: JSON.stringify(ttTep), ghi_chu: ttGhiChu
      });
    } catch (er) { busy(false); return baoTin((er && er.message) || 'Không lập được phiếu'); }
    busy(false);
    baoTin((kq && kq.nhan) || 'Đã lập phiếu.');
    ttReset();
    go(scrHoSoTT ? scrHoSoTT : scrTraTruocTao);
  };
}

/* ---------------- Khối Hàng tặng dùng chung: lý do chọn sẵn (v607)

   Anh Việt 20/10/2026, sau đơn #95631 cửa hàng bảo đã ghi lý do mà vẫn
   mất: *"Cho liệt kê những lý do ra cho anh duyệt rồi map lên để chỉ việc
   chọn chứ không cần phải viết tay mất thời gian"*.

   MỘT khối cho cả hai màn Bill quầy và Doanh thu Sales. Hai màn hai bản là
   hai bản sẽ lệch nhau, mà lỗi gốc chính là một màn có ô lý do còn màn kia
   không có.

   Danh sách loại và lý do ĐỌC TỪ MÁY CHỦ (hang_tang.cai_dat), màn hình không
   tự chép. Lưu bằng MỘT cửa (hang_tang.luu_tang): phương thức, loại, lý do,
   ảnh cùng một lần, thiếu là không lưu gì.

   Ghi chú Pancake CHỈ hiện để bấm chép (anh Việt chọn), không tự đổ vào. */
var TANG_CD = null;

async function tangCaiDat() {
  if (TANG_CD) return TANG_CD;
  TANG_CD = await api('vagabond.hang_tang.cai_dat', {});
  return TANG_CD;
}

/* Trạng thái chọn của từng khối, theo tiền tố id ('pb' bill quầy, 'dsv'
   doanh thu Sales). Giữ ngoài DOM để vẽ lại phần lý do khi đổi loại mà
   không mất người nhận đã gõ. */
var tangChon = {};

function tangLyDoCua(cd, loai) {
  return ((cd && cd.ly_do_san) || []).filter(function (r) { return r.loai === loai; });
}

/* Tách lý do đã lưu "<nhãn>: <phần thêm>" ra lại mã và phần thêm, để mở
   lại một đơn đã khai thì khối hiện đúng cái đã chọn. Đơn cũ gõ tay tự do
   thì không tách được, để trống cho người lập chọn lại. */
function tangTachCu(cd, d) {
  var ma = String(d.vgb_tang_ma_ly_do || '');
  var ly = String(d.vgb_tang_ly_do || '');
  var r = ((cd && cd.ly_do_san) || []).filter(function (x) { return x.ma === ma; })[0];
  if (!r) return { loai: String(d.vgb_tang_loai || ''), ma: '', them: '' };
  var them = ly.indexOf(r.nhan + ': ') === 0 ? ly.slice(r.nhan.length + 2) : '';
  return { loai: r.loai, ma: r.ma, them: them };
}

/* Kiểm như máy chủ để nút sáng hay mờ và nói thiếu gì. Máy chủ vẫn kiểm
   lại, đây chỉ để người lập thấy trước. */
function tangThieu(cd, st, soAnh) {
  if (!st.loai) return 'Chọn loại tặng.';
  var r = ((cd && cd.ly_do_san) || []).filter(function (x) { return x.ma === st.ma; })[0];
  if (!r) return 'Chọn lý do tặng.';
  var t = String(st.them || '').replace(/\s+/g, ' ').trim();
  if (r.can && t.length < (r.toi_thieu || 0)) {
    return r.can === 'tay'
      ? 'Ghi rõ lý do, ít nhất ' + r.toi_thieu + ' ký tự: tặng cho ai, vì việc gì.'
      : 'Điền ' + String(r.nhan_can || '').toLowerCase() + '.';
  }
  if ((cd.loai_can_anh || []).indexOf(st.loai) >= 0 && !soAnh) {
    return 'Đơn Đền bù sự cố phải đính ít nhất một ảnh chứng minh.';
  }
  return '';
}

function tangSoanXem(cd, st) {
  var r = ((cd && cd.ly_do_san) || []).filter(function (x) { return x.ma === st.ma; })[0];
  if (!r) return '';
  var t = String(st.them || '').replace(/\s+/g, ' ').trim();
  return t ? r.nhan + ': ' + t : r.nhan;
}

/* Vẽ phần chọn (chip loại, danh sách lý do, ô thêm, ghi chú Pancake, ảnh,
   nút lưu) vào `o`. Gọi lại mỗi lần đổi loại hay lý do. */
function tangVeForm(px, o, cd, st, gy) {
  var s = '<div style="font-size:13px;font-weight:700;margin:2px 0 6px">Loại tặng <b style="color:#b3261e">*</b></div>' +
    '<div id="' + px + 'TgLoai" style="display:flex;flex-wrap:wrap;gap:6px">' +
    (cd.chip_loai || []).map(function (c) {
      var on = c.k === st.loai;
      return '<button type="button" data-tgl="' + h(c.k) + '" style="min-height:40px;padding:7px 11px;' +
        'border-radius:10px;font-size:13px;cursor:pointer;border:1.5px solid ' +
        (on ? '#0d9488;background:#f0fdfa;color:#0f766e;font-weight:700' : '#e4e7eb;background:#fff;color:#344054') +
        '">' + h(c.ten) + '</button>';
    }).join('') + '</div>';
  if (st.loai) {
    s += '<div style="font-size:13px;font-weight:700;margin:12px 0 6px">Lý do <b style="color:#b3261e">*</b></div>' +
      '<div id="' + px + 'TgLyDo" style="display:grid;gap:6px">' +
      tangLyDoCua(cd, st.loai).map(function (r) {
        var on = r.ma === st.ma;
        return '<button type="button" data-tgm="' + h(r.ma) + '" style="display:flex;gap:9px;align-items:center;' +
          'text-align:left;min-height:44px;padding:9px 10px;border-radius:10px;font-size:13.5px;cursor:pointer;' +
          'border:1.5px solid ' + (on ? '#0d9488;background:#f0fdfa' : '#e4e7eb;background:#fff') + '">' +
          '<span style="width:18px;height:18px;border-radius:50%;flex:none;border:' +
          (on ? '6px solid #0d9488' : '2px solid #9aa5b1') + '"></span>' +
          '<span style="flex:1;min-width:0">' + h(r.nhan) +
          (r.can ? '<small style="display:block;color:#7b8794;font-size:11.5px">Cần ghi: ' + h(r.nhan_can) + '</small>' : '') +
          '</span></button>';
      }).join('') + '</div>';
  }
  var r = (cd.ly_do_san || []).filter(function (x) { return x.ma === st.ma; })[0];
  if (r && r.can) {
    s += '<div style="font-size:13px;font-weight:700;margin:12px 0 6px">' + h(r.nhan_can) +
      ' <b style="color:#b3261e">*</b></div>' +
      (r.can === 'tay'
        ? '<textarea class="tin" id="' + px + 'TgThem" rows="2" style="margin:0" placeholder="Tặng cho ai, vì việc gì">' +
          h(st.them || '') + '</textarea>'
        : '<input class="tin" id="' + px + 'TgThem" style="margin:0" value="' + h(st.them || '') + '" placeholder="' +
          h(r.nhan_can) + '">') +
      (r.can === 'nguoi' && gy && gy.khach
        ? '<div style="font-size:12px;color:#7b8794;margin-top:4px">Máy lấy sẵn tên khách trên đơn, sửa được.</div>' : '');
  }
  if (gy && gy.ghi_chu_pancake) {
    s += '<div style="margin-top:10px;padding:8px 10px;background:#f1f5f9;border-radius:9px;font-size:12.5px;' +
      'color:#3e4c59;display:flex;gap:8px;align-items:center">' +
      '<span style="flex:1;min-width:0">Ghi chú Pancake: "' + h(gy.ghi_chu_pancake) + '"</span>' +
      (r && r.can ? '<button type="button" class="btn gh" data-tgchep style="margin:0;padding:6px 10px;min-height:36px;' +
        'font-size:12.5px;width:auto">Chép vào</button>' : '') + '</div>';
  }
  s += '<label class="tin" style="margin:10px 0 0;display:flex;align-items:center;gap:9px;cursor:pointer">' +
    '<input type="file" accept="image/*" id="' + px + 'TgAnh" multiple style="display:none">' +
    '<span style="font-size:19px">📷</span>' +
    '<span style="font-size:13px;color:#475467" id="' + px + 'TgAnhT">' +
    (st.anh.length ? 'Đã chọn ' + st.anh.length + ' ảnh' : (st.soAnhCu ? 'Đã có ' + st.soAnhCu + ' ảnh, đính thêm' : 'Đính ảnh chứng minh')) +
    '</span></label>';
  var xem = tangSoanXem(cd, st);
  var thieu = tangThieu(cd, st, st.anh.length + (st.soAnhCu || 0));
  if (xem) {
    s += '<div style="margin-top:10px;padding:8px 10px;background:#f8fafc;border-radius:9px;font-size:12.5px;color:#3e4c59">' +
      'Lưu thành: <b id="' + px + 'TgXem">' + h(xem) + '</b></div>';
  }
  s += '<div id="' + px + 'TgThieu" style="margin-top:8px;font-size:12.5px;color:#b3261e;line-height:1.5;display:' +
    (thieu ? 'block' : 'none') + '">' + h(thieu) + '</div>' +
    '<button class="btn" id="' + px + 'TgLuu" style="margin:8px 0 0;' + (thieu ? 'opacity:.55' : '') + '">' +
    '🎁 Lưu và gửi giám đốc duyệt</button>';
  o.innerHTML = s;
}

/* Gắn khối vào màn. `layGhiChu` trả ghi chú hoá đơn đang gõ (hoặc null để
   giữ nguyên), `sauLuu` chạy khi lưu xong. */
async function tangGan(px, d, layGhiChu, sauLuu) {
  var o = document.getElementById(px + 'TgForm');
  if (!o) return;
  var cd, gy = {};
  try {
    cd = await tangCaiDat();
  } catch (e) {
    o.innerHTML = '<div style="font-size:12.5px;color:#b3261e">Không tải được danh sách lý do tặng: ' +
      h(errMsg(e)) + '. Tải lại màn.</div>';
    return;
  }
  try { gy = await api('vagabond.hang_tang.goi_y', { name: d.name }); } catch (e) { gy = {}; }
  var st = tangChon[px + d.name];
  if (!st) {
    st = tangTachCu(cd, d);
    st.anh = [];
    st.soAnhCu = gy.so_anh || 0;
    tangChon[px + d.name] = st;
  }
  function ve() {
    var o2 = document.getElementById(px + 'TgForm');
    if (!o2) return;
    tangVeForm(px, o2, cd, st, gy);
  }
  ve();
  o.onclick = async function (ev) {
    var t = ev.target.closest('[data-tgl]');
    if (t) {
      var k = t.getAttribute('data-tgl');
      if (k !== st.loai) { st.loai = k; st.ma = ''; st.them = ''; }
      return ve();
    }
    t = ev.target.closest('[data-tgm]');
    if (t) {
      st.ma = t.getAttribute('data-tgm');
      var r = (cd.ly_do_san || []).filter(function (x) { return x.ma === st.ma; })[0];
      /* Người nhận để trống thì lấy sẵn tên khách trên đơn. */
      if (r && r.can === 'nguoi' && !String(st.them || '').trim() && gy.khach) st.them = gy.khach;
      if (r && r.can !== 'nguoi' && st.them === gy.khach) st.them = '';
      return ve();
    }
    if (ev.target.closest('[data-tgchep]')) {
      var oi = document.getElementById(px + 'TgThem');
      st.them = ((oi && oi.value) ? oi.value.trim() + ' ' : '') + (gy.ghi_chu_pancake || '');
      return ve();
    }
    if (ev.target.id === px + 'TgLuu') {
      var thieu = tangThieu(cd, st, st.anh.length + (st.soAnhCu || 0));
      if (thieu) return toast(thieu, 4500);
      busy(true);
      try {
        var kq = await api('vagabond.hang_tang.luu_tang', {
          name: d.name, ma_ly_do: st.ma, them: st.them || '',
          anh: st.anh.length ? JSON.stringify(st.anh) : '',
          ghi_chu: layGhiChu ? layGhiChu() : null,
        });
        busy(false);
        delete tangChon[px + d.name];
        toast((kq.cau_thieu || []).length ? kq.cau_thieu[0] : 'Đã lưu và gửi giám đốc duyệt đơn tặng.', 5000);
        if (sauLuu) sauLuu(kq);
      } catch (e) { busy(false); baoTin(errMsg(e), 'Chưa lưu đơn tặng'); }
    }
  };
  o.oninput = function (ev) {
    if (ev.target.id !== px + 'TgThem') return;
    st.them = ev.target.value;
    var thieu = tangThieu(cd, st, st.anh.length + (st.soAnhCu || 0));
    var ot = document.getElementById(px + 'TgThieu');
    if (ot) { ot.textContent = thieu; ot.style.display = thieu ? 'block' : 'none'; }
    var nl = document.getElementById(px + 'TgLuu');
    if (nl) nl.style.opacity = thieu ? '.55' : '';
    var ox = document.getElementById(px + 'TgXem');
    if (ox) ox.textContent = tangSoanXem(cd, st);
  };
  o.onchange = function (ev) {
    if (ev.target.id !== px + 'TgAnh') return;
    var cac = Array.prototype.slice.call(ev.target.files || []);
    if (!cac.length) return;
    st.anh = [];
    var con = cac.length;
    cac.forEach(function (f) {
      var fr = new FileReader();
      fr.onload = function () {
        st.anh.push({ ten: f.name, noi_dung: String(fr.result || '') });
        if (!--con) ve();
      };
      fr.onerror = function () { if (!--con) ve(); };
      fr.readAsDataURL(f);
    });
  };
}

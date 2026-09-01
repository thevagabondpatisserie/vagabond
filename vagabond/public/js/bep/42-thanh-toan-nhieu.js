/* ---------------- Một đơn trả bằng NHIỀU phương thức

   Anh Việt 01/09/2026: bên Loan Anh vướng chuyện khách trả một đơn bằng
   hai đường - chuyển khoản trước một phần, tới cửa hàng đưa nốt tiền mặt.
   Đơn 92857 ngày 31/08 là ví dụ thật: 2.000.000 tiền mặt cộng 225.000 quẹt
   thẻ, tổng 2.225.000.

   Ô "Phương thức thanh toán" ở màn chi tiết chỉ chứa được MỘT tên nên bạn
   nhập phải chọn một cái, và sổ ghi cả 2.225.000 vào tiền mặt. Két tiền
   cuối ca lệch đúng 225.000 mà không ai truy ra được, vì sổ nói tiền mặt.

   Màn này KHÔNG thay ô cũ. Ô cũ vẫn còn và vẫn là ô chính; nó tự mang dòng
   có số tiền lớn nhất. Xem đầu tệp vagabond/thanh_toan_nhieu.py để biết vì
   sao giữ, và những chỗ nào còn đang đọc ô cũ. */

var ttnState = null;

function ttnMoney(v) {
  return (Math.round(v || 0)).toLocaleString('vi-VN');
}

/* Dòng tóm tắt vẽ ngay dưới hàng chip phương thức ở màn chi tiết đơn. */
function ttnTomTat(x) {
  if (!x || !(x.dong || []).length) {
    return '<button class="btn gh" id="ttnMo" style="margin-top:8px">' +
      '➕ Khách trả bằng nhiều đường</button>';
  }
  var chip = x.dong.map(function (d) {
    return '<i>' + h(d.pt) + ' ' + ttnMoney(d.so_tien) + '</i>';
  }).join('');
  var canh = Math.abs(x.lech || 0) > 1
    ? '<div style="font-size:12px;color:#b3261e;margin-top:5px;line-height:1.45">' +
      'Các dòng cộng lại ' + ttnMoney(x.tong_dong) + ', tổng đơn ' +
      ttnMoney(x.tong_don) + '. Lệch ' + ttnMoney(Math.abs(x.lech)) +
      ', chưa ghi sổ được.</div>' : '';
  return '<div style="margin-top:8px">' +
    '<div class="noi">' + chip + '</div>' + canh +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:5px;line-height:1.45">' +
    'Ô phương thức ở trên mang dòng lớn nhất. Màn chốt ca đếm theo từng dòng.</div>' +
    '<button class="btn gh" id="ttnMo" style="margin-top:8px">✏️ Sửa cách chia tiền</button>' +
    '</div>';
}

/* Nạp và vẽ khối này vào một ô sẵn có trên màn chi tiết đơn. */
async function ttnVe(oId, si, tongDon, cacPt) {
  var o = document.getElementById(oId);
  if (!o) return;
  var x = null;
  try { x = await api('vagabond.thanh_toan_nhieu.xem', { si: si }); }
  catch (e) { o.innerHTML = ''; return; }
  ttnState = { si: si, tong_don: tongDon, pt: cacPt || [], x: x };
  /* Đơn đã ghi sổ thì chỉ cho XEM. Đổi cách chia tiền của một tờ đã vào sổ
     là đổi số của ca đã chốt; việc đó đi đường huỷ và lập lại như mọi sửa
     đổi sau ghi sổ khác, không mở thêm một cửa lặng lẽ. */
  o.innerHTML = ttnTomTat(x);
  if (x.da_ghi_so) {
    var n = document.getElementById('ttnMo');
    if (n) n.remove();
    return;
  }
  var b = document.getElementById('ttnMo');
  if (b) b.onclick = function () { ttnSheet(); };
}

function ttnSheet() {
  var st = ttnState;
  if (!st) return;
  var dong = (st.x.dong || []).map(function (d) {
    return { pt: d.pt, so_tien: d.so_tien };
  });
  if (!dong.length) {
    /* Mở lần đầu thì dựng sẵn hai dòng: ô trên đang chọn gì thì dòng một
       mang cái đó, và số tiền để TRỐNG chứ không điền sẵn tổng đơn. Điền
       sẵn thì bấm Lưu ngay là ghi một dòng bằng cả đơn, tức không chia gì
       cả mà nhìn vào tưởng đã chia. */
    dong = [{ pt: st.x.pt_chinh || '', so_tien: 0 }, { pt: '', so_tien: 0 }];
  }

  var ov = document.createElement('div'); ov.className = 'sh';
  document.body.appendChild(ov);

  function tong() {
    return dong.reduce(function (a, d) { return a + (d.so_tien || 0); }, 0);
  }
  function ve() {
    var t = tong(), lech = Math.round(t - st.tong_don);
    var hang = dong.map(function (d, i) {
      var op = '<option value="">Chọn phương thức</option>' +
        st.pt.map(function (p) {
          return '<option value="' + h(p) + '"' + (p === d.pt ? ' selected' : '') +
            '>' + h(p) + '</option>';
        }).join('');
      return '<div style="display:flex;gap:8px;align-items:center;margin-bottom:9px">' +
        '<select class="uom" data-ttnpt="' + i + '" style="flex:1;min-width:0">' + op + '</select>' +
        '<input type="number" inputmode="numeric" class="khsx-o" data-ttnso="' + i + '" ' +
        'style="width:118px;text-align:right" value="' + (d.so_tien || '') + '">' +
        '<div class="del" data-ttnxoa="' + i + '">&times;</div></div>';
    }).join('');
    ov.innerHTML = '<div class="shb" style="padding:18px 16px calc(env(safe-area-inset-bottom,0px) + 16px);max-height:86vh;overflow:auto">' +
      '<div style="font-size:17.5px;font-weight:700;margin-bottom:4px">Khách trả bằng nhiều đường</div>' +
      '<div style="font-size:12.5px;color:#8a8f9c;margin-bottom:12px;line-height:1.5">' +
      'Mỗi đường một dòng. Cộng lại phải đúng bằng tổng đơn thì mới ghi sổ được. ' +
      'Ô Phương thức ở màn ngoài sẽ tự mang dòng lớn nhất.</div>' +
      hang +
      '<button class="btn gh" data-ttnthem style="margin-bottom:12px">+ Thêm một đường</button>' +
      '<div style="display:flex;justify-content:space-between;font-size:13.5px;padding:8px 0;border-top:1px dashed #e6e8ec">' +
      '<span style="color:#667085">Tổng đơn</span><b>' + ttnMoney(st.tong_don) + '</b></div>' +
      '<div style="display:flex;justify-content:space-between;font-size:13.5px;padding:2px 0">' +
      '<span style="color:#667085">Các dòng cộng lại</span><b>' + ttnMoney(t) + '</b></div>' +
      (Math.abs(lech) > 1
        ? '<div style="font-size:12.5px;color:#b3261e;margin-top:6px;line-height:1.5">' +
          (lech > 0 ? 'Thừa ' : 'Thiếu ') + ttnMoney(Math.abs(lech)) +
          '. Sửa cho khớp rồi mới lưu được.</div>'
        : '<div style="font-size:12.5px;color:#0d8a45;margin-top:6px">Khớp tổng đơn.</div>') +
      '<button class="btn gr" data-ttnluu style="margin-top:14px"' +
      (Math.abs(lech) > 1 ? ' disabled' : '') + '>Lưu cách chia</button>' +
      '<button class="btn gh" data-ttnhuy style="margin-top:9px">Đóng</button></div>';
  }
  ve();

  ov.addEventListener('change', function (e) {
    var t = e.target;
    if (t.dataset.ttnpt != null) { dong[+t.dataset.ttnpt].pt = t.value; ve(); }
  });
  ov.addEventListener('input', function (e) {
    var t = e.target;
    if (t.dataset.ttnso != null) {
      dong[+t.dataset.ttnso].so_tien = Math.max(0, parseFloat(t.value) || 0);
      /* Vẽ lại CẢ khối thì ô đang gõ mất con trỏ. Chỉ cập nhật hai dòng
         tổng và trạng thái nút. */
      var t2 = tong(), l2 = Math.round(t2 - st.tong_don);
      var b = ov.querySelector('[data-ttnluu]');
      if (b) b.disabled = Math.abs(l2) > 1;
    }
  });
  ov.onclick = async function (e) {
    var t = e.target;
    if (t.dataset && t.dataset.ttnxoa != null) {
      dong.splice(+t.dataset.ttnxoa, 1);
      if (!dong.length) dong.push({ pt: '', so_tien: 0 });
      return ve();
    }
    if (t.hasAttribute && t.hasAttribute('data-ttnthem')) {
      dong.push({ pt: '', so_tien: 0 }); return ve();
    }
    if ((t.hasAttribute && t.hasAttribute('data-ttnhuy')) || t === ov) {
      return ov.remove();
    }
    if (t.hasAttribute && t.hasAttribute('data-ttnluu')) {
      var sach = dong.filter(function (d) { return d.pt && d.so_tien > 0; });
      if (sach.length < 2) {
        return toast('Cần ít nhất hai đường có số tiền. Một đường thì chọn thẳng ở ô Phương thức.', 6000);
      }
      busy(1);
      try {
        var r = await api('vagabond.thanh_toan_nhieu.luu', {
          si: st.si, dong: JSON.stringify(sach),
        });
        busy(0);
        ov.remove();
        toast('Đã lưu cách chia tiền. Ô phương thức giờ mang ' +
          (r.pt_chinh || 'dòng lớn nhất') + '.', 5000);
        go(function () { scrDsView(st.si, 0); }, true);
      } catch (err) { busy(0); toast(errMsg(err), 8000); }
    }
  };
}

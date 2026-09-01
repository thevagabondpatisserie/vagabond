/* ============ Ô TẢI TỆP DÙNG CHUNG CHO MỌI MÀN (anh Việt 01/09/2026) ======

Anh Việt: *"cho đính kèm nhiều file, hiện dạng thumbnail, tự nén file nhỏ để
đỡ tốn database... những cái này là cái em phải ghi vào backend mỗi khi dựng
màn nào có nút tải tệp lên"*.

Đây là bản ở MÀN HÌNH của luật đó. Bản ở máy chủ nằm ở vagabond/tep_dinh_kem.py.
Màn nào có nút tải tệp thì gọi ba hàm dưới, KHÔNG chép lại đoạn nén ảnh.

  tdkKhoi(id, tuychon)   trả về đoạn HTML của ô tải tệp
  tdkNoi(khung, id)      nối sự kiện sau khi đã vẽ khung
  tdkDs(id)              danh sách đường dẫn tệp của ô đó, để gửi lên máy chủ

BỐN VIỆC Ô NÀY LÀM MÀ MẮT KHÔNG THẤY

1. NÉN ẢNH NGAY TRÊN MÁY NGƯỜI DÙNG trước khi gửi đi. Ảnh điện thoại giờ 4
   tới 8 MB một tấm. Cạnh dài hạ về 1600px, chất lượng 0.72, ra khoảng 200
   tới 400 KB. Nhìn trên màn hình không khác gì, mà nhẹ hơn hai chục lần.
   Nén ở đây chứ không ở máy chủ: nén ở máy chủ thì tấm 8 MB vẫn phải đi hết
   đường 4G của bạn nhân viên đứng trong bếp.

2. XOAY ẢNH VỀ ĐÚNG CHIỀU. Ảnh chụp dọc trên iPhone mang cờ xoay trong dữ
   liệu EXIF; vẽ thẳng lên canvas là mất cờ đó và tấm ảnh nằm ngang. Dùng
   createImageBitmap với imageOrientation 'from-image' thì trình duyệt tự
   xoay hộ. Máy cũ không có hàm đó thì rơi về đường vẽ thẳng, ảnh vẫn lên.

3. TỆP PDF THÌ KHÔNG ĐỤNG. Nén một tờ PDF bằng canvas là biến nó thành ảnh,
   mất chữ, mất khả năng tìm kiếm.

4. TẢI LÊN TỪNG TỆP MỘT, hiện vòng quay riêng cho từng tệp. Gửi cả năm tấm
   một lượt thì mạng yếu là hỏng cả năm, mà người dùng không biết hỏng cái
   nào. */

/* Kho tệp theo từng ô trên màn đang mở. Xoá khi rời màn: giữ lại thì mở
   phiếu khác vẫn thấy tệp của phiếu trước. */
var TDK = {};

var TDK_CANH = 1600;      /* cạnh dài tối đa sau khi nén */
var TDK_CHAT = 0.72;      /* chất lượng JPEG */
var TDK_SO = 12;          /* số tệp tối đa một ô, khớp CAP_SO_TEP máy chủ */
var TDK_CAP = 15 * 1024 * 1024;

function tdkKho(id) {
  if (!TDK[id]) TDK[id] = { ds: [], dang_tai: 0 };
  return TDK[id];
}

/* Nạp sẵn danh sách tệp đã có (mở lại phiếu nháp chẳng hạn). */
function tdkNap(id, ds) {
  var k = tdkKho(id);
  k.ds = (ds || []).map(function (x) {
    if (typeof x === 'string') return { url: x, ten: x.split('/').pop(), anh: 1, duoi: 'TỆP' };
    return { url: x.url, ten: x.ten || '', anh: x.anh ? 1 : 0, duoi: x.duoi || 'TỆP' };
  });
}

function tdkDs(id) {
  return tdkKho(id).ds.map(function (x) { return x.url; });
}

function tdkXoaHet() { TDK = {}; }

function tdkDuoi(ten) {
  var t = String(ten || '');
  if (t.indexOf('.') < 0) return '';
  var d = '.' + t.split('.').pop().toLowerCase();
  return d.length <= 6 ? d : '';
}
function tdkLaAnh(ten) {
  return ['.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif', '.gif', '.bmp']
    .indexOf(tdkDuoi(ten)) >= 0;
}

/* Nén một tệp ảnh thành chuỗi base64. PDF thì đọc nguyên. Trả về qua cb. */
function tdkNen(f, cb, loi) {
  var xong = function (blob, ten) {
    var fr = new FileReader();
    fr.onload = function () {
      var s = String(fr.result || '');
      cb(s.indexOf(',') >= 0 ? s.split(',')[1] : s, ten);
    };
    fr.onerror = function () { loi('Không đọc được tệp ' + f.name); };
    fr.readAsDataURL(blob);
  };
  if (!tdkLaAnh(f.name)) return xong(f, f.name);

  var ve = function (img, w0, h0) {
    var w = w0, h2 = h0;
    if (w >= h2 && w > TDK_CANH) { h2 = Math.round(h2 * TDK_CANH / w); w = TDK_CANH; }
    else if (h2 > w && h2 > TDK_CANH) { w = Math.round(w * TDK_CANH / h2); h2 = TDK_CANH; }
    var cv = document.createElement('canvas');
    cv.width = w; cv.height = h2;
    cv.getContext('2d').drawImage(img, 0, 0, w, h2);
    cv.toBlob(function (b) {
      if (!b) return loi('Không nén được ảnh ' + f.name);
      /* Đổi đuôi sang .jpg vì nội dung sau khi nén là JPEG. Giữ đuôi .heic
         mà ruột là JPEG thì máy tính của kế toán mở ra báo tệp hỏng. */
      var ten = f.name.replace(/\.[^.]+$/, '') + '.jpg';
      xong(b, ten);
    }, 'image/jpeg', TDK_CHAT);
  };

  if (window.createImageBitmap) {
    createImageBitmap(f, { imageOrientation: 'from-image' }).then(function (bm) {
      ve(bm, bm.width, bm.height);
    }).catch(function () { tdkVeThuong(f, ve, loi); });
  } else {
    tdkVeThuong(f, ve, loi);
  }
}

function tdkVeThuong(f, ve, loi) {
  var img = new Image();
  var u = URL.createObjectURL(f);
  img.onload = function () { URL.revokeObjectURL(u); ve(img, img.width, img.height); };
  img.onerror = function () { URL.revokeObjectURL(u); loi('Không đọc được ảnh ' + f.name); };
  img.src = u;
}

/* Một ô vuông hình thu nhỏ. Ảnh thì vẽ ảnh, tệp khác thì vẽ ô mang đuôi tệp
   và tên thật ở dưới - không bao giờ ghi một cái tên mà máy chủ không biết
   có đúng không (bài học nút "Tải uỷ nhiệm chi" ngày 31/08/2026). */
function tdkO(t, id, i, xemDuoc) {
  var trong = t.anh
    ? '<img src="' + h(t.url) + '" alt="' + h(t.ten) + '" loading="lazy" ' +
      'style="width:100%;height:100%;object-fit:cover;display:block">'
    : '<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;' +
      'background:#f1f5f9;color:#475569;font-size:12.5px;font-weight:800;letter-spacing:.5px">' +
      h(t.duoi || 'TỆP') + '</div>';
  return '<div style="width:82px">' +
    '<div style="position:relative;width:82px;height:82px;border-radius:10px;overflow:hidden;' +
    'border:1.5px solid #e5e7eb;background:#fff">' +
    (xemDuoc ? '<a href="' + h(t.url) + '" target="_blank" rel="noopener" style="display:block;width:100%;height:100%">' + trong + '</a>' : trong) +
    '<button data-tdkxoa="' + h(id) + '|' + i + '" title="Gỡ tệp" ' +
    'style="position:absolute;top:3px;right:3px;width:22px;height:22px;border-radius:999px;border:none;' +
    'background:rgba(17,24,39,.72);color:#fff;font-size:13px;line-height:1;cursor:pointer">×</button>' +
    '</div>' +
    '<div style="font-size:10.5px;color:#98a2b3;margin-top:3px;line-height:1.35;word-break:break-all;' +
    'max-height:28px;overflow:hidden">' + h(t.ten || '') + '</div></div>';
}

/* Khối tải tệp. `nhan` là dòng chữ trên nút, `goi_y` là dòng nhắc nhỏ. */
function tdkKhoi(id, tuychon) {
  var o = tuychon || {};
  var k = tdkKho(id);
  var nut = '<button data-tdkchon="' + h(id) + '" class="btn gh" ' +
    'style="margin:0;width:100%;text-align:left">' +
    (o.nhan || '📎 Đính kèm ảnh chứng từ, ảnh hàng hoá') + '</button>' +
    '<input type="file" id="tdkInp_' + h(id) + '" multiple ' +
    'accept="image/*,application/pdf" style="display:none">';

  var luoi = k.ds.length
    ? '<div style="display:flex;flex-wrap:wrap;gap:9px;margin-top:9px">' +
      k.ds.map(function (t, i) { return tdkO(t, id, i, o.xem !== 0); }).join('') + '</div>'
    : '';

  var nhac = '<div id="tdkNhac_' + h(id) + '" style="font-size:11.5px;color:#98a2b3;margin-top:7px;line-height:1.55">' +
    (o.goi_y || 'Chụp hoặc chọn nhiều tệp một lượt. Ảnh được thu nhỏ ngay trên máy anh chị trước khi gửi, nên gửi nhanh và không chiếm chỗ.') +
    '</div>';

  return '<div id="tdkKhoi_' + h(id) + '" style="' + (o.style || 'margin-top:10px') + '">' +
    (o.tieu_de ? '<div style="font-size:11.5px;color:#0f766e;font-weight:800;margin-bottom:7px">' +
      h(o.tieu_de) + '</div>' : '') +
    nut + luoi + nhac + '</div>';
}

/* Vẽ lại RIÊNG một khối, không vẽ lại cả trang: người ta có thể đang gõ dở
   một ô khác trên cùng màn. */
function tdkVeLai(id, tuychon) {
  var n = document.getElementById('tdkKhoi_' + id);
  if (!n) return;
  var tam = document.createElement('div');
  tam.innerHTML = tdkKhoi(id, tuychon);
  n.replaceWith(tam.firstChild);
  tdkNoi(document, id, tuychon);
}

function tdkNoi(khung, id, tuychon) {
  var o = tuychon || {};
  var nut = (khung || document).querySelector('[data-tdkchon="' + id + '"]');
  var inp = document.getElementById('tdkInp_' + id);
  if (nut && inp) {
    nut.onclick = function () { inp.value = ''; inp.click(); };
    inp.onchange = function () { tdkTaiLen(id, inp.files, o); };
  }
  (khung || document).querySelectorAll('[data-tdkxoa^="' + id + '|"]').forEach(function (n) {
    n.onclick = async function () {
      var i = parseInt(n.getAttribute('data-tdkxoa').split('|')[1], 10);
      var k = tdkKho(id);
      var t = k.ds[i];
      if (!t) return;
      /* Gỡ ở máy chủ TRƯỚC rồi mới xoá khỏi màn. Xoá khỏi màn trước thì tệp
         nằm lại trên máy chủ mà không ai còn đường tới nó. */
      try { await api('vagabond.tep_dinh_kem.go_ra', { url: t.url }); }
      catch (e) { /* Tệp đã gắn vào phiếu hoặc đã bị xoá: bỏ khỏi màn là đủ. */ }
      k.ds.splice(i, 1);
      tdkVeLai(id, o);
      if (o.khi_doi) o.khi_doi();
    };
  });
}

async function tdkTaiLen(id, ds, o) {
  var k = tdkKho(id);
  var nhac = document.getElementById('tdkNhac_' + id);
  var cac = [];
  for (var i = 0; i < (ds || []).length; i++) cac.push(ds[i]);
  if (!cac.length) return;
  if (k.ds.length + cac.length > TDK_SO) {
    return baoTin('Một khoản chỉ đính tối đa ' + TDK_SO + ' tệp. Hiện đã có ' +
      k.ds.length + ' tệp.');
  }

  var hong = [];
  for (var j = 0; j < cac.length; j++) {
    var f = cac[j];
    if (f.size > TDK_CAP) {
      hong.push(f.name + ': nặng quá ' + Math.round(TDK_CAP / 1048576) + ' MB');
      continue;
    }
    if (nhac) nhac.innerHTML = 'Đang gửi tệp ' + (j + 1) + '/' + cac.length + '...';
    try {
      var r = await tdkMotTep(f, id);
      k.ds.push(r);
    } catch (e) {
      hong.push(f.name + ': ' + ((e && e.message) || 'gửi không được'));
    }
  }
  tdkVeLai(id, o);
  if (o && o.khi_doi) o.khi_doi();
  if (hong.length) baoTin(hong.join('\n'), 'Có tệp chưa gửi được');
}

function tdkMotTep(f, id) {
  return new Promise(function (ok, hong) {
    tdkNen(f, async function (b64, ten) {
      try {
        var r = await api('vagabond.tep_dinh_kem.nap_tam', {
          ten: ten, noi_dung: b64, phien: id
        });
        ok({ url: r.url, ten: r.ten || ten, anh: r.anh ? 1 : 0, duoi: r.duoi || 'TỆP' });
      } catch (e) { hong(e); }
    }, function (m) { hong(new Error(m)); });
  });
}

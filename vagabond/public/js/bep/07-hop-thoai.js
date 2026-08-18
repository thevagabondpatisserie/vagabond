/* ================= HOP THOAI DUNG CHUNG =================
   Anh Viet 13/08/2026: "phai bien thanh dang chip het de chon chu khong
   phai dang go 1 hay 2 tho so nhu the nay. Ca header cung xau not
   (app....says)".

   window.prompt / confirm / alert cua trinh duyet deo san cai header
   "app.thevagabondpatisserie.com says", khong doi mau duoc, khong bo chip
   vao duoc, va tren dien thoai thi hien giua man khong theo giao dien app.
   Bo nay dung lai khung overlay sh/shb/shh/shl da co san cua pickDate nen
   khong them mot dong CSS nao.

   Tat ca deu tra Promise: cho gan phai await, va ham bao no phai la async.
   Rieng baoTin chi hien roi thoi nen goi khong can await cung duoc. */

function hopKhung(tuaDe, thanHtml, chanHtml) {
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>' + h(tuaDe || '') + '</b><div class="x">&times;</div></div>' +
    '<div class="shl" style="padding:14px 16px 16px">' + thanHtml +
    (chanHtml ? '<div style="display:flex;gap:8px;margin-top:14px">' + chanHtml + '</div>' : '') +
    '</div>';
  ov.appendChild(box);
  document.body.appendChild(ov);
  return { ov: ov, box: box, dong: function () { try { ov.remove(); } catch (e) { } } };
}

/* Chon mot trong nhieu lua chon, moi cai mot chip bam duoc.
   luaChon: [{k, nhan, mo_ta}]. Tra ve k, hoac null neu thoi. */
function hoiChon(tuaDe, moTa, luaChon, kDangChon) {
  return new Promise(function (xong) {
    var than = (moTa ? '<div style="font-size:13.5px;line-height:1.6;color:#4b5563;margin-bottom:12px">' + moTa + '</div>' : '');
    (luaChon || []).forEach(function (x) {
      var chon = kDangChon != null && x.k === kDangChon;
      than += '<div data-hc="' + h(String(x.k)) + '" style="display:flex;align-items:flex-start;gap:11px;padding:13px 14px;border-radius:14px;margin-bottom:9px;cursor:pointer;'
        + (chon ? 'background:#0f766e;color:#fff' : 'background:#f4f6f9;color:#20242e') + '">'
        + '<div style="font-size:20px;line-height:1.2;flex:0 0 auto">' + (x.icon || '•') + '</div>'
        + '<div style="flex:1;min-width:0">'
        + '<div style="font-size:15px;font-weight:700">' + h(x.nhan) + '</div>'
        + (x.mo_ta ? '<div style="font-size:12.5px;line-height:1.5;margin-top:3px;' + (chon ? 'color:#d6f5f0' : 'color:#6b7280') + '">' + h(x.mo_ta) + '</div>' : '')
        + '</div></div>';
    });
    var k = hopKhung(tuaDe, than, '<button class="btn gh" data-hcx style="flex:1;margin:0">Thôi</button>');
    var tra = function (v) { k.dong(); xong(v); };
    k.box.onclick = function (e) {
      if (e.target.closest('.x') || e.target.closest('[data-hcx]')) return tra(null);
      var el = e.target.closest('[data-hc]');
      if (el) tra(el.getAttribute('data-hc'));
    };
    k.ov.onclick = function (e) { if (e.target === k.ov) tra(null); };
  });
}

/* Nhap mot dong chu. tuyChon: {kieu: 'text'|'number'|'email', goi_y, nhieu_dong,
   bat_buoc, don_vi} */
function hoiChu(tuaDe, nhan, macDinh, tuyChon) {
  var o = tuyChon || {};
  return new Promise(function (xong) {
    var oNhap = o.nhieu_dong
      ? '<textarea id="hqIn" class="tin" rows="3" style="margin:0" placeholder="' + h(o.goi_y || '') + '">' + h(macDinh || '') + '</textarea>'
      : '<input id="hqIn" class="tin" style="margin:0" type="' + (o.kieu === 'number' ? 'tel' : (o.kieu || 'text'))
        + '" inputmode="' + (o.kieu === 'number' ? 'numeric' : 'text') + '" placeholder="' + h(o.goi_y || '')
        + '" value="' + h(macDinh == null ? '' : String(macDinh)) + '">';
    var than = (nhan ? '<div style="font-size:13.5px;color:#4b5563;margin-bottom:9px;line-height:1.6">' + nhan + '</div>' : '') + oNhap
      + '<div id="hqLoi" style="display:none;font-size:12.5px;color:#b3261e;margin-top:7px"></div>';
    var k = hopKhung(tuaDe, than,
      '<button class="btn gh" data-hqx style="flex:1;margin:0">Thôi</button>'
      + '<button class="btn" data-hqok style="flex:2;margin:0">Xong</button>');
    var inp = k.box.querySelector('#hqIn');
    var loi = k.box.querySelector('#hqLoi');
    var tra = function (v) { k.dong(); xong(v); };
    var gui = function () {
      var v = String(inp.value == null ? '' : inp.value).trim();
      if (o.bat_buoc && !v) { loi.textContent = 'Chỗ này bắt buộc điền.'; loi.style.display = 'block'; inp.focus(); return; }
      tra(v);
    };
    k.box.onclick = function (e) {
      if (e.target.closest('.x') || e.target.closest('[data-hqx]')) return tra(null);
      if (e.target.closest('[data-hqok]')) return gui();
    };
    k.ov.onclick = function (e) { if (e.target === k.ov) tra(null); };
    if (inp) {
      inp.onkeydown = function (e) { if (e.key === 'Enter' && !o.nhieu_dong) { e.preventDefault(); gui(); } };
      setTimeout(function () { try { inp.focus(); inp.select(); } catch (e) { } }, 60);
    }
  });
}

/* Nhap so tien. Tra ve so, hoac null neu thoi. Bo moi ky tu khong phai so
   ngay luc go nen dan tu Excel co dau cham cung an. */
function hoiSo(tuaDe, nhan, macDinh) {
  return new Promise(function (xong) {
    hoiChu(tuaDe, nhan, macDinh ? String(macDinh) : '', { kieu: 'number', goi_y: '0' }).then(function (v) {
      if (v === null) return xong(null);
      var n = Number(String(v).replace(/[^0-9]/g, '')) || 0;
      xong(n);
    });
  });
}

/* Chon ngay bang lich co san, tra ve dang YYYY-MM-DD hoac null.

   Tham so tuaDe khong bat buoc. Anh Viet 18/08/2026: *"Popup chon ngay doi
   tu 'Chon ngay' thanh 'Chon ngay tao hop dong'"*. Doi thang chu trong
   pickDate thi ba cho goi khac cung bi doi theo, nen truyen tua de vao chu
   khong sua chu co san. */
function hoiNgay(macDinhIso, tuaDe) {
  return new Promise(function (xong) {
    var da = false;
    pickDate(macDinhIso || today(), function (v) { da = true; xong(v || null); }, tuaDe);
    // pickDate dong bang nut x thi khong goi cb, nen doi khung bien mat roi
    // tra null - khong lam vay thi cho await treo mai.
    var canh = setInterval(function () {
      if (da) return clearInterval(canh);
      if (!document.querySelector('.sh')) { clearInterval(canh); xong(null); }
    }, 250);
  });
}

/* Hoi co hay khong. Thay window.confirm. */
function hoiCo(tuaDe, noiDung, nhanOk, nguyHiem) {
  return new Promise(function (xong) {
    var than = '<div style="font-size:14px;line-height:1.7;color:#374151;white-space:pre-wrap">' + h(noiDung || '') + '</div>';
    var k = hopKhung(tuaDe, than,
      '<button class="btn gh" data-hkx style="flex:1;margin:0">Thôi</button>'
      + '<button class="btn" data-hkok style="flex:2;margin:0'
      + (nguyHiem ? ';background:#b3261e;border-color:#b3261e' : '') + '">' + h(nhanOk || 'Đồng ý') + '</button>');
    var tra = function (v) { k.dong(); xong(v); };
    k.box.onclick = function (e) {
      if (e.target.closest('.x') || e.target.closest('[data-hkx]')) return tra(false);
      if (e.target.closest('[data-hkok]')) return tra(true);
    };
    k.ov.onclick = function (e) { if (e.target === k.ov) tra(false); };
  });
}

/* Bao mot tin. Thay window.alert. Goi khong can await. */
function baoTin(noiDung, tuaDe) {
  var than = '<div style="font-size:14px;line-height:1.7;color:#374151;white-space:pre-wrap">' + h(String(noiDung == null ? '' : noiDung)) + '</div>';
  var k = hopKhung(tuaDe || 'Thông báo', than, '<button class="btn" data-hbok style="flex:1;margin:0">Đã hiểu</button>');
  k.box.onclick = function (e) { if (e.target.closest('.x') || e.target.closest('[data-hbok]')) k.dong(); };
  k.ov.onclick = function (e) { if (e.target === k.ov) k.dong(); };
  return k;
}

/* Hai ham boc de thay the co hoc window.prompt va window.confirm. Giu dung
   thu tu tham so cua ban goc nen doi cho goi chi viec them await. */
function hoiNhap(nhan, macDinh, tuaDe) { return hoiChu(tuaDe || 'Nhập thông tin', nhan, macDinh); }
function xacNhan(noiDung, tuaDe, nhanOk) { return hoiCo(tuaDe || 'Xác nhận', noiDung, nhanOk); }

function pickDate(cur, cb, tuaDe) {
  var base = /^\d{4}-\d{2}-\d{2}$/.test(cur || '') ? cur : today();
  var sel = base, pp = base.split('-'), vy = +pp[0], vm = +pp[1] - 1;
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function iso(d) { return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); }
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>' + h(tuaDe || 'Chọn ngày') + '</b><div class="x">&times;</div></div>' +
    '<div class="shl" style="padding:6px 12px 16px"></div>';
  var bd = box.querySelector('.shl');
  function close() { try { ov.remove(); } catch (x) { } }
  function nav(t) { return '<div data-p="' + t + '" style="width:46px;height:46px;border-radius:14px;background:#f2f4f8;display:flex;align-items:center;justify-content:center;font-size:22px;color:#3a4152">' + (t < 0 ? '&#8249;' : '&#8250;') + '</div>'; }
  function quick(n, lb) { return '<div data-q="' + n + '" style="flex:1;height:46px;border-radius:14px;background:#f2f4f8;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:600;color:#3a4152">' + lb + '</div>'; }
  function draw() {
    var st = (new Date(vy, vm, 1).getDay() + 6) % 7, dim = new Date(vy, vm + 1, 0).getDate(), td = today();
    var s = '<div style="display:flex;align-items:center;gap:8px;padding:4px 0 10px">' + nav(-1) +
      '<b style="flex:1;text-align:center;font-size:16.5px">Tháng ' + (vm + 1) + ' / ' + vy + '</b>' + nav(1) + '</div>' +
      '<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:5px;font-size:12px;color:#8a90a0;text-align:center;padding-bottom:5px">' +
      'T2,T3,T4,T5,T6,T7,CN'.split(',').map(function (x) { return '<div>' + x + '</div>'; }).join('') +
      '</div><div style="display:grid;grid-template-columns:repeat(7,1fr);gap:5px">';
    for (var k = 0; k < st; k++) s += '<div></div>';
    for (var d = 1; d <= dim; d++) {
      var v = vy + '-' + pad(vm + 1) + '-' + pad(d);
      var stl = v === sel ? 'background:#111827;color:#fff;font-weight:700' : (v === td ? 'background:#e6efff;color:#1b4dd8;font-weight:700' : 'background:#f7f8fb;color:#20242e');
      s += '<div data-dd="' + v + '" style="height:46px;display:flex;align-items:center;justify-content:center;border-radius:14px;font-size:15.5px;' + stl + '">' + d + '</div>';
    }
    s += '</div><div style="display:flex;gap:8px;padding-top:14px">' + quick(0, 'Hôm nay') + quick(1, 'Ngày mai') + quick(7, 'Sau 7 ngày') + '</div>';
    bd.innerHTML = s;
  }
  box.onclick = function (e) {
    if (e.target.closest('.x')) return close();
    var p = e.target.closest('[data-p]');
    if (p) { vm += +p.dataset.p; if (vm < 0) { vm = 11; vy--; } if (vm > 11) { vm = 0; vy++; } return draw(); }
    var q = e.target.closest('[data-q]');
    if (q) { var dt = new Date(); dt.setDate(dt.getDate() + (+q.dataset.q)); close(); return cb(iso(dt)); }
    var dd = e.target.closest('[data-dd]');
    if (dd) { close(); return cb(dd.dataset.dd); }
  };
  ov.onclick = function (e) { if (e.target === ov) close(); };
  ov.appendChild(box); document.body.appendChild(ov); draw();
}
/* ---- anh dinh kem, tien do, quy OCB cho phieu mua hang test ---- */
var RND_OCB_TK = '1411 - Tạm ứng - Nguyễn Hoàng Việt (OCB) - TV';
var RND_NCC_LE = 'NCC lẻ - mua hàng test (R&D)';
function rndLaThuMua() { return hasRole('Purchase User') || hasRole('Accounts User') || hasRole('System Manager'); }
function rndAnhDs(v) { return String(v || '').split('\n').map(function (x) { return x.trim(); }).filter(Boolean); }
function rndAnhChuoi(a) { return (a || []).join('\n'); }
function rndXemAnh(url) {
  var ov = document.createElement('div');
  ov.style.cssText = 'position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,.92);display:flex;align-items:center;justify-content:center;padding:16px';
  ov.innerHTML = '<img src="' + h(url) + '" style="max-width:100%;max-height:100%;border-radius:8px">' +
    '<div style="position:absolute;top:calc(env(safe-area-inset-top,0px) + 12px);right:18px;color:#fff;font-size:32px;line-height:1">&times;</div>';
  ov.onclick = function () { ov.remove(); };
  document.body.appendChild(ov);
}
/* luoi anh. sua = true thi hien nut them va nut xoa */
function rndAnhLuoi(urls, sua, tag) {
  var o = '<div class="rndAnh" data-tag="' + h(tag || '') + '" style="display:flex;flex-wrap:wrap;gap:8px' + (sua ? ';margin-bottom:11px' : ';margin-top:7px') + '">';
  (urls || []).forEach(function (u, i) {
    o += '<div style="position:relative;width:' + (sua ? 68 : 54) + 'px;height:' + (sua ? 68 : 54) + 'px;border-radius:9px;overflow:hidden;border:1px solid #e3e6ec;background:#f5f6f8">' +
      '<img src="' + h(u) + '" data-anh="' + h(u) + '" loading="lazy" style="width:100%;height:100%;object-fit:cover;display:block">' +
      (sua ? '<span data-xoa="' + i + '" style="position:absolute;top:0;right:0;width:22px;height:22px;line-height:21px;text-align:center;background:rgba(0,0,0,.62);color:#fff;font-size:15px;border-bottom-left-radius:9px">&times;</span>' : '') +
      '</div>';
  });
  if (sua) o += '<button type="button" data-them style="width:68px;height:68px;border-radius:9px;border:1px dashed #b9c0cc;background:#fafbfc;color:#6b7280;font-size:11.5px;line-height:1.3;padding:4px">\uD83D\uDCF7<br>Thêm ảnh</button>';
  o += '</div>';
  return o;
}
/* gan hanh vi cho luoi anh trong pham vi root. layDs() tra ve mang hien tai, cb(dsMoi) goi sau moi thay doi */
function rndGanAnh(root, tag, layDs, cb) {
  if (!root) return;
  var el = root.querySelector('.rndAnh[data-tag="' + tag + '"]');
  if (!el) return;
  el.onclick = function (e) {
    var im = e.target.closest('[data-anh]');
    if (im) return rndXemAnh(im.getAttribute('data-anh'));
    var x = e.target.closest('[data-xoa]');
    if (x) { var ds = layDs().slice(); ds.splice(+x.getAttribute('data-xoa'), 1); return cb(ds); }
    if (!e.target.closest('[data-them]')) return;
    var inp = document.createElement('input');
    inp.type = 'file'; inp.accept = 'image/*'; inp.multiple = true; inp.style.display = 'none';
    inp.onchange = async function () {
      var fs = Array.prototype.slice.call(this.files || []);
      var self = this;
      if (!fs.length) { self.remove(); return; }
      busy(1);
      var ds = layDs().slice(), loi = 0;
      for (var i = 0; i < fs.length; i++) {
        try { ds.push(await vxUpAnh(fs[i])); } catch (err) { loi++; }
      }
      busy(0); self.remove();
      if (loi) toast('Có ' + loi + ' ảnh không tải lên được, thử lại giúp em', 4200);
      cb(ds);
    };
    document.body.appendChild(inp); inp.click();
  };
}
function rndTienDo(items) {
  var t = { tong: (items || []).length, mua: 0, khong: 0, chua: 0, tien: 0, ocb: 0, anh: 0 };
  (items || []).forEach(function (x) {
    if (x.trang_thai_dong === 'Đã mua') {
      t.mua++; t.tien += Number(x.gia) || 0;
      if ((x.tra_bang || 'Quỹ OCB') === 'Quỹ OCB') t.ocb += Number(x.gia) || 0;
      if (rndAnhDs(x.anh_chung_tu).length) t.anh++;
    } else if (x.trang_thai_dong === 'Không mua được') t.khong++;
    else t.chua++;
  });
  return t;
}
function rndThanh(t) {
  if (!t.tong) return '';
  var pc = Math.round((t.mua + t.khong) * 100 / t.tong);
  return '<div style="margin:9px 0 1px"><div style="height:6px;border-radius:99px;background:#e8eaef;overflow:hidden">' +
    '<div style="height:100%;width:' + pc + '%;background:#0B7C93;transition:width .25s"></div></div>' +
    '<div style="font-size:12.5px;color:#6b7280;margin-top:6px">' + t.mua + '/' + t.tong + ' đã mua' +
    (t.khong ? ' · ' + t.khong + ' không mua được' : '') +
    (t.chua ? ' · ' + t.chua + ' chưa mua' : '') + '</div></div>';
}
function rndTre(d) {
  return !!(d && d.ngay_can && String(d.ngay_can).slice(0, 10) < today() &&
    (d.trang_thai === 'Mới tạo' || d.trang_thai === 'Đang xử lý'));
}
function rndBlank() {
  return { ten_hang: '', so_luong: '', link_tham_khao: '', anh_dinh_kem: '', yeu_cau_them: '', can_hoa_don: 0, trang_thai_dong: 'Chưa mua', ncc: '', sdt_ncc: '', gia: 0, tra_bang: 'Quỹ OCB', anh_chung_tu: '', ghi_chu_mua: '' };
}
function rndCopy(x) {
  var o = rndBlank(), k;
  for (k in o) if (x && x[k] !== undefined && x[k] !== null) o[k] = x[k];
  if (x && x.name) o.name = x.name;
  if (x && x.idx) o.idx = x.idx;
  return o;
}
function rndMoney(n) { n = Number(n) || 0; return n.toLocaleString('vi-VN'); }
function rndLbl(t) { return '<div style="font-size:12.5px;font-weight:700;color:#6b7280;margin:2px 0 5px">' + h(t) + '</div>'; }
function rndSeg(nm, opts, cur) {
  return '<div style="display:flex;gap:7px;margin-bottom:11px">' + opts.map(function (o) {
    return '<button type="button" class="btn' + (o === cur ? '' : ' gh') + '" data-seg="' + h(nm) + '" data-v="' + h(o) + '" style="flex:1;height:42px;font-size:13.5px;padding:0 4px">' + h(o) + '</button>';
  }).join('') + '</div>';
}
function rndInp(id, ph, val, num) {
  return '<input class="nt" id="' + id + '" placeholder="' + h(ph) + '" value="' + h(val === 0 ? '' : (val || '')) + '"' +
    (num ? ' type="number" inputmode="decimal" step="any"' : '') + ' style="height:46px;padding:0 12px;margin-bottom:11px">';
}
function rndTa(id, ph, val, rows) {
  return '<textarea class="nt" id="' + id + '" rows="' + (rows || 2) + '" placeholder="' + h(ph) + '" style="margin-bottom:11px">' + h(val || '') + '</textarea>';
}

/* form them / sua mot dong hang, mode = 'req' (nguoi yeu cau) hoac 'buy' (nguoi mua) */
function rndLineSheet(line, mode) {
  return new Promise(function (res) {
    var L = rndCopy(line), isNew = !line;
    var ov = document.createElement('div'); ov.className = 'sh';
    function draw() {
      var b = '<div class="shb" style="padding:16px 16px calc(env(safe-area-inset-bottom,0px) + 16px);max-height:88vh;overflow:auto">' +
        '<div style="font-size:17.5px;font-weight:700;margin-bottom:13px">' +
        (mode === 'buy' ? 'Kết quả mua hàng' : (isNew ? 'Thêm hàng cần mua' : 'Sửa dòng hàng')) + '</div>';
      if (mode === 'buy') {
        b += '<div style="background:#f5f6f8;border-radius:10px;padding:11px 12px;margin-bottom:13px;font-size:14px;line-height:1.6;color:#4a5060">' +
          '<b>' + h(L.ten_hang) + '</b>' + (L.so_luong ? ' · ' + h(L.so_luong) : '') +
          (L.link_tham_khao ? '<br>' + h(L.link_tham_khao) : '') +
          (L.yeu_cau_them ? '<br>' + h(L.yeu_cau_them) : '') +
          (L.can_hoa_don ? '<br>Cần hoá đơn VAT' : '') +
          (rndAnhDs(L.anh_dinh_kem).length ? rndAnhLuoi(rndAnhDs(L.anh_dinh_kem), false, 'xem') : '') + '</div>' +
          rndLbl('Trạng thái dòng này') + rndSeg('trang_thai_dong', ['Chưa mua', 'Đã mua', 'Không mua được'], L.trang_thai_dong) +
          rndLbl('Nhà cung cấp tìm được') + rndInp('rl_ncc', 'Tên farm, shop, nhà cung cấp', L.ncc) +
          rndLbl('Điện thoại nhà cung cấp') + rndInp('rl_sdt', 'Số để lần sau gọi lại', L.sdt_ncc) +
          rndLbl('Giá mua thực tế (đồng)') + rndInp('rl_gia', '0', L.gia, 1) +
          rndLbl('Trả bằng') + rndSeg('tra_bang', ['Quỹ OCB', 'Tiền công ty', 'Khác'], L.tra_bang || 'Quỹ OCB') +
          rndLbl('Ảnh chứng từ (biên lai, hoá đơn)') + rndAnhLuoi(rndAnhDs(L.anh_chung_tu), true, 'buy') +
          rndLbl('Ghi chú của người mua') + rndTa('rl_gcm', 'MOQ bao nhiêu, có xuất hoá đơn không, giao mấy ngày...', L.ghi_chu_mua, 3);
      } else {
        b += rndLbl('Tên hàng cần mua') + rndInp('rl_ten', 'vd: Dứa MD2, chất bảo quản...', L.ten_hang) +
          rndLbl('Số lượng cần') + rndInp('rl_sl', 'vd: 20 kg, 2 thùng, 5 hộp', L.so_luong) +
          rndLbl('Link tham khảo (nếu có)') + rndTa('rl_link', 'Dán link Shopee, website, bài đăng...', L.link_tham_khao, 2) +
          rndLbl('Ảnh tham khảo (chụp màn hình, ảnh sản phẩm)') + rndAnhLuoi(rndAnhDs(L.anh_dinh_kem), true, 'req') +
          rndLbl('Yêu cầu thêm') + rndTa('rl_yc', 'Hỏi MOQ, quy cách đóng gói, cần giao trước ngày nào...', L.yeu_cau_them, 3) +
          rndLbl('Có cần hoá đơn VAT không') + rndSeg('can_hoa_don', ['Cần hoá đơn', 'Không cần'], L.can_hoa_don ? 'Cần hoá đơn' : 'Không cần');
      }
      b += '<button class="btn" data-y>Lưu</button>';
      if (!isNew && mode !== 'buy') b += '<button class="btn dg" data-del style="margin-top:9px">Xoá dòng này</button>';
      b += '<button class="btn gh" data-n style="margin-top:9px">Huỷ</button></div>';
      ov.innerHTML = b;
      var tg = (mode === 'buy') ? 'buy' : 'req';
      rndGanAnh(ov, tg, function () { return rndAnhDs(mode === 'buy' ? L.anh_chung_tu : L.anh_dinh_kem); }, function (ds) {
        grab();
        if (mode === 'buy') L.anh_chung_tu = rndAnhChuoi(ds); else L.anh_dinh_kem = rndAnhChuoi(ds);
        draw();
      });
      rndGanAnh(ov, 'xem', function () { return rndAnhDs(L.anh_dinh_kem); }, function () { });
    }
    function grab() {
      function v(id) { var e = ov.querySelector('#' + id); return e ? e.value.trim() : ''; }
      if (mode === 'buy') {
        L.ncc = v('rl_ncc'); L.sdt_ncc = v('rl_sdt'); L.gia = Number(v('rl_gia')) || 0; L.ghi_chu_mua = v('rl_gcm');
      } else {
        L.ten_hang = v('rl_ten'); L.so_luong = v('rl_sl'); L.link_tham_khao = v('rl_link'); L.yeu_cau_them = v('rl_yc');
      }
    }
    draw();
    document.body.appendChild(ov);
    ov.onclick = function (e) {
      var sg = e.target.closest('[data-seg]');
      if (sg) {
        grab();
        var f = sg.dataset.seg, val = sg.dataset.v;
        if (f === 'can_hoa_don') L.can_hoa_don = (val === 'Cần hoá đơn') ? 1 : 0;
        else L[f] = val;
        return draw();
      }
      if (e.target.hasAttribute('data-del')) { ov.remove(); return res({ del: 1 }); }
      if (e.target === ov || e.target.hasAttribute('data-n')) { ov.remove(); return res(null); }
      if (e.target.hasAttribute('data-y')) {
        grab();
        if (mode !== 'buy' && !L.ten_hang) return toast('Chưa ghi tên hàng cần mua');
        ov.remove(); return res(L);
      }
    };
  });
}

/* ---- 15a. Danh sach phieu ---- */
async function scrRndList() {
  frame('Mua hàng test', '<div class="emp"><div class="e1">⏳</div></div>');
  await loadMasters();
  var docs = [];
  try {
    docs = await getList('RnD Purchase Request', {
      fields: ['name', 'muc_dich', 'ngay_can', 'trang_thai', 'nguoi_yeu_cau', 'nguoi_mua', 'tong_tien', 'modified'],
      limit_page_length: 80, order_by: 'modified desc'
    });
  } catch (e) { toast(errMsg(e)); }
  var dang = docs.filter(function (d) { return d.trang_thai === 'Mới tạo' || d.trang_thai === 'Đang xử lý'; });
  var xong = docs.filter(function (d) { return d.trang_thai === 'Hoàn thành'; });
  var huy = docs.filter(function (d) { return d.trang_thai === 'Huỷ'; });
  function row(d) {
    var s = RNDST[d.trang_thai] || RNDST['Mới tạo'];
    return '<div class="li" data-p="' + h(d.name) + '"><div class="lt">' +
      '<div class="l1">' + h(d.muc_dich || d.name) + '</div>' +
      '<div class="l2">' + h(d.name) + (d.ngay_can ? ' · cần ' + h(dmy(d.ngay_can)) : '') +
      (d.nguoi_yeu_cau ? ' · ' + h(d.nguoi_yeu_cau) : '') +
      (d.tong_tien ? ' · ' + rndMoney(d.tong_tien) + 'đ' : '') + '</div></div>' +
      (rndTre(d) ? '<span class="st r" style="margin-right:5px">Trễ hạn</span>' : '') +
      '<span class="st ' + s.c + '">' + h(s.t) + '</span></div>';
  }
  var body = '<div class="rcvh">Phiếu này dành cho <b>hàng mua về test</b>: không tạo mã, không theo dõi tồn kho. Ghi rõ tên hàng, số lượng, link tham khảo và ảnh chụp màn hình để bạn thu mua khỏi phải hỏi lại. Mua xong bấm <b>Hoàn thành phiếu</b>.</div>';
  if (dang.length) body += '<div class="sec">Đang chờ mua</div><div class="lst">' + dang.map(row).join('') + '</div>';
  if (xong.length) body += '<div class="sec">Đã hoàn thành</div><div class="lst">' + xong.map(row).join('') + '</div>';
  if (huy.length) body += '<div class="sec">Đã huỷ</div><div class="lst">' + huy.map(row).join('') + '</div>';
  if (!docs.length) body += '<div class="emp"><div class="e1">🧪</div><div class="e2">Chưa có phiếu nào.<br>Bấm dấu + để tạo yêu cầu mua hàng test.</div></div>';
  var b = frame('Mua hàng test', body, { fab: true, onFab: function () { rnd.newf = null; go(scrRndNew); } });
  b.onclick = function (e) {
    var r = e.target.closest('[data-p]'); if (!r) return;
    go(function () { scrRndDoc(r.dataset.p); });
  };
}

/* ---- 15b. Tao phieu moi ---- */
async function scrRndNew() {
  await loadMasters();
  if (!rnd.newf) rnd.newf = { muc_dich: '', ngay_can: '', ghi_chu: '', anh_dinh_kem: '', items: [] };
  var f = rnd.newf;
  function draw() {
    var body = '<div class="rcvh">Gom tất cả thứ cần mua để test vào <b>một phiếu</b> theo từng đợt, khỏi nhắn lẻ tẻ qua Lark. Hàng này không nhập kho và không tạo mã.</div>' +
      '<div class="card">' +
      '<div class="fld" data-m><div class="fi">🧪</div><div class="ft"><div class="fl">Mục đích / dự án</div><div class="fv' + (f.muc_dich ? '' : ' ph') + '">' + h(f.muc_dich || 'Bắt buộc - vd: Test bánh dứa MD2') + '</div></div><div class="fc">&#8250;</div></div>' +
      '<div class="fld" data-d><div class="fi">📅</div><div class="ft"><div class="fl">Ngày cần hàng</div><div class="fv' + (f.ngay_can ? '' : ' ph') + '">' + h(f.ngay_can ? dmy(f.ngay_can) : 'Chưa chọn') + '</div></div><div class="fc">&#8250;</div></div>' +
      '<div class="fld" data-g><div class="fi">📝</div><div class="ft"><div class="fl">Ghi chú chung</div><div class="fv' + (f.ghi_chu ? '' : ' ph') + '">' + h(f.ghi_chu || 'Không bắt buộc') + '</div></div><div class="fc">&#8250;</div></div>' +
      '</div>';
    body += '<div class="sec">Ảnh / tài liệu đính kèm cả phiếu</div>' +
      '<div style="padding:0 14px 2px">' + rndAnhLuoi(rndAnhDs(f.anh_dinh_kem), true, 'ph') +
      '<div style="font-size:12.5px;color:#8a90a0;margin:-4px 0 8px">Ảnh chụp màn hình, báo giá, danh sách cần mua... Ảnh riêng của từng món thì đính ngay trong dòng hàng.</div></div>';
    body += '<div class="sec">Hàng cần mua (' + f.items.length + ')</div>';
    if (f.items.length) {
      body += '<div class="lst">' + f.items.map(function (it, i) {
        return '<div class="li" data-i="' + i + '"><div class="lt">' +
          '<div class="l1">' + h(it.ten_hang) + '</div>' +
          '<div class="l2">' + h(it.so_luong || 'chưa ghi số lượng') +
          (it.can_hoa_don ? ' · cần hoá đơn VAT' : '') +
          (it.link_tham_khao ? ' · có link' : '') +
          (rndAnhDs(it.anh_dinh_kem).length ? ' · ' + rndAnhDs(it.anh_dinh_kem).length + ' ảnh' : '') + '</div></div>' +
          '<span class="fc" style="color:#c3c8d4;font-size:22px">&#8250;</span></div>';
      }).join('') + '</div>';
    } else {
      body += '<div class="emp"><div class="e1">🛒</div><div class="e2">Chưa có dòng nào.<br>Bấm nút bên dưới để thêm hàng.<br><span style="font-size:13px;color:#8a90a0">Mỗi dòng có ô dán link tham khảo và ô tải ảnh lên.</span></div></div>';
    }
    body += '<div style="padding:4px 14px 10px"><button class="btn gh" id="rndAdd">+ Thêm hàng cần mua</button></div>';
    var b = frame('Yêu cầu mua hàng test', body, { footer: '<button class="btn" id="rndSave">Gửi yêu cầu</button>' });
    rndGanAnh(b, 'ph', function () { return rndAnhDs(f.anh_dinh_kem); }, function (ds) { f.anh_dinh_kem = rndAnhChuoi(ds); draw(); });
    b.onclick = function (e) {
      if (e.target.closest('[data-m]')) {
        return promptSheet('Mục đích / dự án', 'vd: Test nhân bánh dứa MD2').then(function (v) { if (v !== null) { f.muc_dich = v; draw(); } });
      }
      if (e.target.closest('[data-g]')) {
        return promptSheet('Ghi chú chung cho cả phiếu', 'Không bắt buộc').then(function (v) { if (v !== null) { f.ghi_chu = v; draw(); } });
      }
      if (e.target.closest('[data-d]')) return pickDate(f.ngay_can || today(), function (v) { f.ngay_can = v; draw(); });
      var r = e.target.closest('[data-i]');
      if (r) {
        var i = +r.dataset.i;
        return rndLineSheet(f.items[i], 'req').then(function (v) {
          if (!v) return;
          if (v.del) f.items.splice(i, 1); else f.items[i] = v;
          draw();
        });
      }
    };
    document.getElementById('rndAdd').onclick = function () {
      rndLineSheet(null, 'req').then(function (v) { if (v && !v.del) { f.items.push(v); draw(); } });
    };
    document.getElementById('rndSave').onclick = rndCreate;
  }
  draw();
}

async function rndCreate() {
  var f = rnd.newf;
  if (!f.muc_dich) return toast('Chưa ghi mục đích của phiếu');
  if (!f.items.length) return toast('Chưa có dòng hàng nào');
  busy(1);
  try {
    var d = await api('frappe.client.insert', {
      doc: {
        doctype: 'RnD Purchase Request',
        muc_dich: f.muc_dich,
        ngay_can: f.ngay_can || undefined,
        ghi_chu: f.ghi_chu || undefined,
        anh_dinh_kem: f.anh_dinh_kem || undefined,
        trang_thai: 'Mới tạo',
        nguoi_yeu_cau: S.user,
        items: f.items.map(function (x) { return rndCopy(x); })
      }
    });
    busy(0);
    if (!d || !d.name) return toast('Không tạo được phiếu, thử lại giúp');
    rnd.newf = null;
    toast('Đã gửi yêu cầu ' + d.name);
    go(function () { scrRndDoc(d.name); }, true);
  } catch (e) { busy(0); toast(errMsg(e), 5000); }
}

/* ---- 15c. Xem va xu ly phieu ---- */
async function scrRndDoc(name) {
  frame('Phiếu mua test', '<div class="emp"><div class="e1">⏳</div></div>');
  await loadMasters();
  var doc = null;
  try { doc = await api('frappe.client.get', { doctype: 'RnD Purchase Request', name: name }); }
  catch (e) { toast(errMsg(e)); return back(); }

  function tong() {
    return (doc.items || []).reduce(function (a, x) { return a + (x.trang_thai_dong === 'Đã mua' ? (Number(x.gia) || 0) : 0); }, 0);
  }
  async function save(msg) {
    busy(1);
    try {
      doc.tong_tien = tong();
      doc = await api('frappe.client.save', { doc: doc });
      busy(0);
      if (msg) toast(msg);
      draw();
    } catch (e) { busy(0); toast(errMsg(e), 5000); }
  }

  function draw() {
    var live = doc.trang_thai === 'Mới tạo' || doc.trang_thai === 'Đang xử lý';
    var mine = doc.nguoi_yeu_cau === S.user || doc.owner === S.user;
    var s = RNDST[doc.trang_thai] || RNDST['Mới tạo'];
    var td = rndTienDo(doc.items);
    var chua = td.chua;
    var body = '<div class="card" style="padding:13px 14px">' +
      '<div style="display:flex;align-items:center;gap:9px;margin-bottom:7px">' +
      '<b style="font-size:16.5px;flex:1">' + h(doc.muc_dich || doc.name) + '</b>' +
      (rndTre(doc) ? '<span class="st r">Trễ hạn</span>' : '') +
      '<span class="st ' + s.c + '">' + h(s.t) + '</span></div>' +
      '<div style="font-size:13.5px;color:#6b7280;line-height:1.7">' + h(doc.name) +
      (doc.ngay_can ? '<br>Cần hàng ngày ' + h(dmy(doc.ngay_can)) : '') +
      (doc.nguoi_yeu_cau ? '<br>Người yêu cầu: ' + h(doc.nguoi_yeu_cau) : '') +
      (doc.nguoi_mua ? '<br>Người mua: ' + h(doc.nguoi_mua) : '') +
      (doc.ghi_chu ? '<br>Ghi chú: ' + h(doc.ghi_chu) : '') +
      '<br>Tổng tiền đã mua: <b>' + rndMoney(tong()) + 'đ</b>' +
      '</div>' + rndThanh(td) + '</div>';

    var suaAnh = live && mine;
    body += '<div class="sec">Ảnh / tài liệu đính kèm cả phiếu</div><div style="padding:0 14px 6px">';
    if (rndAnhDs(doc.anh_dinh_kem).length || suaAnh) body += rndAnhLuoi(rndAnhDs(doc.anh_dinh_kem), suaAnh, 'ph');
    else body += '<div style="font-size:13.5px;color:#8a90a0;padding-bottom:6px">Chưa có ảnh nào.</div>';
    body += '</div>';

    body += '<div class="sec">Hàng cần mua (' + (doc.items || []).length + ')</div><div class="lst">' +
      (doc.items || []).map(function (it, i) {
        var ls = RNDLS[it.trang_thai_dong] || RNDLS['Chưa mua'];
        var sub = h(it.so_luong || 'chưa ghi số lượng');
        if (it.can_hoa_don) sub += ' · cần hoá đơn VAT';
        if (it.ncc) sub += '<br>NCC: ' + h(it.ncc) + (it.sdt_ncc ? ' · ' + h(it.sdt_ncc) : '');
        if (it.gia) sub += '<br>Giá: ' + rndMoney(it.gia) + 'đ';
        if (it.yeu_cau_them) sub += '<br>' + h(it.yeu_cau_them);
        if (it.trang_thai_dong === 'Đã mua' && it.tra_bang) sub += '<br>Trả bằng: ' + h(it.tra_bang);
        if (it.link_tham_khao) sub += '<br><span style="color:#0B7C93;word-break:break-all">' + h(it.link_tham_khao) + '</span>';
        if (it.ghi_chu_mua) sub += '<br>Người mua: ' + h(it.ghi_chu_mua);
        var anhL = rndAnhDs(it.anh_dinh_kem).concat(rndAnhDs(it.anh_chung_tu));
        if (anhL.length) sub += rndAnhLuoi(anhL, false, '');
        return '<div class="li" data-i="' + i + '"><div class="lt">' +
          '<div class="l1">' + h(it.ten_hang) + '</div>' +
          '<div class="l2">' + sub + '</div></div>' +
          '<span class="st ' + ls.c + '">' + h(ls.t) + '</span></div>';
      }).join('') + '</div>';

    if (live) {
      body += '<div class="kwn">Bấm vào một dòng để ghi kết quả mua: nhà cung cấp, giá, ghi chú. ' +
        (mine ? 'Là người tạo phiếu nên anh chị vẫn sửa hoặc thêm dòng được khi phiếu chưa hoàn thành.' : '') + '</div>';
      if (mine) body += '<div style="padding:4px 14px 10px"><button class="btn gh" id="rndAdd2">+ Thêm hàng cần mua</button></div>';
    }

    if (doc.trang_thai === 'Hoàn thành' && td.tien > 0) {
      body += '<div class="sec">Quỹ tạm ứng OCB</div><div class="card" style="padding:13px 14px;font-size:14px;line-height:1.75;color:#4a5060">' +
        'Chi từ quỹ OCB: <b>' + rndMoney(td.ocb) + 'đ</b><br>' +
        'Tổng tiền cả phiếu: <b>' + rndMoney(td.tien) + 'đ</b><br>' +
        'Khoản đã có ảnh chứng từ: <b>' + td.anh + '/' + td.mua + '</b>' +
        (doc.phieu_chi_phi ? '<br>Đã lập phiếu ghi chi phí: <b>' + h(doc.phieu_chi_phi) + '</b>' : '') +
        '</div>';
      if (!doc.phieu_chi_phi && td.ocb > 0 && rndLaThuMua()) {
        body += '<div class="kwn">Bấm nút dưới để em dựng sẵn một hoá đơn mua hàng ở dạng nháp, ghi là đã trả từ quỹ OCB. Kế toán xem lại rồi mới ghi sổ.</div>' +
          '<div style="padding:4px 14px 10px"><button class="btn gh" id="rndChiPhi">Lập phiếu ghi chi phí (nháp)</button></div>';
      }
    }

    var ft = '';
    if (live) {
      ft = '<button class="btn" id="rndDone">Hoàn thành phiếu' + (chua ? ' (' + chua + ' dòng chưa mua)' : '') + '</button>';
      if (mine) ft += '<button class="btn gh" id="rndCancel" style="margin-top:9px">Huỷ phiếu</button>';
    }
    var b = frame('Phiếu mua test', body, ft ? { footer: ft } : {});
    rndGanAnh(b, 'ph', function () { return rndAnhDs(doc.anh_dinh_kem); }, function (ds) {
      doc.anh_dinh_kem = rndAnhChuoi(ds); save('Đã cập nhật ảnh');
    });
    b.onclick = function (e) {
      var im0 = e.target.closest('[data-anh]');
      if (im0 && !e.target.closest('.rndAnh[data-tag="ph"]')) return rndXemAnh(im0.getAttribute('data-anh'));
      var r = e.target.closest('[data-i]'); if (!r) return;
      var i = +r.dataset.i;
      if (!live) return;
      var canEdit = mine && doc.items[i].trang_thai_dong === 'Chưa mua';
      var opts = [{ value: 'buy', label: 'Ghi kết quả mua hàng', icon: '💰' }];
      if (canEdit) opts.push({ value: 'req', label: 'Sửa nội dung yêu cầu', icon: '✏️' });
      function open(mode) {
        rndLineSheet(doc.items[i], mode).then(function (v) {
          if (!v) return;
          if (v.del) { doc.items.splice(i, 1); return save('Đã xoá dòng'); }
          var row = doc.items[i], k;
          for (k in v) if (k !== 'name' && k !== 'idx') row[k] = v[k];
          if (mode === 'buy' && !doc.nguoi_mua) doc.nguoi_mua = S.user;
          if (mode === 'buy' && doc.trang_thai === 'Mới tạo') doc.trang_thai = 'Đang xử lý';
          save('Đã lưu');
        });
      }
      if (opts.length === 1) return open('buy');
      sheet(doc.items[i].ten_hang, opts, '', function (o) { open(o.value); });
    };
    var ad = document.getElementById('rndAdd2');
    if (ad) ad.onclick = function () {
      rndLineSheet(null, 'req').then(function (v) {
        if (!v || v.del) return;
        doc.items.push(v); save('Đã thêm dòng');
      });
    };
    var cpn = document.getElementById('rndChiPhi');
    if (cpn) cpn.onclick = async function () {
      var ds = (doc.items || []).filter(function (x) {
        return x.trang_thai_dong === 'Đã mua' && (x.tra_bang || 'Quỹ OCB') === 'Quỹ OCB' && (Number(x.gia) || 0) > 0;
      });
      if (!ds.length) return toast('Không có khoản nào chi từ quỹ OCB');
      var tongDs = ds.reduce(function (a, x) { return a + (Number(x.gia) || 0); }, 0);
      var coVat = ds.filter(function (x) { return x.can_hoa_don; }).length;
      var ok = await confirmSheet('Lập phiếu ghi chi phí?',
        'Em tạo một hoá đơn mua hàng ở dạng NHÁP gồm ' + ds.length + ' khoản, tổng ' + rndMoney(tongDs) + 'đ, ghi là đã trả từ quỹ OCB.\n\n' +
        (coVat ? 'Trong đó ' + coVat + ' khoản có hoá đơn VAT, kế toán sẽ nhập phần thuế và đổi sang đúng nhà cung cấp.\n\n' : '') +
        'Phiếu chỉ ở dạng nháp, kế toán xem lại rồi mới ghi sổ.', 'Lập phiếu nháp');
      if (!ok) return;
      function than(coTra) {
        var d2 = {
          doctype: 'Purchase Invoice', company: COMPANY, supplier: RND_NCC_LE,
          posting_date: today(), set_posting_time: 1, bill_no: doc.name,
          remarks: 'Mua hàng test theo phiếu ' + doc.name + (doc.muc_dich ? ' - ' + doc.muc_dich : ''),
          items: ds.map(function (x) {
            return {
              item_code: x.can_hoa_don ? 'CP-MUANHO-HD' : 'CP-MUANHO-KHD',
              item_name: String(x.ten_hang || 'Hàng test').slice(0, 140),
              description: String(x.ten_hang || '') + (x.so_luong ? ' - ' + x.so_luong : '') + (x.ncc ? ' - NCC: ' + x.ncc : ''),
              qty: 1, uom: 'Lần', rate: Number(x.gia) || 0
            };
          })
        };
        if (coTra) { d2.is_paid = 1; d2.mode_of_payment = 'Chuyển khoản'; d2.cash_bank_account = RND_OCB_TK; d2.paid_amount = tongDs; }
        return d2;
      }
      busy(1);
      var pi = null;
      try { pi = await api('frappe.client.insert', { doc: than(true) }); }
      catch (e1) {
        try { pi = await api('frappe.client.insert', { doc: than(false) }); }
        catch (e2) { busy(0); return toast(errMsg(e2), 6000); }
      }
      busy(0);
      if (!pi || !pi.name) return toast('Không lập được phiếu, thử lại giúp em');
      doc.phieu_chi_phi = pi.name;
      await save('Đã lập phiếu nháp ' + pi.name);
    };
    var dn = document.getElementById('rndDone');
    if (dn) dn.onclick = async function () {
      var ok = await confirmSheet('Hoàn thành phiếu này?',
        chua ? ('Còn ' + chua + ' dòng đang ở trạng thái Chưa mua. Nếu không mua được thì nên đánh dấu "Không mua được" cho từng dòng rồi hãy hoàn thành, để sau này còn tra lại.\n\nVẫn hoàn thành phiếu?')
          : 'Sau khi hoàn thành, phiếu sẽ chuyển sang mục Đã hoàn thành và không sửa được nữa.',
        'Hoàn thành phiếu');
      if (!ok) return;
      doc.trang_thai = 'Hoàn thành';
      if (!doc.nguoi_mua) doc.nguoi_mua = S.user;
      var _n = new Date(); doc.ngay_hoan_thanh = ymdOf(_n) + ' ' + hmOf(_n);
      await save('Đã hoàn thành phiếu');
    };
    var cn = document.getElementById('rndCancel');
    if (cn) cn.onclick = async function () {
      var ok = await confirmSheet('Huỷ phiếu này?', 'Phiếu sẽ chuyển sang mục Đã huỷ. Nội dung vẫn giữ lại để tra cứu.', 'Huỷ phiếu', true);
      if (!ok) return;
      doc.trang_thai = 'Huỷ';
      await save('Đã huỷ phiếu');
    };
  }
  draw();
}

/* ---------- 16. Boot ---------- */
document.title = APPNAME;

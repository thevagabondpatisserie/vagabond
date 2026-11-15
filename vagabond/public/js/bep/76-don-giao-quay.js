/* ---------- v662 Đơn giao của quầy (WEBORDER, anh Việt chốt 15/11/2026) ----------
   Khách đặt qua tab Tại quầy trên trang chủ, chọn giao tận nơi hoặc tự lấy và
   TRẢ TRƯỚC. Tiền về thì đơn hiện ở dải chờ trên mọi màn (66-goi-mon-tai-ban.js,
   "N đơn giao đã trả tiền chờ xác nhận") và ở màn này. Thu ngân:
     1. Xác nhận, chọn hẹn 10, 15, 20 phút: máy lập phiếu tạm tính ở quầy (món,
        phí giao, phần giảm) để chốt bằng đúng cách khách đã trả.
     2. Hoặc Từ chối kèm lý do: đơn đã trả thì máy báo kế toán hoàn tiền.
     3. Đóng gói xong: Xem giá rồi Gọi xe GreenSM (đơn giao tận nơi).
     4. Khách nhận rồi: Đã giao xong.
   Đơn giao của quầy KHÔNG nằm trong màn Vận đơn của Sales (anh Việt: tách riêng
   theo điểm bán). Máy chủ: vagabond/don_quay.py. */

var DQ = null, DQ_DIEM = '';
var DQ_MAU = { 'Chờ quầy xác nhận': ['#fff7ed', '#9a3412', 'Chờ xác nhận'], 'Đã xác nhận': ['#E4F9FD', '#0B7C93', 'Đang làm'],
  'Đã gọi xe': ['#eef2ff', '#3730a3', 'Đã gọi xe'], 'Đã giao': ['#e9f8ef', '#0b7a3b', 'Đã giao'], 'Từ chối': ['#fdecec', '#9b1c1c', 'Từ chối'] };

/* THUẦN: tiền dạng 120.000 đ. */
function dqTien(n) { return (n === null || n === undefined) ? 'chưa rõ' : money(Number(n) || 0) + ' đ'; }
/* THUẦN: các nút việc được làm ở trạng thái này (trùng don_quay.CHUYEN của máy chủ). */
function dqViec(x) {
  if (x.tt === 'Chờ quầy xác nhận') return ['xac_nhan', 'tu_choi'];
  if (x.tt === 'Đã xác nhận') return x.tu_lay ? ['xong'] : ['goi_xe', 'xong'];
  if (x.tt === 'Đã gọi xe') return ['xong'];
  return [];
}

async function scrDonGiaoQuay(diem) {
  if (diem) DQ_DIEM = diem;
  if (!DQ_DIEM && typeof posQuay !== 'undefined' && posQuay) DQ_DIEM = posQuay.ma || '';
  busy(true);
  try { DQ = await api('vagabond.don_quay.danh_sach', { diem: DQ_DIEM }); }
  catch (e) { busy(false); return toast(e.message || 'Chưa tải được đơn giao.'); }
  busy(false);
  if (DQ && DQ.diem) DQ_DIEM = DQ.diem;
  dqVe();
}

function dqThe(x) {
  var m = DQ_MAU[x.tt] || ['#f6f8fc', '#4a5061', x.tt];
  var mon = (x.mon || []).map(function (d) {
    return '<div style="display:flex;gap:8px;font-size:14px;line-height:1.45"><b style="flex:none;min-width:26px">' + d.sl + '×</b><span>' + h(d.ten) +
      (d.tc ? ' <small style="color:#6b7280">· ' + h(d.tc) + '</small>' : '') + ((d.tp || []).length ? ' <small style="color:#6b7280">+ ' + h(d.tp.join(', ')) + '</small>' : '') + '</span></div>';
  }).join('');
  var nut = dqViec(x).map(function (v) {
    if (v === 'xac_nhan') return '<button class="btn" data-dqxn="' + h(x.ma) + '" style="flex:1;min-height:48px">Xác nhận</button>';
    if (v === 'tu_choi') return '<button class="btn gh" data-dqtc="' + h(x.ma) + '" style="flex:1;min-height:48px">Từ chối</button>';
    if (v === 'goi_xe') return '<button class="btn" data-dqxe="' + h(x.ma) + '" style="flex:1;min-height:48px">Gọi xe GreenSM</button>';
    return '<button class="btn gh" data-dqxong="' + h(x.ma) + '" style="flex:1;min-height:48px">Đã giao xong</button>';
  }).join('');
  return '<div class="card" data-dq="' + h(x.ma) + '" style="padding:12px 13px;margin-bottom:10px">' +
    '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px"><b style="flex:1;font-size:15.5px">' + h(x.ten) + ' · ' + h(x.ma) + '</b>' +
    '<span style="flex:none;background:' + m[0] + ';color:' + m[1] + ';font-weight:700;font-size:13px;border-radius:999px;padding:4px 10px">' + h(m[2]) + '</span></div>' +
    '<div style="font-size:13.5px;color:#4a5061;line-height:1.5;margin-bottom:6px">' + (x.tu_lay ? 'Khách tự lấy tại quầy' : 'Giao tới: ' + h(x.dia_chi)) +
    ' · <a href="tel:' + h(x.sdt) + '" style="color:#0B7C93">' + h(x.sdt) + '</a> · đặt lúc ' + h(String(x.luc).slice(11, 16)) +
    (x.hen ? ' · hẹn ' + x.hen + ' phút' : '') + '</div>' + mon +
    (x.ghi_chu ? '<div style="font-size:13px;color:#93370d;background:#fef0c7;border-radius:8px;padding:6px 9px;margin-top:6px">' + h(x.ghi_chu) + '</div>' : '') +
    '<div style="font-size:13.5px;margin-top:8px;line-height:1.5">Đã trả ' + dqTien(x.da_thu) + ' qua ' + h(x.cach_thu || 'chuyển khoản') +
    (x.tu_lay ? '' : ' · phí giao ' + (x.mien_phi ? 'miễn phí' : dqTien(x.phi))) + (x.giam ? ' · giảm ' + dqTien(x.giam) : '') + '</div>' +
    (x.gsm_link ? '<div style="margin-top:6px"><a href="' + h(x.gsm_link) + '" target="_blank" rel="noopener" style="color:#0B7C93;font-weight:700;font-size:14px;display:inline-flex;align-items:center;min-height:44px">Theo dõi tài xế ↗</a></div>' : '') +
    (x.bill ? '<button data-dqbill="' + h(x.bill) + '" style="border:0;background:none;color:#0B7C93;font-weight:700;font-size:14px;min-height:44px;padding:0;cursor:pointer">Mở phiếu tạm tính ' + h(x.bill) + '</button>' : '') +
    (x.tt === 'Từ chối' ? '<div style="font-size:13px;color:#9b1c1c;margin-top:4px">Lý do: ' + h(x.ly_do) + (x.can_hoan ? ' · đã báo kế toán hoàn tiền' : '') + '</div>' : '') +
    (nut ? '<div style="display:flex;gap:8px;margin-top:10px">' + nut + '</div>' : '') + '</div>';
}

function dqVe() {
  var ds = (DQ && DQ.ds) || [];
  var dang = ds.filter(function (x) { return ['Đã giao', 'Từ chối'].indexOf(x.tt) < 0; });
  var xong = ds.filter(function (x) { return ['Đã giao', 'Từ chối'].indexOf(x.tt) >= 0; });
  var html = '<div class="card" style="padding:12px 14px;font-size:13.5px;color:#4a5061;line-height:1.5">' +
    'Khách đặt qua tab Tại quầy trên trang chủ và đã trả online. Xác nhận thì máy lập phiếu tạm tính để chốt bằng đúng cách khách đã trả; đóng gói xong bấm Gọi xe GreenSM. ' +
    'Đơn ở đây không nằm trong màn Vận đơn của Sales.</div>' +
    (((DQ && DQ.cac_diem) || []).length > 1 ? '<div style="display:flex;flex-wrap:wrap;gap:8px;margin:0 0 10px">' + DQ.cac_diem.map(function (d) {
      return posChipNut('data-dqdiem="' + h(d.ma) + '"', h(d.ten), d.ma === DQ_DIEM, false, '#0B7C93');
    }).join('') + '</div>' : '') +
    (dang.length ? dang.map(dqThe).join('') : '<div class="emp"><div class="e1">✅</div><div>Không có đơn giao nào đang chờ.</div></div>') +
    (xong.length ? '<div class="sec">Xong hoặc từ chối trong 24 giờ</div>' + xong.map(dqThe).join('') : '');
  var b = frame('Đơn giao của quầy · ' + h((DQ && DQ.ten_diem) || DQ_DIEM), html, { footer: '<button class="btn gh" id="dqTai">Tải lại</button>' });
  b.addEventListener('click', dqBam);
  var t = document.getElementById('dqTai');
  if (t) t.onclick = function () { scrDonGiaoQuay(); };
}

function dqMoHop(tieuDe, chon, nhan, laDo, xong) {
  var duoc = '', hop = document.createElement('div'); hop.className = 'sh';
  function ve() {
    hop.innerHTML = '<div class="shb" style="padding:18px 16px calc(env(safe-area-inset-bottom,0px) + 16px)">' +
      '<div style="font-size:17.5px;font-weight:700;margin-bottom:10px">' + h(tieuDe) + '</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px">' + chon.map(function (c) {
        return posChipNut('data-dqchon="' + h(c[0]) + '"', h(c[1]), duoc === String(c[0]), false, laDo ? '#b91c1c' : '#0B7C93');
      }).join('') + '</div>' +
      '<button class="btn' + (laDo ? ' dg' : '') + '" data-dqok="1"' + (duoc ? '' : ' disabled style="opacity:.5"') + '>' + h(nhan) + '</button>' +
      '<button class="btn gh" data-dqhuy="1" style="margin-top:9px">Quay lại</button></div>';
  }
  ve();
  document.body.appendChild(hop);
  hop.onclick = async function (e) {
    if (e.target === hop || e.target.closest('[data-dqhuy]')) return hop.remove();
    var c = e.target.closest('[data-dqchon]');
    if (c) { duoc = c.getAttribute('data-dqchon'); return ve(); }
    if (!e.target.closest('[data-dqok]') || !duoc) return;
    hop.remove();
    await xong(duoc);
  };
}

async function dqGoi(ham, than, cau) {
  busy(true);
  try { var kq = await api('vagabond.don_quay.' + ham, than); busy(false); if (cau) toast(cau); return kq; }
  catch (e) { busy(false); toast(e.message || 'Chưa làm được, tải lại danh sách rồi thử lại.'); return null; }
  finally { scrDonGiaoQuay(); }
}

async function dqBam(e) {
  var x;
  if ((x = e.target.closest('[data-dqdiem]'))) return scrDonGiaoQuay(x.getAttribute('data-dqdiem'));
  if ((x = e.target.closest('[data-dqxn]'))) {
    var ma = x.getAttribute('data-dqxn');
    return dqMoHop('Xác nhận đơn ' + ma + ', hẹn xong sau', ((DQ && DQ.hen) || [10, 15, 20]).map(function (p) { return [p, p + ' phút']; }), 'Xác nhận đơn', false,
      function (p) { return dqGoi('xac_nhan', { ma: ma, hen: p }, 'Đã xác nhận, phiếu tạm tính đã lập.'); });
  }
  if ((x = e.target.closest('[data-dqtc]'))) {
    var ma2 = x.getAttribute('data-dqtc');
    return dqMoHop('Từ chối đơn ' + ma2, ((DQ && DQ.ly_do) || ['Hết món', 'Khác']).map(function (l) { return [l, l]; }), 'Từ chối đơn', true,
      function (l) { return dqGoi('tu_choi', { ma: ma2, ly_do: l }, 'Đã từ chối. Đơn đã trả thì kế toán nhận tin hoàn tiền.'); });
  }
  if ((x = e.target.closest('[data-dqxong]'))) {
    var ma3 = x.getAttribute('data-dqxong');
    if (!(await confirmSheet('Đã giao xong', 'Khách đã nhận đơn ' + ma3 + '.', 'Đã giao xong'))) return;
    return dqGoi('xong', { ma: ma3 }, 'Đã ghi đã giao.');
  }
  if ((x = e.target.closest('[data-dqxe]'))) {
    var ma4 = x.getAttribute('data-dqxe');
    busy(true);
    var g;
    try { g = await api('vagabond.don_quay.gsm_bao_gia', { ma: ma4 }); } catch (er) { busy(false); return toast(er.message || 'GreenSM chưa báo được giá.'); }
    busy(false);
    if (!(await confirmSheet('Gọi xe GreenSM', 'Cước tiệm trả: ' + dqTien(g.tong) + (g.km ? ' · ' + g.km + ' km' : '') + '. Gọi xe cho đơn ' + ma4 + '?', 'Gọi xe'))) return;
    return dqGoi('goi_xe', { ma: ma4, ma_gia: g.ma_gia }, 'Đã gọi xe. Link theo dõi tài xế hiện trên thẻ đơn.');
  }
  if ((x = e.target.closest('[data-dqbill]'))) { var bill = x.getAttribute('data-dqbill'); return go(function () { scrPosBill(bill); }); }
}

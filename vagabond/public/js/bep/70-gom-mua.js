/* ---------- 70. Gom yêu cầu mua thành đơn mua (v646) ----------

   Anh Việt 09/11/2026: "Tổng hợp từ mấy cái đơn yêu cầu mua hàng của các bộ
   phận gửi lên ấy. Rồi staff thu mua vào chỉ việc sửa số rồi chốt."

   Máy chủ (vagabond/gom_mua.py) gom mọi dòng yêu cầu mua đã gửi mà chưa ai
   duyệt, chia theo nhà cung cấp mặc định, cộng theo món. Số mua điền sẵn bằng
   tổng số xin (số ĐẶT, điền sẵn được), thu mua sửa rồi bấm Chốt cho từng nhà
   cung cấp. Máy chủ đọc lại các dòng lúc chốt, ghi phần duyệt lên từng phiếu
   xin và lập đơn mua; màn này chỉ gửi mã món và số mua.

   Tiền tố gm = gom mua. */

var GM = { d: null, sua: {}, mo: {} };

/* THUẦN: số mua đang hiện của một món (đã gõ thì theo số gõ, chưa thì số máy). */
function gmSoMua(m) {
  var k = m.ma;
  return GM.sua[k] != null ? GM.sua[k] : m.mua;
}

/* THUẦN: dòng gửi lên khi chốt một nhóm. */
function gmDongChot(nhom) {
  return (nhom.mon || []).map(function (m) { return { ma: m.ma, sl: gmSoMua(m) }; });
}

/* THUẦN: tiền tạm tính của nhóm theo số đang hiện (giá lần mua gần nhất). */
function gmTien(nhom) {
  return Math.round((nhom.mon || []).reduce(function (t, m) { return t + (Number(gmSoMua(m)) || 0) * (m.gia || 0); }, 0));
}

function gmMon(m, i) {
  var mo = !!GM.mo[m.ma];
  var lech = Math.abs((Number(gmSoMua(m)) || 0) - m.xin) > 0.0001;
  return '<div class="khsx-the"><div class="li" data-gmmo="' + h(m.ma) + '">' + anhMon(m.anh) +
    '<div class="lt"><div class="l1">' + h(m.ten) + '</div>' +
    '<div class="l2">Xin ' + kl(m.xin, m.dvt) + ' · ' + m.phieu.length + ' phiếu' +
    (m.ngay_can ? ' · cần ' + h(dmy(m.ngay_can)) : '') + '</div>' +
    '<div class="l2">Kho tổng ' + kl(m.ton, m.dvt) + (m.cho_ve > 0 ? ' · <b style="color:#b45309">chờ về ' + kl(m.cho_ve, m.dvt) + '</b>' : '') +
    (m.gia ? ' · giá lần trước ' + money(m.gia) + ' đ' : '') + '</div></div>' +
    '<input class="tin" data-gmsl="' + h(m.ma) + '" inputmode="decimal" value="' + h(gmSoMua(m)) + '" ' +
    'style="width:84px;margin:0;text-align:center;flex:none' + (lech ? ';border-color:#0B7C93;font-weight:700' : '') + '" aria-label="Số mua ' + h(m.ten) + '">' +
    '</div>' +
    (mo ? '<div style="padding:0 14px 10px 70px;font-size:12.5px;color:#5a6070;line-height:1.7">' +
      m.phieu.map(function (p) {
        return h(p.phieu) + ' · ' + h(p.bo_phan || 'bộ phận chưa ghi') + ' · ' + kl(p.xin, m.dvt) + (p.ngay ? ' · cần ' + h(dmy(p.ngay)) : '');
      }).join('<br>') + '</div>' : '') +
    '</div>';
}

function gmNhom(g, i) {
  return '<div class="sec">' + h(g.ten_ncc) + ' · ' + g.so_mon + ' món · ' + g.so_phieu + ' phiếu</div>' +
    '<div class="lst">' + g.mon.map(gmMon).join('') + '</div>' +
    '<div style="display:flex;align-items:center;gap:10px;margin:8px 0 16px">' +
    '<div style="flex:1;font-size:12.5px;color:#6b7280">' + (g.ncc ? 'Tạm tính ' + money(gmTien(g)) + ' đ' : 'Nhóm này chưa có nhà cung cấp, bấm Chốt để chọn') + '</div>' +
    '<button class="btn gr" data-gmchot="' + i + '" style="flex:0 0 auto;width:auto;padding:0 16px;margin:0">Chốt ' + h(g.ncc ? g.ten_ncc : 'nhóm này') + '</button></div>';
}

async function scrGomMua(giu) {
  if (!coQuyenMua()) {
    frame('Gom yêu cầu mua', '<div class="emp"><div class="e1">🔒</div><div class="e2">Màn này chỉ mở cho Thu mua, Kế toán và Giám đốc.</div></div>');
    return;
  }
  if (!giu || !GM.d) {
    frame('Gom yêu cầu mua', '<div class="emp"><div class="e1">⏳</div></div>');
    try { GM.d = await api('vagabond.gom_mua.ds', {}); GM.sua = {}; }
    catch (e) {
      frame('Gom yêu cầu mua', '<div class="emp"><div class="e1">⚠️</div><div class="e2">' + h(errMsg(e)) + '</div></div>');
      return;
    }
  }
  var d = GM.d, nhom = d.nhom || [];
  var html = '<div class="card" style="padding:12px 14px;font-size:13.5px;line-height:1.55;color:#374151">' +
    'Máy gom <b>' + d.so_dong + ' dòng</b> từ <b>' + d.so_phieu + ' phiếu</b> yêu cầu mua chưa duyệt, chia theo nhà cung cấp. ' +
    'Số mua điền sẵn bằng tổng số xin: sửa nếu cần (gõ 0 là chưa mua đợt này), rồi bấm Chốt. ' +
    'Bấm vào món để xem từng phiếu xin.</div>' +
    (nhom.length ? nhom.map(gmNhom).join('')
      : '<div class="emp"><div class="e1">🎉</div><div class="e2">Không còn yêu cầu mua nào chờ gom</div></div>');
  var b = frame('Gom yêu cầu mua', html, { action: '&#8635;', onAction: function () { GM.d = null; scrGomMua(); } });
  Array.prototype.forEach.call(b.querySelectorAll('[data-gmsl]'), function (o) {
    o.onclick = function (ev) { ev.stopPropagation(); };
    o.oninput = function () {
      var v = parseFloat(String(o.value).replace(',', '.'));
      GM.sua[o.dataset.gmsl] = isNaN(v) ? null : v;
    };
  });
  b.onclick = async function (e) {
    var c = e.target.closest('[data-gmchot]');
    if (c) return gmChot(nhom[+c.dataset.gmchot]);
    var m = e.target.closest('[data-gmmo]');
    if (m) { GM.mo[m.dataset.gmmo] = GM.mo[m.dataset.gmmo] ? 0 : 1; return scrGomMua(1); }
  };
}

async function gmChot(g) {
  if (!g) return;
  var dong = gmDongChot(g);
  var hong = dong.filter(function (x) { return x.sl == null || isNaN(Number(x.sl)) || Number(x.sl) < 0; });
  if (hong.length) return toast('Còn ô số mua để trống hoặc gõ sai, gõ 0 nếu chưa mua đợt này', 5000);
  var ncc = '';
  if (!g.ncc) {
    ncc = await promptSheet('Nhà cung cấp cho nhóm này', 'Gõ đúng mã nhà cung cấp trong danh mục');
    if (!ncc) return;
  }
  var so0 = dong.filter(function (x) { return Number(x.sl) === 0; }).length;
  if (!await confirmSheet('Chốt đơn ' + (g.ncc ? g.ten_ncc : ncc) + '?',
    'Máy duyệt ' + g.so_phieu + ' phiếu xin theo số đang hiện và lập đơn mua ' + (dong.length - so0) + ' món.' +
    (so0 ? '\n\n' + so0 + ' món gõ 0: các dòng xin đó bị từ chối, ghi lý do "chưa mua đợt này".' : '') +
    '\n\nĐơn mua chưa gửi nhà cung cấp; gửi ở màn Đơn mua hàng.', 'Chốt đơn')) return;
  busy(1);
  try {
    var r = await api('vagabond.gom_mua.chot', { ncc: g.ncc, dong: JSON.stringify(dong), ncc_chon: ncc || null });
    toast(r.ghi_chu, 8000);
    GM.d = null;
    if (r.don) { poXem = r.don; return go(scrDonMuaXem); }
    await scrGomMua();
  } catch (e) { toast(errMsg(e), 7000); } finally { busy(0); }
}

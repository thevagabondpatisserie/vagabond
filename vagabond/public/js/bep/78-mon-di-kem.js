/* v668 Món đi kèm (anh Việt duyệt 17/11/2026, phần F prompt /banh). Marketing, bếp duyệt
   các cặp Món gốc - Món gợi ý cho khối Gợi ý mua thêm trên web (goi_y_mua.py).
   Bốn phần: Cặp gợi ý (xem theo món gốc; giữ, sửa câu, bỏ, ghim; chọn nhiều dòng duyệt
   một lần), Mức giữ tại bếp (món đang dưới mức), Kết quả (đơn mới), Cài đặt. */
var MDK_P = 'vagabond.goi_y_mua.';
var MDK = { phan: 'cap', tt: 'Nháp', tim: '', chon: {}, dl: null };
var MDK_QUYEN = ['Marketing', 'System Manager', 'Giám đốc', 'AP Giám đốc'];
function coQuyenMonDiKem() { return MDK_QUYEN.some(function (v) { return hasRole(v); }); }
var MDK_TT = [['Nháp', 'Chờ duyệt', 'Bản nháp, web chưa dùng.'], ['Đã duyệt', 'Đã duyệt', 'Web đang dùng để gợi ý.'], ['Bỏ', 'Đã bỏ', 'Không dùng nữa.']];

function mdkChip(attr, gt, chu, on, so) {
  return '<button type="button" ' + attr + '="' + h(gt) + '" aria-pressed="' + (on ? 'true' : 'false') + '" style="flex:0 0 auto;min-height:44px;padding:0 14px;border-radius:22px;' +
    'border:1px solid ' + (on ? '#0B7C93' : '#d0d5dd') + ';background:' + (on ? '#e6f8fb' : '#fff') + ';font:inherit;font-size:14px;font-weight:' + (on ? 800 : 600) +
    ';color:' + (on ? '#05323C' : '#344054') + '">' + h(chu) + (so !== undefined ? ' <b>' + so + '</b>' : '') + '</button>';
}
function mdkGhim(c) { return c.ghim_tu || c.ghim_den ? '📌 ' + (c.ghim_tu ? h(c.ghim_tu.slice(8, 10) + '/' + c.ghim_tu.slice(5, 7)) : '') + ' - ' + (c.ghim_den ? h(c.ghim_den.slice(8, 10) + '/' + c.ghim_den.slice(5, 7)) : '...') : ''; }

/* THUẦN: gom các cặp theo món gốc (hoặc nhóm món gốc), giữ thứ tự máy chủ trả. */
function mdkGom(ds) {
  var ra = [], theo = {};
  (ds || []).forEach(function (c) {
    var k = c.mon_goc ? c.mon_goc : ('Nhóm ' + (c.nhom_goc || ''));
    if (!theo[k]) { theo[k] = { goc: k, nhom: !c.mon_goc, ds: [] }; ra.push(theo[k]); }
    theo[k].ds.push(c);
  });
  return ra;
}

async function scrMonDiKem() {
  var tieuDe = 'Món đi kèm';
  if (MDK.phan === 'muc') return mdkMucGiu(tieuDe);
  if (MDK.phan === 'kq') return mdkKetQua(tieuDe);
  frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang đọc bảng món đi kèm...</div></div>');
  /* Đổi chip, gõ tìm liên tiếp: lượt trả lời cũ đến muộn không được vẽ đè lượt mới. */
  var luot = MDK.luot = (MDK.luot || 0) + 1, dl;
  try { dl = await api(MDK_P + 'man_hinh', { trang_thai: MDK.tt, tim: MDK.tim }); }
  catch (e) { if (luot !== MDK.luot) return; return frame(tieuDe, '<div class="emp"><div class="e1">⚠️</div><div>' + h(errMsg(e)) + '</div></div>'); }
  if (luot !== MDK.luot) return;
  MDK.dl = dl;
  if (MDK.phan === 'cd') return mdkCaiDat(tieuDe, dl.cai_dat || {});
  return mdkVeCap(tieuDe, dl);
}

/* Vẽ phần Cặp gợi ý từ dữ liệu đã có (chọn dòng không hỏi lại máy chủ). */
function mdkVeCap(tieuDe, dl) {
  var dem = dl.dem || {}, chon = Object.keys(MDK.chon).filter(function (n) { return MDK.chon[n]; });
  var nhom = mdkGom(dl.cap);
  var html = mdkPhan() +
    '<div style="font-size:13.5px;color:#667085;margin:10px 2px 6px">Web chỉ dùng cặp Đã duyệt. Món chưa có cặp duyệt thì web gợi ý theo nhóm, câu chung ở Cài đặt.</div>' +
    '<div style="display:flex;gap:8px;overflow-x:auto;padding:2px 0 8px">' + MDK_TT.map(function (x) { return mdkChip('data-mdktt', x[0], x[1], MDK.tt === x[0], dem[x[0]] || 0); }).join('') + '</div>' +
    '<input id="mdkTim" type="search" value="' + h(MDK.tim) + '" placeholder="Tìm món gốc, món gợi ý, câu lý do" style="width:100%;box-sizing:border-box;min-height:48px;border:1px solid #d0d5dd;border-radius:12px;padding:0 14px;font:inherit;font-size:16px;margin-bottom:8px">' +
    (nhom.length ? nhom.map(function (g) {
      var tatCa = g.ds.every(function (c) { return MDK.chon[c.name]; });
      return '<div class="card" style="padding:8px 12px"><div style="display:flex;align-items:center;gap:8px;min-height:44px">' +
        '<b style="flex:1;min-width:0;font-size:15px;text-transform:capitalize">' + h(g.goc) + '</b>' +
        '<button type="button" data-mdkchonnhom="' + h(g.goc) + '" style="min-height:44px;border:0;background:none;font:inherit;font-size:13.5px;font-weight:700;color:#0B7C93;padding:0 6px">' + (tatCa ? 'Bỏ chọn' : 'Chọn cả món') + '</button></div>' +
        g.ds.map(function (c) {
          return '<div style="display:flex;gap:10px;align-items:center;border-top:1px solid #f2f4f7;min-height:56px">' +
            '<button type="button" role="checkbox" aria-checked="' + (MDK.chon[c.name] ? 'true' : 'false') + '" data-mdkchon="' + h(c.name) + '" aria-label="Chọn dòng ' + h(c.ten_goi_y || c.mon_goi_y) + '" style="flex:0 0 44px;width:44px;height:44px;border:0;background:none;padding:0;font-size:22px">' + (MDK.chon[c.name] ? '☑️' : '⬜') + '</button>' +
            '<button type="button" data-mdksua="' + h(c.name) + '" style="flex:1;min-width:0;min-height:52px;border:0;background:none;font:inherit;text-align:left;padding:6px 0">' +
            '<span style="display:block;font-size:15px;font-weight:700">' + h(c.ten_goi_y || c.mon_goi_y) + '</span>' +
            '<span style="display:block;font-size:13.5px;color:#0B7C93">' + h(c.ly_do_vn || 'Chưa có câu lý do') + '</span>' +
            (mdkGhim(c) ? '<span style="display:block;font-size:13px;color:#667085">' + mdkGhim(c) + '</span>' : '') + '</button></div>';
        }).join('') + '</div>';
    }).join('') : '<div class="emp"><div class="e1">🍰</div><div>Không có cặp nào ở mục này.</div></div>');
  var chan = chon.length ? '<div style="display:flex;gap:8px">' +
    (MDK.tt !== 'Đã duyệt' ? '<button class="btn" data-mdkdoi="Đã duyệt" style="margin:0;flex:1.4">Duyệt ' + chon.length + ' dòng</button>' : '') +
    (MDK.tt !== 'Bỏ' ? '<button class="btn gh" data-mdkdoi="Bỏ" style="margin:0;flex:1">Bỏ ' + chon.length + ' dòng</button>' : '') +
    (MDK.tt !== 'Nháp' ? '<button class="btn gh" data-mdkdoi="Nháp" style="margin:0;flex:1">Về nháp</button>' : '') + '</div>'
    : '<button class="btn gh" data-mdkmoi="1" style="margin:0">＋ Thêm cặp</button>';
  var b = frame(tieuDe, html, { footer: chan });
  mdkNghePhan(b);
  var vf = document.querySelector('.vf');
  if (vf) vf.onclick = async function (e) {
    var n = e.target.closest('[data-mdkdoi]');
    if (n) {
      var tt = n.getAttribute('data-mdkdoi'), ds = Object.keys(MDK.chon).filter(function (k) { return MDK.chon[k]; });
      n.disabled = true;
      try { var r = await api(MDK_P + 'doi_nhieu', { ten: JSON.stringify(ds), trang_thai: tt }); toast('Đã chuyển ' + (r.doi || 0) + ' dòng sang ' + (tt === 'Đã duyệt' ? 'Đã duyệt' : tt === 'Bỏ' ? 'Đã bỏ' : 'Chờ duyệt')); MDK.chon = {}; }
      catch (er) { toast(errMsg(er)); }
      return scrMonDiKem();
    }
    if (e.target.closest('[data-mdkmoi]')) mdkSua(null);
  };
  var o = document.getElementById('mdkTim');
  if (o) o.onchange = function () { MDK.tim = o.value.trim(); MDK.chon = {}; scrMonDiKem(); };
  b.onclick = function (e) {
    var n;
    if ((n = e.target.closest('[data-mdktt]'))) { MDK.tt = n.getAttribute('data-mdktt'); MDK.chon = {}; return scrMonDiKem(); }
    if ((n = e.target.closest('[data-mdkchon]'))) { var k = n.getAttribute('data-mdkchon'); MDK.chon[k] = !MDK.chon[k]; return mdkVeCap(tieuDe, MDK.dl); }
    if ((n = e.target.closest('[data-mdkchonnhom]'))) {
      var g = mdkGom(MDK.dl.cap).filter(function (x) { return x.goc === n.getAttribute('data-mdkchonnhom'); })[0];
      var bat = !g.ds.every(function (c) { return MDK.chon[c.name]; });
      g.ds.forEach(function (c) { MDK.chon[c.name] = bat; });
      return mdkVeCap(tieuDe, MDK.dl);
    }
    if ((n = e.target.closest('[data-mdksua]'))) return mdkSua((MDK.dl.cap || []).filter(function (c) { return c.name === n.getAttribute('data-mdksua'); })[0]);
  };
}

function mdkPhan() {
  return '<div role="tablist" style="display:flex;background:#eef0f5;border-radius:12px;padding:3px;gap:3px">' +
    [['cap', 'Cặp gợi ý'], ['muc', 'Mức giữ'], ['kq', 'Kết quả'], ['cd', 'Cài đặt']].map(function (x) {
      var on = MDK.phan === x[0];
      return '<button role="tab" aria-selected="' + on + '" data-mdkphan="' + x[0] + '" style="flex:1;min-height:44px;border:0;border-radius:10px;font:inherit;font-size:14px;font-weight:' +
        (on ? 800 : 600) + ';background:' + (on ? '#fff' : 'transparent') + ';color:' + (on ? '#05323C' : '#667085') + '">' + x[1] + '</button>';
    }).join('') + '</div>';
}
function mdkNghePhan(b) {
  b.addEventListener('click', function (e) {
    var n = e.target.closest('[data-mdkphan]');
    if (n) { e.stopImmediatePropagation(); MDK.phan = n.getAttribute('data-mdkphan'); MDK.chon = {}; scrMonDiKem(); }
  }, true);
}

function mdkSua(c) {
  c = c || { trang_thai: 'Nháp', uu_tien: 10 };
  var o = function (id, nhan, gt, phu, kieu) {
    return '<label style="display:block;margin:10px 0 0;font-size:14px;font-weight:700">' + nhan +
      (phu ? '<span style="display:block;font-size:13px;font-weight:500;color:#667085">' + phu + '</span>' : '') +
      '<input id="' + id + '" type="' + (kieu || 'text') + '" value="' + h(gt || '') + '" style="display:block;width:100%;box-sizing:border-box;min-height:48px;margin-top:6px;border:1px solid #d0d5dd;border-radius:12px;padding:0 12px;font:inherit;font-size:16px"></label>';
  };
  var ov = crmMoSheet('<div style="font-size:17px;font-weight:800">' + (c.name ? h(c.ten_goi_y || c.mon_goi_y) : 'Thêm cặp món đi kèm') + '</div>' +
    (c.name ? '<div style="font-size:13.5px;color:#667085">Đi kèm: <b style="text-transform:capitalize">' + h(c.mon_goc || ('Nhóm ' + (c.nhom_goc || ''))) + '</b></div>'
      : o('mdkGoc', 'Món gốc', '', 'Tên bánh trên web, viết như thẻ Bánh (ví dụ: candle). Để trống nếu dùng nhóm món.') +
        o('mdkNhom', 'Nhóm món gốc', '', 'Ví dụ: Bánh lạnh. Dùng cho khung Đặt giao của Tại quầy.') + o('mdkMa', 'Mã món gợi ý', '', 'Mã in trên tem, ví dụ BACF00034.')) +
    o('mdkVn', 'Câu lý do', c.ly_do_vn, 'Dưới 40 ký tự, hiện màu xanh dưới tên món.') + o('mdkEn', 'Câu lý do tiếng Anh', c.ly_do_en) +
    '<div style="display:flex;gap:8px">' + '<div style="flex:1">' + o('mdkTu', 'Ghim từ', c.ghim_tu, '', 'date') + '</div><div style="flex:1">' + o('mdkDen', 'Ghim đến', c.ghim_den, '', 'date') + '</div></div>' +
    '<div style="font-size:13px;color:#667085;margin-top:4px">Trong khoảng ghim, món này luôn đứng đầu khối gợi ý.</div>' +
    o('mdkUt', 'Thứ tự ưu tiên', String(c.uu_tien || 10), 'Số nhỏ đứng trước khi cùng được ghim.', 'number') +
    '<div style="display:flex;gap:8px;margin-top:14px"><button class="btn gh" data-mdkluu="Bỏ" style="margin:0;flex:1">Bỏ cặp này</button>' +
    '<button class="btn" data-mdkluu="Đã duyệt" style="margin:0;flex:1.4">Lưu và duyệt</button></div>' +
    '<button class="btn gh" data-mdkluu="Nháp" style="margin:8px 0 0">Lưu nháp</button>');
  ov.onclick = async function (e) {
    var n = e.target.closest('[data-mdkluu]'); if (!n) return;
    var v = function (id) { var x = ov.querySelector('#' + id); return x ? x.value.trim() : undefined; };
    var d = { name: c.name || '', ly_do_vn: v('mdkVn'), ly_do_en: v('mdkEn'), ghim_tu: v('mdkTu'), ghim_den: v('mdkDen'), uu_tien: +v('mdkUt') || 10, trang_thai: n.getAttribute('data-mdkluu') };
    if (!c.name) { d.mon_goc = v('mdkGoc'); d.nhom_goc = v('mdkNhom'); d.mon_goi_y = v('mdkMa'); }
    n.disabled = true;
    try { await api(MDK_P + 'luu_cap', { du_lieu: JSON.stringify(d) }); ov.remove(); toast('Đã lưu'); scrMonDiKem(); }
    catch (er) { n.disabled = false; toast(errMsg(er)); }
  };
}

async function mdkMucGiu(tieuDe) {
  frame(tieuDe, mdkPhan() + '<div class="emp"><div class="e1">⏳</div><div>Đang đọc tồn bếp...</div></div>');
  var luot = MDK.luot = (MDK.luot || 0) + 1, dl;
  try { dl = await api(MDK_P + 'duoi_muc_giu'); } catch (e) { dl = { loi: errMsg(e), mon: [] }; }
  if (luot !== MDK.luot) return;
  var html = mdkPhan() + '<div style="font-size:13.5px;color:#667085;margin:10px 2px">Bánh khô có Mức giữ tại bếp cho đơn web. Phiếu chuyển ra cửa hàng làm tồn bếp xuống dưới mức thì hệ thống cảnh báo, không chặn. Đặt mức ở dòng dưới cùng.</div>' +
    (dl.loi ? '<div class="emp"><div class="e1">⚠️</div><div>' + h(dl.loi) + '</div></div>' :
      (dl.mon.length ? '<div class="card" style="padding:6px 12px">' + dl.mon.map(function (m) {
        return '<div style="display:flex;align-items:center;gap:10px;min-height:52px;border-top:1px solid #f2f4f7"><div style="flex:1;min-width:0"><b style="font-size:15px">' + h(m.ten) + '</b>' +
          '<div style="font-size:13.5px;color:#b42318">Tồn bếp ' + money(m.ton) + ', mức giữ ' + money(m.muc) + '</div></div></div>';
      }).join('') + '</div>' : '<div class="emp"><div class="e1">✅</div><div>' + (dl.co_muc ? 'Không món nào dưới mức giữ.' : 'Chưa món nào có mức giữ.') + '</div></div>')) +
    '<div class="card" style="padding:10px 12px"><b style="font-size:15px">Đặt mức giữ cho một món</b>' +
    '<input id="mdkMucMa" placeholder="Mã món, ví dụ BACF00034" style="display:block;width:100%;box-sizing:border-box;min-height:48px;margin-top:8px;border:1px solid #d0d5dd;border-radius:12px;padding:0 12px;font:inherit;font-size:16px">' +
    '<input id="mdkMucSo" type="number" min="0" placeholder="Số giữ, 0 là bỏ giữ" style="display:block;width:100%;box-sizing:border-box;min-height:48px;margin-top:8px;border:1px solid #d0d5dd;border-radius:12px;padding:0 12px;font:inherit;font-size:16px">' +
    '<button class="btn" id="mdkMucLuu" style="margin:10px 0 0">Lưu mức giữ</button></div>';
  var b = frame(tieuDe, html);
  mdkNghePhan(b);
  var n = document.getElementById('mdkMucLuu');
  if (n) n.onclick = async function () {
    n.disabled = true;
    try { await api(MDK_P + 'dat_muc_giu', { ma: document.getElementById('mdkMucMa').value.trim(), so: document.getElementById('mdkMucSo').value }); toast('Đã lưu mức giữ'); mdkMucGiu(tieuDe); }
    catch (e) { n.disabled = false; toast(errMsg(e)); }
  };
}

async function mdkKetQua(tieuDe) {
  frame(tieuDe, mdkPhan() + '<div class="emp"><div class="e1">⏳</div><div>Đang tính...</div></div>');
  var luot = MDK.luot = (MDK.luot || 0) + 1, r;
  try { r = await api(MDK_P + 'bao_cao_goi_y', { ngay: 30 }); } catch (e) { r = { loi: errMsg(e) }; }
  if (luot !== MDK.luot) return;
  var o = function (so, chu) { return '<div style="flex:1;min-width:0;padding:6px"><b style="font-size:22px">' + so + '</b><div style="font-size:13px;color:#667085">' + chu + '</div></div>'; };
  var html = mdkPhan() + (r.loi ? '<div class="emp"><div class="e1">⚠️</div><div>' + h(r.loi) + '</div></div>' :
    '<div style="font-size:13.5px;color:#667085;margin:10px 2px">30 ngày gần nhất, chỉ đơn từ bản này trở đi (đơn cũ không có dấu thêm từ gợi ý).</div>' +
    '<div class="card" style="display:flex;flex-direction:row;flex-wrap:wrap;padding:6px">' + o(money(r.ti_le) + '%', 'đơn có món mua thêm (' + r.don_co_goi_y + '/' + r.so_don + ')') +
    o(money(r.gia_tri_tb) + ' đ', 'giá trị đơn trung bình') + o(money(r.gia_tri_tb_co_goi_y) + ' đ', 'đơn có món mua thêm') + '</div>' +
    '<div class="card" style="padding:6px 12px"><b style="font-size:15px">Món được thêm nhiều nhất</b>' + ((r.mon || []).length ? r.mon.map(function (m) {
      return '<div style="display:flex;gap:8px;min-height:44px;align-items:center;border-top:1px solid #f2f4f7"><span style="flex:1;min-width:0">' + h(m.ten) + '</span><b>' + m.sl + '</b></div>';
    }).join('') : '<div style="font-size:14px;color:#667085;padding:8px 0">Chưa có đơn nào thêm món từ gợi ý.</div>') + '</div>');
  mdkNghePhan(frame(tieuDe, html));
}

function mdkCaiDat(tieuDe, cd) {
  var dong = function (k, chu, phu) {
    return '<div style="display:flex;align-items:center;gap:10px;min-height:56px;border-top:1px solid #f2f4f7"><div style="flex:1;min-width:0"><b style="font-size:15px">' + chu + '</b>' +
      '<div style="font-size:13px;color:#667085">' + phu + '</div></div>' + crmCongTac('data-mdkbat="' + k + '"', !!cd[k]) + '</div>';
  };
  var o = function (id, chu, phu, gt, kieu) {
    return '<label style="display:block;margin-top:10px;font-size:15px;font-weight:700">' + chu + '<span style="display:block;font-size:13px;font-weight:500;color:#667085">' + phu + '</span>' +
      (kieu === 'vung' ? '<textarea id="' + id + '" rows="3" style="display:block;width:100%;box-sizing:border-box;margin-top:6px;border:1px solid #d0d5dd;border-radius:12px;padding:10px 12px;font:inherit;font-size:16px">' + h(gt) + '</textarea>'
        : '<input id="' + id + '" type="number" min="0" value="' + h(gt) + '" style="display:block;width:100%;box-sizing:border-box;min-height:48px;margin-top:6px;border:1px solid #d0d5dd;border-radius:12px;padding:0 12px;font:inherit;font-size:16px">') + '</label>';
  };
  var html = mdkPhan() + '<div class="card" style="padding:4px 12px">' +
    dong('bat_gio', 'Giỏ đặt trước', 'Khối Giao kèm cùng chuyến dưới nút Chọn thêm bánh.') +
    dong('bat_quay', 'Tại quầy', 'Khối Uống kèm, Ăn kèm trong khung Đặt giao.') +
    dong('bat_dbt', 'Đặc biệt tuần này', 'Tắt: giỏ có món cuối tuần thì không gợi ý.') +
    dong('thanh_mien_phi', 'Thanh miễn phí giao', 'Hiện số tiền còn thiếu để được miễn phí giao.') + '</div>' +
    '<div class="card" style="padding:4px 12px 12px">' +
    o('mdkToiDa', 'Số món tối đa', 'Từ 1 tới 6.', cd.toi_da) + o('mdkNguong', 'Ngưỡng tồn tối thiểu', 'Chỉ gợi ý món còn từ số này trở lên ở đúng nơi xuất đơn.', cd.nguong) +
    o('mdkNhomGy', 'Nhóm món được đem ra gợi ý', 'Mỗi dòng một nhóm món.', (cd.nhom || []).join('\n'), 'vung') +
    o('mdkKho', 'Kho bếp xuất đơn đặt trước', 'Mỗi dòng một kho.', (cd.kho_bep || []).join('\n'), 'vung') +
    o('mdkLy', 'Câu lý do chung theo nhóm', 'Mỗi dòng: Nhóm | câu tiếng Việt | câu tiếng Anh.', (cd.ly_do_nhom || []).map(function (x) { return x.join(' | '); }).join('\n'), 'vung') + '</div>';
  var b = frame(tieuDe, html, { footer: '<button class="btn" id="mdkLuuCd" style="margin:0">Lưu cài đặt</button>' });
  mdkNghePhan(b);
  b.onclick = function (e) { var n = e.target.closest('[data-mdkbat]'); if (n) { var k = n.getAttribute('data-mdkbat'); cd[k] = !cd[k]; crmDatCongTac(n, cd[k]); } };
  var nut = document.getElementById('mdkLuuCd');
  if (nut) nut.onclick = async function () {
    var v = function (id) { return document.getElementById(id).value; };
    nut.disabled = true;
    try {
      await api(MDK_P + 'luu_cai_dat', { du_lieu: JSON.stringify({ bat_gio: cd.bat_gio ? 1 : 0, bat_quay: cd.bat_quay ? 1 : 0, bat_dbt: cd.bat_dbt ? 1 : 0, thanh_mien_phi: cd.thanh_mien_phi ? 1 : 0,
        toi_da: v('mdkToiDa'), nguong: v('mdkNguong'), nhom: v('mdkNhomGy'), kho_bep: v('mdkKho'), ly_do_nhom: v('mdkLy') }) });
      toast('Đã lưu cài đặt gợi ý'); scrMonDiKem();
    } catch (e) { nut.disabled = false; toast(errMsg(e)); }
  };
}

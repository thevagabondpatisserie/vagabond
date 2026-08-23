/* ---------- 31. So nhan banh dau ngay cua cua hang ----------

Anh Viet 23/08/2026: cua hang D1 moi ngay phai tu go mot bang Excel roi chup
gui vao nhom Zalo. Man nay thay dung cai bang do: ton dau, cac dot nhan trong
ngay, va tong dang co.

So nay KHONG dung ton kho ERPNext va khong sinh but toan nao. Ly do day du
nam trong vagabond/nhan_banh.py, tom tat: 20 tren 46 mon banh nuong chua co
gia von nen phieu kho bi chan, va tai khoan doi ung cua nhap kho khong nguon
la 632 Gia von hang ban, nen nhap moi ngay se lam lai gop phinh ao. Khi BOM
xong va ke toan bat tru kho luc ban thi so nay sinh duoc phieu kho that.
*/
var nb = { ngay: '', diem: '', bang: null, chon: {} };

function nbHomNay() { return today(); }

function nbO(x) {
  /* Mot dong mon: ten, o ton dau, cac dot, va tong dang co. */
  var dot = '';
  for (var i = 1; i <= (nb.bang.so_dot || 0); i++) {
    var s = (x.cac_dot || {})[String(i)];
    dot += '<span class="nbd" data-dot="' + i + '" data-ma="' + h(x.ma_hang) + '">' +
      '<i>Đợt ' + i + '</i><b>' + (s > 0 ? s : '·') + '</b></span>';
  }
  var goi = (!x.ton_dau && x.goi_y_ton > 0)
    ? '<span class="nbg" data-goi="' + h(x.ma_hang) + '" data-so="' + x.goi_y_ton + '">hôm qua ' + x.goi_y_ton + '</span>' : '';
  return '<div class="nbr">' +
    (x.hinh ? '<img src="' + h(x.hinh) + '" loading="lazy">' : '<span class="nbi">🥐</span>') +
    '<div class="nbt"><div class="n1">' + h(x.ten_banh) + '</div>' +
    '<div class="n2">' + h(x.ma_hang) + '</div>' +
    '<div class="nbl">' +
    '<span class="nbd t" data-ton="' + h(x.ma_hang) + '"><i>Tồn đầu</i><b>' + (x.ton_dau > 0 ? x.ton_dau : '·') + '</b></span>' +
    dot + goi + '</div></div>' +
    '<div class="nbc"><b>' + (x.tong_co || 0) + '</b><i>đang có</i>' +
    '<span class="nbx" data-xoa="' + h(x.ma_hang) + '">✕</span></div></div>';
}

async function nbTai() {
  busy(1);
  try { nb.bang = await api('vagabond.nhan_banh.bang', { ngay: nb.ngay, diem: nb.diem }); }
  catch (e) { busy(0); return toast(errMsg(e), 4600); }
  busy(0);
  nbVe();
}

function nbVe() {
  var b = nb.bang || { dong: [], so_dot: 0 };
  var chot = b.tinh_trang === 'Da chot';
  var tongCo = 0, tongNhan = 0;
  (b.dong || []).forEach(function (x) { tongCo += (x.tong_co || 0); tongNhan += (x.tong_nhan || 0); });

  var head = '<div class="card" style="padding:12px 14px">' +
    '<div class="fld" data-a="ngay" style="padding-left:0"><div class="fi">📅</div>' +
    '<div class="ft"><div class="fl">Ngày</div><div class="fv">' + h(dmy(b.ngay)) + '</div></div>' +
    '<div class="fc">&#8250;</div></div>' +
    '<div class="fld" data-a="diem" style="padding-left:0"><div class="fi">🏬</div>' +
    '<div class="ft"><div class="fl">Điểm nhận</div><div class="fv">' + h(shortWh(b.diem)) + '</div></div>' +
    '<div class="fc">&#8250;</div></div></div>';

  var tom = '<div class="nbs"><div><b>' + (b.dong || []).length + '</b><i>món</i></div>' +
    '<div><b>' + tongNhan + '</b><i>nhận trong ngày</i></div>' +
    '<div><b>' + tongCo + '</b><i>đang có</i></div></div>';

  var than = (b.dong || []).length
    ? '<div class="nbb">' + b.dong.map(nbO).join('') + '</div>'
    : '<div class="emp"><div class="e1">🥐</div><div class="e2">Chưa ghi món nào cho ngày này</div>' +
      '<div class="e3">Bấm "Nhận đợt mới" để ghi số bếp vừa giao</div></div>';

  var mach = chot
    ? '<div class="nbw">Sổ ngày này đã chốt. Cần sửa thì bấm Mở lại sổ.</div>'
    : '<div class="nbw ok">Bấm vào ô <b>Tồn đầu</b> hoặc ô <b>Đợt</b> để sửa số. Đếm xong cả ngày thì bấm Chốt sổ.</div>';

  var nut = chot
    ? '<button class="btn gh" id="nbMo">Mở lại sổ</button>'
    : '<button class="btn" id="nbThem">Nhận đợt mới</button>' +
      '<button class="btn gh" id="nbChot" style="margin-top:9px">Chốt sổ ngày này</button>';

  var b2 = frame('Nhận bánh', head + tom + mach + than, { footer: nut });

  b2.onclick = function (e) {
    var a = e.target.closest('[data-a]');
    if (a) {
      if (a.dataset.a === 'ngay') {
        var o = [];
        for (var i = 0; i <= 14; i++) { var iso = addDays(today(), -i); o.push({ value: iso, label: dmy(iso) + (i === 0 ? ' (hôm nay)' : i === 1 ? ' (hôm qua)' : '') }); }
        return sheet('Chọn ngày', o, nb.ngay, function (x) { nb.ngay = x.value; nbTai(); });
      }
      if (a.dataset.a === 'diem') return nbChonDiem();
    }
    if (chot) return;
    var xo = e.target.closest('[data-xoa]');
    if (xo) return nbXoa(xo.dataset.xoa);
    var gy = e.target.closest('[data-goi]');
    if (gy) return nbSuaTon(gy.dataset.goi, gy.dataset.so);
    var tn = e.target.closest('[data-ton]');
    if (tn) return nbSuaTon(tn.dataset.ton, '');
    var dt = e.target.closest('[data-dot]');
    if (dt) return nbSuaDot(dt.dataset.ma, dt.dataset.dot);
  };
  var bt = document.getElementById('nbThem'); if (bt) bt.onclick = nbChonMon;
  var bc = document.getElementById('nbChot'); if (bc) bc.onclick = function () { nbChot(0); };
  var bm = document.getElementById('nbMo'); if (bm) bm.onclick = function () { nbChot(1); };
}

async function nbChonDiem() {
  var kq = null;
  busy(1);
  try { kq = await api('vagabond.nhan_banh.diem_nhan', {}); } catch (e) { busy(0); return toast(errMsg(e)); }
  busy(0);
  sheet('Điểm nhận', (kq.ds || []).map(function (x) { return { value: x, label: shortWh(x), tim: x }; }),
    nb.diem, function (o) { nb.diem = o.value; nbTai(); }, true);
}

async function nbSuaTon(ma, goi) {
  var v = await promptSheet('Tồn đầu ngày của món này', goi ? String(goi) : 'Nhập số đếm được');
  if (v === null) return;
  var so = parseInt(v, 10);
  if (isNaN(so) || so < 0) return toast('Số không hợp lệ');
  busy(1);
  try { nb.bang = await api('vagabond.nhan_banh.dat_ton_dau', { ngay: nb.ngay, diem: nb.diem, ma_hang: ma, so_luong: so }); }
  catch (e) { busy(0); return toast(errMsg(e), 4600); }
  busy(0); nbVe(); toast('Đã lưu tồn đầu');
}

async function nbSuaDot(ma, dot) {
  var v = await promptSheet('Số nhận ở đợt ' + dot, 'Nhập 0 để xoá đợt này');
  if (v === null) return;
  var so = parseInt(v, 10);
  if (isNaN(so) || so < 0) return toast('Số không hợp lệ');
  busy(1);
  try { nb.bang = await api('vagabond.nhan_banh.sua_so', { ngay: nb.ngay, diem: nb.diem, ma_hang: ma, dot: dot, so_luong: so }); }
  catch (e) { busy(0); return toast(errMsg(e), 4600); }
  busy(0); nbVe(); toast('Đã lưu');
}

async function nbXoa(ma) {
  var ok = await confirmSheet('Gỡ món này khỏi sổ hôm nay?', 'Xoá cả tồn đầu lẫn mọi đợt đã nhận của món. Không lấy lại được.', 'Gỡ món', true);
  if (!ok) return;
  busy(1);
  try { nb.bang = await api('vagabond.nhan_banh.xoa_mon', { ngay: nb.ngay, diem: nb.diem, ma_hang: ma }); }
  catch (e) { busy(0); return toast(errMsg(e), 4600); }
  busy(0); nbVe(); toast('Đã gỡ món');
}

async function nbChot(moLai) {
  if (!moLai) {
    var ok = await confirmSheet('Chốt sổ ngày ' + dmy(nb.ngay) + '?', 'Chốt rồi thì không ai sửa được nữa, để con số gửi đi không đổi sau lưng người đã đọc. Vẫn mở lại được nếu cần.', 'Chốt sổ');
    if (!ok) return;
  }
  busy(1);
  try { nb.bang = await api('vagabond.nhan_banh.chot_ngay', { ngay: nb.ngay, diem: nb.diem, mo_lai: moLai ? 1 : 0 }); }
  catch (e) { busy(0); return toast(errMsg(e), 4600); }
  busy(0); nbVe(); toast(moLai ? 'Đã mở lại sổ' : 'Đã chốt sổ');
}

/* Bang chon mon cho mot dot nhan. Mon hay nhan bay san len dau de khoi phai
   tim tung mon mot: bep giao gan nhu cung mot ro moi sang. */
async function nbChonMon() {
  var hay = [], tim = [];
  busy(1);
  try { hay = (await api('vagabond.nhan_banh.mon_hay_nhan', { diem: nb.diem })).ds || []; } catch (e) { hay = []; }
  busy(0);
  nb.chon = {};
  var q = '', dsTim = [];

  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>Nhận đợt ' + (nb.bang.dot_moi || 1) + '</b><div class="x">&times;</div></div>' +
    '<div style="padding:2px 14px 6px">' + srchBox('nbq', 'Tìm món...', '') + '</div>' +
    '<div style="padding:0 14px 6px;color:#a0a6b4;font-size:12.5px">Gõ số cho món bếp vừa giao. Món bỏ trống thì không ghi vào sổ.</div>' +
    '<div class="shl" id="nbl"></div>' +
    '<div style="padding:12px 14px calc(env(safe-area-inset-bottom,0px) + 14px)">' +
    '<button class="btn" id="nbLuu">Ghi vào sổ</button></div>';
  var lst = box.querySelector('#nbl');

  function ve() {
    var ds = q ? dsTim : hay;
    lst.innerHTML = ds.length ? ds.map(function (x, i) {
      return '<div class="shi" style="align-items:center">' +
        (x.hinh ? '<img src="' + h(x.hinh) + '" style="width:38px;height:38px;object-fit:cover;border-radius:9px;flex:none;border:1px solid #e5e7eb" loading="lazy">' : '<span>🥐</span>') +
        '<span style="flex:1;min-width:0">' + h(x.ten_banh || x.item_name || x.name) +
        '<div style="color:#a0a6b4;font-size:12px;margin-top:2px">' + h(x.ma_hang || x.name) + '</div></span>' +
        '<input class="nt" type="number" min="0" inputmode="numeric" data-nbq="' + h(x.ma_hang || x.name) + '" value="' + (nb.chon[x.ma_hang || x.name] || '') + '" style="height:44px;width:74px;flex:none;text-align:center;padding:0 6px">' +
        '</div>';
    }).join('') : '<div class="emp"><div class="e2">' + (q ? 'Không tìm thấy món' : 'Chưa có món nào hay nhận, gõ tên món để tìm') + '</div></div>';
    var n = 0;
    for (var k in nb.chon) if (nb.chon[k] > 0) n++;
    var bl = document.getElementById('nbLuu');
    if (bl) { bl.disabled = !n; bl.textContent = n ? 'Ghi ' + n + ' món vào sổ' : 'Chưa gõ số cho món nào'; }
  }
  ve();
  ov.appendChild(box); document.body.appendChild(ov);
  function dong() { ov.remove(); }
  ov.onclick = function (e) { if (e.target === ov) dong(); };
  box.querySelector('.x').onclick = dong;

  var oq = box.querySelector('#nbq');
  var hen = null;
  oq.oninput = function () {
    q = (oq.value || '').trim();
    if (hen) clearTimeout(hen);
    hen = setTimeout(async function () {
      if (!q) { dsTim = []; return ve(); }
      try { dsTim = ((await api('vagabond.nhan_banh.tim_mon', { tu_khoa: q, diem: nb.diem })).ds || []).map(function (x) { return { ma_hang: x.name, ten_banh: x.item_name, hinh: x.image }; }); }
      catch (e) { dsTim = []; }
      ve();
    }, 260);
  };
  lst.oninput = function (e) {
    var o = e.target.closest('[data-nbq]'); if (!o) return;
    var v = parseInt(o.value, 10);
    nb.chon[o.dataset.nbq] = (v > 0) ? v : 0;
    var n = 0;
    for (var k in nb.chon) if (nb.chon[k] > 0) n++;
    var bl = document.getElementById('nbLuu');
    if (bl) { bl.disabled = !n; bl.textContent = n ? 'Ghi ' + n + ' món vào sổ' : 'Chưa gõ số cho món nào'; }
  };
  document.getElementById('nbLuu').onclick = async function () {
    var cac = [];
    for (var k in nb.chon) if (nb.chon[k] > 0) cac.push({ ma_hang: k, so_luong: nb.chon[k] });
    if (!cac.length) return toast('Chưa gõ số cho món nào');
    busy(1);
    try { nb.bang = await api('vagabond.nhan_banh.ghi_nhan', { ngay: nb.ngay, diem: nb.diem, cac_dong: JSON.stringify(cac) }); }
    catch (e) { busy(0); return toast(errMsg(e), 4600); }
    busy(0); dong(); nbVe(); toast('Đã ghi ' + cac.length + ' món vào sổ');
  };
}

async function scrNhanBanh() {
  vgbCss();
  if (!nb.ngay) nb.ngay = nbHomNay();
  if (!nb.diem) nb.diem = 'Kho D1 - TV';
  frame('Nhận bánh', '<div class="emp"><div class="e1">⏳</div></div>');
  await nbTai();
}

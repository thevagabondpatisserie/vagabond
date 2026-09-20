
/* ---------- 37. Ton kho theo chang (28/08/2026) ----------

   Anh Viet: "em dung luon man theo doi ton kho theo chang nha".

   Man Tra ton kho da co (phan 12) tra loi cau "kho nay dang co gi". Man
   nay tra loi cau khac: "hang cua bep dang dung o chang nao". Hai cau do
   khong thay the nhau duoc, nen dat hai man rieng chu khong nhet them mot
   chip vao man cu.

   Nam nhan chang cu gom con hai ten cho phan ban thanh pham:
     BTP thanh phan + Ruot banh (C1)  ->  BTP so cap
     Banh khuon (C2)                  ->  BTP san sang
   Nguyen lieu va Thanh pham giu nguyen vi khong phai ban thanh pham.

   Viec gom lam o may chu, trong vagabond/ton_chang.py. Man hinh KHONG tu
   dich nhan: de mot bang dich o day nua la sang mai hai ban lech nhau, ma
   luc lech thi khong ai biet ben nao dung. */

var tch = { bep: '', chang: '', tim: '', d: null };

var TCH_BEP = [['', '🏠 Cả hai bếp'], ['pastry', '🎂 Pastry'], ['baker', '🥐 Baker']];

/* Thu tu chip do MAY CHU tra ve trong d.thu_tu, khong go tay o day. Thu tu
   la chieu di len cua day chuyen, ma chieu do doi thi phai doi ca luat kho
   ben Python - hai cho phai noi cung mot cau. */

function tchChip(ma, ten, o) {
  var so = (o && o.so_ma) || 0;
  return '<div class="chip' + (tch.chang === ma ? ' on' : '') + '" data-tcc="' + h(ma) + '">' +
    h(ten) + ' <b>' + so + '</b></div>';
}

async function tchTai() {
  tch.d = await api('vagabond.ton_chang.ton_theo_chang', {
    bep: tch.bep || null, chang: tch.chang || null, tim: tch.tim || null
  });
}

async function scrTonChang() {
  if (!tch.d) {
    frame('Tồn kho theo chặng', '<div class="emp"><div class="e1">⏳</div></div>');
    try { await tchTai(); }
    catch (e) {
      frame('Tồn kho theo chặng', '<div class="emp"><div class="e1">🔒</div><div>' + h(errMsg(e)) + '</div></div>');
      return;
    }
  }

  function draw() {
    var d = tch.d;
    var beps = TCH_BEP.map(function (c) {
      return '<div class="chip' + (tch.bep === c[0] ? ' on' : '') + '" data-tcb="' + c[0] + '">' + c[1] + '</div>';
    }).join('');

    /* Chip "Tat ca" dung dau, roi bon chang, roi nhom chua phan chang neu
       co. Chip chang RONG HANG van hien voi so 0: an no di thi nguoi xem
       tuong minh loc nham chu khong nghi la chang do het hang that. */
    var tong = 0;
    (d.thu_tu || []).forEach(function (m) { tong += ((d.bang || {})[m] || {}).so_ma || 0; });
    var chua = ((d.bang || {})[''] || {}).so_ma || 0;
    var chips = '<div class="chip' + (tch.chang === '' ? ' on' : '') + '" data-tcc="">Tất cả <b>' + (tong + chua) + '</b></div>' +
      (d.thu_tu || []).map(function (m) {
        return tchChip(m, (d.ten_chang || {})[m] || m, (d.bang || {})[m]);
      }).join('') +
      (chua ? tchChip('chua', '❓ Chưa phân chặng', (d.bang || {})['']) : '') +
      /* v512: chip SAI KHO (Khai 18/09/2026) - hang nam o kho khac chang cua no. */
      (d.so_sai_kho ? '<div class="chip' + (tch.chang === 'sai_kho' ? ' on' : '') + '" data-tcc="sai_kho" style="border-color:#fca5a5;color:#b3261e">⚠ Sai kho <b>' + d.so_sai_kho + '</b></div>' : '');

    var body = '<div class="chips">' + beps + '</div>' +
      '<div class="chips">' + chips + '</div>' +
      '<div style="font-size:12.5px;color:#0f766e;background:#ccfbf1;border-radius:8px;padding:7px 11px;margin-bottom:9px;line-height:1.5">📊 ' + h(d.tom_tat || '') + '</div>' +
      '<input class="tin" id="tchTim" placeholder="Tìm theo tên hoặc mã món" value="' + h(tch.tim) + '" ' +
      'style="text-align:left;font-size:14.5px;padding:0 13px;margin-bottom:9px;width:100%">';

    body += (d.ds && d.ds.length) ? '<div class="lst">' + d.ds.map(function (x) {
      /* Mot ma nam o may kho thi cong lai, va ghi ro tung kho o dong duoi.
         Bep hay hoi "hang do cua ai" chu khong chi hoi "con bao nhieu". */
      var kho = (x.kho || []).map(function (w) {
        return (w.sai ? '<b style="color:#b3261e">' + h(shortWh(w.kho)) + ' ' + num(w.sl) + ' (sai kho)</b>' : h(shortWh(w.kho)) + ' ' + num(w.sl));
      }).join(' · ');
      return '<div class="li"><div class="lt"><div class="l1">' + h(x.ten) + '</div>' +
        '<div class="l2">' + h(x.ma) + (kho ? ' · ' + kho : '') +
        (x.lam_tuoi ? ' · <b style="color:#b3261e">làm tươi</b>' : '') +
        /* v512 y 3: nut lap phieu chuyen NHAP ve dung kho, chi quan ly san xuat. */
        (x.sai_kho && d.lap_duoc && x.kho_dung ? '<div style="margin-top:5px"><span data-tcvk="' + h(x.ma) + '" style="display:inline-block;background:#fff;color:#b3261e;border:1.5px solid #fca5a5;border-radius:999px;padding:4px 12px;font-size:12.5px;font-weight:700;cursor:pointer">📦 Chuyển về ' + h(shortWh(x.kho_dung)) + '</span></div>' : '') +
        '</div></div>' +
        '<div style="text-align:right"><div class="amt">' + num(x.sl) + '</div>' +
        '<div class="l2">' + h(x.dvt || '') + '</div>' +
        '<div class="st ' + h(x.mau || 'n') + '" style="margin-top:4px">' + h(x.chip || '') + '</div></div></div>';
    }).join('') + '</div>' +
      (d.tong_dong > d.ds.length ? '<div style="text-align:center;font-size:12px;color:#98a2b3;padding:10px">Đang hiện ' + d.ds.length + ' trên ' + d.tong_dong + ', gõ ô tìm để thu hẹp</div>' : '')
      : '<div class="emp"><div class="e1">📦</div><div class="e2">Không có mã nào còn tồn ở bộ lọc này</div></div>';

    var b = frame('Tồn kho theo chặng', body);
    b.onclick = function (e) {
      var t = e.target.closest('[data-tcb]');
      if (t) { tch.bep = t.dataset.tcb; tch.d = null; return scrTonChang(); }
      var c = e.target.closest('[data-tcc]');
      if (c) { tch.chang = c.dataset.tcc; tch.d = null; return scrTonChang(); }
      var v = e.target.closest('[data-tcvk]');
      if (v) return tchChuyenVeDungKho(v.dataset.tcvk);
    };

    var ti = document.getElementById('tchTim');
    if (ti) {
      var cho = null;
      ti.oninput = function () {
        tch.tim = ti.value;
        if (cho) clearTimeout(cho);
        cho = setTimeout(async function () {
          try { await tchTai(); } catch (e) { }
          var giu = document.activeElement === ti;
          var vt = ti.selectionStart;
          draw();
          if (giu) {
            var ti2 = document.getElementById('tchTim');
            if (ti2) { ti2.focus(); try { ti2.setSelectionRange(vt, vt); } catch (e) { } }
          }
        }, 420);
      };
    }
  }
  draw();
}

/* v512 y 3 (anh Viet duyet 19/09/2026): lap phieu chuyen kho NHAP dua hang
   sai kho ve dung kho theo chang. Chi lap nhap, Khai xem tren Desk roi ghi
   so. Moi kho sai mot phieu, hoi xac nhan tung cai. */
async function tchChuyenVeDungKho(ma) {
  var d = tch.d || {};
  var x = (d.ds || []).find(function (r) { return r.ma === ma; });
  if (!x) return;
  var sai = (x.kho || []).filter(function (k) { return k.sai && k.sl > 0; });
  for (var i = 0; i < sai.length; i++) {
    var k = sai[i];
    /* Kho dich cua TUNG kho sai (k.kho_dung), khong lay cua dong: cung mot ma
       nam sai o hai bep thi hai kho dich khac nhau (Codex #349). */
    var den = k.kho_dung || x.kho_dung;
    if (!den) continue;
    var ok = await confirmSheet('Chuyển về đúng kho', 'Lập phiếu chuyển kho NHÁP: ' + num(k.sl) + ' ' + (x.dvt || '') + ' ' + x.ten + ' từ ' + shortWh(k.kho) + ' sang ' + shortWh(den) + '. Chuyển hết số đang nằm sai; phiếu chưa ghi sổ, quản lý xem lại trên máy tính rồi mới ghi.', 'Lập phiếu nháp', false);
    if (!ok) continue;
    busy(true);
    try {
      var kq = await api('vagabond.ton_chang.tao_phieu_ve_dung_kho', { ma: ma, kho_sai: k.kho, sl: k.sl });
      busy(false);
      toast((kq && kq.da_co ? 'Đã có phiếu nháp ' : 'Đã lập phiếu nháp ') + (kq && kq.name) + ', chờ ghi sổ trên máy tính.', 4500);
    } catch (e) { busy(false); baoTin((e && e.message) || 'Không lập được phiếu'); }
  }
}


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
      (chua ? tchChip('chua', '❓ Chưa phân chặng', (d.bang || {})['']) : '');

    var body = '<div class="chips">' + beps + '</div>' +
      '<div class="chips">' + chips + '</div>' +
      '<div style="font-size:12.5px;color:#0f766e;background:#ccfbf1;border-radius:8px;padding:7px 11px;margin-bottom:9px;line-height:1.5">📊 ' + h(d.tom_tat || '') + '</div>' +
      '<input class="tin" id="tchTim" placeholder="Tìm theo tên hoặc mã món" value="' + h(tch.tim) + '" ' +
      'style="text-align:left;font-size:14.5px;padding:0 13px;margin-bottom:9px;width:100%">';

    body += (d.ds && d.ds.length) ? '<div class="lst">' + d.ds.map(function (x) {
      /* Mot ma nam o may kho thi cong lai, va ghi ro tung kho o dong duoi.
         Bep hay hoi "hang do cua ai" chu khong chi hoi "con bao nhieu". */
      var kho = (x.kho || []).map(function (w) {
        return shortWh(w.kho) + ' ' + num(w.sl);
      }).join(' · ');
      return '<div class="li"><div class="lt"><div class="l1">' + h(x.ten) + '</div>' +
        '<div class="l2">' + h(x.ma) + (kho ? ' · ' + h(kho) : '') +
        (x.lam_tuoi ? ' · <b style="color:#b3261e">làm tươi</b>' : '') + '</div></div>' +
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

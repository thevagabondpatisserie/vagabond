/* Giữ nguyên khóa và nội dung khi mất phản hồi, tránh gửi hai yêu cầu đặt bàn. */
(async function () {
  'use strict';
  const tim = id => document.getElementById(id);
  let cauHinh, gio = '', dangGui = false, yeuCau = null;
  const ma = crypto.randomUUID();
  function bao(chu, loi) { tim('trang-thai').textContent = chu; tim('trang-thai').classList.toggle('loi', !!loi); }
  try {
    const r = await fetch('/api/method/vagabond.dat_ban.cau_hinh'); const d = await r.json();
    if (!r.ok || !d.message) throw new Error(); cauHinh = d.message;
    if (!cauHinh.bat) { bao('Tiệm chưa mở nhận đặt bàn online. Gọi 0931 224 334 để được hỗ trợ.'); return; }
    tim('co-so').textContent = cauHinh.ten_co_so; tim('dia-chi').textContent = cauHinh.dia_chi;
    tim('ngay').min = cauHinh.hom_nay; tim('ngay').value = cauHinh.hom_nay;
    tim('so-khach').max = cauHinh.toi_da_khach; tim('so-khach').value = Math.min(2,cauHinh.toi_da_khach);
    cauHinh.khung_gio.forEach(g => { const b = document.createElement('button'); b.type='button'; b.textContent=g; b.setAttribute('aria-pressed','false'); b.onclick=()=>{gio=g;tim('gio').querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));};tim('gio').append(b); });
    tim('dat-ban').hidden = false; bao('Tiệm sẽ liên hệ xác nhận sau khi nhận yêu cầu.');
  } catch (_) { bao('Chưa tải được lịch. Tải lại trang hoặc gọi tiệm để đặt bàn.', true); return; }
  tim('dat-ban').onsubmit = async e => {
    e.preventDefault(); if (dangGui) return;
    if (!gio) { bao('Chọn giờ mong muốn trước khi gửi.',true); return; }
    if (!yeuCau) yeuCau = {co_so:cauHinh.co_so,ngay:tim('ngay').value,gio,so_khach:Number(tim('so-khach').value),ten:tim('ten').value,sdt:tim('sdt').value,ghi_chu:tim('ghi-chu').value};
    dangGui=true; tim('gui').disabled=true;
    tim('dat-ban').querySelectorAll('input,textarea,#gio button').forEach(x=>x.disabled=true);
    bao('Đang gửi yêu cầu...');
    try {
      const r = await fetch('/api/method/vagabond.dat_ban.gui',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-Frappe-CSRF-Token':document.querySelector('meta[name=csrf-token]').content},body:JSON.stringify({du_lieu:yeuCau,ma_lan_gui:ma})});
      const d=await r.json();
      if (!r.ok || !d.message?.ok) {
        if (r.status>=400 && r.status<500 && r.status!==408) {
          yeuCau=null; tim('dat-ban').querySelectorAll('input,textarea,#gio button').forEach(x=>x.disabled=false);
          let chu='Kiểm tra thông tin hoặc chờ vài phút rồi gửi lại.';
          try { chu=JSON.parse(d._server_messages||'[]').map(x=>JSON.parse(x).message).join(' ')||chu; } catch (_) {}
          throw new Error(chu);
        }
        throw new Error('Chưa nhận được kết quả. Bấm Gửi lại cùng yêu cầu để kiểm tra, không cần nhập lại.');
      }
      tim('dat-ban').hidden=true;bao('Đã tiếp nhận yêu cầu '+d.message.ma+'. Tiệm sẽ gọi xác nhận. Bàn chưa được giữ cho tới khi tiệm xác nhận.');
    } catch(e) { bao(e.message==='Failed to fetch'?'Mất kết nối. Bấm Gửi lại cùng yêu cầu để kiểm tra.':e.message,true);tim('gui').textContent=yeuCau?'Gửi lại cùng yêu cầu':'Gửi yêu cầu đặt bàn'; }
    finally { dangGui=false;tim('gui').disabled=false; }
  };
})();

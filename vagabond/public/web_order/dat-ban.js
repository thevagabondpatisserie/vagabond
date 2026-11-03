/* Giữ nguyên khóa và nội dung khi mất phản hồi, tránh gửi hai yêu cầu đặt bàn.
   v630 (anh Việt duyệt mẫu 3, 02/11/2026): đi theo thứ tự khách nghĩ: ngày nào,
   mấy người, mấy giờ, ngồi đâu, rồi mới tới tên và số điện thoại. Ngày là dải
   tới 14 ngày thay ô lịch; giờ chia Sáng, Trưa, Chiều, Tối, giờ hôm nay đã qua
   hạn đặt thì mờ theo đúng luật máy chủ (khung_gio_hom_nay); số khách là nút
   trừ cộng, chặn ở mức tối đa. Trẻ em, bánh đặt sẵn, email gấp vào nút "+",
   mở ra mới hỏi, vẫn gửi đúng các ô cũ máy chủ cần. */
(async function () {
  'use strict';
  if (window.vgbChuSanSang) await window.vgbChuSanSang;
  const tim = id => document.getElementById(id);
  let cauHinh, dip = '', khuVuc = '', gio = '', ngay = '', soKhach = 2, treEm = 0, dangGui = false, yeuCau = null;
  const mo = {};
  const ma = crypto.randomUUID();
  const nutGui = tim('gui').textContent;
  function bao(chu, loi) { const o = tim('trang-thai'); o.textContent = chu; o.classList.toggle('loi', !!loi);
    // v598: lỗi hiện ở đầu trang, khách đang ở nút Gửi cuối trang không thấy. Cuộn tới dòng báo.
    if (loi && o.scrollIntoView) o.scrollIntoView({block: 'center', behavior: 'smooth'}); }
  function tao(the, lop, chu) { const e = document.createElement(the); if (lop) e.className = lop; if (chu) e.textContent = chu; return e; }
  const hai = n => ('0' + n).slice(-2);
  const thu = (s, goc) => { const a = String(s || '').split(',').map(x => x.trim()); return a.length === 7 && a.every(Boolean) ? a : goc.split(','); };
  const THU_NGAN = thu(chuWeb("db630_thu_ngan", "CN,T2,T3,T4,T5,T6,T7"), 'CN,T2,T3,T4,T5,T6,T7');
  const THU_DAI = thu(chuWeb("db630_thu_dai", "Chủ nhật,Thứ Hai,Thứ Ba,Thứ Tư,Thứ Năm,Thứ Sáu,Thứ Bảy"), 'Chủ nhật,Thứ Hai,Thứ Ba,Thứ Tư,Thứ Năm,Thứ Sáu,Thứ Bảy');
  /* Ngày tính theo hom_nay của máy chủ, giờ UTC để không lệch múi giờ máy khách. */
  function ngayTu(iso) { const p = String(iso).split('-').map(Number); return new Date(Date.UTC(p[0], p[1] - 1, p[2])); }
  function isoCua(t) { return t.getUTCFullYear() + '-' + hai(t.getUTCMonth() + 1) + '-' + hai(t.getUTCDate()); }
  function tenNgay(iso, dai) {
    const t = ngayTu(iso), dm = hai(t.getUTCDate()) + '/' + hai(t.getUTCMonth() + 1);
    return (iso === cauHinh.hom_nay ? chuWeb("db630_hom_nay", "Hôm nay") : (dai ? THU_DAI : THU_NGAN)[t.getUTCDay()]) + ' ' + dm;
  }
  const toiDa = () => Math.max(1, Number(cauHinh.toi_da_khach) || 8);
  /* Khung giờ hôm nay còn nhận. Máy chủ cũ chưa gửi danh sách thì không làm mờ gì (máy chủ vẫn chặn lúc gửi). */
  const conHomNay = () => Array.isArray(cauHinh.khung_gio_hom_nay) ? cauHinh.khung_gio_hom_nay : cauHinh.khung_gio;
  const hetGio = (d, g) => d === cauHinh.hom_nay && conHomNay().indexOf(g) < 0;
  const tenKhu = k => String(k).split(' - ')[0];

  /* Mọi nút chọn mang data-chon. Đang gửi hoặc đang giữ yêu cầu chờ gửi lại thì khoá hết;
     nút đánh data-het (giờ đã qua, ngày hết giờ, nút trừ cộng ở mức chặn) luôn tắt. */
  function apKhoa() {
    const khoa = dangGui || !!yeuCau;
    tim('dat-ban').querySelectorAll('input,textarea,[data-chon]').forEach(x => { x.disabled = khoa || x.getAttribute('data-het') === '1'; });
  }
  function het(b, co) { if (co) b.setAttribute('data-het', '1'); else b.removeAttribute('data-het'); }
  function nhan(b, co) { b.setAttribute('aria-pressed', String(!!co)); }

  function veNgay() {
    const g = tim('ngay-dai'); g.replaceChildren();
    const so = Math.min(14, (Number(cauHinh.toi_da_ngay) || 30) + 1), dau = ngayTu(cauHinh.hom_nay);
    for (let i = 0; i < so; i++) {
      const t = new Date(dau.getTime() + i * 864e5), iso = isoCua(t);
      const b = tao('button'); b.type = 'button'; b.setAttribute('data-chon', ''); b.setAttribute('data-ngay', iso);
      b.append(tao('small', '', i ? THU_NGAN[t.getUTCDay()] : chuWeb("db630_hom_nay", "Hôm nay")), tao('b', '', hai(t.getUTCDate())), tao('span', '', i && t.getUTCDate() !== 1 ? '' : chuWeb("db630_thang", "Th{so}", {so: t.getUTCMonth() + 1})));
      b.setAttribute('aria-label', tenNgay(iso, true));
      const khongCon = !cauHinh.khung_gio.some(x => !hetGio(iso, x));
      het(b, khongCon);
      if (khongCon) b.title = chuWeb("db630_het_gio", "Đã hết giờ nhận đặt bàn");
      b.onclick = () => { ngay = iso; capNhat(); };
      g.append(b);
    }
  }
  const BUOI = () => [[0, chuWeb("db630_sang", "Sáng")], [660, chuWeb("db630_trua", "Trưa")], [840, chuWeb("db630_chieu", "Chiều")], [1020, chuWeb("db630_toi", "Tối")]];
  function veGio() {
    const g = tim('gio'); g.replaceChildren();
    const nhom = BUOI().map(x => ({ten: x[1], tu: x[0], ds: []}));
    cauHinh.khung_gio.forEach(k => {
      const p = String(k).split(':'), phut = Number(p[0]) * 60 + Number(p[1] || 0);
      let n = nhom[0]; nhom.forEach(x => { if (phut >= x.tu) n = x; }); n.ds.push(k);
    });
    nhom.filter(n => n.ds.length).forEach(n => {
      const hang = tao('div', 'db-gio-nhom'), ds = tao('div', 'db-gio-ds');
      hang.append(tao('span', 'db-gio-ten', n.ten), ds);
      n.ds.forEach(k => {
        const b = tao('button', '', k); b.type = 'button'; b.setAttribute('data-chon', ''); b.setAttribute('data-gio', k);
        het(b, hetGio(ngay, k));
        if (hetGio(ngay, k)) b.title = chuWeb("db630_het_gio", "Đã hết giờ nhận đặt bàn");
        nhan(b, k === gio);
        b.onclick = () => { gio = k; capNhat(); };
        ds.append(b);
      });
      g.append(hang);
    });
  }
  function datKhach(n) {
    n = Math.round(Number(n));
    if (isFinite(n)) soKhach = Math.max(1, Math.min(toiDa(), n));
    tim('so-khach').value = String(soKhach);
    if (treEm > soKhach) datTre(soKhach);
  }
  function datTre(n) {
    n = Math.round(Number(n));
    if (isFinite(n)) treEm = Math.max(0, Math.min(soKhach, n));
    tim('tre-em').value = String(treEm);
  }
  function capNhat() {
    if (gio && hetGio(ngay, gio)) gio = '';
    tim('ngay-dai').querySelectorAll('[data-ngay]').forEach(b => nhan(b, b.getAttribute('data-ngay') === ngay));
    veGio();
    het(tim('khach-bot'), soKhach <= 1); het(tim('khach-them'), soKhach >= toiDa());
    het(tim('tre-bot'), treEm <= 0); het(tim('tre-them'), treEm >= soKhach);
    tim('so-khach').max = String(toiDa()); tim('tre-em').max = String(soKhach);
    const goi = tim('khach-goi');
    goi.textContent = chuWeb("db630_goi_tiec", "Trên {so} khách, gọi 0931 224 334 để đặt tiệc riêng.", {so: toiDa()});
    goi.classList.toggle('db-cham-tran', soKhach >= toiDa());
    tim('khu-vuc').querySelectorAll('[data-khu]').forEach(b => nhan(b, b.getAttribute('data-khu') === khuVuc));
    tim('dip').querySelectorAll('[data-dip]').forEach(b => nhan(b, b.getAttribute('data-dip') === dip));
    const khach = chuWeb("db630_khach", "{so} khách", {so: soKhach});
    const gioChu = gio || chuWeb("db630_chua_gio", "Chưa chọn giờ");
    tim('tom-tat').textContent = [tenNgay(ngay, true), gioChu, khach, khuVuc && tenKhu(khuVuc)].filter(Boolean).join(' · ');
    tim('tom-ngan-1').textContent = tenNgay(ngay, false) + ' · ' + gioChu;
    tim('tom-ngan-2').textContent = [khach, khuVuc && tenKhu(khuVuc)].filter(Boolean).join(' · ');
    apKhoa();
  }
  function veCuaHang() {
    tim('co-so').textContent = cauHinh.ten_co_so || '';
    tim('dia-chi').textContent = cauHinh.dia_chi || '';
    if (/^\/(?:assets|files)\/[A-Za-z0-9/._-]+$/.test(cauHinh.anh || '')) tim('db-anh').style.backgroundImage = 'url("' + cauHinh.anh + '")';
    if (typeof cauHinh.dang_mo === 'boolean') {
      tim('db-mo-chu').textContent = cauHinh.dang_mo ? chuWeb("db630_dang_mo", "Đang mở cửa") : chuWeb("db630_da_dong", "Đã đóng cửa");
      tim('db-mo-gio').textContent = cauHinh.gio_hom_nay ? ' · ' + chuWeb("db630_gio_hom_nay", "Hôm nay {gio}", {gio: cauHinh.gio_hom_nay}) : '';
      tim('db-mo').classList.toggle('db-dong', !cauHinh.dang_mo);
      tim('db-mo').hidden = false;
    }
    const lien = tim('db-lien'), https = u => /^https:\/\/[^\s/@\\]+(\/|$)/.test(u || '') && !/\s/.test(u);
    const a = (chu, href, ngoai) => { const e = tao('a', '', chu); e.href = href; if (ngoai) { e.target = '_blank'; e.rel = 'noopener'; } lien.append(e); };
    if (https(cauHinh.chi_duong)) a(chuWeb("db630_chi_duong", "Chỉ đường"), cauHinh.chi_duong, 1);
    const so = String(cauHinh.hotline_so || '').replace(/[^0-9+]/g, '');
    if (so && cauHinh.hotline) a(chuWeb("db630_goi", "Gọi {so}", {so: cauHinh.hotline}), 'tel:' + so);
    if (https(cauHinh.zalo)) a(chuWeb("db630_zalo", "Nhắn Zalo"), cauHinh.zalo, 1);
    lien.hidden = !lien.children.length;
  }
  try {
    const r = await fetch('/api/method/vagabond.dat_ban.cau_hinh'); const d = await r.json();
    if (!r.ok || !d.message) throw new Error(); cauHinh = d.message;
    cauHinh.khung_gio = Array.isArray(cauHinh.khung_gio) ? cauHinh.khung_gio : [];
    veCuaHang();
    /* v532: câu đóng do marketing soạn, máy chủ đặt sẵn vào data-dong. */
    if (!cauHinh.bat || !cauHinh.khung_gio.length) { bao(tim('trang-thai').dataset.dong || (chuWeb("dat_ban_b8bab06ff", "Chúng tôi chưa mở nhận đặt bàn online. Gọi 0931 224 334 để được hỗ trợ."))); return; }
    veNgay();
    const dau = [...tim('ngay-dai').querySelectorAll('[data-ngay]')].find(b => b.getAttribute('data-het') !== '1');
    ngay = dau ? dau.getAttribute('data-ngay') : cauHinh.hom_nay;
    (cauHinh.khu_vuc || []).forEach(k => {
      const b = tao('button'); b.type = 'button'; b.setAttribute('data-chon', ''); b.setAttribute('data-khu', k);
      const i = k.indexOf(' - ');
      b.append(tao('b', '', i > 0 ? k.slice(0, i) : k));
      if (i > 0) b.append(tao('span', '', k.slice(i + 3)));
      b.onclick = () => { khuVuc = khuVuc === k ? '' : k; capNhat(); };
      tim('khu-vuc').append(b);
    });
    if (!(cauHinh.khu_vuc || []).length) tim('khu-vuc').append(tao('p', 'db-phu', chuWeb("dat_ban_48f698c3f", "Chúng tôi sẽ tư vấn chỗ ngồi khi xác nhận.")));
    /* "Không có dịp riêng" là không chọn chip nào; máy chủ nhận dịp rỗng như nhau. */
    (cauHinh.dip || []).filter(x => x !== 'Không có dịp riêng').forEach(k => {
      const b = tao('button', '', k); b.type = 'button'; b.setAttribute('data-chon', ''); b.setAttribute('data-dip', k);
      b.onclick = () => { dip = dip === k ? '' : k; capNhat(); };
      tim('dip').append(b);
    });
    tim('khach-bot').onclick = () => { datKhach(soKhach - 1); capNhat(); };
    tim('khach-them').onclick = () => { datKhach(soKhach + 1); capNhat(); };
    tim('so-khach').onchange = () => { datKhach(tim('so-khach').value); capNhat(); };
    tim('tre-bot').onclick = () => { datTre(treEm - 1); capNhat(); };
    tim('tre-them').onclick = () => { datTre(treEm + 1); capNhat(); };
    tim('tre-em').onchange = () => { datTre(tim('tre-em').value); capNhat(); };
    tim('dat-ban').querySelectorAll('[data-mo]').forEach(b => {
      b.onclick = () => {
        const id = b.getAttribute('data-mo'); mo[id] = !mo[id];
        tim(id).hidden = !mo[id]; b.setAttribute('aria-expanded', String(mo[id]));
        if (id === 'o-tre-em' && mo[id] && !treEm) datTre(1);
        capNhat();
      };
    });
    datKhach(Math.min(2, toiDa())); datTre(0);
    capNhat();
    tim('dat-ban').hidden = false; bao((chuWeb("dat_ban_f33d5c7c4", "Chúng tôi sẽ liên hệ xác nhận sau khi nhận yêu cầu.")));
  } catch (_) { bao((chuWeb("dat_ban_13864d971", "Chưa tải được lịch. Tải lại trang hoặc gọi cho chúng tôi để đặt bàn.")), true); return; }
  tim('dat-ban').onsubmit = async e => {
    e.preventDefault(); if (dangGui) return;
    if (!yeuCau) {
      datKhach(tim('so-khach').value); if (mo['o-tre-em']) datTre(tim('tre-em').value); capNhat();
      if (!gio) { bao((chuWeb("dat_ban_77af89de2", "Chọn giờ mong muốn trước khi gửi.")),true); return; }
      /* Ô gấp chưa mở thì gửi như để trống, đúng các khoá máy chủ đã nhận từ trước. */
      yeuCau = {co_so:cauHinh.co_so,ngay,gio,so_khach:soKhach,ten:tim('ten').value,sdt:tim('sdt').value,ghi_chu:tim('ghi-chu').value,dip,khu_vuc:khuVuc,
        tre_em:mo['o-tre-em']?String(treEm):'0',email:mo['o-email']?tim('email').value:'',banh_kem_theo:mo['o-banh']?tim('banh-kem-theo').value:''};
    }
    dangGui=true; apKhoa(); tim('gui').disabled=true;
    bao((chuWeb("dat_ban_115591cea", "Đang gửi yêu cầu...")));
    try {
      const r = await fetch('/api/method/vagabond.dat_ban.gui',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-Frappe-CSRF-Token':document.querySelector('meta[name=csrf-token]').content},body:JSON.stringify({du_lieu:yeuCau,ma_lan_gui:ma})});
      const d=await r.json();
      if (!r.ok || !d.message?.ok) {
        if (r.status>=400 && r.status<500 && r.status!==408) {
          yeuCau=null;
          let chu=(chuWeb("dat_ban_bd4e008af", "Kiểm tra thông tin hoặc chờ vài phút rồi gửi lại."));
          try { chu=JSON.parse(d._server_messages||'[]').map(x=>JSON.parse(x).message).join(' ')||chu; } catch (_) {}
          throw new Error(chu);
        }
        throw new Error((chuWeb("dat_ban_71fbea24c", "Chưa nhận được kết quả. Bấm Gửi lại cùng yêu cầu để kiểm tra, không cần nhập lại.")));
      }
      tim('dat-ban').hidden=true;bao((chuWeb("dat_ban_27a5e32c3", "Đã tiếp nhận yêu cầu") + " ")+d.message.ma+(chuWeb("dat_ban_89b8870d9", ". Chúng tôi sẽ gọi xác nhận. Bàn chưa được giữ cho tới khi chúng tôi xác nhận.")));
    } catch(e) { bao(e.message==='Failed to fetch'?(chuWeb("dat_ban_60ae7eb78", "Mất kết nối. Bấm Gửi lại cùng yêu cầu để kiểm tra.")):e.message,true);tim('gui').textContent=yeuCau?(chuWeb("dat_ban_5ed44ed1c", "Gửi lại cùng yêu cầu")):nutGui; }
    finally { dangGui=false;apKhoa();tim('gui').disabled=false; }
  };
})();

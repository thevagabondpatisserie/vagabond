/* Không giữ token trong localStorage; API chỉ đọc hồ sơ qua cookie HttpOnly.
   v621 (anh Việt 30/10/2026): trang thành viên mới theo bản phác đã duyệt
   (ảnh đại diện, số điểm lớn, thẻ hạng, tiến độ lên hạng, ví quà, mã thành
   viên, hồ sơ) và luồng quà chào mừng tại quầy (?qua=<quầy>): số có Zalo, mã
   Zalo, hồ sơ ngắn, mã quà cho thu ngân. ?bang=<quầy> là bảng in để ở quầy. */
(async function () {
  'use strict';
  if (window.vgbChuSanSang) await window.vgbChuSanSang;
  const tim = id => document.getElementById(id);
  const C = (k, md, thay) => chuWeb(k, md, thay);
  const thamSo = (function () {
    try { return new URLSearchParams((typeof location !== 'undefined' && location.search) || ''); }
    catch (e) { return { get: () => '' }; }
  })();
  const maQuay = ten => String(thamSo.get(ten) || '').replace(/[^A-Za-z0-9_-]/g, '').slice(0, 20).toUpperCase();
  const quayQua = maQuay('qua'), quayBang = maQuay('bang');
  let soDaGui = '', duLieu = null, sanSang = null;
  const lyDo = {get chua_mo(){return chuWeb("thanh_vien_7df724744", "Chúng tôi đang hoàn thiện đăng nhập thành viên. Liên hệ 0931 224 334 để tra điểm.");},get so_dien_thoai_khong_dung(){return chuWeb("thanh_vien_09fcbe5fb", "Kiểm tra lại số điện thoại.");},get gui_qua_nhieu(){return chuWeb("thanh_vien_c3f74f579", "Đã gửi nhiều mã. Chờ 30 phút rồi thử lại.");},get khong_gui_duoc(){return chuWeb("thanh_vien_048bdca06", "Chưa gửi được mã qua Zalo. Chờ một chút hoặc gọi cho chúng tôi.");},get ma_het_han(){return chuWeb("thanh_vien_27c413c51", "Mã đã hết hạn. Gửi mã mới để tiếp tục.");},get ma_khong_dung(){return chuWeb("thanh_vien_77e54d5e8", "Mã chưa đúng. Kiểm tra tin nhắn Zalo.");},get sai_qua_nhieu(){return chuWeb("thanh_vien_aa07e7c30", "Đã nhập sai quá nhiều lần. Gửi mã mới để tiếp tục.");},get can_doi_chieu(){return chuWeb("thanh_vien_dd4609ef6", "Hồ sơ cần được chúng tôi đối chiếu. Gọi 0931 224 334 để được hỗ trợ.");},
    get chua_dang_nhap(){return C('tv6_ly_chua_dn', 'Phiên đăng nhập đã hết. Nhập lại số điện thoại để tiếp tục.');},
    get thieu_ten(){return C('tv6_ly_thieu_ten', 'Quý khách điền tên để chúng tôi gọi đúng.');},
    get ten_khong_dung(){return C('tv6_ly_ten', 'Tên chưa đúng, quý khách kiểm tra lại.');},
    get ngay_sinh_thieu(){return C('tv6_ly_ngay_thieu', 'Chọn đủ ngày và tháng sinh.');},
    get ngay_sinh_khong_dung(){return C('tv6_ly_ngay', 'Ngày sinh chưa đúng, quý khách kiểm tra lại.');},
    get email_khong_dung(){return C('tv6_ly_email', 'Email chưa đúng, quý khách kiểm tra lại hoặc để trống.');},
    get anh_khong_dung(){return C('tv6_ly_anh', 'Chưa đọc được ảnh này, quý khách chọn ảnh khác.');},
    get anh_qua_lon(){return C('tv6_ly_anh_lon', 'Ảnh quá lớn, quý khách chọn ảnh khác.');},
    get qua_chua_mo(){return C('tv6_ly_qua_mo', 'Chương trình quà chào mừng đang tạm dừng. Quý khách vẫn tích điểm như thường.');},
    get nhan_vien(){return C('tv6_ly_nhan_vien', 'Số của nhân viên Vagabond không nhận quà chào mừng.');},
    get ho_so_thieu(){return C('tv6_ly_ho_so', 'Quý khách điền đủ tên, ngày sinh và đồng ý nhận tin Zalo để nhận quà.');},
    get khong_tao_duoc(){return C('tv6_ly_tao', 'Chưa tạo được hồ sơ. Gọi 0931 224 334 để được hỗ trợ.');}};
  function bao(s,loi){const o=tim('trang-thai');o.textContent=s;o.classList.toggle('loi',!!loi);if(loi&&o.scrollIntoView)o.scrollIntoView({block:'center',behavior:'smooth'});}
  async function api(ham,noiDung){const c={credentials:'same-origin',cache:'no-store'};if(noiDung){c.method='POST';c.headers={'Content-Type':'application/json','X-Frappe-CSRF-Token':document.querySelector('meta[name=csrf-token]').content};c.body=JSON.stringify(noiDung);}const r=await fetch('/api/method/vagabond.thanh_vien.'+ham,c);const d=await r.json();if(!r.ok||!d.message)throw new Error((chuWeb("thanh_vien_dd35ada44", "Chưa kết nối được. Thử lại sau ít phút.")));return d.message;}
  function tao(the,chu,lop){const e=document.createElement(the);e.textContent=chu==null?'':chu;if(lop)e.className=lop;return e;}
  function an(el, co) { if (!el) return; if (co) el.setAttribute('hidden', ''); else el.removeAttribute('hidden'); }
  const so = v => Number(v || 0).toLocaleString('vi-VN');
  /* Chữ quà cỡ lớn: "Giảm 20.000đ" hiện thành "20.000đ" (nhãn nhỏ đã nói là quà). */
  const soQua = t => String(t || '').replace(/^Giảm\s+/i, '');
  const MAN = ['dang-nhap', 'qua-ho-so', 'qua-ma', 'ho-so', 'bang-quay'];
  function hien(id) { MAN.forEach(m => an(tim(m), m !== id)); }

  /* Hình bánh có sẵn làm ảnh đại diện: ảnh của web, cắt đúng chỗ, đen trắng. */
  const ANH_MAU = {
    'croissant': ['/assets/vagabond/web_order/anh-bia.png', '20% 30%'],
    'entremet': ['/assets/vagabond/web_order/tay-lam-banh-minh-hoa.jpg', '76% 72%'],
    'lop-banh': ['/assets/vagabond/web_order/anh-bia.png', '55% 62%'],
    'quay': ['/assets/vagabond/images/quay-sales.jpg', '50% 45%'],
  };
  const SO_THICH = [['croissant', C('tv6_st_croissant', 'Croissant và bánh mì')], ['entremet', C('tv6_st_entremet', 'Entremet')],
    ['banh_kem', C('tv6_st_banh_kem', 'Bánh kem sinh nhật')], ['tart', C('tv6_st_tart', 'Tart')], ['do_uong', C('tv6_st_do_uong', 'Đồ uống')]];
  function veAnh(el, d) {
    if (!el) return;
    const anh = String((d && d.anh) || '');
    const mau = ANH_MAU[(d && d.ho_so && d.ho_so.anh_mau) || ''] || ANH_MAU.croissant;
    el.classList.toggle('xam', !/^data:image\/jpeg;base64,[A-Za-z0-9+/=]+$/.test(anh));
    if (/^data:image\/jpeg;base64,[A-Za-z0-9+/=]+$/.test(anh)) { el.style.backgroundImage = 'url("' + anh + '")'; el.style.backgroundPosition = 'center'; }
    else { el.style.backgroundImage = 'url("' + mau[0] + '")'; el.style.backgroundPosition = mau[1]; }
  }

  /* ---------- mã QR (thư viện trong repo, không CDN) ---------- */
  function veQr(el, noiDung) {
    if (!el) return;
    el.replaceChildren();
    try {
      if (typeof qrcode !== 'function') return;
      const q = qrcode(0, 'M'); q.addData(String(noiDung), 'Byte'); q.make();
      const img = tao('img', ''); img.alt = noiDung; img.src = q.createDataURL(6, 2); el.append(img);
    } catch (e) { /* không vẽ được QR thì vẫn còn mã chữ bên dưới */ }
  }

  /* ---------- đăng nhập ---------- */
  function moDangNhap() {
    hien('dang-nhap');
    an(tim('mo-dau-tv'), !!quayQua); an(tim('mo-dau-qua'), !quayQua);
    an(tim('xac-thuc'), true); an(tim('gui-ma'), false);
  }

  /* ---------- đơn bánh (giữ nguyên cách vẽ #245/#300) ---------- */
  function veDon(d) {
    const g=tim('don');g.replaceChildren();
    if(d.don_chua_mo){g.append(tao('p',(chuWeb("thanh_vien_ed802e9dd", "Lịch sử đơn hàng chưa khả dụng. Liên hệ chúng tôi nếu quý khách cần tra cứu."))));}
    else if(d.don_loi){g.append(tao('p',(chuWeb("thanh_vien_9337f4dde", "Chưa tải được lịch sử đơn. Quý khách thử lại sau"))));const nut=tao('button',(chuWeb("thanh_vien_e353f2f3d", "Thử lại")));nut.type='button';nut.onclick=()=>hoSo().catch(()=>bao((chuWeb("thanh_vien_9337f4dde", "Chưa tải được lịch sử đơn. Quý khách thử lại sau")),true));g.append(nut);}
    else if(!d.don.length)g.append(tao('p',(chuWeb("thanh_vien_276b0b7ce", "Chưa có đơn đặt online để hiển thị."))));
    d.don.forEach(o=>{
      const dong=tao('article','');dong.className='don';
      const dau=tao('div','');dau.className='hang-ngang';
      const ngay=/^(\d{4})-(\d{2})-(\d{2})$/.exec(o.ngay_dat||'');
      dau.append(tao('h3',(chuWeb("thanh_vien_0df913f30", "Đơn") + " ")+o.ma_don+(ngay?' · '+ngay[3]+'/'+ngay[2]+'/'+ngay[1]:'')));
      const nhan=tao('span',o.trang_thai||(chuWeb("thanh_vien_c5be72c3f", "Chúng tôi đang cập nhật trạng thái")));
      nhan.className='trang-thai-don '+(['xanh','vang','xam'].includes(o.mau_trang_thai)?o.mau_trang_thai:'xam');
      dau.append(nhan);dong.append(dau);
      const tong=tao('p',Number(o.tong||0).toLocaleString('vi-VN')+' đ');tong.className='tong';dong.append(tong);
      (o.mon||[]).forEach(m=>{
        const mon=tao('div','');mon.className='mon-don';
        const khung=tao('div','🍰');khung.className='ph';
        if(/^(\/files\/|\/assets\/|https:\/\/)/.test(m.hinh||'')){
          const anh=tao('img','');anh.alt=m.ten||(chuWeb("thanh_vien_d592564f9", "Ảnh món"));anh.loading='lazy';anh.src=m.hinh;
          anh.onerror=()=>khung.replaceChildren(tao('span','🍰'));khung.replaceChildren();khung.append(anh);
        }
        const ten=tao('div','');ten.append(tao('h4',m.ten||m.ma||(chuWeb("thanh_vien_50b133f3b", "Món bánh"))),tao('p',(chuWeb("thanh_vien_0433ae990", "Số lượng:") + " ")+m.sl));ten.children[0].className='c-name';
        mon.append(khung,ten);dong.append(mon);
      });g.append(dong);
    });
  }

  /* ---------- ví quà ---------- */
  const NHAN_VC = { dung_duoc: ['tv6_vc_dung', 'Dùng được', 'xanh'], da_dung: ['tv6_vc_da_dung', 'Đã dùng', 'xam'],
    het_han: ['tv6_vc_het', 'Hết hạn', 'xam'], da_huy: ['tv6_vc_huy', 'Đã huỷ', 'xam'] };
  function veVi(d) {
    const g = tim('vi'); g.replaceChildren();
    const ds = d.vi || [];
    if (!ds.length) g.append(tao('p', C('tv6_vi_rong', 'Chưa có voucher nào. Quà sinh nhật và ưu đãi sẽ nằm ở đây.'), 'phu nho'));
    ds.forEach(v => {
      const n = NHAN_VC[v.trang_thai] || NHAN_VC.dung_duoc;
      const ve = tao('article', '', 've' + (v.trang_thai === 'dung_duoc' ? '' : ' mo'));
      ve.setAttribute('data-vc', v.ma);
      const trai = tao('div', '', 've-trai'); trai.append(tao('b', v.uu_dai || '', 'vang'));
      const phai = tao('div', '', 've-phai');
      phai.append(tao('h3', v.ten || ''), tao('p', v.trang_thai === 'da_dung' && v.ngay_dung ? C('tv6_vc_dung_ngay', 'Đã dùng ngày {ngay}', { ngay: v.ngay_dung })
        : (v.dieu_kien || '') + (v.han ? ' · ' + C('tv6_vc_han', 'Hạn {han}', { han: v.han }) : ''), 'phu nho'));
      const chan = tao('div', '', 've-chan'); chan.append(tao('code', v.ma), tao('span', C(n[0], n[1]), 'chip-tt ' + n[2]));
      phai.append(chan); ve.append(trai, phai); g.append(ve);
    });
  }

  /* ---------- trang chính ---------- */
  function veChinh(d) {
    const hs = d.ho_so || {}, hang = d.hang || null;
    tim('vach-trai').textContent = C('tv6_thanh_vien', 'Thành viên');
    tim('vach-phai').textContent = d.ma_tv ? C('tv6_ma_so', 'Mã {ma}', { ma: d.ma_tv }) : '';
    veAnh(tim('av-chinh'), d); veAnh(tim('av-ho-so'), d);
    tim('hang-chip').textContent = (hang && hang.ten_hang) || C('tv6_hang_mac', 'Thành viên');
    tim('ten').textContent = hs.ten || d.ten || (chuWeb("thanh_vien_041a78ae1", "Chào quý khách"));
    tim('tu-nam').textContent = d.tu_nam ? C('tv6_tu_nam', 'Thành viên từ {nam}', { nam: d.tu_nam }) : '';
    tim('diem').textContent = so(d.diem);
    tim('hang').textContent = (hang && hang.ten_hang) || (chuWeb("thanh_vien_b44660fa4", "Thành viên Vagabond"));
    tim('quyen-loi').textContent = (hang && hang.mo_ta) || '';
    const anh = (hang && hang.anh) || ''; an(tim('anh-the'), !anh);
    if (anh && (/^\/files\//.test(anh) || /^\/assets\//.test(anh) || /^https:\/\//.test(anh))) tim('anh-the').src = anh;
    const td = d.tien_do;
    an(tim('tien-do'), !(td && td.hang_tiep));
    if (td && td.hang_tiep) {
      tim('td-tu').textContent = (hang && hang.ten_hang) || '';
      tim('td-den').textContent = td.hang_tiep;
      tim('td-b').style.width = Math.round(Math.max(0, Math.min(1, Number(td.ty_le) || 0)) * 100) + '%';
      tim('td-chu').textContent = C('tv6_td_chu', 'Đã mua {da} trong {thang} tháng. Thêm {thieu} để lên {hang}.',
        { da: so(td.da_mua) + 'đ', thang: td.so_thang, thieu: so(td.con_thieu) + 'đ', hang: td.hang_tiep });
    }
    const muc = d.muc || { du: 0, tong: 5, thieu_qua: [] };
    tim('so-don').textContent = String((d.don || []).length).padStart(2, '0');
    tim('so-vc').textContent = String((d.vi || []).filter(v => v.trang_thai === 'dung_duoc').length).padStart(2, '0');
    tim('so-hs').textContent = muc.du + '/' + muc.tong;
    const q = d.qua || {};
    /* Quà chưa nhận thì luôn còn đường nhận: hồ sơ thiếu thì mời cập nhật,
       hồ sơ đã đủ thì nút Nhận voucher (Codex PR #517 vòng 10). */
    const moi = !!(d.co_ho_so !== false && q.mo && !q.da_nhan);
    const conThieu = (muc.thieu_qua || []).length > 0;
    an(tim('moi-ho-so'), !moi);
    if (moi) {
      tim('moi-gia').textContent = soQua(q.uu_dai);
      tim('moi-dem').textContent = C('tv6_ho_so_dem', 'Hồ sơ {du}/{tong}', { du: muc.du, tong: muc.tong });
      tim('moi-chu').textContent = conThieu
        ? C('tv6_moi_chu', 'Thêm ngày sinh và đồng ý nhận tin Zalo để nhận ngay voucher {uu_dai}.', { uu_dai: q.uu_dai || '' })
        : C('tv6_moi_du', 'Hồ sơ đã đủ. Bấm nhận voucher {uu_dai}, dùng ngay hoặc trong {so_ngay} ngày.', { uu_dai: q.uu_dai || '', so_ngay: q.so_ngay || 7 });
      an(tim('moi-ho-so').querySelector('[data-di]'), !conThieu);
      an(tim('nut-moi-nhan'), conThieu);
    }
    tim('diem-vi').textContent = so(d.diem);
    tim('the-tv-hang').textContent = tim('hang-chip').textContent;
    tim('the-tv-ma').textContent = d.ma_tv || '';
    tim('the-tv-ten').textContent = [hs.ten || d.ten || '', d.sdt ? String(d.sdt).slice(0, 4) + ' *** ' + String(d.sdt).slice(-3) : ''].filter(Boolean).join(' · ');
    if (d.ma_tv) veQr(tim('qr-tv'), d.ma_tv);
  }

  /* ---------- biểu mẫu hồ sơ (dùng cho cả tab Hồ sơ và bước quà) ---------- */
  function oNhap(nhan, id, gt, kieu, them) {
    const l = tao('label', ''); l.append(tao('span', nhan, 'nhan'));
    const o = tao('input', ''); o.id = id; o.type = kieu || 'text'; o.value = gt == null ? '' : String(gt);
    Object.keys(them || {}).forEach(k => o.setAttribute(k, them[k]));
    l.append(o); return l;
  }
  function chon(id, nhan, tu, den, gt) {
    const s = tao('select', ''); s.id = id; s.setAttribute('aria-label', nhan);
    const dau = tao('option', nhan); dau.value = ''; s.append(dau);
    for (let i = tu; i <= den; i++) { const o = tao('option', String(i)); o.value = String(i); if (String(gt) === String(i)) o.selected = true; s.append(o); }
    s.value = gt ? String(gt) : '';
    return s;
  }
  function veForm(f, d, cheDo) {
    const hs = (d && d.ho_so) || {}, sn = hs.sinh_nhat || {};
    f.replaceChildren();
    f.append(oNhap(cheDo === 'qua' ? C('tv6_o_ten_goi', 'Tên gọi') : C('tv6_o_ho_ten', 'Họ và tên'), 'o-ten', hs.ten || '', 'text', { maxlength: '60', autocomplete: 'name' }));
    if (cheDo !== 'qua' && d && d.sdt) {
      const l = tao('div', '', 'o-khoa'); l.append(tao('span', C('tv6_o_sdt', 'Số điện thoại'), 'nhan'));
      const v = tao('div', '', 'gia-tri'); v.append(tao('span', d.sdt), tao('span', C('tv6_da_xac_minh', 'Đã xác minh qua Zalo'), 'xm'));
      l.append(v); f.append(l);
    }
    const ns = tao('div', '', 'o-ngay'); ns.append(tao('span', C('tv6_o_ngay_sinh', 'Ngày sinh'), 'nhan'));
    const hang3 = tao('div', '', 'ba-o');
    hang3.append(chon('o-ngay', C('tv6_ngay', 'Ngày'), 1, 31, sn.ngay), chon('o-thang', C('tv6_thang', 'Tháng'), 1, 12, sn.thang),
      (function () { const o = tao('input', ''); o.id = 'o-nam'; o.type = 'text'; o.setAttribute('inputmode', 'numeric'); o.setAttribute('maxlength', '4');
        o.setAttribute('placeholder', C('tv6_nam', 'Năm')); o.setAttribute('aria-label', C('tv6_nam', 'Năm')); o.value = sn.nam ? String(sn.nam) : ''; return o; })());
    ns.append(hang3, tao('small', C('tv6_ngay_sinh_mo_ta', 'Để gửi quà sinh nhật đúng tháng. Năm sinh không bắt buộc.'), 'phu nho'));
    f.append(ns);
    if (cheDo !== 'qua') f.append(oNhap(C('tv6_o_email', 'Email (không bắt buộc)'), 'o-email', hs.email || '', 'email', { autocomplete: 'email' }));
    const st = tao('div', '', 'o-st'); st.append(tao('span', C('tv6_o_so_thich', 'Quý khách hay chọn (không bắt buộc)'), 'nhan'));
    const chips = tao('div', '', 'chips');
    SO_THICH.forEach(([ma, ten]) => {
      const b = tao('button', ten); b.type = 'button'; b.setAttribute('data-st', ma);
      b.setAttribute('aria-pressed', (hs.so_thich || []).includes(ma) ? 'true' : 'false');
      b.onclick = () => b.setAttribute('aria-pressed', b.getAttribute('aria-pressed') === 'true' ? 'false' : 'true');
      chips.append(b);
    });
    st.append(chips); f.append(st);
    const dy = tao('label', '', 'dong-y' + (cheDo === 'qua' ? '' : ' cong-tac'));
    const ck = tao('input', ''); ck.type = 'checkbox'; ck.id = 'o-dong-y'; ck.checked = !!hs.dong_y_zalo;
    const chu = tao('span', ''); chu.append(tao('b', C('tv6_dy_tieu_de', 'Đồng ý nhận tin từ Vagabond qua Zalo')),
      tao('small', C('tv6_dy_mo_ta', 'Quà sinh nhật, voucher, báo đơn bánh. Tắt lúc nào cũng được trong trang thành viên.')));
    dy.append(ck, chu); f.append(dy);
    const nut = tao('button', cheDo === 'qua' ? C('tv6_nhan_qua_nut', 'Nhận quà {uu_dai}', { uu_dai: (d && d.qua && d.qua.uu_dai) || '' }) : C('tv6_luu_ho_so', 'Lưu hồ sơ'), 'chinh rong');
    nut.id = cheDo === 'qua' ? 'nut-nhan-qua' : 'nut-luu-hs'; f.append(nut);
  }
  function docForm(f) {
    const gt = id => { const o = f.querySelector('#' + id); return o ? String(o.value || '').trim() : ''; };
    const ck = f.querySelector('#o-dong-y');
    return { ten: gt('o-ten'), ngay: gt('o-ngay'), thang: gt('o-thang'), nam: gt('o-nam'), email: gt('o-email'),
      so_thich: Array.prototype.filter.call(f.querySelectorAll('[data-st]'), b => b.getAttribute('aria-pressed') === 'true').map(b => b.getAttribute('data-st')),
      dong_y_zalo: !!(ck && ck.checked) };
  }

  /* ---------- hồ sơ thành viên ---------- */
  function moTab(ten) {
    ['chinh', 'vi', 'don', 'ho-so'].forEach(t => an(tim('tab-' + t), t !== ten));
    document.querySelectorAll('[data-tab]').forEach(b => b.setAttribute('aria-pressed', b.getAttribute('data-tab') === ten ? 'true' : 'false'));
    if (typeof window.scrollTo === 'function') window.scrollTo(0, 0);
  }
  function veHoSo(d) {
    duLieu = d; hien('ho-so');
    veChinh(d); veVi(d); veDon(d);
    veForm(tim('form-ho-so'), d, 'ho-so');
    const am = tim('anh-mau'); am.replaceChildren();
    Object.keys(ANH_MAU).forEach(k => {
      const b = tao('button', ''); b.type = 'button'; b.setAttribute('data-anh-mau', k);
      b.setAttribute('aria-label', C('tv6_chon_hinh', 'Chọn hình bánh này'));
      b.style.backgroundImage = 'url("' + ANH_MAU[k][0] + '")'; b.style.backgroundPosition = ANH_MAU[k][1];
      b.setAttribute('aria-pressed', ((d.ho_so || {}).anh_mau === k && !d.anh) ? 'true' : 'false');
      b.onclick = () => luuHoSo({ anh_mau: k });
      am.append(b);
    });
    bao(d.co_ho_so ? '' : (chuWeb("thanh_vien_389b3feae", "Số điện thoại đã xác thực; chưa có hồ sơ thành viên tại cửa hàng.")));
  }
  /* v623: voucher dành cho thành viên cài trong phiếu Chương trình khuyến mãi
     (bật Phát vào Ví quà). Hồ sơ báo còn chương trình khách đủ điều kiện mà
     chưa nhận (vi_cho) thì xin cấp luôn, khách không phải bấm; máy chủ tự
     kiểm đối tượng, dịp phát và một kỳ một mã. Trả câu báo, rỗng khi không
     có mã mới. Lỗi mạng không chặn trang hồ sơ. */
  let viBao = '';
  async function capVi(d) {
    if (!d || !(Number(d.vi_cho) > 0)) return '';
    try {
      const r = await api('cap_vi_tv', {});
      const n = ((r && r.ok && r.moi) || []).length;
      return n ? C('tv6_vi_moi', 'Quý khách vừa nhận {so} quà mới trong Ví quà, đưa mã cho thu ngân khi thanh toán.', { so: n }) : '';
    } catch (e) { return ''; }
  }
  async function hoSo() {
    let d = await api('toi');
    if (!d.ok) { moDangNhap(); if (d.ly_do !== 'chua_dang_nhap') bao(lyDo[d.ly_do] || (chuWeb("thanh_vien_a6daf06ad", "Không đọc được hồ sơ.")), true); return false; }
    if (quayQua) return buocQua(d);
    viBao = await capVi(d);
    if (viBao) d = await api('toi');
    veHoSo(d);
    if (viBao) { moTab('vi'); bao(viBao); }
    return true;
  }
  async function luuHoSo(them) {
    const f = tim('form-ho-so');
    const dat = Object.assign(docForm(f), them || {});
    const nut = tim('nut-luu-hs'); if (nut) nut.disabled = true;
    try {
      const r = await api('luu_ho_so', { dat: dat });
      if (!r.ok) throw new Error(lyDo[r.ly_do] || C('tv6_luu_loi', 'Chưa lưu được hồ sơ. Thử lại sau.'));
      const qua = await quaSauHoSo();
      await hoSo(); moTab((qua || viBao) ? 'vi' : 'ho-so'); bao(qua || viBao || C('tv6_da_luu', 'Đã lưu hồ sơ.'));
    } catch (e) { bao(e.message, true); } finally { if (nut) nut.disabled = false; }
  }
  /* Khung mời hứa "khai đủ là nhận ngay voucher": lưu xong mà hồ sơ đủ, quà
     đang mở và chưa nhận thì nhận luôn (không gắn quầy). Máy chủ vẫn tự kiểm
     đủ điều kiện, một số một lần. Trả câu báo, rỗng khi không cấp mã mới. */
  async function quaSauHoSo() {
    const d = await api('toi');
    const q = (d && d.qua) || {};
    if (!d || !d.ok || !q.mo || q.da_nhan || ((d.muc || {}).thieu_qua || []).length) return '';
    return nhanQuaWeb(true);
  }
  async function nhanQuaWeb(imLang) {
    const r = await api('nhan_qua', { quay: '' });
    if (!r.ok) { if (imLang) return ''; throw new Error(lyDo[r.ly_do] || C('tv6_qua_loi', 'Chưa nhận được quà. Quý khách nhờ thu ngân hỗ trợ.')); }
    return C('tv6_qua_web', 'Đã nhận voucher {uu_dai}. Mã nằm trong Ví quà, dùng ngay hoặc đến hết {han}.', { uu_dai: r.uu_dai || '', han: r.han || '' });
  }

  /* Ảnh đại diện: thu về 512 px vuông JPEG ngay trên máy khách, không gửi ảnh gốc. */
  async function thuNhoAnh(tep) {
    const bm = await createImageBitmap(tep);
    const c = document.createElement('canvas'); c.width = 512; c.height = 512;
    const canh = Math.min(bm.width, bm.height);
    c.getContext('2d').drawImage(bm, (bm.width - canh) / 2, (bm.height - canh) / 2, canh, canh, 0, 0, 512, 512);
    return c.toDataURL('image/jpeg', 0.85);
  }

  /* ---------- quà chào mừng tại quầy ---------- */
  function veMaQua(r, d) {
    hien('qua-ma');
    const ten = ((d && d.ho_so && d.ho_so.ten) || (d && d.ten) || '');
    tim('qua-chao').textContent = ten ? C('tv6_chao', 'chào mừng {ten}', { ten: ten }) : '';
    tim('qua-uu-dai').textContent = r.uu_dai ? '-' + soQua(r.uu_dai) : '';
    tim('qua-ma-chu').textContent = r.ma || '';
    tim('qua-han').textContent = r.han ? C('tv6_dung_den', 'Dùng ngay hôm nay hoặc đến hết {han}', { han: r.han }) : '';
    tim('qua-ghi').textContent = r.trang_thai === 'da_dung' ? C('tv6_qua_da_dung', 'Mã quà chào mừng của số này đã dùng. Mỗi số nhận một lần.')
      : r.trang_thai === 'het_han' ? C('tv6_qua_het', 'Mã quà chào mừng của số này đã hết hạn. Mỗi số nhận một lần.')
      : r.cu ? C('tv6_qua_cu', 'Số này đã nhận quà chào mừng trước đó, đây là mã của quý khách.')
      : C('tv6_qua_luu', 'Mã đã lưu vào Ví quà trong trang thành viên.');
    an(tim('qua-ma-chu'), r.trang_thai === 'da_dung' || r.trang_thai === 'het_han' || r.trang_thai === 'da_huy');
    bao('');
  }
  async function layQua(d) {
    const r = await api('nhan_qua', { quay: quayQua });
    if (!r.ok) {
      if (r.ly_do === 'ho_so_thieu') { moFormQua(d); bao(lyDo.ho_so_thieu, true); return false; }
      throw new Error(lyDo[r.ly_do] || C('tv6_qua_loi', 'Chưa nhận được quà. Quý khách nhờ thu ngân hỗ trợ.'));
    }
    veMaQua(r, d); return true;
  }
  function moFormQua(d) { hien('qua-ho-so'); veForm(tim('form-qua'), d, 'qua'); }
  async function buocQua(d) {
    duLieu = d;
    const q = d.qua || {};
    if (!q.mo && !q.da_nhan) { veHoSo(d); bao(lyDo.qua_chua_mo, true); return true; }
    if (!q.da_nhan && ((d.muc || {}).thieu_qua || []).length) { moFormQua(d); bao(''); return true; }
    try { await layQua(d); } catch (e) { veHoSo(d); bao(e.message, true); }
    return true;
  }

  /* ---------- bảng để quầy ---------- */
  function veBang(ss) {
    hien('bang-quay');
    document.body.classList.toggle('in-bang', true);
    tim('bq-gia').textContent = soQua(ss && ss.qua && ss.qua.uu_dai);
    const goc = (typeof location !== 'undefined' && location.origin) || '';
    veQr(tim('qr-bang'), goc + '/thanh-vien?qua=' + quayBang);
    bao('');
  }

  /* ---------- nối sự kiện ---------- */
  tim('gui-ma').onsubmit=async e=>{e.preventDefault();tim('nut-gui').disabled=true;try{const so=tim('sdt').value;const d=await api('gui_ma',{sdt:so});if(!d.ok)throw new Error(lyDo[d.ly_do]||(chuWeb("thanh_vien_f23771e85", "Chưa gửi được mã. Thử lại sau.")));soDaGui=so;an(tim('xac-thuc'),false);an(tim('buoc-2'),false);if(tim('buoc-2'))tim('buoc-2').className='on';tim('ma').focus();bao((chuWeb("thanh_vien_593248be0", "Đã gửi mã qua Zalo. Mã có hiệu lực 5 phút.")));}catch(e){bao(e.message,true);}finally{tim('nut-gui').disabled=false;}};
  tim('xac-thuc').onsubmit=async e=>{e.preventDefault();tim('nut-xac-thuc').disabled=true;try{const d=await api('xac_thuc',{sdt:soDaGui,ma:tim('ma').value});if(!d.ok)throw new Error(lyDo[d.ly_do]||(chuWeb("thanh_vien_b345af644", "Không xác thực được. Gửi mã mới.")));tim('ma').value='';await hoSo();}catch(e){bao(e.message,true);}finally{tim('nut-xac-thuc').disabled=false;}};
  /* Đủ 6 số là tự gửi, không phải bấm nút. */
  tim('ma').oninput = () => { const o = tim('ma'); o.value = String(o.value || '').replace(/\D/g, '').slice(0, 6); if (o.value.length === 6 && !tim('nut-xac-thuc').disabled) tim('xac-thuc').onsubmit({ preventDefault() {} }); };
  tim('form-qua').onsubmit = async e => {
    e.preventDefault();
    const dat = docForm(tim('form-qua'));
    if (!dat.ten) return bao(lyDo.thieu_ten, true);
    if (!dat.ngay || !dat.thang) return bao(lyDo.ngay_sinh_thieu, true);
    if (!dat.dong_y_zalo) return bao(C('tv6_can_dong_y', 'Quà dành cho thành viên nhận tin Zalo. Quý khách tích ô đồng ý để nhận quà.'), true);
    const nut = tim('nut-nhan-qua'); if (nut) nut.disabled = true;
    try {
      const r = await api('luu_ho_so', { dat: dat });
      if (!r.ok) throw new Error(lyDo[r.ly_do] || C('tv6_luu_loi', 'Chưa lưu được hồ sơ. Thử lại sau.'));
      await layQua(Object.assign({}, duLieu || {}, { ho_so: { ten: dat.ten } }));
    } catch (e2) { bao(e2.message, true); } finally { if (nut) nut.disabled = false; }
  };
  tim('form-ho-so').onsubmit = e => { e.preventDefault(); luuHoSo(); };
  tim('nut-moi-nhan').onclick = async () => {
    const nut = tim('nut-moi-nhan'); nut.disabled = true;
    try { const cau = await nhanQuaWeb(false); await hoSo(); moTab('vi'); bao(cau); }
    catch (e) { bao(e.message, true); } finally { nut.disabled = false; }
  };
  tim('chon-anh').onchange = async () => {
    const tep = tim('chon-anh').files && tim('chon-anh').files[0];
    if (!tep) return;
    bao(C('tv6_dang_tai_anh', 'Đang tải ảnh...'));
    try {
      const du = await thuNhoAnh(tep);
      const r = await api('doi_anh', { du_lieu: du });
      if (!r.ok) throw new Error(lyDo[r.ly_do] || lyDo.anh_khong_dung);
      await hoSo(); moTab('ho-so'); bao(C('tv6_da_doi_anh', 'Đã đổi ảnh đại diện.'));
    } catch (e) { bao(e.message || lyDo.anh_khong_dung, true); }
  };
  document.querySelectorAll('[data-tab]').forEach(b => { b.onclick = () => moTab(b.getAttribute('data-tab')); });
  document.querySelectorAll('[data-di]').forEach(b => { b.onclick = () => moTab(b.getAttribute('data-di')); });
  tim('nut-ve-trang').onclick = () => { if (typeof location !== 'undefined' && location.assign) location.assign('/thanh-vien'); };
  tim('nut-in').onclick = () => { if (typeof window.print === 'function') window.print(); };
  tim('thoat').onclick=async()=>{tim('thoat').disabled=true;try{await api('thoat',{});moDangNhap();tim('don').replaceChildren();tim('diem').textContent='';tim('ten').textContent='';tim('anh-the').removeAttribute('src');duLieu=null;bao((chuWeb("thanh_vien_e2bfc6a0f", "Đã đăng xuất.")));}catch(e){bao(e.message,true);}finally{tim('thoat').disabled=false;}};

  /* ---------- bắt đầu ---------- */
  try {
    sanSang = await api('san_sang');
    if (quayBang) { veBang(sanSang); return; }
    if (sanSang.qua && sanSang.qua.uu_dai) tim('qua-gia').textContent = soQua(sanSang.qua.uu_dai);
    if (!await hoSo()) {
      if (!sanSang.otp) { tim('nut-gui').disabled = true; bao(lyDo.chua_mo); }
      else bao(quayQua ? C('tv6_qua_bat_dau', 'Nhập số điện thoại có Zalo để nhận quà.') : (chuWeb("thanh_vien_6168467d3", "Nhập số điện thoại đã mua bánh để xem hồ sơ.")));
    }
  } catch (e) { bao(e.message, true); moDangNhap(); }
})();

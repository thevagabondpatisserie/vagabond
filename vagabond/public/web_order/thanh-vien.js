/* Không giữ token trong localStorage; API chỉ đọc hồ sơ qua cookie HttpOnly. */
(async function () {
  'use strict';
  if (window.vgbChuSanSang) await window.vgbChuSanSang; const tim=id=>document.getElementById(id);let soDaGui='';
  const lyDo={get chua_mo(){return chuWeb("thanh_vien_7df724744", "Chúng tôi đang hoàn thiện đăng nhập thành viên. Liên hệ 0931 224 334 để tra điểm.");},get so_dien_thoai_khong_dung(){return chuWeb("thanh_vien_09fcbe5fb", "Kiểm tra lại số điện thoại.");},get gui_qua_nhieu(){return chuWeb("thanh_vien_c3f74f579", "Đã gửi nhiều mã. Chờ 30 phút rồi thử lại.");},get khong_gui_duoc(){return chuWeb("thanh_vien_048bdca06", "Chưa gửi được mã qua Zalo. Chờ một chút hoặc gọi cho chúng tôi.");},get ma_het_han(){return chuWeb("thanh_vien_27c413c51", "Mã đã hết hạn. Gửi mã mới để tiếp tục.");},get ma_khong_dung(){return chuWeb("thanh_vien_77e54d5e8", "Mã chưa đúng. Kiểm tra tin nhắn Zalo.");},get sai_qua_nhieu(){return chuWeb("thanh_vien_aa07e7c30", "Đã nhập sai quá nhiều lần. Gửi mã mới để tiếp tục.");},get can_doi_chieu(){return chuWeb("thanh_vien_dd4609ef6", "Hồ sơ cần được chúng tôi đối chiếu. Gọi 0931 224 334 để được hỗ trợ.");}};
  function bao(s,loi){tim('trang-thai').textContent=s;tim('trang-thai').classList.toggle('loi',!!loi);}
  async function api(ham,noiDung){const c={credentials:'same-origin',cache:'no-store'};if(noiDung){c.method='POST';c.headers={'Content-Type':'application/json','X-Frappe-CSRF-Token':document.querySelector('meta[name=csrf-token]').content};c.body=JSON.stringify(noiDung);}const r=await fetch('/api/method/vagabond.thanh_vien.'+ham,c);const d=await r.json();if(!r.ok||!d.message)throw new Error((chuWeb("thanh_vien_dd35ada44", "Chưa kết nối được. Thử lại sau ít phút.")));return d.message;}
  function tao(the,chu){const e=document.createElement(the);e.textContent=chu;return e;}
  async function hoSo(){const d=await api('toi');if(!d.ok){tim('ho-so').hidden=true;tim('dang-nhap').hidden=false;if(d.ly_do!=='chua_dang_nhap')bao(lyDo[d.ly_do]||(chuWeb("thanh_vien_a6daf06ad", "Không đọc được hồ sơ.")),true);return false;}tim('dang-nhap').hidden=true;tim('ho-so').hidden=false;tim('ten').textContent=d.ten||(chuWeb("thanh_vien_041a78ae1", "Chào quý khách"));tim('hang').textContent=d.hang?.ten_hang||(chuWeb("thanh_vien_b44660fa4", "Thành viên Vagabond"));tim('quyen-loi').textContent=d.hang?.mo_ta||'';tim('diem').textContent=Number(d.diem||0).toLocaleString('vi-VN')+(" " + chuWeb("thanh_vien_4a404c32e", "điểm"));const anh=d.hang?.anh||'';tim('anh-the').hidden=!anh;if(anh && (/^\/files\//.test(anh)||/^\/assets\//.test(anh)||/^https:\/\//.test(anh)))tim('anh-the').src=anh;const g=tim('don');g.replaceChildren();if(d.don_chua_mo){g.append(tao('p',(chuWeb("thanh_vien_ed802e9dd", "Lịch sử đơn hàng chưa khả dụng. Liên hệ chúng tôi nếu quý khách cần tra cứu."))));}else if(d.don_loi){g.append(tao('p',(chuWeb("thanh_vien_9337f4dde", "Chưa tải được lịch sử đơn. Quý khách thử lại sau"))));const nut=tao('button',(chuWeb("thanh_vien_e353f2f3d", "Thử lại")));nut.type='button';nut.onclick=()=>hoSo().catch(()=>bao((chuWeb("thanh_vien_9337f4dde", "Chưa tải được lịch sử đơn. Quý khách thử lại sau")),true));g.append(nut);}else if(!d.don.length)g.append(tao('p',(chuWeb("thanh_vien_276b0b7ce", "Chưa có đơn đặt online để hiển thị."))));d.don.forEach(o=>{
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
  });bao(d.co_ho_so?(chuWeb("thanh_vien_62cff3945", "Điểm đọc từ sổ điểm hiện tại của chúng tôi.")):(chuWeb("thanh_vien_389b3feae", "Số điện thoại đã xác thực; chưa có hồ sơ thành viên tại cửa hàng.")));return true;}
  try{if(!await hoSo()){const c=await api('san_sang');if(!c.otp){tim('nut-gui').disabled=true;bao(lyDo.chua_mo);}else bao((chuWeb("thanh_vien_6168467d3", "Nhập số điện thoại đã mua bánh để xem hồ sơ.")));}}catch(e){bao(e.message,true);tim('dang-nhap').hidden=false;}
  tim('gui-ma').onsubmit=async e=>{e.preventDefault();tim('nut-gui').disabled=true;try{const so=tim('sdt').value;const d=await api('gui_ma',{sdt:so});if(!d.ok)throw new Error(lyDo[d.ly_do]||(chuWeb("thanh_vien_f23771e85", "Chưa gửi được mã. Thử lại sau.")));soDaGui=so;tim('xac-thuc').hidden=false;tim('ma').focus();bao((chuWeb("thanh_vien_593248be0", "Đã gửi mã qua Zalo. Mã có hiệu lực 5 phút.")));}catch(e){bao(e.message,true);}finally{tim('nut-gui').disabled=false;}};
  tim('xac-thuc').onsubmit=async e=>{e.preventDefault();tim('nut-xac-thuc').disabled=true;try{const d=await api('xac_thuc',{sdt:soDaGui,ma:tim('ma').value});if(!d.ok)throw new Error(lyDo[d.ly_do]||(chuWeb("thanh_vien_b345af644", "Không xác thực được. Gửi mã mới.")));tim('ma').value='';await hoSo();}catch(e){bao(e.message,true);}finally{tim('nut-xac-thuc').disabled=false;}};
  tim('thoat').onclick=async()=>{tim('thoat').disabled=true;try{await api('thoat',{});tim('ho-so').hidden=true;tim('dang-nhap').hidden=false;tim('xac-thuc').hidden=true;tim('don').replaceChildren();tim('diem').textContent='';tim('ten').textContent='';tim('anh-the').removeAttribute('src');bao((chuWeb("thanh_vien_e2bfc6a0f", "Đã đăng xuất.")));}catch(e){bao(e.message,true);}finally{tim('thoat').disabled=false;}};
})();

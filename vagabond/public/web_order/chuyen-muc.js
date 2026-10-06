/* #367: nội dung chiến dịch/tuyển dụng từ bản CMS đã xuất bản, không tính
   giảm giá ở trình duyệt. Dùng DOM text, ảnh và liên kết đã qua chuẩn hóa. */
(function(){
  'use strict';
  let noiDung={khoi:[]};
  const trangThai={uu_dai:{tim:'',nhom:''},tuyen_dung:{tim:'',nhom:''}};
  const chu=(k,s)=>window.vgbChu?window.vgbChu(k,s):((window.vgbNhan||{})[k]||s);
  function tao(t,c,s){const e=document.createElement(t);e.className=c||'';if(s)e.textContent=s;return e;}
  function ngayVN(){return new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Ho_Chi_Minh',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());}
  function anToan(u){return typeof u==='string' && !/[\s\\]/.test(u) && ((u[0]==='/'&&u[1]!=='/')||u[0]==='#'||/^https:\/\/[^/@]+(?:\/|$)/.test(u));}
  function veMuc(loai){
    const g=document.getElementById('noi-'+loai);if(!g)return;g.replaceChildren();
    const ngay=ngayVN(), tt=trangThai[loai];
    const ds=(noiDung.khoi||[]).filter(k=>k.loai===loai&&(window.vgbXemThu||(k.hien&&(!k.ket_thuc||k.ket_thuc>=ngay))));
    const loc=tao('div','cm-loc'), tim=tao('input');tim.type='search';tim.placeholder=chu('tim_muc','Tìm theo tên, nhóm hoặc nơi làm');tim.setAttribute('aria-label',tim.placeholder);tim.value=tt.tim;
    const the=tao('div','cm-danh-sach');
    function veThe(){the.replaceChildren();const locDs=ds.filter(k=>(!tt.nhom||k.nhom===tt.nhom)&&[k.tieu_de,k.nhom,k.noi_lam,k.noi_dung].join(' ').toLocaleLowerCase('vi').includes(tt.tim.toLocaleLowerCase('vi')));
      if(!locDs.length){the.append(tao('p','cm-rong',chu(loai+'_rong',loai==='uu_dai'?'Chưa có ưu đãi trong nhóm này. Quý khách có thể xem các nhóm khác.':'Chưa có vị trí phù hợp trong nhóm này. Quý khách vui lòng quay lại sau.')));return;}
      locDs.forEach(k=>{
        const muc=tao('article','cm-the');muc.dataset.khoi=k.id;
        if(k.anh&&anToan(k.anh)){const im=tao('img','cm-anh');im.src=k.anh;im.alt=k.mo_ta_anh||'';im.loading='lazy';muc.append(im);}
        const nd=tao('div','cm-noi-dung');nd.append(tao('p','cm-nhan',k.nhan||k.nhom),tao('h2','',k.tieu_de));
        if(k.bat_dau>ngay)nd.append(tao('p','cm-trang-thai',chu('sap_dien_ra','Sắp diễn ra')));
        if(k.bat_dau||k.ket_thuc)nd.append(tao('p','cm-ngay',[k.bat_dau,k.ket_thuc].filter(Boolean).map(x=>x.split('-').reverse().join('/')).join(' - ')));
        nd.append(tao('p','cm-doan',k.noi_dung));
        if(loai==='uu_dai'&&k.ma_uu_dai)nd.append(tao('p','cm-ma',chu('ma_uu_dai','Mã ưu đãi')+': '+k.ma_uu_dai));
        if(loai==='tuyen_dung'&&!k.ket_thuc)nd.append(tao('p','cm-ngay',chu('chua_han','Nhận hồ sơ đến khi đủ người')));
        if(loai==='tuyen_dung')nd.append(tao('p','cm-thong-tin',[k.noi_lam,k.hinh_thuc].filter(Boolean).join(' · ')));
        let duong=anToan(k.lien_ket)?k.lien_ket:'';
        if(loai==='tuyen_dung'&&!duong&&/^[A-Za-z0-9_.+%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(k.email||''))duong='mailto:'+k.email+'?subject='+encodeURIComponent('Ứng tuyển - '+k.tieu_de);
        if(duong){const a=tao('a','cm-nut',k.nut||(loai==='tuyen_dung'?chu('ung_tuyen','Ứng tuyển vị trí này'):chu('xem_chi_tiet_muc','Xem chi tiết')));a.href=duong;nd.append(a);}
        muc.append(nd);the.append(muc);
      });
    }
    tim.oninput=()=>{tt.tim=tim.value;veThe();};loc.append(tim);
    const chips=tao('div','cm-chips');['',...new Set(ds.map(k=>k.nhom).filter(Boolean))].forEach(n=>{const b=tao('button','',n||chu('tat_ca_muc','Tất cả'));b.setAttribute('aria-pressed',String(n===tt.nhom));b.onclick=()=>{tt.nhom=n;veMuc(loai);};chips.append(b);});
    g.append(loc,chips,the);veThe();
  }
  window.vgbVeChuyenMuc=nd=>{noiDung=nd;veMuc('uu_dai');veMuc('tuyen_dung');};
  document.addEventListener('vgb-nhan',()=>{veMuc('uu_dai');veMuc('tuyen_dung');});
})();

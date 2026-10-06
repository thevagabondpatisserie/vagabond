/* #436: các kênh đặt hàng gom trong một nút; Marketing sửa qua cùng bản nháp.
   Chỉ mở liên kết HTTPS; không nhúng SDK theo dõi hoặc tự mở ứng dụng. */
(function () {
  'use strict';
  const goc = document.createElement('aside');
  goc.className = 'kenh-noi'; document.body.append(goc);
  const tao = (the, chu, lop) => { const e=document.createElement(the);e.textContent=chu||'';if(lop)e.className=lop;return e; };
  function linkAnToan(v, zalo) {
    try { const u=new URL(v);return u.protocol==='https:'&&!u.username&&!u.password&&(!zalo||(u.hostname==='zalo.me'&&/^\/(?:[0-9]{15,25}|[A-Za-z][A-Za-z0-9._-]{2,59})\/?$/.test(u.pathname)))?u.href:''; }
    catch(_){return '';}
  }
  function anhAnToan(v) {
    if(!v || /[\s\\]/.test(v) || v.startsWith('/private/') || /\.svg(?:[?#]|$)/i.test(v))return '';
    return (v.startsWith('/')&&!v.startsWith('//'))||linkAnToan(v)?v:'';
  }
  function logo(k, lop, duPhong) {
    const boc=tao('span','',lop);boc.setAttribute('aria-hidden','true');
    const chu=tao('span',duPhong||k.nut||k.tieu_de?.slice(0,2)||'↗','kenh-logo-du-phong');
    const src=anhAnToan(k.anh);
    if(src){const img=tao('img');img.alt='';img.src=src;img.decoding='async';
      img.onload=()=>{chu.hidden=true;};img.onerror=()=>{img.hidden=true;chu.hidden=false;};
      boc.append(img,chu);chu.hidden=true;
    }else boc.append(chu);
    return boc;
  }
  let dong = () => {};
  document.addEventListener('keydown', e => { if(e.key==='Escape'&&goc.querySelector('.kenh-bang:not([hidden])')){e.preventDefault();e.stopImmediatePropagation();dong(true);} },true);
  document.addEventListener('click', e => { if(!goc.contains(e.target))dong(false); });
  window.addEventListener('hashchange',()=>dong(false));
  function leDay() {
    const bar=document.getElementById('bar');
    goc.style.bottom='calc('+((bar?.classList.contains('on')?bar.getBoundingClientRect().height:0)+16)+'px + env(safe-area-inset-bottom))';
  }
  const bar=document.getElementById('bar');
  if(bar){new MutationObserver(leDay).observe(bar,{attributes:true,attributeFilter:['class']});if(window.ResizeObserver)new ResizeObserver(leDay).observe(bar);}
  window.addEventListener('resize',leDay);
  window.vgbVeKenhNoi = function(nd) {
    const nhan=nd.nhan||{}, chu=(ma,macDinh)=>nhan[ma]||macDinh;
    const kenh=(nd.khoi||[]).filter(k=>k.loai==='kenh_dat_hang'&&k.hien&&linkAnToan(k.lien_ket));
    const zalo=(nd.khoi||[]).find(k=>k.loai==='zalo_oa'&&k.hien&&linkAnToan(k.lien_ket,true));
    const cauHinh=(nd.khoi||[]).find(k=>k.loai==='nut_kenh')||{hien:true,anh:'/assets/vagabond/web_order/logo-kenh/grab.png'};
    const coApp=kenh.length&&cauHinh.hien;
    goc.replaceChildren();goc.setAttribute('aria-label',chu('kenh_noi_nhan','Kênh đặt hàng và hỗ trợ'));
    dong=()=>{};
    if(coApp){
      const bang=tao('div','','kenh-bang');bang.id='kenh-dat-hang';bang.hidden=true;
      const dau=tao('div','','kenh-dau');dau.append(tao('strong',chu('kenh_noi_tieu_de','Đặt qua ứng dụng')));
      const tat=tao('button','×','kenh-dong');tat.type='button';tat.setAttribute('aria-label',chu('kenh_noi_dong','Đóng kênh đặt hàng'));dau.append(tat);bang.append(dau);
      bang.append(tao('p',chu('kenh_noi_mo_ta','Quý khách chọn ứng dụng để xem thực đơn và đặt món.'),'kenh-mo-ta'));
      const ds=tao('div','','kenh-danh-sach');
      kenh.forEach(k=>{const a=tao('a','','kenh-lien-ket');a.href=linkAnToan(k.lien_ket);a.target='_blank';a.rel='noopener noreferrer';a.dataset.khoi=k.id;
        a.append(logo(k,'kenh-logo'),tao('span',k.tieu_de),tao('span','↗','kenh-mui-ten'));ds.append(a);});
      bang.append(ds,tao('p',chu('kenh_noi_tab_moi','Liên kết mở trong tab mới.'),'kenh-chu-thich'));
      const nut=tao('button','','kenh-bong kenh-app');nut.type='button';nut.setAttribute('aria-expanded','false');nut.setAttribute('aria-controls',bang.id);
      const ten=cauHinh.tieu_de||chu('kenh_noi_nut','Đặt qua app');nut.setAttribute('aria-label',ten);nut.title=ten;
      nut.append(logo(cauHinh,'kenh-logo-nut','↗'));
      dong=layLai=>{const mo=!bang.hidden;bang.hidden=true;nut.setAttribute('aria-expanded','false');if(mo&&layLai)nut.focus();};
      nut.onclick=()=>{bang.hidden=!bang.hidden;nut.setAttribute('aria-expanded',String(!bang.hidden));if(!bang.hidden)tat.focus();};tat.onclick=()=>dong(true);
      goc.append(bang,nut);
    }
    if(zalo){const a=tao('a','','kenh-bong kenh-zalo');a.href=linkAnToan(zalo.lien_ket,true);a.target='_blank';a.rel='noopener noreferrer';a.dataset.khoi=zalo.id;
      a.append(logo(zalo,'kenh-logo-zalo',zalo.nut||'Zalo'),tao('span',zalo.tieu_de));goc.append(a);}
    goc.hidden=!coApp&&!zalo;leDay();
  };
}());

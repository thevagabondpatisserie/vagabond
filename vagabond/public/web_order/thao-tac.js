/* #460: bàn phím trong bảng chi tiết. Không tham gia tính đơn hoặc ưu đãi. */
(function(){
  'use strict';
  let bang=null,truoc=null;
  const chon='button:not([disabled]),a[href],input:not([disabled]),select:not([disabled]),textarea:not([disabled]),summary,[tabindex="0"]';
  function nutTrong(el){return Array.from(el.querySelectorAll(chon)).filter(n=>n.getClientRects().length);}
  function dongBo(){
    const moi=document.querySelector('#sheet.open,#sheetMua.open,#checkout.open');
    if(moi===bang)return;
    if(moi){if(!bang)truoc=document.activeElement;bang=moi;const nut=nutTrong(moi)[0];if(nut)nut.focus({preventScroll:true});}
    else{bang=null;if(truoc&&truoc.isConnected&&truoc.getClientRects().length)truoc.focus({preventScroll:true});truoc=null;}
  }
  for(const el of document.querySelectorAll('#sheet,#sheetMua,#checkout'))new MutationObserver(dongBo).observe(el,{attributes:true,attributeFilter:['class']});
  document.addEventListener('keydown',e=>{
    if(e.key!=='Tab'||!bang)return;
    const nuts=nutTrong(bang);if(!nuts.length)return;
    const dau=nuts[0],cuoi=nuts[nuts.length-1],hien=document.activeElement;
    if(e.shiftKey&&(hien===dau||!bang.contains(hien))){e.preventDefault();cuoi.focus();}
    else if(!e.shiftKey&&(hien===cuoi||!bang.contains(hien))){e.preventDefault();dau.focus();}
  });
  dongBo();
})();

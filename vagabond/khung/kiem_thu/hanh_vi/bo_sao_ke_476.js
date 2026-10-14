/* #476: bấm DOM thật của màn chung, không chép lại phép chọn vào ca kiểm. */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert');
const {taiLieuGia} = require('./dom_gia');
const source = fs.readFileSync(path.resolve(__dirname, '../../../public/js/bep/23-khop-sepay.js'), 'utf8');
let dat = 0, hong = 0;
async function ca(ten, fn) { try { await fn(); dat++; } catch(e) { hong++; console.error('HỎNG', ten, e.stack); } }
function dong(name, con, bank='MB') { return {name, con_lai:con, tien:con, bank_account:bank, date:'2026-10-14', dung_duoc:1}; }
async function man(rows, can=714138056, save) {
  const document = taiLieuGia(), calls=[], tin=[];
  let response={rows, so_tien:can, chon_bo:1, tai_khoan_sepay:[{ma:'MB',nhan:'MB'}]};
  const g={document, console, Number, Math, JSON, Object, String, Array, Promise, setTimeout, clearTimeout,
    h:s=>String(s ?? ''), money:s=>String(s), hsNgayVn:s=>s, baoTin:s=>tin.push(s),
    api:async()=>response, frame:(title, html)=>{document.body.innerHTML=html; return document.body;}};
  vm.createContext(g); vm.runInContext(source,g);
  const o={loai:'app',ma:'APP-476',chon:async (...args)=>{calls.push(args); if(save) return save(...args);}};
  const render=async()=>g.scrKhopSepay(o);
  await render();
  return {document,g,o,calls,tin,render,response,
    nut:id=>document.getElementById(id),
    chon:ma=>document.body.querySelector('[data-gd="'+ma+'"]').click()};
}
(async()=>{
  await ca('450M thiếu, đủ hai dòng mới Gán; payload không nhân tổng',async()=>{
    const m=await man([dong('A',450000000),dong('B',264138056)]);
    assert.equal(m.nut('ksGan').disabled,true); m.chon('A');
    assert.equal(m.nut('ksGan').disabled,true); assert(m.nut('ksTong').textContent.includes('264138056'));
    m.chon('B'); assert.equal(m.nut('ksGan').disabled,false);
    await m.nut('ksGan').onclick();
    assert.deepEqual(JSON.parse(m.calls[0][0]),[{name:'A',phan_bo:450000000},{name:'B',phan_bo:264138056}]);
    assert.equal(m.calls[0][1],714138056);
  });
  await ca('một dòng chia phần đúng tiền phiếu, không lấy nguyên BT',async()=>{
    const m=await man([dong('A',100000)],60000); m.chon('A'); await m.nut('ksGan').onclick();
    assert.equal(JSON.parse(m.calls[0][0])[0].phan_bo,60000);
    const text=m.document.body.querySelector('[data-gd="A"]').querySelector('.ksPhan').textContent;
    assert(text.includes('Gán cho phiếu này 60000 đ'));assert(text.includes('còn lại 40000 đ'));
    m.chon('A');assert(!m.document.body.querySelector('[data-gd="A"]').querySelector('.ksPhan').textContent.includes('Gán cho'));
  });
  await ca('khác tài khoản không cộng lẫn',async()=>{
    const m=await man([dong('A',60),dong('B',40,'ACB')],100);m.chon('A');m.chon('B');
    assert.equal(m.nut('ksGan').disabled,true);assert.equal(Object.keys(m.o._boSepay).length,1);assert(m.tin[0].includes('cùng một'));
  });
  await ca('bỏ một dòng hoặc cả bộ làm Gán tắt',async()=>{
    const m=await man([dong('A',60),dong('B',40)],100);m.chon('A');m.chon('B');m.chon('A');
    assert.equal(m.nut('ksGan').disabled,true);m.nut('ksXoa').click();assert.equal(Object.keys(m.o._boSepay).length,0);
  });
  await ca('giữ lựa chọn qua trang rồi chọn phần còn thiếu',async()=>{
    const m=await man([dong('A',60)],100);m.response.con_nua=1;await m.render();m.chon('A');
    m.response.rows=[dong('B',40)];await m.nut('ksTiep').onclick();m.chon('B');
    assert.equal(m.nut('ksGan').disabled,false);await m.nut('ksGan').onclick();assert.equal(JSON.parse(m.calls[0][0]).length,2);
  });
  await ca('BT vừa bị người khác giữ phải bỏ lựa chọn cũ khi tải lại',async()=>{
    const m=await man([dong('A',100)],100);m.chon('A');m.response.rows=[dong('A',20)];await m.render();
    assert.equal(m.nut('ksGan').disabled,true);assert.equal(Object.keys(m.o._boSepay).length,0);
  });
  await ca('nhấp Gán hai lần trong khi đang gửi chỉ gửi một lần',async()=>{
    let xong;const m=await man([dong('A',100)],100,()=>new Promise(r=>{xong=r;}));m.chon('A');
    const p=m.nut('ksGan').onclick();await m.nut('ksGan').onclick();m.chon('A');
    assert.equal(m.calls.length,1);assert.equal(Object.keys(m.o._boSepay).length,1);xong();await p;
  });
  await ca('ghi lỗi còn lựa chọn để thử lại, không giả báo thành công',async()=>{
    const m=await man([dong('A',100)],100,()=>{throw Error('Máy chủ từ chối');});m.chon('A');
    await assert.rejects(m.nut('ksGan').onclick(),/Máy chủ/);
    assert.equal(m.nut('ksGan').disabled,false);assert.equal(Object.keys(m.o._boSepay).length,1);
  });
  await ca('dòng bị chặn và số không hữu hạn không thành lựa chọn',async()=>{
    const a=dong('A',100);a.dung_duoc=0;a.vi_sao_khong='Sai nguồn';
    const m=await man([a,dong('B',NaN)],100);m.chon('A');m.chon('B');
    assert.equal(m.nut('ksGan').disabled,true);assert.equal(Object.keys(m.o._boSepay).length,0);
  });
  await ca('công nợ thu kỳ40 chỉ lấy40, số còn phải thu đổi không cho Gán',async()=>{
    const m=await man([dong('A',100)],100);
    m.o.loai='cong_no';m.o.tien_ky=40;await m.render();m.chon('A');
    await m.nut('ksGan').onclick();assert.equal(m.calls[0][1],40);
    m.response.so_tien=20;await m.render();assert.equal(m.nut('ksGan'),null);
    assert(m.document.body.textContent.includes('đã đổi'));
  });
  await ca('công nợ bộ mất phản hồi thử lại đúng payload và mã lần',async()=>{
    const m=await man([],100),vet=[];
    const s=fs.readFileSync(path.resolve(__dirname,'../../../public/js/bep/21-ke-toan-khac.js'),'utf8');
    vm.runInContext(s,m.g);
    m.g.hoiSo=async()=>40;m.g.hoiChu=async()=> 'Khách trả góp';m.g.hoiCo=async()=>true;
    m.g.go=()=>{};m.g.scrKhopSepay=async o=>{m.o=o;};
    m.g.api=async(h,p)=>{vet.push(JSON.parse(JSON.stringify(p)));if(vet.length===1)throw Error('Mất mạng');return {ok:1};};
    const d={name:'CN',con_thieu:100};
    await m.g.cnKhopBo(d,'LAN1');await m.o.chon('[{"name":"BT","phan_bo":40}]',40);
    assert(m.g.CN_BO_CHO.CN);await m.g.cnKhopBo(d,'LAN-KHAC');
    assert.deepEqual(vet[0],vet[1]);assert.equal(m.g.CN_BO_CHO.CN,undefined);
    assert.equal(vet[1].ma_lan,'LAN1');
  });
  await ca('màn cũ không có cờ bộ vẫn gọi cửa cũ',async()=>{
    const m=await man([dong('A',100)],100);m.response.chon_bo=0;await m.render();m.chon('A');
    assert.equal(m.calls[0][0],'A');assert.equal(m.nut('ksGan'),null);
  });
  await ca('bỏ bộ cần xác nhận; lỗi máy chủ không báo thành công',async()=>{
    const m=await man([],100),vet=[];
    m.g.confirmSheet=async()=>false;m.g.busy=()=>{};m.g.toast=()=>vet.push('toast');
    m.g.api=async()=>{vet.push('api');throw Error('Còn bút toán');};
    await m.g.boBoSepay('ttnb','T',()=>vet.push('ve'));assert.deepEqual(vet,[]);
    m.g.confirmSheet=async()=>true;
    await m.g.boBoSepay('ttnb','T',()=>vet.push('ve'));assert.deepEqual(vet,['api']);assert(m.tin.includes('Còn bút toán'));
    m.g.api=async(ham,p)=>{assert.equal(ham,'vagabond.bo_sao_ke_luong.bo');assert.equal(p.ma,'T');return {ok:1};};
    await m.g.boBoSepay('ttnb','T',()=>vet.push('ve'));assert.deepEqual(vet,['api','toast','ve']);
  });
  await ca('nút bỏ bộ TTNB và hoàn tiền theo cờ quyền máy chủ',async()=>{
    const m=await man([],100);
    for(const [tep,ham,sau,id,d] of [
      ['16-mua-hang.js','ttnbKhopSepay','async function ttnbKhopAuto','ttnbBoBo',{ma_gd:'BT',khop_duoc:0}],
      ['11-khach-ca-hop-dong.js','htCtKhopSepay','async function htSinhLai','htBoBo',{duoc_doi_chieu:1,da_doi_soat:1}]
    ]) {
      const s=fs.readFileSync(path.resolve(__dirname,'../../../public/js/bep/'+tep),'utf8');
      vm.runInContext(s.slice(s.indexOf('function '+ham+'('),s.indexOf(sau)),m.g);
      m.document.body.innerHTML=m.g[ham](d);assert.equal(m.nut(id),null);
      d.bo_sao_ke_duoc=1;m.document.body.innerHTML=m.g[ham](d);assert(m.nut(id));
    }
  });
  console.log('#476 DOM:',dat,'đạt,',hong,'hỏng');if(hong)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});

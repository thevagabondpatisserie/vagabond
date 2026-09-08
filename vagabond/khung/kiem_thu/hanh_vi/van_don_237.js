const fs=require('fs'),vm=require('vm'),assert=require('assert');
const src=fs.readFileSync('vagabond/public/js/bep/12-van-don.js','utf8');
const c={vdTab:'cho_gan',vdSap:''};
vm.createContext(c);
vm.runInContext(src.slice(src.indexOf('function vdLaBookApp'),src.indexOf('async function scrVdView')),c);
vm.runInContext(src.slice(src.indexOf('function vdSapXep'),src.indexOf('/* ---------- Hàng chip')),c);
const rows=[{name:'cu',creation:'2026-09-08 08:00:00'},{name:'moi',creation:'2026-09-08 09:00:00'}];
assert.equal(c.vdSapXep(rows)[0].name,'moi');assert.equal(rows[0].name,'cu');
c.vdTab='dang_giao';assert.equal(c.vdSapXep(rows)[0].name,'cu','giữ thứ tự tuyến');
const code=src.slice(src.indexOf("    if (k === 'giao') {"),src.indexOf("    if (k === 'loi')",src.indexOf("    if (k === 'giao') {")));
(async()=>{
  for(const [d,anh] of [[{kenh:'Khách tự lấy'},false],[{kenh:'Shipper nội bộ',diem_pickup:'TCV'},false],
    ...['Ahamove','GreenSM','Grab','BE','Lalamove'].map(kenh=>[{kenh},false]),[{kenh:'Shipper nội bộ'},true]]) {
    const goi=[];
    Object.assign(c,{d,k:'giao',name:'THU',busy:()=>{},toast:()=>{},baoTin:e=>{throw Error(e)},go:()=>{},scrVdView:()=>{},
      vdDiemNgan:()=>'',vdChupAnh:async cb=>{goi.push('camera');return cb('blob')},
      vdUpload:async()=>{goi.push('upload');return 'file'},api:async(m,p)=>{goi.push(p);return {da_bao_pancake:true}}});
    await vm.runInContext('(async function(){'+code+'})()',c);
    assert.equal(goi.includes('camera'),anh);assert.equal(goi.includes('upload'),anh);
    const req=goi.filter(x=>typeof x==='object');assert.equal(req.length,1);
    assert.equal(req[0].file_url,anh?'file':null);
  }
  console.log('PASS #237: newest-first, preserve route, optional photo reaches completion API');
})().catch(e=>{console.error(e);process.exit(1)});

vm.runInContext(src.slice(src.indexOf('function vdTomTatDongBo'),src.indexOf('async function scrVanDon')),c);
const thongBao=c.vdTomTatDongBo({them:0,lam_moi:1,loi:[],doi_chieu:{
  ngay:{can_kiem:11,doc_duoc:11,chua_kiem:0,loi_doc:0},
  qua_han:{can_kiem:1325,doc_duoc:9,chua_kiem:1316,loi_doc:0}}});
assert(thongBao.includes('Ngày đang xem: đọc được 11/11'));
assert(thongBao.includes('Đơn quá hạn: đọc được 9/1325'));
assert(!thongBao.includes('Lỗi cần kiểm'),'backlog không bị gọi là lỗi');
const loiDoc=c.vdTomTatDongBo({loi:[{ma_don:'93405',loi:'Chưa đọc được'}],doi_chieu:{ngay:{can_kiem:11,doc_duoc:3,chua_kiem:7,loi_doc:1}}});
assert(loiDoc.includes('Bấm Cập nhật đơn để kiểm tiếp'));
assert(loiDoc.includes('93405: Chưa đọc được'),'lỗi thực vẫn hiện');
assert(src.includes('baoTin(vdTomTatDongBo(kq))'),'nút đồng bộ dùng thông báo mới');
console.log('PASS #237: tách ngày đang xem, backlog và lỗi thật');

/* #259: chạy hàm UI thật, chặn929 request và callback cũ ghi sai dòng. */
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const tep = process.argv[2] || 'vagabond/public/js/purchase_invoice.js';
const ma = fs.readFileSync(tep, 'utf8');
const dau = ma.indexOf('async function vgbTaiKhoanDichVu(');
assert(dau >= 0);
const cuoi = ma.indexOf("\nfrappe.ui.form.on('Purchase Invoice'", dau);
assert(cuoi > dau);

function cho() {
  let mo;
  const doi = new Promise(resolve => { mo = resolve; });
  return {doi, mo};
}

function nen(ds, tuy = {}) {
  const goi = [], ghi = [];
  const frm = {doc:{name:'PI-THU', docstatus:0, vgb_loai_chung_tu:'Mua dịch vụ',
    vgb_tk_chi_phi:'TK-A', items:ds}, refresh_field:()=>{}};
  async function tra(cacMa, args) {
    goi.push(cacMa);
    if (tuy.tra) return tuy.tra(cacMa, frm, goi.length);
    return cacMa.filter(m => m !== 'THIEU').map(name => ({name, is_stock_item:name === 'KHO' ? 1 : 0}));
  }
  const ctx = {frappe:{
    call:async q => {
      assert.strictEqual(q.method, 'frappe.client.get_list');
      assert.strictEqual(q.type, 'POST');
      assert.strictEqual(q.args.doctype, 'Item');
      assert.deepStrictEqual(Array.from(q.args.fields), ['name', 'is_stock_item']);
      const dsMa = Array.from(q.args.filters.name[1]);
      assert(dsMa.length <= 100);
      assert.strictEqual(q.args.limit_page_length, dsMa.length);
      return {message:await tra(dsMa, q.args)};
    },
    // Cùng môi trường chạy bản cũ làm bằng chứng đỏ, không viết lại hàm UI.
    db:{get_value:async (_dt, m) => {
      const rows=await tra([m]); return {message:Array.isArray(rows) ? rows[0] || {} : rows};
    }},
    model:{set_value:async (_dt, name, field, value) => {
      const row = frm.doc.items.find(d => d.name === name);
      assert(row); row[field] = value; ghi.push({name, value});
      if (tuy.ghi) await tuy.ghi(frm, ghi.length);
    }}
  }};
  vm.createContext(ctx);
  vm.runInContext(ma.slice(dau, cuoi), ctx);
  return {frm, goi, ghi, chay:()=>ctx.vgbTaiKhoanDichVu(frm)};
}

function dong(name, item_code, them={}) {
  return {doctype:'Purchase Invoice Item', name, item_code, expense_account:'CU', ...them};
}
const cacCa = [];
function ca(ten, ham) { cacCa.push([ten, ham]); }

ca('929 mã riêng chỉ10 request, không cắt ở20 bản ghi', async()=>{
  const n = nen(Array.from({length:929}, (_,i)=>dong('r'+i, 'DV'+i)));
  await n.chay();
  assert(n.goi.length <= 10, `nhận ${n.goi.length} request`);
  assert.strictEqual(n.ghi.length, 929);
  assert(n.frm.doc.items.every(d=>d.expense_account === 'TK-A'));
});
ca('929 dòng cùng một mã chỉ tra một lần', async()=>{
  const n = nen(Array.from({length:929}, (_,i)=>dong('r'+i, 'DV')));
  await n.chay(); assert.strictEqual(n.goi.length, 1); assert.strictEqual(n.ghi.length, 929);
});
ca('giữ hàng kho, PNK và mã thiếu metadata; dòng dịch vụ không mã vẫn áp', async()=>{
  const n = nen([dong('a','KHO'), dong('b','DV',{purchase_receipt:'PR'}),
    dong('c','THIEU'), dong('d','DV'), dong('e',null)]);
  await n.chay();
  assert.deepStrictEqual(n.frm.doc.items.map(d=>d.expense_account), ['CU','CU','CU','TK-A','TK-A']);
});
ca('metadata null hoặc thiếu cờ không được coi là dịch vụ', async()=>{
  const n = nen([dong('a','DV')], {tra:async()=>[{name:'DV', is_stock_item:null}]});
  await n.chay(); assert.strictEqual(n.ghi.length, 0);
});
ca('đổi header khi đang tra không áp phản hồi cũ', async()=>{
  const n = nen([dong('a','DV')], {tra:async(ms,frm)=>{
    frm.doc.vgb_tk_chi_phi='TK-B'; return ms.map(name=>({name,is_stock_item:0}));
  }});
  await n.chay(); assert.strictEqual(n.ghi.length, 0);
});
ca('đổi món, xóa dòng hoặc nối PNK trong lúc tra không ghi đè', async()=>{
  const n = nen([dong('a','DV'),dong('b','DV'),dong('c','DV')], {tra:async(ms,frm,lan)=>{
    if(lan===1) {
      frm.doc.items[0].item_code='KHO'; frm.doc.items.splice(1,1);
      frm.doc.items[1].purchase_receipt='PR';
    }
    return ms.map(name=>({name,is_stock_item:0}));
  }});
  await n.chay(); assert.strictEqual(n.ghi.length, 0);
});
ca('đổi A sang B rồi lại A không cho callback A cũ chạy lần hai', async()=>{
  const tre = cho();
  const n = nen([dong('a','DV')], {tra:async(ms,_frm,lan)=>{
    if(lan===1) await tre.doi; return ms.map(name=>({name,is_stock_item:0}));
  }});
  const cu = n.chay();
  n.frm.doc.vgb_tk_chi_phi='TK-B'; await n.chay();
  n.frm.doc.vgb_tk_chi_phi='TK-A'; await n.chay();
  const so = n.ghi.length; tre.mo(); await cu;
  assert.strictEqual(n.ghi.length, so); assert.strictEqual(n.frm.doc.items[0].expense_account,'TK-A');
});
ca('chuyển object phiếu trong lúc tra không chạm phiếu mới', async()=>{
  const n = nen([dong('a','DV')], {tra:async(ms,frm)=>{
    frm.doc={...frm.doc, name:'PI-KHAC',items:[dong('a','DV')]};
    return ms.map(name=>({name,is_stock_item:0}));
  }});
  await n.chay(); assert.strictEqual(n.ghi.length, 0);
});
ca('đổi loại hoặc submit trong lúc tra dừng cập nhật', async()=>{
  for (const sua of [frm=>{frm.doc.docstatus=1;},frm=>{frm.doc.vgb_loai_chung_tu='Mua hàng';}]) {
    const n = nen([dong('a','DV')], {tra:async(ms,frm)=>{sua(frm); return ms.map(name=>({name,is_stock_item:0}));}});
    await n.chay(); assert.strictEqual(n.ghi.length, 0);
  }
});
ca('đổi header trong await set_value dừng trước dòng sau', async()=>{
  const n = nen([dong('a','DV'),dong('b','DV')], {ghi:async(frm,lan)=>{if(lan===1) frm.doc.vgb_tk_chi_phi='TK-B';}});
  await n.chay(); assert.deepStrictEqual(n.frm.doc.items.map(d=>d.expense_account),['TK-A','CU']);
});
ca('phản hồi lô thiếu danh sách không ghi bất cứ dòng nào', async()=>{
  const n = nen([dong('a','DV')], {tra:async()=>undefined});
  let loi;
  try { await n.chay(); } catch(e) { loi=e; }
  assert.strictEqual(n.ghi.length,0); assert.strictEqual(loi,undefined);
});

(async()=>{
  let hong=0;
  for(const [ten, ham] of cacCa) {
    try { await ham(); console.log('PASS '+ten); }
    catch(e) { hong++; console.error('FAIL '+ten+': '+e.message); }
  }
  console.log(`${cacCa.length-hong}/${cacCa.length} đạt`);
  if(hong) process.exitCode=1;
})();

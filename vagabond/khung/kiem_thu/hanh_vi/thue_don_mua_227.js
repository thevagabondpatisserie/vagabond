/* #227: callback nạp 8% sau sửa giá không thắng lựa chọn 5% của đơn. */
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
let handlers, confirm;
const ctx = {frappe: {ui:{form:{on:(_dt,h)=>{handlers=h;}}}, utils:{escape_html:x=>x},
  confirm:(_s, f)=>{confirm=f;}, show_alert:()=>{}, msgprint:()=>{}}};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync('vagabond/public/js/purchase_order.js','utf8'),ctx);
const doc = {docstatus:0,company:'CT',taxes_and_charges:'5%',vgb_thue_theo_mau:0,
  items:[{item_tax_template:'8%',item_tax_rate:'{"VAT":8}',rate:742857}], taxes:[{account_head:'VAT',rate:5}]};
let button;
const frm={doc,fields_dict:{},set_df_property:()=>{},refresh_field:()=>{},
  add_custom_button:(_s,f)=>{button=f;},
  set_value:async(k,v)=>{doc[k]=v; if(handlers[k]) await handlers[k](frm);},
  trigger:async(event)=>{
    if(event==='taxes_and_charges') doc.taxes[0].rate=5;
    return frm.cscript.calculate_taxes_and_totals();
  },
  cscript:{calculate_taxes_and_totals:function(){
    assert.strictEqual(this,frm.cscript);
    doc.tax=doc.items.reduce((s,r)=>s+r.rate*((JSON.parse(r.item_tax_rate).VAT ?? doc.taxes[0].rate)/100),0);
  }}};
(async()=>{
 handlers.refresh(frm);
 frm.cscript.calculate_taxes_and_totals();
 assert.strictEqual(doc.tax,59428.56); // đúng ảnh lỗi: mặc định món 8% thắng đầu phiếu5%.
 doc.taxes[0].rate=8; // bảng thuế chỉnh tay cũng phải nạp lại mẫu5 trước khi hiện tổng.
 button(); await confirm();
 assert.strictEqual(doc.tax,37142.85);
 // callback phản hồi muộn sau sửa giá mang mẫu8 về lại.
 doc.items[0].rate=100000;
 doc.items[0].item_tax_template='8%';doc.items[0].item_tax_rate='{"VAT":8}';
 frm.cscript.calculate_taxes_and_totals();
 assert.strictEqual(doc.tax,5000);
 assert.strictEqual(doc.items[0].item_tax_template,'');
 // Thêm dòng cũng theo mẫu đầu phiếu.
 doc.items.push({rate:100000,item_tax_template:'10%',item_tax_rate:'{"VAT":10}'});
 frm.cscript.calculate_taxes_and_totals();assert.strictEqual(doc.tax,10000);
 // Chế độ nhiều mức không bị phá.
 doc.vgb_thue_theo_mau=0;
 doc.items[0].item_tax_rate='{"VAT":8}';doc.items[1].item_tax_rate='{"VAT":10}';
 frm.cscript.calculate_taxes_and_totals();assert.strictEqual(doc.tax,18000);
 // Chốt một mẫu khác trong khi hộp hỏi cũ còn mở: không áp nhầm.
 button(); doc.taxes_and_charges='10%'; await confirm();assert.strictEqual(doc.vgb_thue_theo_mau,0);
 doc.shipping_rule='Phi rieng';button();await confirm();assert.strictEqual(doc.vgb_thue_theo_mau,0);
 console.log('PASS: 5/8%, sửa giá phản hồi muộn, thêm món, nhiều mức, hộp hỏi cũ.');
})().catch(e=>{console.error(e);process.exitCode=1;});

/* Hợp đồng Frappe được giả lập; chạy nguyên script desktop, không sao chép phép lọc. */
const fs = require('fs'), vm = require('vm'), assert = require('assert');
class El {
  constructor(text='') { this.label=text; this.children=[]; this.handlers={}; this.attrs={}; }
  prependTo(p) { p.children.unshift(this); return this; }
  appendTo(p) { p.children.push(this); return this; }
  empty() { this.children=[]; return this; }
  css() { return this; }
  text(t) { this.label=t; return this; }
  attr(k,v) { this.attrs[k]=v; return this; }
  toggleClass() { return this; }
  on(k,fn) { this.handlers[k]=fn; return this; }
}
const counts=[], alerts=[];
let prior=0;
const frappe={listview_settings:{BOM:{add_fields:['is_default'],get_indicator:()=>['v002'],refresh:()=>prior++}},
  utils:{escape_html:s=>s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;")},
  db:{count:(dt,args)=>{counts.push([dt,args.filters]);return Promise.resolve(42);}},
  datetime:{get_today:()=> '2026-09-08',add_days:(d,n)=>new Date(Date.parse(d)+n*86400000).toISOString().slice(0,10)},
  msgprint:m=>alerts.push(m)};
const ctx={frappe,$:x=>new El(x)};
vm.runInNewContext(fs.readFileSync('vagabond/public/js/san_xuat_list.js','utf8'),ctx);
function makeList(dt,filters=[]) {
  const lv={doctype:dt,page:{main:new El()},start:40};
  lv.filter_area={get:()=>filters,clear:async()=>{filters=[];},add:async f=>{filters=f;},trigger_refresh:true};
  lv.refresh=async()=>frappe.listview_settings[dt].refresh(lv);
  return lv;
}
function buttons(el) { return [el,...el.children.flatMap(buttons)].filter(e=>e.handlers.click); }
const settle=()=>new Promise(r=>setImmediate(r));
(async()=>{
  const mon = frappe.listview_settings['Work Order'].formatters.production_item;
  const df = {fieldname:'production_item', fieldtype:'Link', options:'Item'};
  const doc = {production_item:'BAWC00132', item_name:'Bánh Ổ Meraki, size 18cm'};
  // Frappe 16.27.1 list_view.js get_subject_text giữ nguyên formatter Link;
  // get_link_element gán vào textContent và title, không diễn giải HTML.
  const text = mon(doc.production_item, df, doc);
  assert.strictEqual(text, 'Bánh Ổ Meraki, size 18cm (BAWC00132)');
  assert(!text.includes('<'), 'subject không được sinh thẻ HTML');
  assert.strictEqual(mon('Tên được truyền làm title', df, doc), text, 'mã lấy từ document');
  assert.strictEqual(mon('NVL001', df, {}), 'NVL001', 'thiếu tên thì hiện mã một lần');
  assert.strictEqual(mon('NVL001', df, {item_name:'NVL001'}), 'NVL001');
  assert.strictEqual(mon('NVL001', df, {item_name:'Bánh "A" & B'}), 'Bánh "A" & B (NVL001)', 'textContent không cần HTML entities');
  const wo=makeList('Work Order', [['Work Order','company','=','TV'],['Work Order','status','!=','Stopped']]);
  await wo.refresh(); await settle();
  assert(counts.every(c=>c[1].some(f=>f[1]==='company')),'count phải giữ company');
  let b=buttons(wo.page.main).find(b=>b.label.startsWith('Đã xong'));
  b.handlers.click(); await settle();
  assert(wo.filter_area.get().some(f=>f[1]==='company'),'giữ company sau click');
  assert(wo.filter_area.get().some(f=>f[1]==='status' && f[3]==='Completed'));
  assert.strictEqual(wo.start,0);
  assert.strictEqual(buttons(wo.page.main).find(b=>b.label.startsWith('Đã xong')).attrs['aria-pressed'],'true');
  b=buttons(wo.page.main).find(b=>b.label==='Hôm nay'); b.handlers.click(); await settle();
  assert(wo.filter_area.get().some(f=>f[1]==='planned_start_date' && f[3]==='2026-09-09 00:00:00'));
  assert(wo.filter_area.get().some(f=>f[1]==='status' && f[3]==='Completed'));
  b=buttons(wo.page.main).find(b=>b.label.startsWith('Tất cả trạng thái')); b.handlers.click(); await settle();
  assert(!wo.filter_area.get().some(f=>f[1]==='status' || f[1]==='docstatus'));
  assert(wo.filter_area.get().some(f=>f[1]==='planned_start_date'));
  b=buttons(wo.page.main).find(b=>b.label.startsWith('Đã đóng')); b.handlers.click(); await settle();
  assert(wo.filter_area.get().some(f=>f[1]==='status' && f[3]==='Closed'));
  const bom=makeList('BOM'); await bom.refresh(); assert(prior===1);
  assert.deepStrictEqual(frappe.listview_settings.BOM.get_indicator(),['v002']);
  await wo.refresh(); assert.strictEqual(wo.page.main.children.length,1,'không nhân thanh lọc');
  frappe.db.count=()=>Promise.reject(Error('network')); await wo.refresh(); await settle();
  assert(buttons(wo.page.main).some(b=>b.label.includes('(?)')),'lỗi không hiện 0');
  const app=fs.readFileSync('vagabond/public/js/bep/05-san-xuat.js','utf8');
  const fn=app.slice(app.indexOf('function mfgNguonCua'),app.indexOf('function mfgWhCard'));
  const state={mfg:{src:'Baker'}}; vm.runInNewContext(fn,state);
  assert.strictEqual(state.mfgNguonCua({kho_mac_dinh:'Pastry'}),'Pastry');
  assert.strictEqual(state.mfgNguonCua({}),'Baker');
  state.mfg.nguon_tay=1;
  assert.strictEqual(state.mfgNguonCua({kho_mac_dinh:'Pastry'}),'Baker');
  assert.strictEqual(state.mfgNguonCua({src:'Kho rieng',kho_mac_dinh:'Pastry'}),'Kho rieng');
  const saved = new Map();
  Object.assign(state, {localStorage: {getItem: k=>saved.get(k), setItem:(k,v)=>saved.set(k,v)},
    S:{wh:['Baker','Pastry']}, mfgKey:()=>'', mfgQuanLy:()=>true, whFind:()=>''});
  vm.runInNewContext(app.slice(app.indexOf('function mfgInitWh'),app.indexOf('function mfgShift')), state);
  state.mfgSaveWh();
  state.mfg={}; state.mfgInitWh();
  assert.strictEqual(state.mfg.nguon_tay,1,'mở lại giữ kho chọn tay');
  assert.strictEqual(state.mfgNguonCua({kho_mac_dinh:'Pastry'}),'Baker');
  state.mfg.nguon_tay=0; state.mfgSaveWh();
  state.mfg={}; state.mfgInitWh();
  assert.strictEqual(state.mfgNguonCua({kho_mac_dinh:'Pastry'}),'Pastry','mở lại giữ chế độ theo Món');
  state.mfg.src='Kho đã tắt'; state.mfg.nguon_tay=1; state.mfgSaveWh();
  state.mfg={}; state.mfgInitWh();
  assert.strictEqual(state.mfg.nguon_tay,0,'kho không còn hợp lệ thì bỏ chế độ ép kho chung');
  assert.strictEqual(alerts.length,0);
  console.log('PASS: chip counts/filter/state/errors, preserve BOM, item/default/manual warehouse');
})().catch(e=>{console.error(e);process.exitCode=1;});

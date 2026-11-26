/* v693: nhịp đọc số trang đặt bánh (web_vue/banh/nhip-doc.js) chạy thật bằng node với
   đồng hồ và trạng thái tab giả. Chạy: node vagabond/khung/kiem_thu/hanh_vi/nhip_doc_693.mjs */
import {nhipDoc, MOI_HIEN} from '../../../public/web_vue/banh/nhip-doc.js';

let dat = 0, hong = 0; const loi = [];
async function ca(ten, f) { try { await f(); dat++; } catch (e) { hong++; loi.push(ten + ': ' + e.message); } }
function la(t, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(t + ' được ' + JSON.stringify(a) + ' cần ' + JSON.stringify(b)); }
const xong = () => new Promise(r => setTimeout(r, 0));

function moi() {
  const s = {t: 0, an: false, goi: 0, cho: []};
  const doc = () => { s.goi++; return new Promise(r => s.cho.push(r)); };
  const n = nhipDoc(doc, 60000, {bay: () => s.t, an: () => s.an});
  const tra = async () => { s.cho.splice(0).forEach(r => r()); await xong(); };
  return {s, n, tra};
}

await ca('đang có lượt chưa xong thì không gửi thêm', async () => {
  const {s, n, tra} = moi();
  const a = n.chay(), b = n.chay(); la('cùng một lượt', a === b, true);
  s.t = 70000; n.nhip(); n.hien(); await xong(); la('một lượt duy nhất', s.goi, 1);
  await tra(); n.nhip(); await xong(); la('xong rồi, đã cũ: đọc tiếp', s.goi, 2);
});
await ca('nhịp chỉ đọc khi số cũ từ một chu kỳ', async () => {
  const {s, n, tra} = moi();
  n.chay(); await xong(); await tra();
  s.t = 59999; n.nhip(); await xong(); la('chưa đủ chu kỳ', s.goi, 1);
  s.t = 60000; n.nhip(); await xong(); la('đủ chu kỳ', s.goi, 2);
});
await ca('tab ẩn không đọc; hiện lại đọc ngay một lượt, sự kiện lặp không gửi trùng', async () => {
  const {s, n, tra} = moi();
  n.chay(); await xong(); await tra();
  s.an = true; for (let t = 0; t <= 600000; t += 5000) { s.t = t; n.nhip(); }
  await xong(); la('ẩn mười phút', s.goi, 1);
  s.an = false; n.hien(); n.hien(); await xong(); la('hiện lại: một lượt', s.goi, 2);
  await tra(); s.t += 1000; n.hien(); await xong(); la('vừa đọc dưới ' + MOI_HIEN + ' ms: không đọc lại', s.goi, 2);
  s.t += 30000; n.nhip(); await xong(); la('nhịp kế chưa đủ chu kỳ', s.goi, 2);
});
await ca('lượt đọc lỗi vẫn nhả để lượt sau chạy', async () => {
  let goi = 0; const s = {t: 0};
  const n = nhipDoc(() => { goi++; return Promise.reject(new Error('mạng')); }, 60000, {bay: () => s.t, an: () => false});
  await n.chay().catch(() => {}); s.t = 60000; n.nhip(); await xong();
  la('đọc lại sau lỗi', goi, 2);
});

console.log(dat + ' ca dat, ' + hong + ' ca hong');
for (const x of loi) console.log('  HONG ' + x);
process.exit(hong ? 1 : 0);

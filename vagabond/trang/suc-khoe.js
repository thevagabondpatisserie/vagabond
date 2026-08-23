
frappe.ready(function(){ chay(); setInterval(chay, 60000); });
var PHUT = 60 * 1000;
// Nguong coi la "dung": qua 3 lan chu ky ma chua chay lai.
var JOBS = [
  { ten: 'Kéo hoá đơn m-invoice', script: 'MInvoice Daily Pull', phut: 15 },
  { ten: 'Tạo chứng từ từ m-invoice', script: 'MInvoice Make Docs Cron', phut: 5 },
  { ten: 'Đồng bộ SePay theo giờ', script: 'SePay - Dong bo giao dich (hang gio)', phut: 60 },
  { ten: 'Trạng thái gửi email đơn mua', script: 'PO - Dong bo trang thai gui email', phut: 5 },
  { ten: 'Trạng thái cung ứng phiếu yêu cầu', script: 'MR - Dong bo trang thai cung ung', phut: 5 },
  { ten: 'Tên người lập chứng từ', script: 'Dong bo ten nguoi lap', phut: 5 }
];

function h_(s){ return String(s == null ? '' : s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
function pill(mau, chu){ return '<span class="pill ' + mau + '">' + h_(chu) + '</span>'; }

async function ds(dt, filters, fields){
  try {
    var r = await frappe.call({ method: 'frappe.client.get_list',
      args: { doctype: dt, filters: filters || [], fields: fields || ['name'], limit_page_length: 0 } });
    return (r && r.message) || [];
  } catch(e){ return []; }
}

async function chay(){
  var el = document.getElementById('noi_dung');
  if (!el) return;

  var jobs = await ds('Scheduled Job Type', [['server_script','!=','']], ['server_script','last_execution','stopped']);
  var bang = {};
  jobs.forEach(function(j){ bang[j.server_script] = j; });

  var bay_gio = new Date();
  var hang = JOBS.map(function(c){
    var j = bang[c.script];
    if (!j) return '<tr><td>' + h_(c.ten) + '</td><td>' + pill('do','Không tìm thấy') + '</td><td></td><td></td></tr>';
    var lan = j.last_execution ? new Date(String(j.last_execution).replace(' ','T')) : null;
    var phut = lan ? Math.round((bay_gio - lan) / PHUT) : null;
    var mau = 'xanh', chu = 'Đang chạy';
    if (j.stopped) { mau = 'xam'; chu = 'Đã tắt'; }
    else if (phut === null) { mau = 'cam'; chu = 'Chưa chạy lần nào'; }
    else if (phut > c.phut * 3) { mau = 'do'; chu = 'Đứng ' + phut + ' phút'; }
    else if (phut > c.phut * 2) { mau = 'cam'; chu = 'Chậm ' + phut + ' phút'; }
    return '<tr><td>' + h_(c.ten) + '</td><td>' + pill(mau, chu) + '</td><td>' + h_(j.last_execution || '-').slice(0,19) + '</td><td>mỗi ' + c.phut + ' phút</td></tr>';
  }).join('');

  var ket = await ds('MInvoice Invoice', [['ly_do_bo_qua','!=','']], ['name','loai','so_hd','ly_do_bo_qua']);
  // Chi dem dong co ngay lap. Dong khong co ngay lap khong bao gio vao hang doi.
  var chua_chay = await ds('MInvoice Invoice', [['da_tao_chung_tu','=',0],['ngay_lap','is','set']], ['name']);
  var pi_nhap = await ds('Purchase Invoice', [['docstatus','=',0]], ['name']);
  var bt_cho = await ds('Bank Transaction', [['status','=','Unreconciled']], ['name']);
  var po_chua = await ds('Purchase Order', [['docstatus','=',1],['trang_thai_gui_email','=','Chưa gửi']], ['name']);
  var mr_cho = await ds('Material Request', [['docstatus','=',1],['trang_thai_cung_ung','=','Chờ mua']], ['name']);

  var sepay = {};
  try { var s = await frappe.call({ method: 'frappe.client.get', args: { doctype: 'SePay Settings', name: 'SePay Settings' } }); sepay = (s && s.message) || {}; } catch(e){}

  var the = [
    ['Hoá đơn m-invoice đang kẹt', ket.length, ket.length ? 'do' : 'xanh'],
    ['Hoá đơn m-invoice chờ xử lý', chua_chay.length, chua_chay.length > 100 ? 'cam' : 'xanh'],
    ['Hoá đơn mua còn Nháp', pi_nhap.length, pi_nhap.length > 50 ? 'cam' : 'xanh'],
    ['Giao dịch ngân hàng chưa đối chiếu', bt_cho.length, bt_cho.length > 200 ? 'cam' : 'xanh'],
    ['Đơn mua chưa gửi email NCC', po_chua.length, po_chua.length > 10 ? 'cam' : 'xanh'],
    ['Phiếu yêu cầu còn chờ mua', mr_cho.length, 'xam']
  ].map(function(x){
    return '<div class="the ' + x[2] + '"><div class="so">' + x[1] + '</div><div class="nhan">' + h_(x[0]) + '</div></div>';
  }).join('');

  var nhom = {};
  ket.forEach(function(k){
    var l = String(k.ly_do_bo_qua).slice(0, 90);
    if (!nhom[l]) nhom[l] = [];
    nhom[l].push(k.loai + ' ' + k.so_hd);
  });
  var ly_do = Object.keys(nhom).map(function(l){
    return '<tr><td>' + h_(l) + '</td><td>' + nhom[l].length + '</td><td class="nho">' + h_(nhom[l].slice(0,6).join(', ')) + '</td></tr>';
  }).join('') || '<tr><td colspan="3">Không có hoá đơn nào kẹt.</td></tr>';

  el.innerHTML =
    '<div class="the_hang">' + the + '</div>' +
    '<h3>Việc chạy nền</h3>' +
    '<table><thead><tr><th>Việc</th><th>Tình trạng</th><th>Lần chạy gần nhất</th><th>Chu kỳ</th></tr></thead><tbody>' + hang + '</tbody></table>' +
    '<h3>Hoá đơn m-invoice đang kẹt, gộp theo lý do</h3>' +
    '<table><thead><tr><th>Lý do</th><th>Số hoá đơn</th><th>Vài hoá đơn đầu</th></tr></thead><tbody>' + ly_do + '</tbody></table>' +
    '<h3>SePay</h3>' +
    '<table><tbody><tr><td>Lần đồng bộ gần nhất</td><td>' + h_(sepay.last_sync || '-') + '</td></tr>' +
    '<tr><td>Kết quả lần cuối</td><td>' + h_(sepay.last_error || '-') + '</td></tr></tbody></table>' +
    '<div class="nho" style="margin-top:14px">Cập nhật lúc ' + new Date().toLocaleTimeString('vi-VN') + ', tự làm mới mỗi phút.</div>';
}

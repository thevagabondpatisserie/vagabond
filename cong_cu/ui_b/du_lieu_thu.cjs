/* Máy chủ GIẢ cho máy chụp: trả dữ liệu thử có kiểm soát cho từng lời gọi /api/.
 * Tên người, món, số tiền là dữ liệu bịa cho việc chụp, không lấy từ site thật.
 * Trả undefined nghĩa là "chưa có dữ liệu thử": máy chụp ghi lại tên để bổ sung. */
'use strict';
var ghiDe = {};
var VAI = {
  'quan-tri': ['System Manager', 'Giám đốc', 'Accounts Manager', 'Accounts User', 'Stock Manager', 'Stock User', 'Sales User', 'Sales Manager',
    'Purchase User', 'Purchase Manager', 'Manufacturing User', 'Manufacturing Manager', 'Quản lý cửa hàng', 'Quầy', 'Bếp', 'Kho', 'Marketing', 'AP Giám đốc'],
  'quay': ['Quầy', 'Sales User', 'Stock User'],
  'bep': ['Bếp', 'Manufacturing User', 'Stock User']
};
exports.dat = function (o) { ghiDe = o || {}; };
exports.tra = function (duong, than, vai) {
  var m = duong.replace('/api/method/', '');
  if (m in ghiDe) return typeof ghiDe[m] === 'function' ? ghiDe[m](than) : ghiDe[m];
  if (m === 'frappe.auth.get_logged_user') return { message: 'thu.nghiem@vagabond.thu' };
  if (m === 'vagabond.nhan_su.khoi_dong') return { message: {
    kho: ['Kho Tổng - TV', 'Bếp Pastry - TV', 'Cửa hàng Trần Cao Vân - TV'],
    nhom: [{ name: 'Thành phẩm Bánh', parent_item_group: 'Bán ra', is_group: 0, custom_bep_phu_trach: 'Bếp Pastry' }],
    vai: VAI[vai] || VAI['quan-tri'],
    toi: { full_name: 'Nguyễn Thử Nghiệm', bo_phan: 'Quản lý' }, quyen_nen: null } };
  if (m === 'frappe.client.get_list' || m === 'frappe.client.get_count' || m === 'vagabond.tim_kiem.tim') {
    if (m === 'frappe.client.get_count') return { message: 0 };
    var dt = than.doctype;
    if (dt === 'Material Request') {
      var loai = '';
      try { loai = (typeof than.filters === 'string' ? JSON.parse(than.filters) : than.filters || {}).material_request_type; } catch (e) { }
      var n = loai === 'Purchase' ? 3 : loai === 'Material Transfer' ? 2 : 12;
      var ds = []; for (var i = 0; i < n; i++) ds.push({ name: 'YC-' + i });
      return { message: ds };
    }
    if (dt === 'Payment Entry') return { message: [{ name: 'APP-1', party_type: 'Supplier' }, { name: 'APP-2', party_type: 'Supplier' }] };
    return { message: [] };
  }
  if (m === 'frappe.client.get' || m === 'frappe.client.get_value') return { message: {} };
  if (m === 'vagabond.khung.ds.danh_ba') return { message: [
    { ma: 'DMSP', ten: 'Sản phẩm' }, { ma: 'DMNCC', ten: 'Nhà cung cấp' }, { ma: 'DMKH', ten: 'Khách hàng' }, { ma: 'DMKHO', ten: 'Kho' }] };
  if (m === 'vagabond.viec_can_lam.danh_sach') return { message: { ds: [], tong: 0 } };
  if (m === 'vagabond.viec_tu_dong.ds') return { message: { viec: [], nhat_ky: [], duoc_sua: 1 } };
  return undefined;
};

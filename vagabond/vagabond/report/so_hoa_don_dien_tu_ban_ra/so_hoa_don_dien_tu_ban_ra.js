/* v536: sổ hoá đơn điện tử bán ra, mỗi tờ m-invoice một dòng, có mã khách kế toán. */
frappe.query_reports["So hoa don dien tu ban ra"] = {
 filters: [
  {fieldname:"tu_ngay",label:__("Từ ngày lập"),fieldtype:"Date",default:frappe.datetime.month_start(),reqd:1},
  {fieldname:"den_ngay",label:__("Đến ngày lập"),fieldtype:"Date",default:frappe.datetime.get_today(),reqd:1},
  {fieldname:"so_hd",label:__("Số hoá đơn"),fieldtype:"Data"},
  {fieldname:"ky_hieu",label:__("Ký hiệu"),fieldtype:"Data"},
  {fieldname:"nguoi_mua",label:__("Tên người mua hoặc MST"),fieldtype:"Data"},
  {fieldname:"ma_khach",label:__("Mã khách kế toán"),fieldtype:"Data"},
  {fieldname:"trang_thai",label:__("Trạng thái"),fieldtype:"Select",options:"\nGốc\nThay thế\nBị thay thế\nĐiều chỉnh\nBị điều chỉnh\nĐã huỷ"},
  {fieldname:"chi_chua_noi",label:__("Chỉ tờ chưa nối đơn ERP"),fieldtype:"Check",default:0}
 ]
};

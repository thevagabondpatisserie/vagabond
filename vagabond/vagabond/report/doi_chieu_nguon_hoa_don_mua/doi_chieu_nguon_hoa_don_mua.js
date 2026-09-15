frappe.query_reports["Doi chieu nguon hoa don mua"] = {
 filters: [
  {fieldname:"hoa_don",label:__("Hoá đơn mua"),fieldtype:"Link",options:"Purchase Invoice"},
  {fieldname:"from_date",label:__("Từ ngày"),fieldtype:"Date",default:frappe.datetime.month_start(),reqd:1},
  {fieldname:"to_date",label:__("Đến ngày"),fieldtype:"Date",default:frappe.datetime.get_today(),reqd:1},
  {fieldname:"page",label:__("Trang (100 hoá đơn/trang)"),fieldtype:"Int",default:1,reqd:1}
 ]
};

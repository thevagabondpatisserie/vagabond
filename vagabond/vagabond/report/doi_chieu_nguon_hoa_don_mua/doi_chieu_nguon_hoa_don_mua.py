"""Báo cáo chỉ đọc theo quyền Purchase Invoice; không ghi Comment hoặc sửa phiếu."""
from html import escape


def gom_ly_do(loi):
	chu = list(dict.fromkeys(loi))
	text = "<br>".join(escape(x) for x in chu[:5])
	if len(chu) > 5:
		text += "<br>Còn %s mục cần kiểm trên chứng từ." % (len(chu) - 5)
	return text


import frappe
from frappe.utils import cint, getdate
from vagabond.luong_hoa_don_goc import doc_canh_bao


def execute(filters=None):
	f = filters or {}
	if not f.get("hoa_don"):
		if not f.get("from_date") or not f.get("to_date"):
			frappe.throw("Chọn khoảng ngày cần kiểm tra.")
		a, b = getdate(f["from_date"]), getdate(f["to_date"])
		if a > b:
			frappe.throw("Từ ngày không được sau Đến ngày.")
	page = max(1, cint(f.get("page")) or 1)
	# get_list giữ quyền chứng từ/công ty của người đọc. Phân trang trước
	# chạy resolver; không gọi toàn bộ lịch sử trong một request.
	query = {"docstatus": ["<", 2], "is_return": 0, "custom_minvoice_id": ["is", "set"]}
	if f.get("hoa_don"):
		query["name"] = f["hoa_don"]
	else:
		query["posting_date"] = ["between", [a, b]]
	ds = frappe.get_list("Purchase Invoice", filters=query,
		fields=["name", "posting_date", "supplier"], order_by="posting_date asc, name asc",
		limit_start=(page-1)*100, limit_page_length=101)
	rows = []
	for p in ds[:100]:
		loi = doc_canh_bao(frappe.get_doc("Purchase Invoice", p.name))
		for group in ("nhan_dien", "nguon", "luong"):
			chu = list(dict.fromkeys(x["chu"] for x in loi if x["nhom"] == group))
			if chu:
				rows.append(dict(hoa_don=p.name, ngay=p.posting_date, nha_cung_cap=p.supplier,
					nhom={"nhan_dien":"Tên/mã nguồn", "nguon":"Chưa kiểm được nguồn", "luong":"Lượng/quy cách"}[group],
					ly_do=gom_ly_do(chu)))
	columns = [dict(fieldname="hoa_don", label="Hoá đơn mua",fieldtype="Link",options="Purchase Invoice",width=180),
		dict(fieldname="ngay",label="Ngày",fieldtype="Date",width=100),
		dict(fieldname="nha_cung_cap",label="Nhà cung cấp",fieldtype="Link",options="Supplier",width=220),
		dict(fieldname="nhom",label="Cần kiểm",fieldtype="Data",width=180),
		dict(fieldname="ly_do",label="Chi tiết",fieldtype="Small Text",width=450)]
	message = ("Lọc theo mã hoá đơn, không giới hạn ngày. " if f.get("hoa_don") else "")
	message += "Đã kiểm %s hoá đơn ở trang %s. " % (min(len(ds),100), page)
	message += "Còn dữ liệu: tăng số Trang để xem tiếp. " if len(ds)>100 else "Đã tới cuối khoảng ngày. "
	message += "Chưa nhận diện tên/mã không có nghĩa lượng hoặc giá sai. Bấm hoá đơn để đối chiếu bản gốc và ánh xạ NCC; báo cáo không sửa hoặc chặn ghi sổ."
	return columns, rows, message

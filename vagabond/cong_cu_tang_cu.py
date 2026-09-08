"""#225: Frappe Cloud không có bench execute, kế toán cần cửa Desk có quyền.

Chỉ mở đúng cặp đã chốt trong doi_chieu_tang_cu. Không nhận mã phiếu/số
 tiền từ client. HTTP POST dùng giao dịch/CSRF của Frappe, không commit
riêng; mọi kiểm tra hash, GL/PLE và rollback ở hàm lõi giữ nguyên.
"""
import frappe


def _quyen():
	if frappe.session.user == "Guest" or not ({"Accounts Manager", "System Manager"} & set(frappe.get_roles())):
		frappe.throw("Chỉ kế toán trưởng hoặc quản trị được xử lý PKT hàng tặng cũ.", frappe.PermissionError)


@frappe.whitelist(methods=["GET", "POST"])
def xem():
	_quyen()
	from vagabond.doi_chieu_tang_cu import ban_xem
	return ban_xem()


@frappe.whitelist(methods=["POST"])
def thay(ma_xac_nhan):
	_quyen()
	from vagabond.doi_chieu_tang_cu import thay as thuc_hien
	kq = thuc_hien(ma_xac_nhan)
	# Commit là của HTTP request Frappe sau khi hàm thành công, không phải
	# một thao tác tiếp theo người dùng phải tự biết chạy trong console.
	kq.pop("chua_commit", None)
	return dict(kq, ok=1)

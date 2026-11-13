"""v655: đối chiếu lại MỘT lần các nguồn Tiền bán từ 01/10/2026 còn dòng chưa nối.

Đo trên site 13/11/2026: 41 nguồn (Xanh SM 15, ShopeeFood 6, OnePay 14, Grab 3,
Shinhan 3) kẹt dòng chưa nối. Xanh SM DSN-2611-06762 có 8 dòng Lệch tiền vì
nguồn được đối chiếu trước luật so tiền sàn v648; OnePay chưa nối theo số đơn
Pancake (v655). Lượt mỗi giờ chỉ nhìn 30 ngày, nên phần từ 01/10 chạy một lần.

Chỉ đổi TRẠNG THÁI đối soát (bảng dòng và nguồn đối soát), không tạo hay sửa
chứng từ kế toán (anh Việt đồng ý 13/11/2026). Chạy trong hàng đợi nền sau khi
migrate xong, để migrate không chờ, và vì đối chiếu có thể gửi tin Zalo lệch
tiền về (một lần mỗi đợt, theo luật sẵn có)."""

TU_NGAY = "2026-10-01"


def execute():
	import frappe

	if not frappe.db.table_exists("Vagabond Doi Soat Nguon"):
		return
	frappe.enqueue("vagabond.doi_soat_vendor.doi_chieu_lai_dong", queue="long", timeout=3000,
		tu_ngay=TU_NGAY, toi_da=1000, enqueue_after_commit=True)

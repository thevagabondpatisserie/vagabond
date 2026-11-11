"""v649: trừ một lần BTP sẵn và Đủ decor cho số Bếp làm đã nhập TRƯỚC khi lên bản v649.

Từ v649 bếp nhập ô Bếp làm là trừ BTP sẵn, Đủ decor ngay (theo phần chênh so với bản
đang lưu), còn chốt sổ thôi trừ theo số bán. Bảng Kiểm bánh chưa chốt mà bếp đã nhập
Bếp làm dưới bản cũ thì phần đó chưa trừ, và sẽ không bao giờ trừ: lần lưu sau chênh 0,
chốt sổ không trừ nữa. Còn nhận hôm nay lại đã bớt đơn theo số Bếp làm, nên web nhận
quá số vỏ thật (Codex #552 vòng 6).

Bản vá này trừ đúng phần đó, một lần, ngay sau khi đồng bộ cấu trúc (cần cột phần Đủ
decor đã trừ). Chỉ lấy bảng CHƯA CHỐT của hôm nay và hôm qua: bảng đã chốt thì bản cũ
đã trừ theo số bán lúc chốt; bảng chưa chốt cũ hơn là bảng bỏ quên, trừ vào tủ hôm nay
sẽ sai nên chỉ in ra để người phụ trách xem. Frappe ghi Patch Log nên không chạy lại.
"""

LUI_NGAY = 1


def can_tru(bang, hom_nay):
	"""THUẦN: (tên bảng cần trừ, tên bảng chưa chốt cũ hơn để báo) từ danh sách
	{name, ngay, tinh_trang}. `ngay`, `hom_nay` là date."""
	import datetime

	moc = hom_nay - datetime.timedelta(days=LUI_NGAY)
	tru, cu = [], []
	for b in bang or []:
		if (b.get("tinh_trang") or "") == "Da chot":
			continue
		(tru if b.get("ngay") and b["ngay"] >= moc else cu).append(b["name"])
	return sorted(tru), sorted(cu)


def execute():
	import frappe
	from frappe.utils import getdate, nowdate

	from vagabond import btp

	bang = [dict(b, ngay=getdate(b.get("ngay")) if b.get("ngay") else None)
		for b in frappe.get_all("Kiem Banh Ngay", fields=["name", "ngay", "tinh_trang"])]
	tru, cu = can_tru(bang, getdate(nowdate()))
	for ten in tru:
		doc = frappe.get_doc("Kiem Banh Ngay", ten)
		btp.tru_vo_theo_sx(btp.chenh_sx([], doc.dong))
	if cu:
		print("v649: bảng Kiểm bánh chưa chốt cũ hơn hôm qua, không trừ BTP: " + ", ".join(cu))

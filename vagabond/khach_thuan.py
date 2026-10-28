# -*- coding: utf-8 -*-
"""Phép THUẦN của màn Danh sách khách hàng (v617). Không chạm Frappe, không
kéo thư viện mạng, để bộ kiểm tầng khung gọi thẳng.

Vì sao có tệp này (anh Việt 28/10/2026, ảnh màn Danh sách khách hàng):
màn ghi "Khách · chi nhiều nhất lên đầu" và "Chi tiêu 12 tháng" nhưng máy chủ
chỉ lấy 400 khách ĐẦU BẢNG CHỮ CÁI (tên bắt đầu bằng số, chữ A) rồi mới xếp
theo tiền. Khách chi nhiều nhất mà tên bắt đầu bằng chữ T thì không bao giờ
hiện, và số "Chi tiêu 12 tháng" chỉ là tổng của 400 người đó. Nay xếp và cộng
ngay trong câu truy vấn, trên ĐỦ nhóm đang lọc.
"""

# Chi tiêu = hoá đơn đã ghi sổ trong 12 tháng (bỏ hoá đơn đánh dấu huỷ) cộng
# mốc chi tiêu cũ bên Fabi (anh Việt 12/08/2026: khách giữ công sức đã tiêu
# bên hệ cũ). Một nguồn cho cả cột tiền, thứ tự và dòng tổng.
CHI_TIEU_12_THANG = (
	"(select customer, sum(grand_total) tien, count(*) so_don, max(posting_date) gan_nhat "
	"from `tabSales Invoice` where docstatus = 1 and posting_date >= %(tu)s "
	"and ifnull(vgb_huy, 0) = 0 group by customer)"
)

SO_DONG_TOI_DA = 200


def dk_ds_khach(nhom_si, dang="", hang="", ten_khop=None, co_hang=True):
	"""Mệnh đề where và tham số cho danh sách khách, hoặc None khi chắc chắn rỗng.

	nhom_si: các nhóm khách được coi là khách sỉ. dang: "si" | "le" | "".
	hang: mã hạng, "_chua" (chưa xếp hạng) hoặc "". ten_khop: None khi không
	tìm; danh sách mã khách khớp chữ tìm khi có tìm (rỗng là không ai khớp).
	co_hang: site đã có cột hạng chưa (chưa có thì lọc hạng coi như chưa ai có).
	"""
	nhom_si = tuple(nhom_si or ())
	dk, ts = ["ifnull(c.disabled, 0) = 0"], {}
	if dang == "si":
		if not nhom_si:
			return None
		dk.append("c.customer_group in %(nhom_si)s")
		ts["nhom_si"] = nhom_si
	elif dang == "le" and nhom_si:
		dk.append("ifnull(c.customer_group, '') not in %(nhom_si)s")
		ts["nhom_si"] = nhom_si
	if hang == "_chua":
		if co_hang:
			dk.append("ifnull(c.vgb_hang, '') = ''")
	elif hang:
		if not co_hang:
			return None
		dk.append("c.vgb_hang = %(hang)s")
		ts["hang"] = hang
	if ten_khop is not None:
		ten_khop = tuple(x for x in ten_khop if x)
		if not ten_khop:
			return None
		dk.append("c.name in %(ten)s")
		ts["ten"] = ten_khop
	return " and ".join(dk), ts


def cau_ds_khach(where, co_hang=True, co_tieu_cu=True, so_dong=SO_DONG_TOI_DA, dem_si=False):
	"""Hai câu SQL: danh sách xếp theo chi tiêu giảm dần, và dòng tổng của cả nhóm
	(số khách, tổng chi tiêu, số khách sỉ khi dem_si: tham số %(nhom_si_dem)s)."""
	tieu_cu = "ifnull(c.vgb_chi_tieu_cu, 0)" if co_tieu_cu else "0"
	cot_hang = "ifnull(c.vgb_hang, '')" if co_hang else "''"
	tu = "from `tabCustomer` c left join %s s on s.customer = c.name where %s" % (CHI_TIEU_12_THANG, where)
	ds = (
		"select c.name, c.customer_name, c.customer_group, c.tax_id, c.mobile_no, "
		"%s hang, %s tieu_cu, ifnull(s.tien, 0) tien_erp, ifnull(s.so_don, 0) so_don, s.gan_nhat "
		"%s order by (ifnull(s.tien, 0) + %s) desc, c.customer_name asc limit %d"
	) % (cot_hang, tieu_cu, tu, tieu_cu, int(so_dong))
	tong = (
		"select count(*) n, sum(ifnull(s.tien, 0) + %s) tien, %s si %s"
	) % (tieu_cu, "sum(c.customer_group in %(nhom_si_dem)s)" if dem_si else "0", tu)
	return ds, tong


def dong_khach(r, la_si, giam_cua_hang):
	"""Một dòng trả về màn từ một dòng SQL. la_si(nhom) -> bool."""
	tieu_cu = float(r.get("tieu_cu") or 0)
	tien_erp = float(r.get("tien_erp") or 0)
	h = r.get("hang") or ""
	return {
		"ma": r.get("name"),
		"ten": r.get("customer_name") or r.get("name"),
		"nhom": r.get("customer_group") or "",
		"si": 1 if la_si(r.get("customer_group")) else 0,
		"mst": r.get("tax_id") or "",
		"dt": r.get("mobile_no") or "",
		"hang": h,
		"giam": float(giam_cua_hang.get(h) or 0),
		"tien": tien_erp + tieu_cu,
		"tien_erp": tien_erp,
		"tieu_cu": tieu_cu,
		"so_don": int(r.get("so_don") or 0),
		"gan_nhat": str(r.get("gan_nhat") or ""),
	}

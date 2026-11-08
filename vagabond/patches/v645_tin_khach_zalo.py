"""v645: bật tin cảm ơn khi khách nhận đơn, giờ gửi 8:00 tới 20:00, và tích tin báo
cáo ưu đãi tuần cho nhóm Marketing.

Anh Việt 08/11/2026: "Em bật tin báo điểm và cảm ơn sau mua đi (sau mua định
nghĩa là các đơn chuyển trạng thái đã nhận, và không gửi sau 8PM)". Đây là tin
chăm sóc (Zalo tag 2): không có ưu đãi, không cần khách đồng ý quảng cáo, và là
điều kiện để Zalo cho gửi tin ưu đãi (khách phải từng nhận tin chăm sóc trong 6
tháng, hạn mức tin ưu đãi bằng 1/6 số tin chăm sóc hai tháng trước).

Bật từ LÚC chạy bản vá (bat_luc = bây giờ): không gửi bù đơn cũ. Mẫu Zalo chưa
duyệt thì máy tự giữ tin chờ và màn Tin Zalo tự động nói rõ vì sao.

Nhóm đã tích "Bánh mới chờ ảnh trên web" (nhóm Marketing, v644) được tích thêm
tin báo cáo ưu đãi tuần. Nhóm để trống Tin nhận đang nhận mọi tin. Chạy lại không
đổi gì (lũy đẳng): kịch bản đã bật thì không đổi lúc bật.
"""

THEO_MOC = (("mkt_banh_cho_anh", "mkt_bao_cao_uu_dai"),)


def _tach(chuoi):
	return [m.strip() for m in str(chuoi or "").replace(";", ",").split(",") if m.strip()]


def tin_them(tin_nhan):
	"""THUẦN: chuỗi Tin nhận mới của một nhóm, None nếu không đổi."""
	cu = _tach(tin_nhan)
	if not cu:
		return None
	moi = list(cu)
	for moc, ma in THEO_MOC:
		if moc in cu and ma not in moi:
			moi.append(ma)
	return ", ".join(moi) if moi != cu else None


def gia_tri_bat(cu, luc):
	"""THUẦN: các ô cần ghi để bật tin cảm ơn, {} nếu đã đúng (lũy đẳng)."""
	from vagabond.zalo_kich_ban import gio_hop_le

	v = {}
	if not int((cu or {}).get("bat") or 0):
		v["bat"] = 1
		v["bat_luc"] = luc
	tu, den = gio_hop_le((cu or {}).get("gio_tu"), (cu or {}).get("gio_den"))
	if (tu, den) != ((cu or {}).get("gio_tu"), (cu or {}).get("gio_den")):
		v["gio_tu"], v["gio_den"] = tu, den
	return v


def execute():
	import frappe
	from vagabond import kenh_zalo, zalo_kich_ban as zk

	la = sorted({ma for _, ma in THEO_MOC} - set(kenh_zalo.TIN))
	if la:
		raise Exception("v645_tin_khach_zalo: mã tin không có trong kenh_zalo.TIN: %s" % ", ".join(la))
	zk._dam_bao()
	for kb in zk.KICH_BAN:
		# Mọi kịch bản đã có: kẹp giờ về 20:00 (luật mới của anh), chỉ bật tin cảm ơn.
		cu = zk._cau_hinh(kb["ma"]) or {}
		v = gia_tri_bat(cu, zk._bay_gio()) if kb["ma"] == "sau_mua" else {}
		if kb["ma"] != "sau_mua":
			tu, den = zk.gio_hop_le(cu.get("gio_tu"), cu.get("gio_den"))
			if (tu, den) != (cu.get("gio_tu"), cu.get("gio_den")):
				v = {"gio_tu": tu, "gio_den": den}
		if v:
			frappe.db.set_value(zk.DT_KB, kb["ma"], v, update_modified=False)
	if frappe.db.has_column("Vagabond Kenh Zalo", "tin_nhan"):
		rows = frappe.get_all("Vagabond Kenh Zalo",
			filters={"parenttype": "Vagabond Settings", "parentfield": "zalo_nhom"},
			fields=["name", "tin_nhan"], order_by="idx asc", limit_page_length=0)
		for r in rows:
			moi = tin_them(r.get("tin_nhan"))
			if moi:
				frappe.db.set_value("Vagabond Kenh Zalo", r["name"], "tin_nhan", moi, update_modified=False)
	frappe.db.commit()
	frappe.clear_cache(doctype="Vagabond Settings")

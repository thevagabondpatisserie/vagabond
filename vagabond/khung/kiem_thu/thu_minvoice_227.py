"""#227: tái hiện rò email qua tìm kiếm và giữ ghi chú trên payload thật."""

import ast
import json
from pathlib import Path
from types import SimpleNamespace

from vagabond import minvoice_an_toan as at, minvoice_kich_ban as kb
from vagabond.khung.kiem_thu.nen import ca, la, dung


def goi():
	return {"data": [{"inv_buyerEmail": "khach-khac@example.com", "inv_TotalAmount": 1900000,
		"inv_TotalAmountWithoutVat": 1759259, "inv_vatAmount": 140741,
		"details": [{"data": [{"inv_itemName": "HỘP MOONGARDEN", "inv_TotalAmount": 1900000}]}]}]}


@ca("#227: khách lẻ không mang email hay địa chỉ lạc ra M-Invoice")
def _khach_le():
	for ten in (None, "", "Bán cho người tiêu dùng", "Ban cho nguoi tieu dung", "Khách lẻ"):
		kq = at.chuan_goi({"name": "SI-227", "vgb_xhd_ten": ten,
			"vgb_xhd_email": "khac@example.com", "vgb_xhd_dia_chi": "Địa chỉ: sai"}, goi())["data"][0]
		la("không gửi email", kq["inv_buyerEmail"], "")
		la("không gửi địa chỉ lạc", kq["inv_buyerAddressLine"], "")
		la("khoá riêng SI", kq["key_api"], "SI-227")


@ca("#227: giữ email riêng đã xác nhận, để trống không bù người khác")
def _email_rieng():
	for mail in ("", "ketoan@example.com"):
		kq = at.chuan_goi({"name": "SI-227", "vgb_xhd_ten": "Nguyễn Văn A", "vgb_xhd_email": mail,
			"vgb_xhd_dia_chi": "- Địa chỉ: 123 đường A"}, goi())["data"][0]
		la("đúng email của phiếu", kq["inv_buyerEmail"], mail)
		la("bóc nhãn ở cửa cuối", kq["inv_buyerAddressLine"], "123 đường A")


@ca("#227: mọi dòng hàng tặng có ghi chú, không xoá căn cứ tính VAT")
def _qua():
	si = {"name": "SI-227", "vgb_pt_thanh_toan": "Hàng tặng", "vgb_tang_duyet": "Đã duyệt"}
	for them in ({}, {"vgb_pt_thanh_toan": "", "vgb_phieu_qua": "QUA-227"}):
		kq = at.chuan_goi(dict(si, **them), goi())["data"][0]
		dung("tên gửi thật có ghi chú", "Hàng biếu tặng không thu tiền" in kq["details"][0]["data"][0]["inv_itemName"])
		la("VAT vẫn đúng", (kq["inv_TotalAmountWithoutVat"], kq["inv_vatAmount"], kq["inv_TotalAmount"]), (1759259, 140741, 1900000))
		la("chạy hai lần không nối đôi", at.chuan_goi(dict(si, **them), {"data": [kq]})["data"][0], kq)
	la("không làm bẩn payload gốc", goi()["data"][0]["details"][0]["data"][0]["inv_itemName"], "HỘP MOONGARDEN")


@ca("#227: chưa duyệt, thiếu tên pháp nhân và email hỏng bị chặn")
def _chan():
	for si in ({"vgb_pt_thanh_toan": "Hàng tặng"}, {"vgb_xhd_mst": "0311234567"},
		{"vgb_xhd_ten": "Nguyễn Văn A", "vgb_xhd_email": "a@example.com,b@example.com"}):
		try:
			at.chuan_goi(si, goi())
		except ValueError:
			continue
		dung("phải chặn dữ liệu không rõ", False)


@ca("#227: ID M-Invoice đủ để chặn gửi lại dù chưa có số")
def _da_gui():
	for o in ("custom_hddt_so", "custom_hddt_id", "custom_minvoice_id"):
		dung("chặn theo " + o, at.da_gui({o: "ma-227"}))
	dung("chặn chờ ký", at.da_gui({"custom_hddt_trang_thai": "Chờ ký"}))
	la("phiếu chưa gửi", at.da_gui({}), False)


@ca("#227: mã đơn rỗng không đọc portal, mã trùng không lấy người đầu")
def _portal():
	p = Path(__file__).resolve().parents[2] / "ban_hang.py"
	cay = ast.parse(p.read_text())
	ham = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "_yeu_cau_xhd_dung_don")
	goi_doc = []
	def nem(cau):
		raise ValueError(cau)
	nen = {"frappe": SimpleNamespace(get_all=lambda *a, **kw: goi_doc.append(kw) or [], throw=nem)}
	exec(compile(ast.Module(body=[ham], type_ignores=[]), str(p), "exec"), nen)
	for ma in (None, "", "  "):
		la("không có yêu cầu", nen[ham.name](ma), None)
	la("không query mã rỗng", goi_doc, [])
	nen["frappe"].get_all = lambda *a, **kw: [{"name": "A"}, {"name": "B"}]
	try:
		nen[ham.name]("227")
	except ValueError:
		return
	dung("trùng mã phải báo", False)


@ca("#227: patch script dừng khi đoạn gốc đổi, không ghi đè người khác")
def _patch_lech():
	for sua in (kb.sua_nap, kb.sua_phat_hanh):
		try:
			sua("ma da doi")
		except ValueError:
			continue
		dung("script đổi phải dừng", False)
	la("patch có mốc chạy lại giữ nguyên", kb.sua_nap(kb.MOC + "\npass"), kb.MOC + "\npass")


def ban_goc(loai):
	return (Path(__file__).parent / "du_lieu" / ("minvoice_" + loai + "_20260907.txt")).read_text()


class To(SimpleNamespace):
	def get(self, o, mac_dinh=None):
		return getattr(self, o, mac_dinh)

	def db_set(self, o, gia_tri, **_):
		setattr(self, o, gia_tri)

	def reload(self):
		return self

	def get_password(self, *_, **__):
		return "mat-khau-thu"


def nen_script(si):
	st = To(pancake_shop_id="shop-thu", api2_base="https://minvoice.invalid", api2_username="thu",
		username="thu", ma_dvcs="VP", thue_suat=8, ma_hang_gop="", ky_hieu="THU",
		buyer_name="Bán cho người tiêu dùng", tong_da_day=0)
	return To(form_dict={"phieu": si.name, "che_do": "day", "khong_commit": 1}, response={},
		utils=To(cint=lambda x: int(x or 0), flt=lambda x: float(x or 0), now=lambda: "2026-09-07", today=lambda: "2026-09-07"),
		db=To(commit=lambda: None, exists=lambda *a: True),
		get_doc=lambda dt, *a, **kw: si if dt == "Sales Invoice" else (To(execute_method=lambda: None) if dt == "Server Script" else st))


@ca("#227: chạy snapshot thật tái hiện lấy nhầm kết quả tìm đầu tiên, bản vá không ghi")
def _tim_nham():
	for sua in (False, True):
		si = To(name="SI-227", custom_pancake_display_id="227", custom_pancake_id="ID-227")
		f = nen_script(si)
		f.make_get_request = lambda *a, **kw: {"data": [{"id": "ID-1227", "display_id": 1227,
			"note_print": "Tên công ty: Công ty người khác\nEmail: khac@example.com"}]}
		ma = ban_goc("nap")
		exec(compile(kb.sua_nap(ma) if sua else ma, "nap-live", "exec"), {"frappe": f})
		la("bản cũ tái hiện/bản mới không ghi email lạc", si.get("vgb_xhd_email"), None if sua else "khac@example.com")


@ca("#227: nạp đúng mã vẫn giữ email người mua đã xác nhận và bỏ mail ghi chú chung")
def _nap_dung():
	for ten, ghi_chu, mong in (("Bán cho người tiêu dùng", "Email: rieng@example.com", None),
		("Nguyễn Văn A", "Tên công ty: Công ty B\nEmail: b@example.com", None),
		("", "Tên công ty: Công ty B\nEmail: b@example.com", "b@example.com")):
		si = To(name="SI-227", custom_pancake_display_id="227", custom_pancake_id="ID-227", vgb_xhd_ten=ten)
		f = nen_script(si)
		f.make_get_request = lambda *a, **kw: {"data": [{"id": "ID-227", "display_id": 227, "note_print": ghi_chu}]}
		exec(compile(kb.sua_nap(ban_goc("nap")), "nap-live", "exec"), {"frappe": f})
		la("email sau nạp", si.get("vgb_xhd_email"), mong)


@ca("#227: chạy toàn bộ script phát hành đã vá qua success, reject, timeout và xem thử")
def _gui_script():
	for che_do, ket_qua in (("day", "ok"), ("day", "loi"), ("day", "timeout"), ("thu", "ok")):
		si = To(name="SI-227", docstatus=1, grand_total=1900000, posting_date="2026-09-07",
			vgb_xhd_ten="Bán cho người tiêu dùng", vgb_xhd_email="lac@example.com",
			vgb_pt_thanh_toan="Hàng tặng", vgb_tang_duyet="Đã duyệt",
			items=[To(amount=1900000, qty=2, item_code="BANH", item_name="HỘP MOONGARDEN", uom="Hộp")])
		f = nen_script(si)
		f.form_dict["che_do"] = che_do
		gui = []
		def kiem(_ten, phieu, goi, giu_cho):
			ra = at.chuan_goi(si, goi)
			if giu_cho:
				si.vgb_hddt_cho_doi_chieu = 1
			return ra
		f.call = kiem
		def post(url, data, **kw):
			if url.endswith("Login"):
				return {"token": "token-thu"}
			gui.append(json.loads(data))
			if ket_qua == "timeout":
				raise TimeoutError("chưa biết kết quả")
			return {"code": "00", "data": {"inv_invoiceAuth_id": "ID-MINV", "inv_invoiceNumber": "227"}} if ket_qua == "ok" else {"code": "296"}
		f.make_post_request = post
		exec(compile(kb.sua_phat_hanh(ban_goc("phat_hanh")), "phat-hanh-live", "exec"), {"frappe": f, "json": json})
		la("xem thử không gửi", len(gui), 0 if che_do == "thu" else 1)
		dd = gui[0]["data"][0] if gui else f.response["message"]["mau"]["data"][0]
		la("payload thật bỏ email lạc", dd["inv_buyerEmail"], "")
		dung("payload thật có ghi chú quà", "không thu tiền" in dd["details"][0]["data"][0]["inv_itemName"])
		la("giữ dấu khi chưa chắc kết quả", si.get("vgb_hddt_cho_doi_chieu", 0), 1 if che_do == "day" and ket_qua != "ok" else 0)
		la("ghi đúng ID khi thành công", si.get("custom_minvoice_id"), "ID-MINV" if che_do == "day" and ket_qua == "ok" else None)


@ca("#227: nạp trả lỗi trong response thì phát hành phải dừng, không gọi Save")
def _nap_loi_khong_gui():
	for loi in ("Không tìm được duy nhất đơn Pancake khớp", "HTTP timeout"):
		si = To(name="SI-227", docstatus=1, grand_total=1900000)
		f = nen_script(si)
		goc = f.get_doc
		f.get_doc = lambda dt, *a, **kw: To(execute_method=lambda: f.response.update(message={"loi": [loi]})) if dt == "Server Script" else goc(dt, *a, **kw)
		gui = []
		f.make_post_request = lambda url, **kw: {"token": "thu"} if url.endswith("Login") else gui.append(url)
		exec(compile(kb.sua_phat_hanh(ban_goc("phat_hanh")), "phat-hanh-live", "exec"), {"frappe": f, "json": json})
		la("không Save khi nạp lỗi", gui, [])
		dung("báo lỗi để kế toán xử lý", bool(f.response["message"]["loi"]))


@ca("#227: mở lại bắt buộc quyền, lý do, xác nhận và không có ID đã nhận")
def _mo_lai():
	goc = at.frappe
	try:
		vet, doi = [], []
		si = To(name="SI-227", vgb_hddt_cho_doi_chieu=1, add_comment=lambda *a: vet.append(a))
		def nem(cau):
			raise ValueError(cau)
		at.frappe = To(get_roles=lambda: ["Sales User"], throw=nem, get_doc=lambda *a, **kw: si,
			db=To(set_value=lambda *a, **kw: doi.append(a)))
		for vai, ly_do, xac_nhan, ma in (("Sales User", "Đã kiểm theo mã SI-227", 1, None),
			("Accounts Manager", "ngắn", 1, None), ("Accounts Manager", "Đã kiểm theo mã SI-227", 0, None),
			("Accounts Manager", "Đã kiểm theo mã SI-227", 1, "DA-GUI")):
			at.frappe.get_roles = lambda: [vai]
			si.custom_minvoice_id = ma
			try:
				at.mo_lai(si.name, ly_do, xac_nhan)
			except ValueError:
				continue
			dung("thiếu điều kiện phải chặn", False)
		la("chưa có lần mở nào", doi, [])
		si.custom_minvoice_id = None
		at.mo_lai(si.name, "Kế toán đã kiểm đúng mã SI-227, không có hoá đơn", 1)
		la("chỉ mở cờ sau xác nhận", len(doi), 1)
		la("có dấu vết người thao tác qua Comment", len(vet), 1)
	finally:
		at.frappe = goc

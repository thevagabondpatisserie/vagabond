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


@ca("#227: patch script dừng khi đoạn gốc đổi, mốc cũ không được bỏ qua sửa mới")
def _patch_lech():
	for sua in (kb.sua_nap, kb.sua_phat_hanh):
		for ma in ("ma da doi", kb.MOC_V446 + "\npass", kb.MOC + "\npass"):
			try:
				sua(ma)
			except ValueError:
				continue
			dung("script đổi hoặc đã vá phải dừng, không vá chồng: " + ma[:20], False)


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

	def add_comment(self, *a):
		self.vet = getattr(self, "vet", []) + [a]


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
		don_khac = {"id": "ID-1227", "display_id": 1227, "note_print": "Tên công ty: Công ty người khác\nEmail: khac@example.com"}
		# Bản cũ chỉ tìm gần đúng page_size 1 nên gặp đơn 1227; bản mới có ID thì tra đúng ID.
		f.make_get_request = lambda url, **kw: {"data": don_khac} if url.endswith("/ID-227") else {"data": [don_khac]}
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
		don = {"id": "ID-227", "display_id": 227, "note_print": ghi_chu}
		f.make_get_request = lambda url, **kw: {"data": don} if url.endswith("/ID-227") else {"data": [don]}
		exec(compile(kb.sua_nap(ban_goc("nap")), "nap-live", "exec"), {"frappe": f})
		la("email sau nạp", si.get("vgb_xhd_email"), mong)


@ca("#227: chạy toàn bộ script phát hành đã vá: tạo, từ chối rõ, timeout, mã lạ, trùng, thiếu dữ liệu, xem thử")
def _gui_script():
	PH = {
		"ok": {"code": "00", "ok": True, "data": {"inv_invoiceAuth_id": "ID-MINV", "inv_invoiceNumber": "227"}},
		"loi": {"code": "296", "ok": False, "message": "Create invoice fail"},
		"timeout": None,
		"ma_la": {"code": "99", "ok": False, "message": "Loi khac"},
		"trung": {"code": "296", "ok": False, "message": "Hoa don da ton tai voi key_api"},
		"thieu": {"code": "00", "ok": True, "data": None},
		"rong": {},
	}
	for che_do, ket_qua in (("day", "ok"), ("day", "loi"), ("day", "timeout"), ("day", "ma_la"),
		("day", "trung"), ("day", "thieu"), ("day", "rong"), ("thu", "ok")):
		si = To(name="SI-227", docstatus=1, grand_total=1900000, posting_date="2026-09-07",
			vgb_xhd_ten="Bán cho người tiêu dùng", vgb_xhd_email="lac@example.com",
			vgb_pt_thanh_toan="Hàng tặng", vgb_tang_duyet="Đã duyệt",
			items=[To(amount=1900000, qty=2, item_code="BANH", item_name="HỘP MOONGARDEN", uom="Hộp")])
		f = nen_script(si)
		f.form_dict["che_do"] = che_do
		f.form_dict["khong_commit"] = 0
		gui = []
		commit = []
		f.db.commit = lambda: commit.append(1)
		def goi(ten, **kw):
			if ten.endswith("kiem_goi"):
				ra = at.chuan_goi(si, kw["goi"])
				if kw["giu_cho"]:
					si.vgb_hddt_cho_doi_chieu = 1
				return ra
			la("script dùng đúng cửa phân loại chung", ten, "vagabond.minvoice_an_toan.phan_loai_phan_hoi")
			return at.phan_loai_phan_hoi_thuan(kw.get("phan_hoi"), kw.get("loi"))
		f.call = goi
		def post(url, data, **kw):
			if url.endswith("Login"):
				return {"token": "token-thu"}
			gui.append(json.loads(data))
			if ket_qua == "timeout":
				raise TimeoutError("chưa biết kết quả")
			return PH[ket_qua]
		f.make_post_request = post
		exec(compile(kb.sua_phat_hanh(ban_goc("phat_hanh")), "phat-hanh-live", "exec"), {"frappe": f, "json": json})
		nhan = che_do + "/" + ket_qua
		la("xem thử không gửi " + nhan, len(gui), 0 if che_do == "thu" else 1)
		dd = gui[0]["data"][0] if gui else f.response["message"]["mau"]["data"][0]
		la("payload thật bỏ email lạc", dd["inv_buyerEmail"], "")
		dung("payload thật có ghi chú quà", "không thu tiền" in dd["details"][0]["data"][0]["inv_itemName"])
		giu = 1 if (che_do == "day" and ket_qua not in ("ok", "loi")) else 0
		la("cờ sau gửi " + nhan, si.get("vgb_hddt_cho_doi_chieu", 0), giu)
		la("ghi ID khi thành công " + nhan, si.get("custom_minvoice_id"), "ID-MINV" if che_do == "day" and ket_qua == "ok" else None)
		if che_do == "day" and ket_qua == "loi":
			la("từ chối rõ có vết Comment", len(si.get("vet", [])), 1)
			la("từ chối rõ commit ngay sau khi gỡ cờ, rồi commit cuối script", len(commit), 2)
			dung("báo cho kế toán biết đã mở lại", "mo lai" in f.response["message"]["loi"][0])
		elif che_do == "day":
			la("chỉ commit cuối script " + nhan, len(commit), 1)
		if giu:
			dung("không rõ thì nói rõ giữ đối chiếu " + nhan, "giu doi chieu" in f.response["message"]["loi"][0])


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


# ---------------------------------------------------------------- bổ sung 08/09/2026 theo review Codex PR #228

@ca("#227 v447: phân loại phản hồi Save theo bằng chứng thật, không coi mọi lỗi là chưa tạo")
def _phan_loai():
	bang = (
		({"code": "00", "ok": True, "data": {"inv_invoiceAuth_id": "A1", "inv_invoiceNumber": 10}}, None, "tao", "A1"),
		({"code": "296", "ok": False, "message": "Create invoice fail"}, None, "tu_choi", ""),
		({"code": "296"}, None, "tu_choi", ""),
		({"code": "296", "ok": True, "message": "Create invoice fail"}, None, "khong_ro", ""),
		({"code": "296", "ok": False, "message": "Hoa don da ton tai"}, None, "khong_ro", ""),
		({"code": "296", "ok": False, "message": "Duplicate key_api"}, None, "khong_ro", ""),
		({"code": "99", "ok": False, "message": "Loi"}, None, "khong_ro", ""),
		({"code": "00", "ok": True, "data": None}, None, "khong_ro", ""),
		({"code": "00", "ok": True}, None, "khong_ro", ""),
		({"code": "01", "data": {"inv_invoiceAuth_id": "A2"}}, None, "khong_ro", "A2"),
		({"ok": False, "message": "khong co ma"}, None, "khong_ro", ""),
		({}, None, "khong_ro", ""),
		(None, None, "khong_ro", ""),
		("<html>502</html>", None, "khong_ro", ""),
		([{"code": "00"}], None, "khong_ro", ""),
		({"code": "00", "ok": True, "data": {"inv_invoiceAuth_id": "A3"}}, TimeoutError("timeout"), "khong_ro", ""),
		(None, "Read timed out", "khong_ro", ""),
		# Codex tái hiện 08/09 (mẫu giả để kiểm độ bền, KHÔNG phải phản hồi thật):
		# data sai cấu trúc hoặc mang dấu vết chứng từ thì không được mở khoá.
		({"code": "296", "data": [{"inv_invoiceAuth_id": "DA-TAO"}]}, None, "khong_ro", ""),
		({"code": "296", "data": {"inv_invoiceNumber": "123"}}, None, "khong_ro", ""),
		({"code": "296", "data": {"sobaomat": "AB12"}}, None, "khong_ro", ""),
		({"code": "296", "data": [[{"key_api": "SI-1"}]]}, None, "khong_ro", ""),
		({"code": "296", "data": {}}, None, "khong_ro", ""),
		({"code": "296", "data": []}, None, "khong_ro", ""),
		({"code": "296", "data": "x"}, None, "khong_ro", ""),
		({"code": "296", "ok": False, "message": "Create invoice fail", "them": 1}, None, "khong_ro", ""),
		({"code": "296", "ok": True, "message": "Create invoice fail"}, None, "khong_ro", ""),
		({"code": "296", "message": {"inv_invoiceNumber": 5}}, None, "khong_ro", ""),
		({"code": "296", "message": ["Create invoice fail"]}, None, "khong_ro", ""),
		({"code": "296", "ok": False, "message": "Create invoice fail", "data": None}, None, "tu_choi", ""),
	)
	for ph, loi, mong, ma_hd in bang:
		kq = at.phan_loai_phan_hoi_thuan(ph, loi)
		la("loại của %r/%r" % (ph, loi), kq["loai"], mong)
		la("id của %r" % (ph,), kq["id"], ma_hd)
		dung("câu báo không rỗng", bool(kq["cau"]))
	la("cửa whitelist nhận chuỗi JSON", at.phan_loai_phan_hoi('{"code": "296"}')["loai"], "tu_choi")
	la("cửa whitelist nhận dict", at.phan_loai_phan_hoi({"code": "00", "data": {"inv_invoiceAuth_id": "A"}})["loai"], "tao")
	la("cửa whitelist nhận chuỗi hỏng", at.phan_loai_phan_hoi("khong phai json")["loai"], "khong_ro")
	la("bảng mã từ chối vẫn chỉ có 296 (không thêm khi chưa có phản hồi thật)", at.MA_TU_CHOI_RO, {"296"})


@ca("#227 v447: kịch bản nạp không giới hạn một kết quả, đối chiếu mã đơn và ID, có phân trang")
def _nap_khong_gioi_han():
	def don(ma, pid=None, ghi_chu="Tên công ty: Công ty %s\nMST: 0311234567\nEmail: %s@example.com", khong_display=False):
		# Pancake của tiệm (đo 08/09/2026): display_id null, id chính là mã đơn.
		return {"id": (pid if pid is not None else (ma if khong_display else "ID-" + str(ma))),
			"display_id": None if khong_display else ma, "note_print": ghi_chu % (ma, ma)}
	# (SI có ID?, các trang tìm kiếm, bản tra theo ID, email mong đợi, có lỗi?)
	trang_day = [don(1000 + i) for i in range(50)]
	ca_kiem = (
		("khong_id", [[don(1227), don(227)]], None, "227@example.com", False),
		("khong_id_trang_2", [trang_day, [don(1227), don(227)]], None, "227@example.com", False),
		("khong_id_khong_thay", [[don(1227), don(2227)]], None, None, True),
		("khong_id_trung_ma", [[don(227, "ID-A"), don(227, "ID-B")]], None, None, True),
		("khong_id_qua_5_trang", [trang_day] * 6, None, None, True),
		# Codex tái hiện 08/09: trang 1 có A/227, trang 6 có B/227, các trang đều đầy.
		# Chưa đọc hết thì không được kết luận duy nhất, không ghi người mua.
		("khong_id_khop_trang_1_nhung_trang_5_day", [[don(227, "ID-A")] + trang_day[:49]] + [trang_day] * 4 + [[don(227, "ID-B", "Tên công ty: Công ty B %s\nMST: 0399999999\nEmail: b%s@example.com")]], None, None, True),
		("khong_id_khop_trang_1_trang_5_ngan", [[don(227, "ID-A")] + trang_day[:49]] + [trang_day] * 3 + [trang_day[:10]], None, "227@example.com", False),
		("khong_id_khop_trang_5_ngan", [trang_day] * 4 + [[don(227)]], None, "227@example.com", False),
		# Đo trên site 08/09/2026: Pancake không trả display_id, id là số và là mã đơn.
		("co_id_that_khong_display", [[don(93310, 93310, khong_display=True)]], {"id": 93310, "display_id": None, "note_print": "Tên công ty: Công ty 227\nMST: 0311234567\nEmail: 227@example.com"}, "227@example.com", False),
		("co_id_that_lech_ma", [[]], {"id": 93311, "display_id": None, "note_print": "Email: x@example.com"}, None, True),
		("khong_id_that_khong_display", [[don(1227, 1227, khong_display=True), don(227, 227, khong_display=True)]], None, "227@example.com", False),
		# total_pages Pancake trả về là dấu hết: 5 trang đầy nhưng total_pages 5 -> đã hết, nạp được.
		("khong_id_total_pages_5", [([don(227, "ID-A")] + trang_day[:49])] + [trang_day] * 4 + [[don(227, "ID-B")]], "TP5", "227@example.com", False),
		# total_pages 6 mà chỉ đọc được 5 -> chưa hết, không ghi.
		("khong_id_total_pages_6", [([don(227, "ID-A")] + trang_day[:49])] + [trang_day] * 4 + [[don(227, "ID-B")]], "TP6", None, True),
		("co_id", [[don(1227)]], don(227), "227@example.com", False),
		("co_id_lech_ma", [[don(227)]], don(1227, "ID-227"), None, True),
		("co_id_khong_co", [[don(227)]], {}, None, True),
	)
	for ten, cac_trang, theo_id, mail_mong, co_loi in ca_kiem:
		tong_trang = {"TP5": 5, "TP6": 6}.get(theo_id) if isinstance(theo_id, str) else None
		if tong_trang:
			theo_id = None
		that = "_that" in ten
		pid = ("93310" if that else "ID-227") if ten.startswith("co_id") else ""
		si = To(name="SI-227", custom_pancake_display_id="93310" if (that and pid) else "227", custom_pancake_id=pid)
		f = nen_script(si)
		goi = []
		def get(url, params=None, **kw):
			goi.append((url.rsplit("/", 1)[1] if (pid and url.endswith("/" + pid)) else "tim", dict(params or {})))
			if pid and url.endswith("/" + pid):
				return {"data": theo_id}
			so = int(params.get("page_number") or 1)
			ra = {"data": cac_trang[so - 1] if so <= len(cac_trang) else []}
			if tong_trang:
				ra["total_pages"] = tong_trang
				ra["total_entries"] = tong_trang * 50
			return ra
		f.make_get_request = get
		exec(compile(kb.sua_nap(ban_goc("nap")), "nap-live", "exec"), {"frappe": f})
		la("email " + ten, si.get("vgb_xhd_email"), mail_mong)
		la("có lỗi báo kế toán " + ten, bool(f.response["message"]["loi"]), co_loi)
		if ten.startswith("co_id"):
			la("có ID thì tra đúng ID, không tìm gần đúng " + ten, [g[0] for g in goi], [pid])
		else:
			dung("không ID thì tìm theo trang 50 " + ten, all(g[1].get("page_size") == 50 and g[1].get("search") == si.custom_pancake_display_id for g in goi))
			la("số trang đã duyệt " + ten, len(goi), min(len(cac_trang), 5) if ten not in ("khong_id", "khong_id_that_khong_display") else 1)
			if "trang_5_day" in ten or "qua_5_trang" in ten:
				dung("chạm trần phân trang thì nói rõ chưa hết kết quả " + ten, any("chưa hết kết quả" in x for x in f.response["message"]["loi"]))
				la("không ghi tên/MST người mua " + ten, (si.get("vgb_xhd_ten"), si.get("vgb_xhd_mst")), (None, None))


@ca("#227 v447: snapshot đối chiếu bằng độ dài và FNV, vá luôn từ bản gốc, sha256 nhận đúng ba bản")
def _snapshot_va_doi_chieu():
	for loai in ("nap", "phat_hanh"):
		goc = kb.ban_goc(loai)
		la("FNV snapshot " + loai, (len(goc), kb.fnv1a(goc)), kb.FNV_GOC[loai])
		cu = kb._sua_nap_v446(goc) if loai == "nap" else kb._sua_phat_hanh_v446(goc)
		moi = kb.ban_moi(loai)
		la("nhận bản gốc", kb.doi_chieu(loai, goc), "goc")
		la("nhận bản vá v446", kb.doi_chieu(loai, cu), "v446")
		la("nhận bản vá hiện tại", kb.doi_chieu(loai, moi), "moi")
		la("bản khác dù cùng độ dài thì không nhận", kb.doi_chieu(loai, goc[:-1] + ("x" if goc[-1] != "x" else "y")), None)
		la("bản có mốc cũ nhưng sửa thêm thì không nhận", kb.doi_chieu(loai, cu + "\n# sua tay"), None)
		for ma_bam, nhan in kb.BAM_BAN_CU.get(loai, {}).items():
			dung("mã băm bản cũ đúng dạng sha256 " + nhan, len(ma_bam) == 64 and ma_bam != kb.bam(moi))
		dung("bản mới khác bản v446", moi != cu)
		dung("bản mới mang mốc v447", moi.startswith(kb.MOC))
		dung("bản v446 không chứa sửa mới", "phan_loai_phan_hoi" not in cu if loai == "phat_hanh" else "page_number" not in cu)
	kb_goc = kb.FNV_GOC["nap"]
	try:
		kb.FNV_GOC["nap"] = (1, 1)
		try:
			kb.ban_goc("nap")
			dung("snapshot lệch phải dừng", False)
		except ValueError:
			pass
	finally:
		kb.FNV_GOC["nap"] = kb_goc


@ca("#227 v447: dong_bo vá bản gốc lẫn bench đã chạy v446, không đụng bản đã đúng, dừng khi lạ")
def _dong_bo():
	goc_frappe = None
	import sys
	goc_frappe = sys.modules.get("frappe")
	luu = []
	def nem(cau):
		raise ValueError(cau)
	class Doc(To):
		def save(self, **kw):
			luu.append(self.name)
	for tinh_huong, mong_luu, mong_dung in (("goc", ["nap", "phat_hanh"], False), ("v446", ["nap", "phat_hanh"], False),
		("moi", [], False), ("la", [], True), ("thieu", [], True)):
		luu[:] = []
		docs = {}
		for ten, loai, cu, sua in kb.BO:
			goc = kb.ban_goc(loai)
			ma = {"goc": goc, "v446": cu(goc), "moi": sua(goc), "la": goc + "\n# ai do sua tay", "thieu": goc}[tinh_huong]
			docs[ten] = Doc(name=loai, script=ma)
		f = To(db=To(exists=lambda dt, ten: tinh_huong != "thieu"), throw=nem, get_doc=lambda dt, ten: docs[ten])
		sys.modules["frappe"] = f
		try:
			try:
				kb.dong_bo()
				dung("phải dừng ở tình huống " + tinh_huong, not mong_dung)
			except ValueError:
				dung("không được dừng ở tình huống " + tinh_huong, mong_dung)
		finally:
			sys.modules["frappe"] = goc_frappe
		la("bản được lưu ở " + tinh_huong, luu, mong_luu)
		if mong_luu:
			for ten, loai, cu, sua in kb.BO:
				la("nội dung lưu đúng bản mới " + loai, docs[ten].script, kb.ban_moi(loai))
	# Chạy hai lần liên tiếp không lưu thêm gì.


@ca("#227 v447: từ chối rõ thì gỡ cờ và commit trước khi ném lỗi; có ID thì không gỡ")
def _go_co_tu_choi():
	goc = at.frappe
	try:
		for ma_co in (None, "DA-CO-ID"):
			thu_tu = []
			si = To(name="SI-227", vgb_hddt_cho_doi_chieu=1, custom_minvoice_id=ma_co, add_comment=lambda *a: thu_tu.append("comment"))
			at.frappe = To(flags=To(vagabond_kiem_that=0), get_doc=lambda *a, **kw: si, throw=lambda c: (_ for _ in ()).throw(ValueError(c)),
				db=To(set_value=lambda *a, **kw: thu_tu.append(("set", a[3])), commit=lambda: thu_tu.append("commit")))
			at.go_co_sau_tu_choi("SI-227", "296 Create invoice fail")
			if ma_co:
				la("đã có ID thì không gỡ cờ, không ghi vết", thu_tu, ["commit"])
			else:
				la("gỡ cờ rồi commit, có vết Comment", thu_tu, ["comment", ("set", 0), "commit"])
		at.frappe = To(flags=To(vagabond_kiem_that=1), throw=lambda c: (_ for _ in ()).throw(ValueError(c)))
		try:
			at.go_co_sau_tu_choi("SI-227", "x")
			dung("bộ kiểm tích hợp không được gỡ cờ thật", False)
		except ValueError:
			pass
	finally:
		at.frappe = goc


@ca("#227 v447: đường Python xuất HĐĐT dùng cùng quy tắc phân loại, gỡ cờ trước khi ném lỗi từ chối")
def _duong_python():
	p = Path(__file__).resolve().parents[2] / "ban_hang.py"
	cay = ast.parse(p.read_text())
	ham = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "xuat_hoa_don_dien_tu")
	goi = [ast.unparse(n.func) for n in ast.walk(ham) if isinstance(n, ast.Call)]
	dung("phân loại bằng quy tắc chung", "minvoice_an_toan.phan_loai_phan_hoi_thuan" in goi)
	dung("từ chối rõ gỡ cờ qua go_co_sau_tu_choi", "minvoice_an_toan.go_co_sau_tu_choi" in goi)
	than = ast.unparse(ham)
	dung("không còn coi thiếu ok là lỗi chưa tạo", 'j.get("ok")' not in than and "j.get('ok')" not in than)
	# Thứ tự trong nguồn: gỡ cờ (kèm commit bên trong) đứng trước throw của nhánh từ chối.
	vi_tri_go = than.index("go_co_sau_tu_choi")
	vi_tri_nem = than.index("frappe.throw", vi_tri_go)
	dung("gỡ cờ trước rồi mới ném lỗi", vi_tri_go < vi_tri_nem)
	# Đây là dò chuỗi (quy tắc 16): chứng minh thật nằm ở khung/bench_thu/giao_dich_that_227 trên bench.


@ca("#225: nạp tay và lô bỏ qua nguồn ngoài Pancake trước HTTP, không đổi dữ liệu")
def _nguon_khong_pancake():
	for nguon in ("Tại chỗ", "GrabFood", "ShopeeFood", "Khách sỉ"):
		for theo_lo in (False, True):
			si = To(name="SI-NGUON", custom_nguon=nguon,
				custom_pancake_display_id="TAICHO-123", custom_pancake_id="ID-123",
				vgb_xhd_ten="Tên đã xác nhận", vgb_xhd_email="dung@example.com")
			truoc = dict(vars(si))
			f = nen_script(si)
			f.form_dict["ghi_de"] = 1
			if theo_lo:
				f.form_dict.pop("phieu")
				f.get_all = lambda *a, **kw: [{"name": si.name}]
			goi_http = []
			f.make_get_request = lambda *a, **kw: goi_http.append(a) or {"data": []}
			exec(compile(kb.ban_moi("nap"), "nap-nguon", "exec"), {"frappe": f})
			la("không tra Pancake " + nguon, goi_http, [])
			la("không ghi dữ liệu " + nguon, vars(si), truoc)
			la("không báo lỗi tìm đơn " + nguon, f.response["message"]["loi"], [])


@ca("#225: nguồn Pancake và phiếu cũ thiếu nguồn vẫn kiểm đúng ID, không bỏ qua lỗi")
def _nguon_pancake_van_kiem():
	for nguon in ("Pancake", "", None):
		si = To(name="SI-PK", custom_nguon=nguon,
			custom_pancake_display_id="123", custom_pancake_id="ID-123")
		f = nen_script(si)
		goi_http = []
		f.make_get_request = lambda *a, **kw: goi_http.append(a) or {"data": {"id": "SAI"}}
		exec(compile(kb.ban_moi("nap"), "nap-nguon", "exec"), {"frappe": f})
		la("vẫn tra đúng ID", len(goi_http), 1)
		dung("vẫn báo không khớp", bool(f.response["message"]["loi"]))


@ca("#225: xuất rải chạy cả hai script, nguồn tại quầy tới Save giả lập không tra Pancake")
def _xuat_nguon_khac():
	for nguon in ("Tại chỗ", "GrabFood"):
		si = To(name="SI-QUAY", docstatus=1, custom_nguon=nguon,
			custom_pancake_display_id="TAICHO-123", grand_total=108000,
			posting_date="2026-09-08", vgb_xhd_ten="Người mua đã xác nhận",
			vgb_xhd_email="dung@example.com",
			items=[To(amount=108000, qty=1, item_code="BANH", item_name="Bánh", uom="Hộp")])
		f = nen_script(si)
		goc = f.get_doc
		def nap():
			exec(compile(kb.ban_moi("nap"), "nap-quay", "exec"), {"frappe": f})
		f.get_doc = lambda dt, *a, **kw: To(execute_method=nap) if dt == "Server Script" else goc(dt, *a, **kw)
		tra = []
		f.make_get_request = lambda *a, **kw: tra.append(a) or {"data": []}
		gui = []
		def post(url, data, **kw):
			if url.endswith("Login"):
				return {"token": "thu"}
			gui.append(json.loads(data))
			return {"code": "00", "ok": True, "data": {"inv_invoiceAuth_id": "ID-THU", "inv_invoiceNumber": "THU"}}
		f.make_post_request = post
		f.call = lambda ten, **kw: at.chuan_goi(si, kw["goi"]) if ten.endswith("kiem_goi") else at.phan_loai_phan_hoi_thuan(kw.get("phan_hoi"), kw.get("loi"))
		exec(compile(kb.ban_moi("phat_hanh"), "phat-quay", "exec"), {"frappe": f, "json": json})
		la("không tra Pancake", tra, [])
		la("Save giả lập đúng một lần", len(gui), 1)
		la("giữ người mua", gui[0]["data"][0]["inv_buyerEmail"], "dung@example.com")
		la("không lỗi nạp", f.response["message"]["loi"], [])


@ca("#236: Patch Log đã có các bản cũ vẫn chạy đồng bộ script v454 đúng một lần")
def _migrate_v454():
	import importlib
	from unittest.mock import patch
	cac_patch = [s.strip() for s in (Path(__file__).resolve().parents[2] / 'patches.txt').read_text().splitlines()
		if s.strip().startswith('vagabond.patches.minvoice_')]
	moi = 'vagabond.patches.minvoice_v454'
	la('patch mới được đăng ký đúng một lần', cac_patch.count(moi), 1)
	# Mô phỏng site đã ghi Patch Log tất cả các bản cũ. Nếu chỉ đổi APPVER
	# hoặc dong_bo_cau_truc, hàm cập nhật script không được gọi và ca này đỏ.
	da_chay = set(cac_patch) - {moi}
	goi = []
	with patch.object(kb, 'dong_bo', lambda: goi.append('dong_bo')):
		for _ in range(2):
			for ten in cac_patch:
				if ten not in da_chay:
					importlib.import_module(ten).execute()
					da_chay.add(ten)
	la('migrate gọi đồng bộ đúng một lần', goi, ['dong_bo'])
	with patch.object(kb, 'dong_bo', side_effect=ValueError('script lạ')):
		try:
			importlib.import_module(moi).execute()
		except ValueError:
			pass
		else:
			dung('patch không được nuốt lỗi rồi coi migrate đạt', False)

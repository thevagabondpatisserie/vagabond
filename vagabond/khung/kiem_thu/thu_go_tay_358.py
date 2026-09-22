"""#358 (anh Việt 22/09/2026): máy gợi ý, người chốt.

Hai đường cũ làm hoá đơn kẹt hoặc sai:
  - dựng phiếu mua: máy đoán ra Món mà chưa biết quy đổi đơn vị thì chặn CẢ
    tờ (tờ 287914 Kamereo kẹt 9 ngày, thử 944 lần vì dòng phí 30.000 đ);
  - gắn Món: chưa biết quy đổi thì gắn tạm hệ số 1 rồi nhắc "nhớ khai".
Nay: dựng vẫn ra phiếu nháp, dòng đó trống mã kèm lời đoán; người chọn Món,
gõ hệ số thì máy ghi luôn vào bảng quy đổi của Món.

Phần trình duyệt kiểm ở hanh_vi/go_tay_358.js."""
import ast
from pathlib import Path
from types import SimpleNamespace

from vagabond.khung.kiem_thu.nen import ca, dung, la, nem
from vagabond import dvt_mua
from vagabond.dvt_mua import can_nguoi_khai_he_so, mon_may_doan, dvt_tren_hoa_don
from vagabond.dvt_mua import dvt_ncc_cua_dong
from vagabond.minvoice_chung_tu import mo_ta_dong

GOC = Path(__file__).resolve().parents[2]
MA_MC = (GOC / "minvoice_chung_tu.py").read_text()
MA_DCM = (GOC / "doi_chieu_mua.py").read_text()


def _ham(ma, ten):
	return [n for n in ast.parse(ma).body if isinstance(n, ast.FunctionDef) and n.name == ten]


@ca("#358 thuần: khi nào hỏi người hệ số, khi nào ghi vào Món")
def _quyet():
	la("đã biết quy đổi thì gắn", can_nguoi_khai_he_so("Lần", True, None), "dung")
	la("nhà cung cấp không ghi đơn vị thì gắn", can_nguoi_khai_he_so("", False, None), "dung")
	la("chưa biết, chưa gõ thì hỏi", can_nguoi_khai_he_so("Lần", False, None), "hoi")
	la("gõ 0 vẫn hỏi", can_nguoi_khai_he_so("Lần", False, 0), "hoi")
	la("gõ âm vẫn hỏi", can_nguoi_khai_he_so("Lần", False, -2), "hoi")
	la("gõ chữ vẫn hỏi", can_nguoi_khai_he_so("Lần", False, "abc"), "hoi")
	la("gõ vô hạn vẫn hỏi", can_nguoi_khai_he_so("Lần", False, "inf"), "hoi")
	la("gõ số dương thì khai", can_nguoi_khai_he_so("BOX", False, "1000"), "khai")
	# Codex #358 P1: hệ số chỉ nhận khi đúng Món đã được hỏi.
	la("đúng Món đã hỏi thì khai", can_nguoi_khai_he_so("BOX", False, 1000, "NVLT00141", "NVLT00141"), "khai")
	la("hỏi Món A mà gắn Món B thì hỏi lại", can_nguoi_khai_he_so("Lần", False, 1, "NVLT00141", "DVTI00014"), "hoi")
	la("gửi hệ số không nói cho Món nào thì hỏi lại", can_nguoi_khai_he_so("Lần", False, 1, "NVLT00141", None), "hoi")
	la("đã biết quy đổi thì lệch Món cũng không sao", can_nguoi_khai_he_so("Lần", True, 1, "NVLT00141", "DVTI00014"), "dung")


@ca("Codex #358 vòng 7: đơn vị nhà cung cấp ghi có ô riêng trên dòng phiếu")
def _o_dvt_ncc():
	than = MA_MC.split("def _dong_pi(")[1].split("\ndef ")[0]
	dung("dòng phiếu mang ô đơn vị nhà cung cấp", '"vgb_dvt_ncc"' in than)
	dung("trống thì ghi rõ là không ghi", "dvt_mua.KHONG_GHI" in than)
	from vagabond import minvoice_chung_tu as mc
	o = [t for t in mc.TRUONG_MOI.get("Purchase Invoice Item", []) if t["fieldname"] == "vgb_dvt_ncc"]
	la("ô được khai để Migrate dựng", len(o), 1)
	la("ô chỉ đọc", o[0]["read_only"], 1)
	# gan_ma_hang đọc ô này trước, không đọc mô tả nữa.
	dung("gắn Món đọc ô riêng", 'd.get("vgb_dvt_ncc")' in MA_DCM)


@ca("Codex #358 P1: 'Nos' trên dòng trống mã là đơn vị lót, không phải đơn vị nhà cung cấp")
def _dvt_lot():
	may = {"ten": "Hạt dẻ", "dvt": "BOX", "goi_y_mon": "NVLT00141", "goi_y_dvt_kho": "Gram"}
	la("hoá đơn có ghi đơn vị thì lấy đơn vị đó", dvt_ncc_cua_dong(mo_ta_dong(may), "Nos"), "BOX")
	la("hoá đơn KHÔNG ghi đơn vị: trả rỗng, không lấy Nos", dvt_ncc_cua_dong("Hạt dẻ", "Nos"), "")
	la("đơn vị thật trên ô uom vẫn dùng", dvt_ncc_cua_dong("Hạt dẻ", "BOX"), "BOX")
	la("nhà cung cấp ghi đúng chữ Nos thì vẫn là Nos", dvt_ncc_cua_dong("Hạt dẻ (Nos)", "Nos"), "Nos")
	# Codex #358 vòng 6: TÊN HÀNG cũng có thể kết thúc bằng ngoặc.
	la("tên hàng có ngoặc, hoá đơn không ghi đơn vị: rỗng",
		dvt_ncc_cua_dong("Hạt dẻ (500g)", "Nos", "Hạt dẻ (500g)"), "")
	la("tên hàng có ngoặc, hoá đơn có ghi đơn vị: lấy đơn vị",
		dvt_ncc_cua_dong("Hạt dẻ (500g) (BOX)", "Nos", "Hạt dẻ (500g)"), "BOX")
	# Ô riêng do máy ghi lúc dựng phiếu là nguồn duy nhất khi có (vòng 7).
	la("ô riêng thắng mọi phép đọc mô tả",
		dvt_ncc_cua_dong("Hạt dẻ (500g) (BOX)", "Nos", "Hạt dẻ (500g)", "BAO"), "BAO")
	la("ô riêng ghi là không ghi thì đúng là không ghi",
		dvt_ncc_cua_dong("Hạt dẻ (500g) (BOX)", "Nos", "Hạt dẻ (500g)", dvt_mua.KHONG_GHI), "")
	la("tên hàng có ngoặc, có lời đoán kèm đơn vị",
		dvt_ncc_cua_dong(mo_ta_dong({"ten": "Hạt dẻ (500g)", "dvt": "BAO", "goi_y_mon": "NVLT1", "goi_y_dvt_kho": "Gram"}), "Nos", "Hạt dẻ (500g)"), "BAO")
	# Không đơn vị thì gắn theo đơn vị kho hệ số 1, KHÔNG hỏi và KHÔNG khai quy đổi.
	# Hàng tồn kho mà hoá đơn không ghi đơn vị: KHÔNG hỏi Nos, cũng KHÔNG
	# lấy đơn vị kho hệ số 1 (Codex #358 vòng 7).
	d = _Dong(idx=1, name="R1", item_code="", description="Hạt dẻ (500g)", uom="Nos", ten_hang_ncc="Hạt dẻ (500g)")
	gan, ghi, Loi = _nap_gan(d, la_kho=1)
	nem("hàng tồn kho không đơn vị thì chặn, nói rõ đường đi tiếp",
		lambda: gan("HDM-1", 1, "NVLT00141"), Loi)
	la("không ghi quy đổi nào vào Món", ghi["khai"], [])
	la("dòng vẫn trống mã", d.item_code, "")
	# Dịch vụ thì vẫn gắn theo đơn vị của Món, hệ số 1, như lúc dựng phiếu.
	d2 = _Dong(idx=1, name="R1", item_code="", description="Phí ship", uom="Nos", ten_hang_ncc="Phí ship")
	gan2, ghi2, _ = _nap_gan(d2, la_kho=0)
	kq = gan2("HDM-1", 1, "DVBH00001")
	la("dịch vụ: không hỏi", kq.get("can_he_so"), None)
	la("dịch vụ: đơn vị kho hệ số 1", (d2.item_code, d2.uom, d2.conversion_factor), ("DVBH00001", "Set", 1.0))
	la("dịch vụ: không khai quy đổi", ghi2["khai"], [])


@ca("#358 thuần: lời đoán ghi lên mô tả không làm mất đơn vị gốc, và đọc lại được")
def _mo_ta():
	x = {"ten": "Phí dịch vụ", "dvt": "Lần", "goi_y_mon": "DVTI00014", "goi_y_dvt_kho": "Set"}
	s = mo_ta_dong(x)
	la("đơn vị gốc vẫn đọc được ở cuối", dvt_tren_hoa_don(s), "Lần")
	la("đọc lại được Món máy đoán", mon_may_doan(s), "DVTI00014")
	la("dòng thường giữ khuôn cũ", mo_ta_dong({"ten": "Bắp", "dvt": "Kg"}), "Bắp (Kg)")
	la("không có lời đoán thì rỗng", mon_may_doan("Bắp (Kg)"), "")


def _nap_tra(quy_doi):
	ham = _ham(MA_MC, "_tra_ma_hang")
	f = SimpleNamespace(db=SimpleNamespace(
		get_value=lambda dt, ten, o=None: {"disabled": 0, "stock_uom": "Set"}.get(o) if dt == "Item" else None,
		exists=lambda dt, ten: dt == "UOM" and ten == "Lần"))
	env = dict(frappe=f, quy_doi_theo_ma=quy_doi)
	import sys
	sys.modules.setdefault("vagabond.quy_cach_ncc", SimpleNamespace(tim_mon=lambda *a: "DVTI00014"))
	exec(compile(ast.Module(body=ham, type_ignores=[]), "minvoice_chung_tu.py", "exec"), env)
	return env["_tra_ma_hang"]


@ca("#358 dựng phiếu: đoán ra Món mà chưa biết quy đổi thì KHÔNG chặn tờ, dòng trống mã kèm lời đoán")
def _dung_khong_chan():
	import sys
	cu = sys.modules.get("vagabond.quy_cach_ncc")
	sys.modules["vagabond.quy_cach_ncc"] = SimpleNamespace(tim_mon=lambda *a: "DVTI00014")
	try:
		tra = _nap_tra(lambda *a: None)
		x = {"ten": "Phí dịch vụ", "dvt": "Lần", "ma": ""}
		la("không ném lỗi, dòng trống mã, giữ đơn vị gốc", tra(x, "0315000500", "KAMEREO"), (None, "Lần", 1))
		la("lời đoán ghi lên dòng", (x.get("goi_y_mon"), x.get("goi_y_dvt_kho")), ("DVTI00014", "Set"))
		tra2 = _nap_tra(lambda *a: ("Lần", 1))
		la("biết quy đổi thì gắn như cũ", tra2({"ten": "Phí dịch vụ", "dvt": "Lần", "ma": ""}, "0315000500", "KAMEREO"), ("DVTI00014", "Lần", 1))
	finally:
		if cu is not None:
			sys.modules["vagabond.quy_cach_ncc"] = cu
		else:
			sys.modules.pop("vagabond.quy_cach_ncc", None)
	dung("đường gắn lại mã người đã chọn vẫn ném lỗi rõ", "Cần khai quy cách mua" in MA_MC.split("def don_vi_theo_ma(")[1].split("\ndef ")[0])


class _Dong(dict):
	def __getattr__(s, k):
		return s.get(k)

	def __setattr__(s, k, v):
		s[k] = v


def _nap_gan(dong, quy_doi_co=None, la_kho=1, map_co=None):
	"""Chạy THẬT gan_ma_hang với frappe giả. quy_doi_co: {đơn vị: hệ số} đã khai trên Món."""
	quy_doi_co = dict(quy_doi_co or {})
	ghi = {"luu": 0, "khai": [], "uom_moi": [], "commit": 0, "map": []}
	doc = SimpleNamespace(name="HDM-1", docstatus=0, items=[dong], flags=SimpleNamespace(),
		save=lambda: ghi.__setitem__("luu", ghi["luu"] + 1), add_comment=lambda *a: None)

	class Loi(Exception):
		pass

	def throw(m, *a, **k):
		raise Loi(m)

	def get_doc(a, b=None):
		if a == "Purchase Invoice":
			return doc
		if isinstance(a, dict) and a.get("doctype") == "UOM":
			return SimpleNamespace(flags=SimpleNamespace(), insert=lambda **k: ghi["uom_moi"].append(a["uom_name"]))
		return SimpleNamespace(flags=SimpleNamespace(), insert=lambda **k: None)

	def get_value(dt, ten, o=None):
		if dt == "Item":
			return {"stock_uom": "Set", "is_stock_item": la_kho}.get(o)
		if dt == "MInvoice NCC Map" and map_co:
			return map_co["item_code"] if o == "item_code" else map_co["name"]
		return None

	f = SimpleNamespace(throw=throw, get_doc=get_doc, session=SimpleNamespace(user="uyen@vgb"),
		db=SimpleNamespace(exists=lambda dt, t=None: dt == "Item", get_value=get_value,
			set_value=lambda *a: ghi["map"].append(a), commit=lambda: ghi.__setitem__("commit", ghi["commit"] + 1)))
	dv = SimpleNamespace(
		dvt_tren_hoa_don=dvt_mua.dvt_tren_hoa_don, goi_y_don_vi=lambda s: "", cung_don_vi=lambda a, b: a == b,
		dvt_ncc_cua_dong=dvt_mua.dvt_ncc_cua_dong,
		chan_hang_kho_khong_dvt=dvt_mua.chan_hang_kho_khong_dvt,
		can_nguoi_khai_he_so=dvt_mua.can_nguoi_khai_he_so,
		he_so_cua_mon=lambda ma, d: quy_doi_co.get(d, 0.0), mon_may_doan=dvt_mua.mon_may_doan)

	def ghi_quy_doi(ma, d, hs, kho):
		quy_doi_co[d] = hs
		ghi["khai"].append((ma, d, hs))
	env = dict(frappe=f, dvt_mua=dv, _kiem_quyen=lambda: None, _lam_duoc=lambda: True,
		cint=lambda n: int(n or 0), flt=lambda n: float(n or 0), nowdate=lambda: "2026-09-22",
		_ghi_quy_doi=ghi_quy_doi, _mst_cua_to=lambda d: "0315000500" if map_co else "")
	ham = _ham(MA_DCM, "gan_ma_hang")
	for n in ham:
		n.decorator_list = []
	exec(compile(ast.Module(body=ham, type_ignores=[]), "doi_chieu_mua.py", "exec"), env)
	return env["gan_ma_hang"], ghi, Loi


@ca("#358 gắn Món: chưa khai đơn vị thì HỎI, không lưu gì; gõ hệ số thì ghi vào Món rồi gắn đúng hệ số đó")
def _gan_hoi_roi_khai():
	d = _Dong(idx=3, name="R3", item_code="", description="Phí dịch vụ (Lần)", uom="Nos", ten_hang_ncc="Phí dịch vụ")
	gan, ghi, _ = _nap_gan(d, la_kho=0)
	kq = gan("HDM-1", 3, "DVTI00014")
	la("hỏi hệ số, đơn vị lấy theo hoá đơn gốc", (kq.get("can_he_so"), kq.get("dvt_ncc"), kq.get("dvt_kho"), kq.get("de_xuat")), (1, "Lần", "Set", 1))
	la("chưa lưu phiếu, chưa khai, dòng vẫn trống", (ghi["luu"], ghi["khai"], d.item_code), (0, [], ""))
	kq = gan("HDM-1", 3, "DVTI00014", he_so=1, he_so_cho="DVTI00014")
	la("ghi hệ số vào Món", ghi["khai"], [("DVTI00014", "Lần", 1.0)])
	la("dòng mang đúng đơn vị và hệ số vừa khai", (d.item_code, d.uom, d.conversion_factor), ("DVTI00014", "Lần", 1.0))
	la("không báo chưa khai đơn vị nữa", kq.get("chua_khai_don_vi"), 0)


@ca("#358 gắn Món: hàng tồn kho không đề xuất hệ số 1; Món đã khai thì gắn luôn không hỏi")
def _gan_kho_va_da_khai():
	d = _Dong(idx=1, name="R1", item_code="", description="Hạt dẻ (BOX)", uom="Nos", ten_hang_ncc="Hạt dẻ")
	gan, ghi, _ = _nap_gan(d, la_kho=1)
	la("hàng kho: không gợi ý 1", gan("HDM-1", 1, "NVLT00141").get("de_xuat"), 0)
	d2 = _Dong(idx=1, name="R1", item_code="", description="Hạt dẻ (BOX)", uom="Nos", ten_hang_ncc="Hạt dẻ")
	gan2, ghi2, _ = _nap_gan(d2, quy_doi_co={"BOX": 1000.0})
	kq = gan2("HDM-1", 1, "NVLT00141")
	la("đã khai thì gắn luôn", (kq.get("can_he_so"), d2.uom, d2.conversion_factor, ghi2["khai"]), (None, "BOX", 1000.0, []))
	d3 = _Dong(idx=1, name="R1", item_code="", description="Hạt dẻ (BOX)", uom="Nos", ten_hang_ncc="Hạt dẻ")
	gan3, ghi3, _ = _nap_gan(d3)
	gan3("HDM-1", 1, "NVLT00141", he_so=0, he_so_cho="NVLT00141")
	la("gõ 0 không ghi gì", (ghi3["khai"], ghi3["luu"], d3.item_code), ([], 0, ""))


@ca("Codex #358 P1: hỏi hệ số cho Món A rồi gắn Món B kèm hệ số cũ thì máy chủ HỎI LẠI cho B, không ghi gì vào B")
def _doi_mon_sau_khi_hoi():
	d = _Dong(idx=3, name="R3", item_code="", description="Phí dịch vụ (Lần)", uom="Nos", ten_hang_ncc="Phí dịch vụ")
	gan, ghi, _ = _nap_gan(d, la_kho=1)
	la("hỏi cho Món A", gan("HDM-1", 3, "DVTI00014").get("can_he_so"), 1)
	kq = gan("HDM-1", 3, "NVLT00141", he_so=1, he_so_cho="DVTI00014")
	la("gắn Món B kèm hệ số của A: hỏi lại cho B", (kq.get("can_he_so"), kq.get("item_code")), (1, "NVLT00141"))
	la("không ghi gì vào Món B, dòng vẫn trống", (ghi["khai"], ghi["luu"], d.item_code), ([], 0, ""))
	kq = gan("HDM-1", 3, "NVLT00141", he_so=1)
	la("gửi hệ số không kèm Món đã hỏi: cũng hỏi lại", (kq.get("can_he_so"), ghi["khai"]), (1, []))


@ca("Codex #358 P2: máy đoán Món X theo ghi nhớ, người chọn Món Y thì ghi nhớ đổi sang Y")
def _sua_ghi_nho():
	may = {"ten": "Phí dịch vụ", "dvt": "Lần", "goi_y_mon": "DVTI00014", "goi_y_dvt_kho": "Set"}
	d = _Dong(idx=3, name="R3", item_code="", description=mo_ta_dong(may), uom="Lần", ten_hang_ncc="Phí dịch vụ")
	gan, ghi, _ = _nap_gan(d, quy_doi_co={"Lần": 1.0}, map_co={"name": "76jk41445u", "item_code": "DVTI00014"})
	gan("HDM-1", 3, "DVBH00001")
	la("ghi nhớ trỏ sang Món người chọn", ghi["map"], [("MInvoice NCC Map", "76jk41445u", "item_code", "DVBH00001")])
	# Người chọn đúng Món máy đoán thì không đụng ghi nhớ.
	d2 = _Dong(idx=3, name="R3", item_code="", description=mo_ta_dong(may), uom="Lần", ten_hang_ncc="Phí dịch vụ")
	gan2, ghi2, _ = _nap_gan(d2, quy_doi_co={"Lần": 1.0}, map_co={"name": "76jk41445u", "item_code": "DVTI00014"})
	gan2("HDM-1", 3, "DVTI00014", he_so=1, he_so_cho="DVTI00014")
	la("chọn đúng lời đoán: giữ nguyên ghi nhớ", ghi2["map"], [])
	# Ghi nhớ trỏ Món khác (không phải nguồn của lời đoán) thì không tự đè.
	d3 = _Dong(idx=3, name="R3", item_code="", description=mo_ta_dong(may), uom="Lần", ten_hang_ncc="Phí dịch vụ")
	gan3, ghi3, _ = _nap_gan(d3, quy_doi_co={"Lần": 1.0}, map_co={"name": "76jk41445u", "item_code": "NVLT9"})
	gan3("HDM-1", 3, "DVBH00001")
	la("ghi nhớ không phải nguồn lời đoán: không đè", ghi3["map"], [])


@ca("Codex #358 P1: dòng máy đoán mà người chưa chốt thì KHÔNG ghi sổ được, ở mọi đường ghi sổ")
def _chan_ghi_so_may_doan():
	may = {"ten": "Phí dịch vụ", "dvt": "Lần", "goi_y_mon": "DVTI00014", "goi_y_dvt_kho": "Set"}
	ds = [
		{"idx": 1, "item_code": "NVLT1", "description": "Bắp (Kg)"},
		{"idx": 2, "item_code": "", "description": mo_ta_dong(may)},
		{"idx": 3, "item_code": "", "description": "Phí ship (Lần)"},
	]
	la("chỉ dòng mang lời đoán mà còn trống mã", dvt_mua.dong_may_doan_chua_chot(ds), [(2, "DVTI00014")])
	ds[1]["item_code"] = "DVTI00014"
	la("đã chốt Món thì hết chặn", dvt_mua.dong_may_doan_chua_chot(ds), [])
	# Gác ở before_submit nên mọi đường ghi sổ (Desk, app, ghi_so_thang) đều đi qua.
	from vagabond import hooks
	la("gác đứng đầu before_submit của Hoá đơn mua",
		hooks.doc_events["Purchase Invoice"]["before_submit"][0], "vagabond.doi_chieu_mua.chan_ghi_so_may_doan")
	ham = _ham(MA_DCM, "chan_ghi_so_may_doan")
	class Loi(Exception):
		pass
	def nem_loi(m):
		raise Loi(m)
	env = dict(frappe=SimpleNamespace(throw=nem_loi), dvt_mua=dvt_mua)
	exec(compile(ast.Module(body=ham, type_ignores=[]), "doi_chieu_mua.py", "exec"), env)
	class _D(dict):
		def get(self, k, m=None):
			return dict.get(self, k, m)
	ds[1]["item_code"] = ""
	doc = SimpleNamespace(items=[_D(x) for x in ds])
	try:
		env["chan_ghi_so_may_doan"](doc, "before_submit")
		dung("phải chặn", False)
	except Loi as e:
		dung("lời chặn nói rõ dòng và Món máy đoán", "Dòng 2" in str(e) and "DVTI00014" in str(e))
	doc = SimpleNamespace(items=[_D(ds[0]), _D(ds[2])])
	env["chan_ghi_so_may_doan"](doc, "before_submit")


@ca("#358 gợi ý Món: lời đoán của máy đứng đầu danh sách")
def _goi_y_dau():
	than = MA_DCM.split("def goi_y_mon(")[1].split("\n@frappe")[0]
	i0 = than.find("mon_may_doan(")
	i1 = than.find("_phieu_ung_vien(doc)")
	dung("đọc lời đoán trên dòng trước phiếu nhập", 0 < i0 < i1)
	dung("ưu tiên 0", '"uu_tien": 0' in than)

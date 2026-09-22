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


def _nap_gan(dong, quy_doi_co=None, la_kho=1):
	"""Chạy THẬT gan_ma_hang với frappe giả. quy_doi_co: {đơn vị: hệ số} đã khai trên Món."""
	quy_doi_co = dict(quy_doi_co or {})
	ghi = {"luu": 0, "khai": [], "uom_moi": [], "commit": 0}
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
		return None

	f = SimpleNamespace(throw=throw, get_doc=get_doc, session=SimpleNamespace(user="uyen@vgb"),
		db=SimpleNamespace(exists=lambda dt, t=None: dt == "Item", get_value=get_value,
			set_value=lambda *a: None, commit=lambda: ghi.__setitem__("commit", ghi["commit"] + 1)))
	dv = SimpleNamespace(
		dvt_tren_hoa_don=dvt_mua.dvt_tren_hoa_don, goi_y_don_vi=lambda s: "", cung_don_vi=lambda a, b: a == b,
		can_nguoi_khai_he_so=dvt_mua.can_nguoi_khai_he_so,
		he_so_cua_mon=lambda ma, d: quy_doi_co.get(d, 0.0))

	def ghi_quy_doi(ma, d, hs, kho):
		quy_doi_co[d] = hs
		ghi["khai"].append((ma, d, hs))
	env = dict(frappe=f, dvt_mua=dv, _kiem_quyen=lambda: None, _lam_duoc=lambda: True,
		cint=lambda n: int(n or 0), flt=lambda n: float(n or 0), nowdate=lambda: "2026-09-22",
		_ghi_quy_doi=ghi_quy_doi, _mst_cua_to=lambda d: "")
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
	kq = gan("HDM-1", 3, "DVTI00014", he_so=1)
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
	gan3("HDM-1", 1, "NVLT00141", he_so=0)
	la("gõ 0 không ghi gì", (ghi3["khai"], ghi3["luu"], d3.item_code), ([], 0, ""))


@ca("#358 gợi ý Món: lời đoán của máy đứng đầu danh sách")
def _goi_y_dau():
	than = MA_DCM.split("def goi_y_mon(")[1].split("\n@frappe")[0]
	i0 = than.find("mon_may_doan(")
	i1 = than.find("_phieu_ung_vien(doc)")
	dung("đọc lời đoán trên dòng trước phiếu nhập", 0 < i0 < i1)
	dung("ưu tiên 0", '"uu_tien": 0' in than)

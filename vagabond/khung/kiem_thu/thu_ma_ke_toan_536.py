# -*- coding: utf-8 -*-
"""v536: mã khách kế toán (mã Fast) và sổ hoá đơn điện tử bán ra.

Bối cảnh 29/09/2026: chị Dung đối chiếu theo mã (KL0001 khách lẻ, KH/NC theo
MST); tờ thay thế 14576 chỉ nằm ở ô ghi tay của đơn gốc, tìm theo tên công ty
không ra. Anh Việt chốt: không tạm ghi bằng MST, đang có mã thì cấp nối tiếp.

Tên, MST, mã trong tệp này là giả; SỐ tờ 14514/14576 giữ đúng để ca kiểm nói
được đúng ca thật. Chạy hàm thật của ma_ke_toan, doi_soat_hddt_ra,
minvoice_chung_tu và báo cáo, với frappe giả từng ca.
"""

import ast
import datetime
from pathlib import Path
from types import SimpleNamespace as NS
import unittest.mock

from vagabond import ma_ke_toan as mk
from vagabond import doi_soat_hddt_ra as ds
from vagabond.khung.kiem_thu.nen import ca, dung, la, nem

GOC = Path(__file__).resolve().parents[2]


class _D(dict):
	__getattr__ = dict.get

	def set(self, k, v):
		self[k] = v


# ------------------------------------------------------------- phép thuần

@ca("v536 mã: chuẩn MST, nhận dạng mã, mã kế tiếp nối mã lớn nhất (KL0001, mã lạ, rỗng không tính)")
def _thuan():
	la("MST", (mk.chuan_mst("0317064683"), mk.chuan_mst("0317064683-001"), mk.chuan_mst("0317 064 683"),
		mk.chuan_mst("123"), mk.chuan_mst(None), mk.chuan_mst("079123456789")),
		("0317064683", "0317064683-001", "0317064683", "", "", "079123456789"))
	la("dạng mã", (mk.la_ma("KH000015", "KH"), mk.la_ma("kh001588", "KH"), mk.la_ma("KL0001", "KH"),
		mk.la_ma("NC000504", "NC"), mk.la_ma("KH", "KH"), mk.la_ma("KHABC", "KH")),
		(True, True, False, True, False, False))
	la("kế tiếp sau KH001588 (Fast đi trước ERP)", mk.ma_ke_tiep(["KH001382", "KH001588", "KL0001", "", "CTY001"], "KH"), "KH001589")
	la("danh sách trống bắt đầu từ 1", mk.ma_ke_tiep([], "NC"), "NC000001")
	la("mã khách lẻ khi không MST", mk.ma_ke_toan_cua_hoa_don("", lambda m: "KH1"), "KL0001")
	la("mã theo MST", mk.ma_ke_toan_cua_hoa_don("0317064683", {"0317064683": "kh000015"}.get), "KH000015")
	la("có MST mà không tra ra thì rỗng, KHÔNG tạm ghi MST", mk.ma_ke_toan_cua_hoa_don("0317064683", lambda m: ""), "")


@ca("v536 đọc tệp Fast: chỉ KH và NC có MST; NV, SEP, CTY001, KL0001, dòng không MST bỏ qua")
def _doc_tep():
	ra = mk.doc_tep_fast([
		{"ma": "KL0001", "ten": "NGƯỜI MUA KHÔNG LẤY HÓA ĐƠN", "mst": ""},
		{"ma": "KH000015", "ten": "Công ty A", "mst": "0300000001", "dia_chi": "Q1"},
		{"ma": "kh000016", "ten": "Công ty B", "mst": "0300000002-001"},
		{"ma": "KH000017", "ten": "Không MST", "mst": ""},
		{"ma": "NC000504", "ten": "NCC C", "mst": "0300000003"},
		{"ma": "NV001", "ten": "Nhân viên", "mst": "0300000004"},
		{"ma": "CTY001", "ten": "Vagabond", "mst": "0300000005"},
		{"ma": "SEP", "ten": "Sếp", "mst": "0300000006"},
	])
	la("ba dòng", [(d["loai"], d["ma"], d["mst"]) for d in ra],
		[("Customer", "KH000015", "0300000001"), ("Customer", "KH000016", "0300000002-001"), ("Supplier", "NC000504", "0300000003")])


@ca("v536 kế hoạch nạp: điền mã cho bản ghi trống, tạo mới, giữ, và ba kiểu xung đột không ghi đè")
def _ke_hoach():
	hien = {"Customer": {"0300000001": {"name": "DN000001", "ma": ""},
			"0300000002": {"name": "DN000002", "ma": "KH000099"},
			"0300000003": {"name": "DN000003", "ma": "KH000020"}},
		"Supplier": {"0300000009": {"name": "NCC9", "ma": "NC000001"}}}
	kh = mk.ke_hoach_nap([
		{"ma": "KH000015", "ten": "A", "mst": "0300000001"},
		{"ma": "KH000016", "ten": "B", "mst": "0300000002"},
		{"ma": "KH000020", "ten": "C", "mst": "0300000003"},
		{"ma": "KH000030", "ten": "D", "mst": "0300000004"},
		{"ma": "KH000030", "ten": "D2", "mst": "0300000005"},
		{"ma": "NC000001", "ten": "E", "mst": "0300000010"},
	], hien)
	la("điền mã", [(d["name"], d["ma"]) for d in kh["cap_nhat"]], [("DN000001", "KH000015")])
	# Codex #389 P2 vòng 3: bản trước mong KH000030 được tạo cho MST đứng trước
	# (thứ tự dòng quyết định). Nay mã gắn cho hai MST thì không dòng nào được ghi.
	la("tạo mới: mã hai MST không về tay dòng nào", [d["ma"] for d in kh["tao_moi"]], [])
	la("giữ", kh["giu"], 1)
	la("xung đột: ERP giữ mã khác; cùng mã hai MST trong tệp; mã đang là của NCC khác",
		[d["ma"] for d in kh["xung_dot"]], ["KH000016", "KH000030", "NC000001"])
	dung("nói rõ ERP đang giữ gì", "KH000099" in kh["xung_dot"][0]["ly_do"])
	# ma_dang_dung đưa từ ngoài: bản ghi KHÔNG MST đang giữ mã cũng chặn.
	kh = mk.ke_hoach_nap([{"ma": "KH000015", "ten": "A", "mst": "0300000001"}], hien,
		{"Customer": {"KH000015": ""}})
	la("mã của bản ghi không MST", ([d["ma"] for d in kh["xung_dot"]], kh["cap_nhat"]), (["KH000015"], []))


# ----------------------------------------------------------- phần chạm hệ

def _nen(khach=None, ncc=None, da_nap="1", loi_set=None):
	"""frappe giả: bảng Customer/Supplier trong bộ nhớ, khoá, mặc định."""
	khach = khach if khach is not None else {}
	ncc = ncc if ncc is not None else {}
	bang = {"Customer": khach, "Supplier": ncc}
	vet = []
	tao = []

	def get_all(dt, filters=None, fields=None, order_by=None, limit_page_length=0, **k):
		rows = []
		for ten, r in bang.get(dt, {}).items():
			ok = True
			for k_, v in (filters or {}).items():
				x = r.get(k_)
				if isinstance(v, list):
					if v[0] == "in":
						ok &= x in v[1]
					elif v[0] == "is":
						ok &= bool(x) if v[1] == "set" else not x
				else:
					ok &= x == v
			if ok:
				rows.append(_D(dict(r, name=ten)))
		return rows[:limit_page_length] if limit_page_length else rows

	def get_value(dt, name, o, **k):
		if dt in bang:
			return (bang[dt].get(name) or {}).get(o)
		return None

	def set_value(dt, name, o, v, **k):
		vet.append(("set", dt, name, o, v))
		if loi_set:
			raise RuntimeError("giả lập rớt DB")
		bang[dt].setdefault(name, {})[o] = v

	def sql(q, a=None, **k):
		vet.append(("sql", " ".join(q.split())[:40], a))
		if "get_lock" in q:
			return [(1,)]
		if "release_lock" in q:
			return [(1,)]
		if q.strip().startswith("select"):
			dt = "Customer" if "tabCustomer" in q else "Supplier"
			o = mk.O_MA[dt]
			return [(r.get(o),) for r in bang[dt].values() if str(r.get(o) or "").startswith(a[0][:-1])]
		return []

	def get_doc(d):
		tao.append(d)
		doc = _D(d)
		doc.flags = NS()
		doc.name = "%s-MOI-%d" % ("DN" if d["doctype"] == "Customer" else "NCC", len(tao))

		def insert():
			bang[d["doctype"]][doc.name] = dict(d)
		doc.insert = insert
		return doc

	mac_dinh = {mk.KHOA_DA_NAP: da_nap}
	if da_nap == "1":
		# Nạp thật luôn lập sàn cho loại mã có trong tệp; cap_ma cần sàn (Codex #389).
		mac_dinh.update({mk.KHOA_SAN + "KH": "1", mk.KHOA_SAN + "NC": "1"})
	f = NS(db=NS(get_value=get_value, set_value=set_value, sql=sql, exists=lambda dt, n: True,
			get_single_value=lambda *a: "Khách lẻ", get_default=lambda k: mac_dinh.get(k),
			commit=lambda: vet.append(("commit",)), count=lambda *a, **k: 0, has_column=lambda *a: True,
			after_commit=NS(add=lambda fn: vet.append(("sau_commit", fn))),
			after_rollback=NS(add=lambda fn: vet.append(("sau_rollback", fn)))),
		get_all=get_all, get_doc=get_doc, log_error=lambda *a, **k: vet.append(("log",) + a),
		get_traceback=lambda: "", get_roles=lambda: ["Accounts Manager"], throw=_throw,
		defaults=NS(set_global_default=lambda k, v: mac_dinh.__setitem__(k, v)))
	return f, bang, vet, tao


def _throw(msg, *a, **k):
	raise ValueError(msg)


KH = {
	"KL042334": {"customer_name": "Ms.Thùy", "tax_id": "", "custom_ma_khach": ""},
	"KH000015": {"customer_name": "Oliver", "tax_id": "0317064683", "custom_ma_khach": ""},
	"DN000001": {"customer_name": "Falcons", "tax_id": "0300000001", "custom_ma_khach": "KH001588"},
	"DN000002": {"customer_name": "Sỉ B", "tax_id": "0300000002-001", "custom_ma_khach": "KH000200"},
}


@ca("v536 hook hoá đơn bán: không MST là KL0001; MST có mã lấy mã; MST 13 số khớp cả hai dạng; khách của đơn vẫn là người đặt")
def _hook_don():
	f, bang, vet, tao = _nen(dict((k, dict(v)) for k, v in KH.items()))
	with unittest.mock.patch.object(mk, "frappe", f):
		d = _D(name="HDB-1", customer="KL042334", vgb_xhd_mst="", vgb_ma_khach_ke_toan="")
		mk.dien_ma_khach_hoa_don(d)
		la("khách lẻ", d.vgb_ma_khach_ke_toan, "KL0001")
		d = _D(name="HDB-2", customer="KL042334", vgb_xhd_mst="0300000001", vgb_xhd_ten="Falcons")
		mk.dien_ma_khach_hoa_don(d)
		la("mã Fast của công ty xuất hoá đơn", d.vgb_ma_khach_ke_toan, "KH001588")
		la("không đổi khách của đơn", d.customer, "KL042334")
		d = _D(name="HDB-3", customer="KL042334", vgb_xhd_mst="0300000002001")
		mk.dien_ma_khach_hoa_don(d)
		la("MST 13 số gõ liền vẫn khớp bản ghi có gạch", d.vgb_ma_khach_ke_toan, "KH000200")
		# Khách sỉ đặt bằng chính hồ sơ công ty, không ghi ô Xuất HĐ cho.
		d = _D(name="HDB-4", customer="DN000001", vgb_xhd_mst="")
		mk.dien_ma_khach_hoa_don(d)
		la("MST của chính khách hàng", d.vgb_ma_khach_ke_toan, "KH001588")
	la("không tạo khách nào", tao, [])


@ca("v536 cấp mã nối tiếp: KH000015 có MST chưa mã nhận KH001589 (sau mã lớn nhất), có khoá, chỉ sau khi nạp danh mục")
def _cap_ma():
	f, bang, vet, tao = _nen(dict((k, dict(v)) for k, v in KH.items()), da_nap="")
	with unittest.mock.patch.object(mk, "frappe", f):
		d = _D(name="HDB-5", customer="KL042334", vgb_xhd_mst="0317064683", vgb_xhd_ten="Oliver")
		mk.dien_ma_khach_hoa_don(d)
		la("chưa nạp danh mục: KHÔNG cấp, để trống, không tạm ghi MST", d.get("vgb_ma_khach_ke_toan"), None)
		dung("chưa nạp: không đụng khoá", not any(v[0] == "sql" and "get_lock" in v[1] for v in vet))
	f, bang, vet, tao = _nen(dict((k, dict(v)) for k, v in KH.items()))
	with unittest.mock.patch.object(mk, "frappe", f):
		d = _D(name="HDB-5", customer="KL042334", vgb_xhd_mst="0317064683", vgb_xhd_ten="Oliver")
		mk.dien_ma_khach_hoa_don(d)
	la("nối tiếp sau KH001588", d.vgb_ma_khach_ke_toan, "KH001589")
	la("ghi vào hồ sơ khách, không tạo khách mới", (bang["Customer"]["KH000015"]["custom_ma_khach"], tao), ("KH001589", []))
	thu_tu = [v[1][:14] if v[0] == "sql" else v[0] for v in vet if v[0] in ("sql", "set", "sau_commit")]
	la("khoá trước khi đọc mã lớn nhất, ghi; khoá giữ tới commit (Codex #383 F2)",
		thu_tu, ["select get_loc", "sau_commit", "select `custom", "set"])
	# Lượt hai cùng khách: trả mã đang có, không cấp thêm.
	with unittest.mock.patch.object(mk, "frappe", f):
		la("đã có mã thì giữ", mk.cap_ma("Customer", "KH000015"), "KH001589")
	# Ghi hỏng giữa chừng vẫn nhả khoá và hook không ném.
	f, bang, vet, tao = _nen(dict((k, dict(v)) for k, v in KH.items()), loi_set=True)
	with unittest.mock.patch.object(mk, "frappe", f):
		d = _D(name="HDB-6", customer="KL042334", vgb_xhd_mst="0317064683")
		mk.dien_ma_khach_hoa_don(d)
	dung("ghi hỏng thì khoá nhả theo rollback của giao dịch, đã đăng ký", any(v[0] == "sau_rollback" for v in vet))
	dung("lỗi vào Error Log, đơn vẫn lưu", any(v[0] == "log" for v in vet) and not d.get("vgb_ma_khach_ke_toan"))


@ca("v536 MST lạ trên hoá đơn: tạo hồ sơ công ty (nhóm doanh nghiệp, có MST) rồi cấp mã; NCC lưu có MST cũng được cấp NC nối tiếp")
def _tao_moi():
	f, bang, vet, tao = _nen(dict((k, dict(v)) for k, v in KH.items()),
		{"NCC1": {"supplier_name": "X", "tax_id": "0300000010", "custom_ma_ncc": "NC000504"}})
	with unittest.mock.patch.object(mk, "frappe", f):
		d = _D(name="HDB-7", customer="KL042334", vgb_xhd_mst="0300000777", vgb_xhd_ten="Công ty mới")
		mk.dien_ma_khach_hoa_don(d)
		la("tạo đúng một khách công ty mang MST", [(t["doctype"], t["customer_type"], t["tax_id"], t["customer_name"]) for t in tao],
			[("Customer", "Company", "0300000777", "Công ty mới")])
		la("mã cấp nối tiếp", d.vgb_ma_khach_ke_toan, "KH001589")
		ncc = _D(doctype="Supplier", name="NCC2", tax_id="0300000011", custom_ma_ncc="")
		bang["Supplier"]["NCC2"] = dict(ncc)
		mk.cap_ma_khi_luu(ncc)
		la("NCC nhận mã sau NC000504", ncc.custom_ma_ncc, "NC000505")
		ncc = _D(doctype="Supplier", name="NCC3", tax_id="", custom_ma_ncc="")
		bang["Supplier"]["NCC3"] = dict(ncc)
		mk.cap_ma_khi_luu(ncc)
		la("không MST thì không cấp", ncc.custom_ma_ncc, "")


@ca("v536 nạp danh mục Fast: chỉ kế toán trưởng hoặc quản trị; điền mã trống, không ghi đè mã khác, bật cờ đã nạp, điền lại hoá đơn")
def _nap():
	f, bang, vet, tao = _nen(dict((k, dict(v)) for k, v in KH.items()), da_nap="")
	f.get_roles = lambda: ["Purchase User"]
	with unittest.mock.patch.object(mk, "frappe", f):
		nem("không đủ vai", lambda: mk.nap_danh_muc_fast("[]"), ValueError)
	f.get_roles = lambda: ["Accounts Manager"]
	goi = []
	with unittest.mock.patch.object(mk, "frappe", f), unittest.mock.patch.object(mk, "dien_ma_hang_loat", lambda: goi.append(1) or 7):
		kq = mk.nap_danh_muc_fast([
			{"ma": "KH000015", "ten": "Oliver", "mst": "0317064683"},
			{"ma": "KH000001", "ten": "Falcons", "mst": "0300000001"},
			{"ma": "KH000300", "ten": "Mới", "mst": "0300000300"},
		])
	la("điền mã cho khách trống mã", bang["Customer"]["KH000015"]["custom_ma_khach"], "KH000015")
	la("không ghi đè mã lệch", bang["Customer"]["DN000001"]["custom_ma_khach"], "KH001588")
	la("kết quả", (kq["cap_nhat"], kq["tao_moi"], kq["chua_tao"], len(kq["xung_dot"]), kq["hoa_don_dien_ma"]), (1, 0, 1, 1, 7))
	la("bật cờ đã nạp", f.db.get_default(mk.KHOA_DA_NAP), "1")
	la("điền lại hoá đơn đúng một lần", goi, [1])
	with unittest.mock.patch.object(mk, "frappe", f), unittest.mock.patch.object(mk, "dien_ma_hang_loat", lambda: 0):
		kq = mk.nap_danh_muc_fast([{"ma": "KH000300", "ten": "Mới", "mst": "0300000300"}], tao_moi=1)
	la("tạo mới khi cho phép", (kq["tao_moi"], [t["tax_id"] for t in tao]), (1, ["0300000300"]))


@ca("v536 điền hàng loạt: ba câu update chỉ chạm ô mã đang trống, không câu nào đụng số, ngày, khách của tờ")
def _hang_loat():
	cau = []
	dem = iter([10, 25])
	f = NS(db=NS(count=lambda *a, **k: next(dem), sql=lambda q, *a, **k: cau.append(" ".join(q.split())), has_column=lambda *a: True))
	with unittest.mock.patch.object(mk, "frappe", f):
		la("số tờ điền thêm", mk.dien_ma_hang_loat(), 15)
	la("ba câu", len(cau), 3)
	for c in cau:
		dung("chỉ ghi ô mã", c.startswith("update `tabSales Invoice` hd") and "set hd.vgb_ma_khach_ke_toan =" in c
			and c.count(" set ") == 1 and "ifnull(hd.vgb_ma_khach_ke_toan, '') = ''" in c)
		dung("không chạm ô khác", not any(o in c.split(" set ")[1].split(" where ")[0] for o in ("customer", "posting_date", "custom_hddt_so")))
	dung("câu 1 so MST bỏ dấu gạch hai phía", "replace(k.tax_id, '-', '') = replace(hd.vgb_xhd_mst, '-', '')" in cau[0])
	dung("câu 3 chỉ khi không MST ở đâu cả", "ifnull(k.tax_id, '') = ''" in cau[2] and "ifnull(hd.vgb_xhd_mst, '') = ''" in cau[2])
	# Bench không có ô mã Fast: chỉ chạy câu khách lẻ.
	cau.clear()
	dem = iter([0, 0])
	f.db.has_column = lambda *a: False
	with unittest.mock.patch.object(mk, "frappe", f):
		mk.dien_ma_hang_loat()
	la("thiếu ô mã: một câu", len(cau), 1)


# ------------------------------------------ nối hai chiều tờ m-invoice và đơn

def _nen_to(don_ds, to_ds):
	"""frappe giả cho doi_soat_hddt_ra: đơn đã ghi sổ và bảng tờ ghi được."""
	ghi = []

	def get_all(dt, filters=None, fields=None, limit_page_length=0, **k):
		ra = []
		for r in don_ds:
			ok = True
			for k_, v in filters.items():
				if k_ == "docstatus":
					continue
				x = r.get(k_)
				ok &= (str(x) in [str(g) for g in v[1]]) if isinstance(v, list) else (x == v)
			if ok:
				ra.append(_D(r))
		return ra[:limit_page_length] if limit_page_length else ra

	def sql(q, a=None, **k):
		if "update `tabMInvoice Invoice`" in q:
			ghi.append(("cau", " ".join(q.split())))
			t = to_ds.get(a["to"])
			if t is not None and not t.get("vgb_don_erp"):
				t["vgb_don_erp"] = a["don"]
				t["ly_do_bo_qua"] = a["ghi_chu"] or t.get("ly_do_bo_qua")
				ghi.append((a["to"], a["don"]))
		return []

	def get_value(dt, name, o, **k):
		return (to_ds.get(name) or {}).get(o)
	f = NS(get_all=get_all, db=NS(sql=sql, get_value=get_value), log_error=lambda *a, **k: ghi.append(("log",)),
		get_traceback=lambda: "")
	return f, ghi


DON_GOC = [
	{"name": "HDB-26-09-03253", "custom_hddt_so": "14514", "custom_hddt_ky_hieu": "1C26MPV", "custom_minvoice_id": "id-14514",
		"custom_hddt_id": "", "custom_hddt_thay_the": "1C26MPV 14576", "docstatus": 1},
	{"name": "HDB-26-09-09999", "custom_hddt_so": "15500", "custom_hddt_ky_hieu": "1C26MPV", "custom_minvoice_id": "",
		"custom_hddt_id": "", "custom_hddt_thay_the": "", "docstatus": 1},
	{"name": "HDB-KHAC", "custom_hddt_so": "15500", "custom_hddt_ky_hieu": "1C26MVO", "custom_minvoice_id": "",
		"custom_hddt_id": "", "custom_hddt_thay_the": "", "docstatus": 1},
]


@ca("v536 tờ ERP phát hành kéo về thì nối ngay vào đơn: theo mã m-invoice, theo ký hiệu và số, không đoán khác ký hiệu")
def _noi_goc():
	to = {"id-14514": {"vgb_don_erp": ""}, "id-15500": {"vgb_don_erp": ""}, "id-fabi": {"vgb_don_erp": ""}}
	f, ghi = _nen_to(DON_GOC, to)
	with unittest.mock.patch.object(ds, "frappe", f), unittest.mock.patch.object(ds, "now_datetime", lambda: datetime.datetime(2026, 9, 29, 8, 0)):
		la("theo mã m-invoice", ds.noi_to_goc_tu_dong("id-14514", "C26MPV", 14514), "HDB-26-09-03253")
		la("theo ký hiệu và số", ds.noi_to_goc_tu_dong("id-15500", "C26MPV", "015500"), "HDB-26-09-09999")
		la("tờ Fabi không có đơn", ds.noi_to_goc_tu_dong("id-fabi", "C26MPV", 77777), "")
		la("khác ký hiệu không nối", ds.noi_to_goc_tu_dong("id-fabi", "C26MVO", 14514), "")
	la("ghi ô Đơn ERP đúng hai tờ", [g for g in ghi if g[0] != "cau"], [("id-14514", "HDB-26-09-03253"), ("id-15500", "HDB-26-09-09999")])
	# Bản giả tự chặn ghi đè; câu SQL thật cũng phải chặn, vì site chạy câu chứ không chạy bản giả.
	dung("câu update chỉ ghi khi ô trống", all("ifnull(vgb_don_erp, '') = ''" in g[1] for g in ghi if g[0] == "cau"))
	dung("ghi rõ lý do", "ERP phát hành" in to["id-14514"]["ly_do_bo_qua"])
	# Kế toán đã nối tay tờ đó vào đơn khác thì máy không ghi đè.
	to["id-tay"] = {"vgb_don_erp": "HDB-TAY"}
	with unittest.mock.patch.object(ds, "frappe", f), unittest.mock.patch.object(ds, "now_datetime", lambda: datetime.datetime(2026, 9, 29, 8, 0)):
		la("ô đã có thì thua", ds.ghi_don_erp_cua_to("id-tay", "HDB-26-09-09999"), False)
	la("giữ nối tay", to["id-tay"]["vgb_don_erp"], "HDB-TAY")


@ca("v536 nhịp kéo hoá đơn: tờ đầu ra do ERP xuất được nối đơn và ghi đúng lý do, không còn gắn cả lô là Fabi; không dựng chứng từ")
def _mot_to():
	# Codex #386 (P1, ab88967f): bản trước chạy thẳng _mot_to với tờ đầu ra, mà
	# trong nhịp thật tờ đầu ra KHÔNG BAO GIỜ tới _mot_to: _chay_trong_khoa đóng
	# dấu chúng ở _dong_dau_ra trước, hàng đợi dựng chỉ lấy đầu vào. Ca cũ xanh
	# trong khi tờ ERP vẫn bị gắn Fabi (điều 15). Ca này chạy ĐÚNG lối vào của
	# nhịp: _chay_trong_khoa, chỉ giả bảng và hàm nối. Đừng đổi về gọi _mot_to.
	from vagabond import minvoice_chung_tu as mc
	from vagabond import doi_soat_hddt_ra as ds2
	ghi = []
	to_ra = [_D(name="id-14514", loai=mc.LOAI_RA, ky_hieu="C26MPV", so_hd=14514),
		_D(name="id-fabi", loai=mc.LOAI_RA, ky_hieu="C26MPV", so_hd=1)]

	def get_all(dt, filters=None, **k):
		return list(to_ra) if (filters or {}).get("loai") == mc.LOAI_RA else []
	f = NS(get_all=get_all, db=NS(commit=lambda: None, rollback=lambda *a, **k: None),
		local=NS(message_log=[]), log_error=lambda *a, **k: None)
	with unittest.mock.patch.object(mc, "frappe", f), \
			unittest.mock.patch.object(mc, "_mo_lai_dau_sai", lambda *a: 0), \
			unittest.mock.patch.object(mc, "_ghi_xong", lambda ma, ly_do: ghi.append((ma, ly_do))), \
			unittest.mock.patch.object(mc, "dung_hoa_don_mua", lambda *a: (_ for _ in ()).throw(AssertionError("không được dựng"))), \
			unittest.mock.patch.object(ds2, "noi_to_goc_tu_dong", lambda ma, kh, so: "HDB-26-09-03253" if ma == "id-14514" else ""):
		kq = mc._chay_trong_khoa("2026-09-01", "2026-09-29")
	la("đóng dấu đủ hai tờ đầu ra", kq["dau_ra_dong_dau"], 2)
	la("lời ghi trên tờ", [(m, "ERP phát hành" in l, "Fabi" in l) for m, l in ghi],
		[("id-14514", True, False), ("id-fabi", False, True)])
	dung("tờ ERP ghi đúng đơn", "HDB-26-09-03253" in ghi[0][1])
	# _mot_to (đường chạy tay, tờ đầu ra lọt hàng đợi) dùng CHUNG phép đó.
	with unittest.mock.patch.object(mc, "khoi_dung_duoc", lambda tt: False), \
			unittest.mock.patch.object(mc, "_da_co_chung_tu", lambda ma: ""), \
			unittest.mock.patch.object(mc, "_ghi_xong", lambda ma, ly_do: ghi.append((ma, ly_do))), \
			unittest.mock.patch.object(mc, "frappe", NS(local=NS(message_log=[]))), \
			unittest.mock.patch.object(ds2, "noi_to_goc_tu_dong", lambda ma, kh, so: "HDB-26-09-03253" if ma == "id-14514" else ""):
		la("tờ ERP qua _mot_to: mã lý do riêng", mc._mot_to(to_ra[0]), (0, "dau_ra_erp"))
		la("tờ không đơn qua _mot_to", mc._mot_to(to_ra[1]), (0, "dau_ra_fabi"))
	dung("mã lý do ERP là bỏ qua hợp lệ", "dau_ra_erp" in mc.LY_DO_BO_QUA_HOP_LE)
	ma = (GOC / "minvoice_chung_tu.py").read_text(encoding="utf-8")
	dung("không còn chỗ nào tự ghi nhãn Fabi ngoài _xu_to_dau_ra",
		ma.count('_ghi_xong(ma, "Hoá đơn đầu ra') == 1 and '"Hoá đơn đầu ra do Fabi xuất' not in ma)


@ca("Codex #389 P1: tra đơn của tờ đầu ra hỏng thì KHÔNG đóng dấu Fabi, tờ nằm lại cho lượt sau thử lại")
def _tra_hong_thu_lai():
	# Đi đúng chuỗi của nhịp thật: noi_to_goc_tu_dong THẬT (chỉ giả frappe cho
	# câu tra ném lỗi), rồi _chay_trong_khoa. Không giả _xu_to_dau_ra.
	from vagabond import minvoice_chung_tu as mc
	from vagabond import doi_soat_hddt_ra as ds2
	log = []

	def ne(*a, **k):
		raise RuntimeError("mat ket noi")
	f_ds = NS(get_all=ne, log_error=lambda *a, **k: log.append(a[-1]), get_traceback=lambda: "")
	with unittest.mock.patch.object(ds2, "frappe", f_ds):
		la("tra hỏng trả None, không phải rỗng", ds2.noi_to_goc_tu_dong("id-14514", "C26MPV", 14514), None)
	dung("có ghi Error Log", any("id-14514" in str(x) for x in log))
	ghi = []
	to_ra = [_D(name="id-14514", loai=mc.LOAI_RA, ky_hieu="C26MPV", so_hd=14514),
		_D(name="id-fabi", loai=mc.LOAI_RA, ky_hieu="C26MPV", so_hd=1)]

	def get_all(dt, filters=None, **k):
		return list(to_ra) if (filters or {}).get("loai") == mc.LOAI_RA else []
	f = NS(get_all=get_all, db=NS(commit=lambda: None, rollback=lambda *a, **k: None),
		local=NS(message_log=[]), log_error=lambda *a, **k: None)
	with unittest.mock.patch.object(mc, "frappe", f), \
			unittest.mock.patch.object(mc, "_mo_lai_dau_sai", lambda *a: 0), \
			unittest.mock.patch.object(mc, "_ghi_xong", lambda ma, ly_do: ghi.append(ma)), \
			unittest.mock.patch.object(ds2, "noi_to_goc_tu_dong", lambda ma, kh, so: None if ma == "id-14514" else ""):
		kq = mc._chay_trong_khoa("2026-09-01", "2026-09-29")
	la("chỉ đóng dấu tờ tra được", ghi, ["id-fabi"])
	la("đếm đúng số tờ đã đóng dấu", kq["dau_ra_dong_dau"], 1)
	with unittest.mock.patch.object(mc, "khoi_dung_duoc", lambda tt: False), \
			unittest.mock.patch.object(mc, "_da_co_chung_tu", lambda ma: ""), \
			unittest.mock.patch.object(mc, "_ghi_xong", lambda ma, ly_do: ghi.append(ma)), \
			unittest.mock.patch.object(mc, "frappe", NS(local=NS(message_log=[]))), \
			unittest.mock.patch.object(ds2, "noi_to_goc_tu_dong", lambda ma, kh, so: None):
		la("qua _mot_to: báo lỗi, không đóng dấu", mc._mot_to(to_ra[0]), (0, "dau_ra_loi"))
	la("không thêm lần đóng dấu nào", ghi, ["id-fabi"])
	dung("dau_ra_loi không phải bỏ qua hợp lệ", "dau_ra_loi" not in mc.LY_DO_BO_QUA_HOP_LE)


@ca("Codex #389 P1: tệp danh mục rỗng hay bị loại hết thì không bật cấp mã; loại mã chưa có sàn thì không cấp")
def _nap_rong():
	la("tệp rỗng báo lỗi", bool(mk.loi_tep_danh_muc([])), True)
	la("tệp chỉ có mã riêng của Fast báo lỗi", bool(mk.loi_tep_danh_muc([{"ma": "CTY001", "mst": "0300000001"}, {"ma": "NV001"}])), True)
	la("tệp có mã KH hợp lệ thì nhận", mk.loi_tep_danh_muc([{"ma": "KH001588", "mst": ""}]), "")
	f, bang, vet, tao = _nen(dict((k, dict(v)) for k, v in KH.items()), da_nap="")
	f.get_roles = lambda: ["Accounts Manager"]
	with unittest.mock.patch.object(mk, "frappe", f):
		nem("nạp tệp rỗng bị chặn", lambda: mk.nap_danh_muc_fast("[]"), ValueError)
		nem("nạp tệp bị loại hết bị chặn", lambda: mk.nap_danh_muc_fast([{"ma": "CTY001", "mst": "0300000001"}]), ValueError)
	dung("cờ đã nạp vẫn tắt", f.db.get_default(mk.KHOA_DA_NAP) in ("", None))
	with unittest.mock.patch.object(mk, "frappe", f):
		la("chưa nạp thì không cấp", mk.cap_ma("Customer", "KH000015"), "")
	# Đã nạp tệp CHỈ có mã khách: khách được cấp, nhà cung cấp chưa có sàn thì chưa.
	with unittest.mock.patch.object(mk, "frappe", f), unittest.mock.patch.object(mk, "dien_ma_hang_loat", lambda: 0):
		mk.nap_danh_muc_fast([{"ma": "KH001588", "ten": "X", "mst": "0300001588"}])
	la("bật cờ khi tệp có mã hợp lệ", f.db.get_default(mk.KHOA_DA_NAP), "1")
	dung("chưa có sàn NC", not f.db.get_default(mk.KHOA_SAN + "NC"))
	with unittest.mock.patch.object(mk, "frappe", f):
		la("NCC chưa có sàn thì không cấp", mk.cap_ma("Supplier", "NCC-A"), "")


@ca("Codex #389 P1 vòng 2: tệp Fast có dòng lặp thì xử một lần; một MST mang hai mã thì là xung đột, không ghi gì cho MST đó")
def _trung_mst():
	kh = mk.ke_hoach_nap([
		{"ma": "KH000300", "ten": "Mới", "mst": "0300000300"},
		{"ma": "KH000300", "ten": "Mới", "mst": "0300000300"},
		{"ma": "KH000401", "ten": "A", "mst": "0300000401"},
		{"ma": "KH000402", "ten": "A lặp mã", "mst": "0300000401"},
	], {"Customer": {}})
	la("dòng lặp y hệt chỉ tạo một lần", [d["ma"] for d in kh["tao_moi"]], ["KH000300"])
	la("MST hai mã: một xung đột, nêu đủ hai mã", [(d["mst"], "KH000401" in d["ly_do"] and "KH000402" in d["ly_do"]) for d in kh["xung_dot"]],
		[("0300000401", True)])
	kh = mk.ke_hoach_nap([{"ma": "KH000401", "mst": "0300000401"}, {"ma": "KH000402", "mst": "0300000401"}],
		{"Customer": {"0300000401": {"name": "C-A", "ma": ""}}})
	la("MST hai mã không cập nhật bản ghi đang có", kh["cap_nhat"], [])
	# Codex #389 P2 vòng 3: một mã gắn hai MST thì cả hai dòng đều không ghi, dù dòng nào đứng trước.
	for thu_tu in (0, 1):
		dong = [{"ma": "KH000500", "mst": "0300000501"}, {"ma": "KH000500", "mst": "0300000502"}]
		kh = mk.ke_hoach_nap(dong[::-1] if thu_tu else dong, {"Customer": {"0300000501": {"name": "C-1", "ma": ""}}})
		la("mã hai MST: không ghi gì (thứ tự %d)" % thu_tu, (kh["tao_moi"], kh["cap_nhat"]), ([], []))
		la("mã hai MST: một xung đột nêu đủ MST (thứ tự %d)" % thu_tu,
			[("0300000501" in d["ly_do"] and "0300000502" in d["ly_do"]) for d in kh["xung_dot"]], [True])


@ca("Codex #389 P1 vòng 3: nối tờ theo ký hiệu và số chỉ khi DUY NHẤT; trùng số qua năm hay qua ký hiệu thì để người nối")
def _so_duy_nhat():
	c = ds.chon_don_duy_nhat
	la("một đơn đúng ký hiệu", c([{"name": "A", "custom_hddt_ky_hieu": "1C26MPV"}], "C26MPV"), "A")
	la("hai đơn cùng ký hiệu cùng số: không nối", c([{"name": "A", "custom_hddt_ky_hieu": "1C26MPV"},
		{"name": "B", "custom_hddt_ky_hieu": "1C26MPV"}], "C26MPV"), "")
	la("đúng ký hiệu thắng đơn cũ ký hiệu trống", c([{"name": "CU", "custom_hddt_ky_hieu": ""},
		{"name": "A", "custom_hddt_ky_hieu": "1C26MPV"}], "C26MPV"), "A")
	la("khác năm không nối", c([{"name": "A", "custom_hddt_ky_hieu": "1C25MPV"}], "C26MPV"), "")
	la("hai đơn cũ ký hiệu trống: không nối", c([{"name": "X", "custom_hddt_ky_hieu": ""},
		{"name": "Y", "custom_hddt_ky_hieu": None}], "C26MPV"), "")
	la("một đơn cũ ký hiệu trống", c([{"name": "X", "custom_hddt_ky_hieu": ""}], "C26MPV"), "X")
	# Qua hàm chạm hệ THẬT: đọc đủ ứng viên (không cắt 5 dòng) rồi mới chọn.
	hoi = []

	def get_all(dt, filters=None, fields=None, limit_page_length=0, **k):
		hoi.append(limit_page_length)
		if "custom_hddt_so" in (filters or {}):
			return [_D(name="HDB-2025", custom_hddt_ky_hieu="1C25MPV"), _D(name="HDB-A", custom_hddt_ky_hieu="1C26MPV"),
				_D(name="HDB-B", custom_hddt_ky_hieu="1C26MPV")]
		return []
	with unittest.mock.patch.object(ds, "frappe", NS(get_all=get_all)):
		la("trùng số trong cùng ký hiệu: rỗng", ds.don_cua_to_goc("id-x", "C26MPV", 14514), "")
	dung("đọc đủ ứng viên, không cắt", hoi[-1] == 0)


@ca("Codex #389 P1 vòng 2: lọc chỉ tờ chưa nối xét CẢ ba đường tra đơn trên cả kỳ rồi mới cắt TOI_DA")
def _chua_noi_truoc_cat():
	bc = _bao_cao()
	# 5 tờ đầu kỳ ô Đơn ERP trống nhưng tra theo số ra đơn (đã nối gián tiếp), tờ cuối kỳ chưa nối thật.
	TO = [_D(name="id-%d" % i, so_hd=100 + i, ky_hieu="C26MPV", ngay_lap=datetime.date(2026, 9, i), nguoi_mua_ban="Khách lẻ",
		mst_doi_tac="", trang_thai="Gốc", hd_goc="", vgb_don_erp="") for i in range(1, 6)]
	TO.append(_D(name="id-cuoi", so_hd=999, ky_hieu="C26MPV", ngay_lap=datetime.date(2026, 9, 29), nguoi_mua_ban="Khách lẻ",
		mst_doi_tac="", trang_thai="Gốc", hd_goc="", vgb_don_erp=""))

	def get_all(dt, filters=None, **k):
		if dt == "Sales Invoice" and "custom_hddt_so" in (filters or {}):
			return [_D(name="HDB-%d" % i, custom_hddt_so=str(100 + i), custom_hddt_ky_hieu="1C26MPV") for i in range(1, 6)]
		return []
	f = NS(get_list=lambda dt, **k: _loc_ten(TO, k), get_all=get_all, throw=_throw)
	with unittest.mock.patch.object(bc, "frappe", f), unittest.mock.patch.object(mk, "frappe", f), \
			unittest.mock.patch.object(bc, "TOI_DA", 2):
		_, rows, msg = bc.execute({"tu_ngay": "2026-09-01", "den_ngay": "2026-09-30", "chi_chua_noi": 1})
	la("chỉ tờ chưa nối thật, dù nằm cuối kỳ", [r["so_hd"] for r in rows], ["999"])
	dung("không báo quá nhiều tờ khi thật ra chỉ có một", "Quá" not in msg)


# ------------------------------------------------------------- sổ hoá đơn

def _bao_cao():
	import importlib
	return importlib.import_module("vagabond.vagabond.report.so_hoa_don_dien_tu_ban_ra.so_hoa_don_dien_tu_ban_ra")


@ca("v536 sổ HĐĐT bán ra: mỗi tờ một dòng đúng số, ký hiệu, ngày, tên, trạng thái, tờ gốc, mã khách KT; tờ 14576 tìm ra")
def _so():
	bc = _bao_cao()
	to = {"name": "id-14576", "so_hd": 14576, "ky_hieu": "C26MPV", "ngay_lap": "2026-09-18", "nguoi_mua_ban": "OLIVER MARKETING",
		"mst_doi_tac": "0317064683", "tien_truoc_thue": 32086610, "tien_thue": 2566929, "tong_tien": 34653539,
		"trang_thai": "Thay thế", "hd_goc": "KH C26MPV - So 14514 - Ngay 2026-09-16", "vgb_don_erp": "", "ma_cqt": "M1-26-ABC", "ngay_ky": "2026-09-18"}
	r = bc.dong_so(to, {"0317064683": "KH000015"}, lambda t: ("HDB-26-09-03253", "thay thế"))
	la("dòng sổ", (r["so_hd"], r["ky_hieu"], r["ngay_lap"], r["nguoi_mua_ban"], r["trang_thai"], r["to_goc"], r["ma_khach"], r["don_erp"], r["cach_noi"], r["tong_tien"]),
		("14576", "C26MPV", "2026-09-18", "OLIVER MARKETING", "Thay thế", "14514", "KH000015", "HDB-26-09-03253", "thay thế", 34653539))
	r = bc.dong_so(dict(to, mst_doi_tac="", hd_goc=""), {}, lambda t: ("", ""))
	la("khách lẻ", (r["ma_khach"], r["to_goc"], r["don_erp"]), ("KL0001", "", ""))
	r = bc.dong_so(to, {}, lambda t: ("", ""))
	la("có MST chưa có mã: nói rõ, không ghi MST vào cột mã", r["ma_khach"], "(chưa có mã)")
	cot = [c["fieldname"] for c in bc.cot()]
	for c in ("so_hd", "ky_hieu", "ngay_lap", "nguoi_mua_ban", "trang_thai", "ma_khach", "don_erp", "to_goc", "mst_doi_tac"):
		dung("có cột " + c, c in cot)


def _loc_ten(to_ds, k):
	"""get_list giả: giữ lọc theo tên và giới hạn dòng như site thật, vì bộ lọc
	của sổ giờ đi hai bước (tra nhẹ rồi đọc đủ theo tên), Codex #389."""
	ra = list(to_ds)
	ten = ((k.get("filters") or {}).get("name") or [None, None])[1]
	if ten is not None:
		ra = [t for t in ra if t["name"] in ten]
	n = k.get("limit_page_length") or 0
	return ra[:n] if n else ra


@ca("Codex #389 P1: sổ HĐĐT lọc người mua và mã khách trên CẢ kỳ rồi mới cắt TOI_DA; lời báo quá nhiều tờ không mất")
def _so_loc_truoc_cat():
	bc = _bao_cao()
	TO = [_D(name="id-%d" % i, so_hd=i, ky_hieu="C26MPV", ngay_lap=datetime.date(2026, 9, i), nguoi_mua_ban="Khách lẻ",
		mst_doi_tac="", trang_thai="Gốc", hd_goc="", vgb_don_erp="HDB-%d" % i) for i in range(1, 6)]
	TO.append(_D(name="id-cuoi", so_hd=99, ky_hieu="C26MPV", ngay_lap=datetime.date(2026, 9, 29), nguoi_mua_ban="OLIVER MARKETING",
		mst_doi_tac="0317064683", trang_thai="Gốc", hd_goc="", vgb_don_erp="HDB-99"))

	def get_all(dt, filters=None, **k):
		return [_D(tax_id="0317064683", custom_ma_khach="KH000015")] if dt == "Customer" else []
	f = NS(get_list=lambda dt, **k: _loc_ten(TO, k), get_all=get_all, throw=_throw)
	ky = {"tu_ngay": "2026-09-01", "den_ngay": "2026-09-30"}
	with unittest.mock.patch.object(bc, "frappe", f), unittest.mock.patch.object(mk, "frappe", f), \
			unittest.mock.patch.object(bc, "TOI_DA", 2):
		_, rows, msg = bc.execute(dict(ky, nguoi_mua="oliver"))
		la("tờ cuối kỳ vẫn tìm ra theo tên", [r["so_hd"] for r in rows], ["99"])
		_, rows, _ = bc.execute(dict(ky, nguoi_mua="0317064683"))
		la("tờ cuối kỳ vẫn tìm ra theo MST", [r["so_hd"] for r in rows], ["99"])
		_, rows, _ = bc.execute(dict(ky, ma_khach="KH000015"))
		la("tờ cuối kỳ vẫn tìm ra theo mã khách", [r["so_hd"] for r in rows], ["99"])
		_, rows, msg = bc.execute(dict(ky, ma_khach="kl0001"))
		la("lọc mã khách cắt đúng TOI_DA + 1", len(rows), 3)
		dung("còn lời báo quá nhiều tờ khi đã lọc", "Quá 2 tờ" in msg)
		_, rows, msg = bc.execute(ky)
		dung("còn lời báo khi không lọc", "Quá 2 tờ" in msg)


@ca("v536 sổ HĐĐT bán ra trên site: đọc bảng tờ, tra đơn ba đường, lọc theo tên hoặc MST và theo mã khách, đếm tờ thiếu mã")
def _so_site():
	bc = _bao_cao()
	TO = [
		_D(name="id-14576", so_hd=14576, ky_hieu="C26MPV", ngay_lap=datetime.date(2026, 9, 18), nguoi_mua_ban="OLIVER MARKETING",
			mst_doi_tac="0317064683", trang_thai="Thay thế", hd_goc="KH C26MPV - So 14514 - Ngay 2026-09-16", vgb_don_erp=""),
		_D(name="id-15500", so_hd=15500, ky_hieu="C26MPV", ngay_lap=datetime.date(2026, 9, 22), nguoi_mua_ban="Khách lẻ",
			mst_doi_tac="", trang_thai="Gốc", hd_goc="", vgb_don_erp=""),
		_D(name="id-tay", so_hd=15600, ky_hieu="C26MPV", ngay_lap=datetime.date(2026, 9, 22), nguoi_mua_ban="CTY B",
			mst_doi_tac="0300000002", trang_thai="Gốc", hd_goc="", vgb_don_erp="HDB-TAY"),
	]
	hoi = []

	def get_all(dt, filters=None, fields=None, limit_page_length=0, **k):
		hoi.append((dt, filters))
		if dt == "Sales Invoice":
			if "custom_hddt_thay_the" in filters:
				return [_D(name="HDB-26-09-03253", custom_hddt_thay_the="1C26MPV 14576")]
			if "custom_hddt_so" in filters:
				return [_D(name="HDB-26-09-09999", custom_hddt_so="15500", custom_hddt_ky_hieu="1C26MPV")]
			return []
		if dt == "Customer":
			return [_D(tax_id="0317064683", custom_ma_khach="KH000015")]
		return []
	f = NS(get_list=lambda dt, **k: _loc_ten(TO, k), get_all=get_all, throw=_throw)
	with unittest.mock.patch.object(bc, "frappe", f), unittest.mock.patch.object(mk, "frappe", f):
		cot, rows, msg = bc.execute({"tu_ngay": "2026-09-01", "den_ngay": "2026-09-30"})
		la("ba dòng, ba cách nối", [(r["so_hd"], r["don_erp"], r["cach_noi"]) for r in rows],
			[("14576", "HDB-26-09-03253", "thay thế"), ("15500", "HDB-26-09-09999", "ERP xuất"), ("15600", "HDB-TAY", "đã nối")])
		la("mã khách", [r["ma_khach"] for r in rows], ["KH000015", "KL0001", "(chưa có mã)"])
		dung("đếm tờ thiếu mã", "1 tờ có MST" in msg)
		_, rows, _ = bc.execute({"tu_ngay": "2026-09-01", "den_ngay": "2026-09-30", "nguoi_mua": "oliver"})
		la("lọc theo tên", [r["so_hd"] for r in rows], ["14576"])
		_, rows, _ = bc.execute({"tu_ngay": "2026-09-01", "den_ngay": "2026-09-30", "nguoi_mua": "0317064683"})
		la("lọc theo MST", [r["so_hd"] for r in rows], ["14576"])
		_, rows, _ = bc.execute({"tu_ngay": "2026-09-01", "den_ngay": "2026-09-30", "ma_khach": "kl0001"})
		la("lọc theo mã khách", [r["so_hd"] for r in rows], ["15500"])
		nem("từ ngày sau đến ngày", lambda: bc.execute({"tu_ngay": "2026-09-30", "den_ngay": "2026-09-01"}), ValueError)
	dung("bảng tra thay thế chỉ đọc đơn từ 120 ngày trước tờ sớm nhất",
		any(h[0] == "Sales Invoice" and "custom_hddt_thay_the" in h[1] and h[1]["posting_date"][1] == datetime.date(2026, 5, 21) for h in hoi))


# ------------------------------------------------------- khai báo và hook

@ca("v536 khai báo: hook nối vào chuỗi cũ (validate hoá đơn bán đặt cuối; khách và NCC khi lưu), không hook '*'; ô mới; báo cáo có vai; patch có dòng")
def _khai():
	g = {}
	ma = (GOC / "hooks.py").read_text(encoding="utf-8")
	exec(compile(ma, "hooks.py", "exec"), g)
	de = g["doc_events"]
	la("validate hoá đơn bán: hàm cuối chuỗi", de["Sales Invoice"]["validate"][-1], "vagabond.ma_ke_toan.dien_ma_khach_hoa_don")
	dung("chuỗi validate cũ còn nguyên", "vagabond.ban_hang.kiem_truoc_khi_luu" in de["Sales Invoice"]["validate"]
		and "vagabond.thanh_toan_nhieu.dat_pt_chinh" in de["Sales Invoice"]["validate"])
	for dt in ("Customer", "Supplier"):
		for sk in ("after_insert", "on_update"):
			dung("%s %s" % (dt, sk), "vagabond.ma_ke_toan.cap_ma_khi_luu" in de[dt][sk])
	la("autoname khách giữ nguyên", de["Customer"]["autoname"], "vagabond.ma_khach.dat_ma")
	dung("không hook '*'", "ma_ke_toan" not in str(de.get("*", {})))
	o = mk.TRUONG_MOI["Sales Invoice"][0]
	la("ô mới chỉ đọc, lọc được", (o["fieldname"], o["read_only"], o["in_standard_filter"]), ("vgb_ma_khach_ke_toan", 1, 1))
	tt = (GOC / "truong_tu_them.py").read_text(encoding="utf-8")
	dung("truong_tu_them dựng nhóm ma_ke_toan", '_dung_nhom(ma_ke_toan.TRUONG_MOI, "ma_ke_toan")' in tt)
	import json
	bc = json.loads((GOC / "vagabond/report/so_hoa_don_dien_tu_ban_ra/so_hoa_don_dien_tu_ban_ra.json").read_text(encoding="utf-8"))
	vai = {r["role"] for r in bc["roles"]}
	dung("kế toán và AP FIN xem được sổ", {"Accounts User", "Accounts Manager", "AP Kiểm soát (FIN)"} <= vai)
	la("báo cáo trên bảng tờ, không phải trên đơn", bc["ref_doctype"], "MInvoice Invoice")
	dong = (GOC / "patches.txt").read_text(encoding="utf-8").splitlines()
	dung("patch v536 đứng trước dòng đồng bộ cấu trúc v536",
		dong.index("vagabond.patches.ma_ke_toan_v536") < max(i for i, d in enumerate(dong) if d.startswith("vagabond.patches.dong_bo_cau_truc #v")))
	# Ô Đơn ERP trên tờ nay lọc được ngay trên danh sách.
	o = next(x for x in ds.TRUONG_MOI["MInvoice Invoice"] if x["fieldname"] == "vgb_don_erp")
	la("ô Đơn ERP lọc được, nhãn không còn 'nối tay'", (o.get("in_standard_filter"), o["label"]), (1, "Đơn ERP"))


@ca("v536 patch: dựng ô rồi điền hoá đơn, nối tờ đầu ra chưa có đơn khi tìm ra đúng MỘT đơn, bỏ qua tờ nhiều ứng viên; bench thiếu bảng thì dừng êm")
def _patch():
	import importlib
	p = importlib.import_module("vagabond.patches.ma_ke_toan_v536")
	vet = []
	TO = [_D(name="id-14514", ky_hieu="C26MPV", so_hd=14514), _D(name="id-14576", ky_hieu="C26MPV", so_hd=14576),
		_D(name="id-doi", ky_hieu="C26MPV", so_hd=15500), _D(name="id-fabi", ky_hieu="C26MPV", so_hd=1)]
	DON = [
		_D(name="HDB-A", custom_minvoice_id="id-14514", custom_hddt_id="", custom_hddt_so="14514", custom_hddt_ky_hieu="1C26MPV", custom_hddt_thay_the="1C26MPV 14576"),
		_D(name="HDB-B", custom_minvoice_id="", custom_hddt_id="", custom_hddt_so="15500", custom_hddt_ky_hieu="1C26MPV", custom_hddt_thay_the=""),
		_D(name="HDB-C", custom_minvoice_id="", custom_hddt_id="", custom_hddt_so="15500", custom_hddt_ky_hieu="1C26MPV", custom_hddt_thay_the=""),
	]

	def get_all(dt, filters=None, fields=None, limit_page_length=0, **k):
		if dt == "MInvoice Invoice":
			return list(TO)
		if "custom_hddt_thay_the" in filters:
			return [d for d in DON if d.custom_hddt_thay_the]
		if "custom_hddt_so" in filters:
			return [d for d in DON if d.custom_hddt_so]
		return [d for d in DON if d.custom_minvoice_id or d.custom_hddt_id]
	noi = []
	f_frappe = NS(db=NS(updatedb=lambda dt: vet.append(("cot", dt)), exists=lambda *a: True, has_column=lambda *a: True,
			commit=lambda: vet.append(("commit",))), get_all=get_all, logger=lambda *a: NS(info=lambda m: vet.append(("log", m))))
	import sys
	cf = NS(create_custom_fields=lambda khai, update=True: vet.append(("truong", sorted(khai))))
	mod = NS(custom=NS(doctype=NS(custom_field=NS(custom_field=cf))))
	with unittest.mock.patch.dict(sys.modules, {"frappe": f_frappe, "frappe.custom": mod.custom, "frappe.custom.doctype": mod.custom.doctype,
			"frappe.custom.doctype.custom_field": mod.custom.doctype.custom_field, "frappe.custom.doctype.custom_field.custom_field": cf}), \
			unittest.mock.patch.object(mk, "dien_ma_hang_loat", lambda: vet.append(("dien",)) or 3), \
			unittest.mock.patch.object(ds, "ghi_don_erp_cua_to", lambda to, don, ghi_chu="": noi.append((to, don)) or True):
		p.execute()
	la("dựng ô trước, cột trong bảng, rồi điền", vet[:3], [("truong", ["Sales Invoice"]), ("cot", "Sales Invoice"), ("dien",)])
	la("nối đúng hai tờ: theo mã, theo ô thay thế; tờ hai ứng viên và tờ Fabi để trống",
		noi, [("id-14514", "HDB-A"), ("id-14576", "HDB-A")])
	dung("ghi số liệu vào log", any(v[0] == "log" and "noi 2/4" in v[1] for v in vet))
	# Bench mới: chưa có ô Đơn ERP thì dừng sau phần hoá đơn, không nổ.
	vet.clear(); noi.clear()
	f_frappe.db.has_column = lambda dt, c: c != "vgb_don_erp"
	with unittest.mock.patch.dict(sys.modules, {"frappe": f_frappe, "frappe.custom.doctype.custom_field.custom_field": cf}), \
			unittest.mock.patch.object(mk, "dien_ma_hang_loat", lambda: 0), \
			unittest.mock.patch.object(ds, "ghi_don_erp_cua_to", lambda *a, **k: noi.append(a) or True):
		p.execute()
	la("không nối gì, vẫn commit", (noi, ("commit",) in vet), ([], True))


# --------------------------------------------- Codex #383 vòng 1, ba finding P1

@ca("Codex #383 F1: nạp tệp với tao_moi=0, mã Fast lớn nhất chưa có bản ghi ERP vẫn được giữ làm sàn, mã máy cấp sau đó không trùng Fast")
def _f1_san_fast():
	# ERP chỉ có mã tới KH000200; tệp Fast có KH001588 gắn MST chưa có trong ERP
	# và người nạp chọn tao_moi=0 (bỏ qua). Trước sửa: cờ đã nạp bật, máy cấp
	# KH000201 cho khách mới, trùng với KH000201 đang tồn tại bên Fast.
	khach = {"DN000002": {"customer_name": "Sỉ B", "tax_id": "0300000002", "custom_ma_khach": "KH000200"},
		"KH000015": {"customer_name": "Oliver", "tax_id": "0317064683", "custom_ma_khach": ""}}
	f, bang, vet, tao = _nen(khach, da_nap="")
	with unittest.mock.patch.object(mk, "frappe", f), unittest.mock.patch.object(mk, "dien_ma_hang_loat", lambda: 0):
		kq = mk.nap_danh_muc_fast([{"ma": "KH001588", "ten": "Chưa có trong ERP", "mst": "0300009999"},
			{"ma": "NC000504", "ten": "NCC Fast", "mst": "0300008888"}], tao_moi=0)
		la("dòng bị bỏ qua vì tao_moi=0", kq["chua_tao"], 2)
		ma = mk.cap_ma("Customer", "KH000015")
		la("mã cấp sau khi nạp phải vượt sàn Fast KH001588", ma, "KH001589")
		bang["Supplier"]["NCC-MOI"] = {"tax_id": "0300007777", "custom_ma_ncc": ""}
		la("sàn NC cũng giữ", mk.cap_ma("Supplier", "NCC-MOI"), "NC000505")
	la("sàn ghi vào mặc định toàn site", (f.db.get_default(mk.KHOA_SAN + "KH"), f.db.get_default(mk.KHOA_SAN + "NC")), ("1588", "504"))


@ca("Codex #383 F2: khoá cấp mã giữ tới lúc commit, không nhả trong hàm; get_lock trả 0 thì không cấp")
def _f2_khoa():
	f, bang, vet, tao = _nen(dict((k, dict(v)) for k, v in KH.items()))
	with unittest.mock.patch.object(mk, "frappe", f):
		la("cấp được", mk.cap_ma("Customer", "KH000015"), "KH001589")
		dung("trong hàm KHÔNG nhả khoá", not any(v[0] == "sql" and "release" in v[1] for v in vet))
		sau_commit = [v[1] for v in vet if v[0] == "sau_commit"]
		sau_rollback = [v[1] for v in vet if v[0] == "sau_rollback"]
		la("đăng ký nhả khoá sau commit và sau rollback", (len(sau_commit), len(sau_rollback)), (1, 1))
		sau_commit[0]()
		dung("nhả khoá khi commit", any(v[0] == "sql" and "release" in v[1] for v in vet))
	# Khoá không lấy được (đang có lượt khác giữ quá 10 giây): không cấp, không ghi.
	f2, bang2, vet2, _ = _nen(dict((k, dict(v)) for k, v in KH.items()))
	sql_cu = f2.db.sql

	def sql_khong_khoa(q, a=None, **k):
		if "get_lock" in q:
			return [(0,)]
		return sql_cu(q, a, **k)
	f2.db.sql = sql_khong_khoa
	with unittest.mock.patch.object(mk, "frappe", f2):
		d = _D(name="HDB-9", customer="KL042334", vgb_xhd_mst="0317064683")
		mk.dien_ma_khach_hoa_don(d)
	la("không lấy được khoá: để trống, không ghi mã", (d.get("vgb_ma_khach_ke_toan"), bang2["Customer"]["KH000015"]["custom_ma_khach"]), (None, ""))
	dung("lỗi vào Error Log", any(v[0] == "log" for v in vet2))


@ca("Codex #383 F3: patch đọc tờ đang trống ô Đơn ERP bằng 'is not set' để bắt cả NULL")
def _f3_null():
	import importlib
	import sys
	p = importlib.import_module("vagabond.patches.ma_ke_toan_v536")
	hoi = []

	def get_all(dt, filters=None, fields=None, limit_page_length=0, **k):
		hoi.append((dt, filters))
		return []
	f_frappe = NS(db=NS(updatedb=lambda dt: None, exists=lambda *a: True, has_column=lambda *a: True, commit=lambda: None),
		get_all=get_all, logger=lambda *a: NS(info=lambda m: None))
	cf = NS(create_custom_fields=lambda khai, update=True: None)
	with unittest.mock.patch.dict(sys.modules, {"frappe": f_frappe, "frappe.custom.doctype.custom_field.custom_field": cf}), \
			unittest.mock.patch.object(mk, "dien_ma_hang_loat", lambda: 0):
		p.execute()
	loc = [h[1] for h in hoi if h[0] == "MInvoice Invoice"]
	la("một câu đọc tờ", len(loc), 1)
	la("lọc ô trống bắt cả NULL", loc[0].get("vgb_don_erp"), ["is", "not set"])

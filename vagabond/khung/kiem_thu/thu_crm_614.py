# -*- coding: utf-8 -*-
"""v614: phân hệ Khách hàng (CRM) đợt 1.

Anh Việt 27/10/2026 duyệt 8 màn mẫu và phương án đã qua Codex rà (PR #503).
Năm điểm Codex nêu được chốt ở đây bằng hàm THẬT của vagabond/crm.py:
  1. chỉ khách đã đồng ý đúng kênh và không nằm trong Danh sách không quảng
     cáo mới vào danh sách gọi; mọi lần đổi đồng ý có dòng nhật ký;
  2. kênh Zalo OA hàng loạt không có trong đợt 1;
  3. lọc theo món chỉ đọc hoá đơn ERP, nhóm Fabi đoán từ ngày cuối;
  4. tiền ERP và tiền Fabi không cộng lẫn;
  5. đối chứng chia ngẫu nhiên, lặp lại được, khoá cố định lúc chốt; đo bằng
     bình quân mỗi khách.

Phần chạm hệ chạy trên lớp Frappe giả của nen.py, mỗi ca vá đúng những lời gọi
cơ sở dữ liệu mà hàm thật dùng. Không gọi thêm hàm nội bộ nào "cho chắc"
(điều 15). Câu SQL thật chạy ở ca tích hợp kiem_that/thu_crm_614.py.
"""

import datetime as dt
import io
import json
import os
import re
import types
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()

from vagabond import crm  # noqa: E402

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HN = dt.date(2026, 10, 27)


class D(dict):
	__getattr__ = dict.get

	def __setattr__(self, k, v):
		self[k] = v

	def as_dict(self):
		return dict(self)


def _nen_ban():
	"""crm gọi la_khach_gop của khach_hang, mô đun đó kéo ban_hang và requests.

	CI chạy tay không (không có requests, CLAUDE.md "giả lập CI tay không"). Chỉ
	khi thiếu requests mới mượn một mô đun rỗng, và patch.dict trả sys.modules
	về nguyên trạng sau ca, để không ca nào khác thấy requests giả này.
	"""
	import contextlib
	import sys

	try:
		import requests  # noqa: F401
		return contextlib.nullcontext()
	except ImportError:
		pass

	@contextlib.contextmanager
	def muon():
		import vagabond

		goc = dict(sys.modules)
		thuoc_tinh = set(vars(vagabond))
		sys.modules["requests"] = types.ModuleType("requests")
		try:
			yield
		finally:
			# Gỡ cả mô đun lẫn thuộc tính gói vừa nạp: "from vagabond import
			# ban_hang" ở ca sau phải thấy đúng cảnh CI thật (không nạp được).
			for k in set(sys.modules) - set(goc):
				del sys.modules[k]
			sys.modules.update(goc)
			for k in set(vars(vagabond)) - thuoc_tinh:
				delattr(vagabond, k)

	return muon()


# ------------------------------------------------------------ xếp nhóm

@ca("v614 xếp nhóm: sáu nhóm theo đúng thứ tự ưu tiên, ranh giới 90 và 365 ngày")
def _xep_nhom():
	n = lambda so, dau, cuoi: crm.xep_nhom(so, dau, cuoi, HN)
	la("chưa có ngày mua", n(0, None, None), "Chưa mua")
	la("một đơn 90 ngày trước vẫn là Mới", n(1, "2026-07-29", "2026-07-29"), "Mới")
	la("một đơn 91 ngày trước không còn Mới", n(1, "2026-07-28", "2026-07-28"), "Sắp rời đi")
	la("nhiều đơn, mua 30 ngày trước", n(5, "2025-01-01", "2026-09-27"), "Trung thành")
	# nhịp 200 ngày: ngưỡng 300 ngày, mua 250 ngày trước vẫn trung thành
	la("nhịp dài: chưa quá 1,5 lần nhịp", n(3, "2025-02-13", "2026-02-19"), "Trung thành")
	la("quá một năm", n(8, "2023-01-01", "2025-10-26"), "Đã ngủ")
	la("đúng 365 ngày chưa ngủ, ít đơn ngoài mùa lễ", n(2, "2025-05-01", "2025-10-27"), "Sắp rời đi")
	la("ít đơn, lần cuối tháng 1", n(2, "2025-12-20", "2026-01-15"), "Chỉ mua dịp lễ")
	la("ít đơn, lần cuối tháng 9 (Trung thu)", n(3, "2025-09-10", "2026-05-02"), "Sắp rời đi")
	la("nhiều đơn lần cuối tháng 12 vẫn là sắp rời đi", n(9, "2025-01-01", "2025-12-24"), "Sắp rời đi")
	la("nhịp", crm.nhip_ngay(3, "2026-01-01", "2026-01-21"), 10)
	la("một đơn chưa có nhịp", crm.nhip_ngay(1, "2026-01-01", "2026-01-01"), 0)


@ca("v614 gộp lượt mua ERP và Fabi: cộng số đơn và lấy ngày rộng nhất, KHÔNG cộng tiền (Codex PR #503)")
def _gop_mua():
	g = crm.gop_mua({"so_don": 2, "tien": 900000, "lan_dau": "2026-08-10", "lan_cuoi": "2026-10-01"},
		{"so_don": 23, "tien": 18540000, "lan_dau": "2022-05-03", "lan_cuoi": "2026-07-30"})
	la("gộp", g, {"so_don": 25, "lan_dau": dt.date(2022, 5, 3), "lan_cuoi": dt.date(2026, 10, 1)})
	dung("không có khoá tiền", "tien" not in g)
	la("chỉ Fabi", crm.gop_mua({}, {"so_don": 1, "lan_dau": "2025-12-24", "lan_cuoi": "2025-12-24"})["lan_cuoi"], dt.date(2025, 12, 24))
	la("trống cả hai", crm.gop_mua(None, None), {"so_don": 0, "lan_dau": None, "lan_cuoi": None})


@ca("v614 dịp đã mua và sinh nhật")
def _dip():
	la("tháng 9, 12, 2", crm.dip_tu_thang([9, 12, 2]), ["Trung thu", "Giáng sinh", "Tết"])
	la("sinh nhật trùng tháng đã mua", crm.dip_tu_thang([3, 5], 3), ["Sinh nhật"])
	la("không trùng thì không có", crm.dip_tu_thang([5], 3), [])


# ------------------------------------------------------------ đồng ý

@ca("v614 đồng ý: ô trống là chưa hỏi, im lặng không phải đồng ý")
def _dong_y():
	la("trống", crm.chuan_dong_y(None), "Chưa hỏi")
	la("chữ lạ", crm.chuan_dong_y("ok"), "Chưa hỏi")
	la("đồng ý", crm.chuan_dong_y(" Đồng ý "), "Đồng ý")
	dung("chưa hỏi cả hai kênh thì quầy hỏi", crm.can_hoi({"dy_zalo": "", "dy_goi": None}))
	dung("đã từ chối gọi thì không hỏi lại", not crm.can_hoi({"dy_goi": "Từ chối"}))
	dung("đã đồng ý Zalo thì không hỏi lại", not crm.can_hoi({"dy_zalo": "Đồng ý"}))
	la("chỉ kênh đổi mới ghi nhật ký", crm.doi_dong_y(
		{"Zalo": "Đồng ý", "Gọi điện": "Chưa hỏi", "Email": "Từ chối"},
		{"Zalo": "Đồng ý", "Gọi điện": "Đồng ý", "Email": "Chưa hỏi"}), [("Gọi điện", "Đồng ý")])
	la("chưa hỏi không xoá đồng ý cũ", crm.doi_dong_y({"Zalo": "Đồng ý"}, {"Zalo": "Chưa hỏi"}), [])
	la("kênh được liên hệ", crm.kenh_duoc_lien_he({"dy_goi": "Đồng ý", "dy_zalo": "Từ chối"}, ["Gọi điện", "Zalo"]), ["Gọi điện"])
	dung("câu hỏi quầy không xưng em", not re.search(r"\bem\b", crm.CAU_HOI_DONG_Y))


# ------------------------------------------------------------ đối chứng

@ca("v614 đối chứng: 10% làm tròn nửa lên, dưới 10 khách không giữ, trần 50%")
def _so_dc():
	la("1.254 khách", crm.so_doi_chung(1254, 10), 125)
	la("15 khách", crm.so_doi_chung(15, 10), 2)
	la("9 khách không giữ", crm.so_doi_chung(9, 10), 0)
	la("tỉ lệ 0", crm.so_doi_chung(500, 0), 0)
	la("trần 50%", crm.so_doi_chung(100, 90), 50)


@ca("v614 chia đối chứng: ngẫu nhiên nhưng lặp lại được theo mã chiến dịch, không phụ thuộc thứ tự đọc")
def _chia_dc():
	ds = ["KH%04d" % i for i in range(1254)]
	n1, d1 = crm.chia_doi_chung(ds, 10, "CD-26-0001")
	n2, d2 = crm.chia_doi_chung(list(reversed(ds)), 10, "CD-26-0001")
	la("cùng hạt giống, khác thứ tự đọc: y hệt", (n1, d1), (n2, d2))
	la("đủ số", (len(n1), len(d1)), (1129, 125))
	dung("không giao nhau, phủ đủ", not (set(n1) & set(d1)) and set(n1) | set(d1) == set(ds))
	_, d3 = crm.chia_doi_chung(ds, 10, "CD-26-0002")
	dung("hạt giống khác thì nhóm khác", d3 != d1)
	dung("không lấy đầu danh sách", d1 != sorted(ds)[:125])
	la("trùng mã bị gộp", crm.chia_doi_chung(["A", "A", "B"], 10, "x"), (["A", "B"] if crm.chia_doi_chung(["A", "B"], 10, "x")[0] == ["A", "B"] else ["B", "A"], []))


@ca("v614 chia Sales: đều, lần lượt; không có Sales thì không chia")
def _chia_sales():
	g = crm.chia_sales(["K%d" % i for i in range(11)], ["a@x", "b@x", "c@x"])
	dem = {}
	for v in g.values():
		dem[v] = dem.get(v, 0) + 1
	la("4-4-3", sorted(dem.values()), [3, 4, 4])
	la("không Sales", crm.chia_sales(["K1"], []), {})


@ca("v614 khung Ai sẽ được liên hệ: đúng số mẫu anh duyệt (4.446 -> 1.129)")
def _dong_chay():
	la("mẫu", crm.dong_chay(4446, 3180, 12, 10, 4), {
		"trong_nhom": 4446, "chua_dong_y": 3180, "khong_quang_cao": 12,
		"du_dieu_kien": 1254, "doi_chung": 125, "nhan": 1129, "so_sales": 4})
	la("không âm", crm.dong_chay(5, 9, 0, 10, 1)["nhan"], 0)


@ca("v614 hiệu quả: bình quân mỗi khách, không trừ thẳng hai tổng (Codex PR #503)")
def _hieu_qua():
	k = crm.hieu_qua({"so_khach": 1129, "khach_mua": 140, "tien": 1129 * 96000},
		{"so_khach": 125, "khach_mua": 5, "tien": 125 * 31000})
	la("bình quân", (k["nhan"]["binh_quan"], k["doi_chung"]["binh_quan"]), (96000, 31000))
	la("mang về thêm", k["mang_ve_them"], 65000 * 1129)
	la("tỉ lệ mua", (k["nhan"]["ty_le_mua"], k["doi_chung"]["ty_le_mua"]), (12.4, 4.0))
	dung("trừ thẳng hai tổng sẽ ra số khác hẳn", k["mang_ve_them"] != 1129 * 96000 - 125 * 31000)
	k0 = crm.hieu_qua({"so_khach": 8, "khach_mua": 2, "tien": 500000}, {"so_khach": 0})
	la("không có đối chứng thì không đoán phần mang về", (k0["co_doi_chung"], k0["mang_ve_them"]), (False, None))


# ------------------------------------------------------------ bộ lọc

@ca("v614 bộ lọc: bỏ khoá lạ, ngày sai, nhóm lạ; câu mô tả tiếng Việt")
def _loc():
	l = crm.loc_sach(json.dumps({"nhom": ["Sắp rời đi", "Hack"], "lan_cuoi_tu": "2025-12-01", "lan_cuoi_den": "abc",
		"chua_mua_ngay": "-3", "mon": " BAWC00080 ", "dong_y": ["Zalo", "Fax"], "x": 1}))
	la("sạch", l, {"nhom": ["Sắp rời đi"], "lan_cuoi_tu": "2025-12-01", "mon": "BAWC00080", "dong_y": ["Zalo"]})
	la("chuỗi hỏng", crm.loc_sach("{"), {})
	la("mô tả mùa lễ", crm.mo_ta_loc({"lan_cuoi_tu": "2025-12-01", "lan_cuoi_den": "2026-02-28"}),
		"mua lần cuối 01/12/2025 tới 28/02/2026")
	la("trống", crm.mo_ta_loc({}), "Tất cả khách")


@ca("v614 bộ lọc ra SQL: mọi giá trị qua tham số, luôn loại giỏ dùng chung và khách đã tắt, món đọc hoá đơn ERP")
def _dieu_kien():
	w, ts = crm.dieu_kien_loc({"nhom": ["Mới", "Đã ngủ"], "chua_mua_ngay": 30, "mon": "X' or 1=1 --",
		"dong_y": ["Gọi điện"], "hang": ["VOYAGER"]}, HN)
	dung("loại giỏ chung", "ifnull(h.la_gop, 0) = 0" in w)
	dung("loại khách tắt", "ifnull(c.disabled, 0) = 0" in w)
	dung("không ghép chữ người dùng vào câu", "1=1" not in w and "VOYAGER" not in w and "Mới" not in w)
	la("tham số", ts, ["Mới", "Đã ngủ", "2026-09-27", "VOYAGER", "X' or 1=1 --"])
	dung("món đọc hoá đơn đã ghi sổ, không huỷ, không trả", "s.docstatus = 1" in w and "vgb_huy" in w and "is_return" in w)
	dung("đồng ý đọc có ifnull", "ifnull(h.dy_goi, '') = 'Đồng ý'" in w)
	la("đồng ý theo kênh chiến dịch", crm.menh_de_dong_y(["Gọi điện", "Zalo"]),
		"(ifnull(h.dy_goi, '') = 'Đồng ý' or ifnull(h.dy_zalo, '') = 'Đồng ý')")
	la("không kênh là sai hết", crm.menh_de_dong_y([]), "1 = 0")


@ca("v614 chưa chốt được: nói đúng việc còn thiếu, theo thứ tự")
def _ly_do():
	cd = {"trang_thai": "Nháp", "kenh_goi": 1, "loc": {"nhom": ["Mới"]}, "kich_ban_duyet": 1}
	la("đủ", crm.ly_do_chua_chot(cd, 2), "")
	dung("thiếu kênh", "kênh" in crm.ly_do_chua_chot(dict(cd, kenh_goi=0), 2))
	dung("thiếu nhóm", "nhóm khách" in crm.ly_do_chua_chot(dict(cd, loc={}), 2))
	dung("kịch bản chưa duyệt", "chưa được duyệt" in crm.ly_do_chua_chot(dict(cd, kich_ban_duyet=0), 2))
	dung("thiếu Sales", "Sales" in crm.ly_do_chua_chot(cd, 0))
	dung("đã chốt", "đã chốt" in crm.ly_do_chua_chot(dict(cd, trang_thai="Đang chạy"), 2))
	la("chỉ gọi điện và Zalo cá nhân, không có Zalo OA", sorted(crm.KENH_CHIEN_DICH.values()), ["Gọi điện", "Zalo"])
	la("tin Zalo thay tên", crm.tin_zalo("Chào {ten}, tiệm có món mới", " Lan "), "Chào Lan, tiệm có món mới")
	la("không tên", crm.tin_zalo("Chào {ten}", ""), "Chào anh/chị")


# ------------------------------------------------------------ phần chạm hệ

def _gia_db(ho_so=None):
	"""Lớp cơ sở dữ liệu giả: hồ sơ CRM và các bảng nhật ký, ghi lại mọi lời gọi."""
	ho_so = dict(ho_so or {})
	ghi = types.SimpleNamespace(doc=[], set=[], bulk=[], sql=[])

	def get_value(dt_, name, cot=None, as_dict=False, **k):
		if dt_ == crm.DT_HO_SO:
			r = ho_so.get(name)
			return D(r) if r else None
		if dt_ == "Customer":
			return "Tên " + name
		return None

	def set_value(dt_, name, v, *a, **k):
		ghi.set.append((dt_, name, v))
		if dt_ == crm.DT_HO_SO and isinstance(v, dict):
			ho_so.setdefault(name, {}).update(v)

	class Doc(D):
		def insert(self, **k):
			ghi.doc.append(dict(self))
			if self.get("doctype") == crm.DT_HO_SO:
				ho_so[self["khach"]] = dict(self)
			return self

	return ho_so, ghi, get_value, set_value, Doc


@ca("v614 ghi đồng ý ở quầy: mỗi kênh đổi một dòng nhật ký có câu đã đọc, hồ sơ chưa có thì dựng")
def _ghi_dong_y():
	ho_so, ghi, gv, sv, Doc = _gia_db()
	fr = crm.frappe
	with _nen_ban(), um.patch.object(fr, "get_roles", lambda *a: ["Sales User"]), \
			um.patch.object(fr.db, "get_value", gv), um.patch.object(fr.db, "set_value", sv), \
			um.patch.object(fr, "get_doc", lambda d, *a, **k: Doc(d)):
		kq = crm.ghi_dong_y("KH-1", json.dumps({"Zalo": "Đồng ý", "Gọi điện": "Đồng ý", "Email": "Chưa hỏi"}), "Quầy")
		la("hai kênh đổi", kq, {"ok": 1, "doi": 2})
		nk = [d for d in ghi.doc if d["doctype"] == crm.DT_NHAT_KY]
		la("hai dòng nhật ký", sorted((d["kenh"], d["trang_thai"], d["noi_ghi"]) for d in nk),
			[("Gọi điện", "Đồng ý", "Quầy"), ("Zalo", "Đồng ý", "Quầy")])
		dung("dòng quầy lưu câu đã đọc làm bằng chứng", all(d["cau_hoi"] == crm.CAU_HOI_DONG_Y for d in nk))
		dung("dựng hồ sơ trước khi ghi", ghi.doc[0]["doctype"] == crm.DT_HO_SO)
		la("hồ sơ cập nhật", (ho_so["KH-1"]["dy_zalo"], ho_so["KH-1"]["dy_goi"], ho_so["KH-1"]["dy_noi"]), ("Đồng ý", "Đồng ý", "Quầy"))
		trc = len(ghi.doc)
		la("bấm lại y như cũ: không ghi gì", crm.ghi_dong_y("KH-1", {"Zalo": "Đồng ý", "Gọi điện": "Đồng ý"}, "Quầy"), {"ok": 1, "doi": 0})
		la("không thêm dòng", len(ghi.doc), trc)
		crm.ghi_dong_y("KH-1", {"Zalo": "Từ chối"}, "Hồ sơ khách")
		la("rút lại Zalo", ho_so["KH-1"]["dy_zalo"], "Từ chối")
		la("dòng hồ sơ không mang câu quầy", ghi.doc[-1]["cau_hoi"], "")
		nem("giỏ dùng chung không ghi được", lambda: crm.ghi_dong_y("Khách lẻ Online", {"Zalo": "Đồng ý"}))
		# Quầy đọc trạng thái này mỗi lần chọn khách; tấm hỏi chỉ hiện khi chưa hỏi.
		la("khách vừa đồng ý: quầy không hỏi lại", crm.dong_y_cua("KH-1")["can_hoi"], 0)
		moi = crm.dong_y_cua("KH-9")
		la("khách mới: quầy được hỏi, kèm câu đọc", (moi["co"], moi["can_hoi"], moi["Zalo"], moi["cau_hoi"]),
			(1, 1, "Chưa hỏi", crm.CAU_HOI_DONG_Y))
		# Giỏ dùng chung trả kèm mã khách để quầy nhớ đã đọc, không hỏi máy chủ
		# lại mỗi lần vẽ giỏ (posTaiThe so khach của lần đọc trước).
		la("giỏ dùng chung không hỏi, có mã khách", crm.dong_y_cua("Khách lẻ Online"), {"co": 0, "khach": "Khách lẻ Online"})
	with um.patch.object(fr, "get_roles", lambda *a: ["Stock User"]):
		nem("vai kho không ghi được", lambda: crm.ghi_dong_y("KH-1", {"Zalo": "Đồng ý"}))


def _cd_gia(**k):
	doc = D(name="CD-26-0001", ten="Giáng sinh 2026", trang_thai="Nháp", loc=json.dumps({"nhom": ["Sắp rời đi"]}),
		kenh_goi=1, kenh_zalo=0, kich_ban="Dạ chào anh chị, tiệm có món mới mùa Giáng sinh", kich_ban_duyet=1,
		ty_le_doi_chung=10, ctkm=None)
	doc.update(k)
	doc["sales"] = [D(nguoi="a@x", ten="Loan Anh"), D(nguoi="b@x", ten="Sales 2")]
	doc["mon"] = []
	doc.get = lambda key, mac=None: dict.get(doc, key, mac)
	doc.as_dict = lambda: dict(doc)
	return doc


@ca("v614 chốt chiến dịch: chỉ khách đã đồng ý và ngoài Danh sách không quảng cáo; đối chứng khoá cố định, không chia Sales")
def _chot():
	fr = crm.frappe
	rows = []
	for i in range(30):
		rows.append(D(khach="K%02d" % i, ten="Khách %d" % i, sdt="09%08d" % i, dy_goi="Đồng ý" if i < 25 else "Chưa hỏi",
			dy_zalo="", dy_email="", kqc=1 if i in (3, 4) else 0, du=1 if i < 25 else 0))
	doc = _cd_gia()
	luu, bulk = [], []
	with um.patch.object(fr, "get_roles", lambda *a: ["Sales Manager"]), \
			um.patch.object(crm, "_cd", lambda n, khoa=False: doc), \
			um.patch.object(crm, "_luu_cd", lambda d: luu.append(dict(d))), \
			um.patch.object(crm, "doc_chien_dich", lambda n: {"name": n}), \
			um.patch.object(fr.db, "sql", lambda q, *a, **k: rows), \
			um.patch.object(fr.db, "bulk_insert", lambda dt_, cot, dong, **k: bulk.extend(dict(zip(cot, d)) for d in dong), create=True), \
			um.patch.object(fr, "generate_hash", lambda length=10: "h%06d" % len(bulk), create=True):
		crm.chot_chien_dich("CD-26-0001")
	la("số trên phiếu", (doc.so_trong_nhom, doc.so_loai_chua_dong_y, doc.so_loai_kqc, doc.so_doi_chung, doc.so_nhan),
		(30, 5, 2, 2, 21))
	la("đủ dòng", len(bulk), 23)
	ten = {r["khach"] for r in bulk}
	dung("không ai chưa đồng ý", not ten & {"K25", "K26", "K27", "K28", "K29"})
	dung("không số trong Danh sách không quảng cáo", not ten & {"K03", "K04"})
	dc = [r for r in bulk if r["nhanh"] == "Đối chứng"]
	nhan = [r for r in bulk if r["nhanh"] == "Nhận"]
	dung("đối chứng không có Sales", all(not r["sales"] for r in dc))
	la("nhận chia đều hai Sales", sorted([sum(1 for r in nhan if r["sales"] == s) for s in ("a@x", "b@x")]), [10, 11])
	_, dc_mong = crm.chia_doi_chung([r.khach for r in rows if r.du and not r.kqc], 10, "CD-26-0001")
	la("đối chứng đúng phép chia lặp lại được", sorted(r["khach"] for r in dc), sorted(dc_mong))
	la("trạng thái và kênh", {(r["trang_thai"], r["kenh_duoc"]) for r in bulk}, {("Chưa gọi", "Gọi điện")})
	la("phiếu sang Đang chạy", (luu[-1]["trang_thai"], doc.chot_boi), ("Đang chạy", "kiemthu@vagabond"))


@ca("v614 chốt chiến dịch: chặn khi kịch bản chưa duyệt, chưa có Sales, đã chốt, hoặc vai không được lập")
def _chot_chan():
	fr = crm.frappe
	for nhan, doc, vai in (
		("kịch bản chưa duyệt", _cd_gia(kich_ban_duyet=0), ["Sales Manager"]),
		("đã chốt", _cd_gia(trang_thai="Đang chạy"), ["Sales Manager"]),
		("Sales thường không chốt được", _cd_gia(), ["Sales User"]),
	):
		goi = []
		with um.patch.object(fr, "get_roles", lambda *a, v=vai: v), \
				um.patch.object(crm, "_cd", lambda n, khoa=False, d=doc: d), \
				um.patch.object(fr.db, "sql", lambda *a, **k: goi.append(1) or []):
			nem(nhan, lambda: crm.chot_chien_dich("CD-26-0001"))
			la(nhan + ": không đọc khách", goi, [])


@ca("v614 lưu chiến dịch: sửa kịch bản sau khi duyệt thì phải duyệt lại; đã chốt thì không sửa")
def _luu_kich_ban():
	fr = crm.frappe
	doc = _cd_gia()
	doc.set = lambda k, v: dict.__setitem__(doc, k, v)
	doc.append = lambda k, v: doc[k].append(D(v))
	with um.patch.object(fr, "get_roles", lambda *a: ["Sales Manager"]), \
			um.patch.object(crm, "_cd", lambda n, khoa=False: doc), \
			um.patch.object(crm, "_luu_cd", lambda d: None), \
			um.patch.object(crm, "doc_chien_dich", lambda n: {"name": n}), \
			um.patch.object(fr.db, "exists", lambda *a, **k: True), \
			um.patch.object(fr.db, "get_value", lambda *a, **k: "x"):
		dat = {"name": doc.name, "ten": doc.ten, "loc": {"nhom": ["Mới"]}, "kenh_goi": 1,
			"kich_ban": doc.kich_ban, "sales": ["a@x"]}
		crm.luu_chien_dich(json.dumps(dat))
		la("giữ nguyên kịch bản thì giữ duyệt", doc.kich_ban_duyet, 1)
		crm.luu_chien_dich(json.dumps(dict(dat, kich_ban=doc.kich_ban + " Giảm 10%.")))
		la("đổi kịch bản thì bỏ duyệt", (doc.kich_ban_duyet, doc.duyet_boi), (0, None))
		doc.trang_thai = "Đang chạy"
		nem("đã chốt không sửa", lambda: crm.luu_chien_dich(json.dumps(dat)))


@ca("v614 sửa trên Desk: chiến dịch đã chốt bị chặn, nháp và lời ghi từ app thì cho qua")
def _desk():
	fr = crm.frappe
	doc = D(name="CD-1")
	doc.is_new = lambda: False
	with um.patch.object(fr.db, "get_value", lambda *a, **k: D(trang_thai="Đang chạy")), \
			um.patch.object(fr, "get_roles", lambda *a: ["Sales Manager"]):
		nem("đã chốt", lambda: crm.kiem_sua_chien_dich(doc))
		fr.flags.crm_ghi = True
		try:
			crm.kiem_sua_chien_dich(doc)
		finally:
			fr.flags.crm_ghi = False
	with um.patch.object(fr.db, "get_value", lambda *a, **k: D(trang_thai="Nháp")), \
			um.patch.object(fr, "get_roles", lambda *a: ["Sales Manager"]):
		crm.kiem_sua_chien_dich(doc)
	src = io.open(os.path.join(GOI, "vagabond", "doctype", "vagabond_chien_dich", "vagabond_chien_dich.py"), encoding="utf-8").read()
	dung("controller gọi kiem_sua_chien_dich", "kiem_sua_chien_dich(self)" in src)


@ca("v614 ghi kết quả: Không muốn nhận tin nữa ghi Từ chối cả gọi điện lẫn Zalo; đối chứng không gọi được; khách người khác thì chặn")
def _ket_qua():
	fr = crm.frappe
	dong = D(name="R1", sales="kiemthu@vagabond", khach="K1", chien_dich="CD-1", so_lan=0, nhanh="Nhận")
	ghi, lh, dy = [], [], []
	with um.patch.object(fr, "get_roles", lambda *a: ["Sales User"]), \
			um.patch.object(fr.db, "exists", lambda *a, **k: True), \
			um.patch.object(fr.db, "get_value", lambda *a, **k: dong), \
			um.patch.object(fr.db, "set_value", lambda *a, **k: ghi.append(a)), \
			um.patch.object(crm, "ghi_lien_he", lambda *a: lh.append(a)), \
			um.patch.object(crm, "ghi_dong_y", lambda *a: dy.append(a)):
		la("hẹn gọi lại", crm.ghi_ket_qua("R1", "Không nghe máy")["trang_thai"], "Hẹn gọi lại")
		la("chưa đụng sổ đồng ý", dy, [])
		crm.ghi_ket_qua("R1", "Không muốn nhận tin nữa", "khách bực")
		la("từ chối cả hai kênh", dy[-1][1], {"Zalo": "Từ chối", "Gọi điện": "Từ chối"})
		la("ghi ở Sales gọi, kèm chiến dịch", dy[-1][2:], ("Sales gọi", "CD-1"))
		la("có dòng nhật ký liên hệ", lh[-1][:4], ("K1", "Gọi điện", "Không muốn nhận tin nữa", "khách bực"))
		nem("kết quả lạ", lambda: crm.ghi_ket_qua("R1", "Đã gửi thư"))
		dong.nhanh = "Đối chứng"
		nem("đối chứng", lambda: crm.ghi_ket_qua("R1", "Quan tâm"))
		dong.nhanh = "Nhận"
		dong.sales = "khac@x"
		nem("khách của Sales khác", lambda: crm.ghi_ket_qua("R1", "Quan tâm"))


@ca("v614 tính nhóm đêm: lượt đêm không ghi đè đồng ý và Danh sách không quảng cáo; ghi theo lô 500, tiền ERP và Fabi hai cột riêng")
def _tinh_dem():
	fr = crm.frappe
	cau, commit = [], []
	erp = [D(customer="KH-%04d" % i, so_don=2, tien=500000, lan_dau=dt.date(2026, 8, 20), lan_cuoi=dt.date(2026, 10, 20)) for i in range(700)]
	khach = [D(name="KH-%04d" % i, customer_name="K%d" % i, mobile_no="+84 909 000 %03d" % (i % 1000),
		vgb_so_don_cu=3, vgb_chi_tieu_cu=1000000, vgb_lan_dau_cu=dt.date(2023, 1, 1), vgb_lan_cuoi_cu=dt.date(2026, 7, 1))
		for i in range(1001)] + [D(name="Khách lẻ Online", customer_name="Khách lẻ Online")]

	def sql(q, ts=None, **k):
		if "group by customer" in q:
			return erp
		if "from `tabCustomer`" in q:
			return khach
		cau.append((q, ts))
		return []

	meta = types.SimpleNamespace(get_valid_columns=lambda: ["vgb_so_don_cu", "vgb_chi_tieu_cu", "vgb_lan_dau_cu", "vgb_lan_cuoi_cu"])
	with _nen_ban(), um.patch.object(fr.db, "sql", sql), um.patch.object(fr.db, "commit", lambda: commit.append(1)), \
			um.patch.object(fr, "get_meta", lambda dt_: meta, create=True):
		kq = crm.tinh_nhom_dem()
	la("đủ khách", kq, {"so_khach": 1002})
	la("ba lô", [len(ts) // 26 for _, ts in cau], [500, 500, 2])
	la("commit sau mỗi lô", len(commit), 3)
	q = cau[0][0]
	sau = q.split("on duplicate key update", 1)[1]
	for c in ("dy_zalo", "dy_goi", "dy_email", "khong_quang_cao", "kqc_ghi_chu", "creation", "owner"):
		dung("UPDATE không đụng %s" % c, "`%s`" % c not in sau)
	for c in ("nhom", "so_don", "lan_cuoi", "tien_erp", "tien_fabi", "tinh_luc"):
		dung("UPDATE có %s" % c, "`%s` = values(`%s`)" % (c, c) in sau)
	ts = cau[0][1]
	cot = re.search(r"\(([^)]*)\) values", q).group(1).replace("`", "").split(", ")
	dong0 = dict(zip(cot, ts[:26]))
	la("tiền ERP và Fabi riêng", (dong0["tien_erp"], dong0["tien_fabi"]), (500000.0, 1000000.0))
	la("số đơn gộp, ngày rộng nhất", (dong0["so_don"], str(dong0["lan_dau"]), str(dong0["lan_cuoi"])), (5, "2023-01-01", "2026-10-20"))
	la("số điện thoại chuẩn", dong0["sdt"], "0909000000")
	la("giỏ chung gắn cờ", dict(zip(cot, cau[2][1][26:]))["la_gop"], 1)
	with _nen_ban(), um.patch.object(fr.db, "sql", sql), um.patch.object(fr.db, "commit", lambda: commit.append(1)), \
			um.patch.object(fr, "get_meta", lambda dt_: meta, create=True):
		commit.clear()
		crm.tinh_nhom_dem(luu=False)
	la("ca kiểm tích hợp không commit", commit, [])


@ca("v614 quyền: danh sách ẩn ô trên app trùng máy chủ; lịch đêm và bản vá có mặt")
def _quyen():
	js = io.open(os.path.join(GOI, "public", "js", "bep", "58-crm.js"), encoding="utf-8").read()
	for ten, may_chu in (("CRM_XEM", crm.CRM_XEM), ("CRM_LAP", crm.CRM_LAP)):
		m = re.search(r"var %s = \[([^\]]*)\]" % ten, js)
		la(ten + " trùng máy chủ", re.findall(r"'([^']+)'", m.group(1)), list(may_chu))
	la("sáu nhóm trùng máy chủ", re.findall(r"'([^']+)'", re.search(r"var CRM_NHOM = \[([^\]]*)\]", js).group(1)), list(crm.NHOM))
	hk = io.open(os.path.join(GOI, "hooks.py"), encoding="utf-8").read()
	dung("lịch 02:30", '.setdefault("30 2 * * *", []).append("vagabond.crm.tinh_nhom_dem")' in hk)
	pt = io.open(os.path.join(GOI, "patches.txt"), encoding="utf-8").read().split()
	dung("bản vá tính lần đầu", "vagabond.patches.v614_crm_tinh_nhom" in pt)
	dung("không còn dấu gạch dài trong mã CRM", not re.search("[\u2013\u2014]", io.open(os.path.join(GOI, "crm.py"), encoding="utf-8").read() + js))


@ca("v614 doctype: hồ sơ CRM theo mã khách, nhật ký đồng ý không ai sửa không ai xoá")
def _doctype():
	def doc(t):
		return json.load(io.open(os.path.join(GOI, "vagabond", "doctype", t, t + ".json"), encoding="utf-8"))
	hs = doc("vagabond_ho_so_crm")
	la("tên theo mã khách", hs["autoname"], "field:khach")
	nk = doc("vagabond_dong_y_nhat_ky")
	dung("không vai nào sửa hay xoá nhật ký", all(not p.get("write") and not p.get("delete") for p in nk["permissions"]))
	dung("mọi ô nhật ký chỉ đọc", all(f.get("read_only") for f in nk["fields"] if f["fieldtype"] not in ("Column Break", "Section Break")))
	ck = doc("vagabond_chien_dich_khach")
	dung("danh sách đã chốt chỉ đọc", all(f.get("read_only") for f in ck["fields"] if f["fieldtype"] not in ("Column Break", "Section Break")))
	cd = doc("vagabond_chien_dich")
	la("trạng thái", [f["options"] for f in cd["fields"] if f["fieldname"] == "trang_thai"][0], "Nháp\nĐang chạy\nĐã kết thúc")
	for t in ("vagabond_ho_so_crm", "vagabond_dong_y_nhat_ky", "vagabond_lien_he_khach", "vagabond_bo_loc_khach",
			"vagabond_chien_dich", "vagabond_chien_dich_khach", "vagabond_chien_dich_mon", "vagabond_chien_dich_sales"):
		d = doc(t)
		la(t + " khai đủ thứ tự ô", d["field_order"], [f["fieldname"] for f in d["fields"]])
		dung(t + " có mốc modified", bool(d.get("modified")))


# ------------------------------------------------- Codex PR #505 vòng 1

@ca("v614 Codex #505: danh sách gọi đọc đồng ý HIỆN TẠI, khách rút đồng ý hay vào danh sách cấm sau khi chốt thì hết nút liên hệ")
def _kenh_luc_nay():
	cd = {"kenh_goi": 1, "kenh_zalo": 1}
	la("vẫn đồng ý cả hai", crm.kenh_lien_he_luc_nay({"dy_goi": "Đồng ý", "dy_zalo": "Đồng ý"}, cd), ["Gọi điện", "Zalo"])
	la("rút gọi điện sau khi chốt", crm.kenh_lien_he_luc_nay({"dy_goi": "Từ chối", "dy_zalo": "Đồng ý"}, cd), ["Zalo"])
	la("vào Danh sách không quảng cáo: không kênh nào",
		crm.kenh_lien_he_luc_nay({"dy_goi": "Đồng ý", "dy_zalo": "Đồng ý", "khong_quang_cao": 1}, cd), [])
	la("chiến dịch chỉ gọi: Zalo đồng ý không mở nút Zalo", crm.kenh_lien_he_luc_nay({"dy_zalo": "Đồng ý"}, {"kenh_goi": 1}), [])
	fr = crm.frappe
	# Dòng đã chốt mang kenh_duoc cũ "Gọi điện, Zalo"; hồ sơ hiện tại đã Từ chối.
	dong = [D(name="L1", chien_dich="CD-1", ten_chien_dich="Giáng sinh", khach="K1", ten_khach="Minh Anh", sdt="0909",
		trang_thai="Chưa gọi", kenh_duoc="Gọi điện, Zalo", noi_dung_zalo="Chào {ten}", kich_ban="", mua_cuoi=None,
		nhom="Mới", hang="", dy_goi="Từ chối", dy_zalo="Từ chối", kqc=0, kenh_goi=1, kenh_zalo=1),
		D(name="L2", chien_dich="CD-1", ten_chien_dich="Giáng sinh", khach="K2", ten_khach="Long", sdt="0912",
		trang_thai="Chưa gọi", kenh_duoc="Gọi điện", noi_dung_zalo="Chào {ten}", kich_ban="", mua_cuoi=None,
		nhom="Mới", hang="", dy_goi="Đồng ý", dy_zalo="Chưa hỏi", kqc=1, kenh_goi=1, kenh_zalo=1),
		D(name="L3", chien_dich="CD-1", ten_chien_dich="Giáng sinh", khach="K3", ten_khach="Thu", sdt="0987",
		trang_thai="Chưa gọi", kenh_duoc="Gọi điện", noi_dung_zalo="Chào {ten}", kich_ban="", mua_cuoi=None,
		nhom="Mới", hang="", dy_goi="Đồng ý", dy_zalo="Chưa hỏi", kqc=0, kenh_goi=1, kenh_zalo=1)]
	cau = []

	def sql(q, ts=None, **k):
		cau.append(q)
		return [D(r) for r in dong]

	meta = types.SimpleNamespace(get_valid_columns=lambda: [])
	with um.patch.object(fr, "get_roles", lambda *a: ["Sales User"]), um.patch.object(fr.db, "sql", sql), \
			um.patch.object(fr, "get_meta", lambda dt_: meta, create=True):
		kq = crm.ds_goi_cua_toi()
	r = {x["name"]: x for x in kq["dong"]}
	la("rút cả hai: không còn kênh", (r["L1"]["kenh_duoc"], r["L1"]["ngung"], r["L1"]["tin_zalo"]), ("", 1, ""))
	la("vào danh sách cấm: không còn kênh", (r["L2"]["kenh_duoc"], r["L2"]["ngung"]), ("", 1))
	la("vẫn đồng ý: giữ nút gọi", (r["L3"]["kenh_duoc"], r["L3"]["ngung"]), ("Gọi điện", 0))
	dung("câu đọc hồ sơ hiện tại", "h.dy_goi" in cau[0] and "khong_quang_cao" in cau[0])


@ca("v614 Codex #505: sửa kịch bản trên Desk sau khi duyệt thì mất duyệt; Sales Manager tự tích duyệt trên Desk không được")
def _desk_duyet():
	la("đổi chữ kịch bản: mất duyệt", crm.duyet_sau_sua("Chào anh chị", 1, "Chào anh chị, có mã", 1, False), 0)
	la("đổi chữ kịch bản dù người có quyền duyệt: vẫn mất duyệt", crm.duyet_sau_sua("A", 1, "B", 1, True), 0)
	la("chỉ thêm khoảng trắng đầu cuối: giữ duyệt", crm.duyet_sau_sua("A", 1, " A ", 1, False), 1)
	la("tự tích duyệt khi không có quyền: bỏ", crm.duyet_sau_sua("A", 0, "A", 1, False), 0)
	la("giám đốc duyệt: giữ", crm.duyet_sau_sua("A", 0, "A", 1, True), 1)
	fr = crm.frappe
	doc = D(name="CD-1", trang_thai="Nháp", kich_ban="Kịch bản sửa trên Desk", kich_ban_duyet=1, duyet_boi="gd@x", duyet_luc="x")
	doc.is_new = lambda: False
	cu = D(trang_thai="Nháp", kich_ban="Kịch bản giám đốc đã đọc", kich_ban_duyet=1)
	with um.patch.object(fr.db, "get_value", lambda *a, **k: cu), um.patch.object(fr, "get_roles", lambda *a: ["Sales Manager"]):
		crm.kiem_sua_chien_dich(doc)
	la("Desk sửa kịch bản: mất duyệt, xoá người duyệt", (doc.kich_ban_duyet, doc.duyet_boi, doc.duyet_luc), (0, None, None))
	moi = D(name="CD-2", trang_thai="Nháp", kich_ban="Kịch bản", kich_ban_duyet=1)
	moi.is_new = lambda: True
	with um.patch.object(fr, "get_roles", lambda *a: ["Sales Manager"]):
		crm.kiem_sua_chien_dich(moi)
	la("tạo mới trên Desk tích sẵn duyệt: bỏ", moi.kich_ban_duyet, 0)


@ca("v614 Codex #505: đo hiệu quả đúng 14 ngày tính từ GIỜ chốt, so cả giờ trên hoá đơn")
def _cua_so():
	tu, den = crm.cua_so_do(dt.datetime(2026, 10, 27, 18, 0, 0))
	la("từ đúng giờ chốt tới đúng 14 ngày sau", (str(tu), str(den)), ("2026-10-27 18:00:00", "2026-11-10 18:00:00"))
	fr = crm.frappe
	doc = D(name="CD-1", ten="Giáng sinh", ngay_chot=dt.datetime(2026, 10, 27, 18, 0, 0), ctkm="CTKM-1", ma_uu_dai="XMAS")
	cau = []

	def sql(q, ts=None, **k):
		cau.append((q, ts))
		if "count(distinct u.hoa_don)" in q:
			return [[0]]
		return []

	with um.patch.object(fr, "get_roles", lambda *a: ["Sales Manager"]), um.patch.object(fr.db, "sql", sql), \
			um.patch.object(fr.db, "exists", lambda *a, **k: True), um.patch.object(fr, "get_doc", lambda *a, **k: doc), \
			um.patch.object(fr.db, "count", lambda *a, **k: 0, create=True):
		kq = crm.hieu_qua_chien_dich("CD-1")
	hd = [c for c in cau if "tabSales Invoice" in c[0] and "u.hoa_don" not in c[0]]
	dung("đủ ba câu đọc hoá đơn", len(hd) == 3)
	for q, ts in hd:
		dung("so cả giờ hoá đơn", "timestamp(s.posting_date, s.posting_time)" in q)
		la("tham số mốc giờ", [str(x) for x in ts[:2]], ["2026-10-27 18:00:00", "2026-11-10 18:00:00"])
	ma = [c for c in cau if "u.hoa_don" in c[0]][0]
	dung("đơn dùng mã so theo giờ dùng mã", "u.luc >=" in ma[0])
	la("hiện mốc đo có giờ", (kq["tu"], kq["den"]), ("2026-10-27 18:00:00", "2026-11-10 18:00:00"))

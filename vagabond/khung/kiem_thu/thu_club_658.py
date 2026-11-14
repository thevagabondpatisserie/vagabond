# -*- coding: utf-8 -*-
"""v658 (anh Việt chốt thiết kế 14/11/2026): giao diện The Vagabond Club.

Trang đăng nhập L3 + K1, trang thành viên J1c (hành trình hạng), T1 (thẻ hạng
vuốt ngang), U3 (dòng thời gian hạn điểm theo từng lần tích).

Phần máy chủ chạy THẬT các phép thuần của diem_web (cac_lan_tich_con_han,
ngay_het_lan_tich, bang_hang_moi, qua_sinh_nhat_tu_ctkm) và noi_dung_web
(chỗ banner Trang thành viên). Phần trang chạy thật trong node:
hanh_vi/thanh_vien_658.js. Đo chạm, chữ, tràn ngang 390 px làm bằng Chromium
thật, ghi trong PR.
"""
import os
import subprocess
from unittest.mock import patch

from vagabond import diem_web as dw
from vagabond import noi_dung_web as nw
from vagabond.diem_han import qua_han_cuon_chieu
from vagabond.khung.kiem_thu.nen import ca, dung, la

# Kịch bản Zalo Sinh nhật đúng như anh Việt bật trên site 14/11/2026: gửi trước 3 ngày, mã dùng 15 ngày.
KB = {"ctkm": "QUA-SINH-NHAT", "bat": 1, "so_ngay": 3, "han_ngay": 15}
GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@ca("v658 U3: mỗi lần tích còn điểm có hạn riêng 12 tháng; điểm đã tiêu và đã hết hạn trừ vào lần CŨ nhất trước; lần sắp hết hạn đứng đầu")
def _():
	but = [("2025-11-29", 20000), ("2026-03-02", 5000), ("2026-05-10", -13000), ("2026-10-17", 7200), ("2026-11-01", 23400)]
	ds = dw.cac_lan_tich_con_han(but, "2026-11-14", 12)
	la("ba lần còn điểm, đúng số còn lại", [(x["ngay_tich"], x["diem"], x["ngay_het"]) for x in ds], [
		("29/11/2025", 7000, "30/11/2026"), ("02/03/2026", 5000, "03/03/2027"),
		("17/10/2026", 7200, "18/10/2027"), ("01/11/2026", 23400, "02/11/2027")])
	la("tổng đúng số dư", sum(x["diem"] for x in ds), 20000 + 5000 - 13000 + 7200 + 23400)
	# Bút ghi lệch thứ tự ngày vẫn sắp đúng theo hạn.
	la("sắp theo hạn", [x["ngay_het"] for x in dw.cac_lan_tich_con_han(list(reversed(but)), "2026-11-14", 12)],
		["30/11/2026", "03/03/2027", "18/10/2027", "02/11/2027"])


@ca("v658 U3: lần tích đã tới ngày mất (việc định kỳ đêm nay ghi bút hết hạn) không còn là còn hạn; bút hết hạn đã ghi trừ đúng lần cũ")
def _():
	but = [("2025-11-13", 3000), ("2025-12-20", 4000)]
	la("13/11/2025 mất ngày 14/11/2026", [x["ngay_tich"] for x in dw.cac_lan_tich_con_han(but, "2026-11-14", 12)], ["20/12/2025"])
	la("hôm trước vẫn còn", [x["ngay_tich"] for x in dw.cac_lan_tich_con_han(but, "2026-11-13", 12)], ["13/11/2025", "20/12/2025"])
	# Việc định kỳ đã ghi bút âm "Hết hạn" 3.000: lần 13/11 hết điểm, lần 20/12 giữ nguyên.
	la("sau bút hết hạn", [(x["ngay_tich"], x["diem"]) for x in dw.cac_lan_tich_con_han(but + [("2026-11-14", -3000)], "2026-11-15", 12)],
		[("20/12/2025", 4000)])
	la("hạn tắt thì không có dòng thời gian", dw.cac_lan_tich_con_han(but, "2026-11-14", 0), [])
	la("không có bút", dw.cac_lan_tich_con_han([], "2026-11-14", 12), [])


@ca("v658 U3: ngày hết hạn từng lần tích CÙNG MỘT LUẬT với việc định kỳ (mốc lùi tháng kẹp cuối tháng): 28/02, 29/02, 31/01, 31/12")
def _():
	for tich, han in (("2026-02-28", 1), ("2024-02-29", 12), ("2026-01-31", 1), ("2025-12-31", 12), ("2025-03-31", 11), ("2026-11-14", 12)):
		d = dw.ngay_het_lan_tich(tich, han)
		hom_truoc = d - dw.timedelta(days=1)
		la("%s hạn %s: hôm trước chưa mất, hôm đó mất" % (tich, han), (
			qua_han_cuon_chieu([(tich, 100)], dw.moc_han(hom_truoc, han)), qua_han_cuon_chieu([(tich, 100)], dw.moc_han(d, han))), (0, 100))


@ca("v658 một nguồn: dòng thời gian U3 và câu nhắc điểm sắp hết hạn (sap_het_han) ra CÙNG ngày, cùng số điểm của lần sắp hết hạn nhất")
def _():
	for but, hn in (([("2025-12-01", 900), ("2025-12-01", 100), ("2026-06-01", 500)], "2026-11-20"),
			([("2025-11-30", 50), ("2025-12-31", 60), ("2026-01-02", -20)], "2026-11-20"),
			([("2026-01-31", 80)], "2027-01-10")):
		sh = dw.sap_het_han(but, hn, 12)
		ds = dw.cac_lan_tich_con_han(but, hn, 12)
		cung_ngay = sum(x["diem"] for x in ds if x["ngay_het"] == ds[0]["ngay_het"])
		la("%s: cùng ngày, cùng số" % but, (sh["ngay"], sh["diem"]), (ds[0]["ngay_het"], cung_ngay))
	# Không chỗ nào tự tính mốc: sap_het_han và ngay_het_lan_tich cùng gọi moc_han.
	import inspect
	dung("sap_het_han dùng moc_han", "moc_han(" in inspect.getsource(dw.sap_het_han))
	dung("ngay_het_lan_tich dùng moc_han", "moc_han(" in inspect.getsource(dw.ngay_het_lan_tich))


@ca("v658 U3: tóm tắt ba lần sắp hết hạn hiện riêng, phần còn lại gộp một dòng; đọc đủ mọi lần tích (không giới hạn trang)")
def _():
	but = [("2026-%02d-05" % m, 1000 * m) for m in range(1, 12)]
	t = dw.tom_tat_lan_tich(dw.cac_lan_tich_con_han(but, "2026-11-14", 12))
	la("ba dòng đầu", [x["ngay_tich"] for x in t["ds"]], ["05/01/2026", "05/02/2026", "05/03/2026"])
	la("phần còn lại", t["khac"], {"diem": sum(1000 * m for m in range(4, 12)), "so": 8})
	la("tổng", t["tong"], sum(1000 * m for m in range(1, 12)))
	dung("không lộ trường nội bộ", all(set(x) == {"diem", "ngay_tich", "ngay_het"} for x in t["ds"]))


@ca("v658 the_le đọc sổ điểm của MỘT khách không LIMIT, trả dòng thời gian khi hạn cuốn chiếu; hạn tắt thì không có")
def _():
	import sys
	import types

	cau = []

	class _Db:
		def sql(self, q, a=None, **k):
			cau.append(q)
			return [("2025-12-01", 900), ("2026-06-01", 500)]

		def get_value(self, *a, **k):
			return None

	def all_(dt, **k):
		if dt == "Vagabond Hang Khach":
			return [{"name": "EXPLORER", "ten_hang": "EXPLORER", "thu_tu": 1, "loai": "Theo chi tieu", "tich_diem": 2, "chi_tieu_tu": 0, "bat": 1},
				{"name": "AMBASSADOR", "ten_hang": "AMBASSADOR", "thu_tu": 4, "loai": "Gan tay", "giam_gia": 10, "tich_diem": 0, "bat": 1},
				{"name": "FAMILY", "ten_hang": "FAMILY", "thu_tu": 5, "loai": "Gan tay", "giam_gia": 20, "bat": 1}]
		return []

	f = types.SimpleNamespace(get_all=all_, db=_Db(), log_error=lambda *a, **k: None, get_traceback=lambda: "")
	fu = types.SimpleNamespace(nowdate=lambda: "2026-11-20")
	from vagabond import diem_han
	for cach, co in (("Cuon chieu", True), ("Tat", False)):
		cau.clear()
		with patch.dict(sys.modules, {"frappe": f, "frappe.utils": fu}), \
				patch.object(dw, "_cd", return_value={"tran_pt": 50, "bill_toi_thieu": 10000}), \
				patch.object(diem_han, "_cd", return_value={"cach": cach, "han_thang": 12}), \
				patch.object(dw, "cau_nhan_dang_chay", return_value=[]):
			r = dw.the_le("KH-1")
		la(cach + ": có dòng thời gian", bool(r["lan_tich"]), co)
		if co:
			la("lần sắp hết hạn", r["lan_tich"]["ds"][0], {"diem": 900, "ngay_tich": "01/12/2025", "ngay_het": "02/12/2026"})
			dung("đọc sổ không LIMIT", cau and "limit" not in cau[0].lower())
		la("hạng mời chỉ AMBASSADOR", [h["ten_hang"] for h in r["hang_moi"]], ["AMBASSADOR"])


@ca("v658 T1: hạng gán tay chỉ hiện AMBASSADOR (FAMILY, OWNER không); số giảm, số tích đọc từ hạng trên site; hạng tắt không hiện")
def _():
	hang = [{"name": "OWNER", "ten_hang": "OWNER", "loai": "Gan tay", "giam_gia": 100, "tich_diem": 0, "bat": 1, "thu_tu": 6},
		{"name": "AMBASSADOR", "ten_hang": "AMBASSADOR", "loai": "Gan tay", "giam_gia": 10, "tich_diem": 0, "bat": 1, "thu_tu": 4},
		{"name": "FAMILY", "ten_hang": "FAMILY", "loai": "Gan tay", "giam_gia": 20, "tich_diem": 0, "bat": 1, "thu_tu": 5},
		{"name": "VOYAGER", "ten_hang": "VOYAGER", "loai": "Theo chi tieu", "giam_gia": 0, "tich_diem": 3, "bat": 1, "thu_tu": 2, "chi_tieu_tu": 10000000}]
	ctkm = [{"ten": "Quà sinh nhật", "doi_tuong": "Theo hang khach", "hien_web": 1, "hang_khach": "VOYAGER\nAMBASSADOR\nFAMILY"}]
	r = dw.bang_hang_moi(hang, ctkm)
	la("chỉ AMBASSADOR", [(h["ten_hang"], h["giam_gia"], h["tich_diem"], h["moi"], h["dac_quyen"]) for h in r],
		[("AMBASSADOR", 10.0, 0.0, 1, ["Quà sinh nhật"])])
	la("hạng tắt", dw.bang_hang_moi([dict(hang[1], bat=0)], ctkm), [])
	la("bảng theo chi tiêu không lẫn hạng mời", [h["ten_hang"] for h in dw.bang_the_le(hang, ctkm)], ["VOYAGER"])


@ca("v658 T1: quà sinh nhật đọc từ chương trình đang gắn ở kịch bản Zalo Sinh nhật; tắt, không hiện web, không theo hạng thì không hứa quà")
def _():
	km = {"name": "QUA-SINH-NHAT", "ten": "Quà sinh nhật thành viên", "bat": 1, "hien_web": 1, "doi_tuong": "Theo hang khach",
		"hang_khach": "VOYAGER\nVAGABONDER\nAMBASSADOR\nFAMILY", "kieu_giam": "Phan tram", "gia_tri": 100,
		"pham_vi": "Nhom mon chi dinh", "nhom_mon": "Bánh lạnh", "giam_toi_da": 185000, "cach_ma": "Ma dung mot lan"}
	hn = "2026-11-14"
	la("đúng số site 14/11", dw.qua_sinh_nhat_tu_ctkm(km, hn, KB), {"ten": "Quà sinh nhật thành viên", "nhom": "Bánh lạnh", "toi_da": 185000,
		"hang": ["VOYAGER", "VAGABONDER", "AMBASSADOR", "FAMILY"], "truoc": 3, "han": 15})
	for sai in ({"bat": 0}, {"hien_web": 0}, {"doi_tuong": "Moi khach"}, {"hang_khach": ""}):
		la("không hứa quà khi %s" % sai, dw.qua_sinh_nhat_tu_ctkm(dict(km, **sai), hn, KB), None)
	la("không phải tặng trọn bánh thì không ghi nhóm", dw.qua_sinh_nhat_tu_ctkm(dict(km, gia_tri=50), hn, KB)["nhom"], "")
	la("không có chương trình", dw.qua_sinh_nhat_tu_ctkm(None, hn, KB), None)


@ca("v658 anh Việt 14/11: quà sinh nhật chỉ hứa khi kịch bản Zalo Sinh nhật đang bật (quà tới tay khách qua tin này); số ngày gửi trước và hạn mã đọc từ kịch bản, hạn kẹp theo ngày kết thúc chương trình")
def _():
	km = {"name": "QUA-SINH-NHAT", "ten": "Quà sinh nhật thành viên", "bat": 1, "hien_web": 1, "doi_tuong": "Theo hang khach",
		"hang_khach": "VOYAGER", "kieu_giam": "Phan tram", "gia_tri": 100, "pham_vi": "Nhom mon chi dinh",
		"nhom_mon": "Bánh lạnh", "giam_toi_da": 185000, "cach_ma": "Ma dung mot lan"}
	hn = "2026-11-14"
	la("kịch bản tắt thì không hứa", dw.qua_sinh_nhat_tu_ctkm(km, hn, dict(KB, bat=0)), None)
	la("không đọc được kịch bản thì không hứa", dw.qua_sinh_nhat_tu_ctkm(km, hn, None), None)
	r = dw.qua_sinh_nhat_tu_ctkm(km, hn, KB)
	la("gửi trước 3 ngày, dùng 15 ngày", (r["truoc"], r["han"]), (3, 15))
	r = dw.qua_sinh_nhat_tu_ctkm(km, hn, dict(KB, so_ngay=0, han_ngay=30))
	la("đổi kịch bản thì trang đổi theo", (r["truoc"], r["han"]), (0, 30))
	r = dw.qua_sinh_nhat_tu_ctkm(dict(km, den_ngay="2026-11-20"), hn, KB)
	la("hạn mã kẹp theo ngày kết thúc chương trình như lúc cấp mã", r["han"], 6)


@ca("v658 Codex #566: chương trình sinh nhật còn bật nhưng hết hạn, chưa bắt đầu, hạn mã đã qua hay không phải mã dùng một lần thì trang KHÔNG hứa quà, đúng như cửa cấp mã từ chối")
def _():
	from vagabond.zalo_kich_ban import ctkm_phat_duoc

	km = {"name": "QUA-SINH-NHAT", "ten": "Quà sinh nhật thành viên", "bat": 1, "hien_web": 1, "doi_tuong": "Theo hang khach",
		"hang_khach": "VOYAGER", "kieu_giam": "Phan tram", "gia_tri": 100, "pham_vi": "Nhom mon chi dinh",
		"nhom_mon": "Bánh lạnh", "giam_toi_da": 185000, "cach_ma": "Ma dung mot lan"}
	hn = "2026-11-14"
	# Đúng thao tác Codex mô tả: hết hạn 01/11, xem trang ngày 14/11.
	het = dict(km, den_ngay="2026-11-01")
	dung("cửa cấp mã từ chối chương trình hết hạn", ctkm_phat_duoc(het, dw._ngay(hn), 7)[0] is None)
	la("trang không hứa quà khi cửa cấp mã từ chối", dw.qua_sinh_nhat_tu_ctkm(het, hn, KB), None)
	for sai in ({"tu_ngay": "2026-12-01"}, {"han_ma": "2026-11-13"}, {"cach_ma": "Ma chung"}):
		la("không hứa quà khi %s" % sai, dw.qua_sinh_nhat_tu_ctkm(dict(km, **sai), hn, KB), None)
	# Biên: ngày kết thúc là hôm nay vẫn cấp được nên vẫn hứa.
	dung("đúng ngày kết thúc vẫn hứa", dw.qua_sinh_nhat_tu_ctkm(dict(km, den_ngay=hn), hn, KB) is not None)
	# Một nguồn: trang hỏi đúng cửa cấp mã, không tự so ngày.
	with patch("vagabond.zalo_kich_ban.ctkm_phat_duoc", lambda k, h, n: (None, "từ chối")):
		la("cửa cấp mã từ chối thì trang không hứa dù ngày hợp lệ", dw.qua_sinh_nhat_tu_ctkm(km, hn, KB), None)


@ca("v658 Codex #566 cùng loại: đặc quyền theo hạng trên thể lệ bỏ chương trình chưa tới ngày bắt đầu và đã qua ngày kết thúc, giữ đúng ngày biên")
def _():
	hn = "2026-11-14"
	la("chưa bắt đầu", dw.ctkm_trong_han({"tu_ngay": "2026-11-15"}, hn), False)
	la("bắt đầu hôm nay", dw.ctkm_trong_han({"tu_ngay": hn}, hn), True)
	la("đã qua ngày kết thúc", dw.ctkm_trong_han({"den_ngay": "2026-11-13"}, hn), False)
	la("kết thúc hôm nay", dw.ctkm_trong_han({"den_ngay": hn}, hn), True)
	la("không đặt ngày", dw.ctkm_trong_han({}, hn), True)
	# the_le dùng đúng hàm này, không còn tự so ngày.
	nguon = open(os.path.join(GOC, "vagabond", "diem_web.py"), encoding="utf-8").read()
	than = nguon[nguon.index("def the_le("):nguon.index("def _qua_sn(")]
	dung("the_le lọc bằng ctkm_trong_han", "ctkm_trong_han(k, hn)" in than and "den_ngay\"]) <" not in than)


@ca("v658 anh Việt 14/11 (giao diện xấu): lớp CSS của thẻ hạng T1 không trùng lớp cũ của trang (lớp .moi cũ của khối mời hồ sơ từng đẩy thẻ AMBASSADOR lệch 24 px, đổi chữ tiêu đề)")
def _():
	import re

	css = open(os.path.join(GOC, "vagabond", "public", "web_order", "thanh-vien.css"), encoding="utf-8").read()
	js = open(os.path.join(GOC, "vagabond", "public", "web_order", "thanh-vien.js"), encoding="utf-8").read()
	cu = css[:css.index("/* v658")]
	dong = js[js.index("function veT1("):js.index("function veU3(")]
	lop = set(re.findall(r"' (la|tiep|moi[\w-]*)'", dong))
	dung("đọc được lớp của thẻ", {"la", "tiep"} <= lop and any(x.startswith("moi") for x in lop))
	trung = [x for x in sorted(lop) if re.search(r"(^|[\s,}])\." + re.escape(x) + r"(?![\w-])", cu)]
	la("không lớp nào của thẻ T1 trùng lớp cũ", trung, [])


@ca("v658 ảnh trang đăng nhập: banner có chỗ Trang thành viên, chỉ dành cho banner; trang thành viên chỉ nhận banner đúng chỗ, đang bật, có ảnh")
def _():
	dung("club là chỗ banner", "club" in nw.VI_TRI_BANNER and "club" in nw.VI_TRI)
	nw._kiem_banner({"vi_tri": "club", "hien": True, "anh": "/files/a.jpg"})
	try:
		nw.chuan_hoa({"khoi": [{"id": "x", "loai": "thong_bao", "hien": True, "vi_tri": "club", "tieu_de": "a"}]})
		dung("khối thường không được đặt ở chỗ club", False)
	except ValueError:
		pass
	nd = {"khoi": [{"id": "a", "loai": "banner", "vi_tri": "club", "hien": True, "anh": "/files/a.jpg"},
		{"id": "b", "loai": "banner", "vi_tri": "dau_trang", "hien": True, "anh": "/files/b.jpg"},
		{"id": "c", "loai": "banner", "vi_tri": "club", "hien": False, "anh": "/files/c.jpg"}]}
	la("đúng chỗ, đang bật", [b["id"] for b in nw.banner_hien(nd, "club", "2026-11-14")], ["a"])
	js = open(os.path.join(GOC, "vagabond", "public", "web_order", "bien-tap-moi.js"), encoding="utf-8").read()
	dung("trình biên tập có chỗ Trang thành viên", "{ma: 'club', ten: 'Trang thành viên'" in js)


@ca("v658 dòng Thành viên từ: tháng và năm vào hệ thống")
def _():
	import sys
	import types
	from vagabond.khung.kiem_thu.nen import gia_lap
	gia_lap()
	rl = types.ModuleType("frappe.rate_limiter")
	rl.rate_limit = lambda *a, **k: (lambda f: f)
	sys.modules.setdefault("frappe.rate_limiter", rl)
	from vagabond import thanh_vien as tv
	la("ngày giờ", tv.thang_nam("2025-03-08 10:11:12"), "03/2025")
	la("rỗng", tv.thang_nam(None), "")


@ca("v658 trang chạy thật trong node (hanh_vi/thanh_vien_658.js): đăng nhập L3 + K1, J1c, T1 đủ bốn hạng, U3 theo hạn, không chữ tiền bánh")
def _():
	r = subprocess.run(["node", os.path.join(GOC, "vagabond", "khung", "kiem_thu", "hanh_vi", "thanh_vien_658.js")],
		capture_output=True, text=True, timeout=120)
	la("chạy xanh", (r.returncode, (r.stderr or "")[-400:], (r.stdout or "")[-800:] if r.returncode else ""), (0, "", ""))
	dung("đủ 13 ca", "13 ca đạt, 0 ca hỏng" in r.stdout)


@ca("v658 hoạ tiết lấy nguyên bộ Gạo Muối (không tự vẽ): đúng mã băm tệp gốc trên canvas thiết kế")
def _():
	import hashlib
	for ten, bam in (("03-quy-dao-bat-giac.svg", "080d278103d2cc21eccda73eeebfeca8bf10fbd9456e7f83b59f53b0701aca9a"),
			("14b-nguyen-tu.svg", "bbfdf0a00d7a6a70a9254c2fd93351e993a15eb99dff50b3fc7e23eaff205181")):
		p = os.path.join(GOC, "vagabond", "public", "web_order", "hoa-tiet", ten)
		la(ten, hashlib.sha256(open(p, "rb").read()).hexdigest(), bam)
	css = open(os.path.join(GOC, "vagabond", "public", "web_order", "thanh-vien.css"), encoding="utf-8").read()
	import re
	khoi = re.sub(r"/\*.*?\*/", "", css[css.index("/* v658 The Vagabond Club"):], flags=re.S)
	dung("không gradient", "gradient" not in khoi)
	dung("tắt chuyển động khi người dùng chọn giảm chuyển động", "prefers-reduced-motion" in khoi)

# -*- coding: utf-8 -*-
"""Màn Phiếu hoàn đơn huỷ, và luật ô tìm phải chạy ở máy chủ.

Anh Việt 31/08/2026, hai việc trong một câu:

	*"thêm dùm anh nút để xem lại danh sách các phiếu hoàn cho đơn đã huỷ
	của pancake để sales theo dõi, nối các trạng thái, hồ sơ, uỷ nhiệm
	chi... anh nhớ phần ô tìm kiếm đã yêu cầu viết ở backend cho MỌI MÀN"*

Hai bộ ca ở đây:

1. Dây chuyền bốn bước của một phiếu hoàn, tính bằng phép THUẦN nên kiểm
   được không cần site.

2. Luật ô tìm. Đây là loại hỏng im lặng nhất trong repo: màn vẫn chạy, vẫn
   ra kết quả, chỉ là kết quả tìm trong đúng N dòng mới nhất. Đơn cũ hơn N
   thì gõ mã ra danh sách rỗng và người dùng kết luận đơn đã mất. Ca kiểm
   quét mã nguồn tìm đúng cái dấu vết đó: một hàm nhận `tim`, đọc dữ liệu
   với `limit_page_length` khác 0, rồi lọc lại bằng Python.
"""

import io
import os
import re

from vagabond.khung.kiem_thu.nen import ca, dung, la


def _goc_app():
	from vagabond import don_huy

	return os.path.dirname(os.path.abspath(don_huy.__file__))


# ------------------------------------------------ dây chuyền bốn bước


@ca("phiếu hoàn: vừa lập xong thì đang chờ kế toán đính uỷ nhiệm chi")
def _():
	from vagabond.don_huy import buoc_cua_phieu

	xong, cho, cau = buoc_cua_phieu("Cho chi", co_unc=0, da_ghi_so=0, da_doi_soat=0)
	la("mới qua bước lập", xong, 1)
	la("đang chờ uỷ nhiệm chi", cho, "unc")
	dung("câu nói nhắc đúng việc", "uỷ nhiệm chi" in cau)


@ca("phiếu hoàn: có uỷ nhiệm chi rồi thì chuyển sang chờ ghi sổ")
def _():
	from vagabond.don_huy import buoc_cua_phieu

	xong, cho, _c = buoc_cua_phieu("Cho chi", co_unc=1, da_ghi_so=0, da_doi_soat=0)
	la("qua hai bước", xong, 2)
	la("chờ ghi sổ", cho, "ghi")


@ca("phiếu hoàn: ghi sổ xong thì chờ khớp sao kê")
def _():
	from vagabond.don_huy import buoc_cua_phieu

	xong, cho, _c = buoc_cua_phieu("Da chi", co_unc=1, da_ghi_so=1, da_doi_soat=0)
	la("qua ba bước", xong, 3)
	la("chờ đối soát", cho, "soat")


@ca("phiếu hoàn: đối soát xong là hết việc, không còn bước nào chờ")
def _():
	from vagabond.don_huy import buoc_cua_phieu

	xong, cho, _c = buoc_cua_phieu("Da doi soat", co_unc=1, da_ghi_so=1, da_doi_soat=1)
	la("đủ bốn bước", xong, 4)
	la("không chờ ai", cho, "")


@ca("phiếu hoàn: trạng thái Hoàn thành thì đủ bốn bước dù cờ đối soát chưa bật")
def _():
	from vagabond.don_huy import buoc_cua_phieu

	xong, cho, _c = buoc_cua_phieu("Hoan thanh")
	la("đủ bốn bước", xong, 4)
	la("không chờ ai", cho, "")


@ca("phiếu hoàn: phiếu đã huỷ thì không đứng ở bước nào")
def _():
	from vagabond.don_huy import buoc_cua_phieu

	xong, cho, cau = buoc_cua_phieu("Da huy", co_unc=1, da_ghi_so=1)
	la("không bước nào", xong, 0)
	la("không chờ ai", cho, "")
	dung("nói rõ là đã huỷ", "huỷ" in cau)


@ca("phiếu hoàn: ghi sổ rồi mà chưa kịp đính uỷ nhiệm chi vẫn tính là qua bước ghi")
def _():
	# Ca that: hook chan ghi so khi thieu UNC chi ap cho phieu sinh tu luong
	# hoan tien. Phieu cu tu truoc khi co hook thi ghi so roi ma khong co
	# tep nao. Day chuyen phai doc duoc ca do chu khong duoc tut nguoc.
	from vagabond.don_huy import buoc_cua_phieu

	xong, _cho, _c = buoc_cua_phieu("Da chi", co_unc=0, da_ghi_so=1)
	la("vẫn ba bước", xong, 3)


@ca("phiếu hoàn: nhãn trạng thái nào cũng có tiếng Việt, không lòi khoá không dấu")
def _():
	from vagabond.don_huy import NHAN_TT_PHIEU, TT_PHIEU

	for k in TT_PHIEU:
		dung("có nhãn cho %s" % k, bool(NHAN_TT_PHIEU.get(k)))
		dung("nhãn khác khoá: %s" % k, NHAN_TT_PHIEU[k] != k)


@ca("phiếu hoàn: đếm chip cộng lại bằng tổng")
def _():
	from vagabond.don_huy import dem_theo_tt_phieu

	d = dem_theo_tt_phieu([
		{"trang_thai": "Cho chi"}, {"trang_thai": "Cho chi"},
		{"trang_thai": "Hoan thanh"}, {"trang_thai": "La gi do"},
	])
	la("chờ chi", d["Cho chi"], 2)
	la("hoàn thành", d["Hoan thanh"], 1)
	la("tổng đếm cả dòng lạ", d["tat_ca"], 4)


# ------------------------------------------------------- luật ô tìm


@ca("ô tìm: rỗng thì trả None chứ không trả danh sách rỗng")
def _():
	from vagabond.don_huy import dieu_kien_tim

	# `or_filters=[]` va `or_filters=None` la hai chuyen khac han voi Frappe.
	la("rỗng", dieu_kien_tim("", ("a", "b")), None)
	la("toàn khoảng trắng", dieu_kien_tim("   ", ("a",)), None)
	la("None", dieu_kien_tim(None, ("a",)), None)


@ca("ô tìm: dựng đủ một điều kiện cho mỗi ô, dạng like hai đầu")
def _():
	from vagabond.don_huy import dieu_kien_tim

	dk = dieu_kien_tim("  92583 ", ("ma_don", "ten_khach"))
	la("hai điều kiện", len(dk), 2)
	la("ô đầu", dk[0], ["ma_don", "like", "%92583%"])
	la("ô sau", dk[1], ["ten_khach", "like", "%92583%"])


@ca("ô tìm: màn Đơn đã huỷ và màn Phiếu hoàn đều đẩy ô tìm xuống máy chủ")
def _():
	import inspect

	from vagabond import don_huy as dh

	for ham in (dh.ds, dh.ds_phieu):
		c = inspect.getsource(ham)
		dung("%s dùng or_filters" % ham.__name__, "or_filters=hoac" in c)
		dung("%s dựng điều kiện bằng hàm chung" % ham.__name__,
			"dieu_kien_tim(" in c)
	# Dem chip phai chay tren CUNG bo loc va CUNG o tim, khong thi go mot cai
	# ten ra 2 dong ma chip van bao 40. Hai man lam theo hai duong khac nhau
	# vi hinh dang du lieu khac nhau, nhung ket qua phai nhu nhau:
	#   - man Don da huy dem bang mot cau truy van thu hai, cung or_filters.
	#   - man Phieu hoan doc HET so mot lan roi dem trong Python, vi diem ban
	#     nam tren hoa don chu khong nam tren ho so, khong dua xuong SQL duoc.
	c1 = inspect.getsource(dh.ds)
	dung("màn Đơn đã huỷ đếm bằng truy vấn thứ hai", c1.count("or_filters=hoac") >= 2)
	c2 = inspect.getsource(dh.ds_phieu)
	dung("màn Phiếu hoàn đọc hết sổ rồi mới đếm", "limit_page_length=0" in c2)
	dung("màn Phiếu hoàn không cắt dòng trước khi đếm",
		c2.index('"tat_ca"') < c2.index("ra[:tran]"))


@ca("ô tìm: không màn nào được lọc lại bằng Python sau khi đã cắt dòng")
def _():
	"""Quét toàn bộ mô đun nghiệp vụ, chốt cho MỌI MÀN chứ không riêng một màn.

	Dấu vết cần bắt: hàm nhận tham số `tim`, đọc dữ liệu với một
	`limit_page_length` khác 0, rồi dựng lại danh sách bằng list comprehension
	có so chuỗi ô tìm. Đó chính là hình dạng của lỗi ở màn Đơn đã huỷ (cắt 200
	dòng rồi mới lọc) và màn Báo giá (cắt 400 tờ rồi mới lọc).
	"""
	goc = _goc_app()
	bo_qua = {
		# `cong_thuc.danh_sach` doc 1200 dong cho ~382 cong thuc, tuc la doc
		# HET so, va o tim phai ghep ten mon tu doctype Item nen khong dua
		# xuong mot cau SQL duoc. Da soat tay 31/08/2026, khong phai ca hong.
		"cong_thuc.py",
	}
	hong = []
	for ten in sorted(os.listdir(goc)):
		if not ten.endswith(".py") or ten in bo_qua:
			continue
		s = io.open(os.path.join(goc, ten), encoding="utf-8").read()
		for m in re.finditer(r"^def (\w+)\(([^)]*)\):", s, re.M):
			if not re.search(r"\btim\b", m.group(2)):
				continue
			i = m.end()
			j = s.find("\ndef ", i)
			than = s[i:len(s) if j < 0 else j]
			cat_truoc = re.search(r"limit_page_length\s*=\s*(?!0\b)", than)
			loc_sau = re.search(r"=\s*\[\s*\w+\s+for\s+\w+\s+in\s+", than)
			if cat_truoc and loc_sau and re.search(r"\btim\b|\bq\b", than):
				hong.append("%s.%s" % (ten[:-3], m.group(1)))
	dung("không hàm nào lọc ô tìm sau khi cắt dòng: " + ", ".join(hong), not hong)


@ca("phiếu hoàn: uỷ nhiệm chi trả về đường dẫn tệp chứ không chỉ một cái cờ")
def _():
	import inspect

	from vagabond import don_huy as dh

	c = inspect.getsource(dh.ds_phieu)
	# Sales can TAI VE de gui khach, do la ca ly do co man nay. Chi tra cai
	# dau tich co/khong thi man dung duoc nhung viec van khong xong.
	dung("có gom tệp uỷ nhiệm chi", "_unc_theo_phieu_chi(" in c)
	dung("có trả danh sách tệp ra màn", '"unc"' in c or "'unc'" in c)
	u = inspect.getsource(dh._unc_theo_phieu_chi)
	dung("lấy file_url", "file_url" in u)
	dung("một câu cho cả trang", '["in", list(ma_pc)]' in u)


@ca("phiếu hoàn: lấy đủ BỐN loại phiếu, không lọc riêng phiếu Pancake")
def _():
	# Anh Viet 31/08/2026 doi gop ca danh muc phieu hoan tien vao day, vi
	# man cu chi co ben phan he Ke toan ma phan he do da khoa lai.
	import inspect

	from vagabond import don_huy as dh

	c = inspect.getsource(dh.ds_phieu)
	dung("không còn khoá cứng loại Pancake",
		'"loai_hoan": LOAI_HUY_PANCAKE' not in c)
	dung("đọc hết sổ rồi mới lọc", "limit_page_length=0" in c)


@ca("phiếu hoàn: loại rỗng đọc là Trả hàng, không bị rơi khỏi danh sách")
def _():
	# 10 tren 16 phieu dang co mang loai rong, vi chung lap truoc 18/08/2026
	# khi chua co o "Loai phieu". Bo sot nhom nay la mat hon nua danh sach.
	from vagabond.don_huy import loai_thuc
	from vagabond.hoan_tien import LOAI_TRA_HANG

	la("rỗng", loai_thuc(""), LOAI_TRA_HANG)
	la("None", loai_thuc(None), LOAI_TRA_HANG)
	la("toàn khoảng trắng", loai_thuc("   "), LOAI_TRA_HANG)
	la("có loại thì giữ nguyên", loai_thuc("Tien nop thua"), "Tien nop thua")


@ca("phiếu hoàn: đủ bốn chip loại, nhãn nào cũng có tiếng Việt")
def _():
	from vagabond.don_huy import cac_loai_hoan

	ds = cac_loai_hoan()
	la("bốn loại", len(ds), 4)
	for k, ten in ds:
		dung("nhãn khác khoá: %s" % k, ten != k)
		dung("nhãn có chữ: %s" % k, bool(str(ten).strip()))


@ca("điểm bán: phiếu huỷ đơn Pancake luôn thuộc Sales Online")
def _():
	from vagabond.don_huy import diem_cua_phieu
	from vagabond.hoan_tien import LOAI_HUY_PANCAKE

	# Don Pancake chua bao gio co hoa don nen khong co quay de doc. Suy
	# thang tu loai phieu, khong hoi hoa don.
	la("không cần quầy", diem_cua_phieu(LOAI_HUY_PANCAKE), "SALES")
	la("có truyền quầy cũng vậy", diem_cua_phieu(LOAI_HUY_PANCAKE, "TCV"), "SALES")


@ca("điểm bán: không có hoá đơn thì trả rỗng, KHÔNG đoán bừa là Sales Online")
def _():
	from vagabond.don_huy import diem_cua_phieu
	from vagabond.hoan_tien import LOAI_TRA_HANG

	# Doan sai mot diem ban la lam lech so lieu cua ca mot cua hang.
	la("trả hàng không hoá đơn", diem_cua_phieu(LOAI_TRA_HANG, None), "")
	la("loại rỗng không hoá đơn", diem_cua_phieu("", None), "")


@ca("phiếu hoàn: ba họ chip đều lọc được, và cắt dòng làm ở bước cuối")
def _():
	import inspect

	from vagabond import don_huy as dh

	c = inspect.getsource(dh.ds_phieu)
	chu_ky = [d for d in c.split("\n") if d.startswith("def ds_phieu(")][0]
	for t in ("diem", "loai", "trang_thai", "tim"):
		dung("nhận tham số %s" % t, ("%s=" % t) in chu_ky)
	dung("trả đếm điểm bán", '"dem_diem"' in c)
	dung("trả đếm loại phiếu", '"dem_loai"' in c)
	# Cat dong PHAI o buoc cuoi, sau khi da loc va da dem xong. Cat truoc la
	# dung cai bay ma `thu_chan_man` va ca kiem o tim canh.
	dung("cắt dòng sau khi đếm", "ra[:tran]" in c)
	dung("đếm trước khi cắt", c.index('"tat_ca"') < c.index("ra[:tran]"))


@ca("phiếu hoàn: màn Sales chỉ đọc, không có hàm nào sửa hồ sơ của kế toán")
def _():
	import inspect

	from vagabond import don_huy as dh

	for ham in (dh.ds_phieu, dh.xuat_excel_phieu, dh._unc_theo_phieu_chi,
			dh._ten_diem):
		c = inspect.getsource(ham)
		for cam in ("frappe.get_doc(", ".save(", ".submit(", "frappe.db.set_value("):
			dung("%s không %s" % (ham.__name__, cam.strip("(.")), cam not in c)


@ca("phiếu hoàn: màn có nghe cú bấm trên root, nút chân màn bấm được")
def _():
	# Cung mot loai loi da giet nut Dong bo Pancake tu ngay dung man 29.
	# Man moi nao co chan man cung phai qua cua nay. `thu_chan_man.py` quet
	# toan bo, day la chot rieng cho man vua dung.
	bep = os.path.join(_goc_app(), "public", "js", "bep")
	s = io.open(os.path.join(bep, "40-phieu-hoan-huy.js"), encoding="utf-8").read()
	dung("nghe trên root", "root.addEventListener('click', phBam)" in s)
	dung("có nút ở chân màn", "data-phb=" in s)
	dung("nút tải tệp không bị nuốt bởi lắng nghe uỷ quyền",
		"closest('a[href]')" in s)
	for t in ("data-phd", "data-phlo", "data-phl"):
		dung("có hàng chip %s" % t, ("'%s'" % t) in s)
	# Nhan chip trang thai do MAY CHU gui xuong. Man tu che bang thu hai la
	# cach sinh ra sau con chip hien nguyen khoa khong dau, 22/08/2026.
	dung("nhãn chip trạng thái đọc từ máy chủ", "kq.nhan || {}" in s)

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
		# Dem chip phai chay tren CUNG bo loc va CUNG o tim, khong thi go
		# mot cai ten ra 2 dong ma chip van bao 40.
		dung("%s đếm chip theo đúng ô tìm" % ham.__name__,
			c.count("or_filters=hoac") >= 2)


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


@ca("phiếu hoàn: chỉ lấy phiếu của đơn Pancake đã huỷ, không lẫn phiếu trả hàng")
def _():
	import inspect

	from vagabond import don_huy as dh

	c = inspect.getsource(dh.ds_phieu)
	dung("lọc theo loại phiếu", '"loai_hoan": LOAI_HUY_PANCAKE' in c)
	dung("đọc hằng từ hoan_tien chứ không tự chế chuỗi",
		"from vagabond.hoan_tien import LOAI_HUY_PANCAKE" in c)


@ca("phiếu hoàn: màn Sales chỉ đọc, không có hàm nào sửa hồ sơ của kế toán")
def _():
	import inspect

	from vagabond import don_huy as dh

	for ham in (dh.ds_phieu, dh.xuat_excel_phieu, dh._unc_theo_phieu_chi):
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

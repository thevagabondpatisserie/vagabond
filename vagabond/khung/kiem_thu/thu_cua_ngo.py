"""Canh cua vao cua may chu: ham nao dang duoc goi tu ngoai.

Vi sao co tep nay
-----------------
Ngay 19/08/2026, khi them ham `dong_bo_so_hddt` vao `hoan_tien.py`, em chen
no vao ngay TRUOC dong `def ds(...)`. Ma phia tren `def ds` la dong
`@frappe.whitelist()`. Ket qua: cai decorator do bam vao ham moi, con `ds`
thi mat quyen goi.

Python khong bao gi ca. Kiem thu cung khong bao, vi khong ca nao goi `ds`.
Cong tam cong doan van tra ve 0. Chi den luc mo man Hoan tien tren app moi
ra loi "Ham vagabond.hoan_tien.ds chua duoc whitelist" - tuc la sales va ke
toan chiu tran.

Day la kieu loi khong the bat bang cach doc lai code cho ky hon, vi no vo
hinh: hai dong dung canh nhau, doi cho la hong, ma nhin thi van rat hop ly.
Nen phai chot bang mot danh sach viet ro ra.

Cach dung khi them ham moi
--------------------------
Them ham CO whitelist thi them ten vao danh sach duoi day. Ca kiem se do.
Neu ca kiem bao thua hoac thieu mot ten ma minh khong co y dinh doi, thi
gan nhu chac chan la mot decorator vua bam nham ham.
"""

import ast
import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la

# Ba lan dirname tu tep nay ra dung thu muc goi `vagabond/`, tuc cho dat
# hoan_tien.py, mua_dich_vu.py va cac mo dun nghiep vu khac.
GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Danh sach cua ngo tung mo dun. Chot ngay 19/08/2026.
CUA_NGO = {
	"hoan_tien.py": [
		"chi_tiet", "dem_cho_chi", "doi_soat", "ds", "ds_ngan_hang",
		# gan_gd_vao them ngay 19/08/2026: gan tay mot khoan tien VAO cho
		# phieu hoan, dung cho ca khach tu go noi dung chuyen khoan nen may
		# khong tu khop duoc (ca Ms.Giang, HT-2026-00912).
		"gan_gd_vao",
		"sepay_tien_ra", "tao", "tao_tien_du", "thong_tin_chuyen_khoan",
		"tinh_trang", "tu_choi", "xem_tien_du",
	],
}


def _ten_whitelist(duong_dan):
	"""Doc thang tu MA NGUON, khong nap mo dun. THUAN theo nghia khong chay code.

	Doc bang ast chu khong import: import thi keo theo ca Frappe that, va
	quan trong hon, ham nao bi bam nham decorator thi khi import van chay
	binh thuong nen khong lo ra.
	"""
	cay = ast.parse(io.open(duong_dan, encoding="utf-8").read())
	ten = []
	for nut in cay.body:
		if not isinstance(nut, ast.FunctionDef):
			continue
		for d in nut.decorator_list:
			la_wl = (
				isinstance(d, ast.Call) and getattr(d.func, "attr", "") == "whitelist"
			) or getattr(d, "attr", "") == "whitelist"
			if la_wl:
				ten.append(nut.name)
				break
	return sorted(ten)


@ca("cửa ngõ: hoàn tiền mở đúng 13 hàm ra ngoài, không thừa không thiếu")
def _():
	# Ham `dong_bo_so_hddt` PHAI KHONG co trong danh sach: no ghi vao co so
	# du lieu va chi duoc goi tu ben trong. Neu no loi ra day nghia la
	# decorator lai bam nham lan nua.
	for tep, mong in CUA_NGO.items():
		duoc = _ten_whitelist(os.path.join(GOI, tep))
		la("số hàm mở ra ngoài của %s" % tep, len(duoc), len(mong))
		la("đúng danh sách của %s" % tep, duoc, sorted(mong))


@ca("cửa ngõ: hàm nội bộ đồng bộ số hoá đơn không được mở ra ngoài")
def _():
	duoc = _ten_whitelist(os.path.join(GOI, "hoan_tien.py"))
	dung("dong_bo_so_hddt phải nằm ngoài danh sách",
		"dong_bo_so_hddt" not in duoc)
	dung("ds phải nằm trong danh sách", "ds" in duoc)

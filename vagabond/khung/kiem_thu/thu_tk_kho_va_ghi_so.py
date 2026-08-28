"""Ca kiểm cho hàng rào tài khoản kho và quyền ghi sổ hoá đơn mua.

Chị Dung 28/08/2026, soi sổ cái PNK-2026-00224:

    *"Phiếu nhập kho phải vào 152 chứ không phải vào 155 á em, 155 là
    thành phẩm khi mình xuất bán thôi, với khi Uyên nối phiếu là máy tự
    ghi sổ luôn á em."*

Ba nhóm ca:

  1. Phép thuần soi tài khoản kho: 155x là thành phẩm, mua về không vào.
  2. Hàng rào chặn đúng lúc ghi sổ phiếu nhập, không chặn lúc lưu nháp,
     và không chặn phiếu trả hàng.
  3. Nối phiếu và ghi sổ là HAI quyền khác nhau: thu mua nối được, chỉ
     kế toán mới ghi sổ.

Mọi ca chạy trên phép THUẦN: đọc mã nguồn, không cần Frappe, không cần
site, không cần mạng, không cần thư viện requests.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BEP = os.path.join(GOI, "public", "js", "bep")


def _doc(ten):
	with io.open(os.path.join(GOI, ten), encoding="utf-8") as f:
		return f.read()


def _js(ten):
	with io.open(os.path.join(BEP, ten), encoding="utf-8") as f:
		return f.read()


def _than(s, dau, cuoi):
	i = s.find(dau)
	if i < 0:
		return ""
	j = s.find(cuoi, i + len(dau))
	return s[i:j if j > i else len(s)]


# ------------------------------------------- 1. Phép thuần soi tài khoản


@ca("tk kho: doc duoc so hieu tu ten tai khoan day du")
def _cat_so_hieu():
	from vagabond import gac_tk_kho as g

	la("cat khoi ten dai", g.so_hieu("1551 - Sản phẩm nhập kho - TV"), "1551")
	la("khong co gach", g.so_hieu("152"), "152")
	la("bo khoang trang", g.so_hieu("  153 - Công cụ  "), "153")
	la("rong thi rong", g.so_hieu(None), "")


@ca("tk kho: 155x la thanh pham, 152 153 156 thi khong")
def _nhan_ra_thanh_pham():
	from vagabond import gac_tk_kho as g

	# 155 theo TT200 la thanh pham DO CHINH doanh nghiep san xuat ra.
	dung("1551 la thanh pham", g.la_tk_thanh_pham("1551 - Sản phẩm nhập kho - TV"))
	dung("1557 la thanh pham", g.la_tk_thanh_pham("1557 - Thành phẩm bất động sản"))
	dung("155 la thanh pham", g.la_tk_thanh_pham("155"))
	# Thu mua ve thi khong bao gio la 155.
	dung("152 khong phai", not g.la_tk_thanh_pham("152 - Nguyên liệu, vật liệu - TV"))
	dung("153 khong phai", not g.la_tk_thanh_pham("153 - Công cụ, dụng cụ - TV"))
	dung("156 khong phai", not g.la_tk_thanh_pham("156 - Hàng hóa - TV"))
	# 154 dung truoc 155 mot so, khong duoc nham.
	dung("154 khong phai", not g.la_tk_thanh_pham("154 - Chi phí sản xuất dở dang - TV"))


@ca("tk kho: kho chua khai tai khoan thi KHONG chan, de ERPNext lay mac dinh")
def _kho_trong_khong_chan():
	from vagabond import gac_tk_kho as g

	la("de trong", g.soi_dong(""), g.TK_TRONG)
	la("None cung vay", g.soi_dong(None), g.TK_TRONG)
	la("152 thi cho qua", g.soi_dong("152 - Nguyên liệu, vật liệu - TV"), g.TK_OK)
	la("1551 thi chan", g.soi_dong("1551 - Sản phẩm nhập kho - TV"), g.TK_THANH_PHAM)


@ca("tk kho: cau bao noi ro phai lam gi va ai sua duoc")
def _cau_bao_dung_viec():
	from vagabond import gac_tk_kho as g

	c = g.loi_thanh_pham(3, "Khay giấy kraft", "Kho D1 - TV", "1551 - Sản phẩm nhập kho - TV")
	dung("noi so dong", "Dòng 3" in c)
	dung("noi ten mon", "Khay giấy kraft" in c)
	dung("noi ten kho", "Kho D1 - TV" in c)
	dung("noi tai khoan sai", "1551" in c)
	# Cau phai chi duong ra, khong duoc chi bao la sai.
	dung("chi duong chon kho khac", "chọn một kho vật tư" in c)
	dung("chi ro ai sua duoc", "chị Dung" in c)


# ------------------------------------- 2. Hàng rào gắn đúng chỗ, đúng lúc


@ca("tk kho: hook dat o before_submit chu khong phai validate")
def _dat_dung_cho():
	s = _doc("hooks.py")
	t = _than(s, '"Purchase Receipt": {', "\n\t\"Phieu Kiem Ke\"")
	dung("co gan hang rao", "vagabond.gac_tk_kho.chan_nhap_vao_thanh_pham" in t)
	# Luu nhap thi cu cho luu, chi chan luc con so sap cham so cai.
	i = t.find('"before_submit"')
	j = t.find("gac_tk_kho.chan_nhap_vao_thanh_pham")
	dung("nam trong khoi before_submit", 0 <= i < j)
	# Khong duoc lam mat hai hook cu cua phien khac o day.
	dung("giu hang rao don vi", "gac_don_vi.chan_don_vi_la" in t)
	dung("giu cau bao ngay don mua", "ngay_don_mua.bao_ngay_don_mua" in t)
	dung("giu ghi vet gia khi nhan", "gia_khi_nhan.ghi_vet" in t)


@ca("tk kho: phieu tra hang KHONG bi chan")
def _tra_hang_khong_chan():
	s = _doc("gac_tk_kho.py")
	t = _than(s, "def chan_nhap_vao_thanh_pham(", "\n@frappe.whitelist()")
	# Tra hang la dao nguoc mot to cu. Chan o day thi to nhap sai ngay
	# truoc khong sua duoc nua.
	dung("bo qua phieu tra hang", 'doc.get("is_return")' in t)
	i = t.find('doc.get("is_return")')
	dung("bo qua ngay tu dau", 0 <= i < t.find("for r in"))


@ca("tk kho: doc tai khoan MOT LAN cho moi kho, khong hoi lai tung dong")
def _khong_hoi_lai_tung_dong():
	s = _doc("gac_tk_kho.py")
	t = _than(s, "def chan_nhap_vao_thanh_pham(", "\n@frappe.whitelist()")
	dung("co bo nho tam", "da_soi" in t)
	dung("gom loi bao mot lan", "frappe.throw(" in t and '"<br><br>".join(loi)' in t)


@ca("tk kho: co cua soat kho chi doc, khong tu sua gi")
def _cua_soat_chi_doc():
	s = _doc("gac_tk_kho.py")
	# soat_kho la ham cuoi tep nen cat toi het tep, dung cat theo dong trong.
	t = s[s.find("def soat_kho("):]
	dung("co kiem quyen", "frappe.throw(" in t)
	dung("dem so phieu nhap da vao", "Purchase Receipt Item" in t)
	dung("chi ra kho dang ghi sai", "dang_ghi_sai" in t)
	# Tuyet doi khong duoc sua gi trong mot cua bao cao.
	for cam in ("db_set", "set_value", ".save()", ".submit()", "db.set_single_value"):
		dung("khong %s" % cam, cam not in t)


@ca("tk kho: phan thuan KHONG import frappe, chay duoc tren may CI tay khong")
def _phan_thuan_sach():
	s = _doc("gac_tk_kho.py")
	tren = s.split("import frappe")[0]
	dung("co vach ngan", "phần cần Frappe" in s)
	for cam in ("frappe.", "import frappe"):
		dung("phan tren khong dung %s" % cam, cam not in tren)
	# Ba ham thuan phai nam tren vach.
	for ham in ("def so_hieu(", "def la_tk_thanh_pham(", "def soi_dong(", "def loi_thanh_pham("):
		dung("%s nam tren vach" % ham, ham in tren)


# --------------------------- 3. Nối phiếu và ghi sổ là hai quyền khác nhau


@ca("ghi so: thu mua noi phieu duoc, chi ke toan moi ghi so")
def _hai_quyen_khac_nhau():
	s = _doc("doi_chieu_mua.py")
	# Vai duoc noi phieu van co Purchase Manager, de Uyen lam viec doi chieu.
	t1 = _than(s, "def _lam_duoc(", "\n\n")
	dung("noi phieu con thu mua", "Purchase Manager" in t1)
	# Vai duoc GHI SO thi khong.
	t2 = _than(s, "VAI_GHI_SO = {", "}")
	dung("ghi so co ke toan", "Accounts Manager" in t2 and "Accounts User" in t2)
	dung("ghi so KHONG co thu mua", "Purchase Manager" not in t2)
	dung("ghi so KHONG co thu kho", "Stock Manager" not in t2)


@ca("ghi so: chan ngay o dau cua noi_phieu, truoc khi dong vao chung tu")
def _chan_som():
	s = _doc("doi_chieu_mua.py")
	t = _than(s, "def noi_phieu(", "\n@frappe.whitelist()")
	dung("co chan", "_ghi_so_duoc()" in t)
	dung("chi chan khi that su ghi so", "cint(ghi_so) and not _ghi_so_duoc()" in t)
	# Phai chan TRUOC khi doc chung tu ra, khong thi chay het roi moi bao hong.
	dung("chan truoc khi mo chung tu",
	     t.find("_ghi_so_duoc()") < t.find('frappe.get_doc("Purchase Invoice"'))
	dung("cau bao chi duong", "Chỉ nối phiếu" in t)


@ca("ghi so: man hinh biet truoc, khong bay nut roi moi bao khong duoc phep")
def _man_hinh_biet_truoc():
	s = _doc("doi_chieu_mua.py")
	la("tra co ghi_so_duoc o ca hai man", s.count('"ghi_so_duoc": 1 if _ghi_so_duoc() else 0,'), 2)
	j = _js("18-doi-chieu-may-in.js")
	dung("man hinh doc co", "kq.ghi_so_duoc" in j)
	dung("khong du quyen thi doi nhan nut", "Nối phiếu, chuyển kế toán ghi sổ" in j)
	dung("noi ro to hoa don di dau", "Chờ ghi sổ" in j)

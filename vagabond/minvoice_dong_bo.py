# -*- coding: utf-8 -*-
"""Keo hoa don tu M-Invoice ve bang MInvoice Invoice, ban trong ma nguon.

Vi sao tep nay ton tai
----------------------
Truoc 20/08/2026 viec keo nam trong mot Server Script tren site ("MInvoice
Daily Pull", cron 15 phut). Ngay 20/08 anh Viet phat hien hoa don dau vao
bi sot tu 14/08 (to 598 cua CACAO BEN TRE 1.590.000 d khong co trong he).
Doc Error Log ra ba nguyen nhan, ca ba deu nam trong cach kich ban cu chay:

1. DAU RA keo truoc, dau vao xep sau trong CUNG mot vong lap. Moi lan ket
   noi sang M-Invoice dut giua chung (ChunkedEncodingError, 502 - co that
   trong Error Log tu 13/08) la ca luot chet, va dau vao chet chum theo
   dau ra. Hoa don mua bi sot tu do.

2. "VO RUOT" khong bao gio lanh. M-Invoice tra ve hoa don vua phat hanh
   voi du lieu con trong (shdon=0, chua co ten nguoi ban). Kich ban cu
   insert mot lan roi exists() bo qua vinh vien, nen ban ghi nam do voi
   so_hd=0 va khong bao gio thanh Hoa don mua. Dem duoc 102 ban ghi nhu
   the tren site ngay 20/08.

3. GET khong commit. Goi thu kich ban qua GET thay tra ve "moi: 33" ma so
   khong nhich: Frappe rollback moi thay doi cua mot request GET. Ma o day
   commit TUNG TRANG ngay trong vong lap nen GET hay POST deu ghi that,
   va mot trang loi khong keo do nhung trang da xong.

Tep nay sua ca ba: dau vao keo TRUOC, moi loai boc rieng trong try/except,
gap ban ghi vo ruot ma M-Invoice da co du lieu thi do lai cho day du, va
commit tung trang. Kich ban cu tren site giu nguyen mot thoi gian de doi
chieu (hai duong cung idempotent, khong sinh trung), go sau khi ban nay
chay on.

Doctype "MInvoice Settings" va "MInvoice Invoice" la doctype khai tren
site, khong nam trong repo nay. Ma o day chi DOC va GHI vao chung, khong
dung cau truc.
"""

# ------------------------------------------------------------ phan thuan
# Cac ham tren day `import frappe` la ham THUAN: bo kiem thu nap bang
# python3 tran, khong can Frappe. Them ham can frappe thi dat DUOI cho
# import, dung chen len tren.

TTHAI_MAP = {
	"1": "Gốc",
	"2": "Thay thế",
	"3": "Điều chỉnh",
	"4": "Bị thay thế",
	"5": "Bị điều chỉnh",
	"6": "Đã huỷ",
}

LOAI_VAO = "Đầu vào"
LOAI_RA = "Đầu ra"


def trang_thai_chu(tthai):
	"""Ma trang thai cua CQT thanh chu de doc. Ma la thi tra nguyen ma."""
	t = str(tthai if tthai is not None else "")
	return TTHAI_MAP.get(t, t)


def ma_tra_cuu_cua(inv):
	"""Ma tra cuu nam trong mang ttkhac, phai do tung dong moi thay."""
	for t in (inv.get("ttkhac") or []):
		if isinstance(t, dict) and t.get("ttruong") == "Mã tra cứu":
			return t.get("dlieu")
	return None


def doi_tac_cua(inv, loai):
	"""Ten, ma so thue va dia chi cua ben doi tac.

	Hoa don DAU RA thi doi tac la nguoi MUA (nm...), dau vao thi doi tac
	la nguoi BAN (nb...). Nham hai tien to nay la ca bang ke sai ten.
	"""
	if loai == LOAI_RA:
		return {
			"ten": inv.get("nmten"),
			"mst": inv.get("nmmst"),
			"dia_chi": inv.get("nmdchi"),
		}
	return {
		"ten": inv.get("nbten"),
		"mst": inv.get("nbmst"),
		"dia_chi": inv.get("nbdchi"),
	}


def hd_goc_chu(inv):
	"""Chuoi mo ta hoa don goc khi to nay la thay the/dieu chinh."""
	if not inv.get("shdgoc"):
		return ""
	ra = "KH %s - So %s" % (str(inv.get("khhdgoc") or ""), str(inv.get("shdgoc")))
	if inv.get("tdlhdgoc"):
		ra += " - Ngay " + str(inv.get("tdlhdgoc"))[:10]
	return ra


def vo_ruot(so_hd_dang_luu, inv):
	"""Ban ghi da co ma ruot con trong, va M-Invoice nay da co so that.

	"Vo ruot" la ban ghi insert luc M-Invoice chua kip do du lieu vao hoa
	don vua phat hanh: so_hd bang 0 hoac rong. Chi do lai khi ho DA co
	shdon that, con ho van tra ve trong thi cho luot sau.
	"""
	return (not so_hd_dang_luu) and bool(inv.get("shdon"))


# ------------------------------------------------------- phan can Frappe

import json

import frappe
from frappe.utils import cint

DT_HD = "MInvoice Invoice"
DT_CAI_DAT = "MInvoice Settings"

# So trang toi da mot luot cho MOT loai hoa don. 300 trang x 100 to la
# 30.000 to, gap nhieu lan ca nam cua tiem - cham tran nghia la co gi do
# sai chu khong phai du lieu that nhieu den vay.
TRANG_TOI_DA = 300


def _cai_dat():
	stg = frappe.get_doc(DT_CAI_DAT)
	token = stg.get_password("api_token", raise_exception=False)
	if not token:
		frappe.throw(
			"Chưa có API Token của M-Invoice. Mở 'MInvoice Settings' trên Desk, "
			"dán token vào ô API Token rồi chạy lại giúp em."
		)
	return {
		"token": token,
		"base": (stg.get("base_url") or "https://qlhd.minvoice.com.vn").rstrip("/"),
		"so_ngay": cint(stg.get("so_ngay_keo")) or 7,
		"keo_vao": cint(stg.get("keo_dau_vao")),
		"keo_ra": cint(stg.get("keo_dau_ra")),
	}


def _goi_minvoice(cd, tham_so):
	"""GET /erp/qlhd-api/invoices voi apiToken. Tra ve dict cua M-Invoice."""
	from frappe.integrations.utils import make_get_request

	return make_get_request(
		cd["base"] + "/erp/qlhd-api/invoices",
		headers={"apiToken": cd["token"]},
		params=tham_so,
	) or {}


def _extra(inv, loai):
	"""Cac truong phu ngoai bo truong chinh. Dung chung cho insert va do lai."""
	ex = {
		"mau_so": str(inv.get("khmshdon") or ""),
		"trang_thai": trang_thai_chu(inv.get("tthai")),
		"dia_chi_doi_tac": doi_tac_cua(inv, loai)["dia_chi"],
		"chiet_khau": inv.get("ttcktmai") or 0,
	}
	if inv.get("nky"):
		try:
			ex["ngay_ky"] = str(
				frappe.utils.add_to_date(
					frappe.utils.get_datetime(
						str(inv.get("nky")).replace("Z", "").split(".")[0]
					),
					hours=7,
				)
			)[:10]
		except Exception:
			pass
	goc = hd_goc_chu(inv)
	if goc:
		ex["hd_goc"] = goc
	if inv.get("thttltsuat"):
		ex["ke_thue"] = json.dumps(inv.get("thttltsuat"), ensure_ascii=False)
	return ex


def _du_lieu(inv, loai):
	"""Toan bo ruot cua mot ban ghi, dung chung cho INSERT va DO LAI VO RUOT.

	Mot ham mot su that: sua truong nao thi ca hai duong cung doi theo.
	Kich ban cu co hai doan gan roi rac va da tung lech nhau.
	"""
	dt = doi_tac_cua(inv, loai)
	ngay = None
	if inv.get("tdlap"):
		ngay = frappe.utils.add_to_date(
			frappe.utils.get_datetime(str(inv.get("tdlap") or "").replace("Z", "")),
			hours=7,
		)
	du = {
		"loai": loai,
		"ky_hieu": inv.get("khhdon"),
		"so_hd": inv.get("shdon"),
		"ngay_lap": str(ngay)[:10] if ngay else None,
		"nguoi_mua_ban": dt["ten"],
		"mst_doi_tac": dt["mst"],
		"tien_truoc_thue": inv.get("tgtcthue"),
		"tien_thue": inv.get("tgtthue"),
		"tong_tien": inv.get("tgtttbso"),
		"ht_thanh_toan": inv.get("thtttoan"),
		"ma_cqt": inv.get("mhdon"),
		"ma_tra_cuu": ma_tra_cuu_cua(inv),
		"chi_tiet": json.dumps(inv.get("hdhhdvu") or [], ensure_ascii=False),
	}
	du.update(_extra(inv, loai))
	return du


def _keo(so_ngay=None, tu_ngay="", den_ngay="", chi_loai="", do_lai_het=0):
	"""Keo mot luot. Tra ve so dem tung viec da lam.

	tu_ngay/den_ngay theo dd/MM/yyyy (dinh dang M-Invoice doi). Bo trong
	thi lay so_ngay gan nhat theo cai dat.
	"""
	cd = _cai_dat()
	so_ngay = cint(so_ngay) or cd["so_ngay"]
	d_tu = tu_ngay or frappe.utils.formatdate(
		frappe.utils.add_days(frappe.utils.nowdate(), -so_ngay), "dd/MM/yyyy"
	)
	d_den = den_ngay or frappe.utils.formatdate(frappe.utils.nowdate(), "dd/MM/yyyy")

	# DAU VAO TRUOC. Xem ghi chu so 1 o dau tep: dau vao ma xep sau la no
	# ganh moi cu dut ket noi cua dau ra.
	cac_loai = []
	if cd["keo_vao"]:
		cac_loai.append(("INPUT_ELECTRONIC_INVOICE", LOAI_VAO))
	if cd["keo_ra"]:
		cac_loai.append(("OUTPUT_ELECTRONIC_INVOICE", LOAI_RA))
	if chi_loai == "in":
		cac_loai = [("INPUT_ELECTRONIC_INVOICE", LOAI_VAO)]
	elif chi_loai == "out":
		cac_loai = [("OUTPUT_ELECTRONIC_INVOICE", LOAI_RA)]

	moi, lanh, quet, cap_nhat, loi_o_loai = 0, 0, 0, 0, []
	for itype, loai in cac_loai:
		trang = 1
		# Moi LOAI boc rieng: dau ra dut giua chung thi dau vao da keo
		# xong van con nguyen, khong chet chum nhu kich ban cu.
		try:
			while trang <= TRANG_TOI_DA:
				resp = _goi_minvoice(cd, {
					"page": trang, "size": 100, "invoiceType": itype,
					"invoiceReleaseDateFrom": d_tu, "invoiceReleaseDateTo": d_den,
				})
				lo = resp.get("listInvoice") or []
				for inv in lo:
					quet += 1
					hid = inv.get("id") or inv.get("_id")
					if not hid:
						continue
					if frappe.db.exists(DT_HD, hid):
						cu_so = frappe.db.get_value(DT_HD, hid, "so_hd")
						if vo_ruot(cu_so, inv):
							# Vo ruot: luc keo lan dau M-Invoice chua co du
							# lieu. Nay ho da co thi do lai day du.
							frappe.db.set_value(DT_HD, hid, _du_lieu(inv, loai))
							lanh += 1
						elif cint(do_lai_het):
							frappe.db.set_value(DT_HD, hid, _extra(inv, loai))
							cap_nhat += 1
						continue
					doc = frappe.get_doc({"doctype": DT_HD, "ma_hd_id": hid})
					doc.update(_du_lieu(inv, loai))
					doc.insert(ignore_permissions=True)
					moi += 1
				# Ghi xuong TUNG TRANG: trang sau co loi thi trang nay van con,
				# va nho vay GET hay POST goi vao cung ghi that nhu nhau.
				frappe.db.commit()
				if trang >= (resp.get("totalPage") or 1):
					break
				trang += 1
		except Exception:
			loi_o_loai.append(loai)
			frappe.log_error(
				frappe.get_traceback(), "MInvoice: dut giua chung o loai " + loai
			)
	return {
		"moi": moi, "chua_lanh": lanh, "da_quet": quet, "cap_nhat": cap_nhat,
		"loi_o_loai": loi_o_loai, "tu_ngay": d_tu, "den_ngay": d_den,
	}


@frappe.whitelist()
def keo(so_ngay=None, tu_ngay="", den_ngay="", chi_loai="", do_lai_het=0):
	"""Chay tay mot luot keo, dung cho keo bu khi phat hien sot.

	Chi ke toan va quan ly: duong nay ghi hang loat vao bang hoa don.
	"""
	if not {"System Manager", "Accounts Manager"} & set(frappe.get_roles()):
		frappe.throw(
			"Chỉ quản lý hoặc kế toán mới chạy kéo bù hoá đơn được. Nhờ chị "
			"Dung hoặc anh Việt chạy giúp."
		)
	return _keo(so_ngay, tu_ngay, den_ngay, chi_loai, do_lai_het)


def dong_bo_tu_dong():
	"""Nhip 15 phut. Khong throw: loi ghi vao Error Log roi doi nhip sau."""
	try:
		if not frappe.db.exists("DocType", DT_CAI_DAT):
			return
		_keo()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "MInvoice: nhip 15 phut vo loi")


def tu_lanh_hang_dem():
	"""Nhip 1h dem: quet lui 30 ngay de lanh not vo ruot va vet sot cu.

	Nhip 15 phut chi nhin so_ngay_keo gan nhat (mac dinh 7 ngay). Hoa don
	phat hanh cham, bi thay the, hay vo ruot qua 7 ngay thi chi nhip dem
	nay cham toi.
	"""
	try:
		if not frappe.db.exists("DocType", DT_CAI_DAT):
			return
		_keo(so_ngay=30)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "MInvoice: nhip dem vo loi")

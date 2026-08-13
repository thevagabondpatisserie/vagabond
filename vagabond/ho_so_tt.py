# -*- coding: utf-8 -*-
"""Hồ sơ thanh toán nhà cung cấp (APP) - lập, duyệt hai cấp, trả tiền, báo NCC.

Anh Việt 13/08/2026: "anh thấy thao tác trên desktop bị rối quá nên mình
làm trên app". Luồng thật ở tiệm:

  Thu mua gom hoá đơn mua đến hạn của MỘT nhà cung cấp thành một hồ sơ
  -> gửi kế toán (FIN) duyệt
  -> gửi giám đốc duyệt
  -> kế toán chuyển tiền
  -> máy dò SePay khớp giao dịch, sinh Payment Entry để clear công nợ
  -> bấm một nút gửi thư báo nhà cung cấp đã thanh toán

Vì sao KHÔNG dùng thẳng Payment Entry của ERPNext làm hồ sơ: Payment Entry
là bút toán chi tiền, nó sinh ra SAU khi đã duyệt. Cái thiếu là khúc TRƯỚC
đó - đề nghị, duyệt hai cấp, và dấu vết ai duyệt lúc nào. Doctype
Vagabond Ho So TT giữ khúc đó; đến lúc trả tiền mới sinh Payment Entry thật.

Ba điều phải giữ:
  1. Một hoá đơn không nằm trong hai hồ sơ còn hiệu lực (chặn ở doctype).
  2. Duyệt phải ĐÚNG THỨ TỰ: kế toán trước, giám đốc sau. Nhảy cóc là mất
     lớp kiểm soát.
  3. Người lập KHÔNG tự duyệt hồ sơ của chính mình.
"""

import base64
import io
import re

import frappe
from frappe.utils import add_days, cint, flt, getdate, now_datetime, nowdate

from vagabond.lib import cfg

# Bốn vai được đụng tới hồ sơ. Thu mua lập, kế toán duyệt cấp một, giám đốc
# duyệt cấp hai. System Manager có hết vì đó là anh Việt.
VAI_LAP = {"Purchase User", "Purchase Manager", "Accounts User", "Accounts Manager", "System Manager"}
VAI_FIN = {"Accounts User", "Accounts Manager", "System Manager"}
VAI_GD = {"Accounts Manager", "System Manager", "Vagabond Giam doc"}

TT_NHAP = "Nhap"
TT_CHO_FIN = "Cho ke toan"
TT_CHO_GD = "Cho giam doc"
TT_DA_DUYET = "Da duyet"
TT_DA_TRA = "Da thanh toan"
TT_TU_CHOI = "Tu choi"
TT_HUY = "Huy"

# Tên hiển thị trên app. Cất trong mã bằng chữ không dấu để tránh lệ thuộc
# bảng mã của cột Select, còn màn hình thì luôn đọc bảng này.
NHAN = {
	TT_NHAP: "Nháp",
	TT_CHO_FIN: "Chờ kế toán duyệt",
	TT_CHO_GD: "Chờ giám đốc duyệt",
	TT_DA_DUYET: "Đã duyệt, chờ chuyển tiền",
	TT_DA_TRA: "Đã thanh toán",
	TT_TU_CHOI: "Từ chối",
	TT_HUY: "Huỷ",
}
THU_TU = [TT_NHAP, TT_CHO_FIN, TT_CHO_GD, TT_DA_DUYET, TT_DA_TRA, TT_TU_CHOI, TT_HUY]

# Ma ho so: APP.26.08.027 - anh Viet chot 13/08/2026, theo dung dang chung tu
# Uyen dang lap bang Excel (APP.26.08.027) va dang phieu thu tu dong da chay
# trong he (APP-26-08-001). So thu tu chay lai tu 001 moi thang.
#
# Ngan hang hay CAT dau cham trong noi dung chuyen khoan, nen khi do SePay
# phai so tren ban DA BO het dau cham va gach: APP2608027. Neu chi tim dung
# chuoi co dau cham thi gap giao dich that cung khong nhan ra.
RE_MA_APP = re.compile(r"APP\.?(\d{2})\.?(\d{2})\.?(\d{3})")
RE_MA_TRAN = re.compile(r"APP(\d{2})(\d{2})(\d{3})")


def _tran(s):
	"""Bo moi ky tu khong phai chu va so, viet hoa - de so ma tren noi dung
	chuyen khoan da bi ngan hang cat bot dau."""
	return re.sub(r"[^A-Z0-9]", "", str(s or "").upper())


def _vai():
	return set(frappe.get_roles())


def _kiem(nhom, viec):
	if not (nhom & _vai()):
		frappe.throw("Tài khoản của bạn không có quyền %s." % viec)


def _sinh_ma(ngay=None):
	"""Mã hồ sơ dạng APP.26.08.027 - năm hai số, tháng hai số, số thứ tự ba số.

	Số thứ tự chạy lại từ 001 mỗi tháng. Đếm theo tiền tố của đúng tháng đó
	chứ không đếm tổng số hồ sơ: xoá một hồ sơ giữa tháng mà đếm tổng thì
	tháng sau sinh trùng mã, mà mã này đi vào nội dung chuyển khoản.
	"""
	d = getdate(ngay or nowdate())
	tien_to = "APP.%02d.%02d." % (d.year % 100, d.month)
	da_co = frappe.get_all(
		"Vagabond Ho So TT",
		filters={"ma": ["like", tien_to + "%"]},
		pluck="ma",
		limit_page_length=0,
	)
	lon_nhat = 0
	for m in da_co:
		duoi = str(m or "").rsplit(".", 1)[-1]
		if duoi.isdigit():
			lon_nhat = max(lon_nhat, int(duoi))
	for i in range(lon_nhat + 1, lon_nhat + 400):
		ma = tien_to + "%03d" % i
		if not frappe.db.exists("Vagabond Ho So TT", ma):
			return ma
	frappe.throw("Không sinh được mã hồ sơ, thử lại giúp em.")


def _tien(v):
	try:
		return "{:,.0f}".format(float(v or 0)).replace(",", ".")
	except Exception:
		return str(v)


def _ngay_vn(s):
	t = str(s or "")
	return "/".join(reversed(t.split("-"))) if t else ""


def _ten_nguoi(email):
	"""Ten that thay vi dia chi thu.

	Anh Viet 13/08/2026 khoanh do man ho so: "hien thi ten dang hoang, chu
	khong phai hien email the nay". Khong tim thay User thi tra lai khuc
	truoc dau @ chu khong tra chuoi rong - mat dau vet con te hon xau.
	"""
	e = (email or "").strip()
	if not e:
		return ""
	ten = frappe.db.get_value("User", e, "full_name")
	if ten and str(ten).strip() and str(ten).strip().lower() != e.lower():
		return str(ten).strip()
	nv = frappe.db.get_value("Employee", {"user_id": e}, "employee_name")
	if nv:
		return str(nv).strip()
	return e.split("@")[0]


def _tk_nhan(ma_ncc):
	"""So tai khoan nhan tien cua mot nha cung cap, doc tu Bank Account.

	Tra ve dict rong neu chua khai - man hinh se bay o trong cho chi Dung
	go tay, khong chan luong.
	"""
	r = frappe.get_all(
		"Bank Account",
		filters={"party_type": "Supplier", "party": ma_ncc},
		fields=["account_name", "bank_account_no", "bank", "iban"],
		order_by="is_default desc, modified desc",
		limit_page_length=1,
	)
	if not r:
		return {}
	o = r[0]
	return {
		"ten_nhan": (o.get("account_name") or "").strip(),
		"stk_nhan": (o.get("bank_account_no") or o.get("iban") or "").strip(),
		"ngan_hang_nhan": (o.get("bank") or "").strip(),
	}


def _bo_dau(s):
	"""Bo dau tieng Viet - ngan hang chi nhan chu khong dau trong noi dung
	chuyen khoan, go co dau vao la ho bien thanh dau hoi."""
	import unicodedata

	t = unicodedata.normalize("NFD", str(s or ""))
	t = "".join(c for c in t if unicodedata.category(c) != "Mn")
	return t.replace("đ", "d").replace("Đ", "D")


# ------------------------------------------------------- chọn hoá đơn để lập


@frappe.whitelist()
def hoa_don_cho_tra(ncc=None, so_ngay=180, chi_qua_han=0):
	"""Hoá đơn mua còn nợ của một nhà cung cấp, để thu mua tick vào hồ sơ.

	Bỏ sẵn những hoá đơn đang nằm trong hồ sơ khác còn hiệu lực - tick vào
	cũng bị chặn lúc lưu, bày ra chỉ tổ mất công.
	"""
	_kiem(VAI_LAP, "xem công nợ phải trả")
	loc = {"docstatus": 1, "outstanding_amount": [">", 0]}
	if ncc:
		loc["supplier"] = ncc
	if cint(so_ngay):
		loc["posting_date"] = [">=", add_days(nowdate(), -int(so_ngay))]
	ds = frappe.get_all(
		"Purchase Invoice",
		filters=loc,
		fields=[
			"name", "supplier", "supplier_name", "posting_date", "due_date",
			"grand_total", "outstanding_amount", "bill_no", "bill_date",
		],
		order_by="due_date asc, posting_date asc",
		limit_page_length=0,
	)
	da_gom = _hd_da_gom()
	hom_nay = getdate(nowdate())
	ra = []
	for r in ds:
		if r.name in da_gom:
			continue
		tre = (hom_nay - getdate(r.due_date)).days if r.due_date else 0
		if cint(chi_qua_han) and tre <= 0:
			continue
		ra.append({
			"hoa_don": r.name,
			"ncc": r.supplier,
			"ten_ncc": r.supplier_name or r.supplier,
			"so_hd_ncc": r.bill_no or "",
			"ngay_hd": str(r.bill_date or r.posting_date or ""),
			"han_tra": str(r.due_date or ""),
			"tre_ngay": tre if tre > 0 else 0,
			"tong_hd": flt(r.grand_total),
			"con_no": flt(r.outstanding_amount),
		})
	return {
		"rows": ra,
		"tong": sum(x["con_no"] for x in ra),
		"qua_han": sum(x["con_no"] for x in ra if x["tre_ngay"] > 0),
		"so_hd": len(ra),
	}


def _hd_da_gom():
	"""Hoá đơn đang nằm trong một hồ sơ còn hiệu lực."""
	rows = frappe.db.sql(
		"""select d.hoa_don from `tabVagabond Ho So TT Dong` d
		inner join `tabVagabond Ho So TT` p on p.name = d.parent
		where p.trang_thai in ('Nhap', 'Cho ke toan', 'Cho giam doc', 'Da duyet')""",
		as_dict=True,
	)
	return set(r["hoa_don"] for r in rows)


@frappe.whitelist()
def ds_ncc_con_no():
	"""Nhà cung cấp nào còn nợ, để app bày chip chọn."""
	_kiem(VAI_LAP, "xem công nợ phải trả")
	ds = frappe.get_all(
		"Purchase Invoice",
		filters={"docstatus": 1, "outstanding_amount": [">", 0]},
		fields=["supplier", "supplier_name", "outstanding_amount", "due_date"],
		limit_page_length=0,
	)
	da_gom = None
	hom_nay = getdate(nowdate())
	gom = {}
	for r in ds:
		o = gom.setdefault(r.supplier, {
			"ncc": r.supplier, "ten": r.supplier_name or r.supplier,
			"so_hd": 0, "tien": 0.0, "qua_han": 0.0,
		})
		o["so_hd"] += 1
		o["tien"] += flt(r.outstanding_amount)
		if r.due_date and getdate(r.due_date) < hom_nay:
			o["qua_han"] += flt(r.outstanding_amount)
	ra = sorted(gom.values(), key=lambda x: (-x["qua_han"], -x["tien"]))
	return {"ncc": ra, "tong": sum(x["tien"] for x in ra)}


# ------------------------------------------------------------------ lập hồ sơ


@frappe.whitelist()
def tao(ncc=None, hoa_don=None, ghi_chu="", gui_luon=0):
	"""Lập một hồ sơ từ danh sách hoá đơn đã tick.

	hoa_don: danh sách mã Purchase Invoice, hoặc danh sách
	{"hoa_don": ..., "so_tien": ...} khi trả một phần.
	"""
	_kiem(VAI_LAP, "lập hồ sơ thanh toán")
	if isinstance(hoa_don, str):
		hoa_don = frappe.parse_json(hoa_don)
	if not hoa_don:
		frappe.throw("Chưa chọn hoá đơn nào.")

	dong = []
	ncc_thay = set()
	for x in hoa_don:
		ma = x if isinstance(x, str) else x.get("hoa_don")
		hd = frappe.db.get_value(
			"Purchase Invoice", ma,
			["name", "supplier", "supplier_name", "posting_date", "bill_date",
			 "bill_no", "due_date", "grand_total", "outstanding_amount", "docstatus"],
			as_dict=True,
		)
		if not hd:
			frappe.throw("Không có hoá đơn mua %s." % ma)
		if hd.docstatus != 1:
			frappe.throw("Hoá đơn %s chưa ghi sổ nên chưa đề nghị trả được." % ma)
		if flt(hd.outstanding_amount) <= 0:
			frappe.throw("Hoá đơn %s đã trả xong rồi." % ma)
		ncc_thay.add(hd.supplier)
		so_tien = flt(x.get("so_tien")) if isinstance(x, dict) and x.get("so_tien") else flt(hd.outstanding_amount)
		dong.append({
			"hoa_don": hd.name,
			"so_hd_ncc": hd.bill_no or "",
			"ngay_hd": hd.bill_date or hd.posting_date,
			"han_tra": hd.due_date,
			"tong_hd": flt(hd.grand_total),
			"con_no": flt(hd.outstanding_amount),
			"so_tien": so_tien,
		})

	# Mot ho so mot nha cung cap: chuyen tien la chuyen cho MOT nguoi, gom
	# hai nha cung cap vao mot ho so thi khong the doi chieu duoc voi ai.
	if len(ncc_thay) > 1:
		frappe.throw(
			"Hồ sơ chỉ gom hoá đơn của MỘT nhà cung cấp. Đang chọn %d nhà: %s."
			% (len(ncc_thay), ", ".join(sorted(ncc_thay)))
		)
	ma_ncc = (ncc or "").strip() or list(ncc_thay)[0]

	doc = frappe.new_doc("Vagabond Ho So TT")
	doc.ma = _sinh_ma()
	doc.loai = "NCC"
	doc.ngay = nowdate()
	doc.nha_cung_cap = ma_ncc
	doc.ten_ncc = frappe.db.get_value("Supplier", ma_ncc, "supplier_name") or ma_ncc
	doc.email_ncc = _email_ncc(ma_ncc)
	doc.trang_thai = TT_CHO_FIN if cint(gui_luon) else TT_NHAP
	doc.nguoi_tao = frappe.session.user
	doc.ghi_chu = (ghi_chu or "").strip()
	for k, v in (_tk_nhan(ma_ncc) or {}).items():
		doc.set(k, v)
	if not doc.ten_nhan:
		doc.ten_nhan = doc.ten_ncc
	for d in dong:
		doc.append("dong", d)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "ma": doc.name, "tong_tien": flt(doc.tong_tien), "trang_thai": doc.trang_thai}


# ------------------------------------------------------------- APP hoàn ứng


# Hai mã món của luồng quỹ tạm ứng OCB, chốt 04/08/2026: hàng test và hàng
# mua lẻ KHÔNG nhập kho, KHÔNG qua đơn mua hàng, lập thẳng hoá đơn mua với
# hai mã này. Không theo dõi tồn, đổ vào tài khoản chi phí 6428.
MON_CO_VAT = "CP-MUANHO-HD"
MON_KHONG_VAT = "CP-MUANHO-KHD"


@frappe.whitelist()
def tao_hoan_ung(nguoi_ung=None, dong=None, ghi_chu="", da_tam_ung=0, gui_luon=0):
	"""Lập hồ sơ hoàn ứng: gõ tay từng khoản đã chi hộ bằng tiền tạm ứng.

	Anh Việt 13/08/2026: "APP này có khả năng đính kèm các hoá đơn từ nhiều
	NCC nhỏ lẻ khác nhau, bao gồm cả hàng test không nhập kho, hàng phát
	sinh, chi phí (bảo trì,...)".

	Khác hẳn hồ sơ NCC ở chỗ: lúc lập CHƯA có hoá đơn mua nào trong hệ. Máy
	chỉ giữ những gì Uyên gõ; đến bước giám đốc duyệt mới sinh hoá đơn mua
	thật, xem _sinh_hoa_don_hoan_ung. Làm vậy để hồ sơ bị từ chối giữa chừng
	không để lại rác trên sổ.

	dong: danh sách {ngay_hd, so_hd_ncc, noi_dung, ben_ban, loai_chi,
	co_vat, so_tien, ghi_chu}.
	"""
	_kiem(VAI_LAP, "lập hồ sơ hoàn ứng")
	if isinstance(dong, str):
		dong = frappe.parse_json(dong)
	if not dong:
		frappe.throw("Chưa nhập khoản chi nào.")
	ma_ncc = (nguoi_ung or "").strip()
	if not ma_ncc:
		frappe.throw("Chưa chọn người được hoàn ứng.")
	if not frappe.db.exists("Supplier", ma_ncc):
		frappe.throw(
			"Không có nhà cung cấp %s. Người được hoàn ứng phải có sẵn hồ sơ "
			"nhà cung cấp để còn theo dõi công nợ." % ma_ncc
		)

	sach = []
	for x in dong:
		if not isinstance(x, dict):
			frappe.throw("Dòng hoàn ứng phải là một khoản chi có nội dung và số tiền.")
		tien = flt(x.get("so_tien"))
		noi_dung = (x.get("noi_dung") or "").strip()
		if tien <= 0:
			frappe.throw("Khoản \"%s\" ghi 0 đồng." % (noi_dung or "chưa đặt tên"))
		if not noi_dung:
			frappe.throw("Có khoản %s đ chưa ghi nội dung chi." % _tien(tien))
		sach.append({
			"ngay_hd": x.get("ngay_hd") or nowdate(),
			"so_hd_ncc": (x.get("so_hd_ncc") or "").strip(),
			"noi_dung": noi_dung,
			"ben_ban": (x.get("ben_ban") or "").strip(),
			"loai_chi": (x.get("loai_chi") or "").strip(),
			"co_vat": 1 if cint(x.get("co_vat")) else 0,
			"so_tien": tien,
			"ghi_chu": (x.get("ghi_chu") or "").strip(),
		})

	doc = frappe.new_doc("Vagabond Ho So TT")
	doc.ma = _sinh_ma()
	doc.loai = "Hoan ung"
	doc.ngay = nowdate()
	doc.nha_cung_cap = ma_ncc
	doc.ten_ncc = frappe.db.get_value("Supplier", ma_ncc, "supplier_name") or ma_ncc
	doc.email_ncc = _email_ncc(ma_ncc)
	doc.da_tam_ung = flt(da_tam_ung)
	doc.trang_thai = TT_CHO_FIN if cint(gui_luon) else TT_NHAP
	doc.nguoi_tao = frappe.session.user
	doc.ghi_chu = (ghi_chu or "").strip()
	for k, v in (_tk_nhan(ma_ncc) or {}).items():
		doc.set(k, v)
	if not doc.ten_nhan:
		doc.ten_nhan = doc.ten_ncc
	for d in sach:
		doc.append("dong", d)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {
		"ok": 1, "ma": doc.name, "tong_tien": flt(doc.tong_tien),
		"con_lai": flt(doc.con_lai), "trang_thai": doc.trang_thai,
	}


@frappe.whitelist()
def ds_nguoi_ung(tu_khoa=""):
	"""Nhà cung cấp để chọn làm người được hoàn ứng.

	Bày sẵn những người đã từng đứng tên hồ sơ hoàn ứng lên đầu - ở tiệm
	chỉ vài người ứng tiền, ngày nào cũng phải cuộn hết danh sách nhà cung
	cấp thì mệt.
	"""
	_kiem(VAI_LAP, "lập hồ sơ hoàn ứng")
	hay = frappe.get_all(
		"Vagabond Ho So TT",
		filters={"loai": "Hoan ung"},
		fields=["nha_cung_cap", "ten_ncc"],
		order_by="creation desc",
		limit_page_length=200,
	)
	quen, thu_tu = {}, []
	for r in hay:
		if r.nha_cung_cap not in quen:
			quen[r.nha_cung_cap] = r.ten_ncc or r.nha_cung_cap
			thu_tu.append(r.nha_cung_cap)

	loc = {"disabled": 0}
	q = (tu_khoa or "").strip()
	if q:
		loc["supplier_name"] = ["like", "%" + q + "%"]
	ds = frappe.get_all(
		"Supplier", filters=loc, fields=["name", "supplier_name"],
		order_by="supplier_name asc", limit_page_length=300,
	)
	ten = {r.name: (r.supplier_name or r.name) for r in ds}
	ra = [{"ncc": m, "ten": quen[m], "hay_dung": 1} for m in thu_tu if not q or q.lower() in (quen[m] or "").lower()]
	da_co = set(thu_tu)
	for r in ds:
		if r.name in da_co:
			continue
		ra.append({"ncc": r.name, "ten": ten[r.name], "hay_dung": 0})
	return {"ncc": ra, "mon": {"co_vat": MON_CO_VAT, "khong_vat": MON_KHONG_VAT}}


def _sinh_hoa_don_hoan_ung(doc):
	"""Dựng hoá đơn mua cho các khoản gõ tay, gắn ngược lại vào dòng hồ sơ.

	Chia làm hai kiểu, có lý do kế toán chứ không phải cho vui:
	  - Khoản CÓ hoá đơn VAT: mỗi số hoá đơn một Hoá đơn mua riêng, vì kê
	    khai thuế đầu vào đi theo từng số hoá đơn.
	  - Khoản KHÔNG có hoá đơn: gom hết vào MỘT hoá đơn mua nhiều dòng, đỡ
	    rác sổ.

	KHÔNG tự tách thuế GTGT: máy không biết thuế suất từng khoản, đoán bừa
	là sai số kê khai. Tổng ghi đúng bằng số tiền Uyên gõ; kế toán mở hoá
	đơn bên Next thêm dòng thuế nếu cần khấu trừ.
	"""
	da_co = [d.hoa_don for d in doc.dong if d.hoa_don]
	if da_co:
		return da_co

	for mon in (MON_CO_VAT, MON_KHONG_VAT):
		if not frappe.db.exists("Item", mon):
			frappe.throw(
				"Chưa có mã món <b>%s</b> trong hệ. Đây là mã dùng cho hàng mua "
				"lẻ không nhập kho; nhờ chị Dung tạo trước rồi duyệt lại giúp em." % mon
			)

	cong_ty = frappe.db.get_single_value("Global Defaults", "default_company")
	if not cong_ty:
		ds_ct = frappe.get_all("Company", pluck="name", limit_page_length=2)
		cong_ty = ds_ct[0] if ds_ct else None
	if not cong_ty:
		frappe.throw("Chưa khai công ty mặc định nên chưa lập được hoá đơn mua.")

	def _mot_hd(cac_dong, so_hd, ngay_hd, mon):
		pi = frappe.new_doc("Purchase Invoice")
		pi.company = cong_ty
		pi.supplier = doc.nha_cung_cap
		pi.set_posting_time = 1
		pi.posting_date = ngay_hd or doc.ngay or nowdate()
		pi.bill_no = so_hd or doc.name
		pi.bill_date = ngay_hd or doc.ngay
		pi.due_date = doc.ngay or nowdate()
		pi.update_stock = 0
		pi.remarks = "Hoàn ứng %s - %s" % (doc.name, doc.ten_ncc or doc.nha_cung_cap)
		for d in cac_dong:
			mo_ta = d.noi_dung or ""
			if d.ben_ban:
				mo_ta += " (mua của %s)" % d.ben_ban
			if d.loai_chi:
				mo_ta += " [%s]" % d.loai_chi
			pi.append("items", {
				"item_code": mon,
				"item_name": (d.noi_dung or mon)[:140],
				"description": mo_ta,
				"qty": 1,
				"rate": flt(d.so_tien),
				"uom": frappe.db.get_value("Item", mon, "stock_uom") or "Nos",
			})
		pi.flags.ignore_permissions = True
		pi.insert(ignore_permissions=True)
		pi.submit()
		return pi.name

	sinh = []
	try:
		co_vat = [d for d in doc.dong if cint(d.co_vat)]
		khong_vat = [d for d in doc.dong if not cint(d.co_vat)]
		for d in co_vat:
			ten_pi = _mot_hd([d], d.so_hd_ncc, d.ngay_hd, MON_CO_VAT)
			d.db_set("hoa_don", ten_pi, update_modified=False)
			sinh.append(ten_pi)
		if khong_vat:
			ngay = min([getdate(d.ngay_hd) for d in khong_vat if d.ngay_hd] or [getdate(doc.ngay or nowdate())])
			ten_pi = _mot_hd(khong_vat, doc.name, ngay, MON_KHONG_VAT)
			for d in khong_vat:
				d.db_set("hoa_don", ten_pi, update_modified=False)
			sinh.append(ten_pi)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ho_so_tt: sinh hoa don hoan ung %s" % doc.name)
		frappe.throw(
			"Không lập được hoá đơn mua cho hồ sơ hoàn ứng %s. Hồ sơ giữ nguyên "
			"ở bước chờ giám đốc, chưa có gì vào sổ. Nhờ chị Dung xem lại mã món "
			"%s / %s và kỳ kế toán rồi duyệt lại." % (doc.name, MON_CO_VAT, MON_KHONG_VAT)
		)
	frappe.db.commit()
	_ghi_vet(doc.name, "Sinh hoá đơn mua cho hoàn ứng: %s" % ", ".join(sinh))
	return sinh


def _email_ncc(ma):
	"""Email nhà cung cấp: ưu tiên liên hệ chính, rồi tới email trên hồ sơ."""
	e = frappe.db.get_value("Supplier", ma, "email_id")
	if e:
		return e
	lh = frappe.db.get_value("Supplier", ma, "supplier_primary_contact")
	if lh:
		e = frappe.db.get_value("Contact", lh, "email_id")
		if e:
			return e
	rows = frappe.db.sql(
		"""select c.email_id from `tabContact` c
		inner join `tabDynamic Link` l on l.parent = c.name
		where l.link_doctype = 'Supplier' and l.link_name = %s
		and ifnull(c.email_id, '') != '' limit 1""",
		ma,
	)
	return rows[0][0] if rows else ""


# ------------------------------------------------------------------ danh sách


@frappe.whitelist()
def danh_sach(trang_thai=None, ncc=None, tu=None, den=None, tu_khoa="", so_ngay=90, loai=None):
	"""Màn Hồ sơ thanh toán: danh sách kèm đếm theo trạng thái cho chip."""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "xem hồ sơ thanh toán")
	if tu and den:
		loc = {"ngay": ["between", [str(tu), str(den)]]}
	else:
		loc = {"ngay": [">=", add_days(nowdate(), -int(so_ngay or 90))]}
	if ncc:
		loc["nha_cung_cap"] = ncc
	if loai:
		loc["loai"] = loai
	ds = frappe.get_all(
		"Vagabond Ho So TT",
		filters=loc,
		fields=[
			"name", "ma", "loai", "ngay", "nha_cung_cap", "ten_ncc", "trang_thai",
			"tong_tien", "da_tra", "da_tam_ung", "con_lai",
			"han_tra_som_nhat", "nguoi_tao",
			"fin_boi", "gd_boi", "ngay_thanh_toan", "ma_giao_dich",
			"email_da_gui", "ly_do_tu_choi", "ghi_chu",
		],
		order_by="ngay desc, creation desc",
		limit_page_length=0,
	)
	so_dong = {}
	if ds:
		# Dem bang get_all chu khong viet SQL "in %s": danh sach mot phan tu
		# thi tuple Python ra ('X',) va cu phap SQL do khong chac chan giua
		# cac ban MariaDB.
		for d in frappe.get_all(
			"Vagabond Ho So TT Dong",
			filters={"parent": ["in", [r.name for r in ds]]},
			fields=["parent"],
			limit_page_length=0,
		):
			so_dong[d.parent] = so_dong.get(d.parent, 0) + 1

	hom_nay = getdate(nowdate())
	q = (tu_khoa or "").strip().lower()
	ra = []
	for r in ds:
		o = dict(r)
		o["so_hd"] = so_dong.get(r.name, 0)
		o["nhan"] = NHAN.get(r.trang_thai, r.trang_thai)
		o["loai"] = r.loai or "NCC"
		o["nguoi_tao_ten"] = _ten_nguoi(r.nguoi_tao)
		o["fin_ten"] = _ten_nguoi(r.fin_boi)
		o["gd_ten"] = _ten_nguoi(r.gd_boi)
		o["tre_ngay"] = (
			(hom_nay - getdate(r.han_tra_som_nhat)).days
			if r.han_tra_som_nhat
			and getdate(r.han_tra_som_nhat) < hom_nay
			and r.trang_thai not in (TT_DA_TRA, TT_TU_CHOI, TT_HUY)
			else 0
		)
		if q and q not in ((r.ma or "") + " " + (r.ten_ncc or "") + " " + (r.ghi_chu or "")).lower():
			continue
		ra.append(o)

	dem, tien = {}, {}
	for o in ra:
		dem[o["trang_thai"]] = dem.get(o["trang_thai"], 0) + 1
		tien[o["trang_thai"]] = tien.get(o["trang_thai"], 0) + flt(o["tong_tien"])
	loc_ra = [o for o in ra if o["trang_thai"] == trang_thai] if trang_thai else ra
	return {
		"rows": loc_ra,
		"tong_dong": len(loc_ra),
		"tong_tien": sum(flt(o["tong_tien"]) for o in loc_ra),
		"tat_ca": len(ra),
		"dem": dem,
		"tien": tien,
		"trang_thai_co": THU_TU,
		"nhan": NHAN,
		"quyen": {
			"lap": 1 if (VAI_LAP & _vai()) else 0,
			"fin": 1 if (VAI_FIN & _vai()) else 0,
			"gd": 1 if (VAI_GD & _vai()) else 0,
		},
	}


def _truong_hddt_pi():
	"""Những cột trên Hoá đơn mua đang giữ thông tin hoá đơn điện tử.

	Dò theo meta chứ không viết cứng tên cột: các trường này do bên m-invoice
	sinh ra, đặt cứng thì hôm nào đội kia đổi tên là màn hình trống trơn mà
	không ai biết vì sao.
	"""
	ra = []
	try:
		meta = frappe.get_meta("Purchase Invoice")
	except Exception:
		return ra
	for f in meta.fields:
		ten = (f.fieldname or "").lower()
		if f.fieldtype in ("Section Break", "Column Break", "Tab Break", "HTML"):
			continue
		if "hddt" in ten or "minvoice" in ten or "m_invoice" in ten or "hoa_don_dien_tu" in ten:
			ra.append((f.fieldname, f.label or f.fieldname))
	return ra


def _ho_so_chung_tu(ten_pi):
	"""Đơn mua hàng, phiếu nhập kho và bản scan gắn với một hoá đơn mua.

	Anh Việt 13/08/2026: "trong APP cũng chưa thấy hiển thị PO và Phiếu Nhập
	kho, bản scan chứng từ nhập kho của bên Kiên đính kèm vào".
	"""
	po, pnk = [], []
	try:
		for r in frappe.get_all(
			"Purchase Invoice Item",
			filters={"parent": ten_pi},
			fields=["purchase_order", "purchase_receipt"],
			limit_page_length=0,
		):
			if r.purchase_order and r.purchase_order not in po:
				po.append(r.purchase_order)
			if r.purchase_receipt and r.purchase_receipt not in pnk:
				pnk.append(r.purchase_receipt)
	except Exception:
		pass
	scan = _dinh_kem([("Purchase Invoice", ten_pi)]
		+ [("Purchase Order", x) for x in po]
		+ [("Purchase Receipt", x) for x in pnk])
	return {"po": po, "pnk": pnk, "scan": scan}


def _dinh_kem(cap):
	"""File đính kèm của một loạt chứng từ, gộp lại thành một danh sách."""
	ra = []
	for dt, dn in cap:
		try:
			for f in frappe.get_all(
				"File",
				filters={"attached_to_doctype": dt, "attached_to_name": dn},
				fields=["name", "file_name", "file_url", "is_private", "file_size"],
				limit_page_length=0,
			):
				ra.append({
					"file": f.name, "ten": f.file_name or f.name,
					"url": f.file_url or "", "rieng": cint(f.is_private),
					"co": cint(f.file_size), "tu": "%s %s" % (dt, dn),
				})
		except Exception:
			continue
	return ra


@frappe.whitelist()
def chi_tiet(name):
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "xem hồ sơ thanh toán")
	doc = frappe.get_doc("Vagabond Ho So TT", name)
	truong_hddt = _truong_hddt_pi()
	dong = []
	for d in doc.dong:
		o = {
			"hoa_don": d.hoa_don or "", "so_hd_ncc": d.so_hd_ncc or "",
			"ngay_hd": str(d.ngay_hd or ""), "han_tra": str(d.han_tra or ""),
			"tong_hd": flt(d.tong_hd), "con_no_luc_lap": flt(d.con_no),
			"con_no_hien_tai": 0.0, "so_tien": flt(d.so_tien),
			"noi_dung": d.noi_dung or "", "ben_ban": d.ben_ban or "",
			"loai_chi": d.loai_chi or "", "co_vat": cint(d.co_vat),
			"ghi_chu": d.ghi_chu or "",
			"po": [], "pnk": [], "scan": [], "hddt": [],
			"ncc_hd": "", "trang_thai_hd": "",
		}
		if d.hoa_don:
			hd = frappe.db.get_value(
				"Purchase Invoice", d.hoa_don,
				["outstanding_amount", "grand_total", "supplier_name", "status", "bill_no", "bill_date"],
				as_dict=True,
			) or {}
			o["con_no_hien_tai"] = flt(hd.get("outstanding_amount"))
			o["ncc_hd"] = hd.get("supplier_name") or ""
			o["trang_thai_hd"] = hd.get("status") or ""
			if hd.get("bill_no") and not o["so_hd_ncc"]:
				o["so_hd_ncc"] = hd.get("bill_no")
			if hd.get("bill_date") and not o["ngay_hd"]:
				o["ngay_hd"] = str(hd.get("bill_date"))
			if truong_hddt:
				gt = frappe.db.get_value(
					"Purchase Invoice", d.hoa_don, [t[0] for t in truong_hddt], as_dict=True
				) or {}
				for ten_truong, nhan_truong in truong_hddt:
					v = gt.get(ten_truong)
					if v not in (None, "", 0):
						o["hddt"].append({"nhan": nhan_truong, "gia_tri": str(v)})
			ct = _ho_so_chung_tu(d.hoa_don)
			o["po"], o["pnk"], o["scan"] = ct["po"], ct["pnk"], ct["scan"]
		dong.append(o)

	return {
		"ho_so": {
			"ma": doc.name, "loai": doc.loai or "NCC", "ngay": str(doc.ngay or ""),
			"ncc": doc.nha_cung_cap, "ten_ncc": doc.ten_ncc,
			"email_ncc": doc.email_ncc or "",
			"trang_thai": doc.trang_thai, "nhan": NHAN.get(doc.trang_thai, doc.trang_thai),
			"tong_tien": flt(doc.tong_tien), "da_tra": flt(doc.da_tra),
			"da_tam_ung": flt(doc.da_tam_ung), "con_lai": flt(doc.con_lai) or flt(doc.tong_tien),
			"han_tra_som_nhat": str(doc.han_tra_som_nhat or ""),
			"nguoi_tao": doc.nguoi_tao, "nguoi_tao_ten": _ten_nguoi(doc.nguoi_tao),
			"fin_boi": doc.fin_boi, "fin_ten": _ten_nguoi(doc.fin_boi),
			"fin_luc": str(doc.fin_luc or ""),
			"gd_boi": doc.gd_boi, "gd_ten": _ten_nguoi(doc.gd_boi),
			"gd_luc": str(doc.gd_luc or ""), "ly_do_tu_choi": doc.ly_do_tu_choi or "",
			"ngay_thanh_toan": str(doc.ngay_thanh_toan or ""),
			"ma_giao_dich": doc.ma_giao_dich or "", "phuong_thuc": doc.phuong_thuc or "",
			"ten_nhan": doc.ten_nhan or "", "stk_nhan": doc.stk_nhan or "",
			"ngan_hang_nhan": doc.ngan_hang_nhan or "",
			"noi_dung_ck": doc.noi_dung_ck or "",
			"email_da_gui": cint(doc.email_da_gui),
			"email_gui_luc": str(doc.email_gui_luc or ""),
			"email_gui_toi": doc.email_gui_toi or "",
			"ghi_chu": doc.ghi_chu or "",
		},
		"dong": dong,
		"ho_so_dinh_kem": _dinh_kem([("Vagabond Ho So TT", doc.name)]),
		"quyen": {
			"lap": 1 if (VAI_LAP & _vai()) else 0,
			"fin": 1 if (VAI_FIN & _vai()) else 0,
			"gd": 1 if (VAI_GD & _vai()) else 0,
		},
		"nhan": NHAN,
	}


# -------------------------------------------------------------------- duyệt


@frappe.whitelist()
def duyet(name, buoc, ly_do=""):
	"""buoc: gui_fin / fin / gd / tu_choi / huy.

	Duyệt phải đúng thứ tự: kế toán trước, giám đốc sau. Người lập không
	tự duyệt hồ sơ của chính mình - đó là cả điểm của việc duyệt hai cấp.
	"""
	doc = frappe.get_doc("Vagabond Ho So TT", name)
	toi = frappe.session.user
	buoc = (buoc or "").strip()

	if buoc == "gui_fin":
		_kiem(VAI_LAP, "gửi hồ sơ đi duyệt")
		if doc.trang_thai not in (TT_NHAP, TT_TU_CHOI):
			frappe.throw("Hồ sơ đang ở trạng thái %s, không gửi lại được." % NHAN.get(doc.trang_thai))
		doc.trang_thai = TT_CHO_FIN
		doc.ly_do_tu_choi = ""

	elif buoc == "fin":
		_kiem(VAI_FIN, "duyệt hồ sơ ở cấp kế toán")
		if doc.trang_thai != TT_CHO_FIN:
			frappe.throw("Hồ sơ đang ở %s, chưa tới lượt kế toán duyệt." % NHAN.get(doc.trang_thai))
		if doc.nguoi_tao == toi and "System Manager" not in _vai():
			frappe.throw("Người lập hồ sơ không tự duyệt được, nhờ người khác duyệt giúp.")
		doc.trang_thai = TT_CHO_GD
		doc.fin_boi = toi
		doc.fin_luc = now_datetime()

	elif buoc == "gd":
		_kiem(VAI_GD, "duyệt hồ sơ ở cấp giám đốc")
		if doc.trang_thai != TT_CHO_GD:
			frappe.throw("Hồ sơ đang ở %s, chưa tới lượt giám đốc duyệt." % NHAN.get(doc.trang_thai))
		# Ho so hoan ung: den day moi sinh hoa don mua that. Dat TRUOC khi
		# doi trang thai - ham nem loi thi ho so con nguyen o buoc cho giam
		# doc, khong co gi nua voi nua chin.
		if (doc.loai or "NCC") == "Hoan ung":
			_sinh_hoa_don_hoan_ung(doc)
			doc.reload()
		doc.trang_thai = TT_DA_DUYET
		doc.gd_boi = toi
		doc.gd_luc = now_datetime()

	elif buoc == "tu_choi":
		_kiem(VAI_FIN | VAI_GD, "từ chối hồ sơ")
		if not (ly_do or "").strip():
			frappe.throw("Từ chối thì phải ghi lý do, để người lập còn biết sửa gì.")
		if doc.trang_thai in (TT_DA_TRA, TT_HUY):
			frappe.throw("Hồ sơ đã %s, không từ chối được nữa." % NHAN.get(doc.trang_thai))
		doc.trang_thai = TT_TU_CHOI
		doc.ly_do_tu_choi = ly_do.strip()

	elif buoc == "huy":
		_kiem(VAI_LAP, "huỷ hồ sơ")
		if doc.trang_thai == TT_DA_TRA:
			frappe.throw("Hồ sơ đã thanh toán rồi, không huỷ được.")
		doc.trang_thai = TT_HUY
		doc.ly_do_tu_choi = (ly_do or "").strip()

	else:
		frappe.throw("Bước duyệt không hợp lệ: %s." % buoc)

	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	_ghi_vet(doc.name, "%s bởi %s%s" % (buoc, toi, (" - " + ly_do) if ly_do else ""))
	return {"ok": 1, "trang_thai": doc.trang_thai, "nhan": NHAN.get(doc.trang_thai)}


def _ghi_vet(name, viec):
	try:
		frappe.get_doc({
			"doctype": "Comment", "comment_type": "Info",
			"reference_doctype": "Vagabond Ho So TT", "reference_name": name,
			"content": viec,
		}).insert(ignore_permissions=True)
	except Exception:
		pass


# ------------------------------------------------------- SePay và clear công nợ


def _sepay_theo_ma_app(ds_ma):
	"""Giao dịch NGÂN HÀNG CHI RA có mã hồ sơ trong nội dung.

	Khác chiều với công nợ phải thu: ở đây tiền ĐI RA, nên lấy withdrawal
	trừ deposit. Kế toán chuyển khoản với nội dung chứa mã APPxxxxxx thì
	SePay đẩy về Bank Transaction, máy tự khớp.
	"""
	# So tren ban DA BO dau cham: ngan hang hay cat bot dau khi day noi dung
	# di, "APP.26.08.027" ve toi SePay co the thanh "APP2608027" hay
	# "APP 26 08 027". Truy van SQL vi vay chi loc tho theo "APP" roi doi
	# chieu chinh xac bang Python.
	tran = {}
	for m in ds_ma or []:
		g = RE_MA_APP.fullmatch(str(m or "").strip().upper()) or RE_MA_TRAN.fullmatch(_tran(m))
		if g:
			tran["APP" + "".join(g.groups())] = str(m).strip()
	if not tran:
		return {}
	try:
		gds = frappe.db.sql(
			"""select description, deposit, withdrawal, reference_number, date
			from `tabBank Transaction`
			where docstatus < 2 and description like %s""",
			("%APP%",), as_dict=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ho_so_tt: doc SePay theo ma ho so")
		return {}
	ra = {}
	for g in gds:
		for k in RE_MA_TRAN.findall(_tran(g.get("description"))):
			khoa = "APP" + "".join(k)
			ten = tran.get(khoa)
			if not ten:
				continue
			o = ra.setdefault(ten, {"chi": 0.0, "so_gd": 0, "ma_gd": "", "ngay": None})
			o["chi"] += flt(g.get("withdrawal")) - flt(g.get("deposit"))
			o["so_gd"] += 1
			if not o["ma_gd"]:
				o["ma_gd"] = (g.get("reference_number") or "").strip()
			if not o["ngay"]:
				o["ngay"] = str(g.get("date") or "")
	return ra


@frappe.whitelist()
def kiem_sepay(name=None):
	"""Dò SePay xem hồ sơ đã chuyển tiền chưa. Không ghi gì, chỉ xem."""
	_kiem(VAI_FIN, "đối chiếu SePay")
	if name:
		ds = [frappe.db.get_value("Vagabond Ho So TT", name, ["name", "tong_tien", "trang_thai"], as_dict=True)]
	else:
		ds = frappe.get_all(
			"Vagabond Ho So TT",
			filters={"trang_thai": TT_DA_DUYET},
			fields=["name", "tong_tien", "trang_thai"],
			limit_page_length=0,
		)
	ds = [d for d in ds if d]
	g = _sepay_theo_ma_app([d["name"] for d in ds])
	ra = []
	for d in ds:
		o = g.get(d["name"]) or {}
		ra.append({
			"ma": d["name"], "tong_tien": flt(d["tong_tien"]),
			"da_chi": flt(o.get("chi")), "so_gd": o.get("so_gd") or 0,
			"ma_gd": o.get("ma_gd") or "", "ngay": o.get("ngay") or "",
			"du": 1 if flt(o.get("chi")) >= flt(d["tong_tien"]) - 1 else 0,
		})
	return {"rows": ra, "so_du": len([x for x in ra if x["du"]])}


@frappe.whitelist()
def danh_dau_da_tra(name, ngay=None, ma_giao_dich=None, phuong_thuc="Chuyển khoản", tao_but_toan=1):
	"""Ghi nhận đã chuyển tiền, và sinh Payment Entry để clear công nợ.

	Bút toán mới là thứ thật sự xoá nợ trên sổ; hồ sơ chỉ là chứng từ đề
	nghị. Nếu ERPNext từ chối bút toán thì hồ sơ vẫn ở Đã duyệt để kế toán
	xử tay, KHÔNG đánh dấu đã trả - đánh dấu mà nợ vẫn treo là tệ hơn.
	"""
	_kiem(VAI_FIN, "ghi nhận thanh toán")
	doc = frappe.get_doc("Vagabond Ho So TT", name)
	if doc.trang_thai == TT_DA_TRA:
		return {"ok": 1, "da_lam_roi": 1, "trang_thai": doc.trang_thai}
	if doc.trang_thai != TT_DA_DUYET:
		frappe.throw(
			"Hồ sơ đang ở %s. Phải duyệt xong hai cấp mới chuyển tiền được."
			% NHAN.get(doc.trang_thai, doc.trang_thai)
		)

	pe = None
	if cint(tao_but_toan):
		pe = _tao_but_toan(doc, ngay or nowdate(), phuong_thuc)

	doc.trang_thai = TT_DA_TRA
	doc.ngay_thanh_toan = ngay or nowdate()
	doc.ma_giao_dich = (ma_giao_dich or "").strip()
	doc.phuong_thuc = (phuong_thuc or "").strip()
	doc.da_tra = flt(doc.tong_tien)
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	_ghi_vet(doc.name, "Đã thanh toán %s đ%s" % (_tien(doc.tong_tien), (" - bút toán " + pe) if pe else ""))
	return {"ok": 1, "trang_thai": doc.trang_thai, "but_toan": pe or ""}


def _tao_but_toan(doc, ngay, phuong_thuc):
	"""Sinh Payment Entry trả nhà cung cấp, phân bổ vào đúng từng hoá đơn.

	GOP THEO HOA DON truoc khi phan bo. Ho so hoan ung gom nhieu khoan khong
	hoa don vao MOT hoa don mua, moi khoan mot dong; de nguyen ma duyet tung
	dong thi Payment Entry co hai ba dong tro cung mot Purchase Invoice, va
	ERPNext se phan bo chong len nhau - tra 3 trieu ma so sach ghi tra 9.
	"""
	con = [d for d in doc.dong if d.hoa_don]
	if not con:
		frappe.throw(
			"Hồ sơ %s chưa có hoá đơn mua nào để xoá công nợ. Với hồ sơ hoàn ứng, "
			"hoá đơn được lập ở bước giám đốc duyệt." % doc.name
		)

	gom = {}
	for d in con:
		gom[d.hoa_don] = gom.get(d.hoa_don, 0.0) + flt(d.so_tien)

	cong_ty = frappe.db.get_value("Purchase Invoice", con[0].hoa_don, "company")
	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = "Pay"
	pe.company = cong_ty
	pe.posting_date = ngay
	pe.party_type = "Supplier"
	pe.party = doc.nha_cung_cap
	pe.paid_amount = flt(doc.tong_tien)
	pe.received_amount = flt(doc.tong_tien)
	pe.reference_no = doc.ma_giao_dich or doc.name
	pe.reference_date = ngay
	pe.remarks = "Hồ sơ thanh toán %s - %s" % (doc.name, doc.ten_ncc or doc.nha_cung_cap)
	if phuong_thuc and frappe.db.exists("Mode of Payment", phuong_thuc):
		pe.mode_of_payment = phuong_thuc
	for ten_hd, tien in gom.items():
		hd = frappe.db.get_value(
			"Purchase Invoice", ten_hd, ["grand_total", "outstanding_amount", "posting_date", "due_date"],
			as_dict=True,
		) or {}
		pe.append("references", {
			"reference_doctype": "Purchase Invoice",
			"reference_name": ten_hd,
			"total_amount": flt(hd.get("grand_total")),
			"outstanding_amount": flt(hd.get("outstanding_amount")),
			"allocated_amount": min(flt(tien), flt(hd.get("outstanding_amount"))),
			"due_date": hd.get("due_date"),
		})
	pe.setup_party_account_field()
	pe.set_missing_values()
	pe.flags.ignore_permissions = True
	pe.insert(ignore_permissions=True)
	pe.submit()
	frappe.db.commit()
	return pe.name


# --------------------------------------------------------- thư báo nhà cung cấp


@frappe.whitelist()
def gui_email_ncc(name, email=None, gui_that=1):
	"""Thư báo đã thanh toán, gửi nhà cung cấp.

	Anh Việt 13/08/2026: "Purchasing hoặc Kế toán nhắn một cái là có thể
	gửi email thông báo được luôn". Dùng chung khung thư thương hiệu với
	thư PO và thư mời nhân sự.

	gui_that=0 chỉ dựng HTML để xem trước, không gửi cho ai.
	"""
	_kiem(VAI_LAP | VAI_FIN, "gửi thư báo nhà cung cấp")
	doc = frappe.get_doc("Vagabond Ho So TT", name)
	if doc.trang_thai != TT_DA_TRA and cint(gui_that):
		frappe.throw(
			"Hồ sơ chưa ở trạng thái Đã thanh toán, gửi thư báo lúc này là "
			"báo nhầm cho nhà cung cấp."
		)
	noi_dung = _thu_html(doc)
	if not cint(gui_that):
		return {"xem_truoc": 1, "html": noi_dung, "toi": email or doc.email_ncc or ""}

	toi = (email or doc.email_ncc or "").strip()
	if not toi or "@" not in toi:
		frappe.throw(
			"Chưa có email của nhà cung cấp %s. Anh chị điền email vào hồ sơ "
			"nhà cung cấp bên Next, hoặc gõ tay vào ô gửi tới." % (doc.ten_ncc or doc.nha_cung_cap)
		)
	frappe.sendmail(
		recipients=[toi],
		sender="erp@thevagabondpatisserie.com",
		subject="The Vagabond Pâtisserie - Thông báo đã thanh toán công nợ (%s)" % doc.name,
		message=noi_dung,
		delayed=False,
		retry=2,
	)
	doc.db_set("email_da_gui", 1, update_modified=False)
	doc.db_set("email_gui_luc", now_datetime(), update_modified=False)
	doc.db_set("email_gui_toi", toi, update_modified=False)
	frappe.db.commit()
	_ghi_vet(doc.name, "Gửi thư báo thanh toán tới %s" % toi)
	return {"ok": 1, "toi": toi}


def _thu_html(doc):
	"""Nội dung thư báo thanh toán. Tách riêng để xem trước được mà không gửi."""
	from vagabond.nhan_su import _khung_thu, _o_nhat

	h = frappe.utils.escape_html
	hang = []
	for d in doc.dong:
		hang.append(
			"<tr>"
			'<td style="padding:7px 10px;border-bottom:1px solid #E6EEF1;font-size:13px">%s</td>'
			'<td style="padding:7px 10px;border-bottom:1px solid #E6EEF1;font-size:13px">%s</td>'
			'<td style="padding:7px 10px;border-bottom:1px solid #E6EEF1;font-size:13px;text-align:right;white-space:nowrap">%s đ</td>'
			"</tr>"
			% (h(d.so_hd_ncc or d.noi_dung or d.hoa_don), _ngay_vn(d.ngay_hd), _tien(d.so_tien))
		)
	# KHONG dat phep % len ca chuoi HTML nay: trong do co width="100%" va
	# noi dung tung dong da ghep san. Python doc "%" do la ma dinh dang roi
	# nem ValueError. Ghep bang cong chuoi, chi dinh dang dung o cho nao that
	# su can. Loi nay tung lam vo nut Xuat bo ho so ngay 13/08/2026.
	bang = (
		'<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" '
		'style="border-collapse:collapse;margin:6px 0 4px">'
		'<tr><td style="padding:7px 10px;background:#E4F9FD;font-size:12px;font-weight:bold;color:#05323C">Số hoá đơn</td>'
		'<td style="padding:7px 10px;background:#E4F9FD;font-size:12px;font-weight:bold;color:#05323C">Ngày</td>'
		'<td style="padding:7px 10px;background:#E4F9FD;font-size:12px;font-weight:bold;color:#05323C;text-align:right">Số tiền</td></tr>'
		+ "".join(hang)
		+ '<tr><td colspan="2" style="padding:9px 10px;font-size:13.5px;font-weight:bold;color:#05323C">TỔNG THANH TOÁN</td>'
		+ '<td style="padding:9px 10px;font-size:15px;font-weight:bold;color:#0B7C93;text-align:right;white-space:nowrap">'
		+ _tien(doc.tong_tien) + " đ</td></tr></table>"
	)

	chi_tiet_tra = [
		"Ngày thanh toán: <b>%s</b>" % _ngay_vn(doc.ngay_thanh_toan),
		"Hình thức: <b>%s</b>" % h(doc.phuong_thuc or "Chuyển khoản"),
	]
	if doc.ma_giao_dich:
		chi_tiet_tra.append("Mã giao dịch: <b>%s</b>" % h(doc.ma_giao_dich))
	chi_tiet_tra.append("Mã hồ sơ bên chúng tôi: <b>%s</b>" % h(doc.name))

	than = (
		"<p style='margin:0 0 14px'>Kính gửi <b>%s</b>,</p>"
		"<p style='margin:0 0 12px'>The Vagabond Pâtisserie xin thông báo đã <b>thanh toán</b> "
		"cho quý công ty số tiền <b>%s đ</b> cho %d hoá đơn dưới đây.</p>"
		"%s"
		"<p style='margin:14px 0 8px'>Thông tin thanh toán:</p>%s"
		"<p style='margin:14px 0 0'>Quý công ty vui lòng đối chiếu và xác nhận giúp. "
		"Có sai lệch xin phản hồi lại thư này để hai bên soát lại sổ.</p>"
		"<p style='margin:12px 0 0'>Trân trọng cảm ơn quý công ty đã đồng hành cùng chúng tôi.</p>"
	) % (
		h(doc.ten_ncc or doc.nha_cung_cap),
		_tien(doc.tong_tien),
		len(doc.dong),
		bang,
		_o_nhat("<br>".join(chi_tiet_tra)),
	)
	return _khung_thu("Thông báo đã thanh toán công nợ", than)


# ------------------------------------------------- nội dung chuyển khoản (MB)


# Nguoi ta gioi han noi dung chuyen khoan quanh 90-100 ky tu tuy ngan hang.
# Cat o 90 cho chac, va cat o cho nao khong lam mat ma APP - ma nam ngay dau
# chuoi chinh la vi vay.
DAI_ND_CK = 90


def _noi_dung_ck(doc):
	"""Nội dung chuyển khoản: mã hồ sơ đứng trước, không dấu, viết hoa.

	Mã đứng ĐẦU chuỗi vì hai lẽ: ngân hàng cắt bớt thì cắt ở đuôi, và
	_sepay_theo_ma_app dò được ngay. Bỏ dấu vì ngân hàng đẩy nội dung có dấu
	về SePay là thành dấu hỏi.
	"""
	ten = _bo_dau(doc.ten_nhan or doc.ten_ncc or doc.nha_cung_cap or "").upper()
	viec = "HOAN UNG" if (doc.loai or "NCC") == "Hoan ung" else "TT CONG NO"
	nd = "VAGABOND %s %s %s" % (doc.name, viec, ten)
	nd = re.sub(r"[^A-Za-z0-9 .]", " ", nd)
	nd = re.sub(r"\s+", " ", nd).strip()
	return nd[:DAI_ND_CK].strip()


@frappe.whitelist()
def noi_dung_chuyen_khoan(name, luu=1):
	"""Sinh sẵn số tài khoản, tên thụ hưởng và nội dung để chị Dung copy.

	Anh Việt 13/08/2026: "generate ra stk, tên người thụ hưởng, nội dung
	chuyển khoản (kèm mã) để chị Dung chỉ việc copy paste vào file chuyển
	khoản theo lô của MB".

	Trả thêm dòng dán thẳng vào file lô: các cột phân cách bằng Tab, dán vào
	Excel là mỗi cột một ô, khỏi phải tách tay.
	"""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "xem hồ sơ thanh toán")
	doc = frappe.get_doc("Vagabond Ho So TT", name)

	# Chua khai tai khoan tren ho so thi thu doc lai tu Bank Account - co the
	# ke toan vua khai xong sau khi ho so da lap.
	if not (doc.stk_nhan or "").strip():
		for k, v in (_tk_nhan(doc.nha_cung_cap) or {}).items():
			if v and not doc.get(k):
				doc.set(k, v)
	if not (doc.ten_nhan or "").strip():
		doc.ten_nhan = doc.ten_ncc or doc.nha_cung_cap

	nd = _noi_dung_ck(doc)
	so_tien = flt(doc.con_lai) or flt(doc.tong_tien)
	if cint(luu):
		doc.db_set("noi_dung_ck", nd, update_modified=False)
		for k in ("ten_nhan", "stk_nhan", "ngan_hang_nhan"):
			if doc.get(k):
				doc.db_set(k, doc.get(k), update_modified=False)
		frappe.db.commit()

	thieu = []
	if not (doc.stk_nhan or "").strip():
		thieu.append("số tài khoản")
	if not (doc.ngan_hang_nhan or "").strip():
		thieu.append("tên ngân hàng")

	cot = ["Số tài khoản", "Tên người thụ hưởng", "Ngân hàng", "Số tiền", "Nội dung"]
	gia_tri = [
		(doc.stk_nhan or "").strip(),
		_bo_dau(doc.ten_nhan or "").upper(),
		(doc.ngan_hang_nhan or "").strip(),
		"%d" % int(round(so_tien)),
		nd,
	]
	return {
		"ma": doc.name,
		"ten_nhan": (doc.ten_nhan or "").strip(),
		"ten_nhan_ck": _bo_dau(doc.ten_nhan or "").upper(),
		"stk": (doc.stk_nhan or "").strip(),
		"ngan_hang": (doc.ngan_hang_nhan or "").strip(),
		"so_tien": so_tien,
		"tong_tien": flt(doc.tong_tien),
		"da_tam_ung": flt(doc.da_tam_ung),
		"noi_dung": nd,
		"cot": cot,
		"dong_mb": "\t".join(gia_tri),
		"thieu": thieu,
	}


@frappe.whitelist()
def sua_tk_nhan(name, ten_nhan=None, stk_nhan=None, ngan_hang_nhan=None):
	"""Sửa tay tài khoản nhận tiền trên hồ sơ (khi Bank Account chưa khai)."""
	_kiem(VAI_LAP | VAI_FIN, "sửa tài khoản nhận tiền")
	doc = frappe.get_doc("Vagabond Ho So TT", name)
	if doc.trang_thai == TT_DA_TRA:
		frappe.throw("Hồ sơ đã thanh toán rồi, không sửa tài khoản nhận nữa.")
	if ten_nhan is not None:
		doc.db_set("ten_nhan", (ten_nhan or "").strip(), update_modified=False)
	if stk_nhan is not None:
		doc.db_set("stk_nhan", re.sub(r"\s+", "", str(stk_nhan or "")), update_modified=False)
	if ngan_hang_nhan is not None:
		doc.db_set("ngan_hang_nhan", (ngan_hang_nhan or "").strip(), update_modified=False)
	frappe.db.commit()
	_ghi_vet(doc.name, "Sửa tài khoản nhận tiền bởi %s" % frappe.session.user)
	return noi_dung_chuyen_khoan(name, luu=1)


# --------------------------------------------------------- xuất bộ hồ sơ (ZIP)


@frappe.whitelist()
def xuat_ho_so(name):
	"""Gói cả bộ chứng từ của một hồ sơ thành một tệp nén.

	Anh Việt 13/08/2026: "xuất ra toàn bộ hồ sơ thanh toán sau khi quá trình
	thanh toán đã hoàn tất gồm phiếu APP, phiếu PO, phiếu nhập kho, phiếu
	nghiệm thu (scan,... tuỳ loại giao dịch mà có phiếu nào)".

	Chứng từ nào dựng không được thì ghi vào MUC-LUC.txt chứ không bỏ im -
	một bộ hồ sơ thiếu tờ mà không ai biết là thiếu thì tệ hơn báo lỗi.
	"""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "xuất bộ hồ sơ thanh toán")
	import zipfile

	d = chi_tiet(name)
	hs = d["ho_so"]
	buf = io.BytesIO()
	muc_luc, hong = [], []

	def _pdf(dt, dn, ten_tep):
		try:
			noi = frappe.get_print(dt, dn, as_pdf=True)
			z.writestr(ten_tep, noi)
			muc_luc.append(ten_tep + "  <- %s %s" % (dt, dn))
			return True
		except Exception:
			hong.append("%s %s" % (dt, dn))
			frappe.log_error(frappe.get_traceback(), "ho_so_tt: in %s %s" % (dt, dn))
			return False

	with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
		# 1. To de nghi thanh toan, dung tu HTML cua chinh he - khong phu
		#    thuoc Print Format nao ca.
		try:
			from frappe.utils.pdf import get_pdf

			z.writestr("01-DE-NGHI-THANH-TOAN-%s.pdf" % hs["ma"], get_pdf(_to_app_html(name)))
			muc_luc.append("01-DE-NGHI-THANH-TOAN-%s.pdf  <- to APP" % hs["ma"])
		except Exception:
			z.writestr("01-DE-NGHI-THANH-TOAN-%s.html" % hs["ma"], _to_app_html(name).encode("utf-8"))
			muc_luc.append("01-DE-NGHI-THANH-TOAN-%s.html  <- to APP (khong dung duoc PDF)" % hs["ma"])

		da_in_po, da_in_pnk = set(), set()
		for i, x in enumerate(d["dong"], 1):
			if x["hoa_don"]:
				_pdf("Purchase Invoice", x["hoa_don"], "02-HOA-DON-MUA/%02d-%s.pdf" % (i, x["hoa_don"]))
			for po in x["po"]:
				if po in da_in_po:
					continue
				da_in_po.add(po)
				_pdf("Purchase Order", po, "03-DON-MUA-HANG/%s.pdf" % po)
			for pnk in x["pnk"]:
				if pnk in da_in_pnk:
					continue
				da_in_pnk.add(pnk)
				_pdf("Purchase Receipt", pnk, "04-PHIEU-NHAP-KHO/%s.pdf" % pnk)

		# 2. Ban scan: chung tu giay ben Kien dinh kem vao PO / PNK / hoa don,
		#    cong voi file dinh kem thang vao ho so.
		da_lay = set()
		for nhom in [x["scan"] for x in d["dong"]] + [d.get("ho_so_dinh_kem") or []]:
			for f in nhom:
				if f["file"] in da_lay:
					continue
				da_lay.add(f["file"])
				try:
					noi = frappe.get_doc("File", f["file"]).get_content()
					if isinstance(noi, str):
						noi = noi.encode("utf-8")
					z.writestr("05-BAN-SCAN/%s" % (f["ten"] or f["file"]), noi)
					muc_luc.append("05-BAN-SCAN/%s  <- %s" % (f["ten"] or f["file"], f["tu"]))
				except Exception:
					hong.append("scan %s" % (f["ten"] or f["file"]))

		mo_ta = [
			"BO HO SO THANH TOAN %s" % hs["ma"],
			"Loai: %s" % ("Hoan ung" if hs["loai"] == "Hoan ung" else "Cong no nha cung cap"),
			"Ben nhan: %s (%s)" % (hs["ten_ncc"] or hs["ncc"], hs["ncc"]),
			"Trang thai: %s" % hs["nhan"],
			"Tong de nghi tra: %s d" % _tien(hs["tong_tien"]),
		]
		if flt(hs.get("da_tam_ung")):
			mo_ta.append("Tru tam ung: %s d" % _tien(hs["da_tam_ung"]))
			mo_ta.append("Con lai chuyen: %s d" % _tien(hs["con_lai"]))
		mo_ta += [
			"Nguoi lap: %s" % (hs["nguoi_tao_ten"] or "-"),
			"Ke toan duyet: %s" % (hs["fin_ten"] or "-"),
			"Giam doc duyet: %s" % (hs["gd_ten"] or "-"),
			"Ngay thanh toan: %s" % (_ngay_vn(hs["ngay_thanh_toan"]) or "-"),
			"Ma giao dich: %s" % (hs["ma_giao_dich"] or "-"),
			"",
			"CAC TEP TRONG BO HO SO:",
		] + ["  " + x for x in muc_luc]
		if hong:
			mo_ta += ["", "KHONG LAY DUOC (can lay tay tren Next):"] + ["  " + x for x in hong]
		z.writestr("MUC-LUC.txt", _bo_dau("\n".join(mo_ta)).encode("utf-8"))

	return {
		"ten_file": "ho-so-%s.zip" % hs["ma"].replace(".", "-"),
		"b64": base64.b64encode(buf.getvalue()).decode(),
		"so_tep": len(muc_luc),
		"hong": hong,
	}


@frappe.whitelist()
def xem_to_app(name):
	"""Tờ đề nghị thanh toán để xem trên màn hình, không cần tải cả bộ."""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "xem hồ sơ thanh toán")
	return {"html": _to_app_html(name)}


def _to_app_html(name):
	"""Tờ đề nghị thanh toán, dựng đúng theo mẫu Excel Uyên đang lập tay."""
	d = chi_tiet(name)
	hs, dong = d["ho_so"], d["dong"]
	h = frappe.utils.escape_html
	la_hu = hs["loai"] == "Hoan ung"

	hang = []
	for i, x in enumerate(dong, 1):
		hang.append(
			"<tr>"
			'<td style="border:1px solid #999;padding:5px;text-align:center">%d</td>'
			'<td style="border:1px solid #999;padding:5px;text-align:center">%s</td>'
			'<td style="border:1px solid #999;padding:5px">%s</td>'
			'<td style="border:1px solid #999;padding:5px">%s</td>'
			'<td style="border:1px solid #999;padding:5px;text-align:right">%s</td>'
			'<td style="border:1px solid #999;padding:5px">%s</td>'
			"</tr>"
			% (
				i, _ngay_vn(x["ngay_hd"]), h(x["so_hd_ncc"] or x["hoa_don"] or ""),
				h(x["noi_dung"] or x["ncc_hd"] or x["hoa_don"] or ""),
				_tien(x["so_tien"]),
				h(x["ghi_chu"] or x["ben_ban"] or ""),
			)
		)

	cuoi = (
		'<tr><td colspan="4" style="border:1px solid #999;padding:6px;font-weight:bold">TỔNG CỘNG</td>'
		'<td style="border:1px solid #999;padding:6px;text-align:right;font-weight:bold">%s</td>'
		'<td style="border:1px solid #999;padding:6px"></td></tr>' % _tien(hs["tong_tien"])
	)
	if flt(hs.get("da_tam_ung")):
		cuoi += (
			'<tr><td colspan="4" style="border:1px solid #999;padding:6px">Trừ số tiền đã tạm ứng</td>'
			'<td style="border:1px solid #999;padding:6px;text-align:right">%s</td>'
			'<td style="border:1px solid #999;padding:6px"></td></tr>'
			'<tr><td colspan="4" style="border:1px solid #999;padding:6px;font-weight:bold">CÒN LẠI</td>'
			'<td style="border:1px solid #999;padding:6px;text-align:right;font-weight:bold">%s</td>'
			'<td style="border:1px solid #999;padding:6px"></td></tr>'
			% (_tien(hs["da_tam_ung"]), _tien(hs["con_lai"]))
		)

	# Ghep bang cong chuoi chu khong dat phep % len ca khoi: trong chuoi co
	# width="100%" va Python doc dau % do la ma dinh dang roi nem ValueError.
	ky = (
		'<table width="100%" style="margin-top:26px;text-align:center;font-size:12px">'
		"<tr><td><b>NGƯỜI ĐỀ NGHỊ</b></td><td><b>KẾ TOÁN (FIN)</b></td><td><b>GIÁM ĐỐC</b></td></tr>"
		'<tr><td style="height:58px"></td><td></td><td></td></tr>'
		+ "<tr><td>" + h(hs["nguoi_tao_ten"] or "")
		+ "</td><td>" + h(hs["fin_ten"] or "")
		+ "</td><td>" + h(hs["gd_ten"] or "")
		+ "</td></tr></table>"
	)

	return (
		'<div style="font-family:Arial,sans-serif;font-size:12.5px;color:#111">'
		'<div style="text-align:center"><div style="font-weight:bold;font-size:14px">'
		"CÔNG TY TNHH PATISSERIE VAGABOND</div>"
		'<div style="font-size:18px;font-weight:bold;margin:12px 0 2px">%s</div>'
		'<div>Số: <b>%s</b> · Ngày %s</div></div>'
		'<div style="margin:14px 0 6px">Kính gửi: <b>Ban Giám đốc</b></div>'
		'<div style="margin:0 0 4px">Đề nghị thanh toán cho: <b>%s</b> (%s)</div>'
		'<div style="margin:0 0 4px">Số tài khoản: <b>%s</b> · Ngân hàng: <b>%s</b></div>'
		'<div style="margin:0 0 10px">Nội dung chuyển khoản: <b>%s</b></div>'
		'<table width="100%%" style="border-collapse:collapse;font-size:12px">'
		'<tr style="background:#eef4f6">'
		'<th style="border:1px solid #999;padding:5px">STT</th>'
		'<th style="border:1px solid #999;padding:5px">Ngày hoá đơn</th>'
		'<th style="border:1px solid #999;padding:5px">Số hoá đơn</th>'
		'<th style="border:1px solid #999;padding:5px">Nội dung</th>'
		'<th style="border:1px solid #999;padding:5px">Số tiền</th>'
		'<th style="border:1px solid #999;padding:5px">Ghi chú</th></tr>'
		"%s%s</table>%s</div>"
	) % (
		"GIẤY ĐỀ NGHỊ HOÀN ỨNG" if la_hu else "GIẤY ĐỀ NGHỊ THANH TOÁN",
		h(hs["ma"]), _ngay_vn(hs["ngay"]),
		h(hs["ten_nhan"] or hs["ten_ncc"] or hs["ncc"]), h(hs["ncc"]),
		h(hs["stk_nhan"] or "..........."), h(hs["ngan_hang_nhan"] or "..........."),
		h(hs["noi_dung_ck"] or ""),
		"".join(hang), cuoi, ky,
	)


# -------------------------------------------------------------------- Excel


@frappe.whitelist()
def xuat_excel(trang_thai=None, ncc=None, tu=None, den=None, tu_khoa="", so_ngay=90, loai=None):
	"""Bộ hồ sơ ra Excel cho kế toán theo dõi: một dòng một hoá đơn."""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "xuất hồ sơ thanh toán")
	kq = danh_sach(
		trang_thai=trang_thai, ncc=ncc, tu=tu, den=den,
		tu_khoa=tu_khoa, so_ngay=so_ngay, loai=loai,
	)
	rows = kq["rows"]
	chi_tiet_dong = {}
	if rows:
		for d in frappe.get_all(
			"Vagabond Ho So TT Dong",
			filters={"parent": ["in", [r["name"] for r in rows]]},
			fields=["parent", "hoa_don", "so_hd_ncc", "ngay_hd", "han_tra",
				"con_no", "so_tien", "noi_dung", "ben_ban", "loai_chi", "co_vat"],
			order_by="parent asc, idx asc",
			limit_page_length=0,
		):
			chi_tiet_dong.setdefault(d.parent, []).append(d)

	bang = [
		["HỒ SƠ THANH TOÁN NHÀ CUNG CẤP"],
		["Từ %s đến %s%s" % (
			tu or ("%d ngày gần đây" % int(so_ngay or 90)), den or nowdate(),
			(" · %s" % NHAN.get(trang_thai, trang_thai)) if trang_thai else "",
		)],
		["Số hồ sơ", len(rows), "Tổng đề nghị trả", kq["tong_tien"]],
		[],
		["Mã hồ sơ", "Loại", "Ngày lập", "Nhà cung cấp", "Trạng thái", "Tổng hồ sơ",
		 "Trừ tạm ứng", "Còn lại chuyển",
		 "Hoá đơn", "Số HĐ NCC", "Ngày HĐ", "Nội dung", "Bên bán", "Loại chi", "Có VAT",
		 "Hạn trả", "Còn nợ lúc lập", "Đề nghị trả",
		 "Người lập", "Kế toán duyệt", "Giám đốc duyệt", "Ngày thanh toán",
		 "Mã giao dịch", "Đã báo NCC"],
	]
	for r in rows:
		ds = chi_tiet_dong.get(r["name"]) or [None]
		for i, d in enumerate(ds):
			bang.append([
				r["ma"] if i == 0 else "",
				("Hoàn ứng" if r.get("loai") == "Hoan ung" else "NCC") if i == 0 else "",
				str(r["ngay"] or "") if i == 0 else "",
				(r["ten_ncc"] or r["nha_cung_cap"]) if i == 0 else "",
				NHAN.get(r["trang_thai"], r["trang_thai"]) if i == 0 else "",
				flt(r["tong_tien"]) if i == 0 else "",
				flt(r.get("da_tam_ung")) if i == 0 else "",
				flt(r.get("con_lai")) if i == 0 else "",
				(d.hoa_don or "") if d else "",
				(d.so_hd_ncc or "") if d else "",
				str(d.ngay_hd or "") if d else "",
				(d.noi_dung or "") if d else "",
				(d.ben_ban or "") if d else "",
				(d.loai_chi or "") if d else "",
				("Có" if cint(d.co_vat) else "") if d else "",
				str(d.han_tra or "") if d else "",
				flt(d.con_no) if d else "",
				flt(d.so_tien) if d else "",
				_ten_nguoi(r["nguoi_tao"]) if i == 0 else "",
				_ten_nguoi(r["fin_boi"]) if i == 0 else "",
				_ten_nguoi(r["gd_boi"]) if i == 0 else "",
				str(r["ngay_thanh_toan"] or "") if i == 0 else "",
				r["ma_giao_dich"] or "" if i == 0 else "",
				("Rồi" if cint(r["email_da_gui"]) else "Chưa") if i == 0 else "",
			])
	bang.append([])
	bang.append(["TỔNG", "", "", "", kq["tong_tien"]])

	from frappe.utils.xlsxutils import make_xlsx

	tep = make_xlsx(bang, "Ho so thanh toan")
	noi_dung = tep.getvalue() if isinstance(tep, io.BytesIO) else tep
	return {
		"ten_file": "ho-so-thanh-toan-%s.xlsx" % nowdate(),
		"b64": base64.b64encode(noi_dung).decode(),
	}

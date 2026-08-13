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
	doc.ngay = nowdate()
	doc.nha_cung_cap = ma_ncc
	doc.ten_ncc = frappe.db.get_value("Supplier", ma_ncc, "supplier_name") or ma_ncc
	doc.email_ncc = _email_ncc(ma_ncc)
	doc.trang_thai = TT_CHO_FIN if cint(gui_luon) else TT_NHAP
	doc.nguoi_tao = frappe.session.user
	doc.ghi_chu = (ghi_chu or "").strip()
	for d in dong:
		doc.append("dong", d)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "ma": doc.name, "tong_tien": flt(doc.tong_tien), "trang_thai": doc.trang_thai}


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
def danh_sach(trang_thai=None, ncc=None, tu=None, den=None, tu_khoa="", so_ngay=90):
	"""Màn Hồ sơ thanh toán: danh sách kèm đếm theo trạng thái cho chip."""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "xem hồ sơ thanh toán")
	if tu and den:
		loc = {"ngay": ["between", [str(tu), str(den)]]}
	else:
		loc = {"ngay": [">=", add_days(nowdate(), -int(so_ngay or 90))]}
	if ncc:
		loc["nha_cung_cap"] = ncc
	ds = frappe.get_all(
		"Vagabond Ho So TT",
		filters=loc,
		fields=[
			"name", "ma", "ngay", "nha_cung_cap", "ten_ncc", "trang_thai",
			"tong_tien", "da_tra", "han_tra_som_nhat", "nguoi_tao",
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


@frappe.whitelist()
def chi_tiet(name):
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "xem hồ sơ thanh toán")
	doc = frappe.get_doc("Vagabond Ho So TT", name)
	dong = []
	for d in doc.dong:
		con = frappe.db.get_value("Purchase Invoice", d.hoa_don, "outstanding_amount")
		dong.append({
			"hoa_don": d.hoa_don, "so_hd_ncc": d.so_hd_ncc,
			"ngay_hd": str(d.ngay_hd or ""), "han_tra": str(d.han_tra or ""),
			"tong_hd": flt(d.tong_hd), "con_no_luc_lap": flt(d.con_no),
			"con_no_hien_tai": flt(con), "so_tien": flt(d.so_tien),
			"ghi_chu": d.ghi_chu or "",
		})
	return {
		"ho_so": {
			"ma": doc.name, "ngay": str(doc.ngay or ""),
			"ncc": doc.nha_cung_cap, "ten_ncc": doc.ten_ncc,
			"email_ncc": doc.email_ncc or "",
			"trang_thai": doc.trang_thai, "nhan": NHAN.get(doc.trang_thai, doc.trang_thai),
			"tong_tien": flt(doc.tong_tien), "da_tra": flt(doc.da_tra),
			"han_tra_som_nhat": str(doc.han_tra_som_nhat or ""),
			"nguoi_tao": doc.nguoi_tao, "fin_boi": doc.fin_boi,
			"fin_luc": str(doc.fin_luc or ""), "gd_boi": doc.gd_boi,
			"gd_luc": str(doc.gd_luc or ""), "ly_do_tu_choi": doc.ly_do_tu_choi or "",
			"ngay_thanh_toan": str(doc.ngay_thanh_toan or ""),
			"ma_giao_dich": doc.ma_giao_dich or "", "phuong_thuc": doc.phuong_thuc or "",
			"email_da_gui": cint(doc.email_da_gui),
			"email_gui_luc": str(doc.email_gui_luc or ""),
			"email_gui_toi": doc.email_gui_toi or "",
			"ghi_chu": doc.ghi_chu or "",
		},
		"dong": dong,
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
	"""Sinh Payment Entry trả nhà cung cấp, phân bổ vào đúng từng hoá đơn."""
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	cong_ty = frappe.db.get_value("Purchase Invoice", doc.dong[0].hoa_don, "company")
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
	for d in doc.dong:
		hd = frappe.db.get_value(
			"Purchase Invoice", d.hoa_don, ["grand_total", "outstanding_amount", "posting_date", "due_date"],
			as_dict=True,
		) or {}
		pe.append("references", {
			"reference_doctype": "Purchase Invoice",
			"reference_name": d.hoa_don,
			"total_amount": flt(hd.get("grand_total")),
			"outstanding_amount": flt(hd.get("outstanding_amount")),
			"allocated_amount": min(flt(d.so_tien), flt(hd.get("outstanding_amount"))),
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
			% (h(d.so_hd_ncc or d.hoa_don), _ngay_vn(d.ngay_hd), _tien(d.so_tien))
		)
	bang = (
		'<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" '
		'style="border-collapse:collapse;margin:6px 0 4px">'
		'<tr><td style="padding:7px 10px;background:#E4F9FD;font-size:12px;font-weight:bold;color:#05323C">Số hoá đơn</td>'
		'<td style="padding:7px 10px;background:#E4F9FD;font-size:12px;font-weight:bold;color:#05323C">Ngày</td>'
		'<td style="padding:7px 10px;background:#E4F9FD;font-size:12px;font-weight:bold;color:#05323C;text-align:right">Số tiền</td></tr>'
		+ "".join(hang) +
		'<tr><td colspan="2" style="padding:9px 10px;font-size:13.5px;font-weight:bold;color:#05323C">TỔNG THANH TOÁN</td>'
		'<td style="padding:9px 10px;font-size:15px;font-weight:bold;color:#0B7C93;text-align:right;white-space:nowrap">%s đ</td></tr>'
		"</table>"
	) % _tien(doc.tong_tien)

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


# -------------------------------------------------------------------- Excel


@frappe.whitelist()
def xuat_excel(trang_thai=None, ncc=None, tu=None, den=None, tu_khoa="", so_ngay=90):
	"""Bộ hồ sơ ra Excel cho kế toán theo dõi: một dòng một hoá đơn."""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "xuất hồ sơ thanh toán")
	kq = danh_sach(trang_thai=trang_thai, ncc=ncc, tu=tu, den=den, tu_khoa=tu_khoa, so_ngay=so_ngay)
	rows = kq["rows"]
	chi_tiet_dong = {}
	if rows:
		for d in frappe.get_all(
			"Vagabond Ho So TT Dong",
			filters={"parent": ["in", [r["name"] for r in rows]]},
			fields=["parent", "hoa_don", "so_hd_ncc", "ngay_hd", "han_tra", "con_no", "so_tien"],
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
		["Mã hồ sơ", "Ngày lập", "Nhà cung cấp", "Trạng thái", "Tổng hồ sơ",
		 "Hoá đơn", "Số HĐ NCC", "Ngày HĐ", "Hạn trả", "Còn nợ lúc lập", "Đề nghị trả",
		 "Người lập", "Kế toán duyệt", "Giám đốc duyệt", "Ngày thanh toán",
		 "Mã giao dịch", "Đã báo NCC"],
	]
	for r in rows:
		ds = chi_tiet_dong.get(r["name"]) or [None]
		for i, d in enumerate(ds):
			bang.append([
				r["ma"] if i == 0 else "",
				str(r["ngay"] or "") if i == 0 else "",
				(r["ten_ncc"] or r["nha_cung_cap"]) if i == 0 else "",
				NHAN.get(r["trang_thai"], r["trang_thai"]) if i == 0 else "",
				flt(r["tong_tien"]) if i == 0 else "",
				d.hoa_don if d else "",
				(d.so_hd_ncc or "") if d else "",
				str(d.ngay_hd or "") if d else "",
				str(d.han_tra or "") if d else "",
				flt(d.con_no) if d else "",
				flt(d.so_tien) if d else "",
				r["nguoi_tao"] if i == 0 else "",
				r["fin_boi"] or "" if i == 0 else "",
				r["gd_boi"] or "" if i == 0 else "",
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

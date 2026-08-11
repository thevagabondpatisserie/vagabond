# -*- coding: utf-8 -*-
"""Cong no phai thu: khach si (Ravie...) va khach VIP gom nhieu hoa don
tra mot lan (anh Viet 11/08/2026).

Vong doi:
  ban hang chon phuong thuc "Cong no" + chon khach
    -> hoa don ghi so nhung KHONG coi la da thu tien
    -> man Cong no phai thu: tick khach, tick nhung hoa don con no
    -> sinh mot PHIEU DOI NO co ma rieng + ma QR MB Bank song 7 ngay
    -> gui khach, khach chuyen mot lan
    -> SePay bat duoc noi dung chua ma phieu -> tu khop -> clear cong no

Vi sao mot ma QR cho ca cum hoa don chu khong tung cai: khach si chuyen
mot lan cho ca thang, doi soat tung bill se khong bao gio khop duoc.
"""

import re

import frappe
from frappe.utils import add_days, flt, getdate, nowdate

from vagabond.ban_hang import _kiem_quyen, QR_QUAY

# Ma phieu doi no: CN + 6 ky tu. Tach han khong gian ma voi bill quay
# (VGB + 5) de khong bao gio khop nham sang nhau.
RE_MA_CN = re.compile(r"CN[A-Z0-9]{6}")

# Ma QR song bao lau. Anh Viet chot 7 ngay: du de ke toan khach si duyet
# chi, ma khong de mot ma treo mai roi khach chuyen nham vao phieu cu.
QR_SO_NGAY = 7

TRANG_THAI_CON_NO = ("Cho thu", "Thu thieu")


def _sinh_ma_cn():
	"""Ma phieu ngan, khong nham lan chu O voi so 0."""
	chu = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
	for _ in range(40):
		ma = "CN" + "".join(
			chu[int(c, 16) % len(chu)] for c in frappe.generate_hash(length=6)
		)
		if not frappe.db.exists("Vagabond Cong No", ma):
			return ma
	frappe.throw("Không sinh được mã phiếu công nợ, thử lại giúp em.")


def _sepay_theo_ma_cn(ds_ma):
	"""Tien SePay da nhan cho tung ma phieu cong no.

	Khach chuyen khoan voi noi dung chua ma CNxxxxxx, ngan hang tra ve
	nguyen chuoi do trong description.
	"""
	ds_ma = [
		str(m).strip().upper()
		for m in (ds_ma or [])
		if RE_MA_CN.fullmatch(str(m or "").strip().upper())
	]
	if not ds_ma:
		return {}
	mau = "(%s)" % "|".join(sorted(set(ds_ma)))
	try:
		gds = frappe.db.sql(
			"""select description, deposit, withdrawal
			from `tabBank Transaction`
			where docstatus < 2 and description regexp %s""",
			mau,
			as_dict=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "cong_no: doc SePay theo ma phieu")
		return {}
	ra = {}
	for g in gds:
		for m in RE_MA_CN.findall((g.get("description") or "").upper()):
			if m not in ds_ma:
				continue
			o = ra.setdefault(m, {"nhan": 0.0, "so_gd": 0})
			o["nhan"] += flt(g.get("deposit")) - flt(g.get("withdrawal"))
			o["so_gd"] += 1
	return ra


def _hd_da_gom():
	"""Hoa don dang nam trong mot phieu doi no chua thu xong - khong duoc
	gom lai lan nua."""
	ds = frappe.db.sql(
		"""select d.hoa_don from `tabVagabond Cong No Dong` d
		inner join `tabVagabond Cong No` p on p.name = d.parent
		where p.trang_thai in ('Cho thu', 'Thu thieu')""",
		as_dict=True,
	)
	return set(r["hoa_don"] for r in ds)


@frappe.whitelist()
def ds_khach_no():
	"""Danh sach khach dang con no, kem so tien va so hoa don.

	Chi tinh hoa don DA GHI SO va co phuong thuc Cong no - hoa don nhap
	con o ban nhap thi chua phai la no that.
	"""
	_kiem_quyen()
	rows = frappe.get_all(
		"Sales Invoice",
		filters={"docstatus": 1, "vgb_pt_thanh_toan": "Công nợ"},
		fields=[
			"name", "customer", "customer_name", "posting_date",
			"grand_total", "custom_nguon", "vgb_quay", "vgb_ma_tham_chieu",
		],
		order_by="posting_date asc",
		limit_page_length=0,
	)
	da_gom = _hd_da_gom()
	khach = {}
	for r in rows:
		k = r.customer or "(chưa gắn khách)"
		o = khach.setdefault(
			k,
			{
				"khach": r.customer or "",
				"ten": r.customer_name or r.customer or "(chưa gắn khách)",
				"so_hd": 0,
				"tien": 0.0,
				"cu_nhat": None,
				"hd": [],
			},
		)
		if r.name in da_gom:
			continue
		o["so_hd"] += 1
		o["tien"] += flt(r.grand_total)
		if not o["cu_nhat"] or str(r.posting_date) < o["cu_nhat"]:
			o["cu_nhat"] = str(r.posting_date)
		o["hd"].append(
			{
				"name": r.name,
				"ngay": str(r.posting_date),
				"tien": flt(r.grand_total),
				"nguon": r.custom_nguon or "",
				"quay": r.vgb_quay or "",
				"ma": r.vgb_ma_tham_chieu or "",
			}
		)
	ra = [v for v in khach.values() if v["so_hd"]]
	# Khach no lau nhat len dau - do la khoan de mat nhat.
	ra.sort(key=lambda x: (x["cu_nhat"] or "9999"))
	hom_nay = getdate(nowdate())
	for v in ra:
		v["so_ngay"] = (hom_nay - getdate(v["cu_nhat"])).days if v["cu_nhat"] else 0
	return {"khach": ra, "tong": sum(v["tien"] for v in ra)}


@frappe.whitelist()
def tao_phieu(khach=None, hoa_don=None, ghi_chu=""):
	"""Gom nhung hoa don da tick thanh MOT phieu doi no."""
	_kiem_quyen()
	khach = (khach or "").strip()
	if not khach:
		frappe.throw("Chưa chọn khách hàng.")
	if isinstance(hoa_don, str):
		hoa_don = frappe.parse_json(hoa_don or "[]")
	hoa_don = [str(x).strip() for x in (hoa_don or []) if str(x or "").strip()]
	if not hoa_don:
		frappe.throw("Chưa tick hoá đơn nào để gom.")
	da_gom = _hd_da_gom()
	dong = []
	for name in hoa_don:
		if name in da_gom:
			frappe.throw("Hoá đơn %s đã nằm trong một phiếu đề nghị thanh toán khác." % name)
		si = frappe.db.get_value(
			"Sales Invoice",
			name,
			["customer", "posting_date", "grand_total", "custom_nguon", "docstatus", "vgb_pt_thanh_toan"],
			as_dict=True,
		)
		if not si:
			frappe.throw("Không có hoá đơn %s." % name)
		if si.docstatus != 1:
			frappe.throw("Hoá đơn %s chưa ghi sổ, không gom được." % name)
		if (si.vgb_pt_thanh_toan or "") != "Công nợ":
			frappe.throw("Hoá đơn %s không phải hoá đơn công nợ." % name)
		if (si.customer or "") != khach:
			frappe.throw("Hoá đơn %s không phải của khách này." % name)
		dong.append(
			{
				"hoa_don": name,
				"ngay": si.posting_date,
				"nguon": si.custom_nguon or "",
				"so_tien": flt(si.grand_total),
			}
		)
	doc = frappe.new_doc("Vagabond Cong No")
	doc.ma_phieu = _sinh_ma_cn()
	doc.khach = khach
	doc.ten_khach = frappe.db.get_value("Customer", khach, "customer_name") or khach
	doc.ngay_tao = nowdate()
	doc.han_qr = add_days(nowdate(), QR_SO_NGAY)
	doc.trang_thai = "Cho thu"
	doc.ghi_chu = (ghi_chu or "").strip()
	doc.nguoi_tao = frappe.session.user
	for d in dong:
		doc.append("dong", d)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return xem_phieu(doc.name)


@frappe.whitelist()
def ds_phieu(trang_thai=None):
	"""Danh sach phieu doi no, kem tien SePay da ve."""
	_kiem_quyen()
	dk = {}
	if trang_thai:
		dk["trang_thai"] = trang_thai
	ds = frappe.get_all(
		"Vagabond Cong No",
		filters=dk,
		fields=[
			"name", "ma_phieu", "khach", "ten_khach", "ngay_tao", "han_qr",
			"tong_tien", "da_thu", "trang_thai", "ghi_chu",
		],
		order_by="creation desc",
		limit_page_length=200,
	)
	sepay = _sepay_theo_ma_cn([r.ma_phieu for r in ds])
	hom_nay = getdate(nowdate())
	for r in ds:
		g = sepay.get(str(r.ma_phieu or "").upper()) or {}
		r["sepay"] = flt(g.get("nhan"))
		r["con_thieu"] = max(0.0, flt(r.tong_tien) - flt(r["sepay"]))
		r["het_han"] = bool(r.han_qr and getdate(r.han_qr) < hom_nay)
		r["so_hd"] = frappe.db.count("Vagabond Cong No Dong", {"parent": r.name})
	return {"phieu": ds}


@frappe.whitelist()
def xem_phieu(name):
	"""Chi tiet mot phieu doi no kem duong dan ma QR."""
	_kiem_quyen()
	doc = frappe.get_doc("Vagabond Cong No", name)
	sepay = _sepay_theo_ma_cn([doc.ma_phieu]).get(str(doc.ma_phieu).upper()) or {}
	nhan = flt(sepay.get("nhan"))
	return {
		"name": doc.name,
		"ma_phieu": doc.ma_phieu,
		"khach": doc.khach,
		"ten_khach": doc.ten_khach,
		"ngay_tao": str(doc.ngay_tao or ""),
		"han_qr": str(doc.han_qr or ""),
		"het_han": bool(doc.han_qr and getdate(doc.han_qr) < getdate(nowdate())),
		"tong_tien": flt(doc.tong_tien),
		"da_thu": flt(doc.da_thu),
		"sepay": nhan,
		"con_thieu": max(0.0, flt(doc.tong_tien) - nhan),
		"trang_thai": doc.trang_thai,
		"ghi_chu": doc.ghi_chu or "",
		"qr": QR_QUAY,
		"dong": [
			{
				"hoa_don": d.hoa_don,
				"ngay": str(d.ngay or ""),
				"nguon": d.nguon or "",
				"so_tien": flt(d.so_tien),
			}
			for d in doc.dong
		],
	}


@frappe.whitelist()
def kiem_sepay(name):
	"""Doi chieu voi SePay va tu clear cong no khi tien da ve du."""
	_kiem_quyen()
	doc = frappe.get_doc("Vagabond Cong No", name)
	sepay = _sepay_theo_ma_cn([doc.ma_phieu]).get(str(doc.ma_phieu).upper()) or {}
	nhan = flt(sepay.get("nhan"))
	doc.da_thu = nhan
	# Lech duoi 1 dong coi nhu du - ngan hang lam tron.
	if nhan >= flt(doc.tong_tien) - 1:
		doc.trang_thai = "Da thu du"
	elif nhan > 0:
		doc.trang_thai = "Thu thieu"
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return xem_phieu(name)


@frappe.whitelist()
def huy_phieu(name, ly_do=""):
	"""Huy phieu de nhung hoa don trong do quay lai danh sach cho gom."""
	_kiem_quyen()
	doc = frappe.get_doc("Vagabond Cong No", name)
	if doc.trang_thai == "Da thu du":
		frappe.throw("Phiếu đã thu đủ tiền, không huỷ được.")
	doc.trang_thai = "Huy"
	doc.ghi_chu = ((doc.ghi_chu or "") + "\nHuỷ: " + (ly_do or "")).strip()
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1}


@frappe.whitelist()
def tim_khach(tu_khoa=""):
	"""Bang tim khach hang cho o chon khach: tim theo ma, ten, ma so thue,
	so dien thoai tren ho so VA so dien thoai o danh ba lien he.

	Anh Viet 11/08/2026: go "Ravie" hay go so dien thoai deu phai xo ra
	danh sach. Truoc day chi tim theo ma va ten nen go so dien thoai khong
	bao gio ra.
	"""
	_kiem_quyen()
	q = (tu_khoa or "").strip()
	truong = ["name", "customer_name", "tax_id", "customer_group", "mobile_no"]
	if not q:
		ds = frappe.get_all(
			"Customer",
			filters={"disabled": 0},
			fields=truong,
			order_by="customer_name asc",
			limit_page_length=60,
		)
		return {"khach": ds}

	ds = frappe.get_all(
		"Customer",
		filters={"disabled": 0},
		or_filters={
			"name": ["like", "%" + q + "%"],
			"customer_name": ["like", "%" + q + "%"],
			"tax_id": ["like", "%" + q + "%"],
			"mobile_no": ["like", "%" + q + "%"],
		},
		fields=truong,
		order_by="customer_name asc",
		limit_page_length=40,
	)
	da_co = {r.name for r in ds}

	# Tim theo so dien thoai o danh ba lien he: khach si thuong luu so o
	# nguoi lien he chu khong o ho so cong ty.
	so = re.sub(r"\D", "", q)
	if len(so) >= 6:
		try:
			ten_lh = frappe.get_all(
				"Contact Phone",
				filters={"phone": ["like", "%" + so + "%"]},
				fields=["parent"],
				limit_page_length=60,
			)
			cha = [r.parent for r in ten_lh]
			if cha:
				lk = frappe.get_all(
					"Dynamic Link",
					filters={
						"parent": ["in", cha],
						"link_doctype": "Customer",
						"parenttype": "Contact",
					},
					fields=["link_name"],
					limit_page_length=60,
				)
				them = [r.link_name for r in lk if r.link_name and r.link_name not in da_co]
				if them:
					ds += frappe.get_all(
						"Customer",
						filters={"name": ["in", them], "disabled": 0},
						fields=truong,
						limit_page_length=20,
					)
		except Exception:
			pass
	return {"khach": ds}


@frappe.whitelist()
def thong_tin_xhd(khach=None):
	"""Thong tin xuat hoa don da luu cua mot khach, de man tinh tien dien
	san khoi go lai (anh Viet 11/08/2026)."""
	_kiem_quyen()
	khach = (khach or "").strip()
	if not khach:
		return {}
	c = frappe.db.get_value(
		"Customer",
		khach,
		["customer_name", "tax_id", "customer_primary_address", "customer_primary_contact"],
		as_dict=True,
	) or {}
	dia_chi, email = "", ""
	if c.get("customer_primary_address"):
		a = frappe.db.get_value(
			"Address",
			c["customer_primary_address"],
			["address_line1", "address_line2", "city", "state"],
			as_dict=True,
		) or {}
		dia_chi = ", ".join(
			[x for x in [a.get("address_line1"), a.get("address_line2"), a.get("city"), a.get("state")] if x]
		)
	if c.get("customer_primary_contact"):
		email = frappe.db.get_value("Contact", c["customer_primary_contact"], "email_id") or ""
	if not email:
		# Nhieu khach si khong gan contact chinh - lay dai dien mot email.
		ds = frappe.get_all(
			"Dynamic Link",
			filters={"link_doctype": "Customer", "link_name": khach, "parenttype": "Contact"},
			fields=["parent"],
			limit_page_length=5,
		)
		for d in ds:
			e = frappe.db.get_value("Contact", d.parent, "email_id")
			if e:
				email = e
				break
	return {
		"ten": c.get("customer_name") or "",
		"mst": c.get("tax_id") or "",
		"dia_chi": dia_chi,
		"email": email,
	}

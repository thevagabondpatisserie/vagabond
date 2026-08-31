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

from vagabond.ban_hang import _kiem_quyen
from vagabond import chiem_sao_ke, tai_khoan

# Ma phieu yeu cau thanh toan.
#
# Doi 14/08/2026 theo anh Viet: truoc day la CN + 6 ky tu ngau nhien
# (CNNGRJJF). Ma ngau nhien doc len khong biet cua thang nao, ma khach si
# thi giu to phieu ca thang moi tra. Nay theo thang: DNTT-26-08-00001.
#
# Ma CU VAN PHAI KHOP: nhung phieu da gui cho khach truoc hom nay van dang
# mang ma CNxxxxxx, khach chuyen theo noi dung do. Bo mau cu di la tien ve
# khong ai nhan ra.
RE_MA_CN = re.compile(r"CN[A-Z0-9]{6}")
RE_MA_DNTT = re.compile(r"DNTT[0-9]{9}")
TIEN_TO_DNTT = "DNTT"


def _chuan_ma(chuoi):
	"""Bo moi ky tu khong phai chu va so, viet hoa.

	Can vi ma hien tren phieu la "DNTT-26-08-00001" cho de doc, con noi dung
	chuyen khoan ngan hang tra ve thuong da bi bo dau gach - moi ngan hang
	xu ly mot kieu. So sanh tren ban da chuan hoa thi kieu nao cung khop.
	"""
	return re.sub(r"[^A-Z0-9]", "", str(chuoi or "").upper())

# Ma QR song bao lau. Anh Viet chot 7 ngay: du de ke toan khach si duyet
# chi, ma khong de mot ma treo mai roi khach chuyen nham vao phieu cu.
QR_SO_NGAY = 7

TRANG_THAI_CON_NO = ("Cho thu", "Thu thieu")


def _sinh_ma_cn():
	"""Ma phieu theo thang: DNTT-26-08-00001.

	Dem theo tien to cua thang chu khong dem tong: sang thang 09 thi so lai
	chay tu 00001, giong cach ma hoa don HDB va HDM dang chay.
	"""
	hn = getdate(nowdate())
	tien_to = "%s-%02d-%02d-" % (TIEN_TO_DNTT, hn.year % 100, hn.month)
	cuoi = frappe.db.sql(
		"""select ma_phieu from `tabVagabond Cong No`
		where ma_phieu like %s order by ma_phieu desc limit 1""",
		(tien_to + "%",),
	)
	so = 0
	if cuoi and cuoi[0][0]:
		duoi = str(cuoi[0][0]).rsplit("-", 1)[-1]
		if duoi.isdigit():
			so = int(duoi)
	for _ in range(50):
		so += 1
		ma = "%s%05d" % (tien_to, so)
		if not frappe.db.exists("Vagabond Cong No", {"ma_phieu": ma}):
			return ma
	frappe.throw("Không sinh được mã phiếu yêu cầu thanh toán, vui lòng thử lại.")


def _sepay_theo_ma_cn(ds_ma):
	"""Tien SePay da nhan cho tung ma phieu cong no.

	Khach chuyen khoan voi noi dung chua ma CNxxxxxx, ngan hang tra ve
	nguyen chuoi do trong description.
	"""
	# Khoa tra cuu la ma DA CHUAN HOA, gia tri tra ve van la ma goc de cho
	# goi khong phai doi lai.
	theo_chuan = {}
	for m in ds_ma or []:
		goc = str(m or "").strip().upper()
		chuan = _chuan_ma(goc)
		if RE_MA_CN.fullmatch(chuan) or RE_MA_DNTT.fullmatch(chuan):
			theo_chuan[chuan] = goc
	if not theo_chuan:
		return {}
	# Loc so bo o tang SQL cho nhe, roi loc lai chac chan o Python tren ban
	# da chuan hoa. Loc SQL dung tien to vi dau gach co the bi ngan hang bo.
	mau = "(%s)" % "|".join(
		sorted(set(k[:6] for k in theo_chuan))
	)
	try:
		gds = frappe.db.sql(
			"""select name, description, reference_number, deposit, withdrawal
			from `tabBank Transaction`
			where docstatus < 2
			and (upper(description) regexp %s or upper(reference_number) regexp %s)""",
			(mau, mau),
			as_dict=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "cong_no: doc SePay theo ma phieu")
		return {}, []
	ra, bo_qua = {}, []
	for g in gds:
		mo_ta = _chuan_ma("%s %s" % (g.get("description") or "", g.get("reference_number") or ""))
		thay = set(RE_MA_CN.findall(mo_ta)) | set(RE_MA_DNTT.findall(mo_ta))
		# CHI GIU MA CUA CHINH DOT NAY. Mot dong sao ke nhac hai ma phieu
		# khac nhau thi may khong biet chia tien cho ai; cong du cho ca hai
		# la nhan doi tien. De nguyen cho nguoi khop tay.
		thay = sorted(m for m in thay if theo_chuan.get(m))
		if not thay:
			continue
		if chiem_sao_ke.dong_nhap_nhang(thay):
			bo_qua.append({
				"ten": g.get("name"),
				"ma": [theo_chuan[m] for m in thay],
				"tien": flt(g.get("deposit")) - flt(g.get("withdrawal")),
			})
			continue
		goc = theo_chuan[thay[0]]
		o = ra.setdefault(goc, {"nhan": 0.0, "so_gd": 0, "gd": []})
		o["nhan"] += flt(g.get("deposit")) - flt(g.get("withdrawal"))
		o["so_gd"] += 1
		if g.get("name") and g["name"] not in o["gd"]:
			o["gd"].append(g["name"])
	return ra, bo_qua


def _sepay_cn(ma):
	"""Bang ket qua cua MOT ma phieu."""
	theo_ma, _bo = _sepay_theo_ma_cn([ma])
	return theo_ma.get(str(ma or "").strip().upper()) or {}


def _giu_gd(doc, ds_gd):
	"""Cac dong sao ke phieu nay dang giu, sau khi chac chan khong dong nao
	da thuoc ve chung tu khac. Tra ve chuoi de ghi vao `ma_gd`.

	Nem loi kem TEN chung tu dang giu, de nguoi doc biet phai di doi chieu o
	dau chu khong phai doan.
	"""
	ds_gd = chiem_sao_ke.tach_gd("\n".join(str(x or "") for x in (ds_gd or [])))
	if not ds_gd:
		return str(doc.get("ma_gd") or "").strip()
	from vagabond import doi_soat_sepay as dss

	chu = dss.chu_cua_giao_dich(ds_gd, bo_qua_loai="cong_no", bo_qua_phieu=doc.name)
	dung_hai = chiem_sao_ke.gd_dung_hai_lan(ds_gd, chu)
	if dung_hai:
		frappe.throw(
			"Không ghi nhận được cho phiếu %s: %s. Một lần chuyển khoản chỉ được "
			"tính cho một chứng từ. Vui lòng kiểm lại nội dung chuyển khoản, hoặc "
			"báo bộ phận kế toán đối soát tay."
			% (doc.ma_phieu, "; ".join(
				"giao dịch %s đã gạch cho %s" % (m, c) for m, c in dung_hai))
		)
	return chiem_sao_ke.gom_gd(ds_gd)


TRUONG_MOI = {
	"Vagabond Cong No": [
		{
			"fieldname": "ma_gd",
			"label": "Dòng sao kê đã gạch cho phiếu này",
			"fieldtype": "Small Text",
			"insert_after": "da_thu",
			"read_only": 1,
			"description": (
				"Mã các dòng sao kê ngân hàng đã được tính là tiền của phiếu này. "
				"Một dòng sao kê chỉ được gạch cho một chứng từ."
			),
		},
		{
			"fieldname": "nguoi_khop_tay",
			"label": "Người khớp tay",
			"fieldtype": "Data",
			"insert_after": "ma_gd",
			"read_only": 1,
		},
		{
			"fieldname": "ngay_khop_tay",
			"label": "Lúc khớp tay",
			"fieldtype": "Datetime",
			"insert_after": "nguoi_khop_tay",
			"read_only": 1,
		},
	]
}


def _ma_do_cong_no(ho_so):
	g = ho_so.get if hasattr(ho_so, "get") else (lambda k: getattr(ho_so, k, None))
	return str(g("ma_phieu") or "").strip()


def _tien_cong_no(ho_so):
	g = ho_so.get if hasattr(ho_so, "get") else (lambda k: getattr(ho_so, k, None))
	return flt(g("tong_tien") or 0)


def _khai_doi_soat():
	"""Dang ky luong cong no vao so doi soat dung chung (dot 2, v299).

	Day la luong tien VAO dau tien vao so. Hai luong da co deu la tien RA.
	"""
	from vagabond import doi_soat_sepay as dss

	dss.khai(
		loai="cong_no",
		doctype="Vagabond Cong No",
		chieu=dss.VAO,
		ma_do=_ma_do_cong_no,
		so_tien=_tien_cong_no,
		dang_cho={"trang_thai": ["in", ["Cho thu", "Thu thieu"]]},
		ten_man="phiếu công nợ",
		truong_gd="ma_gd",
		# Phieu da huy thi NHA dong sao ke ra: tien do hoac chua ve, hoac da
		# duoc thu bang mot phieu khac.
		loc_chiem={"trang_thai": ["!=", "Huy"]},
		truong_nguoi="nguoi_khop_tay",
		truong_luc="ngay_khop_tay",
	)


_khai_doi_soat()


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
			"vgb_khach_no",
		],
		order_by="posting_date asc",
		limit_page_length=0,
	)
	da_gom = _hd_da_gom()
	khach = {}
	for r in rows:
		# Don da ghi so roi moi phat hien gan nham khach le thi ke toan gan
		# chu no vao truong phu vgb_khach_no - khong sua duoc customer nua
		# vi but toan da len so cai. Cot phu nay uu tien hon customer.
		if r.get("vgb_khach_no"):
			r.customer = r.vgb_khach_no
			r.customer_name = (
				frappe.db.get_value("Customer", r.vgb_khach_no, "customer_name") or r.vgb_khach_no
			)
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
			[
				"customer", "posting_date", "grand_total", "custom_nguon",
				"docstatus", "vgb_pt_thanh_toan", "vgb_khach_no",
			],
			as_dict=True,
		)
		if not si:
			frappe.throw("Không có hoá đơn %s." % name)
		if si.docstatus != 1:
			frappe.throw("Hoá đơn %s chưa ghi sổ, không gom được." % name)
		if (si.vgb_pt_thanh_toan or "") != "Công nợ":
			frappe.throw("Hoá đơn %s không phải hoá đơn công nợ." % name)
		# Chu no that nam o vgb_khach_no neu ke toan da gan lai sau khi ghi
		# so - cot do uu tien hon customer, giong ben ds_khach_no.
		if si.get("vgb_khach_no"):
			si.customer = si.vgb_khach_no
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
	sepay, _bo_qua = _sepay_theo_ma_cn([r.ma_phieu for r in ds])
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
	sepay = _sepay_cn(doc.ma_phieu)
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
		# Phieu doi no dung tai khoan ao rieng cua khach si neu da khai: khach
		# si hay chuyen theo noi dung cua ho chu khong theo noi dung minh dat
		# (ca OSHIMA 11/08/2026), nen tach bang TAI KHOAN moi chac.
		"qr": tai_khoan.tk_phieu_no(),
		"dong": [
			{
				"hoa_don": d.hoa_don,
				"ngay": str(d.ngay or ""),
				"nguon": d.nguon or "",
				"so_gtgt": _so_hd_gtgt(d.hoa_don),
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
	truoc = doc.trang_thai
	sepay = _sepay_cn(doc.ma_phieu)
	# MOT DONG SAO KE CHI DUOC GACH CHO MOT CHUNG TU.
	#
	# Truoc day phieu cong no khong ghi lai dong sao ke nao da tinh cho no,
	# nen khong the co phep chan nao ca: mot lan khach chuyen tien co the
	# vua lam sach mot phieu cong no vua duoc tinh la tien cua mot bill quay.
	# Nay ghi ro, va hoi ca cac luong khac truoc khi nhan.
	gd = _giu_gd(doc, sepay.get("gd") or [])
	nhan = flt(sepay.get("nhan"))
	doc.da_thu = nhan
	# Lech duoi 1 dong coi nhu du - ngan hang lam tron.
	if nhan >= flt(doc.tong_tien) - 1:
		doc.trang_thai = "Da thu du"
	elif nhan > 0:
		doc.trang_thai = "Thu thieu"
	doc.ma_gd = gd
	da_du_truoc = truoc == "Da thu du"
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	# Thu bao vua nhan tien: chi gui MOT lan, dung luc phieu chuyen sang du.
	if doc.trang_thai == "Da thu du" and not da_du_truoc:
		try:
			_gui_thu_da_nhan(doc)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "cong_no: gui thu bao da nhan loi")
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


# ------------------------------------------------------- Xuat phieu ra PDF


def _so_hd_gtgt(hoa_don):
	"""So hoa don GTGT tren to hoa don dien tu, dang 'C26MVO 32536'.

	Anh Viet 14/08/2026 khoanh do them cot nay: ke toan ben khach si can so
	hoa don DO de hach toan, con so noi bo HDB-2026-xxxxx chi de minh tra.
	"""
	if not hoa_don:
		return ""
	d = frappe.db.get_value(
		"Sales Invoice", hoa_don,
		["custom_hddt_ky_hieu", "custom_hddt_so"], as_dict=True,
	)
	if not d:
		return ""
	kh = (d.get("custom_hddt_ky_hieu") or "").strip()
	so = str(d.get("custom_hddt_so") or "").strip()
	if kh and so:
		return "%s %s" % (kh, so)
	return so or kh or ""


# Ten day du ngan hang de in tren to gui khach. Anh Viet 14/08/2026: viet
# "MB" khong thoi thi ke toan ben khach khong biet la ngan hang nao.
TEN_NGAN_HANG_DAY_DU = {
	"MB": "MB (Ngân hàng TMCP Quân đội)",
	"VCB": "Vietcombank (Ngân hàng TMCP Ngoại thương Việt Nam)",
	"ICB": "VietinBank (Ngân hàng TMCP Công thương Việt Nam)",
	"BIDV": "BIDV (Ngân hàng TMCP Đầu tư và Phát triển Việt Nam)",
	"TCB": "Techcombank (Ngân hàng TMCP Kỹ thương Việt Nam)",
	"ACB": "ACB (Ngân hàng TMCP Á Châu)",
	"VPB": "VPBank (Ngân hàng TMCP Việt Nam Thịnh Vượng)",
	"OCB": "OCB (Ngân hàng TMCP Phương Đông)",
	"VBA": "Agribank (Ngân hàng NN và PTNT Việt Nam)",
}


def _qr_data_uri(qr, so_tien, noi_dung):
	"""Tai anh QR VietQR ve roi nhung thang vao HTML dang data URI.

	Khong tro thang src toi img.vietqr.io: wkhtmltopdf tren may chu dung
	tien trinh rieng, no tai anh ngoai rat cham va co luc bo qua han - to
	PDF gui khach ma thieu ma QR thi hong mat mot nua cong dung.
	"""
	import base64 as _b64

	if not (qr or {}).get("stk"):
		return ""
	url = (
		"https://img.vietqr.io/image/%s-%s-qr_only.png?amount=%d&addInfo=%s&accountName=%s"
		% (
			qr.get("bank") or "MB",
			qr["stk"],
			int(round(flt(so_tien))),
			frappe.utils.quoted(noi_dung or ""),
			frappe.utils.quoted(qr.get("ten") or ""),
		)
	)
	try:
		import requests

		r = requests.get(url, timeout=8)
		if r.status_code == 200 and r.content:
			return "data:image/png;base64," + _b64.b64encode(r.content).decode()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "cong_no: tai anh QR loi")
	return ""


def _ngay_vn(v):
	if not v:
		return ""
	d = getdate(v)
	return "%02d/%02d/%d" % (d.day, d.month, d.year)


def _tien_vn(v):
	return "{:,.0f}".format(flt(v)).replace(",", ".")


def _chu_so_tien(so):
	"""Doc so tien bang chu. Ke toan khach si hay doi dong nay tren to trinh."""
	so = int(round(flt(so)))
	if so == 0:
		return "Không đồng"
	don_vi = ["", "nghìn", "triệu", "tỷ", "nghìn tỷ"]
	so_chu = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]

	def doc_ba(n, day_du):
		tram, chuc, dv = n // 100, (n // 10) % 10, n % 10
		ra = []
		if tram or day_du:
			ra.append(so_chu[tram] + " trăm")
		if chuc == 0 and dv and (tram or day_du):
			ra.append("lẻ")
		elif chuc == 1:
			ra.append("mười")
		elif chuc > 1:
			ra.append(so_chu[chuc] + " mươi")
		if dv:
			if chuc > 1 and dv == 1:
				ra.append("mốt")
			elif chuc >= 1 and dv == 5:
				ra.append("lăm")
			else:
				ra.append(so_chu[dv])
		return " ".join(x for x in ra if x)

	cum = []
	n = so
	while n > 0:
		cum.append(n % 1000)
		n //= 1000
	phan = []
	for i in range(len(cum) - 1, -1, -1):
		if cum[i] == 0:
			continue
		phan.append(doc_ba(cum[i], i != len(cum) - 1) + (" " + don_vi[i] if don_vi[i] else ""))
	ra = " ".join(phan).strip()
	return (ra[0].upper() + ra[1:] + " đồng") if ra else "Không đồng"


def _phieu_html(name):
	"""To phieu yeu cau thanh toan gui khach, dung khuon ban in Don mua hang.

	Anh Viet 14/08/2026: *"Thêm nút Xuất phiếu sẽ xuất ra phiếu pdf để gửi
	cho bên khách với đầy đủ thông tin mà em thấy là hợp lý nhất, biên soạn
	theo branding của mẫu phiếu PO cho đẹp"*.

	To nay khac han giay de nghi thanh toan ben ho_so_tt: cai kia gui NOI BO
	de xin duyet chi, cai nay gui RA NGOAI cho khach si. Nen o day khong co
	o ky duyet hai cap, ma co khoi thong tin chuyen khoan that to va dong
	so tien bang chu - hai thu ke toan ben khach can de trinh len sep ho.
	"""
	d = xem_phieu(name)
	qr = d.get("qr") or {}
	esc = frappe.utils.escape_html

	# Xâu phông lấy từ một nơi duy nhất, xem vagabond/phong_chu.py.
	from vagabond.mau_chuan import PHONG
	VIEN = "1px solid #c9c4bd"
	o_th = (
		'style="border:%s;padding:6px 7px;background:#f3f0ec;font-size:10.5px;'
		'font-weight:bold;text-align:center"' % VIEN
	)

	def _td(noi, canh="left", dam=False, khong_ngat=False):
		return (
			'<td style="border:%s;padding:5px 7px;font-size:10.5px;text-align:%s;%s%s">%s</td>'
			% (VIEN, canh, "font-weight:bold;" if dam else "",
			   "white-space:nowrap;" if khong_ngat else "", noi)
		)

	hang = []
	for i, x in enumerate(d.get("dong") or [], 1):
		hang.append(
			"<tr>"
			+ _td(str(i), "center")
			+ _td(_ngay_vn(x.get("ngay")) or "-", "center", khong_ngat=True)
			+ _td(esc(x.get("hoa_don") or "-"), khong_ngat=True)
			+ _td(esc(x.get("so_gtgt") or "-"), "center", khong_ngat=True)
			+ _td(_tien_vn(x.get("so_tien")), "right", dam=True, khong_ngat=True)
			+ "</tr>"
		)
	if not hang:
		hang.append(
			'<tr><td colspan="5" style="border:%s;padding:10px;text-align:center;'
			'font-size:10.5px;color:#777">Phiếu chưa có hoá đơn nào.</td></tr>' % VIEN
		)

	tong = flt(d.get("tong_tien"))
	da_thu = flt(d.get("sepay"))
	con_thieu = max(0.0, tong - da_thu)

	cuoi = (
		'<tr><td colspan="4" style="border:%s;padding:6px 7px;font-size:11px;'
		'text-align:right;font-weight:bold">TỔNG CỘNG</td>'
		'<td style="border:%s;padding:6px 7px;font-size:12px;text-align:right;'
		'white-space:nowrap;font-weight:bold">%s</td></tr>' % (VIEN, VIEN, _tien_vn(tong))
	)
	if da_thu > 0:
		cuoi += (
			'<tr><td colspan="4" style="border:%s;padding:6px 7px;font-size:11px;'
			'text-align:right">Đã nhận</td>'
			'<td style="border:%s;padding:6px 7px;font-size:11px;text-align:right;'
			'white-space:nowrap">%s</td></tr>'
			'<tr><td colspan="4" style="border:%s;padding:6px 7px;font-size:11px;'
			'text-align:right;font-weight:bold">CÒN PHẢI THANH TOÁN</td>'
			'<td style="border:%s;padding:6px 7px;font-size:12px;text-align:right;'
			'white-space:nowrap;font-weight:bold">%s</td></tr>'
			% (VIEN, VIEN, _tien_vn(da_thu), VIEN, VIEN, _tien_vn(con_thieu))
		)

	def _o_tt(nhan, gt, to=False):
		return (
			'<tr><td style="border:none;padding:3px 0;font-size:11px;color:#555;'
			'width:38%%;vertical-align:top">%s</td>'
			'<td style="border:none;padding:3px 0;font-size:%s;font-weight:bold;'
			'vertical-align:top">%s</td></tr>'
			% (nhan, "14px" if to else "11.5px", gt)
		)

	tien_ck = con_thieu if da_thu > 0 else tong
	anh_qr = _qr_data_uri(qr, tien_ck, d.get("ma_phieu") or "")
	o_qr = (
		'<td style="border:none;width:170px;text-align:center;vertical-align:top;'
		'padding-left:12px">'
		'<img src="%s" width="150" height="150" '
		'style="width:150px !important;height:150px !important">'
		'<div style="font-size:9.5px;color:#555;margin-top:4px">Quét mã để chuyển khoản</div>'
		"</td>" % anh_qr
	) if anh_qr else ""

	khoi_ck = (
		'<div style="border:2px solid #1c1a17;padding:12px 14px;margin-top:14px">'
		'<div style="font-size:11px;font-weight:bold;letter-spacing:.5px;'
		'margin-bottom:7px">THÔNG TIN CHUYỂN KHOẢN</div>'
		'<table style="width:100%;border:none;border-collapse:collapse"><tr>'
		'<td style="border:none;vertical-align:top">'
		'<table style="width:100%;border:none;border-collapse:collapse">'
		+ _o_tt("Ngân hàng:", esc(
			TEN_NGAN_HANG_DAY_DU.get(qr.get("bank") or "", qr.get("bank") or "...............")
		))
		+ _o_tt("Số tài khoản:", esc(qr.get("stk") or "..............."), to=True)
		+ _o_tt("Tên tài khoản:", esc(qr.get("ten") or "..............."))
		+ _o_tt("Số tiền:", _tien_vn(tien_ck) + " đ", to=True)
		+ _o_tt("Nội dung chuyển khoản:", esc(d.get("ma_phieu") or ""), to=True)
		+ "</table></td>"
		+ o_qr
		+ "</tr></table>"
		'<div style="font-size:10px;color:#555;margin-top:8px;line-height:1.5">'
		"Quý khách vui lòng thêm dòng mã nội bộ của The Vagabond vào nội dung "
		"chuyển khoản để đối soát công nợ được thuận tiện.</div></div>"
	)

	ben_nhan = (
		'<table style="width:100%;border:none;border-collapse:collapse">'
		+ _o_tt("Kính gửi:", esc(d.get("ten_khach") or d.get("khach") or ""), to=True)
		# Ben Next, ma khach hang chinh la ten khach nen hai dong se trung
		# nhau. Chi bay dong ma khi no that su khac ten.
		+ (
			_o_tt("Mã khách hàng:", esc(d.get("khach") or ""))
			if (d.get("khach") or "") != (d.get("ten_khach") or "")
			else ""
		)
		+ _o_tt("Số hoá đơn trong phiếu:", str(len(d.get("dong") or [])))
		+ _o_tt("Hạn thanh toán:", _ngay_vn(d.get("han_qr")) or "...............")
		+ "</table>"
	)

	ghi_chu = ""
	if (d.get("ghi_chu") or "").strip():
		ghi_chu = (
			'<div style="margin-top:12px;font-size:11px"><b>Ghi chú:</b> %s</div>'
			% esc(d["ghi_chu"])
		)

	return (
		'<div style="font-family:%s;color:#1c1a17;font-size:12px;line-height:1.45">'
		'<table style="width:100%%;border:none;border-collapse:collapse"><tr>'
		'<td style="border:none;width:45%%;vertical-align:middle">'
		'<img src="/files/vagabond_logo_print.png" width="150" height="62" '
		'style="width:150px !important;height:62px !important;object-fit:contain">'
		"</td>"
		'<td style="border:none;text-align:right;vertical-align:middle;font-size:9.5px;'
		'color:#444;line-height:1.5">'
		'<b style="font-size:10.5px;color:#1c1a17">CÔNG TY TNHH PATISSERIE VAGABOND</b><br>'
		"MST: 0318561568<br>"
		"9 Trần Cao Vân, Phường Sài Gòn, TP.HCM<br>"
		"www.thevagabondpatisserie.com"
		"</td></tr></table>"
		'<div style="text-align:center;margin:14px 0 2px">'
		'<div style="font-size:19px;font-weight:bold;letter-spacing:1px">'
		"PHIẾU ĐỀ NGHỊ THANH TOÁN</div>"
		'<div style="font-size:11px;color:#555;margin-top:3px">'
		"Số: <b>%s</b> &nbsp;·&nbsp; Ngày %s</div></div>"
		"%s"
		'<table style="width:100%%;border-collapse:collapse;margin-top:12px">'
		"<tr><th %s>STT</th><th %s>Ngày hoá đơn</th><th %s>Số hoá đơn</th>"
		"<th %s>Số hoá đơn GTGT</th><th %s>Số tiền</th></tr>%s%s</table>"
		'<div style="margin-top:8px;font-size:11px">Số tiền bằng chữ: '
		"<i>%s</i></div>"
		"%s%s"
		'<table style="width:100%%;border:none;border-collapse:collapse;margin-top:26px">'
		'<tr><td style="border:none;width:50%%;text-align:center;font-size:11px">'
		'<b>ĐẠI DIỆN BÊN MUA</b><div style="font-size:10px;color:#666;margin-top:2px">'
		"(Ký, ghi rõ họ tên)</div>"
		'<div style="height:58px"></div></td>'
		'<td style="border:none;width:50%%;text-align:center;font-size:11px">'
		"<b>THE VAGABOND PÂTISSERIE</b>"
		'<div style="font-size:10px;color:#666;margin-top:2px">(Ký, ghi rõ họ tên)</div>'
		'<div style="height:58px"></div>'
		'<div style="font-size:10.5px">%s</div></td></tr></table>'
		'<div style="margin-top:14px;font-size:9.5px;color:#777;text-align:center">'
		"Phiếu này được lập từ hệ thống The Vagabond Pâtisserie. "
		"Mọi thắc mắc xin liên hệ bộ phận kinh doanh.</div>"
		"</div>"
	) % (
		PHONG,
		esc(d.get("ma_phieu") or ""), _ngay_vn(d.get("ngay_tao")),
		ben_nhan,
		o_th, o_th, o_th, o_th, o_th,
		"".join(hang), cuoi,
		_chu_so_tien(con_thieu if da_thu > 0 else tong),
		khoi_ck, ghi_chu,
		esc(frappe.db.get_value("User", d.get("nguoi_tao") or frappe.session.user, "full_name") or ""),
	)


@frappe.whitelist()
def xem_truoc_phieu(name):
	"""HTML to phieu de xem truoc tren app truoc khi tai PDF."""
	_kiem_quyen()
	return {"html": _phieu_html(name)}


@frappe.whitelist()
def xuat_phieu(name):
	"""To phieu yeu cau thanh toan ra PDF A4 doc de gui khach."""
	_kiem_quyen()
	from frappe.utils.pdf import get_pdf

	d = xem_phieu(name)
	# Đi qua khung chuẩn: nó chép bộ phông tiếng Việt vào máy chủ rồi ép
	# phông cho cả tờ. Xem vagabond/phong_chu.py.
	from vagabond import mau_chuan

	khung = mau_chuan.khung_trang(_phieu_html(name), name, le="12mm 10mm")
	noi_dung = get_pdf(khung, options={"page-size": "A4", "orientation": "Portrait"})
	import base64

	return {
		"ten_file": "Phieu-de-nghi-thanh-toan-%s.pdf" % (d.get("ma_phieu") or name),
		"b64": base64.b64encode(noi_dung).decode(),
		"kieu": "application/pdf",
	}


# ------------------------------------- Thu bao khach da chuyen tien thanh cong


def _email_khach(khach):
	"""Email de gui thu bao. Uu tien contact chinh, sau do o email tren khach."""
	if not khach:
		return ""
	ct = frappe.db.sql(
		"""select c.email_id from `tabContact` c
		inner join `tabDynamic Link` l on l.parent = c.name
		where l.link_doctype = 'Customer' and l.link_name = %s
			and ifnull(c.email_id, '') != ''
		order by c.is_primary_contact desc, c.modified desc limit 1""",
		(khach,),
	)
	if ct and ct[0][0]:
		return ct[0][0]
	return frappe.db.get_value("Customer", khach, "email_id") or ""


def _thu_da_nhan_html(doc, ds_dong):
	"""Thu bao da nhan tien, giong giong to phieu de khach nhan ra ngay."""
	# Xâu phông thư điện tử, khai một nơi. Xem vagabond/mau_chuan.py.
	from vagabond import mau_chuan

	esc = frappe.utils.escape_html
	hang = "".join(
		'<tr><td style="padding:6px 8px;border-bottom:1px solid #eee;font-size:13px">%s</td>'
		'<td style="padding:6px 8px;border-bottom:1px solid #eee;font-size:13px;'
		'text-align:right;white-space:nowrap">%s đ</td></tr>'
		% (esc(x.get("hoa_don") or ""), _tien_vn(x.get("so_tien")))
		for x in ds_dong
	)
	return (
		'<div style="margin:0;padding:0;background:#F2FAFC">'
		'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
		'border="0"><tr><td align="center" style="padding:20px 8px">'
		'<table role="presentation" width="600" cellpadding="0" cellspacing="0" '
		'border="0" style="width:600px;max-width:600px;background:#fff;'
		'border:1px solid #e4e7ec">'
		'<tr><td style="padding:26px 30px 6px;font-family:' + mau_chuan.PHONG_THU + '">'
		'<div style="font-size:20px;font-weight:bold;color:#1c1a17">'
		"Đã nhận được thanh toán</div>"
		'<div style="font-size:14px;color:#475467;line-height:1.7;margin-top:12px">'
		"Kính gửi <b>%s</b>,<br><br>"
		"The Vagabond Pâtisserie xác nhận đã nhận được khoản thanh toán "
		'<b style="color:#0f766e">%s đ</b> theo phiếu đề nghị thanh toán '
		"<b>%s</b>. Công nợ của quý khách cho các hoá đơn dưới đây đã được "
		"tất toán."
		"</div>"
		'<table style="width:100%%;border-collapse:collapse;margin-top:18px">'
		'<tr><td style="padding:6px 8px;border-bottom:2px solid #1c1a17;'
		'font-size:12px;font-weight:bold">Số hoá đơn</td>'
		'<td style="padding:6px 8px;border-bottom:2px solid #1c1a17;font-size:12px;'
		'font-weight:bold;text-align:right">Số tiền</td></tr>'
		"%s"
		'<tr><td style="padding:9px 8px;font-size:14px;font-weight:bold">Tổng cộng</td>'
		'<td style="padding:9px 8px;font-size:15px;font-weight:bold;text-align:right;'
		'white-space:nowrap">%s đ</td></tr></table>'
		'<div style="font-size:13.5px;color:#475467;line-height:1.7;margin-top:20px">'
		"Cảm ơn quý khách đã tin tưởng và đồng hành cùng The Vagabond Pâtisserie. "
		"Nếu cần hoá đơn hoặc chứng từ gì thêm, quý khách cứ trả lời thẳng thư này, "
		"bộ phận kinh doanh sẽ hỗ trợ ngay."
		"</div>"
		'<div style="font-size:13.5px;color:#475467;margin-top:22px;line-height:1.7">'
		"Trân trọng,<br><b>The Vagabond Pâtisserie</b>"
		'<div style="font-size:12px;color:#98a2b3;margin-top:4px">'
		"9 Trần Cao Vân, Phường Sài Gòn, TP.HCM<br>"
		"www.thevagabondpatisserie.com</div></div>"
		"</td></tr></table></td></tr></table></div>"
	) % (
		esc(doc.ten_khach or doc.khach or "Quý khách"),
		_tien_vn(doc.da_thu),
		esc(doc.ma_phieu or ""),
		hang,
		_tien_vn(doc.tong_tien),
	)


def _gui_thu_da_nhan(doc, buoc_gui=False):
	"""Gui thu bao da nhan tien. Tra ve (da_gui, ly_do)."""
	if doc.get("email_da_gui") and not buoc_gui:
		return False, "đã gửi rồi"
	email = _email_khach(doc.khach)
	if not email:
		return False, "khách chưa có email trên hệ"
	ds_dong = [
		{"hoa_don": x.hoa_don, "so_tien": flt(x.so_tien)} for x in (doc.dong or [])
	]
	frappe.sendmail(
		recipients=email,
		subject="The Vagabond Pâtisserie - đã nhận thanh toán %s" % (doc.ma_phieu or ""),
		message=_thu_da_nhan_html(doc, ds_dong),
		delayed=False,
		retry=3,
	)
	try:
		doc.db_set("email_da_gui", 1, update_modified=False)
		doc.db_set("email_gui_toi", email, update_modified=False)
	except Exception:
		pass
	doc.add_comment("Comment", "Đã gửi thư báo nhận tiền tới %s" % email)
	return True, email


@frappe.whitelist()
def xem_truoc_thu(name):
	"""Xem truoc thu bao da nhan tien, khong gui cho ai."""
	_kiem_quyen()
	doc = frappe.get_doc("Vagabond Cong No", name)
	ds_dong = [{"hoa_don": x.hoa_don, "so_tien": flt(x.so_tien)} for x in (doc.dong or [])]
	return {
		"html": _thu_da_nhan_html(doc, ds_dong),
		"email": _email_khach(doc.khach),
	}


@frappe.whitelist()
def gui_thu_da_nhan(name):
	"""Gui tay thu bao da nhan tien, dung khi may gui hut hoac khach bao chua nhan."""
	_kiem_quyen()
	doc = frappe.get_doc("Vagabond Cong No", name)
	da, ly_do = _gui_thu_da_nhan(doc, buoc_gui=True)
	if not da:
		frappe.throw("Chưa gửi được: %s." % ly_do)
	return {"ok": 1, "loi_nhan": "Đã gửi thư báo tới %s." % ly_do}


# --------------------------------- Doi chieu SePay bang tay cho phieu cong no


@frappe.whitelist()
def tim_giao_dich_thu(tu_khoa="", so_ngay=120, so_tien=None):
	"""Tra cuu giao dich TIEN VE de ke toan tu khop tay vao phieu.

	Anh Viet 14/08/2026: *"Anh nghĩ là thêm phần đối chiếu danh sách sepay
	bằng tay ở đoạn này nữa lỡ đâu máy đối chiếu không được."*

	May doi chieu theo NOI DUNG chuyen khoan. Khach si chuyen tu app ngan
	hang cua cong ty ho, ke toan ben do hay go noi dung theo he thong cua
	ho chu khong theo ma minh dat - luc do may chiu. Man nay la duong lui.
	"""
	_kiem_quyen()
	rows = frappe.get_all(
		"Bank Transaction",
		filters={
			"date": [">=", add_days(nowdate(), -int(so_ngay or 120))],
			"docstatus": ["<", 2],
			"deposit": [">", 0],
		},
		fields=["name", "date", "description", "deposit", "bank_account", "reference_number"],
		order_by="date desc, creation desc",
		limit_page_length=0,
	)
	k = (tu_khoa or "").strip().lower()
	muc = flt(so_tien) if so_tien else 0.0
	ra = []
	for r in rows:
		tien = flt(r.get("deposit"))
		if muc and abs(tien - muc) > 1:
			continue
		mo_ta = r.get("description") or ""
		ma = (r.get("reference_number") or r.get("name") or "").strip()
		if k and k not in mo_ta.lower() and k not in ma.lower():
			continue
		ra.append({
			"ma": ma or r["name"],
			"ngay": str(r["date"] or ""),
			"noi_dung": mo_ta[:300],
			"tien": tien,
			"tai_khoan": r.get("bank_account") or "",
		})
	return {"rows": ra[:300], "tong": len(ra), "con_nua": max(0, len(ra) - 300)}


@frappe.whitelist()
def khop_tay(name, so_tien, ma_giao_dich="", ghi_chu=""):
	"""Ghi nhan tay so tien da nhan cho mot phieu.

	Dung khi SePay khong tu khop duoc. KHONG dung vao bang Bank Transaction,
	chi ghi len phieu va de lai dau vet ai khop, luc nao, giao dich nao.
	"""
	_kiem_quyen()
	so_tien = flt(so_tien)
	if so_tien <= 0:
		frappe.throw("Số tiền khớp tay phải lớn hơn 0.")
	doc = frappe.get_doc("Vagabond Cong No", name)
	if doc.trang_thai == "Huy":
		frappe.throw("Phiếu đã huỷ, không khớp được.")
	if so_tien > flt(doc.tong_tien) + 1:
		frappe.throw(
			"Phiếu chỉ %s đ mà khớp %s đ. Xem lại số tiền."
			% (_tien_vn(doc.tong_tien), _tien_vn(so_tien))
		)
	truoc = doc.trang_thai
	# Ma giao dich go tay cung phai qua cua chiem dung. Truoc day no chi di
	# vao mot dong nhat ky, nen hai ke toan go cung mot ma len hai phieu thi
	# khong ai bao gi, va khong cau truy van nao tim ra duoc.
	gd = _giu_gd(doc, [ma_giao_dich] if str(ma_giao_dich or "").strip() else [])
	doc.da_thu = so_tien
	doc.trang_thai = "Da thu du" if so_tien >= flt(doc.tong_tien) - 1 else "Thu thieu"
	if gd:
		doc.ma_gd = gd
		doc.nguoi_khop_tay = frappe.session.user
		doc.ngay_khop_tay = frappe.utils.now_datetime()
	doc.save(ignore_permissions=True)
	doc.add_comment(
		"Comment",
		"Khớp tay %s đ%s, người làm %s%s"
		% (
			_tien_vn(so_tien),
			" (giao dịch %s)" % ma_giao_dich if ma_giao_dich else "",
			frappe.session.user,
			". Ghi chú: %s" % ghi_chu if (ghi_chu or "").strip() else "",
		),
	)
	frappe.db.commit()
	if doc.trang_thai == "Da thu du" and truoc != "Da thu du":
		try:
			_gui_thu_da_nhan(doc)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "cong_no: gui thu sau khop tay loi")
	return {
		"ok": 1,
		"loi_nhan": "Đã ghi nhận %s đ cho phiếu %s.%s"
		% (
			_tien_vn(so_tien), doc.ma_phieu,
			" Công nợ đã sạch." if doc.trang_thai == "Da thu du" else "",
		),
	}

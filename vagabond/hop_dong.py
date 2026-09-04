"""Phan he hop dong ban hang: catering, event, teabreak, banh thiet ke, B2B.

Man hinh o app /bep goi cac endpoint nay. Mot hop dong gom nhieu hoa don
(Sales Invoice) gan qua truong custom_hop_dong; tien do thu tien tinh tu
grand_total va outstanding_amount cua cac hoa don da submit.
"""

import frappe
from frappe.utils import cint, flt, getdate, nowdate

# Anh Viet 14/08/2026: *"cấp quyền truy cập cho Loan Anh, thu mua và kế toán"*.
# Loan Anh dang co vai Sales User nen vao duoc ngay. Them thu mua va ke toan
# truong vao day cho du bo.
QUYEN = {
	"System Manager",
	"Sales User",
	"Sales Manager",
	"Accounts User",
	"Accounts Manager",
	"Purchase User",
	"Purchase Manager",
	"Bộ phận đặt hàng",
}


def _quyen():
	if not QUYEN & set(frappe.get_roles()):
		frappe.throw("Không có quyền xem hợp đồng")


def _tong(name):
	"""Tong hop hoa don cua mot hop dong."""
	r = frappe.db.sql(
		"""select count(name), coalesce(sum(grand_total), 0), coalesce(sum(outstanding_amount), 0)
		from `tabSales Invoice` where custom_hop_dong = %s and docstatus = 1""",
		name,
	)[0]
	so_nhap = frappe.db.count(
		"Sales Invoice", {"custom_hop_dong": name, "docstatus": 0, "vgb_huy": 0}
	)
	da_xuat = flt(r[1])
	con_no = flt(r[2])
	return {
		"so_hd_chot": r[0],
		"so_hd_nhap": so_nhap,
		"da_xuat": da_xuat,
		"da_thu": da_xuat - con_no,
		"con_no": con_no,
	}


@frappe.whitelist()
def danh_sach(trang_thai=None):
	_quyen()
	loc = {}
	if trang_thai:
		loc["trang_thai"] = trang_thai
	ds = frappe.get_all(
		"Hop Dong Ban Hang",
		filters=loc,
		fields=[
			"name", "ten", "so_hop_dong", "loai", "trang_thai", "khach_hang",
			"ngay_su_kien", "gia_tri",
			# Ba o de man hinh bay chip "con thieu gi". Doc san o day chu
			# khong hoi lai tung dong: hai muoi hop dong la hai muoi luot
			# goi mang, va man danh sach thi mo lien tuc ca ngay.
			"nguoi_ky_a", "nguoi_ky_b", "tep_hop_dong_chot",
		],
		order_by="modified desc",
		limit_page_length=200,
	)
	hom_nay = getdate(nowdate())
	for hd in ds:
		hd.update(_tong(hd["name"]))
		hd["nhan"] = NHAN_TT.get(hd["trang_thai"], hd["trang_thai"])
		hd["co_nguoi_ky"] = 1 if (hd.get("nguoi_ky_a") and hd.get("nguoi_ky_b")) else 0
		hd["co_ban_chot"] = 1 if (hd.get("tep_hop_dong_chot") or "").strip() else 0
		hd["con_ngay"] = _con_ngay(hd.get("ngay_su_kien"), hom_nay)
	return {"rows": ds, "dem": dem_chip(ds), "nhan": NHAN_TT}


# Nhan tieng Viet cua trang thai hop dong. De o day chu khong o man hinh
# (QT-19): man tu dich la hai noi cung giu mot bang chu, va chung se lech
# nhau vao mot ngay khong ai doan truoc.
NHAN_TT = {
	"Nhap": "Nháp",
	"Da gui khach": "Đã gửi khách",
	"Dang thuong thao": "Đang thương thảo",
	"Dang thuc hien": "Đang thực hiện",
	"Hoan tat": "Hoàn tất",
	"Da thanh ly": "Đã thanh lý",
	"Huy": "Huỷ",
}

# Trang thai coi la con song, tuc con phai lam gi do. Chip viec ton chi
# dem trong nhung to nay: mot hop dong da thanh ly ma chua co nguoi ky
# thi khong con ai di ky nua.
TT_CON_SONG = ("Nhap", "Da gui khach", "Dang thuong thao", "Dang thuc hien")

# Su kien con bao nhieu ngay thi coi la sap toi.
SAP_TOI = 7


def _con_ngay(ngay_su_kien, hom_nay):
	"""So ngay tu hom nay toi ngay su kien. None neu chua khai ngay."""
	if not ngay_su_kien:
		return None
	try:
		return (getdate(ngay_su_kien) - hom_nay).days
	except Exception:
		return None


def dem_chip(rows):
	"""Dem cho tung chip loc tren man danh sach. THUAN.

	Nam chip viec ton, dung so lieu da co san tren tung dong chu khong hoi
	them co so du lieu. Chip nao dem ra 0 thi man hinh tu an di: bay mot
	hang chip rong la bat sales doc mot dong khong noi gi.
	"""
	ra = {"tat_ca": len(rows or [])}
	for r in rows or []:
		tt = str((r or {}).get("trang_thai") or "")
		ra[tt] = ra.get(tt, 0) + 1
	song = [r for r in (rows or []) if str(r.get("trang_thai") or "") in TT_CON_SONG]
	ra["con_no"] = len([r for r in song if float(r.get("con_no") or 0) > 0])
	ra["chua_hoa_don"] = len([
		r for r in song
		if not (int(r.get("so_hd_chot") or 0) + int(r.get("so_hd_nhap") or 0))
	])
	ra["sap_toi"] = len([
		r for r in song
		if r.get("con_ngay") is not None and 0 <= int(r["con_ngay"]) <= SAP_TOI
	])
	ra["chua_nguoi_ky"] = len([r for r in song if not int(r.get("co_nguoi_ky") or 0)])
	ra["chua_ban_chot"] = len([r for r in song if not int(r.get("co_ban_chot") or 0)])
	return ra


@frappe.whitelist()
def chi_tiet(name):
	_quyen()
	doc = frappe.get_doc("Hop Dong Ban Hang", name)
	hoa_don = frappe.get_all(
		"Sales Invoice",
		filters={"custom_hop_dong": name, "docstatus": ["<", 2], "vgb_huy": 0},
		fields=["name", "posting_date", "grand_total", "outstanding_amount", "docstatus", "customer_name"],
		order_by="posting_date desc",
		limit_page_length=100,
	)
	kq = {
		"hop_dong": {
			"name": doc.name,
			"ten": doc.ten,
			"so_hop_dong": doc.so_hop_dong,
			"loai": doc.loai,
			"trang_thai": doc.trang_thai,
			"khach_hang": doc.khach_hang,
			"ngay_ky": str(doc.ngay_ky or ""),
			"ngay_su_kien": str(doc.ngay_su_kien or ""),
			"gia_tri": flt(doc.gia_tri),
			"mo_ta": doc.mo_ta or "",
			"ghi_chu": doc.ghi_chu or "",
			# Khoi phap ly (anh Viet 18/08/2026). Man Chi tiet hop dong dua
			# vao doc "bao_gia" de biet co bay ba nut Xem truoc, Xuat PDF,
			# Gui Email hay khong: hop dong go tay khong co goc bao gia thi
			# khong dung duoc to phap ly, va khong bay nut ra roi de nguoi
			# ta bam vao chi de nhan mot cau bao loi.
			"bao_gia": doc.get("bao_gia") or "",
			"ten_khach": doc.get("ten_khach") or "",
			"ma_so_thue": doc.get("ma_so_thue") or "",
			"dia_chi": doc.get("dia_chi") or "",
			"dai_dien": doc.get("dai_dien") or "",
			"chuc_vu": doc.get("chuc_vu") or "",
			"dien_thoai": doc.get("dien_thoai") or "",
			"email": doc.get("email") or "",
			"dat_coc_pt": flt(doc.get("dat_coc_pt")),
			"dat_coc_tien": flt(doc.get("dat_coc_tien")),
			"dia_diem_giao": doc.get("dia_diem_giao") or "",
			"thoi_gian_giao": doc.get("thoi_gian_giao") or "",
			# Nguoi ky va ban scan phu luc (anh Viet 18/08/2026). Man chi
			# tiet phai doc duoc de biet con thieu gi truoc khi gui khach.
			"nguoi_ky_a": doc.get("nguoi_ky_a") or "",
			"chuc_vu_ky_a": doc.get("chuc_vu_ky_a") or "",
			"dt_ky_a": doc.get("dt_ky_a") or "",
			"email_ky_a": doc.get("email_ky_a") or "",
			"nguoi_ky_b": doc.get("nguoi_ky_b") or "",
			"chuc_vu_ky_b": doc.get("chuc_vu_ky_b") or "",
			"dt_ky_b": doc.get("dt_ky_b") or "",
			"email_ky_b": doc.get("email_ky_b") or "",
			"phu_luc_scan": doc.get("phu_luc_scan") or "",
			# --- Thuong thao va dieu chinh (anh Viet 21/08/2026, bai cua
			# Loan Anh ben Sales). Man chi tiet phai doc duoc ba thu: dang
			# thuong thao hay khong, ly do lan nay, va co ban chot tai len
			# chua - vi ca ba deu doi hinh dang cua khoi nut ben duoi. ---
			"ly_do_thuong_thao": doc.get("ly_do_thuong_thao") or "",
			"nguoi_mo_thuong_thao": doc.get("nguoi_mo_thuong_thao") or "",
			"ngay_mo_thuong_thao": str(doc.get("ngay_mo_thuong_thao") or ""),
			"tep_hop_dong_chot": doc.get("tep_hop_dong_chot") or "",
			"tep_chot_ten": doc.get("tep_chot_ten") or "",
			"tep_chot_nguoi": doc.get("tep_chot_nguoi") or "",
			"tep_chot_luc": str(doc.get("tep_chot_luc") or ""),
			"tep_chot_ghi_chu": doc.get("tep_chot_ghi_chu") or "",
			"ngay_dot1": int(doc.get("ngay_dot1") or 0),
			"ngay_dot2": int(doc.get("ngay_dot2") or 0),
		},
		"hoa_don": hoa_don,
	}
	kq.update(_tong(name))
	# So phien ban da chot, de man hien nhan "Hop dong v3" ngay tren dau.
	try:
		kq["so_phien_ban"] = frappe.db.count("Hop Dong Phien Ban", {"hop_dong": name})
	except Exception:
		kq["so_phien_ban"] = 0
	return kq


@frappe.whitelist()
def tao(ten, so_hop_dong=None, loai=None, khach_hang=None, ngay_ky=None, ngay_su_kien=None, gia_tri=0, mo_ta=None, ghi_chu=None):
	_quyen()
	doc = frappe.get_doc(
		{
			"doctype": "Hop Dong Ban Hang",
			"ten": ten,
			"so_hop_dong": so_hop_dong,
			"loai": loai or "Event - Catering",
			"khach_hang": khach_hang or None,
			"ngay_ky": ngay_ky or None,
			"ngay_su_kien": ngay_su_kien or None,
			"gia_tri": flt(gia_tri),
			"mo_ta": mo_ta,
			"ghi_chu": ghi_chu,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


@frappe.whitelist()
def doi_trang_thai(name, trang_thai):
	"""Doi trang thai bang tay tren man chi tiet.

	CO Y khong cho nhay vao hay ra khoi "Dang thuong thao" bang duong nay.
	Vao thuong thao thi phai qua nut Dieu chinh, vi duong do bat ghi ly do
	va chup lai ban goc; ra thi phai qua Chot dieu chinh hoac Dong thuong
	thao, vi hai duong do sinh phien ban va tra ve dung trang thai cu.

	Bo hang rao nay di la mo mot duong vong: bam doi trang thai tay la thoat
	khoi thuong thao ma khong de lai mot dong nhat ky nao - dung cai anh
	Viet dat ra luong nay de chan.
	"""
	_quyen()
	from vagabond.hop_dong_dieu_chinh import TT_THUONG_THAO

	hop_le = {"Nháp", "Đang thực hiện", "Hoàn tất", "Đã thanh lý", "Huỷ"}
	if trang_thai not in hop_le:
		frappe.throw("Trạng thái không hợp lệ")
	dang = frappe.db.get_value("Hop Dong Ban Hang", name, "trang_thai")
	if dang == TT_THUONG_THAO:
		frappe.throw(
			"Hợp đồng đang thương thảo nên không đổi trạng thái tay được. Bấm "
			"Chốt điều chỉnh để ghi lại bản mới, hoặc Đóng thương thảo nếu "
			"khách thôi không sửa nữa."
		)
	frappe.db.set_value("Hop Dong Ban Hang", name, "trang_thai", trang_thai)
	return trang_thai


@frappe.whitelist()
def sua_nguoi_ky(name, nguoi_ky_a=None, chuc_vu_ky_a=None, dt_ky_a=None, email_ky_a=None,
                 nguoi_ky_b=None, chuc_vu_ky_b=None, dt_ky_b=None, email_ky_b=None):
	"""Sua bon o cua khoi chu ky sau khi da tao hop dong.

	Anh Viet 18/08/2026: *"Khoi chu ky cuoi hop dong tuyet doi khong duoc
	ghi Ms./Mr. va khong duoc lay mac dinh ten cua ban Sales"*. Man tao hop
	dong da hoi bon o nay, nhung go nham thi phai sua duoc, khong bat lam
	lai ca to.

	Bo xung ho ngay tai day chu khong tin vao man hinh: cung mot ham voi
	luc tao thi go kieu gi cung ra mot ket qua.
	"""
	_quyen()
	from vagabond.hop_dong_pdf import _bo_xung_ho

	frappe.db.set_value("Hop Dong Ban Hang", name, {
		"nguoi_ky_a": _bo_xung_ho(nguoi_ky_a),
		"chuc_vu_ky_a": (chuc_vu_ky_a or "").strip(),
		"dt_ky_a": (dt_ky_a or "").strip(),
		"email_ky_a": (email_ky_a or "").strip(),
		"nguoi_ky_b": _bo_xung_ho(nguoi_ky_b),
		"chuc_vu_ky_b": (chuc_vu_ky_b or "").strip(),
		"dt_ky_b": (dt_ky_b or "").strip(),
		"email_ky_b": (email_ky_b or "").strip(),
	})
	return True


@frappe.whitelist()
def go_phu_luc_scan(name):
	"""Go ban scan phu luc ra khoi hop dong.

	QT-20: khong xoa han tep, chi bo tro tren hop dong. Tep van nam trong
	kho tep cua he thong, can thi tim lai duoc.
	"""
	_quyen()
	frappe.db.set_value("Hop Dong Ban Hang", name, "phu_luc_scan", "")
	return True


@frappe.whitelist()
def gan_hoa_don(hop_dong, si_name, go=0):
	"""Gan (hoac go) mot hoa don vao hop dong.

	Dung db_set de gan duoc ca hoa don da submit: `custom_hop_dong` la
	truong phu, khong dung cham vao so tien, thue hay du no cua to.

	CHAN GAN TRUNG va GHI VET (anh Viet 04/09/2026). Truoc ban nay ham chi
	co mot dong set_value: gan de len hop dong cu ma khong hoi mot cau,
	nen mot to hoa don co the lang le roi khoi hop dong A sang hop dong B
	va tien do thu tien cua A tut xuong ma khong ai biet vi sao.
	"""
	_quyen()
	if not frappe.db.exists("Sales Invoice", si_name):
		frappe.throw("Không có hoá đơn %s" % si_name)
	go = int(go or 0)
	dang_gan = frappe.db.get_value("Sales Invoice", si_name, "custom_hop_dong")
	if go:
		if not dang_gan:
			return si_name
		frappe.db.set_value("Sales Invoice", si_name, "custom_hop_dong", None)
		_ghi_vet_gan(si_name, dang_gan, "gỡ khỏi")
		return si_name
	if not frappe.db.exists("Hop Dong Ban Hang", hop_dong):
		frappe.throw("Không có hợp đồng %s" % hop_dong)
	if dang_gan == hop_dong:
		# Bam lai lan nua khong phai loi, chi la khong co gi de lam.
		return si_name
	if dang_gan:
		frappe.throw(
			"Hoá đơn %s đang gắn ở hợp đồng %s rồi. Mở hợp đồng đó gỡ ra "
			"trước, rồi hãy gắn sang hợp đồng này - một hoá đơn chỉ thuộc "
			"về một hợp đồng, để tiến độ thu tiền của hai bên không cùng "
			"đếm một khoản." % (si_name, dang_gan)
		)
	frappe.db.set_value("Sales Invoice", si_name, "custom_hop_dong", hop_dong)
	_ghi_vet_gan(si_name, hop_dong, "gắn vào")
	return si_name


def _ghi_vet_gan(si_name, hop_dong, viec):
	"""Ai gan, gan vao dau, luc nao. Ghi vao ca hai phia."""
	cau = "Hoá đơn %s %s hợp đồng %s. Người làm %s." % (
		si_name, viec, hop_dong, frappe.session.user)
	for dt, ten in (("Sales Invoice", si_name), ("Hop Dong Ban Hang", hop_dong)):
		try:
			frappe.get_doc(dt, ten).add_comment("Comment", cau)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "hop_dong: ghi vet gan hoa don")


@frappe.whitelist()
def hoa_don_chua_gan(khach_hang=None, tu_khoa="", ma_so_thue="", so_ngay=180):
	"""Hoa don chua gan hop dong, de tick gan.

	VI SAO PHAI VIET LAI (anh Viet 04/09/2026)
	--------------------------------------------------------------------
	Loan Anh bam "Gan hoa don vao hop dong" ma khong tim thay to vua tao.
	Do tren du lieu that, hai cai chan cong lai:

	  1. LOC CUNG THEO `customer`. Hop dong HDBH-2026-1838 mang khach hang
	     "CONG TY TRACH NHIEM HUU HAN DENTSU VIET NAM", con hoa don
	     HDB-26-09-00508 mang customer "KL042003" (Ms.Linh, khach le dat
	     hang) va chi xuat VAT cho Dentsu. Loc theo customer la loai thang
	     to do ra, du no dung la to can gan.
	  2. CAT CON 60 TO. Ngay 04/09 co 18.711 hoa don chua gan hop dong
	     trong 90 ngay. May lay 60 to moi nhat, va o tim trong bang chon
	     chi tim trong 60 to DA TAI. Ke ca bo cai chan thu nhat thi van
	     khong bao gio tim ra.

	Ca hai deu im lang: man chi bao "khong co hoa don nao chua gan", khong
	he noi la da cat bot.

	Nay: khong loc cung theo khach nua ma XEP uu tien, va o tim day xuong
	may chu - tim duoc theo so hoa don, ten khach, ten va ma so thue tren
	hoa don VAT. Bi cat thi noi ro con bao nhieu to nua.
	"""
	_quyen()
	tu_khoa = (tu_khoa or "").strip()
	loc = {
		"custom_hop_dong": ["in", ["", None]],
		"docstatus": ["<", 2],
		# Hoa don da huy thi khong gan vao hop dong duoc: gan roi la so tien
		# hop dong sai ma khong ai nhin ra.
		"vgb_huy": 0,
		"posting_date": [">=", frappe.utils.add_days(frappe.utils.nowdate(), -cint(so_ngay or 180))],
	}
	TRUONG = ["name", "posting_date", "customer", "customer_name", "grand_total",
		"docstatus", "vgb_xhd_ten", "vgb_xhd_mst"]
	GIOI_HAN = 80

	if tu_khoa:
		# Moi o mot cau truy van roi gom lai: OR nhieu cot khong di qua duoc
		# bo loc dang dict cua Frappe, ma viet SQL tay thi mat luon hang rao
		# quyen cua get_all.
		gom, thay = [], set()
		for cot in ("name", "customer_name", "vgb_xhd_ten", "vgb_xhd_mst", "vgb_ma_tham_chieu"):
			l = dict(loc)
			l[cot] = ["like", "%" + tu_khoa + "%"]
			try:
				ds = frappe.get_all("Sales Invoice", filters=l, fields=TRUONG,
					order_by="posting_date desc", limit_page_length=GIOI_HAN)
			except Exception:
				continue
			for r in ds:
				if r["name"] not in thay:
					thay.add(r["name"])
					gom.append(r)
		rows = gom
	else:
		rows = frappe.get_all("Sales Invoice", filters=loc, fields=TRUONG,
			order_by="posting_date desc", limit_page_length=400)

	mst = (ma_so_thue or "").strip().split("-")[0]
	kh = (khach_hang or "").strip()

	def _uu_tien(r):
		# 0 la len dau. To cua dung khach, hoac to xuat VAT dung ma so thue
		# cua hop dong, gan nhu chac chan la to can tim.
		if kh and r.get("customer") == kh:
			return 0
		if mst and (r.get("vgb_xhd_mst") or "").split("-")[0] == mst:
			return 0
		if kh and kh.lower() in ((r.get("vgb_xhd_ten") or "").lower()):
			return 1
		return 2

	rows.sort(key=lambda r: (_uu_tien(r), str(r.get("posting_date") or "")[::-1]), reverse=False)
	con = max(0, len(rows) - GIOI_HAN)
	ra = rows[:GIOI_HAN]
	for r in ra:
		r["hop_ly"] = _uu_tien(r) < 2
	return {"hoa_don": ra, "con_lai": con, "tu_khoa": tu_khoa}

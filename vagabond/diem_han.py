"""Diem het han theo chu ky, va ha hang tung bac.

Anh Viet chot 16/08/2026, sau khi thay quy diem cu tu Fabi len toi 472
trieu diem: phai co van de thoat, khong thi quy diem chi phinh mai.

Hai viec o day khac han nhau ve muc rui ro
------------------------------------------
Ha hang thi go lai duoc: gan lai hang cho khach la xong. HET HAN DIEM THI
KHONG: mot dem chay nham la ca chuc ngan khach mat sach diem, va khong co
cach nao biet ai dang le duoc giu bao nhieu neu khong doc lai tung but.

Nen ham het han o day:
  - MAC DINH CHAY THU. Phai truyen chay_that=1 moi ghi.
  - Chi chay khi Cai dat bat han. Mac dinh la TAT.
  - Ghi but am loai "Het han", KHONG sua but cu (QT-20).
  - Moi khach moi chu ky chi mot but. Chay lai khong tru hai lan.
  - Mot tran cung: mot dem khong duoc dot qua GIOI_HAN_MOT_DEM khach. Vuot
    thi dung lai va gui thu bao, chu khong am tham chay tiep.

Ba cach tinh han, chon trong Cai dat
------------------------------------
"Cuon chieu" (nen dung): moi but diem song han_thang thang ke tu ngay
tich. Cong bang nhat, va khong co canh khach tich diem ngay 30/12 roi mat
sach vao 31/12.

"Cuoi nam": dung ngay chot co dinh hang nam, xoa sach so du. Don gian de
giai thich voi khach, nhung khac nghiet voi nguoi vua mua cuoi thang 12.

"Ngay ky niem": moi khach mot ngay rieng, tinh tu ngay ho vao he. Trai deu
cong viec ca nam, nhung kho truyen thong vi moi nguoi mot moc.
"""

import frappe
from frappe.utils import add_months, cint, flt, getdate, nowdate

SO_DIEM = "Vagabond So Diem"
LOAI_HET_HAN = "Het han"

CACH = ("Tat", "Cuon chieu", "Cuoi nam", "Ngay ky niem")
MD_CACH = "Tat"
MD_HAN_THANG = 12
MD_NGAY_CHOT = "31-12"

# Mot dem khong duoc dot diem cua qua ngan nay khach.
#
# Khong phai de tiet kiem may. Day la cai phanh: neu mot ngay nao do cau
# hinh bi go nham thanh "Cuoi nam" va hom do dung 31/12, job se dot sach
# quy diem cua 43.000 khach trong mot dem. Cham tran thi dung lai va gui
# thu, de con nguoi kip nhin truoc khi hong het.
GIOI_HAN_MOT_DEM = 3000


# ------------------------------------------------------------ phep tinh THUAN


def qua_han_cuon_chieu(but, moc):
	"""Bao nhieu diem qua han theo loi vao truoc ra truoc. THUAN.

	but: danh sach (ngay, diem) - diem duong la tich, am la da tieu.
	moc: moc ngay; but tich TRUOC moc la da qua han.

	Vi sao phai tru phan da tieu ra: khach tich 100 diem nam ngoai roi tieu
	80 diem thang truoc thi chi con 20 diem qua han, khong phai 100. Tinh
	theo tich khong thoi la dot cua khach 80 diem ho da tieu roi.

	Vao truoc ra truoc: coi moi khoan da tieu la tieu vao phan diem CU
	nhat. Co loi cho khach, va la cach moi chuong trinh diem deu lam.
	"""
	tich_cu = 0.0
	da_ra = 0.0
	so_du = 0.0
	for ngay, diem in but:
		d = flt(diem)
		so_du += d
		if d > 0:
			if str(ngay or "") < str(moc):
				tich_cu += d
		else:
			da_ra += -d
	con_cu = tich_cu - da_ra
	if con_cu <= 0:
		return 0
	# Khong bao gio dot qua so du dang co: so du la su that cuoi cung.
	return int(min(con_cu, max(0.0, so_du)))


def qua_han_xoa_sach(but):
	"""Toan bo so du. Dung cho hai cach "Cuoi nam" va "Ngay ky niem". THUAN."""
	so_du = sum(flt(d) for _, d in but)
	return int(so_du) if so_du > 0 else 0


def den_ngay_chot(hom_nay, ngay_chot):
	"""Hom nay co phai ngay chot khong. THUAN. ngay_chot dang "31-12"."""
	try:
		ng, th = str(ngay_chot or MD_NGAY_CHOT).split("-")
		ng, th = int(ng), int(th)
	except (ValueError, AttributeError):
		return False
	d = getdate(hom_nay)
	if d.day == ng and d.month == th:
		return True
	# Ngay chot 29-02 hoac 31-04 thi nam thuong khong bao gio toi. Cho chay
	# vao ngay cuoi thang do, khong thi cau hinh do la mot job khong bao
	# gio chay ma khong ai biet.
	import calendar

	cuoi = calendar.monthrange(d.year, th)[1] if 1 <= th <= 12 else 0
	return bool(cuoi and ng > cuoi and d.month == th and d.day == cuoi)


def moc_cuon_chieu(hom_nay, han_thang):
	"""Moc ngay cho cach cuon chieu. THUAN."""
	return str(add_months(getdate(hom_nay), -abs(cint(han_thang) or MD_HAN_THANG)))


# ------------------------------------------------------------------- cai dat


def _cd():
	from vagabond.lib import cfg

	try:
		c = cfg()
	except Exception:
		return {"cach": MD_CACH, "han_thang": MD_HAN_THANG, "ngay_chot": MD_NGAY_CHOT}
	cach = (c.get("diem_chu_ky") or MD_CACH).strip()
	return {
		"cach": cach if cach in CACH else MD_CACH,
		"han_thang": cint(c.get("diem_han_thang")) or MD_HAN_THANG,
		"ngay_chot": (c.get("diem_ngay_chot") or MD_NGAY_CHOT).strip(),
	}


# --------------------------------------------------------------- doc du lieu


def _but_theo_khach(ds_khach=None):
	"""Toan bo but diem, gom theo khach. Mot luot doc chu khong hoi tung nguoi."""
	rows = frappe.db.sql(
		"""
		select khach, date(ngay) ngay, diem
		from `tab%s`
		order by khach, ngay
		"""
		% SO_DIEM,
		as_dict=True,
	)
	ra = {}
	for r in rows:
		ra.setdefault(r["khach"], []).append((str(r["ngay"]), flt(r["diem"])))
	if ds_khach is not None:
		gio = set(ds_khach)
		ra = {k: v for k, v in ra.items() if k in gio}
	return ra


def _da_het_han_ky_nay(khach, tu_ngay):
	"""Khach nay da bi dot diem trong ky nay chua. Chan dot hai lan."""
	return bool(
		frappe.db.sql(
			"select name from `tab%s` where khach = %%s and loai = %%s and date(ngay) >= %%s limit 1"
			% SO_DIEM,
			(khach, LOAI_HET_HAN, str(tu_ngay)),
		)
	)


def _ngay_ky_niem(khach):
	"""Ngay khach vao he, dung lam moc cho cach "Ngay ky niem"."""
	d = frappe.db.get_value("Customer", khach, "creation")
	return getdate(d) if d else None


# ---------------------------------------------------------------- viec chinh


@frappe.whitelist()
def het_han(chay_that=0, hom_nay=None, gioi_han=None):
	"""Dot diem qua han. MAC DINH CHAY THU, khong ghi gi.

	Tra ve bao cao du de nguoi doc quyet dinh co bam that hay khong.
	"""
	_chi_quan_ly()
	c = _cd()
	ngay = getdate(hom_nay or nowdate())
	tran = cint(gioi_han) or GIOI_HAN_MOT_DEM

	ra = {
		"chay_that": cint(chay_that),
		"cach": c["cach"],
		"hom_nay": str(ngay),
		"se_dot": [],
		"tong_diem": 0,
		"bo_qua_da_dot": 0,
		"cham_tran": 0,
	}
	if c["cach"] == "Tat":
		ra["ghi_chu"] = "Cài đặt đang tắt hạn điểm nên không có gì để làm."
		return ra

	moc = moc_cuon_chieu(ngay, c["han_thang"])
	# Ky nay bat dau tu bao gio - dung de biet khach da bi dot trong ky chua.
	dau_ky = str(add_months(ngay, -abs(c["han_thang"])))

	theo_khach = _but_theo_khach()
	for khach, but in theo_khach.items():
		if c["cach"] == "Cuon chieu":
			mat = qua_han_cuon_chieu(but, moc)
		elif c["cach"] == "Cuoi nam":
			mat = qua_han_xoa_sach(but) if den_ngay_chot(ngay, c["ngay_chot"]) else 0
		else:  # Ngay ky niem
			ky = _ngay_ky_niem(khach)
			mat = (
				qua_han_xoa_sach(but)
				if (ky and ky.day == ngay.day and ky.month == ngay.month)
				else 0
			)
		if mat <= 0:
			continue
		if _da_het_han_ky_nay(khach, dau_ky):
			ra["bo_qua_da_dot"] += 1
			continue
		ra["se_dot"].append({"khach": khach, "diem": mat})
		ra["tong_diem"] += mat

	ra["so_khach"] = len(ra["se_dot"])
	if ra["so_khach"] > tran:
		ra["cham_tran"] = 1
		ra["ghi_chu"] = (
			"Đêm nay sẽ đốt điểm của %d khách, vượt mức an toàn %d. Máy dừng lại "
			"để người xem trước. Nếu con số này đúng ý thì chạy lại với "
			"gioi_han lớn hơn." % (ra["so_khach"], tran)
		)
		ra["se_dot"] = ra["se_dot"][:100]
		return ra

	if not cint(chay_that):
		ra["se_dot"] = sorted(ra["se_dot"], key=lambda x: -x["diem"])[:100]
		ra["ghi_chu"] = "Bản chạy thử, chưa ghi gì vào sổ."
		return ra

	from vagabond.khach_hang import _ghi_so_diem

	da = 0
	for x in ra["se_dot"]:
		try:
			_ghi_so_diem(
				x["khach"],
				-abs(x["diem"]),
				LOAI_HET_HAN,
				None,
				"Điểm hết hạn theo chu kỳ %s, mốc %s." % (c["cach"], moc),
			)
			da += 1
		except Exception:
			frappe.log_error(frappe.get_traceback(), "diem_han: dot %s" % x["khach"])
	frappe.db.commit()
	ra["da_dot"] = da
	ra["se_dot"] = sorted(ra["se_dot"], key=lambda x: -x["diem"])[:100]
	return ra


def het_han_tu_dong():
	"""Chay hang dem. Tu kiem cau hinh, tat thi thoat ngay."""
	try:
		if _cd()["cach"] == "Tat":
			return
		frappe.set_user("Administrator")
		kq = het_han(chay_that=1)
		if kq.get("cham_tran"):
			# Cham tran la chuyen phai co nguoi doc, khong phai mot dong
			# nhat ky. Gui thu roi thoi, KHONG dot.
			_bao_nguoi(
				"Điểm hết hạn: máy đã dừng lại",
				"Đêm nay có %d khách tới hạn đốt điểm, vượt mức an toàn. Máy chưa "
				"đốt của ai cả. Mở app vào Cài đặt để xem lại." % kq.get("so_khach", 0),
			)
			return
		if kq.get("da_dot"):
			frappe.logger().info("diem_han: da dot %s khach" % kq["da_dot"])
	except Exception:
		frappe.log_error(frappe.get_traceback(), "diem_han: chay tu dong loi")


def _bao_nguoi(tieu_de, noi_dung):
	try:
		from vagabond.lib import cfg

		nhan = (cfg().get("email_canh_bao") or "").strip()
		if not nhan:
			frappe.log_error(noi_dung, tieu_de)
			return
		frappe.sendmail(recipients=[nhan], subject=tieu_de, message=noi_dung)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "diem_han: khong gui duoc thu")


def _chi_quan_ly():
	if not ({"System Manager", "Accounts Manager"} & set(frappe.get_roles())):
		frappe.throw("Chỉ quản trị hệ thống hoặc kế toán trưởng chạy được việc này.")

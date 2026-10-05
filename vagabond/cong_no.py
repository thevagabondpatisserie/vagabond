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

from vagabond.ban_hang import _kiem_quyen_ban
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
		# Codex #400 v5: cua ngo SePay chung kiem quyen theo luong nay.
		quyen_doc=_kiem_quyen_ban,
		quyen_ghi=_kiem_quyen_ban,
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
def ds_khach_no(tim=""):
	"""Danh sach khach dang con no, kem so tien va so hoa don.

	Chi tinh hoa don DA GHI SO - hoa don con o ban nhap thi chua phai no.

	SO NO LA PHAN CHUA THU, KHONG PHAI CA TO (anh Viet 04/09/2026)
	--------------------------------------------------------------------
	Ban truoc quet theo CO `vgb_pt_thanh_toan = "Cong no"` roi cong thang
	`grand_total`. Hai cai sai nam trong mot dong:

	  * Cong ca to thi thu bao nhieu cung khong tru ra. Hoa don 92523 tra
	    truoc 21.989.250 tren tong 43.978.500 van bi doi ca 43.978.500.
	  * Doc CO thi to nao co con ghi Cong no la con no, du tien da ve. Ca
	    Ms.Amber: phieu doi no da ghi thu du 21.000.000 ma to hoa don van
	    nam trong danh sach.

	Nay so no tinh boi `thu_tien.con_no_cua`, doc ca dong thanh toan lan
	du no so cai. Doc phan dau `vagabond/thu_tien.py` truoc khi sua cho
	nay: co mot phep `min` o do ganh ca 2.183 to cu chua co chung tu thu
	tien, bo di la man cong no nhay tu 115 trieu len 1,31 ty.

	Quet ca hai duong: to mang co Cong no, VA to co dong thanh toan ghi
	Cong no. Duong thu hai bat duoc to tra hon hop ma phan da thu lon hon
	phan no, vi khi do o phuong thuc chinh ghi ten phuong thuc kia.
	"""
	_kiem_quyen_ban()
	from vagabond import thu_tien as tt

	TRUONG = [
		"name", "customer", "customer_name", "posting_date",
		"grand_total", "outstanding_amount", "vgb_pt_thanh_toan",
		"custom_nguon", "vgb_quay", "vgb_ma_tham_chieu", "vgb_khach_no",
	]
	rows = frappe.get_all(
		"Sales Invoice",
		filters={"docstatus": 1, "vgb_pt_thanh_toan": "Công nợ"},
		fields=TRUONG,
		order_by="posting_date asc",
		limit_page_length=0,
	)
	da_co = {r["name"] for r in rows}
	them = [x for x in tt.si_co_dong_cong_no() if x not in da_co]
	for i in range(0, len(them), 200):
		rows += frappe.get_all(
			"Sales Invoice",
			filters={"docstatus": 1, "name": ["in", them[i:i + 200]]},
			fields=TRUONG, limit_page_length=0,
		)
	rows.sort(key=lambda r: str(r.get("posting_date") or ""))
	bang_dong = tt.bang_dong_cua([r["name"] for r in rows])
	da_gom = _hd_da_gom()
	for r in rows:
		r["con_no"] = tt.con_no_cua(
			r.get("grand_total"), r.get("outstanding_amount"),
			bang_dong.get(r["name"]) or [], r.get("vgb_pt_thanh_toan"),
		)
	# Da thu het thi khong con la no, du co con ghi gi di nua.
	rows = [r for r in rows if r["con_no"] > 0]
	# v534 (issue #380): tien khach chuyen DA VE, may da lap phieu thu nhung
	# phieu chua ghi so (thieu uy nhiem chi khach gui). Chi tach ra khi giao
	# dich ngan hang da xac minh doc lap (Codex #381 F4); con lai van la no.
	ve = _tien_da_ve_theo_hd([r["name"] for r in rows])
	khach = {}
	# Codex #382 vong 8: phan da ve (da xac minh) tru khoi so con phai doi,
	# ke ca khi moi phu mot phan; phu du thi hoa don tach han. Phep thuan.
	rows, the_ve, khach_cho = tt.chia_no_hoa_don(rows, ve)
	cho_ghi_so = {"so_hd": the_ve["so_hd"], "tien": the_ve["tien"], "so_khach": 0}
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
		o["tien"] += flt(r["con_doi"])
		if not o["cu_nhat"] or str(r.posting_date) < o["cu_nhat"]:
			o["cu_nhat"] = str(r.posting_date)
		o["hd"].append(
			{
				"name": r.name,
				"ngay": str(r.posting_date),
				# `tien` la SO CON PHAI DOI, khong phai tong to. Man hinh bay
				# ca hai de nguoi doc thay ngay to nao da tra mot phan.
				"tien": flt(r["con_doi"]),
				"tong_don": flt(r.grand_total),
				"da_thu": flt(r.grand_total) - flt(r["con_no"]),
				# Tien da ve tai khoan, phieu thu chua ghi so (v534 vong 8):
				# da tru khoi `tien`, so cai chua tru nen khong nam trong da_thu.
				"da_ve": flt(r["da_ve"]),
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
	tong = sum(v["tien"] for v in ra)
	cho_ghi_so["so_khach"] = len(khach_cho)
	# O tim loc o MAY CHU (QT-19), SAU khi da cong tong: the so tren dau man
	# van noi tong no that, khong teo lai theo chu dang go.
	so_khach_tat_ca = len(ra)
	# Codex #382 vong 9: phan loc ra co tong rieng do may chu cong (QT-19).
	ra, tong_loc = tt.loc_khach_no(ra, tim)
	return {
		"khach": ra, "tong": tong, "so_khach_tat_ca": so_khach_tat_ca,
		"tong_loc": tong_loc, "dang_loc": 1 if (tim or "").strip() else 0,
		# Tien da ve cho ghi so: KHONG cong vao "con phai doi", nhung so cai
		# van ghi la no cho toi khi phieu thu vao so. Man hien ca hai.
		"cho_ghi_so": cho_ghi_so,
	}


NGUON_VE = (
	("cong_no", "Khách công nợ"),
	("chuyen_khoan", "Đơn chuyển khoản"),
)


def _tap_tien_da_ve(nguon="", ky="", tu="", den="", tim=""):
	"""Mọi phiếu thu nháp ĐÃ XÁC MINH tiền về, kèm số đếm chip. CHỈ ĐỌC.

	Nguồn "Khách công nợ" là phiếu phân bổ vào hoá đơn công nợ (cờ Công nợ
	hoặc có dòng công nợ); còn lại là đơn chuyển khoản. Ngày lọc theo ngày
	TIỀN VỀ trên giao dịch ngân hàng. Phiếu chưa xác minh được thì không vào
	danh sách này (nó vẫn là nợ), chỉ đếm lại kèm lý do hay gặp nhất.
	"""
	from vagabond import thu_tien as tt
	from vagabond.khung.cong_cu_ds import khoang_ky, trong_khoang

	ds = tt.phieu_thu_nhap()
	si = set()
	for p in ds:
		for ten, _ in p["hd"]:
			si.add(ten)
	thong_tin = {}
	for i in range(0, len(si), 150):
		lo = list(si)[i:i + 150]
		for r in frappe.get_all(
			"Sales Invoice", filters={"name": ["in", lo]},
			fields=["name", "customer_name", "vgb_pt_thanh_toan", "posting_date",
				"custom_pancake_display_id", "vgb_khach_no"],
			limit_page_length=0,
		):
			thong_tin[r.name] = r
	co_dong_cn = tt.si_co_dong_cong_no()
	tu_ngay, den_ngay = khoang_ky(ky, nowdate(), tu, den)
	tim = (tim or "").strip().lower()
	dem = {"tat_ca": 0}
	ly_do = {}
	ra = []
	for p in ds:
		if not p["da_xac_minh"]:
			ly_do[p["ly_do"]] = ly_do.get(p["ly_do"], 0) + 1
			continue
		hd = [thong_tin.get(ten) for ten, _ in p["hd"] if thong_tin.get(ten)]
		la_cn = any(tt.la_cong_no(h.vgb_pt_thanh_toan) or h.vgb_khach_no or h.name in co_dong_cn for h in hd)
		p["nguon"] = "cong_no" if la_cn else "chuyen_khoan"
		p["ten_khach"] = (hd[0].customer_name if hd else "") or p["ten_khach"]
		p["so_hd"] = len(p["hd"])
		p["hd_dau"] = p["hd"][0][0] if p["hd"] else ""
		p["ma_don"] = (hd[0].custom_pancake_display_id if hd else "") or ""
		p["ngay_hd"] = str(hd[0].posting_date)[:10] if hd else ""
		if not trong_khoang(p["ngay_ve"], tu_ngay, den_ngay):
			continue
		if tim and not any(tim in str(x or "").lower() for x in (
				p["ten_khach"], p["hd_dau"], p["pe"], p["ma_gd"], p["ma_don"])):
			continue
		dem[p["nguon"]] = dem.get(p["nguon"], 0) + 1
		dem["tat_ca"] += 1
		if nguon and p["nguon"] != nguon:
			continue
		ra.append(p)
	ra.sort(key=lambda p: (p["ngay_ve"], p["pe"]), reverse=True)
	chua = sorted(ly_do.items(), key=lambda x: -x[1])
	return {
		"ra": ra, "dem": dem, "tu": tu_ngay or "", "den": den_ngay or "",
		"chua_xac_minh": sum(ly_do.values()),
		"ly_do_hay_gap": [{"ly_do": k, "so": v} for k, v in chua[:3]],
	}


@frappe.whitelist()
def ds_tien_da_ve(nguon="cong_no", ky="", tu="", den="", tim="", so_dong=200):
	"""Tab "Tiền đã về" của màn Công nợ (v534, issue #380). CHỈ ĐỌC."""
	_kiem_quyen_ban()
	from vagabond import thu_tien as tt

	nguon = nguon if nguon in dict(NGUON_VE) else ""
	t = _tap_tien_da_ve(nguon, ky, tu, den, tim)
	try:
		tran = max(1, min(int(so_dong or 200), 500))
	except (TypeError, ValueError):
		tran = 200
	ra = t["ra"]
	return {
		"dong": ra[:tran], "tong_dong": len(ra), "con_nua": max(0, len(ra) - tran),
		"tien": sum(flt(p["tien"]) for p in ra),
		"dem": t["dem"], "nguon": nguon,
		"cac_nguon": [{"k": k, "ten": ten} for k, ten in NGUON_VE],
		"tu": t["tu"], "den": t["den"],
		"chua_xac_minh": t["chua_xac_minh"], "ly_do_hay_gap": t["ly_do_hay_gap"],
		"ke_toan": 1 if tt.la_ke_toan() else 0,
	}


COT_NO = [
	{"k": "ten", "nhan": "Khách", "kieu": "chu"},
	{"k": "name", "nhan": "Hoá đơn", "kieu": "chu"},
	{"k": "ngay", "nhan": "Ngày hoá đơn", "kieu": "ngay"},
	{"k": "tong_don", "nhan": "Tổng đơn (đ)", "kieu": "tien"},
	{"k": "da_thu", "nhan": "Đã thu (đ)", "kieu": "tien"},
	{"k": "da_ve", "nhan": "Tiền đã về, chờ ghi sổ (đ)", "kieu": "tien"},
	{"k": "tien", "nhan": "Còn phải đòi (đ)", "kieu": "tien"},
	{"k": "nguon", "nhan": "Nguồn", "kieu": "chu"},
]

COT_VE = [
	{"k": "ngay_ve", "nhan": "Ngày tiền về", "kieu": "ngay"},
	{"k": "ten_khach", "nhan": "Khách", "kieu": "chu"},
	{"k": "hd_dau", "nhan": "Hoá đơn", "kieu": "chu"},
	{"k": "ma_don", "nhan": "Mã đơn", "kieu": "chu"},
	{"k": "tien", "nhan": "Số tiền (đ)", "kieu": "tien"},
	{"k": "ma_gd", "nhan": "Mã giao dịch", "kieu": "chu"},
	{"k": "pe", "nhan": "Phiếu thu nháp", "kieu": "chu"},
	{"k": "ten_nguon", "nhan": "Nguồn", "kieu": "chu"},
	{"k": "co_unc", "nhan": "Uỷ nhiệm chi khách gửi", "kieu": "chu"},
]


def xuat_no(tim="", **khac):
	"""Adapter Excel tab Đang nợ (khung/cong_cu_ds.MAN_XUAT). Một dòng một hoá đơn."""
	kq = ds_khach_no(tim=tim)
	dong = []
	for k in kq["khach"]:
		for d in k.get("hd") or []:
			x = dict(d)
			x["ten"] = k.get("ten")
			dong.append(x)
	return ("Cong-no-phai-thu", COT_NO, dong)


def xuat_tien_da_ve(nguon="cong_no", ky="", tu="", den="", tim="", **khac):
	"""Adapter Excel tab Tiền đã về. ĐỦ dòng, không cắt 200."""
	_kiem_quyen_ban()
	nguon = nguon if nguon in dict(NGUON_VE) else ""
	t = _tap_tien_da_ve(nguon, ky, tu, den, tim)
	ten = dict(NGUON_VE)
	for p in t["ra"]:
		p["ten_nguon"] = ten.get(p.get("nguon"), "")
		p["co_unc"] = "Có" if p.get("so_tep") else "Chưa"
	return ("Tien-da-ve-cho-ghi-so", COT_VE, t["ra"])


def _tien_da_ve_theo_hd(cac_si):
	"""Hoa don nao co phieu thu nhap da xac minh tien ve, phan bo bao nhieu.

	Mot hoa don co nhieu phieu nhap DA XAC MINH thi CONG lai, moi giao dich
	ngan hang tinh mot lan (Codex #382, xem thu_tien.gom_tien_da_ve). Loi
	doc thi tra rong: man cong no van hien du no nhu cu, khong vi phan moi
	ma trang man.
	"""
	from vagabond import thu_tien as tt

	try:
		ds = tt.phieu_thu_nhap(cac_si=cac_si)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "cong_no: doc phieu thu nhap")
		return {}
	return tt.gom_tien_da_ve(ds)


@frappe.whitelist()
def tao_phieu(khach=None, hoa_don=None, ghi_chu="", nhieu_khach=0):
	"""Gom nhung hoa don da tick thanh MOT phieu doi no.

	v575: nhieu_khach=1 cho gom hoa don cua nhieu phap nhan (Loan Anh
	05/10/2026, Oshima's va anh Vu Oshima). `khach` la khach dung ten phieu,
	phai co it nhat mot hoa don trong phieu. Xem gom_phap_nhan.py."""
	from vagabond import gom_phap_nhan as gpn

	_kiem_quyen_ban()
	khach = (khach or "").strip()
	nhieu_khach = bool(frappe.utils.cint(nhieu_khach))
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
		dong.append(
			{
				"hoa_don": name,
				"khach": gpn.chu_no(si.customer, si.get("vgb_khach_no")),
				"ngay": si.posting_date,
				"nguon": si.custom_nguon or "",
				"so_tien": flt(si.grand_total),
			}
		)
	loi, _cac = gpn.kiem_khach(khach, [(d["hoa_don"], d["khach"]) for d in dong], nhieu_khach)
	if loi:
		frappe.throw(loi)
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


def tong_da_nhan(tong_phieu, da_thu, tien_cho):
	"""Tiền phiếu đòi nợ đã nhận, CỘNG DỒN. THUẦN.

	`da_thu` là số đã ghi nhận trên phiếu (mỗi lần khớp tay, mỗi lần SePay
	đều CỘNG thêm, không ghi đè). `tien_cho` là {giao dịch: tiền} của các
	giao dịch SePay mang mã phiếu mà CHƯA được ghi nhận (chưa nằm trong
	ma_gd), để màn hình thấy ngay tiền vừa về trước khi đối chiếu.

	Giữ `da_thu` và `ma_gd` làm nguồn, đúng như dữ liệu cũ đã ghi, nên phiếu
	khớp trước v571 vẫn đọc đúng mà không phải sửa dữ liệu quá khứ (Codex
	#437 vòng 10). Mỗi giao dịch chỉ tính một lần: đã nằm trong ma_gd (theo
	tên hay số tham chiếu) thì không còn trong `tien_cho`.
	"""
	tong = flt(da_thu) + sum(flt(v) for v in (tien_cho or {}).values())
	return max(0.0, min(flt(tong_phieu), tong))


def _gd_chua_ghi(ma_gd, cac_gd):
	"""{tên giao dịch: tiền} của các giao dịch CHƯA nằm trong ma_gd."""
	da = set(chiem_sao_ke.tach_gd(ma_gd))
	ten = [x for x in set(cac_gd or []) if x and x not in da]
	if not ten:
		return {}
	return {r.name: flt(r.deposit) - flt(r.withdrawal) for r in frappe.get_all("Bank Transaction",
		filters={"name": ["in", ten], "docstatus": ["<", 2]},
		fields=["name", "reference_number", "deposit", "withdrawal"], limit_page_length=0)
		if (r.reference_number or "") not in da}


def _da_nhan_phieu(doc, sepay):
	return tong_da_nhan(doc.tong_tien, doc.da_thu, _gd_chua_ghi(doc.get("ma_gd"), (sepay or {}).get("gd")))


def _hd_chua_co_phieu_thu(cac_si):
	"""Hoa don con mot phan no CHUA co phieu thu nao phu that.

	Phieu da ghi so da tru vao outstanding_amount; phieu nhap thi CHI tinh
	phieu da xac minh tien ve (thu_tien.gom_tien_da_ve), dung phep man Tien
	da ve dung. Codex #437 vong 9: tru ca nhap chua xac minh thi phieu cu
	treo lam hoa don trong nhu da xong, khop tay bi tu choi ma khach van o
	Dang no. Rieng buoc lap phieu thi van tru MOI nhap (chong phu trung).
	"""
	from vagabond import thu_tien as tt

	cac_si = [x for x in set(cac_si or []) if x]
	if not cac_si:
		return set()
	con = {r.name: flt(r.outstanding_amount) for r in frappe.get_all("Sales Invoice",
		filters={"name": ["in", cac_si], "docstatus": 1, "outstanding_amount": [">", 0.5]},
		fields=["name", "outstanding_amount"], limit_page_length=0)}
	if not con:
		return set()
	xm = {k: v.get("phan_bo") for k, v in tt.gom_tien_da_ve(tt.phieu_thu_nhap(cac_si=list(con))).items()}
	return {k for k, v in con.items() if tt.con_chua_phu(v, xm.get(k)) > 0.5}


@frappe.whitelist()
def ds_phieu(trang_thai=None):
	"""Danh sach phieu doi no, kem tien SePay da ve."""
	_kiem_quyen_ban()
	dk = {}
	if trang_thai:
		dk["trang_thai"] = trang_thai
	ds = frappe.get_all(
		"Vagabond Cong No",
		filters=dk,
		fields=[
			"name", "ma_phieu", "khach", "ten_khach", "ngay_tao", "han_qr",
			"tong_tien", "da_thu", "trang_thai", "ghi_chu", "ma_gd",
		],
		order_by="creation desc",
		limit_page_length=200,
	)
	sepay, _bo_qua = _sepay_theo_ma_cn([r.ma_phieu for r in ds])
	hom_nay = getdate(nowdate())
	# v571: phieu "Da thu du" ma hoa don van chua co phieu thu nao thi noi ra,
	# vi khach do van nam o tab Dang no.
	du = [r.name for r in ds if r.trang_thai == "Da thu du"]
	hd_phieu = {}
	if du:
		for x in frappe.get_all("Vagabond Cong No Dong", filters={"parent": ["in", du]},
				fields=["parent", "hoa_don"], limit_page_length=0):
			hd_phieu.setdefault(x.parent, []).append(x.hoa_don)
	thieu = _hd_chua_co_phieu_thu([h for v in hd_phieu.values() for h in v])
	# v575: phieu gom nhieu phap nhan thi noi ra tren danh sach.
	khach_dong = {}
	if ds:
		for x in frappe.get_all("Vagabond Cong No Dong", filters={"parent": ["in", [r.name for r in ds]]},
				fields=["parent", "khach"], limit_page_length=0):
			khach_dong.setdefault(x.parent, []).append(x.khach)
	for r in ds:
		g = sepay.get(str(r.ma_phieu or "").upper()) or {}
		r["sepay"] = flt(g.get("nhan"))
		r["da_nhan"] = tong_da_nhan(r.tong_tien, r.da_thu, _gd_chua_ghi(r.get("ma_gd"), g.get("gd")))
		r["con_thieu"] = max(0.0, flt(r.tong_tien) - r["da_nhan"])
		r["thieu_phieu_thu"] = len([h for h in hd_phieu.get(r.name, []) if h in thieu])
		r["het_han"] = bool(r.han_qr and getdate(r.han_qr) < hom_nay)
		r["so_hd"] = frappe.db.count("Vagabond Cong No Dong", {"parent": r.name})
		r["so_khach"] = len(set([k for k in khach_dong.get(r.name, []) if k and k != r.khach])) + 1
	return {"phieu": ds}


def _cac_khach_phieu(doc):
	"""v575: cac phap nhan trong phieu, kem ten, so hoa don, so tien."""
	from vagabond import gom_phap_nhan as gpn

	dong = [{"khach": d.get("khach"), "so_tien": d.so_tien} for d in doc.dong]
	ra = gpn.gom_theo_khach(dong, doc.khach)
	ten = {r.name: r.customer_name for r in frappe.get_all("Customer",
		filters={"name": ["in", [x["khach"] for x in ra]]}, fields=["name", "customer_name"], limit_page_length=0)}
	for x in ra:
		x["ten"] = ten.get(x["khach"]) or x["khach"]
	return ra


@frappe.whitelist()
def xem_phieu(name):
	"""Chi tiet mot phieu doi no kem duong dan ma QR."""
	from vagabond import gom_phap_nhan as gpn

	_kiem_quyen_ban()
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
		"da_nhan": _da_nhan_phieu(doc, sepay),
		"con_thieu": max(0.0, flt(doc.tong_tien) - _da_nhan_phieu(doc, sepay)),
		"thieu_phieu_thu": len(_hd_chua_co_phieu_thu([d.hoa_don for d in doc.dong]))
		if doc.trang_thai == "Da thu du" else 0,
		"trang_thai": doc.trang_thai,
		"ghi_chu": doc.ghi_chu or "",
		# v577: hộp Khớp tay chỉ mời lối "không gắn giao dịch" khi là kế toán;
		# Huỷ phiếu "đã thu đủ" bị kẹt hỏi máy chủ huỷ được không.
		"ke_toan": 1 if _la_ke_toan() else 0,
		"huy_duoc": 1 if doc.trang_thai != "Da thu du" or huy_duoc_phieu_da_thu(
			doc.get("ma_gd"), _phieu_thu_cua_phieu(doc.name, 1))[0] else 0,
		"so_nhap_hong": len(_phieu_thu_cua_phieu(doc.name, 0)),
		# Codex #444 F1: tiền đã về đủ mà sổ cái còn nợ (phiếu thu nháp chờ
		# kế toán ghi sổ) thì màn KHÔNG được báo "công nợ đã sạch".
		"cho_ghi_so": len(_hd_con_no_so_cai(doc)) if doc.trang_thai == "Da thu du" else 0,
		# Phieu doi no dung tai khoan ao rieng cua khach si neu da khai: khach
		# si hay chuyen theo noi dung cua ho chu khong theo noi dung minh dat
		# (ca OSHIMA 11/08/2026), nen tach bang TAI KHOAN moi chac.
		"qr": tai_khoan.tk_phieu_no(),
		"cac_khach": _cac_khach_phieu(doc),
		"dong": [
			{
				"hoa_don": d.hoa_don,
				"khach": gpn.khach_dong(d.get("khach"), doc.khach),
				"ngay": str(d.ngay or ""),
				"nguon": d.nguon or "",
				"so_gtgt": _so_hd_gtgt(d.hoa_don),
				"so_tien": flt(d.so_tien),
			}
			for d in doc.dong
		],
	}


def _la_ke_toan():
	from vagabond import thu_tien as tt

	return tt.la_ke_toan()


def ghi_thu_cho_phieu(doc, pt="Chuyển khoản", ghi_chu="", so_tien=None, khoa="", dinh=None, chat=False):
	"""Sinh chung tu thu tien cho cac hoa don trong mot phieu doi no.

	VI SAO PHAI CO (anh Viet 04/09/2026)
	--------------------------------------------------------------------
	Truoc ban nay phieu doi no chuyen sang "Da thu du" ma khong sinh chung
	tu nao. Ba hau qua, do duoc tren du lieu that:

	  * Hoa don roi khoi phep loai "dang nam trong phieu cho thu" (phep do
	    chi tinh phieu "Cho thu" va "Thu thieu"), nen QUAY LAI danh sach
	    khach dang no. Dung ca Ms.Amber ngay 04/09.
	  * So cai van ghi khach no. Phieu DNTT-26-09-00001 ghi da thu du
	    21.000.000 ma hoa don HDB-26-08-02800 van du no 21.000.000.
	  * Tien vao ngan hang khong duoc ghi doi ung o dau ca.

	Phan bo theo thu tu hoa don cu truoc: khoan cu la khoan de mat nhat,
	tra duoc dong nao thi tra dong cu nhat truoc.

	Loi o day KHONG duoc lam rot viec danh dau phieu: tien da ve that roi,
	khong the vi mot chung tu chua sinh duoc ma bat ke toan lam lai tu dau.
	Ghi nhat ky va noi ro tren phieu de co nguoi di sinh lai.

	v577: `chat=True` (ke toan khop tay khong giao dich) thi NGUOC LAI: mot
	phieu thu hong la nem ngay, nguoi goi khong danh dau phieu, ca luot lui
	lai. Khong gi lap duoc cung nem. Lieu "khong lam rot" o tren da de lai 17
	phieu thu nhap hong va mot phieu "Da thu du" ma khach van no (ca Loan Anh
	05/10/2026, DNTT-26-10-00004). `dinh(phieu)` dinh UNC truoc khi ghi so.
	"""
	from vagabond import thu_tien as tt

	# v571 (Codex #437 vong 10): chi lap cho PHAN MOI nhan (so_tien), khoa
	# chong trung rieng cho lan nhan do. Truoc day lap theo TOAN BO da_thu
	# va dung chung mot khoa, nen lan tra gop sau bi bo qua.
	con = flt(so_tien) if so_tien is not None else flt(doc.da_thu)
	if con <= 0:
		if chat:
			frappe.throw("Số tiền khớp phải lớn hơn 0.")
		return []
	ds = frappe.get_all(
		"Vagabond Cong No Dong",
		filters={"parent": doc.name},
		fields=["hoa_don"], order_by="idx asc", limit_page_length=0,
	)
	ten = [r["hoa_don"] for r in ds if r.get("hoa_don")]
	if not ten:
		return []
	hd = frappe.get_all(
		"Sales Invoice",
		filters={"name": ["in", ten], "docstatus": 1, "outstanding_amount": [">", 0]},
		fields=["name", "outstanding_amount", "posting_date"],
		order_by="posting_date asc", limit_page_length=0,
	)
	ra = []
	# Phan phieu thu NHAP da phu thi khong chia vao lan nua (tra gop).
	nhap = tt.phan_bo_nhap_theo_hd([h["name"] for h in hd])
	for h in hd:
		if con <= 0:
			break
		phan = min(tt.con_chua_phu(h["outstanding_amount"], nhap.get(h["name"])), con)
		if phan <= 0:
			continue
		if chat:
			try:
				ra += tt.ghi_thu_tien(
					h["name"], [{"pt": pt, "so_tien": phan}],
					nguon="phieu:%s%s" % (doc.name, (":" + khoa) if khoa else ""),
					ghi_chu=("Theo phiếu đòi nợ %s. %s" % (doc.ma_phieu or doc.name, ghi_chu)).strip(),
					dinh=dinh,
				)
			except Exception as e:
				frappe.log_error(frappe.get_traceback(), "cong_no: khop tay khong giao dich")
				frappe.throw("Chưa lập được phiếu thu cho hoá đơn %s: %s. Phiếu %s chưa bị đổi gì."
					% (h["name"], frappe.utils.strip_html(str(e) or type(e).__name__)[:300],
						doc.ma_phieu or doc.name))
			con -= phan
			continue
		try:
			ra += tt.ghi_thu_tien(
				h["name"], [{"pt": pt, "so_tien": phan}],
				nguon="phieu:%s%s" % (doc.name, (":" + khoa) if khoa else ""),
				ghi_chu=("Theo phiếu đòi nợ %s. %s" % (doc.ma_phieu or doc.name, ghi_chu)).strip(),
			)
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), "cong_no: sinh chung tu thu tien")
			# v571: giu lai ly do de nguoi bam biet, khong bao "da sach" suong.
			doc.flags.loi_thu = (doc.flags.loi_thu or []) + [
				"%s: %s" % (h["name"], frappe.utils.strip_html(str(e) or type(e).__name__)[:200])]
			continue
		con -= phan
	if chat and not ra:
		frappe.throw("Các hoá đơn trong phiếu %s không còn phần nợ nào chưa có phiếu thu, "
			"nên không lập phiếu thu nào. Phiếu chưa bị đổi gì." % (doc.ma_phieu or doc.name))
	return ra


@frappe.whitelist()
def kiem_sepay(name):
	"""Doi chieu voi SePay va tu clear cong no khi tien da ve du."""
	_kiem_quyen_ban()
	doc = frappe.get_doc("Vagabond Cong No", name)
	truoc = doc.trang_thai
	sepay = _sepay_cn(doc.ma_phieu)
	# MOT DONG SAO KE CHI DUOC GACH CHO MOT CHUNG TU.
	#
	# Truoc day phieu cong no khong ghi lai dong sao ke nao da tinh cho no,
	# nen khong the co phep chan nao ca: mot lan khach chuyen tien co the
	# vua lam sach mot phieu cong no vua duoc tinh la tien cua mot bill quay.
	# Nay ghi ro, va hoi ca cac luong khac truoc khi nhan.
	# v571 (Codex #437 vong 9, 10): chi tinh giao dich CHUA ghi nhan, CONG
	# vao so da co (khop tay truoc do van giu), va phieu thu chi lap cho
	# DUNG phan moi ve, khoa theo giao dich (khong lap lai phan cu).
	cho = _gd_chua_ghi(doc.get("ma_gd"), sepay.get("gd") or [])
	gd = _giu_gd(doc, list(cho))
	moi = sum(cho.values())
	nhan = min(flt(doc.tong_tien), flt(doc.da_thu) + moi)
	doc.da_thu = nhan
	# Lech duoi 1 dong coi nhu du - ngan hang lam tron.
	if nhan >= flt(doc.tong_tien) - 1:
		doc.trang_thai = "Da thu du"
	elif nhan > 0:
		doc.trang_thai = "Thu thieu"
	doc.ma_gd = chiem_sao_ke.gom_gd(chiem_sao_ke.tach_gd(doc.get("ma_gd")) + chiem_sao_ke.tach_gd(gd))
	da_du_truoc = truoc == "Da thu du"
	# TIEN VE THI SO CAI PHAI BIET.
	# v577: moi giao dich moi ve lap phieu thu NHAP theo dung giao dich do
	# (_lap_theo_gd, mot nguon voi khop tay), hoa don sang tab Tien da ve cho
	# ke toan dinh UNC roi ghi so. Truoc day di ghi_thu_cho_phieu: ghi so thang
	# khong UNC nen hong tung hoa don, de lai phieu nhap hong.
	# Lap hong (giao dich lon hon phan no, da noi cho khac...) thi lui DUNG lan
	# lap do va ghi ro ly do len phieu: tien da ve that, phieu van ghi nhan;
	# man hien canh bao "chua co phieu thu" kem nut Khop tay de lam lai.
	loi_lap = []
	if moi > 0:
		cac_hd = [d.hoa_don for d in doc.dong if d.hoa_don]
		for ten_gd in sorted(cho):
			frappe.db.savepoint("vgb_sepay_lap")
			try:
				g = frappe.get_doc("Bank Transaction", ten_gd, for_update=True)
				_lap_theo_gd(cac_hd, g, cho[ten_gd], "Theo phiếu đòi nợ %s. Đối chiếu SePay." % (doc.ma_phieu or doc.name))
			except Exception as e:
				frappe.db.rollback(save_point="vgb_sepay_lap")
				frappe.log_error(frappe.get_traceback(), "cong_no: SePay lap phieu thu nhap")
				loi_lap.append("%s: %s" % (ten_gd, frappe.utils.strip_html(str(e) or type(e).__name__)[:300]))
	doc.save(ignore_permissions=True)
	if loi_lap:
		doc.add_comment("Comment", "SePay nhận tiền nhưng chưa lập được phiếu thu nháp: %s. Bấm Khớp tay để làm lại."
			% "; ".join(loi_lap))
	frappe.db.commit()
	# Thu bao vua nhan tien: chi gui MOT lan, dung luc phieu chuyen sang du.
	if doc.trang_thai == "Da thu du" and not da_du_truoc:
		try:
			_gui_thu_khi_sach(doc)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "cong_no: gui thu bao da nhan loi")
	return xem_phieu(name)


@frappe.whitelist()
def huy_phieu(name, ly_do=""):
	"""Huy phieu de nhung hoa don trong do quay lai danh sach cho gom."""
	_kiem_quyen_ban()
	doc = frappe.get_doc("Vagabond Cong No", name, for_update=True)
	if doc.trang_thai == "Huy":
		return {"ok": 1, "da_xoa_nhap": []}
	if doc.trang_thai == "Da thu du":
		# v577 (ca Ms.Dung DNTT-26-10-00004): phiếu bị đánh dấu "đã thu đủ" bởi
		# lần khớp tay hỏng (không gạch giao dịch, không lập được phiếu thu
		# nào) thì vẫn huỷ được, để gom lại cho đúng.
		duoc, vi_sao = huy_duoc_phieu_da_thu(doc.get("ma_gd"), _phieu_thu_cua_phieu(doc.name, 1))
		if not duoc:
			frappe.throw(vi_sao)
	nhap = _phieu_thu_cua_phieu(doc.name, 0)
	from vagabond import thu_tien as tt

	with tt.nang_quyen_lap_phieu():
		for ten in nhap:
			frappe.delete_doc("Payment Entry", ten, ignore_permissions=True)
	doc.trang_thai = "Huy"
	doc.ghi_chu = ((doc.ghi_chu or "") + "\nHuỷ: " + (ly_do or "")).strip()
	doc.save(ignore_permissions=True)
	if nhap:
		doc.add_comment("Comment", "Huỷ phiếu, dọn %d phiếu thu nháp hỏng của các lần khớp trước: %s"
			% (len(nhap), ", ".join(nhap)))
	frappe.db.commit()
	return {"ok": 1, "da_xoa_nhap": nhap}


def huy_duoc_phieu_da_thu(ma_gd, phieu_thu_da_ghi):
	"""Phiếu "Đã thu đủ" có huỷ được không. THUẦN. Trả (được, lý do).

	Chỉ huỷ được khi tiền chưa từng gắn vào sổ: không gạch giao dịch ngân
	hàng nào (ma_gd trống) và không có phiếu thu nào của phiếu này đã ghi sổ.
	"""
	if str(ma_gd or "").strip():
		return (False, "Phiếu đã gạch giao dịch ngân hàng nên không huỷ được. Phiếu thu nháp của giao dịch "
			"nằm ở tab Tiền đã về; sai thì báo kế toán.")
	if phieu_thu_da_ghi:
		return (False, "Phiếu đã có phiếu thu ghi sổ (%s) nên không huỷ được. Báo kế toán."
			% ", ".join(phieu_thu_da_ghi))
	return (True, "")


def _phieu_thu_cua_phieu(ten_phieu, docstatus):
	"""Phiếu thu do lối ghi_thu_cho_phieu của phiếu đòi nợ này lập.

	docstatus 0: phiếu NHÁP hỏng. Trước v577 lối đó lập nháp rồi ghi sổ hỏng
	(thiếu UNC) mà không lùi, nên nháp ở lại, giữ phần nợ hoá đơn, chặn mọi
	lần khớp sau. docstatus 1: phiếu đã vào sổ, có thì không huỷ phiếu được.

	Nhận diện bằng khoá chống trùng thu_tien.khoa_chong_trung:
	THU:<hoá đơn>:phieu:<tên>:<khoá lần> hoặc THU:<hoá đơn>:phieu:<tên>|<phương thức>.
	Phiếu thu theo giao dịch ngân hàng mang số giao dịch, không khớp mẫu này.
	"""
	ra = []
	for mau in ("THU:%%:phieu:%s:%%" % ten_phieu, "THU:%%:phieu:%s|%%" % ten_phieu):
		for t in frappe.get_all("Payment Entry", filters={"docstatus": docstatus, "payment_type": "Receive",
				"reference_no": ["like", mau]}, pluck="name", limit_page_length=0):
			if t not in ra:
				ra.append(t)
	return ra


@frappe.whitelist()
def tim_khach(tu_khoa=""):
	"""Bang tim khach hang cho o chon khach: tim theo ma, ten, ma so thue,
	so dien thoai tren ho so VA so dien thoai o danh ba lien he.

	Anh Viet 11/08/2026: go "Ravie" hay go so dien thoai deu phai xo ra
	danh sach. Truoc day chi tim theo ma va ten nen go so dien thoai khong
	bao gio ra.
	"""
	_kiem_quyen_ban()
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
	_kiem_quyen_ban()
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

	# v575: phieu gom nhieu phap nhan thi moi dong ghi kem ten khach cua
	# chinh hoa don do, de ke toan ben khach biet bill nao cua ai.
	cac_khach = d.get("cac_khach") or []
	ten_khach_dong = {x["khach"]: x["ten"] for x in cac_khach}
	nhieu = len(cac_khach) > 1
	hang = []
	for i, x in enumerate(d.get("dong") or [], 1):
		o_hd = esc(x.get("hoa_don") or "-")
		if nhieu:
			o_hd += '<div style="font-size:9.5px;color:#555;white-space:normal">%s</div>' % esc(
				ten_khach_dong.get(x.get("khach")) or x.get("khach") or "")
		hang.append(
			"<tr>"
			+ _td(str(i), "center")
			+ _td(_ngay_vn(x.get("ngay")) or "-", "center", khong_ngat=True)
			+ _td(o_hd, khong_ngat=True)
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
		+ (
			_o_tt("Gồm hoá đơn của:", "<br>".join(
				"%s (%s hoá đơn)" % (esc(x["ten"]), x["so_hd"]) for x in cac_khach))
			if nhieu
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
	_kiem_quyen_ban()
	return {"html": _phieu_html(name)}


@frappe.whitelist()
def xuat_phieu(name):
	"""To phieu yeu cau thanh toan ra PDF A4 doc de gui khach."""
	_kiem_quyen_ban()
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


def _email_thu(doc):
	"""v577: thư báo nhận tiền gửi MỌI pháp nhân trong phiếu, khách đứng tên trước.

	Phiếu gom nhiều pháp nhân (v575) trước đây chỉ gửi khách đứng tên, pháp
	nhân kia không biết công nợ của mình đã tất toán. Trả chuỗi email cách
	nhau dấu phẩy, bỏ trống và trùng.
	"""
	from vagabond import gom_phap_nhan as gpn

	cac = [doc.khach] + [d.get("khach") for d in (doc.dong or [])]
	return ", ".join(gpn.ds_email_thu(cac, _email_khach))


def _ten_kinh_gui(doc):
	"""Tên ở dòng Kính gửi: phiếu gom nhiều pháp nhân thì kể đủ (v577)."""
	ten = doc.ten_khach or doc.khach or "Quý khách"
	try:
		cac = [x["ten"] for x in _cac_khach_phieu(doc)] if doc.get("dong") else []
	except Exception:
		cac = []
	if len(cac) > 1:
		return ", ".join(cac[:-1]) + " và " + cac[-1]
	return ten


def _thu_da_nhan_html(doc, ds_dong):
	"""Thu bao da nhan tien. Di qua khuon thu chung (vagabond/thu_khung.py)."""
	from vagabond import thu_khung as _tk

	esc = _tk.h
	dong = [[esc(x.get("hoa_don") or ""), _tien_vn(x.get("so_tien")) + " đ"] for x in ds_dong]
	than = (
		_tk.doan("Kính gửi <b>%s</b>," % esc(_ten_kinh_gui(doc)))
		+ _tk.doan(
			"%s xác nhận đã nhận được khoản thanh toán <b>%s đ</b> theo phiếu đề nghị "
			"thanh toán <b>%s</b>. Công nợ của quý khách cho các hoá đơn dưới đây đã được "
			"tất toán." % (_tk.TEN_TIEM, _tien_vn(doc.da_thu), esc(doc.ma_phieu or ""))
		)
		+ _tk.bang(
			[("Số hoá đơn", "left"), ("Số tiền", "right")], dong,
			tong=("Tổng cộng", _tien_vn(doc.tong_tien) + " đ"), goc_anh=_tk.goc_anh(),
		)
		+ _tk.doan(
			"Cảm ơn quý khách đã tin tưởng và đồng hành cùng %s. Nếu cần hoá đơn hoặc "
			"chứng từ gì thêm, quý khách cứ trả lời thẳng thư này, bộ phận kinh doanh sẽ "
			"hỗ trợ ngay." % _tk.TEN_TIEM, cach=0,
		)
	)
	return _tk.khung("Đã nhận được thanh toán", than, chan="khach", nhan="Công nợ")


def _hd_con_no_so_cai(doc):
	"""Hoá đơn của phiếu còn nợ TRÊN SỔ CÁI (phiếu thu nháp chưa trừ vào đây)."""
	cac = [d.hoa_don for d in (doc.dong or []) if d.hoa_don]
	if not cac:
		return []
	return frappe.get_all("Sales Invoice", filters={"name": ["in", cac], "docstatus": 1,
		"outstanding_amount": [">", 0.5]}, pluck="name", limit_page_length=0)


def _gui_thu_khi_sach(doc):
	"""v577 (Codex #444 F1): thư "đã nhận thanh toán, công nợ đã tất toán" chỉ
	gửi khi sổ cái đã hết nợ mọi hoá đơn của phiếu.

	Khớp theo giao dịch và SePay tự khớp chỉ lập phiếu thu NHÁP: tiền đã về
	nhưng hoá đơn còn nợ trên sổ tới lúc kế toán đính UNC và ghi sổ. Lúc đó
	thu_tien.ghi_so_phieu_thu gọi gui_thu_sau_ghi_so để gửi.
	"""
	if doc.trang_thai != "Da thu du" or doc.get("email_da_gui"):
		return False
	if _hd_con_no_so_cai(doc):
		return False
	da, _ly_do = _gui_thu_da_nhan(doc)
	return da


def gui_thu_sau_ghi_so(cac_hd):
	"""Sau khi một phiếu thu vào sổ: phiếu đòi nợ nào vừa sạch sổ thì gửi thư báo."""
	ten = sorted(set(frappe.get_all("Vagabond Cong No Dong", filters={"hoa_don": ["in", list(cac_hd or []) or [""]],
		"parenttype": "Vagabond Cong No"}, pluck="parent", limit_page_length=0)))
	ra = []
	for t in ten:
		d = frappe.get_doc("Vagabond Cong No", t)
		try:
			if _gui_thu_khi_sach(d):
				ra.append(t)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "cong_no: gui thu sau ghi so")
	return ra


def _gui_thu_da_nhan(doc, buoc_gui=False):
	"""Gui thu bao da nhan tien. Tra ve (da_gui, ly_do)."""
	if doc.get("email_da_gui") and not buoc_gui:
		return False, "đã gửi rồi"
	email = _email_thu(doc)
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
	_kiem_quyen_ban()
	doc = frappe.get_doc("Vagabond Cong No", name)
	ds_dong = [{"hoa_don": x.hoa_don, "so_tien": flt(x.so_tien)} for x in (doc.dong or [])]
	return {
		"html": _thu_da_nhan_html(doc, ds_dong),
		"email": _email_thu(doc),
	}


@frappe.whitelist()
def gui_thu_da_nhan(name):
	"""Gui tay thu bao da nhan tien, dung khi may gui hut hoac khach bao chua nhan."""
	_kiem_quyen_ban()
	doc = frappe.get_doc("Vagabond Cong No", name)
	da, ly_do = _gui_thu_da_nhan(doc, buoc_gui=True)
	if not da:
		frappe.throw("Chưa gửi được: %s." % ly_do)
	return {"ok": 1, "loi_nhan": "Đã gửi thư báo tới %s." % ly_do}


# --------------------------------- Doi chieu SePay bang tay cho phieu cong no


@frappe.whitelist()
def tim_giao_dich_thu(tu_khoa="", so_ngay=120, so_tien=None, chua_noi=0):
	"""Tra cuu giao dich TIEN VE de ke toan tu khop tay vao phieu.

	Anh Viet 14/08/2026: *"Anh nghĩ là thêm phần đối chiếu danh sách sepay
	bằng tay ở đoạn này nữa lỡ đâu máy đối chiếu không được."*

	May doi chieu theo NOI DUNG chuyen khoan. Khach si chuyen tu app ngan
	hang cua cong ty ho, ke toan ben do hay go noi dung theo he thong cua
	ho chu khong theo ma minh dat - luc do may chiu. Man nay la duong lui.

	v577 (ca Loan Anh 05/10/2026, DNTT-26-10-00004): `chua_noi=1` thì KHÔNG
	lọc đúng số tiền nữa mà đưa mọi giao dịch còn tiền chưa nối, giao dịch
	đúng số xếp lên đầu. Khách Kiệt Tác chuyển 9.550.000 đ cho phiếu 8.450.000 đ;
	hộp Khớp tay lọc đúng số nên giao dịch thật không hiện, người bấm buộc
	phải chọn "Không thấy giao dịch".
	"""
	_kiem_quyen_ban()
	from vagabond import thu_tien as tt

	chua_noi = frappe.utils.cint(chua_noi)
	loc = {
		"date": [">=", add_days(nowdate(), -int(so_ngay or 120))],
		"docstatus": ["<", 2],
		"deposit": [">", 0],
	}
	if chua_noi:
		# Cùng điều kiện bước lập phiếu (lap_phieu_thu_theo_gd): giao dịch đã
		# xác nhận, chưa nối chứng từ nào. Giao dịch nối dở thì chọn cũng hỏng.
		loc["docstatus"] = 1
		loc["unallocated_amount"] = [">", 0.5]
		loc["allocated_amount"] = ["<", 0.5]
	rows = frappe.get_all(
		"Bank Transaction",
		filters=loc,
		fields=["name", "date", "description", "deposit", "bank_account", "reference_number",
			"unallocated_amount"],
		order_by="date desc, creation desc",
		limit_page_length=0,
	)
	k = (tu_khoa or "").strip().lower()
	muc = flt(so_tien) if so_tien else 0.0
	ra = []
	for r in rows:
		tien = flt(r.get("deposit"))
		if muc and not chua_noi and abs(tien - muc) > 1:
			continue
		mo_ta = r.get("description") or ""
		ma = (r.get("reference_number") or r.get("name") or "").strip()
		if k and not tt.gd_khop_tu_khoa(k, mo_ta, ma, tien):
			continue
		ra.append({
			"ma": ma or r["name"],
			"ngay": str(r["date"] or ""),
			"noi_dung": mo_ta[:300],
			"tien": tien,
			"con": flt(r.get("unallocated_amount")) if chua_noi else tien,
			"tai_khoan": r.get("bank_account") or "",
		})
	if chua_noi and ra:
		# Giao dịch đã có phiếu thu (nháp ở tab Tiền đã về) thì không đưa ra:
		# bước lập phiếu sẽ từ chối vì mã giao dịch đã bị chiếm.
		da_co = set(frappe.get_all("Payment Entry", filters={"docstatus": ["<", 2],
			"payment_type": "Receive", "reference_no": ["in", [x["ma"] for x in ra]]},
			pluck="reference_no", limit_page_length=0))
		ra = tt.xep_gd_khop_tay([x for x in ra if x["ma"] not in da_co], muc)
	return {"rows": ra[:300], "tong": len(ra), "con_nua": max(0, len(ra) - 300)}


@frappe.whitelist()
def khop_tay(name, so_tien, ma_giao_dich="", ghi_chu="", ma_lan="", unc=None):
	"""Ghi nhan tay so tien da nhan cho mot phieu.

	Dung khi SePay khong tu khop duoc. Ghi len phieu va de lai dau vet ai
	khop, luc nao, giao dich nao.

	v571 (ca chi Hong, DNTT-26-10-00002, 04/10/2026): co chon giao dich ngan
	hang thi lap NGAY mot phieu thu nhap gop moi hoa don cua phieu theo dung
	giao dich do (thu_tien.lap_phieu_thu_theo_gd), TRUOC khi danh dau phieu.
	Lap khong duoc thi bao loi va khong doi gi, chu khong danh dau "da thu
	du" roi im lang nhu truoc. Phieu da "Da thu du" ma hoa don chua co phieu
	thu thi khop lai duoc, de nguoi lam lai dung viec cu.

	v577 (ca Loan Anh 05/10/2026, DNTT-26-10-00004): loi KHONG gan giao dich
	lap phieu thu ngan hang va ghi so NGAY. Tu ngay chot, phieu thu ngan hang
	khong co UNC dinh kem thi hook chan_thieu_dinh_kem chan ghi so; truoc ban
	nay loi bi nuot tung hoa don, phieu van thanh "Da thu du", 17 phieu thu
	nhap hong o lai, bill van o Dang no. Nay loi do:
	  * chi KE TOAN lam duoc (anh Viet chot 28/09: chi ke toan ghi so phieu thu);
	  * bat buoc dinh UNC khach gui (`unc`), dinh vao tung phieu thu truoc khi
	    ghi so;
	  * mot phieu thu hong la NEM, ca luot lui lai, phieu doi no khong doi.
	"""
	_kiem_quyen_ban()
	from vagabond import thu_tien as tt

	so_tien = flt(so_tien)
	if so_tien <= 0:
		frappe.throw("Số tiền khớp tay phải lớn hơn 0.")
	# Codex #437 vòng 4: khoá phiếu để hai người khớp cùng phiếu đi lần lượt.
	doc = frappe.get_doc("Vagabond Cong No", name, for_update=True)
	if doc.trang_thai == "Huy":
		frappe.throw("Phiếu đã huỷ, không khớp được.")
	if so_tien > flt(doc.tong_tien) + 1:
		frappe.throw(
			"Phiếu chỉ %s đ mà khớp %s đ. Xem lại số tiền."
			% (_tien_vn(doc.tong_tien), _tien_vn(so_tien))
		)
	# Codex #437 vòng 10: một lần bấm Khớp tay mang một mã lần (màn tạo khi
	# mở hộp). Gửi lại cùng mã (mất phản hồi, bấm lại) thì KHÔNG cộng tiền
	# hay lập phiếu thu lần hai. Phiếu đã khoá ở trên nên hai lời gọi trùng
	# đi lần lượt, lời sau thấy dấu của lời trước.
	ma_lan = str(ma_lan or "").strip()[:40]
	if ma_lan and frappe.db.exists("Comment", {"reference_doctype": "Vagabond Cong No",
			"reference_name": doc.name, "content": ["like", "%%[lần khớp %s]%%" % ma_lan]}):
		return {"ok": 1, "da_lam_roi": 1, "pe": "", "loi": [],
			"loi_nhan": "Lần khớp này đã ghi nhận rồi, không ghi thêm."}
	truoc = doc.trang_thai
	cac_hd = [d.hoa_don for d in doc.dong if d.hoa_don]
	chua_pt = _hd_chua_co_phieu_thu(cac_hd)
	if truoc == "Da thu du" and not chua_pt:
		frappe.throw("Phiếu %s đã thu đủ và mọi hoá đơn đã có phiếu thu." % doc.ma_phieu)
	# Ma giao dich go tay cung phai qua cua chiem dung. Truoc day no chi di
	# vao mot dong nhat ky, nen hai ke toan go cung mot ma len hai phieu thi
	# khong ai bao gi, va khong cau truy van nao tim ra duoc.
	# Goi TRUOC khi lap phieu thu: phieu thu mang ma giao dich se chiem ma do.
	gd = _giu_gd(doc, [ma_giao_dich] if str(ma_giao_dich or "").strip() else [])
	g = tt.tim_giao_dich(ma_giao_dich) if str(ma_giao_dich or "").strip() else None
	# Codex #437 F1: CO chon giao dich ma khong nap duoc (go nham, da huy giua
	# luc liet ke va luc bam) thi DUNG, khong roi xuong loi "khong giao dich"
	# roi danh dau da thu. Tai hien tren 30e2b9d: phieu thanh Da thu du va di
	# loi cu tung hoa don, khong co giao dich nao dung sau.
	if str(ma_giao_dich or "").strip() and not g:
		frappe.throw(
			"Không tìm thấy giao dịch ngân hàng %s (có thể đã huỷ hoặc gõ nhầm). "
			"Mở lại Khớp tay và chọn lại giao dịch; phiếu %s chưa bị đổi gì."
			% (str(ma_giao_dich).strip(), doc.ma_phieu)
		)
	# Codex #439 (U1): SỬA phiếu đã thu đủ bằng lối không giao dịch mà phần
	# còn nợ đã bị phiếu thu NHÁP chưa xác minh phủ hết thì bước lập phiếu
	# (trừ MỌI nháp để chống phủ trùng) không lập được gì. Trước đây vẫn báo
	# "Công nợ đã sạch". Nay DỪNG trước mọi thay đổi và chỉ đúng phiếu nháp.
	tep_unc = None
	if not g:
		# v577: lối không gắn giao dịch chỉ dành cho kế toán, và phải có UNC.
		# Soát TRƯỚC mọi thay đổi, bằng người đang bấm.
		if not tt.la_ke_toan():
			frappe.throw(cau_khong_gd_sales(doc.ma_phieu or doc.name))
		tep_unc = tt.soat_tep_unc_moi(unc)
	if not g and truoc == "Da thu du" and chua_pt:
		_chan_sua_vuong_nhap(doc.ma_phieu or doc.name, chua_pt)
	lap = None
	if g:
		lap = _lap_theo_gd([h for h in cac_hd if h in chua_pt], g, so_tien,
			"Theo phiếu đòi nợ %s. %s" % (doc.ma_phieu or doc.name, (ghi_chu or "").strip()))
	# Số đã nhận CỘNG DỒN (Codex #437 vòng 4, 9, 10): mỗi lần khớp CỘNG phần
	# mới nhận vào da_thu. Giao dịch đã nằm trong ma_gd (lần khớp trước, hay
	# SePay đã ghi) thì không cộng lại: đây là lần sửa phiếu thu, không phải
	# tiền mới.
	da_ghi = set(chiem_sao_ke.tach_gd(doc.get("ma_gd")))
	if g:
		moi = 0.0 if ({g.name, g.reference_number or ""} & da_ghi) else flt(lap.get("tien"))
	else:
		moi = so_tien
	doc.da_thu = min(flt(doc.tong_tien), flt(doc.da_thu) + moi)
	doc.trang_thai = "Da thu du" if flt(doc.da_thu) >= flt(doc.tong_tien) - 1 else "Thu thieu"
	if gd:
		# Ghi cả TÊN giao dịch để SePay theo mã phiếu không tính lại lần nữa.
		doc.ma_gd = chiem_sao_ke.gom_gd(chiem_sao_ke.tach_gd(doc.get("ma_gd")) + chiem_sao_ke.tach_gd(gd)
			+ ([g.name] if g else []))
		doc.nguoi_khop_tay = frappe.session.user
		doc.ngay_khop_tay = frappe.utils.now_datetime()
	doc.save(ignore_permissions=True)
	# Codex #439 (U2): lối không giao dịch LẬP PHIẾU THU TRƯỚC, rồi mới ghi dấu
	# [lần khớp] và commit. Lỗi ngoài phần bắt lỗi từng hoá đơn thì cả lượt
	# lùi lại, dấu lần khớp chưa thành, bấm lại cùng mã lần vẫn làm lại được.
	# Trước đây dấu đã commit trước nên lần thử lại chỉ nhận "đã làm rồi".
	loi = []
	if not lap and (truoc != "Da thu du" or chua_pt):
		# v577: chặt (chat=True): một phiếu thu hỏng là ném, cả lượt lùi lại,
		# phiếu đòi nợ không thành "đã thu" trong khi khách vẫn nợ trên sổ.
		ghi_thu_cho_phieu(doc, "Chuyển khoản", "Kế toán khớp tay.", so_tien=moi,
			khoa="tay:%s" % (ma_lan or frappe.generate_hash(length=8)),
			dinh=tt.ham_dinh_unc(tep_unc) if tep_unc else None, chat=True)
		loi = doc.flags.loi_thu or []
	# Codex #437 vòng 6: có phiếu thu thì ghi ĐÚNG số máy chủ đã phân bổ,
	# không ghi số máy khách gửi lên.
	so_ghi = flt(lap.get("tien")) if lap else so_tien
	doc.add_comment(
		"Comment",
		"Khớp tay %s đ%s, người làm %s%s%s%s"
		% (
			_tien_vn(so_ghi),
			" (giao dịch %s)" % ma_giao_dich if ma_giao_dich else "",
			frappe.session.user,
			". Phiếu thu nháp %s" % lap["pe"] if lap else "",
			". Ghi chú: %s" % ghi_chu if (ghi_chu or "").strip() else "",
			" [lần khớp %s]" % ma_lan if ma_lan else "",
		),
	)
	frappe.db.commit()
	if doc.trang_thai == "Da thu du" and truoc != "Da thu du":
		try:
			_gui_thu_khi_sach(doc)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "cong_no: gui thu sau khop tay loi")
	return {"ok": 1, "pe": lap["pe"] if lap else "", "loi": loi,
		"loi_nhan": cau_bao_khop_tay(doc.ma_phieu, so_ghi, doc.trang_thai, lap, loi)}


def _lap_theo_gd(cac_hd, g, so_tien, ghi_chu):
	"""Lập phiếu thu NHÁP cho các hoá đơn theo một giao dịch ngân hàng.

	Một nguồn cho cả khớp tay chọn giao dịch và SePay tự khớp (v577, AGENTS
	điều 18). v576 (Codex #442): hoá đơn của nhiều pháp nhân thì mỗi khách
	một phiếu thu nháp cùng giao dịch, chung mã nhóm (tach_khach).
	"""
	from vagabond import gom_phap_nhan as gpn
	from vagabond import thu_tien as tt

	tach = gpn.khop_tung_hoa_don([r.customer for r in frappe.get_all("Sales Invoice",
		filters={"name": ["in", list(cac_hd) or [""]]}, fields=["name", "customer"], limit_page_length=0)])
	return tt.lap_phieu_thu_theo_gd(list(cac_hd), g, so_tien, ghi_chu,
		**({"tach_khach": True} if tach else {}))


def cau_khong_gd_sales(ma_phieu):
	"""Câu báo khi người không phải kế toán chọn khớp tay không gắn giao dịch. THUẦN."""
	return ("Phiếu %s: khớp tay không gắn giao dịch ngân hàng là ghi sổ phiếu thu ngay, nên chỉ kế toán "
		"làm được và phải đính uỷ nhiệm chi khách gửi. Mở lại Khớp tay, gõ tên khách hoặc số tiền vào ô tìm "
		"để tìm giao dịch khách chuyển (khách hay chuyển gộp nhiều phiếu nên số tiền có thể khác). "
		"Vẫn không thấy thì báo kế toán. Phiếu chưa bị đổi gì." % ma_phieu)


def cau_chan_nhap(ma_phieu, nhap):
	"""Câu báo khi phần nợ còn lại đã bị phiếu thu nháp chưa xác minh phủ. THUẦN.

	nhap: {hoá đơn: [phiếu nháp]}.
	"""
	ds = "; ".join("%s: %s" % (hd, ", ".join(pe)) for hd, pe in sorted((nhap or {}).items()) if pe)
	return ("Phiếu %s: phần còn nợ đã có phiếu thu nháp chưa xác minh tiền về (%s), nên khớp tay "
		"không lập thêm phiếu thu để khỏi thu trùng. Vào mục Tiền đã về: gắn đúng giao dịch cho phiếu "
		"nháp đó, hoặc huỷ phiếu nháp sai rồi khớp tay lại. Phiếu nháp hỏng do chính phiếu này lập ở "
		"lần khớp trước thì bấm Huỷ phiếu: máy dọn các phiếu nháp đó, hoá đơn về lại Đang nợ để gom lại. "
		"Phiếu chưa bị đổi gì."
		% (ma_phieu, ds or "không rõ phiếu"))


def _chan_sua_vuong_nhap(ma_phieu, chua_pt):
	"""Dừng lần SỬA không giao dịch nếu phiếu nháp chưa xác minh đã phủ hết phần nợ.

	Cùng phép chia của ghi_thu_cho_phieu (dư nợ trừ MỌI phân bổ nháp), nên
	khi ở đây còn 0 thì bước lập phiếu chắc chắn không lập được gì.
	"""
	from vagabond import thu_tien as tt

	con = {r.name: flt(r.outstanding_amount) for r in frappe.get_all("Sales Invoice",
		filters={"name": ["in", list(chua_pt)], "docstatus": 1, "outstanding_amount": [">", 0.5]},
		fields=["name", "outstanding_amount"], limit_page_length=0)}
	if not con:
		return
	nhap = tt.phan_bo_nhap_theo_hd(list(con))
	if sum(max(tt.con_chua_phu(v, nhap.get(k)), 0) for k, v in con.items()) > 0.5:
		return
	frappe.throw(cau_chan_nhap(ma_phieu, tt.phieu_nhap_cua_hd(list(con))))


def cau_bao_khop_tay(ma_phieu, so_tien, trang_thai, lap, loi):
	"""Cau bao sau khi khop tay, NOI DUNG viec da xay ra. THUAN.

	v571: truoc day luon bao "Cong no da sach" khi phieu du tien, ke ca khi
	phieu thu cho hoa don hong het, nen Loan Anh tin la xong ma khach van o
	tab Dang no.
	"""
	dau = "Đã ghi nhận %s đ cho phiếu %s." % (_tien_vn(so_tien), ma_phieu)
	if lap:
		return (dau + " Đã lập phiếu thu nháp %s cho %d hoá đơn theo giao dịch %s; các hoá đơn "
			"chuyển sang mục Tiền đã về, chờ kế toán đính UNC khách gửi rồi ghi sổ."
			% (lap["pe"], len(lap.get("hd") or []), lap.get("ma_gd") or ""))
	if loi:
		return (dau + " Nhưng máy CHƯA lập được phiếu thu cho %d hoá đơn nên khách vẫn nằm ở "
			"Đang nợ: %s. Báo kế toán xử lý." % (len(loi), "; ".join(loi)))
	return dau + (" Công nợ đã sạch." if trang_thai == "Da thu du" else "")

"""Phan he Bao cao (anh Viet 12/08/2026).

Mot cho duy nhat de ban giam doc, quan ly sales, quan ly cua hang, ke toan
va marketing nhin so lieu CUA CA BA DIEM BAN, khong phai mo ba noi roi
cong tay: Sales Online (307/1 Nguyen Van Troi), District 1 (9 Tran Cao Van)
va NVHTN (21 Pham Ngoc Thach). Them chi nhanh moi thi chi can them mot
dong trong man Cai dat > Diem ban, khong phai sua ma nguon.

Nguyen tac:

1. SO LIEU DOC THANG TU HOA DON, khong co bang tong hop trung gian. Bao cao
   luon dung voi giay to, khong bao gio "quen chay job tong hop". Doi lai
   moi lan mo la quet lai - hien moi ngay vai tram hoa don nen nhanh; khi
   nao du lieu len hang chuc nghin thi moi tinh chuyen luu bang tong.
2. CHI TINH HOA DON DA GHI SO (docstatus 1). Don con nhap chua phai doanh
   thu. Rieng bao cao sua/huy thi nguoc lai, phai soi vao don da huy.
3. Moi bao cao deu tra ve cung MOT hinh dang: cot, dong, tong, bieu do.
   Nho vay man hinh chi viet mot lan, them bao cao moi khong phai sua giao
   dien.
"""

import base64
import io
import re

import frappe

from vagabond import diem_ban
from frappe.utils import add_days, add_months, flt, getdate, nowdate

# Ai duoc xem. Anh Viet chot 12/08/2026: ban giam doc, Loan Anh (quan ly
# sales), De (quan ly cua hang), Dung (ke toan), Vu (marketing - xem so de
# len chuong trinh khuyen mai). Nguoi moi thi cap vai tro "Vagabond Bao cao"
# chu khong sua code.
QUYEN_XEM = {
	"System Manager",
	"Sales Manager",
	"Accounts Manager",
	"Vagabond Bao cao",
}

# Ba diem ban. Don Sales online khong mang ma quay (vgb_quay de trong) nen
# quy uoc quay rong la SALES - cung quy uoc voi module khuyen mai.
def _diem_ban():
	"""Diem ban doc tu Cai dat. Bao cao lay CA diem da tat: so lieu cu cua
	mot diem da dong van phai xem lai duoc. Xem vagabond/diem_ban.py."""
	return [
		{"ma": d["ma"], "ten": d["ten_ngan"], "dia_chi": d["dia_chi"]}
		for d in diem_ban.ds()
	]


KY_HAN = ["ngay", "tuan", "thang", "quy", "nam", "tuy_chon"]

# Bang ke chi tiet mot thang co the len hang nghin dong. Gui het xuong dien
# thoai la treo may, ma cat mat cua ke toan thi bao cao vo dung. Cach xu ly:
# MAN HINH chi nhan toi day, con FILE EXCEL luon day du - vi ke toan can du
# lieu thi ho mo Excel chu khong soi tren dien thoai.
GIOI_HAN_DONG = 600


def _kiem_quyen():
	if not QUYEN_XEM & set(frappe.get_roles()):
		frappe.throw(
			"Phân hệ Báo cáo chỉ mở cho ban giám đốc, quản lý và kế toán. "
			"Cần xem thì nhờ quản trị cấp vai trò \"Vagabond Bao cao\"."
		)


# --------------------------------------------------------------- khoang ngay

def khoang_ngay(ky="ngay", moc=None, tu=None, den=None):
	"""Doi mot ky bao cao thanh cap ngay (tu, den) - hai dau deu tinh.

	moc la mot ngay bat ky NAM TRONG ky do. Vi du ky "thang" voi moc
	15/08 tra ve 01/08 - 31/08. Nho vay man hinh chi can gui ngay dang
	xem, khong phai tu tinh dau thang cuoi thang.
	"""
	ky = (ky or "ngay").strip()
	if ky == "tuy_chon":
		t = getdate(tu or nowdate())
		d = getdate(den or nowdate())
		if d < t:
			t, d = d, t
		return t, d

	m = getdate(moc or nowdate())
	if ky == "ngay":
		return m, m
	if ky == "tuan":
		# Tuan tinh tu thu Hai, dung thoi quen Viet Nam.
		dau = add_days(m, -m.weekday())
		return dau, add_days(dau, 6)
	if ky == "thang":
		dau = m.replace(day=1)
		return dau, add_days(add_months(dau, 1), -1)
	if ky == "quy":
		q = (m.month - 1) // 3
		dau = m.replace(month=q * 3 + 1, day=1)
		return dau, add_days(add_months(dau, 3), -1)
	if ky == "nam":
		dau = m.replace(month=1, day=1)
		return dau, m.replace(month=12, day=31)
	return m, m


def _nhan_ky(ky, tu, den):
	if ky == "ngay":
		return "Ngày %s" % tu.strftime("%d/%m/%Y")
	if ky == "tuan":
		return "Tuần %s - %s" % (tu.strftime("%d/%m"), den.strftime("%d/%m/%Y"))
	if ky == "thang":
		return "Tháng %s" % tu.strftime("%m/%Y")
	if ky == "quy":
		return "Quý %d/%d" % ((tu.month - 1) // 3 + 1, tu.year)
	if ky == "nam":
		return "Năm %d" % tu.year
	return "%s - %s" % (tu.strftime("%d/%m/%Y"), den.strftime("%d/%m/%Y"))


def _ky_truoc(ky, tu, den):
	"""Ky lien truoc cung do dai. Thang 8 doi thang 7, quy 3 doi quy 2, con
	khoang tuy chon thi lui dung bang so ngay dang xem.

	Khong dung add_days(tu, -so_ngay) cho ky thang: thang 7 co 31 ngay ma
	thang 2 co 28, lui theo so ngay se ra khoang lech dau thang."""
	if ky == "ngay":
		return add_days(tu, -1), add_days(tu, -1)
	if ky == "tuan":
		return add_days(tu, -7), add_days(den, -7)
	if ky == "thang":
		dau = add_months(tu, -1)
		return dau, add_days(add_months(dau, 1), -1)
	if ky == "quy":
		dau = add_months(tu, -3)
		return dau, add_days(add_months(dau, 3), -1)
	if ky == "nam":
		dau = tu.replace(year=tu.year - 1, month=1, day=1)
		return dau, dau.replace(month=12, day=31)
	so_ngay = (den - tu).days + 1
	return add_days(tu, -so_ngay), add_days(tu, -1)


def _cot_chinh(kq):
	"""Cot so lieu chinh cua mot bao cao - cot duoc dem ra so voi ky truoc.

	Uu tien cot dang ve bieu do (do la cot nguoi lam bao cao coi la quan
	trong nhat), khong co thi lay cot tien dau tien."""
	bd = kq.get("bieu_do") or {}
	g = bd.get("gia_tri")
	for c in kq["cot"]:
		if c["k"] == g and c["kieu"] in ("tien", "so"):
			return c
	for c in kq["cot"]:
		if c["kieu"] == "tien" and not c.get("kc"):
			return c
	return None


def _diem(si):
	"""Quay cua mot hoa don. Don Sales khong co quay nen tra ve SALES."""
	return (si.get("vgb_quay") or "").strip().upper() or "SALES"


def _hoa_don(tu, den, diem=None, nguon=None, pt=None, docstatus=1):
	"""Doc hoa don trong khoang ngay, da loc theo diem ban - nguon - phuong
	thuc. Loc diem ban lam bang Python vi "SALES" trong app la vgb_quay
	de TRONG duoi CSDL, khong viet duoc thanh bo loc SQL goi gon."""
	loc = {"docstatus": docstatus, "posting_date": ["between", [str(tu), str(den)]]}
	if nguon:
		loc["custom_nguon"] = nguon
	if pt:
		loc["vgb_pt_thanh_toan"] = pt
	ds = frappe.get_all(
		"Sales Invoice",
		filters=loc,
		fields=[
			"name", "posting_date", "posting_time", "customer", "customer_name",
			"grand_total", "net_total", "total_taxes_and_charges", "discount_amount",
			"vgb_quay", "custom_nguon", "vgb_pt_thanh_toan", "custom_hddt_so",
			"custom_hddt_trang_thai", "custom_pancake_display_id", "vgb_khach_no",
			"outstanding_amount", "owner", "vgb_tam_tinh", "vgb_huy",
			"vgb_ma_tham_chieu", "custom_hddt_ky_hieu",
		],
		order_by="posting_date asc, posting_time asc",
		limit_page_length=0,
	)
	# Phieu tam tinh la giay giu mon, khach chua tra tien - khong phai
	# doanh thu, khong duoc dem vao bat ky bao cao nao. Bill da huy cung
	# vay: no van nam trong he thong de doi chieu, nhung khong phai tien.
	ds = [r for r in ds if not r.get("vgb_tam_tinh") and not r.get("vgb_huy")]
	if diem:
		can = [d.strip().upper() for d in str(diem).split(",") if d.strip()]
		ds = [r for r in ds if _diem(r) in can]
	return ds


def _tien(x):
	return flt(x or 0)


def _cot(*bo):
	"""Moi cot: (khoa, nhan, kieu) hoac (khoa, nhan, kieu, khong_cong).

	Kieu de man hinh biet canh phai hay trai va co dinh dang tien hay
	khong: chu / tien / so / phan_tram / ngay.

	khong_cong=True thi bo cot ra khoi dong TONG. Can cho nhung cot ma
	cong lai la vo nghia - vi du don gia: cong don gia cua ba mon khac
	nhau ra mot con so khong dai dien cho cai gi ca."""
	ra = []
	for b in bo:
		c = {"k": b[0], "nhan": b[1], "kieu": b[2]}
		if len(b) > 3 and b[3]:
			c["kc"] = 1
		ra.append(c)
	return ra


# ------------------------------------------------------------------ bao cao

def _bc_tong_doanh_thu(hd, **kw):
	"""BC01 - tong doanh thu, tach theo tung diem ban."""
	# Doc bang ten diem MOT LAN roi dung lai: goi trong vong lap thi moi dong
	# hoa don lai doc va phan tich lai cau hinh, bao cao vai nghin dong la
	# thay cham ngay.
	ten = diem_ban.ten_diem()
	gom = {}
	for r in hd:
		d = _diem(r)
		o = gom.setdefault(d, {"diem": ten.get(d, d), "so_hd": 0, "tien": 0.0, "giam": 0.0})
		o["so_hd"] += 1
		o["tien"] += _tien(r.grand_total)
		o["giam"] += _tien(r.discount_amount)
	dong = []
	for d in _diem_ban():
		o = gom.get(d["ma"])
		if not o:
			o = {"diem": d["ten"], "so_hd": 0, "tien": 0.0, "giam": 0.0}
		o["binh_quan"] = o["tien"] / o["so_hd"] if o["so_hd"] else 0
		dong.append(o)
	tong_tien = sum(o["tien"] for o in dong)
	for o in dong:
		o["ty_le"] = (o["tien"] / tong_tien * 100) if tong_tien else 0
	return {
		"cot": _cot(
			("diem", "Điểm bán", "chu"), ("so_hd", "Số hoá đơn", "so"),
			("tien", "Doanh thu", "tien"), ("binh_quan", "Bình quân/hoá đơn", "tien"),
			("giam", "Đã giảm giá", "tien"), ("ty_le", "Tỷ trọng", "phan_tram"),
		),
		"dong": dong,
		"bieu_do": {"nhan": "diem", "gia_tri": "tien"},
	}


def _bc_theo_ngay(hd, **kw):
	"""BC02 - doanh thu tung ngay trong ky, de nhin duong xu huong."""
	gom = {}
	for r in hd:
		n = str(r.posting_date)
		o = gom.setdefault(n, {"ngay": n, "so_hd": 0, "tien": 0.0})
		o["so_hd"] += 1
		o["tien"] += _tien(r.grand_total)
	dong = sorted(gom.values(), key=lambda x: x["ngay"])
	for o in dong:
		o["binh_quan"] = o["tien"] / o["so_hd"] if o["so_hd"] else 0
		o["ngay_vn"] = getdate(o["ngay"]).strftime("%d/%m")
	return {
		"cot": _cot(
			("ngay_vn", "Ngày", "chu"), ("so_hd", "Số hoá đơn", "so"),
			("tien", "Doanh thu", "tien"), ("binh_quan", "Bình quân/hoá đơn", "tien"),
		),
		"dong": dong,
		"bieu_do": {"nhan": "ngay_vn", "gia_tri": "tien"},
	}


def _bc_nguon_don(hd, **kw):
	"""BC03 - doanh thu theo nguon don, tach rieng tung diem ban."""
	ten = diem_ban.ten_diem()
	gom = {}
	for r in hd:
		n = (r.custom_nguon or "").strip() or "(không ghi nguồn)"
		o = gom.setdefault(n, {"nguon": n, "so_hd": 0, "tien": 0.0, "diem": set()})
		o["so_hd"] += 1
		o["tien"] += _tien(r.grand_total)
		o["diem"].add(ten.get(_diem(r), _diem(r)))
	dong = sorted(gom.values(), key=lambda x: -x["tien"])
	tong = sum(o["tien"] for o in dong)
	for o in dong:
		o["diem"] = ", ".join(sorted(o["diem"]))
		o["ty_le"] = (o["tien"] / tong * 100) if tong else 0
		o["binh_quan"] = o["tien"] / o["so_hd"] if o["so_hd"] else 0
	return {
		"cot": _cot(
			("nguon", "Nguồn đơn", "chu"), ("diem", "Điểm bán", "chu"),
			("so_hd", "Số hoá đơn", "so"), ("tien", "Doanh thu", "tien"),
			("binh_quan", "Bình quân/hoá đơn", "tien"), ("ty_le", "Tỷ trọng", "phan_tram"),
		),
		"dong": dong,
		"bieu_do": {"nhan": "nguon", "gia_tri": "tien"},
	}


def _bc_thanh_toan(hd, **kw):
	"""BC04 - doanh thu theo phuong thuc thanh toan (kieu Fabi)."""
	gom = {}
	for r in hd:
		p = (r.vgb_pt_thanh_toan or "").strip() or "(chưa chọn)"
		o = gom.setdefault(p, {"pt": p, "so_hd": 0, "tien": 0.0, "con_no": 0.0})
		o["so_hd"] += 1
		o["tien"] += _tien(r.grand_total)
		o["con_no"] += _tien(r.outstanding_amount)
	dong = sorted(gom.values(), key=lambda x: -x["tien"])
	tong = sum(o["tien"] for o in dong)
	for o in dong:
		o["ty_le"] = (o["tien"] / tong * 100) if tong else 0
	return {
		"cot": _cot(
			("pt", "Phương thức", "chu"), ("so_hd", "Số hoá đơn", "so"),
			("tien", "Tổng tiền", "tien"), ("con_no", "Còn phải thu", "tien"),
			("ty_le", "Tỷ trọng", "phan_tram"),
		),
		"dong": dong,
		"bieu_do": {"nhan": "pt", "gia_tri": "tien"},
	}


def _bc_hddt(hd, **kw):
	"""BC05 - doi soat hoa don dien tu: don nao co so, dang trang thai gi."""
	gom = {}
	for r in hd:
		if (r.custom_hddt_so or "").strip():
			t = (r.custom_hddt_trang_thai or "").strip() or "Đã đẩy, chưa rõ trạng thái"
		else:
			t = "Chưa xuất hoá đơn điện tử"
		o = gom.setdefault(t, {"trang_thai": t, "so_hd": 0, "tien": 0.0})
		o["so_hd"] += 1
		o["tien"] += _tien(r.grand_total)
	dong = sorted(gom.values(), key=lambda x: -x["so_hd"])
	ten = diem_ban.ten_diem()
	chua = [
		{
			"hoa_don": r.name,
			"ngay": str(r.posting_date),
			"don": r.custom_pancake_display_id or "",
			"diem": ten.get(_diem(r), _diem(r)),
			"tien": _tien(r.grand_total),
		}
		for r in hd
		if not (r.custom_hddt_so or "").strip()
	]
	return {
		"cot": _cot(
			("trang_thai", "Trạng thái hoá đơn điện tử", "chu"),
			("so_hd", "Số hoá đơn", "so"), ("tien", "Doanh thu", "tien"),
		),
		"dong": dong,
		"bieu_do": {"nhan": "trang_thai", "gia_tri": "so_hd"},
		"phu": {
			"tieu_de": "Hoá đơn chưa có số hoá đơn điện tử",
			"cot": _cot(
				("ngay", "Ngày", "ngay"), ("hoa_don", "Mã phiếu", "chu"),
				("don", "Đơn", "chu"), ("diem", "Điểm bán", "chu"),
				("tien", "Số tiền", "tien"),
			),
			"dong": chua[:200],
		},
	}


def _bc_khuyen_mai(hd, tu=None, den=None, **kw):
	"""BC06 - chuong trinh khuyen mai: bao nhieu luot, giam bao nhieu tien."""
	ds = frappe.get_all(
		"Vagabond CTKM Su Dung",
		filters={"ngay": ["between", [str(tu), str(den)]]},
		fields=["ten_ctkm", "loai", "tien_giam", "thu_ngan", "quay", "hoa_don", "voucher"],
		limit_page_length=0,
	)
	gom = {}
	for r in ds:
		t = (r.ten_ctkm or "").strip() or (r.loai or "Khuyến mãi")
		o = gom.setdefault(t, {"ctkm": t, "loai": r.loai or "", "so_lan": 0, "giam": 0.0, "hd": set()})
		o["so_lan"] += 1
		o["giam"] += _tien(r.tien_giam)
		if r.hoa_don:
			o["hd"].add(r.hoa_don)
	dong = sorted(gom.values(), key=lambda x: -x["giam"])
	for o in dong:
		o["so_hd"] = len(o["hd"])
		o.pop("hd", None)
		o["giam_tb"] = o["giam"] / o["so_lan"] if o["so_lan"] else 0
	return {
		"cot": _cot(
			("ctkm", "Chương trình", "chu"), ("loai", "Loại", "chu"),
			("so_lan", "Số lượt", "so"), ("so_hd", "Số hoá đơn", "so"),
			("giam", "Tổng đã giảm", "tien"), ("giam_tb", "Giảm bình quân", "tien"),
		),
		"dong": dong,
		"bieu_do": {"nhan": "ctkm", "gia_tri": "giam"},
	}


def _bc_sua_huy(hd, tu=None, den=None, **kw):
	"""BC07 - hoa don bi sua hoac huy, kem ten nguoi thao tac.

	Hai nguon: hoa don da huy (docstatus 2) va so tay ghi vet moi lan
	sua/xoa/doi ngay ma module ban hang tu ghi vao Comment.
	"""
	# Hai kieu huy deu phai co mat: huy dung nghiep vu (docstatus 2) va huy
	# mem ban nhap (vgb_huy). Truoc day chi lay docstatus 2, nen bill huy
	# mem chi lot vao qua dong ghi vet Comment voi cot tien bang 0 - bao cao
	# huy mat sach so tien, dung cai con so ke toan can nhat.
	huy = frappe.get_all(
		"Sales Invoice",
		filters={
			"posting_date": ["between", [str(tu), str(den)]],
			"docstatus": 2,
		},
		fields=[
			"name", "posting_date", "grand_total", "vgb_quay",
			"custom_pancake_display_id", "modified_by", "vgb_huy", "vgb_huy_ly_do",
			"vgb_huy_boi",
		],
		limit_page_length=0,
	)
	huy += frappe.get_all(
		"Sales Invoice",
		filters={
			"posting_date": ["between", [str(tu), str(den)]],
			"docstatus": 0,
			"vgb_huy": 1,
		},
		fields=[
			"name", "posting_date", "grand_total", "vgb_quay",
			"custom_pancake_display_id", "modified_by", "vgb_huy", "vgb_huy_ly_do",
			"vgb_huy_boi",
		],
		limit_page_length=0,
	)
	ten = diem_ban.ten_diem()
	dong = [
		{
			"ngay": str(r.posting_date),
			"hoa_don": r.name,
			"don": r.custom_pancake_display_id or "",
			"diem": ten.get((r.vgb_quay or "").upper() or "SALES", r.vgb_quay or "Sales Online"),
			"viec": (
				"Huỷ bill nháp: %s" % (r.vgb_huy_ly_do or "không ghi lý do")
				if r.get("vgb_huy")
				else "Huỷ hoá đơn"
			),
			"nguoi": (r.get("vgb_huy_boi") or r.modified_by or ""),
			"tien": _tien(r.grand_total),
		}
		for r in huy
	]
	vet = frappe.get_all(
		"Comment",
		filters={
			"reference_doctype": "Sales Invoice",
			"comment_type": "Info",
			"creation": ["between", [str(tu) + " 00:00:00", str(den) + " 23:59:59"]],
		},
		fields=["reference_name", "content", "creation", "owner"],
		order_by="creation desc",
		limit_page_length=0,
	)
	for v in vet:
		noi_dung = re.sub(r"\s+", " ", v.content or "").strip()
		dong.append(
			{
				"ngay": str(v.creation)[:10],
				"hoa_don": v.reference_name,
				"don": "",
				"diem": "",
				"viec": noi_dung[:180],
				"nguoi": v.owner or "",
				"tien": 0,
			}
		)
	dong.sort(key=lambda x: x["ngay"], reverse=True)
	return {
		"cot": _cot(
			("ngay", "Ngày", "ngay"), ("hoa_don", "Mã phiếu", "chu"),
			("viec", "Việc đã làm", "chu"), ("nguoi", "Người thao tác", "chu"),
			("tien", "Số tiền", "tien"),
		),
		"dong": dong,
		"bieu_do": None,
	}


def _dong_hang(hd):
	"""Doc dong mon cua mot tap hoa don. Chia lo 400 cai mot de cau IN
	khong dai qua muc CSDL chiu duoc."""
	ten = [r.name for r in hd]
	ra = []
	for i in range(0, len(ten), 400):
		ra += frappe.get_all(
			"Sales Invoice Item",
			filters={"parent": ["in", ten[i:i + 400]]},
			fields=["parent", "item_code", "item_name", "item_group", "qty", "amount"],
			limit_page_length=0,
		)
	return ra


def _bc_mon_ban_chay(hd, **kw):
	"""BC08 - mon ban chay nhat trong ky."""
	gom = {}
	for r in _dong_hang(hd):
		o = gom.setdefault(
			r.item_code,
			{"ma_mon": r.item_code, "mon": r.item_name or r.item_code, "nhom": r.item_group or "", "sl": 0.0, "tien": 0.0},
		)
		o["sl"] += flt(r.qty)
		o["tien"] += _tien(r.amount)
	dong = sorted(gom.values(), key=lambda x: -x["sl"])
	return {
		"cot": _cot(
			("mon", "Món", "chu"), ("nhom", "Nhóm món", "chu"),
			("sl", "Số lượng bán", "so"), ("tien", "Doanh thu", "tien"),
		),
		"dong": dong,
		"bieu_do": {"nhan": "mon", "gia_tri": "sl", "so_dong": 12},
	}


def _bc_nhom_mon(hd, **kw):
	"""BC09 - nhom hang ban chay, de biet dong san pham nao keo doanh thu."""
	gom = {}
	for r in _dong_hang(hd):
		n = r.item_group or "(chưa xếp nhóm)"
		o = gom.setdefault(n, {"nhom": n, "sl": 0.0, "tien": 0.0, "so_mon": set()})
		o["sl"] += flt(r.qty)
		o["tien"] += _tien(r.amount)
		o["so_mon"].add(r.item_code)
	dong = sorted(gom.values(), key=lambda x: -x["tien"])
	tong = sum(o["tien"] for o in dong)
	for o in dong:
		o["so_mon"] = len(o["so_mon"])
		o["ty_le"] = (o["tien"] / tong * 100) if tong else 0
	return {
		"cot": _cot(
			("nhom", "Nhóm món", "chu"), ("so_mon", "Số mã món", "so"),
			("sl", "Số lượng bán", "so"), ("tien", "Doanh thu", "tien"),
			("ty_le", "Tỷ trọng", "phan_tram"),
		),
		"dong": dong,
		"bieu_do": {"nhan": "nhom", "gia_tri": "tien"},
	}


def _bc_gio_cao_diem(hd, **kw):
	"""BC10 - doanh thu theo khung gio, de xep ca va chuan bi banh.

	Don online khong co gio ban thuc su nen chi tinh don co gio ghi nhan.
	"""
	gom = {}
	for r in hd:
		gio = str(r.posting_time or "")[:2]
		if not gio.isdigit():
			continue
		k = "%02d:00" % int(gio)
		o = gom.setdefault(k, {"gio": k, "so_hd": 0, "tien": 0.0})
		o["so_hd"] += 1
		o["tien"] += _tien(r.grand_total)
	dong = sorted(gom.values(), key=lambda x: x["gio"])
	return {
		"cot": _cot(
			("gio", "Khung giờ", "chu"), ("so_hd", "Số hoá đơn", "so"),
			("tien", "Doanh thu", "tien"),
		),
		"dong": dong,
		"bieu_do": {"nhan": "gio", "gia_tri": "tien", "so_dong": 24},
	}


def _bc_khach_hang(hd, **kw):
	"""BC11 - khach chi tieu nhieu nhat va so con no."""
	gom = {}
	for r in hd:
		ma = r.vgb_khach_no or r.customer or ""
		ten = r.customer_name or ma
		if r.vgb_khach_no:
			ten = frappe.db.get_value("Customer", r.vgb_khach_no, "customer_name") or r.vgb_khach_no
		o = gom.setdefault(ma, {"khach": ten, "ma": ma, "so_hd": 0, "tien": 0.0, "con_no": 0.0})
		o["so_hd"] += 1
		o["tien"] += _tien(r.grand_total)
		o["con_no"] += _tien(r.outstanding_amount)
	dong = sorted(gom.values(), key=lambda x: -x["tien"])
	for o in dong:
		o["binh_quan"] = o["tien"] / o["so_hd"] if o["so_hd"] else 0
	return {
		"cot": _cot(
			("khach", "Khách hàng", "chu"), ("so_hd", "Số hoá đơn", "so"),
			("tien", "Tổng chi tiêu", "tien"), ("binh_quan", "Bình quân/hoá đơn", "tien"),
			("con_no", "Còn nợ", "tien"),
		),
		"dong": dong,
		"bieu_do": {"nhan": "khach", "gia_tri": "tien", "so_dong": 10},
	}


def _bc_thue(hd, **kw):
	"""BC12 - doanh thu truoc thue, thue dau ra va tong, cho ke toan."""
	gom = {}
	for r in hd:
		n = str(r.posting_date)
		o = gom.setdefault(n, {"ngay": n, "truoc_thue": 0.0, "thue": 0.0, "tong": 0.0, "so_hd": 0})
		o["truoc_thue"] += _tien(r.net_total)
		o["thue"] += _tien(r.total_taxes_and_charges)
		o["tong"] += _tien(r.grand_total)
		o["so_hd"] += 1
	dong = sorted(gom.values(), key=lambda x: x["ngay"])
	for o in dong:
		o["ngay_vn"] = getdate(o["ngay"]).strftime("%d/%m/%Y")
	return {
		"cot": _cot(
			("ngay_vn", "Ngày", "chu"), ("so_hd", "Số hoá đơn", "so"),
			("truoc_thue", "Doanh thu trước thuế", "tien"),
			("thue", "Thuế đầu ra", "tien"), ("tong", "Tổng thanh toán", "tien"),
		),
		"dong": dong,
		"bieu_do": {"nhan": "ngay_vn", "gia_tri": "tong"},
	}


def _bc_ke_hoa_don(hd, **kw):
	"""BC13 - bang ke chi tiet hoa don, moi hoa don mot dong.

	Day la bao cao ke toan mo nhieu nhat: doi chieu voi to khai, voi hoa don
	dien tu, voi sao ke ngan hang. Fabi goi la C03 va D07, ben minh gop lam
	mot vi hai cai do chi khac nhau vai cot."""
	ten = diem_ban.ten_diem()
	dong = []
	for r in hd:
		dong.append({
			"ngay": str(r.posting_date),
			"hoa_don": r.name,
			"ky_hieu": (r.custom_hddt_ky_hieu or "").strip(),
			"so_hddt": (r.custom_hddt_so or "").strip(),
			"don": r.custom_pancake_display_id or "",
			"diem": ten.get(_diem(r), _diem(r)),
			"nguon": (r.custom_nguon or "").strip(),
			"khach": r.customer_name or r.customer or "",
			"pt": (r.vgb_pt_thanh_toan or "").strip(),
			"truoc_thue": _tien(r.net_total),
			"giam": _tien(r.discount_amount),
			"thue": _tien(r.total_taxes_and_charges),
			"tong": _tien(r.grand_total),
			"con_no": _tien(r.outstanding_amount),
		})
	dong.sort(key=lambda x: (x["ngay"], x["hoa_don"]))
	return {
		"cot": _cot(
			("ngay", "Ngày", "ngay"), ("hoa_don", "Mã phiếu", "chu"),
			("ky_hieu", "Ký hiệu", "chu"), ("so_hddt", "Số HĐĐT", "chu"),
			("don", "Đơn", "chu"), ("diem", "Điểm bán", "chu"),
			("nguon", "Nguồn", "chu"), ("khach", "Khách hàng", "chu"),
			("pt", "Phương thức", "chu"),
			("truoc_thue", "Trước thuế", "tien"), ("giam", "Giảm giá", "tien"),
			("thue", "Thuế", "tien"), ("tong", "Tổng tiền", "tien"),
			("con_no", "Còn nợ", "tien"),
		),
		"dong": dong,
		"bieu_do": None,
	}


def _dong_hang_ct(hd):
	"""Dong mon kem don gia va don vi - ban day du hon _dong_hang."""
	ten = [r.name for r in hd]
	ra = []
	for i in range(0, len(ten), 400):
		ra += frappe.get_all(
			"Sales Invoice Item",
			filters={"parent": ["in", ten[i:i + 400]]},
			fields=[
				"parent", "idx", "item_code", "item_name", "item_group",
				"uom", "qty", "rate", "amount",
			],
			order_by="parent asc, idx asc",
			limit_page_length=0,
		)
	return ra


def _bc_ke_dong_mon(hd, **kw):
	"""BC14 - bang ke chi tiet toi tung dong mon tren tung hoa don.

	Day la du lieu THO. Co bang nay thi moi cau hoi kieu "thang 7 banh X
	ban duoc bao nhieu o District 1 qua GrabFood" deu tra loi duoc bang mot
	pivot trong Excel, khong phai viet them bao cao. Fabi tra loi kieu do
	bang bao cao ma tran 261 cot - cung ra so nhung cung nhac va nang may.

	Combo ben minh chi la ghi chu tren dong mon chu khong tach dong con gia
	0 dong nhu Fabi, nen khong co chuyen cong trung doanh thu."""
	ten = diem_ban.ten_diem()
	cha = {r.name: r for r in hd}
	dong = []
	for m in _dong_hang_ct(hd):
		r = cha.get(m.parent)
		if not r:
			continue
		dong.append({
			"ngay": str(r.posting_date),
			"hoa_don": m.parent,
			"diem": ten.get(_diem(r), _diem(r)),
			"nguon": (r.custom_nguon or "").strip(),
			"ma_mon": m.item_code,
			"mon": m.item_name or m.item_code,
			"nhom": m.item_group or "",
			"dvt": m.uom or "",
			"sl": flt(m.qty),
			"don_gia": _tien(m.rate),
			"thanh_tien": _tien(m.amount),
			"khach": r.customer_name or r.customer or "",
			"pt": (r.vgb_pt_thanh_toan or "").strip(),
		})
	return {
		"cot": _cot(
			("ngay", "Ngày", "ngay"), ("hoa_don", "Mã phiếu", "chu"),
			("diem", "Điểm bán", "chu"), ("nguon", "Nguồn", "chu"),
			("ma_mon", "Mã hàng", "chu"), ("mon", "Tên hàng", "chu"),
			("nhom", "Nhóm món", "chu"), ("dvt", "Đơn vị", "chu"),
			("sl", "Số lượng", "so"), ("don_gia", "Đơn giá", "tien", True),
			("thanh_tien", "Thành tiền", "tien"),
			("khach", "Khách hàng", "chu"), ("pt", "Phương thức", "chu"),
		),
		"dong": dong,
		"bieu_do": None,
	}


def _bc_tien_ve_ngay(hd, **kw):
	"""BC15 - moi ngay thu ve bao nhieu, tach theo tung phuong thuc.

	Dung de doi ket cuoi ngay: cot Tien mat phai bang so dem duoc trong
	ket, cot Chuyen khoan phai bang sao ke SePay.

	Cot phuong thuc sinh DONG theo nhung phuong thuc that su co phat sinh
	trong ky, khong cai cung danh sach: them mot vi dien moi trong Cai dat
	la bao cao tu co them cot, khong phai sua ma nguon."""
	pts = sorted({(r.vgb_pt_thanh_toan or "").strip() or "(chưa chọn)" for r in hd})
	khoa = {p: "pt%d" % i for i, p in enumerate(pts)}
	gom = {}
	for r in hd:
		n = str(r.posting_date)
		o = gom.get(n)
		if not o:
			o = {"ngay": n, "so_hd": 0, "tong": 0.0}
			for p in pts:
				o[khoa[p]] = 0.0
			gom[n] = o
		p = (r.vgb_pt_thanh_toan or "").strip() or "(chưa chọn)"
		o["so_hd"] += 1
		o["tong"] += _tien(r.grand_total)
		o[khoa[p]] += _tien(r.grand_total)
	dong = sorted(gom.values(), key=lambda x: x["ngay"])
	for o in dong:
		o["ngay_vn"] = getdate(o["ngay"]).strftime("%d/%m")
	cot = [{"k": "ngay_vn", "nhan": "Ngày", "kieu": "chu"},
		   {"k": "so_hd", "nhan": "Số hoá đơn", "kieu": "so"}]
	for p in pts:
		cot.append({"k": khoa[p], "nhan": p, "kieu": "tien"})
	cot.append({"k": "tong", "nhan": "Tổng tiền về", "kieu": "tien"})
	return {
		"cot": cot,
		"dong": dong,
		"bieu_do": {"nhan": "ngay_vn", "gia_tri": "tong"},
	}


def _bc_ke_thanh_toan(hd, **kw):
	"""BC16 - bang ke thanh toan kem ma tham chieu, de khop sao ke.

	BC04 chi cho biet ca ky thu duoc bao nhieu tien chuyen khoan. Khi so
	tien lech so voi sao ke thi BC04 khong giup gi vi khong truy duoc lech
	o giao dich nao - bang ke nay moi truy duoc.

	Cot canh bao chi ra ma tham chieu bi dung cho hai hoa don khac nhau
	trong cung ky: hoac go nham, hoac mot lan chuyen khoan bi gach cho hai
	don."""
	ten = diem_ban.ten_diem()
	dem = {}
	for r in hd:
		m = (r.vgb_ma_tham_chieu or "").strip().upper()
		if m:
			dem[m] = dem.get(m, 0) + 1
	dong = []
	for r in hd:
		m = (r.vgb_ma_tham_chieu or "").strip()
		canh = ""
		if m and dem.get(m.upper(), 0) > 1:
			canh = "Mã dùng %d lần" % dem[m.upper()]
		elif not m and (r.vgb_pt_thanh_toan or "").strip() in ("Chuyển khoản", "Thẻ"):
			canh = "Thiếu mã tham chiếu"
		dong.append({
			"ngay": str(r.posting_date),
			"hoa_don": r.name,
			"don": r.custom_pancake_display_id or "",
			"diem": ten.get(_diem(r), _diem(r)),
			"pt": (r.vgb_pt_thanh_toan or "").strip() or "(chưa chọn)",
			"ma_tc": m,
			"tong": _tien(r.grand_total),
			"con_no": _tien(r.outstanding_amount),
			"canh_bao": canh,
		})
	# Dong co canh bao len dau: mo bao cao ra la thay ngay cho phai soi.
	dong.sort(key=lambda x: (0 if x["canh_bao"] else 1, x["ngay"], x["hoa_don"]))
	return {
		"cot": _cot(
			("ngay", "Ngày", "ngay"), ("hoa_don", "Mã phiếu", "chu"),
			("don", "Đơn", "chu"), ("diem", "Điểm bán", "chu"),
			("pt", "Phương thức", "chu"), ("ma_tc", "Mã tham chiếu", "chu"),
			("tong", "Số tiền", "tien"), ("con_no", "Còn nợ", "tien"),
			("canh_bao", "Cảnh báo", "chu"),
		),
		"dong": dong,
		"bieu_do": None,
	}


DANH_SACH = [
	{"ma": "BC01", "ten": "Tổng doanh thu", "ic": "💰", "mo": "Tổng doanh thu ba điểm bán, tỷ trọng từng nơi", "ham": _bc_tong_doanh_thu, "nhom": "Doanh thu", "ss": "khoa"},
	{"ma": "BC02", "ten": "Doanh thu theo ngày", "ic": "📈", "mo": "Đường doanh thu từng ngày trong kỳ", "ham": _bc_theo_ngay, "nhom": "Doanh thu", "ss": "vi_tri"},
	{"ma": "BC03", "ten": "Doanh thu theo nguồn đơn", "ic": "🛵", "mo": "Tại chỗ, Sales Online, GrabFood, ShopeeFood, BeFood, GreenSM...", "ham": _bc_nguon_don, "nhom": "Doanh thu", "ss": "khoa"},
	{"ma": "BC04", "ten": "Phương thức thanh toán", "ic": "💳", "mo": "Tiền mặt, chuyển khoản, thẻ, ví, công nợ", "ham": _bc_thanh_toan, "nhom": "Doanh thu", "ss": "khoa"},
	{"ma": "BC05", "ten": "Đối soát hoá đơn điện tử", "ic": "🧾", "mo": "Chờ ký, đã ký, CQT chấp nhận, chưa xuất", "ham": _bc_hddt, "nhom": "Kế toán", "ss": "khoa"},
	{"ma": "BC06", "ten": "Chương trình khuyến mãi", "ic": "🎫", "mo": "Số lượt dùng và tiền đã giảm từng chương trình", "ham": _bc_khuyen_mai, "nhom": "Kiểm soát", "ss": "khoa"},
	{"ma": "BC07", "ten": "Sửa và huỷ hoá đơn", "ic": "✂️", "mo": "Ai sửa, ai huỷ, làm gì trên hoá đơn nào", "ham": _bc_sua_huy, "nhom": "Kiểm soát", "ss": None},
	{"ma": "BC08", "ten": "Món bán chạy", "ic": "🍰", "mo": "Xếp hạng theo số lượng bán ra", "ham": _bc_mon_ban_chay, "nhom": "Hàng hoá", "ss": "khoa"},
	{"ma": "BC09", "ten": "Nhóm món bán chạy", "ic": "🗂️", "mo": "Dòng sản phẩm nào kéo doanh thu", "ham": _bc_nhom_mon, "nhom": "Hàng hoá", "ss": "khoa"},
	{"ma": "BC10", "ten": "Giờ cao điểm", "ic": "⏰", "mo": "Doanh thu theo khung giờ, dùng để xếp ca", "ham": _bc_gio_cao_diem, "nhom": "Vận hành", "ss": "khoa"},
	{"ma": "BC11", "ten": "Khách hàng chi tiêu nhiều", "ic": "👑", "mo": "Xếp hạng khách và số còn nợ", "ham": _bc_khach_hang, "nhom": "Khách hàng", "ss": "khoa"},
	{"ma": "BC12", "ten": "Doanh thu và thuế đầu ra", "ic": "🏛️", "mo": "Trước thuế, thuế, tổng - dùng khai thuế", "ham": _bc_thue, "nhom": "Kế toán", "ss": "vi_tri"},
	{"ma": "BC13", "ten": "Bảng kê chi tiết hoá đơn", "ic": "📄", "mo": "Mỗi hoá đơn một dòng, đủ cột để đối chiếu tờ khai", "ham": _bc_ke_hoa_don, "nhom": "Kế toán", "ss": None},
	{"ma": "BC14", "ten": "Bảng kê chi tiết theo dòng món", "ic": "🧮", "mo": "Dữ liệu thô từng món trên từng hoá đơn, để pivot trong Excel", "ham": _bc_ke_dong_mon, "nhom": "Kế toán", "ss": None},
	{"ma": "BC15", "ten": "Tiền về theo ngày", "ic": "🧺", "mo": "Mỗi ngày thu bao nhiêu theo từng phương thức, dùng đối két", "ham": _bc_tien_ve_ngay, "nhom": "Kiểm soát", "ss": "vi_tri"},
	{"ma": "BC16", "ten": "Bảng kê thanh toán và mã tham chiếu", "ic": "🔗", "mo": "Khớp từng giao dịch với sao kê, chỉ ra mã trùng và mã thiếu", "ham": _bc_ke_thanh_toan, "nhom": "Kế toán", "ss": None},
]
THEO_MA = {b["ma"]: b for b in DANH_SACH}


# ---------------------------------------------------------------------- API

def _ss_tong(ky, t, d, tong, so_hd, diem=None, nguon=None, pt=None):
	"""Khoi so sanh voi ky truoc: tong tien, so hoa don va phan tram chenh.

	Ky truoc bang khong ma ky nay co tien thi khong chia duoc, tra ve None
	de man hinh hien "khong co ky truoc de so" thay vi mot con so vo nghia
	kieu +100% hay vo cuc."""
	tt, dd = _ky_truoc(ky, t, d)
	hd2 = _hoa_don(tt, dd, diem=diem, nguon=nguon, pt=pt)
	tong2 = sum(_tien(r.grand_total) for r in hd2)
	return {
		"nhan_ky": _nhan_ky(ky, tt, dd),
		"tu": str(tt),
		"den": str(dd),
		"tong_doanh_thu": tong2,
		"so_hoa_don": len(hd2),
		"chenh": ((tong - tong2) / tong2 * 100) if tong2 else None,
		"chenh_hd": ((so_hd - len(hd2)) / len(hd2) * 100) if hd2 else None,
	}


@frappe.whitelist()
def danh_sach(ky="ngay", moc=None, tu=None, den=None, diem=None, ss=0):
	"""Man chinh cua phan he: danh sach bao cao kem con so tong de nhin
	phat la biet ngay hom nay ban duoc bao nhieu."""
	_kiem_quyen()
	t, d = khoang_ngay(ky, moc, tu, den)
	hd = _hoa_don(t, d, diem=diem)
	tong = sum(_tien(r.grand_total) for r in hd)
	theo_diem = {}
	for r in hd:
		theo_diem[_diem(r)] = theo_diem.get(_diem(r), 0.0) + _tien(r.grand_total)
	return {
		"ky": ky,
		"tu": str(t),
		"den": str(d),
		"nhan_ky": _nhan_ky(ky, t, d),
		"tong_doanh_thu": tong,
		"so_hoa_don": len(hd),
		"binh_quan": tong / len(hd) if hd else 0,
		"ss": _ss_tong(ky, t, d, tong, len(hd), diem=diem) if int(ss or 0) else None,
		"diem_ban": [
			{"ma": x["ma"], "ten": x["ten"], "dia_chi": x["dia_chi"], "tien": theo_diem.get(x["ma"], 0.0)}
			for x in _diem_ban()
		],
		"bao_cao": [
			{"ma": b["ma"], "ten": b["ten"], "ic": b["ic"], "mo": b["mo"], "nhom": b["nhom"]}
			for b in DANH_SACH
		],
	}


@frappe.whitelist()
def chay(ma, ky="ngay", moc=None, tu=None, den=None, diem=None, nguon=None, pt=None, ss=0, day_du=0):
	"""Chay mot bao cao. Moi bao cao deu tra ve cung mot hinh dang de man
	hinh chi phai viet mot lan.

	ss=1 thi chay them mot lan nua cho ky truoc roi gan them hai cot "Ky
	truoc" va "Chenh" vao cuoi bang. Lam o day chu khong lam trong tung
	bao cao, nho vay MOI bao cao deu co so sanh ma khong phai sua ham nao.

	day_du=1 thi khong cat bot dong - chi dung khi xuat Excel."""
	_kiem_quyen()
	b = THEO_MA.get((ma or "").strip().upper())
	if not b:
		frappe.throw("Không có báo cáo mã %s." % ma)
	t, d = khoang_ngay(ky, moc, tu, den)
	hd = _hoa_don(t, d, diem=diem, nguon=nguon, pt=pt)
	kq = b["ham"](hd, tu=t, den=d)
	tong = sum(_tien(r.grand_total) for r in hd)
	cot = list(kq["cot"])
	dong = kq["dong"]

	khoi_ss = None
	if int(ss or 0):
		khoi_ss = _ss_tong(ky, t, d, tong, len(hd), diem=diem, nguon=nguon, pt=pt)
		chinh = _cot_chinh(kq)
		if b.get("ss") and chinh and dong:
			tt, dd = _ky_truoc(ky, t, d)
			kq2 = b["ham"](
				_hoa_don(tt, dd, diem=diem, nguon=nguon, pt=pt), tu=tt, den=dd
			)
			if b["ss"] == "vi_tri":
				# Bao cao xep theo ngay: khoa hai ky khac nhau nen khong doi
				# duoc theo khoa, phai doi theo thu tu - ngay thu nhat cua
				# thang nay voi ngay thu nhat cua thang truoc.
				truoc = [flt(r.get(chinh["k"]) or 0) for r in kq2["dong"]]
				for i, r in enumerate(dong):
					r["_truoc"] = truoc[i] if i < len(truoc) else 0.0
			else:
				k0 = cot[0]["k"]
				bang = {
					str(r.get(k0)): flt(r.get(chinh["k"]) or 0) for r in kq2["dong"]
				}
				for r in dong:
					r["_truoc"] = bang.get(str(r.get(k0)), 0.0)
			for r in dong:
				truoc_r = flt(r.get("_truoc") or 0)
				nay = flt(r.get(chinh["k"]) or 0)
				if truoc_r:
					r["_chenh"] = (nay - truoc_r) / truoc_r * 100
				elif nay:
					# Ky truoc khong co dong nay ma ky nay co: dong moi,
					# khong chia duoc. Man hinh in chu "mới".
					r["_chenh"] = None
				else:
					# Ca hai ky deu bang 0 - khong tang khong giam, chu
					# khong phai "moi". Diem ban dong cua nam ca hai ky
					# deu roi vao truong hop nay.
					r["_chenh"] = 0.0
			cot = cot + [
				{"k": "_truoc", "nhan": "Kỳ trước", "kieu": chinh["kieu"]},
				{"k": "_chenh", "nhan": "Chênh", "kieu": "phan_tram"},
			]

	# Cong tong tung cot tien va cot so, de dong TONG duoi bang luon dung
	# voi phan da loc chu khong phai con so co dinh. Cong TRUOC khi cat
	# dong, neu khong dong tong se chi la tong cua phan dang hien.
	cong = {}
	for c in cot:
		if c["kieu"] in ("tien", "so") and not c.get("kc"):
			cong[c["k"]] = sum(flt(r.get(c["k"]) or 0) for r in dong)

	tong_dong = len(dong)
	bi_cat = 0
	if not int(day_du or 0) and tong_dong > GIOI_HAN_DONG:
		dong = dong[:GIOI_HAN_DONG]
		bi_cat = 1

	return {
		"ma": b["ma"],
		"ten": b["ten"],
		"ic": b["ic"],
		"mo": b["mo"],
		"nhan_ky": _nhan_ky(ky, t, d),
		"tu": str(t),
		"den": str(d),
		"tong_doanh_thu": tong,
		"so_hoa_don": len(hd),
		"cot": cot,
		"dong": dong,
		"cong": cong,
		"tong_dong": tong_dong,
		"bi_cat": bi_cat,
		"gioi_han": GIOI_HAN_DONG,
		"ss": khoi_ss,
		"co_ss_dong": 1 if b.get("ss") else 0,
		"bieu_do": kq.get("bieu_do"),
		"phu": kq.get("phu"),
		"nguon_loc": sorted({(r.custom_nguon or "").strip() for r in hd if (r.custom_nguon or "").strip()}),
		"pt_loc": sorted({(r.vgb_pt_thanh_toan or "").strip() for r in hd if (r.vgb_pt_thanh_toan or "").strip()}),
	}


@frappe.whitelist()
def xuat_excel(ma, ky="ngay", moc=None, tu=None, den=None, diem=None, nguon=None, pt=None, ss=0):
	"""Xuat bao cao ra file Excel that (.xlsx) cho ke toan.

	Tra ve chuoi base64 chu khong ghi file len may chu: bao cao la so lieu
	song, luu file lai chi to cho nham lan giua ban cu va ban moi.

	day_du=1: file Excel luon co DU dong ke ca khi man hinh da cat bot.
	"""
	_kiem_quyen()
	kq = chay(
		ma, ky=ky, moc=moc, tu=tu, den=den, diem=diem, nguon=nguon, pt=pt,
		ss=ss, day_du=1,
	)
	bang = [
		["%s - %s" % (kq["ma"], kq["ten"])],
		[kq["nhan_ky"]],
		["Tổng doanh thu", kq["tong_doanh_thu"], "Số hoá đơn", kq["so_hoa_don"]],
	]
	if kq.get("ss"):
		bang.append([
			"So với %s" % kq["ss"]["nhan_ky"], kq["ss"]["tong_doanh_thu"],
			"Số hoá đơn", kq["ss"]["so_hoa_don"],
		])
	bang += [
		[],
		[c["nhan"] for c in kq["cot"]],
	]
	for r in kq["dong"]:
		bang.append([r.get(c["k"]) for c in kq["cot"]])
	if kq.get("cong"):
		dong_tong = ["TỔNG"]
		for c in kq["cot"][1:]:
			dong_tong.append(kq["cong"].get(c["k"], ""))
		bang.append(dong_tong)
	if kq.get("phu"):
		bang.append([])
		bang.append([kq["phu"]["tieu_de"]])
		bang.append([c["nhan"] for c in kq["phu"]["cot"]])
		for r in kq["phu"]["dong"]:
			bang.append([r.get(c["k"]) for c in kq["phu"]["cot"]])

	from frappe.utils.xlsxutils import make_xlsx

	tep = make_xlsx(bang, kq["ma"])
	noi_dung = tep.getvalue() if isinstance(tep, io.BytesIO) else tep
	return {
		"ten_file": "%s-%s-%s.xlsx" % (kq["ma"], kq["tu"], kq["den"]),
		"b64": base64.b64encode(noi_dung).decode(),
	}

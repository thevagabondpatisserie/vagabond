"""Xac nhan nhan hang dieu chuyen - anh Viet chot phuong an A ngay 02/09/2026.

Bai toan
--------
Phieu dieu chuyen noi bo ghi so MOT BUOC ben kho xuat: Kien bam chuyen la
hang vao kho bep ngay lap tuc trong so. Bep khong co cho nao de noi "em chi
nhan duoc 8 tren 10". Khi kiem ke ra thieu thi Kho va Bep cai nhau, va
khong ben nao co bang chung.

Ba phuong an da trinh anh Viet ngay 18/08, anh chon A:

  A  Xac nhan CO GHI VET, chua dung but toan. Bep bam Da nhan du hoac Nhan
     thieu kem so thuc nhan va ly do. So kho khong doi. Phan thieu treo
     thanh viec can lam cho thu kho doi chieu.
  B  Hai buoc qua kho Hang dang di duong. Dung chuan ke toan kho nhat,
     nhung bep phai cho co nguoi xac nhan moi co nguyen lieu de dung.
  C  Giu mot buoc, nhan thieu thi lap phieu xuat huy cho phan thieu. Don
     gian nhung do oan cho bep: phan hao hut van dung ten bep chu khong
     phai ten khau van chuyen.

VI SAO A KHONG DUNG TOI SO KHO
------------------------------
Day la cho de hieu nham nhat cua man nay, nen viet ro mot lan.

Bam "Nhan thieu 8 tren 10" KHONG lam ton kho bep giam di 2. So kho van ghi
day du 10 nhu phieu dieu chuyen da ghi. Cai man nay ghi lai la MOT LOI KHAI:
nguoi nhan noi rang ho chi thay 8.

Co y nhu vay. Lech giua so giao va so nhan co the do ba nguyen nhan hoan
toan khac nhau: kho xuat soan thieu, mat tren duong di, hoac nguoi nhan dem
sot. Ba nguyen nhan do ghi vao ba cho khac nhau trong so ke toan. May khong
biet la cai nao, va doan bua thi ghi sai so. Nen may chi ghi lai loi khai
roi treo thanh viec cho thu kho doi chieu; nguoi doi chieu xong moi biet
phai lap phieu gi.

Chay mot thang la co so that de biet chuyen nhan thieu co that khong va
thuong xuyen toi dau, roi moi quyet co len phuong an B hay khong.
"""

import json

import frappe
from frappe.utils import cint, flt, now_datetime

from vagabond import xuat_kho

# Sai so cho phep khi so sanh so luong. Gram va ml deu co phan le nen so
# sanh bang dau bang tran la sai.
EPS = 0.0001

DU = "Đã nhận đủ"
THIEU = "Nhận thiếu"

TRUONG_MOI = {
	"Stock Entry": [
		{
			"fieldname": "vgb_nhan_tt",
			"label": "Người nhận xác nhận",
			"fieldtype": "Select",
			"options": "\n%s\n%s" % (DU, THIEU),
			"read_only": 1,
			"insert_after": "to_warehouse",
			"description": (
				"Kho nhận đã bấm xác nhận chưa. Ô này KHÔNG đụng tới sổ kho, "
				"nó chỉ ghi lại lời khai của người nhận."
			),
		},
		{
			"fieldname": "vgb_nhan_boi",
			"label": "Người xác nhận",
			"fieldtype": "Data",
			"read_only": 1,
			"insert_after": "vgb_nhan_tt",
		},
		{
			"fieldname": "vgb_nhan_luc",
			"label": "Xác nhận lúc",
			"fieldtype": "Datetime",
			"read_only": 1,
			"insert_after": "vgb_nhan_boi",
		},
		{
			"fieldname": "vgb_nhan_ghi_chu",
			"label": "Ghi chú của người nhận",
			"fieldtype": "Small Text",
			"insert_after": "vgb_nhan_luc",
		},
		{
			"fieldname": "vgb_nhan_da_xu_ly",
			"label": "Thủ kho đã đối chiếu phần thiếu",
			"fieldtype": "Check",
			"default": "0",
			"insert_after": "vgb_nhan_ghi_chu",
			"description": (
				"Bật lên khi thủ kho đã tìm ra phần thiếu đi đâu. Phiếu nào "
				"chưa bật thì còn treo trong màn Việc cần làm."
			),
		},
	],
	"Stock Entry Detail": [
		{
			"fieldname": "vgb_sl_nhan",
			"label": "SL người nhận đếm được",
			"fieldtype": "Float",
			"read_only": 1,
			"insert_after": "qty",
			"precision": "3",
			"description": (
				"Số người nhận đếm được thật. Để trống là chưa xác nhận. Ô này "
				"KHÔNG thay số lượng đã ghi sổ."
			),
		}
	],
}


# ------------------------------------------------------------- phần thuần


def lech_mot_dong(sl_giao, sl_nhan):
	"""Lech cua mot dong: giao tru nhan. Ham THUAN.

	So DUONG la nhan thieu, so AM la nhan thua. Nhan thua nghe la doi nhung
	co that: kho xuat soan du mot goi ma khong sua phieu.
	"""
	return flt(sl_giao) - flt(sl_nhan)


def co_lech(sl_giao, sl_nhan):
	"""Hai so nay co khac nhau khong. Ham THUAN.

	So bang EPS chu khong bang dau bang tran: 1.9999999 va 2.0 la cung mot
	so trong doi that, nhung dau bang noi la khac.
	"""
	return abs(lech_mot_dong(sl_giao, sl_nhan)) > EPS


def trang_thai_tu_cac_dong(cac_dong):
	"""Xac nhan nay la Da nhan du hay Nhan thieu. Ham THUAN.

	Vao: danh sach {"giao": ..., "nhan": ...}. Chi can MOT dong lech la ca
	phieu mang nhan Nhan thieu - phieu dung mot phan van la phieu phai doi
	chieu.
	"""
	for d in cac_dong or []:
		if co_lech(d.get("giao"), d.get("nhan")):
			return THIEU
	return DU


def cac_dong_lech(cac_dong):
	"""Chi nhung dong co lech, kem so lech. Ham THUAN.

	Dung de viet cau bao cho thu kho: "thieu 2 NVLT00231, thua 1 BPKG00007"
	doc nhanh hon la ca bang.
	"""
	ra = []
	for d in cac_dong or []:
		l = lech_mot_dong(d.get("giao"), d.get("nhan"))
		if abs(l) > EPS:
			ra.append(
				{
					"ma": d.get("ma") or "",
					"ten": d.get("ten") or "",
					"giao": flt(d.get("giao")),
					"nhan": flt(d.get("nhan")),
					"lech": l,
				}
			)
	return ra


def doc_so_nhan(dong, giao_theo_ma):
	"""Doc va kiem so nguoi nhan go. Ham THUAN.

	Tra ve (dict {ma: so nhan}, danh sach cau loi).

	Hai luat:
	- So nhan khong duoc AM. Go so am la go nham dau, khong phai y dinh.
	- Ma khong co trong phieu thi BO QUA, khong nem loi: may khach cu cach
	  mot ban co the gui len ma da bi go khoi phieu.

	Nhan NHIEU hon so giao thi cho qua, co y. Nhan thua la chuyen co that
	khi kho xuat soan du ma khong sua phieu, va chan lai chi khien nguoi ta
	go bua mot con so cho qua man.
	"""
	if isinstance(dong, str):
		dong = json.loads(dong or "[]")
	ra = {}
	loi = []
	for d in dong or []:
		ma = (d.get("ma") or d.get("item_code") or "").strip()
		if not ma or ma not in giao_theo_ma:
			continue
		sl = flt(d.get("nhan") if d.get("nhan") is not None else d.get("sl"))
		if sl < -EPS:
			loi.append("%s nhận %s, số nhận không được âm" % (ma, sl))
			continue
		ra[ma] = sl
	return ra, loi


def cau_bao_lech(cac_lech):
	"""Cau mot dong mo ta phan lech, de treo len viec can lam. Ham THUAN."""
	if not cac_lech:
		return ""
	phan = []
	for d in cac_lech[:4]:
		l = flt(d.get("lech"))
		phan.append(
			"%s %s %s"
			% ("thiếu" if l > 0 else "thừa", _so(abs(l)), d.get("ma") or "")
		)
	cau = ", ".join(phan)
	if len(cac_lech) > 4:
		cau += " và %d dòng nữa" % (len(cac_lech) - 4)
	return cau


def _so(v):
	"""So luong in ra cho nguoi doc: bo duoi .0 thua. Ham THUAN."""
	v = flt(v)
	return str(int(v)) if abs(v - int(v)) < EPS else ("%.3f" % v).rstrip("0").rstrip(".")


# ------------------------------------------------ phần chạm Frappe


def _kho_cua_toi():
	return xuat_kho._kho_phu_trach()


@frappe.whitelist()
def dong_de_nhan(phieu=None):
	"""Cac dong cua mot phieu dieu chuyen, kem so da xac nhan neu co.

	Chi mo cho nguoi phu trach KHO NHAN cua phieu do. Ai cung xac nhan ho
	duoc thi chu ky khong con nghia gi.
	"""
	xuat_kho._duoc_xuat()
	if not phieu or not frappe.db.exists("Stock Entry", phieu):
		frappe.throw("Không tìm thấy phiếu %s." % (phieu or "(trống)"))
	doc = frappe.get_doc("Stock Entry", phieu)
	_chan_khong_phai_kho_nhan(doc)
	return {
		"phieu": doc.name,
		"ngay": str(doc.posting_date),
		"kho_xuat": doc.from_warehouse or "",
		"kho_nhan": doc.to_warehouse or "",
		"da_xac_nhan": doc.get("vgb_nhan_tt") or "",
		"nhan_boi": doc.get("vgb_nhan_boi") or "",
		"nhan_luc": str(doc.get("vgb_nhan_luc") or ""),
		"nhan_ghi_chu": doc.get("vgb_nhan_ghi_chu") or "",
		"dong": [
			{
				"ma": d.item_code,
				"ten": d.item_name,
				"dvt": d.uom,
				"giao": flt(d.qty),
				# Chua xac nhan thi dien SAN bang so giao, de nguoi nhan chi
				# phai sua dong nao thuc su lech. Bat go lai ca bang la cach
				# chac chan nhat de khong ai dung man nay.
				"nhan": flt(d.get("vgb_sl_nhan")) if d.get("vgb_sl_nhan") is not None else flt(d.qty),
			}
			for d in doc.items
		],
	}


def _chan_khong_phai_kho_nhan(doc):
	if doc.purpose != xuat_kho.LOAI["chuyen"]:
		frappe.throw("Phiếu %s không phải phiếu điều chuyển nội bộ." % doc.name)
	if cint(doc.docstatus) != 1:
		frappe.throw("Phiếu %s chưa ghi sổ nên chưa có hàng để nhận." % doc.name)
	cua_toi = _kho_cua_toi()
	if not cua_toi:
		frappe.throw(
			"Tài khoản của bạn chưa khai Kho phụ trách nên máy chưa biết bạn "
			"nhận hàng về kho nào. Báo anh Việt khai giúp ở màn Quản lý người dùng."
		)
	if doc.to_warehouse not in cua_toi:
		frappe.throw(
			"Phiếu này chuyển về kho %s, không phải kho bạn phụ trách. Chỉ người "
			"nhận hàng mới xác nhận được." % (doc.to_warehouse or "(trống)")
		)


@frappe.whitelist()
def xac_nhan(phieu=None, dong=None, ghi_chu=None):
	"""Nguoi nhan khai so thuc nhan.

	KHONG dung toi so kho. Xem doan dai o dau tep de biet vi sao.
	"""
	xuat_kho._duoc_xuat()
	if not phieu or not frappe.db.exists("Stock Entry", phieu):
		frappe.throw("Không tìm thấy phiếu %s." % (phieu or "(trống)"))
	doc = frappe.get_doc("Stock Entry", phieu)
	_chan_khong_phai_kho_nhan(doc)
	if (doc.get("vgb_nhan_tt") or "").strip():
		frappe.throw(
			"Phiếu %s đã được %s xác nhận rồi. Khai sai thì báo thủ kho, đừng "
			"xác nhận đè lên." % (doc.name, doc.get("vgb_nhan_boi") or "người khác")
		)

	giao_theo_ma = {d.item_code: flt(d.qty) for d in doc.items}
	so_nhan, loi = doc_so_nhan(dong, giao_theo_ma)
	if loi:
		frappe.throw("Số nhận không hợp lệ: %s." % "; ".join(loi))

	cac_dong = []
	for d in doc.items:
		nhan = so_nhan.get(d.item_code, flt(d.qty))
		cac_dong.append(
			{"ma": d.item_code, "ten": d.item_name, "giao": flt(d.qty), "nhan": nhan}
		)
	tt = trang_thai_tu_cac_dong(cac_dong)
	lech = cac_dong_lech(cac_dong)

	# Ghi bang db.set_value chu KHONG mo doc.save(): phieu da ghi so, goi
	# save() tren mot chung tu docstatus 1 la Frappe nem loi hoac de ra mot
	# ban sua doi khong ai muon. Cac o nay deu la o ghi vet, khong phai o
	# nghiep vu, nen ghi thang la dung.
	for d in doc.items:
		frappe.db.set_value(
			"Stock Entry Detail",
			d.name,
			"vgb_sl_nhan",
			so_nhan.get(d.item_code, flt(d.qty)),
			update_modified=False,
		)
	frappe.db.set_value(
		"Stock Entry",
		doc.name,
		{
			"vgb_nhan_tt": tt,
			"vgb_nhan_boi": frappe.session.user,
			"vgb_nhan_luc": now_datetime(),
			"vgb_nhan_ghi_chu": (ghi_chu or "").strip(),
		},
		update_modified=False,
	)
	_ghi_vet(doc.name, tt, lech, ghi_chu)
	frappe.db.commit()
	return {
		"ok": 1,
		"name": doc.name,
		"trang_thai": tt,
		"lech": lech,
		"cau_lech": cau_bao_lech(lech),
	}


def _ghi_vet(name, tt, lech, ghi_chu):
	"""Ai khai gi luc nao. Hong ghi vet khong duoc chan viec xac nhan."""
	try:
		noi = "Người nhận xác nhận: %s" % tt
		cau = cau_bao_lech(lech)
		if cau:
			noi += " (%s)" % cau
		if (ghi_chu or "").strip():
			noi += ". Ghi chú: %s" % ghi_chu.strip()
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": "Stock Entry",
				"reference_name": name,
				"content": "%s - %s" % (noi, frappe.session.user),
			}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "nhan_dieu_chuyen: ghi vet %s" % name)


@frappe.whitelist()
def da_doi_chieu(phieu=None, ghi_chu=None):
	"""Thu kho danh dau da tim ra phan thieu di dau - go phieu khoi viec cho."""
	if not xuat_kho.duoc_duyet():
		frappe.throw("Chỉ quản lý kho mới đánh dấu đã đối chiếu được.")
	if not phieu or not frappe.db.exists("Stock Entry", phieu):
		frappe.throw("Không tìm thấy phiếu %s." % (phieu or "(trống)"))
	frappe.db.set_value(
		"Stock Entry", phieu, "vgb_nhan_da_xu_ly", 1, update_modified=False
	)
	_ghi_vet(phieu, "Thủ kho đã đối chiếu phần thiếu", [], ghi_chu)
	frappe.db.commit()
	return {"ok": 1, "name": phieu}


@frappe.whitelist()
def phieu_lech_cho_xu_ly(gioi_han=40):
	"""Cac phieu nhan thieu ma thu kho chua doi chieu xong.

	Man Viec can lam doc cua nay. Tach ra thanh mot cua rieng chu khong nhet
	vao `viec_can_lam` de sau nay bao cao hao hut van chuyen dung lai duoc.
	"""
	xuat_kho._duoc_xuat()
	ds = frappe.get_all(
		"Stock Entry",
		filters={
			"purpose": xuat_kho.LOAI["chuyen"],
			"docstatus": 1,
			"vgb_nhan_tt": THIEU,
			"vgb_nhan_da_xu_ly": 0,
		},
		fields=[
			"name",
			"posting_date",
			"from_warehouse",
			"to_warehouse",
			"vgb_nhan_boi",
			"vgb_nhan_luc",
			"vgb_nhan_ghi_chu",
		],
		order_by="vgb_nhan_luc desc",
		limit_page_length=int(gioi_han or 40),
	)
	for d in ds:
		dong = frappe.get_all(
			"Stock Entry Detail",
			filters={"parent": d.name, "parenttype": "Stock Entry"},
			fields=["item_code", "item_name", "qty", "vgb_sl_nhan"],
			limit_page_length=0,
		)
		lech = cac_dong_lech(
			[
				{
					"ma": x.item_code,
					"ten": x.item_name,
					"giao": x.qty,
					"nhan": x.vgb_sl_nhan if x.vgb_sl_nhan is not None else x.qty,
				}
				for x in dong
			]
		)
		d["lech"] = lech
		d["cau_lech"] = cau_bao_lech(lech)
	return ds

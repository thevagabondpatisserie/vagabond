"""So NHAN BANH cua cua hang: bep giao bao nhieu, quay nhan bao nhieu.

Vi sao co tep nay
-----------------
Anh Viet 23/08/2026: moi ngay cua hang D1 phai tu go mot bang Excel roi chup
gui vao nhom Zalo WAREHOUSE. Bang do co hai cot: TON DAU va NHAP SANG, doi
khi them vai dot nua trong ngay. Go tay, chup anh, khong ai tra cuu duoc, va
so nam ngoai he thong.

Vi sao KHONG dung phieu nhap kho that (chot voi anh Viet 23/08/2026)
-------------------------------------------------------------------
Duong "dung chuan" la sinh Stock Entry nhap kho vao Kho D1. Da soi ky roi va
CHUA di duoc, vi ba chuyen:

  1. 20 tren 46 mon nhom Banh nuong chua co gia von. ERPNext v16 chan thang
     khi ghi so: "Valuation Rate for the Item ... is required to do accounting
     entries" (erpnext/stock/stock_ledger.py). Gia von cua banh von sinh ra
     tu chinh lenh san xuat, ma BOM thi chua xong.
  2. Bat co "cho phep gia von bang 0" thi qua duoc, nhung hang vao kho gia 0
     se keo tut gia binh quan va lam gia von xuat kho ve sau sai.
  3. Nang nhat: tiem dang bat hach toan ton kho thuong xuyen, va tai khoan
     doi ung cua nhap kho khong nguon duoc khai la 632 Gia von hang ban. Moi
     phieu nhap banh se ghi No ton kho / Co 632, tuc GIAM gia von hang ban.
     Lam moi ngay thi lai gop tren bao cao phinh ao.

Ly do sau cung la vi sao dung chuan phai di qua lenh san xuat: lenh san xuat
tieu nguyen lieu o mot dau va sinh thanh pham o dau kia, hai ve can nhau.
Nhap kho khong nguon khong co ve tieu nen phai muon tam tu 632.

Nen ban nay ghi so vao SO RIENG cua tiem: khong sinh but toan, khong dung
ton kho ERPNext, khong can gia von, khong cho BOM. D1 bo Excel ngay. Khi BOM
xong va ke toan bat tru kho luc ban, cau truc nay da san sang de sinh phieu
kho that tu chinh cac dong da ghi.

Cach dung so
------------
Mot ban ghi cho MOT NGAY tai MOT DIEM NHAN. Trong do:

  - bang `ton`  : ton dau ngay, moi mon mot dong. Quay dem tay moi sang.
  - bang `dong` : moi LAN nhan mot dong, mang so dot. Bep giao ba dot thi mon
                  do co ba dong, khong cong don, de con soi lai tung dot.

Man hinh gop hai bang lai thanh dung hinh cai Excel cu: mon, ton dau, tung
dot, tong nhan, tong co.
"""

import frappe
from frappe.utils import cint, getdate, now_datetime

DT = "Vagabond Nhan Banh"
DIEM_MAC_DINH = "Kho D1 - TV"

# Vai duoc ghi so nhan banh. Quay va bep deu phai ghi duoc: bep giao thi bep
# co the ghi ho luc quay dang dong khach.
QUYEN_GHI = {
	"System Manager",
	"Stock User",
	"Stock Manager",
	"Sales User",
	"Sales Manager",
	"Bộ phận đặt hàng",
}

# Goc cay nhom hang duoc phep nhan. Chan de khong ai lo tay nhan nguyen vat
# lieu vao so nay - so nay chi noi chuyen banh thanh pham giao ra quay.
#
# Lay theo GOC CAY chu khong liet ke cung tung nhom con: hom nay duoi "Thanh
# pham Banh" co bay nhom (Banh nuong, Banh lanh, Banh kho, Banh o sinh nhat,
# Hop banh theo mua, Banh Wholesale, Banh nhe), mai kia them nhom moi thi tu
# co mat, khong phai sua code va deploy lai.
GOC_HANG = "Thành phẩm Bánh"


def _quyen():
	if not QUYEN_GHI & set(frappe.get_roles()):
		frappe.throw("Tài khoản của bạn chưa được cấp quyền ghi sổ nhận bánh.")


# --------------------------------------------------------------- phep thuan


def ma_ngan(ten_kho):
	"""Rut ten kho dai thanh ma ngan de dat ten ban ghi. THUAN.

	"Kho D1 - TV" -> "D1". Bo tien to "Kho " va hau to cong ty " - TV", bo
	dau tieng Viet, roi bo dau cach va ky tu la.

	Vi sao phai BO DAU chu khong chi bo dau cach: ten ban ghi di thang vao
	URL cua Desk va vao cac duong dan bao cao. "NB-TỔNG307-2026-08-23" thi
	trinh duyet ma hoa thanh mot chuoi phan tram dai loang ngoang, khong ai
	doc duoc va khong go tay lai duoc khi can dan cho nhau.
	"""
	import unicodedata

	s = str(ten_kho or "").strip()
	if not s:
		return ""
	if " - " in s:
		s = s.rsplit(" - ", 1)[0]
	if s.lower().startswith("kho "):
		s = s[4:]
	s = unicodedata.normalize("NFD", s)
	s = "".join(c for c in s if unicodedata.category(c) != "Mn")
	s = s.replace("\u0111", "d").replace("\u0110", "D")
	ra = []
	for c in s:
		if c.isascii() and c.isalnum():
			ra.append(c.upper())
	return "".join(ra)[:20] or "KHO"


def dot_ke_tiep(cac_dong):
	"""So dot cho lan nhan sap toi. THUAN.

	Chua co dong nao thi la dot 1. Da co thi lay dot lon nhat cong mot.
	KHONG dem so dong: bep giao mot dot muoi mon la muoi dong nhung van la
	mot dot.
	"""
	lon = 0
	for d in cac_dong or []:
		s = cint((d or {}).get("dot"))
		if s > lon:
			lon = s
	return lon + 1


def gop_bang(cac_ton, cac_dong):
	"""Gop ton dau ngay va cac lan nhan thanh bang mot dong mot mon. THUAN.

	Tra ve (danh sach dong, so dot cao nhat). Moi dong:

	    ma_hang, ten_banh, ton_dau, cac_dot {so dot: so luong}, tong_nhan,
	    tong_co

	tong_co = ton_dau + tong_nhan, tuc so hang quay dang co trong tay hom nay
	truoc khi ban. Day chinh la con so ma cai Excel cu KHONG co: no chi liet
	ke hai cot roi de nguoi doc tu cong nham trong dau.
	"""
	ban, thu_tu, so_dot = {}, [], 0

	def _o(ma, ten):
		ma = str(ma or "").strip()
		if not ma:
			return None
		if ma not in ban:
			ban[ma] = {
				"ma_hang": ma,
				"ten_banh": ten or ma,
				"ton_dau": 0,
				"cac_dot": {},
				"tong_nhan": 0,
				"tong_co": 0,
			}
			thu_tu.append(ma)
		elif ten and ban[ma]["ten_banh"] == ma:
			ban[ma]["ten_banh"] = ten
		return ban[ma]

	for t in cac_ton or []:
		t = t or {}
		o = _o(t.get("ma_hang"), t.get("ten_banh"))
		if o is not None:
			o["ton_dau"] += cint(t.get("so_luong"))

	for d in cac_dong or []:
		d = d or {}
		o = _o(d.get("ma_hang"), d.get("ten_banh"))
		if o is None:
			continue
		dot = cint(d.get("dot")) or 1
		if dot > so_dot:
			so_dot = dot
		sl = cint(d.get("so_luong"))
		o["cac_dot"][str(dot)] = cint(o["cac_dot"].get(str(dot))) + sl
		o["tong_nhan"] += sl

	ra = []
	for ma in thu_tu:
		o = ban[ma]
		o["tong_co"] = o["ton_dau"] + o["tong_nhan"]
		ra.append(o)
	ra.sort(key=lambda x: x["ten_banh"])
	return ra, so_dot


def goi_y_ton_dau(bang_hom_qua):
	"""Tu bang hom qua doan ton dau hom nay, chi de GOI Y. THUAN.

	Tra dict {ma_hang: so}. So nay la ton dau hom qua cong het cac dot nhan
	hom qua, tuc la so hang da co MA CHUA TRU PHAN DA BAN.

	Co tinh KHONG dat thang vao o ton dau: ban ra hien chua tru kho nen phep
	tru khong the tu chay duoc. Quay van phai dem that. Con so nay chi de hien
	mo ben canh o trong, kieu "hom qua co 38, dem duoc bao nhieu?", cho nguoi
	dem co cai moc ma so lech nhieu thi biet duong dem lai.
	"""
	ra = {}
	for d in bang_hom_qua or []:
		d = d or {}
		ma = str(d.get("ma_hang") or "").strip()
		if ma:
			ra[ma] = cint(d.get("tong_co"))
	return ra


# ------------------------------------------------------------ phan cham he


def _ban_ghi(ngay, diem, tao_neu_thieu=0):
	"""Ban ghi so nhan cua mot ngay tai mot diem. None neu chua co va khong tao.

	VI SAO TACH RIENG: bon ham ben duoi deu can dung mot thu, va deu can no
	nem loi giong nhau khi thieu. Gom mot cho de sau nay doi cach dat ten ban
	ghi thi chi sua mot noi. Bai hoc tu mua_vu._doc_mua: bon ham cung goi mot
	ham roi moi ham hieu ket qua mot kieu, ba thang khong ai biet.
	"""
	ng = getdate(ngay) if ngay else getdate()
	kho = str(diem or "").strip() or DIEM_MAC_DINH
	ma = ma_ngan(kho)
	ten = "NB-%s-%s" % (ma, ng)
	if frappe.db.exists(DT, ten):
		return frappe.get_doc(DT, ten)
	if not cint(tao_neu_thieu):
		return None
	if not frappe.db.exists("Warehouse", kho):
		frappe.throw("Không có điểm nhận \"%s\" trên hệ thống." % kho)
	doc = frappe.get_doc({
		"doctype": DT, "ngay": str(ng), "diem": kho, "ma_diem": ma,
		"tinh_trang": "Dang nhan",
	})
	doc.insert(ignore_permissions=True)
	return doc


def _ten_mon(cac_ma):
	"""Ten hien thi va hinh cua mot loat ma hang."""
	ra = {}
	cac_ma = [m for m in (cac_ma or []) if m]
	if not cac_ma:
		return ra
	for r in frappe.get_all(
		"Item",
		filters={"name": ["in", cac_ma]},
		fields=["name", "item_name", "image"],
		limit_page_length=0,
	):
		ra[r["name"]] = {"ten": r.get("item_name") or r["name"], "hinh": r.get("image") or ""}
	return ra


def _bang_tho(doc):
	"""Bang da gop cua mot ban ghi, chua gan ten va hinh."""
	if doc is None:
		return [], 0
	ton = [t.as_dict() for t in doc.get("ton") or []]
	dong = [d.as_dict() for d in doc.get("dong") or []]
	return gop_bang(ton, dong)


@frappe.whitelist()
def diem_nhan():
	"""Cac diem nhan mo ra cho man hinh chon."""
	_quyen()
	ds = frappe.get_all(
		"Warehouse",
		filters={"is_group": 0, "disabled": 0},
		fields=["name"],
		order_by="name",
		limit_page_length=0,
	)
	return {"ds": [x["name"] for x in ds], "mac_dinh": DIEM_MAC_DINH}


@frappe.whitelist()
def bang(ngay=None, diem=None):
	"""Bang nhan banh cua mot ngay: ton dau, tung dot, tong co.

	Chi DOC. Ngay chua co so thi tra bang rong chu khong tao ban ghi - mo man
	de xem khong duoc phep de lai rac trong he.
	"""
	_quyen()
	ng = getdate(ngay) if ngay else getdate()
	kho = str(diem or "").strip() or DIEM_MAC_DINH
	doc = _ban_ghi(ng, kho)
	dong, so_dot = _bang_tho(doc)

	# Goi y ton dau lay tu ngay lien truoc, chi de hien mo canh o trong.
	from frappe.utils import add_days

	hom_qua, _sd = _bang_tho(_ban_ghi(add_days(ng, -1), kho))
	goi_y = goi_y_ton_dau(hom_qua)

	tt = _ten_mon([d["ma_hang"] for d in dong])
	for d in dong:
		t = tt.get(d["ma_hang"]) or {}
		if t.get("ten"):
			d["ten_banh"] = t["ten"]
		d["hinh"] = t.get("hinh") or ""
		d["goi_y_ton"] = cint(goi_y.get(d["ma_hang"]))

	return {
		"ngay": str(ng),
		"diem": kho,
		"co_so": 1 if doc is not None else 0,
		"tinh_trang": (doc.tinh_trang if doc is not None else "Dang nhan"),
		"so_dot": so_dot,
		"dot_moi": dot_ke_tiep([x.as_dict() for x in (doc.get("dong") or [])] if doc else []),
		"dong": dong,
		"ghi_chu": (doc.ghi_chu or "" if doc is not None else ""),
	}


@frappe.whitelist()
def tim_mon(tu_khoa="", diem=None):
	"""Tim mon de them vao so. Chi trong cay hang duoc phep nhan."""
	_quyen()
	q = str(tu_khoa or "").strip()
	nhom = frappe.get_all(
		"Item Group",
		filters={"name": GOC_HANG},
		fields=["lft", "rgt"],
		limit_page_length=1,
	)
	loc = {"disabled": 0, "is_stock_item": 1}
	if nhom:
		con = frappe.get_all(
			"Item Group",
			filters={"lft": [">=", nhom[0]["lft"]], "rgt": ["<=", nhom[0]["rgt"]], "is_group": 0},
			fields=["name"],
			limit_page_length=0,
		)
		loc["item_group"] = ["in", [c["name"] for c in con]] if con else ["in", [GOC_HANG]]
	if q:
		loc["item_name"] = ["like", "%" + q + "%"]
	ds = frappe.get_all(
		"Item",
		filters=loc,
		fields=["name", "item_name", "image", "item_group"],
		order_by="item_name",
		limit_page_length=60,
	)
	return {"ds": ds}


@frappe.whitelist()
def mon_hay_nhan(diem=None, so_ngay=30):
	"""Mon da tung nhan gan day, de man hinh bay san khoi phai tim tung mon."""
	_quyen()
	from frappe.utils import add_days

	kho = str(diem or "").strip() or DIEM_MAC_DINH
	tu = add_days(getdate(), -max(1, cint(so_ngay)))
	cha = frappe.get_all(
		DT,
		filters={"diem": kho, "ngay": [">=", str(tu)]},
		fields=["name"],
		limit_page_length=0,
	)
	if not cha:
		return {"ds": []}
	dem = {}
	for r in frappe.get_all(
		"Vagabond Nhan Banh Dong",
		filters={"parent": ["in", [c["name"] for c in cha]]},
		fields=["ma_hang"],
		limit_page_length=0,
	):
		ma = r.get("ma_hang")
		if ma:
			dem[ma] = dem.get(ma, 0) + 1
	tt = _ten_mon(list(dem.keys()))
	ds = [
		{
			"ma_hang": m,
			"ten_banh": (tt.get(m) or {}).get("ten") or m,
			"hinh": (tt.get(m) or {}).get("hinh") or "",
			"so_lan": n,
		}
		for m, n in dem.items()
	]
	ds.sort(key=lambda x: (-x["so_lan"], x["ten_banh"]))
	return {"ds": ds[:80]}


def _chan_da_chot(doc):
	if doc is not None and doc.tinh_trang == "Da chot":
		frappe.throw(
			"Sổ ngày %s đã chốt rồi, không sửa được nữa. Cần sửa thì mở lại sổ trước."
			% doc.ngay
		)


@frappe.whitelist()
def ghi_nhan(ngay=None, diem=None, dot=0, cac_dong=None, ghi_chu=""):
	"""Ghi mot LAN nhan: nhieu mon cung mot dot.

	cac_dong: list dict {ma_hang, so_luong}. So 0 hoac am thi bo qua chu khong
	nem loi - nguoi go de mot o trong roi bam luu la chuyen binh thuong.
	"""
	_quyen()
	if isinstance(cac_dong, str):
		import json

		cac_dong = json.loads(cac_dong or "[]")
	cac_dong = [d for d in (cac_dong or []) if cint((d or {}).get("so_luong")) > 0]
	if not cac_dong:
		frappe.throw("Chưa nhập số lượng nào. Điền số cho ít nhất một món giúp em.")

	doc = _ban_ghi(ngay, diem, tao_neu_thieu=1)
	_chan_da_chot(doc)
	so_dot = cint(dot) or dot_ke_tiep([x.as_dict() for x in (doc.get("dong") or [])])
	gio = now_datetime().strftime("%H:%M:%S")
	nguoi = frappe.session.user
	tt = _ten_mon([str((d or {}).get("ma_hang") or "").strip() for d in cac_dong])

	for d in cac_dong:
		ma = str(d.get("ma_hang") or "").strip()
		if not ma:
			continue
		doc.append(
			"dong",
			{
				"ma_hang": ma,
				"ten_banh": (tt.get(ma) or {}).get("ten") or ma,
				"so_luong": cint(d.get("so_luong")),
				"dot": so_dot,
				"gio": gio,
				"nguoi_nhan": nguoi,
				"ghi_chu": str(d.get("ghi_chu") or "").strip(),
			},
		)
	if str(ghi_chu or "").strip():
		doc.ghi_chu = str(ghi_chu).strip()
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bang(doc.ngay, doc.diem)


@frappe.whitelist()
def sua_so(ngay=None, diem=None, ma_hang=None, dot=0, so_luong=0):
	"""Sua so cua mot mon trong mot dot. So 0 thi xoa dong do.

	DAT LAI chu khong cong don: nguoi go dang nhin thay con so cu tren man
	hinh va go de LAY con so do.
	"""
	_quyen()
	doc = _ban_ghi(ngay, diem)
	if doc is None:
		frappe.throw("Ngày này chưa có sổ nhận nào để sửa.")
	_chan_da_chot(doc)
	ma = str(ma_hang or "").strip()
	so_dot = cint(dot) or 1
	so = max(0, cint(so_luong))

	con, thay = [], False
	for x in doc.get("dong") or []:
		if x.ma_hang == ma and cint(x.dot) == so_dot:
			if thay or so <= 0:
				continue
			thay = True
			con.append({
				"ma_hang": x.ma_hang, "ten_banh": x.ten_banh, "so_luong": so,
				"dot": so_dot, "gio": x.gio, "nguoi_nhan": frappe.session.user,
				"ghi_chu": x.ghi_chu,
			})
		else:
			con.append({
				"ma_hang": x.ma_hang, "ten_banh": x.ten_banh, "so_luong": x.so_luong,
				"dot": x.dot, "gio": x.gio, "nguoi_nhan": x.nguoi_nhan,
				"ghi_chu": x.ghi_chu,
			})
	if not thay and so > 0:
		tt = _ten_mon([ma])
		con.append({
			"ma_hang": ma, "ten_banh": (tt.get(ma) or {}).get("ten") or ma,
			"so_luong": so, "dot": so_dot,
			"gio": now_datetime().strftime("%H:%M:%S"),
			"nguoi_nhan": frappe.session.user, "ghi_chu": "",
		})
	doc.set("dong", [])
	for x in con:
		doc.append("dong", x)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bang(doc.ngay, doc.diem)


@frappe.whitelist()
def dat_ton_dau(ngay=None, diem=None, ma_hang=None, so_luong=0):
	"""Go so ton dau ngay cua mot mon. DAT LAI, khong cong don."""
	_quyen()
	doc = _ban_ghi(ngay, diem, tao_neu_thieu=1)
	_chan_da_chot(doc)
	ma = str(ma_hang or "").strip()
	if not ma:
		frappe.throw("Chưa chọn mã hàng.")
	so = max(0, cint(so_luong))

	con, thay = [], False
	for x in doc.get("ton") or []:
		if x.ma_hang == ma:
			if thay or so <= 0:
				continue
			thay = True
			con.append({"ma_hang": ma, "ten_banh": x.ten_banh, "so_luong": so})
		else:
			con.append({"ma_hang": x.ma_hang, "ten_banh": x.ten_banh, "so_luong": x.so_luong})
	if not thay and so > 0:
		tt = _ten_mon([ma])
		con.append({
			"ma_hang": ma, "ten_banh": (tt.get(ma) or {}).get("ten") or ma, "so_luong": so,
		})
	doc.set("ton", [])
	for x in con:
		doc.append("ton", x)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bang(doc.ngay, doc.diem)


@frappe.whitelist()
def xoa_mon(ngay=None, diem=None, ma_hang=None):
	"""Go han mot mon khoi so cua ngay: ca ton dau lan moi dot da nhan."""
	_quyen()
	doc = _ban_ghi(ngay, diem)
	if doc is None:
		frappe.throw("Ngày này chưa có sổ nhận nào để sửa.")
	_chan_da_chot(doc)
	ma = str(ma_hang or "").strip()
	for bang_con in ("ton", "dong"):
		con = [x for x in (doc.get(bang_con) or []) if x.ma_hang != ma]
		giu = [x.as_dict() for x in con]
		doc.set(bang_con, [])
		for x in giu:
			x.pop("name", None)
			x.pop("parent", None)
			x.pop("parentfield", None)
			x.pop("parenttype", None)
			doc.append(bang_con, x)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bang(doc.ngay, doc.diem)


@frappe.whitelist()
def chot_ngay(ngay=None, diem=None, mo_lai=0):
	"""Chot so cua ngay, hoac mo lai de sua.

	Chot roi thi khong ai sua duoc nua, de con so gui di khong doi sau lung
	nguoi da doc. Mo lai duoc, nhung phai bam co y.
	"""
	_quyen()
	doc = _ban_ghi(ngay, diem)
	if doc is None:
		frappe.throw("Ngày này chưa có sổ nhận nào để chốt.")
	if cint(mo_lai):
		doc.tinh_trang = "Dang nhan"
		doc.chot_luc = None
		doc.chot_boi = ""
	else:
		doc.tinh_trang = "Da chot"
		doc.chot_luc = now_datetime()
		doc.chot_boi = frappe.session.user
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bang(doc.ngay, doc.diem)

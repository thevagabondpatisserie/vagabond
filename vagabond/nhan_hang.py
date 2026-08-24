"""Nhan hang tung phan tu Don mua hang (anh Viet duyet 15/08/2026, PA-B).

Bai toan cua Kien
-----------------
Mot don mua ba mon, nha cung cap chi giao truoc mot mon. Thu mua tao san
MOT phieu nhap kho nhap tu don do; Kien dien so thuc nhan, may loc bo dong
bang 0 roi ghi so. Xong. KHONG ai sinh phieu nhap dot hai, nen tab "Cho
nhan" trong tron va Kien ket luan la het viec - trong khi don mua van con
no hai mon.

Du lieu khong he thieu: ERPNext van giu `received_qty` tren tung dong don
mua va `per_received` tren dau don. Cai thieu la mot cho de nhin, va mot
duong de nhan tiep. Mo dun nay lam dung hai viec do.

Ba phuong an da can nhac, chot PA-B:

  PA-A  Ghi so xong thi may tu sinh mot phieu nhap nhap cho phan con lai.
        Loai: nha cung cap bo khong giao nua thi phieu nhap nam rac vinh
        vien, giao le ba lan la de ba phieu nhap.
  PA-B  Khong sinh nhap. Kien mo thang DON MUA roi bam "Nhan hang dot
        nay". Nguon su that la don mua, dung thiet ke ERPNext.
  PA-C  Dung mot doctype rieng theo doi hang con no. Loai: nhan doi su
        that, lech mot lan la khong ai biet ben nao dung.

Luat nha ap vao day
-------------------
QT-19  So luong con lai LUON tinh lai o may chu truoc khi ghi. Con so may
       khach gui len chi de hien, khong bao gio duoc tin.
QT-20  Khong xoa vinh vien, khong sua so goc. Dong mot don con no thi dung
       trang thai Closed cua ERPNext va ghi vet ai dong, vi sao. So luong
       dat tren don khong bi sua mot chu.
QT-24  Cau bao loi phai noi nguoi dung lam gi tiep.
"""

import json

import frappe
from frappe.utils import add_days, cint, flt, getdate, nowdate

QUYEN_NHAN = {
	"System Manager",
	"Stock Manager",
	"Stock User",
	"Purchase Manager",
	"Purchase User",
	"Accounts Manager",
}

# Sai so cho phep khi so sanh so luong. Duoi muc nay coi nhu bang nhau:
# don vi kg va lit deu co phan le, so sanh bang dau bang tran la sai.
EPS = 0.0001


def _kiem_quyen():
	if not QUYEN_NHAN & set(frappe.get_roles()):
		frappe.throw(
			"Màn nhận hàng chỉ mở cho kho, thu mua và kế toán. Nếu anh chị cần "
			"vào đây thì báo quản lý cấp thêm quyền Kho."
		)


def _so(v):
	"""So luong in ra cho nguoi doc: bo duoi .0 thua."""
	v = flt(v)
	return str(int(v)) if abs(v - int(v)) < EPS else ("%.3f" % v).rstrip("0").rstrip(".")


def _ghi_vet(doctype, name, viec):
	"""Ai lam gi luc nao. Khong co ghi vet thi huy mem chi la xoa cham hon."""
	try:
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": doctype,
				"reference_name": name,
				"content": "%s - %s" % (viec, frappe.session.user),
			}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "nhan_hang: ghi vet %s" % name)


# ------------------------------------------------------------ so con lai


def con_lai_theo_don(ten_don):
	"""So luong con phai nhan, gom theo don mua. MOT cau hoi cho ca tap.

	Tra ve {ten_don: {so_mon, so_mon_con, sl_dat, sl_nhan, sl_con}}.

	Dung chung cho ba noi: man danh sach cua Kien, cot "Con phai nhan" cua
	bang don mua, va buoc kiem truoc khi ghi phieu. Ba noi cung mot cong
	thuc thi khong bao gio lech nhau.
	"""
	ra = {}
	ds = [x for x in (ten_don or []) if x]
	if not ds:
		return ra
	dong = frappe.get_all(
		"Purchase Order Item",
		filters={"parent": ["in", ds], "docstatus": 1},
		fields=["parent", "qty", "received_qty"],
		limit_page_length=0,
	)
	for r in dong:
		o = ra.setdefault(
			r["parent"],
			{"so_mon": 0, "so_mon_con": 0, "sl_dat": 0.0, "sl_nhan": 0.0, "sl_con": 0.0},
		)
		dat = flt(r["qty"])
		nhan = flt(r["received_qty"])
		con = dat - nhan
		if con < EPS:
			con = 0.0
		o["so_mon"] += 1
		o["sl_dat"] += dat
		o["sl_nhan"] += nhan
		o["sl_con"] += con
		if con > EPS:
			o["so_mon_con"] += 1
	return ra


def _tre_ngay(hen, hom_nay=None):
	if not hen:
		return 0
	hn = hom_nay or getdate(nowdate())
	d = (hn - getdate(hen)).days
	return d if d > 0 else 0


# ------------------------------------------------------- man cua thu kho


@frappe.whitelist()
def danh_sach(so_ngay=90, tu_khoa=""):
	"""Cac don mua CON PHAI NHAN, xep don tre hen len dau.

	Tab thu hai cua man Nhap kho. Chi lay don da ghi so, chua huy mem,
	chua dong, va con it nhat mot mon chua nhan du.
	"""
	_kiem_quyen()
	loc = {"docstatus": 1, "status": ["not in", ["Closed", "Completed"]]}
	so_ngay = cint(so_ngay or 0)
	if so_ngay:
		loc["transaction_date"] = [">=", add_days(nowdate(), -so_ngay)]
	don = frappe.get_all(
		"Purchase Order",
		filters=loc,
		fields=[
			"name", "supplier", "supplier_name", "transaction_date",
			"schedule_date", "per_received", "vgb_huy",
		],
		order_by="schedule_date asc, name asc",
		limit_page_length=0,
	)
	# Don da huy mem khong con la hang se ve. De no trong danh sach la thu
	# kho ngoi doi mot chuyen hang khong bao gio den.
	don = [d for d in don if not cint(d.get("vgb_huy"))]
	con = con_lai_theo_don([d["name"] for d in don])

	hom_nay = getdate(nowdate())
	q = (tu_khoa or "").strip().lower()
	ra = []
	for d in don:
		c = con.get(d["name"]) or {}
		if flt(c.get("sl_con")) <= EPS:
			continue
		if q and q not in (
			(d["name"] or "") + " " + (d.get("supplier_name") or "") + " " + (d.get("supplier") or "")
		).lower():
			continue
		ra.append(
			{
				"name": d["name"],
				"ncc": d.get("supplier_name") or d.get("supplier") or "",
				"ngay": str(d.get("transaction_date") or ""),
				"hen": str(d.get("schedule_date") or ""),
				"tre_ngay": _tre_ngay(d.get("schedule_date"), hom_nay),
				"so_mon": c.get("so_mon") or 0,
				"so_mon_con": c.get("so_mon_con") or 0,
				"sl_con": flt(c.get("sl_con")),
				"da_nhan_pt": flt(d.get("per_received")),
			}
		)
	# Tre hen len dau, roi den hen giao gan nhat. Thu kho mo man ra la thay
	# ngay viec dang chay muon.
	ra.sort(key=lambda x: (-x["tre_ngay"], x["hen"] or "9999-12-31", x["name"]))
	return {"don": ra, "tong_dong": len(ra)}


def _lich_su_nhan(ten_don):
	"""Cac phieu nhap DA GHI SO cua mot don, moi phieu mot dong tom tat."""
	dong = frappe.get_all(
		"Purchase Receipt Item",
		filters={"purchase_order": ten_don, "docstatus": 1},
		fields=["parent", "item_code", "qty"],
		limit_page_length=0,
	)
	gom = {}
	for r in dong:
		o = gom.setdefault(r["parent"], {"so_mon": 0, "sl": 0.0})
		o["so_mon"] += 1
		o["sl"] += flt(r["qty"])
	if not gom:
		return []
	dau = frappe.get_all(
		"Purchase Receipt",
		filters={"name": ["in", list(gom)], "docstatus": 1},
		fields=["name", "posting_date"],
		limit_page_length=0,
	)
	ra = []
	for p in dau:
		g = gom.get(p["name"]) or {}
		ra.append(
			{
				"name": p["name"],
				"ngay": str(p.get("posting_date") or ""),
				"so_mon": g.get("so_mon") or 0,
				"sl": flt(g.get("sl")),
			}
		)
	ra.sort(key=lambda x: (x["ngay"], x["name"]))
	for i, x in enumerate(ra):
		x["dot"] = i + 1
	return ra


@frappe.whitelist()
def chi_tiet(don):
	"""Mot don mua, dung san thanh cac dong de thu kho nhan dot tiep theo.

	Moi dong tra ve DU BA CON SO: dat, da_nhan, con_lai. Man hinh bay ca ba
	chu khong bay mot - dot hai ma chi thay so dat thi go nham la nhap
	trung ca lo.
	"""
	_kiem_quyen()
	d = frappe.get_doc("Purchase Order", don)
	if d.docstatus != 1:
		frappe.throw(
			"Đơn %s chưa ghi sổ nên chưa nhận hàng được. Báo thu mua gửi duyệt "
			"đơn trước." % don
		)
	if cint(d.get("vgb_huy")):
		frappe.throw("Đơn %s đã huỷ, không nhận hàng vào đơn này được." % don)
	if d.status in ("Closed", "Completed"):
		frappe.throw(
			"Đơn %s đã đóng nên không nhận thêm được. Muốn nhận tiếp thì mở lại "
			"đơn bên phần Đơn mua hàng." % don
		)

	ma_hang = [r.item_code for r in d.items]
	lo, han = {}, {}
	if ma_hang:
		for it in frappe.get_all(
			"Item",
			filters={"name": ["in", ma_hang]},
			fields=["name", "has_batch_no", "shelf_life_in_days"],
			limit_page_length=0,
		):
			lo[it["name"]] = 1 if it.get("has_batch_no") else 0
			han[it["name"]] = cint(it.get("shelf_life_in_days"))

	mon = []
	for r in d.items:
		dat = flt(r.qty)
		nhan = flt(r.received_qty)
		con = dat - nhan
		if con < EPS:
			con = 0.0
		mon.append(
			{
				"dong": r.name,
				"ma": r.item_code,
				"ten": r.item_name or r.item_code,
				"dvt": r.uom or r.stock_uom or "",
				"kho": r.warehouse or d.get("set_warehouse") or "",
				"sl_dat": dat,
				"sl_da_nhan": nhan,
				"sl_con": con,
				"gia": flt(r.rate),
				"co_lo": lo.get(r.item_code, 0),
				"han_chuan": han.get(r.item_code, 0),
			}
		)
	# Mon da nhan du xuong cuoi va lam mo tren man hinh: thu kho chi nhin
	# thay viec CON PHAI LAM.
	mon.sort(key=lambda x: (1 if x["sl_con"] <= EPS else 0, x["ten"]))

	ls = _lich_su_nhan(don)
	return {
		"name": d.name,
		"ncc": d.supplier_name or d.supplier or "",
		"ngay": str(d.transaction_date or ""),
		"hen": str(d.schedule_date or ""),
		"tre_ngay": _tre_ngay(d.schedule_date),
		"da_nhan_pt": flt(d.per_received),
		"mon": mon,
		"so_mon_con": len([x for x in mon if x["sl_con"] > EPS]),
		"lich_su": ls,
		"dot_toi": len(ls) + 1,
	}


# ------------------------------------------------------------- ghi phieu


def _doc_dong(dong):
	"""Doc tham so dong tu may khach thanh {ten_dong_don: so_luong}."""
	if isinstance(dong, str):
		try:
			dong = json.loads(dong or "[]")
		except (ValueError, TypeError):
			frappe.throw("Dữ liệu dòng hàng gửi lên không đọc được, vui lòng thử lại.")
	ra = {}
	for x in dong or []:
		khoa = str((x or {}).get("dong") or "").strip()
		if not khoa:
			continue
		ra[khoa] = {
			"sl": flt((x or {}).get("sl")),
			"hsd": str((x or {}).get("hsd") or "").strip(),
		}
	return ra


@frappe.whitelist()
def tao_phieu(don, dong=None, anh1=None, anh2=None, scan=None, ghi_chu=None):
	"""Ghi mot phieu nhap kho cho dot giao nay, dung tu DON MUA.

	Khong dung phieu nhap nhap tao san: don giao le ba lan thi phai lam
	phieu ba lan, ma tao san ba ban nhap la de rac. Dung thang ham dung
	phieu cua ERPNext roi ghi de so luong theo so thuc dem.

	So luong con lai TINH LAI O DAY, khong tin con so may khach gui len.
	Nhap qua phan con lai la chan thang: do la duong duy nhat de nhap trung
	mot lo hang.
	"""
	_kiem_quyen()
	goc = frappe.get_doc("Purchase Order", don)
	if goc.docstatus != 1:
		frappe.throw("Đơn %s chưa ghi sổ nên chưa nhận hàng được." % don)
	if cint(goc.get("vgb_huy")):
		frappe.throw("Đơn %s đã huỷ, không nhận hàng vào đơn này được." % don)
	if goc.status in ("Closed", "Completed"):
		frappe.throw(
			"Đơn %s đã đóng nên không nhận thêm được. Mở lại đơn rồi thử lại." % don
		)

	nhap = _doc_dong(dong)
	if not nhap:
		frappe.throw("Chưa có dòng nào để nhập kho.")

	# Bang tra phan con lai, doc tu chinh don goc chu khong tu may khach.
	con_lai, ten_mon, dvt = {}, {}, {}
	for r in goc.items:
		c = flt(r.qty) - flt(r.received_qty)
		con_lai[r.name] = c if c > EPS else 0.0
		ten_mon[r.name] = r.item_name or r.item_code
		dvt[r.name] = r.uom or r.stock_uom or ""

	la, qua = {}, []
	for khoa, x in nhap.items():
		sl = flt(x.get("sl"))
		if khoa not in con_lai:
			frappe.throw(
				"Dòng hàng gửi lên không thuộc đơn %s. Vui lòng thoát ra mở lại đơn rồi nhập lại." % don
			)
		if sl <= EPS:
			continue
		if sl > con_lai[khoa] + EPS:
			qua.append(
				"%s: còn phải nhận %s %s, đang nhập %s"
				% (ten_mon[khoa], _so(con_lai[khoa]), dvt[khoa], _so(sl))
			)
		la[khoa] = x
	if qua:
		frappe.throw(
			"Nhập quá số còn phải nhận:<br>%s<br><br>Nhà cung cấp giao dư thì "
			"báo thu mua lên đơn bổ sung rồi nhập sau, đừng nhập dồn vào đơn "
			"này." % "<br>".join(qua)
		)
	if not la:
		frappe.throw("Tất cả các dòng đều để 0, chưa có gì để nhập kho.")

	from erpnext.buying.doctype.purchase_order.purchase_order import (
		make_purchase_receipt,
	)

	pr = make_purchase_receipt(don)
	pr.posting_date = nowdate()
	pr.set_posting_time = 1

	# Ham dung phieu cua ERPNext tu bo cac dong da nhan DU, nen dong nao con
	# thieu thi chac chan co mat. Van kiem lai: neu giua luc thu kho dem hang
	# va luc bam Luu ma nguoi khac vua nhan mat dong do, dong day bien khoi
	# phieu va neu im lang thi minh ghi thieu hang ma khong ai biet.
	co_trong_phieu = {r.get("purchase_order_item") for r in pr.items}
	mat = [ten_mon[k] for k in la if k not in co_trong_phieu]
	if mat:
		frappe.throw(
			"Trong lúc anh chị đang đếm thì %s đã được người khác nhận mất rồi. "
			"Thoát ra mở lại đơn %s để lấy số còn lại mới nhất." % (", ".join(mat), don)
		)

	giu, thieu_gia = [], []
	for r in pr.items:
		khoa = r.get("purchase_order_item")
		if khoa not in la:
			continue
		r.qty = flt(la[khoa].get("sl"))
		r.received_qty = r.qty
		r.rejected_qty = 0
		if la[khoa].get("hsd"):
			r.han_su_dung = la[khoa]["hsd"]
		# Don chua kip khai gia thi van cho nhap kho, nhung phai noi ra chu
		# khong de gia von am tham bang 0.
		if flt(r.rate) <= 0:
			r.allow_zero_valuation_rate = 1
			thieu_gia.append(r.item_name or r.item_code)
		giu.append(r)
	if not giu:
		frappe.throw(
			"Không dựng được dòng nào cho phiếu nhập. Vui lòng thoát ra mở lại đơn rồi thử lại."
		)
	for i, r in enumerate(giu):
		r.idx = i + 1
	pr.set("items", giu)

	if anh1:
		pr.custom_hinh_nhan_hang_1 = anh1
	if anh2:
		pr.custom_hinh_nhan_hang_2 = anh2
	if scan:
		pr.custom_scan_bien_ban = scan

	dot = len(_lich_su_nhan(don)) + 1
	ghi = "Nhận hàng đợt %d theo đơn %s." % (dot, don)
	if (ghi_chu or "").strip():
		ghi += " " + (ghi_chu or "").strip()
	if thieu_gia:
		ghi += " Nhập khi chưa có giá: %s - kế toán bổ sung giá sau." % ", ".join(
			thieu_gia
		)
	pr.remarks = ((pr.get("remarks") or "") + " | " + ghi).strip(" |")

	pr.flags.ignore_permissions = True
	pr.insert()
	pr.submit()

	_ghi_vet(
		"Purchase Order",
		don,
		"Nhận hàng đợt %d: phiếu %s, %d món" % (dot, pr.name, len(pr.items)),
	)
	frappe.db.commit()

	sau = con_lai_theo_don([don]).get(don) or {}
	return {
		"phieu": pr.name,
		"dot": dot,
		"so_mon": len(pr.items),
		"con_lai": flt(sau.get("sl_con")),
		"so_mon_con": sau.get("so_mon_con") or 0,
		"thieu_gia": thieu_gia,
	}

# ------------------------------------------------- dong phan con lai lai


@frappe.whitelist()
def dong_con_lai(don, ly_do=None):
	"""Nha cung cap bao khong giao nua: dong phan con no cua don.

	KHONG sua so luong dat, KHONG xoa dong nao (QT-20). Chi dat trang thai
	Closed cua ERPNext va ghi vet ai dong, vi sao. Mo lai duoc bat cu luc
	nao, va so lieu cu van nguyen ven de doi chieu voi nha cung cap.
	"""
	_kiem_quyen()
	if not (ly_do or "").strip():
		frappe.throw(
			"Phải ghi lý do đóng thì sau này còn biết vì sao đơn này không nhận "
			"đủ. Ví dụ: nhà cung cấp báo hết hàng, hoặc mình đổi sang mua nơi khác."
		)
	d = frappe.get_doc("Purchase Order", don)
	if d.docstatus != 1:
		frappe.throw("Đơn %s chưa ghi sổ nên không có gì để đóng." % don)
	if d.status == "Closed":
		return {"ok": 1, "da_dong_tu_truoc": 1}
	con = (con_lai_theo_don([don]).get(don) or {})
	d.update_status("Closed")
	_ghi_vet(
		"Purchase Order",
		don,
		"Đóng phần còn lại (%s đơn vị chưa nhận). Lý do: %s"
		% (_so(con.get("sl_con")), (ly_do or "").strip()),
	)
	frappe.db.commit()
	return {"ok": 1, "con_lai": flt(con.get("sl_con"))}


@frappe.whitelist()
def mo_lai(don, ly_do=None):
	"""Mo lai mot don da dong nham, de nhan tiep."""
	_kiem_quyen()
	d = frappe.get_doc("Purchase Order", don)
	if d.status != "Closed":
		frappe.throw("Đơn %s không ở trạng thái đã đóng." % don)
	d.update_status("Submitted")
	_ghi_vet(
		"Purchase Order",
		don,
		"Mở lại phần còn lại để nhận tiếp. Lý do: %s"
		% ((ly_do or "").strip() or "không ghi"),
	)
	frappe.db.commit()
	return {"ok": 1}

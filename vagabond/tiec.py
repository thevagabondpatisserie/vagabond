# -*- coding: utf-8 -*-
"""Mang B2B va Tiec: lam theo don, khong dinh muc.

Anh Viet duyet ban thiet ke ngay 25/08/2026. Doc ban day du o project doc
`claude/thiet-ke-b2b-tiec-lam-theo-don.md`.

MO HINH: LAM THEO DON, KHONG CO BOM
===================================
Goi tiec khong co ma thanh pham co dinh va khong co BOM tinh. Nghia la:

  - KHONG dung Work Order. Work Order cua ERPNext bat buoc phai co mot
    BOM. Tiec khong co BOM va se khong bao gio co, vi moi tiec mot khac.
    Co nhet vao la phai de ra mot BOM rac cho moi hop dong.

  - Doanh thu di truoc, gia von di sau, HAI DUONG DOC LAP. Sales ban mot
    goi gia tron; bep tieu nguyen lieu bao nhieu thi ghi bay nhieu. Khong
    co phep so "thuc te so voi dinh muc" vi khong co dinh muc de so.

  - Cai duy nhat noi hai duong lai la MOT CAI NEO CHUNG.


VI SAO NEO BANG PROJECT CHU KHONG PHAI SALES ORDER
==================================================
Anh Viet de xuat neo qua Sales Order. Da do tren chinh site that truoc
khi quyet, va phai bao lai la neo nhu vay khong du:

    Bang                  co `project`   co `sales_order`
    GL Entry (42 truong)      CO             KHONG
    Stock Entry               CO             KHONG
    Stock Entry Detail        KHONG           -
    Sales Invoice             CO              -

But toan gia von sinh ra tu phieu xuat kho nam o `GL Entry`. Ma `GL Entry`
KHONG co cot `sales_order`. Neu chi neo vao Sales Order thi o tang so cai,
but toan gia von khong mang mot dau vet nao cua hop dong.

Neo vao Project thi ca hai ve cung nam tren so cai:

    doanh thu   Sales Invoice.project  ->  GL Entry.project   (Co 511)
    gia von     Stock Entry.project    ->  GL Entry.project   (No 632)

Tru nhau ra lai gop cua dung hop dong do, bang phep cong tren so cai chu
khong phai bang mot bao cao tu che.

MOT CAI BAY O DONG THU BA CUA BANG
----------------------------------
`Stock Entry Detail` KHONG co truong `project`. Dat `project` vao tung
dong phieu thi Frappe bo IM LANG, va minh tuong da neo trong khi chua neo
gi ca.

Khong sao, vi `stock_controller.get_gl_entries` lay
`item_row.project or self.project`, nen `project` o DAU PHIEU van di thang
xuong `GL Entry`. Neo mot cho la du. Co ca kiem dao chieu chot dieu nay.


VI SAO GIU `Hop Dong Ban Hang` LAM GOC
======================================
He DA CO SAN doctype `Hop Dong Ban Hang`, dang chay that, va no da mang
gan du moi thu: `loai` co bon lua chon (Event - Catering, Teabreak, Banh
thiet ke, B2B si), ngay su kien, dia diem giao, dat coc, thong tin phap
nhan khach, nguoi ky hai ben, luong thuong thao co ghi vet.

Dung Sales Order lam hop dong nghia la tiem co HAI thu cung ten "hop dong"
chay song song, sales phai nhap hai lan, va bao gio cung co mot cai lech.
Do dung la kieu hong kho tim nhat.

Sales Order KHONG bat buoc. Neu sau nay can theo doi giao tung dot bang
cong cu san cua ERPNext thi them Sales Order nhu mot lop phu, van neo cung
Project, khong pha gi cua bo hien tai.
"""

# ------------------------------------------------------------ phan thuan

# Tien to ma du an. Doc mot cai la biet du an nay sinh ra tu tiec chu
# khong phai tu viec khac.
TIEN_TO_DU_AN = "TIEC-"

# Tai khoan gia von. Dat THANG tren tung dong phieu chu khong dua vao
# `stock_adjustment_account` cua he.
#
# Ly do: tiem dang de `stock_adjustment_account` la 632. O luong tiec thi
# cai mac dinh do TINH CO dung chieu. Nhung hom nao co nguoi doi cai dat
# chung thi luong tiec se am tham doi theo ma khong ai hay. Ghi thang la
# de lan doi do khong cham toi day. Co ca kiem chot.
TK_GIA_VON = "632 - Giá vốn hàng bán - TV"

# Trang thai hop dong bep can nhin. Nhap va da gui khach thi chua chot,
# bep lam theo la lam theo mot ban con thuong thao.
TT_BEP_THAY = ("Đang thực hiện",)


def ma_du_an(hop_dong):
	"""Ma du an cua mot hop dong. THUAN.

	Mot ham nho nhung phai dat mot cho: neu hai noi tu ghep chuoi thi som
	muon co mot noi ghep khac, va luc do but toan doanh thu voi but toan
	gia von roi vao hai du an khac nhau. Bocs gia von ra se thieu mot ve
	ma khong ai biet.
	"""
	t = str(hop_dong or "").strip()
	if not t:
		return ""
	return TIEN_TO_DU_AN + t


def mo_ta_goi_tiec(mon):
	"""Dung doan mo ta thuc don tu danh sach mon. THUAN.

	Sales dan doan nay vao o Description cua dong TIEC-CUSTOM tren hoa
	don. Mot dong mot mon, doc len la ra thuc don:

	    - Bánh su kem x 50 cái
	    - Tart chanh x 30 cái (ít ngọt)
	"""
	ra = []
	for m in (mon or []):
		ten = str((m or {}).get("ten") or "").strip()
		if not ten:
			continue
		sl = (m or {}).get("sl")
		dvt = str((m or {}).get("dvt") or "").strip()
		ghi = str((m or {}).get("ghi_chu") or "").strip()
		dong = "- " + ten
		if sl not in (None, "", 0):
			dong += " x " + _so_gon(sl) + ((" " + dvt) if dvt else "")
		if ghi:
			dong += " (" + ghi + ")"
		ra.append(dong)
	return "\n".join(ra)


def _so_gon(x):
	"""So khong co duoi .0 thua. THUAN."""
	try:
		f = float(x)
	except (TypeError, ValueError):
		return str(x)
	return str(int(f)) if f == int(f) else ("%g" % f)


def gom_dong_xuat(dong):
	"""Cong don cac dong cung mat hang truoc khi dung phieu. THUAN.

	Bep go cung mot mat hang nhieu lan la chuyen THUONG: bo dot 1, bo dot
	2. ERPNext khong cam hai dong cung ma, nhung phieu doc ra roi ram va
	doi chieu ton thi phai cong tay.

	Ghi chu cua cac lan go duoc NOI LAI chu khong bo di: "dot 1" va "dot
	2" la thong tin that cua bep, mat di thi khong lay lai duoc.

	Giu nguyen THU TU go dau tien: bep doc lai phieu theo thu tu ho can.
	"""
	thu_tu = []
	gom = {}
	for d in (dong or []):
		ma = str((d or {}).get("ma") or "").strip()
		if not ma:
			continue
		try:
			sl = float((d or {}).get("sl") or 0)
		except (TypeError, ValueError):
			sl = 0.0
		if sl <= 0:
			continue
		ghi = str((d or {}).get("ghi_chu") or "").strip()
		if ma not in gom:
			gom[ma] = {"ma": ma, "sl": 0.0, "ghi_chu": []}
			thu_tu.append(ma)
		gom[ma]["sl"] += sl
		if ghi and ghi not in gom[ma]["ghi_chu"]:
			gom[ma]["ghi_chu"].append(ghi)
	ra = []
	for ma in thu_tu:
		g = gom[ma]
		ra.append({"ma": ma, "sl": g["sl"], "ghi_chu": ", ".join(g["ghi_chu"])})
	return ra


def kiem_truoc_khi_xuat(hop_dong, kho, dong):
	"""Nhung gi phai co truoc khi dung phieu. THUAN.

	Tra ve danh sach loi bang tieng nguoi. Rong la di duoc.

	Kiem o tang thuan de man hinh bao loi NGAY, khong phai cho mot vong
	xuong may chu roi moi biet minh quen chon kho.
	"""
	loi = []
	if not str(hop_dong or "").strip():
		loi.append("Chưa chọn hợp đồng tiệc.")
	if not str(kho or "").strip():
		loi.append("Chưa chọn kho xuất.")
	sach = gom_dong_xuat(dong)
	if not sach:
		loi.append("Chưa có dòng nguyên liệu nào có số lượng lớn hơn 0.")
	return loi


def tinh_lai_lo(doanh_thu, gia_von):
	"""Lai gop va ty le. THUAN.

	Ty le tra ve None khi chua co doanh thu, KHONG tra 0. Bao "lai 0 phan
	tram" khi chua xuat hoa don la noi sai: chua biet chu khong phai bang
	khong.
	"""
	dt = float(doanh_thu or 0)
	gv = float(gia_von or 0)
	lai = dt - gv
	ty_le = None if dt == 0 else round(lai * 100.0 / dt, 2)
	return {"doanh_thu": dt, "gia_von": gv, "lai_gop": lai, "ty_le": ty_le}


# ------------------------------------------------------- phan can Frappe

import frappe
from frappe.utils import flt, now_datetime, nowdate

# Ba truong moi, `after_migrate` tu dung lai sau moi lan deploy.
TRUONG_MOI = {
	"Stock Entry": [{
		"fieldname": "vgb_hop_dong", "label": "Hợp đồng tiệc",
		"fieldtype": "Link", "options": "Hop Dong Ban Hang",
		"insert_after": "project", "read_only": 1,
		"description":
			"Đường tắt từ phiếu xuất về hợp đồng tiệc. Neo thật để bóc giá "
			"vốn là ô Project ngay trên; ô này để người mở phiếu ra biết "
			"ngay nó thuộc tiệc nào, khỏi tra ngược.",
	}],
	"Stock Entry Detail": [{
		"fieldname": "vgb_ghi_chu", "label": "Ghi chú của bếp",
		"fieldtype": "Small Text", "insert_after": "expense_account",
		"description":
			"Bếp gõ khi cân, ví dụ đợt 1, đợt 2. Máy nối các lần gõ của "
			"cùng một mặt hàng lại chứ không bỏ đi.",
	}],
	"Hop Dong Ban Hang": [{
		"fieldname": "vgb_du_an", "label": "Dự án bóc giá vốn",
		"fieldtype": "Link", "options": "Project", "read_only": 1,
		"insert_after": "gia_tri", "description":
			"Máy tự tạo tại lần xuất nguyên liệu ĐẦU TIÊN, không tạo lúc "
			"lập hợp đồng. Phần lớn hợp đồng không phát sinh xuất kho "
			"riêng, tạo dự án cho tất cả chỉ làm bẩn danh mục Project.",
	}],
}


def _duoc_xem():
	"""Ai mo duoc man Don tiec."""
	from vagabond.xuat_kho import VAI_XUAT

	quyen = set(VAI_XUAT) | {"Giám đốc", "AP Giám đốc", "Sales User",
		"Manufacturing Manager", "Bếp phó"}
	if not quyen & set(frappe.get_roles()):
		frappe.throw("Màn Đơn tiệc dành cho bếp, kho và kinh doanh.")


def _duoc_xuat():
	"""Ai bam duoc nut xuat kho nguyen lieu.

	Dung lai Y NGUYEN `xuat_kho.VAI_XUAT` chu khong tu dat ten vai moi.
	Xuat NVL cho tiec VAN LA mot lan xuat kho; cung mot hanh vi ma hai
	cua doi hai quyen khac nhau la mot cho de tuot. Va ten vai tu bia ra
	co the khong ton tai trong he, luc do phep kiem im lang cho khong ai
	vao duoc.
	"""
	from vagabond.xuat_kho import VAI_XUAT

	if not set(VAI_XUAT) & set(frappe.get_roles()):
		frappe.throw(
			"Chỉ bộ phận kho mới xuất được nguyên liệu cho tiệc. "
			"Phiếu này ghi thẳng vào sổ kho và sổ cái.")


@frappe.whitelist()
def don_tiec(tu_ngay=None, den_ngay=None, trang_thai=None, gioi_han=60):
	"""Danh sach don tiec cho bep, mac dinh la cac tiec sap toi.

	Bep can biet hai thu: lam gi, va giao luc nao. Nen mac dinh chi hien
	hop dong DANG THUC HIEN va co ngay su kien tu hom nay tro di. Nhap va
	da gui khach thi chua chot, bep lam theo la lam theo mot ban con dang
	thuong thao.
	"""
	_duoc_xem()
	loc = {}
	loc["trang_thai"] = trang_thai if trang_thai else ["in", list(TT_BEP_THAY)]
	if tu_ngay and den_ngay:
		loc["ngay_su_kien"] = ["between", [tu_ngay, den_ngay]]
	elif tu_ngay:
		loc["ngay_su_kien"] = [">=", tu_ngay]
	elif den_ngay:
		loc["ngay_su_kien"] = ["<=", den_ngay]
	else:
		loc["ngay_su_kien"] = [">=", nowdate()]

	ds = frappe.get_all(
		"Hop Dong Ban Hang", filters=loc,
		fields=["name", "ten", "so_hop_dong", "loai", "trang_thai",
			"khach_hang", "ten_khach", "ngay_su_kien", "gia_tri",
			"dia_diem_giao", "thoi_gian_giao", "vgb_du_an"],
		order_by="ngay_su_kien asc", limit_page_length=int(gioi_han or 60),
	)
	if not ds:
		return {"ds": [], "tong": 0}

	# So lan da xuat NVL, hoi MOT lan cho ca danh sach. Hoi tung hop dong
	# la mot vong xuong co so du lieu cho moi the tren man hinh.
	dem = {}
	for r in frappe.get_all(
			"Stock Entry",
			filters={"vgb_hop_dong": ["in", [d.name for d in ds]],
				"docstatus": 1},
			fields=["vgb_hop_dong", "name"], limit_page_length=0):
		dem[r.vgb_hop_dong] = dem.get(r.vgb_hop_dong, 0) + 1

	ra = []
	for d in ds:
		ra.append({
			"hop_dong": d.name, "ten": d.ten or d.name,
			"so_hop_dong": d.so_hop_dong or "", "loai": d.loai or "",
			"trang_thai": d.trang_thai or "",
			"khach": d.ten_khach or d.khach_hang or "",
			"ngay_su_kien": str(d.ngay_su_kien or "")[:10],
			"gia_tri": flt(d.gia_tri),
			"dia_diem": d.dia_diem_giao or "",
			"gio_giao": d.thoi_gian_giao or "",
			"du_an": d.vgb_du_an or "",
			"so_lan_xuat": dem.get(d.name, 0),
		})
	return {"ds": ra, "tong": len(ra)}


@frappe.whitelist()
def chi_tiet_tiec(hop_dong=None):
	"""Mot tiec: dau bai, thuc don, va cac phieu xuat NVL da ghi so."""
	_duoc_xem()
	if not hop_dong or not frappe.db.exists("Hop Dong Ban Hang", hop_dong):
		frappe.throw("Không thấy hợp đồng %s." % hop_dong)
	hd = frappe.get_doc("Hop Dong Ban Hang", hop_dong)

	phieu = []
	tong = 0.0
	for se in frappe.get_all(
			"Stock Entry",
			filters={"vgb_hop_dong": hop_dong, "docstatus": ["<", 2]},
			fields=["name", "posting_date", "posting_time", "docstatus",
				"total_outgoing_value", "from_warehouse", "remarks"],
			order_by="posting_date asc, posting_time asc",
			limit_page_length=0):
		dong = frappe.get_all(
			"Stock Entry Detail", filters={"parent": se.name},
			fields=["item_code", "item_name", "qty", "uom", "amount",
				"vgb_ghi_chu"],
			order_by="idx asc", limit_page_length=0)
		gt = flt(se.total_outgoing_value)
		if int(se.docstatus or 0) == 1:
			tong += gt
		phieu.append({
			"phieu": se.name, "ngay": str(se.posting_date or "")[:10],
			"gio": str(se.posting_time or "")[:5],
			"da_ghi_so": 1 if int(se.docstatus or 0) == 1 else 0,
			"kho": se.from_warehouse or "", "gia_tri": gt,
			"ghi_chu": se.remarks or "",
			"dong": [{
				"ma": d.item_code, "ten": d.item_name or d.item_code,
				"sl": flt(d.qty), "dvt": d.uom or "",
				"tien": flt(d.amount), "ghi_chu": d.vgb_ghi_chu or "",
			} for d in dong],
		})

	return {
		"hop_dong": hd.name, "ten": hd.ten or hd.name,
		"so_hop_dong": hd.so_hop_dong or "", "loai": hd.loai or "",
		"trang_thai": hd.trang_thai or "",
		"khach": hd.ten_khach or hd.khach_hang or "",
		"ngay_su_kien": str(hd.ngay_su_kien or "")[:10],
		"gio_giao": hd.thoi_gian_giao or "",
		"dia_diem": hd.dia_diem_giao or "",
		"gia_tri": flt(hd.gia_tri), "mo_ta": hd.mo_ta or "",
		"du_an": hd.get("vgb_du_an") or "",
		"phieu": phieu, "tong_da_xuat": tong,
		"duoc_xuat": bool(_co_vai_xuat()),
	}


def _co_vai_xuat():
	from vagabond.xuat_kho import VAI_XUAT

	return bool(set(VAI_XUAT) & set(frappe.get_roles()))


def _dung_du_an(hd):
	"""Dung du an cho hop dong neu chua co. Tra ve ma du an.

	Tao MUON, tai lan xuat dau tien, chu khong tao ngay luc lap hop dong.
	Phan lon hop dong khong bao gio phat sinh xuat kho rieng, tao du an
	cho tat ca chi lam ban danh sach Project.
	"""
	da_co = hd.get("vgb_du_an")
	if da_co and frappe.db.exists("Project", da_co):
		return da_co
	ma = ma_du_an(hd.name)
	if not frappe.db.exists("Project", ma):
		du_an = frappe.get_doc({
			"doctype": "Project",
			"project_name": ma,
			"status": "Open",
			"expected_start_date": hd.get("ngay_su_kien") or nowdate(),
			"notes": "Dựng tự động cho hợp đồng tiệc %s (%s)." % (
				hd.name, hd.get("ten") or ""),
		})
		du_an.flags.ignore_permissions = True
		du_an.insert(ignore_permissions=True)
		ma = du_an.name
	frappe.db.set_value("Hop Dong Ban Hang", hd.name, "vgb_du_an", ma,
		update_modified=False)
	return ma


@frappe.whitelist()
def xuat_nvl(hop_dong=None, dong=None, ghi_chu=None, ngay=None, kho=None):
	"""Xuat nguyen lieu cho mot tiec. GHI THANG VAO SO KHO VA SO CAI.

	But toan sinh ra:

	    No  632 Gia von hang ban   (dat thang tren tung dong)
	    Co  152/155 Kho            (tai khoan cua kho nguon)

	Ca hai ve mang `project = TIEC-<ma hop dong>`, do la cai neo de bocs
	gia von cua rieng hop dong nay ra khoi so cai.
	"""
	_duoc_xuat()
	if isinstance(dong, str):
		import json as _json

		try:
			dong = _json.loads(dong)
		except ValueError:
			frappe.throw("Danh sách nguyên liệu gửi lên không đọc được.")

	loi = kiem_truoc_khi_xuat(hop_dong, kho, dong)
	if loi:
		frappe.throw("<br>".join(loi))
	if not frappe.db.exists("Hop Dong Ban Hang", hop_dong):
		frappe.throw("Không thấy hợp đồng %s." % hop_dong)
	if not frappe.db.exists("Warehouse", kho):
		frappe.throw("Không thấy kho %s." % kho)

	hd = frappe.get_doc("Hop Dong Ban Hang", hop_dong)
	du_an = _dung_du_an(hd)
	sach = gom_dong_xuat(dong)

	se = frappe.new_doc("Stock Entry")
	se.stock_entry_type = "Material Issue"
	se.purpose = "Material Issue"
	se.company = frappe.defaults.get_user_default("Company") or hd.get("company")
	se.from_warehouse = kho
	se.posting_date = ngay or nowdate()
	se.set_posting_time = 1 if ngay else 0
	# Neo THAT nam o dau phieu. `Stock Entry Detail` khong co truong
	# `project`, dat vao tung dong thi Frappe bo im lang.
	se.project = du_an
	se.vgb_hop_dong = hd.name
	se.remarks = (ghi_chu or "").strip() or (
		"Xuất nguyên liệu cho tiệc %s." % (hd.get("ten") or hd.name))

	for d in sach:
		ma = d["ma"]
		if not frappe.db.exists("Item", ma):
			frappe.throw("Không thấy mặt hàng %s." % ma)
		dvt = frappe.db.get_value("Item", ma, "stock_uom")
		se.append("items", {
			"item_code": ma,
			"s_warehouse": kho,
			"qty": d["sl"],
			"uom": dvt,
			"stock_uom": dvt,
			"conversion_factor": 1,
			# Dat THANG chu khong dua vao `stock_adjustment_account` cua
			# he: hom nao co nguoi doi cai dat chung thi luong tiec khong
			# am tham doi theo.
			"expense_account": TK_GIA_VON,
			"cost_center": frappe.db.get_value(
				"Company", se.company, "cost_center") or None,
			"vgb_ghi_chu": d["ghi_chu"],
		})

	se.flags.ignore_permissions = True
	se.insert(ignore_permissions=True)
	se.submit()
	frappe.db.commit()
	return {
		"ok": 1, "phieu": se.name, "du_an": du_an,
		"so_dong": len(sach), "gia_tri": flt(se.total_outgoing_value),
		"ghi_chu": "Đã ghi sổ phiếu %s, %d dòng, tổng %s đ." % (
			se.name, len(sach), "{:,.0f}".format(flt(se.total_outgoing_value))),
	}


@frappe.whitelist()
def huy_xuat_nvl(phieu=None, ly_do=None):
	"""Huy mot phieu xuat NVL da ghi so. HUY chu khong XOA.

	QT-20: khong bao gio xoa han mot chung tu. Huy thi but toan bi dao
	nguoc va phieu van tra lai duoc; xoa thi khong con gi de tra.
	"""
	_duoc_xuat()
	ly_do = (ly_do or "").strip()
	if not ly_do:
		frappe.throw("Phải ghi lý do huỷ. Phiếu này đã vào sổ kho và sổ cái.")
	if not phieu or not frappe.db.exists("Stock Entry", phieu):
		frappe.throw("Không thấy phiếu %s." % phieu)
	se = frappe.get_doc("Stock Entry", phieu)
	if not se.get("vgb_hop_dong"):
		frappe.throw(
			"Phiếu %s không phải phiếu xuất cho tiệc. Huỷ phiếu đó ở màn "
			"Xuất kho." % phieu)
	if int(se.docstatus or 0) != 1:
		frappe.throw("Phiếu %s chưa ghi sổ hoặc đã huỷ rồi." % phieu)
	se.flags.ignore_permissions = True
	se.cancel()
	try:
		se.add_comment("Comment", "Huỷ phiếu xuất tiệc: %s" % ly_do)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "tiec: ghi chu huy phieu")
	frappe.db.commit()
	return {"ok": 1, "phieu": phieu,
		"ghi_chu": "Đã huỷ phiếu %s. Phiếu vẫn tra lại được trên Desk." % phieu}


@frappe.whitelist()
def lai_lo(hop_dong=None):
	"""Lai lo cua mot hop dong, cong THANG TU SO CAI theo du an.

	Co y doc so cai chu khong cong tay tu Sales Invoice va Stock Entry: so
	cai la noi ke toan nhin, va neu hai cho lech nhau thi CAI LECH DO
	CHINH LA THU CAN BIET.
	"""
	_duoc_xem()
	if not hop_dong or not frappe.db.exists("Hop Dong Ban Hang", hop_dong):
		frappe.throw("Không thấy hợp đồng %s." % hop_dong)
	du_an = frappe.db.get_value("Hop Dong Ban Hang", hop_dong, "vgb_du_an")
	if not du_an:
		return dict(tinh_lai_lo(0, 0), du_an="", chua_co_du_an=1)

	dt = gv = 0.0
	for r in frappe.db.sql(
			"""
			select a.root_type as loai,
			       sum(g.credit) as co, sum(g.debit) as no
			from `tabGL Entry` g
			join `tabAccount` a on a.name = g.account
			where g.project = %(da)s and g.is_cancelled = 0
			group by a.root_type
			""",
			{"da": du_an}, as_dict=True):
		if r.loai == "Income":
			dt += flt(r.co) - flt(r.no)
		elif r.loai == "Expense":
			gv += flt(r.no) - flt(r.co)
	return dict(tinh_lai_lo(dt, gv), du_an=du_an, chua_co_du_an=0)

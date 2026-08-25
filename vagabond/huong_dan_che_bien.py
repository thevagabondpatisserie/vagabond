# -*- coding: utf-8 -*-
"""Huong dan che bien: ban thuyet minh cach lam, di kem cong thuc.

Viec anh Viet giao 25/08/2026
-----------------------------
Cong thuc tren he chuyen TRUNG sang don vi QUA. Anh Viet hoi dung cho:
*"vay co nhung cong thuc su dung long trang thi sao ma biet duoc, neu BOM
de la qua?"*

Ban Khai tra loi: *"vi du cai mo York, Egg white... minh quy uoc thanh
trung tren BOM (thi ho cung thay Qua thoi, nhung co thuyet minh Quy trinh
san xuat se biet la so Gam / Long do, so Gam / Long trang). BOM la luong
NVL de lam plan, yeu cau... Quy trinh cong nghe san xuat bo tro cho BOM de
thuc hien san xuat."*

Dung. Va do chinh la ly do tep nay ton tai: BOM tra loi cau "mua bao nhieu,
gia bao nhieu", huong dan tra loi cau "lam the nao cho ra dung mon do".
Hai cau khac nhau, hai cho khac nhau.


Frappe co san luong nao chua
============================
Co ba luong gan giong, da tra tren site that ngay 25/08/2026:

  Routing                       0 ban ghi
  Operation                     1 ban ghi
  Quality Inspection Template   0 ban ghi
  Quality Procedure             0 ban ghi

Tuc la co san nhung tiem chua dung cai nao. Va khong cai nao vua:

1. `Routing` va `Operation` sinh ra cho DIEU DO CONG SUAT: moi cong doan
   gan mot to may (Workstation) va mot so phut, de he xep lich chay may.
   Nhet cach lam banh vao do thi keo theo ca may moc va lich xuong, ma
   tiem khong dieu do theo kieu do. Dung sai cho la sau nay muon dung
   dung cach lai phai go ra.

2. `Quality Inspection Template` chi giu THONG SO do duoc (min, max, cong
   thuc). Khong co cho de anh mau, ma "the nao la dat" cua tiem banh phan
   lon la nhin bang mat.

3. Ca hai deu khong co cho de anh tung buoc, va deu khong nhap tay tren
   dien thoai duoc: form Desk cua Frappe tren dien thoai rat kho go.

Nen dung rieng. Nhung KHONG dung lai tu dau nhung gi Frappe da lam tot:
truong `Attach Image` xu ly anh, `Table` xu ly bang con, `track_changes`
xu ly lich su sua doi, va Print Format xu ly ban in.


Ba quyet dinh dang noi
======================

1. GAN VAO MON, KHONG GAN VAO CONG THUC
   Cong thuc co phien ban that: tren he dang co BOM-BTPB00007-001-1,
   BOM-BTPB00004-002... Gan huong dan vao mot ban cu the thi moi lan bep
   doi cong thuc la huong dan mo coi.
   Gan vao MON thi huong dan song lau bang mon. Van giu o `bom_soan_theo`
   ghi lai soan theo ban nao, va `cong_thuc_da_doi` tu bat len khi cong
   thuc mac dinh cua mon khong con la ban do nua. Bep nhin thay ngay la
   huong dan nay da cu, thay vi lam theo mot ban da bi thay.

2. BANG DINH LUONG NAM O DAY, KHONG NAM O BOM
   Day la cho tra loi cau hoi cua anh Viet. BOM ghi "trung 8,333 Qua".
   Bang dinh luong ghi "long trang 300 gram, tach tu 8,333 qua" va "long
   do 200 gram, tach tu 8,333 qua". O `tach_tu` sinh ra chinh vi cau hoi
   do.
   Co y KHONG bat bang nay phai khop voi BOM: mot ben la luong mua, mot
   ben la luong dung, va giua hai ben co hao hut. Bat khop la ep nguoi
   soan noi doi.

3. KHONG GHI SO, KHONG DUYET HAI CAP
   Huong dan la tai lieu huong dan, khong phai chung tu. Chi co ba trang
   thai Nhap, Dang dung, Ngung dung. Them luong duyet nhieu cap vao day
   thi bep se khong cap nhat nua, va mot ban huong dan cu ma khong ai sua
   con nguy hiem hon la khong co ban nao.
"""

# ------------------------------------------------------------ phan thuan

DT = "Vagabond Huong Dan Che Bien"

TT_NHAP = "Nháp"
TT_DUNG = "Đang dùng"
TT_NGUNG = "Ngừng dùng"
TRANG_THAI = (TT_NHAP, TT_DUNG, TT_NGUNG)

# Ban in A4 dan tuong bep. Anh Viet chot 25/08/2026: co lam.
MAU_IN = "Vagabond - Hướng dẫn chế biến"

# Sau nhom di ung hay gap trong tiem banh. Chi la GOI Y de nguoi soan bam
# nhanh, khong phai danh sach dong: cong thuc moi co the co thu khac.
GOI_Y_DI_UNG = (
	"Trứng", "Sữa và chế phẩm từ sữa", "Gluten (lúa mì)",
	"Hạt cây (hạnh nhân, hạt điều, óc chó)", "Đậu phộng", "Đậu nành",
)


def tong_thoi_gian(chuan_bi, lam, nghi):
	"""Tong so phut cua mot me. THUAN.

	Cong ca ba chang chu khong chi chang lam: bep xep lich theo luc bat
	dau tinh den luc co thanh pham, ma banh thi phan lon thoi gian nam o
	chang nghi va u.
	"""
	ra = 0
	for v in (chuan_bi, lam, nghi):
		try:
			ra += int(v or 0)
		except (TypeError, ValueError):
			pass
	return ra


def thieu_gi(doc):
	"""Huong dan nay con thieu gi de dung duoc. THUAN.

	Tra ve danh sach cau nhac. Rong nghia la du dung.

	Co y KHONG chan luu khi con thieu: bep truong go dan tren dien thoai,
	chan luu la ho bo cuoc. Chi chan luc chuyen sang "Dang dung".
	"""
	doc = doc or {}
	nhac = []
	if not (doc.get("buoc") or []):
		nhac.append("Chưa có bước làm nào.")
	if not (doc.get("dinh_luong") or []):
		nhac.append("Chưa có bảng định lượng. Đây là chỗ ghi số gram thật, "
					"gồm cả lòng trắng và lòng đỏ.")
	if not str(doc.get("anh_dat_chinh") or "").strip():
		nhac.append("Chưa có ảnh món đạt. QC cần ảnh này để so.")
	if not str(doc.get("di_ung") or "").strip():
		nhac.append("Chưa khai cảnh báo dị ứng. Khách B2B và khách đặt tiệc "
					"hay hỏi, để trống là không trả lời được.")
	tt = str(doc.get("trang_thai") or "")
	if tt == TT_DUNG and not str(doc.get("nguoi_duyet") or "").strip():
		nhac.append("Đang dùng mà chưa có người duyệt.")
	return nhac


def buoc_toi_han(buoc):
	"""Cac buoc co danh dau diem toi han. THUAN.

	Ban Word cua to san xuat dang danh dau OPRP o khau nguyen lieu dau vao
	va khau can. Giu lai dung do, vi do la thu doan kiem tra ATTP se hoi.
	"""
	ra = []
	for i, b in enumerate(buoc or []):
		b = b or {}
		muc = str(b.get("diem_toi_han") or "").strip()
		if muc:
			ra.append({
				"stt": i + 1,
				"cong_doan": str(b.get("cong_doan") or "").strip(),
				"muc": muc,
				"bieu_mau": str(b.get("bieu_mau") or "").strip(),
			})
	return ra


# ------------------------------------------------------- phan can Frappe

import frappe
from frappe.utils import now_datetime

# Bep pho THEM 25/08/2026 theo quyet dinh cua anh Viet. Bep pho la nguoi
# dung bep hang ngay, chinh ho moi biet buoc nao thuc te lam khac voi ban
# soan. Bat ho phai nho bep truong sua tung chu la huong dan se khong bao
# gio duoc cap nhat.
VAI_SUA = {"System Manager", "Manufacturing Manager", "Giám đốc", "AP Giám đốc",
		   "Bếp phó"}
VAI_XEM = VAI_SUA | {"Manufacturing User", "Stock User", "Bộ phận đặt hàng"}


def _vai_sua():
	from vagabond.vai_cua_hang import VAI_QLCT

	if not (VAI_SUA | {VAI_QLCT}) & set(frappe.get_roles()):
		frappe.throw("Chỉ bếp trưởng, bếp phó, quản lý công thức hoặc giám đốc "
					 "mới sửa được hướng dẫn chế biến.")


def _vai_xem():
	from vagabond.vai_cua_hang import VAI_QLCT

	if not (VAI_XEM | {VAI_QLCT}) & set(frappe.get_roles()):
		frappe.throw("Màn Hướng dẫn chế biến dành cho bếp và quản lý sản xuất.")


@frappe.whitelist()
def danh_sach(tu_khoa=None, trang_thai=None, gioi_han=60):
	"""Danh sach huong dan, kem co bao nhieu mon CHUA co huong dan."""
	_vai_xem()
	loc = {}
	if trang_thai:
		loc["trang_thai"] = trang_thai
	if tu_khoa:
		loc["ten_mon"] = ["like", "%" + str(tu_khoa).strip() + "%"]
	ds = frappe.get_all(
		DT, filters=loc,
		fields=["name", "ma_mon", "ten_mon", "nhom_mon", "trang_thai",
				"anh_dat_chinh", "cong_thuc_da_doi", "modified"],
		order_by="modified desc", limit_page_length=int(gioi_han or 60),
	)
	for d in ds:
		d["so_buoc"] = frappe.db.count("Vagabond HDCB Buoc", {"parent": d["name"]})
	return {"danh_sach": ds, "so_mon_chua_co": _dem_mon_chua_co()}


def _dem_mon_chua_co():
	"""Bao nhieu mon co cong thuc ma chua co huong dan."""
	co_bom = set(frappe.get_all(
		"BOM", filters={"docstatus": 1, "is_active": 1}, pluck="item"
	))
	co_hd = set(frappe.get_all(DT, pluck="ma_mon"))
	return len(co_bom - co_hd)


@frappe.whitelist()
def chi_tiet(name=None, ma_mon=None):
	"""Mot huong dan. Truyen ma_mon thi tra ban cua mon do, chua co thi rong."""
	_vai_xem()
	if not name and ma_mon:
		name = frappe.db.get_value(DT, {"ma_mon": ma_mon}, "name")
	if not name:
		return {"chua_co": 1, "ma_mon": ma_mon}
	doc = frappe.get_doc(DT, name)
	d = doc.as_dict()
	d["thieu"] = thieu_gi(d)
	d["diem_toi_han"] = buoc_toi_han(d.get("buoc"))
	d["tong_phut"] = tong_thoi_gian(d.get("tg_chuan_bi"), d.get("tg_lam"), d.get("tg_nghi"))
	d["goi_y_di_ung"] = list(GOI_Y_DI_UNG)
	d["mau_in"] = MAU_IN
	return d


@frappe.whitelist()
def luu(du_lieu=None):
	"""Tao moi hoac ghi de mot huong dan. Nhan mot goi JSON tu man hinh."""
	_vai_sua()
	if isinstance(du_lieu, str):
		import json as _json
		try:
			du_lieu = _json.loads(du_lieu)
		except ValueError:
			frappe.throw("Dữ liệu gửi lên không đọc được.")
	du_lieu = du_lieu or {}
	ma_mon = str(du_lieu.get("ma_mon") or "").strip()
	if not ma_mon:
		frappe.throw("Chưa chọn món.")
	if not frappe.db.exists("Item", ma_mon):
		frappe.throw("Không thấy món %s trên hệ." % ma_mon)

	ten = du_lieu.get("name") or frappe.db.get_value(DT, {"ma_mon": ma_mon}, "name")
	if ten:
		doc = frappe.get_doc(DT, ten)
	else:
		doc = frappe.new_doc(DT)
		doc.ma_mon = ma_mon
		doc.nguoi_soan = frappe.session.user
		doc.ngay_soan = now_datetime()

	for o in ("trang_thai", "me_chuan", "dvt_me", "nang_suat", "hao_hut_cho_phep",
			  "tg_chuan_bi", "tg_lam", "tg_nghi", "dung_cu", "anh_dat_chinh",
			  "di_ung", "han_su_dung", "bao_quan", "ghi_chu", "bom_soan_theo"):
		if o in du_lieu:
			doc.set(o, du_lieu.get(o))

	for bang in ("buoc", "dinh_luong", "tieu_chi"):
		if bang in du_lieu:
			doc.set(bang, [])
			for dong in (du_lieu.get(bang) or []):
				doc.append(bang, dong or {})

	# Chuyen sang "Dang dung" thi moi soi du thieu. Con nhap do dang thi
	# cu luu, bep truong go dan tren dien thoai.
	if str(doc.trang_thai or "") == TT_DUNG:
		thieu = thieu_gi(doc.as_dict())
		if thieu:
			frappe.throw("Chưa dùng được, còn thiếu:<br>- " + "<br>- ".join(thieu))
		if not doc.nguoi_duyet:
			doc.nguoi_duyet = frappe.session.user
			doc.ngay_duyet = now_datetime()

	doc.phien_ban = int(doc.phien_ban or 0) + 1
	doc.cong_thuc_da_doi = 0 if _con_khop(doc) else 1
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "name": doc.name, "phien_ban": doc.phien_ban}


def _con_khop(doc):
	"""Huong dan nay con soan theo dung cong thuc mac dinh cua mon khong."""
	if not doc.get("bom_soan_theo"):
		return True
	mac_dinh = frappe.db.get_value(
		"BOM", {"item": doc.ma_mon, "is_default": 1, "docstatus": 1}, "name"
	)
	return (not mac_dinh) or mac_dinh == doc.bom_soan_theo


@frappe.whitelist()
def soat_cong_thuc_da_doi():
	"""Nhip: bat co cho moi huong dan da lech khoi cong thuc mac dinh.

	Chay tay hoac gan lich sau. Chi doi mot o co, khong dong vao noi dung.
	"""
	_vai_xem()
	doi = []
	for d in frappe.get_all(DT, fields=["name", "ma_mon", "bom_soan_theo", "cong_thuc_da_doi"]):
		if not d.bom_soan_theo:
			continue
		mac_dinh = frappe.db.get_value(
			"BOM", {"item": d.ma_mon, "is_default": 1, "docstatus": 1}, "name"
		)
		lech = 1 if (mac_dinh and mac_dinh != d.bom_soan_theo) else 0
		if lech != int(d.cong_thuc_da_doi or 0):
			frappe.db.set_value(DT, d.name, "cong_thuc_da_doi", lech)
			doi.append({"huong_dan": d.name, "mon": d.ma_mon, "da_doi": lech})
	frappe.db.commit()
	return {"so_ban_doi_co": len(doi), "chi_tiet": doi}


def dung_mau_in():
	"""Tao ban ghi Print Format lan dau, neu chua co. Goi tu after_migrate.

	`mau_in.dong_bo()` CO Y khong tu tao ban ghi moi (xem doc cua no): mot
	ban ghi sinh ra lang le trong luc migrate thi khong ai biet no tu dau
	ra. Nen viec tao lan dau nam o day, co ten ham ro rang, chu khong nup
	trong nhip dong bo chung.

	Tao xong thi phan noi dung HTML de `mau_in.dong_bo()` giu dong bo nhu
	moi mau in khac cua tiem.
	"""
	try:
		if frappe.db.exists("Print Format", MAU_IN):
			return 0
		from vagabond.mau_in import doc_mau
		from vagabond.mau_in.le_in import LE_MM

		doc = frappe.get_doc({
			"doctype": "Print Format",
			"name": MAU_IN,
			"doc_type": DT,
			"module": "Vagabond",
			"standard": "No",
			"print_format_type": "Jinja",
			"custom_format": 1,
			"raw_printing": 0,
			"disabled": 0,
			"margin_top": LE_MM, "margin_bottom": LE_MM,
			"margin_left": LE_MM, "margin_right": LE_MM,
			"html": doc_mau("huong_dan_che_bien.html"),
		})
		doc.flags.ignore_permissions = True
		doc.insert(ignore_permissions=True)
		return 1
	except Exception:
		# Khong bao gio duoc lam hong after_migrate.
		frappe.log_error(frappe.get_traceback(), "huong_dan_che_bien: dung mau in")
		return 0

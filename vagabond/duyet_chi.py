# -*- coding: utf-8 -*-
"""Tach buoc DUYET CHI ra khoi buoc GHI SO tren phieu chi.

Anh Viet 03/09/2026, kem anh phieu APP-26-09-050:

    *"APP ma giam doc duyet xong sao lai de trang thai la da thanh toan?
    Giam doc duyet la moi duyet chi thoi, ke toan chi tien roi dinh kem UNC,
    khop giao dich SePay vao thi moi ghi so va chuyen trang thai da thanh
    toan chu."*

Anh dung. Duong duyet phieu chi dang chay gop hai viec vao mot buoc:

    Nhap -> Cho FIN kiem tra -> Cho giam doc duyet -> "Da duyet - Da ghi so"

Buoc cuoi vua la chu ky cua giam doc vua la lenh ghi so (no dat trang thai
chung tu sang da ghi so). Nghia la giam doc bam Duyet chi mot cai la:

  - tien roi khoi so, cong no nha cung cap giam,
  - trong khi CHUA AI chuyen mot dong nao,
  - chua co uy nhiem chi nao,
  - chua doi chieu voi mot giao dich ngan hang nao.

Sai o cho nao: duyet chi la mot LOI HUA se tra, con ghi so la ghi nhan tien
DA ROI khoi tai khoan. Gop hai cai lam mot thi so sach luon di truoc thuc te,
va cai gia phai tra chi lo ra vao cuoi thang khi so du ngan hang khong khop
voi so du tren so.

Duong moi, them dung mot buoc:

    ... -> Cho giam doc duyet -> DA DUYET CHI, CHO CHUYEN TIEN -> Da ghi so
                                (giam doc ky)            (ke toan xac nhan)

Buoc moi KHONG ghi so. Ke toan chuyen tien that, dinh uy nhiem chi, doi
chieu voi giao dich SePay, roi moi bam mot nut de phieu ghi so.

BA HANG RAO khi ghi so, cai nao thieu cung chan:

  1. Phieu phai da qua chu ky giam doc.
  2. Phai co it nhat mot to uy nhiem chi dinh kem.
  3. Giao dich ngan hang mang ma phieu phai da ve, va tong tien chi ra
     phai du.

Rieng hang rao ba co duong thoat CO VET: chuyen khoan lien ngan hang ngoai
gio thi giao dich co the ve cham, ma tien thi da di that. Ke toan truong go
mot cau ly do la ghi so duoc, va cau do nam lai tren phieu cho ky sau doc.
Khong co duong thoat nay thi den luc ket, nguoi ta se tim cach vong qua ca
he thong, va vong qua thi khong con vet nao het.

Tep nay giu phep THUAN o dau va phan cham Frappe o cuoi.
"""

import frappe
from frappe.utils import cint, flt

PE = "Payment Entry"
PO = "Purchase Order"

TEN_WORKFLOW = "Duyet phieu chi APP"

# Ten cac buoc. Ba buoc dau va buoc cuoi GIU NGUYEN TEN CU: tren he dang co
# phieu mang dung nhung chuoi nay trong o trang thai, doi ten la phieu cu tro
# vao mot buoc khong con ton tai.
TT_NHAP = "Nháp"
TT_CHO_FIN = "Chờ FIN kiểm tra"
TT_CHO_GD = "Chờ giám đốc duyệt"
TT_DA_DUYET_CHI = "Đã duyệt chi - chờ chuyển tiền"
TT_DA_GHI_SO = "Đã duyệt - Đã ghi sổ"
TT_TRA_LAI = "Bị trả lại"

# Nhan doc tren app. O trang thai cu ten la "Da duyet - Da ghi so", nhung tu
# nay no chi con nghia "tien da di va da ghi so", nen app doc khac di.
NHAN = {
	TT_NHAP: "Nháp",
	TT_CHO_FIN: "Chờ kế toán kiểm tra",
	TT_CHO_GD: "Chờ giám đốc duyệt chi",
	TT_DA_DUYET_CHI: "Đã duyệt chi, chờ chuyển tiền",
	TT_DA_GHI_SO: "Đã chuyển tiền, đã ghi sổ",
	TT_TRA_LAI: "Bị trả lại",
}

# Buoc chua ghi so: tien chua di, phieu con phai co nguoi dung tay vao.
TT_CHUA_GHI_SO = (TT_NHAP, TT_CHO_FIN, TT_CHO_GD, TT_DA_DUYET_CHI, TT_TRA_LAI)

VAI_GD = {"AP Giám đốc", "System Manager"}
VAI_FIN = {"AP Kiểm soát (FIN)", "Accounts Manager", "Accounts User", "System Manager"}
# Ai duoc ghi so khi giao dich ngan hang chua ve. Hep hon VAI_FIN mot bac.
VAI_BO_QUA_SEPAY = {"Accounts Manager", "System Manager"}

# Sai lech cho phep giua tien tren phieu va tien ngan hang bao da chi.
# Mot dong: chenh vai tram dong la phi chuyen khoan hoac lam tron.
SAI_LECH_CHO_PHEP = 1.0


# ------------------------------------------------------------- phep THUAN


def nhan_buoc(buoc):
	"""Ten buoc doc duoc tren app."""
	return NHAN.get(str(buoc or "").strip(), str(buoc or "").strip())


def chua_ghi_so(buoc):
	"""Phieu o buoc nay thi tien chua ra khoi so."""
	return str(buoc or "").strip() in TT_CHUA_GHI_SO


def sepay_du(tien_phieu, tien_da_chi):
	"""Giao dich ngan hang mang ma phieu da du tien chua."""
	return 1 if flt(tien_da_chi) >= flt(tien_phieu) - SAI_LECH_CHO_PHEP else 0


def soat_ghi_so(buoc, so_unc, tien_phieu, tien_da_chi, ly_do_som="", duoc_bo_qua=0):
	"""Phieu nay ghi so duoc chua. Tra ve {"ok", "vi_sao", "thieu"}.

	`thieu` la danh sach ma nhung dieu kien con thieu, de man hinh biet to
	do dung o nao thay vi chi hien mot cau chung chung.
	"""
	thieu = []
	if str(buoc or "").strip() != TT_DA_DUYET_CHI:
		thieu.append("chua_duyet")
	if cint(so_unc) <= 0:
		thieu.append("thieu_unc")
	du = sepay_du(tien_phieu, tien_da_chi)
	if not du:
		if (ly_do_som or "").strip() and cint(duoc_bo_qua):
			pass
		else:
			thieu.append("chua_ve_tien")
	if not thieu:
		return {"ok": 1, "vi_sao": "", "thieu": []}
	return {"ok": 0, "vi_sao": cau_thieu(thieu, tien_phieu, tien_da_chi), "thieu": thieu}


def cau_thieu(thieu, tien_phieu=0, tien_da_chi=0):
	"""Cau noi cho nguoi dung, noi ro thieu gi va phai lam gi."""
	cau = []
	if "chua_duyet" in thieu:
		cau.append(
			"Phiếu chưa qua chữ ký giám đốc. Duyệt chi xong mới tới bước "
			"chuyển tiền."
		)
	if "thieu_unc" in thieu:
		cau.append(
			"Chưa đính uỷ nhiệm chi. Chuyển tiền xong thì chụp hoặc tải tờ "
			"uỷ nhiệm chi lên phiếu, đó là bằng chứng tiền đã rời tài khoản."
		)
	if "chua_ve_tien" in thieu:
		cau.append(
			"Chưa thấy giao dịch ngân hàng nào mang mã phiếu này, hoặc số "
			"tiền chưa đủ (%s trên %s). Chờ ngân hàng đẩy về, hoặc nếu tiền "
			"đã đi thật thì kế toán trưởng ghi một câu lý do rồi ghi sổ."
			% (_tien(tien_da_chi), _tien(tien_phieu))
		)
	return "<br><br>".join(cau)


def _tien(x):
	try:
		return "{:,.0f} đ".format(float(x or 0)).replace(",", ".")
	except Exception:
		return "0 đ"


def khuon_workflow():
	"""Khuon duong duyet phieu chi, dung de dung lai bang ma nguon.

	Tra ve (states, transitions) dang danh sach tu dien THUAN, khong cham
	Frappe, de ca kiem doc duoc ma khong can site.
	"""
	states = [
		{"state": TT_NHAP, "doc_status": "0", "allow_edit": "AP Officer"},
		{"state": TT_CHO_FIN, "doc_status": "0", "allow_edit": "AP Kiểm soát (FIN)"},
		{"state": TT_CHO_GD, "doc_status": "0", "allow_edit": "AP Giám đốc"},
		# Buoc moi. doc_status 0: chu ky cua giam doc KHONG ghi so.
		{"state": TT_DA_DUYET_CHI, "doc_status": "0", "allow_edit": "AP Kiểm soát (FIN)"},
		{"state": TT_DA_GHI_SO, "doc_status": "1", "allow_edit": "AP Kiểm soát (FIN)"},
		{"state": TT_TRA_LAI, "doc_status": "0", "allow_edit": "AP Officer"},
	]
	trans = [
		{"state": TT_NHAP, "action": "Gửi kiểm tra", "next_state": TT_CHO_FIN,
			"allowed": "AP Officer"},
		{"state": TT_CHO_FIN, "action": "Xác nhận hợp lệ", "next_state": TT_CHO_GD,
			"allowed": "AP Kiểm soát (FIN)"},
		{"state": TT_CHO_FIN, "action": "Trả lại", "next_state": TT_TRA_LAI,
			"allowed": "AP Kiểm soát (FIN)"},
		# Giam doc ky. KHONG con di thang toi buoc ghi so nua.
		{"state": TT_CHO_GD, "action": "Duyệt chi", "next_state": TT_DA_DUYET_CHI,
			"allowed": "AP Giám đốc"},
		{"state": TT_CHO_GD, "action": "Trả lại", "next_state": TT_TRA_LAI,
			"allowed": "AP Giám đốc"},
		# Ke toan xac nhan tien da di. Day moi la luc phieu ghi so.
		{"state": TT_DA_DUYET_CHI, "action": "Xác nhận đã chuyển tiền",
			"next_state": TT_DA_GHI_SO, "allowed": "AP Kiểm soát (FIN)"},
		{"state": TT_DA_DUYET_CHI, "action": "Trả lại", "next_state": TT_TRA_LAI,
			"allowed": "AP Kiểm soát (FIN)"},
		{"state": TT_TRA_LAI, "action": "Gửi kiểm tra", "next_state": TT_CHO_FIN,
			"allowed": "AP Officer"},
	]
	return states, trans


# ---------------------------------------------------------- cham Frappe

# O ghi vet tren phieu chi. Ba o deu chi de DOC LAI, khong o nao dung vao
# con so tien.
TRUONG_MOI = {
	"Vagabond Ho So TT": [
		{
			"fieldname": "vgb_tt_ly_do_som",
			"label": "Lý do ghi nhận khi chưa thấy giao dịch",
			"fieldtype": "Small Text",
			"read_only": 1,
			"description": (
				"Kế toán trưởng ghi khi tiền đã chuyển thật mà giao dịch ngân "
				"hàng chưa đẩy về. Để lại cho kỳ sau đối chiếu."
			),
		},
	],
	"Payment Entry": [
		{
			"fieldname": "vgb_chi_ma_gd",
			"label": "Mã giao dịch ngân hàng",
			"fieldtype": "Data",
			"read_only": 1,
			"description": "Số tham chiếu của giao dịch chuyển tiền, máy ghi khi kế toán xác nhận.",
		},
		{
			"fieldname": "vgb_chi_ly_do_som",
			"label": "Lý do ghi sổ khi chưa thấy giao dịch",
			"fieldtype": "Small Text",
			"read_only": 1,
			"description": (
				"Kế toán trưởng ghi câu này khi tiền đã chuyển thật mà giao "
				"dịch ngân hàng chưa đẩy về. Để lại cho kỳ sau đối chiếu."
			),
		},
		{
			"fieldname": "vgb_chi_boi",
			"label": "Người xác nhận đã chuyển tiền",
			"fieldtype": "Data",
			"read_only": 1,
		},
		{
			"fieldname": "vgb_chi_unc",
			"label": "Uỷ nhiệm chi của phiếu này",
			"fieldtype": "Small Text",
			"read_only": 1,
			"description": (
				"Kế toán đánh dấu ĐÚNG tờ nào là uỷ nhiệm chi, lúc bấm xác "
				"nhận đã chuyển tiền. Đếm mọi tệp đính kèm thì bảng báo giá "
				"cũng tính là uỷ nhiệm chi, và hàng rào thành ra không rào gì."
			),
		},
	],
}


def dung_workflow():
	"""Dung lai duong duyet phieu chi bang ma nguon. Goi tu after_migrate.

	Lam lai duoc khong gioi han lan. KHONG dung vao phieu nao dang chay: chi
	dat lai danh sach buoc va danh sach duong di cua ban thiet ke.
	"""
	try:
		if not frappe.db.exists("Workflow", TEN_WORKFLOW):
			# Chua co thi khong tu dung moi: duong duyet dinh toi tien, dung
			# ra roi khong ai hay la nguy hiem hon la khong co. Ghi lai de
			# nguoi doc Error Log biet ma dung tay.
			frappe.log_error(
				"Chua co duong duyet %s tren he nay, khong tu dung." % TEN_WORKFLOW,
				"duyet_chi: thieu workflow",
			)
			return
		w = frappe.get_doc("Workflow", TEN_WORKFLOW)
		states, trans = khuon_workflow()
		cu_state = {s.state: s for s in (w.states or [])}
		w.set("states", [])
		for s in states:
			cu = cu_state.get(s["state"])
			w.append("states", {
				"state": s["state"],
				"doc_status": s["doc_status"],
				"allow_edit": s["allow_edit"],
				"update_field": cu.update_field if cu else None,
				"update_value": cu.update_value if cu else None,
			})
		w.set("transitions", [])
		for t in trans:
			w.append("transitions", {
				"state": t["state"],
				"action": t["action"],
				"next_state": t["next_state"],
				"allowed": t["allowed"],
			})
		w.is_active = 1
		w.flags.ignore_permissions = True
		w.save(ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "duyet_chi: dung workflow")


def la_phieu_chi_app(doc):
	"""Phieu nay co thuoc duong duyet phieu chi khong.

	Nhan dien bang NEO VAO DON MUA: phieu tra truoc neo vao Purchase Order,
	con but toan cua man Ho so thanh toan neo vao Purchase Invoice. Nho vay
	hang rao o day khong bao gio cham vao luong kia.
	"""
	if (doc.get("payment_type") or "") != "Pay":
		return 0
	if (doc.get("party_type") or "") != "Supplier":
		return 0
	for r in doc.get("references") or []:
		if (r.get("reference_doctype") or "") == PO:
			return 1
	return 0


def _so_unc(doc):
	"""So to uy nhiem chi cua phieu.

	Dem o `vgb_chi_unc` chu KHONG dem moi tep dinh kem. Phieu APP-26-09-050
	co ba tep dinh kem ma ca ba deu la bang bao gia va hoa don dau vao; dem
	tep dinh kem thi hang rao xanh trong khi chua ai chuyen mot dong nao.
	"""
	try:
		from vagabond import tep_dinh_kem

		return len(tep_dinh_kem.doc_ds(doc.get("vgb_chi_unc")))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "duyet_chi: dem UNC")
		return 0


def _da_chi_theo_sepay(ten_phieu):
	"""Tien ngan hang bao da chi ra cho ma phieu nay."""
	try:
		from vagabond.ho_so_tt import _sepay_theo_ma_app

		g = _sepay_theo_ma_app([ten_phieu]) or {}
		o = g.get(ten_phieu) or {}
		return flt(o.get("chi")), (o.get("ma_gd") or "")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "duyet_chi: doc SePay")
		return 0.0, ""


def chan_ghi_so_som(doc, method=None):
	"""Chan phieu chi ghi so khi tien chua thuc su di.

	Dat o `before_submit`: luu nhap thi cu cho luu, chi chan dung luc con so
	sap cham vao so cai. Hang rao nay soi CA hai duong - nut tren Desk va
	nut tren app - vi ca hai deu di qua day.
	"""
	try:
		if not la_phieu_chi_app(doc):
			return
		if cint(doc.get("vgb_da_soat_duyet_chi") or 0):
			return
		if doc.flags.get("vgb_da_soat_duyet_chi"):
			return
		so_unc = _so_unc(doc)
		da_chi, _ = _da_chi_theo_sepay(doc.name)
		kq = soat_ghi_so(
			doc.get("workflow_state"),
			so_unc,
			flt(doc.get("paid_amount")),
			da_chi,
			doc.get("vgb_chi_ly_do_som") or "",
			1 if (VAI_BO_QUA_SEPAY & set(frappe.get_roles())) else 0,
		)
	except Exception:
		# Hang rao hong KHONG duoc chan ca duong tien: ghi lai roi cho di
		# tiep, vi chan nham con te hon khong chan.
		frappe.log_error(frappe.get_traceback(), "duyet_chi: soat truoc khi ghi so")
		return
	if kq["ok"]:
		return
	frappe.throw(kq["vi_sao"], title="Chưa ghi sổ phiếu chi được")


@frappe.whitelist()
def tinh_hinh(name):
	"""Phieu nay dang thieu gi de ghi so. Chi DOC, khong ghi gi."""
	_kiem_quyen_fin()
	doc = frappe.get_doc(PE, name)
	so_unc = _so_unc(doc)
	da_chi, ma_gd = _da_chi_theo_sepay(doc.name)
	kq = soat_ghi_so(
		doc.get("workflow_state"), so_unc, flt(doc.paid_amount), da_chi,
		doc.get("vgb_chi_ly_do_som") or "",
		1 if (VAI_BO_QUA_SEPAY & set(frappe.get_roles())) else 0,
	)
	return {
		"name": doc.name,
		"buoc": doc.get("workflow_state") or "",
		"nhan": nhan_buoc(doc.get("workflow_state")),
		"tong_tien": flt(doc.paid_amount),
		"so_unc": so_unc,
		"da_chi": da_chi,
		"ma_gd": ma_gd,
		"du_tien": sepay_du(flt(doc.paid_amount), da_chi),
		"ghi_so_duoc": kq["ok"],
		"thieu": kq["thieu"],
		"vi_sao": kq["vi_sao"],
		"duoc_bo_qua_sepay": 1 if (VAI_BO_QUA_SEPAY & set(frappe.get_roles())) else 0,
		"da_ghi_so": 1 if cint(doc.docstatus) == 1 else 0,
	}


def _kiem_quyen_fin():
	if not (VAI_FIN & set(frappe.get_roles())):
		frappe.throw("Chỉ kế toán mới xác nhận chuyển tiền được.")


@frappe.whitelist()
def xac_nhan_da_chuyen(name, ma_giao_dich=None, ly_do_som=None, unc=None):
	"""Ke toan xac nhan tien da chuyen: soat ba hang rao roi ghi so.

	Day la buoc duy nhat dua phieu chi vao so. Truoc buoc nay phieu chi la
	mot loi hua co chu ky, khong phai mot khoan tien da di.
	"""
	_kiem_quyen_fin()
	doc = frappe.get_doc(PE, name)
	if cint(doc.docstatus) == 1:
		return {"ok": 1, "da_lam_roi": 1, "buoc": doc.get("workflow_state") or ""}
	if not la_phieu_chi_app(doc):
		frappe.throw("Phiếu này không thuộc đường duyệt phiếu chi, không xác nhận ở đây được.")

	# Uy nhiem chi dinh ngay tai buoc nay, khong bat ai nho quay lai dinh sau.
	if unc:
		from vagabond import tep_dinh_kem

		da = tep_dinh_kem.doc_ds(doc.get("vgb_chi_unc"))
		them = tep_dinh_kem.gan_vao(PE, doc.name, "vgb_chi_unc", unc)
		doc.vgb_chi_unc = tep_dinh_kem.ghi_ds(da + them)

	so_unc = _so_unc(doc)
	da_chi, ma_gd_ngan_hang = _da_chi_theo_sepay(doc.name)
	ly_do = (ly_do_som or "").strip()
	duoc_bo_qua = 1 if (VAI_BO_QUA_SEPAY & set(frappe.get_roles())) else 0
	kq = soat_ghi_so(
		doc.get("workflow_state"), so_unc, flt(doc.paid_amount), da_chi,
		ly_do, duoc_bo_qua,
	)
	if not kq["ok"]:
		frappe.throw(kq["vi_sao"], title="Chưa ghi sổ phiếu chi được")

	doc.vgb_chi_ma_gd = (ma_giao_dich or ma_gd_ngan_hang or "").strip()
	doc.vgb_chi_boi = frappe.session.user
	if ly_do and not sepay_du(flt(doc.paid_amount), da_chi):
		doc.vgb_chi_ly_do_som = ly_do
	doc.workflow_state = TT_DA_GHI_SO
	# Co rieng cho hang rao biet la duong nay DA SOAT roi, khoi soat hai lan.
	doc.flags.vgb_da_soat_duyet_chi = 1
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	doc.submit()
	frappe.db.commit()
	_ghi_vet(
		doc.name,
		"Xác nhận đã chuyển tiền %s%s%s"
		% (
			_tien(doc.paid_amount),
			(" - giao dịch " + doc.vgb_chi_ma_gd) if doc.vgb_chi_ma_gd else "",
			(" - ghi sổ sớm: " + ly_do) if (ly_do and not sepay_du(flt(doc.paid_amount), da_chi)) else "",
		),
	)
	return {"ok": 1, "buoc": doc.get("workflow_state") or "", "ma_gd": doc.vgb_chi_ma_gd}


def _ghi_vet(name, viec):
	try:
		frappe.get_doc({
			"doctype": "Comment", "comment_type": "Info",
			"reference_doctype": PE, "reference_name": name,
			"content": "%s - %s" % (viec, frappe.session.user),
		}).insert(ignore_permissions=True)
	except Exception:
		pass

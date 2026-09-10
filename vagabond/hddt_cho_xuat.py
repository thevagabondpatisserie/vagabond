"""#266: hoá đơn đã ghi sổ mà lỡ ngày xuất, kéo sang hôm nay để tối nay xuất.

Đêm 09/09/2026 không tờ nào của ngày 09/09 lên được m-invoice: 116 tờ TCV
đã ghi sổ bị từ chối "Mã thuế suất= [8.0]" rồi bị giữ cờ đối chiếu, 59 đơn
Sales bị chặn ngay lúc ghi sổ vì payload thiếu dòng 0 đồng. Cả hai lỗi đã
sửa ở thue_vnd.chuan_tien. Phần này lo phần còn lại: những tờ ĐÃ ghi sổ
mang ngày cũ thì không đổi được ngày sổ nữa, nên phải:

1. Kéo NGÀY LẬP hoá đơn điện tử sang hôm nay (trường vgb_hddt_ngay_xuat),
   sổ vẫn giữ ngày bán. m-invoice đánh số tăng theo ngày lập, tờ mang ngày
   cũ chen vào sau tờ ngày mới là bị từ chối mã 296 (bài học 03/09).
2. Gỡ cờ "cần đối chiếu" CHỈ khi đã hỏi m-invoice theo mã phiếu (keyApi)
   và m-invoice không có tờ nào. Không hỏi được, hay trả lời có dấu vết
   chứng từ, thì giữ cờ. Không lặp lại vụ 13/08 (kéo 135 tờ rồi phải đi
   xoá hoá đơn đúp bên m-invoice).
3. Chuỗi cuối ngày và nhịp bù mỗi giờ phát hành thêm các tờ "chờ xuất cho
   ngày hôm nay", rồi ký chúng, đi cùng kịch bản m-invoice, cùng khoá.
4. Thu ngân và kế toán nhìn thấy chip "Hoá đơn chờ xuất cho ngày ..." trên
   từng tờ, để không nhầm là tờ đã bị bỏ quên hay đã xuất rồi.

Phần thuần ở trên, phần chạm Frappe ở dưới, để kiểm thử không cần site.
"""

import datetime

# ------------------------------------------------------------------ thuần

TRUONG_NGAY_XUAT = "vgb_hddt_ngay_xuat"


def _ngay(v):
	if v is None or v == "":
		return None
	if isinstance(v, datetime.datetime):
		return v.date()
	if isinstance(v, datetime.date):
		return v
	return datetime.date.fromisoformat(str(v)[:10])


def ngay_vn(v):
	d = _ngay(v)
	return d.strftime("%d/%m/%Y") if d else ""


def nhan_chip(ngay_xuat):
	"""Chữ trên chip, MỘT nguồn cho app và nhật ký: "Hoá đơn chờ xuất cho ngày dd/mm/yyyy"."""
	return "Hoá đơn chờ xuất cho ngày " + ngay_vn(ngay_xuat)


def ngay_lap(si, hom_nay=None):
	"""Ngày lập gửi m-invoice: ngày chờ xuất nếu có, không thì ngày sổ.

	Ngày chờ xuất mà nhỏ hơn ngày sổ là dữ liệu hỏng, không gửi.
	"""
	so = _ngay(si.get("posting_date"))
	keo = _ngay(si.get(TRUONG_NGAY_XUAT))
	if keo is None:
		return so
	if so is not None and keo < so:
		raise ValueError("Ngày chờ xuất %s nhỏ hơn ngày sổ %s, kiểm lại phiếu %s." % (ngay_vn(keo), ngay_vn(so), si.get("name")))
	return keo


def da_co_hddt(r):
	return any(str(r.get(o) or "").strip() for o in ("custom_minvoice_id", "custom_hddt_id", "custom_hddt_so"))


def thuoc_diem_dang_xuat(r, ds_nguon, ds_quay):
	"""Cùng bộ lọc với kịch bản phát hành: nguồn đơn nằm trong cài đặt
	m-invoice, và (nếu đã khai) mã quầy nằm trong Vagabond Settings
	vgb_hddt_quay, dấu @ là điểm nhận đơn online (quầy rỗng)."""
	if str(r.get("custom_nguon") or "").strip() not in ds_nguon:
		return False
	if not ds_quay:
		return True
	q = str(r.get("vgb_quay") or "").strip().upper()
	if not q:
		return "@" in ds_quay
	return q in {x.upper() for x in ds_quay if x != "@"}


def loc_to_keo(rows, ngay_cu, hom_nay, ds_nguon, ds_quay):
	"""Tờ đủ điều kiện kéo: đã ghi sổ, có tiền, không huỷ/tạm tính, mang
	ngày sổ ngay_cu (không lớn hơn hôm nay), chưa có hoá đơn điện tử, thuộc
	điểm đang bật xuất. Tờ đang giữ cờ đối chiếu VẪN được liệt kê, kèm dấu
	để bước sau hỏi m-invoice trước khi gỡ.

	ngay_cu bằng hôm nay thì không có gì để kéo ngày, chỉ còn việc gỡ cờ đối
	chiếu (42 tờ TCV ngày 10/09 bị giữ cờ vì cùng lỗi 8.0), nên chỉ liệt kê
	tờ đang giữ cờ."""
	ngay_cu, hom_nay = _ngay(ngay_cu), _ngay(hom_nay)
	if ngay_cu is None or hom_nay is None or ngay_cu > hom_nay:
		raise ValueError("Chỉ kéo tờ của ngày đã qua, hoặc gỡ cờ đối chiếu của hôm nay.")
	ra = []
	for r in rows:
		if ngay_cu == hom_nay and not int(r.get("vgb_hddt_cho_doi_chieu") or 0):
			continue
		if int(r.get("docstatus") or 0) != 1 or float(r.get("grand_total") or 0) <= 0:
			continue
		if int(r.get("vgb_huy") or 0) or int(r.get("vgb_tam_tinh") or 0):
			continue
		if _ngay(r.get("posting_date")) != ngay_cu or da_co_hddt(r):
			continue
		if not thuoc_diem_dang_xuat(r, ds_nguon, ds_quay):
			continue
		ra.append(r)
	return ra


def minvoice_khong_co_to(phan_hoi):
	"""GetInfoInvoice theo keyApi trả về mà KHÔNG mang dấu vết chứng từ nào
	(số, ID, ký hiệu...) ở bất kỳ tầng nào thì mới coi là m-invoice chưa có
	tờ. Lỗi mạng, phản hồi không đọc được, hay có dấu vết đều là "chưa chắc",
	giữ cờ. Dùng chung phép dò dấu vết với phân loại phản hồi Save."""
	from vagabond.minvoice_an_toan import _co_dau_vet
	if not isinstance(phan_hoi, dict):
		return False
	return not _co_dau_vet(phan_hoi)


def gom_ket_qua(ds):
	"""Gộp kết quả từng tờ của phát hành chờ xuất thành dạng gom_lo."""
	ra = {"tim_thay": 0, "tao_ok": 0, "loi": []}
	for r in ds:
		r = r if isinstance(r, dict) else {}
		ra["tim_thay"] += int(r.get("tim_thay") or 0)
		ra["tao_ok"] += int(r.get("tao_ok") or 0)
		ra["loi"] += [str(x) for x in (r.get("loi") or [])]
	return ra


# ------------------------------------------------------------ chạm Frappe

import frappe
from frappe.utils import cint, flt, getdate, nowdate

TRUONG_MOI = {"Sales Invoice": [{
	"fieldname": TRUONG_NGAY_XUAT, "label": "HĐĐT chờ xuất cho ngày",
	"fieldtype": "Date", "read_only": 1, "no_copy": 1,
	"insert_after": "vgb_hddt_cho_doi_chieu",
	"description": "Tờ đã ghi sổ mang ngày cũ, được kéo ngày lập hoá đơn điện tử sang ngày này. Sổ vẫn giữ ngày bán.",
}]}

QUYEN_KEO = {"System Manager", "Accounts Manager", "Accounts User", "Sales Manager"}


def _cai_dat_minvoice():
	stg = frappe.get_doc("MInvoice Phat Hanh Settings")
	ds_nguon = [x.strip() for x in str(stg.get("nguon") or "Pancake").replace("\n", ",").split(",") if x.strip()]
	ds_quay = [x.strip() for x in str(frappe.db.get_single_value("Vagabond Settings", "vgb_hddt_quay") or "").replace("\n", ",").split(",") if x.strip()]
	return stg, ds_nguon, ds_quay


def _dang_nhap_minvoice(stg):
	"""Đăng nhập cổng API m-invoice MỘT lần cho cả lượt. Trả (base, header, lỗi)."""
	base = (stg.get("api2_base") or "").rstrip("/")
	user = stg.get("api2_username") or stg.get("username") or ""
	pwd = stg.get_password("api2_password", raise_exception=False) or stg.get_password("password", raise_exception=False) or ""
	if not (base and user and pwd):
		return None, None, "chưa khai tài khoản cổng API m-invoice"
	import json
	from frappe.integrations.utils import make_post_request
	try:
		z = make_post_request(base + "/api/Account/Login", data=json.dumps({"username": user, "password": pwd, "ma_dvcs": stg.get("ma_dvcs") or "VP"}), headers={"Content-Type": "application/json"})
	except Exception as e:
		return None, None, "không đăng nhập được cổng API m-invoice: " + str(e).replace(pwd, "***")[:150]
	tok = z.get("token") if isinstance(z, dict) else None
	if not tok:
		return None, None, "không đăng nhập được cổng API m-invoice"
	return base, {"Authorization": "Bear " + str(tok), "Content-Type": "application/json"}, ""


def _tra_minvoice(base, hdr, ten_phieu):
	"""Hỏi m-invoice có tờ mang keyApi = mã phiếu không. Trả (chắc chắn không có, câu)."""
	from frappe.integrations.utils import make_get_request
	try:
		r = make_get_request(base + "/api/InvoiceApi78/GetInfoInvoice", headers=hdr, params={"keyApi": ten_phieu})
	except Exception as e:
		return False, "không hỏi được m-invoice: " + str(e)[:150]
	if minvoice_khong_co_to(r):
		return True, "m-invoice trả lời không có tờ nào mang mã phiếu này"
	return False, "m-invoice có dấu vết tờ mang mã phiếu này, kế toán đối chiếu tay"


@frappe.whitelist()
def keo_sang_hom_nay(ngay, chay_thu=1):
	"""Kéo ngày lập HĐĐT của các tờ đã ghi sổ ngày `ngay` sang hôm nay.

	chay_thu=1 chỉ liệt kê. Chạy thật: đặt vgb_hddt_ngay_xuat = hôm nay, ghi
	Comment trên từng tờ; tờ đang giữ cờ đối chiếu thì hỏi m-invoice theo mã
	phiếu, không có tờ mới gỡ cờ, còn lại giữ nguyên và báo về.
	"""
	from vagabond.ban_hang import _kiem_quyen
	_kiem_quyen()
	if not QUYEN_KEO & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý hoặc kế toán mới kéo được ngày xuất hoá đơn điện tử.")
	chay_thu = cint(chay_thu)
	hom_nay = getdate(nowdate())
	try:
		ngay_cu = _ngay(ngay)
		if ngay_cu is None or ngay_cu > hom_nay:
			raise ValueError("Chỉ kéo tờ của ngày đã qua, hoặc gỡ cờ đối chiếu của hôm nay.")
	except ValueError as e:
		frappe.throw(str(e))
	stg, ds_nguon, ds_quay = _cai_dat_minvoice()
	rows = frappe.db.get_all(
		"Sales Invoice",
		filters={"posting_date": ngay_cu, "docstatus": 1},
		fields=["name", "posting_date", "docstatus", "grand_total", "vgb_huy", "vgb_tam_tinh",
			"custom_nguon", "vgb_quay", "custom_minvoice_id", "custom_hddt_id", "custom_hddt_so",
			"vgb_hddt_cho_doi_chieu", TRUONG_NGAY_XUAT, "custom_pancake_display_id"],
		limit_page_length=0,
	)
	try:
		chon = loc_to_keo(rows, ngay_cu, hom_nay, ds_nguon, ds_quay)
	except ValueError as e:
		frappe.throw(str(e))
	kq = {
		"chay_thu": chay_thu, "ngay_cu": str(ngay_cu), "hom_nay": str(hom_nay),
		"chon": len(chon), "tien": sum(flt(r.grand_total) for r in chon),
		"dang_doi_chieu": sum(1 for r in chon if cint(r.vgb_hddt_cho_doi_chieu)),
		"da_keo_truoc": sum(1 for r in chon if _ngay(r.get(TRUONG_NGAY_XUAT)) == hom_nay),
		"keo": 0, "go_co": 0, "giu_co": 0, "loi": [],
		"vi_du": [{"don": r.name, "ma": r.custom_pancake_display_id or r.name, "tien": flt(r.grand_total),
			"doi_chieu": cint(r.vgb_hddt_cho_doi_chieu)} for r in chon[:20]],
	}
	if chay_thu:
		return kq
	nhan = nhan_chip(hom_nay)
	base, hdr, loi_dn = (None, None, "")
	if any(cint(r.vgb_hddt_cho_doi_chieu) for r in chon):
		base, hdr, loi_dn = _dang_nhap_minvoice(stg)
	for r in chon:
		try:
			if cint(r.vgb_hddt_cho_doi_chieu):
				khong_co, cau = _tra_minvoice(base, hdr, r.name) if base else (False, loi_dn)
				if not khong_co:
					kq["giu_co"] += 1
					if len(kq["loi"]) < 50:
						kq["loi"].append("%s: giữ cờ đối chiếu, %s" % (r.custom_pancake_display_id or r.name, cau))
					continue
				frappe.db.set_value("Sales Invoice", r.name, "vgb_hddt_cho_doi_chieu", 0, update_modified=False)
				frappe.get_doc("Sales Invoice", r.name).add_comment("Comment", "Gỡ cờ đối chiếu HĐĐT (#266): " + cau + ".")
				kq["go_co"] += 1
			# Tờ của chính hôm nay không cần kéo ngày: ngày sổ đã là ngày lập.
			if ngay_cu != hom_nay and _ngay(r.get(TRUONG_NGAY_XUAT)) != hom_nay:
				frappe.db.set_value("Sales Invoice", r.name, TRUONG_NGAY_XUAT, hom_nay, update_modified=False)
				frappe.get_doc("Sales Invoice", r.name).add_comment("Comment",
					"%s (kéo từ ngày bán %s, sổ vẫn giữ ngày bán, #266). Người kéo: %s." % (nhan, ngay_vn(ngay_cu), frappe.session.user))
			kq["keo"] += 1
			frappe.db.commit()
		except Exception as e:
			frappe.db.rollback()
			frappe.local.message_log = []
			if len(kq["loi"]) < 50:
				kq["loi"].append("%s: %s" % (r.custom_pancake_display_id or r.name, str(e)[:200]))
	return kq


def ds_cho_xuat(ngay):
	"""Tờ chờ xuất cho ngày `ngay`, chưa có hoá đơn điện tử, không giữ cờ."""
	rows = frappe.db.get_all(
		"Sales Invoice",
		filters={TRUONG_NGAY_XUAT: getdate(ngay), "docstatus": 1, "vgb_huy": 0, "vgb_tam_tinh": 0,
			"grand_total": [">", 0], "vgb_hddt_cho_doi_chieu": ["!=", 1]},
		fields=["name", "custom_minvoice_id", "custom_hddt_id", "custom_hddt_so", "custom_hddt_trang_thai"],
		order_by="name asc", limit_page_length=0,
	)
	return [r for r in rows if not da_co_hddt(r)]


def phat_hanh(ngay, goi_kich_ban):
	"""Phát hành từng tờ chờ xuất cho `ngay` qua kịch bản m-invoice (phieu=...),
	mỗi tờ một lần gọi và tự commit như các lô của chuỗi cuối ngày.
	goi_kich_ban(ten, tham_so) là ban_hang._goi_server_script, truyền vào để
	không import vòng."""
	ds = []
	for r in ds_cho_xuat(ngay):
		try:
			kq = goi_kich_ban("MInvoice - Phat hanh HD Sales (API)",
				{"che_do": "day", "ngay": str(ngay), "so_luong": 0, "phieu": r.name, "khong_commit": 0})
		except Exception:
			frappe.log_error(frappe.get_traceback(), "hddt_cho_xuat: phat hanh %s" % r.name)
			kq = {"tim_thay": 1, "tao_ok": 0, "loi": ["%s: phát hành lỗi, xem Error Log." % r.name]}
		ds.append(kq if isinstance(kq, dict) else {"tim_thay": 1, "tao_ok": 0, "loi": []})
	return gom_ket_qua(ds)


def ky(ngay, goi_kich_ban):
	"""Ký từng tờ chờ xuất cho `ngay` đã lên m-invoice mà còn Chờ ký. Kịch bản
	ký hàng loạt lọc theo ngày SỔ nên không tự thấy các tờ này."""
	rows = frappe.db.get_all(
		"Sales Invoice",
		filters={TRUONG_NGAY_XUAT: getdate(ngay), "docstatus": 1,
			"custom_minvoice_id": ["is", "set"], "custom_hddt_trang_thai": ["in", ["Chờ ký", "Chờ duyệt"]]},
		pluck="name", order_by="name asc", limit_page_length=0,
	)
	ra = {"can_ky": len(rows), "da_ky": 0, "loi": []}
	for ten in rows:
		try:
			kq = goi_kich_ban("MInvoice - Ky hang loat hoa don", {"ngay": str(ngay), "phieu": ten, "so_luong": 0, "lui": 0})
			kq = kq if isinstance(kq, dict) else {}
			ra["da_ky"] += cint(kq.get("da_ky"))
			ra["loi"] += [str(x) for x in (kq.get("loi") or [])]
		except Exception:
			frappe.log_error(frappe.get_traceback(), "hddt_cho_xuat: ky %s" % ten)
			ra["loi"].append("%s: ký lỗi, xem Error Log." % ten)
	return ra

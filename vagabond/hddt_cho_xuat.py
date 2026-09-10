"""#266: hoá đơn đã ghi sổ mà lỡ ngày xuất, kéo sang hôm nay để tối nay xuất.

Đêm 09/09/2026 không tờ nào của ngày 09/09 lên được m-invoice: 116 tờ TCV
đã ghi sổ bị từ chối "Mã thuế suất= [8.0]" rồi bị giữ cờ đối chiếu, 59 đơn
Sales bị chặn ngay lúc ghi sổ vì payload thiếu dòng 0 đồng. Cả hai lỗi đã
sửa ở thue_vnd.chuan_tien. Phần này lo phần còn lại: những tờ ĐÃ ghi sổ
mang ngày cũ thì không đổi được ngày sổ nữa, nên phải:

1. Anh Việt chốt 10/09 19h: XUẤT HOÁ ĐƠN MANG ĐÚNG NGÀY BÁN 09/09 khi cửa
   m-invoice còn mở. Cửa còn mở vì tờ mang số lớn nhất (12943) vẫn đang là
   ngày 08/09. m-invoice đánh số tăng theo ngày lập, nên hễ một tờ mang ngày
   10/09 ra trước là mọi tờ 09/09 bị từ chối mã 296 vĩnh viễn (bài học 03/09,
   45 tờ ngày 01/09 mất cửa). Chỉ khi cửa đã đóng mới kéo ngày lập sang hôm
   nay (trường vgb_hddt_ngay_xuat), sổ vẫn giữ ngày bán.

   Vì cửa đóng bởi chính tờ ngày mới của mình, mọi đường phát hành đều phải
   XUẤT NGÀY CŨ TRƯỚC (xuat_ngay_cu_truoc), không đợi ai bấm nút kịp.
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


# Dấu hiệu phản hồi là LỖI chứ không phải câu trả lời "không có tờ".
DAU_HIEU_LOI = ("error", "exception", "fail", "timeout", "unauthorized", "forbidden",
	"internal", "server", "denied", "expired", "hết hạn", "loi ", "lỗi")
KHOA_PHAN_HOI = {"code", "data", "message", "ok"}

# Mã phiếu bịa ra để đo hình dạng phản hồi "không có tờ" của m-invoice.
KHOA_AM_TINH = "VGB-KHONG-TON-TAI"


def _la_loi_he_thong(phan_hoi):
	"""Mã 3 chữ số bắt đầu 4 hoặc 5, hay message nói lỗi, thì đây là lỗi của
	m-invoice chứ không phải câu trả lời về tờ hoá đơn. Mã 296 (từ chối thật)
	bắt đầu bằng 2 nên không rơi vào đây."""
	ma = str(phan_hoi.get("code") or "").strip()
	if len(ma) == 3 and ma.isdigit() and ma[0] in "45":
		return True
	tin = str(phan_hoi.get("message") or "").lower()
	return any(d in tin for d in DAU_HIEU_LOI)


def _ma_phan_hoi(phan_hoi):
	"""Mã trả về đã chuẩn hoá. None khi phản hồi không mang khoá code."""
	if not isinstance(phan_hoi, dict) or "code" not in phan_hoi:
		return None
	return str(phan_hoi.get("code") or "").strip()


def minvoice_khong_co_to(phan_hoi, chung=None):
	"""m-invoice có CHẮC CHẮN chưa có tờ nào mang mã phiếu này không.

	#266 vòng 2, Codex bắt đúng: bản trước coi MỌI phản hồi dạng dict không
	mang dấu vết là "không có tờ", nên {"code":"500","message":"internal
	error"} cũng gỡ được cờ và tờ đó bị gửi lại, sinh hoá đơn đúp.

	Vòng 3: lọc theo danh sách CẤM (mã 4xx/5xx, chữ "error"...) vẫn sai, vì
	mã lạ như 9999 hay 296 không nằm trong danh sách nào mà vẫn gỡ được cờ.
	Mẫu not-found thật của m-invoice thì chưa ai thấy nên không khai sẵn
	được. Nên lượt chạy tự DỰNG LẤY mẫu đó: hỏi một mã phiếu bịa ra, chắc
	chắn không tồn tại (mẫu âm tính, xem kiem_chung_api). Phản hồi của một
	tờ thật chỉ được coi là "không có tờ" khi nó TRÙNG MÃ với mẫu âm tính
	ấy. Mọi mã khác, kể cả mã chưa từng thấy, đều giữ cờ.

	chung: (kiem_chung_api trả ra) mẫu đối chứng của chính lượt này, gồm cả
	mẫu dương tính (một tờ chắc chắn ĐÃ có hoá đơn phải trả về dấu vết) và
	mẫu âm tính. Không có chung thì không kết luận gì, giữ cờ.
	"""
	from vagabond.minvoice_an_toan import _co_dau_vet
	if not chung:
		return False
	if not isinstance(phan_hoi, dict):
		return False
	if not (set(phan_hoi) & KHOA_PHAN_HOI):
		return False
	if _la_loi_he_thong(phan_hoi):
		return False
	if _ma_phan_hoi(phan_hoi) != chung.get("ma"):
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


def cua_con_mo(ngay, ngay_so_moi_nhat=None):
	"""Ngày này còn phát hành được không.

	m-invoice đánh số tăng theo NGÀY LẬP: tờ mang ngày nhỏ hơn ngày của tờ
	số lớn nhất bị từ chối mã 296 ("date is ... use with other invoice
	before"). Chưa có tờ nào thì mọi ngày đều còn mở.
	"""
	ngay = _ngay(ngay)
	moi = _ngay(ngay_so_moi_nhat)
	if ngay is None:
		return False
	return moi is None or ngay >= moi


def che_do_de_xuat(ngay, hom_nay, ngay_so_moi_nhat=None):
	"""Máy đề xuất cách xử một ngày cũ, người vẫn là người chọn.

	- Cửa còn mở: "giu_ngay", xuất mang đúng ngày bán, sổ và tờ cùng ngày,
	  không phải giải thích với ai vì sao ngày lập khác ngày bán.
	- Cửa đã đóng: "keo", ngày lập là hôm nay, sổ giữ ngày bán.
	"""
	return "giu_ngay" if cua_con_mo(ngay, ngay_so_moi_nhat) else "keo"


def ngay_lap_theo_che_do(che_do, ngay_cu, hom_nay):
	"""Giá trị ghi vào vgb_hddt_ngay_xuat. Cả hai chế độ đều ghi, để chip
	"Hoá đơn chờ xuất cho ngày ..." nói đúng ngày tờ sẽ mang."""
	ngay_cu, hom_nay = _ngay(ngay_cu), _ngay(hom_nay)
	if che_do not in ("giu_ngay", "keo"):
		raise ValueError("Chưa chọn cách xử: giữ đúng ngày bán hay kéo sang hôm nay.")
	return ngay_cu if che_do == "giu_ngay" else hom_nay


def ngay_cu_con_mo(ds_ngay, hom_nay, ngay_so_moi_nhat=None):
	"""Những ngày CŨ đang có tờ chờ xuất mà cửa m-invoice còn mở, cũ trước
	mới sau. Đây là danh sách phải phát hành TRƯỚC tờ của hôm nay."""
	hom_nay = _ngay(hom_nay)
	ra = []
	for d in ds_ngay or []:
		d = _ngay(d)
		if d is None or hom_nay is None or d >= hom_nay:
			continue
		if not cua_con_mo(d, ngay_so_moi_nhat):
			continue
		if d not in ra:
			ra.append(d)
	return sorted(ra)


CHO_SAU_LOI_PHUT = 15


def phai_nhuong_ngay_cu(ngay_lap_to, hom_nay, ds_ngay_cho, ngay_so_moi_nhat=None,
		moc_loi=None, bay_gio=None):
	"""Tờ sắp gửi m-invoice có phải nhường cho ngày cũ đi trước không.

	#266 vòng 2, Codex bắt đúng: hàng rào cũ chỉ nằm ở hai nhịp lịch, trong
	khi chốt đơn tay và chốt cả loạt cũng phát hành ngay sau khi ghi sổ. Nay
	phép này được gọi ở CỬA CHUNG minvoice_an_toan.kiem_goi, nơi cả Python
	lẫn Server Script đều đi qua, nên không còn lối vào nào lách được.

	Trả (phải nhường, danh sách ngày cũ còn mở, lý do).

	Van an toàn: nếu hàng rào vừa thử mà m-invoice không nhận tờ ngày cũ nào
	(moc_loi trong vòng CHO_SAU_LOI_PHUT phút) thì thôi chặn. Không có van
	này thì một ngày cũ hỏng dữ liệu sẽ chặn cả tiệm không xuất được gì.
	"""
	ngay_lap_to, hom_nay = _ngay(ngay_lap_to), _ngay(hom_nay)
	ds = ngay_cu_con_mo(ds_ngay_cho, hom_nay, ngay_so_moi_nhat)
	if not ds:
		return False, [], "không còn ngày cũ nào đang chờ"
	# Chính tờ này là tờ của ngày cũ: nó phải được đi, không thì bế tắc.
	if ngay_lap_to is not None and ngay_lap_to < hom_nay:
		return False, ds, "tờ này mang ngày cũ, được đi trước"
	moc_loi, bay_gio = _gio(moc_loi), _gio(bay_gio)
	if moc_loi is not None and bay_gio is not None:
		if (bay_gio - moc_loi).total_seconds() < CHO_SAU_LOI_PHUT * 60:
			return False, ds, "hàng rào vừa thử không xuất được tờ ngày cũ nào, tạm mở để tiệm chạy tiếp"
	return True, ds, "còn hoá đơn ngày %s chờ xuất" % ", ".join(ngay_vn(d) for d in ds)


def _gio(v):
	if v is None or v == "":
		return None
	if isinstance(v, datetime.datetime):
		return v
	return datetime.datetime.fromisoformat(str(v)[:19])


# ------------------------------------------------------------ chạm Frappe

import frappe
from uuid import uuid4
from frappe.utils import cint, flt, getdate, now_datetime, nowdate

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


def _hoi_minvoice(base, hdr, ten_phieu):
	from frappe.integrations.utils import make_get_request
	return make_get_request(base + "/api/InvoiceApi78/GetInfoInvoice", headers=hdr, params={"keyApi": ten_phieu})


def kiem_chung_api(base, hdr):
	"""Dựng mẫu đối chứng của lượt này. Trả (chung, câu giải thích).

	Hai mẫu, thiếu một là không gỡ cờ tờ nào (#266 vòng 2 và vòng 3):

	- DƯƠNG TÍNH: hỏi một tờ CHẮC CHẮN đã có hoá đơn, phải thấy dấu vết
	  chứng từ. m-invoice sập, trả rỗng hay đổi cách trả lời thì mẫu này
	  không có dấu vết và cả lượt dừng.
	- ÂM TÍNH: hỏi một mã phiếu bịa ra, chắc chắn chưa từng tồn tại. Phản
	  hồi thu được CHÍNH LÀ hình dạng "không có tờ" của m-invoice hôm nay,
	  đo được chứ không phải đoán. Từ đây tờ thật chỉ được gỡ cờ khi trùng
	  mã với mẫu này.

	chung = {"ma": mã của mẫu âm tính, "duong": tên tờ đối chứng dương,
	"khoa_am": mã phiếu bịa ra}. Trả None là không kết luận gì được.
	"""
	from vagabond.minvoice_an_toan import _co_dau_vet
	ten = frappe.db.get_value(
		"Sales Invoice",
		{"docstatus": 1, "custom_hddt_so": ["!=", ""], "custom_minvoice_id": ["!=", ""]},
		"name", order_by="modified desc")
	if not ten:
		return None, "chưa có tờ nào đã xuất để làm mẫu đối chứng dương tính"
	try:
		r = _hoi_minvoice(base, hdr, ten)
	except Exception as e:
		return None, "không hỏi được m-invoice bằng tờ đối chứng %s: %s" % (ten, str(e)[:120])
	if not _co_dau_vet(r):
		return None, ("m-invoice không trả dấu vết cho tờ %s dù tờ này chắc chắn đã có hoá đơn, "
			"nên mọi câu trả lời khác trong lượt này đều không đáng tin" % ten)

	khoa_am = "%s-%s" % (KHOA_AM_TINH, uuid4().hex[:12].upper())
	try:
		am = _hoi_minvoice(base, hdr, khoa_am)
	except Exception as e:
		return None, ("không dựng được mẫu \"không có tờ\": m-invoice báo lỗi khi hỏi mã "
			"không tồn tại %s (%s)" % (khoa_am, str(e)[:120]))
	if _co_dau_vet(am):
		return None, ("m-invoice trả dấu vết chứng từ cho mã %s vốn chưa từng tồn tại, "
			"không tin được câu trả lời nào của lượt này" % khoa_am)
	if not isinstance(am, dict) or not (set(am) & KHOA_PHAN_HOI):
		return None, "mẫu \"không có tờ\" không có hình dạng phản hồi của API: %s" % str(am)[:120]
	if _la_loi_he_thong(am):
		return None, ("m-invoice trả lỗi hệ thống cho mã không tồn tại %s nên không phân biệt "
			"được \"không có tờ\" với \"hỏi không được\": %s" % (khoa_am, str(am)[:120]))
	return ({"ma": _ma_phan_hoi(am), "duong": ten, "khoa_am": khoa_am},
		"đã đối chứng bằng tờ %s và mã không tồn tại %s (mã \"không có tờ\" = %r)" % (
			ten, khoa_am, _ma_phan_hoi(am)))


def _tra_minvoice(base, hdr, ten_phieu, chung=None):
	"""Hỏi m-invoice có tờ mang keyApi = mã phiếu không. Trả (chắc chắn không có, câu)."""
	try:
		r = _hoi_minvoice(base, hdr, ten_phieu)
	except Exception as e:
		return False, "không hỏi được m-invoice: " + str(e)[:150]
	if minvoice_khong_co_to(r, chung):
		return True, "m-invoice trả lời không có tờ nào mang mã phiếu này"
	if not chung:
		return False, "chưa đối chứng được API m-invoice nên không dám kết luận, giữ cờ"
	return False, ("m-invoice không xác nhận là chưa có tờ (mã trả về %r, mã \"không có tờ\" "
		"của lượt này là %r), kế toán đối chiếu tay" % (_ma_phan_hoi(r), chung.get("ma")))


def _dem_theo_ngay(ngay_cu, hom_nay):
	"""(danh sách tờ đủ điều kiện, cài đặt) cho một ngày. Không gọi mạng."""
	stg, ds_nguon, ds_quay = _cai_dat_minvoice()
	rows = frappe.db.get_all(
		"Sales Invoice",
		filters={"posting_date": ngay_cu, "docstatus": 1},
		fields=["name", "posting_date", "docstatus", "grand_total", "vgb_huy", "vgb_tam_tinh",
			"custom_nguon", "vgb_quay", "custom_minvoice_id", "custom_hddt_id", "custom_hddt_so",
			"vgb_hddt_cho_doi_chieu", TRUONG_NGAY_XUAT, "custom_pancake_display_id"],
		limit_page_length=0,
	)
	return loc_to_keo(rows, ngay_cu, hom_nay, ds_nguon, ds_quay), stg


@frappe.whitelist()
def xu_ly_ngay_cu(ngay, chay_thu=1, che_do=""):
	"""Xử tờ đã ghi sổ của một ngày mà chưa có hoá đơn điện tử.

	Hai cách, người chọn, máy đề xuất theo cửa m-invoice còn mở hay không:
	  giu_ngay : xuất mang ĐÚNG ngày bán. Chỉ được khi cửa còn mở, tức ngày
	             đó không nhỏ hơn ngày của tờ mang số lớn nhất.
	  keo      : ngày lập là hôm nay, sổ giữ ngày bán. Dùng khi cửa đã đóng.

	chay_thu=1 chỉ đếm và trả về đề xuất, KHÔNG gọi mạng, không ghi gì.
	Chạy thật đẩy sang hàng đợi dài: 117 tờ vừa hỏi m-invoice vừa phát hành
	thì quá lâu cho một lượt bấm nút (bài học 300 giây ngày 03/09).
	"""
	from vagabond.ban_hang import _kiem_quyen, _ngay_so_hddt_moi_nhat
	_kiem_quyen()
	if not QUYEN_KEO & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý hoặc kế toán mới xử được ngày xuất hoá đơn điện tử.")
	chay_thu = cint(chay_thu)
	hom_nay = getdate(nowdate())
	ngay_cu = _ngay(ngay)
	if ngay_cu is None or ngay_cu > hom_nay:
		frappe.throw("Chỉ xử tờ của ngày đã qua, hoặc của hôm nay.")
	moi_nhat = _ngay_so_hddt_moi_nhat()
	de_xuat = che_do_de_xuat(ngay_cu, hom_nay, moi_nhat)
	if ngay_cu == hom_nay:
		de_xuat = "giu_ngay"
	chon = _dem_theo_ngay(ngay_cu, hom_nay)[0]
	kq = {
		"chay_thu": chay_thu, "ngay_cu": str(ngay_cu), "hom_nay": str(hom_nay),
		"cua_con_mo": 1 if cua_con_mo(ngay_cu, moi_nhat) else 0,
		"ngay_so_moi_nhat": str(moi_nhat) if moi_nhat else "",
		"che_do_de_xuat": de_xuat,
		"chon": len(chon), "tien": sum(flt(r.grand_total) for r in chon),
		"dang_doi_chieu": sum(1 for r in chon if cint(r.vgb_hddt_cho_doi_chieu)),
		"vi_du": [{"don": r.name, "ma": r.custom_pancake_display_id or r.name, "tien": flt(r.grand_total),
			"doi_chieu": cint(r.vgb_hddt_cho_doi_chieu)} for r in chon[:20]],
	}
	if chay_thu:
		return kq
	che_do = str(che_do or "").strip() or de_xuat
	if che_do == "giu_ngay" and not cua_con_mo(ngay_cu, moi_nhat):
		frappe.throw(
			"Cửa m-invoice của ngày %s đã đóng: đã có tờ mang ngày %s, m-invoice không nhận thêm "
			"tờ ngày cũ nữa. Chọn kéo ngày lập sang hôm nay." % (ngay_vn(ngay_cu), ngay_vn(moi_nhat))
		)
	if not chon:
		return dict(kq, keo=0, go_co=0, giu_co=0, loi=[], nhat_ky="Không còn tờ nào để xử.")
	try:
		frappe.enqueue(
			"vagabond.hddt_cho_xuat.chay_nen",
			queue="long", timeout=3600,
			job_id="vgb-xu-ly-ngay-cu-%s" % ngay_cu, deduplicate=True,
			ngay=str(ngay_cu), che_do=che_do, nguoi=frappe.session.user,
		)
		cau = "%s: đang xử %d tờ ngày %s ở lượt chạy nền (%s), mở lại màn này sau vài phút." % (
			hom_nay, len(chon), ngay_vn(ngay_cu),
			"giữ đúng ngày bán" if che_do == "giu_ngay" else "kéo sang hôm nay")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hddt_cho_xuat: khong day duoc sang hang doi")
		return chay_nen(str(ngay_cu), che_do, frappe.session.user)
	frappe.db.set_single_value("Vagabond Settings", "tu_ghi_so_nhat_ky", cau[:500])
	frappe.db.commit()
	return dict(kq, che_do=che_do, tren_hang_doi=1, nhat_ky=cau)


def chay_nen(ngay, che_do, nguoi=""):
	"""Lượt chạy nền: gỡ cờ, đánh dấu ngày lập, phát hành rồi ký.

	Gỡ cờ đối chiếu CHỈ khi m-invoice trả lời không có tờ nào mang mã phiếu
	đó. Không hỏi được thì giữ cờ, thà chậm còn hơn phát hành đúp (13/08).
	"""
	frappe.set_user("Administrator")
	from vagabond.ban_hang import (
		_goi_server_script, _khoa_hddt, _mo_khoa_dong_bo, _cong_tac_minvoice,
		_phat_hanh_theo_lo, _ky_theo_lo,
	)
	hom_nay = getdate(nowdate())
	ngay_cu = _ngay(ngay)
	chon, stg = _dem_theo_ngay(ngay_cu, hom_nay)
	ngay_dat = ngay_lap_theo_che_do(che_do, ngay_cu, hom_nay)
	kq = {"ngay_cu": str(ngay_cu), "che_do": che_do, "chon": len(chon),
		"keo": 0, "go_co": 0, "giu_co": 0, "loi": []}
	nhan = nhan_chip(ngay_dat)
	base, hdr, loi_dn = (None, None, "")
	chung, cau_kc = None, ""
	if any(cint(r.vgb_hddt_cho_doi_chieu) for r in chon):
		base, hdr, loi_dn = _dang_nhap_minvoice(stg)
		if base:
			chung, cau_kc = kiem_chung_api(base, hdr)
			if not chung:
				kq["loi"].append("Không gỡ cờ đối chiếu tờ nào: " + cau_kc)
	for r in chon:
		try:
			if cint(r.vgb_hddt_cho_doi_chieu):
				khong_co, cau = _tra_minvoice(base, hdr, r.name, chung) if base else (False, loi_dn)
				if not khong_co:
					kq["giu_co"] += 1
					if len(kq["loi"]) < 50:
						kq["loi"].append("%s: giữ cờ đối chiếu, %s" % (r.custom_pancake_display_id or r.name, cau))
					continue
				frappe.db.set_value("Sales Invoice", r.name, "vgb_hddt_cho_doi_chieu", 0, update_modified=False)
				frappe.get_doc("Sales Invoice", r.name).add_comment("Comment", "Gỡ cờ đối chiếu HĐĐT (#266): " + cau + ".")
				kq["go_co"] += 1
			if _ngay(r.get(TRUONG_NGAY_XUAT)) != ngay_dat:
				frappe.db.set_value("Sales Invoice", r.name, TRUONG_NGAY_XUAT, ngay_dat, update_modified=False)
				frappe.get_doc("Sales Invoice", r.name).add_comment(
					"Comment", "%s (ngày bán %s, sổ giữ nguyên ngày bán, #266). Người xử: %s." % (
						nhan, ngay_vn(ngay_cu), nguoi or frappe.session.user))
			kq["keo"] += 1
			frappe.db.commit()
		except Exception as e:
			frappe.db.rollback()
			frappe.local.message_log = []
			if len(kq["loi"]) < 50:
				kq["loi"].append("%s: %s" % (r.custom_pancake_display_id or r.name, str(e)[:200]))

	# Giữ ngày thì phát hành NGAY: cửa m-invoice của ngày cũ đóng lại ngay khi
	# tờ đầu tiên của ngày mới ra, mà nhịp xuất rải chạy hai lần mỗi giờ.
	# Kéo sang hôm nay thì để chuỗi cuối ngày lo, đúng lời anh Việt "tối nay".
	if che_do == "giu_ngay" and kq["keo"]:
		# Lượt này có thể là của chính hôm nay (gỡ cờ cho bill quầy). Tờ hôm
		# nay mà ra trước là đóng cửa mọi ngày cũ đang chờ, nên nhường trước.
		bat_ph, bat_ky = _cong_tac_minvoice()
		if ngay_cu >= hom_nay and not xuat_ngay_cu_truoc():
			kq["loi"].append("Còn hoá đơn ngày cũ chờ xuất, chưa phát hành tờ của hôm nay.")
			bat_ph = 0
		if not bat_ph:
			kq["loi"].append("Cấu hình m-invoice đang tắt phát hành, chưa xuất được tờ nào.")
		else:
			khoa = _khoa_hddt(cho=60)
			if khoa is None:
				kq["loi"].append("Lượt phát hành khác đang giữ khoá, nhịp bù mỗi giờ sẽ làm tiếp.")
			else:
				try:
					ph = _phat_hanh_theo_lo(str(ngay_cu))
					kq["phat_hanh"] = "%d/%d tờ" % (ph.get("tao_ok") or 0, ph.get("tim_thay") or 0)
					kq["loi"] += [str(x) for x in (ph.get("loi") or [])][:10]
					if bat_ky:
						k = _ky_theo_lo(str(ngay_cu))
						kq["ky"] = "%d/%d tờ" % (k.get("da_ky") or 0, k.get("can_ky") or 0)
						kq["loi"] += [str(x) for x in (k.get("loi") or [])][:10]
				finally:
					_mo_khoa_dong_bo(khoa)

	cau = "%s lúc %s: ngày %s %s %d tờ%s%s.%s" % (
		nowdate(), now_datetime().strftime("%H:%M"), ngay_vn(ngay_cu),
		"xuất giữ đúng ngày bán" if che_do == "giu_ngay" else "kéo sang ngày " + ngay_vn(ngay_dat),
		kq["keo"],
		(", phát hành " + kq["phat_hanh"]) if kq.get("phat_hanh") else "",
		(", ký " + kq["ky"]) if kq.get("ky") else "",
		(" Còn %d tờ giữ cờ đối chiếu." % kq["giu_co"]) if kq["giu_co"] else "",
	)
	kq["nhat_ky"] = cau
	frappe.db.set_single_value("Vagabond Settings", "tu_ghi_so_nhat_ky", cau[:500])
	frappe.db.commit()
	if kq["loi"]:
		frappe.log_error(title="Vagabond: xử HĐĐT ngày %s" % ngay_cu,
			message=cau + "\n\n" + "\n".join(kq["loi"])[:4000])
	return kq


def ngay_cu_dang_cho():
	"""Các ngày CŨ đang có tờ chờ xuất mang đúng ngày bán của chúng."""
	try:
		r = frappe.db.sql("""select distinct posting_date from `tabSales Invoice`
			where docstatus = 1 and ifnull(vgb_huy, 0) = 0 and ifnull(vgb_tam_tinh, 0) = 0
			  and grand_total > 0 and ifnull(vgb_hddt_cho_doi_chieu, 0) != 1
			  and ifnull(custom_hddt_so, '') = '' and ifnull(custom_minvoice_id, '') = ''
			  and ifnull(custom_hddt_id, '') = ''
			  and {truong} is not null and {truong} = posting_date
			  and posting_date < %(hom_nay)s""".format(truong=TRUONG_NGAY_XUAT),
			{"hom_nay": nowdate()})
		return [x[0] for x in r]
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hddt_cho_xuat: doc ngay cu dang cho")
		return []


KHOA_MOC_LOI = "vgb_hddt_moc_loi_ngay_cu"


def _doc_moc_loi():
	try:
		return frappe.cache().get_value(KHOA_MOC_LOI)
	except Exception:
		return None


def _ghi_moc_loi(co_loi):
	try:
		if co_loi:
			frappe.cache().set_value(KHOA_MOC_LOI, str(now_datetime())[:19], expires_in_sec=3600)
		else:
			frappe.cache().delete_value(KHOA_MOC_LOI)
	except Exception:
		pass


def xuat_ngay_cu_truoc():
	"""HÀNG RÀO THỨ TỰ. Trả True khi đường đã thông cho tờ của HÔM NAY.

	m-invoice đánh số theo ngày lập, nên tờ đầu tiên của hôm nay đóng sập cửa
	của mọi ngày cũ. Đêm 09/09 đã mất cả ngày vì không lớp nào giữ thứ tự này.

	#266 vòng 2, Codex bắt đúng hai chỗ: hàng rào cũ trả về im lặng khi không
	lấy được khoá, và nơi gọi cứ thế đi tiếp. Nay:
	  - không lấy được khoá là CÒN NỢ ngày cũ, trả False (fail closed);
	  - chạy xong mà m-invoice không nhận tờ nào thì ghi mốc lỗi, van an toàn
	    trong phai_nhuong_ngay_cu sẽ mở sau CHO_SAU_LOI_PHUT phút.
	Không có ngày cũ nào đang chờ thì trả True ngay, không tốn gì.
	"""
	try:
		ds = ngay_cu_dang_cho()
		if not ds:
			return True
		from vagabond.ban_hang import (
			_ngay_so_hddt_moi_nhat, _khoa_hddt, _mo_khoa_dong_bo, _cong_tac_minvoice,
			_phat_hanh_theo_lo, _ky_theo_lo,
		)
		bat_ph, bat_ky = _cong_tac_minvoice()
		if not bat_ph:
			# Không phát hành được gì thì tờ hôm nay cũng không ra, cửa ngày
			# cũ không bị đóng. Cho đi tiếp.
			return True
		ngay = ngay_cu_con_mo(ds, getdate(nowdate()), _ngay_so_hddt_moi_nhat())
		if not ngay:
			return True
		khoa = _khoa_hddt(cho=30)
		if khoa is None:
			# Lượt khác đang xuất ngày cũ. Chưa xong thì chưa được đụng tờ
			# hôm nay: đây chính là ca đồng thời Codex chỉ ra.
			return False
		con_no = False
		try:
			for d in ngay:
				ph = _phat_hanh_theo_lo(str(d))
				ky_kq = _ky_theo_lo(str(d)) if bat_ky else {"can_ky": 0, "da_ky": 0, "loi": []}
				if cint(ph.get("tim_thay")) and not cint(ph.get("tao_ok")):
					con_no = True
				frappe.log_error(
					title="Vagabond: xuất ngày cũ trước %s" % d,
					message="Phát hành %d/%d tờ. Ký %d/%d tờ.\n%s" % (
						cint(ph.get("tao_ok")), cint(ph.get("tim_thay")),
						cint(ky_kq.get("da_ky")), cint(ky_kq.get("can_ky")),
						"\n".join(str(x) for x in ((ph.get("loi") or []) + (ky_kq.get("loi") or [])))[:3000]),
				)
		finally:
			_mo_khoa_dong_bo(khoa)
		_ghi_moc_loi(con_no)
		# Còn tờ nào chưa ra thì vẫn là còn nợ; đọc lại cho chắc chứ không
		# tin con số vừa gộp.
		return not ngay_cu_con_mo(ngay_cu_dang_cho(), getdate(nowdate()), _ngay_so_hddt_moi_nhat())
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hddt_cho_xuat: xuat ngay cu truoc")
		# Hỏng giữa chừng thì coi như còn nợ, không cho tờ hôm nay đi.
		return False


def chan_neu_con_ngay_cu(si):
	"""CỬA CHUNG: gọi từ minvoice_an_toan.kiem_goi, ngay trước khi dựng payload.

	Mọi đường phát hành (chuỗi cuối ngày, xuất rải, chốt đơn tay, chốt cả
	loạt, nhịp bù, Server Script After Submit) đều đi qua kiem_goi, nên đặt
	ở đây là gom về một nguồn thay vì thêm chỗ nhớ gọi (điều 18).
	"""
	try:
		ds = ngay_cu_dang_cho()
		if not ds:
			return
		from vagabond.ban_hang import _ngay_so_hddt_moi_nhat
		phai, ngay, ly_do = phai_nhuong_ngay_cu(
			ngay_lap(si), getdate(nowdate()), ds, _ngay_so_hddt_moi_nhat(),
			_doc_moc_loi(), now_datetime())
	except ValueError:
		raise
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hddt_cho_xuat: chan neu con ngay cu")
		return
	if not phai:
		return
	try:
		frappe.enqueue(
			"vagabond.hddt_cho_xuat.xuat_ngay_cu_truoc",
			queue="long", timeout=3600,
			job_id="vgb-xuat-ngay-cu-truoc", deduplicate=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hddt_cho_xuat: khong day duoc hang rao sang hang doi")
	raise ValueError(
		"Chưa xuất tờ này được: %s. m-invoice đánh số theo ngày lập nên một tờ hôm nay ra trước "
		"là đóng cửa của ngày cũ vĩnh viễn. Máy đang xuất bù ngày cũ ở lượt chạy nền, "
		"vài phút nữa tờ này tự đi tiếp." % ly_do)



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

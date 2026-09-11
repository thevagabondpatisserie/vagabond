"""#266: hoá đơn đã ghi sổ mà lỡ ngày xuất, kéo sang hôm nay để tối nay xuất.

Đêm 09/09/2026 không tờ nào của ngày 09/09 lên được m-invoice: 116 tờ TCV
đã ghi sổ bị từ chối "Mã thuế suất= [8.0]" rồi bị giữ cờ đối chiếu, 59 đơn
Sales bị chặn ngay lúc ghi sổ vì payload thiếu dòng 0 đồng. Cả hai lỗi đã
sửa ở thue_vnd.chuan_tien. Phần này lo phần còn lại: những tờ ĐÃ ghi sổ
mang ngày cũ thì không đổi được ngày sổ nữa, nên phải:

1. Điểm c khoản 7 Điều 1 Nghị định 70/2025/NĐ-CP sửa khoản 9 Điều 10 Nghị
   định 123/2020/NĐ-CP: nếu thời điểm ký số khác thời điểm lập thì ký số và
   gửi cơ quan thuế cấp mã chậm nhất là ngày làm việc tiếp theo kể từ lúc
   lập. Nguồn đối chiếu: https://vbpl.vn/TW/Pages/vbpq-thuoctinh.aspx?ItemID=177581

   Backend nhắc hạn bảo thủ là ngày kế tiếp theo lịch khi chưa khai lịch
   nghỉ. Quá hạn mặc định dừng; quản lý có thể xác nhận riêng một ngày lập,
   hiệu lực đến cuối ngày thực hiện, có người và lý do trong lịch sử.
   Xác nhận không biến hóa đơn quá hạn thành đúng hạn, không giả ngày ký.
   Anh Việt chốt 11/09: giữ ngày lập 09/09, ký ngày thực tế.

   Cửa kỹ thuật của m-invoice vẫn phải xét thêm: m-invoice đánh số tăng theo
   ngày lập, nên hễ một tờ ngày mới ra trước thì tờ ngày cũ bị từ chối mã
   296. Chỉ gửi khi cửa kỹ thuật còn mở và còn hạn hoặc có xác nhận quá hạn.

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
import json

# ------------------------------------------------------------------ thuần

TRUONG_NGAY_XUAT = "vgb_hddt_ngay_xuat"
SO_NGAY_KY_GUI_TOI_DA = 1
TRUONG_XAC_NHAN = "vgb_hddt_xac_nhan_qua_han"


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


def loc_to_keo(rows, ngay_cu, hom_nay, ds_nguon, ds_quay, gom_nhap=False):
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
		if int(r.get("docstatus") or 0) not in ((0, 1) if gom_nhap else (1,)) or float(r.get("grand_total") or 0) <= 0:
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


# MẪU PHẢN HỒI "KHÔNG CÓ TỜ" ĐÃ XÁC MINH CỦA GetInfoInvoice.
#
# Để RỖNG là cố ý. Chưa ai bắt được phản hồi thật của m-invoice khi hỏi một
# mã phiếu không tồn tại, nên chưa có căn cứ nào để nói phản hồi X nghĩa là
# "chưa có hoá đơn". Chừng nào còn rỗng thì máy KHÔNG tự gỡ cờ đối chiếu của
# bất kỳ tờ nào, chỉ liệt kê ra cho kế toán đối chiếu tay.
#
# Khi nào bắt được mẫu thật thì khai vào đây, mỗi phần tử là một dict các
# khoá BẮT BUỘC phải khớp đúng, kèm ghi chú ai xác minh và ngày nào. Đừng
# khai theo suy đoán: gỡ cờ sai là gửi hoá đơn đúp lên cơ quan thuế.
MAU_KHONG_CO_TO = ()


def khop_mau_khong_co_to(phan_hoi, mau=None):
	"""Phản hồi có khớp ĐÚNG một mẫu not-found đã xác minh không."""
	mau = MAU_KHONG_CO_TO if mau is None else mau
	if not mau or not isinstance(phan_hoi, dict):
		return False
	for m in mau:
		if not isinstance(m, dict) or not m:
			continue
		if all(k in phan_hoi and phan_hoi.get(k) == v for k, v in m.items()):
			return True
	return False


def minvoice_khong_co_to(phan_hoi, chung=None, mau=None):
	"""m-invoice có CHẮC CHẮN chưa có tờ nào mang mã phiếu này không.

	#266 vòng 5, Codex bắt đúng và tái hiện được: cách suy mẫu not-found bằng
	cách hỏi một mã bịa ra là SAI VỀ LOGIC. Hỏi một mã không tồn tại rồi lấy
	mã trả về làm chuẩn chỉ chứng minh "cổng trả mã ấy cho mã đó", chứ không
	chứng minh mọi phản hồi mang mã ấy đều có nghĩa là không có tờ. Đo được
	ba phản ví dụ, cả ba đều cho gỡ cờ nhầm:
	  A. mẫu âm {"message":"not found"} (không có khoá code) và tờ thật trả
	     {"message":"Không đủ quyền"}: cùng mã None nên khớp.
	  B. mẫu âm {"code":"9999"} và tờ thật cũng 9999: khớp, dù 9999 chính là
	     mã m-invoice đã TỪ CHỐI 116 tờ TCV đêm 09/09.
	  C. mẫu âm {"code":"01"} và tờ thật {"code":"01","data":{"reason":
	     "Không đủ quyền"}}: khớp mã, tuy nội dung là từ chối quyền.

	Nay đòi mẫu not-found ĐÃ XÁC MINH (MAU_KHONG_CO_TO). Chưa khai mẫu thì
	không tờ nào được gỡ cờ, và lý do được nói thẳng ra cho kế toán. Thiếu
	mã, mã rỗng, schema lạ, phản hồi không rõ: giữ cờ.
	"""
	from vagabond.minvoice_an_toan import _co_dau_vet
	mau = MAU_KHONG_CO_TO if mau is None else mau
	if not mau:
		# Chưa có căn cứ. Không đoán.
		return False
	if not chung:
		return False
	if not isinstance(phan_hoi, dict):
		return False
	if not khop_mau_khong_co_to(phan_hoi, mau):
		return False
	# Khớp mẫu rồi vẫn phải sạch dấu vết chứng từ mới nhận.
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


def han_ky_gui(ngay_lap):
	"""Hạn bảo thủ để ký số và gửi cấp mã.

	Nghị định 70/2025/NĐ-CP dùng "ngày làm việc tiếp theo". Tiệm hoạt động
	cả cuối tuần và repo chưa có lịch nghỉ pháp lý riêng, nên chốt hệ thống
	là ngày kế tiếp theo lịch. Cách này có thể chặt hơn lịch nghỉ, không bao
	giờ nới rộng thời hạn bằng suy đoán.
	"""
	d = _ngay(ngay_lap)
	return d + datetime.timedelta(days=SO_NGAY_KY_GUI_TOI_DA) if d else None


def con_trong_han_ky_gui(ngay_lap, hom_nay):
	ngay_lap, hom_nay = _ngay(ngay_lap), _ngay(hom_nay)
	return bool(ngay_lap and hom_nay and hom_nay <= han_ky_gui(ngay_lap))


def cua_minvoice_con_mo(ngay, ngay_so_moi_nhat=None):
	"""Cửa kỹ thuật của m-invoice còn mở khi chưa có số mang ngày mới hơn."""
	ngay = _ngay(ngay)
	moi = _ngay(ngay_so_moi_nhat)
	if ngay is None:
		return False
	return moi is None or ngay >= moi


def ngay_hddt_moi_nhat(*cac_ngay):
	"""Mốc bảo thủ từ tờ có số và tờ đã tạo thành công nhưng chưa lấy số."""
	ds = []
	for x in cac_ngay:
		d = _ngay(x)
		if d is not None:
			ds.append(d)
	return max(ds) if ds else None


def cua_con_mo(ngay, hom_nay, ngay_so_moi_nhat=None, ngay_xac_nhan=()):
	"""Ngày này còn được giữ làm ngày lập HĐĐT khi cả hai cửa còn mở.

	m-invoice đánh số tăng theo NGÀY LẬP: tờ mang ngày nhỏ hơn ngày của tờ
	số lớn nhất bị từ chối mã 296 ("date is ... use with other invoice
	before"). Cửa kỹ thuật còn mở không được dùng để nới quá hạn ký/gửi của
	Nghị định 70/2025/NĐ-CP.
	"""
	return ((con_trong_han_ky_gui(ngay, hom_nay) or _ngay(ngay) in ngay_xac_nhan)
		and cua_minvoice_con_mo(ngay, ngay_so_moi_nhat))


def che_do_de_xuat(ngay, hom_nay, ngay_so_moi_nhat=None):
	"""Máy đề xuất cách xử một ngày cũ, người vẫn là người chọn.

	- Cửa còn mở: "giu_ngay", xuất mang đúng ngày bán, sổ và tờ cùng ngày,
	  không phải giải thích với ai vì sao ngày lập khác ngày bán.
	- Cửa đã đóng: "keo", ngày lập là hôm nay, sổ giữ ngày bán.
	"""
	return "giu_ngay" if cua_con_mo(ngay, hom_nay, ngay_so_moi_nhat) else "keo"


def ngay_lap_theo_che_do(che_do, ngay_cu, hom_nay):
	"""Giá trị ghi vào vgb_hddt_ngay_xuat. Cả hai chế độ đều ghi, để chip
	"Hoá đơn chờ xuất cho ngày ..." nói đúng ngày tờ sẽ mang."""
	ngay_cu, hom_nay = _ngay(ngay_cu), _ngay(hom_nay)
	if che_do not in ("giu_ngay", "keo"):
		raise ValueError("Chưa chọn cách xử: giữ đúng ngày bán hay kéo sang hôm nay.")
	return ngay_cu if che_do == "giu_ngay" else hom_nay


def ngay_cu_con_mo(ds_ngay, hom_nay, ngay_so_moi_nhat=None, ngay_xac_nhan=()):
	"""Những ngày CŨ đang có tờ chờ xuất mà cửa m-invoice còn mở, cũ trước
	mới sau. Đây là danh sách phải phát hành TRƯỚC tờ của hôm nay."""
	hom_nay = _ngay(hom_nay)
	ra = []
	for d in ds_ngay or []:
		d = _ngay(d)
		if d is None or hom_nay is None or d >= hom_nay:
			continue
		if not cua_con_mo(d, hom_nay, ngay_so_moi_nhat, ngay_xac_nhan):
			continue
		if d not in ra:
			ra.append(d)
	return sorted(ra)


# #266 vòng 5: van thời gian đã bị gỡ hẳn khỏi phai_nhuong_ngay_cu. Mốc lỗi
# chỉ còn để người trực đọc, KHÔNG được dùng lại để mở đường cho tờ ngày mới.


def phai_nhuong_ngay_cu(ngay_lap_to, hom_nay, ds_ngay_cho, ngay_so_moi_nhat=None, ngay_xac_nhan=()):
	"""Tờ sắp gửi m-invoice có phải nhường cho ngày cũ đi trước không.

	Trả (phải nhường, danh sách ngày cũ còn mở, lý do).

	#266 vòng 5, Codex bắt hai chỗ, cả hai đều tái hiện được:

	F2. VAN 15 PHÚT ĐÃ BỊ GỠ HẲN. Bản trước: nếu hàng rào vừa thử mà không
	xuất được tờ ngày cũ nào thì tạm mở cho tờ ngày mới đi. Đo lại thì dấu so
	sánh còn ngược: mốc lỗi 0 giây, 60 giây, 899 giây đều CHO ĐI, chỉ từ 900
	giây mới chặn, tức là van mở NGAY sau lỗi chứ không phải sau 15 phút. Mà
	sửa dấu cũng không đủ: một tờ ngày mới đi lọt là đóng cửa ngày cũ VĨNH
	VIỄN, không có khoảng thời gian nào đáng đánh đổi việc đó. Nay không còn
	van nào: còn nợ ngày cũ mà cửa còn mở thì chặn, hết. Lối thoát là người
	xử nốt ngày cũ, không phải đồng hồ.

	F3. CHỈ NGÀY NỢ SỚM NHẤT ĐƯỢC ĐI. Bản trước miễn cho MỌI tờ mang ngày
	trước hôm nay, nên sang 11/09 thì tờ 10/09 vượt được nợ 09/09 và đóng cửa
	09/09. Nay so với ngày nợ SỚM NHẤT: tờ nào mang ngày nhỏ hơn hoặc bằng
	ngày đó thì được đi (nếu chặn cả nó thì tự khoá chính mình), còn lại chặn.
	"""
	ngay_lap_to, hom_nay = _ngay(ngay_lap_to), _ngay(hom_nay)
	ds = ngay_cu_con_mo(ds_ngay_cho, hom_nay, ngay_so_moi_nhat, ngay_xac_nhan)
	if not ds:
		return False, [], "không còn ngày cũ nào đang chờ"
	som_nhat = min(ds)
	# Chính ngày nợ sớm nhất phải được đi, không thì bế tắc: không tờ nào ra
	# được thì nợ không bao giờ vơi.
	if ngay_lap_to is not None and ngay_lap_to <= som_nhat:
		return False, ds, "tờ này mang ngày %s, là ngày nợ sớm nhất, được đi trước" % ngay_vn(som_nhat)
	return True, ds, "còn hoá đơn ngày %s chờ xuất, phải xuất xong ngày %s trước" % (
		", ".join(ngay_vn(d) for d in ds), ngay_vn(som_nhat))


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



def _ngay_xac_nhan_qua_han(hom_nay=None, phieu=None):
	"""Đọc mới mỗi lần; lỗi DB/JSON phải dừng, không coi như hết nợ ngày cũ.

	Xác nhận chỉ cho đúng ngày lập, hết hiệu lực cuối ngày thực hiện.
	Không thay đổi hạn pháp lý, ngày ký hoặc bỏ kiểm trùng của m-invoice.
	"""
	hom_nay = _ngay(hom_nay or nowdate())
	rows = frappe.db.sql("select value from `tabSingles` where doctype=%s and field=%s",
		("Vagabond Settings", TRUONG_XAC_NHAN))
	if not rows or not rows[0][0]:
		return ()
	x = json.loads(rows[0][0])
	if not isinstance(x, dict):
		raise ValueError("Dữ liệu xác nhận HĐĐT quá hạn không hợp lệ")
	if _ngay(x.get("ngay_thuc_hien")) != hom_nay:
		return ()
	if not x.get("nguoi") or not str(x.get("ly_do") or "").strip():
		raise ValueError("Xác nhận HĐĐT quá hạn thiếu người hoặc lý do")
	if not isinstance(x.get("phieu"), list) or not x["phieu"]:
		raise ValueError("Xác nhận HĐĐT quá hạn thiếu danh sách chứng từ")
	if phieu is not None and phieu not in x["phieu"]:
		return ()
	d = _ngay(x.get("ngay_lap"))
	return (d,) if d and d <= hom_nay else ()


def _ghi_xac_nhan_qua_han(ngay_lap, hom_nay, ly_do, phieu=()):
	if "System Manager" not in frappe.get_roles():
		frappe.throw("Chỉ quản lý hệ thống được xác nhận xử lý hóa đơn đã quá hạn.")
	ly_do = str(ly_do or "").strip()
	if len(ly_do) < 10:
		frappe.throw("Ghi rõ quyết định giữ ngày lập và ký ngày thực tế (ít nhất 10 ký tự).")
	if not phieu:
		frappe.throw("Không có chứng từ nào trong phạm vi xác nhận.")
	from vagabond.ban_hang import _khoa_hddt, _mo_khoa_dong_bo
	khoa = _khoa_hddt(cho=5)
	if khoa is None:
		frappe.throw("Đang xử một lô hóa đơn khác. Chờ lô đó xong rồi xác nhận lại.")
	try:
		cu = _ngay_xac_nhan_qua_han(hom_nay)
		if cu and _ngay(ngay_lap) not in cu:
			frappe.throw("Đang có xác nhận cho ngày %s. Xử xong ngày đó trước, không ghi đè xác nhận đang hiệu lực." % ngay_vn(cu[0]))
		x = dict(ngay_lap=str(ngay_lap), ngay_thuc_hien=str(hom_nay), phieu=sorted(set(phieu)),
			nguoi=frappe.session.user, luc=str(now_datetime()), ly_do=ly_do[:1000])
		frappe.get_doc("Vagabond Settings").add_comment("Comment",
			"Xác nhận xử lý HĐĐT quá hạn: " + json.dumps(x, ensure_ascii=False))
		frappe.db.set_single_value("Vagabond Settings", TRUONG_XAC_NHAN,
			json.dumps(x, ensure_ascii=False))
		# Công bố xác nhận trước khi nhả khóa; worker đọc được đúng tập đã lưu.
		frappe.db.commit()
	finally:
		_mo_khoa_dong_bo(khoa)


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
	"""Kiểm cổng m-invoice có đáng tin trong lượt này không. Trả (chung, câu).

	#266 vòng 5: mẫu âm tính KHÔNG còn được dùng để suy ra hình dạng
	"không có tờ" nữa (xem minvoice_khong_co_to). Ở đây nó chỉ còn là một
	phép thử độ tin cậy: hỏi một mã bịa ra mà cổng lại trả về dấu vết chứng
	từ thì cổng đang nhận vơ, cả lượt không tin được.

	Hai phép, thiếu một là không gỡ cờ tờ nào:
	- DƯƠNG TÍNH: hỏi một tờ chắc chắn đã có hoá đơn, và dấu vết trả về phải
	  đúng của TỜ ĐÓ (số hoá đơn khớp), không phải dấu vết của tờ bất kỳ.
	- ÂM TÍNH: hỏi một mã phiếu bịa ra, phải KHÔNG có dấu vết chứng từ.
	"""
	from vagabond.minvoice_an_toan import _co_dau_vet
	ten, so_hd = None, None
	r_ten = frappe.db.get_value(
		"Sales Invoice",
		{"docstatus": 1, "custom_hddt_so": ["!=", ""], "custom_minvoice_id": ["!=", ""]},
		["name", "custom_hddt_so"], order_by="modified desc", as_dict=True)
	if r_ten:
		ten, so_hd = r_ten.get("name"), str(r_ten.get("custom_hddt_so") or "").strip()
	if not ten:
		return None, "chưa có tờ nào đã xuất để làm mẫu đối chứng dương tính"
	try:
		r = _hoi_minvoice(base, hdr, ten)
	except Exception as e:
		return None, "không hỏi được m-invoice bằng tờ đối chứng %s: %s" % (ten, str(e)[:120])
	if not _co_dau_vet(r):
		return None, ("m-invoice không trả dấu vết cho tờ %s dù tờ này chắc chắn đã có hoá đơn, "
			"nên mọi câu trả lời khác trong lượt này đều không đáng tin" % ten)
	# Dấu vết phải LÀ CỦA TỜ ĐÓ. Trả dấu vết của tờ khác nghĩa là cổng đang
	# tra nhầm, còn nguy hơn là không trả gì.
	if so_hd and so_hd not in json.dumps(r, ensure_ascii=False, default=str):
		return None, ("m-invoice trả dấu vết không mang số hoá đơn %s của tờ đối chứng %s, "
			"cổng đang tra nhầm tờ" % (so_hd, ten))

	khoa_am = "%s-%s" % (KHOA_AM_TINH, uuid4().hex[:12].upper())
	try:
		am = _hoi_minvoice(base, hdr, khoa_am)
	except Exception as e:
		return None, ("không thử được mã không tồn tại %s (%s)" % (khoa_am, str(e)[:120]))
	if _co_dau_vet(am):
		return None, ("m-invoice trả dấu vết chứng từ cho mã %s vốn chưa từng tồn tại, "
			"cổng đang nhận vơ, không tin được lượt này" % khoa_am)
	return ({"duong": ten, "so_hd": so_hd, "khoa_am": khoa_am},
		"đã đối chứng bằng tờ %s (số %s) và mã không tồn tại %s" % (ten, so_hd, khoa_am))


def _tra_minvoice(base, hdr, ten_phieu, chung=None):
	"""Hỏi m-invoice có tờ mang keyApi = mã phiếu không. Trả (chắc chắn không có, câu)."""
	if not MAU_KHONG_CO_TO:
		return False, ("chưa khai mẫu phản hồi \"không có tờ\" đã xác minh của GetInfoInvoice "
			"nên máy không dám kết luận, giữ cờ để kế toán đối chiếu tay")
	try:
		r = _hoi_minvoice(base, hdr, ten_phieu)
	except Exception as e:
		return False, "không hỏi được m-invoice: " + str(e)[:150]
	if minvoice_khong_co_to(r, chung):
		return True, "m-invoice trả đúng mẫu đã xác minh là không có tờ nào mang mã phiếu này"
	if not chung:
		return False, "chưa đối chứng được API m-invoice nên không dám kết luận, giữ cờ"
	return False, ("m-invoice không trả đúng mẫu \"không có tờ\" đã xác minh (mã trả về %r), "
		"kế toán đối chiếu tay" % (_ma_phan_hoi(r),))


def _dem_theo_ngay(ngay_cu, hom_nay, gom_nhap=False):
	"""(danh sách tờ đủ điều kiện, cài đặt) cho một ngày. Không gọi mạng."""
	stg, ds_nguon, ds_quay = _cai_dat_minvoice()
	rows = frappe.db.get_all(
		"Sales Invoice",
		filters={"posting_date": ngay_cu, "docstatus": ["in", [0, 1]] if gom_nhap else 1},
		fields=["name", "posting_date", "docstatus", "grand_total", "vgb_huy", "vgb_tam_tinh",
			"custom_nguon", "vgb_quay", "custom_minvoice_id", "custom_hddt_id", "custom_hddt_so",
			"vgb_hddt_cho_doi_chieu", TRUONG_NGAY_XUAT, "custom_pancake_display_id"],
		limit_page_length=0,
	)
	return loc_to_keo(rows, ngay_cu, hom_nay, ds_nguon, ds_quay, gom_nhap), stg


@frappe.whitelist()
def xu_ly_ngay_cu(ngay, chay_thu=1, che_do="", xac_nhan_qua_han=0, ly_do="", pham_vi=None):
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
	cua_phap_ly = con_trong_han_ky_gui(ngay_cu, hom_nay)
	cua_ky_thuat = cua_minvoice_con_mo(ngay_cu, moi_nhat)
	xac_nhan = _ngay_xac_nhan_qua_han(hom_nay)
	if ngay_cu in xac_nhan and cua_ky_thuat:
		de_xuat = "giu_ngay"
	chon = _dem_theo_ngay(ngay_cu, hom_nay)[0]
	pham_vi_hien_tai = _dem_theo_ngay(ngay_cu, hom_nay, gom_nhap=True)[0]
	kq = {
		"chay_thu": chay_thu, "ngay_cu": str(ngay_cu), "hom_nay": str(hom_nay),
		"pham_vi": [r.name for r in pham_vi_hien_tai],
		"so_nhap": sum(1 for r in pham_vi_hien_tai if cint(r.docstatus) == 0),
		"cua_con_mo": 1 if cua_con_mo(ngay_cu, hom_nay, moi_nhat, xac_nhan) else 0,
		"da_xac_nhan_qua_han": int(ngay_cu in xac_nhan),
		"duoc_xac_nhan_qua_han": int("System Manager" in frappe.get_roles()),
		"cua_phap_ly_con_mo": 1 if cua_phap_ly else 0,
		"cua_minvoice_con_mo": 1 if cua_ky_thuat else 0,
		"han_ky_gui": str(han_ky_gui(ngay_cu)),
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
	if che_do not in ("giu_ngay", "keo"):
		frappe.throw("Chế độ xử lý hóa đơn không hợp lệ.")
	if che_do == "giu_ngay" and not cua_phap_ly and cua_ky_thuat and cint(xac_nhan_qua_han):
		pham_vi = json.loads(pham_vi) if isinstance(pham_vi, str) else pham_vi
		if not isinstance(pham_vi, list) or not pham_vi or set(pham_vi) != set(kq["pham_vi"]):
			frappe.throw("Phạm vi chứng từ đã thay đổi hoặc chưa được xem trước. Mở lại màn hình để xác nhận đúng danh sách.")
		_ghi_xac_nhan_qua_han(ngay_cu, hom_nay, ly_do, pham_vi)
		xac_nhan = (ngay_cu,)
	if che_do == "giu_ngay" and not cua_con_mo(ngay_cu, hom_nay, moi_nhat, xac_nhan):
		if not cua_phap_ly:
			frappe.throw(
				"Cửa pháp lý để giữ ngày %s đã đóng. Theo Nghị định 70/2025/NĐ-CP, ký số và gửi "
				"cấp mã chậm nhất ngày làm việc tiếp theo; hệ thống đang dùng hạn bảo thủ %s. "
				"Cần quản lý xác nhận riêng nếu giữ ngày lập cũ; không tự đổi sang %s." % (
					ngay_vn(ngay_cu), ngay_vn(han_ky_gui(ngay_cu)), ngay_vn(hom_nay))
			)
		frappe.throw(
			"Cửa m-invoice của ngày %s đã đóng: đã có tờ mang ngày %s, m-invoice không nhận thêm "
			"tờ ngày cũ nữa. Chọn kéo ngày lập sang hôm nay." % (ngay_vn(ngay_cu), ngay_vn(moi_nhat))
		)
	if not chon:
		return dict(kq, keo=0, go_co=0, giu_co=0, loi=[], nhat_ky=("Đã xác nhận phạm vi gồm %d đơn nháp; cần ghi sổ các đơn này rồi phát hành." % kq["so_nhap"] if kq["so_nhap"] else "Không còn tờ nào để xử."))
	# Đóng băng ngày người dùng vừa xem và xác nhận. Worker qua nửa đêm dùng
	# đúng phạm vi/ngày này hoặc từ chối nếu đã quá hạn, không tự đổi ngầm.
	ngay_dat = ngay_lap_theo_che_do(che_do, ngay_cu, hom_nay)
	# Commit TRƯỚC khi enqueue: lỗi Redis vẫn nằm trong try và có fallback.
	frappe.db.commit()
	try:
		frappe.enqueue(
			"vagabond.hddt_cho_xuat.chay_nen",
			queue="long", timeout=3600,
			job_id="vgb-xu-ly-ngay-cu-%s" % ngay_cu, deduplicate=True,
			ngay=str(ngay_cu), che_do=che_do, nguoi=frappe.session.user,
			ngay_tham_chieu=str(hom_nay), ngay_dich=str(ngay_dat),
		)
		cau = "%s: đang xử %d tờ ngày %s ở lượt chạy nền (%s), mở lại màn này sau vài phút." % (
			hom_nay, len(chon), ngay_vn(ngay_cu),
			"giữ đúng ngày bán" if che_do == "giu_ngay" else "kéo sang hôm nay")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hddt_cho_xuat: khong day duoc sang hang doi")
		return chay_nen(str(ngay_cu), che_do, frappe.session.user,
			str(hom_nay), str(ngay_dat))
	frappe.db.set_single_value("Vagabond Settings", "tu_ghi_so_nhat_ky", cau[:500])
	frappe.db.commit()
	return dict(kq, che_do=che_do, tren_hang_doi=1, nhat_ky=cau)


def _go_co_neu_con_nguyen(ten):
	"""Gỡ cờ đối chiếu bằng MỘT câu ghi có điều kiện. Trả True nếu ghi được.

	Điều kiện gắn đúng vào trạng thái vừa kiểm: còn giữ cờ, và chưa có dấu
	vết hoá đơn nào. Lượt khác chen vào giữa thì không dòng nào khớp, câu ghi
	không đổi gì, và người gọi biết là phải bỏ qua tờ này (#266 vòng 5b).
	"""
	# GIỮ KHOÁ DÒNG trước khi đọc, đúng cách minvoice_an_toan.kiem_goi vẫn
	# làm. Khoá giữ tới lúc commit ở cuối vòng lặp, nên lượt khác không chen
	# vào giữa lúc đọc và lúc ghi được nữa.
	si = frappe.get_doc("Sales Invoice", ten, for_update=True)
	if da_co_hddt(si) or not cint(si.get("vgb_hddt_cho_doi_chieu")):
		return False
	# Ghi kèm luôn điều kiện, cho chắc cả khi bản Frappe nào đó không giữ
	# khoá như mong đợi: đổi rồi thì câu này không chạm được dòng nào.
	frappe.db.sql("""update `tabSales Invoice`
		set vgb_hddt_cho_doi_chieu = 0
		where name = %(ten)s
		  and ifnull(vgb_hddt_cho_doi_chieu, 0) = 1
		  and ifnull(custom_minvoice_id, '') = ''
		  and ifnull(custom_hddt_id, '') = ''
		  and ifnull(custom_hddt_so, '') = ''""", {"ten": ten})
	# Đọc lại DƯỚI CÙNG KHOÁ để chốt là mình gỡ được thật.
	lai = frappe.db.get_value("Sales Invoice", ten,
		["vgb_hddt_cho_doi_chieu", "custom_minvoice_id", "custom_hddt_id", "custom_hddt_so"],
		as_dict=True) or {}
	return not cint(lai.get("vgb_hddt_cho_doi_chieu")) and not da_co_hddt(lai)


def _dat_ngay_neu_con_nguyen(ten, anh_chup, ngay_dat):
	"""Khoá tờ chưa giữ cờ và chỉ đặt ngày khi nó còn đúng ảnh vừa chọn."""
	si = frappe.get_doc("Sales Invoice", ten, for_update=True)
	for truong in ("custom_minvoice_id", "custom_hddt_id", "custom_hddt_so"):
		if str(si.get(truong) or "") != str(anh_chup.get(truong) or ""):
			return False
	if cint(si.get("vgb_hddt_cho_doi_chieu")) != cint(anh_chup.get("vgb_hddt_cho_doi_chieu")):
		return False
	if _ngay(si.get(TRUONG_NGAY_XUAT)) != _ngay(anh_chup.get(TRUONG_NGAY_XUAT)):
		return False
	frappe.db.set_value("Sales Invoice", ten, TRUONG_NGAY_XUAT, ngay_dat, update_modified=False)
	return True


def chay_nen(ngay, che_do, nguoi="", ngay_tham_chieu="", ngay_dich=""):
	"""Lượt chạy nền: gỡ cờ, đánh dấu ngày lập, phát hành rồi ký.

	Gỡ cờ đối chiếu CHỈ khi m-invoice trả lời không có tờ nào mang mã phiếu
	đó. Không hỏi được thì giữ cờ, thà chậm còn hơn phát hành đúp (13/08).
	"""
	# #266 vong 5, claude bat dung: ham nay nang quyen len Administrator de
	# lam viec cua no. Khi xu_ly_ngay_cu khong day duoc sang hang doi va goi
	# THANG ham nay trong chinh request cua nguoi dung, quyen nang len do o
	# lai suot phan con lai cua request. xu_ly_ngay_cu mo cho ca ke toan
	# (QUYEN_KEO), nen mot lan Redis truc trac la ke toan chay tiep request
	# voi quyen Administrator. Nay nang quyen trong try/finally va tra lai
	# dung nguoi goi.
	nguoi_goc = frappe.session.user
	frappe.set_user("Administrator")
	try:
		return _chay_nen_da_nang_quyen(
			ngay, che_do, nguoi, ngay_tham_chieu, ngay_dich)
	finally:
		try:
			frappe.set_user(nguoi_goc)
		except Exception:
			pass


def _chay_nen_da_nang_quyen(
		ngay, che_do, nguoi="", ngay_tham_chieu="", ngay_dich=""):
	"""Than that cua chay_nen. Chi goi tu chay_nen, sau khi da nang quyen."""
	from vagabond.ban_hang import (
		_goi_server_script, _khoa_hddt, _mo_khoa_dong_bo, _cong_tac_minvoice,
		_phat_hanh_theo_lo, _ky_theo_lo,
	)
	ngay_chay_that = getdate(nowdate())
	hom_nay = _ngay(ngay_tham_chieu) or ngay_chay_that
	ngay_cu = _ngay(ngay)
	ngay_dat = _ngay(ngay_dich) or ngay_lap_theo_che_do(che_do, ngay_cu, hom_nay)
	if not con_trong_han_ky_gui(ngay_dat, ngay_chay_that) and ngay_dat not in _ngay_xac_nhan_qua_han(ngay_chay_that):
		raise ValueError(
			"Lệnh xử HĐĐT đã quá hạn ký/gửi của ngày %s (hạn bảo thủ %s). "
			"Mở lại Cài đặt, xem trước và xác nhận ngày mới; máy không tự đổi ngày sau nửa đêm."
			% (ngay_vn(ngay_dat), ngay_vn(han_ky_gui(ngay_dat))))
	chon, stg = _dem_theo_ngay(ngay_cu, hom_nay)
	if not con_trong_han_ky_gui(ngay_dat, ngay_chay_that):
		chon = [r for r in chon if ngay_dat in _ngay_xac_nhan_qua_han(ngay_chay_that, r.name)]
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

	# KHOÁ TRƯỚC KHI ĐỘNG VÀO TỜ NÀO (#266 vòng 5, Codex bắt đúng).
	#
	# Bản trước đọc danh sách, hỏi m-invoice, gỡ cờ và commit TỪNG TỜ, mãi
	# cuối hàm mới lấy khoá để phát hành. Nghĩa là suốt đoạn gỡ cờ, một lượt
	# gửi khác vẫn chạy song song được: lượt này cầm ảnh chụp cũ, ghi cờ về 0
	# và xoá mất dấu giữ chỗ mà lượt kia vừa đặt. Nay lấy khoá TRƯỚC, và
	# ngay trước khi ghi thì ĐỌC LẠI trạng thái tờ đó dưới khoá, khớp với ảnh
	# chụp mới ghi; tờ nào đã đổi trạng thái thì bỏ qua chứ không ghi đè.
	khoa_go = _khoa_hddt(cho=60)
	if khoa_go is None:
		kq["loi"].append("Lượt phát hành khác đang giữ khoá, chưa gỡ cờ tờ nào. "
			"Nhịp bù mỗi giờ sẽ làm tiếp.")
		chon = []
	try:
		for r in chon:
			try:
				# Đọc lại DƯỚI KHOÁ, không tin ảnh chụp lúc đầu hàm.
				moi_nhat = frappe.db.get_value("Sales Invoice", r.name,
					["custom_minvoice_id", "custom_hddt_id", "custom_hddt_so",
						"vgb_hddt_cho_doi_chieu", TRUONG_NGAY_XUAT], as_dict=True) or {}
				if da_co_hddt(moi_nhat):
					kq["loi"].append("%s: lượt khác vừa xuất xong tờ này, bỏ qua."
						% (r.custom_pancake_display_id or r.name))
					continue
				if cint(moi_nhat.get("vgb_hddt_cho_doi_chieu")):
					khong_co, cau = _tra_minvoice(base, hdr, r.name, chung) if base else (False, loi_dn)
					if not khong_co:
						kq["giu_co"] += 1
						if len(kq["loi"]) < 50:
							kq["loi"].append("%s: giữ cờ đối chiếu, %s" % (r.custom_pancake_display_id or r.name, cau))
						continue
					# GHI CÓ ĐIỀU KIỆN, KHÔNG đọc rồi ghi.
					#
					# #266 vòng 5b, Codex bắt đúng: đoạn hỏi m-invoice ở trên
					# có thể lâu, và trong lúc đó quản lý có thể bấm gửi tay
					# hoặc mở lại tờ này, đặt một dấu giữ chỗ MỚI. Đọc bằng
					# get_value trần rồi ghi ở câu sau là vẫn còn khe: dấu mới
					# có thể xuất hiện đúng giữa hai câu, và lượt này xoá mất
					# nó. Nay gỡ cờ bằng MỘT câu UPDATE có điều kiện, buộc
					# trạng thái phải đúng y như lúc vừa kiểm; đổi rồi thì
					# không dòng nào bị ghi và lượt này bỏ qua tờ đó.
					if not _go_co_neu_con_nguyen(r.name):
						kq["loi"].append("%s: lượt khác vừa xuất xong hoặc vừa đặt lại dấu chờ "
							"trong lúc hỏi m-invoice, bỏ qua."
							% (r.custom_pancake_display_id or r.name))
						continue
					frappe.get_doc("Sales Invoice", r.name).add_comment("Comment", "Gỡ cờ đối chiếu HĐĐT (#266): " + cau + ".")
					kq["go_co"] += 1
				if _ngay(moi_nhat.get(TRUONG_NGAY_XUAT)) != ngay_dat:
					if (not cint(moi_nhat.get("vgb_hddt_cho_doi_chieu"))
							and not _dat_ngay_neu_con_nguyen(r.name, moi_nhat, ngay_dat)):
						kq["loi"].append("%s: lượt khác vừa đổi dấu HĐĐT hoặc ngày hẹn, bỏ qua."
							% (r.custom_pancake_display_id or r.name))
						continue
					if cint(moi_nhat.get("vgb_hddt_cho_doi_chieu")):
						frappe.db.set_value("Sales Invoice", r.name, TRUONG_NGAY_XUAT,
							ngay_dat, update_modified=False)
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
	finally:
		if khoa_go is not None:
			_mo_khoa_dong_bo(khoa_go)

	# Phát hành NGAY sau khi người dùng đã xác nhận. Đêm 10/09 cho thấy để
	# chế độ kéo chờ tới chuỗi cuối ngày khiến cả tập có thể lỡ thêm một ngày.
	# Giữ ngày đi qua lô gốc; kéo ngày đi qua tập vgb_hddt_ngay_xuat vừa đặt.
	if kq["keo"]:
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
					ph = (_phat_hanh_theo_lo(str(ngay_cu)) if che_do == "giu_ngay" else
						phat_hanh(str(ngay_dat), _goi_server_script))
					kq["phat_hanh"] = "%d/%d tờ" % (ph.get("tao_ok") or 0, ph.get("tim_thay") or 0)
					kq["loi"] += [str(x) for x in (ph.get("loi") or [])][:10]
					if bat_ky:
						k = (_ky_theo_lo(str(ngay_cu)) if che_do == "giu_ngay" else
							ky(str(ngay_dat), _goi_server_script))
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


class KhongDocDuocNo(Exception):
	"""Không đọc được trạng thái nợ ngày cũ. KHÔNG được hiểu là hết nợ."""


def _loc_diem_dang_xuat(rows):
	"""Ngày còn nợ, CHỈ tính tờ thuộc điểm bán đang bật xuất hoá đơn.

	#266 vòng 5, Codex bắt đúng và đây là lỗi CHẾT MÁY chứ không phải lỗi
	nhỏ: hai tập nợ trước đây đếm mọi tờ cũ chưa có hoá đơn, kể cả tờ của
	nguồn hay quầy KHÔNG bật xuất hoá đơn, và cả phiếu tạo tay trên Desk có
	custom_nguon rỗng. Kịch bản phát hành lọc theo đúng nguồn và quầy trong
	cài đặt, nên nó KHÔNG BAO GIỜ xuất được những tờ ấy. Hệ quả:
	xuat_ngay_cu_truoc không rút cạn nổi ngày đó, còn chan_neu_con_ngay_cu
	thì chặn MỌI tờ mới, vĩnh viễn. Tức là cả tiệm ngừng xuất hoá đơn vì một
	phiếu Desk cũ không liên quan.

	Dùng CHÍNH thuoc_diem_dang_xuat của đường phát hành, không viết lại phép
	lọc thứ hai (điều 18). Đọc cài đặt hỏng thì NÉM, không âm thầm bỏ lọc.
	"""
	try:
		_stg, ds_nguon, ds_quay = _cai_dat_minvoice()
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "hddt_cho_xuat: doc cai dat m-invoice")
		raise KhongDocDuocNo("không đọc được cài đặt m-invoice: %s" % str(e)[:150])
	ra = []
	for r in rows or []:
		if not thuoc_diem_dang_xuat(r, ds_nguon, ds_quay):
			continue
		d = r.get("posting_date")
		if d is not None and d not in ra:
			ra.append(d)
	return ra


def ngay_cu_dang_cho():
	"""Ngày CŨ có tờ ĐỦ ĐIỀU KIỆN TỰ ĐỘNG phát hành mang đúng ngày bán.

	Tập HẸP: chỉ những tờ máy được phép tự gửi đi. Đừng dùng tập này để quyết
	định có chặn tờ ngày mới hay không, xem ngay_cu_can_bao_ve.
	Đọc lỗi thì NÉM, không trả rỗng: rỗng bị caller hiểu là hết nợ (#266 vòng 5).
	"""
	try:
		rows = frappe.db.sql("""select posting_date, custom_nguon, vgb_quay
			from `tabSales Invoice`
			where docstatus = 1 and ifnull(vgb_huy, 0) = 0 and ifnull(vgb_tam_tinh, 0) = 0
			  and grand_total > 0 and ifnull(vgb_hddt_cho_doi_chieu, 0) != 1
			  and ifnull(custom_hddt_so, '') = '' and ifnull(custom_minvoice_id, '') = ''
			  and ifnull(custom_hddt_id, '') = ''
			  and {truong} is not null and {truong} = posting_date
			  and posting_date < %(hom_nay)s""".format(truong=TRUONG_NGAY_XUAT),
			{"hom_nay": nowdate()}, as_dict=True)
		return _loc_diem_dang_xuat(rows)
	except KhongDocDuocNo:
		raise
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "hddt_cho_xuat: doc ngay cu dang cho")
		raise KhongDocDuocNo(str(e)[:200])


def ngay_cu_can_bao_ve():
	"""Ngày CŨ mà cửa m-invoice của nó CHƯA ĐƯỢC PHÉP đóng.

	Tập RỘNG, và cố ý rộng hơn tập tự phát hành (#266 vòng 5, Codex bắt đúng):
	bản trước chỉ bảo vệ những tờ đã đủ điều kiện tự gửi, nên ba nhóm sau
	KHÔNG được bảo vệ, mà đó lại chính là ba nhóm của đêm 09/09:
	  - tờ đang GIỮ CỜ đối chiếu (117 tờ TCV),
	  - đơn còn NHÁP chưa ghi sổ được (59 đơn Sales),
	  - tờ cũ chưa được đánh dấu vgb_hddt_ngay_xuat.
	Nằm trong tập này KHÔNG có nghĩa được tự gỡ cờ hay tự ghi sổ; nó chỉ có
	nghĩa là chưa được để một tờ ngày mới ra trước và đóng cửa của nó.
	Đọc lỗi thì NÉM, không trả rỗng.
	"""
	try:
		rows = frappe.db.sql("""select posting_date, custom_nguon, vgb_quay
			from `tabSales Invoice`
			where docstatus in (0, 1) and ifnull(vgb_huy, 0) = 0 and ifnull(vgb_tam_tinh, 0) = 0
			  and grand_total > 0
			  and ifnull(custom_hddt_so, '') = '' and ifnull(custom_minvoice_id, '') = ''
			  and ifnull(custom_hddt_id, '') = ''
			  and posting_date < %(hom_nay)s""",
			{"hom_nay": nowdate()}, as_dict=True)
		return _loc_diem_dang_xuat(rows)
	except KhongDocDuocNo:
		raise
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "hddt_cho_xuat: doc ngay cu can bao ve")
		raise KhongDocDuocNo(str(e)[:200])


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
	  - chạy xong mà m-invoice không nhận tờ nào thì ghi mốc lỗi để người
	    trực đọc; #266 vòng 5 đã GỠ HẲN van thời gian, mốc này chỉ để xem.
	Không có ngày cũ nào đang chờ thì trả True ngay, không tốn gì.
	"""
	try:
		# Tap RONG quyet dinh con no hay khong; tap HEP quyet dinh gui gi.
		ds = ngay_cu_can_bao_ve()
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
		ngay = ngay_cu_con_mo(ds, getdate(nowdate()), _ngay_so_hddt_moi_nhat(), _ngay_xac_nhan_qua_han())
		if not ngay:
			return True
		khoa = _khoa_hddt(cho=30)
		if khoa is None:
			# Lượt khác đang xuất ngày cũ. Chưa xong thì chưa được đụng tờ
			# hôm nay: đây chính là ca đồng thời Codex chỉ ra.
			return False
		con_no = False
		try:
			# Chi phat hanh nhung ngay co to DU DIEU KIEN tu gui.
			ngay_gui = [d for d in ngay if d in set(ngay_cu_dang_cho())]
			for d in ngay_gui:
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
		return not ngay_cu_con_mo(ngay_cu_can_bao_ve(), getdate(nowdate()), _ngay_so_hddt_moi_nhat(), _ngay_xac_nhan_qua_han())
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hddt_cho_xuat: xuat ngay cu truoc")
		# Hỏng giữa chừng thì coi như còn nợ, không cho tờ hôm nay đi.
		return False


def chan_neu_con_ngay_cu(si):
	"""CỬA CHUNG: gọi từ minvoice_an_toan.kiem_goi, ngay trước khi dựng payload.

	Mọi đường phát hành (chuỗi cuối ngày, xuất rải, chốt đơn tay, chốt cả
	loạt, nhịp bù, Server Script After Submit) đều đi qua kiem_goi, nên đặt
	ở đây là gom về một nguồn thay vì thêm chỗ nhớ gọi (điều 18). Cửa này
	cũng chặn chính tờ đang mang ngày lập đã quá hạn ký/gửi; không chỉ tính
	thứ tự với các tờ khác.

	#266 vòng 5: đọc tập RỘNG (ngay_cu_can_bao_ve), và KHÔNG đọc được trạng
	thái nợ thì CHẶN, không đi tiếp. Trước đây mọi lỗi ngoài ValueError đều
	rơi vào nhánh log rồi return, nên một lần lỗi đọc DB là tờ ngày mới đi
	lọt và đóng cửa ngày cũ vĩnh viễn.
	"""
	hom_nay = getdate(nowdate())
	ngay_to = ngay_lap(si)
	try:
		xac_nhan = _ngay_xac_nhan_qua_han(hom_nay)
		xac_nhan_to = _ngay_xac_nhan_qua_han(hom_nay, si.get("name") or "")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hddt_cho_xuat: doc xac nhan")
		frappe.throw("Chưa xuất được hóa đơn: không đọc được xác nhận xử lý ngày cũ. Nhờ quản lý kiểm tra; máy giữ nguyên chứng từ.")
	if not con_trong_han_ky_gui(ngay_to, hom_nay) and ngay_to not in xac_nhan_to:
		frappe.throw(
			"Cửa pháp lý để phát hành tờ mang ngày %s đã đóng. Theo Nghị định 70/2025/NĐ-CP, "
			"ký số và gửi cấp mã chậm nhất ngày làm việc tiếp theo; hệ thống dùng hạn bảo thủ %s. "
			"Mở Cài đặt để quản lý xác nhận cách xử lý; máy không tự đổi ngày lập." % (
				ngay_vn(ngay_to), ngay_vn(han_ky_gui(ngay_to)))
		)
	try:
		ds = ngay_cu_can_bao_ve()
	except (KhongDocDuocNo, Exception) as e:
		frappe.log_error(frappe.get_traceback(), "hddt_cho_xuat: doc no ngay cu")
		frappe.throw("Chưa xuất tờ này được: không đọc được trạng thái hoá đơn ngày cũ (%s). "
			"Máy dừng lại cho chắc, vì một tờ hôm nay ra trước là đóng cửa ngày cũ vĩnh viễn."
			% str(e)[:120])
	if ngay_to in xac_nhan:
		from vagabond.ban_hang import _ngay_so_hddt_moi_nhat
		if not cua_minvoice_con_mo(ngay_to, _ngay_so_hddt_moi_nhat()):
			frappe.throw("Cửa m-invoice đã đóng cho ngày lập này; xác nhận quá hạn không được vượt thứ tự hóa đơn.")
	if not ds:
		return
	try:
		from vagabond.ban_hang import _ngay_so_hddt_moi_nhat
		phai, ngay, ly_do = phai_nhuong_ngay_cu(
			ngay_to, hom_nay, ds, _ngay_so_hddt_moi_nhat(), xac_nhan)
	except ValueError:
		raise
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "hddt_cho_xuat: chan neu con ngay cu")
		frappe.throw("Chưa xuất tờ này được: không tính được thứ tự ngày xuất (%s)."
			% str(e)[:120])
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
		"là đóng cửa của ngày cũ vĩnh viễn. Xử nốt hoá đơn ngày cũ rồi tờ này mới đi được." % ly_do)


def ds_cho_xuat(ngay):
	"""Tờ chờ xuất cho ngày `ngay`, chưa có hoá đơn điện tử, không giữ cờ.

	#266 vòng 5b, Codex bắt đúng: dấu chờ xuất được đặt lúc kế toán bấm xử
	ngày cũ, còn lượt phát hành chạy sau đó hàng giờ. Trong quãng ấy Giám đốc
	có thể TẮT xuất hoá đơn cho một nguồn hay một quầy. Bản trước không đọc
	custom_nguon và vgb_quay nên vẫn trả tờ đó ra, mà phat_hanh gọi kịch bản
	kèm `phieu=` là đi vào nhánh MỘT TỜ, nhánh này bỏ qua bộ lọc nguồn/quầy
	(minvoice_phat_hanh_20260907.txt dòng 48-54). Kết quả: tờ vẫn được gửi
	lên m-invoice trong khi màn Cài đặt đang hiện là điểm ấy đã tắt.

	Nay đọc lại cài đặt NGAY TRƯỚC KHI GỬI và lọc bằng chính
	thuoc_diem_dang_xuat, cùng một phép lọc với mọi nơi khác (điều 18).
	"""
	rows = frappe.db.get_all(
		"Sales Invoice",
		filters={TRUONG_NGAY_XUAT: getdate(ngay), "docstatus": 1, "vgb_huy": 0, "vgb_tam_tinh": 0,
			"grand_total": [">", 0], "vgb_hddt_cho_doi_chieu": ["!=", 1]},
		fields=["name", "custom_minvoice_id", "custom_hddt_id", "custom_hddt_so",
			"custom_hddt_trang_thai", "custom_nguon", "vgb_quay"],
		order_by="name asc", limit_page_length=0,
	)
	_stg, ds_nguon, ds_quay = _cai_dat_minvoice()
	return [r for r in rows
		if not da_co_hddt(r) and thuoc_diem_dang_xuat(r, ds_nguon, ds_quay)]


def ngay_cho_xuat_can_thu_lai(hom_nay):
	"""Ngày hẹn chưa phát hành cần nhịp giờ thử lại, tách rõ ngày đã quá hạn.

	Một tờ hẹn 10/09 mà lỗi trước nửa đêm vẫn phải được thử lại ngày 11/09.
	Nếu tới sau hạn ký/gửi bảo thủ thì không gửi lùi ngày nữa; trả riêng trong
	`qua_han` để báo người dùng chạy lại cửa kéo ngày thay vì làm tờ biến mất.
	"""
	hom_nay = _ngay(hom_nay)
	rows = frappe.db.get_all(
		"Sales Invoice",
		filters={TRUONG_NGAY_XUAT: ["<=", hom_nay], "docstatus": 1,
			"vgb_huy": 0, "vgb_tam_tinh": 0, "grand_total": [">", 0],
			"vgb_hddt_cho_doi_chieu": ["!=", 1]},
		fields=["name", TRUONG_NGAY_XUAT, "custom_minvoice_id", "custom_hddt_id",
			"custom_hddt_so", "custom_nguon", "vgb_quay"],
		order_by=TRUONG_NGAY_XUAT + " asc, name asc", limit_page_length=0,
	)
	_stg, ds_nguon, ds_quay = _cai_dat_minvoice()
	con_han, qua_han = [], []
	xac_nhan = _ngay_xac_nhan_qua_han(hom_nay)
	for r in rows:
		if da_co_hddt(r) or not thuoc_diem_dang_xuat(r, ds_nguon, ds_quay):
			continue
		d = _ngay(r.get(TRUONG_NGAY_XUAT))
		dich = con_han if con_trong_han_ky_gui(d, hom_nay) or d in xac_nhan else qua_han
		if d and d not in dich:
			dich.append(d)
	return {"con_han": con_han, "qua_han": qua_han}


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

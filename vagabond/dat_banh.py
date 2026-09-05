# -*- coding: utf-8 -*-
"""Nền móng cho luồng khách đặt bánh ổ tại cửa hàng.

Anh Việt giao ở issue #195, chốt năm câu nghiệp vụ ngày 05/09/2026:

  1. Khách trả trước TOÀN BỘ đơn hàng, không phải đặt cọc một phần.
  2. Thu tiền mặt tại quầy được.
  3. Đặt ở điểm này, nhận ở điểm khác được.
  4. Khách huỷ thì hoàn tiền, đi đường `hoan_tien.py` đã chốt với chị Dung
     16/08/2026 (tiền ra từ tài khoản ngân hàng công ty, KHÔNG rút két).
  5. Hoá đơn VAT xuất vào NGÀY GIAO.

Tệp này là phần NỀN, không có màn hình nào. Màn đặt bánh cho thu ngân nằm
ở bản sau.

BA CÁI NGÀY, ĐỪNG LẪN
=====================
Anh Việt hỏi 05/09: nhập luôn ngày thu tiền và ngày lấy bánh được không,
giống lên đơn bên Pancake. Được, và phải tách hẳn ba cái ngày ra:

  - Ngày ĐẶT   : ngày lập phiếu. Không quyết định gì về tiền hay bánh.
  - Ngày THU   : ngày tiền thật sự vào. Quyết định tiền rơi vào CA nào.
                 Khách đặt hôm nay, mai mới chuyển khoản là chuyện thường,
                 nên không được suy ra từ ngày đặt.
  - Ngày NHẬN  : ngày khách ra lấy bánh. Quyết định bảng kiểm bánh giữ chỗ
                 vào NGÀY NÀO, và là ngày xuất hoá đơn VAT.

Gộp bất kỳ hai cái nào lại là sinh ra đúng những lỗi đã mô tả ở issue.

VÌ SAO CHỐT CA LỆCH HAI ĐẦU NẾU KHÔNG LÀM GÌ
=============================================
Câu 1 cộng câu 5 tạo ra một thứ mà đọc lướt không thấy:

  - Ngày thu : tiền vào két, KHÔNG có hoá đơn nào. Két thừa đúng bằng giá
               trị đơn, vì `ca_quay._doanh_thu_he_thong` chỉ đọc hoá đơn.
  - Ngày nhận: có hoá đơn đủ giá trị tại điểm đó, KHÔNG một đồng nào vào
               két. Máy đòi thu ngân một khoản tiền không tồn tại.

Hai đầu gỡ bằng hai đường khác nhau:

  - Đầu ngày nhận: hoá đơn mang phương thức "Trả trước", thuộc nhóm
    `pt_thanh_toan.TIEN_NGAY_KHAC`, và `_ngoai_ket()` đã kể nhóm đó nên
    nó rơi khỏi bảng đối soát két.
  - Đầu ngày thu: `_doanh_thu_he_thong` cộng thêm chứng từ thu ứng trước
    của đúng điểm trong đúng khoảng ca. Đó là hàm `thu_ung_truoc` dưới.

Bất biến phải giữ: tiền vào két trong cả vòng đời một đơn đúng MỘT lần, ở
ngày thu. Đây là điều kiện viết được ca kiểm thử, không phải câu nói cho
hay.
"""

import frappe
from frappe.utils import flt, getdate

# Bánh ổ. Cùng tiền tố mà `kiem_banh` đang dùng, không gõ lại chuỗi ở đây
# để hai nơi không bao giờ nói khác nhau (QT-19).
from vagabond.kiem_banh import TIEN_TO_MA

PT_TRA_TRUOC = "Trả trước"

SO = "Sales Order"
PE = "Payment Entry"

# Ô điểm bán trên chứng từ thu. Không có ô này thì màn Chốt ca không biết
# khoản tiền ứng trước rơi vào quầy nào, và cả ba điểm cùng nhận hoặc cùng
# không nhận - hai kiểu sai đều làm thu ngân phải bịa lý do lệch.
TRUONG_MOI = {
	PE: [
		{
			"fieldname": "vgb_quay",
			"label": "Quầy thu tiền",
			"fieldtype": "Data",
			"insert_after": "mode_of_payment",
			"read_only": 1,
			"description": "Mã quầy nhận khoản tiền này. Máy điền, dùng cho màn Chốt ca.",
		},
		{
			"fieldname": "vgb_phieu_dat",
			"label": "Phiếu đặt bánh",
			"fieldtype": "Link",
			"options": SO,
			"insert_after": "vgb_quay",
			"read_only": 1,
			"description": "Phiếu đặt mà khoản tiền này trả trước cho.",
		},
	],
}


# ------------------------------------------------------------ phần thuần
#
# Không chạm Frappe nên kiểm thử được không cần site.


def _so_nguyen(x):
	try:
		return int(flt(x))
	except (TypeError, ValueError):
		return 0


def la_banh_o(ma):
	"""Mã hàng này có phải bánh ổ không. THUẦN."""
	return str(ma or "").upper().startswith(TIEN_TO_MA)


def con_giu_cho(qty, da_giao, da_xuat_hoa_don):
	"""Một dòng phiếu đặt còn GIỮ CHỖ bao nhiêu cái. THUẦN.

	Vì sao lấy MAX của hai cột đã giao và đã xuất hoá đơn, chứ không cộng
	hai cột lại và cũng không chọn cứng một cột:

	  - Nếu ngày nhận đi đường phiếu giao hàng rồi mới hoá đơn thì cột đã
	    giao chạy trước.
	  - Nếu sinh thẳng hoá đơn có trừ kho thì cột đã xuất hoá đơn chạy,
	    còn cột đã giao có thể đứng yên.

	Cộng hai cột là trừ hai lần, khách đặt 2 cái mà bảng tưởng đã giao 4.
	Chọn cứng một cột là chọn sai ở một trong hai đường. Lấy max thì đường
	nào chạy cũng đúng, và không bao giờ trừ quá số đặt.

	Codex nhắc đúng ở issue #195: đừng chỉ loại mọi hoá đơn có gắn phiếu
	đặt, vì làm vậy thì sau khi giao xong số bánh đã bán trong ngày biến
	mất khỏi bảng. Ở đây phần đã giao rời khỏi cột giữ chỗ và đi vào cột
	kênh khác của chính ngày giao, nên tổng luôn cân.
	"""
	q = _so_nguyen(qty)
	if q <= 0:
		return 0
	xong = max(_so_nguyen(da_giao), _so_nguyen(da_xuat_hoa_don))
	return max(0, min(q, q - xong))


def gom_giu_cho(dong):
	"""Gom các dòng phiếu đặt thành {ngày nhận: {mã hàng: số còn giữ}}. THUẦN.

	`dong` là list dict {item_code, delivery_date, qty, delivered_qty,
	billed_qty}. Bỏ dòng không phải bánh ổ, bỏ dòng đã giao xong, bỏ dòng
	thiếu ngày nhận (không biết giữ chỗ vào ngày nào thì giữ vào ngày nào
	cũng là đoán).
	"""
	ra = {}
	for d in dong or []:
		if not isinstance(d, dict):
			continue
		ma = str(d.get("item_code") or "").strip().upper()
		if not la_banh_o(ma):
			continue
		ngay = str(d.get("delivery_date") or "").strip()
		if not ngay:
			continue
		con = con_giu_cho(d.get("qty"), d.get("delivered_qty"), d.get("billed_qty"))
		if con <= 0:
			continue
		ra.setdefault(ngay, {})
		ra[ngay][ma] = ra[ngay].get(ma, 0) + con
	return ra


def hai_ngay_phai_do(ngay_cu, ngay_moi):
	"""Đổi ngày chứng từ thì phải đo lại NHỮNG ngày nào. THUẦN.

	Lỗi có sẵn từ trước, Codex bắt được ở issue #195: hook cũ chỉ đo lại
	ngày mới, nên số của ngày cũ mắc lại ở đó mãi. Khách dời ngày nhận từ
	20 sang 22 thì ngày 20 vẫn giữ chỗ một cái bánh không còn ai đặt, và
	sales từ chối khách oan.

	Trả về tập ngày, đã bỏ rỗng và bỏ trùng.
	"""
	ra = []
	for n in (ngay_cu, ngay_moi):
		n = str(n or "").strip()
		if n and n not in ra:
			ra.append(n)
	return ra


def tong_ung_truoc(rows):
	"""Gom chứng từ thu ứng trước thành {phương thức: số tiền}. THUẦN.

	Bỏ dòng số tiền không dương: chứng từ âm là dấu hiệu gõ nhầm, cộng vào
	là tự làm lệch ca theo chiều ngược lại.
	"""
	ra = {}
	for r in rows or []:
		if not isinstance(r, dict):
			continue
		so = flt(r.get("so_tien"))
		if so <= 0:
			continue
		pt = str(r.get("pt") or "").strip() or "Chưa rõ"
		ra[pt] = ra.get(pt, 0.0) + so
	return ra


# ------------------------------------------------------------- chạm Frappe


def dong_phieu_dat(ngay=None):
	"""Các dòng phiếu đặt bánh ổ CÒN HIỆU LỰC, để đo giữ chỗ.

	Chỉ lấy phiếu đã ghi sổ và chưa đóng: phiếu nháp chưa phải cam kết,
	phiếu đã đóng hoặc đã huỷ thì khách không còn đặt nữa.
	"""
	loc = {"docstatus": 1, "status": ["not in", ["Closed", "Cancelled"]]}
	cha = frappe.get_all(SO, filters=loc, pluck="name", limit_page_length=0)
	if not cha:
		return []
	loc_dong = {"parent": ["in", cha]}
	if ngay:
		loc_dong["delivery_date"] = str(getdate(ngay))
	return frappe.get_all(
		"Sales Order Item",
		filters=loc_dong,
		fields=["item_code", "delivery_date", "qty", "delivered_qty", "billed_qty"],
		limit_page_length=0,
	)


def dem_giu_cho(ngay):
	"""Số bánh ổ đang được giữ chỗ cho MỘT ngày nhận. {mã hàng: số}."""
	try:
		dong = dong_phieu_dat(ngay)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "dat_banh: doc dong phieu dat")
		return {}
	gom = gom_giu_cho([dict(d, delivery_date=str(d.get("delivery_date") or "")) for d in dong])
	return gom.get(str(getdate(ngay)), {})


def thu_ung_truoc(quay, tu_luc, den_luc, theo_ngay=False):
	"""Tiền khách trả TRƯỚC đã vào trong khoảng ca, theo từng phương thức.

	Đây là nửa còn thiếu của màn Chốt ca. Không có hàm này thì ngày khách
	đặt bánh và trả tiền, két thừa đúng bằng số tiền đó mà không dòng nào
	trên bảng đối soát giải thích được.

	`theo_ngay` đi theo đúng quy ước của `_doanh_thu_he_thong`: điểm có
	quầy lọc theo giờ tạo, điểm không quầy lọc theo ngày chứng từ. Truyền
	sai mốc thì một ca mở 8h sẽ nuốt cả tiền của hôm qua.
	"""
	loc = {
		"docstatus": 1,
		"payment_type": "Receive",
		"party_type": "Customer",
		"vgb_quay": str(quay or "").strip().upper(),
		# Chỉ khoản CHƯA gán hết vào hoá đơn mới là trả trước. Khoản đã gán
		# hết là tiền trả cho một hoá đơn đã tồn tại, và hoá đơn đó đã được
		# đếm ở đường thường rồi - cộng thêm là đếm hai lần.
		"unallocated_amount": [">", 0],
	}
	if theo_ngay:
		loc["posting_date"] = ["between", [str(getdate(tu_luc)), str(getdate(den_luc))]]
	else:
		loc["creation"] = ["between", [str(tu_luc), str(den_luc)]]
	try:
		ds = frappe.get_all(
			PE, filters=loc,
			fields=["name", "mode_of_payment", "unallocated_amount"],
			limit_page_length=0,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "dat_banh: doc thu ung truoc")
		return {}
	return tong_ung_truoc([
		{"pt": r.get("mode_of_payment"), "so_tien": r.get("unallocated_amount")}
		for r in ds
	])

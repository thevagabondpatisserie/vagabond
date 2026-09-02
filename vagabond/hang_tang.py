# -*- coding: utf-8 -*-
"""Phương thức thanh toán "Hàng tặng" và luồng giám đốc duyệt.

Anh Việt đặt bài 31/08/2026:

    *"Anh đang muốn làm thêm 1 phương thức thanh toán nữa là 'Hàng tặng'.
    Máy sẽ cho ghi sổ mà không cần đối soát, xuất hoá đơn nguyên giá sản
    phẩm và ghi trên hoá đơn ở phần ghi chú khi xuất hoá đơn. Nhưng với
    những đơn chọn phương thức này thì em cho anh luồng gửi giám đốc duyệt
    đơn được không để tránh gian lận. Lập 1 màn duyệt đơn tặng bên phân hệ
    kế toán để anh vào duyệt thì đơn sẽ để đó chờ ghi sổ."*

KHÁC GÌ VỚI `qua_tang_hoa_don.py`
=================================
Hai đường tặng, khác nhau ở chỗ ai duyệt và duyệt lúc nào.

`qua_tang_hoa_don` là quà VIP có KẾ HOẠCH: đợt tặng quà đã lập từ trước,
đã duyệt từng khách từng món, hoá đơn chỉ là bước cuối. Duyệt xảy ra trước
khi bán.

Tệp này là hàng tặng PHÁT SINH tại quầy: khách phàn nàn nên tặng lại một
cái bánh, đối tác ghé chơi, KOL tới chụp hình. Không ai lập kế hoạch trước
được, nên duyệt phải xảy ra SAU khi đơn đã lập và TRƯỚC khi đơn vào sổ.

Hai đường dùng chung ba thứ, cố ý không chép lại: câu ghi chú trên từng
dòng hàng, hình dạng bút toán gạt công nợ, và ô Tài khoản chi phí biếu
tặng trong Cài đặt. Xem `qua_tang_hoa_don.them_ghi_chu`, `dong_but_toan`
và `_tk_chi_phi`.

BỐN HÀNG RÀO CHỐNG GIAN LẬN
===========================
1. Không ghi sổ được khi chưa duyệt. Chặn ở `before_submit`, tức là cửa
   thật, không phải chỉ giấu nút trên màn hình.
2. Bắt buộc khai LÝ DO tặng và LOẠI tặng ngay lúc lưu. Không có ô nào để
   trống cho qua, vì "tặng khách" không nói được gì khi rà lại cuối tháng.
3. DẤU VÂN ĐƠN. Duyệt xong mà sửa đơn - thêm món, đổi số lượng, đổi tiền -
   thì đơn tự rơi về Chờ duyệt. Không có hàng rào này thì xin duyệt một cái
   bánh mì rồi sửa thành một cái bánh kem là xong.
4. Giám đốc duyệt, không phải quản lý ca. Xem `VAI_DUYET`.

VÌ SAO KHÔNG CẦN ĐỐI SOÁT
=========================
Đối soát là việc so tiền đã về ngân hàng với tiền trên đơn. Đơn hàng tặng
không có đồng nào về, nên không có gì để soát. Phép "đơn này ghi sổ được
chưa" bên `ghi_so_dieu_kien` vốn chỉ đòi mã tham chiếu với phương thức có
bật cờ bắt buộc, và đòi tiền về với riêng Chuyển khoản, nên Hàng tặng đi
qua tự nhiên. Cái duy nhất phải thêm vào đó là câu "đang chờ giám đốc
duyệt".

TIỀN KHÔNG BAO GIỜ VỀ, KHÁC VỚI TIỀN CHƯA VỀ
=============================================
Màn Chốt ca chia phương thức theo lúc tiền vào két. Hàng tặng không thuộc
nhóm nào có sẵn: không phải tiền vào ngay, không phải bên thứ ba giữ rồi
trả sau, cũng không phải khách nợ phải đi đòi. Nên `pt_thanh_toan` có thêm
nhóm thứ tư `TIEN_KHONG_THU`. Xếp nhầm nó vào ba nhóm cũ thì thu ngân đếm
tiền xong sẽ thấy thiếu đúng bằng số hàng đã tặng, mà không hiểu vì sao.
"""

# --------------------------------------------------------------- phần thuần
#
# Đặt trên `import frappe` để bộ kiểm thử tầng khung chạy được ở CI tay
# không. Ca kiểm ở khung/kiem_thu/thu_hang_tang.py.

PT_TANG = "Hàng tặng"

TT_CHO = "Chờ duyệt"
TT_DUYET = "Đã duyệt"
TT_TU_CHOI = "Từ chối"
TT_DS = (TT_CHO, TT_DUYET, TT_TU_CHOI)

# Loại tặng. Bắt chọn một cái ngay lúc lập, để cuối tháng còn cộng ra được
# tiệm đã tặng đi bao nhiêu cho việc gì. Khoá không dấu để lưu vào cơ sở dữ
# liệu, nhãn có dấu để hiện lên màn.
LOAI_TANG = (
	("vip", "Khách VIP, khách quen"),
	("den_bu", "Đền bù sự cố cho khách"),
	("marketing", "Marketing, KOL, chụp hình"),
	("doi_tac", "Đối tác, ngoại giao"),
	("noi_bo", "Nội bộ, thử món, đào tạo"),
	("khac", "Khác"),
)
NHAN_LOAI = dict(LOAI_TANG)

# Loại tặng BẮT BUỘC có ảnh chứng minh (anh Việt duyệt 31/08/2026).
#
# Chỉ đền bù sự cố. Lý do: ba loại kia có dấu vết ở nơi khác - khách VIP có
# phiếu tặng quà, marketing có kế hoạch, đối tác có lịch hẹn. Riêng "đền bù
# sự cố" thì bằng chứng duy nhất là cái bánh hỏng, mà cái đó chỉ còn lại
# trong một tấm ảnh. Không có ảnh thì bất kỳ ai cũng khai được là đền bù.
LOAI_CAN_ANH = ("den_bu",)

# Chờ duyệt quá bao nhiêu ngày thì kêu. Đơn tặng nằm chờ là đơn chưa vào
# sổ, mà cuối tháng chốt sổ thì nó thành lỗ hổng doanh thu.
CHO_NGAY = 1

# Ô nào trên đơn phải khai trước khi lưu. Câu phải nói RÕ PHẢI LÀM GÌ.
THIEU = {
	"ly_do": (
		"Đơn hàng tặng phải ghi rõ LÝ DO tặng cho ai, vì việc gì. "
		"Ghi \"tặng khách\" là không đủ, cuối tháng rà lại không ai hiểu."
	),
	"loai": "Đơn hàng tặng phải chọn LOẠI tặng để cuối tháng còn cộng ra được.",
	"anh": (
		"Đơn tặng loại Đền bù sự cố phải đính ít nhất một ẢNH chứng minh "
		"(bánh hỏng, tin nhắn khách phàn nàn). Không có ảnh thì ai cũng khai "
		"được là đền bù."
	),
}


def chuoi(x):
	return str(x if x is not None else "").strip()


def _so(x):
	if x is None or x is False or x == "":
		return 0
	try:
		return 1 if int(x) else 0
	except (TypeError, ValueError):
		return 1 if chuoi(x) else 0


def la_don_tang(don):
	"""Tờ này có đi đường hàng tặng không. THUẦN."""
	return chuoi((don or {}).get("vgb_pt_thanh_toan")) == PT_TANG


def can_anh(loai):
	"""Loại tặng này có bắt buộc ảnh chứng minh không. THUẦN."""
	return chuoi(loai) in LOAI_CAN_ANH


def thieu_gi(don, so_anh=None):
	"""Những ô bắt buộc còn trống trên một đơn hàng tặng. THUẦN.

	Trả DANH SÁCH mã thiếu chứ không ném lỗi ngay: phần thuần không được
	chạm Frappe, và người dùng nên thấy hết mọi chỗ sai trong một lần.

	`so_anh` là số ảnh đang đính trên tờ. Truyền None nghĩa là NGƯỜI GỌI
	CHƯA ĐẾM, và khi đó phép kiểm ảnh được bỏ qua thay vì báo thiếu. Thà im
	còn hơn chặn oan một tờ chỉ vì nơi gọi chưa đọc tệp đính kèm.
	"""
	d = don or {}
	ra = []
	if len(chuoi(d.get("vgb_tang_ly_do"))) < 5:
		ra.append("ly_do")
	lo = chuoi(d.get("vgb_tang_loai"))
	if lo not in NHAN_LOAI:
		ra.append("loai")
	elif can_anh(lo) and so_anh is not None and int(so_anh or 0) <= 0:
		ra.append("anh")
	return ra


def dau_van(tong, dong):
	"""Dấu vân của một đơn tặng: đổi ruột là đổi dấu. THUẦN.

	Vì sao phải có. Giám đốc duyệt một đơn 45.000 đ một cái bánh mì, xong
	người lập sửa thành một cái bánh kem 850.000 đ mà trạng thái vẫn Đã
	duyệt. Không hàng rào nào khác bắt được, vì đơn vẫn là đơn đó.

	Dấu gồm tổng tiền, và từng mã món kèm số lượng đã SẮP XẾP. Sắp xếp để
	đảo thứ tự hai dòng không bị coi là đổi ruột - đảo thứ tự thì đơn vẫn y
	nguyên, bắt duyệt lại là làm phiền vô cớ.
	"""
	cac = []
	for d in (dong or []):
		ma = chuoi((d or {}).get("ma"))
		if not ma:
			continue
		try:
			sl = float((d or {}).get("so_luong") or 0)
		except (TypeError, ValueError):
			sl = 0.0
		cac.append("%s:%s" % (ma, ("%.3f" % sl)))
	cac.sort()
	return "%.2f|%s" % (float(tong or 0), ",".join(cac))


def can_duyet_lai(dau_cu, dau_moi):
	"""Đơn đã duyệt có bị sửa ruột sau đó không. THUẦN.

	Chưa có dấu cũ thì KHÔNG bắt duyệt lại: đó là đơn của trước khi có tính
	năng này, hoặc đơn vừa duyệt xong trong cùng một lần lưu. Bắt duyệt lại
	trong hai ca đó là chặn oan người đang làm đúng.
	"""
	cu = chuoi(dau_cu)
	if not cu:
		return False
	return cu != chuoi(dau_moi)


def trang_thai_moi(tt_cu, thieu, dau_cu, dau_moi):
	"""Trạng thái duyệt của đơn sau khi lưu. THUẦN.

	Một chỗ duy nhất quyết định, để màn hình, hook lưu và hook ghi sổ không
	bao giờ nói ba câu khác nhau về cùng một tờ.
	"""
	tt = chuoi(tt_cu)
	if tt not in TT_DS:
		return TT_CHO
	if tt == TT_DUYET and can_duyet_lai(dau_cu, dau_moi):
		return TT_CHO
	# Còn thiếu ô bắt buộc thì không thể đang ở trạng thái đã duyệt: giám đốc
	# duyệt cái gì khi lý do còn trống.
	if tt == TT_DUYET and thieu:
		return TT_CHO
	return tt


def ly_do_chua_ghi_so(don):
	"""Mã lý do đơn tặng chưa ghi sổ được. Rỗng nghĩa là ghi sổ được. THUẦN.

	Dùng chung với `ghi_so_dieu_kien` - xem hai mã `tang_cho_duyet` và
	`tang_tu_choi` khai bên đó. Để phép ở đây chứ không nhét hết sang bên
	kia vì bên kia là tệp phép chung cho MỌI phương thức, còn đây là luật
	riêng của một phương thức.
	"""
	if not la_don_tang(don):
		return ""
	tt = chuoi((don or {}).get("vgb_tang_duyet"))
	if tt == TT_TU_CHOI:
		return "tang_tu_choi"
	if tt != TT_DUYET:
		return "tang_cho_duyet"
	return ""


def cho_bao_lau(tt, lap_luc, hom_nay=None, nguong=CHO_NGAY):
	"""Đơn chờ duyệt đã nằm đó bao nhiêu ngày, và có quá hạn chưa. THUẦN.

	Chỉ tính đơn đang Chờ duyệt. Ngày hỏng hoặc ngày ở tương lai thì trả 0
	và không kêu: thà im còn hơn dựng một cảnh báo đỏ vì một ô ngày lỗi.
	"""
	if chuoi(tt) != TT_CHO:
		return (0, False)
	import datetime

	def _ngay(v):
		if isinstance(v, datetime.datetime):
			return v.date()
		if isinstance(v, datetime.date):
			return v
		s = chuoi(v)[:10]
		try:
			return datetime.date(int(s[0:4]), int(s[5:7]), int(s[8:10]))
		except (ValueError, IndexError):
			return None

	a = _ngay(lap_luc)
	b = _ngay(hom_nay) or datetime.date.today()
	if not a:
		return (0, False)
	so = (b - a).days
	if so < 0:
		return (0, False)
	return (so, so >= int(nguong or CHO_NGAY))


def dieu_kien_tim(tim, truong):
	"""Điều kiện tìm chạy Ở MÁY CHỦ (QT-19). THUẦN.

	Lọc bằng `or_filters` ở tầng cơ sở dữ liệu, không đọc N dòng về rồi lọc
	bằng Python - cách sau chỉ tìm được trong phần đã đọc về.
	"""
	q = chuoi(tim)
	if not q:
		return None
	return [[c, "like", "%" + q + "%"] for c in truong]


# ------------------------------------------------------------ phần chạm hệ

import frappe  # noqa: E402
from frappe.utils import cint, flt, now_datetime, nowdate  # noqa: E402

SI = "Sales Invoice"

# Ai được duyệt. Giám đốc và quản trị hệ thống, hết. Cố ý KHÔNG mở cho
# Accounts Manager hay quản lý cửa hàng: cả hai vai đó đang ở ngay tại chỗ
# bán, mà hàng rào này sinh ra để tách người tặng khỏi người duyệt.
from vagabond.quyen_phan_he import ROLE_GIAM_DOC  # noqa: E402

from vagabond import ten_nguoi  # noqa: E402

VAI_DUYET = {"System Manager", ROLE_GIAM_DOC, "AP Giám đốc"}

TRUONG_TIM = (
	"name", "customer_name", "custom_pancake_display_id",
	"vgb_tang_ly_do", "vgb_ghi_chu", "vgb_ma_tham_chieu",
)

TRUONG_MOI = {
	SI: [
		{
			"fieldname": "sec_hang_tang",
			"label": "Hàng tặng không thu tiền",
			"fieldtype": "Section Break",
			"insert_after": "vgb_but_toan_qua",
			"collapsible": 1,
			"depends_on": "eval:doc.vgb_pt_thanh_toan=='%s'" % PT_TANG,
		},
		{
			"fieldname": "vgb_tang_loai",
			"label": "Loại tặng",
			"fieldtype": "Select",
			"insert_after": "sec_hang_tang",
			"options": "\n" + "\n".join(k for k, _t in LOAI_TANG),
			"description": "Bắt buộc với đơn trả bằng Hàng tặng.",
		},
		{
			"fieldname": "vgb_tang_ly_do",
			"label": "Lý do tặng",
			"fieldtype": "Small Text",
			"insert_after": "vgb_tang_loai",
			"description": (
				"Tặng cho ai, vì việc gì. Đây là thứ giám đốc đọc để duyệt, "
				"và là thứ kế toán đọc lại cuối tháng."
			),
		},
		{
			"fieldname": "vgb_tang_duyet",
			"label": "Duyệt đơn tặng",
			"fieldtype": "Select",
			"insert_after": "vgb_tang_ly_do",
			"options": "\n" + "\n".join(TT_DS),
			"read_only": 1,
			"description": (
				"Máy tự đặt. Chưa Đã duyệt thì đơn không ghi sổ được. Sửa ruột "
				"đơn sau khi đã duyệt thì đơn tự rơi về Chờ duyệt."
			),
		},
		{
			"fieldname": "vgb_tang_nguoi_duyet",
			"label": "Người duyệt",
			"fieldtype": "Link",
			"options": "User",
			"insert_after": "vgb_tang_duyet",
			"read_only": 1,
		},
		{
			"fieldname": "vgb_tang_luc_duyet",
			"label": "Duyệt lúc",
			"fieldtype": "Datetime",
			"insert_after": "vgb_tang_nguoi_duyet",
			"read_only": 1,
		},
		{
			"fieldname": "vgb_tang_y_kien",
			"label": "Ý kiến người duyệt",
			"fieldtype": "Small Text",
			"insert_after": "vgb_tang_luc_duyet",
			"read_only": 1,
		},
		{
			"fieldname": "vgb_tang_dau_van",
			"label": "Dấu vân đơn lúc duyệt",
			"fieldtype": "Data",
			"insert_after": "vgb_tang_y_kien",
			"read_only": 1,
			"hidden": 1,
			"description": (
				"Máy ghi lúc duyệt. Đơn bị sửa ruột sau đó thì dấu lệch và đơn "
				"phải xin duyệt lại."
			),
		},
		{
			"fieldname": "vgb_but_toan_tang",
			"label": "Bút toán gạt công nợ hàng tặng",
			"fieldtype": "Link",
			"options": "Journal Entry",
			"insert_after": "vgb_tang_dau_van",
			"read_only": 1,
		},
	],
}


# Đuôi tệp coi là ẢNH. Đính một tệp .pdf hay .docx rồi bảo đó là bằng chứng
# bánh hỏng thì không ai soi được trên điện thoại, nên chỉ nhận ảnh thật.
DUOI_ANH = (".jpg", ".jpeg", ".png", ".webp", ".heic", ".gif")


def la_anh(ten):
	"""Tên tệp này có phải ảnh không. THUẦN."""
	t = chuoi(ten).lower()
	return any(t.endswith(x) for x in DUOI_ANH)


def _anh_cua_to(name):
	"""Ảnh đang đính trên một tờ hoá đơn. Trả danh sách {url, ten}."""
	ra = []
	try:
		for f in frappe.get_all(
			"File",
			filters={"attached_to_doctype": SI, "attached_to_name": name},
			fields=["file_url", "file_name"],
			order_by="creation asc", limit_page_length=0,
		):
			if la_anh(f.get("file_name")) or la_anh(f.get("file_url")):
				ra.append({"url": f.get("file_url") or "", "ten": f.get("file_name") or ""})
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hang_tang: doc anh dinh kem")
	return ra


def _dong_cua_to(doc):
	"""Các dòng hàng của tờ, dạng phần thuần đọc được."""
	return [
		{"ma": (d.get("item_code") or ""), "so_luong": flt(d.get("qty"))}
		for d in (doc.get("items") or [])
	]


def _dau_van_cua_to(doc):
	return dau_van(flt(doc.get("grand_total")), _dong_cua_to(doc))


def duoc_duyet(nguoi=None):
	return bool(VAI_DUYET & set(frappe.get_roles(nguoi)))


def _chan_neu_khong_duyet():
	if not duoc_duyet():
		frappe.throw(
			"Chỉ Giám đốc mới duyệt được đơn hàng tặng. Hàng rào này sinh ra "
			"để người tặng và người duyệt không phải là một. Cần duyệt thì "
			"nhờ anh Việt.",
			title="Không có quyền duyệt đơn tặng",
		)


# ------------------------------------------------------------------- hooks


def truoc_khi_luu(doc, method=None):
	"""Hook validate: giữ nguyên giá, và đặt trạng thái duyệt.

	VÌ SAO KHÔNG CHẶN CỨNG Ở ĐÂY dù loại tặng và lý do là bắt buộc.

	Thu ngân chọn "Hàng tặng" trên màn tính tiền là một cú bấm, và chính cú
	bấm đó LƯU tờ hoá đơn. Nếu lúc lưu đã đòi lý do thì không bao giờ chọn
	được phương thức này: chưa lưu được thì chưa có ô nào để gõ lý do vào,
	mà muốn có ô thì phải lưu trước. Vòng luẩn quẩn, và người dùng chỉ thấy
	một câu lỗi lạ mỗi lần bấm.

	Nên chỗ chặn đặt ở hai cửa sau, cả hai đều muộn hơn nhưng đều đủ sớm:

	  * `duyet()` từ chối duyệt tờ còn thiếu ô. Giám đốc không duyệt được
	    một tờ trống lý do.
	  * `truoc_khi_ghi_so` từ chối ghi sổ tờ chưa duyệt.

	Nghĩa là tờ thiếu thông tin vẫn lưu được nhưng KHÔNG ĐI ĐƯỢC TỚI ĐÂU,
	và nó nằm ngay trên màn duyệt với nhãn "Chưa ghi lý do" cho ai cũng
	thấy.

	Đơn đã huỷ mềm thì bỏ qua hết: không đụng vào một tờ đã chết.
	"""
	if not la_don_tang(doc):
		return
	if cint(doc.get("vgb_huy")):
		return

	thieu = thieu_gi(doc)

	# Hàng tặng ghi ĐỦ giá bán và thuế suất, đúng luật hàng biếu tặng: giá
	# tính thuế phải là giá bán của hàng cùng loại tại thời điểm tặng. Xoá
	# mọi khoản giảm để không ai vô tình kéo căn cứ tính thuế xuống 0.
	for o in ("additional_discount_percentage", "discount_amount", "vgb_giam_diem"):
		try:
			doc.set(o, 0)
		except Exception:
			continue

	moi = trang_thai_moi(
		doc.get("vgb_tang_duyet"), thieu,
		doc.get("vgb_tang_dau_van"), _dau_van_cua_to(doc),
	)
	if chuoi(doc.get("vgb_tang_duyet")) != moi:
		doc.vgb_tang_duyet = moi
		if moi == TT_CHO:
			# Rơi về Chờ duyệt thì XOÁ dấu cũ, không thì lần lưu sau dấu vẫn
			# lệch và đơn không bao giờ ra khỏi Chờ duyệt được nữa.
			doc.vgb_tang_dau_van = ""
			doc.vgb_tang_nguoi_duyet = None
			doc.vgb_tang_luc_duyet = None


def truoc_khi_ghi_so(doc, method=None):
	"""Hook before_submit: cửa chặn thật của luồng duyệt.

	Ba việc, theo thứ tự: chặn đơn chưa duyệt, kiểm tài khoản chi phí, rồi
	mới nối ghi chú vào từng dòng. Kiểm tài khoản TRƯỚC khi đụng vào diễn
	giải để tờ bị chặn không bị sửa dở dang.
	"""
	if not la_don_tang(doc):
		return
	if cint(doc.get("vgb_huy")):
		return

	tt = chuoi(doc.get("vgb_tang_duyet"))
	if tt == TT_TU_CHOI:
		frappe.throw(
			"Đơn hàng tặng này đã bị từ chối%s. Sửa lại đơn để xin duyệt lần "
			"nữa, hoặc đổi sang phương thức thanh toán khác."
			% ((": " + chuoi(doc.get("vgb_tang_y_kien")))
			   if chuoi(doc.get("vgb_tang_y_kien")) else ""),
			title="Đơn tặng đã bị từ chối",
		)
	if tt != TT_DUYET:
		thieu = thieu_gi(doc)
		frappe.throw(
			"Đơn hàng tặng phải được Giám đốc duyệt rồi mới ghi sổ được. Đơn "
			"đang nằm ở màn <b>Duyệt đơn hàng tặng</b> trong phân hệ Kế toán."
			+ ("<br><br>Đơn còn thiếu, giám đốc chưa duyệt được:<br>"
			   + "<br>".join("- " + THIEU[m] for m in thieu) if thieu else ""),
			title="Đơn tặng chưa được duyệt",
		)
	if can_duyet_lai(doc.get("vgb_tang_dau_van"), _dau_van_cua_to(doc)):
		frappe.throw(
			"Đơn đã bị sửa sau khi duyệt nên phải xin duyệt lại. Lưu đơn lại "
			"một lần để nó quay về hàng chờ duyệt.",
			title="Đơn tặng đã đổi ruột sau khi duyệt",
		)

	from vagabond import qua_tang_hoa_don

	# Thiếu tài khoản mà để tờ vào sổ xong mới báo thì công nợ treo trên đầu
	# khách và có khi đã bắn sang hoá đơn điện tử.
	qua_tang_hoa_don._tk_chi_phi()

	for d in (doc.get("items") or []):
		try:
			d.description = qua_tang_hoa_don.them_ghi_chu(d.get("description"))
		except Exception:
			continue


def sau_khi_ghi_so(doc, method=None):
	"""Hook on_submit: gạt công nợ để khách trả 0 đồng.

	Hoá đơn giữ nguyên giá và thuế - tiệm vẫn kê khai và nộp thuế GTGT đầu
	ra như luật hàng biếu tặng đòi. Phần khách phải trả được gạt sang chi
	phí biếu tặng bằng một bút toán riêng, có trỏ ngược về số hoá đơn.
	"""
	if not la_don_tang(doc) or cint(doc.get("vgb_huy")):
		return
	# Tờ có gắn phiếu quà VIP thì đường kia đã gạt rồi, gạt lần nữa là ghi
	# đúp chi phí. Một tờ chỉ đi một đường.
	if chuoi(doc.get("vgb_phieu_qua")):
		return
	try:
		_gat_cong_no(doc)
	except frappe.ValidationError:
		raise
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hang_tang: gat cong no")
		frappe.msgprint(
			"Đơn hàng tặng %s đã ghi sổ nhưng bút toán gạt công nợ chưa lập "
			"được. Nhờ kế toán lập tay: Nợ chi phí biếu tặng, Có phải thu "
			"khách hàng, gắn đúng số hoá đơn này." % doc.name
		)


def _gat_cong_no(si):
	"""Lập và ghi sổ bút toán gạt công nợ của một đơn hàng tặng."""
	from vagabond import qua_tang_hoa_don

	con_no = flt(si.get("outstanding_amount"))
	if con_no <= 0:
		return None
	tk_chi_phi = qua_tang_hoa_don._tk_chi_phi()
	tk_cong_no = chuoi(si.get("debit_to"))
	if not tk_cong_no:
		frappe.throw("Hoá đơn %s chưa có tài khoản phải thu." % si.name)

	dong = qua_tang_hoa_don.dong_but_toan(
		tk_chi_phi, tk_cong_no, chuoi(si.get("customer")), con_no, si.name
	)
	if not dong:
		return None

	je = frappe.get_doc({
		"doctype": "Journal Entry",
		"voucher_type": "Journal Entry",
		"company": si.get("company"),
		"posting_date": si.get("posting_date") or nowdate(),
		"user_remark": (
			"Gạt công nợ hàng tặng, hoá đơn %s. Loại tặng %s. Lý do: %s. "
			"Giám đốc duyệt: %s."
			% (si.name, NHAN_LOAI.get(chuoi(si.get("vgb_tang_loai")), "?"),
			   chuoi(si.get("vgb_tang_ly_do")),
			   chuoi(si.get("vgb_tang_nguoi_duyet")) or "?")
		),
		"accounts": dong,
	})
	je.flags.ignore_permissions = True
	je.insert(ignore_permissions=True)
	je.submit()
	try:
		frappe.db.set_value(SI, si.name, "vgb_but_toan_tang", je.name,
			update_modified=False)
	except Exception:
		pass
	return je.name


def khi_huy(doc, method=None):
	"""Hook on_cancel: huỷ bút toán gạt công nợ.

	HUỶ chứ tuyệt đối không xoá (QT-20): đây là chứng từ đã vào sổ cái.
	"""
	je = chuoi(doc.get("vgb_but_toan_tang"))
	if not je:
		return
	try:
		d = frappe.get_doc("Journal Entry", je)
		if cint(d.docstatus) == 1:
			d.flags.ignore_permissions = True
			d.cancel()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hang_tang: huy but toan")


# ------------------------------------------------------------------ cửa ngõ


def _quyen():
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()


def _thieu_tai_khoan():
	"""Đã khai Tài khoản chi phí biếu tặng chưa. CHỈ ĐỌC, không ném lỗi.

	Màn hình gọi cái này để cảnh báo TRƯỚC, thay vì để người lập đơn tặng cả
	ngày rồi tới lúc ghi sổ mới biết cả luồng đang tắc vì một ô cấu hình.
	"""
	try:
		from vagabond.lib import cfg

		tk = chuoi((cfg() or {}).get("tk_chi_phi_qua_tang"))
	except Exception:
		return 1
	return 0 if tk else 1


@frappe.whitelist()
def cai_dat():
	"""Những gì màn tính tiền cần biết để vẽ khối Hàng tặng."""
	_quyen()
	return {
		"pt": PT_TANG,
		"loai": [{"k": k, "ten": t, "can_anh": 1 if can_anh(k) else 0}
			for k, t in LOAI_TANG],
		"trang_thai": list(TT_DS),
		"thieu_tai_khoan": _thieu_tai_khoan(),
		"duyet_duoc": 1 if duoc_duyet() else 0,
		"loai_can_anh": list(LOAI_CAN_ANH),
	}


def _dinh_anh(name, anh):
	"""Đính ảnh chứng minh vào tờ hoá đơn. Trả số tệp đính được.

	Cùng nếp với `hoan_tien._dinh_kem`: hỏng một tệp không được làm đổ cả
	yêu cầu, vì phần còn lại của việc đã xong rồi.

	Để `is_private = 1`: ảnh bánh hỏng của khách và tin nhắn khách phàn nàn
	không phải thứ để ai có đường dẫn cũng xem được.
	"""
	n = 0
	for a in (anh or []):
		try:
			ten = chuoi((a or {}).get("ten")) or "anh-hang-tang.jpg"
			if not la_anh(ten):
				continue
			noi = chuoi((a or {}).get("noi_dung"))
			if "," in noi and noi[:5].lower() == "data:":
				noi = noi.split(",", 1)[1]
			if not noi:
				continue
			f = frappe.get_doc({
				"doctype": "File", "file_name": ten,
				"attached_to_doctype": SI, "attached_to_name": name,
				"content": noi, "decode": True, "is_private": 1,
			})
			f.flags.ignore_permissions = True
			f.insert(ignore_permissions=True)
			n += 1
		except Exception:
			frappe.log_error(frappe.get_traceback(), "hang_tang: dinh anh chung minh")
	return n


@frappe.whitelist()
def luu_thong_tin(name, loai=None, ly_do=None, anh=None):
	"""Người lập khai loại tặng và lý do ngay trên màn bill.

	Chỉ đụng đơn CÒN NHÁP. Đơn đã ghi sổ mà đổi lý do tặng thì bút toán và
	hoá đơn điện tử đã đi rồi, sửa ô lý do lúc đó chỉ làm sai lệch dấu vết.
	"""
	_quyen()
	si = frappe.get_doc(SI, name)
	if cint(si.docstatus) != 0:
		frappe.throw("Đơn %s đã ghi sổ, không sửa thông tin hàng tặng được." % name)
	lo = chuoi(loai)
	if lo and lo not in NHAN_LOAI:
		frappe.throw("Loại tặng %s không có trong danh sách." % lo)
	if lo:
		si.vgb_tang_loai = lo
	if ly_do is not None:
		si.vgb_tang_ly_do = chuoi(ly_do)
	si.flags.ignore_permissions = True
	si.save()
	if isinstance(anh, str):
		anh = frappe.parse_json(anh or "[]")
	them_anh = _dinh_anh(name, anh) if anh else 0
	frappe.db.commit()
	da_co = _anh_cua_to(name)
	return {
		"ok": 1,
		"trang_thai": chuoi(si.get("vgb_tang_duyet")),
		"loai": chuoi(si.get("vgb_tang_loai")),
		"ly_do": chuoi(si.get("vgb_tang_ly_do")),
		"anh_them": them_anh,
		"so_anh": len(da_co),
		"anh": da_co,
		# Nói ngay tại đây là còn thiếu gì, để màn hình khỏi phải tự đoán
		# luật. Một nơi khai luật, mọi nơi đọc lại.
		"thieu": thieu_gi(si, so_anh=len(da_co)),
		"cau_thieu": [THIEU[m] for m in thieu_gi(si, so_anh=len(da_co))],
	}


@frappe.whitelist()
def dem_cho_duyet():
	"""Số đơn tặng đang chờ duyệt, và bao nhiêu cái chờ quá hạn.

	Trang chủ gọi để chấm số đỏ lên ô Duyệt đơn hàng tặng. Chỉ đếm, không
	trả nội dung đơn nào, nên ai vào trang chủ cũng gọi được.
	"""
	_quyen()
	try:
		ds = frappe.get_all(
			SI,
			filters={
				"docstatus": 0, "vgb_huy": 0,
				"vgb_pt_thanh_toan": PT_TANG,
				"vgb_tang_duyet": TT_CHO,
			},
			fields=["name", "creation"],
			limit_page_length=0,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hang_tang: dem cho duyet")
		return {"cho": 0, "qua_han": 0}
	hom_nay = nowdate()
	qua = 0
	for d in ds:
		_so_ngay, keu = cho_bao_lau(TT_CHO, d.get("creation"), hom_nay)
		if keu:
			qua += 1
	return {"cho": len(ds), "qua_han": qua, "nguong": CHO_NGAY}


def _diem_cua_don(quay):
	from vagabond import diem_ban

	try:
		return diem_ban.ma_theo_quay(chuoi(quay))
	except Exception:
		return ""


def _ten_diem():
	from vagabond import diem_ban

	try:
		return [{"k": d["ma"], "ten": d["ten"]} for d in diem_ban.ds()]
	except Exception:
		return []


@frappe.whitelist()
def ds_don(diem="", trang_thai="", loai="", tim="", so_dong=200):
	"""Danh sách đơn hàng tặng cho màn duyệt.

	BA HỌ CHIP: điểm bán, trạng thái duyệt, loại tặng. Mỗi họ đếm trên tập
	đã lọc bởi hai họ kia, để bấm một chip xong thì số trên các chip còn lại
	vẫn nói đúng "bấm thêm cái này thì còn bao nhiêu".

	Ô tìm chạy Ở MÁY CHỦ (QT-19): `or_filters` ở tầng cơ sở dữ liệu, không
	đọc N dòng về rồi lọc bằng Python. Phép cắt dòng làm ở bước CUỐI, sau
	khi đã lọc và đã đếm xong.
	"""
	_quyen()
	loc = {"vgb_pt_thanh_toan": PT_TANG, "docstatus": ["<", 2]}
	tt = chuoi(trang_thai)
	if tt in TT_DS:
		loc["vgb_tang_duyet"] = tt
	hoac = dieu_kien_tim(tim, TRUONG_TIM)

	dong = frappe.get_all(
		SI,
		filters=loc, or_filters=hoac,
		fields=[
			"name", "creation", "owner", "docstatus", "posting_date",
			"grand_total", "total_qty", "customer", "customer_name",
			"custom_nguon", "custom_pancake_display_id", "vgb_quay",
			"vgb_huy", "vgb_ghi_chu", "vgb_tang_loai", "vgb_tang_ly_do",
			"vgb_tang_duyet", "vgb_tang_nguoi_duyet", "vgb_tang_luc_duyet",
			"vgb_tang_y_kien", "vgb_but_toan_tang",
			# So hoa don dien tu da xuat cho don nay. Anh Viet 02/09/2026:
			# duyet xong con phai doi chieu voi to hoa don that, ma di tra
			# cuu o man khac thi mat luot.
			"custom_hddt_so", "custom_hddt_trang_thai",
		],
		order_by="creation desc",
		limit_page_length=0,
	)

	hom_nay = nowdate()
	for d in dong:
		d["diem_ban"] = _diem_cua_don(d.get("vgb_quay"))
		d["nhan_loai"] = NHAN_LOAI.get(chuoi(d.get("vgb_tang_loai")), "Chưa chọn")
		d["da_ghi_so"] = 1 if cint(d.get("docstatus")) == 1 else 0
		so_ngay, keu = cho_bao_lau(d.get("vgb_tang_duyet"), d.get("creation"), hom_nay)
		d["cho_ngay"] = so_ngay
		d["cho_lau"] = 1 if keu else 0
		d["creation"] = str(d.get("creation") or "")[:16]
		d["vgb_tang_luc_duyet"] = str(d.get("vgb_tang_luc_duyet") or "")[:16]

	# Hien TEN nguoi chu khong hien dia chi thu, doi mot luot cho ca trang.
	# Anh Viet chot 02/09/2026, xem `vagabond/ten_nguoi.py`.
	ten_nguoi.gan(dong, "owner", "vgb_tang_nguoi_duyet")

	dm = chuoi(diem).upper()
	lo = chuoi(loai)
	hop = lambda r: ((not dm or r["diem_ban"] == dm)
		and (not lo or chuoi(r.get("vgb_tang_loai")) == lo))

	dem_diem, dem_tt, dem_loai = {}, {}, {}
	for r in dong:
		if not lo or chuoi(r.get("vgb_tang_loai")) == lo:
			k = r["diem_ban"] or "?"
			dem_diem[k] = dem_diem.get(k, 0) + 1
			dem_diem["tat_ca"] = dem_diem.get("tat_ca", 0) + 1
		if hop(r):
			k = chuoi(r.get("vgb_tang_duyet")) or TT_CHO
			dem_tt[k] = dem_tt.get(k, 0) + 1
			dem_tt["tat_ca"] = dem_tt.get("tat_ca", 0) + 1
		if not dm or r["diem_ban"] == dm:
			k = chuoi(r.get("vgb_tang_loai")) or "khac"
			dem_loai[k] = dem_loai.get(k, 0) + 1
			dem_loai["tat_ca"] = dem_loai.get("tat_ca", 0) + 1

	ra = [r for r in dong if hop(r)]
	# Đơn chờ quá hạn lên đầu: đó là thứ người mở màn cần thấy trước.
	ra.sort(key=lambda r: (0 if r["cho_lau"] else 1, r["creation"]), reverse=False)
	ra.sort(key=lambda r: 0 if r["cho_lau"] else 1)

	tran = max(1, min(int(so_dong or 200), 500))
	return {
		"dong": ra[:tran],
		"tong_dong": len(ra),
		"con_nua": 1 if len(ra) > tran else 0,
		"diem": _ten_diem(),
		"loai": [{"k": k, "ten": t} for k, t in LOAI_TANG],
		"loai_can_anh": list(LOAI_CAN_ANH),
		"trang_thai": list(TT_DS),
		"dem_diem": dem_diem,
		"dem": dem_tt,
		"dem_loai": dem_loai,
		"tien_cho": sum(flt(r["grand_total"]) for r in ra
			if chuoi(r.get("vgb_tang_duyet")) == TT_CHO),
		"tien_duyet": sum(flt(r["grand_total"]) for r in ra
			if chuoi(r.get("vgb_tang_duyet")) == TT_DUYET),
		"duyet_duoc": 1 if duoc_duyet() else 0,
		"thieu_tai_khoan": _thieu_tai_khoan(),
		"nguong_cho": CHO_NGAY,
	}


@frappe.whitelist()
def chi_tiet(name):
	"""Từng dòng hàng của một đơn tặng, để giám đốc biết mình đang duyệt gì.

	Duyệt mà không thấy món thì chỉ là bấm một cái nút. Đây là màn duyệt
	chứ không phải màn xác nhận.
	"""
	_quyen()
	d = frappe.db.get_value(
		SI, name,
		["name", "customer_name", "grand_total", "vgb_tang_loai",
		 "vgb_tang_ly_do", "vgb_tang_duyet", "vgb_tang_y_kien", "owner",
		 "vgb_quay", "custom_nguon", "custom_pancake_display_id", "creation",
		 "custom_hddt_so", "custom_hddt_trang_thai", "custom_hddt_sobaomat",
		 "vgb_tang_nguoi_duyet"],
		as_dict=True,
	)
	if not d:
		frappe.throw("Không tìm thấy đơn %s." % name)
	mon = frappe.get_all(
		"Sales Invoice Item",
		filters={"parent": name, "parenttype": SI},
		fields=["item_code", "item_name", "qty", "rate", "amount"],
		order_by="idx asc", limit_page_length=0,
	)
	d = dict(d)
	d["mon"] = mon
	d["anh"] = _anh_cua_to(name)
	d["can_anh"] = 1 if can_anh(d.get("vgb_tang_loai")) else 0
	d["nhan_loai"] = NHAN_LOAI.get(chuoi(d.get("vgb_tang_loai")), "Chưa chọn")
	d["creation"] = str(d.get("creation") or "")[:16]
	# Người lập này đã tặng bao nhiêu trong tháng. Con số để giám đốc nhìn
	# trước khi bấm duyệt, không phải hàng rào cứng: đặt hạn mức bao nhiêu
	# là quyết định của anh Việt, máy không tự đặt hộ.
	d["thang_nay"] = _da_tang_thang(d.get("owner"))
	ten_nguoi.gan(d, "owner", "vgb_tang_nguoi_duyet")
	return d


def _da_tang_thang(nguoi):
	"""Tổng tiền hàng tặng người này đã lập trong tháng, kể cả chưa duyệt."""
	nguoi = chuoi(nguoi)
	if not nguoi:
		return {"so": 0, "tien": 0.0}
	try:
		dau = nowdate()[:8] + "01"
		ds = frappe.get_all(
			SI,
			filters={
				"owner": nguoi, "vgb_pt_thanh_toan": PT_TANG,
				"posting_date": [">=", dau], "docstatus": ["<", 2],
				"vgb_huy": 0,
			},
			fields=["grand_total"], limit_page_length=0,
		)
	except Exception:
		return {"so": 0, "tien": 0.0}
	return {"so": len(ds), "tien": sum(flt(r["grand_total"]) for r in ds)}


def _ghi_vet(si, viec):
	try:
		frappe.get_doc({
			"doctype": "Comment", "comment_type": "Info",
			"reference_doctype": SI, "reference_name": si,
			"content": "%s - %s" % (viec, frappe.session.user),
		}).insert(ignore_permissions=True)
	except Exception:
		pass


@frappe.whitelist()
def duyet(name, y_kien=""):
	"""Giám đốc duyệt một đơn hàng tặng.

	Ghi lại DẤU VÂN của đơn ngay lúc duyệt. Sửa ruột sau đó là đơn tự rơi
	về Chờ duyệt, xem `truoc_khi_luu`.
	"""
	_quyen()
	_chan_neu_khong_duyet()
	si = frappe.get_doc(SI, name)
	if not la_don_tang(si):
		frappe.throw("Đơn %s không trả bằng %s nên không nằm trong luồng duyệt."
			% (name, PT_TANG))
	if cint(si.docstatus) != 0:
		frappe.throw("Đơn %s đã ghi sổ hoặc đã huỷ, không duyệt lại được." % name)
	if cint(si.get("vgb_huy")):
		frappe.throw("Đơn %s đã huỷ." % name)
	thieu = thieu_gi(si, so_anh=len(_anh_cua_to(name)))
	if thieu:
		frappe.throw(
			"<br>".join("- " + THIEU[m] for m in thieu),
			title="Đơn còn thiếu thông tin, chưa duyệt được",
		)

	frappe.db.set_value(SI, name, {
		"vgb_tang_duyet": TT_DUYET,
		"vgb_tang_nguoi_duyet": frappe.session.user,
		"vgb_tang_luc_duyet": now_datetime(),
		"vgb_tang_y_kien": chuoi(y_kien),
		"vgb_tang_dau_van": _dau_van_cua_to(si),
	}, update_modified=False)
	frappe.db.commit()
	_ghi_vet(name, "Duyệt đơn hàng tặng %s đ%s" % (
		"{:,.0f}".format(flt(si.grand_total)),
		(", ý kiến: " + chuoi(y_kien)) if chuoi(y_kien) else ""))
	return {"ok": 1, "trang_thai": TT_DUYET}


@frappe.whitelist()
def tu_choi(name, ly_do=""):
	"""Giám đốc từ chối một đơn hàng tặng. BẮT BUỘC nêu lý do.

	Không cho từ chối trống: người lập đơn phải biết sửa gì, không thì họ
	lập lại y hệt và cả hai bên cùng mất thời gian.
	"""
	_quyen()
	_chan_neu_khong_duyet()
	ly = chuoi(ly_do)
	if len(ly) < 5:
		frappe.throw(
			"Từ chối thì phải ghi lý do, để người lập biết đường sửa. "
			"Ví dụ: đơn quá lớn, tặng sai đối tượng, chưa có ai đồng ý.",
			title="Thiếu lý do từ chối",
		)
	si = frappe.get_doc(SI, name)
	if not la_don_tang(si):
		frappe.throw("Đơn %s không trả bằng %s." % (name, PT_TANG))
	if cint(si.docstatus) != 0:
		frappe.throw("Đơn %s đã ghi sổ hoặc đã huỷ." % name)

	frappe.db.set_value(SI, name, {
		"vgb_tang_duyet": TT_TU_CHOI,
		"vgb_tang_nguoi_duyet": frappe.session.user,
		"vgb_tang_luc_duyet": now_datetime(),
		"vgb_tang_y_kien": ly,
		"vgb_tang_dau_van": "",
	}, update_modified=False)
	frappe.db.commit()
	_ghi_vet(name, "Từ chối đơn hàng tặng: %s" % ly)
	return {"ok": 1, "trang_thai": TT_TU_CHOI}


# ------------------------------------------------------------------ báo cáo


def gom_bao_cao(dong, ten_diem=None):
	"""Cộng hàng tặng theo tháng, theo điểm bán, theo loại tặng. THUẦN.

	`dong` là danh sách tự điển: {thang, diem, loai, tien, da_ghi_so}.

	Vì sao là phần thuần: đây là phép cộng, mà phép cộng sai thì không ai
	nhìn ra bằng mắt. Tách ra để kiểm thử được không cần site.

	CHỈ cộng đơn ĐÃ GHI SỔ. Đơn còn chờ duyệt chưa phải chi phí của tiệm,
	gộp vào là báo cáo phồng lên bằng những thứ có thể bị từ chối.
	"""
	thang, diem, loai = {}, {}, {}
	tong, so = 0.0, 0
	for d in (dong or []):
		if not int((d or {}).get("da_ghi_so") or 0):
			continue
		t = float((d or {}).get("tien") or 0)
		tong += t
		so += 1
		for bang, khoa in ((thang, "thang"), (diem, "diem"), (loai, "loai")):
			k = chuoi((d or {}).get(khoa)) or "?"
			o = bang.setdefault(k, {"k": k, "so": 0, "tien": 0.0})
			o["so"] += 1
			o["tien"] += t
	sap = lambda b, theo_khoa: sorted(
		b.values(), key=(lambda o: o["k"]) if theo_khoa else (lambda o: -o["tien"]))
	ra_loai = sap(loai, False)
	for o in ra_loai:
		o["ten"] = NHAN_LOAI.get(o["k"], o["k"])
	ra_diem = sap(diem, False)
	for o in ra_diem:
		o["ten"] = (ten_diem or {}).get(o["k"], o["k"] or "Chưa rõ điểm bán")
	return {
		"so": so, "tien": tong,
		"thang": sap(thang, True),
		"diem": ra_diem,
		"loai": ra_loai,
	}


@frappe.whitelist()
def bao_cao(tu_ngay=None, den_ngay=None):
	"""Tiệm đã tặng đi bao nhiêu, cho việc gì, ở điểm bán nào.

	Anh Việt duyệt 31/08/2026. Mặc định lấy từ đầu năm tới hôm nay: hàng
	tặng là con số cả năm mới nói lên chuyện, xem theo tuần thì tháng nào
	cũng thấy nhỏ.
	"""
	_quyen()
	den = chuoi(den_ngay) or nowdate()
	tu = chuoi(tu_ngay) or (den[:4] + "-01-01")
	ds = frappe.get_all(
		SI,
		filters={
			"vgb_pt_thanh_toan": PT_TANG,
			"posting_date": ["between", [tu, den]],
			"docstatus": ["<", 2],
			"vgb_huy": 0,
		},
		fields=["name", "posting_date", "docstatus", "grand_total",
			"vgb_tang_loai", "vgb_quay"],
		limit_page_length=0,
	)
	dong = [{
		"thang": str(d.get("posting_date") or "")[:7],
		"diem": _diem_cua_don(d.get("vgb_quay")),
		"loai": chuoi(d.get("vgb_tang_loai")),
		"tien": flt(d.get("grand_total")),
		"da_ghi_so": 1 if cint(d.get("docstatus")) == 1 else 0,
	} for d in ds]
	ten = {x["k"]: x["ten"] for x in _ten_diem()}
	ra = gom_bao_cao(dong, ten)
	ra["tu_ngay"] = tu
	ra["den_ngay"] = den
	# Đơn chưa ghi sổ đếm riêng, không cộng vào báo cáo. Người đọc vẫn cần
	# biết còn bao nhiêu đang treo, nhưng không được lẫn vào con số chi phí.
	ra["cho_so"] = sum(1 for d in dong if not d["da_ghi_so"])
	ra["cho_tien"] = sum(d["tien"] for d in dong if not d["da_ghi_so"])
	return ra

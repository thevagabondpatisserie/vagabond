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

CODEX REVIEW PR #197, ĐÃ SỬA
=============================
Bản đầu của tệp này có ba lỗ thật, Codex bắt được hết, ghi lại đây để bản
sau đừng làm lại:

  1. Lọc chứng từ thu bằng `unallocated_amount > 0` và cộng chính con số
     đó. Sai hai lần: chứng từ thu chuẩn tạo từ phiếu đặt thì tiền nằm
     trong dòng tham chiếu, gán đủ xong `unallocated_amount` về 0 nên bị
     loại sạch; và con số ấy còn ĐỔI về sau khi khoản ứng được cấn vào
     hoá đơn, nên không dùng làm số lịch sử của ca được. Xem `tien_thuc_thu`.
  2. Truy vấn không bắt buộc dấu hiệu nào của luồng đặt bánh, nên mọi
     khoản khách nộp thừa ở quầy đều bị cộng nhầm vào ca.
  3. `dem_giu_cho` nuốt lỗi rồi trả về rỗng. Bên gọi hiểu rỗng là "không
     còn ai đặt" và ghi 0 vào mọi dòng, tức là một lỗi cơ sở dữ liệu tạm
     thời sẽ GIẢI PHÓNG toàn bộ bánh đã giữ cho khách. Nay để lỗi nổi lên,
     bên gọi giữ nguyên số cũ.
"""

# ------------------------------------------------------------ phần thuần
#
# Không chạm Frappe, và cố ý KHÔNG dùng cả `frappe.utils`, để chạy được
# trong môi trường không có khung. Vì vậy phần này nhận tiền tố mã bánh
# qua tham số chứ không tự đi lấy: đi lấy là phải nạp `kiem_banh`, mà nạp
# `kiem_banh` là kéo theo Frappe.

PT_TRA_TRUOC = "Trả trước"

SO = "Sales Order"
PE = "Payment Entry"


def _so_nguyen(x):
	try:
		return int(float(x or 0))
	except (TypeError, ValueError):
		return 0


def _so_thuc(x):
	try:
		return float(x or 0)
	except (TypeError, ValueError):
		return 0.0


def la_banh_o(ma, tien_to):
	"""Mã hàng này có phải bánh ổ không. THUẦN.

	`tien_to` do bên gọi truyền vào, chính là `kiem_banh.TIEN_TO_MA`. Không
	gõ lại chuỗi ở đây để hai nơi không bao giờ nói khác nhau (QT-19).
	"""
	return str(ma or "").upper().startswith(tuple(tien_to or ()))


def con_giu_cho(so_dat, da_giao, da_xuat_hoa_don):
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
	q = _so_nguyen(so_dat)
	if q <= 0:
		return 0
	xong = max(_so_nguyen(da_giao), _so_nguyen(da_xuat_hoa_don))
	return max(0, min(q, q - xong))


def gom_giu_cho(dong, tien_to):
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
		if not la_banh_o(ma, tien_to):
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


def ngay_nhan_cua_phieu(dong, tien_to):
	"""Mọi ngày nhận bánh ổ có trong một phiếu đặt. THUẦN.

	Hook đổi phiếu cần danh sách này của CẢ bản cũ lẫn bản mới. Một phiếu
	có thể có nhiều dòng nhiều ngày khác nhau, đo mỗi ngày đầu tiên là bỏ
	sót phần còn lại.

	Khác `gom_giu_cho` ở chỗ KHÔNG bỏ dòng đã giao xong: dòng vừa giao
	xong chính là dòng phải đo lại để nhả số giữ chỗ ra.
	"""
	ra = []
	for d in dong or []:
		if not isinstance(d, dict):
			continue
		if not la_banh_o(d.get("item_code"), tien_to):
			continue
		ngay = str(d.get("delivery_date") or "").strip()[:10]
		if ngay and ngay not in ra:
			ra.append(ngay)
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


def gop_ngay(*danh_sach):
	"""Gộp nhiều danh sách ngày thành một, bỏ rỗng và bỏ trùng. THUẦN."""
	ra = []
	for ds in danh_sach:
		for n in ds or []:
			n = str(n or "").strip()[:10]
			if n and n not in ra:
				ra.append(n)
	return ra


def thieu_o_bat_buoc(phieu):
	"""Chứng từ thu của luồng đặt bánh còn THIẾU ô nào. THUẦN.

	Trả về danh sách nhãn ô thiếu, rỗng nghĩa là đủ.
	"""
	ra = []
	if not str((phieu or {}).get("vgb_phieu_dat") or "").strip():
		ra.append("Phiếu đặt bánh")
	if not str((phieu or {}).get("vgb_quay") or "").strip():
		ra.append("Quầy thu tiền")
	return ra


def tham_chieu_la(ds_tham_chieu):
	"""Các loại chứng từ mà một phiếu thu đang trỏ tới. THUẦN."""
	ra = []
	for r in ds_tham_chieu or []:
		if not isinstance(r, dict):
			continue
		t = str(r.get("reference_doctype") or "").strip()
		if t and t not in ra:
			ra.append(t)
	return ra


def la_phieu_dat_banh(phieu, ds_tham_chieu):
	"""Phiếu thu này có thuộc luồng đặt bánh không. THUẦN.

	Nhận diện RỘNG, cố ý: có ô phiếu đặt, hoặc có trỏ tới một phiếu đặt.
	Rộng để cái hàng rào dưới không bỏ sót phiếu nào; còn phiếu nào ĐƯỢC
	CỘNG vào ca thì `thu_ung_truoc` đòi chặt hơn nhiều.
	"""
	if str((phieu or {}).get("vgb_phieu_dat") or "").strip():
		return True
	return SO in tham_chieu_la(ds_tham_chieu)


def phieu_dat_duoc_tro(ds_tham_chieu):
	"""Các phiếu đặt mà một chứng từ thu đang trỏ tới. THUẦN."""
	ra = []
	for r in ds_tham_chieu or []:
		if not isinstance(r, dict):
			continue
		if str(r.get("reference_doctype") or "").strip() != SO:
			continue
		ten = str(r.get("reference_name") or "").strip()
		if ten and ten not in ra:
			ra.append(ten)
	return ra


def loi_phieu_dat_banh(phieu, ds_tham_chieu):
	"""Câu báo lỗi cho một phiếu thu đặt bánh sai. THUẦN. None là hợp lệ.

	BỐN HÀNG RÀO, và vì sao cần đủ bốn (Codex bắt dần qua ba vòng PR #197):

	  1. Thiếu một trong hai ô thì phiếu KHÔNG BAO GIỜ vào được ca nào cả,
	     vì `thu_ung_truoc` lọc theo quầy ngay ở truy vấn đầu. Không chặn
	     thì tiền thật im lặng biến mất khỏi mọi bảng đối soát. Đây đúng là
	     lỗi mà bản trước của em mắc: em nói có đỡ đường tạo phiếu thu thẳng
	     từ Desk, nhưng đường đó không có ô quầy nên bị loại ngay từ đầu, và
	     ca kiểm của em xanh giả vì tự gán sẵn ô quầy cho nó.

	  2. Trỏ tới cả hoá đơn bán thì ĐẾM HAI LẦN: cả số tiền được cộng vào
	     đường ứng trước, trong khi tờ hoá đơn kia đã được đếm ở đường
	     thường. Một phiếu thu đặt bánh chỉ được trỏ tới phiếu đặt.

	  3. Có ô phiếu đặt mà KHÔNG có dòng tham chiếu nào, hoặc dòng tham
	     chiếu trỏ tới một phiếu đặt KHÁC với ô đã ghi. Ô chỉ đọc là ghi
	     chú, còn thứ ERPNext dùng để cấn tiền vào ngày giao là bảng tham
	     chiếu. Hai cái lệch nhau thì ca vẫn cộng đủ tiền, nhưng tới ngày
	     giao máy không có đường cấn đúng, hoặc cấn nhầm sang đơn khác.

	  4. Trỏ tới nhiều phiếu đặt cùng lúc thì không biết số tiền thuộc về
	     đơn nào. Bản đầu tiên giữ nguyên tắc một phiếu thu cho một phiếu
	     đặt, dễ đối chiếu và dễ huỷ khi khách đổi ý.

	Câu báo lỗi nói rõ làm gì tiếp, theo QT-24.
	"""
	thieu = thieu_o_bat_buoc(phieu)
	if thieu:
		return (
			"Phiếu thu tiền đặt bánh còn thiếu ô %s. Khoản này phải được tạo "
			"từ màn đặt bánh chứ không tạo tay, vì màn đó mới điền được quầy "
			"thu và số phiếu đặt. Thiếu một trong hai ô thì tiền không vào "
			"được ca nào, chốt ca sẽ thiếu đúng số tiền này. Anh chị huỷ "
			"phiếu này rồi thu lại trên màn đặt bánh."
			% " và ".join(thieu)
		)
	la = [t for t in tham_chieu_la(ds_tham_chieu) if t != SO]
	if la:
		return (
			"Phiếu thu tiền đặt bánh đang trỏ tới cả %s. Một phiếu thu đặt "
			"bánh chỉ được trỏ tới phiếu đặt, vì tiền của hoá đơn đã được "
			"đếm ở đường thường rồi, để chung là chốt ca đếm số tiền này hai "
			"lần. Anh chị tách ra thành hai phiếu thu riêng."
			% ", ".join(la)
		)
	tro = phieu_dat_duoc_tro(ds_tham_chieu)
	o = str((phieu or {}).get("vgb_phieu_dat") or "").strip()
	if not tro:
		return (
			"Phiếu thu tiền đặt bánh ghi phiếu đặt %s ở ô ghi chú nhưng chưa "
			"gắn phiếu đặt đó vào bảng tham chiếu. Máy dùng bảng tham chiếu "
			"để cấn tiền vào ngày giao, không dùng ô ghi chú, nên để vậy thì "
			"tới ngày giao khoản này không trừ được vào đơn của khách. Anh "
			"chị huỷ phiếu này rồi thu lại trên màn đặt bánh." % o
		)
	if len(tro) > 1:
		return (
			"Phiếu thu tiền đặt bánh đang gắn %d phiếu đặt cùng lúc (%s). Mỗi "
			"phiếu thu chỉ được gắn một phiếu đặt, không thì không biết tiền "
			"thuộc đơn nào và khách huỷ một đơn là không tách ra được. Anh "
			"chị thu riêng từng đơn." % (len(tro), ", ".join(tro))
		)
	if tro[0] != o:
		return (
			"Phiếu thu tiền đặt bánh ghi phiếu đặt %s ở ô ghi chú nhưng lại "
			"gắn vào phiếu đặt %s. Hai chỗ lệch nhau thì tới ngày giao tiền "
			"sẽ cấn nhầm sang đơn của khách khác. Anh chị huỷ phiếu này rồi "
			"thu lại trên màn đặt bánh." % (o, tro[0])
		)
	return None


def loi_khach_khong_khop(khach_phieu_thu, khach_phieu_dat, phieu_dat):
	"""Khách trên phiếu thu phải trùng khách trên phiếu đặt. THUẦN.

	Không trùng nghĩa là đang thu tiền của người này ghi vào đơn của người
	kia. Ngày giao, đơn của khách A hiện đã trả đủ nhờ tiền của khách B.
	"""
	a = str(khach_phieu_thu or "").strip()
	b = str(khach_phieu_dat or "").strip()
	if not a or not b or a == b:
		return None
	return (
		"Phiếu thu đang đứng tên khách %s nhưng phiếu đặt %s là của khách "
		"%s. Thu tiền của khách này ghi vào đơn của khách kia thì tới ngày "
		"giao đơn kia hiện là đã trả đủ. Anh chị kiểm lại tên khách, hoặc "
		"thu lại trên màn đặt bánh của đúng đơn." % (a, phieu_dat, b)
	)


def tien_thuc_thu(phieu):
	"""Số tiền THẬT SỰ vào của một chứng từ thu. THUẦN.

	VÌ SAO KHÔNG DÙNG `unallocated_amount`, Codex bắt ở PR #197:

	  - Chứng từ thu tạo đúng cách từ phiếu đặt có dòng tham chiếu trỏ về
	    phiếu đó. Gán đủ xong thì `unallocated_amount` bằng 0, tức là mọi
	    khoản trả trước CHUẨN đều bị loại khỏi ca.
	  - Con số ấy còn đổi về sau, lúc khoản ứng được cấn vào hoá đơn ngày
	    giao. Ca của ngày thu là số lịch sử, không được phép đổi theo một
	    việc xảy ra ở ngày khác.

	`received_amount` là số vào tài khoản nhận. Chứng từ cùng loại tiền
	thì bằng `paid_amount`, nên lấy `paid_amount` bù khi ô kia trống.
	"""
	so = _so_thuc((phieu or {}).get("received_amount"))
	if so <= 0:
		so = _so_thuc((phieu or {}).get("paid_amount"))
	return so


def tong_ung_truoc(ds_thu):
	"""Gom chứng từ thu ứng trước thành {phương thức: số tiền}. THUẦN.

	Bỏ dòng số tiền không dương: chứng từ âm là dấu hiệu gõ nhầm, cộng vào
	là tự làm lệch ca theo chiều ngược lại.
	"""
	ra = {}
	for r in ds_thu or []:
		if not isinstance(r, dict):
			continue
		so = _so_thuc(r.get("so_tien"))
		if so <= 0:
			continue
		pt = str(r.get("pt") or "").strip() or "Chưa rõ"
		ra[pt] = ra.get(pt, 0.0) + so
	return ra


# ------------------------------------------------------------- chạm Frappe

import frappe  # noqa: E402
from frappe.utils import getdate  # noqa: E402

from vagabond.kiem_banh import TIEN_TO_MA  # noqa: E402

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
	"""Số bánh ổ đang được giữ chỗ cho MỘT ngày nhận. {mã hàng: số}.

	CỐ Ý KHÔNG BẮT LỖI. Bản đầu bắt lỗi rồi trả về rỗng, và bên gọi hiểu
	rỗng là "không còn ai đặt" nên ghi 0 vào mọi dòng. Nghĩa là một trục
	trặc cơ sở dữ liệu vài giây sẽ nhả toàn bộ bánh đã giữ của khách ra
	bán tiếp, không ai hay. Codex bắt đúng ở PR #197.

	Bên gọi chịu trách nhiệm bắt lỗi và GIỮ NGUYÊN số cũ.
	"""
	dong = dong_phieu_dat(ngay)
	gom = gom_giu_cho(
		[dict(d, delivery_date=str(d.get("delivery_date") or "")) for d in dong],
		TIEN_TO_MA,
	)
	return gom.get(str(getdate(ngay)), {})


def ngay_nhan_cua(doc):
	"""Mọi ngày nhận bánh ổ của một phiếu đặt (bản doc hoặc dict)."""
	if not doc:
		return []
	dong = doc.get("items") if hasattr(doc, "get") else None
	ra = []
	for d in dong or []:
		ra.append({
			"item_code": d.get("item_code") if hasattr(d, "get") else getattr(d, "item_code", None),
			"delivery_date": d.get("delivery_date") if hasattr(d, "get") else getattr(d, "delivery_date", None),
		})
	return ngay_nhan_cua_phieu(ra, TIEN_TO_MA)


def thu_ung_truoc(quay, tu_luc, den_luc, theo_ngay=False):
	"""Tiền khách trả TRƯỚC đã vào trong khoảng ca, theo từng phương thức.

	Đây là nửa còn thiếu của màn Chốt ca. Không có hàm này thì ngày khách
	đặt bánh và trả tiền, két thừa đúng bằng số tiền đó mà không dòng nào
	trên bảng đối soát giải thích được.

	`theo_ngay` đi theo đúng quy ước của `_doanh_thu_he_thong`: điểm có
	quầy lọc theo giờ tạo, điểm không quầy lọc theo ngày chứng từ. Truyền
	sai mốc thì một ca mở 8h sẽ nuốt cả tiền của hôm qua.

	Không đếm hai lần: ngày thu chưa có hoá đơn nào của phiếu này, còn hoá
	đơn ngày giao mang phương thức "Trả trước" nên đã rơi khỏi bảng đối
	soát ở `ca_quay._ngoai_ket`.
	"""
	loc = {
		"docstatus": 1,
		"payment_type": "Receive",
		"party_type": "Customer",
		"vgb_quay": str(quay or "").strip().upper(),
		# Đòi CÓ ô phiếu đặt, không nhận đường vòng nào khác.
		#
		# Bản trước em còn một cửa phụ: phiếu không có ô này nhưng có dòng
		# trỏ tới phiếu đặt thì vẫn nhận, để đỡ đường kế toán tạo thẳng bên
		# Desk. Codex bắt đúng là cửa đó KHÔNG BAO GIỜ MỞ: truy vấn này lọc
		# theo quầy trước, mà phiếu tạo bên Desk không có ai điền ô quầy,
		# nên nó bị loại ngay và dòng tham chiếu chẳng được đọc tới. Ca kiểm
		# của em xanh giả vì tự gán sẵn ô quầy cho chính cái phiếu mà em bảo
		# là không có ô đó.
		#
		# Nay hợp đồng gọn lại đúng một đường: mọi phiếu thu tiền đặt bánh
		# phải có CẢ ô quầy lẫn ô phiếu đặt, và `chan_phieu_dat_banh` chặn
		# ngay lúc ghi sổ nếu thiếu. Thà không cho ghi sổ còn hơn cho ghi sổ
		# rồi tiền im lặng biến mất khỏi mọi bảng đối soát.
		"vgb_phieu_dat": ["is", "set"],
	}
	if theo_ngay:
		loc["posting_date"] = ["between", [str(getdate(tu_luc)), str(getdate(den_luc))]]
	else:
		loc["creation"] = ["between", [str(tu_luc), str(den_luc)]]
	ds = frappe.get_all(
		PE,
		filters=loc,
		fields=["name", "mode_of_payment", "received_amount", "paid_amount"],
		limit_page_length=0,
	)
	return tong_ung_truoc([
		{"pt": r.get("mode_of_payment"), "so_tien": tien_thuc_thu(r)}
		for r in ds
	])


def chan_phieu_dat_banh(doc, method=None):
	"""Hook Payment Entry: chặn ghi sổ phiếu thu đặt bánh khai sai.

	Chỉ đụng tới phiếu của luồng đặt bánh, phiếu thu chi khác đi qua không
	vướng gì. Chặn ở máy chủ chứ không tin ô chỉ đọc trên giao diện, vì ô
	chỉ đọc chặn được người gõ chứ không chặn được đường tạo bằng mã.
	"""
	tc = []
	for r in (doc.get("references") or []):
		lay = (lambda k: r.get(k)) if hasattr(r, "get") else (lambda k: getattr(r, k, None))
		tc.append({
			"reference_doctype": lay("reference_doctype"),
			"reference_name": lay("reference_name"),
		})
	o = {
		"vgb_phieu_dat": doc.get("vgb_phieu_dat"),
		"vgb_quay": doc.get("vgb_quay"),
	}
	if not la_phieu_dat_banh(o, tc):
		return
	loi = loi_phieu_dat_banh(o, tc)
	if loi:
		frappe.throw(loi)
	# Tới đây chắc chắn có đúng một phiếu đặt và nó khớp ô ghi chú. Còn một
	# thứ chỉ hỏi cơ sở dữ liệu mới biết: phiếu đặt đó có đúng của khách này
	# không. Thu tiền của khách này ghi vào đơn của khách kia là kiểu sai
	# không cách nào tự lộ ra, cho tới ngày giao.
	ten_phieu_dat = str(o["vgb_phieu_dat"]).strip()
	khach_dat = frappe.db.get_value(SO, ten_phieu_dat, "customer")
	loi = loi_khach_khong_khop(doc.get("party"), khach_dat, ten_phieu_dat)
	if loi:
		frappe.throw(loi)
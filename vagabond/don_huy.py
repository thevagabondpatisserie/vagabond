"""Đơn Pancake ĐÃ HUỶ mà tiền khách vẫn còn nằm ở công ty.

Việc thật, anh Việt giao 21/08/2026 kèm ảnh ba đơn: 92252 (705.000 đ,
Ms.Như Duyên), 92245 (920.000 đ, Mr.Khoa Lê), 92156 (750.000 đ, Ms.Vi Aibi).

VÌ SAO PHẢI CÓ MÀN RIÊNG, KHÔNG DÙNG LẠI MÀN CŨ
-----------------------------------------------
Nút "Huỷ đơn và hoàn tiền" của v259 treo trên THẺ ĐƠN NHÁP, nên nó chỉ với
tới đúng một ca hẹp: đơn giao trong ngày, đã đồng bộ thành hoá đơn nháp, rồi
khách mới huỷ. Ba đơn anh Việt gửi không thuộc ca đó.

Lý do nằm ở hai tầng lọc của luồng đồng bộ, ghi trong
`claude/lo-hong-huy-don-khong-ve-he.md`:

- `ban_hang.TT_DOANH_SO = {3, 16}`: chỉ đơn đã nhận hoặc đã thu tiền mới
  thành Sales Invoice. Đơn huỷ mang trạng thái 6, không bao giờ lọt.
- Khung quét là NGÀY GIAO chứ không phải ngày đặt. Khách đặt hôm nay giao
  thứ Bảy rồi huỷ ngay chiều nay thì hôm nay đơn còn chưa vào khung quét.

Ghép lại: **những đơn này chưa bao giờ có hoá đơn trong ERPNext, và sẽ không
bao giờ có.** Không phải hoá đơn nháp, là không có gì cả. Nên phải đi tìm
chúng ở chính Pancake, và phải dò tiền bằng đường khác.

CÁCH DÒ TIỀN KHI KHÔNG CÓ HOÁ ĐƠN NÀO ĐỂ BÁM
--------------------------------------------
`ban_hang._sepay_theo_don` buộc một giao dịch vào đúng một đơn bằng cách đọc
`tabBank Transaction` và dò mạch `S<shop>O<id>T` mà Pancake sinh trong mã QR,
dò cả mã hiển thị kiểu WOO2749. Phép đó KHÔNG cần Sales Invoice nào, nên
dùng lại được nguyên vẹn ở đây.

BÚT TOÁN, CHỊ DUNG CHỐT 21/08/2026
----------------------------------
1. Mọi tiền vào lập phiếu thu ngay: Nợ 112 / Có 131, theo đơn.
2. Hoàn thì đủ HAI CHÂN. Máy sinh sẵn cả phiếu thu (lúc tiền vào) lẫn phiếu
   chi (lúc hoàn), cả hai ở dạng NHÁP.
3. Chứng từ gốc hai chiều đều lấy từ e-banking: giấy báo Có cho chiều vào,
   uỷ nhiệm chi cho chiều ra. SePay KHÔNG đủ. Khoản nhỏ dùng sao kê chính
   thức theo kỳ.
4. Theo dõi 131 theo SỐ ĐƠN ghi trong diễn giải, trên mã dùng chung
   "Khách lẻ Online". Số dư của mã bằng tổng đơn đã thu chưa giao chưa hoàn.

Điều 2 là lý do máy không được tự ghi sổ: phiếu nháp chờ kế toán đính chứng
từ e-banking rồi mới ghi. Đúng luật chị Dung chốt 16/08 và giữ nguyên từ đó.

BẢNG ĐỆM TỰ DỌN SAU 30 NGÀY
---------------------------
Anh Việt chốt: giữ 30 ngày rồi tự xoá. Chỗ này phải cẩn thận vì QT-20 cấm
xoá vĩnh viễn dữ liệu nghiệp vụ. Nên cái bị dọn CHỈ LÀ BẢN SAO đọc từ
Pancake của những đơn chưa phát sinh phiếu hoàn. Đơn đã sinh phiếu hoàn thì
giữ vĩnh viễn, vì lúc đó bản ghi là một mắt xích tra cứu. Và dù có dọn thì
nguồn sự thật vẫn nằm ở Pancake, đồng bộ lại là có ngay.
"""

import re
from datetime import datetime, timedelta

import frappe
from frappe.utils import add_days, flt, now_datetime

# Trạng thái Pancake 6 là đã huỷ, 7 là đã xoá. Chỉ lấy 6: đơn bị XOÁ là đơn
# nhập nhầm, không có khách nào chuyển tiền cho nó.
TT_HUY = 6

DT = "Vagabond Don Huy"

# Số ngày giữ bản đệm của đơn CHƯA phát sinh phiếu hoàn.
NGAY_GIU = 30

CHO_HOAN = "Cho hoan"
DANG_HOAN = "Dang hoan"
DA_HOAN = "Da hoan"
KHONG_PHAI = "Khong phai hoan"
BO_QUA = "Bo qua"

NHAN_TT = {
	CHO_HOAN: "Chờ hoàn",
	DANG_HOAN: "Đang hoàn",
	DA_HOAN: "Đã hoàn",
	KHONG_PHAI: "Không phải hoàn",
	BO_QUA: "Bỏ qua",
}

# Trạng thái hồ sơ hoàn tiền nào thì coi là xong. Đọc từ hoan_tien để không
# đẻ ra danh sách thứ hai (bài học 21/08/2026: hop_qua tự chế danh sách vai
# riêng và bỏ sót Sales User, Loan Anh không tuỳ biến hộp được).
TT_XONG = ("Hoan thanh",)
TT_HUY_HO_SO = ("Da huy",)

# Lý do huỷ đơn. KHOÁ không dấu, NHÃN có dấu.
#
# Vì sao hai phần chứ không phải một: khoá đi vào diễn giải chứng từ và vào
# nhật ký, nên phải là chuỗi ASCII ổn định, không đổi theo cách viết. Nhãn là
# thứ người ta đọc, nên phải có dấu tiếng Việt tử tế.
#
# Ngày 22/08/2026 anh Việt chụp màn hình chỉ ra sáu con chip đang hiện nguyên
# khoá: "Khach dat nham ngay", "Bep khong kip lam". Gốc là màn hình tự dựng
# danh sách chip bằng chính chuỗi khoá. Nên bảng này đặt ở MÁY CHỦ và màn
# hình đọc xuống, không màn nào được tự chế bảng thứ hai.
LY_DO_HUY = (
	("Khach doi y", "Khách đổi ý"),
	("Khach dat nham ngay", "Khách đặt nhầm ngày"),
	("Bep khong kip lam", "Bếp không kịp làm"),
	("Het nguyen lieu", "Hết nguyên liệu"),
	("Trung don", "Trùng đơn"),
	("Khac", "Khác"),
)


def nhan_ly_do(khoa):
	"""Khoá lý do huỷ -> nhãn có dấu. THUẦN. Khoá lạ thì trả lại nguyên văn."""
	k = str(khoa or "").strip()
	for a, b in LY_DO_HUY:
		if a == k:
			return b
	return k


# ---------------------------------------------------------------- phép thuần


def la_don_huy(don):
	"""Đơn Pancake này có phải đơn đã huỷ không."""
	try:
		return int((don or {}).get("status")) == TT_HUY
	except (TypeError, ValueError):
		return False


def trang_thai_don(da_nhan, ho_so_trang_thai=None, bo_qua=0):
	"""Chip trạng thái của một đơn huỷ. Đây là phép quyết định cả màn hình.

	Thứ tự các nhánh là cố ý:

	- Người đã bấm Bỏ qua thì tôn trọng, không lôi ra nữa dù có tiền.
	- Chưa thấy đồng nào thì KHÔNG PHẢI HOÀN. Khách huỷ trước khi chuyển
	  tiền là ca thường gặp nhất, lôi vào danh sách chờ hoàn thì Sales phải
	  lọc tay mỗi ngày và sẽ bỏ sót ca thật.
	- Có hồ sơ hoàn rồi thì trạng thái đọc theo hồ sơ đó, không tự đoán.
	"""
	if int(bo_qua or 0):
		return BO_QUA
	if flt(da_nhan) <= 0:
		return KHONG_PHAI
	tt = (ho_so_trang_thai or "").strip()
	if not tt:
		return CHO_HOAN
	if tt in TT_HUY_HO_SO:
		# Hồ sơ bị huỷ hoặc bị từ chối thì tiền vẫn còn ở mình, việc quay
		# lại hàng chờ chứ không được coi là xong.
		return CHO_HOAN
	if tt in TT_XONG:
		return DA_HOAN
	return DANG_HOAN


def muc_hoan(da_nhan):
	"""Số tiền máy điền sẵn vào form hoàn.

	Anh Việt chốt 21/08/2026: hoàn 100% số khách đã chuyển, để số sửa được.
	Phần giữ lại (nếu có thoả thuận trừ tiền nguyên liệu) là DOANH THU và
	phải xuất hoá đơn riêng, nên KHÔNG gộp vào đây. Xem mục "Chỗ nên có
	chính sách thành văn" trong claude/hoan-tien-khi-hoa-don-con-nhap.md.
	"""
	return flt(da_nhan) if flt(da_nhan) > 0 else 0.0


def dem_theo_chip(cac_dong):
	"""Đếm số đơn theo từng chip, để chip hiện số mà không phải gọi lại."""
	dem = {k: 0 for k in NHAN_TT}
	for d in cac_dong or ():
		tt = (d.get("trang_thai") or "").strip()
		if tt in dem:
			dem[tt] += 1
	dem["tat_ca"] = len(cac_dong or ())
	return dem


def tien_cho_hoan(cac_dong):
	"""Tổng tiền đang giữ hộ khách, chỉ tính đơn còn phải hoàn."""
	return sum(flt(d.get("da_nhan")) for d in (cac_dong or ())
		if (d.get("trang_thai") or "") in (CHO_HOAN, DANG_HOAN))


def dien_giai_don(ma_don, ma_hien_thi=None, ten_khach=None):
	"""Câu diễn giải đi vào phiếu thu và phiếu chi.

	Chị Dung chốt điều 4: theo dõi 131 theo SỐ ĐƠN ghi trong diễn giải, vì
	đơn online đổ chung vào mã "Khách lẻ Online". Nên số đơn phải nằm trong
	câu này, không được để nó chỉ nằm ở một trường phụ nào đó.
	"""
	ma = str(ma_don or "").strip()
	hien = str(ma_hien_thi or "").strip()
	ten = str(ten_khach or "").strip()
	phan = ["Don %s" % (hien or ma)]
	if hien and ma and hien != ma:
		phan.append("(ID %s)" % ma)
	if ten:
		phan.append("- %s" % ten)
	return " ".join(phan)


def noi_dung_chuyen_khoan(ma_don, ma_hien_thi=None):
	"""Nội dung chuyển khoản lúc trả tiền lại, theo cú pháp chốt 16/08/2026.

	Dòng sao kê chỉ có một ô nội dung, và ba tháng sau đó là thứ duy nhất kế
	toán đọc được.
	"""
	ma = str(ma_hien_thi or ma_don or "").strip()
	return ("THE VAGABOND HOAN TIEN %s" % ma).strip()


# --------------------------------------- dây chuyền phiếu hoàn, cho Sales
#
# Anh Việt 31/08/2026: *"thêm dùm anh nút để xem lại danh sách các phiếu
# hoàn cho đơn đã huỷ của pancake để sales theo dõi, nối các trạng thái, hồ
# sơ, uỷ nhiệm chi,... bên chỗ kế toán làm lên để tự động cập nhật sang cho
# bên sales theo dõi, tải UNC gửi khách"*.
#
# Sales lập phiếu xong là mất dấu: phần còn lại (chi tiền, đính uỷ nhiệm
# chi, ghi sổ, đối soát sao kê) đều nằm bên kế toán, mà phân hệ Kế toán thì
# v355 đã khoá lại không cho nhân viên vào. Nên phải có một cửa sổ RIÊNG mở
# về phía Sales, chỉ ĐỌC, không sửa được gì của kế toán.
#
# Không đẻ bảng thứ hai và không có nhịp đồng bộ nào: màn đọc thẳng hồ sơ
# hoàn tiền và phiếu chi mà kế toán đang làm, nên kế toán bấm xong là Sales
# thấy ngay ở lần mở màn kế tiếp.

# Bốn bước của một phiếu, theo đúng thứ tự đời thật. Khoá không dấu vì nó đi
# vào tên chip và vào tệp Excel; nhãn có dấu vì người ta đọc.
BUOC = (
	("lap", "Sales đã lập phiếu"),
	("unc", "Kế toán chuyển tiền và đính uỷ nhiệm chi"),
	("ghi", "Kế toán ghi sổ phiếu chi"),
	("soat", "Đối soát với sao kê ngân hàng"),
)

# Trạng thái hồ sơ hoàn tiền. Đọc lại y nguyên chuỗi bên hoan_tien để không
# đẻ ra danh sách thứ hai (bài học 22/08/2026: màn tự chế bảng chip rồi hiện
# nguyên khoá không dấu ra cho người dùng đọc).
TT_PHIEU = ("Cho chi", "Da chi", "Da doi soat", "Hoan thanh", "Da huy")

NHAN_TT_PHIEU = {
	"Cho chi": "Chờ kế toán chi",
	"Da chi": "Đã chi",
	"Da doi soat": "Đã đối soát",
	"Hoan thanh": "Hoàn thành",
	"Da huy": "Đã huỷ / Từ chối",
}

# Bốn loại phiếu hoàn. Khoá đọc từ hoan_tien, KHÔNG chép chuỗi sang đây: đó
# là cách sinh ra hai bảng rồi lệch nhau (bài học ba bảng điểm bán 12/08).
# Chuỗi rỗng là phiếu lập trước 18/08/2026, khi chưa có ô "Loại phiếu"; theo
# mô tả của chính ô đó thì mọi phiếu cũ đều là phiếu trả hàng. Hôm nay còn
# 10 trên 16 phiếu ở dạng rỗng, nên bỏ sót nhóm này là mất hơn nửa danh sách.
LOAI_RONG_LA = "Tra hang"


def cac_loai_hoan():
	"""Danh sách (khoá, nhãn) các loại phiếu, theo đúng thứ tự hiện trên chip."""
	from vagabond.hoan_tien import (
		LOAI_HUY_NHAP, LOAI_HUY_PANCAKE, LOAI_TIEN_DU, LOAI_TRA_HANG,
		NHAN_LOAI_HOAN,
	)

	return [(k, NHAN_LOAI_HOAN.get(k, k)) for k in (
		LOAI_HUY_PANCAKE, LOAI_TRA_HANG, LOAI_TIEN_DU, LOAI_HUY_NHAP)]


def loai_thuc(loai):
	"""Loại thật của một phiếu. THUẦN. Rỗng thì là phiếu trả hàng."""
	return str(loai or "").strip() or LOAI_RONG_LA


def diem_cua_phieu(loai, quay=None):
	"""Điểm bán của một phiếu hoàn. THUẦN.

	Hồ sơ hoàn tiền không mang sẵn ô điểm bán, nên phải suy ra:

	- Phiếu huỷ đơn Pancake thì chưa bao giờ có hoá đơn nào, và đơn Pancake
	  luôn thuộc Sales Online. Suy thẳng, không cần hỏi hoá đơn.
	- Còn lại thì đọc mã quầy trên hoá đơn gốc. Quầy để trống nghĩa là đơn
	  online, tức Sales Online.
	- Không có hoá đơn mà cũng không phải phiếu Pancake thì chịu, trả rỗng
	  chứ KHÔNG đoán bừa là Sales Online: đoán sai một điểm bán là làm lệch
	  số liệu của cả một cửa hàng.
	"""
	from vagabond.hoan_tien import LOAI_HUY_PANCAKE

	if loai_thuc(loai) == LOAI_HUY_PANCAKE:
		return "SALES"
	if quay is None:
		return ""
	from vagabond import diem_ban

	return diem_ban.ma_theo_quay(quay)

# Những ô người ta thật sự gõ vào ô tìm khi đi tìm một phiếu hoàn: mã đơn
# Pancake, số tài khoản khách đọc trong khung chat, tên chủ tài khoản, số
# điện thoại, mã phiếu, mã giao dịch ngân hàng.
TRUONG_TIM_PHIEU = (
	"name", "ma_don_pancake", "ten_tk", "so_tk", "sdt", "phieu_chi", "ma_gd",
)

# Ô tìm của chính màn Đơn đã huỷ.
TRUONG_TIM_DON = ("ma_don", "ma_hien_thi", "ten_khach", "sdt", "ma_gd")


def dieu_kien_tim(tim, truong):
	"""Dựng điều kiện HOẶC cho ô tìm, để đưa thẳng vào `or_filters`. THUẦN.

	QT-19 và anh Việt nhắc lại 31/08/2026: *"ô tìm kiếm đã yêu cầu viết ở
	backend cho MỌI MÀN"*. Lọc bằng Python SAU khi đã cắt dòng là cái bẫy
	im lặng nhất trong repo này: màn vẫn chạy, vẫn ra kết quả, chỉ là kết
	quả tìm trong đúng N dòng mới nhất. Đơn cũ hơn N thì gõ mã vào ô tìm ra
	danh sách rỗng, và người dùng kết luận là đơn đã mất.

	Trả None khi ô tìm rỗng, vì `or_filters=None` mới là "không lọc gì";
	truyền danh sách rỗng xuống Frappe là một chuyện khác hẳn.
	"""
	q = str(tim or "").strip()
	if not q:
		return None
	return [[c, "like", "%" + q + "%"] for c in truong]


def buoc_cua_phieu(trang_thai, co_unc=0, da_ghi_so=0, da_doi_soat=0):
	"""Phiếu đang đứng ở bước nào. THUẦN.

	Trả về (số bước đã xong trên bốn, khoá bước đang chờ, câu nói cho Sales).
	Phiếu đã huỷ thì không còn bước nào để chờ.

	Vì sao đọc bốn cờ chứ không đọc mỗi `trang_thai`: trạng thái nhảy sang
	"Da chi" ngay lúc kế toán ghi sổ phiếu chi, nhưng thứ khách hỏi Sales là
	*"đã chuyển chưa, cho em xin cái uỷ nhiệm chi"*. Cờ uỷ nhiệm chi trả lời
	được câu đó, còn trạng thái thì không.
	"""
	tt = str(trang_thai or "").strip()
	if tt in ("Da huy",):
		return (0, "", "Phiếu đã huỷ, không hoàn nữa.")
	if tt in ("Hoan thanh",) or int(da_doi_soat or 0):
		return (4, "", "Xong. Tiền đã ra và đã khớp sao kê ngân hàng.")
	if int(da_ghi_so or 0) or tt in ("Da chi", "Da doi soat"):
		return (3, "soat", "Tiền đã ra và đã ghi sổ, đang chờ khớp sao kê.")
	if int(co_unc or 0):
		return (2, "ghi", "Đã có uỷ nhiệm chi, đang chờ kế toán ghi sổ.")
	return (1, "unc", "Đang chờ kế toán chuyển tiền và đính uỷ nhiệm chi.")


def dem_theo_tt_phieu(cac_dong):
	"""Đếm phiếu theo từng chip trạng thái. THUẦN."""
	dem = {k: 0 for k in TT_PHIEU}
	for d in cac_dong or ():
		tt = str(d.get("trang_thai") or "").strip()
		if tt in dem:
			dem[tt] += 1
	dem["tat_ca"] = len(cac_dong or ())
	return dem


def _ngay(v):
	"""Đọc ngày từ chuỗi hoặc từ đối tượng ngày giờ. Trả None nếu không đọc được.

	Tự phân tích bằng `datetime` chuẩn chứ KHÔNG gọi `frappe.utils`: hàm này
	là phép thuần, phải chạy được ở máy chạy CI nơi không có Frappe. Bản giả
	lập Frappe của bộ kiểm thử không có `get_datetime`, và ca kiểm đã đỏ
	đúng vì chuyện đó (21/08/2026).
	"""
	if not v:
		return None
	if hasattr(v, "date") and not isinstance(v, str):
		try:
			return v.date()
		except Exception:
			return None
	s = str(v).strip().replace("T", " ")[:10]
	try:
		return datetime.strptime(s, "%Y-%m-%d").date()
	except ValueError:
		return None


def qua_han_don_dep(huy_luc, hom_nay, ngay_giu=NGAY_GIU):
	"""Bản đệm này đã quá hạn giữ chưa. Chỉ tính NGÀY, không tính giờ.

	Tính theo ngày để câu trả lời không đổi tuỳ giờ chạy: một bản ghi không
	thể còn hạn lúc 9 giờ sáng rồi hết hạn lúc 5 giờ chiều cùng ngày.
	"""
	moc, nay = _ngay(huy_luc), _ngay(hom_nay)
	if not (moc and nay):
		return False
	return (nay - moc).days > int(ngay_giu or NGAY_GIU)


# ------------------------------------------------------- phần chạm hệ thống


def _quyen():
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()


def _shop():
	from vagabond.lib import cfg

	c = cfg()
	return c, (c.pancake_shop_id or "").strip()


def khoang_quet(so_ngay=NGAY_GIU, moc_cuoi=None):
	"""Khoảng thời gian quét Pancake, trả về UNIX GIÂY chứ không phải chuỗi.

	Pancake nhận startDateTime và endDateTime là UNIX giây. Truyền chuỗi ISO
	thì nó trả về DANH SÁCH RỖNG và không báo lỗi gì cả: HTTP vẫn 200, "data"
	vẫn có, chỉ là không có phần tử nào. Nhìn từ ngoài y hệt "shop không có
	đơn huỷ nào", nên rất khó ngờ.

	Đã ngã đúng chỗ này hai lần. Lần một ở kiem_banh, đã ghi cảnh báo ngay
	đầu tệp đó. Lần hai ở chính màn này ngày 21/08/2026: deploy v264 xong,
	dong_bo chạy sạch không lỗi, trả về quet 0 trong khi Pancake đang có ba
	đơn huỷ 92252, 92245, 92156 mà anh Việt chụp màn hình gửi sang.

	Tham số `moc_cuoi` chỉ để ca kiểm thử đóng cứng thời điểm, chạy thật thì
	để trống.
	"""
	from zoneinfo import ZoneInfo

	tz = ZoneInfo("Asia/Ho_Chi_Minh")
	cuoi = moc_cuoi or datetime.now(tz)
	if cuoi.tzinfo is None:
		cuoi = cuoi.replace(tzinfo=tz)
	dau = cuoi - timedelta(days=int(so_ngay or NGAY_GIU))
	return int(dau.timestamp()), int(cuoi.timestamp())


def _keo_don_huy(so_ngay=NGAY_GIU):
	"""Kéo đơn Pancake bị huỷ trong khoảng ngày, quét theo NGÀY CẬP NHẬT.

	Quét theo `updated_at` chứ không theo ngày giao là mấu chốt: đơn đặt hôm
	nay giao thứ Bảy mà huỷ chiều nay thì ngày giao còn nằm ở tương lai, quét
	theo ngày giao là không bao giờ thấy nó. Chính chỗ này làm luồng đồng bộ
	cũ bỏ sót toàn bộ đơn huỷ.
	"""
	import requests

	from vagabond.lib import PANCAKE, TIMEOUT, key

	c, shop = _shop()
	if not shop:
		frappe.throw("Chưa khai mã shop Pancake trong Vagabond Settings.")
	k = key(c, "pancake_api_key")
	if not k:
		frappe.throw("Chưa khai khoá API Pancake trong Vagabond Settings.")
	dau, cuoi = khoang_quet(so_ngay)
	ra = []
	for trang in range(1, 11):
		r = requests.get(
			"%s/shops/%s/orders" % (PANCAKE, shop),
			params={
				"api_key": k,
				"updateStatus": "updated_at",
				"startDateTime": dau,
				"endDateTime": cuoi,
				"page_size": 100,
				"page_number": trang,
			},
			timeout=TIMEOUT,
		)
		r.raise_for_status()
		ds_trang = (r.json() or {}).get("data") or []
		ra.extend([o for o in ds_trang if la_don_huy(o)])
		if len(ds_trang) < 100:
			break
	return ra


def _doc_don(o):
	"""Lấy đúng các trường mình cần từ một đơn Pancake, không ôm cả cục."""
	ma = str(o.get("id") or "").strip()
	return {
		"ma_don": ma,
		"ma_hien_thi": str(o.get("system_id") or o.get("display_id") or ma).strip(),
		"ten_khach": (o.get("bill_full_name")
			or ((o.get("customer") or {}).get("name")) or "").strip(),
		"sdt": (o.get("bill_phone_number")
			or ((o.get("shipping_address") or {}).get("phone_number")) or "").strip(),
		"tong_don": flt(o.get("total_price")),
		"ngay_dat": (o.get("inserted_at") or "")[:19] or None,
		"ngay_giao": (o.get("estimate_delivery_date") or "")[:19] or None,
		"huy_luc": (o.get("updated_at") or o.get("inserted_at") or "")[:19] or None,
		"ghi_chu_don": (o.get("note") or o.get("note_print") or "")[:500],
	}


def _tt_ho_so(ho_so):
	if not ho_so:
		return None
	return frappe.db.get_value("Vagabond Hoan Tien", ho_so, "trang_thai")


@frappe.whitelist()
def dong_bo(so_ngay=NGAY_GIU):
	"""Kéo đơn huỷ từ Pancake về bảng đệm và dò tiền cho từng đơn.

	Chạy lại bao nhiêu lần cũng không đổi gì thêm: đơn đã có thì cập nhật,
	chưa có thì tạo. KHÔNG bao giờ đụng vào trạng thái của bản ghi mà người
	ta đã bấm Bỏ qua.
	"""
	# Nhip tu dong chay duoi Administrator, khong co phien nguoi dung. Kiem
	# quyen chi ap cho nguoi bam nut.
	if frappe.session.user != "Administrator":
		_quyen()
	from vagabond.ban_hang import _sepay_theo_don

	dons = [_doc_don(o) for o in _keo_don_huy(so_ngay)]
	dons = [d for d in dons if d["ma_don"]]
	if not dons:
		return {"quet": 0, "moi": 0, "cap_nhat": 0, "don_dep": don_ban_dem()}

	_c, shop = _shop()
	# Dò cả hai đường: ID nội bộ và mã hiển thị, y như bảng doanh số làm.
	ma_tim = []
	for d in dons:
		ma_tim.append(d["ma_don"])
		if d["ma_hien_thi"] and d["ma_hien_thi"] != d["ma_don"]:
			ma_tim.append(d["ma_hien_thi"])
	tien = _sepay_theo_don(shop, ma_tim) or {}

	moi = cap_nhat = 0
	for d in dons:
		t = tien.get(d["ma_don"]) or tien.get((d["ma_hien_thi"] or "").upper()) or {}
		d["da_nhan"] = flt(t.get("nhan"))
		d["ma_gd"] = (t.get("ma") or "")[:140]
		ten = frappe.db.exists(DT, {"ma_don": d["ma_don"]})
		if ten:
			doc = frappe.get_doc(DT, ten)
			cu = (doc.trang_thai or "").strip()
			for khoa, gia_tri in d.items():
				doc.set(khoa, gia_tri)
			doc.dong_bo_luc = now_datetime()
			doc.trang_thai = trang_thai_don(
				doc.da_nhan, _tt_ho_so(doc.ho_so_hoan), 1 if cu == BO_QUA else 0)
			doc.save(ignore_permissions=True)
			cap_nhat += 1
		else:
			doc = frappe.new_doc(DT)
			doc.update(d)
			doc.dong_bo_luc = now_datetime()
			doc.trang_thai = trang_thai_don(d["da_nhan"])
			doc.insert(ignore_permissions=True)
			moi += 1
	return {
		"quet": len(dons), "moi": moi, "cap_nhat": cap_nhat,
		"don_dep": don_ban_dem(),
	}


# Cua so quet cua NHIP TU DONG. Ngan hon cua nut bam tay (30 ngay) vi
# nhip nay chay nua tieng mot lan: quet ba ngay la du bat moi don vua huy,
# va con thua slack cho vai lan nhip hong lien tiep.
NGAY_TU_DONG = 3


def dong_bo_tu_dong():
	"""Scheduler gọi 30 phút một lần: kéo đơn huỷ mới từ Pancake.

	Vì sao phải có nhịp này, ghi lại ngày 31/08/2026
	------------------------------------------------
	Trước hôm nay mô đun này KHÔNG có nhịp tự động nào. Cách duy nhất để đơn
	huỷ về hệ là có người bấm nút Đồng bộ trên màn. Mà chính cái nút đó lại
	nằm ở chân màn và chưa bao giờ bấm được (xem ghi chú ở
	`29-don-huy.js`). Hai cái hỏng chồng lên nhau nên lần đồng bộ cuối cùng
	là 21/08/2026, mười ngày không một đơn huỷ nào về hệ.

	Tiền của khách đang nằm ở mình thì không được chờ ai bấm nút. Nên nhịp
	này là hàng rào thứ hai, và nút bấm tay vẫn giữ để kéo cửa sổ 30 ngày
	khi cần dò lại.

	Hỏng thì ghi nhật ký rồi thôi, không bao giờ ném ra ngoài: nhịp này
	chung slot với các nhịp khác, ném ra là kéo chết cả slot.
	"""
	try:
		dong_bo(so_ngay=NGAY_TU_DONG)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "don_huy: dong bo tu dong")


def don_ban_dem(ngay_giu=NGAY_GIU):
	"""Dọn bản đệm quá hạn. CHỈ dọn đơn chưa hề phát sinh phiếu hoàn.

	Đơn đã có hồ sơ hoàn thì giữ vĩnh viễn: lúc đó bản ghi là một mắt xích
	tra cứu chứ không còn là bản sao đọc chơi, và QT-20 cấm xoá vết. Đơn còn
	Chờ hoàn hoặc Đang hoàn cũng không dọn dù quá hạn, vì tiền của khách vẫn
	đang nằm ở mình.
	"""
	moc = add_days(now_datetime(), -int(ngay_giu or NGAY_GIU))
	cac = frappe.get_all(DT, filters={
		"huy_luc": ["<", moc],
		"ho_so_hoan": ["in", ["", None]],
		"trang_thai": ["in", [KHONG_PHAI, BO_QUA]],
	}, pluck="name")
	for ten in cac:
		frappe.delete_doc(DT, ten, ignore_permissions=True, force=1)
	return len(cac)


@frappe.whitelist()
def ds(trang_thai="", tim="", so_dong=200):
	"""Danh sách đơn huỷ cho màn hình, kèm số đếm từng chip.

	Số đếm tính trên TOÀN BỘ bảng chứ không phải trên trang đang xem, để chip
	"Chờ hoàn 3" nói đúng số việc còn tồn.
	"""
	_quyen()
	loc = {}
	tt = (trang_thai or "").strip()
	if tt and tt in NHAN_TT:
		loc["trang_thai"] = tt
	truong = ["name", "ma_don", "ma_hien_thi", "ten_khach", "sdt", "tong_don",
		"da_nhan", "ngay_dat", "ngay_giao", "huy_luc", "trang_thai",
		"ho_so_hoan", "hoa_don", "ghi_chu_don", "ma_gd"]
	# Ô tìm chạy Ở MÁY CHỦ, không lọc lại bằng Python sau khi đã cắt dòng.
	# Trước 31/08/2026 chỗ này cắt 200 dòng mới nhất rồi mới lọc, nên gõ mã
	# một đơn huỷ từ tháng trước là ra danh sách rỗng dù đơn vẫn còn nguyên.
	hoac = dieu_kien_tim(tim, TRUONG_TIM_DON)
	dong = frappe.get_all(DT, filters=loc, or_filters=hoac, fields=truong,
		order_by="huy_luc desc", limit_page_length=int(so_dong or 200))
	# Số trên chip đếm theo ĐÚNG ô tìm đang gõ. Nếu không thì gõ một cái tên
	# ra 2 dòng mà chip vẫn báo 40, và người đọc không biết tin con số nào.
	tat_ca = frappe.get_all(DT, filters={}, or_filters=hoac,
		fields=["trang_thai", "da_nhan"], limit_page_length=0)
	for d in dong:
		d["nhan_trang_thai"] = NHAN_TT.get(d["trang_thai"], d["trang_thai"])
		d["muc_hoan"] = muc_hoan(d["da_nhan"])
	return {
		"dong": dong,
		"dem": dem_theo_chip(tat_ca),
		"tien_cho_hoan": tien_cho_hoan(tat_ca),
		"nhan": dict(NHAN_TT),
		"ngay_giu": NGAY_GIU,
	}


@frappe.whitelist()
def dem_cho_hoan():
	"""Số việc còn tồn, cho huy hiệu trên chip và mục Việc cần làm."""
	return frappe.db.count(DT, {"trang_thai": ["in", [CHO_HOAN, DANG_HOAN]]})


@frappe.whitelist()
def bo_qua(ma_don, ly_do=""):
	"""Đánh dấu một đơn không cần hoàn nữa. Huỷ mềm, giữ nguyên vết (QT-20)."""
	_quyen()
	ten = frappe.db.exists(DT, {"ma_don": str(ma_don or "").strip()})
	if not ten:
		frappe.throw("Không tìm thấy đơn %s trong danh sách đã huỷ." % ma_don)
	doc = frappe.get_doc(DT, ten)
	if doc.ho_so_hoan:
		frappe.throw("Đơn này đã có hồ sơ hoàn tiền %s, xử lý hồ sơ đó chứ "
			"không bỏ qua ở đây." % doc.ho_so_hoan)
	doc.trang_thai = BO_QUA
	# Ghi AI bỏ qua và VÌ SAO ngay trong ghi chú: ba tháng sau chỉ còn dòng
	# này trả lời được câu "sao đơn 750 nghìn này không ai hoàn".
	cu = (doc.ghi_chu_don or "").strip()
	doc.ghi_chu_don = ("%s [Bỏ qua %s bởi %s] %s" % (
		cu, str(now_datetime())[:16], frappe.session.user,
		(ly_do or "").strip())).strip()[:500]
	doc.save(ignore_permissions=True)
	return {"ma_don": doc.ma_don, "trang_thai": doc.trang_thai}


@frappe.whitelist()
def xuat_excel(trang_thai="", tim=""):
	"""Xuất danh sách ra Excel cho kế toán đối chiếu."""
	_quyen()
	kq = ds(trang_thai=trang_thai, tim=tim, so_dong=2000)
	cot = [
		("ma_hien_thi", "Ma don"),
		("ma_don", "ID Pancake"),
		("ten_khach", "Khach hang"),
		("sdt", "So dien thoai"),
		("tong_don", "Tong tien don"),
		("da_nhan", "Khach da chuyen"),
		("muc_hoan", "Phai hoan"),
		("nhan_trang_thai", "Trang thai"),
		("ho_so_hoan", "Ho so hoan tien"),
		("ngay_dat", "Ngay dat"),
		("ngay_giao", "Ngay giao du kien"),
		("huy_luc", "Huy luc"),
		("ma_gd", "Ma giao dich"),
	]
	return {
		"ten_tep": "don-huy-cho-hoan-%s.csv" % str(now_datetime())[:10],
		"cot": [n for _f, n in cot],
		"hang": [[d.get(f) for f, _n in cot] for d in kq["dong"]],
		"tong_dong": len(kq["dong"]),
		"tien_cho_hoan": kq["tien_cho_hoan"],
	}


# ------------------------------------- màn Phiếu hoàn đơn huỷ, phía Sales


def _unc_theo_phieu_chi(ma_pc):
	"""Uỷ nhiệm chi đã đính vào từng phiếu chi. Một câu cho cả trang.

	Trả đường dẫn tệp chứ không chỉ trả cờ có/không: Sales cần TẢI VỀ để gửi
	cho khách, đó là cả lý do anh Việt xin màn này.
	"""
	ra = {}
	if not ma_pc:
		return ra
	for f in frappe.get_all(
		"File",
		filters={"attached_to_doctype": "Payment Entry",
			"attached_to_name": ["in", list(ma_pc)]},
		fields=["attached_to_name", "file_url", "file_name"],
		order_by="creation asc", limit_page_length=0,
	):
		ra.setdefault(f["attached_to_name"], []).append({
			"url": f["file_url"], "ten": f["file_name"],
		})
	return ra


@frappe.whitelist()
def ds_phieu(diem="", loai="", trang_thai="", tim="", so_dong=200):
	"""Danh sách phiếu hoàn tiền, dựng cho các điểm bán theo dõi.

	Anh Việt 31/08/2026: màn danh mục phiếu hoàn tiền trước giờ chỉ có bên
	phân hệ Kế toán, mà phân hệ đó v355 đã khoá lại không cho nhân viên vào.
	Nên gộp cả bốn loại phiếu vào đây, mở về phía các điểm bán.

	CHỈ ĐỌC. Không hàm nào ở đây sửa được hồ sơ hay phiếu chi của kế toán;
	các điểm bán nhìn thấy việc chạy tới đâu, thế thôi.

	BA HỌ CHIP: điểm bán, loại phiếu, trạng thái. Mỗi họ đếm trên tập đã lọc
	bởi HAI họ kia, để bấm một chip xong thì số trên các chip còn lại vẫn nói
	đúng "bấm thêm cái này thì còn bao nhiêu". Đếm trên toàn sổ mà không nhìn
	các chip khác thì con số to hơn danh sách, người đọc mất tin.

	Vì sao lọc điểm bán bằng Python chứ không bằng câu truy vấn: hồ sơ hoàn
	tiền không mang sẵn ô điểm bán, nó nằm trên hoá đơn gốc. Nhưng phép đọc ở
	đây KHÔNG cắt dòng trước (`limit_page_length=0`), nên đây không phải cái
	bẫy mà `thu_phieu_hoan_huy.py` canh: cắt dòng làm ở bước CUỐI, sau khi đã
	lọc xong và đã đếm xong. Cùng cách tầng khung dựng danh sách vẫn làm.
	"""
	_quyen()
	from vagabond.hoan_tien import DT as HT

	loc = {}
	tt = str(trang_thai or "").strip()
	if tt and tt in TT_PHIEU:
		loc["trang_thai"] = tt
	hoac = dieu_kien_tim(tim, TRUONG_TIM_PHIEU)

	truong = ["name", "loai_hoan", "hoa_don", "ma_don_pancake", "so_tien",
		"trang_thai", "ly_do", "dien_giai", "ten_tk", "so_tk", "ngan_hang",
		"sdt", "phieu_chi", "phieu_thu", "da_doi_soat", "ma_gd",
		"ngay_doi_soat", "noi_dung_ck", "nguoi_duyet", "creation", "so_hddt",
		"ly_do_tu_choi", "nguoi_tu_choi"]
	dong = frappe.get_all(HT, filters=loc, or_filters=hoac, fields=truong,
		order_by="creation desc", limit_page_length=0)

	# Quầy của hoá đơn gốc, một câu cho cả trang. Từ quầy mới ra điểm bán.
	ma_hd = list({d["hoa_don"] for d in dong if d.get("hoa_don")})
	quay = {}
	if ma_hd:
		for r in frappe.get_all("Sales Invoice",
				filters={"name": ["in", ma_hd]},
				fields=["name", "vgb_quay"], limit_page_length=0):
			quay[r["name"]] = r.get("vgb_quay") or ""

	ma_pc = [d["phieu_chi"] for d in dong if d.get("phieu_chi")]
	da_ghi = {}
	if ma_pc:
		for r in frappe.get_all("Payment Entry",
				filters={"name": ["in", ma_pc]},
				fields=["name", "docstatus"], limit_page_length=0):
			da_ghi[r["name"]] = r
	unc = _unc_theo_phieu_chi(ma_pc)

	# Tên khách. Phiếu Pancake lấy từ bảng đệm đơn huỷ vì hồ sơ treo vào mã
	# khách chung; phiếu có hoá đơn thì lấy tên khách trên hoá đơn.
	ma_don = [d["ma_don_pancake"] for d in dong if d.get("ma_don_pancake")]
	don = {}
	if ma_don:
		for r in frappe.get_all(DT, filters={"ma_don": ["in", ma_don]},
				fields=["ma_don", "ma_hien_thi", "ten_khach", "huy_luc"],
				limit_page_length=0):
			don[r["ma_don"]] = r
	ten_hd = {}
	if ma_hd:
		for r in frappe.get_all("Sales Invoice",
				filters={"name": ["in", ma_hd]},
				fields=["name", "customer_name"], limit_page_length=0):
			ten_hd[r["name"]] = r.get("customer_name") or ""

	from vagabond.hoan_tien import NHAN_LOAI_HOAN

	for d in dong:
		pc = da_ghi.get(d.get("phieu_chi") or "") or {}
		tep = unc.get(d.get("phieu_chi") or "") or []
		d["co_unc"] = 1 if tep else 0
		d["unc"] = tep
		d["phieu_chi_da_ghi"] = 1 if int(pc.get("docstatus") or 0) == 1 else 0
		xong, cho, cau = buoc_cua_phieu(
			d.get("trang_thai"), d["co_unc"], d["phieu_chi_da_ghi"],
			d.get("da_doi_soat"))
		d["buoc_xong"] = xong
		d["buoc_cho"] = cho
		d["cau_tinh_hinh"] = cau
		d["nhan_trang_thai"] = NHAN_TT_PHIEU.get(
			d.get("trang_thai"), d.get("trang_thai"))
		d["loai"] = loai_thuc(d.get("loai_hoan"))
		d["nhan_loai"] = NHAN_LOAI_HOAN.get(d.get("loai_hoan") or "", d["loai"])
		hd = d.get("hoa_don") or ""
		d["diem_ban"] = diem_cua_phieu(
			d.get("loai_hoan"), quay.get(hd) if hd else None)
		g = don.get(d.get("ma_don_pancake") or "") or {}
		d["ma_hien_thi"] = (g.get("ma_hien_thi") or d.get("ma_don_pancake")
			or hd or "")
		d["ten_khach"] = g.get("ten_khach") or ten_hd.get(hd, "")
		d["huy_luc"] = g.get("huy_luc")
		d["nhan_ly_do"] = nhan_ly_do(d.get("ly_do"))
		d["creation"] = str(d.get("creation") or "")[:16]
		d["ngay_doi_soat"] = str(d.get("ngay_doi_soat") or "")[:16]

	dm = str(diem or "").strip().upper()
	lo = str(loai or "").strip()
	hop = lambda r: ((not dm or r["diem_ban"] == dm)
		and (not lo or r["loai"] == lo))

	ten_diem = _ten_diem()
	dem_diem, dem_loai, dem_tt = {}, {}, {}
	for r in dong:
		# Mỗi họ chip đếm trên tập đã lọc bởi HAI họ kia.
		if (not lo or r["loai"] == lo):
			dem_diem[r["diem_ban"]] = dem_diem.get(r["diem_ban"], 0) + 1
		if (not dm or r["diem_ban"] == dm):
			dem_loai[r["loai"]] = dem_loai.get(r["loai"], 0) + 1
		if hop(r):
			dem_tt[r["trang_thai"]] = dem_tt.get(r["trang_thai"], 0) + 1
	dem_diem["tat_ca"] = len([r for r in dong if (not lo or r["loai"] == lo)])
	dem_loai["tat_ca"] = len([r for r in dong if (not dm or r["diem_ban"] == dm)])
	dem_tt["tat_ca"] = len([r for r in dong if hop(r)])

	ra = [r for r in dong if hop(r)]
	tran = max(1, min(1000, int(so_dong or 200)))
	# CẮT DÒNG Ở BƯỚC CUỐI, sau khi đã lọc và đã đếm xong.
	return {
		"dong": ra[:tran],
		"tong_dong": len(ra),
		"con_nua": 1 if len(ra) > tran else 0,
		"dem": dem_tt,
		"dem_diem": dem_diem,
		"dem_loai": dem_loai,
		"nhan": dict(NHAN_TT_PHIEU),
		"buoc": [{"k": k, "ten": t} for k, t in BUOC],
		"diem": [{"k": k, "ten": v} for k, v in ten_diem.items()],
		"loai": [{"k": k, "ten": t} for k, t in cac_loai_hoan()],
		"cho_unc": len([r for r in ra if r["buoc_cho"] == "unc"]),
		"tien_dang_chay": sum(flt(r.get("so_tien")) for r in ra
			if r["buoc_xong"] < 4 and r.get("trang_thai") != "Da huy"),
	}


def _ten_diem():
	"""Bảng mã điểm bán -> tên ngắn, cho chip. Hỏng cấu hình thì vẫn chạy."""
	try:
		from vagabond import diem_ban

		return diem_ban.ten_diem()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "don_huy: doc diem ban loi")
		return {"SALES": "Sales Online"}


@frappe.whitelist()
def xuat_excel_phieu(diem="", loai="", trang_thai="", tim=""):
	"""Xuất đúng cái đang hiện trên màn: cùng ba họ chip, cùng ô tìm."""
	_quyen()
	kq = ds_phieu(diem=diem, loai=loai, trang_thai=trang_thai, tim=tim,
		so_dong=1000)
	ten_diem = _ten_diem()
	for d in kq["dong"]:
		d["ten_diem_ban"] = ten_diem.get(d.get("diem_ban") or "", "(chua ro)")
	cot = [
		("ma_hien_thi", "Ma don hoac hoa don"),
		("ma_don_pancake", "ID Pancake"),
		("hoa_don", "Hoa don goc"),
		("ten_diem_ban", "Diem ban"),
		("nhan_loai", "Loai phieu"),
		("ten_khach", "Khach hang"),
		("so_tien", "So tien hoan"),
		("nhan_trang_thai", "Trang thai"),
		("cau_tinh_hinh", "Dang cho gi"),
		("name", "Ma phieu hoan"),
		("phieu_chi", "Phieu chi"),
		("co_unc", "Co uy nhiem chi"),
		("phieu_chi_da_ghi", "Phieu chi da ghi so"),
		("ma_gd", "Ma giao dich"),
		("ngay_doi_soat", "Ngay doi soat"),
		("ten_tk", "Ten chu tai khoan"),
		("so_tk", "So tai khoan"),
		("ngan_hang", "Ngan hang"),
		("nguoi_duyet", "Nguoi lap"),
		("creation", "Lap luc"),
	]
	return {
		"ten_tep": "phieu-hoan-tien-%s.csv" % str(now_datetime())[:10],
		"cot": [n for _f, n in cot],
		"hang": [[d.get(f) for f, _n in cot] for d in kq["dong"]],
		"tong_dong": len(kq["dong"]),
	}


# --------------------------------------------- sinh chứng từ, đủ HAI CHÂN


def _cong_ty():
	return (frappe.defaults.get_user_default("Company")
		or frappe.db.get_value("Company", {"name": ["!=", ""]}, "name"))


def _khach_le_online():
	"""Mã khách dùng chung cho đơn online, chị Dung chốt điều 4.

	Không dựng mã riêng cho từng người: chị Dung chốt theo dõi 131 bằng SỐ
	ĐƠN ghi trong diễn giải. Nên chỗ này chỉ đi tìm đúng mã đang dùng, và
	nếu không thấy thì DỪNG chứ không tự tạo khách mới - tạo bừa một mã
	khách là đẻ ra một dòng công nợ không ai đối chiếu được.
	"""
	for ten in ("Khách lẻ Online", "Khach le Online"):
		if frappe.db.exists("Customer", ten):
			return ten
	ten = frappe.db.get_value("Customer", {"customer_name": ["like", "%lẻ Online%"]}, "name")
	if ten:
		return ten
	frappe.throw("Chưa tìm thấy mã khách \"Khách lẻ Online\" để treo khoản này. "
		"Nhờ kế toán kiểm lại danh mục khách rồi thử lại.")


def _tk_ngan_hang(cong_ty):
	from vagabond.hoan_tien import tk_chi

	tk = tk_chi(cong_ty)
	if not tk:
		frappe.throw("Chưa khai tài khoản ngân hàng của công ty trong Vagabond Settings.")
	tk_ke_toan = frappe.db.get_value("Bank Account", tk, "account")
	if not tk_ke_toan:
		frappe.throw("Tài khoản ngân hàng %s chưa gắn tài khoản kế toán." % tk)
	return tk_ke_toan


@frappe.whitelist()
def xem_hoan(ma_don):
	"""Màn hỏi TRƯỚC khi mở form: đơn này hoàn được bao nhiêu, vì sao."""
	_quyen()
	ten = frappe.db.exists(DT, {"ma_don": str(ma_don or "").strip()})
	if not ten:
		frappe.throw("Chưa có đơn %s trong danh sách. Bấm Đồng bộ rồi thử lại."
			% ma_don)
	d = frappe.get_doc(DT, ten)
	cu = d.ho_so_hoan and frappe.db.get_value(
		"Vagabond Hoan Tien", d.ho_so_hoan,
		["name", "trang_thai", "so_tien"], as_dict=True)
	duoc = 1 if (flt(d.da_nhan) > 0 and not d.ho_so_hoan) else 0
	return {
		"ma_don": d.ma_don,
		"ma_hien_thi": d.ma_hien_thi,
		"ten_khach": d.ten_khach,
		"sdt": d.sdt,
		"tong_don": flt(d.tong_don),
		"da_nhan": flt(d.da_nhan),
		"muc_hoan": muc_hoan(d.da_nhan),
		"trang_thai": d.trang_thai,
		"duoc": duoc,
		"da_co": cu or None,
		"noi_dung_ck": noi_dung_chuyen_khoan(d.ma_don, d.ma_hien_thi),
		# Màn hình vẽ chip từ bảng này chứ không tự chế danh sách. Xem ghi
		# chú ở LY_DO_HUY về vì sao.
		"ly_do_chon": [{"k": a, "ten": b} for a, b in LY_DO_HUY],
		"goi_y_bang_chung": (
			"Chụp hình khung chat với khách, khung chat bếp không làm kịp,..."
		),
		"vi_sao": (
			("Đơn này đã có hồ sơ %s đang ở trạng thái \"%s\"." % (
				cu["name"], cu["trang_thai"])) if cu
			else ("Chưa thấy đồng nào của đơn này về tài khoản công ty. Nếu khách "
			      "có chuyển thật thì đối chiếu sao kê rồi bấm Đồng bộ lại."
			      if flt(d.da_nhan) <= 0 else "")
		),
	}


def _bang_chung_hop_le(tep):
	"""Lọc danh sách ảnh bằng chứng, chỉ giữ mã tệp còn thật trên máy chủ.

	Nhận rộng ở cửa vào - chuỗi JSON, danh sách mã, danh sách {ma: ...} - vì
	màn hình có thể gửi theo cả ba dạng, nhưng ra khỏi hàm này thì chỉ còn
	một dạng duy nhất là danh sách mã File.

	Lọc theo `frappe.db.exists` chứ không tin danh sách màn gửi lên: gửi mã
	bịa thì phiếu sẽ mang một danh sách ảnh không mở được, mà vẫn qua được
	phép kiểm "đã có bằng chứng".
	"""
	if isinstance(tep, str):
		try:
			tep = frappe.parse_json(tep)
		except Exception:
			tep = [x.strip() for x in tep.replace(",", "\n").split("\n") if x.strip()]
	if isinstance(tep, dict):
		tep = [tep]
	ra = []
	for t in (tep or []):
		ma = (t.get("ma") or t.get("file") or t.get("name")) if isinstance(t, dict) else t
		ma = str(ma or "").strip()
		if not ma or ma in ra:
			continue
		try:
			if frappe.db.exists("File", ma):
				ra.append(ma)
		except Exception:
			continue
	return ra


def _gan_bang_chung(tep_bc, ten_ho_so, ten_phieu_chi=None):
	"""Trỏ ảnh bằng chứng về hồ sơ hoàn tiền, để chế độ riêng tư.

	Riêng tư là bắt buộc chứ không phải tuỳ chọn: ảnh khung chat có tên và số
	điện thoại khách, để công khai thì ai có đường dẫn cũng mở được.

	Một tệp chỉ đính vào ĐÚNG MỘT chứng từ trong Frappe, nên bản trên phiếu
	chi là bản NHÂN ĐÔI chứ không phải chuyển chỗ. Làm vậy để hồ sơ vẫn giữ
	ảnh cho Sales xem, mà kế toán mở Payment Entry bên ERPNext cũng thấy ngay
	căn cứ, không phải lần ngược sang màn khác.
	"""
	from vagabond.hoan_tien import DT as HT_DT

	for ma in (tep_bc or []):
		try:
			frappe.db.set_value("File", ma, {
				"attached_to_doctype": HT_DT,
				"attached_to_name": ten_ho_so,
				"is_private": 1,
			}, update_modified=False)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "don_huy: gan bang chung ve ho so")
		if not ten_phieu_chi:
			continue
		try:
			goc = frappe.get_doc("File", ma)
			ban = frappe.get_doc({
				"doctype": "File",
				"file_name": goc.file_name,
				"file_url": goc.file_url,
				"is_private": 1,
				"attached_to_doctype": "Payment Entry",
				"attached_to_name": ten_phieu_chi,
			})
			ban.flags.ignore_permissions = True
			# Hai bản ghi File cùng trỏ một tệp trên đĩa. Không cho Frappe nhân
			# đôi tệp thật, vừa tốn chỗ vừa làm hai bản lệch nhau khi gỡ một bên.
			ban.insert(ignore_permissions=True, ignore_if_duplicate=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "don_huy: chep bang chung sang phieu chi")


@frappe.whitelist()
def tao_hoan(ma_don, so_tien=0, ly_do="", ten_tk="", so_tk="", ngan_hang="",
		sdt_khach="", dien_giai="", otp=None, bang_chung=None):
	"""Lập hồ sơ hoàn tiền cho một đơn Pancake CHƯA BAO GIỜ về ERPNext.

	Sinh đủ HAI CHÂN như chị Dung chốt 21/08/2026 điều 2:

	  1. Phiếu thu (Receive), Nợ 112 / Có 131, ghi nhận khoản khách đã chuyển
	     vào lúc đặt đơn. Không gán vào hoá đơn nào vì không có hoá đơn nào.
	  2. Phiếu chi (Pay), cùng khách cùng số tiền, trả lại khoản giữ hộ.

	Cả hai để NHÁP. Số dư 131 của mã "Khách lẻ Online" sau khi kế toán ghi
	cả hai phiếu sẽ về đúng như trước, và tra theo số đơn trong diễn giải
	thì thấy được cặp bút toán khớp nhau.

	KHÔNG ghi sổ hộ, KHÔNG xuất hoá đơn nào. Đơn này chưa từng có doanh thu
	nên không có gì để khử.
	"""
	_quyen()
	from vagabond.ban_hang import _otp_kiem
	from vagabond.hoan_tien import DT as HT
	from vagabond.hoan_tien import LOAI_HUY_PANCAKE

	ten = frappe.db.exists(DT, {"ma_don": str(ma_don or "").strip()})
	if not ten:
		frappe.throw("Chưa có đơn %s trong danh sách. Bấm Đồng bộ rồi thử lại."
			% ma_don)
	d = frappe.get_doc(DT, ten)
	if d.ho_so_hoan:
		frappe.throw("Đơn %s đã có hồ sơ hoàn tiền %s rồi." % (d.ma_don, d.ho_so_hoan))
	if flt(d.da_nhan) <= 0:
		frappe.throw("Chưa thấy tiền của đơn %s về tài khoản công ty. Không lập "
			"phiếu hoàn cho một khoản chưa vào." % d.ma_don)

	tien = flt(so_tien) or muc_hoan(d.da_nhan)
	if tien <= 0:
		frappe.throw("Số tiền hoàn phải lớn hơn 0.")
	if tien > flt(d.da_nhan) + 0.5:
		frappe.throw("Không hoàn quá số khách đã chuyển. Khách chuyển %s đ."
			% "{:,.0f}".format(flt(d.da_nhan)))
	tk = re.sub(r"[^0-9]", "", str(so_tk or ""))
	if not (tk and (ten_tk or "").strip() and (ngan_hang or "").strip()):
		frappe.throw("Còn thiếu thông tin tài khoản nhận tiền. Điền đủ tên ngân "
			"hàng, số tài khoản và tên chủ tài khoản của khách rồi gửi lại.")

	# SKILL_BANK_ROUTING / QT-31: đổi về tên chuẩn TRƯỚC khi ghi, vì `ngan_hang`
	# là ô Link trỏ vào doctype Bank. Gõ tay "VietinBank" rồi ghi thẳng thì
	# Frappe ném "Không tìm thấy Ngan hang: VietinBank" - đúng lỗi 22/08/2026.
	from vagabond import ngan_hang as nh

	ngan_hang = nh.chuan_hoa_hoac_bao(ngan_hang, "Ngân hàng nhận tiền")

	# Bằng chứng BẮT BUỘC (anh Việt chốt 23/08/2026). Tiền ra thật và người
	# bấm nút thường là Sales, nên phải có ảnh khung chat làm căn cứ. Chặn ở
	# máy chủ chứ không chỉ làm mờ nút trên màn: làm mờ nút thì ai gọi thẳng
	# cửa vẫn lập được phiếu trắng bằng chứng.
	#
	# Cả hai phép kiểm này đứng TRƯỚC _otp_kiem, để người dùng không bị tiêu
	# mất một mã OTP rồi mới biết là thiếu ảnh.
	tep_bc = _bang_chung_hop_le(bang_chung)
	if not tep_bc:
		frappe.throw(
			"Chưa có ảnh bằng chứng. Chụp khung chat khách xin huỷ, hoặc khung "
			"chat bếp báo không làm kịp, rồi tải lên ô Tải lên bằng chứng."
		)

	# Cùng một lớp khoá với luồng hoàn tiền đang chạy: tiền ra thật, và
	# người bấm ở đây thường là Sales chứ không phải kế toán. Sếp tự thao
	# tác thì khỏi nhập mã.
	cach = _otp_kiem(otp, "hoàn tiền đơn Pancake đã huỷ")

	khach = _khach_le_online()
	# Kiểm SỚM, dù ở đây không dựng phiếu tiền nữa: tài khoản ngân hàng công
	# ty chưa khai thì bước đối soát sau này mới hỏng, mà lúc đó người ngồi
	# trước màn là kế toán chứ không phải người vừa bấm. Nói ngay lúc gửi thì
	# Sales còn biết đường báo, chứ không phải chờ một phiếu mãi không nhúc
	# nhích rồi mới đi hỏi.
	_tk_ngan_hang(_cong_ty())
	mo_ta = dien_giai_don(d.ma_don, d.ma_hien_thi, d.ten_khach)
	noi_dung = noi_dung_chuyen_khoan(d.ma_don, d.ma_hien_thi)
	ghi = ("[Huỷ đơn Pancake] %s. Lý do: %s. %s" % (
		mo_ta, nhan_ly_do(ly_do) or "không ghi", (dien_giai or "").strip())).strip()

	ho_so = frappe.get_doc({
		"doctype": HT,
		"ma_don_pancake": d.ma_don,
		"khach": khach,
		"so_tien": tien,
		"loai_hoan": LOAI_HUY_PANCAKE,
		"ly_do": "Khac",
		"dien_giai": ghi,
		"trang_thai": "Cho chi",
		"ten_tk": (ten_tk or "").strip(),
		"so_tk": tk,
		"ngan_hang": (ngan_hang or "").strip() or None,
		"sdt": (sdt_khach or "").strip(),
		"nguoi_duyet": frappe.session.user,
		"cach_duyet": "Gui duyet tu man Don da huy (Pancake), duyet bang %s" % cach,
		"noi_dung_ck": noi_dung,
	})
	ho_so.flags.ignore_permissions = True
	ho_so.insert(ignore_permissions=True)

	# KHÔNG sinh phiếu tiền ở đây nữa (anh Việt chốt 23/08/2026).
	#
	# Trước đây chỗ này dựng luôn hai Payment Entry. Người bấm nút là Sales,
	# mà Sales không có quyền trên Payment Entry - và đúng là không nên có.
	# Kết quả: luồng chưa từng chạy được một lần nào kể từ khi dựng 21/08.
	# Ngày 23/08 chị Loan Anh bấm Gửi kế toán duyệt và nhận "không có quyền
	# truy cập doctype qua quyền vai trò cho tài liệu Phiếu thu/chi".
	#
	# Nay hai phiếu sinh muộn hơn một nhịp, tại bước đối soát bên màn Phiếu
	# hoàn tiền, dưới tay kế toán - người vốn có quyền. Xem đầy đủ ở
	# `hoan_tien._lap_cap_phieu_huy_don`.
	#
	# Ý của chị Dung chốt 21/08 giữ nguyên: vẫn đủ hai chân thu và chi, vẫn
	# ở dạng nháp, kế toán vẫn đính giấy báo Có và uỷ nhiệm chi rồi mới ghi
	# sổ. Chỉ khác thời điểm máy dựng ra chúng.

	# Ảnh bằng chứng đi theo hồ sơ. Phần chép sang phiếu chi để bên ERPNext
	# nhìn thấy ngay căn cứ thì làm lúc phiếu chi ra đời, không làm ở đây.
	_gan_bang_chung(tep_bc, ho_so.name)

	d.ho_so_hoan = ho_so.name
	d.trang_thai = DANG_HOAN
	d.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"ok": 1,
		"ho_so": ho_so.name,
		"so_tien": tien,
		"da_nhan": flt(d.da_nhan),
		"noi_dung_ck": noi_dung,
		"khach": khach,
		"ngan_hang": ngan_hang,
		"so_anh": len(tep_bc),
		"nhac": ("Hồ sơ đã nằm ở màn Phiếu hoàn tiền của kế toán. Chị Dung "
			"chuyển tiền, bấm Đối soát lệnh chi, máy sinh hai phiếu nháp rồi "
			"chị đính uỷ nhiệm chi và ghi sổ."),
	}

# -*- coding: utf-8 -*-
"""Tin Zalo tự động cho khách theo kịch bản (v621).

VÌ SAO CÓ TỆP NÀY
-----------------
Anh Việt 29/10/2026 muốn ERP thành trung tâm duy nhất gửi tin cho khách, thay
phần "Kịch bản CSKH" của CRM Fabi/iPOS: sau mua hàng, sinh nhật, lâu chưa quay
lại. Đợt 1 anh chọn ba kịch bản, tự động hoàn toàn có trần, tin khuyến mãi chỉ
gửi khách đã đồng ý nhận tin Zalo.

Luật Zalo (đọc kỹ trước khi đổi, kiểm 29/10/2026 trên tài liệu chính thức):
  - Từ 01/03/2026 mọi tin gửi qua API (trừ tin tư vấn trong 7 ngày sau tương
    tác) phải theo MẪU đã đăng ký và được Zalo duyệt (ZBS Template Message).
    Câu chữ nằm cố định trong mẫu, máy chỉ điền tham số. Vì vậy màn không cho
    soạn tin tự do như iPOS: mỗi kịch bản gắn một mã mẫu.
  - Mẫu tag 2 (chăm sóc khách hàng) không giới hạn số tin theo tháng.
  - Mẫu tag 3 (hậu mãi, có voucher): khách phải nhận ít nhất một tin tag 1
    hoặc 2 trong 6 tháng (lỗi -140); hạn mức tháng của OA bằng 1/6 số tin tag
    1 và 2 đã gửi hai tháng trước; mỗi khách tối đa 1 tin một ngày. Hạn mức còn
    0 thì máy KHÔNG phát voucher, để dòng chờ và nói rõ vì sao.
  - Mẫu không gửi được 22h tới 6h (lỗi -133). Màn cho đặt giờ gửi trong
    khoảng 6h tới 22h.
  - v645 (anh Việt 08/11/2026): tin cho khách KHÔNG gửi sau 20:00, giờ khách đi
    ngủ (GIO_TOI_DA). Zalo nay cho nhận 24/24 nhưng tiệm tự giữ giờ này.

v645 (anh Việt 08/11/2026) mở rộng thành bộ ưu đãi tự động theo hành trình
khách, đọc ở `docs/huong-dan/uu-dai-zalo-tu-dong.md`:
  - "Sau mua" là lúc khách NHẬN đơn: bill tại quầy lúc tính tiền xong, đơn giao
    lúc Pancake chuyển Đã nhận (đồng bộ dựng hoá đơn nháp đúng lúc đó). Không
    chờ hoá đơn ghi sổ cuối ngày.
  - Thứ tự KICH_BAN là thứ tự ưu tiên khi hạn mức tin ưu đãi của Zalo ít.
  - Mỗi khách tối đa một tin ưu đãi mỗi 7 ngày (TRAN_TUAN_NGAY), trừ đền bù.
  - Kịch bản đo hiệu quả giữ một phần khách làm nhóm đối chứng (doi_chung %).

Ba lớp chống gửi trùng: khoá duy nhất trên sổ tin (một hoá đơn một tin cảm ơn,
một khách một tin sinh nhật mỗi năm, một lần vắng mặt một tin mời quay lại),
dòng sổ ghi TRƯỚC khi gọi Zalo, và việc nền xếp theo job_id có chống trùng.

Phần THUẦN ở đầu tệp (không chạm Frappe) để bộ kiểm tầng khung gọi thẳng.
Phần chạm hệ nạp frappe trong thân hàm.
"""

import json
import re
from datetime import date, datetime, timedelta

DT_KB = "Vagabond Kich Ban Zalo"
DT_TIN = "Vagabond Tin Zalo Khach"

# Trạng thái một dòng sổ tin.
TT_CHO, TT_GUI, TT_LOI, TT_BO = "Chờ gửi", "Đã gửi", "Lỗi", "Bỏ qua"
TT_TIN = (TT_CHO, TT_GUI, TT_LOI, TT_BO)

# Ba kịch bản đợt 1. "ma" là khoá nội bộ, không hiện cho người dùng.
# "km" = 1 là tin khuyến mãi (tag 3, có voucher): chỉ gửi khách đã đồng ý.
KICH_BAN = (
	# kieu: "" tin chăm sóc không mã; "phat" máy phát mã mới lúc gửi; "co_san"
	# gửi một mã đã có (nhắc hạn, đền bù). tran_tuan: tính vào trần 1 tin ưu
	# đãi mỗi tuần. doi_chung: % khách giữ lại không gửi để đo hiệu quả.
	# nhan_ngay, goi_y_ngay, nhan_nhac: chữ của ô số ngày trên màn.
	{
		"ma": "sau_mua",
		"ten": "Cảm ơn khi khách nhận đơn, báo điểm",
		"giai_thich": "Gửi một lần cho mỗi đơn lúc khách nhận: bill tại quầy khi tính tiền xong, đơn giao khi Pancake chuyển Đã nhận. Mã đơn, điểm của đơn, tổng điểm, hạng. Tin chăm sóc, không có ưu đãi.",
		"km": 0, "kieu": "", "mau": "659376", "so_ngay": 0, "nhac_lai": 0, "han": 14, "doi_chung": 0, "tran_tuan": 0,
	},
	# v652 (anh Việt 12/11/2026): báo hoàn điểm đơn web; tin chăm sóc, không voucher.
	{
		"ma": "hoan_diem",
		"ten": "Báo đã hoàn điểm cho đơn web không thành",
		"giai_thich": "Khách dùng điểm khi đặt trên web mà đơn bị huỷ hoặc không gửi được: máy hoàn điểm và báo khách số điểm đã hoàn, mã đơn.",
		"km": 0, "kieu": "", "mau": "", "so_ngay": 0, "nhac_lai": 0, "han": 0, "doi_chung": 0, "tran_tuan": 0,
	},
	{
		"ma": "den_bu_nhe",
		"ten": "Đền bù sự cố mức nhẹ",
		"giai_thich": "Quản lý bấm Cấp mã đền bù ở màn Khuyến mãi (giao trễ, thiếu nến hay thiệp). Máy phát mã ngay, khách đã đồng ý thì gửi Zalo.",
		"km": 1, "kieu": "co_san", "mau": "", "so_ngay": 0, "nhac_lai": 0, "han": 60, "doi_chung": 0, "tran_tuan": 0,
	},
	{
		"ma": "den_bu_vua",
		"ten": "Đền bù sự cố mức vừa",
		"giai_thich": "Sai trang trí, sai lời chúc, thiếu món (giao bù món thiếu trước). Quản lý cấp ở màn Khuyến mãi.",
		"km": 1, "kieu": "co_san", "mau": "", "so_ngay": 0, "nhac_lai": 0, "han": 60, "doi_chung": 0, "tran_tuan": 0,
	},
	{
		"ma": "den_bu_nang",
		"ten": "Đền bù sự cố mức nặng",
		"giai_thich": "Bánh hỏng không dùng được: làm lại hoặc hoàn tiền trước, mã này là phần thêm. Quản lý cấp ở màn Khuyến mãi.",
		"km": 1, "kieu": "co_san", "mau": "", "so_ngay": 0, "nhac_lai": 0, "han": 60, "doi_chung": 0, "tran_tuan": 0,
	},
	{
		"ma": "sinh_nhat",
		"ten": "Chúc mừng sinh nhật kèm voucher",
		"giai_thich": "Gửi trước sinh nhật khách số ngày đã đặt, kèm một mã voucher riêng dùng một lần.",
		"km": 1, "kieu": "phat", "mau": "659377", "so_ngay": 3, "nhac_lai": 0, "han": 14, "doi_chung": 0, "tran_tuan": 1,
		"nhan_ngay": "GỬI TRƯỚC SINH NHẬT (NGÀY)", "goi_y_ngay": "Để 0 là gửi đúng ngày sinh nhật.",
	},
	{
		"ma": "nhac_dip",
		"ten": "Nhắc dịp năm sau",
		"giai_thich": "Năm ngoái khách đặt bánh giao từ 300.000đ vào một ngày: trước ngày đó năm nay máy gửi lời nhắc đặt sớm kèm mã.",
		"km": 1, "kieu": "phat", "mau": "", "so_ngay": 10, "nhac_lai": 0, "han": 12, "doi_chung": 0, "tran_tuan": 1,
		"nhan_ngay": "GỬI TRƯỚC NGÀY DỊP (NGÀY)", "goi_y_ngay": "Tính tới đúng ngày khách nhận bánh năm ngoái.",
	},
	{
		"ma": "don_thu_hai",
		"ten": "Đơn thứ hai: Hẹn gặp lại",
		"giai_thich": "Khách vừa nhận xong đơn đầu tiên: sau số ngày đã đặt, máy gửi mã mời quay lại lần hai.",
		"km": 1, "kieu": "phat", "mau": "", "so_ngay": 3, "nhac_lai": 0, "han": 21, "doi_chung": 10, "tran_tuan": 1,
		"nhan_ngay": "GỬI SAU ĐƠN ĐẦU (NGÀY)", "goi_y_ngay": "Tính từ ngày khách nhận đơn đầu tiên.",
	},
	{
		"ma": "gioi_thieu",
		"ten": "Cảm ơn khách giới thiệu bạn",
		"giai_thich": "Bạn mới gõ số điện thoại của khách ở ô Mã giới thiệu khi đặt đơn đầu tiên trên web. Bạn nhận bánh xong thì khách giới thiệu nhận mã. Khách mua lại gõ số thì không tính. Tối đa 5 lượt mỗi tháng.",
		"km": 1, "kieu": "phat", "mau": "", "so_ngay": 0, "nhac_lai": 0, "han": 30, "doi_chung": 0, "tran_tuan": 1,
	},
	{
		"ma": "quay_lai",
		"ten": "Mời khách lâu chưa quay lại",
		"giai_thich": "Khách quá số ngày đã đặt chưa mua thì gửi lời mời kèm một mã voucher riêng.",
		"km": 1, "kieu": "phat", "mau": "659378", "so_ngay": 45, "nhac_lai": 120, "han": 14, "doi_chung": 10, "tran_tuan": 1,
		"nhan_ngay": "KHÁCH CHƯA MUA BAO NHIÊU NGÀY THÌ GỬI", "goi_y_ngay": "Tính từ lần mua cuối, máy cập nhật mỗi đêm.",
		"nhan_nhac": "KHÔNG GỬI LẠI TRONG (NGÀY)",
	},
	{
		"ma": "quay_lai_2",
		"ten": "Mời khách vắng lâu, mốc hai",
		"giai_thich": "Mốc sau của lời mời quay lại, ưu đãi mạnh hơn và hạn ngắn hơn.",
		"km": 1, "kieu": "phat", "mau": "", "so_ngay": 90, "nhac_lai": 180, "han": 10, "doi_chung": 10, "tran_tuan": 1,
		"nhan_ngay": "KHÁCH CHƯA MUA BAO NHIÊU NGÀY THÌ GỬI", "goi_y_ngay": "Tính từ lần mua cuối, máy cập nhật mỗi đêm.",
		"nhan_nhac": "KHÔNG GỬI LẠI TRONG (NGÀY)",
	},
	{
		"ma": "nhac_han",
		"ten": "Nhắc mã sắp hết hạn",
		"giai_thich": "Mã riêng của khách (Ví quà, tin Zalo, đền bù) còn số ngày đã đặt mà chưa dùng: nhắc đúng một lần.",
		"km": 1, "kieu": "co_san", "mau": "", "so_ngay": 3, "nhac_lai": 0, "han": 0, "doi_chung": 0, "tran_tuan": 1,
		"nhan_ngay": "NHẮC KHI MÃ CÒN (NGÀY)", "goi_y_ngay": "Mã đã dùng thì không nhắc.",
	},
	# v652: nhắc điểm sắp hết hạn, xếp sau cùng (tin chăm sóc, không voucher).
	{
		"ma": "nhac_diem",
		"ten": "Nhắc điểm sắp hết hạn",
		"giai_thich": "Điểm hết hạn cuốn chiếu 12 tháng: trước số ngày đã đặt, máy nhắc khách số điểm sắp hết hạn và ngày hết hạn, để khách đặt bánh trên web dùng điểm. Mỗi khách tối đa một tin trong khoảng đó.",
		"km": 0, "kieu": "", "mau": "", "so_ngay": 30, "nhac_lai": 0, "han": 0, "doi_chung": 0, "tran_tuan": 0,
		"nhan_ngay": "NHẮC TRƯỚC KHI ĐIỂM HẾT HẠN (NGÀY)", "goi_y_ngay": "Chỉ nhắc khi hạn điểm đang chạy cuốn chiếu.",
	},
)
MA_KB = tuple(k["ma"] for k in KICH_BAN)

# Mặc định chung khi tạo dòng cấu hình lần đầu.
MAC_DINH = {"tran_ngay": 300, "gio_tu": 8, "gio_den": 20, "han_ngay": 14}

# v645: không gửi tin cho khách sau 20:00 (anh Việt 08/11/2026), kể cả khi người
# cài gõ giờ đóng muộn hơn.
GIO_TOI_DA = 20
# v645: trần tin ưu đãi của một khách, tính trên mọi kịch bản tran_tuan.
TRAN_TUAN_NGAY = 7
# v645: khách giới thiệu bạn nhận tối đa ngần này mã mỗi tháng.
GIOI_THIEU_TOI_DA_THANG = 5
# v645: nhắc dịp chỉ cho đơn giao (Pancake) từ ngần này trở lên: đơn bánh cho
# một dịp, không phải ly cà phê tại quầy.
NGUONG_DIP = 300000
# v645: khách mua lại trong ngần này ngày trước ngày gửi thì không nhắc dịp.
DIP_DA_MUA_GAN = 14
# Lý do Bỏ qua của nhóm đối chứng bắt đầu bằng chữ này (báo cáo đếm theo nó).
LY_DO_DOI_CHUNG = "Nhóm đối chứng"

# Dòng chờ quá ngần này giờ thì bỏ: tin cảm ơn tới trễ hai ngày là vô duyên,
# tin sinh nhật tới sau sinh nhật là sai.
CHO_TOI_DA_GIO = 48

# Mã lỗi Zalo hay gặp -> câu cho người đọc màn. Nguồn: bảng mã lỗi ZNS/ZBS.
LOI_ZALO = {
	-1: "Không gọi được Zalo (mất mạng hoặc khoá truy cập lỗi), tin để chờ lượt sau.",
	-108: "Số điện thoại không hợp lệ.",
	-114: "Khách không nhận được tin (tài khoản Zalo không hoạt động, tắt nhận tin, hoặc Zalo bản cũ).",
	-115: "Tài khoản gửi tin Zalo hết tiền. Nạp thêm trên Zalo Cloud Account.",
	-118: "Số này chưa dùng Zalo hoặc tài khoản đã khoá.",
	-119: "Tài khoản Zalo này không nhận được tin doanh nghiệp.",
	-124: "Khoá truy cập Zalo hết hạn, máy sẽ tự làm mới ở lượt sau.",
	-131: "Mẫu tin chưa được Zalo duyệt.",
	-133: "Mẫu tin không được gửi từ 22h tới 6h.",
	-137: "Thanh toán phí gửi tin Zalo thất bại (ví hết tiền).",
	-139: "Khách đã từ chối nhận loại tin này.",
	-140: "Zalo chưa cho gửi tin khuyến mãi tới khách này (khách chưa nhận tin chăm sóc nào trong 6 tháng).",
	-141: "Khách đã từ chối nhận tin từ OA.",
	-144: "OA đã gửi hết hạn mức tin trong ngày.",
	-1441: "OA đã dùng hết hạn mức tin khuyến mãi của tháng.",
	-146: "Mẫu tin bị Zalo khoá vì chất lượng gửi thấp.",
	-147: "Mẫu tin đã hết hạn mức gửi trong ngày.",
	-1471: "Khách đã nhận đủ tin khuyến mãi trong tháng.",
	# v646 (Minh Vũ báo 09/11/2026, gửi thử mẫu 659376): ba mã dưới là dữ liệu máy
	# điền KHÔNG khớp mẫu, lỗi của máy chứ không của khách: khách nào cũng hỏng y hệt.
	-1121: "Dữ liệu tin dài hơn ô của mẫu Zalo",
	-1122: "Thiếu dữ liệu mẫu Zalo đòi",
	-1124: "Dữ liệu tin sai định dạng mẫu Zalo",
}
# Lỗi dữ liệu không khớp mẫu: dừng lượt của kịch bản, để dòng chờ (sửa xong máy
# gửi tiếp trong hạn chờ) và báo Marketing một lần mỗi ngày mỗi kịch bản.
LOI_MAU_DU_LIEU = {-1121, -1122, -1124}
# Lỗi của cả lượt (không phải của riêng khách): gặp là dừng lượt, để dòng chờ.
# -1 là mã của chính máy (zalo.gui_mau: mất mạng, không lấy được khoá, phản
# hồi không đọc được): loại vĩnh viễn từng dòng thì một lần mất mạng làm mất
# cả hàng đợi, vì khoá chống trùng chặn quét lại (Codex PR #517 vòng 2).
LOI_DUNG_LUOT = {-1, -115, -124, -131, -137, -144, -1441, -146, -147, -133} | LOI_MAU_DU_LIEU

TRANG_THAI_MAU = {
	"ENABLE": "Đã duyệt",
	"PENDING_REVIEW": "Đang chờ Zalo duyệt",
	"REJECT": "Bị từ chối",
	"DISABLE": "Đã tắt",
}


# ================================================================ phần thuần

def kich_ban(ma):
	"""Khai báo cố định của một kịch bản. THUẦN. Mã lạ trả None."""
	for k in KICH_BAN:
		if k["ma"] == ma:
			return k
	return None


def so_nguyen(v, mac_dinh=0):
	"""Ô số người điền tay -> int. THUẦN. Rỗng, chữ, số âm đều về mặc định."""
	try:
		n = int(float(str(v).strip().replace(",", ".")))
	except (TypeError, ValueError):
		return mac_dinh
	return n if n >= 0 else mac_dinh


def gio_hop_le(tu, den):
	"""Khoảng giờ gửi đã kẹp vào 6h tới GIO_TOI_DA (20h, anh Việt 08/11/2026;
	luật Zalo cũ là 22h). THUẦN.

	Người điền tay có thể gõ 20 rồi 8, hay 0 tới 24: kẹp và đổi chỗ chứ không
	ném lỗi, vì một ô sai không được làm tắt cả kịch bản.
	"""
	a = min(max(so_nguyen(tu, MAC_DINH["gio_tu"]), 6), GIO_TOI_DA)
	b = min(max(so_nguyen(den, MAC_DINH["gio_den"]), 6), GIO_TOI_DA)
	if a > b:
		a, b = b, a
	if a == b:
		a, b = MAC_DINH["gio_tu"], MAC_DINH["gio_den"]
	return a, b


def trong_gio(luc, tu, den):
	"""Lúc này có nằm trong giờ gửi [tu, den) không. THUẦN."""
	a, b = gio_hop_le(tu, den)
	return a <= luc.hour < b


def ngay_cua(v):
	"""Chuỗi hoặc date hoặc datetime -> date. THUẦN. Không đọc được thì None."""
	if isinstance(v, datetime):
		return v.date()
	if isinstance(v, date):
		return v
	s = str(v or "").strip()[:10]
	try:
		return datetime.strptime(s, "%Y-%m-%d").date()
	except ValueError:
		return None


def sinh_nhat_nam(sn, nam):
	"""Ngày sinh nhật của khách trong năm `nam`. THUẦN. 29/02 năm thường là 28/02."""
	sn = ngay_cua(sn)
	if not sn:
		return None
	try:
		return date(nam, sn.month, sn.day)
	except ValueError:
		return date(nam, 2, 28)


def den_sinh_nhat(sn, hom_nay, so_ngay):
	"""Khách có sinh nhật đúng `so_ngay` ngày nữa không. THUẦN.

	Tính theo năm của ngày đích, nên gửi trước 3 ngày cho người sinh 01/01 là
	gửi ngày 29/12 năm trước.
	"""
	hom_nay = ngay_cua(hom_nay)
	if not hom_nay:
		return False
	dich = hom_nay + timedelta(days=so_nguyen(so_ngay))
	d = sinh_nhat_nam(sn, dich.year)
	return bool(d and d == dich)


def vang_mat_du(lan_cuoi, hom_nay, so_ngay, bien=3):
	"""Khách vừa vắng mặt đủ `so_ngay` (trong cửa sổ `bien` ngày). THUẦN.

	Cửa sổ vài ngày để một lượt việc nền bị lỡ không làm sót khách; khoá sổ
	tin theo ngày mua cuối nên trong cửa sổ cũng chỉ gửi một lần.
	"""
	lc, hn = ngay_cua(lan_cuoi), ngay_cua(hom_nay)
	n = so_nguyen(so_ngay)
	if not lc or not hn or n <= 0:
		return False
	vang = (hn - lc).days
	return n <= vang < n + max(1, so_nguyen(bien, 3))


def qua_sinh_nhat(ngay_sinh, nam, hom_nay):
	"""Sinh nhật của dòng chờ (năm `nam` trong khoá) đã qua chưa. THUẦN.

	Dòng chờ hết hạn chung sau 48 giờ, nhưng lời chúc sinh nhật gửi muộn một
	ngày là sai (Codex PR #517 vòng 5). Không còn ngày sinh thì coi như qua.
	"""
	d, hn = sinh_nhat_nam(ngay_sinh, so_nguyen(nam)) if so_nguyen(nam) else None, ngay_cua(hom_nay)
	if not d or not hn:
		return True
	return hn > d


def con_vang_mat(lan_mua_cuoi, hom_nay, so_ngay):
	"""Ngay lúc gửi: khách còn vắng đủ `so_ngay` không. THUẦN.

	Dòng mời quay lại được tạo từ ngày mua cuối của đêm trước; khách có thể
	đã mua lại trước giờ gửi (Codex PR #517 vòng 4). Chưa có lần mua nào thì
	coi như vẫn vắng (dòng đã qua bước quét theo hồ sơ CRM).
	"""
	lc, hn = ngay_cua(lan_mua_cuoi), ngay_cua(hom_nay)
	if not lc or not hn:
		return True
	return (hn - lc).days >= max(1, so_nguyen(so_ngay, 60))


def khoa_tin(ma, khach="", hoa_don="", moc=""):
	"""Khoá duy nhất của một tin trên sổ. THUẦN.

	sau_mua: một hoá đơn một tin. sinh_nhat: một khách một tin mỗi năm (moc là
	năm). quay_lai: một lần vắng mặt một tin (moc là ngày mua cuối).
	v645: gioi_thieu một hoá đơn của bạn mới một tin; đền bù một đơn gốc một mã
	cho MỌI mức (đổi mức không cấp thêm mã); nhắc hạn một mã một lần (moc là mã).
	"""
	if ma in ("sau_mua", "gioi_thieu"):
		return "%s:%s" % (ma, hoa_don)
	if str(ma or "").startswith("den_bu"):
		return "den_bu:%s" % hoa_don
	if ma == "nhac_han":
		return "nhac_han:%s" % moc
	return "%s:%s:%s" % (ma, khach, moc)


def hoa_don_con_nhan(docstatus, ma_pancake="", huy=0, tra=0):
	"""Hoá đơn còn là một đơn khách đã nhận không (cùng ý DK_DA_NHAN). THUẦN.

	Bill tại quầy phải đã ghi sổ; đơn giao (có mã Pancake) nháp cũng tính vì
	đồng bộ chỉ dựng nháp khi Pancake đã chuyển Đã nhận. Huỷ, trả hàng: không.
	"""
	if so_nguyen(huy) or so_nguyen(tra):
		return False
	ds = so_nguyen(docstatus, -1)
	return ds == 1 or (ds == 0 and bool(str(ma_pancake or "").strip()))


def trong_doi_chung(khach, phan_tram):
	"""Khách có nằm trong nhóm đối chứng `phan_tram`% không. THUẦN.

	Cố định theo mã khách (băm), không ngẫu nhiên mỗi lượt: một khách luôn ở
	cùng một phía, nên so "nhận tin" với "không nhận tin" mới công bằng.
	"""
	import hashlib

	pt = min(max(so_nguyen(phan_tram), 0), 50)
	if not pt or not str(khach or "").strip():
		return False
	h = int(hashlib.sha1(("vgb-doi-chung:" + str(khach)).encode("utf-8")).hexdigest()[:8], 16)
	return h % 100 < pt


def ngay_dip_nam_truoc(dich):
	"""Ngày năm ngoái tương ứng ngày `dich` năm nay. THUẦN. 29/02 lùi về 28/02."""
	d = ngay_cua(dich)
	if not d:
		return None
	try:
		return d.replace(year=d.year - 1)
	except ValueError:
		return date(d.year - 1, 2, 28)


def ma_don_cho_khach(ten_hoa_don, ma_pancake=""):
	"""Mã đơn khách nhận ra trong tin: mã Pancake nếu là đơn giao, không thì mã
	hoá đơn. THUẦN."""
	return str(ma_pancake or "").strip() or str(ten_hoa_don or "").strip()


def ten_goi(ten):
	"""Tên điền vào tin. THUẦN.

	Tên nhập từ iPOS có khi là số điện thoại, có khi viết hoa toàn bộ, có khi
	trống. Không được để Zalo hiện "Chúc mừng sinh nhật 0901234567".
	"""
	t = re.sub(r"\s+", " ", str(ten or "")).strip()
	if not t or re.fullmatch(r"[\d\s+().-]+", t):
		return "Quý khách"
	if t.isupper():
		t = " ".join(w.capitalize() for w in t.lower().split(" "))
	return t


def cat(s, n):
	"""Cắt chuỗi về n ký tự, không để thừa khoảng trắng. THUẦN."""
	s = re.sub(r"\s+", " ", str(s if s is not None else "")).strip()
	return s if not n or len(s) <= n else s[:n].rstrip()


def so_chuoi(v):
	"""Số -> chuỗi chữ số nguyên (tham số NUMBER của Zalo). THUẦN.

	Nhận cả số đã định dạng kiểu Việt ("450.000đ", "9.000"): bỏ mọi thứ không
	phải chữ số, vì dấu chấm ở đây là dấu ngăn nghìn chứ không phải thập phân.
	"""
	if isinstance(v, (int, float)):
		return str(int(round(v)))
	x = re.sub(r"\D", "", str(v or ""))
	return x.lstrip("0") or "0"


def tien_vn(v):
	"""450000 -> '450.000đ'. THUẦN."""
	try:
		n = int(round(float(v or 0)))
	except (TypeError, ValueError):
		n = 0
	return "{:,}".format(n).replace(",", ".") + "đ"


def ngay_vn(v):
	"""Ngày -> 'dd/mm/yyyy'. THUẦN."""
	d = ngay_cua(v)
	return d.strftime("%d/%m/%Y") if d else ""


def chuan_tham_so(gia_tri, kieu, toi_da):
	"""Một giá trị -> đúng kiểu tham số của mẫu Zalo. THUẦN.

	kieu, toi_da đọc từ chính mẫu đã duyệt (template/info/v2), không đoán: gửi
	sai kiểu hay dài quá là Zalo từ chối CẢ tin (-1121, -1124).
	"""
	k = str(kieu or "STRING").upper()
	# v646: ô Tiền tệ (VNĐ) của mẫu báo kiểu CURRENCY, cũng chỉ nhận chữ số trơn
	# (450000). Gửi "450.000đ" là Zalo từ chối CẢ tin (-1124, Minh Vũ 09/11/2026).
	if k in ("NUMBER", "CURRENCY"):
		return so_chuoi(gia_tri)
	if k == "DATE":
		return ngay_vn(gia_tri) or cat(gia_tri, 10)
	return cat(gia_tri, so_nguyen(toi_da, 0) or 30)


def du_lieu_mau(gia_tri, tham_so):
	"""Giá trị nghiệp vụ -> template_data theo bộ tham số của mẫu. THUẦN.

	Trả (data, thieu). `thieu` là tên tham số mẫu đòi mà máy không có: khi đó
	KHÔNG gửi, vì Zalo sẽ từ chối cả tin (-1122).
	"""
	data, thieu = {}, []
	for p in tham_so or []:
		ten = p.get("name")
		if not ten:
			continue
		v = (gia_tri or {}).get(ten)
		if v is None or str(v).strip() == "":
			if p.get("require", True):
				thieu.append(ten)
			continue
		data[ten] = chuan_tham_so(v, p.get("type"), p.get("maxLength"))
	return data, thieu


def mo_ta_uu_dai(km, ten_dat="", dieu_kien_dat=""):
	"""Tên ưu đãi (<=30) và điều kiện (<=40) hiện trong ô voucher. THUẦN.

	Ô người điền trên màn thắng; để trống thì máy tự viết từ chương trình
	khuyến mãi: "Giảm 10%", "Giảm 50.000đ", "Hoá đơn từ 300.000đ".
	"""
	km = km or {}
	ten = cat(ten_dat, 30)
	if not ten:
		try:
			gt = float(km.get("gia_tri") or 0)
		except (TypeError, ValueError):
			gt = 0
		if gt > 0 and km.get("kieu_giam") == "Phan tram":
			ten = "Giảm %s%%" % (int(gt) if gt == int(gt) else gt)
		elif gt > 0:
			ten = "Giảm " + tien_vn(gt)
		else:
			ten = cat(km.get("ten") or "Ưu đãi thành viên", 30)
	dk = cat(dieu_kien_dat, 30)
	if not dk:
		try:
			tt = float(km.get("hd_toi_thieu") or 0)
		except (TypeError, ValueError):
			tt = 0
		dk = ("Hoá đơn từ " + tien_vn(tt)) if tt > 0 else "Dùng 1 lần cho 1 hoá đơn"
	return cat(ten, 30), cat(dk, 30)


def y_nghia_loi(j):
	"""Phản hồi Zalo -> (mã, câu cho người đọc). THUẦN. Mã 0 là thành công."""
	j = j if isinstance(j, dict) else {}
	try:
		ma = int(j.get("error"))
	except (TypeError, ValueError):
		return -1, "Zalo không trả lời rõ ràng."
	if ma == 0:
		return 0, ""
	cau = LOI_ZALO.get(ma) or (j.get("message") or "Zalo từ chối tin")
	if ma in LOI_MAU_DU_LIEU and j.get("message"):
		# Câu của Zalo nêu đúng tên ô hỏng ("tong_tien has invalid format"): giữ lại.
		cau = "%s: %s" % (cau, cat(j.get("message"), 120))
	return ma, ("%s (mã %s)" % (cau, ma))[:300]


def chu_tim(tim):
	"""Chữ người gõ vào ô tìm, đã gọn khoảng trắng và bỏ dấu %. THUẦN."""
	return re.sub(r"\s+", " ", str(tim or "")).replace("%", "").strip()


def mau_sdt_tim(tim):
	"""Chữ tìm gần như toàn số -> các mẫu like cho số điện thoại. THUẦN.

	Số lưu nơi thì 09..., nơi thì 84...: gõ kiểu nào cũng ra cả hai.
	Không phải số (vd mã hoá đơn có vài chữ số) thì rỗng.
	"""
	t = chu_tim(tim)
	so = re.sub(r"\D", "", t)
	if len(so) < 4 or len(so) < len(re.sub(r"[\s.\-+]", "", t)) - 1:
		return []
	ds = [so]
	if so.startswith("0") and len(so) >= 9:
		ds.append("84" + so[1:])
	elif so.startswith("84") and len(so) >= 10:
		ds.append("0" + so[2:])
	return ["%" + x + "%" for x in ds]


def dk_tim_tin(tim, khach_khop=None):
	"""Ô tìm của sổ tin -> điều kiện hoặc cho frappe.get_all. THUẦN.

	Tìm theo tên khách, mã khách, hoá đơn, voucher, số điện thoại trên sổ;
	`khach_khop` là các mã khách mà tên hay số trong hồ sơ khớp chữ tìm, để
	ra cả dòng Chờ gửi, Bỏ qua chưa ghi tên và số (Codex PR #517 vòng 3).
	"""
	t = chu_tim(tim)
	if not t:
		return []
	g = "%" + t + "%"
	dk = [["ten_khach", "like", g], ["khach", "like", g], ["hoa_don", "like", g], ["voucher", "like", g]]
	dk += [["sdt", "like", m] for m in mau_sdt_tim(t)]
	if khach_khop:
		dk.append(["khach", "in", list(khach_khop)])
	return dk


def _khach_khop(tim):
	"""Mã khách có tên hay số điện thoại (Customer, hồ sơ CRM) khớp chữ tìm."""
	t = chu_tim(tim)
	if not t:
		return []
	sdt = mau_sdt_tim(t)
	ma = set(frappe.get_all("Customer", or_filters=[["customer_name", "like", "%" + t + "%"]] + [["mobile_no", "like", m] for m in sdt],
		pluck="name", limit_page_length=300))
	if sdt:
		ma.update(frappe.get_all("Vagabond Ho So CRM", or_filters=[["sdt", "like", m] for m in sdt], pluck="name", limit_page_length=300))
	return sorted(ma)[:500]


def con_duoc_gui(tran_ngay, da_gui_hom_nay):
	"""Số tin còn được gửi hôm nay theo trần. THUẦN. Trần 0 là không gửi."""
	return max(0, so_nguyen(tran_ngay) - so_nguyen(da_gui_hom_nay))


def doc_tham_so(v):
	"""Ô JSON tham số mẫu đã lưu -> danh sách. THUẦN. Hỏng thì rỗng."""
	if isinstance(v, list):
		return v
	try:
		x = json.loads(v or "[]")
	except (TypeError, ValueError):
		return []
	return x if isinstance(x, list) else []


def mau_san_sang(cau_hinh):
	"""Kịch bản có gửi được không, và nếu không thì vì sao. THUẦN.

	Trả (được, lý do). Thứ tự lý do theo việc người dùng phải làm trước.
	"""
	c = cau_hinh or {}
	if not int(c.get("bat") or 0):
		return False, "Kịch bản đang tắt."
	if not str(c.get("ma_mau") or "").strip():
		return False, "Chưa gắn mã mẫu Zalo."
	tt = c.get("mau_trang_thai") or ""
	if tt != "ENABLE":
		return False, "Mẫu tin %s." % (TRANG_THAI_MAU.get(tt) or "chưa kiểm trạng thái").lower()
	kb = kich_ban(c.get("ma")) or {}
	if kb.get("km") and kb.get("kieu") != "co_san" and not str(c.get("ctkm") or "").strip():
		return False, "Chưa chọn chương trình khuyến mãi để phát voucher."
	return True, ""


def ctkm_phat_duoc(km, hom_nay, han_ngay):
	"""Chương trình có phát được mã dùng một lần hôm nay không, và hạn mã. THUẦN.

	Trả (hạn, lý do). Hạn là None khi không phát được. Quầy và web
	(khuyen_mai._hop_thoi_gian) từ chối chương trình chưa bắt đầu hay đã qua
	den_ngay, nên phát mã lúc đó là gửi quà không dùng được (Codex PR #517).
	Hạn mã kẹp theo ngày kết thúc chương trình và hạn mã mặc định (han_ma)
	để tin không hứa một ngày quầy sẽ từ chối.
	"""
	km = km or {}
	ten = km.get("ten") or km.get("name") or ""
	if not km.get("name"):
		return None, "Không còn chương trình khuyến mãi đã chọn."
	if km.get("cach_ma") != "Ma dung mot lan" or not int(km.get("bat") or 0):
		return None, "Chương trình %s phải đang bật và để cách phát mã là Mã dùng một lần." % ten
	hom_nay = ngay_cua(hom_nay)
	tu, den, han_ma = ngay_cua(km.get("tu_ngay")), ngay_cua(km.get("den_ngay")), ngay_cua(km.get("han_ma"))
	if tu and hom_nay < tu:
		return None, "Chương trình %s chưa tới ngày bắt đầu %s." % (ten, ngay_vn(tu))
	if den and hom_nay > den:
		return None, "Chương trình %s đã hết hạn ngày %s." % (ten, ngay_vn(den))
	han = hom_nay + timedelta(days=max(1, so_nguyen(han_ngay, MAC_DINH["han_ngay"])))
	for tran in (den, han_ma):
		if tran and han > tran:
			han = tran
	if han < hom_nay:
		return None, "Hạn mã của chương trình %s đã qua (%s)." % (ten, ngay_vn(han))
	return han, ""


def ly_do_khong_gui_lai(km, hom_nay):
	"""Mã Ví quà khách đang giữ còn gửi lại được không. THUẦN.

	Trả '' nếu được. Quầy (khuyen_mai._tra_ma) từ chối mã của chương trình
	đang tắt hay đã qua ngày kết thúc, nên gửi lại lúc đó là gửi quà khách
	không dùng được (Codex PR #520 vòng 5). Không xét hạn mã mặc định của
	chương trình vì mã đã phát có hạn riêng.
	"""
	km = km or {}
	ten = km.get("ten") or km.get("name") or ""
	if not int(km.get("bat") or 0):
		return "Chương trình %s đang tắt, không gửi lại mã Ví quà." % ten
	den = ngay_cua(km.get("den_ngay"))
	if den and ngay_cua(hom_nay) > den:
		return "Chương trình %s đã hết hạn ngày %s, không gửi lại mã Ví quà." % (ten, ngay_vn(den))
	return ""


def xoa_kiem_mau(ly_do="Đang hỏi Zalo mẫu mới."):
	"""Các ô kết quả kiểm mẫu phải xoá khi đổi mã mẫu. THUẦN.

	Trạng thái duyệt và bộ tham số là của mẫu CŨ; giữ lại thì máy gửi mẫu mới
	bằng tham số cũ tới lần kiểm sau (Codex PR #517).
	"""
	return {"mau_trang_thai": "", "mau_tham_so": "[]", "mau_gia": "", "mau_ly_do": ly_do, "mau_kiem_luc": None}


def ngay_sinh_can_quet(dich):
	"""Các cặp (tháng, ngày) sinh cần quét để gửi đúng ngày `dich`. THUẦN.

	Người sinh 29/02 năm thường được chúc vào 28/02.
	"""
	dich = ngay_cua(dich)
	if not dich:
		return []
	ra = [(dich.month, dich.day)]
	if dich.month == 2 and dich.day == 28:
		try:
			date(dich.year, 2, 29)
		except ValueError:
			ra.append((2, 29))
	return ra


def che_sdt(s):
	"""0901486556 -> '•••• 6556'. THUẦN."""
	x = re.sub(r"\D", "", str(s or ""))
	return ("•••• " + x[-4:]) if len(x) >= 4 else ""


def so_dep(v):
	"""25400 -> '25.400'. THUẦN."""
	try:
		n = int(round(float(v or 0)))
	except (TypeError, ValueError):
		n = 0
	return "{:,}".format(n).replace(",", ".")


# ================================================================ phần chạm hệ

import frappe  # noqa: E402


def _bay_gio():
	from frappe.utils import now_datetime

	return now_datetime()


def get_datetime(v):
	from frappe.utils import get_datetime as gd

	return gd(v)


def _cfg():
	from vagabond.lib import cfg

	return cfg()


# Bốn cửa ra ngoài. Nạp zalo.py, khuyen_mai.py TRONG THÂN hàm: zalo.py kéo
# thư viện mạng ở đầu tệp, bộ kiểm tầng khung không được nạp nó.
def _gui_mau(c, sdt, mau, data, dau_vet):
	from vagabond import zalo

	return zalo.gui_mau(c, sdt, mau, data, dau_vet)


def _gui_wa_uu_dai(kh, gt):
	"""Đường phụ WhatsApp cho tin ưu đãi (kenh_khach, một nguồn). Trả (được, lỗi)."""
	from vagabond import kenh_khach

	nd = kenh_khach.noi_dung_uu_dai(gt.get("ten_uu_dai"), gt.get("ma_voucher"), gt.get("dieu_kien"))
	return kenh_khach.gui_uu_dai(_cfg(), kh["sdt84"], kh.get("ten"), nd, gt.get("han_dung") or "", kh.get("dong_y"))


def _doc_mau(ma):
	from vagabond import zalo

	return zalo.doc_mau(ma)


def _han_muc():
	from vagabond import zalo

	return zalo.han_muc()


def _sinh_ma():
	from vagabond import khuyen_mai

	return khuyen_mai._sinh_ma_moi(1)[0]


def _dam_bao():
	"""Tạo dòng cấu hình còn thiếu cho từng kịch bản (lần đầu mở màn hay lần
	đầu việc nền chạy). Dòng mới luôn TẮT: không gì tự gửi khi chưa ai bật."""
	for kb in KICH_BAN:
		if frappe.db.exists(DT_KB, kb["ma"]):
			continue
		frappe.get_doc({
			"doctype": DT_KB, "ma": kb["ma"], "ten": kb["ten"], "bat": 0, "ma_mau": kb["mau"],
			"so_ngay": kb["so_ngay"], "nhac_lai_ngay": kb["nhac_lai"], "tran_ngay": MAC_DINH["tran_ngay"],
			"gio_tu": MAC_DINH["gio_tu"], "gio_den": MAC_DINH["gio_den"],
			"han_ngay": kb.get("han") or MAC_DINH["han_ngay"], "doi_chung": kb.get("doi_chung") or 0,
		}).insert(ignore_permissions=True)


COT_KB = ("ma", "ten", "bat", "bat_luc", "ma_mau", "so_ngay", "nhac_lai_ngay", "ctkm", "han_ngay", "ten_uu_dai", "doi_chung",
	"dieu_kien", "tran_ngay", "gio_tu", "gio_den", "mau_trang_thai", "mau_ly_do", "mau_gia", "mau_tham_so",
	"mau_kiem_luc", "quet_ngay", "ket_qua_luot")


def _cau_hinh(ma):
	r = frappe.db.get_value(DT_KB, ma, list(COT_KB), as_dict=True)
	return dict(r) if r else None


def kiem_mau(ma):
	"""Hỏi Zalo trạng thái và bộ tham số của mẫu đang gắn, ghi vào dòng cấu
	hình. Không gửi tin nào, không tốn tiền."""
	c = _cau_hinh(ma) or {}
	mau = str(c.get("ma_mau") or "").strip()
	if not mau:
		v = {"mau_trang_thai": "", "mau_ly_do": "Chưa gắn mã mẫu.", "mau_tham_so": "[]", "mau_gia": ""}
	else:
		d = _doc_mau(mau)
		if not d.get("ok"):
			v = {"mau_trang_thai": c.get("mau_trang_thai") or "", "mau_ly_do": cat(d.get("loi") or "Không đọc được mẫu.", 300)}
		else:
			v = {"mau_trang_thai": d.get("trang_thai") or "", "mau_ly_do": cat(d.get("ly_do") or "", 300),
				"mau_tham_so": json.dumps(d.get("tham_so") or [], ensure_ascii=False), "mau_gia": str(d.get("gia_sdt") or "")}
	v["mau_kiem_luc"] = _bay_gio()
	frappe.db.set_value(DT_KB, ma, v, update_modified=False)
	return _cau_hinh(ma)


def truoc_luu_form(doc):
	"""Lưu thẳng trên form Desk theo đúng luật của màn app: đổi mã mẫu thì xoá
	kết quả kiểm của mẫu cũ; chuyển từ tắt sang bật thì ghi lúc bật để quét
	sau mua chỉ tính từ lúc đó (Codex PR #517 vòng 2 và 4)."""
	truoc = doc.get_doc_before_save() if hasattr(doc, "get_doc_before_save") else None
	dat = doc.__setitem__ if isinstance(doc, dict) else doc.set
	if truoc is not None and str(truoc.get("ma_mau") or "") != str(doc.get("ma_mau") or ""):
		for k, x in xoa_kiem_mau().items():
			dat(k, x)
	if int(doc.get("bat") or 0) and (truoc is None or not int(truoc.get("bat") or 0)):
		dat("bat_luc", _bay_gio())


def _lan_mua_cuoi(khach):
	"""Ngày hoá đơn đã ghi sổ mới nhất của khách, đọc thẳng từ hoá đơn (không
	chờ hồ sơ CRM cập nhật lúc 02:30)."""
	from vagabond.crm import DK_HD_MUA

	# Cùng điều kiện với hồ sơ CRM: bỏ hoá đơn huỷ và hoá đơn trả hàng.
	r = frappe.db.sql("""select max(posting_date) from `tabSales Invoice` where customer = %s and """ + DK_HD_MUA, (khach,))
	return r[0][0] if r and r[0] else None


def _so_don_da_nhan(khach):
	"""Số đơn khách đã nhận trên ERP (DK_DA_NHAN, gồm đơn giao chưa ghi sổ)."""
	from vagabond.khuyen_mai import NGUON_KHONG_GIAM_HANG

	r = frappe.db.sql("""select count(*) from `tabSales Invoice` si where si.customer = %(k)s and """ + DK_DA_NHAN,
		{"k": khach, "nguon_bo": tuple(NGUON_KHONG_GIAM_HANG)})
	return int(r[0][0] or 0) if r else 0


def _mua_gan(khach, so_ngay):
	"""Khách có đơn đã nhận trong `so_ngay` ngày qua không."""
	from vagabond.khuyen_mai import NGUON_KHONG_GIAM_HANG

	r = frappe.db.sql("""select count(*) from `tabSales Invoice` si where si.customer = %(k)s and si.creation >= %(tu)s and """ + DK_DA_NHAN,
		{"k": khach, "tu": _bay_gio() - timedelta(days=so_nguyen(so_ngay)), "nguon_bo": tuple(NGUON_KHONG_GIAM_HANG)})
	return bool(r and int(r[0][0] or 0))


def _da_nhan_km_tuan(khach):
	"""Khách đã nhận tin ưu đãi nào (kịch bản tính trần tuần) trong TRAN_TUAN_NGAY ngày qua."""
	ds = [k["ma"] for k in KICH_BAN if k.get("tran_tuan")]
	return frappe.db.count(DT_TIN, {"khach": khach, "trang_thai": TT_GUI, "kich_ban": ["in", ds],
		"luc_gui": [">=", _bay_gio() - timedelta(days=TRAN_TUAN_NGAY)]}) > 0


def _voucher_con_dung(ma):
	"""Mã riêng còn dùng được không. Trả (bản ghi, lý do không gửi)."""
	if not ma:
		return None, "Dòng tin không gắn mã."
	v = frappe.db.get_value("Vagabond Voucher", ma, ["ma", "ctkm", "trang_thai", "han_dung", "danh_cho"], as_dict=True)
	if not v:
		return None, "Không còn mã %s." % ma
	if v.get("trang_thai") != "Chua dung":
		return None, "Mã %s đã dùng hoặc đã huỷ." % ma
	han = ngay_cua(v.get("han_dung"))
	if han and han < _bay_gio().date():
		return None, "Mã %s đã hết hạn." % ma
	return v, ""


def _ho_so(khach):
	"""Thông tin khách cần để gửi: tên, số Zalo, đồng ý, điểm, hạng."""
	from vagabond.lib import sdt84

	cu = frappe.db.get_value("Customer", khach, ["customer_name", "mobile_no", "vgb_diem", "vgb_hang", "vgb_sinh_nhat"], as_dict=True) or {}
	hs = frappe.db.get_value("Vagabond Ho So CRM", khach, ["sdt", "dy_zalo", "khong_quang_cao"], as_dict=True) or {}
	return {
		"ten": ten_goi(cu.get("customer_name") or khach),
		"sdt84": sdt84(hs.get("sdt") or cu.get("mobile_no") or ""),
		"dong_y": (hs.get("dy_zalo") or "") == "Đồng ý" and not int(hs.get("khong_quang_cao") or 0),
		"diem": cu.get("vgb_diem") or 0,
		"hang": cu.get("vgb_hang") or "",
		"sinh_nhat": cu.get("vgb_sinh_nhat"),
	}


def _da_gui_hom_nay(ma):
	luc = _bay_gio()
	return frappe.db.count(DT_TIN, {"kich_ban": ma, "trang_thai": TT_GUI, "luc_gui": [">=", luc.replace(hour=0, minute=0, second=0, microsecond=0)]})


def _ghi_cho(ma, khoa, khach, hoa_don=None, diem=0, voucher=None, trang_thai=TT_CHO, loi=""):
	"""Ghi một dòng Chờ gửi. Khoá đã có thì thôi (chống trùng tầng sổ)."""
	if frappe.db.exists(DT_TIN, {"khoa": khoa}):
		return False
	frappe.get_doc({"doctype": DT_TIN, "kich_ban": ma, "khoa": khoa, "khach": khach, "hoa_don": hoa_don,
		"diem": diem, "voucher": voucher, "trang_thai": trang_thai, "loi": cat(loi, 500)}).insert(ignore_permissions=True)
	return True


# v645: điều kiện "khách đã NHẬN đơn" trên hoá đơn, dùng chung cho tin cảm ơn
# và tin cảm ơn người giới thiệu. Bill tại quầy: ghi sổ là khách đã cầm bánh.
# Đơn giao: đồng bộ chỉ dựng hoá đơn (nháp) khi Pancake đã chuyển Đã nhận
# (ban_hang.TT_DOANH_SO), nên có hoá đơn có mã Pancake là đã nhận, không chờ ghi
# sổ cuối ngày. Bỏ đơn sàn và khách sỉ (cùng danh sách khuyen_mai), hoá đơn trả
# hàng, hoá đơn huỷ.
DK_DA_NHAN = """ifnull(si.is_return, 0) = 0 and ifnull(si.vgb_huy, 0) = 0
	and (si.docstatus = 1 or (si.docstatus = 0 and ifnull(si.custom_pancake_id, '') != ''))
	and ifnull(si.custom_nguon, '') not in %(nguon_bo)s"""


def _don_da_nhan(tu, ma, them="", them_ts=None, gioi_han=1000):
	"""Hoá đơn khách NHẬN từ `tu`, chưa có dòng tin của kịch bản `ma`.

	Mốc nhận: đơn giao Pancake là lúc dựng nháp (đồng bộ chỉ dựng nháp khi đơn
	Đã nhận); bill quầy tạo và ghi sổ liền là lúc tạo. Bill quầy lưu nháp
	(ban_hang.pos_chot) rồi ghi sổ sau, kể cả nháp tạo trước lúc bật kịch bản
	hay quá CHO_TOI_DA_GIO: mốc là lúc GHI SỔ, đọc ở dòng tích điểm hook cộng
	điểm ghi đúng lúc đó (Codex PR 548 b4b18d5). Bill không tích điểm mà ghi sổ
	muộn thì không có mốc này (xem docs/huong-dan/uu-dai-zalo-tu-dong.md).
	"""
	from vagabond.khuyen_mai import NGUON_KHONG_GIAM_HANG

	ts = {"tu": tu, "nguon_bo": tuple(NGUON_KHONG_GIAM_HANG), "tien_to": ma + ":"}
	ts.update(them_ts or {})
	cot = """select si.name, si.customer khach, si.docstatus, ifnull(si.custom_pancake_id, '') pid,
		ifnull(si.custom_pancake_display_id, '') pdid, si.grand_total"""
	chua = """ and not exists (select 1 from `tabVagabond Tin Zalo Khach` t where t.khoa = concat(%(tien_to)s, si.name))"""
	gh = " limit " + str(int(gioi_han))
	ra = list(frappe.db.sql(cot + """ from `tabSales Invoice` si
		where si.creation >= %(tu)s and """ + DK_DA_NHAN + them + chua + " order by si.creation" + gh, ts, as_dict=True) or [])
	muon = frappe.db.sql(cot + """ from `tabVagabond So Diem` d join `tabSales Invoice` si on si.name = d.hoa_don
		where d.loai = 'Tich tu hoa don' and d.creation >= %(tu)s and si.creation < %(tu)s
		and si.docstatus = 1 and ifnull(si.custom_pancake_id, '') = '' and """ + DK_DA_NHAN + them + chua
		+ " order by d.creation" + gh, ts, as_dict=True) or []
	co = {r.name for r in ra}
	for r in muon:
		if r.name not in co:
			co.add(r.name)
			ra.append(r)
	return ra[:int(gioi_han)]


def _la_qua_tang(si_name):
	"""Hoá đơn hàng tặng: không cảm ơn như đơn mua (cùng luật không tích điểm)."""
	try:
		r = frappe.db.get_value("Sales Invoice", si_name, ["vgb_qua_tang", "vgb_phieu_qua"], as_dict=True) or {}
	except Exception:
		return False
	return bool(int(r.get("vgb_qua_tang") or 0) or str(r.get("vgb_phieu_qua") or "").strip())


def _tu_luc(ma):
	"""Mốc quét cho kịch bản quét theo hoá đơn: từ lúc bật, tối đa CHO_TOI_DA_GIO."""
	c = _cau_hinh(ma) or {}
	if not int(c.get("bat") or 0):
		return None
	luc = _bay_gio()
	bat_luc = c.get("bat_luc")
	if not bat_luc:
		# Bật bằng đường nào đó không ghi lúc bật: tính từ bây giờ, không gửi bù.
		frappe.db.set_value(DT_KB, ma, "bat_luc", luc, update_modified=False)
		return None
	tu = luc - timedelta(hours=CHO_TOI_DA_GIO)
	if get_datetime(bat_luc) > tu:
		tu = get_datetime(bat_luc)
	return tu


def _la_khach_gop(ma):
	"""Cửa duy nhất tới khach_hang.la_khach_gop cho tệp này và den_bu.

	khach_hang nạp ban_hang, mà ban_hang nạp requests ở đầu tệp; CI chạy không
	có requests. Nạp trễ trong thân hàm để mô đun này vẫn nạp được ở CI, và để
	bộ kiểm vá đúng một chỗ.
	"""
	from vagabond import khach_hang

	return khach_hang.la_khach_gop(ma)


def _diem_cua_don(hoa_don):
	"""Cửa duy nhất tới khach_hang.diem_cua_don (cùng lý do với _la_khach_gop)."""
	from vagabond import khach_hang

	return khach_hang.diem_cua_don(hoa_don)


def quet_sau_mua():
	"""v645: mỗi đơn khách NHẬN sau lúc bật kịch bản -> một dòng chờ (DK_DA_NHAN).

	Trước v645 máy đợi lúc cộng điểm, tức hoá đơn ghi sổ: đơn giao ghi sổ cuối
	ngày nên khách nhận bánh buổi trưa mà sáng hôm sau mới có tin cảm ơn.
	"""
	tu = _tu_luc("sau_mua")
	if not tu:
		return 0
	n = 0
	for r in _don_da_nhan(tu, "sau_mua"):
		if _la_khach_gop(r.khach) or _la_qua_tang(r.name):
			continue
		diem, _da = _diem_cua_don(r.name)
		n += 1 if _ghi_cho("sau_mua", khoa_tin("sau_mua", hoa_don=r.name), r.khach, r.name, diem) else 0
	return n


def _so_dien_thoai_gioi_thieu(si_name):
	"""Số khách gõ ở ô Mã giới thiệu của đơn web, khi số đó KHÔNG phải nhân
	viên (đơn có nhân viên giới thiệu thì đi đường hoa hồng v638)."""
	from vagabond import gioi_thieu

	si = frappe.db.get_value("Sales Invoice", si_name, ["custom_pancake_id", "custom_pancake_display_id"], as_dict=True) or {}
	dw = gioi_thieu._don_web_cua(si)
	if not dw or dw.get(gioi_thieu.O_DW_NGUOI):
		return ""
	try:
		snap = json.loads(frappe.db.get_value(gioi_thieu.DT_DW, dw.get("name"), "snapshot") or "{}")
	except (TypeError, ValueError):
		return ""
	return str(snap.get("gioi_thieu_sdt") or "").strip()


def quet_gioi_thieu():
	"""v645: bạn mới nhận xong đơn web có gõ số của một khách ở ô Mã giới thiệu
	-> dòng chờ phát mã cho khách giới thiệu (tối đa GIOI_THIEU_TOI_DA_THANG)."""
	from vagabond import nhap_khach

	tu = _tu_luc("gioi_thieu")
	if not tu:
		return 0
	dau_thang = _bay_gio().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
	n = 0
	for r in _don_da_nhan(tu, "gioi_thieu", " and ifnull(si.custom_pancake_id, '') != ''"):
		sdt = _so_dien_thoai_gioi_thieu(r.name)
		if not sdt:
			continue
		nguoi = nhap_khach.tim_theo_sdt(sdt)
		if not nguoi or nguoi == r.khach or _la_khach_gop(nguoi):
			continue
		# Chỉ BẠN MỚI mới sinh quà: đơn này là đơn đã nhận đầu tiên của người
		# mua (Codex PR 548 b4b18d5: khách mua lại gõ số người giới thiệu thì
		# mỗi đơn đều sinh thêm quà).
		if _so_don_da_nhan(r.khach) > 1:
			continue
		da = frappe.db.count(DT_TIN, {"kich_ban": "gioi_thieu", "khach": nguoi, "creation": [">=", dau_thang]})
		trang_thai, loi = TT_CHO, ""
		if da >= GIOI_THIEU_TOI_DA_THANG:
			trang_thai, loi = TT_BO, "Khách đã nhận đủ %d mã giới thiệu trong tháng." % GIOI_THIEU_TOI_DA_THANG
		n += 1 if _ghi_cho("gioi_thieu", khoa_tin("gioi_thieu", hoa_don=r.name), nguoi, r.name,
			trang_thai=trang_thai, loi=loi) else 0
	return n


def quet_sinh_nhat(hom_nay):
	"""Khách đã đồng ý Zalo, sinh nhật đúng `so_ngay` ngày nữa -> dòng chờ."""
	c = _cau_hinh("sinh_nhat") or {}
	if not int(c.get("bat") or 0):
		return 0
	dich = hom_nay + timedelta(days=so_nguyen(c.get("so_ngay"), 3))
	cap = ngay_sinh_can_quet(dich)
	if not cap:
		return 0
	dk = " or ".join(["(month(c.vgb_sinh_nhat) = %s and day(c.vgb_sinh_nhat) = %s)"] * len(cap))
	ts = [x for p in cap for x in p]
	rows = frappe.db.sql(
		"""select c.name khach from `tabCustomer` c join `tabVagabond Ho So CRM` h on h.name = c.name
		where c.vgb_sinh_nhat is not null and (%s)
		and ifnull(h.dy_zalo, '') = 'Đồng ý' and ifnull(h.khong_quang_cao, 0) = 0""" % dk, ts, as_dict=True)
	n = 0
	for r in rows:
		n += 1 if _ghi_cho("sinh_nhat", khoa_tin("sinh_nhat", r.khach, moc=dich.year), r.khach) else 0
	return n


def quet_quay_lai(hom_nay, ma="quay_lai"):
	"""Khách đã đồng ý Zalo vừa vắng mặt đủ `so_ngay` -> dòng chờ, trừ khách
	đã nhận tin mời quay lại trong `nhac_lai_ngay` ngày. v645: dùng chung cho
	mốc hai (quay_lai_2)."""
	c = _cau_hinh(ma) or {}
	if not int(c.get("bat") or 0):
		return 0
	kb = kich_ban(ma) or {}
	n_ngay = so_nguyen(c.get("so_ngay"), kb.get("so_ngay") or 60)
	if n_ngay <= 0:
		return 0
	nhac = so_nguyen(c.get("nhac_lai_ngay"), kb.get("nhac_lai") or 120)
	rows = frappe.db.sql(
		"""select h.name khach, h.lan_cuoi from `tabVagabond Ho So CRM` h
		where h.lan_cuoi between %s and %s
		and ifnull(h.dy_zalo, '') = 'Đồng ý' and ifnull(h.khong_quang_cao, 0) = 0
		and not exists (select 1 from `tabVagabond Tin Zalo Khach` t where t.khach = h.name
			and t.kich_ban = %s and t.trang_thai = 'Đã gửi' and t.luc_gui >= %s)""",
		(hom_nay - timedelta(days=n_ngay + 2), hom_nay - timedelta(days=n_ngay), ma, hom_nay - timedelta(days=nhac)),
		as_dict=True)
	n = 0
	for r in rows:
		if not vang_mat_du(r.lan_cuoi, hom_nay, n_ngay):
			continue
		n += 1 if _ghi_cho(ma, khoa_tin(ma, r.khach, moc=ngay_cua(r.lan_cuoi)), r.khach) else 0
	return n


def quet_quay_lai_2(hom_nay):
	return quet_quay_lai(hom_nay, "quay_lai_2")


def quet_don_thu_hai(hom_nay):
	"""v645: khách mới có đúng một đơn (hồ sơ CRM, gồm cả lịch sử Fabi), nhận
	đơn đó đúng `so_ngay` ngày trước -> dòng chờ mời đơn thứ hai."""
	c = _cau_hinh("don_thu_hai") or {}
	if not int(c.get("bat") or 0):
		return 0
	n_ngay = so_nguyen(c.get("so_ngay"), 3)
	rows = frappe.db.sql(
		"""select h.name khach, h.lan_cuoi from `tabVagabond Ho So CRM` h
		where ifnull(h.so_don, 0) = 1 and h.lan_cuoi between %s and %s
		and ifnull(h.dy_zalo, '') = 'Đồng ý' and ifnull(h.khong_quang_cao, 0) = 0""",
		(hom_nay - timedelta(days=n_ngay + 2), hom_nay - timedelta(days=n_ngay)), as_dict=True)
	n = 0
	for r in rows:
		n += 1 if _ghi_cho("don_thu_hai", khoa_tin("don_thu_hai", r.khach), r.khach) else 0
	return n


def quet_nhac_dip(hom_nay):
	"""v645: năm ngoái khách nhận một đơn giao từ NGUONG_DIP vào ngày D -> trước
	D năm nay `so_ngay` ngày, nếu khách chưa mua lại gần đây, dòng chờ nhắc."""
	c = _cau_hinh("nhac_dip") or {}
	if not int(c.get("bat") or 0):
		return 0
	dich = hom_nay + timedelta(days=so_nguyen(c.get("so_ngay"), 10))
	cu = ngay_dip_nam_truoc(dich)
	# Cùng điều kiện "hoá đơn mua" với hồ sơ CRM (crm.DK_HD_MUA), viết với bí danh.
	rows = frappe.db.sql(
		"""select distinct si.customer khach from `tabSales Invoice` si
		join `tabVagabond Ho So CRM` h on h.name = si.customer
		where si.docstatus = 1 and ifnull(si.vgb_huy, 0) = 0 and ifnull(si.is_return, 0) = 0
		and ifnull(si.custom_pancake_id, '') != '' and si.posting_date = %s and si.grand_total >= %s
		and ifnull(h.dy_zalo, '') = 'Đồng ý' and ifnull(h.khong_quang_cao, 0) = 0
		and (h.lan_cuoi is null or h.lan_cuoi < %s)""",
		(cu, NGUONG_DIP, hom_nay - timedelta(days=DIP_DA_MUA_GAN)), as_dict=True)
	n = 0
	for r in rows:
		n += 1 if _ghi_cho("nhac_dip", khoa_tin("nhac_dip", r.khach, moc=dich.isoformat()), r.khach) else 0
	return n


def quet_nhac_han(hom_nay):
	"""v645: mã riêng của khách chưa dùng, hết hạn đúng `so_ngay` ngày nữa ->
	dòng chờ nhắc, mỗi mã một lần."""
	c = _cau_hinh("nhac_han") or {}
	if not int(c.get("bat") or 0):
		return 0
	han = hom_nay + timedelta(days=so_nguyen(c.get("so_ngay"), 3))
	rows = frappe.get_all("Vagabond Voucher", filters={"trang_thai": "Chua dung", "han_dung": han, "danh_cho": ["is", "set"]},
		fields=["name", "danh_cho"], limit_page_length=2000)
	n = 0
	for r in rows:
		n += 1 if _ghi_cho("nhac_han", khoa_tin("nhac_han", moc=r.name), r.danh_cho, voucher=r.name) else 0
	return n


def quet_nhac_diem(hom_nay):
	"""v652: khách có điểm sắp hết hạn (cuốn chiếu) trong `so_ngay` tới -> dòng
	chờ nhắc. Khoá theo ngày mất đầu tiên; mỗi khách tối đa một tin nhắc điểm
	trong `so_ngay` ngày (khách mua nhiều lần không bị nhắc mỗi ngày)."""
	from vagabond import diem_han, diem_web

	c = _cau_hinh("nhac_diem") or {}
	if not int(c.get("bat") or 0):
		return 0
	cd = diem_han._cd()
	if cd["cach"] != "Cuon chieu":
		return 0
	so_ngay = so_nguyen(c.get("so_ngay"), 30) or 30
	han = so_nguyen(cd["han_thang"], 12) or 12
	# Bút tích sẽ mất trong (hôm nay, hôm nay + so_ngay]: ngày tích từ mốc hôm nay tới
	# trước mốc của ngày cuối khung (mốc = ngày lùi han tháng, cùng phép của việc định kỳ).
	tu = diem_web.cong_thang(hom_nay, -han) - timedelta(days=1)
	den = diem_web.cong_thang(hom_nay + timedelta(days=so_ngay), -han) - timedelta(days=1)
	ds = [r[0] for r in frappe.db.sql("""select distinct khach from `tabVagabond So Diem`
		where diem > 0 and date(ngay) > %s and date(ngay) <= %s
		and khach not in (select t.khach from `tabVagabond Tin Zalo Khach` t
			where t.kich_ban = 'nhac_diem' and t.creation >= %s)
		limit 2000""", (tu, den, hom_nay - timedelta(days=so_ngay)))]
	n = 0
	for kh in ds:
		but = [(str(r[0]), float(r[1] or 0)) for r in frappe.db.sql(
			"select date(ngay), diem from `tabVagabond So Diem` where khach = %s order by ngay", (kh,))]
		sh = diem_web.sap_het_han(but, hom_nay, han, so_ngay)
		if sh and sh["diem"] > 0:
			n += 1 if _ghi_cho("nhac_diem", khoa_tin("nhac_diem", kh, moc=sh["ngay"]), kh, diem=sh["diem"]) else 0
	return n


def cho_hoan_diem(khach, ten_don, diem):
	"""v652: xếp tin báo khách đã hoàn điểm của đơn web không thành. Kịch bản
	tắt thì thôi (điểm vẫn hoàn, chỉ không báo). Một đơn một tin."""
	c = _cau_hinh("hoan_diem") or {}
	if not int(c.get("bat") or 0):
		return False
	return _ghi_cho("hoan_diem", khoa_tin("hoan_diem", khach, moc=ten_don), khach, diem=diem)


def _gia_tri_nhac_diem(row, kh):
	"""Tính lại lúc gửi: khách đã dùng điểm từ lúc quét thì không nhắc nữa."""
	from vagabond import diem_han, diem_web

	cd = diem_han._cd()
	if cd["cach"] != "Cuon chieu":
		return None, "Hạn điểm không còn chạy cuốn chiếu."
	c = _cau_hinh("nhac_diem") or {}
	but = [(str(r[0]), float(r[1] or 0)) for r in frappe.db.sql(
		"select date(ngay), diem from `tabVagabond So Diem` where khach = %s order by ngay", (row.khach,))]
	sh = diem_web.sap_het_han(but, _bay_gio().date(), cd["han_thang"], so_nguyen(c.get("so_ngay"), 30) or 30)
	if not sh:
		return None, "Khách không còn điểm sắp hết hạn."
	return {"ten_khach": kh["ten"], "diem_het_han": so_dep(sh["diem"]), "ngay_het_han": sh["ngay"],
		"tong_diem": so_dep(float(kh["diem"] or 0)), "hang": kh["hang"] or "Thành viên"}, ""


def _gia_tri_hoan_diem(row, kh):
	ma_don = str(row.khoa or "").rsplit(":", 1)[-1]
	return {"ten_khach": kh["ten"], "diem_hoan": so_dep(row.get("diem") or 0), "ma_don": ma_don,
		"tong_diem": so_dep(float(kh["diem"] or 0)), "hang": kh["hang"] or "Thành viên"}, ""


# Kịch bản quét một lần mỗi ngày (theo ngày), theo thứ tự ưu tiên của KICH_BAN.
QUET_THEO_NGAY = {
	"nhac_diem": "quet_nhac_diem",
	"sinh_nhat": "quet_sinh_nhat", "nhac_dip": "quet_nhac_dip", "don_thu_hai": "quet_don_thu_hai",
	"quay_lai": "quet_quay_lai", "quay_lai_2": "quet_quay_lai_2", "nhac_han": "quet_nhac_han",
}


def _gia_tri_sau_mua(row, kh):
	si = frappe.db.get_value("Sales Invoice", row.get("hoa_don"), ["docstatus", "posting_date", "posting_time", "grand_total",
		"vgb_huy", "is_return", "custom_pancake_id", "custom_pancake_display_id"], as_dict=True)
	if not si or not hoa_don_con_nhan(si.docstatus, si.custom_pancake_id, si.vgb_huy, si.is_return):
		return None, "Hoá đơn đã huỷ hoặc không còn."
	diem, da_ghi = _diem_cua_don(row.get("hoa_don"))
	gio = str(si.posting_time or "")[:5]
	return {
		"ten_khach": kh["ten"], "ma_hoa_don": ma_don_cho_khach(row.get("hoa_don"), si.custom_pancake_display_id),
		"ngay_mua": (ngay_vn(si.posting_date) + (" " + gio if gio else "")).strip(),
		"tong_tien": tien_vn(si.grand_total), "diem_tich": so_dep(diem),
		# Đơn giao nhận rồi mà chưa ghi sổ: điểm chưa vào số dư, cộng trước để
		# tin không báo tổng điểm thiếu đúng phần của đơn này.
		"tong_diem": so_dep(float(kh["diem"] or 0) + (0 if da_ghi else float(diem or 0))), "hang": kh["hang"] or "Thành viên",
	}, ""


COT_CTKM = ["name", "ten", "cach_ma", "bat", "kieu_giam", "gia_tri", "hd_toi_thieu", "tu_ngay", "den_ngay", "han_ma",
	"doi_tuong", "hang_khach", "nhom_khach", "vi_phat", "vi_dip", "vi_so_lan", "vi_han_ngay"]


def _doc_ctkm(ten):
	if not ten:
		return None
	return frappe.db.get_value("Vagabond CTKM", ten, COT_CTKM, as_dict=True)


def _phat_voucher(c, kh, khach, ma_kb, han=None):
	"""Một mã dùng một lần cho đúng khách, hạn theo số ngày đã đặt (hay hạn
	đã tính sẵn theo luật Ví quà, v623). Trả (mã, hạn, câu lỗi)."""
	km = _doc_ctkm(c.get("ctkm"))
	loi = ""
	if not han:
		han, loi = ctkm_phat_duoc(km, _bay_gio().date(), c.get("han_ngay"))
	if not han:
		return None, None, loi
	ma = _sinh_ma()
	frappe.get_doc({"doctype": "Vagabond Voucher", "ma": ma, "ctkm": km.name, "ten_ctkm": cat(km.ten, 140),
		"trang_thai": "Chua dung", "han_dung": han, "khach": cat(kh["ten"], 140), "sdt": kh["sdt84"], "danh_cho": khach,
		"chi_nguoi_nhan": 1 if int(km.get("vi_phat") or 0) else 0,
		"gui_cho": cat("Tin Zalo: " + (kich_ban(ma_kb) or {}).get("ten", ""), 140)}).insert(ignore_permissions=True)
	return ma, han, ""


def ghi_doi_tuong(km):
	"""Câu ngắn cho màn: chương trình chỉ áp cho ai. THUẦN. Mọi khách thì rỗng.

	Codex PR #517 vòng 7: người cài kịch bản phải biết trước khách ngoài phạm vi
	sẽ bị bỏ qua (không phát mã, không gửi tin)."""
	dt_ = (km or {}).get("doi_tuong") or "Moi khach"
	if dt_ == "Moi khach":
		return ""
	if dt_ == "Theo hang khach":
		ds = ", ".join(x.strip() for x in str(km.get("hang_khach") or "").splitlines() if x.strip())
		ai = "khách hạng " + ds if ds else "một số hạng khách"
	elif dt_ == "Theo nhom khach":
		ds = ", ".join(x.strip() for x in str(km.get("nhom_khach") or "").splitlines() if x.strip())
		ai = "khách nhóm " + ds if ds else "một số nhóm khách"
	elif dt_ == "Khach chi dinh":
		ai = "khách trong danh sách chỉ định"
	elif dt_ == "Nhan vien":
		ai = "nhân viên"
	else:
		ai = "một nhóm khách"
	return "Chỉ áp cho %s, khách khác được bỏ qua" % ai


def _hop_doi_tuong(km, khach, sdt):
	"""Cùng một phép kiểm đối tượng với quầy (một nguồn: khuyen_mai)."""
	from vagabond import khuyen_mai

	return khuyen_mai._hop_doi_tuong(km, khach, sdt)


def _huy_voucher(ma, ly_do):
	if ma:
		frappe.db.set_value("Vagabond Voucher", ma, {"trang_thai": "Da huy", "ghi_chu": cat("Không gửi được tin Zalo: " + ly_do, 500)},
			update_modified=False)


def _xong(row_name, tt, loi="", **v):
	v.update({"trang_thai": tt, "loi": cat(loi, 500)})
	if tt == TT_GUI:
		v["luc_gui"] = _bay_gio()
	frappe.db.set_value(DT_TIN, row_name, v, update_modified=False)
	frappe.db.commit()


def _la_doi_chung(c, kb, row):
	"""v645: nhóm đối chứng cố định theo khách, để báo cáo so được ai nhận tin
	quay lại bao nhiêu với ai không nhận. Gọi SAU mọi điều kiện loại chung
	(Codex PR 548 c02f2be): khách không đủ điều kiện mà bị ghi đối chứng thì
	nhóm đối chứng rộng hơn nhóm nhận tin, tỉ lệ so sánh lệch. Ghi Bỏ qua và
	trả True khi khách thuộc nhóm đối chứng."""
	pt = so_nguyen(c.get("doi_chung"), kb.get("doi_chung") or 0)
	if pt and trong_doi_chung(row.khach, pt):
		_xong(row.name, TT_BO, "%s: %d%% khách không nhận tin này để đo hiệu quả." % (LY_DO_DOI_CHUNG, pt))
		return True
	return False


def _gui_mot(c, row):
	"""Gửi một dòng chờ. Trả mã lỗi Zalo (0 là được, None là lỗi riêng dòng
	đã ghi sổ không cần dừng lượt)."""
	ma_kb = c["ma"]
	kb = kich_ban(ma_kb)
	kh = _ho_so(row.khach)
	if not kh["sdt84"]:
		_xong(row.name, TT_BO, "Khách chưa có số điện thoại.")
		return None
	ma_v = None
	ma_huy = None  # chỉ huỷ mã do chính lượt này phát, không huỷ mã Ví quà đã có
	if kb["km"]:
		# Đọc lại đồng ý NGAY TRƯỚC khi gửi: khách rút đồng ý sau lúc quét thì thôi.
		if not kh["dong_y"]:
			_xong(row.name, TT_BO, "Khách không còn đồng ý nhận tin Zalo.")
			return None
		if ma_kb == "sinh_nhat" and qua_sinh_nhat(kh.get("sinh_nhat"), str(row.khoa or "").rsplit(":", 1)[-1], _bay_gio().date()):
			_xong(row.name, TT_BO, "Khách đã qua sinh nhật, không gửi lời chúc muộn.")
			return None
		if ma_kb in ("quay_lai", "quay_lai_2") and not con_vang_mat(_lan_mua_cuoi(row.khach), _bay_gio().date(), c.get("so_ngay")):
			_xong(row.name, TT_BO, "Khách đã quay lại mua, không gửi lời mời.")
			return None
		if ma_kb == "don_thu_hai" and _so_don_da_nhan(row.khach) > 1:
			_xong(row.name, TT_BO, "Khách đã mua đơn thứ hai, không gửi lời mời.")
			return None
		if ma_kb == "nhac_dip" and _mua_gan(row.khach, DIP_DA_MUA_GAN):
			_xong(row.name, TT_BO, "Khách vừa mua lại trong %d ngày, không nhắc dịp." % DIP_DA_MUA_GAN)
			return None
		# v645 (anh Việt 08/11/2026): mỗi khách tối đa một tin ưu đãi mỗi 7 ngày.
		if kb.get("tran_tuan") and _da_nhan_km_tuan(row.khach):
			_xong(row.name, TT_BO, "Khách đã nhận một tin ưu đãi trong %d ngày qua (mỗi khách tối đa một tin mỗi tuần)." % TRAN_TUAN_NGAY)
			return None
		# Nhóm đối chứng KHÔNG chia ở đây: chia sau mọi điều kiện loại (đối
		# tượng chương trình, Ví quà, mã có sẵn), ở _la_doi_chung bên dưới.
	if kb["km"] and kb.get("kieu") == "co_san":
		# v645: nhắc hạn và đền bù gửi một mã ĐÃ có của khách, không phát mã mới.
		v, ly = _voucher_con_dung(row.get("voucher"))
		if not v:
			_xong(row.name, TT_BO, ly)
			return None
		km = _doc_ctkm(v.get("ctkm")) or {}
		ly = ly_do_khong_gui_lai(km, _bay_gio().date())
		if ly:
			_xong(row.name, TT_BO, ly.replace("mã Ví quà", "mã"))
			return None
		# Codex PR 548 c02f2be: mã có sẵn cũng phải đúng đối tượng của chương
		# trình, không thì quầy (khuyen_mai.tinh) từ chối mã đã hứa.
		ok_dt, ly_dt = _hop_doi_tuong(km, row.khach, kh["sdt84"])
		if not ok_dt:
			_xong(row.name, TT_BO, "Khách không thuộc đối tượng của chương trình ưu đãi: %s." % ly_dt)
			return None
		if _la_doi_chung(c, kb, row):
			return None
		rieng = ma_kb != "nhac_han"
		ten_ud, dk = mo_ta_uu_dai(km, c.get("ten_uu_dai") if rieng else "", c.get("dieu_kien") if rieng else "")
		ma_v = v.get("ma")
		gt = {"ten_khach": kh["ten"], "ten_uu_dai": ten_ud, "dieu_kien": dk, "han_dung": ngay_vn(v.get("han_dung")), "ma_voucher": ma_v}
	elif kb["km"]:
		# Codex PR #517 vòng 7: quầy chỉ nhận mã khi khách đúng đối tượng của
		# chương trình (khuyen_mai.tinh gọi _hop_doi_tuong). Khách ngoài phạm
		# vi thì bỏ qua, không phát mã khách không dùng được.
		ok_dt, ly_dt = _hop_doi_tuong(_doc_ctkm(c.get("ctkm")) or {}, row.khach, kh["sdt84"])
		if not ok_dt:
			_xong(row.name, TT_BO, "Khách không thuộc đối tượng của chương trình ưu đãi: %s." % ly_dt)
			return None
		km = _doc_ctkm(c.get("ctkm")) or {}
		# v623: chương trình phát vào Ví quà thành viên thì một kỳ một mã cho cả
		# hai kênh. Khách đã có mã còn dùng được thì gửi lại đúng mã đó; mã của
		# kỳ này đã dùng hay đã huỷ thì thôi, không phát mã thứ hai. Mã mới đi
		# theo đúng luật Ví quà (dịp phát, hạn), khoá cùng dòng hồ sơ với trang
		# thành viên trước khi xét (Codex PR #520).
		la_vi = bool(so_nguyen(km.get("vi_phat")))
		cu_vi, han_vi = None, None
		if la_vi:
			from vagabond import thanh_vien

			hn = _bay_gio().date()
			thanh_vien.khoa_ho_so(row.khach)
			trong_ky = thanh_vien.ma_vi_trong_ky(km, row.khach, hn)
			if trong_ky:
				cu_vi = next((v for v in trong_ky if thanh_vien.trang_thai_voucher(v, hn) == "dung_duoc"), None)
				if not cu_vi:
					_xong(row.name, TT_BO, "Khách đã nhận mã của chương trình này trong kỳ.")
					return None
				ly_gl = ly_do_khong_gui_lai(km, hn)
				if ly_gl:
					_xong(row.name, TT_BO, ly_gl)
					return None
			else:
				han_vi, ly_vi = thanh_vien.xet_vi(km, row.khach, kh.get("sinh_nhat"), kh["sdt84"], hn)
				if not han_vi:
					_xong(row.name, TT_BO, "Khách chưa đủ điều kiện nhận mã Ví quà của chương trình: %s." % ly_vi)
					return None
		if _la_doi_chung(c, kb, row):
			return None
		if cu_vi:
			ma_v, han = cu_vi.get("ma"), cu_vi.get("han_dung")
		else:
			ma_v, han, loi = _phat_voucher(c, kh, row.khach, ma_kb, han_vi)
			if loi:
				_xong(row.name, TT_LOI, loi)
				return None
			if la_vi:
				# Mã Ví quà đã thuộc về khách: ghi ngay để nhả khoá hồ sơ trước khi
				# gọi Zalo, và gửi lỗi thì KHÔNG huỷ (khách vẫn thấy trong ví;
				# huỷ là mất quà cả kỳ vì mã đã huỷ vẫn tính là đã nhận).
				frappe.db.commit()
			else:
				ma_huy = ma_v
		ten_ud, dk = mo_ta_uu_dai(km, c.get("ten_uu_dai"), c.get("dieu_kien"))
		gt = {"ten_khach": kh["ten"], "ten_uu_dai": ten_ud, "dieu_kien": dk, "han_dung": ngay_vn(han), "ma_voucher": ma_v}
	else:
		gt, loi = {"nhac_diem": _gia_tri_nhac_diem, "hoan_diem": _gia_tri_hoan_diem}.get(ma_kb, _gia_tri_sau_mua)(row, kh)
		if loi:
			_xong(row.name, TT_BO, loi)
			return None
	data, thieu = du_lieu_mau(gt, doc_tham_so(c.get("mau_tham_so")))
	if thieu:
		_huy_voucher(ma_huy, "mẫu đòi tham số máy không có")
		_xong(row.name, TT_LOI, "Mẫu Zalo đòi tham số máy không có: %s. Kiểm lại mã mẫu." % ", ".join(thieu))
		return None
	j = _gui_mau(_cfg(), kh["sdt84"], c["ma_mau"], data, row.khoa)
	ma, cau = y_nghia_loi(j)
	if ma == 0:
		_xong(row.name, TT_GUI, "", sdt=kh["sdt84"], ten_khach=cat(kh["ten"], 140), voucher=ma_v, ma_mau=c["ma_mau"],
			gia=float(c.get("mau_gia") or 0), msg_id=str(((j or {}).get("data") or {}).get("msg_id") or ""))
		try:
			frappe.get_doc({"doctype": "Vagabond Lien He Khach", "khach": row.khach, "kenh": "Zalo OA",
				"ket_qua": cat("Máy gửi tin Zalo: " + kb["ten"], 140), "nguoi": "Administrator",
				"luc": _bay_gio()}).insert(ignore_permissions=True)
			frappe.db.commit()
		except Exception:
			frappe.log_error(title="Vagabond: ghi nhật ký tin Zalo", message=frappe.get_traceback())
		return 0
	# v653 (anh Việt chốt 12/11/2026): Zalo từ chối RIÊNG khách này (không có
	# Zalo, chặn tin...) thì gửi ưu đãi qua WhatsApp, chỉ khi khách đã đồng ý
	# nhận tin. Lỗi của cả lượt (hết hạn mức, mẫu lệch) không rơi sang WhatsApp:
	# dòng còn chờ lượt sau, gửi WhatsApp lúc này là gửi trùng sau đó.
	if ma not in LOI_DUNG_LUOT and gt.get("ten_uu_dai"):
		ok_w, loi_w = _gui_wa_uu_dai(kh, gt)
		if ok_w:
			_xong(row.name, TT_GUI, "Zalo không gửi được (%s), đã gửi qua WhatsApp." % cat(cau, 200), sdt=kh["sdt84"],
				ten_khach=cat(kh["ten"], 140), voucher=ma_v, ma_mau=c["ma_mau"], gia=0, msg_id="")
			return 0
		if loi_w:
			cau = "%s. WhatsApp: %s" % (cau, loi_w)
	_huy_voucher(ma_huy, cau)
	if ma in LOI_DUNG_LUOT:
		# Lỗi của cả lượt: để dòng chờ cho lượt sau, ghi lý do để màn hiện.
		frappe.db.set_value(DT_TIN, row.name, {"loi": cau}, update_modified=False)
		frappe.db.commit()
		if ma in LOI_MAU_DU_LIEU:
			_bao_mau_loi(kb, c, cau)
		return ma
	_xong(row.name, TT_LOI, cau, sdt=kh["sdt84"], ten_khach=cat(kh["ten"], 140), ma_mau=c["ma_mau"])
	return None


def _bao_mau_loi(kb, c, cau):
	"""Báo Marketing: tin của kịch bản bị Zalo từ chối vì dữ liệu không khớp
	mẫu. Một lần mỗi ngày mỗi kịch bản; lỗi gửi báo không làm hỏng lượt."""
	from vagabond import kenh_zalo

	try:
		kenh_zalo.bao_hoac_ghi_loi("canh_bao", "ban_hang", "Tin Zalo cho khách đang dừng: " + cat(kb["ten"], 60),
			["Mẫu %s: %s" % (c.get("ma_mau") or "", cau), "Tin để chờ, không mất. Báo kỹ thuật sửa, hoặc đổi mẫu đúng ở màn Tin Zalo tự động."],
			khoa="zalo_mau_loi:%s:%s" % (kb["ma"], _bay_gio().date().isoformat()), ma_tin="mkt_zalo_mau_loi")
		frappe.db.commit()
	except Exception:
		frappe.log_error(title="Vagabond: báo lỗi mẫu tin Zalo", message=frappe.get_traceback())


def _han_muc_km():
	"""Số tin khuyến mãi OA còn gửi được hôm nay. Không đọc được thì 0
	(an toàn: không phát voucher khi không chắc Zalo cho gửi)."""
	q = _han_muc() or {}
	if not q.get("ok"):
		return 0
	return max(0, min(so_nguyen(q.get("con_km_thang")), so_nguyen(q.get("con_km_ngay"))))


def gui_hang_doi():
	"""Gửi các dòng chờ của mọi kịch bản đang bật, trong giờ, dưới trần."""
	luc = _bay_gio()
	tom = {}
	for kb in KICH_BAN:
		c = _cau_hinh(kb["ma"]) or {}
		if not int(c.get("bat") or 0):
			continue
		kiem = c.get("mau_kiem_luc")
		cu = (not kiem) or get_datetime(kiem) < luc - timedelta(hours=(6 if c.get("mau_trang_thai") == "ENABLE" else 0.5))
		if cu:
			c = kiem_mau(kb["ma"]) or c
		# Dòng chờ quá hạn thì bỏ, voucher chưa phát nên không có gì phải thu hồi.
		frappe.db.sql("""update `tabVagabond Tin Zalo Khach` set trang_thai = %s, loi = %s
			where kich_ban = %s and trang_thai = %s and creation < %s""",
			(TT_BO, "Quá %d giờ chưa gửi được." % CHO_TOI_DA_GIO, kb["ma"], TT_CHO, luc - timedelta(hours=CHO_TOI_DA_GIO)))
		frappe.db.commit()
		duoc, ly_do = mau_san_sang(c)
		if not duoc:
			tom[kb["ma"]] = ly_do
			continue
		if not trong_gio(luc, c.get("gio_tu"), c.get("gio_den")):
			tom[kb["ma"]] = "Ngoài giờ gửi."
			continue
		if kb["km"] and kb.get("kieu") != "co_san":
			# Chương trình hết hạn hay chưa bắt đầu: giữ dòng chờ, không phát mã
			# (Codex PR #517). Sửa chương trình xong thì lượt sau gửi tiếp.
			han, ly_do = ctkm_phat_duoc(_doc_ctkm(c.get("ctkm")), luc.date(), c.get("han_ngay"))
			if not han:
				tom[kb["ma"]] = ly_do + " Tin để chờ."
				continue
		con = con_duoc_gui(c.get("tran_ngay"), _da_gui_hom_nay(kb["ma"]))
		if kb["km"] and con:
			con = min(con, _han_muc_km())
			if not con:
				tom[kb["ma"]] = "Zalo chưa cấp hạn mức tin khuyến mãi cho OA, tin để chờ."
				continue
		if not con:
			tom[kb["ma"]] = "Đã đủ trần tin hôm nay."
			continue
		rows = frappe.db.get_all(DT_TIN, filters={"kich_ban": kb["ma"], "trang_thai": TT_CHO},
			fields=["name", "khach", "hoa_don", "diem", "khoa", "voucher"], order_by="creation asc", limit_page_length=con)
		gui = 0
		dung = None
		het_gio = False
		for r in rows:
			# Mỗi tin là một lời gọi mạng: đọc lại đồng hồ trước từng tin, qua
			# giờ đóng thì dừng, các dòng còn lại để chờ (Codex PR #517).
			if not trong_gio(_bay_gio(), c.get("gio_tu"), c.get("gio_den")):
				het_gio = True
				break
			try:
				m = _gui_mot(c, r)
			except Exception:
				frappe.db.rollback()
				frappe.log_error(title="Vagabond: gửi tin Zalo kịch bản", message=frappe.get_traceback())
				_xong(r.name, TT_LOI, "Lỗi máy khi gửi, xem Error Log.")
				continue
			if m == 0:
				gui += 1
			elif m:
				dung = m
				break
		tom[kb["ma"]] = "Đã gửi %d tin." % gui + ((" Dừng lượt: " + (LOI_ZALO.get(dung) or str(dung))) if dung else "") + \
			(" Hết giờ gửi, các tin còn lại để chờ." if het_gio else "")
	for ma, chu in tom.items():
		frappe.db.set_value(DT_KB, ma, "ket_qua_luot", cat("%s %s" % (luc.strftime("%H:%M %d/%m"), chu), 300), update_modified=False)
	frappe.db.commit()
	return tom


def chay_tu_dong():
	"""Nhịp 5 phút: quét dòng chờ rồi gửi. Lỗi ghi Error Log, không ném."""
	try:
		_dam_bao()
		frappe.db.commit()
	except Exception:
		frappe.log_error(title="Vagabond: tin Zalo tự động, dựng cấu hình", message=frappe.get_traceback())
		return
	luc = _bay_gio()
	for ma, ham in (("sau_mua", quet_sau_mua), ("gioi_thieu", quet_gioi_thieu)):
		try:
			ham()
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title="Vagabond: tin Zalo tự động, quét " + ma, message=frappe.get_traceback())
	for kb in KICH_BAN:
		ma = kb["ma"]
		if ma not in QUET_THEO_NGAY:
			continue
		ham = globals()[QUET_THEO_NGAY[ma]]
		c = _cau_hinh(ma) or {}
		if not int(c.get("bat") or 0) or str(c.get("quet_ngay") or "") == str(luc.date()):
			continue
		try:
			ham(luc.date())
			frappe.db.set_value(DT_KB, ma, "quet_ngay", luc.date(), update_modified=False)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title="Vagabond: tin Zalo tự động, quét " + ma, message=frappe.get_traceback())
	try:
		gui_hang_doi()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="Vagabond: tin Zalo tự động, gửi", message=frappe.get_traceback())


# ================================================================ báo cáo tuần

# v645 (anh Việt 08/11/2026): thứ Hai Marketing nhận một tin tổng kết ưu đãi Zalo.
KB_DO_HIEU_QUA = tuple(k["ma"] for k in KICH_BAN if k.get("doi_chung"))


def ty_le(a, b):
	"""Phần trăm làm tròn, chia 0 thì None. THUẦN."""
	a, b = so_nguyen(a), so_nguyen(b)
	return None if not b else int(round(100.0 * a / b))


def soan_bao_cao_tuan(so, den_ngay):
	"""Câu tin báo cáo tuần từ số đã đọc. THUẦN.

	so: {"gui": {ma: n}, "loi": n, "ma_phat": n, "ma_dung": n, "giam": tiền, "doanh_thu": tiền,
	     "hq": {"nhan": [quay_lai, tong], "dc": [quay_lai, tong]}}
	"""
	gui = so.get("gui") or {}
	dong = ["Ưu đãi qua Zalo, 7 ngày tới %s" % ngay_vn(den_ngay)]
	co = [(k["ten"], so_nguyen(gui.get(k["ma"]))) for k in KICH_BAN if so_nguyen(gui.get(k["ma"]))]
	dong.append("Tin đã gửi: " + ("; ".join("%s %d" % x for x in co) if co else "chưa có tin nào"))
	dong.append("Mã ưu đãi: phát %d, khách đã dùng %d, giảm %s, doanh thu các đơn có mã %s" % (
		so_nguyen(so.get("ma_phat")), so_nguyen(so.get("ma_dung")), tien_vn(so.get("giam") or 0), tien_vn(so.get("doanh_thu") or 0)))
	hq = so.get("hq") or {}
	nhan, dc = hq.get("nhan") or [0, 0], hq.get("dc") or [0, 0]
	a, b = ty_le(nhan[0], nhan[1]), ty_le(dc[0], dc[1])
	if a is not None and b is not None:
		dong.append("Hiệu quả 30 ngày (đơn thứ hai, mời quay lại; khách nhận tin 30 tới 37 ngày trước, đã đủ 30 ngày): "
			"khách nhận tin quay lại mua %d%% (%d/%d), nhóm đối chứng không nhận tin %d%% (%d/%d)"
			% (a, nhan[0], nhan[1], b, dc[0], dc[1]))
	else:
		dong.append("Hiệu quả 30 ngày: chưa đủ dữ liệu để so với nhóm đối chứng")
	if so_nguyen(so.get("loi")):
		dong.append("Lỗi gửi: %d tin. Xem Chăm sóc khách, Tin Zalo tự động." % so_nguyen(so.get("loi")))
	return "\n".join(dong)


def _so_bao_cao_tuan(luc):
	tu = luc - timedelta(days=7)
	gui, loi = {}, 0
	for r in frappe.db.sql("""select kich_ban, trang_thai, count(*) n from `tabVagabond Tin Zalo Khach`
			where ifnull(luc_gui, creation) >= %s group by kich_ban, trang_thai""", (tu,), as_dict=True):
		if r.trang_thai == TT_GUI:
			gui[r.kich_ban] = int(r.n or 0)
		elif r.trang_thai == TT_LOI:
			loi += int(r.n or 0)
	nguon = "(gui_cho like 'Tin Zalo:%%' or gui_cho like 'Đền bù%%')"
	ma_phat = frappe.db.sql("select count(*) from `tabVagabond Voucher` where creation >= %s and " + nguon, (tu,))[0][0]
	dung = frappe.db.sql("""select count(*) n, sum(ifnull(v.tien_giam, 0)) giam, sum(ifnull(si.grand_total, 0)) dt
		from `tabVagabond Voucher` v left join `tabSales Invoice` si on si.name = v.hoa_don
		where v.trang_thai = 'Da dung' and v.ngay_dung >= %s and """ + nguon.replace("gui_cho", "v.gui_cho"), (tu,), as_dict=True)
	d = (dung or [{}])[0] or {}
	# Dòng của kịch bản đo hiệu quả tạo 30 tới 37 ngày trước, tức đã đủ 30 ngày
	# quan sát (Codex PR 548 b4b18d5: lấy 7 tới 37 ngày thì khách mới nhận tin
	# tuần trước chưa kịp mua vẫn vào mẫu số): ai đã gửi, ai là đối chứng, ai
	# đã mua lại trong 30 ngày sau dòng.
	hq = {"nhan": [0, 0], "dc": [0, 0]}
	if KB_DO_HIEU_QUA:
		rows = frappe.db.sql("""select t.trang_thai, ifnull(t.loi, '') loi,
				exists(select 1 from `tabSales Invoice` si where si.customer = t.khach and si.docstatus = 1
					and ifnull(si.is_return, 0) = 0 and ifnull(si.vgb_huy, 0) = 0
					and si.creation > t.creation and si.creation < date_add(t.creation, interval 30 day)) mua
			from `tabVagabond Tin Zalo Khach` t
			where t.kich_ban in %s and t.creation >= %s and t.creation < %s""",
			(KB_DO_HIEU_QUA, luc - timedelta(days=37), luc - timedelta(days=30)), as_dict=True)
		for r in rows:
			if r.trang_thai == TT_GUI:
				k = "nhan"
			elif r.trang_thai == TT_BO and str(r.loi).startswith(LY_DO_DOI_CHUNG):
				k = "dc"
			else:
				continue
			hq[k][1] += 1
			hq[k][0] += 1 if int(r.mua or 0) else 0
	return {"gui": gui, "loi": loi, "ma_phat": int(ma_phat or 0), "ma_dung": int(d.get("n") or 0),
		"giam": float(d.get("giam") or 0), "doanh_thu": float(d.get("dt") or 0), "hq": hq}


def bao_cao_tuan():
	"""Nhịp thứ Hai 09:07: gửi nhóm Marketing (mã tin mkt_bao_cao_uu_dai)."""
	from vagabond import kenh_zalo

	luc = _bay_gio()
	try:
		tin = soan_bao_cao_tuan(_so_bao_cao_tuan(luc), luc.date())
	except Exception:
		frappe.log_error(title="Vagabond: báo cáo ưu đãi Zalo tuần", message=frappe.get_traceback())
		return None
	kenh_zalo.bao_hoac_ghi_loi("ban_tin", "ban_hang", "Báo cáo ưu đãi Zalo tuần %s" % ngay_vn(luc.date()),
		khoa="bao_cao_uu_dai:%s" % luc.date().isoformat(), ma_tin="mkt_bao_cao_uu_dai", noi_dung=tin)
	frappe.db.commit()
	return tin


# ================================================================ màn hình

DUOC_SUA = ("bat", "ma_mau", "so_ngay", "nhac_lai_ngay", "ctkm", "han_ngay", "ten_uu_dai", "dieu_kien", "tran_ngay", "gio_tu", "gio_den",
	"doi_chung")


def _quyen(xem=True):
	from vagabond import crm

	crm._kiem(crm.CRM_XEM if xem else crm.CRM_LAP, "xem tin Zalo tự động" if xem else "sửa tin Zalo tự động")


def _the(c, dem, hom_nay=None):
	kb = kich_ban(c["ma"]) or {}
	duoc, ly_do = mau_san_sang(c)
	can_ctkm = kb.get("km") and (kb.get("kieu") != "co_san" or str(c["ma"]).startswith("den_bu"))
	if duoc and can_ctkm and hom_nay:
		# Thẻ nói luôn khi chương trình đã chọn hết hạn: máy sẽ giữ tin chờ.
		# v645: đền bù cũng cần chương trình (mã phát lúc quản lý bấm cấp).
		han, ly = ctkm_phat_duoc(_doc_ctkm(c.get("ctkm")), hom_nay, c.get("han_ngay"))
		if not han:
			duoc, ly_do = False, ly
	return {
		"ma": c["ma"], "ten": kb.get("ten"), "giai_thich": kb.get("giai_thich"), "km": kb.get("km"),
		"bat": int(c.get("bat") or 0), "san_sang": 1 if duoc else 0, "ly_do": ly_do,
		"ma_mau": c.get("ma_mau") or "", "mau_trang_thai": TRANG_THAI_MAU.get(c.get("mau_trang_thai") or "", "Chưa kiểm"),
		"mau_duyet": 1 if c.get("mau_trang_thai") == "ENABLE" else 0, "mau_ly_do": c.get("mau_ly_do") or "",
		"mau_gia": c.get("mau_gia") or "", "tham_so": [p.get("name") for p in doc_tham_so(c.get("mau_tham_so"))],
		"so_ngay": c.get("so_ngay"), "nhac_lai_ngay": c.get("nhac_lai_ngay"), "ctkm": c.get("ctkm") or "",
		# v645: chữ ô số ngày theo từng kịch bản (màn không tự đoán theo mã), mã
		# có sẵn thì không chọn chương trình phát mã, và % nhóm đối chứng.
		"kieu": kb.get("kieu") or "", "nhan_ngay": kb.get("nhan_ngay") or "", "goi_y_ngay": kb.get("goi_y_ngay") or "",
		"nhan_nhac": kb.get("nhan_nhac") or "", "do_hieu_qua": 1 if kb.get("doi_chung") else 0,
		"doi_chung": so_nguyen(c.get("doi_chung"), kb.get("doi_chung") or 0),
		"han_ngay": c.get("han_ngay"), "ten_uu_dai": c.get("ten_uu_dai") or "", "dieu_kien": c.get("dieu_kien") or "",
		"tran_ngay": c.get("tran_ngay"), "gio_tu": c.get("gio_tu"), "gio_den": c.get("gio_den"),
		"ket_qua_luot": c.get("ket_qua_luot") or "", "dem": dem.get(c["ma"]) or {},
	}


@frappe.whitelist()
def ds_kich_ban():
	"""Màn Tin Zalo tự động: ba thẻ kịch bản, số đếm, hạn mức Zalo."""
	_quyen()
	_dam_bao()
	frappe.db.commit()
	luc = _bay_gio()
	dau = luc.replace(hour=0, minute=0, second=0, microsecond=0)
	dem = {}
	for r in frappe.db.sql(
		"""select kich_ban, trang_thai, count(*) n, sum(ifnull(gia, 0)) phi,
		sum(case when ifnull(luc_gui, creation) >= %s then 1 else 0 end) hn
		from `tabVagabond Tin Zalo Khach` where creation >= %s group by kich_ban, trang_thai""",
		(dau, luc - timedelta(days=30)), as_dict=True):
		d = dem.setdefault(r.kich_ban, {"hom_nay": {}, "ba_muoi": {}, "phi": 0})
		d["hom_nay"][r.trang_thai] = int(r.hn or 0)
		d["ba_muoi"][r.trang_thai] = int(r.n or 0)
		d["phi"] += float(r.phi or 0)
	ds = [_the(_cau_hinh(k["ma"]), dem, luc.date()) for k in KICH_BAN]
	ctkm = []
	for km in frappe.get_all("Vagabond CTKM", filters={"cach_ma": "Ma dung mot lan", "bat": 1}, fields=COT_CTKM,
			order_by="modified desc", limit_page_length=200):
		# Bỏ chương trình đã hết hạn; chương trình sắp bắt đầu vẫn chọn trước được.
		tu, den = ngay_cua(km.get("tu_ngay")), ngay_cua(km.get("den_ngay"))
		if den and den < luc.date():
			continue
		phu = ("Đến hết %s" % ngay_vn(den)) if den else "Không giới hạn ngày"
		if tu and tu > luc.date():
			phu = "Bắt đầu %s, %s" % (ngay_vn(tu), phu[0].lower() + phu[1:])
		dt_ghi = ghi_doi_tuong(km)
		ctkm.append({"name": km.get("name"), "ten": km.get("ten") or km.get("name"),
			"phu": phu + ((" · " + dt_ghi) if dt_ghi else ""), "doi_tuong": dt_ghi})
	q = _han_muc() or {}
	return {"ds": ds, "ctkm": ctkm, "han_muc": q, "sua": 1 if _co_lap() else 0}


def _co_lap():
	from vagabond import crm

	return crm._co(crm.CRM_LAP)


@frappe.whitelist()
def luu_kich_ban(ma=None, dat=None):
	"""Lưu cài đặt một kịch bản. Bật lần đầu thì chỉ tính việc từ lúc bật."""
	_quyen(xem=False)
	if ma not in MA_KB:
		frappe.throw("Không có kịch bản này.")
	_dam_bao()
	dat = json.loads(dat) if isinstance(dat, str) else (dat or {})
	cu = _cau_hinh(ma)
	v = {}
	for k in DUOC_SUA:
		if k not in dat:
			continue
		x = dat.get(k)
		if k in ("bat",):
			v[k] = 1 if str(x).lower() in ("1", "true") else 0
		elif k in ("so_ngay", "nhac_lai_ngay", "han_ngay", "tran_ngay", "gio_tu", "gio_den"):
			v[k] = so_nguyen(x, cu.get(k) or 0)
		elif k == "doi_chung":
			v[k] = min(so_nguyen(x, cu.get(k) or 0), 50)
		elif k == "ctkm":
			x = str(x or "").strip()
			if x and not frappe.db.exists("Vagabond CTKM", x):
				frappe.throw("Không có chương trình khuyến mãi này.")
			v[k] = x or None
		elif k == "ten_uu_dai":
			v[k] = cat(x, 30)
		elif k == "dieu_kien":
			# v646: ô dieu_kien của mọi mẫu đã duyệt dài tối đa 30 (đọc trên site
			# 09/11/2026); để 40 thì chữ người gõ bị cắt cụt lúc gửi mà không ai biết.
			v[k] = cat(x, 30)
		else:
			v[k] = cat(x, 20)
	if "gio_tu" in v or "gio_den" in v:
		v["gio_tu"], v["gio_den"] = gio_hop_le(v.get("gio_tu", cu.get("gio_tu")), v.get("gio_den", cu.get("gio_den")))
	if v.get("bat") and not int(cu.get("bat") or 0):
		v["bat_luc"] = _bay_gio()
	doi_mau = "ma_mau" in v and v["ma_mau"] != (cu.get("ma_mau") or "")
	if doi_mau:
		v.update(xoa_kiem_mau())
	frappe.db.set_value(DT_KB, ma, v)
	frappe.db.commit()
	if doi_mau:
		kiem_mau(ma)
		frappe.db.commit()
	return ds_kich_ban()


@frappe.whitelist()
def kiem_mau_zalo(ma=None):
	"""Nút Kiểm lại mẫu: hỏi Zalo mẫu đã duyệt chưa. Không tốn tin."""
	_quyen()
	if ma not in MA_KB:
		frappe.throw("Không có kịch bản này.")
	_dam_bao()
	kiem_mau(ma)
	frappe.db.commit()
	return ds_kich_ban()


def dk_loc_tin(ma, ky, tu, den, hom_nay):
	"""Điều kiện phạm vi của sổ tin (kịch bản, khoảng ngày tạo dòng). THUẦN.

	Chip ngày dùng chung `khoang_ky` của mọi màn danh sách; hai đầu đều tính.
	Chip trạng thái KHÔNG nằm ở đây, để số đếm trạng thái tính trên đúng phạm
	vi đang lọc (Codex PR #517 vòng 6).
	"""
	from vagabond.khung.cong_cu_ds import khoang_ky

	loc = [["kich_ban", "=", ma]] if ma in MA_KB else []
	a, b = khoang_ky(ky, hom_nay, tu, den)
	if a:
		loc.append(["creation", ">=", a + " 00:00:00"])
	if b:
		loc.append(["creation", "<", (ngay_cua(b) + timedelta(days=1)).isoformat() + " 00:00:00"])
	return loc


@frappe.whitelist()
def ds_tin(ma=None, trang_thai="", bat_dau=0, tim="", ky="", tu="", den=""):
	"""Các tin gần nhất của một kịch bản, mới nhất trước, mỗi trang 50.
	Tìm chữ và lọc ngày làm ở máy chủ trước phân trang, ra cả dòng chưa tải
	(Codex PR #517 vòng 2, 6); kèm số đếm từng trạng thái trong phạm vi lọc."""
	_quyen()
	pham_vi = dk_loc_tin(ma, ky, tu, den, _bay_gio().date())
	loc = list(pham_vi)
	if trang_thai in TT_TIN:
		loc.append(["trang_thai", "=", trang_thai])
	them = {}
	dk = dk_tim_tin(tim, _khach_khop(tim))
	if dk:
		them["or_filters"] = dk
	dem = {"tat_ca": 0}
	for r in frappe.get_all(DT_TIN, filters=pham_vi, fields=["trang_thai", "count(name) as n"], group_by="trang_thai", **them):
		dem[r.get("trang_thai")] = int(r.get("n") or 0)
		dem["tat_ca"] += int(r.get("n") or 0)
	rows = frappe.get_all(DT_TIN, filters=loc, fields=["name", "kich_ban", "khach", "ten_khach", "sdt", "hoa_don", "voucher",
		"trang_thai", "loi", "creation", "luc_gui"], order_by="creation desc", limit_start=so_nguyen(bat_dau), limit_page_length=51, **them)
	ten = {}
	kh = list({r.khach for r in rows if r.khach and not r.ten_khach})
	if kh:
		for x in frappe.get_all("Customer", filters={"name": ["in", kh]}, fields=["name", "customer_name"]):
			ten[x.name] = x.customer_name
	ds = [{"kich_ban": r.kich_ban, "khach": r.khach, "ten_khach": r.ten_khach or ten.get(r.khach) or r.khach,
		"sdt": che_sdt(r.sdt), "hoa_don": r.hoa_don or "", "voucher": r.voucher or "", "trang_thai": r.trang_thai,
		"loi": r.loi or "", "luc": str(r.luc_gui or r.creation)} for r in rows[:50]]
	return {"ds": ds, "con_nua": 1 if len(rows) > 50 else 0, "dem": dem}


MAU_THU = {
	"ten_khach": "Khách thử", "ma_hoa_don": "HDB-THU-0001", "ngay_mua": "29/10/2026 15:30", "tong_tien": "450.000đ",
	"diem_tich": "9.000", "tong_diem": "25.400", "hang": "EXPLORER", "ten_uu_dai": "Giảm 10%",
	"dieu_kien": "Dùng 1 lần cho 1 hoá đơn", "han_dung": "30/11/2026", "ma_voucher": "THUTHU",
	"diem_het_han": "12.000", "ngay_het_han": "31/01/2027", "diem_hoan": "20.000", "ma_don": "DW-2611-00123",
}


@frappe.whitelist()
def gui_thu(ma=None, sdt=None):
	"""Gửi MỘT tin thử của kịch bản vào số người bấm nhập, với dữ liệu mẫu.
	Mã voucher trong tin thử là mã giả, không dùng được."""
	from vagabond.lib import sdt84

	_quyen(xem=False)
	if ma not in MA_KB:
		frappe.throw("Không có kịch bản này.")
	so = sdt84(sdt)
	if not so:
		frappe.throw("Số điện thoại chưa đúng. Nhập số di động 10 số.")
	c = kiem_mau(ma)
	frappe.db.commit()
	if (c or {}).get("mau_trang_thai") != "ENABLE":
		frappe.throw("Mẫu tin chưa được Zalo duyệt nên chưa gửi thử được.")
	data, thieu = du_lieu_mau(MAU_THU, doc_tham_so(c.get("mau_tham_so")))
	if thieu:
		frappe.throw("Mẫu Zalo đòi tham số máy không có: %s." % ", ".join(thieu))
	j = _gui_mau(_cfg(), so, c["ma_mau"], data, "vgb-thu-%s" % ma)
	m, cau = y_nghia_loi(j)
	return {"ok": 1 if m == 0 else 0, "loi": cau, "sdt": che_sdt(so)}

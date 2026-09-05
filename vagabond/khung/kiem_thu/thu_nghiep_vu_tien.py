# -*- coding: utf-8 -*-
"""Ca kiểm cho phần xếp nghiệp vụ phiếu thu chi và trạng thái thanh toán."""

import io
import os

from vagabond import nghiep_vu_tien as N
from vagabond import trang_thai_tra as T
from vagabond.khung.kiem_thu.nen import ca, dung


def _doc(duong):
	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	return io.open(os.path.join(os.path.dirname(goc), duong), encoding="utf-8").read()


# ------------------------------------------------------ xếp nghiệp vụ


@ca("nghiệp vụ tiền: cờ do luồng đóng lên được tin trước mọi phép suy")
def _co_thang_phep_suy():
	"""Hai cờ này do chính luồng sinh phiếu đóng lên nên tin được tuyệt đối.

	Ca kiểm này chốt đúng thứ tự xét, vì đảo lại là hỏng ngay: phiếu hoàn
	tiền khách cũng là phiếu chi gửi tới một bên đối tác, mà phiếu hoàn
	ứng có hoá đơn thì lại mang tên nhà cung cấp thật.
	"""
	dung("cờ hoàn tiền thắng phép suy theo hình dạng",
		N.nghiep_vu_cua_phieu("Pay", "Customer", co_hoan_tien=1) == N.N_HOAN_KHACH)
	dung("cờ hồ sơ hoàn ứng thắng phép suy theo dòng tham chiếu",
		N.nghiep_vu_cua_phieu("Pay", "Supplier", loai_ho_so="Hoan ung",
			ds_tham_chieu=["Purchase Invoice"]) == N.N_HOAN_UNG)
	dung("hoàn ứng CÓ hoá đơn vẫn ra hoàn ứng, dù phiếu mang tên NCC thật",
		N.nghiep_vu_cua_phieu("Pay", "Supplier", loai_ho_so="Hoan ung HD",
			ds_tham_chieu=["Purchase Invoice"]) == N.N_HOAN_UNG)
	dung("hồ sơ loại NCC thì KHÔNG phải hoàn ứng",
		N.nghiep_vu_cua_phieu("Pay", "Supplier", loai_ho_so="NCC",
			ds_tham_chieu=["Purchase Invoice"]) == N.N_TRA_NCC)


@ca("nghiệp vụ tiền: neo vào đơn mua là trả trước, neo vào hoá đơn là trả nợ")
def _tra_truoc_khac_tra_no():
	"""Đây là ranh giới nghiệp vụ thật chứ không phải mẹo đọc dữ liệu.

	Còn ở đơn mua nghĩa là hàng chưa về và hoá đơn chưa có, nên tiền đó là
	tiền đặt cọc. Neo vào hoá đơn mua là trả khoản nợ đã phát sinh.
	"""
	dung("neo vào đơn mua là trả trước",
		N.nghiep_vu_cua_phieu("Pay", "Supplier",
			ds_tham_chieu=["Purchase Order"]) == N.N_TRA_TRUOC)
	dung("neo vào hoá đơn mua là trả công nợ",
		N.nghiep_vu_cua_phieu("Pay", "Supplier",
			ds_tham_chieu=["Purchase Invoice"]) == N.N_TRA_NCC)
	dung("có cả hai thì trả trước xét trước, vì đơn mua là căn cứ hẹp hơn",
		N.nghiep_vu_cua_phieu("Pay", "Supplier",
			ds_tham_chieu=["Purchase Invoice", "Purchase Order"]) == N.N_TRA_TRUOC)


@ca("nghiệp vụ tiền: chuyển nội bộ tách trước vì nó không có bên đối tác")
def _noi_bo():
	"""Chuyển nội bộ để trống party_type nên phải tách trước, kẻo rơi nhầm
	xuống nhánh dưới và bị xếp thành "Chi khác".

	Sự cố 16/08/2026 trong chung_tu_tien.py đúng là ca này: Internal
	Transfer không rơi gọn vào nhánh Pay hay Receive.
	"""
	dung("nhận ra ngay từ loại thanh toán",
		N.nghiep_vu_cua_phieu("Internal Transfer", "") == N.N_NOI_BO)
	dung("không phân biệt hoa thường",
		N.nghiep_vu_cua_phieu("internal transfer", "") == N.N_NOI_BO)
	dung("chuyển nội bộ KHÔNG làm tiền của tiệm tăng lên",
		N.la_tien_vao(N.N_NOI_BO) is False)


@ca("nghiệp vụ tiền: thà nói chưa xếp được còn hơn xếp sai")
def _khong_doan_bua():
	"""Một ô đoán sai làm kế toán tin nhầm còn hại hơn một ô nói thẳng là
	chưa xếp được. Đây cũng đúng bài học của ô bước hoá đơn mua ở v420.
	"""
	dung("chi cho khách mà không có cờ hoàn tiền thì KHÔNG đoán là hoàn tiền",
		N.nghiep_vu_cua_phieu("Pay", "Customer") == N.N_CHI_KHAC)
	dung("chi cho NCC mà không neo vào đâu cả thì chưa xếp được",
		N.nghiep_vu_cua_phieu("Pay", "Supplier") == N.N_CHI_KHAC)
	dung("thu mà không có bên đối tác thì chưa xếp được",
		N.nghiep_vu_cua_phieu("Receive", "") == N.N_THU_KHAC)
	dung("loại thanh toán lạ thì trả rỗng, không bịa",
		N.nghiep_vu_cua_phieu("", "") == "")


@ca("nghiệp vụ tiền: thu tiền khách và hai nhóm khác được đúng màu")
def _thu_va_mau():
	dung("thu của khách là thu tiền khách",
		N.nghiep_vu_cua_phieu("Receive", "Customer") == N.N_THU_KHACH)
	dung("thu tiền khách làm tiền của tiệm tăng", N.la_tien_vao(N.N_THU_KHACH) is True)
	dung("trả nhà cung cấp không làm tiền tăng", N.la_tien_vao(N.N_TRA_NCC) is False)

	dung("thu tiền khách màu xanh lá", N.mau_cua_nghiep_vu(N.N_THU_KHACH) == "green")
	dung("hai nhóm chưa xếp được mang màu đỏ để người ngó tới",
		N.mau_cua_nghiep_vu(N.N_THU_KHAC) == "red"
		and N.mau_cua_nghiep_vu(N.N_CHI_KHAC) == "red")
	so_do = len([1 for x in N.DS_NGHIEP_VU if N.mau_cua_nghiep_vu(x) == "red"])
	dung("không quá hai nghiệp vụ mang màu đỏ", so_do <= 2)


@ca("nghiệp vụ tiền: đã nối đủ dây từ máy chủ ra tới màn danh sách")
def _noi_day_nghiep_vu():
	s = _doc("vagabond/nghiep_vu_tien.py")
	dung("có khai trường mới", "TRUONG_MOI" in s and '"vgb_nghiep_vu"' in s)
	dung("trường để chế độ chỉ đọc", '"read_only": 1' in s)
	dung("có bật ô lọc sẵn trên đầu màn", '"in_standard_filter": 1' in s)
	dung("có khai ô cờ hồ sơ thanh toán", '"vgb_ho_so_tt"' in s)

	than = s.split("def dat_nghiep_vu(")[1]
	dung("hàm đặt nghiệp vụ nuốt lỗi, không làm rớt việc lưu chứng từ tiền",
		"frappe.log_error" in than)

	nap = s.split("def nap_lai_hang_loat(")[1]
	dung("chỉ nhận phiếu còn trống ô", 'TRUONG: ["in", ["", None]]' in nap)
	dung("không làm xê dịch ngày sửa của ai", "update_modified=False" in nap)
	dung("chỉ ghi đúng một ô, không mở cả phiếu",
		"frappe.db.set_value" in nap and "get_doc(" not in nap)

	h = _doc("vagabond/hooks.py")
	dung("hook đã cắm vào lượt lưu phiếu thu chi",
		"vagabond.nghiep_vu_tien.dat_nghiep_vu" in h)
	dung("màn danh sách phiếu thu chi đã được khai",
		'"Payment Entry": "public/js/payment_entry_list.js"' in h)

	t = _doc("vagabond/truong_tu_them.py")
	dung("trường mới được dựng lúc chuyển cấu trúc",
		"nghiep_vu_tien.TRUONG_MOI" in t)

	p = _doc("vagabond/patches/dong_bo_cau_truc.py")
	dung("có nạp lại cho phiếu cũ", "nghiep_vu_tien.nap_lai_hang_loat()" in p)

	hs = _doc("vagabond/ho_so_tt.py")
	dung("hồ sơ thanh toán tự khai mình là cha của phiếu chi",
		"pe.vgb_ho_so_tt = doc.name" in hs)

	j = _doc("vagabond/public/js/payment_entry_list.js")
	for x in N.DS_NGHIEP_VU:
		dung("màn danh sách biết nghiệp vụ %s" % x, x in j)
	dung("có bật cờ cho phiếu nháp", "has_indicator_for_draft = 1" in j)
	dung("có bật cờ cho phiếu đã huỷ", "has_indicator_for_cancelled = 1" in j)
	dung("màn danh sách không tự xếp lại nghiệp vụ",
		"party_type ===" not in j and "reference_doctype" not in j)
	dung("không dùng dấu gạch dài", "—" not in j and "–" not in j)


# ------------------------------------------------------ trạng thái trả


@ca("trạng thái trả: tờ chưa ghi sổ thì chưa có chuyện nợ nần gì")
def _chua_ghi_so():
	"""Tờ chưa ghi sổ thì chưa phát sinh công nợ. Gọi nó "chưa thanh toán"
	là nói thừa và làm người đọc tưởng có ai đó đang nợ.
	"""
	dung("nháp thì nói là chưa ghi sổ",
		T.trang_thai_tra(1000, 1000, ghi_so=0) == T.T_CHUA_GHI)
	dung("nháp đã trả hết cũng vẫn là chưa ghi sổ",
		T.trang_thai_tra(1000, 0, ghi_so=0) == T.T_CHUA_GHI)


@ca("trạng thái trả: tách riêng trả một phần với chưa trả đồng nào")
def _mot_phan():
	"""Gộp hai nhóm này là mất đúng thông tin đáng giá nhất. Tờ chưa trả
	đồng nào và tờ đã trả tám phần mười là hai tình huống khác hẳn nhau
	khi đi đòi nợ hay khi xếp lịch chi.
	"""
	dung("còn nợ đúng bằng tổng tờ là chưa trả đồng nào",
		T.trang_thai_tra(1000, 1000) == T.T_CHUA_TRA)
	dung("còn nợ ít hơn tổng là đã trả được một phần",
		T.trang_thai_tra(1000, 300) == T.T_MOT_PHAN)
	dung("hết nợ là đã thanh toán", T.trang_thai_tra(1000, 0) == T.T_DA_TRA)
	dung("lẻ dưới một đồng coi như hết nợ",
		T.trang_thai_tra(1000, 0.4) == T.T_DA_TRA)
	dung("trả quá tay thì nói thẳng là trả thừa",
		T.trang_thai_tra(1000, -500) == T.T_TRA_THUA)


@ca("trạng thái trả: hạn bằng ngày lập thì KHÔNG gọi là quá hạn")
def _qua_han():
	"""525 nhà cung cấp không ai được khai điều khoản thanh toán nên hạn
	trả bằng luôn ngày lập. Gọi hết là quá hạn thì chữ đó thành hằng số và
	mất nghĩa, đúng bài học đã ghi ở bản v420.
	"""
	dung("hạn bằng ngày lập là chưa khai điều khoản, không phải quá hạn",
		T.qua_han("2026-09-01", "2026-09-01", "2026-09-05") is False)
	dung("hạn thật đã trôi qua mới là quá hạn",
		T.qua_han("2026-09-01", "2026-09-03", "2026-09-05") is True)
	dung("hạn thật còn ở phía trước thì chưa quá hạn",
		T.qua_han("2026-09-01", "2026-09-30", "2026-09-05") is False)
	dung("thiếu ngày nào thì không kết luận",
		T.qua_han("", "2026-09-03", "2026-09-05") is False)

	dung("tờ quá hạn xét trước tờ trả một phần, vì gấp hơn",
		T.trang_thai_tra(1000, 300, 1, "2026-09-01", "2026-09-03", "2026-09-05")
		== T.T_QUA_HAN)
	dung("tờ đã trả hết thì không bao giờ là quá hạn",
		T.trang_thai_tra(1000, 0, 1, "2026-09-01", "2026-09-03", "2026-09-05")
		== T.T_DA_TRA)


@ca("trạng thái trả: phần trăm đã trả nói đúng tờ ở gần đầu hay gần cuối")
def _phan_tram():
	dung("chưa trả gì là 0", T.phan_tram_da_tra(1000, 1000) == 0)
	dung("trả hết là 100", T.phan_tram_da_tra(1000, 0) == 100)
	dung("trả ba phần mười", T.phan_tram_da_tra(1000, 700) == 30)
	dung("tổng bằng 0 thì không chia cho 0", T.phan_tram_da_tra(0, 0) == 0)
	dung("trả thừa vẫn kẹp ở 100", T.phan_tram_da_tra(1000, -200) == 100)


@ca("trạng thái trả: màu không được đỏ hết, chỉ quá hạn mới đỏ")
def _mau_tra():
	"""Chưa thanh toán là chuyện bình thường của mọi tờ vừa ghi sổ. Tô đỏ
	hết thì đỏ mất nghĩa, đúng bài học của chữ "Quá hạn" cũ.
	"""
	dung("đã thanh toán là xanh lá", T.mau_cua_trang_thai(T.T_DA_TRA) == "green")
	dung("quá hạn là đỏ", T.mau_cua_trang_thai(T.T_QUA_HAN) == "red")
	dung("chưa thanh toán là cam chứ không đỏ",
		T.mau_cua_trang_thai(T.T_CHUA_TRA) == "orange")
	so_do = len([1 for x in T.DS_TRANG_THAI if T.mau_cua_trang_thai(x) == "red"])
	dung("chỉ đúng một trạng thái mang màu đỏ", so_do == 1)


@ca("trạng thái trả: hai màn hoá đơn nói cùng một giọng")
def _hai_man_cung_giong():
	"""Trước bản này màn mua chỉ chia được hai mức, màn bán không có gì.
	Cùng một câu hỏi mà hai màn trả lời hai kiểu.

	Phép tính bên màn danh sách là bản chép của trang_thai_tra.py. Ca kiểm
	này chốt rằng cả sáu tên trạng thái đều có mặt đủ ở cả hai nơi, để lần
	sau sửa một bên mà quên bên kia thì cổng đỏ ngay.
	"""
	j = _doc("vagabond/public/js/minvoice_list.js")
	for x in T.DS_TRANG_THAI:
		dung("màn danh sách biết trạng thái %s" % x, x in j)
	dung("có hàm tính dùng chung cho cả hai màn", "function chipTra(" in j)
	dung("màn hoá đơn mua gọi hàm chung", "ganTrangThaiMuaHang" in j)
	dung("màn hoá đơn bán đã được dựng", "ganTrangThaiBanHang" in j)
	dung("màn bán có bật cờ cho tờ nháp",
		"has_indicator_for_draft" in j.split("ganTrangThaiBanHang")[1])
	dung("màn bán kéo về đủ ô để tính", "'grand_total'" in j)
	dung("tờ trả hàng được nói riêng chứ không gọi là trả thừa",
		"'Trả hàng'" in j)
	dung("không dùng dấu gạch dài", "—" not in j and "–" not in j)

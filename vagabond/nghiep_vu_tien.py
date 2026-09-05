# -*- coding: utf-8 -*-
"""Phiếu thu chi thuộc NGHIỆP VỤ nào, hiện ngay trên màn danh sách.

VÌ SAO CÓ TỆP NÀY (anh Việt nói 05/09/2026)
-------------------------------------------
Nguyên văn: "Phiếu thu/chi về bản chất là tiền mặt thì anh thấy vẫn lung
tung khách ở trong phiếu thu/chi. Nó chẳng phải là APP gì cả."

Anh nói đúng, và đây là lý do. Có SÁU nghiệp vụ hoàn toàn khác nhau, của
sáu người khác nhau, đang đổ chung vào đúng một doctype Payment Entry:

  1. Thu tiền khách trả hoá đơn bán
  2. Trả công nợ nhà cung cấp
  3. Trả trước cho nhà cung cấp, tức đặt cọc khi chưa có hoá đơn
  4. Hoàn ứng cho nhân viên, đi qua một bản ghi Supplier đội lốt
  5. Hoàn tiền cho khách khi đơn bị huỷ hoặc khách nộp thừa
  6. Chuyển tiền nội bộ giữa hai tài khoản của chính công ty

Sáu thứ đó chung một màn, chung một đường duyệt, mà TRƯỚC BẢN NÀY không có
một ô nào nói ra nó là loại gì. Ô `vgb_loai_ct` sẵn có không giải quyết
được, vì ô đó chỉ đọc số hiệu tài khoản để gọi tên chứng từ cho đúng luật
kế toán: 111 thì gọi Phiếu thu hay Phiếu chi, 112 thì gọi Uỷ nhiệm chi hay
Giấy báo Có. Nó nói tiền đi qua đâu, không nói việc đó là việc gì.

Nên muốn tìm phiếu hoàn ứng của một bạn nhân viên, mắt phải tự lọc giữa
phiếu trả nhà cung cấp và phiếu hoàn tiền khách, vì cả ba đều là "Phiếu
chi" gửi tới một "Supplier". Đó chính là chỗ lung tung anh nhìn thấy.

CHỌN CÁCH NÀO ĐỂ NHẬN RA NGHIỆP VỤ
----------------------------------
Có hai cách và tệp này dùng cả hai, theo đúng thứ tự tin cậy.

CÁCH CHẮC: đọc CỜ mà chính luồng sinh ra phiếu đã đóng lên nó. Luồng hoàn
tiền khách đã có sẵn cờ `vgb_hoan_tien` từ trước. Bản này thêm cờ
`vgb_ho_so_tt` cho luồng hồ sơ thanh toán, vì đó là chỗ duy nhất biết chắc
một khoản là hoàn ứng nhân viên hay trả nhà cung cấp thật.

VÌ SAO PHẢI THÊM CỜ ĐÓ: khoản hoàn ứng CÓ hoá đơn thì phiếu chi cuối cùng
lại mang tên nhà cung cấp thật đọc từ hoá đơn, chứ không mang tên người
được hoàn ứng. Nhìn vào phiếu không tài nào biết được. Chỉ hồ sơ thanh
toán mới biết, nên phải để hồ sơ tự khai ra lúc nó dựng phiếu.

CÁCH SUY: phiếu cũ không có cờ thì suy từ hình dạng, và chỗ suy đáng tin
nhất là DÒNG THAM CHIẾU. Phiếu neo vào đơn mua hàng là trả trước; phiếu
neo vào hoá đơn mua là trả công nợ. Đây không phải mẹo, nó là ranh giới
nghiệp vụ thật: còn ở đơn mua nghĩa là hàng chưa về, hoá đơn chưa có.

NGUYÊN TẮC: THÀ NÓI KHÔNG BIẾT CÒN HƠN NÓI SAI
----------------------------------------------
Phiếu nào không đủ căn cứ thì trả về "Thu khác" hoặc "Chi khác", không cố
đoán. Một ô đoán sai làm kế toán tin nhầm còn hại hơn một ô nói thẳng là
chưa xếp được. Đây cũng đúng bài học của ô bước hoá đơn mua ở bản v420.
"""

import frappe
from frappe.utils import cint

PE = "Payment Entry"
TRUONG = "vgb_nghiep_vu"

# Tên nghiệp vụ. GIỮ NGUYÊN chuỗi khi sửa: màn danh sách và bộ lọc đã lưu
# của kế toán đều neo vào đúng mấy chữ này.
N_THU_KHACH = "Thu tiền khách"
N_HOAN_KHACH = "Hoàn tiền khách"
N_TRA_NCC = "Trả nhà cung cấp"
N_TRA_TRUOC = "Trả trước nhà cung cấp"
N_HOAN_UNG = "Hoàn ứng nhân viên"
N_NOI_BO = "Chuyển nội bộ"
N_THU_KHAC = "Thu khác"
N_CHI_KHAC = "Chi khác"

DS_NGHIEP_VU = [
	N_THU_KHACH, N_HOAN_KHACH, N_TRA_NCC, N_TRA_TRUOC,
	N_HOAN_UNG, N_NOI_BO, N_THU_KHAC, N_CHI_KHAC,
]

# Loại hồ sơ thanh toán được tính là hoàn ứng nhân viên. Hai chuỗi này phải
# khớp đúng hằng LOAI_HU và LOAI_HU_HD trong ho_so_tt.py.
LOAI_HOAN_UNG = ("Hoan ung", "Hoan ung HD")

TRUONG_MOI = {
	PE: [
		{
			"fieldname": TRUONG,
			"label": "Nghiệp vụ",
			"fieldtype": "Select",
			"options": "\n" + "\n".join(DS_NGHIEP_VU),
			"insert_after": "vgb_loai_ct",
			"read_only": 1,
			"in_standard_filter": 1,
			"in_list_view": 1,
			"description": (
				"Phiếu này thuộc việc gì: thu tiền khách, trả nhà cung cấp, "
				"trả trước, hoàn ứng nhân viên, hoàn tiền khách hay chuyển "
				"nội bộ. Máy tự xếp mỗi lần lưu, không gõ tay. Khác ô Loại "
				"chứng từ: ô kia nói tiền đi qua tài khoản nào."
			),
		},
		{
			"fieldname": "vgb_ho_so_tt",
			"label": "Hồ sơ thanh toán",
			"fieldtype": "Link",
			"options": "Vagabond Ho So TT",
			"insert_after": "vgb_hoan_tien",
			"read_only": 1,
			"description": (
				"Hồ sơ thanh toán đã dựng ra phiếu này. Nhờ ô này mới phân "
				"biệt được khoản hoàn ứng nhân viên với khoản trả nhà cung "
				"cấp thật, vì khoản hoàn ứng có hoá đơn thì phiếu lại mang "
				"tên nhà cung cấp chứ không mang tên người được hoàn ứng."
			),
		},
	],
}


# ------------------------------------------------------------ phép thuần


def nghiep_vu_cua_phieu(loai_tt, ben, co_hoan_tien=0, loai_ho_so="", ds_tham_chieu=None):
	"""Phiếu này thuộc nghiệp vụ nào. THUẦN, không chạm Frappe.

	`loai_tt` là payment_type (Receive, Pay, Internal Transfer).
	`ben` là party_type (Customer, Supplier, rỗng).
	`co_hoan_tien` là phiếu có mang cờ hoàn tiền khách không.
	`loai_ho_so` là loại của hồ sơ thanh toán đã dựng ra phiếu, rỗng nếu không có.
	`ds_tham_chieu` là danh sách reference_doctype của các dòng tham chiếu.

	Thứ tự xét đi từ căn cứ CHẮC tới căn cứ SUY, không được đảo:

	  1. Chuyển nội bộ nhận ra ngay từ loại thanh toán, và nó không có bên
	     đối tác nào cả nên phải tách trước, kẻo rơi nhầm vào nhánh dưới.
	  2. Cờ hoàn tiền khách và cờ hồ sơ hoàn ứng là do chính luồng sinh
	     phiếu đóng lên, tin được tuyệt đối, nên xét trước mọi phép suy.
	  3. Còn lại mới suy từ hình dạng phiếu.
	"""
	lt = str(loai_tt or "").strip().lower()
	b = str(loai_ho_so or "").strip()
	ds = [str(x or "").strip() for x in (ds_tham_chieu or [])]

	if lt == "internal transfer":
		return N_NOI_BO

	if cint(co_hoan_tien):
		return N_HOAN_KHACH
	if b in LOAI_HOAN_UNG:
		return N_HOAN_UNG

	ben = str(ben or "").strip().lower()

	if lt == "receive":
		if ben == "customer":
			return N_THU_KHACH
		return N_THU_KHAC

	if lt == "pay":
		if ben == "supplier":
			# Neo vào ĐƠN MUA nghĩa là hàng chưa về và hoá đơn chưa có, tức
			# là tiền đặt cọc. Neo vào HOÁ ĐƠN MUA là trả nợ đã phát sinh.
			if "Purchase Order" in ds:
				return N_TRA_TRUOC
			if "Purchase Invoice" in ds:
				return N_TRA_NCC
			return N_CHI_KHAC
		if ben == "customer":
			# Chi cho khách mà không mang cờ hoàn tiền: có thể là phiếu tay
			# kế toán tự lập. Không đoán bừa là hoàn tiền.
			return N_CHI_KHAC
		return N_CHI_KHAC

	return ""


def mau_cua_nghiep_vu(nv):
	"""Màu của một nghiệp vụ trên màn danh sách. THUẦN.

	Xanh lá cho tiền VÀO, cam cho tiền RA có đối tác rõ, xám cho chuyển
	nội bộ vì nó không làm đổi tổng tiền của tiệm, và đỏ cho hai nhóm
	"khác" vì đó là phiếu chưa xếp được, cần người ngó tới.
	"""
	return {
		N_THU_KHACH: "green",
		N_HOAN_KHACH: "orange",
		N_TRA_NCC: "blue",
		N_TRA_TRUOC: "purple",
		N_HOAN_UNG: "yellow",
		N_NOI_BO: "gray",
		N_THU_KHAC: "red",
		N_CHI_KHAC: "red",
	}.get(str(nv or "").strip(), "gray")


def la_tien_vao(nv):
	"""Nghiệp vụ này làm tiền của tiệm TĂNG lên không. THUẦN."""
	return str(nv or "").strip() in (N_THU_KHACH, N_THU_KHAC)


# ------------------------------------------------------------ chạm Frappe


def _loai_ho_so(ten_ho_so):
	"""Loại của hồ sơ thanh toán. Rỗng nếu không có hồ sơ hoặc đọc hỏng."""
	ten = str(ten_ho_so or "").strip()
	if not ten:
		return ""
	try:
		return frappe.db.get_value("Vagabond Ho So TT", ten, "loai") or ""
	except Exception:
		return ""


def dat_nghiep_vu(doc, method=None):
	"""Hook validate: ghi lại phiếu này thuộc nghiệp vụ nào.

	Mọi lỗi ở đây chỉ ghi nhật ký. Một ô hiển thị hỏng KHÔNG bao giờ được
	làm rớt việc lưu chứng từ tiền, đây là bài học hook đặt trên "*" ngày
	16/08 đã làm cả tiệm không gửi được email suốt bốn ngày.

	Khác ô bước hoá đơn mua ở một điểm: ô này tính cho MỌI phiếu kể cả
	phiếu đã ghi sổ. Được phép, vì nghiệp vụ của một phiếu không đổi sau
	khi ghi sổ, khác với chuyện trả tiền tới đâu.
	"""
	try:
		ds = []
		for d in doc.get("references") or []:
			ds.append(d.get("reference_doctype"))
		nv = nghiep_vu_cua_phieu(
			doc.get("payment_type"),
			doc.get("party_type"),
			doc.get("vgb_hoan_tien") and 1 or 0,
			_loai_ho_so(doc.get("vgb_ho_so_tt")),
			ds,
		)
		if nv:
			doc.set(TRUONG, nv)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "nghiep_vu_tien: dat nghiep vu")


def nap_lai_hang_loat(gioi_han=20000):
	"""Xếp nghiệp vụ cho những phiếu lập TRƯỚC khi có ô này.

	Cùng bài học của bản v422: ô chỉ được tính lúc lưu phiếu, mà không ai
	đi mở lại hàng nghìn phiếu cũ để bấm lưu. Không nạp lại một lượt thì
	tính năng chỉ chạy cho phiếu mới, tức là gần như không giải quyết được
	cái anh Việt nhìn thấy.

	KHÔNG PHẢI LÀ SỬA DỮ LIỆU CŨ. Ô này do máy xếp ra từ chính dữ liệu
	đang có trên phiếu, chỉ để hiển thị và để lọc, người không gõ được.
	Không đụng tới một con số tiền nào, không đụng tài khoản, không đụng
	trạng thái ghi sổ, không đụng hoá đơn điện tử.

	Đọc theo LÔ chứ không mở từng phiếu: mở phiếu là chạy lại toàn bộ hook
	của phiếu đó, mà trong đám hook ấy có cửa chặn thiếu uỷ nhiệm chi.

	Chạy lại được: chỉ nhận phiếu còn TRỐNG ô nghiệp vụ.
	"""
	kq = {"xet": 0, "ghi": 0}
	try:
		ds = frappe.get_all(
			PE,
			filters={TRUONG: ["in", ["", None]]},
			fields=["name", "payment_type", "party_type", "vgb_hoan_tien", "vgb_ho_so_tt"],
			limit_page_length=cint(gioi_han),
			order_by="modified desc",
		)
		if not ds:
			return kq
		kq["xet"] = len(ds)
		ten = [d["name"] for d in ds]

		tham_chieu = {}
		for lo in range(0, len(ten), 500):
			for r in frappe.get_all(
				"Payment Entry Reference",
				filters={"parent": ["in", ten[lo:lo + 500]]},
				fields=["parent", "reference_doctype"],
				limit_page_length=0,
			):
				tham_chieu.setdefault(r["parent"], []).append(r["reference_doctype"])

		ma_ho_so = [d["vgb_ho_so_tt"] for d in ds if (d.get("vgb_ho_so_tt") or "").strip()]
		loai_ho_so = {}
		for lo in range(0, len(ma_ho_so), 500):
			for h in frappe.get_all(
				"Vagabond Ho So TT",
				filters={"name": ["in", ma_ho_so[lo:lo + 500]]},
				fields=["name", "loai"],
				limit_page_length=0,
			):
				loai_ho_so[h["name"]] = h.get("loai") or ""

		for d in ds:
			nv = nghiep_vu_cua_phieu(
				d.get("payment_type"),
				d.get("party_type"),
				d.get("vgb_hoan_tien") and 1 or 0,
				loai_ho_so.get((d.get("vgb_ho_so_tt") or "").strip(), ""),
				tham_chieu.get(d["name"]) or [],
			)
			if not nv:
				continue
			frappe.db.set_value(PE, d["name"], TRUONG, nv, update_modified=False)
			kq["ghi"] += 1

		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "nghiep_vu_tien: nap lai hang loat")
	return kq

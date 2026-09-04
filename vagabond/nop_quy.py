# -*- coding: utf-8 -*-
"""Phiếu nộp quỹ tiền mặt: gom ca đã chốt, bảng kê mệnh giá, hai bên ký tay.

Nửa sau của luồng dòng tiền (nửa đầu là `ca_quay.py`). Cửa hàng trưởng gom
các ca đã chốt trong ngày, đếm tiền theo mệnh giá, ký tay trên màn hình,
mang tiền về; kế toán hoặc giám đốc đếm lại, ký nhận, phiếu khoá cứng và
các ca bên trong chuyển thành Đã nộp quỹ.

Vì sao kỳ vọng lấy theo số ĐẾM lúc chốt ca chứ không theo số máy
----------------------------------------------------------------
Tiền kỳ vọng của phiếu = tổng tiền mặt thu ngân ĐẾM ĐƯỢC lúc chốt các ca,
trừ tiền lẻ để lại cho ca sau. Không lấy theo doanh thu máy, vì lệch giữa
máy và số đếm đã bị bắt ở tầng CA kèm lý do rồi; tầng phiếu này chỉ hỏi
đúng một câu: số tiền đếm được lúc chốt có về tới quỹ nguyên vẹn không.
Trộn hai tầng là hết truy được lệch nằm ở khúc bán hàng hay khúc vận
chuyển tiền.

Hai đường lập phiếu, và vì sao phải có đường thứ hai
-----------------------------------------------------
Đường CA: gom các ca đã chốt. Đúng về lý thuyết nhưng ngày 30/08/2026 kiểm
trên site thật thì bảng ca rỗng, không một ca nào, tức là ba điểm bán chưa
ai mở ca chốt ca. Cả màn nộp quỹ vì thế chưa ai dùng được.

Đường NGÀY: chọn điểm bán rồi chọn một ngày hoặc một khoảng ngày, máy đọc
doanh thu TIỀN MẶT của điểm đó trong khoảng làm số kỳ vọng. Không cần ca.
Đây là đường anh Việt đặt 30/08/2026 cho ba điểm bán dùng hằng ngày.

Hai đường cùng đổ vào MỘT phiếu, một bảng kê mệnh giá, một cặp chữ ký, một
biên bản. Ô `nguon_ky_vong` ghi phiếu này lấy kỳ vọng từ đâu, để sau này
đọc lại còn biết con số kỳ vọng ấy tin được tới đâu.

Chữ ký
------
Ký tay trên màn hình, lưu thẳng ảnh nét ký (data URL) vào phiếu. Nút ký
nhận chỉ dành cho vai kế toán và giám đốc, chặn ở MÁY CHỦ chứ không chỉ ẩn
nút: ẩn nút thì gọi thẳng API vẫn lọt. Ký nhận xong phiếu khoá cứng, kể cả
bảng mệnh giá, vì biên bản đã có chữ ký hai bên mà còn sửa được số là vô
nghĩa pháp lý.
"""

import base64
import json

import frappe
from frappe.utils import cint, flt, now_datetime, nowdate

from vagabond import ca_quay, giam_doc_sua_huy

NQ = "Vagabond Nop Quy"

TT_NHAP = "Nháp"
TT_CHO_KY = "Chờ ký nhận"
TT_DA_NOP = "Đã nộp quỹ"
# Huỷ MỀM, thêm 04/09/2026. Phiếu huỷ vẫn nằm nguyên trong cơ sở dữ liệu,
# vẫn mở ra đọc được, chỉ không còn chặn phiếu khác của cùng ngày nữa. Xem
# `vagabond/giam_doc_sua_huy.py` để biết vì sao huỷ chứ không xoá.
TT_HUY = "Đã huỷ"

NHAN_TRANG_THAI = {
	TT_NHAP: "Nháp",
	TT_CHO_KY: "Chờ ký nhận",
	TT_DA_NOP: "Đã nộp quỹ",
	TT_HUY: "Đã huỷ",
}

# Phiếu ở các trạng thái này còn GIỮ CHỖ một khoảng ngày của một điểm bán.
# Phiếu đã huỷ thì không, đó là toàn bộ ý nghĩa của việc huỷ.
TT_CON_GIU_CHO = (TT_NHAP, TT_CHO_KY, TT_DA_NOP)

# Vai được ký NHẬN tiền. Bên giao là người lập phiếu, không cần vai riêng:
# ai đứng quầy cũng có thể phải mang tiền về quỹ.
VAI_KY_NHAN = {"System Manager", "Accounts Manager", "AP Kiểm soát (FIN)", "AP Giám đốc"}

# Mệnh giá tiền giấy đang lưu thông, từ lớn tới nhỏ. 200đ và 500đ bỏ ra
# ngoài: thực tế quầy bánh không cầm hai tờ đó, thêm vào chỉ làm bảng dài.
MENH_GIA = (500000, 200000, 100000, 50000, 20000, 10000, 5000, 2000, 1000)

# Lệch bàn giao dưới mức này không bắt lý do, cùng ngưỡng với tầng ca.
NGUONG_LECH = ca_quay.NGUONG_LECH

# Phạm vi của một phiếu: gói gọn trong một ngày, hay trải một khoảng ngày.
PV_NGAY = "Một ngày"
PV_KHOANG = "Khoảng ngày"

# Kỳ vọng của phiếu lấy từ đâu ra.
NG_CA = "Ca đã chốt"
NG_NGAY = "Doanh thu tiền mặt theo ngày"

# Khoảng ngày dài quá thì gần như chắc chắn là gõ nhầm năm.
TOI_DA_SO_NGAY = 62


# ============================================================ phép THUẦN


def doc_bang_ke(tho):
	"""Đọc bảng kê mệnh giá thành danh sách sạch. THUẦN.

	Nhận JSON dạng {"500000": 3, "200000": 1, ...} hoặc danh sách
	[{"menh_gia":..., "so_to":...}]. Mệnh giá lạ hay số tờ âm là gõ nhầm,
	chặn thẳng.
	"""
	if isinstance(tho, str):
		tho = json.loads(tho or "{}")
	if isinstance(tho, dict):
		tho = [{"menh_gia": k, "so_to": v} for k, v in tho.items()]
	ra = []
	for d in tho or []:
		mg = cint(d.get("menh_gia"))
		so = cint(d.get("so_to"))
		if mg not in MENH_GIA:
			raise ValueError("Mệnh giá %s không có trong bảng kê." % mg)
		if so < 0:
			raise ValueError("Số tờ của mệnh giá %s là số âm." % mg)
		if so == 0:
			continue
		ra.append({"menh_gia": mg, "so_to": so, "thanh_tien": float(mg * so)})
	ra.sort(key=lambda d: -d["menh_gia"])
	return ra


def tong_bang_ke(bang):
	"""Tổng tiền mặt thực nhận theo bảng kê. THUẦN."""
	return sum(flt(d.get("thanh_tien")) for d in bang or [])


def tinh_ky_vong(tien_dem_cac_ca, tien_le_giu_lai=0.0):
	"""Tiền kỳ vọng nộp = tổng tiền mặt đếm của các ca trừ tiền để lại. THUẦN."""
	tong = sum(flt(x) for x in tien_dem_cac_ca or [])
	giu = flt(tien_le_giu_lai)
	if giu < 0:
		raise ValueError("Tiền lẻ để lại không thể là số âm.")
	if giu > tong:
		raise ValueError("Tiền lẻ để lại (%s) nhiều hơn tổng tiền mặt của các ca (%s)." % (int(giu), int(tong)))
	return tong - giu


def can_ly_do(lech, nguong=NGUONG_LECH):
	"""Lệch bàn giao này có bắt buộc gõ lý do không. THUẦN."""
	return abs(flt(lech)) >= flt(nguong)


def duoc_ky_nhan(cac_vai):
	"""Người mang các vai này có được ký nhận tiền không. THUẦN."""
	return bool(VAI_KY_NHAN & set(cac_vai or []))


def la_chu_ky(anh):
	"""Chuỗi này có phải ảnh chữ ký data URL không. THUẦN.

	Chỉ nhận ảnh PNG hoặc JPEG nhúng thẳng. Không nhận đường dẫn hay chữ
	thường: chữ ký mà là text thì ai gõ hộ ai cũng được.
	"""
	a = (anh or "").strip()
	return a.startswith("data:image/png;base64,") or a.startswith("data:image/jpeg;base64,")


def doc_ngay(gt):
	"""Chuỗi ngày thành date. THUẦN. Không nhận rác, không đoán hộ."""
	import datetime

	if isinstance(gt, datetime.date):
		return gt
	t = str(gt or "").strip()[:10]
	if not t:
		raise ValueError("Thiếu ngày.")
	try:
		return datetime.date.fromisoformat(t)
	except ValueError:
		raise ValueError("Ngày %r không đọc được, cần dạng 2026-08-30." % t)


def dem_ngay(tu, den):
	"""Khoảng này gồm bao nhiêu ngày, tính cả hai đầu. THUẦN."""
	return (doc_ngay(den) - doc_ngay(tu)).days + 1


def chuan_khoang(pham_vi, tu_ngay, den_ngay=None):
	"""Đưa lựa chọn của người dùng về (tu, den, so_ngay) sạch. THUẦN.

	Phạm vi Một ngày thì bỏ qua ô đến ngày, lấy đúng ngày đó cho cả hai
	đầu. Người dùng đổi ý giữa chừng vẫn còn giá trị cũ trong ô kia, tin
	vào nó là lập phiếu trùm sang ngày không định nộp.
	"""
	pv = (pham_vi or PV_NGAY).strip() or PV_NGAY
	if pv not in (PV_NGAY, PV_KHOANG):
		raise ValueError("Phạm vi %r không có trong hệ." % pv)
	tu = doc_ngay(tu_ngay)
	den = tu if pv == PV_NGAY else doc_ngay(den_ngay)
	if den < tu:
		raise ValueError("Đến ngày (%s) sớm hơn từ ngày (%s)." % (den, tu))
	n = dem_ngay(tu, den)
	if n > TOI_DA_SO_NGAY:
		raise ValueError(
			"Khoảng %s ngày dài quá, tối đa %s ngày một phiếu. Kiểm lại năm "
			"của hai ô ngày." % (n, TOI_DA_SO_NGAY))
	return (str(tu), str(den), n)


def trum_nhau(a1, a2, b1, b2):
	"""Hai khoảng ngày có ngày nào chung không. THUẦN."""
	return not (doc_ngay(a2) < doc_ngay(b1) or doc_ngay(b2) < doc_ngay(a1))


def la_tien_mat(r, ten_tien_mat=None):
	"""Bill này có tính vào tiền mặt của ngày không. THUẦN.

	Bỏ bill đã huỷ và bill tạm tính, cùng một luật với `_doanh_thu_he_thong`
	của tầng ca. Hai tầng đếm khác nhau là hai bên cãi nhau về một con số.
	"""
	d = r or {}
	if cint(d.get("vgb_huy")) or cint(d.get("vgb_tam_tinh")):
		return False
	pt = (d.get("vgb_pt_thanh_toan") or "").strip()
	return pt == (ten_tien_mat or ca_quay.TIEN_MAT)


def gom_tien_mat(rows, ten_tien_mat=None):
	"""Gom bill thành bảng tiền mặt từng ngày. THUẦN.

	Trả (danh sách [{ngay, tien, so_bill}] xếp theo ngày, tổng tiền).
	"""
	theo = {}
	for r in rows or []:
		if not la_tien_mat(r, ten_tien_mat):
			continue
		ng = str((r or {}).get("posting_date") or "")[:10]
		o = theo.setdefault(ng, {"ngay": ng, "tien": 0.0, "so_bill": 0})
		o["tien"] += flt((r or {}).get("grand_total"))
		o["so_bill"] += 1
	ds = sorted(theo.values(), key=lambda d: d["ngay"])
	return (ds, sum(d["tien"] for d in ds))


def _ngay_vn(gt):
	"""2026-08-30 thành 30/08/2026. THUẦN. Không đọc được thì TRẢ NGUYÊN.

	Trả nguyên chứ không cắt mười ký tự đầu: cắt thì một chuỗi rác dài in ra
	thành một chuỗi rác NGẮN HƠN, và người đọc tưởng đó là ngày thật bị mất
	đuôi. Rác thì để nguyên hình rác cho dễ thấy.
	"""
	x = str(gt or "").strip()
	if len(x) >= 10 and x[4] == "-" and x[7] == "-":
		d = x[:10]
		return "%s/%s/%s" % (d[8:10], d[5:7], d[0:4])
	return x


def noi_dung_mac_dinh(ten_ngan, tu_ngay=None, den_ngay=None):
	"""Câu Nội dung nộp tiền gợi sẵn cho một điểm bán. THUẦN.

	Anh Việt 31/08/2026 chốt cấu trúc câu: *"Nộp quỹ tiền mặt doanh thu cửa
	hàng (tên cửa hàng) từ ngày ... đến ngày ..."*

	Vì sao phải có khoảng ngày trong câu. Nội dung này là thứ đi thẳng lên
	tờ biên bản và lên sổ quỹ. Câu cũ chỉ ghi "Nộp doanh thu Sales Online",
	nên hai tờ của hai ngày khác nhau đọc lên y hệt nhau, và người soát sổ
	phải mở từng tờ ra mới biết tờ nào của ngày nào.

	Một ngày thì viết "ngày dd/mm/yyyy", nhiều ngày thì "từ ngày ... đến
	ngày ...". Không ép câu một ngày vào khuôn "từ ... đến ..." với hai ngày
	giống nhau: đọc lên nghe như máy nói.
	"""
	t = (ten_ngan or "").strip()
	cau = "Nộp quỹ tiền mặt doanh thu cửa hàng %s" % t if t else "Nộp quỹ tiền mặt doanh thu"
	a, b = _ngay_vn(tu_ngay), _ngay_vn(den_ngay)
	if a and b and a != b:
		return "%s từ ngày %s đến ngày %s" % (cau, a, b)
	if a or b:
		return "%s ngày %s" % (cau, a or b)
	return cau


# ========================================================= chạm vào hệ


def _kiem_quyen():
	from vagabond.ban_hang import _kiem_quyen as kq

	kq()


@frappe.whitelist()
def ca_cho_nop(tu_ngay=None, den_ngay=None):
	"""Các ca đã chốt, chưa vào phiếu nào, để màn lập phiếu bày ra chọn."""
	_kiem_quyen()
	loc = {"trang_thai": ca_quay.TT_DA_CHOT, "phieu_nop": ["in", ["", None]]}
	if tu_ngay and den_ngay:
		loc["ngay"] = ["between", [tu_ngay, den_ngay]]
	ds = frappe.get_all(
		ca_quay.CA,
		filters=loc,
		fields=["name", "quay", "ngay", "mo_luc", "chot_luc", "tien_mat_dem",
			"tien_le_dau_ca", "tong_lech", "nguoi_chot"],
		order_by="chot_luc asc",
		limit_page_length=100,
	)
	return {"ds": ds}


def _bill_tien_mat(diem, tu, den):
	"""Bill của một điểm bán trong khoảng ngày. Nhập cho `gom_tien_mat`.

	Nạp `ban_hang` ngay trong hàm chứ không ở đầu tệp: `ban_hang` mở đầu
	bằng `import requests`, mà máy chạy CI của GitHub tay không. Nạp ở đầu
	tệp là đỏ cả bộ kiểm thử tầng khung, đã xảy ra ngày 20/08/2026.
	"""
	from vagabond.ban_hang import _loc_diem_ban

	loc = _loc_diem_ban(diem)
	if loc is None:
		frappe.throw("Không nhận ra điểm bán %r." % diem)
	loc = dict(loc)
	loc["posting_date"] = ["between", [tu, den]]
	loc["docstatus"] = ["<", 2]
	return frappe.get_all(
		"Sales Invoice",
		filters=loc,
		fields=["name", "posting_date", "grand_total", "vgb_pt_thanh_toan",
			"vgb_tam_tinh", "vgb_huy"],
		limit_page_length=0,
	)


def _phieu_trum(diem, tu, den, bo_qua=None):
	"""Phiếu nào của điểm này đã trùm lên khoảng ngày đang định nộp.

	Nộp hai lần cùng một ngày là tiền trong sổ nhiều gấp đôi tiền có thật.
	Chặn ở đây chứ không nhắc miệng.
	"""
	ds = frappe.get_all(
		NQ,
		filters={
			"diem_ban": diem, "tu_ngay": ["<=", den], "den_ngay": [">=", tu],
			# Phiếu ĐÃ HUỶ không giữ chỗ nữa. Trước 04/09/2026 bộ lọc này
			# không có dòng nào về trạng thái, nên một phiếu lập thử rồi bỏ
			# đó vẫn khoá cứng ngày đó của điểm đó, mà trên màn không có nút
			# nào gỡ ra. Đúng cảnh NQ-2026-01629 ngày 30/08 của Quận 1.
			"trang_thai": ["in", list(TT_CON_GIU_CHO)],
		},
		fields=["name", "tu_ngay", "den_ngay", "trang_thai"],
		limit_page_length=0,
	)
	return [d for d in ds if d.name != (bo_qua or "")]


@frappe.whitelist()
def doanh_thu_diem(diem=None, pham_vi=None, tu_ngay=None, den_ngay=None):
	"""Doanh thu TIỀN MẶT của một điểm bán trong ngày hoặc khoảng ngày.

	Màn lập phiếu gọi cửa này để bày số kỳ vọng ra trước khi thu ngân đếm
	tờ. Chỉ đọc, không ghi gì.
	"""
	_kiem_quyen()
	from vagabond import diem_ban as db

	ds_diem = [
		{"ma": d["ma"], "ten": d["ten"], "ten_ngan": d["ten_ngan"]}
		for d in db.ds(chi_bat=True)
	]
	if not diem:
		return {"diem": ds_diem, "chon": "", "theo_ngay": [], "tong_tien_mat": 0.0}

	d = db.theo_ma(str(diem).strip().upper())
	if not d:
		frappe.throw("Không nhận ra điểm bán %r." % diem)
	try:
		tu, den, n = chuan_khoang(pham_vi, tu_ngay or nowdate(), den_ngay)
	except ValueError as e:
		frappe.throw(str(e))

	theo_ngay, tong = gom_tien_mat(_bill_tien_mat(d["ma"], tu, den))
	trum = _phieu_trum(d["ma"], tu, den)
	return {
		"diem": ds_diem,
		"chon": d["ma"],
		"ten_diem": d["ten"],
		"ten_ngan": d["ten_ngan"],
		"noi_giao_nhan": d["ten"],
		"noi_dung": noi_dung_mac_dinh(d["ten_ngan"], tu, den),
		"pham_vi": (pham_vi or PV_NGAY),
		"tu_ngay": tu,
		"den_ngay": den,
		"so_ngay": n,
		"theo_ngay": theo_ngay,
		"tong_tien_mat": tong,
		"phieu_trum": [
			{"ma": x.name, "tu_ngay": str(x.tu_ngay), "den_ngay": str(x.den_ngay),
				"trang_thai": x.trang_thai}
			for x in trum
		],
	}


@frappe.whitelist()
def tim_nguoi_nhan(tu_khoa=""):
	"""Gợi ý người có quyền ký nhận tiền, tìm ở MÁY CHỦ theo tên hoặc email.

	Anh Việt 31/08/2026: *"thêm ô 'Nộp cho ai?' và cho thành ô tìm kiếm tên
	nhân viên (thường các bạn sẽ tìm Dung, Việt hoặc Sơn mà điền vào)"*.

	Chỉ trả người MANG VAI ký nhận. Cho gõ tự do rồi lưu một cái tên bất kỳ
	thì tờ biên bản ghi tên một người không có quyền nhận tiền, mà tờ đó là
	chứng từ gốc.

	Tìm ở máy chủ (QT-19): lọc bằng `or_filters` ở tầng cơ sở dữ liệu chứ
	không đọc cả bảng người dùng về rồi lọc bằng Python.
	"""
	_kiem_quyen()
	nguoi = set()
	for vai in VAI_KY_NHAN:
		try:
			for u in frappe.get_all("Has Role", filters={"role": vai},
					fields=["parent"], limit_page_length=0):
				nguoi.add(u["parent"])
		except Exception:
			continue
	if not nguoi:
		return {"ds": []}
	loc = {"name": ["in", sorted(nguoi)], "enabled": 1}
	q = str(tu_khoa or "").strip()
	hoac = None
	if q:
		hoac = [["full_name", "like", "%" + q + "%"],
			["name", "like", "%" + q + "%"]]
	ds = frappe.get_all(
		"User", filters=loc, or_filters=hoac,
		fields=["name", "full_name"], order_by="full_name asc",
		limit_page_length=20,
	)
	return {"ds": [{"ma": d["name"], "ten": d.get("full_name") or d["name"]} for d in ds]}


@frappe.whitelist()
def tao_theo_ngay(diem, bang_ke, pham_vi=None, tu_ngay=None, den_ngay=None,
		ly_do_lech="", ghi_chu="", chu_ky_ben_giao="", anh_minh_chung="",
		noi_dung="", noi_giao_nhan="", nguoi_nhan_du_kien=""):
	"""Lập phiếu nộp tiền theo ĐIỂM BÁN và NGÀY, không cần mở ca chốt ca.

	Kỳ vọng lấy từ doanh thu tiền mặt của điểm trong khoảng ngày. Khác với
	đường ca ở chỗ đó, còn lại giống hệt: cùng bảng kê mệnh giá, cùng luật
	bắt lý do khi lệch, cùng cặp chữ ký, cùng biên bản.
	"""
	_kiem_quyen()
	from vagabond import diem_ban as db

	d = db.theo_ma(str(diem or "").strip().upper())
	if not d:
		frappe.throw("Chưa chọn điểm bán, hoặc điểm bán không có trong hệ.")
	try:
		tu, den, n = chuan_khoang(pham_vi, tu_ngay or nowdate(), den_ngay)
		bang = doc_bang_ke(bang_ke)
	except ValueError as e:
		frappe.throw(str(e))

	# Ảnh cọc tiền BẮT BUỘC (anh Việt 31/08/2026). Trước đó ô này ghi
	# "không bắt buộc", mà đây là chứng từ gốc của một lần bàn giao tiền
	# mặt: không có ảnh thì lúc hai bên nhớ khác nhau về số tiền, không còn
	# gì để đối chiếu ngoài trí nhớ. Chặn ở MÁY CHỦ chứ không chỉ đổi chữ
	# trên màn, vì đổi chữ thì vẫn lập được phiếu trắng ảnh.
	if not (anh_minh_chung or "").strip():
		frappe.throw(
			"Phải chụp ảnh cọc tiền trước khi lập biên nhận. Đây là chứng từ "
			"gốc của một lần bàn giao tiền mặt, không có ảnh thì sau này hai "
			"bên nhớ khác nhau là hết đường đối chiếu.",
			title="Thiếu ảnh minh chứng giao nhận tiền",
		)

	trum = _phieu_trum(d["ma"], tu, den)
	if trum:
		frappe.throw(
			"Điểm %s đã có phiếu %s trùm lên khoảng %s tới %s. Nộp hai lần "
			"cùng một ngày là tiền trong sổ nhiều gấp đôi tiền có thật. Mở "
			"phiếu cũ ra xem trước." % (
				d["ten_ngan"], trum[0].name, trum[0].tu_ngay, trum[0].den_ngay))

	_, ky_vong = gom_tien_mat(_bill_tien_mat(d["ma"], tu, den))
	thuc_nhan = tong_bang_ke(bang)
	lech = thuc_nhan - ky_vong
	if can_ly_do(lech) and not (ly_do_lech or "").strip():
		return {
			"can_ly_do": 1,
			"ky_vong": ky_vong,
			"thuc_nhan": thuc_nhan,
			"lech": lech,
			"nhac": "Thực nộp lệch %s đồng so với doanh thu tiền mặt %s tới %s. "
				"Gõ lý do rồi lập lại." % (int(lech), tu, den),
		}

	# Người dự kiến nhận tiền. Không bắt buộc, nhưng có thì tờ biên bản in
	# ra đã mang tên người nhận thay vì một hàng dấu chấm, và bên nhận biết
	# là mình đang được chờ.
	nhan_du_kien = str(nguoi_nhan_du_kien or "").strip()
	ten_nhan_du_kien = ""
	if nhan_du_kien:
		if not frappe.db.exists("User", nhan_du_kien):
			frappe.throw("Không có người dùng %s trong hệ." % nhan_du_kien)
		ten_nhan_du_kien = (
			frappe.db.get_value("User", nhan_du_kien, "full_name") or nhan_du_kien)

	co_ky = la_chu_ky(chu_ky_ben_giao)
	doc = frappe.get_doc({
		"doctype": NQ,
		"ngay": nowdate(),
		"trang_thai": TT_CHO_KY if co_ky else TT_NHAP,
		"nguon_ky_vong": NG_NGAY,
		"diem_ban": d["ma"],
		"ten_diem_ban": d["ten"],
		"pham_vi": PV_NGAY if n == 1 else PV_KHOANG,
		"tu_ngay": tu,
		"den_ngay": den,
		"so_ngay": n,
		"noi_dung": (noi_dung or "").strip() or noi_dung_mac_dinh(d["ten_ngan"], tu, den),
		"noi_giao_nhan": (noi_giao_nhan or "").strip() or d["ten"],
		"nguoi_nhan_du_kien": nhan_du_kien,
		"ten_nguoi_nhan_du_kien": ten_nhan_du_kien,
		"anh_minh_chung": (anh_minh_chung or "").strip(),
		"nguoi_giao": frappe.session.user,
		"ten_nguoi_giao": frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user,
		"giao_luc": now_datetime() if co_ky else None,
		"chu_ky_ben_giao": chu_ky_ben_giao if co_ky else "",
		"tien_le_giu_lai": 0,
		"tien_ky_vong": ky_vong,
		"tong_thuc_nhan": thuc_nhan,
		"lech": lech,
		"ly_do_lech": (ly_do_lech or "").strip(),
		"ghi_chu": (ghi_chu or "").strip(),
	})
	for x in bang:
		doc.append("menh_gia", x)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"ma": doc.name, "trang_thai": doc.trang_thai, "ky_vong": ky_vong,
		"thuc_nhan": thuc_nhan, "lech": lech}


@frappe.whitelist()
def tao(ds_ca, bang_ke, tien_le_giu_lai=0, ly_do_lech="", ghi_chu="", chu_ky_ben_giao=""):
	"""Lập phiếu nộp quỹ từ các ca đã chốt.

	`ds_ca` là JSON danh sách mã ca. `bang_ke` là JSON bảng mệnh giá. Có
	chữ ký bên giao thì phiếu vào thẳng Chờ ký nhận; chưa ký thì nằm Nháp.

	Mỗi ca chỉ vào được một phiếu: kiểm ở đây bằng ô `phieu_nop` trên ca,
	ghi ngay trong cùng giao dịch để hai người lập phiếu cùng lúc không
	gom trùng ca của nhau.
	"""
	_kiem_quyen()
	if isinstance(ds_ca, str):
		ds_ca = json.loads(ds_ca or "[]")
	ds_ca = [str(x).strip() for x in (ds_ca or []) if str(x).strip()]
	if not ds_ca:
		frappe.throw("Chưa chọn ca nào để nộp.")

	dong_ca = []
	for ma in ds_ca:
		d = frappe.db.get_value(
			ca_quay.CA, ma,
			["name", "quay", "ngay", "trang_thai", "tien_mat_dem", "phieu_nop"],
			as_dict=True,
		)
		if not d:
			frappe.throw("Không thấy ca %s." % ma)
		if d.trang_thai != ca_quay.TT_DA_CHOT:
			frappe.throw("Ca %s đang ở trạng thái %s, chỉ nộp được ca Đã chốt." % (ma, d.trang_thai))
		if (d.phieu_nop or "").strip():
			frappe.throw("Ca %s đã nằm trong phiếu %s rồi." % (ma, d.phieu_nop))
		dong_ca.append(d)

	try:
		bang = doc_bang_ke(bang_ke)
		ky_vong = tinh_ky_vong([d.tien_mat_dem for d in dong_ca], tien_le_giu_lai)
	except ValueError as e:
		frappe.throw(str(e))

	thuc_nhan = tong_bang_ke(bang)
	lech = thuc_nhan - ky_vong
	if can_ly_do(lech) and not (ly_do_lech or "").strip():
		return {
			"can_ly_do": 1,
			"ky_vong": ky_vong,
			"thuc_nhan": thuc_nhan,
			"lech": lech,
			"nhac": "Thực nhận lệch %s đồng so với kỳ vọng. Gõ lý do rồi lập lại." % int(lech),
		}

	co_ky = la_chu_ky(chu_ky_ben_giao)
	# Khoảng ngày của phiếu ca lấy theo ngày của chính các ca, để hai đường
	# lập phiếu cùng lọc được bằng một bộ lọc.
	ngay_ca = sorted(str(d.ngay)[:10] for d in dong_ca if d.ngay)
	tu_ca = ngay_ca[0] if ngay_ca else nowdate()
	den_ca = ngay_ca[-1] if ngay_ca else nowdate()
	# ĐIỂM BÁN CỦA PHIẾU. Trước 01/09/2026 đường CA không ghi ô này, nên
	# phiếu lập theo ca KHÔNG BAO GIỜ khớp bộ lọc chống nộp trùng, và cùng
	# một ngày của cùng một điểm có thể nộp hai lần: một lần theo ca, một
	# lần theo ngày ở màn Biên nhận tiền. Sổ quỹ ghi gấp đôi tiền có thật.
	#
	# Chuyện này chưa nổ vì tới hôm nay bảng ca còn rỗng. Nhưng anh Việt
	# vừa cho mở ca ở Sales Online, nên nó sẽ nổ ngay tuần đầu.
	#
	# Ô `quay` của ca chứa MÃ ĐIỂM BÁN (xem ca_quay.py), nên dùng thẳng.
	diem_ca = sorted({str(d.quay or "").strip().upper() for d in dong_ca if d.quay})
	if len(diem_ca) > 1:
		frappe.throw(
			"Các ca đang chọn thuộc %d điểm bán khác nhau (%s). Mỗi phiếu nộp "
			"quỹ chỉ nộp cho một điểm bán, lập riêng từng điểm."
			% (len(diem_ca), ", ".join(diem_ca))
		)
	diem_phieu = diem_ca[0] if diem_ca else ""
	if diem_phieu:
		trum = _phieu_trum(diem_phieu, tu_ca, den_ca)
		if trum:
			t = trum[0]
			frappe.throw(
				"Điểm bán %s đã có phiếu nộp quỹ %s trùm lên khoảng %s tới %s "
				"(%s). Nộp hai lần cùng một ngày là tiền trong sổ nhiều gấp "
				"đôi tiền có thật. Mở phiếu đó ra xem trước."
				% (diem_phieu, t["name"], t["tu_ngay"], t["den_ngay"], t["trang_thai"])
			)
	doc = frappe.get_doc({
		"doctype": NQ,
		"ngay": nowdate(),
		"diem_ban": diem_phieu,
		"trang_thai": TT_CHO_KY if co_ky else TT_NHAP,
		"nguon_ky_vong": NG_CA,
		"pham_vi": PV_NGAY if tu_ca == den_ca else PV_KHOANG,
		"tu_ngay": tu_ca,
		"den_ngay": den_ca,
		"so_ngay": dem_ngay(tu_ca, den_ca),
		"nguoi_giao": frappe.session.user,
		"ten_nguoi_giao": frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user,
		"giao_luc": now_datetime() if co_ky else None,
		"chu_ky_ben_giao": chu_ky_ben_giao if co_ky else "",
		"tien_le_giu_lai": flt(tien_le_giu_lai),
		"tien_ky_vong": ky_vong,
		"tong_thuc_nhan": thuc_nhan,
		"lech": lech,
		"ly_do_lech": (ly_do_lech or "").strip(),
		"ghi_chu": (ghi_chu or "").strip(),
	})
	for d in dong_ca:
		doc.append("ca", {
			"ca": d.name, "quay": d.quay, "ngay": d.ngay,
			"tien_mat_dem": flt(d.tien_mat_dem),
		})
	for d in bang:
		doc.append("menh_gia", d)
	doc.insert(ignore_permissions=True)
	# Đóng dấu ca thuộc phiếu NGAY, trong cùng giao dịch với insert: hai
	# người cùng lập phiếu thì người sau vấp phải ô phieu_nop đã có.
	for d in dong_ca:
		frappe.db.set_value(ca_quay.CA, d.name, "phieu_nop", doc.name, update_modified=False)
	frappe.db.commit()
	return {"ma": doc.name, "trang_thai": doc.trang_thai, "ky_vong": ky_vong,
		"thuc_nhan": thuc_nhan, "lech": lech}


@frappe.whitelist()
def ky_giao(ma, chu_ky):
	"""Bên giao ký bổ sung cho phiếu còn Nháp."""
	_kiem_quyen()
	doc = frappe.get_doc(NQ, ma)
	if doc.trang_thai != TT_NHAP:
		frappe.throw("Phiếu đang ở trạng thái %s, không ký giao lại được." % doc.trang_thai)
	if not la_chu_ky(chu_ky):
		frappe.throw("Chữ ký không hợp lệ. Vui lòng ký tay lại trên màn hình.")
	doc.chu_ky_ben_giao = chu_ky
	doc.giao_luc = now_datetime()
	doc.trang_thai = TT_CHO_KY
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ma": doc.name, "trang_thai": doc.trang_thai}


@frappe.whitelist()
def ky_nhan(ma, chu_ky):
	"""Kế toán hoặc giám đốc ký nhận tiền. Phiếu khoá cứng từ đây.

	Chặn vai ở máy chủ: ẩn nút trên màn chỉ là lịch sự, đây mới là cửa.
	"""
	if not duoc_ky_nhan(frappe.get_roles()):
		frappe.throw("Chỉ kế toán hoặc giám đốc được ký nhận tiền.")
	doc = frappe.get_doc(NQ, ma)
	if doc.trang_thai != TT_CHO_KY:
		frappe.throw("Phiếu đang ở trạng thái %s, chưa hoặc không còn chờ ký nhận." % doc.trang_thai)
	if not la_chu_ky(chu_ky):
		frappe.throw("Chữ ký không hợp lệ. Vui lòng ký tay lại trên màn hình.")
	if frappe.session.user == doc.nguoi_giao:
		frappe.throw("Bên giao và bên nhận không được là cùng một người.")
	doc.chu_ky_ben_nhan = chu_ky
	doc.nguoi_nhan = frappe.session.user
	doc.ten_nguoi_nhan = frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user
	doc.nhan_luc = now_datetime()
	doc.trang_thai = TT_DA_NOP
	doc.save(ignore_permissions=True)
	for d in doc.ca:
		frappe.db.set_value(ca_quay.CA, d.ca, "trang_thai", ca_quay.TT_DA_NOP, update_modified=False)
	frappe.db.commit()
	return {"ma": doc.name, "trang_thai": doc.trang_thai, "nhan_luc": str(doc.nhan_luc)}


# ------------------------------------------- cửa SỬA và HUỶ của giám đốc
#
# Anh Việt 04/09/2026. Xem `vagabond/giam_doc_sua_huy.py` để biết vì sao
# huỷ chứ không xoá, và vì sao lý do là bắt buộc.


def _nha_ca(doc, ve_da_chot):
	"""Trả các ca mà phiếu đang giữ về cho người khác lập phiếu lại.

	Huỷ hay sửa mà quên nhả ca là khoá vĩnh viễn các ca đó: ô `phieu_nop`
	còn trỏ vào một phiếu không còn hiệu lực, và `tao()` sẽ chặn mãi mãi
	với câu "ca này đã nằm trong phiếu ... rồi".
	"""
	n = 0
	for d in doc.ca or []:
		if not d.ca:
			continue
		frappe.db.set_value(ca_quay.CA, d.ca, "phieu_nop", "", update_modified=False)
		if ve_da_chot:
			frappe.db.set_value(
				ca_quay.CA, d.ca, "trang_thai", ca_quay.TT_DA_CHOT,
				update_modified=False)
		n += 1
	return n


@frappe.whitelist()
def huy(ma, ly_do):
	"""Giám đốc huỷ MỀM một phiếu nộp quỹ. Không xoá, chỉ đổi trạng thái.

	Huỷ được ở mọi trạng thái, kể cả phiếu đã ký nhận: có thật chuyện hai
	bên ký xong mới phát hiện đếm nhầm hay lập trùng, và lúc đó thứ duy
	nhất còn đúng là ghi rõ nó sai chứ không phải giả vờ nó không tồn tại.

	Huỷ xong phiếu KHÔNG còn giữ chỗ khoảng ngày của điểm bán nữa, nên lập
	lại phiếu đúng cho chính ngày đó được ngay.
	"""
	giam_doc_sua_huy.chan("huỷ phiếu nộp quỹ")
	ly_do = giam_doc_sua_huy.doc_ly_do(ly_do)
	doc = frappe.get_doc(NQ, ma)
	giam_doc_sua_huy.da_huy(doc, TT_HUY)

	tt_cu = doc.trang_thai
	so_ca = _nha_ca(doc, ve_da_chot=(tt_cu == TT_DA_NOP))
	doc.trang_thai = TT_HUY
	giam_doc_sua_huy.dong_dau_huy(doc, ly_do)
	doc.save(ignore_permissions=True)
	giam_doc_sua_huy.ghi_vet(NQ, doc.name, giam_doc_sua_huy.cau_vet(
		"Huỷ phiếu nộp quỹ (đang ở %s, %s đ, nhả %d ca)" % (
			tt_cu, int(flt(doc.tong_thuc_nhan)), so_ca),
		frappe.session.user, ly_do))
	frappe.db.commit()
	return {"ma": doc.name, "trang_thai": doc.trang_thai, "tt_cu": tt_cu,
		"so_ca_nha": so_ca}


@frappe.whitelist()
def sua(ma, ly_do, bang_ke=None, tu_ngay=None, den_ngay=None, pham_vi=None,
		noi_dung=None, noi_giao_nhan=None, ghi_chu=None, ly_do_lech=None,
		anh_minh_chung=None):
	"""Giám đốc sửa một phiếu nộp quỹ. Sửa gì cũng phải ghi lý do.

	Sửa là ĐẬP CHỮ KÝ, không phải chỉnh lén
	---------------------------------------
	Tờ biên bản có hai chữ ký là để hai bên xác nhận CÙNG MỘT con số. Sửa
	con số mà giữ nguyên chữ ký cũ thì chữ ký đó đang xác nhận một thứ
	không còn tồn tại, tức là tờ biên bản mất sạch giá trị mà nhìn vào vẫn
	thấy đầy đủ. Nên:

	  - phiếu Đã nộp quỹ mà bị sửa thì rơi về Chờ ký nhận, xoá chữ ký bên
	    nhận, và các ca trả về Đã chốt;
	  - phiếu Chờ ký nhận mà bị sửa vào SỐ TIỀN hoặc KHOẢNG NGÀY thì rơi về
	    Nháp, xoá luôn chữ ký bên giao;
	  - sửa mấy ô chữ (nội dung, nơi giao nhận, ghi chú) thì giữ nguyên
	    trạng thái, vì không ai ký để xác nhận một dòng ghi chú.

	Phiếu đã huỷ thì không sửa. Muốn dùng lại thì lập phiếu mới.
	"""
	giam_doc_sua_huy.chan("sửa phiếu nộp quỹ")
	ly_do = giam_doc_sua_huy.doc_ly_do(ly_do)
	doc = frappe.get_doc(NQ, ma)
	if doc.trang_thai == TT_HUY:
		frappe.throw(
			"Phiếu %s đã huỷ, không sửa được nữa. Lập phiếu mới cho khoảng "
			"ngày đó." % doc.name)

	tt_cu = doc.trang_thai
	tien_cu = flt(doc.tong_thuc_nhan)
	ngay_cu = (str(doc.tu_ngay or ""), str(doc.den_ngay or ""))
	doi = []

	# --- khoảng ngày. Chỉ phiếu lấy kỳ vọng THEO NGÀY mới đổi được: phiếu
	# theo ca lấy ngày từ chính các ca, đổi tay là số kỳ vọng hết khớp với
	# bảng ca ngay bên dưới nó.
	if tu_ngay or den_ngay or pham_vi:
		if (doc.get("nguon_ky_vong") or "") != NG_NGAY:
			frappe.throw(
				"Phiếu này lấy kỳ vọng từ các ca đã chốt, khoảng ngày do "
				"chính các ca quyết định. Muốn đổi ngày thì huỷ phiếu rồi "
				"gom lại ca khác.")
		try:
			tu, den, n = chuan_khoang(
				pham_vi or doc.get("pham_vi"),
				tu_ngay or str(doc.tu_ngay), den_ngay or str(doc.den_ngay))
		except ValueError as e:
			frappe.throw(str(e))
		trum = _phieu_trum(doc.get("diem_ban"), tu, den, bo_qua=doc.name)
		if trum:
			frappe.throw(
				"Đổi sang %s tới %s thì đụng phiếu %s (%s) của cùng điểm bán. "
				"Nộp hai lần cùng một ngày là tiền trong sổ nhiều gấp đôi tiền "
				"có thật." % (tu, den, trum[0]["name"], trum[0]["trang_thai"]))
		if (str(doc.tu_ngay), str(doc.den_ngay)) != (tu, den):
			doi.append("khoảng ngày %s..%s thành %s..%s" % (
				doc.tu_ngay, doc.den_ngay, tu, den))
		doc.tu_ngay, doc.den_ngay, doc.so_ngay = tu, den, n
		doc.pham_vi = PV_NGAY if n == 1 else PV_KHOANG
		_, doc.tien_ky_vong = gom_tien_mat(
			_bill_tien_mat(doc.get("diem_ban"), tu, den))

	# --- bảng kê mệnh giá
	if bang_ke is not None:
		try:
			bang = doc_bang_ke(bang_ke)
		except ValueError as e:
			frappe.throw(str(e))
		if not bang:
			frappe.throw("Bảng kê mệnh giá trống. Phiếu nộp tiền phải có tờ nào đó.")
		doc.set("menh_gia", [])
		for x in bang:
			doc.append("menh_gia", x)
		doc.tong_thuc_nhan = tong_bang_ke(bang)

	doc.lech = flt(doc.tong_thuc_nhan) - flt(doc.tien_ky_vong)
	if flt(doc.tong_thuc_nhan) != tien_cu:
		doi.append("thực nhận %d đ thành %d đ" % (int(tien_cu), int(flt(doc.tong_thuc_nhan))))

	# --- các ô chữ. Truyền None nghĩa là không đụng tới, truyền chuỗi rỗng
	# nghĩa là xoá trắng ô đó.
	for o, gt in (("noi_dung", noi_dung), ("noi_giao_nhan", noi_giao_nhan),
			("ghi_chu", ghi_chu), ("ly_do_lech", ly_do_lech),
			("anh_minh_chung", anh_minh_chung)):
		if gt is None:
			continue
		gt = str(gt).strip()
		if (doc.get(o) or "") != gt:
			doi.append("ô %s" % o)
		doc.set(o, gt)

	if can_ly_do(doc.lech) and not (doc.ly_do_lech or "").strip():
		frappe.throw(
			"Sửa xong phiếu lệch %d đồng so với kỳ vọng. Phải ghi lý do lệch."
			% int(flt(doc.lech)))

	# --- chữ ký nào còn giá trị sau lần sửa này
	doi_tien = (flt(doc.tong_thuc_nhan) != tien_cu
		or (str(doc.tu_ngay or ""), str(doc.den_ngay or "")) != ngay_cu)
	nha_ca = 0
	if tt_cu == TT_DA_NOP:
		nha_ca = _nha_ca(doc, ve_da_chot=True)
		doc.chu_ky_ben_nhan = ""
		doc.nguoi_nhan = None
		doc.ten_nguoi_nhan = ""
		doc.nhan_luc = None
		doc.trang_thai = TT_CHO_KY
	if doi_tien and doc.trang_thai == TT_CHO_KY:
		doc.chu_ky_ben_giao = ""
		doc.giao_luc = None
		doc.trang_thai = TT_NHAP

	doc.save(ignore_permissions=True)
	giam_doc_sua_huy.ghi_vet(NQ, doc.name, giam_doc_sua_huy.cau_vet(
		"Sửa phiếu nộp quỹ (%s): %s" % (
			tt_cu, "; ".join(doi) or "không đổi ô nào"),
		frappe.session.user, ly_do))
	frappe.db.commit()
	return {"ma": doc.name, "trang_thai": doc.trang_thai, "tt_cu": tt_cu,
		"doi": doi, "so_ca_nha": nha_ca,
		"tong_thuc_nhan": flt(doc.tong_thuc_nhan),
		"tien_ky_vong": flt(doc.tien_ky_vong), "lech": flt(doc.lech)}


def _dong_danh_sach(d):
	return {
		"name": d.name, "ngay": str(d.ngay), "trang_thai": d.trang_thai,
		"nguoi_giao": d.ten_nguoi_giao or d.nguoi_giao,
		"nguoi_nhan": d.ten_nguoi_nhan or d.nguoi_nhan or "",
		"tien_ky_vong": flt(d.tien_ky_vong), "tong_thuc_nhan": flt(d.tong_thuc_nhan),
		"lech": flt(d.lech), "so_ca": cint(d.get("so_ca")),
		"diem_ban": d.get("diem_ban") or "",
		"ten_diem_ban": d.get("ten_diem_ban") or "",
		"pham_vi": d.get("pham_vi") or "",
		"tu_ngay": str(d.get("tu_ngay") or ""),
		"den_ngay": str(d.get("den_ngay") or ""),
		"so_ngay": cint(d.get("so_ngay")),
		"nguon_ky_vong": d.get("nguon_ky_vong") or "",
	}


def _loc_danh_sach(trang_thai=None, tu_ngay=None, den_ngay=None, tim="",
		diem=None, chi_toi=0):
	loc = {}
	if trang_thai:
		loc["trang_thai"] = trang_thai
	if tu_ngay and den_ngay:
		loc["ngay"] = ["between", [tu_ngay, den_ngay]]
	elif tu_ngay:
		loc["ngay"] = [">=", tu_ngay]
	if diem:
		loc["diem_ban"] = str(diem).strip().upper()
	# Nhân viên điểm bán chỉ cần thấy phiếu mình lập. Đây là bộ lọc cho gọn
	# màn, KHÔNG phải hàng rào bảo mật: hàng rào nằm ở `_kiem_quyen`.
	if cint(chi_toi):
		loc["nguoi_giao"] = frappe.session.user
	return loc


@frappe.whitelist()
def danh_sach(trang_thai=None, tu_ngay=None, den_ngay=None, tim="", so_dong=200,
		diem=None, chi_toi=0):
	"""Danh sách phiếu nộp quỹ, kèm số đếm cho chip trạng thái."""
	_kiem_quyen()
	ds = frappe.get_all(
		NQ,
		filters=_loc_danh_sach(trang_thai, tu_ngay, den_ngay, diem=diem, chi_toi=chi_toi),
		fields=["name", "ngay", "trang_thai", "nguoi_giao", "ten_nguoi_giao",
			"nguoi_nhan", "ten_nguoi_nhan", "tien_ky_vong", "tong_thuc_nhan", "lech",
			"diem_ban", "ten_diem_ban", "pham_vi", "tu_ngay", "den_ngay", "so_ngay",
			"nguon_ky_vong"],
		order_by="creation desc",
		limit=cint(so_dong) or 200,
	)
	def _khop(d):
		return q in (
			(d.get("name") or "") + " " + (d.get("ten_nguoi_giao") or "")
			+ " " + (d.get("nguoi_giao") or "")
		).lower()

	q = (tim or "").strip().lower()
	if q:
		ds = [d for d in ds if _khop(d)]
	# Số ca của từng phiếu: một câu hỏi cho cả trang, không hỏi từng phiếu.
	so_ca = {}
	if ds:
		for r in frappe.get_all(
			"Vagabond Nop Quy Ca",
			filters={"parent": ["in", [d.name for d in ds]]},
			fields=["parent"],
			limit_page_length=0,
		):
			so_ca[r.parent] = so_ca.get(r.parent, 0) + 1
	for d in ds:
		d["so_ca"] = so_ca.get(d.name, 0)
	# Đếm chip trên TOÀN BỘ tập khớp ngày, không phải trang đang xem.
	#
	# NHƯNG phải khớp cả ô tìm. Trước 03/09/2026 vòng đếm này bỏ qua `tim`,
	# nên gõ một cái tên ra hai dòng mà hàng chip vẫn báo "Tất cả 40 · Nháp
	# 11". Đúng lỗi này đã được vá ở `hoan_tien.ds` và `de_nghi_chi.ds_man`
	# từ trước, riêng đây thì sót.
	dem = {"": 0}
	for r in frappe.get_all(
		NQ, filters=_loc_danh_sach(None, tu_ngay, den_ngay, diem=diem, chi_toi=chi_toi),
		fields=["name", "trang_thai", "ten_nguoi_giao", "nguoi_giao"], limit_page_length=0,
	):
		if q and not _khop(r):
			continue
		dem[r.trang_thai] = dem.get(r.trang_thai, 0) + 1
		dem[""] += 1
	return {"ds": [_dong_danh_sach(d) for d in ds], "dem": dem}


@frappe.whitelist()
def chi_tiet(ma):
	"""Một phiếu, đủ bảng mệnh giá, các ca, và hai chữ ký."""
	_kiem_quyen()
	doc = frappe.get_doc(NQ, ma)
	return {
		"ma": doc.name,
		"ngay": str(doc.ngay),
		"trang_thai": doc.trang_thai,
		"nguon_ky_vong": doc.get("nguon_ky_vong") or "",
		"diem_ban": doc.get("diem_ban") or "",
		"ten_diem_ban": doc.get("ten_diem_ban") or "",
		"pham_vi": doc.get("pham_vi") or "",
		"tu_ngay": str(doc.get("tu_ngay") or ""),
		"den_ngay": str(doc.get("den_ngay") or ""),
		"so_ngay": cint(doc.get("so_ngay")),
		"noi_dung": doc.get("noi_dung") or "",
		"noi_giao_nhan": doc.get("noi_giao_nhan") or "",
		"nguoi_nhan_du_kien": doc.get("nguoi_nhan_du_kien") or "",
		"ten_nguoi_nhan_du_kien": doc.get("ten_nguoi_nhan_du_kien") or "",
		"anh_minh_chung": doc.get("anh_minh_chung") or "",
		"nguoi_giao": doc.nguoi_giao,
		"ten_nguoi_giao": doc.ten_nguoi_giao or doc.nguoi_giao,
		"giao_luc": str(doc.giao_luc or ""),
		"nguoi_nhan": doc.nguoi_nhan or "",
		"ten_nguoi_nhan": doc.ten_nguoi_nhan or "",
		"nhan_luc": str(doc.nhan_luc or ""),
		"tien_le_giu_lai": flt(doc.tien_le_giu_lai),
		"tien_ky_vong": flt(doc.tien_ky_vong),
		"tong_thuc_nhan": flt(doc.tong_thuc_nhan),
		"lech": flt(doc.lech),
		"ly_do_lech": doc.ly_do_lech or "",
		"ghi_chu": doc.ghi_chu or "",
		"co_ky_giao": 1 if (doc.chu_ky_ben_giao or "").strip() else 0,
		"co_ky_nhan": 1 if (doc.chu_ky_ben_nhan or "").strip() else 0,
		"chu_ky_ben_giao": doc.chu_ky_ben_giao or "",
		"chu_ky_ben_nhan": doc.chu_ky_ben_nhan or "",
		"duoc_ky_nhan": 1 if duoc_ky_nhan(frappe.get_roles()) else 0,
		# Nút Sửa và Huỷ chỉ vẽ ra khi máy chủ bảo người này đủ vai. Máy chủ
		# còn chặn lại lần nữa trong `sua` và `huy` - ẩn nút chỉ là lịch sự.
		"duoc_sua_huy": 1 if giam_doc_sua_huy.duoc_sua_huy(frappe.get_roles()) else 0,
		"huy_boi": doc.get("huy_boi") or "",
		"ten_nguoi_huy": doc.get("ten_nguoi_huy") or "",
		"huy_luc": str(doc.get("huy_luc") or ""),
		"ly_do_huy": doc.get("ly_do_huy") or "",
		"ca": [
			{"ca": d.ca, "quay": d.quay, "ngay": str(d.ngay), "tien_mat_dem": flt(d.tien_mat_dem)}
			for d in doc.ca
		],
		"menh_gia": [
			{"menh_gia": cint(d.menh_gia), "so_to": cint(d.so_to), "thanh_tien": flt(d.thanh_tien)}
			for d in doc.menh_gia
		],
	}


@frappe.whitelist()
def xuat_excel(trang_thai="", tu_ngay=None, den_ngay=None, tim="", so_dong=500,
		diem=None, chi_toi=0):
	"""Danh sách phiếu nộp quỹ ra Excel, đúng bộ lọc đang xem trên màn."""
	_kiem_quyen()
	kq = danh_sach(trang_thai=trang_thai, tu_ngay=tu_ngay, den_ngay=den_ngay,
		tim=tim, so_dong=so_dong, diem=diem, chi_toi=chi_toi)
	rows = kq.get("ds") or []
	bang = [
		["PHIẾU NỘP QUỸ TIỀN MẶT"],
		["Xuất lúc", str(now_datetime())[:19],
			"Bộ lọc", NHAN_TRANG_THAI.get(trang_thai, "Tất cả") if trang_thai else "Tất cả",
			"Từ ngày", tu_ngay or "(không)", "Đến ngày", den_ngay or "(không)"],
		["Số phiếu", len(rows),
			"Tổng thực nhận", sum(flt(r.get("tong_thuc_nhan")) for r in rows),
			"Tổng lệch", sum(flt(r.get("lech")) for r in rows)],
		[],
		["Mã phiếu", "Ngày lập", "Điểm bán", "Doanh thu từ ngày", "Đến ngày",
			"Số ngày", "Trạng thái", "Nguồn kỳ vọng", "Số ca", "Bên giao",
			"Bên nhận", "Tiền kỳ vọng", "Thực nhận", "Lệch"],
	]
	for r in rows:
		bang.append([
			r.get("name") or "", r.get("ngay") or "",
			r.get("ten_diem_ban") or r.get("diem_ban") or "",
			r.get("tu_ngay") or "", r.get("den_ngay") or "", cint(r.get("so_ngay")),
			r.get("trang_thai") or "", r.get("nguon_ky_vong") or "",
			cint(r.get("so_ca")),
			r.get("nguoi_giao") or "", r.get("nguoi_nhan") or "",
			flt(r.get("tien_ky_vong")), flt(r.get("tong_thuc_nhan")), flt(r.get("lech")),
		])
	from frappe.utils.xlsxutils import make_xlsx

	tep = make_xlsx(bang, "Nop quy tien mat")
	noi_dung = tep.getvalue() if hasattr(tep, "getvalue") else tep
	return {
		"ten_file": "nop-quy-tien-mat-%s.xlsx" % nowdate(),
		"b64": base64.b64encode(noi_dung).decode(),
		"so_dong": len(rows),
	}


# ================================================== BIÊN BẢN PDF


def _tien(n):
	"""1234567 thành 1.234.567 theo lối kế toán Việt Nam. THUẦN."""
	return "{:,.0f}".format(flt(n)).replace(",", ".")


def chu_so_tien(so):
	"""Đọc số tiền bằng chữ cho biên bản. THUẦN.

	`cong_no.py` có một bản y hệt, nhưng KHÔNG import từ đó: cong_no kéo
	ban_hang, ban_hang mở đầu bằng `import requests`, mà máy chạy CI của
	GitHub không cài gói ngoài nào - đầu workflow đã dặn bộ kiểm thử phải
	chạy tay không. Chính dây chuyền import đó đã làm đỏ 3 ca trên PR #2
	trong khi máy local xanh. Một hàm đọc số thì không có quyền kéo theo
	thư viện mạng.
	"""
	so = int(round(flt(so)))
	if so == 0:
		return "Không đồng"
	don_vi = ["", "nghìn", "triệu", "tỷ", "nghìn tỷ"]
	so_chu = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]

	def doc_ba(n, day_du):
		tram, chuc, dv = n // 100, (n // 10) % 10, n % 10
		ra = []
		if tram or day_du:
			ra.append(so_chu[tram] + " trăm")
		if chuc == 0 and dv and (tram or day_du):
			ra.append("lẻ")
		elif chuc == 1:
			ra.append("mười")
		elif chuc > 1:
			ra.append(so_chu[chuc] + " mươi")
		if dv:
			if chuc > 1 and dv == 1:
				ra.append("mốt")
			elif chuc >= 1 and dv == 5:
				ra.append("lăm")
			else:
				ra.append(so_chu[dv])
		return " ".join(x for x in ra if x)

	cum = []
	n = so
	while n > 0:
		cum.append(n % 1000)
		n //= 1000
	phan = []
	for i in range(len(cum) - 1, -1, -1):
		if cum[i] == 0:
			continue
		phan.append(doc_ba(cum[i], i != len(cum) - 1) + (" " + don_vi[i] if don_vi[i] else ""))
	ra = " ".join(phan).strip()
	return (ra[0].upper() + ra[1:] + " đồng") if ra else "Không đồng"


def _html_bien_ban(d):
	"""Dựng HTML biên bản bàn giao tiền mặt theo thể thức hành chính. THUẦN
	theo nghĩa chỉ đọc dict `d`, không hỏi thêm hệ.

	Thể thức: quốc hiệu tiêu ngữ giữa trang, tên biên bản in hoa, hai bên
	giao nhận, bảng kê mệnh giá, tổng bằng số và bằng chữ, hai chữ ký. Chữ
	"BÊN GIAO" trái "BÊN NHẬN" phải theo đúng lối biên bản hai bên.
	"""
	def ky(anh, ten, luc):
		o = ""
		if anh:
			o += "<img src='%s' style='height:64px;max-width:200px;object-fit:contain'><br>" % anh
		else:
			o += "<div style='height:64px'></div>"
		o += "<b>%s</b>" % (ten or "")
		if luc:
			o += "<br><span style='font-size:11px;color:#333'>Ký lúc %s</span>" % str(luc)[:16]
		return o

	dong_mg = ""
	for m in d.get("menh_gia") or []:
		dong_mg += (
			"<tr><td style='text-align:right'>%s</td>"
			"<td style='text-align:center'>%s</td>"
			"<td style='text-align:right'>%s</td></tr>"
			% (_tien(m["menh_gia"]), cint(m["so_to"]), _tien(m["thanh_tien"]))
		)
	dong_ca = ""
	for c in d.get("ca") or []:
		dong_ca += (
			"<tr><td>%s</td><td style='text-align:center'>%s</td>"
			"<td style='text-align:center'>%s</td>"
			"<td style='text-align:right'>%s</td></tr>"
			% (c["ca"], c["quay"], c["ngay"], _tien(c["tien_mat_dem"]))
		)

	# Khối giữa biên bản đổi theo nguồn kỳ vọng: phiếu theo ca thì kê ca,
	# phiếu theo ngày thì kê điểm bán và khoảng ngày. Một biên bản mà kê
	# bảng ca rỗng thì người đọc không biết số kỳ vọng ở đâu ra.
	if (d.get("nguon_ky_vong") or "") == NG_NGAY:
		nhan_ngay = (
			"ngày %s" % _ngay_chu(d.get("tu_ngay"))
			if str(d.get("tu_ngay") or "") == str(d.get("den_ngay") or "")
			else "từ %s đến %s (%s ngày)" % (
				_ngay_chu(d.get("tu_ngay")), _ngay_chu(d.get("den_ngay")),
				cint(d.get("so_ngay")))
		)
		khoi_nguon = (
			"<p style='margin:10px 0 4px'>Hai bên cùng kiểm đếm và bàn giao số "
			"tiền mặt bán hàng tại <b>%s</b>, doanh thu %s.</p>"
			"<p style='margin:6px 0'>Nội dung nộp tiền: <b>%s</b>. "
			"Nơi giao nhận: <b>%s</b>.</p>"
			"<p style='margin:6px 0'>Doanh thu tiền mặt theo hệ thống trong "
			"kỳ: <b>%s đồng</b>.</p>"
			% (
				frappe.utils.escape_html(d.get("ten_diem_ban") or d.get("diem_ban") or ""),
				nhan_ngay,
				frappe.utils.escape_html(d.get("noi_dung") or ""),
				frappe.utils.escape_html(d.get("noi_giao_nhan") or ""),
				_tien(d.get("tien_ky_vong")),
			)
		)
	else:
		khoi_nguon = (
			"<p style='margin:10px 0 4px'>Hai bên cùng kiểm đếm và bàn giao số "
			"tiền mặt thu tại quầy theo các ca làm việc sau:</p>"
			"<table style='width:100%%;border-collapse:collapse;margin:4px 0' "
			"border='1' cellpadding='5'>"
			"<tr style='background:#f2f2f2'><th>Mã ca</th><th>Quầy</th>"
			"<th>Ngày</th><th>Tiền mặt đếm lúc chốt (đ)</th></tr>%s</table>"
			"<p style='margin:6px 0'>Tiền lẻ để lại quầy cho ca sau: "
			"<b>%s đồng</b>. Số tiền kỳ vọng bàn giao: <b>%s đồng</b>.</p>"
			% (
				dong_ca or "<tr><td colspan='4' style='text-align:center'>(không có ca)</td></tr>",
				_tien(d.get("tien_le_giu_lai")),
				_tien(d.get("tien_ky_vong")),
			)
		)

	lech = flt(d.get("lech"))
	khoi_lech = ""
	if abs(lech) >= 1:
		khoi_lech = (
			"<p style='margin:6px 0'>Chênh lệch so với kỳ vọng: <b>%s%s đồng</b> (%s)."
			" Lý do: %s</p>"
			% ("+" if lech > 0 else "-", _tien(abs(lech)),
				"thừa" if lech > 0 else "thiếu",
				frappe.utils.escape_html(d.get("ly_do_lech") or "(chưa ghi)"))
		)

	return """
<div style="font-size:13px;color:#000;line-height:1.55">
	<table style="width:100%%;border-collapse:collapse"><tr>
		<td style="width:42%%;text-align:center;vertical-align:top;font-size:12px">
			<b>THE VAGABOND P&Acirc;TISSERIE</b><br>Số: %(ma)s
		</td>
		<td style="text-align:center;vertical-align:top">
			<b>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</b><br>
			<b>Độc lập - Tự do - Hạnh phúc</b><br>
			<span style="display:inline-block;border-top:1px solid #000;width:180px;margin-top:2px"></span>
		</td>
	</tr></table>
	<p style="text-align:right;font-style:italic;margin:10px 0 0">Ngày %(ngay_chu)s</p>
	<h2 style="text-align:center;margin:14px 0 4px;font-size:17px">BIÊN BẢN BÀN GIAO TIỀN MẶT</h2>
	<p style="text-align:center;margin:0 0 12px;font-style:italic">(Kèm bảng kê mệnh giá)</p>

	<p style="margin:4px 0"><b>Bên giao (Bên A):</b> Ông/Bà %(ben_giao)s, đại diện cửa hàng.</p>
	<p style="margin:4px 0"><b>Bên nhận (Bên B):</b> Ông/Bà %(ben_nhan)s, đại diện kế toán/quỹ.</p>
	%(khoi_nguon)s

	<p style="margin:10px 0 4px"><b>Bảng kê mệnh giá thực nhận:</b></p>
	<table style="width:70%%;border-collapse:collapse;margin:4px 0" border="1" cellpadding="5">
		<tr style="background:#f2f2f2"><th>Mệnh giá (đ)</th><th>Số tờ</th><th>Thành tiền (đ)</th></tr>
		%(dong_mg)s
		<tr><td colspan="2" style="text-align:right"><b>Tổng cộng</b></td>
		<td style="text-align:right"><b>%(thuc_nhan)s</b></td></tr>
	</table>
	<p style="margin:6px 0">Tổng số tiền thực nhận (bằng số): <b>%(thuc_nhan)s đồng</b>.</p>
	<p style="margin:6px 0">Bằng chữ: <b><i>%(bang_chu)s</i></b>.</p>
	%(khoi_lech)s
	<p style="margin:10px 0 4px">Biên bản được lập khi hai bên đã cùng kiểm đếm, có giá trị làm chứng từ
	gốc cho việc ghi sổ quỹ tiền mặt. Bên nhận chịu trách nhiệm về số tiền kể từ thời điểm ký nhận.</p>

	<table style="width:100%%;border-collapse:collapse;margin-top:18px"><tr>
		<td style="width:50%%;text-align:center;vertical-align:top">
			<b>BÊN GIAO</b><br><span style="font-style:italic;font-size:11.5px">(Ký, ghi rõ họ tên)</span><br>%(ky_giao)s
		</td>
		<td style="text-align:center;vertical-align:top">
			<b>BÊN NHẬN</b><br><span style="font-style:italic;font-size:11.5px">(Ký, ghi rõ họ tên)</span><br>%(ky_nhan)s
		</td>
	</tr></table>
</div>""" % {
		"ma": d.get("ma") or "",
		"ngay_chu": _ngay_chu(d.get("ngay") or ""),
		"ben_giao": frappe.utils.escape_html(d.get("ten_nguoi_giao") or ""),
		# Chưa ai ký nhận thì in tên người DỰ KIẾN nhận, kèm chữ "(dự kiến)"
		# để không ai đọc nhầm thành đã nhận. Trước đó chỗ này in một hàng
		# dấu chấm, mà tờ in ra là để cầm đi đưa cho đúng người.
		"ben_nhan": frappe.utils.escape_html(
			d.get("ten_nguoi_nhan")
			or ((d.get("ten_nguoi_nhan_du_kien") or "") + " (dự kiến)"
				if (d.get("ten_nguoi_nhan_du_kien") or "").strip()
				else "................................")),
		"khoi_nguon": khoi_nguon,
		"ky_vong": _tien(d.get("tien_ky_vong")),
		"dong_mg": dong_mg or "<tr><td colspan='3' style='text-align:center'>(trống)</td></tr>",
		"thuc_nhan": _tien(d.get("tong_thuc_nhan")),
		"bang_chu": chu_so_tien(d.get("tong_thuc_nhan")),
		"khoi_lech": khoi_lech,
		"ky_giao": ky(d.get("chu_ky_ben_giao"), d.get("ten_nguoi_giao"), d.get("giao_luc")),
		"ky_nhan": ky(d.get("chu_ky_ben_nhan"), d.get("ten_nguoi_nhan"), d.get("nhan_luc")),
	}


def _ngay_chu(ngay):
	"""2026-08-20 thành 'ngày 20 tháng 08 năm 2026'. THUẦN."""
	s = str(ngay or "")[:10]
	if len(s) == 10 and s[4] == "-":
		return "%s tháng %s năm %s" % (s[8:10], s[5:7], s[0:4])
	return s


@frappe.whitelist()
def xuat_pdf(ma):
	"""Tờ biên bản PDF khổ A4, trả về base64 cho app tải xuống."""
	_kiem_quyen()
	d = chi_tiet(ma)
	from frappe.utils.pdf import get_pdf

	from vagabond import mau_chuan

	# Đi qua khung chuẩn để lấy đúng bộ phông có dấu tiếng Việt. Trước
	# 31/08/2026 tờ này tự dựng khung và khai `Times New Roman` - phông máy
	# chủ KHÔNG có - nên wkhtmltopdf mượn phông khác cho riêng chữ có dấu và
	# tờ in ra vỡ chữ. Xem `vagabond/phong_chu.py`.
	khung = mau_chuan.khung_trang(
		_html_bien_ban(d), "Biên bản bàn giao tiền mặt %s" % ma, le="16mm 15mm")
	noi_dung = get_pdf(khung, options={"page-size": "A4", "orientation": "Portrait"})
	return {
		"ten_file": "Bien-ban-ban-giao-%s.pdf" % str(ma).replace("/", "-"),
		"b64": base64.b64encode(noi_dung).decode(),
		"kieu": "application/pdf",
	}

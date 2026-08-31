# -*- coding: utf-8 -*-
"""Hoá đơn điện tử thành chứng từ trong sổ: soi chỗ sót và dựng lại cho đúng.

Bài anh Việt giao 26/08/2026, sau khi bên Uyên báo: "ngày 4/8 Ngon Cổ Điển
xuất 3 HĐ, next lấy về có 2 HĐ thôi ạ".

Đúng là sót. Tờ giữa, số 50845, 6.868.800 đ, nằm nguyên trong bảng hoá đơn
điện tử nhưng không bao giờ thành Hoá đơn mua hàng.

QUÉT RỘNG RA THÌ KHÔNG PHẢI MỘT TỜ
-----------------------------------
Đếm ngày 26/08/2026 trên site thật, từ 25/07 tới 25/08:

    Nhóm A  22 hoá đơn ĐẦU VÀO    126.427.733 đ
            "Item Wise Tax Details do not match with Taxes and Charges"
    Nhóm B 103 hoá đơn ĐẦU RA      31.176.592 đ
            mã hàng trên hoá đơn không có trong danh mục Món

    Tổng   125 hoá đơn            157.604.325 đ

Cả 125 tờ đều đã bị đóng dấu `da_tao_chung_tu = 1`, tức là hệ tự nhận
"xong rồi", trong khi không có chứng từ nào được dựng. Lý do có ghi vào ô
`ly_do_bo_qua`, nhưng không có màn nào hiện ô đó ra, nên không ai đọc.

BA CÁI SAI, VÀ CẢ BA ĐỀU NẰM Ở CHỖ KHÁC NHAU
---------------------------------------------
1. SAI VỀ THUẾ (nhóm A).

   Tờ hoá đơn điện tử ghi MỘT con số thuế tổng, và đó là con số đã gửi cơ
   quan thuế. Khi dựng Hoá đơn mua hàng, ERPNext lại đi hỏi từng mã hàng
   xem "Mẫu thuế mặt hàng" của mày là bao nhiêu, cộng lại, rồi so với con
   số tổng kia. Lệch một đồng là nó ném lỗi và bỏ cả tờ.

   Mà lệch là chuyện đương nhiên: mẫu thuế trên danh mục Món là dự đoán
   cho tương lai, còn con số trên hoá đơn là sự thật đã xảy ra. Hàng mua
   tháng này 8% mà danh mục ghi 10% thì không bao giờ khớp.

   Cách gỡ: XOÁ mẫu thuế mặt hàng khỏi từng dòng của chứng từ sinh ra, để
   con số thuế của hoá đơn điện tử là nguồn sự thật duy nhất. Đã dò mã
   nguồn ERPNext v16 (`controllers/taxes_and_totals.py`): phép kiểm đó bỏ
   qua dòng thuế dạng "Actual" khi thuế suất từng dòng bằng 0, nên xoá
   mẫu thuế là đủ, không phải vá gì thêm.

2. SAI VỀ CÁCH BỎ CUỘC (cả hai nhóm).

   Dựng hỏng thì hệ vẫn đóng dấu `da_tao_chung_tu = 1`. Đóng dấu là lời
   hứa "cái này xong rồi", mà lời hứa đó sai. Tờ hỏng biến mất khỏi mọi
   danh sách, và chỉ lộ ra khi có người ngồi dò tay như bên Uyên vừa làm.

   Cách gỡ: hỏng thì KHÔNG đóng dấu. Ghi lý do, đếm số lần đã thử, và để
   nguyên trạng thái chưa xong. Hàng đợi xếp theo số lần thử tăng dần nên
   tờ hỏng đi xuống cuối, không chiếm chỗ của tờ mới, nhưng vẫn nằm trong
   danh sách và vẫn đếm được.

3. KHÔNG CÓ CHỖ NÀO NHÌN THẤY (cả hai nhóm).

   Cửa `con_sot` ở dưới liệt kê thẳng những tờ chưa thành chứng từ, gom
   theo lý do, kèm tổng tiền. Chỉ đọc.

HOÁ ĐƠN ĐẦU RA KHÔNG PHẢI VIỆC CỦA MÔ ĐUN NÀY
----------------------------------------------
Anh Việt chốt 26/08/2026: "Nhóm B không đụng vào nữa, cái đó bên Fabi đang
xuất hoá đơn."

Nhóm B là 103 tờ đầu ra bán lẻ, mã hàng là mã của máy bán hàng ngoài quầy
(BAEN00012 "Bánh Khúc"...), không có trong danh mục Món của hệ. Chúng do
Fabi xuất, sổ sách bên đó đã ghi.

Nên hoá đơn đầu ra nào KHÔNG có chứng từ trong hệ thì đánh dấu BỎ QUA HỢP
LỆ kèm lý do, chứ không nằm mãi trong danh sách còn sót. Để chúng trong
danh sách là 103 dòng báo động giả, mà một danh sách kêu oan thì y hệt một
danh sách không ai đọc: đúng cái bẫy đã làm 22 tờ đầu vào nằm im cả tháng.

Hoá đơn đầu ra do CHÍNH HỆ xuất thì khác: chúng đã có `custom_minvoice_id`
trỏ về, nên `_da_co_chung_tu` nhận ra và không rơi vào nhánh này.

BA HÀNG RÀO NỮA, ĐỂ KHÔNG BAO GIỜ LẶP LẠI
------------------------------------------
1. DỰNG XONG PHẢI ĐỐI CHIẾU TỔNG. Chứng từ sinh ra mà tổng tiền lệch hoá
   đơn điện tử quá một đồng thì HUỶ CẢ LƯỢT GHI của tờ đó và ghi lý do.
   Sai lặng lẽ còn tệ hơn không dựng: không dựng thì còn đếm được.

2. KHÔNG BÓ HẸP CỬA SỔ NGÀY. Bản cũ chỉ quét 60 ngày gần nhất, tờ cũ hơn
   thì vĩnh viễn không ai dựng. Nay mặc định quét từ đầu, và xếp hàng đợi
   theo số lần thử nên tờ hỏng vẫn không chiếm chỗ.

3. CHẶN TRÙNG THEO SỐ HOÁ ĐƠN. Kế toán có thể đã gõ tay một tờ mà không
   gắn mã hoá đơn điện tử. Dựng thêm là hai chứng từ cho một tờ hoá đơn.
   Gặp thì DỪNG và báo, không tự gắn vào chứng từ của người khác.
"""

import json

# ------------------------------------------------------------ phần thuần
#
# Đặt trên `import frappe` để bộ kiểm thử tầng khung chạy được ở CI mà
# không cần site. Ca kiểm ở khung/kiem_thu/thu_minvoice_chung_tu.py.

DT_HD = "MInvoice Invoice"
PI = "Purchase Invoice"
SI = "Sales Invoice"

LOAI_VAO = "Đầu vào"
LOAI_RA = "Đầu ra"

# Trạng thái mà hoá đơn KHÔNG cần thành chứng từ nữa.
TT_KHOI_DUNG = ("Bị thay thế", "Đã huỷ")

# Chuông báo tắc nhịp gửi về hộp thư kế toán, vì việc phải làm khi nghe
# chuông là việc của kế toán chứ không phải của người viết mã.
EMAIL_KE_TOAN = "account@thevagabondpatisserie.com"

# Lệch tới bao nhiêu đồng thì coi như khớp, khỏi nắn.
#
# Một đồng là ngưỡng của cổng chặn ghi sổ và đúng là phải thế. Ở đây nắn
# tổng nên để 1 đồng: dưới mức đó là làm tròn của chính máy phát hành.
NGUONG_KHOP = 1.0


def nan_dau_dong(sl, gia, thtien=None):
	"""Dua mot dong ve dang ERPNext nhan duoc: don gia KHONG AM. THUAN.

	Hoa don dieu chinh giam va hoa don thay the ghi so am. Nghi dinh
	70/2025 cho phep ghi dau tru, va nha phat hanh moi noi ghi mot kieu:
	co noi de so luong am va don gia duong, co noi de CA HAI cung am.

	Ca hai cung am la cai bay: am nhan am ra duong, nen mot to hoan tien
	56 trieu di vao so thanh mot to MUA 56 trieu, tien di nguoc chieu ma
	khong lop nao keu. Da gap dung ca nay voi to hoan tien cua Grab.

	Quy uoc cua ERPNext cho chung tu tra hang: don gia luon duong, dau am
	nam o SO LUONG. Nen o day gom het dau ve mot cho:

	    dau lay theo thanh tien khi co, khong thi lay theo tich so luong
	    nhan don gia; don gia tra ve luon la tri tuyet doi.

	Tra ve cap (so luong, don gia).
	"""
	try:
		sl = float(sl or 0)
	except (TypeError, ValueError):
		sl = 0.0
	try:
		gia = float(gia or 0)
	except (TypeError, ValueError):
		gia = 0.0
	try:
		tt = float(thtien) if thtien not in (None, "") else None
	except (TypeError, ValueError):
		tt = None

	if tt is not None and tt != 0:
		am = tt < 0
	else:
		am = (sl * gia) < 0

	gia = abs(gia)
	sl = -abs(sl) if am else abs(sl)
	return (sl, gia)


def dong_tu_hoa_don(it, dau_to=1):
	"""Một dòng hàng của hoá đơn điện tử thành số liệu dùng được. THUẦN.

	Ô đơn giá TRỐNG là chuyện thật: hoá đơn tiền điện, tiền nước, phí dịch
	vụ đều chỉ có thành tiền. Gặp thì đặt số lượng về 1 và lấy thành tiền
	làm đơn giá, như vậy tổng luôn khớp tuyệt đối.

	Bản cũ giữ nguyên số lượng rồi vẫn lấy thành tiền làm đơn giá, nên
	thành tiền bị nhân lên bằng số lượng lần. Một hoá đơn điện 53 triệu
	từng thành 814 tỷ vì lỗi này.

	Ô đơn giá ghi SỐ KHÔNG cũng phải xử như trống - ca thật 27/08/2026
	--------------------------------------------------------------------
	Hoá đơn tiếp khách Avanti C26TAV/5019 có dòng "Phí phục vụ" ghi
	sluong 0, dgia 0, thtien 1.283.500. Bản cũ chỉ bắt trường hợp dgia là
	None nên dòng đó vào chứng từ với đơn giá 0. Mà đơn giá 0 thì ERPNext
	tự điền lại theo Bảng giá nhập của mặt hàng, ở đây là 4.500.000, làm tờ
	hoá đơn phình thêm đúng 4,5 triệu.

	Nên: đơn giá trống HOẶC bằng không, mà có thành tiền, thì lấy thành
	tiền làm đơn giá và đặt số lượng về 1. Không bao giờ để một dòng đi vào
	chứng từ với đơn giá 0 trong khi hoá đơn có tiền.

	`dau_to` là dấu của cả tờ, lấy từ tổng tiền. Tờ dương thì giữ nguyên
	mọi thứ như cũ, kể cả dòng chiết khấu ghi số âm. Tờ ÂM thì gom hết dấu
	về ô số lượng, xem `nan_dau_dong`.
	"""
	d = it or {}
	sl = d.get("sluong") or 1
	gia = d.get("dgia")
	if not gia and d.get("thtien"):
		gia = d.get("thtien")
		sl = 1
	elif gia is None:
		gia = 0
	if int(dau_to or 1) < 0:
		sl, gia = nan_dau_dong(sl, gia, d.get("thtien"))
	return {
		"ma": str(d.get("mhhdvu") or "").strip(),
		"ten": str(d.get("ten") or "").strip(),
		"dvt": d.get("dvtinh"),
		"sl": sl,
		"gia": gia,
		"tien": (sl or 0) * (gia or 0),
	}


def dau_cua_to(tong_tien):
	"""To nay la to am hay to duong. THUAN. Tra ve -1 hoac 1."""
	try:
		return -1 if float(tong_tien or 0) < 0 else 1
	except (TypeError, ValueError):
		return 1


def can_theo_truoc_thue(tong_dong, truoc_thue):
	"""So tổng dòng hàng với tiền trước thuế của hoá đơn. THUẦN.

	Trả về (viec, so_tien):
	    ("khop", 0)   không phải nắn gì
	    ("giam", x)   dòng hàng THỪA x đồng, ghi x vào ô Giảm giá
	    ("phi", x)    dòng hàng THIẾU x đồng, thêm một dòng phí x đồng

	Ba nguồn làm lệch: chiết khấu, giảm thuế theo nghị quyết, và các khoản
	phí (vé máy bay, phí dịch vụ) không nằm trong dòng hàng khi lên XML.
	"""
	chenh = float(tong_dong or 0) - float(truoc_thue or 0)
	if chenh > NGUONG_KHOP:
		return ("giam", chenh)
	if chenh < -NGUONG_KHOP:
		return ("phi", -chenh)
	return ("khop", 0)


def cap_trung(hang):
	"""Gom những chứng từ cùng trỏ về MỘT tờ hoá đơn điện tử. THUẦN.

	`hang` là list dict có `ma_hddt` và `ten`. Trả list nhóm từ 2 tờ trở lên,
	tờ cũ nhất đứng đầu.

	VÌ SAO ĐẾM CÁI NÀY (31/08/2026)
	-------------------------------
	Hôm đó 31 tờ hoá đơn mua bị dựng hai lần vì hai lượt chạy chồng nhau.
	Khoá ở `_chay` chặn nguyên nhân đó rồi, nhưng chặn một nguyên nhân đã
	biết không bằng NHÌN THẤY được khi có nguyên nhân mới.

	Không ai phát hiện ra bằng máy cả: anh Việt nhìn màn danh sách thấy
	dòng nào cũng có một dòng y hệt bên dưới. Một cái đếm đơn giản như hàm
	này thì lượt quét đầu tiên đã kêu.
	"""
	theo_ma = {}
	for h in hang or []:
		ma = str((h or {}).get("ma_hddt") or "").strip()
		if not ma:
			continue
		theo_ma.setdefault(ma, []).append(h)
	ra = []
	for ma, ds in theo_ma.items():
		if len(ds) < 2:
			continue
		ra.append({
			"ma_hddt": ma,
			"so_to": len(ds),
			"ten": [str((x or {}).get("ten") or "") for x in ds],
		})
	ra.sort(key=lambda x: (-x["so_to"], x["ma_hddt"]))
	return ra


def khoi_dung_duoc(trang_thai):
	"""Tờ này khỏi cần dựng chứng từ nữa. THUẦN."""
	return str(trang_thai or "").strip() in TT_KHOI_DUNG


def rut_gon_loi(loi):
	"""Câu lỗi rút gọn để cất vào ô lý do. THUẦN.

	Cắt thẻ HTML và xuống dòng: ô này hiện trong bảng, để nguyên thẻ br thì
	người đọc thấy chữ "<br>" giữa câu.
	"""
	s = str(loi or "").replace("<br>", " ").replace("\n", " ")
	while "  " in s:
		s = s.replace("  ", " ")
	return s.strip()[:400] or "Không dựng được chứng từ, chưa rõ nguyên nhân"


def gom_theo_ly_do(hang):
	"""Gom danh sách tờ sót theo lý do, đếm số tờ và cộng tiền. THUẦN."""
	bang = {}
	for h in hang or []:
		k = str((h or {}).get("ly_do") or "").strip() or "(không ghi lý do)"
		o = bang.setdefault(k, {"ly_do": k, "so_to": 0, "tien": 0.0, "loai": set()})
		o["so_to"] += 1
		o["tien"] += abs(float((h or {}).get("tong_tien") or 0))
		if h.get("loai"):
			o["loai"].add(h["loai"])
	ra = []
	for o in bang.values():
		o["loai"] = sorted(o["loai"])
		ra.append(o)
	return sorted(ra, key=lambda o: -o["tien"])


# ------------------------------------------------------- phần chạm hệ

import frappe  # noqa: E402
from frappe.utils import cint, flt, nowdate  # noqa: E402

from contextlib import ExitStack  # noqa: E402

# KHOA TEP, cung khuon voi ban_hang.py. May chu khong co thi lui ve khoa
# rong chu khong chan nghiep vu: mot lan dung to con hon ca ngay khong dung
# duoc to nao.
try:  # pragma: no cover
	from frappe.utils.synchronization import LockTimeoutError, filelock  # noqa: E402
except Exception:  # pragma: no cover
	import contextlib

	class LockTimeoutError(Exception):
		pass

	@contextlib.contextmanager
	def filelock(ten, timeout=30, **kw):
		yield

QUYEN = {"System Manager", "Accounts Manager", "Accounts User"}

# Tên khoá của lượt dựng chứng từ.
#
# VÌ SAO PHẢI CÓ KHOÁ (ca thật 31/08/2026, mất 31 tờ trùng)
# ----------------------------------------------------------
# Ngày 31/08 chạy bù hai lượt chồng lên nhau: một lượt gọi trước còn đang
# chạy dở ở máy chủ, một lượt nữa gọi vào. Cả hai đều đọc hàng đợi bằng
# `da_tao_chung_tu = 0`, đều thấy CÙNG một tờ, `_da_co_chung_tu` của cả hai
# đều trả về rỗng vì chưa bên nào kịp ghi, rồi cả hai cùng dựng.
#
# Kết quả: 31 cặp Hoá đơn mua hàng y hệt nhau, cách nhau ba mươi mốt phần
# nghìn giây, 81.136.219 đ mua vào đếm hai lần. Chưa tờ nào ghi sổ nên chưa
# vào sổ cái, nhưng nếu kế toán ghi sổ trước khi ai kịp nhìn thì đó là một
# tháng số liệu mua vào sai gấp đôi.
#
# Phép kiểm "đã có chứng từ chưa" KHÔNG BAO GIỜ tự nó đủ, vì giữa lúc kiểm
# và lúc ghi luôn có một khe hở. Chỉ có khoá mới đóng được khe đó.
#
# Từ bản này nguy cơ còn cao hơn trước chứ không thấp đi: nhịp tự động 15
# phút vừa được khai lại, và nút "Đồng bộ M-Invoice" cho phép người ta bấm
# tay bất cứ lúc nào. Hai đường đó gặp nhau là chuyện sớm muộn.
KHOA_DUNG = "vagabond_minvoice_dung_chung_tu"

# Mỗi lượt dựng tối đa bao nhiêu tờ. Cao hơn thì một lượt chạy quá dài và
# Frappe cắt ngang giữa chừng.
MOI_LUOT = 200

# Mốc sớm nhất còn đi dựng chứng từ. Trước mốc này là sổ của năm cũ, đã
# khoá, không tự đụng vào (Điều 11).
NGAY_BAT_DAU = "2026-01-01"

TRUONG_MOI = {
	DT_HD: [
		{
			"fieldname": "so_lan_thu",
			"label": "Số lần đã thử dựng chứng từ",
			"fieldtype": "Int",
			"insert_after": "da_tao_chung_tu",
			"read_only": 1,
			"description": (
				"Máy tự đếm. Tờ thử nhiều lần mà vẫn hỏng thì xuống cuối hàng "
				"đợi, nhưng KHÔNG bị đánh dấu là đã xong."
			),
		},
	],
}


def _kiem_quyen(viec="xem hoá đơn điện tử chưa thành chứng từ"):
	if not QUYEN & set(frappe.get_roles()):
		frappe.throw(
			"Tài khoản của bạn không có quyền %s. Nhờ chị Dung hoặc anh Việt "
			"chạy giúp." % viec
		)


def _da_co_chung_tu(ma):
	"""Tờ này đã có chứng từ thật trong sổ chưa. Trả tên chứng từ hoặc rỗng."""
	for dt in (PI, SI):
		ten = frappe.db.get_value(dt, {"custom_minvoice_id": ma}, "name")
		if ten:
			return ten
	return ""


def _trung_theo_so_hoa_don(r):
	"""Đã có chứng từ khác cùng nhà cung cấp và cùng số hoá đơn chưa.

	Kế toán có thể đã gõ tay một tờ mà không gắn mã hoá đơn điện tử. Dựng
	thêm là hai chứng từ cho một tờ hoá đơn, và số liệu mua vào nhân đôi.

	Tìm được thì DỪNG và báo, KHÔNG tự gắn mã vào chứng từ của người khác:
	gắn nhầm còn khó gỡ hơn là để hai bên tự nhìn nhau.
	"""
	so = str(r.get("so_hd") or "").strip()
	if not so:
		return ""
	mst = (r.get("mst_doi_tac") or "").strip()
	ncc = None
	if mst:
		ncc = frappe.db.get_value("Supplier", {"tax_id": mst}, "name")
	if not ncc and r.get("nguoi_mua_ban"):
		ncc = frappe.db.get_value(
			"Supplier", {"supplier_name": r["nguoi_mua_ban"].strip()}, "name")
	if not ncc:
		return ""
	return frappe.db.get_value(PI, {
		"supplier": ncc, "bill_no": so, "docstatus": ["<", 2],
		"custom_minvoice_id": ["in", ["", None]],
	}, "name") or ""


def _ghi_hong(ma, loi):
	"""Ghi lý do hỏng và tăng số lần thử. TUYỆT ĐỐI không đóng dấu đã xong.

	Đây là chỗ bản cũ sai nặng nhất: nó đóng dấu `da_tao_chung_tu = 1` ngay
	cả khi không dựng được gì, nên tờ hỏng biến mất khỏi mọi danh sách.
	"""
	try:
		lan = cint(frappe.db.get_value(DT_HD, ma, "so_lan_thu"))
		frappe.db.set_value(DT_HD, ma, {
			"ly_do_bo_qua": rut_gon_loi(loi),
			"so_lan_thu": lan + 1,
			"da_tao_chung_tu": 0,
		}, update_modified=False)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "minvoice_chung_tu: ghi hong")


def _ghi_xong(ma, ghi_chu=""):
	"""Đóng dấu đã xong. CHỈ gọi khi thật sự có chứng từ."""
	frappe.db.set_value(DT_HD, ma, {
		"da_tao_chung_tu": 1,
		"ly_do_bo_qua": ghi_chu or "",
	}, update_modified=False)


def bo_mau_thue_mat_hang(doc):
	"""Xoá mẫu thuế mặt hàng khỏi mọi dòng của chứng từ vừa dựng.

	ĐÂY LÀ PHÉP SỬA CHÍNH của bản này. Xem mục 1 ở đầu tệp.

	Con số thuế trên hoá đơn điện tử là con số đã gửi cơ quan thuế. Mẫu
	thuế trên danh mục Món là dự đoán. Để cả hai cùng nói thì ERPNext bắt
	chúng khớp nhau, mà chúng không có lý do gì phải khớp.

	Xoá xong thì thuế suất từng dòng bằng 0, và ERPNext bỏ qua phép đối
	chiếu với dòng thuế dạng "Actual" (đã dò mã nguồn v16,
	`controllers/taxes_and_totals.py`).
	"""
	for d in doc.get("items") or []:
		try:
			# CHUỖI RỖNG, KHÔNG PHẢI None. Đây là chỗ bản đầu sai và tưởng đã
			# xong: deploy v315 xong chạy thử vẫn hỏng nguyên si.
			#
			# `accounts_controller.set_missing_item_details` chép giá trị từ
			# danh mục Món vào ô nào đang là None:
			#
			#     if item.get(fieldname) is None or fieldname in force_item_fields:
			#         item.set(fieldname, value)
			#
			# `item_tax_template` KHÔNG nằm trong `force_item_fields`, nên đặt
			# chuỗi rỗng là ERPNext để yên, còn đặt None là nó điền lại mẫu
			# thuế của mã hàng ngay trong lúc validate, và mọi công xoá ở đây
			# thành công cốc.
			d.item_tax_template = ""
			d.item_tax_rate = "{}"
		except Exception:
			continue
	return doc


def _dong_pi(x, tk_chi_phi, mapped=None, uom=None, he_so=1):
	"""Một dòng Hoá đơn mua hàng từ một dòng hoá đơn điện tử.

	Ghim luôn `price_list_rate` bằng đúng đơn giá trên hoá đơn. Bảng giá
	nhập trong máy chỉ là giá tham khảo của mình, còn đơn giá trên hoá đơn
	điện tử là số nhà cung cấp đã gửi cơ quan thuế. Không ghim thì ERPNext
	lấy giá bảng điền vào những dòng đơn giá 0, và ngày 27/08/2026 việc đó
	đã làm tờ tiếp khách Avanti phình thêm 4,5 triệu.
	"""
	dong = {
		"qty": x["sl"],
		"rate": x["gia"],
		"price_list_rate": x["gia"],
		"discount_percentage": 0,
		"discount_amount": 0,
		"margin_rate_or_amount": 0,
		"conversion_factor": he_so or 1,
		"description": x["ten"] + ((" (%s)" % x["dvt"]) if x["dvt"] else ""),
	}
	if mapped:
		dong["item_code"] = mapped
		dong["uom"] = uom
	else:
		dong["item_name"] = (x["ten"] or "Hàng hoá/dịch vụ")[:140]
		dong["uom"] = uom or "Nos"
		dong["stock_uom"] = uom or "Nos"
		dong["ten_hang_ncc"] = x["ten"][:140]
	if tk_chi_phi:
		dong["expense_account"] = tk_chi_phi
	return dong


@frappe.whitelist()
def con_sot(tu_ngay=None, den_ngay=None, gioi_han=2000):
	"""CHỈ ĐỌC: hoá đơn điện tử chưa thành chứng từ, gom theo lý do.

	Đây là màn mà lẽ ra phải có từ đầu. Không có nó thì 125 tờ nằm im một
	tháng mà không ai biết, và chỉ lộ khi có người ngồi dò tay.

	Soi bằng SỰ THẬT chứ không bằng lời hứa: tờ nào không có chứng từ nào
	trỏ về là còn sót, bất kể ô `da_tao_chung_tu` đang ghi gì.
	"""
	_kiem_quyen()
	den_ngay = den_ngay or nowdate()
	tu_ngay = tu_ngay or frappe.utils.add_days(den_ngay, -180)

	ds = frappe.get_all(
		DT_HD,
		filters={"ngay_lap": ["between", [tu_ngay, den_ngay]]},
		fields=["name", "loai", "ky_hieu", "so_hd", "ngay_lap",
			"nguoi_mua_ban", "tong_tien", "trang_thai", "ly_do_bo_qua",
			"da_tao_chung_tu"],
		order_by="ngay_lap desc",
		limit_page_length=cint(gioi_han) or 2000,
	)

	hang = []
	so_dau_ra_fabi = 0
	for h in ds:
		if khoi_dung_duoc(h.get("trang_thai")):
			continue
		if _da_co_chung_tu(h["name"]):
			continue
		if (h.get("loai") or "") == LOAI_RA:
			# Đầu ra bán lẻ do Fabi xuất, không phải việc của hệ (anh Việt
			# chốt 26/08/2026). Vẫn ĐẾM để có người nhìn thấy con số, nhưng
			# không đổ vào danh sách việc phải làm.
			so_dau_ra_fabi += 1
			continue
		hang.append({
			"ma": h["name"],
			"loai": h.get("loai"),
			"ky_hieu": h.get("ky_hieu"),
			"so_hd": h.get("so_hd"),
			"ngay_lap": str(h.get("ngay_lap") or ""),
			"doi_tac": (h.get("nguoi_mua_ban") or "")[:60],
			"tong_tien": flt(h.get("tong_tien")),
			"ly_do": rut_gon_loi(h.get("ly_do_bo_qua")) if h.get("ly_do_bo_qua")
				else ("Đã đóng dấu xong nhưng không có chứng từ nào"
					if cint(h.get("da_tao_chung_tu")) else "Chưa tới lượt dựng"),
		})

	return {
		"tu_ngay": str(tu_ngay), "den_ngay": str(den_ngay),
		"trung": _dem_trung(),
		"so_to": len(hang),
		"tong_tien": sum(abs(h["tong_tien"]) for h in hang),
		"theo_ly_do": gom_theo_ly_do(hang),
		"dau_ra_fabi": so_dau_ra_fabi,
		"vo_ruot": _dem_vo_ruot(),
		"ds": hang[:500],
	}


def _dem_trung():
	"""Chứng từ nào đang trùng: nhiều tờ cùng trỏ về một hoá đơn điện tử.

	Chỉ đếm tờ CÒN SỐNG: bỏ tờ đã huỷ ở ERPNext và tờ đã tick "Đã huỷ" của
	mình, vì gỡ trùng bằng cách đánh dấu huỷ là cách gỡ hợp lệ.
	"""
	try:
		hang = []
		for dt in (PI, SI):
			for r in frappe.get_all(
				dt,
				filters={"docstatus": ["<", 2], "custom_minvoice_id": ["is", "set"]},
				fields=["name", "custom_minvoice_id", "vgb_huy"],
				limit_page_length=0,
			):
				if cint(r.get("vgb_huy")):
					continue
				hang.append({"ma_hddt": r.custom_minvoice_id, "ten": r.name})
		nhom = cap_trung(hang)
		return {
			"so_nhom": len(nhom),
			"so_to_thua": sum(n["so_to"] - 1 for n in nhom),
			"ds": nhom[:50],
		}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "minvoice_chung_tu: dem trung")
		return {"so_nhom": 0, "so_to_thua": 0, "ds": []}


def _dem_vo_ruot():
	"""Đếm bản ghi VỎ RUỘT: có mã hoá đơn nhưng chưa có ruột.

	Vỏ ruột sinh ra khi M-Invoice trả về một tờ mà chưa kịp đổ dữ liệu vào:
	số hoá đơn trống, ngày trống, tiền bằng 0. Lượt kéo sau lẽ ra lành lại,
	`minvoice_dong_bo.vo_ruot` lo việc đó.

	Nhưng đếm ngày 26/08/2026 thì có 112 vỏ ruột ĐẦU VÀO, cái cũ nhất từ
	22/07, tức là hơn một tháng chưa lành. Nhịp quét đêm chỉ lùi 30 ngày nên
	không với tới cái cũ, còn cái mới thì M-Invoice vẫn chưa trả số.

	Mỗi vỏ ruột đầu vào là một hoá đơn mua có thể đang thiếu. Nên phải ĐẾM
	và cho người nhìn thấy, chứ không để nó nằm im như 22 tờ vừa rồi.
	"""
	try:
		return {
			"vao": frappe.db.count(DT_HD, {
				"so_hd": ["in", ["", None, "0"]], "loai": LOAI_VAO}),
			"ra": frappe.db.count(DT_HD, {
				"so_hd": ["in", ["", None, "0"]], "loai": LOAI_RA}),
			"cu_nhat": frappe.db.get_value(
				DT_HD, {"so_hd": ["in", ["", None, "0"]], "loai": LOAI_VAO},
				"creation", order_by="creation asc"),
		}
	except Exception:
		return {"vao": 0, "ra": 0, "cu_nhat": None}


@frappe.whitelist()
def lanh_vo_ruot(so_ngay=60):
	"""Kéo lại một khoảng rộng để lành các bản ghi vỏ ruột.

	Không dựng chứng từ nào, chỉ đổ ruột vào những tờ còn trống. Nhịp quét
	đêm chỉ lùi 30 ngày, nên tờ cũ hơn phải gọi tay ở đây.

	Chạy xong mà vẫn còn vỏ ruột thì nghĩa là chính M-Invoice chưa có số cho
	tờ đó, không phải lỗi bên mình. Lúc đó là câu hỏi cho nhà cung cấp phần
	mềm hoá đơn, đừng ngồi dò tay tiếp.
	"""
	_kiem_quyen("kéo lại hoá đơn điện tử")
	from vagabond import minvoice_dong_bo

	truoc = _dem_vo_ruot()
	kq = minvoice_dong_bo._keo(so_ngay=cint(so_ngay) or 60)
	sau = _dem_vo_ruot()
	return {
		"ok": 1, "keo": kq, "truoc": truoc, "sau": sau,
		"da_lanh": max(0, cint(truoc.get("vao")) - cint(sau.get("vao"))),
		"loi_nhan": (
			"Vỏ ruột đầu vào: trước %s tờ, sau %s tờ. Còn lại là những tờ "
			"M-Invoice vẫn chưa trả số, hỏi bên họ chứ đừng dò tay."
			% (truoc.get("vao"), sau.get("vao"))
		),
	}


@frappe.whitelist()
def mo_lai(ma=None, tat_ca_hong=0):
	"""Mở lại tờ đã bị đóng dấu nhầm, để lượt chạy sau thử lại. CHỈ ĐỔI CỜ.

	Không dựng chứng từ nào ở đây, không đụng tới số liệu. Chỉ gỡ cái dấu
	"xong rồi" đang sai.
	"""
	_kiem_quyen("mở lại hoá đơn điện tử đã bị bỏ qua")
	if cint(tat_ca_hong):
		kq = con_sot()
		ds = [h["ma"] for h in (kq.get("ds") or [])]
	else:
		ds = [x for x in [(ma or "").strip()] if x]
	if not ds:
		frappe.throw("Chưa chỉ ra tờ nào.")
	for x in ds:
		frappe.db.set_value(DT_HD, x, {
			"da_tao_chung_tu": 0, "so_lan_thu": 0,
		}, update_modified=False)
	frappe.db.commit()
	return {"ok": 1, "mo_lai": len(ds),
		"loi_nhan": "Đã mở lại %s tờ, lượt dựng sau sẽ thử lại." % len(ds)}


# ------------------------------------------------- dựng chứng từ đầu vào


def _cty():
	return frappe.db.get_single_value("Global Defaults", "default_company")


def _tim_ncc(mst, ten):
	"""Nhà cung cấp theo mã số thuế, rồi tới tên. Không có thì dựng mới."""
	mst = (mst or "").strip()
	goc = mst.split("-")[0] if mst else ""
	sup = None
	if mst:
		sup = frappe.db.get_value("Supplier", {"tax_id": mst}, "name")
		if not sup and goc != mst:
			sup = frappe.db.get_value("Supplier", {"tax_id": goc}, "name")
		if not sup:
			sup = frappe.db.get_value("Supplier", {"tax_id": ["like", goc + "%"]}, "name")
	if not sup and ten:
		sup = frappe.db.get_value("Supplier", {"supplier_name": ten.strip()}, "name")
	# TÊN ĐÃ BỊ CẮT CÒN 140 (ca thật 31/08/2026)
	#
	# Ô `supplier_name` chỉ chứa 140 ký tự, mà tên trên hoá đơn điện tử thì
	# dài hơn: "CHI NHÁNH CÔNG TY TNHH LUCA..." bị cắt cụt lúc dựng lần đầu.
	# Lượt sau tra bằng tên ĐẦY ĐỦ nên không thấy, hệ đi dựng nhà cung cấp
	# mới, và cơ sở dữ liệu ném Duplicate entry vì khoá chính trùng.
	#
	# Tra thêm một nhịp bằng đúng cái tên đã cắt trước khi kết luận là chưa
	# có. Cùng một nhà cung cấp mà đẻ ra hai bản ghi còn tệ hơn báo lỗi.
	ten_cat = (ten or ("NCC " + mst))[:140].strip()
	if not sup and ten_cat:
		sup = frappe.db.get_value("Supplier", {"supplier_name": ten_cat}, "name")
	if not sup and ten_cat and frappe.db.exists("Supplier", ten_cat):
		sup = ten_cat
	if sup:
		return sup, goc
	s = frappe.get_doc({
		"doctype": "Supplier",
		"supplier_name": ten_cat,
		"supplier_group": "Công ty (NCC)",
		"supplier_type": "Company",
		"country": "Vietnam",
	})
	if mst:
		s.tax_id = mst
	try:
		s.insert(ignore_permissions=True)
	except Exception:
		# Vẫn trùng thì nghĩa là có sẵn một bản ghi mang đúng tên đó, chỉ là
		# ba nhịp tra ở trên không soi ra (khác dấu cách, khác hoa thường).
		# Lùi lại lấy bản ghi có sẵn chứ đừng làm chết cả tờ hoá đơn.
		frappe.db.rollback()
		sup = frappe.db.get_value("Supplier", {"supplier_name": ten_cat}, "name")
		if not sup:
			raise
		return sup, goc
	return s.name, goc


def _tra_ma_hang(x, goc_mst, ncc):
	"""Mã hàng của hệ ứng với dòng này. Không tra ra thì trả (None, dvt)."""
	uom = x.get("dvt")
	if not (uom and frappe.db.exists("UOM", uom)):
		uom = None
	mapped = None
	if goc_mst:
		if x["ma"]:
			mapped = frappe.db.get_value("MInvoice NCC Map", {
				"supplier_mst": goc_mst, "ma_ncc": x["ma"],
				"item_code": ["is", "set"]}, "item_code")
		if not mapped and x["ten"]:
			mapped = frappe.db.get_value("MInvoice NCC Map", {
				"supplier_mst": goc_mst, "ten_ncc": x["ten"][:140],
				"item_code": ["is", "set"]}, "item_code")
	if not mapped and x["ten"]:
		mapped = frappe.db.get_value("Anh Xa Mat Hang NCC", {
			"nha_cung_cap": ncc, "ten_hang_ncc": x["ten"]}, "ma_hang")
	if not mapped:
		return None, uom, 1

	dvt_kho = frappe.db.get_value("Item", mapped, "stock_uom")
	dung_uom, he_so = dvt_kho, 1
	if uom and uom != dvt_kho:
		cf = frappe.db.get_value("UOM Conversion Detail",
			{"parent": mapped, "uom": uom}, "conversion_factor")
		if cf:
			dung_uom, he_so = uom, cf
		else:
			# TRA KHONG RA HE SO. Van dung don vi kho voi he so 1 de to hoa
			# don con dung so tien, nhung KHONG IM LANG nua.
			#
			# Ca that 27/08/2026, HDM-26-08-00115: nha cung cap ghi "Gói",
			# Mon chua khai Gói nen may lang le ha ve Gram he so 1. Hoa don
			# thanh 4,5 Gram trong khi phieu nhap la 4,5 Kg tuc 4.500 Gram.
			# Tien van dung 1.575.000 nen nhin qua khong thay gi, nhung so
			# luong lech mot nghin lan. Noi vao la hong gia von va ton kho.
			#
			# Dau vet nam o ngay o phan mo ta dong (`_dong_pi` ghi ten kem
			# "(don vi cua nha cung cap)"), va `don_vi_chua_khai` doc lai
			# duoc tu do de man ra hoa don loi ra.
			frappe.log_error(
				"Món %s: nhà cung cấp ghi đơn vị %r, danh mục Món chưa khai "
				"đơn vị đó nên tạm dùng %s hệ số 1. Số tiền đúng nhưng số "
				"lượng có thể lệch. Khai đơn vị vào bảng quy đổi của món rồi "
				"dựng lại tờ hoá đơn."
				% (mapped, uom, dvt_kho),
				"minvoice: don vi chua khai",
			)
	return mapped, dung_uom, he_so


def don_vi_chua_khai(dvt_ncc, dvt_dang_dung, he_so_dang_dung):
	"""Dong nay co dang mang don vi bia ra khong. THUAN.

	True khi nha cung cap co ghi don vi, ma don vi minh dang dung tren dong
	lai khac ten VA he so dang la 1. Do dung la dau van tay cua duong ha
	ngam: tra khong ra he so nen tam lay don vi kho voi he so 1.

	He so khac 1 thi khong tinh, vi luc do da tra ra bang quy doi that.
	"""
	from vagabond import dvt_mua

	ncc = (dvt_ncc or "").strip()
	if not ncc:
		return False
	if dvt_mua.cung_don_vi(ncc, dvt_dang_dung):
		return False
	return abs(dvt_mua.he_so(he_so_dang_dung) - 1.0) < 1e-9


def dung_hoa_don_mua(r):
	"""Dựng một Hoá đơn mua hàng từ một tờ hoá đơn điện tử đầu vào.

	Trả về tên chứng từ. Ném lỗi thì người gọi ghi lý do, KHÔNG đóng dấu.
	"""
	cty = _cty()
	tk_chi_phi = frappe.db.get_value("Company", cty, "default_expense_account")
	tt_chi_phi = frappe.db.get_value("Company", cty, "cost_center")
	tk_thue_vao = frappe.db.get_value(
		"Account", {"company": cty, "name": ["like", "1331 -%"]}, "name")

	ncc, goc_mst = _tim_ncc(r.get("mst_doi_tac"), r.get("nguoi_mua_ban"))

	# Dấu của cả tờ. Tờ âm là hoá đơn điều chỉnh giảm hoặc hoá đơn thay thế
	# ghi số âm, Nghị định 70/2025 cho phép. Xem `nan_dau_dong`.
	dau = dau_cua_to(r.get("tong_tien"))
	dong_goc = [dong_tu_hoa_don(it, dau)
		for it in json.loads(r.get("chi_tiet") or "[]")]

	dong = []
	for x in dong_goc:
		ma, uom, he_so = _tra_ma_hang(x, goc_mst, ncc)
		dong.append(_dong_pi(x, tk_chi_phi, ma, uom, he_so))

	if not dong:
		dong = [_dong_pi({
			"ma": "", "ten": "Hàng hoá/dịch vụ theo hoá đơn", "dvt": None,
			"sl": dau, "gia": abs(flt(r.get("tien_truoc_thue"))), "tien": 0,
		}, tk_chi_phi)]

	# Cân theo TRỊ TUYỆT ĐỐI rồi mới gắn dấu lại, để tờ âm và tờ dương đi
	# chung một đường. Nhân `dau` vào cả hai vế là phép nhân cùng chiều nên
	# tờ dương ra đúng kết quả cũ, không đổi gì.
	tong_dong = sum(flt(d.get("qty")) * flt(d.get("rate")) for d in dong)
	viec, so_tien = can_theo_truoc_thue(
		dau * tong_dong, dau * flt(r.get("tien_truoc_thue")))
	giam_gia = (dau * so_tien) if viec == "giam" else 0
	if viec == "phi":
		dong.append(_dong_pi({
			"ma": "", "ten": "Phí khác theo hoá đơn", "dvt": None,
			"sl": dau, "gia": so_tien, "tien": so_tien,
		}, tk_chi_phi))

	pi = frappe.get_doc({
		"doctype": PI, "company": cty, "supplier": ncc,
		"set_posting_time": 1, "posting_date": str(r.get("ngay_lap")),
		"currency": "VND", "update_stock": 0,
		"is_return": 1 if flt(r.get("tong_tien")) < 0 else 0,
		"apply_discount_on": "Net Total", "discount_amount": giam_gia,
		"bill_no": str(r.get("so_hd") or ""), "bill_date": str(r.get("ngay_lap")),
		"custom_minvoice_id": r.get("name"),
		"custom_trang_thai_hddt": r.get("trang_thai") or "",
		"remarks": "m-invoice %s so %s%s" % (
			r.get("ky_hieu") or "", r.get("so_hd"),
			(" | Tra cuu: " + r["ma_tra_cuu"]) if r.get("ma_tra_cuu") else ""),
		"items": dong,
	})
	# Tờ âm thì tiền thuế cũng âm, nên phải xét KHÁC KHÔNG chứ không phải
	# lớn hơn không. Xét lớn hơn không là bỏ luôn dòng thuế của tờ âm, và
	# tổng chứng từ lệch đúng bằng tiền thuế.
	if tk_thue_vao and flt(r.get("tien_thue")) != 0:
		pi.append("taxes", {
			"charge_type": "Actual", "account_head": tk_thue_vao,
			"description": "Thuế GTGT được khấu trừ",
			"tax_amount": flt(r.get("tien_thue")),
			"category": "Total", "add_deduct_tax": "Add",
		})

	# PHÉP SỬA CHÍNH. Phải chạy TRƯỚC insert, vì ERPNext tính thuế từng dòng
	# ngay trong validate của insert.
	bo_mau_thue_mat_hang(pi)

	pi.cost_center = tt_chi_phi
	for d in pi.items:
		if not d.cost_center:
			d.cost_center = tt_chi_phi
	for t in pi.taxes:
		if not t.cost_center:
			t.cost_center = tt_chi_phi

	pi.insert(ignore_permissions=True)

	# HÀNG RÀO CUỐI: tổng của chứng từ vừa dựng phải bằng tổng trên hoá đơn
	# điện tử. Lệch thì ném lỗi, và người gọi sẽ huỷ cả lượt ghi của tờ này.
	#
	# Sai lặng lẽ còn tệ hơn không dựng: không dựng thì còn đếm được bằng
	# `con_sot`, còn dựng sai thì nó nằm trong sổ như một con số thật.
	lech = flt(pi.grand_total) - flt(r.get("tong_tien"))
	if abs(lech) > NGUONG_KHOP:
		frappe.throw(
			"Chứng từ dựng ra tổng %s đ, hoá đơn điện tử ghi %s đ, lệch %s đ. "
			"Không nhận." % (
				"{:,.0f}".format(flt(pi.grand_total)),
				"{:,.0f}".format(flt(r.get("tong_tien"))),
				"{:,.0f}".format(lech)),
		)
	return pi.name


def _mot_to(r):
	"""Xử một tờ. Trả (da_dung, ghi_chu). Không bao giờ ném ra ngoài."""
	ma = r.get("name")
	try:
		if khoi_dung_duoc(r.get("trang_thai")):
			_ghi_xong(ma, "Hoá đơn %s nên không cần chứng từ."
				% (r.get("trang_thai") or "").lower())
			return (0, "khoi_dung")
		cu = _da_co_chung_tu(ma)
		if cu:
			_ghi_xong(ma, "Đã có chứng từ %s." % cu)
			return (0, "da_co")
		if (r.get("loai") or "") == LOAI_RA:
			# Anh Việt chốt 26/08/2026: đầu ra bán lẻ do Fabi xuất. Xem mục
			# "Hoá đơn đầu ra không phải việc của mô đun này" ở đầu tệp.
			_ghi_xong(ma, "Hoá đơn đầu ra do Fabi xuất, hệ không dựng chứng từ.")
			return (0, "dau_ra_fabi")
		trung = _trung_theo_so_hoa_don(r)
		if trung:
			_ghi_hong(ma, "Đã có chứng từ %s cùng nhà cung cấp và cùng số hoá "
				"đơn nhưng chưa gắn mã hoá đơn điện tử. Nhờ kế toán soi rồi "
				"gắn tay, hệ không tự gắn vào chứng từ có sẵn." % trung)
			return (0, "trung_so_hoa_don")
		ten = dung_hoa_don_mua(r)
		_ghi_xong(ma, "")
		return (1, ten)
	except Exception as e:
		# Huỷ mọi thứ tờ này vừa ghi dở, kể cả chứng từ đã insert mà đối
		# chiếu tổng không đạt. Rollback chỉ lùi tới lần commit gần nhất, mà
		# `_chay` commit sau TỪNG tờ, nên không đụng tới tờ trước.
		try:
			frappe.db.rollback()
		except Exception:
			pass
		_ghi_hong(ma, e)
		frappe.log_error(frappe.get_traceback(),
			"minvoice_chung_tu: to %s" % ma)
		return (0, rut_gon_loi(e))


# Lý do bỏ qua được coi là HỢP LỆ, không phải hỏng. Tách hẳn ra hằng số vì
# ngày 31/08/2026 lượt chạy tay báo "173 con_hong" trong khi cả 173 tờ đều
# là đầu ra Fabi, tức là không có gì hỏng cả. Con số báo động sai còn nguy
# hơn không báo: nhìn quen rồi thì tới lúc hỏng thật cũng không ai giật mình.
LY_DO_BO_QUA_HOP_LE = ("khoi_dung", "da_co", "dau_ra_fabi")

# Mỗi lượt đóng dấu tối đa bao nhiêu tờ đầu ra. Đóng dấu chỉ là một câu
# UPDATE nên nhẹ hơn dựng chứng từ rất nhiều, cho phép nhiều hơn MOI_LUOT.
DAU_RA_MOI_LUOT = 2000


def _dong_dau_ra(gioi_han=None):
	"""Đóng dấu hàng loạt hoá đơn ĐẦU RA, chúng không cần chứng từ.

	VÌ SAO PHẢI TÁCH RA MỘT ĐƯỜNG RIÊNG (31/08/2026)
	------------------------------------------------
	Đầu ra bán lẻ do Fabi xuất, hệ không dựng chứng từ cho chúng (anh Việt
	chốt 26/08/2026). Nhưng bản trước vẫn thả chúng vào CÙNG hàng đợi với
	đầu vào, mỗi tờ ăn một chỗ trong 200 chỗ của một lượt.

	Ngày 31/08/2026 đếm được 3.907 tờ đầu ra đứng xếp hàng. Với nhịp 200 tờ
	một lượt thì một hoá đơn MUA mới về phải chờ gần hai mươi lượt mới tới
	lượt mình, trong khi việc duy nhất cần làm với 3.907 tờ kia là đặt một
	con số 1 vào một ô.

	Nên: quét chúng bằng một đường riêng, đóng dấu hàng loạt, và hàng đợi
	dựng chứng từ ở dưới chỉ còn ĐẦU VÀO. Hai việc khác hẳn nhau về giá,
	gộp chung một hàng đợi là để việc rẻ chặn đường việc đắt.
	"""
	ds = frappe.get_all(
		DT_HD,
		filters={"da_tao_chung_tu": 0, "loai": LOAI_RA},
		pluck="name",
		limit_page_length=cint(gioi_han) or DAU_RA_MOI_LUOT,
	)
	for ma in ds:
		_ghi_xong(ma, "Hoá đơn đầu ra do Fabi xuất, hệ không dựng chứng từ.")
	if ds:
		frappe.db.commit()
	return len(ds)


def _chay(tu_ngay=None, den_ngay=None, gioi_han=None):
	"""Dựng chứng từ cho các tờ chưa xong. MỘT LƯỢT MỘT LÚC. Trả về số đếm.

	Khoá bọc CẢ lượt chứ không bọc từng tờ. Bọc từng tờ vẫn hở: hai lượt
	đọc hàng đợi cùng lúc thì cả hai đã cầm sẵn cùng một danh sách, khoá
	bên trong chỉ làm chúng dựng nối đuôi nhau chứ không ngăn được tờ thứ
	hai. Phải chặn từ lúc đọc hàng đợi.

	Xin không được khoá thì BỎ LƯỢT chứ không chạy. Bỏ một lượt là mười lăm
	phút sau dựng, không mất gì; chạy chồng là sinh chứng từ trùng, mà gỡ
	chứng từ trùng thì phải có người ngồi dò từng cặp.
	"""
	try:
		pila = ExitStack()
		pila.enter_context(filelock(KHOA_DUNG, timeout=5))
	except LockTimeoutError:
		return {
			"quet": 0, "da_dung": 0, "bo_qua_hop_le": 0, "dau_ra_dong_dau": 0,
			"con_hong": 0, "vi_du_hong": [], "dang_chay_do": 1,
			"tu_ngay": str(tu_ngay or ""), "den_ngay": str(den_ngay or ""),
			"loi_nhan": (
				"Máy đang dựng chứng từ dở từ lượt trước. Anh chị chờ một phút "
				"rồi bấm lại, đừng bấm thêm lần nữa kẻo sinh chứng từ trùng."
			),
		}
	except Exception:
		# Khong lay duoc khoa vi ly do khac thi ghi nhat ky roi chay tiep:
		# khong duoc vi mot cai khoa hong ma ca day chuyen dung lai.
		frappe.log_error(frappe.get_traceback(),
			"minvoice_chung_tu: khong lay duoc khoa dung")
		pila = ExitStack()
	try:
		return _chay_trong_khoa(tu_ngay, den_ngay, gioi_han)
	finally:
		pila.close()


def _chay_trong_khoa(tu_ngay=None, den_ngay=None, gioi_han=None):
	"""Ruột của một lượt dựng. CHỈ gọi từ `_chay`, nơi đã cầm khoá."""
	den_ngay = den_ngay or nowdate()
	# KHÔNG bó hẹp cửa sổ ngày. Bản cũ chỉ ngó 60 ngày gần nhất, tờ cũ hơn
	# thì vĩnh viễn không ai dựng và cũng không ai đếm. Hàng đợi đã xếp theo
	# số lần thử nên tờ hỏng không chiếm chỗ, mở rộng ra là an toàn.
	tu_ngay = tu_ngay or NGAY_BAT_DAU
	dau_ra = _dong_dau_ra()
	ds = frappe.get_all(
		DT_HD,
		filters={
			"ngay_lap": ["between", [tu_ngay, den_ngay]],
			"da_tao_chung_tu": 0,
			# CHỈ ĐẦU VÀO. Xem `_dong_dau_ra` ở trên để biết vì sao đầu ra
			# không được đứng chung hàng đợi này.
			"loai": LOAI_VAO,
		},
		fields=["name", "loai", "so_hd", "ky_hieu", "ngay_lap",
			"nguoi_mua_ban", "mst_doi_tac", "tien_truoc_thue", "tien_thue",
			"tong_tien", "ma_tra_cuu", "chi_tiet", "trang_thai"],
		# Tờ thử nhiều lần xuống cuối, để tờ mới không bao giờ bị tờ hỏng
		# chiếm hết chỗ trong một lượt.
		order_by="so_lan_thu asc, ngay_lap asc, so_hd asc",
		limit_page_length=cint(gioi_han) or MOI_LUOT,
	)
	dung, bo, hong = 0, 0, []
	for r in ds:
		ok, ghi_chu = _mot_to(r)
		if ok:
			dung += 1
		elif ghi_chu in LY_DO_BO_QUA_HOP_LE:
			bo += 1
		else:
			hong.append([r.get("loai"), r.get("so_hd"), ghi_chu])
		frappe.db.commit()
	return {"quet": len(ds), "da_dung": dung, "bo_qua_hop_le": bo,
		"dau_ra_dong_dau": dau_ra,
		"con_hong": len(hong), "vi_du_hong": hong[:8],
		"tu_ngay": str(tu_ngay), "den_ngay": str(den_ngay)}


@frappe.whitelist()
def chay_bu(tu_ngay=None, den_ngay=None, gioi_han=None):
	"""Chạy tay một lượt dựng chứng từ, dùng khi phát hiện sót."""
	_kiem_quyen("dựng chứng từ từ hoá đơn điện tử")
	return _chay(tu_ngay, den_ngay, gioi_han)


def chay_tu_dong():
	"""Điểm gọi của bộ lập lịch. Không ném lỗi ra ngoài.

	PHẢI CÓ TÊN NÀY TRONG `hooks.py`. Xem ca kiểm "nhip tu dong da khai
	trong hooks" ở khung/kiem_thu/thu_minvoice_chung_tu.py để biết vì sao
	có một ca kiểm chỉ để canh đúng một dòng khai báo.
	"""
	try:
		if not frappe.db.exists("DocType", DT_HD):
			return
		_chay()
	except Exception:
		frappe.log_error(frappe.get_traceback(),
			"minvoice_chung_tu: nhip tu dong vo loi")


# ------------------------------------------------- nút bấm tay và chuông báo


@frappe.whitelist()
def dong_bo_ngay(so_ngay=None):
	"""Kéo hoá đơn từ M-Invoice rồi dựng chứng từ, trong MỘT nhịp bấm.

	Đây là ruột của nút "Đồng bộ M-Invoice" trên màn danh sách Desk (anh
	Việt xin 31/08/2026). Trước bản này muốn chạy tay phải mở console gọi
	hai cửa riêng, mà kế toán thì không có đường nào.

	HAI BƯỚC, KHÔNG PHẢI MỘT. Bước kéo đổ hoá đơn từ M-Invoice vào bảng
	trung gian, bước dựng biến chúng thành chứng từ trong sổ. Ngày
	26/08/2026 bước kéo vẫn chạy đều suốt năm ngày trong khi bước dựng đã
	chết, và không ai nhận ra vì trong đầu mọi người "đồng bộ" là một việc.
	Nên ở đây trả về số đếm của CẢ HAI bước, để nhìn một cái là biết bước
	nào đứng.
	"""
	_kiem_quyen("đồng bộ hoá đơn điện tử")
	from vagabond import minvoice_dong_bo

	keo = minvoice_dong_bo._keo(so_ngay=cint(so_ngay) or 0)
	dung_ct = _chay()
	return {
		"ok": 1,
		"keo": keo,
		"dung": dung_ct,
		"loi_nhan": (
			"Kéo về %s tờ mới, lành %s tờ vỏ ruột. Dựng được %s chứng từ, "
			"còn %s tờ hỏng cần soi."
			% (keo.get("moi", 0), keo.get("chua_lanh", 0),
				dung_ct.get("da_dung", 0), dung_ct.get("con_hong", 0))
		),
	}


# Bao nhiêu giờ không dựng được tờ nào thì coi là nhịp đã tắc.
#
# Nhịp dựng chạy 15 phút một lần, nên 6 tiếng là hai mươi tư lượt trượt
# liên tiếp - đủ dài để không kêu oan vì một đêm vắng hoá đơn, đủ ngắn để
# không lặp lại chuyện 26/08.
GIO_COI_LA_TAC = 6


def nhip_da_tac(so_to_cho, gio_ke_tu_lan_dung_cuoi, nguong=GIO_COI_LA_TAC):
	"""Nhịp dựng chứng từ có đang tắc không. THUẦN.

	Tắc = ĐANG có tờ xếp hàng VÀ đã quá lâu không dựng được tờ nào.

	Hai vế phải đi cùng nhau. Chỉ nhìn "lâu rồi không dựng" thì đêm nào
	cũng kêu, vì đêm không ai mua gì. Chỉ nhìn "có tờ xếp hàng" thì lúc
	nào cũng kêu, vì luôn có tờ vừa về chưa tới lượt.
	"""
	try:
		cho = int(so_to_cho or 0)
	except (TypeError, ValueError):
		cho = 0
	try:
		gio = float(gio_ke_tu_lan_dung_cuoi or 0)
	except (TypeError, ValueError):
		gio = 0.0
	return cho > 0 and gio >= float(nguong)


def canh_bao_tac_nhip():
	"""Nhịp ngày: nhịp dựng chứng từ mà tắc thì gửi thư, đừng để im.

	VÌ SAO CÓ HÀM NÀY
	-----------------
	Ngày 26/08/2026 lúc 16h28, kịch bản dựng chứng từ trên site bị tắt, và
	bản thay thế trong mã nguồn thì chưa được khai vào bộ lập lịch. Bước
	kéo vẫn chạy đều nên bảng hoá đơn điện tử vẫn đầy lên mỗi 15 phút,
	nhìn vào đâu cũng thấy "đang chạy".

	NĂM NGÀY sau anh Việt mới phát hiện, và phát hiện bằng cách ngồi so
	tay một tờ của Tác Khí Việt trên trang m-invoice với màn hoá đơn mua
	hàng. 69 tờ hoá đơn mua đứng ngoài sổ suốt thời gian đó.

	Không lớp nào kêu lên, vì không lớp nào có việc kêu. Error Log thì im
	(nhịp có chạy đâu mà lỗi), `con_sot` thì có nhưng phải mở ra mới thấy.

	Hàm này là cái lớp còn thiếu: nó không sửa gì cả, nó chỉ la lên.
	"""
	try:
		if not frappe.db.exists("DocType", DT_HD):
			return
		cho = frappe.db.count(DT_HD, {
			"da_tao_chung_tu": 0, "loai": LOAI_VAO,
			"ngay_lap": ["is", "set"],
		})
		lan_cuoi = frappe.db.get_value(
			PI, {"custom_minvoice_id": ["is", "set"]}, "creation",
			order_by="creation desc")
		gio = 999.0
		if lan_cuoi:
			gio = (
				frappe.utils.now_datetime() - frappe.utils.get_datetime(lan_cuoi)
			).total_seconds() / 3600.0
		# HAI CHUYỆN KHÁC HẲN NHAU, MỘT LÁ THƯ
		#
		# Tắc nhịp là thiếu chứng từ. Trùng là THỪA chứng từ. Ngày 31/08/2026
		# gặp cả hai trong một buổi sáng, và cái thừa nguy hơn: thiếu thì kế
		# toán tự thấy vì hoá đơn không có trong sổ, còn thừa thì nằm im
		# trong danh sách trông y như thật, ghi sổ xong là mua vào đếm hai lần.
		trung = _dem_trung()
		tac = nhip_da_tac(cho, gio)
		if not tac and not cint(trung.get("so_to_thua")):
			return
		phan = []
		if tac:
			phan.append(
				"<p><b>Nhịp dựng chứng từ đang tắc.</b> Đang có <b>%s</b> hoá "
				"đơn điện tử đầu vào xếp hàng mà <b>%s tiếng</b> nay hệ không "
				"dựng thêm được chứng từ nào.</p>"
				"<p>Mở màn Hoá đơn mua hàng trên Desk, bấm nút "
				"<b>Đồng bộ M-Invoice</b>. Vẫn không nhúc nhích thì báo anh "
				"Việt, nhiều khả năng nhịp tự động đã tắt.</p>" % (cho, int(gio))
			)
		if cint(trung.get("so_to_thua")):
			phan.append(
				"<p><b>Có chứng từ trùng.</b> %s tờ hoá đơn điện tử đang có "
				"nhiều hơn một chứng từ trỏ về, thừa <b>%s tờ</b>.</p>"
				"<p>ĐỪNG GHI SỔ khi còn trùng, ghi sổ là mua vào đếm hai lần. "
				"Giữ tờ dựng trước, tick <b>Đã huỷ</b> cho tờ sau. Các tờ đang "
				"trùng: %s.</p>"
				% (
					trung.get("so_nhom"),
					trung.get("so_to_thua"),
					", ".join(
						" và ".join(n.get("ten") or [])
						for n in (trung.get("ds") or [])[:10]
					) or "(xem màn Còn sót)",
				)
			)
		frappe.sendmail(
			recipients=[EMAIL_KE_TOAN],
			subject=(
				"Hoá đơn điện tử: %s"
				% (" và ".join(
					(["nhịp dựng chứng từ đang tắc"] if tac else [])
					+ (["có chứng từ trùng"] if cint(trung.get("so_to_thua")) else [])
				))
			),
			message="".join(phan),
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(),
			"minvoice_chung_tu: chuong bao tac nhip")

"""Phép khớp một dòng sao kê với một phiếu. THUẦN, không chạm Frappe.

Tách riêng khỏi `doi_soat_sepay.py` theo quy tắc 6 của repo: phép thuần phải
chạy được không cần Frappe, không cần site, không cần mạng. Cổng
`kiem_diem_otp.py` bóc thẳng mã nguồn của `hoan_tien.khop_giao_dich` ra chạy
tay, nên chuỗi nhập của nó không được kéo theo `frappe`.

Phần chạm hệ - sổ đăng ký các luồng và ba cửa ngõ - nằm ở `doi_soat_sepay.py`.
Đọc ghi chú dài ở đầu tệp đó để biết vì sao cả hai tệp này ra đời.
"""

import re

# Ba ket qua cua mot phep xet. Chuoi chu khong phai so, de doc log ra la hieu.
KHOP = "khop"
XEM_LAI = "xem_lai"
KHONG = "khong"

# Lech bao nhieu dong thi van coi la dung so tien. Mot dong, khong phai phan
# tram: ngan hang khong lam tron tien Viet.
DUNG_SAI = 1.0


def _so(v):
	"""Doi ve so thuc, hong thi ve 0. THUAN.

	Khong dung `frappe.utils.flt` vi tep nay phai nhap duoc khi khong co
	Frappe.
	"""
	try:
		return float(v or 0)
	except (TypeError, ValueError):
		return 0.0


# --------------------------------------------------------------- lớp 1: chuỗi
#
# Ba hàm THUẦN. Không chạm Frappe, không đọc cơ sở dữ liệu, bộ kiểm thử chạy
# được không cần site.


def got(chu):
	"""Bỏ mọi ký tự không phải chữ hoặc số, rồi viết HOA. THUẦN.

	Vì sao cần: ngân hàng không trả lại nội dung y nguyên. Cùng một lệnh chi,
	sao kê có thể về thành "THE VAGABOND HOAN TIEN HDB 26 08 00323" (mất dấu
	gạch), hoặc đính thêm mã tham chiếu ở hai đầu. So hai chuỗi thô là trượt.

	Đây là bản DUY NHẤT. Bốn bản chép rời trước v294 đều trỏ về đây.
	"""
	return re.sub(r"[^0-9A-Za-z]+", "", str(chu or "")).upper()


def co_ma(mo_ta, ma):
	"""Mã có nằm trong dòng sao kê này không. THUẦN.

	CHẶN CHỮ SỐ CẢ HAI ĐẦU, và đó là điểm khác quan trọng nhất so với mọi bản
	trước v294.

	Vì sao chặn hai đầu chứ không chỉ phía sau
	------------------------------------------
	Mã đơn Pancake chỉ có năm chữ số. Bản cũ `hoan_tien.khop_giao_dich` chỉ
	chặn phía sau, nên dò "92252" sẽ dính nhầm vào một dòng chứa "192252".
	Chính vì cái bẫy đó mà phiếu hoàn Pancake buộc phải dò cả câu, và dò cả
	câu là thứ đã làm phiếu 92245 trượt. Chặn hai đầu gỡ được cả hai chuyện
	trong một nước.

	Vì sao chặn CHỮ SỐ chứ không chặn cả chữ cái
	--------------------------------------------
	Xét trên bản đã gọt, mọi ký tự ngăn cách đã biến mất, nên chữ cái đứng
	sát mã là chuyện bình thường và vô hại: "DH 92245" gọt thành "DH92245",
	trước mã là chữ H. Đòi hai bên phải là ký tự ngăn cách thì không dòng nào
	khớp nữa. Còn chữ số đứng sát thì luôn đáng ngờ, vì nó nghĩa là mã của
	mình chỉ là một khúc của một con số dài hơn.
	"""
	g_ma, g_mo = got(ma), got(mo_ta)
	if not g_ma or not g_mo:
		return False
	vt = g_mo.find(g_ma)
	while vt >= 0:
		truoc = g_mo[vt - 1] if vt > 0 else ""
		sau = g_mo[vt + len(g_ma):vt + len(g_ma) + 1]
		if not truoc.isdigit() and not sau.isdigit():
			return True
		vt = g_mo.find(g_ma, vt + 1)
	return False


def tim_ma(mo_ta, ds_ma):
	"""Trong danh sách mã đang chờ, mã nào khớp dòng sao kê này. THUẦN.

	Trả chuỗi rỗng nếu không mã nào khớp. Mã DÀI hơn được xét trước: nếu một
	dòng mang cả "APP2608027" lẫn "APP26080", thì mã dài mới là mã thật.
	"""
	mo = str(mo_ta or "")
	if not mo:
		return ""
	for x in sorted((str(m or "") for m in (ds_ma or []) if m), key=len, reverse=True):
		if co_ma(mo, x):
			return x
	return ""


# ------------------------------------------------------------- lớp 2: quyết định


def xet(mo_ta, tien_dong, ma_phieu, tien_phieu, chu_cu=None, dung_sai=DUNG_SAI):
	"""Một dòng sao kê có phải của phiếu này không. THUẦN.

	Trả về (kết quả, câu giải thích). Ba kết quả:

	  KHOP     mã khớp, tiền khớp, dòng chưa bị phiếu khác chiếm
	  XEM_LAI  mã khớp nhưng có chuyện người phải nhìn: tiền lệch, hoặc dòng
	           đã có chủ
	  KHONG    mã không khớp, hoặc phiếu không có mã để dò

	Vì sao "mã khớp mà tiền lệch" là XEM_LAI chứ không phải KHONG: đó có thể
	là kế toán chuyển thiếu, ngân hàng trừ phí, hoặc chuyển làm hai lần. Cả
	ba đều là việc của người, và im lặng bỏ qua thì phiếu nằm mãi ở "Chờ chi"
	mà không ai biết vì sao.

	Vì sao "không có mã" là KHONG chứ không phải đoán theo tiền: hai khách
	cùng được hoàn 250.000 đ trong một ngày là chuyện thường. Số tiền một
	mình không bao giờ đủ để máy tự quyết một lần tiền ra.
	"""
	ma = str(ma_phieu or "").strip()
	if not ma:
		return KHONG, "Phiếu này chưa có mã nào để dò trên sao kê."
	if not co_ma(mo_ta, ma):
		return KHONG, ""
	if chu_cu:
		return XEM_LAI, (
			"Dòng sao kê này đã được phiếu %s dùng rồi. Một lần tiền chỉ ứng "
			"với một phiếu." % chu_cu
		)
	lech = _so(tien_dong) - _so(tien_phieu)
	if abs(lech) > _so(dung_sai):
		return XEM_LAI, (
			"Mã khớp nhưng số tiền lệch: sao kê %s đ, phiếu %s đ."
			% (tien_vn(tien_dong), tien_vn(tien_phieu))
		)
	return KHOP, ""


def tien_vn(v):
	"""Số tiền viết theo lối Việt, dấu chấm ngăn nghìn. THUẦN."""
	return "{:,.0f}".format(_so(v)).replace(",", ".")


def xep_ung_vien(dong, ma_phieu, tien_phieu):
	"""Xếp thứ tự ứng viên cho NGƯỜI nhìn. THUẦN.

	Khớp mã lên trước, rồi đúng số tiền, rồi lệch ít nhất. Số tiền chỉ dùng
	để xếp chỗ, không dùng để loại: loại theo tiền chính là cái bẫy của
	`sepay.tim_gd_vao` bản cũ, nó cắt mất đúng dòng mà kế toán cần khi ngân
	hàng trừ phí.

	`dong` là danh sách dict có `mo_ta` và `tien`. Trả về danh sách mới, mỗi
	phần tử được bồi thêm `khop_ma`, `dung_tien`, `lech`.
	"""
	ra = []
	for d in dong or []:
		lech = abs(_so(d.get("tien")) - _so(tien_phieu))
		x = dict(d)
		x["khop_ma"] = 1 if (ma_phieu and co_ma(d.get("mo_ta"), ma_phieu)) else 0
		x["dung_tien"] = 1 if lech <= DUNG_SAI else 0
		x["lech"] = lech
		ra.append(x)
	ra.sort(key=lambda r: (-r["khop_ma"], -r["dung_tien"], r["lech"]))
	return ra



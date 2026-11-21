# -*- coding: utf-8 -*-
"""Gom tin "tiền vào / tiền ra chưa có chứng từ" theo nhóm việc (anh Việt 19/11/2026).

Hai tin 08:00 của nhóm Kế toán (kt_tien_chua_gan, kt_tien_ra_chua_gan) trước đây
liệt kê 10 khoản lớn nhất rồi "+106 khoản khác": kế toán không biết bắt đầu từ
đâu, và cùng một loại việc (tiền Grab về, trừ thẻ Visa) hiện lại mỗi sáng. Anh
Việt chốt 19/11/2026:
- chỉ nhắc khoản từ MOC_NHAC (01/11/2026) trở đi, khoản cũ hơn kế toán bỏ qua;
- tin tiền vào chỉ đếm tài khoản chính của công ty (không đếm quỹ tạm ứng);
- tin gom theo nhóm việc: mỗi nhóm một dòng (bao nhiêu khoản, bao nhiêu tiền,
  làm gì), chỉ nhóm "chưa rõ nguồn" mới liệt kê từng khoản.

Mọi hàm ở đây THUẦN (không chạm Frappe) để kiểm thử không cần site.
"""

import re

MOC_NHAC = "2026-11-01"
TOI_DA_KHOAN_LE = 5

# (khoá, tên nhóm, việc cần làm, mẫu nhận diện trên nội dung sao kê). Thứ tự là
# thứ tự xét: mẫu đứng trước thắng.
NHOM_VAO = (
	("noi_bo", "Chuyển nội bộ giữa tài khoản công ty",
		"Kế toán lập phiếu chuyển tiền nội bộ.",
		re.compile(r"NOI\s*BO|CHUYEN\s*TIEN\s*TU\s*SHINHAN", re.I)),
	("doi_tac", "Tiền đối tác về (Grab, ShopeeFood, OnePay, Xanh SM, beFood, Payoo)",
		"Kế toán lập phiếu thu tiền đối tác, gắn ở Đối chiếu ngân hàng.",
		re.compile(r"GRAB|SHOPEE|AIRPAY|ONEPAY|\bGSM\b|BEFOOD|BE\s*GROUP|PAYOO", re.I)),
	("pancake", "Khách chuyển cho đơn Pancake chưa có bill",
		"Sales tạo bill hoặc gắn ở Đối soát chuyển khoản.",
		re.compile(r"S\d+O\d+T", re.I)),
)
NHOM_RA = (
	("meta_the", "Quảng cáo Meta trừ thẻ Visa MB",
		"Máy gom vào bút toán Meta sau cuối tháng; kế toán ghi sổ ở Đối soát chi phí Meta.",
		re.compile(r"RETAIL\s*VISA.*(FACEBK|FACEBOOK)", re.I)),
	("the", "Trừ thẻ Visa (Meta, phần mềm, phí ngoại tệ)",
		"Kế toán lập phiếu chi hoặc bút toán theo sao kê thẻ.",
		re.compile(r"RETAIL\s*VISA|VISADN|MASTERCARD|\bPOS\b", re.I)),
	("thue", "Nộp thuế, phí nhà nước",
		"Kế toán lập phiếu chi nộp thuế.",
		re.compile(r"\bMTC\s*:|\bCQT\s*:|NOP\s*THUE|THUE\s*CO\s*SO|NSNN", re.I)),
	("ncc", "Trả nhà cung cấp chưa nối phiếu chi",
		"Kế toán mở phiếu chi tương ứng, chọn đúng dòng sao kê.",
		# v680: mã chuẩn chung APP-261201-000099 (ma_chung_tu), có gạch, khoảng trắng hay viết liền.
		re.compile(r"TT\s*HD\s*NCC|\bAPP[\s.\-]*(?:\d{6}[\s.\-]*\d{6}|\d{2}[\s.\-]*\d{2}[\s.\-]*\d{3})", re.I)),
)
KHAC_VAO = ("khac", "Chưa rõ nguồn", "Kế toán xác định từng khoản:")
KHAC_RA = ("khac", "Chưa rõ nội dung", "Kế toán xác định từng khoản:")


def _f(x):
	try:
		return float(x or 0)
	except (TypeError, ValueError):
		return 0.0


def tien(x):
	return "{:,.0f}".format(round(_f(x))).replace(",", ".") + " đ"


def ngay_dm(ngay):
	s = str(ngay or "")[:10]
	return "%s/%s" % (s[8:10], s[5:7]) if len(s) == 10 else s


def rut(s, n=60):
	s = re.sub(r"\s+", " ", str(s or "")).strip()
	return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def tu_moc(ngay, moc=MOC_NHAC):
	"""Khoản có thuộc phạm vi nhắc không: ngày từ mốc trở đi. Ngày rỗng thì không."""
	s = str(ngay or "")[:10]
	return bool(s) and s >= moc


def nhom_cua(mo_ta, bang):
	"""Khoá nhóm của một dòng sao kê theo bảng mẫu; không mẫu nào khớp thì "khac"."""
	s = str(mo_ta or "")
	for khoa, _ten, _viec, mau in bang:
		if mau.search(s):
			return khoa
	return "khac"


def gom(ds, bang, khac, toi_da_le=TOI_DA_KHOAN_LE):
	"""Gom các khoản theo nhóm. ds: [{"tien","ngay","mo_ta"}].

	Trả (dòng tổng, các dòng nhóm). Nhóm xếp theo tiền giảm dần; nhóm "khác"
	luôn đứng cuối và liệt kê từng khoản (lớn trước, tối đa toi_da_le)."""
	nhom = {}
	for g in ds or []:
		nhom.setdefault(nhom_cua(g.get("mo_ta"), bang), []).append(g)
	ten = {k: (t, v) for k, t, v, _m in bang}
	ten[khac[0]] = (khac[1], khac[2])
	ra = []
	thu_tu = sorted([k for k in nhom if k != khac[0]], key=lambda k: -sum(_f(g.get("tien")) for g in nhom[k]))
	for k in thu_tu:
		gs = nhom[k]
		t, viec = ten[k]
		ra.append("%s: %d khoản, %s. %s" % (t, len(gs), tien(sum(_f(g.get("tien")) for g in gs)), viec))
	if khac[0] in nhom:
		gs = sorted(nhom[khac[0]], key=lambda g: (-_f(g.get("tien")), str(g.get("ngay"))))
		t, viec = ten[khac[0]]
		ra.append("%s: %d khoản, %s. %s" % (t, len(gs), tien(sum(_f(g.get("tien")) for g in gs)), viec))
		for g in gs[:toi_da_le]:
			ra.append("  %s: %s, %s" % (ngay_dm(g.get("ngay")), tien(g.get("tien")), rut(g.get("mo_ta"))))
		if len(gs) > toi_da_le:
			ra.append("  +%d khoản khác" % (len(gs) - toi_da_le))
	return ra


def soan_vao(ds, gio=24, moc=MOC_NHAC):
	"""(tiêu đề, các dòng) tin tiền vào chưa gắn chứng từ; rỗng thì None."""
	ds = [g for g in ds or [] if _f(g.get("tien")) > 0]
	if not ds:
		return None
	dong = ["%d khoản, tổng %s, vào tài khoản chính từ %s, quá %d giờ chưa gắn chứng từ" % (
		len(ds), tien(sum(_f(g.get("tien")) for g in ds)), ngay_dm(moc) + "/" + moc[:4], gio)]
	dong += gom(ds, NHOM_VAO, KHAC_VAO)
	return "Tiền vào tài khoản công ty chưa gắn chứng từ", dong


def soan_ra(ds, gio=24, moc=MOC_NHAC):
	"""(tiêu đề, các dòng) tin tiền ra chưa có chứng từ; rỗng thì None."""
	ds = [g for g in ds or [] if _f(g.get("tien")) > 0]
	if not ds:
		return None
	dong = ["%d khoản, tổng %s, ra khỏi tài khoản công ty từ %s, quá %d giờ chưa có chứng từ" % (
		len(ds), tien(sum(_f(g.get("tien")) for g in ds)), ngay_dm(moc) + "/" + moc[:4], gio)]
	dong += gom(ds, NHOM_RA, KHAC_RA)
	return "Tiền ra khỏi tài khoản công ty chưa có chứng từ", dong

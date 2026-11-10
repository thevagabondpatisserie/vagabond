# -*- coding: utf-8 -*-
"""v647 (anh Việt 10/11/2026): sơ đồ bàn theo khu của từng điểm bán. THUẦN.

Tiệm đặt tên bàn theo khu (A1 là bàn số 1 khu A, B1, VIP1) chứ không chỉ
đánh số. Mỗi điểm bán khai một lần: các dòng (khu, từ số, đến số), máy ghép
tên bàn. Màn In QR tại bàn và màn Tính tiền cùng đọc một sơ đồ (anh Việt
chốt "dùng chung").

Luật tên bàn: tên khu (chữ không dấu, tối đa 4 ký tự, có thể trống) + số
1..99, tối đa 6 ký tự. Bàn chỉ có số ("5") là bàn của khu trống, giữ đúng
như trước v647 để QR bàn số đã in vẫn quét được.
"""
import re
import unicodedata

KHU_TOI_DA = 4
SO_TOI_DA = 99
BAN_TOI_DA = 99
DONG_TOI_DA = 12
# Điểm chưa khai sơ đồ: màn Tính tiền hiện Bàn 1 tới 20 như trước v647.
MAC_DINH = [{"khu": "", "tu": 1, "den": 20}]


def bo_dau(s):
	s = str(s or "").replace("đ", "d").replace("Đ", "D")
	return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def chuan_khu(khu):
	"""Tên khu: chữ hoa không dấu, chỉ chữ cái, tối đa 4 ký tự. Trả None khi
	gõ có chữ số hay ký tự lạ mà bỏ đi sẽ đổi nghĩa (ví dụ "A1")."""
	s = re.sub(r"[\s\-_.]", "", bo_dau(khu).upper())
	if not re.fullmatch(r"[A-Z]{0,%d}" % KHU_TOI_DA, s):
		return None
	return s


def chuan_ten_ban(ban):
	"""Tên bàn chuẩn: "A1", "VIP2", "5". Nhận " a01 ", "Bàn A1", 5. Sai thì None."""
	s = bo_dau(ban if ban is not None else "").upper().strip()
	s = re.sub(r"^BAN\s+", "", s)
	# Một dấu cách hay gạch nối CHỈ giữa khu và số ("A 1", "VIP-2"); "-1" sai.
	m = re.fullmatch(r"(?:([A-Z]{1,%d})[ \-_.]?)?0*([0-9]{1,2})" % KHU_TOI_DA, s)
	if not m:
		return None
	n = int(m.group(2))
	if not 1 <= n <= SO_TOI_DA:
		return None
	return "%s%d" % (m.group(1) or "", n)


def la_so(ten):
	"""Bàn chỉ có số (khu trống)."""
	return bool(ten) and str(ten).isdigit()


def _so(x):
	try:
		return int(str(x).strip())
	except (TypeError, ValueError):
		return None


def kiem_so_do(ds):
	"""Chuẩn hoá các dòng người quản lý gõ. Trả (dòng chuẩn, [câu lỗi]).
	Dòng trống hẳn (không khu, không số) bỏ qua; dòng sai ghi lỗi có số dòng."""
	ra, loi, da_co = [], [], {}
	for i, d in enumerate(ds or []):
		d = d or {}
		khu_go = str(d.get("khu") or "").strip()
		tu, den = _so(d.get("tu")), _so(d.get("den"))
		if not khu_go and tu is None and den is None:
			continue
		so_dong = "Dòng %d" % (i + 1)
		khu = chuan_khu(khu_go)
		if khu is None:
			loi.append("%s: tên khu chỉ gồm chữ không dấu, tối đa %d ký tự (ví dụ A, B, VIP)." % (so_dong, KHU_TOI_DA))
			continue
		if tu is None or den is None or not (1 <= tu <= SO_TOI_DA and 1 <= den <= SO_TOI_DA):
			loi.append("%s: số bàn từ 1 tới %d." % (so_dong, SO_TOI_DA))
			continue
		if tu > den:
			tu, den = den, tu
		trung = [n for n in range(tu, den + 1) if (khu, n) in da_co]
		if trung:
			loi.append("%s: bàn %s%d đã có ở dòng %d." % (so_dong, khu, trung[0], da_co[(khu, trung[0])]))
			continue
		for n in range(tu, den + 1):
			da_co[(khu, n)] = i + 1
		ra.append({"khu": khu, "tu": tu, "den": den})
	if len(ra) > DONG_TOI_DA:
		loi.append("Tối đa %d khu một điểm bán." % DONG_TOI_DA)
	if len(da_co) > BAN_TOI_DA:
		loi.append("Tối đa %d bàn một điểm bán, sơ đồ đang có %d bàn." % (BAN_TOI_DA, len(da_co)))
	return ra, loi


def chuan_so_do(ds):
	"""Sơ đồ đã lưu về đúng khuôn, bỏ dòng hỏng (đọc cấu hình cũ, không báo lỗi)."""
	ra, loi = kiem_so_do(ds)
	return [] if loi else ra


def dang_dung(so_do):
	"""Sơ đồ thật đang áp: chưa khai thì mặc định Bàn 1 tới 20."""
	return chuan_so_do(so_do) or [dict(x) for x in MAC_DINH]


def nhom_ban(so_do):
	"""[{"khu", "ban": [tên]}] theo thứ tự đã khai, gộp các dòng cùng khu."""
	ra = []
	for d in dang_dung(so_do):
		g = next((x for x in ra if x["khu"] == d["khu"]), None)
		if not g:
			g = {"khu": d["khu"], "ban": []}
			ra.append(g)
		g["ban"].extend("%s%d" % (d["khu"], n) for n in range(d["tu"], d["den"] + 1))
	return ra


def ten_ban(so_do):
	return [b for g in nhom_ban(so_do) for b in g["ban"]]


def co_ban(so_do, ten):
	"""Link QR của bàn này còn dùng được không. Bàn chỉ có số luôn được (QR
	bàn số in trước v647 vẫn quét được); bàn theo khu phải còn trong sơ đồ,
	đổi tên khu là QR cũ của khu đó hết dùng."""
	t = chuan_ten_ban(ten)
	if t is None:
		return False
	return la_so(t) or t in ten_ban(so_do)


def mat_khi_doi(cu, moi):
	"""Bàn theo khu có trong sơ đồ cũ mà sơ đồ mới không còn: QR đã in của các
	bàn đó sẽ hết dùng, máy báo trước khi lưu."""
	con = set(ten_ban(moi))
	return [t for t in ten_ban(cu) if not la_so(t) and t not in con]


def nhan_in(ten):
	"""Chữ in trên standee: "BÀN A1"."""
	return "BÀN %s" % (chuan_ten_ban(ten) or str(ten or "").upper())


def mo_ta_dong(d):
	"""Một dòng giải thích dưới dòng khai: "A1 đến A12 · 12 bàn"."""
	n = d["den"] - d["tu"] + 1
	a, b = "%s%d" % (d["khu"], d["tu"]), "%s%d" % (d["khu"], d["den"])
	if n == 1:
		return "%s · 1 bàn" % a
	if n == 2:
		return "%s, %s · 2 bàn" % (a, b)
	return "%s đến %s · %d bàn" % (a, b, n)

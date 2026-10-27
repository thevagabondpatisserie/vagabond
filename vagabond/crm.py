"""Phân hệ Khách hàng (CRM) đợt 1, v614.

VÌ SAO CÓ TỆP NÀY
-----------------
Anh Việt 26/10/2026: "giờ mình tới cái phần CRM vì rất quan trọng, chuẩn bị
đến mùa giáng sinh, tết". Site có 44.850 hồ sơ khách, 43.204 khách có số điện
thoại, lịch sử Fabi 39,9 tỷ đồng, nhưng app không có cách chọn đúng nhóm khách
rồi mời họ, và không biết lời mời nào mang về đơn nào.

Bản định hướng (docs/dinh-huong-crm-2026.md, PR #503) qua Codex rà năm điểm,
cả năm điểm đều đúng và đã gom vào đây:

1. Gọi giới thiệu bánh là gọi quảng cáo (Điều 11 Nghị định 91/2020). Chỉ gọi
   và nhắn khách đã ĐỒNG Ý đúng kênh, đã loại số trong Danh sách không quảng
   cáo, và mọi lần đồng ý hay từ chối đều có dòng nhật ký làm bằng chứng.
2. Gửi Zalo OA hàng loạt cần gói OA trả phí, nên đợt 1 chỉ có gọi điện và
   Zalo cá nhân (Sales tự nhắn, máy chỉ soạn sẵn câu).
3. Fabi chỉ để lại SỐ TỔNG (tiền, số đơn, ngày đầu, ngày cuối), không có
   từng món. Lọc theo món chỉ đọc hoá đơn ERP từ 08/2026.
4. Đơn Pancake đã thành hoá đơn ERP mang mã đơn Pancake, nên tiền CHỈ tính
   từ hoá đơn ERP. Số Fabi giữ riêng, không cộng lẫn với số ERP theo kỳ.
5. Nhóm đối chứng chia và khoá cố định NGAY lúc chốt danh sách. Danh sách đã
   chốt không đổi theo nhóm chạy đêm, đo hiệu quả bằng doanh thu bình quân
   mỗi khách, cùng một mốc 14 ngày cho cả hai nhóm.

Màn hình ở bep/58-crm.js, mẫu anh Việt duyệt 27/10/2026 (8 màn).
"""

import json
import random

# ================================================================ phần thuần
#
# Mọi hàm trong phần này KHÔNG chạm Frappe, để bộ kiểm tầng khung chạy được
# không cần site. Phần chạm hệ nằm dưới dòng `import frappe`.

NHOM = ("Trung thành", "Mới", "Sắp rời đi", "Đã ngủ", "Chỉ mua dịp lễ", "Chưa mua")

# Giải thích từng nhóm, hiện ngay dưới chip (skill thiết kế tiện lợi: mỗi lựa
# chọn có một dòng nói nó là gì).
GIAI_THICH_NHOM = {
	"Trung thành": "Mua từ hai lần trở lên và vẫn đang mua đúng nhịp quen của chính họ",
	"Mới": "Mới mua lần đầu trong 90 ngày qua",
	"Sắp rời đi": "Đã quá nhịp mua quen thuộc nhưng chưa quá một năm",
	"Đã ngủ": "Hơn một năm không mua",
	"Chỉ mua dịp lễ": "Ít đơn, lần cuối rơi vào mùa Trung thu hoặc Giáng sinh, Tết",
	"Chưa mua": "Có hồ sơ nhưng chưa có đơn nào trên ERP lẫn Fabi",
}

# Tháng mùa lễ: 8, 9 là Trung thu; 12, 1, 2 là Giáng sinh và Tết.
THANG_LE = {8, 9, 12, 1, 2}

KENH = ("Zalo", "Gọi điện", "Email")
COT_DONG_Y = {"Zalo": "dy_zalo", "Gọi điện": "dy_goi", "Email": "dy_email"}
TT_DONG_Y = ("Chưa hỏi", "Đồng ý", "Từ chối")
NOI_GHI = ("Quầy", "Web", "Sales gọi", "Hồ sơ khách", "Desk")

# Kênh liên hệ của chiến dịch đợt 1. Zalo OA hàng loạt để đợt 2 vì cần gói
# OA trả phí (Codex PR #503).
KENH_CHIEN_DICH = {"goi": "Gọi điện", "zalo": "Zalo"}

# Câu thu ngân đọc khi hỏi khách. Dòng nhật ký lưu NGUYÊN câu đã đọc, vì đó
# là bằng chứng khách biết rõ nội dung và cách thức (Điều 21 NĐ 13/2023).
CAU_HOI_DONG_Y = (
	"Dạ anh/chị có muốn tiệm báo món mới và ưu đãi dịp lễ qua Zalo hoặc gọi điện "
	"không ạ? Anh/chị đổi ý lúc nào cũng được."
)

# Kết quả một lần gọi -> trạng thái của dòng trong danh sách gọi.
KET_QUA = {
	"Quan tâm": "Đã xong",
	"Đã đặt đơn": "Đã xong",
	"Không nghe máy": "Hẹn gọi lại",
	"Hẹn gọi lại": "Hẹn gọi lại",
	"Không muốn nhận tin nữa": "Đã xong",
}
KET_QUA_TU_CHOI = "Không muốn nhận tin nữa"
TT_GOI = ("Chưa gọi", "Hẹn gọi lại", "Đã xong")

CUA_SO_DO = 14  # ngày đo hiệu quả, tính từ lúc chốt danh sách
TY_LE_DOI_CHUNG = 10


def _ngay(s):
	"""'2026-10-27' hoặc date -> date. Rỗng thì None. THUẦN."""
	import datetime as dt

	if not s:
		return None
	if isinstance(s, dt.datetime):
		return s.date()
	if isinstance(s, dt.date):
		return s
	try:
		return dt.date.fromisoformat(str(s)[:10])
	except ValueError:
		return None


def gop_mua(erp, fabi):
	"""Gộp lượt mua ERP và Fabi thành số đơn, ngày đầu, ngày cuối. THUẦN.

	Chỉ gộp SỐ ĐƠN và NGÀY, không gộp tiền: tiền Fabi là tích luỹ trước 08/2026,
	tiền ERP là theo kỳ, cộng lẫn là trộn hai cửa sổ thời gian (Codex PR #503).

	erp, fabi: dict có so_don, lan_dau, lan_cuoi (thiếu thì coi như không mua).
	"""
	erp = erp or {}
	fabi = fabi or {}
	so = int(erp.get("so_don") or 0) + int(fabi.get("so_don") or 0)
	dau = [d for d in (_ngay(erp.get("lan_dau")), _ngay(fabi.get("lan_dau"))) if d]
	cuoi = [d for d in (_ngay(erp.get("lan_cuoi")), _ngay(fabi.get("lan_cuoi"))) if d]
	return {
		"so_don": so,
		"lan_dau": min(dau) if dau else None,
		"lan_cuoi": max(cuoi) if cuoi else None,
	}


def nhip_ngay(so_don, lan_dau, lan_cuoi):
	"""Số ngày trung bình giữa hai lần mua. Một đơn thì chưa có nhịp. THUẦN."""
	d1, d2 = _ngay(lan_dau), _ngay(lan_cuoi)
	if not d1 or not d2 or int(so_don or 0) < 2:
		return 0
	return max(1, int(round((d2 - d1).days / (int(so_don) - 1))))


def xep_nhom(so_don, lan_dau, lan_cuoi, hom_nay):
	"""Xếp một khách vào một trong sáu nhóm. THUẦN.

	Thứ tự xét là thứ tự ưu tiên, khách rơi vào nhóm ĐẦU TIÊN khớp:
	  1. Chưa có ngày mua nào                   -> Chưa mua
	  2. Một đơn, mua trong 90 ngày             -> Mới
	  3. Hai đơn trở lên, chưa quá nhịp quen
	     (lấy số lớn hơn giữa 90 ngày và 1,5 lần nhịp)  -> Trung thành
	  4. Quá 365 ngày                            -> Đã ngủ
	  5. Ba đơn trở xuống, lần cuối rơi vào tháng mùa lễ -> Chỉ mua dịp lễ
	  6. Còn lại                                 -> Sắp rời đi

	Nhóm 5 đoán từ NGÀY CUỐI, vì Fabi không để lại từng lần mua. Đó là giới hạn
	thật của dữ liệu, ghi rõ trong PR, không giả là biết nhiều hơn.
	"""
	hn = _ngay(hom_nay)
	cuoi = _ngay(lan_cuoi)
	so = int(so_don or 0)
	if not cuoi or so <= 0:
		return "Chưa mua"
	cach = (hn - cuoi).days
	if so == 1 and cach <= 90:
		return "Mới"
	nhip = nhip_ngay(so, lan_dau, lan_cuoi)
	if so >= 2 and cach <= max(90, int(nhip * 1.5)):
		return "Trung thành"
	if cach > 365:
		return "Đã ngủ"
	if so <= 3 and cuoi.month in THANG_LE:
		return "Chỉ mua dịp lễ"
	return "Sắp rời đi"


def dip_tu_thang(ds_thang, thang_sinh=None):
	"""Tháng đã mua -> tên dịp. THUẦN.

	    [9, 12] -> ["Trung thu", "Giáng sinh"]
	Tháng sinh nhật của khách nếu trùng một tháng đã mua thì thêm "Sinh nhật".
	"""
	ra = []
	s = set(int(t) for t in (ds_thang or []) if t)
	if s & {8, 9}:
		ra.append("Trung thu")
	if 12 in s:
		ra.append("Giáng sinh")
	if s & {1, 2}:
		ra.append("Tết")
	if thang_sinh and int(thang_sinh) in s:
		ra.append("Sinh nhật")
	return ra


def chuan_dong_y(v):
	"""Giá trị đồng ý của một kênh về đúng ba chữ đã lưu. THUẦN.

	Ô cũ để trống nghĩa là chưa hỏi, KHÔNG phải đồng ý: im lặng không phải là
	đồng ý (Luật Bảo vệ dữ liệu cá nhân 2025).
	"""
	v = (v or "").strip()
	return v if v in TT_DONG_Y else "Chưa hỏi"


def can_hoi(ho_so):
	"""Quầy có nên hỏi khách này không: chưa hỏi đủ cả gọi điện lẫn Zalo. THUẦN.

	Đã đồng ý hay đã từ chối một kênh thì coi như đã hỏi kênh đó. Email không
	tính vì phần lớn khách không để email ở quầy.
	"""
	ho_so = ho_so or {}
	return chuan_dong_y(ho_so.get("dy_goi")) == "Chưa hỏi" and chuan_dong_y(ho_so.get("dy_zalo")) == "Chưa hỏi"


def doi_dong_y(cu, moi):
	"""Kênh nào đổi trạng thái giữa hai bản. THUẦN.

	cu, moi: {"Zalo": "Đồng ý", ...}. Trả danh sách (kênh, trạng thái mới), chỉ
	những kênh thật sự đổi và trạng thái mới là Đồng ý hoặc Từ chối. Không ghi
	dòng nhật ký nào cho kênh không đổi, để sổ đồng ý không đầy dòng trùng.
	"""
	ra = []
	for k in KENH:
		m = chuan_dong_y((moi or {}).get(k))
		if m == "Chưa hỏi":
			continue
		if m != chuan_dong_y((cu or {}).get(k)):
			ra.append((k, m))
	return ra


def kenh_duoc_lien_he(ho_so, kenh_chon):
	"""Những kênh trong kenh_chon mà khách đã đồng ý. THUẦN.

	kenh_chon: danh sách tên kênh ("Gọi điện", "Zalo").
	"""
	ra = []
	for k in kenh_chon or []:
		cot = COT_DONG_Y.get(k)
		if cot and chuan_dong_y((ho_so or {}).get(cot)) == "Đồng ý":
			ra.append(k)
	return ra


def so_doi_chung(n, ty_le):
	"""Số khách giữ làm đối chứng, làm tròn nửa lên. THUẦN.

	Ít hơn 10 khách thì không giữ: nhóm đối chứng một hai người không đo được gì,
	mà lại bớt người được liên hệ.
	"""
	n = int(n or 0)
	t = max(0, min(50, int(ty_le or 0)))
	if n < 10 or not t:
		return 0
	return int(n * t / 100.0 + 0.5)


def chia_doi_chung(ds_khach, ty_le, hat_giong):
	"""Chia ngẫu nhiên nhóm nhận và nhóm đối chứng, lặp lại được. THUẦN.

	Hạt giống là mã chiến dịch, nên chạy lại với cùng danh sách ra đúng cùng
	cách chia: không ai "chọn tay" được người vào đối chứng, và kiểm lại được.
	Danh sách vào được sắp xếp trước để thứ tự đọc từ cơ sở dữ liệu không ảnh
	hưởng kết quả.

	Trả (nhan, doi_chung), cả hai giữ thứ tự sau khi xáo.
	"""
	ds = sorted(set(ds_khach or []))
	r = random.Random(str(hat_giong))
	r.shuffle(ds)
	k = so_doi_chung(len(ds), ty_le)
	return ds[k:], ds[:k]


def chia_sales(ds_nhan, sales):
	"""Chia đều khách cho Sales, lần lượt từng người. THUẦN.

	Danh sách nhận đã xáo ngẫu nhiên nên chia lần lượt là đều cả về số lượng lẫn
	loại khách. Trả dict khách -> người.
	"""
	sales = [s for s in (sales or []) if s]
	if not sales:
		return {}
	return {k: sales[i % len(sales)] for i, k in enumerate(ds_nhan or [])}


def dong_chay(trong_nhom, chua_dong_y, khong_quang_cao, ty_le, so_sales):
	"""Các con số của khung "Ai sẽ được liên hệ". THUẦN."""
	du = max(0, int(trong_nhom or 0) - int(chua_dong_y or 0) - int(khong_quang_cao or 0))
	dc = so_doi_chung(du, ty_le)
	return {
		"trong_nhom": int(trong_nhom or 0),
		"chua_dong_y": int(chua_dong_y or 0),
		"khong_quang_cao": int(khong_quang_cao or 0),
		"du_dieu_kien": du,
		"doi_chung": dc,
		"nhan": du - dc,
		"so_sales": int(so_sales or 0),
	}


def hieu_qua(nhan, doi_chung):
	"""Hiệu quả chiến dịch từ số liệu hai nhóm. THUẦN.

	nhan, doi_chung: dict so_khach, khach_mua, tien.
	So BÌNH QUÂN MỖI KHÁCH, không trừ thẳng hai tổng: nhóm đối chứng chỉ bằng
	một phần chín nhóm nhận, trừ tổng là ra một con số vô nghĩa (Codex PR #503).
	Phần mang về thêm = (bình quân nhận - bình quân đối chứng) x số khách nhận.
	"""
	def _bq(g):
		n = int((g or {}).get("so_khach") or 0)
		tien = float((g or {}).get("tien") or 0)
		mua = int((g or {}).get("khach_mua") or 0)
		return {
			"so_khach": n,
			"khach_mua": mua,
			"tien": tien,
			"ty_le_mua": round(mua * 100.0 / n, 1) if n else 0.0,
			"binh_quan": round(tien / n) if n else 0,
		}

	a, b = _bq(nhan), _bq(doi_chung)
	co_dc = b["so_khach"] > 0
	them = (a["binh_quan"] - b["binh_quan"]) * a["so_khach"] if co_dc else None
	return {"nhan": a, "doi_chung": b, "mang_ve_them": them, "co_doi_chung": co_dc}


def tin_zalo(mau, ten):
	"""Câu Zalo soạn sẵn cho một khách: thay {ten} bằng tên. THUẦN."""
	ten = (ten or "").strip() or "anh/chị"
	return (mau or "").replace("{ten}", ten).strip()


def loc_sach(loc):
	"""Bộ lọc khách về dạng sạch, bỏ khoá lạ. THUẦN.

	Khoá hợp lệ:
	  nhom          danh sách nhóm trong NHOM
	  lan_cuoi_tu   ngày, lần mua cuối từ ngày này
	  lan_cuoi_den  ngày, lần mua cuối tới ngày này
	  chua_mua_ngay số nguyên, đã ít nhất từng này ngày không mua
	  hang          danh sách hạng khách
	  mon           mã món đã mua trên ERP (từ 08/2026)
	  dong_y        danh sách kênh đã đồng ý (khớp MỘT kênh là đủ)
	"""
	if isinstance(loc, str):
		try:
			loc = json.loads(loc or "{}")
		except ValueError:
			loc = {}
	loc = loc if isinstance(loc, dict) else {}
	ra = {}
	nhom = [n for n in (loc.get("nhom") or []) if n in NHOM]
	if nhom:
		ra["nhom"] = nhom
	for k in ("lan_cuoi_tu", "lan_cuoi_den"):
		d = _ngay(loc.get(k))
		if d:
			ra[k] = str(d)
	try:
		n = int(loc.get("chua_mua_ngay") or 0)
	except (TypeError, ValueError):
		n = 0
	if n > 0:
		ra["chua_mua_ngay"] = n
	hang = [str(x).strip() for x in (loc.get("hang") or []) if str(x).strip()]
	if hang:
		ra["hang"] = hang
	mon = str(loc.get("mon") or "").strip()
	if mon:
		ra["mon"] = mon
	dy = [k for k in (loc.get("dong_y") or []) if k in COT_DONG_Y]
	if dy:
		ra["dong_y"] = dy
	return ra


def mo_ta_loc(loc):
	"""Bộ lọc -> một câu tiếng Việt để hiện dưới tên bộ lọc. THUẦN."""
	loc = loc_sach(loc)
	ph = []
	if loc.get("nhom"):
		ph.append("nhóm " + ", ".join(loc["nhom"]))
	tu, den = loc.get("lan_cuoi_tu"), loc.get("lan_cuoi_den")

	def vn(s):
		p = s.split("-")
		return "%s/%s/%s" % (p[2], p[1], p[0])

	if tu and den:
		ph.append("mua lần cuối %s tới %s" % (vn(tu), vn(den)))
	elif tu:
		ph.append("mua lần cuối từ %s" % vn(tu))
	elif den:
		ph.append("mua lần cuối tới %s" % vn(den))
	if loc.get("chua_mua_ngay"):
		ph.append("%d ngày chưa mua" % loc["chua_mua_ngay"])
	if loc.get("hang"):
		ph.append("hạng " + ", ".join(loc["hang"]))
	if loc.get("mon"):
		ph.append("đã mua " + loc["mon"] + " (từ 08/2026)")
	if loc.get("dong_y"):
		ph.append("đã đồng ý " + " hoặc ".join(loc["dong_y"]))
	return "; ".join(ph) if ph else "Tất cả khách"


def dieu_kien_loc(loc, hom_nay):
	"""Bộ lọc -> (mệnh đề where, tham số) trên bảng hồ sơ h nối Customer c. THUẦN.

	Luôn loại giỏ dùng chung (la_gop) và khách đã tắt. Mọi giá trị đi qua tham
	số, không ghép chuỗi người dùng vào câu SQL.
	"""
	import datetime as dt

	loc = loc_sach(loc)
	dk = ["ifnull(h.la_gop, 0) = 0", "ifnull(c.disabled, 0) = 0"]
	ts = []
	if loc.get("nhom"):
		dk.append("h.nhom in (%s)" % ", ".join(["%s"] * len(loc["nhom"])))
		ts.extend(loc["nhom"])
	if loc.get("lan_cuoi_tu"):
		dk.append("h.lan_cuoi >= %s")
		ts.append(loc["lan_cuoi_tu"])
	if loc.get("lan_cuoi_den"):
		dk.append("h.lan_cuoi <= %s")
		ts.append(loc["lan_cuoi_den"])
	if loc.get("chua_mua_ngay"):
		moc = _ngay(hom_nay) - dt.timedelta(days=loc["chua_mua_ngay"])
		dk.append("h.lan_cuoi <= %s")
		ts.append(str(moc))
	if loc.get("hang"):
		dk.append("c.vgb_hang in (%s)" % ", ".join(["%s"] * len(loc["hang"])))
		ts.extend(loc["hang"])
	if loc.get("mon"):
		dk.append(
			"exists (select 1 from `tabSales Invoice Item` i join `tabSales Invoice` s on s.name = i.parent"
			" where s.customer = h.name and s.docstatus = 1 and ifnull(s.vgb_huy, 0) = 0"
			" and ifnull(s.is_return, 0) = 0 and i.item_code = %s)"
		)
		ts.append(loc["mon"])
	if loc.get("dong_y"):
		dk.append("(" + " or ".join("ifnull(h.%s, '') = 'Đồng ý'" % COT_DONG_Y[k] for k in loc["dong_y"]) + ")")
	return " and ".join(dk), ts


def menh_de_dong_y(kenh_chon):
	"""Mệnh đề 'đã đồng ý ít nhất một kênh đã chọn'. THUẦN. Rỗng thì sai."""
	cot = [COT_DONG_Y[k] for k in (kenh_chon or []) if k in COT_DONG_Y]
	if not cot:
		return "1 = 0"
	return "(" + " or ".join("ifnull(h.%s, '') = 'Đồng ý'" % c for c in cot) + ")"


def kenh_cua_chien_dich(cd):
	"""Danh sách kênh đã chọn trên một chiến dịch. THUẦN."""
	ra = []
	if int((cd or {}).get("kenh_goi") or 0):
		ra.append(KENH_CHIEN_DICH["goi"])
	if int((cd or {}).get("kenh_zalo") or 0):
		ra.append(KENH_CHIEN_DICH["zalo"])
	return ra


def ly_do_chua_chot(cd, so_sales):
	"""Câu nói vì sao chưa chốt được chiến dịch, rỗng là chốt được. THUẦN."""
	cd = cd or {}
	if (cd.get("trang_thai") or "Nháp") != "Nháp":
		return "Chiến dịch đã chốt danh sách rồi, danh sách không đổi nữa."
	if not kenh_cua_chien_dich(cd):
		return "Chọn ít nhất một kênh liên hệ (gọi điện hoặc Zalo cá nhân)."
	if not loc_sach(cd.get("loc")):
		return "Chọn nhóm khách hoặc bộ lọc trước khi chốt."
	if not int(cd.get("kich_ban_duyet") or 0):
		return "Kịch bản gọi chưa được duyệt. Nhờ giám đốc duyệt rồi chốt."
	if not int(so_sales or 0):
		return "Thêm ít nhất một Sales nhận danh sách gọi."
	return ""


# ================================================================ phần chạm hệ

import frappe  # noqa: E402
from frappe.utils import cint, flt, now_datetime, nowdate  # noqa: E402

DT_HO_SO = "Vagabond Ho So CRM"
DT_NHAT_KY = "Vagabond Dong Y Nhat Ky"
DT_LIEN_HE = "Vagabond Lien He Khach"
DT_BO_LOC = "Vagabond Bo Loc Khach"
DT_CD = "Vagabond Chien Dich"
DT_CD_KHACH = "Vagabond Chien Dich Khach"

# Ai được dùng phân hệ: Sales, quản lý cửa hàng, Marketing, giám đốc.
CRM_XEM = ("Sales User", "Sales Manager", "System Manager", "VGB - Quản lý cửa hàng", "Marketing")
# Ai được lập và chốt chiến dịch.
CRM_LAP = ("Sales Manager", "System Manager")
# Ai được duyệt kịch bản gọi (anh Việt).
CRM_DUYET = ("System Manager",)
# Ai được đánh dấu số trong Danh sách không quảng cáo.
CRM_KQC = ("Sales Manager", "System Manager", "VGB - Quản lý cửa hàng")


def _co(vai):
	return bool(set(vai) & set(frappe.get_roles()))


def _kiem(vai, viec):
	if not _co(vai):
		frappe.throw("Tài khoản của bạn chưa được %s." % viec)


def _json(v):
	if isinstance(v, (dict, list)):
		return v
	try:
		return json.loads(v or "{}")
	except ValueError:
		return {}


def _ho_so(khach, tao=False):
	"""Hồ sơ CRM của một khách. Chưa có mà tao=True thì dựng dòng trống."""
	d = frappe.db.get_value(DT_HO_SO, khach, "*", as_dict=True)
	if d or not tao:
		return d
	ten = frappe.db.get_value("Customer", khach, "customer_name")
	if ten is None:
		frappe.throw("Không có khách hàng %s." % khach)
	doc = frappe.get_doc({
		"doctype": DT_HO_SO, "khach": khach, "ten_khach": ten,
		"dy_zalo": "Chưa hỏi", "dy_goi": "Chưa hỏi", "dy_email": "Chưa hỏi", "nhom": "Chưa mua",
	})
	doc.insert(ignore_permissions=True)
	return frappe.db.get_value(DT_HO_SO, khach, "*", as_dict=True)


# ---------------------------------------------------------------- đồng ý

@frappe.whitelist()
def dong_y_cua(khach=None):
	"""Trạng thái đồng ý của một khách, cho tấm hỏi ở quầy."""
	_kiem(CRM_XEM, "dùng phân hệ Khách hàng")
	khach = (khach or "").strip()
	from vagabond.khach_hang import la_khach_gop

	if not khach or la_khach_gop(khach):
		# Trả kèm mã khách để quầy nhớ là đã hỏi khách này rồi, không hỏi lại
		# máy chủ mỗi lần vẽ lại giỏ của khách vãng lai.
		return {"co": 0, "khach": khach}
	hs = _ho_so(khach) or {}
	return {
		"co": 1,
		"khach": khach,
		"Zalo": chuan_dong_y(hs.get("dy_zalo")),
		"Gọi điện": chuan_dong_y(hs.get("dy_goi")),
		"Email": chuan_dong_y(hs.get("dy_email")),
		"can_hoi": 1 if can_hoi(hs) else 0,
		"cau_hoi": CAU_HOI_DONG_Y,
	}


@frappe.whitelist()
def ghi_dong_y(khach=None, dat=None, noi_ghi="Quầy", chien_dich=None):
	"""Ghi khách đồng ý hay từ chối từng kênh, kèm dòng nhật ký làm bằng chứng.

	dat: {"Zalo": "Đồng ý"|"Từ chối", "Gọi điện": ..., "Email": ...}. Kênh để
	"Chưa hỏi" thì giữ nguyên, không xoá một lần đồng ý cũ.
	"""
	_kiem(CRM_XEM, "ghi đồng ý nhận tin")
	khach = (khach or "").strip()
	from vagabond.khach_hang import la_khach_gop

	if not khach or la_khach_gop(khach):
		frappe.throw("Chọn đúng một khách có tên trước khi ghi đồng ý nhận tin.")
	if noi_ghi not in NOI_GHI:
		noi_ghi = "Hồ sơ khách"
	dat = _json(dat)
	hs = _ho_so(khach, tao=True)
	cu = {k: hs.get(COT_DONG_Y[k]) for k in KENH}
	doi = doi_dong_y(cu, dat)
	if not doi:
		return {"ok": 1, "doi": 0}
	luc = now_datetime()
	for kenh, tt in doi:
		frappe.get_doc({
			"doctype": DT_NHAT_KY, "khach": khach, "kenh": kenh, "trang_thai": tt,
			"noi_ghi": noi_ghi, "cau_hoi": CAU_HOI_DONG_Y if noi_ghi == "Quầy" else "",
			"nguoi": frappe.session.user, "luc": luc, "chien_dich": chien_dich or None,
		}).insert(ignore_permissions=True)
	moi = {COT_DONG_Y[k]: tt for k, tt in doi}
	moi.update({"dy_luc": luc, "dy_noi": noi_ghi})
	frappe.db.set_value(DT_HO_SO, khach, moi, update_modified=True)
	return {"ok": 1, "doi": len(doi)}


@frappe.whitelist()
def dat_khong_quang_cao(khach=None, bat=1, ghi_chu=""):
	"""Đánh dấu số của khách nằm trong Danh sách không quảng cáo."""
	_kiem(CRM_KQC, "đánh dấu Danh sách không quảng cáo")
	khach = (khach or "").strip()
	_ho_so(khach, tao=True)
	frappe.db.set_value(DT_HO_SO, khach, {
		"khong_quang_cao": 1 if cint(bat) else 0,
		"kqc_ghi_chu": (ghi_chu or "").strip()[:500],
	}, update_modified=True)
	return {"ok": 1}


@frappe.whitelist()
def so_dong_y(kenh="", trang_thai="", so_dong=100):
	"""Sổ đồng ý: tổng theo kênh và các dòng nhật ký mới nhất."""
	_kiem(CRM_XEM, "xem sổ đồng ý nhận tin")
	tong = {}
	for k in KENH:
		cot = COT_DONG_Y[k]
		rows = frappe.db.sql(
			"select ifnull(h.%s, 'Chưa hỏi') tt, count(*) n from `tab%s` h where ifnull(h.la_gop, 0) = 0 group by tt"
			% (cot, DT_HO_SO), as_dict=True)
		tong[k] = {chuan_dong_y(r.tt): cint(r.n) for r in rows}
	loc = {}
	if kenh in KENH:
		loc["kenh"] = kenh
	if trang_thai in ("Đồng ý", "Từ chối"):
		loc["trang_thai"] = trang_thai
	dong = frappe.get_all(
		DT_NHAT_KY, filters=loc,
		fields=["name", "khach", "kenh", "trang_thai", "noi_ghi", "nguoi", "luc", "chien_dich"],
		order_by="luc desc", limit_page_length=min(500, cint(so_dong) or 100))
	ten = _ten_khach([d.khach for d in dong])
	for d in dong:
		d["ten_khach"] = ten.get(d.khach) or d.khach
		d["ten_nguoi"] = _ten_nguoi(d.nguoi)
	kqc = frappe.db.count(DT_HO_SO, {"khong_quang_cao": 1})
	return {"tong": tong, "dong": dong, "khong_quang_cao": kqc}


def _ten_khach(ds):
	ds = list({d for d in ds if d})
	if not ds:
		return {}
	return dict(frappe.db.sql("select name, customer_name from `tabCustomer` where name in %s", (tuple(ds),)))


def _ten_nguoi(u):
	if not u:
		return ""
	return frappe.db.get_value("User", u, "full_name") or u


# ---------------------------------------------------------------- hồ sơ 360

@frappe.whitelist()
def ho_so_crm(khach=None):
	"""Phần CRM của hồ sơ khách: nhóm, đồng ý, món hay mua, dịp, nhật ký."""
	_kiem(CRM_XEM, "dùng phân hệ Khách hàng")
	khach = (khach or "").strip()
	if not khach or not frappe.db.exists("Customer", khach):
		frappe.throw("Không có khách hàng %s." % (khach or "(trống)"))
	hs = _ho_so(khach) or {}
	mon = frappe.db.sql(
		"""
		select i.item_code, max(i.item_name) ten, sum(i.qty) sl, count(distinct s.name) so_don
		from `tabSales Invoice Item` i join `tabSales Invoice` s on s.name = i.parent
		where s.customer = %s and s.docstatus = 1 and ifnull(s.vgb_huy, 0) = 0
		  and ifnull(s.is_return, 0) = 0 and i.item_code != %s
		group by i.item_code order by so_don desc, sl desc limit 6
		""",
		(khach, _ma_phi_giao()), as_dict=True)
	thang = [cint(r[0]) for r in frappe.db.sql(
		"""select distinct month(posting_date) from `tabSales Invoice`
		where customer = %s and docstatus = 1 and ifnull(vgb_huy, 0) = 0""", (khach,))]
	sn = frappe.db.get_value("Customer", khach, "vgb_sinh_nhat") if _co_cot("Customer", "vgb_sinh_nhat") else None
	khac = frappe.db.sql(
		"""
		select sum(docstatus = 0 and ifnull(vgb_huy, 0) = 0) chua_ghi_so,
		       sum(ifnull(vgb_huy, 0) = 1) huy,
		       sum(docstatus = 1 and ifnull(is_return, 0) = 1) tra
		from `tabSales Invoice` where customer = %s
		""", (khach,), as_dict=True)
	khac = (khac or [{}])[0] or {}
	lh = frappe.get_all(
		DT_LIEN_HE, filters={"khach": khach},
		fields=["name", "kenh", "ket_qua", "ghi_chu", "chien_dich", "nguoi", "luc"],
		order_by="luc desc", limit_page_length=20)
	for r in lh:
		r["ten_nguoi"] = _ten_nguoi(r.nguoi)
		r["ten_chien_dich"] = frappe.db.get_value(DT_CD, r.chien_dich, "ten") if r.chien_dich else ""
	return {
		"nhom": hs.get("nhom") or "Chưa mua",
		"giai_thich_nhom": GIAI_THICH_NHOM.get(hs.get("nhom") or "Chưa mua", ""),
		"tinh_luc": str(hs.get("tinh_luc") or ""),
		"nhip_ngay": cint(hs.get("nhip_ngay")),
		"dong_y": {k: chuan_dong_y(hs.get(COT_DONG_Y[k])) for k in KENH},
		"khong_quang_cao": cint(hs.get("khong_quang_cao")),
		"mon": mon,
		"dip": dip_tu_thang(thang, _ngay(sn).month if _ngay(sn) else None),
		"khac": {k: cint(khac.get(k)) for k in ("chua_ghi_so", "huy", "tra")},
		"lien_he": lh,
		"duoc_dat_kqc": 1 if _co(CRM_KQC) else 0,
	}


def _ma_phi_giao():
	from vagabond.ban_hang import MA_PHI_GIAO

	return MA_PHI_GIAO


def _cot_hang():
	"""Cột hạng khách nếu site có, không thì chuỗi rỗng (bench tay không)."""
	return "c.vgb_hang" if _co_cot("Customer", "vgb_hang") else "''"


def _co_cot(dt, cot):
	try:
		return cot in frappe.get_meta(dt).get_valid_columns()
	except Exception:
		return False


@frappe.whitelist()
def ghi_lien_he(khach=None, kenh="Gọi điện", ket_qua="", ghi_chu="", chien_dich=None):
	"""Một dòng nhật ký liên hệ trên hồ sơ khách."""
	_kiem(CRM_XEM, "ghi nhật ký liên hệ")
	khach = (khach or "").strip()
	if not khach or not frappe.db.exists("Customer", khach):
		frappe.throw("Không có khách hàng %s." % (khach or "(trống)"))
	ket_qua = (ket_qua or "").strip()
	ghi_chu = (ghi_chu or "").strip()
	if not ket_qua and not ghi_chu:
		frappe.throw("Ghi kết quả hoặc vài chữ ghi chú cho lần liên hệ này.")
	doc = frappe.get_doc({
		"doctype": DT_LIEN_HE, "khach": khach, "kenh": kenh if kenh in ("Gọi điện", "Zalo", "Email", "Gặp tại quầy", "Khác") else "Khác",
		"ket_qua": ket_qua[:140], "ghi_chu": ghi_chu[:1000], "chien_dich": chien_dich or None,
		"nguoi": frappe.session.user, "luc": now_datetime(),
	}).insert(ignore_permissions=True)
	return {"ok": 1, "name": doc.name}


# ---------------------------------------------------------------- nhóm khách

@frappe.whitelist()
def nhom_khach():
	"""Số khách từng nhóm, kèm số đã đồng ý từng kênh, và bộ lọc đã lưu."""
	_kiem(CRM_XEM, "xem nhóm khách")
	rows = frappe.db.sql(
		"""
		select h.nhom, count(*) n,
		       sum(h.dy_zalo = 'Đồng ý') zalo, sum(h.dy_goi = 'Đồng ý') goi,
		       sum(h.dy_zalo = 'Từ chối' or h.dy_goi = 'Từ chối') tu_choi,
		       sum(h.dy_zalo = 'Đồng ý' or h.dy_goi = 'Đồng ý') it_nhat_mot
		from `tab%s` h join `tabCustomer` c on c.name = h.name
		where ifnull(h.la_gop, 0) = 0 and ifnull(c.disabled, 0) = 0
		group by h.nhom
		""" % DT_HO_SO, as_dict=True)
	theo = {r.nhom: r for r in rows}
	nhom = []
	for n in NHOM:
		r = theo.get(n) or {}
		nhom.append({
			"nhom": n, "giai_thich": GIAI_THICH_NHOM[n], "so": cint(r.get("n")),
			"zalo": cint(r.get("zalo")), "goi": cint(r.get("goi")),
			"tu_choi": cint(r.get("tu_choi")), "it_nhat_mot": cint(r.get("it_nhat_mot")),
		})
	tinh = frappe.db.sql("select max(tinh_luc) from `tab%s`" % DT_HO_SO)
	return {"nhom": nhom, "bo_loc": _ds_bo_loc(), "tinh_luc": str((tinh and tinh[0][0]) or ""),
		"duoc_lap": 1 if _co(CRM_LAP) else 0}


def _ds_bo_loc():
	ra = []
	for r in frappe.get_all(DT_BO_LOC, filters={"an": 0}, fields=["name", "ten", "loc", "owner"], order_by="modified desc"):
		loc = loc_sach(r.loc)
		ra.append({"name": r.name, "ten": r.ten, "loc": loc, "mo_ta": mo_ta_loc(loc), "so": dem_loc(loc)})
	return ra


def dem_loc(loc):
	where, ts = dieu_kien_loc(loc, nowdate())
	r = frappe.db.sql(
		"select count(*) from `tab%s` h join `tabCustomer` c on c.name = h.name where %s" % (DT_HO_SO, where), ts)
	return cint(r[0][0]) if r else 0


@frappe.whitelist()
def ds_khach_loc(loc=None, so_dong=50):
	"""Mẫu danh sách khách khớp một bộ lọc, để xem trước trên màn Nhóm khách."""
	_kiem(CRM_XEM, "xem nhóm khách")
	loc = loc_sach(loc)
	where, ts = dieu_kien_loc(loc, nowdate())
	rows = frappe.db.sql(
		"""
		select h.name khach, c.customer_name ten, c.mobile_no sdt, h.nhom, h.lan_cuoi, h.so_don,
		       h.dy_zalo, h.dy_goi, %s hang
		from `tab%s` h join `tabCustomer` c on c.name = h.name
		where %s order by h.lan_cuoi desc limit %d
		""" % (_cot_hang(), DT_HO_SO, where, min(200, cint(so_dong) or 50)), ts, as_dict=True)
	return {"so": dem_loc(loc), "mo_ta": mo_ta_loc(loc), "dong": rows}


@frappe.whitelist()
def luu_bo_loc(ten=None, loc=None, name=None):
	"""Lưu hoặc sửa một bộ lọc đã đặt tên."""
	_kiem(CRM_XEM, "lưu bộ lọc khách")
	ten = (ten or "").strip()
	if len(ten) < 3:
		frappe.throw("Đặt tên bộ lọc ít nhất 3 chữ, ví dụ: Khách mùa lễ năm ngoái.")
	loc = loc_sach(loc)
	if not loc:
		frappe.throw("Bộ lọc đang trống. Chọn nhóm, khoảng ngày mua hoặc món trước khi lưu.")
	if name and frappe.db.exists(DT_BO_LOC, name):
		frappe.db.set_value(DT_BO_LOC, name, {"ten": ten, "loc": json.dumps(loc, ensure_ascii=False)})
		return {"ok": 1, "name": name}
	doc = frappe.get_doc({"doctype": DT_BO_LOC, "ten": ten, "loc": json.dumps(loc, ensure_ascii=False)})
	doc.insert(ignore_permissions=True)
	return {"ok": 1, "name": doc.name}


@frappe.whitelist()
def an_bo_loc(name=None):
	"""Ẩn một bộ lọc (huỷ mềm, không xoá, QT-20)."""
	_kiem(CRM_XEM, "sửa bộ lọc khách")
	if name and frappe.db.exists(DT_BO_LOC, name):
		frappe.db.set_value(DT_BO_LOC, name, "an", 1)
	return {"ok": 1}


# ---------------------------------------------------------------- chiến dịch

def _luu_cd(doc):
	"""Lưu chiến dịch từ phân hệ: bật cờ để kiem_sua_chien_dich cho qua."""
	frappe.flags.crm_ghi = True
	try:
		doc.save(ignore_permissions=True)
	finally:
		frappe.flags.crm_ghi = False


def kiem_sua_chien_dich(doc):
	"""Chặn sửa tay trên Desk một chiến dịch đã chốt.

	Danh sách đã chốt phải cố định (Codex PR #503): đổi kênh, bộ lọc hay tỉ lệ
	đối chứng sau khi chốt là làm hỏng phép đo. Mọi thay đổi đi qua app.
	"""
	if doc.is_new() or frappe.flags.get("crm_ghi"):
		return
	cu = frappe.db.get_value(DT_CD, doc.name, "trang_thai")
	if cu and cu != "Nháp":
		frappe.throw("Chiến dịch %s đã chốt danh sách nên không sửa trên Desk được. "
			"Mở app, phân hệ Khách hàng, Chiến dịch." % doc.name)


def _cd(name, khoa=False):
	if not name or not frappe.db.exists(DT_CD, name):
		frappe.throw("Không có chiến dịch %s." % (name or "(trống)"))
	return frappe.get_doc(DT_CD, name, for_update=khoa)


def _cd_dict(doc):
	d = doc.as_dict()
	d["loc"] = loc_sach(doc.loc)
	d["mo_ta_loc"] = mo_ta_loc(d["loc"])
	d["kenh"] = kenh_cua_chien_dich(d)
	d["sales"] = [{"nguoi": r.nguoi, "ten": r.ten or _ten_nguoi(r.nguoi)} for r in (doc.get("sales") or [])]
	d["mon"] = [{"item": r.item, "ten": r.ten} for r in (doc.get("mon") or [])]
	return d


@frappe.whitelist()
def ds_chien_dich():
	"""Danh sách chiến dịch, mới nhất trước, kèm tiến độ gọi."""
	_kiem(CRM_XEM, "xem chiến dịch")
	ds = frappe.get_all(DT_CD, fields=["name", "ten", "trang_thai", "ngay_chot", "han", "so_nhan", "so_doi_chung"],
		order_by="creation desc", limit_page_length=100)
	if ds:
		tien = frappe.db.sql(
			"""select chien_dich, trang_thai, count(*) n from `tab%s`
			where chien_dich in %%s and nhanh = 'Nhận' group by chien_dich, trang_thai""" % DT_CD_KHACH,
			(tuple(d.name for d in ds),), as_dict=True)
		for d in ds:
			d["tien_do"] = {r.trang_thai: cint(r.n) for r in tien if r.chien_dich == d.name}
	return {"ds": ds, "duoc_lap": 1 if _co(CRM_LAP) else 0}


@frappe.whitelist()
def doc_chien_dich(name=None):
	"""Một chiến dịch kèm khung "Ai sẽ được liên hệ"."""
	_kiem(CRM_XEM, "xem chiến dịch")
	doc = _cd(name)
	d = _cd_dict(doc)
	d["dong_chay"] = xem_truoc_dict(d) if doc.trang_thai == "Nháp" else {
		"trong_nhom": cint(doc.so_trong_nhom), "chua_dong_y": cint(doc.so_loai_chua_dong_y),
		"khong_quang_cao": cint(doc.so_loai_kqc), "du_dieu_kien": cint(doc.so_nhan) + cint(doc.so_doi_chung),
		"doi_chung": cint(doc.so_doi_chung), "nhan": cint(doc.so_nhan), "so_sales": len(d["sales"]),
	}
	d["ly_do_chua_chot"] = ly_do_chua_chot(d, len(d["sales"])) if doc.trang_thai == "Nháp" else ""
	d["duoc_lap"] = 1 if _co(CRM_LAP) else 0
	d["duoc_duyet"] = 1 if _co(CRM_DUYET) else 0
	return d


def xem_truoc_dict(d):
	"""Đếm khung "Ai sẽ được liên hệ" cho một chiến dịch chưa chốt."""
	loc = loc_sach(d.get("loc"))
	kenh = d.get("kenh") or kenh_cua_chien_dich(d)
	if not loc:
		return dong_chay(0, 0, 0, d.get("ty_le_doi_chung"), len(d.get("sales") or []))
	where, ts = dieu_kien_loc(loc, nowdate())
	dy = menh_de_dong_y(kenh)
	r = frappe.db.sql(
		"""
		select count(*) tong, sum(not %s) chua, sum(%s and ifnull(h.khong_quang_cao, 0) = 1) kqc
		from `tab%s` h join `tabCustomer` c on c.name = h.name where %s
		""" % (dy, dy, DT_HO_SO, where), ts, as_dict=True)
	r = (r or [{}])[0] or {}
	return dong_chay(r.get("tong"), r.get("chua"), r.get("kqc"), d.get("ty_le_doi_chung"), len(d.get("sales") or []))


@frappe.whitelist()
def luu_chien_dich(dat=None):
	"""Tạo hoặc sửa một chiến dịch còn ở trạng thái Nháp."""
	_kiem(CRM_LAP, "lập chiến dịch")
	dat = _json(dat)
	ten = (dat.get("ten") or "").strip()
	if len(ten) < 4:
		frappe.throw("Đặt tên chiến dịch, ví dụ: Giáng sinh 2026 gọi khách mùa lễ cũ.")
	loc = loc_sach(dat.get("loc"))
	if dat.get("name"):
		doc = _cd(dat["name"], khoa=True)
		if doc.trang_thai != "Nháp":
			frappe.throw("Chiến dịch đã chốt danh sách thì không sửa được nữa. Lập chiến dịch mới nếu cần.")
	else:
		doc = frappe.new_doc(DT_CD)
		doc.trang_thai = "Nháp"
	kich_ban_cu = (doc.kich_ban or "").strip()
	doc.ten = ten
	doc.loc = json.dumps(loc, ensure_ascii=False)
	doc.bo_loc = dat.get("bo_loc") or None
	doc.kenh_goi = 1 if cint(dat.get("kenh_goi")) else 0
	doc.kenh_zalo = 1 if cint(dat.get("kenh_zalo")) else 0
	doc.ctkm = dat.get("ctkm") or None
	doc.han = dat.get("han") or None
	doc.kich_ban = (dat.get("kich_ban") or "").strip()
	doc.noi_dung_zalo = (dat.get("noi_dung_zalo") or "").strip()
	doc.ty_le_doi_chung = max(0, min(50, cint(dat.get("ty_le_doi_chung") if dat.get("ty_le_doi_chung") is not None else TY_LE_DOI_CHUNG)))
	# Sửa kịch bản sau khi duyệt thì phải duyệt lại: câu Sales đọc cho khách
	# phải đúng câu giám đốc đã đọc.
	if doc.kich_ban.strip() != kich_ban_cu and cint(doc.kich_ban_duyet):
		doc.kich_ban_duyet = 0
		doc.duyet_boi = None
		doc.duyet_luc = None
	doc.set("mon", [])
	for m in dat.get("mon") or []:
		item = (m.get("item") if isinstance(m, dict) else m) or ""
		if item and frappe.db.exists("Item", item):
			doc.append("mon", {"item": item, "ten": frappe.db.get_value("Item", item, "item_name")})
	doc.set("sales", [])
	for u in dat.get("sales") or []:
		u = (u.get("nguoi") if isinstance(u, dict) else u) or ""
		if u and frappe.db.exists("User", u):
			doc.append("sales", {"nguoi": u, "ten": _ten_nguoi(u)})
	if doc.ctkm:
		doc.ma_uu_dai = frappe.db.get_value("Vagabond CTKM", doc.ctkm, "ma_co_dinh") or ""
	_luu_cd(doc)
	return doc_chien_dich(doc.name)


@frappe.whitelist()
def duyet_kich_ban(name=None):
	"""Giám đốc duyệt kịch bản gọi của một chiến dịch."""
	_kiem(CRM_DUYET, "duyệt kịch bản gọi")
	doc = _cd(name, khoa=True)
	if doc.trang_thai != "Nháp":
		frappe.throw("Chiến dịch đã chốt, kịch bản đã khoá.")
	if len((doc.kich_ban or "").strip()) < 20:
		frappe.throw("Kịch bản gọi còn trống hoặc quá ngắn, chưa duyệt được.")
	doc.kich_ban_duyet = 1
	doc.duyet_boi = frappe.session.user
	doc.duyet_luc = now_datetime()
	_luu_cd(doc)
	return doc_chien_dich(doc.name)


@frappe.whitelist()
def chot_chien_dich(name=None):
	"""Chốt danh sách: chia đối chứng, chia Sales, khoá cố định."""
	_kiem(CRM_LAP, "chốt chiến dịch")
	doc = _cd(name, khoa=True)
	d = _cd_dict(doc)
	ly_do = ly_do_chua_chot(d, len(d["sales"]))
	if ly_do:
		frappe.throw(ly_do)
	loc, kenh = d["loc"], d["kenh"]
	where, ts = dieu_kien_loc(loc, nowdate())
	dy = menh_de_dong_y(kenh)
	tat_ca = frappe.db.sql(
		"""
		select h.name khach, c.customer_name ten, ifnull(h.sdt, c.mobile_no) sdt,
		       h.dy_zalo, h.dy_goi, h.dy_email, ifnull(h.khong_quang_cao, 0) kqc, %s du
		from `tab%s` h join `tabCustomer` c on c.name = h.name where %s
		""" % (dy, DT_HO_SO, where), ts, as_dict=True)
	chua = [r for r in tat_ca if not cint(r.du)]
	kqc = [r for r in tat_ca if cint(r.du) and cint(r.kqc)]
	du = {r.khach: r for r in tat_ca if cint(r.du) and not cint(r.kqc)}
	if not du:
		frappe.throw("Không có khách nào vừa khớp bộ lọc vừa đã đồng ý kênh đã chọn. Chưa chốt được.")
	nhan, dc = chia_doi_chung(list(du), doc.ty_le_doi_chung, doc.name)
	giao = chia_sales(nhan, [s["nguoi"] for s in d["sales"]])
	cot = ["name", "creation", "modified", "modified_by", "owner", "docstatus", "idx",
		"chien_dich", "khach", "ten_khach", "sdt", "nhanh", "sales", "trang_thai", "kenh_duoc", "so_lan"]
	luc = now_datetime()
	nguoi = frappe.session.user
	dong = []
	for k in nhan + dc:
		r = du[k]
		dong.append((
			frappe.generate_hash(length=12), luc, luc, nguoi, nguoi, 0, 0,
			doc.name, k, (r.ten or "")[:140], (r.sdt or "")[:40],
			"Nhận" if k in giao else "Đối chứng", giao.get(k), "Chưa gọi",
			", ".join(kenh_duoc_lien_he(r, kenh)), 0,
		))
	for i in range(0, len(dong), 500):
		frappe.db.bulk_insert(DT_CD_KHACH, cot, dong[i:i + 500])
	doc.trang_thai = "Đang chạy"
	doc.ngay_chot = luc
	doc.chot_boi = nguoi
	doc.so_trong_nhom = len(tat_ca)
	doc.so_loai_chua_dong_y = len(chua)
	doc.so_loai_kqc = len(kqc)
	doc.so_nhan = len(nhan)
	doc.so_doi_chung = len(dc)
	_luu_cd(doc)
	return doc_chien_dich(doc.name)


@frappe.whitelist()
def ket_thuc_chien_dich(name=None):
	"""Đóng chiến dịch: danh sách gọi không còn hiện cho Sales."""
	_kiem(CRM_LAP, "kết thúc chiến dịch")
	doc = _cd(name, khoa=True)
	if doc.trang_thai == "Đang chạy":
		doc.trang_thai = "Đã kết thúc"
		_luu_cd(doc)
	return {"ok": 1}


@frappe.whitelist()
def ds_sales():
	"""Người dùng đang bật có vai Sales, để chọn người nhận danh sách gọi."""
	_kiem(CRM_LAP, "lập chiến dịch")
	ds = frappe.db.sql(
		"""
		select distinct u.name, u.full_name ten from `tabUser` u
		join `tabHas Role` r on r.parent = u.name and r.parenttype = 'User'
		where u.enabled = 1 and u.user_type = 'System User' and r.role in ('Sales User', 'Sales Manager')
		order by u.full_name
		""", as_dict=True)
	for d in ds:
		d["ten"] = d.ten or d.name
	return {"ds": ds}


@frappe.whitelist()
def ds_ctkm_ma():
	"""Chương trình khuyến mãi đang bật, dùng mã cố định: mã riêng của chiến dịch."""
	_kiem(CRM_LAP, "lập chiến dịch")
	ds = frappe.get_all("Vagabond CTKM", filters={"bat": 1, "cach_ma": "Ma co dinh"},
		fields=["name", "ten", "ma_co_dinh", "den_ngay"], order_by="modified desc", limit_page_length=200)
	return {"ds": [{"name": d.name, "ten": d.ten, "ma": d.ma_co_dinh or "", "den_ngay": str(d.den_ngay or "")}
		for d in ds if (d.ma_co_dinh or "").strip()]}


# ---------------------------------------------------------------- danh sách gọi

@frappe.whitelist()
def tong_quan():
	"""Số khách mình còn phải gọi, cho số đỏ trên ô Khách hàng."""
	if not _co(CRM_XEM):
		return {"viec_toi": 0}
	r = frappe.db.sql(
		"""
		select count(*) from `tab%s` k join `tab%s` d on d.name = k.chien_dich
		where k.sales = %%s and k.nhanh = 'Nhận' and k.trang_thai != 'Đã xong' and d.trang_thai = 'Đang chạy'
		""" % (DT_CD_KHACH, DT_CD), (frappe.session.user,))
	return {"viec_toi": cint(r[0][0]) if r else 0}


@frappe.whitelist()
def ds_goi_cua_toi(chien_dich=None):
	"""Khách được chia cho người đang đăng nhập, trong các chiến dịch đang chạy."""
	_kiem(CRM_XEM, "xem danh sách gọi")
	dk = "k.sales = %s and k.nhanh = 'Nhận' and d.trang_thai = 'Đang chạy'"
	ts = [frappe.session.user]
	if chien_dich:
		dk += " and k.chien_dich = %s"
		ts.append(chien_dich)
	rows = frappe.db.sql(
		"""
		select k.name, k.chien_dich, d.ten ten_chien_dich, k.khach, k.ten_khach, k.sdt, k.trang_thai,
		       k.ket_qua, k.ghi_chu, k.lan_cuoi, k.so_lan, k.kenh_duoc, d.noi_dung_zalo, d.kich_ban,
		       h.lan_cuoi mua_cuoi, h.nhom, %s hang
		from `tab%s` k join `tab%s` d on d.name = k.chien_dich
		left join `tab%s` h on h.name = k.khach
		left join `tabCustomer` c on c.name = k.khach
		where %s order by field(k.trang_thai, 'Chưa gọi', 'Hẹn gọi lại', 'Đã xong'), k.ten_khach
		""" % (_cot_hang(), DT_CD_KHACH, DT_CD, DT_HO_SO, dk), ts, as_dict=True)
	for r in rows:
		r["tin_zalo"] = tin_zalo(r.noi_dung_zalo, r.ten_khach)
		r.pop("noi_dung_zalo", None)
	return {"dong": rows, "ket_qua": list(KET_QUA)}


@frappe.whitelist()
def ghi_ket_qua(name=None, ket_qua=None, ghi_chu=""):
	"""Ghi kết quả một lần gọi khách trong danh sách gọi.

	"Không muốn nhận tin nữa" ghi ngay Từ chối cho cả gọi điện lẫn Zalo vào sổ
	đồng ý, để khách bị loại khỏi mọi chiến dịch sau.
	"""
	_kiem(CRM_XEM, "ghi kết quả gọi")
	if ket_qua not in KET_QUA:
		frappe.throw("Chọn một kết quả trong danh sách.")
	if not name or not frappe.db.exists(DT_CD_KHACH, name):
		frappe.throw("Không tìm thấy dòng này trong danh sách gọi.")
	k = frappe.db.get_value(DT_CD_KHACH, name, ["name", "sales", "khach", "chien_dich", "so_lan", "nhanh"],
		as_dict=True, for_update=True)
	if k.nhanh != "Nhận":
		frappe.throw("Khách thuộc nhóm đối chứng, không liên hệ trong chiến dịch này.")
	if k.sales != frappe.session.user and not _co(CRM_LAP):
		frappe.throw("Khách này đã chia cho Sales khác.")
	luc = now_datetime()
	frappe.db.set_value(DT_CD_KHACH, name, {
		"trang_thai": KET_QUA[ket_qua], "ket_qua": ket_qua, "ghi_chu": (ghi_chu or "").strip()[:1000],
		"lan_cuoi": luc, "so_lan": cint(k.so_lan) + 1,
	}, update_modified=True)
	ghi_lien_he(k.khach, "Gọi điện", ket_qua, ghi_chu, k.chien_dich)
	if ket_qua == KET_QUA_TU_CHOI:
		ghi_dong_y(k.khach, {"Zalo": "Từ chối", "Gọi điện": "Từ chối"}, "Sales gọi", k.chien_dich)
	return {"ok": 1, "trang_thai": KET_QUA[ket_qua]}


# ---------------------------------------------------------------- hiệu quả

@frappe.whitelist()
def hieu_qua_chien_dich(name=None):
	"""Doanh thu nhóm được liên hệ so với nhóm đối chứng, 14 ngày từ lúc chốt."""
	_kiem(CRM_XEM, "xem hiệu quả chiến dịch")
	doc = _cd(name)
	if not doc.ngay_chot:
		frappe.throw("Chiến dịch chưa chốt danh sách nên chưa có gì để đo.")
	import datetime as dt

	tu = _ngay(doc.ngay_chot)
	den = tu + dt.timedelta(days=CUA_SO_DO)
	nhanh = {}
	for n in ("Nhận", "Đối chứng"):
		r = frappe.db.sql(
			"""
			select count(distinct k.khach) so_khach,
			       count(distinct s.customer) khach_mua, ifnull(sum(s.grand_total), 0) tien
			from `tab%s` k left join `tabSales Invoice` s on s.customer = k.khach
			     and s.docstatus = 1 and ifnull(s.vgb_huy, 0) = 0 and ifnull(s.is_return, 0) = 0
			     and s.posting_date >= %%s and s.posting_date < %%s
			where k.chien_dich = %%s and k.nhanh = %%s
			""" % DT_CD_KHACH, (str(tu), str(den), doc.name, n), as_dict=True)
		nhanh[n] = (r or [{}])[0] or {}
	kq = hieu_qua(nhanh["Nhận"], nhanh["Đối chứng"])
	ma = 0
	if doc.ctkm:
		r = frappe.db.sql(
			"""select count(distinct u.hoa_don) from `tabVagabond CTKM Su Dung` u
			join `tabSales Invoice` s on s.name = u.hoa_don
			join `tab%s` k on k.khach = s.customer and k.chien_dich = %%s
			where u.ctkm = %%s and ifnull(u.da_tra, 0) = 0 and u.ngay >= %%s and u.ngay < %%s""" % DT_CD_KHACH,
			(doc.name, doc.ctkm, str(tu), str(den)))
		ma = cint(r[0][0]) if r else 0
	tu_choi = frappe.db.count(DT_CD_KHACH, {"chien_dich": doc.name, "ket_qua": KET_QUA_TU_CHOI})
	theo_sales = frappe.db.sql(
		"""
		select k.sales, count(distinct k.khach) so_khach, count(distinct s.name) so_don,
		       count(distinct case when k.trang_thai = 'Đã xong' then k.khach end) da_xong
		from `tab%s` k left join `tabSales Invoice` s on s.customer = k.khach
		     and s.docstatus = 1 and ifnull(s.vgb_huy, 0) = 0 and ifnull(s.is_return, 0) = 0
		     and s.posting_date >= %%s and s.posting_date < %%s
		where k.chien_dich = %%s and k.nhanh = 'Nhận' group by k.sales
		""" % DT_CD_KHACH, (str(tu), str(den), doc.name), as_dict=True)
	for r in theo_sales:
		r["ten"] = _ten_nguoi(r.sales)
	kq.update({
		"ten": doc.ten, "tu": str(tu), "den": str(den - dt.timedelta(days=1)), "ctkm": doc.ctkm or "",
		"ma_uu_dai": doc.ma_uu_dai or "", "don_dung_ma": ma, "khach_tu_choi": tu_choi,
		"theo_sales": theo_sales, "dang_do": 1 if _ngay(nowdate()) < den else 0,
	})
	return kq


# ---------------------------------------------------------------- tính nhóm đêm

def tinh_nhom_dem(luu=True):
	"""Tính lại nhóm cho mọi khách. Lịch 02:30 mỗi đêm.

	Codex hỏi "RFM chạy đêm trên 45.000 khách mà không nặng site": hai câu gom
	(một trên hoá đơn, một trên Customer), xếp nhóm trong Python, rồi ghi theo
	lô 500 dòng bằng INSERT ... ON DUPLICATE KEY UPDATE, commit sau mỗi lô.
	Cột đồng ý và Danh sách không quảng cáo KHÔNG nằm trong phần UPDATE, nên
	lượt đêm không bao giờ ghi đè lời khách đã nói.

	luu=False chỉ dùng cho ca kiểm tích hợp: bench chạy trong điểm lưu và khoá
	commit, nên lượt tính ở đó không được commit.
	"""
	from vagabond.khach_hang import la_khach_gop

	hn = _ngay(nowdate())
	erp = {}
	for r in frappe.db.sql(
		"""
		select customer, count(*) so_don, sum(grand_total) tien, min(posting_date) lan_dau, max(posting_date) lan_cuoi
		from `tabSales Invoice`
		where docstatus = 1 and ifnull(vgb_huy, 0) = 0 and ifnull(is_return, 0) = 0
		group by customer
		""", as_dict=True):
		erp[r.customer] = r
	co = frappe.get_meta("Customer").get_valid_columns()
	cot_fabi = [c for c in ("vgb_so_don_cu", "vgb_chi_tieu_cu", "vgb_lan_dau_cu", "vgb_lan_cuoi_cu") if c in co]
	khach = frappe.db.sql(
		"select name, customer_name, mobile_no%s from `tabCustomer` where ifnull(disabled, 0) = 0"
		% "".join(", " + c for c in cot_fabi), as_dict=True)
	luc = now_datetime()
	cot = ["name", "creation", "modified", "modified_by", "owner", "docstatus", "idx", "khach", "ten_khach", "sdt",
		"nhom", "so_don", "lan_dau", "lan_cuoi", "nhip_ngay", "so_don_erp", "tien_erp", "lan_cuoi_erp",
		"so_don_fabi", "tien_fabi", "lan_cuoi_fabi", "la_gop", "tinh_luc", "dy_zalo", "dy_goi", "dy_email"]
	cap_nhat = [c for c in cot if c not in ("name", "creation", "owner", "docstatus", "idx", "khach", "dy_zalo", "dy_goi", "dy_email")]
	sql_dau = "insert into `tab%s` (%s) values " % (DT_HO_SO, ", ".join("`%s`" % c for c in cot))
	sql_sau = " on duplicate key update " + ", ".join("`%s` = values(`%s`)" % (c, c) for c in cap_nhat)
	lo, dem = [], 0
	from vagabond.lib import sdt as chuan_sdt

	for k in khach:
		e = erp.get(k.name) or {}
		f = {"so_don": k.get("vgb_so_don_cu"), "lan_dau": k.get("vgb_lan_dau_cu"), "lan_cuoi": k.get("vgb_lan_cuoi_cu")}
		g = gop_mua(e, f)
		gop = 1 if la_khach_gop(k.name) else 0
		lo.append((
			k.name, luc, luc, "Administrator", "Administrator", 0, 0, k.name, (k.customer_name or "")[:140],
			chuan_sdt(k.mobile_no) or None,
			xep_nhom(g["so_don"], g["lan_dau"], g["lan_cuoi"], hn), g["so_don"], g["lan_dau"], g["lan_cuoi"],
			nhip_ngay(g["so_don"], g["lan_dau"], g["lan_cuoi"]),
			cint(e.get("so_don")), flt(e.get("tien")), e.get("lan_cuoi"),
			cint(k.get("vgb_so_don_cu")), flt(k.get("vgb_chi_tieu_cu")), k.get("vgb_lan_cuoi_cu") or None,
			gop, luc, "Chưa hỏi", "Chưa hỏi", "Chưa hỏi",
		))
		if len(lo) >= 500:
			_ghi_lo(sql_dau, sql_sau, lo, luu)
			dem += len(lo)
			lo = []
	if lo:
		_ghi_lo(sql_dau, sql_sau, lo, luu)
		dem += len(lo)
	return {"so_khach": dem}


def _ghi_lo(sql_dau, sql_sau, lo, luu=True):
	o = "(" + ", ".join(["%s"] * len(lo[0])) + ")"
	frappe.db.sql(sql_dau + ", ".join([o] * len(lo)) + sql_sau, [v for dong in lo for v in dong])
	if luu:
		frappe.db.commit()


def tinh_nhom_lan_dau():
	"""Gọi từ patch lúc deploy: xếp hàng lượt tính đầu tiên, khỏi chờ tới 02:30."""
	frappe.enqueue("vagabond.crm.tinh_nhom_dem", queue="long", timeout=3000, job_id="crm_tinh_nhom_lan_dau",
		deduplicate=True)

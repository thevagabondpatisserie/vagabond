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
	{
		"ma": "sau_mua",
		"ten": "Cảm ơn sau mua hàng, báo điểm",
		"giai_thich": "Gửi một lần cho mỗi hoá đơn có tích điểm: mã hoá đơn, điểm vừa tích, tổng điểm, hạng.",
		"km": 0,
		"mau": "659376",
		"so_ngay": 0,
		"nhac_lai": 0,
	},
	{
		"ma": "sinh_nhat",
		"ten": "Chúc mừng sinh nhật kèm voucher",
		"giai_thich": "Gửi trước sinh nhật khách số ngày đã đặt, kèm một mã voucher riêng dùng một lần.",
		"km": 1,
		"mau": "659377",
		"so_ngay": 3,
		"nhac_lai": 0,
	},
	{
		"ma": "quay_lai",
		"ten": "Mời khách lâu chưa quay lại",
		"giai_thich": "Khách quá số ngày đã đặt chưa mua thì gửi lời mời kèm một mã voucher riêng.",
		"km": 1,
		"mau": "659378",
		"so_ngay": 60,
		"nhac_lai": 120,
	},
)
MA_KB = tuple(k["ma"] for k in KICH_BAN)

# Mặc định chung khi tạo dòng cấu hình lần đầu.
MAC_DINH = {"tran_ngay": 300, "gio_tu": 8, "gio_den": 20, "han_ngay": 14}

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
}
# Lỗi của cả lượt (không phải của riêng khách): gặp là dừng lượt, để dòng chờ.
# -1 là mã của chính máy (zalo.gui_mau: mất mạng, không lấy được khoá, phản
# hồi không đọc được): loại vĩnh viễn từng dòng thì một lần mất mạng làm mất
# cả hàng đợi, vì khoá chống trùng chặn quét lại (Codex PR #517 vòng 2).
LOI_DUNG_LUOT = {-1, -115, -124, -131, -137, -144, -1441, -146, -147, -133}

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
	"""Khoảng giờ gửi đã kẹp vào 6h tới 22h (luật Zalo). THUẦN.

	Người điền tay có thể gõ 20 rồi 8, hay 0 tới 24: kẹp và đổi chỗ chứ không
	ném lỗi, vì một ô sai không được làm tắt cả kịch bản.
	"""
	a = min(max(so_nguyen(tu, MAC_DINH["gio_tu"]), 6), 22)
	b = min(max(so_nguyen(den, MAC_DINH["gio_den"]), 6), 22)
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


def khoa_tin(ma, khach="", hoa_don="", moc=""):
	"""Khoá duy nhất của một tin trên sổ. THUẦN.

	sau_mua: một hoá đơn một tin. sinh_nhat: một khách một tin mỗi năm (moc là
	năm). quay_lai: một lần vắng mặt một tin (moc là ngày mua cuối).
	"""
	if ma == "sau_mua":
		return "sau_mua:%s" % hoa_don
	return "%s:%s:%s" % (ma, khach, moc)


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
	if k == "NUMBER":
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
	dk = cat(dieu_kien_dat, 40)
	if not dk:
		try:
			tt = float(km.get("hd_toi_thieu") or 0)
		except (TypeError, ValueError):
			tt = 0
		dk = ("Hoá đơn từ " + tien_vn(tt)) if tt > 0 else "Dùng 1 lần cho 1 hoá đơn"
	return cat(ten, 30), cat(dk, 40)


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
	return ma, ("%s (mã %s)" % (cau, ma))[:300]


def dk_tim_tin(tim):
	"""Ô tìm của sổ tin -> điều kiện hoặc cho frappe.get_all. THUẦN.

	Tìm theo tên khách, mã khách, hoá đơn, voucher; chuỗi gần như toàn số thì
	tìm thêm số điện thoại (gõ 09... thì đổi sang 84... như số đã lưu).
	"""
	t = re.sub(r"\s+", " ", str(tim or "")).replace("%", "").strip()
	if not t:
		return []
	g = "%" + t + "%"
	dk = [["ten_khach", "like", g], ["khach", "like", g], ["hoa_don", "like", g], ["voucher", "like", g]]
	so = re.sub(r"\D", "", t)
	if len(so) >= 4 and len(so) >= len(re.sub(r"[\s.\-+]", "", t)) - 1:
		if so.startswith("0") and len(so) >= 9:
			so = "84" + so[1:]
		dk.append(["sdt", "like", "%" + so + "%"])
	return dk


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
	if kb.get("km") and not str(c.get("ctkm") or "").strip():
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
			"gio_tu": MAC_DINH["gio_tu"], "gio_den": MAC_DINH["gio_den"], "han_ngay": MAC_DINH["han_ngay"],
		}).insert(ignore_permissions=True)


COT_KB = ("ma", "ten", "bat", "bat_luc", "ma_mau", "so_ngay", "nhac_lai_ngay", "ctkm", "han_ngay", "ten_uu_dai",
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


def doi_mau_tren_form(doc):
	"""Sửa mã mẫu thẳng trên form Desk cũng xoá kết quả kiểm của mẫu cũ."""
	truoc = doc.get_doc_before_save() if hasattr(doc, "get_doc_before_save") else None
	if truoc is not None and str(truoc.get("ma_mau") or "") != str(doc.get("ma_mau") or ""):
		dat = doc.__setitem__ if isinstance(doc, dict) else doc.set
		for k, x in xoa_kiem_mau().items():
			dat(k, x)


def _ho_so(khach):
	"""Thông tin khách cần để gửi: tên, số Zalo, đồng ý, điểm, hạng."""
	from vagabond.lib import sdt84

	cu = frappe.db.get_value("Customer", khach, ["customer_name", "mobile_no", "vgb_diem", "vgb_hang"], as_dict=True) or {}
	hs = frappe.db.get_value("Vagabond Ho So CRM", khach, ["sdt", "dy_zalo", "khong_quang_cao"], as_dict=True) or {}
	return {
		"ten": ten_goi(cu.get("customer_name") or khach),
		"sdt84": sdt84(hs.get("sdt") or cu.get("mobile_no") or ""),
		"dong_y": (hs.get("dy_zalo") or "") == "Đồng ý" and not int(hs.get("khong_quang_cao") or 0),
		"diem": cu.get("vgb_diem") or 0,
		"hang": cu.get("vgb_hang") or "",
	}


def _da_gui_hom_nay(ma):
	luc = _bay_gio()
	return frappe.db.count(DT_TIN, {"kich_ban": ma, "trang_thai": TT_GUI, "luc_gui": [">=", luc.replace(hour=0, minute=0, second=0, microsecond=0)]})


def _ghi_cho(ma, khoa, khach, hoa_don=None, diem=0):
	"""Ghi một dòng Chờ gửi. Khoá đã có thì thôi (chống trùng tầng sổ)."""
	if frappe.db.exists(DT_TIN, {"khoa": khoa}):
		return False
	frappe.get_doc({"doctype": DT_TIN, "kich_ban": ma, "khoa": khoa, "khach": khach, "hoa_don": hoa_don,
		"diem": diem, "trang_thai": TT_CHO}).insert(ignore_permissions=True)
	return True


def quet_sau_mua():
	"""Mỗi lượt cộng điểm từ hoá đơn sau lúc bật kịch bản -> một dòng chờ."""
	c = _cau_hinh("sau_mua") or {}
	if not int(c.get("bat") or 0):
		return 0
	luc = _bay_gio()
	tu = luc - timedelta(hours=CHO_TOI_DA_GIO)
	bat_luc = c.get("bat_luc")
	if bat_luc and get_datetime(bat_luc) > tu:
		tu = get_datetime(bat_luc)
	rows = frappe.db.sql(
		"""select d.khach, d.diem, d.hoa_don from `tabVagabond So Diem` d
		where d.loai = 'Tich tu hoa don' and d.diem > 0 and ifnull(d.hoa_don, '') != '' and d.creation >= %s
		and not exists (select 1 from `tabVagabond Tin Zalo Khach` t where t.khoa = concat('sau_mua:', d.hoa_don))
		order by d.creation limit 1000""", (tu,), as_dict=True)
	n = 0
	for r in rows:
		n += 1 if _ghi_cho("sau_mua", khoa_tin("sau_mua", hoa_don=r.hoa_don), r.khach, r.hoa_don, r.diem) else 0
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


def quet_quay_lai(hom_nay):
	"""Khách đã đồng ý Zalo vừa vắng mặt đủ `so_ngay` -> dòng chờ, trừ khách
	đã nhận tin mời quay lại trong `nhac_lai_ngay` ngày."""
	c = _cau_hinh("quay_lai") or {}
	if not int(c.get("bat") or 0):
		return 0
	n_ngay = so_nguyen(c.get("so_ngay"), 60)
	if n_ngay <= 0:
		return 0
	nhac = so_nguyen(c.get("nhac_lai_ngay"), 120)
	rows = frappe.db.sql(
		"""select h.name khach, h.lan_cuoi from `tabVagabond Ho So CRM` h
		where h.lan_cuoi between %s and %s
		and ifnull(h.dy_zalo, '') = 'Đồng ý' and ifnull(h.khong_quang_cao, 0) = 0
		and not exists (select 1 from `tabVagabond Tin Zalo Khach` t where t.khach = h.name
			and t.kich_ban = 'quay_lai' and t.trang_thai = 'Đã gửi' and t.luc_gui >= %s)""",
		(hom_nay - timedelta(days=n_ngay + 2), hom_nay - timedelta(days=n_ngay), hom_nay - timedelta(days=nhac)),
		as_dict=True)
	n = 0
	for r in rows:
		if not vang_mat_du(r.lan_cuoi, hom_nay, n_ngay):
			continue
		n += 1 if _ghi_cho("quay_lai", khoa_tin("quay_lai", r.khach, moc=ngay_cua(r.lan_cuoi)), r.khach) else 0
	return n


def _gia_tri_sau_mua(row, kh):
	si = frappe.db.get_value("Sales Invoice", row.get("hoa_don"), ["docstatus", "posting_date", "posting_time", "grand_total"], as_dict=True)
	if not si or int(si.docstatus or 0) != 1:
		return None, "Hoá đơn đã huỷ hoặc không còn."
	gio = str(si.posting_time or "")[:5]
	return {
		"ten_khach": kh["ten"], "ma_hoa_don": row.get("hoa_don"),
		"ngay_mua": (ngay_vn(si.posting_date) + (" " + gio if gio else "")).strip(),
		"tong_tien": tien_vn(si.grand_total), "diem_tich": so_dep(row.get("diem")),
		"tong_diem": so_dep(kh["diem"]), "hang": kh["hang"] or "Thành viên",
	}, ""


COT_CTKM = ["name", "ten", "cach_ma", "bat", "kieu_giam", "gia_tri", "hd_toi_thieu", "tu_ngay", "den_ngay", "han_ma"]


def _doc_ctkm(ten):
	if not ten:
		return None
	return frappe.db.get_value("Vagabond CTKM", ten, COT_CTKM, as_dict=True)


def _phat_voucher(c, kh, khach, ma_kb):
	"""Một mã dùng một lần cho đúng khách, hạn theo số ngày đã đặt.
	Trả (mã, hạn, câu lỗi)."""
	km = _doc_ctkm(c.get("ctkm"))
	han, loi = ctkm_phat_duoc(km, _bay_gio().date(), c.get("han_ngay"))
	if not han:
		return None, None, loi
	ma = _sinh_ma()
	frappe.get_doc({"doctype": "Vagabond Voucher", "ma": ma, "ctkm": km.name, "ten_ctkm": cat(km.ten, 140),
		"trang_thai": "Chua dung", "han_dung": han, "khach": cat(kh["ten"], 140), "sdt": kh["sdt84"], "danh_cho": khach,
		"gui_cho": cat("Tin Zalo: " + (kich_ban(ma_kb) or {}).get("ten", ""), 140)}).insert(ignore_permissions=True)
	return ma, han, ""


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
	if kb["km"]:
		# Đọc lại đồng ý NGAY TRƯỚC khi gửi: khách rút đồng ý sau lúc quét thì thôi.
		if not kh["dong_y"]:
			_xong(row.name, TT_BO, "Khách không còn đồng ý nhận tin Zalo.")
			return None
		ma_v, han, loi = _phat_voucher(c, kh, row.khach, ma_kb)
		if loi:
			_xong(row.name, TT_LOI, loi)
			return None
		km = _doc_ctkm(c.get("ctkm")) or {}
		ten_ud, dk = mo_ta_uu_dai(km, c.get("ten_uu_dai"), c.get("dieu_kien"))
		gt = {"ten_khach": kh["ten"], "ten_uu_dai": ten_ud, "dieu_kien": dk, "han_dung": ngay_vn(han), "ma_voucher": ma_v}
	else:
		gt, loi = _gia_tri_sau_mua(row, kh)
		if loi:
			_xong(row.name, TT_BO, loi)
			return None
	data, thieu = du_lieu_mau(gt, doc_tham_so(c.get("mau_tham_so")))
	if thieu:
		_huy_voucher(ma_v, "mẫu đòi tham số máy không có")
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
	_huy_voucher(ma_v, cau)
	if ma in LOI_DUNG_LUOT:
		# Lỗi của cả lượt: để dòng chờ cho lượt sau, ghi lý do để màn hiện.
		frappe.db.set_value(DT_TIN, row.name, {"loi": cau}, update_modified=False)
		frappe.db.commit()
		return ma
	_xong(row.name, TT_LOI, cau, sdt=kh["sdt84"], ten_khach=cat(kh["ten"], 140), ma_mau=c["ma_mau"])
	return None


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
		if kb["km"]:
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
			fields=["name", "khach", "hoa_don", "diem", "khoa"], order_by="creation asc", limit_page_length=con)
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
	try:
		quet_sau_mua()
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="Vagabond: tin Zalo tự động, quét sau mua", message=frappe.get_traceback())
	for ma, ham in (("sinh_nhat", quet_sinh_nhat), ("quay_lai", quet_quay_lai)):
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


# ================================================================ màn hình

DUOC_SUA = ("bat", "ma_mau", "so_ngay", "nhac_lai_ngay", "ctkm", "han_ngay", "ten_uu_dai", "dieu_kien", "tran_ngay", "gio_tu", "gio_den")


def _quyen(xem=True):
	from vagabond import crm

	crm._kiem(crm.CRM_XEM if xem else crm.CRM_LAP, "xem tin Zalo tự động" if xem else "sửa tin Zalo tự động")


def _the(c, dem, hom_nay=None):
	kb = kich_ban(c["ma"]) or {}
	duoc, ly_do = mau_san_sang(c)
	if duoc and kb.get("km") and hom_nay:
		# Thẻ nói luôn khi chương trình đã chọn hết hạn: máy sẽ giữ tin chờ.
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
		ctkm.append({"name": km.get("name"), "ten": km.get("ten") or km.get("name"), "phu": phu})
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
		elif k == "ctkm":
			x = str(x or "").strip()
			if x and not frappe.db.exists("Vagabond CTKM", x):
				frappe.throw("Không có chương trình khuyến mãi này.")
			v[k] = x or None
		elif k == "ten_uu_dai":
			v[k] = cat(x, 30)
		elif k == "dieu_kien":
			v[k] = cat(x, 40)
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


@frappe.whitelist()
def ds_tin(ma=None, trang_thai="", bat_dau=0, tim=""):
	"""Các tin gần nhất của một kịch bản, mới nhất trước, mỗi trang 50.
	Có ô tìm thì tìm ở máy chủ, ra cả dòng chưa tải (Codex PR #517 vòng 2)."""
	_quyen()
	loc = {"kich_ban": ma} if ma in MA_KB else {}
	if trang_thai in TT_TIN:
		loc["trang_thai"] = trang_thai
	them = {}
	dk = dk_tim_tin(tim)
	if dk:
		them["or_filters"] = dk
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
	return {"ds": ds, "con_nua": 1 if len(rows) > 50 else 0}


MAU_THU = {
	"ten_khach": "Khách thử", "ma_hoa_don": "HDB-THU-0001", "ngay_mua": "29/10/2026 15:30", "tong_tien": "450.000đ",
	"diem_tich": "9.000", "tong_diem": "25.400", "hang": "EXPLORER", "ten_uu_dai": "Giảm 10%",
	"dieu_kien": "Dùng 1 lần cho 1 hoá đơn", "han_dung": "30/11/2026", "ma_voucher": "THUTHU",
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

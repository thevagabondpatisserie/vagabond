# -*- coding: utf-8 -*-
"""Việc hôm nay (Bảng sáng): máy đọc số bán và số kho, nháp sẵn việc để giao.

Vì sao có tệp này
-----------------
Anh Việt 21/09/2026: *"Anh thường bị stuck mỗi ngày không biết nên giao việc
gì cho các bộ phận vì anh cũng là SME, tự quản hết tất cả các bộ phận nên bị
overload"*, và muốn phân hệ Báo cáo biến số liệu khô thành gợi ý như trợ lý
của Fabi.

Tiệm không thiếu báo cáo: `bao_cao.py` đã có 16 cái trả đúng số. Thiếu là ba
tầng phía trên con số: NHẬN ĐỊNH (số này tốt hay xấu), GỢI Ý (nên làm gì) và
GIAO VIỆC (ai làm, hạn nào, làm chưa). Tệp này lo cả ba cho đợt 1 của issue
#351, đúng phạm vi anh Việt duyệt sau góp ý của Codex:

  - Bốn luật: món đang lên, món giảm hai tuần liền (chỉ là "cần kiểm tra"),
    lô quá hạn và cận hạn theo từng kho, món bán chạy mà bảng kiểm bánh ngày
    mai còn ít hơn mức bán một ngày. Cộng một lớp "độ tin cậy số liệu" để
    máy nói thẳng khi số chưa đủ hay chưa mới, thay vì suy diễn.
  - Không mô hình ngôn ngữ. Mọi câu chữ ở đây là câu mẫu điền số.
  - Không tự tạo chứng từ nghiệp vụ, không tự khuyến mãi, không nhắn khách.

Ba quyết định thiết kế, và vì sao
---------------------------------
1. SỐ DO MÁY TÍNH MỘT LẦN LÚC 7 GIỜ, MÀN CHỈ ĐỌC. Tính bảng sáng phải đọc ba
   tuần hoá đơn cùng mọi lô sắp hết hạn. Để mỗi lần mở màn quét lại thì người
   mở phải chờ, và hai người mở cùng lúc là hai lượt quét. Nên nhịp 7 giờ dựng
   sẵn rồi cất vào bộ nhớ đệm; mở màn mà chưa có bản của hôm nay (vừa deploy,
   bộ nhớ đệm bị xoá) thì xếp MỘT lượt dựng chạy nền, màn nói đang dựng chứ
   không đứng chờ.
2. VIỆC ĐƯỢC GIAO LÀ MỘT TASK LÕI CỦA ERPNEXT, GIAO BẰNG TODO. Không đẻ
   doctype riêng. Task có sẵn trạng thái, hạn, người hoàn thành, và khi Task
   chuyển sang Completed thì chính ERPNext đóng mọi ToDo của nó
   (`erpnext/projects/doctype/task/task.py`, hàm `unassign_todo`:
   `if self.status == "Completed": close_all_assignments(...)`). Nhờ vậy
   bản Desk thấy đúng cùng một việc ở danh sách Task và ô Assigned To.
3. KHOÁ CHỐNG TRÙNG THEO VẤN ĐỀ, KHÔNG THEO NGÀY. Khoá là luật + đối tượng +
   phạm vi, ví dụ `lo_qua_han|Kho tổng 307 - TV|`. Một vấn đề tồn năm ngày
   vẫn chỉ ra một việc; hai quản lý cùng bấm Giao một lúc cũng chỉ ra một việc
   (khoá tên của cơ sở dữ liệu, cùng cách `ton_chang.tao_phieu_ve_dung_kho`).

Phép THUẦN ở trên, phần chạm Frappe ở dưới, để bộ kiểm chạy được không cần
site (vagabond/khung/kiem_thu/thu_bang_sang_351.py).
"""

import datetime
import json

# phần thuần
# Codex #356 (AGENTS.md mục "Tách phần thuần và phần cần Frappe"): phần trên
# dòng `import frappe` phải chạy được khi KHÔNG có Frappe, để bộ kiểm tầng
# khung nạp riêng nó. Nên ba phép đổi kiểu dưới đây viết thuần, không lấy của
# frappe.utils, và hằng vai lấy từ vai_cua_hang khi có, rơi về bản chép khi
# không có Frappe (ca kiểm chốt hai bản trùng nhau).
try:
	from vagabond.vai_cua_hang import VAI_MARKETING, VAI_QLCH
except ImportError:
	VAI_MARKETING, VAI_QLCH = "Marketing", "VGB - Quản lý cửa hàng"


def flt(v):
	"""Số thực, hỏng thì 0. THUẦN (thay frappe.utils.flt cho phần thuần)."""
	if v is None or v == "":
		return 0.0
	try:
		return float(str(v).replace(",", "")) if isinstance(v, str) else float(v)
	except (TypeError, ValueError):
		return 0.0


def cint(v):
	"""Số nguyên cắt phần lẻ, hỏng thì 0. THUẦN."""
	return int(flt(v))


def getdate(v=None):
	"""Ngày từ date, datetime hoặc chuỗi 'YYYY-MM-DD[ ...]'. Trống thì hôm nay. THUẦN."""
	if v is None or v == "":
		return datetime.date.today()
	if isinstance(v, datetime.datetime):
		return v.date()
	if isinstance(v, datetime.date):
		return v
	return datetime.datetime.strptime(str(v).strip()[:10], "%Y-%m-%d").date()

# Đổi số này mỗi khi đổi cách một luật tính. Việc đã giao lưu kèm số này để
# sau này tra ngược được việc đó sinh ra từ luật phiên bản nào.
PHIEN_BAN_LUAT = "351.1"

# Ngưỡng THỬ, anh Việt chốt lại sau khi thấy ví dụ thật (Codex #351 mục 2).
# Mỗi luật xu hướng cần đủ ba thứ cùng lúc: đủ mẫu, đủ chênh tuyệt đối, đủ
# chênh tương đối. Thiếu một là từ 1 lên 2 cũng thành "tăng 100%".
NGUONG = {
	"san_mau": 12,             # tuần gốc phải bán ít nhất ngần này
	"tang_tuyet_doi": 8,
	"tang_ty_le": 0.30,
	"top_tang": 20,            # chỉ xét món đang nằm trong 20 món bán nhiều nhất
	"giam_tuyet_doi": 8,
	"giam_ty_le": 0.30,        # tổng giảm qua hai tuần so với tuần gốc
	"ban_tb_toi_thieu": 2.0,   # bán trung bình mỗi ngày tại quầy
	"thieu_toi_thieu": 2,      # thiếu ít nhất ngần này cái mới báo
	"ngay_can_han": 7,
	"ty_le_nhap": 0.20,        # đơn chưa ghi sổ quá tỷ lệ này thì nhắc số tạm tính
	"hd_toi_thieu_tuan": 30,   # tuần gốc ít hơn ngần này hoá đơn là chưa đủ lịch sử
	"gio_dong_bo_cu": 3,       # đơn Pancake đồng bộ lần cuối quá ngần này giờ là cũ
}

# Mã món bán: bánh (BA...) và đồ uống (NU...). Phụ kiện (BAPK: dĩa, nĩa,
# thiệp) và dịch vụ (DV: phí giao, logo) nằm trong hoá đơn nhưng không phải
# món, để chúng vào là "Dĩa giấy bã mía đang lên" đứng đầu bảng.
TIEN_TO_MON = ("BA", "NU")
TIEN_TO_LOAI_TRU = ("BAPK",)
# Hàng theo mùa (hộp Trung thu...): hết mùa thì giảm là đúng quy luật, không
# phải việc cần kiểm tra.
TIEN_TO_MUA_VU = ("BASS",)

# Điểm bán không có quầy (đơn Sales Online, vgb_quay để trống). Bán ở đây là
# đơn đặt trước, đã nằm trong cột "đã đặt" của bảng kiểm bánh.
DIEM_KHONG_QUAY = "SALES"

VAI_GIAM_DOC = {"System Manager", "AP Giám đốc", "Giám đốc"}

BO_PHAN = (
	("marketing", "Marketing", "📣"),
	("bep", "Bếp", "🧑‍🍳"),
	("kho", "Kho", "📦"),
	("sales", "Sales", "🛒"),
)
TEN_BO_PHAN = {k: t for k, t, _ in BO_PHAN}
ICON_BO_PHAN = {k: i for k, _, i in BO_PHAN}

# Ai THẤY nhận định của bộ phận nào (ngoài giám đốc thấy hết). Người thấy thì
# được giao, vì giao là việc của người quản bộ phận đó.
XEM_BO_PHAN = {
	"marketing": {VAI_MARKETING, "Sales Manager", VAI_QLCH},
	"sales": {"Sales Manager", VAI_QLCH},
	"bep": {"Bếp trưởng", "Manufacturing Manager", VAI_QLCH},
	"kho": {"Stock Manager", "Manufacturing Manager"},
}
# Ai được máy GỢI Ý làm người nhận. Chỉ là gợi ý đầu danh sách; người giao
# vẫn tìm được mọi tài khoản đang bật.
NHAN_BO_PHAN = {
	"marketing": {VAI_MARKETING},
	"sales": {"Bộ phận đặt hàng", "Sales Manager"},
	"bep": {"Bếp trưởng", "Bếp phó", "Manufacturing Manager"},
	"kho": {"Stock Manager"},
}
QUYEN_BANG_SANG = set(VAI_GIAM_DOC)
for _v in XEM_BO_PHAN.values():
	QUYEN_BANG_SANG |= _v
del _v

MUC = {"cao": 3, "vua": 2, "thap": 1}

# Mỗi luật: tên, mức, bộ phận, hạn gợi ý (ngày), số ngày ẩn sau khi xong, và
# số ngày TỐI ĐA được bỏ qua. Lô quá hạn chỉ cho bỏ qua 3 ngày: Codex #351
# dặn không để cảnh báo quá hạn chìm vì bị bỏ qua nhiều lần.
LUAT = {
	"lo_qua_han": {"ten": "Lô đã quá hạn", "muc": "cao", "bo_phan": ["kho"], "han": 0, "an_sau_xong": 1, "bo_qua_toi_da": 3},
	"thieu_thanh_pham": {"ten": "Có thể thiếu bánh", "muc": "cao", "bo_phan": ["bep", "sales"], "han": 0, "an_sau_xong": 1, "bo_qua_toi_da": 3},
	"mon_giam": {"ten": "Món giảm hai tuần liền", "muc": "vua", "bo_phan": ["marketing", "bep"], "han": 3, "an_sau_xong": 7, "bo_qua_toi_da": 14},
	"lo_can_han": {"ten": "Lô sắp hết hạn", "muc": "vua", "bo_phan": ["kho", "bep"], "han": 1, "an_sau_xong": 3, "bo_qua_toi_da": 7},
	"mon_tang": {"ten": "Món đang lên", "muc": "vua", "bo_phan": ["marketing"], "han": 3, "an_sau_xong": 7, "bo_qua_toi_da": 14},
	"mon_moi": {"ten": "Món mới có đà", "muc": "thap", "bo_phan": ["marketing"], "han": 7, "an_sau_xong": 14, "bo_qua_toi_da": 14},
}

# Lý do bỏ qua. "Số liệu chưa đúng" là tín hiệu quý nhất: nó nói luật nào
# đang bắt nhầm, để chỉnh ngưỡng bằng ví dụ thật chứ không đoán.
LY_DO_BO_QUA = (
	("dang_xu_ly", "Đã biết, đang xử lý"),
	("so_sai", "Số liệu chưa đúng"),
	("khong_can", "Không cần làm lúc này"),
	("khac", "Lý do khác"),
)
TEN_LY_DO = dict(LY_DO_BO_QUA)

# Trạng thái Task còn mở (chưa xong, chưa huỷ).
TASK_MO = ("Open", "Working", "Pending Review", "Overdue")

KHOA_DEM = "vgb_bang_sang"


# =================================================================== THUẦN

def so(n):
	"""Số nguyên có dấu chấm nghìn, kiểu Việt Nam. THUẦN."""
	try:
		v = int(round(float(n or 0)))
	except Exception:
		v = 0
	return "{:,}".format(v).replace(",", ".")


def ngay_ngan(d):
	"""dd/mm. THUẦN."""
	try:
		return getdate(d).strftime("%d/%m")
	except Exception:
		return str(d or "")


def kho_ngan(kho):
	"""Bỏ hậu tố công ty: "Kho tổng 307 - TV" -> "Kho tổng 307". THUẦN."""
	k = str(kho or "").strip()
	return k.rsplit(" - ", 1)[0] if " - " in k else k


def la_mon_ban(ma):
	"""Mã này có phải món bán (bánh, đồ uống) không. THUẦN."""
	m = str(ma or "").strip().upper()
	if not m or m.startswith(TIEN_TO_LOAI_TRU):
		return False
	return m.startswith(TIEN_TO_MON)


def la_mua_vu(ma):
	return str(ma or "").strip().upper().startswith(TIEN_TO_MUA_VU)


def cua_so_tuan(hom_qua):
	"""Ba cửa sổ bảy ngày liền nhau kết thúc ở `hom_qua`. THUẦN.

	Trả về [(tu, den) tuần cũ nhất, tuần giữa, tuần gần nhất]. Ba cửa sổ để
	"giảm hai tuần liền" có đủ HAI lần so sánh (Codex #351 mục 1).
	"""
	d = getdate(hom_qua)
	ra = []
	for k in (2, 1, 0):
		den = d - datetime.timedelta(days=7 * k)
		ra.append((den - datetime.timedelta(days=6), den))
	return ra


def tuan_cua(ngay, cua_so):
	"""Ngày này thuộc cửa sổ nào (0, 1, 2), không thuộc thì None. THUẦN."""
	d = getdate(ngay)
	for i, (tu, den) in enumerate(cua_so):
		if tu <= d <= den:
			return i
	return None


def gom_ban(dong, hd_theo_ten, cua_so, chi_quay=False):
	"""Cộng số lượng bán theo mã và theo tuần, kèm tách theo nguồn đơn. THUẦN.

	dong: dòng món (parent, item_code, item_name, qty).
	hd_theo_ten: {tên hoá đơn: {"posting_date", "nguon", "diem"}}.
	chi_quay=True thì bỏ đơn của điểm không quầy (đơn đặt trước online).

	Trả {ma: {"ten", "q": [q_cu, q_giua, q_gan], "nguon": [{nguon: q}, x3]}}.
	Lượng là lượng RÒNG: dòng trả hàng mang số âm được cộng vào luôn.
	"""
	ra = {}
	for r in dong or []:
		ma = r.get("item_code")
		if not la_mon_ban(ma):
			continue
		hd = hd_theo_ten.get(r.get("parent"))
		if not hd:
			continue
		if chi_quay and hd.get("diem") == DIEM_KHONG_QUAY:
			continue
		t = tuan_cua(hd.get("posting_date"), cua_so)
		if t is None:
			continue
		o = ra.setdefault(ma, {"ten": r.get("item_name") or ma, "q": [0.0, 0.0, 0.0], "nguon": [{}, {}, {}]})
		sl = flt(r.get("qty"))
		o["q"][t] += sl
		ng = hd.get("nguon") or "Khác"
		o["nguon"][t][ng] = o["nguon"][t].get(ng, 0.0) + sl
	return ra


def xep_hang(ban, tuan=2):
	"""{ma: hạng} theo số bán của một tuần, hạng 1 là bán nhiều nhất. THUẦN."""
	ds = sorted(ban.items(), key=lambda kv: (-kv[1]["q"][tuan], kv[0]))
	return {ma: i + 1 for i, (ma, _) in enumerate(ds)}


def nguon_chinh(nguon_truoc, nguon_sau, chieu, nguong=0.6):
	"""Kênh chiếm phần lớn thay đổi, hoặc "" nếu thay đổi rải đều. THUẦN.

	chieu = 1 là tìm kênh kéo tăng, -1 là kênh kéo giảm.
	"""
	chenh = {}
	for k in set(nguon_truoc or {}) | set(nguon_sau or {}):
		c = (flt((nguon_sau or {}).get(k)) - flt((nguon_truoc or {}).get(k))) * chieu
		if c > 0:
			chenh[k] = c
	tong = sum(chenh.values())
	if tong <= 0:
		return ""
	k, v = max(chenh.items(), key=lambda kv: (kv[1], kv[0]))
	return k if v / tong >= nguong else ""


def _pt(a, b):
	"""Phần trăm thay đổi từ b sang a, làm tròn. THUẦN."""
	return int(round((a - b) / b * 100)) if b else 0


def xet_tang(q, hang, n=None):
	"""Món đang lên? Trả "tang", "moi" hoặc None. THUẦN.

	q = [cũ, giữa, gần]. Tuần gốc bằng 0 thì KHÔNG tính phần trăm (Codex #351
	mục 2): hai tuần trước đều chưa bán là "mới phát sinh", không phải "tăng
	vô cực".
	"""
	n = n or NGUONG
	q0, q1, q2 = q
	if q2 < n["san_mau"]:
		return None
	if q1 <= 0:
		return "moi" if q0 <= 0 else None
	# Codex #356: sàn mẫu áp cho TUẦN GỐC, không chỉ tuần gần. Từ 4 lên 12 là
	# mẫu số nhỏ, "tăng 200%" không có nghĩa.
	if q1 < n["san_mau"]:
		return None
	if hang > n["top_tang"]:
		return None
	if q2 - q1 < n["tang_tuyet_doi"]:
		return None
	if (q2 - q1) / q1 < n["tang_ty_le"]:
		return None
	return "tang"


def xet_giam(q, n=None):
	"""Món giảm hai tuần liền? THUẦN.

	Hai lần so sánh: tuần giữa thấp hơn tuần cũ VÀ tuần gần thấp hơn tuần
	giữa; cộng lại giảm ít nhất 30% và ít nhất 8 cái so với tuần cũ.
	"""
	n = n or NGUONG
	q0, q1, q2 = q
	if q0 < n["san_mau"]:
		return False
	if not (q1 < q0 and q2 < q1):
		return False
	if q0 - q2 < n["giam_tuyet_doi"]:
		return False
	return (q0 - q2) / q0 >= n["giam_ty_le"]


def nhan_dinh_xu_huong(ban, anh=None, nhan_tuan=None, n=None):
	"""Nhận định món tăng, món mới, món giảm từ bảng `gom_ban`. THUẦN."""
	n = n or NGUONG
	anh = anh or {}
	hang = xep_hang(ban)
	ra = []
	for ma, o in ban.items():
		q = [flt(x) for x in o["q"]]
		ten = o.get("ten") or ma
		doi = {"loai": "mon", "ma": ma, "ten": ten, "anh": anh.get(ma) or ""}
		so_lieu = {"chuoi": [int(round(x)) for x in q], "nhan": nhan_tuan or []}
		kq = xet_tang(q, hang.get(ma, 999), n)
		if kq == "tang":
			kenh = nguon_chinh(o["nguon"][1], o["nguon"][2], 1)
			cau = "Tuần qua bán %s, tuần trước %s (tăng %s, +%d%%)." % (
				so(q[2]), so(q[1]), so(q[2] - q[1]), _pt(q[2], q[1]))
			if kenh:
				cau += " Phần tăng chủ yếu đến từ %s." % kenh
			ra.append(_nd("mon_tang", ma, "tat_ca", "%s đang lên" % ten, cau,
				"Đẩy món này lên story và lên đầu menu các kênh giao hàng trong tuần; báo bếp để chuẩn bị đủ hàng.",
				doi, so_lieu, diem=q[2] - q[1]))
		elif kq == "moi":
			ra.append(_nd("mon_moi", ma, "tat_ca", "%s mới bán, đã có đà" % ten,
				"Tuần qua bán %s, hai tuần trước chưa bán cái nào." % so(q[2]),
				"Theo dõi thêm một tuần; giữ được đà thì lên bài giới thiệu món.",
				doi, so_lieu, diem=q[2]))
		if not la_mua_vu(ma) and xet_giam(q, n):
			kenh = nguon_chinh(o["nguon"][0], o["nguon"][2], -1)
			cau = "Ba tuần gần nhất: %s → %s → %s (giảm %d%% so với ba tuần trước)." % (
				so(q[0]), so(q[1]), so(q[2]), -_pt(q[2], q[0]))
			if kenh:
				cau += " Phần giảm chủ yếu ở %s." % kenh
			ra.append(_nd("mon_giam", ma, "tat_ca", "%s giảm hai tuần liền" % ten, cau,
				"Kiểm tra trước khi kết luận: có bị hết hàng, bị ẩn trên kênh giao hàng, đổi công thức hay đổi giá không. Chưa rõ nguyên nhân thì chưa giảm giá.",
				doi, so_lieu, diem=q[0] - q[2]))
	return ra


def nhan_dinh_thieu(kiem_banh, ban_quay, ngay_mai, anh=None, n=None):
	"""Món bán chạy mà bảng kiểm bánh ngày mai còn ít hơn mức bán một ngày. THUẦN.

	kiem_banh: dòng bảng Kiểm bánh ngày của NGÀY MAI (ma_hang, ten_banh, hinh,
	co_the_ban, da_dat, sx). Cột co_the_ban đã là tồn + bếp đã lên - đã đặt -
	phát sinh - chờ chốt - kênh khác (xem goi_y_ycsx.py).
	ban_quay: kết quả `gom_ban(..., chi_quay=True)`, tức bán tại quầy, KHÔNG
	gồm đơn đặt trước. Lấy đơn đặt trước vào đây là trừ đơn đặt hai lần, vì
	co_the_ban đã trừ rồi (Codex #351 mục 1, luật 12).

	Phần âm của co_the_ban là phần màn Gợi ý YCSX ĐÃ đề nghị làm thêm. Luật
	này không cộng lại phần đó, chỉ nói rằng quầy không còn cái nào để bán lẻ.
	"""
	n = n or NGUONG
	anh = anh or {}
	ra = []
	for d in kiem_banh or []:
		ma = str(d.get("ma_hang") or "").strip()
		if not ma or ma not in ban_quay:
			continue
		tb = flt(ban_quay[ma]["q"][2]) / 7.0
		if tb < n["ban_tb_toi_thieu"]:
			continue
		ctb = cint(d.get("co_the_ban"))
		con = max(ctb, 0)
		thieu = int(round(tb - con))
		if thieu < n["thieu_toi_thieu"]:
			continue
		ten = d.get("ten_banh") or ban_quay[ma].get("ten") or ma
		if ctb < 0:
			cau = ("Tại quầy bán trung bình %s cái/ngày. Bảng kiểm bánh ngày %s đang âm %s (màn Gợi ý YCSX đã tính phần này), "
				"chưa còn cái nào cho khách mua lẻ." % (_tb(tb), ngay_ngan(ngay_mai), so(-ctb)))
		else:
			cau = ("Tại quầy bán trung bình %s cái/ngày. Bảng kiểm bánh ngày %s còn có thể bán %s "
				"(đã trừ %s đơn đặt, đã tính bếp đã lên %s)." % (
					_tb(tb), ngay_ngan(ngay_mai), so(ctb), so(d.get("da_dat")), so(d.get("sx"))))
		ra.append(_nd("thieu_thanh_pham", ma, str(ngay_mai), "%s có thể thiếu ngày %s" % (ten, ngay_ngan(ngay_mai)), cau,
			"Bếp xem lại kế hoạch ngày %s; cần thêm thì Sales lập yêu cầu sản xuất bổ sung khoảng %s cái." % (ngay_ngan(ngay_mai), so(thieu)),
			{"loai": "mon", "ma": ma, "ten": ten, "anh": d.get("hinh") or anh.get(ma) or ""},
			{"tb_ngay": round(tb, 1), "co_the_ban": ctb, "thieu": thieu},
			diem=thieu))
	return ra


def _tb(x):
	"""Số trung bình một chữ số lẻ, dấu phẩy thập phân kiểu Việt. THUẦN."""
	v = round(flt(x), 1)
	return ("%d" % v) if v == int(v) else ("%.1f" % v).replace(".", ",")


# Codex #353 vòng 3: người nhận phải thấy ĐỦ lô để xử lý, nên gửi hết lô của
# kho (thẻ gọn 3 lô, bấm mở ra đủ). Trần này chỉ để chặn bảng phình bất
# thường; vượt trần thì thẻ nói rõ và chỉ đường xem đủ trên Desk.
LO_GUI_TOI_DA = 200


def nhan_dinh_lo(lo, hom_nay, n=None):
	"""Gộp lô quá hạn và cận hạn theo TỪNG KHO, mỗi kho một nhận định. THUẦN.

	lo: [{"lo", "ma", "ten", "kho", "han", "sl"}], chỉ lô còn hàng thật tại
	kho đó (Codex #351: chỉ tính lượng còn tại đúng kho).

	Quá hạn và cận hạn tách hai nhận định, vì hai việc khác hẳn nhau: cận hạn
	là xem kế hoạch dùng, quá hạn là cách ly và xử lý theo thẩm quyền, KHÔNG
	gợi ý dùng hay bán rẻ.
	"""
	n = n or NGUONG
	t = getdate(hom_nay)
	nhom = {}
	for x in lo or []:
		if flt(x.get("sl")) <= 0 or not x.get("han") or not x.get("kho"):
			continue
		h = getdate(x["han"])
		if h < t:
			loai = "lo_qua_han"
		elif (h - t).days <= n["ngay_can_han"]:
			loai = "lo_can_han"
		else:
			continue
		nhom.setdefault((loai, x["kho"]), []).append(x)
	ra = []
	for (loai, kho), ds in sorted(nhom.items(), key=lambda kv: (kv[0][0], kv[0][1])):
		ds = sorted(ds, key=lambda x: (str(x.get("han")), x.get("ten") or ""))
		so_ma = len({x.get("ma") for x in ds})
		mau = ", ".join(
			"%s (%s %s)" % (x.get("ten") or x.get("ma"), "hạn" if loai == "lo_qua_han" else "hết hạn", getdate(x["han"]).strftime("%d/%m/%Y"))
			for x in ds[:2]
		)
		con = len(ds) - 2
		if con > 0:
			mau += " và %d lô nữa" % con
		doi = {"loai": "kho", "ma": kho, "ten": kho_ngan(kho), "anh": ""}
		so_lieu = {"so_lo": len(ds), "so_ma": so_ma,
			"lo": [{"lo": x.get("lo"), "ma": x.get("ma"), "ten": x.get("ten"), "han": str(x.get("han")), "sl": flt(x.get("sl")),
				"dvt": x.get("dvt") or ""} for x in ds[:LO_GUI_TOI_DA]]}
		# Câu đầy đủ (có tên lô mẫu) đi vào mô tả Task để đọc được trên Desk.
		# Trên app thẻ đã có bảng lô, nên thẻ dùng câu ngắn cho khỏi nói hai lần.
		if loai == "lo_qua_han":
			x = _nd(loai, kho, "", "%d lô quá hạn ở %s" % (len(ds), kho_ngan(kho)),
				"%d lô của %d mã còn hàng đã quá hạn: %s." % (len(ds), so_ma, mau),
				"Kiểm thực tế ngay: hàng quá hạn thật thì cách ly, không dùng, không bán, báo quản lý kho xử lý theo thẩm quyền. Hạn ghi sai lúc nhập thì báo kế toán kho, không tự sửa.",
				doi, so_lieu, diem=len(ds))
			x["cau_ngan"] = "%d lô của %d mã còn hàng đã quá hạn." % (len(ds), so_ma)
		else:
			x = _nd(loai, kho, "", "%d lô sắp hết hạn ở %s" % (len(ds), kho_ngan(kho)),
				"Hết hạn trong %d ngày tới: %s." % (n["ngay_can_han"], mau),
				"Bếp ưu tiên dùng các lô này trước (hạn gần dùng trước); không kịp dùng thì báo quản lý kho trước ngày hết hạn.",
				doi, so_lieu, diem=len(ds))
			x["cau_ngan"] = "%d lô còn hàng hết hạn trong %d ngày tới." % (len(ds), n["ngay_can_han"])
		ra.append(x)
	return ra


def _nd(luat, doi_tuong, pham_vi, tieu_de, cau, goi_y, doi, so_lieu, diem=0):
	"""Dựng một nhận định. THUẦN."""
	l = LUAT[luat]
	return {
		"khoa": "%s|%s|%s" % (luat, doi_tuong, pham_vi or ""),
		"luat": luat,
		"ten_luat": l["ten"],
		"muc": l["muc"],
		"bo_phan": list(l["bo_phan"]),
		"han": l["han"],
		"bo_qua_toi_da": l["bo_qua_toi_da"],
		"tieu_de": tieu_de,
		"cau": cau,
		"goi_y": goi_y,
		"doi": doi,
		"so_lieu": so_lieu,
		"diem": flt(diem),
	}


def xep(ds):
	"""Mức cao trước, trong cùng mức thì việc lớn trước. THUẦN."""
	return sorted(ds or [], key=lambda x: (-MUC.get(x.get("muc"), 0), -flt(x.get("diem")), x.get("khoa") or ""))


def chat_luong(hd_tuan, hd_hom_qua, diem_ban, kb_ngay_mai, ngay_mai, bay_gio, n=None):
	"""Những điều người đọc cần biết để tin hay chưa tin các nhận định. THUẦN.

	hd_tuan: [số hoá đơn tuần cũ, giữa, gần]; hd_hom_qua: {điểm: số hoá đơn};
	diem_ban: [{"ma", "ten", "tb_tuan_giua"}] số hoá đơn trung bình/ngày tuần
	giữa; kb_ngay_mai: {"co_so", "dong_bo_luc"}; nhap: (số đơn nháp, tổng số
	đơn) của tuần gần.
	"""
	n = n or NGUONG
	ra = []
	if flt(hd_tuan.get("cu")) < n["hd_toi_thieu_tuan"]:
		ra.append({"ma": "lich_su", "cau": "Chưa đủ ba tuần số bán, chưa xét được món giảm hai tuần liền."})
	for d in diem_ban or []:
		if flt(d.get("tb_ngay")) >= 5 and not cint((hd_hom_qua or {}).get(d["ma"])):
			ra.append({"ma": "thieu_hd_" + d["ma"], "cau": "Chưa có hoá đơn hôm qua của %s; nếu hôm qua có bán thì đơn chưa về, số của điểm này đang thiếu." % d["ten"]})
	nhap, tong = hd_tuan.get("nhap") or (0, 0)
	if tong and nhap / float(tong) >= n["ty_le_nhap"]:
		ra.append({"ma": "nhap", "cau": "%s trên %s đơn tuần qua chưa ghi sổ; số bán đang là số tạm tính." % (so(nhap), so(tong))})
	kb = kb_ngay_mai or {}
	if not cint(kb.get("co_so")):
		ra.append({"ma": "kiem_banh", "cau": "Chưa có bảng kiểm bánh ngày %s nên chưa xét được món có thể thiếu." % ngay_ngan(ngay_mai)})
	elif not kb.get("dong_bo_luc"):
		# Codex #353: bảng có mà chưa đồng bộ lần nào thì cột đã đặt có thể
		# trống; không được coi là số mới.
		ra.append({"ma": "pancake", "cau": "Bảng kiểm bánh ngày %s chưa đồng bộ đơn Pancake lần nào; số đã đặt có thể còn thiếu." % ngay_ngan(ngay_mai)})
	else:
		try:
			cu = (now_datetime_thuan(bay_gio) - now_datetime_thuan(kb["dong_bo_luc"])).total_seconds() / 3600.0
		except Exception:
			cu = 0
		if cu >= n["gio_dong_bo_cu"]:
			ra.append({"ma": "pancake", "cau": "Đơn Pancake đồng bộ lần cuối lúc %s; đơn đặt mới hơn chưa được trừ." % str(kb["dong_bo_luc"])[11:16]})
	return ra


def now_datetime_thuan(v):
	"""Chuỗi hoặc datetime -> datetime không múi giờ. THUẦN."""
	if isinstance(v, datetime.datetime):
		return v.replace(tzinfo=None)
	s = str(v or "").strip().replace("T", " ")[:19]
	return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")


def bo_phan_duoc_xem(vai):
	"""Những bộ phận người mang bộ vai này được xem. THUẦN."""
	v = set(vai or [])
	if v & VAI_GIAM_DOC:
		return [k for k, _, _ in BO_PHAN]
	return [k for k, _, _ in BO_PHAN if v & XEM_BO_PHAN.get(k, set())]


def loc_theo_vai(ds, vai):
	"""Chỉ giữ nhận định có ít nhất một bộ phận người này được xem. THUẦN.

	Lọc ở MÁY CHỦ trước khi trả về, không phải ẩn trên màn hình (AGENTS.md
	mục 2b điều 16): marketing không nhận về số lô quá hạn của kho.
	"""
	duoc = set(bo_phan_duoc_xem(vai))
	return [x for x in ds or [] if duoc & set(x.get("bo_phan") or [])]


def chia_theo_viec(ds, viec, hom_nay):
	"""Tách nhận định thành "cần giao" theo việc đã có của cùng khoá. THUẦN.

	viec: danh sách Task đã sinh từ bảng sáng (khoa, status, completed_on,
	nhac_lai). Một nhận định bị ẩn khỏi "cần giao" khi:
	  - khoá đó đang có việc MỞ (nó nằm ở tab Đã giao);
	  - khoá đó bị bỏ qua và chưa tới ngày nhắc lại;
	  - khoá đó vừa xong trong số ngày `an_sau_xong` của luật, để số kịp phản
	    ánh việc đã làm. Lô quá hạn chỉ ẩn một ngày: còn quá hạn thì mai báo lại.
	"""
	theo_khoa = {}
	for v in viec or []:
		theo_khoa.setdefault(v.get("khoa"), []).append(v)
	return [x for x in ds or [] if not ly_do_an(x["luat"], theo_khoa.get(x["khoa"], []), hom_nay)[0]]


def ly_do_an(luat, viec_cua_khoa, hom_nay):
	"""Vì sao một nhận định đang KHÔNG được giao mới: ("mo"|"bo_qua"|"vua_xong",
	tên Task) hoặc (None, None). THUẦN.

	MỘT nguồn cho cả bảng (chia_theo_viec) lẫn bước kiểm lại trong khoá của
	giao/bo_qua (Codex #353 vòng 3: hai quản lý bấm Bỏ qua và Giao cùng lúc
	từ cùng một bảng; trước đây trong khoá chỉ kiểm việc mở, nên Giao vẫn
	tạo việc ngay sau khi người kia vừa bỏ qua)."""
	t = getdate(hom_nay)
	for v in viec_cua_khoa or []:
		st = v.get("status")
		if st in TASK_MO:
			return "mo", v.get("name")
	for v in viec_cua_khoa or []:
		st = v.get("status")
		if st == "Cancelled" and v.get("nhac_lai") and getdate(v["nhac_lai"]) > t:
			return "bo_qua", v.get("name")
		if st == "Completed" and v.get("completed_on"):
			ngay = LUAT.get(luat, {}).get("an_sau_xong", 1)
			if (t - getdate(v["completed_on"])).days < ngay:
				return "vua_xong", v.get("name")
	return None, None


def so_ngay_bo_qua(luat, so_ngay):
	"""Kẹp số ngày bỏ qua trong giới hạn của luật, ít nhất một ngày. THUẦN."""
	tran = LUAT.get(luat, {}).get("bo_qua_toi_da", 7)
	return max(1, min(cint(so_ngay) or 1, tran))


def nhan_dinh_bao_cao_mon(dong_nay, dong_truoc, nhan_truoc, anh=None, n=None):
	"""Thẻ Nhận định trên báo cáo Món bán chạy (BC08). THUẦN.

	So kỳ đang xem với kỳ liền trước, CÙNG bộ lọc của báo cáo (Codex #351
	mục 4). Tính trên toàn bộ dòng trước khi báo cáo cắt bớt để hiện, nên
	món thứ 700 vẫn được xét. Chỉ xét món bán, bỏ phụ kiện và dịch vụ.
	"""
	n = n or NGUONG
	anh = anh or {}
	nay = {r.get("ma_mon"): r for r in dong_nay or [] if la_mon_ban(r.get("ma_mon"))}
	truoc = {r.get("ma_mon"): flt(r.get("sl")) for r in dong_truoc or [] if la_mon_ban(r.get("ma_mon"))}
	tang, giam, moi = [], [], 0
	for ma in set(nay) | set(truoc):
		a = flt((nay.get(ma) or {}).get("sl"))
		b = truoc.get(ma, 0.0)
		ten = (nay.get(ma) or {}).get("mon") or ma
		if b <= 0:
			if a >= n["san_mau"]:
				moi += 1
			continue
		# Codex #356: kỳ gốc phải đủ mẫu (cùng luật với xet_tang).
		if b < n["san_mau"]:
			continue
		if a - b >= n["tang_tuyet_doi"] and (a - b) / b >= n["tang_ty_le"]:
			tang.append({"ma": ma, "ten": ten, "anh": anh.get(ma) or "", "nay": a, "truoc": b, "pt": _pt(a, b)})
		elif b - a >= n["giam_tuyet_doi"] and (b - a) / b >= n["giam_ty_le"] and not la_mua_vu(ma):
			giam.append({"ma": ma, "ten": ten, "anh": anh.get(ma) or "", "nay": a, "truoc": b, "pt": _pt(a, b)})
	tang.sort(key=lambda x: (-(x["nay"] - x["truoc"]), x["ma"]))
	giam.sort(key=lambda x: (-(x["truoc"] - x["nay"]), x["ma"]))
	if not (tang or giam or moi):
		return None
	return {"so_voi": nhan_truoc, "tang": tang[:2], "giam": giam[:2], "so_tang": len(tang), "so_giam": len(giam), "moi": moi}


def loi_nguoi_nhan(email, u):
	"""Câu lỗi nếu tài khoản này không được nhận việc nội bộ, None nếu được.
	THUẦN. u: {"enabled", "user_type"} đọc từ User, hoặc None nếu không có.

	Codex #356: gọi thẳng API `giao` thì không qua danh sách chọn của
	nguoi_de_giao, nên phải soát lại đúng luật đó ở máy chủ: chỉ tài khoản nội
	bộ (System User) đang bật, không phải Administrator, Guest. Giao cho một
	Website User là mở Task nội bộ (kèm quyền ghi) cho người ngoài."""
	if email in ("Administrator", "Guest"):
		return "Không giao việc cho tài khoản %s. Chọn người trong danh sách." % email
	if not u or not cint(u.get("enabled")):
		return "Tài khoản %s không còn hoạt động. Chọn người khác." % email
	if (u.get("user_type") or "") != "System User":
		return "Tài khoản %s không phải tài khoản nội bộ nên không nhận việc được. Chọn người trong danh sách." % email
	return None


def soat_ket_qua(trang_thai, trang_thai_cu, ket_qua):
	"""Câu lỗi nếu Task bảng sáng ở Completed mà thiếu kết quả, None nếu hợp
	lệ. THUẦN.

	Codex #353 vòng 2: xét MỌI lần lưu khi đang Completed, không chỉ lúc
	chuyển sang; trước đó sửa trắng ô kết quả của việc đã xong vẫn lưu được.
	`trang_thai_cu` giữ lại cho chữ ký cũ, không còn dùng để miễn."""
	if trang_thai == "Completed" and len(str(ket_qua or "").strip()) < 5:
		return ("Việc này sinh từ màn Việc hôm nay: ghi ngắn kết quả đã làm vào ô \"Kết quả người nhận báo\" "
			"(mục Gợi ý từ Việc hôm nay) rồi mới đánh dấu xong.")
	return None


def soat_huy(trang_thai, trang_thai_cu, quyen, ly_do, nhac_lai, hom_nay):
	"""Câu lỗi nếu Task bảng sáng bị chuyển sang Cancelled sai đường. THUẦN.

	Codex #356: người nhận đổi Task sang Cancelled trên Desk thì ERPNext đóng
	việc mà không có lý do, không có ngày nhắc; nhận định hiện lại ngay ở Cần
	giao, còn tab Bỏ qua có một dòng không ai hiểu. Huỷ là "bỏ qua", chỉ quản
	lý làm, và phải có lý do trong danh sách cùng ngày nhắc lại sau hôm nay,
	đúng như đường bo_qua trên app."""
	if trang_thai != "Cancelled" or trang_thai_cu == "Cancelled":
		return None
	if quyen != "quan_ly":
		return "Người nhận không huỷ việc được. Làm không được thì ghi kết quả rồi báo xong, hoặc báo người giao để họ bấm Bỏ qua."
	if ly_do not in TEN_LY_DO:
		return "Huỷ việc từ màn Việc hôm nay là Bỏ qua: bấm nút \"Bỏ qua việc này\" trên form để chọn lý do và ngày nhắc lại."
	try:
		ok = bool(nhac_lai) and getdate(nhac_lai) > getdate(hom_nay)
	except Exception:
		ok = False
	if not ok:
		return "Bỏ qua phải có ngày nhắc lại sau hôm nay (ô \"Nhắc lại ngày\")."
	return None


def can_kiem_nguoi_sua(nguoi, truoc, trang_thai, ket_qua, vai=None):
	"""Lần lưu Task bảng sáng này có phải soát người sửa không. THUẦN.

	Codex #353 vòng 4: soát MỌI lần lưu của người thường, không chỉ khi đổi
	trạng thái hay kết quả. Người nhận cũ còn giữ DocShare ghi, sửa tiêu đề,
	mô tả, hạn trên Desk cũng làm người đang nhận đọc sai việc. Chỉ nhịp máy
	(Administrator) và System Manager được miễn. `truoc`, `trang_thai`,
	`ket_qua` giữ cho chữ ký cũ."""
	if nguoi in ("Administrator", "Guest", None, ""):
		return False
	if "System Manager" in set(vai or []):
		return False
	return True


# Căn cứ của một việc sinh từ bảng sáng: máy ghi lúc giao, không ai được sửa.
TRUONG_KHOA_TASK = ("vgb_goi_y_khoa", "vgb_goi_y_luat", "vgb_goi_y_bo_phan", "vgb_goi_y_phien_ban",
	"vgb_goi_y_den_ngay", "vgb_goi_y_so_lieu")
TASK_DONG = ("Completed", "Cancelled")


def loi_truong_khoa(truoc, sau):
	"""Câu lỗi nếu lần lưu đổi một trường căn cứ, None nếu không. THUẦN.

	Codex #356: gửi thẳng tài liệu qua API thì đổi được cả ô chỉ đọc; xoá ô
	khoá là Task thoát khỏi mọi luật và biến khỏi bảng sáng."""
	g = lambda v: "" if v is None else str(v).strip()[:10] if len(str(v)) >= 10 and str(v)[4:5] == "-" else ("" if v is None else str(v).strip())
	for f in TRUONG_KHOA_TASK:
		if g((truoc or {}).get(f)) != g(sau.get(f)):
			return "Không sửa được ô căn cứ \"%s\" của việc sinh từ màn Việc hôm nay." % f
	return None


def loi_mo_lai(cu, moi):
	"""Câu lỗi nếu mở lại việc đã đóng (xong hoặc bỏ qua). THUẦN.

	Codex #356: mở lại trên Desk thì ToDo không được dựng lại, việc thành
	"đang mở" mà không ai thấy, và nhận định bị ẩn khỏi Cần giao mãi. Việc đã
	đóng thì để nhận định hiện lại và giao việc mới."""
	if cu in TASK_DONG and moi not in TASK_DONG:
		return "Việc này đã đóng, không mở lại được. Nếu vẫn cần làm, nhận định sẽ hiện lại ở Cần giao để giao việc mới (việc bỏ qua thì bấm Hiện lại ở tab Bỏ qua)."
	if cu in TASK_DONG and moi in TASK_DONG and cu != moi:
		return "Việc đã đóng không đổi trạng thái được nữa."
	return None


# Hàng chip khoảng ngày (AGENTS.md: ba hàng chip trên mọi màn danh sách).
KY_NGAY = (("", "Tất cả"), ("hom_nay", "Hôm nay"), ("7", "7 ngày"), ("30", "30 ngày"))


def loc_theo_ky(ds, ky, hom_nay):
	"""Giữ dòng có mốc ngày trong khoảng đang chọn. THUẦN.

	Codex #356: lịch sử xong, bỏ qua trải nhiều ngày mà màn chỉ có chip trạng
	thái và bộ phận; thiếu hàng khoảng ngày thì phải cuộn hết mới tìm được."""
	if not ky:
		return list(ds or [])
	t = getdate(hom_nay)
	so = 0 if ky == "hom_nay" else cint(ky) - 1
	ra = []
	for x in ds or []:
		try:
			m = getdate(x.get("moc")) if x.get("moc") else None
		except Exception:
			m = None
		if m is not None and 0 <= (t - m).days <= so:
			ra.append(x)
	return ra


def mo_ta_viec(x):
	"""Nội dung ô mô tả của Task: đọc được trên Desk không cần app. THUẦN."""
	def e(s):
		return (str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
	return "<p><b>%s</b></p><p>%s</p><p>Gợi ý: %s</p>" % (e(x.get("tieu_de")), e(x.get("cau")), e(x.get("goi_y")))


# =================================================================== FRAPPE

import frappe  # noqa: E402  phần chạm hệ bắt đầu từ đây
from frappe.utils import add_days, now_datetime, nowdate  # noqa: E402

def _vai():
	return set(frappe.get_roles())


def _kiem_quyen():
	if not (_vai() & QUYEN_BANG_SANG):
		frappe.throw(
			"Màn Việc hôm nay chỉ mở cho giám đốc và quản lý các bộ phận. "
			"Cần xem thì nhờ quản trị cấp vai quản lý của bộ phận mình."
		)


def _hom_nay():
	return getdate(nowdate())


def _hoa_don_ba_tuan(cua_so):
	"""Hoá đơn ba tuần, tính CẢ đơn chưa ghi sổ (cùng chế độ cho cả ba tuần,
	Codex #351 mục 4), bỏ đơn hàng tặng: quà không phải sức mua."""
	from vagabond import bao_cao
	from vagabond.hang_tang import PT_TANG

	hd = bao_cao._hoa_don(cua_so[0][0], cua_so[2][1])
	return [r for r in hd if (r.get("vgb_pt_thanh_toan") or "") != PT_TANG]


def _anh_mon(ds_ma):
	ra = {}
	ds_ma = sorted({m for m in ds_ma if m})
	for i in range(0, len(ds_ma), 400):
		for it in frappe.get_all("Item", filters={"name": ["in", ds_ma[i:i + 400]]}, fields=["name", "image"], limit_page_length=0):
			ra[it["name"]] = it.get("image") or ""
	return ra


def _lo_sap_het(hom_nay, n=None):
	"""Lô có hạn tới hết ngày cận hạn, kèm số còn tại từng kho."""
	from vagabond import tra_ton

	n = n or NGUONG
	lo = frappe.get_all(
		"Batch",
		# Codex #353 vòng 2: KHÔNG lọc disabled. Lô đã tắt vẫn có thể còn hàng
		# trong kho (lo_hang.py cho xuất kèm nhắc), nên vẫn phải nhắc xử lý.
		filters={"expiry_date": ["<=", str(add_days(hom_nay, n["ngay_can_han"]))]},
		fields=["name", "item", "item_name", "expiry_date"],
		limit_page_length=0,
	)
	if not lo:
		return []
	ds_ma = sorted({b["item"] for b in lo})
	so_lo = {}
	for i in range(0, len(ds_ma), 400):
		so_lo.update(tra_ton._so_lo({"item_code": ["in", ds_ma[i:i + 400]]}))
	theo_lo = {b["name"]: b for b in lo}
	# Codex #353 vòng 3: số còn phải đi kèm đơn vị tồn kho (gram hay kg hay
	# cái), không thì "còn 5.000" không biết là bao nhiêu để cách ly.
	dvt = {}
	for i in range(0, len(ds_ma), 400):
		for it in frappe.get_all("Item", filters={"name": ["in", ds_ma[i:i + 400]]}, fields=["name", "stock_uom"], limit_page_length=0):
			dvt[it["name"]] = it.get("stock_uom") or ""
	ra = []
	for (ten_lo, kho), sl in so_lo.items():
		b = theo_lo.get(ten_lo)
		if not b or flt(sl) <= 0:
			continue
		ra.append({"lo": ten_lo, "ma": b["item"], "ten": b.get("item_name") or b["item"], "kho": kho, "han": b["expiry_date"], "sl": flt(sl),
			"dvt": dvt.get(b["item"], "")})
	return ra


TEN_PHAN_HONG = {
	"kiem_banh": "bảng kiểm bánh ngày mai",
	"xu_huong": "món tăng, món giảm",
	"thieu": "món có thể thiếu ngày mai",
	"lo": "lô quá hạn, cận hạn",
}


def canh_bao_hong(hong):
	"""Dòng cảnh báo cho những phần tính hỏng lần dựng này. THUẦN.

	Một phần hỏng mà bảng vẫn im lặng thì người đọc tưởng "không có việc":
	thiếu lô quá hạn trông y như kho sạch. Nên nói thẳng phần nào chưa có."""
	ten = [TEN_PHAN_HONG.get(x, x) for x in dict.fromkeys(hong or [])]
	if not ten:
		return []
	return [{"ma": "loi_tinh", "cau": "Lần tính này chưa đọc được phần: %s. Bảng dưới đây THIẾU phần đó, không phải là không có việc. Bấm Tính lại sau ít phút; vẫn thiếu thì báo quản trị." % ", ".join(ten)}]


def dung_bang_sang():
	"""Dựng bảng sáng tới hết hôm qua và cất vào bộ nhớ đệm. Trả về bảng."""
	from vagabond import bao_cao, kiem_banh

	hom_nay = _hom_nay()
	hom_qua = add_days(hom_nay, -1)
	ngay_mai = add_days(hom_nay, 1)
	cs = cua_so_tuan(hom_qua)
	nhan_tuan = ["%s-%s" % (ngay_ngan(t), ngay_ngan(d)) for t, d in cs]

	hd = _hoa_don_ba_tuan(cs)
	theo_ten = {}
	hd_tuan = {"cu": 0, "giua": 0, "gan": 0}
	nhap_gan = [0, 0]
	hd_hom_qua = {}
	hd_giua_diem = {}
	for r in hd:
		diem = bao_cao._diem(r)
		theo_ten[r["name"]] = {"posting_date": r.get("posting_date"), "nguon": (r.get("custom_nguon") or "").strip() or "Khác", "diem": diem}
		t = tuan_cua(r.get("posting_date"), cs)
		if t is None:
			continue
		hd_tuan[("cu", "giua", "gan")[t]] += 1
		if t == 2:
			nhap_gan[1] += 1
			nhap_gan[0] += 1 if r.get("_nhap") else 0
		if t == 1:
			hd_giua_diem[diem] = hd_giua_diem.get(diem, 0) + 1
		if getdate(r.get("posting_date")) == getdate(hom_qua):
			hd_hom_qua[diem] = hd_hom_qua.get(diem, 0) + 1
	hd_tuan["nhap"] = tuple(nhap_gan)

	dong = bao_cao._dong_hang(hd)
	ban = gom_ban(dong, theo_ten, cs)
	ban_quay = gom_ban(dong, theo_ten, cs, chi_quay=True)

	# Codex #353 vòng 2: phần nào tính hỏng thì GHI LẠI và báo trên bảng,
	# không để bảng trông lành mà thiếu hẳn một mục (vd không còn lô quá hạn).
	hong = []
	try:
		kb = kiem_banh.bang(str(ngay_mai)) or {}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "phan_tich: doc kiem banh")
		kb = {}
		hong.append("kiem_banh")

	nd = []
	anh = {}
	try:
		nd += nhan_dinh_xu_huong(ban, None, nhan_tuan)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "phan_tich: xu huong")
		hong.append("xu_huong")
	try:
		if cint(kb.get("co_so")):
			nd += nhan_dinh_thieu(kb.get("dong") or [], ban_quay, ngay_mai)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "phan_tich: thieu thanh pham")
		hong.append("thieu")
	try:
		nd += nhan_dinh_lo(_lo_sap_het(hom_nay), hom_nay)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "phan_tich: lo")
		hong.append("lo")
	anh = _anh_mon([x["doi"]["ma"] for x in nd if x["doi"]["loai"] == "mon" and not x["doi"].get("anh")])
	for x in nd:
		if x["doi"]["loai"] == "mon" and not x["doi"].get("anh"):
			x["doi"]["anh"] = anh.get(x["doi"]["ma"]) or ""

	diem_ban = [
		{"ma": d["ma"], "ten": d["ten"], "tb_ngay": hd_giua_diem.get(d["ma"], 0) / 7.0}
		for d in bao_cao._diem_ban()
	]
	bay_gio = now_datetime()
	bang = {
		"chot_luc": str(bay_gio)[:19],
		"den_ngay": str(hom_qua),
		"ngay_mai": str(ngay_mai),
		"nhan_tuan": nhan_tuan,
		"phien_ban": PHIEN_BAN_LUAT,
		"nhan_dinh": xep(nd),
		"chat_luong": canh_bao_hong(hong) + chat_luong(hd_tuan, hd_hom_qua, diem_ban, kb, ngay_mai, bay_gio),
	}
	frappe.cache().set_value(KHOA_DEM, bang, expires_in_sec=60 * 60 * 48)
	return bang


def dung_bang_sang_tu_dong():
	"""Nhịp 7 giờ sáng. Hỏng thì ghi log, không làm hỏng bộ lập lịch."""
	try:
		dung_bang_sang()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "phan_tich: dung bang sang tu dong")


def _xep_dung():
	"""Xếp MỘT lượt dựng chạy nền; đang có lượt trong hàng đợi thì thôi."""
	try:
		frappe.enqueue(
			"vagabond.phan_tich.dung_bang_sang_tu_dong",
			queue="long", timeout=900,
			job_id="vgb-bang-sang-%s" % _hom_nay(),
			deduplicate=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "phan_tich: xep dung")


def _doc_bang():
	"""Bảng của hôm nay trong bộ nhớ đệm, hoặc None nếu chưa có hay đã cũ."""
	try:
		b = frappe.cache().get_value(KHOA_DEM)
	except Exception:
		b = None
	if not b or b.get("den_ngay") != str(add_days(_hom_nay(), -1)):
		return None
	return b


TRUONG_VIEC = ["name", "subject", "status", "exp_end_date", "completed_on", "completed_by", "owner", "creation", "modified",
	"vgb_goi_y_khoa", "vgb_goi_y_luat", "vgb_goi_y_bo_phan", "vgb_goi_y_nhac_lai",
	"vgb_goi_y_bo_qua_ly_do", "vgb_goi_y_ket_qua", "vgb_goi_y_anh", "_assign"]


def _viec_bang_sang(so_ngay=30):
	"""Task sinh từ bảng sáng: MỌI việc còn mở, cộng lịch sử gần đây.

	Codex #353: lọc `modified` 30 ngày và trần 300 dòng TRƯỚC khi tách mở
	với đóng làm một việc mở để lâu không ai đụng biến mất khỏi tab Đã giao
	và số trễ hạn, rồi nhận định của nó hiện lại ở Cần giao. Nên việc mở đọc
	riêng, không giới hạn tuổi; chỉ lịch sử (xong, bỏ qua) mới có hạn ngày.
	"""
	mo = frappe.get_all(
		"Task",
		filters={"vgb_goi_y_khoa": ["is", "set"], "status": ["in", list(TASK_MO)]},
		fields=TRUONG_VIEC, order_by="modified desc", limit_page_length=0,
	)
	cu = frappe.get_all(
		"Task",
		filters={"vgb_goi_y_khoa": ["is", "set"], "status": ["in", ["Completed", "Cancelled"]],
			"modified": [">=", str(add_days(_hom_nay(), -so_ngay))]},
		fields=TRUONG_VIEC, order_by="modified desc", limit_page_length=500,
	)
	ds = mo + cu
	for d in ds:
		d["khoa"] = d.get("vgb_goi_y_khoa")
		d["nhac_lai"] = d.get("vgb_goi_y_nhac_lai")
	return ds


def _ten_nguoi(emails):
	ra = {}
	for e in sorted({x for x in emails if x}):
		ra[e] = frappe.db.get_value("User", e, "full_name") or e
	return ra


def _dong_viec(d, ten, hom_nay):
	"""Một dòng việc cho màn hình."""
	try:
		nhan = json.loads(d.get("_assign") or "[]")
	except Exception:
		nhan = []
	han = getdate(d["exp_end_date"]) if d.get("exp_end_date") else None
	st = d.get("status")
	if st == "Completed":
		tt = "xong"
	elif st == "Cancelled":
		tt = "bo_qua"
	elif han and han < hom_nay:
		tt = "tre"
	else:
		tt = "dang_lam" if st == "Working" else "mo"
	bp = [x for x in (d.get("vgb_goi_y_bo_phan") or "").split(",") if x]
	return {
		"name": d["name"],
		"tieu_de": d.get("subject") or "",
		"luat": d.get("vgb_goi_y_luat") or "",
		"bo_phan": bp,
		"tt": tt,
		"han": str(han) if han else "",
		"nguoi": [ten.get(e, e) for e in nhan] or ([ten.get(d.get("completed_by"), d.get("completed_by"))] if d.get("completed_by") else []),
		"xong_luc": str(d.get("completed_on") or ""),
		"ket_qua": d.get("vgb_goi_y_ket_qua") or "",
		"ly_do": TEN_LY_DO.get(d.get("vgb_goi_y_bo_qua_ly_do") or "", ""),
		"nhac_lai": str(d.get("vgb_goi_y_nhac_lai") or ""),
		"anh": d.get("vgb_goi_y_anh") or "",
		"giao_boi": ten.get(d.get("owner"), d.get("owner")),
		# Mốc ngày cho hàng chip khoảng ngày: việc xong theo ngày xong, bỏ
		# qua theo lần sửa cuối (lúc bỏ qua), còn lại theo ngày giao.
		"moc": str(d.get("completed_on") or "")[:10] if tt == "xong"
			else str(d.get("modified") or d.get("creation") or "")[:10] if tt == "bo_qua"
			else str(d.get("creation") or "")[:10],
	}


@frappe.whitelist()
def bang_sang(tab="can_giao", bo_phan="", ky=""):
	"""Màn Việc hôm nay: nhận định cần giao, việc đã giao, việc xong, bỏ qua.

	Chỉ ĐỌC. Lọc theo vai ở máy chủ trước khi trả về.
	"""
	_kiem_quyen()
	vai = _vai()
	hom_nay = _hom_nay()
	b = _doc_bang()
	if b is None:
		_xep_dung()
	duoc = bo_phan_duoc_xem(vai)
	viec = _viec_bang_sang()
	viec_xem = [v for v in viec if set((v.get("vgb_goi_y_bo_phan") or "").split(",")) & set(duoc)]

	nd = loc_theo_vai((b or {}).get("nhan_dinh") or [], vai)
	can_giao = chia_theo_viec(nd, viec, hom_nay)

	emails = []
	for v in viec_xem:
		try:
			emails += json.loads(v.get("_assign") or "[]")
		except Exception:
			pass
		emails += [v.get("owner"), v.get("completed_by")]
	ten = _ten_nguoi(emails)
	dong = [_dong_viec(v, ten, hom_nay) for v in viec_xem]
	da_giao = [d for d in dong if d["tt"] in ("mo", "dang_lam", "tre")]
	da_giao.sort(key=lambda d: (0 if d["tt"] == "tre" else 1, d["han"] or "9"))
	xong = [d for d in dong if d["tt"] == "xong" and d["xong_luc"] and (hom_nay - getdate(d["xong_luc"])).days <= 14]
	bo_qua = [d for d in dong if d["tt"] == "bo_qua" and (hom_nay - getdate(d["nhac_lai"] or hom_nay)).days <= 14]

	# Codex #356: ô "Trễ hạn" ở đầu màn phải mở đúng phần trễ, không phải cả
	# tab Đã giao. "tre" là tab lọc riêng, không có chip dưới.
	tre = [d for d in da_giao if d["tt"] == "tre"]
	nhom = {"can_giao": can_giao, "da_giao": da_giao, "tre": tre, "xong": xong, "bo_qua": bo_qua}
	tab = tab if tab in nhom else "can_giao"
	cua_tab = nhom[tab]
	dem_bp = {k: 0 for k in duoc}
	for x in cua_tab:
		for k in x.get("bo_phan") or []:
			if k in dem_bp:
				dem_bp[k] += 1
	bo_phan = (bo_phan or "").strip()
	hien = [x for x in cua_tab if not bo_phan or bo_phan in (x.get("bo_phan") or [])]
	ky = ky if ky in dict(KY_NGAY) else ""
	if tab != "can_giao":
		hien = loc_theo_ky(hien, ky, hom_nay)
	return {
		"ky": ky,
		"chip_ky": [{"k": k, "ten": t} for k, t in KY_NGAY],
		"dang_dung": 1 if b is None else 0,
		"chot_luc": (b or {}).get("chot_luc") or "",
		"den_ngay": (b or {}).get("den_ngay") or str(add_days(hom_nay, -1)),
		"nhan_tuan": (b or {}).get("nhan_tuan") or [],
		"tab": tab,
		"bo_phan": bo_phan,
		"dem": {k: len(v) for k, v in nhom.items()},
		"so_tre": sum(1 for d in da_giao if d["tt"] == "tre"),
		"chip_bo_phan": [{"k": k, "ten": TEN_BO_PHAN[k], "ic": ICON_BO_PHAN[k], "so": dem_bp.get(k, 0)} for k in duoc],
		"ds": hien,
		"chat_luong": (b or {}).get("chat_luong") or [],
		"ly_do_bo_qua": [{"k": k, "ten": t} for k, t in LY_DO_BO_QUA],
		"ten_bo_phan": TEN_BO_PHAN,
	}


@frappe.whitelist()
def dem_trang_chu():
	"""Hai con số cho ô trên trang chủ. Không có quyền thì trả 0, không ném lỗi."""
	if not (_vai() & QUYEN_BANG_SANG):
		return {"can_giao": 0, "tre": 0, "co_quyen": 0}
	kq = bang_sang()
	return {"can_giao": kq["dem"]["can_giao"], "tre": kq["so_tre"], "dang_dung": kq["dang_dung"], "co_quyen": 1}


def _tim_nhan_dinh(khoa):
	"""Nhận định của bảng hôm nay theo khoá, đã lọc theo vai người hỏi."""
	b = _doc_bang()
	if b is None:
		frappe.throw("Bảng hôm nay đang dựng lại. Chờ khoảng một phút rồi bấm Tải lại.", title="Đang dựng bảng")
	for x in loc_theo_vai(b.get("nhan_dinh") or [], _vai()):
		if x["khoa"] == khoa:
			return x
	frappe.throw(
		"Nhận định này không còn trong bảng hôm nay (số đã đổi hoặc bạn không phụ trách bộ phận này). Tải lại màn để xem bảng mới.",
		title="Không còn nhận định",
	)


def _viec_cua_khoa(khoa):
	"""Mọi Task gần đây của một khoá, đọc NGAY trong khoá tên (không dùng bảng
	trong bộ nhớ đệm, vì bảng là ảnh chụp và có thể đã cũ)."""
	return [
		{"name": r.get("name"), "khoa": khoa, "status": r.get("status"), "completed_on": r.get("completed_on"),
			"nhac_lai": r.get("vgb_goi_y_nhac_lai")}
		for r in frappe.get_all("Task", filters={"vgb_goi_y_khoa": khoa},
			fields=["name", "status", "completed_on", "vgb_goi_y_nhac_lai"], order_by="modified desc", limit_page_length=50)
	]


CAU_DA_AN = {
	"bo_qua": "Nhận định này vừa được bỏ qua (việc %s). Tải lại màn để xem bảng mới; cần làm ngay thì bấm Hiện lại ở tab Bỏ qua.",
	"vua_xong": "Nhận định này vừa được làm xong (việc %s). Tải lại màn để xem bảng mới.",
}


def _khoa_ten(khoa):
	"""Khoá tên của cơ sở dữ liệu cho một nhận định. Hai người bấm cùng lúc
	thì người sau chờ người trước xong rồi mới thấy việc đã có."""
	import hashlib

	# Tên khoá của MariaDB dài tối đa 64 ký tự; tên kho dài thì cắt ngang là
	# hai khoá khác nhau thành một. Băm ra cho đủ ngắn và vẫn phân biệt.
	ten = "vgb_bs:" + hashlib.md5(khoa.encode("utf-8")).hexdigest()
	kq = frappe.db.sql("select get_lock(%s, 5)", (ten,))
	if not (kq and kq[0] and kq[0][0]):
		frappe.throw("Người khác đang giao đúng việc này. Chờ vài giây rồi tải lại màn.", title="Đang bận")
	return ten


def _nha_khoa(ten):
	try:
		frappe.db.sql("select release_lock(%s)", (ten,))
	except Exception:
		pass


@frappe.whitelist()
def nguoi_de_giao(khoa):
	"""Danh sách người để chọn khi giao: người máy gợi ý trước, rồi mọi tài
	khoản nội bộ đang bật (ô chọn có tìm, không bao giờ ô gõ tay)."""
	_kiem_quyen()
	x = _tim_nhan_dinh(khoa)
	from vagabond import giao_viec

	goi_y = set()
	for bp in x.get("bo_phan") or []:
		goi_y |= set(giao_viec._nguoi_theo_vai(NHAN_BO_PHAN.get(bp, set())))
	if x["doi"].get("loai") == "kho":
		goi_y |= set(giao_viec._nguoi_giu_kho(x["doi"]["ma"]))
	ds = frappe.get_all(
		"User",
		filters={"enabled": 1, "user_type": "System User", "name": ["not in", ["Administrator", "Guest"]]},
		fields=["name", "full_name", "user_image"],
		order_by="full_name asc",
		limit_page_length=0,
	)
	ra = [{"email": u["name"], "ten": u.get("full_name") or u["name"], "anh": u.get("user_image") or "", "goi_y": 1 if u["name"] in goi_y else 0} for u in ds]
	ra.sort(key=lambda u: (-u["goi_y"], u["ten"]))
	return {"nguoi": ra, "han_goi_y": x.get("han") or 0, "tieu_de": x["tieu_de"]}


def _ds_email(nguoi):
	if isinstance(nguoi, str):
		try:
			nguoi = json.loads(nguoi)
		except Exception:
			nguoi = [x.strip() for x in nguoi.split(",")]
	return [x for x in dict.fromkeys(nguoi or []) if x]


@frappe.whitelist()
def giao(khoa, nguoi, han=None, ghi_chu=None):
	"""Giao một nhận định thành việc: một Task, ToDo cho từng người nhận.

	Bấm lại hay hai người cùng bấm thì trả về đúng việc đã có, không sinh
	việc thứ hai. Không giao được cho ai thì BÁO LỖI, không báo thành công
	giả (Codex #351 mục 3: giao_viec.giao trả giao:0 khi không tìm ra người).
	"""
	_kiem_quyen()
	x = _tim_nhan_dinh(khoa)
	ds = _ds_email(nguoi)
	if not ds:
		frappe.throw("Chưa chọn người nhận việc. Chọn ít nhất một người rồi bấm Giao.")
	for e in ds:
		loi = loi_nguoi_nhan(e, frappe.db.get_value("User", e, ["enabled", "user_type"], as_dict=True))
		if loi:
			frappe.throw(loi)
	han = getdate(han) if han else add_days(_hom_nay(), cint(x.get("han")))
	if han < _hom_nay():
		frappe.throw("Hạn không được trước hôm nay.")
	khoa_ten = _khoa_ten(khoa)
	try:
		ly, co = ly_do_an(x["luat"], _viec_cua_khoa(khoa), _hom_nay())
		if ly == "mo":
			return {"ok": 1, "name": co, "da_co": 1}
		if ly:
			frappe.throw(CAU_DA_AN[ly] % co, title="Bảng đã đổi")
		mo_ta = mo_ta_viec(x)
		if ghi_chu and str(ghi_chu).strip():
			mo_ta += "<p>Ghi chú của người giao: %s</p>" % frappe.utils.escape_html(str(ghi_chu).strip())
		t = frappe.get_doc({
			"doctype": "Task",
			"subject": x["tieu_de"][:140],
			"status": "Open",
			"priority": {"cao": "High", "vua": "Medium"}.get(x["muc"], "Low"),
			"exp_end_date": "%s 18:00:00" % han,
			"description": mo_ta,
			"vgb_goi_y_khoa": khoa,
			"vgb_goi_y_luat": x["luat"],
			"vgb_goi_y_bo_phan": ",".join(x.get("bo_phan") or []),
			"vgb_goi_y_phien_ban": PHIEN_BAN_LUAT,
			"vgb_goi_y_den_ngay": (_doc_bang() or {}).get("den_ngay"),
			"vgb_goi_y_so_lieu": json.dumps({"cau": x["cau"], "so_lieu": x.get("so_lieu")}, ensure_ascii=False),
			"vgb_goi_y_anh": x["doi"].get("anh") or "",
		})
		t.insert(ignore_permissions=True)
		so = _gan_nguoi(t, ds, x["tieu_de"][:140], han)
		if so != len(ds):
			frappe.throw("Không giao được việc cho người đã chọn. Tải lại màn rồi thử lại; vẫn lỗi thì báo quản trị.")
		from vagabond import thong_bao

		for e in ds:
			if e != frappe.session.user:
				thong_bao.gui(e, "Việc mới: %s" % x["tieu_de"][:80], x["goi_y"][:160], "/viec-can-lam", "Task:%s" % t.name)
		# Codex #353 vòng 2: ghi hẳn xuống TRƯỚC khi nhả khoá. Nhả trước khi
		# Frappe commit thì người bấm thứ hai lấy được khoá mà chưa thấy Task
		# vừa tạo, và sinh việc thứ hai (vgb_goi_y_khoa không có ràng buộc duy
		# nhất). Khoá tên của MariaDB gắn theo phiên, không theo giao dịch.
		frappe.db.commit()
		return {"ok": 1, "name": t.name, "so_nguoi": len(ds), "han": str(han)}
	finally:
		_nha_khoa(khoa_ten)


def _gan_nguoi(t, ds, mo_ta, han):
	"""Tạo ToDo cho từng người và chia sẻ Task cho họ. Trả số người đã gắn.

	KHÔNG đi qua `frappe.desk.form.assign_to.add` (và vì thế không qua
	`giao_viec.giao`): hàm đó gọi `check_permission()` trên Task với quyền của
	NGƯỜI GIAO, rồi `frappe.share.add` kiểm quyền chia sẻ của người giao
	(frappe/desk/form/assign_to.py `_add`, frappe/share.py `add_docshare`:
	`if not flags.get("ignore_share_permission"): check_share_permission`).
	Quản lý cửa hàng hay marketing không có vai Projects User nên cả hai bước
	đều hỏng, và giao_viec.giao nuốt lỗi trả `giao: 0`. Quyền ở đây đã được
	kiểm bằng `_kiem_quyen` và `_tim_nhan_dinh` (người giao phải thấy nhận
	định của bộ phận đó), nên ghi ToDo và DocShare bằng quyền hệ thống.

	ToDo tự chép người nhận vào ô `_assign` của Task (ToDo.on_update), nên
	ô Assigned To trên Desk khớp với app mà không phải chép tay.
	"""
	from frappe.share import add_docshare

	so = 0
	for e in ds:
		if not frappe.db.exists("ToDo", {"reference_type": "Task", "reference_name": t.name, "allocated_to": e, "status": "Open"}):
			frappe.get_doc({
				"doctype": "ToDo",
				"allocated_to": e,
				"reference_type": "Task",
				"reference_name": t.name,
				"description": mo_ta,
				"date": str(han),
				"priority": t.priority or "Medium",
				"status": "Open",
				"assigned_by": frappe.session.user,
			}).insert(ignore_permissions=True)
		add_docshare("Task", t.name, user=e, read=1, write=1, flags={"ignore_share_permission": True})
		so += 1
	# Người giao cũng phải mở được việc mình giao trên Desk.
	if frappe.session.user not in ds and frappe.session.user not in ("Administrator", "Guest"):
		add_docshare("Task", t.name, user=frappe.session.user, read=1, write=1, flags={"ignore_share_permission": True})
	return so


@frappe.whitelist()
def bo_qua(khoa, ly_do, so_ngay=7):
	"""Bỏ qua một nhận định tới ngày nhắc lại. Lưu thành Task đã huỷ để còn
	dấu vết ai bỏ qua, vì sao, tới bao giờ (QT-20: không xoá, chỉ đóng)."""
	_kiem_quyen()
	x = _tim_nhan_dinh(khoa)
	if ly_do not in TEN_LY_DO:
		frappe.throw("Chọn một lý do bỏ qua trong danh sách.")
	ngay = so_ngay_bo_qua(x["luat"], so_ngay)
	khoa_ten = _khoa_ten(khoa)
	try:
		ly, co = ly_do_an(x["luat"], _viec_cua_khoa(khoa), _hom_nay())
		if ly == "mo":
			frappe.throw("Việc này đã được giao. Mở tab Đã giao để xem ai đang làm.")
		if ly == "bo_qua":
			return {"ok": 1, "name": co, "da_co": 1}
		if ly:
			frappe.throw(CAU_DA_AN[ly] % co, title="Bảng đã đổi")
		nhac = add_days(_hom_nay(), ngay)
		t = frappe.get_doc({
			"doctype": "Task",
			"subject": ("Bỏ qua: " + x["tieu_de"])[:140],
			"status": "Cancelled",
			"priority": "Low",
			"description": mo_ta_viec(x),
			"vgb_goi_y_khoa": khoa,
			"vgb_goi_y_luat": x["luat"],
			"vgb_goi_y_bo_phan": ",".join(x.get("bo_phan") or []),
			"vgb_goi_y_phien_ban": PHIEN_BAN_LUAT,
			"vgb_goi_y_den_ngay": (_doc_bang() or {}).get("den_ngay"),
			"vgb_goi_y_bo_qua_ly_do": ly_do,
			"vgb_goi_y_nhac_lai": str(nhac),
			"vgb_goi_y_so_lieu": json.dumps({"cau": x["cau"], "so_lieu": x.get("so_lieu")}, ensure_ascii=False),
			"vgb_goi_y_anh": x["doi"].get("anh") or "",
		})
		t.insert(ignore_permissions=True)
		frappe.db.commit()  # như giao(): ghi xong rồi mới nhả khoá
		return {"ok": 1, "name": t.name, "nhac_lai": str(nhac), "so_ngay": ngay}
	finally:
		_nha_khoa(khoa_ten)


def _quyen_viec(t, ghi=False):
	"""Người đang đăng nhập có được xem (ghi=False) hay cập nhật (ghi=True)
	việc này không.

	Codex #353: người từng nhận mà ToDo đã đóng (việc giao lại cho người
	khác) vẫn được XEM lại, nhưng không được đổi trạng thái; đổi trạng thái
	chỉ dành cho ToDo còn mở hoặc người quản lý bộ phận.
	"""
	# Codex #356: xét quyền QUẢN LÝ trước. Quản lý bộ phận cũng hay là người
	# được giao (máy gợi ý Sales, Stock, Manufacturing Manager), mà xét ToDo
	# trước thì họ chỉ còn là "nhan" và mất nút Bỏ qua của chính bộ phận mình.
	if _vai() & VAI_GIAM_DOC:
		return "quan_ly"
	duoc = set(bo_phan_duoc_xem(_vai()))
	if duoc & set((t.get("vgb_goi_y_bo_phan") or "").split(",")):
		return "quan_ly"
	u = frappe.session.user
	loc = {"reference_type": "Task", "reference_name": t.name, "allocated_to": u}
	if ghi:
		loc["status"] = "Open"
	if frappe.db.exists("ToDo", loc):
		return "nhan"
	return ""


def _lay_viec(name, ghi=False):
	if not name or not frappe.db.exists("Task", name):
		frappe.throw("Không tìm thấy việc %s. Có thể việc đã bị gỡ; tải lại danh sách." % (name or ""))
	t = frappe.get_doc("Task", name)
	if not t.get("vgb_goi_y_khoa"):
		frappe.throw("Việc %s không sinh từ màn Việc hôm nay." % name)
	q = _quyen_viec(t, ghi)
	if not q:
		frappe.throw("Việc này không (còn) giao cho bạn và không thuộc bộ phận bạn quản lý."
			if ghi else "Việc này không giao cho bạn và không thuộc bộ phận bạn quản lý.")
	return t, q


@frappe.whitelist()
def viec(name):
	"""Chi tiết một việc sinh từ bảng sáng, cho người nhận và người quản lý."""
	t, q = _lay_viec(name)
	hom_nay = _hom_nay()
	d = t.as_dict()
	nhan = frappe.get_all("ToDo", filters={"reference_type": "Task", "reference_name": name}, fields=["allocated_to", "status"], limit_page_length=0)
	ten = _ten_nguoi([x["allocated_to"] for x in nhan] + [t.owner, t.get("completed_by")])
	d["_assign"] = json.dumps([x["allocated_to"] for x in nhan if x["status"] == "Open"])
	dong = _dong_viec(d, ten, hom_nay)
	try:
		sl = json.loads(t.get("vgb_goi_y_so_lieu") or "{}")
	except Exception:
		sl = {}
	dong.update({
		"cau": sl.get("cau") or "",
		"so_lieu": sl.get("so_lieu") or {},
		"goi_y": _goi_y_tu_mo_ta(t.get("description")),
		"ghi_chu_giao": _ghi_chu_tu_mo_ta(t.get("description")),
		"nguoi_nhan": [ten.get(x["allocated_to"], x["allocated_to"]) for x in nhan],
		"giao_luc": str(t.creation)[:16],
		"den_ngay": str(t.get("vgb_goi_y_den_ngay") or ""),
		"xong_boi": ten.get(t.get("completed_by"), t.get("completed_by") or ""),
		"quyen": q,
		"sua_duoc": 1 if t.status in TASK_MO else 0,
		# Cho nút "Bỏ qua việc này" trên Desk: một nguồn lý do, trần ngày.
		"ly_do_bo_qua": [{"k": k, "ten": ten} for k, ten in LY_DO_BO_QUA],
		"bo_qua_toi_da": LUAT.get(t.get("vgb_goi_y_luat"), {}).get("bo_qua_toi_da", 7),
	})
	return dong


def _goi_y_tu_mo_ta(html):
	s = str(html or "")
	i = s.find("<p>Gợi ý: ")
	if i < 0:
		return ""
	j = s.find("</p>", i)
	return s[i + len("<p>Gợi ý: "):j if j > 0 else None]


def _ghi_chu_tu_mo_ta(html):
	s = str(html or "")
	i = s.find("<p>Ghi chú của người giao: ")
	if i < 0:
		return ""
	j = s.find("</p>", i)
	return s[i + len("<p>Ghi chú của người giao: "):j if j > 0 else None]


@frappe.whitelist()
def cap_nhat_viec(name, trang_thai, ket_qua=None):
	"""Người nhận báo đang làm hoặc đã xong. Báo xong PHẢI kèm kết quả: máy
	không tự đóng việc chỉ vì số đã hết vượt ngưỡng (Codex #351 mục 3)."""
	t, q = _lay_viec(name, ghi=True)
	if t.status not in TASK_MO:
		frappe.throw("Việc này đã %s, không cập nhật được nữa." % ("xong" if t.status == "Completed" else "đóng"))
	if trang_thai == "dang_lam":
		t.status = "Working"
	elif trang_thai == "xong":
		kq = str(ket_qua or "").strip()
		if len(kq) < 5:
			frappe.throw("Ghi ngắn kết quả đã làm (ít nhất vài chữ) để người giao đọc được sáng mai.")
		t.status = "Completed"
		t.completed_by = frappe.session.user
		t.completed_on = str(_hom_nay())
		t.vgb_goi_y_ket_qua = kq[:500]
	else:
		frappe.throw("Trạng thái không hợp lệ.")
	t.flags.ignore_permissions = True
	t.save()
	return {"ok": 1, "tt": "xong" if t.status == "Completed" else "dang_lam"}


@frappe.whitelist()
def bo_qua_viec(name, ly_do, so_ngay=7):
	"""Quản lý bỏ qua một việc ĐÃ GIAO, từ nút trên form Task ở Desk.

	Codex #356: ô "Lý do bỏ qua" trên Task là ô chỉ đọc, nên đổi trạng thái
	sang Cancelled ngay trên Desk luôn bị chặn vì thiếu lý do. Nút này chọn lý
	do trong LY_DO_BO_QUA và số ngày nhắc lại, rồi huỷ Task; hook
	kiem_nguoi_sua_task vẫn soát lại đúng các luật đó ở máy chủ."""
	t, q = _lay_viec(name, ghi=True)
	if q != "quan_ly":
		frappe.throw("Chỉ người quản lý bộ phận mới bỏ qua việc đã giao. Làm không được thì báo người giao.")
	if t.status not in TASK_MO:
		frappe.throw("Việc này đã đóng, không bỏ qua được nữa.")
	if ly_do not in TEN_LY_DO:
		frappe.throw("Chọn một lý do bỏ qua trong danh sách.")
	ngay = so_ngay_bo_qua(t.get("vgb_goi_y_luat"), so_ngay)
	nhac = add_days(_hom_nay(), ngay)
	t.status = "Cancelled"
	t.vgb_goi_y_bo_qua_ly_do = ly_do
	t.vgb_goi_y_nhac_lai = str(nhac)
	t.flags.ignore_permissions = True
	t.save()
	# Codex #356: ERPNext chỉ tự đóng ToDo khi Task Completed. Bỏ qua thì tự
	# đóng, không thì người nhận còn một việc sống trên Desk cho Task đã huỷ.
	so_dong = _dong_todo(t.name)
	return {"ok": 1, "name": t.name, "nhac_lai": str(nhac), "so_ngay": ngay, "dong_todo": so_dong}


def _dong_todo(ten_task):
	"""Đóng (Cancelled) mọi ToDo còn mở của một Task. Trả số đã đóng."""
	so = 0
	for r in frappe.get_all("ToDo", filters={"reference_type": "Task", "reference_name": ten_task, "status": "Open"},
			fields=["name"], limit_page_length=0):
		d = frappe.get_doc("ToDo", r["name"])
		d.status = "Cancelled"
		d.flags.ignore_permissions = True
		d.save(ignore_permissions=True)
		so += 1
	return so


@frappe.whitelist()
def hien_lai(name):
	"""Đưa một nhận định đã bỏ qua trở lại bảng ngay hôm nay."""
	t, q = _lay_viec(name)
	if q != "quan_ly" or t.status != "Cancelled":
		frappe.throw("Chỉ đưa lại được nhận định đã bỏ qua, và chỉ người quản lý bộ phận đó.")
	frappe.db.set_value("Task", name, "vgb_goi_y_nhac_lai", str(_hom_nay()))
	return {"ok": 1}


@frappe.whitelist()
def tinh_lai():
	"""Người quản lý bấm tính lại. Mười phút một lần là đủ, không cho bấm dồn."""
	_kiem_quyen()
	b = _doc_bang()
	if b and b.get("chot_luc"):
		try:
			cach = (now_datetime() - now_datetime_thuan(b["chot_luc"])).total_seconds()
		except Exception:
			cach = 9999
		if cach < 600:
			return {"ok": 0, "cau": "Bảng vừa tính lúc %s. Số bán tính tới hết hôm qua nên tính lại lúc này không đổi gì." % b["chot_luc"][11:16]}
	_xep_dung()
	return {"ok": 1, "cau": "Đang tính lại, khoảng một phút nữa bấm Tải lại."}


def kiem_nguoi_sua_task(doc, method=None):
	"""Hook before_validate của Task bảng sáng: ai được lưu.

	Codex #353 vòng 2 và 4: người nhận cũ vẫn giữ DocShare ghi, nên trên Desk
	họ lưu được Task (đánh dấu xong, sửa tiêu đề, hạn). Mọi lần lưu của người
	thường phải là người đang nhận (ToDo mở) hoặc quản lý bộ phận.

	Đặt ở before_validate, KHÔNG ở validate: bench CI trên ae8e76b bắt được
	người nhận THẬT báo xong bị chặn, vì tới lúc hook validate chạy thì
	ERPNext (Task.validate) đã đóng ToDo của chính họ. before_validate chạy
	trước bộ điều khiển Task nên còn thấy đúng ToDo đang mở."""
	if doc.is_new():
		return
	# Codex #356: nhận diện Task bảng sáng theo giá trị ĐÃ LƯU, không theo ô
	# gửi lên: xoá trắng ô khoá qua API là lách được mọi luật dưới đây.
	truoc = frappe.db.get_value("Task", doc.name, ["status"] + list(TRUONG_KHOA_TASK), as_dict=True) or {}
	if not truoc.get("vgb_goi_y_khoa") and not doc.get("vgb_goi_y_khoa"):
		return
	vai = _vai()
	cu = truoc.get("status")
	if frappe.session.user != "Administrator":
		loi = loi_truong_khoa(truoc, doc) or loi_mo_lai(cu, doc.get("status"))
		if loi:
			frappe.throw(loi, title="Không sửa được")
	if not can_kiem_nguoi_sua(frappe.session.user, {}, doc.get("status"), doc.get("vgb_goi_y_ket_qua"), vai):
		q = "quan_ly"
	else:
		q = _quyen_viec(doc, ghi=True)
		if not q:
			frappe.throw("Việc này không (còn) giao cho bạn và không thuộc bộ phận bạn quản lý, nên không sửa được.",
				title="Không có quyền")
	loi = soat_huy(doc.get("status"), cu, q, doc.get("vgb_goi_y_bo_qua_ly_do"), doc.get("vgb_goi_y_nhac_lai"), _hom_nay())
	if loi:
		frappe.throw(loi, title="Không huỷ được")


def kiem_task(doc, method=None):
	"""Hook validate của Task. Chỉ động tới Task sinh từ bảng sáng.

	Codex #353: người nhận có quyền ghi Task (được chia sẻ) nên đánh dấu xong
	được ngay trên Desk mà không qua cap_nhat_viec; khi đó ERPNext đóng ToDo
	mà ô kết quả trống. Chặn ở tầng chứng từ thì app và Desk cùng một luật.
	Ai được lưu thì xét ở kiem_nguoi_sua_task (before_validate).
	"""
	if doc.is_new():
		if not doc.get("vgb_goi_y_khoa"):
			return
		cu = None
	else:
		truoc = frappe.db.get_value("Task", doc.name, ["status", "vgb_goi_y_khoa"], as_dict=True) or {}
		if not truoc.get("vgb_goi_y_khoa") and not doc.get("vgb_goi_y_khoa"):
			return
		cu = truoc.get("status")
	loi = soat_ket_qua(doc.get("status"), cu, doc.get("vgb_goi_y_ket_qua"))
	if loi:
		frappe.throw(loi, title="Thiếu kết quả")
	if doc.get("status") == "Completed" and cu != "Completed":
		if not doc.get("completed_by"):
			doc.completed_by = frappe.session.user
		if not doc.get("completed_on"):
			doc.completed_on = str(_hom_nay())


# ------------------------------------------------------ Việc cần làm (người nhận)

def viec_can_lam_cua(nguoi):
	"""Dòng cho màn Việc cần làm: việc từ bảng sáng đang giao ĐÍCH DANH cho
	người này. Lọc theo ToDo của chính họ, không theo vai."""
	ten = [t["reference_name"] for t in frappe.get_all(
		"ToDo",
		filters={"allocated_to": nguoi, "status": "Open", "reference_type": "Task"},
		fields=["reference_name"],
		limit_page_length=0,
	) if t.get("reference_name")]
	if not ten:
		return []
	hom_nay = _hom_nay()
	ra = []
	for t in frappe.get_all(
		"Task",
		filters={"name": ["in", ten], "vgb_goi_y_khoa": ["is", "set"], "status": ["in", list(TASK_MO)]},
		fields=["name", "subject", "exp_end_date", "vgb_goi_y_bo_phan"],
		limit_page_length=0,
	):
		han = getdate(t["exp_end_date"]) if t.get("exp_end_date") else None
		ra.append({
			"loai": "goi_y", "ma": t["name"], "nhom": "Việc được giao",
			"phu": t.get("subject") or "",
			"ngay": str(han) if han else "",
			"tt": "tre_hen" if han and han < hom_nay else "cho_lam",
		})
	return ra


# ------------------------------------------------------ Nhận định trên BC08

def the_bao_cao_mon(kq_nay, ky, tu, den, diem=None, nguon=None, pt=None, nhap=1):
	"""Thẻ Nhận định gắn vào kết quả báo cáo BC08. Hỏng thì trả None."""
	from vagabond import bao_cao

	try:
		tt, dd = bao_cao._ky_truoc(ky, tu, den)
		hd2 = bao_cao._loc_nhap(bao_cao._hoa_don(tt, dd, diem=diem, nguon=nguon, pt=pt), nhap)
		truoc = bao_cao._bc_mon_ban_chay(hd2)["dong"]
		the = nhan_dinh_bao_cao_mon(kq_nay, truoc, bao_cao._nhan_ky(ky, tt, dd))
		if the:
			anh = _anh_mon([x["ma"] for x in the["tang"] + the["giam"]])
			for x in the["tang"] + the["giam"]:
				x["anh"] = anh.get(x["ma"]) or ""
			the["mo_bang_sang"] = 1 if _vai() & QUYEN_BANG_SANG else 0
		return the
	except Exception:
		frappe.log_error(frappe.get_traceback(), "phan_tich: the bao cao mon")
		return None


# ------------------------------------------------------ Lối vào trên Desk
#
# Quy ước của tiệm: tính năng mới trên app phải có đường vào trên bản Desk,
# vì anh Việt duyệt việc nặng trên máy tính. Sidebar Desk v16 lấy từ doctype
# Workspace Sidebar (bảng con Workspace Sidebar Item), không lấy từ bảng
# links của Workspace. Trường của Item đọc từ
# frappe/desk/doctype/workspace_sidebar_item/workspace_sidebar_item.json:
# type (Link|Section Break...), label, link_type (DocType|...|URL), link_to,
# url, child, filters (JSON).

SIDEBAR_DESK = "Selling"
NHAN_NHOM_DESK = "Việc hôm nay"


def muc_sidebar():
	"""Ba mục thêm vào sidebar Bán hàng trên Desk. THUẦN."""
	return [
		{"type": "Section Break", "label": NHAN_NHOM_DESK, "icon": ""},
		{"type": "Link", "label": "Mở màn Việc hôm nay", "link_type": "URL", "url": "/viec-hom-nay", "child": 1},
		{"type": "Link", "label": "Việc đã giao từ Việc hôm nay", "link_type": "DocType", "link_to": "Task", "child": 1,
			"filters": json.dumps([["Task", "vgb_goi_y_luat", "is", "set"]])},
	]


def dung_sidebar():
	"""Thêm lối vào vào sidebar Bán hàng nếu chưa có. Lặp lại được, không
	đụng mục nào khác; sidebar chưa có trên site thì thôi."""
	try:
		if not frappe.db.exists("Workspace Sidebar", SIDEBAR_DESK):
			return 0
		sb = frappe.get_doc("Workspace Sidebar", SIDEBAR_DESK)
		co = {(r.get("type"), r.get("label")) for r in sb.get("items") or []}
		them = 0
		for m in muc_sidebar():
			if (m["type"], m["label"]) in co:
				continue
			sb.append("items", m)
			them += 1
		if them:
			sb.flags.ignore_permissions = True
			sb.save()
		return them
	except Exception:
		frappe.log_error(frappe.get_traceback(), "phan_tich: dung sidebar")
		return 0


# ------------------------------------------------------ Trường trên Task

TRUONG_MOI = {
	"Task": [
		{"fieldname": "vgb_goi_y_sec", "label": "Gợi ý từ Việc hôm nay", "fieldtype": "Section Break",
			"insert_after": "description", "collapsible": 1},
		{"fieldname": "vgb_goi_y_khoa", "label": "Khoá nhận định", "fieldtype": "Data", "read_only": 1,
			"insert_after": "vgb_goi_y_sec", "search_index": 1,
			"description": "Luật + đối tượng + phạm vi. Một vấn đề chỉ có một việc đang mở."},
		{"fieldname": "vgb_goi_y_luat", "label": "Luật", "fieldtype": "Data", "read_only": 1, "in_standard_filter": 1,
			"insert_after": "vgb_goi_y_khoa"},
		{"fieldname": "vgb_goi_y_bo_phan", "label": "Bộ phận", "fieldtype": "Data", "read_only": 1,
			"insert_after": "vgb_goi_y_luat"},
		{"fieldname": "vgb_goi_y_phien_ban", "label": "Phiên bản luật", "fieldtype": "Data", "read_only": 1,
			"insert_after": "vgb_goi_y_bo_phan"},
		{"fieldname": "vgb_goi_y_den_ngay", "label": "Số liệu tới hết ngày", "fieldtype": "Date", "read_only": 1,
			"insert_after": "vgb_goi_y_phien_ban"},
		{"fieldname": "vgb_goi_y_cb", "fieldtype": "Column Break", "insert_after": "vgb_goi_y_den_ngay"},
		{"fieldname": "vgb_goi_y_so_lieu", "label": "Căn cứ số liệu", "fieldtype": "Code", "options": "JSON", "read_only": 1,
			"insert_after": "vgb_goi_y_cb"},
		{"fieldname": "vgb_goi_y_ket_qua", "label": "Kết quả người nhận báo", "fieldtype": "Small Text",
			"insert_after": "vgb_goi_y_so_lieu"},
		{"fieldname": "vgb_goi_y_bo_qua_ly_do", "label": "Lý do bỏ qua", "fieldtype": "Data", "read_only": 1,
			"insert_after": "vgb_goi_y_ket_qua"},
		{"fieldname": "vgb_goi_y_nhac_lai", "label": "Nhắc lại từ ngày", "fieldtype": "Date",
			"insert_after": "vgb_goi_y_bo_qua_ly_do"},
		{"fieldname": "vgb_goi_y_anh", "label": "Ảnh", "fieldtype": "Data", "read_only": 1, "hidden": 1,
			"insert_after": "vgb_goi_y_nhac_lai"},
	],
}
